# Verification record

Keep one running record here. A pass applies only to the stated scope. Earlier verification of the
engine is in [EricMG13/final-workflow](https://github.com/EricMG13/final-workflow)'s
`VERIFICATION.md`, which also keeps the retained runs this copy leaves out.

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
