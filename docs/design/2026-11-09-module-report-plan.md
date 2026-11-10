# Module report with source chips — implementation plan

Spec: `docs/design/2026-11-09-module-report-spec.md`. Mockup: `docs/design/mockups/module-report.html`.
Branch: `claude/deploy-info-architecture-review-47e09f` (contains `feat/credit-os-static-pages`).
Owner, 2026-11-09: "apply the new report design to each handoff as it arrives".

## Global constraints (every brief and review)

- Static pages: no `fetch`, no `setInterval`, no dependency; open from `file://`.
- Python computes, the page draws. No inferred pages, classes, dates or judgements in JS.
- No stub or fake value standing in for real behaviour; no catch-all hiding a failure unless the
  fail-open is documented and logged (the existing `moduleBody` catch is the one allowed).
- Answer keys live in tests and fixtures the implementer does not edit; comparisons are not weakened.
- Gates: `uv run python tools/quality_gate.py --base main` (changed Python), targeted
  `timeout 300 uv run pytest <files> -q`, `node --test apps/issuer-library/credit_os/web/*.test.cjs`.
- Edits to copied Credit OS files are recorded in `apps/issuer-library/credit_os/SOURCE.md`.
- Each report ends with `Not verified:`.

## Data shapes already in `data.js` (`window.CREDIT_OS_DATA`)

- `workspace.outputs[<id>]`: `id` = `<run folder>/<relative path>` e.g.
  `cpos-tdg-sol-high-cp2-001/deliveries/<hash>/CP-1.md`; fields `module`, `run`, `label`, `href`,
  `sha256`, `sections`, `summary {bottomLine,line,...}`, `call`, `basis`.
- `workspace.handoffs[<sha256>]`: parsed sections `[{heading, level, line, blocks:[{type:'table',
  line, headers, rows:[{line, cells}]} | {type:'text', line, end, text}]}]`.
- The page's `evidence` Map is keyed `${outputId}:${line}` (screen.js:51-63).

## Task 1 — Python citation resolver → `chips` in data.js

**Files:** create `src/deploy_workflow/credit_os_chips.py`; modify
`apps/issuer-library/update_library.py` (`build_into`: `data["chips"] = chips(...)`); create
`tests/test_credit_os_chips.py`; extend `tests/library_fixtures.py` only by adding a fixture
handoff text constant with citations (do not change existing fixture behaviour).

**Interfaces (produce):**
```python
Locator = TypedDict: kind: Literal["issuer_page","upstream","gap"], source: str|None,
          page: int|None, page_end: int|None, module: str|None, codes: tuple[str,...]
def parse_locators(text: str) -> list[Locator]
    # "K, page:118" -> issuer_page K 118; "K, pages 31-32" -> 31..32; "page:123" with no key
    # -> the last key named earlier in the same text, else gap; "[CP-1: D4, F1]" -> upstream
    # CP-1 codes (D4,F1); trailing register codes "D1, D3, E1." at the end of a cell -> upstream
    # of the module itself (module=None, codes). Never guesses beyond these patterns.
def inventory(cp0_sections) -> dict[str, tuple[str, str]]
    # From CP-0's table whose heading starts "Complete supplied inventory": key -> (file, sha256).
def chips(run_dir: Path, output_id: str, module: str, sections, inv) -> dict[str, list[dict]]
    # key f"{output_id}:{line}" for every table row and text block that yields >=1 locator;
    # chip dicts per spec: kind, source, file, sha256, hash_matches_inventory, page, page_end,
    # quote, quote_found, excerpt (<=600 chars of the page text around the quote, or the page
    # start), module, codes, line. A "Not supplied" cell -> one gap chip labelled "Not supplied".
```
Page text comes from `run_dir/source-text/<file>` JSONL records `{"page": n, "text": ...}`;
`hash_matches_inventory` = sha256 of that file equals the inventory hash. `quote` = the first
“…” span in the cell, else the first numeric cell value (thousands separators tolerated);
`quote_found` = that string occurs in the page text (digits compared with separators stripped).

**Tests (answer keys written in the test from the fixture, not from the code):**
`parse_locators("K, page:118 states …")` → `[issuer_page K 118]`; `"M, pages 31-32"` →
`(31,32)`; `"…K, page:120 … page:123"` → two K chips; `"[CP-1: D4, F1]"` → upstream CP-1
`("D4","F1")`; `"… basis. D1, D3, E1."` → upstream None `("D1","D3","E1")`; `"Not supplied: x"`
→ gap "Not supplied"; a cell with none → `[]`. `chips(...)` on a fixture run whose
`source-text/K.jsonl` has page 123 containing `Cash paid during the period for interest, net
$ 1,158` → `quote_found` true for a row quoting `1,158`/`1158`, false for `1,159`;
`hash_matches_inventory` false after one byte of the file changes. `update_library` writes
`chips` into `data.js` and the key for the fixture row exists.

## Task 2 — Module canvas, chips and inspector

**Files:** modify `apps/issuer-library/credit_os/web/screen.js` (`renderContent` for analytical
outputs, `showInspector`, `renderNavigator`), `views.js` (`outlineMarkup` → anchors; a new
`moduleReport(id)`), `screen.css` (chip, finding, limits, audit styles from the mockup);
`static.test.cjs`; `SOURCE.md`.

**Behaviour:** for an analytical module with an output, `renderContent(id, section)` returns the
six-part canvas regardless of `section`; `section` becomes the anchor scrolled to:
`head`, `bottom-line`, `numbers`, `findings`, `limits`, `audit`. Workspace tabs (W-*) and
the module chooser/unavailable views are unchanged.
1. Head: name, code, "Current methodology", handoff file and line count; right: acceptance badge
   from `catalogue.real[*].artifacts` (grey "Candidate · not accepted" unless the catalogue marks
   acceptance), the existing output selector, Handoff download. No output: the existing
   `unavailableView` text replaced by one sentence "No output found" (and the navigator state
   word matches).
2. Band: existing `callBand` (summary quoted once) plus footer "Quoted from the handoff ·
   <file> · line <n>". Remove the duplicate "Reader summary" prose from the canvas (it stays in
   Evidence & audit).
3. Analytical panel: existing `readerCharts` output for the module's chart-data tables, each
   chart row ending in `chipsMarkup(key)`; then a key-numbers table from the module's first
   reader table that has ≥2 numeric columns, capped at 8 rows × 6 columns (further rows go to
   Evidence & audit), empty cells `n.a.` with `title`.
4. Findings: the `Finding | Creditor impact | Confidence` table rows → `<article class="finding">`.
5. Limits: sections `sectionGroups` puts under "Limits & monitoring" rendered as two columns of
   text blocks with chips.
6. `<details class="audit">`: every other section as `L<line>` list items linking to the
   existing section rendering (lazy: render on open).
Chips: `chipsMarkup(key)` reads `window.CREDIT_OS_DATA.chips[key]`; markup per mockup
(`.chip`, `.av`, `.dot`); label `p.<page>` / `L<line>` / codes / `Not supplied` / `no page`.
Click → `showInspector(key, chipIndex)`: existing inspector content, then "Source page · <file
title> p.<n>" with the excerpt and `<mark>` on the quote, badges "Matches publication" /
"Changed since inventory" (amber) and "Quote found on page" / "Quote not found" (amber),
"Open source file" link to `source-text/<file>` via the run's href root. Esc / Back restore focus.

**Tests (`node --test`):** static assertions on the built markup via the existing jsdom-free
pattern (string checks on rendered functions where the suite already does so, else on source):
the canvas has the six anchors in order; no `—` text in a table cell for the fixture; every
`.chart-row` contains a `<strong>` with text; the no-output state is one sentence; `screen.css`
has no `font-size` below 11px; chips with `kind==='gap'` render `Not supplied`/`no page`.
Browser (`tests/test_library_page_browser.py` pattern, `file://`, 1440 and 1280): no horizontal
overflow (`scrollWidth<=clientWidth`), chart value column inside its card, chip click opens the
inspector with `.excerpt`, Escape returns focus to the chip.

## Task 3 — Chart-row widths and hedge-chart constants

**Files:** `screen.css` (`.chart-row` → `minmax(150px,1.1fr) minmax(140px,2fr) 72px auto`;
`.summary-chart` loses `overflow:hidden`), `views.js` `hedgeChart` (axis start = earliest date
in the table or 18 months before as-of, end = latest or 36 months after, base rule = the run's
as-of from `contexts[context].asOf`; unit from the table's unit column; no literal dates),
`static.test.cjs` (no `2024-09-30`, `Mar 2023`, `Sep 2027`, `'FX forwards'` literals in
views.js).

## Task 4 — Rebuild and check

`uv run python apps/issuer-library/update_library.py --workspace ~/Documents/RBOT-HTML` after
each task; open `library/index.html` at 1440 and 1280; for each module output in the listed runs
(two sol-high runs now; `cpos-tdg-sol-medium-all-001` when CP-OS completes it) confirm the six
parts render and chips resolve; record counts (chips by kind, quote_found rate) in the report.
Whole-branch review (`mx-architect`), then the quality gate and both node suites.
