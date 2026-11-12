# Forecast Named Rows and Units Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** (PR A) CP-2G names the table row and period column of each base operand, so the Forecast page's history is read from the named row and never located by amount. (PR B) A CP-1 handoff that prints USD thousands gets a forecast: the inputs block states its amounts as printed with `scale: 1000`, Python divides, and every published figure stays in USD millions.

**Architecture:** Both changes sit at the door of `cpos_forecast.parse`. PR A lets a CP-2G block carry `row` and `period` and checks them with the layer-1 check; `cpos_periods` then builds history from named rows only and the amount-location code is deleted. PR B converts a scale-1000 block to USD millions before the schema validates it, so the existing amount types, the forecast engine, the facility schedule and every published key are untouched; only the printed and cell checks read the amounts as stated, and `cpos_periods` divides the cells it reads by the same scale. The store takes the grid's units caption from the forecast record when the record states it.

**Tech Stack:** Python, `decimal` (`cp2g._EXACT`), pydantic (existing `Contract`), pytest, `hypothesis` (already pinned, `pyproject.toml:13`); the store stays standard-library only. No new dependency. No `views.js` change.

**Spec:** This document's Design section. Source of both problems: `docs/superpowers/plans/2026-11-12-forecast-period-columns.md`, "After the tasks" (named rows; units). The owner has decided both are to be built, as two PRs in this order.

## Design

### Found while planning (each checked on this branch, 184cec8)

- `origin/main` is four commits ahead of this branch (tip 9fd334b, PR #65). It touches `cpos_launch.py` (16 lines added at :120, nothing inside the instruction blocks), appends tests to `tests/test_cpos_launch.py` and adds 4 lines to `VERIFICATION.md` (986 lines). Rebase before Task A1; the pre-flight table gives both sets of line numbers.
- **Four** of the six retained CP-1 handoffs print USD thousands, not three as the period-columns plan says (table below).
- The residual is real at the surface a reader sees: on the base, `model_files` with an unnamed CP-2G block on the residual's handoff publishes `FY2023 interest = 31`, the accrual row's figure (reviewer's probe `.superpowers/sdd/2026-11-12-forecast-period-columns/probes/adv2_right_row_unheaded.py`, output `FY2023 interest: 31`).
- With one label, `cpos_periods._identified` is always true: on the named path the whole identification rule is already dead code.
- The Forecast page's units caption is a guess: `store.cashflow_units` (`store.py:1478`) takes the first `<ISO> millions|billions|thousands` phrase of the forecast source handoff's `## Request`. The retained IHRT CP-2G handoff's Request says `USD thousands`; the live TDG forecast run's says `monetary inputs are millions`, which the pattern does not match (`Units not recorded`). After PR B a thousands issuer's grid would show millions captioned `USD thousands` unless the caption comes from the record.
- No retained delivery request (the five `web-*` deliveries and `tdg-forecast-002`) carries the `history` flag, and none of the six CP-1 handoffs has an inputs block. No retained delivery holds model files either: `tdg-forecast-002`'s block gave no drivers, so `parse` declined it and nothing was published. "Earlier deliveries re-derive byte for byte" is therefore pinned by the synthetic test alone.
- On `tdg-forecast-002`'s real CP-1, with its block's base amounts hand-named, the prototype reads revenue, EBITDA, interest, taxes, capex and cash under `FY2024`; fcf, debt and undrawn are printed only under `FY2024 / September 30, 2024` and have no history. That is the same six and three the amount location found.
- On the four retained thousands handoffs, hand-written scale-1000 blocks parse on the prototype (LTH revenue `2620.995`, Sotera `1100.441` from a cell without separators, B&G `849.827`, IHRT `3751.025`). Two residuals show on real text: LTH's `Revolver availability 618.5` (a `US$ million` row) named in a scale-1000 block parses to `0.6185`; B&G's `849827` without `scale` parses as USD 849,827 million.
- A throwaway prototype of both PRs in the session scratchpad (not in the worktree) passes the tests and answer keys written below and leaves the existing period, facility, launch and store tests green except the one Task A1 replaces. The two instruction tests were checked against the edited strings, not run. Line estimates are measured on it. It was not type-checked or run through the quality gate.

### PR A: named rows

**Parse.** A CP-2G block is *named* when any base operand states `row` or `period`. A named block is checked operand by operand with `_layer1_problem`, exactly as CP-1's layer-1 block is: an operand with an amount names both and the amount is the one number at that row label and column header; an operand without an amount names neither. A block that names none is checked as today (`_printed`) and forecasts as today.

**History.** `model_files` passes `named` for either source: `{key: (row, period)}` of the operands that state an amount and both names. `cpos_periods` reads a line only from a name. An operand with an amount and no name has no history, reason (exact): `the forecast inputs do not name the row and period of this line`.

**One period rule for both sources (layer 1's rule today, kept).**
1. Each operand's line is read under its own named period: the rows with the named label that print the base amount under a header of `period_of(period)`. Named periods may differ between operands (revenue under `FY2024`, debt under `9M 2025`); nothing reconciles them.
2. A named header that is not a period (a balance-sheet date, `LTM Q3 2025`, a calculation column) is accepted by `parse`, because it is a table cell, and the line has no history: `CP-1 prints the base amount only under a column header that is not a period ({header})`. The forecast is not affected.
3. The base period, used only by the forecast-year guard, is the latest period named for revenue or EBITDA (`_named_base`). The anchor is still the latest period of the revenue or EBITDA line.
4. A same-label row that does not print the base amount under the named period is not read (ruling 15 of the period-columns plan, kept).

**Kept for a named line:** period header forms and tails, the sign of interest, taxes and capex from the printed base cell (`_row_sign`, `NO_SIGN`), `DIFFERENT` and `NOT_PRINTED` per period, the anchor, YTD, PYTD, LTM arithmetic, the date check, the forecast-year guard, the 38-digit, 80-character, 200-character, 12-quarter and 8-year limits, the unread-headers limit.

**Deleted from `cpos_periods.py`** (served unnamed operands only): `_printed_in`, `_listed`, `_why_not`, `_by_label`, `_identified`, `_base_period`, `_refused_headers`; constants `NOT_IDENTIFIED`, `NO_BASE_PERIOD`, `NOT_IN_BASE_PERIOD`, `_MAX_PERIODS_NAMED`; the `itertools.combinations` import. `_hits` and `_line` take a required label; `_line` merges its rows directly. `NOT_A_CELL` stays for a named row that does not print the amount under the named period, which `parse` makes unreachable from `model_files`. Measured on the prototype after `ruff format`: `cpos_periods.py` 135 lines removed, 26 added (943 to 834). The period-columns plan guessed 150 to 200.

**Moot in the period-columns plan:** Design "Which lines have history" steps 1 to 3; ruling 14's second sentence (different labels as one line); ruling 15 bullets 1 (CP-2G base period, matching by amount) and 2; ruling 16 bullets 2 (revenue and EBITDA must share one period), 5 (the residual, now closed) and 6; Review Focus 1. Still in force: ruling 14's first sentence, ruling 15 bullets 3 to 7, ruling 16 bullets 1, 3, 4, 7, 8.

### PR B: units

**Where an amount enters the block** (all five, both sources; nothing else is scaled):

| Slot | Type today | Named in messages as |
| --- | --- | --- |
| `base.<key>.amount`, ten operands | `Signed`, `cpos_forecast.py:42` | `base revenue` |
| `base_drivers.dividends.values[i]`, `base_drivers.debt_repayment.values[i]` | `cp2g.AmountDriver`, `cp2g.py:164` | `base_drivers dividends year 1` |
| the same two drivers in `upside_drivers` and `downside_drivers` (`CaseDrivers`, `cpos_forecast.py:74-75`) | `cp2g.AmountDriver` | `upside_drivers dividends year 1` |
| `facilities[i].balance` | `cp2g.Amount`, `cpos_facilities.py:26` | `facility 1 balance` |
| `facilities[i].annual_amortisation` | `cp2g.Amount` or null, `cpos_facilities.py:34` | `facility 1 annual_amortisation` |

Growth, shares, the shock, percents, `reference_rate` and `years` are ratios or dates and are never scaled. The layer-1 path is the same `parse` with the first two rows only. `cp2g.MinimumLiquidity` is not in the block.

**Conversion at the door.** `scale` is optional, `1` or `1000`; absent or null means 1 (measured on the project's strict `Contract`: JSON `1000.0` and `1e3` read as 1000 and `true` as 1; a string is refused). At scale 1000, before the schema validates, each stated amount is replaced by its USD millions value: an exact shift of the decimal point three places, written without trailing zeros (`"600000"` is `"600"`, `"175509.5"` is `"175.5095"`). The stated text is kept by name for the checks. The amount types are **not** widened: `cp2g.AMOUNT_PATTERN` also governs the typed CP-2G submission and must not change.

**The pattern at scale 1000.** A stated amount fully matches `-?[0-9]{1,9}(\.[0-9])?`: at most nine integer digits and one decimal place, no separators. Its millions value then always fits the unchanged patterns (six integer digits, four decimals). A thousands amount with two or more decimals is not exact at four decimals in millions: it is refused, never rounded, and the operand is stated as missing. No retained handoff prints one.

**Checks.** The printed check (`_printed`), the cell check (`_layer1_problem`) and the facility balance check compare the amount **as stated** with CP-1's text. Every calculation uses the divided amount. `cpos_periods` compares each cell with the operand times the scale and divides the values it publishes by the scale, so history and forecast are in one unit; at scale 1 it does no arithmetic on a cell. Ratios are scale-free. The 1.25 times check and the scheduled-repayment check run on divided balances against divided base debt, so they hold as before; they are one-sided (a balance too small is not caught).

**Mixed units inside one handoff: one scale per block.** Every amount of the block is in the unit `scale` states. An operand whose only cell is in the other unit is stated as missing with a reason; a facility whose balance is in the other unit is left out. Python enforces this in one place only (ruling B7): a named row of a table with a `Reporting unit` column (the launcher's own chart-table contract, `cpos_launch.py:1104`) whose unit cell names the other unit is refused.

**How the reader is told.** When the block states `scale`, `forecast_exact.json` carries `"scale"` and `"units": "USD millions"`. At 1000 the scope limits gain, second in the list (exact): `The forecast inputs state base amounts, amount drivers and facility amounts in USD thousands, as CP-1 prints them (scale 1000); Python divided each by 1,000 before any calculation. Every figure here is USD millions.` The store shows the record's `units` as the grid caption; without it the caption is the Request phrase as today. The `history` record's shape and version do not change.

**Schema version.** `cpos-forecast-inputs/1` stays for both PRs. An absent `scale`, `row` or `period` means what it means today, so every existing block is still a valid `/1` block with the same outputs. A new version would make `parse` refuse every retained block (the version is matched exactly) or need two accepted versions, for no gain.

### Units in the six retained CP-1 handoffs (read only)

| Run | Statement tables | Other units inside the handoff |
| --- | --- | --- |
| `web-0dca13e7` (NATL) | USD millions (lines 19, 53) | none; the word thousand does not occur |
| `web-2cb85cb4` (LTH) | US$ thousands (lines 30, 69, 139), seven-digit revenue | the debt table's last four rows are `US$ million` (`Revolver availability 618.5`), unit in a column headed `Unit and terms / evidence`; `Chart data: debt maturities` is `US$m` with `Not supplied: reported in US$ thousands` |
| `web-79a17365` (Sotera) | US$ thousands (lines 16, 48), cells without separators (`1100441`) | `Chart data: liquidity` is `US$m` (`Reporting unit` column): cash `332.437`, undrawn `585.8` |
| `web-b7425f3d` (B&G) | USD thousands (lines 19, 57, 87, 130), six-digit amounts (`849,827`) | tables all thousands; revolver capacity `USD 233.0 million` in prose only |
| `web-d95ed5de` (IHRT) | USD thousands (lines 30, 69, 97, 131), seven-digit revenue | availability `$426.3 million` in prose only; a principal-map table with thousands and millions columns side by side (line 272) |
| `web-f7d2f1ab` (TDG) | USD millions | none |

Mixed units occur in all four thousands handoffs, and in each the revolver availability (the `undrawn` operand) is stated in USD millions: two in a table cell, two in prose only. B&G's six-digit amounts pass today's pattern, so a block that copies them without `scale` is read as millions, a thousand times too large; nothing in Python detects a missing or wrong `scale`.

### Rulings carried in this plan (defaults; the owner may change any)

| # | Ruling | Cost if wrong |
| --- | --- | --- |
| A1 | A CP-2G block naming no operand parses and forecasts as today; every history line is missing with the one reason | A model that ignores the instruction gets a forecast with no history. Refusing instead would break re-derivation of retained deliveries |
| A2 | Naming some operands that have amounts but not all is refused; the message names the first one missing them, in the block's order | CP-2G is sent back for repair (bounded retries); if it cannot repair it declines the forecast |
| A3 | For a named block the cell check replaces the printed-somewhere check: a figure CP-1 prints only in prose is no longer a base amount | That operand is missing in the forecast (B&G and IHRT state revolver availability only in prose) |
| A4 | One period rule for both sources, as in the Design; no check that operands name consistent periods | A flow named at an interim period beside a full-year revenue is not detected (true of layer 1 today) |
| A5 | The CP-2G instruction also asks for a period-headed column where CP-1 prints the amount under more than one; this sentence is not in the layer-1 text | Without it CP-2G may name a calculation column and lose a line's history |
| A6 | `cpos-history/1` and `cpos-forecast-inputs/1` are kept | A delivery made with the `history` flag from an unnamed CP-2G block between PR #63 and PR A would not re-derive byte for byte. None exists in the retained set |
| B1 | `scale` is 1 or 1000, absent means 1; a block without it gives byte-identical files | none known |
| B2 | One scale per block; an operand in the other unit is missing with a reason | `undrawn`, and with it the Liquidity row of every forecast year and history column, is `n.a.` on all four retained thousands issuers |
| B3 | At scale 1000 a stated amount has at most nine digits and one decimal place; anything else is refused, never rounded | A thousands cell printed with two or more decimals cannot be stated (none retained) |
| B4 | The block is converted before validation; amount types are not widened | A schema error at scale 1000 quotes the divided value, not the stated one |
| B5 | `scale` and `units` are published only when the block states `scale`; the limit line only at 1000 | A new block that omits `scale` keeps the guessed caption |
| B6 | The store's caption is the record's `units` when present | none known; old deliveries carry none and are unchanged |
| B7 | A named row whose own `Reporting unit` cell names the other unit is refused, when `scale` is stated | A false refusal loses the operand (CP-2G repairs it) or, on the layer-1 path, the forecast. Without it a millions cell copied into a thousands block is published a thousand times too small. Task B3 is this ruling alone and can be dropped |
| B8 | The 1.25 times and repayment messages quote divided figures and say so at scale 1000 | none known |
| B9 | `units` is always `USD millions`: the block's contract is USD | A non-USD issuer's caption says USD (the instruction already says USD today) |

### Not covered, stated so nobody assumes otherwise

- Nothing detects a missing or wrong `scale` (B&G's six-digit thousands read as millions). The instruction asks for `scale`; that is the only control.
- A millions cell in a thousands block is caught only through a `Reporting unit` column. LTH's `Unit and terms / evidence` column (its availability row parses to `0.6185`) and facility balances are not checked for unit. Open question 2 is the wider check.
- A balance named under a date header has no history (as today).
- The store's older label reader (TDG row labels in `annual.md`, used for a model without a `history` record and for senior secured leverage) reads CP-1 as printed. A scale-1000 delivery requested without the history record and printed with TDG's exact labels would show thousands; new CP-OS runs always ask for the record.

## Global Constraints

- Two PRs in this order: PR A is Tasks A1 to A4, PR B is Tasks B1 to B6, stacked on PR A. Each under 800 changed lines (`git diff --numstat` rule); the splits are named under "Line estimates".
- A block without `scale` and without names produces byte-identical files (no retained delivery holds model files to re-derive, so the pin is synthetic). Pins that must stay green and unedited: `tests/test_cpos_facilities.py::test_a_block_without_facilities_is_byte_identical_to_main` and every existing parse test except the one Task A1 replaces.
- `cp2g.py` and `cpos_facilities.py` are not edited. `views.js` is not edited.
- Excel is input only; no workbook output. Missing is never zero. Exact amounts: arithmetic in `cp2g._EXACT`, published as `format(value, "f")`; nothing is rounded.
- Expected values in tests are the answer keys below or `Fraction` arithmetic written in the test, never production output. The implementer does not edit an expected value or weaken a comparison.
- No provider call, no network, no credential file. `~/Documents/FinalWorkflow-Live` and `/private/tmp/claude-501/rbot-live3` are read only.
- No stub or fake value standing in for real behaviour; no catch-all that hides a failure. Every task report ends with a `Not verified:` line.
- Per task run only the named tests (each under 300 seconds). Before each PR: `uv run python tools/quality_gate.py` (PR B: `--base` the PR A branch), then confidence-review and rewrite-tournament (post-edit) once on the branch diff.
- One verification record: `VERIFICATION.md`, under 1,000 lines (986 at `origin/main`; trim the oldest entries).
- The caption change in PR B is a presentation change: it needs the fidelity check and a reader check recorded with its scope (Task B6).

## Review Focus

1. Scale 1000 with a decimal cell: cash `175,509.5` stated `"175509.5"`. Expected: `175.5095` exactly; `"175509.55"` is refused, not rounded. Tests in B1 and B2.
2. A negative bracketed thousands cell: capex `(139,750)` stated `"139750"`. Expected: magnitude `139.75`, history sign from the printed base cell. Tests in B1 and B2.
3. A named row in two tables with different figures. Expected: under the same header text, refused (`is not one number in CP-1`); under another header of the same period (`FY2024 revised`), only the row that prints the base amount is read. Test in A2.
4. A block with `scale` and unnamed rows. Expected: the forecast is in millions, the printed check reads the stated text, every history line has the one reason. Test in B1.
5. Facility balances at scale 1000 against base debt. Expected: both divided, the 1.25 times check on the divided figures, the message says so. Test in B1.

Two more a reviewer should try: the residual's shape (the right row under a non-period header, another row printing the same amount in the base period; expected `n.a.` with the header named, Task A2); and a millions cell named in a thousands block with and without a `Reporting unit` column (refused with it, published a thousand times too small without it: the stated residual).

## File Structure

| File | PR | Responsibility |
| --- | --- | --- |
| `src/deploy_workflow/owners/cpos_forecast.py` | A, B | `parse` accepts a named CP-2G block; `model_files` passes `named`; the scale conversion, the stated-amount checks, `scale` and `units` in the record |
| `src/deploy_workflow/owners/cpos_periods.py` | A, B | History from named rows only; amount location deleted; cells divided by the scale |
| `src/deploy_workflow/owners/cpos_launch.py` | A, B | `FORECAST_BLOCK` and `LAYER1_FORECAST_BLOCK` wording |
| `apps/issuer-library/credit_os/store.py` | B | `recorded_units`; the caption |
| `tests/test_cpos_periods.py` | A | Named default, deleted and changed tests, new tests |
| `tests/test_cpos_launch.py` | A, B | Parse, repair-check, end-to-end and instruction tests |
| `tests/test_cpos_scale.py` (new) | B | Scale answer keys |
| `tests/test_credit_os_store.py` | B | Caption tests |
| `.github/workflows/checks.yml` | B | `tests/test_cpos_scale.py` in the PR check list (:42) |
| `VERIFICATION.md` | A, B | One entry per PR |

## Pre-flight: where each named thing is

Verified by reading at 184cec8. Where `origin/main` (9fd334b) differs, its line follows in brackets.

| Name | File:line |
| --- | --- |
| `SCHEMA_VERSION`, `LIMIT`, `LAYER1_LIMIT`, `Signed` | `cpos_forecast.py:29`, `:30`, `:36`, `:42` |
| `Operand` (`amount`, `row`, `period`) | `cpos_forecast.py:45` (`:49`, `:51`, `:52`) |
| `CaseDrivers` (`dividends`, `debt_repayment`) | `cpos_forecast.py:66` (`:74`, `:75`) |
| `ForecastInputs` (`facilities`, `consistent`) | `cpos_forecast.py:94` (`:102`, `:106`) |
| `_printed`, `_plain`, `_signed`, `_tables`, `_cells`, `_agrees` | `cpos_forecast.py:142`, `:161`, `:166`, `:178`, `:219`, `:232` |
| `_layer1_problem`, `_declined` | `cpos_forecast.py:243`, `:268` |
| `parse` (the operand loop) | `cpos_forecast.py:290` (`:315-322`) |
| `_check_facilities` (1.25 times, repayments) | `cpos_forecast.py:328` (`:344-360`) |
| `_facility_detail`, `_unallocated` | `cpos_forecast.py:389`, `:457` |
| `model_files` (`exact`, `named`, the history call) | `cpos_forecast.py:481` (`:535`, `:563-571`, `:580-585`) |
| `period_of`, `period_dates` | `cpos_periods.py:30`, `:82` |
| `NOT_A_CELL`, `NOT_IDENTIFIED`, `NO_BASE_PERIOD`, `NOT_IN_BASE_PERIOD` | `cpos_periods.py:97`, `:98`, `:101`, `:102` |
| `NO_REASON`, `NO_SIGN`, `DIFFERENT`, `NOT_PRINTED`, `NOT_UNDER_A_PERIOD`, `_MAX_PERIODS_NAMED` | `cpos_periods.py:103`, `:104`, `:105`, `:106`, `:107`, `:114` |
| `Line`, `_Hit`, `_number`, `_published`, `_hits` | `cpos_periods.py:124`, `:144`, `:154`, `:163`, `:169` |
| `_printed_in`, `_negative`, `_row_sign`, `_row`, `_rows_under` | `cpos_periods.py:192`, `:202`, `:207`, `:226`, `:241` |
| `_listed`, `_why_not`, `_by_label`, `_identified`, `_unread`, `_line` | `cpos_periods.py:251`, `:257`, `:268`, `:277`, `:301`, `:310` |
| `_base_period`, `_refused_headers`, `lines`, `_locate`, `_named_base`, `_named_line` | `cpos_periods.py:340`, `:354`, `:368`, `:382`, `:407`, `:415` |
| `_anchor_of`, `_limits` (its `NO_BASE_PERIOD` use), `_before_forecast`, `history` | `cpos_periods.py:502`, `:865` (`:880`), `:891`, `:916` |
| `_EXACT`, `AMOUNT_PATTERN`, `Amount`, `AmountDriver`, `BaseDrivers`, `_exact`, `Val`, `Operands`, `forecast` | `cp2g.py:90`, `:138`, `:146`, `:164`, `:171`, `:274`, `:285`, `:412`, `:551` |
| `Facility` (`balance`, `annual_amortisation`) | `cpos_facilities.py:24` (`:26`, `:34`) |
| `FORECAST_BLOCK` (the `base` sentence; facility units) | `cpos_launch.py:1521` (`:1525-1528`; `:1545`, `:1554`) [`:1537` (`:1541-1544`; `:1561`, `:1570`)] |
| `PERIOD_TABLE_BLOCK`, `LAYER1_FORECAST_BLOCK` (its `base` sentences) | `cpos_launch.py:1587`, `:1600` (`:1603-1613`) [`:1603`, `:1616` (`:1619-1629`)] |
| the block loop; `_forecast_issues` | `cpos_launch.py:2115-2118`; `:2298` [`:2131-2134`; `:2314`] |
| callers of `model_files` | `cpos.py:555`; `markdown_delivery.py:926` |
| `cashflow_units`, `forecast_inputs`, `cashflow_of` (its `units` entry), `read_cashflow` | `store.py:1478`, `:1872`, `:2748` (`:2827`), `:2855` |
| the caption | `views.js:939` |
| `BASE`, `printed`, `PATHS`, `forecast_block`, `forecast_run` | `tests/test_cpos_launch.py:2439`, `:2453`, `:2459`, `:2475`, `:2570` |
| `layer1_block`, `_operand`, `_cp1_doc`, `TWO_YEARS`, `test_a_cp2g_operand_names_no_row_or_period`, `cp2g_check` | `tests/test_cpos_launch.py:2658`, `:2666`, `:2670`, `:2687`, `:2848`, `:3481` |
| `CP1`, `BASE`, `OPERANDS`, `TABLES`, `cell`, `_md`, `_hist`, `NAMED` | `tests/test_cpos_periods.py:87`, `:107`, `:119`, `:120`, `:302`, `:932`, `:937`, `:941` |
| `test_a_block_without_facilities_is_byte_identical_to_main`, `test_refusals` | `tests/test_cpos_facilities.py:451`, `:291` |
| `HISTORY`, `REFERENCE`, `FILES` | `tests/test_credit_os_store.py:1336`, `:1356`, `:1377` |

### Answer keys (hand-computed; do not edit)

**AK-1, millions with named rows.** Fixture `CP1`, `BASE` and `NAMED` of `tests/test_cpos_periods.py` (every operand named at its row, period `FY2024`). History: the period-columns plan's answer key table, unchanged (for example LTM revenue 1000 + 780 - 720 = 1060; LTM cash proxy 211). Forecast first year from `BASE` and `PATHS` of `tests/test_cpos_launch.py` (growth 0.05, margin 0.30, capex 0.04, taxes and working capital 0.10, rate 0.06, dividends 20, repayment 50; opening debt 600, cash 100, undrawn 50):

| Line | Arithmetic | Value |
| --- | --- | ---: |
| revenue | 1000 x 1.05 | 1050 |
| ebitda | 1050 x 0.30 | 315 |
| interest | 600 x 0.06 | 36 |
| tax_wc | 1050 x 0.10 | 105 |
| capex | 1050 x 0.04 | 42 |
| cfo | 315 - 36 - 105 | 174 |
| fcf | 174 - 42 | 132 |
| closing_debt | 600 - 50 | 550 |
| closing_cash | 100 + 132 - 20 - 50 | 162 |
| net_debt | 550 - 162 | 388 |
| liquidity | 162 + 50 | 212 |

Ratios: total leverage 550/315, coverage 315/36 = 8.75, cash proxy to debt 132/550 = 0.24. Downside (EBITDA x 0.8, interest x 1.1): ebitda 252, interest 39.6, fcf 252 - 39.6 - 105 - 42 = 65.4, closing cash 100 + 65.4 - 70 = 95.4.

**AK-2, the residual.** `CP1` with the cash-flow table's header `FY2024` written `Year ended 2024-12-31`, plus a table `| Income statement | FY2024 | FY2023 |` with the row `| Interest expense | (36) | (31) |`. CP-1 prints no cash interest for FY2023 (31 is the accrual expense). Expected: no column publishes interest from the unnamed block; with interest, taxes, wc, capex and fcf named under `Year ended 2024-12-31`, FY2023 interest is `n.a.` with `CP-1 prints the base amount only under a column header that is not a period (Year ended 2024-12-31)`, and FY2023 revenue is 940.

**AK-3, thousands, every cell of `CP1` times 1,000 (`CP1_K`).** The third table is printed without separators.

```
| Reported label | Q3 2025 | Q3 2024 revised | 9M 2025 | 9M 2024 | FY2024 | FY2023 | Locator |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Net sales | 270,000 | 250,000 | 780,000 | 720,000 | 1,000,000 | 940,000 | p.2 |
| Adjusted EBITDA | 84,000 | 75,000 | 240,000 | 216,000 | 300,000 | 276,000 | p.9 |

| Reported label | 9M 2025 | 9M 2024 | FY2024 | Locator |
| --- | --- | --- | --- | --- |
| Cash paid for interest | (27,000) | (28,000) | (36,000) | p.4 |
| Income taxes paid | (15,000) | (14,000) | (20,000) | p.4 |
| Change in working capital | (12,000) | (9,000) | (10,000) | p.4 |
| Capital expenditures | (33,000) | (29,000) | (40,000) | p.4 |
| Free cash flow | 153,000 | 136,000 | 194,000 | p.4 |

| Metric | FY2024 | 9M 2025 | 9M 2024 |
| --- | --- | --- | --- |
| Total debt | 600000 | 590000 | 620000 |
| Cash and cash equivalents | 100000 | 120000 | 90000 |
| Undrawn revolver | 50000 | 50000 | 50000 |
```

Block: `scale` 1000, base amounts `BASE` times 1,000 (`"1000000"`, `"300000"`, ...), named as `NAMED`, drivers as `PATHS` with dividends `"20000"` and debt_repayment `"50000"`. Expected: parsed amounts are `BASE` exactly; dividends `("20", "20", "20")`, repayment `("50", "50", "50")`; the first forecast year, the downside figures and every history value are AK-1's; `base`, `reference_drivers`, `outputs` of `forecast_exact.json` and the whole `history` record equal the millions fixture's.

**AK-4, thousands, realistic (`CP1_K2`).**

```
| Reported label | H1 2025 | H1 2024 | FY2024 | Locator |
| --- | --- | --- | --- | --- |
| Total revenue | 1,421,519 | 1,264,478 | 2,620,995 | p.2 |
| Adjusted EBITDA | 370,100 | 310,479 | 667,621 | p.9 |
| Cash paid for interest | (52,000) | (49,750) | (100,250) | p.4 |
| Capital expenditures | (71,500) | (60,250) | (139,750) | p.4 |

| Reported facility / accounting row | H1 2025 | FY2024 | Unit and terms / evidence |
| --- | --- | --- | --- |
| Term Loan Facility | 995,000 | 1,000,000 | US$ thousands; 6.25% |
| 6.000% Senior Secured Notes | 500,000 | 500,000 | US$ thousands; 6.00% |
| Total debt | 1,534,356 | 1,555,597 | US$ thousands |
| Cash and cash equivalents | 175,509.5 | 10,879 | US$ thousands |
| Revolver availability | 618.5 | Not supplied | US$ million |

### Chart data: liquidity

| Period | Cash | Undrawn committed facilities | Reporting unit | Basis and limitation |
| --- | --- | --- | --- | --- |
| H1 2025 | 175.5095 | 618.5 | US$m | Availability after letters of credit. |
```

Block: `scale` 1000, with this base and these drivers (the same value in all three years):

```python
def _at(amount, row, period):
    return {"amount": amount, "reason": None, "row": row, "period": period}

K2_BASE = {
    "revenue": _at("2620995", "Total revenue", "FY2024"),
    "ebitda": _at("667621", "Adjusted EBITDA", "FY2024"),
    "interest": _at("100250", "Cash paid for interest", "FY2024"),
    "taxes": {"amount": None, "reason": "CP-1 states no cash taxes."},
    "wc": {"amount": None, "reason": "CP-1 states no working capital change."},
    "capex": _at("139750", "Capital expenditures", "FY2024"),
    "fcf": {"amount": None, "reason": "CP-1 states no free cash flow."},
    "debt": _at("1534356", "Total debt", "H1 2025"),
    "cash": _at("175509.5", "Cash and cash equivalents", "H1 2025"),
    "undrawn": {"amount": None, "reason": "CP-1 prints revolver availability in USD millions, not in this block's unit."},
}
K2_PATHS = {"revenue_growth": ("0.10",) * 3, "ebitda_margin": ("0.25",) * 3, "capex_pct_revenue": ("0.05",) * 3,
            "tax_wc_pct_revenue": ("0.02",) * 3, "interest_rate": ("0.065",) * 3, "dividends": ("0",) * 3,
            "debt_repayment": ("22873",) * 3}
```

| Item | Arithmetic | Value |
| --- | --- | ---: |
| parsed revenue, ebitda, interest | 2,620,995 / 1000; 667,621 / 1000; 100,250 / 1000 | 2620.995; 667.621; 100.25 |
| parsed capex, debt, cash | 139,750 / 1000; 1,534,356 / 1000; 175,509.5 / 1000 | 139.75; 1534.356; 175.5095 |
| revenue | 2620.995 x 1.10 | 2883.0945 |
| ebitda | 2883.0945 x 0.25 | 720.773625 |
| interest | 1534.356 x 0.065 | 99.73314 |
| tax_wc | 2883.0945 x 0.02 | 57.66189 |
| capex | 2883.0945 x 0.05 | 144.154725 |
| cfo | 720.773625 - 99.73314 - 57.66189 | 563.378595 |
| fcf | 563.378595 - 144.154725 | 419.22387 |
| closing_debt | 1534.356 - 22.873 | 1511.483 |
| closing_cash | 175.5095 + 419.22387 - 0 - 22.873 | 571.86037 |
| net_debt | 1511.483 - 571.86037 | 939.62263 |
| liquidity | undrawn is missing | n.a., undrawn's reason |

Total leverage 1511.483 / 720.773625 = 12091864/5766189. Downside: ebitda 576.6189, interest 109.706454, fcf 576.6189 - 109.706454 - 57.66189 - 144.154725 = 265.095831, closing cash 175.5095 + 265.095831 - 22.873 = 417.732331.

History, anchor H1 2025 (N = 2025, k = 2), all divided by 1,000:

| Key | YTD | PYTD | FY2024 | LTM = FY + YTD - PYTD |
| --- | ---: | ---: | ---: | ---: |
| revenue | 1421.519 | 1264.478 | 2620.995 | 2778.036 |
| ebitda | 370.1 | 310.479 | 667.621 | 727.242 |
| interest | 52 | 49.75 | 100.25 | 102.5 |
| capex | 71.5 | 60.25 | 139.75 | 151 |

YTD closing cash 175.5095; FY2024 closing debt 1555.597; LTM total leverage 1534.356 / 727.242 (scale-free: 1,534,356 / 727,242).

**AK-5, facilities on `CP1_K2`.**

```python
def _fixed(name, balance, rate, amortisation):
    return {"name": name, "balance": balance, "fixed_rate_pct": rate, "spread_pct": None, "floor_pct": None,
            "reference_rate": None, "annual_amortisation": amortisation, "maturity": None}

FAC = [_fixed("Term Loan Facility", "995000", "6.25", "10000"), _fixed("Notes", "500000", "6.00", None)]
```

Divided: 995, 500, amortisation 10; total 1495; unallocated 1534.356 - 1495 = 39.356. First-year interest 995 x 0.0625 + 500 x 0.06 + 39.356 x 0.065 = 62.1875 + 30 + 2.55814 = 94.74564; repayment 10. Limit: 1.25 x 1534.356 = 1917.945. With the term loan's balance stated `"1534356"`: total 2034.356, refused.

**AK-6, exact messages.**

| Input | Message |
| --- | --- |
| named CP-2G, amount 900 at `revenue`, `FY2025` (cell `1,000`) | ``CP-2G: base revenue 900 is not CP-1's cell at row `revenue`, period `FY2025` (1,000)`` |
| named CP-2G, taxes and capex unnamed | ``CP-2G: base taxes must name the `row` label and `period` header it was read from`` |
| operand without an amount names a row | `CP-2G: base revenue states no amount, so it names no row or period` |
| scale 1000, cash `"175.5095"` | `CP-2G: base cash 175.5095 is not an amount in thousands as CP-1 prints it (scale 1000): at most nine digits and one decimal place, no separators` |
| `scale` of `"1000"`, 100, 0, -1000, a list or an object | ``CP-2G: `scale` must be 1 (CP-1 prints USD millions) or 1000 (USD thousands)`` |
| scale 1000, undrawn `"618.5"` named `H1 2025`, `Undrawn committed facilities` | ``CP-2G: base undrawn: row `H1 2025` states its Reporting unit as `US$m`, not the block's unit (USD thousands, scale 1000); state a reason instead of an amount`` |
| AK-5's refused balances | `CP-2G: facility balances total 2034.356, more than 1.25 times base debt 1534.356, in USD millions after dividing by scale 1000; check the unit` |

---

## PR A: CP-2G names the row and period of each base operand

### Task A1: A CP-2G block may name its cells

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_forecast.py` (`parse` :315-322; the docstrings of `Operand` :45 and `_layer1_problem` :243 say both sources)
- Test: `tests/test_cpos_launch.py` (replace `test_a_cp2g_operand_names_no_row_or_period` :2848; add the tests below after it)

**Interfaces:**
- Consumes: `_layer1_problem`, `_printed` (unchanged).
- Produces: `parse(source_text, cp1_text, "CP-2G")` accepts `row` and `period` on base operands. Named means any operand states either. A named block: each operand through `_layer1_problem`, the error prefixed `CP-2G: `. A block naming none: as today.

- [ ] **Step 1: Write the failing tests**

```python
def _named_cp2g(doc: str, **operands):
    """A CP-2G block that names each operand's cell, parsed against the CP-1 document."""
    base = {k: _operand(v, k) for k, v in BASE.items()} | operands
    return cpos_forecast.parse(forecast_block(base=base), doc.replace("__BLOCK__", ""))

def test_a_cp2g_block_may_name_the_row_and_period_of_every_base_operand():
    inputs = _named_cp2g(_cp1_doc(TWO_YEARS))
    assert (inputs.base["revenue"].row, inputs.base["revenue"].period) == ("revenue", "FY2025")
    assert inputs.downside_shock is not None  # still CP-2G's block: the shock and cases stay

MUST_NAME = "CP-2G: base revenue must name the `row` label and `period` header it was read from"

@pytest.mark.parametrize(("operand", "complaint"), [
    (_operand("900"), "CP-2G: base revenue 900 is not CP-1's cell at row `revenue`, period `FY2025` (1,000)"),
    (_operand("1000", "Revenue"), "CP-2G: base revenue: no table cell of CP-1 is at row `Revenue`, period `FY2025`"),
    (_operand("1000", period="FY2023"), "CP-2G: base revenue: no table cell of CP-1 is at row `revenue`, period `FY2023`"),
    ({"amount": "1000", "reason": None}, MUST_NAME),
    ({"amount": "1000", "reason": None, "row": "revenue"}, MUST_NAME),
    ({"amount": None, "reason": "unknown", "row": "revenue", "period": "FY2025"},
     "CP-2G: base revenue states no amount, so it names no row or period"),
])
def test_a_named_cp2g_operand_that_is_not_its_cell_is_refused(operand, complaint):
    with pytest.raises(ValueError) as caught:
        _named_cp2g(_cp1_doc(TWO_YEARS), revenue=operand)
    assert str(caught.value) == complaint

def test_a_cp2g_block_naming_some_operands_is_refused_at_the_first_one_missing():
    unnamed = {key: {"amount": BASE[key], "reason": None} for key in ("taxes", "capex")}
    with pytest.raises(ValueError) as caught:
        _named_cp2g(_cp1_doc(TWO_YEARS), **unnamed)
    assert str(caught.value) == "CP-2G: base taxes must name the `row` label and `period` header it was read from"

def test_a_named_cp2g_amount_printed_only_in_prose_is_refused():
    doc = _cp1_doc("", head="Basis: revenue 1,234 per annual report\n\n").replace("__BLOCK__", "")
    unnamed = {k: {"amount": v, "reason": None} for k, v in BASE.items()}
    unnamed["revenue"] = {"amount": "1234", "reason": None}
    assert cpos_forecast.parse(forecast_block(base=unnamed), doc)  # printed somewhere: as before
    with pytest.raises(ValueError, match="CP-2G: base revenue: no table cell of CP-1"):
        _named_cp2g(doc, revenue=_operand("1234"))

def test_a_named_cp2g_operand_that_is_not_its_cell_is_sent_back_for_repair():
    cp1 = "| Base | FY2025 |\n| --- | --- |\n" + "\n".join(f"| {k} | {printed(k, v)} |" for k, v in BASE.items())
    task = types.SimpleNamespace(module_id="CP-2G", handoffs={"CP-1": cp1.encode()})
    base = {k: _operand(v, k) for k, v in BASE.items()}
    assert cpos_launch._forecast_issues(task, forecast_block(base=base)) == ()
    base["capex"] = _operand("40", "Capex")
    (issue,) = cpos_launch._forecast_issues(task, forecast_block(base=base))
    assert issue == (
        "Forecast inputs: CP-2G: base capex: no table cell of CP-1 is at row `Capex`, period "
        "`FY2025`. Correct the block; if you cannot, set every driver's values to "
        "[null, null, null] and say why in scope_limits.")
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_launch.py -q -k "named_cp2g or may_name_the_row or naming_some"` — expected: all fail (`only CP-1 does`).
- [ ] **Step 3: Implement.** In `parse`, compute `named = source == "CP-1" or any(o.row is not None or o.period is not None for o in inputs.base.values())`; a named block runs `_layer1_problem` per operand, else the `_printed` check. Delete the `only CP-1 does` refusal. No change to `model_files` yet.
- [ ] **Step 4: Run** the same command, then `uv run pytest tests/test_cpos_launch.py tests/test_cpos_facilities.py -q -k "forecast or layer1 or cp2g or facilit or block"` — expected: all pass, the byte-identical pin included.
- [ ] **Step 5: Commit** `feat(forecast): a CP-2G block may name the row and period of each base operand`

### Task A2: History from named rows only; delete the amount location

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_forecast.py` (`model_files` :563-571: `named` for either source, an empty mapping when nothing is named)
- Modify: `src/deploy_workflow/owners/cpos_periods.py` (deletions and changes listed in the Design)
- Test: `tests/test_cpos_periods.py`

**Interfaces:**
- Produces:
  - `NOT_NAMED = "the forecast inputs do not name the row and period of this line"`.
  - `lines(tables, operands, *, named=None)` and `history(tables, operands, *, named=None, forecast_year=None)`: `named` None is an empty mapping. An operand with an amount and no entry: `Line(reason=NOT_NAMED)`.
  - `_locate(tables, operands, named) -> tuple[dict[str, Line], Period | None]`, the base period from `_named_base(named)`.
  - `_hits(tables, key, amount, label: str)`, `_line(tables, key, amount, label: str, target)`: no rows under the target gives `Line(reason=NOT_A_CELL)`.
  - `_limits` lists unread headers of located lines only.
- Removed: everything under "Deleted" in the Design.

- [ ] **Step 0: Before any edit, run the reviewer's probe** and record its output and exit code: `PYTHONPATH=src:.:tests uv run python .superpowers/sdd/2026-11-12-forecast-period-columns/probes/adv2_right_row_unheaded.py` — expected: prints `FY2023 interest: 31`, exit 1. The folder is git-ignored and local to the worktree the period-columns work ran in; if it is absent, say so and go on (Step 4's first test states the same key).
- [ ] **Step 1: Change the test file's set-up.** Drop `NO_BASE_PERIOD`, `NOT_IDENTIFIED`, `NOT_IN_BASE_PERIOD`, `history` and `lines` from the `cpos_periods` import; add `NOT_NAMED` and `NOT_UNDER_A_PERIOD`; import the module (`from deploy_workflow.owners import cp2g, cpos_forecast, cpos_periods`). Move `NAMED` (:941-952) to just after `TABLES` (:120) and add:

```python
def lines(tables, operands, *, named=NAMED):
    """The lines with the fixture's rows named, as a block that names them has them read."""
    return cpos_periods.lines(tables, operands, named=named)

def history(tables, operands, *, named=NAMED, **kwargs):
    return cpos_periods.history(tables, operands, named=named, **kwargs)

def named_block(**changes):
    base = {k: {"amount": v, "reason": None, "row": NAMED[k][0], "period": NAMED[k][1]} for k, v in BASE.items()}
    return forecast_block(base=base, **changes)
```

- [ ] **Step 2: Delete the thirteen tests that pinned the amount location:** `test_a_second_row_with_the_base_amount_leaves_the_line_unidentified`, `test_the_same_line_in_two_tables_is_one_line_when_they_agree`, `test_two_labels_that_disagree_in_a_shared_period_are_not_identified`, `test_a_match_under_a_header_that_is_not_a_period_does_not_anchor_a_row`, `test_a_base_amount_printed_only_under_a_date_header_has_no_history`, `test_a_row_printing_the_amount_in_another_period_is_not_the_line`, `test_two_labels_sharing_only_the_base_period_are_not_one_line`, `test_revenue_and_ebitda_printed_in_two_periods_leave_no_base_period`, `test_an_amount_printed_only_under_other_periods_names_them`, `test_the_periods_named_are_ascending_and_at_most_five`, `test_layer_one_names_read_the_same_values_as_the_cp2g_path` (now the same as `test_each_base_line_is_read_in_every_period_cp1_prints`), `test_revenue_printed_under_no_period_leaves_no_base_period_and_names_the_header`, `test_a_different_label_printed_for_the_base_period_alone_leaves_the_line_unidentified`.

- [ ] **Step 3: Change these tests, and only as stated.** Every other test keeps its body and passes through the named default.

| Test | Change |
| --- | --- |
| `test_no_base_line_under_a_period_header_gives_every_column_its_reason` | call with `named=None`; revenue's reason is `NOT_NAMED` |
| `test_model_files_publishes_the_history_record`, `test_a_cell_too_long_to_read_exactly_does_not_end_the_forecast` | `named_block()` in place of `forecast_block()` |
| `test_a_figure_of_39_digits_is_not_a_figure` | `named = {**NAMED, key: ("Other", "9M 2025")}` passed to both calls; `line.values == {} and line.reason == NOT_A_CELL` for every key |
| `test_an_ltm_that_cannot_be_built_is_not_called_checked` | `named={"revenue": ("Net sales", "9M 2025")}` |
| `test_an_accrual_row_does_not_supply_another_periods_cash_interest` | FY2023 interest equals `{"amount": None, "reason": "CP-1 does not print this line for FY2023"}`; `_read(cp1, "interest").reason is None` |
| `test_an_ltm_base_amount_gives_the_interest_line_no_history` | interest named `("Cash paid for interest", "LTM Q3 2025")`; `interest.values == {}` and `interest.reason == NOT_UNDER_A_PERIOD.format(header="LTM Q3 2025")` |
| `test_a_header_quoted_in_a_reason_is_cut_to_80_characters` | debt named `("Total debt", "x" * 200 + " 2024")`; same expected reason |
| `test_the_forecast_year_never_drops_the_base_period` | keep the first three assertions; delete the second fixture (the layer-one guard test below it covers a named FY2025 base) |
| `test_a_weeks_tail_is_not_read_on_a_fiscal_year_header` | every operand named under `stub = "FY2024: thirty-nine weeks ended 2024-09-28"`; `"FY2024"` is no column id; LTM revenue equals `{"amount": None, "reason": NOT_UNDER_A_PERIOD.format(header=stub)}` |
| `test_an_ebitda_cell_of_a_million_digits_is_not_a_figure_and_nothing_raises` | the added row's label is `Adjusted EBITDA`; FY2022 ebitda equals `{"amount": None, "reason": "CP-1 does not print this line for FY2022"}`, FY2022 closing debt is 600; `named_block()` |
| `test_a_30_kb_handoff_of_the_reason_amplification_shape_gives_a_small_record` | `named = {"revenue": ("Net sales", "Q4 2024"), "ebitda": ("Adjusted EBITDA", "x" * 26_000 + " 2025")}`; twelve quarter columns; record under 1,000,000 characters |

- [ ] **Step 4: Write the new failing tests**

```python
RESIDUAL_HEAD = "| Reported label | 9M 2025 | 9M 2024 | FY2024 | Locator |"
RESIDUAL = CP1.replace(RESIDUAL_HEAD, "| Reported label | 9M 2025 | 9M 2024 | Year ended 2024-12-31 | Locator |") + (
    "\n" + _md(["Income statement", "FY2024", "FY2023"], [["Interest expense", "(36)", "(31)"]]))
UNHEADED = ("interest", "taxes", "wc", "capex", "fcf")

def test_a_cp2g_block_on_the_residuals_handoff_publishes_no_other_rows_interest():   # AK-2
    unnamed = model_files(RESIDUAL.encode(), forecast_block().encode(), history=True)
    record = json.loads(unnamed["calculation.json"])["history"]
    assert all(c["values"]["interest"]["amount"] is None for c in record["columns"])
    base = {k: {"amount": v, "reason": None, "row": NAMED[k][0],
                "period": "Year ended 2024-12-31" if k in UNHEADED else "FY2024"} for k, v in BASE.items()}
    files = model_files(RESIDUAL.encode(), forecast_block(base=base).encode(), history=True)
    record = json.loads(files["calculation.json"])["history"]
    assert cell(record, "FY2023", "interest") == {"amount": None, "reason":
        "CP-1 prints the base amount only under a column header that is not a period (Year ended 2024-12-31)"}
    assert D(cell(record, "FY2023", "revenue")["amount"]) == D(940)

def test_unnamed_operands_have_no_history_and_one_reason():
    found = lines(TABLES, OPERANDS, named=None)
    assert all(line.reason == NOT_NAMED and not line.values for line in found.values())
    record = history(TABLES, OPERANDS, named=None)
    assert [c["id"] for c in record["columns"]] == ["Quarter", "YTD", "PYTD", "Fiscal year", "LTM", "PRIOR_LTM", "PF"]
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason": NOT_NAMED}
    assert cell(record, "LTM", "fcf") == {"amount": None, "reason": NO_ANCHOR}
    assert record["limits"][0] == NOT_BUILT and f"revenue: {NOT_NAMED}" in record["limits"]

def test_an_operand_with_an_amount_and_no_name_is_the_only_line_without_history():
    found = lines(TABLES, OPERANDS, named={k: v for k, v in NAMED.items() if k != "capex"})
    assert found["capex"].reason == NOT_NAMED and found["capex"].values == {}
    assert found["revenue"].reason is None and found["interest"].reason is None

def test_named_periods_may_differ_between_operands():
    ops = replace(OPERANDS, debt=cp2g.Val(D(590), None), cash=cp2g.Val(D(120), None))
    named = {**NAMED, "debt": ("Total debt", "9M 2025"), "cash": ("Cash and cash equivalents", "9M 2025")}
    record = _hist(CP1, ops, named=named, forecast_year=2025)
    assert D(cell(record, "LTM", "closing_debt")["amount"]) == D(590)
    assert D(cell(record, "FY2024", "closing_debt")["amount"]) == D(600)
    assert D(cell(record, "LTM", "revenue")["amount"]) == D(1060)

def test_a_named_row_in_two_tables_with_another_figure_for_the_named_period():   # Review Focus 3
    cp1 = CP1 + "\n" + _md(["Restated", "FY2024 revised", "FY2023"], [["Net sales", "1,010", "950"]])
    revenue = _read(cp1, "revenue")
    assert revenue.reason is None
    assert revenue.values[("FY", 2024, 4)] == D(1000) and revenue.values[("FY", 2023, 4)] == D(940)
    same = CP1 + "\n" + _md(["Restated", "FY2024", "FY2023"], [["Net sales", "1,010", "950"]])
    with pytest.raises(ValueError, match="is not one number in CP-1"):
        model_files(same.encode(), named_block().encode(), history=True)

def test_model_files_reads_a_named_cp2g_block_through_its_rows():   # AK-1
    files = model_files(CP1.encode(), named_block().encode(), history=True)
    record = json.loads(files["calculation.json"])["history"]
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1060")
    assert D(cell(record, "LTM", "fcf")["amount"]) == D("211")
    unnamed = model_files(CP1.encode(), forecast_block().encode(), history=True)
    assert json.loads(unnamed["forecast_exact.json"])["outputs"] == json.loads(files["forecast_exact.json"])["outputs"]
    record = json.loads(unnamed["calculation.json"])["history"]
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason": NOT_NAMED}
    assert all(v["amount"] is None and v["reason"] for c in record["columns"] for v in c["values"].values())
```

- [ ] **Step 5: Run** `uv run pytest tests/test_cpos_periods.py -q` — expected: an import error until `NOT_NAMED` exists; add the constant alone and run again: the first new test fails on its first assertion (`31` is published) and the changed and other new tests fail.
- [ ] **Step 6: Implement** per Interfaces and the Design's deletion list. Nothing is located by amount across labels after this step.
- [ ] **Step 7: Run** `uv run pytest tests/test_cpos_periods.py tests/test_cpos_facilities.py -q` and `uv run pytest tests/test_cpos_launch.py -q -k "forecast or layer1 or library or cp2g"` — expected: all pass. The probe of Step 0 no longer applies (its unnamed call has no `FY2023` column and stops with `StopIteration`); say so in the report, do not edit it.
- [ ] **Step 8: Commit** `feat(forecast): history from named rows only; remove the amount location`

### Task A3: The CP-2G instruction asks for the row and period

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_launch.py` (`FORECAST_BLOCK`, the `base` sentence, :1525-1528 here, :1541-1544 at `origin/main`)
- Test: `tests/test_cpos_launch.py` (next to `test_the_forecast_instructions_ask_for_the_cases_as_driver_overrides`, :3211)

- [ ] **Step 1: Write the failing test**

```python
def test_the_cp2g_instruction_asks_for_the_row_and_period_of_every_base_operand():
    block = cpos_launch.FORECAST_BLOCK
    for words in ('"row": "<label>", "period": "<header>"', "exact first-cell text", "exact header text",
                  "of one of the CP-1 handoff's tables", "Name both for every operand that has an amount",
                  "positive magnitude", "with its sign reversed", "is not a cell",
                  "`FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`"):
        assert words in block, words
    assert "copied exactly as CP-1 prints it (outflows as positive magnitudes)" not in block
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_launch.py -q -k row_and_period_of_every` — expected: fails.
- [ ] **Step 3: Replace the `base` sentence** (from `` `base` holds `` up to the operand list's full stop) with this exact copy, the operand list still built from `cp2g.OPERAND_METRIC`:

> `base` holds exactly these ten operands in USD millions, each `{"amount": "<decimal>", "reason": null, "row": "<label>", "period": "<header>"}` or `{"amount": null, "reason": "<why CP-1 does not state it>"}`: revenue, ebitda, interest, taxes, wc, capex, fcf, debt, cash, undrawn. `row` is the exact first-cell text of the row of one of the CP-1 handoff's tables that you read the amount from, and `period` the exact header text of that table's column (for example `"row": "Net sales", "period": "FY2024"`). Name both for every operand that has an amount. Copy the amount as that cell prints it, in millions; for interest, taxes and capex write the positive magnitude whatever sign the cell shows; for working capital write the cell's value with its sign reversed (a cell printing (45), an investment, is 45; a cell printing 45 or +45, a release, is -45). A figure in CP-1's prose, a basis line or its sources is not a cell: an amount CP-1 prints in no table cell is stated as missing, with the reason. Where CP-1 prints the amount under more than one column, name a column headed by a reporting period (`FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`): the Forecast page shows history only for a line named under such a header.

- [ ] **Step 4: Run** `uv run pytest tests/test_cpos_launch.py -q -k "instruction or forecast"` — expected: all pass.
- [ ] **Step 5: Commit** `feat(cp2g): ask CP-2G for the row and period of each base operand`

### Task A4: End to end, record, gates

**Files:**
- Test: `tests/test_cpos_launch.py`
- Modify: `VERIFICATION.md`

- [ ] **Step 1: Write the end-to-end test** (canned provider; the CP-1 answer prints `| Base | FY2025 |`):

```python
def test_a_cp2g_block_that_names_its_rows_publishes_their_history(tmp_path, provider, capsys):
    base = {k: _operand(v, k) for k, v in BASE.items()}
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block(base=base))
    assert code == 0, seen.err
    assert "Model not published" not in seen.err
    (folder,) = (out / "deliveries").iterdir()
    record = json.loads((folder / "calculation.json").read_text())["history"]
    column = next(c for c in record["columns"] if c["id"] == "FY2025")
    assert column["values"]["revenue"] == {"amount": "1000", "reason": None}
    assert column["values"]["tax_wc"] == {"amount": "30", "reason": None}   # 20 + 10
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_launch.py -q -k names_its_rows` — expected: passes (Tasks A1 and A2 built it); a failure is a defect in them.
- [ ] **Step 3: Retained check (offline, read only; a one-off `uv run python -c`, nothing written there).** On `/private/tmp/claude-501/rbot-live3/runs/tdg-forecast-002/deliveries/*/CP-1.md` and `CP-2G.md`: (a) `parse` as delivered — expected: `CP-2G: the handoff gives no forecast drivers, so no forecast was computed`, as at delivery; (b) the block's base amounts with these names and the synthetic `PATHS` drivers through `model_files(..., history=True)`:

| Operand | `row` | `period` |
| --- | --- | --- |
| revenue 7940 | `NET SALES` | `FY2024` |
| ebitda 3813 | `EBITDA` | `FY2024` |
| interest 1158 | `Cash paid during the period for interest, net` | `FY2024` |
| taxes 539 | `Cash paid during the period for income taxes, net of refunds` | `FY2024` |
| capex 165 | `Capital expenditures` | `FY2024` |
| cash 6261 | `CASH AND CASH EQUIVALENTS, END OF PERIOD` | `FY2024` |
| fcf 1880 | `FCF before acquisitions and shareholder distributions` | `FY2024 / September 30, 2024` |
| debt 24880 | `Carrying financial debt` | `FY2024 / September 30, 2024` |
| undrawn 843 | `Available revolving credit` | `FY2024 / September 30, 2024` |

  Expected: accepted; the `FY2024` column reads revenue 7940, ebitda 3813, interest 1158, capex 165, closing cash 6261; closing debt and undrawn are `n.a.` with `CP-1 prints the base amount only under a column header that is not a period (FY2024 / September 30, 2024)`; `tax_wc` is `n.a.` with the block's working-capital reason. Scope to record: a hand-written block over a real CP-1 with synthetic drivers; it proves the cell check and the history on real printed tables, not a model's ability to name rows. If the folder is gone, record that.
- [ ] **Step 4: Run** `uv run python tools/quality_gate.py` — expected: exit 0. Then the PR check's pytest command from `.github/workflows/checks.yml` — expected: exit 0.
- [ ] **Step 5: Record in `VERIFICATION.md`** one entry, scope stated exactly: "offline; synthetic fixtures with hand-computed answer keys; the reviewer's residual probe run before the change (exit 1); one retained live forecast run's CP-1 read with a hand-named block and synthetic drivers; no retained delivery holds model files, so byte-identical re-derivation is proven on the synthetic pin only; no provider called and no model response: no CP-2G has yet named a row. A CP-2G block that names no row publishes a forecast with no history." Commands and exit codes. Trim the oldest entries to stay under 1,000 lines.
- [ ] **Step 6: Commit** `test(forecast): a named CP-2G run end to end; record`

---

## PR B: units

### Task B1: `scale` at the door of `parse`

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_forecast.py`
- Create: `tests/test_cpos_scale.py`; add it to `.github/workflows/checks.yml:42`

**Interfaces:**
- Produces:
  - `ForecastInputs.scale: Literal[1, 1000] | None = None`.
  - `def _slots(document: dict[str, Any]) -> Iterator[tuple[str, Any, Any]]`: `(name, holder, key)` of every amount slot of the Design's table, wherever the document's shape allows one; names as in that table.
  - `def _to_millions(document: dict[str, Any], source: str) -> dict[str, str]`: a `scale` that is present, not null and not equal to 1 or 1000 raises AK-6's message. At 1000: each slot holding text must fully match `-?[0-9]{1,9}(\.[0-9])?` (else AK-6's message, the text cut at 40 characters) and is replaced by `format(cp2g._exact(Decimal(text).scaleb(-3)), "f")`; returns the stated text by name. Otherwise returns `{}` and changes nothing. A slot that is not text is left for the schema.
  - `parse` calls it after `_declined` and before validation. The operand loop reads `amount = stated.get(f"base {key}", operand.amount)` for `_printed` and for `_layer1_problem(text, key, operand, amount)` (new fourth argument: the amount as stated, used wherever it reads `operand.amount` today).
  - `_check_facilities(inputs, facilities, cp1_text, stated)`: the printed check and its message use `stated.get(f"facility {i} balance", facility.balance)`, `i` from 1. At scale 1000 the 1.25 times and repayment messages gain `, in USD millions after dividing by scale 1000` after the debt figure; at scale 1 they are unchanged.
- The returned `ForecastInputs` holds USD millions everywhere.
- Keep `parse` inside the quality gate's complexity limit: move the operand loop out if needed.

- [ ] **Step 1: Write the failing tests.** `tests/test_cpos_scale.py` holds `CP1_K`, `CP1_K2`, `K2_BASE`, `K2_PATHS` and `FAC` (AK-3, AK-4, AK-5, literal), and:

```python
import json, re
from decimal import Decimal
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st
from test_cpos_launch import PATHS, forecast_block
from test_cpos_periods import BASE, CP1, NAMED, OPERANDS, cell

from deploy_workflow.owners import cpos_forecast, cpos_periods
from deploy_workflow.owners.cpos_forecast import model_files, parse   # Task B2 adds SCALE_LIMIT

K = {k: str(int(v) * 1000) for k, v in BASE.items()}
K_PATHS = {**PATHS, "dividends": ("20000",) * 3, "debt_repayment": ("50000",) * 3}

def drivers(paths):
    return {n: {"values": list(v), "category": "Analyst Interpretation", "rationale": "Synthetic.", "limitation": None}
            for n, v in paths.items()}

def named_base(amounts):
    return {k: {"amount": v, "reason": None, "row": NAMED[k][0], "period": NAMED[k][1]} for k, v in amounts.items()}

def block_k(**changes):
    return forecast_block(**{"scale": 1000, "base": named_base(K), "base_drivers": drivers(K_PATHS), **changes})

def block_m(**changes):
    return forecast_block(**{"base": named_base(BASE), **changes})

def block_k2(**changes):
    return forecast_block(**{"scale": 1000, "base": K2_BASE, "base_drivers": drivers(K2_PATHS), **changes})

def test_scale_1000_states_thousands_and_parses_to_millions():   # AK-3
    inputs = parse(block_k(), CP1_K)
    assert {k: o.amount for k, o in inputs.base.items()} == BASE
    assert inputs.base_drivers.dividends.values == ("20", "20", "20")
    assert inputs.base_drivers.debt_repayment.values == ("50", "50", "50")
    assert inputs.scale == 1000

def test_a_decimal_and_a_bracketed_thousands_cell_parse_exactly():   # Review Focus 1, 2; AK-4
    base = parse(block_k2(), CP1_K2).base
    assert {k: o.amount for k, o in base.items() if o.amount} == {"revenue": "2620.995", "ebitda": "667.621",
        "interest": "100.25", "capex": "139.75", "debt": "1534.356", "cash": "175.5095"}

@pytest.mark.parametrize("operand, message", [   # AK-6
    ({"cash": {**K2_BASE["cash"], "amount": "175.5095"}}, "CP-2G: base cash 175.5095 is not an amount in thousands as CP-1 "
     "prints it (scale 1000): at most nine digits and one decimal place, no separators"),
    ({"cash": {**K2_BASE["cash"], "amount": "175509.55"}}, "CP-2G: base cash 175509.55 is not an amount in thousands"),
    ({"revenue": {**K2_BASE["revenue"], "amount": "2,620,995"}}, "CP-2G: base revenue 2,620,995 is not an amount in thousands"),
    ({"revenue": {**K2_BASE["revenue"], "amount": "1234567890"}}, "CP-2G: base revenue 1234567890 is not an amount in thousands"),
    ({"revenue": {**K2_BASE["revenue"], "amount": "2621"}},
     "CP-2G: base revenue 2621 is not CP-1's cell at row `Total revenue`, period `FY2024` (2,620,995)"),
])
def test_refusals_at_scale_1000(operand, message):
    with pytest.raises(ValueError) as caught:
        parse(block_k2(base={**K2_BASE, **operand}), CP1_K2)
    assert message in str(caught.value)

@pytest.mark.parametrize("scale", ["1000", 100, 0, -1000, [1000], {"x": 1}])
def test_a_scale_that_is_not_1_or_1000_is_refused(scale):
    with pytest.raises(ValueError) as caught:
        parse(block_k(scale=scale), CP1_K)
    assert str(caught.value) == "CP-2G: `scale` must be 1 (CP-1 prints USD millions) or 1000 (USD thousands)"

def test_a_millions_block_does_not_read_a_thousands_handoff():
    with pytest.raises(ValueError, match="CP-2G: base revenue 1000 is not CP-1's cell"):
        parse(block_m(), CP1_K)
    with pytest.raises(ValueError, match="CP-2G: base revenue 1000000 is not CP-1's cell"):
        parse(block_k(), CP1)

def test_a_block_with_scale_and_unnamed_rows():   # Review Focus 4
    base = {k: {"amount": v, "reason": None} for k, v in K.items()}
    files = model_files(CP1_K.encode(), block_k(base=base).encode(), history=True)
    assert json.loads(files["forecast_exact.json"])["outputs"]["REFERENCE"]["years"][0]["revenue"]["amount"] == "1050"
    record = json.loads(files["calculation.json"])["history"]
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason": cpos_periods.NOT_NAMED}
    with pytest.raises(ValueError, match="CP-2G: base revenue 1000000 is not printed in CP-1"):
        parse(block_k(base=base), CP1)

def test_facilities_at_scale_1000_are_divided_and_checked_against_the_divided_debt():   # Review Focus 5; AK-5
    exact = json.loads(model_files(CP1_K2.encode(), block_k2(facilities=FAC).encode())["forecast_exact.json"])
    assert [f["balance"] for f in exact["facilities"]] == ["995", "500"]
    assert exact["facilities"][0]["annual_amortisation"] == "10"
    assert exact["unallocated_debt"]["amount"] == "39.356"
    first = exact["outputs"]["REFERENCE"]["years"][0]
    assert first["interest"]["amount"] == "94.74564" and first["repayment"]["amount"] == "10"
    with pytest.raises(ValueError) as caught:
        parse(block_k2(facilities=[{**FAC[0], "balance": "1534356"}, FAC[1]]), CP1_K2)
    assert str(caught.value) == ("CP-2G: facility balances total 2034.356, more than 1.25 times base debt 1534.356, "
                                 "in USD millions after dividing by scale 1000; check the unit")
    with pytest.raises(ValueError, match="CP-2G: facility Notes balance 500 is not printed in CP-1"):
        parse(block_k2(facilities=[FAC[0], {**FAC[1], "balance": "500"}]), CP1_K2)

@given(st.from_regex(r"-?[0-9]{1,9}(\.[0-9])?", fullmatch=True))
def test_the_division_is_exact_and_fits_the_millions_pattern(text):
    document = {"scale": 1000, "base": {"revenue": {"amount": text, "reason": None}}}
    assert cpos_forecast._to_millions(document, "CP-2G") == {"base revenue": text}
    millions = document["base"]["revenue"]["amount"]
    assert Fraction(millions) * 1000 == Fraction(text)
    assert re.fullmatch(r"-?[0-9]{1,6}(\.[0-9]{1,4})?", millions)
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_scale.py -q` — expected: all fail (`scale` is an extra field; `_to_millions` not defined).
- [ ] **Step 3: Implement.** No `try` around the conversion; the two `ValueError`s are the documented refusals.
- [ ] **Step 4: Run** the same command and `uv run pytest tests/test_cpos_facilities.py tests/test_cpos_periods.py -q` and `uv run pytest tests/test_cpos_launch.py -q -k "forecast or layer1 or cp2g"` — expected: all pass; the byte-identical pin is green.
- [ ] **Step 5: Commit** `feat(forecast): an inputs block may state amounts in thousands with scale 1000`

### Task B2: Publish in millions; history in the same unit

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_forecast.py` (`model_files`: the `exact` document :535 and the history call :580)
- Modify: `src/deploy_workflow/owners/cpos_periods.py` (`lines`, `_locate`, `history`)
- Test: `tests/test_cpos_scale.py`

**Interfaces:**
- Produces:
  - `UNITS = "USD millions"`, `SCALE_LIMIT` (the Design's exact text).
  - `forecast_exact.json`: `"scale"` and `"units"` only when the block states `scale`; `SCALE_LIMIT` second in `scope_limits` only at 1000.
  - `history(tables, operands, *, named=None, forecast_year=None, scale: int = 1)` and `lines(..., scale: int = 1)`. In `_locate`, at a scale other than 1, a named line is read with `operand.amount * scale` and its values are divided by the scale, inside `localcontext(cp2g._EXACT)`; at scale 1 the code path is today's.
  - `model_files` passes `scale=inputs.scale or 1`.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_thousands_handoff_publishes_the_millions_figures():   # AK-1, AK-3
    k = model_files(CP1_K.encode(), block_k().encode(), history=True)
    m = model_files(CP1.encode(), block_m().encode(), history=True)
    exact_k, exact_m = (json.loads(f["forecast_exact.json"]) for f in (k, m))
    first = exact_k["outputs"]["REFERENCE"]["years"][0]
    key = {"revenue": "1050", "ebitda": "315", "interest": "36", "tax_wc": "105", "capex": "42", "cfo": "174",
           "fcf": "132", "closing_debt": "550", "closing_cash": "162", "net_debt": "388", "liquidity": "212",
           "dividends": "20", "repayment": "50"}
    assert {n: first[n]["amount"] for n in key} == key
    assert first["coverage"]["amount"] == "8.75" and first["fcf_to_debt"]["amount"] == "0.24"
    down = exact_k["outputs"]["DOWNSIDE"]["years"][0]
    assert [down[n]["amount"] for n in ("ebitda", "interest", "fcf", "closing_cash")] == ["252", "39.6", "65.4", "95.4"]
    for name in ("base", "reference_drivers", "outputs"):
        assert exact_k[name] == exact_m[name], name
    assert (exact_k["scale"], exact_k["units"]) == (1000, "USD millions")
    assert "scale" not in exact_m and "units" not in exact_m and SCALE_LIMIT not in exact_m["scope_limits"]
    assert exact_k["scope_limits"][:3] == [cpos_forecast.LIMIT, SCALE_LIMIT, "Synthetic; not analytical review."]
    assert json.loads(k["calculation.json"])["history"] == json.loads(m["calculation.json"])["history"]

@pytest.mark.parametrize("key, ytd, pytd, fy, ltm", [
    ("revenue", "780", "720", "1000", "1060"), ("interest", "27", "28", "36", "35"), ("tax_wc", "27", "23", "30", "34"),
    ("fcf", "153", "136", "194", "211"), ("closing_debt", "590", "620", "600", "590"), ("liquidity", "170", "140", "150", "170"),
])
def test_history_at_scale_1000_is_the_answer_key_in_millions(key, ytd, pytd, fy, ltm):
    record = cpos_periods.history(cpos_forecast._tables(CP1_K), OPERANDS, named=NAMED, scale=1000)
    assert [cell(record, c, key)["amount"] for c in ("YTD", "PYTD", "FY2024", "LTM")] == [ytd, pytd, fy, ltm]

def test_ratios_are_scale_free():
    record = cpos_periods.history(cpos_forecast._tables(CP1_K), OPERANDS, named=NAMED, scale=1000)
    assert abs(Fraction(cell(record, "LTM", "total_leverage")["amount"]) - Fraction(590, 324)) < Fraction(1, 10**12)
    assert abs(Fraction(cell(record, "LTM", "coverage")["amount"]) - Fraction(324, 35)) < Fraction(1, 10**12)

def test_the_realistic_thousands_handoff():   # AK-4
    files = model_files(CP1_K2.encode(), block_k2().encode(), history=True)
    exact = json.loads(files["forecast_exact.json"])
    first = exact["outputs"]["REFERENCE"]["years"][0]
    key = {"revenue": "2883.0945", "ebitda": "720.773625", "interest": "99.73314", "tax_wc": "57.66189",
           "capex": "144.154725", "cfo": "563.378595", "fcf": "419.22387", "closing_debt": "1511.483",
           "closing_cash": "571.86037", "net_debt": "939.62263", "repayment": "22.873"}
    assert {n: first[n]["amount"] for n in key} == key
    assert first["liquidity"] == {"amount": None, "reason": K2_BASE["undrawn"]["reason"]}
    assert abs(Fraction(first["total_leverage"]["amount"]) - Fraction(12091864, 5766189)) < Fraction(1, 10**30)
    down = exact["outputs"]["DOWNSIDE"]["years"][0]
    assert [down[n]["amount"] for n in ("ebitda", "interest", "fcf", "closing_cash")] == \
        ["576.6189", "109.706454", "265.095831", "417.732331"]
    record = json.loads(files["calculation.json"])["history"]
    for name, *want in [("revenue", "1421.519", "1264.478", "2620.995", "2778.036"), ("ebitda", "370.1", "310.479", "667.621", "727.242"),
                        ("interest", "52", "49.75", "100.25", "102.5"), ("capex", "71.5", "60.25", "139.75", "151")]:
        assert [cell(record, c, name)["amount"] for c in ("YTD", "PYTD", "FY2024", "LTM")] == want
    assert cell(record, "YTD", "closing_cash")["amount"] == "175.5095"
    assert cell(record, "FY2024", "closing_debt")["amount"] == "1555.597"
    assert abs(Fraction(cell(record, "LTM", "total_leverage")["amount"]) - Fraction(1534356, 727242)) < Fraction(1, 10**12)

def test_a_block_with_scale_one_is_the_block_without_it_plus_the_units():
    stated = json.loads(model_files(CP1.encode(), block_m(scale=1).encode())["forecast_exact.json"])
    absent = json.loads(model_files(CP1.encode(), block_m().encode())["forecast_exact.json"])
    assert (stated.pop("scale"), stated.pop("units")) == (1, "USD millions")
    stated["consumed"] = absent["consumed"]   # the handoff's hash differs by the one key
    assert stated == absent

def test_layer_one_at_scale_1000():
    block = json.loads(block_k().split("```json\n")[1].split("\n```")[0])
    block["downside_shock"] = None
    text = CP1_K + "\n### Forecast inputs (machine-readable)\n\n```json\n" + json.dumps(block) + "\n```\n"
    files = model_files(text.encode(), text.encode(), "CP-1", history=True)
    exact = json.loads(files["forecast_exact.json"])
    assert exact["outputs"]["REFERENCE"]["years"][0]["closing_cash"]["amount"] == "162"
    assert exact["scope_limits"][:2] == [cpos_forecast.LAYER1_LIMIT, SCALE_LIMIT]
    assert cell(json.loads(files["calculation.json"])["history"], "LTM", "revenue")["amount"] == "1060"
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_scale.py -q` — expected: the new tests fail (no `scale` or `units` key and no `SCALE_LIMIT`; the history lines are missing because the cells are still compared in thousands).
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `uv run pytest tests/test_cpos_scale.py tests/test_cpos_periods.py tests/test_cpos_facilities.py -q` — expected: all pass.
- [ ] **Step 5: Commit** `feat(forecast): publish a thousands block in USD millions, history included`

### Task B3: A named row in the other unit is refused (ruling B7; drop this task if the owner strikes it)

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_forecast.py`
- Test: `tests/test_cpos_scale.py`

**Interfaces:**
- Produces:
  - `def _unit_cells(text: str, label: str, period: str) -> set[str]`: for each table of `_tables(text)` with a header cell that is exactly `Reporting unit` and a column headed `period`, the plain `Reporting unit` cell of every row labelled `label`.
  - `def _unit_problem(text: str, key: str, operand: Operand, scale: int) -> str | None`: AK-6's message for the first unit cell (sorted) that names the other unit. Other-unit words, case-insensitive: at scale 1000 `million`, `billion`, or `US$`, `USD` or `$` followed by `m`, `mm` or `bn` at a word end; at scale 1 `thousand`, `$000`, or `US$` or `USD` followed by `k` at a word end.
  - `parse` runs it for a named operand with an amount, after `_layer1_problem` passes, only when the block states `scale`.

- [ ] **Step 1: Write the failing tests**

```python
CHART_ROW = {"amount": "618.5", "reason": None, "row": "H1 2025", "period": "Undrawn committed facilities"}

def test_a_millions_chart_row_in_a_thousands_block_is_refused():   # AK-6
    with pytest.raises(ValueError) as caught:
        parse(block_k2(base={**K2_BASE, "undrawn": CHART_ROW}), CP1_K2)
    assert str(caught.value) == ("CP-2G: base undrawn: row `H1 2025` states its Reporting unit as `US$m`, not the "
                                 "block's unit (USD thousands, scale 1000); state a reason instead of an amount")

def test_the_same_row_is_read_by_a_millions_block():
    base = {k: {"amount": None, "reason": "not used"} for k in K2_BASE} | {"undrawn": CHART_ROW}
    assert parse(forecast_block(scale=1, base=base), CP1_K2).base["undrawn"].amount == "618.5"

def test_a_thousands_unit_cell_refuses_a_millions_block():
    cp1 = CP1_K2.replace("| US$m |", "| US$ thousands |")
    base = {k: {"amount": None, "reason": "not used"} for k in K2_BASE} | {"undrawn": CHART_ROW}
    with pytest.raises(ValueError, match="not the block's unit \\(USD millions, scale 1\\)"):
        parse(forecast_block(scale=1, base=base), cp1)

def test_a_block_without_scale_is_not_checked_for_units():
    base = {k: {"amount": None, "reason": "not used"} for k in K2_BASE} | {"undrawn": CHART_ROW}
    assert parse(forecast_block(base=base), CP1_K2.replace("| US$m |", "| US$ thousands |"))
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_scale.py -q -k "unit or chart_row or millions_block"` — expected: the two refusal tests fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `uv run pytest tests/test_cpos_scale.py tests/test_cpos_launch.py -q -k "scale or unit or layer1 or forecast"` — expected: all pass.
- [ ] **Step 5: Commit** `feat(forecast): refuse a named row whose Reporting unit is not the block's`

### Task B4: The two instruction texts

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_launch.py` (`FORECAST_BLOCK`, `LAYER1_FORECAST_BLOCK`)
- Test: `tests/test_cpos_launch.py`

- [ ] **Step 1: Write the failing test**

```python
def test_both_forecast_instructions_ask_for_the_scale():
    for block, tables in ((cpos_launch.FORECAST_BLOCK, "CP-1's"), (cpos_launch.LAYER1_FORECAST_BLOCK, "your")):
        for words in (f"`scale` is `1` when {tables} statement tables print USD millions and `1000` when they print USD thousands",
                      "Python divides by `scale`", "Do not convert an amount yourself",
                      'a cell printing 2,620,995 is `"2620995"`', "at most nine digits and one decimal place",
                      "only in the other unit", "every other driver is a ratio and is never scaled"):
            assert words in block, words
        assert "ten operands in USD millions" not in block and "in millions;" not in block
    assert "`balance` is in the block's unit" in cpos_launch.FORECAST_BLOCK
    assert "`annual_amortisation` is in the block's unit, a year" in cpos_launch.FORECAST_BLOCK
    assert "USD millions a year" not in cpos_launch.FORECAST_BLOCK
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_launch.py -q -k ask_for_the_scale` — expected: fails.
- [ ] **Step 3: Edit `FORECAST_BLOCK`** (exact copy; the text is Task A3's):
  1. `` `base` holds exactly these ten operands in USD millions, each `` becomes: `` `scale` is `1` when CP-1's statement tables print USD millions and `1000` when they print USD thousands; every amount in this block is stated in that one unit, exactly as CP-1 prints it, and Python divides by `scale`, so every published figure is USD millions. Do not convert an amount yourself. `base` holds exactly these ten operands, each ``
  2. `Copy the amount as that cell prints it, in millions;` becomes: `Copy the amount as that cell prints it (with "scale": 1000 a cell printing 2,620,995 is "2620995"; at most nine digits and one decimal place);` with `"scale": 1000` and `"2620995"` in backticks.
  3. After `is stated as missing, with the reason.` add: `An amount CP-1 prints only in the other unit (for example revolver availability in USD millions where the statements are in thousands) is stated as missing, with the reason; do not rescale it.`
  4. After `(a ratio of 0.48022670 is written "0.4802")` and before `` ; `category` `` add: `; the dividends and debt_repayment values are amounts in the block's unit (with "scale": 1000, USD 20 million is "20000", at most one decimal place) and every other driver is a ratio and is never scaled`, the two driver names, the scale and the amount in backticks.
  5. `` `balance` is USD millions and `` becomes `` `balance` is in the block's unit and ``; `` `annual_amortisation` is USD millions a year, `` becomes `` `annual_amortisation` is in the block's unit, a year, ``; after `` A row's `balance` is its drawn principal. `` add: `Leave out a facility whose balance CP-1 prints only in the other unit.`
- [ ] **Step 4: Edit `LAYER1_FORECAST_BLOCK`** (exact copy):
  1. `` `base` holds exactly these ten operands in USD millions, each `` becomes: `` `scale` is `1` when your statement tables print USD millions and `1000` when they print USD thousands; every amount in this block is stated in that one unit, exactly as your tables print it, and Python divides by `scale`, so every published figure is USD millions. Do not convert an amount yourself. `base` holds exactly these ten operands, each ``
  2. `Copy the amount as that cell prints it, in millions;` becomes the same sentence as in `FORECAST_BLOCK`.
  3. After `A figure in prose, a basis line or the sources is not a cell.` add: `An amount your tables print only in the other unit is stated as missing, with the reason.`
  4. After `each rounded to at most four decimal places` and before `` ; `category` `` add the same clause as in `FORECAST_BLOCK`.
- [ ] **Step 5: Run** `uv run pytest tests/test_cpos_launch.py -q -k "instruction or forecast or layer1 or period_table"` — expected: all pass.
- [ ] **Step 6: Commit** `feat(cp1, cp2g): ask for the scale of the forecast inputs`

### Task B5: The grid's caption is the record's

**Files:**
- Modify: `apps/issuer-library/credit_os/store.py` (next to `cashflow_units` :1478; `cashflow_of` :2748 and its `units` entry :2827; `read_cashflow` :2855)
- Test: `tests/test_credit_os_store.py` (after the history tests; `FILES`, `REFERENCE` at :1377, :1356)

**Interfaces:**
- Produces:
  - `UNITS_LIMIT = 40`; `def recorded_units(exact: Any) -> str | None`: the record's `units`; None when absent or null; a value that is not text of 1 to 40 characters raises `TypeError("units is not a short text")`.
  - `read_cashflow` reads it in the `forecast_exact.json` stage and passes it to `cashflow_of(..., handoff, budget, units=None)`, whose `"units"` entry is the record's when present, else today's expression.
  - A record without `units`: unchanged, byte for byte.

- [ ] **Step 1: Write the failing tests**

```python
REQUEST_IN_THOUSANDS = "## Request\n\nBase: September balances, USD thousands, consolidated.\n"

def with_units(units):
    return {**FILES, "forecast_exact.json": json.dumps({**REFERENCE, "scale": 1000, "units": units}).encode()}

def test_the_units_caption_is_the_records_statement_not_the_requests_phrase():
    assert store.read_cashflow(with_units("USD millions"), REQUEST_IN_THOUSANDS)[0]["units"] == "USD millions"
    assert store.read_cashflow(with_units("USD millions"), None)[0]["units"] == "USD millions"

def test_a_record_without_units_keeps_the_requests_phrase():
    assert store.read_cashflow(FILES, REQUEST_IN_THOUSANDS)[0]["units"] == "USD thousands"
    assert store.read_cashflow(FILES, None)[0]["units"] is None

@pytest.mark.parametrize("units", [5, "", "x" * 41, ["USD millions"]])
def test_units_that_are_not_a_short_text_are_reported_not_shown(units):
    assert store.read_cashflow(with_units(units), None) == (None, ("file", "forecast_exact.json"))
```

- [ ] **Step 2: Run** `uv run pytest tests/test_credit_os_store.py -q -k units` — expected: the first and third fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `uv run pytest tests/test_credit_os_store.py -q` and `uv run pytest tests/test_cpos_launch.py -q -k library` — expected: all pass.
- [ ] **Step 5: Commit** `feat(library): the Forecast grid's units caption comes from the forecast record`

### Task B6: Fidelity check, reader check, record, gates

**Files:**
- Modify: `VERIFICATION.md`

- [ ] **Step 1: Fidelity check (a probe saved under `.superpowers/sdd/<this plan>/probes/`, not committed).** Build `model_files(CP1_K2, handoff, history=True)` where the handoff is `## Request` with the words `USD thousands` followed by `block_k2()`, pass the files and the handoff text to `store.read_cashflow`, and compare with AK-4: `units == "USD millions"`; Revenue row `1421.519, 1264.478, 2620.995, 2778.036` in YTD, PYTD, FY2024, LTM and `2883.0945` in the first base-case year; Undrawn facility `n.a.` with the stated reason; `SCALE_LIMIT` second in `limits`. Exit 1 on any difference.
- [ ] **Step 2: Retained check (offline, read only).** For each of the four thousands handoffs run `parse` on hand-written scale-1000 blocks (one operand stated, the other nine missing, synthetic drivers) and record, per run, accepted with the parsed amount or the refusal text:

| Run | Stated, named | Expected |
| --- | --- | --- |
| `web-2cb85cb4` | revenue `2620995` at `Total revenue`, `FY2024`; debt `1534356` at `Total debt`, `June 30, 2025` | `2620.995`; `1534.356` |
| `web-79a17365` | revenue `1100441` at `Total net revenues`, `FY2024`; cash `332437` at `Cash and cash equivalents`, `H1 2025` | `1100.441`; `332.437` |
| `web-79a17365` | undrawn `585.8` at `June 30, 2025`, `Undrawn committed facilities` | refused by Task B3 (`US$m`) |
| `web-b7425f3d` | revenue `849827` at `Net sales`, `H1 2025` | `849.827` |
| `web-d95ed5de` | revenue `3751025` at `Revenue`, `FY2023`; debt `5221847` at `Total debt`, `2024-09-30` | `3751.025`; `5221.847` |

  Also record the two residuals as they are: LTH undrawn `618.5` at `Revolver availability`, `June 30, 2025` is accepted as `0.6185`; B&G revenue `849827` with no `scale` is accepted as millions. This proves the checks on real printed forms, not a model's ability to write the block.
- [ ] **Step 3: Reader check.** Open the page built from Step 1's files (the library fixture of `tests/test_library_page_browser.py`) and one existing published model without `units`. Read both against the September VMO2 reference as the portfolio manager: the caption says USD millions; no figure reads a thousand times too large or too small beside its neighbours; the scale line is among the limits. Record what was read. A real run is not available offline: record the real-run reader check as pending the paid run.
- [ ] **Step 4: Run** `uv run python tools/quality_gate.py --base <PR A branch>` — expected: exit 0. Then the PR check's pytest command — expected: exit 0.
- [ ] **Step 5: Record in `VERIFICATION.md`** one entry, scope stated exactly: "offline; synthetic thousands and millions fixtures with hand-computed answer keys; four retained thousands CP-1 handoffs read for printed forms and unit lines with hand-written blocks; no provider called and no model response: no model has yet written `scale`; nothing detects a missing or wrong `scale`; the reader check on a real thousands run is pending a paid run". Commands, exit codes and the per-run results of Step 2. Trim the oldest entries.
- [ ] **Step 6: Commit** `docs(verification): forecast units`

## Line estimates against the 800-line limit

Measured on the throwaway prototype after `ruff format` (not this plan file, which goes in its own docs commit or counts against a PR).

| PR | Measured | Not prototyped | Estimate | Split if over |
| --- | --- | --- | --- | --- |
| A | 666: `cpos_periods.py` -135 +26; `cpos_forecast.py` -16 +14; `tests/test_cpos_periods.py` -176 +200; `tests/test_cpos_launch.py` +99 | instruction text and its test, the replaced test, `VERIFICATION.md`: about 45 | about 710 | A-i: Tasks A1 and A3 (about 170; a named block parses, history still as before). A-ii: Tasks A2 and A4 |
| B | 643: `cpos_forecast.py` -16 +129; `cpos_periods.py` -3 +9; `store.py` -3 +21; `tests/test_credit_os_store.py` +28; `tests/test_cpos_scale.py` +434 | instruction texts and test, the property test, `checks.yml`, `VERIFICATION.md`: about 100 | about 745 | B-i: Tasks B1 to B3 (about 610; safe alone, because no instruction asks for `scale` yet). B-ii: Tasks B4 to B6 (about 135) |

Both estimates are within 100 lines of the limit. Run the numstat command before the last task of each PR and split there if it is over.

## Open questions

1. **`undrawn` on thousands issuers.** With one scale per block it is missing on all four retained thousands handoffs, and Liquidity with it. An operand-level `scale` (1 or 1000, default the block's) would recover the two that print it in a table cell, for about 40 lines, at the price of one more thing a model can get wrong per operand. Recommended: ship one scale per block as decided; decide the operand-level scale after the first paid thousands run shows whether the missing Liquidity row matters to the reader.
2. **Widen ruling B7 beyond the `Reporting unit` column.** LTH states the unit in a column headed `Unit and terms / evidence`, so its availability row is not caught and parses to `0.6185`. The wider rule: refuse a named operand when a cell of its row other than the amount cell, the named column's header or the table's first header cell names the other unit and none of them names the block's unit. Measured over the 534 table rows that hold a number in the four retained thousands handoffs (a one-off script, the rule not built into `parse`): it refuses seven rows, six rightly (LTH's four `US$ million` rows, Sotera's two chart rows) and one wrongly (IHRT's `Cash consideration`, a thousands calculation row whose formula cell says `USD 37.6 million represented as 37,600`; not a base operand). Recommended: yes, in Task B3, about 15 more lines; a wrong figure is worse than an unavailable one. Its cost: a row whose other cells mention only the other unit is refused though it is in the block's unit, which CP-2G can repair by stating the operand as missing and which on the layer-1 path loses the forecast.
3. **Require names in the repair loop.** `_forecast_issues` could send back a CP-2G block that names no row. Recommended: not yet. Its fallback line tells the model to null every driver, which would trade a forecast without history for no forecast. Decide after the paid run.
4. **The repair line for a base-operand refusal** tells the model to null every driver if it cannot correct the block. Recommended: yes, change it for errors about a base operand to offer stating that operand as missing with its reason (one string and one test in Task A4); a wrong row label should not cost the forecast.
5. **The period-header sentence in the layer-1 instruction** (ruling A5 adds it for CP-2G only). Recommended: yes, add the same sentence to `LAYER1_FORECAST_BLOCK` in Task B4, where that text is edited anyway.
6. **Currency.** `units` says USD for every issuer because the block's contract is USD. Recommended: leave; a `currency` field is its own change.
7. **Where this plan file is committed.** Recommended: its own docs commit on `main` or a docs PR, so it does not count against either PR.

## After the tasks

- Whole-branch, once per PR: confidence-review and rewrite-tournament (post-edit: PR A `cpos_forecast.parse`, `cpos_periods._locate`, `_line`; PR B `cpos_forecast._to_millions`, `_slots`, `_check_facilities`, `cpos_periods._locate`, `store.read_cashflow`). Both PRs change money code: adversarial review of the diff, and hand-picked mutants on `_to_millions` and `_locate` as the period-columns PRs did (the repository has no mutation tool configured).
- Owner's actions, not in this plan:
  1. One paid run with CP-2G on an issuer whose CP-1 prints USD thousands (LTH or IHRT), then the reader check on its Forecast page. Until then both changes are proven on synthetic inputs and retained printed forms only.
  2. Answer the open questions; 4 and 5 change task text before the first dispatch.
- For the owner, found here and predating this plan: nothing checks that the flow operands name one period, on either source (ruling A4); a six-digit thousands amount without `scale` is read as millions; the period-columns plan's "three of six" thousands handoffs is four.

## Controller rulings on the open questions (2026-11-12, before the first dispatch)

1. Operand-level `scale`: not built. One scale per block; `undrawn` in the other unit is missing with its reason. Cost: Liquidity is `n.a.` on the four retained thousands issuers until the owner decides after a paid run.
2. Ruling B7 is widened as the question describes, in Task B3: a named operand is refused when a cell of its row other than the amount cell, the named column's header, or the table's first header cell names the other unit and none of them names the block's unit. Cost: a row that mentions only the other unit in passing is refused (one of 534 retained rows, not a base operand).
3. The repair loop does not require names. Cost: a model that ignores the instruction gets a forecast without history.
4. Task A4 also changes the repair line for a base-operand refusal: it offers stating that operand as missing with its reason, instead of nulling every driver.
5. Task B4 adds the period-header sentence to `LAYER1_FORECAST_BLOCK`.
6. No `currency` field.
7. This plan file is committed on its own; it is left out of each PR's line count.
