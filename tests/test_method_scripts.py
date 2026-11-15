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
    units = {"Cash interest": "US$ millions", "Cash taxes": "USD mn", ENDING: "USD million"}
    assert statuses(ms.run("CP-2D", cp2d(units=units))) == {ms.ENDING: "agreed", ms.MTE: "agreed"}


def test_cp2d_an_absent_register_is_not_checked():
    text = cp2d().replace("### T2E.5 — 12-Month Liquidity Bridge", "### Liquidity bridge")
    outcomes = ms.run("CP-2D", text)
    assert [o.reason for o in outcomes] == ["the handoff has no T2E.5 register"] * 2


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


def test_cp3c_a_malformed_table_is_not_checked():
    text = cp3c().replace(
        "| Line | Amount | Drawn | Years | Committed | Currency | Scale |\n|---|",
        "| Line | Amount | Drawn | Years | Committed | Currency | Scale |\n|--|",
    )
    outcomes = ms.run("CP-3C", text)
    assert {o.status for o in outcomes} == {"not checked"}
    assert "no separator row" in outcomes[0].reason


def test_cp3c_no_horizon_is_refused_by_the_script():
    outcomes = ms.run("CP-3C", cp3c(funding=[r for r in FUNDING if r[0] != "Horizon"]))
    assert {o.status for o in outcomes} == {"not checked"}
    assert "horizon_years is required" in outcomes[0].reason


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
