# Sweep report — end-to-end wiring, 2026-11-10

Contract: `CONTRACT.md` beside this file. Base `53a5632` (main after PR 27); range `c721a0f..53a5632`
(PRs 19–27). Branch `claude/sweep-wiring`. No provider call, no spend.

## Journeys proved (offline, canned provider answers)

| Journey | How | Result at base |
|---|---|---|
| Context form → reader → launcher | Live TDG context loaded into the form (`fill`), rebuilt (`build`), fed to the launcher without `--live` | Round-trips except the intended changes: a blank cutoff becomes the as-of date, and the classification is asked for. The launcher reads it and prepares the plan. |
| Launcher → CP-OS → delivery → library → screens, every pathway | Scratch probe, now `test_each_pathways_run_reaches_the_library_screens` (browser) | 6 of 6 pathways: run listed by the real library build. Overview, Reports list, the report, Evidence, Forecast and `report.html` render with no console message and no `undefined`/`NaN`/`null`. Forecast model present exactly when CP-2G runs. |
| Inbox drop → watcher → real launcher → filing → library | Scratch probe, now `test_a_drop_is_run_by_the_real_launcher_filed_and_listed` | Finished; filed report equals the delivered one byte for byte; the real library lists the run. |

Before this sweep, the watcher tests used stand-in launchers and a stubbed library. The launcher tests stubbed the library too, except one CP-2G route. A mutation that divides the watcher's `--cap` by 100 passes the stand-in test and fails the new one.

## Register

| Row | Kind | Disposition |
|---|---|---|
| W1 | Screens copy run statuses, classification and rating scope from Python with no test tying them | fixed: `test_the_library_screens_value_lists_are_the_codes` (fails when a status is dropped from `views.js`) |
| W3 | No committed journey across launcher → library → screens per pathway, or inbox → real launcher → library | fixed: the two journey tests above; `test_context_form.py` and `test_handoff_loop.py` added to the per-PR CI list |
| W2 | `prepare(retained=)` and its resume helpers (`Accepted`, `_Now`, `_mismatch`, `_retained_prefix`) have no production caller | removed on the owner's ruling ("Remove it"): 127 lines out of `cpos_launch.py`. Prepared run folders are byte-identical before and after for all six pathways. CP-OS's own replay of pinned answers stays, and its test now pins the answers in the manifest directly. |
| F1 | Form output vs reader | not-a-defect |
| W1b | `TERM_LABELS` in `views.js` (deal-term and quote figures) | open: values match `DealTerm`/`Quote` today; the builder of `run.facilities` was not traced, so no tie was written |

No product defect was reproduced. Complexity: no function in the range's code is over the gate's limits beyond the existing, already-marked ones (`run_handoffs`, `registry.__post_init__`).

## Performance (median of 5 after 1 warm-up; noise = max − min)

| Path | Baseline | Verdict |
|---|---|---|
| `prepare()`, all 20 modules | 23.8 ms, noise 18.0 ms | no candidate: negligible next to a run |
| Library rebuild, 10 run folders (3 listed) | 372.9 ms, noise 37.0 ms; profile spread (JSON decode 0.12 s, chips 0.14 s) | no candidate above the floor |
| Library page render | — | unmeasured: the app pane shows file pages as static snapshots |
| Live spend per run | PR 27 (at base): first requests 9.6 → 5.6 MB on tdg-all-001 handoffs | fixed-at-base; estimate, not measured live |

## Checks

Baseline and final logs: `.superpowers/sdd/sweep-wiring/evidence/` (ignored). Final results are in
`VERIFICATION.md`.

Not verified: a live run on these journeys; page render timing; `TERM_LABELS` against its builder;
Windows paths for the inbox journey; the form's download click itself (its `build()` output was
used).
