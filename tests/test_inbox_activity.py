"""Activity data: module states, spend from the budget journal, the snapshot and activity.js."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from deploy_workflow.inbox.activity import module_states, snapshot, spent, write
from deploy_workflow.inbox.drops import Layout, ensure_layout
from deploy_workflow.inbox.runs import Record
from deploy_workflow.model.budget import Budget
from deploy_workflow.run_events import append_event


@pytest.fixture
def layout() -> Iterator[Layout]:
    with tempfile.TemporaryDirectory(prefix="ib", dir="/tmp") as root:
        yield ensure_layout(Path(root))


def test_module_states_follow_the_events():
    events = [
        {"event": "module_started", "module": "CP-0"},
        {"event": "module_accepted", "module": "CP-0"},
        {"event": "module_started", "module": "CP-1"},
    ]
    states = dict(module_states("earnings_update", events))
    assert (
        states["CP-0"] == "done"
        and states["CP-1"] == "running"
        and states["CP-5"] == "waiting"
        and states["Report"] == "waiting"
    )


def test_report_entry_follows_delivery_events():
    running = dict(module_states("earnings_update", [{"event": "delivery_started"}]))
    done = dict(
        module_states("earnings_update", [{"event": "delivery_started"}, {"event": "delivered"}])
    )
    assert running["Report"] == "running" and done["Report"] == "done"


def test_spend_counts_settled_charges_and_full_unknown_holds(tmp_path):
    run_dir = tmp_path / "run" / "live"
    budget = Budget(Decimal(20), run_dir)
    for call_id, hold in (("a", "1.50"), ("b", "0.50"), ("c", "2.00")):
        budget.reserve(call_id, Decimal(hold), config_id="sol-medium")
    budget.settle("a", Decimal("1.25"))
    budget.settle("b", Decimal("0.40"))
    budget.settle("c", None)  # unknown charge: the full 2.00 hold stays counted
    assert spent(tmp_path / "run") == Decimal("3.65")


def test_spend_is_zero_before_any_call_and_unknown_when_unreadable(tmp_path):
    assert spent(tmp_path) == Decimal(0)
    (tmp_path / "live").write_text("not a folder")
    assert spent(tmp_path) is None


def test_snapshot_marks_a_silent_run_as_stalled(layout):
    record = Record(
        "id1", "credit_snapshot", "acme", "running", "t", started_at="2026-11-09T10:00:00Z"
    )
    late = snapshot(
        layout, [record], cap=Decimal(20), now=datetime(2026, 11, 9, 11, 0, 1, tzinfo=UTC)
    )
    soon = snapshot(
        layout, [record], cap=Decimal(20), now=datetime(2026, 11, 9, 10, 59, 0, tzinfo=UTC)
    )
    assert late["runs"][0]["stalled"] is True and "stalled" not in soon["runs"][0]


def test_snapshot_orders_runs_and_reads_each_run_folder(layout):
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    records = [
        Record("1", "credit_snapshot", "old", "finished", "t", ended_at="2026-11-09T08:00:00Z"),
        Record("2", "credit_snapshot", "new", "failed", "t", ended_at="2026-11-09T09:00:00Z"),
        Record("3", "credit_snapshot", "wait", "queued", "t"),
        Record("4", "credit_snapshot", "go", "running", "t", started_at="2026-11-09T11:59:00Z"),
        Record("5", "credit_snapshot", "bad", "rejected", "t", ended_at="2026-11-09T07:00:00Z"),
    ]
    (layout.runs / "4").mkdir()
    append_event(layout.runs / "4", "module_started", module="CP-0")
    data = snapshot(layout, records, cap=Decimal(20), now=now, held="paused")
    assert [r["id"] for r in data["runs"]] == ["4", "3", "2", "1", "5"]
    by_id = {r["id"]: r for r in data["runs"]}
    assert data["cap"] == "20" and data["held"] == "paused" and data["updated"].endswith("Z")
    assert dict(by_id["4"]["modules"])["CP-0"] == "running" and by_id["4"]["spent"] == "0"
    assert "modules" not in by_id["5"] and "modules" not in by_id["3"]


def test_unreadable_event_log_gives_waiting_and_unreadable_journal_gives_null_spend(layout):
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    record = Record("9", "credit_snapshot", "x", "running", "t", started_at="2026-11-09T11:59:00Z")
    run = layout.runs / "9"
    (run / "events.jsonl").mkdir(parents=True)  # reading it as a file fails
    (run / "live").write_text("not a folder")
    entry = snapshot(layout, [record], cap=Decimal(20), now=now)["runs"][0]
    assert entry["spent"] is None
    assert {s for _, s in entry["modules"]} == {"waiting"}


def test_written_script_cannot_close_its_element(layout):
    write(layout, {"runs": [{"folder": "</script><img src=x>"}]})
    text = (layout.engine / "activity.js").read_text(encoding="utf-8")
    assert text.startswith("window.RUN_ACTIVITY=") and "<" not in text
    assert not list(layout.engine.glob("*.tmp"))
