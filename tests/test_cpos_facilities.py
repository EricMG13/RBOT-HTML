"""CP-2G facility schedule: stated terms to interest and repayment (hand-computed answer key)."""

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


def test_no_schedule_is_todays_forecast():
    assert cp2g.forecast(
        operands=OPERANDS, drivers=DRIVERS, shock=None, schedule=None
    ) == cp2g.forecast(operands=OPERANDS, drivers=DRIVERS, shock=None)


def test_missing_base_debt_stays_missing_with_its_reason():
    ops = replace(OPERANDS, debt=cp2g.Val(None, "why"))
    y = cp2g.forecast(operands=ops, drivers=DRIVERS, shock=None, schedule=TOTALS).years[0]
    assert (y.interest.amount, y.interest.reason) == (None, "why")
    assert y.closing_debt.amount is None
