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

## From the register and routing cut (T4, PRs 107 and 108)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 7 | Ten modules stop writing registers nobody reads | Modules | The cut sections disappear; confirm no empty headings or dead links remain | Check | T4 session report |
| 8 | Handoffs are shorter | Evidence | "Original Markdown" links and `handoffs.zip` carry the shorter handoffs; data on the page is identical | Check | T4 session report |
| 9 | CP-OS refuses a handoff missing an in-scope register | Run-start progress | A refusal reason the analyst can read, if refusals are shown there | Check | T4 |
| 9a | The cut tells Rates, FX & hedging not to write any ESG table (T2G.1 to T2G.8) | Modules (ESG part), run-start catalogue | PR 100's ESG part would be empty on new runs and the catalogue sentence false; owner, 2026-11-13: "Yes, keep ESG tables"; T4 is removing T2G.1 to T2G.8 from its cut list | Done in PR 108 (`7adb21e`); T5B.3 and T6A.7 are kept too | Re-read of PR 108 |
| 9b | Evidence validation no longer writes its issue log or audit tables | Modules (Evidence validation), Evidence | Confirm its findings still reach the reader through its passages and Gaps | Check | Review of PRs 107 and 108 |

## From CP-DR online lookup (T5, PR 110)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 10 | Web lookup is on by default for public cases | Run-start form and summary | A control to force it on or off, and the summary the analyst approves states which | Needed | T5 brief |
| 11 | Fetched pages are kept under `<run>/web/` | Evidence | List each web source: URL, fetch time, the page's own date, hash; open the retained copy, not the live page | Needed | T5 brief |
| 12 | Pages dated after the as-of date are allowed only as later events | Modules (CP-DR, CP-1C, CP-2), Evidence | A visible "later event" label; undated pages labelled as undated | Needed | Owner decision |
| 13 | Fetched PDFs are refused in this version | Overview or Modules limitations | State the limitation where CP-DR could not read a PDF source | Needed | T5 session report |
| 14 | SEC requests need the owner's User-Agent variable | Run-start page | A clear message when it is missing and SEC lookups are refused | Needed | Controller ruling |
| 14a | Every SEC filing and SEC data page is "undated" to the code | Modules (CP-DR), Evidence | Each carries "Undated" and a Gaps item; decide whether the reader sees the filing date from the filing list instead | Decide | Review of PR 110 |
| 14b | Lookup is on by default for a public case | Run-start summary | The summary the analyst approves does not show the Lookup line | Needed | PR 110 ruling, open point 4 |
| 14c | Retained pages are kept in `<run>/live/web/`, not `<run>/web/` | Evidence | Read the web sources from that folder | Needed | PR 110 ruling, open point 12 |

## From CP-1 on the full method (T6, PR 111)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 15 | Leverage moves to carrying value over reported EBITDA (TDG FY2024: 6.01x total, 4.51x net, 3.60x cover become 6.53x, 4.88x, 3.29x) | Overview, Forecast, charts | Axis and table labels must say carrying value; check chart routes still find CP-1's tables | Needed | CP-1 fact-find |
| 16 | Earlier runs used principal | Changes | Show the basis change as a method change, not a change in the issuer | Needed | CP-1 fact-find |
| 17 | The maturity ladder carries a reconciliation from principal to carrying total | Forecast or Modules (CP-1) | Show the reconciliation with the ladder | Decide | T6 ruling |
| 18 | Reported EBITDA is primary; adjusted shown beside it | Overview, charts | Label which EBITDA each ratio uses | Needed | T6 ruling |
| 19 | CP-1 tables get a fixed row vocabulary | Financials grid, company profile | Row counts varied 83 against 16 between two runs; confirm the grid is stable and complete with the new tables | Check | Comparison report |
| 20 | A CP-1 written before the code check may fail it | Run-start (resume) | Say why an older run cannot be resumed | Decide | T6 ruling |
| 20a | A non-USD issuer cannot state leverage (the US$m tables are gaps and the tie refuses a stated ratio) | Overview, Forecast, charts | Leverage is empty for GBP and EUR issuers, VMO2 included, until the owner decides | Needed (owner decision) | PR 111 ruling; review of PR 111 |
| 20b | The leverage chart ties to reported EBITDA only | Overview, charts | An issuer that states only adjusted EBITDA shows no headline leverage; adjusted leverage is in the register only | Needed (owner decision) | Review of PR 111 |
| 20c | CP-1 now writes a Period table, a debt reconciliation and `### Confidence inputs` | Modules (CP-1), Changes | Confirm each is drawn once and the Changes page reads periods by date | Check | PR 111 ruling |

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

## From Signal (PRs 101, 102, 106, 109)

| # | Cause | Screen | Change | Status | Source |
| --- | --- | --- | --- | --- | --- |
| 32 | The run-start service can show a Signal link | Run-start rail | Shown only when started with `--signal-url`; a change to the run-start page, so it needs the reader check | Check | Review of PR 109 |

## Not verified

- No row marked Check or Needed has been looked at on a rendered page for this record.
- Rows for T4, T5 and T6 come from their briefs, session reports, rulings and my reading of PRs
  107, 108, 110 and 111; none has had a paid run.
- Any presentation change needs the reader check and fidelity check `AGENTS.md` requires.
