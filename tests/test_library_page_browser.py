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
| FY2027 ending September 30 | 310 | US$m | Synthetic bucket. |
| FY2028 ending September 30 | 450 | US$m | Synthetic bucket. |
| FY2029 ending September 30 | 75 | US$m | Synthetic bucket. |
| FY2030 ending September 30 | 860 | US$m | Synthetic bucket. |
| FY2031 ending September 30 | 140 | US$m | Synthetic bucket. |
| FY2032 ending September 30 | 100 | US$m | Synthetic bucket. |
| FY2033 ending September 30 | 107 | US$m | Synthetic bucket. |
| FY2034 ending September 30 | 114 | US$m | Synthetic bucket. |
| FY2035 ending September 30 | 121 | US$m | Synthetic bucket. |
| FY2036 ending September 30 | 128 | US$m | Synthetic bucket. |
| FY2037 ending September 30 | 135 | US$m | Synthetic bucket. |
| FY2038 ending September 30 | 142 | US$m | Synthetic bucket. |
| FY2039 ending September 30 | 149 | US$m | Synthetic bucket. |
| FY2040 ending September 30 | 156 | US$m | Synthetic bucket. |
| FY2041 ending September 30 | 163 | US$m | Synthetic bucket. |
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


# The Report history is a vertical run timeline (one entry per run).
HISTORY = '<ol class="tl tl-v">'
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
    # One issuer is one card and one list row (the list pane is in the page, hidden until picked).
    assert len(re.findall(r"<tr[ >]", dom.split("<tbody>", 1)[1].split("</tbody>")[0])) == 1
    assert len(re.findall(r'<article class="lib-card"', dom)) == 1
    assert "Northbridge Synthetic Group" in dom
    # A run is named by its period and pathway, never by its code: the row's cell and the card read
    # "31 December 2024 · Credit snapshot" and the id only opens it (in the link, not in any text).
    assert re.search(
        r'<a href="#W-Overview/overview\?c=run-a"[^>]*>31 December 2024 \u00b7 Credit snapshot</a>',
        dom,
    )
    assert '<p class="lc-when">31 December 2024</p>' in dom
    assert ">run-a<" not in dom and 'title="run-a"' not in dom
    assert 'id="library-nav"' not in dom  # Issuers are a filter, not a second navigation.
    delivery = next((tmp_path / "runs/run-a/deliveries").iterdir()).name
    # The delivered report is retired (decision 1): the row and the card open the run and its
    # history.
    assert '<a class="report-link" href="#W-Overview/overview?c=run-a"' in dom
    assert '<a class="report-link" href="#W-Report/history?c=run-a"' in dom
    assert '<a class="lc-open" href="#W-Overview/overview?c=run-a"' in dom
    assert '<a class="lc-hist" href="#W-Report/history?c=run-a"' in dom
    assert "#W-Reports" not in dom and "report.html" not in dom and "Open report" not in dom
    # Source references are Evidence's: the library home links no retained file. Evidence offers
    # the original handoff the cited source came from, and the file it links is the retained one.
    assert f"/deliveries/{delivery}/" not in dom and "CP-1.md" not in dom
    evidence, console = visit(page, "#W-Evidence/sources?c=run-a")
    assert console == []
    assert 'href="downloads/run-a/CP-1.md" download=""' in evidence
    retained = (tmp_path / "runs/run-a/deliveries" / delivery / "CP-1.md").read_bytes()
    assert (page.parent / "downloads/run-a/CP-1.md").read_bytes() == retained
    dom, console = visit(page, "#W-Overview/overview?c=run-a")
    assert console == []
    # The Overview selects (ruling H5): this earlier-format run has no reader passages, so no
    # lead, and the visuals catalogue places no CP-1 chart on it; the charts stay with the module.
    assert 'id="overview-lead"' in dom and EARLIER_LEAD in dom
    assert "No bottom line in this handoff." in dom and 'id="overview-modules"' in dom
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
    assert HISTORY in dom and '<li class="tl-i" aria-current="true">' in dom
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
        assert HISTORY in dom, old
    # With no run named, the page opens the workspace's first run, as every run page does.
    dom, console = visit(page, "#W-Reports/list")
    assert console == [] and HISTORY in dom


def test_an_old_reports_hash_opens_the_library_when_no_run_is_known(tmp_path):
    update_library.update_library(tmp_path)  # No runs.
    dom, console = visit(tmp_path / "library/index.html", "#W-Reports/list")
    assert console == []
    assert HISTORY not in dom and "No issuers in this library yet" in dom


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
    const mark=document.querySelector('.run-card .step.'+state+' .state');
    const s=getComputedStyle(mark);
    out[state]=[s.color,mark.querySelector('.state-w').textContent];
  }
  const head=getComputedStyle(document.querySelector('.run-card .run-marks .state'));
  out.head=[head.backgroundColor,head.color];
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
    # Each module's step carries its state as a word and a colour (running blue-700, done green,
    # waiting text-tertiary); the card's own mark reads running blue-700 on the quiet surface.
    assert seen["running"] == ["rgb(0, 18, 178)", "Running"]
    assert seen["done"] == ["rgb(15, 128, 72)", "Done"]
    assert seen["waiting"] == ["rgb(71, 74, 79)", "Waiting"]
    assert seen["head"] == ["rgb(250, 250, 251)", "rgb(0, 18, 178)"]


RUN_ACTIVITY_PROBE = (
    Path(__file__).with_name("browser_probe_run_activity.js").read_text(encoding="utf-8")
)
LONG_FOLDER = (
    "2026-11-12-a-very-long-issuer-folder-name-that-would-not-fit-a-narrow-card-without-wrapping"
)


def run_activity_library(tmp_path: Path, queued_pathway: str = "earnings_update") -> Path:
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
                "pathway": queued_pathway,
                "folder": LONG_FOLDER + "-q1",
                "files": ["queued-a.pdf", "queued-b.pdf"],
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
    # Eight modules as C13 steps in the data's order; two loaders (run mark, running
    # module); two queued rows.
    assert seen["stepStates"] == ["done"] * 3 + ["running"] + ["waiting"] * 4, seen
    assert seen["loaders"] == 2 and seen["queued"] == 2, seen
    # A changed snapshot is drawn again.
    assert seen["changedShown"] is True


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


def cdp_measure(page: Path, route: str, measure: str, wait_for: str, options: dict | None = None):
    """A JS expression's value after a real hover or an emulated media feature (DevTools Protocol).

    options: width, hover (a selector to point at), features (media features to emulate)."""
    job = {"width": 1440, "hover": None, "features": None, **(options or {})}
    job |= {"url": page.as_uri() + route, "height": 900, "waitFor": wait_for, "measure": measure}
    job_file = page.parent / "cdp-job.json"
    job_file.write_text(json.dumps(job), encoding="utf-8")
    script = Path(__file__).with_name("browser_cdp_measure.cjs")
    done = subprocess.run(
        ["node", str(script), chrome(), str(job_file)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_the_empty_states_library_button_keeps_its_white_label_on_hover(tmp_path):
    run_activity_library(tmp_path)
    (tmp_path / "activity.js").write_text(
        'window.RUN_ACTIVITY={"updated":"2026-11-12T00:00:00Z","runs":[]};\n', encoding="utf-8"
    )
    seen = cdp_measure(
        tmp_path / "library/index.html",
        "#CP-OS/activity",
        '(() => { const e = document.querySelector(".activity-empty a");'
        " return { hover: e.matches(':hover'), color: getComputedStyle(e).color }; })()",
        ".activity-empty a",
        {"hover": ".activity-empty a"},
    )
    assert seen == {"hover": True, "color": "rgb(255, 255, 255)"}


def test_forced_colours_outline_the_run_cards_steps_marks_and_waiting_rows(tmp_path):
    page = run_activity_library(tmp_path)
    seen = cdp_measure(
        page,
        "#CP-OS/activity",
        "(() => { const style = s => getComputedStyle(document.querySelector(s));"
        " return { step: style('.run-card .step').borderTopStyle,"
        " card: style('.run-card').borderTopStyle,"
        " row: style('.run-queue li').borderTopStyle,"
        " mark: style('.run-card .run-marks .state').borderTopStyle }; })()",
        ".run-card",
        {"features": [{"name": "forced-colors", "value": "active"}]},
    )
    assert seen == {"step": "solid", "card": "solid", "row": "solid", "mark": "solid"}


def test_a_waiting_row_centres_its_parts_and_keeps_a_top_edge(tmp_path):
    page = run_activity_library(tmp_path)
    seen = cdp_measure(
        page,
        "#CP-OS/activity",
        "(() => { const row = document.querySelector('.run-queue li');"
        " const mid = r => (r.top + r.bottom) / 2, box = row.getBoundingClientRect();"
        " const parts = ['.rq-mark', '.rq-who'].map(q => mid(row.querySelector(q)"
        ".getBoundingClientRect()));"
        " return { off: parts.map(m => Math.round(Math.abs(m - mid(box)))),"
        " edge: getComputedStyle(row).boxShadow }; })()",
        ".run-queue li",
    )
    # The row's mark and its text block sit on the row's middle; its top edge is a 1px inset line.
    assert all(off <= 2 for off in seen["off"]), seen
    assert "inset" in seen["edge"] and "0px 0px 0px 1px" in seen["edge"], seen


def test_a_real_pathway_name_stays_on_one_line_in_the_waiting_row(tmp_path):
    page = run_activity_library(tmp_path, queued_pathway="distressed_restructuring")
    seen = cdp_measure(
        page,
        "#CP-OS/activity",
        "(() => { const cell = [...document.querySelectorAll('.run-queue .run-path')]"
        ".find(e => e.textContent === 'Distressed restructuring');"
        " if (!cell) return -1;"
        " const r = document.createRange(); r.selectNodeContents(cell);"
        " return r.getClientRects().length; })()",
        ".run-queue li",
    )
    assert seen == 1


def test_an_empty_library_says_so(tmp_path):
    update_library.update_library(tmp_path)
    dom, console = visit(tmp_path / "library/index.html")
    assert console == []
    assert "No issuers in this library yet" in dom


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
    assert seen["control"].startswith("Basis for paragraph: The figure is printed in Z"), seen
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
    # An earlier-format run has no lead to select from, so the page draws only the lead sentence and
    # the module tiles.
    assert seen["parts"] == ["overview-lead", "overview-modules"]
    assert seen["timeline"] == 0
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
    # A file name is shown as stored where file names live (the inspector and the Evidence Sources
    # tab) and is no longer drawn on the module page itself (decision: findings pages carry no file
    # names; one trace control opens Evidence).
    for where in ("inspector", f"#W-Evidence/sources?c={run}"):
        assert any(k.startswith(where) and MEMO in k for k in seen["kept"]), (where, seen["kept"])
    assert not any(k.startswith("module page") and MEMO in k for k in seen["kept"]), seen["kept"]


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


def test_a_row_route_into_the_reference_part_opens_it_and_escape_returns_to_the_row_control(
    tmp_path,
):
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


def test_a_gaps_route_on_a_row_without_a_gap_opens_the_row_alone(tmp_path):
    page = nine_part_library(tmp_path)
    row = (
        line_of(tmp_path, "### Quoted findings") + 4
    )  # In Reference only; Key numbers does not draw it.
    seen = probe_route(page, f"#CP-1/head?c=run-a&e={row}&chip=gaps")
    assert seen["inspectorHidden"] is False
    assert (
        seen["rowPressed"] == 1
    )  # The row's own trace control is pressed; no gap list was asked for.


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
def test_the_overview_lists_the_leads_dates_instead_of_drawing_lanes_and_fits_the_page(
    tmp_path, width
):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    # The Calendar tab is retired (decision 12) and the Overview draws no lane (H5): "What to watch"
    # lists the lead module's dated items in one timeline, day-dated and period-dated items in the
    # table's own row order (the component does not sort), here 2025-03-31, 2025-06, 2025-Q3, 2025.
    dom, console = visit(page, f"#W-Overview?c={NEW_FORMAT_RUN}", width)
    assert console == []
    seen = read_overview(page, f"#W-Overview?c={NEW_FORMAT_RUN}", width)
    assert seen["fits"] is True
    assert seen["watch"]["entries"] == NEW_FORMAT_EVENTS
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
def test_the_run_label_and_the_forecast_charts_keep_the_run_and_fit_the_page(tmp_path, width):
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
        # One line under the tabs: the run named by its date and pathway (never by its code, however
        # long), and the way to the history.
        assert seen["shown"] is True
        assert seen["text"].startswith("Showing run: 31 December 2025 \u00b7 Credit snapshot")
        assert long.upper() not in seen["text"].upper()
        assert seen["historyText"] == "All runs of this issuer" and seen["popovers"] == 0
        assert seen["tabs"] == ["Report", "Overview", "Changes", "Modules", "Forecast", "Evidence"]
        assert seen["current"] == [route.split("?")[0][3:]]
        # The chart cards are the Forecast page's (each opens on its chart); the Overview has none.
        assert seen["indexRows"] == (
            []
            if "Overview" in route
            else ["Leverage|chart", "Interest cover|chart", "Liquidity|chart"]
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
        ("#W-Overview?c=synthetic-nbg-new-format-001", 0),
        ("#W-Evidence/registers?c=synthetic-nbg-new-format-001&m=CP-1", 2),
    ],
)
def test_wide_tables_scroll_in_their_own_region_on_a_narrow_page(tmp_path, route, tables):
    """W1: the Overview (a timeline and tiles, no table) and the Evidence tables do not widen a
    phone-width page, and every table sits in its own focusable scroll region."""
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
    assert seen["scrolling"] >= (1 if tables else 0)


def test_evidence_keeps_file_names_as_stored_and_says_when_no_supplied_file_is_recorded(tmp_path):
    """R6: the Input hashes list labels a module-named file by its module's name (the hash stays); a
    run record with no supplied-file list does not claim every supplied file was used."""
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    dom, console = visit(tmp_path / "library/index.html", "#W-Evidence/record?c=run-a")
    assert console == []
    cells = re.findall(r'<div class="ev-nm">([^<]*instructions)</div>', dom)
    assert cells == ["Source readiness instructions", "Financial foundation instructions"]
    # Each handoff and instruction link stays inside library/, where the served page can open it.
    assert 'href="downloads/run-a/CP-0.md" download' in dom
    assert 'href="downloads/run-a/instructions/CP-0.md" download' in dom
    dom, console = visit(tmp_path / "library/index.html", "#W-Evidence/sources?c=run-a")
    assert console == []
    assert "The run record lists no supplied files." in dom
    assert "Every supplied file is named" not in dom


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
        # `#content .history .tl-i`: the run timeline is still drawn without the link.
        assert seen["historyRuns"] == 1, seen


SCOPE_PROBE = Path(__file__).with_name("browser_probe_header_scope.js").read_text(encoding="utf-8")
# The run header's height from a file, for this file's fixture (`make_run(..., as_of="2024-12-31")`,
# route #CP-1/head?c=run-a): 152.33px at both widths, measured with this test's probe on the
# redesigned header (title, meta line and the As of and pathway chips) at 37b1689. The header held
# 113.14px at commit 1f1691c before the redesign added the meta line and the chips.
HEADER_HEIGHT = {1440: 152.33, 1280: 152.33}


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_run_header_is_unchanged_from_a_file_and_as_of_stays_on_one_line(tmp_path, width):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_probe(tmp_path / "library/index.html", "#CP-1/head?c=run-a", width, SCOPE_PROBE)
    assert seen["sideCount"] == 0, seen
    # The run's scope is two chips on one row: the as-of date, then the pathway.
    assert seen["chipsText"] == ["As of 31 December 2024", "Credit snapshot"], seen
    assert seen["scopeHeight"] <= 24 and seen["chipsOnOneRow"] is True, seen
    assert abs(seen["headerHeight"] - HEADER_HEIGHT[width]) <= 0.5, seen


@pytest.mark.parametrize("width", [1440, 1280])
def test_the_run_header_keeps_as_of_on_one_line_beside_the_start_link_when_served(tmp_path, width):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    from_file = read_probe(page, "#CP-1/head?c=run-a", width, SCOPE_PROBE)
    seen = read_served_probe(page, "#CP-1/head?c=run-a", width, SCOPE_PROBE)
    assert seen["scopeText"] == "As of 31 December 2024", seen
    assert seen["scopeHeight"] <= 24 and seen["chipsOnOneRow"] is True, seen  # one line
    assert seen["scopeOverlapsTitle"] is False and seen["linkOverlapsTitle"] is False, seen
    assert seen["linkOverlapsChips"] is False and seen["fits"] is True, seen
    # The start link adds no height: the served header is the header from a file.
    assert abs(seen["headerHeight"] - from_file["headerHeight"]) <= 0.5, (seen, from_file)
    assert abs(seen["linkRight"] - seen["headerRight"]) <= 1, seen  # at the header's right edge
    if width == 1440:
        assert seen["linkMidMinusTitleMid"] <= 12, seen  # the title and the link share a row


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
    # The header: the way back to the library, the title at 32px (screen.css line 812: 700 32px,
    # 26px under 720px; it was 24px before the redesign), no run chip or Change run.
    assert seen["back"] == {"text": "Issuer library", "href": "#W-Library/cases"}
    assert "Change run" not in seen["headerText"] and seen["headerCodes"] == 0
    assert seen["h1Size"] == "32px"
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
    # The strip: the run named by its period and pathway (no run code), and the link to every run
    # of the issuer at the right edge.
    assert seen["allText"] == "All runs of this issuer" and 0 <= seen["allGap"] <= 30
    assert seen["barRun"].startswith("Showing run: 31 December 2024 \u00b7 Credit snapshot")
    assert seen["barCodes"] == 0 and "RUN-A" not in seen["barRun"].upper()
    assert seen["fits"] is True and seen["fitsOpen"] is True
    # The trace drawer is a fixed 420px panel over the page at both widths (screen.css line 833; it
    # was a 340px or 300px column before the redesign), and opening it keeps the page fitting.
    assert abs(seen["inspectorWidth"] - 420) <= 1


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


def with_chart_in_findings(text: str) -> str:
    """The synthetic CP-2 handoff with one placed chart under its Findings part, where the
    launcher's handoffs hold their `Chart data:` tables."""
    marker = "\n## Calculations"
    assert marker in text
    return text.replace(marker, MATURITIES + marker, 1)


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
    # "Findings" is the screen-reader heading of the part; "Bottom line" is the band's visible
    # eyebrow.
    [hidden] = [h for h in bottom["headings"] if h["text"] == "Findings"]
    assert "sr-only" in hidden["cls"] and hidden["srOnly"] is True
    assert bottom["verdict"]["eyebrow"] == "Bottom line"
    assert bottom["firstText"].startswith("Creditors are exposed to refinancing risk")
    # The passage is the headline of a navy band, white on --navy (a long passage is set at 16px).
    assert bottom["verdict"]["bg"] == INK  # --navy is rgb(0, 5, 51)
    assert (bottom["first"]["size"], bottom["first"]["color"]) == ("16px", "rgb(255, 255, 255)")
    # Key findings: a numbered feed, one control per finding that opens its trace.
    assert seen["feed"]["count"] == 3 and seen["feed"]["hasBasis"] == [1, 1, 1]
    assert (seen["feed"]["titleSize"], seen["feed"]["numWidth"]) == ("14px", "30px")
    assert (seen["feed"]["numText"], seen["feed"]["numColor"]) == ("1", "rgb(0, 18, 178)")
    assert seen["callout"]["heading"] == "What would change the view"
    assert (seen["prose"]["size"], seen["prose"]["line"]) == ("13px", "22.1px")
    assert seen["prose"]["width"] <= 660
    assert seen["cards"], "the new-format module page draws at least one chart card"
    assert all(not c["closed"] and c["height"] > 40 for c in seen["cards"])
    assert seen["fits"] is True
    # Limitations: a compact list, each with an amber 15px mark.
    assert (seen["limit"]["iconWidth"], seen["limit"]["size"]) == ("15px", "13px")
    # The inspector opened from a figure: the figure leads, large, before the context line.
    fig = seen["fromFigure"]
    assert fig["figure"]["size"] == "22px" and fig["figure"]["before"] is True
    assert fig["figure"]["text"] == "USD 1,390 million" and fig["h2"]["srOnly"] is True
    assert fig["card"] == "10px" and fig["fits"] is True
    assert fig["context"]["size"] == "13px" and fig["context"]["color"] == "rgb(56, 59, 63)"
    assert fig["back"] == "Close the trace and go back to the analysis"
    for literal in (
        "Trace",
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
    # The retained handoff, then the way on to this module's trace in Evidence.
    assert len(fig["links"]) == 2 and fig["links"][0].endswith("CP-2.md")
    assert fig["links"][1] == f"#W-Evidence/trace?c={NEW_FORMAT_RUN}&m=CP-2"
    # Opened from a Basis control: no figure; the eyebrow is the drawn "Evidence inspector".
    chip = seen["fromChip"]
    assert chip["hasFigure"] is False and chip["h2"]["srOnly"] is False
    assert chip["card"] == "10px" and chip["fits"] is True
    assert chip["back"] == "Close the trace and go back to the analysis"
    for literal in (
        "Trace",
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


def test_a_two_paragraph_bottom_line_draws_both_in_the_navy_band(tmp_path):
    second = "A second paragraph: the covenant package is untested.\n"

    def edit(text: str) -> str:
        marker = "\n### Key findings"
        assert marker in text
        return text.replace(marker, "\n" + second + marker, 1)

    seen = read_module_page(synthetic_workspace(tmp_path, edit), f"#CP-2?c={NEW_FORMAT_RUN}")
    paragraphs = seen["bottom"]["ps"]
    assert len(paragraphs) == 2 and paragraphs[1]["text"] == second.strip()
    # Both paragraphs sit in the band: the first is the headline (16px, long), the second the
    # band's body text (14px).
    assert [p["size"] for p in paragraphs] == ["16px", "14px"]
    assert [p["text"] for p in seen["bottom"]["verdict"]["body"]] == [second.strip()]


NARROW_HEADER_PROBE = """(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('header.issuer h1'); i++) await sleep(50);
  await sleep(200);
  const header = document.querySelector('header.issuer');
  const h1 = header.querySelector('h1'), scope = header.querySelector('.hchips .hchip');
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
    [(1000, "20px 22px", "14px"), (600, "18px 16px", None)],
)
def test_the_trace_drawer_keeps_its_padding_on_small_screens(
    tmp_path, width, padding, context_bottom
):
    """The drawer's body pads 20px 22px, and 18px 16px under 768px (screen.css lines 841, 843)."""
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
def test_the_drawer_field_card_keeps_its_small_screen_look(tmp_path, width, route):
    """At 1050px and below the drawer's fields are rows as before the redesign (padding 12px 0, no
    card border); the card is for wider windows. The drawer stacks each field's label over its value
    (screen.css line 842), so the old 160px label column is gone."""
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    seen = read_probe(page, route.format(NEW_FORMAT_RUN), width, FIELD_CARD_PROBE)
    assert (seen["padding"], seen["borderLeft"], seen["display"]) == ("12px 0px", "0px", "block")
    # The value runs the whole body: the card adds no padding or border of its own and no column.
    assert abs(seen["valueWidth"] - seen["bodyContent"]) <= 1, seen


OVERVIEW_STYLE_PROBE = (
    Path(__file__).with_name("browser_probe_overview_style.js").read_text(encoding="utf-8")
)


def test_the_overview_draws_figure_links_and_basis_controls_like_the_module_page(tmp_path):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    where = {
        "module": ("CP-2", "#key-findings .feed"),
        "overview": ("W-Overview", "#overview-why .feed"),
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
    ("route", "text_edge"),
    [
        # The timeline and the empty state are cards that inset their own text, so the body's first
        # block is what shares the header's edges there; plain pages share it by their first text
        # too.
        ("#W-Report/history?c=run-a", False),
        ("#W-Changes/changes?c=run-a", False),
        ("#W-Forecast/none?c=run-a", True),
        ("#W-Evidence/sources?c=run-a", True),
    ],
)
def test_the_body_of_a_run_tools_page_shares_both_edges_with_the_header(tmp_path, route, text_edge):
    make_run(tmp_path, "run-a", as_of="2024-12-31")
    update_library.update_library(tmp_path)
    seen = read_probe(tmp_path / "library/index.html", route, 1440, EDGES_PROBE)
    assert seen["fits"] is True
    parts = ("content", "head", "browse") if text_edge else ("head", "browse")
    for part in parts:
        if part in seen:
            assert abs(seen[part]["left"] - seen["h1Left"]) <= 1, (part, seen)
    for part in ("content", "head"):
        if part in seen:
            assert abs(seen[part]["right"] - seen["headerRight"]) <= 1, (part, seen)
    assert abs(seen["block"]["left"] - seen["h1Left"]) <= 1, seen
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


@pytest.mark.parametrize("width", [1440, 1000])
def test_chart_periods_on_the_forecast_page_do_not_draw_their_labels_over_each_other(
    tmp_path, width
):
    # The Overview draws no chart (they are the Forecast page's, and a mark carries no citation
    # label), so the period labels are read on the Forecast chart card of the same fixture chart.
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    seen = read_probe(page, f"#W-Forecast?c={NEW_FORMAT_RUN}", width, CHIP_OVERLAP_PROBE)
    assert seen["labels"] >= 12, "the fixture chart draws a label per period"
    assert seen["crossing"] == [] and seen["fits"] is True, seen
    # The twelve or more long period labels are wider than the card: the chart scrolls in its own
    # focusable region, which stays inside the card, and the page does not widen (fits above).
    assert seen["chartScrolls"] is True and seen["overflowX"] in ("auto", "scroll"), seen
    assert seen["regionFocusable"] is True and seen["regionInsideCard"] is True, seen


OVERVIEW_LAYOUT_PROBE = (
    Path(__file__).with_name("browser_probe_overview_layout.js").read_text(encoding="utf-8")
)
# The parts the Overview draws for the synthetic new-format run, in page order: the lead, the why
# grid (key findings; what would change the view and what to watch, which sits in its side column),
# one tile per module and the limitations.
OVERVIEW_PARTS = [
    "overview-lead",
    "overview-why",
    "overview-watch",
    "overview-modules",
    "overview-limitations",
]
# The module tiles' name, declared state and bottom line, as SYNTHETIC-CP-0/1/2/3/5 write them: the
# fixture's own sentences, in the catalogue's group order.
NEW_FORMAT_TILES = [
    [
        "Source readiness",
        "",
        (
            "The two documents read are enough for a credit snapshot, but no covenant package was "
            "read, so creditor protections cannot be confirmed from the file set."
        ),
    ],
    [
        "Business & governance",
        "",
        (
            "Northbridge is a single-segment services group whose creditors depend on one "
            "operating company, so debt service rests on that company's cash generation."
        ),
    ],
    [
        "Financial foundation",
        "",
        (
            "The canonical data set holds the debt, cash, earnings and maturity figures the later "
            "modules rely on, each tied to a page of the two documents read."
        ),
    ],
    [
        "Liquidity",
        "Not assessable",
        (
            "Not assessable: the documents read give no monthly cash forecast and no revolver "
            "drawing terms, so cash cover of the maturities cannot be tested."
        ),
    ],
    [
        "Fundamental credit",
        "",
        (
            "Creditors are exposed to refinancing risk rather than to weak earnings: net debt of "
            "USD 1,390 million is 4.2x earnings, and the next maturities fall inside two years."
        ),
    ],
]
# The dated events the fixture's EVENTS table holds (in the lead module), as the date is written
# and the event's name, in the table's own row order.
NEW_FORMAT_EVENTS = [
    ["2025-03-31", "Synthetic note"],
    ["2025-06", "Synthetic call"],
    ["2025-Q3", "Synthetic review"],
    ["2025", "Synthetic maturity year"],
]


def read_overview(page: Path, route: str, width: int) -> dict:
    return read_probe(page, route, width, OVERVIEW_LAYOUT_PROBE)


@pytest.mark.parametrize("width", [1440, 1280, 1200])
def test_the_new_format_overview_takes_the_redesign_layout(tmp_path, width):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    seen = read_overview(page, f"#W-Overview?c={NEW_FORMAT_RUN}", width)
    assert seen["fits"] is True and seen["navigatorShown"] is False
    assert seen["parts"] == OVERVIEW_PARTS
    # The lead: "Credit view" is the screen-reader heading, "Bottom line" the eyebrow, the passage
    # the headline (a long passage is set at 16px, a short one at 22px).
    lead = seen["lead"]
    assert lead["h2"]["text"] == "Credit view" and lead["h2"]["cls"] == "sr-only"
    assert lead["eyebrow"] == "Bottom line" and lead["firstSize"] == "16px"
    assert lead["firstText"].startswith("Creditors are exposed to refinancing risk")
    assert "Written by" not in lead["text"]
    # The why grid is a 24-column grid with the findings over 14 columns and the side column over
    # 10, side by side at every window width here; each span is columns plus the gaps inside it.
    why = seen["why"]
    unit = (why["width"] - 23 * why["gap"]) / 24
    assert abs(why["key"]["width"] - (14 * unit + 13 * why["gap"])) <= 1, why
    assert abs(why["side"]["width"] - (10 * unit + 9 * why["gap"])) <= 1, why
    assert why["side"]["left"] >= why["key"]["left"] + why["key"]["width"] and why["gap"] > 0
    assert why["key"]["top"] == why["side"]["top"]
    # The page heading starts where the grid does.
    assert abs(why["pageH2Left"] - why["key"]["left"]) <= 1, why
    assert len(why["keyItems"]) == 3 and why["callout"] == "What would change the view"
    # What to watch: the lead module's dated events, one list in date order, in the side column,
    # attributed to the module; no lane is drawn.
    watch = seen["watch"]
    assert watch["entries"] == NEW_FORMAT_EVENTS and watch["inSide"] is True
    assert watch["from"] == "From Fundamental credit" and watch["lanes"] == 0
    # One tile per module in the catalogue's order, each with the module's own bottom line.
    assert seen["tiles"] == NEW_FORMAT_TILES
    # The chart index is the Forecast page's: the Overview carries no link to it.
    assert seen["chartIndexLinks"] == 0


def test_the_earlier_format_overview_has_its_sentence_and_the_module_tiles_only(tmp_path):
    make_run(tmp_path, "run-a", as_of="2025-03-31", cp1_extra=EVENTS)
    update_library.update_library(tmp_path)
    page = tmp_path / "library/index.html"
    seen = read_overview(page, "#W-Overview?c=run-a", 1440)
    assert seen["fits"] is True
    # No reader passages, so no lead: the page draws only the sentence, then one tile per module
    # (the why grid, the watch timeline and the limitations all hang on a lead).
    assert seen["parts"] == ["overview-lead", "overview-modules"] and "watch" not in seen
    assert EARLIER_LEAD in seen["lead"]["text"] and seen["lead"]["h2"]["text"] == "Credit view"
    assert seen["lead"]["h2"]["transform"] == "uppercase"
    assert seen["chartIndexLinks"] == 0 and "why" not in seen
    assert [tile[0] for tile in seen["tiles"]] == ["Source readiness", "Financial foundation"]


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
  for (let i = 0; i < 200 && !document.querySelector('.overview-part'); i++) await sleep(50);
  const content = document.getElementById('content');
  const tabOf = () => [...document.querySelectorAll('.workspace-tabs a')]
    .find(a => a.textContent.trim() === 'Forecast')?.getAttribute('href');
  const seen = {
    links: [...document.querySelectorAll('#content a')]
      .filter(a => /chart index/i.test(a.textContent)).length,
    tabBefore: tabOf(),
  };
  // The chart index has no link on the Overview; its route is still the Forecast page's.
  location.hash = '#W-Forecast/run-charts?c=' + PROBE.run;
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


def test_the_chart_index_route_lands_on_the_run_charts_and_the_overview_links_no_index(tmp_path):
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    route = f"#W-Overview?c={NEW_FORMAT_RUN}"
    seen = read_probe(page, route, 1280, CHART_INDEX_LINK_PROBE, {"run": NEW_FORMAT_RUN})
    assert seen["links"] == 0, seen  # The Overview carries no link to the chart index.
    assert seen["hash"].startswith("#W-Forecast/run-charts") and "Forecast" in seen["heading"]
    assert seen["indexShown"] is True
    # The index is drawn after the whole Forecast page: it is at the top of the canvas, or the
    # canvas is scrolled as far as it goes.
    assert -1 <= seen["offset"] <= 20 or seen["atEnd"], seen
    assert seen["scrollTop"] > 0, seen
    # The Forecast tab keeps the link it had.
    assert seen["tabBefore"] and seen["tabAfter"] == seen["tabBefore"], seen


def two_model_workspace(workspace: Path, model_ids=("model-a", "model-b")) -> Path:
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
        for model_id in model_ids
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
  // The chart index has no link on the Overview now: the reader arrives by its route.
  await to('#W-Forecast/run-charts?c=' + run);
  await sleep(300);
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
  seen.outline = [...document.querySelectorAll('.sec-rail .rail-item')]
    .map(a => a.firstChild.textContent.trim());
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();"""


@pytest.mark.parametrize(
    ("edit", "rail"),
    [
        # The chart section sits after `## Gaps` (a gaps section to Evidence, drawn as a card).
        (
            with_chart_and_event,
            ["Bottom line", "Key findings", "Charts", "Timeline", "Limitations"],
        ),
        # The chart section sits under `## Findings`, where the launcher's handoffs hold it.
        (with_chart_in_findings, ["Bottom line", "Key findings", "Charts", "Limitations"]),
    ],
    ids=["under-gaps", "under-findings"],
)
def test_a_chart_route_scrolls_its_card_into_view_and_no_chart_data_text_is_drawn(
    tmp_path, edit, rail
):
    page = synthetic_workspace(tmp_path, edit)
    [handoff] = [
        f
        for f in tmp_path.glob(f"runs/{NEW_FORMAT_RUN}/deliveries/**/*CP-2*.md")
        if "### Chart data: debt maturities" in f.read_text(encoding="utf-8")
    ]
    line = handoff.read_text(encoding="utf-8").splitlines().index("### Chart data: debt maturities")
    seen = read_probe(page, f"#CP-2/s-{line + 1}?c={NEW_FORMAT_RUN}", 1280, CHART_ROUTE_PROBE)
    assert seen["card"] is True and seen["inView"] is True
    assert seen["chartData"] is False and seen["cards"] >= 1
    # The section rail ("On this page") lists the parts the page draws, and no raw section names;
    # the audit part is gone from the module page (Evidence holds it).
    assert seen["outline"] == rail
    hidden = ("Chart data", "Events", "Request", "Next module", "Evidence")
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


INTER_MODULE_TABLE = """
### Exposure by maturity

| Exposure | Effect | Consequence for CP-1 |
| --- | --- | --- |
| Revolver step-down | Cushion narrows over time. | Passed on as a stated constraint. |
"""


def with_inter_module_table(text: str) -> str:
    """The synthetic CP-2 handoff with a findings table holding an inter-module column."""
    marker = "\n## Calculations"
    assert marker in text
    return text.replace(marker, INTER_MODULE_TABLE + marker, 1)


HIDDEN_REACH_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const search = document.getElementById('module-search');
  const ask = async query => {
    search.value = query;
    search.dispatchEvent(new Event('input', {bubbles: true}));
    await sleep(200);
    return document.getElementById('search-results').innerText;
  };
  const seen = {};
  seen.hidden = await ask(PROBE.hidden);
  seen.shown = await ask(PROBE.shown);
  search.value = '';
  search.dispatchEvent(new Event('input', {bubbles: true}));
  const row = [...evidence.entries()].find(([, item]) => item.title === 'Revolver step-down');
  seen.rowIndexed = Boolean(row);
  seen.rowLabels = row ? row[1].fields.map(field => field[0]) : [];
  if (row) {
    location.hash = '#CP-2/head?c=' + PROBE.run + '&e=' + encodeURIComponent(row[0]);
    await sleep(600);
    const drawer = document.getElementById('inspector');
    seen.drawerOpen = !drawer.hidden;
    seen.drawer = drawer.innerText;
  }
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();
"""


def test_search_and_the_drawer_do_not_reach_text_written_for_another_module(tmp_path):
    """Review H2 (rule 7): a Next module sentence is not a search hit, and the drawer of a row
    does not show its inter-module column; the visible columns of the row still open."""
    page = synthetic_workspace(tmp_path, with_inter_module_table)
    config = {
        "run": NEW_FORMAT_RUN,
        "hidden": "builds the canonical data from",
        "shown": "Cushion narrows",
    }
    seen = read_probe(page, f"#CP-2/head?c={NEW_FORMAT_RUN}", 1280, HIDDEN_REACH_PROBE, config)
    assert "canonical data" not in seen["hidden"], seen["hidden"]
    # The search still finds a shown row.
    assert "Revolver step-down" in seen["shown"], seen["shown"]
    assert seen["rowIndexed"] and seen["rowLabels"] == ["Exposure", "Effect"], seen
    assert seen["drawerOpen"] and "Cushion narrows over time." in seen["drawer"], seen
    assert "Consequence for" not in seen["drawer"] and "stated constraint" not in seen["drawer"]


MODEL_HEADING_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const seen = {};
  for (const route of PROBE.routes) {
    location.hash = route;
    await sleep(700);
    seen[route] = {
      title: document.getElementById('section-title')?.textContent ?? null,
      announcement: document.getElementById('announcement').textContent,
      option: document.querySelector('#model-select option:checked')?.textContent ?? null,
    };
  }
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();
"""


def test_a_forecast_model_is_named_for_assistive_technology_as_the_select_names_it(tmp_path):
    """Review M3: the page's section heading and live announcement are the model's label, never its
    64-character id."""
    ids = ("a" * 64, "b" * 64)
    page = two_model_workspace(tmp_path, ids)
    routes = [
        f"#W-Forecast/{ids[0]}?c={NEW_FORMAT_RUN}",
        f"#W-Forecast/run-charts?c={NEW_FORMAT_RUN}",
    ]
    seen = read_probe(page, routes[0], 1280, MODEL_HEADING_PROBE, {"routes": routes})
    for route, entry in seen.items():
        assert entry["option"] and entry["title"] == entry["option"], (route, entry)
        assert entry["option"] in entry["announcement"], (route, entry)
        assert ids[0] not in entry["title"] + entry["announcement"], (route, entry)


ROUTE_FAILURE_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('header.issuer h1'); i++) await sleep(50);
  // A classifier that fails while the route is being read, before any block is placed.
  window.Shapes.tableShape = () => { throw new Error('probe: cannot classify'); };
  location.hash = PROBE.route;
  await sleep(700);
  const seen = {
    header: document.querySelector('header.issuer h1')?.textContent ?? '',
    content: document.getElementById('content').innerText,
    tabs: document.querySelectorAll('.workspace-tabs a').length,
  };
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();
"""


def test_a_route_that_cannot_be_drawn_says_so_under_the_issuer_header_and_logs_it(tmp_path):
    """Review M4 (c): the documented, logged fail-open of the route render keeps the issuer header
    and states the failure; it never leaves the page empty."""
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    inject_probe(page, ROUTE_FAILURE_PROBE, {"route": f"#CP-2/head?c={NEW_FORMAT_RUN}"})
    dom, console = visit(page, f"#W-Overview?c={NEW_FORMAT_RUN}")
    seen = probe_json(dom)
    assert seen["header"] and seen["tabs"] > 0, seen
    assert "Couldn\u2019t present this page" in seen["content"], seen
    assert any("The route could not be drawn" in line for line in console), console


SEARCH_AUDIT_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const search = document.getElementById('module-search');
  search.value = PROBE.query;
  search.dispatchEvent(new Event('input', {bubbles: true}));
  await sleep(300);
  const hits = [...document.querySelectorAll('#search-results a.search-hit')].map(a => ({
    text: a.innerText.replace(/\\s+/g, ' ').trim(),
    label: a.getAttribute('aria-label'),
    href: a.getAttribute('href'),
  }));
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({hits});
  document.body.appendChild(out);
})();
"""


def test_a_search_hit_in_an_audit_section_is_named_by_its_module_and_evidence_tab(tmp_path):
    """Review M5: the query still matches a source file's name, but the hit says only which module's
    Evidence tab holds it, and opens that tab at the row."""
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    config = {"query": "annual-report.pdf"}
    seen = read_probe(page, f"#W-Overview?c={NEW_FORMAT_RUN}", 1280, SEARCH_AUDIT_PROBE, config)
    assert seen["hits"], seen
    for hit in seen["hits"]:
        assert ".pdf" not in hit["text"] + hit["label"], hit
    sources = [hit for hit in seen["hits"] if "Sources" in hit["text"]]
    assert sources, seen
    assert all(re.search(r"^#W-Evidence/sources\?", hit["href"]) for hit in sources), sources
    assert any("Fundamental credit Sources" in hit["label"] for hit in sources), sources
    assert any(re.search(r"[?&]r=\d+", hit["href"]) for hit in sources), sources


DRAWER_DIALOG_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const drawer = document.getElementById('inspector');
  const outside = () => [...document.querySelectorAll(
    'a[href],button,input,select,textarea,[tabindex]:not([tabindex="-1"])'
  )].filter(el => !el.closest('[inert]') && !drawer.contains(el)
    && !el.closest('#drawer-backdrop'));
  const ready = () => document.querySelector('#content [data-paragraph]');
  for (let i = 0; i < 200 && !ready(); i++) await sleep(50);
  const trigger = document.querySelector('#content [data-paragraph]');
  const seen = {before: {inert: document.querySelectorAll('[inert]').length}};
  trigger.focus();
  trigger.click();
  await sleep(600);
  seen.open = !drawer.hidden;
  seen.role = drawer.getAttribute('role');
  seen.modal = drawer.getAttribute('aria-modal');
  seen.name = drawer.getAttribute('aria-label');
  seen.focusIn = drawer.contains(document.activeElement);
  seen.canvasInert = document.getElementById('canvas').inert;
  seen.railInert = document.querySelector('.rail').inert;
  seen.outside = outside().length;
  document.activeElement.dispatchEvent(
    new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
  await sleep(600);
  seen.closed = drawer.hidden;
  seen.after = {inert: document.querySelectorAll('[inert]').length};
  seen.focusBack = document.activeElement === trigger;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();
"""


def test_the_trace_drawer_is_a_modal_dialog_that_makes_the_page_behind_it_inert(tmp_path):
    """Review L6: role=dialog, aria-modal, an accessible name; nothing behind it can be tabbed to
    while it is open; focus moves in on open and returns to the control on Escape."""
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    route = f"#CP-2/head?c={NEW_FORMAT_RUN}"
    seen = read_probe(page, route, 1280, DRAWER_DIALOG_PROBE)
    assert seen["before"]["inert"] == 0, seen
    assert seen["open"] and seen["role"] == "dialog" and seen["modal"] == "true", seen
    assert seen["name"] == "Evidence inspector" and seen["focusIn"], seen
    assert seen["canvasInert"] and seen["railInert"] and seen["outside"] == 0, seen
    assert seen["closed"] and seen["after"]["inert"] == 0 and seen["focusBack"], seen


HIDDEN_TABLE = """
## Consumer readiness and command sheet

| Consumer | Command |
| --- | --- |
| Liquidity | Run HIDDENFIGUREUNIQUE next. |
"""


def with_hidden_table(text: str) -> str:
    """The synthetic CP-2 handoff with a table in a section written for another module."""
    marker = "\n## Next module"
    assert marker in text
    return text.replace(marker, HIDDEN_TABLE + marker, 1)


def test_a_section_written_for_another_module_is_not_a_figure_hit(tmp_path):
    """Round 2, H2 residual: the Figures group skips hidden sections, as the item map does."""
    page = synthetic_workspace(tmp_path, with_hidden_table)
    config = {"query": "consumer readiness"}
    seen = read_probe(page, f"#W-Overview?c={NEW_FORMAT_RUN}", 1280, SEARCH_AUDIT_PROBE, config)
    assert seen["hits"] == [], seen


ROUTE_CHROME_FAILURE_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('header.issuer h1'); i++) await sleep(50);
  window.Shapes.tableShape = () => { throw new Error('probe: cannot classify'); };
  window.updateWorkspaceChrome = () => { throw new Error('probe: no chrome'); };
  location.hash = PROBE.route;
  await sleep(700);
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    content: document.getElementById('content').innerText,
    link: document.querySelector('#content a[href="#W-Library/cases"]')?.textContent ?? null,
  });
  document.body.appendChild(out);
})();
"""


def test_the_route_failure_statement_does_not_depend_on_the_header_and_tabs(tmp_path):
    """Round 2: the stated failure is written first; a fault in the header code is logged apart."""
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    inject_probe(page, ROUTE_CHROME_FAILURE_PROBE, {"route": f"#CP-2/head?c={NEW_FORMAT_RUN}"})
    dom, console = visit(page, f"#W-Overview?c={NEW_FORMAT_RUN}")
    seen = probe_json(dom)
    assert "Couldn\u2019t present this page" in seen["content"] and seen["link"] == "Issuer library"
    assert any("The route could not be drawn" in line for line in console), console
    assert any("header and tabs could not be drawn" in line for line in console), console


EVIDENCE_HIT_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const seen = [];
  for (const href of PROBE.hrefs) {
    location.hash = href;
    await sleep(900);
    const row = /[?&]r=(\\d+)/.exec(href)[1];
    seen.push({href, marked: document.querySelectorAll('#ev-panel .is-hit').length,
      onCard: document.querySelectorAll(`#ev-panel [data-line="${row}"].is-hit`).length});
  }
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();
"""


def test_a_search_hit_on_the_sources_and_gaps_tabs_lands_on_and_marks_its_card(tmp_path):
    """Round 2: the file card and the gap card carry the handoff line a hit names."""
    page = synthetic_workspace(tmp_path, with_chart_and_event)
    probe = SEARCH_AUDIT_PROBE
    asked = {}
    for name, query in (("sources", "annual-report.pdf"), ("gaps", "No peer set supplied")):
        inject_probe(page, probe, {"query": query})
        dom, _ = visit(page, f"#W-Overview?c={NEW_FORMAT_RUN}")
        asked[name] = [
            h["href"] for h in probe_json(dom)["hits"] if f"W-Evidence/{name}" in h["href"]
        ]
        page.write_text(
            page.read_text().replace(
                '<script src="probe-config.js"></script><script src="probe.js"></script>', ""
            )
        )
        assert asked[name], (name, asked)
    hrefs = [href for found in asked.values() for href in found]
    seen = read_probe(
        page, f"#W-Overview?c={NEW_FORMAT_RUN}", 1280, EVIDENCE_HIT_PROBE, {"hrefs": hrefs}
    )
    for entry in seen:
        assert entry["marked"] == 1 and entry["onCard"] == 1, entry


RAGGED_ROW = """
### Ragged

| Item | Status |
| --- | --- |
| Covenant test | Passed | EXTRA |
| Only one |
"""


def with_ragged_table(text: str) -> str:
    """The synthetic CP-2 handoff with a ragged table (read as one unstructured block)."""
    marker = "\n## Calculations"
    assert marker in text
    return text.replace(marker, RAGGED_ROW + marker, 1)


def test_the_module_page_of_a_handoff_that_could_not_be_read_draws_no_raw_text(tmp_path):
    """Round 2: the audit fold states it and links the download; no raw text is drawn."""
    page = synthetic_workspace(tmp_path, with_ragged_table)
    dom, console = visit(page, f"#CP-2/head?c={NEW_FORMAT_RUN}")
    assert console == []
    assert "could not be read into sections. Its file is in the run" in html.unescape(dom)
    assert "SYNTHETIC FIXTURE" not in dom and "Covenant test" not in dom
    assert 'class="text-action" href="' in dom and "download" in dom
