# Forecast Reader Findings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Fix the seven findings of the reader check of run `20261112-164724-01` (LTH), recorded in `VERIFICATION.md` (2026-11-12, "Reader check of the Forecast page on a real run").

**Architecture:** Two independent branches from `main`. Engine (`claude/forecast-reader-findings`, Tasks E1-E4): the forecast inputs block may name a cell of a period-row table with a `column` key; the history record reads such tables and reads an `LTM Qn YYYY` label as a balance date for stocks only; one limit line is corrected; the instruction texts follow. Page (`claude/forecast-reader-findings-page`, Tasks P1-P3): history-path labels and notes, a fold for lines with no figure, a readable model picker.

**Tech stack:** Python 3 (pydantic, Decimal), plain JS (`views.js`), pytest, `node --test`.

**Spec:** the reader-check entry in `VERIFICATION.md`; owner rulings 1-16 in `docs/superpowers/plans/2026-11-12-forecast-period-columns.md`; `docs/superpowers/plans/2026-11-12-forecast-named-rows-and-units.md`.

## Global Constraints

- Ruling 1 stands: the seven column groups always appear; an empty group is one `n.a.` column. No column is removed.
- Missing is never zero. Delivery adds no analysis. Exact Decimal arithmetic; no rounding in the record.
- A block that uses none of the new keys publishes byte-identical files (pin it with a test on an existing fixture).
- Existing checks are not weakened: exact cell, sign rule, unit guard, partial naming refused, `scale`.
- No stub or fake value standing in for real behaviour; no catch-all that hides a failure. Answer keys in this plan are not edited by the implementer; comparisons are not weakened.
- Never `git add -f`. Never touch `~/Documents/FinalWorkflow-Live`, `/private/tmp/claude-501/rbot-live3` or `~/rbot-run-root` except to read.
- Gates per task: the affected tests; `uv run python tools/quality_gate.py`. Every report ends with a `Not verified:` line.
- Commits end `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`.

## Controller rulings

- R1. A new operand key `column` (not orientation guessing): explicit, and `row`/`period` keep their meaning. Cost if wrong: one more key for the model to learn.
- R2. `LTM Qn YYYY` as a row label or column header is read for stocks only (debt, cash, undrawn) as the balance at that label's End date, and only when CP-1's period table dates that label and its End equals the End of the record's YTD column (or of the fiscal year when there is no YTD). It is never read for a flow. Without the dated label: not read, reason stated. Cost if wrong: a balance column stays `n.a.`; never a wrong-date balance.
- R3. An operand without a base amount cannot name a history-only cell. LTH's June 2025 undrawn 618.5 therefore stays out and LTM liquidity stays `n.a.` with its reason. Known limit, reported to the owner.
- R4. `interest` is defined to the model as interest paid in cash; a model that has only interest expense may name it and must say so in `scope_limits`. On the history path the page calls the row "Interest". Cost if wrong: coverage on an expense basis is shown, labelled as such.
- R5. Finding 3 is fixed by folding lines with no figure in any column into one closed list; columns are untouched (ruling 1).
- R6. Nothing checks that a stock is named at the base period (ruling A4 of the named-rows plan stands). Known limit.

## Review Focus

1. A `column` name that matches a header in two tables with different cells for the row: refused, as an ambiguous `row`/`period` is today (E1 test).
2. A period-row table whose row label is a date (`2024-12-31`), not a period: the base cell is accepted, history shows `n.a.` with the existing not-under-a-period reason (E1 test).
3. `LTM Q2 2025` dated by the period table to a day other than the YTD End: stocks `n.a.`, reason names both dates (E2 test).
4. A fold that hides a row carrying a value only in an "other cases" table: the row is not empty (P2 test).
5. Two deliveries of one run in the picker: labels differ (P3 test).

---

## Engine branch

Fixture for E1-E3 (add to the tests as a new CP-1 fixture; the hand key below is the answer key). First table is measure-row, second and third period-row; period table dates the labels.

```
### Periods
| Period | Start | End |
| FY2024 | 2024-01-01 | 2024-12-31 |
| H1 2025 | 2025-01-01 | 2025-06-30 |
| H1 2024 | 2024-01-01 | 2024-06-30 |
| LTM Q2 2025 | 2024-07-01 | 2025-06-30 |

| Line, USD million | FY2024 | H1 2025 | H1 2024 | LTM Q2 2025 |
| Total revenue | 1000 | 540 | 500 | 1040 |
| Adjusted EBITDA | 300 | 170 | 150 | 320 |
| Interest paid | 36 | 17 | 18 | 35 |
| Total debt | 600 | Not applicable (balance date) | Not applicable (balance date) | 590 |

### Chart data: Liquidity
| Period | Cash | Undrawn | Reporting unit | Basis and limitation |
| FY2024 | 100 | 50 | US$m | Year end. |
| LTM Q2 2025 | 120 | 60 | US$m | 30 June 2025. |

### Net debt data
| Period | Gross debt | Cash | Net debt | Reporting unit | Basis and limitation |
| FY2024 | 600 | 100 | 500 | US$m | Year end. |
| LTM Q2 2025 | 590 | 120 | 470 | US$m | 30 June 2025. |
```

Block base: revenue 1000, ebitda 300, interest 36 (row/period form, `FY2024`); debt 600 (`"row": "Total debt"`, `"period": "FY2024"`); cash 100 (`"row": "FY2024"`, `"column": "Cash"`); undrawn 50 (`"row": "FY2024"`, `"column": "Undrawn"`); others missing with a reason.

Hand key, history record:

| line | FY2024 | YTD (H1 2025) | PYTD (H1 2024) | LTM Q2 2025 |
| :--- | :--- | :--- | :--- | :--- |
| revenue | 1000 | 540 | 500 | 1040 (1000+540-500) |
| ebitda | 300 | 170 | 150 | 320 |
| interest | 36 | 17 | 18 | 35 |
| closing_cash | 100 | after E1: n.a.; after E2: 120 | n.a. | after E2: 120 |
| undrawn | 50 | after E2: 60 | n.a. | after E2: 60 |
| liquidity | 150 | after E2: 180 | n.a. | after E2: 180 |
| closing_debt | 600 | after E2: 590 | n.a. | after E2: 590 |
| net_debt | 500 | after E2: 470 | n.a. | after E2: 470 |
| total leverage | 2 | n.a. (not twelve months) | n.a. | after E2: 590/320 |
| net leverage | 500/300 | n.a. | n.a. | after E2: 470/320 |

### Task E1: `column` names a cell of a period-row table

**Files:** `src/deploy_workflow/owners/cpos_forecast.py`, `src/deploy_workflow/owners/cpos_periods.py`; tests `tests/test_cpos_periods.py`, `tests/test_cpos_scale.py`, `tests/test_cpos_launch.py` (only where existing assertions on refusal text change).

**Interfaces — produces:** `Operand.column: str | None`; `cpos_periods` reads a column-form operand's table transposed (`_transposed(tables, column)`); `history(...)`/`_locate(...)` receive which keys are in column form.

- [ ] Tests first, on the fixture: (a) the block above is accepted and FY2024 `closing_cash` 100, `undrawn` 50, `liquidity` 150, `net_debt` 500 are in the record and in `forecast_exact.json`'s base; (b) `column` and `period` both stated → refused; (c) `column` without `row`, or `row` alone → refused with `base cash must name the `row` label and either the `period` header or the `column` header it was read from`; (d) amount 101 → refused (cell differs), text names `column`; (e) column header in no table → refused; (f) Review Focus 1 and 2; (g) the same fixture times 1000 at `scale` 1000 with the row's `Reporting unit` cell left `US$m` → refused by the unit guard; with it changed to `US$ thousands` → publishes the same figures as the millions fixture; (h) an existing fixture without `column` publishes byte-identical files before and after.
- [ ] `Operand` gains `column`; validator refuses `column` with `period`. `_layer1_problem`, `_check_base`, `_unit_problem` use `operand.period or operand.column` as the header; the refusal's `where` says `column` when that key is used. `model_files` passes the column-form keys to the history.
- [ ] `cpos_periods._transposed(tables, column)`: for each table holding `column` at header index > 0, a two-row measure table `[[header[0], *row labels], [column, *cells]]`, fed to the unchanged line reader with the target period read from the named `row`.
- [ ] Run the affected tests and the quality gate; commit.

### Task E2: an `LTM Qn YYYY` label is a balance date for stocks (ruling R2)

**Files:** `src/deploy_workflow/owners/cpos_periods.py`; test `tests/test_cpos_periods.py`.

- [ ] Tests first: the "after E2" cells of the hand key; Review Focus 3 (period table End `2025-05-31` for the LTM label → those stocks `n.a.`, reason `CP-1 dates LTM Q2 2025 to 2025-05-31, not the 2025-06-30 the year to date ends`); no period table row for the label → `n.a.`, reason `CP-1's period table does not date LTM Q2 2025`; a flow under an `LTM Qn YYYY` header is still never read (revenue LTM stays the built 1040 even if the printed cell is changed to 9999); a fiscal-year anchor (no YTD) reads the label only when its End equals the fiscal year's End.
- [ ] Implement for `closing_debt`, `closing_cash`, `undrawn` only, in both table shapes (header in a measure-row table, row label in a period-row table). The YTD and LTM columns carry the same balance.
- [ ] Run the affected tests and the quality gate; commit.

### Task E3: the "column headers not read" limit (finding 6)

**Files:** `src/deploy_workflow/owners/cpos_periods.py`; test `tests/test_cpos_periods.py`.

- [ ] Tests first: with the LTM built, the limits do not list the header equal to the LTM column's label; they carry `CP-1's own LTM Q2 2025 figures for revenue, earnings and cash flow are not read; the LTM column is built from FY2024 + H1 2025 - H1 2024.`; with the LTM not built the old line is unchanged; other unread headers are still listed.
- [ ] Implement in `_limits`/`_unread`. Run tests and gate; commit.

### Task E4: instruction and repair wording (findings 1, 2, 4)

**Files:** `src/deploy_workflow/owners/cpos_launch.py`; test `tests/test_cpos_launch.py`.

- [ ] FORECAST_BLOCK and LAYER1 (both), after the row/period sentence: `In a table with one row per period (CP-1's `Chart data:` tables and `Net debt data`), name the row by its period exactly as printed ("row": "FY2024") and the measure by its exact column header as `column` ("column": "Cash"), and leave out `period`.`
- [ ] Both blocks, where the operand keys are listed: ``interest` is interest paid in cash in the base period; where CP-1 prints only interest expense you may name that cell and must say in `scope_limits` that interest is interest expense, not cash paid.`
- [ ] PERIOD_TABLE_BLOCK (CP-1): `Print a balance (debt, cash, undrawn facilities) at a period's end under that period's column as a plain number: the `H1 2025` column holds the 30 June 2025 balance. Put the date in the row label or the Source, not in the cell.`
- [ ] `_forecast_issues` repair lines: `row, period or amount` → `row, period, column or amount`; `no row or period` → `no row, period or column`.
- [ ] Tests assert each sentence is in the instruction a CP-2G / CP-1 run is sent and the repair line for a `column` refusal. Run tests and gate; commit.

---

## Page branch

### Task P1: history-path labels and notes (findings 4, 5)

**Files:** `apps/issuer-library/credit_os/store.py`; test `tests/test_credit_os_store.py`.

On the history path only (a delivery with a history record); the older HTML-Model path is byte-identical (pin it).

- [ ] Row labels: `Adj EBITDA (EBITDA As Defined)` → `Adj EBITDA (as named in Financial foundation)`; `LTM Adj EBITDA (As Defined)` → `LTM Adj EBITDA`; `Closing debt (carrying value)` → `Closing debt`; `Cash interest` → `Interest`; `Interest coverage (Adj EBITDA / cash interest)` → `Interest coverage (Adj EBITDA / interest)`.
- [ ] Notes: drop the `EBITDA (EBIT + D&A) differs…` note and the two notes that say `EBITDA As Defined` and `securitization`; add, in this order after the Base case note: `Adj EBITDA is the earnings line the forecast inputs name in Financial foundation; in the forecast it is the model's earnings on that basis, not issuer guidance.` · `Leverage is closing debt, as the forecast inputs name it in Financial foundation, over Adj EBITDA. Leverage is shown for twelve-month periods only.` · `Historical interest is the Financial foundation line the forecast inputs name, which may be interest expense rather than cash paid; forecast interest is opening debt times the interest-rate driver.`
- [ ] Tests: exact label and note lists on a history fixture; no note on the history path contains `As Defined`, `securitization` or `refinancing`; the HTML-Model fixture's notes and labels unchanged. Run tests and gate; commit.

### Task P2: fold lines with no figure (finding 3)

**Files:** `apps/issuer-library/credit_os/store.py`, `apps/issuer-library/credit_os/web/views.js`; tests `tests/test_credit_os_store.py`, the node tests in `apps/issuer-library/credit_os/web/` that cover `views.js`, `tests/test_library_page_browser.py` (browser, run once at the branch gate).

- [ ] Store: each grid row gains `"empty": true` when no cell of the main table or any other-case table has a value. Section heading rows are empty when all their rows are.
- [ ] `views.js`: the main table renders the non-empty rows; the empty rows render, unchanged in columns and cells, inside `<details class="cashflow-empty"><summary>Lines with no figure in this run (N)</summary>…</details>` after the main table and before `cashflow-other`. `Why cells show n.a.` still counts every row.
- [ ] Tests: on the history fixture the folded set is exactly the rows with no value (name them in the test from the fixture by hand, not from the code); Review Focus 4; N equals the number of folded line rows; a delivery where every row has a value renders no `cashflow-empty`. Run tests and gate; commit.

### Task P3: model picker label (finding 7)

**Files:** `apps/issuer-library/credit_os/web/views.js`; node test beside it.

- [ ] Option text: `<run date> · <pathway> · <run id>` from the run context (`runDate`, `runPathway`, `ctx.run`), falling back to the run folder, then the delivery id. When two options have the same text, each gains ` · <first 8 characters of the delivery id>`. The relationship is appended only when recorded. Option values stay the delivery id.
- [ ] Tests: one delivery → no hash in the text; Review Focus 5; no context → falls back. Run tests and gate; commit.

---

## Verification (controller, after both branches)

- Engine: the real LTH CP-1 of run `20261112-164724-01` read with a hand-named block (synthetic drivers): FY2024 cash 10.879 and net debt 1,544.718 in the record. Scope stated as synthetic naming on a real handoff.
- Page: the LTH run's library rebuilt from a copy of the run root and read at 1440 px; reader check against the September VMO2 reference recorded with its scope.
- One `VERIFICATION.md` entry per branch.
