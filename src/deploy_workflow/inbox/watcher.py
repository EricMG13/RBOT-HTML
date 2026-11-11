"""The inbox watcher: the one long-running process that turns drops into filed reports.

Each poll it reaps ended runs, scans the inbox, checks claimed drops, starts prepared runs within
the limits and publishes run activity. A record is saved before every step that an interruption
could cut short, so a restart always finds what to do next: a drop leaves the inbox in one rename
and gets its record at once, is never put back, and a run is marked running (and counted) before
its process starts. A run is shown as finished only when the library lists it.

``submit`` takes an approved submission from the start page: under ``lock`` (also held by every
poll) it saves the run's record, then renames the uploaded files folder to ``drops/<id>``. A
record whose folder is still missing is finished by the next poll or restart; one submission is
never two records.
"""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import IO, Any

from deploy_workflow.inbox import activity, drops, filing, runs, startup
from deploy_workflow.inbox.drops import DropRejected
from deploy_workflow.inbox.runs import Record
from deploy_workflow.inbox.startup import StartupRefused
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.owners import cpos_launch
from deploy_workflow.run_start import submissions
from deploy_workflow.run_start.submissions import Answers

__all__ = ["Settings", "StartupRefused", "Watcher", "main"]

_TIME = "%Y-%m-%dT%H:%M:%SZ"
_REBUILD_FAILED = "the library could not be rebuilt ({}); ended runs wait for it"
_KEPT = "_engine/drops/"
_NO_RECORD = (
    "the watcher stopped while taking this folder in; its files are in _engine/drops/{}"
    " \N{EM DASH} drop it again"
)
_CUT_SHORT = (
    "the watcher stopped while starting this run; its process may still be running"
    " \N{EM DASH} check before dropping the folder again"
)
# ponytail: a run whose launcher writes its PID file after 60 s is cut short; a reused process ID
# after a reboot reads as alive. Both are known ceilings, not handled.
_PID_GRACE_SECONDS = 60


@dataclass(frozen=True)
class Settings:
    root: Path
    config: str = "sol-medium"
    cap: Decimal = Decimal(20)
    max_running: int = 3
    max_per_day: int = 30
    settle_seconds: float = 120
    poll_seconds: float = 10
    ruling: Path = startup.STANDING_RULING
    launcher: tuple[str, ...] = (
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "deploy_workflow.owners.cpos_launch",
    )


def _local_now() -> datetime:
    return datetime.now().astimezone()


def _stop(child: subprocess.Popen[bytes]) -> None:
    child.terminate()
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait()


_MAX_PID_DIGITS = 10  # a longer number is no process ID (and int() refuses thousands of digits)


class Watcher:
    def __init__(
        self,
        settings: Settings,
        *,
        clock: Callable[[], float] = time.time,
        now: Callable[[], datetime] = _local_now,
    ) -> None:
        self.settings, self.clock, self.now = settings, clock, now
        self.layout = drops.ensure_layout(settings.root)
        startup.check_launchable(settings.config, settings.ruling, settings.cap)
        self._lock: IO[str] | None = startup.take_lock(self.layout)
        self._logger = startup.open_log(self.layout, __name__)  # only the lock holder logs
        self.lock = threading.Lock()  # held by step() and submit(): a submit never splits a poll
        self._records = {r.id: r for r in runs.load_all(self.layout)}
        self._children: dict[str, subprocess.Popen[bytes]] = {}
        self._tracker = drops.ReadyTracker(settings.settle_seconds, clock)
        self._unreadable: dict[Path, tuple[float, str]] = {}
        self._unmovable: dict[Path, str] = {}  # ready drops the watcher cannot move -> error
        self._rebuild_error = ""
        self._logged_rebuild_error = ""  # the last rebuild error written to the log
        self._stopped: dict[str, str] = {}  # run ID -> why the watcher stopped its process
        self._kept_activity: dict[str, tuple[runs.Record, dict[str, Any]]] = {}
        self._bad_pid_files: set[str] = set()  # run IDs whose unusable PID file is logged
        self._limit_held = ""
        startup.write_pages(self.layout)
        self._recover()
        self._rebuild()

    def close(self) -> None:
        """Release the folder lock and the log file. Safe to call twice."""
        handle, self._lock = self._lock, None
        if handle is not None:
            startup.release_lock(handle)
        startup.close_log(self.layout)

    def _recover(self) -> None:
        """Decide what an earlier stop left: runs cut short while starting, unrecorded folders."""
        self._track_untracked()
        self._finish_moves()
        self._reject_unrecorded_folders()

    def _track_untracked(self) -> None:
        """A running record with no PID and no child of this watcher was cut short between the
        child's start and the PID save: take the PID from the file the launcher wrote, or wait out
        the grace, then mark it interrupted (never restarted)."""
        for record in self._with_status("running"):
            if record.pid != 0 or record.id in self._children:
                continue
            with self._guard(f"run {record.id}"):
                pid = self._pid_from_file(record)
                if pid:
                    self._put(replace(record, pid=pid))
                elif self._past_grace(record):
                    self._put(
                        replace(
                            record,
                            status="interrupted",
                            reason=_CUT_SHORT,
                            ended_at=self._utc(self.now()),
                        )
                    )

    def _pid_from_file(self, record: Record) -> int:
        """The positive process ID in the run's PID file, else 0 (bad content: logged once)."""
        try:
            raw = runs.pid_file(self.layout, record.id).read_bytes()
        except FileNotFoundError:
            return 0
        text = raw.decode("ascii", "replace").strip()
        if text.isascii() and text.isdigit() and len(text) <= _MAX_PID_DIGITS and int(text) > 0:
            return int(text)
        if record.id not in self._bad_pid_files:
            self._bad_pid_files.add(record.id)
            self._logger.warning(
                "run %s: PID file holds %r, not a process ID", record.id, text[:40]
            )
        return 0

    def _past_grace(self, record: Record) -> bool:
        try:
            started = datetime.strptime(record.started_at, _TIME).replace(tzinfo=UTC)
        except ValueError:
            return True  # an unreadable time is treated as past the grace
        return (self.now().astimezone(UTC) - started).total_seconds() >= _PID_GRACE_SECONDS

    def _finish_moves(self) -> None:
        """A queued submission whose folder is still in ``uploads`` was cut short between its
        record and the rename: finish the rename."""
        for record in self._with_status("queued"):
            if record.submission and not os.path.lexists(self.layout.drops / record.id):
                with self._guard(f"submission {record.submission}"):
                    self._move_files(record)

    def _move_files(self, record: Record) -> None:
        files = self.layout.uploads / record.submission / "files"
        if files.is_dir() and not files.is_symlink():
            os.rename(files, self.layout.drops / record.id)

    def submit(self, sid: str, answers: Answers, approved_digest: str) -> Record:
        """Start one run for an approved submission. Repeating a submission returns its record.

        ``Refused`` if the files or answers differ from what was approved. The record is saved
        before the rename, so an interruption between them is finished by the next poll."""
        with self.lock:
            for record in self._records.values():
                if record.submission == sid:
                    return record
            files = submissions.files_folder(self.layout, sid)
            # context.json is made here from the answers; a left-over one (an earlier cut-short
            # attempt) is ours, since an upload may not carry that name.
            (files / "context.json").unlink(missing_ok=True)
            if submissions.digest(self.layout, sid, answers) != approved_digest:
                raise submissions.Refused(
                    "the documents or answers changed after approval; review the summary again"
                )
            (files / "context.json").write_bytes(submissions.context_bytes(answers))
            context = answers["context"]
            record = Record(
                self._new_id(),
                context["run"]["pathway"],
                context["identity"]["issuer_name"],
                "queued",
                self._utc(self.now()),
                issuer_id=context["identity"]["issuer_id"],
                issuer_name=context["identity"]["issuer_name"],
                as_of=context["run"]["as_of"],
                prepared=True,  # a submission arrives already checked
                submission=sid,
                modules=tuple(answers["modules"]),
                max_turns=answers["max_turns"],
                level=answers["level"],
                submitted_by=answers["submitted_by"],
            )
            self._put(record)
            self._move_files(record)
            return record

    def _reject_unrecorded_folders(self) -> None:
        """A folder or file in ``_engine/drops`` with no record was cut short before its record.

        Nothing is moved or deleted; the record says where the files are."""
        for folder in sorted(self.layout.drops.iterdir()):
            if folder.name in self._records or drops._is_noise(folder.name):
                continue  # a system file (.DS_Store, Thumbs.db) is not a claim
            with self._guard(f"folder {folder}"):
                self._put(
                    Record(
                        folder.name,
                        "",
                        folder.name,
                        "rejected",
                        self._utc(self.now()),
                        reason=_NO_RECORD.format(folder.name),
                        ended_at=self._utc(self.now()),
                    )
                )

    # -- shared helpers ---------------------------------------------------------------------

    @contextmanager
    def _guard(self, what: str) -> Iterator[None]:
        """Log an OSError with its traceback and carry on; the next poll retries."""
        try:
            yield
        except OSError:
            self._logger.exception("%s", what)

    def _utc(self, moment: datetime) -> str:
        return moment.astimezone(UTC).strftime(_TIME)

    def _put(self, record: Record) -> None:
        runs.save(self.layout, record)  # the in-memory copy changes only once the file has
        self._records[record.id] = record
        if record.status not in ("queued", "running"):
            self._remove_pid_file(record.id)

    def _remove_pid_file(self, run_id: str) -> None:
        try:
            runs.pid_file(self.layout, run_id).unlink(missing_ok=True)
        except OSError:
            self._logger.exception("run %s: its PID file could not be removed", run_id)

    def _with_status(self, status: str) -> list[Record]:
        return sorted((r for r in self._records.values() if r.status == status), key=lambda r: r.id)

    def _rebuild(self) -> Any:
        try:
            library = cpos_launch.update_library_at(self.layout.engine)
        except Exception as error:  # noqa: BLE001
            # Documented fail-open: the rebuild is display. Ended runs wait unfiled and the next
            # poll retries; the traceback is logged and the page says why. KeyboardInterrupt and
            # SystemExit (BaseException) still stop the watcher.
            self._rebuild_failed(f"library rebuild failed: {error}", f"{error}", exc=True)
            return None
        if library is None:
            self._rebuild_failed(
                "library rebuild skipped: update_library.py not found",
                "update_library.py not found",
            )
            return None
        self._rebuild_error = ""
        if self._logged_rebuild_error:
            self._logged_rebuild_error = ""
            self._logger.info("library rebuild works again")
        return library

    def _rebuild_failed(self, log_text: str, error: str, *, exc: bool = False) -> None:
        """Keep the page notice; write the log line only when the error differs from the last."""
        self._rebuild_error = _REBUILD_FAILED.format(error)
        if log_text != self._logged_rebuild_error:
            self._logged_rebuild_error = log_text
            if exc:
                self._logger.exception("library rebuild failed")
            else:
                self._logger.error("%s", log_text)

    # -- one poll ---------------------------------------------------------------------------

    def step(self) -> None:
        with self.lock:
            self._step()

    def _step(self) -> None:
        self._track_untracked()
        self._finish_moves()
        self._reap()
        self._scan()
        self._prepare_queued()
        self._start_queued()
        with self._guard("activity"):
            snapshot = activity.snapshot(
                self.layout,
                list(self._records.values()),
                cap=self.settings.cap,
                now=self.now(),
                kept=self._kept_activity,
                held="; ".join(
                    t
                    for t in (self._rebuild_error, self._limit_held, *self._unmovable_notes())
                    if t
                ),
            )
            activity.write(self.layout, snapshot)

    def run_forever(self) -> None:
        """Poll until interrupted. The runs it started keep going."""
        try:
            while True:
                self.step()
                time.sleep(self.settings.poll_seconds)
        except KeyboardInterrupt:
            pass
        finally:
            self.close()

    # -- reap and finish --------------------------------------------------------------------

    def _exit_of(self, record: Record) -> tuple[bool, int | None]:
        child = self._children.get(record.id)
        if child is not None:  # poll() only: alive() would reap it and hide the exit code
            code = child.poll()
            return code is not None, code
        return not runs.alive(record.pid), None  # adopted after a restart

    def _reap(self) -> None:
        ended: list[tuple[Record, int | None]] = []
        for record in self._with_status("running"):
            if record.pid == 0 and record.id not in self._children:
                continue  # inside the PID grace: _track_untracked decides it
            with self._guard(f"run {record.id}"):
                done, code = self._exit_of(record)
                if done:
                    ended.append((record, code))
        library = self._rebuild() if ended or self._rebuild_error else None
        if library is None:
            return  # nothing is decided without a rebuild; the next poll tries again
        for record, code in ended:
            with self._guard(f"run {record.id}"):
                self._put(self._decide(record, code, library))
                self._children.pop(record.id, None)
                self._stopped.pop(record.id, None)

    def _decide(self, record: Record, code: int | None, library: Any) -> Record:
        if record.id in self._stopped:  # its process was stopped because its record failed to save
            reason = self._stopped[record.id]
            return replace(record, status="failed", reason=reason, ended_at=self._utc(self.now()))
        state, reason = runs.outcome(self.layout, record, code)
        ended = replace(record, status=state, reason=reason, ended_at=self._utc(self.now()))
        if state != "finished":
            return ended
        if record.id not in {run["id"] for run in library.runs}:
            why = dict(library.excluded).get(record.id, "the library did not list it")
            return replace(ended, status="failed", reason=f"not listed: {why}")
        reports = sorted((self.layout.runs / record.id / "deliveries").glob("*/report.html"))
        if len(reports) != 1:
            reason = f"expected one deliveries/*/report.html, found {len(reports)}"
            return replace(ended, status="failed", reason=reason)
        if not (record.report and (self.layout.root / record.report).is_file()):
            try:
                filed = filing.file_report(
                    self.layout,
                    reports[0],
                    issuer_id=record.issuer_id,
                    issuer_name=record.issuer_name,
                    as_of=record.as_of,
                    pathway=record.pathway,
                    claimed=frozenset(
                        self.layout.root / r.report
                        for r in self._records.values()
                        if r.report and r.id != record.id
                    ),
                )
                _, differs = filing.issuer_folder(self.layout, record.issuer_id, record.issuer_name)
            except ValueError as error:  # a corrupt issuer registry; the report stays in its run
                self._logger.exception("run %s could not be filed", record.id)
                return replace(ended, status="failed", reason=f"could not be filed: {error}")
            # Kept in memory at once: if the save below fails, the retry must not file it again.
            record.report = filed.relative_to(self.layout.root).as_posix()
            record.name_differs = differs
        return replace(ended, report=record.report, name_differs=record.name_differs)

    # -- scan -------------------------------------------------------------------------------

    def _new_id(self) -> str:
        stamp = datetime.now(UTC) if self.now().tzinfo is None else self.now().astimezone(UTC)
        number = 1
        while True:
            name = f"{stamp:%Y%m%d-%H%M%S}-{number:02d}"
            taken = (
                self.layout.drops / name,
                self.layout.runs / name,
                self.layout.logs / f"{name}.log",
            )
            if name not in self._records and not any(os.path.lexists(p) for p in taken):
                return name
            number += 1

    def _scan(self) -> None:
        with self._guard("scan of the inbox"):
            found = drops.candidates(self.layout)
            listed = {entry for _, entry in found}
            self._tracker.forget_missing(listed)
            self._unreadable = {e: v for e, v in self._unreadable.items() if e in listed}
            self._unmovable = {e: v for e, v in self._unmovable.items() if e in listed}
            for pathway, entry in found:
                with self._guard(f"drop {entry}"):
                    if self._tracker.ready(entry):
                        self._claim(pathway, entry, None)
                    else:
                        self._watch_unreadable(pathway, entry)

    def _watch_unreadable(self, pathway: str, entry: Path) -> None:
        """A drop that cannot be read is rejected once that has lasted past the settle time and
        nothing in it has changed for as long: a copy still arriving is left alone."""
        error = drops.unreadable(entry)
        if error is None:
            self._unreadable.pop(entry, None)
            return
        first, _ = self._unreadable.setdefault(entry, (self.clock(), error))
        since = max(first, self._tracker.unchanged_since(entry) or first)
        if self.clock() - since > self.settings.settle_seconds:
            del self._unreadable[entry]
            self._claim(pathway, entry, f"cannot be read: {error}")

    def _claim(self, pathway: str, entry: Path, refusal: str | None) -> None:
        """Move a drop out of the inbox and record it at once. ``refusal`` rejects it unchecked."""
        record_id = self._new_id()
        try:
            folder = drops.claim(self.layout, entry, record_id)
        except OSError as error:  # it will not move (rights, another volume): say so, once
            self._note_unmovable(entry, error)
            return
        self._unmovable.pop(entry, None)
        if folder is None:
            return
        record = Record(record_id, pathway, entry.name, "queued", self._utc(self.now()))
        try:
            self._put(record)
        except OSError:  # no record exists, so the drop goes back for the next poll
            self._logger.exception("drop %s (%s)", entry, record_id)
            self._put_back(folder, entry)
            return
        if refusal:
            self._reject(record, refusal)

    def _note_unmovable(self, entry: Path, error: OSError) -> None:
        """Log a drop that cannot be moved once per distinct error; the page shows it as held."""
        text = error.strerror or type(error).__name__  # not str(): it holds the claim ID
        if self._unmovable.get(entry) != text:
            self._logger.error(
                "drop %s is ready but cannot be moved out of the inbox: %s", entry, text
            )
        self._unmovable[entry] = text

    def _unmovable_notes(self) -> list[str]:
        return [
            f"{entry.name} cannot be moved out of the inbox: {text}"
            for entry, text in sorted(self._unmovable.items())
        ]

    def _put_back(self, folder: Path, entry: Path) -> None:
        """Return a claimed drop whose record could not be saved to where it was."""
        if folder.exists() and not os.path.lexists(entry):
            with self._guard(f"returning {folder} to the inbox"):
                os.rename(folder, entry)

    def _reject(self, record: Record, reason: str) -> None:
        """Record the drop as rejected, then move it to ``inbox/failed``; it never goes back.

        The record comes first: if saving it fails nothing has moved and the next poll retries."""
        ended = replace(record, status="rejected", reason=reason, ended_at=self._utc(self.now()))
        drop = self.layout.drops / record.id
        if not os.path.lexists(drop):
            self._put(
                replace(ended, reason=f"{reason}; its folder was not found in {_KEPT}{record.id}")
            )
            return
        self._put(ended)
        try:
            self.layout.failed.mkdir(parents=True, exist_ok=True)
            drops.reject(self.layout, drop, record.folder, reason, self.now())
        except OSError as error:
            self._logger.exception("run %s could not be moved to inbox/failed", record.id)
            why = (
                f"{reason} (the folder could not be moved to inbox/failed: {error}; "
                f"it is kept in {_KEPT}{record.id})"
            )
            self._put(replace(ended, reason=why))

    # -- prepare ----------------------------------------------------------------------------

    def _prepare_queued(self) -> None:
        for record in self._with_status("queued"):
            if not record.prepared:
                with self._guard(f"run {record.id}"):
                    self._prepare(record)

    def _prepare(self, record: Record) -> None:
        """Check a claimed drop and run the offline check. An interruption leaves it unprepared."""
        try:
            checked = drops.check(self.layout.drops / record.id, record.pathway)
            identity = checked.run.identity
            record = replace(
                record,
                issuer_id=identity.issuer_id,
                issuer_name=identity.issuer_name,
                as_of=checked.run.run.as_of,
                files=checked.files,
            )
            reason = runs.prepare(
                self.layout,
                record,
                checked.context,
                launcher=self.settings.launcher,
                config=self.settings.config,
                cap=self.settings.cap,
            )
        except DropRejected as error:
            reason = str(error)
        except OSError as error:
            self._logger.exception("run %s could not be checked", record.id)
            reason = f"could not be checked: {error}"
        if reason:
            self._reject(record, reason)
        else:
            self._put(replace(record, prepared=True))

    # -- start ------------------------------------------------------------------------------

    def _started_today(self) -> int:
        # Each moment's own local date, by the machine's time-zone rules: on a clock-change day
        # the offset of "now" would put the day's first hour on the day before.
        today = self.now().astimezone().date()
        count = 0
        for record in self._records.values():
            if not record.started_at:
                continue
            try:
                started = datetime.strptime(record.started_at, _TIME).replace(tzinfo=UTC)
            except ValueError:
                # Fail closed: an unreadable time counts toward today's limit.
                self._logger.warning(
                    "run %s: started_at %r unreadable", record.id, record.started_at
                )
                count += 1
                continue
            count += started.astimezone().date() == today
        return count

    def _start_queued(self) -> None:
        today = self._started_today()
        self._limit_held = ""
        for record in self._with_status("queued"):
            if not record.prepared:
                continue
            if today >= self.settings.max_per_day:  # first: shown even while every slot is busy
                limit = self.settings.max_per_day
                self._limit_held = f"daily limit of {limit} runs reached; waiting until tomorrow"
                break
            if len(self._with_status("running")) >= self.settings.max_running:
                break
            with self._guard(f"run {record.id}"):
                today += self._launch(record)

    def _launch(self, record: Record) -> bool:
        """Start one run. True once it is recorded as started (and so counted for the day)."""
        try:
            context = drops.check(self.layout.drops / record.id, record.pathway).context
        except DropRejected as error:  # changed since the offline check
            reason = str(error)
            self._put(
                replace(record, status="failed", reason=reason, ended_at=self._utc(self.now()))
            )
            return False
        running = replace(record, status="running", started_at=self._utc(self.now()), pid=0)
        self._put(running)  # first: whatever happens next, this run is counted and never repeated
        try:
            child = runs.start(
                self.layout,
                running,
                context,
                launcher=self.settings.launcher,
                config=self.settings.config,
                cap=self.settings.cap,
                ruling=startup.STANDING_RULING,  # start-up proved settings.ruling is this file
            )
        except OSError as error:
            self._logger.exception("run %s could not be started", record.id)
            reason = f"could not be started: {error}"
            self._put(
                replace(running, status="failed", reason=reason, ended_at=self._utc(self.now()))
            )
            return True
        self._children[record.id] = child
        try:
            self._put(replace(running, pid=child.pid))
        except BaseException as error:
            _stop(child)  # a run nobody can track must not keep spending
            if not isinstance(error, OSError):
                self._children.pop(record.id, None)
                raise
            # The process has ended; the next poll reaps it through the Popen kept in _children.
            self._stopped[record.id] = (
                f"stopped by the watcher: its record could not be saved ({error})"
            )
            self._logger.exception("run %s: its process ID could not be saved", record.id)
        return True


def _amount(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"{text!r} is not an amount") from None
    return value


def _parser() -> argparse.ArgumentParser:
    defaults = Settings(Path("."))
    parser = argparse.ArgumentParser(prog="python -m deploy_workflow.inbox.watcher")
    parser.add_argument("--root", type=Path, required=True, help="the shared folder")
    parser.add_argument("--config", choices=tuple(CONFIGS), default=defaults.config)
    parser.add_argument("--cap", type=_amount, default=defaults.cap, help="USD per run")
    parser.add_argument("--max-running", type=int, default=defaults.max_running)
    parser.add_argument("--max-per-day", type=int, default=defaults.max_per_day)
    parser.add_argument("--settle-seconds", type=float, default=defaults.settle_seconds)
    parser.add_argument("--poll-seconds", type=float, default=defaults.poll_seconds)
    parser.add_argument("--ruling", type=Path, default=defaults.ruling)
    return parser


def _unusable(args: argparse.Namespace) -> str:
    """Why the watcher cannot poll with these settings, else "". A poll interval of zero spins,
    a negative one stops the first sleep, and a limit below one never starts a run."""
    if not (math.isfinite(args.poll_seconds) and args.poll_seconds > 0):
        return "--poll-seconds must be a finite number above zero"
    if not (math.isfinite(args.settle_seconds) and args.settle_seconds >= 0):
        return "--settle-seconds must be a finite number, zero or more"
    if args.max_running < 1:
        return "--max-running must be at least 1"
    if args.max_per_day < 1:
        return "--max-per-day must be at least 1"
    return ""


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not (args.cap.is_finite() and args.cap > 0):
        print("--cap must be a finite amount above zero", file=sys.stderr)
        return 2
    refused = _unusable(args)
    if refused:
        print(refused, file=sys.stderr)
        return 2
    settings = Settings(
        args.root,
        config=args.config,
        cap=args.cap,
        max_running=args.max_running,
        max_per_day=args.max_per_day,
        settle_seconds=args.settle_seconds,
        poll_seconds=args.poll_seconds,
        ruling=args.ruling,
    )
    try:
        watcher = Watcher(settings)
    except (ValueError, OSError) as error:  # StartupRefused, a long root, an unreadable record
        print(error, file=sys.stderr)
        return 2
    watcher.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
