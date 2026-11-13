# Frontend changes needed after the methodology changes

Running record, started 2026-11-13. One row per screen change that a methodology or CP-OS change
makes necessary or worth deciding. Screens: the run-start page and the issuer library's Overview,
Changes, Modules, Forecast and Evidence pages.

Status: **Done** (in a PR), **Needed** (the screen is wrong or incomplete without it),
**Decide** (owner choice), **Check** (not yet looked at on a real page).
"Source" says where the fact comes from; a session's report is not a check of the page.

## From the defect fixes (PR 103)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 1 | Events now carry a Published date, not "—" | Changes, any events list | Confirm the date shows and sorts; every dated row was "—" in both TDG runs | Check | T1 |
| 2 | A repair that dropped sourced values is recorded in the write's `review.json` | Evidence | Show the dropped values per module; today they are only a `Review:` line in the launcher output | Decide | T2, branch review |
| 3 | A module written after Copilot summarised its context is flagged | Modules, Evidence | Mark the module; today the flag is only in the launcher output and events | Needed | T3 |
| 4 | Summary charges are folded into a call's cost | Library cost table | Mark which calls include a summary charge | Decide | T3 review |
| 5 | Late or unreported summary charges are disclosed outside `Charged:` | Run-start page spend, library cost | Show the "Charged excludes" lines; the run-start page shows neither today | Needed | T3 money review |
| 6 | First prompt near the context limit prints a warning | Run-start progress | Show the warning during the run; today it is in the log only | Decide | T3 |

## From the register and routing cut (T4, in progress)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 7 | Ten modules stop writing registers nobody reads | Modules | The cut sections disappear; confirm no empty headings or dead links remain | Check | T4 session report |
| 8 | Handoffs are shorter | Evidence | "Original Markdown" links and `handoffs.zip` carry the shorter handoffs; data on the page is identical | Check | T4 session report |
| 9 | CP-OS refuses a handoff missing an in-scope register | Run-start progress | A refusal reason the analyst can read, if refusals are shown there | Check | T4 |
| 9a | The cut tells Rates, FX & hedging not to write any ESG table (T2G.1 to T2G.8) | Modules (ESG part), run-start catalogue | PR 100's ESG part would be empty on new runs and the catalogue sentence false; keep the ESG tables the page draws, or remove the part | Decide | Review of PRs 107 and 108 |
| 9b | Evidence validation no longer writes its issue log or audit tables | Modules (Evidence validation), Evidence | Confirm its findings still reach the reader through its passages and Gaps | Check | Review of PRs 107 and 108 |

## From CP-DR online lookup (T5, in progress)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 10 | Web lookup is on by default for public cases | Run-start form and summary | A control to force it on or off, and the summary the analyst approves states which | Needed | T5 brief |
| 11 | Fetched pages are kept under `<run>/web/` | Evidence | List each web source: URL, fetch time, the page's own date, hash; open the retained copy, not the live page | Needed | T5 brief |
| 12 | Pages dated after the as-of date are allowed only as later events | Modules (CP-DR, CP-1C, CP-2), Evidence | A visible "later event" label; undated pages labelled as undated | Needed | Owner decision |
| 13 | Fetched PDFs are refused in this version | Overview or Modules limitations | State the limitation where CP-DR could not read a PDF source | Needed | T5 session report |
| 14 | SEC requests need the owner's User-Agent variable | Run-start page | A clear message when it is missing and SEC lookups are refused | Needed | Controller ruling |

## From CP-1 on the full method (T6, in progress)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 15 | Leverage and net debt move to carrying value (TDG FY2024: 6.01x becomes 5.96x) | Overview, Forecast, charts | Axis and table labels must say carrying value; check chart routes still find CP-1's tables | Needed | CP-1 fact-find |
| 16 | Earlier runs used principal | Changes | Show the basis change as a method change, not a change in the issuer | Needed | CP-1 fact-find |
| 17 | The maturity ladder carries a reconciliation from principal to carrying total | Forecast or Modules (CP-1) | Show the reconciliation with the ladder | Decide | T6 ruling |
| 18 | Reported EBITDA is primary; adjusted shown beside it | Overview, charts | Label which EBITDA each ratio uses | Needed | T6 ruling |
| 19 | CP-1 tables get a fixed row vocabulary | Financials grid, company profile | Row counts varied 83 against 16 between two runs; confirm the grid is stable and complete with the new tables | Check | Comparison report |
| 20 | A CP-1 written before the code check may fail it | Run-start (resume) | Say why an older run cannot be resumed | Decide | T6 ruling |

## From `run_script` (T7, not started)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 21 | Module figures come from scripts, not model arithmetic | Evidence (calculations) | Show which figures a script produced and its inputs | Decide | Plan |

## From ESG naming (PR 100, PR 105)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 22 | ESG tables were written but unnamed | Modules (Rates, FX & hedging), run-start catalogue | Named ESG part; register tables link to Evidence | Done, PR 100 | Review of PR 100 |
| 23 | Label reads "Environmental, social and sustainability (ESG)" | Same | Choose the wording; "Environmental, social and transition" is the alternative | Decide | Review of PR 100 |
| 24 | A long state squeezed a checklist label to zero width | Library status list | Fixed; at 561 to 1024 px a long state can still be wider than its label | Done, PR 105 | Review of PR 105 |

## From the tiers and depth proposals (not decided, nothing built)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 25 | Deep, Full and Lite tiers | Run-start form | Tier choice with what each runs, cost and time estimates | Decide | Tiers proposal |
| 26 | Full's report lacks the downside stress and break-point sections that Lite shows | Overview | Add them to Full; it runs the same module | Needed | Tiers proposal |
| 27 | Modules skipped for thin sources | Run-start summary, Overview, Modules, Changes | State each skip and why; Changes must not read a skip as a change of view | Decide | Tiers proposal |
| 28 | Deep runs 21 modules | Overview | About 24 front-page sections, not all 56 | Decide | Tiers proposal |
| 29 | Depth setting Brief, Standard, Extended | Run-start form and summary, Overview, Modules | Setting, and a statement of what a Brief run left out | Decide | Depth proposal, PR 104 |

## Existing gaps the runs showed (not caused by these changes)

| # | Screen | Gap | Status | Source |
| --- | --- | --- | --- | --- |
| 30 | Overview | The front-page call reads "Assessment pending" although CP-3 and CP-6 give a recommendation | Needed | Comparison report |
| 31 | Overview, run lists | The report does not say which effort produced it; both runs carry the same run id | Needed | Comparison report |

## Not verified

- No row marked Check or Needed has been looked at on a rendered page for this record.
- Rows for T4, T5 and T6 come from their briefs and session reports; their PRs are not open yet and
  the rows may change when they are.
- Any presentation change needs the reader check and fidelity check `AGENTS.md` requires.
