"""The scheduler: the one long-running part that turns submitted runs into filed reports.

Each poll it reaps ended runs, starts queued runs within the limits, files finished reports and
publishes run activity. A record is saved before every step that an interruption could cut short,
so a restart always finds what to do next: a run is marked running (and counted) before its
process starts, and is shown as finished only when the library lists it.

``submit`` takes an approved submission from the start page: under ``lock`` (also held by every
poll) it saves the run's record, then renames the sealed files folder to ``drops/<id>``. A record
whose folder is still missing is finished by the next poll or restart; one submission is never
two records. Records written by the earlier folder watcher still load and show in Run activity;
every run it left queued (one with no submission) is marked failed at start-up, and none of them
is ever started: only Submit on an approved summary starts a run.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import IO, Any

from deploy_workflow.context import load_context
from deploy_workflow.inbox import activity, filing, layout, runs, startup
from deploy_workflow.inbox.runs import Record
from deploy_workflow.inbox.startup import StartupRefused
from deploy_workflow.owners import cpos_launch
from deploy_workflow.run_start import submissions
from deploy_workflow.run_start.submissions import Answers

__all__ = ["MAX_QUEUED", "Scheduler", "Settings", "StartupRefused"]

_TIME = "%Y-%m-%dT%H:%M:%SZ"
_REBUILD_FAILED = "the library could not be rebuilt ({}); ended runs wait for it"
_CUT_SHORT = (
    "the service stopped while starting this run; its process may still be running"
    " \N{EM DASH} check before submitting it again"
)
_OLD_WATCHER = (
    "queued by the folder watcher before the run start page replaced it;"
    " submit it again from the run start page"
)
_NO_CONTEXT = "no context.json in _engine/drops/{}; submit it again from the run page"
# ponytail: a run whose launcher writes its PID file after 60 s is cut short; a reused process ID
# after a reboot reads as alive. Both are known ceilings, not handled.
_PID_GRACE_SECONDS = 60
_SID = re.compile(r"[0-9a-f]{32}")
_CHANGED = "the submitted documents changed before the run could start"
# Ceiling on submissions waiting for a slot: their files sit outside the uploads store limit.
MAX_QUEUED = 30


@dataclass(frozen=True)
class Settings:
    root: Path
    cap: Decimal = Decimal(20)
    max_running: int = 3
    max_per_day: int = 30
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


class Scheduler:
    def __init__(
        self,
        settings: Settings,
        *,
        clock: Callable[[], float] = time.time,
        now: Callable[[], datetime] = _local_now,
    ) -> None:
        self.settings, self.clock, self.now = settings, clock, now
        self.layout = layout.ensure_layout(settings.root)
        startup.check_launchable(settings.ruling, settings.cap)
        self._lock: IO[str] | None = startup.take_lock(self.layout)
        self._logger = startup.open_log(self.layout, __name__)  # only the lock holder logs
        self.lock = threading.Lock()  # held by step() and submit(): a submit never splits a poll
        self._records = {r.id: r for r in runs.load_all(self.layout)}
        self._children: dict[str, subprocess.Popen[bytes]] = {}
        self._rebuild_error = ""
        self._logged_rebuild_error = ""  # the last rebuild error written to the log
        self._stopped: dict[str, str] = {}  # run ID -> why the scheduler stopped its process
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
        """Decide what an earlier stop left: runs cut short while starting, half-finished moves,
        and runs the earlier folder watcher queued without ever checking."""
        self._track_untracked()
        self._finish_moves()
        self._fail_unchecked()

    def _fail_unchecked(self) -> None:
        """A queued record with no ``submission`` was queued by the old folder watcher. Only a run
        started by Submit on an approved summary may start (ruling 2026-11-11): fail it, with the
        reason, rather than leave it waiting (and counted against the queue limit) for ever."""
        for record in self._with_status("queued"):
            if not record.submission:
                with self._guard(f"run {record.id}"):
                    self._fail(record, _OLD_WATCHER)

    def _fail(self, record: Record, reason: str) -> None:
        self._put(replace(record, status="failed", reason=reason, ended_at=self._utc(self.now())))

    def _track_untracked(self) -> None:
        """A running record with no PID and no child of this scheduler was cut short between the
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
        record and the rename: finish the rename, once the files are shown to be the approved ones.

        A record is failed only when that check fails; a rename that fails is retried."""
        for record in self._with_status("queued"):
            if record.submission and not os.path.lexists(self.layout.drops / record.id):
                with self._guard(f"submission {record.submission}"):
                    self._move_files(record)

    def _sealed(self, record: Record) -> Path:
        return self.layout.uploads / record.submission / "sealed"

    def _move_files(self, record: Record) -> None:
        sealed = self._sealed(record)
        if not sealed.is_dir() or sealed.is_symlink():
            return
        if self._sealed_digest(record, sealed) != record.digest or not record.digest:
            self._put(
                replace(
                    record,
                    status="failed",
                    reason=_CHANGED,
                    ended_at=self._utc(self.now()),
                )
            )
            return
        os.rename(sealed, self.layout.drops / record.id)
        submissions.release(self.layout, record.submission)

    def _sealed_digest(self, record: Record, sealed: Path) -> str:
        """The approval digest of the sealed files as ``submit`` computed it (the digest ignores the
        ``context.json`` it wrote there); "" when that cannot be recomputed (it then fails)."""
        try:
            answers = submissions.validated(
                {
                    "context": json.loads((sealed / "context.json").read_bytes()),
                    "modules": list(record.modules),
                    "max_turns": record.max_turns,
                    "level": record.level,
                    "model": record.model,
                    "effort": record.effort,
                    "submitted_by": record.submitted_by,
                }
            )
        except (OSError, ValueError):  # no or unreadable context.json: it changed
            return ""
        try:
            return submissions.bound(
                submissions.digest(self.layout, record.submission, answers), record.prior
            )
        except submissions.Refused:
            return ""

    def submit(self, sid: str, answers: Answers, approved_digest: str) -> Record:
        """Start one run for an approved submission. Repeating a submission returns its record.

        ``Refused`` if the answers are not valid, a module is unknown, or the approval is not the
        digest this service issued for exactly the files and answers now held. The files are
        sealed first (no upload or removal lands after that), checked, then the record is saved
        and only then is the sealed folder renamed, so an interruption between them is finished
        by the next poll against the digest the record keeps."""
        with self.lock:
            answers = submissions.validated(answers)
            submissions.require_provider_key(answers)
            try:  # a context the launcher would refuse, or a deactivated pathway, is a 400
                run = load_context(submissions.context_bytes(answers)).run
                cpos_launch.refuse_deactivated(run.pathway)
            except ValueError as refusal:
                raise submissions.Refused(str(refusal)) from refusal
            if not isinstance(sid, str) or not _SID.fullmatch(sid):
                raise submissions.Refused("unknown submission")
            for record in self._records.values():
                if record.submission == sid:
                    return record
            for name in answers["modules"]:
                if name not in cpos_launch.METHODS:
                    raise submissions.Refused(f"unknown module {name}")
            if len(self._with_status("queued")) >= MAX_QUEUED:
                raise submissions.Refused("too many runs are waiting; try again later")
            sealed = submissions.seal(self.layout, sid)
            try:
                record = self._record_for(sid, answers, approved_digest, sealed)
            except BaseException:
                submissions.unseal(self.layout, sid)
                raise
            os.rename(sealed, self.layout.drops / record.id)
            submissions.release(self.layout, sid)
            return record

    def _record_for(self, sid: str, answers: Answers, approved_digest: str, sealed: Path) -> Record:
        """Check the sealed files against the issued approval, write ``context.json`` into them
        and save the queued record. Nothing has moved when this raises."""
        # context.json is made here from the answers; a left-over one (an earlier cut-short
        # attempt) is ours, since an upload may not carry that name.
        (sealed / "context.json").unlink(missing_ok=True)
        prior = submissions.issued_prior(self.layout, sid)
        current = submissions.bound(submissions.digest(self.layout, sid, answers), prior)
        if not approved_digest or not (
            approved_digest == submissions.issued(self.layout, sid) == current
        ):
            raise submissions.Refused(
                "the documents or answers changed after approval; review the summary again"
            )
        (sealed / "context.json").write_bytes(submissions.context_bytes(answers))
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
            model=answers["model"],
            effort=answers["effort"],
            submitted_by=answers["submitted_by"],
            digest=current,
            prior=prior,
        )
        self._put(record)
        return record

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
            # SystemExit (BaseException) still stop the scheduler.
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
        with self._guard("sweep of the uploads"):
            queued = frozenset(r.submission for r in self._with_status("queued") if r.submission)
            submissions.sweep(self.layout, self.clock(), queued)
        self._reap()
        self._start_queued()
        with self._guard("activity"):
            snapshot = activity.snapshot(
                self.layout,
                list(self._records.values()),
                cap=self.settings.cap,
                now=self.now(),
                kept=self._kept_activity,
                held="; ".join(t for t in (self._rebuild_error, self._limit_held) if t),
            )
            activity.write(self.layout, snapshot)

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
        deliveries = sorted((self.layout.runs / record.id / "deliveries").glob("*/delivery.json"))
        if len(deliveries) != 1:
            reason = f"expected one deliveries/*/delivery.json, found {len(deliveries)}"
            return replace(ended, status="failed", reason=reason)
        # A delivery has no report page: the library shows the run itself, so nothing is filed.
        # An earlier-format delivery that still holds one is filed as before.
        page = deliveries[0].with_name("report.html")
        if page.is_file() and not (record.report and (self.layout.root / record.report).is_file()):
            try:
                filed = filing.file_report(
                    self.layout,
                    page,
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

    # -- ids --------------------------------------------------------------------------------

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
        if not record.submission or not record.digest:
            self._fail(record, _OLD_WATCHER)  # only Submit on an approved summary starts a run
            return False
        drop = self.layout.drops / record.id
        if not os.path.lexists(drop) and self._sealed(record).is_dir():
            return False  # its move is not finished yet (a failed rename): _finish_moves retries
        context = drop / "context.json"
        if context.is_symlink() or not context.is_file():
            # A folder that has lost its context file: failed with the reason, never started.
            self._put(
                replace(
                    record,
                    status="failed",
                    reason=_NO_CONTEXT.format(record.id),
                    ended_at=self._utc(self.now()),
                )
            )
            return False
        try:
            runs.command(  # a record that cannot become a command fails here, before it is counted
                self.layout,
                record,
                context,
                launcher=self.settings.launcher,
                cap=self.settings.cap,
                ruling=startup.STANDING_RULING,
            )
        except (ValueError, TypeError) as error:
            # Documented fail-open: a hand-edited or wrongly typed field must not stop the poll for
            # every other run. Logged with the run's ID; the record is failed and uses no slot.
            self._logger.exception("run %s cannot be built into a command", record.id)
            reason = f"could not be started: {error}"
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
                cap=self.settings.cap,
                ruling=startup.STANDING_RULING,  # start-up proved settings.ruling is this file
            )
        except (OSError, ValueError, TypeError) as error:
            # Documented fail-open: one record that cannot be turned into a command or started (a
            # hand-edited or wrongly typed field raises ValueError or TypeError, not only OSError)
            # must not stop the poll for every other run. The traceback is logged with the run's
            # ID and the record is marked failed with the error text; nothing else is hidden.
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
                f"stopped by the scheduler: its record could not be saved ({error})"
            )
            self._logger.exception("run %s: its process ID could not be saved", record.id)
        return True
