"""Which runs the Issuer Library lists, and what it shows for each. Reads files only.

A run folder under ``runs/`` is listed when CP-OS completed it and every module in it ran on the
current methodology:

- completed: a ``completed-<sha256>.json`` record named by its own hash, of the launcher's report
  kind, names a ``delivery-<sha256>.json`` manifest named by its own hash. One folder under
  ``deliveries/`` holds exactly the files its ``delivery.json`` lists, with those hashes, and its
  ``report.html`` has the hash the completion record states. The handoffs the manifest names
  still have their hashes, and the manifest, the delivery's ``view.json`` and ``workflow.json``
  name the same run. The report is not rebuilt: a renderer change since the run does not unlist it.
- current methodology: each module was answered in this run (not replayed from another run, not
  synthetic). The request record beside its accepted answer still has the fingerprint CP-OS named
  its folder by (``cpos.request_fingerprint``), so it holds the instructions actually sent, and
  their method block is exactly the one the launcher sends that module today
  (``cpos_launch.method_text``): no section changed, added or dropped.

Every other run folder is left out with its reason. Nothing here runs analysis, calls a provider
or writes a file.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

from deploy_workflow.reader_summary import TABLES, reader_tables

REPORT_KIND = "cpos-markdown-delivery/1"
MAX_FILE_BYTES = 64 << 20  # The library's one file limit, as in its discovery contract.
ANSWERED = frozenset({"live-provider", "host-session"})
EXECUTION_WORDS = {
    "live-provider": "Model provider",
    "host-session": "Host session",
    "retained-response-replay": "Reused from an earlier run",
    "synthetic": "Synthetic",
}
_COMPLETED = re.compile(r"^completed-([0-9a-f]{64})\.json$")
_RESPONSE = re.compile(r"^requests/([A-Z0-9-]+)/([0-9a-f]{64})/([1-9][0-9]*)\.response\.md$")
_HEADING = re.compile(r"^=== (\S+) sha256 [0-9a-f]{64} ===$", re.MULTILINE)
_SHA = re.compile(r"^[0-9a-f]{64}$")
_IDENTITY = ("run_id", "issuer_id", "issuer_name", "as_of", "pathway")

MethodText = Callable[[str], str | None]  # The current method block for a module, None if unknown.
MethodHeadings = Callable[[str], list[tuple[str, str]]]  # (section name, heading with its sha256)


class Refused(ValueError):
    """Why one run folder is not listed."""


@dataclass
class Library:
    runs: list[dict[str, Any]] = field(default_factory=list)
    excluded: list[tuple[str, str]] = field(default_factory=list)  # (run folder, reason)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_inside(folder: Path, relative: str) -> bytes:
    """A regular file at ``relative`` below ``folder``; no absolute path, ``..``, link or hidden
    name on the way, and at most ``MAX_FILE_BYTES``."""
    # Split the text itself: PurePosixPath would drop "." and empty segments before they are seen.
    parts = relative.split("/")
    if "\\" in relative or any(not part or part.startswith(".") for part in parts):
        raise Refused(f"{relative!r} is not a path inside the run")
    path = folder
    for part in parts:
        path = path / part
        try:
            mode = os.lstat(path).st_mode
        except OSError as error:
            raise Refused(f"{relative} is missing") from error
        if stat.S_ISLNK(mode):
            raise Refused(f"{relative} is a link")
    if not stat.S_ISREG(mode):
        raise Refused(f"{relative} is not a file")
    if os.stat(path).st_size > MAX_FILE_BYTES:
        raise Refused(f"{relative} is larger than 64 MiB")
    return path.read_bytes()


def read_pinned(folder: Path, relative: str, digest: object) -> bytes:
    raw = read_inside(folder, relative)
    if not isinstance(digest, str) or sha256(raw) != digest:
        raise Refused(f"{relative} no longer has its recorded sha256")
    return raw


def json_object(raw: bytes, name: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refused(f"{name} is not valid JSON") from error
    if not isinstance(value, dict):
        raise Refused(f"{name} is not a JSON object")
    return value


def completion_records(folder: Path) -> list[tuple[str, dict[str, Any]]]:
    """Each ``completed-<sha256>.json`` whose content has the hash its name states."""
    records = []
    for entry in sorted(os.listdir(folder)):
        match = _COMPLETED.match(entry)
        if not match:
            continue
        raw = read_inside(folder, entry)
        if sha256(raw) != match[1]:
            raise Refused(f"{entry} does not have the sha256 its name states")
        records.append((entry, json_object(raw, entry)))
    return records


def report_completion(folder: Path) -> dict[str, Any]:
    """The one completion record of the launcher's report kind."""
    records = completion_records(folder)
    if not records:
        raise Refused("not completed: no completion record")
    reports = [record for _, record in records if record.get("kind") == REPORT_KIND]
    if not reports:
        kinds = sorted({str(record.get("kind")) for _, record in records})
        raise Refused(f"not a report run of the current launcher (completion kind {kinds})")
    if len(reports) > 1:
        raise Refused("more than one report completion record; the current one is ambiguous")
    return reports[0]


def delivery_folder(folder: Path, report_sha256: str) -> tuple[str, Mapping[str, str]]:
    """The folder under ``deliveries/`` holding exactly its listed files and the stated report."""
    deliveries = folder / "deliveries"
    names = sorted(os.listdir(deliveries)) if deliveries.is_dir() else []
    for name in names:
        relative = f"deliveries/{name}"
        if name.startswith(".") or not os.path.lexists(folder / relative / "delivery.json"):
            continue  # Not a delivery: it has no receipt.
        receipt = json_object(read_inside(folder, f"{relative}/delivery.json"), "delivery.json")
        files = receipt.get("files")
        if not isinstance(files, dict) or files.get("report.html") != report_sha256:
            continue
        # Exactly, as CP-OS checks a publication: hidden entries count too.
        if set(os.listdir(folder / relative)) != set(files) | {"delivery.json"}:
            raise Refused(f"{relative} does not hold exactly the files its delivery.json lists")
        for entry, digest in files.items():
            read_pinned(folder, f"{relative}/{entry}", digest)
        return relative, files
    raise Refused("no delivery folder holds the report the completion record names")


def run_identity(run: Mapping[str, Any]) -> dict[str, str]:
    """The run's identity from ``workflow.json``: each part a non-empty string."""
    for key in _IDENTITY:
        if not isinstance(run.get(key), str) or not run[key].strip():
            raise Refused(f"workflow.json does not state the run's {key}")
    return {key: run[key] for key in _IDENTITY}


def same_identity(other: object, identity: Mapping[str, str], what: str) -> None:
    if not isinstance(other, dict):
        raise Refused(f"{what} does not name its run")
    for key, value in identity.items():
        if other.get(key) != value:
            raise Refused(f"{what} names a different run ({key})")


def verified_delivery(folder: Path, completion: Mapping[str, Any]) -> dict[str, Any]:
    """The checked delivery: its manifest, folder, report hash and handoffs."""
    manifest_sha = completion.get("delivery_manifest_sha256")
    report_sha = completion.get("report_sha256")
    if not isinstance(manifest_sha, str) or not _SHA.match(manifest_sha):
        raise Refused("the completion record names no delivery manifest")
    if not isinstance(report_sha, str) or not _SHA.match(report_sha):
        raise Refused("the completion record names no report")
    name = f"delivery-{manifest_sha}.json"
    manifest = json_object(read_pinned(folder, name, manifest_sha), name)
    relative, files = delivery_folder(folder, report_sha)
    view = json_object(read_inside(folder, f"{relative}/view.json"), "view.json")
    handoffs, modules = manifest.get("handoffs"), completion.get("modules")
    execution = completion.get("module_execution")
    if not isinstance(handoffs, dict) or not isinstance(modules, dict) or not modules:
        raise Refused("the delivery records no handoffs")
    if (
        not isinstance(execution, dict)
        or set(handoffs) != set(modules)
        or set(modules) != set(execution)
    ):
        raise Refused("the completion record and the delivery manifest name different modules")
    for module, path in modules.items():
        pin = handoffs[module]
        if not isinstance(pin, dict) or pin.get("path") != path:
            raise Refused(f"the delivery does not record {module}'s handoff")
        read_pinned(folder, str(path), pin.get("sha256"))
        if files.get(f"{module}.md") != pin["sha256"]:
            raise Refused(f"the delivery's copy of {module}'s handoff is not the one it names")
    return {
        "manifest": manifest,
        "view": view,
        "folder": relative,
        "report_sha256": report_sha,
        "handoffs": {m: handoffs[m] for m in modules},
    }


def sent_instructions(folder: Path, module: str, response: str, identity: Mapping[str, str]) -> str:
    """The instructions a module's accepted answer was given, from the request record beside it.

    CP-OS named the request folder by the fingerprint of the request's inputs, and the completion
    record names the answer in that folder, so a record that still has that fingerprint is the
    request actually sent.
    """
    from deploy_workflow.owners.cpos import request_fingerprint

    match = _RESPONSE.match(response)
    if not match or match[1] != module:
        raise Refused(f"{module}: its answer is not in a CP-OS request folder")
    relative = f"requests/{module}/{match[2]}/{match[3]}.request.json"
    request = json_object(read_inside(folder, relative), relative)
    inputs = {key: value for key, value in request.items() if key not in {"attempt", "feedback"}}
    if request.get("attempt") != int(match[3]) or request_fingerprint(inputs) != match[2]:
        raise Refused(f"{relative} is not the request its folder was named for")
    if request.get("module_id") != module or request.get("retained_response_sha256") is not None:
        raise Refused(f"{relative} is not a request answered in this run")
    same_identity(request.get("run"), identity, f"the {module} request")
    instructions = request.get("instructions")
    if not isinstance(instructions, str):
        raise Refused(f"{relative} records no instructions")
    return instructions


def method_difference(block: str, module: str, headings: MethodHeadings) -> str:
    """Which method sections differ between what was sent and what is selected today."""
    sent = set(_HEADING.findall(block))
    current = headings(module)
    changed = [name for name, heading in current if heading not in block]
    dropped = sorted(sent - {name for name, _ in current})
    parts = [f"{', '.join(changed)} changed"] if changed else []
    parts += [f"{', '.join(dropped)} no longer selected"] if dropped else []
    return "; ".join(parts) or "method text changed"


def check_methodology(
    folder: Path,
    delivered: Mapping[str, Any],
    execution: Mapping[str, Any],
    identity: Mapping[str, str],
    method: tuple[MethodText, MethodHeadings],
) -> None:
    """Refuse unless every module was answered here on exactly the method it would be sent today."""
    from deploy_workflow.owners.cpos_launch import METHOD_MARK

    method_text, method_headings = method
    for module, pin in delivered["handoffs"].items():
        how = execution.get(module)
        if how not in ANSWERED:
            word = EXECUTION_WORDS.get(str(how), f"recorded as {how!r}")
            raise Refused(f"{module}: {word.lower()}; its methodology is not this run's")
        current = method_text(module)
        if current is None:
            raise Refused(f"{module}: no current method is selected for this module")
        text = sent_instructions(folder, module, pin["path"], identity).replace("\r\n", "\n")
        _, mark, block = text.partition(METHOD_MARK)
        if not mark or block != current + "\n":
            detail = method_difference(block, module, method_headings)
            raise Refused(f"{module}: not on the current methodology ({detail})")


def reader_summary(text: str) -> dict[str, Any] | None:
    """The handoff's own reader tables, verbatim; None when they are not in the expected form."""
    tables = reader_tables(text)
    if len(tables) < 2 or tuple(tables[0][0]) != TABLES[0] or tuple(tables[1][0]) != TABLES[1]:
        return None
    if len(tables[0]) != 2 or any(len(row) != 3 for row in tables[0] + tables[1]):
        return None
    bottom, confidence, limitation = tables[0][1]
    findings = [{"finding": f, "impact": i, "confidence": c} for f, i, c in tables[1][1:]]
    return {
        "bottom_line": bottom,
        "confidence": confidence,
        "limitation": limitation,
        "findings": findings,
    }


def decimal_text(value: object) -> Decimal | None:
    if not isinstance(value, str):
        return None
    try:
        amount = Decimal(value)
    except InvalidOperation:
        return None
    return amount if amount.is_finite() else None


def call_records(folder: Path) -> list[dict[str, Any]]:
    """The run's model-call records; an unreadable line is kept as an empty record."""
    try:
        raw = read_inside(folder, "live/calls.jsonl")
    except Refused:
        return []
    calls = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            value = {}
        calls.append(value if isinstance(value, dict) else {})
    return calls


def execution_record(folder: Path) -> dict[str, Any]:
    """Model, effort, spend and start time, as the run's own call records state them."""
    calls = call_records(folder)
    try:
        loop = json_object(read_inside(folder, "live/loop.json"), "loop.json")
    except Refused:
        loop = {}
    settled = [decimal_text(call.get("settled_usd")) for call in calls]
    known = [amount for amount in settled if amount is not None]
    models = sorted(
        {
            f"{call.get('reported_model') or call.get('requested_model')}"
            f" · {call.get('requested_effort')}"
            for call in calls
            if call.get("reported_model") or call.get("requested_model")
        }
    )
    started = sorted(str(c["started_at"]) for c in calls if isinstance(c.get("started_at"), str))
    return {
        "config": loop.get("config") if isinstance(loop.get("config"), str) else None,
        "models": models,
        "calls": len(calls),
        "spend_usd": format(sum(known, Decimal(0)), "f") if calls else None,
        "unknown_charges": len(settled) - len(known),
        "started_at": started[0] if started else None,
    }


def text_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def link(page_dir: Path, target: Path) -> str:
    return quote(PurePosixPath(Path(os.path.relpath(target, page_dir))).as_posix(), safe="/")


def module_titles() -> dict[str, str]:
    from deploy_vii.registry import modules

    return {module.module_id: module.title for module in modules()}


def module_entries(
    folder: Path, page_dir: Path, delivered: Mapping[str, Any], execution: Mapping[str, Any]
) -> list[dict[str, Any]]:
    titles = module_titles()
    entries = []
    for module, pin in delivered["handoffs"].items():
        raw = read_inside(folder, pin["path"])
        entries.append(
            {
                "id": module,
                "title": titles.get(module, module),
                "execution": EXECUTION_WORDS.get(str(execution.get(module)), "Not recorded"),
                "href": link(page_dir, folder / pin["path"]),
                "sha256": pin["sha256"],
                "summary": reader_summary(raw.decode("utf-8", errors="replace")),
            }
        )
    return entries


def admit_run(
    folder: Path, page_dir: Path, method: tuple[MethodText, MethodHeadings]
) -> dict[str, Any]:
    """The run's library record, or ``Refused`` with the reason it is not listed."""
    if not os.path.lexists(folder / "workflow.json"):
        raise Refused("not a CP-OS launcher run (no workflow.json)")
    workflow = json_object(read_inside(folder, "workflow.json"), "workflow.json")
    run = workflow.get("run")
    if not isinstance(run, dict):
        raise Refused("workflow.json names no run")
    identity = run_identity(run)
    completion = report_completion(folder)
    delivered = verified_delivery(folder, completion)
    same_identity(delivered["manifest"].get("run"), identity, "the delivery manifest")
    same_identity(delivered["view"].get("run"), identity, "the delivered report")
    execution = completion["module_execution"]
    check_methodology(folder, delivered, execution, identity, method)
    report = folder / delivered["folder"] / "report.html"
    requested = run.get("requested_modules")
    cap = completion.get("provider_cap_usd")
    return {
        "id": folder.name,
        **identity,
        **{key: text_or_none(run.get(key)) for key in ("case_kind", "method_version")},
        "requested_modules": [m for m in requested if isinstance(m, str)]
        if isinstance(requested, list)
        else [],
        "modules": module_entries(folder, page_dir, delivered, execution),
        "scope": text_or_none(completion.get("scope")) or "",
        "cap_usd": cap if decimal_text(cap) is not None else None,
        "report": {"href": link(page_dir, report), "sha256": delivered["report_sha256"]},
        "execution": execution_record(folder),
    }


def mark_latest(runs: list[dict[str, Any]]) -> None:
    """Flag each issuer's latest evidence date; runs sharing that date are all flagged and counted.
    A run with no as-of date is never the latest."""
    latest: dict[str, str] = {}
    for run in runs:
        as_of = run.get("as_of")
        if isinstance(as_of, str) and as_of > latest.get(run["issuer_id"], ""):
            latest[run["issuer_id"]] = as_of
    for run in runs:
        flagged = isinstance(run.get("as_of"), str) and latest.get(run["issuer_id"]) == run["as_of"]
        run["latest"] = flagged
        run["latest_shared_with"] = (
            sum(
                1
                for other in runs
                if other is not run
                and other["issuer_id"] == run["issuer_id"]
                and other.get("as_of") == run["as_of"]
            )
            if flagged
            else 0
        )


def current_method() -> tuple[MethodText, MethodHeadings]:
    """The launcher's own definition of each module's current method."""
    from deploy_workflow.owners.cpos_launch import (
        METHODS,
        method_heading,
        method_sections,
        method_text,
    )

    def text(module: str) -> str | None:
        return method_text(module) if module in METHODS else None

    def headings(module: str) -> list[tuple[str, str]]:
        sections = method_sections(module) if module in METHODS else []
        return [(name, method_heading(name, body)) for name, body in sections]

    return text, headings


def build_library(
    workspace: Path, page_dir: Path, method: tuple[MethodText, MethodHeadings] | None = None
) -> Library:
    """Every run folder in ``workspace/runs``, listed or left out with its reason."""
    method = method or current_method()
    library = Library()
    runs_dir = workspace / "runs"
    names = sorted(os.listdir(runs_dir)) if runs_dir.is_dir() else []
    for name in names:
        folder = runs_dir / name
        # A name the file system could not decode is shown with replacement characters.
        shown = name.encode("utf-8", "surrogateescape").decode("utf-8", "replace")
        if name.startswith(".") or not (folder.is_symlink() or folder.is_dir()):
            continue  # Hidden entries and plain files are not run folders.
        if folder.is_symlink():
            library.excluded.append((shown, "a link to another folder; not followed"))
            continue
        try:
            library.runs.append(admit_run(folder, page_dir, method))
        except Refused as error:
            library.excluded.append((shown, str(error)))
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
            # One unreadable folder must not stop the others from being listed.
            library.excluded.append((shown, f"unreadable run record ({type(error).__name__})"))
    mark_latest(library.runs)
    # Issuer A to Z; within an issuer the latest evidence date first, then the run folder.
    library.runs.sort(key=lambda r: r["id"])
    library.runs.sort(key=lambda r: str(r.get("as_of") or ""), reverse=True)
    library.runs.sort(key=lambda r: str(r.get("issuer_name") or ""))
    return library
