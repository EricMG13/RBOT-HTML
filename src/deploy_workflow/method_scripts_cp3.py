"""CP-3's method scripts on its `### Recovery waterfall` table (harness:
`deploy_workflow.method_scripts`): `recovery_waterfall.py` for the allocation, and CP-1C's
`peer_statistics.py` for each case's enterprise value.

The SKILL names `recovery_waterfall.py` as the owner of "per-class recovery under each
enterprise-value case and the fulcrum in each", and CP-4B's runbook says "CP-3A owns the dollar
waterfall". No CP-3 register holds its inputs or results (T3B.2's Amount is carrying value, T3B.4
an ordinal, T3B.6 a label; no register holds an enterprise value), so CP-3 is asked for one table
(owner, 2026-11-15: "1. yes 2. yes 3. yes"):

| Line | Amount | Low | Base | High | Currency | Scale |
|---|---|---|---|---|---|---|
| Enterprise value | — | <EV> | <EV> | <EV> | USD | m |
| EV multiple | — | <x> | <x> | <x> | — | — |
| EV metric | — | <EBITDA> | <EBITDA> | <EBITDA> | USD | m |
| EV basis | — | <metric, period, multiple basis, source> | ... | ... | — | — |
| Cost: <label> | <amount> | — | — | — | USD | m |
| Claim: <instrument> | <claim> | <recovery %> | <recovery %> | <recovery %> | USD | m |
| Fulcrum | — | <instrument or None> | ... | ... | — | — |
| Residual to equity | — | <amount> | <amount> | <amount> | USD | m |

Where CP-3 receives CP-1C, the cases are CP-1C's T4.10 Low, Median and High implied EV (this
overrides CP-1C's own "NOT recovery estimate" rule for CP-3's use only); otherwise CP-3 states its
own cases with their basis, or `Not supplied: <reason>` where none can be supported (recorded, not
refused). Claims are allocated in row order, senior first, as the script takes them. A handoff
without the table, unless CP-3 stopped at its gate, is sent back.
"""

import re
import types
from dataclasses import dataclass, replace
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    AMOUNT_STEP,
    ARCHIVE,
    Loaded,
    Outcome,
    Status,
    Table,
    Upstream,
    _cell_half,
    _Claim,
    _columns,
    _judged,
    _label,
    _NotChecked,
    _plain,
    _value,
    _Where,
    bare,
    blank,
    column,
    currency_of,
    figure,
    half,
    heading_table,
    quotient_slack,
    register_table,
    said_none,
    scale_of,
    share,
)

RECOVERY = ARCHIVE + "skills/cp-4c-restructuring-fulcrum/scripts/recovery_waterfall.py"
WATERFALL_HEADING = "Recovery waterfall"
CASES = ("Low", "Base", "High")
WATERFALL_COLUMNS = ("Line", "Amount", *CASES, "Currency", "Scale")
EV, FULCRUM, RESIDUAL = "Enterprise value", "Fulcrum", "Residual to equity"
NO_FULCRUM = ("none", "no fulcrum", "n/a")
RECOVERY_FORMULA = (
    "Recovery = min(claim, value left after the costs and every senior claim) / claim, value "
    "allocated in the table's row order (recovery_waterfall.py)"
)
FULCRUM_FORMULA = (
    "The fulcrum is the first claim, in row order, that recovers more than nothing and less than "
    "in full; a boundary or zero recovery is no fulcrum (recovery_waterfall.py)"
)
RESIDUAL_FORMULA = (
    "Residual to equity = enterprise value - costs - every claim's recovery, floored at 0; value "
    "the claims do not absorb is not left unallocated (recovery_waterfall.py)"
)
MULTIPLE, METRIC, BASIS = "EV multiple", "EV metric", "EV basis"
BASIS_ROWS = (MULTIPLE, METRIC, BASIS)
PEER_STATISTICS = ARCHIVE + "skills/cp-1c-peer-benchmark/scripts/peer_statistics.py"
T410_CASES = {"Low": "Low", "Base": "Median", "High": "High"}  # CP-1C's implied EV range
EV_FORMULA = (
    "Enterprise value = EV multiple x EV metric (CP-1C's Implied EV formula; peer_statistics.py "
    "implied_ev, which gives none on a metric at or below zero)"
)
COPY_FORMULA = (
    "The case's enterprise value is CP-1C's T4.10 implied EV for it (Low, Median, High), as the "
    "CP-1C handoff CP-3 was sent states it"
)
_METHODS = ("ev/ebitda", "ev/revenue", "tv/ebitda", "tv/revenue")
_HEADING = f"`### {WATERFALL_HEADING}`"


def _where(figure_name: str, script: str = RECOVERY) -> _Where:
    return _Where("CP-3", script, figure_name, _HEADING)


@dataclass(frozen=True)
class _Waterfall:
    """The table as the script reads it."""

    claims: list[dict[str, Any]]  # in row order; a claim named twice is kept, for the script
    stated: dict[str, list[str]]  # claim name -> its row, as written
    costs: list[dict[str, Any]]
    ev: dict[str, float | None]  # case -> enterprise value (None: stated none)
    fulcrum: list[str] | None
    residual: list[str] | None
    unit: str
    cols: dict[str, int]
    halves: dict[str, float]  # `costs`, `claim:<name>`, `ev:<case>`: displayed rounding
    basis: dict[str, list[str] | None]  # the EV multiple, metric and basis rows, as written
    ev_cells: dict[str, str]  # case -> the Enterprise value cell, as written


def _kind(line: str) -> tuple[str, str]:
    """(`claim` | `cost` | the row's label, the name after `Claim:` / `Cost:`)."""
    head, colon, rest = _plain(line).partition(":")
    if colon and _label(head) in ("claim", "cost"):
        return _label(head), rest.strip()
    return _label(line), ""


def _unit(rows: list[list[str]], cols: dict[str, int]) -> str:
    pairs = {(currency_of(r[cols["Currency"]]), scale_of(r[cols["Scale"]])) for r in rows}
    if len(pairs) != 1 or None in next(iter(pairs)):
        shown = "; ".join(sorted({f"{r[cols['Currency']]} {r[cols['Scale']]}" for r in rows}))
        raise _NotChecked(
            f"{_HEADING} rows state different or unread currencies or scales: {shown}"
        )
    currency, scale = next(iter(pairs))
    return f"{currency} {scale}"


def _single(rows: dict[str, list[list[str]]], name: str) -> list[str] | None:
    found = rows.get(_label(name), [])
    if len(found) > 1:
        raise _NotChecked(f"{_HEADING} has {len(found)} `{name}` rows")
    return found[0] if found else None


def _read(table: Table, tables: types.ModuleType) -> _Waterfall:
    cols = _columns(table, WATERFALL_COLUMNS, _HEADING)
    if isinstance(cols, str):
        raise _NotChecked(cols)
    claims, costs, money = [], [], []
    halves: dict[str, float] = {"costs": 0.0}
    stated: dict[str, list[str]] = {}
    labelled: dict[str, list[list[str]]] = {}
    for row in table[1]:
        kind, name = _kind(row[cols["Line"]])
        if kind == "claim":
            claims.append(
                {"claim_id": name, "class": name, "amount": _value(row[cols["Amount"]], tables)}
            )
            stated[name] = row
            halves[f"claim:{name}"] = _cell_half(row[cols["Amount"]], tables)
        elif kind == "cost":
            costs.append({"label": name, "amount": _value(row[cols["Amount"]], tables)})
            halves["costs"] += _cell_half(row[cols["Amount"]], tables)
        elif kind not in (_label(n) for n in (EV, FULCRUM, RESIDUAL, *BASIS_ROWS)):
            raise _NotChecked(
                f"{_HEADING} has a row the check does not read: `{row[cols['Line']]}`"
            )
        else:
            labelled.setdefault(kind, []).append(row)
        if kind not in (_label(n) for n in (FULCRUM, MULTIPLE, BASIS)):
            money.append(row)
    ev_row = _single(labelled, EV)
    if ev_row is None:
        raise _NotChecked(f"{_HEADING} has no `{EV}` row")
    ev = {case: _value(ev_row[cols[case]], tables) for case in CASES}
    halves |= {f"ev:{case}": _cell_half(ev_row[cols[case]], tables) for case in CASES}
    return _Waterfall(
        claims,
        stated,
        costs,
        ev,
        _single(labelled, FULCRUM),
        _single(labelled, RESIDUAL),
        _unit(money, cols),
        cols,
        halves,
        {name: _single(labelled, name) for name in BASIS_ROWS},
        {case: ev_row[cols[case]] for case in CASES},
    )


def _recoveries(
    case: str, w: _Waterfall, result: dict[str, Any], tables: types.ModuleType
) -> list[Outcome]:
    out = []
    above = w.halves[f"ev:{case}"] + w.halves["costs"]  # rounding of the value left for a claim
    for row in result["claims"]:
        name = row["claim_id"]
        own = w.halves.get(f"claim:{name}", 0.0)
        where = _where(f"Recovery: {name} ({case})")
        cell = w.stated[name][w.cols[case]]
        if blank(cell, tables):
            out.append(
                where(
                    "not checked", stated=cell, reason=f"no recovery is stated for {name} in {case}"
                )
            )
        elif row["recovery_pct"] is None:
            why = result.get("note") or f"{name}'s claim is 0, so it has no recovery percentage"
            out.append(where("not checked", stated=cell, reason=str(why)))
        else:
            slack = quotient_slack(row["recovered"], above, row["amount"], own)
            claim = _Claim(where, cell, row["recovery_pct"], 0.0, "", RECOVERY_FORMULA)
            out.append(share(replace(claim, slack=slack), tables))
        above += own  # a junior claim's value is what is left after this one
    return out


def _fulcrum(case: str, w: _Waterfall, result: dict[str, Any]) -> Outcome:
    where = _where(f"{FULCRUM} ({case})")
    cell = None if w.fulcrum is None else w.fulcrum[w.cols[case]]
    if cell is None or _plain(cell) in ("", *core.NOT_APPLICABLE):
        return where("not checked", stated=cell, reason=f"{_HEADING} states no fulcrum for {case}")
    if result["status"] != "complete":
        return where("not checked", stated=cell, reason=str(result.get("note")))
    found = result["fulcrum_claim_id"]
    name = re.sub(r"\s*\([^)]*\)$", "", _label(cell))  # `Senior Notes (partial)` names the notes
    agreed = name in NO_FULCRUM if found is None else name == _label(found)
    label = "no fulcrum" if found is None else str(found)
    status: Status = "agreed" if agreed else "disagreed"
    return where(status, stated=cell, recomputed_label=label, reason=FULCRUM_FORMULA)


def _residual(
    case: str, w: _Waterfall, result: dict[str, Any], tables: types.ModuleType
) -> Outcome:
    where = _where(f"{RESIDUAL} ({case})")
    cell = None if w.residual is None else w.residual[w.cols[case]]
    if cell is None or blank(cell, tables):
        return where(
            "not checked", stated=cell, reason=f"{_HEADING} states no {RESIDUAL} for {case}"
        )
    if result["residual_to_equity"] is None:
        return where("not checked", stated=cell, reason=str(result.get("note")))
    claim = _Claim(where, cell, result["residual_to_equity"], AMOUNT_STEP, w.unit, RESIDUAL_FORMULA)
    claims = sum(h for k, h in w.halves.items() if k.startswith("claim:"))
    slack = w.halves[f"ev:{case}"] + w.halves["costs"] + claims  # a difference of all of them
    return _judged(replace(claim, slack=slack), tables)


# --- the enterprise value of each case ------------------------------------------------------


def _row_cell(w: _Waterfall, name: str, case: str) -> str | None:
    row = w.basis.get(name)
    return None if row is None else row[w.cols[case]]


def _ev_figure(w: _Waterfall, case: str, loaded: Loaded) -> Outcome:
    """The case's EV against the method's own arithmetic: multiple x metric (CP-1C's script)."""
    where = _where(f"{EV} ({case})", PEER_STATISTICS)
    cell = w.ev_cells[case]
    multiple, metric = _row_cell(w, MULTIPLE, case), _row_cell(w, METRIC, case)
    if (
        multiple is None
        or metric is None
        or blank(multiple, loaded.tables)
        or blank(metric, loaded.tables)
    ):
        reason = f"the {EV} for {case} states no {MULTIPLE} and {METRIC} to recompute it from"
        return where("not checked", stated=cell, reason=reason)
    read_m = figure(re.sub(r"(?i)\s*x(?=\)?$)", "", _plain(multiple)), loaded.tables)
    read_b = figure(metric, loaded.tables)
    if isinstance(read_m, str) or isinstance(read_b, str):
        return where(
            "not checked", stated=cell, reason=str(read_m if isinstance(read_m, str) else read_b)
        )
    peers = core._loaded(PEER_STATISTICS).script
    stats = {
        "statistics_including_outliers": dict.fromkeys(("minimum", "median", "maximum"), read_m[0])
    }
    implied = peers.implied_ev(
        {"borrower_metric": read_b[0]}, stats | {"meaningful_as_sector_multiple": True}
    )
    value = None if implied is None else implied["median"]
    if value is None:
        why = f"{EV_FORMULA}; the {METRIC} {read_b[0]:g} is not above zero, so there is none"
        return where("disagreed", stated=cell, recomputed_label="Not Calculable", reason=why)
    slack = abs(read_m[0]) * half(read_b[1]) + abs(read_b[0]) * half(read_m[1])  # a product
    claim = _Claim(where, cell, value, AMOUNT_STEP, w.unit, EV_FORMULA, slack=slack)
    return _judged(claim, loaded.tables)


def _t410_value(text: str, method: str, case: str, tables: types.ModuleType) -> tuple[str, str]:
    """T4.10's implied EV for the case (Low, Median or High) of the named method, as written, with
    the header it sits under; `_NotChecked` when T4.10 cannot be read for it."""
    table = register_table(text, "T4.10")
    if isinstance(table, str):
        raise _NotChecked(f"CP-1C's handoff: {table}")
    rows = [r for r in table[1] if method in _label(r[0])]
    if len(rows) != 1:
        raise _NotChecked(f"CP-1C's T4.10 has {len(rows) or 'no'} `{method}` rows")
    wanted = T410_CASES[case]
    try:
        index, header = column(table, wanted, "CP-1C's T4.10")
        return rows[0][index], header
    except _NotChecked:
        pass
    found = [i for i, h in enumerate(table[0]) if "low/median/high" in _label(h)]
    if len(found) != 1:
        raise _NotChecked(f"CP-1C's T4.10 has no `{wanted}` column")
    parts = [p.strip() for p in _plain(rows[0][found[0]]).split("/")]
    if len(parts) < 3 or blank(rows[0][found[0]], tables):
        return rows[0][found[0]], table[0][found[0]]
    return parts[-3:][list(T410_CASES).index(case)], table[0][found[0]]


def _ev_copy(w: _Waterfall, case: str, loaded: Loaded, upstream: Upstream) -> Outcome | None:
    """When the case's basis names CP-1C's T4.10, its EV against the T4.10 CP-3 was sent: a
    mis-copied figure is the likeliest error. None when the basis does not name T4.10."""
    basis = _label(_row_cell(w, BASIS, case) or "")
    if not re.search(r"t4\.10|cp 1c", basis):
        return None
    where = _where(f"{EV} ({case}) from CP-1C T4.10", PEER_STATISTICS)
    cell = w.ev_cells[case]
    method = next((m for m in _METHODS if m in basis), None)
    try:
        if "CP-1C" not in upstream:
            raise _NotChecked("CP-3 was not sent CP-1C's handoff, whose T4.10 the basis names")
        if method is None:
            raise _NotChecked(
                f"the basis names T4.10 but none of its methods ({', '.join(_METHODS)})"
            )
        sent = _t410_value(upstream["CP-1C"], method, case, loaded.tables)
    except _NotChecked as why:
        return where("not checked", stated=cell, reason=str(why))
    return _copied(_Claim(where, cell, 0.0, AMOUNT_STEP, w.unit, COPY_FORMULA), sent, loaded.tables)


def _copied(claim: _Claim, sent: tuple[str, str], tables: types.ModuleType) -> Outcome:
    """The stated EV (``claim``) against T4.10's figure and header as sent."""
    where, cell, unit = claim.where, claim.stated, claim.unit
    source, header = sent
    if blank(source, tables) or said_none(source):
        why = f"{COPY_FORMULA}; T4.10 states no figure for it (`{source}`)"
        return where("disagreed", stated=cell, recomputed_label="none in T4.10", reason=why)
    stated_unit = (currency_of(source) or currency_of(header), scale_of(source) or scale_of(header))
    read = figure(bare(source), tables)
    if isinstance(read, str):
        return where("not checked", stated=cell, reason=f"T4.10: {read}")
    known = None not in stated_unit
    if known and f"{stated_unit[0]} {stated_unit[1]}" != unit:
        why = f"T4.10 states `{stated_unit[0]} {stated_unit[1]}`, the waterfall `{unit}`"
        return where("not checked", stated=cell, reason=why)
    outcome = _judged(replace(claim, recomputed=read[0]), tables)
    if known or outcome.status != "disagreed":
        return outcome
    why = "T4.10 states no currency or scale, so a different figure may be a different scale"
    return replace(outcome, status="not checked", reason=why)


def _ev(case: str, w: _Waterfall, loaded: Loaded, upstream: Upstream) -> list[Outcome]:
    """The case's EV: its basis owed, its arithmetic and, from T4.10, its copy."""
    cell = w.ev_cells[case]
    if blank(cell, loaded.tables) or said_none(cell):
        reason = f"CP-3 states no enterprise value can be supported for {case}: `{cell}`"
        where = _where(f"{EV} ({case})", PEER_STATISTICS)
        return [where("not checked", stated=cell, reason=reason)]
    basis = _row_cell(w, BASIS, case)
    if basis is None or blank(basis, loaded.tables):
        why = (
            f"`### {WATERFALL_HEADING}` states an {EV} for {case} with no {BASIS}: state the "
            "metric and period it values, the multiple or other basis, and where each came from "
            "(CP-1C T4.10, or the evidence you were given), or write the value `Not supplied: "
            "<reason>`."
        )
        return [_where(f"{BASIS} ({case})", PEER_STATISTICS)("missing", stated=cell, reason=why)]
    copy = _ev_copy(w, case, loaded, upstream)
    return [_ev_figure(w, case, loaded), *([copy] if copy is not None else [])]


def _case(case: str, w: _Waterfall, loaded: Loaded, upstream: Upstream) -> list[Outcome]:
    result = None
    if w.ev[case] is None:
        reason = f"{_HEADING} states no {EV} for {case} (missing, not zero)"
    else:
        result = loaded.script.waterfall(w.ev[case], w.claims, w.costs)
        reason = str(result.get("note"))  # a cost without an amount stops the whole case
    values = _ev(case, w, loaded, upstream)
    if result is None or "claims" not in result:
        names = [f"Recovery: {c['claim_id']} ({case})" for c in w.claims]
        names += [f"{FULCRUM} ({case})", f"{RESIDUAL} ({case})"]
        return [*values, *(_where(n)("not checked", reason=reason) for n in names)]
    return [
        *values,
        *_recoveries(case, w, result, loaded.tables),
        _fulcrum(case, w, result),
        _residual(case, w, result, loaded.tables),
    ]


MISSING_TABLE = (
    f"Write `### {WATERFALL_HEADING}` in `## Findings` as your instructions describe. Where no "
    f"enterprise value can be supported, write the table with each `{EV}` cell as `Not supplied: "
    "<reason>`; that is recorded, not refused."
)


def check(text: str, loaded: Loaded, upstream: Upstream) -> list[Outcome]:
    """Each case's enterprise value (its basis, its arithmetic and its copy from CP-1C's T4.10),
    then recovery by claim, the fulcrum and the residual to equity, recomputed by the scripts from
    the table's own rows. An absent table is sent back unless CP-3 stopped at its gate."""
    table = heading_table(text, WATERFALL_HEADING)
    if isinstance(table, str) and table.startswith("the handoff has no") and not core.blocked(text):
        return [_where(WATERFALL_HEADING)("missing", reason=MISSING_TABLE)]
    try:
        if isinstance(table, str):
            raise _NotChecked(table)
        waterfall = _read(table, loaded.tables)
        return [o for case in CASES for o in _case(case, waterfall, loaded, upstream)]
    except _NotChecked as why:
        return [_where(WATERFALL_HEADING)("not checked", reason=str(why))]
    except ValueError as error:  # the script refuses: a claim named twice, a negative amount
        cause = f"the script refused the table: {error}"
        return [_where(WATERFALL_HEADING)("not checked", reason=cause)]


CP3_NOTE = (
    "Python checks your recovery waterfall after you answer, with the method's own "
    "`recovery_waterfall.py` and CP-1C's `peer_statistics.py` (you cannot run them). Write it in "
    f"`## Findings` as `### {WATERFALL_HEADING}` with the columns "
    f"`{' | '.join(WATERFALL_COLUMNS)}`: an `{EV}` row; `{MULTIPLE}`, `{METRIC}` (the EBITDA or "
    f"revenue it multiplies) and `{BASIS}` (that metric and its period, the multiple's basis and "
    "where each came from) rows; a `Cost: <label>` row per cost; a `Claim: <instrument>` row per "
    "claim, senior first, its claim in Amount and its recovery % in each case; `Fulcrum` (the "
    "claim, or None); `Residual to equity`. Where you were sent CP-1C's T4.10, the cases are its "
    "Low, Median and High implied EV, the basis naming `CP-1C T4.10` and its method (EV/EBITDA); "
    "otherwise state your own cases with their basis from the evidence you were given. Where no "
    f"enterprise value can be supported, write each `{EV}` cell `Not supplied: <reason>`: that is "
    "recorded, not refused. An implied EV from peer multiples is indicative, not a valuation: "
    "say in your limitations that the recoveries carry that limitation. A cell that does not "
    "apply is `—`. A figure that disagrees is sent back for repair, and so is a missing table.\n\n"
)
# Owner, 2026-11-15: "1. yes 2. yes 3. yes" (ruling 2026-11-15-method-script-checks.md).
core.register("CP-3", RECOVERY, check, CP3_NOTE)
