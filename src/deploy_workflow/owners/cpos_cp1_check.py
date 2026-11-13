"""CP-1's figures, checked in code when its handoff is accepted.

Every comparison runs only when each figure in it is a stated plain number: a `Not supplied:` or
`Not calculable:` cell is never read as zero and never refused for being absent. The tables the
check reads, and their fixed rows and names, are defined here once; the launcher text sent to CP-1
is rendered from these constants. Decimal and Fraction only: no float touches an amount or ratio.

This module imports nothing from `cpos_launch` (which imports it), so it keeps its own small table
reader."""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from deploy_vii.model._cells import beyond_rounding
from deploy_workflow.changes import same_period
from deploy_workflow.credit_os_catalogue import period_order
from deploy_workflow.owners.cpos_periods import period_of

_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
GAP_WORDS = ("Not supplied:", "Not calculable:")
STATEMENT_UNIT = "USD millions"  # The statement tables' unit; the Net debt table is US$m.
REGISTER_UNIT = "US$m"


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


def _number(cell: str) -> Decimal | None:
    return Decimal(cell.replace(",", "")) if _NUMBER.fullmatch(cell) else None


def _gap(cell: str) -> bool:
    return cell.startswith(GAP_WORDS) and bool(cell.partition(":")[2].strip())


def _readable(cell: str) -> bool:
    return _number(cell) is not None or _gap(cell)


def _fmt(value: Decimal) -> str:
    return f"{value:,}"


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
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    if len(rows) > 1 and all(re.fullmatch(r":?-{3,}:?", c) for c in rows[1]):
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
        return next((i for i, p in enumerate(self.periods) if same_period(p, period)), None)

    def cell(self, label: str, at: int) -> str | None:
        row = self.rows.get(label)
        return row[at + 1] if row else None

    def unit(self, label: str) -> str | None:
        row = self.rows.get(label)
        return row[-3] if row else None


def _statement(lines: list[str], spec: StatementSpec) -> Statement | None:
    rows = _table(lines, spec.heading)
    if not rows or len(rows[0]) < 5 or rows[0][0] != "Line item" or rows[0][-3:] != STATEMENT_TAIL:
        return None
    header, body = rows[0], rows[1:]
    good = [row for row in body if len(row) == len(header)]
    labels = [row[0] for row in good]
    return Statement(
        spec,
        header[1:-3],
        {row[0]: row for row in reversed(good)},
        tuple(
            sorted(
                {n for n in labels if labels.count(n) > 1 and n in (*spec.fixed, *spec.optional)}
            )
        ),
        tuple(row[0] for row in body if len(row) != len(header)),
    )


@dataclass(frozen=True)
class Reg:
    metric: Metric
    cells: dict[str, str]

    @property
    def period(self) -> str:
        return self.cells["Period"]

    @property
    def where(self) -> str:
        return f"`{REGISTER_HEADING}` {self.metric.name} {self.period}"


def _register(lines: list[str]) -> tuple[list[Reg] | None, list[str]]:
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
        regs.append(Reg(_METRIC[row[0]], dict(zip(REGISTER_COLUMNS, row, strict=True))))
    return regs, issues


def _find(regs: list[Reg], name: str, period: str) -> Reg | None:
    return next((r for r in regs if r.metric.name == name and same_period(r.period, period)), None)


# --- 2a: the tables and fixed rows exist ---------------------------------------------------


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
    if not missing and not notes:
        return []
    count = f"{5 - len(missing)} of 5 required tables are present"
    parts = [f"{count}"]
    if missing:
        parts.append(f"missing or headed otherwise than the method states: {_names(missing)}")
    parts += notes
    return ["; ".join(parts) + ". Add what is missing; nothing is filled in for you."]


def _names(names: Sequence[str]) -> str:
    return ", ".join(f"`{n}`" for n in names)


# --- 2b: operands readable -----------------------------------------------------------------


def _statement_cells(found: Statement) -> list[str]:
    issues = [
        f"`{found.spec.heading}` row `{label}` needs {len(found.periods) + 4} cells"
        for label in found.wrong_width
    ]
    for label in (*found.spec.fixed, *found.spec.optional):
        for at, period in enumerate(found.periods):
            cell = found.cell(label, at)
            if cell is not None and not _readable(cell):
                issues.append(
                    f"`{found.spec.heading}` {label} {period}: `{cell}` must be a plain number or "
                    "`Not supplied: <reason>` / `Not calculable: <reason>`."
                )
    return issues


def _orderable(period: str) -> bool:
    return period_order(period) is not None or period_of(period) is not None


def _register_cells(regs: list[Reg]) -> list[str]:
    issues = []
    seen: set[tuple[str, str]] = set()
    for reg in regs:
        issues += [
            f"{reg.where}: {column} `{reg.cells[column]}` must be a plain number or "
            "`Not supplied: <reason>` / `Not calculable: <reason>`."
            for column in ("Numerator Value", "Denominator Value", "Calculated Value")
            if not _readable(reg.cells[column])
        ]
        if not _orderable(reg.period):
            issues.append(
                f"{reg.where}: Period `{reg.period}` is not a period column header such as "
                "`FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`."
            )
        issues += [
            f"{reg.where}: {column} is empty."
            for column in ("Currency", "Unit")
            if not reg.cells[column]
        ]
        if reg.cells["Unit"] and reg.cells["Unit"] != REGISTER_UNIT:
            issues.append(f"{reg.where}: Unit is `{reg.cells['Unit']}`; write `{REGISTER_UNIT}`.")
        key = (reg.metric.name, reg.period)
        if key in seen:
            issues.append(f"{reg.where}: stated twice; one row names each metric and period once.")
        seen.add(key)
    return issues


# --- 2c: ratio recomputed ------------------------------------------------------------------


def _quotient(numerator: Decimal, denominator: Decimal, places: int) -> str:
    """The exact quotient to `places` + 2 decimal places, written out digit by digit (no context
    precision applies to an integer)."""
    shown = places + 2
    quotient = Fraction(numerator) / Fraction(denominator) * 10**shown
    scaled = abs(quotient.numerator) * 2 + quotient.denominator
    digits = str(scaled // (2 * quotient.denominator)).rjust(shown + 1, "0")
    sign = "-" if quotient < 0 else ""
    return f"{sign}{digits[:-shown]}.{digits[-shown:]}"


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
    if abs(Fraction(c) - Fraction(n) / Fraction(d)) <= Fraction(1, 2 * 10**places):
        return None
    return (
        f"the Calculated Value {calculated} is not {numerator} divided by {denominator} "
        f"({_quotient(n, d, places)}); it must be within half a unit of its last printed place"
    )


def _ratios(regs: list[Reg]) -> list[str]:
    found = (
        (
            r,
            recomputation(
                r.cells["Numerator Value"],
                r.cells["Denominator Value"],
                r.cells["Calculated Value"],
            ),
        )
        for r in regs
    )
    return [f"{r.where}: {why}; {CORRECT}." for r, why in found if why]


# --- 2d: chart ties ------------------------------------------------------------------------


def _chart_ties(lines: list[str], regs: list[Reg]) -> list[str]:
    issues = []
    for heading, columns in CHART_COLUMNS.items():
        for record in _records(lines, heading):
            for column in columns:
                shown = record.get(column, "")
                if _number(shown) is None:
                    continue
                reg = _find(regs, column, record["Period"])
                if reg is None:
                    issues.append(
                        f"`{heading}` {record['Period']}: {column} {shown} has no row for that "
                        f"period in `{REGISTER_HEADING}`; add it, worked from the figures."
                    )
                elif (
                    value := _number(reg.cells["Calculated Value"])
                ) is not None and value != _number(shown):
                    issues.append(
                        f"`{heading}` {record['Period']}: {column} {shown} is not the Calculated "
                        f"Value {reg.cells['Calculated Value']} in `{REGISTER_HEADING}`; {CORRECT}."
                    )
    return issues


def _numerator_ties(net_debt: list[dict[str, str]], regs: list[Reg]) -> list[str]:
    issues = []
    for reg in regs:
        column = reg.metric.numerator
        stated = _number(reg.cells["Numerator Value"])
        if column is None or stated is None:
            continue
        for record in net_debt:
            held = _number(record.get(column, ""))
            if held is not None and same_period(reg.period, record["Period"]) and held != stated:
                issues.append(
                    f"{reg.where}: the numerator {reg.cells['Numerator Value']} is not the "
                    f"{column} {record[column]} stated for {record['Period']} in "
                    f"`{NET_DEBT_HEADING}`; {CORRECT}."
                )
    return issues


# --- 2e: statement ties --------------------------------------------------------------------


def _operand_ties(reg: Reg, income: Statement | None, flow: Statement | None) -> list[str]:
    """The register row's EBITDA and cash interest operands against their statement lines."""
    cover = reg.metric.cover
    pairs = [
        (income, reg.metric.ebitda, "Numerator Value" if cover else "Denominator Value"),
        (flow, INTEREST, "Denominator Value" if cover else ""),
    ]
    issues = []
    for found, label, column in pairs:
        at = found.column(reg.period) if found and column else None
        if found is None or at is None or found.unit(label) != STATEMENT_UNIT:
            continue
        shown, stated = found.cell(label, at) or "", reg.cells[column]
        if (
            _number(shown) is not None
            and _number(stated) is not None
            and _number(shown) != _number(stated)
        ):
            issues.append(
                f"{reg.where}: {column} {stated} is not the {label} {shown} in "
                f"`{found.spec.heading}` for {found.periods[at]}; {CORRECT}."
            )
    return issues


def _debt_tie(balance: Statement | None, net_debt: list[dict[str, str]]) -> list[str]:
    if balance is None or balance.unit("Total Debt") != STATEMENT_UNIT:
        return []
    issues = []
    for at, period in enumerate(balance.periods):
        shown = balance.cell("Total Debt", at) or ""
        for record in net_debt:
            gross = record.get("Gross debt", "")
            if (
                same_period(period, record["Period"])
                and _number(shown) is not None
                and _number(gross) is not None
                and _number(shown) != _number(gross)
            ):
                issues.append(
                    f"`{balance.spec.heading}` Total Debt {period}: {shown} is not the Gross debt "
                    f"{gross} stated for {record['Period']} in `{NET_DEBT_HEADING}`; {CORRECT}."
                )
    return issues


# --- 2f: statement reconciliations ---------------------------------------------------------


def _adds_up(
    found: Statement, at: int, parts: list[str], total: str, optional: tuple[str, ...] = ()
) -> str | None:
    """Parts (and the optional rows when stated) must add to the total, to half a unit of the
    finest printed place among them."""
    labels = [*parts, *(o for o in optional if _number(found.cell(o, at) or "") is not None)]
    figures = [_number(found.cell(label, at) or "") for label in labels]
    held = _number(found.cell(total, at) or "")
    if held is None or any(f is None for f in figures):
        return None
    values = [f for f in figures if f is not None]
    added = sum(values, Decimal(0))
    if not beyond_rounding(held, added, values):
        return None
    shown = ", ".join(f"{label} {found.cell(label, at)}" for label in labels)
    return (
        f"`{found.spec.heading}` {found.periods[at]}: {shown} add to {_fmt(added)}, not the "
        f"{total} {found.cell(total, at)} (difference {_fmt(abs(held - added))}); {CORRECT}."
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


def ladder_issues(ladder: list[str], principal: str, items: str, carrying: str) -> list[str]:
    """The ladder's rows sum to the contractual principal, and principal plus reconciling items is
    the carrying value, each exactly and each only when its figures are all stated."""
    issues = []
    rows, stated = [_number(c) for c in ladder], _number(principal)
    if rows and stated is not None and all(r is not None for r in rows):
        total = sum((r for r in rows if r is not None), Decimal(0))
        if total != stated:
            issues.append(
                f"`{LADDER_HEADING}` rows add to {_fmt(total)}, not the Contractual principal "
                f"{principal} (difference {_fmt(abs(stated - total))}); {CORRECT}."
            )
    figures = [_number(c) for c in (principal, items, carrying)]
    if all(f is not None for f in figures):
        p, i, c = (f for f in figures if f is not None)
        if p + i != c:
            issues.append(
                f"`{RECON_HEADING}`: Contractual principal {principal} plus Reconciling items "
                f"{items} is {_fmt(p + i)}, not the Carrying value {carrying} (difference "
                f"{_fmt(abs(c - p - i))}); {CORRECT}."
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
    row = rows[0]
    ladder = [r["Debt maturing"] for r in _records(lines, LADDER_HEADING) if "Debt maturing" in r]
    issues = ladder_issues(ladder, *(row[c] for c in RECON_COLUMNS))
    carrying = _number(row["Carrying value"])
    for record in net_debt:
        gross = _number(record.get("Gross debt", ""))
        if (
            carrying is not None
            and gross is not None
            and same_period(row["Period"], record["Period"])
            and carrying != gross
        ):
            issues.append(
                f"`{RECON_HEADING}` {row['Period']}: Carrying value {row['Carrying value']} is "
                f"not the Gross debt {record['Gross debt']} stated for {record['Period']} in "
                f"`{NET_DEBT_HEADING}`; {CORRECT}."
            )
    return issues


# --- the check -----------------------------------------------------------------------------


def cp1_issues(text: str) -> tuple[str, ...]:
    """Each way CP-1's statement tables, calculation register and debt reconciliation fail the
    method's own arithmetic and completeness, one sentence each, for the rejection path."""
    lines = text.splitlines()
    statements = [_statement(lines, spec) for spec in STATEMENTS]
    income, flow, balance = statements
    found_regs, unreadable = _register(lines)
    regs = found_regs or []
    net_debt = _records(lines, NET_DEBT_HEADING)
    steps: list[Callable[[], list[str]]] = [
        lambda: _completeness(lines, statements),
        lambda: [i for found in statements if found for i in _statement_cells(found)],
        lambda: unreadable,
        lambda: _register_cells(regs),
        lambda: _ratios(regs),
        lambda: _chart_ties(lines, regs) if found_regs is not None else [],
        lambda: _numerator_ties(net_debt, regs),
        lambda: [i for reg in regs for i in _operand_ties(reg, income, flow)],
        lambda: _debt_tie(balance, net_debt),
        lambda: _statement_sums(balance, BALANCE_RULES),
        lambda: _statement_sums(flow, CASH_RULES),
        lambda: _reconciliation(lines, net_debt),
    ]
    return tuple(issue for step in steps for issue in step())
