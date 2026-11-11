"""Submissions: an analyst's uploaded files, the limits on them, the offline summary and the digest.

The start page's service is reachable from other machines, so every name and length that arrives
here is hostile. A name is cut into parts, each part is made safe, and nothing is ever joined into
a path outside the submission's own ``files`` folder. A refusal leaves no file behind.
"""

from __future__ import annotations

import hashlib
import json
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

from deploy_workflow.context import ContextRefused, load_context
from deploy_workflow.inbox.drops import Layout
from deploy_workflow.inbox.filing import safe_name
from deploy_workflow.owners.cpos_launch import LaunchRefused, prepare, read_documents

MAX_FILE = 50 * 1024 * 1024
MAX_FILES = 500
MAX_TOTAL = 512 * 1024 * 1024
STALE_SECONDS = 24 * 3600
_MAX_DEPTH = 8
_CHUNK = 1024 * 1024
_ID = re.compile(r"[0-9a-f]{32}")
_DRIVE = re.compile(r"[A-Za-z]:")
_CONTEXT_NAME = "context.json"

# One lock for the whole process: it guards the limit checks and the reservations of uploads still
# being written. Ceiling: it does not see a second service process on the same root, so the count
# and total limits hold per process only; the service runs as one process.
_LOCK = threading.Lock()
_PENDING: dict[str, dict[str, tuple[str, int]]] = {}  # sid -> temporary name -> (stored name, size)


class Refused(ValueError):
    """The upload or request cannot be accepted; the message says why."""


class Answers(TypedDict):
    context: dict[str, Any]  # a context/1 object, as the page's build() makes it
    modules: list[str]  # [] = the pathway's modules
    max_turns: int  # 32 unless Advanced changes it
    level: str  # "basic" | "standard" | "advanced"
    submitted_by: str


def new(layout: Layout) -> str:
    """A fresh submission: 32 hex characters, with an empty ``uploads/<id>/files``."""
    sid = secrets.token_hex(16)
    (layout.uploads / sid / "files").mkdir(parents=True)
    return sid


def _folder(layout: Layout, sid: str) -> Path:
    if not isinstance(sid, str) or not _ID.fullmatch(sid):
        raise Refused("unknown submission")
    folder = layout.uploads / sid
    if folder.is_symlink() or not (folder / "files").is_dir():
        raise Refused("unknown submission")
    return folder


def files_folder(layout: Layout, sid: str) -> Path:
    return _folder(layout, sid) / "files"


def _parts(name: str) -> list[str]:
    """The safe parts of an uploaded name, or ``Refused``."""
    if not isinstance(name, str) or not name:
        raise Refused("a file needs a name")
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


def _stored(root: Path) -> dict[str, int]:
    """Relative posix name -> size of each regular file under ``root``; links are not followed."""
    found: dict[str, int] = {}
    for here, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(here) / d).is_symlink()]
        for n in names:
            path = Path(here) / n
            if not path.is_symlink():
                found[path.relative_to(root).as_posix()] = path.lstat().st_size
    return found


def _touch(folder: Path) -> None:
    os.utime(folder)  # a submission's age is its last change; the sweep reads it


def _reserve(sid: str, root: Path, stored: str, length: int) -> str:
    """Check the limits against what is stored and in flight; record the reservation."""
    tmp = f".part-{uuid.uuid4().hex}"
    with _LOCK:
        existing = _stored(root)
        pending = _PENDING.setdefault(sid, {})
        count = len(set(existing) - {stored}) + len(pending) + 1
        total = sum(v for k, v in existing.items() if k != stored)
        total += sum(size for _, size in pending.values()) + length
        if count > MAX_FILES:
            raise Refused(f"more than {MAX_FILES} files")
        if total > MAX_TOTAL:
            raise Refused(f"more than {MAX_TOTAL // (1024 * 1024)} MB in total")
        pending[tmp] = (stored, length)
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


def add_file(layout: Layout, sid: str, name: str, body: BinaryIO, length: int) -> str:
    """Store ``length`` bytes from ``body`` under a safe version of ``name``; return that name.

    The bytes go to a temporary name in the submission folder and are renamed into place on
    success, so a refusal or a cut-off upload leaves nothing behind. A name already stored is
    replaced."""
    folder = _folder(layout, sid)
    root = folder / "files"
    parts = _parts(name)
    if not isinstance(length, int) or isinstance(length, bool) or length < 0:
        raise Refused("the upload has no valid length")
    if length > MAX_FILE:
        raise Refused(f"a file is at most {MAX_FILE // (1024 * 1024)} MB")
    stored = "/".join(parts)
    tmp = _reserve(sid, root, stored, length)
    temp_path = folder / tmp
    try:
        _write(body, temp_path, length)
        target = root.joinpath(*parts)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir() or target.is_symlink():
                raise Refused(f"{stored!r} is already a folder")
            os.replace(temp_path, target)
        except (NotADirectoryError, FileExistsError) as error:
            raise Refused(f"{stored!r} clashes with a file or folder already stored") from error
    finally:
        temp_path.unlink(missing_ok=True)
        with _LOCK:
            _PENDING.get(sid, {}).pop(tmp, None)
            if not _PENDING.get(sid):
                _PENDING.pop(sid, None)
    _touch(folder)
    return stored


def remove_file(layout: Layout, sid: str, name: str) -> None:
    folder = _folder(layout, sid)
    root = folder / "files"
    parts = _parts(name)
    target = root.joinpath(*parts)
    if target.is_symlink() or not target.is_file():
        raise Refused(f"{'/'.join(parts)!r} is not stored")
    target.unlink()
    for parent in target.parents:  # no empty folder is left where a file was
        if parent == root or any(parent.iterdir()):
            break
        parent.rmdir()
    _touch(folder)


def reading(layout: Layout, sid: str) -> dict[str, Any]:
    """What the launcher makes of each uploaded file; its refusal comes back as ``error``."""
    try:
        got = read_documents(files_folder(layout, sid))
    except LaunchRefused as refusal:
        return {"documents": [], "ignored": [], "error": str(refusal)}
    return {"documents": list(got.documents), "ignored": list(got.ignored), "error": ""}


def context_bytes(answers: Answers) -> bytes:
    return (json.dumps(answers["context"], indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def digest(layout: Layout, sid: str, answers: Answers) -> str:
    """SHA-256 over the context, each stored file's name and hash, the modules and the turns.

    ``level`` and ``submitted_by`` are not covered: they change what the page shows, not the run."""
    root = files_folder(layout, sid)
    files = []
    for rel in sorted(_stored(root)):
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


def summary(
    layout: Layout, sid: str, answers: Answers, *, config: str, cap: Decimal
) -> dict[str, Any]:
    """The launcher's own forecast for these files and answers, with the digest to approve.

    The context is written to a temporary folder and the run folder is another one; both are under
    the state folder, never in the files, and both are removed. A refusal comes back as ``error``
    with no digest."""
    files = files_folder(layout, sid)
    layout.state.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="summary-", dir=layout.state))
    try:
        try:
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
        except (ContextRefused, LaunchRefused) as refusal:
            return {"error": str(refusal)}
        return {
            "digest": digest(layout, sid, answers),
            "error": "",
            "modules": list(prepared.ordered),
            "items": list(prepared.expectations),
            "documents": list(prepared.documents),
            "ignored": list(prepared.ignored),
            "omitted": list(prepared.omitted),
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)


def sweep(layout: Layout, now: float) -> None:
    """Delete each ``uploads/<id>`` not modified for ``STALE_SECONDS``; other entries are left."""
    if not layout.uploads.is_dir():
        return
    for entry in layout.uploads.iterdir():
        if not _ID.fullmatch(entry.name) or entry.is_symlink() or not entry.is_dir():
            continue
        if now - entry.stat().st_mtime >= STALE_SECONDS:
            shutil.rmtree(entry, ignore_errors=True)
