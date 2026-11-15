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
    assert ending.tolerance == 1.0  # no decimal shown: one unit
    assert outcomes[1].tolerance == pytest.approx(0.1)  # `48.0`: one unit in the first place
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


def test_cp2d_months_to_empty_within_one_displayed_unit():
    # 48 exactly: 48 and 48.00 agree, 48.2 is out by more than 0.1.
    assert ms.run("CP-2D", cp2d(months="48 months"))[1].status == "agreed"
    assert ms.run("CP-2D", cp2d(months="48.00"))[1].status == "agreed"
    assert ms.run("CP-2D", cp2d(months="48.2"))[1].status == "disagreed"


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
    assert [o.tolerance for o in outcomes] == pytest.approx([1.0, 0.1, 0.1])
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
    # The impact is a cost of 5.0; written (5.0) it is -5.0 against the script's 5.0.
    outcomes = ms.run("CP-2E", cp2e(impact="USD (5.0)m"))
    assert [o.status for o in outcomes] == ["agreed", "agreed", "disagreed"]
    assert outcomes[2].recomputed == 5.0


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


def test_cp2e_hedged_above_gross_is_refused_by_the_script_not_clamped_to_zero():
    # Hedged 900 against gross 800: the perimeters differ or a hedge is double-counted. The script
    # refuses rather than report zero unhedged exposure; the stated 0 is neither passed nor sent
    # back: it is recorded as not checked, with the script's reason.
    rows = EXPOSURE | {
        "Hedged floating-rate debt": "USD 900m",
        "Unhedged floating-rate debt": "USD 0m",
        "Unhedged debt percentage": "0.0%",
    }
    outcomes = ms.run("CP-2E", cp2e(rows, impact="USD 0m"))
    assert statuses(outcomes) == dict.fromkeys(CP2E_FIGURES, "not checked")
    assert "exceeds gross floating-rate debt" in outcomes[0].reason
    assert ms.issues("CP-2E", cp2e(rows, impact="USD 0m")) == ()


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
    assert low["Recovery: Term Loan B"].tolerance == pytest.approx(0.1)
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


# --- the policy -----------------------------------------------------------------------------------


def test_modules_without_a_script_check_get_none():
    assert ms.run("CP-2G", cp2d()) == () and ms.issues("CP-1", "anything") == ()
    assert ms.record("CP-2G", b"x") is None


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
