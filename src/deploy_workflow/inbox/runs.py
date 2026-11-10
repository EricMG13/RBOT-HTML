"""Run records and the launcher child process: save, load, launch, liveness, outcome."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal, get_args

from deploy_workflow import platform_io
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
    prepared: bool = False  # the offline check passed; only then may the run be started


PID_FILE_VARIABLE = "DEPLOY_WORKFLOW_PID_FILE"  # the launcher reads the same name


def pid_file(layout: Layout, run_id: str) -> Path:
    """Where a run's launcher writes its own process ID: beside the run's record file."""
    return layout.state / f"{run_id}.pid"


_SRC = Path(__file__).resolve().parents[2]


def child_environment() -> dict[str, str]:
    """The environment for a launcher child: this process's, plus the engine's ``src`` folder
    first on ``PYTHONPATH`` (the package is not installed) and UTF-8 output. The provider key
    passes through untouched."""
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join([str(_SRC), existing] if existing else [str(_SRC)])
    env["PYTHONUTF8"] = "1"
    return env


def save(layout: Layout, record: Record) -> None:
    """Write state/<id>.json through a temporary file, then ``os.replace`` it into place."""
    if not record.id or Path(record.id).name != record.id or record.id.startswith("."):
        raise ValueError(f"run ID {record.id!r} is not a plain file name")
    target = layout.state / f"{record.id}.json"
    descriptor, temporary = tempfile.mkstemp(prefix=".run-", suffix=".tmp", dir=layout.state)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(asdict(record), handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        platform_io.replace(temporary, target)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _load(path: Path) -> Record:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["files"] = tuple(data.get("files", ()))
        record = Record(**data)
        if record.status not in get_args(Status):
            raise ValueError(f"unknown status {record.status!r}")
        return record
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise ValueError(f"{path.name}: unreadable run record ({error})") from error


def load_all(layout: Layout) -> list[Record]:
    """Every run record, sorted by id. The issuer registry, temporary files and dot files (such as
    a Mac ``._x.json`` sidecar) are not records."""
    paths = [
        p for p in layout.state.glob("*.json") if p.name != _REGISTRY and not p.name.startswith(".")
    ]
    return sorted((_load(p) for p in paths), key=lambda r: r.id)


def alive(pid: int) -> bool:
    """Whether process ``pid`` is running. For adopted PIDs (a record read after a restart).

    On a PID a live ``Popen`` tracks, use ``Popen.poll()`` instead: on POSIX this reaps the
    process with ``waitpid``, which would take the exit status away from the ``Popen``.
    """
    if pid <= 0:
        return False
    # ponytail: a reused process ID reads as alive; add the creation time if that ever bites.
    if sys.platform == "win32":
        # os.kill(pid, 0) terminates a process on Windows; wait on a handle instead.
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        running = ctypes.get_last_error() == 5  # no handle: access denied means it exists
        if handle:
            try:
                running = bool(kernel32.WaitForSingleObject(handle, 0) == 0x102)  # still running
            finally:
                kernel32.CloseHandle(handle)
        return running
    try:
        try:
            reaped, _status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            os.kill(pid, 0)  # not our child
        else:
            return reaped == 0  # 0: our child, still running; else it had exited and is reaped
    except (ProcessLookupError, OverflowError):
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
    timeout: float = 600,
) -> str:
    """Dry run (no ruling, no spend). Returns "" on success, else the refusal text."""
    argv = command(layout, record, context, launcher=launcher, config=config, cap=cap, ruling=None)
    try:
        done = subprocess.run(
            argv,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=child_environment(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        reason = f"the offline check did not finish in {timeout:g} s"
        with (layout.logs / f"{record.id}.log").open("a", encoding="utf-8") as log_file:
            log_file.write(reason + "\n")
        return reason
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
    env = child_environment()
    env[PID_FILE_VARIABLE] = str(pid_file(layout, record.id))
    with (layout.logs / f"{record.id}.log").open("ab") as log_file:
        if sys.platform == "win32":  # a Ctrl-C to the watcher must not stop its runs
            return subprocess.Popen(
                argv,
                stdout=log_file,
                stderr=log_file,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        # A new session keeps a terminal Ctrl-C (SIGINT to the watcher's group) off the run.
        return subprocess.Popen(
            argv, stdout=log_file, stderr=log_file, env=env, start_new_session=True
        )


def outcome(layout: Layout, record: Record, exit_code: int | None) -> tuple[Status, str]:
    """Decide a run's end from its event log, then from the launcher's exit code."""
    try:
        events = read_events(layout.runs / record.id / EVENTS)
    except FileNotFoundError:
        events = []  # no log yet: nothing to report
    except (OSError, ValueError) as error:
        # Documented fail-open: an unreadable log counts as no events; the exit code decides.
        log.warning("run %s: event log unreadable (%s); treated as no events", record.id, error)
        events = []
    events = [e for e in events if isinstance(e, dict)]  # a valid JSON line need not be an event
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
