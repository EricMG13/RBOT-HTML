# Verification archive

Entries moved verbatim from VERIFICATION.md when older than two days.

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
