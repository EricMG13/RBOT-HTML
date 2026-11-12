# CP-2G Facility Schedule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When the CP-2G handoff states the issuer's debt facilities, Python computes forecast cash interest and scheduled repayment per facility instead of from one analyst rate and one analyst repayment figure.

**Architecture:** The CP-2G forecast inputs block (`cpos-forecast-inputs/1`) gains an optional `facilities` list. A new pure module turns it into a per-year `(interest, repayment)` schedule; `cp2g.forecast` takes that schedule in place of the `interest_rate` and `debt_repayment` drivers. A block without `facilities` computes exactly as today, byte for byte.

**Tech Stack:** Python, `decimal` (38-digit half-even, existing `cp2g` contexts), pydantic `Contract`, pytest. No new dependency.

**Spec:** This document's Design section. Method source: caos-databricks `dfff264c`, `caos/calculators/credit_model/projection.py` (`facility_rate`, `_schedule`, `_interest`), adapted. No CP-CF request contract, rate deck or reconciliation is taken.

## Design

### Why the facilities are stated by CP-2G, not CP-1

On the active CP-OS path CP-1 is free Markdown. Retained runs (`~/Documents/FinalWorkflow-Live/runs/web-*/CP-1.md`, read only) print facility balances in a table but put coupons, margins, floors and amortisation in prose, under headings that differ run to run. There is no machine-readable facility register to read. CP-1 is not changed. CP-2G, which already reads CP-1 and already restates the ten base operands, restates the facility rows; Python checks each balance and each rate term is printed in CP-1, as it already does for base operands (`cpos_forecast._printed`).

### The `facilities` field

Optional; absent or `null` means today's behaviour. Each row:

| Field | Form | Check |
| --- | --- | --- |
| `name` | text, 1 to 120 characters, unique in the list | |
| `balance` | `^[0-9]{1,6}(\.[0-9]{1,4})?$`, USD millions | printed in CP-1 |
| `fixed_rate_pct` | percent as CP-1 prints it, `^[0-9]{1,2}(\.[0-9]{1,4})?$`, at most 30, or null | printed in CP-1 |
| `spread_pct` | same form, at most 20, or null | printed in CP-1 |
| `floor_pct` | same form, at most 10, or null | printed in CP-1 |
| `reference_rate` | three decimal fractions (`cp2g.GROWTH_PATTERN`), one per forecast year, or null. The analyst's assumption for the reference rate | none: an assumption |
| `annual_amortisation` | amount form, USD millions a year, or null (not stated: none) | none: often derived from a percent of principal |
| `maturity` | `YYYY-MM-DD` or null | |

A row states either `fixed_rate_pct` alone, or `reference_rate` with `spread_pct` (and optionally `floor_pct`); anything else is refused.

### Arithmetic

For facility *i* in forecast year *t* (t = 0, 1, 2), all exact Decimal:

- rate: fixed `fixed_rate_pct / 100`; floating `max(reference_rate[t], floor_pct / 100) + spread_pct / 100` (no floor: the reference rate itself).
- `interest[i][t] = opening[i][t] * rate[i][t]`
- `repaid[i][t] = min(annual_amortisation, opening[i][t])` (null amortisation: 0)
- `opening[i][t+1] = opening[i][t] - repaid[i][t]`; `opening[i][0] = balance`
- year totals: `interest[t] = sum_i interest[i][t]`, `repayment[t] = sum_i repaid[i][t]`

In `cp2g._year`, with a schedule: cash interest is `interest[t] * (1 + k)` (k the downside rate increase, 0 otherwise), missing with the opening debt's reason when the opening debt is missing; repayment is `repayment[t]`. Everything else in `_year` is unchanged, so total debt still closes at opening debt less repayment.

### Rulings carried in this plan

1. With `facilities` stated, the `interest_rate` and `debt_repayment` drivers are not used in any case. `base_drivers` still states them (schema unchanged). An `upside_drivers` or `downside_drivers` case that names either is refused. A scope limit says so. (Alternative not taken: treat `debt_repayment` as voluntary prepayment on top of the schedule.)
2. Base debt not in a facility row (`base debt - sum of balances`) bears no interest and is not repaid; its amount is published as `unallocated_debt` and named in a scope limit. Missing base debt: `unallocated_debt` is missing with the base debt's reason.
3. A facility whose `maturity` falls on or before the third forecast year's end keeps its balance (assumed refinanced), named with its year in a scope limit.
4. Sum of balances above 1.25 times a known base debt is refused: a unit or currency slip (CP-1 in thousands), not a carrying-value difference.
6. Rebased onto main `36b6d8f` (2026-11-12): CP-1 may now write a layer-1 forecast block (`parse(..., source="CP-1")`). Facilities are CP-2G's only: a CP-1 block that states `facilities` is refused, as it already is for a shock or cases. CP-1's instruction (`LAYER1_FORECAST_BLOCK`) is not changed.
5. No presentation change: `cp2g.Year` keeps its fields, so `apps/issuer-library/credit_os/store.py` and the Forecast page read the same keys. New detail appears only in `forecast_exact.json` and `scope_limits`.

## Global Constraints

- Excel is input only; no workbook output.
- Missing is never zero: every value is known, missing with its reason, or not applicable.
- All sums and products run in `cp2g`'s 38-digit half-even context with the Inexact trap.
- Expected values in tests are independent of production code: the hand-computed figures below, or `Fraction` arithmetic written in the test.
- No provider call, no credential file. A live CP-2G run is a separate owner action, not part of this plan.
- Never change predecessor repositories or retained run directories.
- One verification record: `VERIFICATION.md`, under 1,000 lines.
- Every task report ends with a `Not verified:` line. No stub or fake value standing in for real behaviour; no catch-all that hides a failure.
- Per task run only the named tests (each under 300 seconds). Before completion: `uv run python tools/quality_gate.py`, then confidence-review and rewrite-tournament (post-edit) once on the branch diff.

## Review Focus

1. CP-1 prints thousands, CP-2G states millions (or the reverse): refused by ruling 4, not forecast a thousand times out. Test in Task 3.
2. A block without `facilities`: `forecast_exact.json` is byte-identical to today's. Test in Task 3.
3. A rate written `9.5` where CP-1 prints `9.500`: refused, naming the facility and the term. Test in Task 3.
4. Base debt missing with facilities stated: no exception; interest and debt are missing with the base debt's reason. Test in Task 2.
5. A case override naming `interest_rate` while facilities are stated: refused, not silently ignored. Test in Task 3.

## File Structure

| File | Responsibility |
| --- | --- |
| `src/deploy_workflow/owners/cpos_facilities.py` (new) | `Facility` contract and the pure `schedule` |
| `src/deploy_workflow/owners/cp2g.py` | `_year` and `forecast` accept a schedule |
| `src/deploy_workflow/owners/cpos_forecast.py` | `facilities` field, printed checks, wiring, published detail |
| `src/deploy_workflow/owners/cpos_launch.py` | `FORECAST_BLOCK` instruction text |
| `src/deploy_vii/methods/cp2g.md` | Method note |
| `tests/test_cpos_facilities.py` (new) | Tasks 1 to 3 |
| `tests/test_cpos_launch.py` | Instruction text assertion (Task 4) |

### Answer key (hand-computed; do not edit)

Facilities: **A** fixed 6.00%, balance 400, amortisation 20. **B** floating, reference rate (0.04, 0.03, 0.005), floor 1.00%, spread 3.00%, balance 150, amortisation null. Base debt 600.

| Year | A opening | A interest | B rate | B interest | Interest | Repayment | Closing debt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 400 | 24 | 0.07 | 10.5 | 34.5 | 20 | 580 |
| 2 | 380 | 22.8 | 0.06 | 9 | 31.8 | 20 | 560 |
| 3 | 360 | 21.6 | 0.04 | 6 | 27.6 | 20 | 540 |

Unallocated debt 50. Downside with rate increase 0.10: interest 37.95, 34.98, 30.36. Cap case: balance 30, amortisation 20 repays 20, 10, 0.

---

### Task 1: Facility contract and schedule

**Files:**
- Create: `src/deploy_workflow/owners/cpos_facilities.py`
- Test: `tests/test_cpos_facilities.py`

**Interfaces:**
- Consumes: `deploy_vii.contracts.Contract`; `cp2g.GROWTH_PATTERN`, `cp2g.AMOUNT_PATTERN`, `cp2g._EXACT`.
- Produces:
  - `class Facility(Contract)` with the eight fields in the Design table (`reference_rate: tuple[str, str, str] | None`).
  - `@dataclass(frozen=True) class FacilityYear: opening: Decimal; rate: Decimal; interest: Decimal; repaid: Decimal; closing: Decimal`
  - `@dataclass(frozen=True) class Schedule: rows: tuple[tuple[FacilityYear, FacilityYear, FacilityYear], ...]` (one triple per facility, input order) with `def totals(self) -> tuple[tuple[Decimal, Decimal], tuple[Decimal, Decimal], tuple[Decimal, Decimal]]` returning `(interest, repayment)` per year.
  - `def schedule(facilities: Sequence[Facility]) -> Schedule`

- [ ] **Step 1: Write the failing tests**

```python
A = {"name": "Notes", "balance": "400", "fixed_rate_pct": "6.00", "spread_pct": None,
     "floor_pct": None, "reference_rate": None, "annual_amortisation": "20", "maturity": None}
B = {"name": "Term loan", "balance": "150", "fixed_rate_pct": None, "spread_pct": "3.00",
     "floor_pct": "1.00", "reference_rate": ["0.04", "0.03", "0.005"],
     "annual_amortisation": None, "maturity": None}

def test_schedule_matches_the_answer_key():
    s = schedule([Facility(**A), Facility(**B)])
    assert s.totals() == ((D("34.5"), D("20")), (D("31.8"), D("20")), (D("27.6"), D("20")))
    assert [y.rate for y in s.rows[1]] == [D("0.07"), D("0.06"), D("0.04")]
    assert [y.closing for y in s.rows[0]] == [D("380"), D("360"), D("340")]

def test_amortisation_never_takes_a_balance_below_zero():
    s = schedule([Facility(**{**A, "balance": "30"})])
    assert [y.repaid for y in s.rows[0]] == [D("20"), D("10"), D("0")]

@pytest.mark.parametrize("change", [
    {"fixed_rate_pct": None},                                   # no rate at all
    {"spread_pct": "3.00"},                                     # fixed and floating together
    {"fixed_rate_pct": None, "spread_pct": "3.00"},             # spread without a reference rate
    {"fixed_rate_pct": "31"}, {"fixed_rate_pct": "6.00001"}, {"balance": "-1"}, {"name": ""},
])
def test_a_row_that_is_not_one_rate_form_is_refused(change):
    with pytest.raises(ValidationError):
        Facility(**{**A, **change})
```

Compare Decimals by value (`==`), with `D = Decimal`.

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_facilities.py -q` — expected: fails on import.
- [ ] **Step 3: Implement `Facility` and `schedule`** per the Design's Arithmetic section, inside `localcontext(cp2g._EXACT)`. The rate-form rule and the 30 / 20 / 10 ceilings are one `model_validator`.
- [ ] **Step 4: Run** the same command — expected: all pass.
- [ ] **Step 5: Commit** `feat(cp2g): facility schedule from stated terms`

### Task 2: The engine takes a schedule

**Files:**
- Modify: `src/deploy_workflow/owners/cp2g.py:497-556` (`_year`, `forecast`)
- Test: `tests/test_cpos_facilities.py`

**Interfaces:**
- Consumes: `Schedule.totals()` from Task 1.
- Produces: `forecast(*, operands, drivers, shock, schedule: tuple[tuple[Decimal, Decimal], ...] | None = None) -> CaseForecast`. `_year` gains a last parameter `scheduled: tuple[Decimal, Decimal] | None`. With `None`, both behave exactly as now.

- [ ] **Step 1: Write the failing tests** using `tests/test_cpos_launch.py`'s `BASE` and `PATHS` values to build `Operands` and `Drivers`:

```python
TOTALS = ((D("34.5"), D("20")), (D("31.8"), D("20")), (D("27.6"), D("20")))

def test_scheduled_interest_and_repayment_replace_the_two_drivers():
    years = cp2g.forecast(operands=OPERANDS, drivers=DRIVERS, shock=None, schedule=TOTALS).years
    assert [y.interest.amount for y in years] == [D("34.5"), D("31.8"), D("27.6")]
    assert [y.closing_debt.amount for y in years] == [D("580"), D("560"), D("540")]

def test_the_downside_rate_increase_scales_scheduled_interest():
    years = cp2g.forecast(operands=OPERANDS, drivers=DRIVERS,
                          shock=(D("0"), D("0.10")), schedule=TOTALS).years
    assert [y.interest.amount for y in years] == [D("37.95"), D("34.98"), D("30.36")]

def test_no_schedule_is_todays_forecast():
    assert cp2g.forecast(operands=OPERANDS, drivers=DRIVERS, shock=None, schedule=None) == \
           cp2g.forecast(operands=OPERANDS, drivers=DRIVERS, shock=None)

def test_missing_base_debt_stays_missing_with_its_reason():      # Review Focus 4
    ops = replace(OPERANDS, debt=cp2g.Val(None, "why"))
    y = cp2g.forecast(operands=ops, drivers=DRIVERS, shock=None, schedule=TOTALS).years[0]
    assert (y.interest.amount, y.interest.reason) == (None, "why")
    assert y.closing_debt.amount is None
```

Also assert year 1 free cash flow against a `Fraction` computed in the test from `BASE`, `PATHS` and interest 34.5 (the pattern of `key_case` in `tests/test_cpos_launch.py`).

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_facilities.py -q` — expected: the four new tests fail (`unexpected keyword argument 'schedule'`).
- [ ] **Step 3: Implement.** In `_year`, when `scheduled` is given: `interest = _apply(lambda d: scheduled[0] * (1 + k), debt)` and `rep = scheduled[1]`. `forecast` passes `schedule[t]`.
- [ ] **Step 4: Run** `uv run pytest tests/test_cpos_facilities.py tests/test_cpos_launch.py -q -k "forecast or facilit"` — expected: all pass.
- [ ] **Step 5: Commit** `feat(cp2g): forecast accepts a facility schedule`

### Task 3: The inputs block states facilities

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_forecast.py` (`ForecastInputs`, `parse`, `model_files`)
- Test: `tests/test_cpos_facilities.py`

**Interfaces:**
- Consumes: `Facility`, `schedule`, `Schedule` (Task 1); `cp2g.forecast(..., schedule=)` (Task 2).
- Produces: `ForecastInputs.facilities: tuple[Facility, ...] | None = None` (1 to 40 rows when stated). `forecast_exact.json` gains, only when facilities are stated: `facilities` (the rows as stated), `facility_schedule` (per facility `name` and three years of `opening`, `rate`, `interest`, `repaid`, `closing` as plain decimal strings), `unallocated_debt` (`{"amount", "reason"}`), and three appended `scope_limits`.

Scope limit texts (exact; `{…}` filled, amounts as plain decimal strings):

- `Cash interest and scheduled repayment are computed from the facility terms the CP-2G handoff stated; the interest_rate and debt_repayment drivers are not used.`
- `Debt of {amount} is not in a stated facility; it bears no interest and is not repaid in this forecast.` (omitted when the amount is 0; when base debt is missing: `Base debt is missing, so debt outside the stated facilities is not known.`)
- `{name} matures in FY{year} and is assumed refinanced; its balance is held.` (one per such facility)

Refusals (`ValueError`, exact text):

- `CP-2G: facility {name} {field} {value} is not printed in CP-1` (`field` one of `balance`, `fixed_rate_pct`, `spread_pct`, `floor_pct`)
- `CP-2G: facility balances total {sum}, more than 1.25 times base debt {debt}; check the unit`
- `CP-2G: {case} states {driver}, which is not used when facilities are stated` (`case` is `upside_drivers` or `downside_drivers`)
- `CP-1: a layer-1 forecast states no facilities` (a block parsed with `source="CP-1"`; extend the existing shock-and-cases refusal's condition, keeping its own text for those)
- duplicate names: a pydantic issue through the existing `shape_issues` path.

- [ ] **Step 1: Write the failing tests** with `forecast_block` and `BASE` imported from `tests/test_cpos_launch.py`, CP-1 text `" ".join(BASE.values()) + " 400 150 6.00 3.00 1.00"` (call `model_files(cp1, handoff)` with the default `source="CP-2G"`):

```python
def test_a_block_with_facilities_publishes_the_answer_key():
    exact = json.loads(model_files(CP1, block(facilities=[A, B]))["forecast_exact.json"])
    ref = exact["outputs"]["REFERENCE"]["years"]
    assert [D(y["interest"]["amount"]) for y in ref] == [D("34.5"), D("31.8"), D("27.6")]
    assert [D(y["closing_debt"]["amount"]) for y in ref] == [D("580"), D("560"), D("540")]
    assert D(exact["unallocated_debt"]["amount"]) == D("50")
    assert D(exact["facility_schedule"][1]["years"][2]["rate"]) == D("0.04")
    assert "Debt of 50 is not in a stated facility; it bears no interest and is not repaid in this forecast." in exact["scope_limits"]

def test_a_block_without_facilities_is_byte_identical():          # Review Focus 2
    assert model_files(CP1, block()) == model_files(CP1, block(facilities=None))
    assert b"facilit" not in model_files(CP1, block())["forecast_exact.json"]

@pytest.mark.parametrize("rows, cp1, message", [
    ([{**A, "fixed_rate_pct": "6.0"}], CP1_TEXT, "facility Notes fixed_rate_pct 6.0 is not printed in CP-1"),   # Focus 3
    ([{**A, "balance": "400000"}], CP1_TEXT + " 400000", "more than 1.25 times base debt 600; check the unit"),  # Focus 1
])
def test_refusals(rows, cp1, message): ...

def test_a_case_override_of_an_unused_driver_is_refused():        # Review Focus 5
    # downside_drivers names interest_rate, facilities stated
    ... match="downside_drivers states interest_rate, which is not used when facilities are stated"

def test_cp1s_layer1_block_states_no_facilities():
    # layer1_block(facilities=[A]) from tests/test_cpos_launch.py, parsed with source="CP-1"
    ... match="CP-1: a layer-1 forecast states no facilities"

def test_a_maturity_inside_the_forecast_is_named():
    # A with maturity inside the second forecast year (years run 2025-04-01 to 2028-03-31)
    ... "Notes matures in FY2026 and is assumed refinanced; its balance is held." in scope_limits
```

Published amounts are compared as `Decimal` (the existing `_cell` writes `format(amount, "f")`, which may keep trailing zeros). In scope-limit text, amounts are written normalised without an exponent (`50`, not `50.00`).

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_facilities.py -q` — expected: new tests fail (`facilities` is an extra field or absent from output).
- [ ] **Step 3: Implement.** `parse` runs the printed and 1.25 checks after the base-operand check. `model_files` builds the schedule once and passes `schedule.totals()` to every case's `cp2g.forecast`. The three new keys and limits are written only when facilities are stated (the existing `_stated` pattern).
- [ ] **Step 4: Run** `uv run pytest tests/test_cpos_facilities.py -q` and `uv run pytest tests/test_cpos_launch.py -q -k forecast` — expected: all pass.
- [ ] **Step 5: Commit** `feat(cp2g): forecast inputs block states facilities`

### Task 4: Instruction text, method note, verification record, gates

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_launch.py:1473` (`FORECAST_BLOCK` only; `LAYER1_FORECAST_BLOCK` is not touched)
- Modify: `src/deploy_vii/methods/cp2g.md` (Method bullet on interest and debt; the "New borrowing, refinancing, maturities" and "Interest on average balance" rows)
- Modify: `VERIFICATION.md`
- Test: `tests/test_cpos_launch.py` (next to the other `all_instructions` assertions)

**Interfaces:**
- Consumes: the field names and forms of Task 1 and the rulings above.

- [ ] **Step 1: Write the failing test**

```python
def test_cp2g_is_told_how_to_state_facilities(tmp_path):
    _, texts = all_instructions(tmp_path, modules=("CP-0", "CP-1", "CP-2A", "CP-2G"))
    head = texts["CP-2G"].partition(cpos_launch.METHOD_MARK)[0]
    for word in ("`facilities`", "fixed_rate_pct", "spread_pct", "floor_pct", "reference_rate",
                 "annual_amortisation", "maturity", "exactly as CP-1 prints"):
        assert word in head
    assert "`facilities`" not in texts["CP-1"]
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_launch.py -q -k told_how_to_state_facilities` — expected: fails.
- [ ] **Step 3: Add this sentence group to `FORECAST_BLOCK`, after the `upside_drivers` sentence** (exact copy):

> `facilities` is optional: state it when CP-1 prints the debt facilities' balances and rate terms, otherwise write null. Each row is `{"name", "balance", "fixed_rate_pct", "spread_pct", "floor_pct", "reference_rate", "annual_amortisation", "maturity"}`. `balance` is USD millions and `fixed_rate_pct`, `spread_pct` and `floor_pct` are percents, each copied exactly as CP-1 prints it (a 9.500% coupon is "9.500"). A fixed-rate facility states `fixed_rate_pct` and null for the other rate fields; a floating-rate facility states `spread_pct`, `floor_pct` or null, and `reference_rate`, your assumed reference rate for each forecast year as three decimal fractions. `annual_amortisation` is USD millions a year, or null when CP-1 states none; `maturity` is YYYY-MM-DD or null. When `facilities` is stated Python computes cash interest and scheduled repayment from it and does not use the `interest_rate` and `debt_repayment` drivers, so do not vary those two in `upside_drivers` or `downside_drivers`.

- [ ] **Step 4: Update `methods/cp2g.md`**: the Method bullet says interest and repayment come from stated facilities when present (analyst rate and repayment otherwise); the maturities row says a maturity inside the forecast is held and named; no other row changes.
- [ ] **Step 5: Run** `uv run pytest tests/test_cpos_launch.py -q -k "instruction or forecast or told"` and `uv run python tools/quality_gate.py` — expected: pass, exit 0.
- [ ] **Step 6: Record in `VERIFICATION.md`** (986 lines now; trim its oldest entries so the file ends under 1,000) one entry: scope "offline synthetic tests of the facility schedule; no provider called, no model response; a live CP-2G run with `facilities` is not yet done", the commands run and their exit codes.
- [ ] **Step 7: Commit** `docs(cp2g): facility schedule instructions and record`

## After the tasks

- Whole-branch: confidence-review and rewrite-tournament (post-edit, `cp2g._year`, `cpos_facilities.schedule`, `cpos_forecast.model_files`) once on the branch diff.
- Not in this plan, owner's call: one paid CP-2G run on an issuer whose CP-1 prints facility terms, read against its handoff, to show a real model fills `facilities` correctly. Until then the change is proven on synthetic inputs only.
