"""Run records and the launcher child process: save, load, launch, liveness, outcome."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal, get_args

from deploy_workflow import platform_io
from deploy_workflow.inbox.layout import Layout
from deploy_workflow.owners.cpos_launch import METHODS
from deploy_workflow.run_events import EVENTS, read_events

log = logging.getLogger(__name__)

Status = Literal["queued", "running", "finished", "failed", "capped", "rejected", "interrupted"]

_REGISTRY = "issuers.json"
DEFAULT_MAX_TURNS = 32
_TURNS = (1, 64)  # the range submissions.validated accepts
_PRIOR = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")  # a run folder name, or `none`
MODELS = ("gpt", "claude")
EFFORTS = ("fast", "balanced", "high")
# The only launches the service makes: (model, effort) -> (launcher --config, --balanced or not).
# Every config named here must be named by the standing ruling; start-up checks all of them.
_LAUNCHES: dict[tuple[str, str], tuple[str, bool]] = {
    ("gpt", "fast"): ("sol-medium", False),
    ("gpt", "balanced"): ("sol-medium", True),
    ("gpt", "high"): ("sol-high", False),
    ("claude", "fast"): ("opus-medium", False),
    ("claude", "balanced"): ("opus-medium", True),
    ("claude", "high"): ("opus-high", False),
}
LAUNCH_CONFIGS = tuple(dict.fromkeys(config for config, _ in _LAUNCHES.values()))


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
    submission: str = ""  # the start page's submission ID; empty for a folder drop
    modules: tuple[str, ...] = ()  # () = the pathway's modules
    max_turns: int = DEFAULT_MAX_TURNS
    level: str = ""
    # Records written before the model and effort choice ran all-medium on GPT Sol.
    model: str = "gpt"
    effort: str = "fast"
    submitted_by: str = ""
    digest: str = ""  # the approved digest of the submitted files; the move is checked against it
    prior: str = ""  # the earlier run the approval named (a run folder name or `none`); "": search


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
    platform_io.write_atomic(target, json.dumps(asdict(record), indent=2), sync=True)


def _load(path: Path) -> Record:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["files"] = tuple(data.get("files", ()))
        data["modules"] = tuple(data.get("modules", ()))
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


def launch_options(model: str, effort: str) -> tuple[str, bool]:
    """The launcher ``--config`` and whether ``--balanced`` follows it, for a model and effort."""
    try:
        return _LAUNCHES[model, effort]
    except (KeyError, TypeError):
        raise ValueError(f"no launch for model {model!r} at effort {effort!r}") from None


def config_for(model: str, effort: str) -> str:
    """The configuration a run of this model and effort launches with."""
    return launch_options(model, effort)[0]


def _check_options(record: Record) -> None:
    """``ValueError`` unless the record's modules are method names, its turns a whole number in
    range and its model and effort known: a hand-edited record must not put an option of its own
    into the launcher's argv."""
    for field, allowed in (("model", MODELS), ("effort", EFFORTS)):
        value = getattr(record, field)
        if not isinstance(value, str) or value not in allowed:
            raise ValueError(
                f"run {record.id}: {field} {value!r} is not one of {', '.join(allowed)}"
            )
    for name in record.modules:
        if not isinstance(name, str) or name not in METHODS:
            raise ValueError(f"run {record.id}: {name!r} is not a module")
    if not isinstance(record.prior, str) or (record.prior and not _PRIOR.fullmatch(record.prior)):
        raise ValueError(f"run {record.id}: prior {record.prior!r} is not a run folder name")
    turns = record.max_turns
    if not isinstance(turns, int) or isinstance(turns, bool) or not _TURNS[0] <= turns <= _TURNS[1]:
        raise ValueError(f"run {record.id}: max_turns {turns!r} is not a whole number 1 to 64")


def command(  # noqa: PLR0913 - the signature the scheduler calls
    layout: Layout,
    record: Record,
    context: Path,
    *,
    launcher: Sequence[str],
    cap: Decimal,
    ruling: Path | None,
) -> list[str]:
    _check_options(record)
    config, balanced = launch_options(record.model, record.effort)
    argv = [
        *launcher,
        "--context", str(context),
        "--sources", str(layout.drops / record.id),
        "--config", config,
        *(["--balanced"] if balanced else []),
        "--cap", str(cap),
        "--out", str(layout.runs / record.id),
        "--no-library",
    ]  # fmt: skip
    if record.modules:
        argv += ["--modules", *record.modules]
    if record.prior:  # what the approval named: the launcher uses exactly that run
        argv += ["--prior", record.prior]
    if record.max_turns != DEFAULT_MAX_TURNS:
        argv += ["--max-turns", str(record.max_turns)]
    if ruling is not None:
        argv += ["--live", "--ruling", str(ruling)]
    return argv


def start(  # noqa: PLR0913 - the signature the scheduler calls
    layout: Layout,
    record: Record,
    context: Path,
    *,
    launcher: Sequence[str],
    cap: Decimal,
    ruling: Path,
) -> subprocess.Popen[bytes]:
    """Start the paid run as a child; stdout and stderr append to logs/<id>.log."""
    argv = command(layout, record, context, launcher=launcher, cap=cap, ruling=ruling)
    env = child_environment()
    env[PID_FILE_VARIABLE] = str(pid_file(layout, record.id))
    child: subprocess.Popen[bytes] | None = None
    try:
        with (layout.logs / f"{record.id}.log").open("ab") as log_file:
            if sys.platform == "win32":  # a Ctrl-C to the service must not stop its runs
                child = subprocess.Popen(
                    argv,
                    stdout=log_file,
                    stderr=log_file,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:  # a new session keeps a terminal Ctrl-C (SIGINT to the service group) off it
                child = subprocess.Popen(
                    argv, stdout=log_file, stderr=log_file, env=env, start_new_session=True
                )
    except OSError:
        if child is None:
            raise
        # Documented fail-open: the launcher has started and holds its own copy of the handle, so
        # an error closing this one is logged; raising would leave a paid run nobody tracks.
        log.exception("run %s: closing the log handle failed after the launcher started", record.id)
    return child


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
