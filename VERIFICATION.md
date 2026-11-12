# Verification record

Keep one running record here. A pass applies only to the stated scope. Earlier verification of the
engine is in [EricMG13/final-workflow](https://github.com/EricMG13/final-workflow)'s
`VERIFICATION.md`, which also keeps the retained runs this copy leaves out.

## 2026-11-12 — CP-8 fixes, rounds 1-3 (branches `claude/cp8-changes-r1`, `-r3`)

Scope: engine, method and run start service, offline, no provider call. Round 1: pack schema `cpos-changes/2` (difference
for equal units; `comparable` yes/no/judge; refs `E1`/`C1`); the checker reads each row and every printed difference; a CP-8
not accepted, an unbuildable pack or a hold over the cap delivers without CP-8; the approval names the earlier run and the
digest binds it (`--prior`); display name "Changes since the last run". Round 2: `same_period`, `definition_resolved`. Round 3:
the sentence word lists are deleted; the check is mechanical (K1-K12): `changes.same_period` (same date, else same fiscal
year), a withheld difference in no checked line, every figure of a checked line held in the pack, its definition texts or a
handoff of either run (the launch caller passes this run's handoffs and `prior/*.md`), fact rows carry held amounts but no
pack value or difference (Q-1). Answer keys are hand-written in `tests/test_changes.py`. Changed expectations (by the rulings):
`test_a_cp8_that_is_not_accepted_loses_only_itself...` (exit 0); the summary digest is `bound(digest, prior)`; 500 US$m not
held; "debt was 333"; two movement-in-words cases and one trend assertion dropped; a test renamed. Real pair (cpos-tdg-sol-medium-all-001
then tdg-reader-format-001): five measures, all `judge`; 20 `E`, 11 `C` refs; CP-8's first request 318,153 bytes, hold 5.73.
Results before the merge with main: fast set 1,439 passed, browser 138 passed, quality gate 0; reviewer probes `t4r3_same_period_rows`,
`t4r4_fact_row_leak`, `t4r4_sentences`, `t4r4_same_period`, `t4r2_prior` pass. After the merge: MERGERESULT
Not verified: a real model writing the ledger or judging a definition; whether the estimate matches a live first request; the
library's Changes section; a real CP-8 handoff against the new figure rule (hand-written mini pack and probes only).
## 2026-11-12 — CP-8 in the run: prior run, pins, comparison pack, check (branch `claude/cp8-changes`, decisions M5, M7, M8)

Scope: engine and method, offline, no provider call. Built: `changes.py` (prior-run rule, `prior/*` pins, `changes.json`),
`changes_check.py`, registry fan-in, `cp8.md`, `changes.json` in the delivery, the summary's `changes` line. Answer keys are
hand-written in `tests/test_changes.py`; isolation is checked on the requests sent. Changed: `test_cpos_launch.py` no longer
passes every method to `--modules`; `test_run_start_page.py` asserts `changes`. Results then: fast set plus `test_changes.py`
1,063 passed; all non-live, non-browser, non-slow less `tests/model` and `tests/test_financial_workflow.py` 1,477 passed;
browser 100 passed; quality gate 0. Not verified: any real model writing CP-8's registers; whether CP-8's request fits a long
run's context; real earlier runs on the lean-copy deliveries; the library's Changes section.

## 2026-11-12 — Run start page: effort (Fast / Balanced / High) and model (GPT Sol / Claude Opus)

Scope: offline, macOS; no provider was called and no run was started. Owner instruction recorded as
the 2026-11-12 amendment in `docs/rulings/2026-11-11-run-start-submit.md` (configs sol-medium,
sol-high, opus-medium, opus-high; USD 20 cap unchanged).
- Effort map: `BALANCED_HIGH_MODULES` (CP-1A, CP-1D, CP-2, CP-2A, CP-3, CP-3C, CP-4, CP-4C, CP-6);
  basis per module in `runs/tdg-mixed-effort-comparison.md`. Twelve of twenty assignments are
  inferred from module type, not measured.
- Engine: config `opus-high` (claude-opus-5-5, effort high, opus-medium price object);
  `cpos_launch --balanced`. Service: answers carry `model` and `effort`, defaults gpt/balanced,
  other values only at Advanced; six (model, effort) pairs map to the four configs; start-up
  requires the ruling to name all four; Claude refused without the Anthropic key. Page:
  two Advanced-only radio groups and a "Model and effort" summary row.
- Passed: quality gate 0 findings (42 files); 1,787 tests across the page, launcher, handoff loop,
  run start, inbox, packaging and `tests/model` files. Four failures, none from this change: the
  three in `tests/known-failures.txt`, and `test_upload_to_filed_report_with_the_real_launcher`,
  which fails identically on a clean `38d23de` checkout (empty `record.report`) and is not listed.
- Reviews: task reviews of engine, service and page, and a security review of the paid-launch
  gating (five invariants, seven saved probes), no High. One Medium fixed with a failing test
  first (the Claude-unavailable refusal now links to Pathway); Low test gaps closed in the same round.
- Page seen in a browser at desktop and 375 px (no horizontal overflow); controls appear only at
  Advanced with Balanced and GPT Sol selected. Not a reader check: no report page changed.
- Open, not fixed: a queued Claude run started after a restart without the Anthropic key fails
  as "launcher exited 2" and counts toward the daily limit (nothing is spent); a pre-change
  sealed-but-unmoved submission fails with a misleading reason; on the CLI a ruling naming
  sol-medium also admits `--balanced` / `--high-modules`; AGENTS.md names
  `tests/nightly-known-failures.txt` but the file is `tests/known-failures.txt`.
- Not verified: any live call (Opus at high effort, Balanced on either model, Claude from the
  page); the summary and Submit against a running service by hand; Windows; the full suite;
  confidence-review and rewrite-tournament on this change.

## 2026-11-12 — Per-module effort (`--high-modules`) and one mixed-effort TDG live run

Scope: historical TDG FY2024 (as of 2024-09-30), ruling `docs/rulings/2026-11-12-tdg-mixed-effort-to-cp2.md`;
one paid run on gpt-6.1-sol. Not a current credit view; one run per setting.
- Code: `HandoffExecutor(effort_by_module=...)`, passed by `run_live_handoffs` and `cpos_launch
  --high-modules`. `tests/test_handoff_loop.py` and `tests/test_cpos_launch.py` passed (472, 1 skipped);
  quality gate 0 findings; task review passed with three Low test gaps open (pass-through to
  `run_live_handoffs`, seed digest, multi-turn). confidence-review and rewrite-tournament not run.
- Live: `runs/cpos-tdg-sol-mixed-cp2-001` (main checkout), high on CP-0, CP-1A, CP-1D, CP-2, CP-2A.
  `live/calls.jsonl` records high on CP-0, CP-1A, CP-1D and medium on CP-1, CP-1B, CP-DR, CP-1C.
  Six modules accepted; stopped at CP-1D (three drafts refused: "Invalid Markdown table header",
  which names no table; the fault was a 7-column header over an 8-column separator). USD 3.46.
  CP-2, CP-2A, CP-2E did not run; no report was published.
- Comparison with the saved all-medium runs: `runs/tdg-mixed-effort-comparison.md` (handoffs read
  by a separate reviewer, tabled figures checked against the 10-K). High: clear gain on CP-1D
  (unaccepted draft), none on CP-0, inconclusive on CP-1A; the medium modules needed no more.
- Not verified: CP-2 onward under mixed effort; a same-code all-medium control (instructions
  changed after both baselines); the full test suite.
## 2026-11-12 — CP-2G facility schedule (branch `claude/cash-flow-model-comparison-498459`)

Owner waiver 2026-11-12: the 800-line PR limit is waived for this branch's pull request (about 1,290
changed lines: plan document about 340, tests about 520; the whole-branch review found no sensible split).

Scope: CP-2G facility schedule: offline synthetic tests only; no provider called, no model response
retained; a live CP-2G run that states `facilities` has not been done; the Forecast page was not
exercised with the new `forecast_exact.json` keys.
- `uv run pytest tests/test_cpos_facilities.py -q`: exit 0, 55 passed (the answer key puts the debt outside the stated facilities at the analyst's rate: 37.5, 34.8, 30.6).
- `uv run pytest tests/test_cpos_launch.py -q -k "forecast or told_how"`: exit 0, 24 passed; the whole
  file: 507 passed, 1 skipped (the paid live test).
- `uv run python tools/quality_gate.py`: exit 0, 0 findings.
- Independent checks: the output for a block without facilities is byte-identical to origin/main 36b6d8f
  (sha256 e5017389abc2c878a0b0bae323a50bcbadf35c3a08f676f277c1505b9d047089 over the five model files);
  the arithmetic matched an independent Fraction calculation over 74 accepted seeded random blocks
  (11 with debt outside the stated facilities, per-case rates included; reviewer's probe, not in the suite); the
  adversarial review found and fixed two Medium defects (negative total debt from repayments above
  base debt; unbounded floating all-in rate). Three boundary tests each kill their mutant (`0 <= rate`
  to `0 < rate`; `unallocated < 0` to `<= 0`; `due < start` to `<=`).
- Known limits: debt outside the stated facilities bears interest at the analyst's assumed rate, not a sourced one; with base debt
  missing no unit check runs on facility balances; the printed-in-CP-1 check for rate terms accepts
  any matching percent anywhere in CP-1.

## 2026-11-11 — Starting a run from an earlier run: the whole branch (branch `claude/initiating-runs-existing-issuers-4a8739`)

Owner waiver 2026-11-12: the 800-line PR limit is waived for #52 (2,784 changed lines).

Scope: offline, macOS, headless Chrome against the run start service over a fake launcher (no provider
called, no paid run). The whole branch after its whole-branch review: carry from an earlier run (locked
ID, documents, answers, pathway, module subset, turns), the existing-issuer notice, "Start again from
this run", and "Start a run" on the library's Report history. This wave fixed the review's seam findings
(`?from=` with a submitted run still held, carried-file marks against uploads, the carried pathway and
subset/turns marks, `open_regular` through `platform_io.regular_open`, hidden names, refused listings).
- `uv run pytest tests/test_run_start_prior.py tests/test_run_start_submissions.py tests/test_run_start_service.py -q`: exit 0, 170 passed.
- `uv run pytest tests/test_run_start_page.py tests/test_library_page_browser.py -q --deselect tests/test_run_start_page.py::test_upload_to_filed_report_with_the_real_launcher`: exit 0, 131 passed (91 page, 40 library), none skipped (Chrome ran).
  `test_upload_to_filed_report_with_the_real_launcher` fails on the base already and is not part of this change.
- Review probes (`wb_seams.py`: 10 passed; the earlier probes exit as before, `probe_carry_races.py`'s
  seal-between-copies case still fails: ruled out of this wave).
- `uv run python tools/quality_gate.py`: exit 0.
- Fidelity: the notice text, marks, load messages and the progress note are asserted in the DOM Chrome builds.
- Reader check: not done; pending. No real run was read against the September VMO2 reference.
- CP-8 summary lines (the "changes section" and the two-prior-runs lines) are not built: the CP-8 redesign has not merged.
- Windows not run: the `O_BINARY` open of a carried file is from reading `platform_io.regular_open` only.

## 2026-11-12 — Run start page browser tests after the preset change (branch `claude/web-search-run-page`)

The browser tests (`-m browser`) were not run for the commits from 73b499b (presets) to d185d83. Run then:
`tests/test_run_start_page.py` 14 failed, 42 passed (at 0e2c564: 1 failed, 55 passed). Causes: (a) real page
defect, `build()` required "Current period" whenever CP-2G was in the run; CP-2G joined credit_snapshot and
covenant_refinancing, so a Basic submission that the launcher accepts (`cpos_launch.prepare` takes a blank period)
was blocked. The page now requires it for an earnings update only, labels it recommended, and adds a "Note" row
for CP-2G when it is blank (10 tests). (b) stale expectations: Standard now shows the research-questions stage
for credit_snapshot and covenant_refinancing (CP-DR is in every pathway); the services-forecast and limit-tick
tests now count the page's own CP-DR note, CP-2A no-legal-documents limit and CP-2G reading it. (c) pre-existing
since PR #46: a delivery files no report page, so `record.report` is `""`; the assertion now says so (the run
page's link to the library's Report history for the run is checked by the next test). The research-text
assertion already matched the final copy. After: that file 56 passed; `-m browser -k "run_start or context_form
or library or inbox"` 100 passed, exit 0; the fast set 756 passed, exit 0; quality gate 0 findings, exit 0.
Not verified: a forecast run with a blank current period through a live provider.

## 2026-11-12 — Web search from the run page; leaked citation markers (branch `claude/web-search-run-page`, decisions M1, M4)

(a) Paid test, this dated case only (TDG FY2024, ruling `2026-11-11-cpdr-web-search-live-test.md`, run `tdg-cpdr-web-001`): CP-0, CP-1, CP-DR and CP-1C accepted, charged USD 3.39131650. CP-DR located HEICO and
Howmet figures and CP-1C read them. Defect: the delivered CP-DR handoff held 54 provider citation markers
(U+E200 `cite` U+E202 `turn..view..` U+E201) in reader prose, which the eight prose checks did not catch.
Fix: markers are removed from a searching module's answer before the check (count in `<n>.markers.json` and a
`citation_markers_removed` event; provider response unchanged), plus prose check 9 for any other shape
(reader-ruling amendment). On that handoff the removal leaves 0 markers and adds no double space or
space before a comma or full stop. Not verified: `store:false` behaviour was not separately inspected, peer
figures were not checked against the cited pages, analytical accuracy.
(b) This change, offline (no provider call): the standing run-start ruling lists `web-search`; `prepare`'s
cap check holds the CP-DR search fee (USD 0.16) as the live loop does; the summary passes it; the page's
approval summary says what goes to OpenAI; READMEs updated. Tests: `test_citation_markers.py`, the
`prepare` and ruling tests in `test_cpos_launch.py`, `test_context_form.py`, `test_run_start_submissions.py`.
`test_inbox_scheduler.py::test_a_submission_is_run_by_the_real_launcher_and_listed` failed identically on the base
`claude/forecast-layer1` (canned answers; stopped at the checker); commit ebd4c13 fixed it (the canned launcher
answers CP-2G with a forecast block).
(c) Fix round 1 (security review, offline, no provider call): the page and ruling no longer say queries "use
public names only" as a fact: the module is told to, the queries it sent are kept in `<n>.response.json`, and
`flag_search_queries` flags afterwards any query with a supplied file name or a source figure of 4+ digits (years
1900-2100 excepted) as a `search_query_flagged` event and `<n>.queries.json` (detection, not prevention; the
library's Run record does not show the count: its store has no field). Owner ruling 2026-11-12: web search for
`public` and `private` cases, off for `synthetic` (one rule, `web_search_offered`; offline hold, live hold and
the `Web:` line agree; the page says before Submit whether the run searches). Source guidance and a `Source type`
cell on web rows (METHODOLOGY-REVIEW.md): no paid run has exercised the new source guidance. Markers: a marker
never spans lines, stripping is linear, the tool result tells the model how many were removed and an edit may quote
marked text, check 9 covers `cite\s*turn\d+[a-z]+\d+` anywhere in the handoff and only U+E200-U+E202.
Forecast riders: `~~~` fences are code, `\|` stays in its cell, working capital is the cell sign-reversed as CP-2G
reads it (the base's test fixtures now print wc as `(10)`).

## 2026-11-11 — Forecast from layer 1 (branch `claude/forecast-layer1`, decision M3)

CP-MODEL (preset or `--modules`) means "publish the forecast"; it makes no model call. Without CP-2G,
CP-1 gets a layer-1 variant of the forecast block (base operands as CP-1 prints them, run-rate drivers,
no cases, no shock) and the forecast comes from it; with CP-2G the block, checks and files are unchanged.
A bad or absent CP-1 block is not a CP-1 check: the model is withheld through the existing fail-open
(stderr, `model_not_published` event, `forecast_failure` in the completion record). Published limits
say "run-rate inputs the CP-1 handoff stated"; the library shows them under Model limitations, unchanged.
Offline, synthetic handoffs only (no provider call, no run folder touched): new tests fail on the base
and pass now. `uv run pytest tests/test_cpos_launch.py tests/test_handoff_loop.py tests/test_update_library.py
tests/test_credit_os_store.py -q -m "not live and not browser"` 666 passed, exit 0; `uv run python
tools/quality_gate.py` 0 findings, exit 0. Changed expectations: `--modules CP-MODEL` is no longer refused;
earnings_update's report scope now names the run-rate forecast; the publish-failure stub takes a source
argument.
Fix round 1 (the operand-key row rule) was replaced in round 2 after re-review: CP-1 keeps its natural
tables; each layer-1 base operand states `{"amount","reason":null,"row","period"}`, the exact first-cell
label and period header it was read from, and Python reads that one cell (tables outside fences, `## Sources`,
the block and the reader passages; trimmed and emphasis-stripped, case-sensitive; `1,000`, `-1,000`, `(1,000)`,
U+2212 parse as signed; `1,000k`, `12%`, `n.a.` do not). Outflows (cp2g.OUTFLOWS) compare by magnitude, all
others signed; zero, or several differing, cells refuse the operand by name (fail-open unchanged). CP-2G
refuses a `row`/`period` and keeps its check byte for byte. The block still does not vouch for a reader
figure in `figure_issues`. Probes `r2_m1_row_defeats.py`, `m3_layer1_operand.py`, `m3_block_vouches_reader.py`,
`r2_m2_block_edges.py` exit 0 (the first two pass partly because the old-shape blocks they build carry no
row/period and are refused; the accept/refuse cases are in the new tests). `uv run pytest tests/test_cpos_launch.py
tests/test_prose_checks.py tests/test_handoff_loop.py tests/test_update_library.py -q -m "not live and not browser"`
690 passed, exit 0; `uv run python tools/quality_gate.py` 0 findings, exit 0.
Known limits: driver values are not checked against their anchors (the rationale is free text); runs
interrupted before this change refuse to resume. Not verified: a real model writing the layer-1 block; the library on a layer-1 model beyond the
store tests; `tests/test_financial_workflow.py`.

## 2026-11-11 — Pathway presets: CP-DR and CP-2E everywhere (branch `claude/module-presets`)

Decisions M1-M7 are recorded in `docs/rulings/2026-11-11-module-presets-and-changes.md` (a decision
record; it does not lift the pause).

(a) Live run facts, this dated case only (ruling `docs/rulings/2026-11-11-reader-format-live-test.md`): TDG
FY2024 public files, context `runs/tdg-context-2024-09-30.json`, `credit_snapshot`, sol-medium, cap USD 15;
run folder outside the repository. CP-0, CP-1, CP-1A, CP-2, CP-4, CP-3, CP-5 and CP-6 were all accepted and
delivered; charged USD 3.20906590; two drafts were rejected and repaired within the retry limit (CP-1, CP-3).
Reader check so far: only CP-6's reader passages were read by the controller: judgement first, sources on
Basis lines, no codes in sentences. Remaining weakness: pipeline wording in reader text ("producer-owned
corrections remain open", "canonical financial amount", "open producer QA findings") and dense prose.
Not verified: the other seven modules' prose; a side-by-side against the VMO2 reference; analytical accuracy.

(b) This change, offline only (no provider call, no run folder read or written): M1 and M2 presets, CP-2G
added to credit_snapshot and covenant_refinancing, CP-8 removed from portfolio_decision, context-form
copy. Gate results: `uv run pytest tests/test_cpos_launch.py
tests/test_context_form.py tests/test_inbox_activity.py -q -m "not live and not browser"` 509 passed, exit 0;
`tests/test_cp8_comparison.py tests/test_handoff_loop.py` 44 passed, exit 0; `uv run python
tools/quality_gate.py` 0 findings, exit 0. Plans per pathway were prepared offline by the parametrised
test (every pathway, four peer sources); `tests/test_financial_workflow.py` was not run (over the
fast-test limit). M3-M7 are decided and not built here.

## 2026-11-11 — Runs on earlier methods are listed and marked (branch `claude/list-earlier-method-runs`)

Scope: offline, macOS; synthetic fixtures only (`tests/library_fixtures.py`, the fake launcher run). No
model call, no run folder under `runs/` read or changed. Owner decision 2026-11-11: a run whose module
methods changed since it ran is listed with `method_changes` and shown as "Earlier methods" (Report history
status, run label; Run record lists the changes). Other refusals are unchanged. Real TDG runs were not
rebuilt here.
- Gates: `uv run pytest tests/test_library_index.py tests/test_update_library.py tests/test_credit_os_catalogue.py -q` 90 passed, exit 0; `node --test` static, reader, calendar 257 pass, exit 0; `uv run python tools/quality_gate.py` 0 findings, exit 0.

## 2026-11-11 — Issuer library presentation to the reader ruling (branch `claude/library-layout-637b87`)

Owner waiver 2026-11-11: the 800-line PR limit is waived for #47 (5,969 changed lines).

Scope: offline, macOS, headless Chrome; the library app (`apps/issuer-library`) only. No provider was
called, no run was started, no stored handoff or run folder was changed (retained runs were read through
a symlinked `runs` folder in a scratch workspace). No run in the new handoff format exists yet: the new
format was seen only on a hand-made synthetic fixture (`apps/issuer-library/fixtures/synthetic-new-format/`,
built into a scratch workspace by `fixtures/build_synthetic_run.py`); the earlier format on the three
listed retained TDG runs (`cpos-tdg-sol-high-001`, `cpos-tdg-sol-high-cp2-001`,
`cpos-tdg-copilot-sol-medium-002`). This is not the reader check against the September VMO2 reference
that AGENTS.md requires for a presentation change: that needs a real new-format run and stays open.
- Built (decisions 3-7, 9, 10, 12, 14; H1, H3, H4, H5, H7): rail without Reports; per issuer Report
  history, Overview, Modules, Forecast, Evidence with a run label; delivered report view, its adapter and
  the Calendar tab retired; Overview selects passages only (CP-6 else CP-2 lead, bottom lines, limitations
  de-duplicated by the check-7 normalisation, key charts, nearest dates); flat Modules navigator of the
  modules that ran; figures and a quiet Basis link open the inspector; earlier-format trailing citations
  move verbatim behind Basis; Evidence's four lists with handoff and instruction copies under
  `library/downloads/`; Run activity shows live runs only.
- Gates (HEAD of the branch at push): `node --test` reader/static/calendar 245 pass, exit 0; `uv run
  pytest -m "not live and not browser"` on the eight library test files 348 passed, exit 0;
  `tests/test_library_page_browser.py` 38 passed; `uv run python tools/quality_gate.py` 0 findings, exit 0.
  `tests/test_library_reader_refs.py` asserts every Basis item and Source cell of each synthetic handoff is
  reachable from the rendered page, with hand-written counts.
- Walk-through at 1440 px and 375 px on both libraries: every page renders with no console error except
  the pre-existing missing `../activity.js` when opened outside the run start service; a figure opens the
  inspector by keyboard (Enter) and Esc returns focus; no horizontal overflow at 375 px.
- Known limits: the inspector shows a source page's excerpt for a Basis item only once the engine's
  `credit_os_chips` change (PR #46) is merged; earlier-format dates written as text cannot feed Nearest
  dates; document dates of source files are not recorded anywhere, so Evidence shows "Not recorded";
  key charts are selected per module from the catalogue (rows carry no chart identity);
  `src/deploy_workflow/run_start/service.py` still links finished runs to `library/reports/`, which this
  branch no longer writes (fixed on the engine branch).

## 2026-11-11 — Reader standard and checks in CP-OS; delivered report retired (branch `claude/reader-engine-d46913`)

Scope: instructions, checks and delivery changed; proven by synthetic passages and offline tests
only. No provider was called and no run was started. No retained model response written under the
new standard exists yet, and the reading check of one real run against the September VMO2
reference (decision 11) is not done.
- Changed: CP-OS instructions (`owners/cpos_launch.py`): every prose module is told to open
  `## Findings` with `### Bottom line`, `### Key findings`, `### Contrary evidence and what would
  change the view`, `### Limitations`; data modules (CP-0/CP-PARSE, CP-1, CP-1C) and blocked
  modules only `### Bottom line`; the Basis line form of H3; figures with currency or unit; no
  labels; persona kept with "Lead with the judgement; use data to support it, not to narrate it.";
  CANON_SHARED's reader-facing layer and reading order sent to prose modules. `### Reader summary`,
  the per-module opening H3, the CP-2-only reader standard and its front lines are removed.
- Checks: the eight H6 prose checks (`prose_checks.py`) run in the CP-OS handoff check on the reader
  passages; a failure is repair feedback naming check, line and text, inside the existing retry and
  cap. Hand-written passing and failing passages per check (`tests/test_prose_checks.py`); check 7
  across a run shown with the fake provider. Instructions and checks were cross-checked by a
  whole-branch review: every instructed form passes all eight checks. The Reader-summary figure rule was restored
  for the new passages as a fidelity check (`figure_issues`, labelled `Fidelity check:`, not a ninth
  prose check): every reader-passage figure must appear outside the reader passages with the same
  sign, unit and scale (owner, 2026-11-11). Review fixes in the same entry: the library build skips
  a delivery with no `report.html` (`apps/issuer-library/update_library.py`, the cause of the 14
  failures above); check 6 also takes the first-column letter+digit cells of `## Calculations`
  tables (period labels excepted); a Basis line after a blank line is sentence text.
- CP-8 requires an eighth dimension, Presentation (`tests/test_cp8_comparison.py`).
- Delivery: new deliveries write no `report.html`; completion records carry `delivery_sha256`
  (of `delivery.json`); HTML Model, charts, calculation JSON and forecast files unchanged. Earlier
  runs with `report.html` are still listed and accepted as CP-8 bundles (tests on both formats).
- Passed, exit 0: the affected fast tests (`test_cpos_launch`, `test_prose_checks`,
  `test_reader_summary`, `test_handoff_loop`, `test_library_index`, `test_cp8_comparison`,
  `test_credit_os_catalogue`, inbox tests, `test_run_start_page`, `test_update_library`,
  `test_credit_os_store`; `-m "not live and not browser"`) on this branch merged with the library
  branch (`claude/library-layout-637b87` at 3294c8d) in a scratch worktree: 899 passed;
  `tools/quality_gate.py`: 0 findings. Before the `update_library.py` fix, 14 of those tests failed on
  its `report.html` read.
- Limitation (owner ruling: left as is): `owner_rendering.py:992`, `financial_rendering.py:167` and
  `rendering.py:162` still write `report.html` outside CP-OS.
- Not verified: any real model response to the new instructions; the reading check against VMO2;
  the browser test of the library's Run activity link (library side); the full weekly suite.

## 2026-11-11 — Reader and issuer report ruling, documents only (branch `claude/reader-ruling-docs-2d2c2a`)

Scope: documents only. Changed: `docs/rulings/2026-11-11-reader-and-issuer-report.md` (new),
`AGENTS.md`, `METHODOLOGY-REVIEW.md`, `README.md` and this entry. No code, test, prompt text or app
changed; no provider was called. Nothing enforces the ruling yet: CP-OS still sends the reader
standard to CP-2 only, delivery still publishes `report.html`, and the library is unchanged.
- The two following sessions must prove, against the ruling's "Handoff contract":
  module instructions, checks and delivery: every prose module is sent the four reader passages
  and the Basis line form, data modules the bottom line; the eight prose checks block a handoff
  and send a targeted repair request within the existing cap, each shown failing on a crafted
  handoff and passing on a conforming one; CP-8 compares presentation; fidelity checks unchanged.
  Library presentation: Report history, Overview selection (CP-6 then CP-2 lead), the flat
  Modules navigator, Evidence's four lists and the Basis/inspector behaviour, each on a
  conforming fixture and on an existing run labelled "Earlier format" with stored handoffs
  byte-unchanged.
- Judgement quality is proven only by reading one real run per change against the September
  VMO2 reference; no paid run is allowed in these sessions, so that reading stays open.

## 2026-11-11 — Run start page: the inbox watcher and folder drop removed (branch `claude/no-nothing-6d5113`)

Scope: offline, macOS, with stand-in launchers (the fake launcher `tests/fixtures/fake_launcher.py`
and the canned-provider launcher `tests/fixtures/canned_provider_launcher.py`). No provider was
called and nothing ran on Windows. This is not proof of a paid run.
- Built: `inbox/watcher.py` is now `inbox/scheduler.py` (`Scheduler`; the folder scan, claim,
  settle timer, rejection into `inbox/failed`, `_template` copies and the watcher's own command
  line are gone); `Layout` and `ensure_layout` moved to `inbox/layout.py` and make no `inbox`;
  `inbox/drops.py` and `Start watcher.cmd` are deleted; `Start run page.cmd <root> [address]`
  runs `-m deploy_workflow.run_start`; the package ships the 2026-11-11 ruling; the issuer-ID
  length limit moved from the drop check to the summary. Records the watcher wrote still load and
  show; every run it queued (a record with no submission) is marked failed at start-up with a
  reason and is never started.
- Passed on this tree, exit 0 (final wave, after the whole-branch review): `uv run pytest` on
  `tests/test_inbox_scheduler.py`, `test_inbox_runs.py`, `test_inbox_activity.py`,
  `test_inbox_filing.py`, `test_inbox_layout.py`, `test_run_start_submissions.py`,
  `test_run_start_scheduler.py`, `test_run_start_service.py`, `test_run_start_page.py`,
  `test_context_form.py`, `test_context_module_options.py`, `test_cpos_launch.py`,
  `test_issuer_library_packaging.py`, `test_library_page_browser.py` and `test_library_index.py`:
  933 passed, 1 skipped (the paid test), in Chrome, so the 55 page tests ran;
  `uv run python tools/quality_gate.py`: 0 findings; `node --test` on `static.test.cjs` and
  `calendar.test.cjs`: 187 passed (the library's own JavaScript, which CI runs).
- Final wave, what it changed: the summary joins the launcher's forecast with the page's own
  rules and asks a tick for every gap, limited and will-refuse item and every check that has a
  fix; the as-of and legal-disagreement rules are limited for the whole run; Run activity shows the
  submitter and, when served, links the library's own copy of a finished run's report (the page's
  finished view links the same copy); library files are opened with `platform_io.regular_open`
  (binary, no wait on a FIFO); a timeout the service meets itself is a 500; a reload with a
  saved submission the service no longer holds says so and offers a new submission as a
  separate click; `runs.prepare` and `Scheduler.run_forever` are deleted.
- Reviewer probes after the wave (`.superpowers/sdd/2026-11-11-staged-run-start/probes/`): the four
  review gaps, the served library report, the FIFO and the issuer-ID wording pass. Three probes
  still fail by ruling or scope and are explained in `final-wave-report.md`: the filed
  `issuers/...` link (the ruling links the library's copy, no new route), the service's answer
  for a submitted submission (the ruling makes the page, not the service, say it), and the refused
  folder's file list (not in this wave). `t8r1_server_side_timeout.py` tests Python's own
  exception classes and cannot pass; `tests/test_run_start_service.py` covers the behaviour.
- CI deselects every page test (they need Chrome), so no CI run touches the approval or Submit.
- The real launcher ran in one scheduler test (canned provider answers, the real library
  rebuild); the others stand in a launcher.
- Not verified: a paid run through Submit; whether CP-3 and CP-6 honour `module_options`; Windows
  (`Start run page.cmd`, the file lock, paths); browsers other than Chrome; more than two
  analysts submitting at once; `../runs/...` download links, which the service does not serve; the
  full test suite (weekly job); the page tests in CI (CI deselects them); Windows file opening
  (`O_BINARY` is requested through `platform_io`, not run there).

## 2026-11-11 — Work-PC change packs (`tools/work_pc_delta.py`)

Scope: offline tooling only; no analytical module, provider call or deliverable changed.
The work PC takes ZIP downloads without git, so `generate` writes a numbered pack per sync
(package/version tables from `pyproject.toml` and `uv.lock`, merged PR titles, every changed
file with the new-version line ranges, the full patch) and `check` compares any folder with
the git blob hashes in `manifest.json`.

Confidence review: same-day packs sorted by hash, not order (confirmed, fixed with a
sequence prefix); `\x1f` stripped as whitespace dropped PR titles (confirmed, fixed);
a pack's own commit leaking into the next pack (tested: excluded); renames, deletions,
names with spaces, transitive-only lock changes, CRLF re-saves, `.venv` noise (tested).
`check` matched a `git archive` ZIP of `04e7221` exactly. Whole-history pack
`472bdea..04e7221`: 5.9 MB. No symlinks in the tree (they would be reported as `extra`).

Verification: `pytest tests/test_work_pc_delta.py tests/test_quality_gate.py` 5 passed;
`tools/quality_gate.py` 0 findings. First pack `04e7221..6f5ac16` (PR #42); `check` on a
`git archive` of the PR head: identical.

Follow-up: `.github/workflows/work-pc-pack.yml` makes and commits a pack after each push to
`main`; a range with only pack-folder changes makes none (tested), and the CI fast-test
list now includes `tests/test_work_pc_delta.py`. The workflow itself first runs on merge;
a protected `main` would refuse its push (the run fails visibly; hand generation remains).

## 2026-11-10 — Visuals package 8: complete the whole-branch review

Scope: continued the interrupted `claude/visuals-p8` changes from reviewed package 7
(original tip `44108e6`). Offline synthetic tests and a deterministic rebuild from retained
handoffs; no provider call or new analytical run. Packages 1–8 were later pushed and merged through GitHub PRs #33–#40. No further rewrite tournaments,
per the current user's instruction.

Confidence review, ranked doubts and outcomes:
- **Missing evidence could force invented rows (M1).** Every owner row table now accepts its
  explicit all-gap form; the library retains the reason in `chartGaps` without a chart or an
  invalid-table complaint. Checked all independently written owner fixtures and the original
  reviewer's no-data probe. Empty unit/basis and mixed gap/data rows remain invalid. A stated
  gap in a unit/basis cell remains permitted as explicit missing information, never a guessed unit.
- **Index claims could disagree with actual pages (M2).** Not-assessable modules' charts show
  their limitation and no placement/table-form link; maps remain available as their pages draw
  them. Static regressions and the original folded-page browser probe (updated to expect the
  removed link) verify this through the generated library.
- **Event-log failure could masquerade as no history (M3/L4).** The run record carries the read
  error; the page names and escapes it. Non-object JSON records invalidate the log without
  stopping the build. Missing logs remain distinct. The shared log reader's existing tolerance
  for an unfinished final JSON line is unchanged.
- **Launcher/store disagreement could misstate figures (L1-L3/L5).** Fixed currency instructions,
  reminder status, unit constraints, peer bounds, maturity ordering, scenario count and duplicate
  class/scenario rejection. The reviewer's parity probe reports zero disagreements. Confidence
  review additionally reproduced a missing EUR period relabelling later USD figures; the chart
  now takes its unit from a numeric row. No numeric value is converted or derived.
- **Cleanup could remove a live caller (L6).** Traced callers and removed unused owner metadata,
  UI options, the redundant format lookup/CSS class and comparison-registry intermediate;
  repeated allocation/map instructions are emitted once. Affected fixtures still pass.
- **Package limit (M4).** Removed one redundant test-heading comment from package 2 and restacked
  the later local packages. Package 2 is exactly 800 changed lines; each other package is below
  800. Original branch tips are retained under `refs/codex-backups/visuals-p*-before-p8-review`.

Verification (each test process bounded to 300 seconds using Python subprocess timeout because
this macOS host has no `timeout` executable):
- `uv run pytest -q --tb=short -m 'not live' tests/test_cpos_launch.py
  tests/test_update_library.py tests/test_credit_os_store.py tests/test_library_page_browser.py`:
  **612 passed, 1 deselected**, including Chrome over file URLs; 84.40 seconds.
- `node --test apps/issuer-library/credit_os/web/static.test.cjs
  apps/issuer-library/credit_os/web/calendar.test.cjs`: **186 passed**.
- `uv run python tools/quality_gate.py`: **0 findings**; `git diff --check` clean.
- Retained-source rebuild into a temporary directory: `cpos-tdg-copilot-sol-medium-002`,
  `cpos-tdg-sol-high-001`, `cpos-tdg-sol-high-cp2-001`. The unfinished Copilot run was excluded
  for no completion record; `cpos-tdg-sol-medium-all-001` was excluded for the changed shared
  methodology. Original run directories were read only. This is library compatibility evidence,
  not proof that a model satisfies the new combined chart instructions or a complete TDG pathway.
- Still outside scope: paid model output for the new contracts, Windows, screen-reader/print
  testing, the pre-existing escaped-pipe parser discrepancy and the weekly full test suite.

## 2026-11-10 — Word documents (.docx) in the issuer folder (branch `claude/optimistic-johnson-bmnwip`, after main `3ac4db6`)

Owner: "Add docx compatibility too". Input only: nothing is written as Word.

- How it reads them:
  - The launcher now reads `.docx`. Like an HTML filing, a Word file is converted to text pages
    (`docx_text.py`) and pinned as `<name>.jsonl`, headed by its name and hash.
  - The text covers body paragraphs in order, table rows as cells joined by ` | `, and tabs and
    line breaks. Tracked deletions and tab-stop definitions are not text. Headers, footers,
    footnotes and comments are not read.
  - Parsing uses the workbook reader's guarded XML parse (no DTD or entity) and its size limits.
    A file that is not a Word document, or has no text, stops the launch naming the file.
- Unchanged:
  - HTML filings convert to the same bytes as before, so existing run folders still resume.
  - Old `.doc` files are still not read; the form says to save them as PDF.
- Also updated: the context form's file types (its copy is drift-tested against the launcher's),
  its help text, and README. The inbox reads the same list.
- Tests:
  - `tests/test_docx_text.py` (7) and a launcher test, written first; the tab-stop case found a
    defect, fixed before commit.
  - Launcher, context-form, inbox-drops, library-page and Word tests: all pass except 3 inbox
    permission tests that also fail on main here, because the sandbox runs as root.
  - Quality gate: 0 findings.
- Not verified: Word files made by Word itself; the tests build minimal files by hand.

## 2026-11-10 — Web search for the research module, offline (branch `claude/optimistic-johnson-bmnwip`, after main `1fbc57c`)

Owner: "Cp-dr supplies the peers … By default cp-dr always provides the peers or 1C and 2 can never
run", then "Yes" to working out web search for CP-DR. No provider was called; no paid run.

- Sources:
  - OpenAI pages fetched 2026-11-10 through owner-approved network access: the pricing page, the
    web search guide, the Responses reference and the gpt-6.1-sol model page.
  - Quoted in `cases/pricing/openai-web-search.json`: USD 10.00 per 1,000 calls plus search
    content tokens at model rates; tool `{"type": "web_search"}`; `include`
    `web_search_call.action.sources`; `max_tool_calls`; web search listed as supported for
    gpt-6.1-sol.
- What changed:
  - **Grant.** CP-DR searches only when the run's ruling lists `web-search` on its `configs:`
    line (`owners/cpos.py` `web_search_ruled`), and only on OpenAI. Other providers are refused
    before a call. The launcher prints a `Web:` line when CP-DR runs.
  - **Request.** Only CP-DR's requests carry the hosted tool, with at most 16 calls per response.
    Its system text adds the rules: public names only in a query, nothing published after the
    research cutoff, every web item cited by URL and date, figures quoted verbatim.
  - **Record.** A reply's `web_search_call` items are kept in the response record under
    `openai-web-search` and never sent back. A reasoning item before one is dropped, since it
    would go back without the item that followed it.
  - **Money.** Each searching call holds USD 0.16 more and is charged USD 0.01 per search action.
    Opening a page or searching within one is not charged; the guide names only search actions.
    A sent reply that cannot be read is charged the whole USD 0.16.
- Unchanged without the grant: the stored request and the OpenAI body for CP-2 and for CP-DR
  hash the same before and after (checked by script on both checkouts).
- Tests:
  - Written first: `tests/model/test_providers.py` (3) and `tests/test_handoff_loop.py` (3) failed
    at import before the code existed. `tests/test_cpos_launch.py` (1) fails with the launcher's
    grant wiring reverted.
  - Added after: the unreadable-reply charge test; reverting that charge to zero fails it.
  - `tests/model/test_pricing.py` pins the fee to the key file.
  - `tests/model`, the loop, launcher, library-page, context-form and inbox-watcher tests: 1,178
    passed, 3 skipped. 8 failed, every one of them also failing on unchanged code here: the 3 on
    `tests/known-failures.txt`, and 5 inbox-watcher permission tests, because the sandbox runs as
    root.
  - Quality gate: 0 findings.
- Not verified, until a paid run:
  - that web search runs with `store: false`;
  - that search content tokens are in `usage.input_tokens`;
  - that CP-DR ends a searching turn with a tool call under `tool_choice: "required"`;
  - whether its peer pack respects the cutoff;
  - whether CP-1C then has peers.
- Not done: the standing inbox ruling and every other ruling are unchanged, so web search stays off
  until the owner adds `web-search` to a ruling.
- Merged as `88c50ee` (#30). Owner: "Merge then test".
  - Ruling `docs/rulings/2026-11-10-cpdr-web-search-test.md`: CP-0, CP-1, CP-DR and CP-1C on TDG,
    `sol-medium` with web search, cap USD 10.
  - Dry launch here (no provider call) with tdg-all-001's context and a one-line stand-in source:
    the four modules are accepted and the launcher prints "CP-DR searches the web (the ruling lists
    web-search)".
  - Each call holds USD 5.73, or 5.89 for CP-DR, so the run can spend about USD 4.10 before the
    next hold no longer fits the cap. A stop there can be resumed.
  - The paid run needs the owner's machine, which has the TDG files and the key.

## 2026-11-10 — Context form against live run tdg-all-001 (branch `claude/optimistic-johnson-bmnwip`, after main `53a5632`)

Owner: "Yes do that" (compare tdg-all-001 with the form's forecast), "Your recommendation", then
"Cp-dr supplies the peers, the user does not provide them unless they specifically want to in the
context file…" and "User can provide peers but it is optional". Design note section 8. Compared
against the run's record below. The run folder was not read.

- Forecasts were made before the run reported. Of the 10 modules with a recorded outcome, the form
  flagged 9 and the launcher's `run_expectations` 5. The form's miss was CP-DR: Ready, but Blocked.
  The form's 4 Gaps for a missing source (CP-1C, CP-2H, CP-3D, CP-3) came back Blocked.
  CP-1D's Gap came back Restricted.
- CP-1D: no bridge is now Limited (its reads worked in the run).
- CP-DR: the form no longer asks for the peers' filings. Supplying peers is optional: add the
  peers' filings to the folder, which CP-DR is told to read, or give your own peer figures. CP-DR
  carries a Note, not counted: CP-OS gives no module a web search tool (`model/handoff.py`
  `TOOLS`). CP-OS sends CP-DR both cp-os's SKILL v1.1 (2026-07-22, web or hybrid research; blocks
  without web) and `cpdr.md` (2026-10-31, LOCAL). Neither reaches public peers here.
- Not changed: CP-2H, CP-3D and CP-3 had every read refused in the run, so they wait for a rerun.
  The registry keeps CP-DR optional for CP-1C and CP-2. That is a registry decision, not a form
  one.
- Tests: `test_the_research_module_supplies_the_peers_and_the_bridge_is_forecast_as_run` fails on
  the first version of this change, which asked about peer files, and passes now.
  `tests/test_library_page_browser.py` and `tests/test_context_form.py`: 45 passed. Quality gate: 0
  findings.
- Not verified: no live run of the changed forecast; one issuer, one date.

## 2026-11-10 — Sweep: end-to-end wiring (branch `claude/sweep-wiring`, base `53a5632`)

Owner: "Move to latest main - run /sweep refactoring and optimisation sweep make sure front to back
and end to end wiring." Contract and report: `docs/sweeps/2026-11-10-wiring/`. Range `c721a0f..53a5632`
(PRs 19–27). Offline, canned provider answers, no spend.

- Journeys proved at base:
  - The live TDG context round-trips through the context form, with only the intended changes. The
    launcher reads the form's output.
  - Every pathway: launcher → CP-OS → delivery → real library → five screens and `report.html`,
    with no console message and no unfilled value.
  - An inbox drop is run by the real launcher, filed byte for byte and listed. Before this, the
    watcher tests used stand-in launchers.
- No product defect was reproduced. Landed, tests and CI only:
  - `test_each_pathways_run_reaches_the_library_screens` (browser, 6 pathways).
  - `test_a_drop_is_run_by_the_real_launcher_filed_and_listed` with
    `tests/fixtures/canned_provider_launcher.py`. Dividing the watcher's `--cap` by 100 fails it
    and passes the stand-in test.
  - `test_the_library_screens_value_lists_are_the_codes`: run statuses, classification and rating
    scope in `views.js` against the Python literals; fails when a status is dropped.
  - `checks.yml` now runs `test_handoff_loop.py` and `test_context_form.py` on every PR.
- Performance, median of 5 after one warm-up, noise = max − min. `prepare()` over all 20 modules:
  23.8 ms (noise 18.0). Library rebuild of 10 run folders: 372.9 ms (noise 37.0), with no single
  hot spot. Nothing above the floor; page render unmeasured.
- `prepare(retained=)` and its resume helpers had no production caller. Owner: "Remove it". 127
  lines are gone from `cpos_launch.py`. The prepared run folder (manifest and instructions) hashes
  the same before and after for all six pathways. CP-OS's replay of pinned answers stays, and its
  test now pins them in the manifest directly. Reverting the producers pin check still fails it.
- Gates on the final tree, all exit 0:
  - quality gate: 0 findings.
  - `node --test` static and calendar.
  - CI pytest list plus the two added files: 1529 passed, 13 deselected (7 known failures, 6
    browser), after the removal took out two tests.
  - Browser (`test_library_page_browser.py`, `test_cpos_launch.py`): 29 passed. After the
    removal, `test_cpos_launch.py`'s 7 browser tests passed again.
  - Base logs: the same commands at `53a5632`, all exit 0.
- Not verified:
  - a live run of the journeys;
  - page render timing;
  - `TERM_LABELS` against the builder of `run.facilities` (not traced);
  - the form's download click (its `build()` output was used);
  - Windows paths.

## 2026-11-10 — All-modules live run tdg-all-001 and its corrections (branch `claude/all-modules-live-fixes`)

Owner: "Yes, run it", then "Merge now apply corrections on next PR". Ruling
`docs/rulings/2026-11-10-all-modules-live-test.md` (cap USD 20); run folder
`/private/tmp/claude-501/rbot-live7/runs/tdg-all-001` (outside the repo, unchanged here).

- Run (live, sol-medium, TDG 2024-09-30, all 19 analytical modules on #23's methods): 18 modules
  accepted, USD 10.32 spent against an estimate of USD 4–6. It stopped at CP-5, before any call:
  "1105073 input-token bound is over the 1050000 supported". No delivery was made.
- What the run shows: every module now states that CP-OS acceptance stands for lineage and records
  the helper scripts as not run. CP-1D, CP-2A and CP-2G are no longer blocked (Restricted); CP-1B
  ran. Still Blocked, each for a missing source only: CP-DR (no external research), CP-1C (no
  peers), CP-4 (no legal documents), CP-2H (no rating reports), CP-3D and CP-3 (no market data),
  CP-4C (follows CP-4).
- Defects found and fixed, each with a test written first and seen failing:
  1. The pre-send bound counted one byte per token. 817 retained CP-OS live calls measure at least
     4.11 request bytes per input token (median 4.44); `run_pathway.py` notes 2.51 at the lowest.
     The bound now counts two (`BYTES_PER_TOKEN_BOUND`); the hold is unchanged, since a Sol call
     holds its whole context.
  2. Every module was sent every earlier handoff, so first requests grew from 20 KB (CP-0) to
     1.01 MB (CP-5). CP-OS now sends only the registry's producers (required, plus optional ones
     the run selects; CP-5 every analyst before it), and the resume pins and the launcher's
     retained-prefix match use the same set. On tdg-all-001's handoffs the first requests total
     5.6 MB instead of 9.6 MB (estimate, not a live measurement).
  3. Six modules (CP-2H, CP-3D, CP-3C, CP-4C, CP-3, CP-5) had every source read refused by the
     700,000-byte reads cap. The cap is now 1,100,000 bytes (268,000 tokens at 4.11 bytes per
     token, under the 272,000-token long-context price).
- Registry: CP-4 += optional CP-1A (its runbook's upstream; CP-3C is left out because CP-3C already
  takes CP-4, which would make a cycle), CP-6 += optional CP-1B, CP-1C, CP-4 (its SKILL's upstream). The
  context form's edge table follows. The transport rules add one sentence saying which handoffs
  are supplied; this also changes every manifest, so a relaunch into an older run folder is
  refused ("choose a new --out") rather than re-sending its modules.
- Gates: CI pytest list plus `tests/test_handoff_loop.py` and `tests/test_context_form.py`, 1529
  passed, 7 deselected (known failures); quality gate 0 findings. Both exit 0. Two mutations (each resume site reverted to "every earlier module") fail the replay
  test.
- Not verified: no live run of the changes; CP-5 and CP-6 have still not completed on TDG; the
  cost saving and the reads CP-3 and CP-5 now get are estimates from retained requests; the
  relaunch refusal for old folders was checked by instruction text (old `CP-0.md` lacks the new
  sentence), not by a launch.

## 2026-11-10 — Names, not codes, on every library screen (branch `claude/names-not-codes`)

Owner: "Remove all cp-IDs and methodology step IDs from user facing screens. Replace with module
name or other." Display only (`apps/issuer-library/credit_os/web/`); routes, hrefs, download names,
`data.js` and the retained handoffs are unchanged. Record: `docs/design/2026-11-10-screens-pass.md`,
"Codes off the screen".

- Change: module codes read as module names everywhere, including Evidence & audit, the Evidence
  tab, the inspector, chips, the coverage strip, the reports' "Built from" table and each delivered
  report with its own inspector. `CP-x.md` reads "<name> handoff" and `CP-x_RUNBOOK.md` "<name>
  runbook". A method step id (`T4.10`, `T1D.1`, `T4.D1`, `T2G.*`, `T2E.3.r01`) becomes the step's
  title from the same output, or "a method step" / "method steps" when there is none. A column of
  bare step ids is dropped. Kept as written: register references (`C9`, `G1`, `GAP-001`), a bare
  `T<n>` ("T2 Biosystems", "Tier 2 (T2)"), and the quoted issuer source excerpt.
- Answer key (scratch crawler, not shipped): every in-app route plus the delivered reports. Text,
  option text, title, aria-label, alt and placeholder; one inspector per page. Before: 22,649
  module-code and 1,914 step-id hits over 349 routes of the four retained TDG runs. After
  (`54d7763`): `counted 0`. After merging main (`715f6f5`): `counted 0` over 186 routes and three
  runs. Main's methodology change now excludes `cpos-tdg-sol-medium-all-001` from the library ("not
  on the current methodology").
- Tests written first and seen failing (15 static, 3 browser). On the merged tree: `node --test`
  static + calendar 125 pass; `tests/test_library_page_browser.py` 21 passed; CI fast pytest list
  1471 passed, 7 deselected; quality gate 0 findings. All exit 0.
- Review: task review and fix round (mx-precise), whole-branch review (mx-architect), one fix
  wave and its re-review; implementation by mx-feature. Parked as latent, no retained instance:
  - step titles taken from any short second cell;
  - a step id cited beside another module's code takes this output's title;
  - the `;` joiner merging two untitled clauses;
  - `CP-0-A.md`-style names in the app.
- Not verified: Windows and Edge, phone widths, a screen reader; live Run activity data; a Forecast
  model with step ids; runbook names on a rendered page (string-level test only); any issuer other
  than TDG.

## 2026-11-10 — Context form adopted (branch `claude/optimistic-johnson-bmnwip`, after main `4ce88c2`)

Owner: "Approved". The proposal below replaced `docs/templates/context-form.html` and follows main's
ruling that CP-1C takes its peers from CP-DR by default (`pathway_modules`). Design note section 7
has the detail. Checks are offline (headless Chromium 1.63, the Python reader, the inbox's own
functions); no provider call and no analytical run.

- **Same output as before.** The original form (`483a555`) and the adopted one give byte-identical
  `context.json` for the three fixture contexts. `cp_dr_public` is the default in both.
- **The research module joins.** With the default peer source, Relative Value and Distressed list
  CP-DR in the launcher's order. "Not available" for the peers' files makes CP-1C a Gap, and choosing
  your own figures drops CP-DR.
- **End to end again.** Three downloads load in `load_context` and pass `inbox.drops.check`, and
  round-trip byte for byte. Every stage advanced by click and by tap at 390 px, and Start over is
  clean.
- **Inbox copies.** Copies written by `write_templates` as `context-form.html` lock the pathway,
  load the built library's fonts and log nothing.
- **Tests.**
  - `tests/test_library_page_browser.py` `FORM_PROBE`: the old probe was seen failing on the adopted
    form (`#s1-pathway` is gone). Rewritten, the file passes: 20 passed.
  - New `tests/test_context_form.py`: 22 passed. Each of nine one-line changes to the form's copied
    tables made its test fail, among them the Distressed order main had already changed.
  - `test_issuer_library_packaging.py`: 9 passed. The watcher's form tests: 2 passed.
  - `test_inbox_drops.py`: 55 passed, 3 failed. The three are permission tests that fail here
    because this sandbox runs as root, and they fail the same without this change.
  - Quality gate exit 0 (176 changed lines in scope, after one long line in the probe was split).
- **Research cutoff written (owner: "Your recommendation").**
  - New browser test `test_the_research_cutoff_follows_the_as_of_date_and_is_written`, seen
    failing on the form before the change: the cutoff came out blank.
  - Against the original form, the three fixture contexts differ only in `run.cutoff`. A blank one
    becomes the as-of date (`2026-10-31`); an explicit `2025-12-31` is kept.
  - The new downloads load and are accepted by the inbox. Each has
    `effective_cutoff(as_of, cutoff) == effective_cutoff(as_of, "")`, so the code reads them as it
    read a blank cutoff.
- **Not verified:** Firefox, Safari and real issuer folders. Whether CP-DR finds peers in a folder's
  filings: no live run. Whether the readiness forecast matches live outcomes.

## 2026-11-10 — Context form proposal (branch `claude/optimistic-johnson-bmnwip`)

Proposal only: `docs/templates/context-form-proposal.html` is new, and
`docs/design/2026-11-10-context-form-proposal.md` holds the module review and the design.
`context-form.html`, `context.py`, the inbox and the tests are unchanged. All checks below are
offline browser and reader checks, run in headless Chromium 1.63. No provider was called and no
analytical run was made with it.

- **Same output as the current form.** Each of three fixture contexts was loaded into both forms with
  `fill()` and written with `build()`. The two `context.json` files are byte-identical for each:
  `cases/context/primary-full.json`, `cases/context/research-minimal.json` and
  `cases/cpdr-context-cutoff/context.json`.
- **End to end through the page.**
  - Three files were made by clicking through the page and downloading: Earnings Update; Distressed
    with TDG-like dates, a duplicate S&P row and stale peers; and a new issue on Credit Snapshot.
  - Each loads in `context.load_context` and passes `inbox.drops.check` for its pathway.
  - Each round-trips through `fill()` and `build()` byte for byte.
  - The readiness panel showed what its own rules state, for example CP-2H Gap on two S&P rows and
    CP-1C Gap on one admitted peer. This checks the page against its rules, not against a run.
- **Inbox copies.** Copies made by the real `write_templates` lock the pathway (5 other cards
  disabled). A loaded file naming another pathway is replaced, with a note.
- **Newly caught.** `load_context` refuses a research question containing `|`, and an issuer name
  with U+2028. The current form writes both; the proposal stops both before download.
- **Defect found and fixed in the proposal.** A blur that adds a message moved the Next button
  between mousedown and mouseup, and the click was lost. The current form uses the same pattern; not
  verified there. After the fix, every stage advanced by click on desktop and by tap at iPhone 13
  size, with no horizontal scroll at 390 px.
- **Other checks.** Start over returns the page to a fresh build. No console errors in any run.
  Quality gate exit 0, with no Python changed.
- **Restyled in the Credit OS language after merging main `caeb622`.** All the checks above were
  repeated on the restyled page with the same results: byte-identical output, three downloads loading
  and accepted by the inbox, round-trips, every stage by click and by tap, and Start over.
  - An inbox copy (from `write_templates`, beside a copy of the library's web folder at
    `_engine/library`) loads Red Hat Display, Text and Mono from there, shows the rail links to the
    library, and logs nothing. The repository copy loads the repository's fonts and hides those links.
  - Compared by eye with the library built offline from the synthetic fixture run, shown in its empty
    state because that run is not on the current methodology.
  - Found and fixed while restyling: the yes/no inputs had no positioned parent, so their own hit
    area sat outside their segment.
- **Not verified:**
  - Firefox and Safari, and the folder picker in them.
  - Real issuer folders. The folder check guesses only from file names.
  - Whether the readiness forecast matches what the modules actually do in a live run. It ports
    `run_expectations.RULES` plus rules cited in the design note, but no run has been compared.

## 2026-11-10 — Module method gaps: what CP-OS sends against what each method needs (branch `claude/module-method-gaps`)

Owner: "review all the modules for any missing items from methodology files", then "Fix all … Keep a
copy of the methodology in the repo" and "Cp-1c is supposed to get that information from cp-dr by
default". Comparison: each module's method text as sent, against the retained all-modules run
(`runs/cpos-tdg-sol-medium-all-001`, 11 of its 15 skill modules Blocked) and the 2026-11-10 inbox run.
Offline only; no provider call.

- Acceptance and scripts (CP-1D, CP-3, CP-5 blocked for want of an acceptance receipt or script
  output): every module's instructions now carry what only CP-2G had: CP-OS's check is the
  acceptance, helper scripts are recorded as not run, nobody can be asked, and an entry value comes
  from the context, the handoffs, then the method's safe default.
- Companions: the methodology is copied read-only from `~/Documents/cp-os` at `b57a344` into
  `docs/reuse/selected-methods/` (63 files added, manifest hashes checked). Each skill is sent the
  files its SKILL calls mandatory or binding, and the Confidence Score section of `CANON_SHARED.md`.
  CP-4's instructions grow from 88 KB to 191 KB and CP-3's from 104 KB to 165 KB; the read budget
  already counts instructions, so reads shrink rather than the request growing.
- CP-1B runs Deploy V's skill; the structured-runtime step it had needs a `read_inputs` view CP-OS
  never gives (blocked on both runs).
- Order: CP-2A and CP-2E now run after CP-2 (CP-2A had blocked with "CP-2 is Not supplied"), CP-2A
  after CP-1B, CP-1C and CP-2 after CP-DR. Correction to the review note: CP-1D does not need CP-2;
  CP-2 is its consumer.
- CP-2A stress sizes: `cp2a.md` governs over the SKILL, so CP-2A states labelled, anchored
  scenarios, one as an EBITDA-decline and rate-increase pair CP-2G can apply.
- CP-DR as CP-1C's peer source: no pathway lists CP-DR, so the default (`cp_dr_public`) left CP-1C
  with no producer. CP-DR now joins a pathway that has CP-1C; it is asked for the peer pack (TDR.4
  to TDR.6) and CP-1C is told to read it. Run activity shows the added module once it starts.
- Tests written first and seen failing (10); CI test set plus every registry-dependent test: 1,471
  passed, 7 known failures deselected; quality gate exit 0. Offline prepare of all 20 modules on the
  TDG files gives the order CP-0, CP-1, CP-1A, CP-1B, CP-DR, CP-1C, CP-1D, CP-2, CP-4, CP-2A, CP-2E,
  CP-2D, CP-2G, CP-2H, CP-3D, CP-3C, CP-4C, CP-3, CP-5, CP-6.
- Consequence: a run made before this change that includes any skill module is no longer "on the
  current methodology", so the library stops listing it and names the changed files (checked:
  `tdg-forecast-005` is reported "Not shown … CP-2A: not on the current methodology").
- Not verified: any model behaviour. No live run was made, so whether the modules now proceed past
  their old blocks is unproven. CP-DR has no web or research tool in this transport: its peer pack
  can only use files in the run's folder, so CP-1C on public filings alone will still lack peers
  here. Gates for market data (CP-3, CP-3D), executed legal documents (CP-4), rating reports (CP-2H)
  and distress (CP-4C) are unchanged and untested with such files. The skills' scripts and three
  `.xlsx` placeholders were not copied. Output-side loss of analysis was checked for CP-2G only.

## 2026-11-10 — Library and report screens: reader value against production detail (branch `claude/forecast-publication-screens`)

Scope: the static library page only (`apps/issuer-library/credit_os/web/`), on
`claude/forecast-publication` (PR 19) merged with `claude/period-charts` (PR 20). One agent, no
sub-agents, no provider call. Record and dispositions: `docs/design/2026-11-10-screens-pass.md`.

- Change: production detail leaves the reading path (SHA-256 ids as link text, file names and line
  numbers in heads and bands, handoff word counts, "file hashes checked at build", a citation count
  on every Overview finding, five empty metric cards, a Completeness filter no run can match). It
  stays in a title, the evidence inspector or one "Built from" disclosure. Reports and the report
  selector name their run; the acceptance state sits beside Open report; "run" replaces "case";
  a missing figure reads `n.a.`; a sorted column shows its direction.
- Adversarial design review (breaker, newcomer, truster): BLOCK before the fixes (D1), CONCERNS
  after them; D1 to D8 fixed, D9 to D14 left with the owner (design doc table).
- Tests: twelve static tests changed or added and seen failing against the unchanged screens
  (`git archive` of HEAD). `node --test` static + calendar 116 pass, 0 fail; CI fast pytest list
  1441 passed, 7 deselected; `tests/test_library_page_browser.py` 20 passed; quality gate 0
  findings, exit 0.
- Looked at: headless Chrome at 1440 and 1280 over `file://`, and the built-in browser over a
  local server, on a library rebuilt from the four retained TDG runs: library, Overview, module
  matrix, CP-1 charts, reports list, report reader. No console error from the page (the one 404
  is the optional `activity.js`, absent without a live run).
- Not verified: phone and tablet widths; Windows and Edge; a library with many issuers or with an
  accepted report (fixture only); a live run's activity view; the delivered report's own layout
  inside the frame, which belongs to the delivery renderer; no independent review of this pass.

## 2026-11-10 — Forecast tab: open items of run tdg-forecast-005 and CP-2G's own cases (branch `claude/forecast-tab-register`)

Owner: investigate the open items; leave any that come from the sources lacking the needed files, but
check the code would produce the output if they were there. All checks offline on retained data.

- In-loop forecast check (not triggered live): replaying run 004's real CP-2G answer through
  `_forecast_issues` gives the repair request naming `ebitda_margin`'s pattern failure (9 problems),
  and replaying run 005's answer gives none. Verified on real model output; no provider call.
- No downside case (sources): CP-2A's method forbids unsupported stress magnitudes, and the filings
  give no rate path or stated stress case, so CP-2G wrote `downside_shock: null` and said why. With
  a shock of 0.20/0.10 set in run 005's real CP-2G block, `model_files` writes REFERENCE and
  DOWNSIDE, and the library grid shows a Downside group: Adj EBITDA 3,364 / 3,710 / 4,092, each
  the base figure × 0.8 by hand; FY2025 interest 1,156.92 × 1.1 = 1,272.612.
- Upside footnote (code): the cash flow notes said "The upside case stays in the calculation record".
  CP-OS models never had one; the predecessor's models (`final-workflow` deliverables) do carry an
  UPSIDE case, which the library hid. Sentence removed; the grid now shows UPSIDE (below).
- No assumption register (code): `register_of` matched only headings containing "assumption
  register", but the method fixes the id T2H.3, not the wording; runs 001–005 wrote "Assumption
  register", "assumption lock", "assumption disposition" and "Assumptions and definition lock". It
  now also matches a heading starting with T2H.3. Run 005's rebuilt library shows the register
  (B1–B7, F1–F4, U1, D1–D2, L1–L2).
- Tests written first and seen failing (4 of 5); library tests 68 passed incl. browser; gate exit 0.
- CP-2G's own cases computed (owner, 2026-11-10, "Yes, compute them"): the inputs block takes
  optional `upside_drivers` and `downside_drivers`, each only the drivers that differ from base
  (the rest inherited). Python writes UPSIDE and DOWNSIDE_DRIVERS; CP-2A's shock stays DOWNSIDE on
  base drivers (the predecessor's meaning), never compounded with CP-2G's downside. The keys are
  written only when stated: run 005's delivery, made before this, still re-verifies byte for byte
  (it failed with `delivery_changed: forecast_exact.json` in the first version, caught in review).
  Grid groups: Base, Upside, Downside (CP-2G drivers), Downside stress (shock on base drivers).
- Answer key written by hand, not by production code: upside year 1 (growth 0.10, margin 0.35)
  revenue 1,100, EBITDA 385, CFO 239, FCF 195, closing cash 225; downside year 1 (no growth, no
  dividends) 1,000 / 300 / 164 / 124 / 174; all three years of every case against the test's
  fraction model. Run 005 replayed offline with its register's U1 (growth 0.2058) and D1–D2 (growth
  0, margin 0.4781): upside revenue 9,574.052 = 7,940 × 1.2058; downside EBITDA 3,796.114 = 7,940 ×
  0.4781. Tests first and seen failing (9); 237 passed incl. browser; node 105; gate exit 0.
- Not verified: a live CP-2G run writing the case blocks (instructions changed, no paid run); the
  predecessor's UPSIDE shown in this library (no such workspace built here).

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

