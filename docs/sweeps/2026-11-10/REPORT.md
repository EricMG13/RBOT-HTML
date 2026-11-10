# Sweep report — refactoring and optimisation, 2026-11-10

Base `origin/main` `c145b16`; final tree `dc90974` on `claude/refactor-optimisation-sweep-01c49e`
(7 commits, 446 changed lines before this report). Contract: `CONTRACT.md` beside this file.
Scope of evidence: synthetic tests, scratch harnesses and a scratch copy of four retained runs on
macOS. No provider was called, nothing ran on Windows, and no file under `runs/` was written.

## Landed (6 items, the contract's cap)

| # | Kind | Commit | What was wrong or costly | Evidence |
|---|---|---|---|---|
| D1 | defect, Medium | `41ceb1e` | `report_fields` looked for a level-1 "Front matter" section; the parser emits level 2, so `state.declared` was `None` for every real handoff. | Failing test first. Rebuild of the retained runs: 13 outputs now carry their status (Blocked 11, Requires More Work 2); nothing else in the built library changed. |
| F1 | defect, Medium (spend) | `d0ed255`, `f28523a` | The watcher launched with any `--cap` (500 accepted); the standing ruling allows USD 20 per run. Start-up now refuses a cap above 20, and a NaN cap. | Failing test first; 16 boundary cases by the reviewer (20, 20.00, 2E+1 start; 20.01, Infinity, NaN refused before the lock). |
| D2 | defect, Low | `fec7d32` | A source-text page number that overflows (`1e400`) raised `OverflowError` out of `read_pages` and would stop the library build. It is now a stated reason. | Failing tests first; two probes. |
| D3 | defect, Low | `fec7d32` | `is_file_name` accepted `C:x.jsonl`, which leaves `source-text/` on Windows. Names containing `:` are refused. | Failing test first; shown with `PureWindowsPath` only. |
| S1 | performance | `84987fb`, `d0ed255`, `f28523a`, `dc90974` | Every watcher poll re-read the event log and budget journal of every shown ended run. A settled run is now read once. | Below. |
| O1 | performance | `1aa9714`, `dc90974` | One library rebuild read each run's `view.json` 5 times, parsed it 3 times and hashed every delivery file 3 times. The build now carries the delivery it verified. | Below. |

### Measurements

Median of 5 runs after 1 warm-up; noise is max − min of the 5. Harnesses are in
`.superpowers/sdd/sweep-2026-11-10/evidence/` (not committed).

| Item | Metric | Before | After | Noise | Verdict against the contract (≥ 20% and ≥ 2 × noise) |
|---|---|---|---|---|---|
| S1 | watcher step, 200 ended runs × 40 calls | 801.6 ms; 16,200 file opens, 200 event reads, 200 journal reads per step | 2.4 ms; 0 opens, 0 reads | 107.6 ms / 0.3 ms | accepted (99.7%) |
| S1 | watcher step, 50 ended runs × 40 calls | 172.3 ms; 4,050 opens | 1.3 ms; 0 | 9.9 ms / 0.3 ms | accepted |
| O1 | library rebuild, 4 retained runs, 3 interleaved rounds | 0.810, 0.777, 0.766 s | 0.584, 0.576, 0.548 s | 0.036–0.098 s | accepted: 0.201 s (26%) on the middle round; the worst noise sample (0.098 s) makes 2 × noise 0.196 s, so the margin is thin |
| O1 | bytes read per rebuild | 185,378,190 | 65,669,876 (45,285,987 distinct) | exact | — |
| O1 | `read_inside` calls / view parses per run (library side) | 283 / 2 | 177 / 1 | exact | — |

Protected output: the built `library/` has the same sha256 (`e79349ea…a14772`, build time masked)
before and after O1, and against `origin/main` differs only in the 13 declared statuses of D1.
Written `activity.js` is byte-identical with and without the store over 214 records (reviewer's
probe). Guards left in the suite: a work-count test for each (zero reads on the second snapshot;
`view.json` read at most twice and one delivery check per build).

S1 reuses an entry only for a finished, failed, capped or rejected record that is unchanged, has
its run folder, and is not "started with no saved process ID"; interrupted, running and queued
runs, and any fail-open read, are read every poll. O1 added +8% peak memory on four runs
(112.7 → 121.7 MB, reviewer's measure).

### Reviews

Per task: library and chips commits approved (17 parity probes against the parent commit, same
output and messages for 13 tamper cases). Inbox commits: one Medium (a "failed" run with a live
launcher had its empty entry kept), fixed test-first in `f28523a`, re-review passed. Whole branch
(confidence review, rewrite tournament on the changed functions, over-engineering pass): approve
with notes; every tournament result was "leave as is"; one Low and one Info fixed in `dc90974`.

Ledger: T1 `agent=mx-feature fix-rounds=0 gates-first-pass=y` · T2 `mx-feature 0 y` · T3
`mx-feature 0 y` · T4 `mx-feature 1 y` · T5 `mx-feature 0 y` · final batch `mx-feature 0 y`.

## Found and left (probes fail at base; copies in the coordinator's notes folder, `B-sweep-open-probes/`)

| # | Sev | Where | Finding | Disposition |
|---|---|---|---|---|
| F1b | Medium | `watcher.py` `--ruling`, `--config` | `--config sol-high` with another ruling passes start-up and launches. | decision: should the watcher accept any ruling but the standing one? |
| F2 | Low | `runs.py:211-223` | `OSError` closing the log handle after `Popen` records "failed" while the child runs untracked. | open (cap reached); S1 no longer freezes its display |
| F3 | Low | `watcher.py:168-173` | A rebuild error outside `OSError`/`ValueError`/`ImportError` stops the watcher. Root cause D2 is fixed. | decision: catch-all with a logged fail-open? |
| F4 | Low | `watcher.py:322-331` | An unreadable drop is moved to `failed` while other files still copy. | open |
| F5 | Low | `watcher.py:459-467` | The daily-limit note is hidden while every slot is busy. | open |
| F6 | Low | `watcher.py:67-68, 453` | On the autumn clock-change day a start in the first local hour is not counted. | open |
| F7 | Low | `drops.py:233-252, 93-96` | A file named like a pathway folder is never reported and stops the next start. | open |
| D4 | Low | `tools/quality_gate.py:64-66` | Changed files with a space or non-ASCII name are dropped silently (none tracked today). Predates PRs 10 and 11. | owner |
| B1 | Low | `activity.py` `_entry` | A settled run first read while only its event log or only its journal is invisible is kept with waiting modules or spend 0. | open; indistinguishable from a run that wrote neither |
| B2 | Info | `credit_os_chips.py:390` | A source named with `:` (legal on macOS/Linux) now gets a gap chip. Safe direction of D3. | accepted |
| B3 | Info | `store.py:601` | A handoff with no YAML whose first line is `## Front matter` reads as declaring a status. | open; parser gives both the same shape |

Structure measured and deferred: 349 lines of identical function bodies in scope, 160 of them the
`cpXX_module` builder repeated in 11 owner modules (no owner tests in this repository protect
them); three temp-file-then-replace writers in `inbox/` (42 lines); `Pages` rebuilt per output (34
source-text reads for 6 files; chips pass 0.11 s, under the threshold); `drops.check` twice per
run; `issuer_folder` twice per filing; `parse_locators` has no production caller. No function in
the update's files exceeds the gate's complexity limits. Fast tests take 65 s; the slowest are
watcher tests with real waits (3.7 s).

For the web session (not edited here): the module head's declared badge now appears on real data.

## Gates on `dc90974`, all exit 0

- `uv run python tools/quality_gate.py`: 0 findings, 19 changed files, 1,120 lines in scope.
- The `checks.yml` pytest command plus `tests/test_credit_os_chips.py tests/test_inbox_*.py`:
  1,392 passed, 7 deselected (base: 1,372).
- `node --test` on `static.test.cjs` and `calendar.test.cjs`: 97 pass.

One new suppression: `# noqa: PLR0913` on `activity.snapshot` (six arguments), as `runs.py` and
`filing.py` already do.

Not verified: any Windows behaviour (D3, the watcher, a dropped share); a live watcher over a real
run or any provider path; the browser tests and how the page renders the newly declared statuses;
the full and slow suites; memory and timing beyond four retained runs; repeated rebuilds inside a
long-lived watcher beyond three in one process; GitNexus impact (no index in this worktree; callers
traced with grep); mutation testing on the spend-cap change.
