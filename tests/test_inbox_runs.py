"""Run records, launcher process control and outcomes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from decimal import Decimal
from pathlib import Path

import pytest

from deploy_workflow.inbox.drops import Layout, ensure_layout
from deploy_workflow.inbox.runs import (
    Record,
    alive,
    command,
    load_all,
    outcome,
    prepare,
    save,
    start,
)
from deploy_workflow.run_events import append_event

FAKE = [sys.executable, str(Path("tests/fixtures/fake_launcher.py").resolve())]
CTX = Path("c.json")
RECORD = Record("id1", "credit_snapshot", "acme", "queued", "t")
CAP = Decimal(20)


@pytest.fixture
def layout() -> Iterator[Layout]:
    with tempfile.TemporaryDirectory(prefix="ib", dir="/tmp") as root:
        yield ensure_layout(Path(root))


@pytest.fixture
def fake_env(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, object]], None]:
    def set_plan(plan: dict[str, object]) -> None:
        monkeypatch.setenv("FAKE_PLAN", json.dumps(plan))

    return set_plan


def test_records_round_trip_in_id_order(layout):
    save(layout, Record("20261109-000002-01", "credit_snapshot", "b", "queued", "t2"))
    save(
        layout,
        Record(
            "20261109-000001-01", "earnings_update", "a", "running", "t1", pid=7, files=("a.pdf",)
        ),
    )
    assert [r.id for r in load_all(layout)] == ["20261109-000001-01", "20261109-000002-01"]
    assert load_all(layout)[0].files == ("a.pdf",) and load_all(layout)[0].pid == 7


def test_load_all_skips_issuer_registry_and_temporary_files(layout):
    save(layout, RECORD)
    (layout.state / "issuers.json").write_text("{}", encoding="utf-8")
    (layout.state / "id9.json.tmp").write_text("{", encoding="utf-8")
    assert [r.id for r in load_all(layout)] == ["id1"]


def test_load_all_names_an_unreadable_record(layout):
    (layout.state / "bad.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.json"):
        load_all(layout)
    (layout.state / "bad.json").write_text(json.dumps({"id": "x", "future": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.json"):
        load_all(layout)


def test_command_for_prepare_and_live(layout):
    record = Record("id1", "credit_snapshot", "acme", "queued", "t")
    base = command(
        layout,
        record,
        Path("c.json"),
        launcher=["py", "-m", "x"],
        config="sol-medium",
        cap=Decimal(20),
        ruling=None,
    )
    assert base == [
        "py",
        "-m",
        "x",
        "--context",
        "c.json",
        "--sources",
        str(layout.drops / "id1"),
        "--config",
        "sol-medium",
        "--cap",
        "20",
        "--out",
        str(layout.runs / "id1"),
        "--no-library",
    ]
    live = command(
        layout,
        record,
        Path("c.json"),
        launcher=["py"],
        config="sol-medium",
        cap=Decimal(20),
        ruling=Path("r.md"),
    )
    assert live[-3:] == ["--live", "--ruling", "r.md"]


def test_alive_for_this_process_and_not_for_an_exited_one():
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    assert alive(os.getpid()) is True and alive(child.pid) is False and alive(0) is False
    assert alive(-5) is False


@pytest.mark.parametrize(
    ("events", "exit_code", "expected"),
    [
        ([("module_started", {"module": "CP-0"}), ("delivered", {})], 0, ("finished", "")),
        ([("stopped", {"reason": "budget"})], 1, ("capped", "stopped at the cap")),
        ([("stopped", {"reason": "checker"})], 1, ("failed", "stopped: checker")),
        ([], 2, ("failed", "launcher exited 2; see logs/id1.log")),
        (
            [("module_started", {"module": "CP-0"})],
            None,
            ("interrupted", "the run's process ended without a result"),
        ),
    ],
)
def test_outcome(layout, events, exit_code, expected):
    for name, fields in events:
        append_event(layout.runs / "id1", name, **fields)
    assert outcome(layout, RECORD, exit_code) == expected


def test_outcome_treats_an_unreadable_event_file_as_no_events(layout):
    (layout.runs / "id1").mkdir()
    (layout.runs / "id1" / "events.jsonl").write_text("{bad\n{bad\n", encoding="utf-8")
    assert outcome(layout, RECORD, 3) == ("failed", "launcher exited 3; see logs/id1.log")


def test_prepare_returns_the_refusal_text(layout, fake_env):
    fake_env({"prepare_exit": 2, "prepare_error": "--sources: cannot read a.pdf: bad"})
    assert (
        prepare(layout, RECORD, CTX, launcher=FAKE, config="sol-medium", cap=CAP)
        == "--sources: cannot read a.pdf: bad"
    )
    assert "cannot read a.pdf" in (layout.logs / "id1.log").read_text(encoding="utf-8")


def test_prepare_success_and_silent_failure(layout, fake_env):
    fake_env({})
    assert prepare(layout, RECORD, CTX, launcher=FAKE, config="sol-medium", cap=CAP) == ""
    fake_env({"prepare_exit": 2})
    assert (
        prepare(layout, RECORD, CTX, launcher=FAKE, config="sol-medium", cap=CAP)
        == "launcher exited 2"
    )


def test_start_runs_the_plan_and_logs(layout, fake_env):
    fake_env(
        {
            "events": [["module_started", {"module": "CP-0"}], ["delivered", {}]],
            "report": True,
            "exit": 0,
        }
    )
    process = start(
        layout, RECORD, CTX, launcher=FAKE, config="sol-medium", cap=CAP, ruling=Path("r.md")
    )
    assert process.wait(timeout=60) == 0
    assert outcome(layout, RECORD, 0) == ("finished", "")
    assert (layout.runs / "id1" / "deliveries" / "d1" / "report.html").is_file()
    assert (layout.logs / "id1.log").is_file()
