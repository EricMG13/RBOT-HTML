"""CP-1's method script, `credit_metrics.py`, run on T4.8 and T4.9 (harness:
`deploy_workflow.method_scripts`).

How the work divides with `owners.cpos_cp1_check`, which already checks CP-1 at acceptance: that
module recomputes the six fixed T4.9 rows (`Total debt / EBITDA` and its five twins), binding each
operand to the figure it must be (gross or net debt from `Net debt data`, EBITDA and cash interest
from the statements) and printing to two places. This check leaves those six rows to it and takes
what it does not cover:

- T4.9 rows with a free `Metric Name` whose `Formula` is a quotient: `Calculated Value` against the
  script's `ratio` of the row's own `Numerator Value` and `Denominator Value`, read as a ratio or a
  percentage of it, or as the script's `growth` (n / d - 1) for a change, in either form. Only the
  arithmetic is bound: which debt or EBITDA the operands are is the row's own statement (a free name
  fixes no operand), so a ratio on principal where the method wants carrying value (the retained
  TDG figures: 25,068 / 3,813 = 6.57, carrying 24,880 gives 6.53) agrees when its own division is
  right. A row whose formula is not a quotient (a sum, a difference) is not checked.
- T4.8 rows whose `Derived Period Type` is LTM: `Derived Value` against the script's
  `derive_periods` (latest full year + current stub - prior-year stub). T4.8 has no currency or
  scale column, so a row is compared only when its figures state one, in the cells or the column
  headers, and the same one; otherwise it is not checked. Other derived types (Q2, Q3, Q4, YTD) are
  not checked: T4.8's three component columns do not say which periods they hold.

CP-1 is sent no note: the `earnings_update` instructions are within 93 characters of their
ceiling (ruling 2026-11-15-method-script-checks.md).
"""

import re
import types

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    ARCHIVE,
    Amount,
    Loaded,
    Outcome,
    Status,
    _Claim,
    _columns,
    _judged,
    _label,
    _NotChecked,
    _plain,
    _Where,
    bare,
    blank,
    column,
    compare,
    currency_of,
    figure,
    money,
    register_table,
)

CREDIT_METRICS = ARCHIVE + "skills/cp-1-canonical-data-foundation/scripts/credit_metrics.py"
# The fixed rows `owners.cpos_cp1_check.METRICS` checks (REF_CP-1_09); this check leaves them to it.
FIXED_ROWS = (
    "Total debt / EBITDA",
    "Net debt / EBITDA",
    "EBITDA / cash interest",
    "Total debt / adjusted EBITDA",
    "Net debt / adjusted EBITDA",
    "Adjusted EBITDA / cash interest",
)
T49_COLUMNS = (
    "Metric Name",
    "Formula",
    "Numerator Value",
    "Denominator Value",
    "Period",
    "Currency",
    "Unit",
    "Calculated Value",
)
T48_MONEY = ("Full-Year Component", "Current Stub", "Prior-Year Stub", "Derived Value")
RATIO_STEP = 1e-9  # the script does not round a ratio
LTM_STEP = 1e-6
RATIO_FORMULA = (
    "Calculated Value = Numerator Value / Denominator Value (the script's ratio), or that x 100 "
    "for a percentage; for a change, Numerator / Denominator - 1 (the script's growth)"
)
LTM_FORMULA = (
    "LTM = Full-Year Component + Current Stub - Prior-Year Stub (REF_CP-1_08; the script's "
    "derive_periods)"
)
_QUOTIENT = re.compile(r"/|÷|\bdivided by\b|\bover\b|\bratio\b|\bmargin\b|\bconversion\b")


def _where(register: str, figure_name: str) -> _Where:
    return _Where("CP-1", CREDIT_METRICS, figure_name, register)


# --- T4.9: the free-name rows -------------------------------------------------------------------


def _forms(n: float, d: float, script: types.ModuleType) -> list[tuple[str, float]]:
    """The script's readings of one quotient: ratio and growth, each as stated or in percent."""
    ratio = script.ratio(n, d)
    change = script.growth(n, d)
    out = []
    for name, value in (("ratio", ratio), ("growth", change)):
        if value is not None:
            out += [(name, value), (f"{name} in percent", value * 100)]
    return out


def _operands(
    row: list[str], cols: dict[str, int], tables: types.ModuleType
) -> tuple[float, float]:
    values = []
    for name in ("Numerator Value", "Denominator Value"):
        cell = row[cols[name]]
        if blank(cell, tables):
            raise _NotChecked(f"T4.9 states no {name} (missing, not zero)")
        read = figure(cell, tables)
        if isinstance(read, str):
            raise _NotChecked(f"{name}: {read}")
        values.append(read[0])
    return values[0], values[1]


def _free_row(row: list[str], cols: dict[str, int], loaded: Loaded) -> Outcome:
    name, period = _plain(row[cols["Metric Name"]]), _plain(row[cols["Period"]])
    where = _where("T4.9", f"{name} ({period})")
    stated = row[cols["Calculated Value"]]
    try:
        if not _QUOTIENT.search(_label(row[cols["Formula"]])):
            raise _NotChecked(f"its Formula `{row[cols['Formula']]}` is not a quotient")
        if blank(row[cols["Currency"]], loaded.tables) or blank(row[cols["Unit"]], loaded.tables):
            raise _NotChecked("T4.9 states no Currency or Unit for its operands")
        n, d = _operands(row, cols, loaded.tables)
    except _NotChecked as why:
        return where("not checked", stated=stated, reason=str(why))
    return _judged_forms(where, stated, n, d, loaded)


def _judged_forms(where: _Where, stated: str, n: float, d: float, loaded: Loaded) -> Outcome:
    said_none = _label(stated).startswith("not calculable")
    if blank(stated, loaded.tables) and not said_none:
        return where("not checked", stated=stated, reason="T4.9 states no Calculated Value")
    forms = _forms(n, d, loaded.script)
    if said_none or not forms:
        agreed = said_none and loaded.script.ratio(n, d) is None
        status: Status = "agreed" if agreed else "disagreed"
        label = "Not Calculable" if not forms else None
        first = forms[0][1] if forms else None
        return where(
            status, stated=stated, recomputed=first, recomputed_label=label, reason=RATIO_FORMULA
        )
    read = figure(re.sub(r"(?i)\s*(?:x|%)(?=\)?$)", "", _plain(stated)), loaded.tables)
    if isinstance(read, str):
        return where("not checked", stated=stated, reason=read)
    for form, value in forms:
        close, tolerance = compare(read, value, RATIO_STEP)
        if close:
            reason = f"{RATIO_FORMULA}; agrees as the {form}"
            return where(
                "agreed", stated=stated, recomputed=value, tolerance=tolerance, reason=reason
            )
    form, nearest = min(forms, key=lambda f: abs(f[1] - read[0]))  # the form it was meant in
    tolerance = compare(read, nearest, RATIO_STEP)[1]
    return where(
        "disagreed",
        stated=stated,
        recomputed=nearest,
        tolerance=tolerance,
        reason=f"{RATIO_FORMULA}; nearest as the {form}",
    )


def _t49(text: str, loaded: Loaded) -> list[Outcome]:
    table = register_table(text, "T4.9")
    cols = table if isinstance(table, str) else _columns(table, T49_COLUMNS, "T4.9")
    if isinstance(table, str) or isinstance(cols, str):
        return [_where("T4.9", "T4.9")("not checked", reason=str(cols))]
    fixed = {_label(n) for n in FIXED_ROWS}
    rows = [r for r in table[1] if _label(r[cols["Metric Name"]]) not in fixed]
    return [_free_row(r, cols, loaded) for r in rows]


# --- T4.8: LTM ----------------------------------------------------------------------------------


def _ltm_row(row: list[str], cols: dict[str, tuple[int, str]], loaded: Loaded) -> Outcome:
    name = _plain(row[cols["Metric Name"][0]])
    where = _where("T4.8", f"LTM: {name}")
    stated = row[cols["Derived Value"][0]]
    try:
        amounts = {c: _amount(row, cols[c], loaded.tables) for c in T48_MONEY}
    except _NotChecked as why:
        return where("not checked", stated=stated, reason=str(why))
    units = {a.unit for a in amounts.values() if a.unit is not None}
    if len(units) != 1:
        return where("not checked", stated=stated, reason=_unit_reason(units))
    if amounts["Derived Value"].value is None:
        return where("not checked", stated=stated, reason="T4.8 states no Derived Value")
    parts = {"FY": "Full-Year Component", "YTD": "Current Stub", "prior_YTD": "Prior-Year Stub"}
    values, derived = loaded.script.derive_periods({k: amounts[c].value for k, c in parts.items()})
    if values.get("LTM") is None:
        missing = ", ".join(parts[k] for k in derived["LTM"]["missing"])
        return where(
            "not checked", stated=stated, reason=f"T4.8 states no {missing} (missing, not zero)"
        )
    unit = units.pop()
    claim = _Claim(where, bare(stated), values["LTM"], LTM_STEP, unit, LTM_FORMULA)
    return _judged(claim, loaded.tables)


def _amount(row: list[str], col: tuple[int, str], tables: types.ModuleType) -> Amount:
    """A T4.8 figure with the unit its cell or column header states; a figure stating none is
    not read (T4.8 has no currency or scale column)."""
    cell = row[col[0]]
    if blank(cell, tables):
        return Amount(None, None, cell)
    if currency_of(cell) is None and currency_of(col[1]) is None:
        raise _NotChecked("T4.8 states no currency or scale for this row's figures")
    return money(cell, col[1], tables)


def _unit_reason(units: set[str]) -> str:
    if not units:
        return "T4.8 states no figure for this row"
    return f"this row's figures state different units: {sorted(units)}"


def _t48(text: str, loaded: Loaded) -> list[Outcome]:
    table = register_table(text, "T4.8")
    if isinstance(table, str):
        return [_where("T4.8", "T4.8")("not checked", reason=table)]
    try:
        cols = {
            c: column(table, c, "T4.8") for c in ("Metric Name", "Derived Period Type", *T48_MONEY)
        }
    except _NotChecked as why:
        return [_where("T4.8", "T4.8")("not checked", reason=str(why))]
    ltm = re.compile(r"\bltm\b|last twelve months")
    rows = [r for r in table[1] if ltm.search(_label(r[cols["Derived Period Type"][0]]))]
    return [_ltm_row(r, cols, loaded) for r in rows]


def check(text: str, loaded: Loaded) -> list[Outcome]:
    """T4.8's LTM figures and T4.9's free-name quotients, each recomputed by the script."""
    return [*_t48(text, loaded), *_t49(text, loaded)]


core.register("CP-1", CREDIT_METRICS, check, None)  # no note: the earnings_update ceiling
