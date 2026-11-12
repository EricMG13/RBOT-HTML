"""`scale` at the door of `parse`: a block may state amounts in USD thousands."""

import json
import re
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st
from test_cpos_launch import PATHS, forecast_block
from test_cpos_periods import BASE, CP1, NAMED, cell

from deploy_workflow.owners import cpos_forecast, cpos_periods
from deploy_workflow.owners.cpos_forecast import model_files, parse

CP1_K = """| Reported label | Q3 2025 | Q3 2024 revised | 9M 2025 | 9M 2024 | FY2024 | FY2023 \
| Locator |
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
"""

CP1_K2 = """| Reported label | H1 2025 | H1 2024 | FY2024 | Locator |
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
"""


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
    "undrawn": {
        "amount": None,
        "reason": "CP-1 prints revolver availability in USD millions, not in this block's unit.",
    },
}
K2_PATHS = {
    "revenue_growth": ("0.10",) * 3,
    "ebitda_margin": ("0.25",) * 3,
    "capex_pct_revenue": ("0.05",) * 3,
    "tax_wc_pct_revenue": ("0.02",) * 3,
    "interest_rate": ("0.065",) * 3,
    "dividends": ("0",) * 3,
    "debt_repayment": ("22873",) * 3,
}


def _fixed(name, balance, rate, amortisation):
    return {
        "name": name,
        "balance": balance,
        "fixed_rate_pct": rate,
        "spread_pct": None,
        "floor_pct": None,
        "reference_rate": None,
        "annual_amortisation": amortisation,
        "maturity": None,
    }


FAC = [
    _fixed("Term Loan Facility", "995000", "6.25", "10000"),
    _fixed("Notes", "500000", "6.00", None),
]

K = {k: str(int(v) * 1000) for k, v in BASE.items()}
K_PATHS = {**PATHS, "dividends": ("20000",) * 3, "debt_repayment": ("50000",) * 3}


def drivers(paths):
    return {
        n: {
            "values": list(v),
            "category": "Analyst Interpretation",
            "rationale": "Synthetic.",
            "limitation": None,
        }
        for n, v in paths.items()
    }


def named_base(amounts):
    return {
        k: {"amount": v, "reason": None, "row": NAMED[k][0], "period": NAMED[k][1]}
        for k, v in amounts.items()
    }


def block_k(**changes):
    return forecast_block(
        **{"scale": 1000, "base": named_base(K), "base_drivers": drivers(K_PATHS), **changes}
    )


def block_m(**changes):
    return forecast_block(**{"base": named_base(BASE), **changes})


def block_k2(**changes):
    return forecast_block(
        **{"scale": 1000, "base": K2_BASE, "base_drivers": drivers(K2_PATHS), **changes}
    )


def test_scale_1000_states_thousands_and_parses_to_millions():  # AK-3
    inputs = parse(block_k(), CP1_K)
    assert {k: o.amount for k, o in inputs.base.items()} == BASE
    assert inputs.base_drivers.dividends.values == ("20", "20", "20")
    assert inputs.base_drivers.debt_repayment.values == ("50", "50", "50")
    assert inputs.scale == 1000


def test_a_decimal_and_a_bracketed_thousands_cell_parse_exactly():  # Review Focus 1, 2; AK-4
    base = parse(block_k2(), CP1_K2).base
    assert {k: o.amount for k, o in base.items() if o.amount} == {
        "revenue": "2620.995",
        "ebitda": "667.621",
        "interest": "100.25",
        "capex": "139.75",
        "debt": "1534.356",
        "cash": "175.5095",
    }


@pytest.mark.parametrize(
    "operand, message",
    [  # AK-6
        (
            {"cash": {**K2_BASE["cash"], "amount": "175.5095"}},
            (
                "CP-2G: base cash 175.5095 is not an amount in thousands as CP-1 "
                "prints it (scale 1000): at most nine digits and one decimal place, no separators"
            ),
        ),
        (
            {"cash": {**K2_BASE["cash"], "amount": "175509.55"}},
            "CP-2G: base cash 175509.55 is not an amount in thousands",
        ),
        (
            {"revenue": {**K2_BASE["revenue"], "amount": "2,620,995"}},
            "CP-2G: base revenue 2,620,995 is not an amount in thousands",
        ),
        (
            {"revenue": {**K2_BASE["revenue"], "amount": "1234567890"}},
            "CP-2G: base revenue 1234567890 is not an amount in thousands",
        ),
        (
            {"revenue": {**K2_BASE["revenue"], "amount": "2621"}},
            (
                "CP-2G: base revenue 2621 is not CP-1's cell at row `Total revenue`, "
                "period `FY2024` (2,620,995)"
            ),
        ),
    ],
)
def test_refusals_at_scale_1000(operand, message):
    with pytest.raises(ValueError) as caught:
        parse(block_k2(base={**K2_BASE, **operand}), CP1_K2)
    assert message in str(caught.value)


@pytest.mark.parametrize("scale", ["1000", 100, 0, -1000, [1000], {"x": 1}])
def test_a_scale_that_is_not_1_or_1000_is_refused(scale):
    with pytest.raises(ValueError) as caught:
        parse(block_k(scale=scale), CP1_K)
    assert (
        str(caught.value)
        == "CP-2G: `scale` must be 1 (CP-1 prints USD millions) or 1000 (USD thousands)"
    )


def test_a_millions_block_does_not_read_a_thousands_handoff():
    with pytest.raises(ValueError, match="CP-2G: base revenue 1000 is not CP-1's cell"):
        parse(block_m(), CP1_K)
    with pytest.raises(ValueError, match="CP-2G: base revenue 1000000 is not CP-1's cell"):
        parse(block_k(), CP1)


def test_a_block_with_scale_and_unnamed_rows():  # Review Focus 4
    base = {k: {"amount": v, "reason": None} for k, v in K.items()}
    files = model_files(CP1_K.encode(), block_k(base=base).encode(), history=True)
    first = json.loads(files["forecast_exact.json"])["outputs"]["REFERENCE"]["years"][0]
    assert first["revenue"]["amount"] == "1050"
    record = json.loads(files["calculation.json"])["history"]
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason": cpos_periods.NOT_NAMED}
    with pytest.raises(ValueError, match="CP-2G: base revenue 1000000 is not printed in CP-1"):
        parse(block_k(base=base), CP1)


def test_facilities_at_scale_1000_are_divided_and_checked_against_the_divided_debt():  # AK-5
    exact = json.loads(
        model_files(CP1_K2.encode(), block_k2(facilities=FAC).encode())["forecast_exact.json"]
    )
    assert [f["balance"] for f in exact["facilities"]] == ["995", "500"]
    assert exact["facilities"][0]["annual_amortisation"] == "10"
    assert exact["unallocated_debt"]["amount"] == "39.356"
    first = exact["outputs"]["REFERENCE"]["years"][0]
    assert first["interest"]["amount"] == "94.74564" and first["repayment"]["amount"] == "10"
    with pytest.raises(ValueError) as caught:
        parse(block_k2(facilities=[{**FAC[0], "balance": "1534356"}, FAC[1]]), CP1_K2)
    assert str(caught.value) == (
        "CP-2G: facility balances total 2034.356, more than 1.25 times base debt 1534.356, "
        "in USD millions after dividing by scale 1000; check the unit"
    )
    with pytest.raises(
        ValueError, match="CP-2G: facility Notes balance 500 is not printed in CP-1"
    ):
        parse(block_k2(facilities=[FAC[0], {**FAC[1], "balance": "500"}]), CP1_K2)


@given(st.from_regex(r"-?[0-9]{1,9}(\.[0-9])?", fullmatch=True))
def test_the_division_is_exact_and_fits_the_millions_pattern(text):
    document = {"scale": 1000, "base": {"revenue": {"amount": text, "reason": None}}}
    assert cpos_forecast._to_millions(document, "CP-2G") == {"base revenue": text}
    millions = document["base"]["revenue"]["amount"]
    assert Fraction(millions) * 1000 == Fraction(text)
    assert re.fullmatch(r"-?[0-9]{1,6}(\.[0-9]{1,4})?", millions)
