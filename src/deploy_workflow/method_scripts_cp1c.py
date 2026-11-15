"""CP-1C's method script, `peer_statistics.py`, run on T4.6 and T4.10 (harness:
`deploy_workflow.method_scripts`).

The SKILL names the script as the owner of "peer minimum/maximum/range/median/quartiles/average
... under CP-1C's per-statistic minimum-N gates (median 3, quartile 4, average 5, nothing below
2), the with- and without-outlier versions, implied EV Low/Median/High". Step 04D builds T4.6
(`Metric | Borrower Value | Peer Avg | Median | Min | Max | Q1 | Q3 | N | Borrower Position`, or the
SKILL's combined `Peer Avg/Median/Min/Max` and `Q1/Q3`) from the peer rows of T4.3 to T4.5; the
trading and transaction comps (T4.8, T4.9) carry the multiples. Step 06C: "Low = minimum peer
multiple x borrower metric; Median = median ...; High = maximum ...".

T4.6, per metric: the peer values are the cells of the benchmark column named as the metric (an
abbreviation such as `Net Lev` read as `Net Leverage`; a joined column such as
`Total/Net/Sr Sec Leverage` read part by part when every cell holds as many figures), each with its
row's Comp Status and Calc Status (the script's closed sets) and T4.7's outlier flag. The
borrower's own row is left out (an entity marked `borrower` or named as the front matter's issuer,
or, failing that, the row stating the Borrower Value). The script runs on that set with and without
the flagged outliers; the version whose N is the N T4.6 states is compared, and if neither is, or
two differ, nothing is (the peer set cannot be identified). Peer Avg, Median, Min and Max are
compared; a figure stated where the script's gate gives none disagrees. Only metrics written with a
unit (`x` or `%`, in the cell or the column header) are compared: an absolute amount's scale is not
stated in T4.6.

T4.10, per row whose Method names a T4.6 multiple: Low, Median and High against T4.6's Min, Median
and Max multiple times the row's one borrower-metric figure (the script's `implied_ev`).

Not checked by design: Q1 and Q3 (the method names no quantile convention; the script's is
inclusive, owner's decision), N itself (it selects the peer set), standard deviation and range
(not T4.6 columns), Borrower Position (words).
"""

import re
import types
from dataclasses import dataclass, replace
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow import method_scripts_cp3_ev as cp3_ev
from deploy_workflow.method_scripts import (
    AMOUNT_STEP,
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
    currency_of,
    figure,
    half,
    register_table,
    said_none,
    scale_of,
)

PEER_STATISTICS = cp3_ev.PEER_STATISTICS
BENCHMARKS = ("T4.3", "T4.4", "T4.5", "T4.8", "T4.9")
STATS = {"Avg": "average", "Median": "median", "Min": "minimum", "Max": "maximum"}
EV_CASES = {"Low": "Min", "Base": "Median", "High": "Max"}  # T4.10 case -> T4.6 statistic
ABBREVIATIONS = {
    "lev": "leverage",
    "rev": "revenue",
    "int": "interest",
    "adj": "adjusted",
    "sr": "senior",
    "sec": "secured",
    "cov": "coverage",
}
NOT_METRICS = ("entity", "txn name", "period", "currency", "source", "date", "type", "metric def")
STATS_FORMULA = (
    "Peer statistics over the comparable peers T4.3 to T4.5, T4.8 and T4.9 state for the metric "
    "(Comp Status Comparable or Comparable with Limitations; Calc Status not Provisional), with or "
    "without T4.7's outliers as T4.6's N says, under the method's gates: median 3, average 5, "
    "none below 2 (peer_statistics.py)"
)
EV_FORMULA = (
    "Implied EV Low / Median / High = T4.6's Min / Median / Max peer multiple x the borrower "
    "metric (REF_CP-1C_06C; peer_statistics.py implied_ev)"
)
QUARTILES = (
    "the method names no quantile convention (the script's is inclusive, Excel PERCENTILE.INC): "
    "the owner's decision"
)
CP1C_NOTE = (
    "Python checks T4.6 and T4.10 after you answer, with the method's own `peer_statistics.py` "
    "(you cannot run it): each metric's Peer Avg, Median, Min and Max from the peer rows of T4.3 "
    "to T4.5, T4.8 and T4.9 (their Comp Status and Calc Status, T4.7's outliers) under the "
    "method's minimum-N gates, and each T4.10 Low, Median and High as T4.6's Min, Median and Max "
    "multiple times the borrower metric. So name each T4.6 metric as its column is named, write "
    "each value with its unit (`11.5x`, `24.0%`), mark the borrower's own row `(borrower)`, and "
    "state as N the peers the statistics use. A figure that disagrees is sent back for repair; "
    "one whose input is missing is not checked, never read as zero.\n\n"
)


def _key(name: str) -> str:
    """A metric name as compared: a unit in brackets aside, abbreviations spelt out."""
    text = re.sub(r"\s*\((?:x|%|times|percent)\)\s*$", "", _label(name))
    return " ".join(ABBREVIATIONS.get(w, w) for w in text.split())


def _unit(cell: str, header: str) -> str:
    """`x` or `%` as the cell or its column header writes it; `` for neither."""
    text = _plain(cell).rstrip(") ")
    if text.endswith("%") or "(%)" in header:
        return "%"
    if re.search(r"\d\s*[x×]$", text, re.IGNORECASE) or re.search(r"\((?:x|×)\)", header):
        return "x"
    return ""


def _number(cell: str, tables: types.ModuleType) -> tuple[float, int] | str:
    text = re.sub(r"\s*[x×%]\s*(?=\)?$)", "", _plain(cell), flags=re.IGNORECASE)
    return figure(text, tables)


@dataclass(frozen=True)
class _Peer:
    entity: str
    cell: str
    unit: str
    comparability: str
    status: str


@dataclass(frozen=True)
class _Series:
    """One metric's cells in a benchmark register."""

    register: str
    peers: tuple[_Peer, ...]


def _status_columns(header: list[str]) -> tuple[int | None, int | None]:
    comp = [i for i, h in enumerate(header) if "comp" in _label(h).split("/")[-1]]
    calc = [i for i, h in enumerate(header) if _label(h).startswith("calc")]
    return (comp[0] if len(comp) == 1 else None), (calc[0] if len(calc) == 1 else None)


def _statuses(row: list[str], comp: int | None, calc: int | None) -> tuple[str, str]:
    """(comparability, calculation status); a joined `Calc/Comp Status` cell split in two."""
    if comp is None:
        return "", ""
    cell = _plain(row[comp])
    if comp == calc and "/" in cell:
        first, _, second = cell.partition("/")
        return second.strip(), first.strip()
    return cell, _plain(row[calc]) if calc is not None else ""


def _columns(table: Table) -> dict[str, list[tuple[int, int | None, str]]]:
    """Metric key -> (column, part or None, header) for every column and joined part."""
    header, rows = table
    out: dict[str, list[tuple[int, int | None, str]]] = {}
    for i, name in enumerate(header):
        if _label(name).startswith(NOT_METRICS) or "status" in _label(name):
            continue
        out.setdefault(_key(name), []).append((i, None, name))
        parts = [p.strip() for p in _plain(name).split("/")]
        cells = [_plain(r[i]) for r in rows if _plain(r[i])]
        if len(parts) > 1 and cells and all(len(c.split("/")) == len(parts) for c in cells):
            tail = parts[-1].split()[-1]
            for n, part in enumerate(parts):
                for spelt in {part, f"{part} {tail}"}:
                    out.setdefault(_key(spelt), []).append((i, n, name))
    return out


def _series(text: str, metric: str) -> _Series | str:
    """The one benchmark column that holds the metric, or why none is read."""
    found: list[_Series] = []
    for ident in BENCHMARKS:
        table = register_table(text, ident)
        if isinstance(table, str):
            continue
        comp, calc = _status_columns(table[0])
        for at, part, header in _columns(table).get(_key(metric), []):
            peers = []
            for row in table[1]:
                pieces = _plain(row[at]).split("/")  # an empty or short cell: no value here
                cell = row[at] if part is None else (pieces[part] if part < len(pieces) else "")
                peers.append(
                    _Peer(_plain(row[0]), cell, _unit(cell, header), *_statuses(row, comp, calc))
                )
            found.append(_Series(ident, tuple(peers)))
    if len(found) != 1:
        return f"{'no' if not found else len(found)} benchmark columns hold `{metric}`"
    return found[0]


@dataclass(frozen=True)
class _Stated:
    """One T4.6 row as written."""

    metric: str
    borrower: str
    stats: dict[str, str]  # Avg, Median, Min, Max -> cell
    n: str


def _t46_rows(text: str) -> list[_Stated] | str:
    table = register_table(text, "T4.6")
    if isinstance(table, str):
        return table
    header = [_label(h) for h in table[0]]

    def at(*names: str) -> int | None:
        found = [i for i, h in enumerate(header) if h in names]
        return found[0] if len(found) == 1 else None

    joined = next((i for i, h in enumerate(header) if "avg/median/min/max" in h), None)
    own = {s: at(f"peer {s.casefold()}", s.casefold()) for s in STATS}
    own["Avg"] = own["Avg"] if own["Avg"] is not None else at("peer average", "average")
    metric, borrower, n = at("metric"), at("borrower value"), at("n")
    if metric is None or n is None or (joined is None and None in own.values()):
        return "T4.6 has no Metric, N or peer statistic columns"
    rows = []
    for row in table[1]:
        if joined is not None:
            parts = [p.strip() for p in _plain(row[joined]).split("/")]
            cells = dict(zip(STATS, parts, strict=False)) if len(parts) == 4 else {}
        else:
            cells = {s: row[i] for s, i in own.items() if i is not None}
        cell = row[borrower] if borrower is not None else ""
        rows.append(_Stated(_plain(row[metric]), cell, cells, row[n]))
    return rows


def _issuer(text: str) -> set[str]:
    """The front matter's issuer name and id, as compared."""
    head = text.lstrip("﻿").split("\n---", 1)[0] if text.lstrip().startswith("---") else ""
    found = re.findall(r"^issuer_(?:name|id):\s*[\"']?(.+?)[\"']?\s*$", head, re.MULTILINE)
    return {_label(f) for f in found if f.strip()}


# The script's closed sets (REF_CP-1C_STEPS label taxonomies), longest first so that `Comparable
# with Limitations` is not read as `Comparable`.
COMPARABILITY: tuple[str, ...] = (
    "comparable with limitations",
    "not comparable",
    "insufficient information",
)
COMPARABILITY += ("comparable",)
CALCULATION: tuple[str, ...] = (
    "reported",
    "calculated",
    "derived",
    "provisional",
    "not comparable",
)
CALCULATION += ("insufficient information",)


def _closed(cell: str, words: tuple[str, ...]) -> str:
    """The closed-set word a status cell starts with (`Comparable (size)` is `Comparable`); the
    cell as written when it starts with none, for the script to refuse."""
    text = _label(cell)
    return next((w for w in words if re.match(rf"{re.escape(w)}\b", text)), _plain(cell))


def _value(cell: str) -> str | None:
    """A peer value as the script takes it: its unit aside; None for a gap or a null word (the
    script leaves the peer out of the statistics, never as zero)."""
    text = _plain(cell)
    if (
        not text
        or text in core.NOT_APPLICABLE
        or said_none(text)
        or text.casefold().startswith(core.GAP_WORDS)
    ):
        return None
    return re.sub(r"\s*[x×%]\s*(?=\)?$)", "", text, flags=re.IGNORECASE)


def _payloads(
    series: _Series, stated: _Stated, text: str, outliers: set[str]
) -> list[list[dict[str, Any]]]:
    """The candidate peer sets: without the marked borrower row, and, if none is marked, without
    the row stating the Borrower Value."""
    issuer = _issuer(text)

    def marked(entity: str) -> bool:
        name = _label(entity)
        return "borrower" in name or name in issuer

    def payload(peers: list[_Peer]) -> list[dict[str, Any]]:
        return [
            {
                "name": p.entity,
                "value": _value(p.cell),
                "comparability": _closed(p.comparability, COMPARABILITY),
                "calculation_status": _closed(p.status, CALCULATION) or None,
                "outlier": _label(p.entity) in outliers,
            }
            for p in peers
        ]

    peers = list(series.peers)
    if any(marked(p.entity) for p in peers):
        return [payload([p for p in peers if not marked(p.entity)])]
    same = [p for p in peers if _label(core.bare(p.cell)) == _label(core.bare(stated.borrower))]
    return [payload(peers), *([payload([p for p in peers if p not in same])] if same else [])]


def _outliers(text: str, metric: str) -> set[str]:
    table = register_table(text, "T4.7")
    if isinstance(table, str):
        return set()
    header = [_label(h) for h in table[0]]
    if "entity" not in header or "metric" not in header:
        return set()
    e, m = header.index("entity"), header.index("metric")
    return {_label(r[e]) for r in table[1] if _key(r[m]) == _key(metric)}


def _statistics(stated: _Stated, text: str, loaded: Loaded) -> tuple[dict[str, Any], float, str]:
    """The script's statistics for the peer set T4.6's N identifies, the inputs' largest rounding
    and their unit; `_NotChecked` when the set cannot be identified."""
    series = _series(text, stated.metric)
    if isinstance(series, str):
        raise _NotChecked(series)
    n = figure(stated.n, loaded.tables)
    if isinstance(n, str):
        raise _NotChecked(f"T4.6 states no N for `{stated.metric}` ({n})")
    found: list[dict[str, Any]] = []
    for peers in _payloads(series, stated, text, _outliers(text, stated.metric)):
        try:
            result = loaded.script.analyse({"metric": stated.metric, "peers": peers})
        except ValueError as error:  # a status outside the closed sets, an unread figure
            raise _NotChecked(f"the script refused the peer rows: {error}") from error
        for key in ("statistics_including_outliers", "statistics_excluding_outliers"):
            version = result.get(key)
            if version is not None and version["n"] == n[0] and version not in found:
                found.append(version)
    if len(found) != 1:
        why = "no" if not found else f"{len(found)} different"
        raise _NotChecked(f"{why} peer sets in {series.register} give T4.6's N of {stated.n}")
    units = {p.unit for p in series.peers if not blank(p.cell, loaded.tables)}
    rounding = [_cell_half(p.cell, loaded.tables) for p in series.peers]
    return found[0], max(rounding, default=0.0), units.pop() if len(units) == 1 else ""


def _cell_half(cell: str, tables: types.ModuleType) -> float:
    read = _number(cell, tables)
    return 0.0 if isinstance(read, str) else half(read[1])


def _states_number(cell: str) -> bool:
    """Whether a statistic cell states a figure: it starts with one, its bracketed notes aside
    (`Suppressed (N=4)`, `N<5` and `Not calculated: N below 5` state none; `11.25x (indicative
    only)` states one)."""
    text = re.sub(r"^([(\s]*)[–−]", r"\1-", _plain(cell))
    return bool(re.match(r"^\s*\(?\s*[-+]?\s*\d", text))


def _stat(
    where: _Where,
    cell: str,
    found: tuple[float | None, int],
    basis: tuple[str, float],
    tables: types.ModuleType,
) -> Outcome:
    """One stated statistic against the script's (``found``: its value and N; ``basis``: the
    peer values' unit and largest rounding)."""
    (value, n), (unit, slack) = found, basis
    if blank(cell, tables) or not _states_number(cell):  # a word, never a disagreement
        return _worded(where, cell, value, n)
    if _unit(cell, "") not in (unit, "") or not unit:
        why = f"`{cell}` and its peer values are not both in `x` or `%`"
        return where("not checked", stated=cell, reason=why)
    if value is None:
        why = f"{STATS_FORMULA}; at N={n} the method's gate gives none"
        return where("disagreed", stated=cell, recomputed_label="Not Calculable", reason=why)
    text = re.sub(r"\s*[x×%]\s*$", "", _plain(cell), flags=re.IGNORECASE)
    claim = _Claim(where, text, value, 1e-9, unit, STATS_FORMULA)
    return _judged(replace(claim, slack=slack), tables)


def _worded(where: _Where, cell: str, value: float | None, n: int) -> Outcome:
    """A statistic cell that states no figure: a null word agrees where the gate gives none; any
    other word, or a null word where the script computes one, is not checked (the method may
    have suppressed it)."""
    if value is None and said_none(cell):
        return where("agreed", stated=cell, reason=STATS_FORMULA)
    if value is None:
        why = f"`{cell}` states no figure where the method's gate gives none at N={n}"
    else:
        why = f"`{cell}` states no figure where the script computes one"
    return where("not checked", stated=cell, recomputed=value, reason=why)


def _t46(stated: _Stated, text: str, loaded: Loaded) -> list[Outcome]:
    def where(stat: str) -> _Where:
        return _Where("CP-1C", PEER_STATISTICS, f"Peer {stat}: {stated.metric}", "T4.6")

    quartiles = [where(q)("not checked", reason=QUARTILES) for q in ("Q1", "Q3")]
    if len(stated.stats) != 4:
        why = "the joined peer statistic cell is not four figures"
        return [*(where(s)("not checked", reason=why) for s in STATS), *quartiles]
    try:
        version, slack, unit = _statistics(stated, text, loaded)
    except _NotChecked as error:
        cause = str(error)
        return [
            *(where(s)("not checked", stated=stated.stats[s], reason=cause) for s in STATS),
            *quartiles,
        ]
    return [
        *(
            _stat(
                where(s), stated.stats[s], (version[k], version["n"]), (unit, slack), loaded.tables
            )
            for s, k in STATS.items()
        ),
        *quartiles,
    ]


# --- T4.10 -------------------------------------------------------------------------------------

_YEAR = re.compile(r"(?<![\d,.])(?:FY|CY|LTM|Q[1-4]\s*)?(?:19|20)\d{2}(?![\d,.])", re.IGNORECASE)


def _borrower_metric(cell: str, tables: types.ModuleType) -> tuple[float, int]:
    text = _YEAR.sub(" ", _plain(cell))
    found = cp3_ev._FIGURE.findall(text)
    if len(found) != 1:
        raise _NotChecked(f"the borrower metric `{cell}` is not one figure")
    read = figure(found[0], tables)
    if isinstance(read, str):
        raise _NotChecked(read)
    return read


# Words a T4.10 Method adds to the multiple it applies (`EV/EBITDA trading comps (T4.8)`);
# a qualifier that changes the multiple (`transaction`, `ex-outliers`) is kept.
_GENERIC = re.compile(
    r"\b(?:trading|comps?|comparables?|peer|peers|multiples?|method|implied ev)\b"
)


def _method(cell: str) -> str:
    """The multiple a T4.10 Method names, as compared with T4.6's metric keys."""
    text = re.sub(r"\(\s*t4\.\d+\s*\)", " ", _key(cell))
    return re.sub(r"\s+", " ", _GENERIC.sub(" ", text)).strip()


def _t410(text: str, rows: list[_Stated], loaded: Loaded) -> list[Outcome]:
    table = register_table(text, "T4.10")
    if isinstance(table, str):
        return []
    by_metric = {_key(r.metric): r for r in rows}
    out = []
    for row in table[1]:
        method = _method(row[0])
        named = [m for m in by_metric if m and m == method]
        stated = by_metric[named[0]] if len(named) == 1 else None
        for case in EV_CASES:
            where = _Where(
                "CP-1C", PEER_STATISTICS, f"Implied EV {case}: {_plain(row[0])}", "T4.10"
            )
            out.append(_ev(where, case, (table, row), stated, loaded))
    return out


def _ev(
    where: _Where, case: str, t410: tuple[Table, list[str]], stated: _Stated | None, loaded: Loaded
) -> Outcome:
    """One T4.10 case against T4.6's multiple for it times the row's borrower metric."""
    (table, row), tables = t410, loaded.tables
    try:
        cell, header = cp3_ev._t410_cell(table, row, case)
        if stated is None:
            raise _NotChecked("the Method names no single T4.6 multiple")
        multiple = stated.stats.get(EV_CASES[case], "")
        if blank(cell, tables) or said_none(cell) or blank(multiple, tables) or said_none(multiple):
            raise _NotChecked(f"no implied EV or T4.6 multiple is stated for {case}")
        metric_cell = row[core.column(table, "Borrower Metric", "T4.10")[0]]
        metric = _borrower_metric(metric_cell, tables)
        if _unit(multiple, "") != "x":
            raise _NotChecked(f"T4.6's `{stated.metric}` {EV_CASES[case]} is not a multiple (`x`)")
        m = _number(multiple, tables)
        if isinstance(m, str):
            raise _NotChecked(m)
        units = {(currency_of(c), scale_of(c)) for c in (f"{cell} {header}", metric_cell)}
        if len(units) != 1:
            raise _NotChecked("the implied EV and the borrower metric state different units")
    except _NotChecked as error:
        return where("not checked", reason=str(error))
    value = cp3_ev._implied(m[0], metric[0])
    if value is None:
        why = f"{EV_FORMULA}; the borrower metric is not above zero, so there is none"
        return where("disagreed", stated=cell, recomputed_label="Not Calculable", reason=why)
    slack = abs(m[0]) * half(metric[1]) + abs(metric[0]) * half(m[1])  # a product
    claim = _Claim(where, core.bare(cell), value, AMOUNT_STEP, "", EV_FORMULA, slack=slack)
    return _judged(claim, tables)


def check(text: str, loaded: Loaded, _upstream: Upstream) -> list[Outcome]:
    """T4.6's peer statistics, then T4.10's implied EV range, recomputed by the script."""
    rows = _t46_rows(text)
    if isinstance(rows, str):
        where = _Where("CP-1C", PEER_STATISTICS, "Peer statistics", "T4.6")
        return [where("not checked", reason=rows)]
    return [*(o for r in rows for o in _t46(r, text, loaded)), *_t410(text, rows, loaded)]


core.register("CP-1C", PEER_STATISTICS, check, CP1C_NOTE)
