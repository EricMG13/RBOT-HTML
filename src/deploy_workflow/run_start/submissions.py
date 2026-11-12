"""Submissions: an analyst's uploaded files, the limits on them, the offline summary and the digest.

The start page's service is reachable from other machines, so every name and length that arrives
here is hostile. A name is cut into parts, each part is made safe, and nothing is ever joined into
a path outside the submission's own ``files`` folder. A refusal leaves no file behind.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import re
import secrets
import shutil
import tempfile
import threading
import unicodedata
import uuid
from collections.abc import Collection
from decimal import Decimal
from pathlib import Path
from typing import Any, BinaryIO, TypedDict

from deploy_workflow.context import load_context
from deploy_workflow.inbox.filing import safe_name
from deploy_workflow.inbox.layout import MAX_ISSUER_ID, Layout
from deploy_workflow.inbox.runs import EFFORTS, MODELS, config_for
from deploy_workflow.inbox.startup import STANDING_RULING
from deploy_workflow.model.adapter import KEY_VARIABLES
from deploy_workflow.owners.cpos import web_search_run
from deploy_workflow.owners.cpos_launch import NO_PRIOR, LaunchRefused, prepare, read_documents
from deploy_workflow.platform_io import regular_open

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
_KEYS = {"context", "modules", "max_turns", "level", "submitted_by", "model", "effort"}
DEFAULT_MODEL, DEFAULT_EFFORT = "gpt", "balanced"  # the only pair below the Advanced level
_ADVANCED = "advanced"
_CLAUDE_UNAVAILABLE = "Claude Opus is not available on this service"
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
    model: str  # "gpt" | "claude"; anything but "gpt" needs Advanced
    effort: str  # "fast" | "balanced" | "high"; anything but "balanced" needs Advanced


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
    if answers["model"] not in MODELS:  # a list or None is not hashable-safe: compare as text
        raise Refused(f"model is one of {', '.join(MODELS)}")
    if answers["effort"] not in EFFORTS:
        raise Refused(f"effort is one of {', '.join(EFFORTS)}")
    chosen = (answers["model"], answers["effort"]) != (DEFAULT_MODEL, DEFAULT_EFFORT)
    if chosen and answers["level"] != _ADVANCED:
        raise Refused("the model and effort can be changed only at the Advanced level")
    by = answers["submitted_by"]
    if not isinstance(by, str) or len(by) > _SUBMITTER_AT_MOST:
        raise Refused(f"submitted_by is text of at most {_SUBMITTER_AT_MOST} characters")
    return answers  # type: ignore[return-value]


def require_provider_key(answers: Answers) -> None:
    """``Refused`` when the answers pick Claude and this service's environment has no Anthropic key.

    Only presence is read; the key's value is never returned, logged or shown. Start-up requires
    the OpenAI key but not this one, so its absence only makes Claude submissions refusable."""
    if answers["model"] == "claude" and not os.environ.get(KEY_VARIABLES["anthropic"]):
        raise Refused(_CLAUDE_UNAVAILABLE)


def _open_folders(layout: Layout) -> list[Path]:
    """The unsubmitted submissions: an id folder that has ``files`` and no ``sealed`` folder.

    What a submitted submission leaves behind (an ``issued`` file, an empty folder) is not one."""
    if not layout.uploads.is_dir():
        return []
    return [
        entry
        for entry in layout.uploads.iterdir()
        if _ID.fullmatch(entry.name)
        and not entry.is_symlink()
        and entry.is_dir()
        and (entry / "files").is_dir()
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
    real = False
    for name in ("sealed", "files"):
        inside = folder / name
        if inside.is_symlink():  # a link planted here would be followed by every reader
            raise Refused("unknown submission")
        real = real or inside.is_dir()
    if real:
        return folder
    raise Refused("unknown submission")


def _is_sealed(folder: Path) -> bool:
    sealed = folder / "sealed"
    return sealed.is_dir() and not sealed.is_symlink()


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


def _stored(root: Path, *, strict: bool = False, any_error: bool = False) -> dict[str, int]:
    """Relative posix name -> size of each regular file under ``root``; links are not followed.

    With ``strict`` a link anywhere under ``root`` is a ``Refused``: the launcher follows links and
    the digest does not, so a link would let bytes change without the digest changing. With
    ``any_error`` (and ``strict``) every walk error is a ``Refused``, not only an unreadable folder:
    a folder that is never renamed under the walk (a source folder) has no vanishing to forgive."""
    found: dict[str, int] = {}

    def unreadable(error: OSError) -> None:
        # Only a folder that exists but cannot be read is refused; one that vanished (a seal
        # renamed it) is left to the callers' own retry, as before.
        if not any_error and not isinstance(error, PermissionError):
            return
        try:
            shown = Path(error.filename).relative_to(root).as_posix() if error.filename else ""
        except ValueError:
            shown = ""
        shown = shown or "a folder"
        raise Refused(f"{shown!r} cannot be read")

    walk = os.walk(root, followlinks=False, onerror=unreadable if strict else None)
    for here, dirs, names in walk:
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


def _place(folder: Path, parts: list[str], temp_path: Path, *, replace: bool = True) -> None:
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
            if not replace and os.path.lexists(target):
                raise _Taken(f"{stored!r} is already stored")
            os.replace(temp_path, target)
        except (NotADirectoryError, FileExistsError) as error:
            raise Refused(f"{stored!r} clashes with a file or folder already stored") from error


def _unlink_temporary(temp_path: Path) -> None:
    try:
        temp_path.unlink(missing_ok=True)
    except OSError as error:
        # Not fail-open: the caller is refused. The leftover is outside ``files`` (not part of the
        # documents) and the sweep removes it with the folder.
        log.warning("could not remove the temporary upload %s (%s)", temp_path, error)
        raise Refused("the upload could not be cleaned up; try again") from error


def add_file(layout: Layout, sid: str, name: str, body: BinaryIO, length: int) -> str:
    """Store ``length`` bytes from ``body`` under a safe version of ``name``; return that name.

    The bytes go to a temporary name in the submission folder and are renamed into place on
    success, so a refusal or a cut-off upload leaves nothing behind. A name already stored is
    replaced, except for a file opened by ``open_regular`` (a carry), which is refused as taken."""
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
        _place(folder, parts, temp_path, replace=not isinstance(body, _Carried))
    finally:
        # The reservation is released first: a failed unlink must not hold it for the life of the
        # process (it blocks ``seal`` and the sweep).
        with _LOCK:
            held = _PENDING.get(sid, {})
            held.pop(tmp, None)
            if not held:
                _PENDING.pop(sid, None)
        _unlink_temporary(temp_path)
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


def listing(source: Path) -> dict[str, int]:
    """Relative posix name -> size of each regular file under ``source``, but its own context.json.

    ``Refused`` when anything under ``source`` is a link or cannot be walked: a copy must never
    follow a link. A name with a part starting ``.`` (``.DS_Store``) is left out: the launcher
    does not read it, so it is neither carried nor counted."""
    return {
        name: size
        for name, size in _stored(source, strict=True, any_error=True).items()
        if name.casefold() != _CONTEXT_NAME and not any(p.startswith(".") for p in name.split("/"))
    }


class _Taken(Refused):
    """A carried file's name is already stored; the carry keeps the stored file."""


class _Carried(io.BufferedReader):
    """A source file opened by ``open_regular``; ``add_file`` never replaces a file for one.

    Kept as a handle type, not a ``replace`` keyword: the tests' and probes' wrappers around
    ``add_file`` take its five positional arguments only."""


def open_regular(path: Path, size: int | None = None) -> _Carried:
    """Open ``path`` for reading; ``Refused`` unless it is a regular file with one link (and
    ``size`` bytes when given). The last part is not followed if it is a link."""
    # O_NONBLOCK: opening a FIFO must not wait for a writer (regular_open then refuses it).
    # regular_open adds O_BINARY where the platform has it and refuses a reparse point.
    options = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = regular_open(path, options)
    except OSError as error:
        raise Refused(f"{path.name!r} cannot be read as a regular file") from error
    try:
        info = os.fstat(fd)
        if info.st_nlink != 1:
            raise Refused(f"{path.name!r} is a link, not an uploaded file")
        if size is not None and info.st_size != size:
            raise Refused(f"{path.name!r} changed while it was being copied")
        return _Carried(io.FileIO(fd, "rb"))
    except BaseException:
        os.close(fd)
        raise


def _fold(name: str) -> str:
    """A stored name as a case- and normalisation-insensitive disk sees it."""
    return unicodedata.normalize("NFC", "/".join(_parts(name))).casefold()


def _check_carry(root: Path, sid: str, wanted: dict[str, int]) -> tuple[list[str], list[str]]:
    """The names to copy and the names kept (in stored form), the limits checked against what is
    stored and in flight. A name is compared in its stored form, as the disk compares it."""
    existing = _stored(root)
    taken = {_fold(name) for name in existing}
    names: list[str] = []
    kept: list[str] = []
    for name in sorted(wanted):
        key = _fold(name)
        if key in taken:
            kept.append("/".join(_parts(name)))
        else:
            taken.add(key)
            names.append(name)
    for name in names:
        if wanted[name] > MAX_FILE:
            raise Refused(f"a file is at most {MAX_FILE // (1024 * 1024)} MB")
    own = _PENDING.get(sid, {})
    if len(existing) + len(own) + len(names) > MAX_FILES:
        raise Refused(f"more than {MAX_FILES} files")
    total = sum(existing.values()) + sum(size for _, size in own.values())
    if total + sum(wanted[name] for name in names) > MAX_TOTAL:
        raise Refused(f"more than {MAX_TOTAL // (1024 * 1024)} MB in total")
    return names, kept


def _roll_back(layout: Layout, sid: str, made: list[tuple[str, int]]) -> None:
    """Remove the files this carry created, each only while it still has the size it wrote."""
    try:
        root = files_folder(layout, sid)
    except Refused as error:
        log.warning("carry %s: the files could not be rolled back (%s)", sid, error)
        return
    for stored, size in made:
        path = root.joinpath(*stored.split("/"))
        try:
            if path.is_symlink() or not path.is_file() or path.lstat().st_size != size:
                continue  # replaced since: no longer this call's file
            remove_file(layout, sid, stored)
        except (Refused, OSError) as error:  # logged; the caller sees the original failure
            log.warning("carry %s: could not remove %s (%s)", sid, stored, error)


def carry(layout: Layout, sid: str, source: Path) -> dict[str, list[str]]:
    """Copy each file under ``source`` (but its context.json) into the submission.

    A name already stored is kept, never replaced, and is reported as kept. Nothing is copied when
    a link is found or a limit would be passed; a copy that fails part-way removes the files this
    call created. Returns the names carried and the names kept, each sorted."""
    folder = _folder(layout, sid)
    if source.is_symlink() or not source.is_dir():
        raise Refused("the earlier run's files are not a plain folder")
    wanted = listing(source)
    with _LOCK:
        root = _usable_root(folder)
        names, kept = _check_carry(root, sid, wanted)
    # ponytail: the pre-check and the copies are not one atomic step. Each copy is created without
    # replacing (``_place`` refuses a name taken since, and the file is then kept), ``add_file``
    # re-checks the limits, and a failure removes only what this call created. A seal landing
    # between two copies leaves the earlier ones in the sealed folder (a wider lock is needed).
    made: list[tuple[str, int]] = []
    try:
        for name in names:
            _refuse_links(source, name.split("/"))
            with open_regular(source / name, wanted[name]) as handle:
                try:
                    made.append(
                        (
                            add_file(layout, sid, name, handle, wanted[name]),
                            wanted[name],
                        )
                    )
                except _Taken:
                    kept.append("/".join(_parts(name)))
    except BaseException:
        _roll_back(layout, sid, made)
        raise
    return {"carried": sorted(stored for stored, _ in made), "kept": sorted(set(kept))}


def reading(layout: Layout, sid: str) -> dict[str, Any]:
    """What the launcher makes of each uploaded file; its refusal comes back as ``error``."""
    root = files_folder(layout, sid)
    try:
        _stored(root, strict=True)
        got = read_documents(root)
    except (LaunchRefused, Refused) as refusal:
        return {"documents": [], "ignored": [], "error": _without_path(str(refusal), root)}
    return {"documents": list(got.documents), "ignored": list(got.ignored), "error": ""}


_DOCUMENTS = "the uploaded documents"


def _without_path(text: str, root: Path) -> str:
    """``text`` with the server's path to the documents replaced: it is not the analyst's to see."""
    for shown in sorted({str(root), str(root.resolve())}, key=len, reverse=True):
        text = text.replace(shown, _DOCUMENTS)
    return text


def context_bytes(answers: Answers) -> bytes:
    text = json.dumps(answers["context"], indent=2, ensure_ascii=False) + "\n"
    try:
        return text.encode("utf-8")
    except UnicodeEncodeError:
        raise Refused("the context holds text that cannot be stored (a lone surrogate)") from None


def _digest(root: Path, answers: Answers) -> str:
    files = []
    for rel in sorted(_stored(root, strict=True)):
        if rel == _CONTEXT_NAME:  # made from the answers (the scheduler writes it); never uploaded
            continue
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
        "model": answers["model"],
        "effort": answers["effort"],
    }
    text = json.dumps(covered, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def bound(value: str, prior: str) -> str:
    """``value`` (a digest) with the approved choice of earlier run (``prior``: a run folder name or
    ``none``; owner, 2026-11-12: what CP-8 compares with is part of what is approved) folded in.
    Empty when none was recorded, which leaves the digest as it was."""
    if not prior:
        return value
    return hashlib.sha256(f"{value}\nprior={prior}".encode()).hexdigest()


def digest(layout: Layout, sid: str, answers: Answers) -> str:
    """SHA-256 over the context, each stored file's name and hash, the modules, the turns, the model
    and the effort.

    ``level`` and ``submitted_by`` are not covered: they change what the page shows, not the run.
    The approval's digest is this one with the earlier run named at approval folded in (`bound`)."""
    answers = validated(answers)
    root = files_folder(layout, sid)
    value = _digest(root, answers)
    if not root.is_dir():  # a seal renamed the folder before the walk: it saw nothing
        value = _digest(files_folder(layout, sid), answers)
    return value


def _remove(folder: Path) -> None:
    # Fail-open by design: the caller's result is correct whether or not the folder goes, and
    # ``sweep`` removes state/summary-* and stale uploads/<id> folders again, so a leftover is
    # retried. The failure is logged with the folder's name, not hidden.
    try:
        shutil.rmtree(folder)
    except OSError as error:
        log.warning("could not remove %s (%s); the sweep will try again", folder, error)


def release(layout: Layout, sid: str) -> None:
    """Remove ``uploads/<id>`` once its files have moved on to a run; what is left is ``issued``.

    Nothing is removed while ``files`` or ``sealed`` is still there. A failed removal is logged and
    the sweep tries again (see ``_remove``), so the open count is not what depends on it."""
    if not isinstance(sid, str) or not _ID.fullmatch(sid):
        return
    folder = layout.uploads / sid
    with _LOCK:
        if folder.is_symlink() or not folder.is_dir():
            return
        if any(os.path.lexists(folder / name) for name in ("files", "sealed")):
            return
        _remove(folder)


_ISSUED = "issued"


def _issued_lines(layout: Layout, sid: str) -> list[str]:
    path = _folder(layout, sid) / _ISSUED
    if path.is_symlink():
        return []
    try:
        return path.read_text(encoding="ascii", errors="replace").split()
    except FileNotFoundError:
        return []


def issued(layout: Layout, sid: str) -> str:
    """The digest the latest summary of this submission returned; empty when there is none."""
    lines = _issued_lines(layout, sid)
    return lines[0] if lines else ""


def issued_prior(layout: Layout, sid: str) -> str:
    """The earlier run the latest summary named (a run folder name, or ``none`` for a first run);
    empty when there is none. It is part of the issued digest."""
    lines = _issued_lines(layout, sid)
    return lines[1] if len(lines) > 1 else ""


def _record_issued(layout: Layout, sid: str, value: str, prior: str = "") -> None:
    """Replace the submission's issued digest (and the earlier run it names) with ``value`` (none
    when empty), under the lock."""
    folder = _folder(layout, sid)
    with _LOCK:
        if not folder.is_dir():  # the scheduler's release removed it after the check above
            raise Refused("unknown submission")
        path = folder / _ISSUED
        if not value:
            path.unlink(missing_ok=True)
            return
        temp = folder / f".issued-{uuid.uuid4().hex}"
        try:
            temp.write_text(value + "\n" + (prior + "\n" if prior else ""), encoding="ascii")
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)


def summary(layout: Layout, sid: str, answers: Answers, *, cap: Decimal) -> dict[str, Any]:
    """The launcher's own forecast for these files and answers, with the digest to approve.

    The forecast is for the config the answers' model and effort launch with (``runs.config_for``).

    The digest it returns is the one approval this service will accept for the submission: it is
    recorded in ``uploads/<id>/issued``, replaced by each later summary and removed when a summary
    returns an error. The context is written to a temporary folder and the run folder is another
    one; both are under the state folder, never in the files, and both are removed. A refusal
    comes back as ``error`` with no digest, and so does a change to the documents while the
    forecast was being made."""
    result = _summarise(layout, sid, answers, cap=cap)
    digest_issued = result.get("digest", "")
    try:
        _record_issued(layout, sid, digest_issued, result.get("prior_choice", ""))
    except Refused:
        if digest_issued:  # a digest was made for a submission that is not there: not possible
            raise
        # An error answer for an unknown submission has no issued digest to clear; the answer
        # (the refusal text) is still returned unchanged.
    return result


def _summarise(layout: Layout, sid: str, answers: Answers, *, cap: Decimal) -> dict[str, Any]:
    try:
        answers = validated(answers)
        require_provider_key(answers)
        config = config_for(answers["model"], answers["effort"])
    except Refused as refusal:
        return {"error": str(refusal)}
    files = files_folder(layout, sid)
    with _SUMMARY_LOCK:
        layout.state.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="summary-", dir=layout.state))
        try:
            try:
                try:
                    before = _digest(files, answers)
                except OSError as error:
                    log.warning("summary %s: the files could not be read: %s", sid, error)
                    return {"error": _CHANGED}
                run = load_context(context_bytes(answers))
                if len(run.identity.issuer_id) > MAX_ISSUER_ID:
                    raise Refused(
                        f"issuer_id is {len(run.identity.issuer_id)} characters; "
                        f"use at most {MAX_ISSUER_ID}"
                    )
                context_dir = work / "context"
                context_dir.mkdir()
                context = context_dir / _CONTEXT_NAME
                context.write_bytes(context_bytes(answers))
                try:
                    prepared = prepare(
                        context,
                        files,
                        work / "run",
                        config=config,
                        cap=cap,
                        modules=answers["modules"] or None,
                        web_search=web_search_run(config, STANDING_RULING),
                        # The summary prepares in a temporary folder, so it names where the
                        # earlier runs are: the launcher's own `_engine` folder.
                        workspace=layout.engine,
                    )
                    after = _digest(files, answers)
                except OSError as error:  # a file went away while it was being read: it changed
                    log.warning("summary %s: the files could not be read: %s", sid, error)
                    return {"error": _CHANGED}
            except ValueError as refusal:  # Refused, ContextRefused and LaunchRefused included
                return {"error": _without_path(str(refusal), files)}
            if before != after:
                return {"error": _CHANGED}
            # What CP-8 compares with is part of the approval: the run named here is the one the
            # launcher is told to use (`--prior`), and it is folded into the digest.
            chosen = prepared.prior.folder if prepared.prior is not None else NO_PRIOR
            return {
                "digest": bound(after, chosen),
                "prior_choice": chosen,
                "prior": None
                if prepared.prior is None
                else {
                    "id": prepared.prior.folder,
                    "as_of": prepared.prior.as_of,
                    "pathway": prepared.prior.pathway,
                },
                "error": "",
                "modules": list(prepared.ordered),
                "items": list(prepared.expectations),
                "documents": list(prepared.documents),
                "ignored": list(prepared.ignored),
                "omitted": list(prepared.omitted),
                "changes": prepared.changes.removeprefix("changes: "),
                "model": answers["model"],
                "effort": answers["effort"],
            }
        finally:
            _remove(work)


def sweep(layout: Layout, now: float, keep: Collection[str] = ()) -> None:
    """Delete each ``uploads/<id>`` and ``state/summary-*`` not modified for ``STALE_SECONDS``.

    A submission with an upload in flight, or whose id is in ``keep`` (one the scheduler still
    holds a queued record for), is kept. Other entries are left."""
    if layout.uploads.is_dir():
        for entry in layout.uploads.iterdir():
            if not _ID.fullmatch(entry.name) or entry.is_symlink() or not entry.is_dir():
                continue
            with _LOCK:
                if _PENDING.get(entry.name) or entry.name in keep:
                    continue
                if now - entry.stat().st_mtime >= STALE_SECONDS:
                    _remove(entry)
    if layout.state.is_dir():
        for entry in layout.state.iterdir():
            leftover = entry.name.startswith("summary-") and entry.is_dir()
            if leftover and not entry.is_symlink() and now - entry.stat().st_mtime >= STALE_SECONDS:
                _remove(entry)
