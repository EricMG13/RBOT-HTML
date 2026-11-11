"""Reachability of every reference a handoff carries (ruling decisions 7 and 14, H3, H4, H7).

Each SYNTHETIC-*.md handoff is parsed with credit_os.store.parse_source, drawn by the page's own
prose and table renderer (reader.js, run under Node) and the rendered HTML is read back: every
Basis item must sit in the data of the control that opens it, every Source-column cell must be in
the rendered table. The expected counts are written by hand below from the Markdown (counted line
by line), not computed from the renderer.
"""

import html
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
from credit_os import store

FIXTURES = ROOT / "apps/issuer-library/fixtures/synthetic-new-format"
READER = ROOT / "apps/issuer-library/credit_os/web/reader.js"
OUT = "run/CP-X.md"

# basis_items: the items of every Basis line (items split on "; ").
# source_cells: cells under a column headed exactly "Source".
EXPECTED = {
    "SYNTHETIC-CP-0.md": {
        "basis_items": 0,
        "source_cells": 4,
    },  # Sources 2 + Source readiness register 2
    "SYNTHETIC-CP-1.md": {"basis_items": 0, "source_cells": 6},  # Sources 2 + facts C1-C4 4
    "SYNTHETIC-CP-1A.md": {
        "basis_items": 4,
        "source_cells": 11,
    },  # Basis lines 12,12,43-45,none = 4; Sources 2 + 9 events
    "SYNTHETIC-CP-2.md": {
        "basis_items": 10,
        "source_cells": 2,
    },  # lines 18:2 23:2 25:2 27:1 32:1 40:1 42:1; Sources 2
    "SYNTHETIC-CP-2D.md": {"basis_items": 0, "source_cells": 0},
}

RENDER = r"""
const reader = require(process.argv[1]);
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const ctx = {id: input.id, tables: true, chips: () => 0, caption: heading => heading};
if (input.earlier) {
  const view = b => reader.paragraphView(b.text, `${input.id}:${b.line}`, {earlier: true}).html;
  process.stdout.write(JSON.stringify(input.blocks.map(view)));
} else {
  process.stdout.write(JSON.stringify(input.sections.map(s => reader.sectionBodyHtml(s, ctx))));
}
"""


def render(payload: dict[str, Any]) -> list[str]:
    node = shutil.which("node")
    assert node, "node is required: the reachability test draws with the page's own reader.js"
    done = subprocess.run(
        [node, "-e", RENDER, str(READER)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    rendered: list[str] = json.loads(done.stdout)
    return rendered


class Page(HTMLParser):
    """The visible text, the Basis/figure controls and the tables of rendered HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self.controls: list[dict[str, str]] = []
        self.tables: list[dict[str, Any]] = []
        self._cell: list[str] | None = None
        self._row: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {name: value or "" for name, value in attrs}
        if tag == "button" and "data-paragraph" in a:
            self.controls.append(a)
        elif tag == "table":
            self.tables.append({"headers": None, "rows": []})
        elif tag == "tr":
            self._row = []
        elif tag in ("th", "td"):
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("th", "td") and self._cell is not None and self._row is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            table = self.tables[-1]
            if table["headers"] is None:
                table["headers"] = self._row
            else:
                table["rows"].append(self._row)
            self._row = None

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self._cell is not None:
            self._cell.append(data)


def read(markup: str) -> Page:
    page = Page()
    page.feed(markup)
    return page


def basis_items(text: str) -> list[str] | None:
    """The items of a block's Basis line (H3: last line, starts `Basis: `, items split on `; `)."""
    last = text.split("\n")[-1]
    if not last.startswith("Basis: "):
        return None
    return [
        i.strip() for i in last.removeprefix("Basis: ").removesuffix(".").split("; ") if i.strip()
    ]


def shown(cell: str) -> str:
    return "n.a." if cell in {"", "—", "–", "-", "Not supplied"} else cell


def basis_data(control: dict[str, str]) -> list[str]:
    items: list[str] = json.loads(html.unescape(control["data-basis"]))
    return items


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_every_reference_of_a_new_format_handoff_is_reachable(name: str) -> None:
    sections = store.parse_source((FIXTURES / name).read_text(encoding="utf-8"))
    pages = render({"id": OUT, "sections": sections})
    page = read("".join(pages))

    # (a) each paragraph's Basis items are the data of every control that opens it, in order,
    # as the handoff wrote them.
    found = 0
    for section in sections:
        for block in section["blocks"]:
            if block["type"] != "text":
                continue
            items = basis_items(block["text"])
            controls = [c for c in page.controls if c["data-paragraph"] == f"{OUT}:{block['line']}"]
            if items is None:
                assert not controls, f"{name}:{block['line']} has no Basis line but a control"
                continue
            assert controls, f"{name}:{block['line']} has Basis items and no control"
            for control in controls:
                assert basis_data(control) == items, f"{name}:{block['line']}"
            found += len(items)
    assert found == EXPECTED[name]["basis_items"]
    # No Basis line is printed as text.
    assert "Basis:" not in "".join(page.text)

    # (b) each Source-column cell is in the rendered table, in the same column and row.
    cells = 0
    for section in sections:
        for block in section["blocks"]:
            if block["type"] != "table" or "Source" not in block["headers"]:
                continue
            column = block["headers"].index("Source")
            drawn = next(t for t in page.tables if t["headers"] == block["headers"])
            assert [r[column] for r in drawn["rows"]] == [r["cells"][column] for r in block["rows"]]
            cells += len(block["rows"])
    assert cells == EXPECTED[name]["source_cells"]

    # Tables are drawn exactly as the handoff has them: same headers in the same order (none of
    # the app's), same rows.
    written = [b for section in sections for b in section["blocks"] if b["type"] == "table"]
    assert [t["headers"] for t in page.tables] == [b["headers"] for b in written]
    # A cell that says there is no value (empty, a dash, "Not supplied") is drawn as "n.a." with the
    # written text in its title: never as zero.
    assert [t["rows"] for t in page.tables] == [
        [[shown(c) for c in r["cells"]] for r in b["rows"]] for b in written
    ]


EARLIER = """# CP-1 handoff

## Findings

### Reader summary

| Bottom line | Confidence | Main limitation |
| --- | --- | --- |
| Leverage rose. | Medium | Synthetic. |

### Analysis

Net debt rose to 1,390 million [K, page:123]. Liquidity is ample [CP-1: D4, F1] [K, page:124].

Cash interest was 1,158 in FY2024 [K, page:123].

A bracket [mid-sentence] stays where it is.
"""


def test_earlier_format_citations_sit_behind_a_basis_control_not_in_the_sentence() -> None:
    sections = store.parse_source(EARLIER)
    analysis = next(s for s in sections if s["heading"] == "Analysis")
    blocks = [b for b in analysis["blocks"] if b["type"] == "text"]
    assert len(blocks) == 3
    drawn = render({"id": OUT, "earlier": True, "blocks": blocks})

    expected = [
        (
            ["[K, page:123]", "[CP-1: D4, F1]", "[K, page:124]"],
            "Net debt rose to 1,390 million. Liquidity is ample.",
        ),
        (["[K, page:123]"], "Cash interest was 1,158 in FY2024."),
        (
            [],
            "A bracket [mid-sentence] stays where it is.",
        ),  # not a trailing citation: wording untouched
    ]
    for markup, (items, sentence), block in zip(drawn, expected, blocks, strict=True):
        page = read(markup)
        # Every earlier-format paragraph has one Basis control and no figure button; each moved
        # citation is in its data.
        assert [c["data-paragraph"] for c in page.controls] == [f"{OUT}:{block['line']}"]
        assert 'class="basis-link"' in markup and 'class="figure"' not in markup
        assert basis_data(page.controls[0]) == items
        visible = re.sub(r"\s+", " ", "".join(page.text)).strip()
        assert visible == f"{sentence} Basis"
        for citation in items:
            assert citation not in visible
