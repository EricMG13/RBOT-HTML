"""CP-1 period headers: the forms the retained handoffs print (answer key from the plan)."""

import json
from dataclasses import replace
from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest
from test_cpos_launch import forecast_block

from deploy_workflow.owners import cp2g, cpos_forecast, cpos_periods
from deploy_workflow.owners.cpos_forecast import model_files
from deploy_workflow.owners.cpos_periods import (
    NO_ANCHOR,
    NO_PF,
    NO_SIGN,
    NOT_A_CELL,
    NOT_BUILT,
    NOT_DATED,
    NOT_EXACT,
    NOT_NAMED,
    NOT_UNDER_A_PERIOD,
    PART_YEAR,
    period_dates,
    period_label,
    period_of,
)

D = Decimal


@pytest.mark.parametrize(
    "header, period",
    [
        ("FY2024", ("FY", 2024, 4)),
        ("FY 2024", ("FY", 2024, 4)),
        ("**FY2024 revised**", ("FY", 2024, 4)),
        ("Q3 2025", ("QUARTER", 2025, 3)),
        ("Q3 2024 recast", ("QUARTER", 2024, 3)),
        ("Q1 FY2025", ("QUARTER", 2025, 1)),
        ("Q1 FY2025: thirteen weeks ended 2024-12-28", ("QUARTER", 2025, 1)),
        ("9M 2025", ("YTD", 2025, 3)),
        ("9M2024", ("YTD", 2024, 3)),
        ("9M 2024 revised", ("YTD", 2024, 3)),
        ("H1 2025", ("YTD", 2025, 2)),
        ("6M 2025", ("YTD", 2025, 2)),
    ],
)
def test_the_header_forms_the_retained_handoffs_print(header, period):
    assert period_of(header) == period


@pytest.mark.parametrize(
    "header",
    [
        "Q2 2025 net sales",
        "Rolling reported periods to 2024-12-28",
        "September 30, 2025",
        "LTM June 2025",
        "FY24",
        "Q5 2025",
        "2025",
        "Locator",
        "FY2024 and FY2023",
        "",
        "FY2024, annual definition",
        "FY2025: guidance midpoint",
        "FY2024: nine months ended 2024-12-31",
        "FY2024: thirty-nine weeks ended 2024-09-28",
    ],
)
def test_anything_else_is_not_a_period(header):
    assert period_of(header) is None


def test_labels():
    assert [
        period_label(p)
        for p in (("QUARTER", 2025, 3), ("YTD", 2025, 3), ("YTD", 2025, 2), ("FY", 2024, 4))
    ] == ["Q3 2025", "9M 2025", "H1 2025", "FY2024"]


CP1 = """| Reported label | Q3 2025 | Q3 2024 revised | 9M 2025 | 9M 2024 | FY2024 | FY2023 \
| Locator |
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
"""
BASE = {
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
OPERANDS = cp2g.Operands(**{key: cp2g.Val(D(amount), None) for key, amount in BASE.items()})
TABLES = cpos_forecast._tables(CP1)

NAMED = {
    "revenue": ("Net sales", "FY2024"),
    "ebitda": ("Adjusted EBITDA", "FY2024"),
    "interest": ("Cash paid for interest", "FY2024"),
    "taxes": ("Income taxes paid", "FY2024"),
    "wc": ("Change in working capital", "FY2024"),
    "capex": ("Capital expenditures", "FY2024"),
    "fcf": ("Free cash flow", "FY2024"),
    "debt": ("Total debt", "FY2024"),
    "cash": ("Cash and cash equivalents", "FY2024"),
    "undrawn": ("Undrawn revolver", "FY2024"),
}


def lines(tables, operands, *, named=NAMED):
    """The lines with the fixture's rows named, as a block that names them has them read."""
    return cpos_periods.lines(tables, operands, named=named)


def history(tables, operands, *, named=NAMED, **kwargs):
    return cpos_periods.history(tables, operands, named=named, **kwargs)


def named_block(**changes):
    base = {
        k: {"amount": v, "reason": None, "row": NAMED[k][0], "period": NAMED[k][1]}
        for k, v in BASE.items()
    }
    return forecast_block(base=base, **changes)


def test_each_base_line_is_read_in_every_period_cp1_prints():
    found = lines(TABLES, OPERANDS)
    assert found["revenue"].values == {
        ("QUARTER", 2025, 3): D("270"),
        ("QUARTER", 2024, 3): D("250"),
        ("YTD", 2025, 3): D("780"),
        ("YTD", 2024, 3): D("720"),
        ("FY", 2024, 4): D("1000"),
        ("FY", 2023, 4): D("940"),
    }
    assert found["interest"].values == {
        ("YTD", 2025, 3): D("27"),
        ("YTD", 2024, 3): D("28"),
        ("FY", 2024, 4): D("36"),
    }
    assert found["wc"].values[("YTD", 2025, 3)] == D("12")  # (12) printed: an investment
    assert found["debt"].values[("YTD", 2024, 3)] == D("620")
    assert all(line.reason is None for line in found.values())


# Review Focus 2
def test_an_original_and_a_revised_comparative_that_differ_blank_that_period_only():
    cp1 = (
        CP1 + "\n| Reported label | Q3 2024 | FY2024 |\n| --- | --- | --- |"
        "\n| Net sales | 251 | 1,000 |\n"
    )
    line = lines(cpos_forecast._tables(cp1), OPERANDS)["revenue"]
    assert (
        line.gaps[("QUARTER", 2024, 3)] == "CP-1 prints different figures for this line in Q3 2024"
    )
    assert line.values[("FY", 2024, 4)] == D("1000")


def test_a_stated_gap_cell_is_not_a_figure():
    cp1 = CP1.replace(
        "| Capital expenditures | (33) |", "| Capital expenditures | Not supplied: not extracted |"
    )
    assert ("YTD", 2025, 3) not in lines(cpos_forecast._tables(cp1), OPERANDS)["capex"].values


def test_an_operand_without_an_amount_or_a_cell_has_its_reason():
    ops = replace(
        OPERANDS, undrawn=cp2g.Val(None, "CP-1 states no facility"), fcf=cp2g.Val(D("999"), None)
    )
    found = lines(TABLES, ops)
    assert (
        found["undrawn"].reason == "CP-1 states no facility" and found["fcf"].reason == NOT_A_CELL
    )


def test_year_headers_that_are_not_periods_are_named():
    cp1 = CP1.replace(
        "| Metric | FY2024 | 9M 2025 | 9M 2024 |",
        "| Metric | FY2024 | September 30, 2025 | 9M 2024 |",
    )
    assert lines(cpos_forecast._tables(cp1), OPERANDS)["debt"].unread == ("September 30, 2025",)


def test_odd_table_shapes_do_not_raise():
    found = lines(
        [
            [],
            [["Metric"]],
            [
                ["Metric", "FY2024"],
                [],
                ["Net sales"],
                ["Net sales", "1,000"],
                ["Adjusted EBITDA", "300"],
            ],
        ],
        OPERANDS,
    )
    assert found["revenue"].values == {("FY", 2024, 4): D("1000")}


def _read(cp1, key):
    return lines(cpos_forecast._tables(cp1), OPERANDS)[key]


def test_a_period_column_without_a_number_is_a_not_printed_gap():
    cp1 = CP1.replace(
        "| Capital expenditures | (33) |", "| Capital expenditures | Not supplied: not extracted |"
    )
    capex = _read(cp1, "capex")
    assert capex.gaps == {("YTD", 2025, 3): "CP-1 does not print this line for 9M 2025"}


def test_a_repeated_label_with_different_figures_gaps_that_period_only():
    cp1 = CP1.replace(
        "| Adjusted EBITDA |",
        "| Net sales | 271 | 250 | 780 | 720 | 1,000 | 940 | p.2 |\n| Adjusted EBITDA |",
    )
    revenue = _read(cp1, "revenue")
    assert revenue.gaps == {
        ("QUARTER", 2025, 3): "CP-1 prints different figures for this line in Q3 2025"
    }
    assert revenue.values[("QUARTER", 2024, 3)] == D("250")


def test_two_columns_of_one_table_for_one_period_that_differ_are_a_gap():
    cp1 = CP1.replace("| Q3 2024 revised |", "| Q3 2024 revised | Q3 2024 |", 1)
    cp1 = cp1.replace(
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        1,
    )
    cp1 = cp1.replace("| Net sales | 270 | 250 |", "| Net sales | 270 | 250 | 249 |")
    cp1 = cp1.replace("| Adjusted EBITDA | 84 | 75 |", "| Adjusted EBITDA | 84 | 75 | 74 |")
    revenue = _read(cp1, "revenue")
    assert revenue.gaps[("QUARTER", 2024, 3)] == (
        "CP-1 prints different figures for this line in Q3 2024"
    )
    assert ("QUARTER", 2024, 3) not in revenue.values


def test_a_working_capital_release_is_found_in_the_cell_printed_positive():
    ops = replace(OPERANDS, wc=cp2g.Val(D("-10"), None))  # FY2024, the base period, printed +10
    cp1 = CP1.replace(
        "| Change in working capital | (12) | (9) | (10) |",
        "| Change in working capital | 12 | 9 | 10 |",
    )
    wc = lines(cpos_forecast._tables(cp1), ops)["wc"]
    assert wc.reason is None and wc.values[("YTD", 2025, 3)] == D("-12")


# --- history (Task 3) ---------------------------------------------------------------------------


def cell(record, column_id, key):
    return next(c for c in record["columns"] if c["id"] == column_id)["values"][key]


def test_the_columns_are_the_owners_set_in_order():
    record = history(TABLES, OPERANDS)
    assert [(c["id"], c["label"], c["prior"]) for c in record["columns"]] == [
        ("Q3 2024", "Q3 2024", None),
        ("Q3 2025", "Q3 2025", "Q3 2024"),
        ("YTD", "YTD (9M 2025)", "PYTD"),
        ("PYTD", "PYTD (9M 2024)", None),
        ("FY2023", "FY2023", None),
        ("FY2024", "FY2024", "FY2023"),
        ("LTM", "LTM Q3 2025", "PRIOR_LTM"),
        ("PRIOR_LTM", "Prior LTM", None),
        ("PF", "PF LTM", None),
    ]
    assert record["schema_version"] == "cpos-history/1"


@pytest.mark.parametrize(
    "key, ytd, pytd, fy, ltm",
    [
        ("revenue", "780", "720", "1000", "1060"),
        ("ebitda", "240", "216", "300", "324"),
        ("interest", "27", "28", "36", "35"),
        ("tax_wc", "27", "23", "30", "34"),
        ("capex", "33", "29", "40", "44"),
        ("cfo", "186", "165", "234", "255"),
        ("fcf", "153", "136", "194", "211"),
        ("closing_debt", "590", "620", "600", "590"),
        ("closing_cash", "120", "90", "100", "120"),
        ("net_debt", "470", "530", "500", "470"),
        ("liquidity", "170", "140", "150", "170"),
    ],
)
def test_the_answer_key(key, ytd, pytd, fy, ltm):
    record = history(TABLES, OPERANDS)
    got = [D(cell(record, c, key)["amount"]) for c in ("YTD", "PYTD", "FY2024", "LTM")]
    assert got == [D(ytd), D(pytd), D(fy), D(ltm)]


def test_ratios():
    record = history(TABLES, OPERANDS)

    def near(column, key, want):
        return abs(Fraction(cell(record, column, key)["amount"]) - want) < Fraction(1, 10**12)

    assert near("LTM", "total_leverage", Fraction(590, 324))
    assert near("LTM", "net_leverage", Fraction(470, 324))
    assert near("LTM", "coverage", Fraction(324, 35)) and near("YTD", "coverage", Fraction(240, 27))
    assert near("FY2024", "fcf_to_debt", Fraction(194, 600))
    assert near("LTM", "fcf_to_debt", Fraction(211, 590))
    assert cell(record, "YTD", "total_leverage") == {"amount": None, "reason": PART_YEAR}
    assert cell(record, "Q3 2025", "fcf_to_debt")["reason"] == PART_YEAR


def test_prior_ltm_names_the_period_cp1_does_not_print():
    record = history(TABLES, OPERANDS)
    assert cell(record, "PRIOR_LTM", "revenue") == {
        "amount": None,
        "reason": "needs 9M 2023, which CP-1 does not print",
    }
    assert (
        cell(record, "PRIOR_LTM", "interest")["reason"]
        == "needs FY2023, 9M 2023, which CP-1 does not print"
    )
    assert cell(record, "PRIOR_LTM", "closing_debt")["amount"] == "620"


def test_prior_ltm_is_built_when_the_earlier_year_to_date_is_printed():
    cp1 = (
        CP1.replace("| FY2023 | Locator |", "| FY2023 | 9M 2023 | Locator |", 1)
        .replace(
            "| --- | --- | --- | --- | --- | --- | --- | --- |\n",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
            1,
        )
        .replace("| 940 | p.2 |", "| 940 | 690 | p.2 |")
        .replace("| 276 | p.9 |", "| 276 | 204 | p.9 |")
    )
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    assert D(cell(record, "PRIOR_LTM", "revenue")["amount"]) == D("970")
    assert D(cell(record, "PRIOR_LTM", "ebitda")["amount"]) == D("288")
    assert cell(record, "PRIOR_LTM", "interest")["reason"].startswith("needs FY2023, 9M 2023")


def test_pf_is_unavailable_with_its_reason():
    column = history(TABLES, OPERANDS)["columns"][-1]
    assert column["reason"] == NO_PF
    assert len(column["values"]) == 16
    assert all(v == {"amount": None, "reason": NO_PF} for v in column["values"].values())


FY_ONLY = """| Reported label | FY2024 | FY2023 | Locator |
| --- | --- | --- | --- |
| Net sales | 1,000 | 940 | p.2 |
| Adjusted EBITDA | 300 | 276 | p.9 |

| Reported label | FY2024 | Locator |
| --- | --- | --- |
| Cash paid for interest | (36) | p.4 |
| Income taxes paid | (20) | p.4 |
| Change in working capital | (10) | p.4 |
| Capital expenditures | (40) | p.4 |
| Free cash flow | 194 | p.4 |

| Metric | FY2024 |
| --- | --- |
| Total debt | 600 |
| Cash and cash equivalents | 100 |
| Undrawn revolver | 50 |
"""


def test_a_fiscal_year_anchor_has_no_year_to_date():  # Review Focus 4
    record = history(cpos_forecast._tables(FY_ONLY), OPERANDS)
    no_ytd = "the latest reported period is fiscal year FY2024; there is no year to date"
    assert cell(record, "YTD", "revenue")["reason"] == no_ytd
    assert next(c for c in record["columns"] if c["id"] == "PYTD")["reason"] == no_ytd
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1000")
    assert D(cell(record, "PRIOR_LTM", "revenue")["amount"]) == D("940")
    assert cell(record, "PRIOR_LTM", "interest")["reason"] == (
        "needs FY2023, which CP-1 does not print"
    )
    labels = [c["label"] for c in record["columns"]]
    assert labels[:1] == ["Quarter"] and "LTM FY2024" in labels
    placeholder = record["columns"][0]
    assert placeholder["reason"] == "CP-1 prints no quarter column Python can read"


def test_a_missing_quarter_cell_keeps_its_reason():
    assert cell(history(TABLES, OPERANDS), "Q3 2025", "interest") == {
        "amount": None,
        "reason": "CP-1 does not print this line for Q3 2025",
    }


def test_the_limits_say_what_was_not_checked_or_read():
    limits = history(TABLES, OPERANDS)["limits"]
    assert limits[0] == NOT_DATED and len(limits) == 1


def test_a_quarter_without_its_year_to_date_period_is_not_summed():
    cp1 = (
        "| Reported label | Q3 2025 | FY2024 |\n| --- | --- | --- |\n| Net sales | 270 | 1,000 |\n"
        "| Adjusted EBITDA | 84 | 300 |\n"
    )
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    assert cell(record, "YTD", "revenue")["reason"] == "needs 9M 2025, which CP-1 does not print"
    assert cell(record, "LTM", "revenue")["reason"].startswith("needs ")
    assert cell(record, "Q3 2025", "revenue")["amount"] == "270"


def test_no_base_line_under_a_period_header_gives_every_column_its_reason():
    ops = replace(OPERANDS, undrawn=cp2g.Val(None, "CP-1 states no facility"))
    record = history([[["Metric", "Note"], ["Net sales", "1,000"]]], ops, named=None)
    assert [c["id"] for c in record["columns"]] == [
        "Quarter", "YTD", "PYTD", "Fiscal year", "LTM", "PRIOR_LTM", "PF",
    ]  # fmt: skip
    for column in record["columns"][:-1]:
        assert column["reason"] == NO_ANCHOR
        assert cell(record, column["id"], "fcf") == {"amount": None, "reason": NO_ANCHOR}
        assert cell(record, column["id"], "revenue")["reason"] == NOT_NAMED
        assert cell(record, column["id"], "undrawn")["reason"] == "CP-1 states no facility"
    assert record["columns"][-1]["reason"] == NO_PF


def test_history_never_raises_on_odd_tables():
    record = history(
        [
            [],
            [["Metric"]],
            [
                ["Metric", "FY2024"],
                [],
                ["Net sales"],
                ["Net sales", "1,000"],
                ["Adjusted EBITDA", "300"],
            ],
        ],
        OPERANDS,
    )
    assert record["columns"][-1]["id"] == "PF"
    assert cell(record, "FY2024", "revenue") == {"amount": "1000", "reason": None}


def test_a_non_positive_denominator_keeps_the_calculators_reason():
    ops = replace(OPERANDS, interest=cp2g.Val(D("0"), None))
    cp1 = CP1.replace(
        "| Cash paid for interest | (27) | (28) | (36) |",
        "| Cash paid for interest | (0) | (0) | (0) |",
    )
    record = history(cpos_forecast._tables(cp1), ops)
    assert cell(record, "FY2024", "interest") == {"amount": "0", "reason": None}
    assert cell(record, "FY2024", "coverage") == {"amount": None, "reason": cp2g.NC_INTEREST}


def test_limits_name_lines_without_history_and_headers_not_read():
    cp1 = CP1.replace(
        "| Metric | FY2024 | 9M 2025 | 9M 2024 |",
        "| Metric | FY2024 | September 30, 2025 | 9M 2024 |",
    )
    ops = replace(OPERANDS, undrawn=cp2g.Val(None, "CP-1 states no facility"))
    limits = history(cpos_forecast._tables(cp1), ops)["limits"]
    assert limits[0] == NOT_DATED
    assert "undrawn revolver: CP-1 states no facility" in limits
    assert limits[-1] == "CP-1 column headers not read as periods: September 30, 2025."


REVENUE_ONLY = cp2g.Operands(
    **{
        key: cp2g.Val(
            D("1000") if key == "revenue" else None, None if key == "revenue" else "not stated"
        )
        for key in BASE
    }
)


def test_a_period_printed_with_different_figures_still_sets_the_anchor():
    cp1 = (
        "| Reported label | 9M 2025 | 9M 2025 restated | 9M 2024 | FY2024 |\n"
        "| --- | --- | --- | --- | --- |\n| Net sales | 780 | 790 | 720 | 1,000 |\n"
    )
    record = history(cpos_forecast._tables(cp1), REVENUE_ONLY)
    gap = "CP-1 prints different figures for this line in 9M 2025"
    assert next(c for c in record["columns"] if c["id"] == "LTM")["label"] == "LTM Q3 2025"
    assert cell(record, "YTD", "revenue") == {"amount": None, "reason": gap}
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason": gap}
    assert D(cell(record, "PYTD", "revenue")["amount"]) == D("720")


def test_a_fourth_quarter_is_a_fiscal_year_anchor():
    cp1 = (
        "| Reported label | Q4 2025 | FY2024 |\n| --- | --- | --- |\n| Net sales | 260 | 1,000 |\n"
    )
    record = history(cpos_forecast._tables(cp1), REVENUE_ONLY)
    assert next(c for c in record["columns"] if c["id"] == "LTM")["label"] == "LTM FY2025"
    no_ytd = "the latest reported period is fiscal year FY2025; there is no year to date"
    assert cell(record, "YTD", "revenue")["reason"] == no_ytd
    assert cell(record, "LTM", "revenue") == {
        "amount": None,
        "reason": "needs FY2025, which CP-1 does not print",
    }
    assert D(cell(record, "PRIOR_LTM", "revenue")["amount"]) == D("1000")
    assert D(cell(record, "Q4 2025", "revenue")["amount"]) == D("260")


def test_a_sum_needing_more_than_38_digits_is_missing_not_an_exception():
    big = "9999.0000000000000000000000000000000001"  # 38 digits
    cp1 = (
        "| Reported label | 9M 2025 | 9M 2024 | FY2024 |\n| --- | --- | --- | --- |\n"
        f"| Net sales | 780 | 720 | {big} |\n"
    )
    ops = replace(REVENUE_ONLY, revenue=cp2g.Val(D(big), None))
    record = history(cpos_forecast._tables(cp1), ops)
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason": NOT_EXACT}


# --- the period table and the date check (Task 4) -----------------------------------------------
PERIOD_ROWS = {
    "FY2024": ("2024-01-01", "2024-12-31"),
    "FY2023": ("2023-01-01", "2023-12-31"),
    "9M 2025": ("2025-01-01", "2025-09-30"),
    "9M 2024": ("2024-01-01", "2024-09-30"),
    "Q3 2025": ("2025-07-01", "2025-09-30"),
    "Q3 2024 revised": ("2024-07-01", "2024-09-30"),
}


def _period_table(rows):
    body = "".join(f"| {label} | {s} | {e} |\n" for label, (s, e) in rows.items())
    return "| Period | Start | End |\n| --- | --- | --- |\n" + body


CP1_DATED = CP1 + "\n" + _period_table(PERIOD_ROWS)


def dated(**changes):
    rows = {**PERIOD_ROWS, **changes}
    return CP1 + "\n" + _period_table({k: v for k, v in rows.items() if v is not None})


def _column(record, column_id):
    return next(c for c in record["columns"] if c["id"] == column_id)


def test_the_period_table_is_read():
    dates, twice = period_dates(cpos_forecast._tables(CP1_DATED))
    assert dates[("YTD", 2025, 3)] == (date(2025, 1, 1), date(2025, 9, 30))
    assert dates[("QUARTER", 2024, 3)] == (date(2024, 7, 1), date(2024, 9, 30)) and twice == ()


def test_a_checked_ltm_says_so_and_carries_its_dates():
    record = history(cpos_forecast._tables(CP1_DATED), OPERANDS)
    ltm = _column(record, "LTM")
    assert (ltm["start"], ltm["end"]) == ("2024-10-01", "2025-09-30")
    assert D(ltm["values"]["revenue"]["amount"]) == D("1060")
    assert (
        record["limits"][0]
        == "The last twelve months were checked against CP-1's period dates (365 days)."
    )
    assert (_column(record, "YTD")["start"], _column(record, "YTD")["end"]) == (
        "2025-01-01",
        "2025-09-30",
    )
    assert (_column(record, "Q3 2024")["start"], _column(record, "FY2023")["end"]) == (
        "2024-07-01",
        "2023-12-31",
    )
    assert (_column(record, "PF")["start"], _column(record, "PF")["end"]) == (None, None)


def test_a_changed_year_end_is_not_summed():  # Review Focus 6
    record = history(cpos_forecast._tables(dated(FY2024=("2023-10-01", "2024-09-30"))), OPERANDS)
    assert cell(record, "LTM", "revenue") == {
        "amount": None,
        "reason": "FY2024, 9M 2025 and 9M 2024 are not a continuous twelve months by CP-1's "
        "period dates (FY2024 ends 2024-09-30; 9M 2025 starts 2025-01-01)",
    }
    for key in ("ebitda", "interest", "tax_wc", "capex", "cfo", "fcf", "coverage", "fcf_to_debt"):
        assert cell(record, "LTM", key)["amount"] is None, key
    assert cell(record, "LTM", "total_leverage")["amount"] is None
    assert cell(record, "LTM", "net_leverage")["amount"] is None
    assert D(cell(record, "LTM", "closing_debt")["amount"]) == D("590")
    assert D(cell(record, "LTM", "net_debt")["amount"]) == D("470")
    assert D(cell(record, "YTD", "revenue")["amount"]) == D("780")
    ltm = _column(record, "LTM")
    assert (ltm["start"], ltm["end"]) == (None, None)


def test_a_mislabelled_interim_is_not_summed():
    record = history(
        cpos_forecast._tables(dated(**{"9M 2024": ("2024-01-01", "2024-06-30")})), OPERANDS
    )
    assert cell(record, "LTM", "revenue")["reason"].endswith("(457 days)")


def test_a_pytd_that_does_not_start_with_the_fiscal_year_is_not_summed():
    record = history(
        cpos_forecast._tables(dated(**{"9M 2024": ("2024-01-02", "2024-09-30")})), OPERANDS
    )
    assert cell(record, "LTM", "revenue")["reason"].endswith(
        "(9M 2024 starts 2024-01-02; FY2024 starts 2024-01-01)"
    )


WEEK52 = """| Reported label | Q1 FY2025 | Q1 FY2024 | FY2024 | Locator |
| --- | --- | --- | --- | --- |
| Net sales | 270 | 250 | 1,000 | p.2 |

| Period | Start | End |
| --- | --- | --- |
| FY2024 | 2023-10-01 | 2024-09-30 |
| Q1 FY2025 | 2024-10-01 | 2024-12-28 |
| Q1 FY2024 | 2023-10-01 | 2023-12-30 |
"""


def test_a_52_week_quarter_passes():
    record = history(cpos_forecast._tables(WEEK52), REVENUE_ONLY)
    assert record["limits"][0].endswith("(364 days).")
    ltm = _column(record, "LTM")
    assert (ltm["start"], ltm["end"]) == ("2023-12-31", "2024-12-28")
    assert D(ltm["values"]["revenue"]["amount"]) == D("1020")


@pytest.mark.parametrize("cp1", [CP1, dated(**{"9M 2024": None})])
def test_without_the_dates_the_ltm_is_built_and_marked_unchecked(cp1):  # Review Focus 7
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1060")
    assert record["limits"][0] == NOT_DATED
    ltm = _column(record, "LTM")
    assert (ltm["start"], ltm["end"]) == (None, None)


def test_a_period_dated_twice_differently_is_undated():
    cp1 = CP1_DATED + "| FY2024 | 2024-01-01 | 2024-12-30 |\n"
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    assert record["limits"][0] == NOT_DATED
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1060")
    twice = (
        "CP-1's period table dates FY2024 more than once, differently; it is treated as undated."
    )
    assert record["limits"].count(twice) == 1
    assert period_dates(cpos_forecast._tables(cp1))[1] == ("FY2024",)


def test_two_rows_with_the_same_dates_are_one():
    cp1 = CP1_DATED + "| FY 2024 | 2024-01-01 | 2024-12-31 |\n"
    dates, twice = period_dates(cpos_forecast._tables(cp1))
    assert dates[("FY", 2024, 4)] == (date(2024, 1, 1), date(2024, 12, 31)) and twice == ()


@pytest.mark.parametrize(
    "start, end",
    [("2024-13-01", "2024-12-31"), ("2024-12-31", "2024-01-01"), ("Jan 1, 2024", "2024-12-31")],
)
def test_an_unreadable_date_row_is_not_a_date(start, end):
    dates = period_dates(cpos_forecast._tables(dated(FY2024=(start, end))))[0]
    assert ("FY", 2024, 4) not in dates


def test_a_period_table_may_have_more_columns_and_there_may_be_several():
    cp1 = (
        CP1 + "\n| Period | Start | End | Locator |\n| --- | --- | --- | --- |\n"
        "| FY2024 | 2024-01-01 | 2024-12-31 | p.1 |\n"
        "\n| Period | Start | End |\n| --- | --- | --- |\n| 9M 2025 | 2025-01-01 | 2025-09-30 |\n"
        "\n| Item | Start | End |\n| --- | --- | --- |\n| FY2023 | 2023-01-01 | 2023-12-31 |\n"
    )
    dates, twice = period_dates(cpos_forecast._tables(cp1))
    assert set(dates) == {("FY", 2024, 4), ("YTD", 2025, 3)} and twice == ()


def _with_9m_2023(cp1):
    return (
        cp1.replace("| FY2023 | Locator |", "| FY2023 | 9M 2023 | Locator |", 1)
        .replace(
            "| --- | --- | --- | --- | --- | --- | --- | --- |\n",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
            1,
        )
        .replace("| 940 | p.2 |", "| 940 | 690 | p.2 |")
        .replace("| 276 | p.9 |", "| 276 | 204 | p.9 |")
    )


def test_a_checked_prior_ltm_carries_its_dates():
    cp1 = _with_9m_2023(dated(**{"9M 2023": ("2023-01-01", "2023-09-30")}))
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    prior = _column(record, "PRIOR_LTM")
    assert (prior["start"], prior["end"]) == ("2023-10-01", "2024-09-30")
    assert D(prior["values"]["revenue"]["amount"]) == D("970")


def test_a_failed_prior_ltm_check_leaves_the_ltm_and_the_limit_alone():
    cp1 = _with_9m_2023(dated(**{"9M 2023": ("2023-01-01", "2023-06-30")}))
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    assert cell(record, "PRIOR_LTM", "revenue") == {
        "amount": None,
        "reason": "FY2023, 9M 2024 and 9M 2023 are not a continuous twelve months by CP-1's "
        "period dates (458 days)",
    }
    assert D(cell(record, "PRIOR_LTM", "closing_debt")["amount"]) == D("620")
    prior = _column(record, "PRIOR_LTM")
    assert (prior["start"], prior["end"]) == (None, None)
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1060")
    assert record["limits"][0].endswith("(365 days).")


def test_a_prior_ltm_that_cannot_be_built_is_not_checked():
    record = history(cpos_forecast._tables(dated(FY2023=("2023-01-01", "2023-03-01"))), OPERANDS)
    assert cell(record, "PRIOR_LTM", "revenue")["reason"].startswith("needs ")


FY_DATED = FY_ONLY + "\n| Period | Start | End |\n| --- | --- | --- |\n"


def test_a_fiscal_year_anchor_checks_the_fiscal_year_itself():
    cp1 = FY_DATED + "| FY2024 | 2024-01-01 | 2024-12-31 |\n| FY2023 | 2023-01-01 | 2023-12-31 |\n"
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    ltm, prior = _column(record, "LTM"), _column(record, "PRIOR_LTM")
    assert (ltm["start"], ltm["end"]) == ("2024-01-01", "2024-12-31")
    assert (prior["start"], prior["end"]) == ("2023-01-01", "2023-12-31")
    assert record["limits"][0].endswith("(366 days).")
    assert D(ltm["values"]["revenue"]["amount"]) == D("1000")


def test_a_short_fiscal_year_anchor_is_not_twelve_months():
    cp1 = FY_DATED + "| FY2024 | 2024-01-01 | 2024-06-30 |\n"
    record = history(cpos_forecast._tables(cp1), OPERANDS)
    assert cell(record, "LTM", "revenue") == {
        "amount": None,
        "reason": "FY2024 is not twelve months by CP-1's period dates (182 days)",
    }
    assert D(cell(record, "LTM", "closing_debt")["amount"]) == D("600")
    assert D(cell(record, "PRIOR_LTM", "revenue")["amount"]) == D("940")


def test_the_dated_more_than_once_limit_follows_the_operand_reasons():
    cp1 = dated() + "| FY2024 | 2024-01-01 | 2024-12-30 |\n"
    ops = replace(OPERANDS, undrawn=cp2g.Val(None, "CP-1 states no facility"))
    limits = history(cpos_forecast._tables(cp1), ops)["limits"]
    assert limits[1] == "undrawn revolver: CP-1 states no facility"
    assert limits[2].startswith("CP-1's period table dates FY2024 more than once")


def test_history_is_published_only_when_asked():
    default = model_files(CP1.encode(), forecast_block().encode())
    asked = model_files(CP1.encode(), forecast_block().encode(), history=True)
    assert "history" not in json.loads(default["calculation.json"])
    assert default == model_files(CP1.encode(), forecast_block().encode(), history=False)
    assert "history" in json.loads(asked["calculation.json"])
    for name in ("annual.md", "forecast.md", "forecast_exact.json", "quarter.md"):
        assert asked[name] == default[name]
    without = json.loads(asked["calculation.json"])
    del without["history"]
    assert without == json.loads(default["calculation.json"])


PRIOR_LTM_CP1 = """| Reported label | Q3 2025 | Q3 2024 revised | 9M 2025 | 9M 2024 | 9M 2023 \
| FY2024 | FY2023 | Locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Net sales | 270 | 250 | 780 | 720 | 690 | 1,000 | 940 | p.2 |
| Adjusted EBITDA | 84 | 75 | 240 | 216 | 204 | 300 | 276 | p.9 |

| Period | Start | End |
| --- | --- | --- |
| FY2024 | 2024-01-01 | 2024-12-31 |
| FY2023 | 2023-01-01 | 2023-12-31 |
| 9M 2025 | 2025-01-01 | 2025-09-30 |
| 9M 2024 | 2024-01-01 | 2024-09-30 |
| Q3 2025 | 2025-07-01 | 2025-09-30 |
| Q3 2024 revised | 2024-07-01 | 2024-09-30 |
"""


def test_the_prior_ltm_built_without_dates_is_flagged_and_a_checked_one_is_not():  # arch L1
    flag = "The prior last twelve months were not checked against period dates."
    ops = replace(
        OPERANDS,
        **{k: cp2g.Val(None, "not stated") for k in BASE if k not in ("revenue", "ebitda")},
    )
    undated = history(cpos_forecast._tables(PRIOR_LTM_CP1), ops, forecast_year=2025)
    assert undated["limits"][0].endswith("(365 days).")
    assert undated["limits"][1] == flag
    dated_all = PRIOR_LTM_CP1 + "| 9M 2023 | 2023-01-01 | 2023-09-30 |\n"
    checked = history(cpos_forecast._tables(dated_all), ops, forecast_year=2025)
    assert flag not in checked["limits"]


def test_model_files_publishes_the_history_record():
    files = model_files(CP1.encode(), named_block().encode(), history=True)
    record = json.loads(files["calculation.json"])["history"]
    ltm = next(c for c in record["columns"] if c["id"] == "LTM")
    assert D(ltm["values"]["revenue"]["amount"]) == D("1060")
    assert json.loads(files["calculation.json"])["annual_periods"] == []


def test_a_cp1_without_tables_still_publishes_the_forecast():
    files = model_files(" ".join(BASE.values()).encode(), forecast_block().encode(), history=True)
    record = json.loads(files["calculation.json"])["history"]
    assert [c["kind"] for c in record["columns"]] == [
        "QUARTER",
        "YTD",
        "PYTD",
        "FY",
        "LTM",
        "PRIOR_LTM",
        "PF",
    ]
    assert all(
        v["amount"] is None and v["reason"] for c in record["columns"] for v in c["values"].values()
    )
    assert "REFERENCE" in json.loads(files["forecast_exact.json"])["outputs"]


def test_the_forecast_figures_do_not_change():
    with_tables = model_files(CP1.encode(), forecast_block().encode())
    without = model_files(" ".join(BASE.values()).encode(), forecast_block().encode())
    assert (
        json.loads(with_tables["forecast_exact.json"])["outputs"]
        == json.loads(without["forecast_exact.json"])["outputs"]
    )


def test_a_cell_too_long_to_read_exactly_does_not_end_the_forecast():
    long = "| Other | (" + "1" * 40 + ") |"
    cp1 = CP1 + "\n| Item | FY2024 |\n| --- | --- |\n" + long + "\n"
    files = model_files(cp1.encode(), named_block().encode(), history=True)
    record = json.loads(files["calculation.json"])["history"]
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1060")


BIG = "1000.000000000000000000000000000000000001"


@pytest.mark.parametrize(
    "key, sign",
    [
        (key, sign)
        for key in ("revenue", "interest", "wc")
        for sign in ("({})", "{}", "-{}")
        if (key, sign) != ("revenue", "{}")  # a positive revenue cell needs no negation
    ],
)
def test_a_figure_of_39_digits_is_not_a_figure(key, sign):
    cp1 = (
        "| Reported label | 9M 2025 | 9M 2024 | FY2024 |\n| --- | --- | --- | --- |\n"
        "| Net sales | 780 | 720 | 1,000 |\n"
        f"| Other | {sign.format(BIG)} | 1 | 1 |\n"
    )
    ops = replace(REVENUE_ONLY, **{key: cp2g.Val(D(BIG), None)})
    named = {**NAMED, key: ("Other", "9M 2025")}
    record = history(cpos_forecast._tables(cp1), ops, named=named)  # must not raise
    assert record["columns"][-1]["id"] == "PF"
    line = lines(cpos_forecast._tables(cp1), ops, named=named)[key]
    assert line.values == {}
    assert line.reason == NOT_A_CELL


def test_an_ltm_that_cannot_be_built_is_not_called_checked():
    ops = replace(REVENUE_ONLY, revenue=cp2g.Val(D("780"), None))
    named = {"revenue": ("Net sales", "9M 2025")}
    cp1 = (
        "| Reported label | 9M 2025 | 9M 2024 |\n| --- | --- | --- |\n| Net sales | 780 | 720 |\n\n"
        "| Period | Start | End |\n| --- | --- | --- |\n| FY2024 | 2024-01-01 | 2024-12-31 |\n"
        "| 9M 2025 | 2025-01-01 | 2025-09-30 |\n| 9M 2024 | 2024-01-01 | 2024-09-30 |\n"
    )
    record = history(cpos_forecast._tables(cp1), ops, named=named)
    ltm = next(c for c in record["columns"] if c["id"] == "LTM")
    assert record["limits"][0] == NOT_BUILT and (ltm["start"], ltm["end"]) == (None, None)
    assert ltm["values"]["revenue"] == {
        "amount": None,
        "reason": "needs FY2024, which CP-1 does not print",
    }


def test_a_year_boundary_is_not_a_year_header():
    cp1 = CP1.replace(
        "| Metric | FY2024 | 9M 2025 | 9M 2024 |", "| Metric | FY2024 | Ref 20250 | 9M 2024 |"
    ).replace(
        "| Reported label | 9M 2025 | 9M 2024 | FY2024 | Locator |",
        "| Reported label | September 30, 2025 | 9M 2024 | FY2024 | Locator |",
    )
    unread = lines(cpos_forecast._tables(cp1), OPERANDS)["interest"].unread
    assert unread == ("September 30, 2025",)
    assert lines(cpos_forecast._tables(cp1), OPERANDS)["debt"].unread == ()


# --- the adversarial review's fixes (rulings 1 to 8) --------------------------------------------
def _md(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    return "\n".join(out + ["| " + " | ".join(r) + " |" for r in rows]) + "\n"


def _hist(cp1, ops=OPERANDS, **kwargs):
    return history(cpos_forecast._tables(cp1), ops, **kwargs)


def test_an_accrual_row_does_not_supply_another_periods_cash_interest():  # adv_wrong_row a1
    cp1 = CP1 + "\n" + _md(["Income", "FY2024", "FY2023"], [["Interest expense", "(36)", "(31)"]])
    record = _hist(cp1)
    assert cell(record, "FY2023", "interest") == {
        "amount": None,
        "reason": "CP-1 does not print this line for FY2023",
    }
    assert _read(cp1, "interest").reason is None


def test_an_ltm_base_amount_gives_the_interest_line_no_history():  # adv_wrong_row a3
    cp1 = _md(
        ["Reported label", "9M 2025", "9M 2024", "FY2024", "LTM Q3 2025"],
        [
            ["Net sales", "780", "720", "1,000", "1,060"],
            ["Adjusted EBITDA", "240", "216", "300", "324"],
            ["Cash paid for interest", "(27)", "(28)", "(36)", "(35)"],
        ],
    ) + _md(["Leases", "FY2024", "FY2023"], [["Lease payments", "(35)", "(33)"]])
    ops = replace(
        OPERANDS, revenue=cp2g.Val(D(1060), None), ebitda=cp2g.Val(D(324), None),
        interest=cp2g.Val(D(35), None),
    )  # fmt: skip
    named = {**NAMED, "interest": ("Cash paid for interest", "LTM Q3 2025")}
    interest = lines(cpos_forecast._tables(cp1), ops, named=named)["interest"]
    assert interest.values == {}
    assert interest.reason == NOT_UNDER_A_PERIOD.format(header="LTM Q3 2025")


def test_layer_one_reads_the_named_row_only():
    cp1 = (
        CP1
        + "\n| Item | FY2024 | FY2023 |\n| --- | --- | --- |\n| Lease payments | (36) | (33) |\n"
    )
    named = {**NAMED, "interest": ("Cash paid for interest", "FY2024")}
    interest = lines(cpos_forecast._tables(cp1), OPERANDS, named=named)["interest"]
    assert interest.reason is None
    assert interest.values == {
        ("YTD", 2025, 3): D("27"),
        ("YTD", 2024, 3): D("28"),
        ("FY", 2024, 4): D("36"),
    }


def test_layer_one_names_a_period_that_is_not_one():
    named = {**NAMED, "debt": ("Total debt", "December 31, 2024")}
    debt = lines(TABLES, OPERANDS, named=named)["debt"]
    assert debt.values == {} and debt.reason == (
        "CP-1 prints the base amount only under a column header that is not a period "
        "(December 31, 2024)"
    )


def test_model_files_reads_a_layer_one_forecast_through_its_named_rows():
    # The CP-1 handoff is its own forecast source: the base operands name row and period.
    base = {
        k: {"amount": v, "reason": None, "row": NAMED[k][0], "period": NAMED[k][1]}
        for k, v in BASE.items()
    }
    block = json.loads(forecast_block(base=base).split("```json\n")[1].split("\n```")[0])
    block["downside_shock"] = None  # a layer-1 forecast states no shock
    text = (
        CP1
        + "\n### Forecast inputs (machine-readable)\n\n```json\n"
        + json.dumps(block)
        + "\n```\n"
    )
    files = model_files(text.encode(), text.encode(), "CP-1", history=True)
    record = json.loads(files["calculation.json"])["history"]
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1060")


# --- ruling 2: a row's sign comes from its base cell --------------------------------------------
def test_a_net_refund_in_one_period_keeps_its_sign():  # adv_outflow_refund_sign
    cp1 = CP1.replace("| Income taxes paid | (15) | (14) |", "| Income taxes paid | (15) | 8 |")
    record = _hist(cp1)
    assert D(cell(record, "PYTD", "tax_wc")["amount"]) == D(1)  # -8 + 9
    assert D(cell(record, "LTM", "tax_wc")["amount"]) == D(56)  # (20 + 15 + 8) + (10 + 12 - 9)
    assert D(cell(record, "LTM", "cfo")["amount"]) == D(233)  # 324 - 35 - 56


def test_a_row_printed_positive_is_read_as_printed():
    cp1 = CP1.replace(
        "| Capital expenditures | (33) | (29) | (40) |", "| Capital expenditures | 33 | 29 | 40 |"
    )
    capex = _read(cp1, "capex")
    assert capex.values[("YTD", 2025, 3)] == D(33) and capex.values[("FY", 2024, 4)] == D(40)


# --- ruling 4: nothing at or after the forecast is history --------------------------------------
def test_a_guidance_column_is_not_history_and_does_not_move_the_anchor():  # adv_guidance_column
    cp1 = (
        CP1
        + "\n"
        + _md(["Outlook", "FY2024", "FY2025"], [["Capital expenditures", "(40)", "(45)"]])
    )
    record = _hist(cp1, forecast_year=2025)
    assert "FY2025" not in [c["id"] for c in record["columns"]]
    assert _column(record, "LTM")["label"] == "LTM Q3 2025"
    assert D(cell(record, "LTM", "capex")["amount"]) == D(44)
    assert (
        "CP-1 column FY2025 is in the forecast years and is not read as history."
        in record["limits"]
    )


def test_the_anchor_follows_revenue_and_ebitda_only():
    cp1 = (
        CP1 + "\n" + _md(["Other", "FY2024", "Q4 2025"], [["Capital expenditures", "(40)", "(45)"]])
    )
    record = _hist(cp1)
    assert _column(record, "LTM")["label"] == "LTM Q3 2025"
    assert "Q4 2025" not in [c["id"] for c in record["columns"]]


# --- ruling 5: a fiscal year that is not twelve months carries no full-year ratio ---------------
def test_a_transition_year_has_no_full_year_ratios():  # adv_short_fiscal_year_ratio
    record = _hist(dated(FY2024=("2024-04-01", "2024-12-31")))
    reason = "FY2024 is not twelve months by CP-1's period dates (275 days)"
    for key in ("total_leverage", "net_leverage", "fcf_to_debt"):
        assert cell(record, "FY2024", key) == {"amount": None, "reason": reason}
    assert D(cell(record, "FY2024", "revenue")["amount"]) == D(1000)


# --- ruling 6: a numeral of more than 38 digits is not a figure ---------------------------------
def test_an_ebitda_cell_of_a_million_digits_is_not_a_figure_and_nothing_raises():
    tiny = "0." + "0" * 999_999 + "1"
    cp1 = (
        CP1
        + "\n"
        + _md(
            ["Reported label", "FY2024", "FY2022"],
            [["Adjusted EBITDA", "300", tiny], ["Total debt", "600", "600"]],
        )
    )
    record = _hist(cp1)
    assert cell(record, "FY2022", "ebitda") == {
        "amount": None,
        "reason": "CP-1 does not print this line for FY2022",
    }
    assert D(cell(record, "FY2022", "closing_debt")["amount"]) == D(600)
    assert cell(record, "FY2022", "total_leverage")["amount"] is None
    files = model_files(cp1.encode(), named_block().encode(), history=True)
    assert json.loads(files["calculation.json"])["history"]["columns"][-1]["id"] == "PF"


# --- ruling 7: handoff text is bounded ----------------------------------------------------------
def test_a_header_quoted_in_a_reason_is_cut_to_80_characters():
    cp1 = CP1.replace("| Metric | FY2024 |", "| Metric | " + "x" * 200 + " 2024 |")
    cp1 = cp1.replace("| Total debt | 600 |", "| Total debt | 599 |")
    ops = replace(OPERANDS, debt=cp2g.Val(D(599), None))
    named = {**NAMED, "debt": ("Total debt", "x" * 200 + " 2024")}
    debt = lines(cpos_forecast._tables(cp1), ops, named=named)["debt"]
    assert debt.reason == (
        "CP-1 prints the base amount only under a column header that is not a period "
        f"({'x' * 80}...)"
    )


def test_the_unread_headers_limit_lists_ten_and_counts_the_rest():
    heads = [f"Ref {2000 + i}" for i in range(13)]
    cp1 = (
        CP1
        + "\n"
        + _md(["Reported label", *heads, "FY2024"], [["Net sales", *["1"] * 13, "1,000"]])
    )
    limits = _hist(cp1)["limits"]
    names = ", ".join(heads[:10])
    assert f"CP-1 column headers not read as periods: {names} and 3 more." in limits


def test_only_the_latest_columns_are_shown():
    quarters = [f"Q{q} {y}" for y in (2021, 2022, 2023) for q in (1, 2, 3, 4)] + [
        "Q1 2024",
        "Q2 2024",
        "Q3 2024",
    ]
    years = [f"FY{y}" for y in range(2015, 2025)]
    rows = [
        [
            "Net sales",
            *[str(100 + i) for i in range(len(quarters))],
            *["1,000" if y == "FY2024" else "90" for y in years],
        ],
        [
            "Adjusted EBITDA",
            *[str(50 + i) for i in range(len(quarters))],
            *["300" if y == "FY2024" else "40" for y in years],
        ],
    ]
    record = _hist(_md(["Reported label", *quarters, *years], rows))
    ids = [c["id"] for c in record["columns"]]
    assert (
        ids[0] == "Q4 2021"
        and "Q3 2021" not in ids
        and len([c for c in record["columns"] if c["kind"] == "QUARTER"]) == 12
    )
    fiscal = [c["id"] for c in record["columns"] if c["kind"] == "FY"]
    assert fiscal == [f"FY{y}" for y in range(2017, 2025)]
    assert "Only the latest 12 quarter columns are shown." in record["limits"]
    assert "Only the latest 8 fiscal-year columns are shown." in record["limits"]


def test_a_30_kb_handoff_of_the_reason_amplification_shape_gives_a_small_record():
    heads = [f"Q{q} {y}" for y in range(1925, 2025) for q in range(1, 5)]
    cp1 = _md(["Label", *heads], [["Net sales", *["1,000"] * len(heads)]])
    cp1 += "\n" + _md(["Label", "x" * 26_000 + " 2025"], [["Adjusted EBITDA", "300"]])
    named = {
        "revenue": ("Net sales", "Q4 2024"),
        "ebitda": ("Adjusted EBITDA", "x" * 26_000 + " 2025"),
    }
    assert len(cp1) >= 30_000
    record = _hist(cp1, named=named)
    assert len([c for c in record["columns"] if c["kind"] == "QUARTER"]) == 12
    assert len(json.dumps(record)) < 1_000_000


# --- ruling 8: reasons state the cause ----------------------------------------------------------
def test_nothing_located_says_it_was_not_built_even_with_a_period_table():  # adv_reason_text r1
    cp1 = _md(["Period", "Start", "End"], [["FY2024", "2024-01-01", "2024-12-31"]])
    cp1 += "\n" + _md(["Reported label", "FY2024"], [["Something else", "7"]])
    assert _hist(cp1)["limits"][0] == NOT_BUILT


def test_an_empty_operand_reason_is_published_as_no_reason_stated():  # adv_reason_text r2
    ops = replace(OPERANDS, revenue=cp2g.Val(None, ""))
    record = _hist(CP1, ops)
    assert cell(record, "Q3 2025", "revenue") == {"amount": None, "reason": "no reason was stated"}
    assert D(cell(record, "FY2024", "ebitda")["amount"]) == D(300)
    assert "revenue: no reason was stated" in record["limits"]
    assert all(
        v["amount"] is not None or v["reason"]
        for c in record["columns"]
        for v in c["values"].values()
    )


# --- fix round 2 ---------------------------------------------------------------------------------
TAX_ROW = "| Income taxes paid | (15) | (14) | (20) | p.4 |"
ZERO_TAXES = replace(OPERANDS, taxes=cp2g.Val(D(0), None))


@pytest.mark.parametrize("base", ["(0)", "0", "-0", "\u22120"])
def test_a_zero_base_cell_takes_the_sign_the_row_is_printed_in(base):  # A, adv2_zero_base_sign
    # Signed zero: the brackets or minus decide. Unsigned zero: the other cells are all printed
    # negative, so the row is outflows. The hand key is the same for all four.
    record = _hist(CP1.replace(TAX_ROW, TAX_ROW.replace("(20)", base)), ZERO_TAXES)
    assert D(cell(record, "YTD", "tax_wc")["amount"]) == D(27)
    assert D(cell(record, "LTM", "tax_wc")["amount"]) == D(14)


@pytest.mark.parametrize("row", ["(15) | 14 | 0", "0 | 0 | 0"])
def test_a_zero_base_cell_with_no_common_sign_gives_no_history(row):  # A
    cp1 = CP1.replace(TAX_ROW, f"| Income taxes paid | {row} | p.4 |")
    taxes = _read_ops(cp1, ZERO_TAXES, "taxes")
    assert taxes.reason == NO_SIGN and taxes.values == {}


def _read_ops(cp1, ops, key):
    return lines(cpos_forecast._tables(cp1), ops)[key]


def test_an_unsigned_zero_base_with_unsigned_cells_is_read_as_printed():  # A
    cp1 = CP1.replace(TAX_ROW, "| Income taxes paid | 15 | 14 | 0 | p.4 |")
    taxes = _read_ops(cp1, ZERO_TAXES, "taxes")
    assert taxes.values[("YTD", 2025, 3)] == D(15)


def test_the_forecast_year_never_drops_the_base_period():  # B, adv2_forecast_guard_base_year
    record = _hist(CP1, forecast_year=2024)
    assert D(cell(record, "LTM", "revenue")["amount"]) == D(1060)
    assert not any("forecast years" in x for x in record["limits"])
    assert "FY2024" in [c["id"] for c in record["columns"]]


def test_the_forecast_year_guard_on_the_layer_one_path_protects_the_named_base():  # B
    named = {"revenue": ("Net sales", "FY2025"), "ebitda": ("Adjusted EBITDA", "FY2025")}
    cp1 = _md(
        ["Label", "FY2025", "FY2026"],
        [["Net sales", "1,000", "1,100"], ["Adjusted EBITDA", "300", "330"]],
    )
    ops = replace(OPERANDS, **{k: cp2g.Val(None, "not stated") for k in BASE if k not in named})
    ops = replace(ops, revenue=cp2g.Val(D(1000), None))
    record = _hist(cp1, ops, named=named, forecast_year=2025)
    assert [c["id"] for c in record["columns"] if c["kind"] == "FY"] == ["FY2025"]
    forecast = "CP-1 column FY2026 is in the forecast years and is not read as history."
    assert forecast in record["limits"]


def test_a_weeks_tail_is_not_read_on_a_fiscal_year_header():  # D
    stub = "FY2024: thirty-nine weeks ended 2024-09-28"
    cp1 = CP1.replace("| FY2024 |", f"| {stub} |")
    named = {key: (row, stub) for key, (row, _) in NAMED.items()}
    record = _hist(cp1, named=named)
    assert "FY2024" not in [c["id"] for c in record["columns"]]
    assert cell(record, "LTM", "revenue") == {
        "amount": None,
        "reason": NOT_UNDER_A_PERIOD.format(header=stub),
    }
    assert (
        "revenue: CP-1 prints the base amount only under a column header that is not a period "
        "(FY2024: thirty-nine weeks ended 2024-09-28)"
    ) in record["limits"]


def test_a_line_printed_only_for_the_base_period_has_that_one_value():
    cp1 = CP1.replace(
        "| Metric | FY2024 | 9M 2025 | 9M 2024 |\n| --- | --- | --- | --- |",
        "| Metric | FY2024 |\n| --- | --- |",
    )
    cp1 = cp1.replace("| Total debt | 600 | 590 | 620 |", "| Total debt | 600 |")
    debt = lines(cpos_forecast._tables(cp1), OPERANDS)["debt"]
    assert debt.reason is None and debt.values == {("FY", 2024, 4): D("600")}


def test_an_operand_reason_is_cut_to_200_characters():  # F
    ops = replace(OPERANDS, undrawn=cp2g.Val(None, "r" * 500))
    assert _read_ops(CP1, ops, "undrawn").reason == "r" * 200 + "..."


# --- history from named rows only (Task A2) -----------------------------------------------------
RESIDUAL_HEAD = "| Reported label | 9M 2025 | 9M 2024 | FY2024 | Locator |"
RESIDUAL = CP1.replace(
    RESIDUAL_HEAD, "| Reported label | 9M 2025 | 9M 2024 | Year ended 2024-12-31 | Locator |"
) + ("\n" + _md(["Income statement", "FY2024", "FY2023"], [["Interest expense", "(36)", "(31)"]]))
UNHEADED = ("interest", "taxes", "wc", "capex", "fcf")


def test_a_cp2g_block_on_the_residuals_handoff_publishes_no_other_rows_interest():  # AK-2
    unnamed = model_files(RESIDUAL.encode(), forecast_block().encode(), history=True)
    record = json.loads(unnamed["calculation.json"])["history"]
    assert all(c["values"]["interest"]["amount"] is None for c in record["columns"])
    base = {
        k: {
            "amount": v,
            "reason": None,
            "row": NAMED[k][0],
            "period": "Year ended 2024-12-31" if k in UNHEADED else "FY2024",
        }
        for k, v in BASE.items()
    }
    files = model_files(RESIDUAL.encode(), forecast_block(base=base).encode(), history=True)
    record = json.loads(files["calculation.json"])["history"]
    assert cell(record, "FY2023", "interest") == {
        "amount": None,
        "reason": "CP-1 prints the base amount only under a column header that is not a period "
        "(Year ended 2024-12-31)",
    }
    assert D(cell(record, "FY2023", "revenue")["amount"]) == D(940)


def test_unnamed_operands_have_no_history_and_one_reason():
    found = lines(TABLES, OPERANDS, named=None)
    assert all(line.reason == NOT_NAMED and not line.values for line in found.values())
    record = history(TABLES, OPERANDS, named=None)
    assert [c["id"] for c in record["columns"]] == [
        "Quarter", "YTD", "PYTD", "Fiscal year", "LTM", "PRIOR_LTM", "PF",
    ]  # fmt: skip
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason": NOT_NAMED}
    assert cell(record, "LTM", "fcf") == {"amount": None, "reason": NO_ANCHOR}
    assert record["limits"][0] == NOT_BUILT and f"revenue: {NOT_NAMED}" in record["limits"]


def test_an_operand_with_an_amount_and_no_name_is_the_only_line_without_history():
    found = lines(TABLES, OPERANDS, named={k: v for k, v in NAMED.items() if k != "capex"})
    assert found["capex"].reason == NOT_NAMED and found["capex"].values == {}
    assert found["revenue"].reason is None and found["interest"].reason is None


def test_named_periods_may_differ_between_operands():
    ops = replace(OPERANDS, debt=cp2g.Val(D(590), None), cash=cp2g.Val(D(120), None))
    named = {
        **NAMED,
        "debt": ("Total debt", "9M 2025"),
        "cash": ("Cash and cash equivalents", "9M 2025"),
    }
    record = _hist(CP1, ops, named=named, forecast_year=2025)
    assert D(cell(record, "LTM", "closing_debt")["amount"]) == D(590)
    assert D(cell(record, "FY2024", "closing_debt")["amount"]) == D(600)
    assert D(cell(record, "LTM", "revenue")["amount"]) == D(1060)


def test_a_named_row_in_two_tables_with_another_figure_for_the_named_period():  # Review Focus 3
    cp1 = (
        CP1 + "\n" + _md(["Restated", "FY2024 revised", "FY2023"], [["Net sales", "1,010", "950"]])
    )
    revenue = _read(cp1, "revenue")
    assert revenue.reason is None
    assert revenue.values[("FY", 2024, 4)] == D(1000) and revenue.values[("FY", 2023, 4)] == D(940)
    same = CP1 + "\n" + _md(["Restated", "FY2024", "FY2023"], [["Net sales", "1,010", "950"]])
    with pytest.raises(ValueError, match="is not one number in CP-1"):
        model_files(same.encode(), named_block().encode(), history=True)


def test_model_files_reads_a_named_cp2g_block_through_its_rows():  # AK-1
    files = model_files(CP1.encode(), named_block().encode(), history=True)
    record = json.loads(files["calculation.json"])["history"]
    assert D(cell(record, "LTM", "revenue")["amount"]) == D("1060")
    assert D(cell(record, "LTM", "fcf")["amount"]) == D("211")
    unnamed = model_files(CP1.encode(), forecast_block().encode(), history=True)
    outputs = json.loads(unnamed["forecast_exact.json"])["outputs"]
    assert outputs == json.loads(files["forecast_exact.json"])["outputs"]
    record = json.loads(unnamed["calculation.json"])["history"]
    assert cell(record, "LTM", "revenue") == {"amount": None, "reason": NOT_NAMED}
    assert all(
        v["amount"] is None and v["reason"] for c in record["columns"] for v in c["values"].values()
    )


@pytest.mark.parametrize("blank", ["", "   ", "**", " ` ` "])
@pytest.mark.parametrize("which", [0, 1])
def test_a_blank_row_or_period_name_names_no_line_even_beside_an_unlabeled_row(blank, which):
    cp1 = _md(["Metric", "FY2024"], [["Net sales", "1,000"], [" ", "1,000"], ["", "1,000"]])
    name = list(NAMED["revenue"])
    name[which] = blank
    ops = replace(OPERANDS, revenue=cp2g.Val(D(1000), None))
    line = lines(cpos_forecast._tables(cp1), ops, named={**NAMED, "revenue": tuple(name)})[
        "revenue"
    ]
    assert line.reason == cpos_periods.NOT_NAMED
    assert line.values == {}
