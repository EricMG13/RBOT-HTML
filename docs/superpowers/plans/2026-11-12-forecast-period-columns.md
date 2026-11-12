# Forecast Page Main Period Columns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The issuer library Forecast page shows the owner's main period set, in this order: quarters, YTD and PYTD, fiscal years, LTM and prior LTM, PF, then Base case and Downside case; a column that cannot be built shows as unavailable with its reason.

**Architecture:** A new pure module reads the period columns CP-1 already prints, finds the forecast's base lines in CP-1's tables, and builds the historical columns with exact Decimal arithmetic. `cpos_forecast.model_files` publishes them as a `history` record in `calculation.json`. The library store lays that record out before the forecast columns and keeps two forecast cases in the main grid; the page places what the store sends. CP-1's instructions are not changed.

**Tech Stack:** Python, `decimal` (the existing `cp2g._EXACT` context), pytest; the store stays standard-library only; one small change to `views.js`. No new dependency.

**Spec:** This document's Design section. Owner's requirement, verbatim: "main period should be: Quarterlies, YTD & PYTD, FYs, LTM & Prior LTM, PF, Base & downside case". Period rules follow `src/deploy_vii/model/periods.py` (anchor, YTD and PYTD of the same fiscal quarter, LTM = FY + YTD - PYTD) and `src/deploy_vii/model/statements.py::pro_forma_column`; the code is not imported (it needs typed CP-1 registers the active path does not have).

## Design

### What the page shows today (found while planning)

On the active CP-OS path the Forecast grid has **no historical column at all**. `cpos_forecast.model_files` writes `calculation.json` with `"annual_periods": []` and `quarter.md` as `No quarter handoff in this run.`; `tests/test_cpos_launch.py::test_the_library_lists_the_published_forecast_as_a_model` pins the columns as `FY2025E, FY2026E, FY2027E` per case. The quarter and fiscal-year columns in `store.py` (`quarter_columns`, `fiscal_columns`) are reached only by the older TDG delivery (`model_handoff_delivery.py`), whose tables use ISO date-range and `FYnnnn` headers and TDG's exact row labels (`CASHFLOW_LABELS`). So this plan must first give the active path a history, then order it.

### What CP-1 prints (six retained handoffs, read only)

`~/Documents/FinalWorkflow-Live/runs/web-*/CP-1.md`. None of the six has a forecast inputs block (they predate it), so they prove header forms only.

| Run | Period headers of the statement tables |
| --- | --- |
| `web-0dca13e7` (NATL) | `Q3 2025`, `Q3 2024 revised`, `Q3 2024 recast`, `9M 2025`, `9M 2024 revised`, `FY2024 revised`, `FY2024, annual definition` |
| `web-2cb85cb4` (LTH) | `FY2023`, `FY2024`, `H1 2024`, `H1 2025`, `Q2 2024`, `Q2 2025` |
| `web-79a17365` | `Q2 2025`, `Q2 2024`, `H1 2025`, `H1 2024`, `FY2024` |
| `web-b7425f3d` | `Q2 2025`, `Q2 2024`, `H1 2025`, `H1 2024` (no fiscal year); also `Q2 2025 net sales` |
| `web-d95ed5de` (IHRT) | `FY2022`, `FY2023`, `9M2023`, `9M2024`, `Q3 2023`, `Q3 2024` |
| `web-f7d2f1ab` (TDG) | `FY2023`, `FY2024`, `Q1 FY2024`, `Q1 FY2025`, `Q1 FY2024: thirteen weeks ended 2023-12-30`, `Rolling reported periods to 2024-12-28` |

Every run prints the latest quarter, the year to date and their prior-year comparatives. No run prints the year to date two years back. LTM appears only as a calculation or in prose. Pro forma is never a period column. Balance-sheet tables are often headed by dates, not periods. Four runs print period dates in a table, in four different forms.

### Period identification: header forms, and a period table for the dates

**Headers.** A header is a period when, after Markdown emphasis is stripped, it fully matches:

`(FY ?<year> | (Q1|Q2|Q3|Q4|H1|6M|9M) ?(FY ?)?<year>)` followed by nothing, by ` revised`, ` recast` or ` restated`, or by `:` or `,` and any text.

`<year>` is four digits and is read as the fiscal year. `6M` is `H1`. Anything else (`Q2 2025 net sales`, `Rolling reported periods to 2024-12-28`, `September 30, 2025`) is not a period and is never guessed. Headers of the tables that hold a located line and contain a four-digit year but are not read are listed in a limit, so a missed form is visible.

**Dates: the period table (owner, 2026-11-12: "approved").** CP-1 is asked to print one table whose header is `| Period | Start | End |` (more columns may follow), one row per period column header it uses: `Period` the header text exactly, `Start` and `End` the first and last day as `YYYY-MM-DD`. A row is read when its `Period` is a period by the header rule and both dates are valid with start not after end; two rows for one period with different dates leave that period undated and are named in a limit. This is the only CP-1 instruction change.

With the dates of the fiscal year, the year to date and the prior year to date, the LTM is checked as the typed engine checks it: the fiscal year ends the day before the year to date starts, the prior year to date starts on the fiscal year's first day, and `days(FY) + days(YTD) - days(PYTD)` is from 364 to 371 (a 52- or 53-week year passes). A failed check leaves the LTM's flows and the ratios on them unavailable with the reason; balances are kept. At a fiscal-year anchor the fiscal year's own days are checked. Prior LTM is checked the same way when it can be built.

A CP-1 without the table, or without the dates of one of the three periods (every handoff written before this change): the LTM is still built from the labels and a limit says it was not date-checked. It is never refused for missing dates (ruling 5).

### Which lines have history

The grid's forecast rows are the lines `cp2g.Year` computes. History is shown for the same lines, from the forecast's ten base operands (`forecast_exact.json` `base`). CP-1's tables use the issuer's own row labels, so a line is found by its base amount, not by a label list:

1. For an operand with an amount, the candidate rows are every row of every CP-1 table (`cpos_forecast._tables`) with a cell, under a header that is a period, that is a number (`_signed`) and agrees with the amount under the one sign rule (`_agrees`).
2. No candidate: the line has no history (`the base amount is not a table cell of CP-1`; when it is printed only under a header that is not a period, `CP-1 prints the base amount only under a column header that is not a period ({header})`).
3. Candidates with different labels in one table, or with different labels and a different figure in any period they share, or with different labels and no one period in which all of them print the base amount: the line is not identified, and has no history.
4. Otherwise the line's figure for a period is the one distinct number its candidate rows print under headers of that period; none is `CP-1 does not print this line for {period}`; several is `CP-1 prints different figures for this line in {period}`. A non-numeric cell (`Not supplied: ...`) is not a figure.
5. The figure takes the operand's convention: interest, taxes and capex as positive magnitudes, working capital with its sign reversed.

The same rule serves a CP-2G block and CP-1's layer-1 block (its `row` and `period` are already checked by `parse`).

### Columns and arithmetic

The anchor is the latest recognised period of a table holding a located line, by (fiscal year, quarters to date): `Q1` 1, `H1` 2, `9M` 3, `FY` 4. Write the anchor as year N, quarter k.

| Group | Columns | Built from |
| --- | --- | --- |
| Quarter | every printed quarter, by year then quarter | the cell |
| Year to date | `YTD`, `PYTD` | the `Q1`, `H1` or `9M` period of quarter k in year N, and in year N-1 |
| Fiscal year | every printed fiscal year, ascending | the cell |
| Last twelve months | `LTM`, `Prior LTM` | flows: `FY(N-1) + YTD - PYTD`; prior: `FY(N-2) + PYTD - YTD(N-2)`. Balances: the YTD's (prior: the PYTD's) |
| Pro forma | `PF LTM` | nothing today |

At a fiscal-year anchor (k = 4) there is no year to date; `LTM` is `FY(N)` and `Prior LTM` is `FY(N-1)`.

Published keys per column, named as `cp2g.Year` names them so the store reads history with the forecast row specs: `revenue`, `ebitda`, `interest`, `capex`, `closing_debt`, `closing_cash`, `undrawn` (read); `tax_wc = taxes + wc`, `cfo = ebitda - interest - tax_wc`, `fcf = cfo - capex`, `liquidity = closing_cash + undrawn`, `net_debt = closing_debt - closing_cash`, `total_leverage = closing_debt / ebitda`, `net_leverage = net_debt / ebitda`, `coverage = ebitda / interest`, `fcf_to_debt = fcf / closing_debt` (derived, with `cp2g._ratio` and its not-computable reasons). A derived value with a missing component is missing with that component's reason.

### What is unavailable today, and what would populate it

| Column | Today | Shows | Minimum to populate (owner's decision) |
| --- | --- | --- | --- |
| Prior LTM (deferred by the owner) | Unavailable in all six retained runs at an interim anchor: no run prints the year to date two years back, and two print no fiscal year before last | `n.a.`, reason `needs 9M 2023, which CP-1 does not print` (the missing periods named) | The prior-year interim filing among the issuer files, and one more comparative column in CP-1's flow tables. No new table |
| PF (deferred by the owner) | Nothing writes pro forma adjustments | `n.a.`, reason `no handoff states pro forma adjustments` | A table of adjustments to the LTM (`Adjustment`, line, amount, basis) and a decision on who states it: CP-1 from issuer-stated figures, or a transaction module. `pro_forma_column`'s rule then applies: each adjustment added once to its line |
| LTM, YTD, PYTD | Buildable in five of six retained runs' period sets (one prints no fiscal year) when the lines are located | value, or `n.a.` naming the missing period | none |
| Balances in history | Only where CP-1 prints debt, cash or undrawn under a period header, not a date | value, or `n.a.` | Not in this plan: the period table's end dates could let a date header be read |

### Rulings carried in this plan (defaults; the owner may change any)

1. The seven groups always appear, in the owner's order. A group with nothing to show is one column of `n.a.` cells with its reason, never a blank, a zero or an omitted column.
2. `YTD` precedes `PYTD` and `LTM` precedes `Prior LTM`, the owner's wording. (The typed engine orders PYTD first.)
3. Main forecast columns are Base case (`REFERENCE`) and one Downside case: `DOWNSIDE` (CP-2A's shock on base drivers) when the run has it, else `DOWNSIDE_DRIVERS` (CP-2G's own). A note names which. With neither, the Downside group is one unavailable column (`no downside case was computed in this run`).
4. Every other case (`UPSIDE`, and `DOWNSIDE_DRIVERS` when the shock is the Downside) moves to a collapsed "Other forecast cases" table under the main grid, same rows, forecast columns only. Nothing is dropped.
5. The LTM is date-checked when CP-1's period table dates its three periods, and refused only when those dates fail the check. Without the dates it is built from the labels and a limit says it was not checked; a stub year or a changed year-end is then not detected.
6. A quarter is shown only when CP-1 prints it; none is calculated (`H1 - Q1`). The year to date is the printed `H1` or `9M` column, never a sum of quarters. CP-1's own LTM column or figure is not adopted.
7. The row "Cash proxy" means `cfo - capex` in every column. CP-1's own free cash flow (the `fcf` operand) is a different measure and is not shown in this row.
8. History is unreadable, never fatal: `history` returns reasons and raises nothing, because a `ValueError` from `model_files` drops the whole forecast (`cpos.py:457`).
9. A delivery without a `history` record (every existing one, and the older TDG delivery) keeps today's historical columns; only rulings 3 and 4 apply to it. The store checks files against `delivery.json` hashes on disk, so old deliveries are unaffected.
11. Owner, 2026-11-12 ("approved"): rulings 2, 3 and 4 stand; the period table is added now; Prior LTM and PF ship as `n.a.` with their reasons and no new handoff content; the proof is one paid run after PR 2, the owner's separate action.
12. The period-table instruction also asks CP-1 to head period columns in the forms Python reads (`FY2024`, `Q3 2025`, `H1 2025`, `9M 2025`). It goes to CP-1 whenever a forecast is wanted, with or without CP-2G.
13. Not in this plan: base operands are stated in USD millions and checked against CP-1's text as printed, so a CP-1 that prints thousands has its forecast refused today (`base ebitda 667.621 is not printed in CP-1`; seven-digit amounts fail the amount pattern). The fix changes how base operands are checked and is its own change; see "After the tasks".
14. Added at Task 2's review (2026-11-12): a line is anchored only by the base amount printed under a period header, and rows with different labels are one line only when all print the base amount in one common period. Both fail closed: a wrong row's figures are worse than an unavailable line.
15. Added at the adversarial review (2026-11-12); these replace the header and location rules above where they differ:
    - Every line is tied to one base period. With CP-2G as source it is the single period in which CP-1's revenue and EBITDA rows print their base amounts; with CP-1's layer-1 block it is the row and period CP-1 named. A row is a candidate only when it prints the base amount in that period. No single base period: no history, with the reason. Matching by amount alone located unrelated rows for about a quarter of two-digit amounts in two retained handoffs.
    - Rows with different labels are one line only when they also agree in a period other than the base.
    - For interest, taxes and capex a row's sign comes from its base cell (a refund stays a refund), not a magnitude per period.
    - Header tails are an allowlist: none, ` revised`, ` recast`, ` restated`, or `: <word> weeks ended YYYY-MM-DD`. `FY2024, annual definition`, a guidance column and a stub-year header are not periods and are named as unread.
    - A fiscal-year column at or after the first forecast year is not history. The anchor is the latest period of the revenue or EBITDA line; nothing later is published.
    - A fiscal year dated outside 364 to 371 days shows no full-year ratios.
    - A numeral of more than 38 digits is not a figure. Quoted headers are cut at 80 characters; at most 12 quarter and 8 fiscal-year columns are published, with a limit line when cut.
    - Not fixed here, for the owner: a regular expression in `cpos_forecast._tables` (before this branch) takes about 24 seconds on a heading with 3,000 spaces; quarter labels read `Q1 2025` where CP-1 wrote `Q1 FY2025`.
16. Added at the adversarial re-reviews and the whole-branch review (2026-11-12):
    - The sign of an interest, taxes or capex row is read from how its base cell is printed (brackets or a minus, zero included). An unsigned zero base takes the common sign of the row's other figures; with none or mixed signs the line has no history.
    - CP-2G base period: each of revenue and EBITDA that has an amount must print it under a period, and they must share exactly one. Otherwise no line has history, and the headers they are printed under are named.
    - The forecast-year guard never drops the base period or anything earlier.
    - The `: <word> weeks ended DATE` tail is read only on quarter and year-to-date headers, not on a fiscal-year header.
    - Considered and not adopted: blocking a line when another label prints the base amount under a header that is not a period. The one live forecast run (`tdg-forecast-002`) restates its base figures that way in a summary table, and the rule removed the history of four correctly located lines. Residual: if the right row sits under a non-period header and one other row prints the identical amount in the base period, that other row's figures are published.
    - Considered and withdrawn: ignoring a row printed for the base period alone. It let a coincident row through. A different label printing the base period alone leaves the line not identified.
    - The `history` record is published only when the delivery request asks for it (a flag written only when true, as `forecast` is), so a delivery made before this change re-derives byte for byte. New CP-OS runs ask.
    - A prior LTM built without a date check has its own limit line. Operand reasons are cut at 200 characters.
10. Delivery adds no analysis: the store and page compute nothing new. Growth and margins use the store's existing `derive`; each column's `prior` is its prior-year column.

## Global Constraints

- The one instruction change is CP-1's period table (Task 6). CP-2G's instructions and CP-1's other instructions are not changed.
- Excel is input only; no workbook output.
- Missing is never zero: every value is known, or missing with its reason.
- Exact amounts: sums run in `cp2g._EXACT`; a published amount is `format(value, "f")`.
- Expected values in tests are the hand-computed answer key below or `Fraction` arithmetic written in the test, never production output.
- No provider call, no credential file. Never change predecessor repositories or retained run directories (`~/Documents/FinalWorkflow-Live` is read only).
- A presentation change needs a reader check recorded in `VERIFICATION.md` with its scope, as well as the fidelity check (Task 10).
- One verification record: `VERIFICATION.md`, under 1,000 lines (973 now; trim the oldest entries).
- Every task report ends with a `Not verified:` line. No stub or fake value standing in for real behaviour; no catch-all that hides a failure.
- Per task run only the named tests (each under 300 seconds). Before each PR: `uv run python tools/quality_gate.py`, then confidence-review and rewrite-tournament (post-edit) once on the branch diff.
- Two PRs, each under 800 changed lines: PR 1 is Tasks 1 to 6 (no presentation change), PR 2 is Tasks 7 to 10.

## Review Focus

1. A coincidental match: another row prints the base amount (capex 40 and amortisation 40). Expected: the line is not identified and shows `n.a.`, not the wrong row's figures. Test in Task 2. (Residual, not testable away: a wrong row that shares no period with the right one.)
2. Original and revised comparatives (`Q3 2024` and `Q3 2024 revised`) print different figures for one line. Expected: that period only is `n.a.` with its reason. Test in Task 2.
3. CP-1 with no readable table, or a base operand with no amount. Expected: the forecast still publishes; history columns are unavailable with reasons. Test in Task 5.
4. A fiscal-year-end anchor. Expected: no year to date, `LTM` is the fiscal year, `Prior LTM` is the year before. Test in Task 3.
6. Period dates that do not make twelve months (a changed year-end, a mislabelled interim). Expected: the LTM's flows are `n.a.` with the reason, not a wrong sum. Test in Task 4.
7. A CP-1 without the period table. Expected: the LTM is built and a limit says it was not date-checked. Test in Task 4.
5. A run with CP-2G's downside and CP-2A's shock. Expected: the shock is the Downside case; the other downside and the upside are in the other-cases table, none lost. Test in Task 8.

## File Structure

| File | Responsibility |
| --- | --- |
| `src/deploy_workflow/owners/cpos_periods.py` (new) | Period headers, line location, historical columns: pure, no I/O |
| `src/deploy_workflow/owners/cpos_forecast.py` | `model_files` writes `history` into `calculation.json` |
| `src/deploy_workflow/owners/cpos_launch.py` | `PERIOD_TABLE_BLOCK` in CP-1's instruction |
| `apps/issuer-library/credit_os/store.py` | Reads `history`, lays out the main columns, splits the cases |
| `apps/issuer-library/credit_os/web/views.js`, `screen.css` | Other-cases table |
| `tests/test_cpos_periods.py` (new) | Tasks 1 to 5 |
| `tests/test_credit_os_store.py` | Tasks 7 and 8 |
| `tests/test_cpos_launch.py` | The instruction assertion (Task 6); the two pinned group lists (Task 8) |
| `tests/test_library_page_browser.py` | Task 9 |
| `VERIFICATION.md` | Task 10 |

### Answer key (hand-computed; do not edit)

Fixture `CP1` (USD millions), three tables. The FY2024 column is `tests/test_cpos_launch.py`'s `BASE`.

```
| Reported label | Q3 2025 | Q3 2024 revised | 9M 2025 | 9M 2024 | FY2024 | FY2023 | Locator |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Net sales | 270 | 250 | 780 | 720 | 1,000 | 940 | p.2 |
| Adjusted EBITDA | 84 | 75 | 240 | 216 | 300 | 276 | p.9 |

| Reported label | 9M 2025 | 9M 2024 | FY2024 | Locator |
| --- | --- | --- | --- | --- |
| Cash paid for interest | (27) | (28) | (36) | p.4 |
| Income taxes paid | (15) | (14) | (20) | p.4 |
| Change in working capital | (12) | (9) | (10) | p.4 |
| Capital expenditures | (33) | (29) | (40) | p.4 |
| Free cash flow | 153 | 136 | 194 | p.4 |

| Metric | FY2024 | 9M 2025 | 9M 2024 |
| --- | --- | --- | --- |
| Total debt | 600 | 590 | 620 |
| Cash and cash equivalents | 100 | 120 | 90 |
| Undrawn revolver | 50 | 50 | 50 |
```

Anchor: 9M 2025 (N = 2025, k = 3).

| Key | Q3 2024 | Q3 2025 | YTD | PYTD | FY2023 | FY2024 | LTM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| revenue | 250 | 270 | 780 | 720 | 940 | 1000 | 1060 |
| ebitda | 75 | 84 | 240 | 216 | 276 | 300 | 324 |
| interest | n.a. | n.a. | 27 | 28 | n.a. | 36 | 35 |
| tax_wc | n.a. | n.a. | 27 | 23 | n.a. | 30 | 34 |
| capex | n.a. | n.a. | 33 | 29 | n.a. | 40 | 44 |
| cfo | n.a. | n.a. | 186 | 165 | n.a. | 234 | 255 |
| fcf | n.a. | n.a. | 153 | 136 | n.a. | 194 | 211 |
| closing_debt | n.a. | n.a. | 590 | 620 | n.a. | 600 | 590 |
| closing_cash | n.a. | n.a. | 120 | 90 | n.a. | 100 | 120 |
| net_debt | n.a. | n.a. | 470 | 530 | n.a. | 500 | 470 |
| liquidity | n.a. | n.a. | 170 | 140 | n.a. | 150 | 170 |

LTM ratios: total leverage 590/324, net leverage 470/324, coverage 324/35, cash proxy to debt 211/590. FY2024: 600/300 = 2, 500/300, 300/36, 194/600. Leverage and cash proxy to debt in a quarter, YTD or PYTD column: `n.a.`, `a ratio to part-year earnings is not shown`; coverage YTD 240/27.

Prior LTM: every flow `n.a.`, reason `needs 9M 2023, which CP-1 does not print`. With a `9M 2023` column added to the first table (Net sales 690, Adjusted EBITDA 204): prior LTM revenue 940 + 720 - 690 = 970, EBITDA 276 + 216 - 204 = 288; interest still `n.a.` (`needs FY2023, 9M 2023, ...`).

Fiscal-year anchor (the first table cut to `FY2024` and `FY2023`, the other two to `FY2024`): `YTD` and `PYTD` `n.a.`, reason `the latest reported period is fiscal year FY2024; there is no year to date`; LTM revenue 1000; prior LTM revenue 940.

Store growth and margin (existing `derive`): Q3 2025 revenue growth 270/250 - 1 = 0.08; YTD 780/720 - 1 = 1/12; FY2024 1000/940 - 1 = 3/47; LTM `n.a.` (prior LTM missing); FY2025E base case 1050/1000 - 1 = 0.05; LTM EBITDA margin 324/1060.

---

### Answer key for the date check (hand-computed; do not edit)

Period table appended to `CP1` (`CP1_DATED`):

```
| Period | Start | End |
| --- | --- | --- |
| FY2024 | 2024-01-01 | 2024-12-31 |
| FY2023 | 2023-01-01 | 2023-12-31 |
| 9M 2025 | 2025-01-01 | 2025-09-30 |
| 9M 2024 | 2024-01-01 | 2024-09-30 |
| Q3 2025 | 2025-07-01 | 2025-09-30 |
| Q3 2024 revised | 2024-07-01 | 2024-09-30 |
```

Days, first and last day included: FY2024 366 (leap year); 9M 2025 273 (31+28+31+30+31+30+31+31+30); 9M 2024 274. FY2024 ends 2024-12-31, the day before 9M 2025 starts; 9M 2024 starts with FY2024. Span 366 + 273 - 274 = **365**: checked. LTM runs 2024-10-01 to 2025-09-30.

| Case | Change to the table | Result |
| --- | --- | --- |
| Changed year-end | FY2024 is 2023-10-01 to 2024-09-30 | not continuous: FY2024 ends 2024-09-30, 9M 2025 starts 2025-01-01. LTM revenue `n.a.`; LTM `closing_debt` still 590 |
| Mislabelled interim | 9M 2024 is 2024-01-01 to 2024-06-30 (182 days) | span 366 + 273 - 182 = 457: LTM revenue `n.a.` |
| 52-week quarter | FY2024 2023-10-01 to 2024-09-30 (366), `Q1 FY2025` 2024-10-01 to 2024-12-28 (31+30+28 = 89), `Q1 FY2024` 2023-10-01 to 2023-12-30 (31+30+30 = 91) | span 366 + 89 - 91 = 364: checked |
| No table (`CP1`) | none | LTM revenue 1060; limit says not date-checked |
| One period undated | the `9M 2024` row removed | LTM revenue 1060; not date-checked |
| Two rows disagree | a second `FY2024` row, 2024-01-01 to 2024-12-30 | FY2024 undated and named in a limit; LTM revenue 1060; not date-checked |

---

## PR 1: history record (no presentation change)

### Task 1: Period headers

**Files:**
- Create: `src/deploy_workflow/owners/cpos_periods.py`
- Test: `tests/test_cpos_periods.py`

**Interfaces:**
- Produces:
  - `Period = tuple[str, int, int]`: `(kind, fiscal year, quarters to date)`, kind `"QUARTER"`, `"YTD"` or `"FY"`.
  - `def period_of(header: str) -> Period | None`
  - `def period_label(period: Period) -> str`

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("header, period", [
    ("FY2024", ("FY", 2024, 4)), ("FY 2024", ("FY", 2024, 4)), ("**FY2024 revised**", ("FY", 2024, 4)),
    ("FY2024, annual definition", ("FY", 2024, 4)),
    ("Q3 2025", ("QUARTER", 2025, 3)), ("Q3 2024 recast", ("QUARTER", 2024, 3)),
    ("Q1 FY2025", ("QUARTER", 2025, 1)),
    ("Q1 FY2025: thirteen weeks ended 2024-12-28", ("QUARTER", 2025, 1)),
    ("9M 2025", ("YTD", 2025, 3)), ("9M2024", ("YTD", 2024, 3)), ("9M 2024 revised", ("YTD", 2024, 3)),
    ("H1 2025", ("YTD", 2025, 2)), ("6M 2025", ("YTD", 2025, 2)),
])
def test_the_header_forms_the_retained_handoffs_print(header, period):
    assert period_of(header) == period

@pytest.mark.parametrize("header", [
    "Q2 2025 net sales", "Rolling reported periods to 2024-12-28", "September 30, 2025",
    "LTM June 2025", "FY24", "Q5 2025", "2025", "Locator", "FY2024 and FY2023", "",
])
def test_anything_else_is_not_a_period(header):
    assert period_of(header) is None

def test_labels():
    assert [period_label(p) for p in (("QUARTER", 2025, 3), ("YTD", 2025, 3), ("YTD", 2025, 2), ("FY", 2024, 4))] \
        == ["Q3 2025", "9M 2025", "H1 2025", "FY2024"]
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_periods.py -q` — expected: fails on import.
- [ ] **Step 3: Implement** with one compiled pattern (`re.ASCII`, `fullmatch`) per the Design's header form; strip emphasis with `cpos_forecast._plain`.
- [ ] **Step 4: Run** the same command — expected: all pass.
- [ ] **Step 5: Commit** `feat(forecast): read the period headers CP-1 prints`

### Task 2: Locate the base lines

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_periods.py`
- Test: `tests/test_cpos_periods.py`

**Interfaces:**
- Consumes: `period_of`; `cpos_forecast._tables`, `_signed`, `_plain`, `_agrees`; `cp2g.Operands`, `cp2g.Val`, `cp2g.OUTFLOWS`.
- Produces:
  - `@dataclass(frozen=True) class Line: values: dict[Period, Decimal]; gaps: dict[Period, str]; reason: str | None; unread: tuple[str, ...]` (`reason` set: no history for the line; `unread`: year-bearing headers of its tables that are not periods).
  - `def lines(tables: list[list[list[str]]], operands: cp2g.Operands) -> dict[str, Line]`, one entry per operand key.
  - Reason texts (module constants, exact): `NOT_A_CELL = "the base amount is not a table cell of CP-1"`, `NOT_IDENTIFIED = "CP-1 prints the base amount in more than one row and they differ; the line is not identified"`, `DIFFERENT = "CP-1 prints different figures for this line in {period}"`. An operand with no amount: its own reason.

- [ ] **Step 1: Write the failing tests** with `CP1` from the answer key, `TABLES = cpos_forecast._tables(CP1)` and `OPERANDS` built from `tests/test_cpos_launch.py`'s `BASE`:

```python
def test_each_base_line_is_read_in_every_period_cp1_prints():
    found = lines(TABLES, OPERANDS)
    assert found["revenue"].values == {("QUARTER", 2025, 3): D("270"), ("QUARTER", 2024, 3): D("250"),
        ("YTD", 2025, 3): D("780"), ("YTD", 2024, 3): D("720"), ("FY", 2024, 4): D("1000"), ("FY", 2023, 4): D("940")}
    assert found["interest"].values == {("YTD", 2025, 3): D("27"), ("YTD", 2024, 3): D("28"), ("FY", 2024, 4): D("36")}
    assert found["wc"].values[("YTD", 2025, 3)] == D("12")      # (12) printed: an investment
    assert found["debt"].values[("YTD", 2024, 3)] == D("620")
    assert all(line.reason is None for line in found.values())

def test_a_second_row_with_the_base_amount_leaves_the_line_unidentified():   # Review Focus 1
    cp1 = CP1.replace("| Free cash flow |", "| Amortisation | (33) | (30) | (40) | p.4 |\n| Free cash flow |")
    found = lines(cpos_forecast._tables(cp1), OPERANDS)
    assert found["capex"].reason == NOT_IDENTIFIED and found["capex"].values == {}
    assert found["revenue"].reason is None

def test_the_same_line_in_two_tables_is_one_line_when_they_agree():
    cp1 = CP1 + "\n| Summary | FY2024 | 9M 2025 |\n| --- | --- | --- |\n| Revenue | 1,000 | 780 |\n"
    assert lines(cpos_forecast._tables(cp1), OPERANDS)["revenue"].values[("YTD", 2025, 3)] == D("780")

def test_two_labels_that_disagree_in_a_shared_period_are_not_identified():
    cp1 = CP1 + "\n| Summary | FY2024 | 9M 2025 |\n| --- | --- | --- |\n| Revenue | 1,000 | 781 |\n"
    assert lines(cpos_forecast._tables(cp1), OPERANDS)["revenue"].reason == NOT_IDENTIFIED

def test_an_original_and_a_revised_comparative_that_differ_blank_that_period_only():   # Review Focus 2
    cp1 = CP1 + "\n| Reported label | Q3 2024 | FY2024 |\n| --- | --- | --- |\n| Net sales | 251 | 1,000 |\n"
    line = lines(cpos_forecast._tables(cp1), OPERANDS)["revenue"]
    assert line.gaps[("QUARTER", 2024, 3)] == "CP-1 prints different figures for this line in Q3 2024"
    assert line.values[("FY", 2024, 4)] == D("1000")

def test_a_stated_gap_cell_is_not_a_figure():
    cp1 = CP1.replace("| Capital expenditures | (33) |", "| Capital expenditures | Not supplied: not extracted |")
    assert ("YTD", 2025, 3) not in lines(cpos_forecast._tables(cp1), OPERANDS)["capex"].values

def test_an_operand_without_an_amount_or_a_cell_has_its_reason():
    ops = replace(OPERANDS, undrawn=cp2g.Val(None, "CP-1 states no facility"), fcf=cp2g.Val(D("999"), None))
    found = lines(TABLES, ops)
    assert found["undrawn"].reason == "CP-1 states no facility" and found["fcf"].reason == NOT_A_CELL

def test_year_headers_that_are_not_periods_are_named():
    cp1 = CP1.replace("| Metric | FY2024 | 9M 2025 | 9M 2024 |", "| Metric | FY2024 | September 30, 2025 | 9M 2024 |")
    assert lines(cpos_forecast._tables(cp1), OPERANDS)["debt"].unread == ("September 30, 2025",)
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_periods.py -q` — expected: the new tests fail (`lines` not defined).
- [ ] **Step 3: Implement `lines`** per "Which lines have history", steps 1 to 5. Labels compare with `_plain`; only cells in columns after the first are read.
- [ ] **Step 4: Run** the same command — expected: all pass.
- [ ] **Step 5: Commit** `feat(forecast): find the base lines in CP-1's tables by amount`

### Task 3: Historical columns

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_periods.py`
- Test: `tests/test_cpos_periods.py`

**Interfaces:**
- Consumes: `lines`, `period_label`; `cp2g._EXACT`, `cp2g._ratio`, `cp2g.NC_EBITDA`, `cp2g.NC_INTEREST`, `cp2g.NC_DEBT`, `cp2g.Val`.
- Produces: `def history(tables: list[list[list[str]]], operands: cp2g.Operands) -> dict[str, object]`, the published record:

```json
{"schema_version": "cpos-history/1",
 "columns": [{"id": "Q3 2025", "kind": "QUARTER", "label": "Q3 2025", "prior": "Q3 2024", "reason": null,
              "values": {"revenue": {"amount": "270", "reason": null}, "...": {}}}],
 "limits": ["..."]}
```

  - `kind`: `QUARTER`, `YTD`, `PYTD`, `FY`, `LTM`, `PRIOR_LTM`, `PF`. Column order: quarters, `YTD`, `PYTD`, fiscal years, `LTM`, `PRIOR_LTM`, `PF`.
  - `id`: the period label for a quarter or fiscal year; `YTD`, `PYTD`, `LTM`, `PRIOR_LTM`, `PF` otherwise. A group with no period is one column with id and label `Quarter` or `Fiscal year`.
  - `label`: `YTD (9M 2025)`, `PYTD (9M 2024)`, `LTM Q3 2025` (`LTM FY2024` at a fiscal-year anchor), `Prior LTM`, `PF LTM`; `YTD` and `PYTD` bare when there is none.
  - `prior`: the id of the prior-year column (a quarter's same quarter a year before, a fiscal year's previous year, `YTD` to `PYTD`, `LTM` to `PRIOR_LTM`), or null.
  - `reason`: null, or why the whole column has no value. `values`: all sixteen keys of "Columns and arithmetic", each `{amount, reason}`.
  - Texts (exact): `NO_YTD = "the latest reported period is fiscal year {label}; there is no year to date"`; `NEEDS = "needs {labels}, which CP-1 does not print"` (missing periods, comma-separated: the fiscal year, then the added year to date, then the subtracted one); `NO_PF = "no handoff states pro forma adjustments"`; `PART_YEAR = "a ratio to part-year earnings is not shown"`; `NO_COLUMN = "CP-1 prints no {quarter|fiscal-year} column Python can read"`; `NO_ANCHOR = "no base line was found under a period header of CP-1"`.
  - `limits`: first `NOT_DATED = "Historical columns are built from the periods CP-1 labels; CP-1 dates no period table for them, so the last twelve months are not checked for a short or changed fiscal year."` (Task 4 replaces it when the dates are checked); one `"{line}: {reason}"` per line with a reason (`line` from `cp2g._OPERAND_WORDS`); `"CP-1 column headers not read as periods: {headers}."` when any.

- [ ] **Step 1: Write the failing tests** (`cell(record, id, key)` returns the column's `values[key]`):

```python
def test_the_columns_are_the_owners_set_in_order():
    record = history(TABLES, OPERANDS)
    assert [(c["id"], c["label"], c["prior"]) for c in record["columns"]] == [
        ("Q3 2024", "Q3 2024", None), ("Q3 2025", "Q3 2025", "Q3 2024"),
        ("YTD", "YTD (9M 2025)", "PYTD"), ("PYTD", "PYTD (9M 2024)", None),
        ("FY2023", "FY2023", None), ("FY2024", "FY2024", "FY2023"),
        ("LTM", "LTM Q3 2025", "PRIOR_LTM"), ("PRIOR_LTM", "Prior LTM", None), ("PF", "PF LTM", None)]

@pytest.mark.parametrize("key, ytd, pytd, fy, ltm", [
    ("revenue", "780", "720", "1000", "1060"), ("ebitda", "240", "216", "300", "324"),
    ("interest", "27", "28", "36", "35"), ("tax_wc", "27", "23", "30", "34"),
    ("capex", "33", "29", "40", "44"), ("cfo", "186", "165", "234", "255"),
    ("fcf", "153", "136", "194", "211"), ("closing_debt", "590", "620", "600", "590"),
    ("closing_cash", "120", "90", "100", "120"), ("net_debt", "470", "530", "500", "470"),
    ("liquidity", "170", "140", "150", "170"),
])
def test_the_answer_key(key, ytd, pytd, fy, ltm):
    record = history(TABLES, OPERANDS)
    got = [D(cell(record, column, key)["amount"]) for column in ("YTD", "PYTD", "FY2024", "LTM")]
    assert got == [D(ytd), D(pytd), D(fy), D(ltm)]

def test_ratios():
    record = history(TABLES, OPERANDS)
    near = lambda column, key, want: abs(Fraction(cell(record, column, key)["amount"]) - want) < Fraction(1, 10**12)
    assert near("LTM", "total_leverage", Fraction(590, 324)) and near("LTM", "net_leverage", Fraction(470, 324))
    assert near("LTM", "coverage", Fraction(324, 35)) and near("YTD", "coverage", Fraction(240, 27))
    assert near("FY2024", "fcf_to_debt", Fraction(194, 600))
    assert cell(record, "YTD", "total_leverage") == {"amount": None, "reason": PART_YEAR}

def test_prior_ltm_names_the_period_cp1_does_not_print():
    record = history(TABLES, OPERANDS)
    assert cell(record, "PRIOR_LTM", "revenue") == {"amount": None, "reason": "needs 9M 2023, which CP-1 does not print"}
    assert cell(record, "PRIOR_LTM", "interest")["reason"] == "needs FY2023, 9M 2023, which CP-1 does not print"

def test_prior_ltm_is_built_when_the_earlier_year_to_date_is_printed():
    # CP1 with a `9M 2023` column in the first table: Net sales 690, Adjusted EBITDA 204
    assert D(cell(record, "PRIOR_LTM", "revenue")["amount"]) == D("970")
    assert D(cell(record, "PRIOR_LTM", "ebitda")["amount"]) == D("288")

def test_pf_is_unavailable_with_its_reason():
    column = history(TABLES, OPERANDS)["columns"][-1]
    assert column["reason"] == NO_PF and all(v == {"amount": None, "reason": NO_PF} for v in column["values"].values())

def test_a_fiscal_year_anchor_has_no_year_to_date():            # Review Focus 4
    # the fiscal-year-anchor fixture of the answer key
    assert cell(record, "YTD", "revenue")["reason"] == "the latest reported period is fiscal year FY2024; there is no year to date"
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1000")
    assert D(cell(record, "PRIOR_LTM", "revenue")["amount"]) == D("940")
    assert [c["label"] for c in record["columns"]][:1] == ["Quarter"]     # no quarter printed: one n.a. column

def test_a_missing_quarter_cell_keeps_its_reason():
    assert cell(history(TABLES, OPERANDS), "Q3 2025", "interest") == \
        {"amount": None, "reason": "CP-1 does not print this line for Q3 2025"}

def test_the_limits_say_what_was_not_checked_or_read():
    limits = history(TABLES, OPERANDS)["limits"]
    assert limits[0] == NOT_DATED
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_periods.py -q` — expected: the new tests fail.
- [ ] **Step 3: Implement `history`.** The year to date for k = 1 is the `Q1` quarter period. A flow's LTM is missing with `NEEDS` naming every one of its three periods the line lacks. All sums inside `localcontext(cp2g._EXACT)`.
- [ ] **Step 4: Run** the same command — expected: all pass.
- [ ] **Step 5: Commit** `feat(forecast): quarters, YTD, PYTD, fiscal years, LTM, prior LTM and PF from CP-1's periods`

### Task 4: Period table and the date check

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_periods.py`
- Test: `tests/test_cpos_periods.py`

**Interfaces:**
- Consumes: `period_of`, `period_label`, `history` (Task 3).
- Produces:
  - `def period_dates(tables: list[list[list[str]]]) -> tuple[dict[Period, tuple[date, date]], tuple[str, ...]]`: the dated periods and the labels of periods whose rows disagree. A period table is any table whose first three header cells, plain, are `Period`, `Start`, `End`.
  - `history` calls it. Each column gains `"start"` and `"end"` (ISO text or null): a quarter's, fiscal year's, YTD's and PYTD's own dates; a checked LTM's start is the day after its PYTD ends (its fiscal year's start at a fiscal-year anchor) and its end the YTD's.
  - Texts (exact): `NOT_CONTINUOUS = "{fy}, {ytd} and {pytd} are not a continuous twelve months by CP-1's period dates ({detail})"`, `detail` one of `"{fy} ends {date}; {ytd} starts {date}"`, `"{pytd} starts {date}; {fy} starts {date}"`, `"{days} days"`, the first that applies; at a fiscal-year anchor `"{fy} is not twelve months by CP-1's period dates ({days} days)"`. Limits: `DATED = "The last twelve months were checked against CP-1's period dates ({days} days)."` in place of `NOT_DATED`; `"CP-1's period table dates {label} more than once, differently; it is treated as undated."` per such period.
  - A failed check sets the reason on the LTM's seven flow keys and the ratios on them (`cfo`, `fcf`, leverage, coverage, cash proxy to debt); `closing_debt`, `closing_cash`, `undrawn`, `liquidity`, `net_debt` are kept.

- [ ] **Step 1: Write the failing tests** (`dated(**rows)` returns `CP1` with the answer key's period table, a keyword replacing or, with `None`, removing a row):

```python
def test_the_period_table_is_read():
    dates, twice = period_dates(cpos_forecast._tables(CP1_DATED))
    assert dates[("YTD", 2025, 3)] == (date(2025, 1, 1), date(2025, 9, 30))
    assert dates[("QUARTER", 2024, 3)] == (date(2024, 7, 1), date(2024, 9, 30)) and twice == ()

def test_a_checked_ltm_says_so_and_carries_its_dates():
    record = history(cpos_forecast._tables(CP1_DATED), OPERANDS)
    ltm = next(c for c in record["columns"] if c["id"] == "LTM")
    assert (ltm["start"], ltm["end"]) == ("2024-10-01", "2025-09-30")
    assert D(ltm["values"]["revenue"]["amount"]) == D("1060")
    assert record["limits"][0] == "The last twelve months were checked against CP-1's period dates (365 days)."

def test_a_changed_year_end_is_not_summed():                     # Review Focus 6
    record = history(cpos_forecast._tables(dated(FY2024=("2023-10-01", "2024-09-30"))), OPERANDS)
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason":
        "FY2024, 9M 2025 and 9M 2024 are not a continuous twelve months by CP-1's period dates "
        "(FY2024 ends 2024-09-30; 9M 2025 starts 2025-01-01)"}
    assert cell(record, "LTM", "total_leverage")["amount"] is None
    assert D(cell(record, "LTM", "closing_debt")["amount"]) == D("590")
    assert D(cell(record, "YTD", "revenue")["amount"]) == D("780")

def test_a_mislabelled_interim_is_not_summed():
    record = history(cpos_forecast._tables(dated(**{"9M 2024": ("2024-01-01", "2024-06-30")})), OPERANDS)
    assert cell(record, "LTM", "revenue")["reason"].endswith("(457 days)")

def test_a_52_week_quarter_passes():
    # the 52-week case of the answer key, on a CP-1 whose first table is headed Q1 FY2025, Q1 FY2024, FY2024
    assert record["limits"][0].endswith("(364 days).")

@pytest.mark.parametrize("cp1", [CP1, dated(**{"9M 2024": None})])
def test_without_the_dates_the_ltm_is_built_and_marked_unchecked(cp1):     # Review Focus 7
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1060") and record["limits"][0] == NOT_DATED

def test_a_period_dated_twice_differently_is_undated():
    cp1 = CP1_DATED + "| FY2024 | 2024-01-01 | 2024-12-30 |\n"
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    assert record["limits"][0] == NOT_DATED
    assert "CP-1's period table dates FY2024 more than once, differently; it is treated as undated." in record["limits"]

@pytest.mark.parametrize("start, end", [("2024-13-01", "2024-12-31"), ("2024-12-31", "2024-01-01"), ("Jan 1, 2024", "2024-12-31")])
def test_an_unreadable_date_row_is_not_a_date(start, end):
    assert ("FY", 2024, 4) not in period_dates(cpos_forecast._tables(dated(FY2024=(start, end))))[0]
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_periods.py -q` — expected: the new tests fail (`period_dates` not defined).
- [ ] **Step 3: Implement.** Days are `(end - start).days + 1`. The checks run only when all three periods (or the anchor fiscal year) are dated.
- [ ] **Step 4: Run** the same command — expected: all pass, Task 3's tests included.
- [ ] **Step 5: Commit** `feat(forecast): date-check the last twelve months against CP-1's period table`

### Task 5: Publish the record

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_forecast.py:558-566` (`model_files`, the `calculation` document)
- Test: `tests/test_cpos_periods.py`

**Interfaces:**
- Consumes: `cpos_periods.history` (imported inside `model_files`: `cpos_periods` imports `cpos_forecast`'s helpers at module level).
- Produces: `calculation.json` gains `"history": <the record>`; `annual_periods`, `values` and every other file are unchanged.

- [ ] **Step 1: Write the failing tests** with `forecast_block` from `tests/test_cpos_launch.py`:

```python
def test_model_files_publishes_the_history_record():
    files = model_files(CP1.encode(), forecast_block().encode())
    record = json.loads(files["calculation.json"])["history"]
    ltm = next(c for c in record["columns"] if c["id"] == "LTM")
    assert D(ltm["values"]["revenue"]["amount"]) == D("1060")
    assert json.loads(files["calculation.json"])["annual_periods"] == []

def test_a_cp1_without_tables_still_publishes_the_forecast():      # Review Focus 3
    files = model_files(" ".join(BASE.values()).encode(), forecast_block().encode())
    record = json.loads(files["calculation.json"])["history"]
    assert [c["kind"] for c in record["columns"]] == ["QUARTER", "YTD", "PYTD", "FY", "LTM", "PRIOR_LTM", "PF"]
    assert all(v["amount"] is None and v["reason"] for c in record["columns"] for v in c["values"].values())
    assert "REFERENCE" in json.loads(files["forecast_exact.json"])["outputs"]

def test_the_forecast_figures_do_not_change():
    assert json.loads(model_files(CP1.encode(), forecast_block().encode())["forecast_exact.json"])["outputs"] == \
           json.loads(model_files(" ".join(BASE.values()).encode(), forecast_block().encode())["forecast_exact.json"])["outputs"]
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_periods.py -q` — expected: the new tests fail (`KeyError: 'history'`).
- [ ] **Step 3: Implement**: `history(_tables(cp1.decode("utf-8")), operands)` added to the `calculation` document. No `try`.
- [ ] **Step 4: Run** `uv run pytest tests/test_cpos_periods.py -q` and `uv run pytest tests/test_cpos_launch.py -q -k "forecast or library"` — expected: all pass (the library ignores the new key until PR 2).
- [ ] **Step 5: Run** `uv run python tools/quality_gate.py` — expected: exit 0. Add `tests/test_cpos_periods.py` to the PR check where `tests/test_cpos_facilities.py` is listed (`.github/workflows/checks.yml:42`).
- [ ] **Step 6: Commit** `feat(forecast): publish the historical columns with the model files`

### Task 6: CP-1 is asked for the period table

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_launch.py` (a new `PERIOD_TABLE_BLOCK` next to `LAYER1_FORECAST_BLOCK`; one entry in the block loop at `:1817`, `("CP-1", PERIOD_TABLE_BLOCK, forecast)`, before the layer-1 entry)
- Modify: `VERIFICATION.md`
- Test: `tests/test_cpos_launch.py` (next to the other `all_instructions` assertions)

**Interfaces:**
- Consumes: the table form of Task 4.

- [ ] **Step 1: Write the failing test**

```python
def test_cp1_is_asked_for_the_period_table_whenever_a_forecast_is_wanted(tmp_path):
    for modules in (("CP-0", "CP-1", "CP-2A", "CP-2G"), ("CP-0", "CP-1")):
        _, texts = all_instructions(tmp_path / "-".join(modules), modules=modules)
        head = texts["CP-1"].partition(cpos_launch.METHOD_MARK)[0]
        for words in ("`| Period | Start | End |`", "YYYY-MM-DD", "exactly as you print it", "`9M 2025`", "add no figure"):
            assert words in head
        assert all("| Period | Start | End |" not in text for name, text in texts.items() if name != "CP-1")
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_launch.py -q -k period_table` — expected: fails.
- [ ] **Step 3: Add `PERIOD_TABLE_BLOCK`** (exact copy, ending with a blank line as the other blocks do):

> Period table: inside `## Findings`, print one table whose header is exactly `| Period | Start | End |`, with one row for every period column header you use in your financial tables. `Period` is that header's text exactly as you print it (for example `9M 2025` or `FY2024`); `Start` and `End` are the period's first and last day as YYYY-MM-DD. Head period columns as `FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`, the year being the fiscal year the period belongs to. Python uses this table only to check that the fiscal year, the year to date and the prior year to date make twelve months; add no figure to it and change no other table.

- [ ] **Step 4: Run** `uv run pytest tests/test_cpos_launch.py -q -k "period_table or instruction or forecast"` — expected: all pass (the stubbed runs still deliver with the longer CP-1 instruction).
- [ ] **Step 5: Run** `uv run python tools/quality_gate.py` — expected: exit 0.
- [ ] **Step 6: Record in `VERIFICATION.md`** (973 lines; trim the oldest entries to stay under 1,000) one entry for PR 1, scope stated exactly: "offline synthetic tests of the history record and the date check; six retained CP-1 handoffs read for header forms only; no provider called, no model response; no real CP-1 has yet printed the period table; nothing on the page changes until PR 2". Include the retained-header result of Task 10 Step 1, run now, and the commands with exit codes.
- [ ] **Step 7: Commit** `feat(cp1): ask CP-1 for the period table; record`

---

## PR 2: the page

### Task 7: The store lays out the history

**Files:**
- Modify: `apps/issuer-library/credit_os/store.py` (`Column`, `cashflow_columns`, `op_key`, `cashflow_of`, `read_cashflow`, `CASHFLOW_NOTES`)
- Test: `tests/test_credit_os_store.py`; update `tests/test_cpos_launch.py:2981` and `:3001-3004` (the published model now has history columns first: assert the forecast labels and revenues from the end of the row, not from index 0)

**Interfaces:**
- Consumes: the `history` record's shape (Task 3). The test writes its own record by hand; it does not call `cpos_periods`.
- Produces:
  - `def history_inputs(record: Any) -> list[dict[str, Any]] | None`: the validated columns, or None when `calculation.json` has no `history`. At most `HISTORY_COLUMN_LIMIT = 60` columns (`CashflowLimit` beyond); each `values` through `checked_entries`; `kind` one of the seven; `prior` an earlier or later id of the record or null.
  - `def history_columns(history: list[dict[str, Any]]) -> list[Column]`: one `Column` per entry, `kind="h"`, `record` its `values`, `period=None`, `ytd=False`, `prior` the index of its `prior` id, new optional key `unavailable: NotRequired[str]` from `reason`. Group by kind: `QUARTER` "Quarter", `YTD`/`PYTD` "Year to date", `FY` "Fiscal year", `LTM`/`PRIOR_LTM` "Last twelve months", `PF` "Pro forma".
  - With a history, `cashflow_of` uses `history_columns` in place of `quarter_columns` and `fiscal_columns`; a history column's cells use each row's **forecast** spec; `op_key` on a history column returns `unavailable_cell(column["unavailable"])` when the key is absent and the column has a reason, else `absent_cell()`; a `None` spec on a history column is the same. The first forecast year's `prior` is the history column with id `FY{year - 1}`.
  - Notes with a history: `Q1_NOTE` and the "Pro forma: no pro forma period ..." note are dropped; added: `"LTM is the last fiscal year plus the year to date less the prior year to date, from the periods CP-1 labels."`. The record's `limits` follow the forecast's in `limits`.
  - Without a history: unchanged, byte for byte.

- [ ] **Step 1: Write the failing tests.** `HISTORY` is a hand-written record with the nine columns of the answer key and, per column, only the keys `revenue` and `ebitda` from the answer key table (`PRIOR_LTM` and `PF` with their reasons); `FILES` adds a `forecast_exact.json` with `REFERENCE` years 2025 to 2027 (revenue 1050, 1092, 1124.76; ebitda 315, 338.52, 359.9232), `annual.md` and `quarter.md` as one line of prose:

```python
def test_history_columns_precede_the_forecast_in_the_owners_order():
    grid, problem = store.read_cashflow(FILES, None)
    assert problem is None
    assert [(c["group"], c["label"]) for c in grid["columns"]][:9] == [
        ("Quarter", "Q3 2024"), ("Quarter", "Q3 2025"),
        ("Year to date", "YTD (9M 2025)"), ("Year to date", "PYTD (9M 2024)"),
        ("Fiscal year", "FY2023"), ("Fiscal year", "FY2024"),
        ("Last twelve months", "LTM Q3 2025"), ("Last twelve months", "Prior LTM"), ("Pro forma", "PF LTM")]
    assert [c["label"] for c in grid["columns"]][9:12] == ["FY2025E", "FY2026E", "FY2027E"]

def test_values_growth_and_margin_read_across_the_new_columns():
    row = {r["label"]: r["cells"] for r in store.read_cashflow(FILES, None)[0]["rows"]}
    assert [c["exact"] for c in row["Revenue"][:7]] == ["250", "270", "780", "720", "940", "1000", "1060"]
    growth = row["Revenue YoY growth"]
    assert Fraction(growth[1]["exact"]) == Fraction(8, 100)                        # Q3 2025 on Q3 2024
    assert abs(Fraction(growth[2]["exact"]) - Fraction(1, 12)) < Fraction(1, 10**20)   # YTD on PYTD
    assert abs(Fraction(growth[5]["exact"]) - Fraction(3, 47)) < Fraction(1, 10**20)   # FY2024 on FY2023
    assert Fraction(growth[9]["exact"]) == Fraction(5, 100)                        # FY2025E on FY2024
    assert growth[6]["status"] == "na"                                             # LTM: prior LTM missing
    assert abs(Fraction(row["Adj EBITDA margin"][6]["exact"]) - Fraction(324, 1060)) < Fraction(1, 10**20)

def test_an_unavailable_column_gives_every_row_its_reason():
    grid = store.read_cashflow(FILES, None)[0]
    assert all(row["cells"][8]["status"] == "na" for row in grid["rows"])
    reason = {r["label"]: r["cells"][8]["reason"] for r in grid["rows"]}
    assert reason["Revenue"] == reason["Distributions"] == "no handoff states pro forma adjustments"
    assert not any(note.startswith("Pro forma:") for note in grid["notes"])

def test_a_model_without_a_history_record_is_laid_out_as_before():
    files = {**FILES, "calculation.json": WITHOUT_HISTORY}
    assert [c["label"] for c in store.read_cashflow(files, None)[0]["columns"]][:3] == ["FY2025E", "FY2026E", "FY2027E"]

@pytest.mark.parametrize("damage", [
    {"columns": "x"}, {"columns": [{"id": "A", "kind": "WEEK", "label": "A", "prior": None, "reason": None, "values": {}}]},
    {"columns": [{"id": "A", "kind": "FY", "label": "A", "prior": "B", "reason": None, "values": {}}]},
])
def test_a_malformed_history_is_reported_not_shown(damage):
    grid, problem = store.read_cashflow({**FILES, "calculation.json": with_history(damage)}, None)
    assert grid is None and problem == ("file", "calculation.json")
```

- [ ] **Step 2: Run** `uv run pytest tests/test_credit_os_store.py -q -k "history or owners_order or new_columns or unavailable_column"` — expected: fail.
- [ ] **Step 3: Implement.** `read_cashflow` reads the history in the `calculation.json` stage; `cashflow_of` takes it with the recorded inputs.
- [ ] **Step 4: Run** `uv run pytest tests/test_credit_os_store.py -q` and `uv run pytest tests/test_cpos_launch.py -q -k "library"` — expected: all pass.
- [ ] **Step 5: Commit** `feat(library): Forecast grid shows quarters, YTD, fiscal years, LTM and PF before the cases`

### Task 8: Base case and one Downside case

**Files:**
- Modify: `apps/issuer-library/credit_os/store.py` (`FORECAST_CASES`, `forecast_inputs`, `cashflow_of`)
- Test: `tests/test_credit_os_store.py`; update `tests/test_cpos_launch.py:2982-2997`

**Interfaces:**
- Produces:
  - `FORECAST_CASES` names: `REFERENCE` "Base case", `UPSIDE` "Upside", `DOWNSIDE_DRIVERS` "Downside (CP-2G drivers)", `DOWNSIDE` "Downside stress (shock on base drivers)" (the last three as now).
  - `def main_cases(cases: Forecast, keys: list[str]) -> tuple[Forecast, Forecast, str]`: (main, other, note). Main is `REFERENCE` then the Downside, renamed "Downside case": `DOWNSIDE` when present, else `DOWNSIDE_DRIVERS`. Notes (exact): `"Downside case is the CP-2A shock applied to the base-case drivers."`, `"Downside case is CP-2G's own downside drivers; no CP-2A shock was supplied."`, `"Downside case: no downside case was computed in this run."`.
  - With no downside, the main grid ends with one column, group "Downside case", label "Downside", every cell `n.a.` with reason `no downside case was computed in this run`.
  - `cashflow["other"]`: `None`, or `{"columns": [...], "rows": [...]}` in the main grid's shapes, forecast columns of the other cases only, each case under its own name. Both grids' cells count against the budget.
  - Applies to every model, with or without a history.

- [ ] **Step 1: Write the failing tests** (`cases(*keys)` builds a `forecast_exact.json` holding those cases, revenue 1050 for `REFERENCE`, 1100 `UPSIDE`, 1000 `DOWNSIDE_DRIVERS`, 1040 `DOWNSIDE` in the first year):

```python
def test_the_shock_is_the_downside_when_both_downsides_exist():      # Review Focus 5
    grid = store.read_cashflow(cases("REFERENCE", "UPSIDE", "DOWNSIDE_DRIVERS", "DOWNSIDE"), None)[0]
    assert [c["group"] for c in grid["columns"]][-6::3] == ["Base case", "Downside case"]
    revenue = next(r for r in grid["rows"] if r["label"] == "Revenue")["cells"]
    assert [revenue[-6]["exact"], revenue[-3]["exact"]] == ["1050", "1040"]
    assert [c["group"] for c in grid["other"]["columns"]][::3] == ["Upside", "Downside (CP-2G drivers)"]
    other = next(r for r in grid["other"]["rows"] if r["label"] == "Revenue")["cells"]
    assert [other[0]["exact"], other[3]["exact"]] == ["1100", "1000"]
    assert "Downside case is the CP-2A shock applied to the base-case drivers." in grid["notes"]

def test_cp2gs_downside_is_the_downside_without_a_shock():
    grid = store.read_cashflow(cases("REFERENCE", "DOWNSIDE_DRIVERS"), None)[0]
    assert next(r for r in grid["rows"] if r["label"] == "Revenue")["cells"][-3]["exact"] == "1000"
    assert grid["other"] is None
    assert "Downside case is CP-2G's own downside drivers; no CP-2A shock was supplied." in grid["notes"]

def test_no_downside_is_an_unavailable_column_not_a_missing_one():
    grid = store.read_cashflow(cases("REFERENCE"), None)[0]
    assert (grid["columns"][-1]["group"], grid["columns"][-1]["label"]) == ("Downside case", "Downside")
    assert all(r["cells"][-1]["reason"] == "no downside case was computed in this run" for r in grid["rows"])
```

In `tests/test_cpos_launch.py`, the two group assertions become `["Base case", "Downside case"]`, and the every-case test reads the upside and CP-2G downside figures from `grid["other"]` (same expected revenues: `1100, 1210, 1331` and `1000, 1000, 1000`).

- [ ] **Step 2: Run** `uv run pytest tests/test_credit_os_store.py -q -k downside` — expected: fail.
- [ ] **Step 3: Implement.** One row-building loop serves both grids.
- [ ] **Step 4: Run** `uv run pytest tests/test_credit_os_store.py -q` and `uv run pytest tests/test_cpos_launch.py -q -k "library or cases"` — expected: all pass.
- [ ] **Step 5: Commit** `feat(library): Base case and one Downside case in the main Forecast grid`

### Task 9: The page shows the other cases

**Files:**
- Modify: `apps/issuer-library/credit_os/web/views.js:913-935` (`cashflowSection`), `screen.css` (next to `.cashflow-na`)
- Test: `tests/test_library_page_browser.py`

**Interfaces:**
- Consumes: `cashflow.other` (Task 8); column `group` and `label` (Task 7).
- Produces: `cashflowTable(c)` (the existing `<table class="cashflow">` markup, taken out of `cashflowSection` unchanged) used for the main grid and, when `c.other` is set, inside `<details class="cashflow-other"><summary>Other forecast cases: {group names, comma-separated}</summary>...</details>` after the notes. The scenario ground (`/^(Base case|Downside)/`) is unchanged. No other markup changes.

- [ ] **Step 1: Write the failing browser test** on a library built from Task 7's `FILES` with Task 8's four cases, using the file's existing `visit` helper on the model's Forecast route:

```python
groups = page.eval_on_selector_all(".forecast-cashflow > .table-scroll thead tr:first-child th[scope=colgroup]", "e => e.map(x => x.textContent)")
assert groups == ["Quarter", "Year to date", "Fiscal year", "Last twelve months", "Pro forma", "Base case", "Downside case"]
assert page.locator("details.cashflow-other summary").inner_text() == "Other forecast cases: Upside, Downside (CP-2G drivers)"
assert page.locator("details.cashflow-other table.cashflow thead tr:first-child th[scope=colgroup]").count() == 2
pf = page.locator(".forecast-cashflow > .table-scroll tbody tr:not(.band-row)").first.locator("td").nth(8)
assert pf.inner_text() == "n.a." and pf.get_attribute("aria-label") == "n.a.: no handoff states pro forma adjustments"
assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")   # the grid scrolls inside its region
```

- [ ] **Step 2: Run** `uv run pytest tests/test_library_page_browser.py -q -k other_forecast_cases` — expected: fails (no `details.cashflow-other`).
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** the same command and the web tests the repository already runs for `views.js` (docs/QUALITY-GATE.md) — expected: pass.
- [ ] **Step 5: Commit** `feat(library): other forecast cases under the main Forecast grid`

### Task 10: Retained-header check, reader check, record, gates

**Files:**
- Modify: `VERIFICATION.md`

- [ ] **Step 1: Retained-header check (offline, read only).** For each `~/Documents/FinalWorkflow-Live/runs/web-*/CP-1.md`, run `cpos_forecast._tables` and `cpos_periods.period_of` over every header (a one-off `uv run python -c`, no file written under that directory) and record, per run, the headers read as periods and the year-bearing headers not read. Expected from this plan's survey: every statement-table header in the Design table is read except `Q2 2025 net sales` (and its siblings) and `Rolling reported periods to 2024-12-28`. A statement-table period header not read is a defect in Task 1: fix it there with a failing test first.
- [ ] **Step 2: Fidelity check.** On the page Task 9's browser test builds, compare every history cell of the page with the answer key table: 11 keys by 7 columns, and the `n.a.` reasons of `Prior LTM` and `PF LTM`.
- [ ] **Step 3: Reader check.** Open that page and one existing published model without a history record. Read both against the September VMO2 reference as the portfolio manager: the seven groups are in the owner's order; a reader can tell an unavailable column from a zero; the Downside note says which case it is; the grid stays readable at fifteen columns. Record what was read and the result.
- [ ] **Step 4: Record in `VERIFICATION.md`** (trim the oldest entries to stay under 1,000 lines) one entry with the scope stated exactly: "synthetic fixture and six retained CP-1 handoffs for header forms; no provider called; no retained run has a forecast inputs block, so no real run's Forecast page was read: the reader check on a real run is pending a paid run". Commands and exit codes.
- [ ] **Step 5: Run** `uv run python tools/quality_gate.py` — expected: exit 0.
- [ ] **Step 6: Commit** `docs(verification): Forecast page main period columns`

## After the tasks

- Whole-branch, once per PR: confidence-review and rewrite-tournament (post-edit: `cpos_periods.lines`, `cpos_periods.history`; `store.cashflow_of`, `store.main_cases`).
- Owner's actions, not in this plan:
  1. One paid run with CP-2G on an issuer whose CP-1 prints interim and annual columns, then the reader check on that run's Forecast page. Until then the change is proven on synthetic inputs and retained header forms only.
  3. Decide whether CP-1 should print the year to date two years back (needs the prior-year interim filing) so `Prior LTM` is populated at an interim date.
  4. Decide where pro forma adjustments are stated, and by which module, so `PF LTM` is populated.
  5. Confirm ruling 3 (CP-2A's shock is "Downside") and ruling 2 (YTD before PYTD, LTM before prior LTM).
- Recommended before the paid run (owner's decision; it changes CP-2G's instruction): have CP-2G name the `row` and `period` of each base operand, as CP-1's layer-1 block already does. Locating a line by its amount is the source of every wrong-row finding in review; with named rows the residual above goes, and about 150 to 200 lines of identification code with it.
- Units, before the paid run (not in this plan; it changes how base operands are checked): the block states base operands in USD millions "exactly as CP-1 prints" them, and `cpos_forecast._printed` and the line location compare with CP-1's text as printed. Three of six retained CP-1 handoffs print USD thousands. There a CP-2G that converts to millions is refused (`667.621` is not printed where CP-1 prints `667,621`), and one that copies thousands fails the six-digit amount pattern for revenue and would mis-scale `dividends`, `debt_repayment` and facility amounts. Either way `model_files` raises and the run delivers no forecast, no history and no facility schedule. Smallest fix seen: an optional `scale` in the inputs block (1 or 1000, default 1 so existing blocks are unchanged), amounts copied as printed and divided by Python, the amount pattern widened, and the two instruction texts updated; about 150 to 250 changed lines with tests, money code, its own PR and adversarial review.
- Follow-ups seen, not fixed here: the grid's row labels carry TDG wording on every issuer ("Adj EBITDA (EBITDA As Defined)").
