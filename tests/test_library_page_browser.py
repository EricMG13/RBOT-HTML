"""The generated library in a real browser (headless Chrome), opened from disk over file://.

Chrome's console is read for errors, including Content Security Policy violations: the page's
policy blocks every network request, so a violation is a request the page tried to make or a source
it needs but is not allowed. Needs Google Chrome or Chromium; skipped where there is none."""

import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
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
    # The deliverable opens the report inside the app, from the row and from the selected run.
    report = f'href="#W-Reports/{delivery}?c=run-a"'
    assert f'<a class="report-link" {report}' in dom
    assert f'<a class="primary-action" {report}' in dom
    # A cited source links the retained file it quotes.
    assert f'href="../runs/run-a/deliveries/{delivery}/CP-1.md" target="_blank"' in dom
    dom, console = visit(page, "#W-Overview/overview?c=run-a")
    assert console == []
    assert (
        len(re.findall(r'<div class="panel-card">', dom)) == 4
    )  # Leverage, cover, liquidity, maturities, each under the module that owns it.
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
    assert seen["running"] == ["rgb(0, 5, 51)", "rgb(255, 255, 255)"]
    assert seen["done"][0] == "rgb(246, 247, 250)"
    assert seen["waiting"][1] == "rgb(74, 80, 104)"


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


def test_the_count_of_citations_without_a_page_opens_their_list_and_escape_returns(tmp_path):
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
    # The count under the UNKEYED paragraph (two citations), not the first count on the page (one).
    assert seen["count"] == "2 citations without a page", seen
    assert seen["verified"] >= 1 and seen["singleGaps"] == 0
    opened = seen["open"]
    assert opened["hidden"] is False and "chip=gaps" in opened["hash"]
    assert opened["items"] == opened["expected"] == 2
    assert opened["focusInInspector"] is True
    assert seen["escaped"] == {
        "hidden": True,
        "focusOnCount": True,
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
    found = re.search(r'<details class="fold" id="reference"[^>]*>(.*?)</details>', dom, re.DOTALL)
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
def test_the_run_report_fits_and_the_register_checkbox_adds_rows(tmp_path, width):
    page = report_library(tmp_path, cp0_confidence="Not assessable")
    (page.parent / "probe.js").write_text(OVERVIEW_PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#W-Overview?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert seen["rows"] > 0, "the run report drew no chart rows"
    assert seen["valueInCard"] is True and seen["fits"] is True
    assert 0 < seen["established"] < seen["total"], "the run has no not-assessable row"
    assert seen["before"] == seen["established"]  # Not-assessable rows start hidden.
    assert seen["after"] == seen["total"]  # Ticking the checkbox shows every row.
    assert seen["emptyBefore"] is False  # Rows are shown, so the empty row is not.
    # Unticked and filtered to a not-assessable row's group: none is shown, the empty row is.
    assert seen["filtered"] == {"shown": 0, "emptyShown": True}
    # Design pass 2026-11-10: parts listed and reachable, tables whole and in the text face.
    assert seen["outline"][-5:] == [
        "Findings register",
        "Open items",
        "Module matrix",
        "Deliverables from this run",
        "Chart index",
    ]
    assert seen["jump"] == {
        "hash": "#W-Overview/run-matrix",
        "current": ["Module matrix"],
        "inView": True,
    }
    assert seen["scrollers"] == 0 and seen["monoProse"] == 0
    assert seen["coverage"] == ["Source readiness", "Financial foundation"]  # Names, not codes.


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


# Names, not codes: the module page with its audit section and the inspector open, then the Evidence
# tab, Run activity and a search, read as a reader sees and hears them (text, title, aria-label).
# Register references (C1, K) are not codes of this kind.
CODES_PROBE = """(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms)), hits = [];
  const code = /\\bCP-[A-Z0-9]+\\b|\\bT\\d+[A-Z]?(?:\\.\\d+)?\\b/;
  const scan = where => {
    const walker = document.createTreeWalker(
      document.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    while (walker.nextNode()) {
      const node = walker.currentNode, text = node.nodeType === 3;
      const seen = text
        ? [node.parentElement.closest('script,style,#probe') ? '' : node.data]
        : ['title', 'aria-label'].map(a => node.getAttribute(a) || '');
      for (const value of seen) if (code.test(value)) hits.push(where + ': ' + value.slice(0, 80));
    }
  };
  for (let i = 0; i < 200 && !document.querySelector('.module-head'); i++) await sleep(50);
  document.querySelector('.audit-open').click();
  await sleep(100);
  scan('module page');
  document.querySelector('.chip[data-evidence]').click();
  await sleep(300);
  scan('inspector');
  for (const route of ['#W-Evidence/sources?c=run-a', '#CP-OS/activity']) {
    location.hash = route;
    await sleep(300);
    scan(route);
  }
  location.hash = '#CP-1/head?c=run-a';
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
    inspector: !!document.querySelector('.evidence-context'),
    searched: document.querySelectorAll('.search-hit').length,
  });
  document.body.append(out);
})();"""


def test_no_module_code_or_step_id_reaches_a_reader_from_a_module_page(tmp_path):
    page = nine_part_library(tmp_path)
    (page.parent / "probe.js").write_text(CODES_PROBE, encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#CP-1/head?c=run-a")
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert seen["inspector"] is True and seen["titled"] == 0 and seen["searched"] > 0
    assert seen["hits"] == []


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
const shown = radios.filter(x => !x.closest('.card').hidden).map(x => x.value);
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
pick('data-k="management_bridge"', 'no');  // The checklist is drawn for the pathway first.
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


def test_a_fixed_pathway_is_selected_and_locked(tmp_path):
    from deploy_workflow.inbox.drops import ensure_layout, write_templates

    short = tempfile.mkdtemp(prefix="ib", dir="/tmp")  # tmp_path is over the 80-character limit.
    shutil.rmtree(short)
    layout = ensure_layout(Path(short))
    try:
        write_templates(layout, ROOT / "docs/templates/context-form.html")
        form = layout.inbox / "earnings_update/_template/context-form.html"
        page = (
            tmp_path / "probe.html"
        )  # The form with a probe that tries another pathway and run type, then reads.
        text = form.read_text(encoding="utf-8")
        page.write_text(text.replace("</body>", FORM_PROBE, 1), encoding="utf-8")
        dom, console = visit(page)
        assert console == []
        probe = json.loads(
            html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1])
        )
        # Only the folder's pathway is offered; the other five are disabled and hidden.
        assert probe["shown"] == ["earnings_update"] and probe["disabled"] == 5
        assert probe["built"]["run"]["pathway"] == "earnings_update"  # The pathway held ...
        # ... and so did the run type: an Earnings Update compares two periods (form, 2026-11-10).
        assert probe["built"]["run"]["run_type"] == "earnings"
        assert probe["warned"] == [
            'run.pathway: this form is fixed to earnings_update; "credit_snapshot" was replaced'
        ]
        assert (
            probe["same"] == []
        )  # A loaded context naming the fixed pathway gives no such warning.
    finally:
        shutil.rmtree(layout.root)


@pytest.mark.parametrize("width", [1440, 1280])
def test_a_liquidity_bridge_is_a_waterfall_with_its_table_form_and_fits_the_page(tmp_path, width):
    make_run(tmp_path, "run-a", as_of="2024-12-31", cp1_extra=CHARTS + BRIDGE)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    probe = Path(__file__).with_name("browser_probe_bridge.js")
    (page.parent / "probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#W-Overview?c=run-a", width)
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
    dom, console = visit(page, "#W-Overview?c=run-a", width)
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
def test_the_calendar_draws_the_event_lane_with_its_table_and_fits_the_page(tmp_path, width):
    make_run(tmp_path, "run-a", as_of="2025-12-31", cp1_extra=CHARTS + EVENTS)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    probe = Path(__file__).with_name("browser_probe_calendar.js")
    (page.parent / "probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#W-Calendar?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert (seen["lanes"], seen["points"], seen["spans"], seen["tableRows"]) == (1, 1, 3, 4)
    assert seen["laneName"] == "Financing" and seen["focusable"] is True
    assert seen["tableAfterLanes"] is True and seen["fits"] is True
    # The Overview draws the same lanes compactly, linked to the Calendar tab, with no table.
    dom, console = visit(page, "#W-Overview?c=run-a", width)
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert console == [] and (seen["lanes"], seen["tableRows"], seen["fits"]) == (1, 0, True)
    assert 'class="event-lanes compact"' in dom and "Open the Calendar tab" in dom


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_overview_draws_the_map_with_its_table_and_the_status_map_and_fits_the_page(
    tmp_path, width
):
    make_run(tmp_path, "run-a", as_of="2025-12-31", cp1_extra=CHARTS + MAPS)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    probe = Path(__file__).with_name("browser_probe_maps.js")
    (page.parent / "probe.js").write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
    page.write_text(page.read_text().replace("</body>", '<script src="probe.js"></script></body>'))
    dom, console = visit(page, "#W-Overview?c=run-a", width)
    assert console == []
    seen = json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))
    assert (seen["nodes"], seen["edges"], seen["labels"], seen["tableRows"]) == (11, 12, 12, 12)
    assert seen["statusNodes"] >= 1 and seen["statusStates"] == seen["statusNodes"]
    assert seen["wide"] is True and seen["scrolls"] is True  # Natural width, scrolled in its card.
    assert seen["scrollFocusable"] is True and seen["fits"] is True and seen["statusItems"] >= 1
    assert seen["tableAfterDiagram"] is True and seen["cutEdges"] == 1


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_context_bar_and_the_chart_index_keep_the_run_and_fit_the_page(tmp_path, width):
    # Long names: a 38-character issuer and 80-character run folders, with every popover open.
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
        assert seen["shown"] is True and "As of 31 December 2025" in seen["text"]
        assert len(seen["others"]) == 1 and f"c={long}-other" in seen["others"][0]
        assert seen["roles"] == ["source", "analysis", "export"]
        assert seen["indexRows"] == [
            "Leverage|Drawn",
            "Interest cover|Drawn",
            "Liquidity|Drawn",
            "Financing events|Drawn",
            "Credit-risk transmission map|Drawn",
        ]
        assert seen["indexScrollFocusable"] is True
        assert seen["summaryFocus"] is True and seen["listInView"] is True and seen["fits"] is True
        assert (
            f"c={long}" in seen["after"] and seen["barAfter"] is True
        )  # Moving to a file keeps the run.
