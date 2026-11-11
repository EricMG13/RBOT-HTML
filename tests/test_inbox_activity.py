"""Activity data: module states, spend from the budget journal, the snapshot and activity.js."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from deploy_workflow.inbox.activity import module_states, snapshot, spent, write
from deploy_workflow.inbox.layout import Layout, ensure_layout
from deploy_workflow.inbox.runs import Record
from deploy_workflow.model.budget import Budget, OverrunStop
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


def test_cpdr_is_listed_from_the_start_in_every_pathway():
    """Owner, 2026-11-11: CP-DR and CP-2E are in every preset, so the view lists them before
    any event and before CP-1C."""
    for pathway in ("relative_value", "earnings_update", "credit_snapshot"):
        names = [name for name, _ in module_states(pathway, [])]
        assert "CP-DR" in names and "CP-2E" in names
    names = [name for name, _ in module_states("relative_value", [])]
    assert names.index("CP-DR") < names.index("CP-1C") and names[-1] == "Report"


def test_a_module_outside_the_preset_is_shown_once_it_starts():
    """An explicit --modules run can start a module the preset does not list (CP-2H in Relative
    Value); the events are how this view learns of it."""
    events = [{"event": "module_started", "module": "CP-2H"}]
    assert "CP-2H" not in dict(module_states("relative_value", []))
    states = module_states("relative_value", events)
    assert dict(states)["CP-2H"] == "running" and states[-1][0] == "Report"
    # A module name the plan does not know (a hand-edited event) is not shown and does not raise.
    assert "CP-XX" not in dict(
        module_states("relative_value", [{"event": "module_started", "module": "CP-XX"}])
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


def test_spend_of_an_unreadable_run_folder_is_unknown(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    run.chmod(0o000)
    try:
        assert spent(run) is None
    finally:
        run.chmod(0o755)


def test_spend_matches_the_budget_over_every_kind_of_call(tmp_path):
    live = tmp_path / "run" / "live"
    budget = Budget(Decimal(20), live)
    budget.reserve("a", Decimal("1.50"), config_id="sol-medium")
    budget.settle("a", Decimal("1.25"))  # settled 1.25
    budget.reserve("c", Decimal("2.00"), config_id="sol-medium")
    budget.release("c")  # released 0
    budget.reserve("d", Decimal("2.00"), config_id="sol-medium")
    budget.settle("d", None, retryable=True)  # unknown, full hold 2.00
    budget.reserve("e", Decimal("2.00"), retry_of="d", config_id="sol-medium")
    budget.settle("e", Decimal("1.10"))  # retry settled 1.10
    budget.reserve("f", Decimal("3.00"), config_id="sol-medium")  # open hold 3.00
    budget.reserve("b", Decimal("1.00"), config_id="sol-medium")
    with pytest.raises(OverrunStop):
        budget.settle("b", Decimal("1.75"))  # overrun 1.75
    # 1.25 + 1.75 + 0 + 2.00 + 1.10 + 3.00 = 9.10
    assert spent(tmp_path / "run") == Decimal("9.10")


def test_spend_keeps_digits_a_28_digit_context_would_round(tmp_path):
    budget = Budget(Decimal(20), tmp_path / "run" / "live")
    budget.reserve("a", Decimal(2), config_id="sol-medium")
    budget.settle("a", Decimal(1))
    budget.reserve("b", Decimal(1), config_id="sol-medium")
    budget.settle("b", Decimal("0.0000000000000000000000000001"))  # 1E-28
    assert spent(tmp_path / "run") == Decimal("1.0000000000000000000000000001")


def test_a_zero_charge_is_shown_without_an_exponent(layout):
    run = layout.runs / "z"
    budget = Budget(Decimal(20), run / "live")
    budget.reserve("a", Decimal(1), config_id="sol-medium")
    budget.settle("a", Decimal("0E-8"))
    record = Record("z", "credit_snapshot", "x", "running", "t", started_at="2026-11-09T11:59:00Z")
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    assert snapshot(layout, [record], cap=Decimal(20), now=now)["runs"][0]["spent"] == "0.00000000"


def test_write_does_not_follow_a_planted_temporary_name_and_leaves_no_temporary(layout):
    outside = layout.engine.parent / "outside.txt"
    outside.write_text("precious\n")
    (layout.engine / "activity.js.tmp").symlink_to(outside)
    write(layout, {"runs": []})
    assert outside.read_text() == "precious\n"
    assert (layout.engine / "activity.js").read_text().startswith("window.RUN_ACTIVITY=")


def test_write_removes_its_temporary_file_when_the_replace_fails(layout, monkeypatch):
    def refuse(*_a, **_k):
        raise OSError("no")

    monkeypatch.setattr(os, "replace", refuse)
    with pytest.raises(OSError):
        write(layout, {"runs": []})
    assert not list(layout.engine.glob("*.tmp"))


def test_stall_check_accepts_other_time_formats_and_a_naive_now(layout):
    record = Record(
        "t1", "credit_snapshot", "x", "running", "t", started_at="2026-11-09 09:00:00+00:00"
    )
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    assert snapshot(layout, [record], cap=Decimal(20), now=now)["runs"][0]["stalled"] is True
    naive = datetime(2026, 11, 9, 12, 0, 0)
    assert "runs" in snapshot(layout, [record], cap=Decimal(20), now=naive)


def test_an_unparsable_time_is_logged_not_silent(layout, caplog):
    record = Record("t2", "credit_snapshot", "x", "running", "t", started_at="yesterday")
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    entry = snapshot(layout, [record], cap=Decimal(20), now=now)["runs"][0]
    assert "stalled" not in entry and "yesterday" in caplog.text


def test_an_empty_start_time_and_no_events_is_not_stalled_and_logs_nothing(layout, caplog):
    record = Record("t3", "credit_snapshot", "x", "running", "t", started_at="")
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    entry = snapshot(layout, [record], cap=Decimal(20), now=now)["runs"][0]
    assert "stalled" not in entry and caplog.text == ""


def test_only_200_ended_records_are_kept_and_the_running_one_leads(layout):
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    records = [
        Record(f"e{i:03}", "credit_snapshot", "f", "finished", "t", ended_at="2026-11-09T08:00:00Z")
        for i in range(205)
    ]
    records.append(
        Record("r", "credit_snapshot", "f", "running", "t", started_at="2026-11-09T11:59:00Z")
    )
    runs = snapshot(layout, records, cap=Decimal(20), now=now)["runs"]
    assert len(runs) == 201 and runs[0]["id"] == "r"


def test_an_event_line_that_is_not_an_object_is_dropped_not_fatal(layout):
    record = Record("r1", "credit_snapshot", "f", "running", "t", started_at="2026-11-09T11:59:00Z")
    run_dir = layout.runs / "r1"
    run_dir.mkdir()
    (run_dir / "events.jsonl").write_text(
        '{"event": "module_started", "module": "CP-0"}\n[]\n"text"\n7\n', encoding="utf-8"
    )
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    [entry] = snapshot(layout, [record], cap=Decimal(20), now=now)["runs"]
    assert dict(entry["modules"])["CP-0"] == "running"


def test_l4_a_run_with_no_event_log_yet_is_waiting_and_logs_nothing(layout, caplog):
    record = Record("t4", "credit_snapshot", "x", "queued", "t")
    (layout.runs / "t4").mkdir()  # the offline step made the folder; no events yet
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    entry = snapshot(layout, [record], cap=Decimal(20), now=now)["runs"][0]
    assert {s for _, s in entry["modules"]} == {"waiting"}
    assert "event log unreadable" not in caplog.text


def test_m3_write_retries_a_refused_replace(layout, monkeypatch):
    real, refusals = os.replace, [2]

    def refuse_twice(source, target):
        if refusals[0]:
            refusals[0] -= 1
            raise PermissionError(13, "in use", str(target))
        real(source, target)

    monkeypatch.setattr(os, "replace", refuse_twice)
    write(layout, {"runs": []})
    assert refusals == [0]
    assert (layout.engine / "activity.js").read_text().startswith("window.RUN_ACTIVITY=")


# -- kept ended runs (S1): an ended run whose launcher is gone is read once --------------------


def _ended(layout, run_id="k1", status="finished", journal=True, **fields):
    run_dir = layout.runs / run_id
    append_event(run_dir, "module_started", module="CP-0")
    append_event(run_dir, "module_accepted", module="CP-0")
    if journal:  # a run that reached a provider call left a budget journal (USD 2 held)
        Budget(Decimal(20), run_dir / "live").reserve("e" * 32, Decimal(2), config_id="sol-medium")
    # A run reaped normally carries the process ID it was started with (and a start time).
    fields.setdefault("started_at", "2026-11-09T07:00:00Z")
    fields.setdefault("pid", 4242)
    return Record(
        run_id, "credit_snapshot", "f", status, "t", ended_at="2026-11-09T08:00:00Z", **fields
    )


@pytest.fixture
def reads(monkeypatch):
    """Counts of the readers that open an event log and a budget journal."""
    from deploy_workflow.inbox import activity

    counts = {"events": 0, "journal": 0}
    real_events, real_journal = activity.read_events, activity.read_reservation_snapshot

    def events(*args, **kwargs):
        counts["events"] += 1
        return real_events(*args, **kwargs)

    def journal(*args, **kwargs):
        counts["journal"] += 1
        return real_journal(*args, **kwargs)

    monkeypatch.setattr(activity, "read_events", events)
    monkeypatch.setattr(activity, "read_reservation_snapshot", journal)
    return counts


_NOW = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)


@pytest.mark.parametrize("status", ["finished", "failed", "capped"])
def test_s1_an_ended_run_is_read_once_and_shows_the_same_entry(layout, reads, status):
    record = _ended(layout, status=status)
    kept: dict = {}
    first = snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
    before = dict(reads)
    second = snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
    assert reads == before and before["events"] == 1
    assert second == first == snapshot(layout, [record], cap=Decimal(20), now=_NOW)


def test_s1_a_run_that_may_still_have_a_launcher_is_always_read_again(layout, reads):
    # interrupted may still spend (VERIFICATION.md, known and left open); running and queued too.
    kept: dict = {}
    for status in ("interrupted", "running", "queued"):
        record = _ended(layout, run_id=status, status=status, started_at="2026-11-09T11:59:00Z")
        snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
        before = reads["events"]
        snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
        assert reads["events"] == before + 1, status
    assert kept == {}


def test_s1_an_unreadable_journal_is_not_kept(layout, reads):
    record = _ended(layout, journal=False)
    (layout.runs / "k1" / "live").write_text("not a folder", encoding="utf-8")
    kept: dict = {}
    assert (
        snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)["runs"][0]["spent"] is None
    )
    snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
    assert reads["events"] == 2 and kept == {}


def test_s1_an_unreadable_event_log_is_not_kept(layout, reads):
    record = _ended(layout)
    (layout.runs / "k1" / "events.jsonl").write_text("{broken\n{}\n", encoding="utf-8")
    kept: dict = {}
    snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
    snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
    assert reads["events"] == 2 and kept == {}


def test_s1_a_changed_record_is_read_again(layout, reads):
    record = _ended(layout)
    kept: dict = {}
    snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
    append_event(layout.runs / "k1", "module_started", module="CP-1")
    assert (
        dict(
            snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)["runs"][0]["modules"]
        )["CP-1"]
        == "waiting"
    )  # same record: kept
    changed = replace(record, status="failed", reason="later")
    entry = snapshot(layout, [changed], cap=Decimal(20), now=_NOW, kept=kept)["runs"][0]
    assert entry["status"] == "failed" and dict(entry["modules"])["CP-1"] == "running"


def test_s1_nothing_is_kept_for_a_record_no_longer_shown(layout):
    records = [_ended(layout, run_id=f"e{i:03}") for i in range(3)]
    kept: dict = {}
    snapshot(layout, records, cap=Decimal(20), now=_NOW, kept=kept)
    assert set(kept) == {"e000", "e001", "e002"}
    snapshot(layout, records[:1], cap=Decimal(20), now=_NOW, kept=kept)
    assert set(kept) == {"e000"}


def test_s1_a_failed_run_started_but_with_no_saved_pid_is_read_again(layout, reads):
    # "failed: could not be started" after Popen leaves a live paid child and no saved pid.
    record = _ended(layout, status="failed", pid=0, reason="could not be started")
    kept: dict = {}
    snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
    append_event(layout.runs / "k1", "module_started", module="CP-1")
    entry = snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)["runs"][0]
    assert dict(entry["modules"])["CP-1"] == "running" and kept == {}
    never_started = replace(record, started_at="")  # refused before launch: nothing can change
    snapshot(layout, [never_started], cap=Decimal(20), now=_NOW, kept=kept)
    assert set(kept) == {"k1"}


def test_s1_a_settled_run_whose_folder_was_not_visible_is_read_again(layout):
    record = _ended(layout)
    hidden = layout.runs / "k1-away"
    kept: dict = {}
    (layout.runs / "k1").rename(hidden)  # the share dropped for one poll
    first = snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)["runs"][0]
    assert "modules" not in first and kept == {}
    hidden.rename(layout.runs / "k1")
    second = snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)["runs"][0]
    assert second["modules"] and Decimal(second["spent"]) == 2


@pytest.mark.parametrize("hidden", ["events.jsonl", "live"])
def test_s1_a_settled_run_first_read_without_its_log_or_journal_is_read_again(layout, hidden):
    # An absent event log or journal reads as "nothing yet"; for a settled run that is not a
    # fact to keep: the file may only have been out of sight for one poll.
    record = _ended(layout)
    path = layout.runs / "k1" / hidden
    away = path.with_name(hidden + ".away")
    kept: dict = {}
    path.rename(away)
    snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)
    assert kept == {}
    away.rename(path)
    entry = snapshot(layout, [record], cap=Decimal(20), now=_NOW, kept=kept)["runs"][0]
    assert dict(entry["modules"])["CP-0"] == "done" and Decimal(entry["spent"]) == 2
    assert set(kept) == {"k1"}


def test_an_event_whose_name_is_not_text_is_not_fatal():
    events = [{"event": ["x"]}, {"event": {"a": 1}}, {"event": "delivered"}]
    assert dict(module_states("earnings_update", events))["Report"] == "done"


def test_a_pathway_the_plan_does_not_know_shows_only_the_report_entry():
    assert module_states("no-such-pathway", []) == [["Report", "waiting"]]


def test_a_line_or_marker_nested_too_deep_to_parse_is_unreadable_not_fatal(layout):
    record = _ended(layout, status="running")
    deep = "[" * 100_000 + "]" * 100_000
    (layout.runs / "k1" / "events.jsonl").write_text(deep + "\n{}\n", encoding="utf-8")
    marker = next((layout.runs / "k1" / "live").rglob("e" * 32 + "*"))
    marker.write_text(deep, encoding="utf-8")
    [entry] = snapshot(layout, [record], cap=Decimal(20), now=_NOW)["runs"]
    assert {state for _, state in entry["modules"]} == {"waiting"} and entry["spent"] is None


def test_the_submitters_name_is_published_in_the_runs_entry(layout):
    record = Record("1", "credit_snapshot", "acme", "queued", "t", submitted_by="Dana Reyes")
    now = datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC)
    [entry] = snapshot(layout, [record], cap=Decimal(20), now=now)["runs"]
    assert entry["submitted_by"] == "Dana Reyes"
