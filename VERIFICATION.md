# Verification record

Keep one running record here. A pass applies only to the stated scope. Earlier verification of the
engine is in [EricMG13/final-workflow](https://github.com/EricMG13/final-workflow)'s
`VERIFICATION.md`, which also keeps the retained runs this copy leaves out.

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
- Not verified: a real print dialog and printers; Safari and Firefox; a screen reader; Windows
  forced colours (rule written, not rendered); touch input; the inbox-built library with Run
  activity; runs without charts or with a committee band; whether a keyboard-only reader finds
  the full basis (it is in the selected-run panel, not on focus).

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
