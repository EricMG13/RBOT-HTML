"""The Downside stress case follows the forward credit model (ruling 2026-11-13).

The fixture is cut verbatim from the real run tdg-full-copilot-sol-high-001-resume; the answer
keys below are hand-written from that run's own CP-2G figures (CP-2G.md C05) and CP-2A's s01.
"""

import hashlib
import json
import re
import sys
import types
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from deploy_workflow.owners import cp2g, cpos_forecast, cpos_launch
from deploy_workflow.owners.cpos_forecast import model_files

sys.path.insert(0, str(Path(__file__).parents[1] / "apps" / "issuer-library"))
from credit_os import store

FIXTURE = Path(__file__).parent / "fixtures" / "tdg_sol_high_2026_11_13"
CP1 = (FIXTURE / "CP-1-tables.md").read_bytes()
BLOCK = (FIXTURE / "CP-2G-forecast-block.md").read_text(encoding="utf-8")
T2DS = (FIXTURE / "CP-2A-T2DS.1.md").read_bytes()
FENCED = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def block_with(**changes) -> str:
    """The real block with some keys replaced (nothing else edited)."""
    match = FENCED.search(BLOCK)
    document = json.loads(match.group(1))
    document.update(changes)
    return BLOCK[: match.start(1)] + json.dumps(document) + BLOCK[match.end(1) :]


def shock(decline="0.2", increase="0.3"):
    return {"ebitda_decline": decline, "rate_increase": increase}


def exact_of(block: str) -> dict:
    return json.loads(model_files(CP1, block.encode())["forecast_exact.json"])


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


# --- 1. the calculation ---------------------------------------------------------------------


def test_the_stress_case_is_the_shock_on_the_downside_drivers_for_the_real_run():
    exact = exact_of(block_with(downside_shock=shock()))
    years = exact["outputs"]["DOWNSIDE"]["years"]
    assert [y["revenue"]["amount"] for y in years] == ["7940", "7940", "7940"]  # flat, not +12%
    first = years[0]
    assert Decimal(first["ebitda"]["amount"]) == Decimal("3338.6112")  # 7940 x 0.5256 x 0.8
    # The module printed 1982.936 (CP-2G.md C05) because it rounded its shocked yield to 0.0797.
    # The proportional field gives the exact figure 24880 x 0.0613 x 1.3 = 1982.6872; the 0.2488
    # difference is that rounding, and no tolerance is used to make them equal.
    assert Decimal(first["interest"]["amount"]) == Decimal("1982.68720")
    coverage = Decimal(first["ebitda"]["amount"]) / Decimal(first["interest"]["amount"])
    assert coverage.quantize(Decimal("0.01")) == Decimal("1.68")  # the module's own figure
    assert exact["downside_basis"] == "downside_drivers"


def test_without_downside_drivers_the_shock_is_on_the_base_drivers_and_the_bytes_are_unchanged():
    files = model_files(CP1, block_with(downside_drivers=None).encode())
    exact = json.loads(files["forecast_exact.json"])
    assert "downside_basis" not in exact
    revenue = exact["outputs"]["DOWNSIDE"]["years"][0]["revenue"]["amount"]
    assert Decimal(revenue) == Decimal("8892.8")  # 7940 x 1.12, base growth
    # Pinned from origin/main's output for the same block before the change.
    assert sha(files["forecast_exact.json"]) == (
        "01595b50efc9e010dacc47aa01ea2b052c5a2b4f22a0d7215079b8530e7177d7"
    )
    assert sha(files["calculation.json"]) == (
        "e2c2cd687f2b3c7a6f423beba59543b4dd0d16e1af5964ea3fa04312ce1d2682"
    )


def test_a_block_with_no_shock_publishes_the_bytes_it_always_did():
    files = model_files(CP1, block_with(downside_shock=None).encode())
    assert "downside_basis" not in json.loads(files["forecast_exact.json"])
    assert sha(files["forecast_exact.json"]) == (
        "80ca308273bf8baf666c63f0c82e2e74fee70a2a13befe627c64ca0a8394a5d1"
    )
    assert sha(files["calculation.json"]) == (
        "177de2661617322811f741e16b764dc13e70a572374adcc05094f483dba904bc"
    )


decimals = st.integers(min_value=0, max_value=10_000).map(lambda n: str(Decimal(n) / 10_000))


@settings(max_examples=25, deadline=None)
@given(
    decline=decimals,
    increase=decimals,
    growth=st.lists(decimals, min_size=3, max_size=3),
    with_downside_drivers=st.booleans(),
)
def test_the_stress_case_equals_the_forecast_of_the_shock_over_the_cases_drivers(
    decline, increase, growth, with_downside_drivers
):
    downside = None
    if with_downside_drivers:
        driver = {
            "values": growth,
            "category": "Analyst Interpretation",
            "rationale": "r",
            "limitation": None,
        }
        downside = {"revenue_growth": driver}
    block = block_with(downside_shock=shock(decline, increase), downside_drivers=downside)
    inputs = cpos_forecast.parse(block, CP1.decode("utf-8"))
    base = inputs.base_drivers
    drivers = base if inputs.downside_drivers is None else inputs.downside_drivers.over(base)
    operands = cp2g.Operands(
        **{
            key: cp2g.Val(None if o.amount is None else Decimal(o.amount), o.reason)
            for key, o in inputs.base.items()
        }
    )
    expected = cp2g.forecast(
        operands=operands,
        drivers=cp2g.Drivers.from_submission(drivers),
        shock=(Decimal(decline), Decimal(increase)),
    )
    exact = exact_of(block)
    got = exact["outputs"]["DOWNSIDE"]["years"]
    for year, want in zip(got, expected.years, strict=True):
        for name in ("revenue", "ebitda", "interest", "closing_cash", "coverage"):
            assert year[name]["amount"] == (
                None
                if getattr(want, name).amount is None
                else format(getattr(want, name).amount, "f")
            )
    assert ("downside_basis" in exact) is with_downside_drivers


# --- 2. the page's labels -------------------------------------------------------------------

BASIS_LABEL = "Downside stress (shock on downside drivers)"
BASIS_NOTE = (
    "Downside case is the stress case: a shock applied to the model's own downside drivers."
)
OLD_LABEL = "Downside stress (shock on base drivers)"
OLD_NOTE = "Downside case is the stress case: a shock applied to the base-case drivers."


def test_the_page_names_the_basis_the_model_states():
    exact = {
        "outputs": {
            k: {"years": [{"year": 2025, "planning_start": "a", "planning_end": "b"}]}
            for k in ("REFERENCE", "DOWNSIDE_DRIVERS", "DOWNSIDE")
        },
        "scope_limits": [],
        "downside_basis": "downside_drivers",
    }
    cases, _, keys = store.forecast_inputs(exact)
    assert dict(zip(keys, (name for name, _ in cases), strict=True))["DOWNSIDE"] == BASIS_LABEL
    assert store.main_cases(cases, keys)[2] == BASIS_NOTE
    older = {k: v for k, v in exact.items() if k != "downside_basis"}
    cases, _, keys = store.forecast_inputs(older)
    assert dict(zip(keys, (name for name, _ in cases), strict=True))["DOWNSIDE"] == OLD_LABEL
    assert store.main_cases(cases, keys)[2] == OLD_NOTE


# --- 3. the instruction ---------------------------------------------------------------------


def test_the_instruction_says_the_shock_is_one_cp2a_row_and_a_proportional_interest_increase():
    text = cpos_launch.FORECAST_BLOCK
    assert "applies it to the base drivers." not in text
    assert "copied unchanged from one CP-2A scenario row" in text
    assert "proportional cash-interest increase, never a yield change" in text
    assert "to your downside drivers, or to the base drivers when you set none" in text


# --- 4. the launcher's check ----------------------------------------------------------------

SOL_001_T2DS = b"""<!-- table-id: T2DS.1 -->
| Scenario | EBITDA decline fraction s | Cash-interest increase fraction k | Note |
|---|---|---|---|
| s00 \xe2\x80\x94 control | 0 | 0 | none |
| s01 \xe2\x80\x94 operating warning | 0.20 | 0.025 (2.5% increase) | none |
| s02 \xe2\x80\x94 cash-conversion break | 0.45 | 0.05 | none |
"""


def task_with(cp2a: bytes | None):
    handoffs = {"CP-1": CP1}
    if cp2a is not None:
        handoffs["CP-2A"] = cp2a
    return types.SimpleNamespace(module_id="CP-2G", handoffs=handoffs)


def issues(block, cp2a):
    return cpos_launch._forecast_issues(task_with(cp2a), block)


def test_the_module_as_sent_is_sent_back_because_a_yield_change_is_not_a_scenario():
    (issue,) = issues(BLOCK, T2DS)  # 0.2 / 0.0184, as the module sent it
    assert "copy one CP-2A scenario" in issue
    assert "never a yield change" in issue
    assert "0.2000 / 0.3000" in issue and "0.4000 / 0.3000" in issue


def test_the_stated_scenario_is_accepted_whatever_its_trailing_zeros():
    assert issues(block_with(downside_shock=shock("0.2", "0.3")), T2DS) == ()
    assert issues(block_with(downside_shock=shock("0.4000", "0.30")), T2DS) == ()


def test_the_other_real_table_form_is_read_too():
    ok = block_with(downside_shock=shock("0.2", "0.025"))
    assert issues(ok, SOL_001_T2DS) == ()
    (issue,) = issues(block_with(downside_shock=shock("0.2", "0.3")), SOL_001_T2DS)
    assert "0.20 / 0.025" in issue or "0.2 / 0.025" in issue


@pytest.mark.parametrize(
    "cp2a",
    [
        None,
        b"No tables here.\n",
        b"<!-- table-id: T2DS.1 -->\n| Scenario | Name |\n|---|---|\n| s01 | x |\n",
        (
            b"<!-- table-id: T2DS.1 -->\n| Scenario | EBITDA decline | Cash-interest increase |\n"
            b"|---|---|---|\n| s01 | n/a | n/a |\n"
        ),
    ],
    ids=["no CP-2A", "no table", "no columns", "no row readable"],
)
def test_a_table_python_cannot_read_never_sends_the_block_back(cp2a):
    assert issues(BLOCK, cp2a) == ()  # documented fail-open: a repair round costs money


def test_no_shock_needs_no_scenario():
    assert issues(block_with(downside_shock=None), T2DS) == ()
