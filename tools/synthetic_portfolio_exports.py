"""SYNTHETIC portfolio exports: one clean, and one per kind of defect found in a real export.

The shape is the one a fund's systems export (ruling 2026-11-15-full-assessment-portfolio-workbook,
"The export shape"): a mandate CSV (Section, Field, Value, Notes), two constraints CSVs, an exposure
report CSV with five stacked sections (A summary, B ratings, C sectors, D largest holdings,
E maturities) and a workbook with a Holdings and a Market Data sheet. Every name, identifier and
number here is invented; none is fund or market data, and none is taken from the owner's files.
They are inputs for `deploy_vii.inputs.portfolio_export`, never an output of a run (AGENTS.md:
Excel is an input format only). Tests build them in memory; to look at them:

    uv run python tools/synthetic_portfolio_exports.py <folder> [--as-of YYYY-MM-DD]

The clean export reconciles exactly: seven positions, par 100,000,000, market value at mid
100,000,000. Each kind in `BROKEN` changes it in one place, mirroring one class of defect; what the
check must report for each is written by hand in tests/test_portfolio_export.py.
"""

from __future__ import annotations

import argparse
import copy
import csv
import io
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook  # type: ignore[import-untyped]

Row = list[object]

AS_OF = date(2025, 3, 31)
MANDATE = "SYNTHETIC CP-6A Mandate File.csv"
CONSTRAINTS = "SYNTHETIC CP-6A Portfolio Constraints Compliance Monitor.csv"
FIT_CONSTRAINTS = "SYNTHETIC CP-3C Portfolio Constraints.csv"
EXPOSURE = "SYNTHETIC CP-6A Exposure Report.csv"
HOLDINGS = "SYNTHETIC Holdings.xlsx"
HOLDING_HEADER: Row = [
    *("Ticker", "Borrower Name", "Index Sector", "Sub Sector", "Loan Name", "FIGI", "Ranking"),
    *("Ratings", "Size ($Mn)", "Margin", "Maturity", "Bid", "Ask", "Δ 1M", "Δ YTD", "Mid YTM"),
    *("Mid 3Y DM", "Holdings"),
]
# Ticker, borrower, sector, loan, FIGI, ranking, ratings, margin, maturity, bid, ask, YTM, DM, par
POSITIONS: list[tuple[object, ...]] = [
    (
        "ASTR",
        "Aster Fictional Co",
        "Software",
        "ASTR TL B",
        "BBG00SYN0001",
        "1L Gtd Sr. Secd",
        "B2 / B",
        300,
        date(2029, 6, 30),
        99.5,
        100.5,
        8.0,
        350,
        20_000_000,
    ),
    (
        "ASTR",
        "Aster Fictional Co",
        "Software",
        "ASTR TL B2",
        "BBG00SYN0002",
        "1L Sr. Secd",
        "B2 / B",
        350,
        date(2030, 1, 31),
        97.5,
        98.5,
        8.5,
        400,
        10_000_000,
    ),
    (
        "BRCH",
        "Birch Imaginary Inc",
        "Chemicals",
        "BRCH TL",
        "BBG00SYN0003",
        "1L Sr. Secd",
        "Ba3 / BB-",
        400,
        date(2028, 3, 31),
        99.5,
        100.5,
        9.0,
        450,
        15_000_000,
    ),
    (
        "CEDR",
        "Cedar Example LLC",
        "Software",
        "CEDR TL",
        "BBG00SYN0004",
        "1L Sr. Secd",
        "B3 / B-",
        325,
        date(2029, 9, 30),
        98.5,
        99.5,
        8.25,
        375,
        10_000_000,
    ),
    (
        "DUNE",
        "Dune Sample Corp",
        "Healthcare",
        "DUNE TL B",
        "BBG00SYN0005",
        "1L Sr. Secd",
        "B1 / B+",
        275,
        date(2030, 6, 30),
        99.5,
        100.5,
        7.75,
        325,
        25_000_000,
    ),
    (
        "ELMI",
        "Elm Invented Ltd",
        "Healthcare",
        "ELMI 2L TL",
        "BBG00SYN0006",
        "2L Secd",
        "Caa1 / CCC+",
        600,
        date(2031, 3, 31),
        100.5,
        101.5,
        11.0,
        650,
        10_000_000,
    ),
    (
        "FERN",
        "Fern Placeholder SA",
        "Chemicals",
        "FERN TL",
        "BBG00SYN0007",
        "1L Sr. Secd",
        "Ba2 / BB",
        450,
        date(2028, 12, 31),
        101.5,
        102.5,
        9.5,
        500,
        10_000_000,
    ),
]
MARKET: list[tuple[object, ...]] = [
    (
        "GLDN",
        "Golden Mock Holdings",
        "Software",
        "GLDN TL",
        "BBG00SYN0101",
        "1L Sr. Secd",
        "B2 / B",
        375,
        date(2029, 3, 31),
        98.0,
        99.0,
        9.1,
        410,
    ),
    (
        "HAZL",
        "Hazel Specimen Corp",
        "Chemicals",
        "HAZL TL",
        "BBG00SYN0102",
        "1L Sr. Secd",
        "B1 / B",
        325,
        date(2030, 3, 31),
        99.0,
        100.0,
        8.4,
        360,
    ),
    (
        "IRIS",
        "Iris Template Ltd",
        "Healthcare",
        "IRIS TL",
        "BBG00SYN0103",
        "1L Sr. Secd",
        "Ba3 / BB-",
        300,
        date(2028, 9, 30),
        100.0,
        100.5,
        7.9,
        320,
    ),
]


@dataclass
class Spec:
    """The export's files as rows; `holdings` and `market` are the workbook's data rows (header
    excluded), `empty_rows` the rows of empty text written below the holdings."""

    mandate: list[Row]
    constraints: list[Row]
    fit_constraints: list[Row]
    exposure: list[Row]
    holdings: list[Row]
    market: list[Row]
    empty_rows: int = 0
    extra: dict[str, bytes] = field(default_factory=dict)


def _holding(values: tuple[object, ...], with_par: bool = True) -> Row:
    ticker, name, sector, loan, figi, ranking, ratings, margin, maturity, bid, ask, ytm, dm = (
        values[:13]
    )
    row: Row = [ticker, name, sector, "Sub-sector (fictional)", loan, figi, ranking, ratings]
    row += [500, margin, maturity, bid, ask, 0.25, 1.5, ytm, dm]
    return [*row, values[13]] if with_par else row


def _constraint(cells: str, stamp: str) -> Row:
    """One monitor row from `ID | Category | Parameter | Limit | Breach | Current | Headroom |
    Status`; the source document and checker are fixed, an em dash marks not applicable."""
    ident, category, parameter, limit, breach, current, room, status = cells.split(" | ")
    source = "—" if breach == "—" else "Indenture 7 (fictional)"
    return [
        ident,
        category,
        parameter,
        limit,
        breach,
        source,
        current,
        room,
        status,
        stamp,
        "analyst",
    ]


# The monitor's rows, phrased as the real export phrases them (fictional names and figures).
MONITOR_ROWS = (
    (
        "C-01 | Single Name | Max single issuer exposure (largest: Aster) | ≤ 30.0% NAV | Hard | "
        "29.80% | 0.20% | Watch"
    ),
    (
        "C-02 | Concentration | Aggregate top 10 issuers | ≤ 100.0% NAV | Soft | 100.00% | 0.00% | "
        "Pass"
    ),
    (
        "C-03 | Sector | Max single sector (largest: Software) | ≤ 40.0% NAV | Soft | 39.70% | "
        "0.30% | Watch"
    ),
    "C-04 | Sector | 2nd largest sector: Healthcare | ≤ 40.0% NAV | Soft | 35.10% | 4.90% | Pass",
    "C-05 | Sector | 3rd largest sector: Chemicals | ≤ 40.0% NAV | Soft | 25.20% | 14.80% | Pass",
    "C-06 | Seniority | Min 1st Lien / Senior Secured | ≥ 85.0% NAV | Hard | 89.90% | 4.90% | Pass",
    "C-07 | Seniority | Max 2nd Lien / Unsecured | ≤ 15.0% NAV | Hard | 10.10% | 4.90% | Pass",
    (
        "C-08 | Rating | Max CCC+ and below (incl. Unrated & Other) | ≤ 12.5% NAV | Hard | "
        "10.10% | "
        "2.40% | Pass"
    ),
    "C-09 | Rating | Max unrated exposure | ≤ 5.0% NAV | Soft | 0.00% | 5.00% | Pass",
    (
        "C-10 | Rating | Min portfolio WAR | ≥ Caa1 (numeric ≤ 17) | Hard | B1 (14.3) | "
        "2.7 notches | "
        "Pass"
    ),
    "C-11 | Tenor | Max WAL (weighted avg life) | ≤ 6.00 yrs | Soft | 4.52 yrs | 1.48 yrs | Pass",
    "C-12 | Diversification | Min number of obligors | ≥ 5 | Soft | 6 | 1 | Pass",
    "C-13 | Prohibited | Max equity exposure | 0% NAV | Hard | 0.00% | — | Pass",
    "C-14 | Spread | Weighted average spread | Info only | — | 361.25 bps | — | Info",
    # An exclusion row: no Max or Min, so its 0% limit is a maximum.
    "C-15 | Exclusions | Excluded sectors (Tobacco, Weapons) | 0% NAV | Hard | 0% | 0% | Pass",
)
# The second constraints export: other column names, no ID, source or checked columns.
FIT_HEADER: Row = [
    *("Constraint Category", "Parameter", "Limit / Guideline", "Breach Type"),
    *("Current Exposure", "Headroom", "Status"),
]


def clean(as_of: date = AS_OF) -> Spec:
    stamp = as_of.strftime("%d-%b-%Y")
    monitor = [_constraint(cells, stamp) for cells in MONITOR_ROWS]
    return Spec(
        mandate=[
            ["Section", "Field", "Value", "Notes"],
            ["Strategy", "Fund Name", "SYNTHETIC Example Loan Fund (fictional)", ""],
            ["Key Parties", "Collateral Manager", "Example Manager LLP (fictional)", ""],
            ["Capital Structure", "Class A-1 Notes", "$40,000,000 — SOFR + 130bps", "AAA"],
            ["Capital Structure", "Class A-2 Notes", "$15,000,000 — SOFR + 160bps", "AAA"],
            ["Capital Structure", "Class B Notes", "$10,000,000 — SOFR + 190bps", "AA"],
            ["Capital Structure", "Class C Notes", "$8,000,000 — SOFR + 240bps", "A"],
            ["Capital Structure", "Class D Notes", "$7,000,000 — SOFR + 350bps", "BBB-"],
            ["Capital Structure", "Class E Notes", "$5,000,000 — SOFR + 650bps", "BB-"],
            ["Capital Structure", "Subordinated Notes / Equity", "$15,000,000", "first loss"],
            ["Capital Structure", "Total Liabilities + Equity", "$100,000,000", ""],
            ["Fees", "Senior Management Fee", "0.20% p.a.", ""],
            ["Reporting", "As of Date", stamp, "positions and compliance date"],
        ],
        constraints=[
            [
                *("ID", "Constraint Category", "Parameter", "Limit", "Breach Type"),
                *("Source Document", "Current Value", "Headroom", "Status", "Last Checked"),
                "Checked By",
            ],
            *monitor,
        ],
        fit_constraints=[
            FIT_HEADER,
            *([row[1], row[2], row[3], row[4], row[6], row[7], row[8]] for row in monitor[:7]),
        ],
        exposure=[
            ["A. Summary Metrics"],
            ["Metric", "Value", "Notes"],
            ["NAV", "USD 100,000,000", "collateral market value"],
            ["Total Par", "100,000,000", ""],
            ["Positions", "7", ""],
            ["Obligors", "6", ""],
            ["Sectors", "3", ""],
            ["Weighted Average Price", "100.000", ""],
            ["WA Margin", "361.25 bps", ""],
            ["WA YTM", "8.61%", ""],
            ["Max Single Issuer", "Aster (29.80%)", ""],
            ["Max Single Sector", "Software (39.70%)", ""],
            ["Top 10 Issuers", "100.00%", ""],
            ["1st Lien", "89.90%", ""],
            ["2nd Lien", "10.10%", ""],
            ["Weighted Average Rating (WAR)", "B1 (14.3)", ""],
            ["Weighted Average Life (yrs)", "4.52", ""],
            [],
            ["B. Rating Distribution"],
            ["Bucket", "% NAV", "Issuers"],
            ["BB", "25.20%", "2"],
            ["B", "64.70%", "3"],
            ["CCC", "10.10%", "1"],
            ["Total", "100.00%", "6"],
            [],
            ["C. Top 20 Sectors"],
            ["Sector", "% NAV", "Issuers", "Limit", "Headroom", "Status"],
            ["Software", "39.70%", "2", "≤ 40.0% NAV", "0.30%", "Pass"],
            ["Healthcare", "35.10%", "2", "≤ 40.0% NAV", "4.90%", "Pass"],
            ["Top 20 Subtotal", "74.80%", "", "", "", ""],
            ["Other Sectors", "25.20%", "", "", "", ""],
            ["Total", "100.00%", "6", "", "", ""],
            [],
            ["D. Top 10 Holdings"],
            [
                "Rank",
                "Issuer",
                "# Positions",
                "Rating",
                "Sector",
                "MV ($)",
                "% NAV",
                "Rating Bucket",
            ],
            ["1", "Aster", "2", "B2", "Software", "29,800,000", "29.80%", "B"],
            ["2", "Dune Sample", "1", "B1", "Healthcare", "25,000,000", "25.00%", "B"],
            ["3", "Birch", "1", "Ba3", "Chemicals", "15,000,000", "15.00%", "BB"],
            ["4", "Fern", "1", "Ba2", "Chemicals", "10,200,000", "10.20%", "BB"],
            ["5", "Elm", "1", "Caa1", "Healthcare", "10,100,000", "10.10%", "CCC"],
            ["6", "Cedar", "1", "B3", "Software", "9,900,000", "9.90%", "B"],
            ["", "Top 10 Total", "7", "", "", "100,000,000", "100.00%", ""],
            [],
            ["E. Maturity Profile"],
            ["Bucket", "% NAV", "MV (USD)"],
            ["2028", "25.20%", "25,200,000"],
            ["2029", "29.90%", "29,900,000"],
            ["2030", "34.80%", "34,800,000"],
            ["2031", "10.10%", "10,100,000"],
            ["Total", "100.00%", "100,000,000"],
        ],
        holdings=[_holding(values) for values in POSITIONS],
        market=[_holding(values, with_par=False) for values in MARKET],
    )


def _csv(rows: list[Row]) -> bytes:
    stream = io.StringIO()
    csv.writer(stream, lineterminator="\n").writerows(rows)
    return stream.getvalue().encode("utf-8")


def _workbook(spec: Spec) -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.title = "Holdings"
    for row in [HOLDING_HEADER, *spec.holdings]:
        sheet.append(row)
    for _ in range(spec.empty_rows):
        sheet.append([""] * len(HOLDING_HEADER))
    market = book.create_sheet("Market Data")
    for row in [HOLDING_HEADER[:-1], *spec.market]:
        market.append(row)
    for page in (sheet, market):
        for cells in page.iter_rows(min_row=2, min_col=11, max_col=11):
            cells[0].number_format = "yyyy-mm-dd"
    stream = io.BytesIO()
    book.save(stream)
    return stream.getvalue()


def files(spec: Spec) -> dict[str, bytes]:
    out = {
        MANDATE: _csv(spec.mandate),
        CONSTRAINTS: _csv(spec.constraints),
        FIT_CONSTRAINTS: _csv(spec.fit_constraints),
        EXPOSURE: _csv(spec.exposure),
        HOLDINGS: _workbook(spec),
    }
    return {**out, **spec.extra}


BOOK = "SYNTHETIC Portfolio Export.xlsx"
SHEETS = (
    ("Mandate File", "mandate"),
    ("Constraints Monitor", "constraints"),
    ("CP-3C Constraints", "fit_constraints"),
    ("Exposure Report", "exposure"),
)


def workbook_files(spec: Spec) -> dict[str, bytes]:
    """The same export as one workbook: the reports as sheets beside Holdings and Market Data."""
    book = Workbook()
    book.remove(book.active)
    for title, attribute in SHEETS:
        sheet = book.create_sheet(title)
        for row in getattr(spec, attribute):
            sheet.append(row or [None])
    source = load_workbook(io.BytesIO(_workbook(spec)))
    for name in source.sheetnames:
        target = book.create_sheet(name)
        for row in source[name].iter_rows(values_only=True):
            target.append(list(row))
        for cells in target.iter_rows(min_row=2, min_col=11, max_col=11):
            cells[0].number_format = "yyyy-mm-dd"
    out = io.BytesIO()
    book.save(out)
    return {BOOK: out.getvalue()}


def _find(rows: list[Row], first: str) -> Row:
    return next(row for row in rows if row and row[0] == first)


def _set(rows: list[Row], first: str, column: int, value: object) -> None:
    _find(rows, first)[column] = value


def _report_not_holdings(spec: Spec) -> None:  # class 1
    for metric, value in (
        ("NAV", "USD 105,000,000"),
        ("Total Par", "110,000,000"),
        ("Positions", "8"),
        ("Obligors", "7"),
        ("Sectors", "4"),
    ):
        _set(spec.exposure, metric, 1, value)


def _issuer_row(spec: Spec, issuer: str) -> Row:
    return next(row for row in spec.exposure if len(row) > 1 and row[1] == issuer)


def _concentration(spec: Spec) -> None:  # class 2
    _set(spec.exposure, "Max Single Issuer", 1, "Aster (35.00%)")
    _set(spec.exposure, "Top 10 Issuers", 1, "95.00%")
    aster = _issuer_row(spec, "Aster")
    aster[2], aster[5], aster[6] = "3", "35,000,000", "35.00%"
    total = _issuer_row(spec, "Top 10 Total")
    spec.exposure.insert(
        spec.exposure.index(total),
        ["7", "Ghost", "1", "B2", "Software", "5,000,000", "5.00%", "B"],
    )
    total[2], total[5], total[6] = "9", "110,200,000", "110.20%"


def _hidden_breach(spec: Spec) -> None:  # class 3
    _find(spec.exposure, "Software")[1:6] = ["34.70%", "2", "≤ 35.0% NAV", "0.30%", "Pass"]
    _find(spec.exposure, "Healthcare")[1:6] = ["40.10%", "2", "≤ 45.0% NAV", "4.90%", "Pass"]


def _subtotals(spec: Spec) -> None:  # class 4
    _set(spec.exposure, "B", 1, "64.71%")  # rows add to 100.01: rounding, tolerated
    rating_total = next(row for row in spec.exposure if row and row[0] == "Total")
    rating_total[2] = "7"
    sector_total = [row for row in spec.exposure if row and row[0] == "Total"][1]
    sector_total[1] = "99.90%"


def _summary_metrics(spec: Spec) -> None:  # class 5
    for metric, value in (
        ("Weighted Average Price", "101.00"),
        ("WA YTM", "3.20%"),
        ("WA Margin", "375 bps"),
        ("2nd Lien", "12.00%"),
    ):
        _set(spec.exposure, metric, 1, value)


def _capital(spec: Spec) -> None:  # class 6
    # Class A-1 at 20m instead of 40m: the tranches add to 80m against a stated total of 90m,
    # and 90m is 90% of the collateral.
    _set(spec.mandate, "Capital Structure", 2, "$20,000,000 — SOFR + 130bps")
    total = next(row for row in spec.mandate if row[1] == "Total Liabilities + Equity")
    total[2] = "$90,000,000"


def _century(spec: Spec) -> None:  # class 7
    for row, year in zip(spec.holdings[:3], (1929, 1930, 1928), strict=True):
        assert isinstance(row[10], date)
        row[10] = row[10].replace(year=year)
    spec.market[0][10] = date(1931, 3, 31)


def _impossible(spec: Spec) -> None:  # class 8
    spec.holdings[1][15] = -246.5
    spec.holdings[2][16] = 27085


def _tokens(spec: Spec) -> None:  # class 9
    spec.holdings[3][13] = "#N/A N/A"  # Δ 1M, row 5
    spec.holdings[4][16] = "#N/A N/A"  # Mid 3Y DM, row 6
    spec.holdings[0][7] = "#N/A N/A / B"  # row 2
    spec.holdings[2][7] = "WR / NR"  # row 4
    spec.holdings[3][7] = "B3 *+ / B-"  # row 5


def _unpriced(spec: Spec) -> None:  # class 9, a price token: the position drops out of value
    spec.holdings[6][11] = spec.holdings[6][12] = "#N/A N/A"  # row 8


def _identifiers(spec: Spec) -> None:  # class 10
    spec.holdings[2][5] = "BBG00SYN003"  # row 4: eleven characters
    spec.holdings[4][5] = "BBG00SYN0004"  # row 6: Cedar's FIGI on Dune's loan
    spec.holdings[6][0] = "ASTR"  # row 8: Aster's ticker on Fern
    spec.market[1][1] = "Hazel Spec�men Corp"  # Market Data row 3
    spec.market[2][6] = "B1 / B"  # Market Data row 4: a rating in Ranking
    spec.empty_rows = 3


def _units(spec: Spec) -> None:  # class 12
    _find(spec.constraints, "C-01")[6] = "~29.8%"
    _find(spec.constraints, "C-02")[3] = "max 40 percent"
    _find(spec.constraints, "C-03")[6] = "10.10"


def _crossed(spec: Spec) -> None:  # bid above ask; the mid (99) is unchanged
    spec.holdings[3][11], spec.holdings[3][12] = 99.5, 98.5  # row 5


def _above_tranche(spec: Spec) -> None:
    spec.holdings[4][8] = 20  # row 6: 25,000,000 par in a 20 million tranche


def _two_tickers(spec: Spec) -> None:
    spec.holdings[1][0] = "ASTR2"  # row 3: Aster under a second ticker


def _wrong_kind(spec: Spec) -> None:  # on Market Data, so no recomputed figure moves
    spec.market[0][7] = "1st Lien"  # row 2: a ranking in Ratings
    spec.market[1][4] = "BBG00SYN0102"  # row 3: a FIGI in Loan Name


def _rating_buckets(spec: Spec) -> None:
    _find(spec.exposure, "BB")[1:3] = ["30.20%", "3"]
    _find(spec.exposure, "B")[1:3] = ["59.70%", "2"]


def _maturity_buckets(spec: Spec) -> None:
    _find(spec.exposure, "2028")[1:3] = ["30.20%", "30,200,000"]
    _find(spec.exposure, "2029")[1:3] = ["24.90%", "24,900,000"]


def _lien_split(spec: Spec) -> None:
    _set(spec.exposure, "1st Lien", 1, "85.00%")


def _named_largest(spec: Spec) -> None:
    # The fund names Dune as its largest issuer and Chemicals as its second largest sector; the
    # holdings' largest issuer is Aster (29.80%) and second largest sector Healthcare (35.10%).
    _set(spec.exposure, "Max Single Issuer", 1, "Dune Sample (25.00%)")
    _set(spec.constraints, "C-01", 2, "Max single issuer exposure (largest: Dune Sample)")
    _set(spec.constraints, "C-04", 2, "2nd largest sector: Chemicals")


def _files_differ(spec: Spec) -> None:
    second_lien = next(row for row in spec.fit_constraints if row[1] == "Max 2nd Lien / Unsecured")
    second_lien[4] = "12.10%"


def _ambiguous_name(spec: Spec) -> None:
    # Cedar's position held under a second Aster entity: the report's "Aster" now matches two
    # borrowers and its "Cedar" matches none.
    spec.holdings[3][1] = "Aster Sample LLC"


def _brand_names(spec: Spec) -> None:
    # Three listed names no borrower matches: "Brcknell Group" (Birch's ticker BRCH begins with
    # its first three letters), "Sanddune Health" (Dune, the first word of Dune Sample Corp, is
    # in it) and "Quill Holdings" (nothing points to a borrower).
    for old, new in (
        ("Birch", "Brcknell Group"),
        ("Dune Sample", "Sanddune Health"),
        ("Fern", "Quill Holdings"),
    ):
        next(row for row in spec.exposure if row[1:2] == [old])[1] = new


def _unclassified_lien(spec: Spec) -> None:
    spec.holdings[2][6] = "Sr. Secd"  # row 4: Birch's ranking without a lien token


BROKEN: dict[str, Callable[[Spec], None]] = {
    "report-not-holdings": _report_not_holdings,
    "concentration": _concentration,
    "hidden-breach": _hidden_breach,
    "subtotals": _subtotals,
    "summary-metrics": _summary_metrics,
    "capital-structure": _capital,
    "century-dates": _century,
    "impossible-values": _impossible,
    "vendor-tokens": _tokens,
    "unpriced-position": _unpriced,
    "identifiers": _identifiers,
    "units": _units,
    "crossed-quote": _crossed,
    "above-tranche": _above_tranche,
    "borrower-two-tickers": _two_tickers,
    "wrong-kind": _wrong_kind,
    "rating-buckets": _rating_buckets,
    "maturity-buckets": _maturity_buckets,
    "lien-split": _lien_split,
    "named-largest": _named_largest,
    "constraint-files-differ": _files_differ,
    "ambiguous-name": _ambiguous_name,
    "brand-names": _brand_names,
    "unclassified-lien": _unclassified_lien,
}


def broken(kind: str, as_of: date = AS_OF) -> Spec:
    spec = copy.deepcopy(clean(as_of))
    BROKEN[kind](spec)
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=AS_OF)
    args = parser.parse_args(argv)
    for kind, spec in (("clean", clean(args.as_of)), *((k, broken(k, args.as_of)) for k in BROKEN)):
        folder = args.folder / kind
        folder.mkdir(parents=True, exist_ok=True)
        for name, raw in files(spec).items():
            (folder / name).write_bytes(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
