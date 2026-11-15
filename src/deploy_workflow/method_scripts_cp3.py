"""CP-3's method script, `recovery_waterfall.py`, run on a `### Recovery waterfall` table when the
handoff has one (harness: `deploy_workflow.method_scripts`).

The SKILL names the script as the owner of "per-class recovery under each enterprise-value case and
the fulcrum in each". No CP-3 register holds its inputs or its results: T3B.2's Amount is carrying
value (CP-3A runbook: "every instrument Amount uses the canonical carrying-value debt basis"), not
the claim a waterfall allocates; T3B.4's Structural Rank is an ordinal; T3B.6's Recovery Sensitivity
is a label, and step 6 says not to infer recovery values; no register holds an enterprise value.
So the check reads one table, proposed to the owner and NOT asked of CP-3 (no note is sent):

| Line | Amount | Low | Base | High | Currency | Scale |
|---|---|---|---|---|---|---|
| Enterprise value | — | <EV> | <EV> | <EV> | USD | m |
| Cost: <label> | <amount> | — | — | — | USD | m |
| Claim: <instrument> | <claim> | <recovery %> | <recovery %> | <recovery %> | USD | m |
| Fulcrum | — | <instrument or None> | ... | ... | — | — |
| Residual to equity | — | <amount> | <amount> | <amount> | USD | m |

Claims are allocated in row order, senior first, as the script takes them. A handoff without the
table has every figure "not checked".
"""

import types
from dataclasses import dataclass
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    AMOUNT_STEP,
    ARCHIVE,
    Loaded,
    Outcome,
    Status,
    Table,
    _Claim,
    _columns,
    _judged,
    _label,
    _NotChecked,
    _plain,
    _value,
    _Where,
    blank,
    currency_of,
    heading_table,
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
_HEADING = f"`### {WATERFALL_HEADING}`"


def _where(figure_name: str) -> _Where:
    return _Where("CP-3", RECOVERY, figure_name, _HEADING)


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
    stated: dict[str, list[str]] = {}
    labelled: dict[str, list[list[str]]] = {}
    for row in table[1]:
        kind, name = _kind(row[cols["Line"]])
        if kind == "claim":
            claims.append(
                {"claim_id": name, "class": name, "amount": _value(row[cols["Amount"]], tables)}
            )
            stated[name] = row
        elif kind == "cost":
            costs.append({"label": name, "amount": _value(row[cols["Amount"]], tables)})
        elif kind not in (_label(EV), _label(FULCRUM), _label(RESIDUAL)):
            raise _NotChecked(
                f"{_HEADING} has a row the check does not read: `{row[cols['Line']]}`"
            )
        else:
            labelled.setdefault(kind, []).append(row)
        if kind != _label(FULCRUM):
            money.append(row)
    ev_row = _single(labelled, EV)
    if ev_row is None:
        raise _NotChecked(f"{_HEADING} has no `{EV}` row")
    ev = {case: _value(ev_row[cols[case]], tables) for case in CASES}
    return _Waterfall(
        claims,
        stated,
        costs,
        ev,
        _single(labelled, FULCRUM),
        _single(labelled, RESIDUAL),
        _unit(money, cols),
        cols,
    )


def _recoveries(
    case: str, w: _Waterfall, result: dict[str, Any], tables: types.ModuleType
) -> list[Outcome]:
    out = []
    for row in result["claims"]:
        name = row["claim_id"]
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
            out.append(share(where, cell, row["recovery_pct"], RECOVERY_FORMULA, tables))
    return out


def _fulcrum(case: str, w: _Waterfall, result: dict[str, Any]) -> Outcome:
    where = _where(f"{FULCRUM} ({case})")
    cell = None if w.fulcrum is None else w.fulcrum[w.cols[case]]
    if cell is None or _plain(cell) in ("", *core.NOT_APPLICABLE):
        return where("not checked", stated=cell, reason=f"{_HEADING} states no fulcrum for {case}")
    if result["status"] != "complete":
        return where("not checked", stated=cell, reason=str(result.get("note")))
    found = result["fulcrum_claim_id"]
    said_none = _label(cell) in NO_FULCRUM
    agreed = said_none if found is None else _label(cell) == _label(found)
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
    return _judged(claim, tables)


def _case(case: str, w: _Waterfall, loaded: Loaded) -> list[Outcome]:
    result = None
    if w.ev[case] is None:
        reason = f"{_HEADING} states no {EV} for {case} (missing, not zero)"
    else:
        result = loaded.script.waterfall(w.ev[case], w.claims, w.costs)
        reason = str(result.get("note"))  # a cost without an amount stops the whole case
    if result is None or "claims" not in result:
        names = [f"Recovery: {c['claim_id']} ({case})" for c in w.claims]
        names += [f"{FULCRUM} ({case})", f"{RESIDUAL} ({case})"]
        return [_where(n)("not checked", reason=reason) for n in names]
    return [
        *_recoveries(case, w, result, loaded.tables),
        _fulcrum(case, w, result),
        _residual(case, w, result, loaded.tables),
    ]


def check(text: str, loaded: Loaded) -> list[Outcome]:
    """Recovery by claim, the fulcrum and the residual to equity in each enterprise-value case,
    recomputed by the script from the table's own claims, costs and enterprise values."""
    table = heading_table(text, WATERFALL_HEADING)
    try:
        if isinstance(table, str):
            raise _NotChecked(table)
        waterfall = _read(table, loaded.tables)
        return [o for case in CASES for o in _case(case, waterfall, loaded)]
    except _NotChecked as why:
        return [_where(WATERFALL_HEADING)("not checked", reason=str(why))]
    except ValueError as error:  # the script refuses: a claim named twice, a negative amount
        return [
            _where(WATERFALL_HEADING)(
                "not checked", reason=f"the script refused the table: {error}"
            )
        ]


core.register("CP-3", RECOVERY, check, None)  # owner decision pending: CP-3 is not asked for it
