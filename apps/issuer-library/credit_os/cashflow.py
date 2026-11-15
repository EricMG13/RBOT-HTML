"""The Forecast page's cash flow grid, read from a published model's files (`read_cashflow`).

Part of the library's store (`credit_os.store`, which re-exports every name here).
"""

import datetime
import decimal
import json
import re
from collections.abc import Callable
from typing import Any, NamedTuple, NotRequired, TypedDict

from credit_os.source import (
    MONTHS,
    describe,
    display_date,
    physical_lines,
    text_or_none,
    valid_date,
)

CASHFLOW_FILES = ("forecast_exact.json", "calculation.json", "annual.md", "quarter.md")
# The CP-1 handoff table labels the cash flow reader matches, exactly as the handoffs print them
# (TDG wording). To read another issuer's handoffs, add or change its labels here; nothing else in
# the reader names a handoff label. Matching is exact and case-sensitive except the debt register,
# which is matched case-insensitively (see secured_debt).
CASHFLOW_LABELS = {
    "revenue": "NET SALES",
    "cogs": "COST OF SALES",
    "gross_profit": "GROSS PROFIT",
    "selling_admin": "SELLING AND ADMINISTRATIVE EXPENSES",
    "amortization": "AMORTIZATION OF INTANGIBLE ASSETS",
    "operating_income": "INCOME FROM OPERATIONS",
    "segment_revenue": "Net Sales",
    "total_prefix": "Total",
    "da": "Depreciation and amortization expense",
    "issuer_ebitda": "EBITDA",
    "adjusted_ebitda": "Total Company EBITDA As Defined",
    "interest_net": "Interest expense-net",
    "pretax_income": "Income from continuing operations before income taxes",
    "secured_securitization": "Trade receivable securitization",
    "secured_term_loans": "Term loans aggregate",
    "secured_notes": "secured notes",
    "unsecured_notes": "subordinated",
    "unsecured": "unsecured",
    "label_header": "Label",
    "period_header": "Period",
    "period_end_header": "End",
}
# Inputs beyond these are refused before any cell is built (see CashflowLimit).
QUARTER_COLUMN_LIMIT = 40
FORECAST_YEAR_LIMIT = 20
FISCAL_YEAR_LIMIT = 20
UNIT_ROW_LIMIT = 200
ADD_BACK_ROW_LIMIT = 200
TABLE_ROW_LIMIT = 2000
QUARTER_DAYS = 100
QUARTER_LENGTH_SLACK = 7
FORECAST_CASES = (
    ("REFERENCE", "Base case"),
    ("UPSIDE", "Upside"),
    ("DOWNSIDE_DRIVERS", "Downside (CP-2G drivers)"),
    ("DOWNSIDE", "Downside stress (shock on base drivers)"),
)
# The stress case's name when the model's shock sits on its own downside drivers (the model's
# `downside_basis`); a model delivered before that field existed keeps the base-drivers name.
STRESS_ON_DOWNSIDE_DRIVERS = "Downside stress (shock on downside drivers)"
NO_VALUE = "the model's source table has no value for this period"
PRINTED_DASH = "printed as \u2014 in the source"
PRIOR_MISSING = "prior-year period not in the handoffs"
COMPONENT_MISSING = "a component is not in the handoffs"
REASON_PHRASES = {
    "NOT_SOURCED": "not reported in the source",
    "NOT_STATED": COMPONENT_MISSING,
    "ZERO_OR_NEGATIVE_DENOMINATOR": "a divisor is zero or negative",
    "COMPONENT_MISSING": COMPONENT_MISSING,
    "PRIOR_PERIOD_MISSING": PRIOR_MISSING,
    "REGISTER_DATE_DIFFERS": "secured-debt carrying values are recorded at another date",
    "UNCLASSIFIED_ROW": "the debt register has a row that cannot be classified",
    "WINDOW_MISSING": "last-twelve-months Adj EBITDA cannot be built from the handoffs",
}
LTM_NEEDED = "needs last-twelve-months Adj EBITDA for this quarter, which is not recorded"
DEBT_TOTAL_NEEDED = "needs quarter-end total carrying debt, which the model does not derive"
DEBT_SENIOR_NEEDED = (
    "needs quarter-end senior secured carrying debt, which the model does not derive"
)
MONTHS_SHORT = {name[:3]: number for number, name in enumerate(MONTHS, 1)}
Q1_NOTE = "Q1 is the first quarter of the fiscal year, so it is also the year to date."
CASHFLOW_NOTES = (
    Q1_NOTE,
    "Pro forma: no pro forma period is recorded in the handoffs.",
    (
        "Base case is the model's reference case: a conditional illustration, not an "
        "evidence-supported central issuer forecast."
    ),
    "n.m. \u2014 not modelled: the calculation record does not project this line.",
    (
        "EBITDA (EBIT + D&A) differs from the issuer's reported EBITDA, which also deducts "
        "refinancing costs and includes other income or expense."
    ),
    (
        "Adj EBITDA is the issuer's EBITDA As Defined, a non-GAAP measure; in the forecast it is "
        "the model's earnings on that basis, not issuer guidance."
    ),
    (
        "Leverage uses carrying debt including securitization; senior secured debt is the term "
        "loans, secured notes and securitization at carrying value. Ratios are shown for fiscal "
        "years only."
    ),
)
# On the history path the notes name no issuer's wording: CP-1's labelled periods and the forecast
# inputs block (which names the Financial foundation lines) decide what each line is.
HISTORY_NOTES = (
    CASHFLOW_NOTES[2],
    (
        "Adj EBITDA is the earnings line the forecast inputs name in Financial foundation; in the "
        "forecast it is the model's earnings on that basis, not issuer guidance."
    ),
    (
        "Leverage is closing debt, as the forecast inputs name it in Financial foundation, over "
        "Adj EBITDA. Leverage is shown for twelve-month periods only."
    ),
    (
        "Historical interest is the Financial foundation line the forecast inputs name, which may "
        "be interest expense rather than cash paid."
    ),
    CASHFLOW_NOTES[3],
)
LTM_NOTE = (
    "LTM is the last fiscal year when that is the latest period CP-1 labels; otherwise the last "
    "fiscal year plus the year to date less the prior year to date."
)
HISTORY_LIMIT_COUNT = 200
HISTORY_LIMIT_CHARS = 2000
# The prior a history column of a kind may name, as the period history writes them.
HISTORY_PRIOR_KINDS = {"QUARTER": "QUARTER", "YTD": "PYTD", "FY": "FY", "LTM": "PRIOR_LTM"}
FY_PLACEHOLDER = "Fiscal year"  # the id of the fiscal-year column when CP-1 prints no year
NO_LINE = "the period history does not carry this line"
LENGTH_DIFFERS = "the prior-year period has a different length"
PRIOR_NOT_YEAR = "the prior fiscal year is not twelve months"
YEAR_DAYS = range(364, 372)  # a 52- or 53-week year, both ends counted
HISTORY_SCHEMA = "cpos-history/1"
HISTORY_COLUMN_LIMIT = 60
HISTORY_GROUPS = {
    "QUARTER": "Quarter",
    "YTD": "Year to date",
    "PYTD": "Year to date",
    "FY": "Fiscal year",
    "LTM": "Last twelve months",
    "PRIOR_LTM": "Last twelve months",
    "PF": "Pro forma",
}
HISTORY_KEYS = frozenset(("id", "kind", "label", "prior", "reason", "start", "end", "values"))
QUARTER_HEADER = re.compile(r"(\d{4}-\d{2}-\d{2})[–-](\d{4}-\d{2}-\d{2})", re.ASCII)
FISCAL_HEADER = re.compile(r"FY\d{4}", re.ASCII)
TABLE_NUMBER = re.compile(r"(\()?((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(\))?", re.ASCII)
SEPARATOR_CELL = re.compile(r":?-+:?")
CARRYING = re.compile(r"carrying\s+(\d[\d,]*(?:\.\d+)?)", re.ASCII)
REGISTER_DATE = re.compile(r"\b([A-Z][a-z]{2}) (\d{1,2}), (\d{4})\b", re.ASCII)


class Cell(TypedDict):
    """One grid cell. `status` is value, na (not available, with a reason) or nm (not modelled)."""

    exact: str | None
    display: str
    reason: str | None
    status: str


PeriodKey = tuple[str, ...]
Span = tuple[str, ...]  # (start, end) ISO dates of a quarter column
SecuredDebt = tuple[datetime.date, decimal.Decimal | None, str | None]
Spec = tuple[Any, ...]  # (operation name, *its arguments); see CELL_OPS
RowKey = str | tuple[str, str]
Forecast = list[tuple[str, list[dict[str, Any]]]]  # (case name, that case's years)
Fiscal = list[tuple[str, dict[str, Any]]]  # (fiscal year label, its values)
History = tuple[list[dict[str, Any]], list[str]]  # (validated history columns, their limits)
Recorded = tuple[Fiscal, dict[str, dict[str, Any]], History | None]


class Table(TypedDict):
    """A Markdown table: its header, rows by first-found label, and column index by period."""

    header: list[str]
    rows: dict[str, list[str]]
    periods: dict[PeriodKey, int]
    repeated: str | None
    interrupted: str | None


class Column(TypedDict):
    """A grid column; `prior` is the index of its prior-year column."""

    label: str
    group: str
    kind: str
    record: dict[str, Any] | None
    start: str | None
    end: str | None
    period: PeriodKey | None
    prior: int | None
    ytd: bool
    length_differs: NotRequired[bool]
    prior_not_year: NotRequired[bool]
    unavailable: NotRequired[str]


def display_amount(exact: str, kind: str) -> str:
    """An exact decimal string as the reader sees it: half-up, money in brackets when negative."""
    with decimal.localcontext(decimal.Context(prec=200)) as context:
        value = decimal.Decimal(exact)
        if not value.is_finite():
            raise ValueError(f"not a finite decimal: {exact!r}")
        if kind in ("percent", "multiple"):
            scaled = value * 100 if kind == "percent" else value
            two = scaled.quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP, context)
            if two == 0:
                two = abs(two)  # a negative that rounds to zero is not shown as -0.00
            return f"{two:,.2f}{'%' if kind == 'percent' else 'x'}"
        rounded = value.quantize(decimal.Decimal(1), decimal.ROUND_HALF_UP, context)
        if rounded == 0:
            return "0"  # a negative that rounds to zero is not shown as -0 or in brackets
        return f"({-rounded:,})" if rounded < 0 else f"{rounded:,}"


def cashflow_units(handoff: str) -> str | None:
    """The first '<ISO currency> millions|billions|thousands' phrase of the Request section."""
    request = re.search(
        r"^## Request[ \t]*\r?\n(.*?)(?=^## |\Z)", handoff, re.MULTILINE | re.DOTALL
    )
    phrase = (
        re.search(r"\b[A-Z]{3}\s+(?:millions|billions|thousands)\b", request.group(1))
        if request
        else None
    )
    return re.sub(r"\s+", " ", phrase.group(0)) if phrase else None


UNITS_LIMIT = 40


def recorded_units(exact: Any) -> str | None:
    """The `units` the forecast record states for its published figures, or None when it states
    none. `scale` and `units` are recorded together. `units` is a printable text of 1 to
    UNITS_LIMIT characters with something visible in it (no control, bidi-control or newline
    character); anything else is not shown: TypeError."""
    if not isinstance(exact, dict):
        return None
    units = exact.get("units")
    if (units is None) != (exact.get("scale") is None):
        raise TypeError("scale and units are not recorded together")
    if units is None:
        return None
    if not isinstance(units, str) or not 1 <= len(units) <= UNITS_LIMIT:
        raise TypeError("units is not a short text")
    if not units.isprintable() or not units.strip():
        raise TypeError("units is not printable text")
    return units


def units_caption(units: str | None, handoff: str | None) -> str | None:
    """The record's own statement of its units; without one, the Request section's phrase."""
    if units is not None:
        return units
    return cashflow_units(handoff) if handoff is not None else None


class CashflowBudget(Exception):
    """A grid larger than the cells left in the workspace's budget; raised before any cell."""


class CashflowLimit(Exception):
    """A cash flow input larger than the reader accepts; names the file and what was too large."""

    def __init__(self, file: str, what: str, found: int, limit: int) -> None:
        super().__init__(f"{file} exceeds the cash flow model's limits ({what}, {found} > {limit})")


def grid_cell(
    exact: str | None, display: str, reason: str | None = None, status: str = "value"
) -> Cell:
    return {"exact": exact, "display": display, "reason": reason, "status": status}


def amount_cell(exact: str, kind: str) -> Cell:
    return grid_cell(exact, display_amount(exact, kind))


def absent_cell() -> Cell:
    return unavailable_cell(NO_VALUE)


def unavailable_cell(reason: str | None) -> Cell:
    return grid_cell(None, "n.a.", reason, "na")


def not_modelled_cell() -> Cell:
    return grid_cell(None, "n.m.", "not modelled in the calculation record", "nm")


def held_cell(held: dict[str, Any], kind: str, negate: bool = False) -> Cell:
    """A calculation record's {amount, reason}; an amount of null is n.a. with its reason."""
    exact = held["amount"]
    if exact is None:
        reason, note = held.get("reason"), held.get("note")
        words = REASON_PHRASES.get(reason, reason) if isinstance(reason, str) else None
        if reason == "WINDOW_MISSING" and isinstance(note, str) and note:
            words = f"{words}: {note[:LABEL_LIMIT]}"  # the cause the delivery recorded
        return unavailable_cell(words)
    if negate:
        value = decimal.Decimal(exact).copy_negate()
        exact = "0" if value == 0 else str(value)
    return amount_cell(exact, kind)


def checked_entries(record: dict[str, Any], skip: tuple[str, ...] = ()) -> None:
    """Every entry of a calculation record but `skip` is {amount: text|null, reason: text|null}."""
    for key, held in record.items():
        if key in skip:
            continue
        if not isinstance(held, dict) or not {"amount", "reason"} <= held.keys():
            raise TypeError(f"{key} is not an amount and a reason")
        exact, reason = held["amount"], held["reason"]
        if not (reason is None or isinstance(reason, str)):
            raise TypeError(f"the reason of {key} is not text")
        if exact is None:
            continue
        if not isinstance(exact, str) or len(exact) > 200:
            raise ValueError("an amount is not a decimal string")
        display_amount(exact, "money")  # a non-finite or out-of-range amount raises here
        display_amount(exact, "percent")


def source_cell(text: str, kind: str) -> Cell:
    """A Markdown table cell as the handoff printed it."""
    if text == "":
        return absent_cell()
    if text == "\u2014":
        return unavailable_cell(PRINTED_DASH)
    found = TABLE_NUMBER.fullmatch(text) if len(text) <= 40 else None
    if found is None or bool(found.group(1)) != bool(found.group(3)):
        return unavailable_cell("source cell is not a number")
    digits = found.group(2).replace(",", "")
    negative = found.group(1) and decimal.Decimal(digits) != 0
    return amount_cell(f"-{digits}" if negative else digits, kind)


def table_cells(line: str) -> list[str]:
    """The cells of a table row; an escaped pipe (backslash, pipe) is text inside a cell."""
    inner = line.strip().removeprefix("|").removesuffix("|")
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", inner)]


MARKS = re.compile(r"[*_()]")
TOTAL_AT_EDGE = re.compile(r"(?:(?:sub)?totals?\b.*|.*\b(?:sub)?totals?)")
TOTAL_WORD = re.compile(r"\b(?:sub)?totals?\b")
SEPARATOR = re.compile(r"[ \t]*(?=[^-]*-)(?=.*\|)[ \t:|-]+")
TABLE_ROW = re.compile(r" {0,3}(\|.*?)\s*")
CODE_SPAN = re.compile(r"(`+).+?\1")
FENCE_LINE = re.compile(r"[ \t]*(?:`{3,}|~{3,})")
HEADING_START = re.compile(r" {0,3}(#{1,6})(?:[ \t]|$)")


def plain_label(label: str) -> str:
    """A register row label as classified, delivery's `_plain` written again: emphasis marks and
    parentheses removed, whitespace runs one space, trailing `:` and `.` stripped, casefolded."""
    text = " ".join(MARKS.sub("", label).split())
    return text.rstrip(":.").strip().casefold()


def total_kind(low: str) -> str | None:
    """`edge` when the whole word total or subtotal starts or ends the plain label (a subtotal),
    `inner` when it sits elsewhere (a row that cannot be classified), else None."""
    if TOTAL_AT_EDGE.fullmatch(low):
        return "edge"
    return "inner" if TOTAL_WORD.search(low) else None


def table_row(line: str) -> str | None:
    """The row text of a line that starts with '|' after at most three spaces (four is code),
    without trailing whitespace; None for any other line."""
    found = TABLE_ROW.fullmatch(line)
    return None if found is None else found[1]


def inline_comments(line: str) -> tuple[str, bool]:
    """`line` without its complete HTML comments, and whether one is still open at its end.
    Code spans are blanked before looking for `<!--`; `<!-->` and `<!--->` are whole comments."""
    kept = ""
    while True:
        masked = CODE_SPAN.sub(lambda m: "x" * len(m[0]), line)
        opener = masked.find("<!--")
        if opener < 0:
            return kept + line, False
        if masked.startswith(">", opener + 4):
            end = opener + 5
        elif masked.startswith("->", opener + 4):
            end = opener + 6
        elif (closer := masked.find("-->", opener + 4)) >= 0:
            end = closer + 3
        else:
            return kept + line[:opener], True
        kept, line = kept + line[:opener], line[end:]


def shown_lines(lines: list[str]) -> list[str]:
    """The lines as a Markdown viewer shows them (delivery's `_shown` written again): comments
    removed, fenced code blanked, line numbers kept. A comment never closed hides the rest."""
    shown, fenced, opened = [], False, False
    for line in lines:
        if opened:
            end = line.find("-->")
            text, opened = ("", True) if end < 0 else inline_comments(line[end + 3 :])
            shown.append(text)
            continue
        found = HEADING_START.match(line)
        fenced = fenced and not (found and len(found[1]) == 2)
        toggled = FENCE_LINE.match(line) is not None
        fenced ^= toggled
        if fenced or toggled:
            shown.append("")
            continue
        text, opened = inline_comments(line)
        shown.append(text)
    return shown


def period_key(header: str) -> PeriodKey | None:
    quarter = QUARTER_HEADER.fullmatch(header)
    if quarter:
        try:
            for part in quarter.groups():
                datetime.date.fromisoformat(part)
        except ValueError:
            return None
        return ("q",) + quarter.groups()
    return ("fy", header) if FISCAL_HEADER.fullmatch(header) else None


def holds_carrying_value(row: list[str]) -> bool:
    return len(row) > 1 and len(row[1]) <= 4000 and CARRYING.search(row[1]) is not None


def markdown_table(lines: list[str], file: str) -> Table:
    """One run of '|' lines: header, optional separator, rows. Rows are found by their label."""
    header = table_cells(lines[0])
    separated = len(lines) > 1 and all(SEPARATOR_CELL.fullmatch(c) for c in table_cells(lines[1]))
    if len(lines) - 1 - separated > TABLE_ROW_LIMIT:
        raise CashflowLimit(file, "table rows", len(lines) - 1 - separated, TABLE_ROW_LIMIT)
    body = [table_cells(line) for line in lines[1 + separated :]]
    label_header = CASHFLOW_LABELS["label_header"]
    label_column = header.index(label_header) if label_header in header else 0
    rows: dict[str, list[str]] = {}
    repeated: str | None = None
    folded: set[str] = set()
    for row in body:
        if label_column < len(row):
            # Case-insensitive, as the debt classification is.
            # A later row of a label already seen is dropped by `rows`: that matters when it holds a
            # carrying value, not for a blank label or a note row.
            label = row[label_column]
            dropped = plain_label(label) in folded and label != ""
            if dropped and repeated is None and holds_carrying_value(row):
                repeated = label
            folded.add(plain_label(label))
            rows.setdefault(row[label_column], row)
    periods: dict[PeriodKey, int] = {}
    for index, name in enumerate(header):
        key = period_key(name)
        if key is not None:
            periods.setdefault(key, index)
    return {
        "header": header,
        "rows": rows,
        "periods": periods,
        "repeated": repeated,
        "interrupted": None,
    }


def markdown_tables(text: str, file: str) -> list[Table]:
    """The tables of a Markdown text as a viewer shows it; `file` names it in a limit error. A table
    is its header and raw rows; `interrupted` when hiding changed one or '|' text outside code
    follows before the next `#` heading without its own separator row (delivery's rule). Rows after
    a split table are never merged: they read under its header, with no period and its problem."""
    tables: list[Table] = []
    raw = physical_lines(text)
    shown = shown_lines(raw)
    at, head, problem = 0, "", None  # the header and problem of a split table
    while at < len(raw):
        if table_row(shown[at]) is None:
            at += 1
            continue
        end = at + 1
        while end < len(raw) and table_row(raw[end]) is not None:
            end += 1
        rows = [row for row in map(table_row, shown[at:end]) if row is not None]
        follows = problem is not None and not SEPARATOR.fullmatch("".join(shown[at + 1 : at + 2]))
        table = markdown_table([head, *rows] if follows else rows, file)
        stop = next((i for i in range(end, len(raw)) if HEADING_START.match(shown[i])), len(raw))
        more = next((i for i in range(end, stop) if "|" in CODE_SPAN.sub("", shown[i])), stop)
        split = more < stop and not SEPARATOR.fullmatch("".join(shown[more + 1 : more + 2]))
        if any(shown[i] != raw[i] for i in range(at, more + 1 if split else end)):
            table["interrupted"] = "interrupted by a comment"
        elif split:
            table["interrupted"] = "split by a blank line or a comment"
        if follows:
            table["periods"], table["interrupted"] = {}, problem
        head, problem = head if follows else rows[0], table["interrupted"] if split else None
        tables.append(table)
        at = end
    return tables


def table_holding(tables: list[Table], label: str) -> Table | None:
    return next((table for table in tables if label in table["rows"]), None)


def table_cell(
    table: Table | None, label: str, period: PeriodKey | None, kind: str = "money"
) -> Cell:
    row = None if table is None else table["rows"].get(label)
    index = None if table is None or period is None else table["periods"].get(period)
    if row is None or index is None or index >= len(row):
        return absent_cell()
    return source_cell(row[index], kind)


def add_back_labels(table: Table | None) -> list[str]:
    """The rows between 'Interest expense-net' and the pre-tax income row of a bridge."""
    start = CASHFLOW_LABELS["interest_net"]
    if table is None or start not in table["rows"]:
        return []
    labels = list(table["rows"])
    labels = labels[labels.index(start) + 1 :]
    end = CASHFLOW_LABELS["pretax_income"]
    labels = labels[: labels.index(end)] if end in labels else labels
    return [label for label in labels if label]


def register_date(text: str) -> datetime.date | None:
    found = REGISTER_DATE.search(text)
    if found is None or found.group(1) not in MONTHS_SHORT:
        return None
    try:
        return datetime.date(int(found.group(3)), MONTHS_SHORT[found.group(1)], int(found.group(2)))
    except ValueError:
        return None


def secured_debt(tables: list[Table]) -> SecuredDebt | None:
    """(register date, secured carrying total, problem) of the annual debt register, or None.

    Labels match case-insensitively. Secured: the securitization, the term loans aggregate, and
    secured notes. Unsecured: subordinated or unsecured notes. Total rows are subtotals. Any other
    row with a `carrying <n>` value cannot be classified: the total is then None and the problem
    names the label. None when the register date or a secured carrying value is missing.
    """
    names = CASHFLOW_LABELS
    anchor = names["secured_term_loans"].casefold()
    debt = next(
        (t for t in tables if any(plain_label(label) == anchor for label in t["rows"])), None
    )
    if debt is None or len(debt["header"]) < 2:
        return None
    when = register_date(debt["header"][1])
    if when is None:
        return None
    required = {names["secured_securitization"].casefold(), names["secured_term_loans"].casefold()}
    secured_notes = re.compile(r"(?<![a-z])" + re.escape(names["secured_notes"]))
    total, incomplete, unclassified = decimal.Decimal(0), False, None
    named: set[str] = set()
    for label, row in debt["rows"].items():
        low = plain_label(label)
        kind = total_kind(low)
        if kind == "edge":
            continue
        unsecured = names["unsecured_notes"] in low or names["unsecured"] in low
        secured = kind is None and (
            low in required or (secured_notes.search(low) and not unsecured)
        )
        carrying = CARRYING.search(row[1]) if len(row) > 1 and len(row[1]) <= 4000 else None
        if not secured:
            if carrying is not None and not unsecured and unclassified is None:
                unclassified = label[:LABEL_LIMIT]
            continue
        if carrying is None:
            incomplete = True
            continue
        total += decimal.Decimal(carrying.group(1).replace(",", ""))
        named.add(low)
    if debt["interrupted"] is not None:
        return (
            when,
            None,
            f"the debt register ({debt['header'][1][:LABEL_LIMIT]}) is {debt['interrupted']}",
        )
    if debt["repeated"] is not None:
        return (
            when,
            None,
            f"the debt register repeats a row label: {debt['repeated'][:LABEL_LIMIT]}",
        )
    if unclassified is not None:
        return (
            when,
            None,
            f"the debt register has a row that cannot be classified: {unclassified}",
        )
    return (when, total, None) if required <= named and not incomplete else None


def fiscal_year_ends(tables: list[Table]) -> dict[str, str]:
    """FY label -> ISO end date from the annual period register (headed Period ... End)."""
    names = CASHFLOW_LABELS
    period_name, end_name = names["period_header"], names["period_end_header"]
    register = next(
        (t for t in tables if period_name in t["header"] and end_name in t["header"]), None
    )
    if register is None:
        return {}
    period, end = register["header"].index(period_name), register["header"].index(end_name)
    return {
        row[period]: row[end]
        for row in register["rows"].values()
        if len(row) > max(period, end) and FISCAL_HEADER.fullmatch(row[period])
    }


def derive(kind: str, operands: list[Cell], compute: Callable[..., decimal.Decimal]) -> Cell:
    """A value from other cells under prec=28; n.m. or a gap in an operand carries through."""
    if any(operand["status"] == "nm" for operand in operands):
        return not_modelled_cell()
    exacts = [operand["exact"] for operand in operands]
    values = [decimal.Decimal(exact) for exact in exacts if exact is not None]
    if len(values) != len(exacts):
        return unavailable_cell(COMPONENT_MISSING)
    try:
        with decimal.localcontext(decimal.Context(prec=28)):
            result = compute(*values)
    except (decimal.DivisionByZero, decimal.InvalidOperation):
        return unavailable_cell("a divisor is zero")
    try:
        return amount_cell("0" if result == 0 else str(result), kind)
    except (ArithmeticError, ValueError):
        return unavailable_cell("the value cannot be displayed")


def forecast_inputs(exact: Any) -> tuple[Forecast, list[str], list[str]]:
    """(source years by case, scope limits, the cases' keys in step) of the forecast record;
    validated here."""
    cases: Forecast = []
    keys: list[str] = []
    for key, name in FORECAST_CASES:
        if key not in exact["outputs"]:
            continue
        years = exact["outputs"][key]["years"]
        if len(years) > FORECAST_YEAR_LIMIT:
            raise CashflowLimit(
                CASHFLOW_FILES[0], f"forecast years in {key}", len(years), FORECAST_YEAR_LIMIT
            )
        for year in years:
            if not isinstance(year["year"], int):
                raise TypeError("year is not a number")
            checked_entries(year, ("year", "planning_start", "planning_end"))
        if key == "DOWNSIDE" and exact.get("downside_basis") == "downside_drivers":
            name = STRESS_ON_DOWNSIDE_DRIVERS
        cases.append((name, years))
        keys.append(key)
    limits = exact["scope_limits"]
    if not isinstance(limits, list) or not all(isinstance(item, str) for item in limits):
        raise TypeError("scope_limits is not a list of text")
    return cases, limits, keys


DOWNSIDE_CASE = "Downside case"
DOWNSIDE_NOTES = {
    "DOWNSIDE": "Downside case is the stress case: a shock applied to the base-case drivers.",
    "DOWNSIDE_ON_DRIVERS": (
        "Downside case is the stress case: a shock applied to the model's own downside drivers."
    ),
    "DOWNSIDE_DRIVERS": (
        "Downside case is CP-2G's own downside drivers; no CP-2A shock was supplied."
    ),
    None: "Downside case: no downside case was computed in this run.",
}
NO_DOWNSIDE = "no downside case was computed in this run"


def main_cases(cases: Forecast, keys: list[str]) -> tuple[Forecast, Forecast, str]:
    """(main, other, note): the main grid's Base case and one Downside case, the other cases.

    A case with no years is not computed: it is never the Downside and opens no group.
    The Downside case is the CP-2A shock (DOWNSIDE) when computed, else CP-2G's own downside
    drivers; it is shown as "Downside case", its note naming the basis the model states.
    `keys` are the cases' keys in step with `cases`.
    """
    named = {key: case for key, case in zip(keys, cases, strict=True) if case[1]}  # computed only
    chosen = next((key for key in ("DOWNSIDE", "DOWNSIDE_DRIVERS") if key in named), None)
    main: Forecast = [named["REFERENCE"]] if "REFERENCE" in named else []
    if chosen is not None:
        main.append((DOWNSIDE_CASE, named[chosen][1]))
    other = [case for key, case in named.items() if key not in ("REFERENCE", chosen)]
    on_drivers = chosen == "DOWNSIDE" and named[chosen][0] == STRESS_ON_DOWNSIDE_DRIVERS
    return main, other, DOWNSIDE_NOTES["DOWNSIDE_ON_DRIVERS" if on_drivers else chosen]


def cell_count(rows: int, columns: int) -> int:
    """The cells of a grid of `rows` x `columns`: the one count the budget is charged by."""
    return rows * columns


def grid_cells(grid: dict[str, Any]) -> int:
    """The cells a model's Forecast grid holds, main and other cases together."""
    held = cell_count(len(grid["rows"]), len(grid["columns"]))
    if grid["other"] is not None:
        held += cell_count(len(grid["other"]["rows"]), len(grid["other"]["columns"]))
    return held


def fiscal_inputs(record: Any) -> Fiscal:
    """[(fiscal year label, its values)] in the record's annual_periods order; validated here."""
    labels = record["annual_periods"]
    if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
        raise TypeError("annual_periods is not a list of text")
    if len(labels) > FISCAL_YEAR_LIMIT:
        raise CashflowLimit(CASHFLOW_FILES[1], "fiscal years", len(labels), FISCAL_YEAR_LIMIT)
    years: Fiscal = []
    for label in labels:
        values = record["values"][label]
        checked_entries(values)
        years.append((label, values))
    return years


def quarter_inputs(record: Any) -> dict[str, dict[str, Any]]:
    """The record's derived quarter values by window text; absent is empty; validated here."""
    quarters = record.get("quarters", {})
    if not isinstance(quarters, dict):
        raise TypeError("quarters is not a mapping of windows")
    for held in quarters.values():
        if not isinstance(held, dict):
            raise TypeError("a quarter window is not a mapping")
        checked_entries(held)
    return quarters


def optional_text(value: Any, what: str) -> None:
    if not (value is None or (isinstance(value, str) and len(value) <= LABEL_LIMIT)):
        raise TypeError(f"{what} is not short text")


def history_column_input(column: Any) -> None:
    """One history column's own fields are the right types and bounds; validated here."""
    if not isinstance(column, dict) or column.keys() != HISTORY_KEYS:
        raise TypeError("a history column does not have the recorded fields")
    for name in ("id", "label"):
        if not isinstance(column[name], str) or not 0 < len(column[name]) <= LABEL_LIMIT:
            raise TypeError(f"the {name} of a history column is not short text")
    if column["kind"] not in HISTORY_GROUPS:
        raise ValueError("a history column has an unknown kind")
    for name in ("prior", "reason"):
        optional_text(column[name], f"the {name} of a history column")
    if column["reason"] == "":
        raise ValueError("the reason of a history column is empty")
    if column["reason"] is not None and column["reason"].isspace():
        raise ValueError("the reason of a history column is only whitespace")
    for name in ("start", "end"):
        if column[name] is not None and not (
            isinstance(column[name], str) and valid_date(column[name])
        ):
            raise ValueError(f"the {name} of a history column is not a date")
    if not isinstance(column["values"], dict):
        raise TypeError("the values of a history column are not a mapping")
    checked_entries(column["values"])


def history_limits(record: Any) -> list[str]:
    """The history record's scope limits ([] without a record); validated here."""
    if "history" not in record:
        return []
    limits = record["history"].get("limits") if isinstance(record["history"], dict) else None
    if not isinstance(limits, list) or not all(isinstance(item, str) for item in limits):
        raise TypeError("history limits is not a list of text")
    if len(limits) > HISTORY_LIMIT_COUNT or any(len(i) > HISTORY_LIMIT_CHARS for i in limits):
        raise ValueError("history limits are more or longer than the record allows")
    return limits


def history_inputs(record: Any) -> list[dict[str, Any]] | None:
    """The validated history columns of calculation.json, or None when it has no `history`.

    The record is written by another process: its version, column count, ids, kinds, priors, dates
    and values are checked before any is used; a record that fails is malformed as a whole.
    """
    if "history" not in record:
        return None
    history = record["history"]
    if not isinstance(history, dict) or history.get("schema_version") != HISTORY_SCHEMA:
        raise ValueError("the history record has an unknown version")
    columns = history["columns"]
    if not isinstance(columns, list):
        raise TypeError("history columns is not a list")
    capped(columns, "history columns", HISTORY_COLUMN_LIMIT, CASHFLOW_FILES[1])
    for column in columns:
        history_column_input(column)
    ids = [column["id"] for column in columns]
    if len(set(ids)) != len(ids):
        raise ValueError("history column ids repeat")
    check_history_priors(columns)
    return columns


def check_history_priors(columns: list[dict[str, Any]]) -> None:
    """Ids and kinds agree on fiscal years; a prior is a column of the kind the history pairs."""
    kinds = {column["id"]: column["kind"] for column in columns}
    for column in columns:
        name, kind, prior = column["id"], column["kind"], column["prior"]
        is_year_id = re.fullmatch(r"FY\d+", name, re.ASCII) is not None
        placeholder = kind == "FY" and name == FY_PLACEHOLDER and prior is None
        if is_year_id != (kind == "FY") and not placeholder:
            raise ValueError("a history column's id and kind disagree on a fiscal year")
        if kind == "FY" and not placeholder and FISCAL_HEADER.fullmatch(name) is None:
            raise ValueError("a fiscal-year history column's id is not FY and a year")
        if prior is not None and (
            prior == name or prior not in kinds or HISTORY_PRIOR_KINDS.get(kind) != kinds.get(prior)
        ):
            raise ValueError("a history column's prior is not a column of the kind that follows")
        year_prior = kind == "FY" and prior is not None and prior != FY_PLACEHOLDER
        if year_prior and prior != f"FY{int(name[2:]) - 1}":
            raise ValueError("a fiscal year's prior is not the year before it")


def history_columns(history: list[dict[str, Any]]) -> list[Column]:
    """One column per history entry, in the record's order; its prior is that entry's index."""
    index = {column["id"]: at for at, column in enumerate(history)}
    columns: list[Column] = []
    for entry in history:
        column = Column(
            label=entry["label"],
            group=HISTORY_GROUPS[entry["kind"]],
            kind="h",
            record=entry["values"],
            start=entry["start"],
            end=entry["end"],
            period=None,
            prior=None if entry["prior"] is None else index[entry["prior"]],
            ytd=False,
        )
        if entry["reason"] is not None:
            column["unavailable"] = entry["reason"]
        if column["prior"] is not None and lengths_differ(entry, history[column["prior"]]):
            column["length_differs"] = True
        columns.append(column)
    return columns


def lengths_differ(entry: dict[str, Any], prior: dict[str, Any]) -> bool:
    """Both periods are dated and their lengths differ by more than the quarter slack."""
    if None in (entry["start"], entry["end"], prior["start"], prior["end"]):
        return False
    gap = span_days(entry["start"], entry["end"]) - span_days(prior["start"], prior["end"])
    return abs(gap) > QUARTER_LENGTH_SLACK


def span_days(start: str, end: str) -> int:
    return (datetime.date.fromisoformat(end) - datetime.date.fromisoformat(start)).days


def quarter_numbers(quarters: list[Span], ends: dict[str, str] | None) -> list[int | None]:
    """Per quarter, the fiscal year it opens (as Q1) or None.

    A quarter opens fiscal year N+1 when it spans at most QUARTER_DAYS days and starts the day
    after the end the period register records for FY N. Anything else is neither Q1 nor year to
    date.
    """
    openings: dict[datetime.date, int] = {}
    for label, end in (ends or {}).items():
        try:
            day = datetime.date.fromisoformat(end) + datetime.timedelta(days=1)
            openings.setdefault(day, int(label.removeprefix("FY")) + 1)
        except (ValueError, OverflowError):
            continue  # a register row with an unreadable end opens no fiscal year
    numbers: list[int | None] = []
    longest: dict[int, tuple[int, int]] = {}
    for index, (start, end) in enumerate(quarters):
        days = span_days(start, end)
        number = (
            openings.get(datetime.date.fromisoformat(start)) if 0 <= days <= QUARTER_DAYS else None
        )
        numbers.append(number)
        if number is not None and days > longest.get(number, (-1, 0))[0]:
            longest[number] = (days, index)
    # One Q1 per fiscal year: the longest span; the other candidates are plain date ranges.
    return [
        number if number is not None and longest[number][1] == index else None
        for index, number in enumerate(numbers)
    ]


def quarter_columns(quarters: list[Span], ends: dict[str, str] | None) -> list[Column]:
    """One column per quarter; a Q1 (year to date) has the previous year's Q1 as prior."""
    numbers = quarter_numbers(quarters, ends)
    first_quarter: dict[int, int] = {}
    for index, number in enumerate(numbers):
        if number is not None:
            first_quarter.setdefault(number, index)
    columns: list[Column] = []
    for (start, end), number in zip(quarters, numbers, strict=True):
        prior = None if number is None else first_quarter.get(number - 1)
        column = Column(
            label=f"{start}–{end}" if number is None else f"Q1 FY{number} (YTD)",
            group="Quarter",
            kind="q",
            record=None,
            start=start,
            end=end,
            period=("q", start, end),
            prior=prior,
            ytd=number is not None,
        )
        if prior is not None and abs(span_days(start, end) - span_days(*quarters[prior])) > (
            QUARTER_LENGTH_SLACK
        ):
            column["length_differs"] = True
        columns.append(column)
    return columns


def fiscal_columns(columns: list[Column], fiscal: Fiscal) -> dict[str, int]:
    """Append one column per fiscal year; returns each label's column index."""
    fiscal_index: dict[str, int] = {}
    for label, values in fiscal:
        found = FISCAL_HEADER.fullmatch(label)
        columns.append(
            Column(
                label=label,
                group="Fiscal year",
                kind="fy",
                record=values,
                start=None,
                end=None,
                period=("fy", label),
                prior=fiscal_index.get(f"FY{int(label[2:]) - 1}") if found else None,
                ytd=False,
            )
        )
        fiscal_index.setdefault(label, len(columns) - 1)
    return fiscal_index


def twelve_months(column: Column) -> bool:
    """A column CP-1 does not date, or dates as a 52- or 53-week year, is a full year."""
    if column["start"] is None or column["end"] is None:
        return True
    return span_days(column["start"], column["end"]) + 1 in YEAR_DAYS


def first_year_prior(fiscal_index: dict[str, int], year: int, on_base: bool) -> int | None:
    """The fiscal-year column a case's first year grows on, in `fiscal_index`.

    With the period history (`on_base`) that is the column of the first year's own number, the
    forecast's base year, when the history has one; otherwise the year before it.
    """
    prior = fiscal_index.get(f"FY{year}") if on_base else None
    return fiscal_index.get(f"FY{year - 1}") if prior is None else prior


def forecast_columns(
    columns: list[Column], cases: Forecast, fiscal_index: dict[str, int], on_base: bool = False
) -> None:
    """Append one column per forecast year of each case.

    The prior of a year is the same case's year before it; of a case's first year, a fiscal year
    of `fiscal_index` (see first_year_prior); a prior that is not that year is None.
    """
    for name, years in cases:
        case_index: dict[int, int] = {}
        for year in years:
            prior = case_index.get(year["year"] - 1)
            first = prior is None and not case_index
            if first:
                prior = first_year_prior(fiscal_index, year["year"], on_base)
            columns.append(
                Column(
                    label=f"FY{year['year']}E",
                    group=name,
                    kind="fc",
                    record=year,
                    start=text_or_none(year.get("planning_start")),
                    end=text_or_none(year.get("planning_end")),
                    period=None,
                    prior=prior,
                    ytd=False,
                )
            )
            if first and on_base and prior is not None and not twelve_months(columns[prior]):
                columns[-1]["prior_not_year"] = True
            case_index.setdefault(year["year"], len(columns) - 1)


class CashflowInputs(NamedTuple):
    """What every cell of one model's grid reads: tables, the debt register, fiscal-year ends."""

    tables: dict[str, Table | None]
    secured: SecuredDebt | None
    ends: dict[str, str]
    quarters: dict[str, dict[str, Any]]


class CellContext(NamedTuple):
    """The one argument of a cell operation: inputs, the cell's column, position and row kind."""

    inputs: CashflowInputs
    column: Column
    at: int
    grid: dict[RowKey, list[Cell]]
    kind: str


def add_cells(cells: list[Cell], kind: str = "money") -> Cell:
    return derive(kind, cells, lambda a, b: a + b)


def op_table(c: CellContext, name: str, label: str) -> Cell:
    return table_cell(c.inputs.tables[name], label, c.column["period"], c.kind)


def op_table_sum(c: CellContext, name: str, first: str, second: str) -> Cell:
    table = c.inputs.tables[name]
    cells = [table_cell(table, label, c.column["period"], c.kind) for label in (first, second)]
    return add_cells(cells, c.kind)


def op_key(c: CellContext, key: str, negate: bool = False) -> Cell:
    record = c.column["record"]
    if record is None:
        raise ValueError(f"the {c.column['label']} column holds no record to read {key} from")
    return held_cell(record[key], c.kind, negate) if key in record else spec_cell(None, c)


def op_sum(c: CellContext, *rows: RowKey) -> Cell:
    return add_cells([c.grid[row][c.at] for row in rows], c.kind)


def op_growth(c: CellContext, source: RowKey) -> Cell:
    """YoY growth of an earlier row against the same row in the column's prior-year column."""
    current = c.grid[source][c.at]
    if current["status"] == "nm":
        return not_modelled_cell()
    if c.column["prior"] is None:
        return unavailable_cell(PRIOR_MISSING)
    if c.column.get("length_differs"):
        return unavailable_cell(LENGTH_DIFFERS)
    if c.column.get("prior_not_year"):
        return unavailable_cell(PRIOR_NOT_YEAR)
    prior = c.grid[source][c.column["prior"]]
    return derive("percent", [current, prior], lambda a, b: a / b - 1)


def op_margin(c: CellContext, source: RowKey) -> Cell:
    return derive("percent", [c.grid[source][c.at], c.grid["revenue"][c.at]], lambda a, b: a / b)


def op_prefer(c: CellContext, key: str, fallback: Spec) -> Cell:
    """The calculation record's own value for the key when it holds one, else the derivation."""
    record = c.column["record"]
    if record is not None and key in record:
        return held_cell(record[key], c.kind)
    return spec_cell(fallback, c)


def quarter_held(c: CellContext, key: str) -> dict[str, Any] | None:
    """The record's entry for the key in this quarter column's window (either dash), or None."""
    column = c.column
    if column["kind"] != "q" or column["start"] is None or column["end"] is None:
        return None
    for dash in ("\u2013", "-"):
        window = c.inputs.quarters.get(f"{column['start']}{dash}{column['end']}")
        if window is not None and key in window:
            held: dict[str, Any] = window[key]
            return held
    return None


def op_quarter(c: CellContext, key: str, fallback: Spec | None = None) -> Cell:
    """The record's quarter value for this column's window, else the fallback, else n.a."""
    held = quarter_held(c, key)
    if held is not None:
        return held_cell(held, c.kind)
    return spec_cell(fallback, c) if fallback is not None else absent_cell()


def op_needs_ltm(c: CellContext, debt_needed: str = DEBT_TOTAL_NEEDED) -> Cell:
    held = quarter_held(c, "ltm_adj_ebitda")
    return unavailable_cell(LTM_NEEDED if held is None or held["amount"] is None else debt_needed)


def op_senior(c: CellContext) -> Cell:
    """Secured carrying values over Adj EBITDA, for the fiscal year ending on the register date."""
    if c.inputs.secured is None:
        return unavailable_cell(COMPONENT_MISSING)
    when, total, problem = c.inputs.secured
    if c.inputs.ends.get(c.column["label"]) != when.isoformat():
        return unavailable_cell(
            f"secured-debt carrying values are recorded only at {display_date(when.isoformat())}"
        )
    if problem is not None or total is None:
        return unavailable_cell(problem)
    return derive("multiple", [c.grid["adj"][c.at]], lambda a: total / a)


CELL_OPS: dict[str, Callable[..., Cell]] = {
    "table": op_table,
    "table-sum": op_table_sum,
    "key": op_key,
    "sum": op_sum,
    "growth": op_growth,
    "margin": op_margin,
    "ltm": op_needs_ltm,
    "quarter": op_quarter,
    "senior": op_senior,
    "prefer": op_prefer,
}


def spec_cell(spec: Spec | None, cell: CellContext) -> Cell:
    """One cell from its row's spec for the column's kind (None: n.a., or n.m. in forecast).

    A history column with a reason gives every row n.a. with that reason, derived rows included.
    """
    column = cell.column
    if column["kind"] == "h" and "unavailable" in column:
        return unavailable_cell(column["unavailable"])
    if spec is None:
        if column["kind"] == "h":
            return unavailable_cell(NO_LINE)
        return not_modelled_cell() if column["kind"] == "fc" else absent_cell()
    return CELL_OPS[spec[0]](cell, *spec[1:])


def every(spec: Spec) -> tuple[Spec, Spec, Spec]:
    return (spec, spec, spec)


# Rows the grid shows as totals (the ones a reader adds up to): by row key.
TOTAL_ROWS = frozenset(
    (
        "revenue",
        "gp",
        "ebit",
        "ebitda",
        "adj",
        "cfo",
        "fcf",
        "closing-cash",
        "liquidity",
        "closing-debt",
        "net-debt",
    )
)


class RowSpec(NamedTuple):
    """A grid row as data; a None spec shows n.a. (history) or n.m. (forecast)."""

    key: RowKey
    band: str
    label: str
    kind: str
    quarter: Spec | None
    fiscal: Spec | None
    forecast: Spec | None


# Rows as data: (id, band, label, kind, quarter spec, fiscal-year spec, forecast spec).
INCOME = "Profitability"
HEAD_ROWS = (
    RowSpec(
        "revenue",
        "Revenue",
        "Revenue",
        "money",
        ("table", "income", CASHFLOW_LABELS["revenue"]),
        ("key", "revenue"),
        ("key", "revenue"),
    ),
    RowSpec(
        "revenue-growth",
        "Revenue",
        "Revenue YoY growth",
        "percent",
        ("growth", "revenue"),
        ("prefer", "revenue_growth", ("growth", "revenue")),
        ("growth", "revenue"),
    ),
    RowSpec(
        "cogs",
        INCOME,
        "COGS (cost of sales)",
        "money",
        ("table", "income", CASHFLOW_LABELS["cogs"]),
        ("key", "cogs"),
        None,
    ),
    RowSpec(
        "gp",
        INCOME,
        "Gross profit",
        "money",
        ("table", "income", CASHFLOW_LABELS["gross_profit"]),
        ("key", "gross_profit"),
        None,
    ),
    RowSpec(
        "gp-margin",
        INCOME,
        "Gross profit margin",
        "percent",
        ("margin", "gp"),
        ("prefer", "gross_margin", ("margin", "gp")),
        ("margin", "gp"),
    ),
    RowSpec(
        "opex",
        INCOME,
        "Opex (selling and administrative, amortization of intangibles)",
        "money",
        (
            "table-sum",
            "income",
            CASHFLOW_LABELS["selling_admin"],
            CASHFLOW_LABELS["amortization"],
        ),
        ("key", "opex_magnitude"),
        None,
    ),
    RowSpec(
        "ebit",
        INCOME,
        "EBIT (income from operations)",
        "money",
        ("table", "income", CASHFLOW_LABELS["operating_income"]),
        ("key", "ebit_reported"),
        None,
    ),
    RowSpec(
        "da",
        INCOME,
        "D&A (depreciation and amortization)",
        "money",
        ("table", "bridge", CASHFLOW_LABELS["da"]),
        ("key", "cash_flow_DA"),
        None,
    ),
    RowSpec(
        "ebitda",
        INCOME,
        "EBITDA (EBIT + D&A)",
        "money",
        ("sum", "ebit", "da"),
        ("key", "operating_ebitda"),
        None,
    ),
    RowSpec(
        "issuer",
        INCOME,
        "Issuer EBITDA (reported)",
        "money",
        ("table", "bridge", CASHFLOW_LABELS["issuer_ebitda"]),
        ("key", "issuer_ordinary_ebitda"),
        None,
    ),
)
ADJUSTED = "Adjusted EBITDA"
PROXY = "Earnings to cash proxy"
CASH = "Cash and liquidity"
DEBT = "Debt"
CREDIT = "Credit metrics"
TAIL_ROWS = (
    RowSpec(
        "adj",
        ADJUSTED,
        "Adj EBITDA (EBITDA As Defined)",
        "money",
        ("table", "qdef", CASHFLOW_LABELS["adjusted_ebitda"]),
        ("key", "issuer_as_defined"),
        ("key", "ebitda"),
    ),
    RowSpec(
        "adj-margin",
        ADJUSTED,
        "Adj EBITDA margin",
        "percent",
        ("margin", "adj"),
        ("prefer", "adj_ebitda_margin", ("margin", "adj")),
        ("margin", "adj"),
    ),
    RowSpec(
        "adj-growth",
        ADJUSTED,
        "Adj EBITDA YoY growth",
        "percent",
        ("growth", "adj"),
        ("prefer", "adj_ebitda_growth", ("growth", "adj")),
        ("growth", "adj"),
    ),
    RowSpec(
        "ltm-adj",
        ADJUSTED,
        "LTM Adj EBITDA (As Defined)",
        "money",
        ("quarter", "ltm_adj_ebitda"),
        ("key", "issuer_as_defined"),
        None,
    ),
    RowSpec(
        "interest",
        PROXY,
        "Cash interest",
        "money",
        None,
        ("key", "interest_cash"),
        ("key", "interest"),
    ),
    RowSpec("tax", PROXY, "Cash taxes", "money", None, ("key", "tax_cash"), None),
    RowSpec(
        "tax-wc",
        PROXY,
        "Cash taxes and working capital, combined",
        "money",
        None,
        None,
        ("key", "tax_wc"),
    ),
    RowSpec("cfo", PROXY, "Model cash from operations", "money", None, None, ("key", "cfo")),
    RowSpec(
        "capex",
        PROXY,
        "Capital expenditure (outflow)",
        "money",
        None,
        ("key", "capex_signed", True),
        ("key", "capex"),
    ),
    RowSpec(
        "fcf", PROXY, "Cash proxy (not issuer free cash flow)", "money", None, None, ("key", "fcf")
    ),
    RowSpec("dividends", CASH, "Distributions", "money", None, None, ("key", "dividends")),
    RowSpec("repayment", CASH, "Debt repayment", "money", None, None, ("key", "repayment")),
    RowSpec("opening-cash", CASH, "Opening cash", "money", None, None, ("key", "opening_cash")),
    RowSpec(
        "closing-cash",
        CASH,
        "Closing cash",
        "money",
        None,
        ("key", "cash"),
        ("key", "closing_cash"),
    ),
    RowSpec("undrawn", CASH, "Undrawn facility", "money", None, None, ("key", "undrawn")),
    RowSpec("liquidity", CASH, "Accessible liquidity", "money", None, None, ("key", "liquidity")),
    RowSpec("opening-debt", DEBT, "Opening debt", "money", None, None, ("key", "opening_debt")),
    RowSpec(
        "closing-debt",
        DEBT,
        "Closing debt (carrying value)",
        "money",
        None,
        ("key", "carrying_debt"),
        ("key", "closing_debt"),
    ),
    RowSpec(
        "net-debt",
        DEBT,
        "Net debt (all modelled cash deducted)",
        "money",
        None,
        ("key", "net_carrying_debt"),
        ("key", "net_debt"),
    ),
    RowSpec(
        "senior",
        CREDIT,
        "Senior secured leverage (secured debt / Adj EBITDA)",
        "multiple",
        ("quarter", "senior_secured_multiple", ("ltm", DEBT_SENIOR_NEEDED)),
        ("prefer", "senior_secured_multiple", ("senior",)),
        None,
    ),
    RowSpec(
        "total-leverage",
        CREDIT,
        "Total leverage (debt / Adj EBITDA)",
        "multiple",
        ("ltm",),
        ("key", "gross_carrying_multiple"),
        ("key", "total_leverage"),
    ),
    RowSpec(
        "net-leverage",
        CREDIT,
        "Net leverage (net debt / Adj EBITDA)",
        "multiple",
        ("ltm",),
        ("key", "net_carrying_multiple"),
        ("key", "net_leverage"),
    ),
    RowSpec(
        "coverage",
        CREDIT,
        "Interest coverage (Adj EBITDA / cash interest)",
        "multiple",
        None,
        ("key", "issuer_earnings_cash_interest"),
        ("key", "coverage"),
    ),
    RowSpec(
        "cash-to-debt",
        CREDIT,
        "Cash proxy / closing debt",
        "percent",
        None,
        None,
        ("key", "fcf_to_debt"),
    ),
)


# A free-text label copied from a handoff into the grid is cut to this many characters.
LABEL_LIMIT = 200


def capped(found: Any, what: str, limit: int, file: str) -> None:
    if len(found) > limit:
        raise CashflowLimit(file, what, len(found), limit)


def listed_labels(tables: dict[str, Table | None]) -> list[str]:
    """Business units (rows `Total <unit>`) of the annual, then the quarter, segment table."""
    units: dict[str, None] = {}
    prefix = CASHFLOW_LABELS["total_prefix"] + " "
    for name, file in (("aseg", CASHFLOW_FILES[2]), ("qseg", CASHFLOW_FILES[3])):
        table = tables[name]
        for label in () if table is None else table["rows"]:
            if label.startswith(prefix) and label.removeprefix(prefix):
                units.setdefault(label.removeprefix(prefix))
        capped(units, "business-unit rows", UNIT_ROW_LIMIT, file)
    return list(units)


def listed_add_backs(tables: dict[str, Table | None]) -> list[str]:
    """The annual add-back labels in order, then any quarter-only label."""
    labels = dict.fromkeys(add_back_labels(tables["adef"]))
    capped(labels, "add-back rows", ADD_BACK_ROW_LIMIT, CASHFLOW_FILES[2])
    labels.update(dict.fromkeys(add_back_labels(tables["qdef"])))
    capped(labels, "add-back rows", ADD_BACK_ROW_LIMIT, CASHFLOW_FILES[3])
    return list(labels)


# Row labels on the history path, by row key.
HISTORY_LABELS: dict[RowKey, str] = {
    "adj": "Adj EBITDA (as named in Financial foundation)",
    "ltm-adj": "LTM Adj EBITDA",
    "interest": "Interest",
    "closing-debt": "Closing debt",
    "coverage": "Interest coverage (Adj EBITDA / interest)",
}


def cashflow_rows(tables: dict[str, Table | None], with_history: bool = False) -> list[RowSpec]:
    """The grid's rows in presentation order: units, the fixed head, add-backs, the fixed tail."""
    rows: list[RowSpec] = []
    for unit in listed_labels(tables):
        total = f"{CASHFLOW_LABELS['total_prefix']} {unit}"
        rows.append(
            RowSpec(
                ("unit", unit),
                "Revenue",
                unit[:LABEL_LIMIT],
                "money",
                ("table", "qseg", total),
                ("table", "aseg", total),
                None,
            )
        )
        rows.append(
            RowSpec(
                ("growth", unit),
                "Revenue",
                f"{unit[:LABEL_LIMIT]} YoY growth",
                "percent",
                *every(("growth", ("unit", unit))),
            )
        )
    rows.extend(HEAD_ROWS)
    for label in listed_add_backs(tables):
        rows.append(
            RowSpec(
                ("add-back", label),
                "Add-backs to issuer EBITDA",
                label[:LABEL_LIMIT],
                "money",
                ("table", "qdef", label),
                ("table", "adef", label),
                None,
            )
        )
    tail = [
        spec._replace(label=HISTORY_LABELS.get(spec.key, spec.label)) if with_history else spec
        for spec in TAIL_ROWS
    ]
    return rows + tail


def cashflow_notes(year_to_date: bool, with_history: bool) -> list[str]:
    if with_history:  # CP-1's labelled periods replace the Q1 and pro forma notes
        return [LTM_NOTE, *HISTORY_NOTES]
    return [note for note in CASHFLOW_NOTES if year_to_date or note != Q1_NOTE]


def no_downside_column() -> Column:
    """The main grid's last column when no downside case was computed: n.a. in every row."""
    return Column(
        label="Downside",
        group=DOWNSIDE_CASE,
        kind="h",
        record=None,
        start=None,
        end=None,
        period=None,
        prior=None,
        ytd=False,
        unavailable=NO_DOWNSIDE,
    )


def row_part(rows: list[dict[str, Any]], part: slice) -> list[dict[str, Any]]:
    """The rows with only the cells of the columns in `part`."""
    return [{**row, "cells": row["cells"][part]} for row in rows]


def cashflow_of(
    forecast: tuple[Forecast, list[str], list[str]],
    recorded: Recorded,
    statements: tuple[list[Table], list[Table]],
    units: str | None,
    budget: int,
) -> dict[str, Any]:
    """History from the parsed annual and quarter tables and the forecast record, as a grid.

    `units` is the caption of the grid's amounts (see `units_caption`).

    `recorded` ends with the history (CP-1's period columns and their limits) or None; with it
    those columns replace the quarter and fiscal-year columns and read each row's forecast spec.

    Raises CashflowBudget, before computing any cell, when rows x columns passes `budget`.
    """
    cases, limits, keys = forecast
    main, other, downside_note = main_cases(cases, keys)
    fiscal, quarters, history = recorded
    annual, quarter = statements
    names = CASHFLOW_LABELS
    tables: dict[str, Table | None] = {
        "income": table_holding(quarter, names["cogs"]),
        "qseg": table_holding(quarter, names["segment_revenue"]),
        "aseg": table_holding(annual, names["segment_revenue"]),
        "bridge": table_holding(quarter, names["issuer_ebitda"]),
        "qdef": table_holding(quarter, names["adjusted_ebitda"]),
        "adef": table_holding(annual, names["adjusted_ebitda"]),
    }
    ends = fiscal_year_ends(annual)
    inputs = CashflowInputs(tables, secured_debt(annual), ends, quarters)
    income = tables["income"]
    periods = sorted({key[1:] for key in income["periods"] if key[0] == "q"}) if income else []
    capped(periods, "quarter columns", QUARTER_COLUMN_LIMIT, CASHFLOW_FILES[3])
    layout = [
        RowSpec._make(spec) for spec in cashflow_rows(tables, history is not None)
    ]  # a plain 7-tuple row works
    if history is None:
        columns = quarter_columns(periods, ends)
        fiscal_index = fiscal_columns(columns, fiscal)
    else:
        columns = history_columns(history[0])
        fiscal_index = {c["id"]: at for at, c in enumerate(history[0]) if c["kind"] == "FY"}
    on_base = history is not None
    forecast_columns(columns, main, fiscal_index, on_base)
    if not any(c["group"] == DOWNSIDE_CASE for c in columns):
        columns.append(no_downside_column())
    main_count = len(columns)
    forecast_columns(columns, other, fiscal_index, on_base)  # priors read the main grid's history
    if cell_count(len(layout), len(columns)) > budget:
        raise CashflowBudget(
            "the cash flow model is not shown; the workspace's cash flow models exceed "
            f"{CASHFLOW_CELL_BUDGET:,} cells"
        )
    grid: dict[RowKey, list[Cell]] = {}
    rows = []
    for spec in layout:
        pick = {"q": spec.quarter, "fy": spec.fiscal, "fc": spec.forecast, "h": spec.forecast}
        grid[spec.key] = [
            spec_cell(pick[column["kind"]], CellContext(inputs, column, index, grid, spec.kind))
            for index, column in enumerate(columns)
        ]
        rows.append(
            {
                "band": spec.band,
                "label": spec.label,
                "kind": spec.kind,
                "total": spec.key in TOTAL_ROWS,
                # no figure in any column of the main grid or of the other cases
                "empty": all(cell["status"] != "value" for cell in grid[spec.key]),
                "cells": grid[spec.key],
            }
        )
    year_to_date = any(column["ytd"] for column in columns[:main_count])
    shown = [
        {
            "label": c["label"],
            "group": c["group"],
            "start": c["start"],
            "end": c["end"],
            "ytd": c["ytd"],
        }
        for c in columns
    ]
    return {
        "units": units,
        "columns": shown[:main_count],
        "rows": row_part(rows, slice(0, main_count)),
        "other": None
        if main_count == len(columns)
        else {"columns": shown[main_count:], "rows": row_part(rows, slice(main_count, None))},
        "notes": [*cashflow_notes(year_to_date, history is not None), downside_note],
        "limits": limits if history is None else [*limits, *history[1]],
    }


# Across every model of one page load; a model whose grid would pass it is listed without a grid.
CASHFLOW_CELL_BUDGET = 250_000

# Errors a malformed input file or layout can raise; each is reported, never ends the store.
CASHFLOW_ERRORS = (
    OSError,
    ValueError,
    KeyError,
    TypeError,
    AttributeError,
    IndexError,
    ArithmeticError,
    RecursionError,
    MemoryError,
)


def read_cashflow(
    files: dict[str, bytes], handoff: str | None, budget: int | None = None
) -> tuple[dict[str, Any] | None, tuple[str, str] | None]:
    """(grid, None), or (None, (kind, text)).

    Kind "file" (text: the input that cannot be read), "limit" (text: the limit message, or the
    budget message when the grid passes `budget`, which no cell was computed for) or "layout"
    (text: describe(error) of the failure while laying out). `budget` is the cells left to this
    grid; None means the whole CASHFLOW_CELL_BUDGET, read when called.

    Documented fail-open: an input the reader cannot read or lay out leaves the model listed with
    no grid and a Workspace issue naming the file or the cause. A model too large to parse
    (MemoryError) or nested too deep (RecursionError) is reported the same way, not allowed to end
    the store.
    """
    stage = CASHFLOW_FILES[0]
    try:
        exact = json.loads(files[stage].decode("utf-8"))
        forecast = forecast_inputs(exact)
        units = recorded_units(exact)
        stage = CASHFLOW_FILES[1]
        record = json.loads(files[stage].decode("utf-8"))
        fiscal = fiscal_inputs(record)
        quarter_values = quarter_inputs(record)
        columns = history_inputs(record)
        history = None if columns is None else (columns, history_limits(record))
        stage = CASHFLOW_FILES[2]
        annual = markdown_tables(files[stage].decode("utf-8"), stage)
        stage = CASHFLOW_FILES[3]
        quarter = markdown_tables(files[stage].decode("utf-8"), stage)
    except CashflowLimit as error:
        return None, ("limit", str(error))
    except CASHFLOW_ERRORS:
        return None, ("file", stage)
    try:
        left = CASHFLOW_CELL_BUDGET if budget is None else budget
        recorded = (fiscal, quarter_values, history)
        return cashflow_of(
            forecast, recorded, (annual, quarter), units_caption(units, handoff), left
        ), None
    except (CashflowLimit, CashflowBudget) as error:
        return None, ("limit", str(error))
    except CASHFLOW_ERRORS as error:
        return None, ("layout", describe(error))


class GridAsk(NamedTuple):
    """What a model's grid is built from besides its files: its handoff text and its cell budget
    (None: the whole CASHFLOW_CELL_BUDGET)."""

    handoff: str | None
    budget: int | None


def cashflow_or_issues(
    folder: str,
    files: dict[str, Any],
    inputs: dict[str, bytes | None],
    ask: GridAsk,
    issues: list[str],
) -> dict[str, Any] | None:
    """The model's cash flow grid, or None with one issue for each of the four unusable files."""
    present: dict[str, bytes] = {}
    for name in CASHFLOW_FILES:
        data = inputs[name]
        if data is not None:
            present[name] = data
            continue
        what = "does not match its delivery record" if name in files else "is missing or unreadable"
        issues.append(f"{folder}: {name} {what}")
    if len(present) != len(CASHFLOW_FILES):
        return None
    cashflow, problem = read_cashflow(present, ask.handoff, ask.budget)
    if problem is not None:
        kind, text = problem
        issues.append(
            {
                "file": f"{folder}: {text} is missing or unreadable",
                "limit": f"{folder}: {text}",
                "layout": f"{folder}: the cash flow model could not be laid out ({text})",
            }[kind]
        )
    return cashflow
