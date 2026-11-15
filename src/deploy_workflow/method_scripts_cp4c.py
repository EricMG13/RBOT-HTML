"""CP-4C's method script, `recovery_waterfall.py`, run on T4E.5 and T4E.6 (harness:
`deploy_workflow.method_scripts`).

CP-4C's SKILL names the script as the owner of "the claims waterfall, per-class recovery
percentages, the fulcrum, and the low/base/high sensitivity", claims "consumed in the order you
supply". T4E.5 is that waterfall, one row per step: `scenario; entity; available value; priority
claim; allocation; residual; currency and scale; legal evidence ID`. Each row is checked by itself:
the script allocates the row's available value to its one claim (the lesser of the two) and leaves
the rest, so Allocation and Residual are recomputed from the row's own Available value and
Priority claim. A row is its own step, so value by entity, a new collateral pool and a deficiency
claim at a lower rank are all readable as the method allows them ("Allocate residual value by
entity and class"), without the check assuming one pool.

The fulcrum (T4E.6 `fulcrum class/range`) is "the class receiving the marginal reorganised
equity/value after senior claims": the script's first claim, in order, that recovers more than
nothing and less than in full. It is recomputed only for a scenario whose T4E.5 rows are one entity
and one chain (each row's available value is the residual of the row before), so the script's one
pool is the handoff's; a fulcrum stated as a range is not compared.

Not checked by design: T4E.7 recoveries (the method separates cash, reinstated debt, new debt,
equity and warrants and discounts them for timing, which the script does not), the chart tables
`recovery by class` (Recovery % "as the owner states it", which may be on another basis) and
`value allocation` (the launcher already reconciles its steps), and T4E.3's enterprise value (its
multiple or discount is free text).
"""

import re
import types
from dataclasses import dataclass, replace
from itertools import pairwise
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    AMOUNT_STEP,
    Loaded,
    Outcome,
    Status,
    Table,
    Upstream,
    _Claim,
    _judged,
    _label,
    _NotChecked,
    _plain,
    _Where,
    column,
    money,
    register_table,
)
from deploy_workflow.method_scripts_cp3 import NO_FULCRUM, RECOVERY, _named

COLUMNS = ("scenario", "entity", "available value", "priority claim", "allocation", "residual")
UNIT = "currency and scale"
ALLOCATION_FORMULA = (
    "Allocation = the lesser of the row's priority claim and its available value; Residual = "
    "available value - allocation (recovery_waterfall.py, one claim per T4E.5 step)"
)
FULCRUM_FORMULA = (
    "The fulcrum is the first claim, in T4E.5's row order, that recovers more than nothing and "
    "less than in full; a boundary or zero recovery is no fulcrum (recovery_waterfall.py)"
)
_NOTE = re.compile(r"^(?P<figure>.*?)\s*\((?P<note>[^()]*[A-Za-z][^()]*)\)\s*$")
CP4C_NOTE = (
    "Python checks T4E.5 and T4E.6 after you answer, with the method's own "
    "`recovery_waterfall.py` (you cannot run it). Each T4E.5 row is one step of the waterfall: "
    "its Allocation must be the lesser of its Priority claim and its Available value, and its "
    "Residual the Available value less the Allocation. So write Priority claim as `<class>: "
    "<amount>`, and Available value, Allocation and Residual as figures in the row's currency "
    "and scale. Claims that rank equally share one row (`TLB: 900; RCF: 600`); a secured claim "
    "limited by its collateral is two rows, the secured part and the deficiency at its own "
    "rank; another entity's or pool's value starts its own rows. An allocation the governing "
    "evidence sets otherwise is written with its reason after the figure (`300 (settlement)`) "
    "and is then not checked. Where a scenario's rows are one entity and one chain, its T4E.6 "
    "fulcrum is recomputed too. A figure that disagrees is sent back for repair; one whose "
    "input is missing is not checked, never read as zero."
    "\n\n"
)


def _where(figure_name: str) -> _Where:
    return _Where("CP-4C", RECOVERY, figure_name, "T4E.5")


@dataclass(frozen=True)
class _Step:
    """One T4E.5 row as the script reads it."""

    scenario: str
    entity: str
    name: str  # the class the Priority claim cell names
    available: core.Amount
    claim: core.Amount
    allocation: str  # the cells as written
    residual: str
    noted: str  # the reason written after the allocation figure, if any
    source: str  # where a cell that states no unit takes it from (the row's, else the header's)


def _columns(table: Table) -> dict[str, tuple[int, str]]:
    cols = {name: column(table, name, "T4E.5") for name in COLUMNS}
    found = [i for i, c in enumerate(table[0]) if _label(c) == UNIT]
    cols[UNIT] = (found[0], table[0][found[0]]) if len(found) == 1 else (-1, "")
    return cols


def _unit_source(row: list[str], cols: dict[str, tuple[int, str]], name: str) -> str:
    """Where a money cell's unit is read when the cell states none: the row's currency and scale,
    else the column header (`available value (USD m)`); a claim whose header states none is in
    the available value's (`priority claim` names a class, so its header rarely carries one)."""
    at = cols[UNIT][0]
    own = f"{row[at] if at >= 0 else ''} {cols[name][1]}"
    if name == "priority claim" and not (core.currency_of(own) and core.scale_of(own)):
        return f"{own} {cols['available value'][1]}"
    return own


def _claim(cell: str, unit: str, tables: types.ModuleType) -> tuple[str, core.Amount]:
    """`<class>: <amount>`, a bare amount, or claims ranking equally in one row (`TLB: 900; RCF:
    600`, their sum); a name with no amount states no claim."""
    parts = [p for p in _plain(cell).split(";") if p.strip()]
    if len(parts) > 1:
        read = [_claim(p, unit, tables) for p in parts]
        units = {a.unit for _, a in read}
        if len(units) != 1:
            raise _NotChecked(f"Priority claim `{cell}` states its claims in different units")
        total = sum(float(a.value or 0.0) for _, a in read)
        half = sum(a.half for _, a in read)
        return " and ".join(n for n, _ in read), core.Amount(total, units.pop(), cell, half)
    head, colon, rest = _plain(cell).rpartition(":")
    name, amount = (head.strip(), rest) if colon else ("", _plain(cell))
    found = money(amount, unit, tables)
    if found.value is None:
        raise _NotChecked(f"Priority claim `{cell}` states no claim amount (missing, not zero)")
    return name or _plain(cell), found


def _step(row: list[str], cols: dict[str, tuple[int, str]], tables: types.ModuleType) -> _Step:
    def amount(name: str) -> core.Amount:
        return money(row[cols[name][0]], _unit_source(row, cols, name), tables)

    name, claim = _claim(
        row[cols["priority claim"][0]], _unit_source(row, cols, "priority claim"), tables
    )
    allocation = _plain(row[cols["allocation"][0]])
    noted = _NOTE.match(allocation)
    return _Step(
        _plain(row[cols["scenario"][0]]),
        _plain(row[cols["entity"][0]]),
        name,
        amount("available value"),
        claim,
        noted["figure"] if noted else allocation,
        row[cols["residual"][0]],
        noted["note"] if noted else "",
        _unit_source(row, cols, "allocation"),
    )


def _row(step: _Step, loaded: Loaded, left_over: float | None = None) -> list[Outcome]:
    """The step's allocation and residual from its own available value or, for rows that repeat
    one pool (``left_over``: the value left after the rows above), from what is left."""
    at = f"{step.name} ({step.scenario}, {step.entity})"
    allocation, residual = _where(f"Allocation: {at}"), _where(f"Residual: {at}")
    if step.available.value is None:
        why = "T4E.5 states no available value for this row (missing, not zero)"
        return [w("not checked", reason=why) for w in (allocation, residual)]
    units = {step.available.unit, step.claim.unit}
    if len(units) != 1:
        why = (
            f"the row's available value and claim are in different units: {sorted(map(str, units))}"
        )
        return [w("not checked", reason=why) for w in (allocation, residual)]
    if step.noted:
        why = f"the allocation is set by the governing evidence (`{step.noted}`), not the waterfall"
        return [
            w("not checked", stated=step.allocation, reason=why) for w in (allocation, residual)
        ]
    claims = [{"claim_id": step.name, "class": step.name, "amount": step.claim.value}]
    available = step.available.value if left_over is None else left_over
    try:
        result = loaded.script.waterfall(available, claims)
    except ValueError as error:  # a negative value (an entity in deficit): the script refuses
        why = f"the script refused the row: {error}"
        return [w("not checked", reason=why) for w in (allocation, residual)]
    recovered, left = result["claims"][0]["recovered"], result["residual_to_equity"]
    slack = max(step.available.half, step.claim.half)  # a lesser-of: the larger rounding
    out = []
    for where, cell, value, bound in (
        (allocation, step.allocation, recovered, slack),
        (residual, step.residual, left, step.available.half + slack),
    ):
        out.append(_figure(where, cell, (value, bound), step, loaded.tables))
    return out


def _figure(
    where: _Where, cell: str, recomputed: tuple[float, float], step: _Step, tables: types.ModuleType
) -> Outcome:
    """One stated allocation or residual against the script's, in the row's unit. An allocation
    may be written as an outflow (`-600`, as the value allocation chart writes it): the method
    fixes no sign, so its magnitude is compared."""
    try:
        read = money(cell, step.source, tables)
    except _NotChecked as error:
        return where("not checked", stated=cell, reason=str(error))
    if read.value is None:
        return where("not checked", stated=cell, reason="T4E.5 states no figure here")
    if read.unit != step.available.unit:
        why = f"`{cell}` is in {read.unit}, the row's available value in {step.available.unit}"
        return where("not checked", stated=cell, reason=why)
    stated = core.bare(cell)
    if where.figure.startswith("Allocation") and read.value < 0:
        stated = stated.strip("()").lstrip("-\u2212 ")
    value, bound = recomputed  # the script's figure and its inputs' rounding bound
    claim = _Claim(where, stated, value, AMOUNT_STEP, str(read.unit), ALLOCATION_FORMULA)
    return _judged(replace(claim, slack=bound), tables)


def _units(steps: list[_Step], tables: types.ModuleType) -> set[str | None]:
    """Every unit the steps' available values, claims and residuals are stated in."""
    units: set[str | None] = set()
    for step in steps:
        units |= {step.available.unit, step.claim.unit}
        try:
            units.add(money(step.residual, step.source, tables).unit)
        except _NotChecked:
            units.add("unread")
    return units - {None}


def _pooled(steps: list[_Step]) -> bool:
    """Rows of one entity that each repeat the pool as their available value (and state the
    residual after every row above): read as one pool, not as steps."""
    values = [s.available for s in steps]
    if len(steps) < 2 or len({s.entity for s in steps}) != 1 or values[0].value is None:
        return False
    first = float(values[0].value)
    return all(
        v.value is not None and abs(v.value - first) <= v.half + values[0].half + 1e-9
        for v in values[1:]
    )


def _chain(steps: list[_Step], tables: types.ModuleType) -> str:
    """Why a scenario's rows are not one pool the script can allocate, or ``""``."""
    if len({s.entity for s in steps}) != 1:
        return "its T4E.5 rows are more than one entity, and the script allocates one pool"
    if any(s.noted for s in steps):
        return "a T4E.5 allocation is set by the governing evidence, not the waterfall"
    if len(_units(steps, tables)) != 1:
        return "its T4E.5 rows state more than one currency or scale, or one is not read"
    if _pooled(steps):
        return ""
    for before, after in pairwise(steps):
        left = core.figure(core.bare(before.residual), tables)
        start = after.available
        apart = (
            isinstance(left, str)
            or start.value is None
            or abs(left[0] - start.value) > core.half(left[1]) + start.half + 1e-9
        )
        if apart:
            return (
                "its T4E.5 rows are not one chain (an available value is not the residual before)"
            )
    return ""


def _fulcrum(scenario: str, steps: list[_Step], stated: str | None, loaded: Loaded) -> Outcome:
    where = _Where("CP-4C", RECOVERY, f"Fulcrum ({scenario})", "T4E.6")
    if stated is None or _plain(stated) in ("", *core.NOT_APPLICABLE):
        return where("not checked", stated=stated, reason=f"T4E.6 states no fulcrum for {scenario}")
    why = _chain(steps, loaded.tables)
    if why or steps[0].available.value is None:
        return where("not checked", stated=stated, reason=why or "no available value to allocate")
    claims = [{"claim_id": s.name, "class": s.name, "amount": s.claim.value} for s in steps]
    try:
        result: dict[str, Any] = loaded.script.waterfall(steps[0].available.value, claims)
    except ValueError as error:
        return where("not checked", stated=stated, reason=f"the script refused the pool: {error}")
    found, name = result["fulcrum_claim_id"], _named(stated)
    if name not in NO_FULCRUM and name not in {_named(s.name) for s in steps}:
        why = f"`{stated}` names no single T4E.5 claim (a range is not compared)"
        return where("not checked", stated=stated, reason=why)
    agreed = name in NO_FULCRUM if found is None else name == _named(found)
    label = "no fulcrum" if found is None else str(found)
    if not agreed and name in _boundary(steps):
        why = (
            f"value runs out at a class boundary within the inputs' rounding, so `{stated}` (a "
            f"class beside it) and the script's {label} are both defensible"
        )
        return where("not checked", stated=stated, recomputed_label=label, reason=why)
    status: Status = "agreed" if agreed else "disagreed"
    return where(status, stated=stated, recomputed_label=label, reason=FULCRUM_FORMULA)


def _boundary(steps: list[_Step]) -> set[str]:
    """The names a reader may defensibly give the fulcrum when the value runs out at a class
    boundary within the inputs' rounding: the last covered class, the first impaired one, or
    none. Empty when the value ends inside a class."""
    slack = float(steps[0].available.half) + sum(s.claim.half for s in steps)
    pool, total = float(steps[0].available.value or 0.0), 0.0
    names = [_named(s.name) for s in steps]
    out: set[str] = set()
    for i, step in enumerate(steps):
        total += float(step.claim.value or 0.0)
        if abs(pool - total) <= slack + 1e-9:
            out |= {names[i], *names[i + 1 : i + 2], *NO_FULCRUM}
    return out


def _stated_fulcra(text: str) -> dict[str, str]:
    """T4E.6's fulcrum by its scenario cell (as compared); empty when T4E.6 is not read."""
    table = register_table(text, "T4E.6")
    if isinstance(table, str):
        return {}
    try:
        scenario = column(table, "scenario/EV range", "T4E.6")[0]
        fulcrum = column(table, "fulcrum class/range", "T4E.6")[0]
    except _NotChecked:
        return {}
    return {_label(row[scenario]): row[fulcrum] for row in table[1]}


def _match(scenario: str, fulcra: dict[str, str]) -> str | None:
    """The T4E.6 fulcrum whose scenario cell is this scenario, alone or before its EV range."""
    want = _label(scenario)
    found = [f for s, f in fulcra.items() if s == want or re.match(rf"{re.escape(want)}\b", s)]
    return found[0] if len(found) == 1 else None


def _share(step: _Step, tables: types.ModuleType) -> float | None:
    """The share of its claim a row's stated allocation is; None when it is not read."""
    try:
        read = money(step.allocation, step.source, tables)
    except _NotChecked:
        return None
    if read.value is None or not step.claim.value:
        return None
    return abs(read.value) / step.claim.value


def _pro_rata(group: list[_Step], tables: types.ModuleType) -> bool:
    """Rows that share one available value with the same partial recovery: claims ranking
    equally, each written as its own row. The note asks for one row, but the split is right."""
    if len(group) < 2 or len({s.available.value for s in group}) != 1:
        return False
    shares = [_share(s, tables) for s in group]
    known = [x for x in shares if x is not None]
    return (
        len(known) == len(group)
        and all(0 < x < 1 for x in known)
        and (max(known) - min(known) <= 0.01)
    )


def _rows(steps: list[_Step], loaded: Loaded) -> list[Outcome]:
    """Every step's outcomes: each row by itself, or, for an entity's rows that repeat one pool,
    each from the value the rows above it leave; rows sharing a pool pro rata are not checked."""
    groups: dict[tuple[str, str], list[_Step]] = {}
    for step in steps:
        groups.setdefault((step.scenario, step.entity), []).append(step)
    left: dict[int, float] = {}  # id(step) -> the value left for it, in a pooled group
    skipped: dict[int, str] = {}  # id(step) -> why it is not checked
    for group in groups.values():
        if _pro_rata(group, loaded.tables):
            why = "these rows share one available value pro rata, as claims ranking equally do"
            skipped |= dict.fromkeys(map(id, group), why)
        elif _pooled(group) and len(_units(group, loaded.tables)) == 1:
            try:
                left |= _left_over(group, loaded)
            except ValueError as error:  # the script refuses a value (a deficit pool)
                skipped |= dict.fromkeys(map(id, group), f"the script refused the pool: {error}")
    out: list[Outcome] = []
    for step in steps:
        if id(step) in skipped:
            at = f"{step.name} ({step.scenario}, {step.entity})"
            out += [
                _where(f"{f}: {at}")("not checked", reason=skipped[id(step)])
                for f in ("Allocation", "Residual")
            ]
        else:
            out += _row(step, loaded, left.get(id(step)))
    return out


def _left_over(group: list[_Step], loaded: Loaded) -> dict[int, float]:
    """For rows that repeat one pool: the value the rows above each one leave."""
    remaining, left = float(group[0].available.value or 0.0), {}
    for step in group:
        left[id(step)] = remaining
        claim = [{"claim_id": step.name, "amount": step.claim.value}]
        remaining = float(loaded.script.waterfall(remaining, claim)["residual_to_equity"])
    return left


def check(text: str, loaded: Loaded, _upstream: Upstream) -> list[Outcome]:
    """Each T4E.5 step's allocation and residual, then each one-pool scenario's T4E.6 fulcrum."""
    table = register_table(text, "T4E.5")
    try:
        if isinstance(table, str):
            raise _NotChecked(table)
        cols = _columns(table)
    except _NotChecked as error:
        return [_where("T4E.5")("not checked", reason=str(error))]
    out: list[Outcome] = []
    read: list[_Step] = []
    scenarios: dict[str, list[_Step]] = {}
    unread: dict[str, str] = {}  # scenario -> why a row above one of its read rows is not read
    for written in table[1]:
        row = [re.sub(r"^([(\s*]*)[–−]", r"\1-", c).replace("−", "-") for c in written]
        scenario = _plain(row[cols["scenario"][0]])
        try:
            step = _step(row, cols, loaded.tables)
        except (_NotChecked, ValueError) as error:  # ValueError: the script's parser refuses
            claim = _plain(row[cols["priority claim"][0]])
            out.append(_where(f"Row: {claim} ({scenario})")("not checked", reason=str(error)))
            unread.setdefault(scenario, str(error))
            continue
        read.append(step)
        if scenario in unread:  # a claim above this one has no amount: its value is unknown
            scenarios[scenario] = []
            continue
        scenarios.setdefault(scenario, []).append(step)
    out += _rows(read, loaded)
    fulcra = _stated_fulcra(text)
    for scenario in dict.fromkeys([*scenarios, *unread]):
        steps = scenarios.get(scenario, [])
        if not steps:
            where = _Where("CP-4C", RECOVERY, f"Fulcrum ({scenario})", "T4E.6")
            why = f"a T4E.5 row above a claim is not read: {unread.get(scenario, 'no claim')}"
            out.append(where("not checked", reason=why))
            continue
        out.append(_fulcrum(scenario, steps, _match(scenario, fulcra), loaded))
    return out


core.register("CP-4C", RECOVERY, check, CP4C_NOTE)
