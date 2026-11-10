"""Run activity for the library page: module progress, spend and the written activity.js."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from deploy_vii.contracts import PATHWAY_MODULES, PathwayId
from deploy_vii.registry import plan
from deploy_workflow import platform_io
from deploy_workflow.inbox.drops import Layout
from deploy_workflow.inbox.runs import Record
from deploy_workflow.model.budget import BudgetError, exact_sum, read_reservation_snapshot
from deploy_workflow.model.pricing import money_text
from deploy_workflow.owners.cpos_launch import NOT_ANALYTICAL
from deploy_workflow.run_events import EVENTS, read_events

log = logging.getLogger(__name__)

STALLED_AFTER = 3600  # seconds without a new event
KEPT_ENDED = 200
# Ended statuses whose launcher the watcher knows is gone: _reap saw it exit, or it never started.
# "interrupted" is excluded: a run cut short before its process ID was saved may still spend.
# So is a run with a start time but no process ID, whatever its status: "failed: could not be
# started" after Popen (watcher start path) leaves a live child; see _shown.
_SETTLED = frozenset({"finished", "failed", "capped", "rejected"})
_TIME = "%Y-%m-%dT%H:%M:%SZ"
_ORDER = {"running": 0, "queued": 1}


def _state(module: str, started: set[str], accepted: set[str]) -> str:
    if module in accepted:
        return "done"
    return "running" if module in started else "waiting"


def module_states(pathway: str, events: Sequence[Mapping[str, Any]]) -> list[list[str]]:
    """[[module, done|running|waiting], ...] in plan order, then the final Report entry."""
    started = {str(e.get("module")) for e in events if e.get("event") == "module_started"}
    accepted = {str(e.get("module")) for e in events if e.get("event") == "module_accepted"}
    modules = plan(
        tuple(m for m in PATHWAY_MODULES[cast(PathwayId, pathway)] if m not in NOT_ANALYTICAL)
    )
    states = [[m, _state(m, started, accepted)] for m in modules]
    names = {e.get("event") for e in events}
    report = "waiting"
    if "delivered" in names:
        report = "done"
    elif "delivery_started" in names:
        report = "running"
    return [*states, ["Report", report]]


def spent(run_dir: Path) -> Decimal | None:
    """Settled charges plus the full hold of unknown ones; None when the journal cannot be read."""
    live = run_dir / "live"
    try:
        if not live.exists() and not live.is_symlink():
            return Decimal(0)
        if not live.is_dir():
            raise BudgetError("live is not a folder")
        amounts = [
            item.settled_usd
            if item.status in ("settled", "overrun") and item.settled_usd is not None
            else item.usd
            for item in read_reservation_snapshot(live)
            if item.status in ("settled", "overrun", "unknown", None)
        ]
        return exact_sum(amounts)
    except (BudgetError, OSError) as error:
        # Documented fail-open (display only): an unreadable journal shows as an unknown spend.
        log.warning(
            "budget journal under %s unreadable (%s); spend shown as unknown", run_dir, error
        )
        return None


def _events(run_dir: Path, run_id: str) -> tuple[list[dict[str, Any]], bool]:
    """The events, and whether the log was read (False: the fail-open below was taken)."""
    try:
        # A valid JSON line need not be an event; only objects are kept.
        return [e for e in read_events(run_dir / EVENTS) if isinstance(e, dict)], True
    except FileNotFoundError:
        return [], True  # no log yet (a prepared run waiting for a slot): nothing to report
    except (OSError, ValueError) as error:
        # Documented fail-open (display only): an unreadable log shows every module as waiting.
        log.warning("run %s: event log unreadable (%s); modules shown as waiting", run_id, error)
        return [], False


def _age_seconds(
    record: Record, events: Sequence[Mapping[str, Any]], now: datetime
) -> float | None:
    last = str(events[-1].get("at", "")) if events else ""
    text = last or record.started_at
    if not text:  # Nothing to measure from: simply not stalled.
        return None
    try:
        then = datetime.fromisoformat(text)
    except ValueError:
        log.warning("run %s: time %r cannot be parsed; stall check skipped", record.id, text)
        return None
    if then.tzinfo is None:
        then = then.replace(tzinfo=UTC)
    return (now.astimezone(UTC) - then).total_seconds()


def _entry(layout: Layout, record: Record, now: datetime) -> tuple[dict[str, Any], bool]:
    """The run's entry, and whether it is complete: a rejected run reads nothing, and any other
    run is complete only when its folder was visible and neither fail-open below was taken."""
    entry: dict[str, Any] = asdict(record)
    entry["files"] = list(record.files)
    run_dir = layout.runs / record.id
    events: list[dict[str, Any]] = []
    complete = record.status == "rejected"
    if record.status != "rejected" and run_dir.is_dir():
        events, readable = _events(run_dir, record.id)
        entry["modules"] = module_states(record.pathway, events)
        amount = spent(run_dir)
        entry["spent"] = None if amount is None else money_text(amount)
        complete = readable and amount is not None
    if record.status == "running":
        age = _age_seconds(record, events, now)
        if age is not None and age > STALLED_AFTER:
            entry["stalled"] = True
    return entry, complete


def _shown(
    layout: Layout, record: Record, now: datetime, kept: dict[str, tuple[Record, dict[str, Any]]]
) -> dict[str, Any]:
    """The entry for a shown run; an ended run with a gone launcher is read once, not per poll."""
    if record.status not in _SETTLED or (record.started_at and not record.pid):
        return _entry(layout, record, now)[0]
    saved = kept.get(record.id)
    if saved is not None and saved[0] == record:  # any changed field is a miss
        return saved[1]
    entry, complete = _entry(layout, record, now)
    if complete:  # a fail-open result is read again next poll
        kept[record.id] = (replace(record), entry)
    return entry


def snapshot(  # noqa: PLR0913 - one more argument: the caller's store of finished entries
    layout: Layout,
    records: Sequence[Record],
    *,
    cap: Decimal,
    now: datetime,
    held: str = "",
    kept: dict[str, tuple[Record, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """``kept`` is the caller's store of finished entries (run ID -> record, entry); pass the
    same dict on every poll to read each ended run once. It is pruned to the runs shown."""
    store = {} if kept is None else kept
    live = [r for r in records if r.status in _ORDER]
    live.sort(key=lambda r: (_ORDER[r.status], r.id))
    ended = [r for r in records if r.status not in _ORDER]
    ended.sort(key=lambda r: (r.ended_at or r.claimed_at, r.id), reverse=True)
    shown = [*live, *ended[:KEPT_ENDED]]
    runs = [_shown(layout, r, now, store) for r in shown]
    for run_id in store.keys() - {r.id for r in shown}:
        del store[run_id]
    return {
        "updated": now.astimezone(UTC).strftime(_TIME),
        "cap": str(cap),
        "held": held,
        "runs": runs,
    }


def write(layout: Layout, data: Mapping[str, Any]) -> None:
    """Write _engine/activity.js through a temporary file, then ``os.replace`` it."""
    text = json.dumps(data, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c")
    layout.engine.mkdir(parents=True, exist_ok=True)
    target = layout.engine / "activity.js"
    descriptor, name = tempfile.mkstemp(dir=layout.engine, prefix="activity.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(
                f"window.RUN_ACTIVITY={text};window.onRunActivity&&window.onRunActivity();\n"
            )
        platform_io.replace(name, target)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise
