"""The `portfolio` workbook: the fund's mandate, exposures and compliance limits (task PF-1).

The user supplies one XLSX workbook in their environment; it enters a pack as an ordinary XLSX
source (`preparation.SourceRequest`), CP-0 classes its authority, and the Portfolio Fit and
Portfolio Debate owners quote its cells by `sheet:<name>!<cell>` locators. This module holds
the template contract as data (`SHEETS`, every column's fix), `validate_portfolio`, the
self-check the user runs before `prepare`, and `portfolio_facts`, the typed reader the
Portfolio Fit module consumes. It never sets an authority and computes nothing a module owns
(`one_pct_nav` is the Portfolio Fit module's arithmetic, not an input).

Like `rv_quotes`, the validator reads the workbook through `preparation.prepare_source`, so it
sees exactly the stored lexemes `prepare` freezes. Numbers are `Decimal`s parsed from the stored
lexeme and compared exactly (`EXACT`), never floats.
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal
from itertools import pairwise
from pathlib import Path
from typing import ClassVar, Literal, cast
from urllib.parse import quote, unquote

from deploy_vii.contracts import Contract, Source, Span
from deploy_vii.inputs.rv_quotes import (
    CURRENCY,
    DAMAGED,
    FIX,
    IDENTIFIER,
    MEDIA_TYPE,
    SERIAL,
    Issue,
    ValidationReport,
    cell_letters,
    echo,
    iso_date,
    sheet_cells,
)
from deploy_vii.preparation import MAX_BYTES, SourceRequest, prepare_source

__all__ = ["MEDIA_TYPE", "Issue"]

TEMPLATE = "docs/templates/portfolio.template.xlsx"
README_SHEET = "README"
WORKBOOK_SHEET = "Mandate"  # the sheet a workbook-level issue names
PCT_NAV = "% NAV"
SECTOR_ID = "SECTOR"
STRATEGIES = ("CLO", "Indexed Loans", "Indexed HY", "Other")
SECTIONS = (
    "Strategy",
    "Key Parties",
    "Capital Structure",
    "Mandate Constraints",
    "Liquidity Terms",
    "Fees",
    "Reporting",
)
STATUSES = ("Pass", "Watch", "Breach")
BREACH_TYPES = ("Hard", "Soft")
SCOPES = (
    "issuer",
    "rating_bucket",
    "sector",
    "seniority",
    "instrument",
    "duration",
    "diversification",
    "yield",
    "pricing",
    "covenant",
    "esg",
    "other",
)
TOLERANCE = Decimal("0.01")  # stated headroom against limit minus current value
WATCH_SHARE = Decimal("0.1")  # Watch is allowed while headroom is under 10 % of the limit
RATING_SUM = (Decimal("99.0"), Decimal("101.0"))
# The checks of sums and shares (owner, 2026-11-15: "check data first likely incorrect sums and
# values"; ruling 2026-11-15-full-assessment-portfolio-workbook). A distribution of NAV
# (Rating_Distribution, Maturity_Profile) adds to `RATING_SUM`; a part of NAV (Sector_Exposure,
# Top_Holdings, Holdings_Detail) adds to at most its upper end. Shares are stored to two decimals,
# so a share recomputed from amounts is compared to within `TOLERANCE` and a sum of n stored
# shares to within n times `SHARE_ROUNDING`, half a unit in the second decimal.
SHARE_ROUNDING = Decimal("0.005")
FRACTION_SUM = (Decimal("0.99"), Decimal("1.01"))  # a distribution entered as fractions of 1
HUNDRED = Decimal(100)
PRICE_RANGE = (Decimal(1), Decimal(150))  # market value per 100 of par, outside: a unit mix-up
STALE_DAYS = 30  # the workbook's as_of may be at most this many days before the run's as-of date
TOP_TEN = 10
TOP10_METRIC = "top10_pct_nav"
SHOWN = Decimal("0.0001")  # a recomputed share is shown to four decimals; compared exactly
NON_NEGATIVE = frozenset({"pct_nav", "limit_pct_nav", "limit", "current_value"})
POSITIVE = frozenset({"par", "market_value"})
MAX_NUMBER = 40  # characters of a number lexeme
# A plain decimal with at most a two-digit exponent: with `MAX_NUMBER` characters every value
# lies within 1e-140..1e140, so `EXACT` adds, subtracts and takes a tenth without rounding.
NUMBER = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]{1,2})?$")
EXACT = Context(prec=2000, Emax=9999, Emin=-9999)
CONTROL_ID = re.compile(r"^[A-Z]+-[0-9]{2}$")
TOTAL = re.compile(r"\b(?:sub)?total\b")
# Columns whose numbers are percent of NAV, always or on a `% NAV` Compliance_Monitor row. A
# numeric cell Excel shows as a percentage stores the fraction (2.5 % is stored 0.025).
PCT_COLUMNS = frozenset({"pct_nav", "limit_pct_nav", "headroom_pct_nav"})
PCT_NAV_ROW_COLUMNS = frozenset({"limit", "current_value", "headroom", "value"})
PERCENT_FORMATS = frozenset({"builtin:9", "builtin:10"})  # 0% and 0.00%
LITERAL = re.compile(r'"[^"]*"|\\.')  # quoted text or an escaped character in a format code

DATE_FIX = "enter the date as text YYYY-MM-DD (format the column as Text so Excel keeps it)"
PCT_FIX = "enter the share of NAV in percent as a plain number (2.5 means 2.5 % NAV)"
COUNT_FIX = "enter the number of issuers as a whole number of at least 0, e.g. 12"
RANK_FIX = "number the holdings 1, 2, 3 and so on, with no gaps or repeats"
STATUS_FIX = "enter Pass, Watch or Breach"
ISSUER_FIX = "enter the issuer's name"
INSTRUMENT_FIX = "describe the instrument, e.g. Term Loan B due 2030"
RATING_FIX = "enter the rating as reported, e.g. B2 / B"
SECTOR_FIX = "enter the sector's name"
UNIT_FIX = "enter % NAV, or the Mandate nav_currency code (e.g. USD) for an amount limit"
SHEET_LIST = (
    "Mandate, Exposure_Summary, Rating_Distribution, Sector_Exposure, Top_Holdings, "
    "Maturity_Profile, Compliance_Monitor, Holdings_Detail (optional) and README (optional)"
)
RULE_FIX: Mapping[str, str] = {
    "number": FIX["number"],
    "long": "enter the number with at most 40 characters (Excel keeps 15 significant digits)",
    "formula": FIX["formula"],
    "read": FIX["read"],
    "workbook": FIX["workbook"],
    "damaged": FIX["damaged"],
    "unknown_sheet": f"delete the sheet or move it to another workbook; keep only {SHEET_LIST}",
    "order": f"order the sheets as in {TEMPLATE}: {SHEET_LIST}",
    "duplicate": "keep one row per {key}, or correct the repeated value",
    "total": "leave out total and subtotal rows; Python adds the rows up",
    "nav_value": "enter the fund's NAV, a number above 0",
    "nav_currency": FIX["currency"],
    "strategy": "enter one of CLO, Indexed Loans, Indexed HY or Other",
    "exposure_nav": "enter the same NAV on Exposure_Summary and Mandate",
    "exposure_unit": "enter the nav row's unit as the Mandate nav_currency, e.g. USD",
    "exposure_missing": (
        "add a row: metric nav, value the fund's NAV (the Mandate nav), unit the "
        "nav_currency, as_of the NAV date"
    ),
    "one_pct_nav": "delete the one_pct_nav row; Python computes 1 % of NAV from nav",
    "rating_sum": "correct the percentages, or add a row Unallocated with the remainder of NAV",
    "maturity_sum": "correct the percentages, or add a row Unknown with the remainder of NAV",
    "fraction": "enter each share in percent of NAV: 2.5 means 2.5 % NAV, not 0.025",
    "part_sum": (
        "correct the percentages: these rows are parts of NAV and cannot add to more than all of it"
    ),
    "holding_share": (
        "enter market_value / nav x 100, or correct market_value or the Mandate nav (both in "
        "the same unit and currency)"
    ),
    "price": (
        "enter par and market_value in the same unit and currency (both in units, not thousands)"
    ),
    "rank_order": "rank the holdings from the largest share of NAV down",
    "top_detail": (
        "enter the same share of NAV on Top_Holdings and Holdings_Detail, or correct the one that "
        "is wrong"
    ),
    "top10": (
        "correct top10_pct_nav or the Top_Holdings percentages: the ten largest holdings add to "
        "top10_pct_nav"
    ),
    "sector_holdings": (
        "correct the sector's pct_nav or the holdings' sector or pct_nav: the holdings in a "
        "sector cannot add to more than the sector"
    ),
    "sector_row": (
        "enter the same figure on Compliance_Monitor and Sector_Exposure, or correct the one "
        "that is wrong"
    ),
    "amount_nav": (
        "enter the current value in the Mandate nav_currency and the same unit as nav (units, "
        "not thousands), or correct it"
    ),
    "metric_currency": (
        "enter the amount in the Mandate nav_currency (an amount in another currency is not "
        "comparable with NAV); write a unit that is not a currency in lower case, e.g. bps"
    ),
    "metric_as_of": "enter the metric as at the Mandate as_of date, or correct the date",
    "checked_before": "check the row again at the Mandate as_of date and enter that date",
    "matured": "delete the matured position, or correct its maturity date",
    "after_run": "enter the date the figures were measured, on or before the run's as-of date",
    "stale": (
        f"supply the workbook as at a date at most {STALE_DAYS} days before the run's as-of date"
    ),
    "negative_amount": "enter a number of at least 0: a limit or an exposure is never negative",
    "not_positive": "enter a number above 0",
    "ranks": RANK_FIX,
    "headroom": "enter limit minus current_value, or correct limit or current_value",
    "sector_headroom": "enter limit_pct_nav minus pct_nav, or correct the limit or the exposure",
    "sector_headroom_alone": "enter limit_pct_nav, or leave headroom_pct_nav empty",
    "sector_status_alone": "enter limit_pct_nav, or leave status empty",
    "breach": "enter Breach, or correct the values: a current value above its limit is a breach",
    "not_breach": (
        "enter Pass or Watch, or correct the values: only a current value above its limit is "
        "a breach"
    ),
    "watch": "enter Pass: Watch is for headroom under 10 % of the limit",
    "percent": "format the cell as General and enter 2.5 for 2.5 % NAV",
    "negative": "enter the share of NAV as a number of at least 0; a short position is not a share",
    "hidden": "unhide the sheet, row or column, or delete it: hidden cells are not read as data",
    "error_cell": "enter the real value in place of the error, or leave an optional cell empty",
    "boolean_cell": "enter text or a plain number, not TRUE or FALSE",
}
REQUIRED_FIELDS: Mapping[tuple[str, str], str] = {
    ("Strategy", "fund_name"): (
        "add a row: section Strategy, field fund_name, value the fund's name"
    ),
    ("Strategy", "strategy"): (
        "add a row: section Strategy, field strategy, value CLO, Indexed Loans, Indexed HY or Other"
    ),
    ("Capital Structure", "nav"): (
        "add a row: section Capital Structure, field nav, value the fund's NAV as a plain number"
    ),
    ("Capital Structure", "nav_currency"): (
        "add a row: section Capital Structure, field nav_currency, value the NAV's three-letter "
        "currency code, e.g. USD"
    ),
    ("Reporting", "as_of"): (
        "add a row: section Reporting, field as_of, value the NAV and compliance date as text "
        "YYYY-MM-DD"
    ),
}

Kind = Literal["text", "number", "count", "rank", "date", "choice", "identifier", "id", "unit"]


@dataclass(frozen=True)
class Column:
    name: str
    kind: Kind
    fix: str
    required: bool = True
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class Sheet:
    name: str
    columns: tuple[Column, ...]
    noun: str
    key: tuple[str, ...]
    label: str | None = None  # the column whose total rows are refused
    optional: bool = False

    def letter(self, column: str) -> str:
        return cell_letters(self.names.index(column) + 1)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    def header_fix(self) -> str:
        last = self.letter(self.names[-1])
        return (
            f"set row 1 to exactly: {', '.join(self.names)} (A1 to {last}1, nothing after {last}1)"
        )

    def fixes(self) -> tuple[str, ...]:
        return (
            self.header_fix(),
            f"copy the header row of {self.name} from {TEMPLATE} and add one row per {self.noun}",
            f"add one row per {self.noun}, starting in row 2",
            f"add the sheet {self.name} with its header row, as in {TEMPLATE}",
        )


def text(name: str, fix: str, *, required: bool = True) -> Column:
    return Column(name, "text", fix, required)


def choice(name: str, choices: tuple[str, ...], *, required: bool = True) -> Column:
    return Column(name, "choice", f"enter {alternatives(choices)}", required, choices)


def alternatives(choices: Sequence[str]) -> str:
    listed = ", ".join(choices[:-1]) + " or " + choices[-1]
    return listed if len(choices) <= 3 else "one of " + listed


def pct(name: str = "pct_nav") -> Column:
    return Column(name, "number", PCT_FIX)


MANDATE = Sheet(
    "Mandate",
    (
        choice("section", SECTIONS),
        text("field", "enter the field's name, e.g. fund_name"),
        text("value", "enter the field's value, or delete the row"),
        text("notes", "", required=False),
    ),
    "mandate field",
    ("section", "field"),
)
EXPOSURE = Sheet(
    "Exposure_Summary",
    (
        text("metric", "enter the metric's name, e.g. nav"),
        Column("value", "number", "enter the metric's value as a plain number"),
        text("unit", "enter the unit, e.g. USD, % NAV, years or count"),
        Column("as_of", "date", DATE_FIX),
    ),
    "metric",
    ("metric",),
)
RATINGS = Sheet(
    "Rating_Distribution",
    (
        text("rating_bucket", "enter the rating bucket, e.g. B or Unrated"),
        pct(),
        Column("issuers", "count", COUNT_FIX),
    ),
    "rating bucket",
    ("rating_bucket",),
    label="rating_bucket",
)
SECTORS = Sheet(
    "Sector_Exposure",
    (
        text("sector", SECTOR_FIX),
        pct(),
        Column("issuers", "count", COUNT_FIX),
        Column("limit_pct_nav", "number", PCT_FIX, required=False),
        Column("headroom_pct_nav", "number", PCT_FIX, required=False),
        choice("status", STATUSES, required=False),
    ),
    "sector",
    ("sector",),
    label="sector",
)
TOP_HOLDINGS = Sheet(
    "Top_Holdings",
    (
        Column("rank", "rank", RANK_FIX),
        text("issuer", ISSUER_FIX),
        text("instrument", INSTRUMENT_FIX),
        pct(),
        text("rating", RATING_FIX),
    ),
    "holding",
    ("rank",),
)
MATURITIES = Sheet(
    "Maturity_Profile",
    (text("bucket", "enter the maturity bucket, e.g. 3-5 Years"), pct()),
    "maturity bucket",
    ("bucket",),
    label="bucket",
)
COMPLIANCE = Sheet(
    "Compliance_Monitor",
    (
        Column(
            "id",
            "id",
            "enter an id such as C-01 (capital letters, a hyphen, two digits), or SECTOR for "
            "the sector-limit row",
        ),
        text("constraint_category", "enter the constraint category, e.g. Single Name"),
        text("parameter", "describe the constraint, e.g. Max single issuer exposure"),
        Column(
            "limit",
            "number",
            "enter the limit as a plain number in limit_unit (2.5 means 2.5 % NAV)",
        ),
        Column("limit_unit", "unit", UNIT_FIX),
        choice("breach_type", BREACH_TYPES),
        choice("scope", SCOPES),
        text("source_document", "enter the document that sets the limit, e.g. Indenture s7.11"),
        Column(
            "current_value", "number", "enter the current exposure as a plain number in limit_unit"
        ),
        Column("headroom", "number", "enter limit minus current_value as a plain number"),
        choice("status", STATUSES),
        Column("last_checked", "date", DATE_FIX),
        text("checked_by", "enter who checked the row, e.g. analyst"),
    ),
    "constraint",
    ("id",),
)
HOLDINGS = Sheet(
    "Holdings_Detail",
    (
        text("issuer", ISSUER_FIX),
        text("instrument", INSTRUMENT_FIX),
        Column("facility_id", "identifier", FIX["facility_id"]),
        Column("par", "number", "enter the par amount as a plain number"),
        Column("market_value", "number", "enter the market value as a plain number"),
        pct(),
        text("rating", RATING_FIX),
        text("sector", SECTOR_FIX),
        text("seniority", "enter the seniority, e.g. 1st Lien"),
        Column("maturity", "date", DATE_FIX),
    ),
    "position",
    ("facility_id",),
    optional=True,
)
SHEETS = (MANDATE, EXPOSURE, RATINGS, SECTORS, TOP_HOLDINGS, MATURITIES, COMPLIANCE, HOLDINGS)
BY_NAME = {sheet.name: sheet for sheet in SHEETS}
# Every fixed-text fix the validator can print (the README documents each verbatim). The
# per-sheet structure fixes (`Sheet.fixes`) and the repeated-key fix are patterns over a sheet's
# header, noun or key; the README documents those patterns.
FIXES = tuple(
    dict.fromkeys(
        fix
        for fix in (
            *RULE_FIX.values(),
            *REQUIRED_FIELDS.values(),
            *(column.fix for sheet in SHEETS for column in sheet.columns),
        )
        if fix and "{" not in fix
    )
)


class PortfolioReport(ValidationReport):
    """`rows` counts data rows on every contract sheet; `sheets` the contract sheets present
    (README excluded); `compliance_rows` the Compliance_Monitor data rows."""

    sheets: int
    compliance_rows: int

    def lines(self) -> tuple[str, ...]:
        summary = (
            f"OK: {self.sheets} sheets, {self.compliance_rows} compliance rows"
            if self.ok
            else f"FAILED: {len(self.issues)} issues"
        )
        return (*(issue.render() for issue in self.issues), summary)


class PortfolioRefused(ValueError):
    """`portfolio_facts` on a workbook the validator does not pass; `report` says why."""

    def __init__(self, report: PortfolioReport) -> None:
        super().__init__(f"portfolio workbook refused: {len(report.issues)} issues")
        self.report = report


def cell_locator(sheet: str, column: str, row: int) -> str:
    return f"sheet:{quote(sheet, safe='')}!{BY_NAME[sheet].letter(column)}{row}"


class SheetRow(Contract):
    """One data row; `row` is its worksheet row number, so `locator` names the frozen span."""

    SHEET: ClassVar[str]
    row: int

    def locator(self, column: str) -> str:
        return cell_locator(self.SHEET, column, self.row)


class MandateField(SheetRow):
    SHEET: ClassVar[str] = MANDATE.name
    section: str
    field: str
    value: str
    notes: str | None


class Mandate(Contract):
    fund_name: str
    strategy: Literal["CLO", "Indexed Loans", "Indexed HY", "Other"]
    nav: Decimal
    nav_currency: str
    as_of: date
    fields: tuple[MandateField, ...]

    def locator(self, name: str) -> str:
        """The value cell of a required field (`fund_name`, `strategy`, `nav`, `nav_currency`,
        `as_of`)."""
        (section,) = (section for section, field in REQUIRED_FIELDS if field == name)
        (item,) = (item for item in self.fields if (item.section, item.field) == (section, name))
        return item.locator("value")


class Exposure(SheetRow):
    SHEET: ClassVar[str] = EXPOSURE.name
    metric: str
    value: Decimal
    unit: str
    as_of: date


class RatingBucket(SheetRow):
    SHEET: ClassVar[str] = RATINGS.name
    rating_bucket: str
    pct_nav: Decimal
    issuers: int


Status = Literal["Pass", "Watch", "Breach"]


class SectorExposure(SheetRow):
    SHEET: ClassVar[str] = SECTORS.name
    sector: str
    pct_nav: Decimal
    issuers: int
    limit_pct_nav: Decimal | None
    headroom_pct_nav: Decimal | None
    status: Status | None


class TopHolding(SheetRow):
    SHEET: ClassVar[str] = TOP_HOLDINGS.name
    rank: int
    issuer: str
    instrument: str
    pct_nav: Decimal
    rating: str


class MaturityBucket(SheetRow):
    SHEET: ClassVar[str] = MATURITIES.name
    bucket: str
    pct_nav: Decimal


Scope = Literal[
    "issuer",
    "rating_bucket",
    "sector",
    "seniority",
    "instrument",
    "duration",
    "diversification",
    "yield",
    "pricing",
    "covenant",
    "esg",
    "other",
]


class ComplianceRow(SheetRow):
    """One Compliance_Monitor row. Every limit is a maximum (there is no direction field).
    Consumers compute room as `limit - current_value` and never read `headroom` for it."""

    SHEET: ClassVar[str] = COMPLIANCE.name
    id: str
    constraint_category: str
    parameter: str
    limit: Decimal
    limit_unit: str
    breach_type: Literal["Hard", "Soft"]
    scope: Scope
    source_document: str
    current_value: Decimal
    headroom: Decimal
    """The sheet's stated headroom, never used for room: checked to within 0.01 of
    `limit - current_value` on `% NAV` rows and unchecked on currency rows."""
    status: Status
    last_checked: date
    checked_by: str


class Holding(SheetRow):
    SHEET: ClassVar[str] = HOLDINGS.name
    issuer: str
    instrument: str
    facility_id: str
    par: Decimal
    market_value: Decimal
    pct_nav: Decimal
    rating: str
    sector: str
    seniority: str
    maturity: date


class PortfolioFacts(Contract):
    """The validated workbook as typed rows, in sheet row order; `holdings` is None when the
    optional Holdings_Detail sheet is absent."""

    mandate: Mandate
    exposures: tuple[Exposure, ...]
    ratings: tuple[RatingBucket, ...]
    sectors: tuple[SectorExposure, ...]
    top_holdings: tuple[TopHolding, ...]
    maturities: tuple[MaturityBucket, ...]
    compliance: tuple[ComplianceRow, ...]
    holdings: tuple[Holding, ...] | None


Value = str | Decimal | int | date


@dataclass
class Row:
    """One data row: `raw` holds every column's stripped lexeme, `values` the typed value of
    each non-empty cell without a finding, `flagged` the columns with a finding."""

    number: int
    raw: dict[str, str]
    values: dict[str, Value] = field(default_factory=dict)
    flagged: set[str] = field(default_factory=set)

    def ok(self, *names: str) -> bool:
        return all(name in self.values for name in names)

    def number_of(self, name: str) -> Decimal:
        return cast(Decimal, self.values[name])


@dataclass
class Table:
    sheet: Sheet
    rows: list[Row]


@dataclass
class Findings:
    file: str
    issues: list[Issue] = field(default_factory=list)

    def add(self, sheet: str, cell: str, problem: str, fix: str) -> None:
        self.issues.append(Issue(file=self.file, sheet=sheet, cell=cell, problem=problem, fix=fix))


@dataclass(frozen=True)
class NavBasis:
    """The Mandate's NAV and currency when valid, for the cross-sheet rules."""

    nav: Decimal | None = None
    nav_cell: str = ""
    currency: str | None = None
    as_of: date | None = None
    as_of_cell: str = ""


def report(
    rows: int, issues: Sequence[Issue], sheets: int = 0, compliance_rows: int = 0
) -> PortfolioReport:
    return PortfolioReport(
        ok=not issues,
        rows=rows,
        issues=tuple(issues),
        sheets=sheets,
        compliance_rows=compliance_rows,
    )


def validate_portfolio(path: Path, *, run_date: date | None = None) -> PortfolioReport:
    """Validate one user-supplied portfolio workbook; every finding is an `Issue` with a fix.
    With `run_date` (the run's as-of date) its dates are also checked against it."""
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except OSError as error:
        reason = error.strerror or type(error).__name__
        issue = Issue(
            file=path.name,
            sheet=WORKBOOK_SHEET,
            cell="A1",
            problem=f"cannot read the file: {reason}",
            fix=RULE_FIX["read"],
        )
        return report(0, (issue,))
    return validate_portfolio_bytes(path.name, raw, run_date=run_date)


def validate_portfolio_bytes(
    file: str, raw: bytes, *, run_date: date | None = None
) -> PortfolioReport:
    """`validate_portfolio` on bytes already read; `file` names the workbook in each issue."""
    request = SourceRequest(source_id="portfolio", path=file, media_type=MEDIA_TYPE)
    try:
        source = prepare_source(request, raw)
    except DAMAGED as error:
        # As in `rv_quotes`: CPython's zipfile raises these for a corrupt deflate stream, a
        # truncated member and a ZipCrypto-encrypted member, and `prepare_source` does not
        # catch them, so `prepare` would stop on the same file. Reported, never swallowed.
        kind = type(error).__name__
        kind = kind if type(error).__module__ == "builtins" else f"{type(error).__module__}.{kind}"
        problem = (
            "prepare cannot read this file as an OOXML workbook: damaged ZIP member "
            f"({kind}: {error})"
        )
        findings = Findings(file)
        findings.add(WORKBOOK_SHEET, "A1", problem, RULE_FIX["damaged"])
        return report(0, findings.issues)
    return read(file, source, run_date)[0]


def portfolio_facts(source: Source) -> PortfolioFacts:
    """The typed rows of a prepared portfolio source (a pack `Source` or `prepare_source`'s
    result). Pure: reads only the source's spans and coverage. Raises `PortfolioRefused`, with
    the validator's report, unless the workbook passes.

    `ComplianceRow.headroom` and `SectorExposure.headroom_pct_nav` are the stated figures:
    checked to within 0.01 on `% NAV` rows and unchecked on currency rows. A consumer computes
    room as `limit - current_value` (or `limit_pct_nav - pct_nav`) and never reads headroom."""
    result, typed_facts = read(source.name, source)
    if typed_facts is None:
        raise PortfolioRefused(result)
    return typed_facts


def read(
    file: str, source: Source, run_date: date | None = None
) -> tuple[PortfolioReport, PortfolioFacts | None]:
    findings = Findings(file)
    if source.status != "ready" or source.extraction_status == "blocked" or not source.coverage:
        # `prepare_source` failed to extract: the same refusal `prepare` would freeze.
        problem = f"prepare cannot read this file as an OOXML workbook: {source.limitation}"
        findings.add(WORKBOOK_SHEET, "A1", problem, RULE_FIX["workbook"])
        return report(0, findings.issues), None
    names = []
    for item in source.coverage:
        name = unquote(item.locator.removeprefix("sheet:"))
        if not name or item.locator != "sheet:" + quote(name, safe=""):
            findings.add(
                WORKBOOK_SHEET,
                "A1",
                "coverage locator is not a canonical sheet URI",
                RULE_FIX["workbook"],
            )
        elif name in BY_NAME and item.status == "unreadable":
            findings.add(
                name,
                "A1",
                f"sheet {name} coverage is unreadable: {item.limitation}",
                RULE_FIX["workbook"],
            )
        elif name in BY_NAME and item.status == "empty":
            findings.add(name, "A1", f"sheet {name} is empty", BY_NAME[name].fixes()[1])
        names.append(name)
    grids, locator_issues = sheet_cells(source.spans, file)
    findings.issues.extend(locator_issues)
    if findings.issues:
        return report(0, findings.issues), None
    sheet_list_findings(names, findings)
    tables: dict[str, Table] = {}
    for sheet in SHEETS:
        if sheet.name in names:
            table = load_table(sheet, grids.get(sheet.name, {}), findings)
            if table is not None:
                tables[sheet.name] = table
                SHEET_RULES[sheet.name](table, tables, findings)
    workbook_rules(tables, findings, run_date)
    present = sum(1 for sheet in SHEETS if sheet.name in names)
    compliance = len(tables[COMPLIANCE.name].rows) if COMPLIANCE.name in tables else 0
    rows = sum(len(table.rows) for table in tables.values())
    result = report(rows, findings.issues, present, compliance)
    return result, (build_facts(tables) if result.ok else None)


def sheet_list_findings(names: Sequence[str], findings: Findings) -> None:
    """Unknown, missing and out-of-order sheets."""
    known = {*BY_NAME, README_SHEET}
    for name in names:
        if name not in known:
            findings.add(name, "A1", f"unknown sheet '{echo(name)}'", RULE_FIX["unknown_sheet"])
    found = ", ".join(echo(name) for name in names) or "none"
    for sheet in SHEETS:
        if not sheet.optional and sheet.name not in names:
            problem = f"no sheet named {sheet.name} (found: {found})"
            findings.add(sheet.name, "A1", problem, sheet.fixes()[3])
    order = [name for name in names if name in BY_NAME]
    for before, after in pairwise(order):
        if SHEETS.index(BY_NAME[after]) < SHEETS.index(BY_NAME[before]):
            problem = f"sheet {after} comes after {before}"
            findings.add(after, "A1", problem, RULE_FIX["order"])
            break


def stored(grid: Mapping[tuple[int, int], Span], column: int, row: int) -> str:
    span = grid.get((column, row))
    return "" if span is None else span.text.strip()


def load_table(
    sheet: Sheet, grid: Mapping[tuple[int, int], Span], findings: Findings
) -> Table | None:
    """The sheet's parsed rows, or None (with one issue) when it is empty, its header is not
    the template's or it has no data rows."""
    width = len(sheet.columns)
    if not any(span.text.strip() for span in grid.values()):
        findings.add(sheet.name, "A1", f"sheet {sheet.name} is empty", sheet.fixes()[1])
        return None
    if hidden_findings(sheet, grid, findings):
        return None
    header = header_problem(sheet, grid)
    if header is not None:
        findings.add(sheet.name, *header, sheet.header_fix())
        return None
    numbers = sorted(
        {
            row
            for _, row in grid
            if row > 1 and any(stored(grid, column, row) for column in range(1, width + 1))
        }
    )
    if not numbers:
        findings.add(sheet.name, "A2", "no rows below the header", sheet.fixes()[2])
        return None
    rows = [parse_row(sheet, grid, number, findings) for number in numbers]
    key_findings(sheet, rows, findings)
    return Table(sheet, rows)


def hidden_findings(sheet: Sheet, grid: Mapping[tuple[int, int], Span], findings: Findings) -> bool:
    """Refuse hidden content, which is a stale or filtered row a reader of the workbook does not
    see: one issue for a hidden sheet, else one per row holding a hidden cell. True if any."""
    filled = [(cell, span) for cell, span in grid.items() if span.text.strip()]
    hidden = [cell for cell, span in filled if span.hidden]
    if not hidden:
        return False
    if len(hidden) == len(filled):
        message = f"sheet {sheet.name} is hidden"
        findings.add(sheet.name, "A1", message, RULE_FIX["hidden"])
        return True
    for row in sorted({row for _, row in hidden}):
        column = min(column for column, found in hidden if found == row)
        message = f"row {row} holds hidden cells"
        findings.add(sheet.name, f"{cell_letters(column)}{row}", message, RULE_FIX["hidden"])
    return True


def header_problem(sheet: Sheet, grid: Mapping[tuple[int, int], Span]) -> tuple[str, str] | None:
    """The first header cell that is not the template's, as (cell, problem)."""
    for column, expected in enumerate(sheet.names, 1):
        found = stored(grid, column, 1)
        if found != expected:
            shown = f"'{echo(found)}'" if found else "empty"
            return f"{cell_letters(column)}1", f"header is {shown}, expected '{expected}'"
    last = cell_letters(len(sheet.columns))
    for column in sorted(column for column, row in grid if row == 1 and column > len(sheet.names)):
        found = stored(grid, column, 1)
        if found:
            return (
                f"{cell_letters(column)}1",
                f"header is '{echo(found)}', expected nothing after {last}1",
            )
    return None


def parse_row(
    sheet: Sheet, grid: Mapping[tuple[int, int], Span], number: int, findings: Findings
) -> Row:
    row = Row(number, {})
    for index, column in enumerate(sheet.columns, 1):
        span = grid.get((index, number))
        value = "" if span is None else span.text.strip()
        row.raw[column.name] = value
        cell = f"{cell_letters(index)}{number}"
        if span is not None and span.formula is not None:
            message = (
                f"{column.name} holds a formula; prepare freezes stored values and never "
                "recalculates"
            )
            findings.add(sheet.name, cell, message, RULE_FIX["formula"])
            row.flagged.add(column.name)
            continue
        if span is not None and span.data_type in ("e", "b"):
            # An Excel error (`t="e"`, e.g. #N/A) or a TRUE/FALSE cell (`t="b"`, stored 1 or
            # 0) is not a value in any column.
            if span.data_type == "e":
                message = f"{column.name} holds the Excel error '{echo(value)}'"
                findings.add(sheet.name, cell, message, RULE_FIX["error_cell"])
            else:
                message = f"{column.name} holds a TRUE/FALSE cell"
                findings.add(sheet.name, cell, message, RULE_FIX["boolean_cell"])
            row.flagged.add(column.name)
            continue
        if not value:
            if column.required:
                findings.add(sheet.name, cell, f"{column.name} is empty", column.fix)
                row.flagged.add(column.name)
            continue
        parsed, problem = parse_value(column, value)
        if problem is None:
            row.values[column.name] = parsed
        else:
            findings.add(sheet.name, cell, *problem)
            row.flagged.add(column.name)
    if sheet.label is not None and sheet.label in row.values:
        label = row.raw[sheet.label]
        if TOTAL.search(label.casefold()):
            message = f"{sheet.label} '{echo(label)}' is a total row"
            findings.add(
                sheet.name, f"{sheet.letter(sheet.label)}{number}", message, RULE_FIX["total"]
            )
            del row.values[sheet.label]
            row.flagged.add(sheet.label)
    percent_findings(sheet, grid, row, findings)
    return row


def percent_formatted(span: Span) -> bool:
    """A numeric cell whose number format scales it by 100 for display: builtin 9 or 10, or a
    custom code with a `%` outside quoted text and escapes (`0.00"%"` only shows a sign)."""
    code = span.number_format
    if span.data_type != "n" or code is None:
        return False
    if code.startswith("builtin:"):
        return code in PERCENT_FORMATS
    return "%" in LITERAL.sub("", code)


def percent_findings(
    sheet: Sheet, grid: Mapping[tuple[int, int], Span], row: Row, findings: Findings
) -> None:
    """Refuse percent-formatted numbers in percent columns: one issue per cell, and the value
    is dropped so no rule computes with a fraction."""
    pct_nav_row = PCT_NAV in (row.raw.get("limit_unit"), row.raw.get("unit"))
    for index, column in enumerate(sheet.columns, 1):
        name = column.name
        span = grid.get((index, row.number))
        scaled = name in PCT_COLUMNS or (pct_nav_row and name in PCT_NAV_ROW_COLUMNS)
        if span is not None and scaled and name in row.values and percent_formatted(span):
            message = f"{name} '{echo(row.raw[name])}' is formatted as a percentage"
            findings.add(
                sheet.name, f"{cell_letters(index)}{row.number}", message, RULE_FIX["percent"]
            )
            del row.values[name]
            row.flagged.add(name)


def parse_number(name: str, value: str) -> tuple[Decimal, tuple[str, str] | None]:
    if not NUMBER.match(value):
        return Decimal(0), (f"{name} '{echo(value)}' is not a number", RULE_FIX["number"])
    if len(value) > MAX_NUMBER:
        problem = f"{name} '{echo(value)}' is longer than {MAX_NUMBER} characters"
        return Decimal(0), (problem, RULE_FIX["long"])
    return Decimal(value), None


def range_problem(name: str, shown: str, number: Decimal) -> tuple[str, str] | None:
    """A share, limit or exposure below 0, or a par amount or market value not above 0."""
    if name in NON_NEGATIVE and number < 0:
        fix = RULE_FIX["negative" if name == "pct_nav" else "negative_amount"]
        return f"{name} '{shown}' is negative", fix
    if name in POSITIVE and number <= 0:
        return f"{name} '{shown}' is not above 0", RULE_FIX["not_positive"]
    return None


def parse_date(name: str, value: str) -> tuple[date, tuple[str, str] | None]:
    if iso_date(value):
        return date.fromisoformat(value), None
    kind = "an Excel date serial, not" if SERIAL.match(value) else "not"
    return date.min, (f"{name} '{echo(value)}' is {kind} an ISO date YYYY-MM-DD", DATE_FIX)


def parse_value(column: Column, value: str) -> tuple[Value, tuple[str, str] | None]:  # noqa: PLR0911 - nine returns at base, unchanged
    """A non-empty stored lexeme as its typed value, or the (problem, fix) it fails with."""
    name, shown = column.name, echo(value)
    if column.kind == "number":
        number, problem = parse_number(name, value)
        return number, problem or range_problem(name, shown, number)
    if column.kind in ("count", "rank"):
        least = 0 if column.kind == "count" else 1
        number, problem = parse_number(name, value)
        if (
            problem is None
            and number == number.to_integral_value(context=EXACT)
            and number >= least
        ):
            return int(number), None
        return 0, (f"{name} '{shown}' is not a whole number of at least {least}", column.fix)
    if column.kind == "date":
        return parse_date(name, value)
    if column.kind == "choice" and value not in column.choices:
        return value, (f"{name} '{shown}' is not {alternatives(column.choices)}", column.fix)
    if column.kind == "identifier" and not IDENTIFIER.match(value):
        message = f"{name} '{shown}' has characters other than letters, digits, - and _"
        return value, (message, column.fix)
    if column.kind == "id" and not (CONTROL_ID.match(value) or value == SECTOR_ID):
        return value, (f"{name} '{shown}' is not of the form C-01 or SECTOR", column.fix)
    if column.kind == "unit" and not (value == PCT_NAV or CURRENCY.match(value)):
        message = f"{name} '{shown}' is not % NAV or a three-letter currency code"
        return value, (message, column.fix)
    return value, None


def key_findings(
    sheet: Sheet, rows: Sequence[Row], findings: Findings, names: tuple[str, ...] = ()
) -> None:
    """A repeated key (the sheet's, or `names`) is one issue on the later row; rows with an
    invalid key cell are not also duplicates."""
    names = names or sheet.key
    seen: dict[tuple[Value, ...], int] = {}
    key = " and ".join(names)
    first, last = sheet.letter(names[0]), sheet.letter(names[-1])
    for row in rows:
        if not row.ok(*names):
            continue
        values = tuple(row.values[name] for name in names)
        if values in seen:
            cell = f"{first}{row.number}" + ("" if first == last else f":{last}{row.number}")
            problem = f"duplicates row {seen[values]} on {key}"
            findings.add(sheet.name, cell, problem, RULE_FIX["duplicate"].format(key=key))
        else:
            seen[values] = row.number


def nav_basis(tables: Mapping[str, Table]) -> NavBasis:
    table = tables.get(MANDATE.name)
    if table is None:
        return NavBasis()
    values = mandate_values(table)
    nav, currency, as_of = values.get("nav"), values.get("nav_currency"), values.get("as_of")
    return NavBasis(
        nav=nav[0] if nav is not None and isinstance(nav[0], Decimal) else None,
        nav_cell=f"Mandate!C{nav[1]}" if nav is not None else "",
        currency=currency[0] if currency is not None and isinstance(currency[0], str) else None,
        as_of=as_of[0] if as_of is not None and isinstance(as_of[0], date) else None,
        as_of_cell=f"Mandate!C{as_of[1]}" if as_of is not None else "",
    )


def mandate_values(table: Table) -> dict[str, tuple[Value, int]]:
    """Each valid required field's typed value and row number (the first row when repeated)."""
    values: dict[str, tuple[Value, int]] = {}
    for row in table.rows:
        pair = (row.raw["section"], row.raw["field"])
        if (
            pair in REQUIRED_FIELDS
            and row.ok("section", "field", "value")
            and pair[1] not in values
        ):
            parsed, problem = mandate_value(pair[1], row.raw["value"])
            if problem is None:
                values[pair[1]] = (parsed, row.number)
    return values


def mandate_value(name: str, value: str) -> tuple[Value, tuple[str, str] | None]:
    if name == "strategy" and value not in STRATEGIES:
        return value, (
            f"strategy '{echo(value)}' is not {alternatives(STRATEGIES)}",
            RULE_FIX["strategy"],
        )
    if name == "nav":
        nav, problem = parse_number(name, value)
        if problem is None and nav <= 0:
            problem = f"nav {echo(value)} is not above 0", RULE_FIX["nav_value"]
        return nav, problem
    if name == "nav_currency" and not CURRENCY.match(value):
        message = f"nav_currency '{echo(value)}' is not a three-letter ISO 4217 code"
        return value, (message, RULE_FIX["nav_currency"])
    if name == "as_of":
        return parse_date(name, value)
    return value, None


def mandate_rules(table: Table, tables: Mapping[str, Table], findings: Findings) -> None:
    present: set[tuple[str, str]] = set()
    for row in table.rows:
        pair = (row.raw["section"], row.raw["field"])
        if row.ok("section", "field"):
            present.add(pair)
        if pair in REQUIRED_FIELDS and row.ok("section", "field", "value"):
            _, problem = mandate_value(pair[1], row.raw["value"])
            if problem is not None:
                findings.add(MANDATE.name, f"C{row.number}", *problem)
    last = table.rows[-1].number
    for (section, name), fix in REQUIRED_FIELDS.items():
        if (section, name) not in present:
            findings.add(MANDATE.name, f"A{last + 1}", f"no {section} row with field {name}", fix)


def metric_findings(row: Row, basis: NavBasis, findings: Findings) -> None:
    """An Exposure_Summary row measured on another date than the Mandate as_of, or an amount in
    another currency than the Mandate nav_currency (the nav row's unit has its own rule)."""
    sheet, as_of = EXPOSURE.name, row.values.get("as_of")
    if basis.as_of is not None and isinstance(as_of, date) and as_of != basis.as_of:
        problem = (
            f"as_of {as_of} of {echo(row.raw['metric'])} is not the Mandate as_of "
            f"{basis.as_of} ({basis.as_of_cell}): the metric is from another date"
        )
        findings.add(sheet, f"D{row.number}", problem, RULE_FIX["metric_as_of"])
    unit = row.raw["unit"]
    if (
        row.raw["metric"] != "nav"
        and row.ok("unit")
        and CURRENCY.match(unit)
        and basis.currency is not None
        and unit != basis.currency
    ):
        problem = (
            f"unit {unit} of {echo(row.raw['metric'])} reads as a currency code other than the "
            f"Mandate nav_currency {basis.currency}: two currencies in one workbook's amounts"
        )
        findings.add(sheet, f"C{row.number}", problem, RULE_FIX["metric_currency"])


def exposure_rules(table: Table, tables: Mapping[str, Table], findings: Findings) -> None:
    basis = nav_basis(tables)
    sheet = EXPOSURE.name
    for row in table.rows:
        metric_findings(row, basis, findings)
    navs = [row for row in table.rows if row.raw["metric"] == "nav"]
    for row in table.rows:
        if row.raw["metric"] == "one_pct_nav":
            problem = "one_pct_nav is computed from nav and is not supplied"
            findings.add(sheet, f"A{row.number}", problem, RULE_FIX["one_pct_nav"])
    if not navs:
        last = table.rows[-1].number
        findings.add(sheet, f"A{last + 1}", "no metric nav", RULE_FIX["exposure_missing"])
        return
    nav = navs[0]
    if basis.nav is not None and nav.ok("value") and nav.number_of("value") != basis.nav:
        problem = (
            f"nav {echo(nav.raw['value'])} is not the Mandate nav {basis.nav} ({basis.nav_cell})"
        )
        findings.add(sheet, f"B{nav.number}", problem, RULE_FIX["exposure_nav"])
    if basis.currency is not None and nav.ok("unit") and nav.raw["unit"] != basis.currency:
        problem = (
            f"unit '{echo(nav.raw['unit'])}' of nav is not the Mandate nav_currency "
            f"{basis.currency}"
        )
        findings.add(sheet, f"C{nav.number}", problem, RULE_FIX["exposure_unit"])


def plain(value: Decimal) -> str:
    """An exact figure as a plain decimal, never in exponent form."""
    return f"{value:f}"


def rounded(value: Decimal) -> str:
    """A recomputed figure shown to four decimals; every comparison uses it exactly."""
    return plain(value.quantize(SHOWN, rounding=ROUND_HALF_EVEN, context=EXACT))


def sum_of(rows: Sequence[Row], name: str) -> Decimal:
    total = Decimal(0)
    for row in rows:
        total = EXACT.add(total, row.number_of(name))
    return total


def row_list(rows: Sequence[Row]) -> str:
    numbers = ", ".join(str(row.number) for row in rows)
    return f"row{'s' if len(rows) > 1 else ''} {numbers}"


def column_cells(sheet: Sheet, rows: Sequence[Row], name: str) -> str:
    letter = sheet.letter(name)
    return f"{letter}{rows[0].number}:{letter}{rows[-1].number}"


def distribution_findings(table: Table, fix: str, findings: Findings) -> None:
    """A distribution of NAV adds to 99 to 101 (`RATING_SUM`); one that adds to about 1 holds
    fractions. Skipped while a row's pct_nav has an issue: a missing share is never 0."""
    if not all(row.ok("pct_nav") for row in table.rows):
        return
    total = sum_of(table.rows, "pct_nav")
    low, high = RATING_SUM
    if low <= total <= high:
        return
    off = EXACT.subtract(total, HUNDRED)
    side = f"{plain(off)} more than 100" if off > 0 else f"{plain(off.copy_abs())} short of 100"
    problem = (
        f"pct_nav of the {len(table.rows)} rows sums to {plain(total)}, outside {low} to "
        f"{high} ({side})"
    )
    if FRACTION_SUM[0] <= total <= FRACTION_SUM[1]:
        problem += "; the shares look like fractions of 1"
        fix = RULE_FIX["fraction"]
    findings.add(table.sheet.name, column_cells(table.sheet, table.rows, "pct_nav"), problem, fix)


def part_findings(table: Table, findings: Findings) -> None:
    """Rows that are parts of NAV add to at most the upper end of `RATING_SUM`."""
    if not all(row.ok("pct_nav") for row in table.rows):
        return
    total, high = sum_of(table.rows, "pct_nav"), RATING_SUM[1]
    if total > high:
        problem = (
            f"pct_nav of the {len(table.rows)} rows sums to {plain(total)}, more than {high} "
            f"({plain(EXACT.subtract(total, HUNDRED))} more than all of NAV)"
        )
        cells = column_cells(table.sheet, table.rows, "pct_nav")
        findings.add(table.sheet.name, cells, problem, RULE_FIX["part_sum"])


def rating_rules(table: Table, tables: Mapping[str, Table], findings: Findings) -> None:
    distribution_findings(table, RULE_FIX["rating_sum"], findings)


def maturity_rules(table: Table, tables: Mapping[str, Table], findings: Findings) -> None:
    distribution_findings(table, RULE_FIX["maturity_sum"], findings)


def status_problem(row: Row, status: str, limit: str, current: str) -> tuple[str, str] | None:
    """Breach exactly when the current value exceeds the limit; Watch only while the headroom
    (limit minus current value, computed) is under 10 % of the limit."""
    value, ceiling = row.number_of(current), row.number_of(limit)
    state = row.raw[status]
    shown = f"{current} {echo(row.raw[current])}"
    bound = f"{limit} {echo(row.raw[limit])}"
    if value > ceiling and state != "Breach":
        return f"status '{state}' but {shown} exceeds {bound}", RULE_FIX["breach"]
    if value <= ceiling and state == "Breach":
        return f"status 'Breach' but {shown} does not exceed {bound}", RULE_FIX["not_breach"]
    room = EXACT.subtract(ceiling, value)
    if state == "Watch" and room >= EXACT.multiply(ceiling, WATCH_SHARE):
        return f"status 'Watch' but the headroom {room} is at least 10 % of {bound}", RULE_FIX[
            "watch"
        ]
    return None


def headroom_problem(
    row: Row, headroom: str, limit: str, current: str, fix: str
) -> tuple[str, str] | None:
    room = EXACT.subtract(row.number_of(limit), row.number_of(current))
    if EXACT.abs(EXACT.subtract(row.number_of(headroom), room)) <= TOLERANCE:
        return None
    problem = (
        f"{headroom} {echo(row.raw[headroom])} is not {limit} {echo(row.raw[limit])} minus "
        f"{current} {echo(row.raw[current])} = {room} (to within {TOLERANCE})"
    )
    return problem, fix


def sector_rules(table: Table, tables: Mapping[str, Table], findings: Findings) -> None:
    sheet = SECTORS.name
    part_findings(table, findings)
    for row in table.rows:
        limited = bool(row.raw["limit_pct_nav"])
        if row.raw["headroom_pct_nav"] and not limited:
            problem = "headroom_pct_nav is given without limit_pct_nav"
            findings.add(sheet, f"E{row.number}", problem, RULE_FIX["sector_headroom_alone"])
        elif row.ok("headroom_pct_nav", "limit_pct_nav", "pct_nav"):
            found = headroom_problem(
                row, "headroom_pct_nav", "limit_pct_nav", "pct_nav", RULE_FIX["sector_headroom"]
            )
            if found is not None:
                findings.add(sheet, f"E{row.number}", *found)
        if row.raw["status"] and not limited:
            problem = "status is given without limit_pct_nav"
            findings.add(sheet, f"F{row.number}", problem, RULE_FIX["sector_status_alone"])
        elif row.ok("status", "limit_pct_nav", "pct_nav"):
            found = status_problem(row, "status", "limit_pct_nav", "pct_nav")
            if found is not None:
                findings.add(sheet, f"F{row.number}", *found)


def top_holding_rules(table: Table, tables: Mapping[str, Table], findings: Findings) -> None:
    part_findings(table, findings)
    key_findings(TOP_HOLDINGS, table.rows, findings, ("issuer", "instrument"))
    if not all(row.ok("rank") for row in table.rows):
        return
    ranks = {cast(int, row.values["rank"]) for row in table.rows}
    count = len(table.rows)
    if len(ranks) == count and ranks != set(range(1, count + 1)):
        missing = ", ".join(str(rank) for rank in range(1, count + 1) if rank not in ranks)
        cells = f"A{table.rows[0].number}:A{table.rows[-1].number}"
        problem = f"ranks are not 1 to {count}: {missing} missing"
        findings.add(TOP_HOLDINGS.name, cells, problem, RULE_FIX["ranks"])
    elif len(ranks) == count:
        rank_order_findings(table, findings)


def rank_order_findings(table: Table, findings: Findings) -> None:
    """Rank 1 is the largest share of NAV: a holding larger than the one ranked above it."""
    ordered = sorted(table.rows, key=lambda row: cast(int, row.values["rank"]))
    for above, below in pairwise(ordered):
        if above.ok("pct_nav") and below.ok("pct_nav"):
            larger = below.number_of("pct_nav") > above.number_of("pct_nav")
            if larger:
                problem = (
                    f"rank {below.values['rank']} holds {below.raw['pct_nav']} % NAV, more than "
                    f"rank {above.values['rank']}'s {above.raw['pct_nav']}"
                )
                cell = f"{TOP_HOLDINGS.letter('pct_nav')}{below.number}"
                findings.add(TOP_HOLDINGS.name, cell, problem, RULE_FIX["rank_order"])


def compliance_rules(table: Table, tables: Mapping[str, Table], findings: Findings) -> None:
    sheet = COMPLIANCE.name
    basis = nav_basis(tables)
    currency = basis.currency
    for row in table.rows:
        unit = row.raw["limit_unit"]
        if row.ok("limit_unit") and unit != PCT_NAV and currency is not None and unit != currency:
            problem = f"limit_unit {unit} is not the Mandate nav_currency {currency}"
            findings.add(sheet, f"E{row.number}", problem, UNIT_FIX)
        if row.ok("headroom", "limit", "current_value") and unit == PCT_NAV:
            found = headroom_problem(
                row, "headroom", "limit", "current_value", RULE_FIX["headroom"]
            )
            if found is not None:
                findings.add(sheet, f"J{row.number}", *found)
        if row.ok("status", "limit", "current_value"):
            found = status_problem(row, "status", "limit", "current_value")
            if found is not None:
                findings.add(sheet, f"K{row.number}", *found)
        constraint_findings(row, basis, findings)
        sector_row_findings(row, tables.get(SECTORS.name), findings)


def constraint_findings(row: Row, basis: NavBasis, findings: Findings) -> None:
    """A row checked before the Mandate as_of, and an amount above the fund's NAV in its own
    currency (a unit mix-up: thousands or millions against units)."""
    sheet, checked = COMPLIANCE.name, row.values.get("last_checked")
    if basis.as_of is not None and isinstance(checked, date) and checked < basis.as_of:
        problem = (
            f"last_checked {checked} is before the Mandate as_of {basis.as_of} "
            f"({basis.as_of_cell}): the row was checked against older exposures"
        )
        findings.add(sheet, f"L{row.number}", problem, RULE_FIX["checked_before"])
    if (
        basis.nav is not None
        and row.raw["limit_unit"] == basis.currency
        and row.ok("current_value")
        and row.number_of("current_value") > basis.nav
    ):
        problem = (
            f"current_value {row.raw['current_value']} {basis.currency} is more than the fund's "
            f"nav {plain(basis.nav)} ({basis.nav_cell}) by "
            f"{plain(EXACT.subtract(row.number_of('current_value'), basis.nav))}"
        )
        findings.add(sheet, f"I{row.number}", problem, RULE_FIX["amount_nav"])


def sector_row_findings(row: Row, sectors: Table | None, findings: Findings) -> None:
    """The sector-limit row against the Sector_Exposure row its parameter names (exactly one):
    the same exposure and, where the sector states one, the same limit, to within `TOLERANCE`."""
    if sectors is None or row.raw["id"] != SECTOR_ID or row.raw["limit_unit"] != PCT_NAV:
        return
    named = [s for s in sectors.rows if s.ok("sector") and s.raw["sector"] in row.raw["parameter"]]
    if len(named) != 1:
        return
    (sector,) = named
    for mine, theirs in (("current_value", "pct_nav"), ("limit", "limit_pct_nav")):
        if row.ok(mine) and sector.ok(theirs):
            off = EXACT.abs(EXACT.subtract(row.number_of(mine), sector.number_of(theirs)))
            if off > TOLERANCE:
                problem = (
                    f"{mine} {row.raw[mine]} of the sector-limit row is not the {theirs} "
                    f"{sector.raw[theirs]} of {echo(sector.raw['sector'])} on Sector_Exposure "
                    f"(row {sector.number}); difference {plain(off)}, more than {TOLERANCE}"
                )
                cell = f"{COMPLIANCE.letter(mine)}{row.number}"
                findings.add(COMPLIANCE.name, cell, problem, RULE_FIX["sector_row"])


def holding_rules(table: Table, tables: Mapping[str, Table], findings: Findings) -> None:
    part_findings(table, findings)
    basis = nav_basis(tables)
    for row in table.rows:
        price_findings(row, findings)
        share_findings(row, basis, findings)
        maturity = row.values.get("maturity")
        if basis.as_of is not None and isinstance(maturity, date) and maturity < basis.as_of:
            problem = (
                f"maturity {maturity} is before the Mandate as_of {basis.as_of} "
                f"({basis.as_of_cell}): a matured position is not held"
            )
            findings.add(HOLDINGS.name, f"J{row.number}", problem, RULE_FIX["matured"])


def price_findings(row: Row, findings: Findings) -> None:
    """market_value per 100 of par outside `PRICE_RANGE`: par and market value in other units."""
    if not row.ok("par", "market_value"):
        return
    par, value = row.number_of("par"), row.number_of("market_value")
    scaled = EXACT.multiply(value, HUNDRED)
    low, high = PRICE_RANGE
    if EXACT.multiply(par, low) <= scaled <= EXACT.multiply(par, high):
        return
    price = EXACT.divide(scaled, par)
    problem = (
        f"market_value {row.raw['market_value']} is {rounded(price)} per 100 of par "
        f"{row.raw['par']}, outside {low} to {high}: par and market_value look like different "
        "units"
    )
    findings.add(HOLDINGS.name, f"E{row.number}", problem, RULE_FIX["price"])


def share_findings(row: Row, basis: NavBasis, findings: Findings) -> None:
    """pct_nav against market_value / nav x 100, to within `TOLERANCE` (compared exactly as
    |pct_nav x nav - market_value x 100| <= TOLERANCE x nav, with no division)."""
    if basis.nav is None or not row.ok("pct_nav", "market_value"):
        return
    pct, value = row.number_of("pct_nav"), row.number_of("market_value")
    gap = EXACT.subtract(EXACT.multiply(pct, basis.nav), EXACT.multiply(value, HUNDRED))
    if EXACT.abs(gap) <= EXACT.multiply(TOLERANCE, basis.nav):
        return
    share = EXACT.divide(EXACT.multiply(value, HUNDRED), basis.nav)
    problem = (
        f"pct_nav {row.raw['pct_nav']} is not market_value {row.raw['market_value']} / Mandate "
        f"nav {plain(basis.nav)} ({basis.nav_cell}) x 100 = {rounded(share)}; difference "
        f"{rounded(EXACT.abs(EXACT.subtract(pct, share)))}, more than {TOLERANCE}"
    )
    findings.add(HOLDINGS.name, f"F{row.number}", problem, RULE_FIX["holding_share"])


def workbook_rules(tables: Mapping[str, Table], findings: Findings, run_date: date | None) -> None:
    """The rules that compare sheets read after the one they report on, and the dates against the
    run's as-of date when one is given (the launcher gives it; the self-check takes --as-of)."""
    top10_findings(tables, findings)
    sector_holding_findings(tables, findings)
    top_detail_findings(tables, findings)
    if run_date is not None:
        run_date_findings(tables, findings, run_date)


def top10_findings(tables: Mapping[str, Table], findings: Findings) -> None:
    """The holdings ranked 1 to 10 against the Exposure_Summary top10_pct_nav: never more, and
    equal when ten are listed, each to within n x `SHARE_ROUNDING`."""
    exposure, top = tables.get(EXPOSURE.name), tables.get(TOP_HOLDINGS.name)
    if exposure is None or top is None or not all(r.ok("rank", "pct_nav") for r in top.rows):
        return
    metrics = [
        r
        for r in exposure.rows
        if r.raw["metric"] == TOP10_METRIC and r.raw["unit"] == PCT_NAV and r.ok("value")
    ]
    listed = [r for r in top.rows if cast(int, r.values["rank"]) <= TOP_TEN]
    if len(metrics) != 1 or not listed:
        return
    (metric,) = metrics
    stated, total = metric.number_of("value"), sum_of(listed, "pct_nav")
    allowance = EXACT.multiply(SHARE_ROUNDING, Decimal(len(listed)))
    off = EXACT.subtract(total, stated)
    if off > allowance or (len(listed) == TOP_TEN and off.copy_negate() > allowance):
        side = "less" if off > 0 else "more"
        problem = (
            f"top10_pct_nav {metric.raw['value']} is {side} than the {plain(total)} that the "
            f"{len(listed)} largest holdings on Top_Holdings add to; difference "
            f"{plain(off.copy_abs())}, more than {plain(allowance.normalize())}"
        )
        findings.add(EXPOSURE.name, f"B{metric.number}", problem, RULE_FIX["top10"])


def sector_holding_findings(tables: Mapping[str, Table], findings: Findings) -> None:
    """The Holdings_Detail rows of a sector add to at most its Sector_Exposure pct_nav."""
    sectors, holdings = tables.get(SECTORS.name), tables.get(HOLDINGS.name)
    if sectors is None or holdings is None:
        return
    by_name = {s.raw["sector"]: s for s in sectors.rows if s.ok("sector", "pct_nav")}
    groups: dict[str, list[Row]] = {}
    for row in holdings.rows:
        if row.ok("sector", "pct_nav") and row.raw["sector"] in by_name:
            groups.setdefault(row.raw["sector"], []).append(row)
    for name, rows in groups.items():
        sector, total = by_name[name], sum_of(rows, "pct_nav")
        allowance = EXACT.multiply(SHARE_ROUNDING, Decimal(len(rows) + 1))
        off = EXACT.subtract(total, sector.number_of("pct_nav"))
        if off > allowance:
            problem = (
                f"pct_nav {sector.raw['pct_nav']} of {echo(name)} is less than the "
                f"{plain(total)} its holdings on Holdings_Detail ({row_list(rows)}) add to; "
                f"difference {plain(off)}, more than {plain(allowance.normalize())}"
            )
            cell = f"{SECTORS.letter('pct_nav')}{sector.number}"
            findings.add(SECTORS.name, cell, problem, RULE_FIX["sector_holdings"])


def top_detail_findings(tables: Mapping[str, Table], findings: Findings) -> None:
    """A top holding against the Holdings_Detail rows of the same issuer and instrument."""
    top, holdings = tables.get(TOP_HOLDINGS.name), tables.get(HOLDINGS.name)
    if top is None or holdings is None:
        return
    detail: dict[tuple[str, str], list[Row]] = {}
    for row in holdings.rows:
        if row.ok("issuer", "instrument", "pct_nav"):
            detail.setdefault((row.raw["issuer"], row.raw["instrument"]), []).append(row)
    for row in top.rows:
        rows = detail.get((row.raw["issuer"], row.raw["instrument"]), [])
        if not rows or not row.ok("issuer", "instrument", "pct_nav"):
            continue
        total = sum_of(rows, "pct_nav")
        allowance = EXACT.multiply(SHARE_ROUNDING, Decimal(len(rows) + 1))
        off = EXACT.abs(EXACT.subtract(row.number_of("pct_nav"), total))
        if off > allowance:
            problem = (
                f"pct_nav {row.raw['pct_nav']} is not the {plain(total)} that Holdings_Detail "
                f"({row_list(rows)}) gives the same issuer and instrument; difference "
                f"{plain(off)}, more than {plain(allowance.normalize())}"
            )
            cell = f"{TOP_HOLDINGS.letter('pct_nav')}{row.number}"
            findings.add(TOP_HOLDINGS.name, cell, problem, RULE_FIX["top_detail"])


def run_date_findings(tables: Mapping[str, Table], findings: Findings, run_date: date) -> None:
    """The Mandate as_of after the run's as-of date or more than `STALE_DAYS` before it, and a
    Compliance_Monitor row checked after the run's as-of date."""
    basis = nav_basis(tables)
    if basis.as_of is not None:
        cell = basis.as_of_cell.partition("!")[2]
        days = (run_date - basis.as_of).days
        if days < 0:
            problem = f"as_of {basis.as_of} is after the run's as-of date {run_date}"
            findings.add(MANDATE.name, cell, problem, RULE_FIX["after_run"])
        elif days > STALE_DAYS:
            problem = (
                f"as_of {basis.as_of} is {days} days before the run's as-of date {run_date}, "
                f"more than {STALE_DAYS}: the fund's exposures and compliance are stale"
            )
            findings.add(MANDATE.name, cell, problem, RULE_FIX["stale"])
    compliance = tables.get(COMPLIANCE.name)
    for row in compliance.rows if compliance is not None else ():
        checked = row.values.get("last_checked")
        if isinstance(checked, date) and checked > run_date:
            problem = f"last_checked {checked} is after the run's as-of date {run_date}"
            findings.add(COMPLIANCE.name, f"L{row.number}", problem, RULE_FIX["after_run"])


SHEET_RULES = {
    MANDATE.name: mandate_rules,
    EXPOSURE.name: exposure_rules,
    RATINGS.name: rating_rules,
    SECTORS.name: sector_rules,
    TOP_HOLDINGS.name: top_holding_rules,
    MATURITIES.name: maturity_rules,
    COMPLIANCE.name: compliance_rules,
    HOLDINGS.name: holding_rules,
}


def typed(row: Row, sheet: Sheet) -> dict[str, Value | None]:
    """A passing row's columns as model fields: optional empty cells are None."""
    fields: dict[str, Value | None] = {"row": row.number}
    fields.update((name, row.values.get(name)) for name in sheet.names)
    return fields


def build_facts(tables: Mapping[str, Table]) -> PortfolioFacts:
    """The typed rows of a workbook with no issues (every required cell holds a valid value)."""
    mandate_table = tables[MANDATE.name]
    required = {name: value for name, (value, _) in mandate_values(mandate_table).items()}
    holdings = tables.get(HOLDINGS.name)
    return PortfolioFacts(
        mandate=Mandate(
            fund_name=cast(str, required["fund_name"]),
            strategy=cast(
                Literal["CLO", "Indexed Loans", "Indexed HY", "Other"], required["strategy"]
            ),
            nav=cast(Decimal, required["nav"]),
            nav_currency=cast(str, required["nav_currency"]),
            as_of=cast(date, required["as_of"]),
            fields=tuple(
                MandateField.model_validate(typed(row, MANDATE)) for row in mandate_table.rows
            ),
        ),
        exposures=rows_of(tables, EXPOSURE, Exposure),
        ratings=rows_of(tables, RATINGS, RatingBucket),
        sectors=rows_of(tables, SECTORS, SectorExposure),
        top_holdings=rows_of(tables, TOP_HOLDINGS, TopHolding),
        maturities=rows_of(tables, MATURITIES, MaturityBucket),
        compliance=rows_of(tables, COMPLIANCE, ComplianceRow),
        holdings=None if holdings is None else rows_of(tables, HOLDINGS, Holding),
    )


def rows_of[RowModel: SheetRow](
    tables: Mapping[str, Table], sheet: Sheet, model: type[RowModel]
) -> tuple[RowModel, ...]:
    return tuple(model.model_validate(typed(row, sheet)) for row in tables[sheet.name].rows)
