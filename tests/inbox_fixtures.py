"""Fixtures and helpers shared by the inbox watcher and run-start scheduler tests.

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

from deploy_workflow.inbox.drops import Layout
from deploy_workflow.inbox.runs import load_all
from deploy_workflow.inbox.watcher import Settings, Watcher
from deploy_workflow.model.adapter import KEY_VARIABLES
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.owners import cpos_launch

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
    """A test that never closes its Watcher must not leave a log file open for the next."""
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
