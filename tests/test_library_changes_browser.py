"""The Changes tab in a real browser (headless Chrome), over a library built from two synthetic
runs of one issuer and pathway. The pack and CP-8's handoff are written by hand; every expected
string below is literal text from them. Needs Google Chrome or Chromium; skipped without one."""

import json
import re
import sys
from pathlib import Path

import pytest
from library_fixtures import CITED, make_run, method, with_changes, without_report  # noqa: F401
from test_credit_os_catalogue import CHARTS
from test_library_page_browser import read_probe, visit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library

pytestmark = pytest.mark.browser

NOTE = "changes: not produced — cpos_live_not_accepted: CP-8 not accepted within bounds"
BOTTOM = (
    "The credit picture is about the same since the earlier run, and the change is the analysis."
)
EVIL = "<script>window.hit=1</script>"
PACK = {
    "schema": "cpos-changes/2",
    "prior": {
        "run": "nbg-2024-09-30-credit_snapshot",
        "as_of": "2024-09-30",
        "pathway": "credit_snapshot",
        "format": "earlier",
        "methods_changed": [],
    },
    "current": {"as_of": "2025-03-31", "pathway": "credit_snapshot", "format": "current"},
    "measures": [
        {
            "key": "leverage",
            "label": "Total debt / EBITDA",
            "unit": "x",
            "comparable": "judge",
            "reason": "the label or definition text differs; CP-8 judges",
            "prior": {
                "label": "Total debt / EBITDA",
                "unit": "x",
                "value": "6.57",
                "period": "FY2024",
            },
            "current": {
                "label": "Total debt / EBITDA",
                "unit": "x",
                "value": "6.01",
                "period": "FY2025",
            },
            "difference": "-0.56",
            "same_period": False,
        },
        {
            "key": "cash",
            "label": "Cash",
            "unit": "US$m",
            "comparable": "yes",
            "reason": "",
            "prior": {"label": "Cash", "unit": "US$m", "value": "6261", "period": "2024-09-30"},
            "current": {"label": "Cash", "unit": "US$m", "value": "6300", "period": "2025-03-31"},
            "difference": "39",
            "same_period": False,
        },
    ],
    "omitted": {"net_debt_change": "gross debt is not stated in either run"},
    "modules": [
        {
            "module": "CP-2",
            "title": "Fundamental credit",
            "ran_prior": True,
            "ran_current": True,
            "prior_bottom_line": "CP-2 earlier view.",
            "current_bottom_line": f"CP-2 current view {EVIL}.",
        }
    ],
    "limitations": {"earlier": [], "current": []},
}
CP8 = f"""# CP-8 Changes since the last run

## Findings

### Bottom line

{BOTTOM}
Basis: CP-1 handoff.

### Key findings

- Cash is USD 6,300 million.

### Contrary evidence and what would change the view

None.

### Limitations

None.

### What changed: the issuer

| Measure or fact | Earlier | Current | Cause | Effect on the credit view |
| --- | --- | --- | --- | --- |
| Total debt / EBITDA | 6.57x (FY2024) | 6.01x (FY2025) | Unresolved | Not comparable. |
| Cash | 6261 US$m (2024-09-30) | 6300 US$m (2025-03-31) | New period | Same definition. |

### What changed: the analysis

| Module | Status | Cause | Why |
| --- | --- | --- | --- |
| Fundamental credit (CP-2) | Unchanged | Presentation | The headings differ only. |

### Limitations ledger

| Earlier ref | Current ref | Limitation | Status | What closed it |
| --- | --- | --- | --- | --- |
| E1 | — | An earlier limitation. | No longer stated | — |
| — | C1 | A current limitation. | New | — |

## Gaps

None.
"""


@pytest.fixture(autouse=True)
def stand_in_method(monkeypatch):
    monkeypatch.setattr("deploy_workflow.library_index.current_method", lambda: method())


def run_of(workspace: Path, folder: str, **spec) -> Path:
    return without_report(make_run(workspace, folder, **spec)).parent.parent


def build(workspace: Path) -> Path:
    update_library.update_library(workspace)
    return workspace / "library/index.html"


def two_runs(workspace: Path, *, pack=True, note=None) -> None:
    run_of(
        workspace, "earlier", as_of="2024-09-30", modules=("CP-0", "CP-1", "CP-2"), cp1_extra=CHARTS
    )
    now = run_of(
        workspace,
        "later",
        as_of="2025-03-31",
        modules=("CP-0", "CP-1", "CP-2", "CP-8"),
        cp1_extra=CHARTS,
        cp8=CP8,
    )
    with_changes(now, pack=json.dumps(PACK).encode() if pack else None, note=note)


def tab_names(dom: str) -> list[str]:
    tabs = re.search(r'<div class="workspace-tabs[^"]*"[^>]*>(.*?)</div>', dom, re.DOTALL).group(1)
    return re.findall(r"<a [^>]*>(?:<img[^>]*>)?([A-Za-z ]+)</a>", tabs)


def test_the_changes_tab_sits_between_overview_and_modules_and_shows_the_comparison(tmp_path):
    two_runs(tmp_path)
    page = build(tmp_path)
    dom, console = visit(page, "#W-Changes/changes?c=later")
    assert console == []
    assert tab_names(dom) == ["Report", "Overview", "Changes", "Modules", "Forecast", "Evidence"]
    assert re.search(r'<a href="#W-Changes/changes[^"]*" aria-current="page"', dom)
    assert "Since 30 September 2024 · Full credit assessment" in dom
    assert BOTTOM in dom and "Cash is USD 6,300 million." in dom
    # Part 2: values as the pack writes them, drawn as the earlier and current side of a card;
    # leverage is Not comparable and shows no difference on the route or in Evidence.
    assert (
        '<p class="chg-v">6.57x (FY2024)</p>' in dom
        and '<p class="chg-v">6.01x (FY2025)</p>' in dom
    )
    assert "-0.56" not in dom
    assert '<p class="chg-v">6261 US$m (2024-09-30)</p>' in dom
    assert '<p class="chg-v">6300 US$m (2025-03-31)</p>' in dom
    # The computed difference is Evidence's: listed there only where the measure is comparable.
    evidence, console = visit(page, "#W-Evidence/calculations?c=later&m=CP-8")
    assert console == []
    assert (
        '<td class="">Total debt / EBITDA</td><td class="">6.57x (FY2024)</td>'
        '<td class="">6.01x (FY2025)</td><td class="">\u2014</td>'
    ) in evidence
    assert (
        '<td class="">Cash</td><td class="">6261 US$m (2024-09-30)</td>'
        '<td class="">6300 US$m (2025-03-31)</td><td class="">39 US$m</td>'
    ) in evidence
    assert "-0.56" not in evidence
    # Part 3 and 5: the module row, and Over time with both runs, earliest first.
    assert 'change-status">Unchanged</span>' in dom
    over = dom[dom.index('id="changes-over-time"') :]
    assert over.index("30 September 2024") < over.index("31 March 2025")
    assert "Fundamental credit bottom line." in over
    # Model output is text, never markup.
    assert "window.hit" not in dom.replace("&lt;script&gt;window.hit=1&lt;/script&gt;", "")
    assert "<script>window.hit=1" not in dom


def test_a_first_run_says_so_and_shows_nothing_else(tmp_path):
    with_changes(run_of(tmp_path, "only", as_of="2025-03-31"), first=True)
    dom, console = visit(build(tmp_path), "#W-Changes/changes?c=only")
    assert console == []
    assert tab_names(dom)[2] == "Changes"
    assert "<li>First run of this pathway</li>" in dom
    assert 'class="empty-state" role="status"' in dom
    for part in ("changes-issuer", "changes-analysis", "changes-over-time", "changes-heading"):
        assert part not in dom


def test_a_cp8_that_was_not_produced_says_so_with_its_reason(tmp_path):
    two_runs(tmp_path, pack=False, note=NOTE)
    dom, console = visit(build(tmp_path), "#W-Changes/changes?c=later")
    assert console == []
    assert "The explanation of what changed was not produced for this run." in dom
    assert (
        "Recorded reason: cpos_live_not_accepted: "
        "Changes since the last run not accepted within bounds" in dom
    )
    assert 'id="changes-what"' not in dom
    assert 'id="changes-over-time"' in dom


def test_a_run_with_no_recorded_comparison_is_not_called_a_first_run(tmp_path):
    run_of(tmp_path, "old", as_of="2025-03-31")
    dom, console = visit(build(tmp_path), "#W-Changes/changes?c=old")
    assert console == []
    assert "No comparison was recorded for this run" in dom
    assert "First run of this pathway" not in dom


def test_over_time_joins_two_runs_the_pack_names_by_run_folder(tmp_path):
    """The pack names the earlier run by its folder, as the run start service names folders (not by
    the manifest's run_id); a line joins the points where the later pack compares exactly them."""
    run_of(
        tmp_path,
        "20261101-090000-01",
        as_of="2024-09-30",
        modules=("CP-0", "CP-1", "CP-2"),
        cp1_extra=CHARTS,
    )
    now = run_of(
        tmp_path,
        "20261112-090000-01",
        as_of="2025-03-31",
        modules=("CP-0", "CP-1", "CP-2", "CP-8"),
        cp1_extra=CHARTS,
        cp8=CP8,
    )
    held = {"label": "Cash", "unit": "US$m", "value": "6261", "period": "2024-09-30"}
    cash = {**PACK["measures"][1], "prior": held, "current": held, "difference": "0"}
    pack = {**PACK, "prior": {**PACK["prior"], "run": "20261101-090000-01"}, "measures": [cash]}
    with_changes(now, pack=json.dumps(pack).encode())
    dom, console = visit(build(tmp_path), "#W-Changes/changes?c=20261112-090000-01")
    assert console == []
    over = dom[dom.index('id="changes-over-time"') :]
    assert over.count("<line ") == 1


def test_no_module_code_reaches_a_reader_from_the_changes_tab(tmp_path):
    """Owner ruling 2026-11-12: the Changes tab names modules and never shows a code. The answer
    key is the library page's codes probe (it scans the Changes route among its routes, text,
    `title` and `aria-label`, folds opened) over a run that has CP-8's pack and handoff."""
    from test_library_page_browser import read_codes_probe

    two_runs(tmp_path)
    page = build(tmp_path)
    dom, console = visit(page, "#W-Changes/changes?c=later")
    assert console == []
    assert 'id="changes-issuer"' in dom and 'id="changes-analysis"' in dom
    seen = read_codes_probe(page, "later", "#CP-2/head?c=later")
    assert seen["hits"] == []


def with_one_model(page: Path) -> None:
    """List one forecast model for the later run, so its Forecast page and chart index are drawn."""
    data_js = page.parent / "data.js"
    prefix = "window.CREDIT_OS_DATA="
    data = json.loads(data_js.read_text(encoding="utf-8").removeprefix(prefix).rstrip().rstrip(";"))
    run = data["workspace"]["runs"]["later"]
    data["workspace"]["models"] = [
        {
            "id": "model-a",
            "issuerKey": run["issuerKey"],
            "mode": "accepted",
            "qualification": "unrun",
            "runId": None,
            "runFolder": "later",
            "scope": None,
            "inputContract": None,
            "revisionNote": None,
            "previous": None,
            "href": "../models/model-a.html?embedded=1",
            "download": "../models/model-a.html?download=1",
            "files": [],
            "sources": [],
            "register": None,
            "cashflow": None,
        }
    ]
    data_js.write_text(prefix + update_library.embedded_json(data) + ";\n", encoding="utf-8")


TRACE_PROBE = """
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const seen = {};
  for (const [name, route, selector] of PROBE.routes) {
    location.hash = route;
    await sleep(900);
    const control = document.querySelector(selector);
    const entry = {found: Boolean(control)};
    if (control) {
      control.click();
      await sleep(600);
      const drawer = document.getElementById('inspector');
      entry.open = !drawer.hidden;
      entry.title = drawer.querySelector('.inspector-body h3')?.textContent ?? '';
      entry.text = drawer.innerText.length;
      entry.hash = location.hash;
    }
    seen[name] = entry;
    location.hash = route;
    await sleep(300);
  }
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();
"""


def test_a_trace_control_opens_the_drawer_on_every_findings_route(tmp_path):
    """Review H1: a trace key opens on any route of its run, not only on a route with an output.
    The Forecast chart index keeps its own route when its control is used."""
    two_runs(tmp_path)
    page = build(tmp_path)
    with_one_model(page)
    routes = [
        ["overview", "#W-Overview/overview?c=later", "#content .basis-link"],
        ["module", "#CP-0/head?c=later", "#content .basis-link"],
        ["changes", "#W-Changes/changes?c=later", "#content .trace-row"],
        ["forecast", "#W-Forecast/run-charts?c=later", "#content .trace-row"],
    ]
    seen = read_probe(page, "#W-Overview/overview?c=later", 1280, TRACE_PROBE, {"routes": routes})
    for name, entry in seen.items():
        assert entry["found"] and entry["open"] and entry["text"] > 0 and entry["title"], (
            name,
            entry,
        )
    assert "Total debt / EBITDA" in seen["changes"]["title"], seen["changes"]
    assert seen["forecast"]["hash"].startswith("#W-Forecast/run-charts?"), seen["forecast"]
    assert "e=" in seen["forecast"]["hash"], seen["forecast"]


def test_report_history_links_what_changed_only_for_a_run_with_a_comparison_record(tmp_path):
    """Review L7: an earlier listed run of the same pathway is not a comparison; the link is drawn
    only where the run's own record holds one."""
    two_runs(tmp_path)
    run_of(
        tmp_path, "latest", as_of="2025-06-30", modules=("CP-0", "CP-1", "CP-2"), cp1_extra=CHARTS
    )
    dom, console = visit(build(tmp_path), "#W-Report/history?c=later")
    assert console == []
    asked = re.findall(r'aria-label="(What changed in the run of [^"]+)"', dom)
    assert len(asked) == 1 and asked[0].startswith("What changed in the run of 31 March 2025"), (
        asked
    )
