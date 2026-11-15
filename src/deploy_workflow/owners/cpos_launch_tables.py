"""The tables CP-OS asks of a module beside its report routes (the chart strip, owner, event
and map tables) and the checks that read them (``chart_issues``). Moved from
``cpos_launch``; the launcher re-exports every name.
"""

import re
from collections import Counter
from collections.abc import Collection, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from typing import Any, cast

from deploy_workflow import confidence
from deploy_workflow.changes import same_period
from deploy_workflow.credit_os_catalogue import chart_row, period_order
from deploy_workflow.handoff_delivery import MarkdownRoute
from deploy_workflow.markdown_delivery import STRIP_FIGURES
from deploy_workflow.owners import cpos_cp1_check as cp1_check
from deploy_workflow.owners.cpos_launch_methods import _SCORE, METHODS
from deploy_workflow.prose_checks import ISO_4217

# Fixed so any run's charts can be read without issuer-specific row selectors.
MONEY = cp1_check.MONEY  # CP-1's money tables' unit, resolved per handoff by `money_unit`.
CHART_TABLES: dict[str, tuple[str, tuple[str, ...], str]] = {
    "S.1": ("Chart data: leverage", ("Total debt / EBITDA", "Net debt / EBITDA"), "x"),
    "S.2": ("Chart data: interest cover", ("EBITDA / cash interest",), "x"),
    "S.3": ("Chart data: liquidity", ("Cash", "Undrawn committed facilities"), MONEY),
    "S.4": ("Chart data: debt maturities", ("Debt maturing",), MONEY),
}
CHART_BLOCKS = frozenset(STRIP_FIGURES) - {"yield-against-maturity"}
NOT_SUPPLIED = "Not supplied:"
PLAIN_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _chart_route(block_id: str, figure: str) -> MarkdownRoute:
    heading, columns, unit = CHART_TABLES[figure]
    return MarkdownRoute(
        module_id="CP-1",
        heading=heading,
        kind="chart",
        block_id=block_id,
        figure_id=cast(Any, figure),
        value_columns=columns,
        orientation="period-rows",
        # The route's class; CP-1's money unit is resolved per handoff (`_owner_table`).
        chart_unit=cast(Any, "US$m" if unit == MONEY else unit),
    )


@dataclass(frozen=True)
class OwnerTable:
    """A `### Chart data: ...` table an owning module is asked for beside the report's own charts.

    Only the library draws it, so it is not a delivery route. `steps` makes it a bridge: rows are
    steps, the first the opening amount and the last the closing, the rows between signed changes.
    Add a bridge or a period table for any module here and the instructions and the loop's
    validation follow."""

    heading: str
    value_columns: tuple[str, ...]
    chart_unit: str
    steps: bool = False
    rules: str = ""  # The catalogue guard for the view, sent to the module with the table.
    # A row table (debt stack, headroom, limits) states its own header up to the Reporting unit:
    # `numbers` are plain numbers or a stated gap (`in_unit`, default all, are in the Reporting
    # unit); `choices` fix a column's words; `may_gap` text columns may be a stated gap; `ranked`
    # is a column of whole numbers that must not fall down the rows.
    columns: tuple[str, ...] = ()
    numbers: tuple[str, ...] = ()
    in_unit: tuple[str, ...] = ()
    choices: tuple[tuple[str, tuple[str, ...]], ...] = ()
    may_gap: tuple[str, ...] = ()
    ranked: str = ""
    noun: str = "period"
    dates: tuple[str, ...] = ()  # YYYY-MM-DD calendar dates (or a stated gap).
    ordered: tuple[str, ...] = ()  # Stated numbers that must not fall left to right.
    counts: tuple[str, ...] = ()  # Whole numbers of zero or more (or a stated gap).
    not_before: tuple[str, ...] = ()  # (later, earlier) date columns: the first may not precede.
    one_unit: bool = False  # Every row states the same Reporting unit (one scale for the figure).
    series: str = ""  # A column whose distinct words are the figure's series, at most MAX_SERIES.
    unique: tuple[str, ...] = ()  # Columns whose values together name a row once.
    optional: bool = False  # The module writes the table only if the handoff supplies its case.
    events: bool = False  # A dated-event table: no unit or basis columns; dates by precision.
    edges: bool = False  # A node/edge map table: no unit or basis columns; an edge type's words.
    none_text: str = (
        ""  # The words of an Event cell that states none: the one row `_states_none` takes.
    )
    scored: bool = False  # The confidence inputs table: its rows are `confidence`'s, not columns.
    money_table: bool = False  # `chart_unit` is the handoff's resolved money unit (`MONEY` was it).

    @property
    def bare(self) -> bool:
        """A table with no Reporting unit or Basis and limitation columns."""
        return self.events or self.edges


NET_DEBT_HEADING = "Net debt data"  # not a `Chart data:` heading: the library does not draw it
NET_DEBT = OwnerTable(
    NET_DEBT_HEADING,
    ("Gross debt", "Cash", "Net debt"),
    MONEY,
    rules=(
        "Gross debt is total debt at balance-sheet carrying value (current plus long-term, net of"
        " issuance costs and discounts), not principal, and the Basis and limitation cell says "
        "what gross debt includes (for example securitization and finance leases the issuer "
        "carries within its debt lines) and states the principal total beside it. Cash is the "
        "same figure as the Cash column of the `Chart data: liquidity` "
        "table for that period. Net debt is gross debt less cash, worked with `calculate` and "
        "listed in `## Calculations`. Write one row per period you state, at least the latest "
        "balance-sheet date. `Period` is `FY2024 / 2024-09-30` for a fiscal year end (fiscal "
        "year, space, slash, space, the year-end date) and the date alone (`2025-06-30`) for an "
        "interim balance sheet: one form for every row of the table, each period once, and no "
        "other word in the cell (say `pro forma` or `reported` in the Basis and limitation cell)."
        " A row whose three figures are all stated is refused if net debt differs from gross debt"
        " less cash by any amount, and a row is refused if its cash differs from the liquidity "
        "table's for the same period."
    ),
)


def _decimal(cell: str) -> Decimal | None:
    return Decimal(cell.replace(",", "")) if PLAIN_NUMBER.fullmatch(cell) else None


def _unorderable_period(lines: list[str], rows: list[list[str]]) -> str | None:
    """The Period cell that keeps the pack from ordering the net debt table, or None when the
    table orders. The pack's own reader (`chart_row`) decides; only its ValueError is caught. The
    cell named is the first the reader's `period_order` rejects, else the first whose form differs
    from the first row's or that repeats an earlier one; a row of the wrong width is
    `chart_issues`'s, not this check's."""
    try:
        chart_row(lines, NET_DEBT_HEADING, prefix="")
    except ValueError:
        pass
    else:
        return None
    ordered: list[tuple[str, tuple[int, ...]]] = []
    for row in (r for r in rows[2:] if len(r) == len(rows[0])):
        key = period_order(row[0])
        if key is None:
            return row[0]
        ordered.append((row[0], key))
    for number, (period, key) in enumerate(ordered):
        if key[0] != ordered[0][1][0] or any(key == earlier for _, earlier in ordered[:number]):
            return period
    return None


def _net_debt_issues(text: str) -> tuple[str, ...]:
    """Each stated row of the net debt table holds net debt = gross debt - cash exactly, and its
    cash is the liquidity table's for the same period; its Period cells are ones the pack can
    order. A figure that is not stated is not checked; the table's own shape is `chart_issues`'s."""
    heading, liquidity = f"### {NET_DEBT_HEADING}", "### Chart data: liquidity"
    lines = text.splitlines()
    rows = _stated_rows(text, heading) if heading in lines else []
    if not rows or rows[0] != _chart_header(NET_DEBT):
        return ()
    liquid = _stated_rows(text, liquidity) if liquidity in lines else []
    cash_of = [(row[0], row[1]) for row in liquid[2:] if len(row) == 5 and liquid[0][1] == "Cash"]
    issues = []
    unordered = _unorderable_period(lines, rows)
    if unordered is not None:
        issues.append(
            f"`{heading}` Period `{unordered}` cannot be ordered: write "
            "`FY2024 / 2024-09-30` for a fiscal year end or the date alone (`2025-06-30`) for an "
            "interim balance sheet, one form for the whole table and each period once; put any "
            "other word in the Basis and limitation cell."
        )
    for row in rows[2:]:
        if len(row) != len(rows[0]):
            continue
        period, gross, cash, net = (row[0], *(_decimal(c) for c in row[1:4]))
        if gross is not None and cash is not None and net is not None and net != gross - cash:
            issues.append(
                f"`{heading}` {period}: net debt {row[3]} is not gross debt {row[1]} less cash "
                f"{row[2]}; correct the row, nothing is filled in for you."
            )
        for other, shown in cash_of:
            stated = _decimal(shown)
            if (
                cash is not None
                and stated is not None
                and same_period(period, other)
                and cash != stated
            ):
                issues.append(
                    f"`{heading}` {period}: cash {row[2]} is not the Cash {shown} stated "
                    f"for {other} in `{liquidity}`; correct whichever is wrong, and let this row's "
                    "Period carry the balance-sheet date so it matches one liquidity row."
                )
    return tuple(issues)


DEBT_RECON = OwnerTable(
    cp1_check.RECON_HEADING,
    cp1_check.RECON_COLUMNS,
    MONEY,
    rules=(
        "One row, for the balance-sheet date the maturity ladder is drawn at; `Period` is a Period "
        "cell of `Net debt data`. Contractual principal is the sum of the `Debt maturing` rows of "
        "`Chart data: debt maturities`. Reconciling items is one signed net figure: issuance "
        "costs, discounts and premiums, and any debt the ladder leaves out, each named in Basis "
        "and limitation and summed in `## Calculations`; a negative has a minus sign and a "
        "positive no plus sign (`561`, not `+561`). Carrying value is the Gross debt of "
        "`Net debt data` for the same period. Principal plus reconciling items must equal "
        "carrying value exactly. When "
        "the principal is a stated number, every `Debt maturing` cell must be one too."
    ),
)


POST_BS_NONE = "None found in the sources read"
POST_BS = OwnerTable(
    "Post-balance-sheet adjustments",
    (),
    "",
    columns=("Event", "Date", "Amount", "Pro forma net debt", "Pro forma net leverage"),
    numbers=("Amount", "Pro forma net debt", "Pro forma net leverage"),
    in_unit=("Amount", "Pro forma net debt"),
    dates=("Date",),
    noun="event",
    none_text=POST_BS_NONE,
    rules=(
        "One row per event after the balance-sheet date that changes net debt, such as an issue, "
        "repayment, acquisition, disposal or dividend that the sources state. Date is the event "
        "date: YYYY-MM-DD only when the source states the day; when it gives only a month, "
        "quarter or year, write `Not supplied: the source states <what it gives> only` and never "
        "invent a day. Amount is the event's effect on net debt, a plain number without a sign "
        "when net debt rises and with a minus sign when it falls; Pro forma net debt is "
        "year-end net debt after the event, both in the Reporting unit; Pro forma net leverage is "
        "the same net debt over the same EBITDA as the year-end net leverage, as times without "
        "an `x`. "
        "Work each figure with `calculate`; a figure you cannot state is `Not supplied: "
        "<reason>`; Basis and limitation names the event's source and what is not yet reflected. "
        "Do not add a pro forma row to any chart or net debt table."
    ),
)


def _owner_tables(module: str, routes: Sequence[MarkdownRoute]) -> tuple[OwnerTable, ...]:
    """The tables a module is asked for beside its report routes. CP-1 is on every pathway asked
    for all four chart tables CP-8's pack reads (owner, 2026-11-12, "Yes, all pathways"): those
    its report's chart blocks do not already route are asked as owner tables, with no new
    report section. It is also asked for the net debt table (owner, 2026-11-12, "Yes, add it")."""
    tables = OWNER_TABLES.get(module, ())
    if module != "CP-1":
        return tables
    routed = {r.heading for r in routes}
    chart = tuple(
        OwnerTable(h, cols, unit) for h, cols, unit in CHART_TABLES.values() if h not in routed
    )
    return (*chart, NET_DEBT, DEBT_RECON, POST_BS, *tables)


DIRECTIONS = ("Passes below", "Passes at or below", "Passes above", "Passes at or above")


# The catalogue's launcher-asked figures (docs/visualisations/catalogue.csv) that are not report
# strip figures: S.5 (CP-1-V05), the liquidity bridge (CP-2D-V01) and the refinancing need
# (CP-3C-V01).
OWNER_TABLES: dict[str, tuple[OwnerTable, ...]] = {
    "CP-1": (
        OwnerTable(
            "Chart data: revenue and EBITDA",
            ("Revenue", "Adjusted EBITDA"),
            MONEY,
            rules=(
                "The Adjusted EBITDA column is the EBITDA measure the method specifies; name its "
                "identity (reported, issuer-adjusted or house-adjusted) in Basis and "
                "limitation, and do not mix identities across rows. Every row is a comparable "
                "period of the same duration; one table must not mix durations (annual with "
                "quarterly or half-year); a period of another duration is "
                "`Not supplied: <reason>`."
            ),
        ),
        OwnerTable(
            "Chart data: debt stack",
            (),
            MONEY,
            rules=(
                "Rows run in legal rank order, most senior first. Ranking is the legal rank as "
                "a plain whole number (1 is most senior; equal ranks share a number); a "
                "facility whose legal rank no source states is left out and named under Gaps. "
                "Secured is Yes or No. Cumulative leverage is the stated cumulative debt "
                "through that facility over the common EBITDA denominator, as times without an "
                "`x`; state it only for a positive common EBITDA denominator, else "
                "`Not supplied: <reason>`. Name each facility's guarantor or obligor scope in "
                "Basis and limitation. Reporting unit is the Amount's unit only (the money unit): "
                "write leverage in times and any other note in Basis and limitation. An enterprise "
                "value is not a sourced fact merely because "
                "it is a chart marker: add no enterprise value row unless a source states it."
            ),
            columns=("Facility", "Ranking", "Secured", "Amount", "Cumulative leverage"),
            numbers=("Amount", "Cumulative leverage"),
            in_unit=("Amount",),
            choices=(("Secured", ("Yes", "No")),),
            ranked="Ranking",
            noun="facility",
        ),
        OwnerTable(
            "Chart data: EBITDA bridge",
            ("Amount",),
            MONEY,
            steps=True,
            rules=(
                "The first row is the reported measure and the last row is the specified "
                "adjusted measure the method names; name both in Basis and limitation. The "
                "rows between are the signed adjustments the method states, each as stated: do "
                "not manufacture intermediate adjustments from the endpoints. If the method "
                "states only the endpoints, or its adjustments do not reconcile them, write "
                "`Not supplied: <reason>` in every Amount."
            ),
        ),
    ),
    "CP-2H": (
        OwnerTable(
            "Chart data: rating triggers",
            (),
            "",
            rules=(
                "Agency names the agency and Trigger the trigger as the agency states it; "
                "Threshold and Current are the same metric on the same basis, in the Reporting "
                "unit; Direction says which side passes (the trigger is not reached). No rating "
                "probability is stated or implied. Where only a synthetic-source frame exists, "
                "write `Not supplied: <reason>` in Threshold and Current and state the "
                "synthetic-source limitation in Basis and limitation; name the agency basis of "
                "an agency-adjusted metric."
            ),
            columns=("Agency", "Trigger", "Threshold", "Current", "Direction"),
            numbers=("Threshold", "Current"),
            choices=(("Direction", DIRECTIONS),),
            noun="trigger",
        ),
    ),
    "CP-4": (
        OwnerTable(
            "Chart data: covenant headroom",
            (),
            "",
            rules=(
                "One row per covenant test the handoff settles. Preserve the quantity and the "
                "strictness of each test: Direction says which side passes, as the covenant "
                "defines it. Threshold and Current are the same quantity in the Reporting unit. "
                "Headroom is the stated headroom with its unit, as the method states it, never "
                "worked out here. The chart is not a legal compliance opinion."
            ),
            columns=("Test", "Threshold", "Current", "Headroom", "Direction"),
            numbers=("Threshold", "Current"),
            choices=(("Direction", DIRECTIONS),),
            may_gap=("Headroom",),
            noun="test",
        ),
    ),
    "CP-6": (
        OwnerTable(
            "Chart data: portfolio limits",
            (),
            "",
            rules=(
                "Rows come from the selected portfolio evaluation: Current exposure, Proposed "
                "exposure and Limit value are its stated figures in one Reporting unit; name the "
                "NAV denominator in Basis and limitation. Proposed exposure is `Not supplied: "
                "<reason>` when no proposal is evaluated. This module owns the interpretation; "
                "delivery only renders it. Do not state invented holdings or a new analytical "
                "owner's result."
            ),
            columns=("Limit", "Current exposure", "Proposed exposure", "Limit value"),
            numbers=("Current exposure", "Proposed exposure", "Limit value"),
            noun="limit",
        ),
    ),
    "CP-2D": (
        OwnerTable(
            "Chart data: liquidity bridge",
            ("Amount",),
            "US$m",
            steps=True,
            rules=(
                "Only accessible liquidity is bridged: restricted or trapped cash and uncertain "
                "facility access are not accessible liquidity, so exclude them or state each as "
                "its own step. Use the method's signed values and timing; name the basis in "
                "Basis and limitation."
            ),
        ),
    ),
    "CP-3C": (
        OwnerTable(
            "Chart data: refinancing need",
            ("Debt maturing", "Committed resources"),
            "US$m",
            rules=(
                "Committed resources exclude a refinancing that is only a suggested path; a "
                "resource shared by more than one need is counted once, never a double-counting. "
                "Name the maturity and funding basis in Basis and limitation."
            ),
        ),
    ),
}


PAIR_COLUMNS = ("Measure", "Prior period", "Prior", "Current period", "Current")
PAIR_GAPS = ("Prior period", "Current period")
PEER_COLUMNS = ("Metric", "Issuer", "Peer low", "Peer median", "Peer high", "Peer count")
PEER_NUMBERS = PEER_COLUMNS[1:]
PEER_BOUNDS = PEER_COLUMNS[2:5]
YIELD_COLUMNS = (
    "Instrument",
    "Maturity date",
    "Yield",
    "Spread",
    "Quote date",
    "Source class",
)


def _peer_range(heading: str, rules: str) -> OwnerTable:
    return OwnerTable(
        heading,
        (),
        "",
        rules=rules,
        columns=PEER_COLUMNS,
        numbers=PEER_NUMBERS,
        in_unit=PEER_NUMBERS[:-1],
        ordered=PEER_BOUNDS,
        counts=("Peer count",),
        noun="metric",
    )


PEER_RULES = (
    "Issuer, Peer low, Peer median and Peer high are the stated values of the method's settled "
    "observations; Peer count is the number of included peers behind the range, a plain "
    "number. Name the excluded peers, each with its reason, in Basis and limitation. A value "
    "that is not settled is `Not supplied: <reason>`, never zero. No other dispersion statistic "
    "is stated. "
)
# The catalogue's other launcher-asked figures: CP-1B (EU.1, EU.2), CP-1C (RV.3a, RV.3b), CP-3D
# (RV.1, a report strip figure that delivery does not ask for as a chart).
OWNER_TABLES |= {
    "CP-1B": (
        OwnerTable(
            "Chart data: prior and current results",
            (),
            "",
            rules=(
                "Pair only compatible quantities: Prior and Current are the same measure on a "
                "comparable perimeter and duration, otherwise `Not supplied: <reason>`. Every "
                "row states one Reporting unit; margin belongs on a separate percent panel, not "
                "in this table. Name the EBITDA identity (reported, issuer-adjusted or "
                "house-adjusted) in Basis and limitation. Prior period and Current period are "
                "the periods as the source labels them."
            ),
            columns=PAIR_COLUMNS,
            numbers=PAIR_COLUMNS[2::2],
            may_gap=PAIR_GAPS,
            one_unit=True,
            noun="measure",
        ),
        OwnerTable(
            "Chart data: margin and KPI changes",
            (),
            "",
            rules=(
                "A margin (the method's T1B.1 margin) and any sourced segment or KPI pair the "
                "handoff actually supplies; do not invent a KPI series. Prior and Current are "
                "the stated values, in the Reporting unit the row states. Percent change and "
                "percentage-point change remain distinct: no change is stated, and it is "
                "not worked out here. One row is one pair, a comparison and not a trend."
            ),
            columns=PAIR_COLUMNS,
            numbers=PAIR_COLUMNS[2::2],
            may_gap=PAIR_GAPS,
            noun="measure",
        ),
    ),
    "CP-1C": (
        _peer_range(
            "Chart data: peer range \u2014 percent metrics",
            PEER_RULES + "Percent metrics only (EBITDA margin, FFO / debt); multiples stay out "
            "of the percent table.",
        ),
        _peer_range(
            "Chart data: peer range \u2014 multiples",
            PEER_RULES + "Multiples only (total leverage, coverage); name the issuer and peer "
            "definitions in Basis and limitation, and do not calendarise or FX-convert peers. "
            "Percentages stay out of this table.",
        ),
    ),
    "CP-3D": (
        OwnerTable(
            "Chart data: yield against maturity",
            (),
            "",
            rules=(
                "One row per instrument with a quote. Yield is on the one yield measure named in "
                "Basis and limitation; YTM, discount margin and spread are never mixed in one "
                "table, so a row on another measure is `Not supplied: <reason>` in Yield. "
                "Spread is stated as the source gives it, with its unit. Maturity date and "
                "Quote date are YYYY-MM-DD dates; Source class names the quote's source class."
            ),
            columns=YIELD_COLUMNS,
            numbers=("Yield",),
            may_gap=("Spread",),
            dates=("Maturity date", "Quote date"),
            not_before=("Maturity date", "Quote date"),
            noun="instrument",
        ),
    ),
}

# CP-4C (DR.2 to DR.5). A value allocation is a step table the bridge check reads unchanged: the
# first row is the enterprise value (the opening), the costs and each class's distribution are the
# negative changes, and the last row is the value not distributed (the closing), so the opening
# plus the changes reconcile to it exactly. Available value is the running position after the
# costs and is stated in the text, not as a row the check would add twice.
MAX_SERIES = 3
ALLOCATION_RULES = (
    " Scenario identity is the label of its source valuation row; name it in Basis and "
    "limitation of the first row. The first row is the enterprise value as stated. The next rows "
    "are the costs and deductions, each a negative change. Then each class's distribution is a "
    "negative change, in the order the method states them: assume no legal pool order. The last "
    "row is the value not distributed after the last distribution (0 when all is allocated), so "
    "that the first row plus the changes reconcile to it. Available value is the running position "
    "after the costs: state it in Basis and limitation of the last cost row, not as a row. Do "
    "not invent an absent downside or stress case."
)


def _allocation(scenario: int) -> OwnerTable:
    ask = " Ask for this scenario only if the handoff supplies it." if scenario > 1 else ""
    rest = ALLOCATION_RULES if scenario == 1 else " The rules of scenario 1 apply."
    return OwnerTable(
        f"Chart data: value allocation \u2014 scenario {scenario}",
        ("Amount",),
        "US$m",
        steps=True,
        rules=f"Scenario {scenario} of the handoff's valuation rows.{ask}{rest}",
        optional=scenario > 1,
    )


OWNER_TABLES["CP-4C"] = (
    OwnerTable(
        "Chart data: recovery by class",
        (),
        "",
        rules=(
            "One row per class and scenario the handoff supplies; do not invent an absent "
            "downside or stress case. Claim and Recovery are the stated amounts in the Reporting "
            "unit, one unit for every row. Recovery % is the recovery percentage as the owner "
            "states it, a plain number without a percent sign, never worked out here from "
            "Recovery and Claim. Cap a recovery only as the method caps it; keep the entity and "
            "collateral pools and the legal limitations in Basis and limitation. This is the "
            "single enterprise value slice, not a complete multi-entity waterfall. At most 3 "
            "distinct scenarios, as the value allocation has three."
        ),
        columns=("Class", "Scenario", "Claim", "Recovery", "Recovery %"),
        numbers=("Claim", "Recovery", "Recovery %"),
        in_unit=("Claim", "Recovery"),
        one_unit=True,
        series="Scenario",
        unique=("Class", "Scenario"),
        noun="class and scenario",
    ),
    *(_allocation(n) for n in (1, 2, 3)),
)


# Package 5: one dated-event table asked of each lane's owning module (the Calendar tab draws a lane
# per module that supplies one). Lane name and catalogue guard; the header and checks are shared.
EVENT_COLUMNS = (
    *("Event date", "Date precision", "Published", "Event"),
    *("Status", "Source", "Credit relevance"),
)
EVENT_RULES = (
    "One row per dated event the handoff states. Event date is written at the precision the "
    "source gives and Date precision names it: `day` YYYY-MM-DD, `month` YYYY-MM, `quarter` "
    "YYYY-Qn, `year` YYYY. Never write a day the source does not state, and infer no day from a "
    "coarser date. Published is the date of the publication the row is taken from (YYYY-MM-DD), "
    "the one cited in Source: a row from a 10-K dated 2024-11-07 carries 2024-11-07 even when the "
    "event is a 2033 maturity, and it equals the event date when the document is published that "
    "day (an 8-K, an earnings release). Write `Not supplied: <reason>` only when that document "
    "states no date; never `\u2014` or `Not stated`. Status starts with `Historical`, "
    "`Scheduled` or `Scenario`, then ` \u2014 ` and the source's own words, e.g. `Scenario \u2014 "
    "modelled downgrade trigger`. Record each event once, in the lane of the module that owns "
    "it; another module refers to it in Credit relevance, it does not repeat the row. Source "
    "names the document and locator; Credit relevance says why the event matters. An event "
    "with no stated date has no row. A user-entered reminder's Status is `User reminder`. "
)
EVENT_LANES: dict[str, tuple[str, str]] = {
    "CP-0": (
        "Sources",
        (
            "Publication date, reporting period and import timestamp are different dates; the "
            "Event date is the date the event states, never the import timestamp. Unknown dates "
            "stay unplaced."
        ),
    ),
    "CP-1A": (
        "Issuer history",
        (
            "Separate announced, completed, cancelled and subsequent events in Status; never "
            "fold a later payment into an earlier financial period."
        ),
    ),
    "CP-1B": (
        "Earnings and guidance",
        (
            "Reporting-period end is not the release date. No guessed next earnings date: a future "
            "date only if the source explicitly schedules it."
        ),
    ),
    "CP-DR": (
        "Research catalysts",
        (
            "Retained supplied evidence only, with the impacted consumer in Credit relevance; "
            "date-free themes stay a watchlist, not a row."
        ),
    ),
    "CP-2D": (
        "Financing",
        (
            "Maturities, dated obligations and funding-gap windows. Maturity is not a refinancing "
            "commitment. Do not double-count a facility CP-1 and CP-3C both state."
        ),
    ),
    "CP-2E": (
        "Hedges",
        (
            "Hedge expiries and dated terms the handoff actually retains. Notional is not "
            "effectiveness or fair value. No row without a stated date."
        ),
    ),
    "CP-2H": (
        "Ratings",
        (
            "Separate an observed rating action, a scheduled review and a modelled trigger in "
            "Status. A historical action only if the handoff states it."
        ),
    ),
    "CP-3": (
        "Instruments",
        (
            "Sourced maturity, call/put, coupon/reset and offer deadlines, with the security "
            "identity in Event. Do not create coupon schedules or option-exercise assumptions. "
            "Unknown dates stay unplaced."
        ),
    ),
    "CP-3C": (
        "Refinancing",
        (
            "Source-dated maturities, call windows and explicit deadlines. Show analyst milestones "
            "separately from contractual deadlines, in Status; preserve contingent triggers."
        ),
    ),
    "CP-4": (
        "Legal",
        (
            "A fixed deadline only when the source or legal module establishes the triggering date "
            "and calculation; otherwise state the relative condition under Gaps, with no dated row."
        ),
    ),
    "CP-6": (
        "Decision and watch",
        (
            "Explicit decision and assigned review dates with sources. Undated conditions stay a "
            "watchlist. A user-entered reminder is labelled `User reminder` in Status, separate "
            "from a sourced issuer event."
        ),
    ),
}
for _module, (_lane, _guard) in EVENT_LANES.items():
    OWNER_TABLES[_module] = (
        *OWNER_TABLES.get(_module, ()),
        OwnerTable(
            f"Events: {_lane}",
            (),
            "",
            rules=EVENT_RULES + _guard,
            columns=EVENT_COLUMNS,
            choices=(("Date precision", ("day", "month", "quarter", "year")),),
            events=True,
        ),
    )


DASHES = ("\u2014", "-", "\u2013")  # An Evidence cell that is only a dash states nothing.
EDGE_COLUMNS = ("From", "Relationship", "Edge type", "To", "Evidence")
EDGE_RULES = (
    "One row per edge the handoff states, From and To each one named node: the same name for the "
    "same node in every row. Edge type is exactly one of the words listed; Relationship and "
    "Evidence are stated in your own words from the source, never blank. No weights, "
    "probabilities, coordinates or likelihoods; no edge the handoff does not state. "
)
FACTS = ("Documentary Fact", "Management Language", "Analyst Interpretation")
NARROW = (
    "The current narrow registers alone do not establish a complete graph: draw an edge only "
    "from the broader handoff, with the applicable document and jurisdiction in Evidence. "
)
# Heading, owner, edge types, the catalogue guard (docs/visualisations/catalogue.csv).
MAPS: tuple[tuple[str, str, tuple[str, ...], str], ...] = (
    (
        "Map: ownership and control",
        "CP-1A",
        ("Ownership", "Legal control", "Guarantee", "Other stated"),
        (
            "Undisclosed percentages stay unknown. Ownership, legal control and guarantees use "
            "different labelled edges. No inferred sponsor willingness."
        ),
    ),
    (
        "Map: operating model to credit",
        "CP-1A",
        (*FACTS, "Insufficient Information"),
        (
            "Evidence to mechanism to credit implication; every edge stated in the handoff. No "
            "weighted cash-flow arrows without amounts."
        ),
    ),
    (
        "Map: credit-risk transmission",
        "CP-2",
        (*FACTS, "Insufficient Information"),
        (
            "Driver to mechanism to creditor outcome. Only stated causal links, in qualitative "
            "categories. Do not invent likelihood or impact coordinates."
        ),
    ),
    (
        "Map: stress scenario",
        "CP-2A",
        ("Assumption", "Test outcome", "Explanation"),
        (
            "Branches describe computed conditions, not probabilities. No forecast date from a "
            "static stress."
        ),
    ),
    (
        "Map: legal entities",
        "CP-4",
        ("Ownership", "Guarantee", "Security", "Structural claim"),
        NARROW + "Require explicit edges, applicable document and jurisdiction.",
    ),
    (
        "Map: intercreditor",
        "CP-4",
        ("Payment rank", "Security rank", "Enforcement control", "Standstill", "Release"),
        NARROW + "Economic ranking and enforcement control are different edges; no numerical "
        "recovery without CP-4C inputs.",
    ),
    (
        "Map: support and contradiction",
        "CP-5",
        ("Supports", "Contradicts", "Unresolved"),
        (
            "Labelled edges for support, contradiction and unresolved between claim, source and "
            "derived-fact identities. No automatic causal or confidence weight based on edge count."
        ),
    ),
)
CONFIDENCE = OwnerTable(confidence.HEADING, (), "", scored=True)
for _module, _paths in METHODS.items():
    if _SCORE in _paths:  # The method carries the score the module may not state: it states inputs.
        OWNER_TABLES[_module] = (*OWNER_TABLES.get(_module, ()), CONFIDENCE)
for _heading, _module, _types, _guard in MAPS:
    OWNER_TABLES[_module] = (
        *OWNER_TABLES.get(_module, ()),
        OwnerTable(
            _heading,
            (),
            "",
            rules=f"{EDGE_RULES}Edge type words: {', '.join(_types)}. {_guard}",
            columns=EDGE_COLUMNS,
            choices=(("Edge type", _types),),
            edges=True,
        ),
    )


def _owner_table(table: MarkdownRoute | OwnerTable) -> OwnerTable:
    if isinstance(table, OwnerTable):
        return table
    unit = MONEY if table.module_id == "CP-1" and table.chart_unit == "US$m" else table.chart_unit
    return OwnerTable(table.heading, table.value_columns, str(unit))


def _chart_header(table: MarkdownRoute | OwnerTable) -> list[str]:
    spec = _owner_table(table)
    first = "Step" if spec.steps else "Period"
    leading = list(spec.columns) or [first, *spec.value_columns]
    if spec.bare:
        return leading
    return [*leading, "Reporting unit", "Basis and limitation"]


def _stated_rows(text: str, heading: str) -> list[list[str]]:
    lines = text.splitlines()
    rows = []
    for line in lines[lines.index(heading) + 1 :]:
        if line.startswith("#"):
            break
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def _decimals(number: str) -> int:
    return len(number.partition(".")[2])


def _bridge_issues(heading: str, rows: list[list[str]]) -> list[str]:
    """A step table is a check on what the module stated, never a derivation: nothing is filled.

    Every amount is a plain signed number, or every one is `Not supplied: <reason>` (a bridge the
    module cannot state). Opening plus the stated changes must equal the closing; each amount has
    at most the table's own number of decimals, so the sum is exact and any difference is real."""
    amounts = [row[1] for row in rows]
    unsupplied = [
        a.startswith(NOT_SUPPLIED) and a.removeprefix(NOT_SUPPLIED).strip() for a in amounts
    ]
    if not rows:
        return [f"`{heading}` needs an opening and a closing row."]
    if all(unsupplied):
        return []
    if len(rows) < 2:
        return [f"`{heading}` needs an opening and a closing row."]
    if not all(PLAIN_NUMBER.fullmatch(a) for a in amounts):
        return [
            (
                f"`{heading}`: every Amount must be a plain signed number (a gap is "
                "`Not supplied: <reason>` in every Amount, so no partial bridge is drawn)."
            )
        ]
    values = [Decimal(a.replace(",", "")) for a in amounts]
    opening, *changes, closing = values
    if opening + sum(changes, Decimal(0)) != closing:
        total = opening + sum(changes, Decimal(0))
        return [
            (
                f"`{heading}`: the opening {amounts[0]} plus the stated changes {total:,} does not "
                f"equal the closing {amounts[-1]}; state the missing step or correct the amount. "
                "Nothing is filled in for you."
            )
        ]
    return []


def _stated_gap(cell: str) -> bool:
    return cell.startswith(NOT_SUPPLIED) and bool(cell.removeprefix(NOT_SUPPLIED).strip())


CURRENCY_CODES = ISO_4217  # the repo's one list of real codes; LTM, PIK, RCF, TTM are not in it


_AMOUNT_WORD = r"(?:m|mn|bn|k|thousands?|millions?|billions?|amounts?)"
_SYMBOL_CODE = {"$": "USD", "\u20ac": "EUR", "\u00a3": "GBP", "\u00a5": "JPY"}


def _own_currency(chart_unit: str) -> tuple[set[str], list[str]]:
    """The currency codes and symbols the chart unit itself names (`GBPm`: GBP; `US$m`: USD)."""
    codes = {c for c in CURRENCY_CODES if re.search(rf"\b{c}", chart_unit)}
    codes |= {c for s, c in _SYMBOL_CODE.items() if s in chart_unit}
    return codes, [s for s, c in _SYMBOL_CODE.items() if c in codes]


def _names_currency(text: str, codes: Collection[str], symbols: str) -> bool:
    """Whether `text` names one of `codes` (or a symbol of `symbols`) in a currency position only:
    next to an amount word or unit (`GBPm`, `EUR millions`, `m EUR`), or standing alone (`(ILS)`,
    `and EUR`). A capitalised word that is also a code (`ALL figures`, `TOP line`) does not."""
    code = "(?:" + "|".join(sorted(codes)) + ")"
    alone = rf"(?:^|[(/;,&]|\band\b|\bor\b)\s*{code}\s*(?=$|[)/;,&])"
    beside = rf"\b{code}\s*{_AMOUNT_WORD}\b|\b{_AMOUNT_WORD}\s+{code}\b"
    return bool(
        re.search(f"{alone}|{beside}|[{symbols}]" if symbols else f"{alone}|{beside}", text)
    )


def _other_currency(rest: str, chart_unit: str) -> bool:
    """Whether `rest` (a unit cell without the chart unit) names a currency other than the chart
    unit's own: a code or symbol of another currency (`_names_currency`)."""
    own, own_symbols = _own_currency(chart_unit)
    symbols = "".join(s for s in _SYMBOL_CODE if s not in own_symbols)
    return _names_currency(rest, CURRENCY_CODES - own, symbols)


_MILLIONS = r"(?i:m|mn|millions?)"


def _millions_of(unit: str, codes: Collection[str]) -> bool:
    """Whether the whole cell is a millions spelling of one of `codes`: `GBP m`, `GBPmn`,
    `\u00a3m`, `GBP millions`, `millions GBP`."""
    symbols = [re.escape(s) for s, c in _SYMBOL_CODE.items() if c in codes]
    symbols += [r"US\$"] * ("USD" in codes)
    token = "(?:" + "|".join([*sorted(codes), *symbols]) + ")"
    return bool(re.fullmatch(rf"{token}\s*{_MILLIONS}|{_MILLIONS}\s+{token}", unit.strip()))


_PREFIXED = re.compile(rf"[A-Za-z]\s*[{''.join(_SYMBOL_CODE)}]")
_PREFIXED_RUN = re.compile(rf"[A-Za-z]+\s*[{''.join(_SYMBOL_CODE)}]")


def _unidentified_symbols(unit: str) -> tuple[bool, str]:
    """Whether `unit` has a currency symbol with a letter right before it, spaced or not (`C$`,
    `C $`, `A$`, `CN\u00a5`): the symbol alone does not say which currency it is. `US$` is the
    launcher's own spelling of USD, so it is not one. Also returns `unit` with those prefixed
    symbols removed."""
    text = unit.replace("US$", "USD")
    return bool(_PREFIXED.search(text)), _PREFIXED_RUN.sub("", text)


def _money_advice(money: str, unit: str) -> str:
    """What to do about a cell that is not a CP-1 money table's unit. Only a millions spelling of
    the statement currency is told to use the money unit: the same currency at another scale is
    restated first, so no figure is read 1,000 times too large; another currency keeps the gap.
    A letter-prefixed symbol is not identified as the statement currency, so it is told to use the
    money unit only if the figure is that currency in millions, else to write the gap."""
    own, _ = _own_currency(money)
    gap = f"write `Not supplied: reported in {unit}`"
    if _millions_of(unit, own):
        return f"use `{money}`."
    prefixed, rest = _unidentified_symbols(unit)
    if prefixed and not _other_currency(rest, money):
        return f"use `{money}` if the figure is in the statement currency in millions, else {gap}."
    if _millions_of(unit, CURRENCY_CODES):
        return f"use `{money}` if the figure is in the statement currency, else {gap}."
    if _names_currency(unit, own, "".join(_own_currency(money)[1])) and not _other_currency(
        unit, money
    ):
        return f"restate the figure in millions of the statement currency and write `{money}`."
    return f"{gap}."


def _unit_advice(spec: OwnerTable, unit: str) -> str:
    """What to do about a unit cell that is not the chart unit. A cell that holds the chart unit
    and adds other words is a unit cell holding more than the unit: its amounts are sound, so the
    advice is to cut the cell, never to replace the amounts with gaps. When the rest names another
    currency (`_other_currency`) the amounts may really be in it, so the gap advice stays. A ratio
    table written in a money unit is told to write `x`."""
    own = re.compile(rf"{re.escape(spec.chart_unit)}(?!\w)")
    if (
        spec.chart_unit
        and own.search(unit)
        and not _other_currency(own.sub("", unit), spec.chart_unit)
    ):
        return (
            f"the Reporting unit must be exactly `{spec.chart_unit}` (the Amount's unit only); "
            "move the rest to Basis and limitation."
        )
    if spec.chart_unit == "x" and re.fullmatch(r"US\$m|[A-Z]{3}m", unit):
        return "write `x`, the unit of a ratio."
    if spec.money_table:
        return _money_advice(spec.chart_unit, unit)
    return f"write `Not supplied: reported in {unit}`."


NO_MONEY = (
    "the statement tables do not state one currency, so no money unit is known; state every "
    "statement's Unit in the issuer's one currency, or write `Not supplied: <reason>`."
)


def _number_issue(spec: OwnerTable, name: str, cell: str, unit: str) -> str | None:
    if _stated_gap(cell):
        return None
    if not PLAIN_NUMBER.fullmatch(cell):
        return f"{name} `{cell}` must be a plain number or `Not supplied: <reason>`."
    if spec.chart_unit == MONEY and name in (spec.in_unit or spec.numbers):
        return f"{name} {cell} is stated, but {NO_MONEY}"
    if spec.chart_unit and name in (spec.in_unit or spec.numbers) and unit != spec.chart_unit:
        return (
            f"{name} in {unit} cannot be charted as {spec.chart_unit}; {_unit_advice(spec, unit)}"
        )
    return None


def _iso_date(cell: str) -> bool:
    try:
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", cell)) and bool(date.fromisoformat(cell))
    except ValueError:
        return False


def _order_issue(spec: OwnerTable, header: list[str], row: list[str]) -> str | None:
    """The stated numbers of `ordered` columns must not fall left to right (a gap is skipped)."""
    stated = [
        row[header.index(n)] for n in spec.ordered if PLAIN_NUMBER.fullmatch(row[header.index(n)])
    ]
    values = [Decimal(cell.replace(",", "")) for cell in stated]
    if values == sorted(values):
        return None
    return f"{' <= '.join(spec.ordered)} must hold in that order; stated {', '.join(stated)}."


def _dates_issue(spec: OwnerTable, header: list[str], row: list[str]) -> str | None:
    """A stated maturity before its own quote date is a matured instrument, sent back."""
    later, earlier = (row[header.index(name)] for name in spec.not_before)
    if _iso_date(later) and _iso_date(earlier) and later < earlier:
        return f"{spec.not_before[0]} {later} is before {spec.not_before[1]} {earlier}."
    return None


EVENT_SHAPES = {"month": r"\d{4}-(?:0[1-9]|1[0-2])", "quarter": r"\d{4}-Q[1-4]", "year": r"\d{4}"}
EVENT_STATUS = re.compile(
    r"(?:Historical|Scheduled|Scenario) \u2014 \S|User reminder(?: \u2014 \S|$)"
)
EVENT_KINDS = "Historical, Scheduled or Scenario"
PUBLISHED_FORMS = (
    "the YYYY-MM-DD date of the publication the row is taken from (cited in Source), or "
    "`Not supplied: <reason>` only when that document states no date; `\u2014` and `Not stated` "
    "are not accepted"
)
EVENT_FORMS = {"day": "YYYY-MM-DD", "month": "YYYY-MM", "quarter": "YYYY-Qn", "year": "YYYY"}


def _event_issues(spec: OwnerTable, header: list[str], row: list[str]) -> list[str]:
    """An event date must be in the form its precision names, never a coarser or finer one."""
    if not spec.events:
        return []
    cells = dict(zip(header, row, strict=True))
    precision, stated, published = cells["Date precision"], cells["Event date"], cells["Published"]
    issues = []
    if precision in EVENT_FORMS and not _stated_gap(stated):
        legal = (
            _iso_date(stated)
            if precision == "day"
            else re.fullmatch(EVENT_SHAPES.get(precision, ""), stated)
        )
        if not legal:
            issues.append(
                f"Event date `{stated}` must be {EVENT_FORMS[precision]} at precision {precision}."
            )
    if not _stated_gap(published) and not _iso_date(published):
        issues.append(f"Published `{published}` must be {PUBLISHED_FORMS}.")
    if not _stated_gap(cells["Status"]) and not EVENT_STATUS.match(cells["Status"]):
        issues.append(
            f"Status `{cells['Status']}` must start with {EVENT_KINDS} and ` \u2014 `, "
            "or be `User reminder`."
        )
    return issues


def _cell_issue(spec: OwnerTable, name: str, cell: str, unit: str) -> str | None:
    """What is wrong with one cell of a row table, or None. Nothing is repaired or worked out."""
    allowed = dict(spec.choices).get(name)
    if name in ("Basis and limitation", "Reporting unit"):
        issue = None if cell else f"{name} is blank."
    elif spec.events and name == "Published":
        issue = None  # `_event_issues` owns the whole rule, so a bad cell is refused once.
    elif spec.edges and name == "Evidence" and cell in DASHES:
        issue = f"{name} `{cell}` is not evidence: write where the source names its source."
    elif name in spec.counts:
        legal = _stated_gap(cell) or re.fullmatch(r"\d+", cell)
        issue = None if legal else f"{name} `{cell}` must be a whole number of 0 or more."
    elif name in spec.numbers:
        issue = _number_issue(spec, name, cell, unit)
    elif name in spec.dates:
        issue = (
            None
            if _stated_gap(cell) or _iso_date(cell)
            else f"{name} `{cell}` must be YYYY-MM-DD; when the source states no day, write "
            "`Not supplied: the source states <what it gives> only`."
        )
    elif allowed is not None:
        issue = None if cell in allowed else f"{name} `{cell}` must be one of {', '.join(allowed)}."
    elif name == spec.ranked:
        legal = re.fullmatch(r"[1-9]\d*", cell)
        issue = None if legal else f"{name} `{cell}` must be a plain positive whole number."
    elif not cell or (_stated_gap(cell) and name not in spec.may_gap):
        issue = f"{name} is blank or not stated."
    else:
        issue = None
    return issue


def _states_none(spec: OwnerTable, header: list[str], rows: list[list[str]]) -> bool:
    """The one escape for every owner table: each row's cells before the Reporting unit (every cell
    of a bare table) are stated gaps, so the module states none; the unit and basis stay stated."""
    tail = 0 if spec.bare else 2
    if spec.none_text and len(rows) == 1 and rows[0][:1] == [spec.none_text]:
        return (
            len(rows[0]) == len(header)
            and all((c in DASHES or _stated_gap(c)) for c in rows[0][1 : len(header) - tail])
            and all(rows[0][len(header) - tail :])
        )
    return bool(rows) and all(
        len(row) == len(header)
        and all(_stated_gap(c) for c in row[: len(row) - tail])
        and all(row[len(row) - tail :])
        for row in rows
    )


def _near_none_issues(spec: OwnerTable, heading: str, event: str) -> list[str]:
    """An Event that is the none text with other case or punctuation is not the none row: it
    would pass as an event with gaps, so the module is told the exact text."""
    if not spec.none_text or event == spec.none_text:
        return []
    if event.casefold().strip(" .") != spec.none_text.casefold():
        return []
    advice = f"`{spec.none_text}` and the other cells as asked; any other Event names an event."
    return [f"`{heading}`: to state that there is no event, write the Event exactly {advice}"]


SEPARATOR_CELL = re.compile(r":?-{3,}:?")
SECOND_TABLE = "a second table under this heading: give it its own ### heading"


def _first_table(heading: str, rows: list[list[str]]) -> tuple[list[list[str]], list[str]]:
    """The rows of the table the heading owns. A separator row among the rows opens a second table
    (its header is the row before it): the rows from that header on are not this table's, and the
    one issue says so instead of reporting its header and separator as malformed rows."""
    for at, row in enumerate(rows):
        if at and all(SEPARATOR_CELL.fullmatch(cell) for cell in row):
            return rows[: at - 1], [f"`{heading}`: {SECOND_TABLE}."]
    return rows, []


def _row_table_issues(
    spec: OwnerTable, heading: str, header: list[str], rows: list[list[str]]
) -> list[str]:
    """A row table's rows against its fixed header, cell by cell, in the order stated."""
    rows, issues = _first_table(heading, rows)
    ranks = []
    if _states_none(spec, header, rows):
        return issues  # The module states none: valid, and nothing is drawn.
    for row in rows:
        if len(row) != len(header):
            issues.append(f"`{heading}` row needs {len(header)} cells: {' | '.join(row)}")
            continue
        issues += _near_none_issues(spec, heading, row[0])
        unit = row[-2]
        for name, cell in zip(header, row, strict=True):
            problem = _cell_issue(spec, name, cell, unit)
            if problem:
                issues.append(f"`{heading}` {row[0] or 'row'}: {problem}")
        issues += [f"`{heading}` {row[0]}: {p}" for p in _event_issues(spec, header, row)]
        order = _order_issue(spec, header, row) if spec.ordered else None
        if order:
            issues.append(f"`{heading}` {row[0]}: {order}")
        matured = _dates_issue(spec, header, row) if spec.not_before else None
        if matured:
            issues.append(f"`{heading}` {row[0]}: {matured}")
        if spec.ranked and row[header.index(spec.ranked)].isdecimal():
            ranks.append(int(row[header.index(spec.ranked)]))
    if ranks != sorted(ranks):
        issues.append(
            f"`{heading}`: rows must run in rank order, most senior first (ranks {ranks})."
        )
    if not rows:
        issues.append(f"`{heading}` needs at least one row.")
    seen = (
        {row[header.index(spec.series)] for row in rows if len(row) == len(header)}
        if spec.series
        else ()
    )
    if len(seen) > MAX_SERIES:
        issues.append(f"`{heading}`: at most {MAX_SERIES} distinct {spec.series} values are drawn.")
    keys = Counter(
        tuple(row[header.index(n)] for n in spec.unique)
        for row in rows
        if spec.unique and len(row) == len(header)
    )
    issues.extend(
        f"`{heading}`: {' / '.join(key)} is stated twice; one row names it once."
        for key, count in sorted(keys.items())
        if count > 1
    )
    if spec.one_unit and len({row[-2] for row in rows if len(row) == len(header)}) > 1:
        issues.append(f"`{heading}`: every row states one Reporting unit, as one scale is drawn.")
    return issues


def _misheaded(text: str, heading: str) -> tuple[str, ...]:
    """An optional table written under a near-miss heading (a hyphen for the dash, other case) is
    sent back naming the exact heading; otherwise its absence is the module's decision."""

    def plain(line: str) -> str:
        return " ".join(re.sub("[\u2010-\u2015-]", "-", line).lower().split())

    near = [line for line in text.splitlines() if plain(line) == plain(f"### {heading}")]
    return (f"Write the heading exactly as `### {heading}`, not `{near[0]}`.",) if near else ()


def _absent_issues(text: str, spec: OwnerTable, heading: str) -> tuple[str, ...]:
    near = _misheaded(text, spec.heading) if spec.optional or spec.bare else ()
    if spec.optional or near:  # An optional case not supplied is not asked for, nor drawn.
        return near
    return (f"Add `{heading}` inside ## Findings, with its table.",)


def _confidence_issues(text: str, heading: str) -> tuple[str, ...]:
    """`confidence` reads the table; a refusal is its reason, nothing is repaired. A blocked
    module's one not-assessable row is the form it was asked to write, so it is no refusal."""
    got = confidence.from_handoff(text)
    if isinstance(got, confidence.Refused) and not got.blocked:
        return (f"`{heading}`: {got.reason}.",)
    return ()


def _resolved(spec: OwnerTable, money: str | None) -> OwnerTable:
    """A `MONEY` table in the handoff's money unit; unchanged when there is none (`NO_MONEY`)."""
    if spec.chart_unit == MONEY and money:
        return replace(spec, chart_unit=money, money_table=True)
    return spec


def _unit_issue(spec: OwnerTable, unit: str) -> str | None:
    """What is wrong with a stated number whose row states `unit`, in a period table."""
    if spec.chart_unit == MONEY:
        return f"a number is stated, but {NO_MONEY}"
    if unit != spec.chart_unit:
        return (
            f"a number in {unit} cannot be charted as {spec.chart_unit}; {_unit_advice(spec, unit)}"
        )
    return None


def _adjusted(spec: OwnerTable) -> OwnerTable | None:
    """CP-1's leverage or interest-cover table headed with the adjusted names; None for any other
    table (only those two have a twin)."""
    columns = cp1_check.CHART_COLUMNS.get(spec.heading)
    if columns is None or spec.value_columns != columns:
        return None
    return replace(spec, value_columns=tuple(cp1_check.ADJUSTED_TWIN[c] for c in columns))


def _stated_header(spec: OwnerTable, rows: list[list[str]]) -> list[str]:
    """The header a chart table is asked for: its own, or for CP-1's two ratio tables the one with
    the adjusted names when that is what the handoff wrote (an issuer that states only an adjusted
    EBITDA)."""
    header, twin = _chart_header(spec), _adjusted(spec)
    if rows and twin is not None and rows[0] == _chart_header(twin):
        return rows[0]
    return header


def _header_issue(spec: OwnerTable, heading: str, header: list[str]) -> str:
    """The refusal of a chart table's header. The two ratio tables name both accepted headers: the
    adjusted one is for an issuer that states only an adjusted EBITDA."""
    twin = _adjusted(spec)
    if twin is None:
        return f"`{heading}` needs the table headed `| {' | '.join(header)} |`."
    return (
        f"`{heading}` needs the table headed `| {' | '.join(_chart_header(spec))} |` or, for an "
        f"issuer that states only adjusted EBITDA, `| {' | '.join(_chart_header(twin))} |`."
    )


def chart_issues(
    text: str, table: MarkdownRoute | OwnerTable, *, money: str | None = None
) -> tuple[str, ...]:
    """A chart table's cells reach the page as they are, so each must already be chart-ready.
    `money` is the handoff's money unit (`money_unit`); a `MONEY` table states it, and without
    one no figure of it is stated."""
    spec = _resolved(_owner_table(table), money)
    heading = f"### {spec.heading}"
    if heading not in text.splitlines():
        return _absent_issues(text, spec, heading)
    if spec.scored:
        return _confidence_issues(text, heading)
    rows = _stated_rows(text, heading)
    header = _stated_header(spec, rows)
    if not rows or rows[0] != header:
        return (_header_issue(spec, heading, header),)
    if spec.columns:
        return tuple(_row_table_issues(spec, heading, header, rows[2:]))
    stated = []
    body, issues = _first_table(heading, rows[2:])
    for row in body:
        if len(row) != len(header):
            issues.append(f"`{heading}` row needs {len(header)} cells: {' | '.join(row)}")
            continue
        period, *values, unit, basis = row
        stated.append(row)
        if not basis:
            issues.append(f"`{heading}` {period}: Basis and limitation is blank.")
        for value in values:
            if value.startswith(NOT_SUPPLIED) and value.removeprefix(NOT_SUPPLIED).strip():
                continue
            if not PLAIN_NUMBER.fullmatch(value):
                issues.append(
                    f"`{heading}` {period}: `{value} |` must be a plain number "
                    "or `Not supplied: <reason>`."
                )
            elif problem := _unit_issue(spec, unit):
                issues.append(f"`{heading}` {period}: {problem}")
    if spec.steps and not issues:
        issues += _bridge_issues(heading, stated)
    return tuple(issues)
