"""The portfolio export: a fund's mandate, constraints and exposure report as CSV exports, with a
holdings workbook (ruling 2026-11-15-full-assessment-portfolio-workbook, "The export shape").

This is the shape the owner's portfolio data arrives in, beside the template workbook
(`deploy_vii.inputs.portfolio`). It is checked, never converted into the template: converting
would mean choosing between figures that disagree, which the CP-6A method says to surface instead.

The holdings are the authority. From them the check recomputes par, market value at mid
((bid + ask) / 2 x par / 100), position, borrower, ticker and sector counts, issuer and sector
shares of the recomputed market value, the second-lien share and par-weighted averages of price,
margin and yield. Every figure the exposure report, the constraints or the mandate states is a
claim checked against that recomputation or against the file's own rows and totals. Nothing is
coerced: a cell that cannot be read with its unit, a vendor error token (`#N/A N/A`) or an
approximate value (`~100%`) is missing, never zero, and is reported.

Tolerances, all stated here and tested: a stated figure is rounded to the places it shows, so it
may differ from the exact figure by half a unit in its last place (a sum of n stated figures by the
sum of those halves); a figure the fund marks itself (NAV, market values, the average price, shares
of NAV) may also differ from a recomputation at mid by `MARK_TOLERANCE` of the stated figure.
Counts and par are exact.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Context, Decimal, InvalidOperation
from pathlib import Path

from deploy_vii.contracts import Span
from deploy_vii.inputs.rv_quotes import Issue, ValidationReport, sheet_cells
from deploy_vii.preparation import xlsx_content

EXACT = Context(prec=2000, Emax=9999, Emin=-9999)
HUNDRED = Decimal(100)
MARK_TOLERANCE = Decimal("0.005")  # 0.5 % of a figure the fund marks, against mid
CAPITAL_BAND = Decimal("0.05")  # the tranches fund 95 % to 105 % of the collateral
STALE_DAYS = 30
CENTURY = 1950  # a maturity before this year is a two-digit year read as 19xx
YTM_RANGE = (Decimal(-10), Decimal(100))  # percent
DM_RANGE = (Decimal(-1000), Decimal(10000))  # basis points
FIGI = re.compile(r"^[A-Z0-9]{12}$")
TOKEN = re.compile(r"^#(?:N/?A|VALUE!|REF!|DIV/0!|NAME\?|NUM!|NULL!)", re.IGNORECASE)
RATING_LIKE = re.compile(r"^(?:[A-Z][a-z]{0,2}\d?|[A-Z]{1,3}[+-]?)\s*/\s*\S")
MOJIBAKE = re.compile("[�\u0000-\u0008\u000b\u000c\u000e-\u001f]|Ã.|â€")
WITHDRAWN = frozenset({"WR", "NR"})
_AGENCIES = re.compile(r"\s+/\s+")  # Moody's / S&P; "#N/A" holds an unspaced slash
SHOWN = Decimal("0.01")
LISTED = 5  # rows named in one aggregated finding
FILE_FIX = "export the file again from the source system"
ROLES = ("mandate", "constraints", "exposure", "holdings", "market")

FIX: Mapping[str, str] = {
    "par": (
        "correct the stated figure, or the holdings, so the report states what the holdings hold"
    ),
    "count": "correct the stated count to the holdings' count, or correct the holdings",
    "nav": "correct the stated NAV or the holdings' prices: the holdings at mid do not add to it",
    "share": "correct the stated share to the holdings' share, or correct the holdings",
    "absent": "remove the row, or add the holding to the holdings sheet",
    "breach": "correct the stated figure and the status: on the holdings' figures the limit is "
    "breached",
    "total": "correct the total or its rows: a total adds its rows",
    "metric": "correct the stated figure to the holdings' figure, or correct the holdings",
    "plausible": "correct the yield or the margin: a loan's yield is above its margin over the "
    "base rate",
    "capital": "correct the capital structure or the collateral figure: they do not balance",
    "century": "enter four-digit years: the export read two-digit years as 19xx",
    "matured": "delete the matured positions, or correct their maturity dates",
    "range": "correct the values or leave them empty: they are outside any loan's range",
    "token": "fill the missing values from the source, or leave them empty; the check treats "
    "them as missing, never as zero",
    "figi": "correct the identifier: a FIGI has 12 capital letters and digits",
    "figi_reuse": "give each loan its own FIGI",
    "ticker": "give each borrower its own ticker, or correct the borrower name",
    "name": "export the file again with UTF-8 text, or correct the name",
    "ranking": "enter the lien ranking (e.g. 1st Lien) in Ranking; the rating goes in Ratings",
    "empty_rows": "delete the empty rows below the data",
    "bid_ask": "correct the quote: a bid is at or below its ask",
    "tranche": "correct the position or the tranche size: a holding is part of its tranche",
    "kind": "move the value to its own column",
    "borrower_tickers": "give each borrower one ticker, or correct the ticker",
    "stale": f"supply figures measured at most {STALE_DAYS} days before the run's as-of date",
    "future": "enter the date the figures were measured, on or before the run's as-of date",
    "unit": "enter the figure with its unit, e.g. 2.5% NAV, 313 bps or 4.8 yrs",
    "approximate": "enter the exact figure: an approximate value cannot be checked against a limit",
    "differs": "correct the file that is wrong: the two constraints files state different figures",
    "lien": "enter the lien position (1L, 2L) at the start of Ranking",
    "headroom": "enter the limit minus the current value (or the reverse for a minimum)",
    "status": "enter the status the figures give: Breach exactly when the limit is not met",
    "layout": "export the report with its sections A to E, each a title row, a header row and "
    "data rows",
    "column": "export the sheet with its full header row",
    "missing": "add the holdings sheet: without it no stated figure can be verified",
    "par_cell": "enter the position's par in Holdings, a plain number",
}


# --- Values with units ---------------------------------------------------------------------------

_OPERATORS = {"≤": "<=", "<=": "<=", "≥": ">=", ">=": ">=", "<": "<=", ">": ">="}
_QUANTITY = re.compile(
    r"^(?P<op>≤|≥|<=|>=|<|>)?\s*(?P<approx>~)?\s*(?P<cur>USD|EUR|GBP|\$|€|£)?\s*"
    r"(?P<num>[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*"
    r"(?P<mult>bn|mm|mn|m|k)?\s*(?P<unit>%\s*NAV|%|bps?|yrs?|years?|notches|x|USD|EUR|GBP)?$",
    re.IGNORECASE,
)
_RATING_NUMBER = re.compile(
    r"^(?P<op>≤|≥|<=|>=)?\s*[A-Za-z]{1,4}\d?[+-]?\s*\(\s*(?:numeric\s*)?(?P<inner>≤|≥|<=|>=)?\s*"
    r"(?P<num>\d+(?:\.\d+)?)\s*\)$"
)
_MULTIPLIER = {"k": Decimal(1000), "m": Decimal(10**6), "mm": Decimal(10**6), "mn": Decimal(10**6)}
_MULTIPLIER["bn"] = Decimal(10**9)
_UNITS = {"bp": "bps", "bps": "bps", "yr": "yrs", "yrs": "yrs", "year": "yrs", "years": "yrs"}


@dataclass(frozen=True)
class Quantity:
    """A stated figure with its unit. `places` is the decimals it was written with (before any
    multiplier), so `half_unit` is how far rounding can have moved it."""

    value: Decimal
    unit: str = ""
    operator: str = ""
    approximate: bool = False
    places: int = 0
    scale: Decimal = Decimal(1)

    @property
    def half_unit(self) -> Decimal:
        return EXACT.multiply(Decimal(5).scaleb(-self.places - 1), self.scale)

    @property
    def percent(self) -> bool:
        return self.unit in ("%", "% NAV")


def quantity(text: str) -> Quantity | None:
    """`text` as a figure with its unit, or None when it cannot be read that way (never coerced)."""
    text = " ".join(text.split())
    rating = _RATING_NUMBER.match(text)
    if rating is not None:
        op = _OPERATORS.get(rating["inner"] or rating["op"] or "", "")
        return Quantity(Decimal(rating["num"]), "rating number", op, places=_places(rating["num"]))
    found = _QUANTITY.match(text)
    if found is None:
        return None
    number = found["num"].replace(",", "")
    multiplier = _MULTIPLIER.get((found["mult"] or "").lower(), Decimal(1))
    unit = _unit(found["unit"] or "", found["cur"] or "")
    return Quantity(
        EXACT.multiply(Decimal(number), multiplier),
        unit,
        _OPERATORS.get(found["op"] or "", ""),
        bool(found["approx"]),
        _places(number),
        multiplier,
    )


def _places(number: str) -> int:
    return len(number.partition(".")[2])


def _unit(unit: str, currency: str) -> str:
    folded = " ".join(unit.split()).lower()
    if folded.startswith("%"):
        return "% NAV" if "nav" in folded else "%"
    if folded in _UNITS:
        return _UNITS[folded]
    if folded:
        return folded.upper() if folded in ("usd", "eur", "gbp") else folded
    return {"$": "USD", "€": "EUR", "£": "GBP"}.get(currency, currency.upper())


def plain(value: Decimal) -> str:
    return f"{value:f}"


def money(value: Decimal) -> str:
    """An amount as the reader writes it: thousands separated, at most two decimals."""
    shown = value.quantize(SHOWN, rounding=ROUND_HALF_EVEN, context=EXACT)
    text = f"{shown:,.2f}"
    return text.removesuffix(".00")


def figure(value: Decimal) -> str:
    """An exact figure without trailing zeros, never in exponent form."""
    return plain(value.normalize(EXACT)) if value else "0"


def count(number: int, noun: str) -> str:
    plural = noun[:-1] + "ies" if noun.endswith("y") else noun + "s"
    return f"{number} {noun if number == 1 else plural}"


def pct(value: Decimal) -> str:
    return f"{value.quantize(SHOWN, rounding=ROUND_HALF_EVEN, context=EXACT):f}%"


def share(part: Decimal, whole: Decimal) -> Decimal:
    return EXACT.divide(EXACT.multiply(part, HUNDRED), whole) if whole else Decimal(0)


def within(stated: Quantity, exact: Decimal, *, marked: bool = False) -> bool:
    """Whether a stated figure is the exact one, allowing its rounding (and a mark at mid)."""
    allowed = stated.half_unit
    if marked:
        allowed = EXACT.add(allowed, EXACT.multiply(MARK_TOLERANCE, stated.value.copy_abs()))
    return EXACT.abs(EXACT.subtract(stated.value, exact)) <= allowed


def folded(text: str) -> str:
    return " ".join(text.casefold().split())


def rows_named(numbers: Sequence[int]) -> str:
    shown = ", ".join(str(n) for n in numbers[:LISTED])
    more = f" and {len(numbers) - LISTED} more" if len(numbers) > LISTED else ""
    return f"row{'s' if len(numbers) > 1 else ''} {shown}{more}"


# --- Reading the files ---------------------------------------------------------------------------


def csv_rows(raw: bytes) -> list[list[str]]:
    """A CSV's rows as stripped text (UTF-8, with or without a byte-order mark; else Latin-1)."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    return [[cell.strip() for cell in row] for row in csv.reader(io.StringIO(text))]


def _cells(row: Sequence[str]) -> list[str]:
    return [cell for cell in row if cell]


@dataclass(frozen=True)
class Cell:
    text: str
    numeric: bool = False
    date_format: bool = False


_DATE_CODE = re.compile(r"[dmy]", re.IGNORECASE)
_DATE_BUILTINS = frozenset({f"builtin:{n}" for n in (*range(14, 23), 45, 46, 47)})
_QUOTED = re.compile(r'"[^"]*"|\\.|\[[^\]]*\]')


def _is_date_format(code: str | None) -> bool:
    if code is None:
        return False
    if code.startswith("builtin:"):
        return code in _DATE_BUILTINS
    bare = _QUOTED.sub("", code)
    return bool(_DATE_CODE.search(bare)) and "0" not in bare


def sheet_rows(raw: bytes, name: str) -> list[tuple[int, list[Cell]]] | None:
    """A workbook sheet's rows as (row number, cells), or None when the sheet is not there."""
    grids, _ = sheet_cells(xlsx_content(raw).spans, "workbook")
    wanted = next((sheet for sheet in grids if folded(sheet) == folded(name)), None)
    if wanted is None:
        return None
    grid: Mapping[tuple[int, int], Span] = grids[wanted]
    width = max((column for column, _ in grid), default=0)
    numbers = sorted({row for _, row in grid})
    return [
        (number, [_cell(grid.get((column, number))) for column in range(1, width + 1)])
        for number in numbers
    ]


def _cell(span: Span | None) -> Cell:
    if span is None:
        return Cell("")
    numeric = span.data_type == "n"
    return Cell(span.text.strip(), numeric, numeric and _is_date_format(span.number_format))


def workbook_sheets(raw: bytes) -> tuple[str, ...]:
    try:
        grids, _ = sheet_cells(xlsx_content(raw).spans, "workbook")
    except Exception:  # noqa: BLE001 - any reader failure: not a workbook here
        return ()
    return tuple(grids)


_TEXT_DATES = ("%Y-%m-%d", "%d-%b-%Y", "%d %b %Y", "%m/%d/%Y", "%d/%m/%Y", "%b %d, %Y")
_TWO_DIGIT = re.compile(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2}$|^\d{1,2}-[A-Za-z]{3}-\d{2}$")


def read_date(cell: Cell) -> date | None:
    """A date from an Excel date cell (a serial number) or text in a full-year format."""
    from datetime import datetime

    if cell.date_format:
        try:
            return date(1899, 12, 30) + timedelta(days=int(Decimal(cell.text)))
        except (InvalidOperation, OverflowError, ValueError):
            return None
    for pattern in _TEXT_DATES:
        try:
            return datetime.strptime(cell.text, pattern).date()
        except ValueError:
            continue
    return None


def text_date(text: str) -> date | None:
    return read_date(Cell(text))


# --- The files' roles ----------------------------------------------------------------------------

_MANDATE_HEADER = ["section", "field", "value"]
_SECTION_KEYS = (
    ("sectors", ("sector", "industr")),
    ("ratings", ("rating",)),
    ("maturity", ("maturit",)),
    ("holdings", ("holding", "issuer", "obligor", "top 10", "top10")),
    ("summary", ("summary", "metric", "overview")),
)
_HOLDING_COLUMNS: Mapping[str, tuple[str, ...]] = {
    "ticker": ("ticker",),
    "borrower": ("borrower", "issuer name", "obligor"),
    "sector": ("index sector", "sector", "industry"),
    "loan": ("loan name", "loan", "facility"),
    "figi": ("figi",),
    "ranking": ("ranking", "seniority", "lien"),
    "ratings": ("rating",),
    "margin": ("margin", "spread"),
    "maturity": ("maturity",),
    "bid": ("bid",),
    "ask": ("ask", "offer"),
    "ytm": ("ytm", "yield"),
    "dm": ("dm", "discount margin"),
    "size": ("size",),
    "change_1m": ("δ 1m", "1m"),
    "change_ytd": ("δ ytd", "ytd"),
    "par": ("holdings", "par", "position", "quantity"),
}
_REQUIRED_HOLDING = ("borrower", "sector", "par", "bid", "ask")


def _first_row(rows: Sequence[Sequence[str]]) -> list[str]:
    return next((list(row) for row in rows if _cells(row)), [])


def is_mandate(rows: Sequence[Sequence[str]]) -> bool:
    return [folded(cell) for cell in _first_row(rows)[:3]] == _MANDATE_HEADER


def is_constraints(rows: Sequence[Sequence[str]]) -> bool:
    """A header with Parameter, a Limit column (`Limit`, `Limit / Guideline`) and a current figure
    (`Current Value`, `Current Exposure`)."""
    header = [folded(cell) for cell in _first_row(rows)]
    return (
        "parameter" in header
        and any("limit" in h for h in header)
        and any("current" in h or "exposure" in h for h in header)
    )


def section_key(title: str) -> str | None:
    text = folded(title)
    return next((key for key, words in _SECTION_KEYS if any(w in text for w in words)), None)


def _is_title(row: Sequence[str]) -> bool:
    filled = _cells(row)
    return len(filled) == 1 and bool(row) and row[0] == filled[0]


def is_exposure(rows: Sequence[Sequence[str]]) -> bool:
    keys = {section_key(row[0]) for row in rows if _is_title(row)}
    return len(keys - {None}) >= 2


def column_index(header: Sequence[str], words: Iterable[str], skip: int = -1) -> int | None:
    """The first header (after `skip`) holding one of `words`, in the order `words` gives."""
    names = [folded(cell) for cell in header]
    for word in words:
        for index, name in enumerate(names):
            if index > skip and word in name and not (word == "sector" and "sub" in name):
                return index
    return None


def holdings_header(rows: Sequence[tuple[int, list[Cell]]]) -> tuple[int, dict[str, int]] | None:
    """The header row's number and the column of each known holdings field."""
    for number, cells in rows:
        texts = [cell.text for cell in cells]
        if sum(1 for text in texts if text) < 5:
            continue
        columns = {
            key: index
            for key, words in _HOLDING_COLUMNS.items()
            if (index := column_index(texts, words)) is not None
        }
        if "borrower" in columns:
            return number, columns
    return None


# --- The parsed export ---------------------------------------------------------------------------


@dataclass
class Holding:
    row: int
    sheet: str
    text: dict[str, str]
    cells: dict[str, Cell]
    numbers: dict[str, Decimal] = field(default_factory=dict)
    maturity: date | None = None


@dataclass
class Section:
    key: str
    title: str
    header: list[str]
    rows: list[tuple[int, list[str]]]


@dataclass
class Export:
    """The recognised files: each role's file name, rows and parsed content."""

    files: dict[str, str] = field(default_factory=dict)  # role -> the first part's label
    roles: dict[str, str] = field(default_factory=dict)  # part label -> role, every part
    mandate: list[tuple[int, list[str]]] = field(default_factory=list)
    constraints: list[tuple[str, list[tuple[int, list[str]]], list[str]]] = field(
        default_factory=list
    )  # (file, rows, header) for each constraints file
    sections: dict[str, Section] = field(default_factory=dict)
    holdings: list[Holding] = field(default_factory=list)
    market: list[Holding] = field(default_factory=list)
    holding_columns: dict[str, int] = field(default_factory=dict)
    book: str = ""  # the workbook that holds the holdings
    empty_rows: dict[str, list[int]] = field(default_factory=dict)  # sheet -> row numbers


@dataclass(frozen=True)
class Part:
    """One recognised part of the export: a CSV file, or one sheet of a workbook."""

    file: str
    sheet: str | None
    role: str
    rows: tuple[tuple[int, tuple[str, ...]], ...] = ()  # (row number, cells)

    @property
    def label(self) -> str:
        return self.file if self.sheet is None else f"{self.file} [{self.sheet}]"


def _role(rows: Sequence[Sequence[str]]) -> str | None:
    if is_mandate(rows):
        return "mandate"
    if is_constraints(rows):
        return "constraints"
    return "exposure" if is_exposure(rows) else None


def _text(cell: Cell) -> str:
    """A workbook cell as the CSV export would write it: a date cell as its ISO date."""
    if cell.date_format:
        when = read_date(cell)
        return when.isoformat() if when is not None else cell.text
    return cell.text


def _workbook_parts(name: str, raw: bytes) -> list[Part]:
    found: list[Part] = []
    for sheet in workbook_sheets(raw):
        rows = sheet_rows(raw, sheet) or []
        if folded(sheet) in ("holdings", "market data") or (
            (header := holdings_header(rows)) is not None and "par" in header[1]
        ):
            kind = "market" if folded(sheet) == "market data" else "holdings"
            found.append(Part(name, sheet, kind))
            continue
        texts = [[_text(cell) for cell in cells] for _, cells in rows]
        if (role := _role(texts)) is not None:
            numbered = tuple((n, tuple(r)) for (n, _), r in zip(rows, texts, strict=True))
            found.append(Part(name, sheet, role, numbered))
    return found


def parts(files: Mapping[str, bytes]) -> list[Part]:
    """Every recognised part, CSV files and workbook sheets alike, in file order. A workbook's
    `Holdings` sheet (or any sheet whose header has a borrower and a par column) is the holdings;
    its `Market Data` sheet the quote universe."""
    found: list[Part] = []
    for name in sorted(files):
        raw, lower = files[name], name.lower()
        if lower.endswith(".csv"):
            rows = csv_rows(raw)
            if (role := _role(rows)) is not None:
                numbered = tuple((n, tuple(r)) for n, r in enumerate(rows, 1))
                found.append(Part(name, None, role, numbered))
        elif lower.endswith(".xlsx"):
            found += _workbook_parts(name, raw)
    return found


def recognise(files: Mapping[str, bytes]) -> dict[str, str]:
    """The files that hold a part of the export, with their parts' roles."""
    roles: dict[str, list[str]] = {}
    for part in parts(files):
        if part.role != "market":
            roles.setdefault(part.file, []).append(part.role)
    return {name: ", ".join(found) for name, found in roles.items()}


def sections(rows: Sequence[tuple[int, Sequence[str]]]) -> dict[str, Section]:
    """The exposure report's stacked sections: a title row, a header row, then data rows."""
    found: dict[str, Section] = {}
    current: Section | None = None
    for number, row in rows:
        if not _cells(row):
            continue
        if _is_title(row) and (key := section_key(row[0])) is not None:
            current = Section(key, row[0], [], [])
            found.setdefault(key, current)
        elif current is not None and not current.header:
            current.header = list(row)
        elif current is not None:
            current.rows.append((number, list(row)))
    return found


def _holding(sheet: str, number: int, cells: list[Cell], columns: Mapping[str, int]) -> Holding:
    picked = {
        key: cells[index] if index < len(cells) else Cell("") for key, index in columns.items()
    }
    return Holding(number, sheet, {key: cell.text for key, cell in picked.items()}, picked)


def holding_rows(raw: bytes, sheet: str, export: Export) -> list[Holding]:
    """The rows under the header of `sheet`; rows of empty cells are counted, not read."""
    rows = sheet_rows(raw, sheet)
    if rows is None:
        return []
    header = holdings_header(rows)
    if header is None:
        return []
    start, columns = header
    if "par" in columns:
        export.holding_columns = dict(columns)
    out: list[Holding] = []
    for number, cells in rows:
        if number <= start:
            continue
        if not any(cell.text for cell in cells):
            export.empty_rows.setdefault(sheet, []).append(number)
            continue
        out.append(_holding(sheet, number, cells, columns))
    return out


def read_export(files: Mapping[str, bytes]) -> Export:
    export = Export()
    for part in parts(files):
        export.roles[part.label] = part.role
        if part.role == "market":
            export.market = holding_rows(files[part.file], part.sheet or "", export)
            continue
        export.files.setdefault(part.role, part.label)
        rows = [(number, list(row)) for number, row in part.rows]
        if part.role == "mandate":
            export.mandate = rows
        elif part.role == "constraints":
            header = next(row for _, row in rows if _cells(row))
            export.constraints.append((part.label, rows, header))
        elif part.role == "exposure":
            export.sections = sections(rows)
        else:
            export.book = part.file
            export.holdings = holding_rows(files[part.file], part.sheet or "", export)
    return export


# --- Findings ------------------------------------------------------------------------------------


# The order findings are reported in, most consequential first: a limit breached on the holdings'
# figures that the report passes; stated figures that do not reconcile to the holdings (or a file
# that cannot be read); the report's own inconsistencies (totals, headroom, status, the capital
# structure, two files that disagree); cell defects (3, the default); then staleness.
PRIORITY: Mapping[str, int] = {
    "breach": 0,
    **dict.fromkeys(
        ("par", "nav", "count", "share", "absent", "metric", "missing", "layout", "column"), 1
    ),
    **dict.fromkeys(("total", "capital", "headroom", "status", "plausible", "differs"), 2),
    **dict.fromkeys(("stale", "future"), 4),
}


@dataclass
class Findings:
    issues: list[tuple[int, Issue]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    table: list[tuple[str, str, str, str]] = field(default_factory=list)

    def add(self, file: str, where: str, cell: str, problem: str, fix: str) -> None:
        issue = Issue(file=file, sheet=where, cell=cell, problem=problem, fix=FIX[fix])
        self.issues.append((PRIORITY.get(fix, 3), issue))

    def ordered(self) -> tuple[Issue, ...]:
        return tuple(issue for _, issue in sorted(self.issues, key=lambda item: item[0]))


class ExportReport(ValidationReport):
    """`files`: each recognised file and its role. `recomputed`: what the holdings give, as lines a
    reader can quote. `notes`: what was read but is not a defect (watch flags, withdrawn ratings,
    figures the check does not recompute)."""

    files: tuple[tuple[str, str], ...] = ()
    recomputed: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    table: tuple[tuple[str, str, str, str], ...] = ()

    @property
    def sources(self) -> tuple[str, ...]:
        """The file names the parts come from, each once."""
        return tuple(dict.fromkeys(label.split(" [")[0] for label, _ in self.files))

    def lines(self) -> tuple[str, ...]:
        summary = (
            f"OK: {len(self.files)} parts, {self.rows} holdings"
            if self.ok
            else f"FAILED: {len(self.issues)} issues"
        )
        return (*(render(issue) for issue in self.issues), summary)

    def table_lines(self) -> tuple[str, ...]:
        """The headline figures, stated against the holdings, as an aligned table."""
        if not self.table:
            return ()
        rows = [("figure", "stated", "holdings", "difference"), *self.table]
        widths = [max(len(row[i]) for row in rows) for i in range(4)]
        out = ["Reconciliation, stated against the holdings:"]
        out += [
            "  " + "  ".join(c.ljust(w) for c, w in zip(row, widths, strict=True)).rstrip()
            for row in rows
        ]
        return tuple(out)


def render(issue: Issue) -> str:
    """One export finding on one line, as `Issue.render` writes a workbook's: file, part and row,
    what is wrong and the fix, with control characters escaped."""
    line = f"{issue.file}, {issue.sheet}, {issue.cell}: {issue.problem} — fix: {issue.fix}"
    return "".join(
        char if char.isprintable() else char.encode("unicode_escape").decode("ascii")
        for char in line
    )


# --- Typed holdings ------------------------------------------------------------------------------

_NUMERIC = ("par", "bid", "ask", "margin", "ytm", "dm", "change_1m", "change_ytd", "size")


@dataclass
class Tally:
    """Per column, the rows with a vendor error token and the rows that cannot be read."""

    tokens: dict[str, list[int]] = field(default_factory=dict)
    unreadable: dict[str, list[int]] = field(default_factory=dict)


def type_rows(rows: Sequence[Holding]) -> dict[str, Tally]:
    """Read each row's numbers and maturity; per sheet, the cells that could not be read."""
    tallies: dict[str, Tally] = {}
    for holding in rows:
        tally = tallies.setdefault(holding.sheet, Tally())
        for key in _NUMERIC:
            text = holding.text.get(key, "")
            if not text:
                continue
            if TOKEN.match(text):
                tally.tokens.setdefault(key, []).append(holding.row)
                continue
            found = quantity(text)
            if found is None or found.approximate:
                tally.unreadable.setdefault(key, []).append(holding.row)
            else:
                holding.numbers[key] = found.value
        cell = holding.cells.get("maturity")
        if cell is not None and cell.text and not TOKEN.match(cell.text):
            holding.maturity = read_date(cell)
            if holding.maturity is None:
                tally.unreadable.setdefault("maturity", []).append(holding.row)
    return tallies


def mid(holding: Holding) -> Decimal | None:
    if "bid" in holding.numbers and "ask" in holding.numbers:
        return EXACT.divide(EXACT.add(holding.numbers["bid"], holding.numbers["ask"]), Decimal(2))
    return None


_LIEN = re.compile(r"^\s*([12])\s*L\b", re.IGNORECASE)


def lien(holding: Holding) -> str:
    """first, second, unsecured or unclassified: the leading lien token of Ranking (`1L Sr.
    Secd`, `2L Secd`), else the words first/second lien or unsecured. A Ranking with none of
    these is unclassified and reported, never counted as first lien."""
    text = holding.text.get("ranking", "")
    if (token := _LIEN.match(text)) is not None:
        return "first" if token[1] == "1" else "second"
    words = folded(text)
    if "2nd lien" in words or "second lien" in words:
        return "second"
    if "1st lien" in words or "first lien" in words:
        return "first"
    return "unsecured" if "unsec" in words else "unclassified"


@dataclass
class Recomputed:
    """What the holdings give. Shares are of `value`, the market value of the priced positions."""

    positions: int = 0
    par: Decimal = Decimal(0)
    priced_par: Decimal = Decimal(0)
    value: Decimal = Decimal(0)
    unpriced: list[Holding] = field(default_factory=list)
    borrowers: dict[str, list[Holding]] = field(default_factory=dict)
    tickers: set[str] = field(default_factory=set)
    sectors: dict[str, Decimal] = field(default_factory=dict)
    issuer_value: dict[str, Decimal] = field(default_factory=dict)
    second_lien: Decimal = Decimal(0)
    price: Decimal | None = None
    margin: Decimal | None = None
    ytm: Decimal | None = None
    ytm_all: Decimal | None = None
    names: dict[str, str] = field(default_factory=dict)  # folded borrower -> as written
    tickers_of: dict[str, set[str]] = field(default_factory=dict)  # folded borrower -> tickers
    sheet: str = "Holdings"
    left_out: int = 0  # holdings rows with no readable par

    def issuer_share(self, name: str) -> Decimal:
        return share(self.issuer_value.get(folded(name), Decimal(0)), self.value)

    def largest_issuer(self) -> tuple[str, Decimal]:
        name = max(self.issuer_value, key=lambda key: self.issuer_value[key], default="")
        return self.names.get(name, name), self.issuer_share(name) if name else Decimal(0)

    def top_ten(self) -> Decimal:
        top = sorted(self.issuer_value.values(), reverse=True)[:10]
        return share(sum(top, Decimal(0)), self.value)


def _weighted(rows: Iterable[tuple[Decimal, Decimal]]) -> Decimal | None:
    pairs = list(rows)
    weight = sum((w for w, _ in pairs), Decimal(0))
    if not weight:
        return None
    return EXACT.divide(sum((EXACT.multiply(w, v) for w, v in pairs), Decimal(0)), weight)


def recompute(rows: Sequence[Holding]) -> Recomputed:
    out = Recomputed(sheet=rows[0].sheet if rows else "Holdings")
    priced: list[tuple[Decimal, Decimal]] = []
    for holding in rows:
        par = holding.numbers.get("par")
        if par is None:
            out.left_out += 1
            continue
        out.positions += 1
        out.par = EXACT.add(out.par, par)
        key = folded(holding.text.get("borrower", ""))
        out.names.setdefault(key, holding.text.get("borrower", ""))
        out.borrowers.setdefault(key, []).append(holding)
        if holding.text.get("ticker"):
            out.tickers.add(holding.text["ticker"])
            out.tickers_of.setdefault(key, set()).add(holding.text["ticker"].upper())
        sector = holding.text.get("sector", "")
        price = mid(holding)
        if price is None:
            out.unpriced.append(holding)
            out.sectors.setdefault(sector, Decimal(0))
            continue
        value = EXACT.divide(EXACT.multiply(par, price), HUNDRED)
        priced.append((par, price))
        out.priced_par = EXACT.add(out.priced_par, par)
        out.value = EXACT.add(out.value, value)
        out.sectors[sector] = EXACT.add(out.sectors.get(sector, Decimal(0)), value)
        out.issuer_value[key] = EXACT.add(out.issuer_value.get(key, Decimal(0)), value)
        if lien(holding) == "second":
            out.second_lien = EXACT.add(out.second_lien, value)
    out.price = _weighted(priced)
    _averages(rows, out)
    return out


def _averages(rows: Sequence[Holding], out: Recomputed) -> None:
    held = [h for h in rows if "par" in h.numbers]
    out.margin = _weighted(
        (h.numbers["par"], h.numbers["margin"]) for h in held if "margin" in h.numbers
    )
    with_ytm = [(h.numbers["par"], h.numbers["ytm"]) for h in held if "ytm" in h.numbers]
    low, high = YTM_RANGE
    out.ytm_all = _weighted(with_ytm)
    out.ytm = _weighted((w, v) for w, v in with_ytm if low <= v <= high)


def recomputed_lines(found: Recomputed) -> tuple[str, ...]:
    """What the holdings give, as plain sentences a module can quote with their basis."""
    lines = [
        f"positions with a par: {found.positions}; par {money(found.par)}",
        (
            f"market value at mid of the {found.positions - len(found.unpriced)} priced positions: "
            f"{money(found.value)}"
        ),
        (
            f"borrowers: {len(found.borrowers)}; tickers: {len(found.tickers)}; sectors: "
            f"{len(found.sectors)}"
        ),
    ]
    if found.unpriced:
        par = sum((h.numbers["par"] for h in found.unpriced), Decimal(0))
        lines.append(f"positions with no price: {len(found.unpriced)}, par {money(par)}")
    if found.value:
        name, largest = found.largest_issuer()
        lines += [
            f"largest borrower: {name}, {pct(largest)} of market value",
            f"ten largest borrowers: {pct(found.top_ten())} of market value",
            f"second lien: {pct(share(found.second_lien, found.value))} of market value",
        ]
    for label, value, unit in (
        ("par-weighted mid price", found.price, ""),
        ("par-weighted margin", found.margin, " bps"),
        ("par-weighted yield to maturity, values outside -10% to 100% left out", found.ytm, "%"),
    ):
        if value is not None:
            lines.append(f"{label}: {plain(value.quantize(SHOWN, context=EXACT))}{unit}")
    return tuple(lines)


# --- Row checks: holdings and market data --------------------------------------------------------

_COLUMN_NAME = {
    "par": "Holdings (par)",
    "bid": "Bid",
    "ask": "Ask",
    "margin": "Margin",
    "ytm": "Mid YTM",
    "dm": "Mid 3Y DM",
    "maturity": "Maturity",
    "change_1m": "Δ 1M",
    "size": "Size ($Mn)",
    "change_ytd": "Δ YTD",
}


def tally_findings(
    file: str, sheet: str, tally: Tally, findings: Findings, par_of: Mapping[int, Decimal]
) -> None:
    """A column's error tokens and unreadable cells (par has its own finding, `par_findings`),
    with the par of the positions a missing price leaves out of the market value."""
    for key, numbers in tally.tokens.items():
        if key == "par":
            continue
        affected = sum((par_of.get(n, Decimal(0)) for n in numbers), Decimal(0))
        priced = f"; par affected {money(affected)}" if key in ("bid", "ask") and affected else ""
        problem = (
            f"{_COLUMN_NAME.get(key, key)} holds a vendor error token such as #N/A N/A on "
            f"{rows_named(numbers)}; read as missing, never as zero{priced}"
        )
        findings.add(file, sheet, _COLUMN_NAME.get(key, key), problem, "token")
    for key, numbers in tally.unreadable.items():
        if key == "par":
            continue
        problem = (
            f"{_COLUMN_NAME.get(key, key)} cannot be read as a number or date with its unit on "
            f"{rows_named(numbers)}; not coerced"
        )
        findings.add(file, sheet, _COLUMN_NAME.get(key, key), problem, "unit")


def date_findings(
    file: str, rows: Sequence[Holding], as_of: date | None, findings: Findings
) -> None:
    by_sheet: dict[str, list[Holding]] = {}
    for holding in rows:
        by_sheet.setdefault(holding.sheet, []).append(holding)
    for sheet, held in by_sheet.items():
        dated = [h for h in held if h.maturity is not None]
        old = [h for h in dated if h.maturity is not None and h.maturity.year < CENTURY]
        if old:
            years = sorted({h.maturity.year for h in old if h.maturity is not None})
            span = str(years[0]) if len(years) == 1 else f"{years[0]} to {years[-1]}"
            problem = (
                f"{len(old)} of {len(dated)} maturities {'falls' if len(old) == 1 else 'fall'} "
                f"in {span} "
                f"({rows_named([h.row for h in old])}): two-digit years read as 19xx"
            )
            findings.add(file, sheet, "Maturity", problem, "century")
        if as_of is not None:
            matured = [
                h
                for h in dated
                if h.maturity is not None and CENTURY <= h.maturity.year and h.maturity < as_of
            ]
            if matured:
                problem = (
                    f"{len(matured)} maturities fall before the as-of date {as_of} "
                    f"({rows_named([h.row for h in matured])}): matured positions"
                )
                findings.add(file, sheet, "Maturity", problem, "matured")


def range_findings(
    file: str, rows: Sequence[Holding], found: Recomputed, findings: Findings
) -> None:
    for key, (low, high), unit in (("ytm", YTM_RANGE, "%"), ("dm", DM_RANGE, " bps")):
        for sheet in dict.fromkeys(h.sheet for h in rows):
            bad = [
                h
                for h in rows
                if h.sheet == sheet and key in h.numbers and not low <= h.numbers[key] <= high
            ]
            if not bad:
                continue
            values = sorted(h.numbers[key] for h in bad)
            seen = ", ".join(dict.fromkeys(f"{plain(v)}{unit}" for v in (values[0], values[-1])))
            problem = (
                f"{_COLUMN_NAME[key]} lies outside {plain(low)}{unit} to {plain(high)}{unit} on "
                f"{rows_named([h.row for h in bad])} ({'from ' if len(values) > 1 else ''}"
                f"{seen.replace(', ', ' to ')})"
            )
            if key == "ytm" and sheet == found.sheet and found.ytm_all is not None:
                problem += (
                    f"; with them the par-weighted yield is {pct(found.ytm_all)}, without them "
                    f"{pct(found.ytm) if found.ytm is not None else 'not computable'}"
                )
            findings.add(file, sheet, _COLUMN_NAME[key], problem, "range")


def identifier_findings(file: str, rows: Sequence[Holding], findings: Findings) -> None:
    for sheet in dict.fromkeys(h.sheet for h in rows):
        held = [h for h in rows if h.sheet == sheet]
        _figi_findings(file, sheet, held, findings)
        _ticker_findings(file, sheet, held, findings)
        _name_findings(file, sheet, held, findings)


def _figi_findings(file: str, sheet: str, rows: Sequence[Holding], findings: Findings) -> None:
    wrong = [h for h in rows if h.text.get("figi") and not FIGI.match(h.text["figi"])]
    if wrong:
        verb = "is" if len(wrong) == 1 else "are"
        problem = (
            f"{count(len(wrong), 'FIGI')} {verb} not 12 capital letters and digits "
            f"({rows_named([h.row for h in wrong])})"
        )
        findings.add(file, sheet, "FIGI", problem, "figi")
    used: dict[str, list[Holding]] = {}
    for holding in rows:
        if holding.text.get("figi"):
            used.setdefault(holding.text["figi"], []).append(holding)
    for figi, held in used.items():
        if len(held) < 2:
            continue
        loans = {folded(h.text.get("loan", "")) for h in held}
        borrowers = {folded(h.text.get("borrower", "")) for h in held}
        what = (
            "different borrowers"
            if len(borrowers) > 1
            else "different loans"
            if len(loans) > 1
            else "the same loan twice"
        )
        problem = f"FIGI {figi} is used on {rows_named([h.row for h in held])}, for {what}"
        findings.add(file, sheet, "FIGI", problem, "figi_reuse")


def _ticker_findings(file: str, sheet: str, rows: Sequence[Holding], findings: Findings) -> None:
    names: dict[str, dict[str, int]] = {}
    for holding in rows:
        ticker, name = holding.text.get("ticker", ""), holding.text.get("borrower", "")
        if ticker and name:
            names.setdefault(ticker, {}).setdefault(name, holding.row)
    for ticker, borrowers in names.items():
        if len(borrowers) > 1:
            listed = "; ".join(f"{name} (row {row})" for name, row in borrowers.items())
            problem = f"ticker {ticker} names {len(borrowers)} borrowers: {listed}"
            findings.add(file, sheet, "Ticker", problem, "ticker")


def _name_findings(file: str, sheet: str, rows: Sequence[Holding], findings: Findings) -> None:
    for holding in rows:
        name = holding.text.get("borrower", "")
        if MOJIBAKE.search(name):
            shown = name.encode("unicode_escape").decode("ascii")
            problem = f"borrower name '{shown}' on row {holding.row} holds damaged characters"
            findings.add(file, sheet, "Borrower Name", problem, "name")
        ranking = holding.text.get("ranking", "")
        if ranking and RATING_LIKE.match(ranking):
            problem = f"Ranking on row {holding.row} holds a rating, '{ranking}'"
            findings.add(file, sheet, "Ranking", problem, "ranking")


def rating_findings(file: str, rows: Sequence[Holding], findings: Findings) -> None:
    missing: list[int] = []
    withdrawn: list[int] = []
    watch: list[int] = []
    for holding in rows:
        parts = [part.strip() for part in _AGENCIES.split(holding.text.get("ratings", ""))]
        if any(TOKEN.match(part) for part in parts if part):
            missing.append(holding.row)
        if any(part.upper() in WITHDRAWN for part in parts):
            withdrawn.append(holding.row)
        if any("*" in part for part in parts):
            watch.append(holding.row)
    sheet = rows[0].sheet if rows else "Holdings"
    if missing:
        problem = f"Ratings holds a vendor error token for an agency on {rows_named(missing)}"
        findings.add(file, sheet, "Ratings", problem, "token")
    if withdrawn:
        findings.notes.append(
            f"{sheet}: ratings withdrawn or not rated (WR, NR) on {rows_named(withdrawn)}; read as "
            "unrated"
        )
    if watch:
        findings.notes.append(
            f"{sheet}: ratings with a watch flag (*+, *-) on {rows_named(watch)}; read without the "
            "flag"
        )


def lien_findings(file: str, rows: Sequence[Holding], findings: Findings) -> None:
    """Positions whose Ranking states no lien: not classified, and left out of the lien split."""
    lacking = [h.row for h in rows if lien(h) == "unclassified"]
    if lacking:
        problem = (
            f"Ranking states no lien (1L, 2L, first, second, unsecured) on {rows_named(lacking)}; "
            "not classified, and not counted as first lien"
        )
        findings.add(file, rows[0].sheet, "Ranking", problem, "lien")


def par_findings(file: str, rows: Sequence[Holding], findings: Findings) -> None:
    lacking = [h.row for h in rows if "par" not in h.numbers]
    if lacking:
        problem = (
            f"positions without a readable par, left out of every recomputed figure: "
            f"{len(lacking)} ({rows_named(lacking)}; an error token, an unreadable value or an "
            "empty cell)"
        )
        findings.add(file, rows[0].sheet, "Holdings (par)", problem, "par_cell")


def empty_row_findings(file: str, export: Export, findings: Findings) -> None:
    for sheet, numbers in export.empty_rows.items():
        problem = (
            f"rows below the header with only empty cells: {len(numbers)} ({rows_named(numbers)})"
        )
        findings.add(file, sheet, "rows", problem, "empty_rows")


# --- The report against the holdings -------------------------------------------------------------

_METRICS = (
    ("second_lien", ("2nd lien", "second lien")),
    ("first_lien", ("1st lien", "first lien")),
    ("wal", ("wal", "weighted average life", "average life")),
    ("top10", ("top 10", "top10", "top ten")),
    ("largest", ("largest issuer", "largest obligor", "largest borrower", "single issuer")),
    ("largest_sector", ("single sector", "largest sector")),
    ("positions", ("position", "number of loans", "facilities")),
    ("obligors", ("obligor", "issuers", "borrowers")),
    ("sectors", ("sector",)),
    ("price", ("price",)),
    ("ytm", ("ytm", "yield")),
    ("margin", ("margin", "spread")),
    ("par", ("par",)),
    ("nav", ("nav", "net asset", "collateral")),
)


_COUNT, _AMOUNT, _SHARE = (
    frozenset({""}),
    frozenset({"", "USD", "EUR", "GBP"}),
    frozenset({"%", "% NAV"}),
)
# The unit each metric is stated in; a metric named like one but in another unit is not that
# metric (e.g. "Sector Concentration 12%" is no sector count) and is listed as not checked.
_METRIC_UNITS: Mapping[str, frozenset[str]] = {
    "positions": _COUNT,
    "obligors": _COUNT,
    "sectors": _COUNT,
    "par": _AMOUNT,
    "nav": _AMOUNT,
    "price": frozenset({""}),
    "margin": frozenset({"", "bps"}),
    "ytm": _SHARE,
    "second_lien": _SHARE,
    "first_lien": _SHARE,
    "wal": frozenset({"yrs"}),
    "largest": _SHARE,
    "largest_sector": _SHARE,
    "top10": _SHARE,
}


_COUNT_KEYS = frozenset({"positions", "obligors", "sectors"})


def _fits(key: str, found: Quantity) -> bool:
    """Whether a stated figure is in the unit its metric is stated in; counts are whole."""
    integral = found.value == found.value.to_integral_value(context=EXACT)
    return found.unit in _METRIC_UNITS[key] and (key not in _COUNT_KEYS or integral)


_NAME_UNIT = (("(yrs)", "yrs"), ("(years)", "yrs"), ("(bps)", "bps"), ("(%)", "%"), ("%", "%"))


def _unit_from_name(name: str, found: Quantity) -> Quantity:
    """A bare figure takes the unit its metric's name states: `Weighted Average Life (yrs)` =
    `4.82` is 4.82 yrs."""
    if found.unit:
        return found
    text = folded(name)
    unit = next((unit for mark, unit in _NAME_UNIT if mark in text), "")
    return replace(found, unit=unit) if unit else found


def metric_key(name: str) -> str | None:
    text = folded(name)
    return next((key for key, words in _METRICS if any(w in text for w in words)), None)


@dataclass
class Claim:
    """A figure the report states: where it is, how it is written, and what it reads as."""

    where: str
    cell: str
    text: str
    value: Quantity
    name: str = ""  # the issuer or sector a `<name> (2.37%)` cell names


_NAME_AND_FIGURE = re.compile(r"^(?P<name>.*?\S)\s*\((?P<figure>[^()]+)\)\s*$")


def summary_claims(export: Export, findings: Findings) -> tuple[dict[str, Claim], list[str]]:
    section = export.sections.get("summary")
    claims: dict[str, Claim] = {}
    unchecked: list[str] = []
    if section is None:
        return claims, unchecked
    where = f"{section.title}"
    for number, row in section.rows:
        name, text = row[0], row[1] if len(row) > 1 else ""
        key = metric_key(name)
        found, named = quantity(text), ""
        if found is None and (pair := _NAME_AND_FIGURE.match(text)) is not None:
            found, named = quantity(pair["figure"]), pair["name"].strip()
        if found is not None:
            found = _unit_from_name(name, found)
        if any(word in folded(name) for word in _AS_OF_FIELDS):
            continue
        if key is None or key in claims or (found is not None and not _fits(key, found)):
            unchecked.append(f"{name} ({text})")
        elif found is None or found.approximate:
            _unreadable((export.files["exposure"], where, f"row {number}"), name, text, findings)
        else:
            claims[key] = Claim(where, f"row {number}", text, found, named)
    return claims, unchecked


def _unreadable(place: tuple[str, str, str], name: str, text: str, findings: Findings) -> None:
    """A stated figure that cannot be read with its unit, at (file, part, cell)."""
    approximate = text.strip().startswith("~")
    problem = (
        f"{name} '{text}' is approximate; it is not read as an exact figure"
        if approximate
        else f"{name} '{text}' cannot be read as a figure with its unit; not coerced"
    )
    findings.add(*place, problem, "approximate" if approximate else "unit")


def _claim_finding(
    file: str, claim: Claim, label: str, exact: Decimal, findings: Findings, **how: object
) -> None:
    """One stated figure against the holdings' figure; `how` holds `marked`, `fix`, `shown`
    (a formatter) and `note` (words after the figures)."""
    marked = bool(how.get("marked", False))
    shown = how.get("shown", figure)
    assert callable(shown)
    places = claim.value.places + 2

    def show(value: Decimal) -> str:
        return _to_places(shown, value, places)

    gap = EXACT.abs(EXACT.subtract(claim.value.value, exact))
    if how.get("table"):
        findings.table.append((str(how["table"]), claim.text, show(exact), show(gap)))
    if within(claim.value, exact, marked=marked):
        return
    problem = (
        f"{label} is stated as {claim.text}; the holdings give {show(exact)}, a difference of "
        f"{show(gap)}{how.get('note', '')}"
    )
    findings.add(file, claim.where, claim.cell, problem, str(how.get("fix", "metric")))


def _to_places(shown: Callable[[Decimal], str], value: Decimal, places: int) -> str:
    """A recomputed figure (or a difference) to the stated figure's places plus two: a share,
    a plain figure or years at `places`; amounts and counts as they are written."""
    fixed = plain(
        value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN, context=EXACT)
    )
    if shown is pct:
        return f"{fixed}%"
    if shown is _years:
        return f"{fixed} yrs"
    return fixed if shown is figure else shown(value)


def _count(value: Decimal) -> str:
    return f"{value:,.0f}"


def summary_findings(
    export: Export,
    claims: Mapping[str, Claim],
    found: Recomputed,
    shape: Profile,
    findings: Findings,
) -> None:
    file = export.files["exposure"]
    for key, label, exact, how in _headline(found, shape):
        if exact is None or (not found.value and key not in _COUNTED):
            continue
        if key in claims:
            _claim_finding(file, claims[key], label, exact, findings, **how)
        elif "table" in how:
            shown = how.get("shown", figure)
            assert callable(shown)
            row = stated_in_constraints(export, key, (found, shape)) or (
                str(how["table"]),
                "not stated",
                _to_places(shown, exact, 2),
                "",
            )
            findings.table.append(row)
    _sector_table(export, found, findings)
    _named_largest(file, claims, found, findings)
    _internal_findings(file, claims, findings)


def _sector_table(export: Export, found: Recomputed, findings: Findings) -> None:
    """The three largest sectors in the holdings, each beside the share the report's sector
    section states for it (or "not listed")."""
    section = export.sections.get("sectors")
    stated: dict[str, str] = {}
    if section is not None:
        columns = section_columns(section.header)
        for _, row in section.rows:
            stated[folded(label_of(row, columns))] = _cell_text(row, columns.pct)
    for rank, name in enumerate(_sectors_ranked(found)[:3], 1):
        exact = share(found.sectors[name], found.value)
        text = stated.get(folded(name), "")
        given = quantity(text) if text else None
        places = given.places + 2 if given is not None else 2
        gap = (
            ""
            if given is None
            else _to_places(pct, EXACT.abs(EXACT.subtract(given.value, exact)), places)
        )
        findings.table.append(
            (
                f"{_ordinal(rank)}largest sector: {name}",
                text or "not listed",
                _to_places(pct, exact, places),
                gap,
            )
        )


def _named_largest(
    file: str, claims: Mapping[str, Claim], found: Recomputed, findings: Findings
) -> None:
    """The issuer or sector a summary cell names as the largest (`<name> (2.37%)`) against the
    holdings' largest."""
    issuer = claims.get("largest")
    if issuer is not None and issuer.name:
        problem = _issuer_named(issuer.name, found)
        if problem:
            findings.add(file, issuer.where, issuer.cell, f"the summary {problem}", "share")
    sector = claims.get("largest_sector")
    ranked = _sectors_ranked(found)
    if sector is not None and sector.name and ranked and folded(ranked[0]) != folded(sector.name):
        top = ranked[0]
        problem = (
            f"the summary names {sector.name} as the largest sector; in the holdings it is "
            f"{top} ({pct(share(found.sectors[top], found.value))})"
        )
        findings.add(file, sector.where, sector.cell, problem, "share")


_COUNTED = ("par", "positions", "obligors", "sectors")


def _years(value: Decimal) -> str:
    return f"{plain(value.quantize(SHOWN, context=EXACT))} yrs"


def _of_rows(found: Recomputed) -> str:
    rows = f"{found.positions:,} of {count(found.positions + found.left_out, 'row')}"
    return f"{rows}; {found.left_out:,} left out" if found.left_out else rows


def _yield_note(found: Recomputed) -> str:
    if found.ytm is None or found.ytm_all is None or found.ytm == found.ytm_all:
        return ""
    return f"; without the values outside -10% to 100% it would be {pct(found.ytm)} (not applied)"


def _life_note(shape: Profile) -> str:
    if not shape.centuries or shape.life_corrected is None:
        return ""
    fixed = plain(shape.life_corrected.quantize(SHOWN, context=EXACT))
    return (
        f"; with the {count(shape.centuries, 'maturity')} before 1950 read as 20xx it would be "
        f"{fixed} yrs (not applied)"
    )


def _headline(
    found: Recomputed, shape: Profile
) -> tuple[tuple[str, str, Decimal | None, dict[str, object]], ...]:
    """Each headline figure: its summary key, its words, the holdings' figure and how to show it."""
    name, largest = found.largest_issuer()
    unpriced = (
        f"; it leaves out {count(len(found.unpriced), 'position')} with no price"
        if found.unpriced
        else ""
    )
    return (
        ("par", "total par", found.par, {"fix": "par", "shown": money, "table": "total par"}),
        (
            "nav",
            "NAV",
            found.value,
            {
                "fix": "nav",
                "shown": money,
                "marked": True,
                "note": unpriced,
                "table": "NAV / market value at mid",
            },
        ),
        (
            "positions",
            "the number of positions",
            Decimal(found.positions),
            {
                "fix": "count",
                "shown": _count,
                "note": f" (rows with a readable par: {_of_rows(found)})",
                "table": f"positions (rows with a readable par: {_of_rows(found)})",
            },
        ),
        (
            "obligors",
            "the number of obligors",
            Decimal(len(found.borrowers)),
            {
                "fix": "count",
                "shown": _count,
                "note": f" (by borrower name; {len(found.tickers)} tickers)",
                "table": "obligors (by borrower name)",
            },
        ),
        (
            "sectors",
            "the number of sectors",
            Decimal(len(found.sectors)),
            {
                "fix": "count",
                "shown": _count,
                "note": " (by the Index Sector column)",
                "table": "sectors (by Index Sector)",
            },
        ),
        (
            "largest",
            "the largest issuer's share",
            largest,
            {
                "fix": "share",
                "marked": True,
                "shown": pct,
                "note": f" ({name})",
                "table": "largest issuer",
            },
        ),
        (
            "largest_sector",
            "the largest sector's share",
            share(max(found.sectors.values(), default=Decimal(0)), found.value),
            {"fix": "share", "marked": True, "shown": pct},
        ),
        (
            "top10",
            "the ten largest issuers' share",
            found.top_ten(),
            {"fix": "share", "marked": True, "shown": pct, "table": "ten largest issuers"},
        ),
        (
            "first_lien",
            "the first-lien share",
            share(shape.liens.get("first", Decimal(0)), found.value),
            {"fix": "share", "marked": True, "shown": pct, "table": "first lien"},
        ),
        (
            "second_lien",
            "the second-lien share",
            share(found.second_lien, found.value),
            {"fix": "share", "marked": True, "shown": pct, "table": "second lien"},
        ),
        (
            "price",
            "the weighted average price",
            found.price,
            {"marked": True, "table": "weighted average price"},
        ),
        (
            "margin",
            "the weighted average margin",
            found.margin,
            {"table": "weighted average margin (bps)"},
        ),
        (
            "ytm",
            "the weighted average yield to maturity (all rows, as given)",
            found.ytm_all,
            {"shown": pct, "note": _yield_note(found), "table": "weighted average yield, all rows"},
        ),
        (
            "wal",
            "the weighted average life",
            shape.life,
            {
                "marked": True,
                "shown": _years,
                "note": _life_note(shape),
                "table": "weighted average life",
            },
        ),
    )


def _internal_findings(file: str, claims: Mapping[str, Claim], findings: Findings) -> None:
    """Stated figures that disagree with each other: the average price against NAV over par, and a
    yield below the margin over the base rate."""
    price, nav, par = claims.get("price"), claims.get("nav"), claims.get("par")
    if price is not None and nav is not None and par is not None and par.value.value:
        ratio = share(nav.value.value, par.value.value)
        allowed = EXACT.add(price.value.half_unit, Decimal("0.0005"))
        if EXACT.abs(EXACT.subtract(price.value.value, ratio)) > allowed:
            problem = (
                f"the weighted average price is stated as {price.text}; the stated NAV over the "
                f"stated par is {plain(ratio.quantize(Decimal('0.001'), context=EXACT))}"
            )
            findings.add(file, price.where, price.cell, problem, "metric")
    ytm, margin = claims.get("ytm"), claims.get("margin")
    if (
        ytm is not None
        and margin is not None
        and ytm.value.percent
        and EXACT.multiply(ytm.value.value, HUNDRED) < margin.value.value
    ):
        problem = (
            f"the weighted average yield to maturity is stated as {ytm.text}, below the "
            f"stated weighted average margin of {margin.text} over the base rate"
        )
        findings.add(file, ytm.where, ytm.cell, problem, "plausible")


@dataclass
class Columns:
    name: int
    pct: int | None
    count: int | None
    value: int | None
    limit: int | None
    headroom: int | None
    status: int | None


_RANK = ("rank", "#", "no", "no.")
_NAMES = ("issuer", "name", "obligor", "borrower", "sector", "bucket", "metric")


def section_columns(header: Sequence[str]) -> Columns:
    """A section's columns by their headers. The name column is the first, unless the first is a
    rank (the largest-holdings layout: `Rank, Issuer, # Positions, ...`)."""
    names = [folded(cell) for cell in header]
    name = 0
    if names and names[0] in _RANK:
        name = next((i for i, n in enumerate(names) if any(w in n for w in _NAMES)), 1)

    def first(test: Callable[[str], bool]) -> int | None:
        return next((i for i, n in enumerate(names) if i > 0 and i != name and test(n)), None)

    return Columns(
        name=name,
        pct=first(lambda n: ("%" in n or "pct" in n) and "limit" not in n and "headroom" not in n),
        count=first(lambda n: any(w in n for w in ("issuer", "count", "#", "obligor", "position"))),
        value=first(lambda n: "mv" in n or "market value" in n or n.startswith("value")),
        limit=first(lambda n: "limit" in n),
        headroom=first(lambda n: "headroom" in n),
        status=first(lambda n: "status" in n),
    )


def label_of(row: Sequence[str], columns: Columns) -> str:
    return _cell_text(row, columns.name)


def _cell_text(row: Sequence[str], index: int | None) -> str:
    return row[index] if index is not None and index < len(row) else ""


def _label_kind(label: str) -> str:
    text = folded(label)
    if "subtotal" in text:
        return "subtotal"
    if "total" in text:
        return "total"
    return "other" if text.startswith("other") else "row"


def total_findings(file: str, section: Section, findings: Findings) -> None:
    """Each Total and Subtotal row against the rows it adds, per column: shares and amounts to
    within the rounding of the figures added, counts exactly."""
    columns = section_columns(section.header)
    for index, is_count in ((columns.pct, False), (columns.value, False), (columns.count, True)):
        if index is not None:
            _column_totals(file, section, index, is_count, findings)


def _column_totals(
    file: str, section: Section, index: int, is_count: bool, findings: Findings
) -> None:
    columns = section_columns(section.header)
    column = section.header[index] if index < len(section.header) else f"column {index + 1}"
    added: dict[str, list[Quantity]] = {"row": [], "other": []}
    silent: dict[str, list[str]] = {"row": [], "other": []}  # rows stating nothing here
    for number, row in section.rows:
        label = label_of(row, columns)
        text, kind = _cell_text(row, index), _label_kind(label)
        stated = quantity(text) if text else None
        if kind in added:
            (added[kind].append(stated) if stated is not None else silent[kind].append(label))
            continue
        if stated is None:
            continue
        parts = ("row",) if kind == "subtotal" else ("row", "other")
        quiet = [name for part in parts for name in silent[part]]
        if quiet:
            findings.notes.append(
                f"not checked: {section.title}, {label} {column}, because "
                f"{', '.join(quiet)} states no {column}"
            )
            continue
        rows = [q for part in parts for q in added[part]]
        _one_total(file, section, (number, label, column, text), (stated, rows, is_count), findings)


def _one_total(
    file: str,
    section: Section,
    at: tuple[int, str, str, str],
    values: tuple[Quantity, Sequence[Quantity], bool],
    findings: Findings,
) -> None:
    """A Total or Subtotal row (`at`: row, label, column, text) against the rows it adds
    (`values`: the stated total, the rows' figures, whether they are counts)."""
    number, label, column, text = at
    stated, added, is_count = values
    total = sum((q.value for q in added), Decimal(0))
    allowed = Decimal(0) if is_count else sum((q.half_unit for q in (*added, stated)), Decimal(0))
    gap = EXACT.abs(EXACT.subtract(stated.value, total))
    if gap > allowed:
        problem = (
            f"{label} states {column} {text}; its {len(added)} rows add to {plain(total)}, a "
            f"difference of {plain(gap)}"
            + ("" if is_count else f", more than their rounding ({plain(allowed)})")
        )
        findings.add(file, section.title, f"row {number}", problem, "total")


def _stated(row: Sequence[str], index: int | None) -> tuple[str, Quantity | None]:
    text = _cell_text(row, index)
    return text, (quantity(text) if text else None)


_LEGAL = frozenset(
    {
        *("inc", "incorporated", "llc", "ltd", "limited", "corp", "corporation", "co"),
        *("company", "sa", "plc", "lp", "llp", "bv", "gmbh", "ag", "nv", "sarl", "sas", "spa"),
        "the",
    }
)


def name_words(text: str) -> tuple[str, ...]:
    """A name as its words, ignoring case, punctuation and legal suffixes (Inc, LLC, Ltd, ...)."""
    words = re.findall(r"[a-z0-9]+", text.casefold())
    return tuple(word for word in words if word not in _LEGAL) or tuple(words)


def match_issuer(name: str, found: Recomputed) -> tuple[str, list[str]]:
    """How a report's issuer name matches the holdings' borrowers: `exact` (the same words),
    `ticker` (the name is a borrower's ticker) or `prefix` (the name's words begin the borrower's
    words, e.g. a group name against a legal name), and the folded borrower keys it matches;
    ("", []) when none does. More than one key is an ambiguous match."""
    words = name_words(name)
    tests: tuple[tuple[str, Callable[[str], bool]], ...] = (
        ("exact", lambda key: name_words(found.names[key]) == words),
        ("ticker", lambda key: name.strip().upper() in found.tickers_of.get(key, set())),
        ("prefix", lambda key: name_words(found.names[key])[: len(words)] == words),
    )
    for how, test in tests:
        keys = [key for key in found.borrowers if words and test(key)]
        if keys:
            return how, keys
    return "", []


def no_match(name: str, found: Recomputed) -> str:
    """The words for a listed name no borrower matches, with the borrowers it may stand for
    (`candidates`), which are not matched and not compared."""
    possible = candidates(name, found)
    listed = (
        f"possible, not compared: {'; '.join(possible)}"
        if possible
        else "no possible borrower by ticker letters or name word"
    )
    return f"no borrower matches {name} by exact name, ticker or prefix ({listed})"


def candidates(name: str, found: Recomputed) -> list[str]:
    """Borrowers a listed name may stand for, though it matches none: one with a ticker that
    begins with the name's first three letters (a brand held under its acquisition vehicle), or
    whose first word (four letters or more) occurs in the name (`FooBarco` and `Barco
    Communications Inc`). A candidate is never a match."""
    letters = "".join(name_words(name))
    out: list[str] = []
    for key in sorted(found.borrowers, key=lambda key: found.names[key]):
        borrower = found.names[key]
        ticker = next(
            (
                t
                for t in sorted(found.tickers_of.get(key, set()))
                if len(letters) >= 3 and t[:3].isalpha() and t[:3].casefold() == letters[:3]
            ),
            None,
        )
        first = (name_words(borrower) or ("",))[0]
        if ticker is not None:
            out.append(f"{borrower} (ticker {ticker} begins with the same three letters)")
        elif len(first) >= 4 and first in letters and (word := _as_written(first, borrower)):
            out.append(f"{borrower} ({word} of the borrower's name occurs in the listed name)")
    return out


def _as_written(word: str, text: str) -> str:
    found = re.search(re.escape(word), text, flags=re.IGNORECASE)
    return "" if found is None else found.group(0)


def holding_section_findings(export: Export, found: Recomputed, findings: Findings) -> None:
    """The report's largest holdings, by issuer: each name is matched to the holdings' borrowers
    (`match_issuer`); a matched issuer's market value, share and positions are compared; an
    ambiguous match is a note and is not compared; a name no borrower matches is a finding."""
    section = export.sections.get("holdings")
    if section is None or not found.value:
        return
    file, columns = export.files["exposure"], section_columns(section.header)
    matched: list[str] = []
    for number, row in section.rows:
        name = label_of(row, columns)
        if _label_kind(name) != "row" or not name:
            continue
        how, keys = match_issuer(name, found)
        cell = f"row {number}"
        if not keys:
            problem = f"{no_match(name, found)}; listed among the largest holdings"
            findings.add(file, section.title, cell, problem, "absent")
            continue
        if len(keys) > 1:
            shown = "; ".join(found.names[key] for key in keys)
            findings.notes.append(
                f"{section.title}, {cell}: {name} matches {len(keys)} borrowers ({shown}); "
                "ambiguous, not compared"
            )
            continue
        (key,) = keys
        matched.append(f"{name} = {found.names[key]} ({how})")
        _holding_row(file, (section, cell, row, columns), key, found, findings)
    if matched:
        findings.notes.append(f"largest holdings matched by name: {'; '.join(matched)}")


def _holding_row(
    file: str,
    at: tuple[Section, str, Sequence[str], Columns],
    key: str,
    found: Recomputed,
    findings: Findings,
) -> None:
    section, cell, row, columns = at
    name = label_of(row, columns)
    value = found.issuer_value.get(key, Decimal(0))
    for index, label, exact, how in (
        (columns.value, "its market value", value, {"marked": True, "shown": money}),
        (columns.pct, "its share", share(value, found.value), {"marked": True, "shown": pct}),
        (
            columns.count,
            "its number of positions",
            Decimal(len(found.borrowers[key])),
            {"shown": _count},
        ),
    ):
        text, stated = _stated(row, index)
        if stated is not None:
            claim = Claim(section.title, cell, text, stated)
            _claim_finding(file, claim, f"{name}: {label}", exact, findings, fix="share", **how)


def sector_section_findings(export: Export, found: Recomputed, findings: Findings) -> None:
    """Each listed sector's share against the holdings' (sectors by the Index Sector column), and
    its limit on the holdings' share: a limit the stated share meets but the holdings' share
    breaks is a breach the report hides."""
    section = export.sections.get("sectors")
    if section is None or not found.value:
        return
    file, columns = export.files["exposure"], section_columns(section.header)
    by_name = {folded(name): value for name, value in found.sectors.items()}
    for number, row in section.rows:
        name, cell = label_of(row, columns), f"row {number}"
        if _label_kind(name) != "row":
            continue
        if folded(name) not in by_name:
            problem = f"sector {name} is listed but no holding is in it"
            findings.add(file, section.title, cell, problem, "absent")
            continue
        exact = share(by_name[folded(name)], found.value)
        text, stated = _stated(row, columns.pct)
        if stated is not None:
            claim = Claim(section.title, cell, text, stated)
            _claim_finding(
                file,
                claim,
                f"{name}: its share",
                exact,
                findings,
                fix="share",
                marked=True,
                shown=pct,
            )
        limit = _stated(row, columns.limit)[1]
        status = _cell_text(row, columns.status)
        if (
            limit is not None
            and limit.operator != ">="
            and exact > limit.value
            and ("breach" not in folded(status))
        ):
            problem = (
                f"{name}: the holdings give {pct(exact)} against the limit "
                f"{_cell_text(row, columns.limit)}, a breach; the report states "
                f"{text or 'no share'} and status {status or 'none'}"
            )
            findings.add(file, section.title, cell, problem, "breach")


# --- Constraints ---------------------------------------------------------------------------------

_CONSTRAINT_COLUMNS = {
    "id": ("id",),
    "category": ("constraint category", "category"),
    "parameter": ("parameter",),
    "limit": ("limit",),
    "current": ("current", "exposure"),
    "headroom": ("headroom",),
    "status": ("status",),
    "checked": ("last checked",),
}
# A cell that says "not applicable" (an em or en dash, a hyphen, n/a): no figure, and no defect.
NOT_APPLICABLE = frozenset({"—", "–", "-", "n/a", "na", "not applicable"})
_MAXIMUM = re.compile(r"\b(?:max|maximum|at most|up to|no more than)\b")
_EXCLUDED = re.compile(r"\b(?:exclu\w*|prohibit\w*|not permitted)")
_MINIMUM = re.compile(r"\b(?:min|minimum|at least|no less than)\b")
_NAMED = re.compile(
    r"\(largest:\s*(?P<name>[^)]+)\)|largest (?:issuer|sector|obligor):\s*(?P<after>.+)$"
)
_ORDINAL = re.compile(r"\b(?P<n>\d+)(?:st|nd|rd|th) largest sector\b")


def _same_family(a: Quantity, b: Quantity) -> bool:
    return (a.percent and b.percent) or a.unit == b.unit


def _breached(limit: Quantity, value: Decimal) -> bool:
    return value > limit.value if limit.operator == "<=" else value < limit.value


@dataclass(frozen=True)
class Target:
    """What a constraint's parameter says it measures, as the holdings give it."""

    what: str
    value: Decimal
    unit: str  # "%", "yrs" or "" (a count)
    named: tuple[str, str] | None = None  # ("issuer" or "sector", the name the row states)
    rank: int = 1  # the n-th largest, for a sector row
    note: str = ""  # words after the figures
    key: str = ""  # the headline figure it is (`_headline`), when it is one


def named_in(text: str) -> str | None:
    found = _NAMED.search(text)
    return None if found is None else (found["name"] or found["after"]).strip()


def _sectors_ranked(found: Recomputed) -> list[str]:
    return sorted(found.sectors, key=lambda name: found.sectors[name], reverse=True)


def _sector_target(text: str, found: Recomputed) -> Target | None:
    ordinal = _ORDINAL.search(text)
    rank = int(ordinal["n"]) if ordinal else 1
    name = named_in(text) or (text.partition(":")[2].strip() if ordinal and ":" in text else None)
    ranked = _sectors_ranked(found)
    if name is not None:
        key = next((s for s in found.sectors if folded(s) == folded(name)), None)
        value = share(found.sectors[key], found.value) if key is not None else Decimal(0)
        return Target(f"sector {name}", value, "%", ("sector", name), rank)
    if rank > len(ranked):
        return None
    sector = ranked[rank - 1]
    return Target(
        f"{_ordinal(rank)}largest sector ({sector})",
        share(found.sectors[sector], found.value),
        "%",
        rank=rank,
    )


def _ordinal(rank: int) -> str:
    return "" if rank == 1 else f"{rank}{ {2: 'nd', 3: 'rd'}.get(rank, 'th') } "


def _has(text: str, *words: str) -> bool:
    return any(word in text for word in words)


def _lien_share(found: Recomputed, shape: Profile, *keys: str) -> Decimal:
    return share(sum((shape.liens.get(k, Decimal(0)) for k in keys), Decimal(0)), found.value)


def _excludes(text: str) -> bool:
    """An exclusion row: excluded, exclusion, prohibited or not permitted outside its brackets and
    no Max or Min (`Max single sector (excluding cash)` is a sector limit)."""
    outside = re.sub(r"\([^)]*\)", " ", text)
    return bool(_EXCLUDED.search(outside)) and not (
        _MAXIMUM.search(outside) or _MINIMUM.search(outside)
    )


def _exclusion_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    """An exclusion row that lists its sectors in brackets (`Excluded sectors (Tobacco,
    Weapons)`): their combined share, by the Index Sector column. Without a list, nothing."""
    listed = re.search(r"\(([^)]+)\)", parameter)
    if listed is None:
        return None
    names = [name.strip() for name in re.split(r"[,;]", listed[1]) if name.strip()]
    held = {folded(sector): value for sector, value in found.sectors.items()}
    value = sum((held.get(folded(name), Decimal(0)) for name in names), Decimal(0))
    return Target(f"sectors {', '.join(names)}", share(value, found.value), "%")


def _top_ten_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    return Target("ten largest issuers", found.top_ten(), "%", key="top10")


def _sector_row_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    return _sector_target(parameter, found)


def _issuer_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    name, largest = found.largest_issuer()
    stated = named_in(parameter)
    named = ("issuer", stated) if stated else None
    return Target(f"largest issuer ({name})", largest, "%", named, key="largest")


def _second_lien_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    keys = ("second", "unsecured") if "unsecured" in folded(parameter) else ("second",)
    words = "second lien" + (" and unsecured" if len(keys) > 1 else "")
    return Target(words, _lien_share(found, shape, *keys), "%", key="second_lien")


def _first_lien_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    return Target("first lien", _lien_share(found, shape, "first"), "%", key="first_lien")


def _ccc_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    buckets = ("CCC", "Unrated") if "unrated" in folded(parameter) else ("CCC",)
    value = sum((shape.buckets.get(b, Decimal(0)) for b in buckets), Decimal(0))
    return Target(" and ".join(buckets), share(value, found.value), "%")


def _unrated_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    return Target("unrated", share(shape.buckets.get("Unrated", Decimal(0)), found.value), "%")


def _life_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    if shape.life is None:
        return None
    return Target("weighted average life", shape.life, "yrs", note=_life_note(shape), key="wal")


def _obligor_target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    return Target("obligors by borrower name", Decimal(len(found.borrowers)), "", key="obligors")


Builder = Callable[[str, "Recomputed", "Profile"], "Target | None"]
# What a parameter's words say it measures, tested in this order (the specific before the general:
# "Aggregate top 10 issuers" is the top ten, not the largest issuer; "Excluded sectors (...)" is
# the listed sectors, not the largest sector). A CCC row that includes
# Other is not recomputed: no rule says what Other holds.
_TARGETS: tuple[tuple[Callable[[str], bool], Builder], ...] = (
    (lambda t: _excludes(t) and _has(t, "sector", "industr"), _exclusion_target),
    (lambda t: _has(t, "top 10", "top ten", "ten largest"), _top_ten_target),
    (lambda t: _has(t, "sector", "industry"), _sector_row_target),
    (
        lambda t: _has(t, "single issuer", "single name", "largest issuer", "single obligor"),
        _issuer_target,
    ),
    (lambda t: _has(t, "2nd lien", "second lien"), _second_lien_target),
    (lambda t: _has(t, "1st lien", "first lien"), _first_lien_target),
    (lambda t: "ccc" in t and "other" not in t, _ccc_target),
    (lambda t: "unrated" in t and "ccc" not in t, _unrated_target),
    (lambda t: _has(t, "wal", "weighted avg life", "weighted average life"), _life_target),
    (lambda t: "obligor" in t and "number" in t, _obligor_target),
)


def target(parameter: str, found: Recomputed, shape: Profile) -> Target | None:
    """The holdings' figure for what a constraint's parameter says, or None when the parameter
    names nothing the holdings give (it is then not checked, never matched to the nearest), or
    when there are no priced holdings to compare with."""
    if not found.value:
        return None
    text = folded(parameter)
    build = next((build for test, build in _TARGETS if test(text)), None)
    return None if build is None else build(parameter, found, shape)


@dataclass
class ConstraintRow:
    file: str
    number: int
    cells: dict[str, str]

    @property
    def label(self) -> str:
        return self.cells.get("id") or self.cells.get("parameter") or f"row {self.number}"

    def text(self, key: str) -> str:
        """A cell's text; "" when empty or not applicable."""
        value = self.cells.get(key, "")
        return "" if folded(value) in NOT_APPLICABLE else value


def constraint_rows(export: Export) -> list[ConstraintRow]:
    rows_out: list[ConstraintRow] = []
    for file, rows, header in export.constraints:
        columns = {
            key: index
            for key, words in _CONSTRAINT_COLUMNS.items()
            if key != "id" and (index := column_index(header, words)) is not None
        }
        # The id column by its whole header: "id" is also inside "Limit / Guideline".
        ident = next((i for i, cell in enumerate(header) if folded(cell) in ("id", "#")), None)
        if ident is not None:
            columns["id"] = ident
        start = next(number for number, row in rows if _cells(row))
        rows_out += [
            ConstraintRow(file, number, {k: _cell_text(row, i) for k, i in columns.items()})
            for number, row in rows
            if number > start and _cells(row)
        ]
    return rows_out


def constraint_findings(
    export: Export, found: Recomputed, shape: Profile, findings: Findings
) -> list[tuple[str, date]]:
    """Every constraints row, then the files against each other; returns the dates each row was
    last checked, for staleness."""
    checked: list[tuple[str, date]] = []
    unmapped: list[str] = []
    items = constraint_rows(export)
    for item in items:
        if not _constraint(item, (found, shape), findings):
            unmapped.append(f"{item.label} {item.cells.get('parameter', '')}".strip())
        if (when := text_date(item.cells.get("checked", ""))) is not None:
            checked.append((item.file, when))
    if unmapped:
        findings.notes.append(
            "not checked against the holdings (the parameter names nothing they give): "
            + "; ".join(dict.fromkeys(unmapped))
        )
    _between_files(items, findings)
    return checked


def _read(item: ConstraintRow, key: str, findings: Findings) -> Quantity | None:
    text = item.text(key)
    if not text:
        return None
    stated = quantity(text)
    if stated is not None and key == "limit" and not stated.operator:
        stated = _with_direction(stated, item.cells.get("parameter", ""))
    if stated is None or stated.approximate or (key == "limit" and not stated.operator):
        place = (item.file, "Constraints", f"row {item.number}")
        _unreadable(place, f"{item.label} {key}", text, findings)
        return None
    return stated


def _with_direction(limit: Quantity, parameter: str) -> Quantity:
    """A limit stated without ≤ or ≥ (e.g. `0% NAV`) takes its direction from the parameter's
    Max or Min; with neither, an exclusion (`_excludes`) or a limit of zero is a maximum, "at most
    0%". Otherwise it stays without one and is reported unread."""
    text = folded(parameter)
    if _MAXIMUM.search(text):
        return replace(limit, operator="<=")
    if _MINIMUM.search(text):
        return replace(limit, operator=">=")
    return replace(limit, operator="<=") if _excludes(text) or not limit.value else limit


def _constraint(item: ConstraintRow, facts: tuple[Recomputed, Profile], findings: Findings) -> bool:
    """One row's own arithmetic, then against the holdings. False when the parameter names
    nothing the holdings give."""
    if "info" in folded(item.cells.get("limit", "")):
        return True
    limit, current = _read(item, "limit", findings), _read(item, "current", findings)
    if limit is None or current is None:
        return True
    if not _same_family(limit, current):
        if not current.unit:
            problem = (
                f"{item.label}: current value '{item.cells['current']}' has no unit; the limit "
                f"'{item.cells['limit']}' is in {limit.unit}"
            )
            findings.add(item.file, "Constraints", f"row {item.number}", problem, "unit")
        return True
    _own_arithmetic(item, limit, current, findings)
    goal = target(item.cells.get("parameter", ""), *facts)
    if goal is None:
        return False
    _against_holdings(item, (limit, current), goal, facts[0], findings)
    return True


def _own_arithmetic(
    item: ConstraintRow, limit: Quantity, current: Quantity, findings: Findings
) -> None:
    where, cell = "Constraints", f"row {item.number}"
    status = item.text("status")
    if status and _breached(limit, current.value) != ("breach" in folded(status)):
        problem = (
            f"{item.label}: status {status} with current value {item.cells['current']} against "
            f"the limit {item.cells['limit']}"
        )
        findings.add(item.file, where, cell, problem, "status")
    headroom = _read(item, "headroom", findings)
    if headroom is not None and _same_family(headroom, limit):
        room = EXACT.subtract(limit.value, current.value)
        expected = room if limit.operator == "<=" else room.copy_negate()
        if not within(headroom, expected):
            problem = (
                f"{item.label}: headroom {item.cells['headroom']} is not the limit "
                f"{item.cells['limit']} less the current value {item.cells['current']} "
                f"({plain(expected)})"
            )
            findings.add(item.file, where, cell, problem, "headroom")


def _against_holdings(
    item: ConstraintRow,
    stated: tuple[Quantity, Quantity],
    goal: Target,
    found: Recomputed,
    findings: Findings,
) -> None:
    limit, current = stated
    if goal.named is not None:
        _named_finding(item, goal, found, findings)
    if not _in_family(current, goal):
        return
    claim = Claim("Constraints", f"row {item.number}", item.cells["current"], current)
    _claim_finding(
        item.file,
        claim,
        f"{item.label}: the current value ({goal.what})",
        goal.value,
        findings,
        fix="share",
        marked=goal.unit != "",
        shown=_shown(goal),
        note=goal.note,
    )
    status = item.text("status")
    if _breached(limit, goal.value) and "breach" not in folded(status):
        problem = (
            f"{item.label}: on the holdings' {_unit_text(goal)} ({goal.what}) the limit "
            f"{item.cells['limit']} is breached; the status says {status or 'none'}"
        )
        findings.add(item.file, "Constraints", f"row {item.number}", problem, "breach")


def _in_family(current: Quantity, goal: Target) -> bool:
    return current.percent if goal.unit == "%" else current.unit == goal.unit


def _shown(goal: Target) -> Callable[[Decimal], str]:
    return pct if goal.unit == "%" else _years if goal.unit == "yrs" else _count


def stated_in_constraints(
    export: Export, key: str, facts: tuple[Recomputed, Profile]
) -> tuple[str, str, str, str] | None:
    """A reconciliation-table row for a headline figure the summary does not state, from the first
    constraints row whose parameter gives it: (what, with the file and row; stated; holdings;
    difference).
    The row itself is checked with the constraints."""
    for item in constraint_rows(export):
        goal = target(item.cells.get("parameter", ""), *facts)
        current = quantity(item.text("current"))
        if goal is None or goal.key != key or current is None or not _in_family(current, goal):
            continue
        places = current.places + 2
        gap = EXACT.abs(EXACT.subtract(current.value, goal.value))
        return (
            f"{goal.what} (constraints: {item.file}, row {item.number})",
            item.cells["current"],
            _to_places(_shown(goal), goal.value, places),
            _to_places(_shown(goal), gap, places),
        )
    return None


def _unit_text(goal: Target) -> str:
    return (
        pct(goal.value)
        if goal.unit == "%"
        else _years(goal.value)
        if goal.unit == "yrs"
        else _count(goal.value)
    )


def _named_finding(
    item: ConstraintRow, goal: Target, found: Recomputed, findings: Findings
) -> None:
    """The issuer or sector a row names as the largest (or n-th largest) against the holdings'."""
    assert goal.named is not None
    kind, name = goal.named
    cell = f"row {item.number}"
    if kind == "issuer":
        problem = _issuer_named(name, found)
    else:
        ranked = _sectors_ranked(found)
        actual = ranked[goal.rank - 1] if goal.rank <= len(ranked) else None
        if not any(folded(s) == folded(name) for s in found.sectors):
            problem = f"names the sector {name}, which no holding is in"
        elif actual is not None and folded(actual) != folded(name):
            problem = (
                f"names {name} as the {_ordinal(goal.rank)}largest sector; in the holdings it is "
                f"{actual} ({pct(share(found.sectors[actual], found.value))})"
            )
        else:
            problem = ""
    if problem:
        findings.add(item.file, "Constraints", cell, f"{item.label}: {problem}", "share")


def _issuer_named(name: str, found: Recomputed) -> str:
    how, keys = match_issuer(name, found)
    largest, value = found.largest_issuer()
    if not keys:
        return f"names {name} as the largest issuer; {no_match(name, found)}"
    if len(keys) > 1:
        return ""  # ambiguous: reported where the largest holdings are matched
    if found.names[keys[0]] != largest:
        return (
            f"names {name} ({found.names[keys[0]]}, by {how}) as the largest issuer; in the "
            f"holdings it is {largest} ({pct(value)})"
        )
    return ""


_COMPARED = ("limit", "current", "headroom", "status")


def _between_files(items: Sequence[ConstraintRow], findings: Findings) -> None:
    """Two constraints files stating the same parameter: each figure must agree."""
    by_parameter: dict[str, list[ConstraintRow]] = {}
    for item in items:
        if item.cells.get("parameter"):
            by_parameter.setdefault(folded(item.cells["parameter"]), []).append(item)
    for rows in by_parameter.values():
        files = {row.file for row in rows}
        if len(files) < 2:
            continue
        first = rows[0]
        for other in rows[1:]:
            if other.file == first.file:
                continue
            for key in _COMPARED:
                if not _same_cell(first.text(key), other.text(key)):
                    problem = (
                        f"{first.cells['parameter']}: {key} is {first.text(key) or 'empty'} in "
                        f"{first.file} (row {first.number}) and {other.text(key) or 'empty'} here"
                    )
                    findings.add(
                        other.file, "Constraints", f"row {other.number}", problem, "differs"
                    )


def _same_cell(a: str, b: str) -> bool:
    if folded(a) == folded(b):
        return True
    one, two = quantity(a), quantity(b)
    return one is not None and two is not None and one.value == two.value and _same_family(one, two)


# --- The mandate ---

_LEADING = re.compile(
    r"^\s*(?:USD|EUR|GBP|\$|€|£)?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:bn|mm|mn|m|k)?(?=\s|$|[—–])",
    re.IGNORECASE,
)


def leading_amount(text: str) -> Quantity | None:
    """The amount a capital-structure cell starts with: `$280,000,000 — SOFR + 130bps` is
    280,000,000; what follows (a spread, a rating) is a note, not part of the figure."""
    whole = quantity(text)
    if whole is not None:
        return whole
    found = _LEADING.match(text)
    return quantity(found.group(0)) if found is not None else None


_AS_OF_FIELDS = ("as of", "as_of", "report date", "valuation date", "reporting date")


def mandate_findings(
    export: Export, claims: Mapping[str, Claim], findings: Findings
) -> list[tuple[str, date]]:
    """The capital structure against its stated total and the collateral; returns the mandate's
    as-of dates for staleness."""
    file = export.files.get("mandate", "")
    tranches: list[tuple[int, Quantity]] = []
    total: tuple[int, str, Quantity] | None = None
    collateral: Quantity | None = None
    dates: list[tuple[str, date]] = []
    for number, row in export.mandate[1:]:
        section, name, value = (_cell_text(row, i) for i in (0, 1, 2))
        if any(word in folded(name) for word in _AS_OF_FIELDS) and (when := text_date(value)):
            dates.append((file, when))
        amount = leading_amount(value) if "capital" in folded(section) else None
        if amount is None or amount.percent:
            continue
        if "total" in folded(name):
            total = (number, value, amount)
        elif any(word in folded(name) for word in ("nav", "collateral", "par")):
            collateral = amount
        else:
            tranches.append((number, amount))
    if total is not None:
        base = claims["nav"].value if "nav" in claims else collateral
        _capital(file, total, tranches, base, findings)
    return dates


def _capital(
    file: str,
    total: tuple[int, str, Quantity],
    tranches: Sequence[tuple[int, Quantity]],
    base: Quantity | None,
    findings: Findings,
) -> None:
    number, text, stated = total
    added = sum((q.value for _, q in tranches), Decimal(0))
    allowed = sum((q.half_unit for _, q in tranches), stated.half_unit)
    if tranches and EXACT.abs(EXACT.subtract(added, stated.value)) > allowed:
        problem = (
            f"the capital structure total {text} is not its {len(tranches)} tranches' sum "
            f"{money(added)}"
        )
        findings.add(file, "Mandate", f"row {number}", problem, "total")
    if base is not None and base.value:
        ratio = EXACT.divide(stated.value, base.value)
        if EXACT.abs(EXACT.subtract(ratio, Decimal(1))) > CAPITAL_BAND:
            problem = (
                f"the capital structure total {text} is {pct(EXACT.multiply(ratio, HUNDRED))} of "
                f"the collateral NAV {money(base.value)}, outside 95% to 105%: the tranches and "
                "the "
                "collateral do not balance"
            )
            findings.add(file, "Mandate", f"row {number}", problem, "capital")


# --- Dates ---------------------------------------------------------------------------------------


def report_dates(export: Export) -> list[tuple[str, date]]:
    """The exposure report's own as-of dates: summary rows such as `As of Date, 29-May-2026`."""
    section = export.sections.get("summary")
    if section is None:
        return []
    found = [
        (export.files["exposure"], when)
        for _, row in section.rows
        if any(word in folded(row[0]) for word in _AS_OF_FIELDS)
        and (when := text_date(_cell_text(row, 1))) is not None
    ]
    return found


def stale_findings(dated: Sequence[tuple[str, date]], run_date: date, findings: Findings) -> None:
    """Each file's dates against the run's as-of date: after it, or more than `STALE_DAYS`
    before it."""
    by_file: dict[str, set[date]] = {}
    for file, when in dated:
        by_file.setdefault(file, set()).add(when)
    for file, dates in by_file.items():
        late = sorted(d for d in dates if d > run_date)
        old = sorted(d for d in dates if (run_date - d).days > STALE_DAYS)
        if late:
            problem = f"dated {', '.join(map(str, late))}, after the run's as-of date {run_date}"
            findings.add(file, "dates", "as of", problem, "future")
        if old:
            days = (run_date - old[-1]).days
            problem = (
                f"dated {', '.join(map(str, old))}, {days} days or more before the run's as-of "
                f"date {run_date}, more than {STALE_DAYS}: stale"
            )
            findings.add(file, "dates", "as of", problem, "stale")


# --- The whole export ----------------------------------------------------------------------------


def validate_export(files: Mapping[str, bytes], *, run_date: date | None = None) -> ExportReport:
    """Check a portfolio export (any of its parts, as CSV files or workbook sheets) with the
    holdings as the authority. Findings come most consequential first (`PRIORITY`)."""
    findings = Findings()
    export = read_export(files)
    rows = [*export.holdings, *export.market]
    tallies = type_rows(rows)
    found = recompute(export.holdings)
    if export.book:
        _holdings_checks(export, tallies, found, findings)
    elif export.files:
        first = next(iter(export.files.values()))
        findings.add(first, "files", "holdings", "no holdings sheet is among the files", "missing")
    claims, unchecked = summary_claims(export, findings) if "exposure" in export.files else ({}, [])
    dated = mandate_findings(export, claims, findings) if "mandate" in export.files else []
    dated += report_dates(export)
    data_date = next((when for _, when in dated), None)
    shape = profile(export.holdings, data_date or run_date)
    dated += constraint_findings(export, found, shape, findings)
    if "exposure" in export.files:
        _report_checks(export, (claims, found, shape), data_date or run_date, findings)
    date_findings(export.book, rows, run_date or data_date, findings)
    if run_date is not None:
        stale_findings(dated, run_date, findings)
    notes = [*findings.notes, *(f"not checked: {item}" for item in unchecked)]
    if "ratings" in export.sections and export.book:
        notes.append(BUCKET_RULE)
    order = sorted(export.roles.items(), key=lambda item: (ROLES.index(item[1]), item[0]))
    return ExportReport(
        ok=not findings.issues,
        rows=found.positions,
        issues=findings.ordered(),
        files=tuple(order),
        recomputed=recomputed_lines(found) if export.book else (),
        notes=tuple(notes),
        table=tuple(findings.table),
    )


def _report_checks(
    export: Export,
    facts: tuple[Mapping[str, Claim], Recomputed, Profile],
    as_of: date | None,
    findings: Findings,
) -> None:
    """The exposure report: its figures against the holdings, then its own totals."""
    claims, found, shape = facts
    if export.book:
        summary_findings(export, claims, found, shape, findings)
        holding_section_findings(export, found, findings)
        sector_section_findings(export, found, findings)
        rating_section_findings(export, found, shape, findings)
        maturity_section_findings(export, found, shape, as_of, findings)
    for section in export.sections.values():
        if section.key != "summary":
            total_findings(export.files["exposure"], section, findings)
    if not export.sections:
        findings.add(export.files["exposure"], "layout", "A1", "no sections found", "layout")


def _holdings_checks(
    export: Export, tallies: Mapping[str, Tally], found: Recomputed, findings: Findings
) -> None:
    file = export.book
    missing = [key for key in _REQUIRED_HOLDING if key not in export.holding_columns]
    if missing:
        problem = f"the holdings header has no column for {', '.join(missing)}"
        findings.add(file, found.sheet, "header", problem, "column")
    rows = [*export.holdings, *export.market]
    par_of = {h.row: h.numbers["par"] for h in export.holdings if "par" in h.numbers}
    for sheet, tally in tallies.items():
        tally_findings(file, sheet, tally, findings, par_of if sheet == found.sheet else {})
    if export.holdings:
        par_findings(file, export.holdings, findings)
        lien_findings(file, export.holdings, findings)
        tranche_findings(file, export.holdings, findings)
        borrower_ticker_findings(file, export.holdings, findings)
    range_findings(file, rows, found, findings)
    quote_findings(file, rows, findings)
    identifier_findings(file, rows, findings)
    kind_findings(file, rows, findings)
    for sheet_rows_ in (export.holdings, export.market):
        if sheet_rows_:
            rating_findings(file, sheet_rows_, findings)
    empty_row_findings(file, export, findings)


def validate_export_paths(paths: Sequence[Path], *, run_date: date | None = None) -> ExportReport:
    """`validate_export` on files on disk; a file that cannot be read is the one issue."""
    files: dict[str, bytes] = {}
    for path in paths:
        try:
            files[path.name] = path.read_bytes()
        except OSError as error:
            issue = Issue(
                file=path.name,
                sheet="file",
                cell="A1",
                problem=f"cannot read the file: {error.strerror or type(error).__name__}",
                fix="check the path and that the file is readable",
            )
            return ExportReport(ok=False, rows=0, issues=(issue,))
    report = validate_export(files, run_date=run_date)
    unknown = [name for name in files if name not in report.sources]
    if not unknown:
        return report
    extra = tuple(
        Issue(
            file=name,
            sheet="file",
            cell="A1",
            problem="not recognised as the mandate, constraints, exposure report or holdings",
            fix=FIX["layout"],
        )
        for name in unknown
    )
    return report.model_copy(update={"ok": False, "issues": (*report.issues, *extra)})


# --- Ratings, liens, life and maturities ---------------------------------------------------------

# Moody's and S&P scales as one number each (Aaa/AAA 1 .. C 21, D 22); the constraint
# `≥ Caa1 (numeric ≤ 17)` uses the same numbers.
MOODYS = (
    *("Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3", "Baa1", "Baa2", "Baa3", "Ba1", "Ba2", "Ba3"),
    *("B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "Ca", "C"),
)
SP = (
    *("AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-"),
    *("B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"),
)
# The bucket rule: Moody's when it rates the loan, else S&P; 1-10 investment grade, 11-13 BB,
# 14-16 B, 17 and worse CCC; no rating (withdrawn, not rated, an error token) unrated.
BUCKETS = (("IG", 10), ("BB", 13), ("B", 16), ("CCC", 99))
BUCKET_RULE = (
    "rating buckets recomputed from Moody's, else S&P: Baa3/BBB- or better IG, Ba1-Ba3/BB+ to "
    "BB- BB, B1-B3/B+ to B- B, Caa1/CCC+ or worse CCC, no rating Unrated; 'Other' is not "
    "recomputed"
)
WATCH = re.compile(r"\s*\*\s*[+-]?\s*$|\s*\(?\b(?:sf|pi|u)\)?$")
YEAR_DAYS = Decimal("365.25")


def rating_number(holding: Holding) -> int | None:
    parts = [WATCH.sub("", p.strip()) for p in _AGENCIES.split(holding.text.get("ratings", ""))]
    for scale, part in zip((MOODYS, SP), (*parts, "", ""), strict=False):
        if part in scale:
            return scale.index(part) + 1
    return None


def rating_bucket(holding: Holding) -> str:
    number = rating_number(holding)
    if number is None:
        return "Unrated"
    return next(name for name, worst in BUCKETS if number <= worst)


def label_bucket(label: str) -> str | None:
    """The bucket a report's rating row names, or None (e.g. Other) when it names none."""
    text = folded(label)
    for bucket, words in (
        ("Unrated", ("unrated", "not rated", "nr")),
        ("CCC", ("ccc", "caa")),
        ("IG", ("ig", "investment", "baa", "bbb")),
        ("BB", ("bb", "ba")),
        ("B", ("b",)),
    ):
        if any(re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", text) for w in words):
            return bucket
    return None


def corrected(when: date) -> date:
    """A maturity whose two-digit year was read as 19xx, read as 20xx instead."""
    return when.replace(year=when.year + 100) if when.year < CENTURY else when


def years_to(when: date, as_of: date) -> Decimal:
    return EXACT.divide(Decimal((when - as_of).days), YEAR_DAYS)


@dataclass
class Profile:
    """Market value by rating bucket (with the borrowers in each), by lien, and by maturity, and
    the par-weighted life, from the priced positions; maturities as given and, when some fall
    before 1950, also with those years read as 20xx."""

    buckets: dict[str, Decimal] = field(default_factory=dict)
    bucket_borrowers: dict[str, set[str]] = field(default_factory=dict)
    liens: dict[str, Decimal] = field(default_factory=dict)
    life: Decimal | None = None
    life_corrected: Decimal | None = None
    by_maturity: list[tuple[date, date, Decimal]] = field(default_factory=list)  # given, fixed, mv
    centuries: int = 0


def profile(rows: Sequence[Holding], as_of: date | None) -> Profile:
    out = Profile()
    lives: list[tuple[Decimal, Decimal, Decimal]] = []
    for holding in rows:
        par, price = holding.numbers.get("par"), mid(holding)
        if par is None or price is None:
            continue
        value = EXACT.divide(EXACT.multiply(par, price), HUNDRED)
        bucket = rating_bucket(holding)
        out.buckets[bucket] = EXACT.add(out.buckets.get(bucket, Decimal(0)), value)
        out.bucket_borrowers.setdefault(bucket, set()).add(folded(holding.text["borrower"]))
        out.liens[lien(holding)] = EXACT.add(out.liens.get(lien(holding), Decimal(0)), value)
        if holding.maturity is not None:
            fixed = corrected(holding.maturity)
            out.centuries += fixed != holding.maturity
            out.by_maturity.append((holding.maturity, fixed, value))
            if as_of is not None:
                lives.append((par, years_to(holding.maturity, as_of), years_to(fixed, as_of)))
    out.life = _weighted((w, given) for w, given, _ in lives)
    out.life_corrected = _weighted((w, fixed) for w, _, fixed in lives)
    return out


_RANGE = re.compile(r"(?:(\d+(?:\.\d+)?)\s*(?:-|to|–)\s*)?(\d+(?:\.\d+)?)\s*\+?\s*y", re.IGNORECASE)


def maturity_bounds(label: str) -> tuple[Decimal, Decimal] | int | None:
    """A maturity bucket's label as a calendar year, or as years to maturity [low, high), or None
    when it is neither: `2028`; `1-2 Years`; `< 1 Year`; `> 7 Years` or `7+ Years`."""
    text = folded(label)
    if re.fullmatch(r"(?:19|20)\d\d", text):
        return int(text)
    found = _RANGE.search(text)
    if found is None:
        return None
    high = Decimal(found[2])
    if found[1] is not None:
        return Decimal(found[1]), high
    if text.startswith(("<", "under", "less", "up to")):
        return Decimal(0), high
    if text.startswith((">", "over", "more")) or "+" in text:
        return high, Decimal(10**6)
    return None


def maturity_value(
    found: Profile, bounds: tuple[Decimal, Decimal] | int, as_of: date | None, fixed: bool
) -> Decimal | None:
    total = Decimal(0)
    for given, mended, value in found.by_maturity:
        when = mended if fixed else given
        if isinstance(bounds, int):
            hit = when.year == bounds
        elif as_of is None:
            return None
        else:
            years = years_to(when, as_of)
            hit = bounds[0] <= years < bounds[1]
        if hit:
            total = EXACT.add(total, value)
    return total


# --- More cell checks ----------------------------------------------------------------------------

_FIGI_LIKE = re.compile(r"^BBG[A-Z0-9]{6,}$")


def quote_findings(file: str, rows: Sequence[Holding], findings: Findings) -> None:
    """A bid above its ask, per sheet."""
    for sheet in dict.fromkeys(h.sheet for h in rows):
        crossed = [
            h
            for h in rows
            if h.sheet == sheet
            and "bid" in h.numbers
            and "ask" in h.numbers
            and h.numbers["bid"] > h.numbers["ask"]
        ]
        if crossed:
            first = crossed[0]
            problem = (
                f"the bid is above the ask on {rows_named([h.row for h in crossed])} (row "
                f"{first.row}: bid {first.text['bid']}, ask {first.text['ask']})"
            )
            findings.add(file, sheet, "Bid", problem, "bid_ask")


def tranche_findings(file: str, rows: Sequence[Holding], findings: Findings) -> None:
    """A holding's par above its tranche's size (Size ($Mn), in millions)."""
    for holding in rows:
        par, size = holding.numbers.get("par"), holding.numbers.get("size")
        if par is not None and size is not None and par > EXACT.multiply(size, Decimal(10**6)):
            problem = (
                f"row {holding.row} holds par {money(par)} of a tranche of "
                f"{holding.text['size']} million"
            )
            findings.add(file, holding.sheet, "Holdings (par)", problem, "tranche")


def borrower_ticker_findings(file: str, rows: Sequence[Holding], findings: Findings) -> None:
    """A borrower name under two tickers (the reverse of a ticker naming two borrowers)."""
    tickers: dict[str, dict[str, int]] = {}
    shown: dict[str, str] = {}
    for holding in rows:
        name, ticker = holding.text.get("borrower", ""), holding.text.get("ticker", "")
        if name and ticker:
            shown.setdefault(folded(name), name)
            tickers.setdefault(folded(name), {}).setdefault(ticker, holding.row)
    for key, found in tickers.items():
        if len(found) > 1:
            listed = "; ".join(f"{ticker} (row {row})" for ticker, row in found.items())
            problem = f"borrower {shown[key]} has {len(found)} tickers: {listed}"
            findings.add(file, rows[0].sheet, "Ticker", problem, "borrower_tickers")


def kind_findings(file: str, rows: Sequence[Holding], findings: Findings) -> None:
    """A cell holding another column's kind of value: a lien in Ratings, a FIGI in a name."""
    for holding in rows:
        ratings = holding.text.get("ratings", "")
        if "lien" in folded(ratings):
            problem = f"Ratings on row {holding.row} holds a ranking, '{ratings}'"
            findings.add(file, holding.sheet, "Ratings", problem, "kind")
        for key, column in (("borrower", "Borrower Name"), ("loan", "Loan Name")):
            if _FIGI_LIKE.match(holding.text.get(key, "")):
                problem = f"{column} on row {holding.row} holds a FIGI, '{holding.text[key]}'"
                findings.add(file, holding.sheet, column, problem, "kind")


# --- The report's ratings and maturities against the holdings ------------------------------------


def rating_section_findings(
    export: Export, found: Recomputed, shape: Profile, findings: Findings
) -> None:
    """Each rating bucket the report states, by `BUCKET_RULE`: its share and its issuer count;
    then each bucket the holdings fill that the report does not list."""
    section = export.sections.get("ratings")
    if section is None or not found.value:
        return
    file, columns = export.files["exposure"], section_columns(section.header)
    listed: set[str] = set()
    for number, row in section.rows:
        name = label_of(row, columns)
        bucket = label_bucket(name) if _label_kind(name) == "row" else None
        if bucket is None:
            continue
        listed.add(bucket)
        borrowers = Decimal(len(shape.bucket_borrowers.get(bucket, ())))
        value = share(shape.buckets.get(bucket, Decimal(0)), found.value)
        for index, label, exact, how in (
            (columns.pct, "its share", value, {"marked": True, "shown": pct}),
            (columns.count, "its issuer count", borrowers, {"shown": _count}),
        ):
            text, stated = _stated(row, index)
            if stated is not None:
                claim = Claim(section.title, f"row {number}", text, stated)
                words = f"rating bucket {name} ({bucket}): {label}"
                _claim_finding(file, claim, words, exact, findings, fix="share", **how)
    for bucket, value in shape.buckets.items():
        if bucket not in listed and value:
            issuers = count(len(shape.bucket_borrowers[bucket]), "issuer")
            problem = (
                f"the report lists no {bucket} row; the holdings put "
                f"{pct(share(value, found.value))} ({issuers}) there"
            )
            findings.add(file, section.title, "rows", problem, "share")


def maturity_section_findings(
    export: Export, found: Recomputed, shape: Profile, as_of: date | None, findings: Findings
) -> None:
    """Each maturity bucket the report states: its share and market value, from the maturities as
    given; with the 19xx years read as 20xx the figure is given beside it, never applied."""
    section = export.sections.get("maturity")
    if section is None or not found.value:
        return
    file, columns = export.files["exposure"], section_columns(section.header)
    for number, row in section.rows:
        name = label_of(row, columns)
        bounds = maturity_bounds(name) if _label_kind(name) == "row" else None
        given = maturity_value(shape, bounds, as_of, False) if bounds is not None else None
        if bounds is None or given is None:
            continue
        mended = maturity_value(shape, bounds, as_of, True)
        for index, label, exact, shown, other in (
            (
                columns.pct,
                "its share",
                share(given, found.value),
                pct,
                share(mended or Decimal(0), found.value),
            ),
            (columns.value, "its market value", given, money, mended or Decimal(0)),
        ):
            text, stated = _stated(row, index)
            if stated is None:
                continue
            note = (
                f"; with the maturities before 1950 read as 20xx it would be {shown(other)} "
                "(not applied)"
                if shape.centuries and other != exact
                else ""
            )
            claim = Claim(section.title, f"row {number}", text, stated)
            _claim_finding(
                file,
                claim,
                f"maturity bucket {name}: {label}",
                exact,
                findings,
                fix="share",
                marked=True,
                shown=shown,
                note=note,
            )
