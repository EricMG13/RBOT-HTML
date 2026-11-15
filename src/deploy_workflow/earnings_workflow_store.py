"""CP-1B owner checkpoint: canonical JSON and hashes, the retained audit store under
`earnings-owner-audit/`, authenticated snapshots and ticket bindings.

Moved unchanged from `earnings_workflow`, which re-exports every name.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from pydantic import JsonValue

from deploy_vii.contracts import Contract, Run, Source, Span
from deploy_vii.cp1_workflow import CP1_PROMOTION
from deploy_vii.execution import Attempt, Execution, ExecutionSnapshot, current_inputs
from deploy_vii.preparation import PreparedPack
from deploy_workflow.earnings_workflow_contracts import (
    _KINDS,
    _PINS,
    _SESSION_POLICY_SHA256,
    MAX_AUDIT,
    MAX_JSON_DEPTH,
    AuditEntry,
    OwnerBinding,
    OwnerCaseId,
    OwnerError,
    OwnerPins,
    SourceIdentity,
)
from deploy_workflow.financial_workflow import FinancialBinding


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def _text_depth(text: str) -> int:
    """Maximum bracket nesting of JSON-looking text, without recursion.

    Counts `[` and `{` outside string literals; it is a bound, not a parser, so
    malformed text is measured the same way and rejected later by the real parser.
    """
    depth = deepest = 0
    in_string = escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            deepest = max(deepest, depth)
        elif char in "]}" and depth:
            depth -= 1
    return deepest


def _json_copy(value: object) -> JsonValue:
    """Validate exact JSON types before serialization; invoke no user copy hooks."""
    active: set[int] = set()

    def visit(item: object, depth: int) -> None:
        if item is None or type(item) in {str, bool, int}:
            return
        if type(item) is float and math.isfinite(item):
            return
        # The receipt models re-parse these values with pydantic, which rejects
        # nesting from depth 200; refuse here, before any tool consumes a sequence.
        if type(item) not in {dict, list} or id(item) in active or depth >= MAX_JSON_DEPTH:
            raise OwnerError("bad_arguments")
        active.add(id(item))
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str:
                    raise OwnerError("bad_arguments")
                visit(child, depth + 1)
        else:
            for child in cast(list[object], item):
                visit(child, depth + 1)
        active.remove(id(item))

    try:
        visit(value, 0)
        return cast(JsonValue, json.loads(_canonical(value).encode("utf-8")))
    except (RecursionError, ValueError):
        # ValueError covers UnicodeEncodeError and the interpreter's integer-digit
        # limit (json.dumps of an int over 4300 digits); both are actor input.
        raise OwnerError("bad_arguments") from None


def _parse[T: Contract](model: type[T], value: Any) -> T:
    return model.model_validate_json(_canonical(value))


_PENDING = ".pending-"


def _is_put_residue(path: Path) -> bool:
    """A temp file `_put` left behind by a crash; it is never a record or evidence."""
    return re.fullmatch(r"\.pending-[0-9a-f]{32}", path.name) is not None and path.is_file()


def _put(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / (_PENDING + uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != raw:
                raise OwnerError("identity_mismatch") from None
    finally:
        temporary.unlink(missing_ok=True)


def _sealed_on_disk(store: Execution) -> bool:
    return (store.directory / "earnings-owner-audit/owner-receipt.sha256").exists()


def _audit(store: Execution, kind: str, digest: str) -> Path:
    return store.directory / "earnings-owner-audit" / kind / digest


def _retain(store: Execution, kind: str, record: Contract) -> None:
    path = _audit(store, kind, record.content_hash())
    if not path.exists() and len(_inventory(store)) >= MAX_AUDIT:
        raise OwnerError("transport_limit")
    _put(path, record.model_dump_json().encode())


def _payload(store: Execution, raw: bytes) -> str:
    digest = _hash(raw)
    path = _audit(store, "payloads", digest)
    if not path.exists() and len(_inventory(store)) >= MAX_AUDIT:
        raise OwnerError("transport_limit")
    _put(path, raw)
    return digest


@contextmanager
def _stored_read() -> Iterator[None]:
    """Refuse unreadable or malformed stored bytes as `identity_mismatch`.

    Fail-closed and limited to the stored-record read sites that wrap it: a missing
    file, a directory in place of a file, or bytes that do not decode or validate
    mean the stored evidence was altered. Errors raised by B1's own composition are
    never inside this context, so programming defects propagate (lease: unexpected
    programming/I/O failures propagate). The original error stays as `__cause__`.
    """
    try:
        yield
    except OwnerError:
        raise
    except (FileNotFoundError, IsADirectoryError, ValueError) as error:
        raise OwnerError("identity_mismatch") from error


def _head(store: Execution) -> ExecutionSnapshot:
    with _stored_read():
        return store.read()


def _stored_bytes(store: Execution, kind: str, digest: str) -> bytes:
    """The bytes of one stored audit record; an unreadable record is tampered or lost."""
    with _stored_read():
        return _audit(store, kind, digest).read_bytes()


def _raw(store: Execution, digest: str) -> bytes:
    raw = _stored_bytes(store, "payloads", digest)
    if _hash(raw) != digest:
        raise OwnerError("identity_mismatch")
    return raw


def _text(store: Execution, digest: str) -> str:
    """A stored payload as text; stored bytes that do not decode are tampered evidence."""
    raw = _raw(store, digest)
    with _stored_read():
        return raw.decode("utf-8")


def _known[K, V](order: Mapping[K, V], key: K) -> V:
    """Look `key` up in an index built from stored records; an unknown key is tamper.

    Every key comes from a stored record that must name another stored record or a
    snapshot on the authenticated chain, so a miss means a record was forged,
    altered or deleted (lease: conflicting or ambiguous evidence refuses).
    """
    if key not in order:
        raise OwnerError("identity_mismatch")
    return order[key]


def _records[T: Contract](store: Execution, kind: str, model: type[T]) -> tuple[T, ...]:
    folder = store.directory / "earnings-owner-audit" / kind
    if folder.exists() and not folder.is_dir():
        raise OwnerError("identity_mismatch")
    result = []
    for path in sorted(folder.iterdir()) if folder.exists() else ():
        if _is_put_residue(path):
            continue
        with _stored_read():
            raw = path.read_bytes()
            record = model.model_validate_json(raw)
        if path.name != _hash(raw) or record.model_dump_json().encode() != raw:
            raise OwnerError("identity_mismatch")
        result.append(record)
    return tuple(result)


def _inventory(store: Execution) -> tuple[AuditEntry, ...]:
    root = store.directory / "earnings-owner-audit"
    entries = []
    if root.exists():
        for path in root.iterdir():
            if _is_put_residue(path):
                continue
            if path.name in {"owner-receipt.json", "owner-receipt.sha256"}:
                if not path.is_file():
                    raise OwnerError("identity_mismatch")
                continue
            if path.name not in {*_KINDS, "payloads"} or not path.is_dir():
                raise OwnerError("identity_mismatch")
            for record in path.iterdir():
                if _is_put_residue(record):
                    continue
                if not record.is_file() or re.fullmatch("[0-9a-f]{64}", record.name) is None:
                    raise OwnerError("identity_mismatch")
                if _hash(record.read_bytes()) != record.name:
                    raise OwnerError("identity_mismatch")
                entries.append(_parse(AuditEntry, {"kind": path.name, "sha256": record.name}))
    if len(entries) > MAX_AUDIT:
        raise OwnerError("transport_limit")
    return tuple(sorted(entries, key=lambda e: (e.kind, e.sha256)))


def _snapshot(store: Execution, digest: str) -> ExecutionSnapshot:
    with _stored_read():
        raw = (store.directory / "snapshots" / (digest + ".json")).read_bytes()
        value = ExecutionSnapshot.model_validate_json(raw)
    if _hash(raw) != digest or value.content_hash() != digest:
        raise OwnerError("identity_mismatch")
    with _stored_read():
        store.pack(value)
    return value


class _FrozenExecution(Execution):
    def __init__(self, store: Execution, snapshot: ExecutionSnapshot) -> None:
        super().__init__(store.directory)
        self.snapshot = snapshot

    def read(self) -> ExecutionSnapshot:
        return self.snapshot

    def _load(self, sha256: str) -> bytes:
        # The core raises only for an invalid hash, a missing blob or a hash mismatch
        # (execution.py:554-562): each means a referenced journal blob is lost or altered.
        with _stored_read():
            return super()._load(sha256)

    def _write(self, snapshot: ExecutionSnapshot) -> None:
        raise OwnerError("not_permitted")


def _case_pins(
    case_manifest: Path, case_id: OwnerCaseId, pack: PreparedPack
) -> tuple[dict[str, Any], OwnerPins]:
    raw = case_manifest.read_bytes()
    if _hash(raw) != _PINS["manifest.json"]:
        raise OwnerError("identity_mismatch")
    descriptor = json.loads(raw)
    matches = [case for case in descriptor["cases"] if case["case_id"] == case_id]
    if len(matches) != 1:
        raise OwnerError("bad_arguments")
    case = matches[0]
    source_raw = (case_manifest.parent / descriptor["source_manifest"]).read_bytes()
    if _hash(source_raw) != _PINS["source_manifest"]:
        raise OwnerError("identity_mismatch")
    for name in (
        "expected.json",
        "access-expected.json",
        "render-expected.json",
        "owner-expected.json",
    ):
        if _hash((case_manifest.parent / name).read_bytes()) != _PINS[name]:
            raise OwnerError("identity_mismatch")
    if (
        _hash((case_manifest.parent / "session-binding-expected.json").read_bytes())
        != _SESSION_POLICY_SHA256
    ):
        raise OwnerError("identity_mismatch")
    source_manifest = json.loads(source_raw)
    sources = []
    for item in source_manifest["sources"]:
        missing = case["source_state"] == "financial_missing" and item["source_id"] == "financial"
        spans = () if missing else tuple(Span(**page) for page in item["pages"])
        if not missing and _hash("\f".join(span.text for span in spans).encode()) != item["sha256"]:
            raise OwnerError("identity_mismatch")
        sources.append(
            Source(
                source_id=item["source_id"],
                name=item["name"],
                status="missing" if missing else "ready",
                sha256=None if missing else item["sha256"],
                spans=spans,
                coverage=(),
                media_type=None,
                extractor="supplied-representation",
                extraction_status="blocked" if missing else "complete",
                limitation="Quarterly financial statements were not supplied."
                if missing
                else "Unaudited without auditor; borrower, guarantor and restricted perimeters unavailable."
                if item["source_id"] == "financial"
                else None,
            )
        )
    expected = PreparedPack(
        run=Run.model_validate_json(_canonical(case["run"])), sources=tuple(sources)
    )
    if pack != expected or pack.model_dump_json() != expected.model_dump_json():
        raise OwnerError("identity_mismatch")
    pins = OwnerPins(
        case_manifest_sha256=_PINS["manifest.json"],
        source_manifest_sha256=_PINS["source_manifest"],
        core_expected_sha256=_PINS["expected.json"],
        access_expected_sha256=_PINS["access-expected.json"],
        render_expected_sha256=_PINS["render-expected.json"],
        owner_expected_sha256=_PINS["owner-expected.json"],
        sources=tuple(
            SourceIdentity(source_id=s.source_id, status=s.status, sha256=s.sha256)
            for s in pack.sources
        ),
    )
    return case, pins


def _binding(
    snapshot: ExecutionSnapshot, attempt: Attempt, step: str
) -> FinancialBinding | OwnerBinding:
    data = {
        "run_id": snapshot.run.run_id,
        "issuer_id": snapshot.run.issuer_id,
        "as_of": snapshot.run.as_of.isoformat(),
        "method_version": snapshot.run.method_version,
        "pack_sha256": snapshot.pack_sha256,
        "snapshot_sha256": snapshot.content_hash(),
        "module_id": attempt.module_id,
        "step_id": step,
        "ticket_id": attempt.ticket_id,
        "attempt": attempt.number,
        "inputs": [i.model_dump(mode="json") for i in attempt.inputs],
    }
    return (
        _parse(OwnerBinding, data)
        if attempt.module_id == "CP-1B"
        else _parse(FinancialBinding, data)
    )


def _historical(store: Execution, binding: FinancialBinding | OwnerBinding) -> _FrozenExecution:
    snapshot = _snapshot(store, binding.snapshot_sha256)
    matches = [a for a in snapshot.attempts if a.ticket_id == binding.ticket_id]
    if len(matches) != 1:
        raise OwnerError("identity_mismatch")
    attempt = matches[0]
    chain = (
        ("source_readiness",)
        if attempt.module_id == "CP-0"
        else (("earnings_delta",) if attempt.module_id == "CP-1B" else CP1_PROMOTION)
    )
    if (
        _binding(snapshot, attempt, binding.step_id) != binding
        or attempt.status != "pending"
        or attempt.issues
        or attempt.interruption is not None
        or attempt.payload_sha256 is not None
        or attempt.result_sha256 is not None
        or current_inputs(snapshot, attempt.module_id) != attempt.inputs
        or tuple(s.step_id for s in attempt.steps) != chain[: len(attempt.steps)]
        or any(s.status != "valid" for s in attempt.steps)
        or len(attempt.steps) >= len(chain)
        or chain[len(attempt.steps)] != binding.step_id
    ):
        raise OwnerError("identity_mismatch")
    return _FrozenExecution(store, snapshot)
