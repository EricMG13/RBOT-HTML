"""Run records, launcher process control and outcomes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from decimal import Decimal
from pathlib import Path

import pytest

from deploy_workflow.inbox.drops import Layout, ensure_layout
from deploy_workflow.inbox.runs import (
    Record,
    alive,
    child_environment,
    command,
    load_all,
    outcome,
    prepare,
    save,
    start,
)
from deploy_workflow.run_events import append_event

FAKE = [sys.executable, str(Path(__file__).parent / "fixtures" / "fake_launcher.py")]
RULING = Path(__file__).resolve().parents[1] / "docs" / "rulings" / "2026-11-09-inbox-automation.md"
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


def test_start_runs_the_plan_and_logs(layout, fake_env, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-the-test")
    fake_env(
        {
            "events": [["module_started", {"module": "CP-0"}], ["delivered", {}]],
            "report": True,
            "exit": 0,
        }
    )
    process = start(layout, RECORD, CTX, launcher=FAKE, config="sol-medium", cap=CAP, ruling=RULING)
    assert process.wait(timeout=60) == 0
    assert outcome(layout, RECORD, 0) == ("finished", "")
    assert (layout.runs / "id1" / "deliveries" / "d1" / "report.html").is_file()
    assert (layout.logs / "id1.log").is_file()


def _live(layout, **kw):
    return start(layout, RECORD, CTX, launcher=FAKE, config="sol-medium", cap=CAP, **kw)


def test_child_environment_adds_the_source_folder_and_utf8_and_keeps_the_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-the-test")
    monkeypatch.setenv("PYTHONPATH", "/elsewhere")
    env = child_environment()
    src = str(Path(__file__).resolve().parents[1] / "src")
    assert env["PYTHONPATH"] == os.pathsep.join([src, "/elsewhere"])
    assert env["PYTHONUTF8"] == "1" and env["OPENAI_API_KEY"] == "fake-key-for-the-test"
    monkeypatch.delenv("PYTHONPATH")
    assert child_environment()["PYTHONPATH"] == src


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups")
def test_start_puts_the_run_in_its_own_session(layout, fake_env, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-the-test")
    fake_env({"sleep": 5})
    process = _live(layout, ruling=RULING)
    try:
        assert os.getpgid(process.pid) != os.getpgid(os.getpid())
    finally:
        process.kill()
        process.wait()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX zombies")
def test_an_exited_unwaited_child_is_not_alive():
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    deadline = time.time() + 20
    while time.time() < deadline and subprocess.run(
        ["ps", "-o", "stat=", "-p", str(child.pid)], capture_output=True, text=True, check=False
    ).stdout.strip().startswith(("S", "R")):
        time.sleep(0.05)
    assert alive(child.pid) is False


def test_alive_answers_false_for_a_pid_the_platform_refuses():
    assert alive(2**31) is False and alive(2**63) is False


def test_prepare_survives_output_that_is_not_valid_text(layout, tmp_path):
    script = tmp_path / "launcher.py"
    script.write_text(
        "import sys\nsys.stdout.buffer.write(b'\\xff\\xfe ok\\n')\n"
        "sys.stderr.buffer.write(b'--sources: \\xff refused\\n')\nsys.exit(2)\n",
        encoding="utf-8",
    )
    text = prepare(
        layout, RECORD, CTX, launcher=[sys.executable, str(script)], config="sol-medium", cap=CAP
    )
    assert "refused" in text and (layout.logs / "id1.log").is_file()


def test_prepare_gives_up_on_a_launcher_that_hangs(layout):
    hang = [sys.executable, "-c", "import time; time.sleep(30)"]
    text = prepare(layout, RECORD, CTX, launcher=hang, config="sol-medium", cap=CAP, timeout=0.5)
    assert text == "the offline check did not finish in 0.5 s"


def test_save_refuses_an_id_that_is_not_a_plain_file_name(layout):
    for bad in ("../escaped", "a/b", ".hidden", ""):
        with pytest.raises(ValueError, match="run ID"):
            save(layout, Record(bad, "c", "f", "queued", "t"))
    assert not (layout.engine / "escaped.json").exists()


def test_racing_saves_neither_fail_nor_leave_temporary_files(layout):
    errors: list[BaseException] = []

    def hammer() -> None:
        for _ in range(100):
            try:
                save(layout, RECORD)
            except OSError as error:
                errors.append(error)

    threads = [threading.Thread(target=hammer) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == [] and load_all(layout) == [RECORD]
    assert [p.name for p in layout.state.iterdir()] == ["id1.json"]


def test_load_all_skips_dot_files_and_refuses_an_unknown_status(layout):
    save(layout, RECORD)
    (layout.state / "._id1.json").write_bytes(b"\x00\x05Mac OS X")
    assert [r.id for r in load_all(layout)] == ["id1"]
    (layout.state / "odd.json").write_text(
        json.dumps(
            {"id": "odd", "pathway": "c", "folder": "f", "status": "paused", "claimed_at": "t"}
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"odd\.json"):
        load_all(layout)


def test_outcome_ignores_log_lines_that_are_not_events(layout):
    (layout.runs / "id1").mkdir()
    (layout.runs / "id1" / "events.jsonl").write_text(
        '1\nnull\n"delivered"\n{"event": "delivered"}\n', encoding="utf-8"
    )
    assert outcome(layout, RECORD, 1) == ("finished", "")


def test_a_missing_event_log_is_not_warned_about(layout, caplog):
    assert outcome(layout, RECORD, 3) == ("failed", "launcher exited 3; see logs/id1.log")
    assert "unreadable" not in caplog.text


def _fake_live(tmp_path, ruling, key):
    env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    env |= {"PYTHONPATH": child_environment()["PYTHONPATH"], "FAKE_PLAN": "{}"}
    if key:
        env["OPENAI_API_KEY"] = "fake-key-for-the-test"
    argv = [*FAKE, "--context", "c.json", "--sources", str(tmp_path), "--config", "sol-medium"]
    argv += ["--cap", "20", "--out", str(tmp_path / "out"), "--no-library", "--live"]
    if ruling is not None:
        argv += ["--ruling", str(ruling)]
    return subprocess.run(argv, env=env, capture_output=True, text=True, check=False)


def test_fake_launcher_refuses_what_the_real_one_refuses(tmp_path):
    no_ruling = _fake_live(tmp_path, None, key=True)
    assert no_ruling.returncode == 2 and "--ruling" in no_ruling.stderr
    bad_ruling = _fake_live(tmp_path, tmp_path / "r.md", key=True)
    assert bad_ruling.returncode == 2 and "ruling" in bad_ruling.stderr
    no_key = _fake_live(tmp_path, RULING, key=False)
    assert no_key.returncode == 2 and "OPENAI_API_KEY" in no_key.stderr
    assert _fake_live(tmp_path, RULING, key=True).returncode == 0


def test_fake_launcher_refuses_an_unknown_config_through_argparse(tmp_path):
    argv = [*FAKE, "--config", "nope", "--context", "c", "--sources", str(tmp_path)]
    argv += ["--cap", "1", "--out", str(tmp_path / "out"), "--no-library"]
    env = {**os.environ, "PYTHONPATH": child_environment()["PYTHONPATH"]}
    done = subprocess.run(argv, env=env, capture_output=True, text=True, check=False)
    assert done.returncode == 2 and "invalid choice" in done.stderr


def test_prepared_defaults_to_false_and_an_old_record_without_it_loads(layout):
    assert RECORD.prepared is False
    old = {"id": "old1", "pathway": "credit_snapshot", "folder": "f", "status": "queued"}
    old["claimed_at"] = "t"
    (layout.state / "old1.json").write_text(json.dumps(old), encoding="utf-8")
    save(layout, Record("new1", "credit_snapshot", "f", "queued", "t", prepared=True))
    loaded = {r.id: r.prepared for r in load_all(layout)}
    assert loaded == {"new1": True, "old1": False}


def test_m3_save_waits_out_a_refused_replace(layout, monkeypatch):
    real, refusals = os.replace, [2]

    def refuse_twice(source, target):
        if refusals[0]:
            refusals[0] -= 1
            raise PermissionError(13, "in use", str(target))
        real(source, target)

    monkeypatch.setattr(os, "replace", refuse_twice)
    save(layout, RECORD)
    assert refusals == [0]
    assert [r.id for r in load_all(layout)] == ["id1"]


def test_start_gives_the_child_a_pid_file_beside_the_record_and_load_all_ignores_it(
    layout, monkeypatch, tmp_path
):
    real_shape = str(Path(__file__).parent / "fixtures" / "real_shape_launcher.py")
    monkeypatch.setenv("REAL_SHAPE_HOLD", str(tmp_path / "never"))  # stays alive; killed below
    expected = layout.state / "id1.pid"
    process = start(
        layout, RECORD, CTX, launcher=[sys.executable, real_shape], config="sol-medium",
        cap=CAP, ruling=RULING,
    )  # fmt: skip
    try:
        deadline = time.monotonic() + 30
        while not expected.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert expected.read_text(encoding="utf-8") == str(process.pid)  # the child's own PID
        assert load_all(layout) == []  # a .pid file is not a record
    finally:
        process.kill()
        process.wait()


def test_the_pid_file_variable_is_in_the_child_environment_only_through_start(
    layout, fake_env, monkeypatch
):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-the-test")
    monkeypatch.delenv("DEPLOY_WORKFLOW_PID_FILE", raising=False)
    assert "DEPLOY_WORKFLOW_PID_FILE" not in child_environment()
    captured: dict[str, object] = {}
    real = subprocess.Popen

    def spy(*args, **kwargs):
        captured.update(kwargs["env"])
        return real(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", spy)
    fake_env({})
    start(layout, RECORD, CTX, launcher=FAKE, config="sol-medium", cap=CAP, ruling=RULING).wait()
    assert captured["DEPLOY_WORKFLOW_PID_FILE"] == str(layout.state / "id1.pid")
