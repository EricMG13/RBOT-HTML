"""`scale` at the door of `parse`: a block may state amounts in USD thousands."""

import json
import re
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st
from test_cpos_launch import PATHS, forecast_block
from test_cpos_periods import BASE, CP1, NAMED, OPERANDS, cell

from deploy_workflow.owners import cpos_forecast, cpos_periods
from deploy_workflow.owners.cpos_forecast import SCALE_LIMIT, model_files, parse

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


def test_the_thousands_handoff_publishes_the_millions_figures():  # AK-1, AK-3
    k = model_files(CP1_K.encode(), block_k().encode(), history=True)
    m = model_files(CP1.encode(), block_m().encode(), history=True)
    exact_k, exact_m = (json.loads(f["forecast_exact.json"]) for f in (k, m))
    first = exact_k["outputs"]["REFERENCE"]["years"][0]
    key = {
        "revenue": "1050",
        "ebitda": "315",
        "interest": "36",
        "tax_wc": "105",
        "capex": "42",
        "cfo": "174",
        "fcf": "132",
        "closing_debt": "550",
        "closing_cash": "162",
        "net_debt": "388",
        "liquidity": "212",
        "dividends": "20",
        "repayment": "50",
    }
    assert {n: first[n]["amount"] for n in key} == key
    assert first["coverage"]["amount"] == "8.75" and first["fcf_to_debt"]["amount"] == "0.24"
    down = exact_k["outputs"]["DOWNSIDE"]["years"][0]
    assert [down[n]["amount"] for n in ("ebitda", "interest", "fcf", "closing_cash")] == [
        "252",
        "39.6",
        "65.4",
        "95.4",
    ]
    for name in ("base", "reference_drivers", "outputs"):
        assert exact_k[name] == exact_m[name], name
    assert (exact_k["scale"], exact_k["units"]) == (1000, "USD millions")
    assert "scale" not in exact_m and "units" not in exact_m
    assert SCALE_LIMIT not in exact_m["scope_limits"]
    assert exact_k["scope_limits"][:3] == [
        cpos_forecast.LIMIT,
        SCALE_LIMIT,
        "Synthetic; not analytical review.",
    ]
    assert (
        json.loads(k["calculation.json"])["history"] == json.loads(m["calculation.json"])["history"]
    )


@pytest.mark.parametrize(
    "key, ytd, pytd, fy, ltm",
    [
        ("revenue", "780", "720", "1000", "1060"),
        ("interest", "27", "28", "36", "35"),
        ("tax_wc", "27", "23", "30", "34"),
        ("fcf", "153", "136", "194", "211"),
        ("closing_debt", "590", "620", "600", "590"),
        ("liquidity", "170", "140", "150", "170"),
    ],
)
def test_history_at_scale_1000_is_the_answer_key_in_millions(key, ytd, pytd, fy, ltm):
    record = cpos_periods.history(cpos_forecast._tables(CP1_K), OPERANDS, named=NAMED, scale=1000)
    assert [cell(record, c, key)["amount"] for c in ("YTD", "PYTD", "FY2024", "LTM")] == [
        ytd,
        pytd,
        fy,
        ltm,
    ]


def test_ratios_are_scale_free():
    record = cpos_periods.history(cpos_forecast._tables(CP1_K), OPERANDS, named=NAMED, scale=1000)
    leverage = cell(record, "LTM", "total_leverage")["amount"]
    coverage = cell(record, "LTM", "coverage")["amount"]
    assert abs(Fraction(leverage) - Fraction(590, 324)) < Fraction(1, 10**12)
    assert abs(Fraction(coverage) - Fraction(324, 35)) < Fraction(1, 10**12)


def test_the_realistic_thousands_handoff():  # AK-4
    files = model_files(CP1_K2.encode(), block_k2().encode(), history=True)
    exact = json.loads(files["forecast_exact.json"])
    first = exact["outputs"]["REFERENCE"]["years"][0]
    key = {
        "revenue": "2883.0945",
        "ebitda": "720.773625",
        "interest": "99.73314",
        "tax_wc": "57.66189",
        "capex": "144.154725",
        "cfo": "563.378595",
        "fcf": "419.22387",
        "closing_debt": "1511.483",
        "closing_cash": "571.86037",
        "net_debt": "939.62263",
        "repayment": "22.873",
    }
    assert {n: first[n]["amount"] for n in key} == key
    assert first["liquidity"] == {"amount": None, "reason": K2_BASE["undrawn"]["reason"]}
    leverage = Fraction(first["total_leverage"]["amount"])
    assert abs(leverage - Fraction(12091864, 5766189)) < Fraction(1, 10**30)
    down = exact["outputs"]["DOWNSIDE"]["years"][0]
    assert [down[n]["amount"] for n in ("ebitda", "interest", "fcf", "closing_cash")] == [
        "576.6189",
        "109.706454",
        "265.095831",
        "417.732331",
    ]
    record = json.loads(files["calculation.json"])["history"]
    for name, *want in [
        ("revenue", "1421.519", "1264.478", "2620.995", "2778.036"),
        ("ebitda", "370.1", "310.479", "667.621", "727.242"),
        ("interest", "52", "49.75", "100.25", "102.5"),
        ("capex", "71.5", "60.25", "139.75", "151"),
    ]:
        assert [cell(record, c, name)["amount"] for c in ("YTD", "PYTD", "FY2024", "LTM")] == want
    assert cell(record, "YTD", "closing_cash")["amount"] == "175.5095"
    assert cell(record, "FY2024", "closing_debt")["amount"] == "1555.597"
    ltm = Fraction(cell(record, "LTM", "total_leverage")["amount"])
    assert abs(ltm - Fraction(1534356, 727242)) < Fraction(1, 10**12)


def test_a_block_with_scale_one_is_the_block_without_it_plus_the_units():
    stated = json.loads(model_files(CP1.encode(), block_m(scale=1).encode())["forecast_exact.json"])
    absent = json.loads(model_files(CP1.encode(), block_m().encode())["forecast_exact.json"])
    assert (stated.pop("scale"), stated.pop("units")) == (1, "USD millions")
    stated["consumed"] = absent["consumed"]  # the handoff's hash differs by the one key
    assert stated == absent


def test_layer_one_at_scale_1000():
    block = json.loads(block_k().split("```json\n")[1].split("\n```")[0])
    block["downside_shock"] = None
    text = CP1_K + "\n### Forecast inputs (machine-readable)\n\n```json\n"
    text += json.dumps(block) + "\n```\n"
    files = model_files(text.encode(), text.encode(), "CP-1", history=True)
    exact = json.loads(files["forecast_exact.json"])
    assert exact["outputs"]["REFERENCE"]["years"][0]["closing_cash"]["amount"] == "162"
    assert exact["scope_limits"][:2] == [cpos_forecast.LAYER1_LIMIT, SCALE_LIMIT]
    assert (
        cell(json.loads(files["calculation.json"])["history"], "LTM", "revenue")["amount"] == "1060"
    )


CHART_ROW = {
    "amount": "618.5",
    "reason": None,
    "row": "H1 2025",
    "period": "Undrawn committed facilities",
}
NO_BASE = {k: {"amount": None, "reason": "not used"} for k in K2_BASE}


def test_a_millions_chart_row_in_a_thousands_block_is_refused():  # AK-6
    with pytest.raises(ValueError) as caught:
        parse(block_k2(base={**K2_BASE, "undrawn": CHART_ROW}), CP1_K2)
    assert str(caught.value) == (
        "CP-2G: base undrawn: row `H1 2025` states its Reporting unit as `US$m`, not the "
        "block's unit (USD thousands, scale 1000); state a reason instead of an amount"
    )


def test_the_same_row_is_read_by_a_millions_block():
    base = NO_BASE | {"undrawn": CHART_ROW}
    assert parse(forecast_block(scale=1, base=base), CP1_K2).base["undrawn"].amount == "618.5"


def test_a_thousands_unit_cell_refuses_a_millions_block():
    cp1 = CP1_K2.replace("| US$m |", "| US$ thousands |")
    base = NO_BASE | {"undrawn": CHART_ROW}
    with pytest.raises(ValueError, match="not the block's unit \\(USD millions, scale 1\\)"):
        parse(forecast_block(scale=1, base=base), cp1)


def test_a_block_without_scale_is_not_checked_for_units():
    base = NO_BASE | {"undrawn": CHART_ROW}
    assert parse(forecast_block(base=base), CP1_K2.replace("| US$m |", "| US$ thousands |"))


def _extra(table):
    return CP1_K2 + "\n" + table


def _revolver(row, period, **changes):
    return block_k2(base={**K2_BASE, "undrawn": _at("618.5", row, period)} | changes)


def test_another_cell_of_the_row_naming_the_other_unit_is_refused():  # widened B7 (b)
    with pytest.raises(ValueError) as caught:
        parse(_revolver("Revolver availability", "H1 2025"), CP1_K2)
    assert str(caught.value) == (
        "CP-2G: base undrawn: row `Revolver availability` states its Unit and terms / evidence "
        "as `US$ million`, not the block's unit (USD thousands, scale 1000); "
        "state a reason instead of an amount"
    )


def test_the_named_columns_header_naming_the_other_unit_is_refused():  # widened B7 (c)
    cp1 = _extra(
        "| Item | H1 2025 (US$m) | Notes |\n| --- | --- | --- |\n| Revolver | 618.5 | x |\n"
    )
    with pytest.raises(ValueError, match="states its period header as `H1 2025 \\(US\\$m\\)`"):
        parse(_revolver("Revolver", "H1 2025 (US$m)"), cp1)


def test_the_first_header_cell_naming_the_other_unit_is_refused():  # widened B7 (d)
    cp1 = _extra(
        "| Item (US$ million) | H1 2025 | Notes |\n| --- | --- | --- |\n| Revolver | 618.5 | x |\n"
    )
    with pytest.raises(
        ValueError, match="states its first header cell as `Item \\(US\\$ million\\)`"
    ):
        parse(_revolver("Revolver", "H1 2025"), cp1)


def test_a_row_naming_both_units_is_accepted():  # widened B7 (e)
    cp1 = _extra(
        "| Item | H1 2025 | Basis | Unit |\n| --- | --- | --- | --- |\n"
        "| Revolver | 618.5 | US$ million facility | US$ thousands |\n"
    )
    assert parse(_revolver("Revolver", "H1 2025"), cp1).base["undrawn"].amount == "0.6185"


def test_a_row_naming_no_unit_is_accepted():  # widened B7 (f)
    cp1 = _extra("| Item | H1 2025 | Notes |\n| --- | --- | --- |\n| Revolver | 618.5 | x |\n")
    assert parse(_revolver("Revolver", "H1 2025"), cp1).base["undrawn"].amount == "0.6185"


def test_the_amount_cell_itself_is_never_read_for_unit_words():
    cp1 = _extra("| Item | H1 2025 | Notes |\n| --- | --- | --- |\n| Revolver | 618.5 | x |\n")
    assert parse(_revolver("Revolver", "H1 2025"), cp1)
    assert (
        cpos_forecast._unit_problem(
            cp1.replace("| 618.5 |", "| 618.5 million |"),
            "undrawn",
            cpos_forecast.Operand(amount="0.6185", reason=None, row="Revolver", period="H1 2025"),
            1000,
        )
        is None
    )


def test_a_block_without_scale_is_not_checked_for_the_widened_rule():  # widened B7 (g)
    cp1 = (
        CP1 + "\n| Item | FY2024 | Unit |\n| --- | --- | --- |\n| Revolver | 50 | US$ thousands |\n"
    )
    base = named_base(BASE) | {"undrawn": _at("50", "Revolver", "FY2024")}
    assert parse(block_m(base=base), cp1).base["undrawn"].amount == "50"
    with pytest.raises(ValueError, match="states its Unit as `US\\$ thousands`"):
        parse(block_m(base=base, scale=1), cp1)


@pytest.mark.parametrize(
    "text, named",
    [
        ("US$ thousands", {"thousands"}),
        ("USD thousands;  6.25%", {"thousands"}),
        ("In thousands", {"thousands"}),
        ("USD 858,064 thousand", {"thousands"}),
        ("$000", {"thousands"}),
        ("US$k", {"thousands"}),
        ("USD K", {"thousands"}),
        ("US$ million", {"millions"}),
        ("USD millions", {"millions"}),
        ("US$m", {"millions"}),
        ("USD m", {"millions"}),
        ("$m", {"millions"}),
        ("$M", {"millions"}),
        ("USD mm", {"millions"}),
        ("US$bn", {"millions"}),
        ("stated in millions", {"millions"}),
        ("USD million/billion", {"millions"}),
        ("US$ thousands; USD 37.6 million", {"thousands", "millions"}),
        ("", set()),
        ("p.4", set()),
        ("9M 2025", set()),
        ("1,000", set()),
        ("US$ and a mid-year note", set()),
        ("Mmm", set()),
    ],
)
def test_the_words_that_name_a_unit(text, named):
    assert cpos_forecast._units_named(text) == named
