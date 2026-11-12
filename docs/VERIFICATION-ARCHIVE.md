# Verification archive

Entries moved verbatim from VERIFICATION.md when older than two days.

## 2026-11-10 — Short live test: an inbox drop and the forecast modules (ruling `2026-11-10-short-live-test.md`)

Scope: two live runs on sol-medium over the retained TDG FY2024 public files, both written outside
the repository (`/private/tmp/claude-501/rbot-live`, `…/rbot-live2`); `main` at `9aec393`. Each
proves its dated case and route only; outputs are unreviewed candidates.

- Inbox (`deploy_workflow.inbox.watcher`, `--cap 10 --settle-seconds 10 --poll-seconds 5`): a
  copied folder dropped into `inbox/earnings_update/` at 08:56:09Z was claimed at 08:56:21Z, ran
  CP-0, CP-1, CP-1B, CP-1D and CP-5 live (39 calls, 3 drafts rejected and repaired), delivered at
  09:10:39Z and was filed as `issuers/TransDigm Group Incorporated (tdg)/2024-09-30
  earnings_update.html`. Recorded spend USD 1.0761. Watcher-built library in headless Chrome: one
  row; the run id opens Overview; 5 of 5 module pages render; "Open report" opens the report in
  the app; Run activity shows the run finished, its spend and a link to the filed report that
  exists on disk; no script error.
- Forecast (`cpos_launch --modules CP-0 CP-1 CP-2A CP-2G --cap 10`): four modules accepted,
  delivered in 17 minutes, USD 1.1979. The forecast model was **not published**: CP-2G's inputs
  block now validates (the 2026-11-09 failure is gone) but the handoff declares a blocked
  forecast with every driver null ("the forecast horizon is not locked and required invocation
  and upstream acceptance validation cannot be completed through the supplied tools"). The library
  lists the run, 4 of 4 module pages and the report render, and Forecast reads "No forecast model
  was published from this run's files".
- A run without a report cannot be produced by a run: `library_index` lists only runs with a
  verified delivered report, and `credit_os_catalogue.run_record` always writes `handoff_href`
  empty, so "Open primary handoff" never draws in this build. "Handoffs only" appears only if a
  listed delivery fails cataloguing.
- Not verified: the Forecast tab with a published model (no retained or new run has one); a
  refused drop, the queue limits and a restart of the watcher (covered by tests, not run live);
  Windows; analytical accuracy of either run.

## 2026-11-09 — TDG live runs on sol-high, compared with medium

Scope: historical TDG FY2024 (as of 2024-09-30), ruling `docs/rulings/2026-11-09-tdg-sol-high-test.md`.
Sources were read from Final-workflow-PY `data/public-corpus/v1/TDG` (not modified).
- `runs/cpos-tdg-sol-high-001` (CP-0, CP-1, CP-1A): accepted, USD 1.38, 41 calls, no repairs.
- `runs/cpos-tdg-sol-high-cp2-001` (CP-0 to CP-2): accepted, USD 1.63, no repairs; report published.
- Comparison with the retained medium runs is in `runs/tdg-effort-comparison.md`; only automated
  checks plus a spot check of the tabled figures against the 10-K were applied, not an analytical review.

## 2026-11-09 — Lean copy of final-workflow `ffb75ba` (branch `claude/busy-bell-obfret`)

Scope: what this repository holds and runs; Linux, offline. No provider was called.
- Import commit `5c6e61b`: files the two Python steps need, byte-identical to final-workflow
  `ffb75ba` (checked file by file), with their tests and synthetic fixtures. Not copied: `runs/`,
  `deliverables/`, `data/`, most of `cases/`, `examples/`, the Go application and its web
  front end, design work and archives.
- Adaptations, in the next commit: Python-only `packaging/build.py` and `Smoke-test.ps1` (no Go,
  no bridge); the package ships an empty `engine/docs/rulings` and none of this repository's
  rulings; the CI workflows `checks.yml` and `weekly-tests.yml`; `tests/known-failures.txt`
  (3 failures carried over from final-workflow's list: a missing `2026-10-31-context-plan.md`).
- Tests left in final-workflow because they read retained runs: `test_run_expectations.py`,
  `test_handoff_delivery.py`, the retained-run check in `test_library_index.py` and the live
  evidence check in `test_cpos_launch.py`.
- Passed: the CI fast set as written in `checks.yml`, 1011 tests with the 3 known failures
  deselected (library 37+7, packaging 8, reader summary 51, launcher 116, provider/model tests);
  `logic.test.cjs` 5; the browser check 2 (Chromium over `file://`, no request, no script error);
  the quality gate against `5c6e61b`, 0 findings. The offline run review and a library update
  were run as `Smoke-test.ps1` does them, with the checkout's Python on Linux.
- Also passed: `test_handoff_loop.py` 30. `test_financial_workflow.py` passed its first 11 tests
  and was stopped at the 15-minute limit with no failure; the weekly job runs it whole.
- Not verified: anything on Windows (wrappers, package, Edge over `file://`); a live model run (the
  owner runs the Copilot test locally).

## 2026-11-09 — TDG live runs on sol-high, compared with medium

Scope: historical TDG FY2024 (as of 2024-09-30), ruling `docs/rulings/2026-11-09-tdg-sol-high-test.md`.
Sources were read from Final-workflow-PY `data/public-corpus/v1/TDG` (not modified).
- `runs/cpos-tdg-sol-high-001` (CP-0, CP-1, CP-1A): accepted, USD 1.38, 41 calls, no repairs.
- `runs/cpos-tdg-sol-high-cp2-001` (CP-0 to CP-2): accepted, USD 1.63, no repairs; report published.
- Comparison with the retained medium runs is in `runs/tdg-effort-comparison.md`; only automated
  checks plus a spot check of the tabled figures against the 10-K were applied, not an analytical review.

## 2026-11-10 — Inbox: a run started just before a hard kill is adopted (tip `6ea3a9b`)

Scope: macOS, fake and real-shaped launchers, plus the real launcher started without `--live` and
without a key. No provider was called. Nothing ran on Windows.
- Change: the launcher writes its own process ID to a per-run file (`DEPLOY_WORKFLOW_PID_FILE`) as
  its first step and refuses to start if it cannot; the watcher adopts a `running` record with no
  process ID from that file, and marks it `interrupted` only after 60 s without one. This closes
  the first item under "Known and left open" in the entry below.
- Passed on the tip, exit 0: the eight affected pytest files (381 passed, 1 skipped: the paid
  test); the quality gate, 0 findings in 7 changed files.
- Review (adversarial): approved, 0 High, 0 Medium, 1 Low fixed test-first (a corrupt process-ID
  file stopped the watcher). The reviewer killed a real watcher with SIGKILL before the start,
  after the start and after the file was written: each time one process at most, the live run
  adopted and one report filed, or `interrupted` after the grace with nothing started.
- Not verified: Windows (on a virtual environment the process ID in the file may differ from the
  one the watcher started; the file replace; liveness checks); a launcher that needs more than
  60 s to reach its first line; process-ID reuse after a reboot; a paid run.

## 2026-11-10 — Inbox automation (branch `claude/user-journey-2939fb`, tip `f13ce44`)

Scope: synthetic runs through a fake launcher on macOS. No provider was called, the real launcher
was never started with `--live`, and nothing ran on Windows or over a network share. This is not
proof of any pathway or issuer.
- Built: `deploy_workflow.inbox` (drops, filing, runs, activity, watcher, startup), the live Run
  activity view, the per-pathway context form, `Start watcher.cmd`, the standing ruling
  `docs/rulings/2026-11-09-inbox-automation.md`. Design:
  `docs/superpowers/specs/2026-11-09-inbox-automation-design.md`.
- Passed on the tip, with `origin/main` `51203a9` merged in: `tests/test_inbox_*.py`,
  `test_cpos_launch.py`, `test_update_library.py`, `test_issuer_library_packaging.py` — 365 passed,
  1 skipped (the paid test); `static.test.cjs` and `calendar.test.cjs` 28; the browser tests 5
  (local Chrome over `file://`); the quality gate, 0 findings in 19 changed files.
- One test runs the watcher with the real library rebuild and a real-shaped completed run; the
  others replace the library's listing. The real launcher's offline step was exercised by a
  reviewer's probe only, not by the suite.
- Reviews: each task; the whole branch (approved with fixes, 0 High, 4 Medium, all fixed and
  re-reviewed). Killing the watcher mid-run and starting another adopted the live run with one
  launch, one record and one filed report; that probe is timing-sensitive on a loaded machine.
- Known and left open: a hard kill between a run's process start and the save of its process ID
  leaves that run untracked (it is shown `interrupted` and is not restarted, while its launcher
  may still spend up to the cap); deleting `watcher.lock` while a watcher runs lets a second one
  start; queued runs never expire; setting the clock back allows 30 more starts that day.
- Not verified: anything on Windows (the file lock, sharing-violation readiness, the retry on a
  refused replace, folder permissions after the move, `Start watcher.cmd`, Edge over `file://`);
  one measured live run (whether USD 20 covers a pathway on `sol-medium` is unmeasured); the full
  test suite (weekly job).

## 2026-11-10 — Refactoring and optimisation sweep (branch `claude/refactor-optimisation-sweep-01c49e`, tip `dc90974`)

Scope: synthetic tests, scratch harnesses and a scratch copy of four retained runs on macOS. No
provider was called and nothing ran on Windows. Report with all measurements and the open rows:
`docs/sweeps/2026-11-10/REPORT.md`.
- Fixed test-first: `state.declared` was `None` for every real handoff (now Blocked 11, Requires
  More Work 2 on `cpos-tdg-sol-medium-all-001`); the watcher accepted a cap above the ruling's
  USD 20; an overflowing source-text page number stopped the build; a drive-relative source name
  was accepted.
- Measured: watcher step at 200 ended runs 801.6 ms to 2.4 ms (16,200 file opens to 0); library
  rebuild of four runs 0.777 s to 0.576 s, bytes read 185.4 MB to 65.7 MB, built library identical
  (build time masked).
- Gates on `dc90974`, exit 0: the quality gate (0 findings in 19 files); the `checks.yml` pytest
  command plus the chips and inbox tests (1,392 passed, 7 deselected); node page logic (97 pass).
- Reviews: per task and whole branch; one Medium (a "failed" run with a live launcher kept its
  empty activity entry) fixed in `f28523a` and re-reviewed.
- Not verified: Windows; a live watcher or provider path; the browser tests and the page's
  rendering of the declared statuses; the full suite; ten open or decision rows listed in the report.
- Follow-up (branch `claude/sweep-followup-ruling-rebuild`, tip `e74f2b4`; owner, 2026-11-10): the
  two decision rows are ruled and fixed test-first. The watcher starts and launches only under its
  standing ruling; a library-rebuild error of any `Exception` type is logged, shown on the page and
  retried instead of stopping the watcher. Exit 0 on `e74f2b4`: the quality gate; the same pytest
  command (1,412 passed, 7 deselected). Review found the first ruling test passed without the
  guard; it is now a cause test (fails with the check removed). The packaged layout was checked by
  building the package into a temporary folder on macOS, not on Windows.
- Outstanding items and a review of `main` (branch `claude/sweep-outstanding-items`, base
  `b2ae395`; owner, 2026-11-10; written without sub-agents): the seven open rows are fixed
  test-first (F2, F4, F5, F6, F7, D4, B1) and B3 is accepted and pinned. The review added four
  fixes: a page range in handoff text hung the library build; one malformed line in a run folder
  ended the watcher; `--poll-seconds 0` and like settings were accepted; the PR check ran no inbox
  or chips test. Exit 0 on the branch: the quality gate; the PR check's pytest command with those
  tests added (1,437 passed, 7 deselected); node page logic (107 pass). The library built from the
  four retained runs is byte-identical to `main`'s. Not verified: Windows; a live watcher; the
  inbox tests on Linux before this PR's own check; no independent review (the owner ruled out
  sub-agents), only the author's adversarial pass.

## 2026-11-10 — Run report Phase A (library Overview and module pages)

Scope: the library page Overview is now a run report (what the run establishes, credit story by
question, findings register, open items, module matrix); module pages split View from Statements
and registers. Spec `docs/design/2026-11-09-run-report-spec.md`, plan
`docs/superpowers/plans/2026-11-09-run-report-phase-a.md`. Commits fdb21ee..a887ba4, then merge
4dad3d9 of `origin/main` 51203a9.
- Real-data check: deterministic rebuild of one retained run, `cpos-tdg-sol-medium-all-001`, into a
  temporary folder; no model call, nothing written under `runs/` or `library/`. Result: `7 of 20
  modules reach a conclusion · 13 not assessable`; established CP-1, CP-1A, CP-2, CP-2D, CP-2E,
  CP-3C, CP-DR; findings register 33 rows shown, 84 with not-assessable modules included; 58 checks
  pass; key-numbers differences against the previous page 0.
- Gates on 4dad3d9, all exit 0: `node --test apps/issuer-library/credit_os/web/static.test.cjs` (82
  pass); pytest on the seven affected files (300 passed, 1 skipped: the paid live test); `uv run
  python tools/quality_gate.py --base origin/main`.
- Reviews: per-task and whole-branch; one Medium fixed test-first in a887ba4 (an empty
  `committee_status:` took the next front-matter line as the status); the merge resolution was
  reviewed separately and found sound.
- Merge ruling: front matter follows `main` (dc2320c): a level-2 `Front matter` section whose
  locator covers only the lines between the `---` markers. Placements of the 20 real handoffs are
  identical before and after.
- Second merge 85d47f6 of `origin/main` 2ecfc8f (inbox automation), then fix 4abfb18: the review of
  that merge found the live Run activity chips had lost their running, done and waiting colours to
  the run report's `.chip` rule; fixed test-first. On 4abfb18, exit 0: node (93 pass), pytest on the
  affected files with the inbox tests (409 passed, 1 skipped, run on 85d47f6; the two page files
  re-run on 4abfb18, 34 passed), the quality gate, and the same real-run rebuild.
- Not verified: runs other than `cpos-tdg-sol-medium-all-001` were only built without error; widths
  below 1280px; keyboard and screen-reader use; a bold `**Not assessable**` bottom line or an empty
  Confidence cell reads as established (neither occurs in retained data); the Overview opened with
  no run context; the branch diff is 2,245 lines against the 800-line cap.

## 2026-11-10 — Design pass on the run report and library (branch `claude/impeccable-report-library-595877`)

Scope: `/impeccable` critique, harden, layout and polish on `apps/issuer-library/credit_os/web/`
(page parts only; no Python under `src/` or `apps/issuer-library/*.py` changed). What changed and
the two spec amendments: `docs/design/2026-11-10-impeccable-pass.md`. Base `origin/main` c145b16.
- Real-data check: the four retained TDG runs built into a scratch folder through a link to `runs/`
  (nothing written under `runs/` or the checkout's `library/`; no model call). Word-level diff of the
  drawn page text against the `origin/main` page parts on `cpos-tdg-sol-medium-all-001` (Overview,
  CP-1, CP-6), `cpos-tdg-sol-high-001` (Overview) and the library table: the only differences are
  coverage labels (module names to codes), three repeated chart legends and three repeated
  "Missing values have no bar" notes removed, and four run ids added to library rows. CP-6: none.
- Measured in headless Chrome from disk at 1440 and 1280: no horizontal overflow on the four
  routes; library table 922px in a 922px box at 1280 (was 964px); run-report tables are not scroll
  boxes and their headers stick at 0px; heading levels have no skip on Overview, CP-1, CP-6; long
  unbroken, RTL, CJK and emoji text injected into every bottom line, finding and limitation does not
  widen the page at 1280 or 500px; the Overview prints as 15 pages and CP-1 as 8.
- Driven in the app's browser pane at 1440: library row to run, outline click and Tab+Enter to a
  part (route, scroll, current entry, focus ring), count of citations without a page to the
  inspector and Esc back to the count, a chart chip to the inspector, the Reference route.
- Gates, all exit 0: `node --test` on `static.test.cjs` and `calendar.test.cjs` (104 pass);
  `uv run pytest tests/test_library_page_browser.py tests/test_update_library.py
  tests/test_library_index.py tests/test_credit_os_store.py` (94 passed, browser tests included);
  `uv run python tools/quality_gate.py --base origin/main`.
- Reviews: critique by two independent agents; confidence review fixed three findings (a
  half-retagged chart heading, the catalogue opening on a no-output module, print without
  background fills); rewrite tournament run inline (one hoist applied, the rest held).
- Detector after the pass (1280): no skipped-heading or line-length finding on the four routes;
  the remaining tiny-text findings are the committed 11px label size and nested-cards is the app frame.
- Basis clamp (owner, 2026-11-10, after the PR opened): the library's ratio basis shows three lines
  per row. Probe at 1440 and 1280: 12 of 12 basis cells clamped, each cell's title equals its full
  text, rows 145–161px, table 922px in 922px at 1280. Node 105 pass; the three library pytest files
  70 passed.
- Second hardening pass (CSS only, `/impeccable harden`): headless Chrome probes on the built TDG
  library. Six routes × seven widths (1440–500px), inspector open and closed: no page or canvas
  overflow. Hostile text (240-character unbroken words, long URLs, Arabic/Japanese/emoji) in handoff
  fields and library rows at 1280 and 500px: none after the fix (before: band +1,194px, library
  table 7,802px in 922px). Edge states (malformed and unknown run-part routes, nothing established,
  no reader summaries, 400 findings, no outputs, 404 library rows in 50ms): no script errors.
  Library and run report printed to PDF and read. 106 node tests, 94 pytest (library set, browser
  included), quality gate exit 0. Known: on portrait A4 the printed library table runs 8px past
  its card edge (nine columns of whole words); nothing is cut. Module tables with hostile cell text
  scroll sideways in their own box, as before.
- Library simplification (owner: one item per column; `/impeccable` distill): ten single-value
  columns, issuer rail replaced by an Issuer select, filters as a toolbar. Headless Chrome on the
  built TDG library: rows 41px at 1440 and 1280 (one 31-character run id wraps at 1280); six routes
  × six widths without overflow; hostile text contained at 1280 and 500px; a flow probe with a
  synthetic second issuer covered `?issuer=zzz` in the address, the select, Reset, Any run, sort,
  row selection and the panel heading, with no script error. Printed to PDF and read (the run id
  column wraps to several lines on portrait A4). 106 node tests; 103 pytest (library set, browser
  included). Superseded by this: the basis clamp and its focus rule above.
- Not verified: a real print dialog and printers; Safari and Firefox; a screen reader; Windows
  forced colours (rule written, not rendered); touch input; the inbox-built library with Run
  activity; runs without charts or with a committee band; whether a keyboard-only reader finds
  the full basis (it is in the selected-run panel, not on focus).

## 2026-11-10 — Library links to the report and to retained sources (branch `claude/library-open-report-link`)

Cause: the page matched a catalogue deliverable to the store's report by a server address ending
`&embedded=1` and linked only root-absolute paths; the static build writes `reports/…` and `../…`
with the query removed. So "Open report" (row, selected run, deliverables list) was plain text and
"Open retained source" never appeared. Present since the web assets were copied (`5249e4e`).

- Fix in `views.js`: match by the one address the build writes; `libraryPath` accepts only those two
  relative forms and refuses a scheme, a root, a backslash, a query, an empty or dot segment and
  percent-encoded dots or slashes.
- Tests written first and seen failing: the browser test on a fixture library (row and selected-run
  links to `#W-Reports/<delivery>?c=run-a`, source link to the retained `CP-1.md`) and a node test
  of the path guard (4 accepted, 31 refused forms). 107 node tests; 107 pytest (library set,
  browser included); quality gate exit 0.
- Real library rebuilt from this branch over the four TDG runs, headless Chrome: each row's
  deliverable opens its own report in the app; the two file links in the selected-run panel exist
  on disk; no script error. The row link is regular weight so rows stay 41px at 1440 and 1280.
- End-to-end walk on merged `main` before the fix (same build): library → run id → Overview → 20 of
  20 module pages → chip → evidence inspector; Reports, Evidence, Calendar, Run activity render;
  75 of 76 file links exist (`../activity.js` is written only by the inbox watcher).
- Not verified: the inbox watcher, a live model run and delivery (no provider run started); an
  inbox-built library; a run with a published forecast model or without a report ("Open primary
  handoff"); the Windows package; Safari and Firefox.

## 2026-11-10 — Reader charts over time (branch `claude/period-charts`)

Owner: "Charts with periods should be transposed, with period on the x axis". Every reader chart is a
`Chart data:` table whose first column is Period (`store.py` `_chart_table`), so `readerChart` now
draws columns over periods: periods along the x axis in table order, one column per series from a
zero baseline (a raised baseline when a value is negative), the exact value on each column, the
series named once in a legend, and each period's chips under its label. Values, periods, labels and
chips are unchanged; a value that is text still prints n.a. with the text in its title.

- Tests written first and seen failing (two in `static.test.cjs`); one older test updated for the
  new value markup. 109 node tests; `tests/test_library_page_browser.py` 20 passed; quality gate 0.
- Built TDG library in headless Chrome, CP-1 Key numbers (Leverage, Interest cover, Liquidity, Debt
  maturities): fits at 1440, 1280, 1024, 768 and 500px and with the inspector open; no value label
  outside its card; no two value labels overlap; chips stay under their own period. Below about 96px
  a period the chart scrolls sideways in its own box (Debt maturities at 500px). Printed to PDF:
  charts print whole.
- Not verified: a chart with a negative value in real data (fixture only); Safari, Firefox.

## 2026-11-10 — CP-2G entry values in the launcher's instructions (branch `claude/forecast-publication`)

Comparison (module CP-2G, live run `tdg-forecast-001`, sol-medium, TDG FY2024): the handoff declared
a blocked forecast with every driver null. Its stated causes were procedural, not evidential: "What
forecast horizon should be locked: FY2025–FY2027?" and "required invocation and upstream
acceptance validation cannot be completed through the supplied tools". The method sent has an
entry protocol (`forecast_horizon`, `base_period`, `cases`; "block_model_when_material_forecast_
scope_is_missing") that takes its values from a command qualifier the launcher never gave.

- Change: `FORECAST_BLOCK` (launcher preface, outside the method block) now states the command
  with those three entry values and says the helper scripts are not run in this transport and are
  not a reason to block. A driver the evidence cannot support still stays null.
- Test written first and seen failing (`test_the_forecast_instructions_lock_the_entry_values_…`).
  `tests/test_cpos_launch.py` 157 passed, 1 paid test skipped; quality gate exit 0. Offline
  prepare: CP-2G's instructions carry the paragraph; CP-0, CP-1 and CP-2A instructions are
  byte-identical; `tdg-forecast-001` is still listed as on the current methodology.
- Live proof (`/private/tmp/claude-501/rbot-live3/runs/tdg-forecast-002`, sol-medium, 16 minutes,
  USD 1.3061, same four modules): the procedural block is gone. CP-2G's request now reads "FY2025,
  FY2026 and FY2027 as the locked annual forecast horizon" and `qa_status` moved from Blocked to
  Restricted. The forecast model is **still not published**: every driver is still null, now for
  a stated evidential reason ("essential operating, cash-conversion, exit-interest and financing
  assumptions cannot be supported by the supplied evidence. This is an evidence constraint, not
  a request to reconfirm the locked entry values"). It declined even capex, where it quotes
  management's FY2025 range of 2.5% to 3.5% of sales, because no point value or later year is given.
- Driver rule (owner, 2026-11-10, "Yes, allow judgment"): the preface now asks for a value for every
  driver, as labelled `Analyst Interpretation` anchored to a stated figure where guidance is absent,
  and keeps null only when nothing stated can anchor it. Test changed first and seen failing; 157
  passed; gate exit 0.
- Third live run (`/private/tmp/claude-501/rbot-live4/runs/tdg-forecast-003`, 13 minutes,
  USD 1.0801): **not a test of the driver rule.** CP-2A itself came back Blocked this time ("missing
  financing documents and legal-perimeter evidence"; it was Requires More Work in -001 and
  Restricted in -002 on identical instructions and sources), and CP-2G stopped at the method's
  required-dependency gate, as the method directs. No forecast was published.
- Not verified: that CP-2G gives drivers under the new rule, and the Forecast tab with a published
  model; no run has produced one. CP-2A's run-to-run variation between Blocked and usable on the
  same inputs is unexamined. "Open primary handoff" was left as it is: no run can reach it.
- Why CP-2A blocked in -003 (read from the three retained runs, no provider call): the pinned context
  declares `attachments.legal_documents: executed`, but the pack is public filings only. In -003
  CP-0 wrote that gap as conditioning "full downside readiness", CP-1's readiness table then marked
  "CP-2A complete failure, covenant and funding-access sequence | Not ready", and CP-2A read that as
  a prohibition from both predecessors. In -001 and -002 CP-0 and CP-1 did not write those lines
  and CP-2A ran. The trigger is the context's declaration; the form's value for this pack is `none`.
  Not tested: a run with `legal_documents: none`.
- Fourth live run (`/private/tmp/claude-501/rbot-live5/runs/tdg-forecast-004`, `legal_documents:
  none`, USD 1.2605): CP-2A came back Restricted and CP-2G gave a labelled, anchored value for every
  driver, so the driver rule works. The forecast was still **not published**: `ebitda_margin`,
  `tax_wc_pct_revenue` and `interest_rate` were written at 38 decimal places (calculator output
  pasted in) against the inputs schema's four, and delivery dropped the block after payment.
- Fix: the preface states the four-decimal limit, and the in-loop check now parses CP-2G's block
  against CP-1 (`_forecast_issues`), so a block delivery would refuse goes back for repair. A
  declined (all-null) block is still accepted, and the repair text offers declining, so the model
  can always finish. Delivery's fail-open stays as a backstop. Tests written first and seen failing;
  the five invalid-block cases now assert a repair request rather than a report without a model.
  `tests/test_cpos_launch.py` 160 passed, 1 paid test skipped; quality gate exit 0.
- Fifth live run (`/private/tmp/claude-501/rbot-live6/runs/tdg-forecast-005`, run-004 context,
  USD 1.4039): **forecast published** (`cp_forecast_published: true`; `forecast.md` and
  `forecast_exact.json` delivered). CP-2G wrote four-decimal drivers (`ebitda_margin` "0.4802",
  anchored to CP-1's FY2024 EBITDA 3,813 on sales 7,940) on its first draft, so the new check passed
  it; its two repairs were reader-summary issues. CP-2A gave no shock, so only the reference case
  exists. The library built for that workspace shows the Forecast tab: revenue 8,757 / 9,658 /
  10,652, Adj EBITDA 4,205 / 4,638 / 5,115, total leverage 5.74x / 5.18x / 4.68x. Spot check by
  hand: 7,940 × 1.1029 = 8,757 and 8,757 × 0.4802 = 4,205.
- Not verified: the in-loop forecast check repairing a real model's bad block (it was not
  triggered live); the tab's note mentions an upside case that this run does not have, and the
  model has no assumption register. Resuming a pre-fix run directory whose retained CP-2G answer
  this check now rejects would stop with `cpos_feedback_changed`; runs 001–004 are not resumed.
- Spend across the six live runs of this test: USD 1.0761 + 1.1979 + 1.3061 + 1.0801 + 1.2605 +
  1.4039 = 7.3246.
