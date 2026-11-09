"""Drops in the shared inbox: folder layout, readiness, claim, check and reject.

An analyst copies a folder into ``inbox/<pathway>/``. The watcher waits until the copy has stopped
changing, moves it out of the inbox in one rename (so a drop can never start twice), checks it, and
either launches it or moves it to ``inbox/failed/`` with a ``WHY.txt``. Names an analyst chose are
never joined into a path outside the folder they came from, and a symlink planted in the inbox is
never followed.
"""

from __future__ import annotations

import json
import os
import re
import stat
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from deploy_vii.contracts import PATHWAY_MODULES
from deploy_vii.preparation import MAX_BYTES
from deploy_workflow.context import SCHEMA, ContextRefused, RunContext, load_context
from deploy_workflow.owners.cpos_launch import SOURCE_SUFFIXES

PATHWAYS: tuple[str, ...] = tuple(PATHWAY_MODULES)
MAX_ROOT = 80
TEMPLATE = "_template"
FAILED = "failed"
_SHARING_VIOLATIONS = (32, 33)  # Windows: sharing violation, lock violation.
_NAME_LIMIT = 60
_UNSAFE = re.compile(r'[\x00-\x1f<>:"/\\|?*]')

Signature = tuple[tuple[str, int, int], ...]


@dataclass(frozen=True)
class Layout:
    root: Path

    @property
    def inbox(self) -> Path:
        return self.root / "inbox"

    @property
    def failed(self) -> Path:
        return self.inbox / FAILED

    @property
    def issuers(self) -> Path:
        return self.root / "issuers"

    @property
    def engine(self) -> Path:
        return self.root / "_engine"

    @property
    def runs(self) -> Path:
        return self.engine / "runs"

    @property
    def drops(self) -> Path:
        return self.engine / "drops"

    @property
    def state(self) -> Path:
        return self.engine / "state"

    @property
    def logs(self) -> Path:
        return self.engine / "logs"


def ensure_layout(root: Path) -> Layout:
    """Create every folder under ``root``; refuse a root so long that Windows paths would break."""
    resolved = root.resolve()
    if len(str(resolved)) > MAX_ROOT:
        raise ValueError(
            f"root {resolved} is {len(str(resolved))} characters; "
            f"use a shorter path (at most {MAX_ROOT})"
        )
    layout = Layout(resolved)
    folders = [layout.failed, layout.issuers, layout.runs, layout.drops, layout.state, layout.logs]
    folders += [layout.inbox / pathway for pathway in PATHWAYS]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
    return layout


def _is_link(path: Path) -> bool:
    """A symlink, or a Windows junction (which ``is_symlink`` does not report)."""
    return path.is_symlink() or os.path.isjunction(path)


def _raise(exc: OSError) -> None:
    raise exc


def _files(entry: Path) -> list[Path]:
    """The files of an entry that are not links (special files included, to be refused later).

    A link is never followed. A listing error is raised, not hidden. A missing entry has none."""
    if not os.path.lexists(entry) or _is_link(entry):
        return []
    if not entry.is_dir():
        return [entry]
    found: list[Path] = []
    for here, dirs, names in os.walk(entry, followlinks=False, onerror=_raise):
        dirs[:] = sorted(d for d in dirs if not _is_link(Path(here) / d))
        found += [Path(here) / n for n in sorted(names) if not _is_link(Path(here) / n)]
    return found


def signature(entry: Path) -> Signature:
    """Sorted (relative posix path, size, mtime_ns) per file; a file is one row."""
    rows = []
    for path in _files(entry):
        stat_result = path.lstat()
        rel = path.name if path == entry else path.relative_to(entry).as_posix()
        rows.append((rel, stat_result.st_size, stat_result.st_mtime_ns))
    return tuple(sorted(rows))


def unlocked(path: Path) -> bool:
    """False only when another process holds the file open (Windows sharing or lock violation).

    Anything that is not a regular file (a FIFO, a device) is never opened: opening it can block
    forever. ``check`` refuses such a file once the drop has settled."""
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            return True
    except OSError:
        return False
    try:
        with path.open("r+b"):
            return True
    except OSError as exc:
        if getattr(exc, "winerror", None) in _SHARING_VIOLATIONS:
            return False
    try:  # Read-only, or no write permission: reading is all the launcher needs.
        with path.open("rb"):
            return True
    except OSError:
        return False


@dataclass
class ReadyTracker:
    """An entry is ready when its signature has been the same, by the watcher's own clock, for
    ``settle_seconds`` and no file in it is held open. File times are not used: a Windows copy
    keeps the source's old modified time."""

    settle_seconds: float
    clock: Callable[[], float]
    _seen: dict[Path, tuple[Signature, float]] = field(default_factory=dict, init=False)

    def forget_missing(self, listed: Iterable[Path]) -> None:
        """Drop every tracked entry that is not in ``listed`` (what the last scan found)."""
        keep = set(listed)
        for entry in [e for e in self._seen if e not in keep]:
            del self._seen[entry]

    def ready(self, entry: Path) -> bool:
        try:
            entry.lstat()
            sig = signature(entry)
        except OSError:  # Vanished, unreadable or being moved while we looked.
            self._seen.pop(entry, None)
            return False
        now = self.clock()
        before = self._seen.get(entry)
        if before is None or before[0] != sig:
            self._seen[entry] = (sig, now)
            return False
        if now - before[1] < self.settle_seconds:
            return False
        try:
            files = _files(entry)
        except OSError:
            return False
        if not all(unlocked(path) for path in files):
            return False
        del self._seen[
            entry
        ]  # Once handed out, a folder dropped again under this name starts over.
        return True


def _is_noise(name: str) -> bool:
    """Finder and Explorer bookkeeping and Office lock files are not drops."""
    return name.casefold() in ("thumbs.db", "desktop.ini") or name.startswith((".", "~$"))


def _real_folder_under(folder: Path, parent: Path) -> bool:
    """A real folder (no symlink, no junction) whose resolved parent is ``parent``."""
    return not _is_link(folder) and folder.is_dir() and folder.resolve().parent == parent.resolve()


def candidates(layout: Layout) -> list[tuple[str, Path]]:
    """(pathway, entry) for each entry in a pathway folder; strays directly in the inbox get "".

    A pathway folder that is a link, or that resolves outside the inbox, is not listed."""
    found: list[tuple[str, Path]] = []
    for pathway in PATHWAYS:
        folder = layout.inbox / pathway
        if _real_folder_under(folder, layout.inbox):
            found += [
                (pathway, e)
                for e in sorted(folder.iterdir())
                if e.name.casefold() != TEMPLATE and not _is_noise(e.name)
            ]
    skip = {*(p.casefold() for p in PATHWAYS), FAILED}
    found += [
        ("", e)
        for e in sorted(layout.inbox.iterdir())
        if e.name.casefold() not in skip and not _is_noise(e.name)
    ]
    return found


def claim(layout: Layout, entry: Path, claim_id: str) -> Path | None:
    """Move ``entry`` to ``drops/<claim_id>`` in one rename; None if it is held open or taken."""
    target = layout.drops / claim_id
    if os.path.lexists(target):  # POSIX would replace an empty folder.
        return None
    try:
        os.rename(entry, target)
    except OSError:
        return None
    return target


class DropRejected(ValueError):
    """The drop cannot be launched; the message is the reason shown to the analyst."""


@dataclass(frozen=True)
class Checked:
    context: Path
    run: RunContext
    files: tuple[str, ...]


def _is_context(path: Path) -> bool:
    if path.suffix.lower() != ".json" or path.is_symlink() or not path.is_file():
        return False
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:  # Too large to be a context: an ordinary source.
            return False
        body = json.loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError, RecursionError):  # Not JSON, not text or absurdly nested.
        return False
    return isinstance(body, dict) and body.get("schema") == SCHEMA


def _first_link_or_special(drop: Path) -> str | None:
    """Relative posix path of the first (sorted) link, junction or non-regular file, if any."""
    odd: list[str] = []
    for here, dirs, names in os.walk(drop, followlinks=False, onerror=_raise):
        for name in (*dirs, *names):
            path = Path(here) / name
            mode = path.lstat().st_mode
            if _is_link(path) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                odd.append(path.relative_to(drop).as_posix())
        dirs[:] = [d for d in dirs if not _is_link(Path(here) / d)]
    return min(odd) if odd else None


def check(drop: Path, pathway: str) -> Checked:
    """Validate a claimed drop or raise ``DropRejected`` with the reason."""
    if not pathway:
        raise DropRejected("not inside a pathway folder")
    if drop.is_symlink() or not drop.is_dir():
        raise DropRejected("not a folder")
    odd = _first_link_or_special(drop)
    if odd is not None:
        raise DropRejected(f"contains a link or special file: {odd}")
    contexts = sorted(p for p in drop.iterdir() if _is_context(p))
    if not contexts:
        raise DropRejected("no context file")
    if len(contexts) > 1:
        raise DropRejected(f"more than one context file: {', '.join(p.name for p in contexts)}")
    context = contexts[0]
    try:
        run = load_context(context.read_bytes())
    except ContextRefused as exc:
        raise DropRejected(f"context file: {exc}") from exc
    if run.run.pathway != pathway:
        raise DropRejected(f"context names pathway {run.run.pathway}, dropped in {pathway}")
    files = []
    for path in _files(drop):
        rel = path.relative_to(drop)
        if path == context or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if any(part.startswith((".", "_", "~$")) for part in rel.parts):
            continue
        files.append(rel.as_posix())
    if not files:
        raise DropRejected("no source file the launcher can read")
    return Checked(context, run, tuple(sorted(files)))


def _safe_name(name: str) -> str:
    cleaned = _UNSAFE.sub("_", name).strip(" .")[:_NAME_LIMIT].strip(" .")
    return cleaned or "drop"


def _write_note(folder: Path, text: str) -> None:
    """Create ``WHY.txt`` (or ``WHY (2).txt``...) as a new file; never open an existing name."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    number = 1
    while True:
        name = "WHY.txt" if number == 1 else f"WHY ({number}).txt"
        try:
            fd = os.open(folder / name, flags, 0o644)
        except FileExistsError:  # A file, link or folder the analyst put there.
            number += 1
            continue
        with os.fdopen(fd, "wb") as stream:
            stream.write(text.encode("utf-8", errors="backslashreplace"))
        return


def reject(layout: Layout, drop: Path, name: str, reason: str, now: datetime) -> Path:
    """Move ``drop`` to ``inbox/failed/<date time> <name>/`` and write ``WHY.txt`` beside it."""
    if not _real_folder_under(layout.failed, layout.inbox):
        raise OSError(
            f"{layout.failed} is not a real folder directly under the inbox "
            "(a link, a junction or missing); nothing was moved"
        )
    base = f"{now:%Y-%m-%d %H%M%S} {_safe_name(name)}"
    dest = layout.failed / base
    number = 2
    while dest.exists() or dest.is_symlink():
        dest = layout.failed / f"{base} ({number})"
        number += 1
    if drop.is_dir() and not drop.is_symlink():
        os.rename(drop, dest)
    else:  # A stray file or link: give it a folder of its own to sit in beside WHY.txt.
        dest.mkdir()
        os.rename(drop, dest / _safe_name(drop.name))
    _write_note(dest, f"{reason}\n\nFix the folder and drop it again.\n")
    return dest


_HTML_TAG = b'<html lang="en">'


def write_templates(layout: Layout, form: Path) -> None:
    """Give each pathway folder a ``_template/context-form.html`` fixed to that pathway.

    The copy is the form's bytes with ``data-pathway`` added to the opening ``<html>`` tag. A copy
    already there is left alone. A link at ``_template`` or at the copy is refused with ``OSError``;
    a form with no ``<html lang="en">`` tag raises ``ValueError`` before anything is written."""
    original = form.read_bytes()
    if original.count(_HTML_TAG) != 1:
        raise ValueError(f"{form} must contain exactly one {_HTML_TAG.decode()} tag to mark")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    for pathway in PATHWAYS:
        folder = layout.inbox / pathway / TEMPLATE
        if _is_link(folder):
            raise OSError(f"{folder} is a link; no form was written")
        folder.mkdir(exist_ok=True)
        target = folder / form.name
        if os.path.lexists(target):
            if _is_link(target):
                raise OSError(f"{target} is a link; no form was written")
            continue
        marked = original.replace(_HTML_TAG, f'<html lang="en" data-pathway="{pathway}">'.encode())
        fd = os.open(target, flags, 0o644)
        with os.fdopen(fd, "wb") as stream:
            stream.write(marked)
