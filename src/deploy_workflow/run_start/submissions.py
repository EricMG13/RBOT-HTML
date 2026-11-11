"""Submissions: an analyst's uploaded files, the limits on them, the offline summary and the digest.

The start page's service is reachable from other machines, so every name and length that arrives
here is hostile. A name is cut into parts, each part is made safe, and nothing is ever joined into
a path outside the submission's own ``files`` folder. A refusal leaves no file behind.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import secrets
import shutil
import tempfile
import threading
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, BinaryIO, TypedDict

from deploy_workflow.context import load_context
from deploy_workflow.inbox.drops import Layout
from deploy_workflow.inbox.filing import safe_name
from deploy_workflow.owners.cpos_launch import LaunchRefused, prepare, read_documents

MAX_FILE = 50 * 1024 * 1024
MAX_FILES = 500
MAX_TOTAL = 512 * 1024 * 1024
STALE_SECONDS = 24 * 3600
# Ceiling on unsubmitted submissions at once: a peer cannot make more folders than this.
MAX_OPEN = 50
# Ceiling on the bytes held by all unsubmitted uploads together (stored plus in flight), so the
# per-submission limits cannot add up to more than this on disk.
MAX_STORE = 5 * 1024**3
_MAX_DEPTH = 8
_CHUNK = 1024 * 1024
_ID = re.compile(r"[0-9a-f]{32}")
_DRIVE = re.compile(r"[A-Za-z]:")
_CONTEXT_NAME = "context.json"
_MODULES_AT_MOST = 40
_MODULE_NAME_AT_MOST = 12
_TURNS = (1, 64)
_LEVELS = ("basic", "standard", "advanced")
_SUBMITTER_AT_MOST = 80
_KEYS = {"context", "modules", "max_turns", "level", "submitted_by"}
_CHANGED = "the documents changed while the summary was being made; open the summary again"

log = logging.getLogger(__name__)

# One lock for the whole process: it guards the limit checks and the reservations of uploads still
# being written. Ceiling: it does not see a second service process on the same root, so the count
# and total limits hold per process only; the service runs as one process.
_LOCK = threading.Lock()
# Ceiling: one summary at a time. A summary re-reads every file and writes converted copies under
# the state folder, so parallel requests would multiply that disk and CPU use.
_SUMMARY_LOCK = threading.Lock()
_PENDING: dict[str, dict[str, tuple[str, int]]] = {}  # sid -> temporary name -> (stored name, size)


class Refused(ValueError):
    """The upload or request cannot be accepted; the message says why."""


class Answers(TypedDict):
    context: dict[str, Any]  # a context/1 object, as the page's build() makes it
    modules: list[str]  # [] = the pathway's modules
    max_turns: int  # 32 unless Advanced changes it
    level: str  # "basic" | "standard" | "advanced"
    submitted_by: str


def validated(answers: object) -> Answers:
    """``answers`` as an ``Answers``, or ``Refused`` with a plain sentence."""
    if not isinstance(answers, dict) or set(answers) != _KEYS:
        raise Refused(f"the answers need exactly these parts: {', '.join(sorted(_KEYS))}")
    if not isinstance(answers["context"], dict):
        raise Refused("the context must be an object")
    modules = answers["modules"]
    if not isinstance(modules, list) or len(modules) > _MODULES_AT_MOST:
        raise Refused(f"modules must be a list of at most {_MODULES_AT_MOST} names")
    if not all(isinstance(m, str) and len(m) <= _MODULE_NAME_AT_MOST for m in modules):
        raise Refused(f"each module name is text of at most {_MODULE_NAME_AT_MOST} characters")
    turns = answers["max_turns"]
    if not isinstance(turns, int) or isinstance(turns, bool) or not _TURNS[0] <= turns <= _TURNS[1]:
        raise Refused(f"max_turns is a whole number from {_TURNS[0]} to {_TURNS[1]}")
    if answers["level"] not in _LEVELS:
        raise Refused(f"level is one of {', '.join(_LEVELS)}")
    by = answers["submitted_by"]
    if not isinstance(by, str) or len(by) > _SUBMITTER_AT_MOST:
        raise Refused(f"submitted_by is text of at most {_SUBMITTER_AT_MOST} characters")
    return answers  # type: ignore[return-value]


def _open_folders(layout: Layout) -> list[Path]:
    """The unsubmitted submissions: an id folder with no ``sealed`` folder."""
    if not layout.uploads.is_dir():
        return []
    return [
        entry
        for entry in layout.uploads.iterdir()
        if _ID.fullmatch(entry.name)
        and not entry.is_symlink()
        and entry.is_dir()
        and not (entry / "sealed").exists()
    ]


def new(layout: Layout) -> str:
    """A fresh submission: 32 hex characters, with an empty ``uploads/<id>/files``."""
    sid = secrets.token_hex(16)
    with _LOCK:
        if len(_open_folders(layout)) >= MAX_OPEN:
            raise Refused("too many unfinished submissions; try again later")
        (layout.uploads / sid / "files").mkdir(parents=True)
    return sid


def _folder(layout: Layout, sid: str) -> Path:
    if not isinstance(sid, str) or not _ID.fullmatch(sid):
        raise Refused("unknown submission")
    folder = layout.uploads / sid
    if folder.is_symlink():
        raise Refused("unknown submission")
    for name in ("sealed", "files"):
        inside = folder / name
        if inside.is_dir() and not inside.is_symlink():
            return folder
    raise Refused("unknown submission")


def _is_sealed(folder: Path) -> bool:
    return (folder / "sealed").is_dir()


def _active(folder: Path) -> Path:
    return folder / ("sealed" if _is_sealed(folder) else "files")


def files_folder(layout: Layout, sid: str) -> Path:
    return _active(_folder(layout, sid))


def seal(layout: Layout, sid: str) -> Path:
    """Freeze the uploads: ``files`` becomes ``sealed`` and no upload or removal is accepted."""
    folder = _folder(layout, sid)
    with _LOCK:
        if _is_sealed(folder):
            return folder / "sealed"
        if _PENDING.get(sid):
            raise Refused("an upload is still in progress")
        os.rename(folder / "files", folder / "sealed")
    return folder / "sealed"


def unseal(layout: Layout, sid: str) -> None:
    """Put a sealed submission's uploads back; nothing happens when it is not sealed."""
    folder = _folder(layout, sid)
    with _LOCK:
        if _is_sealed(folder):
            if (folder / "files").exists():
                raise Refused("this submission has uploads that a seal would overwrite")
            os.rename(folder / "sealed", folder / "files")


def _parts(name: str) -> list[str]:
    """The safe parts of an uploaded name, or ``Refused``."""
    if not isinstance(name, str) or not name:
        raise Refused("a file needs a name")
    try:
        name.encode("utf-8")
    except UnicodeEncodeError:
        raise Refused("a file name must be valid text") from None
    raw = re.split(r"[/\\]", name)
    if _DRIVE.fullmatch(raw[0]):  # "C:" is the first part of "C:\x" once split
        raise Refused(f"{name!r} starts with a drive letter")
    if len(raw) > _MAX_DEPTH:
        raise Refused(f"{name!r} is nested more than {_MAX_DEPTH} folders deep")
    for part in raw:
        if part.strip() in ("", ".", ".."):
            raise Refused(f"{name!r} has an empty, '.' or '..' part")
    parts = [safe_name(part) for part in raw]
    if len(parts) == 1 and parts[0].casefold() == _CONTEXT_NAME:
        raise Refused("context.json is made from the answers, not uploaded")
    return parts


def _stored(root: Path, *, strict: bool = False) -> dict[str, int]:
    """Relative posix name -> size of each regular file under ``root``; links are not followed.

    With ``strict`` a link anywhere under ``root`` is a ``Refused``: the launcher follows links and
    the digest does not, so a link would let bytes change without the digest changing."""
    found: dict[str, int] = {}
    for here, dirs, names in os.walk(root, followlinks=False):
        linked = [d for d in dirs if (Path(here) / d).is_symlink()]
        if strict and linked:
            raise Refused(f"{linked[0]!r} is a link, not an uploaded file")
        dirs[:] = [d for d in dirs if not (Path(here) / d).is_symlink()]
        for n in names:
            path = Path(here) / n
            if path.is_symlink():
                if strict:
                    raise Refused(f"{n!r} is a link, not an uploaded file")
                continue
            found[path.relative_to(root).as_posix()] = path.lstat().st_size
    return found


def _touch(folder: Path) -> None:
    os.utime(folder)  # a submission's age is its last change; the sweep reads it


def _usable_root(folder: Path) -> Path:
    """``folder/files`` when it is a real, unsealed folder; call with ``_LOCK`` held."""
    if _is_sealed(folder):
        raise Refused("this submission has been submitted")
    root = folder / "files"
    if folder.is_symlink() or root.is_symlink() or not root.is_dir():
        raise Refused("unknown submission")
    return root


def _refuse_links(root: Path, parts: list[str]) -> None:
    """``Refused`` when any existing part of ``root/parts`` is a link."""
    here = root
    for part in parts:
        here = here / part
        if here.is_symlink():
            raise Refused(f"{'/'.join(parts)!r} goes through a link")
        if not here.exists():
            return


def _reserve(layout: Layout, folder: Path, sid: str, stored: str, length: int) -> str:
    """Check the limits against what is stored and in flight; record the reservation."""
    tmp = f".part-{uuid.uuid4().hex}"
    with _LOCK:
        root = _usable_root(folder)
        parts = stored.split("/")
        _refuse_links(root, parts)
        existing = _stored(root)
        own = _PENDING.get(sid, {})
        count = len(set(existing) - {stored}) + len(own) + 1
        total = sum(v for k, v in existing.items() if k != stored)
        total += sum(size for _, size in own.values()) + length
        if count > MAX_FILES:
            raise Refused(f"more than {MAX_FILES} files")
        if total > MAX_TOTAL:
            raise Refused(f"more than {MAX_TOTAL // (1024 * 1024)} MB in total")
        store = total + sum(
            size for other, held in _PENDING.items() if other != sid for _, size in held.values()
        )
        for other in _open_folders(layout):
            if other != folder and not (other / "files").is_symlink():
                store += sum(_stored(other / "files").values())
        if store > MAX_STORE:
            raise Refused("the service's storage for uploads is full; try again later")
        _PENDING.setdefault(sid, {})[tmp] = (stored, length)
    return tmp


def _write(body: BinaryIO, target: Path, length: int) -> None:
    with target.open("xb") as out:
        left = length
        while left:
            chunk = body.read(min(_CHUNK, left))
            if not chunk:
                raise Refused(f"the upload ended {left} bytes short of its {length}")
            out.write(chunk)
            left -= len(chunk)


def _place(folder: Path, parts: list[str], temp_path: Path) -> None:
    """Move a finished upload into ``files``; the folder creation and the rename are one step."""
    with _LOCK:
        root = _usable_root(folder)
        _refuse_links(root, parts)
        target = root.joinpath(*parts)
        stored = "/".join(parts)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir():
                raise Refused(f"{stored!r} is already a folder")
            os.replace(temp_path, target)
        except (NotADirectoryError, FileExistsError) as error:
            raise Refused(f"{stored!r} clashes with a file or folder already stored") from error


def add_file(layout: Layout, sid: str, name: str, body: BinaryIO, length: int) -> str:
    """Store ``length`` bytes from ``body`` under a safe version of ``name``; return that name.

    The bytes go to a temporary name in the submission folder and are renamed into place on
    success, so a refusal or a cut-off upload leaves nothing behind. A name already stored is
    replaced."""
    folder = _folder(layout, sid)
    if _is_sealed(folder):
        raise Refused("this submission has been submitted")
    parts = _parts(name)
    if not isinstance(length, int) or isinstance(length, bool) or length < 0:
        raise Refused("the upload has no valid length")
    if length > MAX_FILE:
        raise Refused(f"a file is at most {MAX_FILE // (1024 * 1024)} MB")
    stored = "/".join(parts)
    tmp = _reserve(layout, folder, sid, stored, length)
    temp_path = folder / tmp
    try:
        _write(body, temp_path, length)
        _place(folder, parts, temp_path)
    finally:
        temp_path.unlink(missing_ok=True)
        with _LOCK:
            held = _PENDING.get(sid, {})
            held.pop(tmp, None)
            if not held:
                _PENDING.pop(sid, None)
    _touch(folder)
    return stored


def remove_file(layout: Layout, sid: str, name: str) -> None:
    folder = _folder(layout, sid)
    parts = _parts(name)
    with _LOCK:
        root = _usable_root(folder)
        _refuse_links(root, parts)
        target = root.joinpath(*parts)
        if not target.is_file():
            raise Refused(f"{'/'.join(parts)!r} is not stored")
        target.unlink()
        for parent in target.parents:  # no empty folder is left where a file was
            if parent == root or any(parent.iterdir()):
                break
            parent.rmdir()
    _touch(folder)


def reading(layout: Layout, sid: str) -> dict[str, Any]:
    """What the launcher makes of each uploaded file; its refusal comes back as ``error``."""
    root = files_folder(layout, sid)
    try:
        _stored(root, strict=True)
        got = read_documents(root)
    except (LaunchRefused, Refused) as refusal:
        return {"documents": [], "ignored": [], "error": str(refusal)}
    return {"documents": list(got.documents), "ignored": list(got.ignored), "error": ""}


def context_bytes(answers: Answers) -> bytes:
    text = json.dumps(answers["context"], indent=2, ensure_ascii=False) + "\n"
    try:
        return text.encode("utf-8")
    except UnicodeEncodeError:
        raise Refused("the context holds text that cannot be stored (a lone surrogate)") from None


def _digest(root: Path, answers: Answers) -> str:
    files = []
    for rel in sorted(_stored(root, strict=True)):
        sha = hashlib.sha256()
        with (root / rel).open("rb") as stream:
            while chunk := stream.read(_CHUNK):
                sha.update(chunk)
        files.append([rel, sha.hexdigest()])
    covered = {
        "context": hashlib.sha256(context_bytes(answers)).hexdigest(),
        "files": files,
        "modules": list(answers["modules"]),
        "max_turns": answers["max_turns"],
    }
    text = json.dumps(covered, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def digest(layout: Layout, sid: str, answers: Answers) -> str:
    """SHA-256 over the context, each stored file's name and hash, the modules and the turns.

    ``level`` and ``submitted_by`` are not covered: they change what the page shows, not the run."""
    return _digest(files_folder(layout, sid), validated(answers))


def _remove(folder: Path) -> None:
    # Fail-open by design: the caller's result is correct whether or not the folder goes, and
    # ``sweep`` removes state/summary-* and stale uploads/<id> folders again, so a leftover is
    # retried. The failure is logged with the folder's name, not hidden.
    try:
        shutil.rmtree(folder)
    except OSError as error:
        log.warning("could not remove %s (%s); the sweep will try again", folder, error)


_ISSUED = "issued"


def issued(layout: Layout, sid: str) -> str:
    """The digest the latest summary of this submission returned; empty when there is none."""
    path = _folder(layout, sid) / _ISSUED
    if path.is_symlink():
        return ""
    try:
        return path.read_text(encoding="ascii", errors="replace").strip()
    except FileNotFoundError:
        return ""


def _record_issued(layout: Layout, sid: str, value: str) -> None:
    """Replace the submission's issued digest with ``value`` (none when empty), under the lock."""
    folder = _folder(layout, sid)
    with _LOCK:
        path = folder / _ISSUED
        if not value:
            path.unlink(missing_ok=True)
            return
        temp = folder / f".issued-{uuid.uuid4().hex}"
        try:
            temp.write_text(value + "\n", encoding="ascii")
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)


def summary(
    layout: Layout, sid: str, answers: Answers, *, config: str, cap: Decimal
) -> dict[str, Any]:
    """The launcher's own forecast for these files and answers, with the digest to approve.

    The digest it returns is the one approval this service will accept for the submission: it is
    recorded in ``uploads/<id>/issued``, replaced by each later summary and removed when a summary
    returns an error. The context is written to a temporary folder and the run folder is another
    one; both are under the state folder, never in the files, and both are removed. A refusal
    comes back as ``error`` with no digest, and so does a change to the documents while the
    forecast was being made."""
    result = _summarise(layout, sid, answers, config=config, cap=cap)
    digest_issued = result.get("digest", "")
    try:
        _record_issued(layout, sid, digest_issued)
    except Refused:
        if digest_issued:  # a digest was made for a submission that is not there: not possible
            raise
        # An error answer for an unknown submission has no issued digest to clear; the answer
        # (the refusal text) is still returned unchanged.
    return result


def _summarise(
    layout: Layout, sid: str, answers: Answers, *, config: str, cap: Decimal
) -> dict[str, Any]:
    try:
        answers = validated(answers)
    except Refused as refusal:
        return {"error": str(refusal)}
    files = files_folder(layout, sid)
    with _SUMMARY_LOCK:
        layout.state.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="summary-", dir=layout.state))
        try:
            try:
                before = _digest(files, answers)
                load_context(context_bytes(answers))
                context_dir = work / "context"
                context_dir.mkdir()
                context = context_dir / _CONTEXT_NAME
                context.write_bytes(context_bytes(answers))
                prepared = prepare(
                    context,
                    files,
                    work / "run",
                    config=config,
                    cap=cap,
                    modules=answers["modules"] or None,
                )
                after = _digest(files, answers)
            except ValueError as refusal:  # Refused, ContextRefused and LaunchRefused included
                return {"error": str(refusal)}
            if before != after:
                return {"error": _CHANGED}
            return {
                "digest": after,
                "error": "",
                "modules": list(prepared.ordered),
                "items": list(prepared.expectations),
                "documents": list(prepared.documents),
                "ignored": list(prepared.ignored),
                "omitted": list(prepared.omitted),
            }
        finally:
            _remove(work)


def sweep(layout: Layout, now: float) -> None:
    """Delete each ``uploads/<id>`` and ``state/summary-*`` not modified for ``STALE_SECONDS``.

    A submission with an upload in flight is kept. Other entries are left."""
    if layout.uploads.is_dir():
        for entry in layout.uploads.iterdir():
            if not _ID.fullmatch(entry.name) or entry.is_symlink() or not entry.is_dir():
                continue
            with _LOCK:
                if _PENDING.get(entry.name):
                    continue
                if now - entry.stat().st_mtime >= STALE_SECONDS:
                    _remove(entry)
    if layout.state.is_dir():
        for entry in layout.state.iterdir():
            leftover = entry.name.startswith("summary-") and entry.is_dir()
            if leftover and not entry.is_symlink() and now - entry.stat().st_mtime >= STALE_SECONDS:
                _remove(entry)
