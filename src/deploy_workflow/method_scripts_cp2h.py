"""CP-2H's method script, `covenant_headroom.py` (`trigger_headroom`), run on T2R.4 (harness:
`deploy_workflow.method_scripts`).

The SKILL: the script "owns T2R.4 signed trigger headroom via its `trigger_headroom` entry point.
The max-ratio vs min-ratio direction comes from the register's own `trigger direction` column —
required, never inferred". REF_CP-2H_C: "A maximum leverage trigger and a minimum coverage trigger
require different headroom formulas"; "Where the agency supplies a range rather than a hard
threshold, show distance to both bounds"; qualitative triggers get no numerical headroom. T2R.4's
columns: `agency; rating type; trigger direction; metric; threshold; case/period value; headroom;
status`.

Per row: the direction is passed to the script's own `normalise_test_type` as written, or its first
word (`maximum (leverage)`), never guessed; `upgrade`, `downgrade` and the timing words
`maintenance` and `incurrence` say nothing about a ceiling or a floor, so such a row is not checked.
The threshold is one figure, or two for a range (`5.0x-5.5x`, `5.0x to 5.5x`); a comparator (`>`)
and a year are not figures. The case/period value may hold one figure or several cases (`5.2x /
6.1x`); headroom and status are read with as many parts, each compared with its case. A stated
headroom against a range agrees with the distance to either bound, and two stated figures each with
one. Status is compared when it starts with Compliant, At threshold or Breach(ed), and not when the
recomputed headroom is within the inputs' rounding of zero.

Not checked by design: whether a breach is sustained (the script needs the agency's observation
window, which no column holds), qualitative triggers (words, not figures).
"""

import re
import types
from dataclasses import dataclass, replace
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    Loaded,
    Outcome,
    Status,
    Upstream,
    _Claim,
    _judged,
    _label,
    _NotChecked,
    _plain,
    _Where,
    blank,
    column,
    currency_of,
    figure,
    half,
    register_table,
    scale_of,
)
from deploy_workflow.method_scripts_cp4 import COVENANT_HEADROOM, HEADROOM_STEP, TIMING_ONLY

COLUMNS = ("trigger direction", "metric", "threshold", "case/period value", "headroom", "status")
NO_DIRECTION = (*TIMING_ONLY, "upgrade", "downgrade")
STATUSES = {"compliant": "Compliant", "at threshold": "At threshold", "breach": "Breached"}
HEADROOM_FORMULA = (
    "Headroom = threshold - value for a maximum (max-ratio) trigger, value - threshold for a "
    "minimum (min-ratio) trigger, to each bound of a range; positive is Compliant, zero At "
    "threshold, negative Breached against the binding bound (REF_CP-2H_C; covenant_headroom.py "
    "trigger_headroom)"
)
_NUMBER = re.compile(r"\(?[-−]?\d[\d,]*(?:\.\d+)?\)?\s*(?:[x×%]|bps)?", re.IGNORECASE)
_RANGE = re.compile(r"(?<=[\d%x×])\s*[-–—]\s*(?=\d)")
_YEAR = re.compile(r"(?<![\d,.])(?:FY|CY|LTM|H[12]|Q[1-4]\s*)?(?:19|20)\d{2}[A-Z]?(?![\d,.])")
CP2H_NOTE = (
    "Python checks T2R.4 after you answer, with the method's own `covenant_headroom.py` "
    "(`trigger_headroom`; you cannot run it): each quantitative trigger's signed Headroom "
    "(maximum: threshold - value; minimum: value - threshold; to each bound of a range) and its "
    "Status (Compliant, At threshold, Breached). So write trigger direction as `maximum` or "
    "`minimum` (never inferred: a row without one is not checked) and threshold, value and "
    "headroom in one unit (`5.0x`); several cases in one cell are separated by ` / ` in the "
    "same order in Headroom and Status. A figure that disagrees is sent back for repair; one "
    "whose input is missing is not checked, never read as zero.\n\n"
)


def _where(figure_name: str) -> _Where:
    return _Where("CP-2H", COVENANT_HEADROOM, figure_name, "T2R.4")


@dataclass(frozen=True)
class _Figure:
    value: float
    places: int
    unit: str  # `x`, `%` or `bps` as written; `` for a bare figure


def _figures(cell: str, tables: types.ModuleType) -> list[_Figure]:
    """Every figure a cell states, a year and a comparator aside; `_NotChecked` for none read."""
    text = _YEAR.sub(" ", core._plain(cell)).replace("−", "-")
    text = _RANGE.sub(" to ", text)  # `5.0x-5.5x` is a range, not 5.0 and -5.5
    out = []
    for token in _NUMBER.findall(text):
        unit = re.search(r"([x×%]|bps)\s*$", token, re.IGNORECASE)
        bare = re.sub(r"\s*(?:[x×%]|bps)\s*$", "", token, flags=re.IGNORECASE).strip()
        read = figure(bare, tables)
        if isinstance(read, str):
            raise _NotChecked(read)
        kind = "" if unit is None else {"×": "x"}.get(unit[1], unit[1].casefold())
        out.append(_Figure(read[0], read[1], kind))
    return out


def _direction(cell: str, loaded: Loaded) -> str:
    text = _plain(cell)
    if blank(text, loaded.tables):
        raise _NotChecked("T2R.4 states no trigger direction, and the script never infers one")
    reason = ""
    for candidate in (text, re.split(r"[\s(]", text, maxsplit=1)[0]):
        if _label(candidate) in NO_DIRECTION:
            raise _NotChecked(f"trigger direction `{cell}` does not say ceiling or floor")
        try:
            return str(loaded.script.normalise_test_type(candidate, "T2R.4"))
        except ValueError as error:
            reason = str(error)
    raise _NotChecked(f"the script does not read trigger direction `{cell}`: {reason}")


def _parts(cell: str) -> list[str]:
    return [p.strip() for p in core._plain(cell).split(" / ")] if " / " in cell else [cell]


def _unit_kind(figures: list[_Figure], cells: list[str]) -> str:
    """The one unit every figure is in; `_NotChecked` when they differ or a scale differs."""
    kinds = {f.unit for f in figures} - {""}
    if len(kinds) > 1:
        raise _NotChecked(f"threshold, value and headroom are in different units: {sorted(kinds)}")
    money = {(currency_of(c), scale_of(c)) for c in cells}
    if any(m != (None, None) for m in money) and len(money) != 1:
        raise _NotChecked("threshold, value and headroom state different currencies or scales")
    return kinds.pop() if kinds else "x"


@dataclass(frozen=True)
class _Row:
    metric: str
    direction: str
    thresholds: list[_Figure]
    values: list[_Figure]
    headrooms: list[str]  # per case, as written
    statuses: list[str]
    unit: str


def _read(row: list[str], cols: dict[str, int], loaded: Loaded) -> _Row:
    tables = loaded.tables
    cells = {name: row[cols[name]] for name in COLUMNS}
    for name in ("threshold", "case/period value"):
        if blank(cells[name], tables):
            raise _NotChecked(f"T2R.4 states no {name} (missing, not zero)")
    direction = _direction(cells["trigger direction"], loaded)
    thresholds = _figures(cells["threshold"], tables)
    values = _figures(cells["case/period value"], tables)
    if not 1 <= len(thresholds) <= 2 or not values:
        raise _NotChecked("the threshold is not one figure or a range of two, or no value is read")
    headrooms, statuses = [cells["headroom"]], [cells["status"]]
    if len(values) > 1:  # several cases: each cell holds one part per case, in order
        headrooms, statuses = _parts(cells["headroom"]), _parts(cells["status"])
        if len(headrooms) != len(values):
            raise _NotChecked("the cases in the value cell and the headroom cell do not pair up")
    every = [*thresholds, *values]
    unit = _unit_kind(every, [cells["threshold"], cells["case/period value"], cells["headroom"]])
    return _Row(_plain(cells["metric"]), direction, thresholds, values, headrooms, statuses, unit)


def _trigger(r: _Row, loaded: Loaded) -> dict[str, Any]:
    bounds: dict[str, Any] = (
        {"threshold": r.thresholds[0].value}
        if len(r.thresholds) == 1
        else {"threshold_lower": min(f.value for f in r.thresholds)}
        | {"threshold_upper": max(f.value for f in r.thresholds)}
    )
    cases = [
        {"case": f"case {i + 1}", "period": f"case {i + 1}", "value": f.value}
        for i, f in enumerate(r.values)
    ]
    result: dict[str, Any] = loaded.script.trigger_headroom(
        {"trigger": r.metric, "trigger_direction": r.direction, "cases": cases} | bounds
    )
    return result


def _headroom(
    where: _Where, cell: str, found: tuple[dict[str, Any], float], r: _Row, loaded: Loaded
) -> Outcome:
    """One case's stated headroom against the script's (``found``: its period and the inputs'
    rounding bound)."""
    period, slack = found
    if blank(cell, loaded.tables):
        return where("not checked", stated=cell, reason="T2R.4 states no headroom here")
    try:
        stated = _figures(cell, loaded.tables)
    except _NotChecked as error:
        return where("not checked", stated=cell, reason=str(error))
    if (
        not stated
        or len(stated) > len(period["headroom"])
        or any(s.unit not in ("", r.unit) for s in stated)
    ):
        why = f"`{cell}` is not {len(period['headroom'])} figure(s) in {r.unit}"
        return where("not checked", stated=cell, reason=why)
    bounds = list(period["headroom"].values())
    outcomes = []
    for s in stated:
        nearest = min(bounds, key=lambda b: abs(b - s.value))  # a range: either bound's distance
        text = f"{s.value:.{s.places}f}"
        claim = _Claim(where, text, nearest, HEADROOM_STEP, r.unit, HEADROOM_FORMULA)
        outcomes.append(_judged(replace(claim, slack=slack), loaded.tables))
    worst = next((o for o in outcomes if o.status != "agreed"), outcomes[0])
    return worst


def _status(where: _Where, cell: str, period: dict[str, Any], slack: float) -> Outcome:
    stated = _label(cell)
    word = next((w for w in STATUSES if stated.startswith(w)), None)
    if word is None:
        why = f"Status `{cell}` is none of Compliant, At threshold, Breached"
        return where("not checked", stated=cell, reason=why)
    found = str(period["status"])
    if found != STATUSES[word] and abs(period["binding_headroom"]) <= slack:
        why = (
            f"the recomputed headroom {period['binding_headroom']:g} is within the inputs' "
            f"rounding ({slack:g}) of zero, so they cannot settle `{cell}` against {found}"
        )
        return where("not checked", stated=cell, recomputed_label=found, reason=why)
    status: Status = "agreed" if found == STATUSES[word] else "disagreed"
    return where(status, stated=cell, recomputed_label=found, reason=HEADROOM_FORMULA)


def _row(row: list[str], cols: dict[str, int], loaded: Loaded) -> list[Outcome]:
    name = f"{_plain(row[cols['metric']])}"
    try:
        r = _read(row, cols, loaded)
        result = _trigger(r, loaded)
    except _NotChecked as error:
        why = str(error)
        return [_where(f"{f}: {name}")("not checked", reason=why) for f in ("Headroom", "Status")]
    except ValueError as error:  # the script refuses the inputs
        why = f"the script refused the inputs: {error}"
        return [_where(f"{f}: {name}")("not checked", reason=why) for f in ("Headroom", "Status")]
    out = []
    for i, period in enumerate(result["periods"]):
        label = name if len(result["periods"]) == 1 else f"{name} (case {i + 1})"
        slack = half(r.values[i].places) + max(half(t.places) for t in r.thresholds)
        headroom = r.headrooms[i] if i < len(r.headrooms) else ""
        status = r.statuses[i] if i < len(r.statuses) else ""
        out.append(_headroom(_where(f"Headroom: {label}"), headroom, (period, slack), r, loaded))
        out.append(_status(_where(f"Status: {label}"), status, period, slack))
    return out


def check(text: str, loaded: Loaded, _upstream: Upstream) -> list[Outcome]:
    """Each T2R.4 trigger's signed headroom and status, recomputed by the script from its row."""
    table = register_table(text, "T2R.4")
    try:
        if isinstance(table, str):
            raise _NotChecked(table)
        cols = {name: column(table, name, "T2R.4")[0] for name in COLUMNS}
    except _NotChecked as error:
        return [_where("Headroom: all")("not checked", reason=str(error))]
    return [o for row in table[1] for o in _row(row, cols, loaded)]


core.register("CP-2H", COVENANT_HEADROOM, check, CP2H_NOTE)
