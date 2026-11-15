"""SYNTHETIC portfolio workbooks: one clean, and one per kind of wrong sum or value.

Every row is invented for a fictional fund; none of it is fund or market data. The workbooks are
inputs for the portfolio workbook check (`deploy_vii.inputs.portfolio`), never an output of a run
(AGENTS.md: Excel is an input format only). Tests build them in memory; to look at them, write
them to a folder of your choice:

    uv run python tools/synthetic_portfolio_workbooks.py <folder> [--as-of YYYY-MM-DD]

The clean workbook follows `docs/templates/portfolio.template.xlsx` with its dates moved to the
as-of date. Each broken one changes the clean rows in one place (`BROKEN`); what the check must
report for each is written by hand in tests/test_portfolio_workbook.py, not derived from here.
"""

from __future__ import annotations

import argparse
import copy
import io
import re
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import Workbook  # type: ignore[import-untyped]

Cell = str | int | float | None
Rows = dict[str, list[list[Cell]]]

AS_OF = "2025-03-31"  # the synthetic launcher tests' run date (tests/test_cpos_launch.py AS_OF)
FUND = "SYNTHETIC Example Credit Fund I (fictional)"


def clean_rows(as_of: str = AS_OF) -> Rows:
    """The template's layout and figures, every date at `as_of` (maturities stay after it)."""
    return {
        "Mandate": [
            ["section", "field", "value", "notes"],
            ["Strategy", "fund_name", FUND, "SYNTHETIC: fictional fund"],
            ["Strategy", "strategy", "CLO", None],
            ["Capital Structure", "nav", "630928502", "collateral pool market value"],
            ["Capital Structure", "nav_currency", "USD", None],
            ["Mandate Constraints", "constraint_schedule", "see Compliance_Monitor", None],
            ["Reporting", "as_of", as_of, "NAV and compliance date"],
        ],
        "Exposure_Summary": [
            ["metric", "value", "unit", "as_of"],
            ["nav", 630928502, "USD", as_of],
            ["total_par", 635000000, "USD", as_of],
            ["obligors", 300, "count", as_of],
            ["wa_margin", 325, "bps", as_of],
            ["first_lien_pct_nav", 99.39, "% NAV", as_of],
            ["top10_pct_nav", 11.0, "% NAV", as_of],
        ],
        "Rating_Distribution": [
            ["rating_bucket", "pct_nav", "issuers"],
            ["IG (Baa+)", 0.5, 2],
            ["BB (Ba)", 25.0, 60],
            ["B", 67.14, 225],
            ["CCC (Caa+)", 0.23, 2],
            ["Other", 3.4, 9],
            ["Unrated", 3.73, 8],
        ],
        "Sector_Exposure": [
            ["sector", "pct_nav", "issuers", "limit_pct_nav", "headroom_pct_nav", "status"],
            ["Health Care Services", 7.0, 20, 10.0, 3.0, "Pass"],
            ["Business Services", 6.5, 30, 10.0, 3.5, "Pass"],
            ["Software", 5.75, 35, 10.0, 4.25, "Pass"],
            ["Chemicals", 5.25, 12, 10.0, 4.75, "Pass"],
            ["Leisure Facilities & Services", 4.57, 15, 10.0, 5.43, "Pass"],
        ],
        "Top_Holdings": [
            ["rank", "issuer", "instrument", "pct_nav", "rating"],
            [1, "Alpha Example Holdings", "Term Loan B due 2030", 2.37, "B2 / B+"],
            [2, "Beta Sample Aerospace", "Term Loan B due 2031", 1.8, "Ba2 / BB"],
            [3, "Gamma Illustrative Media", "Term Loan B due 2029", 1.5, "B3 / B-"],
            [4, "Delta Placeholder Networks", "Term Loan due 2028", 1.1, "B1 / B"],
            [5, "Epsilon Demo Leisure", "Senior Secured Notes due 2032", 0.9, "Ba3 / BB-"],
        ],
        "Maturity_Profile": [
            ["bucket", "pct_nav"],
            ["< 1 Year", 0.5],
            ["1-2 Years", 4.0],
            ["2-3 Years", 12.0],
            ["3-5 Years", 30.0],
            ["5-7 Years", 53.5],
        ],
        "Compliance_Monitor": [
            [
                *("id", "constraint_category", "parameter", "limit", "limit_unit"),
                *("breach_type", "scope", "source_document", "current_value", "headroom"),
                *("status", "last_checked", "checked_by"),
            ],
            [
                *("C-01", "Single Name", "Max single issuer exposure", 2.5, "% NAV", "Hard"),
                *("issuer", "Indenture s7.11 (fictional)", 2.37, 0.13, "Watch", as_of, "analyst"),
            ],
            [
                *("C-02", "Single Name", "Max single issuer amount", 20000000, "USD", "Hard"),
                *("issuer", "Indenture s7.11 (fictional)", 14962500, 5037500, "Pass", as_of),
                "analyst",
            ],
            [
                *("C-05", "Rating - Unrated", "Max unrated exposure", 5.0, "% NAV", "Soft"),
                *("rating_bucket", "Indenture s7.11 (fictional)", 3.73, 1.27, "Pass", as_of),
                "analyst",
            ],
            [
                "SECTOR",
                "Sector",
                "Max single sector (candidate's sector: Leisure Facilities & Services)",
                *(10.0, "% NAV", "Soft", "sector", "Indenture s7.11 (fictional)", 4.57, 5.43),
                *("Pass", as_of, "analyst"),
            ],
        ],
        "Holdings_Detail": [
            [
                *("issuer", "instrument", "facility_id", "par", "market_value", "pct_nav"),
                *("rating", "sector", "seniority", "maturity"),
            ],
            [
                *("Alpha Example Holdings", "Term Loan B due 2030", "TLB-2030", 15000000),
                *(14962500, 2.37, "B2 / B+", "Software", "1st Lien", "2030-09-30"),
            ],
            [
                *("Beta Sample Aerospace", "Term Loan B due 2031", "TLB-2031", 11400000),
                *(11357000, 1.8, "Ba2 / BB", "Business Services", "1st Lien", "2031-06-30"),
            ],
            [
                *("Gamma Illustrative Media", "Term Loan B due 2029", "TLB-2029", 9500000),
                *(9464000, 1.5, "B3 / B-", "Health Care Services", "1st Lien", "2029-03-31"),
            ],
        ],
        "README": [
            ["SYNTHETIC example: a fictional fund and fictional issuers; not fund or market data."],
        ],
    }


@dataclass
class Spec:
    """A workbook to build: its rows, and cells to style or to give a formula with a cache."""

    rows: Rows
    percent: list[tuple[str, str]] = field(default_factory=list)  # (sheet, cell) shown as 0.00%
    formulas: list[tuple[str, str, str, str]] = field(default_factory=list)  # sheet, cell, f, cache


def workbook_bytes(spec: Spec) -> bytes:
    book = Workbook()
    book.remove(book.active)
    for name, rows in spec.rows.items():
        sheet = book.create_sheet(name)
        for row in rows:
            sheet.append(row)
    for name, cell in spec.percent:
        book[name][cell].number_format = "0.00%"
    for name, cell, formula, _ in spec.formulas:
        book[name][cell] = f"={formula}"
    stream = io.BytesIO()
    book.save(stream)
    raw = stream.getvalue()
    for name, cell, formula, cache in spec.formulas:
        raw = _with_cache(raw, list(spec.rows).index(name) + 1, cell, formula, cache)
    return raw


def _with_cache(raw: bytes, index: int, cell: str, formula: str, cache: str) -> bytes:
    """Give a formula cell a stored (cached) value, as Excel does and openpyxl does not."""
    member = f"xl/worksheets/sheet{index}.xml"
    source = zipfile.ZipFile(io.BytesIO(raw))
    xml = source.read(member).decode()
    pattern = re.compile(rf'(<c r="{cell}"[^>]*><f>{re.escape(formula)}</f>)<v ?/>')
    xml, count = pattern.subn(rf"\g<1><v>{cache}</v>", xml)
    if count != 1:
        raise ValueError(f"{member}: no formula cell {cell}")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            body = xml.encode() if info.filename == member else source.read(info.filename)
            target.writestr(info, body)
    return out.getvalue()


def _set(rows: Rows, sheet: str, row: int, column: int, value: Cell) -> None:
    """Row and column count from 1 as in the sheet (row 1 is the header)."""
    rows[sheet][row - 1][column - 1] = value


def _rating_short(spec: Spec) -> None:
    _set(spec.rows, "Rating_Distribution", 4, 2, 65.14)  # B: sums to 98.0


def _rating_fractions(spec: Spec) -> None:
    for line in spec.rows["Rating_Distribution"][1:]:
        line[1] = round(float(str(line[1])) / 100, 6)


def _maturity_over(spec: Spec) -> None:
    _set(spec.rows, "Maturity_Profile", 6, 2, 55.5)  # sums to 102.0


def _holding_share(spec: Spec) -> None:
    _set(spec.rows, "Holdings_Detail", 2, 6, 2.4)  # market value gives 2.3715


def _par_thousands(spec: Spec) -> None:
    _set(spec.rows, "Holdings_Detail", 3, 4, 11400)  # par in thousands, value in units


def _negative_weight(spec: Spec) -> None:
    _set(spec.rows, "Sector_Exposure", 3, 2, -6.5)


def _duplicate_holding(spec: Spec) -> None:
    spec.rows["Top_Holdings"][3][1:3] = ["Beta Sample Aerospace", "Term Loan B due 2031"]


def _stale_formula(spec: Spec) -> None:
    # Headroom 0.13 as a formula whose cache was not recalculated after the limit changed.
    spec.formulas.append(("Compliance_Monitor", "J2", "D2-I2", "0.63"))


def _percent_format(spec: Spec) -> None:
    _set(spec.rows, "Top_Holdings", 2, 4, 0.0237)
    spec.percent.append(("Top_Holdings", "D2"))


def _blank_share(spec: Spec) -> None:
    _set(spec.rows, "Maturity_Profile", 3, 2, None)


def _two_currencies(spec: Spec) -> None:
    _set(spec.rows, "Exposure_Summary", 3, 3, "EUR")


def _sector_row(spec: Spec) -> None:
    _set(spec.rows, "Compliance_Monitor", 5, 9, 5.57)
    _set(spec.rows, "Compliance_Monitor", 5, 10, 4.43)


def _rank_order(spec: Spec) -> None:
    _set(spec.rows, "Top_Holdings", 5, 4, 1.6)  # rank 4 above rank 3's 1.5


def _top10(spec: Spec) -> None:
    _set(spec.rows, "Exposure_Summary", 7, 2, 7.0)  # the five largest add to 7.67


def _amount_above_nav(spec: Spec) -> None:
    _set(spec.rows, "Compliance_Monitor", 3, 9, 14962500000)  # entered in thousandths


def _checked_early(spec: Spec) -> None:
    _set(spec.rows, "Compliance_Monitor", 4, 12, "2025-02-28")


def _sector_below_holdings(spec: Spec) -> None:
    _set(spec.rows, "Sector_Exposure", 4, 2, 2.0)  # Software, below its holding's 2.37
    _set(spec.rows, "Sector_Exposure", 4, 5, 8.0)


def _matured(spec: Spec) -> None:
    _set(spec.rows, "Holdings_Detail", 4, 10, "2025-01-31")


BROKEN: dict[str, Callable[[Spec], None]] = {
    "rating-sum-short": _rating_short,
    "rating-fractions": _rating_fractions,
    "maturity-sum-over": _maturity_over,
    "holding-share-wrong": _holding_share,
    "par-in-thousands": _par_thousands,
    "negative-weight": _negative_weight,
    "duplicate-holding": _duplicate_holding,
    "stale-formula": _stale_formula,
    "percent-as-fraction": _percent_format,
    "blank-share": _blank_share,
    "two-currencies": _two_currencies,
    "sector-row-mismatch": _sector_row,
    "rank-order": _rank_order,
    "top10-exceeded": _top10,
    "amount-above-nav": _amount_above_nav,
    "checked-before-as-of": _checked_early,
    "sector-below-holdings": _sector_below_holdings,
    "matured-position": _matured,
}


def clean(as_of: str = AS_OF) -> Spec:
    return Spec(clean_rows(as_of))


def broken(kind: str, as_of: str = AS_OF) -> Spec:
    spec = Spec(copy.deepcopy(clean_rows(as_of)))
    BROKEN[kind](spec)
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--as-of", default=AS_OF)
    args = parser.parse_args(argv)
    args.folder.mkdir(parents=True, exist_ok=True)
    (args.folder / "SYNTHETIC-portfolio-clean.xlsx").write_bytes(workbook_bytes(clean(args.as_of)))
    for kind in BROKEN:
        raw = workbook_bytes(broken(kind, args.as_of))
        (args.folder / f"SYNTHETIC-portfolio-{kind}.xlsx").write_bytes(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
