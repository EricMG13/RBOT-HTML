# Credit OS Static Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace RBOT-HTML's library page with Credit OS's library and issuer pages, rendered as static files built after every completed run.

**Architecture:** Credit OS's screens are fed by two JSON documents (`/api/catalogue`, `/api/workspace`). `update_library.py` builds both at build time — the catalogue from `library_index.build_library` plus run metadata, the workspace from Credit OS's stdlib `store.workspace_store` — and writes them as `library/data.js` beside a copy of the Credit OS web assets. A static boot script reads that data instead of fetching. `cpos_launch` rebuilds the library after a completed run.

**Tech Stack:** Python 3.13 (stdlib + pydantic, already pinned), vanilla JS/CSS copied from Credit OS, Node for `.cjs` checks, Playwright not required (existing `browser_check.cjs` pattern).

**Spec:** `docs/superpowers/specs/2026-11-09-credit-os-static-pages.md`

## Global Constraints

- Source of copied code: `~/Documents/Final-workflow-PY` commit `07e14eca` (read only; never modified). Record it in `apps/issuer-library/credit_os/SOURCE.md` with each copied file's sha256 at that commit.
- No new dependency. No server, no `fetch`/XHR in built pages; pages open from `file://` with no network request (CSP `default-src 'none'` plus the self/file sources the assets need).
- Only `library_index`-listed runs appear. No legacy seed, no curated legacy runs (store.py's `CURATED_RUNS` and pinned legacy routes must yield nothing for RBOT runs).
- Never mutate run folders: built output goes only under `<workspace>/library/` (git-ignored); refuse to write through a `library` symlink (existing rule).
- Gates: `uv run python tools/quality_gate.py` (changed Python, whole new files), targeted pytest with `timeout 300`, `node --test` for `.cjs`.
- Every brief/review: no stub or fake value standing in for real behaviour; no catch-all hiding a failure unless the fail-open is documented and logged; answer keys are not edited by the implementer; each report ends with `Not verified:`.

## Review Focus

1. A run whose CP-1A event table heading differs ("Credit-relevant history and event status" vs "Dated business history and acquisition register") — Calendar must find it by the table's first header starting with `Date`. Test in Task 4.
2. Free-form event dates ("May 21 and June 6, 2024", "1993 inception…", "October 2024") — shown exactly as written, ordered by the first year then month found, undated rows last; no date invented. Test in Task 4.
3. Opening `library/index.html` from `file://` — the report frame must load without the HEAD `fetch` Credit OS uses (it fails on `file://` and would show "missing"). Browser check in Task 5.
4. A library rebuild failure after a successful paid run — the run still exits 0 and its report stays published; the failure is printed to stderr and logged. Test in Task 6.
5. A workspace with zero listed runs — library shows the empty state, not a script error. Test in Task 5.

---

### Task 1: Copy Credit OS assets and store

**Files:**
- Create: `apps/issuer-library/credit_os/web/` ← copy `screen.css brand.css report-adapter.css report-adapter.js views.js screen.js screening.js hydrate.js fonts/ icons/ brand/` from Final-workflow-PY `apps/issuer-library/web/`
- Create: `apps/issuer-library/credit_os/store.py`, `apps/issuer-library/credit_os/catalog.json` ← from `apps/issuer-library/engine/`
- Create: `apps/issuer-library/credit_os/SOURCE.md` (commit, file list, sha256 at source, and every edit made after copying)
- Test: `tests/test_credit_os_store.py`

**Interfaces:**
- Produces: `credit_os.store.workspace_store(workspace: Path, catalogue: dict[str, Any]) -> dict[str, Any]` (unchanged signature); module importable as `apps/issuer-library/credit_os/store.py` via `sys.path` insert of `apps/issuer-library` (same pattern `update_library.py` uses for `src`).

- [ ] **Step 1: Write the failing test** `test_store_reads_a_listed_run`: build a workspace with `tests/library_fixtures.make_run(ws, "run-a")`, call `workspace_store(ws, {"real": [], "sources": {}})`; assert every module handoff of the fixture appears in `store["outputs"]` with a `sha256` key present in `store["handoffs"]`, and `store["reports"]` holds the fixture's report path. Second test `test_store_has_no_legacy_routes`: the same call yields no output or report whose path is outside `runs/run-a/`.
- [ ] **Step 2:** Run `timeout 300 uv run pytest tests/test_credit_os_store.py -q` → FAIL (module missing).
- [ ] **Step 3:** Copy the files byte-identical; then fix only what the quality gate reports in `store.py` (2 × E501, 12 strict-mypy errors measured on 2026-11-09), recording each edit in `SOURCE.md`. No behaviour change.
- [ ] **Step 4:** Tests pass; `uv run python tools/quality_gate.py` exits 0.
- [ ] **Step 5:** Commit `feat(library): copy Credit OS web assets and store from final-workflow 07e14eca`.

### Task 2: Credit OS catalogue from the library index

**Files:**
- Create: `src/deploy_workflow/credit_os_catalogue.py`
- Test: `tests/test_credit_os_catalogue.py`

**Interfaces:**
- Consumes: `deploy_workflow.library_index.Library` (`runs: list[dict]` entries as built today).
- Produces: `catalogue(workspace: Path, library: Library) -> dict[str, Any]` returning `{"real": [run, ...], "sources": {id: source}, "workspace": str(workspace), "issues": [...]}`. Each run dict has the Credit OS `Run` fields the screens read: `id` (= run folder), `issuer` (context `identity.ticker`, else `issuer_id` upper), `name` (issuer_name), `title` ("Credit Snapshot"-style pathway title from `PATHWAY` labels), `workflow`, `sector`, `country`, `currency` (context `run.reporting_currency`), `date` (as_of), `period` (context `current_period` upper, e.g. `FY-2024`), `period_kind` ("Annual"), `summary` (CP-2 else latest module reader-summary bottom line), `gaps` (main limitations), `metrics`, `artifacts` (one per verified delivery: `folder`, `available: true`, report path), `files`, `checklist: null`.
- `metrics`: from CP-1's `### Chart data: leverage | interest cover | liquidity` tables, latest period row: `leverage`, `net_leverage`, `coverage`, `cash`, `undrawn`. Each metric's `source` is a key into `sources` with `{path, sha256, line, quote}` where `quote` is the exact table row text and `sha256` the handoff's. A `Not supplied: …` cell gives no metric (missing ≠ zero).

- [ ] **Step 1: Failing tests** with an answer key written from the fixture, not from code: `test_catalogue_lists_only_library_runs` (two fixture runs, one excluded by library_index → one catalogue run); `test_metrics_quote_the_handoff_row` (fixture CP-1 chart tables with FY2024 `6.57 | 4.93`, `3.29`, `6261 | 843` → metrics values `"6.57"`, `"4.93"`, `"3.29"`, `"6261"`, `"843"`, units `x`/`US$m`, and each `sources[...]['quote']` equals the row line verbatim and `line` its 1-based line number); `test_not_supplied_is_absent` (`Not supplied: reason` cell → key absent from `metrics`); `test_identity_from_context` (ticker, name, sector, currency, date from the run's `context.json`).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement; read handoffs only through paths and hashes `library_index` verified.
- [ ] **Step 4:** Tests pass; quality gate exits 0.
- [ ] **Step 5:** Commit `feat(library): build the Credit OS catalogue from listed runs`.

### Task 3: Static shell — library and issuer pages without run controls

**Files:**
- Create: `apps/issuer-library/credit_os/web/index.html` (from Credit OS `index.html`), `apps/issuer-library/credit_os/web/static-boot.js` (replaces `boot.js`), `apps/issuer-library/credit_os/web/shared.js` (moved verbatim from `actions.js`: `applyTitle`, `shownRunHref`, `presentRun`; the calls to `loadRunActivity`, `installNewRun`, `installSettings` are deleted, not stubbed)
- Modify: copied `views.js`, `screen.js` (call sites only; record edits in `SOURCE.md`)
- Test: `apps/issuer-library/credit_os/web/static.test.cjs`

**Interfaces:**
- Consumes: `window.CREDIT_OS_DATA = {catalogue, workspace}` set by `data.js` (Task 5).
- Produces: `static-boot.js` sets `DESIGN_DATA`, `DESIGN_WORKSPACE`, `DESIGN_CATALOGUE`, `DESIGN_APP` exactly as `boot.js` did, after `hydrate(workspace)`; loads `views.js`, `shared.js`, `screen.js`; no `fetch`, no polling, no `watchRuns`.
- Rail: Issuer library, Reports, Search only. Destinations `CP-OS`, `W-NewRun`, `W-Settings`, `W-Help` removed from `installDestinations`; `#new-run` section removed from `index.html`.
- Report frame: drop the HEAD `fetch` in the frame loader; rely on the frame `load` event and the existing timeout message.

- [ ] **Step 1: Failing test** (`node --test`, static assertions on file text): `index.html` has no `W-NewRun`, `CP-OS/activity`, `W-Settings`, `W-Help` link; `static-boot.js`, `views.js`, `screen.js`, `shared.js` contain no `fetch(` and no `setInterval(`; `installDestinations` keys equal exactly `W-Library W-Overview W-Calendar W-Reports W-Evidence W-Forecast`.
- [ ] **Step 2:** Run `node --test apps/issuer-library/credit_os/web/static.test.cjs` → FAIL.
- [ ] **Step 3:** Make the edits.
- [ ] **Step 4:** Test passes.
- [ ] **Step 5:** Commit `feat(library): static Credit OS shell without run controls`.

### Task 4: Calendar from any run's CP-1A, all modules listed, Forecast state

**Files:**
- Modify: copied `views.js` (`calendarSections`, `calendarRun`), `screen.js` (`eventTimeline`), navigator module list
- Create: `apps/issuer-library/credit_os/web/calendar.js` (pure functions, no DOM)
- Test: `apps/issuer-library/credit_os/web/calendar.test.cjs`, extend `static.test.cjs`

**Interfaces:**
- Produces: `eventTable(sections) -> {headers, rows} | null` — the first table in a CP-1A output whose first header starts with `Date` (case-insensitive); `eventOrder(cell: string) -> [year, month] | null` — first 4-digit year in the cell, and the first English month name (full or 3-letter) found before or after it, month `0` when none; `orderEvents(rows) -> rows` — stable sort by `eventOrder`, rows with `null` last, keeping text exactly.
- Calendar tab shows "Issuer events" for any run whose CP-1A output has an event table; the hard-coded `order` map and `pins['CP-1A']` lookup are removed. Hedge schedule route stays only if a CP-2E output exists.
- Navigator lists every module in `catalog.json` (20); a module the run did not produce shows "Not run in this run". Forecast with no model keeps "No forecast model was published from this run's files".

- [ ] **Step 1: Failing tests** using the two real CP-1A event cells as the answer key: `eventOrder("May 21 and June 6, 2024")` → `[2024,5]`; `eventOrder("1993 inception; history through FY2024")` → `[1993,0]`; `eventOrder("October 2024")` → `[2024,10]`; `eventOrder("Subsequent period")` → `null`; `orderEvents` keeps input text byte-identical and puts the `null` row last; `eventTable` finds tables under both headings `Credit-relevant history and event status` and `Dated business history and acquisition register` and returns `null` when the first header is `Category`. `static.test.cjs`: no `'May 8, 2023'` literal remains in `screen.js`.
- [ ] **Step 2:** Run both `.cjs` tests → FAIL.
- [ ] **Step 3:** Implement and wire.
- [ ] **Step 4:** Pass.
- [ ] **Step 5:** Commit `feat(library): calendar from any run's CP-1A event table; list every module`.

### Task 5: Build the static library

**Files:**
- Modify: `apps/issuer-library/update_library.py` (writes the `library/` folder), `apps/issuer-library/README.md`, root `README.md` (library section)
- Delete: `apps/issuer-library/static/{app.js,logic.js,logic.test.cjs,library.css,template.html}`; keep or adapt `browser_check.cjs` to the new page
- Modify: `apps/issuer-library/packaging/build.py` file list
- Test: `tests/test_update_library.py` (rewrite), `tests/test_library_page_browser.py` (adapt)

**Interfaces:**
- Consumes: Task 1 `workspace_store`, Task 2 `catalogue`, Task 3/4 web files.
- Produces: `update_library(workspace: Path) -> Library` writing `<workspace>/library/index.html`, `library/data.js` (`window.CREDIT_OS_DATA=` + JSON), `library/web/*` assets, and `library/reports/<run>/<delivery>/report.html` = the delivered report with `report-adapter.css`, `brand.css` and `report-adapter.js` inserted before the last `</body>` (Credit OS `report_presentation`); store `reports[].path` rewritten to that copy. Written to a temp folder then renamed over `library/`; refuses a `library` symlink. CLI unchanged: `python apps/issuer-library/update_library.py [--workspace FOLDER]`, prints listed and excluded runs as today.

- [ ] **Step 1: Failing tests:** `test_writes_static_library` (fixture workspace → `library/index.html`, `data.js`, one presented report; `data.js` JSON `catalogue.real[0].id == "run-a"`); `test_presented_report_keeps_original` (original delivery bytes unchanged, sha256 equal before/after); `test_refuses_library_symlink`; `test_empty_workspace` (no runs → page builds, `catalogue.real == []`); browser test: open `file://…/library/index.html` in Chromium, no console error, no request outside `file://`, library table shows the run, Overview shows the four chart cards, Reports tab frame loads the presented report.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Pass; quality gate 0; run on the real workspace `uv run python apps/issuer-library/update_library.py --workspace "$PWD"` lists exactly the two sol-high runs.
- [ ] **Step 5:** Commit `feat(library): build Credit OS library and issuer pages as static files`.

### Task 6: Rebuild the library after a completed run

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_launch.py` (after the report is published in `main`)
- Test: `tests/test_cpos_launch.py` (two tests)

**Interfaces:**
- Consumes: Task 5 `update_library(workspace)`; workspace = the parent of the run folder's `runs/` directory; skip with a printed note when the out folder is not under a `runs/` directory.

- [ ] **Step 1: Failing tests:** `test_completed_run_updates_the_library` (monkeypatched `run_live_handoffs` returning a report path in `tmp/runs/x`; assert `update_library` called once with `tmp`, stdout has `Library:`); `test_library_failure_keeps_the_run` (`update_library` raises `OSError` → exit 0, stderr names the failure and the manual command).
- [ ] **Step 2:** Run `timeout 300 uv run pytest tests/test_cpos_launch.py -k library -q` → FAIL.
- [ ] **Step 3:** Implement; the catch is narrow (`OSError`, `ValueError`, `Refused`) and documented as fail-open.
- [ ] **Step 4:** Pass; quality gate 0.
- [ ] **Step 5:** Commit `feat(launch): update the library after a completed run`.

## Owner questions (answered)

1. Global rule caps a PR at 800 changed lines. Task 1 copies about 4,600 lines verbatim (store.py 2,874; views/screen/screening JS ~1,500; CSS). Accept the copied files as excluded from the count (as RBOT's own import commit `5c6e61b` was), or split into two PRs?

   **Answer (owner, 2026-11-09):** "Exclude copied files" — files copied verbatim from Credit OS (listed in `SOURCE.md`) do not count toward the 800-line cap; edits to them and all new code do.
