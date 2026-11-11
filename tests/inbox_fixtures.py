"""Fixtures and helpers shared by the scheduler tests.

Tests start real child processes (tests/fixtures/fake_launcher.py), which call no provider and
spend nothing. The ``root`` fixture kills any run still alive.
"""

from __future__ import annotations

import json
import logging
import os
import re
import signal
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from deploy_workflow.inbox.layout import Layout
from deploy_workflow.inbox.runs import Record, load_all
from deploy_workflow.inbox.scheduler import Scheduler, Settings
from deploy_workflow.model.adapter import KEY_VARIABLES
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.owners import cpos_launch
from deploy_workflow.run_start import submissions

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
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


@pytest.fixture(autouse=True)
def _no_leaked_log_handlers() -> Iterator[None]:
    """A test that never closes its Scheduler must not leave a log file open for the next."""
    yield
    package = logging.getLogger("deploy_workflow.inbox")
    for handler in list(package.handlers):
        package.removeHandler(handler)
        handler.close()


@pytest.fixture
def fake_env(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, Any]], None]:
    def set_plan(plan: dict[str, Any]) -> None:
        monkeypatch.setenv("FAKE_PLAN", json.dumps({"report": True, **plan}))

    return set_plan


@pytest.fixture(autouse=True)
def listed(request: pytest.FixtureRequest) -> Callable[..., None]:
    """Replace the library rebuild: ``"*"`` lists every run folder, None excludes each.

    The replacement is installed for each test that uses ``root``. This fixture is autouse and a
    plugin's autouse fixtures reach every test in the session, so it asks for ``monkeypatch`` only
    when it installs: a test of another module keeps its own fixture teardown order."""

    def install(which: str | None = "*", reason: str = "") -> None:
        def build(workspace: Path) -> SimpleNamespace:
            names = sorted(p.name for p in (workspace / "runs").iterdir())
            runs = [{"id": n} for n in names] if which == "*" else []
            left = [] if which == "*" else [(n, reason) for n in names]
            return SimpleNamespace(runs=runs, excluded=left)

        request.getfixturevalue("monkeypatch").setattr(cpos_launch, "update_library_at", build)

    if "root" in request.fixturenames:
        install("*")
    return install


def settings(root: Path, **changes: Any) -> Settings:
    changes = {"launcher": (sys.executable, FAKE), **changes}
    return Settings(root, **changes)


def layout(root: Path) -> Layout:
    return Layout(root)


def submit_run(
    w: Scheduler,
    root: Path,
    issuer: str = "acme",
    *,
    pathway: str = "credit_snapshot",
    payload: bytes | None = None,
) -> Record:
    """Upload one document and submit it the way the start page does: the service's own summary
    issues the approval digest, then ``Scheduler.submit`` takes the run."""
    body = json.loads(json.dumps(CONTEXT))
    body["run"]["pathway"] = pathway
    body["run"]["as_of"] = "2026-11-09"
    body["identity"]["issuer_id"] = issuer
    body["identity"]["issuer_name"] = "Acme Corp"
    answers = submissions.validated(
        {
            "context": body,
            "modules": [],
            "max_turns": 32,
            "level": "basic",
            "submitted_by": "analyst",
        }
    )
    lay = Layout(root)
    sid = submissions.new(lay)
    text = payload or f"Net sales were 100 for {issuer}.".encode()
    (submissions.files_folder(lay, sid) / "a.txt").write_bytes(text)
    got = submissions.summary(lay, sid, answers, config=w.settings.config, cap=w.settings.cap)
    assert got["error"] == "", got["error"]
    return w.submit(sid, answers, str(got["digest"]))


def status(root: Path) -> list[str]:
    return [r.status for r in load_all(layout(root))]


def activity_js(root: Path) -> str:
    return (root / "_engine/activity.js").read_text(encoding="utf-8")


def pump(w: Scheduler, until: Callable[[], bool], limit: float = 5) -> None:
    deadline = time.monotonic() + limit
    while not until():
        assert time.monotonic() < deadline, "condition not met in time"
        w.step()
        time.sleep(0.05)


def go(w: Scheduler) -> None:
    """Two polls: the first starts what is queued, the second sees what the start left."""
    w.step()
    w.step()
