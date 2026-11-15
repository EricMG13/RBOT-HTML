"""The enterprise value of each case in CP-3's `### Recovery waterfall` (harness:
`deploy_workflow.method_scripts`; the waterfall itself is `method_scripts_cp3`).

Owner, 2026-11-15: "1. yes 2. yes 3. yes". Each case's `Enterprise value` states its `EV multiple`,
`EV metric` and `EV basis`; it is recomputed as multiple x metric by CP-1C's own
`peer_statistics.implied_ev`. A basis that begins `CP-1C T4.10` (optionally followed by the method,
`EV/EBITDA`) claims to have copied CP-1C's implied EV range; only that leading token is read, never
the prose after it, so a basis that mentions T4.10 to set it aside is not a copy. For a copy, the
multiple CP-3 states is compared with T4.10's for the case (its Low, Median or High implied EV over
its borrower metric): a multiple needs no unit, and CP-3 may rightly apply it to another metric. A
T4.10 that states no figure for the case leaves the copy not checked; CP-3's own arithmetic still
stands or falls by itself.
"""

import re
import types
from dataclasses import dataclass

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    AMOUNT_STEP,
    ARCHIVE,
    Loaded,
    Outcome,
    Table,
    Upstream,
    _Claim,
    _judged,
    _label,
    _NotChecked,
    _plain,
    _Where,
    blank,
    column,
    figure,
    half,
    quotient_slack,
    register_table,
    said_none,
)

PEER_STATISTICS = ARCHIVE + "skills/cp-1c-peer-benchmark/scripts/peer_statistics.py"
EV, MULTIPLE, METRIC, BASIS = "Enterprise value", "EV multiple", "EV metric", "EV basis"
T410_CASES = {"Low": ("Low",), "Base": ("Median", "Base"), "High": ("High",)}
RATIO_STEP = 1e-9
EV_FORMULA = (
    "Enterprise value = EV multiple x EV metric (CP-1C's Implied EV formula; peer_statistics.py "
    "implied_ev, which gives none on a metric at or below zero)"
)
COPY_FORMULA = (
    "A case copied from CP-1C's T4.10 uses its multiple: T4.10's Low, Median or High implied EV "
    "over T4.10's borrower metric, as the CP-1C handoff CP-3 was sent states them"
)
_COPY = re.compile(r"^cp 1c t4\.10\b\W*(ev/ebitda|ev/revenue|tv/ebitda|tv/revenue)?")
_FIGURE = re.compile(r"\(?-?\d[\d,]*(?:\.\d+)?\)?")
_HEADING = "`### Recovery waterfall`"


@dataclass(frozen=True)
class Case:
    """One case's EV cells as written (None: the row is absent)."""

    name: str  # Low, Base or High
    ev: str
    multiple: str | None
    metric: str | None
    basis: str | None
    unit: str


def _where(figure_name: str) -> _Where:
    return _Where("CP-3", PEER_STATISTICS, figure_name, _HEADING)


def multiple_figure(cell: str, tables: types.ModuleType) -> tuple[float, int] | str:
    """A multiple as written: `8.5x`, `8.5×` or `8.5x (peer median)` is 8.5."""
    text = re.sub(r"\s*\([^)]*\)\s*$", "", _plain(cell))
    return figure(re.sub(r"\s*[x×]$", "", text, flags=re.IGNORECASE), tables)


def _stated(cell: str | None, tables: types.ModuleType) -> bool:
    return cell is not None and not blank(cell, tables)


def ev_figure(case: Case, loaded: Loaded) -> Outcome:
    """The case's EV against the method's own arithmetic: multiple x metric (CP-1C's script)."""
    where = _where(f"{EV} ({case.name})")
    tables = loaded.tables
    if not (_stated(case.multiple, tables) and _stated(case.metric, tables)):
        reason = f"the {EV} for {case.name} states no {MULTIPLE} and {METRIC} to recompute it from"
        return where("not checked", stated=case.ev, reason=reason)
    read_m = multiple_figure(str(case.multiple), tables)
    read_b = figure(str(case.metric), tables)
    if isinstance(read_m, str) or isinstance(read_b, str):
        unread = read_m if isinstance(read_m, str) else read_b
        return where("not checked", stated=case.ev, reason=str(unread))
    value = _implied(read_m[0], read_b[0])
    if value is None:
        why = f"{EV_FORMULA}; the {METRIC} {read_b[0]:g} is not above zero, so there is none"
        return where("disagreed", stated=case.ev, recomputed_label="Not Calculable", reason=why)
    slack = abs(read_m[0]) * half(read_b[1]) + abs(read_b[0]) * half(read_m[1])  # a product
    claim = _Claim(where, case.ev, value, AMOUNT_STEP, case.unit, EV_FORMULA, slack=slack)
    return _judged(claim, tables)


def _implied(multiple: float, metric: float) -> float | None:
    """CP-1C's script's implied EV for one multiple (its Low, Median and High all that one)."""
    peers = core._loaded(PEER_STATISTICS).script
    stats = {
        "statistics_including_outliers": dict.fromkeys(("minimum", "median", "maximum"), multiple)
    }
    implied = peers.implied_ev(
        {"borrower_metric": metric}, stats | {"meaningful_as_sector_multiple": True}
    )
    return None if implied is None else implied["median"]


# --- the copy from CP-1C's T4.10 ---------------------------------------------------------------


def _t410_row(table: Table, method: str | None, case: str, tables: types.ModuleType) -> list[str]:
    """The T4.10 row the copy names (by method), or the one row with a figure for the case."""
    if method is not None:
        rows = [r for r in table[1] if method in _label(r[0])]
    else:
        rows = [r for r in table[1] if not blank(_t410_cell(table, r, case)[0], tables)]
    if len(rows) != 1:
        named = f"`{method}` " if method else "with a figure for the case "
        raise _NotChecked(f"CP-1C's T4.10 has {len(rows) or 'no'} rows {named}")
    return rows[0]


def _t410_cell(table: Table, row: list[str], case: str) -> tuple[str, str]:
    """T4.10's implied EV for the case in the row, from its own column (`Low`, `Median` or `Base`,
    `High`) or the SKILL's combined `Implied EV/Low/Median/High` column."""
    for name in T410_CASES[case]:
        try:
            index, header = column(table, name, "CP-1C's T4.10")
            return row[index], header
        except _NotChecked:
            continue
    found = [i for i, h in enumerate(table[0]) if "low/median/high" in _label(h)]
    if len(found) != 1:
        raise _NotChecked(f"CP-1C's T4.10 has no `{T410_CASES[case][0]}` column")
    parts = [p.strip() for p in _plain(row[found[0]]).split("/")]
    order = ("Low", "Base", "High").index(case)
    return (parts[-3:][order] if len(parts) >= 3 else row[found[0]]), table[0][found[0]]


def _t410_multiple(
    text: str, method: str | None, case: str, tables: types.ModuleType
) -> tuple[float, float]:
    """T4.10's multiple for the case (its implied EV over its borrower metric) and the bound their
    displayed rounding puts on it; `_NotChecked` when T4.10 states none or cannot be read."""
    table = register_table(text, "T4.10")
    if isinstance(table, str):
        raise _NotChecked(f"CP-1C's handoff: {table}")
    row = _t410_row(table, method, case, tables)
    cell = _t410_cell(table, row, case)[0]
    if blank(cell, tables) or said_none(cell):
        raise _NotChecked(f"CP-1C's T4.10 states no figure for {case} (`{cell}`)")
    metrics = _FIGURE.findall(_plain(row[column(table, "Borrower Metric", "CP-1C's T4.10")[0]]))
    if len(metrics) != 1:
        raise _NotChecked("CP-1C's T4.10 borrower metric is not one figure")
    ev, metric = figure(core.bare(cell), tables), figure(metrics[0], tables)
    if isinstance(ev, str) or isinstance(metric, str) or metric[0] <= 0:
        raise _NotChecked("CP-1C's T4.10 implied EV or borrower metric is not read")
    return ev[0] / metric[0], quotient_slack(ev[0], half(ev[1]), metric[0], half(metric[1]))


def ev_copy(case: Case, loaded: Loaded, upstream: Upstream) -> Outcome | None:
    """When the case's basis begins `CP-1C T4.10`, its multiple against T4.10's for the case in
    the CP-1C handoff CP-3 was sent; None when the basis does not claim the copy."""
    claim = _COPY.match(_label(case.basis or ""))
    if claim is None:
        return None
    where = _where(f"{MULTIPLE} ({case.name}) from CP-1C T4.10")
    stated = case.multiple
    try:
        if "CP-1C" not in upstream:
            raise _NotChecked("CP-3 was not sent CP-1C's handoff, which the basis names")
        if not _stated(stated, loaded.tables):
            raise _NotChecked(f"the case states no {MULTIPLE} to compare with T4.10's")
        sent, slack = _t410_multiple(upstream["CP-1C"], claim[1], case.name, loaded.tables)
    except _NotChecked as why:
        return where("not checked", stated=stated, reason=str(why))
    text = re.sub(r"\s*\([^)]*\)\s*$", "", _plain(str(stated)))
    text = re.sub(r"\s*[x×]$", "", text, flags=re.IGNORECASE)
    copy = _Claim(where, text, sent, RATIO_STEP, "x", COPY_FORMULA, slack=slack)
    return _judged(copy, loaded.tables)


def outcomes(case: Case, loaded: Loaded, upstream: Upstream) -> list[Outcome]:
    """The case's EV: its basis owed, its arithmetic and, when copied, its multiple."""
    if blank(case.ev, loaded.tables) or said_none(case.ev):
        reason = f"CP-3 states no enterprise value can be supported for {case.name}: `{case.ev}`"
        return [_where(f"{EV} ({case.name})")("not checked", stated=case.ev, reason=reason)]
    if not _stated(case.basis, loaded.tables):
        why = (
            f"{_HEADING} states an {EV} for {case.name} with no {BASIS}: state the metric and "
            "period it values, the multiple or other basis, and where each came from (CP-1C "
            "T4.10, or the evidence you were given), or write the value `Not supplied: <reason>`."
        )
        return [_where(f"{BASIS} ({case.name})")("missing", stated=case.ev, reason=why)]
    copied = ev_copy(case, loaded, upstream)
    return [ev_figure(case, loaded), *([copied] if copied is not None else [])]
