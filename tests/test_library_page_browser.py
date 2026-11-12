"""The generated library in a real browser (headless Chrome), opened from disk over file://.

Chrome's console is read for errors, including Content Security Policy violations: the page's
policy blocks every network request, so a violation is a request the page tried to make or a source
it needs but is not allowed. Needs Google Chrome or Chromium; skipped where there is none."""

import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from library_fixtures import (
    CITED,
    REPORT_ROWS,
    SOURCE_NAME,
    SOURCE_PAGES,
    inventory_text,
    make_run,
    method,
)
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
# Synthetic: a liquidity bridge as the launcher asks CP-2D for it (here placed in the CP-1 fixture).
BRIDGE = """
### Chart data: liquidity bridge

| Step | Amount | Reporting unit | Basis and limitation |
| --- | --- | --- | --- |
| Opening accessible liquidity | 900 | US$m | Synthetic. |
| Free cash flow | 120 | US$m | Synthetic. |
| Debt repayment | -450 | US$m | Synthetic. |
| Closing accessible liquidity | 570 | US$m | Synthetic. |
"""


def chart_table(heading: str, header: str, *rows: str) -> str:
    divider = " | ".join(["---"] * (header.count("|") + 1))
    body = "".join(f"\n| {row} |" for row in rows)
    return f"\n### Chart data: {heading}\n\n| {header} |\n| {divider} |{body}\n"


# Synthetic: the credit-structure tables as the launcher asks for them (placed in the CP-1 fixture).
UNIT_BASIS = "Reporting unit | Basis and limitation"
STRUCTURE = (
    chart_table(
        "debt stack",
        f"Facility | Ranking | Secured | Amount | Cumulative leverage | {UNIT_BASIS}",
        "Term loan | 1 | Yes | 1,200 | 2.4 | US$m | Synthetic.",
        "Notes | 2 | No | 800 | 4.0 | US$m | Synthetic.",
    )
    + chart_table(
        "covenant headroom",
        f"Test | Threshold | Current | Headroom | Direction | {UNIT_BASIS}",
        "Net leverage | 5.0 | 4.2 | 0.8x | Passes at or below | x | Synthetic.",
        "Liquidity | 100 | Not supplied: not stated | Not supplied: no current "
        "| Passes at or above | US$m | Synthetic.",
    )
    + chart_table(
        "portfolio limits",
        f"Limit | Current exposure | Proposed exposure | Limit value | {UNIT_BASIS}",
        "Single issuer | 3.0 | 4.0 | 5.0 | % NAV | Synthetic.",
    )
    + chart_table(
        "prior and current results",
        f"Measure | Prior period | Prior | Current period | Current | {UNIT_BASIS}",
        "Revenue | FY2023 | 2,100 | FY2024 | 2,250 | US$m | Synthetic.",
    )
    + chart_table(
        "margin and KPI changes",
        f"Measure | Prior period | Prior | Current period | Current | {UNIT_BASIS}",
        "EBITDA margin | FY2023 | 19.5 | FY2024 | 21.0 | % | Synthetic.",
    )
    + chart_table(
        "peer range \u2014 percent metrics",
        f"Metric | Issuer | Peer low | Peer median | Peer high | Peer count | {UNIT_BASIS}",
        "EBITDA margin | 21.0 | 12.0 | 18.5 | 26.0 | 7 | % | Synthetic.",
    )
    + chart_table(
        "yield against maturity",
        f"Instrument | Maturity date | Yield | Spread | Quote date | Source class | {UNIT_BASIS}",
        "Note A | 2028-06-15 | 6.4 | +310 bp | 2024-12-31 | Dealer quote | % | Synthetic.",
        "Note B | 2030-06-15 | 7.0 | +350 bp | 2024-12-31 | Dealer quote | % | Synthetic.",
    )
    + chart_table(
        "recovery by class",
        f"Class | Scenario | Claim | Recovery | Recovery % | {UNIT_BASIS}",
        "Senior | Base | 1,200 | 1,080 | 90 | US$m | Synthetic.",
        "Senior | Downside | 1,200 | 720 | 60 | US$m | Synthetic.",
        "Junior | Base | 800 | Not supplied: no value | Not supplied: no value | US$m | Synthetic.",
    )
    + chart_table(
        "value allocation \u2014 scenario 1",
        f"Step | Amount | {UNIT_BASIS}",
        "Enterprise value | 2,000 | US$m | Synthetic.",
        "Senior distribution | -1,080 | US$m | Synthetic.",
        "Value not distributed | 920 | US$m | Synthetic.",
    )
)
# Synthetic: a calendar lane as the launcher asks a module for it (here placed in the CP-1 fixture).
EVENTS = """
### Events: Financing

| Event date | Date precision | Published | Event | Status | Source | Credit relevance |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-03-31 | day | \u2014 | Synthetic note | Scheduled — due | Synthetic filing p.1 | Wall |
| 2025-06 | month | 2025-05-01 | Synthetic call | Historical — announced | Synthetic memo | Cost |
| 2025-Q3 | quarter | \u2014 | Synthetic review | Scenario — modelled | Synthetic memo | Rating |
| 2025 | year | \u2014 | Synthetic maturity year | Scheduled — due | Synthetic filing p.2 | Wall |
"""
# Synthetic: a credit-risk transmission map as the launcher asks for it (in the CP-1 fixture).
MAPS = """
### Map: credit-risk transmission

| From | Relationship | Edge type | To | Evidence |
| --- | --- | --- | --- | --- |
| Synthetic driver | drives | Documentary Fact | Synthetic mechanism | Synthetic p.1 |
| Synthetic mechanism | squeezes | Management Language | Synthetic outcome | Synthetic p.2 |
| Synthetic driver | also hits | Analyst Interpretation | Synthetic outcome | Synthetic p.3 |
| Synthetic outcome | feeds back | Insufficient Information | Synthetic driver | Synthetic p.4 |
| Synthetic outcome | then | Documentary Fact | Synthetic step 1 | Synthetic p.5 |
| Synthetic step 1 | then | Documentary Fact | Synthetic step 2 | Synthetic p.6 |
| Synthetic step 2 | then | Documentary Fact | Synthetic step 3 | Synthetic p.7 |
| Synthetic step 3 | then | Documentary Fact | Synthetic step 4 | Synthetic p.8 |
| Synthetic step 4 | then | Documentary Fact | Synthetic step 5 | Synthetic p.9 |
| Synthetic step 5 | then | Documentary Fact | Synthetic step 6 | Synthetic p.10 |
| Synthetic step 6 | then | Documentary Fact | Synthetic step 7 | Synthetic p.11 |
| Synthetic step 7 | then | Documentary Fact | Synthetic step 8 | Synthetic p.12 |
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


EARLIER_LEAD = (
    "This run is in the earlier format: "
    "its handoffs carry no reader passages for Overview to select."
)


def visit(page: Path, route: str = "", width: int = 1280) -> tuple[str, list[str]]:
    """The page's DOM after it ran, and its console messages."""
    done = subprocess.run(
        [
            chrome(),
            "--headless=new",
            "--disable-gpu",
            f"--window-size={width},900",
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
    # The row names its run (the cell's title holds the id whole), and the id opens it.
    assert re.search(
        r'<td class="run-id" title="run-a">'
        r'<a href="#W-Overview/overview\?c=run-a"[^>]*>run-a</a></td>',
        dom,
    )
    assert 'id="library-nav"' not in dom  # Issuers are a filter, not a second navigation.
    delivery = next((tmp_path / "runs/run-a/deliveries").iterdir()).name
    # The delivered report is retired (decision 1): the row opens the run and its history.
    assert '<a class="report-link" href="#W-Overview/overview?c=run-a"' in dom
    assert '<a class="report-link" href="#W-Report/history?c=run-a"' in dom
    assert "#W-Reports" not in dom and "report.html" not in dom and "Open report" not in dom
    # A cited source links the retained file it quotes.
    assert f'href="../runs/run-a/deliveries/{delivery}/CP-1.md" target="_blank"' in dom
    dom, console = visit(page, "#W-Overview/overview?c=run-a")
    assert console == []
    # The Overview selects (ruling H5): this earlier-format run has no reader passages, so no
    # lead, and the visuals catalogue places no CP-1 chart on it; the charts stay with the module.
    assert 'id="overview-lead"' in dom and EARLIER_LEAD in dom
    assert "No bottom line in this handoff." in dom and 'id="overview-dates"' in dom
    assert 'class="navigator"' in dom and 'class="workbench overview-workspace"' in dom
    assert len(re.findall(r'<div class="panel-card">', dom)) == 0
    dom, console = visit(page, "#CP-1/performance?c=run-a")
    assert console == []
    assert (
        len(re.findall(r'<div class="panel-card">', dom)) == 4
    )  # Leverage, cover, liquidity, maturities.
    # The Report history lists the run; no report frame is drawn and no report copy is held.
    dom, console = visit(page, "#W-Report/history?c=run-a")
    assert console == []
    assert '<table class="history-table">' in dom and 'aria-current="true"' in dom
    assert "<iframe" not in dom.replace('id="model-preview"', "")
    assert not (page.parent / "reports").exists()
    assert not (page.parent / "report-adapter.js").exists()
    # An old Reports or Calendar hash opens the run's Report history, not a blank page.
    old_hashes = (
        "#W-Reports/list?c=run-a",
        f"#W-Reports/{delivery}?c=run-a",
        "#W-Calendar?c=run-a",
    )
    for old in old_hashes:
        dom, console = visit(page, old)
        assert console == []
        assert '<table class="history-table">' in dom, old
    # With no run named, the page opens the workspace's first run, as every run page does.
    dom, console = visit(page, "#W-Reports/list")
    assert console == [] and '<table class="history-table">' in dom


def test_an_old_reports_hash_opens_the_library_when_no_run_is_known(tmp_path):
    update_library.update_library(tmp_path)  # No runs.
    dom, console = visit(tmp_path / "library/index.html", "#W-Reports/list")
    assert console == []
    assert "history-table" not in dom and "No runs in this workspace yet" in dom


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
    # Run activity is live runs only (decision 10): from disk there is no live data, and the
    # excluded folder is no longer listed there.
    assert "Run activity could not be read" in dom and "run-half" not in dom
    assert "Run folders not shown" not in dom
    assert (
        'data-place="Run activity"' in dom
        and "<button" not in dom.split('id="content"', 1)[1].split("</article>")[0]
    )
    # The folder and its reason are on the library page, in a details element that is closed.
    dom, console = visit(page, "#W-Library/cases")
    assert console == []
    shown = re.search(r'<details class="library-not-shown">(.*?)</details>', dom, re.DOTALL)
    assert shown and "Run folders not shown" in shown[1] and "run-half" in shown[1]
    assert html.escape(reason, quote=False) in shown[1]
    dom, console = visit(page, "#W-Forecast/none?c=run-a")
    assert console == []
    assert "No forecast model was published from this run’s files" in dom


LIVE_CHIPS_PROBE = """addEventListener('load',()=>setTimeout(()=>{
  const out={};
  for(const state of ['running','done','waiting']){
    const s=getComputedStyle(document.querySelector('.chip-'+state));
    out[state]=[s.backgroundColor,s.color];
  }
  document.body.insertAdjacentHTML('beforeend','<pre id="chips">'+JSON.stringify(out)+'</pre>');
},500));
"""


def test_live_run_chips_show_their_state_colours(tmp_path):
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    activity = {
        "updated": "2026-11-10T00:00:00Z",
        "runs": [
            {
                "id": "r1",
                "status": "running",
                "issuer_name": "Northbridge Synthetic Group",
                "modules": [["CP-1", "running"], ["CP-0", "done"], ["CP-2", "waiting"]],
            }
        ],
    }
    # The page loads ../activity.js, the file the watcher writes beside the library folder.
    (tmp_path / "activity.js").write_text(
        f"window.RUN_ACTIVITY={json.dumps(activity)};\n", encoding="utf-8"
    )
    page = tmp_path / "library/index.html"
    probe = tmp_path / "library/probe.html"
    (tmp_path / "library/probe.js").write_text(
        LIVE_CHIPS_PROBE, encoding="utf-8"
    )  # CSP: self only.
    probe.write_text(
        page.read_text(encoding="utf-8").replace(
            "</body>", '<script src="probe.js"></script></body>', 1
        ),
        encoding="utf-8",
    )
    dom, console = visit(probe, "#CP-OS/activity")
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="chips">(.*?)</pre>', dom, re.DOTALL)[1]))
    # Module badges follow the component reference: running blue-700 on blue-50, done green on
    # green-bg, waiting text-tertiary on gray-100.
    assert seen["running"] == ["rgb(229, 232, 255)", "rgb(0, 18, 178)"]
    assert seen["done"] == ["rgb(232, 255, 244)", "rgb(15, 128, 72)"]
    assert seen["waiting"] == ["rgb(244, 244, 245)", "rgb(71, 74, 79)"]


RUN_ACTIVITY_PROBE = (
    Path(__file__).with_name("browser_probe_run_activity.js").read_text(encoding="utf-8")
)
LONG_FOLDER = (
    "2026-11-12-a-very-long-issuer-folder-name-that-would-not-fit-a-narrow-card-without-wrapping"
)


def run_activity_library(tmp_path: Path) -> Path:
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    modules = [
        [f"Module {i}", s] for i, s in enumerate(["done"] * 3 + ["running"] + ["waiting"] * 4)
    ]
    activity = {
        "updated": "2026-11-12T00:00:00Z",
        "cap": "20",
        "runs": [
            {
                "id": "r1",
                "status": "running",
                "issuer_name": "Northbridge Synthetic Group",
                "pathway": "credit_snapshot",
                "folder": LONG_FOLDER,
                "submitted_by": "Dana Reyes",
                "started_at": "2026-11-12T00:00:00Z",
                "spent": "3.10",
                "modules": modules,
                "files": ["annual-report.pdf", "presentation.pdf"],
                "reason": "reading",
            },
            {
                "id": "q1",
                "status": "queued",
                "issuer_name": "Queued Issuer One",
                "pathway": "earnings_update",
                "folder": LONG_FOLDER + "-q1",
            },
            {
                "id": "q2",
                "status": "queued",
                "issuer_name": "Queued Issuer Two",
                "pathway": "credit_snapshot",
                "folder": "q2",
            },
        ],
    }
    (tmp_path / "activity.js").write_text(
        f"window.RUN_ACTIVITY={json.dumps(activity)};\n", encoding="utf-8"
    )
    return tmp_path / "library/index.html"


def test_run_activity_puts_waiting_beside_running_on_a_wide_window(tmp_path):
    page = run_activity_library(tmp_path)
    seen = read_probe(page, "#CP-OS/activity", 1440, RUN_ACTIVITY_PROBE)
    assert seen["waitingLeft"] > seen["runningRight"], seen
    assert seen["progressName"] == "Modules done"
    assert (seen["progressMax"], seen["progressValue"], seen["barHeight"]) == (8, 3, 8)
    # A list opened before the reload is still open after it.
    assert seen["openBefore"] is True and seen["openAfter"] is True and seen["changedShown"] is True


def test_run_activity_has_no_horizontal_scroll_on_a_phone(tmp_path):
    # Chrome will not open a window under 500px, so the page opens in a 375px frame.
    page = run_activity_library(tmp_path)
    (page.parent / "probe.js").write_text(RUN_ACTIVITY_PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    wrapper = page.parent / "wrap.html"
    wrapper.write_text(
        '<iframe src="index.html#CP-OS/activity" width="375" height="800"></iframe><pre id="probe">'
        "</pre><script>addEventListener('message', e => "
        "{ document.getElementById('probe').textContent = e.data; });</script>",
        encoding="utf-8",
    )
    dom, console = visit(wrapper, "", 1000)
    assert console == []
    seen = probe_json(dom)
    assert seen["innerWidth"] == 375 and seen["scrollWidth"] <= 375, seen
    assert seen["contentScroll"] <= seen["contentClient"], seen


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


# A script the test adds beside the generated page (the page's policy allows its own folder):
# it drives the module report as a reader would and writes what it saw into the DOM, where
# --dump-dom returns it.
PROBE = Path(__file__).with_name("browser_probe_module_report.js").read_text(encoding="utf-8")


OVERVIEW_PROBE = Path(__file__).with_name("browser_probe_overview.js").read_text(encoding="utf-8")


def report_library(tmp_path: Path, cp0_confidence: str = "Medium") -> Path:
    digest = hashlib.sha256(SOURCE_PAGES).hexdigest()
    run = make_run(
        tmp_path,
        "run-a",
        as_of="2024-12-31",
        cp0_extra=inventory_text(digest),
        cp0_confidence=cp0_confidence,
        # Under Findings: the tables are Reference, not audit (R39).
        cp1_finding=CITED_FINDING,
        cp1_findings=CITED + REPORT_ROWS,
    )
    (run / "source-text").mkdir()
    (run / "source-text" / SOURCE_NAME).write_bytes(SOURCE_PAGES)
    update_library.update_library(tmp_path)
    return tmp_path / "library/index.html"


@pytest.mark.parametrize("width", [1440, 1280])
def test_a_module_report_fits_and_its_chips_open_the_source_page(tmp_path, width):
    page = report_library(tmp_path)
    (page.parent / "probe.js").write_text(PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#CP-1/head?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    for state in ("closed", "inspector"):  # With the inspector open the canvas is narrower still.
        assert seen[state] == {"fits": True, "valueInCard": True, "chipsInCard": True, "rows": 2}, (
            state
        )
    assert seen["rowFocus"] == {"focused": True, "box": True}  # The row button takes focus.
    opened = seen["open"]
    assert opened["hidden"] is False and "chip=" in opened["hash"] and "e=" in opened["hash"]
    assert opened["excerpt"] and "Cash paid during the period" in opened["excerpt"]
    assert opened["mark"] == "Cash paid during the period"
    assert "Matches publication" in opened["text"] and "Quote found on page" in opened["text"]
    assert f"Source page · {SOURCE_NAME} p.123" in opened["text"]
    assert opened["pressed"] == "true" and opened["focusInInspector"] is True
    assert opened["open"] == f"../runs/run-a/source-text/{SOURCE_NAME}"
    assert seen["escaped"] == {"hidden": True, "focusOnChip": True, "hash": "#CP-1/head?c=run-a"}
    assert seen["anchor"]["hash"] == "#CP-1/numbers?c=run-a"
    assert seen["anchor"]["current"] == "Key numbers" and seen["anchor"]["chipStillThere"] is True


# A Reader summary finding whose impact cites a page: the Findings part draws a page chip.
CITED_FINDING = (
    "| Interest was paid in cash. | K, page:123 says “Cash paid during the period”. | High |"
)
GAPS_PROBE = Path(__file__).with_name("browser_probe_gaps.js").read_text(encoding="utf-8")
# Two citations whose key no inventory knows: each resolves to a gap chip with no page.
UNKEYED = "\n### Unkeyed citations\n\nThe figure is printed in Z, page:9 and in Y, page:8.\n"


def test_a_paragraph_citing_no_page_lists_them_behind_its_basis_button_and_escape_returns(
    tmp_path,
):
    digest = hashlib.sha256(SOURCE_PAGES).hexdigest()
    run = make_run(
        tmp_path,
        "run-a",
        as_of="2024-12-31",
        cp0_extra=inventory_text(digest),
        cp1_finding=CITED_FINDING,
        cp1_findings=CITED + REPORT_ROWS + UNKEYED,
    )
    (run / "source-text").mkdir()
    (run / "source-text" / SOURCE_NAME).write_bytes(SOURCE_PAGES)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    (page.parent / "probe.js").write_text(GAPS_PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#CP-1/head?c=run-a")
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    # The Basis button of the UNKEYED paragraph (two citations no inventory knows): no chip or
    # count is printed in prose.
    assert seen["control"] == "Basis", seen
    assert seen["verified"] >= 1 and seen["proseChips"] == 0
    opened = seen["open"]
    assert opened["hidden"] is False and "chip=p" in opened["hash"]
    assert opened["items"] == 2  # one citation-gap section per citation
    assert opened["focusInInspector"] is True and opened["pressed"] == "true"
    assert seen["escaped"] == {
        "hidden": True,
        "focusOnControl": True,
        "hash": "#CP-1/head?c=run-a",
    }


# A narrative section and a register wider than the canvas, inserted under Findings. A section with
# a table is Reference, so the register sits in the closed Statements and registers part.
LONG = "A long note that keeps the register wider than the canvas"
ANALYSIS_ROWS = f"""
### Credit analysis

### Debt structure

Debt is mostly secured, K, page:123 states the figure.

| Instrument | Maturity | Amount | Note | Covenants | Security | Guarantors | Call schedule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Term loan | 2028 | 1,200 | {LONG} | Not supplied | First lien | Parent | Non-call 2y |
| Notes | 2030 | 700 | {LONG} | Incurrence | None | Parent | Make-whole |
"""


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_reference_part_fits_the_page(tmp_path, width):
    digest = hashlib.sha256(SOURCE_PAGES).hexdigest()
    run = make_run(
        tmp_path,
        "run-a",
        as_of="2024-12-31",
        cp0_extra=inventory_text(digest),
        cp1_findings=ANALYSIS_ROWS,
        cp1_extra=CITED + REPORT_ROWS,
    )
    (run / "source-text").mkdir()
    (run / "source-text" / SOURCE_NAME).write_bytes(SOURCE_PAGES)
    update_library.update_library(tmp_path)
    dom, console = visit(tmp_path / "library/index.html", "#CP-1/reference?c=run-a", width)
    assert console == []
    # The fold holds Basis disclosures (earlier-format chips, ruling H4), so its end is the first
    # </details> outside one.
    fold = (
        r'<details class="fold" id="reference"[^>]*>'
        r'((?:<details class="basis-fold".*?</details>|(?!</details>).)*)</details>'
    )
    found = re.search(fold, dom, re.DOTALL)
    assert found and re.search(r'<details class="fold" id="reference" open', dom)
    reference = found[1]
    assert "Debt structure" in reference and "Term loan" in reference
    assert "Call schedule" in reference
    # Row and page chips on the paragraph and the register.
    assert reference.count('class="chip') >= 4
    probe = Path(__file__).with_name("browser_probe_fits.js")
    (tmp_path / "library/probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page = tmp_path / "library/index.html"
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#CP-1/reference?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    # The fixture rows after Sources are audit; Debt structure is the one reference table.
    assert seen["pageFits"] is True and seen["tablesInCards"] is True and seen["tables"] == 1


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_overview_fits_and_has_no_module_navigator(tmp_path, width):
    page = report_library(tmp_path, cp0_confidence="Not assessable")
    (page.parent / "probe.js").write_text(OVERVIEW_PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#W-Overview?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    # Decision 6: no module navigator, Browse modules button or outline; the parts are H5's.
    assert seen["navigatorShown"] is False and seen["moduleToggleShown"] is False
    assert seen["outline"] == 0 and seen["fits"] is True
    assert seen["parts"] == [
        "overview-lead",
        "overview-bottom-lines",
        "overview-limitations",
        "overview-dates",
    ]
    # An earlier-format run has no passages (H7): no lead or bottom line; modules still listed.
    assert EARLIER_LEAD in seen["lead"]
    assert seen["bottomLines"][:2] == ["Source readiness Not assessable", "Financial foundation"]


# A handoff with all nine parts: prose under Findings (Analysis), the tables above (Reference), then
# Calculations and Gaps sections, inserted before Sources.
CALC_AND_GAPS = """
## Calculations

### Net debt trace

Net debt is 1,200 less 3,472, K, page:123 states the figure.

## Gaps

### Coverage gaps

Coupons are not supplied.
"""
SECTIONS_PROBE = Path(__file__).with_name("browser_probe_sections.js").read_text(encoding="utf-8")


def nine_part_library(tmp_path: Path) -> Path:
    digest = hashlib.sha256(SOURCE_PAGES).hexdigest()
    run = make_run(
        tmp_path,
        "run-a",
        as_of="2024-12-31",
        cp0_extra=inventory_text(digest),
        cp1_finding=CITED_FINDING,
        cp1_findings=CITED + REPORT_ROWS + UNKEYED + CALC_AND_GAPS,
    )
    (run / "source-text").mkdir()
    (run / "source-text" / SOURCE_NAME).write_bytes(SOURCE_PAGES)
    update_library.update_library(tmp_path)
    return tmp_path / "library/index.html"


# Names, not codes (owner ruling 2026-11-12: no module code is shown anywhere on screen): the module
# page with its audit section and the inspector open, the Evidence tab, Report history, Overview,
# Run activity and a search, read as a reader sees and hears them (text, title, aria-label). The
# module navigator is on every module page. Register references (C1, K) are not codes of this kind;
# `.excerpt` is the issuer's own quoted text. RUN is replaced by the run the probe reads.
CODES_PROBE = """(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms)), hits = [], kept = [];
  let inspected = 0;
  const code = /\\bCP-[A-Z0-9]+\\b|\\bT\\d+[A-Z]?(?:\\.\\d+)?\\b/;
  const scan = where => {
    const walker = document.createTreeWalker(
      document.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    while (walker.nextNode()) {
      const node = walker.currentNode, text = node.nodeType === 3;
      const seen = text
        ? [node.parentElement.closest('script,style,#probe,.excerpt') ? '' : node.data]
        : ['title', 'aria-label'].map(a => node.getAttribute(a) || '');
      for (const value of seen) {
        if (!code.test(value)) continue;
        if (code.test(stripStored(value))) hits.push(where + ': ' + value.slice(0, 80));
        else kept.push(where + ': ' + value.slice(0, 80));
      }
    }
  };
  for (let i = 0; i < 200 && !document.querySelector('.module-head'); i++) await sleep(50);
  // A stored source file name of the shown run is shown as stored: a value whose only
  // matches sit inside one is kept, not a hit.
  const evidence = (window.DESIGN_DATA.runs['RUN'] || {}).evidence || {};
  const stored = [
    ...(evidence.sources || []), ...(evidence.unused || []), ...(evidence.unrecorded || []),
  ]
    .map(f => f.name).filter(Boolean).sort((a, b) => b.length - a.length);
  const stripStored = value => stored.reduce((v, name) => v.split(name).join(''), value);
  // An earlier-format page opens its audit section from a button and its inspector from a chip; a
  // new-format page opens its inspector from a paragraph's figure or Basis control.
  const audit = document.querySelector('.audit-open');
  document.querySelectorAll('details:not([open])').forEach(d => {
    d.open = true;
    d.dispatchEvent(new Event('toggle'));
  });
  document.querySelectorAll('.audit-open').forEach(button => button.click());
  await sleep(150);
  scan('module page');
  const controls = [...document.querySelectorAll('#content [data-paragraph]')];
  if (!controls.length) controls.push(document.querySelector('.chip[data-evidence]'));
  for (const control of controls) {
    control.click();
    await sleep(150);
    inspected++;
    scan('inspector');
  }
  for (const route of ['#W-Evidence/sources?c=RUN', '#W-Report/history?c=RUN',
                       '#W-Overview/overview?c=RUN', '#W-Changes/changes?c=RUN',
                       '#CP-OS/activity']) {
    location.hash = route;
    await sleep(300);
    scan(route);
  }
  location.hash = 'START';
  await sleep(300);
  const search = document.getElementById('module-search');
  search.value = 'cp-1';
  search.dispatchEvent(new Event('input', { bubbles: true }));
  await sleep(200);
  scan('search');
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    hits,
    titled: document.querySelectorAll('a.module-item[title]').length,
    audit: !!audit,
    inspector: !!document.querySelector('.evidence-context'),
    searched: document.querySelectorAll('.search-hit').length,
    moduleCodes: document.querySelectorAll('.module-code').length,
    kept,
    inspected,
  });
  document.body.append(out);
})();"""


def read_codes_probe(page: Path, run: str, start: str) -> dict:
    script = CODES_PROBE.replace("RUN", run).replace("START", start)
    (page.parent / "probe.js").write_text(script, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, start)
    assert console == []
    return json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))


def test_no_module_code_or_step_id_reaches_a_reader_from_a_module_page(tmp_path):
    seen = read_codes_probe(nine_part_library(tmp_path), "run-a", "#CP-1/head?c=run-a")
    assert seen["audit"] is True
    assert seen["inspector"] is True and seen["titled"] == 0 and seen["searched"] > 0
    assert seen["moduleCodes"] == 0
    assert seen["hits"] == []


MEMO = "CP-2025-Info-Memo.pdf"  # an issuer file whose own name holds a CP- token


def adversarial_new_format_workspace(workspace: Path) -> None:
    """The synthetic new-format run with a supplied file named `CP-2025-Info-Memo.pdf`: a Sources
    row for it and a finding whose Basis is `CP-2025-Info-Memo.pdf, page 3; Liquidity (CP-2D)`."""
    fixtures = ROOT / "apps/issuer-library/fixtures"
    handoffs = workspace / "handoffs-in"
    shutil.copytree(fixtures / "synthetic-new-format", handoffs)
    cp2 = handoffs / "SYNTHETIC-CP-2.md"
    text = cp2.read_text(encoding="utf-8")
    row = "| NBG_2024-12-31_Q4-results.pdf | Earnings and quarterly cash. |\n"
    assert row in text and "\n### Contrary evidence" in text
    text = text.replace(row, row + f"| {MEMO} | Commercial paper programme terms. |\n")
    finding = (
        "- The commercial paper programme is capped at USD 250 million, which limits short-term"
        f" funding.\nBasis: {MEMO}, page 3; Liquidity (CP-2D)\n"
    )
    text = text.replace("\n### Contrary evidence", finding + "\n### Contrary evidence", 1)
    cp2.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(
        "build_synthetic_run", fixtures / "build_synthetic_run.py"
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.SOURCE_DIR = handoffs
    builder.SUPPLIED = (*builder.SUPPLIED, MEMO)
    builder.build(workspace, builder.DEFAULT_FOLDER)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "apps/issuer-library/update_library.py"),
            "--workspace",
            str(workspace),
        ],
        check=True,
        capture_output=True,
    )


def test_no_module_code_reaches_a_reader_from_a_new_format_run(tmp_path):
    """The synthetic new-format run (its own handoffs, Basis lines naming `Liquidity (CP-2D)`), with
    a supplied file whose name holds a code: the file name stays as stored, every module code
    is named."""
    adversarial_new_format_workspace(tmp_path)
    run = "synthetic-nbg-new-format-001"
    seen = read_codes_probe(tmp_path / "library/index.html", run, f"#CP-2?c={run}")
    assert seen["inspector"] is True and seen["titled"] == 0 and seen["searched"] > 0
    assert seen["moduleCodes"] == 0
    assert seen["hits"] == []
    assert seen["inspected"] >= 2
    for where in ("module page", "inspector"):
        assert any(k.startswith(where) and MEMO in k for k in seen["kept"]), (where, seen["kept"])


def line_of(tmp_path: Path, heading: str) -> int:
    handoff = next(tmp_path.glob("runs/run-a/deliveries/*/CP-1.md"))
    return handoff.read_text().splitlines().index(heading) + 1


def probe_route(page: Path, route: str, width: int = 1280) -> dict:
    (page.parent / "probe.js").write_text(SECTIONS_PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, route, width)
    assert console == []
    return json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_nine_part_module_page_has_no_horizontal_overflow(tmp_path, width):
    seen = probe_route(nine_part_library(tmp_path), "#CP-1/head?c=run-a", width)
    # Closed on arrival; the page fits with every fold open.
    assert seen["fits"] is True and seen["referenceOpen"] is False


def test_a_section_route_opens_the_reference_part_and_scrolls_to_it(tmp_path):
    page = nine_part_library(tmp_path)
    line = line_of(tmp_path, "### Cash table")
    seen = probe_route(page, f"#CP-1/s-{line}?c=run-a")
    assert seen["referenceOpen"] is True
    assert seen["target"] == {"found": True, "inReference": True, "topInside": True}
    assert seen["inspectorHidden"] is True


def test_a_row_route_into_the_reference_part_opens_it_and_escape_returns_to_the_row_chip(tmp_path):
    page = nine_part_library(tmp_path)
    row = line_of(tmp_path, "### Cash table") + 4  # The "Cash interest" row of the table.
    seen = probe_route(page, f"#CP-1/reference?c=run-a&e={row}")
    assert seen["referenceOpen"] is True and seen["inspectorHidden"] is False
    assert seen["escaped"]["hidden"] is True and seen["escaped"]["onChip"] is True
    assert seen["escaped"]["key"].endswith(f"CP-1.md:{row}")


def test_a_row_route_from_the_head_opens_the_fold_holding_the_row(tmp_path):
    page = nine_part_library(tmp_path)
    row = (
        line_of(tmp_path, "### Quoted findings") + 4
    )  # In Reference only; Key numbers does not draw it.
    # The section is the head, so only the trigger can open the closed Reference part.
    seen = probe_route(page, f"#CP-1/head?c=run-a&e={row}")
    assert seen["referenceOpen"] is True and seen["inspectorHidden"] is False


def test_chip_gaps_on_a_row_without_a_gap_opens_the_row_alone(tmp_path):
    page = nine_part_library(tmp_path)
    row = (
        line_of(tmp_path, "### Quoted findings") + 4
    )  # In Reference only; Key numbers does not draw it.
    seen = probe_route(page, f"#CP-1/head?c=run-a&e={row}&chip=gaps")
    assert seen["inspectorHidden"] is False
    assert seen["rowPressed"] == 1  # The row's own chip is pressed; no gap list was asked for.


def test_the_report_canvas_and_old_section_links(tmp_path):
    page = nine_part_library(tmp_path)
    dom, console = visit(page, "#CP-1/s54?c=run-a")  # A section id from before the report.
    assert console == []
    ids = re.findall(
        r'\bid="(head|bottom-line|numbers|findings|analysis|limits|reference|calculations|audit)"',
        dom,
    )
    assert ids == [
        "head",
        "bottom-line",
        "numbers",
        "findings",
        "analysis",
        "limits",
        "reference",
        "calculations",
        "audit",
    ]
    assert (
        "Candidate · not accepted" in dom and "Reader summary" in dom
    )  # The summary stays in the audit list.
    assert dom.count('<td><span class="na"') == 0  # No bare dash or empty cell.
    assert "n.a." in dom
    dom, console = visit(page, "#CP-1/findings?c=run-a")
    assert console == []
    assert re.search(r'aria-current="location"[^>]*>Findings<', dom)
    dom, console = visit(page, "#CP-0/head?c=run-a")
    assert console == []
    dom, console = visit(page, "#CP-1A/head?c=run-a")  # No CP-1A output in this run.
    assert console == []
    assert "No output found" in dom and "Not run in this run" not in dom


FORM_PROBE = """<script>
(() => {  // Its own scope: the form's script declares globals of its own.
document.querySelector('[data-k="pathway"][value="credit_snapshot"]').checked = true;
document.querySelector('[data-k="run_type"][value="secondary"]').checked = true;
document.getElementById('f').dispatchEvent(new Event('change', {bubbles: true}));
const radios = [...document.querySelectorAll('[data-k="pathway"]')];
const shown = radios.filter(x => !x.closest('label').hidden).map(x => x.value);
const out = document.createElement('pre');
out.id = 'probe';
const built = build();
const other = JSON.parse(JSON.stringify(built));
other.run.pathway = 'credit_snapshot';
const warned = fill(other).filter(w => w.startsWith('run.pathway'));
const same = fill(built).filter(w => w.startsWith('run.pathway'));
const disabled = radios.filter(x => x.disabled).length;
out.textContent = JSON.stringify({shown, disabled, built, warned, same});
document.body.append(out);
})();
</script>
</body>"""


CUTOFF_PROBE = """<script>
(() => {  // Its own scope: the form's script declares globals of its own.
const asOf = document.getElementById('d-as_of'), cut = document.getElementById('d-cutoff');
const type = (el, value) => {
  el.value = value;
  el.dispatchEvent(new Event('input', {bubbles: true}));
};
type(asOf, '2026-10-31');
const followed = build().run.cutoff;
type(cut, '2026-09-30');
type(asOf, '2026-11-05');
const kept = build().run.cutoff;
type(cut, '');
const cleared = build().run.cutoff;
const file = JSON.parse(JSON.stringify(build()));
file.run.as_of = '2026-08-31';
file.run.cutoff = '';
const notes = fill(file).filter(n => n.startsWith('run.cutoff'));
const loaded = build().run.cutoff;
const out = document.createElement('pre');
out.id = 'probe';
out.textContent = JSON.stringify({followed, kept, cleared, notes, loaded});
document.body.append(out);
})();
</script>
</body>"""


def test_the_research_cutoff_follows_the_as_of_date_and_is_written(tmp_path):
    # Session A, 2026-11-10: the modules read a blank cutoff in the pinned context as "information
    # cutoff not supplied". The code reads blank as the as-of date, so the form writes that date.
    page = tmp_path / "cutoff.html"
    text = (ROOT / "docs/templates/context-form.html").read_text(encoding="utf-8")
    page.write_text(text.replace("</body>", CUTOFF_PROBE, 1), encoding="utf-8")
    dom, console = visit(page)
    assert console == []
    probe = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert probe["followed"] == "2026-10-31"  # Follows the as-of date ...
    assert probe["kept"] == "2026-09-30"  # ... until the analyst sets an earlier one ...
    assert probe["cleared"] == "2026-11-05"  # ... and again once that is cleared.
    assert probe["loaded"] == "2026-08-31" and len(probe["notes"]) == 1  # A blank file says so.


SOURCES_PROBE = """<script>
(() => {  // Its own scope: the form's script declares globals of its own.
const pick = (attr, value) => {
  document.querySelector(`[${attr}][value="${value}"]`).checked = true;
  document.getElementById('f').dispatchEvent(new Event('change', {bubbles: true}));
};
const forecast = () => Object.fromEntries(readiness(build()).mods.map(m => [m.id, m]));
pick('data-k="pathway"', 'distressed_restructuring');
const peers = forecast();
const asked = [...document.querySelectorAll('[data-chk]')].map(c => c.dataset.chk);
pick('data-k="pathway"', 'earnings_update');
// No bridge file is chosen: the attachment is false, and the forecast says so.
const out = document.createElement('pre');
out.id = 'probe';
out.textContent = JSON.stringify({
  source: build().valuation.peer_source,
  asked,
  research: peers['CP-DR'],
  benchmark: peers['CP-1C'].status,
  nobridge: forecast()['CP-1D'].status,
});
document.body.append(out);
})();
</script>
</body>"""


def test_the_research_module_supplies_the_peers_and_the_bridge_is_forecast_as_run(tmp_path):
    # Owner, 2026-11-10: "Cp-dr supplies the peers, the user does not provide them unless they
    # specifically want to in the context file." So the form never asks for peers' filings, and the
    # research module's block in live run tdg-all-001 (no web-search grant in its ruling) is a note,
    # not the analyst's to fix. That run's Earnings quality came back Restricted with no bridge.
    page = tmp_path / "sources.html"
    text = (ROOT / "docs/templates/context-form.html").read_text(encoding="utf-8")
    page.write_text(text.replace("</body>", SOURCES_PROBE, 1), encoding="utf-8")
    dom, console = visit(page)
    assert console == []
    probe = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert probe["source"] == "cp_dr_public"  # The research module finds the peers by default ...
    assert probe["asked"] and not any("peer" in item for item in probe["asked"])  # ... unasked.
    research = probe["research"]
    assert research["status"] == "information" and len(research["items"]) == 1
    assert "web-search" in research["items"][0]["reason"]  # The ruling's grant, not the analyst's.
    assert probe["benchmark"] == "ready"
    assert probe["nobridge"] == "limited"


def test_a_copy_of_the_page_marked_with_a_pathway_no_longer_fixes_it(tmp_path):
    # The folder watcher once wrote such a copy into each inbox folder; the page's mark is ignored.
    marked = (ROOT / "docs/templates/context-form.html").read_text(encoding="utf-8")
    assert marked.count('<html lang="en">') == 1
    marked = marked.replace('<html lang="en">', '<html lang="en" data-pathway="earnings_update">')
    page = (
        tmp_path / "probe.html"
    )  # The form with a probe that tries another pathway and run type, then reads.
    page.write_text(marked.replace("</body>", FORM_PROBE, 1), encoding="utf-8")
    dom, console = visit(page)
    assert console == []
    probe = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    # The page is served by the start service, not opened from a folder: the copy's
    # data-pathway mark is ignored, every pathway is offered and none is disabled.
    assert len(probe["shown"]) == 7 and probe["disabled"] == 0  # the six and the short snapshot
    assert probe["built"]["run"]["pathway"] == "credit_snapshot"  # The probe's own choice held ...
    # The probe's event targets the form, not the radio, so the run type stays at the
    # pathway's default (research for Credit Snapshot).
    assert probe["built"]["run"]["run_type"] == "research"
    assert probe["warned"] == []  # A loaded context naming another pathway is not replaced.
    assert probe["same"] == []


@pytest.mark.parametrize("width", [1440, 1280])
def test_a_liquidity_bridge_is_a_waterfall_with_its_table_form_and_fits_the_page(tmp_path, width):
    make_run(tmp_path, "run-a", as_of="2024-12-31", cp1_extra=CHARTS + BRIDGE)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    probe = Path(__file__).with_name("browser_probe_bridge.js")
    (page.parent / "probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#CP-1/performance?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert seen["title"] == "Liquidity bridge"
    assert (seen["points"], seen["totals"], seen["outflows"]) == (4, 2, 1)
    assert seen["barsInside"] is True and seen["fits"] is True
    assert seen["formRows"] == 4 and seen["formHidden"] is True  # Present for a reader, closed.


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_credit_structure_views_are_drawn_with_their_table_forms_and_fit_the_page(
    tmp_path, width
):
    make_run(tmp_path, "run-a", as_of="2024-12-31", cp1_extra=CHARTS + STRUCTURE)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    probe = Path(__file__).with_name("browser_probe_structure.js")
    (page.parent / "probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#CP-1/performance?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert (seen["segments"], seen["bulletRows"], seen["limitRows"]) == (2, 2, 1)
    assert (seen["markers"], seen["ticks"]) == (1, 3)  # No marker for the current value not stated.
    assert seen["forms"] >= 9 and seen["formsClosed"] is True and seen["fits"] is True
    assert (seen["dumbbells"], seen["bands"], seen["scatterDots"]) == (2, 1, 2)
    assert (seen["recoveryGroups"], seen["recoveryBars"]) == (
        2,
        2,
    )  # No bar for a value not stated.


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_overview_lists_the_nearest_dates_instead_of_drawing_lanes_and_fits_the_page(
    tmp_path, width
):
    make_run(tmp_path, "run-a", as_of="2025-03-31", cp1_extra=CHARTS + EVENTS)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    probe = Path(__file__).with_name("browser_probe_overview.js")
    (page.parent / "probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    # The Calendar tab is retired (decision 12) and the Overview draws no lane (H5): it lists the
    # dated items on or after the as-of date in one list, five at most (M2, H5.5): day-dated and
    # period-dated items share one ordering, by the day or the period end, nearest first.
    dom, console = visit(page, "#W-Overview?c=run-a", width)
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert console == [] and seen["fits"] is True
    assert seen["dates"] == [
        "2025-03-31Synthetic noteFinancial foundation",
        "2025-06Synthetic callFinancial foundation",
        "2025-Q3Synthetic reviewFinancial foundation",
        "2025Synthetic maturity yearFinancial foundation",
    ]
    assert "Dated to a month, quarter or year" not in dom
    assert "event-lanes" not in dom and "W-Calendar" not in dom


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_map_with_its_table_is_drawn_and_fits_the_page_and_no_status_map_remains(
    tmp_path, width
):
    make_run(tmp_path, "run-a", as_of="2025-12-31", cp1_extra=CHARTS + MAPS)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    probe = Path(__file__).with_name("browser_probe_maps.js")
    (page.parent / "probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    # The map is drawn by its owning module (the catalogue places no CP-1 map on the Overview) ...
    dom, console = visit(page, "#CP-1/maps?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert (seen["nodes"], seen["edges"], seen["labels"], seen["tableRows"]) == (11, 12, 12, 12)
    assert seen["wide"] is True and seen["scrolls"] is True  # Natural width, scrolled in its card.
    assert seen["scrollFocusable"] is True and seen["fits"] is True
    assert seen["tableAfterDiagram"] is True and seen["cutEdges"] == 1
    # ... the status map is retired with the old Evidence content (decision 9); neither the
    # Evidence page nor the Overview draws a map.
    dom, console = visit(page, "#W-Evidence/sources?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert seen["statusNodes"] == 0 and seen["statusItems"] == 0 and seen["fits"] is True
    assert "status-map" not in dom and "map-card" not in dom
    dom, console = visit(page, "#W-Overview?c=run-a", width)
    assert console == [] and "map-card" not in dom and "status-map" not in dom


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_run_label_and_the_chart_index_keep_the_run_and_fit_the_page(tmp_path, width):
    # Long names: a 38-character issuer and 80-character run folders.
    long = "cpos-tdg-copilot-sol-medium-revision-with-a-very-long-folder-name-0000000000000001"
    issuer = "Synthetic Holding Company Incorporated Ltd"
    make_run(
        tmp_path, long, as_of="2025-12-31", issuer_name=issuer, cp1_extra=CHARTS + EVENTS + MAPS
    )
    make_run(tmp_path, f"{long}-other", as_of="2025-06-30", issuer_name=issuer)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    probe = Path(__file__).with_name("browser_probe_index.js")
    (page.parent / "probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    for route in (f"#W-Overview?c={long}", f"#W-Forecast?c={long}"):
        dom, console = visit(page, route, width)
        assert console == []
        seen = json.loads(
            html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1])
        )
        # One line under the tabs: the run's date, pathway and code, and the way to the history.
        assert seen["shown"] is True
        assert seen["text"].startswith("Showing run: 31 December 2025 · Credit snapshot · ")
        assert long.upper() in seen["text"]
        assert seen["historyText"] == "All runs of this issuer" and seen["popovers"] == 0
        assert seen["tabs"] == ["Report", "Overview", "Changes", "Modules", "Forecast", "Evidence"]
        assert seen["current"] == [route.split("?")[0][3:]]
        # The chart index is the Forecast page's; the Overview selects passages instead.
        assert seen["indexRows"] == (
            []
            if "Overview" in route
            else [
                "Leverage|Drawn",
                "Interest cover|Drawn",
                "Liquidity|Drawn",
                "Financing events|Drawn",
                "Credit-risk transmission map|Drawn",
            ]
        )
        assert seen["indexScrollFocusable"] is ("Forecast" in route) and seen["fits"] is True
        # The link opens the issuer's Report history under the same run; the label is hidden there.
        assert seen["after"] == f"#W-Report/history?c={long}"
        assert seen["barOnHistory"] is True and seen["historyFits"] is True
        assert [row.split("|")[1] for row in seen["historyRows"]] == ["true", "null"]
        assert seen["historyRows"][0].startswith("31 December 2025")
        assert seen["historyRows"][1].startswith("30 June 2025")


INSPECTOR_PROBE = Path(__file__).with_name("browser_probe_inspector.js").read_text(encoding="utf-8")
# Hand-counted from SYNTHETIC-CP-2.md: Basis items per paragraph line (the file's own lines).
CP2_BASIS_ITEMS_BY_PARAGRAPH = 7  # paragraphs with a Basis line
CP2_BASIS_ITEMS = 10


def test_the_inspector_draws_every_basis_item_of_every_paragraph_as_the_handoff_has_it(tmp_path):
    """Reads the inspector the reader sees, not the control's data-basis: the answer key is the
    handoff's own Basis lines (parsed here from the Markdown), item by item and in order."""
    fixtures = ROOT / "apps/issuer-library/fixtures"
    subprocess.run(
        [
            sys.executable,
            str(fixtures / "build_synthetic_run.py"),
            "--workspace",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
    )
    # The synthetic run's page is built by the real entry point and method, not the stand-in.
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "apps/issuer-library/update_library.py"),
            "--workspace",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
    )
    page = tmp_path / "library/index.html"
    (page.parent / "probe.js").write_text(INSPECTOR_PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#CP-2?c=synthetic-nbg-new-format-001")
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert seen, "no paragraph control on the CP-2 page"

    lines = (
        (fixtures / "synthetic-new-format/SYNTHETIC-CP-2.md")
        .read_text(encoding="utf-8")
        .split("\n")
    )
    k1 = next(line for line in lines if line.startswith("| K1 |"))
    k1_cells = [c.strip() for c in k1.strip("|").split("|")]
    k1_headers = ["ID", "Calculation", "Steps", "Result"]  # the Calculations table's header row
    assert (
        next(line for line in lines if line.startswith("| ID |")).strip("|").split("|")[0].strip()
        == "ID"
    )

    by_line: dict[int, list[str]] = {}
    for number, line in enumerate(lines, start=1):
        if line.startswith("Basis: "):
            by_line[number - 1] = [
                i.strip() for i in line.removeprefix("Basis: ").removesuffix(".").split("; ")
            ]
    assert len(by_line) == CP2_BASIS_ITEMS_BY_PARAGRAPH
    assert sum(len(v) for v in by_line.values()) == CP2_BASIS_ITEMS
    ran = {"CP-0", "CP-1", "CP-1A", "CP-2", "CP-2D"}

    drawn_lines = set()
    for record in seen:
        assert record["hidden"] is False, record
        line = int(record["key"].rsplit(":", 1)[1])
        # Each paragraph here is one line then its Basis line; the key's line is the paragraph's.
        want = by_line.get(line)
        if want is None:
            continue
        drawn_lines.add(line)
        got = record["items"]
        assert len(got) == len(want), (record["key"], [g["text"][:50] for g in got], want)
        for item, drawn in zip(want, got, strict=True):
            if item.startswith("calculation "):
                assert drawn["cells"] == [
                    x for pair in zip(k1_headers, k1_cells, strict=True) for x in pair
                ], drawn
            elif m := re.fullmatch(r"(.+) \((CP-[A-Z0-9]+)\)", item):
                # The handoff's `Name (code)` item is drawn as its written name only (R5).
                assert drawn["text"].startswith(m[1]) and m[2] not in drawn["text"], drawn
                assert bool(drawn["links"]) == (m[2] in ran), drawn
                assert ("Not run in this run" in drawn["text"]) == (m[2] not in ran)
            else:
                file, _, pages = item.partition(", page")
                assert drawn["text"].startswith(file), (item, drawn["text"])
                if pages:
                    assert f"page{pages}" in drawn["text"], (item, drawn["text"])
    assert len(drawn_lines) == CP2_BASIS_ITEMS_BY_PARAGRAPH
    assert console == []


NARROW_PROBE = (
    Path(__file__).with_name("browser_probe_narrow_tables.js").read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    ("route", "tables"),
    [
        ("#W-Overview?c=synthetic-nbg-new-format-001", 1),
        ("#W-Evidence?c=synthetic-nbg-new-format-001", 4),
    ],
)
def test_wide_tables_scroll_in_their_own_region_on_a_narrow_page(tmp_path, route, tables):
    """W1: the Overview nearest dates and the Evidence tables do not widen a phone-width page."""
    for script, args in (("fixtures/build_synthetic_run.py", []), ("update_library.py", [])):
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "apps/issuer-library" / script),
                "--workspace",
                str(tmp_path),
            ],
            check=True,
            capture_output=True,
        )
    page = tmp_path / "library/index.html"
    (page.parent / "probe.js").write_text(NARROW_PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, route, 500)
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert console == []
    assert seen["pageFits"] is True
    assert seen["tables"] == seen["inRegion"] == tables
    assert seen["scrolling"] >= 1


def test_evidence_keeps_file_names_as_stored_and_says_when_no_supplied_file_is_recorded(tmp_path):
    """R6: the Hashes table labels a module-named file by its module's name (the hash stays); a run
    record with no supplied-file list does not claim every supplied file was used."""
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    dom, console = visit(tmp_path / "library/index.html", "#W-Evidence/sources?c=run-a")
    assert console == []
    cells = re.findall(r"<td>([^<]*instructions)</td>", dom)
    assert cells == ["Source readiness instructions", "Financial foundation instructions"]
    assert "The run record lists no supplied files." in dom
    assert "Every supplied file is named" not in dom
    # Each handoff and instruction link stays inside library/, where the served page can open it.
    assert 'href="downloads/run-a/CP-0.md" download' in dom
    assert 'href="downloads/run-a/instructions/CP-0.md" download' in dom


def served_dom(root: Path, route: str, width: int = 1280) -> str:
    """The DOM Chrome builds for a page of the library when a local web server serves it."""
    import functools
    import http.server
    import threading

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):  # the request log is noise here
            return

    handler = functools.partial(Quiet, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        done = subprocess.run(
            [
                chrome(),
                "--headless=new",
                "--disable-gpu",
                f"--window-size={width},900",
                "--virtual-time-budget=10000",
                "--dump-dom",
                f"http://127.0.0.1:{server.server_address[1]}/library/index.html{route}",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
    finally:
        server.shutdown()
        server.server_close()
    return html.unescape(done.stdout)


START_RUN_PROBE = Path(__file__).with_name("browser_probe_start_run.js").read_text(encoding="utf-8")
RUN_ROUTES = ["#W-Report/history?c=run-a", "#W-Overview?c=run-a", "#CP-1/head?c=run-a"]


@pytest.mark.parametrize("width", [1440, 600])
@pytest.mark.parametrize("route", RUN_ROUTES)
def test_the_run_header_starts_a_run_on_this_issuer_when_served(tmp_path, route, width):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_served_probe(tmp_path / "library/index.html", route, width, START_RUN_PROBE)
    # One link, in the header (not in the page body), the one the history page used to draw.
    assert (seen["inHeader"], seen["inDocument"], seen["inContent"]) == (1, 1, 0)
    assert seen["text"] == "Start a run on this issuer" and seen["href"] == "/?from=run-a"
    assert seen["cls"] == "start-run primary-action" and seen["icons"] == 1
    # It never overlaps the title and the page does not scroll sideways.
    assert seen["overlapsTitle"] is False and seen["fits"] is True, seen
    if width == 600:
        # On a phone it is a full row under the title.
        assert seen["belowTitle"] is True and abs(seen["linkWidth"] - seen["rowWidth"]) <= 1, seen


@pytest.mark.parametrize("route", RUN_ROUTES)
def test_the_run_header_has_no_start_link_from_a_file(tmp_path, route):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_probe(tmp_path / "library/index.html", route, 1280, START_RUN_PROBE)
    assert seen["inAnyFormOfTheClass"] is False and seen["inDocument"] == 0 and seen["fits"] is True
    if route.startswith("#W-Report/history"):
        # `#content .history-table`: the table is still drawn without the link.
        assert seen["historyTable"] == 1, seen


SCOPE_PROBE = Path(__file__).with_name("browser_probe_header_scope.js").read_text(encoding="utf-8")
# The run header's height at commit 1f1691c (no start link, no `.issuer-side`) for this file's
# fixture (`make_run(..., as_of="2024-12-31")`, route #CP-1/head?c=run-a), measured by running
# this test's probe on `git archive 1f1691c`: 113.140625px at both widths.
BASE_HEADER_HEIGHT = {1440: 113.14, 1280: 113.14}


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_run_header_is_unchanged_from_a_file_and_as_of_stays_on_one_line(tmp_path, width):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_probe(tmp_path / "library/index.html", "#CP-1/head?c=run-a", width, SCOPE_PROBE)
    assert seen["sideCount"] == 0, seen
    assert seen["scopeHeight"] <= 24, seen
    assert abs(seen["headerHeight"] - BASE_HEADER_HEIGHT[width]) <= 0.5, seen


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_run_header_keeps_as_of_on_one_line_beside_the_start_link_when_served(tmp_path, width):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_served_probe(
        tmp_path / "library/index.html", "#CP-1/head?c=run-a", width, SCOPE_PROBE
    )
    assert seen["scopeHeight"] <= 24, seen  # one line
    assert seen["iconGap"] <= 12, seen  # the calendar icon sits against the text
    assert seen["scopeOverlapsTitle"] is False and seen["linkOverlapsTitle"] is False, seen
    assert seen["fits"] is True, seen
    if width == 1440:
        assert seen["sameRow"] <= 12, seen  # the block and the link share a row


def inject_probe(page: Path, script: str, config=None) -> None:
    """Add `script` to the built page; it reads `window.PROBE` (the `config`) and writes its JSON
    to <pre id="probe">."""
    (page.parent / "probe-config.js").write_text(
        "window.PROBE=" + json.dumps(config or {}) + ";", encoding="utf-8"
    )
    (page.parent / "probe.js").write_text(script, encoding="utf-8")
    tags = '<script src="probe-config.js"></script><script src="probe.js"></script>'
    page.write_text(page.read_text().replace("</body>", tags + "</body>"))


def probe_json(dom: str) -> dict:
    return json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))


def read_probe(page: Path, route: str, width: int, script: str, config=None) -> dict:
    """Load `route` of the built page at `width` from disk with `script` injected; the console
    must be clean. Returns the JSON the script wrote."""
    inject_probe(page, script, config)
    dom, console = visit(page, route, width)
    assert console == []
    return probe_json(dom)


def read_served_probe(page: Path, route: str, width: int, script: str) -> dict:
    """The same over a local web server (the library is then "served over http")."""
    inject_probe(page, script)
    return probe_json(served_dom(page.parent.parent, route, width))


CHROME_PROBE = Path(__file__).with_name("browser_probe_chrome.js").read_text(encoding="utf-8")


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_run_chrome_navigator_and_columns_take_the_redesign_measures(tmp_path, width):
    seen = read_probe(report_library(tmp_path), "#CP-1/head?c=run-a", width, CHROME_PROBE)
    assert seen["width"] == width
    # The header: the way back to the library, the title at 24px, no run chip or Change run.
    assert seen["back"] == {"text": "Issuer library", "href": "#W-Library/cases"}
    assert "Change run" not in seen["headerText"] and seen["headerCodes"] == 0
    assert seen["h1Size"] == "24px"
    # The fixture issuer has a ticker (the catalogue's issuer field), no sector, and one run.
    assert seen["meta"] == "NBG · 1 run"
    # The tabs are text only, in the same six names and order as before.
    assert [t["text"] for t in seen["tabs"]] == [
        "Report",
        "Overview",
        "Changes",
        "Modules",
        "Forecast",
        "Evidence",
    ]
    assert [t["art"] for t in seen["tabs"]] == [0] * 6
    # The navigator: 250px (220px at 1280), uppercase 11px group headings, the open entry in blue.
    assert abs(seen["navWidth"] - (250 if width == 1440 else 220)) <= 1
    assert (seen["headingTransform"], seen["headingSize"]) == ("uppercase", "11px")
    assert (seen["itemBackground"], seen["itemWeight"]) == ("rgb(229, 232, 255)", "600")
    # The strip: the link to every run of the issuer at the right edge; the run code as stored.
    assert seen["allText"] == "All runs of this issuer" and 0 <= seen["allGap"] <= 30
    assert seen["codeTransform"] == "none" and seen["codeText"] == "RUN-A"
    assert seen["fits"] is True and seen["fitsOpen"] is True
    # The inspector: 340px at 1440, 300px at 1280.
    assert abs(seen["inspectorWidth"] - (340 if width == 1440 else 300)) <= 1


MODULE_PAGE_PROBE = (
    Path(__file__).with_name("browser_probe_module_page.js").read_text(encoding="utf-8")
)
INK = "rgb(0, 5, 51)"  # --text-primary
NEW_FORMAT_RUN = "synthetic-nbg-new-format-001"


def read_module_page(page: Path, route: str, width: int = 1440) -> dict:
    return read_probe(page, route, width, MODULE_PAGE_PROBE)


def synthetic_workspace(workspace: Path, edit=lambda text: text) -> Path:
    """The synthetic new-format run, built by the real entry points; `edit` may change the CP-2
    handoff first."""
    fixtures = ROOT / "apps/issuer-library/fixtures"
    handoffs = workspace / "handoffs-in"
    shutil.copytree(fixtures / "synthetic-new-format", handoffs)
    cp2 = handoffs / "SYNTHETIC-CP-2.md"
    cp2.write_text(edit(cp2.read_text(encoding="utf-8")), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(
        "build_synthetic_run", fixtures / "build_synthetic_run.py"
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.SOURCE_DIR = handoffs
    builder.build(workspace, builder.DEFAULT_FOLDER)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "apps/issuer-library/update_library.py"),
            "--workspace",
            str(workspace),
        ],
        check=True,
        capture_output=True,
    )
    return workspace / "library/index.html"


def with_chart_and_event(text: str) -> str:
    """The synthetic CP-2 handoff with one placed chart and dated events, before its last part."""
    marker = "\n## Next module"
    assert marker in text
    return text.replace(marker, MATURITIES + EVENTS + marker, 1)


def test_the_earlier_format_module_page_takes_the_redesign_layout(tmp_path):
    seen = read_module_page(nine_part_library(tmp_path), "#CP-1/head?c=run-a")
    delivery = next((tmp_path / "runs/run-a/deliveries").iterdir()).name
    # Head: the group is the eyebrow with the name, tools kept, the Handoff link quiet.
    head = seen["head"]
    assert head["h2"] == "Financial foundation"
    assert (head["size"], head["transform"]) == ("12px", "uppercase")
    assert "Financial performance" in head["text"] and "has-bottom-line" in head["cls"]
    assert head["download"]["href"].endswith("CP-1.md") and head["download"]["icon"] == 1
    assert head["download"]["border"] == "0px"
    assert head["toolsRight"] <= head["headRight"]
    # Bottom line: the quoted text is the headline, no navy band.
    bottom = seen["bottom"]
    assert bottom["firstText"] == "Financial foundation bottom line."
    assert (bottom["first"]["size"], bottom["first"]["color"]) == ("22px", INK)
    assert bottom["bg"] in ("rgba(0, 0, 0, 0)", "rgb(255, 255, 255)")
    for word in ("Confidence", "Main limitation", "Quoted from the handoff", "View source"):
        assert word in bottom["text"], word
    for line in bottom["lines"]:
        assert (line["size"], line["line"], line["color"], line["label"]) == (
            "13px",
            "18px",
            "rgb(56, 59, 63)",
            "600",
        )
    assert bottom["badgeClass"] == "badge badge-gray" and bottom["linkBorder"] == "0px"
    # Prose, charts, folds.
    assert (seen["prose"]["size"], seen["prose"]["line"]) == ("15px", "24px")
    assert seen["prose"]["width"] <= 660
    assert seen["cards"] and all(not c["closed"] and c["height"] > 40 for c in seen["cards"])
    folds = {f["id"]: f for f in seen["folds"]}
    assert set(folds) == {"reference", "calculations", "audit"}
    for fold in folds.values():
        assert (fold["display"], fold["radius"]) == ("flex", "10px"), fold
    assert folds["reference"]["children"] == ["Statements and registers", "3 tables · 8 rows"]
    assert folds["calculations"]["children"] == ["Calculations", "11 words"]
    assert folds["audit"]["children"][0] == "Evidence & audit"
    assert folds["audit"]["text"].endswith("14 sections · unchanged from the handoff")
    # The finding: one item, no pill, the same Basis control.
    [finding] = seen["findings"]
    assert finding["pills"] == 0
    for word in (
        "Interest was paid in cash.",
        "Creditor impact",
        "K, page:123 says “Cash paid during the period”.",
        "Confidence High",
    ):
        assert word in finding["text"], word
    # The Basis control carries the same data-* attributes as before the redesign (commit 4b88927).
    assert finding["basis"] == [
        {
            "paragraph": (f"run-a/deliveries/{delivery}/CP-1.md:16"),
            "basis": "[]",
        }
    ]
    lead = seen["finding0"]
    assert (lead["size"], lead["line"], lead["weight"]) == ("15px", "24px", "600")
    assert (lead["dotWidth"], lead["dotBg"], lead["border"]) == ("6px", "rgb(0, 26, 255)", "0px")
    assert (lead["impact"]["size"], lead["impact"]["line"]) == ("14px", "21px")
    # Limits: grey dot, 14px/21px secondary.
    limit = seen["limit"]
    assert (limit["size"], limit["line"], limit["color"], limit["dotWidth"]) == (
        "14px",
        "21px",
        "rgb(56, 59, 63)",
        "6px",
    )
    assert seen["fits"] is True


def test_a_module_page_with_no_bottom_line_draws_its_name_as_the_headline(tmp_path):
    run = make_run(
        tmp_path,
        "run-a",
        as_of="2024-12-31",
        modules=("CP-0", "CP-1", "CP-8"),
        cp8=(
            "# CP-8 handoff\n\n## Request\nChanges.\n\n"
            "## Findings\n\nA note.\n\n## Sources\n- fixture\n"
        ),
    )
    assert run.is_dir()
    update_library.update_library(tmp_path)
    seen = read_module_page(tmp_path / "library/index.html", "#CP-8/head?c=run-a")
    head = seen["head"]
    assert "bottom" not in seen and "has-bottom-line" not in head["cls"]
    assert (head["size"], head["transform"]) == ("22px", "none")
    assert "Decision and review" in head["text"] and head["h2"] == "Changes since the last run"


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_new_format_module_page_and_its_inspector_take_the_redesign_layout(tmp_path, width):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    seen = read_module_page(page, f"#CP-2?c={NEW_FORMAT_RUN}", width)
    head = seen["head"]
    assert (head["h2"], head["size"], head["transform"]) == (
        "Fundamental credit",
        "12px",
        "uppercase",
    )
    bottom = seen["bottom"]
    [hidden] = [h for h in bottom["headings"] if h["text"] == "Bottom line"]
    assert "sr-only" in hidden["cls"] and hidden["srOnly"] is True
    assert bottom["firstText"].startswith("Creditors are exposed to refinancing risk")
    assert (bottom["first"]["size"], bottom["first"]["color"]) == ("22px", INK)
    assert seen["keyItem"]["size"] == "15px"
    assert (seen["keyItem"]["dotWidth"], seen["keyItem"]["dotBg"]) == ("6px", "rgb(0, 26, 255)")
    assert (seen["prose"]["size"], seen["prose"]["line"]) == ("15px", "24px")
    assert seen["prose"]["width"] <= 660
    assert seen["cards"], "the new-format module page draws at least one chart card"
    assert all(not c["closed"] and c["height"] > 40 for c in seen["cards"])
    assert seen["fits"] is True
    # Limitations: grey dot list.
    assert (seen["limit"]["dotWidth"], seen["limit"]["size"]) == ("6px", "14px")
    # The inspector opened from a figure: the figure leads, large, before the context line.
    fig = seen["fromFigure"]
    assert fig["figure"]["size"] == "22px" and fig["figure"]["before"] is True
    assert fig["figure"]["text"] == "USD 1,390 million" and fig["h2"]["srOnly"] is True
    assert fig["card"] == "10px" and fig["fits"] is True
    assert fig["context"]["size"] == "13px" and fig["context"]["color"] == "rgb(56, 59, 63)"
    for literal in (
        "Back to analysis",
        "Esc",
        "Evidence inspector",
        "Fundamental credit · Line 17",
        "Bottom line",
        "Not classified",
        "Paragraph",
        (
            "Creditors are exposed to refinancing risk rather than to weak earnings: "
            "net debt of USD 1,390 million is 4.2x earnings, and the next maturities "
            "fall inside two years."
        ),
        "Figure",
        "USD 1,390 million",
        "Basis",
        "NBG_2025-03-31_annual-report.pdf, page 41",
        "Calculation K1",
        "Net debt to EBITDA",
        "Gross debt 1,700 less cash 310 gives net debt 1,390; divided by EBITDA 331",
        "4.2x",
        "Other citations",
        "Citation gap · NBG_2025-03-31_annual-report.pdf p.41 · not in inventory",
        "the Basis file is not in the Source readiness inventory",
        "Source location",
        "Download retained handoff",
        "Fundamental credit handoff",
        "Northbridge Synthetic Group · SYNTHETIC-NBG-NEW-FORMAT-001 · saved output",
        "Reading boundary",
        "The library does not authenticate the underlying PDFs.",
    ):
        assert literal in fig["text"], literal
    assert len(fig["links"]) == 1 and fig["links"][0].endswith("CP-2.md")
    # Opened from a Basis control: no figure; the eyebrow is the drawn "Evidence inspector".
    chip = seen["fromChip"]
    assert chip["hasFigure"] is False and chip["h2"]["srOnly"] is False
    assert chip["card"] == "10px" and chip["fits"] is True
    for literal in (
        "Back to analysis",
        "Esc",
        "Evidence inspector",
        "Fundamental credit · Line 26",
        "Key findings",
        (
            "Liquidity support rests on an undrawn revolver that steps down, "
            "which narrows the cushion over time."
        ),
        "NBG_2024-12-31_Q4-results.pdf, page 7",
        "Citation gap · NBG_2024-12-31_Q4-results.pdf p.7 · not in inventory",
        "Source location",
        "Download retained handoff",
        "Reading boundary",
    ):
        assert literal in chip["text"], literal


def test_a_two_paragraph_bottom_line_draws_both_in_the_headline_style(tmp_path):
    second = "A second paragraph: the covenant package is untested.\n"

    def edit(text: str) -> str:
        marker = "\n### Key findings"
        assert marker in text
        return text.replace(marker, "\n" + second + marker, 1)

    seen = read_module_page(synthetic_workspace(tmp_path, edit), f"#CP-2?c={NEW_FORMAT_RUN}")
    paragraphs = seen["bottom"]["ps"]
    assert len(paragraphs) == 2 and paragraphs[1]["text"] == second.strip()
    assert [p["size"] for p in paragraphs] == ["22px", "22px"]


NARROW_HEADER_PROBE = """(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('header.issuer h1'); i++) await sleep(50);
  await sleep(200);
  const header = document.querySelector('header.issuer');
  const h1 = header.querySelector('h1'), scope = header.querySelector('.scope');
  const cs = getComputedStyle(header);
  const seen = {padL: cs.paddingLeft, padT: cs.paddingTop,
    scopeBelowTitle: scope.getBoundingClientRect().top >= h1.getBoundingClientRect().bottom - 1};
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();"""


def test_the_run_header_keeps_the_phone_layout_at_600px(tmp_path):
    seen = read_probe(report_library(tmp_path), "#CP-1/head?c=run-a", 600, NARROW_HEADER_PROBE)
    assert (seen["padL"], seen["padT"], seen["scopeBelowTitle"]) == ("15px", "12px", True)


INSPECTOR_PADDING_PROBE = """(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('#content .basis-link'); i++) await sleep(50);
  document.querySelector('#content .basis-link:not([data-figure])').click();
  await sleep(300);
  const body = document.querySelector('.inspector-body');
  const ctx = body.querySelector('.evidence-context');
  const seen = {padding: getComputedStyle(body).padding,
    contextBottom: getComputedStyle(ctx).marginBottom};
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();"""


@pytest.mark.parametrize(
    ("width", "padding", "context_bottom"),
    [(1000, "24px", "14px"), (600, "18px 15px", None)],
)
def test_the_inspector_keeps_its_small_screen_padding(tmp_path, width, padding, context_bottom):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    seen = read_probe(page, f"#CP-2?c={NEW_FORMAT_RUN}", width, INSPECTOR_PADDING_PROBE)
    assert seen["padding"] == padding
    if context_bottom:
        assert seen["contextBottom"] == context_bottom


FIELD_CARD_PROBE = (
    Path(__file__).with_name("browser_probe_field_card.js").read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    ("width", "route"),
    [(1000, "#W-Overview?c={}"), (760, "#W-Overview?c={}"), (1000, "#CP-2?c={}")],
)
def test_the_inspector_field_card_keeps_its_small_screen_look(tmp_path, width, route):
    """At 1050px and below the inspector's fields are rows as before the redesign (padding 12px 0,
    no card border, a 160px label column); the card is for wider windows."""
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    seen = read_probe(page, route.format(NEW_FORMAT_RUN), width, FIELD_CARD_PROBE)
    assert (seen["padding"], seen["borderLeft"], seen["columns"]) == ("12px 0px", "0px", "160px")
    # The value column is what is left of the body after the 160px label column and the 18px gap:
    # the card adds no padding or border of its own (measured at fe3dd7d: 54px and 474px at 1000px).
    assert abs(seen["valueWidth"] - (seen["bodyContent"] - 160 - 18)) <= 1, seen


OVERVIEW_STYLE_PROBE = (
    Path(__file__).with_name("browser_probe_overview_style.js").read_text(encoding="utf-8")
)


def test_the_overview_draws_figure_links_and_basis_controls_like_the_module_page(tmp_path):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    where = {
        "module": ("CP-2", "#key-findings"),
        "overview": ("W-Overview", "#overview-lead .reading-findings"),
    }
    read = {
        name: read_probe(
            page,
            f"#{route}?c={NEW_FORMAT_RUN}",
            1440,
            OVERVIEW_STYLE_PROBE,
            {"figure": f"{scope} .figure", "basis": f"{scope} .basis-link:not(.figure)"},
        )
        for name, (route, scope) in where.items()
    }
    for name, seen in read.items():
        assert "Red Hat Mono" in seen["figure"]["family"], (name, seen)
        assert seen["basis"]["size"] == "13px", (name, seen)
    assert read["overview"] == read["module"]


EDGES_PROBE = Path(__file__).with_name("browser_probe_edges.js").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "route",
    [
        "#W-Report/history?c=run-a",
        "#W-Changes/changes?c=run-a",
        "#W-Forecast/none?c=run-a",
        "#W-Evidence/sources?c=run-a",
    ],
)
def test_the_body_of_a_run_tools_page_shares_both_edges_with_the_header(tmp_path, route):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_probe(tmp_path / "library/index.html", route, 1440, EDGES_PROBE)
    assert seen["fits"] is True
    for part in ("content", "head", "browse"):
        if part in seen:
            assert abs(seen[part]["left"] - seen["h1Left"]) <= 1, (part, seen)
    for part in ("content", "head"):
        if part in seen:
            assert abs(seen[part]["right"] - seen["headerRight"]) <= 1, (part, seen)
    # The Browse modules button is as wide as its label: its padding is the 28px, both sides.
    assert (seen["browse"]["paddingLeft"], seen["browse"]["paddingRight"]) == ("28px", "28px"), seen
    assert "content" in seen, seen


PADDING_PROBE = (
    Path(__file__).with_name("browser_probe_content_padding.js").read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    ("route", "side"), [("#W-Library/cases", "18px"), ("#CP-OS/activity", "18px")]
)
def test_the_library_home_and_run_activity_keep_their_content_padding(tmp_path, route, side):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_probe(tmp_path / "library/index.html", route, 1440, PADDING_PROBE)
    assert (seen["left"], seen["right"]) == (side, side)


CHIP_OVERLAP_PROBE = (
    Path(__file__).with_name("browser_probe_chip_overlap.js").read_text(encoding="utf-8")
)


def test_chart_periods_in_the_overview_aside_do_not_draw_their_labels_over_each_other(tmp_path):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    seen = read_probe(page, f"#W-Overview?c={NEW_FORMAT_RUN}", 1440, CHIP_OVERLAP_PROBE)
    assert seen["chips"] >= 2, "the fixture chart draws a citation label per period"
    assert seen["crossing"] == [] and seen["fits"] is True, seen
    # The three periods no longer fit the 400px aside, so the chart scrolls in its own box.
    assert seen["chartScrolls"] is True and seen["chartInsideAside"] is True, seen


OVERVIEW_LAYOUT_PROBE = (
    Path(__file__).with_name("browser_probe_overview_layout.js").read_text(encoding="utf-8")
)
OVERVIEW_ORDER = [
    "overview-lead",
    "overview-bottom-lines",
    "overview-limitations",
    "overview-charts",
    "overview-dates",
]
# What the Overview drew for the synthetic new-format run before the two-column layout (BASE
# 60233d2): the text of each Bottom line by module entry and of each Nearest dates row, in order.
BASE_NEW_FORMAT_ENTRIES = [
    (
        "Source readinessThe two documents read are enough for a credit snapshot, "
        "but no covenant package was read, so creditor protections cannot be "
        "confirmed from the file set."
    ),
    (
        "Financial foundationThe canonical data set holds the debt, cash, earnings "
        "and maturity figures the later modules rely on, each tied to a page of the "
        "two documents read."
    ),
    (
        "Business & governanceNorthbridge is a single-segment services group whose "
        "creditors depend on one operating company, so debt service rests on that "
        "company's cash generation. Basis"
    ),
    (
        "Liquidity Not assessableNot assessable: the documents read give no monthly "
        "cash forecast and no revolver drawing terms, so cash cover of the "
        "maturities cannot be tested."
    ),
]
BASE_NEW_FORMAT_DATES = [
    "2025-03-31Annual report reference dateBusiness & governance",
    "2025-03-31Synthetic noteFundamental credit",
    "2025-05-15First quarter resultsBusiness & governance",
    "2025-06-30Revolver commitment step-downBusiness & governance",
    "2025-06Synthetic callFundamental credit",
]


def read_overview(page: Path, route: str, width: int) -> dict:
    return read_probe(page, route, width, OVERVIEW_LAYOUT_PROBE)


@pytest.mark.parametrize(("width", "stacked"), [(1440, False), (1280, True), (1200, True)])
def test_the_new_format_overview_takes_the_two_column_layout(tmp_path, width, stacked):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    seen = read_overview(page, f"#W-Overview?c={NEW_FORMAT_RUN}", width)
    assert seen["fits"] is True
    assert seen["ids"] == OVERVIEW_ORDER
    assert seen["inMain"] == OVERVIEW_ORDER[:3] and seen["inAside"] == OVERVIEW_ORDER[3:]
    assert seen["asideLabel"] == "Charts and dates"
    main, aside = seen["mainBox"], seen["asideBox"]
    if width == 1440:
        assert abs(aside["width"] - 400) <= 1 and aside["left"] >= main["right"]
        # The page heading starts where the grid does.
        assert abs(seen["pageH2Left"] - main["left"]) <= 1, (seen["pageH2Left"], main["left"])
    if stacked:
        assert aside["top"] >= main["bottom"], "the aside is under the main column"
    # The lead: the eyebrow is Credit view with the writing module, the passage the headline.
    lead = seen["lead"]
    assert lead["h2"] == {"text": "Credit view", "size": "12px", "transform": "uppercase"}
    assert lead["h3Class"] == "sr-only" and lead["firstSize"] == "22px"
    assert lead["firstText"].startswith("Creditors are exposed to refinancing risk")
    assert "Written by Fundamental credit" in lead["text"]
    # Bottom line by module: a row (module left, text right), the text as BASE drew it.
    assert seen["entryColumns"].startswith("210px")
    assert seen["entries"] == BASE_NEW_FORMAT_ENTRIES
    # Nearest dates: the same table, header cells kept but hidden, one grid row per date.
    dates = seen["dates"]
    assert dates["caption"] is True and dates["cols"] == 3 and dates["theadHeight"] <= 1
    assert dates["rowDisplay"] == "grid" and dates["rows"] == BASE_NEW_FORMAT_DATES
    # Key charts: the link to the chart index on this run's Forecast page; cards fit the column.
    assert seen["charts"]["href"].startswith("#W-Forecast")
    assert seen["charts"]["cards"]
    if width == 1440:
        assert all(w <= 400 for w in seen["charts"]["cards"]), seen["charts"]["cards"]


def test_the_earlier_format_overview_has_its_sentence_and_no_chart_index_link(tmp_path):
    make_run(tmp_path, "run-a", as_of="2025-03-31", cp1_extra=EVENTS)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    seen = read_overview(page, "#W-Overview?c=run-a", 1440)
    assert seen["fits"] is True and seen["hasMain"] and seen["hasAside"]
    assert seen["ids"] == [*OVERVIEW_ORDER[:3], "overview-dates"]
    assert EARLIER_LEAD in seen["lead"]["text"] and seen["lead"]["h2"]["text"] == "Credit view"
    assert seen["lead"]["h2"]["transform"] == "uppercase"
    assert seen["chartIndexLinks"] == 0 and "charts" not in seen
    assert abs(seen["asideBox"]["width"] - 400) <= 1
    assert seen["dates"]["rowDisplay"] == "grid" and seen["dates"]["theadHeight"] <= 1


FORECAST_CASES_PROBE = Path(__file__).with_name("browser_probe_forecast_cases.js")


def library_with_four_case_model(
    tmp_path: Path, keys: tuple[str, ...] = ("REFERENCE", "UPSIDE", "DOWNSIDE_DRIVERS", "DOWNSIDE")
) -> Path:
    """A library whose run lists one model: the store's real grid over the hand-written files of
    test_credit_os_store (history plus the four CP-2G cases). The model's envelope is the only
    synthetic part (accepted by the controller); no published model folder is built."""
    from credit_os import store
    from test_credit_os_store import cases

    make_run(tmp_path, "run-a", as_of="2025-09-30")
    update_library.update_library(tmp_path)
    data_js = tmp_path / "library/data.js"
    prefix = "window.CREDIT_OS_DATA="
    data = json.loads(data_js.read_text(encoding="utf-8").removeprefix(prefix).rstrip().rstrip(";"))
    grid, problem = store.read_cashflow(cases(*keys), None)
    assert problem is None
    run = data["workspace"]["runs"]["run-a"]
    data["workspace"]["models"] = [
        {
            "id": "model-a",
            "issuerKey": run["issuerKey"],
            "mode": "accepted",
            "qualification": "unrun",
            "runId": None,
            "runFolder": "run-a",
            "scope": None,
            "inputContract": None,
            "revisionNote": None,
            "previous": None,
            "href": "../models/model-a.html?embedded=1",
            "download": "../models/model-a.html?download=1",
            "files": [],
            "sources": [],
            "register": None,
            "cashflow": grid,
        }
    ]
    data_js.write_text(prefix + update_library.embedded_json(data) + ";\n", encoding="utf-8")
    return tmp_path / "library/index.html"


def test_the_page_shows_the_other_forecast_cases_in_a_closed_details_below_the_main_grid(tmp_path):
    page = library_with_four_case_model(tmp_path)
    (page.parent / "probe.js").write_text(
        FORECAST_CASES_PROBE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    probe = page.with_name("probe.html")
    probe.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(probe, "#W-Forecast/model-a?c=run-a")
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert seen["groups"] == [
        "Quarter",
        "Year to date",
        "Fiscal year",
        "Last twelve months",
        "Pro forma",
        "Base case",
        "Downside case",
    ]
    # The store's group name is "Downside (CP-2G drivers)"; screen.js moduleNames rewrites the code.
    assert (
        seen["summary"] == "Other forecast cases: Upside, Downside (Forward credit model drivers)"
    )
    assert seen["otherGroups"] == 2 and seen["otherOpen"] is False
    assert seen["otherName"] == "Other forecast cases"
    assert seen["pf"] == {
        "text": "n.a.",
        "label": "n.a.: no handoff states pro forma adjustments",
    }
    assert seen["fits"] is True and seen["ids"] is True  # the grid scrolls inside its region


@pytest.mark.parametrize(
    "keys, last",
    [
        (("REFERENCE", "UPSIDE", "DOWNSIDE_DRIVERS", "DOWNSIDE"), "FY2027E"),
        (("REFERENCE",), "FY2027E"),
    ],
)
def test_the_caption_range_ends_on_the_last_real_period_never_the_placeholder(tmp_path, keys, last):
    page = library_with_four_case_model(tmp_path, keys)
    dom, console = visit(page, "#W-Forecast/model-a?c=run-a")
    assert console == []
    caption = re.search(r'<p class="forecast-caption">(.*?)</p>', dom, re.DOTALL)[1]
    assert f"Q3 2024 to {last} " in caption and " to Downside" not in caption


def test_other_forecast_cases_screenshot_for_the_reader_check(tmp_path):
    target = os.environ.get("FORECAST_SCREENSHOT")
    if not target:
        pytest.skip("set FORECAST_SCREENSHOT to the PNG path to write")
    screenshot = Path(target)
    page = library_with_four_case_model(tmp_path)
    (page.parent / "open.js").write_text(
        "addEventListener('load',()=>setTimeout(()=>{"
        "document.querySelector('details.cashflow-other').open=true;"
        "document.body.style.minHeight='1500px'},1500));",
        encoding="utf-8",
    )
    shot = page.with_name("shot.html")
    shot.write_text(page.read_text().replace("</body>", '<script src="open.js"></script></body>'))
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            chrome(),
            "--headless=new",
            "--disable-gpu",
            "--window-size=1280,3200",
            "--virtual-time-budget=10000",
            f"--screenshot={screenshot}",
            shot.as_uri() + "#W-Forecast/model-a?c=run-a",
        ],
        capture_output=True,
        timeout=120,
        check=True,
    )
    assert screenshot.stat().st_size > 0


CHART_INDEX_LINK_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.chart-index-link'); i++) await sleep(50);
  const content = document.getElementById('content');
  const link = document.querySelector('.chart-index-link');
  const tabOf = () => [...document.querySelectorAll('.workspace-tabs a')]
    .find(a => a.textContent.trim() === 'Forecast')?.getAttribute('href');
  const seen = {href: link.getAttribute('href'), tabBefore: tabOf()};
  link.click();
  for (let i = 0; i < 200 && !document.getElementById('run-charts'); i++) await sleep(50);
  await sleep(400);
  const index = document.getElementById('run-charts');
  seen.hash = location.hash;
  seen.heading = document.getElementById('section-nav').textContent;
  seen.indexShown = Boolean(index);
  seen.offset = index
    ? index.getBoundingClientRect().top - content.getBoundingClientRect().top : null;
  seen.atEnd = content.scrollTop + content.clientHeight >= content.scrollHeight - 1;
  seen.scrollTop = content.scrollTop;
  seen.tabAfter = tabOf();
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();
"""


def test_the_overviews_chart_index_link_lands_on_the_chart_index(tmp_path):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    route = f"#W-Overview?c={NEW_FORMAT_RUN}"
    seen = read_probe(page, route, 1280, CHART_INDEX_LINK_PROBE)
    assert seen["href"].startswith("#W-Forecast") and f"c={NEW_FORMAT_RUN}" in seen["href"]
    assert seen["hash"].startswith("#W-Forecast") and "Forecast" in seen["heading"]
    assert seen["indexShown"] is True
    # The index is drawn after the whole Forecast page: it is at the top of the canvas, or the
    # canvas is scrolled as far as it goes.
    assert -1 <= seen["offset"] <= 20 or seen["atEnd"], seen
    assert seen["scrollTop"] > 0, seen
    # The Forecast tab keeps the link it had.
    assert seen["tabBefore"] and seen["tabAfter"] == seen["tabBefore"], seen


def two_model_workspace(workspace: Path) -> Path:
    """The synthetic new-format run (with its Chart index link) listing two forecast models."""
    page = synthetic_workspace(workspace, with_chart_and_event)
    data_js = page.parent / "data.js"
    prefix = "window.CREDIT_OS_DATA="
    data = json.loads(data_js.read_text(encoding="utf-8").removeprefix(prefix).rstrip().rstrip(";"))
    run = data["workspace"]["runs"][NEW_FORMAT_RUN]
    data["workspace"]["models"] = [
        {
            "id": model_id,
            "issuerKey": run["issuerKey"],
            "mode": "accepted",
            "qualification": "unrun",
            "runId": None,
            "runFolder": NEW_FORMAT_RUN,
            "scope": None,
            "inputContract": None,
            "revisionNote": None,
            "previous": None,
            "href": f"../models/{model_id}.html?embedded=1",
            "download": f"../models/{model_id}.html?download=1",
            "files": [],
            "sources": [],
            "register": None,
            "cashflow": None,
        }
        for model_id in ("model-a", "model-b")
    ]
    data_js.write_text(prefix + update_library.embedded_json(data) + ";\n", encoding="utf-8")
    return page


CHART_INDEX_TWO_MODELS_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const run = %s;
  const content = document.getElementById('content');
  const tab = () => [...document.querySelectorAll('.workspace-tabs a')]
    .find(a => a.textContent.trim() === 'Forecast')?.getAttribute('href');
  const to = async hash => { location.hash = hash; await sleep(500); };
  const state = () => {
    const index = document.getElementById('run-charts');
    return {
      hash: location.hash,
      model: document.getElementById('model-select')?.value ?? null,
      tab: tab(),
      scrollTop: content.scrollTop,
      offset: index
        ? index.getBoundingClientRect().top - content.getBoundingClientRect().top : null,
      atEnd: content.scrollTop + content.clientHeight >= content.scrollHeight - 1,
    };
  };
  const seen = {};
  await to('#W-Forecast?c=' + run);
  const options = [...document.querySelectorAll('#model-select option')].map(o => o.value);
  seen.options = options;
  const second = options[1];
  await to('#W-Forecast/' + second + '?c=' + run);
  seen.remembered = second;
  await to('#W-Overview?c=' + run);
  seen.tabBefore = tab();
  document.querySelector('.chart-index-link').click();
  await sleep(600);
  seen.afterLink = state();
  // R-2: back to the top, away to the Forecast tab, then to the index route again.
  content.scrollTop = 0;
  await to(tab().slice(0));
  seen.onTab = state();
  await to(seen.afterLink.hash);
  seen.again = state();
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();
"""


def test_the_chart_index_route_keeps_the_chosen_forecast_model_and_scrolls_on_every_visit(tmp_path):
    page = two_model_workspace(tmp_path)
    probe = CHART_INDEX_TWO_MODELS_PROBE % json.dumps(NEW_FORMAT_RUN)
    seen = read_probe(page, f"#W-Overview?c={NEW_FORMAT_RUN}", 1280, probe)
    assert len(seen["options"]) == 2 and seen["remembered"] != seen["options"][0], seen
    after = seen["afterLink"]
    # R-1: the link draws the model the reader chose, lands on the index and leaves the tab alone.
    assert after["hash"].startswith("#W-Forecast/run-charts"), seen
    assert after["model"] == seen["remembered"], seen
    assert after["tab"] == seen["tabBefore"], seen
    assert seen["tabBefore"].startswith("#W-Forecast/" + seen["remembered"]), seen
    assert -1 <= after["offset"] <= 20 or after["atEnd"], seen
    assert after["scrollTop"] > 0, seen
    # R-2: back to the same route from another Forecast route scrolls to the index again.
    assert seen["onTab"]["scrollTop"] == 0 and seen["onTab"]["hash"] == seen["tabBefore"], seen
    again = seen["again"]
    assert again["hash"] == after["hash"] and again["model"] == seen["remembered"], seen
    assert -1 <= again["offset"] <= 20 or again["atEnd"], seen
    assert again["scrollTop"] > 0, seen


# Ruling 2026-11-12, decision 1: a chart is shown once, as a card; its section route scrolls the
# card into view.
CHART_ROUTE_PROBE = """(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const content = document.getElementById('content'), seen = {};
  const wanted = (location.hash.match(/\\/(s-\\d+)/) || [])[1];
  for (let i = 0; i < 200 && !document.getElementById('charts'); i++) await sleep(50);
  await sleep(300);
  const target = document.getElementById(wanted), view = content.getBoundingClientRect();
  const box = target && target.getBoundingClientRect();
  seen.card = Boolean(target && target.classList.contains('panel-card'));
  seen.inView = Boolean(
    box && box.top >= view.top - 1 && box.top < view.bottom);
  seen.chartData = content.innerText.includes('Chart data:');
  seen.cards = document.querySelectorAll('#charts .panel-card').length;
  seen.outline = [...document.querySelectorAll('.section-outline .section-item')]
    .map(a => a.textContent.trim());
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();"""


def test_a_chart_route_scrolls_its_card_into_view_and_no_chart_data_text_is_drawn(tmp_path):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    [handoff] = [
        f
        for f in tmp_path.glob(f"runs/{NEW_FORMAT_RUN}/deliveries/**/*CP-2*.md")
        if "### Chart data: debt maturities" in f.read_text(encoding="utf-8")
    ]
    line = handoff.read_text(encoding="utf-8").splitlines().index("### Chart data: debt maturities")
    seen = read_probe(page, f"#CP-2/s-{line + 1}?c={NEW_FORMAT_RUN}", 1280, CHART_ROUTE_PROBE)
    assert seen["card"] is True and seen["inView"] is True
    assert seen["chartData"] is False and seen["cards"] >= 1
    assert seen["outline"][-1] == "Evidence & audit"
    hidden = ("Chart data", "Events", "Request", "Next module")
    assert not any(entry.startswith(hidden) for entry in seen["outline"])


COMPONENT_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 100 && !document.querySelector('.badge'); i++) await sleep(50);
  await sleep(300);
  const button = document.querySelector('.primary-action');
  const badge = document.querySelector('.badge');
  const b = button && getComputedStyle(button), g = badge && getComputedStyle(badge);
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    button: b && [b.height, b.borderTopLeftRadius, b.fontWeight],
    badge: g && [g.borderTopLeftRadius],
    scrollWidth: document.documentElement.scrollWidth, inner: innerWidth});
  document.body.appendChild(out);
})();
"""


def test_the_primary_button_and_a_state_badge_have_the_component_reference_box(tmp_path):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_served_probe(
        tmp_path / "library/index.html", "#W-Report/history?c=run-a", 1440, COMPONENT_PROBE
    )
    assert seen["button"] == ["40px", "8px", "600"], seen
    assert seen["badge"] == ["6px"], seen


def test_the_library_home_does_not_scroll_sideways_at_375px(tmp_path):
    # Chrome will not open a window under 500px, so the library opens in a 375px frame, where
    # its own media queries see 375px, and the framed page posts its measures to the wrapper.
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    (page.parent / "probe.js").write_text(
        COMPONENT_PROBE.replace(
            "document.body.appendChild(out);",
            "parent.postMessage(out.textContent, '*');",
        ),
        encoding="utf-8",
    )
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    wrapper = page.parent / "wrap.html"
    wrapper.write_text(
        '<iframe src="index.html" width="375" height="800"></iframe><pre id="probe"></pre>'
        "<script>addEventListener('message', e => "
        "{ document.getElementById('probe').textContent = e.data; });</script>",
        encoding="utf-8",
    )
    dom, console = visit(wrapper, "", 1000)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert seen["inner"] == 375 and seen["scrollWidth"] <= 375, seen
