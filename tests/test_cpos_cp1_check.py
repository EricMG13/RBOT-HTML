"""CP-1's figures checked in code at acceptance (contract section 3 of the CP-1 method task).

Every expected figure below is hand-worked from the TDG FY2024 10-K figures the controller wrote
into the contract's answer key; none is produced by the code under test."""

import re
from decimal import Decimal
from fractions import Fraction

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from deploy_workflow.confidence import INPUT_ROWS
from deploy_workflow.owners import cpos_cp1_check as check
from deploy_workflow.owners.cpos_launch import (
    CHART_TABLES,
    CP1_CHECK_BLOCK,
    CURRENCY_CODES,
    DEBT_RECON,
    PERIOD_REQUIRED_BLOCK,
    _chart_header,
    _cp1_issues,
    _owned_issues,
    chart_issues,
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
PERIODS = (("FY2024", "2023-10-01", "2024-09-30"), ("FY2023", "2022-10-01", "2023-09-30"))


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
        "periods": PERIODS,
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
        "PERIODS",
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
    periods = use["periods"]
    period_table = (
        table("Period table", ["Period", "Start", "End"], [list(r) for r in periods]).split(
            "\n", 2
        )[2]  # the table alone: CP-1 prints it without a heading
        if periods
        else ""
    )
    parts = [period_table if p == "PERIODS" else p for p in parts]
    kept = [p for p in parts if p and not any(p.startswith(f"### {name}") for name in drop)]
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


def test_the_statement_ties_run_for_a_statement_in_any_currency():
    # C1 (replaces R13, which skipped a non-USD statement): the same wrong operand is refused
    # under a EUR statement as under a USD one, in the issuer's own currency.
    reg = register(overrides={("Net debt / EBITDA", "FY2024"): ["18,619", "4,173", "4.46"]})
    text = build(reg=reg, leverage=(("6.53", "4.46"), ("6.27", "5.17")))
    for statements in (text, relabel(text, "EUR")):
        issue = only(_cp1_issues(statements))
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
    named(issue, "6 of 6 required tables", "T4.6 Balance sheet", "Total Assets")


def test_missing_tables_are_counted_and_named():
    issue = only(_cp1_issues(build(drop=("T4.4 Income statement", "T4.9 Calculation register"))))
    named(issue, "4 of 6 required tables", "T4.4 Income statement", "T4.9 Calculation register")


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
    named(issue, "5 of 6 required tables", "T4.4 Income statement")


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
    # 4,498 at 4de3482; round 2 may add 1,200; round 3 added 378 (4,907 -> 5,285); the budget cut
    # removed 128 (5,285 -> 5,157), so the bound falls by the same 128; the money-unit sentence
    # replaced the USD-only one (5,157 -> 5,337), so it rises by the same 180; the adjusted-names
    # sentence (owner ruling C2) added 193 (5,337 -> 5,530), so it rises by the same 193
    assert len(CP1_CHECK_BLOCK) <= 4_498 + 1_200 + 250 + 180 + 193


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
        "is the sixth table",
        "`End` of that column's row",
        (
            "The money unit is `US$m` when your statements are in USD, else their currency code "
            "and `m` (`GBPm`), in millions even where a statement prints thousands"
        ),
        (
            "and `Currency` is the statements' code. A figure in another currency is `Not "
            "supplied: reported in <unit>`"
        ),
        "once in the whole handoff",
    ):
        assert words in CP1_CHECK_BLOCK, words


def test_the_period_table_sentence_names_the_header_the_check_reads():
    sentence = PERIOD_REQUIRED_BLOCK
    assert "| " + " | ".join(check.PERIOD_HEADER) + " |" in sentence
    assert sentence.count(".") <= 3 and "YYYY-MM-DD" in sentence  # one instruction, short
    assert "| " + " | ".join(check.PERIOD_HEADER) + " |" not in CP1_CHECK_BLOCK  # not twice


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
    periods = (*PERIODS, ("9M 2025", "2024-10-01", "2025-06-30"))
    text = build(
        periods=periods,
        reg=reg,
        leverage=(("8.29", "6.21"), ("6.27", "5.17")),
        cover=("2.59", "2.71"),
    )
    assert _cp1_issues(text) != ()  # a fiscal-year row with that EBITDA is refused
    text = text.replace(DATED, "2025-06-30")
    text = re.sub(r"^\| FY2024 \| (?=\d\.\d\d \|)", "| 2025-06-30 | ", text, flags=re.MULTILINE)
    assert _cp1_issues(text) == ()


def dated_alone(text: str) -> str:
    """The Net debt rows and the reconciliation dated by the day alone, as the pack allows."""
    for old, new in ((DATED, "2024-09-30"), ("FY2023 / 2023-09-30", "2023-09-30")):
        text = text.replace(f"| {old} | 24", f"| {new} | 24").replace(
            f"| {old} | 19", f"| {new} | 19"
        )
    return text


def fiscal_register_beside_dated_net_debt(**given) -> str:
    """Net debt rows and the reconciliation by the day alone; register rows by `FY2024`/`FY2023`."""
    text = dated_alone(build(**given))
    text = text.replace(f"| {DATED} | USD", "| FY2024 | USD")
    return text.replace("| FY2023 / 2023-09-30 | USD", "| FY2023 | USD")


def test_a_register_by_fiscal_year_beside_date_only_net_debt_ties_across_the_forms():
    assert _cp1_issues(fiscal_register_beside_dated_net_debt()) == ()
    reg = register(overrides={("Total debt / EBITDA", "FY2024"): ["25,068", "3,813", "6.53"]})
    text = fiscal_register_beside_dated_net_debt(reg=reg)
    issues = [i for i in _cp1_issues(text) if "the numerator" in i]
    named(only(tuple(issues)), "Total debt / EBITDA", "25,068", "24,880", "188")


def test_a_register_period_that_resolves_to_a_period_with_no_net_debt_row_is_refused():
    periods = (*PERIODS, ("FY2022", "2021-10-01", "2022-09-30"))
    text = build(periods=periods)
    row = re.search(
        r"^\| Total debt / EBITDA \|.*\| FY2024 / 2024-09-30 \|.*$", text, re.MULTILINE
    )[0]
    text = text.replace(row, row + "\n" + row.replace("FY2024 / 2024-09-30", "FY2022"))
    issues = [i for i in _cp1_issues(text) if "matches no Period cell" in i]
    named(
        only(tuple(issues)),
        "Total debt / EBITDA",
        "FY2022",
        "FY2024 / 2024-09-30",
    )


def test_a_reconciliation_period_that_matches_no_net_debt_row_is_refused():
    text = build(recon=("24,319", "561", "24,880")).replace(
        f"| {DATED} | 24,319", "| 30 September 2024 | 24,319"
    )
    sole(text, "Debt principal to carrying value", "30 September 2024", "matches no Period cell")


def test_a_net_debt_table_dated_by_the_day_ties_register_rows_written_with_that_date():
    text = build().replace(DATED, "2024-09-30").replace("FY2023 / 2023-09-30", "2023-09-30")
    text = re.sub(r"^\| FY2024 \| (?=\d\.\d\d \|)", "| 2024-09-30 | ", text, flags=re.MULTILINE)
    text = re.sub(r"^\| FY2023 \| (?=\d\.\d\d \|)", "| 2023-09-30 | ", text, flags=re.MULTILINE)
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
    issues = _cp1_issues(elsewhere)
    assert any("T4.6 Balance sheet" in i and "## Calculations" in i for i in issues), issues
    assert any("0 of 6 required tables" in i for i in issues), issues


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


# --- fix round 2: the controller's rulings R8', R11-R14 (answer key typed from the brief) ---


def move_under_calculations(text: str, heading: str) -> str:
    """The `### heading` table cut out of `## Findings` and put under `## Calculations`."""
    block = re.search(rf"### {re.escape(heading)}\n.*?(?=\n\n###|\n\n## )", text, re.DOTALL)
    assert block, heading
    out = text.replace(block[0] + "\n\n", "", 1)
    return out.replace("## Calculations\n\n", f"## Calculations\n\n{block[0]}\n\n", 1)


def test_a_leverage_chart_under_calculations_is_refused_by_name_and_place():
    text = build(leverage=(("6.01", "4.88"), ("6.27", "5.17")))  # the register states 6.53
    issues = _cp1_issues(move_under_calculations(text, "Chart data: leverage"))
    assert any("Chart data: leverage" in i and "## Calculations" in i for i in issues), issues


def test_a_fenced_second_chart_heading_before_the_real_one_is_refused():
    text = build()
    real = re.search(r"### Chart data: leverage\n.*?(?=\n\n###)", text, re.DOTALL)[0]
    wrong = real.replace("6.53", "6.01")
    text = text.replace(real, f"```\n{wrong}\n```\n\n{real}", 1)
    issues = _cp1_issues(text)
    assert any("Chart data: leverage" in i and "code fence" in i for i in issues), issues


def test_net_debt_data_under_calculations_is_refused():
    issues = _cp1_issues(move_under_calculations(build(), "Net debt data"))
    assert any("Net debt data" in i and "## Calculations" in i for i in issues), issues


def test_every_table_the_check_reads_must_be_written_once_inside_findings():
    for heading in (
        *(s.heading for s in check.STATEMENTS),
        check.REGISTER_HEADING,
        check.RECON_HEADING,
        check.NET_DEBT_HEADING,
        check.LADDER_HEADING,
        *check.CHART_COLUMNS,
    ):
        copy = f"### {heading}\n\nSynthetic.\n\n"
        twice = build().replace(f"### {heading}", copy + f"### {heading}", 1)
        issues = _cp1_issues(twice)
        assert any(heading in i and "more than once" in i for i in issues), (heading, issues)


def date_only(text: str) -> str:
    """Every Period cell of the fixture written as the day alone (the Period table keeps its
    labels and dates)."""
    text = text.replace(DATED, "2024-09-30").replace("FY2023 / 2023-09-30", "2023-09-30")
    text = re.sub(r"^\| FY2024 \| (\d\.\d\d)", r"| 2024-09-30 | \1", text, flags=re.MULTILINE)
    return re.sub(r"^\| FY2023 \| (\d\.\d\d)", r"| 2023-09-30 | \1", text, flags=re.MULTILINE)


def principal_as_debt(**kwargs) -> str:
    """Gross debt 25,068 (the contractual principal) in Net debt, register, chart and the
    reconciliation, against T4.6 Total Debt 24,880: the known failure of the 10-K."""
    net_debt = {**NET_DEBT, DATED: ("25,068", "6,261", "18,807")}
    reg = register(
        overrides={
            ("Total debt / EBITDA", "FY2024"): ["25,068", "3,813", "6.57"],
            ("Net debt / EBITDA", "FY2024"): ["18,807", "3,813", "4.93"],
            ("Total debt / adjusted EBITDA", "FY2024"): ["25,068", "4,173", "6.01"],
            ("Net debt / adjusted EBITDA", "FY2024"): ["18,807", "4,173", "4.51"],
        }
    )
    return build(
        net_debt=net_debt,
        reg=reg,
        leverage=(("6.57", "4.93"), ("6.27", "5.17")),
        recon=("24,319", "749", "25,068"),
        **kwargs,
    )


def eBITDA_3000(**kwargs) -> str:
    reg = register(overrides={("EBITDA / cash interest", "FY2024"): ["3,000", "1,158", "2.59"]})
    return build(reg=reg, cover=("2.59", "2.71"), **kwargs)


@pytest.mark.parametrize("dated", [False, True], ids=["FY form", "date only"])
def test_a_fiscal_year_gross_debt_that_is_not_total_debt_is_refused_in_either_period_form(dated):
    text = principal_as_debt()
    text = date_only(text) if dated else text
    sole(text, "Net debt data", "Gross debt 25,068", "Total Debt", "24,880", "difference 188")


@pytest.mark.parametrize("dated", [False, True], ids=["FY form", "date only"])
def test_a_fiscal_year_ebitda_that_is_not_the_statement_is_refused_in_either_period_form(dated):
    text = eBITDA_3000()
    text = date_only(text) if dated else text
    sole(text, "EBITDA / cash interest", "3,000", "3,813", "EBITDA (Reported)", "difference 813")


def test_a_cash_interest_operand_that_is_not_the_statement_line_is_refused():
    reg = register(overrides={("EBITDA / cash interest", "FY2024"): ["3,813", "1,000", "3.81"]})
    sole(
        build(reg=reg, cover=("3.81", "2.71")),
        "EBITDA / cash interest",
        "1,000",
        "1,158",
        "Cash Interest Paid",
        "difference 158",
    )


def test_the_full_fixture_passes_with_every_period_cell_written_as_the_day_alone():
    assert _cp1_issues(date_only(build())) == ()


def test_a_period_cell_with_a_date_that_is_not_the_period_tables_end_is_refused():
    text = build().replace(DATED, "FY2024 / 2024-09-29")
    issues = _cp1_issues(text)
    assert any(
        "FY2024 / 2024-09-29" in i and "2024-09-30" in i and "Period table" in i for i in issues
    ), issues


def test_a_period_cell_whose_label_is_not_a_period_table_row_is_refused():
    text = build().replace(DATED, "FY2025 / 2024-09-30")
    issues = _cp1_issues(text)
    assert any("FY2025 / 2024-09-30" in i and "Period table" in i for i in issues), issues


def test_a_handoff_with_no_period_table_is_one_table_short():
    issue = sole(build(periods=()), "5 of 6 required tables", "Period table")
    assert "| Period | Start | End |" in issue


def test_a_statement_column_with_no_period_table_row_is_refused():
    text = build(periods=PERIODS[:1])  # no FY2023 row
    issues = _cp1_issues(text)
    assert any("FY2023" in i and "Period table" in i for i in issues), issues


def test_a_period_the_period_table_dates_twice_differently_is_refused():
    text = build(periods=(*PERIODS, ("FY2024", "2023-10-01", "2024-10-01")))
    assert any("FY2024" in i and "twice" in i for i in _cp1_issues(text))


def test_a_fiscal_year_ending_in_february_is_tied_by_its_date_not_its_label_arithmetic():
    # Fiscal 2024 ends 2025-02-01 and is headed FY2024 in the statements and the Period table.
    periods = (("FY2024", "2024-02-04", "2025-02-01"), ("FY2023", "2023-02-05", "2024-02-03"))
    text = build(periods=periods).replace(DATED, "2025-02-01")
    text = text.replace("FY2023 / 2023-09-30", "2024-02-03")
    text = re.sub(r"^\| FY2024 \| (\d\.\d\d)", r"| 2025-02-01 | \1", text, flags=re.MULTILINE)
    text = re.sub(r"^\| FY2023 \| (\d\.\d\d)", r"| 2024-02-03 | \1", text, flags=re.MULTILINE)
    assert _cp1_issues(text) == ()
    wrong = text.replace("| 3,813 | 3,148 |", "| 3,900 | 3,148 |")  # T4.4 reported EBITDA FY2024
    assert any("EBITDA (Reported)" in i and "3,900" in i for i in _cp1_issues(wrong))


def test_an_interim_only_handoff_has_no_statement_tie():
    periods = (("9M 2025", "2024-10-01", "2025-06-30"), ("9M 2024", "2023-10-01", "2024-06-30"))
    text = build(periods=periods).replace(DATED, "2025-06-30")
    text = text.replace("FY2023 / 2023-09-30", "2024-06-30")
    text = text.replace("| Line item | FY2024 | FY2023 |", "| Line item | 9M 2025 | 9M 2024 |")
    text = re.sub(r"^\| FY2024 \| (\d\.\d\d)", r"| 2025-06-30 | \1", text, flags=re.MULTILINE)
    text = re.sub(r"^\| FY2023 \| (\d\.\d\d)", r"| 2024-06-30 | \1", text, flags=re.MULTILINE)
    assert _cp1_issues(text) == ()
    assert _cp1_issues(text.replace("| 3,813 | 3,148 |", "| 3,000 | 3,148 |")) == ()


def test_the_no_column_advice_names_a_header_the_pack_accepts():
    text = build().replace("| Line item | FY2024 | FY2023 |", "| Line item | FY2024 | FY2022 |")
    advice = [
        found[1]
        for issue in _cp1_issues(text)
        if (found := re.search(r"add the column, headed `([^`]*)`", issue))
    ]
    assert advice and set(advice) == {"FY2023"}


EUR_GAP = "Not supplied: reported in EUR millions"


def eur_issuer(*, cover_stated: bool) -> str:
    overrides = {}
    for name, rows in REGISTER.items():
        for period, (num, den, value) in zip(("FY2024", "FY2023"), rows, strict=True):
            keep = cover_stated and "cash interest" in name
            overrides[(name, period)] = [num, den, value] if keep else [EUR_GAP] * 3
    reg = register(overrides=overrides)
    gap = (EUR_GAP, EUR_GAP)
    return build(
        net_debt={p: (EUR_GAP, EUR_GAP, EUR_GAP) for p in NET_DEBT},
        reg=reg,
        leverage=(gap, gap),
        cover=gap if not cover_stated else ("3.29", "2.71"),
        recon=("24,319", "561", EUR_GAP),
    ).replace("| USD millions |", "| EUR millions |")


@pytest.mark.parametrize("cover_stated", [False, True], ids=["six rows gapped", "cover stated"])
def test_a_eur_issuer_with_gapped_us_dollar_tables_is_refused_naming_its_money_unit(cover_stated):
    # C1 reverses the old premise (a EUR issuer's money tables were gapped US$m tables): its
    # money tables are in `EURm`, so these US$m ones are refused and the advice names `EURm`.
    issues = _cp1_issues(eur_issuer(cover_stated=cover_stated))
    assert issues and any("`EURm`" in i for i in issues), issues


@pytest.mark.parametrize("cell", ["\uff12\uff14\uff0c\uff18\uff18\uff10", "24,88O", "24.880,0"])
def test_a_figure_a_tie_cannot_read_is_refused_not_skipped(cell):
    # Fullwidth digits, a letter O and a European grouping are not plain ASCII-digit numbers.
    net_debt = {**NET_DEBT, DATED: (cell, "6,261", "18,619")}
    issues = _cp1_issues(build(net_debt=net_debt))
    assert any("Gross debt" in i and cell in i and "plain number" in i for i in issues), issues


def test_a_chart_cell_that_is_not_a_number_is_refused_by_the_tie():
    issues = _cp1_issues(build(leverage=(("6.5x", "4.88"), ("6.27", "5.17"))))
    assert any("6.5x" in i and "plain number" in i for i in issues), issues


# --- fix round 2, Low 2: one test per mutant the re-review found surviving ---


def test_two_statement_columns_with_the_same_header_are_refused():
    text = build().replace("| Line item | FY2024 | FY2023 |", "| Line item | FY2024 | FY2024 |", 1)
    assert any("two columns headed `FY2024`" in i for i in _cp1_issues(text))


def findings_with_a_fenced_section_line(fence: str) -> str:
    """A fence inside `## Findings` holding a line that, read outside a fence, closes it."""
    return build().replace(
        "## Findings\n\n", f"## Findings\n\n{fence}\n## Notes\n{fence.strip()}\n\n", 1
    )


@pytest.mark.parametrize("fence", ["~~~", "  ```", "```"])
def test_a_section_line_inside_a_fence_does_not_end_findings(fence):
    assert _cp1_issues(findings_with_a_fenced_section_line(fence)) == ()


def test_a_reconciliation_or_ladder_cell_over_twenty_five_characters_is_refused():
    huge = "1" + "0" * 25
    issues = _cp1_issues(build(recon=(huge, "561", "24,880")))
    assert any("25 characters" in i for i in issues), issues
    ladder = (huge, *LADDER[1:])
    assert any("25 characters" in i for i in _cp1_issues(build(ladder=ladder)))


def test_a_reconciliation_or_ladder_cell_that_is_not_a_number_is_refused():
    issues = _cp1_issues(build(recon=("24,319", "5 61", "24,880")))
    assert any("5 61" in i and "plain number" in i for i in issues), issues
    gap = "Not supplied: the ladder is incomplete"
    ladder = ("93", "9x", "92", "6,637", "4,768", "12,637")
    issues = _cp1_issues(build(ladder=ladder, recon=(gap, "561", "24,880")))
    assert any("9x" in i and "plain number" in i for i in issues), issues


# --- round 3: refuse the inputs on which the readers of a handoff disagree ----------------------

LEVERAGE_ROW = "| FY2023 | 6.27 | 5.17 | x | Synthetic. |"


@pytest.mark.parametrize(
    ("char", "code"),
    [("\x0c", "U+000C"), (" ", "U+2028"), ("\r", "U+000D"), ("\x85", "U+0085")],
)
def test_an_invisible_line_break_inside_a_row_is_refused(char, code):
    text = build()
    assert LEVERAGE_ROW in text
    text = text.replace(LEVERAGE_ROW, LEVERAGE_ROW.replace("Synthetic.", f"Syn{char}thetic."))
    issues = _cp1_issues(text)
    assert any(code in i and "invisible line-break character" in i for i in issues), issues


def test_an_html_comment_is_refused():
    text = build().replace("## Calculations\n\nNone.", "## Calculations\n\n<!-- note -->\n\nNone.")
    issues = _cp1_issues(text)
    assert any("<!--" in i and "HTML comment" in i for i in issues), issues


@pytest.mark.parametrize(
    "variant",
    [
        "###  Chart data: leverage",
        "#### Chart data: leverage",
        "**Chart data: leverage**",
        "### Chart data: leverage ",
    ],
)
def test_a_variant_of_a_checked_heading_is_refused(variant):
    text = build().replace("## Calculations\n\nNone.", f"## Calculations\n\n{variant}\n\nNone.")
    issues = _cp1_issues(text)
    assert any("exactly `### Chart data: leverage`" in i for i in issues), issues


LEVERAGE_HEAD = "### Chart data: leverage\n\n"
FENCED_ROW = "| FY2024 | 6.01 | 4.51 | x | Synthetic. |"


@pytest.mark.parametrize(("open_", "close"), [("```", "```"), ("```\n~~~", "~~~\n```")])
def test_a_fenced_table_straight_after_a_checked_heading_is_refused(open_, close):
    text = build().replace(
        LEVERAGE_HEAD, f"{LEVERAGE_HEAD}{open_}\n{FENCED_ROW}\n# end\n{close}\n\n", 1
    )
    issues = _cp1_issues(text)
    assert any("header row" in i and "Chart data: leverage" in i for i in issues), issues


def test_an_indented_row_after_a_table_is_refused():
    text = build().replace(
        LEVERAGE_ROW, f"{LEVERAGE_ROW}\n  | FY2022 | 6.01 | 4.51 | x | Synthetic. |", 1
    )
    issues = _cp1_issues(text)
    assert any("blank line" in i and "Chart data: leverage" in i for i in issues), issues


def test_a_table_without_a_separator_row_is_refused():
    text = build().replace(
        "| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit | Basis and "
        "limitation |\n| --- | --- | --- | --- | --- |\n",
        "| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit | Basis and "
        "limitation |\n",
        1,
    )
    issues = _cp1_issues(text)
    assert any("separator" in i and "Chart data: leverage" in i for i in issues), issues


def test_a_fenced_json_block_under_its_own_heading_is_no_issue():
    block = "### Forecast inputs (machine-readable)\n\n```json\n{}\n```\n\n"
    text = build().replace("## Calculations", f"{block}## Calculations", 1)
    assert _cp1_issues(text) == ()


def _periods_of(**ends: str) -> tuple[tuple[str, str, str], ...]:
    return tuple((label, "2023-10-01", end) for label, end in ends.items())


@pytest.mark.parametrize(
    ("fy24_end", "net_debt_date"),
    [
        ("2024-09-30", "2024-09-29"),
        ("2024-09-28", "2024-09-30"),
        ("2024-06-30", "2024-09-30"),
    ],
)
def test_a_date_that_ends_no_period_row_is_refused(fy24_end, net_debt_date):
    periods = (("FY2024", "2023-10-01", fy24_end), PERIODS[1])
    net_debt = {net_debt_date: NET_DEBT[DATED], **{k: v for k, v in NET_DEBT.items() if k != DATED}}
    issues = _cp1_issues(build(periods=periods, net_debt=net_debt))
    assert any("Net debt data" in i and "ends on" in i and net_debt_date in i for i in issues), (
        issues
    )


def test_a_period_cell_naming_a_period_table_end_still_passes_when_it_is_interim():
    periods = (*PERIODS, ("9M 2025", "2024-10-01", "2025-06-30"))
    text = build(periods=periods).replace(DATED, "2025-06-30")
    assert not any("ends on" in i for i in _cp1_issues(text))


GAP = "Not supplied: no financial sources"


def _blocked(periods) -> str:
    def rows(spec):
        return {label: (GAP, GAP) for label in spec}

    return build(
        periods=periods,
        income=rows(["EBITDA (Reported)"]),
        cash_flow=rows(check.STATEMENTS[1].fixed),
        balance=rows(check.STATEMENTS[2].fixed),
        reg=table(
            "T4.9 Calculation register",
            list(check.REGISTER_COLUMNS),
            [["Not assessable", *[GAP] * 12]],
        ),
        leverage=((GAP, GAP), (GAP, GAP)),
        cover=(GAP, GAP),
        ladder=(GAP,),
        recon=(GAP, GAP, GAP),
        net_debt={"FY2024 / 2024-09-30": (GAP, GAP, GAP)},
    )


def test_a_blocked_module_may_leave_its_period_dates_unsupplied():
    assert _cp1_issues(_blocked((("FY2024", GAP, GAP), ("FY2023", GAP, GAP)))) == ()


def test_a_period_row_without_dates_beside_stated_figures_is_refused():
    periods = (("FY2024", GAP, GAP), PERIODS[1])
    issues = _cp1_issues(build(periods=periods))
    assert any("`Period table` row `FY2024`" in i and "YYYY-MM-DD" in i for i in issues), issues


def test_a_blocked_module_with_no_period_table_is_still_counted():
    issue = only(_cp1_issues(_blocked(())))
    named(issue, "5 of 6 required tables")


# --- one period key for every match between tables (R11) -----------------------------------


def dated_register_layout(text: str) -> str:
    """Net debt, the register and the reconciliation by the day alone; the charts left as built."""
    return text.replace("FY2024 / 2024-09-30", "2024-09-30").replace(
        "FY2023 / 2023-09-30", "2023-09-30"
    )


def test_charts_by_fiscal_year_beside_a_date_only_register_pass():
    text = dated_register_layout(build())
    assert "| FY2024 | 6.53 | 4.88 |" in text and "| 2024-09-30 | USD | US$m | 6.53 |" in text
    assert _cp1_issues(text) == ()


def test_a_wrong_chart_figure_beside_a_date_only_register_is_refused():
    text = dated_register_layout(build(leverage=(("6.01", "4.88"), ("6.27", "5.17"))))
    named(only(_cp1_issues(text)), "Chart data: leverage", "FY2024", "6.01", "6.53", "0.52")


def test_charts_dated_beside_a_register_in_the_fiscal_year_form_pass():
    text = build()
    text = re.sub(r"^\| FY2024 \| (6\.53|3\.29)", r"| 2024-09-30 | \1", text, flags=re.MULTILINE)
    text = re.sub(r"^\| FY2023 \| (6\.27|2\.71)", r"| 2023-09-30 | \1", text, flags=re.MULTILINE)
    assert "| 2024-09-30 | 6.53 |" in text and "FY2024 / 2024-09-30" in text
    assert _cp1_issues(text) == ()


def test_a_chart_row_with_no_register_row_says_so_and_does_not_call_a_figure_unstated():
    text = build().replace("| FY2023 | 6.27 |", "| FY2022 | 6.27 |")
    issues = _cp1_issues(text)
    assert len(issues) == 2, issues  # one per leverage column the row states
    named(issues[0], "Chart data: leverage", "FY2022", "6.27", "no Total debt / EBITDA row")
    assert all("not stated" not in i and "Not supplied" not in i for i in issues)


def test_a_chart_row_dated_with_an_interim_end_does_not_match_the_fiscal_year_row():
    periods = (*PERIODS, ("Q1 FY2025", "2024-10-01", "2024-12-31"))
    text = build(periods=periods).replace("| FY2024 | 3.29 |", "| 2024-12-31 | 3.29 |")
    issue = only(_cp1_issues(text))
    named(
        issue, "Chart data: interest cover", "2024-12-31", "3.29", "no EBITDA / cash interest row"
    )
    assert "not stated" not in issue and "Not supplied" not in issue


# --- the issuer's own currency (owner ruling C1, 2026-11-13) --------------------------------


def money(code: str) -> str:
    """The money unit, written here independently of the code under test."""
    return "US$m" if code == "USD" else f"{code}m"


def relabel(text: str, code: str = "GBP") -> str:
    """The fixture with its statements in `code` and every CP-1 money table in its money unit."""
    text = text.replace("| USD | US$m |", f"| {code} | {money(code)} |")
    text = text.replace("USD millions", f"{code} millions")
    text = text.replace("USD thousands", f"{code} thousands")
    return text.replace("US$m", money(code))


def owner_tables(unit: str) -> str:
    """The CP-1 owner tables `build()` does not print, so a whole handoff passes `_owned_issues`."""
    tail = ["Reporting unit", "Basis and limitation"]
    return "\n\n".join(
        [
            table(
                "Chart data: liquidity",
                ["Period", "Cash", "Undrawn committed facilities", *tail],
                [["FY2024", "6,261", "500", unit, BASIS], ["FY2023", "3,472", "400", unit, BASIS]],
            ),
            table(
                "Chart data: revenue and EBITDA",
                ["Period", "Revenue", "Adjusted EBITDA", *tail],
                [["FY2024", "11,000", "4,173", unit, BASIS]],
            ),
            table(
                "Chart data: debt stack",
                ["Facility", "Ranking", "Secured", "Amount", "Cumulative leverage", *tail],
                [["Term loan", "1", "Yes", "12,000", "3.1", unit, BASIS]],
            ),
            table(
                "Chart data: EBITDA bridge",
                ["Step", "Amount", *tail],
                [
                    ["Reported EBITDA", "3,813", unit, BASIS],
                    ["Add-backs", "360", unit, BASIS],
                    ["Adjusted EBITDA", "4,173", unit, BASIS],
                ],
            ),
            table(
                "Confidence inputs",
                ["Input", "Value"],
                [
                    [name, value]
                    for name, value in zip(
                        INPUT_ROWS,
                        [
                            "8",
                            "2",
                            "2",
                            "0",
                            "0",
                            "0",
                            "0",
                            "0",
                            "95",
                            "100",
                            "pass",
                            "0",
                            "0",
                            "1",
                        ],
                        strict=True,
                    )
                ],
            ),
            table(
                "Post-balance-sheet adjustments",
                ["Event", "Date", "Amount", "Pro forma net debt", "Pro forma net leverage", *tail],
                [["None found in the sources read", *["—"] * 4, unit, BASIS]],
            ),
        ]
    )


def complete(text: str, unit: str = "US$m") -> str:
    return text.replace("\n\n## Calculations", "\n\n" + owner_tables(unit) + "\n\n## Calculations")


def owned(text: str) -> list[str]:
    return _owned_issues("CP-1", [], text)


def in_section(text: str, heading: str, old: str, new: str) -> str:
    """`old` replaced by `new` inside the one table under `### heading`."""
    start = text.index(f"### {heading}")
    end = text.find("\n### ", start + 1)
    end = len(text) if end < 0 else end
    return text[:start] + text[start:end].replace(old, new) + text[end:]


def test_the_usd_handoff_passes_whole_in_us_dollars():
    assert owned(complete(build())) == []


def test_a_gbp_issuer_states_leverage_in_its_own_currency():
    text = relabel(build())
    assert "6.53" in text and "GBPm" in text and "US$m" not in text
    assert owned(complete(text, "GBPm")) == []


@pytest.mark.parametrize("code", ["EUR", "JPY", "CHF"])
def test_another_currency_takes_its_code_and_m(code):
    assert owned(complete(relabel(build(), code), f"{code}m")) == []


def test_a_gbp_balance_sheet_in_thousands_ties_to_the_gbpm_tables():
    text = relabel(balance_in_thousands(thousands(BALANCE)))
    assert text.count("GBP thousands") == len(BALANCE)
    assert owned(complete(text, "GBPm")) == []


def test_gbp_statements_with_us_dollar_tables_are_refused_naming_the_money_unit():
    text = complete(build().replace("USD millions", "GBP millions"))
    issues = owned(text)
    assert issues and any("`GBPm`" in i for i in issues), issues


def test_usd_statements_with_gbpm_tables_are_refused():
    text = relabel(build()).replace("GBP millions", "USD millions")
    issues = owned(complete(text, "GBPm"))
    assert issues and any("`US$m`" in i for i in issues), issues


def test_a_gbp_gross_debt_that_is_not_the_total_debt_is_refused_with_the_difference():
    text = relabel(build(balance={**BALANCE, "Total Debt": ("25,068", "19,750")}))
    issue = only(_cp1_issues(text))
    named(issue, "Gross debt", "25,068", "Total Debt", "24,880", "difference 188")


def test_gbp_thousands_that_are_one_million_off_the_gbpm_figure_are_refused():
    debt = {**thousands(BALANCE), "Total Debt": ("24,881,000", "19,750,000")}
    issue = only(_cp1_issues(relabel(balance_in_thousands(debt))))
    named(issue, "Total Debt", "24,881,000", "24,880", "difference 1")


def test_fixed_rows_in_two_currencies_are_refused_naming_both_rows_and_codes():
    text = in_section(relabel(build()), "T4.6 Balance sheet", "GBP millions", "USD millions")
    issue = next(i for i in _cp1_issues(text) if "currency" in i)
    named(issue, "GBP", "USD", "EBITDA (Reported)", "Total Assets")


def test_a_register_currency_that_is_not_the_statement_currency_is_refused():
    text = relabel(build()).replace("| GBP | GBPm |", "| USD | GBPm |")
    issues = [i for i in _cp1_issues(text) if "Currency" in i]
    assert len(issues) == 12, issues
    named(issues[0], "`USD`", "`GBP`")


def test_a_register_unit_that_is_not_the_money_unit_is_refused():
    text = relabel(build()).replace("| GBP | GBPm |", "| GBP | US$m |")
    issues = [i for i in _cp1_issues(text) if "the money unit" in i and "`GBPm`" in i]
    assert len(issues) == 12, issues


def test_the_adjusted_ebitda_row_in_another_currency_than_the_statements_is_refused():
    gbp_text = relabel(build())
    row = "| EBITDA (Adjusted) | 4,173 | 3,395 | GBP millions |"
    assert row in gbp_text
    text = gbp_text.replace(row, row.replace("GBP millions", "USD millions"))
    issues = [i for i in owned(complete(text, "GBPm")) if "currency" in i]
    assert len(issues) == 1, issues
    named(issues[0], "GBP", "USD", "EBITDA (Adjusted)")


def test_the_adjusted_ebitda_row_in_the_statement_currency_is_not_refused():
    assert owned(complete(relabel(build()), "GBPm")) == []


def test_figures_with_no_single_statement_currency_are_refused_not_assumed_usd():
    text = build().replace("| USD millions |", "| Not supplied: no unit |")
    issues = owned(complete(text))
    assert any("do not state one currency" in i for i in issues), issues


def test_money_unit_is_the_one_currency_of_the_fixed_rows():
    assert check.money_unit(build()) == "US$m"
    assert check.money_unit(relabel(build())) == "GBPm"
    assert check.money_unit(relabel(balance_in_thousands(thousands(BALANCE)))) == "GBPm"
    mixed = in_section(relabel(build()), "T4.6 Balance sheet", "GBP millions", "USD millions")
    assert check.money_unit(mixed) is None
    assert check.money_unit(build().replace("| USD millions |", "| n/a |")) is None
    assert check.money_unit("## Findings\n\nNone.\n") is None


def test_a_money_table_with_no_money_unit_refuses_a_stated_figure_and_accepts_gaps():
    stated = relabel(complete(build()), "GBP")
    issues = chart_issues(stated, DEBT_RECON)
    assert len(issues) == 3, issues  # each of the three stated figures
    for issue in issues:
        named(issue, "do not state one currency")
    gap = "Not supplied: pending"
    row = f"| FY2024 / 2024-09-30 | {gap} | {gap} | {gap} | GBPm | {BASIS} |"
    header = (
        "| Period | Contractual principal | Reconciling items | Carrying value "
        "| Reporting unit | Basis and limitation |"
    )
    rule = "| --- | --- | --- | --- | --- | --- |"
    section = f"### Debt principal to carrying value\n\n{header}\n{rule}\n{row}"
    assert chart_issues(section, DEBT_RECON) == ()


def test_a_wrong_unit_cell_in_the_statement_currency_is_told_to_use_the_money_unit():
    text = relabel(build()).replace(
        "| 24,319 | 561 | 24,880 | GBPm |", "| 24,319 | 561 | 24,880 | US$m |"
    )
    issues = chart_issues(text, DEBT_RECON, money="GBPm")
    assert len(issues) == 3, issues
    named(issues[0], "US$m", "use `GBPm`", "Not supplied: reported in US$m")


@settings(deadline=None, max_examples=40)
@given(
    code=st.sampled_from(sorted(CURRENCY_CODES)),
    other=st.sampled_from(sorted(CURRENCY_CODES)),
    in_thousands=st.booleans(),
)
def test_a_handoff_passes_with_its_own_currencys_money_unit_and_fails_with_any_other(
    code, other, in_thousands
):
    base = (
        build(
            income=thousands(INCOME),
            cash_flow=thousands(CASH_FLOW),
            balance=thousands(BALANCE),
        ).replace("USD millions", "USD thousands")
        if in_thousands
        else build()
    )
    assert owned(complete(relabel(base, code), money(code))) == []
    if other != code:
        wrong = relabel(base, code).replace(money(code), money(other))
        assert owned(complete(wrong, money(other)))


# ---- C2 (owner ruling, 2026-11-13): an issuer that states only an adjusted EBITDA may head the
# leverage and interest-cover columns with the adjusted names. Figures are the contract's answer
# key (adjusted EBITDA 4,173 / 3,395): FY2024 5.96, 4.46, 3.60; FY2023 5.82, 4.79, 2.93.
ADJUSTED_NAMES = ("Total debt / adjusted EBITDA", "Net debt / adjusted EBITDA")
COVER_NAME = "Adjusted EBITDA / cash interest"
ONLY_ADJUSTED = "Not supplied: the issuer states adjusted EBITDA only"
LEVERAGE_HEAD = "| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit |"
COVER_HEAD = "| Period | EBITDA / cash interest | Reporting unit |"
ADJUSTED_FIGURES = {
    "leverage": (("5.96", "4.46"), ("5.82", "4.79")),
    "cover": ("3.60", "2.93"),
}


def adjusted_only(*, headed: bool = True, **given) -> str:
    """The passing fixture with reported EBITDA a stated gap, the reported register rows removed,
    the adjusted ones kept and (`headed`) both chart tables headed with the adjusted names."""
    rows = {k: v for k, v in REGISTER.items() if k in (*ADJUSTED_NAMES, COVER_NAME)}
    use = {
        "income": {**INCOME, "EBITDA (Reported)": (ONLY_ADJUSTED, ONLY_ADJUSTED)},
        "reg": register(rows),
        **ADJUSTED_FIGURES,
        **given,
    }
    text = build(**use)
    if not headed:
        return text
    text = text.replace(
        LEVERAGE_HEAD, f"| Period | {ADJUSTED_NAMES[0]} | {ADJUSTED_NAMES[1]} | Reporting unit |"
    )
    return text.replace(COVER_HEAD, f"| Period | {COVER_NAME} | Reporting unit |")


def test_the_adjusted_only_handoff_passes_and_states_the_answer_keys_figures():
    text = adjusted_only()
    assert _cp1_issues(text) == ()
    assert owned(complete(text)) == []
    for figure in ("5.96", "4.46", "3.60", "5.82", "4.79", "2.93"):
        assert f"| {figure} |" in text or f"| {figure} " in text, figure
    assert "Total debt / EBITDA" not in text and "| EBITDA / cash interest" not in text


def test_the_adjusted_only_handoff_relabelled_gbp_passes():
    assert owned(complete(relabel(adjusted_only()), "GBPm")) == []


def test_the_unchanged_reported_fixture_still_passes_through_the_whole_check():
    assert owned(complete(build())) == []


def test_adjusted_headers_beside_stated_reported_ebitda_are_refused_naming_the_period():
    text = adjusted_only(income=INCOME, reg=register())  # reported 3,813 is stated for FY2024
    issue = next(i for i in _cp1_issues(text) if "so the chart columns are the reported" in i)
    named(issue, "reported EBITDA is stated for FY2024", "the adjusted ratios stay in the register")


def test_adjusted_headers_are_refused_when_reported_ebitda_is_stated_for_one_period_only():
    income = {**INCOME, "EBITDA (Reported)": (ONLY_ADJUSTED, "3,148")}
    issues = _cp1_issues(adjusted_only(income=income))
    issue = only(tuple(i for i in issues if "reported EBITDA is stated" in i))
    named(issue, "reported EBITDA is stated for FY2023, so the chart columns are the reported")
    assert "FY2024" not in issue


def test_adjusted_headers_are_refused_when_a_reported_register_row_states_its_operand():
    text = adjusted_only(reg=register())  # T4.4 reported is a gap, the register states 3,813
    assert any("reported EBITDA is stated for FY2024" in i for i in _cp1_issues(text))


def test_a_table_mixing_reported_and_adjusted_names_is_refused():
    text = adjusted_only().replace(
        f"| Period | {ADJUSTED_NAMES[0]} |", "| Period | Total debt / EBITDA |"
    )
    issues = _cp1_issues(text)
    assert any("Total debt / EBITDA" in i and "Net debt / adjusted EBITDA" in i for i in issues)
    assert any("never both" in i or "all with the" in i for i in issues), issues
    assert any("Net debt / adjusted EBITDA" in i for i in owned(complete(text)))


def test_leverage_on_adjusted_names_with_interest_cover_on_the_reported_name_is_refused():
    text = adjusted_only().replace(f"| Period | {COVER_NAME} | Reporting unit |", COVER_HEAD)
    issues = _cp1_issues(text)
    assert any("different EBITDA" in i and "Chart data: interest cover" in i for i in issues)


def test_a_chart_figure_that_differs_from_the_adjusted_register_row_is_refused():
    text = adjusted_only(leverage=(("6.01", "4.46"), ("5.82", "4.79")))
    issue = only(_cp1_issues(text))
    named(issue, "Total debt / adjusted EBITDA", "6.01", "5.96", "difference 0.05")


def test_an_adjusted_operand_that_is_not_the_adjusted_statement_line_is_refused():
    rows = {k: v for k, v in REGISTER.items() if k in (*ADJUSTED_NAMES, COVER_NAME)}
    rows[COVER_NAME] = (("4,000", "1,158", "3.45"), rows[COVER_NAME][1])
    text = adjusted_only(reg=register(rows), cover=("3.45", "2.93"))
    issue = only(_cp1_issues(text))
    named(issue, "4,000", "4,173", "EBITDA (Adjusted)", "difference 173")


def test_reported_headers_carrying_the_adjusted_ratios_are_refused():
    text = adjusted_only(headed=False)  # 5.96 stated under `Total debt / EBITDA`, no reported row
    issues = _cp1_issues(text)
    assert any("Total debt / EBITDA" in i and "5.96" in i and "no" in i for i in issues), issues


def test_an_adjusted_column_with_a_figure_and_no_adjusted_register_row_is_refused():
    rows = {k: v for k, v in REGISTER.items() if k in ADJUSTED_NAMES[:1] + (COVER_NAME,)}
    issues = _cp1_issues(adjusted_only(reg=register(rows)))
    issue = next(i for i in issues if "Net debt / adjusted EBITDA" in i)
    named(issue, "4.46", "no Net debt / adjusted EBITDA row")


def test_an_issuer_states_adjusted_only_reads_the_chart_and_register_by_the_twin_names():
    assert check.ADJUSTED_TWIN == dict(
        zip((m.name for m in check.METRICS[:3]), (m.name for m in check.METRICS[3:]), strict=True)
    )
    assert check.ADJUSTED_TWIN["EBITDA / cash interest"] == COVER_NAME


@settings(deadline=None, max_examples=60)
@given(
    where=st.integers(0, 5),
    cents=st.integers(0, 99_999),
)
def test_any_chart_cell_of_the_adjusted_only_handoff_off_its_register_value_is_refused(
    where, cents
):
    truth = ["5.96", "4.46", "5.82", "4.79", "3.60", "2.93"]
    changed = f"{cents // 100}.{cents % 100:02d}"
    if changed == truth[where]:
        return
    values = [*truth[:4], *truth[4:]]
    values[where] = changed
    text = adjusted_only(
        leverage=((values[0], values[1]), (values[2], values[3])), cover=(values[4], values[5])
    )
    assert _cp1_issues(text), (where, changed)
