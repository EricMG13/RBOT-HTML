"""CP-1's figures checked in code at acceptance (contract section 3 of the CP-1 method task).

Every expected figure below is hand-worked from the TDG FY2024 10-K figures the controller wrote
into the contract's answer key; none is produced by the code under test."""

import re
from decimal import Decimal
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from deploy_workflow.owners import cpos_cp1_check as check
from deploy_workflow.owners.cpos_launch import (
    CHART_TABLES,
    CP1_CHECK_BLOCK,
    DEBT_RECON,
    _chart_header,
    _cp1_issues,
    _owned_issues,
)

BASIS = "Synthetic."
UNIT = "USD millions"


def table(heading: str, header: list[str], rows: list[list[str]]) -> str:
    out = [
        f"### {heading}",
        "",
        f"| {' | '.join(header)} |",
        f"| {' | '.join('---' for _ in header)} |",
    ]
    out += [f"| {' | '.join(row)} |" for row in rows]
    return "\n".join(out)


def statement(heading: str, rows: dict[str, tuple[str, str]], unit: str = UNIT) -> str:
    body = [[label, a, b, unit, BASIS, "10-K"] for label, (a, b) in rows.items()]
    return table(heading, ["Line item", "FY2024", "FY2023", "Unit", "Basis", "Source"], body)


INCOME = {
    "Revenue": ("11,000", "9,500"),
    "EBITDA (Reported)": ("3,813", "3,148"),
    "EBITDA (Adjusted)": ("4,173", "3,395"),
}
CASH_FLOW = {
    "Net Cash from Operating Activities": ("2,045", "1,375"),
    "Net Cash from Investing Activities": ("-2,441", "-900"),
    "Net Cash from Financing Activities": ("3,171", "-16"),
    "FX Effect on Cash": ("14", "12"),
    "Net Cash Change": ("2,789", "471"),
    "Opening Cash": ("3,472", "3,001"),
    "Closing Cash": ("6,261", "3,472"),
    "Cash Interest Paid": ("1,158", "1,160"),
}
BALANCE = {
    "Total Assets": ("25,586", "19,970"),
    "Total Liabilities": ("31,869", "21,948"),
    "Total Equity": ("-6,283", "-1,978"),
    "Total Debt": ("24,880", "19,750"),
    "Cash & Equivalents": ("6,261", "3,472"),
}
# metric -> (FY2024, FY2023) as (numerator, denominator, value)
REGISTER = {
    "Total debt / EBITDA": (("24,880", "3,813", "6.53"), ("19,750", "3,148", "6.27")),
    "Net debt / EBITDA": (("18,619", "3,813", "4.88"), ("16,278", "3,148", "5.17")),
    "EBITDA / cash interest": (("3,813", "1,158", "3.29"), ("3,148", "1,160", "2.71")),
    "Total debt / adjusted EBITDA": (("24,880", "4,173", "5.96"), ("19,750", "3,395", "5.82")),
    "Net debt / adjusted EBITDA": (("18,619", "4,173", "4.46"), ("16,278", "3,395", "4.79")),
    "Adjusted EBITDA / cash interest": (("4,173", "1,158", "3.60"), ("3,395", "1,160", "2.93")),
}
LADDER = ("93", "92", "92", "6,637", "4,768", "12,637")  # sums to 24,319
NET_DEBT = {
    "FY2024 / 2024-09-30": ("24,880", "6,261", "18,619"),
    "FY2023 / 2023-09-30": ("19,750", "3,472", "16,278"),
}


def register(rows=REGISTER, overrides=None) -> str:
    """Each row's Period is the Net debt row's Period cell; `overrides` is keyed by the short
    period (`FY2024`)."""
    out = []
    for name, (latest, earlier) in rows.items():
        for period, (num, den, value) in (("FY2024", latest), ("FY2023", earlier)):
            cells = [num, den, value]
            cells = (overrides or {}).get((name, period), cells)
            dated = next(p for p in NET_DEBT if p.startswith(period))
            out.append(
                [name, "numerator / denominator", cells[0], "10-K", cells[1], "10-K", dated]
                + ["USD", "US$m", cells[2], "Calculated", "Tier 1", BASIS]
            )
    return table("T4.9 Calculation register", list(check.REGISTER_COLUMNS), out)


def build(*, reg=None, drop=(), **given) -> str:
    use = {
        "income": INCOME,
        "cash_flow": CASH_FLOW,
        "balance": BALANCE,
        "leverage": (("6.53", "4.88"), ("6.27", "5.17")),
        "cover": ("3.29", "2.71"),
        "ladder": LADDER,
        "recon": ("24,319", "561", "24,880"),
        "net_debt": NET_DEBT,
        **given,
    }
    income, cash_flow, balance = use["income"], use["cash_flow"], use["balance"]
    leverage, cover, ladder, recon = use["leverage"], use["cover"], use["ladder"], use["recon"]
    parts = [
        statement("T4.4 Income statement", income),
        statement("T4.5 Cash flow statement", cash_flow),
        statement("T4.6 Balance sheet", balance),
        reg if reg is not None else register(),
        table(
            "Chart data: leverage",
            [
                "Period",
                "Total debt / EBITDA",
                "Net debt / EBITDA",
                "Reporting unit",
                "Basis and limitation",
            ],
            [["FY2024", *leverage[0], "x", BASIS], ["FY2023", *leverage[1], "x", BASIS]],
        ),
        table(
            "Chart data: interest cover",
            ["Period", "EBITDA / cash interest", "Reporting unit", "Basis and limitation"],
            [["FY2024", cover[0], "x", BASIS], ["FY2023", cover[1], "x", BASIS]],
        ),
        table(
            "Chart data: debt maturities",
            ["Period", "Debt maturing", "Reporting unit", "Basis and limitation"],
            [[f"FY{2025 + i}", cell, "US$m", BASIS] for i, cell in enumerate(ladder)],
        ),
        table(
            "Net debt data",
            ["Period", "Gross debt", "Cash", "Net debt", "Reporting unit", "Basis and limitation"],
            [[p, *v, "US$m", BASIS] for p, v in use["net_debt"].items()],
        ),
        table(
            "Debt principal to carrying value",
            [
                "Period",
                "Contractual principal",
                "Reconciling items",
                "Carrying value",
                "Reporting unit",
                "Basis and limitation",
            ],
            [["FY2024 / 2024-09-30", *recon, "US$m", BASIS]],
        ),
    ]
    kept = [p for p in parts if not any(p.startswith(f"### {name}") for name in drop)]
    return "## Findings\n\n" + "\n\n".join(kept) + "\n\n## Calculations\n\nNone.\n"


def with_row(rows: dict, label: str, cells: tuple[str, str]) -> dict:
    return {**rows, label: cells}


def without(rows: dict, label: str) -> dict:
    return {k: v for k, v in rows.items() if k != label}


def test_the_hand_worked_figures_pass():
    assert _cp1_issues(build()) == ()


@pytest.mark.parametrize("printed", ["6.5", "7"])
def test_a_ratio_to_fewer_than_two_places_is_refused(printed):
    # R6 (supersedes the contract's acceptance of 6.5): 24,880 / 3,813 = 6.52504 is within half a
    # unit of 6.5 and of 7, yet the fixed rows are printed to exactly two places.
    reg = register(overrides={("Total debt / EBITDA", "FY2024"): ["24,880", "3,813", printed]})
    text = build(reg=reg, leverage=((printed, "4.88"), ("6.27", "5.17")))
    issue = only(_cp1_issues(text))
    named(issue, "Total debt / EBITDA", "FY2024", printed, "exactly two decimal places", "6.5250")


def test_a_ratio_printed_to_three_places_is_refused():
    reg = register(overrides={("Total debt / EBITDA", "FY2024"): ["24,880", "3,813", "6.525"]})
    text = build(reg=reg, leverage=(("6.525", "4.88"), ("6.27", "5.17")))
    assert "exactly two decimal places" in only(_cp1_issues(text))


def test_a_missing_cash_interest_with_a_not_calculable_cover_passes():
    flow = {**CASH_FLOW, "Cash Interest Paid": ("Not supplied: the 10-K gives no figure", "1,160")}
    none = ["Not supplied: the 10-K gives no figure", "Not calculable: no cash interest"]
    reg = register(
        overrides={
            ("EBITDA / cash interest", "FY2024"): ["3,813", none[0], none[1]],
            ("Adjusted EBITDA / cash interest", "FY2024"): ["4,173", none[0], none[1]],
        }
    )
    text = build(cash_flow=flow, reg=reg, cover=("Not supplied: no cash interest", "2.71"))
    assert _cp1_issues(text) == ()


def only(issues: tuple[str, ...]) -> str:
    assert len(issues) == 1, issues
    return issues[0]


def named(issue: str, *words: str) -> None:
    for word in words:
        assert word in issue, (word, issue)
    assert "remove" not in issue.lower() and "delete" not in issue.lower()


@pytest.mark.parametrize("printed", ["6.54", "6.52"])
def test_a_ratio_more_than_half_a_unit_from_the_quotient_is_refused(printed):
    reg = register(overrides={("Total debt / EBITDA", "FY2024"): ["24,880", "3,813", printed]})
    text = build(reg=reg, leverage=((printed, "4.88"), ("6.27", "5.17")))
    issue = only(_cp1_issues(text))
    named(issue, "Total debt / EBITDA", "FY2024", printed, "24,880", "3,813", "6.5250")


def test_a_chart_figure_that_differs_from_the_register_is_refused():
    text = build(leverage=(("6.01", "4.88"), ("6.27", "5.17")))
    issue = only(_cp1_issues(text))
    named(issue, "Chart data: leverage", "FY2024", "6.01", "6.53", "Total debt / EBITDA")


def test_a_chart_period_with_no_register_row_is_refused():
    reg = register({k: v for k, v in REGISTER.items() if k != "EBITDA / cash interest"})
    issues = _cp1_issues(build(reg=reg))
    assert len(issues) == 2, issues  # one per period the chart states
    named(issues[0], "Chart data: interest cover", "EBITDA / cash interest", "FY2024", "3.29")


def test_a_numerator_that_is_principal_not_carrying_is_refused():
    reg = register(overrides={("Total debt / EBITDA", "FY2024"): ["25,068", "3,813", "6.57"]})
    text = build(reg=reg, leverage=(("6.57", "4.88"), ("6.27", "5.17")))
    issue = only(_cp1_issues(text))
    named(issue, "Total debt / EBITDA", "FY2024", "25,068", "24,880")


def test_a_reported_ebitda_operand_that_differs_from_the_statement_is_refused():
    reg = register(overrides={("Net debt / EBITDA", "FY2024"): ["18,619", "4,173", "4.46"]})
    text = build(reg=reg, leverage=(("6.53", "4.46"), ("6.27", "5.17")))
    issue = only(_cp1_issues(text))
    named(issue, "Net debt / EBITDA", "FY2024", "4,173", "3,813", "EBITDA (Reported)")


def test_the_statement_ties_run_for_any_currency_in_millions():
    # R3: a statement Unit is a currency code plus `millions` or `thousands`; the tie to the
    # US$m tables then runs (the old "skipped unless USD millions" rule is gone).
    reg = register(overrides={("Net debt / EBITDA", "FY2024"): ["18,619", "4,173", "4.46"]})
    text = build(reg=reg, leverage=(("6.53", "4.46"), ("6.27", "5.17")))
    issue = only(_cp1_issues(text.replace("| USD millions |", "| EUR millions |")))
    named(issue, "Net debt / EBITDA", "4,173", "3,813", "EBITDA (Reported)", "difference 360")


def test_a_balance_sheet_debt_that_differs_from_gross_debt_is_refused():
    issue = only(_cp1_issues(build(balance={**BALANCE, "Total Debt": ("25,068", "19,750")})))
    named(issue, "T4.6 Balance sheet", "Total Debt", "FY2024", "25,068", "24,880")


def test_a_reconciliation_that_does_not_add_to_carrying_is_refused():
    issue = only(_cp1_issues(build(recon=("24,319", "500", "24,880"))))
    named(issue, "Debt principal to carrying value", "24,319", "500", "24,880", "61")


def test_a_ladder_that_does_not_sum_to_the_stated_principal_is_refused():
    issue = only(_cp1_issues(build(recon=("25,068", "-188", "24,880"))))
    named(issue, "Chart data: debt maturities", "24,319", "25,068", "749")


def test_a_carrying_value_that_differs_from_gross_debt_is_refused():
    issue = only(_cp1_issues(build(recon=("24,319", "500", "24,819"))))
    named(issue, "24,819", "24,880", "Gross debt")


def test_a_ladder_row_that_is_a_gap_beside_a_stated_principal_is_refused():
    # R7; the stated principal 25,068 and the six rows' sum are not compared when a row is a gap.
    ladder = ("93", "Not supplied: not disclosed", "92", "6,637", "4,768", "12,637")
    issue = only(_cp1_issues(build(ladder=ladder, recon=("24,319", "561", "24,880"))))
    named(issue, "Chart data: debt maturities", "24,319", "row 2", "Not supplied: not disclosed")


def test_a_ladder_with_a_gap_beside_a_gap_principal_is_not_summed():
    ladder = ("93", "Not supplied: not disclosed", "92", "6,637", "4,768", "12,637")
    gap = "Not supplied: the ladder is incomplete"
    assert _cp1_issues(build(ladder=ladder, recon=(gap, "Not supplied: none", "24,880"))) == ()


def test_a_balance_sheet_that_does_not_balance_is_refused():
    issue = only(_cp1_issues(build(balance={**BALANCE, "Total Equity": ("-6,238", "-1,978")})))
    named(issue, "T4.6 Balance sheet", "FY2024", "25,586", "31,869", "-6,238", "45")


def test_a_cash_walk_that_does_not_close_is_refused():
    issues = _cp1_issues(build(cash_flow={**CASH_FLOW, "Net Cash Change": ("2,798", "471")}))
    assert len(issues) == 2, issues
    closing = next(i for i in issues if "Closing Cash" in i)
    named(closing, "T4.5 Cash flow statement", "FY2024", "3,472", "2,798", "6,261", "9")
    flows = next(i for i in issues if "Net Cash Change" in i and "Closing" not in i)
    named(flows, "2,045", "2,798", "2,789")


def test_a_missing_fixed_row_is_named_with_the_table_count():
    issue = only(_cp1_issues(build(balance=without(BALANCE, "Total Assets"))))
    named(issue, "5 of 5 required tables", "T4.6 Balance sheet", "Total Assets")


def test_missing_tables_are_counted_and_named():
    issue = only(_cp1_issues(build(drop=("T4.4 Income statement", "T4.9 Calculation register"))))
    named(issue, "3 of 5 required tables", "T4.4 Income statement", "T4.9 Calculation register")


def test_a_denominator_with_words_in_it_is_refused():
    reg = register(
        overrides={("Total debt / adjusted EBITDA", "FY2024"): ["24,880", "4,173 (adj.)", "5.96"]}
    )
    issue = only(_cp1_issues(build(reg=reg)))
    named(issue, "Total debt / adjusted EBITDA", "FY2024", "Denominator Value", "4,173 (adj.)")


def test_a_register_period_the_pack_cannot_order_is_refused():
    reg = register().replace("| FY2023 / 2023-09-30 |", "| last year |", 1)
    assert any("last year" in i for i in _cp1_issues(build(reg=reg)))


def test_an_empty_unit_or_currency_is_refused():
    reg = register().replace("| USD | US$m |", "|  | US$m |", 1)
    assert any("Currency" in i for i in _cp1_issues(build(reg=reg)))


def test_a_zero_denominator_cannot_have_a_calculated_number():
    reg = register(overrides={("EBITDA / cash interest", "FY2024"): ["3,813", "0", "3.29"]})
    flow = {**CASH_FLOW, "Cash Interest Paid": ("0", "1,160")}
    issues = _cp1_issues(build(reg=reg, cash_flow=flow))
    assert any("not above zero" in i and "3.29" in i for i in issues), issues


def test_a_statement_cell_with_words_is_refused():
    income = {**INCOME, "EBITDA (Reported)": ("3,813 est.", "3,148")}
    issues = _cp1_issues(build(income=income))
    assert any("T4.4 Income statement" in i and "3,813 est." in i for i in issues), issues


def test_a_table_that_cannot_be_read_is_an_issue_not_a_pass():
    text = build().replace(
        "| Line item | FY2024 | FY2023 | Unit | Basis | Source |", "| Item | FY2024 |", 1
    )
    issue = only(_cp1_issues(text))
    named(issue, "4 of 5 required tables", "T4.4 Income statement")


def test_a_blocked_module_that_states_every_figure_as_a_gap_passes():
    gap = "Not supplied: no financial sources"

    def rows(spec):
        return {label: (gap, gap) for label in spec}

    income = rows(["EBITDA (Reported)"])
    cash = rows(check.STATEMENTS[1].fixed)
    balance = rows(check.STATEMENTS[2].fixed)
    blocked_register = table(
        "T4.9 Calculation register",
        list(check.REGISTER_COLUMNS),
        [["Not assessable", *[gap] * 12]],
    )
    text = build(
        income=income,
        cash_flow=cash,
        balance=balance,
        reg=blocked_register,
        leverage=((gap, gap), (gap, gap)),
        cover=(gap, gap),
        ladder=(gap,),
        recon=(gap, gap, gap),
        net_debt={"FY2024 / 2024-09-30": (gap, gap, gap)},
    )
    assert _cp1_issues(text) == ()


def test_the_check_runs_through_the_existing_rejection_path():
    text = build(recon=("24,319", "500", "24,880"))
    assert any("61" in i for i in _owned_issues("CP-1", [], text))
    assert not any("61" in i for i in _owned_issues("CP-2", [], text))


def test_the_check_reads_the_same_chart_columns_the_launcher_asks_for():
    asked = {heading: columns for heading, columns, _ in CHART_TABLES.values()}
    for heading, columns in check.CHART_COLUMNS.items():
        assert asked[heading] == columns


def test_the_reconciliation_header_is_the_one_the_launcher_asks_for():
    assert check.RECON_HEADER == _chart_header(DEBT_RECON)
    assert DEBT_RECON.chart_unit == check.REGISTER_UNIT


def test_a_net_debt_or_chart_table_without_a_period_column_does_not_stop_the_check():
    text = build().replace("| Period | Gross debt |", "| Year | Gross debt |")
    text = text.replace("| Period | Total debt / EBITDA |", "| Year | Total debt / EBITDA |")
    assert isinstance(_cp1_issues(text), tuple)


def test_figures_beyond_the_working_precision_are_still_compared_exactly():
    huge = "9" * 90
    assert check.recomputation(huge, "7", "1" + "4" * 89 + ".0") is not None
    assert check.recomputation("1" + "0" * 90, "1" + "0" * 90, "1") is None


def test_the_launcher_text_names_every_fixed_row_and_metric_and_is_short():
    for statement_spec in check.STATEMENTS:
        for label in (*statement_spec.fixed, *statement_spec.optional, statement_spec.heading):
            assert label in CP1_CHECK_BLOCK
    for metric in check.METRICS:
        assert metric.name in CP1_CHECK_BLOCK
    assert check.REGISTER_HEADING in CP1_CHECK_BLOCK
    assert check.RECON_HEADING in CP1_CHECK_BLOCK
    assert "| " + " | ".join(check.REGISTER_COLUMNS) + " |" in CP1_CHECK_BLOCK
    assert len(CP1_CHECK_BLOCK) < 3_426 + 1_500  # fix round 1 may grow the block by under 1,500


def test_the_launcher_text_states_every_refusal_of_the_rulings_from_the_constants():
    for form in check.PERIOD_FORMS:
        assert f"`{form}`" in CP1_CHECK_BLOCK
    assert check.UNIT_EXAMPLE in CP1_CHECK_BLOCK
    assert f"at most {check.MAX_CELL} characters" in CP1_CHECK_BLOCK
    for words in (
        "exactly two decimal places",
        "positive amount paid",
        "Period cell of the `Net debt data` row",
        "interim rows have no statement tie",
        "`## Gaps`",
        "gap beside a stated principal",
        "only there, outside code fences",
        "Gross debt and Cash against `Total Debt` and `Cash & Equivalents`",
    ):
        assert words in CP1_CHECK_BLOCK, words


# --- properties -------------------------------------------------------------------------


def cell(value: Fraction | int, places: int) -> str:
    scaled = Fraction(value) * 10**places
    return f"{Decimal(int(scaled)).scaleb(-places):f}"


@given(
    num=st.integers(1, 10**9),
    den=st.integers(1, 10**9),
    places=st.integers(0, 3),
    half_even=st.booleans(),
)
def test_the_correctly_rounded_quotient_passes_and_one_place_away_fails(
    num, den, places, half_even
):
    quotient = Fraction(num, den) * 10**places
    floor = quotient.numerator // quotient.denominator
    remainder = quotient - floor
    if remainder != Fraction(1, 2):
        rounded = floor + (1 if remainder > Fraction(1, 2) else 0)
    elif half_even:
        rounded = floor + (floor % 2)
    else:
        rounded = floor + 1
    good = cell(Fraction(rounded, 10**places), places)
    assert check.recomputation(str(num), str(den), good) is None
    for step in (-1, 1):
        off = Fraction(rounded + step, 10**places)
        away = abs(off - Fraction(num, den)) > Fraction(1, 2 * 10**places)
        if off >= 0:
            found = check.recomputation(str(num), str(den), cell(off, places))
            assert (found is not None) == away


@given(
    num=st.one_of(st.integers(-(10**6), 10**6).map(str), st.just("Not supplied: none")),
    den=st.one_of(st.integers(-(10**6), 10**6).map(str), st.just("Not supplied: none")),
    calc=st.one_of(st.just("Not calculable: none"), st.just("Not supplied: none")),
)
def test_a_gap_never_produces_a_recomputation_issue(num, den, calc):
    assert check.recomputation(num, den, calc) is None
    assert check.recomputation("Not supplied: none", "3,813", "6.53") is None
    assert check.recomputation(num, "Not supplied: none", "6.53") is None


@given(items=st.lists(st.integers(0, 10**7), min_size=1, max_size=8), extra=st.integers(0, 10**5))
def test_a_ladder_passes_exactly_when_it_sums_and_reconciles(items, extra):
    total = sum(items)
    ladder = [f"{i:,}" for i in items]
    carrying = total + extra
    assert check.ladder_issues(ladder, f"{total:,}", f"{extra:,}", f"{carrying:,}") == []
    assert check.ladder_issues(ladder, f"{total + 1:,}", f"{extra:,}", f"{carrying:,}") != []
    assert check.ladder_issues(ladder, f"{total:,}", f"{extra:,}", f"{carrying + 1:,}") != []
    gap = ["Not supplied: none", *ladder]
    assert check.ladder_issues(gap, f"{total + 1:,}", f"{extra:,}", f"{total + 1 + extra:,}") != []
    unsaid = "Not supplied: the ladder is incomplete"
    assert check.ladder_issues(gap, unsaid, f"{extra:,}", f"{total + extra:,}") == []


def test_a_second_reconciliation_row_is_refused_not_ignored():
    text = build().replace(
        "| FY2024 / 2024-09-30 | 24,319 |",
        "| FY2024 / 2024-09-30 | 24,319 | 561 | 24,880 | US$m | x |\n"
        "| FY2024 / 2024-09-30 | 24,319 |",
    )
    assert any("states 2 rows" in i for i in _cp1_issues(text))


def test_a_register_row_of_the_wrong_width_is_an_issue_not_a_crash():
    text = build().replace("| Tier 1 | Synthetic. |", "| Tier 1 |", 1)
    assert any("needs 13 cells" in i for i in _cp1_issues(text))


def test_a_stated_temporary_equity_joins_the_balance_sheet_sum():
    issue = only(_cp1_issues(build(balance={**BALANCE, "Temporary Equity": ("100", "0")})))
    named(issue, "Temporary Equity 100", "25,686", "25,586")


# --- fix round 1: the controller's rulings R1-R10 (answer key typed from the brief) ---------

DATED = "FY2024 / 2024-09-30"


def sole(text: str, *words: str) -> str:
    issue = only(_cp1_issues(text))
    named(issue, *words)
    return issue


def test_a_chart_figure_against_a_gap_calculated_value_is_refused():
    reg = register(
        overrides={
            ("Total debt / EBITDA", "FY2024"): ["24,880", "3,813", "Not calculable: pending"]
        }
    )
    text = build(reg=reg, leverage=(("6.01", "4.88"), ("6.27", "5.17")))
    sole(text, "Chart data: leverage", "FY2024", "6.01", "Not calculable: pending", "difference")


def test_a_calculated_value_beside_a_gap_denominator_is_refused():
    reg = register(
        overrides={("Total debt / EBITDA", "FY2024"): ["24,880", "Not supplied: see note", "9.99"]}
    )
    text = build(reg=reg, leverage=(("9.99", "4.88"), ("6.27", "5.17")))
    issues = _cp1_issues(text)
    # Two-sided: the ratio needs both operands, and the EBITDA operand is a gap beside T4.4's 3,813.
    assert len(issues) == 2, issues
    named(next(i for i in issues if "9.99" in i), "Total debt / EBITDA", "FY2024", "denominator")
    named(next(i for i in issues if "T4.4" in i), "Not supplied: see note", "3,813")


def test_a_calculated_value_beside_a_gap_numerator_is_refused():
    reg = register(
        overrides={("Total debt / EBITDA", "FY2024"): ["Not supplied: see note", "3,813", "6.53"]}
    )
    issues = _cp1_issues(build(reg=reg))
    assert len(issues) == 2, issues
    named(next(i for i in issues if "6.53" in i), "Total debt / EBITDA", "numerator")
    named(next(i for i in issues if "Gross debt" in i), "Not supplied: see note", "24,880")


def test_a_stated_chart_figure_against_a_stated_register_figure_it_lacks_a_gap_cell_for():
    # Two-sided: the register states 3.29 for FY2024, the chart cell is a gap.
    text = build(cover=("Not supplied: not charted", "2.71"))
    sole(text, "Chart data: interest cover", "FY2024", "3.29", "Not supplied: not charted")


def test_a_net_debt_numerator_that_is_not_net_debt_is_refused():
    reg = register(overrides={("Net debt / EBITDA", "FY2024"): ["18,807", "3,813", "4.93"]})
    text = build(reg=reg, leverage=(("6.53", "4.93"), ("6.27", "5.17")))
    sole(text, "Net debt / EBITDA", "FY2024", "18,807", "18,619", "difference 188")


def test_a_cash_walk_one_unit_out_is_refused():
    flow = {**CASH_FLOW, "Closing Cash": ("6,262", "3,472")}
    sole(build(cash_flow=flow), "Closing Cash", "6,262", "3,472", "2,789", "difference 1)")


def test_a_net_debt_cash_that_is_not_the_balance_sheet_cash_is_refused():
    net_debt = {**NET_DEBT, DATED: ("24,880", "5,000", "19,880")}
    reg = register(
        overrides={
            ("Net debt / EBITDA", "FY2024"): ["19,880", "3,813", "5.21"],
            ("Net debt / adjusted EBITDA", "FY2024"): ["19,880", "4,173", "4.76"],
        }
    )
    text = build(net_debt=net_debt, reg=reg, leverage=(("6.53", "5.21"), ("6.27", "5.17")))
    sole(text, "Net debt data", "Cash 5,000", "Cash & Equivalents", "6,261", "difference 1,261")


@pytest.mark.parametrize(
    "side", ["gross", "cash"], ids=["Total Debt is a gap", "Cash & Equivalents is a gap"]
)
def test_a_net_debt_figure_stated_beside_a_balance_sheet_gap_is_refused(side):
    label = "Total Debt" if side == "gross" else "Cash & Equivalents"
    balance = {**BALANCE, label: ("Not supplied: not split out", BALANCE[label][1])}
    issue = only(_cp1_issues(build(balance=balance)))
    named(issue, "Net debt data", "FY2024", "Not supplied: not split out", "T4.6 Balance sheet")


def test_a_reported_ebitda_gap_beside_register_figures_is_refused_for_each_row():
    income = {**INCOME, "EBITDA (Reported)": ("Not supplied: adjusted only", "3,148")}
    issues = _cp1_issues(build(income=income))
    assert len(issues) == 3, issues  # the two leverage rows' denominators and the cover numerator
    for issue in issues:
        named(issue, "3,813", "EBITDA (Reported)", "Not supplied: adjusted only", "FY2024")


def test_a_fiscal_year_with_no_statement_column_is_refused():
    text = build().replace(
        "| Line item | FY2024 | FY2023 | Unit", "| Line item | FY2023 | FY2022 | Unit"
    )
    issues = _cp1_issues(text)
    assert any("no column for the fiscal year" in i and "EBITDA" in i for i in issues), issues
    assert any("Net debt data" in i and "T4.6 Balance sheet" in i for i in issues), issues


def test_the_interim_rows_have_no_statement_tie():
    # An interim row's EBITDA is a last-twelve-months figure: R2 says it is not tied to a column.
    reg = register(
        overrides={
            ("Total debt / EBITDA", "FY2024"): ["24,880", "3,000", "8.29"],
            ("Net debt / EBITDA", "FY2024"): ["18,619", "3,000", "6.21"],
            ("EBITDA / cash interest", "FY2024"): ["3,000", "1,158", "2.59"],
        }
    )
    text = build(reg=reg, leverage=(("8.29", "6.21"), ("6.27", "5.17")), cover=("2.59", "2.71"))
    assert _cp1_issues(text) != ()  # a fiscal-year row with that EBITDA is refused
    text = text.replace(DATED, "2025-06-30")
    text = re.sub(r"^\| FY2024 \|", "| 2025-06-30 |", text, flags=re.MULTILINE)
    assert _cp1_issues(text) == ()


def dated_alone(text: str) -> str:
    """The Net debt rows and the reconciliation dated by the day alone, as the pack allows."""
    for old, new in ((DATED, "2024-09-30"), ("FY2023 / 2023-09-30", "2023-09-30")):
        text = text.replace(f"| {old} | 24", f"| {new} | 24").replace(
            f"| {old} | 19", f"| {new} | 19"
        )
    return text


def test_a_register_period_that_matches_no_net_debt_row_is_refused():
    text = dated_alone(build())  # Net debt rows `2024-09-30`, register still `FY2024 / ...`
    text = text.replace(f"| {DATED} | USD", "| FY2024 | USD")
    text = text.replace("| FY2023 / 2023-09-30 | USD", "| FY2023 | USD")
    issues = [i for i in _cp1_issues(text) if "matches no Period cell" in i]
    assert len(issues) == 12, issues  # six fixed rows in each of two periods
    named(issues[0], "Total debt / EBITDA", "FY2024", "`2024-09-30`", "`2023-09-30`")


def test_a_reconciliation_period_that_matches_no_net_debt_row_is_refused():
    text = build(recon=("24,319", "561", "24,880")).replace(
        f"| {DATED} | 24,319", "| 30 September 2024 | 24,319"
    )
    sole(text, "Debt principal to carrying value", "30 September 2024", "matches no Period cell")


def test_a_net_debt_table_dated_by_the_day_ties_register_rows_written_with_that_date():
    text = build().replace(DATED, "2024-09-30").replace("FY2023 / 2023-09-30", "2023-09-30")
    text = re.sub(r"^\| FY2024 \|", "| 2024-09-30 |", text, flags=re.MULTILINE)
    text = re.sub(r"^\| FY2023 \|", "| 2023-09-30 |", text, flags=re.MULTILINE)
    assert _cp1_issues(text) == ()


@pytest.mark.parametrize("header", ["FY 2024", "FY2024 restated", "2024", "Notes"])
def test_a_statement_period_header_that_is_not_one_of_the_four_forms_is_refused(header):
    text = build().replace(
        "| Line item | FY2024 | FY2023 |", f"| Line item | {header} | FY2023 |", 1
    )
    issues = _cp1_issues(text)
    assert any(f"`{header}` is not a period" in i and "`FY2024`" in i for i in issues), issues


@pytest.mark.parametrize("header", ["FY2024", "Q3 2025", "H1 2025", "9M 2025"])
def test_every_period_header_form_the_method_names_is_a_period(header):
    text = build().replace(
        "| Line item | FY2024 | FY2023 |", f"| Line item | {header} | FY2023 |", 1
    )
    assert not any("is not a period" in i for i in _cp1_issues(text))


def test_a_statement_unit_that_is_not_a_currency_code_and_a_scale_is_refused():
    text = build().replace("| 3,813 | 3,148 | USD millions |", "| 3,813 | 3,148 | US$m |")
    issue = [i for i in _cp1_issues(text) if "Unit `US$m`" in i]
    assert len(issue) == 1, issue
    named(issue[0], "T4.4 Income statement", "millions", "thousands")


def thousands(rows: dict) -> dict:
    return {
        k: tuple(f"{int(v.replace(',', '')) * 1000:,}" for v in cells) for k, cells in rows.items()
    }


def balance_in_thousands(balance: dict) -> str:
    text = build(balance=balance)
    head, balance_sheet, tail = re.split(r"(?=### T4\.6 )|(?=### T4\.9 )", text)
    return head + balance_sheet.replace("USD millions", "USD thousands") + tail


def test_a_balance_sheet_in_thousands_ties_to_the_millions_tables():
    text = balance_in_thousands(thousands(BALANCE))
    assert text.count("USD thousands") == len(BALANCE)
    assert _cp1_issues(text) == ()


@pytest.mark.parametrize(
    ("debt", "refused"), [("24,880,400", False), ("24,880,600", True), ("24,879,400", True)]
)
def test_a_thousands_figure_agrees_within_half_a_millions_unit(debt, refused):
    balance = thousands({**BALANCE, "Total Debt": ("24,880", "19,750")})
    balance["Total Debt"] = (debt, "19,750,000")
    text = balance_in_thousands(balance)
    issues = [i for i in _cp1_issues(text) if "Total Debt" in i]
    assert bool(issues) is refused, issues
    if refused:
        named(issues[0], debt, "24,880", "difference")


def test_a_register_unit_that_is_not_the_net_debt_reporting_unit_is_refused_without_relabelling():
    text = build().replace("| USD | US$m |", "| GBP | GBP m |")
    issues = [i for i in _cp1_issues(text) if "Reporting unit" in i]
    assert len(issues) == 12, issues
    named(issues[0], "GBP m", "`US$m`", "Net debt data", "equal it")
    assert not any("write `US$m`" in i for i in issues)


def test_a_negative_cash_interest_is_refused_once_with_the_sign_rule():
    flow = {**CASH_FLOW, "Cash Interest Paid": ("-1,158", "1,160")}
    issue = sole(build(cash_flow=flow), "Cash Interest Paid", "FY2024", "-1,158", "positive")
    assert "signed" in issue


def test_the_activity_totals_and_fx_are_signed_and_pass():
    assert _cp1_issues(build()) == ()  # investing -2,441 and operating, financing as written


def test_a_ladder_that_is_a_gap_is_refused_beside_a_stated_principal_only():
    gap = ("Not supplied: not disclosed", *LADDER[1:])
    sole(build(ladder=gap), "row 1", "24,319", "Not supplied: not disclosed")


def test_a_cell_longer_than_twenty_five_characters_is_unreadable_not_a_number():
    huge = "9" * 26
    reg = register(overrides={("Total debt / EBITDA", "FY2024"): [huge, "3,813", "6.53"]})
    issues = _cp1_issues(build(reg=reg))
    assert any("Numerator Value" in i and "25 characters" in i for i in issues), issues
    twenty_five = "1" + "0" * 24  # 25 characters: still a number
    assert check._stated(twenty_five) is not None
    assert check._stated(twenty_five + "0") is None


def test_the_calculated_value_is_checked_when_the_cell_is_thousands_long_without_crashing():
    reg = register(overrides={("Total debt / EBITDA", "FY2024"): ["9" * 5000, "3,813", "1"]})
    assert any("Numerator Value" in i for i in _cp1_issues(build(reg=reg)))


def test_the_ladder_sums_exactly_beyond_twenty_eight_digits():
    big = "1" + "0" * 30
    assert check.ladder_issues([big, "1"], big, "0", big) != []
    exact = "1" + "0" * 29 + "1"
    assert check.ladder_issues([big, "1"], exact, "0", exact) == []


def test_a_second_balance_sheet_in_findings_is_refused():
    wrong = {**BALANCE, "Total Assets": ("30,000", "19,970")}
    text = build().replace(
        "\n\n## Calculations",
        "\n\n" + statement("T4.6 Balance sheet", wrong) + "\n\n## Calculations",
    )
    issue = only(_cp1_issues(text))
    named(issue, "T4.6 Balance sheet", "more than once")


def test_a_table_outside_findings_or_inside_a_fence_is_not_read():
    fenced = "```markdown\n" + statement("T4.6 Balance sheet", BALANCE) + "\n```\n\n"
    wrong = build(balance={**BALANCE, "Total Assets": ("30,000", "19,970")})
    assert _cp1_issues("## Request\n\n" + fenced + wrong) != ()
    body = build().split("## Findings\n\n", 1)[1].split("\n\n## Calculations", 1)[0]
    elsewhere = "## Findings\n\nSee below.\n\n## Calculations\n\n" + body + "\n"
    issue = only(_cp1_issues(elsewhere))
    named(issue, "0 of 5 required tables")


def test_an_escaped_pipe_in_a_cell_and_a_one_hyphen_separator_parse():
    text = build().replace(
        "| 3,813 | 3,148 | USD millions | Synthetic. | 10-K |",
        "| 3,813 | 3,148 | USD millions | Synthetic. | 10-K \\| note 7 |",
    )
    assert "\\|" in text and _cp1_issues(text) == ()
    head = (
        "| Period | Contractual principal | Reconciling items | Carrying value | Reporting unit |"
    )
    text = build().replace(
        f"{head} Basis and limitation |\n| --- | --- | --- | --- | --- | --- |",
        f"{head} Basis and limitation |\n|-|-|-|-|-|-|",
    )
    assert "|-|-|-|-|-|-|" in text and _cp1_issues(text) == ()


@pytest.mark.parametrize(
    ("kwargs", "words"),
    [
        (
            {"balance": {**BALANCE, "Total Equity": ("-6,238", "-1,978")}},
            ("`## Gaps`", "Not supplied"),
        ),
        ({"cash_flow": {**CASH_FLOW, "Net Cash Change": ("2,798", "471")}}, ("`## Gaps`",)),
    ],
)
def test_an_identity_refusal_tells_the_model_how_a_source_printed_difference_is_stated(
    kwargs, words
):
    for issue in _cp1_issues(build(**kwargs)):
        named(issue, *words)


def test_every_refusal_of_a_figure_states_the_difference():
    cases = [
        build(leverage=(("6.01", "4.88"), ("6.27", "5.17"))),
        build(balance={**BALANCE, "Total Debt": ("25,068", "19,750")}),
        build(recon=("24,319", "500", "24,880")),
        build(recon=("25,068", "-188", "24,880")),
        build(balance={**BALANCE, "Total Equity": ("-6,238", "-1,978")}),
        build(cash_flow={**CASH_FLOW, "Closing Cash": ("6,262", "3,472")}),
    ]
    for text in cases:
        for issue in _cp1_issues(text):
            assert "difference" in issue, issue


def test_the_block_and_the_reconciliation_rule_say_a_positive_has_no_plus_sign():
    assert "no plus sign" in CP1_CHECK_BLOCK
    assert "no plus sign" in DEBT_RECON.rules


def test_a_statement_figure_off_by_the_thousands_scale_alone_is_refused():
    balance = {**BALANCE, "Total Debt": ("24,880,000", "19,750")}
    issues = [i for i in _cp1_issues(build(balance=balance)) if "Total Debt" in i]
    assert issues and "24,880,000" in issues[0] and "difference" in issues[0]


@given(millions=st.integers(1, 10**9), offset=st.integers(-499, 499))
def test_a_thousands_figure_within_half_a_unit_ties_and_one_beyond_does_not(millions, offset):
    where = "x"
    left = check.Side("A", f"{millions * 1000 + offset:,}", "", 1000)
    right = check.Side("B", f"{millions:,}")
    assert check._tie(where, left, right) is None
    beyond = check.Side("A", f"{millions * 1000 + 501:,}", "", 1000)
    assert check._tie(where, beyond, right) is not None
    gap = check.Side("A", "Not supplied: none", "", 1000)
    assert check._tie(where, gap, right) is not None
    assert check._tie(where, gap, check.Side("B", "Not supplied: none")) is None
    assert check._tie(where, check.Side("A", None), check.Side("B", None)) is None


def test_a_register_period_written_as_the_date_alone_finds_its_fiscal_year_column():
    # Net debt `FY2024 / 2024-09-30`; the register and chart write the date: same period, and the
    # statement column is found by the Net debt row's fiscal year.
    text = build().replace(f"| {DATED} | USD", "| 2024-09-30 | USD")
    text = text.replace("| FY2023 / 2023-09-30 | USD", "| 2023-09-30 | USD")
    text = re.sub(r"^\| FY2024 \| (6\.53|3\.29)", r"| 2024-09-30 | \1", text, flags=re.MULTILINE)
    text = re.sub(r"^\| FY2023 \| (6\.27|2\.71)", r"| 2023-09-30 | \1", text, flags=re.MULTILINE)
    assert _cp1_issues(text) == ()


def test_a_net_debt_or_chart_figure_longer_than_twenty_five_characters_is_refused():
    huge = "1" + "0" * 25
    net_debt = {**NET_DEBT, DATED: (huge, "6,261", "18,619")}
    issues = _cp1_issues(build(net_debt=net_debt))
    assert any("Net debt data" in i and "Gross debt" in i and "25 characters" in i for i in issues)
    issues = _cp1_issues(build(cover=(huge, "2.71")))
    assert any("Chart data: interest cover" in i and "25 characters" in i for i in issues)
