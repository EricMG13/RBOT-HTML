# Issuer Library Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. One fresh implementer per task, a task review after each, a
> whole-branch review at the end.

**Goal:** Every library screen presents findings as components chosen by data shape, with audit,
tracing and governance material only in Evidence and inter-module content drawn nowhere.

**Architecture:** Two new pure scripts sit beside the existing ones: `shapes.js` classifies
sections, tables, columns and paragraphs; `components.js` turns a classified block into markup.
`evidence.js` owns the Evidence page. Existing `views.js`, `screen.js`, `reader.js` and
`changes.js` call them; routes and data shapes do not change.

**Tech Stack:** Classic scripts and CSS in `apps/issuer-library/credit_os/web/`, Node's test runner
(`*.test.cjs`), pytest, headless Chrome probes. No dependency, no build step.

**Spec:** `docs/visualisations/2026-11-13-screen-component-map.md` (component IDs C1 to C36, shape
rules, screen tables). Owner's go: 2026-11-13, "Yes, build it" (as the mocks show).

**Prior art (adapt, do not start blank):**

| Source | Use |
|---|---|
| `.superpowers/sdd/2026-11-13-report-redesign/mock/` (`mock.css`, `mock.js`, `overview.js`, `downside.js`, `evidence.js`; git-ignored, on disk) | The approved look and behaviour of every component in the three mocked pages. Port the markup and CSS; replace its heading lookups with `shapes.js` |
| Branch `claude/report-visualization-overhaul-f3347d` (`typed.js`, `.g24` rules in `screen.css`, `ledgerTable` in `changes.js`) | Column typing (`columnKinds`, `statusTone`), the capped-gutter grid, the CSS-only ledger filter. Read with `git show <branch>:<path>` |
| Existing `views.js` charts (`bridgeChart`, `stackChart`, `dumbbellChart`, `rangeChart`, `comparisonChart`), `mapDiagram`, `eventLanesView`, inspector (`showInspector`) | Reuse; restyle rather than rewrite |

Public search was not run: rule 5 fixes the component sources to eight named libraries, which were
read live (`.superpowers/sdd/2026-11-13-report-redesign/research/`).

## Global Constraints

1. **Stack.** Plain classic scripts and CSS; no dependency, no build step, no network, no inline
   script or event-handler attribute (the page's policy is `script-src 'self'`). Inline
   `style="..."` and inline SVG are allowed. New scripts are added to `static-boot.js`'s load list
   the way existing ones are.
2. **Handoff data only.** Every figure, sentence and label of issuer content is drawn with the
   handoff's own characters. Nothing is computed, rounded, abbreviated or filled in. A number is
   parsed only to place a mark (`chartNumber`); the text beside the mark is the cell. Counts of
   listed items (rows, modules, files) may be shown. Missing stays missing.
3. **Findings pages** (Overview, Changes, Modules, Forecast, library home, history) never draw:
   Basis text, a Source/Evidence/Source Trace column, a file name, a hash, an ID column, a
   calculation ID, a method code (`T2B.3`), the run code, or an inter-module column. One trace
   icon per paragraph, row group or figure opens the drawer.
4. **Evidence is complete.** Every table cell and paragraph of every handoff section whose role is
   `sources`, `calculations`, `gaps` or `registers`, and every table of a `finding` or `drawing`
   section as written, is present in Evidence, except hidden columns of kind inter-module.
5. **Rule 7.** A section with role `hidden` and a column of kind inter-module are drawn nowhere.
   They remain in the downloadable original handoff.
6. **Shape, not heading.** `tableShape` takes only the block. No component or view selects by a
   section heading or module id, except the four passage headings and the `Chart data:`, `Map:`,
   `Events:` prefixes that `store.py` already contracts.
7. **No repeated component for different information; nothing that looks like rendered Markdown.**
   A shape has one component. The fallback (`records`) is a designed card, never a plain grid.
8. **Colour, type, grid.** Only tokens in `screen.css` `:root`. Status colours (`--green`,
   `--amber`, `--red`) mark state only, never a series. A state is never colour alone. Grid is
   `.g24{display:grid;grid-template-columns:repeat(24,minmax(0,1fr));gap:24px min(16px,4%)}` with
   `column-gap:min(24px,4%)` from 992px; spans `.c5 .c6 .c7 .c8 .c10 .c12 .c14 .c16 .c19 .c24`;
   below 768px every span is 24. Card radius 12px, 1px `--rule` border. A side accent border is
   used only on the callout (C6), the section rail's current item and risk-matrix chips.
9. **Motion.** Only as in the spec's section 8, inside
   `@media (prefers-reduced-motion: no-preference)`, none in print. Nothing loops except a loader
   while a run is live.
10. **Accessibility.** Real buttons; `aria-pressed` on toggles; `aria-label` on icon buttons; focus
    visible; the drawer closes on Escape and returns focus; contrast at least 4.5:1; works under
    `forced-colors: active`; prints its text. No page-level horizontal scroll at 1440px or 390px.
11. **Existing code stays findable.** `static.test.cjs` slices `views.js` by function names and
    text anchors: do not rename or reorder existing functions. A test that pins markup this plan
    changes is updated to the new markup in the same task; no test is deleted without an
    equivalent and no assertion is weakened to pass.
12. **Process.** No stub or fake value standing in for real behaviour. No catch-all that hides a
    failure. The answer key `apps/issuer-library/fixtures/shape-key.json` and the probes under
    `.superpowers/sdd/2026-11-13-report-redesign/probes/` are not edited by an implementer, and a
    comparison with them is not weakened. Tests first for new logic. Every report ends with a
    `Not verified:` line. Commit per task (`feat(library): ...`, `test(library): ...`) ending with
    `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`. Nothing is pushed.
13. **Out of scope.** `store.py` data shapes, module instructions, launchers, method files, the
    run start form, the HTML Model's internals.

**Gates per task** (all exit 0, from the repo root):

- `node --test apps/issuer-library/credit_os/web/*.test.cjs` (the directory form fails on Node 24).
- `uv run pytest -q -p no:cacheprovider tests/test_update_library.py tests/test_library_index.py tests/test_library_reader_refs.py tests/test_issuer_library_packaging.py` (Bash timeout 300 s).
- `uv run python tools/quality_gate.py --base 517b9fb` only if a `.py` file changed.
- From Task 2 on: rebuild the scratch library
  (`uv run python apps/issuer-library/update_library.py --workspace <WS>`, `<WS>` given in the
  dispatch) and run `bash .superpowers/sdd/2026-11-13-report-redesign/probes/run.sh <WS> <checks>`
  with the checks the task names.
- The 98 browser tests (`-m browser`) run once, in Task 13.

## Review Focus

1. A table whose shape nothing recognises (new module, renamed columns): drawn as a `records`
   card with every non-hidden cell, never dropped and never a raw grid. Test in Task 1 and Task 6.
2. A cell that does not parse as a number in a numeric component ("n/a", "Not calculable: ..."):
   shown as its text with no mark, and the component still draws. Test in Task 5.
3. A first run or a run without CP-8, CP-6 or charts: Overview, Changes and Forecast draw their
   designed empty states, not blank regions or errors. Tests in Tasks 8, 9, 10.
4. A handoff in the earlier format (`isNewFormat` false): the module page keeps today's rendering
   path unchanged. Test in Task 4.
5. A deep link into Evidence (`#W-Evidence/gaps?c=...&m=CP-2A`) and the old Evidence route
   (`#W-Evidence/sources`): both open the right tab and module. Test in Task 3.

---

### Task 0: Probes (controller's answer keys; `mx-scaffold`)

**Files:** Create under `.superpowers/sdd/2026-11-13-report-redesign/probes/`: `run.sh`,
`harness.html`, `harness.js`, `findings.cjs`, `evidence.cjs`, `overflow.cjs`.

Specified in `.superpowers/sdd/2026-11-13-report-redesign/probes-brief.md`. Checks: `findings`
(figure tokens verbatim; forbidden strings), `evidence` (constraint 4), `hidden` (constraint 5),
`overflow` (constraint 10, every route at 390, 768, 1000, 1440).

### Task 1: `shapes.js`, the classifiers

**Files:** Create `web/shapes.js`, `web/shapes.test.cjs`. Modify `web/static-boot.js` (load list).
Key (read-only): `apps/issuer-library/fixtures/shape-key.json`.

**Interfaces (produces; `window.Shapes` and `module.exports`):**
- `sectionRole(chain: string[], placement: string): 'passage'|'finding'|'drawing'|'sources'|'calculations'|'gaps'|'registers'|'hidden'`
  where `chain` is the headings from the level-2 ancestor down to the section itself.
- `tableShape(block: {headers: string[], rows: {cells: string[]}[]}): 'statement'|'metric'|'measure'|'cases'|'caseRows'|'ranked'|'matrix'|'watch'|'status'|'sided'|'change'|'moduleState'|'qa'|'facts'|'dated'|'edges'|'records'`
- `columnKind(header: string): 'source'|'id'|'intermodule'|'limitation'|'consequence'|'period'|'case'|'label'|'text'`
- `hiddenColumns(headers: string[], shape: string): number[]` (source, id and inter-module
  columns; the `moduleState` table's module column is its label and is not hidden).
- `blockRole(text: string): 'note'|'prose'` (a module-status, confidence or method paragraph is a
  note and belongs to Evidence).
- `promoted(shape): boolean` true for `matrix`, `watch`, `dated`: a register table of that shape
  is also drawn on the module page (the first of each shape; `dated` only when the module has no
  `Events:` section).

- [ ] Tests first, in `shapes.test.cjs`, against the key: all 321 `sections` roles; all 41
  `tables` shapes and `hidden` indices (the test passes only `{headers, rows}`); every `notes`
  entry is a note and no other text block of a `finding` section is. Plus: a zero-row table and
  an unrecognised header set are `records`; headers differing only in case or outer spaces
  classify the same; a `statement` whose second period cell is "Not calculated" is still a
  `statement`.
- [ ] Implement; rules read headers and cell patterns only.
- [ ] Gates; commit.

### Task 2: Shell, trace drawer, toast, tooltip

**Files:** Modify `web/index.html`, `web/views.js` (`updateWorkspaceChrome`, tabs), `web/screen.js`
(`showInspector`), `web/reader.js` (`basisButton`, `paragraphView`), `web/screen.css`. Create
`web/components.js` (first functions), `web/components.test.cjs`.

**Interfaces (produces):** `Components.traceButton(key, label): string` (16px icon button,
`data-basis` as today); `Components.toast(text): void`; `[data-tip]` CSS tooltip;
`Components.icon(name): string` (inline SVG from `icons/`, `currentColor`).

- [ ] C1 pills for the workspace tabs (order and labels unchanged; the active pill slides).
- [ ] Header: issuer name large; chips for period and pathway in words; an amber chip "Methods
  changed since this run" when `run.methodChanges.length > 0`, linking to Evidence's Run record.
  The run code leaves every page except Evidence.
- [ ] The Basis button becomes the trace icon; the inspector becomes the C22 drawer (slides in,
  backdrop below 1600px, Escape, focus return) and ends with "Open in Evidence"
  (`#W-Evidence/trace?c=<run>&m=<module>`).
- [ ] Tests: no findings route's module head or tabs contain the run code; the drawer's footer
  link carries the module; `traceButton` has an `aria-label`. Probe checks: `overflow`.

### Task 3: Evidence

**Files:** Create `web/evidence.js`, `web/evidence.test.cjs`. Modify `web/views.js`
(`evidenceView` delegates), `web/screen.js` (route parse for `?m=` and the tab), `web/screen.css`.

**Interfaces:** consumes `Shapes.sectionRole`, `Shapes.hiddenColumns`, `Shapes.blockRole`.
Produces routes `#W-Evidence/<summary|trace|sources|calculations|gaps|registers|record>?c=&m=`;
`#W-Evidence/sources` without `m` keeps working.

- [ ] Governance summary (C30 half-ring, tiles, per-module gap bars, method changes, run record)
  as mocked; counts only.
- [ ] C26 filter bar (search, module chips) and C25 tabs with counts.
- [ ] Trace (statements with Basis items; rows expand to excerpts), Sources (file cards, C28
  reader stack, C35 copy with toast), Calculations, Gaps, Registers (tables as written minus
  inter-module columns; also the as-written tables of `finding` and `drawing` sections; notes),
  Run record (C13 steps, hashes, instructions, model calls grouped per module), original
  handoffs.
- [ ] Tests: Review Focus 5; a `hidden` section's text is absent from every tab; an
  inter-module column header is absent. Probe checks: `evidence hidden overflow`.

### Task 4: Module page: passages, rail and the role split

**Files:** Modify `web/views.js` (`newFormatParts`, `reportOutline`), `web/components.js`,
`web/screen.css`, `web/static.test.cjs`, `web/reader.test.cjs`.

**Interfaces (produces):** `Components.verdictPanel(texts, trace)`, `findingsFeed(texts, trace)`,
`callout(title, texts, trace)`, `limitationsBlock(texts, gapCount, evidenceHref)`,
`sectionRail(items)`.

- [ ] A new-format module page draws only `passage`, `finding` and `drawing` sections, in handoff
  order: C2, C5, C6, then analysis sections, then Limitations with the gap signal. Sources,
  Calculations, Gaps, registers, notes and hidden sections are no longer drawn there.
- [ ] C33 rail replaces the section nav on module pages (scroll-marked; a strip on phones).
- [ ] Until Tasks 5 to 7 land, a `finding` table draws through the `records` fallback.
- [ ] Tests: Review Focus 4; no `Basis:` text; the first sentence of Bottom line is the panel's
  lead. Probe checks: `findings hidden overflow`.

### Task 5: Numeric shape components

**Files:** Modify `web/components.js`, `web/components.test.cjs`, `web/views.js` (dispatch),
`web/screen.css`.

**Interfaces (produces):** `Components.render(shape, block, ctx): string` dispatching to
`casesBlock`, `caseRowsBlock`, `rankedLadder`, `statementCard`, `metricTiles`, `measureTiles`,
`changeCards`. `ctx = {id, section, trace(line), evidenceHref}`.

- [ ] `cases`: C8 case selector over C3 tiles and C10 range tracks, Chart/Table toggle.
  `caseRows` with text columns: C9 cards that select the case when a `cases` table precedes them
  in the section's parent; with numeric columns: a compact case-by-measure panel.
- [ ] `ranked`: C11 ladder with a phone list. `statement`: paired bars with a Bars/Figures toggle.
  `metric`: grouped tiles, definition in C24 unless it holds only calculation IDs. `measure`: C3
  tiles with the consequence beneath. `change`: C19, a dumbbell when both cells parse.
- [ ] Tests: each component on its key table contains every non-hidden cell's text; Review Focus
  2; a cell holding an ID token inside a sentence (`As SC1; ...`) is not drawn and the row links
  to Evidence. Probe checks: `findings overflow`.

### Task 6: Non-numeric shape components

**Files:** as Task 5.

**Interfaces (produces):** `statusChecklist`, `sidedBoard`, `moduleStateTiles`, `qaAccordion`,
`factList`, `recordCards`, `riskMatrix`, `watchList`, registered in `Components.render`.

- [ ] `status`: C12 with C29. `sided`: C7 with a qualifier tag. `moduleState`: C20 tiles, a
  repeated state collapsed to an icon and a count. `qa`: C18 with an answer-state badge. `facts`:
  C17 grouped by category. `records`: designed cards, one per row, label first. `matrix`: C16.
  `watch`: indicator, leading/lagging icon, threshold; limitation in a `<details>`.
- [ ] Tests: every non-hidden cell present; Review Focus 1; a `sided` cell "Bear (weakly)" places
  right with the tag "weakly". Probe checks: `findings overflow`.

### Task 7: Events, maps and promoted registers

**Files:** Modify `web/views.js` (`eventLanesView`, `mapDiagram`, `mapsView`), `web/components.js`,
`web/screen.css`, tests.

- [ ] `dated`: C15 timeline (horizontal from 992px when six or fewer events, else vertical);
  category icon; the Source column goes to the trace icon. A `gap` event lane draws C32 with the
  module's stated reason.
- [ ] `edges`: C14: the existing diagram restyled, edge style by type, a relationship panel on
  select, a step list on phones; the edge table leaves the findings page.
- [ ] Promoted registers per `Shapes.promoted`.
- [ ] Tests: an events table with one "Not supplied: ..." row draws the empty state, not a
  timeline; the edge table's Evidence column text is absent. Probe checks: `findings overflow`.

### Task 8: Overview

**Files:** Modify `web/views.js` (`runReport`, `overview*`), `web/components.js`, `web/screen.css`,
tests.

- [ ] C2 from the lead module's Bottom line; a C4 strip from the first `metric` table of the run
  (rows whose label appears in the lead Bottom line or Key findings text, at most four); C7 from
  the first `sided` table; C5; C6; C15 from the lead module's events, else the first promoted
  `dated` table, attributed; C20 module tiles with `state.declared` badges; Limitations with the
  gap signal. The chart index and "Evidence and audit" link lists are removed.
- [ ] Tests: Review Focus 3 (no CP-6: the lead falls back as today; no `sided` table: no board);
  a tile opens one at a time. Probe checks: `findings overflow`.

### Task 9: Changes

**Files:** Modify `web/changes.js`, `web/changes.test.cjs`, `web/evidence.js` (ledger in Gaps),
`web/screen.css`.

- [ ] Summary bar kept; `change` via C19; `moduleState` via C20 with unchanged modules collapsed;
  the ledger moves to Evidence's Gaps tab; first run draws C32.
- [ ] Tests: Review Focus 3; ledger rows are absent from the Changes route and present in
  Evidence. Probe checks: `findings evidence overflow`.

### Task 10: Forecast

**Files:** Modify `web/views.js` (`forecastView`, `readerChart`, `newFormatChartCards`,
`chartIndex`), `web/screen.css`, tests.

- [ ] Run charts as small multiples; form by contract kind and shape (spec section 5); a
  Chart/Table toggle per card; "Basis and limitation" as a visible footnote; sources to the trace
  icon; a chart gap draws C32 with its stated reason; the HTML Model frame gains only a framed
  header.
- [ ] Tests: a two-row period contract is not drawn as a line; Review Focus 3. Probe checks:
  `findings overflow`.

### Task 11: Library home and report history

**Files:** Modify `web/views.js` (`library*`, `historyView`), `web/screen.js` (library hash state
unchanged), `web/screen.css`, tests.

- [ ] C26 filter bar with counts in place of the five selects (same filter state and hash);
  issuer cards with a C21 strip and a Cards/List toggle (List keeps today's table); C4 strip in
  the issuer detail; a live run row shows C31 and C13.
- [ ] History: vertical C15, one entry per run with state mark, date, pathway, C21, "What
  changed" link.
- [ ] Tests: every existing filter and sort still changes the result set and the hash; the module
  names of a run appear once (as dot labels), not as a text list. Probe checks: `overflow`.

### Task 12: Run activity

**Files:** Modify `web/views.js` (`activityView`, `liveRun*`), `web/screen.css`, tests.

- [ ] C13 steps with C31 state marks; a loader and elapsed time on the running module only; C23
  on completion or failure; C32 for the empty and unreadable states. Spend is not shown.
- [ ] Tests: the loader's animation is inside the reduced-motion media query; the unreadable
  state names what to do. Probe checks: `overflow`.

### Task 13: Browser tests and full probes

**Files:** Modify `tests/test_library_*_browser.py`, `tests/browser_probe_*.js` as the new markup
requires (constraint 11).

- [ ] `uv run pytest -q -m browser` green; every probe check green on the real run and on
  `fixtures/synthetic-new-format`.
- [ ] Report: each changed assertion with its old and new form.

### Task 14: Records

**Files:** Modify `AGENTS.md` (the reader line: where the library draws source references),
`VERIFICATION.md` (one entry, file stays under 1,000 lines), `apps/issuer-library/README.md`,
`docs/visualisations/2026-11-13-screen-component-map.md` (status and what was built).

- [ ] Reader check against the September VMO2 reference and the fidelity check (probe output),
  recorded with scope: one historical run, earlier methods.
