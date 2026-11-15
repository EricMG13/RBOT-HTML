"""CP-2G's method script, `credit_metrics.py`, run on T2H.4, T2H.5 and T2H.6 (harness:
`deploy_workflow.method_scripts`).

The SKILL gives the script "per-period KPIs on each case and the opening-to-closing roll-forward
with its residual". The registers (SKILL `appendix_contract`) are, per period and case: T2H.4
`EBITDA`, `FCF`; T2H.5 `opening debt/cash`, `issuance`, `repayment`, `interest`, `closing
debt/cash`; T2H.6 `gross/net leverage`, `coverage`, `FCF/debt`, `definition IDs`.

Combined cells. A column whose name joins two figures with `/` (`opening debt/cash`, `closing
debt/cash`, `gross/net leverage`) holds two figures separated by `/`, in the order the name gives
them (`4,500 / 300`, `4.5x / 4.2x`). A cell that is a gap as a whole leaves both missing; one side
that is a gap leaves that side missing; a cell that is not two parts states neither figure.

Units. T2H.4 and T2H.5 have no currency or scale column: each money column's header states it
(`EBITDA (USD m)`), or each cell does (`USD 4,500m`). Every money figure read must be in one
currency and scale, or nothing is compared.

What is checked, per T2H.6 row: gross leverage = closing debt / EBITDA; net leverage = (closing
debt - closing cash) / EBITDA (both against a positive EBITDA, annual periods only: a quarter's
EBITDA is not a leverage denominator); coverage = EBITDA / |interest|, compared as a disagreement
only when the row's definition names EBITDA over interest (the method allows interest or
fixed-charge coverage); FCF/debt = FCF / closing debt (annual only). Per T2H.5 row: the opening
debt and cash equal the same case's prior closing (the row before it in T2H.5, compared only
when both are annual periods whose years are consecutive), a disagreement otherwise; and closing
debt = opening debt + issuance - repayment (each as its size), agreed when it rolls, otherwise not
checked with the residual, because the method allows a logged residual and T2H.5 has no column for
other debt movements (PIK, FX, accretion). The cash roll-forward is not checked: dividends and
other cash uses are not columns.
"""

import re
import types
from dataclasses import dataclass, replace

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
    _plain,
    _Where,
    bare,
    blank,
    column,
    money,
    register_table,
    share,
)

CREDIT_METRICS = ARCHIVE + "skills/cp-1-canonical-data-foundation/scripts/credit_metrics.py"
# Each register's money columns (SKILL appendix_contract) -> the field(s) each holds, in order.
T2H4_MONEY = {"EBITDA": ("ebitda",), "FCF": ("fcf",)}
T2H5_MONEY = {
    "opening debt/cash": ("opening_debt", "opening_cash"),
    "issuance": ("issuance",),
    "repayment": ("repayment",),
    "interest": ("interest",),
    "closing debt/cash": ("closing_debt", "closing_cash"),
}
RATIO_STEP = 1e-9  # the script does not round its ratios
NOT_MEANINGFUL = ("n.m.", "nm", "not meaningful", "not calculable")
_PART = re.compile(r"\s*/\s*")
_NOT_ANNUAL = re.compile(r"\b(?:q[1-4]|h[12]|[1-9]m|quarter|half|month|ytd)\b")
_EBITDA_OVER_INTEREST = re.compile(r"ebitda\s*(?:/|to|over)\s*(?:\(?cash\s+|net\s+)?interest")
CP2G_NOTE = (
    "Python checks figures in T2H.5 and T2H.6 after you answer, with the method's own "
    "`credit_metrics.py` (you cannot run it): per period and case, gross and net leverage "
    "(closing debt, and closing debt less closing cash, over T2H.4 EBITDA), coverage (EBITDA / "
    "cash interest), FCF/debt, and that each opening debt and cash is the case's prior closing. "
    "So give T2H.4, T2H.5 and T2H.6 the method's columns with the same period and case labels, "
    "put the currency and scale in each money column's header (`EBITDA (USD m)`), and write each "
    "combined cell as two figures in its column's order (`4,500 / 300`, `4.5x / 4.2x`). A figure "
    "that disagrees is sent back for repair; one whose input is missing is not checked, never "
    "read as zero.\n\n"
)

Key = tuple[str, str]  # (period, case) as labelled
Field = Amount | str  # a money figure as read, or why its cell is not read


@dataclass(frozen=True)
class _Kpi:
    """One T2H.6 figure: the script's KPI, its inputs, and the formula in words."""

    name: str
    kpi: str
    inputs: tuple[str, ...]
    formula: str
    annual: bool  # a leverage or FCF/debt figure needs an annual period


KPIS = (
    _Kpi(
        "Gross leverage",
        "total_leverage",
        ("closing_debt", "ebitda"),
        "Gross leverage = closing debt (T2H.5) / EBITDA (T2H.4), EBITDA positive",
        True,
    ),
    _Kpi(
        "Net leverage",
        "net_leverage",
        ("closing_debt", "closing_cash", "ebitda"),
        "Net leverage = (closing debt - closing cash) (T2H.5) / EBITDA (T2H.4), EBITDA positive",
        True,
    ),
    _Kpi(
        "Coverage",
        "interest_coverage",
        ("ebitda", "interest"),
        "Coverage = EBITDA (T2H.4) / |interest| (T2H.5), interest not zero",
        False,
    ),
    _Kpi(
        "FCF/debt",
        "fcf_percent_debt",
        ("fcf", "closing_debt"),
        "FCF/debt = FCF (T2H.4) / closing debt (T2H.5)",
        True,
    ),
)


def _where(register: str, figure_name: str, key: Key) -> _Where:
    return _Where("CP-2G", CREDIT_METRICS, f"{figure_name} ({key[0]}, {key[1]})", register)


def _split(cell: str, tables: types.ModuleType) -> tuple[str, str] | None:
    """A combined cell's two parts in order, a whole gap as two gaps, or None (not two parts)."""
    if blank(cell, tables):
        return cell, cell
    parts = _PART.split(re.sub(r"(?i)\bn/a\b", "na", _plain(cell)))
    return (parts[0], parts[1]) if len(parts) == 2 else None


def _money(cell: str, header: str, tables: types.ModuleType) -> Field:
    try:
        return money(cell, header, tables)
    except _NotChecked as why:
        return str(why)


def _fields(
    row: list[str], spec: dict[str, tuple[int, str]], tables: types.ModuleType
) -> dict[str, Field]:
    out: dict[str, Field] = {}
    for name, (index, header) in spec.items():
        keys = (T2H4_MONEY | T2H5_MONEY)[name]
        if len(keys) == 1:
            out[keys[0]] = _money(row[index], header, tables)
            continue
        parts = _split(row[index], tables)
        if parts is None:
            why = f"`{row[index]}` is not two figures as its column `{name}` names them"
            out |= dict.fromkeys(keys, why)
        else:
            out |= {k: _money(p, header, tables) for k, p in zip(keys, parts, strict=True)}
    return out


def _keyed(table: Table, where: str) -> dict[Key, list[str]]:
    period = column(table, "period", where)[0]
    case = column(table, "case", where)[0]
    rows: dict[Key, list[str]] = {}
    for row in table[1]:
        key = (_plain(row[period]), _plain(row[case]))
        if (_label(key[0]), _label(key[1])) in {(_label(a), _label(b)) for a, b in rows}:
            raise _NotChecked(f"{where} has two rows for {key[0]}, {key[1]}")
        rows[key] = row
    return rows


@dataclass(frozen=True)
class _Model:
    """T2H.4 and T2H.5 as the script reads them, by (period, case)."""

    fields: dict[Key, dict[str, Field]]
    order: dict[str, list[Key]]  # case -> its T2H.5 rows in order
    unit: str


def _model(text: str, tables: types.ModuleType) -> _Model:
    fields: dict[Key, dict[str, Field]] = {}
    order: dict[str, list[Key]] = {}
    for ident, spec in (("T2H.4", T2H4_MONEY), ("T2H.5", T2H5_MONEY)):
        table = register_table(text, ident)
        if isinstance(table, str):
            raise _NotChecked(table)
        rows = _keyed(table, ident)
        cols = {name: column(table, name, ident) for name in spec}
        for key, row in rows.items():
            fields.setdefault(_norm(key), {}).update(_fields(row, cols, tables))
            if ident == "T2H.5":
                order.setdefault(_label(key[1]), []).append(key)
    units = {f.unit for row in fields.values() for f in row.values() if isinstance(f, Amount)}
    units.discard(None)
    if len(units) > 1:
        raise _NotChecked(
            f"T2H.4 and T2H.5 state money in different units: {sorted(map(str, units))}"
        )
    return _Model(fields, order, str(units.pop()) if units else "")


def _norm(key: Key) -> Key:
    return _label(key[0]), _label(key[1])


def _inputs(model: _Model, key: Key, names: tuple[str, ...]) -> dict[str, float] | str:
    """The named inputs of one period and case, or why one is not read (missing is not zero)."""
    row = model.fields.get(_norm(key))
    if row is None:
        return f"T2H.4 and T2H.5 have no row for {key[0]}, {key[1]}"
    values: dict[str, float] = {}
    for name in names:
        field = row.get(name)
        what = f"{name.replace('_', ' ')} for {key[0]}, {key[1]}"
        if field is None:
            return f"{_register_of(name)} has no {what}"
        if isinstance(field, str):
            return field
        if field.value is None:
            return f"{_register_of(name)} states no {what} (missing, not zero)"
        values[name] = field.value
    return values


def _register_of(name: str) -> str:
    return "T2H.4" if name in ("ebitda", "fcf") else "T2H.5"


# --- T2H.6: the KPIs ----------------------------------------------------------------------------


def _stated_kpis(
    row: list[str], cols: dict[str, int], tables: types.ModuleType
) -> dict[str, str | None]:
    pair = _split(row[cols["gross/net leverage"]], tables)
    gross, net = pair if pair is not None else (None, None)
    return {
        "Gross leverage": gross,
        "Net leverage": net,
        "Coverage": row[cols["coverage"]],
        "FCF/debt": row[cols["FCF/debt"]],
    }


def _kpi(kpi: _Kpi, key: Key, stated: str | None, model: _Model, loaded: Loaded) -> Outcome:
    where = _where("T2H.6", kpi.name, key)
    if stated is None:
        return where("not checked", reason="T2H.6's `gross/net leverage` cell is not two figures")
    said_none = _label(stated) in NOT_MEANINGFUL
    if blank(stated, loaded.tables) and not said_none:
        return where("not checked", stated=stated, reason=f"T2H.6 states no {kpi.name} figure")
    if kpi.annual and _NOT_ANNUAL.search(_label(key[0])):
        reason = f"{key[0]} is not an annual period: its EBITDA or FCF is not a full year's"
        return where("not checked", stated=stated, reason=reason)
    inputs = _inputs(model, key, kpi.inputs)
    if isinstance(inputs, str):
        return where("not checked", stated=stated, reason=inputs)
    names = {"closing_debt": "total_debt", "closing_cash": "cash_and_equivalents"}
    names |= {"interest": "cash_interest_paid"}
    value = loaded.script.compute_kpis({names.get(k, k): v for k, v in inputs.items()})[kpi.kpi]
    if value is None or said_none:
        agreed = value is None and said_none
        label = "Not Calculable" if value is None else None
        return where(
            "agreed" if agreed else "disagreed",
            stated=stated,
            recomputed=value,
            recomputed_label=label,
            reason=kpi.formula,
        )
    return _ratio(kpi, where, stated, value, loaded.tables)


def _coverage_defined(outcome: Outcome, definition: str) -> Outcome:
    """A coverage that is not EBITDA / interest disagrees only when the row says that is its
    definition; otherwise it may be another coverage the method allows."""
    if outcome.status != "disagreed" or _EBITDA_OVER_INTEREST.search(_label(definition)):
        return outcome
    reason = (
        "the stated coverage is not EBITDA / |interest| and the row's definition does not say it "
        "is; it may be fixed-charge or EBITDA-less-capex coverage, which T2H.4 and T2H.5 cannot "
        "recompute"
    )
    return replace(outcome, status="not checked", reason=reason)


def _ratio(
    kpi: _Kpi, where: _Where, stated: str, value: float, tables: types.ModuleType
) -> Outcome:
    if kpi.name == "FCF/debt":
        return share(where, stated, value, kpi.formula, tables)
    multiple = re.sub(r"(?i)\s*x(?=\)?$)", "", _plain(stated))  # `4.5x` is 4.5, unit x
    claim = _Claim(where, multiple, value, RATIO_STEP, "x", kpi.formula)
    return _judged(claim, tables)


def _kpis(text: str, model: _Model, loaded: Loaded) -> list[Outcome]:
    table = register_table(text, "T2H.6")
    if isinstance(table, str):
        return [_Where("CP-2G", CREDIT_METRICS, "T2H.6", "T2H.6")("not checked", reason=table)]
    rows = _keyed(table, "T2H.6")
    names = ("gross/net leverage", "coverage", "FCF/debt", "definition IDs")
    cols = {name: column(table, name, "T2H.6")[0] for name in names}
    out = []
    for key, row in rows.items():
        stated = _stated_kpis(row, cols, loaded.tables)
        definition = f"{row[cols['definition IDs']]} {table[0][cols['coverage']]}"
        outcomes = [_kpi(k, key, stated[k.name], model, loaded) for k in KPIS]
        out += [
            _coverage_defined(o, definition) if o.figure.startswith("Coverage") else o
            for o in outcomes
        ]
    return out


# --- T2H.5: the roll-forward --------------------------------------------------------------------

OPENING_FORMULA = (
    "Opening {what} = the same case's closing {what} in the period before it in T2H.5 (CP-2G: "
    "'Reconcile opening balances to the prior closing period')"
)
CLOSING_FORMULA = "Closing debt = opening debt + issuance - repayment (T2H.5)"


def _year(period: str) -> int | None:
    """The fiscal year an annual period names (`FY2026`, `2026E`, `FY26`); None for any other."""
    label = _label(period)
    if _NOT_ANNUAL.search(label):
        return None
    found = re.search(r"(?<!\d)(\d{4})(?!\d)|\bfy\s*(\d{2})(?!\d)", label)
    if found is None:
        return None
    return int(found[1]) if found[1] else 2000 + int(found[2])


def _follows(period: str, prior: str) -> bool:
    """Whether ``period`` is the annual period right after ``prior`` (a row before it in T2H.5
    is not taken as its prior period on order alone)."""
    year, before = _year(period), _year(prior)
    return year is not None and before is not None and year == before + 1


def _opening(what: str, key: Key, prior: Key | None, model: _Model, loaded: Loaded) -> Outcome:
    where = _where("T2H.5", f"Opening {what}", key)
    field = model.fields[_norm(key)].get(f"opening_{what}")
    if not isinstance(field, Amount) or field.value is None:
        reason = field if isinstance(field, str) else f"T2H.5 states no opening {what}"
        return where("not checked", reason=reason)
    if prior is None or not _follows(key[0], prior[0]):
        reason = f"T2H.5 shows no year that {key[0]} follows in case {key[1]}"
        return where("not checked", stated=bare(field.cell), reason=reason)
    inputs = _inputs(model, prior, (f"closing_{what}",))
    if isinstance(inputs, str):
        return where("not checked", stated=bare(field.cell), reason=inputs)
    rolled = loaded.script.roll_forward(inputs[f"closing_{what}"], [], field.value)
    formula = OPENING_FORMULA.format(what=what)
    claim = _Claim(
        where, bare(field.cell), rolled["expected_closing"], AMOUNT_STEP, model.unit, formula
    )
    return _judged(claim, loaded.tables)


def _closing(key: Key, model: _Model, loaded: Loaded) -> Outcome:
    where = _where("T2H.5", "Closing debt", key)
    names = ("opening_debt", "issuance", "repayment", "closing_debt")
    inputs = _inputs(model, key, names)
    if isinstance(inputs, str):
        return where("not checked", reason=inputs)
    flows = [abs(inputs["issuance"]), -abs(inputs["repayment"])]
    rolled = loaded.script.roll_forward(inputs["opening_debt"], flows, inputs["closing_debt"])
    stated = bare(_cell(model, key, "closing_debt"))
    claim = _Claim(
        where, stated, rolled["expected_closing"], AMOUNT_STEP, model.unit, CLOSING_FORMULA
    )
    outcome = _judged(claim, loaded.tables)
    if outcome.status == "disagreed":
        reason = (
            f"a residual of {rolled['residual']:g}: the method allows a residual it logs, and "
            "T2H.5 has no column for other debt movements (PIK, FX, accretion)"
        )
        return replace(outcome, status="not checked", reason=reason)
    return outcome


def _cell(model: _Model, key: Key, name: str) -> str:
    field = model.fields[_norm(key)][name]
    return field.cell if isinstance(field, Amount) else field


def _rolls(model: _Model, loaded: Loaded) -> list[Outcome]:
    out = []
    for keys in model.order.values():
        for i, key in enumerate(keys):
            prior = keys[i - 1] if i else None
            out += [
                _opening("debt", key, prior, model, loaded),
                _opening("cash", key, prior, model, loaded),
                _closing(key, model, loaded),
            ]
    return out


def check(text: str, loaded: Loaded) -> list[Outcome]:
    """Leverage, coverage and FCF/debt per period and case (T2H.6) and the debt roll-forward
    (T2H.5), each recomputed by the script from T2H.4 and T2H.5."""
    try:
        model = _model(text, loaded.tables)
        return [*_kpis(text, model, loaded), *_rolls(model, loaded)]
    except _NotChecked as why:
        return [
            _Where("CP-2G", CREDIT_METRICS, "all", "T2H.4-T2H.6")("not checked", reason=str(why))
        ]


core.register("CP-2G", CREDIT_METRICS, check, CP2G_NOTE)
