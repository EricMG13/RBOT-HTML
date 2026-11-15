"""CP-2E's method script, `rate_fx_sensitivity.py`, run on T2F.4 and T2F.5 (harness:
`deploy_workflow.method_scripts`).

The method's step 4 (REF_CP-2E_04) makes T2F.4 carry the rows Total debt, Gross floating-rate debt,
Hedged floating-rate debt, Unhedged floating-rate debt and Unhedged debt percentage; step 5
(REF_CP-2E_05) makes T2F.5 carry the +100 bps cash-interest impact. T2F.4 has no currency or scale
column, so each amount states its own (`USD 1,250m`), or the amount column's header does
(`Amount (USD m)`); a cell's own unit wins. FX and cost sensitivities are not checked: their net
exposure and adverse move are free text in T2F.6 and T2F.7, not columns.
"""

import types
from dataclasses import dataclass, replace
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    AMOUNT_STEP,
    ARCHIVE,
    Amount,
    Loaded,
    Outcome,
    Table,
    _Claim,
    _judged,
    _label,
    _NotChecked,
    _Where,
    bare,
    blank,
    column,
    money,
    quotient_slack,
    register_table,
    share,
)

RATE_FX = ARCHIVE + "skills/cp-2e-macro-fx-hedging-sensitivity/scripts/rate_fx_sensitivity.py"
TOTAL = "Total debt"
GROSS = "Gross floating-rate debt"
HEDGED = "Hedged floating-rate debt"
UNHEDGED = "Unhedged floating-rate debt"
SHARE = "Unhedged debt percentage"
SHOCK = "+100 bps cash-interest impact"
EXPOSURE_ROWS = (TOTAL, GROSS, HEDGED, UNHEDGED, SHARE)  # REF_CP-2E_04 instruction 2
UNHEDGED_FORMULA = (
    "Unhedged floating-rate debt = Gross floating-rate debt - Hedged floating-rate debt "
    "(REF_CP-2E_04)"
)
SHARE_FORMULA = "Unhedged debt percentage = Unhedged floating-rate debt / Total debt (REF_CP-2E_04)"
SHOCK_FORMULA = (
    "+100 bps cash-interest impact = (Gross floating-rate debt - Hedged floating-rate debt) x "
    "1.00% (REF_CP-2E_05)"
)
CP2E_NOTE = (
    "Python checks three of your figures after you answer, with the method's own "
    "`rate_fx_sensitivity.py` (you cannot run it): in T2F.4, Unhedged floating-rate debt and "
    "Unhedged debt percentage, from its Total debt, Gross floating-rate debt and Hedged "
    "floating-rate debt rows; in T2F.5, the Estimated Cash Impact of the `+100 bps cash-interest "
    "impact` row. Write those rows once each with these names, every amount with its currency "
    "and scale (`USD 1,250m`) and the percentage with `%`. A figure that disagrees is sent back "
    "for repair; one whose input is missing is not checked, never read as zero.\n\n"
)
_UNHEDGED = _Where("CP-2E", RATE_FX, UNHEDGED, "T2F.4")
_SHARE = _Where("CP-2E", RATE_FX, SHARE, "T2F.4")
_SHOCK = _Where("CP-2E", RATE_FX, SHOCK, "T2F.5")


def _rows(table: Table, item: int, names: tuple[str, ...], where: str) -> dict[str, list[str]]:
    wanted = {_label(n): n for n in names}
    rows: dict[str, list[str]] = {}
    for row in table[1]:
        name = wanted.get(_label(row[item]))
        if name is not None and name in rows:
            raise _NotChecked(f"{where} has two `{name}` rows")
        if name is not None:
            rows[name] = row
    return rows


@dataclass(frozen=True)
class _Exposure:
    """T2F.4 as the script reads it, and the two figures it states."""

    amounts: dict[str, Amount | str]  # Total, Gross, Hedged, Unhedged rows present (str: unread)
    share: str | None  # the Unhedged debt percentage cell as written
    unit: str


def _exposure(text: str, tables: types.ModuleType) -> _Exposure:
    table = register_table(text, "T2F.4")
    if isinstance(table, str):
        raise _NotChecked(table)
    metric = column(table, "metric", "T2F.4")[0]
    amount, header = column(table, "amount", "T2F.4")
    rows = _rows(table, metric, EXPOSURE_ROWS, "T2F.4")
    amounts = {n: _read(r[amount], header, tables) for n, r in rows.items() if n != SHARE}
    read = [a for a in amounts.values() if isinstance(a, Amount) and a.unit is not None]
    units = {str(a.unit) for a in read}
    if len(units) > 1:
        shown = "; ".join(f"`{a.cell}`" for a in read)
        raise _NotChecked(f"T2F.4's amounts state different currencies or scales: {shown}")
    share = rows[SHARE][amount] if SHARE in rows else None
    return _Exposure(amounts, share, units.pop() if units else "")


def _read(cell: str, header: str, tables: types.ModuleType) -> Amount | str:
    """An amount, or why it is not read: an unread row stops only the checks that use it."""
    try:
        return money(cell, header, tables)
    except _NotChecked as why:
        return str(why)


def _inputs(exposure: _Exposure) -> dict[str, float | None]:
    values = {n: a.value for n, a in exposure.amounts.items() if isinstance(a, Amount)}
    return {
        "total_debt": values.get(TOTAL),
        "gross_floating_rate_debt": values.get(GROSS),
        "hedged_floating_rate_debt": values.get(HEDGED),
    }


def _missing(exposure: _Exposure, names: tuple[str, ...]) -> str | None:
    absent = [n for n in names if n not in exposure.amounts]
    if absent:
        return f"T2F.4 has no {', '.join(f'`{n}`' for n in absent)} row (absent, not zero)"
    unread = [a for n in names if isinstance(a := exposure.amounts[n], str)]
    if unread:
        return unread[0]
    blanks = [n for n in names if _value(exposure, n) is None]
    if blanks:
        return (
            f"T2F.4 states no amount for {', '.join(f'`{n}`' for n in blanks)} (missing, not zero)"
        )
    return None


def _value(exposure: _Exposure, name: str) -> float | None:
    amount = exposure.amounts.get(name)
    return amount.value if isinstance(amount, Amount) else None


def _half(exposure: _Exposure, *names: str) -> float:
    """The summed half-last-place rounding of the named amounts (their displayed precision)."""
    return sum(a.half for n in names if isinstance(a := exposure.amounts.get(n), Amount))


def _unhedged(exposure: _Exposure, result: dict[str, Any], tables: types.ModuleType) -> Outcome:
    stated = exposure.amounts.get(UNHEDGED)
    if isinstance(stated, str):
        return _UNHEDGED("not checked", reason=stated)
    if stated is None or stated.value is None:
        cell = None if stated is None else stated.cell
        return _UNHEDGED("not checked", stated=cell, reason=f"T2F.4 states no {UNHEDGED} figure")
    gap = _missing(exposure, (GROSS, HEDGED))
    if gap is not None:
        return _UNHEDGED("not checked", stated=stated.cell, reason=gap)
    recomputed = result["unhedged_floating_rate_debt"]
    claim = _Claim(
        _UNHEDGED, bare(stated.cell), recomputed, AMOUNT_STEP, exposure.unit, UNHEDGED_FORMULA
    )
    return _judged(replace(claim, slack=_half(exposure, GROSS, HEDGED)), tables)


def _share(exposure: _Exposure, result: dict[str, Any], tables: types.ModuleType) -> Outcome:
    cell = exposure.share
    if cell is None or blank(cell, tables):
        return _SHARE("not checked", stated=cell, reason=f"T2F.4 states no {SHARE} figure")
    gap = _missing(exposure, (TOTAL, GROSS, HEDGED))
    if gap is not None:
        return _SHARE("not checked", stated=cell, reason=gap)
    recomputed = result["unhedged_debt_percentage"]
    if recomputed is None:
        reason = "Total debt is zero, so the script gives no percentage"
        return _SHARE("not checked", stated=cell, reason=reason)
    unhedged = float(result["unhedged_floating_rate_debt"])
    total = float(_value(exposure, TOTAL) or 0.0)
    slack = quotient_slack(unhedged, _half(exposure, GROSS, HEDGED), total, _half(exposure, TOTAL))
    claim = _Claim(_SHARE, cell, recomputed, AMOUNT_STEP, "", SHARE_FORMULA, slack=slack)
    return share(claim, tables)


def _shock_cell(text: str, tables: types.ModuleType) -> Amount:
    table = register_table(text, "T2F.5")
    if isinstance(table, str):
        raise _NotChecked(table)
    item = column(table, "sensitivity", "T2F.5")[0]
    impact, header = column(table, "estimated cash impact", "T2F.5")
    rows = [r for r in table[1] if _label(r[item]).lstrip("+ ") == _label(SHOCK).lstrip("+ ")]
    if len(rows) != 1:
        raise _NotChecked(f"T2F.5 has {len(rows) or 'no'} `{SHOCK}` rows")
    return money(rows[0][impact], header, tables)


def _shock(
    text: str, exposure: _Exposure, result: dict[str, Any], tables: types.ModuleType
) -> Outcome:
    try:
        stated = _shock_cell(text, tables)
    except _NotChecked as why:
        return _SHOCK("not checked", reason=str(why))
    if stated.value is None:
        return _SHOCK("not checked", stated=stated.cell, reason=f"T2F.5 states no {SHOCK} figure")
    gap = _missing(exposure, (GROSS, HEDGED))
    if gap is not None:
        return _SHOCK("not checked", stated=stated.cell, reason=gap)
    if exposure.unit and stated.unit != exposure.unit:
        reason = f"T2F.5's impact is in `{stated.unit}`, T2F.4's amounts in `{exposure.unit}`"
        return _SHOCK("not checked", stated=stated.cell, reason=reason)
    recomputed = result["cash_interest_impact_plus_100bps"]
    # Neither the method nor the note fixes this cell's sign: an increase in cash interest may be
    # written as an outflow. The magnitude is compared and the stated sign kept in the record.
    written = bare(stated.cell)
    size = written.strip("()").lstrip("-+").strip() if stated.value < 0 else written
    slack = 0.01 * _half(exposure, GROSS, HEDGED)  # BPS_SHOCK times the inputs' rounding
    claim = _Claim(_SHOCK, size, recomputed, AMOUNT_STEP, str(stated.unit), SHOCK_FORMULA)
    outcome = _judged(replace(claim, slack=slack), tables)
    if stated.value >= 0:
        return outcome
    sign = "; compared as a magnitude: the cell writes the impact as an outflow (negative)"
    return replace(outcome, stated=written, reason=outcome.reason + sign)


def check(text: str, loaded: Loaded) -> list[Outcome]:
    """Unhedged floating-rate debt and its share of total debt (T2F.4) and the +100 bps
    cash-interest impact (T2F.5), each recomputed by the script from T2F.4's own rows."""
    tables = loaded.tables
    try:
        exposure = _exposure(text, tables)
        result = loaded.script.compute(_inputs(exposure))
    except _NotChecked as why:
        return [w("not checked", reason=str(why)) for w in (_UNHEDGED, _SHARE, _SHOCK)]
    except ValueError as error:  # the script refuses: hedged above gross, a negative amount
        cause = f"the script refused T2F.4's inputs: {error}"
        return [w("not checked", reason=cause) for w in (_UNHEDGED, _SHARE, _SHOCK)]
    return [
        _unhedged(exposure, result, tables),
        _share(exposure, result, tables),
        _shock(text, exposure, result, tables),
    ]


core.register("CP-2E", RATE_FX, check, CP2E_NOTE)
