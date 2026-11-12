"""CP-2G facility schedule: stated terms to interest and repayment (hand-computed answer key)."""

import json
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction

import pytest
from pydantic import ValidationError

from deploy_workflow.owners import cp2g
from deploy_workflow.owners.cpos_facilities import Facility, schedule

D = Decimal
A = {
    "name": "Notes",
    "balance": "400",
    "fixed_rate_pct": "6.00",
    "spread_pct": None,
    "floor_pct": None,
    "reference_rate": None,
    "annual_amortisation": "20",
    "maturity": None,
}
B = {
    "name": "Term loan",
    "balance": "150",
    "fixed_rate_pct": None,
    "spread_pct": "3.00",
    "floor_pct": "1.00",
    "reference_rate": ["0.04", "0.03", "0.005"],
    "annual_amortisation": None,
    "maturity": None,
}


def test_schedule_matches_the_answer_key():
    s = schedule([Facility(**A), Facility(**B)])
    assert s.totals() == ((D("34.5"), D("20")), (D("31.8"), D("20")), (D("27.6"), D("20")))
    assert [y.rate for y in s.rows[1]] == [D("0.07"), D("0.06"), D("0.04")]
    assert [y.closing for y in s.rows[0]] == [D("380"), D("360"), D("340")]


def test_amortisation_never_takes_a_balance_below_zero():
    s = schedule([Facility(**{**A, "balance": "30"})])
    assert [y.repaid for y in s.rows[0]] == [D("20"), D("10"), D("0")]


@pytest.mark.parametrize(
    "change",
    [
        {"fixed_rate_pct": None},  # no rate at all
        {"spread_pct": "3.00"},  # fixed and floating together
        {"fixed_rate_pct": None, "spread_pct": "3.00"},  # spread without a reference rate
        {"fixed_rate_pct": "31"},
        {"fixed_rate_pct": "6.00001"},
        {"balance": "-1"},
        {"name": ""},
        {"floor_pct": "1.00"},  # floor without a spread
        {"fixed_rate_pct": None, "spread_pct": "21", "reference_rate": ["0.04", "0.03", "0.005"]},
        {
            "fixed_rate_pct": None,
            "spread_pct": "3",
            "floor_pct": "11",
            "reference_rate": ["0.04", "0.03", "0.005"],
        },
        {"maturity": "2030-13-01"},
    ],
)
def test_a_row_that_is_not_one_rate_form_is_refused(change):
    with pytest.raises(ValidationError):
        Facility(**{**A, **change})


# --- the engine takes a schedule (Task 2) ------------------------------------------------------
# Copied from tests/test_cpos_launch.py (BASE, PATHS): tests is not a package, so not importable.
_BASE = {
    "revenue": "1000",
    "ebitda": "300",
    "interest": "36",
    "taxes": "20",
    "wc": "10",
    "capex": "40",
    "fcf": "194",
    "debt": "600",
    "cash": "100",
    "undrawn": "50",
}
_PATHS = {
    "revenue_growth": ("0.05", "0.04", "0.03"),
    "ebitda_margin": ("0.30", "0.31", "0.32"),
    "capex_pct_revenue": ("0.04", "0.04", "0.04"),
    "tax_wc_pct_revenue": ("0.10", "0.10", "0.10"),
    "interest_rate": ("0.06", "0.06", "0.06"),
    "dividends": ("20", "20", "20"),
    "debt_repayment": ("50", "50", "50"),
}
OPERANDS = cp2g.Operands(**{k: cp2g.Val(D(v), None) for k, v in _BASE.items()})
DRIVERS = cp2g.Drivers(**{k: tuple(D(x) for x in v) for k, v in _PATHS.items()})
TOTALS = ((D("34.5"), D("20")), (D("31.8"), D("20")), (D("27.6"), D("20")))


def test_scheduled_interest_and_repayment_replace_the_two_drivers():
    years = cp2g.forecast(operands=OPERANDS, drivers=DRIVERS, shock=None, schedule=TOTALS).years
    assert [y.interest.amount for y in years] == [D("34.5"), D("31.8"), D("27.6")]
    assert [y.closing_debt.amount for y in years] == [D("580"), D("560"), D("540")]


def test_scheduled_year_one_free_cash_flow_and_cash():
    y = cp2g.forecast(operands=OPERANDS, drivers=DRIVERS, shock=None, schedule=TOTALS).years[0]
    revenue = Fraction(1000) * (1 + Fraction("0.05"))
    fcf = (
        revenue * Fraction("0.30")
        - Fraction("34.5")
        - revenue * Fraction("0.10")
        - revenue * Fraction("0.04")
    )
    assert Fraction(y.fcf.amount) == fcf
    assert Fraction(y.closing_cash.amount) == 100 + fcf - 20 - 20


def test_the_downside_rate_increase_scales_scheduled_interest():
    years = cp2g.forecast(
        operands=OPERANDS, drivers=DRIVERS, shock=(D("0"), D("0.10")), schedule=TOTALS
    ).years
    assert [y.interest.amount for y in years] == [D("37.95"), D("34.98"), D("30.36")]


def test_no_schedule_uses_the_two_drivers():
    year = cp2g.forecast(operands=OPERANDS, drivers=DRIVERS, shock=None, schedule=None).years[0]
    assert year.interest.amount == D("36")  # 600 x 0.06
    assert year.closing_debt.amount == D("550")  # 600 - 50


def test_missing_base_debt_stays_missing_with_its_reason():
    ops = replace(OPERANDS, debt=cp2g.Val(None, "why"))
    y = cp2g.forecast(operands=ops, drivers=DRIVERS, shock=None, schedule=TOTALS).years[0]
    assert (y.interest.amount, y.interest.reason) == (None, "why")
    assert y.closing_debt.amount is None


# --- the inputs block states facilities (Task 3) ------------------------------------------------
# A local builder modelled on forecast_block in tests/test_cpos_launch.py (not importable).
_CP1 = " ".join(_BASE.values()) + " 400 150 6.00% 3.00% 1.00%"


def _block(**changes) -> bytes:
    inputs = {
        "schema_version": "cpos-forecast-inputs/1",
        "base": {k: {"amount": v, "reason": None} for k, v in _BASE.items()},
        "base_drivers": {
            name: {
                "values": list(v),
                "category": "Analyst Interpretation",
                "rationale": "Synthetic.",
                "limitation": None,
            }
            for name, v in _PATHS.items()
        },
        "downside_shock": {"ebitda_decline": "0.20", "rate_increase": "0.10"},
        "years": [
            {"year": 2025 + i, "start": f"{2025 + i}-04-01", "end": f"{2026 + i}-03-31"}
            for i in range(3)
        ],
        "scope_limits": ["Synthetic; not analytical review."],
        **changes,
    }
    return (
        f"### Forecast inputs (machine-readable)\n\n```json\n{json.dumps(inputs)}\n```\n".encode()
    )


def _exact(cp1: str = _CP1, **changes) -> dict:
    from deploy_workflow.owners.cpos_forecast import model_files

    return json.loads(model_files(cp1.encode(), _block(**changes))["forecast_exact.json"])


def _refusal(cp1: str = _CP1, source: str = "CP-2G", **changes) -> str:
    from deploy_workflow.owners import cpos_forecast

    with pytest.raises(ValueError) as caught:
        cpos_forecast.parse(_block(**changes).decode(), cp1, source)
    return str(caught.value)


def test_a_block_with_facilities_publishes_the_answer_key():
    exact = _exact(facilities=[A, B])
    ref = exact["outputs"]["REFERENCE"]["years"]
    # 50 of base debt is outside the facilities and bears the analyst's 6%: 3 on top of 34.5 etc.
    assert [D(y["interest"]["amount"]) for y in ref] == [D("37.5"), D("34.8"), D("30.6")]
    assert [D(y["closing_debt"]["amount"]) for y in ref] == [D("580"), D("560"), D("540")]
    assert D(exact["unallocated_debt"]["amount"]) == D("50")
    assert exact["unallocated_debt"]["reason"] is None
    assert D(exact["facility_schedule"][1]["years"][2]["rate"]) == D("0.04")
    assert exact["facility_schedule"][1]["years"][2]["year"] == 2027
    assert [f["name"] for f in exact["facility_schedule"]] == ["Notes", "Term loan"]
    assert exact["facilities"][0]["balance"] == "400"
    limits = exact["scope_limits"]
    assert limits[1] == "Synthetic; not analytical review."
    assert limits[2] == (
        "Cash interest on the stated facilities and scheduled repayment are computed from the "
        "facility terms the CP-2G handoff stated; the analyst's repayment assumption is not used."
    )
    assert limits[3] == (
        "Debt of 50 is not in a stated facility; it bears interest at the analyst's assumed rate "
        "and is not repaid in this forecast."
    )


def _interest(exact: dict, case: str) -> list[Decimal]:
    return [D(y["interest"]["amount"]) for y in exact["outputs"][case]["years"]]


def test_debt_outside_the_facilities_bears_the_analyst_rate_in_every_case():
    exact = _exact(
        facilities=[A, B],
        downside_drivers={"interest_rate": {**_driver("interest_rate"), "values": ["0.08"] * 3}},
    )
    assert _interest(exact, "REFERENCE") == [D("37.5"), D("34.8"), D("30.6")]
    assert _interest(exact, "DOWNSIDE") == [D("41.25"), D("38.28"), D("33.66")]
    assert _interest(exact, "DOWNSIDE_DRIVERS") == [D("38.5"), D("35.8"), D("31.6")]


def test_no_remainder_adds_no_interest():
    # hand-computed on opening balances: 400 at 6% + 200 at 7%/6%/4%, A amortising 20 a year
    rows = [A, {**B, "balance": "200"}]
    exact = _exact(_CP1 + " 200", facilities=rows)
    assert _interest(exact, "REFERENCE") == [D("38"), D("34.8"), D("29.6")]


def test_balances_above_base_debt_add_no_remainder_interest():
    rows = [{**A, "balance": "500"}, {**B, "balance": "150"}]
    exact = _exact(_CP1 + " 500", facilities=rows)
    # 500 at 6% (480, 460 after amortisation) + 150 at 7%/6%/4%
    assert _interest(exact, "REFERENCE") == [D("40.5"), D("37.8"), D("33.6")]


def test_a_block_without_facilities_publishes_no_facility_key():
    # The handoff text differs (null vs absent), so its hash in `consumed` does; all else is equal.
    from deploy_workflow.owners.cpos_forecast import model_files

    cp1 = _CP1.encode()
    plain = json.loads(model_files(cp1, _block())["forecast_exact.json"])
    nulled = json.loads(model_files(cp1, _block(facilities=None))["forecast_exact.json"])
    plain["consumed"] = nulled["consumed"] = None
    assert plain == nulled
    assert b"facilit" not in model_files(cp1, _block())["forecast_exact.json"]
    assert plain["scope_limits"][1:] == ["Synthetic; not analytical review."]


def test_missing_base_debt_says_so():
    base = {k: {"amount": v, "reason": None} for k, v in _BASE.items()}
    base["debt"] = {"amount": None, "reason": "CP-1 gives no debt"}
    exact = _exact(base=base, facilities=[A])
    assert exact["unallocated_debt"] == {"amount": None, "reason": "CP-1 gives no debt"}
    assert (
        "Base debt is missing, so debt outside the stated facilities is not known."
        in exact["scope_limits"]
    )


@pytest.mark.parametrize(
    "rows, cp1, message",
    [
        (
            [{**A, "fixed_rate_pct": "6.0"}],
            _CP1,
            "CP-2G: facility Notes fixed_rate_pct 6.0% is not printed in CP-1",
        ),
        (
            [{**A, "balance": "999"}],
            _CP1,
            "CP-2G: facility Notes balance 999 is not printed in CP-1",
        ),
        (
            [B, {**B, "name": "T2", "floor_pct": "2.50"}],
            _CP1,
            "CP-2G: facility T2 floor_pct 2.50% is not printed in CP-1",
        ),
        (
            [{**A, "balance": "400000"}],
            _CP1 + " 400000",
            (
                "CP-2G: facility balances total 400000, more than 1.25 times base debt 600; "
                "check the unit"
            ),
        ),
    ],
)
def test_refusals(rows, cp1, message):
    assert _refusal(cp1, facilities=rows) == message


def test_the_balance_check_is_one_and_a_quarter_inclusive():
    exact = _exact(_CP1 + " 750", facilities=[{**A, "balance": "750"}])
    assert D(exact["unallocated_debt"]["amount"]) == D("-150")
    assert "more than 1.25 times" in _refusal(_CP1 + " 751", facilities=[{**A, "balance": "751"}])


@pytest.mark.parametrize("case", ["upside_drivers", "downside_drivers"])
def test_a_case_override_of_debt_repayment_is_refused(case):
    override = {"debt_repayment": {**_driver("debt_repayment")}}
    message = _refusal(facilities=[A], **{case: override})
    assert message == (
        f"CP-2G: {case} states debt_repayment, which is not used when facilities are stated"
    )


@pytest.mark.parametrize("case", ["upside_drivers", "downside_drivers"])
def test_a_case_override_of_interest_rate_is_accepted_with_facilities(case):
    assert _exact(facilities=[A], **{case: {"interest_rate": _driver("interest_rate")}})


def _driver(name: str) -> dict:
    return {
        "values": list(_PATHS[name]),
        "category": "Analyst Interpretation",
        "rationale": "Synthetic.",
        "limitation": None,
    }


def test_a_case_override_of_another_driver_is_allowed_with_facilities():
    exact = _exact(facilities=[A], upside_drivers={"dividends": _driver("dividends")})
    assert "UPSIDE" in exact["outputs"]


def test_cp1s_layer1_block_states_no_facilities():
    message = _refusal(source="CP-1", downside_shock=None, facilities=[A])
    assert message == "CP-1: a layer-1 forecast states no facilities"


def test_duplicate_names_are_refused():
    assert "facility names must be unique" in _refusal(facilities=[A, {**B, "name": "Notes"}])


def test_a_facility_name_is_trimmed_and_unique_ignoring_case_and_edges():
    for name in (" Notes", "Notes ", "   "):
        with pytest.raises(ValidationError, match="must not start or end with whitespace"):
            Facility(**{**A, "name": name})
    assert "facility names must be unique" in _refusal(facilities=[B, {**B, "name": "TERM LOAN"}])


@pytest.mark.parametrize(
    "rows, bound",
    [
        ([], "facilities: Tuple should have at least 1 item"),
        ([{**A, "name": f"F{i}"} for i in range(41)], "facilities: Tuple should have at most 40"),
    ],
)
def test_one_to_forty_facilities(rows, bound):
    assert bound in _refusal(facilities=rows)


MATURES_2026 = (
    "Notes matures in FY2026 and is assumed refinanced; no repayment at maturity is modelled."
)


def test_a_maturity_inside_the_forecast_is_named():
    limits = _exact(facilities=[{**A, "maturity": "2026-09-30"}])["scope_limits"]
    assert MATURES_2026 in limits


def test_a_maturity_before_the_forecast_is_named_in_the_first_year_and_a_late_one_is_not():
    rows = [
        {**A, "maturity": "2020-01-01"},
        {**B, "maturity": "2028-03-31"},
    ]
    limits = _exact(facilities=rows)["scope_limits"]
    assert (
        "Notes has a stated maturity of 2020-01-01, before the forecast; it is assumed "
        "refinanced and no repayment at maturity is modelled." in limits
    )
    assert (
        "Term loan matures in FY2027 and is assumed refinanced; "
        "no repayment at maturity is modelled." in limits
    )
    after = _exact(facilities=[{**A, "maturity": "2028-04-01"}])["scope_limits"]
    assert not any("matures in" in s for s in after)


def test_a_maturity_is_a_dated_form_only():
    with pytest.raises(ValidationError):
        Facility(**{**A, "maturity": "20300101"})


def test_a_maturity_that_is_not_a_calendar_date_names_the_field():
    with pytest.raises(ValidationError, match="maturity 2030-13-01 is not a calendar date"):
        Facility(**{**A, "maturity": "2030-13-01"})


# --- fix round 1 --------------------------------------------------------------------------------
def test_scheduled_repayments_above_base_debt_are_refused():
    row = {**A, "balance": "700", "annual_amortisation": "300"}
    message = _refusal(_CP1 + " 700", facilities=[row])
    assert message == "CP-2G: scheduled repayments total 700, more than base debt 600"


def test_scheduled_repayments_equal_to_base_debt_are_accepted():
    row = {**A, "balance": "700", "annual_amortisation": "200"}
    exact = _exact(_CP1 + " 700", facilities=[row])
    assert D(exact["unallocated_debt"]["amount"]) == D("-100")


def test_balances_above_base_debt_name_the_excess_in_a_scope_limit():
    rows = [{**A, "balance": "500"}, {**B, "balance": "150"}]
    exact = _exact(_CP1 + " 500", facilities=rows)
    assert D(exact["unallocated_debt"]["amount"]) == D("-50")
    limits = exact["scope_limits"]
    assert limits[3] == (
        "Stated facility balances exceed base debt by 50; interest is computed on the stated "
        "balances."
    )


@pytest.mark.parametrize(
    "reference, year, rate",
    [(["1", "1", "1"], 1, "1.03"), (["0.04", "0.5", "0.04"], 2, "0.53")],
)
def test_a_floating_all_in_rate_above_thirty_percent_is_refused(reference, year, rate):
    with pytest.raises(ValidationError) as caught:
        Facility(**{**B, "floor_pct": None, "reference_rate": reference})
    assert (
        f"all-in rate {rate} in forecast year {year} is outside 0 to 0.30; reference_rate is a "
        "decimal fraction (0.04 is 4%)"
    ) in str(caught.value)


def test_a_negative_all_in_rate_is_refused_and_a_negative_reference_rate_above_zero_is_not():
    with pytest.raises(ValidationError, match="all-in rate -0.47 in forecast year 1 is outside"):
        Facility(**{**B, "floor_pct": None, "reference_rate": ["-0.5", "-0.5", "-0.5"]})
    ok = Facility(**{**B, "floor_pct": None, "reference_rate": ["-0.01", "0", "0.27"]})
    assert [y.rate for y in schedule([ok]).rows[0]] == [D("0.02"), D("0.03"), D("0.30")]


def test_a_rate_term_is_a_printed_percent():
    # "6.00" appears in CP-1 only as part of 16.00 and as a bare number: neither is a percent
    for cp1 in (_CP1.replace("6.00%", "16.00%"), _CP1.replace("6.00%", "6.00")):
        assert "fixed_rate_pct 6.00% is not printed" in _refusal(cp1, facilities=[A])
    spaced = _CP1.replace("6.00%", "6.00 %")
    assert _exact(spaced, facilities=[A])["facilities"][0]["fixed_rate_pct"] == "6.00"


def test_forecast_states_exactly_three_schedule_pairs():
    with pytest.raises(ValueError, match="exactly three"):
        cp2g.forecast(operands=OPERANDS, drivers=DRIVERS, shock=None, schedule=TOTALS[:2])


def test_a_block_without_facilities_is_byte_identical_to_main():
    import hashlib

    from deploy_workflow.owners.cpos_forecast import model_files

    doc = {
        "schema_version": "cpos-forecast-inputs/1",
        "base": {k: {"amount": v, "reason": None} for k, v in _BASE.items()},
        "base_drivers": {n: _driver(n) for n in _PATHS},
        "downside_shock": {"ebitda_decline": "0.20", "rate_increase": "0.10"},
        "upside_drivers": {
            "revenue_growth": {**_driver("revenue_growth"), "values": ["0.07", "0.06", "0.05"]}
        },
        "years": [
            {"year": 2025 + i, "start": f"{2025 + i}-04-01", "end": f"{2026 + i}-03-31"}
            for i in range(3)
        ],
        "scope_limits": ["Synthetic; not analytical review."],
    }
    handoff = f"### Forecast inputs (machine-readable)\n\n```json\n{json.dumps(doc)}\n```\n"
    files = model_files(" ".join(_BASE.values()).encode(), handoff.encode())
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode())
        digest.update(files[name])
    assert digest.hexdigest() == "e5017389abc2c878a0b0bae323a50bcbadf35c3a08f676f277c1505b9d047089"


# --- boundaries carried from review -------------------------------------------------------------
def test_a_floating_all_in_rate_of_exactly_zero_and_of_exactly_thirty_percent_is_accepted():
    zero = Facility(**{**B, "floor_pct": None, "reference_rate": ["-0.03", "-0.03", "-0.03"]})
    assert [y.rate for y in schedule([zero]).rows[0]] == [D("0")] * 3
    top = Facility(**{**B, "floor_pct": None, "reference_rate": ["0.27", "0.27", "0.27"]})
    assert [y.rate for y in schedule([top]).rows[0]] == [D("0.30")] * 3


def test_balances_equal_to_base_debt_state_zero_unallocated_and_no_limit_either_way():
    rows = [{**A, "balance": "450"}, {**B, "balance": "150"}]
    exact = _exact(_CP1 + " 450", facilities=rows)
    assert D(exact["unallocated_debt"]["amount"]) == 0
    assert exact["unallocated_debt"]["reason"] is None
    assert not any("is not in a stated facility" in s for s in exact["scope_limits"])
    assert not any("exceed base debt" in s for s in exact["scope_limits"])


def test_a_maturity_on_the_first_forecast_years_start_is_inside_the_forecast():
    limits = _exact(facilities=[{**A, "maturity": "2025-04-01"}])["scope_limits"]
    assert (
        "Notes matures in FY2025 and is assumed refinanced; no repayment at maturity is modelled."
        in limits
    )
    assert not any("before the forecast" in s for s in limits)
