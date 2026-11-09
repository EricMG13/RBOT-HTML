# Run Report, Phase A — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The Overview becomes a run report that leads with what the run established, and each
module page separates its narrative from its registers, calculations and audit text.

**Architecture:** Python (`store.py`) adds three fields to every output record: `state`,
`placement` (one part name per handoff section) and `words`. `views.js` draws both pages from
those fields and classifies nothing itself. `screen.js` only routes, opens closed parts and filters
the register.

**Tech Stack:** Python 3 (uv, pytest), plain browser JavaScript evaluated by `node --test`,
headless Chrome on `file://`. No new dependency.

**Spec:** `docs/design/2026-11-09-run-report-spec.md` (Phase A only). Background:
`docs/design/2026-11-09-run-page-content-review.md`.

## Global Constraints

- Every sentence on either page is a handoff cell verbatim. Counts come from Python fields.
- Python computes, the page draws: no placement, status, date or judgement inferred in JS.
- The page makes no network request and opens from `file://` (`static.test.cjs` forbids `fetch(`
  and `setInterval(`). No `font-size` below 11px in `screen.css`. Nothing is truncated.
- No stub or fake value standing in for real behaviour. No catch-all that hides a failure unless
  the fail-open is documented and logged.
- Answer keys in this plan (tables, strings, counts) are not edited by the implementer, and no
  comparison is weakened. A key that looks wrong is reported, not changed.
- Never write under `~/Documents/RBOT-HTML/runs` or `~/Documents/RBOT-HTML/library`; copy nothing
  from `runs` into the repo. No credential files; no provider call.
- Agents: `mx-feature` implements, `mx-precise` reviews each task and saves each probe as a script,
  `mx-architect` reviews the branch. At most two Sonnet fix rounds per task. Every report ends with
  `Not verified:`. Ledger line: `agent=<name> fix-rounds=<n> gates-first-pass=<y|n|n/a>`.
- Per task run only: `uv run pytest <files named in the task> -q` (Bash timeout 300 s; there is
  no `timeout` binary) and `node --test apps/issuer-library/credit_os/web/static.test.cjs`.
- Edits to copied Credit OS files are recorded in `apps/issuer-library/credit_os/SOURCE.md` under
  the ruling numbers below. Commit per task on this branch; no merge, no push.
- GitNexus: this repository is not indexed, so `impact` and `detect_changes` do not apply.
- Out of scope: Phase B and everything under "Not in this spec".

## Pre-flight (run 2026-11-09 on 5d994c0) and rulings

| # | Finding | Ruling |
|---|---|---|
| R34 | All 29 outputs of the four retained runs use the level-2 skeleton `Request, Sources, Findings, Calculations, Gaps, Next module`. | A section under any other level-2 heading is placed `audit`. |
| R35 | `Confidence` is only ever `Medium`, `Low`, `High` or exactly `Not assessable`. | Not established = the cell, stripped and case-folded, starts with `not assessable`. |
| R36 | The spec's method-code regex misses `C.1 — `, `T4.D1 — ` and `TDR.1 — ` (66 of 447 headings matched; 71 with the wider form). | Use `/^([A-Z][A-Z0-9]*\.[A-Z]?\d+\|[a-z0-9]+(\.[a-z0-9_]+)+)\s+—\s+/`. **Owner may overrule before Task 3.** |
| R37 | Own-heading and ancestor evidence rules give identical `words` on all 20 modules. | Keep the ruled R31a ancestor rule, under `Findings` only. |
| R38 | Handoff sections are stored once per digest. | `placement` lives on the output record, parallel to its sections. |
| R39 | The fixture handoff ends with `## Sources`, so text appended by `cp1_extra` would now be `audit`. | Add `RunSpec.cp1_findings`, inserted before `## Sources`. Tests that read Analysis, Reference or key numbers pass their tables through it; each expected line number in them moves by exactly −2 and nothing else changes. `ANALYSIS_ROWS`' `## Credit analysis` becomes `### Credit analysis`. |
| R40 | The spec fixes no route for a section or for the citation count. | Section route `#<module>/s-<line>`; count route `chip=gaps`; not-assessable fold anchor `handoff-text`. |
| R41 | An output without a Reader summary does not occur in the retained runs. | It keeps the full module page (no band, no findings) and one line `<name> · No reader summary` on the run report. |

Census key (medium-all run): `words` for CP-1 = view 746, reference 3,000, calculations 1,145,
limits 940, audit 972; CP-2E = 806, 4,103, 731, 408, 652. Finding rows: 33 established, 84 in all.

## Review Focus

1. An output with no Reader summary (`established: null`) → run report and module page still
   render, and the count line says `1 without a reader summary`. Tests: Task 3 step 1 (d), Task 4.
2. Confidence written `not assessable.` or ` Not Assessable` → not established. Test: Task 1.
3. A level-2 heading outside the skeleton → `audit`, counted in `words.audit`, still listed in
   Evidence & audit. Tests: Task 1 (`Extra notes`), Task 3 step 1 (h).
4. A link with `e=<key>` to a row inside a closed part → the part opens, the inspector opens, Esc
   returns focus to that chip. Test: Task 3 step 5.
5. A module the reading groups do not name → appears under `Other modules` in the strip, story,
   register, open items and matrix. Test: Task 4 (`CP-X`).

---

### Task 1: `state`, `placement`, `words` in the store

**Files:**
- Modify: `apps/issuer-library/credit_os/store.py` (new functions beside `reader_fields`, line 510;
  call at line 674), `tests/library_fixtures.py` (`RunSpec`, lines 68–117)
- Test: `tests/test_credit_os_store.py`, `tests/test_update_library.py`

**Interfaces:**
- Produces, on every `workspace.outputs[id]`:
  `state: {"established": bool | None, "declared": str | None}`;
  `placement: list[str]`, one of `consumed | view | reference | calculations | limits | audit`
  per section of `workspace.handoffs[sha256]`, same order;
  `words: {"view": int, "reference": int, "calculations": int, "limits": int, "audit": int}`.
- Produces: `RunSpec.cp1_findings: str = ""` (R39).

- [ ] **Step 1: Write the failing tests** in `tests/test_credit_os_store.py`, building section
  dicts by hand (`{"heading", "level", "line", "blocks"}`; text block `{"type": "text", "text"}`,
  table block `{"type": "table", "headers", "rows": [{"cells": [...]}]}`):

| Heading | Level | Blocks | Placement | Words |
|---|---|---|---|---|
| `CP-1 handoff` | 1 | none | audit | 0 |
| `Front matter` | 1 | text `module: CP-1\ncommittee_status: Requires More Work` | audit | 6 |
| `Request` | 2 | text `What is asked.` | audit | 3 |
| `Sources` | 2 | text `K is the annual filing.` | audit | 5 |
| `Findings` | 2 | none | view | 0 |
| `Reader summary` | 3 | any table | consumed | not counted |
| `Chart data: leverage` | 3 | any table | consumed | not counted |
| `Liquidity view` | 3 | text `Cash covers two years of interest.` | view | 6 |
| `Debt register` | 3 | text `Drawn amounts.` + table row `Term loan`, `100` | reference | 5 |
| `Source register` | 3 | table row `K`, `Annual filing` | audit | 3 |
| `Source notes` | 4 | text `One two.` | audit | 2 |
| `Calculations` | 2 | text `EBITDA 10 less capex 4 is 6.` | calculations | 7 |
| `Bridge` | 3 | table row `10`, `4`, `6` | calculations | 3 |
| `Gaps` | 2 | text `Not supplied: the credit agreement.` | limits | 5 |
| `Extra notes` | 2 | text `One two three.` | audit | 3 |
| `Next module` | 2 | text `CP-2.` | audit | 1 |

```python
def test_sections_are_placed_by_their_level_two_parent():
    assert placements(SECTIONS) == EXPECTED_PLACEMENT          # the Placement column
def test_words_count_cells_and_prose_not_headings_or_headers():
    assert report_fields(SECTIONS, {"confidence": "Medium"})["words"] == {
        "view": 6, "reference": 5, "calculations": 10, "limits": 5, "audit": 23}
@pytest.mark.parametrize("cell, expected", [("Medium", True), ("Not assessable", False),
    ("not assessable.", False), (" Not Assessable", False)])
def test_established_reads_the_confidence_cell(cell, expected): ...
def test_no_reader_summary_is_neither():   # report_fields(SECTIONS, None)["state"]["established"] is None
def test_declared_is_the_front_matter_status_verbatim():       # "Requires More Work"
def test_declared_is_none_without_front_matter():              # SECTIONS minus `Front matter`
def test_every_built_output_carries_the_three_fields(tmp_path):
    # read_store: CP-1 has state == {"established": True, "declared": None},
    # len(placement) == len(handoffs[sha256]), set(words) == the five keys
```

  In `tests/test_update_library.py` add: the built `data.js` holds `state`, `placement` and `words`
  on the CP-1 output.

- [ ] **Step 2: Run** `uv run pytest tests/test_credit_os_store.py tests/test_update_library.py -q`.
  Expected: the new tests fail on the missing names.
- [ ] **Step 3: Implement** in `store.py`:
  `EVIDENCE_HEADING` (the pattern at `views.js:281`, `re.I`);
  `placements(sections: list[dict]) -> list[str]` (parent = the nearest heading at level ≤ 2, the
  section itself included; rules as in the spec's placement table, R34 and R37);
  `section_words(section: dict) -> int` (whitespace-split words of text blocks and table cells);
  `report_fields(sections: list[dict], summary: dict | None) -> dict` returning `state`,
  `placement`, `words` (`declared` from `^committee_status:\s*(.+)$` in the `Front matter` text).
  Call it after `reader_fields` at line 674. Add `cp1_findings` to `RunSpec` and the writer.
- [ ] **Step 4: Run** the Step 2 command plus `tests/test_library_index.py
  tests/test_credit_os_chips.py tests/test_credit_os_catalogue.py`. Expected: all pass. A test that
  compared a whole output record gains the three fields and nothing else.
- [ ] **Step 5: Commit** `feat(library): state, placement and word counts per module output`,
  together with the spec, the review and this plan.

Not verified: outputs with malformed front matter (none retained).

### Task 2: Chips — verified quotes and one count for unresolved citations

**Files:**
- Modify: `apps/issuer-library/credit_os/web/views.js` (`chipView` line 220, `chipsMarkup`),
  `web/screen.js` (`parseRoute`, `showInspector`, click handler line 575), `web/screen.css`
  (`.chip` block, lines 416–428), `credit_os/SOURCE.md`
- Test: `web/static.test.cjs`, `tests/test_library_page_browser.py`,
  `tests/browser_probe_module_report.js`

**Interfaces:**
- Produces: `chipsMarkup(key)` renders resolved chips, then at most one
  `<button type="button" class="chip-count" data-gaps="<key>">N citation(s) without a page</button>`.
  Unresolved = `kind === 'gap' && label !== 'Not supplied'`.
- Produces: route parameter `chip=gaps`; `showInspector(key, 'gaps')` lists every unresolved
  chip of the key in order.

- [ ] **Step 1: Write the failing tests** (`static.test.cjs`; add fixture key `${OUT}:53` with two
  `no page` gap chips and `${OUT}:54` with one):
  - `chipsMarkup(`${OUT}:16`)` contains `class="chip verified"` and `title="Quote found on page"`.
  - `chipsMarkup(`${OUT}:52`)` has exactly one `chip gap` (`Not supplied`) and one `chip-count`
    reading `2 citations without a page`.
  - `chipsMarkup(`${OUT}:53`)` has no `chip gap` and one count `2 citations without a page`;
    `${OUT}:54` reads `1 citation without a page`.
  - Update the gap-chip test at line 178 to these keys.
  Browser (`test_library_page_browser.py`): clicking `.chip-count` opens the inspector listing
  that many items; Esc returns focus to the count button.
- [ ] **Step 2: Run** node and `uv run pytest tests/test_library_page_browser.py -q`. Expected:
  new tests fail.
- [ ] **Step 3: Implement** the three interfaces above. `parseRoute` accepts `chip=gaps` only when
  the key has an unresolved chip.
- [ ] **Step 4: Run** both commands. Expected: pass.
- [ ] **Step 5: Commit** `feat(library): verified chips and one count for citations without a page`.

Not verified: the count on a key with more than nine unresolved chips (layout only).

### Task 3: Module page in nine parts

**Files:**
- Modify: `web/views.js` (lines 146–330 and `sectionGroups`, `outlineMarkup`,
  `navigationSections`, 396–452), `web/screen.js` (`parseRoute`, `scrollToPart`), `web/screen.css`,
  `credit_os/SOURCE.md`
- Test: `web/static.test.cjs`, `tests/test_library_page_browser.py`,
  `tests/browser_probe_module_report.js`

**Interfaces:**
- Consumes: `data[id].state`, `.placement`, `.words` (Task 1); `chipsMarkup` (Task 2).
- Produces: `REPORT_PARTS` = `head, bottom-line, numbers, findings, analysis, limits, reference,
  calculations, audit` with labels `Module, Bottom line, Key numbers, Findings, Analysis,
  Limits & monitoring, Statements and registers, Calculations, Evidence & audit`;
  `reportParts(id) -> [[anchor, label, html]]`, present parts only; `moduleReport`,
  `outlineMarkup` and `navigationSections` all read it. `METHOD_CODE` (R36).
- Produces: every drawn section wrapper has `id="s-<line>"`.

- [ ] **Step 1: Write the failing tests** (`static.test.cjs`). The harness fixture gains `level`
  on each section and `state`, `placement`, `words` on the output; add a prose `Liquidity view`
  (view), `T2F.1 — Macro source gate` (view), `Calculation trace` (calculations) and a level-2
  `Extra notes` (audit). Rewrite the tests at lines 155, 163, 226, 247, 274 and 433–517 to:
  - (a) Full fixture: the nine anchors appear once each, in order.
  - (b) A fixture with no `view` and no `calculations` section: no `id="analysis"`, no
    `id="calculations"`, no outline entry for either, no `part-empty` text anywhere.
  - (c) `established: false`: anchors are `head, bottom-line, findings, limits, handoff-text,
    audit`; `<details id="handoff-text">` has no `open`; its summary reads
    `Full handoff text · <view + reference + calculations> words`; `id="analysis"` sits inside it;
    no `id="numbers"`.
  - (d) `established: null`, `summary: null`: anchors are `head, numbers, analysis, limits,
    reference, calculations, audit`; no `handoff-text`.
  - (e) `<details id="reference">` is closed; its summary is `Statements and registers · <n>
    table(s) · <m> row(s)` with the fixture's own counts written as literals; its sections render
    whole, in handoff order.
  - (f) `<details id="calculations">` is closed; summary `Calculations · <words.calculations> words`.
  - (g) Headings: `T2F.1 — Macro source gate` shows `Macro source gate` with the full heading in
    `title`; `cp2b.cp_model_catalysts — blocked interface` → `blocked interface`;
    `TDR.1 — Research brief` → `Research brief`; `Net debt — bridge` unchanged.
  - (h) `Extra notes` is in the Evidence & audit list and in no other part.
  - (i) `declared: 'Blocked'` → the head holds `<span class="badge badge-gray">Blocked</span>`
    beside the acceptance badge; `null` → the acceptance badge only.
  - (j) Analysis holds only `view` sections, open, in handoff order, each `id="s-<line>"`.
- [ ] **Step 2: Run** node. Expected: (a)–(j) fail.
- [ ] **Step 3: Implement** `reportParts` and the part functions from `placement`. A section with
  no blocks is not drawn. Limits draws the `limits` sections as it does today. The method code is
  dropped from Analysis, Limits, Reference and Calculations headings, not from the audit list. Key numbers are chosen among `reference` sections by the existing rule;
  the chosen table also stays whole in Reference. The audit list holds the `modules[id].sections`
  entries with a section placed `audit` or `consumed`. Delete `EMPTY_PART`, `sectionGroups`,
  `analysisSections`, `limitsGroup`, `analysisBlocks`, `EVIDENCE_HEADING` and `isEvidenceSection`
  wherever no caller remains.
- [ ] **Step 4: Run** node. Expected: pass.
- [ ] **Step 5: Write the failing browser tests** (apply R39 to the existing ones first):
  - `#CP-1/s-<line of a Reference section>?c=run-a`: `details#reference` is open and the section's
    top is inside the content viewport.
  - `#CP-1/reference?c=run-a&e=<row line in that section>`: the part is open, the inspector is
    open, and after Esc `document.activeElement` is that row's chip.
  - `test_the_report_canvas_and_old_section_links` expects the nine anchors.
  - 1440 and 1280: no horizontal overflow on the module page.
- [ ] **Step 6: Implement** in `screen.js`: `parseRoute` accepts a present part anchor or an
  `s-<line>` of a drawn section, else `head`; `scrollToPart` opens every `<details>` that is or
  contains the target, then scrolls; a route with `e` opens the details holding its trigger.
- [ ] **Step 7: Run** `uv run pytest tests/test_library_page_browser.py -q` and node. Expected: pass.
- [ ] **Step 8: Commit** `feat(library): module page separates view, registers and calculations`.

Not verified: which key-numbers table each real module now picks (compared in Task 5).

### Task 4: Run report on the Overview

**Files:**
- Modify: `web/views.js` (lines 762–812; `readerChart` line 207), `web/screen.js` (change handler,
  line 564), `web/screen.css`, `credit_os/SOURCE.md`
- Rewrite: `tests/browser_probe_overview.js`
- Test: `web/static.test.cjs`, `tests/test_library_page_browser.py`

**Interfaces:**
- Consumes: `state`, `words` (Task 1); `reportBand(id)`, `chipsMarkup`, `groups`, `routeHref`,
  `moduleLink`, `defaultOutput`, `contextModules`.
- Produces: `runReport(context) -> string`, called by `workspaceView` for `W-Overview`;
  `registerRowShown(row: {group, confidence, established}, filter: {group, confidence, all}) ->
  boolean`; `readerChart(id, chart, chips = false, note = true)`.
- Markup the tests read: `.run-count`; `.coverage a.cov` (class `filled` when established);
  `.story-group > h2`; `.story-module`; `.na-line`; `table.register tr[data-group]
  [data-confidence][data-established]`; `select[data-register-filter="group"|"confidence"]`;
  `input#register-all`; `table.open-items`; `table.matrix`.

- [ ] **Step 1: Write the failing tests** (`static.test.cjs`). Give the harness a `groups`
  stand-in and a four-module run: `CP-1` (established, Medium, two findings, two charts), `CP-2A`
  (not assessable, declared `Blocked`, one finding), `CP-6` (not assessable), `CP-X` (in no named
  group, no summary).
  - Count line: `1 of 4 modules reach a conclusion · 2 not assessable · 1 without a reader summary`.
  - Coverage: four `a.cov` in group order, code as label, only `CP-1` `filled`, each linking to
    its module.
  - No `.band` while CP-6 is not assessable; one `.band` quoting CP-6 once it is established.
    `views.js` no longer contains `CALL_ORDER` or `summaryView`.
  - `CP-1` `.story-module`: name link, bottom line verbatim, confidence pill, two `.finding`
    with their chips, main limitation, the declared status when the fixture sets one, both charts inside the same element; the note
    `Missing values have no bar` occurs once in that group.
  - `CP-2A`: one `.na-line` holding the name link, `Not assessable`, `Blocked` and the limitation
    verbatim; no `.finding` belongs to it. A group with no established module has its `h2` and
    lines only.
  - `CP-X`: under `Other modules` as `CP-X · No reader summary`; present in coverage and matrix.
  - Register: columns `Group, Module, Finding, Creditor impact, Confidence`; three rows; the one with `data-established="false"` is `hidden`; the checkbox label
    is `Include not-assessable modules (1)`; that row carries a `Not assessable` mark. `registerRowShown` is false for a not-assessable row
    until `all`, and false on a group or confidence mismatch.
  - Open items: one row per module with a summary (three), grouped, each linking to
    `#<module>/limits`.
  - Matrix: four rows; `CP-X` declared cell `not declared`; the two word columns equal
    `words.view` and `words.reference + words.calculations`.
  - Deliverables and the source-inventory link render as before.
- [ ] **Step 2: Run** node. Expected: fail.
- [ ] **Step 3: Implement** `runReport` in the spec's order (count line with the acceptance and
  qualification badges as `summaryLead` prints them today, coverage, band, story, register, open
  items, matrix, deliverables). Only modules with an output in the run are listed. Delete
  `CALL_ORDER`, `firstFinding`, `moduleSummary`, `leadModule`, `summaryLead`, `summaryCharts`,
  `summaryCard` and `summaryView` where unused.
- [ ] **Step 4: Run** node. Expected: pass.
- [ ] **Step 5: Write the failing browser test** replacing
  `test_the_overview_chart_values_stay_inside_their_cards` (1440 and 1280): chart rows exist and
  each value is inside its card; no horizontal overflow; ticking `#register-all` raises the
  visible register rows from the established count to the total; console is empty.
- [ ] **Step 6: Implement** the `change` handling in `screen.js` with `registerRowShown`.
- [ ] **Step 7: Run** `uv run pytest tests/test_library_page_browser.py -q` and node. Expected: pass.
- [ ] **Step 8: Commit** `feat(library): the Overview is a run report`.

Not verified: a run with several outputs for one module (only the default output is reported).

### Task 5: Real-run check, gates and branch review

**Files:**
- Create (not committed): `.superpowers/sdd/<plan>/probe_rebuild.py`
- Modify: `VERIFICATION.md` (one entry), `apps/issuer-library/credit_os/SOURCE.md` if incomplete

- [ ] **Step 1: Write the probe** (`mx-feature`). It builds the library into a scratch directory
  with `build_library(ws, out)` then `update_library.build_into(out, ws, lib)`,
  `ws = ~/Documents/RBOT-HTML`, and reads only from there. For `cpos-tdg-sol-medium-all-001` it
  asserts: count line `7 of 20 modules reach a conclusion · 13 not assessable`; established set
  `CP-1, CP-1A, CP-2, CP-2D, CP-2E, CP-3C, CP-DR`; 33 register rows visible, 84 with the checkbox;
  the checkbox label `Include not-assessable modules (51)`; the `words` key above for CP-1 and
  CP-2E; over the run report and all 20 module routes in headless Chrome, every `.chip.gap` is
  labelled `Not supplied`, the console is empty and nothing overflows at 1440 and 1280. It also
  prints, per module, the key-numbers table chosen now and at 5d994c0.
- [ ] **Step 2: Run it.** Expected: exit 0. A key-numbers difference is reported to the owner, not
  "fixed".
- [ ] **Step 3: Gates.** `uv run python tools/quality_gate.py --base main`;
  `node --test apps/issuer-library/credit_os/web/static.test.cjs
  apps/issuer-library/credit_os/web/calendar.test.cjs`; `uv run pytest tests/test_credit_os_store.py
  tests/test_update_library.py tests/test_library_index.py tests/test_credit_os_chips.py
  tests/test_credit_os_catalogue.py tests/test_library_page_browser.py -q`. Expected: all exit 0.
  Measure the diff against the 800-line cap and report the number.
- [ ] **Step 4: Branch review.** `confidence-review` and `rewrite-tournament` (post-edit) once on
  `5d994c0..HEAD`; then `mx-architect` on the same range with the spec and this plan. `mx-precise`
  re-runs the probe.
- [ ] **Step 5: Record and commit.** One `VERIFICATION.md` entry naming the probe result and its
  scope (one retained run, deterministic rebuild, no model call).
  `docs(verification): run report phase A`.

Not verified: the other three retained runs beyond building without error; screen widths below
1280; the weekly full suite.
