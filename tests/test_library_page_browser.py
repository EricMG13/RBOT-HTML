"""The generated library in a real browser (headless Chrome), opened from disk over file://.

Chrome's console is read for errors, including Content Security Policy violations: the page's
policy blocks every network request, so a violation is a request the page tried to make or a source
it needs but is not allowed. Needs Google Chrome or Chromium; skipped where there is none."""

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from library_fixtures import make_run, method
from test_credit_os_catalogue import CHARTS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library

pytestmark = pytest.mark.browser
MATURITIES = """
### Chart data: debt maturities

| Period | Debt maturing | Reporting unit | Basis and limitation |
| --- | --- | --- | --- |
| FY2025 ending September 30 | 580 | US$m | Synthetic bucket. |
| FY2026 ending September 30 | 92 | US$m | Synthetic bucket. |
| Thereafter | 12637 | US$m | Synthetic bucket. |
"""
CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def chrome() -> str:
    found = next((c for c in CANDIDATES if Path(c).is_file()), None)
    found = found or shutil.which("google-chrome") or shutil.which("chromium")
    if found is None:
        pytest.skip("Chrome or Chromium is not installed")
    return found


def visit(page: Path, route: str = "") -> tuple[str, list[str]]:
    """The page's DOM after it ran, and its console messages."""
    done = subprocess.run(
        [
            chrome(),
            "--headless=new",
            "--disable-gpu",
            "--enable-logging=stderr",
            "--v=0",
            "--virtual-time-budget=10000",
            "--dump-dom",
            page.as_uri() + route,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    return done.stdout, re.findall(r"CONSOLE[^\n]*", done.stderr)


@pytest.fixture(autouse=True)
def stand_in_method(monkeypatch):
    monkeypatch.setattr("deploy_workflow.library_index.current_method", lambda: method())


def test_the_library_works_from_disk_without_any_request(tmp_path):
    make_run(tmp_path, "run-a", as_of="2024-12-31", cp1_extra=CHARTS + MATURITIES)
    (tmp_path / "runs/legacy").mkdir()
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    dom, console = visit(page)
    assert console == []  # No script error and no policy violation.
    assert len(re.findall(r"<tr[ >]", dom.split("<tbody>", 1)[1].split("</tbody>")[0])) == 1
    assert "Northbridge Synthetic Group" in dom
    dom, console = visit(page, "#W-Overview/overview?c=run-a")
    assert console == []
    assert (
        len(re.findall(r'class="summary-chart"', dom)) == 4
    )  # Leverage, cover, liquidity, maturities.
    dom, console = visit(page, "#W-Reports/list?c=run-a")
    delivery = re.search(r'href="#W-Reports/([0-9a-f]{64})\?c=run-a"', dom)
    assert delivery, "the Reports tab lists the run's report"
    dom, console = visit(page, f"#W-Reports/{delivery[1]}?c=run-a")
    assert console == []  # The presented report ran its adapter and the policy allowed it.
    frame = re.search(r'<iframe id="report-preview"[^>]*src="([^"]*)"', dom)
    assert frame and frame[1] == f"reports/run-a/{delivery[1]}/report.html"
    assert (page.parent / frame[1]).is_file()
    assert re.search(r'frame-status"[^>]*hidden', dom)  # Loaded: the loading notice is gone.


def test_run_activity_and_forecast_not_run_from_disk(tmp_path):
    make_run(tmp_path, "run-a")  # No CP-2G output, so no forecast model.
    half = make_run(tmp_path, "run-half", issuer_id="zzz", issuer_name="Zeta Synthetic")
    next(half.glob("completed-*.json")).unlink()
    library = update_library.update_library(tmp_path)
    reason = dict(library.excluded)["run-half"]
    assert reason
    page = tmp_path / "library/index.html"
    dom, console = visit(page, "#CP-OS/activity")
    assert console == []
    assert "Run folders not shown" in dom and "run-half" in dom
    assert html.escape(reason, quote=False) in dom
    assert (
        'data-place="Run activity"' in dom
        and "<button" not in dom.split('id="content"', 1)[1].split("</article>")[0]
    )
    dom, console = visit(page, "#W-Forecast/none?c=run-a")
    assert console == []
    assert "No forecast model was published from this run’s files" in dom


def test_an_empty_library_says_so(tmp_path):
    update_library.update_library(tmp_path)
    dom, console = visit(tmp_path / "library/index.html")
    assert console == []
    assert "No runs in this workspace yet" in dom


def test_a_policy_violation_is_seen(tmp_path):
    """The check is not blind: loosening nothing but forbidding scripts shows up in the console."""
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    page.write_text(page.read_text().replace("script-src 'self'", "script-src 'none'"))
    _, console = visit(page)
    assert any("Content Security Policy" in line for line in console)


PROBE = """<script>
document.querySelector('[data-k="run_type"][value="secondary"]').checked = true;
document.getElementById('f').dispatchEvent(new Event('change', {bubbles: true}));
const sel = document.getElementById('s1-pathway');
const out = document.createElement('pre');
out.id = 'probe';
out.textContent = JSON.stringify({value: sel.value, disabled: sel.disabled, built: build()});
document.body.append(out);
</script>
</body>"""


def test_a_fixed_pathway_is_selected_and_locked(tmp_path):
    from deploy_workflow.inbox.drops import ensure_layout, write_templates

    short = tempfile.mkdtemp(prefix="ib", dir="/tmp")  # tmp_path is over the 80-character limit.
    shutil.rmtree(short)
    layout = ensure_layout(Path(short))
    write_templates(layout, ROOT / "docs/templates/context-form.html")
    form = layout.inbox / "earnings_update/_template/context-form.html"
    page = tmp_path / "probe.html"  # The form with a probe that changes the run type, then reads.
    text = form.read_text(encoding="utf-8")
    page.write_text(text.replace("</body>", PROBE, 1), encoding="utf-8")
    dom, console = visit(page)
    assert console == []
    probe = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert probe["value"] == "earnings_update" and probe["disabled"] is True
    assert probe["built"]["run"]["run_type"] == "secondary"  # The run type did change ...
    assert probe["built"]["run"]["pathway"] == "earnings_update"  # ... the pathway did not.
    shutil.rmtree(layout.root)
