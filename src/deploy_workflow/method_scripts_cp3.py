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
from deploy_workflow import method_scripts_cp3_ev as cp3_ev
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
    blank,
    currency_of,
    quotient_slack,
    scale_of,
    share,
)

RECOVERY = ARCHIVE + "skills/cp-4c-restructuring-fulcrum/scripts/recovery_waterfall.py"
WATERFALL_HEADING = "Recovery waterfall"
CASES = ("Low", "Base", "High")
WATERFALL_COLUMNS = ("Line", "Amount", *CASES, "Currency", "Scale")
EV, FULCRUM, RESIDUAL = "Enterprise value", "Fulcrum", "Residual to equity"
# No debt claim is the fulcrum: value covers all of them, or none recovers in part.
NO_FULCRUM = ("none", "no fulcrum", "n/a", "na", "not applicable", "equity", "nil")
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
    skipped: tuple[str, ...]  # rows the check does not read (a total, a subtotal), named


def _kind(line: str) -> tuple[str, str]:
    """(`claim` | `cost` | the row's label, the name after `Claim:` / `Cost:`)."""
    head, colon, rest = _plain(line).partition(":")
    if colon and _label(head) in ("claim", "cost"):
        return _label(head), rest.strip()
    return _label(line), ""


def _states_gap(cell: str) -> bool:
    """A unit cell that states a gap in the module's own wording (`Not supplied: <reason>`,
    `Not calculable: <reason>`), as the T3.3 every-row-states-a-gap check reads it. Twin of
    `_GAP_FORM` in method_scripts_completeness.py (not importable here: the layers forbid it)."""
    text = _plain(cell).casefold()
    return text.startswith(core.GAP_WORDS) or bool(
        re.match(r"(?:not calculable|not assessable|unavailable|not applicable)\s*:", text)
    )


def _unit(rows: list[list[str]], cols: dict[str, int]) -> str:
    """The table's one money unit; a row that states neither currency nor scale (`—`) takes it."""
    stating = [r for r in rows if _plain(r[cols["Currency"]]) not in ("", *core.NOT_APPLICABLE)]
    rows = stating or rows
    pairs = {(currency_of(r[cols["Currency"]]), scale_of(r[cols["Scale"]])) for r in rows}
    if len(pairs) != 1 or None in next(iter(pairs)):
        gaps = {_plain(c) for r in rows for c in (r[cols["Currency"]], r[cols["Scale"]])}
        gaps = {c for c in gaps if _states_gap(c)}
        if gaps:  # a stated gap (the module's own wording) is not a unit that differs
            left = {
                (currency_of(r[cols["Currency"]]), scale_of(r[cols["Scale"]]))
                for r in rows
                if not any(_states_gap(r[cols[c]]) for c in ("Currency", "Scale"))
            }
            if len(left) <= 1 and None not in next(iter(left), ()):
                raise _NotChecked(
                    f"{_HEADING} rows state a gap ({'; '.join(sorted(gaps))}), so recovery is "
                    "not recomputed"
                )
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
    skipped: list[str] = []
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
            if any("%" in row[cols[c]] for c in CASES):  # it may be a claim not marked `Claim:`
                raise _NotChecked(
                    f"{_HEADING} has a row the check does not read: `{row[cols['Line']]}`"
                )
            skipped.append(_plain(row[cols["Line"]]))
            continue
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
        tuple(skipped),
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


def _named(cell: str) -> str:
    """The claim a fulcrum cell names: a leading `Claim:` and a trailing note (after a dash, or
    in brackets) are not the name (`Debt (66.7%)`, `Debt - 66.7% recovery` name `Debt`)."""
    text = re.sub(r"^\s*claim\s*:\s*", "", _plain(cell), flags=re.IGNORECASE)
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text)
    return _label(re.split(r"\s+[-—–]\s+", text, maxsplit=1)[0])


def _fulcrum(case: str, w: _Waterfall, result: dict[str, Any]) -> Outcome:
    where = _where(f"{FULCRUM} ({case})")
    cell = None if w.fulcrum is None else w.fulcrum[w.cols[case]]
    if cell is None or _plain(cell) in ("", *core.NOT_APPLICABLE):
        return where("not checked", stated=cell, reason=f"{_HEADING} states no fulcrum for {case}")
    if result["status"] != "complete":
        return where("not checked", stated=cell, reason=str(result.get("note")))
    found, name = result["fulcrum_claim_id"], _named(cell)
    claims = {_named(c["claim_id"]) for c in w.claims}
    if name not in NO_FULCRUM and name not in claims:
        why = f"`{cell}` names no claim of the table and none of {', '.join(NO_FULCRUM)}"
        return where("not checked", stated=cell, reason=why)
    agreed = name in NO_FULCRUM if found is None else name == _named(found)
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


def _ev_case(case: str, w: _Waterfall) -> cp3_ev.Case:
    def cell(name: str) -> str | None:
        row = w.basis.get(name)
        return None if row is None else row[w.cols[case]]

    return cp3_ev.Case(case, w.ev_cells[case], cell(MULTIPLE), cell(METRIC), cell(BASIS), w.unit)


def _case(case: str, w: _Waterfall, loaded: Loaded, upstream: Upstream) -> list[Outcome]:
    result = None
    if w.ev[case] is None:
        reason = f"{_HEADING} states no {EV} for {case} (missing, not zero)"
    else:
        result = loaded.script.waterfall(w.ev[case], w.claims, w.costs)
        reason = str(result.get("note"))  # a cost without an amount stops the whole case
    values = cp3_ev.outcomes(_ev_case(case, w), loaded, upstream)
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


_TITLE = re.compile(r"^\s*(?:#{1,6}\s+(?P<heading>.*?)\s*#*|\*\*(?P<bold>.+?)\*\*\s*:?)\s*$")


def find_table(text: str) -> Table | str | None:
    """The waterfall table: under a heading (any level) or a bold line whose words include
    "recovery waterfall" (numbering and a trailing note aside), else the one table with its
    columns. None when there is none; why, when there are two or it is unread."""
    lines = core._unfenced(text)
    titles = []
    for i, line in enumerate(lines):
        found = _TITLE.match(line)
        if found and "recovery waterfall" in _label(found["heading"] or found["bold"] or ""):
            titles.append(i)
    if len(titles) > 1:
        return f"the handoff has {len(titles)} recovery waterfall headings"
    if titles:
        return core._table_after(lines, titles[0], _HEADING)
    wanted = {_label(c) for c in WATERFALL_COLUMNS}
    headers = [
        i
        for i, line in enumerate(lines)
        if line.lstrip().startswith("|") and wanted <= {_label(c) for c in core._cells(line)}
    ]
    if len(headers) > 1:
        return f"the handoff has {len(headers)} tables with the waterfall's columns"
    return core._table_after(lines, headers[0] - 1, _HEADING) if headers else None


def check(text: str, loaded: Loaded, upstream: Upstream) -> list[Outcome]:
    """Each case's enterprise value (its basis, its arithmetic and its copy from CP-1C's T4.10),
    then recovery by claim, the fulcrum and the residual to equity, recomputed by the scripts from
    the table's own rows. An absent table is sent back unless CP-3 stopped at its gate."""
    table = find_table(text)
    if table is None:
        if core.blocked(text):
            return [_where(WATERFALL_HEADING)("not checked", reason="CP-3 stopped at its gate")]
        return [_where(WATERFALL_HEADING)("missing", reason=MISSING_TABLE)]
    try:
        if isinstance(table, str):
            raise _NotChecked(table)
        waterfall = _read(table, loaded.tables)
        skipped = [
            _where(f"Row: {name}")("not checked", reason="a row the check does not read")
            for name in waterfall.skipped
        ]
        return [*skipped, *(o for case in CASES for o in _case(case, waterfall, loaded, upstream))]
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
    "claim, senior first, its claim in Amount and its recovery % in each case (claims that rank "
    "equally share one row naming them all); `Fulcrum` (the claim, or None); `Residual to "
    "equity`. Where you were sent CP-1C's T4.10, the cases are its Low, Median and High implied "
    "EV, each basis beginning `CP-1C T4.10 EV/EBITDA` (or its method); "
    "otherwise state your own cases with their basis from the evidence you were given. Where no "
    f"enterprise value can be supported, write each `{EV}` cell `Not supplied: <reason>`: that is "
    "recorded, not refused. An implied EV from peer multiples is indicative, not a valuation: "
    "say in your limitations that the recoveries carry that limitation. A cell that does not "
    "apply is `—`. A figure that disagrees is sent back for repair, and so is a missing table.\n\n"
)
# Owner, 2026-11-15: "1. yes 2. yes 3. yes" (ruling 2026-11-15-method-script-checks.md).
core.register("CP-3", RECOVERY, check, CP3_NOTE)
