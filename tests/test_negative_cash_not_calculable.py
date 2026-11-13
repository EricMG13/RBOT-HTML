"""No net debt, net leverage or liquidity is published for a forecast year with negative cash
(owner decision 2026-11-13). Answer keys are hand-written from the real run
tdg-full-copilot-sol-high-001-resume, Downside case, shock 0.3 (fixture cut from that run)."""

import json
from dataclasses import replace
from decimal import Decimal, localcontext

from hypothesis import given, settings
from hypothesis import strategies as st
from test_downside_follows_forward_model import CP1, block_with, exact_of, sha, shock

from deploy_workflow.owners import cp2g, cpos_forecast

REASON = "Not calculable: cash is negative before funding"
FIELDS = ("net_debt", "net_leverage", "liquidity")


def downside_years(**changes):
    block = block_with(downside_shock=shock("0.2", "0.3"), **changes)
    return exact_of(block)["outputs"]["DOWNSIDE"]["years"]


def amounts(year, *names):
    return {n: year[n]["amount"] for n in names}


def test_the_real_run_publishes_net_figures_only_for_the_year_with_cash():
    first, second, third = downside_years()
    # FY2025: cash is positive, so the figures stay.
    assert Decimal(first["net_debt"]["amount"]) == Decimal("22746.4960")
    ratio = Decimal(first["net_leverage"]["amount"])
    with localcontext() as context:
        context.prec = 38  # the module's quotient carries 38 significant digits
        key = Decimal("22746.4960") / Decimal("3338.6112")
    assert ratio == key
    assert ratio.quantize(Decimal("0.01")) == Decimal("6.81")
    assert Decimal(first["liquidity"]["amount"]) == Decimal("2396.504")
    # FY2026 and FY2027: cash is an unfunded gap, so the three figures are missing with a reason.
    for year in (second, third):
        for name in FIELDS:
            assert year[name] == {"amount": None, "reason": REASON}
    # The cash itself is not hidden, and the roll-forward is untouched.
    assert Decimal(second["closing_cash"]["amount"]) == Decimal("-309.7718")
    assert Decimal(third["closing_cash"]["amount"]) == Decimal("-2165.71612")
    assert Decimal(third["opening_cash"]["amount"]) == Decimal("-309.7718")
    # Captured from the output at 01eee08 (the parent), not hand-written; unchanged by this change.
    assert amounts(first, "total_leverage", "coverage") == {
        "total_leverage": "7.2784755529484834891825678893067872054",
        "coverage": "1.6838819557618569384015794321968689766",
    }
    assert amounts(second, "total_leverage", "coverage") == {
        "total_leverage": "7.2509191845998719467543869738410989576",
        "coverage": "1.7240733769281893262317405873686460962",
    }
    assert amounts(third, "total_leverage", "coverage") == {
        "total_leverage": "7.2233628162512604043262060583754107097",
        "coverage": "1.7306255394644332711265406589994258154",
    }


def test_the_forward_model_itself_still_computes_the_numbers():
    inputs = cpos_forecast.parse(block_with(downside_shock=shock()), CP1.decode("utf-8"))
    operands = cp2g.Operands(
        **{
            key: cp2g.Val(None if o.amount is None else Decimal(o.amount), o.reason)
            for key, o in inputs.base.items()
        }
    )
    result = cp2g.forecast(
        operands=operands,
        drivers=cp2g.Drivers.from_submission(inputs.downside_drivers.over(inputs.base_drivers)),
        shock=(Decimal("0.2"), Decimal("0.3")),
    )
    second, third = result.years[1], result.years[2]
    assert second.closing_cash.amount == Decimal("-309.7718")
    assert third.opening_cash.amount == Decimal("-309.7718")
    assert second.net_leverage.amount is not None
    assert second.liquidity.amount == Decimal("533.2282")
    assert third.liquidity.amount == Decimal("-1322.71612")


def real_year():
    """A real forecast year (FY2025: positive cash) to vary one field of."""
    inputs = cpos_forecast.parse(block_with(downside_shock=shock()), CP1.decode("utf-8"))
    operands = cp2g.Operands(
        **{
            key: cp2g.Val(None if o.amount is None else Decimal(o.amount), o.reason)
            for key, o in inputs.base.items()
        }
    )
    result = cp2g.forecast(
        operands=operands,
        drivers=cp2g.Drivers.from_submission(inputs.downside_drivers.over(inputs.base_drivers)),
        shock=(Decimal("0.2"), Decimal("0.3")),
    )
    return result.years[0]


def with_cash(amount):
    return replace(real_year(), closing_cash=cp2g.Val(amount))


def test_zero_cash_is_not_a_gap_and_keeps_the_three_figures():
    for zero in (Decimal(0), Decimal("-0")):
        published = cpos_forecast._published(with_cash(zero))
        want = cpos_forecast._published(real_year())
        for name in FIELDS:
            assert published[name] == want[name]
            assert published[name]["amount"] is not None
            assert published[name]["reason"] is None
        assert published["net_debt"]["amount"] == "22746.496"
        assert published["liquidity"]["amount"] == "2396.504"


def test_missing_cash_is_not_called_negative():
    own = "net leverage: its own reason"
    year = replace(
        real_year(),
        closing_cash=cp2g.Val(None, "closing cash: some reason"),
        net_leverage=cp2g.Val(None, own),
    )
    published = cpos_forecast._published(year)
    assert published["net_debt"] == {"amount": "22746.496", "reason": None}
    assert published["net_leverage"] == {"amount": None, "reason": own}
    assert published["liquidity"] == {"amount": "2396.504", "reason": None}
    assert published["closing_cash"] == {"amount": None, "reason": "closing cash: some reason"}
    assert "cash is negative" not in json.dumps(published)


def test_the_smallest_negative_cash_hides_the_three_figures():
    published = cpos_forecast._published(with_cash(Decimal("-0.0001")))
    for name in FIELDS:
        assert published[name] == {
            "amount": None,
            "reason": "Not calculable: cash is negative before funding",
        }
    assert published["closing_cash"] == {"amount": "-0.0001", "reason": None}
    assert published["total_leverage"] == cpos_forecast._published(real_year())["total_leverage"]


def test_a_block_that_never_reaches_negative_cash_publishes_the_bytes_it_did():
    # Pinned from the output at 01eee08 (the parent), whose cases these are.
    exact = exact_of(block_with(downside_shock=shock()))
    pins = {
        "REFERENCE": "9a18aea18eb38420f211131e835916059728fe37cf5513d5db70b0393ccc9a30",
        "UPSIDE": "e9af0ea2790bb09024ae87aa475ed10ab570cfd37bde9fe0af25c03b0976164e",
    }
    for case, pin in pins.items():
        blob = json.dumps(exact["outputs"][case], sort_keys=True).encode()
        assert sha(blob) == pin


decimals = st.integers(min_value=0, max_value=10_000).map(lambda n: str(Decimal(n) / 10_000))


@settings(max_examples=40, deadline=None)
@given(
    decline=decimals,
    increase=decimals,
    growth=st.lists(decimals, min_size=3, max_size=3),
    dividends=st.lists(st.integers(min_value=0, max_value=20_000).map(str), min_size=3, max_size=3),
)
def test_the_three_fields_are_missing_if_and_only_if_closing_cash_is_negative(
    decline, increase, growth, dividends
):
    def driver(values):
        return {
            "values": values,
            "category": "Analyst Interpretation",
            "rationale": "r",
            "limitation": None,
        }

    downside = {"revenue_growth": driver(growth), "dividends": driver(dividends)}
    block = block_with(downside_shock=shock(decline, increase), downside_drivers=downside)
    inputs = cpos_forecast.parse(block, CP1.decode("utf-8"))
    operands = cp2g.Operands(
        **{
            key: cp2g.Val(None if o.amount is None else Decimal(o.amount), o.reason)
            for key, o in inputs.base.items()
        }
    )
    want = cp2g.forecast(
        operands=operands,
        drivers=cp2g.Drivers.from_submission(inputs.downside_drivers.over(inputs.base_drivers)),
        shock=(Decimal(decline), Decimal(increase)),
    )
    got = exact_of(block)["outputs"]["DOWNSIDE"]["years"]
    for year, expected in zip(got, want.years, strict=True):
        cash = expected.closing_cash.amount
        assert year["closing_cash"]["amount"] == (None if cash is None else format(cash, "f"))
        for name in FIELDS:
            value = getattr(expected, name)
            if cash is not None and cash < 0:
                assert year[name] == {"amount": None, "reason": REASON}
            else:
                assert year[name] == {
                    "amount": None if value.amount is None else format(value.amount, "f"),
                    "reason": value.reason,
                }
