"""CP-1 period headers: the period a Markdown table header names.

Pure (no I/O). The period rules follow `src/deploy_vii/model/periods.py`: `6M` is `H1`, the year is
the fiscal year, and a header that is not exactly one period is not guessed at.
"""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal, Inexact, localcontext
from typing import NamedTuple

from deploy_workflow.owners import cp2g
from deploy_workflow.owners.cpos_forecast import _agrees, _cut, _plain, _signed

Period = tuple[str, int, int]
"""`(kind, fiscal year, quarters to date)`; kind is `QUARTER`, `YTD` or `FY`."""

_REVISED = r"(?: revised| recast| restated)?"
_HEADER = re.compile(
    rf"(?:FY ?(?P<fy>\d{{4}}){_REVISED}"
    r"|(?P<span>Q[1-4]|H1|6M|9M) ?(?:FY ?)?(?P<year>\d{4})"
    r"(?: revised| recast| restated|: [A-Za-z-]+ weeks ended \d{4}-\d{2}-\d{2})?)",
    re.ASCII,
)
_YTD_QUARTERS = {"H1": 2, "6M": 2, "9M": 3}


def period_of(header: str) -> Period | None:
    """The period a header names, or None when it is anything else."""
    found = _HEADER.fullmatch(_plain(header))
    if found is None:
        return None
    if found["fy"] is not None:
        return ("FY", int(found["fy"]), 4)
    span, year = found["span"], int(found["year"])
    if span in _YTD_QUARTERS:
        return ("YTD", year, _YTD_QUARTERS[span])
    return ("QUARTER", year, int(span[1]))


def period_label(period: Period) -> str:
    """`Q3 2025`, `H1 2025`, `9M 2025` or `FY2024`."""
    kind, year, quarters = period
    if kind == "FY":
        return f"FY{year}"
    if kind == "YTD":
        return f"{'H1' if quarters == 2 else '9M'} {year}"
    return f"Q{quarters} {year}"


Span = tuple[date, date]
Dates = dict[Period, Span]
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)
DATED_TWICE = (
    "CP-1's period table dates {label} more than once, differently; it is treated as undated."
)


def _date(cell: str) -> date | None:
    """The calendar date a cell prints as `YYYY-MM-DD`, else None."""
    text = _plain(cell)
    if _ISO_DATE.fullmatch(text) is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:  # the shape of a date but not a calendar day (2024-13-01)
        return None


def _dated_row(row: list[str]) -> tuple[Period, Span] | None:
    """The period and the dates a period-table row states, or None when it is not readable."""
    if len(row) < 3:
        return None
    period, start, end = period_of(row[0]), _date(row[1]), _date(row[2])
    if period is None or start is None or end is None or start > end:
        return None
    return period, (start, end)


def period_dates(tables: list[list[list[str]]]) -> tuple[Dates, tuple[str, ...]]:
    """The dated periods of CP-1's period tables (header `Period`, `Start`, `End`, more columns
    allowed) and the labels of periods whose rows disagree, which are left undated."""
    seen: dict[Period, set[Span]] = {}
    for table in tables:
        if not table or [_plain(cell) for cell in table[0][:3]] != ["Period", "Start", "End"]:
            continue
        for row in table[1:]:
            if (found := _dated_row(row)) is not None:
                seen.setdefault(found[0], set()).add(found[1])
    dates = {period: next(iter(spans)) for period, spans in seen.items() if len(spans) == 1}
    twice = tuple(period_label(period) for period, spans in seen.items() if len(spans) > 1)
    return dates, twice


_LTM_LABEL = re.compile(r"LTM Q[1-4] \d{4}", re.ASCII)
LtmDates = dict[str, set[Span]]


def ltm_dates(tables: list[list[list[str]]]) -> LtmDates:
    """The spans CP-1's period tables state for rows labelled `LTM Qn YYYY` (a label that is not a
    period; read only as a stock's balance date)."""
    seen: LtmDates = {}
    for table in tables:
        if not table or [_plain(cell) for cell in table[0][:3]] != ["Period", "Start", "End"]:
            continue
        for row in table[1:]:
            if len(row) < 3 or _LTM_LABEL.fullmatch(_plain(row[0])) is None:
                continue
            start, end = _date(row[1]), _date(row[2])
            if start is not None and end is not None and start <= end:
                seen.setdefault(_plain(row[0]), set()).add((start, end))
    return seen


NOT_A_CELL = "the base amount is not a table cell of CP-1"
NOT_NAMED = "the forecast inputs do not name the row and period of this line"
NO_REASON = "no reason was stated"
NO_SIGN = "the base cell is zero, so the sign of this row's figures is not known"
DIFFERENT = "CP-1 prints different figures for this line in {period}"
NOT_PRINTED = "CP-1 does not print this line for {period}"
LABEL_NOT_DATED = "CP-1's period table does not date {label}"
LABEL_OTHER_DAY = "CP-1 dates {label} to {end}, not the {anchor} the {what} ends"
_STOCKS = frozenset({"debt", "cash", "undrawn"})
NOT_UNDER_A_PERIOD = (
    "CP-1 prints the base amount only under a column header that is not a period ({header})"
)
_YEAR = re.compile(r"(?<!\d)(?:19|20)\d\d(?!\d)")
_MAX_DIGITS = 38  # a numeral of more digits than the exact context holds is not a figure
_MAX_REASON = 200
_BASE_SIGNED = frozenset({"interest", "taxes", "capex"})  # signed by their base cell


class ByColumn(NamedTuple):
    """A forecast-inputs name for a cell of a table with one row per period: the period's row
    label and the measure's column header (the pair `(row, period)` otherwise)."""

    row: str
    column: str


@dataclass(frozen=True)
class Line:
    """One base operand's history. `reason` set: no history for the line. `unread`: the
    year-bearing headers of its tables that are not periods (`unread_rows`: the row labels of a
    table read by column). `balances`: for a stock, the figures under each `LTM Qn YYYY` label."""

    values: dict[Period, Decimal] = field(default_factory=dict)
    gaps: dict[Period, str] = field(default_factory=dict)
    reason: str | None = None
    unread: tuple[str, ...] = ()
    unread_rows: tuple[str, ...] = ()
    balances: dict[str, set[Decimal]] = field(default_factory=dict)


@dataclass(frozen=True)
class _Row:
    table: int
    figures: dict[Period, set[Decimal]]
    columns: set[Period]
    signless: bool = False  # an unsigned zero base cell and no common sign in the row
    balances: dict[str, set[Decimal]] = field(default_factory=dict)


@dataclass(frozen=True)
class _Hit:
    """A table row with at least one cell that reads as the base amount: `agreeing` holds the
    column and printed number of each such cell."""

    table: int
    header: list[str]
    row: list[str]
    agreeing: list[tuple[int, Decimal]]


def _number(cell: str) -> Decimal | None:
    """The signed number a cell prints. None when it is not one, or when its numeral has more than
    38 digits (a figure the exact context cannot hold is not read, so no sum of it can round)."""
    if sum(ch.isdigit() for ch in _plain(cell)) > _MAX_DIGITS:
        return None
    with localcontext(cp2g._EXACT):
        return _signed(cell)


def _published(key: str, number: Decimal, flip: bool) -> Decimal:
    """A row's figure in a period: working capital reversed; interest, taxes and capex negated
    in every period when the row's base cell is printed negative; any other operand as printed."""
    return -number if key == "wc" or flip else number


def _hits(tables: list[list[list[str]]], key: str, amount: Decimal, label: str) -> list[_Hit]:
    """The rows labelled `label` with a cell that reads as the amount under a header of the same
    table."""
    found: list[_Hit] = []
    for index, table in enumerate(tables):
        header, rows = (table[0], table[1:]) if table else ([], [])
        for row in rows:
            if not row or _plain(row[0]) != label:
                continue
            agreeing = [
                (column, number)
                for column, cell in enumerate(row[1:], 1)
                if column < len(header)
                and (number := _number(cell)) is not None
                and _agrees(key, number, amount)
            ]
            if agreeing:
                found.append(_Hit(index, header, row, agreeing))
    return found


def _negative(cell: str) -> bool:
    """Whether a cell is written negative: with brackets or a minus (ASCII or Unicode), zero too."""
    return _plain(cell).startswith(("(", "-", "\u2212"))


def _row_sign(hit: _Hit, base_column: int) -> bool | None:
    """Whether an interest, taxes or capex row is printed negative. The base cell says, even at
    zero when written signed; an unsigned zero takes the common sign of the row's other non-zero
    cells under period headers, and None when there are none or they differ."""
    if _negative(hit.row[base_column]) or any(n != 0 for c, n in hit.agreeing if c == base_column):
        return _negative(hit.row[base_column])
    signs = {
        _negative(cell)
        for column, cell in enumerate(hit.row)
        if column
        and column != base_column
        and column < len(hit.header)
        and period_of(hit.header[column]) is not None
        and (number := _number(cell)) is not None
        and number != 0
    }
    return signs.pop() if len(signs) == 1 else None


def _row(hit: _Hit, key: str, base_column: int) -> _Row:
    sign = _row_sign(hit, base_column) if key in _BASE_SIGNED else False
    figures: dict[Period, set[Decimal]] = {}
    columns: set[Period] = set()
    balances: dict[str, set[Decimal]] = {}
    for column, name in enumerate(hit.header):
        period = period_of(name) if column else None
        if period is None:
            if column and key in _STOCKS and _LTM_LABEL.fullmatch(_plain(name)):
                number = _number(hit.row[column]) if column < len(hit.row) else None
                if number is not None:
                    balances.setdefault(_plain(name), set()).add(number)
            continue
        columns.add(period)
        number = _number(hit.row[column]) if column < len(hit.row) else None
        if number is not None:
            figures.setdefault(period, set()).add(_published(key, number, bool(sign)))
    return _Row(hit.table, figures, columns, sign is None, balances)


def _rows_under(hits: list[_Hit], key: str, target: Period) -> list[_Row]:
    """The rows that print the base amount under a header of the target period."""
    rows = []
    for hit in hits:
        base = next((c for c, _ in hit.agreeing if period_of(hit.header[c]) == target), None)
        if base is not None:
            rows.append(_row(hit, key, base))
    return rows


def _unread(tables: list[list[list[str]]], rows: list[_Row]) -> tuple[str, ...]:
    found: dict[str, None] = {}
    for index in dict.fromkeys(row.table for row in rows):
        for name in tables[index][0][1:]:
            if period_of(name) is None and _YEAR.search(name):
                found[name] = None
    return tuple(found)


def _line(
    tables: list[list[list[str]]],
    key: str,
    amount: Decimal,
    label: str,
    target: Period,
) -> Line:
    """The operand's history from the rows labelled `label` that print its base amount under a
    header of the target period."""
    rows = _rows_under(_hits(tables, key, amount, label), key, target)
    if not rows:
        return Line(reason=NOT_A_CELL)
    unread = _unread(tables, rows)
    if any(row.signless for row in rows):
        return Line(reason=NO_SIGN, unread=unread)
    figures: dict[Period, set[Decimal]] = {}
    for row in rows:
        for period, found in row.figures.items():
            figures.setdefault(period, set()).update(found)
    values: dict[Period, Decimal] = {}
    gaps: dict[Period, str] = {}
    for period in set().union(*(row.columns for row in rows)):
        found = figures.get(period, set())
        if len(found) == 1:
            (values[period],) = found
        else:
            template = DIFFERENT if found else NOT_PRINTED
            gaps[period] = template.format(period=period_label(period))
    balances: dict[str, set[Decimal]] = {}
    for row in rows:
        for name, found in row.balances.items():
            balances.setdefault(name, set()).update(found)
    return Line(values=values, gaps=gaps, balances=balances, unread=unread)


def lines(
    tables: list[list[list[str]]],
    operands: cp2g.Operands,
    *,
    named: Mapping[str, tuple[str, str]] | None = None,
) -> dict[str, Line]:
    """One `Line` per operand key: the figure, in each period its table headers name, of the rows
    that print the operand's base amount under the period the forecast inputs name for it, read
    from the rows of the label they name (`named`: `{key: (row label, period header)}`; None is
    none named). An operand with an amount and no name has no history. Never raises on a table
    shape. A `ByColumn` name is read as a period row's cell under a measure column."""
    return _locate(tables, operands, named or {}, 1)[0]


def _locate(
    tables: list[list[list[str]]],
    operands: cp2g.Operands,
    named: Mapping[str, tuple[str, str]],
    scale: int,
) -> tuple[dict[str, Line], Period | None]:
    """The lines and the base period (the latest period named for revenue or EBITDA). At a scale
    other than 1 each cell is compared with the operand times the scale, and the figures found are
    divided by it, so the lines are in the operands' unit; at scale 1 no cell is touched."""
    found: dict[str, Line] = {}
    with localcontext(cp2g._EXACT):
        for key, operand in operands.items():
            if operand.amount is None:
                found[key] = Line(reason=_cut(operand.reason or NO_REASON, _MAX_REASON))
            elif scale == 1:
                found[key] = _named_line(tables, key, operand.amount, named.get(key))
            else:
                line = _named_line(tables, key, operand.amount * scale, named.get(key))
                found[key] = replace(
                    line,
                    values={p: v / scale for p, v in line.values.items()},
                    balances={n: {v / scale for v in vs} for n, vs in line.balances.items()},
                )
    return found, _named_base(named)


def _named_base(named: Mapping[str, tuple[str, str]]) -> Period | None:
    """The latest period that the forecast inputs name for revenue or EBITDA (by its header, or
    by its row label when the operand is named by column)."""
    periods = [
        p
        for key in ("revenue", "ebitda")
        if key in named
        and (p := period_of(named[key][0 if isinstance(named[key], ByColumn) else 1]))
    ]
    return max(periods, key=lambda p: (p[1], p[2]), default=None)


def _transposed(tables: list[list[list[str]]], column: str) -> list[list[list[str]]]:
    """The tables that hold `column` as a header (not the first), each as a two-row measure table:
    the header is the first header cell then the row labels, the one row is `column` then its cells,
    so a table with one row per period reads as a table with the periods as headers."""
    found = []
    for table in tables:
        header, rows = (table[0], table[1:]) if table else ([], [])
        for index in (i for i, name in enumerate(header) if i > 0 and _plain(name) == column):
            kept = [row for row in rows if row and len(row) > index]
            found.append(
                [
                    [header[0], *(row[0] for row in kept)],
                    [header[index], *(row[index] for row in kept)],
                ]
            )
    return found


def _named_line(
    tables: list[list[list[str]]],
    key: str,
    amount: Decimal,
    name: tuple[str, str] | None,
) -> Line:
    """An operand's line: the rows labelled as it names, under the period it names. By column, the
    name is (period row label, measure header): the tables are read transposed and the period is
    the row's."""
    if name is None or not _plain(name[0]) or not _plain(name[1]):
        return Line(reason=NOT_NAMED)
    if isinstance(name, ByColumn):
        target = period_of(name[0])
        if target is None:
            return Line(reason=NOT_UNDER_A_PERIOD.format(header=_cut(_plain(name[0]))))
        line = _line(_transposed(tables, _plain(name[1])), key, amount, _plain(name[1]), target)
        return replace(line, unread=(), unread_rows=line.unread)  # its headers are row labels
    target = period_of(name[1])
    if target is None:
        return Line(reason=NOT_UNDER_A_PERIOD.format(header=_cut(_plain(name[1]))))
    return _line(tables, key, amount, _plain(name[0]), target)


# --- the historical columns ---------------------------------------------------------------------
PRIOR_NOT_DATED = "The prior last twelve months were not checked against period dates."
NOT_DATED = (
    "Historical columns are built from the periods CP-1 labels; CP-1 dates no period table for "
    "them, so the last twelve months are not checked for a short or changed fiscal year."
)
NO_YTD = "the latest reported period is fiscal year {label}; there is no year to date"
NEEDS = "needs {labels}, which CP-1 does not print"
NO_PF = "no handoff states pro forma adjustments"
NOT_EXACT = "the figures cannot be added exactly"
PART_YEAR = "a ratio to part-year earnings is not shown"
NO_COLUMN = "CP-1 prints no {group} column Python can read"
NO_ANCHOR = "no base line was found under a period header of CP-1"
DATED = "The last twelve months were checked against CP-1's period dates ({days} days)."
NOT_CONTINUOUS = (
    "{fy}, {ytd} and {pytd} are not a continuous twelve months by CP-1's period dates ({detail})"
)
NOT_BUILT = (
    "The last twelve months could not be built from the periods CP-1 prints, so there was "
    "nothing to check against its period dates."
)
NOT_TWELVE = "{fy} is not twelve months by CP-1's period dates ({days} days)"
OWN_LTM = (
    "CP-1's own {label} figures for revenue, earnings and cash flow are not read; the LTM column "
    "is built from {fy} + {ytd} - {pytd}."
)
IN_FORECAST = "CP-1 column {label} is in the forecast years and is not read as history."
SHOWN = "Only the latest {n} {kind} columns are shown."
_KIND_WORDS = {"QUARTER": "quarter", "FY": "fiscal-year"}
_MAX_QUARTERS, _MAX_YEARS = 12, 8
_MAX_UNREAD = 10
_TWELVE_MONTHS = range(364, 372)  # a 52- or 53-week year passes

_READ = ("revenue", "ebitda", "interest", "taxes", "wc", "capex", "debt", "cash", "undrawn")
_FLOWS = frozenset({"revenue", "ebitda", "interest", "taxes", "wc", "capex"})
_PUBLISHED = (
    "revenue",
    "ebitda",
    "interest",
    "capex",
    "closing_debt",
    "closing_cash",
    "undrawn",
    "tax_wc",
    "cfo",
    "fcf",
    "liquidity",
    "net_debt",
    "total_leverage",
    "net_leverage",
    "coverage",
    "fcf_to_debt",
)
_READ_PUBLISHED = frozenset(_PUBLISHED[:7])
_OPERAND_OF = {"closing_debt": "debt", "closing_cash": "cash"}
_FLOW_PUBLISHED = ("revenue", "ebitda", "interest", "tax_wc", "capex")
_DERIVED_FROM_FLOWS = ("cfo", "fcf", "total_leverage", "net_leverage", "coverage", "fcf_to_debt")
_PART_YEAR_KEYS = ("total_leverage", "net_leverage", "fcf_to_debt")

Reads = dict[str, cp2g.Val]
Column = dict[str, object]


@dataclass(frozen=True)
class _Anchor:
    year: int
    quarters: int
    fiscal: bool


@dataclass(frozen=True)
class _Context:
    found: dict[str, Line]
    located: list[Line]
    anchor: _Anchor | None
    printed: frozenset[Period]
    dates: Dates
    no_anchor: str = NO_ANCHOR
    labels: LtmDates = field(default_factory=dict)


def _anchor_of(found: dict[str, Line]) -> _Anchor | None:
    """The latest period, by (fiscal year, quarters to date), for which the revenue line or the
    EBITDA line has a value or a gap. A fourth quarter or a fiscal year is a fiscal-year anchor."""
    keys = [
        (y, q, kind == "FY" or q == 4)
        for line in (found["revenue"], found["ebitda"])
        if line.reason is None
        for kind, y, q in (*line.values, *line.gaps)
    ]
    best = max(keys, default=None)
    return _Anchor(*best) if best else None


def _ytd_period(year: int, quarters: int) -> Period:
    return ("QUARTER", year, 1) if quarters == 1 else ("YTD", year, quarters)


def _publish(value: cp2g.Val) -> dict[str, str | None]:
    amount = None if value.amount is None else format(value.amount, "f")
    return {"amount": amount, "reason": value.reason}


def _column(
    column_id: str,
    kind: str,
    label: str,
    prior: str | None,
    values: dict[str, cp2g.Val],
) -> Column:
    return {
        "id": column_id,
        "kind": kind,
        "label": label,
        "prior": prior,
        "reason": None,
        "start": None,
        "end": None,
        "values": {key: _publish(values[key]) for key in _PUBLISHED},
    }


def _dated(column: Column, span: Span | None) -> Column:
    """The column with the first and last day of its period, ISO text."""
    if span is None:
        return column
    return {**column, "start": span[0].isoformat(), "end": span[1].isoformat()}


def _why(column: Column, reason: str | None) -> Column:
    """The column with the reason it has no value as a whole."""
    return {**column, "reason": reason}


def _blanket(text: str) -> dict[str, cp2g.Val]:
    return {key: cp2g.Val(None, text) for key in _PUBLISHED}


def _no_anchor_values(found: dict[str, Line], reason: str = NO_ANCHOR) -> dict[str, cp2g.Val]:
    """Every value missing with `reason` (no anchor); a read value takes its own line's first."""
    values = _blanket(reason)
    for key in _PUBLISHED:
        own = found[_OPERAND_OF.get(key, key)].reason if key in _READ_PUBLISHED else None
        if own is not None:
            values[key] = cp2g.Val(None, own)
    return values


def _read(line: Line, period: Period) -> cp2g.Val:
    """The line's value in the period, else why it has none."""
    if period in line.values:
        return cp2g._known(line.values[period])
    if period in line.gaps:
        return cp2g.Val(None, line.gaps[period])
    return cp2g.Val(None, line.reason or NOT_PRINTED.format(period=period_label(period)))


def _lacking(line: Line, periods: tuple[Period, ...]) -> cp2g.Val | None:
    """The line's reason, or NEEDS naming each of the periods it has no value for; None when it
    has them all."""
    if line.reason is not None:
        return cp2g.Val(None, line.reason)
    missing = [p for p in periods if p not in line.values]
    for period in missing:
        if period in line.gaps:
            return cp2g.Val(None, line.gaps[period])
    labels = dict.fromkeys(period_label(p) for p in missing)
    return cp2g.Val(None, NEEDS.format(labels=", ".join(labels))) if labels else None


def _needs(line: Line, period: Period) -> cp2g.Val:
    return _lacking(line, (period,)) or cp2g._known(line.values[period])


def _combine(fn: Callable[..., Decimal], *args: cp2g.Val) -> cp2g.Val:
    """`fn` over the amounts, the first missing one winning. The one place sums are formed: a
    result that cannot be held exactly (`decimal.Inexact`, the documented case) is missing with
    NOT_EXACT; nothing else is caught."""
    try:
        return cp2g._apply(fn, *args)
    except Inexact:
        return cp2g.Val(None, NOT_EXACT)


def _flow(line: Line, fiscal: Period, add: Period, sub: Period) -> cp2g.Val:
    """`fiscal + add - sub`, or why one of the three is missing."""
    lacking = _lacking(line, (fiscal, add, sub))
    if lacking is not None:
        return lacking
    one, two, three = (cp2g.Val(line.values[p]) for p in (fiscal, add, sub))
    return _combine(lambda a, b, c: a + b - c, one, two, three)


def _derived(reads: Reads, part_year: bool) -> dict[str, cp2g.Val]:
    """The sixteen published values from the nine read ones."""
    val = {key: reads[_OPERAND_OF.get(key, key)] for key in _PUBLISHED[:7]}
    tax_wc = _combine(lambda a, b: a + b, reads["taxes"], reads["wc"])
    cfo = _combine(lambda e, i, t: e - i - t, val["ebitda"], val["interest"], tax_wc)
    fcf = _combine(lambda c, x: c - x, cfo, val["capex"])
    net_debt = _combine(lambda d, c: d - c, val["closing_debt"], val["closing_cash"])
    val["tax_wc"], val["cfo"], val["fcf"], val["net_debt"] = tax_wc, cfo, fcf, net_debt
    val["liquidity"] = _combine(lambda c, u: c + u, val["closing_cash"], val["undrawn"])
    val["total_leverage"] = cp2g._ratio(val["closing_debt"], val["ebitda"], cp2g.NC_EBITDA)
    val["net_leverage"] = cp2g._ratio(net_debt, val["ebitda"], cp2g.NC_EBITDA)
    val["coverage"] = cp2g._ratio(val["ebitda"], val["interest"], cp2g.NC_INTEREST)
    val["fcf_to_debt"] = cp2g._ratio(fcf, val["closing_debt"], cp2g.NC_DEBT)
    if part_year:
        for key in _PART_YEAR_KEYS:
            val[key] = cp2g.Val(None, PART_YEAR)
    return val


def _ids(periods: list[Period]) -> dict[Period, str]:
    return {period: period_label(period) for period in periods}


def _full_year(values: dict[str, cp2g.Val], dates: Dates, period: Period) -> dict[str, cp2g.Val]:
    """A fiscal year CP-1 dates outside twelve months carries no ratio to its part-year flows."""
    span = dates.get(period)
    if span is None or _days(span) in _TWELVE_MONTHS:
        return values
    reason = NOT_TWELVE.format(fy=period_label(period), days=_days(span))
    return {**values, **{key: cp2g.Val(None, reason) for key in _PART_YEAR_KEYS}}


def _group(ctx: _Context, kind: str, group: str, cap: int) -> tuple[list[Column], str | None]:
    """One column for each period of the kind that a located line has a value or a gap for, no
    later than the anchor; at most the latest `cap` (then the limit that says so)."""
    limit = None if ctx.anchor is None else (ctx.anchor.year, ctx.anchor.quarters)
    every = sorted(
        {
            p
            for line in ctx.located
            for p in (*line.values, *line.gaps)
            if p[0] == kind and (limit is None or (p[1], p[2]) <= limit)
        },
        key=lambda p: (p[1], p[2]),
    )
    periods = every[-cap:]
    cut = SHOWN.format(n=cap, kind=_KIND_WORDS[kind]) if len(every) > cap else None
    if not periods:
        return [_placeholder(ctx, kind, group)], cut
    ids = _ids(periods)
    columns = []
    for period in periods:
        prior = (kind, period[1] - 1, period[2])
        if ctx.anchor is None:
            values = _no_anchor_values(ctx.found, ctx.no_anchor)
        else:
            reads = {key: _read(ctx.found[key], period) for key in _READ}
            values = _derived(reads, part_year=kind == "QUARTER")
            values = _full_year(values, ctx.dates, period) if kind == "FY" else values
        reason = ctx.no_anchor if ctx.anchor is None else None
        column = _column(ids[period], kind, ids[period], ids.get(prior), values)
        columns.append(_why(_dated(column, ctx.dates.get(period)), reason))
    return columns, cut


def _placeholder(ctx: _Context, kind: str, group: str) -> Column:
    if ctx.anchor is None:
        reason, values = ctx.no_anchor, _no_anchor_values(ctx.found, ctx.no_anchor)
    else:
        reason = NO_COLUMN.format(group=group.lower())
        values = _blanket(reason)
    return _why(_column(group, kind, group, None, values), reason)


def _label_problem(ctx: _Context, label: str, period: Period) -> str | None:
    """Why the `LTM Qn YYYY` label is not the balance date of the column (its End is the End of
    the dates of `period`, the year to date or the fiscal year), or None."""
    spans = ctx.labels.get(label)
    if not spans:
        return LABEL_NOT_DATED.format(label=label)
    if len(spans) > 1:
        return DATED_TWICE.format(label=label)
    span = ctx.dates.get(period)
    if span is None:
        return LABEL_NOT_DATED.format(label=period_label(period))
    ((_, end),) = spans
    if end != span[1]:
        return LABEL_OTHER_DAY.format(
            label=label,
            end=end.isoformat(),
            anchor=span[1].isoformat(),
            what="fiscal year" if period[0] == "FY" else "year to date",
        )
    return None


def _balance(ctx: _Context, line: Line, real: cp2g.Val, period: Period) -> cp2g.Val:
    """A stock's balance at the column's date: the figure of the column's own period when CP-1
    prints one, else the one printed under the `LTM Qn YYYY` label, read only when CP-1 dates that
    label to the day the column's period ends. Two figures that differ give no balance."""
    label = f"LTM Q{period[2]} {period[1]}"
    printed = line.balances.get(label)
    if line.reason is not None or not printed:
        return real
    different = cp2g.Val(None, DIFFERENT.format(period=period_label(period)))
    if real == different:
        return real
    problem = _label_problem(ctx, label, period)
    if problem is not None:
        return real if real.amount is not None else cp2g.Val(None, problem)
    if len(printed) > 1:
        return different
    (figure,) = printed
    if real.amount is None:
        return cp2g._known(figure)
    return real if real.amount == figure else different


def _balances(ctx: _Context, reads: Reads, period: Period) -> Reads:
    """The reads with each stock replaced by its `_balance`."""
    return {
        key: _balance(ctx, ctx.found[key], value, period) if key in _STOCKS else value
        for key, value in reads.items()
    }


def _ytd_reads(ctx: _Context, period: Period) -> Reads:
    """A year-to-date column's values: its period's cells, or NEEDS when no located line prints
    the period (a quarter is never summed into it)."""
    if period in ctx.printed:
        return {key: _read(ctx.found[key], period) for key in _READ}
    return {key: _needs(ctx.found[key], period) for key in _READ}


@dataclass(frozen=True)
class _Checked:
    """A date check that ran: `reason` set when it failed, else the twelve months' span, days."""

    reason: str | None
    span: Span | None = None
    days: int | None = None


def _days(span: Span) -> int:
    return (span[1] - span[0]).days + 1


def _break(dates: Dates, fiscal: Period, added: Period, taken: Period) -> str | None:
    """What stops the fiscal year plus `added` less `taken` being one continuous twelve months."""
    (first, last), (start, _), (taken_start, _) = dates[fiscal], dates[added], dates[taken]
    labels = period_label(fiscal), period_label(added), period_label(taken)
    if (start - last).days != 1:
        return f"{labels[0]} ends {last.isoformat()}; {labels[1]} starts {start.isoformat()}"
    if taken_start != first:
        return (
            f"{labels[2]} starts {taken_start.isoformat()}; {labels[0]} starts {first.isoformat()}"
        )
    days = _days(dates[fiscal]) + _days(dates[added]) - _days(dates[taken])
    return None if days in _TWELVE_MONTHS else f"{days} days"


def _check_interim(dates: Dates, fiscal: Period, added: Period, taken: Period) -> _Checked | None:
    """The fiscal year ends the day before `added` starts, `taken` starts on the fiscal year's
    first day, and the span is twelve months; None when one of the three is undated."""
    if not all(period in dates for period in (fiscal, added, taken)):
        return None
    detail = _break(dates, fiscal, added, taken)
    if detail is not None:
        labels = (period_label(p) for p in (fiscal, added, taken))
        fy, ytd, pytd = labels
        return _Checked(NOT_CONTINUOUS.format(fy=fy, ytd=ytd, pytd=pytd, detail=detail))
    days = _days(dates[fiscal]) + _days(dates[added]) - _days(dates[taken])
    end = dates[added][1]
    return _Checked(None, (end - timedelta(days=days - 1), end), days)


def _check_year(dates: Dates, fiscal: Period) -> _Checked | None:
    """At a fiscal-year anchor: the fiscal year's own days; None when it is undated."""
    if fiscal not in dates:
        return None
    days = _days(dates[fiscal])
    if days in _TWELVE_MONTHS:
        return _Checked(None, dates[fiscal], days)
    return _Checked(NOT_TWELVE.format(fy=period_label(fiscal), days=days))


def _failed(values: dict[str, cp2g.Val], check: _Checked | None) -> dict[str, cp2g.Val]:
    """The values with the flows and what is derived from them missing, when the check failed."""
    if check is None or check.reason is None:
        return values
    return {
        **values,
        **{key: cp2g.Val(None, check.reason) for key in (*_FLOW_PUBLISHED, *_DERIVED_FROM_FLOWS)},
    }


def _built(values: dict[str, cp2g.Val]) -> bool:
    """Whether any flow of the column has a value (the prior LTM can be built)."""
    return any(values[key].amount is not None for key in _FLOW_PUBLISHED)


def _span(check: _Checked | None) -> Span | None:
    return None if check is None else check.span


def _twelve_months(
    label: str,
    ltm: dict[str, cp2g.Val],
    ltm_check: _Checked | None,
    prior: dict[str, cp2g.Val],
    prior_check: _Checked | None,
) -> list[Column]:
    """The LTM and Prior LTM columns, each with its failed check applied and its dates."""
    return [
        _dated(
            _column("LTM", "LTM", label, "PRIOR_LTM", _failed(ltm, ltm_check)), _span(ltm_check)
        ),
        _dated(
            _column("PRIOR_LTM", "PRIOR_LTM", "Prior LTM", None, _failed(prior, prior_check)),
            _span(prior_check),
        ),
    ]


def _interim(
    ctx: _Context, anchor: _Anchor
) -> tuple[list[Column], list[str], tuple[str, str] | None]:
    """YTD, PYTD, LTM and Prior LTM for an anchor inside a fiscal year, the LTM's check, and the
    LTM's label with the line saying it is built (CP-1's own figures under that label are not
    read) when it was built."""
    n, k = anchor.year, anchor.quarters
    ytd_p, pytd_p, older_p = _ytd_period(n, k), _ytd_period(n - 1, k), _ytd_period(n - 2, k)
    ytd, pytd = _ytd_reads(ctx, ytd_p), _ytd_reads(ctx, pytd_p)
    ytd = _balances(ctx, ytd, ytd_p)
    ltm, prior = dict(ytd), dict(pytd)
    for key in _FLOWS:
        line = ctx.found[key]
        ltm[key] = _flow(line, ("FY", n - 1, 4), ytd_p, pytd_p)
        prior[key] = _flow(line, ("FY", n - 2, 4), pytd_p, older_p)
    ltm_values = _derived(ltm, False)
    ltm_built = _built(ltm_values)
    ltm_check = _check_interim(ctx.dates, ("FY", n - 1, 4), ytd_p, pytd_p) if ltm_built else None
    prior_values = _derived(prior, False)
    prior_built = _built(prior_values)
    prior_check = (
        _check_interim(ctx.dates, ("FY", n - 2, 4), pytd_p, older_p) if prior_built else None
    )
    columns = [
        _column("YTD", "YTD", f"YTD ({period_label(ytd_p)})", "PYTD", _derived(ytd, True)),
        _column("PYTD", "PYTD", f"PYTD ({period_label(pytd_p)})", None, _derived(pytd, True)),
    ]
    columns[0] = _dated(columns[0], ctx.dates.get(ytd_p))
    columns[1] = _dated(columns[1], ctx.dates.get(pytd_p))
    label = f"LTM Q{k} {n}"
    own = OWN_LTM.format(
        label=label,
        fy=period_label(("FY", n - 1, 4)),
        ytd=period_label(ytd_p),
        pytd=period_label(pytd_p),
    )
    return (
        [*columns, *_twelve_months(label, ltm_values, ltm_check, prior_values, prior_check)],
        _first_limits(ltm_check, ltm_built, prior_built and prior_check is None),
        (label, own) if ltm_built else None,
    )


def _fiscal(ctx: _Context, anchor: _Anchor) -> tuple[list[Column], list[str], None]:
    """At a fiscal-year anchor: no year to date; LTM is the year, Prior LTM the year before."""
    n = anchor.year
    reason = NO_YTD.format(label=period_label(("FY", n, 4)))
    ltm = {key: _needs(ctx.found[key], ("FY", n, 4)) for key in _READ}
    ltm = _balances(ctx, ltm, ("FY", n, 4))
    prior = {key: _needs(ctx.found[key], ("FY", n - 1, 4)) for key in _READ}
    ltm_values = _derived(ltm, False)
    ltm_built = _built(ltm_values)
    ltm_check = _check_year(ctx.dates, ("FY", n, 4)) if ltm_built else None
    prior_values = _derived(prior, False)
    prior_built = _built(prior_values)
    prior_check = _check_year(ctx.dates, ("FY", n - 1, 4)) if prior_built else None
    return (
        [
            _why(_column("YTD", "YTD", "YTD", "PYTD", _blanket(reason)), reason),
            _why(_column("PYTD", "PYTD", "PYTD", None, _blanket(reason)), reason),
            *_twelve_months(f"LTM FY{n}", ltm_values, ltm_check, prior_values, prior_check),
        ],
        _first_limits(ltm_check, ltm_built, prior_built and prior_check is None),
        None,
    )


def _four(ctx: _Context) -> tuple[list[Column], list[str], tuple[str, str] | None]:
    """YTD, PYTD, LTM and Prior LTM, in that order, the first limit line (what the LTM's date
    check found), and the LTM label and line when it was built from the interim periods."""
    if ctx.anchor is None:
        values = _no_anchor_values(ctx.found, ctx.no_anchor)
        return [
            _why(_column("YTD", "YTD", "YTD", "PYTD", values), ctx.no_anchor),
            _why(_column("PYTD", "PYTD", "PYTD", None, values), ctx.no_anchor),
            _why(_column("LTM", "LTM", "LTM", "PRIOR_LTM", values), ctx.no_anchor),
            _why(_column("PRIOR_LTM", "PRIOR_LTM", "Prior LTM", None, values), ctx.no_anchor),
        ], [NOT_BUILT], None  # fmt: skip
    if ctx.anchor.fiscal:
        return _fiscal(ctx, ctx.anchor)
    return _interim(ctx, ctx.anchor)


def _first_limits(check: _Checked | None, built: bool, prior_unchecked: bool) -> list[str]:
    """What the date check says of the LTM: nothing to check, not run, failed (its reason) or
    passed (its days); then, when a Prior LTM was built and its check did not run, that."""
    if not built:
        first = NOT_BUILT
    elif check is None:
        first = NOT_DATED
    elif check.reason is not None:
        first = check.reason
    else:
        first = DATED.format(days=check.days)
    return [first, PRIOR_NOT_DATED] if prior_unchecked else [first]


def _limits(
    found: dict[str, Line],
    first: list[str],
    twice: tuple[str, ...],
    forecast: tuple[str, ...],
    own: tuple[str, str] | None,
) -> list[str]:
    limits = list(first)
    limits += [
        f"{cp2g._OPERAND_WORDS[key]}: {line.reason}"
        for key, line in found.items()
        if line.reason is not None
    ]
    limits += [IN_FORECAST.format(label=label) for label in forecast]
    limits += [DATED_TWICE.format(label=label) for label in twice]
    lists = {
        what: list(
            dict.fromkeys(
                _cut(_plain(header))
                for line in found.values()
                if line.reason is None
                for header in getattr(line, kind)
            )
        )
        for what, kind in (("column headers", "unread"), ("row labels", "unread_rows"))
    }
    if own is not None and any(own[0] in unread for unread in lists.values()):
        limits.append(own[1])
        lists = {what: [h for h in unread if h != own[0]] for what, unread in lists.items()}
    for what, unread in lists.items():
        if unread:
            names = ", ".join(unread[:_MAX_UNREAD])
            more = f" and {len(unread) - _MAX_UNREAD} more" if len(unread) > _MAX_UNREAD else ""
            limits.append(f"CP-1 {what} not read as periods: {names}{more}.")
    return limits


def _before_forecast(
    found: dict[str, Line], forecast_year: int | None, base: Period | None
) -> tuple[dict[str, Line], tuple[str, ...]]:
    """The lines without the fiscal years from the forecast's first year on that are later than
    the base period (the base period and earlier ones are printed actuals, whatever the label of
    the forecast's first year), and those years' labels (ascending)."""
    if forecast_year is None:
        return found, ()

    def future(period: Period) -> bool:
        later = base is None or (period[1], period[2]) > (base[1], base[2])
        return period[0] == "FY" and period[1] >= forecast_year and later

    dropped: set[Period] = set()
    kept = {}
    for key, line in found.items():
        dropped |= {p for p in (*line.values, *line.gaps) if future(p)}
        kept[key] = replace(
            line,
            values={p: v for p, v in line.values.items() if not future(p)},
            gaps={p: g for p, g in line.gaps.items() if not future(p)},
        )
    return kept, tuple(period_label(p) for p in sorted(dropped))


def history(
    tables: list[list[list[str]]],
    operands: cp2g.Operands,
    *,
    named: Mapping[str, tuple[str, str]] | None = None,
    forecast_year: int | None = None,
    scale: int = 1,
) -> dict[str, object]:
    """The Forecast page's historical columns, read from CP-1's period-labelled tables (`named`:
    the forecast inputs' row and period for each operand, a `ByColumn` where it names a measure
    column; `forecast_year`: the first forecast year, from which no fiscal year is history;
    `scale`: 1000 when CP-1's cells are in thousands and the operands in millions, then every
    figure is published in millions). Never raises: a value that cannot be built is missing with
    its reason."""
    located_lines, base = _locate(tables, operands, named or {}, scale)
    found, forecast = _before_forecast(located_lines, forecast_year, base)
    located = [line for line in found.values() if line.reason is None]
    printed = frozenset(p for line in located for p in (*line.values, *line.gaps))
    dates, twice = period_dates(tables)
    labels = ltm_dates(tables)
    anchor = _anchor_of(found)
    nothing_named = not any(key in (named or {}) for key in ("revenue", "ebitda"))
    unnamed = (
        anchor is None
        and nothing_named
        and NOT_NAMED in (found["revenue"].reason, found["ebitda"].reason)
    )
    ctx = _Context(
        found, located, anchor, printed, dates, NOT_NAMED if unnamed else NO_ANCHOR, labels
    )
    (ytd, pytd, ltm, prior), first, own = _four(ctx)
    pf = _why(_column("PF", "PF", "PF LTM", None, _blanket(NO_PF)), NO_PF)
    quarters, quarter_cut = _group(ctx, "QUARTER", "Quarter", _MAX_QUARTERS)
    years, year_cut = _group(ctx, "FY", "Fiscal year", _MAX_YEARS)
    limits = _limits(found, first, twice, forecast, own)
    limits += [cut for cut in (quarter_cut, year_cut) if cut is not None]
    return {
        "schema_version": "cpos-history/1",
        "columns": [*quarters, ytd, pytd, *years, ltm, prior, pf],
        "limits": limits,
    }
