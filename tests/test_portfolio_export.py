"""The portfolio export (mandate, constraints and exposure report CSVs and a holdings workbook):
its checks with the holdings as the authority, the self-check command, and what the launcher tells
CP-0, CP-3 and CP-6 (ruling 2026-11-15-full-assessment-portfolio-workbook, "The export shape").

Every export here is SYNTHETIC (tools/synthetic_portfolio_exports.py), one per class of defect
the coordinating session found in the owner's export; no name or number is the owner's. Expected
findings are written by hand, with the arithmetic in the comment beside each. Offline only.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest
from test_cpos_launch import context_file, issuer_folder

from deploy_vii.inputs import portfolio_export as pe
from deploy_vii.inputs.__main__ import main as self_check
from deploy_vii.inputs.portfolio_export import Quantity, quantity, validate_export
from deploy_workflow.owners.cpos_launch import _readiness, prepare
from tools import synthetic_portfolio_exports as synth

RUN_DATE = date(2025, 3, 31)
REPORT = synth.EXPOSURE
BOOK = synth.HOLDINGS
MONITOR = synth.CONSTRAINTS
FIT = synth.FIT_CONSTRAINTS


def findings(spec: synth.Spec, run_date: date | None = RUN_DATE) -> list[tuple[str, ...]]:
    report = validate_export(synth.files(spec), run_date=run_date)
    return [(i.file, i.sheet, i.cell, i.problem) for i in report.issues]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("≤ 2.5% NAV", Quantity(Decimal("2.5"), "% NAV", "<=", places=1)),
        ("≥ Caa1 (numeric ≤ 17)", Quantity(Decimal(17), "rating number", "<=")),
        ("B1 (14.3)", Quantity(Decimal("14.3"), "rating number", places=1)),
        ("4.82 yrs", Quantity(Decimal("4.82"), "yrs", places=2)),
        ("313 bps", Quantity(Decimal(313), "bps")),
        ("2.7 notches", Quantity(Decimal("2.7"), "notches", places=1)),
        ("USD 300,000,000", Quantity(Decimal(300000000), "USD")),
        ("~100%", Quantity(Decimal(100), "%", approximate=True)),
        ("Info only", None),
        ("max 40 percent", None),
    ],
)
def test_figures_keep_their_unit_and_are_never_coerced(text, expected):
    assert quantity(text) == expected


def test_the_clean_export_passes_and_says_what_the_holdings_give():
    report = validate_export(synth.files(synth.clean()), run_date=RUN_DATE)
    assert report.lines() == ("OK: 6 parts, 7 holdings",)
    assert [role for _, role in report.files] == [
        *("mandate", "constraints", "constraints", "exposure", "holdings", "market")
    ]
    # Par 20 + 10 + 15 + 10 + 25 + 10 + 10 = 100m; at mid 20 + 9.8 + 15 + 9.9 + 25 + 10.1 + 10.2.
    # Margin (20x300 + 10x350 + 15x400 + 10x325 + 25x275 + 10x600 + 10x450) / 100 = 361.25;
    # yield (160 + 85 + 135 + 82.5 + 193.75 + 110 + 95) / 100 = 8.6125.
    assert report.recomputed == (
        "positions with a par: 7; par 100,000,000",
        "market value at mid of the 7 priced positions: 100,000,000",
        "borrowers: 6; tickers: 6; sectors: 3",
        "largest borrower: Aster Fictional Co, 29.80% of market value",
        "ten largest borrowers: 100.00% of market value",
        "second lien: 10.10% of market value",
        "par-weighted mid price: 100.00",
        "par-weighted margin: 361.25 bps",
        "par-weighted yield to maturity, values outside -10% to 100% left out: 8.61%",
    )
    assert report.notes == (
        (
            "not checked against the holdings (the parameter names nothing they give): C-08 "
            "Max CCC+ "
            "and below (incl. Unrated & Other); C-10 Min portfolio WAR; C-13 Max equity exposure"
        ),
        (
            "largest holdings matched by name: Aster = Aster Fictional Co (prefix); Dune Sample = "
            "Dune Sample Corp (exact); Birch = Birch Imaginary Inc (prefix); Fern = Fern "
            "Placeholder "
            "SA (ticker); Elm = Elm Invented Ltd (prefix); Cedar = Cedar Example LLC (prefix)"
        ),
        "not checked: C. Top 20 Sectors, Total Issuers, because Other Sectors states no Issuers",
        "not checked: Weighted Average Rating (WAR) (B1 (14.3))",
        pe.BUCKET_RULE,
    )


def test_the_reconciliation_table_puts_each_stated_headline_beside_the_holdings():
    report = validate_export(synth.files(synth.broken("report-not-holdings")), run_date=RUN_DATE)
    # Life: par-weighted (20 x 1552 + 10 x 1767 + 15 x 1096 + 10 x 1644 + 25 x 1917 + 10 x 2191
    # + 10 x 1371) days / 365.25 / 100 = 4.52 years from 31 March 2025.
    assert report.table[:5] == (
        ("total par", "110,000,000", "100,000,000", "10,000,000"),
        ("NAV / market value at mid", "USD 105,000,000", "100,000,000", "5,000,000"),
        ("positions (rows with a readable par: 7 of 7 rows)", "8", "7", "1"),
        ("obligors (by borrower name)", "7", "6", "1"),
        ("sectors (by Index Sector)", "4", "3", "1"),
    )
    # Recomputed figures to the stated places plus two: life 4.5211 against a stated 4.52.
    # The summary states it as `Weighted Average Life (yrs)` = `4.52`: read as 4.52 yrs.
    assert report.table[-4] == ("weighted average life", "4.52", "4.5211 yrs", "0.0011 yrs")
    # The three largest sectors by the holdings, each beside the report's sector section; the
    # third is in Other Sectors, so not listed.
    assert report.table[-3:] == (
        ("largest sector: Software", "39.70%", "39.7000%", "0.0000%"),
        ("2nd largest sector: Healthcare", "35.10%", "35.1000%", "0.0000%"),
        ("3rd largest sector: Chemicals", "not listed", "25.20%", ""),
    )
    lines = report.table_lines()
    assert lines[0] == "Reconciliation, stated against the holdings:"
    assert lines[2].split() == ["total", "par", "110,000,000", "100,000,000", "10,000,000"]


def test_the_table_reads_figures_as_the_real_summary_labels_state_them():
    # `Weighted Average Price` = `100.000` (market value equals par, so 100 at mid),
    # `Weighted Average Life (yrs)` = `4.52` (the unit from the name) and the yield as given on
    # every row, with its percent sign.
    table = validate_export(synth.files(synth.clean()), run_date=RUN_DATE).table
    assert ("weighted average price", "100.000", "100.00000", "0.00000") in table
    assert ("weighted average life", "4.52", "4.5211 yrs", "0.0011 yrs") in table
    assert ("weighted average yield, all rows", "8.61%", "8.6125%", "0.0025%") in table


def test_a_headline_the_summary_omits_is_read_from_a_constraints_row():
    spec = synth.clean()
    spec.exposure = [row for row in spec.exposure if row[:1] != ["2nd Lien"]]
    table = validate_export(synth.files(spec), run_date=RUN_DATE).table
    # Elm, the one second-lien loan: 10m at 101 = 10.1m of 100m; no unsecured loan.
    assert (
        "second lien and unsecured (constraints: SYNTHETIC CP-3C Portfolio Constraints.csv, row 8)",
        "10.10%",
        "10.1000%",
        "0.0000%",
    ) in table


def test_a_sector_limit_with_an_exclusion_in_brackets_is_still_the_largest_sector():
    # Read as an exclusion, C-03 would compare its 39.70% with 0% held in a sector "excluding
    # cash"; read as the largest sector it agrees with Software's 39.70%.
    spec = synth.clean()
    synth._set(spec.constraints, "C-03", 2, "Single sector concentration (excluding cash)")
    assert findings(spec) == []


def test_the_positions_line_states_the_row_total():
    spec = synth.clean()
    spec.holdings[6][-1] = "#N/A N/A"  # row 8: Fern's par
    report = validate_export(synth.files(spec), run_date=RUN_DATE)
    assert report.table[2] == (
        "positions (rows with a readable par: 6 of 7 rows; 1 left out)",
        "7",
        "6",
        "1",
    )


def test_an_exclusion_row_is_a_maximum_on_the_sectors_it_lists():
    # The clean export's C-15 (Tobacco, Weapons; no holding in either) passes. Listing Software
    # instead: 20 + 9.8 + 9.9 = 39.7m of 100m against at most 0%.
    spec = synth.clean()
    synth._set(spec.constraints, "C-15", 2, "Excluded sectors (Tobacco, Software)")
    assert findings(spec) == [
        (
            MONITOR,
            "Constraints",
            "row 16",
            (
                "C-15: on the holdings' 39.70% (sectors Tobacco, Software) the limit 0% NAV is "
                "breached; the status says Pass"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 16",
            (
                "C-15: the current value (sectors Tobacco, Software) is stated as 0%; the "
                "holdings give 39.70%, a difference of 39.70%"
            ),
        ),
    ]


def test_a_breach_the_report_hides_is_reported_first():
    spec = synth.broken("hidden-breach")
    synth.BROKEN["subtotals"](spec)
    synth.BROKEN["identifiers"](spec)
    found = findings(spec)
    assert "a breach" in found[0][3]
    kinds = [problem for _, _, _, problem in found]
    first_total = next(i for i, p in enumerate(kinds) if "rows add to" in p)
    first_cell = next(i for i, p in enumerate(kinds) if "FIGI" in p)
    assert 0 < first_total < first_cell


def test_the_same_export_as_sheets_of_one_workbook_gives_the_same_findings():
    clean = validate_export(synth.workbook_files(synth.clean()), run_date=RUN_DATE)
    assert clean.lines() == ("OK: 6 parts, 7 holdings",)
    assert clean.files[0] == (f"{synth.BOOK} [Mandate File]", "mandate")
    as_csv = findings(synth.broken("hidden-breach"))
    report = validate_export(synth.workbook_files(synth.broken("hidden-breach")), run_date=RUN_DATE)
    assert [(i.cell, i.problem) for i in report.issues] == [(c, p) for _, _, c, p in as_csv]
    assert report.issues[0].file == f"{synth.BOOK} [Exposure Report]"


EXPECTED = {
    # Class 1. Par and counts against the holdings (positions are rows with a readable par;
    # sectors by Index Sector); 105 / 110 x 100 = 95.4545...
    "report-not-holdings": [
        (
            REPORT,
            "A. Summary Metrics",
            "row 4",
            (
                "total par is stated as 110,000,000; the holdings give 100,000,000, a difference "
                "of 10,000,000"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 3",
            (
                "NAV is stated as USD 105,000,000; the holdings give 100,000,000, a difference "
                "of 5,000,000"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 5",
            (
                "the number of positions is stated as 8; the holdings give 7, a difference of 1 "
                "(rows with a readable par: 7 of 7 rows)"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 6",
            (
                "the number of obligors is stated as 7; the holdings give 6, a difference of 1 "
                "(by borrower name; 6 tickers)"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 7",
            (
                "the number of sectors is stated as 4; the holdings give 3, a difference of 1 "
                "(by the Index Sector column)"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 8",
            (
                "the weighted average price is stated as 100.000; the stated NAV over the stated "
                "par is 95.455"
            ),
        ),
    ],
    # Class 2. Aster (a group name, matched as a prefix of Aster Fictional Co): 20m at 100 +
    # 10m at 98 = 29.8m of 100m. Ghost matches no borrower and no borrower may be meant: no
    # ticker begins with GHO and no borrower's first word occurs in it.
    "concentration": [
        (
            REPORT,
            "A. Summary Metrics",
            "row 11",
            (
                "the largest issuer's share is stated as Aster (35.00%); the holdings give "
                "29.8000%, a difference of 5.2000% (Aster Fictional Co)"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 13",
            (
                "the ten largest issuers' share is stated as 95.00%; the holdings give "
                "100.0000%, a difference of 5.0000%"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 36",
            (
                "Aster: its market value is stated as 35,000,000; the holdings give 29,800,000, "
                "a difference of 5,200,000"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 36",
            (
                "Aster: its share is stated as 35.00%; the holdings give 29.8000%, a difference "
                "of 5.2000%"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 36",
            "Aster: its number of positions is stated as 3; the holdings give 2, a difference of 1",
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 42",
            (
                "no borrower matches Ghost by exact name, ticker or prefix (no possible borrower "
                "by ticker letters or name word); listed among the largest holdings"
            ),
        ),
    ],
    # Class 3, first because it is a breach: Software 20 + 9.8 + 9.9 = 39.7m against 35%.
    "hidden-breach": [
        (
            REPORT,
            "C. Top 20 Sectors",
            "row 28",
            (
                "Software: the holdings give 39.70% against the limit ≤ 35.0% NAV, a breach; the "
                "report states 34.70% and status Pass"
            ),
        ),
        (
            REPORT,
            "C. Top 20 Sectors",
            "row 28",
            (
                "Software: its share is stated as 34.70%; the holdings give 39.7000%, a "
                "difference of 5.0000%"
            ),
        ),
        (
            REPORT,
            "C. Top 20 Sectors",
            "row 29",
            (
                "Healthcare: its share is stated as 40.10%; the holdings give 35.1000%, a "
                "difference of 5.0000%"
            ),
        ),
    ],
    # Class 4. Ratings 100.01 against 100.00 is rounding; issuers 2 + 3 + 1 = 6, not 7. Sectors:
    # 39.70 + 35.10 + Other 25.20 = 100.00 against 99.90, over 4 x 0.005; the sector Total's
    # issuer count is not checked (Other Sectors states none).
    "subtotals": [
        (
            REPORT,
            "B. Rating Distribution",
            "row 24",
            "Total states Issuers 7; its 3 rows add to 6, a difference of 1",
        ),
        (
            REPORT,
            "C. Top 20 Sectors",
            "row 32",
            (
                "Total states % NAV 99.90%; its 3 rows add to 100.00, a difference of 0.10, more "
                "than their rounding (0.020)"
            ),
        ),
    ],
    # Class 5. Margin 36125 / 100 = 361.25; yield 861.25 / 100 = 8.6125; second lien 10.1m;
    # shown to the stated places plus two.
    "summary-metrics": [
        (
            REPORT,
            "A. Summary Metrics",
            "row 15",
            (
                "the second-lien share is stated as 12.00%; the holdings give 10.1000%, a "
                "difference of 1.9000%"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 8",
            (
                "the weighted average price is stated as 101.00; the holdings give 100.0000, a "
                "difference of 1.0000"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 9",
            (
                "the weighted average margin is stated as 375 bps; the holdings give 361.25, a "
                "difference of 13.75"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 10",
            (
                "the weighted average yield to maturity (all rows, as given) is stated as 3.20%; "
                "the holdings give 8.6125%, a difference of 5.4125%"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 8",
            (
                "the weighted average price is stated as 101.00; the stated NAV over the stated "
                "par is 100.000"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 10",
            (
                "the weighted average yield to maturity is stated as 3.20%, below the stated "
                "weighted average margin of 375 bps over the base rate"
            ),
        ),
    ],
    # Class 6. Tranche cells are an amount then text ('$40,000,000 — SOFR + 130bps'): Class
    # A-1 at 20m, so 20 + 15 + 10 + 8 + 7 + 5 + 15 = 80m against a stated 90m; 90m / 100m = 90%.
    "capital-structure": [
        (
            synth.MANDATE,
            "Mandate",
            "row 11",
            "the capital structure total $90,000,000 is not its 7 tranches' sum 80,000,000",
        ),
        (
            synth.MANDATE,
            "Mandate",
            "row 11",
            (
                "the capital structure total $90,000,000 is 90.00% of the collateral NAV "
                "100,000,000, outside 95% to 105%: the tranches and the collateral do not balance"
            ),
        ),
    ],
    # Class 7. Three maturities 100 years early (36,525 days each): life 4.5211 - 45 = -40.4789
    # as given, 4.52 read as 20xx (not applied); the WAL constraint and the buckets the same way.
    "century-dates": [
        (
            MONITOR,
            "Constraints",
            "row 12",
            (
                "C-11: the current value (weighted average life) is stated as 4.52 yrs; the "
                "holdings give -40.4789 yrs, a difference of 44.9989 yrs; with the 3 maturities "
                "before 1950 read as 20xx it would be 4.52 yrs (not applied)"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 17",
            (
                "the weighted average life is stated as 4.52; the holdings give -40.4789 "
                "yrs, a difference of 44.9989 yrs; with the 3 maturities before 1950 read as "
                "20xx it would be 4.52 yrs (not applied)"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 46",
            (
                "maturity bucket 2028: its share is stated as 25.20%; the holdings give "
                "10.2000%, a difference of 15.0000%; with the maturities before 1950 read as "
                "20xx it would be 25.20% (not applied)"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 46",
            (
                "maturity bucket 2028: its market value is stated as 25,200,000; the holdings "
                "give 10,200,000, a difference of 15,000,000; with the maturities before 1950 "
                "read as 20xx it would be 25,200,000 (not applied)"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 47",
            (
                "maturity bucket 2029: its share is stated as 29.90%; the holdings give 9.9000%, "
                "a difference of 20.0000%; with the maturities before 1950 read as 20xx it would "
                "be 29.90% (not applied)"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 47",
            (
                "maturity bucket 2029: its market value is stated as 29,900,000; the holdings "
                "give 9,900,000, a difference of 20,000,000; with the maturities before 1950 "
                "read as 20xx it would be 29,900,000 (not applied)"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 48",
            (
                "maturity bucket 2030: its share is stated as 34.80%; the holdings give "
                "25.0000%, a difference of 9.8000%; with the maturities before 1950 read as 20xx "
                "it would be 34.80% (not applied)"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 48",
            (
                "maturity bucket 2030: its market value is stated as 34,800,000; the holdings "
                "give 25,000,000, a difference of 9,800,000; with the maturities before 1950 "
                "read as 20xx it would be 34,800,000 (not applied)"
            ),
        ),
        (
            BOOK,
            "Holdings",
            "Maturity",
            "3 of 7 maturities fall in 1928 to 1930 (rows 2, 3, 4): two-digit years read as 19xx",
        ),
        (
            BOOK,
            "Market Data",
            "Maturity",
            "1 of 3 maturities falls in 1931 (row 2): two-digit years read as 19xx",
        ),
    ],
    # Class 8. As given, with row 3's -246.5 on 10m, the yield is (776.25 - 2,465) / 100 =
    # -16.8875; without it, 776.25 / 90 = 8.625, which also misses 8.61.
    "impossible-values": [
        (
            REPORT,
            "A. Summary Metrics",
            "row 10",
            (
                "the weighted average yield to maturity (all rows, as given) is stated as 8.61%; "
                "the holdings give -16.8875%, a difference of 25.4975%; without the values "
                "outside -10% to 100% it would be 8.62% (not applied)"
            ),
        ),
        (
            BOOK,
            "Holdings",
            "Mid YTM",
            (
                "Mid YTM lies outside -10% to 100% on row 3 (-246.5%); with them the "
                "par-weighted yield is -16.89%, without them 8.62%"
            ),
        ),
        (
            BOOK,
            "Holdings",
            "Mid 3Y DM",
            "Mid 3Y DM lies outside -1000 bps to 10000 bps on row 4 (27085 bps)",
        ),
    ],
    # Class 9. WR / NR reads Birch (15m) as unrated: the unrated limit of 5% is breached on the
    # holdings while the monitor says 0.00% and Pass (first); BB keeps Fern alone.
    "vendor-tokens": [
        (
            MONITOR,
            "Constraints",
            "row 10",
            (
                "C-09: on the holdings' 15.00% (unrated) the limit ≤ 5.0% NAV is breached; the "
                "status says Pass"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 10",
            (
                "C-09: the current value (unrated) is stated as 0.00%; the holdings give "
                "15.0000%, a difference of 15.0000%"
            ),
        ),
        (
            REPORT,
            "B. Rating Distribution",
            "row 21",
            (
                "rating bucket BB (BB): its share is stated as 25.20%; the holdings give "
                "10.2000%, a difference of 15.0000%"
            ),
        ),
        (
            REPORT,
            "B. Rating Distribution",
            "row 21",
            (
                "rating bucket BB (BB): its issuer count is stated as 2; the holdings give 1, a "
                "difference of 1"
            ),
        ),
        (
            REPORT,
            "B. Rating Distribution",
            "rows",
            "the report lists no Unrated row; the holdings put 15.00% (1 issuer) there",
        ),
        (
            BOOK,
            "Holdings",
            "Δ 1M",
            (
                "Δ 1M holds a vendor error token such as #N/A N/A on row 5; read as missing, "
                "never as zero"
            ),
        ),
        (
            BOOK,
            "Holdings",
            "Mid 3Y DM",
            (
                "Mid 3Y DM holds a vendor error token such as #N/A N/A on row 6; read as "
                "missing, never as zero"
            ),
        ),
        (BOOK, "Holdings", "Ratings", "Ratings holds a vendor error token for an agency on row 2"),
    ],
    # Class 10.
    "identifiers": [
        (BOOK, "Holdings", "FIGI", "1 FIGI is not 12 capital letters and digits (row 4)"),
        (
            BOOK,
            "Holdings",
            "FIGI",
            "FIGI BBG00SYN0004 is used on rows 5, 6, for different borrowers",
        ),
        (
            BOOK,
            "Holdings",
            "Ticker",
            (
                "ticker ASTR names 2 borrowers: Aster Fictional Co (row 2); Fern Placeholder SA "
                "(row 8)"
            ),
        ),
        (
            BOOK,
            "Market Data",
            "Borrower Name",
            "borrower name 'Hazel Spec\\ufffdmen Corp' on row 3 holds damaged characters",
        ),
        (BOOK, "Market Data", "Ranking", "Ranking on row 4 holds a rating, 'B1 / B'"),
        (
            BOOK,
            "Holdings",
            "rows",
            "rows below the header with only empty cells: 3 (rows 9, 10, 11)",
        ),
    ],
    # Class 12, in the monitor only, so it now also differs from the second constraints file.
    "units": [
        (
            MONITOR,
            "Constraints",
            "row 3",
            (
                "Aggregate top 10 issuers: limit is ≤ 100.0% NAV in SYNTHETIC CP-3C Portfolio "
                "Constraints.csv (row 3) and max 40 percent here"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 4",
            (
                "Max single sector (largest: Software): current is 39.70% in SYNTHETIC CP-3C "
                "Portfolio Constraints.csv (row 4) and 10.10 here"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 2",
            "C-01 current '~29.8%' is approximate; it is not read as an exact figure",
        ),
        (
            MONITOR,
            "Constraints",
            "row 3",
            "C-02 limit 'max 40 percent' cannot be read as a figure with its unit; not coerced",
        ),
        (
            MONITOR,
            "Constraints",
            "row 4",
            "C-03: current value '10.10' has no unit; the limit '≤ 40.0% NAV' is in % NAV",
        ),
    ],
    # A bid above its ask (the mid, 99, does not move).
    "crossed-quote": [
        (BOOK, "Holdings", "Bid", "the bid is above the ask on row 5 (row 5: bid 99.5, ask 98.5)"),
    ],
    # 25,000,000 par in a 20 million tranche.
    "above-tranche": [
        (
            BOOK,
            "Holdings",
            "Holdings (par)",
            "row 6 holds par 25,000,000 of a tranche of 20 million",
        ),
    ],
    # The reverse of a ticker naming two borrowers.
    "borrower-two-tickers": [
        (
            BOOK,
            "Holdings",
            "Ticker",
            "borrower Aster Fictional Co has 2 tickers: ASTR (row 2); ASTR2 (row 3)",
        ),
    ],
    # On Market Data, so no recomputed figure moves.
    "wrong-kind": [
        (BOOK, "Market Data", "Ratings", "Ratings on row 2 holds a ranking, '1st Lien'"),
        (BOOK, "Market Data", "Loan Name", "Loan Name on row 3 holds a FIGI, 'BBG00SYN0102'"),
    ],
    # Moody's B2/B2/B3/B1 -> B (Aster, Cedar, Dune: 64.70, 3); Ba3/Ba2 -> BB (25.20, 2).
    "rating-buckets": [
        (
            REPORT,
            "B. Rating Distribution",
            "row 21",
            (
                "rating bucket BB (BB): its share is stated as 30.20%; the holdings give "
                "25.2000%, a difference of 5.0000%"
            ),
        ),
        (
            REPORT,
            "B. Rating Distribution",
            "row 21",
            (
                "rating bucket BB (BB): its issuer count is stated as 3; the holdings give 2, a "
                "difference of 1"
            ),
        ),
        (
            REPORT,
            "B. Rating Distribution",
            "row 22",
            (
                "rating bucket B (B): its share is stated as 59.70%; the holdings give 64.7000%, "
                "a difference of 5.0000%"
            ),
        ),
        (
            REPORT,
            "B. Rating Distribution",
            "row 22",
            (
                "rating bucket B (B): its issuer count is stated as 2; the holdings give 3, a "
                "difference of 1"
            ),
        ),
    ],
    # 2028: Birch 15 + Fern 10.2 = 25.2m; 2029: Aster 20 + Cedar 9.9 = 29.9m.
    "maturity-buckets": [
        (
            REPORT,
            "E. Maturity Profile",
            "row 46",
            (
                "maturity bucket 2028: its share is stated as 30.20%; the holdings give "
                "25.2000%, a difference of 5.0000%"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 46",
            (
                "maturity bucket 2028: its market value is stated as 30,200,000; the holdings "
                "give 25,200,000, a difference of 5,000,000"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 47",
            (
                "maturity bucket 2029: its share is stated as 24.90%; the holdings give "
                "29.9000%, a difference of 5.0000%"
            ),
        ),
        (
            REPORT,
            "E. Maturity Profile",
            "row 47",
            (
                "maturity bucket 2029: its market value is stated as 24,900,000; the holdings "
                "give 29,900,000, a difference of 5,000,000"
            ),
        ),
    ],
    # First lien (leading 1L): 100 - 10.1 (Elm, 2L) = 89.9m.
    "lien-split": [
        (
            REPORT,
            "A. Summary Metrics",
            "row 14",
            (
                "the first-lien share is stated as 85.00%; the holdings give 89.9000%, a "
                "difference of 4.9000%"
            ),
        ),
    ],
    # The fund names Dune as largest issuer (Aster is, 29.80%) and Chemicals as second largest
    # sector (Healthcare is, 35.10%); the named sector's own share is compared: 25.20 vs 35.10.
    "named-largest": [
        (
            MONITOR,
            "Constraints",
            "row 2",
            (
                "C-01: names Dune Sample (Dune Sample Corp, by exact) as the largest issuer; in "
                "the holdings it is Aster Fictional Co (29.80%)"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 5",
            (
                "C-04: names Chemicals as the 2nd largest sector; in the holdings it is "
                "Healthcare (35.10%)"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 5",
            (
                "C-04: the current value (sector Chemicals) is stated as 35.10%; the holdings "
                "give 25.2000%, a difference of 9.9000%"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 11",
            (
                "the largest issuer's share is stated as Dune Sample (25.00%); the holdings give "
                "29.8000%, a difference of 4.8000% (Aster Fictional Co)"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 11",
            (
                "the summary names Dune Sample (Dune Sample Corp, by exact) as the largest "
                "issuer; in the holdings it is Aster Fictional Co (29.80%)"
            ),
        ),
    ],
    # The second constraints file states 12.10% for the 2nd-lien row; the monitor 10.10%.
    "constraint-files-differ": [
        (
            FIT,
            "Constraints",
            "row 8",
            (
                "Max 2nd Lien / Unsecured: the current value (second lien and unsecured) is "
                "stated as 12.10%; the holdings give 10.1000%, a difference of 2.0000%"
            ),
        ),
        (
            FIT,
            "Constraints",
            "row 8",
            (
                "Max 2nd Lien / Unsecured: headroom 4.90% is not the limit ≤ 15.0% NAV less the "
                "current value 12.10% (2.90)"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 8",
            (
                "Max 2nd Lien / Unsecured: current is 12.10% in SYNTHETIC CP-3C Portfolio "
                "Constraints.csv (row 8) and 10.10% here"
            ),
        ),
    ],
    # Cedar's position held by 'Aster Sample LLC': 'Aster' matches two borrowers (a note, not
    # compared) and 'Cedar' matches none (a finding); its ticker CEDR begins with CED, so Aster
    # Sample LLC is named as possible and not compared.
    "ambiguous-name": [
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 41",
            (
                "no borrower matches Cedar by exact name, ticker or prefix (possible, not "
                "compared: Aster Sample LLC (ticker CEDR begins with the same three letters)); "
                "listed among the largest holdings"
            ),
        ),
    ],
    # Birch's Ranking 'Sr. Secd' has no lien token: not classified, so first lien is
    # 89.9 - 15 = 74.9%, and the 85% minimum is breached on the holdings while both files say Pass.
    # Three listed names no borrower matches by exact name, ticker or prefix, each with what may be
    # meant: Birch's ticker BRCH begins with BRC; Dune, Dune Sample Corp's first word, is inside
    # Sanddune; nothing points from Quill Holdings to a borrower. None is compared.
    "brand-names": [
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 37",
            (
                "no borrower matches Sanddune Health by exact name, ticker or prefix (possible, "
                "not compared: Dune Sample Corp (Dune of the borrower's name occurs in the listed "
                "name)); listed among the largest holdings"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 38",
            (
                "no borrower matches Brcknell Group by exact name, ticker or prefix (possible, "
                "not compared: Birch Imaginary Inc (ticker BRCH begins with the same three "
                "letters)); listed among the largest holdings"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 39",
            (
                "no borrower matches Quill Holdings by exact name, ticker or prefix (no possible "
                "borrower by ticker letters or name word); listed among the largest holdings"
            ),
        ),
    ],
    "unclassified-lien": [
        (
            FIT,
            "Constraints",
            "row 7",
            (
                "Min 1st Lien / Senior Secured: on the holdings' 74.90% (first lien) the limit ≥ "
                "85.0% NAV is breached; the status says Pass"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 7",
            (
                "C-06: on the holdings' 74.90% (first lien) the limit ≥ 85.0% NAV is breached; "
                "the status says Pass"
            ),
        ),
        (
            FIT,
            "Constraints",
            "row 7",
            (
                "Min 1st Lien / Senior Secured: the current value (first lien) is stated as "
                "89.90%; the holdings give 74.9000%, a difference of 15.0000%"
            ),
        ),
        (
            MONITOR,
            "Constraints",
            "row 7",
            (
                "C-06: the current value (first lien) is stated as 89.90%; the holdings give "
                "74.9000%, a difference of 15.0000%"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 14",
            (
                "the first-lien share is stated as 89.90%; the holdings give 74.9000%, a "
                "difference of 15.0000%"
            ),
        ),
        (
            BOOK,
            "Holdings",
            "Ranking",
            (
                "Ranking states no lien (1L, 2L, first, second, unsecured) on row 4; not "
                "classified, and not counted as first lien"
            ),
        ),
    ],
}


def test_every_class_but_the_unpriced_one_has_its_expected_findings():
    assert set(EXPECTED) == set(synth.BROKEN) - {"unpriced-position"}


@pytest.mark.parametrize("kind", sorted(EXPECTED))
def test_each_defect_class_is_found_where_it_is(kind):
    assert findings(synth.broken(kind)) == EXPECTED[kind]


def test_a_metric_in_another_unit_is_not_checked_as_the_metric_it_sounds_like():
    spec = synth.clean()
    spec.exposure.insert(13, ["Sector Concentration (Top 1)", "39.70%", ""])
    report = validate_export(synth.files(spec), run_date=RUN_DATE)
    assert report.ok
    assert "not checked: Sector Concentration (Top 1) (39.70%)" in report.notes


def test_withdrawn_ratings_and_watch_flags_are_notes_not_defects():
    report = validate_export(synth.files(synth.broken("vendor-tokens")), run_date=RUN_DATE)
    assert report.notes[:2] == (
        "Holdings: ratings withdrawn or not rated (WR, NR) on row 4; read as unrated",
        "Holdings: ratings with a watch flag (*+, *-) on row 5; read without the flag",
    )


def test_an_unpriced_position_is_missing_from_value_never_valued_at_zero_price():
    found = findings(synth.broken("unpriced-position"))
    # Fern (10m par) has no price: value 100 - 10.2 = 89.8m; Aster 29.8 / 89.8 = 33.18%.
    assert (
        BOOK,
        "Holdings",
        "Bid",
        (
            "Bid holds a vendor error token such as #N/A N/A on row 8; read as missing, never as "
            "zero; par affected 10,000,000"
        ),
    ) in found
    assert (
        REPORT,
        "A. Summary Metrics",
        "row 3",
        (
            "NAV is stated as USD 100,000,000; the holdings give 89,800,000, a difference of "
            "10,200,000; it leaves out 1 position with no price"
        ),
    ) in found
    # On the holdings' figures the issuer limit of 30% is breached; the monitor says Watch.
    assert (
        MONITOR,
        "Constraints",
        "row 2",
        (
            "C-01: on the holdings' 33.18% (largest issuer (Aster Fictional Co)) the limit "
            "≤ 30.0% NAV is breached; the status says Watch"
        ),
    ) in found


@pytest.mark.parametrize(
    ("run_date", "word"),
    [(date(2025, 4, 30), None), (date(2025, 5, 1), "stale"), (date(2025, 3, 30), "after")],
)
def test_the_exports_dates_against_the_run_date(run_date, word):
    found = findings(synth.clean(), run_date)
    if word is None:  # 30 days
        assert found == []
        return
    files = [f for f, sheet, _, problem in found if sheet == "dates" and word in problem]
    assert files == [synth.MANDATE, MONITOR]


def test_without_a_holdings_sheet_nothing_stated_can_be_verified():
    files = synth.files(synth.clean())
    del files[BOOK]
    report = validate_export(files, run_date=RUN_DATE)
    assert (report.issues[0].problem, report.issues[0].fix) == (
        "no holdings sheet is among the files",
        "add the holdings sheet: without it no stated figure can be verified",
    )


def test_the_self_check_takes_a_folder_and_prints_the_table_first(tmp_path, capsys):
    folder = tmp_path / "export"
    folder.mkdir()
    for name, raw in synth.files(synth.clean()).items():
        (folder / name).write_bytes(raw)
    (folder / "~$SYNTHETIC Holdings.xlsx").write_bytes(b"lock")  # Office's lock file: skipped
    assert (
        self_check(["validate-input", "portfolio-exports", str(folder), "--as-of", "2025-03-31"])
        == 0
    )
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "Reconciliation, stated against the holdings:"
    assert out[-1] == "OK: 6 parts, 7 holdings"
    paths = sorted(str(p) for p in folder.iterdir() if not p.name.startswith("~$"))
    (tmp_path / "notes.csv").write_text("a,b\n1,2\n")
    assert (
        self_check(["validate-input", "portfolio-export", *paths, str(tmp_path / "notes.csv")]) == 1
    )
    assert "not recognised as the mandate" in capsys.readouterr().out
    assert self_check(["validate-input", "portfolio-exports", *paths, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["recomputed"][0].startswith("positions with a par")
    with pytest.raises(SystemExit) as stopped:
        self_check(["validate-input", "portfolio", *paths[:2]])
    assert stopped.value.code == 2


# --- The launcher --------------------------------------------------------------------------------


def launch(tmp_path, pathway: str, spec: synth.Spec | None, *, declared: bool = True):
    context = context_file(tmp_path, pathway)
    data = json.loads(context.read_text())
    data["attachments"]["portfolio_workbook"] = declared
    context.write_text(json.dumps(data))
    folder = issuer_folder(tmp_path)
    for name, raw in (synth.files(spec) if spec is not None else {}).items():
        (folder / name).write_bytes(raw)
    prepared = prepare(context, folder, tmp_path / "run", config="sol-medium", cap="20")
    texts = {
        module: (prepared.directory / pin.path).read_text()
        for module, pin in prepared.plan.instructions.items()
    }
    return prepared, texts, {item["id"]: item for item in prepared.expectations}


def test_a_full_assessment_with_a_clean_export_tells_cp0_cp3_and_cp6_what_the_holdings_give(
    tmp_path,
):
    prepared, texts, items = launch(tmp_path, "credit_snapshot", synth.clean())
    told = [m for m, text in texts.items() if "Portfolio export:" in text]
    assert told == ["CP-0", "CP-3", "CP-6"]
    for module in told:
        assert "The export passes every check." in texts[module]
        assert (
            "- total par: stated 100,000,000; holdings 100,000,000; difference 0" in texts[module]
        )
        assert "- largest borrower: Aster Fictional Co, 29.80% of market value" in texts[module]
        assert f"`{synth.HOLDINGS} [Holdings]` (holdings)" in texts[module]
    assert not [i for i in items if "portfolio" in i]
    assert "Portfolio: " in _readiness(prepared, "sol-medium")


def test_a_full_assessment_with_a_hidden_breach_lists_it_and_is_limited(tmp_path):
    _, texts, items = launch(tmp_path, "credit_snapshot", synth.broken("hidden-breach"))
    told = texts["CP-6"].split("Portfolio export:")[1]
    assert "The export fails 3 checks, listed below as file, part and row" in told
    assert (
        f"- {REPORT}, C. Top 20 Sectors, row 28: Software: the holdings give 39.70% against the "
        "limit ≤ 35.0% NAV, a breach; the report states 34.70% and status Pass"
    ) in told
    assert items["CP-6:portfolio-workbook-fails-checks"]["outcome"] == "limited"


@pytest.mark.parametrize("pathway", ["relative_value", "lite_credit_assessment"])
def test_other_pathways_leave_an_export_an_ordinary_source(tmp_path, pathway):
    prepared, texts, items = launch(tmp_path, pathway, synth.broken("hidden-breach"))
    assert not [m for m, text in texts.items() if "Portfolio export:" in text]
    assert not [i for i in items if "portfolio" in i]
    assert REPORT in prepared.plan.sources


# --- The real layout's facts, one by one (SYNTHETIC values) --------------------------------------


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        ("$280,000,000 — SOFR + 130bps", Decimal(280000000)),  # an amount, then a note
        ("$45,000,000", Decimal(45000000)),  # the equity row: a bare amount
        ("USD 12,500,000 – SOFR + 650bps", Decimal(12500000)),
        ("SOFR + 130bps", None),  # no leading amount
    ],
)
def test_a_capital_structure_cell_is_read_by_its_leading_amount(text, amount):
    found = pe.leading_amount(text)
    assert (found.value if found is not None else None) == amount


def test_a_limit_without_a_sign_takes_its_direction_from_the_parameter():
    zero = quantity("0% NAV")
    assert zero == Quantity(Decimal(0), "% NAV")
    assert pe._with_direction(zero, "Max equity exposure").operator == "<="
    assert pe._with_direction(zero, "Min number of obligors").operator == ">="
    # An exclusion is a maximum, and a zero limit with no direction word is "at most 0%".
    assert pe._with_direction(zero, "Excluded sectors (Tobacco, Weapons)").operator == "<="
    assert pe._with_direction(zero, "Prohibited instruments").operator == "<="
    assert pe._with_direction(zero, "Equity exposure").operator == "<="
    five = quantity("5% NAV")
    assert five is not None
    assert pe._with_direction(five, "Excluded sectors (Tobacco)").operator == "<="
    assert pe._with_direction(five, "Equity exposure").operator == ""
    # An exclusion inside the brackets does not make a minimum a maximum.
    assert pe._with_direction(five, "Min first lien (excluding cash)").operator == ">="


def test_the_second_constraints_layout_is_recognised():
    header = list(synth.FIT_HEADER)  # Limit / Guideline, Current Exposure; no ID or dates
    assert pe.is_constraints([header])
    assert not pe.is_constraints([["Constraint Category", "Parameter", "Status"]])


@pytest.mark.parametrize(
    ("ranking", "kind"),
    [
        ("1L Gtd Sr. Secd", "first"),
        ("1L Sr. Secd", "first"),
        ("2L Secd", "second"),
        ("2L Otd Secd", "second"),
        ("Second Lien", "second"),
        ("Sr Unsecd", "unsecured"),
        ("Sr. Secd", "unclassified"),  # no lien token: reported, not counted as first lien
    ],
)
def test_the_lien_is_the_rankings_leading_token(ranking, kind):
    holding = pe.Holding(2, "Holdings", {"ranking": ranking}, {})
    assert pe.lien(holding) == kind


def _borrowers(*rows: tuple[str, str]) -> pe.Recomputed:
    found = pe.Recomputed()
    for name, ticker in rows:
        key = pe.folded(name)
        found.names[key] = name
        found.borrowers[key] = []
        found.tickers_of[key] = {ticker}
    return found


@pytest.mark.parametrize(
    ("name", "how", "matched"),
    [
        ("Dune Sample Corp.", "exact", ["dune sample corp"]),  # punctuation and suffix ignored
        ("dune sample", "exact", ["dune sample corp"]),
        ("ASTR", "ticker", ["aster fictional co"]),
        ("Aster", "prefix", ["aster fictional co", "aster sample llc"]),  # ambiguous: two
        ("Aster Fictional", "exact", ["aster fictional co"]),  # "Co" is a legal suffix
        ("Fictional", "", []),  # a word inside a name is not a prefix: no match
        ("Ghost", "", []),
    ],
)
def test_a_report_name_is_matched_to_a_borrower_on_a_stated_basis(name, how, matched):
    found = _borrowers(
        ("Aster Fictional Co", "ASTR"), ("Aster Sample LLC", "ASTS"), ("Dune Sample Corp", "DUNE")
    )
    assert pe.match_issuer(name, found) == (how, matched)


def test_the_top_ten_total_row_is_read_as_a_total_from_the_issuer_column():
    spec = synth.clean()
    total = next(row for row in spec.exposure if len(row) > 1 and row[1] == "Top 10 Total")
    total[5] = "99,000,000"  # the rows add to 100,000,000
    assert findings(spec) == [
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 42",
            (
                "Top 10 Total states MV ($) 99,000,000; its 6 rows add to 100000000, a "
                "difference of "
                "1000000, more than their rounding (3.5)"
            ),
        )
    ]


def test_not_applicable_cells_and_info_rows_are_not_defects():
    report = validate_export(synth.files(synth.clean()), run_date=RUN_DATE)
    # C-13 has headroom "—" and C-14 is Info only with breach type and headroom "—".
    assert report.ok
