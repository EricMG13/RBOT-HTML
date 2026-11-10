"""The inbox watcher: claim, prepare, launch, limit, file and publish.

Tests start real child processes (tests/fixtures/fake_launcher.py), which call no provider and
spend nothing. Every wait has a limit, and the ``root`` fixture kills any run still alive.
"""

from __future__ import annotations

import gc
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import library_fixtures
import pytest

from deploy_workflow.inbox import activity
from deploy_workflow.inbox import watcher as watcher_module
from deploy_workflow.inbox.drops import Layout, ensure_layout
from deploy_workflow.inbox.runs import Record, alive, load_all
from deploy_workflow.inbox.watcher import Settings, StartupRefused, Watcher, main
from deploy_workflow.model.adapter import KEY_VARIABLES
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.owners import cpos_launch
from deploy_workflow.owners.cpos_launch import update_library_at

HERE = Path(__file__).resolve().parent
FAKE = str(HERE / "fixtures" / "fake_launcher.py")
CONTEXT = json.loads((HERE.parent / "cases/context/research-minimal.json").read_text("utf-8"))
DELIVERED = [["delivered", {}]]
KEY = KEY_VARIABLES[CONFIGS["sol-medium"].provider]
STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")


def _kill_leftovers(layout: Layout) -> None:
    for record in load_all(layout):
        if record.pid > 0:
            try:
                os.kill(record.pid, signal.SIGKILL)
                os.waitpid(record.pid, 0)
            except (ProcessLookupError, ChildProcessError):
                pass


@pytest.fixture
def root(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    # pytest's tmp_path is longer than the 80-character root limit on macOS.
    monkeypatch.setenv(KEY, "test-key-not-real")
    with tempfile.TemporaryDirectory(prefix="ib", dir="/tmp") as short:
        folder = Path(short).resolve()
        yield folder
        try:
            _kill_leftovers(Layout(folder))
        except ValueError:  # a test left an unreadable record on purpose
            pass


@pytest.fixture
def fake_env(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, Any]], None]:
    def set_plan(plan: dict[str, Any]) -> None:
        monkeypatch.setenv("FAKE_PLAN", json.dumps({"report": True, **plan}))

    return set_plan


@pytest.fixture(autouse=True)
def listed(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Replace the library rebuild: ``"*"`` lists every run folder, None excludes each."""

    def install(which: str | None = "*", reason: str = "") -> None:
        def build(workspace: Path) -> SimpleNamespace:
            names = sorted(p.name for p in (workspace / "runs").iterdir())
            runs = [{"id": n} for n in names] if which == "*" else []
            left = [] if which == "*" else [(n, reason) for n in names]
            return SimpleNamespace(runs=runs, excluded=left)

        monkeypatch.setattr(cpos_launch, "update_library_at", build)

    install("*")
    return install


def settings(root: Path, **changes: Any) -> Settings:
    changes = {"settle_seconds": 0, "launcher": (sys.executable, FAKE), **changes}
    return Settings(root, **changes)


def layout(root: Path) -> Layout:
    return Layout(root)


def make_drop(
    root: Path,
    pathway: str,
    name: str,
    *,
    issuer: str = "acme",
    context_pathway: str | None = None,
) -> Path:
    body = json.loads(json.dumps(CONTEXT))
    body["run"]["pathway"] = context_pathway or pathway
    body["run"]["as_of"] = "2026-11-09"
    body["identity"]["issuer_id"] = issuer
    body["identity"]["issuer_name"] = "Acme Corp"
    folder = root / "inbox" / pathway / name
    folder.mkdir(parents=True)
    (folder / "context.json").write_text(json.dumps(body), encoding="utf-8")
    (folder / "a.pdf").write_bytes(b"%PDF-1.4 not real")
    return folder


def status(root: Path) -> list[str]:
    return [r.status for r in load_all(layout(root))]


def activity_js(root: Path) -> str:
    return (root / "_engine/activity.js").read_text(encoding="utf-8")


def pump(w: Watcher, until: Callable[[], bool], limit: float = 5) -> None:
    deadline = time.monotonic() + limit
    while not until():
        assert time.monotonic() < deadline, "condition not met in time"
        w.step()
        time.sleep(0.05)


def go(w: Watcher) -> None:
    """Two polls: the first sees a drop, the second finds it unchanged for 0 s and settled."""
    w.step()
    w.step()


def test_a_drop_becomes_a_filed_report_exactly_once(root, fake_env, listed):
    fake_env({"events": DELIVERED})
    listed("*")
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    pump(w, lambda: status(root) == ["finished"])
    assert not (root / "inbox/credit_snapshot/acme").exists()
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
    assert (record.issuer_id, record.as_of, record.files) == ("acme", "2026-11-09", ("a.pdf",))


def test_a_drop_still_arriving_does_not_start(root, fake_env):
    now = [0.0]
    w = Watcher(settings(root, settle_seconds=120), clock=lambda: now[0])
    make_drop(root, "credit_snapshot", "acme")
    w.step()
    now[0] = 60
    w.step()
    assert load_all(layout(root)) == []


def test_rejected_drop_lands_in_failed_with_its_reason(root):
    make_drop(root, "earnings_update", "acme", context_pathway="credit_snapshot")
    w = Watcher(settings(root))
    go(w)
    [failed] = (root / "inbox/failed").iterdir()
    assert (
        "context names pathway credit_snapshot, dropped in earnings_update"
        in (failed / "WHY.txt").read_text()
    )
    assert status(root) == ["rejected"]


def test_a_drop_the_offline_check_refuses_is_rejected_with_its_text(root, fake_env):
    fake_env({"prepare_exit": 2, "prepare_error": "no readable source"})
    make_drop(root, "credit_snapshot", "acme")
    go(Watcher(settings(root)))
    [failed] = (root / "inbox/failed").iterdir()
    assert "no readable source" in (failed / "WHY.txt").read_text()
    assert status(root) == ["rejected"]


def test_the_fourth_drop_waits_for_a_slot(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 2})
    for i in range(4):
        make_drop(root, "credit_snapshot", f"d{i}", issuer=f"i{i}")
    w = Watcher(settings(root))
    go(w)
    assert sorted(status(root)) == ["queued", "running", "running", "running"]


def test_the_daily_limit_holds_the_next_run_until_tomorrow(root, fake_env):
    day = [datetime(2026, 11, 9, 23, 0).astimezone()]
    w = Watcher(settings(root, max_per_day=1), now=lambda: day[0])
    fake_env({"events": DELIVERED})
    make_drop(root, "credit_snapshot", "a", issuer="a")
    pump(w, lambda: "finished" in status(root))
    make_drop(root, "credit_snapshot", "b", issuer="b")
    go(w)
    assert "queued" in status(root) and "daily limit" in activity_js(root)
    day[0] = datetime(2026, 11, 10, 0, 1).astimezone()
    w.step()
    assert "queued" not in status(root)


def test_the_held_text_names_the_configured_limit(root, fake_env):
    fake_env({"events": DELIVERED})
    w = Watcher(settings(root, max_per_day=1))
    make_drop(root, "credit_snapshot", "a", issuer="a")
    pump(w, lambda: "finished" in status(root))
    make_drop(root, "credit_snapshot", "b", issuer="b")
    go(w)
    assert "daily limit of 1 runs reached; waiting until tomorrow" in activity_js(root)


def test_a_restart_adopts_a_live_run_and_starts_no_duplicate(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 3})
    make_drop(root, "credit_snapshot", "acme")
    go(Watcher(settings(root)))  # run is now a live child of a watcher we drop
    second = Watcher(settings(root))
    second.step()
    deadline = time.monotonic() + 5  # the child creates its run folder a moment after it starts
    while not list((root / "_engine/runs").iterdir()) and time.monotonic() < deadline:
        time.sleep(0.05)
    second.step()
    assert status(root) == ["running"] and len(list((root / "_engine/runs").iterdir())) == 1
    pump(second, lambda: status(root) != ["running"], limit=8)
    assert status(root) in (["finished"], ["interrupted"])  # adopted: decided from the events


def test_same_folder_name_twice_gives_two_runs(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 1})
    make_drop(root, "credit_snapshot", "acme")
    make_drop(root, "earnings_update", "acme", context_pathway="earnings_update")
    w = Watcher(settings(root))
    go(w)
    assert len(load_all(layout(root))) == 2 and len(list((root / "_engine/drops").iterdir())) == 2


def test_a_finished_run_the_library_does_not_list_is_not_filed(root, fake_env, listed):
    fake_env({"events": DELIVERED})
    listed(None, reason="no completion record")
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    pump(w, lambda: status(root) == ["failed"])
    assert not (root / "issuers").exists() or not any((root / "issuers").iterdir())
    assert "not listed: no completion record" in load_all(layout(root))[0].reason


def test_a_failed_activity_write_is_logged_and_the_watcher_goes_on(root, fake_env, monkeypatch):
    def full(*_):
        raise OSError("disk full")

    with monkeypatch.context() as patch:
        patch.setattr(activity, "write", full)
        w = Watcher(settings(root))
        w.step()  # this write fails; step must not raise
    w.step()  # the real write is back
    assert "disk full" in (root / "_engine/logs/watcher.log").read_text()
    assert (root / "_engine/activity.js").is_file()


def test_start_up_refuses_without_the_provider_key(root, monkeypatch):
    monkeypatch.delenv(KEY_VARIABLES[CONFIGS["sol-medium"].provider], raising=False)
    assert main(["--root", str(root)]) == 2


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


def test_r1_a_run_this_watcher_started_ends_by_poll_not_by_alive(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED})
    asked: list[int] = []

    def watch(pid: int) -> bool:
        asked.append(pid)
        return alive(pid)

    monkeypatch.setattr(watcher_module.runs, "alive", watch)
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    pump(w, lambda: status(root) == ["finished"])
    assert asked == []


def test_r2_a_second_watcher_on_a_held_lock_is_refused_with_the_holders_text(root):
    first = Watcher(settings(root))
    try:
        text = (root / "_engine/watcher.lock").read_text(encoding="utf-8")
        assert text == f"{socket.gethostname()} {os.getpid()}"
        with pytest.raises(StartupRefused, match=r"another watcher is running on this folder \("):
            Watcher(settings(root))
        assert main(["--root", str(root)]) == 2
        assert (root / "_engine/watcher.lock").read_text(encoding="utf-8") == text
    finally:
        first.close()


def test_r2_the_lock_dies_with_the_watcher_and_close_releases_it(root):
    Watcher(settings(root)).close()  # a clean stop
    again = Watcher(settings(root))
    del again  # a crash: the operating system drops the lock with the process's handle
    gc.collect()
    last = Watcher(settings(root))
    last.close()
    last.close()  # closing twice is harmless


def test_r2_run_forever_releases_the_lock_on_exit(root, monkeypatch):
    w = Watcher(settings(root))

    def interrupt(_seconds: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(watcher_module.time, "sleep", interrupt)
    w.run_forever()
    Watcher(settings(root)).close()


def test_f1_two_watchers_started_together_one_refuses(root):
    gate = threading.Barrier(2)
    results: list[str] = []
    kept: list[Watcher] = []

    def start() -> None:
        gate.wait()
        try:
            kept.append(Watcher(settings(root)))
            results.append("ran")
        except StartupRefused:
            results.append("refused")

    threads = [threading.Thread(target=start) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    for watcher in kept:
        watcher.close()
    assert sorted(results) == ["ran", "refused"]


def test_r4_a_drop_that_cannot_be_read_is_rejected_after_the_settle_time(root):
    now = [0.0]
    drop = make_drop(root, "credit_snapshot", "acme")
    (drop / "locked").mkdir()
    (drop / "locked").chmod(0)
    w = Watcher(settings(root, settle_seconds=120), clock=lambda: now[0])
    try:
        w.step()
        now[0] = 120
        w.step()
        assert load_all(layout(root)) == []  # not yet longer than the settle time
        now[0] = 121
        w.step()
        [record] = load_all(layout(root))
        assert record.status == "rejected" and record.reason.startswith("cannot be read: ")
        [failed] = (root / "inbox/failed").iterdir()
        assert "cannot be read" in (failed / "WHY.txt").read_text()
    finally:
        for locked in root.rglob("locked"):
            locked.chmod(0o755)


def test_r5_a_drop_taken_back_and_dropped_again_waits_the_full_time(root, fake_env):
    fake_env({"events": DELIVERED})
    now = [0.0]
    w = Watcher(settings(root, settle_seconds=120), clock=lambda: now[0])
    drop = make_drop(root, "credit_snapshot", "acme")
    w.step()
    now[0] = 100
    drop.rename(root / "taken-back")
    w.step()  # the scan lists nothing, so the tracker forgets it
    (root / "taken-back").rename(drop)
    w.step()
    now[0] = 130
    w.step()
    assert load_all(layout(root)) == []
    now[0] = 230
    w.step()
    assert len(load_all(layout(root))) == 1


def test_r6_a_failed_rebuild_changes_nothing_and_is_retried(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED})
    good = cpos_launch.update_library_at

    def broken(_workspace: Path) -> None:
        raise OSError("library locked")

    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    monkeypatch.setattr(cpos_launch, "update_library_at", broken)
    pump(w, lambda: "library locked" in _log(root))
    assert status(root) == ["running"] and not any((root / "issuers").iterdir())
    monkeypatch.setattr(cpos_launch, "update_library_at", good)
    pump(w, lambda: status(root) == ["finished"])
    assert len(list((root / "issuers").iterdir())) == 1


def _log(root: Path) -> str:
    log = root / "_engine/logs/watcher.log"
    return log.read_text(encoding="utf-8") if log.is_file() else ""


def test_r11_main_takes_every_setting_as_a_flag(monkeypatch):
    seen: list[Settings] = []

    class Stub:
        def __init__(self, given: Settings) -> None:
            seen.append(given)

        def run_forever(self) -> None:
            return None

    monkeypatch.setattr(watcher_module, "Watcher", Stub)
    argv = ["--root", "/tmp/x", "--config", "sol-high", "--cap", "7.5", "--max-running", "2"]
    argv += ["--max-per-day", "5", "--settle-seconds", "30", "--poll-seconds", "4"]
    argv += ["--ruling", "/tmp/r.md"]
    assert main(argv) == 0
    [got] = seen
    assert (got.config, str(got.cap), got.max_running, got.max_per_day) == ("sol-high", "7.5", 2, 5)
    assert (got.settle_seconds, got.poll_seconds, got.ruling) == (30, 4, Path("/tmp/r.md"))
    assert main(["--root", "/tmp/x", "--cap", "0"]) == 2


def test_an_unreadable_run_record_stops_start_up_naming_the_file(root, capsys):
    ensure_layout(root)
    (root / "_engine/state/bad.json").write_text("{not json", encoding="utf-8")
    assert main(["--root", str(root)]) == 2
    assert "bad.json" in capsys.readouterr().err


def test_start_up_writes_the_library_page_and_the_forms_once(root):
    Watcher(settings(root))
    page = root / "library.html"
    assert 'http-equiv="refresh" content="0; url=_engine/library/index.html"' in page.read_text()
    form = root / "inbox/credit_snapshot/_template/context-form.html"
    assert 'data-pathway="credit_snapshot"' in form.read_text(encoding="utf-8")
    page.write_text("mine", encoding="utf-8")
    Watcher(settings(root))
    assert page.read_text() == "mine"


# --- fix round 1: a record is written before every step that can be interrupted -------------


def _runs() -> Any:
    return watcher_module.runs


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


def test_a_claim_whose_record_cannot_be_saved_goes_back_where_it_was(root, monkeypatch):
    _once(monkeypatch, "save", OSError("state folder is full"))
    folder = make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    w.step()
    w._scan()  # the claim happens here; its record cannot be saved
    assert folder.is_dir() and not list((root / "_engine/drops").iterdir())
    assert load_all(layout(root)) == []


def test_the_claim_writes_its_record_before_anything_else_happens(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED})
    make_drop(root, "credit_snapshot", "acme")
    _once(monkeypatch, "prepare", KeyboardInterrupt())
    w = Watcher(settings(root))
    with pytest.raises(KeyboardInterrupt):
        go(w)
    record = _only(root)
    assert (record.status, record.prepared, record.folder) == ("queued", False, "acme")
    assert len(list((root / "_engine/drops").iterdir())) == 1
    w.close()


def test_m2_an_interrupt_during_prepare_is_resumed_by_the_next_start(root, fake_env, monkeypatch):
    fake_env({"events": DELIVERED})
    make_drop(root, "credit_snapshot", "acme")
    _once(monkeypatch, "prepare", KeyboardInterrupt())
    w = Watcher(settings(root))
    with pytest.raises(KeyboardInterrupt):
        go(w)
    w.close()
    second = Watcher(settings(root))
    pump(second, lambda: status(root) == ["finished"])
    assert len(list((root / "_engine/runs").iterdir())) == 1


def test_a_prepare_stage_fills_the_record_and_marks_it_prepared(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 3})
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root, max_running=0))
    go(w)
    record = _only(root)
    assert (record.status, record.prepared) == ("queued", True)
    assert (record.issuer_id, record.issuer_name, record.as_of, record.files) == (
        "acme",
        "Acme Corp",
        "2026-11-09",
        ("a.pdf",),
    )


def test_an_oserror_while_checking_rejects_the_drop_with_that_reason(root, monkeypatch):
    def broken(*_a: Any, **_k: Any) -> Any:
        raise OSError("disk went away")

    monkeypatch.setattr(watcher_module.drops, "check", broken)
    make_drop(root, "credit_snapshot", "acme")
    go(Watcher(settings(root)))
    record = _only(root)
    assert record.status == "rejected" and record.reason == "could not be checked: disk went away"
    [failed] = (root / "inbox/failed").iterdir()
    assert "could not be checked: disk went away" in (failed / "WHY.txt").read_text()


def test_m3_a_missing_failed_folder_is_recreated_and_the_drop_prepared_once(
    root, fake_env, monkeypatch
):
    fake_env({"prepare_exit": 2, "prepare_error": "no readable source"})
    calls: list[str] = []
    real = _runs().prepare

    def prepare(layout_, record, *a, **k):
        calls.append(record.id)
        return real(layout_, record, *a, **k)

    monkeypatch.setattr(_runs(), "prepare", prepare)
    w = Watcher(settings(root))
    shutil.rmtree(root / "inbox/failed")
    make_drop(root, "credit_snapshot", "acme")
    for _ in range(6):
        w.step()
    assert len(calls) == 1 and status(root) == ["rejected"]
    [failed] = (root / "inbox/failed").iterdir()
    assert "no readable source" in (failed / "WHY.txt").read_text()


def test_m3_when_the_move_to_failed_fails_the_record_still_says_why(root, fake_env, monkeypatch):
    fake_env({"prepare_exit": 2, "prepare_error": "no readable source"})
    prepares: list[Any] = []
    real = _runs().prepare

    def counted(*a: Any, **k: Any) -> str:
        prepares.append(a)
        return real(*a, **k)

    def refuse(*_a: Any, **_k: Any) -> Any:
        raise OSError("failed is not a real folder")

    monkeypatch.setattr(_runs(), "prepare", counted)
    monkeypatch.setattr(watcher_module.drops, "reject", refuse)
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    for _ in range(5):
        w.step()
    record = _only(root)
    assert record.status == "rejected" and len(prepares) == 1
    assert record.reason.startswith("no readable source (the folder could not be moved to ")
    assert f"it is kept in _engine/drops/{record.id})" in record.reason
    assert not (root / "inbox/credit_snapshot/acme").exists()
    assert (root / "_engine/drops" / record.id).is_dir()


def test_m1_an_interrupt_before_the_start_save_starts_nothing_and_resumes_once(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED})
    started = _track_starts(monkeypatch)
    make_drop(root, "credit_snapshot", "acme")
    _once(monkeypatch, "save", KeyboardInterrupt(), lambda lay, r: r.status == "running")
    w = Watcher(settings(root))
    with pytest.raises(KeyboardInterrupt):
        go(w)
    w.close()
    assert started == [] and (_only(root).status, _only(root).prepared) == ("queued", True)
    pump(Watcher(settings(root)), lambda: status(root) == ["finished"])
    assert len(started) == 1


def test_m1_an_interrupt_after_start_leaves_one_process_at_most_and_no_second_start(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED, "sleep": 20})
    started = _track_starts(monkeypatch)
    make_drop(root, "credit_snapshot", "acme")
    _once(monkeypatch, "save", KeyboardInterrupt(), lambda lay, r: r.status == "running" and r.pid)
    w = Watcher(settings(root))
    try:
        with pytest.raises(KeyboardInterrupt):
            go(w)
        w.close()
        assert len(started) == 1 and started[0].poll() is not None  # the child was stopped
        record = _only(root)
        assert (record.status, record.pid) == ("running", 0) and record.started_at
        second = Watcher(settings(root))
        for _ in range(3):
            second.step()
        assert len(started) == 1
        record = _only(root)
        assert record.status == "interrupted"
        assert record.reason == (
            "the watcher stopped while starting this run; its process may still be running"
            " \N{EM DASH} check before dropping the folder again"
        )
    finally:
        _wait_all(started)


def test_d6_a_running_record_without_a_pid_is_decided_before_the_first_scan(root):
    ensure_layout(root)
    save_record = watcher_module.runs.save
    save_record(
        Layout(root),
        Record("20261109-000001-01", "credit_snapshot", "acme", "running", "t", started_at="t"),
    )
    Watcher(settings(root)).close()
    assert _only(root).status == "interrupted"
    assert "may still be running" in _only(root).reason


def test_a_start_that_raises_oserror_fails_the_run_and_counts_toward_the_day(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED})

    def refuse(*_a: Any, **_k: Any) -> Any:
        raise OSError("cannot create the log")

    monkeypatch.setattr(_runs(), "start", refuse)
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root, max_per_day=1))
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
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root, max_per_day=1))
    try:
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
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root, max_per_day=1))
    try:
        for _ in range(6):
            w.step()
        assert len(started) == 1
    finally:
        _wait_all(started)


def test_l7_a_new_id_never_reuses_a_record_a_drop_folder_a_run_folder_or_a_log(root):
    w = Watcher(settings(root), now=lambda: datetime(2026, 11, 9, 12, 0, 0, tzinfo=UTC))
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
    fake_env({"events": DELIVERED})
    real = _runs().save
    failures = [3]

    def save(lay: Layout, record: Any) -> None:
        if record.status == "finished" and failures[0] > 0:
            failures[0] -= 1
            raise OSError("state folder briefly unwritable")
        real(lay, record)

    monkeypatch.setattr(_runs(), "save", save)
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    pump(w, lambda: status(root) == ["finished"], limit=10)
    assert [p.name for p in (root / "issuers/Acme Corp (acme)").iterdir()] == [
        "2026-11-09 credit_snapshot.html"
    ]
    assert _only(root).report == "issuers/Acme Corp (acme)/2026-11-09 credit_snapshot.html"


def test_f3_a_corrupt_issuer_registry_fails_the_run_instead_of_stopping_the_watcher(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 1})
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    go(w)
    (root / "_engine/state/issuers.json").write_text("{", encoding="utf-8")
    pump(w, lambda: status(root) != ["running"], limit=10)
    record = _only(root)
    assert record.status == "failed" and record.reason.startswith("could not be filed: ")
    assert not (root / "issuers").exists() or not any((root / "issuers").iterdir())


def test_f4_a_drop_with_a_file_nobody_can_open_is_rejected_after_the_settle_time(root):
    now = [0.0]
    drop = make_drop(root, "credit_snapshot", "acme")
    (drop / "locked.pdf").write_bytes(b"%PDF")
    (drop / "locked.pdf").chmod(0)
    w = Watcher(settings(root, settle_seconds=120), clock=lambda: now[0])
    try:
        for t in (0, 60, 120):
            now[0] = t
            w.step()
        assert load_all(layout(root)) == []
        now[0] = 121
        w.step()
        record = _only(root)
        assert record.status == "rejected" and record.reason.startswith("cannot be read: ")
        assert "locked.pdf" in record.reason
    finally:
        for locked in root.rglob("locked.pdf"):
            locked.chmod(0o644)


def test_f5_the_page_says_why_ended_runs_wait_when_the_library_cannot_be_rebuilt(
    root, fake_env, listed, monkeypatch
):
    fake_env({"events": DELIVERED})
    started = _track_starts(monkeypatch)

    def broken(_workspace: Path) -> None:
        raise ValueError("library is a link")

    monkeypatch.setattr(cpos_launch, "update_library_at", broken)
    make_drop(root, "credit_snapshot", "a", issuer="a")
    w = Watcher(settings(root, max_running=1))
    try:
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
    make_drop(root, "credit_snapshot", "a", issuer="a")
    w = Watcher(settings(root, max_per_day=1))
    try:
        pump(w, lambda: status(root) == ["running"])
        started[0].kill()
        started[0].wait()

        def broken(_workspace: Path) -> None:
            raise OSError("locked")

        monkeypatch.setattr(cpos_launch, "update_library_at", broken)
        make_drop(root, "credit_snapshot", "b", issuer="b")
        for _ in range(3):
            w.step()
        text = activity_js(root)
        assert (
            "the library could not be rebuilt (locked); ended runs wait for it; daily limit" in text
        )
    finally:
        _wait_all(started)


@pytest.mark.parametrize("cap", ["NaN", "Infinity", "-Infinity", "0", "-3"])
def test_f6_a_cap_that_is_not_a_finite_positive_amount_exits_2_with_one_line(cap, capsys):
    assert main(["--root", "/tmp/x", f"--cap={cap}"]) == 2
    err = capsys.readouterr().err
    assert "--cap" in err and "Traceback" not in err and len(err.strip().splitlines()) == 1


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
    monkeypatch.setattr(watcher_module.startup, "sys", SimpleNamespace(platform="win32"))


def test_m1_on_windows_the_lock_is_the_same_byte_whatever_text_the_file_holds(root, monkeypatch):
    _windows_locking(monkeypatch)
    (root / "_engine").mkdir()
    (root / "_engine/watcher.lock").write_text("old-host 12345678901234567890", encoding="utf-8")
    first = Watcher(settings(root))
    try:
        with pytest.raises(StartupRefused, match="another watcher is running on this folder"):
            Watcher(settings(root))
    finally:
        first.close()  # unlocks the byte it locked: raises nothing
    Watcher(settings(root)).close()
    text = (root / "_engine/watcher.lock").read_text(encoding="utf-8")
    assert text == f"{socket.gethostname()} {os.getpid()}"


def _fail_rejected_saves(monkeypatch: pytest.MonkeyPatch, times: int) -> list[int]:
    real = _runs().save
    left = [times]

    def save(layout_: Layout, record: Record) -> None:
        if record.status == "rejected" and left[0] > 0:
            left[0] -= 1
            raise PermissionError(13, "Access is denied (injected)")
        real(layout_, record)

    monkeypatch.setattr(_runs(), "save", save)
    return left


@pytest.mark.parametrize("failures", [1, 5])
def test_l1_a_failed_rejected_save_is_retried_and_nothing_is_moved_until_it_holds(
    root, monkeypatch, failures
):
    _fail_rejected_saves(monkeypatch, failures)
    drop = root / "inbox/credit_snapshot/no-context"
    drop.mkdir(parents=True)
    (drop / "a.pdf").write_bytes(b"%PDF")
    w = Watcher(settings(root))
    try:
        for _ in range(failures + 4):
            w.step()
    finally:
        w.close()
    record = _only(root)
    assert record.status == "rejected" and record.reason.startswith("no context file")
    [failed] = (root / "inbox/failed").iterdir()
    assert sorted(p.name for p in failed.iterdir()) == ["WHY.txt", "a.pdf"]


def test_l1_a_drop_folder_that_is_missing_is_rejected_saying_so_without_a_stray_folder(root):
    lay = layout(root)
    w = Watcher(settings(root))
    try:
        gone = Record(
            "20260101-000000-01", "credit_snapshot", "gone", "queued", "2026-01-01T00:00:00Z"
        )
        from deploy_workflow.inbox import runs as runs_module

        runs_module.save(lay, gone)
        w._records[gone.id] = gone
        for _ in range(3):
            w.step()
    finally:
        w.close()
    record = _only(root)
    assert record.status == "rejected"
    assert record.reason.endswith(f"; its folder was not found in _engine/drops/{record.id}")
    assert "kept in _engine" not in record.reason
    assert list((root / "inbox/failed").iterdir()) == []


def test_l2_a_folder_in_engine_drops_with_no_record_is_rejected_at_start_up(root):
    lay = ensure_layout(root)
    orphan = lay.drops / "20260101-000000-01"
    orphan.mkdir()
    (orphan / "context.json").write_text("{}", encoding="utf-8")
    Watcher(settings(root)).close()
    record = _only(root)
    assert (record.id, record.folder, record.pathway, record.status) == (
        orphan.name,
        orphan.name,
        "",
        "rejected",
    )
    assert record.reason == (
        "the watcher stopped while taking this folder in; its files are in "
        f"_engine/drops/{orphan.name} \N{EM DASH} drop it again"
    )
    assert (orphan / "context.json").is_file()
    again = Watcher(settings(root))
    again.step()
    again.close()
    assert len(load_all(lay)) == 1 and status(root) == ["rejected"]


def test_l4_a_rebuild_error_is_logged_once_until_it_changes_and_the_recovery_once(
    root, monkeypatch
):
    problem = ["share unavailable"]

    def broken(_workspace: Path) -> None:
        raise OSError(5, problem[0])

    monkeypatch.setattr(cpos_launch, "update_library_at", broken)
    w = Watcher(settings(root))
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
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    try:
        go(w)
        pump(w, lambda: status(root) not in (["running"], ["queued"]), limit=10)
        record = _only(root)
        assert record.status == "failed"
        assert record.reason == (
            "stopped by the watcher: its record could not be saved (state folder is full)"
        )
    finally:
        _wait_all(started)
        w.close()
