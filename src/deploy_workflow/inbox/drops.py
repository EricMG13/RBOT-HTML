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
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from deploy_vii.contracts import PATHWAY_MODULES
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


def _files(entry: Path) -> list[Path]:
    """The regular files of an entry; a symlink (the entry or inside it) is never followed."""
    if entry.is_symlink():
        return []
    if entry.is_file():
        return [entry]
    found: list[Path] = []
    for here, dirs, names in os.walk(entry, followlinks=False):
        dirs.sort()
        for name in sorted(names):
            path = Path(here) / name
            if not path.is_symlink():
                found.append(path)
    return found


def signature(entry: Path) -> Signature:
    """Sorted (relative posix path, size, mtime_ns) per file; a file is one row."""
    rows = []
    for path in _files(entry):
        stat = path.stat()
        rel = path.name if path == entry else path.relative_to(entry).as_posix()
        rows.append((rel, stat.st_size, stat.st_mtime_ns))
    return tuple(sorted(rows))


def unlocked(path: Path) -> bool:
    """False only when another process holds the file open (Windows sharing or lock violation)."""
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

    def ready(self, entry: Path) -> bool:
        try:
            sig = signature(entry)
        except OSError:  # Vanished or being moved while we looked.
            self._seen.pop(entry, None)
            return False
        now = self.clock()
        before = self._seen.get(entry)
        if before is None or before[0] != sig:
            self._seen[entry] = (sig, now)
            return False
        if now - before[1] < self.settle_seconds:
            return False
        return all(unlocked(path) for path in _files(entry))


def candidates(layout: Layout) -> list[tuple[str, Path]]:
    """(pathway, entry) for each entry in a pathway folder; strays directly in the inbox get ""."""
    found: list[tuple[str, Path]] = []
    for pathway in PATHWAYS:
        folder = layout.inbox / pathway
        if folder.is_dir():
            found += [(pathway, e) for e in sorted(folder.iterdir()) if e.name != TEMPLATE]
    skip = {*PATHWAYS, FAILED}
    found += [("", e) for e in sorted(layout.inbox.iterdir()) if e.name not in skip]
    return found


def claim(layout: Layout, entry: Path, claim_id: str) -> Path | None:
    """Move ``entry`` to ``drops/<claim_id>`` in one rename; None if it is held open or taken."""
    target = layout.drops / claim_id
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
        body = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):  # Not JSON (or not text): an ordinary source, not the context.
        return False
    return isinstance(body, dict) and body.get("schema") == SCHEMA


def check(drop: Path, pathway: str) -> Checked:
    """Validate a claimed drop or raise ``DropRejected`` with the reason."""
    if not pathway:
        raise DropRejected("not inside a pathway folder")
    if drop.is_symlink() or not drop.is_dir():
        raise DropRejected("not a folder")
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


def reject(layout: Layout, drop: Path, name: str, reason: str, now: datetime) -> Path:
    """Move ``drop`` to ``inbox/failed/<date time> <name>/`` and write ``WHY.txt`` beside it."""
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
    (dest / "WHY.txt").write_text(
        f"{reason}\n\nFix the folder and drop it again.\n", encoding="utf-8"
    )
    return dest
