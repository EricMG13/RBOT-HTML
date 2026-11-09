"""The inbox watcher: claim, prepare, launch, limit, file and publish.

Tests start real child processes (tests/fixtures/fake_launcher.py), which call no provider and
spend nothing. Every wait has a limit, and the ``root`` fixture kills any run still alive.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import library_fixtures
import pytest

from deploy_workflow.inbox import activity
from deploy_workflow.inbox import watcher as watcher_module
from deploy_workflow.inbox.drops import Layout, ensure_layout
from deploy_workflow.inbox.runs import alive, load_all
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
        update_library_at(lay.engine)
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


def test_r2_a_second_watcher_on_a_live_one_is_refused(root):
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        ensure_layout(root)
        (root / "_engine/watcher.lock").write_text(str(other.pid), encoding="utf-8")
        with pytest.raises(StartupRefused, match=rf"another watcher \(pid {other.pid}\)"):
            Watcher(settings(root))
        assert main(["--root", str(root)]) == 2
        assert (root / "_engine/watcher.lock").read_text(encoding="utf-8") == str(other.pid)
    finally:
        other.kill()
        other.wait()


def test_r2_a_stale_lock_is_replaced_and_removed_on_a_clean_exit(root, monkeypatch):
    gone = subprocess.Popen([sys.executable, "-c", "pass"])
    gone.wait()
    ensure_layout(root)
    lock = root / "_engine/watcher.lock"
    lock.write_text(str(gone.pid), encoding="utf-8")
    w = Watcher(settings(root))
    assert lock.read_text(encoding="utf-8") == str(os.getpid())

    def interrupt(_seconds: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(watcher_module.time, "sleep", interrupt)
    w.run_forever()
    assert not lock.exists()


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


def test_r9_a_run_that_cannot_be_recorded_is_terminated_and_stays_queued(
    root, fake_env, monkeypatch
):
    fake_env({"events": DELIVERED, "sleep": 20})
    started: list[subprocess.Popen[bytes]] = []
    real_start, real_save = watcher_module.runs.start, watcher_module.runs.save

    def start(*args: Any, **kwargs: Any) -> subprocess.Popen[bytes]:
        started.append(real_start(*args, **kwargs))
        return started[-1]

    def save(lay: Layout, record: Any) -> None:
        if record.status == "running":
            raise OSError("state folder is full")
        real_save(lay, record)

    monkeypatch.setattr(watcher_module.runs, "start", start)
    monkeypatch.setattr(watcher_module.runs, "save", save)
    make_drop(root, "credit_snapshot", "acme")
    w = Watcher(settings(root))
    go(w)
    assert len(started) == 1 and started[0].wait(timeout=5) is not None
    assert status(root) == ["queued"]
    assert "state folder is full" in _log(root)


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
