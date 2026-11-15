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

from deploy_vii.inputs.__main__ import main as self_check
from deploy_vii.inputs.portfolio_export import Quantity, quantity, validate_export
from deploy_workflow.owners.cpos_launch import _readiness, prepare
from tools import synthetic_portfolio_exports as synth

RUN_DATE = date(2025, 3, 31)
REPORT = synth.EXPOSURE
BOOK = synth.HOLDINGS
MONITOR = synth.CONSTRAINTS


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
    assert report.lines() == ("OK: 5 files, 7 holdings",)
    assert [role for _, role in report.files] == [
        *("mandate", "constraints", "constraints", "exposure", "holdings")
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
    assert report.notes == ("not checked: WAL (4.82 yrs)",)


EXPECTED = {
    # Class 1. 105 / 110 x 100 = 95.4545...
    "report-not-holdings": [
        (
            REPORT,
            "A. Summary Metrics",
            "row 4",
            (
                "total par is stated as 110,000,000; the holdings give 100,000,000, a difference "
                "of "
                "10,000,000"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 3",
            (
                "NAV is stated as USD 105,000,000; the holdings give 100,000,000, a difference of "
                "5,000,000"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 5",
            "the number of positions is stated as 8; the holdings give 7, a difference of 1",
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 6",
            (
                "the number of obligors is stated as 7; the holdings give 6, a difference of 1 "
                "(6 tickers)"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 7",
            "the number of sectors is stated as 4; the holdings give 3, a difference of 1",
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 8",
            (
                "the weighted average price is stated as 100.00; the stated NAV over the stated "
                "par is "
                "95.455"
            ),
        ),
    ],
    # Class 2. Aster: 20m at 100 + 10m at 98 = 29.8m of 100m; the ten largest are all six.
    "concentration": [
        (
            REPORT,
            "A. Summary Metrics",
            "row 11",
            (
                "the largest issuer's share is stated as 35.00%; the holdings give 29.80%, a "
                "difference of 5.20% (Aster Fictional Co)"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 12",
            (
                "the ten largest issuers' share is stated as 95.00%; the holdings give 100.00%, a "
                "difference of 5.00%"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 34",
            (
                "Aster Fictional Co: its market value is stated as 35,000,000; the holdings give "
                "29,800,000, a difference of 5,200,000"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 34",
            (
                "Aster Fictional Co: its share is stated as 35.00%; the holdings give 29.80%, a "
                "difference of 5.20%"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 34",
            (
                "Aster Fictional Co: its number of positions is stated as 3; the holdings give 2, "
                "a "
                "difference of 1"
            ),
        ),
        (
            REPORT,
            "D. Top 10 Holdings",
            "row 40",
            (
                "Ghost Fictional Holdings is listed among the largest holdings but is not in the "
                "holdings"
            ),
        ),
    ],
    # Class 3. Software: 20 + 9.8 + 9.9 = 39.7m; Healthcare: 25 + 10.1 = 35.1m.
    "hidden-breach": [
        (
            REPORT,
            "C. Top Sectors",
            "row 25",
            (
                "Software: its share is stated as 34.70%; the holdings give 39.70%, a difference "
                "of "
                "5.00%"
            ),
        ),
        (
            REPORT,
            "C. Top Sectors",
            "row 25",
            (
                "Software: the holdings give 39.70% against the limit ≤ 35.0% NAV, a breach; the "
                "report states 34.70% and status Pass"
            ),
        ),
        (
            REPORT,
            "C. Top Sectors",
            "row 26",
            (
                "Healthcare: its share is stated as 40.10%; the holdings give 35.10%, a difference "
                "of "
                "5.00%"
            ),
        ),
    ],
    # Class 4. Ratings 25.20 + 64.71 + 10.10 = 100.01 against 100.00: inside the rounding of
    # four two-decimal figures (0.02), so no finding; issuers 2 + 3 + 1 = 6, not 7. Sectors
    # 39.70 + 35.10 + 25.20 + 0.00 = 100.00 against 99.90: 0.10, over 5 x 0.005.
    "subtotals": [
        (
            REPORT,
            "B. Rating Distribution",
            "row 21",
            "Total states Issuers 7; its 3 rows add to 6, a difference of 1",
        ),
        (
            REPORT,
            "C. Top Sectors",
            "row 30",
            (
                "Total states % NAV 99.90%; its 4 rows add to 100.00, a difference of 0.10, more "
                "than "
                "their rounding (0.025)"
            ),
        ),
    ],
    # Class 5. Price: 100 at mid; margin 361.25; yield 8.6125; second lien 10.1m of 100m.
    "summary-metrics": [
        (
            REPORT,
            "A. Summary Metrics",
            "row 8",
            (
                "the weighted average price is stated as 101.00; the holdings give 100, a "
                "difference "
                "of 1"
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
                "the weighted average yield to maturity is stated as 3.20%; the holdings give "
                "8.6125, "
                "a difference of 5.4125"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 13",
            (
                "the second-lien share is stated as 12.00%; the holdings give 10.10%, a difference "
                "of "
                "1.90%"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 8",
            (
                "the weighted average price is stated as 101.00; the stated NAV over the stated "
                "par is "
                "100.000"
            ),
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 10",
            (
                "the weighted average yield to maturity is stated as 3.20%, below the stated "
                "weighted "
                "average margin of 375 bps over the base rate"
            ),
        ),
    ],
    # Class 6. 50 + 20 + 10 = 80m against a stated 90m; 90m / 100m = 90%.
    "capital-structure": [
        (
            synth.MANDATE,
            "Mandate",
            "row 7",
            "the capital structure total USD 90,000,000 is not its 3 tranches' sum 80,000,000",
        ),
        (
            synth.MANDATE,
            "Mandate",
            "row 7",
            (
                "the capital structure total USD 90,000,000 is 90.00% of the collateral NAV "
                "100,000,000, outside 95% to 105%: the tranches and the collateral do not balance"
            ),
        ),
    ],
    "century-dates": [
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
    # Class 8. With row 3's -246.5: (160 - 2465 + 135 + 82.5 + 193.75 + 110 + 95) / 100 =
    # -16.8875; without it 776.25 / 90 = 8.625, which then also misses the stated 8.61.
    "impossible-values": [
        (
            BOOK,
            "Holdings",
            "Mid YTM",
            (
                "Mid YTM lies outside -10% to 100% on row 3 (-246.5%); with them the par-weighted "
                "yield is -16.89%, without them 8.62%"
            ),
        ),
        (
            BOOK,
            "Holdings",
            "Mid 3Y DM",
            "Mid 3Y DM lies outside -1000 bps to 10000 bps on row 4 (27085 bps)",
        ),
        (
            REPORT,
            "A. Summary Metrics",
            "row 10",
            (
                "the weighted average yield to maturity is stated as 8.61%; the holdings give "
                "8.625, "
                "a difference of 0.015"
            ),
        ),
    ],
    "vendor-tokens": [
        (
            BOOK,
            "Holdings",
            "Δ 1M",
            (
                "Δ 1M holds a vendor error token such as #N/A N/A on row 5; read as missing, never "
                "as "
                "zero"
            ),
        ),
        (
            BOOK,
            "Holdings",
            "Mid 3Y DM",
            (
                "Mid 3Y DM holds a vendor error token such as #N/A N/A on row 6; read as missing, "
                "never as zero"
            ),
        ),
        (BOOK, "Holdings", "Ratings", "Ratings holds a vendor error token for an agency on row 2"),
    ],
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
    "units": [
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
            "C-03: current value '10.10' has no unit; the limit '≤ 15.0% NAV' is in % NAV",
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
        "Bid holds a vendor error token such as #N/A N/A on row 8; read as missing, never as zero",
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


def test_the_self_check_takes_the_exports_files_together(tmp_path, capsys):
    paths = []
    for name, raw in synth.files(synth.clean()).items():
        (tmp_path / name).write_bytes(raw)
        paths.append(str(tmp_path / name))
    assert self_check(["validate-input", "portfolio-export", *paths, "--as-of", "2025-03-31"]) == 0
    assert capsys.readouterr().out == "OK: 5 files, 7 holdings\n"
    (tmp_path / "notes.csv").write_text("a,b\n1,2\n")
    assert (
        self_check(["validate-input", "portfolio-export", *paths, str(tmp_path / "notes.csv")]) == 1
    )
    assert "not recognised as the mandate" in capsys.readouterr().out
    assert self_check(["validate-input", "portfolio-export", *paths, "--json"]) == 0
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
        assert "- largest borrower: Aster Fictional Co, 29.80% of market value" in texts[module]
        assert f"`{synth.HOLDINGS}` (holdings)" in texts[module]
    assert not [i for i in items if "portfolio" in i]
    assert "Portfolio: " in _readiness(prepared, "sol-medium")


def test_a_full_assessment_with_a_hidden_breach_lists_it_and_is_limited(tmp_path):
    _, texts, items = launch(tmp_path, "credit_snapshot", synth.broken("hidden-breach"))
    told = texts["CP-6"].split("Portfolio export:")[1]
    assert "The export fails 3 checks, listed below as file, part and row" in told
    assert (
        f"- {REPORT}, C. Top Sectors, row 25: Software: the holdings give 39.70% against the "
        "limit ≤ 35.0% NAV, a breach; the report states 34.70% and status Pass"
    ) in told
    assert items["CP-6:portfolio-workbook-fails-checks"]["outcome"] == "limited"


@pytest.mark.parametrize("pathway", ["relative_value", "lite_credit_assessment"])
def test_other_pathways_leave_an_export_an_ordinary_source(tmp_path, pathway):
    prepared, texts, items = launch(tmp_path, pathway, synth.broken("hidden-breach"))
    assert not [m for m, text in texts.items() if "Portfolio export:" in text]
    assert not [i for i in items if "portfolio" in i]
    assert REPORT in prepared.plan.sources
