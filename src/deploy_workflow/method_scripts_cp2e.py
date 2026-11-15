"""CP-2E's method script, `rate_fx_sensitivity.py`, run on T2F.4 and T2F.5 (harness:
`deploy_workflow.method_scripts`).

The method's step 4 (REF_CP-2E_04) makes T2F.4 carry the rows Total debt, Gross floating-rate debt,
Hedged floating-rate debt, Unhedged floating-rate debt and Unhedged debt percentage; step 5
(REF_CP-2E_05) makes T2F.5 carry the +100 bps cash-interest impact. T2F.4 has no currency or scale
column, so each amount states its own (`USD 1,250m`), or the amount column's header does
(`Amount (USD m)`); a cell's own unit wins. FX and cost sensitivities are not checked: their net
exposure and adverse move are free text in T2F.6 and T2F.7, not columns.
"""

import re
import types
from dataclasses import dataclass
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    AMOUNT_STEP,
    ARCHIVE,
    Loaded,
    Outcome,
    Table,
    _Claim,
    _judged,
    _label,
    _NotChecked,
    _plain,
    _Where,
    blank,
    currency_of,
    figure,
    register_table,
    scale_of,
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
_CODE = re.compile(r"(?<![A-Za-z])[A-Z]{3}(?![A-Za-z])|US\$|[€£$]")
_SCALE_WORD = re.compile(
    r"(?<=[\d\s)])(?:m|mn|mm|bn|k|million|millions|billion|billions|thousand|thousands)\.?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _Amount:
    """A money cell as read: its figure (None when it states none) and its unit."""

    value: float | None
    unit: str | None  # `<currency> <scale>`; None for a cell that states no figure
    cell: str


def _column(table: Table, name: str, where: str) -> tuple[int, str]:
    """The column named ``name`` (its header may add a unit: `Amount (USD m)`) and the header."""
    found = [i for i, c in enumerate(table[0]) if re.fullmatch(rf"{name}\b.*", _label(c))]
    if len(found) != 1:
        raise _NotChecked(f"{where} has {len(found) or 'no'} `{name}` column{'s' * (found != [])}")
    return found[0], table[0][found[0]]


def _amount(cell: str, header: str, tables: types.ModuleType) -> _Amount:
    """A money cell: its unit is the cell's own currency and scale, else the column header's."""
    if blank(cell, tables):
        return _Amount(None, None, cell)
    text = _plain(cell)
    own = (currency_of(text), scale_of(text))
    head = (currency_of(header), scale_of(header))
    currency, scale = own[0] or head[0], own[1] or head[1]
    if currency is None or scale is None:
        raise _NotChecked(f"`{cell}` states no currency and scale, nor does its column")
    read = figure(_bare(cell), tables)
    if isinstance(read, str):
        raise _NotChecked(read)
    return _Amount(read[0], f"{currency} {scale}", cell)


def _bare(cell: str) -> str:
    """A money cell's figure without its currency and scale (`USD 1,250m` -> `1,250`)."""
    return _SCALE_WORD.sub("", _CODE.sub("", _plain(cell))).strip()


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

    amounts: dict[str, _Amount]  # Total, Gross, Hedged, Unhedged rows that are present
    share: str | None  # the Unhedged debt percentage cell as written
    unit: str


def _exposure(text: str, tables: types.ModuleType) -> _Exposure:
    table = register_table(text, "T2F.4")
    if isinstance(table, str):
        raise _NotChecked(table)
    metric = _column(table, "metric", "T2F.4")[0]
    amount, header = _column(table, "amount", "T2F.4")
    rows = _rows(table, metric, EXPOSURE_ROWS, "T2F.4")
    amounts = {n: _amount(r[amount], header, tables) for n, r in rows.items() if n != SHARE}
    units = {a.unit for a in amounts.values() if a.unit is not None}
    if len(units) > 1:
        shown = "; ".join(f"`{a.cell}`" for a in amounts.values() if a.unit is not None)
        raise _NotChecked(f"T2F.4's amounts state different currencies or scales: {shown}")
    share = rows[SHARE][amount] if SHARE in rows else None
    return _Exposure(amounts, share, units.pop() if units else "")


def _inputs(exposure: _Exposure) -> dict[str, float | None]:
    values = {n: a.value for n, a in exposure.amounts.items()}
    return {
        "total_debt": values.get(TOTAL),
        "gross_floating_rate_debt": values.get(GROSS),
        "hedged_floating_rate_debt": values.get(HEDGED),
    }


def _missing(exposure: _Exposure, names: tuple[str, ...]) -> str | None:
    absent = [n for n in names if n not in exposure.amounts]
    if absent:
        return f"T2F.4 has no {', '.join(f'`{n}`' for n in absent)} row (absent, not zero)"
    blanks = [n for n in names if exposure.amounts[n].value is None]
    if blanks:
        return (
            f"T2F.4 states no amount for {', '.join(f'`{n}`' for n in blanks)} (missing, not zero)"
        )
    return None


def _unhedged(exposure: _Exposure, result: dict[str, Any], tables: types.ModuleType) -> Outcome:
    stated = exposure.amounts.get(UNHEDGED)
    if stated is None or stated.value is None:
        cell = None if stated is None else stated.cell
        return _UNHEDGED("not checked", stated=cell, reason=f"T2F.4 states no {UNHEDGED} figure")
    gap = _missing(exposure, (GROSS, HEDGED))
    if gap is not None:
        return _UNHEDGED("not checked", stated=stated.cell, reason=gap)
    recomputed = result["unhedged_floating_rate_debt"]
    claim = _Claim(
        _UNHEDGED, _bare(stated.cell), recomputed, AMOUNT_STEP, exposure.unit, UNHEDGED_FORMULA
    )
    return _judged(claim, tables)


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
    return share(_SHARE, cell, recomputed, SHARE_FORMULA, tables)


def _shock_cell(text: str, tables: types.ModuleType) -> _Amount:
    table = register_table(text, "T2F.5")
    if isinstance(table, str):
        raise _NotChecked(table)
    item = _column(table, "sensitivity", "T2F.5")[0]
    impact, header = _column(table, "estimated cash impact", "T2F.5")
    rows = [r for r in table[1] if _label(r[item]).lstrip("+ ") == _label(SHOCK).lstrip("+ ")]
    if len(rows) != 1:
        raise _NotChecked(f"T2F.5 has {len(rows) or 'no'} `{SHOCK}` rows")
    return _amount(rows[0][impact], header, tables)


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
    claim = _Claim(
        _SHOCK, _bare(stated.cell), recomputed, AMOUNT_STEP, str(stated.unit), SHOCK_FORMULA
    )
    return _judged(claim, tables)


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
