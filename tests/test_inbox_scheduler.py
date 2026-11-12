"""The scheduler: launch, limit, restart, file and publish, for runs taken in through ``submit``.

Tests start real child processes (tests/fixtures/fake_launcher.py), which call no provider and
spend nothing. Every wait has a limit, and the ``root`` fixture kills any run still alive.
"""

from __future__ import annotations

import gc
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import library_fixtures
import pytest
from inbox_fixtures import (
    CONTEXT,
    DELIVERED,
    HERE,
    REPO,
    STAMP,
    activity_js,
    go,
    layout,
    pump,
    settings,
    status,
    submit_run,
)

from deploy_workflow.inbox import activity
from deploy_workflow.inbox import scheduler as scheduler_module
from deploy_workflow.inbox import startup as startup_module
from deploy_workflow.inbox.layout import Layout, ensure_layout
from deploy_workflow.inbox.runs import Record, alive, load_all
from deploy_workflow.inbox.scheduler import Scheduler, Settings, StartupRefused
from deploy_workflow.inbox.startup import STANDING_RULING
from deploy_workflow.model.adapter import KEY_VARIABLES
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.owners import cpos_launch
from deploy_workflow.owners.cpos_launch import update_library_at
from deploy_workflow.run_start import submissions

pytest_plugins = ["inbox_fixtures"]


def test_a_delivery_without_a_report_page_finishes_and_files_nothing(root, fake_env, listed):
    """The delivery has no report.html: the library shows the run itself, so no copy is filed."""
    fake_env({"events": DELIVERED})
    listed("*")
    w = Scheduler(settings(root))
    submit_run(w, root)
    pump(w, lambda: status(root) == ["finished"])
    [record] = load_all(layout(root))
    assert record.report == "" and not list((root / "issuers").rglob("*.html"))
    assert [p.name for p in (root / "_engine/runs" / record.id / "deliveries/d1").iterdir()] == [
        "delivery.json"
    ]


def test_a_run_with_two_deliveries_fails_rather_than_choosing(root, fake_env, listed):
    fake_env({"events": DELIVERED, "sleep": 1})
    listed("*")
    w = Scheduler(settings(root))
    submit_run(w, root)
    go(w)
    other = root / "_engine/runs" / _only(root).id / "deliveries/d2"
    other.mkdir(parents=True)
    (other / "delivery.json").write_text('{"files": {}}', encoding="utf-8")
    pump(w, lambda: status(root) != ["running"], limit=10)
    record = _only(root)
    assert record.status == "failed"
    assert record.reason == "expected one deliveries/*/delivery.json, found 2"


def test_an_earlier_format_delivery_is_filed_exactly_once(root, fake_env, listed):
    fake_env({"events": DELIVERED, "report_page": True})
    listed("*")
    w = Scheduler(settings(root))
    submit_run(w, root)
    pump(w, lambda: status(root) == ["finished"])
    assert [p.name for p in (root / "issuers/Acme Corp (acme)").iterdir()] == [
        "2026-11-09 credit_snapshot.html"
    ]
    for _ in range(5):
        w.step()
    assert len(load_all(layout(root))) == 1
    [record] = load_all(layout(root))
    assert record.report == "issuers/Acme Corp (acme)/2026-11-09 credit_snapshot.html"
    assert STAMP.fullmatch(record.claimed_at) and STAMP.fullmatch(record.started_at)
    assert STAMP.fullmatch(record.ended_at)
    assert (record.issuer_id, record.as_of) == ("acme", "2026-11-09")


def test_a_submission_is_run_by_the_real_launcher_and_listed(root, tmp_path, monkeypatch):
    """Sweep 2026-11-10 (wiring): the other scheduler tests stand in a launcher. Here the real one
    runs CP-OS and delivery on canned answers, and the real library rebuild lists the run."""
    from test_cpos_launch import context_file, issuer_folder

    from deploy_workflow.run_start import submissions

    monkeypatch.setattr(cpos_launch, "update_library_at", update_library_at)
    canned = str(HERE / "fixtures/canned_provider_launcher.py")
    w = Scheduler(settings(root, launcher=(sys.executable, canned)))
    lay = layout(root)
    sid = submissions.new(lay)
    source = issuer_folder(tmp_path)
    for path in sorted(source.rglob("*")):
        if path.is_file():
            target = submissions.files_folder(lay, sid) / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, target)
    answers = submissions.validated(
        {
            "context": json.loads(context_file(tmp_path, "credit_snapshot").read_text()),
            "modules": [],
            "max_turns": 32,
            "level": "basic",
            "model": "gpt",
            "effort": "balanced",
            "submitted_by": "analyst",
        }
    )
    got = submissions.summary(lay, sid, answers, cap=w.settings.cap)
    assert got["error"] == "", got["error"]
    w.submit(sid, answers, str(got["digest"]))
    pump(w, lambda: status(root) not in ([], ["queued"], ["running"]), limit=120)
    [record] = load_all(layout(root))
    assert record.status == "finished", record.reason
    assert record.report == ""  # the delivery has no report page, so nothing is filed
    assert not list((root / "_engine/runs" / record.id / "deliveries").glob("*/report.html"))
    assert f'"{record.id}"' in (root / "_engine/library/data.js").read_text(encoding="utf-8")


def test_the_fourth_run_waits_for_a_slot(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 2})
    w = Scheduler(settings(root))
    for i in range(4):
        submit_run(w, root, f"i{i}")
    go(w)
    assert sorted(status(root)) == ["queued", "running", "running", "running"]


def test_the_daily_limit_holds_the_next_run_until_tomorrow(root, fake_env):
    day = [datetime(2026, 11, 9, 23, 0).astimezone()]
    w = Scheduler(settings(root, max_per_day=1), now=lambda: day[0])
    fake_env({"events": DELIVERED})
    submit_run(w, root, "a")
    pump(w, lambda: "finished" in status(root))
    submit_run(w, root, "b")
    go(w)
    assert "queued" in status(root) and "daily limit" in activity_js(root)
    day[0] = datetime(2026, 11, 10, 0, 1).astimezone()
    w.step()
    assert "queued" not in status(root)


def test_the_held_text_names_the_configured_limit(root, fake_env):
    fake_env({"events": DELIVERED})
    w = Scheduler(settings(root, max_per_day=1))
    submit_run(w, root, "a")
    pump(w, lambda: "finished" in status(root))
    submit_run(w, root, "b")
    go(w)
    assert "daily limit of 1 runs reached; waiting until tomorrow" in activity_js(root)


def test_a_restart_adopts_a_live_run_and_starts_no_duplicate(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 3})
    first = Scheduler(settings(root))
    submit_run(first, root)
    go(first)  # the run is now a live child of a scheduler we drop
    del first  # a crash: the lock goes with the object
    gc.collect()
    second = Scheduler(settings(root))
    second.step()
    deadline = time.monotonic() + 5  # the child creates its run folder a moment after it starts
    while not list((root / "_engine/runs").iterdir()) and time.monotonic() < deadline:
        time.sleep(0.05)
    second.step()
    assert status(root) == ["running"] and len(list((root / "_engine/runs").iterdir())) == 1
    pump(second, lambda: status(root) != ["running"], limit=8)
    assert status(root) in (["finished"], ["interrupted"])  # adopted: decided from the events


def test_the_same_issuer_submitted_twice_gives_two_runs(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 1})
    w = Scheduler(settings(root))
    submit_run(w, root, payload=b"Net sales were 100.")
    submit_run(w, root, payload=b"Net sales were 200.")
    go(w)
    assert len(load_all(layout(root))) == 2 and len(list((root / "_engine/drops").iterdir())) == 2


def test_a_finished_run_the_library_does_not_list_is_not_filed(root, fake_env, listed):
    fake_env({"events": DELIVERED})
    listed(None, reason="no completion record")
    w = Scheduler(settings(root))
    submit_run(w, root)
    pump(w, lambda: status(root) == ["failed"])
    assert not (root / "issuers").exists() or not any((root / "issuers").iterdir())
    assert "not listed: no completion record" in load_all(layout(root))[0].reason


def test_a_failed_activity_write_is_logged_and_the_scheduler_goes_on(root, fake_env, monkeypatch):
    def full(*_):
        raise OSError("disk full")

    with monkeypatch.context() as patch:
        patch.setattr(activity, "write", full)
        w = Scheduler(settings(root))
        w.step()  # this write fails; step must not raise
    w.step()  # the real write is back
    assert "disk full" in (root / "_engine/logs/watcher.log").read_text()
    assert (root / "_engine/activity.js").is_file()


def test_start_up_refuses_without_the_provider_key(root, monkeypatch):
    monkeypatch.delenv(KEY_VARIABLES[CONFIGS["sol-medium"].provider], raising=False)
    with pytest.raises(StartupRefused, match="is not set in the launching environment"):
        Scheduler(settings(root))


def test_longest_engine_path_fits_under_an_80_character_root(monkeypatch):
    monkeypatch.undo()  # the real rebuild, not the stand-in
    monkeypatch.setattr(
        "deploy_workflow.library_index.current_method", lambda: library_fixtures.method()
    )
    with tempfile.TemporaryDirectory(prefix="ib", dir="/tmp") as short:
        base = Path(short).resolve()
        root = base / ("r" * (80 - len(str(base)) - 1))
        lay = ensure_layout(root)
        library_fixtures.make_run(lay.engine, "20261109-134102-01")
        assert update_library_at(lay.engine) is not None
        assert max(len(str(p)) for p in root.rglob("*")) < 260


# --- controller rulings R1-R11 -------------------------------------------------------------


def test_r1_a_run_this_scheduler_started_ends_by_poll_not_by_alive(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED})
    asked: list[int] = []

    def watch(pid: int) -> bool:
        asked.append(pid)
        return alive(pid)

    monkeypatch.setattr(scheduler_module.runs, "alive", watch)
    w = Scheduler(settings(root))
    submit_run(w, root)
    pump(w, lambda: status(root) == ["finished"])
    assert asked == []


def test_r2_a_second_scheduler_on_a_held_lock_is_refused_with_the_holders_text(root):
    first = Scheduler(settings(root))
    try:
        text = (root / "_engine/watcher.lock").read_text(encoding="utf-8")
        assert text == f"{socket.gethostname()} {os.getpid()}"
        with pytest.raises(
            StartupRefused, match=r"another run page service .* is running on this folder \("
        ):
            Scheduler(settings(root))
        assert (root / "_engine/watcher.lock").read_text(encoding="utf-8") == text
    finally:
        first.close()


def test_r2_the_lock_dies_with_the_scheduler_and_close_releases_it(root):
    Scheduler(settings(root)).close()  # a clean stop
    again = Scheduler(settings(root))
    del again  # a crash: the operating system drops the lock with the process's handle
    gc.collect()
    last = Scheduler(settings(root))
    last.close()
    last.close()  # closing twice is harmless


def test_f1_two_schedulers_started_together_one_refuses(root):
    gate = threading.Barrier(2)
    results: list[str] = []
    kept: list[Scheduler] = []

    def start() -> None:
        gate.wait()
        try:
            kept.append(Scheduler(settings(root)))
            results.append("ran")
        except StartupRefused:
            results.append("refused")

    threads = [threading.Thread(target=start) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    for scheduler in kept:
        scheduler.close()
    assert sorted(results) == ["ran", "refused"]


def test_r6_a_failed_rebuild_changes_nothing_and_is_retried(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED, "report_page": True})
    good = cpos_launch.update_library_at

    def broken(_workspace: Path) -> None:
        raise OSError("library locked")

    w = Scheduler(settings(root))
    submit_run(w, root)
    monkeypatch.setattr(cpos_launch, "update_library_at", broken)
    pump(w, lambda: "library locked" in _log(root))
    assert status(root) == ["running"] and not any((root / "issuers").iterdir())
    monkeypatch.setattr(cpos_launch, "update_library_at", good)
    pump(w, lambda: status(root) == ["finished"])
    assert len(list((root / "issuers").iterdir())) == 1


@pytest.mark.parametrize("error", [RuntimeError("surprise"), TypeError("surprise")])
def test_an_unexpected_rebuild_error_does_not_stop_the_scheduler(
    root, fake_env, monkeypatch, error
):
    fake_env({"report": True, "report_page": True, "events": DELIVERED})
    good = cpos_launch.update_library_at

    def broken(_workspace: Path) -> None:
        raise error

    monkeypatch.setattr(cpos_launch, "update_library_at", broken)
    w = Scheduler(settings(root))  # constructs although the first rebuild raises
    try:
        submit_run(w, root)
        pump(w, lambda: bool(w._children))  # launched
        [child] = w._children.values()
        child.wait(timeout=10)  # the run has really ended before the unfiled assertions
        assert "surprise" in _log(root)
        for _ in range(3):
            w.step()  # returns; the run ended but stays unfiled
        assert "the library could not be rebuilt (surprise); ended runs wait for it" in (
            activity_js(root)
        )
        assert status(root) == ["running"]
        assert not list((root / "issuers").rglob("*.html"))
        monkeypatch.setattr(cpos_launch, "update_library_at", good)
        pump(w, lambda: status(root) == ["finished"])
        assert len(list((root / "issuers").rglob("*.html"))) == 1
    finally:
        w.close()


def test_a_keyboard_interrupt_from_the_rebuild_still_stops_the_scheduler(root, monkeypatch):
    def interrupted(_workspace: Path) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cpos_launch, "update_library_at", interrupted)
    with pytest.raises(KeyboardInterrupt):
        Scheduler(settings(root))


def test_a_ruling_other_than_the_standing_one_is_refused_at_start_up(root, tmp_path, monkeypatch):
    # The cause: another ruling under docs/rulings that names the config passes check_ruling.
    monkeypatch.setenv(KEY_VARIABLES[CONFIGS["sol-high"].provider], "test-key-not-real")
    sol_high = REPO / "docs/rulings/2026-11-09-tdg-sol-high-test.md"
    with pytest.raises(StartupRefused, match="2026-11-11-run-start-submit"):
        Scheduler(settings(root, ruling=sol_high))
    other = tmp_path / "2026-11-09-tdg-sol-high-test.md"
    other.write_text("sol-medium", encoding="utf-8")
    with pytest.raises(StartupRefused, match="2026-11-11-run-start-submit"):
        Scheduler(settings(root, ruling=other))
    Scheduler(settings(root)).close()


def test_every_launch_is_under_the_standing_ruling_even_if_a_symlink_is_repointed(
    root, monkeypatch
):
    launched: list[Path] = []

    def record_start(*_args: Any, ruling: Path, **_kwargs: Any) -> subprocess.Popen[bytes]:
        launched.append(Path(ruling))
        return subprocess.Popen([sys.executable, "-c", "pass"])

    monkeypatch.setattr(scheduler_module.runs, "start", record_start)
    link = root / "ruling.md"
    link.symlink_to(STANDING_RULING)
    w = Scheduler(settings(root, ruling=link))
    try:
        link.unlink()
        link.symlink_to(REPO / "docs/rulings/2026-11-05-launcher-live-test.md")
        submit_run(w, root)
        pump(w, lambda: bool(launched))
    finally:
        w.close()
    assert launched == [STANDING_RULING]


def _ruling_without(tmp_path: Path, config: str, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A copy of the standing ruling that does not name ``config``, made the standing one."""
    rulings = tmp_path / "rulings"
    rulings.mkdir()
    lines = STANDING_RULING.read_text(encoding="utf-8").splitlines()
    kept = [
        " ".join(t for t in line.split() if t != config) if line.startswith("configs:") else line
        for line in lines
    ]
    copy = rulings / STANDING_RULING.name
    copy.write_text("\n".join(kept) + "\n", encoding="utf-8")
    monkeypatch.setattr("deploy_workflow.model.adapter.LIVE_RULINGS_ROOT", rulings)
    monkeypatch.setattr(startup_module, "STANDING_RULING", copy)
    return copy


@pytest.mark.parametrize("missing", ["sol-medium", "sol-high", "opus-medium", "opus-high"])
def test_start_up_is_refused_when_the_ruling_lacks_one_of_the_four_configs(
    root, tmp_path, monkeypatch, missing
):
    copy = _ruling_without(tmp_path, missing, monkeypatch)
    with pytest.raises(StartupRefused, match=f"does not list '{missing}'"):
        Scheduler(settings(root, ruling=copy))


def test_start_up_needs_the_openai_key_but_not_the_anthropic_key(root, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    Scheduler(settings(root)).close()
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(StartupRefused, match="OPENAI_API_KEY is not set"):
        Scheduler(settings(root))


def _submit_advanced(w: Scheduler, root: Path, model: str, effort: str) -> Record:
    body = json.loads(json.dumps(CONTEXT))
    body["run"]["as_of"] = "2026-11-09"
    answers = submissions.validated(
        {
            "context": body,
            "modules": [],
            "max_turns": 32,
            "level": "advanced",
            "model": model,
            "effort": effort,
            "submitted_by": "analyst",
        }
    )
    lay = Layout(root)
    sid = submissions.new(lay)
    (submissions.files_folder(lay, sid) / "a.txt").write_bytes(b"Net sales were 100.")
    got = submissions.summary(lay, sid, answers, cap=w.settings.cap)
    assert got["error"] == "", got["error"]
    return w.submit(sid, answers, str(got["digest"]))


@pytest.mark.parametrize(
    ("model", "effort", "fragment"),
    [
        ("gpt", "fast", ["--config", "sol-medium", "--cap"]),
        ("gpt", "balanced", ["--config", "sol-medium", "--balanced", "--cap"]),
        ("gpt", "high", ["--config", "sol-high", "--cap"]),
        ("claude", "fast", ["--config", "opus-medium", "--cap"]),
        ("claude", "balanced", ["--config", "opus-medium", "--balanced", "--cap"]),
        ("claude", "high", ["--config", "opus-high", "--cap"]),
    ],
)
def test_a_submitted_model_and_effort_are_stored_and_launched(
    root, monkeypatch, model, effort, fragment
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    argvs: list[list[str]] = []
    real_command = scheduler_module.runs.command

    def recording(*args: Any, **kwargs: Any) -> list[str]:
        argv = real_command(*args, **kwargs)
        argvs.append(argv)
        return argv

    monkeypatch.setattr(scheduler_module.runs, "command", recording)
    monkeypatch.setattr(
        scheduler_module.runs,
        "start",
        lambda *_a, **_k: subprocess.Popen([sys.executable, "-c", "pass"]),
    )
    w = Scheduler(settings(root))
    try:
        record = _submit_advanced(w, root, model, effort)
        assert (record.model, record.effort) == (model, effort)
        assert (load_all(layout(root))[0].model, load_all(layout(root))[0].effort) == (
            model,
            effort,
        )
        pump(w, lambda: bool(argvs))
    finally:
        w.close()
    at = argvs[0].index("--config")
    assert argvs[0][at : at + len(fragment)] == fragment


def test_a_default_submission_stores_gpt_balanced(root):
    w = Scheduler(settings(root))
    try:
        record = submit_run(w, root)
    finally:
        w.close()
    assert (record.model, record.effort) == ("gpt", "balanced")


def test_submit_refuses_claude_without_the_anthropic_key(root, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    w = Scheduler(settings(root))
    try:
        body = json.loads(json.dumps(CONTEXT))
        body["run"]["as_of"] = "2026-11-09"
        answers = submissions.validated(
            {
                "context": body, "modules": [], "max_turns": 32, "level": "advanced",
                "model": "claude", "effort": "high", "submitted_by": "analyst",
            }
        )  # fmt: skip
        lay = Layout(root)
        sid = submissions.new(lay)
        (submissions.files_folder(lay, sid) / "a.txt").write_bytes(b"Net sales were 100.")
        got = submissions.summary(lay, sid, answers, cap=w.settings.cap)
        monkeypatch.delenv("ANTHROPIC_API_KEY")
        with pytest.raises(submissions.Refused, match="Claude Opus is not available"):
            w.submit(sid, answers, str(got["digest"]))
        assert load_all(layout(root)) == []
    finally:
        w.close()


def _log(root: Path) -> str:
    log = root / "_engine/logs/watcher.log"
    return log.read_text(encoding="utf-8") if log.is_file() else ""


def test_an_unreadable_run_record_stops_start_up_naming_the_file(root):
    ensure_layout(root)
    (root / "_engine/state/bad.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="bad.json"):
        Scheduler(settings(root))


def test_start_up_writes_the_library_page_once_and_no_inbox(root):
    Scheduler(settings(root)).close()
    page = root / "library.html"
    assert 'http-equiv="refresh" content="0; url=_engine/library/index.html"' in page.read_text()
    assert not (root / "inbox").exists()
    page.write_text("mine", encoding="utf-8")
    Scheduler(settings(root)).close()
    assert page.read_text() == "mine"


# --- fix round 1: a record is written before every step that can be interrupted -------------


def _runs() -> Any:
    return scheduler_module.runs


def _once(monkeypatch: pytest.MonkeyPatch, name: str, fault: BaseException, when=None) -> list[Any]:
    """Make runs.<name> raise ``fault`` on the first call where ``when(*args)`` holds."""
    real = getattr(_runs(), name)
    hits: list[Any] = []

    def patched(*args: Any, **kwargs: Any) -> Any:
        if not hits and (when is None or when(*args)):
            hits.append(args)
            raise fault
        return real(*args, **kwargs)

    monkeypatch.setattr(_runs(), name, patched)
    return hits


def _track_starts(monkeypatch: pytest.MonkeyPatch) -> list[subprocess.Popen[bytes]]:
    started: list[subprocess.Popen[bytes]] = []
    real = _runs().start

    def start(*args: Any, **kwargs: Any) -> subprocess.Popen[bytes]:
        started.append(real(*args, **kwargs))
        return started[-1]

    monkeypatch.setattr(_runs(), "start", start)
    return started


def _wait_all(children: list[subprocess.Popen[bytes]]) -> None:
    for child in children:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=10)


def _only(root: Path):
    [record] = load_all(layout(root))
    return record


def test_m1_an_interrupt_before_the_start_save_starts_nothing_and_resumes_once(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED})
    started = _track_starts(monkeypatch)
    _once(monkeypatch, "save", KeyboardInterrupt(), lambda lay, r: r.status == "running")
    w = Scheduler(settings(root))
    submit_run(w, root)
    with pytest.raises(KeyboardInterrupt):
        go(w)
    w.close()
    assert started == [] and (_only(root).status, _only(root).prepared) == ("queued", True)
    pump(Scheduler(settings(root)), lambda: status(root) == ["finished"])
    assert len(started) == 1


def test_m1_an_interrupt_after_start_leaves_one_process_at_most_and_no_second_start(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED, "sleep": 20})
    started = _track_starts(monkeypatch)
    _once(monkeypatch, "save", KeyboardInterrupt(), lambda lay, r: r.status == "running" and r.pid)
    w = Scheduler(settings(root))
    try:
        submit_run(w, root)
        with pytest.raises(KeyboardInterrupt):
            go(w)
        w.close()
        assert len(started) == 1 and started[0].poll() is not None  # the child was stopped
        record = _only(root)
        assert (record.status, record.pid) == ("running", 0) and record.started_at
        # No PID file exists (the fake launcher never writes one): past the 60 s grace the
        # run is cut short. Inside the grace it stays running (see test_c_...).
        second = Scheduler(settings(root), now=lambda: datetime.now(UTC) + timedelta(seconds=61))
        for _ in range(3):
            second.step()
        assert len(started) == 1
        record = _only(root)
        assert record.status == "interrupted"
        assert record.reason == (
            "the service stopped while starting this run; its process may still be running"
            " \N{EM DASH} check before submitting it again"
        )
    finally:
        _wait_all(started)


def test_d6_a_running_record_without_a_pid_is_decided_before_the_first_scan(root):
    ensure_layout(root)
    save_record = scheduler_module.runs.save
    save_record(
        Layout(root),
        Record("20261109-000001-01", "credit_snapshot", "acme", "running", "t", started_at="t"),
    )
    Scheduler(settings(root)).close()
    assert _only(root).status == "interrupted"
    assert "may still be running" in _only(root).reason


def test_a_start_that_raises_oserror_fails_the_run_and_counts_toward_the_day(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED})

    def refuse(*_a: Any, **_k: Any) -> Any:
        raise OSError("cannot create the log")

    monkeypatch.setattr(_runs(), "start", refuse)
    w = Scheduler(settings(root, max_per_day=1))
    submit_run(w, root)
    for _ in range(4):
        w.step()
    record = _only(root)
    assert (
        record.status == "failed" and record.reason == "could not be started: cannot create the log"
    )
    assert record.started_at and record.ended_at
    assert w._started_today() == 1


def test_a_pid_save_that_fails_with_oserror_stops_the_child_and_never_restarts_the_run(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED, "sleep": 1})
    started = _track_starts(monkeypatch)
    hits = _once(
        monkeypatch,
        "save",
        OSError("state folder is full"),
        lambda lay, r: r.status == "running" and r.pid,
    )
    w = Scheduler(settings(root, max_per_day=1))
    try:
        submit_run(w, root)
        pump(w, lambda: status(root) not in (["running"], ["queued"]), limit=10)
        for _ in range(3):
            w.step()
        assert hits and len(started) == 1  # stopped when its record could not be completed
        assert status(root) in (["failed"], ["interrupted"])
    finally:
        _wait_all(started)


def test_runs_that_cannot_be_recorded_still_count_toward_the_daily_limit(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED, "sleep": 20})
    started = _track_starts(monkeypatch)
    real = _runs().save

    def save(lay: Layout, record: Any) -> None:
        if record.status == "running" and record.pid:
            raise OSError("state folder is full")
        real(lay, record)

    monkeypatch.setattr(_runs(), "save", save)
    w = Scheduler(settings(root, max_per_day=1))
    try:
        submit_run(w, root)
        for _ in range(6):
            w.step()
        assert len(started) == 1
    finally:
        _wait_all(started)


def test_l7_a_new_id_never_reuses_a_record_a_run_files_folder_a_run_folder_or_a_log(root):
    w = Scheduler(settings(root), now=lambda: datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC))
    prefix = "20261109-120000"
    (root / f"_engine/drops/{prefix}-01").mkdir()
    (root / f"_engine/runs/{prefix}-02").mkdir()
    (root / f"_engine/logs/{prefix}-03.log").write_text("x", encoding="utf-8")
    w._put(Record(f"{prefix}-04", "credit_snapshot", "f", "queued", "t"))
    assert w._new_id() == f"{prefix}-05"
    w.close()


def test_f2_a_report_is_filed_once_even_when_the_finished_record_cannot_be_saved(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED, "report_page": True})
    real = _runs().save
    failures = [3]

    def save(lay: Layout, record: Any) -> None:
        if record.status == "finished" and failures[0] > 0:
            failures[0] -= 1
            raise OSError("state folder briefly unwritable")
        real(lay, record)

    monkeypatch.setattr(_runs(), "save", save)
    w = Scheduler(settings(root))
    submit_run(w, root)
    pump(w, lambda: status(root) == ["finished"], limit=10)
    assert [p.name for p in (root / "issuers/Acme Corp (acme)").iterdir()] == [
        "2026-11-09 credit_snapshot.html"
    ]
    assert _only(root).report == "issuers/Acme Corp (acme)/2026-11-09 credit_snapshot.html"


def test_f3_a_corrupt_issuer_registry_fails_the_run_instead_of_stopping_the_scheduler(
    root, fake_env
):
    fake_env({"events": DELIVERED, "sleep": 1, "report_page": True})
    w = Scheduler(settings(root))
    submit_run(w, root)
    go(w)
    (root / "_engine/state/issuers.json").write_text("{", encoding="utf-8")
    pump(w, lambda: status(root) != ["running"], limit=10)
    record = _only(root)
    assert record.status == "failed" and record.reason.startswith("could not be filed: ")
    assert not (root / "issuers").exists() or not any((root / "issuers").iterdir())


def test_f5_the_page_says_why_ended_runs_wait_when_the_library_cannot_be_rebuilt(
    root, fake_env, listed, monkeypatch
):
    fake_env({"events": DELIVERED})
    started = _track_starts(monkeypatch)

    def broken(_workspace: Path) -> None:
        raise ValueError("library is a link")

    monkeypatch.setattr(cpos_launch, "update_library_at", broken)
    w = Scheduler(settings(root, max_running=1))
    try:
        submit_run(w, root, "a")
        go(w)
        started[0].wait(timeout=10)
        for _ in range(3):
            w.step()
        assert "the library could not be rebuilt (library is a link); ended runs wait for it" in (
            activity_js(root)
        )
        monkeypatch.setattr(
            cpos_launch,
            "update_library_at",
            lambda ws: SimpleNamespace(
                runs=[{"id": p.name} for p in (ws / "runs").iterdir()], excluded=[]
            ),
        )
        pump(w, lambda: status(root) == ["finished"])
        w.step()
        assert "could not be rebuilt" not in activity_js(root)
    finally:
        _wait_all(started)


def test_f5_both_notices_are_joined_with_a_semicolon(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED, "sleep": 20})
    started = _track_starts(monkeypatch)
    w = Scheduler(settings(root, max_per_day=1))
    try:
        submit_run(w, root, "a")
        pump(w, lambda: status(root) == ["running"])
        started[0].kill()
        started[0].wait()

        def broken(_workspace: Path) -> None:
            raise OSError("locked")

        monkeypatch.setattr(cpos_launch, "update_library_at", broken)
        submit_run(w, root, "b")
        for _ in range(3):
            w.step()
        text = activity_js(root)
        assert (
            "the library could not be rebuilt (locked); ended runs wait for it; daily limit" in text
        )
    finally:
        _wait_all(started)


# -- fix round 2 ---------------------------------------------------------------------------------


def _windows_locking(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run startup's Windows branch here: an ``msvcrt`` stand-in with Windows' rules.

    ``locking`` locks ``n`` bytes from the descriptor's current position, a second lock on a byte
    another descriptor holds fails with ``PermissionError``, and unlocking bytes that descriptor
    does not hold fails too."""
    held: dict[tuple[int, int], int] = {}

    def locking(fd: int, mode: int, nbytes: int) -> None:
        assert nbytes == 1
        key = (os.fstat(fd).st_ino, os.lseek(fd, 0, os.SEEK_CUR))
        if mode == 0:  # LK_UNLCK
            if held.get(key) != fd:
                raise PermissionError(13, "unlock of a byte this handle did not lock")
            del held[key]
        elif key in held:
            raise PermissionError(13, "the byte is locked by another handle")
        else:
            held[key] = fd

    fake = SimpleNamespace(locking=locking, LK_NBLCK=2, LK_UNLCK=0)
    monkeypatch.setitem(sys.modules, "msvcrt", fake)
    monkeypatch.setattr(scheduler_module.startup, "sys", SimpleNamespace(platform="win32"))


def test_m1_on_windows_the_lock_is_the_same_byte_whatever_text_the_file_holds(root, monkeypatch):
    _windows_locking(monkeypatch)
    (root / "_engine").mkdir()
    (root / "_engine/watcher.lock").write_text("old-host 12345678901234567890", encoding="utf-8")
    first = Scheduler(settings(root))
    try:
        with pytest.raises(
            StartupRefused, match="another run page service .* is running on this folder"
        ):
            Scheduler(settings(root))
    finally:
        first.close()  # unlocks the byte it locked: raises nothing
    Scheduler(settings(root)).close()
    text = (root / "_engine/watcher.lock").read_text(encoding="utf-8")
    assert text == f"{socket.gethostname()} {os.getpid()}"


def test_l4_a_rebuild_error_is_logged_once_until_it_changes_and_the_recovery_once(
    root, monkeypatch
):
    problem = ["share unavailable"]

    def broken(_workspace: Path) -> None:
        raise OSError(5, problem[0])

    monkeypatch.setattr(cpos_launch, "update_library_at", broken)
    w = Scheduler(settings(root))
    try:
        for _ in range(20):
            w.step()
        assert _log(root).count("library rebuild failed") == 1
        problem[0] = "share unplugged"
        for _ in range(20):
            w.step()
        assert _log(root).count("library rebuild failed") == 2
        monkeypatch.setattr(
            cpos_launch, "update_library_at", lambda ws: SimpleNamespace(runs=[], excluded=[])
        )
        for _ in range(3):
            w.step()
        assert _log(root).count("library rebuild works again") == 1
        assert "could not be rebuilt" not in activity_js(root)
    finally:
        w.close()


def test_l6_a_run_stopped_because_its_record_cannot_be_saved_says_so(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED, "sleep": 1})
    started = _track_starts(monkeypatch)
    _once(
        monkeypatch,
        "save",
        OSError("state folder is full"),
        lambda lay, r: r.status == "running" and r.pid,
    )
    w = Scheduler(settings(root))
    try:
        submit_run(w, root)
        go(w)
        pump(w, lambda: status(root) not in (["running"], ["queued"]), limit=10)
        record = _only(root)
        assert record.status == "failed"
        assert record.reason == (
            "stopped by the scheduler: its record could not be saved (state folder is full)"
        )
    finally:
        _wait_all(started)
        w.close()


def test_m3_one_refused_replace_of_the_pid_save_does_not_stop_the_run(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED, "sleep": 1})
    real, seen = os.replace, []

    def replace(source, target, *args, **kwargs):
        target = Path(target)
        if target.parent.name == "state" and target.name != "issuers.json":
            seen.append(target.name)
            if len(seen) in (3, 4):  # saves: queued, running, then the PID save, refused twice
                raise PermissionError(13, "in use by another process", str(target))
        return real(source, target, *args, **kwargs)

    w = Scheduler(settings(root))
    monkeypatch.setattr(os, "replace", replace)
    submit_run(w, root)
    pump(w, lambda: status(root) == ["finished"], limit=15)
    w.close()
    assert len(seen) >= 4  # the refusals were reached
    assert _only(root).reason == ""


def test_m2_the_fail_opens_of_runs_and_activity_reach_the_scheduler_log(root):
    layout_ = ensure_layout(root)
    gone = subprocess.Popen([sys.executable, "-c", "pass"])
    gone.wait()
    run_id = "20261109-100000-01"
    (layout_.runs / run_id).mkdir()
    (layout_.drops / run_id).mkdir()
    (layout_.runs / run_id / "events.jsonl").mkdir()  # reading it as a file fails
    (layout_.runs / run_id / "live").write_text("not a folder")
    from deploy_workflow.inbox.runs import save

    save(
        layout_,
        Record(
            run_id,
            "credit_snapshot",
            "acme",
            "running",
            "2026-11-09T10:00:00Z",
            started_at="2026-11-09T10:00:00Z",
            pid=gone.pid,
            prepared=True,
        ),
    )
    w = Scheduler(settings(root, max_per_day=0))
    w.step()
    w.step()
    w.close()
    log = (root / "_engine/logs/watcher.log").read_text(encoding="utf-8")
    assert "event log unreadable" in log
    assert "budget journal" in log
    package = logging.getLogger("deploy_workflow.inbox")
    assert not [h for h in package.handlers if getattr(h, "root", None) == layout_.root]


def test_i1_the_default_launcher_command_forces_utf8():
    assert Settings(Path(".")).launcher == (
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "deploy_workflow.owners.cpos_launch",
    )


def test_l9_a_run_is_filed_and_listed_through_the_real_library_rebuild(root, monkeypatch):
    # Opts out of the autouse ``listed`` stand-in: the real rebuild decides what is listed.
    monkeypatch.setattr(cpos_launch, "update_library_at", update_library_at)
    # The fixture run carries the fixture's method text, so the listing compares with that.
    monkeypatch.setattr(
        "deploy_workflow.library_index.current_method", lambda: library_fixtures.method()
    )
    w = Scheduler(
        settings(root, launcher=(sys.executable, str(HERE / "fixtures/real_shape_launcher.py")))
    )
    try:
        submit_run(w, root)
        pump(w, lambda: status(root) == ["finished"], limit=30)
    finally:
        w.close()
    record = _only(root)
    assert record.reason == "" and record.report.startswith("issuers/Acme Corp (acme)/")
    filed = root / record.report
    assert (
        filed.read_bytes()
        == next(
            (root / "_engine/runs" / record.id / "deliveries").glob("*/report.html")
        ).read_bytes()
    )
    library = update_library_at(root / "_engine")
    assert record.id in [run["id"] for run in library.runs]
    assert f'"report": "{record.report}"' in activity_js(root)


def test_a_cap_above_the_standing_rulings_usd_20_is_refused_at_start_up(root):
    refusal = r"cap 500 .*above USD 20.*2026-11-11-run-start-submit"
    with pytest.raises(StartupRefused, match=refusal):
        Scheduler(settings(root, cap=Decimal(500)))
    with pytest.raises(StartupRefused, match="above USD 20"):
        Scheduler(settings(root, cap=Decimal("20.01")))
    Scheduler(settings(root, cap=Decimal(20))).close()
    with pytest.raises(StartupRefused, match="above USD 20"):
        Scheduler(settings(root, cap=Decimal("NaN")))


# -- a run started just before a hard kill: its own PID file --------------------------------

REAL_SHAPE = str(HERE / "fixtures" / "real_shape_launcher.py")
PID_RUN = "20261109-000001-01"
T0 = datetime(2026, 11, 10, 12, 0, 0, tzinfo=UTC)


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _save_running(root: Path, started_at: str, run_id: str = PID_RUN) -> Path:
    """A record as left by a service killed after it started the child, before the PID save."""
    lay = ensure_layout(root)
    scheduler_module.runs.save(
        lay,
        Record(
            run_id, "credit_snapshot", "acme", "running", "t",
            issuer_id="acme", issuer_name="Acme Corp", as_of="2026-11-09",
            started_at=started_at, prepared=True,
        ),
    )  # fmt: skip
    return lay.state / f"{run_id}.pid"


class _Clock:
    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


def test_a_a_run_whose_pid_was_never_saved_is_adopted_from_its_own_pid_file(root, tmp_path):
    pid_file = _save_running(root, _stamp(datetime.now(UTC)))
    hold = tmp_path / "release"
    context = tmp_path / "context.json"
    context.write_text(json.dumps(CONTEXT), encoding="utf-8")
    env = {**os.environ, "DEPLOY_WORKFLOW_PID_FILE": str(pid_file), "REAL_SHAPE_HOLD": str(hold)}
    env["PYTHONPATH"] = os.pathsep.join(
        [str(HERE.parent / "src"), *filter(None, [env.get("PYTHONPATH")])]
    )
    child = subprocess.Popen(
        [
            sys.executable, REAL_SHAPE, "--context", str(context), "--config", "sol-medium",
            "--cap", "20", "--out", str(root / "_engine/runs" / PID_RUN), "--live",
            "--ruling", "r", "--no-library",
        ],
        env=env,
    )  # fmt: skip
    w = None
    try:
        deadline = time.monotonic() + 30
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        w = Scheduler(settings(root, max_running=1))
        w.step()
        submit_run(w, root, "other")
        go(w)
        by_id = {r.id: r for r in load_all(layout(root))}
        assert by_id[PID_RUN].status == "running" and by_id[PID_RUN].pid == child.pid
        assert [r.status for i, r in sorted(by_id.items()) if i != PID_RUN] == ["queued"]
        hold.write_text("go", encoding="utf-8")
        pump(w, lambda: {r.id: r.status for r in load_all(layout(root))}[PID_RUN] == "finished", 30)
        record = {r.id: r for r in load_all(layout(root))}[PID_RUN]
        assert record.report.startswith("issuers/Acme Corp (acme)/")
        assert [f.name for f in (root / "issuers").rglob("*.html")] == [
            "2026-11-09 credit_snapshot.html"
        ]  # exactly one report filed
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=10)
        if w is not None:
            _wait_all(list(w._children.values()))
            w.close()


def test_b_a_run_with_no_pid_file_after_the_grace_is_interrupted_and_nothing_starts(
    root, monkeypatch
):
    started = _track_starts(monkeypatch)
    _save_running(root, _stamp(T0 - timedelta(seconds=61)))
    w = Scheduler(settings(root), now=_Clock(T0))
    try:
        w.step()
    finally:
        w.close()
    record = _only(root)
    assert record.status == "interrupted" and "may still be running" in record.reason
    assert started == []  # no process was started


def test_c_a_run_with_no_pid_file_inside_the_grace_stays_running_then_is_interrupted(root):
    _save_running(root, _stamp(T0 - timedelta(seconds=10)))
    clock = _Clock(T0)
    w = Scheduler(settings(root), now=clock)
    try:
        w.step()
        assert _only(root).status == "running"
        clock.moment = T0 + timedelta(seconds=51)  # 61 s after the start
        w.step()
    finally:
        w.close()
    assert _only(root).status == "interrupted"


@pytest.mark.parametrize("text", ["abc", "0", "-5", "", b"\xff\xfe", "1" * 5000])
def test_d_a_pid_file_that_is_not_a_positive_integer_is_no_pid_file_and_logged_once(root, text):
    pid_file = _save_running(root, _stamp(T0 - timedelta(seconds=10)))
    if isinstance(text, bytes):
        pid_file.write_bytes(text)
    else:
        pid_file.write_text(text, encoding="utf-8")
    clock = _Clock(T0)
    w = Scheduler(settings(root), now=clock)
    try:
        w.step()
        w.step()
        assert _only(root).status == "running" and _only(root).pid == 0
        clock.moment = T0 + timedelta(seconds=51)
        w.step()
    finally:
        w.close()
    assert _only(root).status == "interrupted"
    assert _log(root).count(f"run {PID_RUN}: PID file") == 1
    assert not pid_file.exists()


def test_e_the_pid_file_is_gone_once_the_run_has_ended(root):
    w = Scheduler(settings(root, launcher=(sys.executable, REAL_SHAPE)))
    try:
        submit_run(w, root)
        pump(w, lambda: status(root) == ["finished"], limit=30)
    finally:
        w.close()
    assert list((root / "_engine/state").glob("*.pid")) == []


# -- outstanding rows of the 2026-11-10 sweep ------------------------------------------------


def test_the_daily_limit_is_shown_while_every_slot_is_busy(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 20})
    w = Scheduler(settings(root, max_running=1, max_per_day=1))
    submit_run(w, root, "a")
    go(w)
    assert status(root) == ["running"]  # 1 of 1 started today, and the only slot is busy
    submit_run(w, root, "b")
    go(w)
    assert sorted(status(root)) == ["queued", "running"]
    assert "daily limit of 1 runs reached" in activity_js(root)


@pytest.mark.skipif(not hasattr(time, "tzset"), reason="needs a settable process time zone")
def test_a_start_earlier_the_same_local_day_counts_across_a_clock_change(root, monkeypatch):
    # New York, 1 Nov 2026: clocks went back at 02:00. A start at 00:30 EDT (04:30Z) and "now"
    # at 23:00 EST are the same local day, though 23:00's offset puts 04:30Z on 31 Oct.
    monkeypatch.setenv("TZ", "America/New_York")
    time.tzset()
    try:
        late = datetime(2026, 11, 2, 4, 0, tzinfo=UTC).astimezone()  # 23:00 EST on 1 Nov
        assert (late.hour, late.day) == (23, 1)
        scheduler_module.runs.save(
            ensure_layout(root),
            Record(
                "20261101-043000-01", "credit_snapshot", "first", "finished", "t",
                started_at="2026-11-01T04:30:00Z", ended_at="2026-11-01T05:00:00Z", prepared=True,
            ),
        )  # fmt: skip
        w = Scheduler(settings(root, max_per_day=1), now=lambda: late)
        submit_run(w, root, "b")
        go(w)
        w.step()
        assert sorted(status(root)) == ["finished", "queued"]
        assert "daily limit of 1 runs reached" in activity_js(root)
    finally:
        monkeypatch.undo()
        time.tzset()


def test_a_malformed_line_in_a_runs_files_does_not_stop_the_scheduler(root, fake_env):
    # A run folder is written by the launcher, but one bad line there must not end the process
    # that supervises every other run.
    fake_env({"events": DELIVERED, "sleep": 20})
    w = Scheduler(settings(root))
    submit_run(w, root)
    go(w)
    [record] = load_all(layout(root))
    log = root / "_engine/runs" / record.id / "events.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    for text in ('{"event": ["x"]}\n{"event": "y"}\n', "[" * 100_000 + "]" * 100_000 + "\n{}\n"):
        log.write_text(text, encoding="utf-8")
        w.step()
        assert f'"id": "{record.id}"' in activity_js(root)


# -- the folder watcher is gone ---------------------------------------------------------------


def test_the_layout_makes_no_inbox(root):
    ensure_layout(root)
    assert not (root / "inbox").exists()
    for name in ("issuers", "_engine/runs", "_engine/drops", "_engine/state", "_engine/logs"):
        assert (root / name).is_dir()
    assert (root / "_engine/uploads").is_dir()


def test_nothing_imports_the_removed_modules():
    removed = ("inbox." + "drops", "inbox." + "watcher")
    found = []
    for top in ("src", "apps"):
        for path in sorted((REPO / top).rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:  # a binary file is no import
                continue
            found += [f"{path.relative_to(REPO)}: {name}" for name in removed if name in text]
    assert found == []
    for name in ("drops", "watcher"):
        assert not (REPO / "src/deploy_workflow/inbox" / f"{name}.py").exists()


def test_an_existing_inbox_folder_is_never_read_or_changed(root, fake_env):
    fake_env({"events": DELIVERED})
    drop = root / "inbox/credit_snapshot/acme"
    drop.mkdir(parents=True)
    (drop / "context.json").write_text("{}", encoding="utf-8")
    (drop / "a.pdf").write_bytes(b"%PDF-1.4 not real")
    (root / "inbox/failed").mkdir()
    before = sorted(
        (p.relative_to(root), p.stat().st_mtime_ns) for p in (root / "inbox").rglob("*")
    )
    w = Scheduler(settings(root))
    try:
        submit_run(w, root)
        pump(w, lambda: status(root) == ["finished"])
    finally:
        w.close()
    after = sorted((p.relative_to(root), p.stat().st_mtime_ns) for p in (root / "inbox").rglob("*"))
    assert after == before
    assert len(load_all(layout(root))) == 1  # the folder in the old inbox started nothing


def test_records_the_folder_watcher_wrote_still_load_and_show(root):
    lay = ensure_layout(root)
    scheduler_module.runs.save(
        lay,
        Record(
            "20261109-100000-01", "credit_snapshot", "acme", "rejected", "2026-11-09T10:00:00Z",
            reason="no context file", ended_at="2026-11-09T10:00:00Z",
        ),
    )  # fmt: skip
    w = Scheduler(settings(root))
    try:
        w.step()
    finally:
        w.close()
    [record] = load_all(lay)
    assert (record.status, record.submission, record.reason) == ("rejected", "", "no context file")
    assert '"id": "20261109-100000-01"' in activity_js(root)
    assert "no context file" in activity_js(root)


def test_a_queued_record_the_folder_watcher_never_checked_is_failed_with_the_reason(root):
    lay = ensure_layout(root)
    waiting = Record(
        "20261109-100000-01", "credit_snapshot", "acme", "queued", "2026-11-09T10:00:00Z"
    )
    scheduler_module.runs.save(lay, waiting)
    w = Scheduler(settings(root))
    try:
        w.step()
    finally:
        w.close()
    record = _only(root)
    assert record.status == "failed" and record.ended_at
    assert record.reason == _OLD_WATCHER


_OLD_WATCHER = (
    "queued by the folder watcher before the run start page replaced it;"
    " submit it again from the run start page"
)


def test_an_old_prepared_record_with_no_submission_is_failed_and_never_started(root, monkeypatch):
    started = _track_starts(monkeypatch)
    lay = ensure_layout(root)
    run_id = "20261109-100000-01"
    (lay.drops / run_id).mkdir()
    (lay.drops / run_id / "context.json").write_text("{}", encoding="utf-8")
    scheduler_module.runs.save(
        lay, Record(run_id, "credit_snapshot", "acme", "queued", "t", prepared=True)
    )
    w = Scheduler(settings(root))
    try:
        w.step()
    finally:
        w.close()
    record = _only(root)
    assert started == []
    assert record.status == "failed" and record.reason == _OLD_WATCHER


def test_launch_refuses_a_record_with_no_submission_or_no_digest(root, monkeypatch):
    started = _track_starts(monkeypatch)
    lay = ensure_layout(root)
    w = Scheduler(settings(root))
    try:
        for run_id, extra in (
            ("20261109-100000-01", {"submission": "", "digest": "d"}),
            ("20261109-100000-02", {"submission": "s" * 32, "digest": ""}),
        ):
            (lay.drops / run_id).mkdir()
            (lay.drops / run_id / "context.json").write_text("{}", encoding="utf-8")
            record = Record(
                run_id, "credit_snapshot", "acme", "queued", "t", prepared=True, **extra
            )
            scheduler_module.runs.save(lay, record)
            assert w._launch(record) is False
    finally:
        w.close()
    assert started == []
    assert {r.status for r in load_all(lay)} == {"failed"}


def test_a_queued_run_with_no_context_json_in_its_folder_fails_and_starts_nothing(
    root, monkeypatch
):
    started = _track_starts(monkeypatch)
    lay = ensure_layout(root)
    run_id = "20261109-100000-01"
    (lay.drops / run_id).mkdir()
    (lay.drops / run_id / "a.pdf").write_bytes(b"%PDF-1.4 not real")
    (lay.drops / run_id / "ctx.json").write_text("{}", encoding="utf-8")  # any other name
    scheduler_module.runs.save(
        lay,
        Record(
            run_id,
            "credit_snapshot",
            "acme",
            "queued",
            "t",
            prepared=True,
            submission="s" * 32,
            digest="d",
        ),
    )
    w = Scheduler(settings(root))
    try:
        w.step()
        w.step()
    finally:
        w.close()
    record = _only(root)
    assert record.status == "failed" and record.started_at == ""
    assert (
        record.reason
        == f"no context.json in _engine/drops/{run_id}; submit it again from the run page"
    )
    assert started == []
