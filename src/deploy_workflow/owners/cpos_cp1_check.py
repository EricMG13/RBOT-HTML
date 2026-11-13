"""CP-1's figures, checked in code when its handoff is accepted.

Every arithmetic comparison runs only when each figure in it is a stated plain number, and a `Not
supplied:` or `Not calculable:` cell is never read as zero. A tie between two tables is two-sided:
a figure stated on one side and a gap (or nothing) on the other is refused, never skipped. The
tables the check reads, and their fixed rows and names, are defined here once; the launcher text
sent to CP-1 is rendered from these constants. Decimal and Fraction only: no float touches an
amount or ratio.

Tables are read only inside `## Findings` and outside code fences. This module imports nothing
from `cpos_launch` (which imports it), so it keeps its own small table reader."""

import re
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Context, Decimal, Inexact
from fractions import Fraction
from typing import NamedTuple

from deploy_vii.model._cells import beyond_rounding, half_unit
from deploy_workflow.changes import same_period
from deploy_workflow.credit_os_catalogue import period_order
from deploy_workflow.owners.cpos_periods import period_of

_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?", re.ASCII)
_TWO_PLACES = re.compile(r"-?\d[\d,]*\.\d{2}", re.ASCII)
_UNIT = re.compile(r"[A-Z]{3} (millions|thousands)", re.ASCII)
_PERIOD_HEADER = re.compile(r"FY\d{4}|Q[1-4] \d{4}|H1 \d{4}|9M \d{4}", re.ASCII)
_FISCAL = re.compile(r"FY(\d{4})(?: / \d{4}-\d{2}-\d{2})?", re.ASCII)
_SEPARATOR = re.compile(r"\s*:?-+:?\s*")
_EXACT = Context(prec=1000, traps=[Inexact])  # exact sums of figures of at most MAX_CELL digits
GAP_WORDS = ("Not supplied:", "Not calculable:")
MAX_CELL = 25  # A longer cell is not a plain number; this also bounds every sum.
PERIOD_FORMS = ("FY2024", "Q3 2025", "H1 2025", "9M 2025")
UNIT_EXAMPLE = "USD millions"
REGISTER_UNIT = "US$m"  # The Net debt table's Reporting unit.
PLAIN = (
    f"a plain number of at most {MAX_CELL} characters (a negative has a minus sign, a positive "
    "no plus sign) or `Not supplied: <reason>` / `Not calculable: <reason>`"
)


@dataclass(frozen=True)
class StatementSpec:
    heading: str
    fixed: tuple[str, ...]
    optional: tuple[str, ...] = ()


REPORTED = "EBITDA (Reported)"
ADJUSTED = "EBITDA (Adjusted)"
INTEREST = "Cash Interest Paid"
STATEMENTS = (
    StatementSpec("T4.4 Income statement", (REPORTED,), (ADJUSTED,)),
    StatementSpec(
        "T4.5 Cash flow statement",
        (
            "Net Cash from Operating Activities",
            "Net Cash from Investing Activities",
            "Net Cash from Financing Activities",
            "Net Cash Change",
            "Opening Cash",
            "Closing Cash",
            INTEREST,
        ),
        ("FX Effect on Cash",),
    ),
    StatementSpec(
        "T4.6 Balance sheet",
        ("Total Assets", "Total Liabilities", "Total Equity", "Total Debt", "Cash & Equivalents"),
        ("Temporary Equity",),
    ),
)
STATEMENT_TAIL = ["Unit", "Basis", "Source"]
REGISTER_HEADING = "T4.9 Calculation register"
REGISTER_COLUMNS = (
    "Metric Name",
    "Formula",
    "Numerator Value",
    "Numerator Source",
    "Denominator Value",
    "Denominator Source",
    "Period",
    "Currency",
    "Unit",
    "Calculated Value",
    "Calculation Status",
    "Evidence Quality Tier",
    "Limitations",
)
RECON_HEADING = "Debt principal to carrying value"
RECON_COLUMNS = ("Contractual principal", "Reconciling items", "Carrying value")
RECON_HEADER = ["Period", *RECON_COLUMNS, "Reporting unit", "Basis and limitation"]
NET_DEBT_HEADING = "Net debt data"
NET_DEBT_COLUMNS = ("Gross debt", "Cash", "Net debt")
LADDER_HEADING = "Chart data: debt maturities"
CHART_COLUMNS = {
    "Chart data: leverage": ("Total debt / EBITDA", "Net debt / EBITDA"),
    "Chart data: interest cover": ("EBITDA / cash interest",),
}


@dataclass(frozen=True)
class Metric:
    """A fixed register row: `numerator` is the Net debt data column the numerator must equal, or
    None when the numerator is EBITDA (cover); `ebitda` is the statement row EBITDA must equal."""

    name: str
    numerator: str | None
    ebitda: str

    @property
    def cover(self) -> bool:
        return self.numerator is None


METRICS = (
    Metric("Total debt / EBITDA", "Gross debt", REPORTED),
    Metric("Net debt / EBITDA", "Net debt", REPORTED),
    Metric("EBITDA / cash interest", None, REPORTED),
    Metric("Total debt / adjusted EBITDA", "Gross debt", ADJUSTED),
    Metric("Net debt / adjusted EBITDA", "Net debt", ADJUSTED),
    Metric("Adjusted EBITDA / cash interest", None, ADJUSTED),
)
_METRIC = {m.name: m for m in METRICS}
CORRECT = "correct whichever figure is wrong"
IDENTITY = (
    f"{CORRECT}; if the filing itself prints the difference, write `Not supplied: <reason>` on "
    "the total it cannot support and add a line under `## Gaps`"
)


def _number(cell: str) -> Decimal | None:
    return Decimal(cell.replace(",", "")) if _NUMBER.fullmatch(cell) else None


def _stated(cell: str | None) -> Decimal | None:
    """The plain number a cell holds, None for a gap, an absent cell or one too long to read."""
    return _number(cell) if cell is not None and len(cell) <= MAX_CELL else None


def _gap(cell: str) -> bool:
    return cell.startswith(GAP_WORDS) and bool(cell.partition(":")[2].strip())


def _readable(cell: str) -> bool:
    return _stated(cell) is not None or _gap(cell)


def _fmt(value: Decimal) -> str:
    return f"{value:,}"


def _sum(values: Sequence[Decimal]) -> Decimal:
    total = Decimal(0)
    for value in values:
        total = _EXACT.add(total, value)
    return total


# --- the table reader ----------------------------------------------------------------------


def _findings(text: str) -> list[str]:
    """The lines of `## Findings` outside code fences: the only place a table is read."""
    kept: list[str] = []
    inside, fence = False, None
    for line in text.splitlines():
        marker = line.lstrip()[:3]
        if marker in ("```", "~~~"):
            fence = None if fence == marker else (fence or marker)
        elif fence is None and line.startswith("## "):
            inside = line.rstrip() == "## Findings"
        elif fence is None and inside:
            kept.append(line)
    return kept


def _cells(line: str) -> list[str]:
    inner = line.strip()[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", inner)]


def _table(lines: list[str], heading: str) -> list[list[str]] | None:
    """The first table under `### heading` as rows of cells (header first, separator dropped);
    None when the heading is absent, an empty list when it holds no table."""
    try:
        start = lines.index(f"### {heading}")
    except ValueError:
        return None
    rows: list[list[str]] = []
    for line in lines[start + 1 :]:
        if line.startswith("#") or (rows and not line.startswith("|")):
            break
        if line.startswith("|"):
            rows.append(_cells(line))
    if len(rows) > 1 and all(_SEPARATOR.fullmatch(c) for c in rows[1]):
        del rows[1]
    return rows


def _records(
    lines: list[str], heading: str, header: list[str] | None = None
) -> list[dict[str, str]]:
    """The rows of a table as {column: cell}, rows of the wrong width left to that table's own
    check; empty when the table is absent or, given `header`, headed otherwise."""
    rows = _table(lines, heading)
    if not rows or "Period" not in rows[0] or (header is not None and rows[0] != header):
        return []
    return [dict(zip(rows[0], row, strict=True)) for row in rows[1:] if len(row) == len(rows[0])]


@dataclass(frozen=True)
class Statement:
    spec: StatementSpec
    periods: list[str]
    rows: dict[str, list[str]]  # label -> cells (first cell the label)
    stated_twice: tuple[str, ...]
    wrong_width: tuple[str, ...]

    def column(self, period: str) -> int | None:
        return next(
            (
                i
                for i, p in enumerate(self.periods)
                if _PERIOD_HEADER.fullmatch(p) and same_period(p, period)
            ),
            None,
        )

    def cell(self, label: str, at: int) -> str | None:
        row = self.rows.get(label)
        return row[at + 1] if row else None

    def unit(self, label: str) -> str | None:
        row = self.rows.get(label)
        return row[-3] if row else None

    def per(self, label: str) -> int | None:
        """How many of the row's units make one of the US$m tables' (1 for millions, 1,000 for
        thousands); None when the Unit cell is neither (refused where it is read)."""
        found = _UNIT.fullmatch(self.unit(label) or "")
        return None if found is None else 1000 if found[1] == "thousands" else 1


def _statement(lines: list[str], spec: StatementSpec) -> Statement | None:
    rows = _table(lines, spec.heading)
    if not rows or len(rows[0]) < 5 or rows[0][0] != "Line item" or rows[0][-3:] != STATEMENT_TAIL:
        return None
    header, body = rows[0], rows[1:]
    good = [row for row in body if len(row) == len(header)]
    counts = Counter(row[0] for row in good)
    return Statement(
        spec,
        header[1:-3],
        {row[0]: row for row in reversed(good)},
        tuple(sorted(n for n in counts if counts[n] > 1 and n in (*spec.fixed, *spec.optional))),
        tuple(row[0] for row in body if len(row) != len(header)),
    )


@dataclass(frozen=True)
class Reg:
    metric: Metric
    cells: dict[str, str]
    nd: dict[str, str] | None  # the `Net debt data` row whose Period this row's matches

    @property
    def period(self) -> str:
        return self.cells["Period"]

    @property
    def where(self) -> str:
        return f"`{REGISTER_HEADING}` {self.metric.name} {self.period}"

    @property
    def fiscal(self) -> bool:
        """A fiscal-year row (the Net debt form `FY2024 / 2024-09-30`), the only kind tied to the
        statement tables: an interim row's EBITDA is a last-twelve-months figure."""
        return self.nd is not None and _FISCAL.fullmatch(self.nd["Period"]) is not None


def _listed(net_debt: list[dict[str, str]]) -> str:
    return ", ".join(f"`{r['Period']}`" for r in net_debt)


def _net_row(net_debt: list[dict[str, str]], period: str) -> dict[str, str] | None:
    return next((r for r in net_debt if same_period(period, r["Period"])), None)


def _register(
    lines: list[str], net_debt: list[dict[str, str]]
) -> tuple[list[Reg] | None, list[str]]:
    """The fixed-name rows of the register (None when the table is absent or misheaded: the count
    in `_completeness` says so), and the issues of rows that cannot be read."""
    rows = _table(lines, REGISTER_HEADING)
    if not rows or rows[0] != list(REGISTER_COLUMNS):
        return None, []
    regs, issues = [], []
    for row in rows[1:]:
        if row[0] not in _METRIC:
            continue
        if len(row) != len(REGISTER_COLUMNS):
            issues.append(
                f"`{REGISTER_HEADING}` {row[0]} row needs {len(REGISTER_COLUMNS)} cells: "
                + " | ".join(row)
            )
            continue
        cells = dict(zip(REGISTER_COLUMNS, row, strict=True))
        regs.append(Reg(_METRIC[row[0]], cells, _net_row(net_debt, cells["Period"])))
    return regs, issues


def _find(regs: list[Reg], name: str, period: str) -> Reg | None:
    return next((r for r in regs if r.metric.name == name and same_period(r.period, period)), None)


# --- two-sided ties ------------------------------------------------------------------------


class Side(NamedTuple):
    """One side of a tie: what it is called, its cell (None when no such cell exists), where it
    is stated, and `per`, how many of its units make one of the US$m tables' unit."""

    name: str
    cell: str | None
    source: str = ""
    per: int = 1

    @property
    def said(self) -> str:
        """The figure as the message gives it: `Gross debt 24,880 stated for FY2024 in ...`."""
        return f"{self.name} {self.cell}" + (f" {self.source}" if self.source else "")

    @property
    def where(self) -> str:
        """The place alone, for a side that states nothing."""
        return f"{self.name} {self.source}".strip()


def _figure(side: Side) -> Decimal | None:
    value = _stated(side.cell)
    return value.scaleb(-3) if value is not None and side.per == 1000 else value


def _tie(where: str, left: Side, right: Side) -> str | None:
    """The issue when two stated figures differ, or when one is stated and the other is a gap or
    absent; None when both agree or neither is stated. Figures in the same unit agree exactly; one
    in thousands agrees within half a unit of the millions figure's last printed place."""
    if any(s.cell is not None and not _readable(s.cell) for s in (left, right)):
        return None  # refused where the cell is read
    a, b = _figure(left), _figure(right)
    if a is None and b is None:
        return None
    if a is None or b is None:
        stated, other = (left, right) if a is not None else (right, left)
        shown = "not stated" if other.cell is None else f"`{other.cell}`"
        return (
            f"{where}: {stated.said} is a figure, but {other.where} is {shown}, so "
            "the two cannot be compared (no difference can be worked); state the figure on both "
            "sides or write `Not supplied: <reason>` on both."
        )
    unscaled = [f for s, f in ((left, a), (right, b)) if s.per == 1]
    allowed = half_unit(unscaled) if len(unscaled) < 2 else Decimal(0)
    if abs(a - b) <= allowed:
        return None
    return f"{where}: {left.said} is not {right.said} (difference {_fmt(abs(a - b))}); {CORRECT}."


def _line_tie(found: Statement, label: str, period: str, side: Side, where: str) -> list[str]:
    """A figure of a US$m table against the statement line for the same fiscal year. A fiscal
    year with no column in the statement is refused when the figure is stated."""
    at = found.column(period)
    if at is None:
        if _stated(side.cell) is None:
            return []
        year = _FISCAL.match(period)
        text = (
            f"{where}: {side.said} is a figure, but `{found.spec.heading}` has no column for the "
            f"fiscal year of {period} (no difference can be worked); add the column, headed "
            f"`{year[0] if year else 'FY2024'}`."
        )
        return [text]
    per, cell = found.per(label), found.cell(label, at)
    if per is None or (label == INTEREST and (_stated(cell) or 0) < 0):
        return []  # refused where the Unit cell or the sign is read
    source = f"in `{found.spec.heading}` for {found.periods[at]}"
    issue = _tie(where, side, Side(f"the {label}", cell, source, per))
    return [issue] if issue else []


# --- 2a: the tables and fixed rows exist ---------------------------------------------------


def _names(names: Sequence[str]) -> str:
    return ", ".join(f"`{n}`" for n in names)


def _completeness(lines: list[str], statements: list[Statement | None]) -> list[str]:
    missing = [
        spec.heading for spec, found in zip(STATEMENTS, statements, strict=True) if found is None
    ]
    register = _table(lines, REGISTER_HEADING)
    if not register or register[0] != list(REGISTER_COLUMNS):
        missing.append(REGISTER_HEADING)
    recon = _table(lines, RECON_HEADING)
    if not recon or recon[0] != RECON_HEADER:
        missing.append(RECON_HEADING)
    notes = []
    for found in statements:
        if found is None:
            continue
        lacking = [r for r in found.spec.fixed if r not in found.rows]
        if lacking:
            notes.append(f"`{found.spec.heading}` has no row for {_names(lacking)}")
        if found.stated_twice:
            notes.append(
                f"`{found.spec.heading}` states {_names(found.stated_twice)} more than once; "
                "each fixed row is written once"
            )
    twice = [
        h
        for h in (*(s.heading for s in STATEMENTS), REGISTER_HEADING, RECON_HEADING)
        if lines.count(f"### {h}") > 1
    ]
    if twice:
        notes.append(f"{_names(twice)} appears more than once in `## Findings`; write it once")
    if not missing and not notes:
        return []
    parts = [f"{5 - len(missing)} of 5 required tables are present"]
    if missing:
        parts.append(f"missing or headed otherwise than the method states: {_names(missing)}")
    parts += notes
    return ["; ".join(parts) + ". Add what is missing; nothing is filled in for you."]


# --- 2b: operands readable -----------------------------------------------------------------


def _header_issues(found: Statement) -> list[str]:
    heading, forms = found.spec.heading, ", ".join(f"`{f}`" for f in PERIOD_FORMS)
    issues = [
        f"`{heading}` column header `{p}` is not a period: write exactly one of {forms}."
        for p in found.periods
        if not _PERIOD_HEADER.fullmatch(p)
    ]
    counts = Counter(found.periods)
    issues += [f"`{heading}` has two columns headed `{p}`." for p in counts if counts[p] > 1]
    return issues


def _line_issues(found: Statement, label: str) -> list[str]:
    heading, unit = found.spec.heading, found.unit(label)
    issues = []
    if unit is not None and _UNIT.fullmatch(unit) is None:
        issues.append(
            f"`{heading}` {label}: Unit `{unit}` must be a three-letter currency code and "
            f"`millions` or `thousands`, for example `{UNIT_EXAMPLE}`."
        )
    for at, period in enumerate(found.periods):
        cell = found.cell(label, at)
        if cell is None:
            continue
        if not _readable(cell):
            issues.append(f"`{heading}` {label} {period}: `{cell}` must be {PLAIN}.")
        elif label == INTEREST and (_stated(cell) or 0) < 0:
            issues.append(
                f"`{heading}` {label} {period}: {cell} is negative; write cash interest as the "
                "positive amount paid (the three activity totals and `FX Effect on Cash` are the "
                "signed rows, an outflow negative)."
            )
    return issues


def _statement_cells(found: Statement) -> list[str]:
    issues = [
        f"`{found.spec.heading}` row `{label}` needs {len(found.periods) + 4} cells"
        for label in found.wrong_width
    ]
    issues += _header_issues(found)
    for label in (*found.spec.fixed, *found.spec.optional):
        issues += _line_issues(found, label)
    return issues


def _orderable(period: str) -> bool:
    return period_order(period) is not None or period_of(period) is not None


def _row_issues(reg: Reg, listed: list[dict[str, str]]) -> list[str]:
    """One register row's cells: readable, its Period one of the Net debt rows', its Unit that
    row's Reporting unit, its Calculated Value to two places."""
    issues = [
        f"{reg.where}: {column} `{reg.cells[column]}` must be {PLAIN}."
        for column in ("Numerator Value", "Denominator Value", "Calculated Value")
        if not _readable(reg.cells[column])
    ]
    if not _orderable(reg.period):
        forms = ", ".join(f"`{f}`" for f in PERIOD_FORMS)
        issues.append(
            f"{reg.where}: Period `{reg.period}` is not a Period of `{NET_DEBT_HEADING}` or a "
            f"period column header such as {forms}."
        )
    elif listed and reg.nd is None:
        issues.append(
            f"{reg.where}: Period `{reg.period}` matches no Period cell of `{NET_DEBT_HEADING}` "
            f"({_listed(listed)}); write the Period cell of the Net "
            "debt row it belongs to, for example `FY2024 / 2024-09-30`."
        )
    issues += [
        f"{reg.where}: {column} is empty."
        for column in ("Currency", "Unit")
        if not reg.cells[column]
    ]
    unit = reg.cells["Unit"]
    if unit and reg.nd and reg.nd.get("Reporting unit", unit) != unit:
        issues.append(
            f"{reg.where}: Unit `{unit}` is not the Reporting unit `{reg.nd['Reporting unit']}` "
            f"of the `{NET_DEBT_HEADING}` row for {reg.nd['Period']}; the register's Unit must "
            "equal it."
        )
    return issues


def _register_cells(regs: list[Reg], net_debt: list[dict[str, str]]) -> list[str]:
    issues = []
    seen: set[tuple[str, str]] = set()
    for reg in regs:
        issues += _row_issues(reg, net_debt)
        issues += _precision(reg)
        key = (reg.metric.name, reg.period)
        if key in seen:
            issues.append(f"{reg.where}: stated twice; one row names each metric and period once.")
        seen.add(key)
    return issues


def _precision(reg: Reg) -> list[str]:
    """The Calculated Value of a fixed row is printed to exactly two decimal places."""
    cell = reg.cells["Calculated Value"]
    if _stated(cell) is None or _TWO_PLACES.fullmatch(cell):
        return []
    n, d = (_stated(reg.cells[c]) for c in ("Numerator Value", "Denominator Value"))
    worked = (
        f" ({n:,} divided by {d:,} is {_quotient(n, d, 2)})"
        if n is not None and d is not None and d > 0
        else ""
    )
    text = (
        f"{reg.where}: Calculated Value {cell} must be printed to exactly two decimal "
        f"places, for example 6.53{worked}."
    )
    return [text]


# --- 2c: ratio recomputed ------------------------------------------------------------------


def _fixed(value: Fraction, places: int) -> str:
    """`value` to `places` decimal places, half up, written digit by digit (no context precision
    applies to an integer)."""
    scaled = value * 10**places
    half_up = (abs(scaled.numerator) * 2 + scaled.denominator) // (2 * scaled.denominator)
    digits = str(half_up).rjust(places + 1, "0")
    return f"{'-' if value < 0 else ''}{digits[:-places]}.{digits[-places:]}"


def _quotient(numerator: Decimal, denominator: Decimal, places: int) -> str:
    """The exact quotient to `places` + 2 decimal places."""
    return _fixed(Fraction(numerator) / Fraction(denominator), places + 2)


def recomputation(numerator: str, denominator: str, calculated: str) -> str | None:
    """Why `calculated` is not numerator / denominator, or None when it is (to half a unit of its
    own last printed place) or when a figure is not a stated number. A stated denominator that is
    not above zero leaves no ratio to state."""
    n, d, c = _number(numerator), _number(denominator), _number(calculated)
    if d is None or c is None:
        return None
    if d <= 0:
        return (
            f"the denominator {denominator} is not above zero, so the Calculated Value "
            f"{calculated} cannot be a number; write `Not calculable: <reason>`"
        )
    if n is None:
        return None
    places = len(calculated.partition(".")[2])
    exact = Fraction(n) / Fraction(d)
    if abs(Fraction(c) - exact) <= Fraction(1, 2 * 10**places):
        return None
    return (
        f"the Calculated Value {calculated} is not {numerator} divided by {denominator} "
        f"({_quotient(n, d, places)}; difference {_fixed(abs(Fraction(c) - exact), places + 2)}); "
        "it must be within half a unit of its last printed place"
    )


def _unstated_operands(numerator: str, denominator: str, calculated: str) -> str | None:
    """A stated Calculated Value needs both operands stated."""
    if _stated(calculated) is None:
        return None
    lacking = [
        f"{name} `{cell}`"
        for name, cell in (("numerator", numerator), ("denominator", denominator))
        if _stated(cell) is None
    ]
    if not lacking:
        return None
    return (
        f"the Calculated Value {calculated} is stated, but the {' and the '.join(lacking)} state "
        "no figure, so it cannot be worked out (no difference can be worked); state the operands "
        "or write `Not calculable: <reason>`"
    )


def _ratios(regs: list[Reg]) -> list[str]:
    issues = []
    for reg in regs:
        n, d, c = (
            reg.cells[k] for k in ("Numerator Value", "Denominator Value", "Calculated Value")
        )
        if all(_readable(cell) for cell in (n, d, c)):  # an unreadable cell is refused as such
            why = recomputation(n, d, c) or _unstated_operands(n, d, c)
            if why:
                issues.append(f"{reg.where}: {why}; {CORRECT}.")
    return issues


def _long_cells(lines: list[str], net_debt: list[dict[str, str]]) -> list[str]:
    """A figure cell of the chart or Net debt tables longer than MAX_CELL is not a plain number."""
    tables = [(h, c, _records(lines, h)) for h, c in CHART_COLUMNS.items()]
    tables.append((NET_DEBT_HEADING, NET_DEBT_COLUMNS, net_debt))
    return [
        f"`{heading}` {record['Period']} {column}: `{record[column][:30]}...` is not {PLAIN}."
        for heading, columns, records in tables
        for record in records
        for column in columns
        if len(record.get(column, "")) > MAX_CELL and not _gap(record[column])
    ]


# --- 2d: chart ties ------------------------------------------------------------------------


def _chart_ties(lines: list[str], regs: list[Reg]) -> list[str]:
    issues = []
    for heading, columns in CHART_COLUMNS.items():
        for record in _records(lines, heading):
            for column in columns:
                if column not in record:
                    continue  # the chart table's own check says so
                reg = _find(regs, column, record["Period"])
                value = reg.cells["Calculated Value"] if reg else None
                issue = _tie(
                    f"`{heading}` {record['Period']}",
                    Side(column, record[column]),
                    Side("the Calculated Value", value, f"in `{REGISTER_HEADING}`"),
                )
                if issue:
                    issues.append(issue)
    return issues


def _numerator_ties(regs: list[Reg]) -> list[str]:
    issues = []
    for reg in regs:
        column = reg.metric.numerator
        if column is None or reg.nd is None or column not in reg.nd:
            continue
        source = f"stated for {reg.nd['Period']} in `{NET_DEBT_HEADING}`"
        issue = _tie(
            reg.where,
            Side("the numerator", reg.cells["Numerator Value"]),
            Side(f"the {column}", reg.nd[column], source),
        )
        if issue:
            issues.append(issue)
    return issues


# --- 2e: statement ties (fiscal-year rows) -------------------------------------------------


def _operand_ties(reg: Reg, income: Statement | None, flow: Statement | None) -> list[str]:
    """A fiscal-year register row's EBITDA and cash interest operands against their statement
    lines (found by the fiscal year of its Net debt row); an interim row has no statement tie."""
    if not reg.fiscal or reg.nd is None:
        return []
    column = "Numerator Value" if reg.metric.cover else "Denominator Value"
    pairs = [(income, reg.metric.ebitda, column)]
    if reg.metric.cover:
        pairs.append((flow, INTEREST, "Denominator Value"))
    issues = []
    for found, label, operand in pairs:
        if found is not None:
            side = Side(operand, reg.cells[operand])
            issues += _line_tie(found, label, reg.nd["Period"], side, reg.where)
    return issues


def _net_debt_ties(balance: Statement | None, net_debt: list[dict[str, str]]) -> list[str]:
    """A fiscal-year Net debt row's gross debt and cash against the balance sheet's Total Debt and
    Cash & Equivalents for that year."""
    if balance is None:
        return []
    issues = []
    for record in net_debt:
        if _FISCAL.fullmatch(record["Period"]) is None:
            continue
        for column, label in (("Gross debt", "Total Debt"), ("Cash", "Cash & Equivalents")):
            if column in record:
                where = f"`{NET_DEBT_HEADING}` {record['Period']}"
                issues += _line_tie(
                    balance, label, record["Period"], Side(column, record[column]), where
                )
    return issues


# --- 2f: statement reconciliations ---------------------------------------------------------


def _adds_up(
    found: Statement, at: int, parts: list[str], total: str, optional: tuple[str, ...] = ()
) -> str | None:
    """Parts (and the optional rows when stated) must add to the total, to half a unit of the
    finest printed place among them."""
    labels = [*parts, *(o for o in optional if _stated(found.cell(o, at)) is not None)]
    figures = [_stated(found.cell(label, at)) for label in labels]
    held = _stated(found.cell(total, at))
    if held is None or any(f is None for f in figures):
        return None
    values = [f for f in figures if f is not None]
    added = _sum(values)
    if not beyond_rounding(held, added, values):
        return None
    shown = ", ".join(f"{label} {found.cell(label, at)}" for label in labels)
    return (
        f"`{found.spec.heading}` {found.periods[at]}: {shown} add to {_fmt(added)}, not the "
        f"{total} {found.cell(total, at)} (difference {_fmt(abs(held - added))}); {IDENTITY}."
    )


def _statement_sums(
    found: Statement | None, rules: list[tuple[list[str], str, tuple[str, ...]]]
) -> list[str]:
    if found is None:
        return []
    issues = (
        _adds_up(found, at, parts, total, optional)
        for at in range(len(found.periods))
        for parts, total, optional in rules
    )
    return [i for i in issues if i]


FLOWS = [
    "Net Cash from Operating Activities",
    "Net Cash from Investing Activities",
    "Net Cash from Financing Activities",
]
BALANCE_RULES: list[tuple[list[str], str, tuple[str, ...]]] = [
    (["Total Liabilities", "Total Equity"], "Total Assets", ("Temporary Equity",))
]
CASH_RULES: list[tuple[list[str], str, tuple[str, ...]]] = [
    (FLOWS, "Net Cash Change", ("FX Effect on Cash",)),
    (["Opening Cash", "Net Cash Change"], "Closing Cash", ()),
]


# --- 2g: the ladder ------------------------------------------------------------------------


def ladder_issues(
    ladder: list[str], principal: str, items: str, carrying: str, period: str = ""
) -> list[str]:
    """When the Contractual principal is stated, every ladder row is stated and they add to it
    exactly; when all three reconciliation figures are stated, principal plus reconciling items is
    the carrying value exactly. Figures are plain numbers (the table check caps their length)."""
    issues, at = [], f" for {period}" if period else ""
    rows, stated = [_number(c) for c in ladder], _number(principal)
    if stated is not None:
        lacking = [
            (n, c) for n, (c, v) in enumerate(zip(ladder, rows, strict=True), 1) if v is None
        ]
        if lacking:
            issues.append(
                f"`{LADDER_HEADING}`{at}: the Contractual principal {principal} is stated, but "
                + " and ".join(f"Debt maturing row {n} is `{c}`" for n, c in lacking)
                + f", so the rows cannot add to it (no difference can be worked); {CORRECT}."
            )
        elif rows:
            total = _sum([v for v in rows if v is not None])
            if total != stated:
                issues.append(
                    f"`{LADDER_HEADING}`{at}: the rows add to {_fmt(total)}, not the Contractual "
                    f"principal {principal} (difference {_fmt(abs(stated - total))}); {CORRECT}."
                )
    figures = [_number(c) for c in (principal, items, carrying)]
    if all(f is not None for f in figures):
        p, i, c = (f for f in figures if f is not None)
        if _sum([p, i]) != c:
            issues.append(
                f"`{RECON_HEADING}`{at}: Contractual principal {principal} plus Reconciling items "
                f"{items} is {_fmt(_sum([p, i]))}, not the Carrying value {carrying} (difference "
                f"{_fmt(abs(c - _sum([p, i])))}); {CORRECT}."
            )
    return issues


def _reconciliation(lines: list[str], net_debt: list[dict[str, str]]) -> list[str]:
    table = _table(lines, RECON_HEADING)
    if not table or table[0] != RECON_HEADER:
        return []  # absent or misheaded: `_completeness` says so
    if len(table) != 2:
        return [
            (
                f"`{RECON_HEADING}` states {len(table) - 1} rows; write exactly one, for the "
                "balance-sheet date the ladder is drawn at."
            )
        ]
    rows = _records(lines, RECON_HEADING, RECON_HEADER)
    if not rows:
        return [f"`{RECON_HEADING}` row needs {len(RECON_HEADER)} cells: {' | '.join(table[1])}"]
    row, period = rows[0], rows[0]["Period"]
    ladder = [r["Debt maturing"] for r in _records(lines, LADDER_HEADING) if "Debt maturing" in r]
    figures = [row[c] for c in RECON_COLUMNS]
    too_long = [c for c in (*figures, *ladder) if len(c) > MAX_CELL and not _gap(c)]
    if too_long:
        return [f"`{RECON_HEADING}` or `{LADDER_HEADING}`: `{too_long[0][:30]}...` is not {PLAIN}."]
    issues = ladder_issues(ladder, figures[0], figures[1], figures[2], period)
    nd = _net_row(net_debt, period)
    if nd is None and net_debt:
        issues.append(
            f"`{RECON_HEADING}` Period `{period}` matches no Period cell of `{NET_DEBT_HEADING}` "
            f"({_listed(net_debt)}); write the Period cell of the "
            "Net debt row for the balance-sheet date, for example `FY2024 / 2024-09-30`."
        )
    elif nd is not None and "Gross debt" in nd:
        tie = _tie(
            f"`{RECON_HEADING}` {period}",
            Side("Carrying value", row["Carrying value"]),
            Side(
                "the Gross debt",
                nd["Gross debt"],
                f"stated for {nd['Period']} in `{NET_DEBT_HEADING}`",
            ),
        )
        issues += [tie] if tie else []
    return issues


# --- the check -----------------------------------------------------------------------------


def cp1_issues(text: str) -> tuple[str, ...]:
    """Each way CP-1's statement tables, calculation register and debt reconciliation fail the
    method's own arithmetic and completeness, one sentence each, for the rejection path."""
    lines = _findings(text)
    statements = [_statement(lines, spec) for spec in STATEMENTS]
    income, flow, balance = statements
    net_debt = _records(lines, NET_DEBT_HEADING)
    found_regs, unreadable = _register(lines, net_debt)
    regs = found_regs or []
    steps: list[Callable[[], list[str]]] = [
        lambda: _completeness(lines, statements),
        lambda: [i for found in statements if found for i in _statement_cells(found)],
        lambda: unreadable,
        lambda: _register_cells(regs, net_debt),
        lambda: _long_cells(lines, net_debt),
        lambda: _ratios(regs),
        lambda: _chart_ties(lines, regs) if found_regs is not None else [],
        lambda: _numerator_ties(regs),
        lambda: [i for reg in regs for i in _operand_ties(reg, income, flow)],
        lambda: _net_debt_ties(balance, net_debt),
        lambda: _statement_sums(balance, BALANCE_RULES),
        lambda: _statement_sums(flow, CASH_RULES),
        lambda: _reconciliation(lines, net_debt),
    ]
    return tuple(issue for step in steps for issue in step())
