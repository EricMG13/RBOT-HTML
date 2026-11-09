"""Run activity for the library page: module progress, spend and the written activity.js."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from deploy_vii.contracts import PATHWAY_MODULES, PathwayId
from deploy_vii.registry import plan
from deploy_workflow.inbox.drops import Layout
from deploy_workflow.inbox.runs import Record
from deploy_workflow.model.budget import BudgetError, exact_sum, read_reservation_snapshot
from deploy_workflow.model.pricing import money_text
from deploy_workflow.owners.cpos_launch import NOT_ANALYTICAL
from deploy_workflow.run_events import EVENTS, read_events

log = logging.getLogger(__name__)

STALLED_AFTER = 3600  # seconds without a new event
KEPT_ENDED = 200
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


def _events(run_dir: Path, run_id: str) -> list[dict[str, Any]]:
    try:
        return read_events(run_dir / EVENTS)
    except (OSError, ValueError) as error:
        # Documented fail-open (display only): an unreadable log shows every module as waiting.
        log.warning("run %s: event log unreadable (%s); modules shown as waiting", run_id, error)
        return []


def _age_seconds(
    record: Record, events: Sequence[Mapping[str, Any]], now: datetime
) -> float | None:
    last = str(events[-1].get("at", "")) if events else ""
    text = last or record.started_at
    try:
        then = datetime.fromisoformat(text)
    except ValueError:
        log.warning("run %s: time %r cannot be parsed; stall check skipped", record.id, text)
        return None
    if then.tzinfo is None:
        then = then.replace(tzinfo=UTC)
    return (now.astimezone(UTC) - then).total_seconds()


def _entry(layout: Layout, record: Record, now: datetime) -> dict[str, Any]:
    entry: dict[str, Any] = asdict(record)
    entry["files"] = list(record.files)
    run_dir = layout.runs / record.id
    events: list[dict[str, Any]] = []
    if record.status != "rejected" and run_dir.is_dir():
        events = _events(run_dir, record.id)
        entry["modules"] = module_states(record.pathway, events)
        amount = spent(run_dir)
        entry["spent"] = None if amount is None else money_text(amount)
    if record.status == "running":
        age = _age_seconds(record, events, now)
        if age is not None and age > STALLED_AFTER:
            entry["stalled"] = True
    return entry


def snapshot(
    layout: Layout,
    records: Sequence[Record],
    *,
    cap: Decimal,
    now: datetime,
    held: str = "",
) -> dict[str, Any]:
    live = [r for r in records if r.status in _ORDER]
    live.sort(key=lambda r: (_ORDER[r.status], r.id))
    ended = [r for r in records if r.status not in _ORDER]
    ended.sort(key=lambda r: (r.ended_at or r.claimed_at, r.id), reverse=True)
    return {
        "updated": now.astimezone(UTC).strftime(_TIME),
        "cap": str(cap),
        "held": held,
        "runs": [_entry(layout, r, now) for r in [*live, *ended[:KEPT_ENDED]]],
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
        os.replace(name, target)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise
