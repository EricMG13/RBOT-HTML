"""The standalone HTML file rendered by `deploy_vii.render` names modules, not module codes, in its
own navigation and headings (owner ruling 2026-11-12), read in real headless Chrome.

The probe is appended to the rendered file as an inline script (the file's policy allows inline
scripts and nothing else), walks every route the navigator and the rail reach, and writes what it
read to a `<pre id="probe">`. Body content (claims, tables, limitation text) is not scanned."""

import hashlib
import html
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from test_library_page_browser import visit

from deploy_vii.contracts import (
    Citation,
    Fact,
    ModuleView,
    ReportTable,
    Run,
    TableColumn,
    TableRow,
    View,
)
from deploy_vii.render import empty_view, render

pytestmark = pytest.mark.browser

# Hand-written answer key: titles the fixture gives and the words the page owes for them.
MODEL = "Synthetic data foundation"
LIQUIDITY = "Synthetic liquidity bridge"
OUTSIDE = "Synthetic outside module"
UNNAMED = "Unnamed module"  # CP-3 is given its own code as its title
LIMIT_TEXT = "Synthetic liquidity limitation."

PROBE = r"""(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const code = /\bCP-[A-Z0-9]+\b/;
  const out = {hits: [], routes: {}, filter: null, field: null, nav: [], outside: []};
  const attrs = el => [el.getAttribute("title") || "", el.getAttribute("aria-label") || ""];
  const scan = (where, root) => {
    const values = [];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    if (root.nodeType === 1) values.push(...attrs(root));
    while (walker.nextNode()) {
      const n = walker.currentNode;
      values.push(...(n.nodeType === 3 ? [n.data] : attrs(n)));
    }
    values.filter(v => code.test(v)).forEach(v => out.hits.push(where + ": " + v.slice(0, 80)));
  };
  for (let i = 0; i < 100 && !document.querySelector("#module-list a"); i++) await sleep(50);
  const links = [...document.querySelectorAll("#module-list a, #nav-foot a, [data-dest]")];
  const hashes = [...new Set(links.map(a => a.getAttribute("href")))];
  const rowOf = a => ({href: a.getAttribute("href"), text: a.textContent.trim()});
  out.nav = [...document.querySelectorAll("#module-list a")].map(rowOf);
  out.outside = [...document.querySelectorAll("#nav-foot a")].map(rowOf);
  for (const hash of hashes) {
    location.hash = hash; await sleep(60);
    const where = hash;
    const rec = {h1: document.querySelector("#view-root h1").textContent};
    scan(where + " navigator", document.getElementById("navigator"));
    scan(where + " rail", document.getElementById("rail"));
    scan(where + " h1", document.querySelector("#view-root h1"));
    const titles = [...document.querySelectorAll("#view-root section.block > header h2")];
    rec.panels = titles.map(h => h.textContent);
    titles.forEach(h => scan(where + " panel title", h));
    const table = [...document.querySelectorAll("#view-root table")]
      .find(t => t.querySelector("caption").textContent === "Current report coverage");
    if (table) {
      scan(where + " coverage", table);
      rec.coverageHead = [...table.querySelectorAll("th")].map(c => c.textContent);
      rec.coverage = [...table.querySelectorAll("tbody tr")].map(tr => ({
        cells: [...tr.children].map(c => c.textContent),
        href: (tr.querySelector("a") || {getAttribute: () => null}).getAttribute("href")}));
    }
    const fact = document.querySelector("#view-root .fact-value");
    if (fact) {
      fact.click(); await sleep(60);
      const dts = [...document.querySelectorAll("#inspector-content dt")];
      const field = dts.find(dt => dt.textContent === "Field");
      if (field) {
        const value = field.nextElementSibling;
        out.field = value.textContent; scan(where + " field", value);
      }
    }
    out.routes[hash] = rec;
  }
  location.hash = "#front"; await sleep(60);
  const input = document.getElementById("module-filter");
  input.value = "cp-2d"; input.dispatchEvent(new Event("input")); await sleep(60);
  out.filter = [...document.querySelectorAll("#module-list a")].map(rowOf);
  const pre = document.createElement("pre"); pre.id = "probe";
  pre.textContent = JSON.stringify(out);
  document.body.append(pre);
})();"""


def fixture_view() -> View:
    run = Run(
        run_id="shell-test",
        issuer_id="SYN",
        issuer_name="Synthetic Issuer",
        as_of=date(2024, 9, 30),
        case_kind="synthetic",
        pathway="credit_snapshot",
        requested_modules=("CP-1", "CP-2D", "CP-3"),
    )
    base = empty_view(run)
    sha = hashlib.sha256(b"synthetic").hexdigest()
    fact = Fact(
        fact_id="f1",
        label="Synthetic revenue",
        table_id="T4.4",
        row_id="revenue",
        field="value",
        amount=Decimal(1200),
        unit="US$m",
        period="FY2024",
        citations=(
            Citation(source_id="S1", source_sha256=sha, locator="p.1", quote="Synthetic quote."),
        ),
    )
    table = ReportTable(
        table_id="T4.4",
        title="Synthetic revenue",
        columns=(TableColumn(field="value", label="Value"),),
        rows=(TableRow(row_id="revenue", label="Total", fact_ids=("f1",)),),
        row_header="Measure",
    )
    changes: dict[str, dict[str, object]] = {
        "CP-1": {
            "title": MODEL,
            "status": "candidate",
            "artifact_sha256": sha,
            "facts": (fact,),
            "tables": (table,),
        },
        "CP-2D": {"title": LIQUIDITY, "status": "restricted", "limitations": (LIMIT_TEXT,)},
        "CP-1B": {"title": OUTSIDE},
        "CP-3": {"title": "CP-3"},
    }
    modules = tuple(
        ModuleView.model_validate(item.model_dump() | changes.get(item.module_id, {}))
        for item in base.modules
    )
    return base.model_copy(update={"modules": modules})


@pytest.fixture(scope="module")
def seen(tmp_path_factory) -> dict:
    page: Path = tmp_path_factory.mktemp("shell") / "model.html"
    text = render(fixture_view())
    assert "</body>" in text
    page.write_text(text.replace("</body>", f"<script>{PROBE}</script></body>"), encoding="utf-8")
    dom, console = visit(page)
    assert console == []  # No script error and no policy violation.
    return json.loads(html.unescape(re.search(r'<pre id="probe">(.*?)</pre>', dom, re.DOTALL)[1]))


def test_no_module_code_in_the_shells_own_navigation_and_headings(seen):
    assert seen["hits"] == []
    assert len(seen["routes"]) > 10  # Every navigator row, the outside list and the rail.


def test_navigator_rows_name_the_module_and_keep_the_code_in_the_link(seen):
    rows = {row["href"]: row["text"] for row in seen["nav"] + seen["outside"]}
    assert MODEL in rows["#CP-1"] and LIQUIDITY in rows["#CP-2D"]
    assert UNNAMED in rows["#CP-3"] and OUTSIDE in rows["#CP-1B"]
    assert all(href.startswith("#CP-") for href in rows if href != "#front")


def test_page_heading_is_the_module_title(seen):
    heads = {route: item["h1"] for route, item in seen["routes"].items()}
    assert heads["#CP-1"] == MODEL and heads["#CP-2D"] == LIQUIDITY
    assert heads["#CP-3"] == UNNAMED and heads["#CP-1B"] == OUTSIDE


def test_coverage_table_is_module_and_status_with_the_title_as_the_link(seen):
    analysis = seen["routes"]["#analysis"]
    assert analysis["coverageHead"] == ["Module", "Status"]
    by_href = {row["href"]: row["cells"] for row in analysis["coverage"]}
    assert by_href["#CP-1"][0] == MODEL and by_href["#CP-2D"][0] == LIQUIDITY
    assert by_href["#CP-3"][0] == UNNAMED and by_href["#CP-1B"][0] == OUTSIDE
    assert all(len(cells) == 2 for cells in by_href.values())


def test_limitation_panel_is_titled_with_the_module(seen):
    assert LIQUIDITY in seen["routes"]["#limitations"]["panels"]


def test_inspector_field_row_names_the_module_title(seen):
    assert seen["field"] == f"{MODEL} / T4.4 / revenue / value"


def test_typing_a_code_into_the_filter_still_finds_the_module(seen):
    assert [row["href"] for row in seen["filter"]] == ["#CP-2D"]
