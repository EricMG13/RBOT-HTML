"""The methods' own scripts run on a returned handoff (`deploy_workflow.method_scripts`).

SYNTHETIC: every handoff here is hand-made in the transport's layout (`##` sections, registers as
`###` headings with pipe tables). No model wrote them; the register and column names a real
CP-2D or CP-3C writes are unproven until a paid run. Every expected value is worked by hand in the
comment beside it, never by calling the script.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

from deploy_workflow import method_scripts as ms

ROOT = Path(__file__).resolve().parents[1]
CALCULATORS = (
    "skills/cp-2d-liquidity-cash-flow-bridge/scripts/liquidity_bridge.py",
    "skills/cp-3c-refinancing-lme-risk/scripts/funding_gap.py",
    "skills/cp-1-canonical-data-foundation/scripts/credit_metrics.py",
    "skills/cp-2e-macro-fx-hedging-sensitivity/scripts/rate_fx_sensitivity.py",
    "skills/cp-1c-peer-benchmark/scripts/peer_statistics.py",
    "skills/cp-2h-ratings-migration-trigger/scripts/covenant_headroom.py",
    "skills/cp-3d-market-implied-risk/scripts/bond_analytics.py",
    "skills/cp-4c-restructuring-fulcrum/scripts/recovery_waterfall.py",
)


def statuses(outcomes):
    return {o.figure: o.status for o in outcomes}


# --- loading ------------------------------------------------------------------------------------


@pytest.mark.parametrize("path", CALCULATORS)
def test_each_calculator_passes_its_own_self_check(path, capsys):
    loaded = ms.load(ms.ARCHIVE + path)
    loaded.script._self_check()
    assert "self-check: OK" in capsys.readouterr().out


def test_loading_leaves_no_trace_in_the_interpreter_or_the_archive():
    path, modules, bytecode = list(sys.path), set(sys.modules), sys.dont_write_bytecode
    ms.load(ms.LIQUIDITY_BRIDGE)
    assert sys.path == path
    assert set(sys.modules) == modules
    assert sys.dont_write_bytecode is bytecode
    assert not list((ROOT / ms.ARCHIVE).rglob("__pycache__/*liquidity_bridge*"))
    assert not list((ROOT / ms.ARCHIVE / "scripts").glob("__pycache__"))


def copy_archive(tmp_path: Path) -> Path:
    for name in (
        ms.MANIFEST,
        ms.LIQUIDITY_BRIDGE,
        *(f"{ms.SHARED}{n}.py" for n in ms.SHARED_MODULES),
    ):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, tmp_path / name)
    return tmp_path


def test_a_script_whose_bytes_are_not_registered_is_refused(tmp_path):
    root = copy_archive(tmp_path)
    assert ms.load(ms.LIQUIDITY_BRIDGE, root).script.compute  # the copy itself loads
    with (root / ms.LIQUIDITY_BRIDGE).open("a") as script:
        script.write("\n# one byte more\n")
    with pytest.raises(ms.ScriptRefused, match="not the registered ones"):
        ms.load(ms.LIQUIDITY_BRIDGE, root)


def test_a_changed_shared_module_is_refused_too(tmp_path):
    root = copy_archive(tmp_path)
    with (root / ms.SHARED / "cp_tables.py").open("a") as shared:
        shared.write("\nNULL_CELLS.add('0')\n")
    with pytest.raises(ms.ScriptRefused, match="cp_tables.py"):
        ms.load(ms.LIQUIDITY_BRIDGE, root)


def test_an_unregistered_script_is_refused(tmp_path):
    root = copy_archive(tmp_path)
    data = json.loads((root / ms.MANIFEST).read_text())
    data["files"] = [e for e in data["files"] if e["archive_path"] != ms.LIQUIDITY_BRIDGE]
    (root / ms.MANIFEST).write_text(json.dumps(data))
    with pytest.raises(ms.ScriptRefused, match="not registered"):
        ms.load(ms.LIQUIDITY_BRIDGE, root)


def test_the_registered_hashes_are_the_files_on_disk():
    hashes = ms.registered()
    for path in (
        *(ms.ARCHIVE + p for p in CALCULATORS),
        *(f"{ms.SHARED}{n}.py" for n in ms.SHARED_MODULES),
    ):
        assert hashes[path] == hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), path


# --- CP-2D --------------------------------------------------------------------------------------

# SYNTHETIC, USD millions. Beginning accessible liquidity 400 (cash 310 + accessible revolver 90).
# Net movement: 85 - 15 - 42 - 8 - 55 - 60 - 12 + 7 = -100, so the ending is 400 - 100 = 300.
# Average monthly burn 100 / 12 = 8.3333...; Months to Empty 400 / (100 / 12) = 48 exactly.
BRIDGE = {
    "Beginning cash": "310",
    "Accessible revolver availability": "90",
    "Beginning accessible liquidity": "400",
    "Operating cash inflow/outflow": "85",
    "Working-capital impact": "(15)",
    "Cash interest": "42",
    "Cash taxes": "8",
    "Mandatory capex": "55",
    "Debt amortization/maturities": "60",
    "Other cash uses": "12",
    "Committed inflows": "7",
    "Ending accessible liquidity": "300",
}


def cp2d(rows=None, units=None, months="48.0", basis="T2E.5 bridge, 12 months; recurring"):
    rows = dict(BRIDGE) if rows is None else rows
    units = units or {}
    lines = [
        f"| {item} | {amount} | {units.get(item, 'USD m')} | Calculated | Synthetic. | S1 |"
        for item, amount in rows.items()
    ]
    return "\n".join(
        [
            "---",
            "module: CP-2D",
            "---",
            "## Request",
            "SYNTHETIC handoff.",
            "## Findings",
            "### Bottom line",
            "Liquidity is adequate.",
            "### T2E.5 — 12-Month Liquidity Bridge",
            "| Bridge Item | Amount | Currency and Scale | Status | Comment | Source Trace |",
            "|---|---|---|---|---|---|",
            *lines,
            "",
            "### T2E.6 — Months to Empty Result",
            "| Calculation | Result | Formula / Inputs | Cash-Burn Basis | Status | Source Trace |",
            "|---|---|---|---|---|---|",
            f"| Months to Empty | {months} | 400 / (100 / 12) | {basis} | Calculated | T2E.5 |",
            "## Gaps",
            "None.",
        ]
    )


def test_cp2d_all_figures_right():
    outcomes = ms.run("CP-2D", cp2d())
    assert statuses(outcomes) == {ms.ENDING: "agreed", ms.MTE: "agreed"}
    ending = outcomes[0]
    assert (ending.stated, ending.recomputed, ending.unit) == ("300", 300.0, "USD m")
    # One unit (no decimal shown) plus the inputs' rounding: nine whole-number inputs, each up to
    # 0.5 off, so 1 + 9 x 0.5 = 5.5 (coordinator's review, 2026-11-15).
    assert ending.tolerance == 5.5
    # `48.0`: 0.1, plus the quotient's first-order bound: liquidity 400 (+-0.5) over the burn
    # 100 / 12 = 8.333 (+-8 x 0.5 / 12 = 0.333): (0.5 + 48 x 0.333) / 8.333 = 1.98.
    assert outcomes[1].tolerance == pytest.approx(0.1 + 16.5 / (100 / 12))
    assert ms.issues("CP-2D", cp2d()) == ()


def test_cp2d_one_figure_wrong_is_an_issue_naming_register_row_values_and_formula():
    text = cp2d(BRIDGE | {"Ending accessible liquidity": "310"})
    outcomes = ms.run("CP-2D", text)
    assert statuses(outcomes) == {ms.ENDING: "disagreed", ms.MTE: "agreed"}  # MTE reads inputs
    (issue,) = ms.issues("CP-2D", text)
    assert "T2E.5 row `Ending accessible liquidity` states 310 USD m" in issue
    assert "recomputes 300 USD m" in issue
    assert "liquidity_bridge.py" in issue and "- Cash interest" in issue


def test_cp2d_a_cash_use_written_negative_is_subtracted_as_written():
    # (42) instead of 42: the formula subtracts -42, so the ending is 300 + 84 = 384, not 300.
    outcomes = ms.run("CP-2D", cp2d(BRIDGE | {"Cash interest": "(42)"}))
    assert outcomes[0].status == "disagreed" and outcomes[0].recomputed == 384.0
    assert "written negative is added" in outcomes[0].reason
    # The burn is now 16 / 12 a month: 400 / (16 / 12) = 300 months, not the stated 48.0.
    assert outcomes[1].status == "disagreed" and outcomes[1].recomputed == 300.0


def test_cp2d_a_missing_input_is_not_checked_and_never_zero():
    rows = {k: v for k, v in BRIDGE.items() if k != "Cash taxes"}
    outcomes = ms.run("CP-2D", cp2d(rows))
    assert statuses(outcomes) == {ms.ENDING: "not checked", ms.MTE: "not checked"}
    assert "no `Cash taxes` row (absent, not zero)" in outcomes[0].reason
    assert ms.issues("CP-2D", cp2d(rows)) == ()


def test_cp2d_a_blank_is_missing_and_a_zero_is_a_figure():
    blank = ms.run("CP-2D", cp2d(BRIDGE | {"Cash taxes": "Not supplied: no tax schedule"}))
    assert statuses(blank) == {ms.ENDING: "not checked", ms.MTE: "not checked"}
    assert "states no amount for `Cash taxes` (missing, not zero)" in blank[0].reason
    # Taxes 0 instead of 8: the ending is 300 + 8 = 308, the burn 92 / 12 and MTE
    # 400 / (92 / 12) = 52.17... (stated 52.2, one decimal place).
    zero = ms.run("CP-2D", cp2d(BRIDGE | {"Cash taxes": "0", ENDING: "308"}, months="52.2"))
    assert statuses(zero) == {ms.ENDING: "agreed", ms.MTE: "agreed"}


def test_cp2d_a_scale_mismatch_is_not_compared():
    outcomes = ms.run("CP-2D", cp2d(units={"Cash taxes": "USD bn"}))
    assert statuses(outcomes) == {ms.ENDING: "not checked", ms.MTE: "not checked"}
    assert "different or unread currency and scale" in outcomes[0].reason


def test_cp2d_two_currencies_are_not_compared():
    outcomes = ms.run("CP-2D", cp2d(units={"Mandatory capex": "EUR m"}))
    assert statuses(outcomes) == {ms.ENDING: "not checked", ms.MTE: "not checked"}
    assert "EUR m" in outcomes[0].reason


def test_cp2d_notation_variants_of_one_unit_agree():
    units = {"Cash interest": "US$ millions", "Cash taxes": "USD mn", ENDING: "USDm"}
    assert statuses(ms.run("CP-2D", cp2d(units=units))) == {ms.ENDING: "agreed", ms.MTE: "agreed"}


def test_cp2d_an_absent_register_is_not_checked():
    text = cp2d().replace("### T2E.5 — 12-Month Liquidity Bridge", "### Liquidity bridge")
    outcomes = ms.run("CP-2D", text)
    assert [o.reason for o in outcomes] == ["the handoff has no T2E.5 register"] * 2


def test_cp2d_the_register_is_found_by_its_tag_or_a_bold_id_but_not_inside_a_code_fence():
    heading = "### T2E.5 — 12-Month Liquidity Bridge"
    tagged = cp2d().replace(heading, "<!-- table-id: cp2d.T2E.5 -->")
    bold = cp2d().replace(heading, "#### **T2E.5** Liquidity bridge")
    for text in (tagged, bold):
        assert statuses(ms.run("CP-2D", text)) == {ms.ENDING: "agreed", ms.MTE: "agreed"}
    start = cp2d().index(heading)
    end = cp2d().index("### T2E.6")
    fenced = cp2d()[:start] + "```\n" + cp2d()[start:end] + "```\n" + cp2d()[end:]
    assert ms.run("CP-2D", fenced)[0].reason == "the handoff has no T2E.5 register"
    twice = cp2d().replace("### T2E.6", cp2d()[start:end] + "### T2E.6")
    assert ms.run("CP-2D", twice)[0].reason == "the handoff has 2 T2E.5 registers"


def test_cp2d_a_malformed_table_is_not_checked():
    text = cp2d().replace("| Cash taxes | 8 |", "| Cash taxes | 8 | 9 |")
    outcomes = ms.run("CP-2D", text)
    assert statuses(outcomes) == {ms.ENDING: "not checked", ms.MTE: "not checked"}
    assert "a row of 7 cells under 6 columns" in outcomes[0].reason


def test_cp2d_an_ambiguous_figure_is_refused_not_guessed():
    outcomes = ms.run("CP-2D", cp2d(BRIDGE | {"Cash taxes": "8,5"}))
    assert outcomes[0].status == "not checked" and "ambiguous" in outcomes[0].reason


def test_cp2d_a_cash_generative_bridge_has_no_runway():
    # Operating cash flow 285 instead of 85: net movement +100, the ending 500, burn below zero.
    rows = BRIDGE | {"Operating cash inflow/outflow": "285", ENDING: "500"}
    agreed = ms.run("CP-2D", cp2d(rows, months="Not Calculable"))
    assert statuses(agreed) == {ms.ENDING: "agreed", ms.MTE: "agreed"}
    wrong = ms.run("CP-2D", cp2d(rows, months="48.0"))
    assert wrong[1].status == "disagreed" and wrong[1].recomputed is None
    assert "recomputes Not Calculable" in ms.issue(wrong[1])


def test_cp2d_months_to_empty_on_another_burn_basis_is_not_checked():
    outcomes = ms.run("CP-2D", cp2d(months="20.0", basis="Q3 2025 operating burn, seasonal"))
    assert statuses(outcomes) == {ms.ENDING: "agreed", ms.MTE: "not checked"}
    assert "not the T2E.5 bridge" in outcomes[1].reason


def test_cp2d_a_row_outside_the_formula_does_not_make_a_disagreement():
    # A lease row the formula does not name: the stated ending 280 includes it, the formula's 300
    # does not, so the difference may be the row and is recorded, not sent back.
    rows = dict(BRIDGE)
    rows = {**{k: v for k, v in rows.items() if k != ENDING}, "Lease payment": "20", ENDING: "280"}
    outcomes = ms.run("CP-2D", cp2d(rows))
    assert outcomes[0].status == "not checked" and "`Lease payment`" in outcomes[0].reason
    # ... and agreement is still proved when the row does not change the ending.
    rows[ENDING] = "300"
    assert ms.run("CP-2D", cp2d(rows))[0].status == "agreed"


def test_cp2d_months_to_empty_within_one_displayed_unit_and_the_inputs_rounding():
    # 48 exactly. The bound is the stated place plus the inputs' rounding (1.98, worked above):
    # 48, 48.00 and 50.0 (out by 2.0, within 0.1 + 1.98) agree; 50.2 (out by 2.2) disagrees.
    for months in ("48 months", "48.00", "50.0"):
        assert ms.run("CP-2D", cp2d(months=months))[1].status == "agreed", months
    assert ms.run("CP-2D", cp2d(months="50.2"))[1].status == "disagreed"


# --- CP-3C --------------------------------------------------------------------------------------

# SYNTHETIC, EUR millions, horizon 2 years from the balance-sheet date.
# Maturities due: Term Loan A 300 (1.5y) + Senior Notes 450 (2.0y, at the horizon, inside) = 750;
# Term Loan B (5.0y) is beyond the horizon.
# Available liquidity: cash 220 + RCF undrawn 400 - 150 = 250 (committed, expires 3.0y, after the
# horizon) = 470; the bilateral line expires inside the horizon (1.0y) and the uncommitted line
# is not committed: neither counts.
# Funding gap: 750 - (470 + 80) = 200.
WALL = [
    ("Term Loan A", "300", "EUR", "m", "1.5"),
    ("Senior Notes 2027", "450", "EUR", "m", "2.0"),
    ("Term Loan B", "900", "EUR", "m", "5.0"),
]
FUNDING = [
    ("Horizon", "—", "—", "2", "—"),
    ("Cash", "220", "—", "—", "—"),
    ("Facility: RCF", "400", "150", "3.0", "Yes"),
    ("Facility: Bilateral line", "100", "0", "1.0", "Yes"),
    ("Facility: Uncommitted line", "50", "0", "4.0", "No"),
    ("Forecast free cash flow", "80", "—", "—", "—"),
    ("Maturities due", "750", "—", "—", "—"),
    ("Available liquidity", "470", "—", "—", "—"),
    ("Funding gap", "200", "—", "—", "—"),
]


def cp3c(wall=None, funding=None, heading="### Funding gap"):
    wall_rows = [
        f"| {name} | {amount} | {ccy} | {scale} | 2027-01-01 | {years} | Senior | 5% | Fixed | — "
        "| High | Synthetic. | S1 |"
        for name, amount, ccy, scale, years in (WALL if wall is None else wall)
    ]
    funding_rows = [
        f"| {line} | {amount} | {drawn} | {years} | {committed} | "
        f"{'—' if line == 'Horizon' else 'EUR'} | {'—' if line == 'Horizon' else 'm'} |"
        for line, amount, drawn, years, committed in (FUNDING if funding is None else funding)
    ]
    return "\n".join(
        [
            "## Request",
            "SYNTHETIC handoff.",
            "## Findings",
            "### Bottom line",
            "Refinancing risk is high.",
            "### T3D.2 — Maturity Wall and Refinancing Register",
            (
                "| Instrument | Amount | Currency | Scale | Maturity Date | Years to Maturity | "
                "Seniority / Lien | Coupon / Margin | Fixed / Floating | Call Date | "
                "Refinancing Pressure | Credit Implication | Source Trace |"
            ),
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
            *wall_rows,
            "",
            heading,
            "| Line | Amount | Drawn | Years | Committed | Currency | Scale |",
            "|---|---|---|---|---|---|---|",
            *funding_rows,
            "## Gaps",
            "None.",
        ]
    )


LINES = ("Maturities due", "Available liquidity", "Funding gap")


def replaced(rows, line, **cells):
    names = ("amount", "drawn", "years", "committed")
    return [
        (r[0], *(cells.get(n, r[i + 1]) for i, n in enumerate(names))) if r[0] == line else r
        for r in rows
    ]


def test_cp3c_all_figures_right():
    outcomes = ms.run("CP-3C", cp3c())
    assert statuses(outcomes) == dict.fromkeys(LINES, "agreed")
    assert [o.recomputed for o in outcomes] == [750.0, 470.0, 200.0]
    assert {o.unit for o in outcomes} == {"EUR m"}
    assert ms.issues("CP-3C", cp3c()) == ()


def test_cp3c_one_figure_wrong():
    text = cp3c(funding=replaced(FUNDING, "Funding gap", amount="180"))
    assert statuses(ms.run("CP-3C", text)) == {
        "Maturities due": "agreed",
        "Available liquidity": "agreed",
        "Funding gap": "disagreed",
    }
    (issue,) = ms.issues("CP-3C", text)
    assert (
        "`### Funding gap` row `Funding gap` states 180 EUR m" in issue
        and "recomputes 200 EUR m" in issue
    )
    assert "funding_gap.py" in issue


def test_cp3c_counting_an_expiring_facility_is_a_disagreement():
    # The model counted the bilateral line (expires at 1.0y, inside the 2y horizon): 570 and 100.
    funding = replaced(
        replaced(FUNDING, "Available liquidity", amount="570"), "Funding gap", amount="100"
    )
    outcomes = ms.run("CP-3C", cp3c(funding=funding))
    assert statuses(outcomes)["Available liquidity"] == "disagreed"
    assert "expiring inside the Horizon, adds nothing" in outcomes[1].reason


def test_cp3c_a_sign_error_in_drawn_is_a_disagreement():
    # Drawn -150: undrawn 400 + 150 = 550, liquidity 770, gap 750 - 850 < 0, so 0.
    outcomes = ms.run("CP-3C", cp3c(funding=replaced(FUNDING, "Facility: RCF", drawn="-150")))
    assert [o.status for o in outcomes] == ["agreed", "disagreed", "disagreed"]
    assert [o.recomputed for o in outcomes] == [750.0, 770.0, 0.0]


def test_cp3c_a_missing_input_is_not_checked():
    outcomes = ms.run(
        "CP-3C", cp3c(funding=replaced(FUNDING, "Cash", amount="Not supplied: no balance"))
    )
    assert statuses(outcomes) == {
        "Maturities due": "agreed",
        "Available liquidity": "not checked",
        "Funding gap": "not checked",
    }
    assert "no supported cash balance" in outcomes[1].reason
    wall = [
        w if w[0] != "Term Loan A" else (w[0], "Not supplied: undisclosed", *w[2:]) for w in WALL
    ]
    outcomes = ms.run("CP-3C", cp3c(wall=wall))
    assert (
        outcomes[0].status == "not checked" and "Not Calculable, not the sum" in outcomes[0].reason
    )


def test_cp3c_a_blank_forecast_is_not_zero_but_adds_nothing_to_the_gap():
    # Forecast free cash flow not supplied: the gap is 750 - 470 = 280 on liquidity alone; a
    # stated 0 gives the same arithmetic. Both are the method's own reading.
    for fcf in ("Not supplied: no forecast", "0"):
        funding = replaced(
            replaced(FUNDING, "Forecast free cash flow", amount=fcf), "Funding gap", amount="280"
        )
        assert statuses(ms.run("CP-3C", cp3c(funding=funding))) == dict.fromkeys(LINES, "agreed")


def test_cp3c_a_scale_mismatch_is_not_compared():
    wall = [w if w[0] != "Term Loan B" else (*w[:3], "bn", w[4]) for w in WALL]
    outcomes = ms.run("CP-3C", cp3c(wall=wall))
    assert statuses(outcomes) == dict.fromkeys(LINES, "not checked")
    assert "`Term Loan B` is in scale `bn`" in outcomes[0].reason


def test_cp3c_two_currencies_are_refused_by_the_script():
    wall = [w if w[0] != "Senior Notes 2027" else (w[0], w[1], "USD", *w[3:]) for w in WALL]
    outcomes = ms.run("CP-3C", cp3c(wall=wall))
    assert outcomes[0].status == "not checked" and "multiple currencies" in outcomes[0].reason
    assert outcomes[2].status == "not checked"
    assert outcomes[1].status == "agreed"  # liquidity is all in EUR


def test_cp3c_an_absent_register_is_not_checked():
    no_table = ms.run("CP-3C", cp3c(heading="### Refinancing need"))
    assert {o.reason for o in no_table} == {"the handoff has no `### Funding gap` table"}
    no_wall = cp3c().replace("### T3D.2 — Maturity Wall", "### Maturity Wall")
    assert {o.reason for o in ms.run("CP-3C", no_wall)} == {"the handoff has no T3D.2 register"}


def test_cp3c_a_deeper_heading_is_read():
    assert statuses(ms.run("CP-3C", cp3c(heading="#### Funding gap"))) == dict.fromkeys(
        LINES, "agreed"
    )


def test_cp3c_a_malformed_table_is_not_checked():
    text = cp3c().replace(
        "| Line | Amount | Drawn | Years | Committed | Currency | Scale |\n|---|",
        "| Line | Amount | Drawn | Years | Committed | Currency | Scale |\n|--|",
    )
    outcomes = ms.run("CP-3C", text)
    assert {o.status for o in outcomes} == {"not checked"}
    assert "no separator row" in outcomes[0].reason


def test_cp3c_a_row_the_check_does_not_read_is_not_compared():
    # `Facility - Term deposit` is not a `Facility: <name>` row: the script would not count it,
    # so a difference it makes is not the model's error.
    funding = [*FUNDING[:5], ("Facility - Term deposit", "30", "0", "3.0", "Yes"), *FUNDING[5:]]
    outcomes = ms.run("CP-3C", cp3c(funding=funding))
    assert {o.status for o in outcomes} == {"not checked"}
    assert "rows the check does not read" in outcomes[0].reason


def test_cp3c_committed_is_read_from_its_first_word_only():
    funding = replaced(FUNDING, "Facility: RCF", committed="Yes (committed revolver)")
    assert statuses(ms.run("CP-3C", cp3c(funding=funding))) == dict.fromkeys(LINES, "agreed")
    # `Committed` (neither Yes nor No) asserts nothing: the RCF is not counted, 220 and 530.
    funding = replaced(FUNDING, "Facility: RCF", committed="Committed")
    outcomes = ms.run("CP-3C", cp3c(funding=funding))
    assert [o.recomputed for o in outcomes] == [750.0, 220.0, 450.0]


def test_a_large_figure_is_written_in_full_in_the_issue():
    rows = BRIDGE | {"Beginning accessible liquidity": "4000400", ENDING: "4000400"}
    # 4,000,400 - 100 = 4,000,300 recomputed against 4,000,400 stated; Months to Empty
    # 4,000,400 / (100 / 12) = 480,048, stated right.
    (issue,) = ms.issues("CP-2D", cp2d(rows, months="480048"))
    assert "recomputes 4000300 USD m" in issue


def test_cp3c_the_gap_is_compared_within_its_inputs_rounding():
    # The gap sums the due notes (300, 450), the cash (220), the RCF (400 and 150) and the
    # forecast (80), each up to 0.5 off: 1 + 6 x 0.5 = 4. 204 agrees with 200; 205 does not.
    for amount, status in (("204", "agreed"), ("205", "disagreed")):
        outcome = ms.run("CP-3C", cp3c(funding=replaced(FUNDING, "Funding gap", amount=amount)))[2]
        assert (outcome.status, outcome.tolerance) == (status, 4.0), amount


def test_cp3c_no_horizon_is_refused_by_the_script():
    outcomes = ms.run("CP-3C", cp3c(funding=[r for r in FUNDING if r[0] != "Horizon"]))
    assert {o.status for o in outcomes} == {"not checked"}
    assert "horizon_years is required" in outcomes[0].reason


# --- CP-2E --------------------------------------------------------------------------------------

# SYNTHETIC, USD millions. Unhedged floating-rate debt = gross 800 - hedged 300 = 500; its share
# of total debt 500 / 2,000 = 0.25, written 25.0%; +100 bps cash-interest impact 500 x 1% = 5.0.
EXPOSURE = {
    "Total debt": "USD 2,000m",
    "Fixed-rate debt": "USD 1,200m",  # a row outside the formulas: read by nothing
    "Gross floating-rate debt": "USD 800m",
    "Hedged floating-rate debt": "USD 300m",
    "Unhedged floating-rate debt": "USD 500m",
    "Unhedged debt percentage": "25.0%",
}
SHOCK = ms.method_scripts_cp2e.SHOCK
CP2E_FIGURES = ("Unhedged floating-rate debt", "Unhedged debt percentage", SHOCK)


def cp2e(rows=None, impact="USD 5.0m", amount="Amount", sensitivities=None):
    rows = dict(EXPOSURE) if rows is None else rows
    sensitivities = sensitivities or {
        SHOCK: impact,
        "EUR/USD -10%": "USD 12.0m",  # FX: its inputs are free text, so it is not checked
    }
    return "\n".join(
        [
            "## Request",
            "SYNTHETIC handoff.",
            "## Findings",
            "### Bottom line",
            "Rate exposure is moderate.",
            "### T2F.4 — Unhedged Exposure Table",
            f"| Metric | {amount} | Formula / Source | Status | Credit Implication | Source |",
            "|---|---|---|---|---|---|",
            *(f"| {k} | {v} | T2F.2 | Calculated | Synthetic. | S1 |" for k, v in rows.items()),
            "",
            "### T2F.5 — Rate Sensitivity Table",
            (
                "| Sensitivity | Formula | Source Inputs | Estimated Cash Impact | "
                "FCF / Liquidity Implication | Status | Source Trace |"
            ),
            "|---|---|---|---|---|---|---|",
            *(
                f"| {k} | x | T2F.4 | {v} | Lower FCF. | Calculated | S1 |"
                for k, v in sensitivities.items()
            ),
            "## Gaps",
            "None.",
        ]
    )


def test_cp2e_all_figures_right():
    outcomes = ms.run("CP-2E", cp2e())
    assert statuses(outcomes) == dict.fromkeys(CP2E_FIGURES, "agreed")
    assert [o.recomputed for o in outcomes] == [500.0, 25.0, 5.0]
    assert [o.unit for o in outcomes] == ["USD m", "%", "USD m"]
    # One unit in the stated place plus the inputs' rounding (whole numbers, each up to 0.5 off):
    # unhedged 1 + 0.5 + 0.5 = 2.0; share 0.1 + 100 x (1.0 + 0.25 x 0.5) / 2,000 = 0.15625 points;
    # impact 0.1 + 1% x 1.0 = 0.11.
    assert [o.tolerance for o in outcomes] == pytest.approx([2.0, 0.15625, 0.11])
    assert ms.issues("CP-2E", cp2e()) == ()


def test_cp2e_one_figure_wrong():
    # Unhedged stated 550: the share and the shock are recomputed from gross and hedged, so agree.
    text = cp2e(EXPOSURE | {"Unhedged floating-rate debt": "USD 550m"})
    assert [o.status for o in ms.run("CP-2E", text)] == ["disagreed", "agreed", "agreed"]
    (issue,) = ms.issues("CP-2E", text)
    assert "T2F.4 row `Unhedged floating-rate debt` states 550 USD m" in issue
    assert "recomputes 500 USD m" in issue and "rate_fx_sensitivity.py" in issue
    assert "Gross floating-rate debt - Hedged floating-rate debt" in issue


def test_cp2e_a_sign_error_is_a_disagreement():
    # Unhedged debt is gross less hedged, 500; written (500) it is -500.
    outcomes = ms.run("CP-2E", cp2e(EXPOSURE | {"Unhedged floating-rate debt": "USD (500)m"}))
    assert [o.status for o in outcomes] == ["disagreed", "agreed", "agreed"]


def test_cp2e_the_impact_written_as_an_outflow_is_compared_as_a_magnitude():
    # Neither the method nor the note fixes the impact's sign: -5.0, (5.0) and a whole bracketed
    # cell all agree with 5.0, the stated sign kept; a wrong magnitude still disagrees.
    for impact in ("-USD 5.0m", "USD (5.0)m", "(USD 5.0m)"):
        outcome = ms.run("CP-2E", cp2e(impact=impact))[2]
        assert outcome.status == "agreed", impact
        assert "as an outflow (negative)" in outcome.reason and outcome.stated.startswith(
            ("-", "(")
        )
    assert ms.run("CP-2E", cp2e(impact="(USD 6.0m)"))[2].status == "disagreed"


def test_cp2e_an_unread_row_stops_only_the_checks_that_use_it():
    # Total debt with no unit: the share needs it; unhedged and the impact do not.
    outcomes = ms.run("CP-2E", cp2e(EXPOSURE | {"Total debt": "2,000"}))
    assert [o.status for o in outcomes] == ["agreed", "not checked", "agreed"]
    assert "states no currency and scale" in outcomes[1].reason


def test_cp2e_a_figure_wrong_by_more_than_the_rounding_bound_still_disagrees():
    # Unhedged: bound 2.0 (worked above); 502 agrees, 503 does not.
    rows = EXPOSURE | {"Unhedged floating-rate debt": "USD 502m"}
    assert ms.run("CP-2E", cp2e(rows))[0].status == "agreed"
    rows = EXPOSURE | {"Unhedged floating-rate debt": "USD 503m"}
    assert ms.run("CP-2E", cp2e(rows))[0].status == "disagreed"


def test_cp2e_a_wrong_share_and_its_unit():
    # 20.0% against 25.0%: out by more than 0.1 point. As a decimal (rule 8) 0.25 agrees; a bare 25
    # is above 1, so not the method's decimal share: not compared.
    share = "Unhedged debt percentage"
    assert ms.run("CP-2E", cp2e(EXPOSURE | {share: "20.0%"}))[1].status == "disagreed"
    assert ms.run("CP-2E", cp2e(EXPOSURE | {share: "0.25"}))[1].status == "agreed"
    bare = ms.run("CP-2E", cp2e(EXPOSURE | {share: "25"}))[1]
    assert bare.status == "not checked" and "no `%`" in bare.reason


def test_cp2e_a_missing_input_is_not_checked_and_never_zero():
    rows = {k: v for k, v in EXPOSURE.items() if k != "Hedged floating-rate debt"}
    outcomes = ms.run("CP-2E", cp2e(rows))
    assert statuses(outcomes) == dict.fromkeys(CP2E_FIGURES, "not checked")
    assert "no `Hedged floating-rate debt` row (absent, not zero)" in outcomes[0].reason
    # Total debt missing: the share is not checked, the other two still are.
    rows = {k: v for k, v in EXPOSURE.items() if k != "Total debt"}
    assert [o.status for o in ms.run("CP-2E", cp2e(rows))] == ["agreed", "not checked", "agreed"]


def test_cp2e_a_blank_is_missing_and_a_zero_is_a_figure():
    unknown = {"Hedged floating-rate debt": "[Insufficient Information]"}
    blank = ms.run("CP-2E", cp2e(EXPOSURE | unknown))
    assert statuses(blank) == dict.fromkeys(CP2E_FIGURES, "not checked")
    assert "states no amount for `Hedged floating-rate debt` (missing, not zero)" in blank[0].reason
    # Hedged 0: unhedged 800 - 0 = 800, share 800 / 2,000 = 40.0%, impact 800 x 1% = 8.0.
    rows = EXPOSURE | {
        "Hedged floating-rate debt": "USD 0m",
        "Unhedged floating-rate debt": "USD 800m",
        "Unhedged debt percentage": "40.0%",
    }
    zero = ms.run("CP-2E", cp2e(rows, impact="USD 8.0m"))
    assert statuses(zero) == dict.fromkeys(CP2E_FIGURES, "agreed")


def test_cp2e_fully_hedged_is_zero_unhedged_and_agreed():
    # Hedged 800 = gross 800: unhedged 0, share 0 / 2,000 = 0.0%, impact 0.
    rows = EXPOSURE | {
        "Hedged floating-rate debt": "USD 800m",
        "Unhedged floating-rate debt": "USD 0m",
        "Unhedged debt percentage": "0.0%",
    }
    outcomes = ms.run("CP-2E", cp2e(rows, impact="USD 0m"))
    assert statuses(outcomes) == dict.fromkeys(CP2E_FIGURES, "agreed")


def test_cp2e_hedged_above_gross_is_sent_back_as_a_contradiction():
    # Hedged 900 against gross 800: the perimeters differ or a hedge is double-counted. The script
    # refuses rather than report zero unhedged exposure. Owner, 2026-11-15 ("approved"): the pair
    # is sent back as a contradiction, nothing recomputed; the three figures are not checked.
    rows = EXPOSURE | {
        "Hedged floating-rate debt": "USD 900m",
        "Unhedged floating-rate debt": "USD 0m",
        "Unhedged debt percentage": "0.0%",
    }
    outcomes = ms.run("CP-2E", cp2e(rows, impact="USD 0m"))
    pair = f"{ms.method_scripts_cp2e.HEDGED} against {ms.method_scripts_cp2e.GROSS}"
    assert statuses(outcomes) == {pair: "contradicted"} | dict.fromkeys(CP2E_FIGURES, "not checked")
    assert (
        outcomes[0].recomputed is None and "exceeds gross floating-rate debt" in outcomes[0].reason
    )
    (issue,) = ms.issues("CP-2E", cp2e(rows, impact="USD 0m"))
    assert "Hedged floating-rate debt `USD 900m` above Gross floating-rate debt `USD 800m`" in issue
    assert "perimeters differ or a hedge is double-counted" in issue and "recomputes" not in issue


def test_cp2e_other_refusals_of_the_script_stay_not_checked():
    # A negative gross: the script refuses, but no two rows contradict each other.
    outcomes = ms.run("CP-2E", cp2e(EXPOSURE | {"Gross floating-rate debt": "USD (800)m"}))
    assert {o.status for o in outcomes} == {"not checked"}
    assert "is negative" in outcomes[0].reason
    assert ms.issues("CP-2E", cp2e(EXPOSURE | {"Gross floating-rate debt": "USD (800)m"})) == ()


def test_cp2e_a_scale_mismatch_is_not_compared():
    outcomes = ms.run("CP-2E", cp2e(EXPOSURE | {"Total debt": "USD 2.0bn"}))
    assert statuses(outcomes) == dict.fromkeys(CP2E_FIGURES, "not checked")
    assert "different currencies or scales" in outcomes[0].reason
    shock = ms.run("CP-2E", cp2e(impact="USD 0.005bn"))
    assert [o.status for o in shock] == ["agreed", "agreed", "not checked"]
    assert "`USD bn`, T2F.4's amounts in `USD m`" in shock[2].reason


def test_cp2e_two_currencies_are_not_compared():
    outcomes = ms.run("CP-2E", cp2e(EXPOSURE | {"Hedged floating-rate debt": "EUR 300m"}))
    assert statuses(outcomes) == dict.fromkeys(CP2E_FIGURES, "not checked")
    assert "EUR 300m" in outcomes[0].reason


def test_cp2e_the_unit_may_head_the_column_and_a_cell_without_one_is_unread():
    bare = {k: v.removeprefix("USD ").removesuffix("m") for k, v in EXPOSURE.items()}
    headed = ms.run("CP-2E", cp2e(bare, amount="Amount (USD m)"))
    assert statuses(headed) == dict.fromkeys(CP2E_FIGURES, "agreed")
    unread = ms.run("CP-2E", cp2e(bare))
    assert statuses(unread) == dict.fromkeys(CP2E_FIGURES, "not checked")
    assert "states no currency and scale, nor does its column" in unread[0].reason


def test_cp2e_an_absent_register_is_not_checked():
    no_exposure = cp2e().replace("### T2F.4 — Unhedged Exposure Table", "### Unhedged exposure")
    reasons = {o.reason for o in ms.run("CP-2E", no_exposure)}
    assert reasons == {"the handoff has no T2F.4 register"}
    no_shock = cp2e().replace("### T2F.5 — Rate Sensitivity Table", "### Rate sensitivity")
    outcomes = ms.run("CP-2E", no_shock)
    assert [o.status for o in outcomes] == ["agreed", "agreed", "not checked"]
    assert outcomes[2].reason == "the handoff has no T2F.5 register"


def test_cp2e_a_malformed_table_is_not_checked():
    text = cp2e().replace("| Total debt | USD 2,000m |", "| Total debt | USD 2,000m | extra |")
    outcomes = ms.run("CP-2E", text)
    assert statuses(outcomes) == dict.fromkeys(CP2E_FIGURES, "not checked")
    assert "a row of 7 cells under 6 columns" in outcomes[0].reason


def test_cp2e_a_repeated_or_unnamed_shock_row_is_not_checked():
    twice = {SHOCK: "USD 5.0m", "+100 bps Cash-Interest Impact": "USD 8.0m"}
    outcome = ms.run("CP-2E", cp2e(sensitivities=twice))[2]
    assert outcome.status == "not checked" and "has 2 `+100 bps cash-interest impact` rows" in (
        outcome.reason
    )
    other = ms.run("CP-2E", cp2e(sensitivities={"+100 bps on gross debt": "USD 8.0m"}))[2]
    assert other.status == "not checked" and "has no `+100 bps" in other.reason


def test_cp2e_a_repeated_input_row_is_not_checked():
    text = cp2e().replace(
        "| Total debt |", "| Hedged floating-rate debt | USD 100m | x | x | x | x |\n| Total debt |"
    )
    outcomes = ms.run("CP-2E", text)
    assert statuses(outcomes) == dict.fromkeys(CP2E_FIGURES, "not checked")
    assert "two `Hedged floating-rate debt` rows" in outcomes[0].reason


# --- CP-3 (the table is proposed to the owner; CP-3 is not asked for it) ------------------------

# SYNTHETIC, USD millions. Claims in row order RCF 50, Term Loan B 300, Senior Notes 200; admin
# cost 20 comes off the top of each enterprise value.
# Low, EV 200: 180 left. RCF 50 of 50 (100%); 130 left, Term Loan B 130 of 300 = 43.33% (the first
# partial: the fulcrum); Senior Notes 0%. Residual 0.
# Base, EV 420: 400 left. RCF 100%; Term Loan B 300 of 300 (100%); 50 left, Senior Notes 50 of
# 200 = 25.0% (fulcrum). Residual 0.
# High, EV 700: 680 left. All three whole (100%); 680 - 550 = 130 to equity; no fulcrum.
WATERFALL = [
    ("Enterprise value", "—", "200", "420", "700", "USD", "m"),
    ("Cost: Administrative claims", "20", "—", "—", "—", "USD", "m"),
    ("Claim: RCF", "50", "100%", "100%", "100%", "USD", "m"),
    ("Claim: Term Loan B", "300", "43.3%", "100%", "100%", "USD", "m"),
    ("Claim: Senior Notes", "200", "0%", "25.0%", "100%", "USD", "m"),
    ("Fulcrum", "—", "Term Loan B", "Senior Notes", "None", "—", "—"),
    ("Residual to equity", "—", "0", "0", "130", "USD", "m"),
]
CP3_CLAIMS = ("RCF", "Term Loan B", "Senior Notes")


def cp3(rows=None, heading="### Recovery waterfall"):
    rows = WATERFALL if rows is None else rows
    return "\n".join(
        [
            "## Request",
            "SYNTHETIC handoff.",
            "## Findings",
            "### Bottom line",
            "Senior Notes are the fulcrum in the base case.",
            heading,
            "| Line | Amount | Low | Base | High | Currency | Scale |",
            "|---|---|---|---|---|---|---|",
            *("| " + " | ".join(row) + " |" for row in rows),
            "## Gaps",
            "None.",
        ]
    )


def edited(line, **cells):
    names = ("amount", "low", "base", "high", "currency", "scale")
    return [
        (r[0], *(cells.get(n, r[i + 1]) for i, n in enumerate(names))) if r[0] == line else r
        for r in WATERFALL
    ]


def by_case(outcomes, case):
    return {
        o.figure.removesuffix(f" ({case})"): o for o in outcomes if o.figure.endswith(case + ")")
    }


def test_cp3_all_figures_right():
    outcomes = ms.run("CP-3", cp3())
    assert len(outcomes) == 15 and {o.status for o in outcomes} == {"agreed"}
    low = by_case(outcomes, "Low")
    assert low["Recovery: Term Loan B"].recomputed == pytest.approx(43.333333, abs=1e-4)
    # 0.1, plus the rounding bound: the value left for the loan (EV 200, cost 20, RCF 50, each
    # +-0.5, so +-1.5) over its claim 300 (+-0.5): 100 x (1.5 + 0.4333 x 0.5) / 300 = 0.572.
    assert low["Recovery: Term Loan B"].tolerance == pytest.approx(
        0.1 + 100 * (1.5 + 130 / 300 * 0.5) / 300
    )
    assert low["Fulcrum"].recomputed_label == "Term Loan B"
    high = by_case(outcomes, "High")
    assert high["Residual to equity"].recomputed == 130.0
    assert high["Fulcrum"].recomputed_label == "no fulcrum"
    assert ms.issues("CP-3", cp3()) == ()


def test_cp3_is_not_asked_for_the_table():
    assert "CP-3" in ms.CHECKS and "CP-3" not in ms.NOTES


def test_cp3_one_recovery_wrong():
    text = cp3(edited("Claim: Senior Notes", base="30.0%"))
    wrong = [o for o in ms.run("CP-3", text) if o.status == "disagreed"]
    assert [o.figure for o in wrong] == ["Recovery: Senior Notes (Base)"]
    (issue,) = ms.issues("CP-3", text)
    assert "`### Recovery waterfall` row `Recovery: Senior Notes (Base)` states 30.0 %" in issue
    assert "recomputes 25 %" in issue and "recovery_waterfall.py" in issue


def test_cp3_a_wrong_fulcrum_names_the_scripts_fulcrum():
    rows = edited("Fulcrum", base="Term Loan B")
    (issue,) = ms.issues("CP-3", cp3(rows))
    assert "row `Fulcrum (Base)` states Term Loan B" in issue
    assert "recomputes Senior Notes from the handoff's own rows" in issue


def test_cp3_a_fulcrum_named_with_a_note_is_its_claim():
    rows = edited("Fulcrum", base="Senior Notes (partial)")
    assert by_case(ms.run("CP-3", cp3(rows)), "Base")["Fulcrum"].status == "agreed"


def test_cp3_unallocated_value_is_a_disagreement():
    # High: 130 reaches equity. Stating 0 leaves it unallocated.
    outcome = by_case(ms.run("CP-3", cp3(edited("Residual to equity", high="0"))), "High")
    assert outcome["Residual to equity"].status == "disagreed"
    assert "not left unallocated" in outcome["Residual to equity"].reason


def test_cp3_a_sign_error_is_a_disagreement():
    outcome = by_case(ms.run("CP-3", cp3(edited("Residual to equity", high="(130)"))), "High")
    assert outcome["Residual to equity"].status == "disagreed"


def test_cp3_a_claim_guaranteed_at_two_entities_is_refused_by_the_script():
    # The notes listed once per guarantor entity would recover twice: the script refuses.
    rows = [
        *WATERFALL[:5],
        ("Claim: Senior Notes", "200", "0%", "0%", "0%", "USD", "m"),
        *WATERFALL[5:],
    ]
    (outcome,) = ms.run("CP-3", cp3(rows))
    assert outcome.status == "not checked" and "double-counts recovery" in outcome.reason


def test_cp3_a_missing_enterprise_value_is_not_checked_and_never_zero():
    outcomes = ms.run("CP-3", cp3(edited("Enterprise value", base="Not supplied: no valuation")))
    base = by_case(outcomes, "Base")
    assert {o.status for o in base.values()} == {"not checked"}
    assert "states no Enterprise value for Base (missing, not zero)" in base["Fulcrum"].reason
    assert {o.status for o in by_case(outcomes, "Low").values()} == {"agreed"}


def test_cp3_a_claim_without_an_amount_stops_the_claims_below_it():
    outcomes = by_case(
        ms.run("CP-3", cp3(edited("Claim: Term Loan B", amount="[Insufficient Information]"))),
        "Base",
    )
    assert outcomes["Recovery: RCF"].status == "agreed"
    for name in (
        "Recovery: Term Loan B",
        "Recovery: Senior Notes",
        "Fulcrum",
        "Residual to equity",
    ):
        assert outcomes[name].status == "not checked", name
    assert "not established" in outcomes["Fulcrum"].reason


def test_cp3_a_blank_cost_stops_the_case_and_a_zero_cost_is_a_figure():
    blank = ms.run(
        "CP-3", cp3(edited("Cost: Administrative claims", amount="Not supplied: none disclosed"))
    )
    assert {o.status for o in blank} == {"not checked"}
    assert "has no supported amount" in blank[0].reason
    # Cost 0: Base has 420; RCF 50, Term Loan B 300, 70 left, Senior Notes 70 / 200 = 35.0%.
    zero = by_case(ms.run("CP-3", cp3(edited("Cost: Administrative claims", amount="0"))), "Base")
    assert zero["Recovery: Senior Notes"].recomputed == pytest.approx(35.0)


def test_cp3_a_scale_mismatch_or_two_currencies_are_not_compared():
    for cells in ({"scale": "bn"}, {"currency": "EUR"}):
        (outcome,) = ms.run("CP-3", cp3(edited("Claim: RCF", **cells)))
        assert (
            outcome.status == "not checked" and "different or unread currencies" in outcome.reason
        )


def test_cp3_an_absent_or_malformed_table_is_not_checked():
    (absent,) = ms.run("CP-3", cp3(heading="### Recovery analysis"))
    assert absent.reason == "the handoff has no `### Recovery waterfall` table"
    broken = cp3().replace("| Claim: RCF | 50 |", "| Claim: RCF | 50 | 9 |")
    (outcome,) = ms.run("CP-3", broken)
    assert "a row of 8 cells under 7 columns" in outcome.reason


def test_cp3_a_row_the_check_does_not_read_is_not_compared():
    rows = [*WATERFALL[:2], ("Tax leakage", "5", "—", "—", "—", "USD", "m"), *WATERFALL[2:]]
    (outcome,) = ms.run("CP-3", cp3(rows))
    assert outcome.status == "not checked" and "`Tax leakage`" in outcome.reason


# --- CP-2G --------------------------------------------------------------------------------------

# SYNTHETIC, USD millions, annual. (period, case): T2H.4 EBITDA, FCF; T2H.5 opening debt / cash,
# issuance, repayment, interest, closing debt / cash; T2H.6 gross / net leverage, coverage and
# FCF/debt.
# Base FY2025: closing debt 5,000 + 0 - 200 = 4,800. Gross 4,800 / 1,000 = 4.8x; net
#   (4,800 - 500) / 1,000 = 4.3x; coverage 1,000 / 350 = 2.857 (2.9x); FCF/debt 300 / 4,800 = 6.25%.
# Base FY2026: opens at FY2025's close 4,800 / 500; closing 4,800 + 100 - 300 = 4,600. Gross
#   4,600 / 1,100 = 4.18 (4.2x); net 3,950 / 1,100 = 3.59 (3.6x); coverage 1,100 / 330 = 3.33
#   (3.3x); FCF/debt 350 / 4,600 = 7.61% (7.6%).
# Downside FY2025: closing 4,800. Gross 4,800 / 800 = 6.0x; net 4,450 / 800 = 5.5625 (5.6x);
#   coverage 800 / 360 = 2.22 (2.2x); FCF/debt 150 / 4,800 = 3.125% (3.1%).
# Downside FY2026: EBITDA -50, so no leverage multiple (n.m.); coverage -50 / 380 = -0.13
#   ((0.1x)); FCF/debt -200 / 4,800 = -4.17% ((4.2%)); closing 4,800 + 0 - 0 = 4,800.
MODEL = {
    ("FY2025", "Base"): ("1,000", "300", "5,000 / 400", "0", "200", "350", "4,800 / 500"),
    ("FY2026", "Base"): ("1,100", "350", "4,800 / 500", "100", "300", "330", "4,600 / 650"),
    ("FY2025", "Downside"): ("800", "150", "5,000 / 400", "0", "200", "360", "4,800 / 350"),
    ("FY2026", "Downside"): ("(50)", "(200)", "4,800 / 350", "0", "0", "380", "4,800 / 150"),
}
METRICS = {
    ("FY2025", "Base"): ("4.8x / 4.3x", "2.9x", "6.25%"),
    ("FY2026", "Base"): ("4.2x / 3.6x", "3.3x", "7.6%"),
    ("FY2025", "Downside"): ("6.0x / 5.6x", "2.2x", "3.1%"),
    ("FY2026", "Downside"): ("n.m. / n.m.", "(0.1x)", "(4.2%)"),
}
DEFINITION = "D1 debt / EBITDA; D2 EBITDA / cash interest; D3 FCF / debt"


def cp2g(model=None, metrics=None, unit="USD m", t2h5_unit=None, definition=DEFINITION):
    model = MODEL if model is None else model
    metrics = METRICS if metrics is None else metrics
    five = t2h5_unit or unit
    return "\n".join(
        [
            "## Findings",
            "### Bottom line",
            "Leverage falls in the base case.",
            "### T2H.4 — Operating forecast outputs",
            (
                f"| period | case | revenue | EBITDA ({unit}) | margin | CFO | capex | "
                f"FCF ({unit}) | evidence/assumption IDs |"
            ),
            "|---|---|---|---|---|---|---|---|---|",
            *(
                f"| {p} | {c} | — | {v[0]} | — | — | — | {v[1]} | A1 |"
                for (p, c), v in model.items()
            ),
            "",
            "### T2H.5 — Financing and liquidity outputs",
            (
                f"| period | case | opening debt/cash ({five}) | issuance ({five}) | "
                f"repayment ({five}) | interest ({five}) | closing debt/cash ({five}) | "
                "accessible liquidity |"
            ),
            "|---|---|---|---|---|---|---|---|",
            *(f"| {p} | {c} | {' | '.join(v[2:])} | — |" for (p, c), v in model.items()),
            "",
            "### T2H.6 — Credit metrics outputs",
            (
                "| period | case | gross/net leverage | coverage | FCF/debt | liquidity runway "
                "| definition IDs |"
            ),
            "|---|---|---|---|---|---|---|",
            *(
                f"| {p} | {c} | {' | '.join(v)} | — | {definition} |"
                for (p, c), v in metrics.items()
            ),
            "## Gaps",
            "None.",
        ]
    )


def cp2g_status(outcomes):
    return {o.figure: o.status for o in outcomes}


def test_cp2g_all_figures_right():
    outcomes = ms.run("CP-2G", cp2g())
    status = cp2g_status(outcomes)
    assert len(outcomes) == 16 + 12
    kpis = [f for f in status if not f.startswith(("Opening", "Closing"))]
    assert {status[f] for f in kpis} == {"agreed"}
    assert status["Gross leverage (FY2026, Downside)"] == "agreed"  # n.m. against EBITDA -50
    for case in ("Base", "Downside"):
        assert status[f"Opening debt (FY2026, {case})"] == "agreed"
        assert status[f"Opening cash (FY2026, {case})"] == "agreed"
        assert status[f"Opening debt (FY2025, {case})"] == "not checked"  # no earlier period
        assert status[f"Closing debt (FY2025, {case})"] == "agreed"
    by = {o.figure: o for o in outcomes}
    assert by["Net leverage (FY2026, Base)"].recomputed == pytest.approx(3950 / 1100)
    # 0.1, plus the quotient's bound: net debt 3,950 (+-0.5 +-0.5) over EBITDA 1,100 (+-0.5):
    # (1.0 + 3.591 x 0.5) / 1,100 = 0.00254.
    assert by["Net leverage (FY2026, Base)"].tolerance == pytest.approx(
        0.1 + (1.0 + 3950 / 1100 * 0.5) / 1100
    )
    assert by["FCF/debt (FY2025, Base)"].recomputed == pytest.approx(6.25)
    assert ms.issues("CP-2G", cp2g()) == ()


def test_cp2g_one_figure_wrong():
    text = cp2g(metrics=METRICS | {("FY2026", "Base"): ("4.5x / 3.6x", "3.3x", "7.6%")})
    (issue,) = ms.issues("CP-2G", text)
    assert "T2H.6 row `Gross leverage (FY2026, Base)` states 4.5 x" in issue
    assert "recomputes 4.181818" in issue and "credit_metrics.py" in issue


def test_cp2g_a_sign_error_is_a_disagreement():
    text = cp2g(metrics=METRICS | {("FY2025", "Base"): ("4.8x / (4.3x)", "2.9x", "6.25%")})
    assert cp2g_status(ms.run("CP-2G", text))["Net leverage (FY2025, Base)"] == "disagreed"


def test_cp2g_an_opening_balance_that_is_not_the_prior_close_is_a_disagreement():
    model = MODEL | {
        ("FY2026", "Base"): ("1,100", "350", "4,900 / 500", "100", "300", "330", "4,700 / 650")
    }
    # Opening 4,900 against FY2025's close of 4,800; the year itself rolls (4,900 + 100 - 300).
    metrics = METRICS | {("FY2026", "Base"): ("4.3x / 3.7x", "3.3x", "7.4%")}
    outcomes = {o.figure: o for o in ms.run("CP-2G", cp2g(model, metrics))}
    opening = outcomes["Opening debt (FY2026, Base)"]
    assert (opening.status, opening.stated, opening.recomputed) == ("disagreed", "4,900", 4800.0)
    assert outcomes["Closing debt (FY2026, Base)"].status == "agreed"
    (issue,) = ms.issues("CP-2G", cp2g(model, metrics))
    assert "prior closing" in issue.lower() or "closing debt in the period before" in issue


def test_cp2g_an_opening_is_compared_only_with_the_year_before_it():
    # FY2026 listed before FY2025: the row before FY2025 is FY2026, not its prior year.
    order = [("FY2026", "Base"), ("FY2025", "Base")]
    model = {k: MODEL[k] for k in order}
    status = cp2g_status(ms.run("CP-2G", cp2g(model, {k: METRICS[k] for k in order})))
    assert status["Opening debt (FY2025, Base)"] == "not checked"
    assert status["Opening debt (FY2026, Base)"] == "not checked"  # first row of its case


def test_cp2g_a_closing_residual_is_recorded_not_sent_back():
    # Closing 4,850 against 5,000 + 0 - 200 = 4,800: a residual of 50 the method may have logged.
    model = MODEL | {
        ("FY2025", "Base"): ("1,000", "300", "5,000 / 400", "0", "200", "350", "4,850 / 500")
    }
    metrics = METRICS | {("FY2025", "Base"): ("4.85x / 4.35x", "2.9x", "6.2%")}
    outcomes = {o.figure: o for o in ms.run("CP-2G", cp2g(model, metrics))}
    closing = outcomes["Closing debt (FY2025, Base)"]
    assert closing.status == "not checked" and "a residual of 50" in closing.reason
    # FY2026 opens at 4,800, not the 4,850 the model closed FY2025 at: that is a disagreement.
    assert outcomes["Opening debt (FY2026, Base)"].status == "disagreed"


def test_cp2g_a_missing_input_is_not_checked_and_never_zero():
    model = MODEL | {
        ("FY2026", "Base"): ("Not supplied: no guidance", "350", *MODEL[("FY2026", "Base")][2:])
    }
    status = cp2g_status(ms.run("CP-2G", cp2g(model)))
    for name in ("Gross leverage", "Net leverage", "Coverage"):
        assert status[f"{name} (FY2026, Base)"] == "not checked"
    assert status["FCF/debt (FY2026, Base)"] == "agreed"
    reason = {o.figure: o.reason for o in ms.run("CP-2G", cp2g(model))}["Coverage (FY2026, Base)"]
    assert "states no ebitda for FY2026, Base (missing, not zero)" in reason


def test_cp2g_a_blank_issuance_is_missing_and_a_zero_is_a_figure():
    model = MODEL | {
        ("FY2025", "Base"): (
            "1,000",
            "300",
            "5,000 / 400",
            "Not supplied: undisclosed",
            "200",
            "350",
            "4,800 / 500",
        )
    }
    assert cp2g_status(ms.run("CP-2G", cp2g(model)))["Closing debt (FY2025, Base)"] == "not checked"
    assert cp2g_status(ms.run("CP-2G", cp2g()))["Closing debt (FY2025, Base)"] == "agreed"  # 0


def test_cp2g_a_unit_mismatch_or_two_currencies_are_not_compared():
    for t2h5 in ("USD bn", "EUR m"):
        (outcome,) = ms.run("CP-2G", cp2g(t2h5_unit=t2h5))
        assert outcome.status == "not checked" and "different units" in outcome.reason
    unread = ms.run("CP-2G", cp2g(unit="m"))  # a scale with no currency: no figure is read
    assert {o.status for o in unread} == {"not checked"}
    assert "states no currency and scale, nor does its column" in unread[0].reason


def test_cp2g_an_absent_register_is_not_checked():
    no_metrics = cp2g().replace("### T2H.6 — Credit metrics outputs", "### Credit metrics")
    outcomes = ms.run("CP-2G", no_metrics)
    assert outcomes[0].reason == "the handoff has no T2H.6 register"
    assert "agreed" in {o.status for o in outcomes}  # the roll-forward still runs
    no_ops = cp2g().replace("### T2H.4 — Operating forecast outputs", "### Operating forecast")
    (outcome,) = ms.run("CP-2G", no_ops)
    assert outcome.reason == "the handoff has no T2H.4 register"


def test_cp2g_a_malformed_table_is_not_checked():
    text = cp2g().replace("| FY2025 | Base | 4.8x / 4.3x |", "| FY2025 | Base | 4.8x | 4.3x |")
    outcome = ms.run("CP-2G", text)[0]  # T2H.6 is unread; T2H.5's roll-forward still runs
    assert outcome.status == "not checked" and "a row of 8 cells under 7 columns" in outcome.reason


def test_cp2g_a_combined_cell_needs_both_figures_in_its_columns_order():
    one = cp2g(metrics=METRICS | {("FY2025", "Base"): ("4.8x", "2.9x", "6.25%")})
    status = cp2g_status(ms.run("CP-2G", one))
    assert (
        status["Gross leverage (FY2025, Base)"]
        == status["Net leverage (FY2025, Base)"]
        == "not checked"
    )
    half = cp2g(metrics=METRICS | {("FY2025", "Base"): ("4.8x / n/a", "2.9x", "6.25%")})
    status = cp2g_status(ms.run("CP-2G", half))
    assert status["Gross leverage (FY2025, Base)"] == "agreed"
    assert status["Net leverage (FY2025, Base)"] == "not checked"
    swapped = cp2g(metrics=METRICS | {("FY2025", "Base"): ("4.3x / 4.8x", "2.9x", "6.25%")})
    status = cp2g_status(ms.run("CP-2G", swapped))
    assert (
        status["Gross leverage (FY2025, Base)"]
        == status["Net leverage (FY2025, Base)"]
        == "disagreed"
    )


def test_cp2g_coverage_on_another_definition_is_compared_only_when_named_ebitda_over_interest():
    # 2.4x is not 1,000 / 350 = 2.857. Under a fixed-charge definition it is not compared; under
    # the row's own `EBITDA / cash interest` definition it is a disagreement.
    metrics = METRICS | {("FY2025", "Base"): ("4.8x / 4.3x", "2.4x", "6.25%")}
    other = cp2g_status(ms.run("CP-2G", cp2g(metrics=metrics, definition="D2 fixed-charge cover")))
    assert other["Coverage (FY2025, Base)"] == "not checked"
    named = cp2g_status(ms.run("CP-2G", cp2g(metrics=metrics)))
    assert named["Coverage (FY2025, Base)"] == "disagreed"


def test_cp2g_a_leverage_multiple_on_negative_ebitda_is_not_calculable():
    metrics = METRICS | {("FY2026", "Downside"): ("(96.0x) / (93.0x)", "(0.1x)", "(4.2%)")}
    outcomes = {o.figure: o for o in ms.run("CP-2G", cp2g(metrics=metrics))}
    gross = outcomes["Gross leverage (FY2026, Downside)"]
    assert gross.status == "disagreed" and gross.recomputed_label == "Not Calculable"
    assert "recomputes Not Calculable" in ms.issue(gross)


def test_cp2g_a_null_word_with_its_explanation_is_a_null_word():
    # Review case: EBITDA (10); "Not meaningful (negative EBITDA)" agrees with Not Calculable.
    model = MODEL | {
        ("FY2026", "Downside"): ("(10)", "(200)", "4,800 / 350", "0", "0", "380", "4,800 / 150")
    }
    cells = ("Not meaningful (negative EBITDA) / n.m.", "(0.0x)", "(4.2%)")
    status = cp2g_status(ms.run("CP-2G", cp2g(model, METRICS | {("FY2026", "Downside"): cells})))
    assert status["Gross leverage (FY2026, Downside)"] == "agreed"
    assert status["Net leverage (FY2026, Downside)"] == "agreed"


def test_cp2g_leverage_on_another_named_basis_is_not_compared():
    # 5.0x is not 4,800 / 1,000 = 4.8x. Under `covenant EBITDA` it is not compared; under the
    # fixture's own definition it is a disagreement. Opaque ids cannot be recognised (ruling).
    metrics = METRICS | {("FY2025", "Base"): ("5.0x / 4.3x", "2.9x", "6.25%")}
    other = cp2g_status(ms.run("CP-2G", cp2g(metrics=metrics, definition="D4 covenant EBITDA")))
    assert other["Gross leverage (FY2025, Base)"] == "not checked"
    assert cp2g_status(ms.run("CP-2G", cp2g(metrics=metrics)))["Gross leverage (FY2025, Base)"] == (
        "disagreed"
    )


def test_cp2g_an_unread_t2h6_column_leaves_the_roll_forward_checked():
    text = cp2g().replace("| FCF/debt |", "| FCF to debt |")
    outcomes = ms.run("CP-2G", text)
    assert outcomes[0].figure == "T2H.6" and "no `FCF/debt` column" in outcomes[0].reason
    assert {o.status for o in outcomes[1:]} >= {"agreed"}


def test_cp2g_leverage_on_a_quarter_is_not_compared():
    model = {("Q1 2025", "Base"): MODEL[("FY2025", "Base")]}
    metrics = {("Q1 2025", "Base"): METRICS[("FY2025", "Base")]}
    status = cp2g_status(ms.run("CP-2G", cp2g(model, metrics)))
    assert status["Gross leverage (Q1 2025, Base)"] == "not checked"
    assert status["FCF/debt (Q1 2025, Base)"] == "not checked"
    assert status["Coverage (Q1 2025, Base)"] == "agreed"


# --- CP-4 ---------------------------------------------------------------------------------------

# SYNTHETIC. Headroom by the method's two formulas (REF_CP-4A_04):
# Net leverage, max-ratio: 5.00 - 4.20 = 0.80x, Compliant.
# Interest cover, min-ratio: 2.50 - 2.00 = 0.50x, Compliant.
# Senior secured leverage, max-ratio: 3.50 - 3.50 = 0.00x, At threshold.
# Minimum liquidity, min-ratio, USD m: 80 - 100 = -20, Breached.
COVENANTS = {
    "Net leverage": ("max-ratio", "5.00x", "4.20x", "0.80x", "Compliant"),
    "Interest cover": ("min-ratio", "2.00x", "2.50x", "0.50x", "Compliant"),
    "Senior secured leverage": ("max-ratio", "3.50x", "3.50x", "0.00x", "At threshold"),
    "Minimum liquidity": ("min-ratio", "USD 100m", "USD 80m", "USD (20)m", "Breached"),
}


def cp4(rows=None):
    rows = COVENANTS if rows is None else rows
    return "\n".join(
        [
            "## Findings",
            "### Bottom line",
            "One covenant is breached.",
            "### T4C.4 — Headroom Table",
            (
                "| Test | Test Type | Threshold | Current Basis | Formula | Headroom | Status | "
                "Limitation | Risk Mechanic | Credit Implication | Evidence ID |"
            ),
            "|---|---|---|---|---|---|---|---|---|---|---|",
            *(
                f"| {t} | {v[0]} | {v[1]} | {v[2]} | x | {v[3]} | {v[4]} | — | x | x | E1 |"
                for t, v in rows.items()
            ),
            "## Gaps",
            "None.",
        ]
    )


def covenant(name, **cells):
    names = ("type", "threshold", "current", "headroom", "status")
    row = COVENANTS[name]
    return COVENANTS | {name: tuple(cells.get(n, row[i]) for i, n in enumerate(names))}


def test_cp4_all_figures_right():
    outcomes = ms.run("CP-4", cp4())
    assert len(outcomes) == 8 and {o.status for o in outcomes} == {"agreed"}
    by = {o.figure: o for o in outcomes}
    assert by["Headroom: Net leverage"].recomputed == pytest.approx(0.8)
    # 0.01, plus the inputs' rounding: 5.00 and 4.20, each up to 0.005 off, so 0.02 in all.
    assert by["Headroom: Net leverage"].tolerance == pytest.approx(0.02)
    assert by["Headroom: Minimum liquidity"].unit == "USD m"
    assert by["Status: Minimum liquidity"].recomputed_label == "Breached"
    assert ms.issues("CP-4", cp4()) == ()


def test_cp4_one_figure_wrong():
    (issue,) = ms.issues("CP-4", cp4(covenant("Net leverage", headroom="0.70x")))
    assert "T4C.4 row `Headroom: Net leverage` states 0.70 x" in issue
    assert "recomputes 0.8 x" in issue and "covenant_headroom.py" in issue


def test_cp4_the_max_ratio_formula_on_a_min_ratio_test_is_a_sign_error():
    # Interest cover is a floor: 2.50 - 2.00 = +0.50. Threshold - current (-0.50) is the ceiling's
    # formula, and its "Breached" reads a cushion as a breach.
    rows = covenant("Interest cover", headroom="(0.50x)", status="Breached")
    by = {o.figure: o for o in ms.run("CP-4", cp4(rows))}
    assert by["Headroom: Interest cover"].status == "disagreed"
    assert by["Status: Interest cover"].status == "disagreed"
    assert by["Status: Interest cover"].recomputed_label == "Compliant"


def test_cp4_headroom_from_unrounded_inputs_agrees_within_their_rounding():
    # Review case: 5.00 - 4.4 = 0.60 from the displayed inputs; a true current of 4.37 shown as
    # 4.4 gives 0.63. The bound is 0.01 (the stated place) + 0.005 + 0.05 = 0.065: 0.63 agrees,
    # 0.70 (out by 0.10) still disagrees.
    by = {
        o.figure: o
        for o in ms.run("CP-4", cp4(covenant("Net leverage", current="4.4x", headroom="0.63x")))
    }
    assert by["Headroom: Net leverage"].status == "agreed"
    assert by["Headroom: Net leverage"].tolerance == pytest.approx(0.065)
    by = {
        o.figure: o
        for o in ms.run("CP-4", cp4(covenant("Net leverage", current="4.4x", headroom="0.70x")))
    }
    assert by["Headroom: Net leverage"].status == "disagreed"


def test_cp4_a_status_at_the_threshold_within_rounding_is_not_decided():
    # 3.50 against 3.50: headroom 0.00, inside the inputs' rounding (0.01) of zero. A stated
    # Breached (from an unrounded 3.504) is not sent back; at 3.40 Breached is a disagreement.
    rows = covenant("Senior secured leverage", headroom="(0.00x)", status="Breached")
    by = {o.figure: o for o in ms.run("CP-4", cp4(rows))}
    assert by["Status: Senior secured leverage"].status == "not checked"
    rows = covenant("Senior secured leverage", current="3.40x", headroom="0.10x", status="Breached")
    by = {o.figure: o for o in ms.run("CP-4", cp4(rows))}
    assert by["Status: Senior secured leverage"].status == "disagreed"


def test_cp4_the_stated_test_type_drives_the_sign():
    # Net leverage typed min-ratio: the script computes 4.20 - 5.00 = -0.80 and Breached.
    by = {o.figure: o for o in ms.run("CP-4", cp4(covenant("Net leverage", type="min-ratio")))}
    assert by["Headroom: Net leverage"].recomputed == pytest.approx(-0.8)
    assert by["Headroom: Net leverage"].status == "disagreed"


def test_cp4_a_test_type_not_stated_is_not_checked_never_inferred():
    for written, words in (
        ("—", "states no Test Type"),
        ("Maintenance", "names when the test applies"),
        ("Leverage", "does not read Test Type"),
    ):
        by = {o.figure: o for o in ms.run("CP-4", cp4(covenant("Net leverage", type=written)))}
        assert by["Headroom: Net leverage"].status == "not checked", written
        assert words in by["Headroom: Net leverage"].reason, written
    # The script's own spellings, and a type followed by words, are read.
    for written in ("max-ratio (leverage ceiling)", "Maximum", "ceiling"):
        by = {o.figure: o for o in ms.run("CP-4", cp4(covenant("Net leverage", type=written)))}
        assert by["Headroom: Net leverage"].status == "agreed", written


def test_cp4_a_missing_input_is_not_checked_and_never_zero():
    rows = covenant("Net leverage", current="[Insufficient Information]")
    by = {o.figure: o for o in ms.run("CP-4", cp4(rows))}
    assert by["Headroom: Net leverage"].status == by["Status: Net leverage"].status == "not checked"
    assert "states no Current Basis (missing, not zero)" in by["Headroom: Net leverage"].reason


def test_cp4_a_blank_headroom_is_missing_and_a_zero_is_a_figure():
    rows = covenant("Senior secured leverage", headroom="Not supplied: no certificate")
    by = {o.figure: o for o in ms.run("CP-4", cp4(rows))}
    assert by["Headroom: Senior secured leverage"].status == "not checked"
    assert by["Status: Senior secured leverage"].status == "agreed"
    by = {o.figure: o for o in ms.run("CP-4", cp4())}
    assert by["Headroom: Senior secured leverage"].status == "agreed"  # 0.00x


def test_cp4_a_unit_or_currency_mismatch_is_not_compared():
    for current in ("USD 0.08bn", "EUR 80m", "80"):
        rows = covenant("Minimum liquidity", current=current)
        by = {o.figure: o for o in ms.run("CP-4", cp4(rows))}
        assert by["Headroom: Minimum liquidity"].status == "not checked", current
        assert "different units" in by["Headroom: Minimum liquidity"].reason, current
    rows = covenant("Minimum liquidity", headroom="(20)")  # a bare figure for an amount
    by = {o.figure: o for o in ms.run("CP-4", cp4(rows))}
    assert "the Headroom is in `x`, its test in `USD m`" in by["Headroom: Minimum liquidity"].reason


def test_cp4_a_whole_bracketed_amount_is_negative():
    # Review: `(USD 20m)` is -20, as `USD (20)m` is.
    rows = covenant("Minimum liquidity", headroom="(USD 20m)")
    assert {o.figure: o for o in ms.run("CP-4", cp4(rows))}[
        "Headroom: Minimum liquidity"
    ].status == ("agreed")


def test_cp4_a_comparator_before_the_threshold_is_read():
    by = {o.figure: o for o in ms.run("CP-4", cp4(covenant("Net leverage", threshold="≤ 5.00x")))}
    assert by["Headroom: Net leverage"].status == "agreed"


def test_cp4_a_status_in_other_words_is_not_compared():
    by = {o.figure: o for o in ms.run("CP-4", cp4(covenant("Net leverage", status="Pass")))}
    assert by["Status: Net leverage"].status == "not checked"
    assert by["Headroom: Net leverage"].status == "agreed"


def test_cp4_an_absent_or_malformed_register_is_not_checked():
    (absent,) = ms.run("CP-4", cp4().replace("### T4C.4 — Headroom Table", "### Headroom"))
    assert absent.reason == "the handoff has no T4C.4 register"
    broken = cp4().replace("| Net leverage | max-ratio |", "| Net leverage | max-ratio | x |")
    (outcome,) = ms.run("CP-4", broken)
    assert "a row of 12 cells under 11 columns" in outcome.reason


# --- CP-1 ---------------------------------------------------------------------------------------

# SYNTHETIC, USD millions, FY2024. T4.9 free-name rows (Calculated Value = numerator / denominator,
# or that x 100, or numerator / denominator - 1 for a change):
#   EBITDA margin 500 / 2,000 = 0.25, written 25.0 (percent); Capex / revenue 100 / 2,000 = 0.05;
#   Revenue growth 2,000 / 1,600 - 1 = 0.25, written 25.0; FCF / debt 150 / 2,000 = 0.075, 7.5.
#   Liquidity (cash + undrawn) is a sum, not a quotient. Total debt / EBITDA is a fixed row.
# T4.8 LTM: revenue 2,000 + 1,100 - 1,000 = 2,100; EBITDA 500 + 300 - 250 = 550.
FREE_ROWS = {
    "Total debt / EBITDA": ("Total debt / EBITDA", "2,000", "500", "4.00"),
    "EBITDA margin": ("EBITDA / Revenue", "500", "2,000", "25.0"),
    "Capex / revenue": ("Capex / Revenue", "100", "2,000", "0.05"),
    "Revenue growth": ("FY2024 / FY2023 - 1", "2,000", "1,600", "25.0"),
    "FCF / debt": ("FCF / Total debt", "150", "2,000", "7.5"),
    "Liquidity": ("Cash + undrawn", "300", "200", "500"),
}
LTM_ROWS = {
    "Revenue": ("USD 2,000m", "USD 1,100m", "USD 1,000m", "USD 2,100m"),
    "EBITDA": ("USD 500m", "USD 300m", "USD 250m", "USD 550m"),
}
CP1_FIGURES = ("EBITDA margin", "Capex / revenue", "Revenue growth", "FCF / debt", "Liquidity")


def cp1(free=None, ltm=None, currency="USD", unit="millions"):
    free = FREE_ROWS if free is None else free
    ltm = LTM_ROWS if ltm is None else ltm
    return "\n".join(
        [
            "## Findings",
            "### Bottom line",
            "Leverage is high.",
            "### T4.8 Constructed period register",
            (
                "| Metric Name | Derived Period Type | Full-Year Component | Current Stub | "
                "Prior-Year Stub | Derived Value | Calculation Status | Source Files | "
                "Limitations |"
            ),
            "|---|---|---|---|---|---|---|---|---|",
            *(f"| {m} | LTM | {' | '.join(v)} | Derived | S1 | — |" for m, v in ltm.items()),
            "| Revenue | Q2 | USD 2,000m | USD 600m | — | USD 1,400m | Derived | S1 | — |",
            "",
            "### T4.9 Calculation register",
            (
                "| Metric Name | Formula | Numerator Value | Numerator Source | "
                "Denominator Value | Denominator Source | Period | Currency | Unit | "
                "Calculated Value | Calculation Status | Evidence Quality Tier | Limitations |"
            ),
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
            *(
                f"| {m} | {v[0]} | {v[1]} | S1 | {v[2]} | S1 | FY2024 | {currency} | {unit} | "
                f"{v[3]} | Calculated | A | — |"
                for m, v in free.items()
            ),
            "## Gaps",
            "None.",
        ]
    )


def cp1_by(text):
    return {o.figure: o for o in ms.run("CP-1", text)}


def test_cp1_all_figures_right():
    by = cp1_by(cp1())
    assert [by[f"{m} (FY2024)"].status for m in CP1_FIGURES[:4]] == ["agreed"] * 4
    assert by["Liquidity (FY2024)"].status == "not checked"  # a sum: not a quotient
    assert by["LTM: Revenue"].status == by["LTM: EBITDA"].status == "agreed"
    assert by["LTM: Revenue"].recomputed == 2100.0 and by["LTM: Revenue"].unit == "USD m"
    assert "agrees as the ratio in percent" in by["EBITDA margin (FY2024)"].reason
    assert "agrees as the growth in percent" in by["Revenue growth (FY2024)"].reason
    assert ms.issues("CP-1", cp1()) == ()


def test_cp1_leaves_the_six_fixed_rows_to_the_cp1_check():
    from deploy_workflow.owners.cpos_cp1_check import METRICS

    assert ms.method_scripts_cp1.FIXED_ROWS == tuple(m.name for m in METRICS)
    assert "Total debt / EBITDA (FY2024)" not in cp1_by(cp1())
    # ... even when its figure is wrong: the CP-1 check sends that back, not this one.
    wrong = FREE_ROWS | {"Total debt / EBITDA": ("Total debt / EBITDA", "2,000", "500", "5.00")}
    assert ms.issues("CP-1", cp1(wrong)) == ()


def test_cp1_one_figure_wrong():
    text = cp1(FREE_ROWS | {"EBITDA margin": ("EBITDA / Revenue", "500", "2,000", "26.0")})
    (issue,) = ms.issues("CP-1", text)
    assert "T4.9 row `EBITDA margin (FY2024)` states 26.0" in issue
    assert "recomputes 25 " in issue and "nearest as the ratio in percent" in issue
    assert "credit_metrics.py" in issue
    ltm = LTM_ROWS | {"Revenue": (*LTM_ROWS["Revenue"][:3], "USD 2,200m")}
    (issue,) = ms.issues("CP-1", cp1(ltm=ltm))
    assert "T4.8 row `LTM: Revenue` states 2,200 USD m" in issue and "recomputes 2100" in issue


def test_cp1_a_sign_error_is_a_disagreement():
    ltm = LTM_ROWS | {"Revenue": (*LTM_ROWS["Revenue"][:3], "USD (2,100)m")}
    assert cp1_by(cp1(ltm=ltm))["LTM: Revenue"].status == "disagreed"
    free = FREE_ROWS | {"Revenue growth": ("FY2024 / FY2023 - 1", "2,000", "1,600", "-25.0")}
    assert cp1_by(cp1(free))["Revenue growth (FY2024)"].status == "disagreed"


def test_cp1_the_operand_identity_trap_on_the_retained_tdg_figures():
    # Figures from the real TransDigm excerpt (tests/fixtures/tdg_sol_high_2026_11_13, FY2024, USD
    # millions; the row layout is synthetic): total debt principal 25,068, carrying 24,880, EBITDA
    # 3,813. 25,068 / 3,813 = 6.574 (6.57); 24,880 / 3,813 = 6.525 (6.53). The check binds the
    # row's own operands, not which debt they are: 6.57 on principal agrees with its own division.
    name = "Total debt / unadjusted EBITDA"
    principal = {name: ("Total debt / EBITDA", "25,068", "3,813", "6.57")}
    assert cp1_by(cp1(principal))[f"{name} (FY2024)"].status == "agreed"
    carrying = {name: ("Total debt / EBITDA", "24,880", "3,813", "6.57")}
    outcome = cp1_by(cp1(carrying))[f"{name} (FY2024)"]
    assert outcome.status == "disagreed"
    assert outcome.recomputed == pytest.approx(24880 / 3813)


def test_cp1_a_denominator_at_or_below_zero_follows_the_scripts_convention():
    # Review cases. 500 / -10: the method's Not Calculable agrees, in any of the null words.
    def outcome(name, formula, d, value):
        return cp1_by(cp1({name: (formula, "500", d, value)}))[f"{name} (FY2024)"]

    for value in ("Not Calculable", "n.m.", "Not meaningful (negative EBITDA)"):
        assert outcome("Debt / EBITDA pro forma", "Debt / EBITDA", "-10", value).status == "agreed"
        assert outcome("Sales ratio", "Sales / Base", "0", value).status == "agreed", value
    # A figure: a leverage quotient against EBITDA below zero has none (the script's convention).
    lev = outcome("Debt / EBITDA pro forma", "Debt / EBITDA", "-10", "-50.0x")
    assert lev.status == "disagreed" and lev.recomputed_label == "Not Calculable"
    # ... any quotient against zero has none ...
    assert outcome("Sales ratio", "Sales / Base", "0", "0.0").status == "disagreed"
    # ... but a growth or margin against a negative base is not the script's to decide.
    growth = outcome("EBITDA growth", "FY2024 / FY2023 - 1", "-10", "-5100.0")
    assert growth.status == "not checked" and "fixes no convention" in growth.reason


def test_cp1_the_rows_formula_chooses_ratio_or_growth():
    # Revenue growth 2,000 / 1,600 - 1 = 0.25. Stated 1.25 (the ratio, not the change) now
    # disagrees; it agreed when every form was accepted (review).
    growth = FREE_ROWS | {"Revenue growth": ("FY2024 / FY2023 - 1", "2,000", "1,600", "1.25")}
    assert cp1_by(cp1(growth))["Revenue growth (FY2024)"].status == "disagreed"
    # A margin is a ratio, written as a decimal or in percent: 0.25 and 25.0 both agree.
    for value in ("0.25", "25.0", "25.0%"):
        margin = FREE_ROWS | {"EBITDA margin": ("EBITDA / Revenue", "500", "2,000", value)}
        assert cp1_by(cp1(margin))["EBITDA margin (FY2024)"].status == "agreed", value
    # `x 100` in the formula: percent only; 0.25 is then not the figure.
    pct = FREE_ROWS | {"EBITDA margin": ("EBITDA / Revenue x 100", "500", "2,000", "0.25")}
    assert cp1_by(cp1(pct))["EBITDA margin (FY2024)"].status == "disagreed"


def test_cp1_a_figure_wrong_by_more_than_the_rounding_bound_still_disagrees():
    # 25,068 / 3,813 = 6.5743; bound 0.01 + (0.5 + 6.574 x 0.5) / 3,813 = 0.01099: 6.58 agrees,
    # 6.59 (out by 0.0157) does not.
    name = "Total debt / unadjusted EBITDA"
    for value, status in (("6.58", "agreed"), ("6.59", "disagreed")):
        row = {name: ("Total debt / EBITDA", "25,068", "3,813", value)}
        assert cp1_by(cp1(row))[f"{name} (FY2024)"].status == status, value


def test_cp1_a_missing_input_is_not_checked_and_never_zero():
    ltm = LTM_ROWS | {
        "Revenue": (*LTM_ROWS["Revenue"][:2], "Not supplied: no Q3 2023", "USD 2,100m")
    }
    outcome = cp1_by(cp1(ltm=ltm))["LTM: Revenue"]
    assert outcome.status == "not checked"
    assert "states no Prior-Year Stub (missing, not zero)" in outcome.reason
    free = FREE_ROWS | {"Capex / revenue": ("Capex / Revenue", "100", "Not supplied: x", "0.05")}
    outcome = cp1_by(cp1(free))["Capex / revenue (FY2024)"]
    assert outcome.status == "not checked" and "(missing, not zero)" in outcome.reason


def test_cp1_a_blank_is_missing_and_a_zero_is_a_figure():
    # Current stub 0: 2,000 + 0 - 1,000 = 1,000.
    ltm = LTM_ROWS | {"Revenue": ("USD 2,000m", "USD 0m", "USD 1,000m", "USD 1,000m")}
    assert cp1_by(cp1(ltm=ltm))["LTM: Revenue"].status == "agreed"
    # Revenue 0: no margin. `Not calculable` agrees with the script's None; a figure does not.
    zero = FREE_ROWS | {
        "EBITDA margin": ("EBITDA / Revenue", "500", "0", "Not calculable: no sales")
    }
    assert cp1_by(cp1(zero))["EBITDA margin (FY2024)"].status == "agreed"
    zero = FREE_ROWS | {"EBITDA margin": ("EBITDA / Revenue", "500", "0", "0.0")}
    assert cp1_by(cp1(zero))["EBITDA margin (FY2024)"].status == "disagreed"


def test_cp1_a_unit_mismatch_or_two_currencies_are_not_compared():
    for cell in ("USD 1.1bn", "EUR 1,100m"):
        ltm = LTM_ROWS | {"Revenue": ("USD 2,000m", cell, "USD 1,000m", "USD 2,100m")}
        outcome = cp1_by(cp1(ltm=ltm))["LTM: Revenue"]
        assert outcome.status == "not checked" and "different units" in outcome.reason, cell
    bare = {
        m: tuple(c.removeprefix("USD ").removesuffix("m") for c in v) for m, v in LTM_ROWS.items()
    }
    outcome = cp1_by(cp1(ltm=bare))["LTM: Revenue"]
    assert outcome.status == "not checked" and "states no currency or scale" in outcome.reason
    outcome = cp1_by(cp1(unit="Not supplied: x"))["EBITDA margin (FY2024)"]
    assert outcome.status == "not checked" and "no Currency or Unit" in outcome.reason


def test_cp1_an_absent_or_malformed_register_is_not_checked():
    no_ltm = cp1().replace("### T4.8 Constructed period register", "### Constructed periods")
    by = cp1_by(no_ltm)
    assert by["T4.8"].reason == "the handoff has no T4.8 register"
    assert by["EBITDA margin (FY2024)"].status == "agreed"
    broken = cp1().replace("| EBITDA margin | EBITDA / Revenue |", "| EBITDA margin | x | y |")
    assert "a row of 14 cells under 13 columns" in cp1_by(broken)["T4.9"].reason


def test_cp1_the_retained_tdg_excerpt_has_neither_register():
    # Real (TransDigm, run of 2026-11-13): the older CP-1 layout, written before T4.8 and T4.9.
    text = (ROOT / "tests/fixtures/tdg_sol_high_2026_11_13/CP-1-tables.md").read_text()
    by = cp1_by(text)
    assert set(by) == {"T4.8", "T4.9"} and {o.status for o in by.values()} == {"not checked"}


# --- the policy -----------------------------------------------------------------------------------


def test_modules_without_a_script_check_get_none():
    assert ms.run("CP-0", cp2d()) == () and ms.issues("CP-5", "anything") == ()
    assert ms.record("CP-0", b"x") is None


def test_a_script_that_fails_becomes_not_checked(monkeypatch):
    def broken(*_args, **_kwargs):
        raise ZeroDivisionError("inside the script")

    monkeypatch.setattr(ms._loaded(ms.LIQUIDITY_BRIDGE).script, "compute", broken)
    (outcome,) = ms.run("CP-2D", cp2d())
    assert outcome.status == "not checked"
    assert outcome.reason == "the check could not run: ZeroDivisionError: inside the script"
    assert ms.issues("CP-2D", cp2d()) == ()


def test_a_refused_script_becomes_not_checked(monkeypatch):
    def refused(path):
        raise ms.ScriptRefused(f"{path}: its bytes are not the registered ones")

    monkeypatch.setattr(ms, "_loaded", refused)
    (outcome,) = ms.run("CP-3C", cp3c())
    assert outcome.status == "not checked" and "not the registered ones" in outcome.reason


def test_the_record_holds_every_outcome_and_the_script_hash():
    raw = cp2d(BRIDGE | {ENDING: "310"}).encode()
    record = ms.record("CP-2D", raw)
    assert record["kind"] == ms.RECORD_KIND
    assert record["response_sha256"] == hashlib.sha256(raw).hexdigest()
    assert record["scripts"] == {ms.LIQUIDITY_BRIDGE: ms.registered()[ms.LIQUIDITY_BRIDGE]}
    assert [(c["figure"], c["status"]) for c in record["checks"]] == [
        (ms.ENDING, "disagreed"),
        (ms.MTE, "agreed"),
    ]
    json.dumps(record)  # it is written as JSON
    assert ms.record("CP-2D", b"\xff")["checks"][0]["reason"] == "not UTF-8"


ENDING = ms.ENDING
