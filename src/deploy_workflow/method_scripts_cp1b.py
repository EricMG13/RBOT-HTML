"""CP-1B's method script, `credit_metrics.py` (`growth`), run on T4.6 and T4.4 (harness:
`deploy_workflow.method_scripts`).

CP-1B's SKILL: `./scripts/credit_metrics.py` "owns the numeric columns of T4.4/T4.6 — absolute and
percentage change". The archive holds no CP-1B scripts folder; cp-os b57a344's
`skills/cp-1b-earnings-delta/scripts/credit_metrics.py` (the staged byte copy in this repository's
history at 86b9466, SHA256SUMS checked) is byte-identical to the archived CP-1 copy (sha256
`8f90ad05`), so that registered file runs. The script computes the percentage change only
(`growth`: current / prior - 1, none on a zero prior); the absolute change is not one of its
functions, so it is not checked.

T4.6 (`Metric | Comparison Basis | Prior Value | Current Value | Abs Change | % Change | ...`):
each row's % Change against `growth(Current Value, Prior Value)`. T4.4 (`Line Item | Period
1...N | YoY Change (Abs) | YoY Change (%) | ...`, or the SKILL's joined `YoY Abs/%`): each row's
YoY % against the latest period and the same period one year before it, when the headers name
both (`FY2024` and `FY2023`, `Q3 2024` and `Q3 2023`); otherwise not checked.

Not checked: a metric whose values are percentages or multiples (a margin's change may be stated in
percentage points or as a relative change, and the column does not say which), a change written in
`pp` or `bps`, a prior below zero (a change on a negative base has more than one convention), values
in different currencies or scales, a bare figure of 1 or less in a % column (it could be a decimal
or a small percentage). A figure stated over a zero prior disagrees: the script gives none.
"""

import re
import types
from dataclasses import dataclass

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    ARCHIVE,
    Loaded,
    Outcome,
    Status,
    Table,
    Upstream,
    _Claim,
    _label,
    _NotChecked,
    _plain,
    _Where,
    blank,
    currency_of,
    figure,
    half,
    quotient_slack,
    register_table,
    said_none,
    scale_of,
    share,
)

CREDIT_METRICS = ARCHIVE + "skills/cp-1-canonical-data-foundation/scripts/credit_metrics.py"
# T4.4's cost lines (REF_CP-1B_05: COGS, SG&A, D&A, cash interest and taxes, capex) and any other.
_COST = re.compile(
    r"\b(?:cogs|cost|costs|sg&a|sga|expense|expenses|interest|tax|taxes|capex|d&a|depreciation|"
    r"amorti[sz]ation)\b",
    re.IGNORECASE,
)
GROWTH_FORMULA = (
    "% Change = Current / Prior - 1, in percent; none on a zero prior (credit_metrics.py growth, "
    "which CP-1B's SKILL names for T4.4 and T4.6)"
)
# A period header (`FY2024`, `FY24`, `Q3 2024`, `2024A`, `LTM 2024`), compared without spaces.
_PERIOD = re.compile(
    r"^(?:fy|cy|ltm|ytd|[hq][1-4]|[1-4][hq]|\d{1,2}m)?\s*(?:fy)?\s*'?(?:19|20)?\d{2}[a-z]?$"
)
_YEAR = re.compile(r"^(?P<pre>.*?)(?P<year>(?:19|20)\d{2}|\d{2})(?P<post>[a-z]?)$")
# What CP-1B would need to be told for this check (not sent: `earnings_update` has 93 characters
# under its ceiling, and the owner raises a ceiling, not this module). Kept to measure the need.
CP1B_NOTE_UNSENT = (
    "Python checks your T4.6 % Change and T4.4 YoY % after you answer, with the method's own "
    "`credit_metrics.py` (you cannot run it): Current / Prior - 1, from the row's own values. "
    "So write % Change with `%`, Prior and Current in one unit, and name T4.4's periods so the "
    "year-earlier one is recognisable (`FY2023`, `FY2024`). A figure that disagrees is sent back "
    "for repair; one whose input is missing is not checked, never read as zero.\n\n"
)


@dataclass(frozen=True)
class _Pair:
    """One stated change and the two values it rests on, as written."""

    register: str
    name: str
    prior: str
    current: str
    stated: str


def _where(pair: _Pair) -> _Where:
    return _Where("CP-1B", CREDIT_METRICS, f"% Change: {pair.name}", pair.register)


def _amount(cell: str, tables: types.ModuleType) -> tuple[float, int, str] | None:
    """A value and its unit (currency and scale, or ``""``); None for a cell that states none.
    `_NotChecked` for a percentage or a multiple (a margin's change is ambiguous)."""
    text = _plain(cell)
    if blank(text, tables) or said_none(text) or text in core.NOT_APPLICABLE:
        return None
    if re.search(r"(?:%|\d\s*[x×])\)?$", text, re.IGNORECASE):
        raise _NotChecked(f"`{cell}` is a percentage or a multiple; its change may be in points")
    unit = " ".join(filter(None, (currency_of(text), scale_of(text))))
    read = figure(core.bare(text), tables)
    if isinstance(read, str):
        raise _NotChecked(read)
    return read[0], read[1], unit


def _dash(text: str) -> str:
    """A leading en dash or minus sign as the minus it is (`–7.3%`, `−600`)."""
    return re.sub(r"^([(\s]*)[–−]", r"\1-", text)


def states_figure(cell: str) -> bool:
    """Whether a change cell states a figure: it starts with one, its bracketed notes aside
    (`N/A (zero base)` and `New` state none; `(10.0%)` and `7.1% (organic)` state one)."""
    text = _dash(_plain(cell))
    return bool(re.match(r"^\s*\(?\s*[-+]?\s*\d", text))


def _stated(cell: str) -> str:
    """The % Change cell as a share the harness reads: `%` kept; a bare figure in a % column is
    percent when above 1, and not read when 1 or less (a decimal or a small percentage)."""
    text = _dash(_plain(cell))
    if re.search(r"\b(?:pp|bps?|ppt|points?)\b", text, re.IGNORECASE):
        raise _NotChecked(f"`{cell}` is a change in points, not a percentage change")
    if "%" in text:
        return text
    read = re.fullmatch(r"\(?[-+]?(\d[\d,]*(?:\.\d+)?)\)?", text.strip())
    if read and float(read[1].replace(",", "")) > 1:
        return f"{text}%"
    raise _NotChecked(f"`{cell}` states no `%` figure above 1 (a decimal or a small percentage)")


def _check(pair: _Pair, loaded: Loaded) -> Outcome:
    where, tables = _where(pair), loaded.tables
    if blank(pair.stated, tables):
        return where("not checked", stated=pair.stated, reason="no change is stated")
    try:
        prior, current = _amount(pair.prior, tables), _amount(pair.current, tables)
        if prior is None or current is None:
            raise _NotChecked("a prior or current value is not stated (missing, not zero)")
        if prior[2] != current[2]:  # one stated unit beside a bare figure is no match either
            raise _NotChecked(f"prior and current are in different units: {prior[2]}, {current[2]}")
        if prior[0] < 0:
            raise _NotChecked(
                "the prior is below zero: a change on a negative base is a convention"
            )
        value = loaded.script.growth(current[0], prior[0])
        if value is None:  # a zero prior: the script gives none; only a stated figure disagrees
            if not states_figure(pair.stated):
                status: Status = "agreed" if said_none(pair.stated) else "not checked"
                why = f"{GROWTH_FORMULA}; the prior is zero and the cell states no figure"
                return where(status, stated=pair.stated, reason=why)
            why = f"{GROWTH_FORMULA}; the prior is zero"
            return where(
                "disagreed", stated=pair.stated, recomputed_label="Not Calculable", reason=why
            )
        if not states_figure(pair.stated):
            raise _NotChecked("the change states no figure where the script computes one")
        text = _stated(pair.stated)
        if _COST.search(pair.name) and _sign(text) != (value >= 0):
            # A cost may carry either sign: the method fixes none (SKILL: "absolute and
            # percentage change"), so a cost's rise may be written as an unfavourable (10.0%).
            text = text.replace("(", "").replace(")", "").lstrip("-+ ")
            value = abs(value)
    except _NotChecked as error:
        return where("not checked", stated=pair.stated, reason=str(error))
    slack = quotient_slack(current[0], half(current[1]), prior[0], half(prior[1]))
    claim = _Claim(where, text, value, 1e-6, "", GROWTH_FORMULA, slack=slack)
    return share(claim, tables)


def _sign(text: str) -> bool:
    """Whether a stated change is zero or more."""
    return not re.match(r"^\s*(?:\(|-)", text)


def _column(table: Table, *names: str) -> int | None:
    header = [_label(h) for h in table[0]]
    found = [i for i, h in enumerate(header) if h in names]
    return found[0] if len(found) == 1 else None


def _t46(text: str) -> list[_Pair] | str:
    table = register_table(text, "T4.6")
    if isinstance(table, str):
        return table
    cols = [_column(table, n) for n in ("metric", "prior value", "current value", "% change")]
    if None in cols:
        return "T4.6 has no Metric, Prior Value, Current Value or % Change column"
    m, p, c, g = (int(i) for i in cols if i is not None)
    return [_Pair("T4.6", _plain(r[m]), r[p], r[c], r[g]) for r in table[1]]


def _compact(label: str) -> str:
    return _label(label).replace(" ", "").replace("'", "")


def _kind(label: str) -> str:
    """A period header without its year (`Q3 2024` -> `q3`, `FY2024` -> `fy`)."""
    found = _YEAR.match(_compact(label))
    return found["pre"] if found else _compact(label)


def _year(label: str) -> int:
    found = _YEAR.match(_compact(label))
    year = int(found["year"]) if found else 0
    return year + 2000 if year < 100 else year


def _year_earlier(label: str, labels: list[str]) -> int | None:
    """The one column whose header is ``label`` one year earlier (`FY2024` -> `FY2023`)."""
    found = _YEAR.match(_compact(label))
    if found is None:
        return None
    year = found["year"]
    want = f"{found['pre']}{str(int(year) - 1).zfill(len(year))}{found['post']}"
    same = [i for i, h in enumerate(labels) if h and _compact(h) == want]
    return same[0] if len(same) == 1 else None


def _t44(text: str) -> list[_Pair] | str:
    table = register_table(text, "T4.4")
    if isinstance(table, str):
        return table
    pct = _column(table, "yoy change (%)", "yoy %", "yoy change %")
    joined = _column(table, "yoy abs/%", "yoy change (abs/%)")
    line = _column(table, "line item")
    if line is None or (pct is None and joined is None):
        return "T4.4 has no Line Item or YoY % column"
    periods = [i for i, h in enumerate(table[0]) if _PERIOD.match(_label(h))]
    if not periods:
        return "T4.4 names no period columns"
    labels = [table[0][i] if i in periods else "" for i in range(len(table[0]))]
    top = max(_year(table[0][i]) for i in periods)
    pairs = [
        (i, j)
        for i in periods
        if _year(table[0][i]) == top and (j := _year_earlier(table[0][i], labels)) is not None
    ]
    if not pairs:
        return "T4.4 has no period column one year before its latest"
    if len({_kind(table[0][i]) for i, _ in pairs}) > 1:  # `Q3 2024` and `9M 2024` both pair
        return (
            "T4.4 has more than one period kind with a year-earlier column; its YoY pair is unsaid"
        )
    latest, earlier = pairs[-1]
    out = []
    for row in table[1]:
        stated = (
            row[pct]
            if pct is not None
            else ([*re.split(r"\s+/\s+", _plain(row[int(joined or 0)])), ""])[1]
        )
        out.append(_Pair("T4.4", _plain(row[line]), row[earlier], row[latest], stated))
    return out


def check(text: str, loaded: Loaded, _upstream: Upstream) -> list[Outcome]:
    """Each T4.6 % Change and T4.4 YoY %, recomputed by the script's `growth`."""
    out: list[Outcome] = []
    for ident, read in (("T4.6", _t46(text)), ("T4.4", _t44(text))):
        if isinstance(read, str):
            where = _Where("CP-1B", CREDIT_METRICS, "% Change: all", ident)
            out.append(where("not checked", reason=read))
            continue
        out += [_check(pair, loaded) for pair in read]
    return out


# No note: `earnings_update` has 93 characters left under its ceiling (ruling section).
core.register("CP-1B", CREDIT_METRICS, check, None)
