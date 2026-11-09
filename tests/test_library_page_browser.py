"""The generated library page in a real browser, opened from disk with every other request blocked.
Synthetic runs (tests/library_fixtures.py); needs node with the playwright package."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from library_fixtures import make_run, method

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "apps/issuer-library/static/browser_check.cjs"
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library

pytestmark = pytest.mark.browser
HOSTILE = "<img src=x onerror=alert(1)><script>alert(2)</script>"


def browser_report(page: Path) -> dict:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    probe = subprocess.run([node, "-e", "require('playwright')"], capture_output=True, check=False)
    if probe.returncode:
        pytest.skip("the playwright package is not available to node")
    done = subprocess.run(
        [node, str(CHECK), str(page)], capture_output=True, text=True, timeout=240, check=False
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


@pytest.fixture
def stand_in_method(monkeypatch):
    monkeypatch.setattr("deploy_workflow.library_index.current_method", lambda: method())


def test_the_page_works_from_disk_without_any_request(tmp_path, stand_in_method):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    make_run(tmp_path, "run-b", as_of="2025-03-31")
    make_run(tmp_path, "run-c", issuer_id="zzz", issuer_name=HOSTILE, as_of="2025-06-30")
    (tmp_path / "runs/legacy").mkdir()
    page, _ = update_library.update(tmp_path, built_at="09 Nov 2026, 12:00 UTC")
    report = browser_report(page)
    assert report["blocked"] == [] and report["errors"] == [] and report["dialogs"] == []
    assert report["scripts"] == 2  # The data block and the page script; nothing injected.
    assert report["rows"] == 3
    assert any(HOSTILE in text for text in report["issuers"])  # Shown as text, not markup.
    assert report["missingLinks"] == [] and report["remoteLinks"] == []
    assert report["selected"] == "Northbridge Synthetic Group"
    assert report["bottomLines"] == ["CP-0 bottom line.", "CP-1 bottom line."]
    assert report["rowsAfterSearch"] == 0
    assert report["rowsLatest"] == 2  # run-b for nbg, run-c for zzz.
    assert report["reportOpened"] is True


def test_an_empty_library_says_how_runs_get_there(tmp_path, stand_in_method):
    page, _ = update_library.update(tmp_path, built_at="09 Nov 2026, 12:00 UTC")
    report = browser_report(page)
    assert report["blocked"] == [] and report["errors"] == []
    assert report["rows"] == 0
    assert report["emptyHeading"] == ["No completed runs on the current methodology yet"]
