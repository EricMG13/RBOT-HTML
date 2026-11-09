"""Run records and the launcher child process: save, load, launch, liveness, outcome."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal

from deploy_workflow.inbox.drops import Layout
from deploy_workflow.run_events import EVENTS, read_events

log = logging.getLogger(__name__)

Status = Literal["queued", "running", "finished", "failed", "capped", "rejected", "interrupted"]

_REGISTRY = "issuers.json"


@dataclass
class Record:
    id: str
    pathway: str
    folder: str
    status: Status
    claimed_at: str
    issuer_id: str = ""
    issuer_name: str = ""
    as_of: str = ""
    files: tuple[str, ...] = ()
    started_at: str = ""
    ended_at: str = ""
    pid: int = 0
    reason: str = ""
    report: str = ""  # posix path relative to the root
    name_differs: bool = False


def save(layout: Layout, record: Record) -> None:
    """Write state/<id>.json through a temporary file, then ``os.replace`` it into place."""
    target = layout.state / f"{record.id}.json"
    temporary = layout.state / f"{record.id}.json.tmp"
    temporary.write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")
    os.replace(temporary, target)


def _load(path: Path) -> Record:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["files"] = tuple(data.get("files", ()))
        return Record(**data)
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise ValueError(f"{path.name}: unreadable run record ({error})") from error


def load_all(layout: Layout) -> list[Record]:
    """Every run record, sorted by id. The issuer registry and temporary files are not records."""
    paths = [p for p in layout.state.glob("*.json") if p.name != _REGISTRY]
    return sorted((_load(p) for p in paths), key=lambda r: r.id)


def alive(pid: int) -> bool:
    if pid <= 0:
        return False
    # ponytail: a reused process ID reads as alive; add the creation time if that ever bites.
    if sys.platform == "win32":
        # os.kill(pid, 0) terminates a process on Windows; wait on a handle instead.
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined,unused-ignore]
        handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            return False
        try:
            return bool(kernel32.WaitForSingleObject(handle, 0) == 0x102)  # still running
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def command(  # noqa: PLR0913 - the signature the watcher calls
    layout: Layout,
    record: Record,
    context: Path,
    *,
    launcher: Sequence[str],
    config: str,
    cap: Decimal,
    ruling: Path | None,
) -> list[str]:
    argv = [
        *launcher,
        "--context", str(context),
        "--sources", str(layout.drops / record.id),
        "--config", config,
        "--cap", str(cap),
        "--out", str(layout.runs / record.id),
        "--no-library",
    ]  # fmt: skip
    if ruling is not None:
        argv += ["--live", "--ruling", str(ruling)]
    return argv


def prepare(  # noqa: PLR0913 - the signature the watcher calls
    layout: Layout,
    record: Record,
    context: Path,
    *,
    launcher: Sequence[str],
    config: str,
    cap: Decimal,
) -> str:
    """Dry run (no ruling, no spend). Returns "" on success, else the refusal text."""
    argv = command(layout, record, context, launcher=launcher, config=config, cap=cap, ruling=None)
    done = subprocess.run(argv, capture_output=True, text=True, check=False)
    with (layout.logs / f"{record.id}.log").open("a", encoding="utf-8") as log_file:
        log_file.write(done.stdout)
        log_file.write(done.stderr)
    if done.returncode == 0:
        return ""
    lines = [line.strip() for line in done.stderr.splitlines() if line.strip()]
    return lines[-1] if lines else f"launcher exited {done.returncode}"


def start(  # noqa: PLR0913 - the signature the watcher calls
    layout: Layout,
    record: Record,
    context: Path,
    *,
    launcher: Sequence[str],
    config: str,
    cap: Decimal,
    ruling: Path,
) -> subprocess.Popen[bytes]:
    """Start the paid run as a child; stdout and stderr append to logs/<id>.log."""
    argv = command(
        layout, record, context, launcher=launcher, config=config, cap=cap, ruling=ruling
    )
    with (layout.logs / f"{record.id}.log").open("ab") as log_file:
        if sys.platform == "win32":  # a Ctrl-C to the watcher must not stop its runs
            return subprocess.Popen(
                argv,
                stdout=log_file,
                stderr=log_file,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        return subprocess.Popen(argv, stdout=log_file, stderr=log_file)


def outcome(layout: Layout, record: Record, exit_code: int | None) -> tuple[Status, str]:
    """Decide a run's end from its event log, then from the launcher's exit code."""
    try:
        events = read_events(layout.runs / record.id / EVENTS)
    except (OSError, ValueError) as error:
        # Documented fail-open: an unreadable log counts as no events; the exit code decides.
        log.warning("run %s: event log unreadable (%s); treated as no events", record.id, error)
        events = []
    if any(e.get("event") == "delivered" for e in events):
        return "finished", ""
    for event in events:
        if event.get("event") == "stopped":
            reason = str(event.get("reason", ""))
            if reason == "budget":
                return "capped", "stopped at the cap"
            return "failed", f"stopped: {reason}"
    if exit_code is None:
        return "interrupted", "the run's process ended without a result"
    return "failed", f"launcher exited {exit_code}; see logs/{record.id}.log"
