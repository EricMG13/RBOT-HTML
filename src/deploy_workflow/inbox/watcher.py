"""The inbox watcher: the one long-running process that turns drops into filed reports.

Each poll it reaps ended runs, scans the inbox, starts queued runs within the limits and publishes
run activity. A drop leaves the inbox in one rename, a run record is saved before and after its
process starts, and a run is shown as finished only when the library lists it.
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from deploy_workflow.inbox import activity, drops, filing, runs
from deploy_workflow.inbox.drops import DropRejected
from deploy_workflow.inbox.runs import Record
from deploy_workflow.model.adapter import (
    COPILOT_RUNTIME_VARIABLE,
    KEY_VARIABLES,
    LivePauseInForce,
    check_ruling,
)
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.owners import cpos_launch

ROOT = Path(__file__).resolve().parents[3]
_TIME = "%Y-%m-%dT%H:%M:%SZ"
_FORM = ROOT / "docs/templates/context-form.html"
_PAGE = (
    '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
    '<meta http-equiv="refresh" content="0; url=_engine/library/index.html">'
    "<title>Issuer library</title></head><body>"
    '<p><a href="_engine/library/index.html">Open the issuer library</a></p></body></html>\n'
)


class StartupRefused(ValueError):
    """The watcher cannot launch runs, or another watcher already owns this folder."""


@dataclass(frozen=True)
class Settings:
    root: Path
    config: str = "sol-medium"
    cap: Decimal = Decimal(20)
    max_running: int = 3
    max_per_day: int = 30
    settle_seconds: float = 120
    poll_seconds: float = 10
    ruling: Path = ROOT / "docs/rulings/2026-11-09-inbox-automation.md"
    launcher: tuple[str, ...] = (sys.executable, "-m", "deploy_workflow.owners.cpos_launch")


def _local_now() -> datetime:
    return datetime.now().astimezone()


def _stop(child: subprocess.Popen[bytes]) -> None:
    child.terminate()
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait()


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
        self._logger = self._open_log()
        self._check_launchable()
        self._records = {r.id: r for r in runs.load_all(self.layout)}
        self._children: dict[str, subprocess.Popen[bytes]] = {}
        self._tracker = drops.ReadyTracker(settings.settle_seconds, clock)
        self._unreadable: dict[Path, tuple[float, str]] = {}
        self._held = ""
        self._take_lock()
        self._write_pages()
        self._rebuild()

    # -- start-up ---------------------------------------------------------------------------

    def _open_log(self) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.{self.layout.root}")
        if not logger.handlers:
            handler = logging.FileHandler(self.layout.logs / "watcher.log", encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _check_launchable(self) -> None:
        config = CONFIGS.get(self.settings.config)
        if config is None:
            raise StartupRefused(f"unknown config {self.settings.config!r}")
        try:
            check_ruling(self.settings.config, self.settings.ruling)
        except (LivePauseInForce, ValueError, OSError) as error:
            raise StartupRefused(f"live runs are not allowed: {error}") from error
        key = KEY_VARIABLES[config.provider]
        if not os.environ.get(key):
            raise StartupRefused(f"{key} is not set in the launching environment")
        runtime = Path(os.environ.get(COPILOT_RUNTIME_VARIABLE, ""))
        if config.provider == "copilot" and not runtime.is_file():
            raise StartupRefused(f"{COPILOT_RUNTIME_VARIABLE} must name an existing file")

    def _take_lock(self) -> None:
        lock = self.layout.engine / "watcher.lock"
        mine = str(os.getpid())
        try:
            descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            try:
                other = int(lock.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                other = 0  # unreadable: treated as stale
            if other != os.getpid() and runs.alive(other):
                raise StartupRefused(
                    f"another watcher (pid {other}) is running on this folder"
                ) from None
            lock.write_text(mine, encoding="utf-8")  # stale: its process is gone
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(mine)

    def _release_lock(self) -> None:
        lock = self.layout.engine / "watcher.lock"
        with self._guard("watcher.lock"):
            if lock.read_text(encoding="utf-8").strip() == str(os.getpid()):
                lock.unlink()

    def _write_pages(self) -> None:
        try:
            with (self.layout.root / "library.html").open("xb") as page:
                page.write(_PAGE.encode())
        except FileExistsError:
            pass  # never overwritten
        drops.write_templates(self.layout, _FORM)

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

    def _with_status(self, status: str) -> list[Record]:
        return sorted((r for r in self._records.values() if r.status == status), key=lambda r: r.id)

    def _rebuild(self) -> Any:
        try:
            library = cpos_launch.update_library_at(self.layout.engine)
        except (OSError, ValueError, ImportError):
            self._logger.exception("library rebuild failed")
            return None
        if library is None:
            self._logger.error("library rebuild skipped: update_library.py not found")
        return library

    # -- one poll ---------------------------------------------------------------------------

    def step(self) -> None:
        self._reap()
        self._scan()
        self._start_queued()
        with self._guard("activity"):
            snapshot = activity.snapshot(
                self.layout,
                list(self._records.values()),
                cap=self.settings.cap,
                now=self.now(),
                held=self._held,
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
            self._release_lock()

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
            with self._guard(f"run {record.id}"):
                done, code = self._exit_of(record)
                if done:
                    ended.append((record, code))
        library = self._rebuild() if ended else None
        if library is None:
            return  # nothing is decided without a rebuild; the next poll tries again
        for record, code in ended:
            with self._guard(f"run {record.id}"):
                self._put(self._decide(record, code, library))
                self._children.pop(record.id, None)

    def _decide(self, record: Record, code: int | None, library: Any) -> Record:
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
        filed = filing.file_report(
            self.layout,
            reports[0],
            issuer_id=record.issuer_id,
            issuer_name=record.issuer_name,
            as_of=record.as_of,
            pathway=record.pathway,
        )
        _, differs = filing.issuer_folder(self.layout, record.issuer_id, record.issuer_name)
        return replace(
            ended, report=filed.relative_to(self.layout.root).as_posix(), name_differs=differs
        )

    # -- scan -------------------------------------------------------------------------------

    def _new_id(self) -> str:
        stamp = datetime.now(UTC) if self.now().tzinfo is None else self.now().astimezone(UTC)
        number = 1
        while True:
            name = f"{stamp:%Y%m%d-%H%M%S}-{number:02d}"
            if name not in self._records and not os.path.lexists(self.layout.drops / name):
                return name
            number += 1

    def _scan(self) -> None:
        with self._guard("scan of the inbox"):
            found = drops.candidates(self.layout)
            listed = {entry for _, entry in found}
            self._tracker.forget_missing(listed)
            self._unreadable = {e: v for e, v in self._unreadable.items() if e in listed}
            for pathway, entry in found:
                with self._guard(f"drop {entry}"):
                    if self._tracker.ready(entry):
                        self._admit(pathway, entry, None)
                    else:
                        self._watch_unreadable(pathway, entry)

    def _watch_unreadable(self, pathway: str, entry: Path) -> None:
        """A drop that cannot be listed is rejected once that has lasted past the settle time."""
        try:
            drops.signature(entry)
        except OSError as error:
            first, _ = self._unreadable.setdefault(entry, (self.clock(), str(error)))
            if self.clock() - first > self.settings.settle_seconds:
                del self._unreadable[entry]
                self._admit(pathway, entry, f"cannot be read: {error}")
        else:
            self._unreadable.pop(entry, None)

    def _admit(self, pathway: str, entry: Path, refusal: str | None) -> None:
        """Claim a drop, check it and queue or reject it. ``refusal`` rejects it unchecked."""
        record_id = self._new_id()
        folder = drops.claim(self.layout, entry, record_id)
        if folder is None:
            return
        record = Record(record_id, pathway, entry.name, "queued", self._utc(self.now()))
        try:
            reason = refusal
            if reason is None:
                try:
                    checked = drops.check(folder, pathway)
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
            if reason:
                drops.reject(self.layout, folder, entry.name, reason, self.now())
                record = replace(
                    record, status="rejected", reason=reason, ended_at=self._utc(self.now())
                )
            self._put(record)
        except OSError:
            self._logger.exception("drop %s (%s)", entry, record_id)
            self._put_back(folder, entry)

    def _put_back(self, folder: Path, entry: Path) -> None:
        """Return a claimed drop to the inbox so the next poll tries it again."""
        if folder.exists() and not os.path.lexists(entry):
            with self._guard(f"returning {folder} to the inbox"):
                os.rename(folder, entry)

    # -- start ------------------------------------------------------------------------------

    def _started_today(self) -> int:
        today = self.now()
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
            count += started.astimezone(today.tzinfo).date() == today.date()
        return count

    def _start_queued(self) -> None:
        today = self._started_today()
        self._held = ""
        for record in self._with_status("queued"):
            if len(self._with_status("running")) >= self.settings.max_running:
                break
            if today >= self.settings.max_per_day:
                limit = self.settings.max_per_day
                self._held = f"daily limit of {limit} runs reached; waiting until tomorrow"
                break
            with self._guard(f"run {record.id}"):
                today += self._launch(record)

    def _launch(self, record: Record) -> bool:
        try:
            context = drops.check(self.layout.drops / record.id, record.pathway).context
        except DropRejected as error:
            ended = self._utc(self.now())
            self._put(replace(record, status="failed", reason=f"{error}", ended_at=ended))
            return False
        child = runs.start(
            self.layout,
            record,
            context,
            launcher=self.settings.launcher,
            config=self.settings.config,
            cap=self.settings.cap,
            ruling=self.settings.ruling,
        )
        try:
            self._put(
                replace(record, status="running", pid=child.pid, started_at=self._utc(self.now()))
            )
        except OSError:
            _stop(child)  # a run nobody is tracking must not keep spending
            raise
        self._children[record.id] = child
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


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.cap > 0:
        print("--cap must be a positive amount", file=sys.stderr)
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
