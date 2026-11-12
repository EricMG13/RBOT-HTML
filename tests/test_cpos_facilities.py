"""CP-2G facility schedule: stated terms to interest and repayment (hand-computed answer key)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

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
