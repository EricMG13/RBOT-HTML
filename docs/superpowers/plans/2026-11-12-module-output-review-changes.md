# Module Output Review Changes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix what the section-by-section review of a real run's module pages found: show each chart once, make source references open, clean labels and drawings, and hold every displayed section to the reader's vocabulary.

**Architecture:** Display fixes live in the static library (`apps/issuer-library/credit_os/web/` and `store.py`, plus `src/deploy_workflow/credit_os_chips.py`) and apply to existing runs. Method changes live in the launcher's shared instruction text and the Python checkers (`src/deploy_workflow/owners/cpos_launch.py`, `src/deploy_workflow/prose_checks.py`), all before `METHOD_MARK`, so no existing run becomes "Earlier methods".

**Tech Stack:** Python 3 (uv, pytest, ruff, mypy), plain browser JavaScript (node --test, headless Chrome browser tests).

**Spec:** `docs/rulings/2026-11-12-module-output-review-changes.md` (decisions 1-11). Evidence: `reviews/2026-11-12-module-output-adversarial/latest-run-tdg-proof-snapshot-opus-002.md`.

## Global Constraints

- No provider or model call. No change to any run folder, stored handoff, route, `href` or stored file name.
- No module code (`CP-…`) on screen; `Source` cell text and file names exact (rulings 2026-11-11 H4 and amendment 2026-11-12).
- No new dependency. No stub or fake value standing in for real behaviour. No catch-all that hides a failure.
- Every code fix starts with a test that fails for the stated cause; existing tests are changed only where this plan names them, never weakened.
- Geometry of a drawing uses stated numbers only (views.js:264-266); a dated item is never moved to a day the source does not state (views.js:683).
- Gates per task: the node tests and the pytest files the task names; then `uv run python tools/quality_gate.py`. Each test run within `timeout 300`.
- Node tests: `node --test apps/issuer-library/credit_os/web/reader.test.cjs apps/issuer-library/credit_os/web/static.test.cjs apps/issuer-library/credit_os/web/calendar.test.cjs apps/issuer-library/credit_os/web/changes.test.cjs`.
- Real-run fixture for probes (read-only copy): `SCR/ws2` where `SCR=/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad`; rebuild its library into a fresh folder with `uv run python apps/issuer-library/update_library.py --workspace <copy>`.
- Every task report ends with a `Not verified:` line.

## Review Focus

1. An earlier-format run's module page: must render exactly as before (placement path, `drawn()`); no task may route it through the new-format changes.
2. A route `#<module>/s-<line>` to a chart, map or events section after the body copy is gone: must scroll to the drawing, not the page head.
3. A handoff whose `## Sources` table has no sha256 column, or an older CP-0 with an "inventory" section: both must still resolve chips.
4. A retained accepted handoff re-checked under the wider prose scope: the refusal must name the section and line; credit words (consumer, upstream, transport) alone must pass.
5. A `### Confidence inputs` table with a zero total, a missing row or a non-number: the page shows no score and says why; nothing is guessed.

---

## Branch A `claude/modules-page-sources-charts`

### Task A1: each drawing once; routing text in an audit fold; a card for a chart with no numbers (decisions 1, 2)

**Files:** Modify `apps/issuer-library/credit_os/web/views.js` (`newFormatRest` 581, `newFormatParts` 610, `reportChartCards` 583, `reportMaps` 764, `reportTimeline` 585, `drawnAnchors` 415, `reportAudit` 555-561, list at 85), `screen.css`. Tests: `static.test.cjs` (1324, 1348 outline pins change; 2413-2418; 2420+; 2244, 2345, 2449-2466; 816-826), `tests/test_library_page_browser.py` (~1437).

**Interfaces:** Produces: section anchor ids `s-<line>` on each chart `panel-card`, `map-card` and timeline lane; a new-format part `['audit','Evidence & audit',…]` last on the page.

- [ ] Failing node tests: (1) new-format outline no longer lists `Chart data:`/`Map:`/`Events:`/`Request`/`Next module`/`Front matter` entries and ends with `Evidence & audit`; (2) the body has no "Chart data:" heading while the Charts part holds every chart with its Table form; (3) prose written under a `Chart data:` table appears as that chart card's caption; (4) a `chartGaps` entry draws a card with "Not established for this run" and its reason, in table-line order; (5) the compact timeline has a "Table form" fold; (6) front matter in the fold is drawn as lines, without a `filename` line; (7) an earlier-format page's parts are unchanged.
- [ ] Failing browser test: `#CP-1/s-<chart line>` scrolls a chart card into view; no "Chart data:" text on a new-format module page.
- [ ] Implement; `Calculations` is not listed twice (drop it from the 85 list for new-format outputs).
- [ ] Node tests, `uv run pytest tests/test_library_page_browser.py -m browser -q`, quality gate. Commit.

### Task A2: source references resolve (decision 3)

**Files:** Modify `src/deploy_workflow/credit_os_chips.py` (`inventory_tables` 281-295, 310; Basis item grammar ~44, 195-232), `apps/issuer-library/credit_os/web/reader.js` (`basisItem` 79-123, `tableView` 336-345, `writtenCell` 329-331), `views.js` (`gapCount` 434, chip label 438, legend 475). Tests: `tests/test_credit_os_chips.py` (108, 335, 801), `reader.test.cjs` (395), `static.test.cjs` (510, 518, 785, 2082).

**Interfaces:** Produces: `inventory()` also reads the `## Sources` table (file = first cell; sha256 from a column headed `sha256` when present); a Basis item or Source cell `<file>, pages 71, 121` yields one locator per page; a `Source` column cell is a `<button data-chip … data-index …>` around unchanged text when a chip matches its file and page.

- [ ] Failing Python tests: a new-format handoff set whose sources are only in `## Sources` yields `issuer_page` chips; comma page lists resolve to each page; a Sources table without a sha256 column still resolves; an old "inventory" section still resolves.
- [ ] Failing node tests: Source cell button present with exact text; chip label "Row"; legend "this table row · another module"; count text "N unresolved citations".
- [ ] Implement. Probe on the real run copy: count of `issuer_page` chips was 0 of 639; report the new count.
- [ ] `uv run pytest tests/test_credit_os_chips.py tests/test_credit_os_store.py tests/test_library_reader_refs.py -q`, node tests, quality gate. Commit.

### Task A3: register and module labels (decision 4)

**Files:** Modify `views.js` (`MODULE_REF` 27, `STEP_LEAD` 30 unchanged, `STEP_HEADING` 32, `METHOD_CODE` 409, `stepText` 57-58, 75), `screen.js` (259, 268). Tests: `static.test.cjs` (2106-2116, 2118-2147, 2174, 2191-2200).

- [ ] Failing node tests with the real strings: heading `T2.12 Gaps ledger` → "Gaps ledger" (heading, outline, search label); `'T9.9 stands'` in a sentence keeps its current result; `CP-3B-MON-001` → "MON-001" on its own module's page and "Security selection MON-001" elsewhere; `CP-2A-DP-005` likewise; cell `Gap CP-2A-GAP-005` → "Gap 5"; no output contains "a method step" for a heading that has a title.
- [ ] Implement. Node tests, quality gate. Commit.

### Task A4: negative figures, fenced blocks, wide tables (decision 5)

**Files:** Modify `reader.js` (`figureSpans` 198-225, `sectionBodyHtml` 349-368, `tableView` 336-345), `apps/issuer-library/credit_os/store.py` (`text_block` 316-367), `screen.css` (382, 384). Tests: `reader.test.cjs` (103-115, 395-398), `static.test.cjs` (1369), `tests/test_credit_os_store.py`, `tests/test_library_page_browser.py` (729-733).

- [ ] Failing tests: `USD -158 million` and `USD −2,505 million` are one figure each including sign and currency; `10-12` (a range) and `FY2023-24` are not signed figures; a text block opening with three backticks renders `<pre><code>` with escaped inner text, no figure buttons, blank lines inside the fence kept in one block; `tableView` wrapper has `role="region" tabindex="0" aria-label`.
- [ ] Implement; CSS: scroll-shadow cue on `.analysis-section .table-card`, header cells may wrap there.
- [ ] Node tests, `uv run pytest tests/test_credit_os_store.py -q`, browser tests, quality gate. Commit.

## Branch B `claude/modules-page-drawings` (stacked on A)

### Task B1: bridge labels and debt stack colours (decision 6)

**Files:** Modify `views.js` (`axisLines` 200-205, `bridgeChart` 206-226, `stackChart` 281), `screen.css`. Tests: `static.test.cjs` (1744; 1816-1830 change from index colours to rank/security).

- [ ] Failing node tests: nine long step labels produce label boxes that do not overlap (word-wise wrap to a budget derived from the step width, at most 3 lines, ellipsis, full text in `<title>`); stack segments of equal Ranking and Secured share a series class, different ones differ, and a legend names each ("Rank 1 · secured", …); a row with no Ranking keeps a neutral class.
- [ ] Implement. Node tests, browser tests, quality gate. Commit.

### Task B2: timeline (decision 6)

**Files:** Modify `views.js` (`eventLanesView` 691-711), `calendar.js` (`eventAxis`/`eventPlace`), `screen.css` (527). Tests: `static.test.cjs` (2234-2291), `calendar.test.cjs`.

- [ ] Failing tests: year ticks between axis start and end; an as-of rule when the run's as-of date is inside the axis and none when outside; two points closer than 12 px are stacked vertically at their own x (x unchanged); each point carries a visible number matching a numbered key (date and description); a month or year span is still drawn over its whole length.
- [ ] Implement. Node tests, browser tests, quality gate. Commit.

### Task B3: maps (decision 6)

**Files:** Modify `views.js` (`mapDiagram` 730-751, `lines()` 742, edge labels 738/745), `screen.css` (539). Tests: `static.test.cjs` (2324-2361).

- [ ] Failing node tests: no node line breaks inside a word or number ("6.01x" stays whole); text over 3 lines ends with an ellipsis and the full text is in `<title>`; two edges into one target have label positions that do not overlap; the map scroller has the same region/tabindex/cue as tables.
- [ ] Implement. Node tests, browser tests, quality gate. Commit.

## Branch C `claude/reader-rules-all-sections` (stacked on B)

### Task C1: launcher shared text (decisions 7, 9, 11 wording)

**Files:** Modify `src/deploy_workflow/owners/cpos_launch.py` (`TRANSPORT_RULES` 1541-1560, `VOICE_RULES` 331-372, rejection list 1930-1933, `PROSE_PASSAGES` 292-321), new constant `MODULE_NAMES` there. Tests: `tests/test_cpos_launch.py` (substring tests near 736-750).

**Interfaces:** Produces: `MODULE_NAMES: dict[str, str]` equal to the names in `screen.js` `groups`; instruction text sent to every module.

- [ ] Failing tests: instructions for a prose and a data module contain the new rules (vocabulary across shown sections; no mention of helper scripts, no confidence score, band or QA status stated; Sources columns `Source | Document | Document date | sha256 | Use` with the exact file name first and run settings not listed; other modules by plain name from the sent list; one qualification sentence after each chart table; map text at most 60 characters; bottom line limits 45 and 180 words) and no longer contain "record each as not run"; `MODULE_NAMES` equals the pairs parsed from `screen.js`; `method_text(module)` is byte-identical to before for every module (so no run is marked Earlier methods).
- [ ] Implement. `uv run pytest tests/test_cpos_launch.py tests/test_library_index.py -q -m "not live and not browser"`, quality gate. Commit.

### Task C2: prose checks on every shown section; check 10; bottom line shape (decisions 7, 8)

**Files:** Modify `src/deploy_workflow/prose_checks.py` (`_findings_sections` 89-107, `SIMPLE_CHECKS` 288-313, `_check_bottom_line` 240-285, `prose_issues` 715-732). Tests: `tests/test_prose_checks.py` (101-109 and 112-116 change by this ruling), `tests/test_cpos_launch.py` (~1578), `tests/test_citation_markers.py`.

**Interfaces:** Produces: `prose_issues` also checks sentence text of every other H3 under `## Findings` (not `Chart data:`, `Map:`, `Events:`, forecast input or `Confidence inputs` sections, not tables, fences or Basis lines) and of `## Calculations` and `## Gaps`, with checks 2-5 and 10; check 6 stays on the passages; each issue names the section heading and line.

- [ ] Failing tests: a module code, page locator, bracket or hash in a `### Method`-style section sentence is refused with the section named; each banned phrase of decision 7 is refused in a passage and in another section; "consumer demand", "upstream operations", "the transport sector", "USD", "EBITDA", "FY2024" pass; a snake_case token and a `READY_WITH_LIMITATIONS` token are refused; the same text inside a table row, a fence or a Basis line passes; a first sentence of 46 words and a bottom line of 181 words are refused, 45 and 180 pass; the fidelity `figure_issues` result on the real CP-8 text (`tests/test_changes.py:2218-2221`) is unchanged.
- [ ] Probe (report only): run `prose_issues` over the 13 accepted handoffs of the real run copy and report refusals per module and check.
- [ ] Implement. `uv run pytest tests/test_prose_checks.py tests/test_cpos_launch.py tests/test_citation_markers.py tests/test_changes.py -q -m "not live and not browser"`, quality gate. Commit.

### Task C3: Python-owned confidence score (decision 9)

**Files:** Create `src/deploy_workflow/confidence.py`; modify `cpos_launch.py` (an `OwnerTable` `### Confidence inputs` for every module whose `METHODS` entry carries `_SCORE`, 141/246), `apps/issuer-library/credit_os/store.py` (module view carries the result), `views.js` (module head shows it). Tests: create `tests/test_confidence.py`; `tests/test_cpos_launch.py`, `tests/test_credit_os_store.py`, `static.test.cjs`.

**Interfaces:** Produces: `confidence.score(lineage: dict[str, int], fields_present: int, fields_total: int, source_gate: str, findings: dict[str, int]) -> Score` (`Score.value: int`, `Score.band: str`, `Score.status: str`), formula and caps exactly as `docs/reuse/selected-methods/CANON_SHARED.md:333-391`; `confidence.from_handoff(text: str) -> Score | Refused`; store field `confidence` on a module view: `{"value", "band"}` or `{"missing": "<reason>"}`.

- [ ] Failing tests: `score()` equals the archived script `docs/reuse/selected-methods/skills/cp-5-evidence-trace-validator/scripts/confidence_score.py` (run as a subprocess; the answer key, not edited) on at least 12 hand-picked input sets including each cap (CRITICAL → at most 39 and Blocked; MATERIAL → at most 59 and Restricted) and both clamps; `from_handoff` reads the table; a zero total, a missing row or a non-number gives `Refused` with the reason; the checker refuses a draft of a scoring module without a well-formed table; the module head shows "Confidence 58 · Low" from the store field and "Confidence not computed: <reason>" otherwise; an existing run without the table shows nothing new.
- [ ] Implement. Tests above, node tests, quality gate. Commit.

### Task C4: post-balance-sheet adjustments (decision 10)

**Files:** Modify `cpos_launch.py` (an `OwnerTable` `### Post-balance-sheet adjustments` on CP-1 for all seven pathways beside `NET_DEBT` 574-589; one `VOICE_RULES` sentence). Tests: `tests/test_cpos_launch.py`.

**Interfaces:** Produces: table columns `Event | Date | Amount | Pro forma net debt | Pro forma net leverage | Reporting unit | Basis and limitation`; one row reading "None found in the sources read" is valid.

- [ ] Failing tests: CP-1 instructions name the table; a CP-1 draft without it is refused; a draft with a dated row or the single "None found" row passes; the heading is not a `Chart data:` heading (the library does not draw it) and the Changes pack's measures are unchanged for a fixture that adds it (`tests/test_changes.py` exact-dict cases untouched).
- [ ] Implement. `uv run pytest tests/test_cpos_launch.py tests/test_changes.py -q -m "not live and not browser"`, quality gate. Commit.

## Closing

- [ ] Whole-branch review of each branch diff (confidence-review and rewrite-tournament once per branch).
- [ ] Fidelity check: build the real-run copy before (`a873f6f`) and after; for each of the 13 module pages compare every word in the DOM by count; every difference must be one this plan names.
- [ ] Reader check: read the after pages of Financial foundation, Business & governance and Fundamental credit at 1440 against the September VMO2 screenshots; record scope.
- [ ] PR-check pytest list and node tests exit 0; quality gate 0 findings.
- [ ] `VERIFICATION.md` entry (trim oldest to stay under 1,000 lines); `METHODOLOGY-REVIEW.md` dated note naming this ruling.
- [ ] Not in this plan: the paid run that proves decisions 7-11 on a model (owner's action).
