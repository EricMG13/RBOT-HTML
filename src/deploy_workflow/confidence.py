"""The CP Confidence Score, computed by Python from the inputs table a module writes.

The formula, weights, caps and bands are those of CANON_SHARED.md (CP_CONFIDENCE_SCORE.md) and of
the archived `confidence_score.py`, whose float arithmetic and `round` (half to even) are kept
exactly. A module states inputs only; it never writes the score or the band; a blocked module
states one not-assessable row. Pure functions."""

import re
from dataclasses import dataclass
from typing import NamedTuple

from deploy_workflow.prose_checks import bottom_line_text

HEADING = "Confidence inputs"
LINEAGE_WEIGHTS = {
    "directly sourced": 1.0,
    "calculated": 0.9,
    "assumption-based": 0.5,
    "analyst inference": 0.4,
    "weak lineage": 0.3,
    "untraced": 0.0,
    "conflicting": 0.0,
    "insufficient information": 0.0,
}
SOURCE_GATE = {"pass": 1.0, "partial": 0.7, "fail": 0.0}
PENALTIES = {"critical": 40, "material": 15, "minor": 3}
BANDS = ((80, "High"), (60, "Medium"), (40, "Low"), (0, "Insufficient Information"))

# The rows of the table, in the order a module is asked to write them: the lineage classes
# (counts of material claims whose strongest evidence is of that class), the required fields
# present and in all, the source gate, and the findings by severity.
LINEAGE_ROWS = (
    "Directly Sourced",
    "Calculated",
    "Assumption-Based",
    "Analyst Inference",
    "Weak Lineage",
    "Untraced",
    "Conflicting",
    "Insufficient Information",
)
PRESENT_ROW, TOTAL_ROW, GATE_ROW = "Fields present", "Fields total", "Source gate"
FIELD_ROWS = (PRESENT_ROW, TOTAL_ROW)
FINDING_ROWS = ("CRITICAL", "MATERIAL", "MINOR")
COUNT_ROWS = (*LINEAGE_ROWS, PRESENT_ROW, TOTAL_ROW, *FINDING_ROWS)
INPUT_ROWS = (*LINEAGE_ROWS, PRESENT_ROW, TOTAL_ROW, GATE_ROW, *FINDING_ROWS)
HEADER = ("Input", "Value")
# No real handoff counts 10**20 claims or findings. A claim or finding count with more digits is
# refused, so the float arithmetic on it cannot overflow (a 309-digit int cannot convert) and
# `score` itself raises ValueError for it, never OverflowError. Field counts only meet exact int
# division, which the archived script also does at any size; `from_handoff` bounds their digits
# under Python's own 4,300-digit limit on reading an int, so that limit never surfaces.
MAX_DIGITS = 20
MAX_COUNT = 10**MAX_DIGITS - 1
MAX_FIELD_DIGITS = 4000
FENCE = "```"
# A blocked module's Bottom line begins `Not assessable:` (the launcher's words, and the reader's
# test for a blocked module); it then writes the one row the launcher's blocked rule gives every
# table, `| Not assessable | Not supplied: <reason> |`, in place of the fourteen.
BLOCKED_MARK = "Not assessable:"
BLOCKED_ROW = "Not assessable"
GAP_MARK = "Not supplied:"

# What the library page shows when there is no score: one of these plain sentences, never model
# text, a heading marker or a module code. The detailed `reason` goes only to the retry message.
SHOWN_MISSING = "the inputs table is missing rows"
SHOWN_NOT_WHOLE = "the inputs table has a value that is not a whole number"
SHOWN_TWICE = "the inputs table is written more than once"
SHOWN_UNREADABLE = "the inputs table could not be read"
SHOWN_RANGE = "the inputs table has a value outside its allowed range"
SHOWN_BLOCKED = "the module was blocked, so no score is computed"
SHOWN = (
    SHOWN_MISSING,
    SHOWN_NOT_WHOLE,
    SHOWN_TWICE,
    SHOWN_UNREADABLE,
    SHOWN_RANGE,
    SHOWN_BLOCKED,
)


class Score(NamedTuple):
    value: int
    band: str
    status: str


@dataclass(frozen=True)
class Refused:
    """No score: `reason` says why in words for the module's retry; `shown` is the one plain
    sentence of `SHOWN` for the page; `absent` is true when the section is not there at all
    (nothing was asked of the module), false when it is there and wrong; `blocked` is true for a
    blocked module's one not-assessable row, which is the form it was asked to write."""

    reason: str
    absent: bool = False
    shown: str = SHOWN_UNREADABLE
    blocked: bool = False


class Absent(ValueError):
    """The handoff has no confidence inputs section at all."""


class Unreadable(ValueError):
    """The section is wrong; the message is the reason, `shown` the page sentence."""

    def __init__(self, reason: str, shown: str = SHOWN_UNREADABLE):
        super().__init__(reason)
        self.shown = shown


class Blocked(Unreadable):
    """A blocked module's one not-assessable row: no score, and nothing wrong."""

    def __init__(self) -> None:
        super().__init__("the module is blocked, so it states no inputs", SHOWN_BLOCKED)


def _is_blocked_row(text: str, rows: list[list[str]]) -> bool:
    """Exactly one body row, `Not assessable` with a stated gap, in a handoff whose Bottom line
    begins `Not assessable:`. Any other handoff writing it is wrong, as before."""
    if len(rows) != 2 or rows[1][0] != BLOCKED_ROW or len(rows[1]) != len(HEADER):
        return False
    cell = rows[1][1]
    if not (cell.startswith(GAP_MARK) and cell.removeprefix(GAP_MARK).strip()):
        return False
    return (bottom_line_text(text) or "").startswith(BLOCKED_MARK)


def _count(value: int, what: str, limit: int = MAX_COUNT) -> None:
    if value < 0:
        raise ValueError(f"negative {what}")
    if value > limit:
        raise ValueError(f"{what} has more than {len(str(limit))} digits")


def _band(value: int) -> str:
    return next(name for threshold, name in BANDS if value >= threshold)


def score(
    lineage: dict[str, int],
    fields_present: int,
    fields_total: int,
    source_gate: str,
    findings: dict[str, int],
) -> Score:
    """The score, band and QA status; ValueError, as the script exits 2, for an input it refuses."""
    gate = str(source_gate).strip().casefold()
    if gate not in SOURCE_GATE:
        raise ValueError(f"Source gate must be one of {sorted(SOURCE_GATE)}, got {source_gate!r}")
    if fields_total <= 0:
        raise ValueError("Fields total must be positive")
    if not 0 <= fields_present <= fields_total:
        raise ValueError(f"Fields present {fields_present} is outside 0..{fields_total}")
    total, weighted = 0, 0.0
    for name, count in lineage.items():
        key = str(name).strip().casefold()
        if key not in LINEAGE_WEIGHTS:
            raise ValueError(f"unknown lineage class {name!r}")
        _count(count, f"claim count for {name!r}")
        weighted += LINEAGE_WEIGHTS[key] * count
        total += count
    evidence = (weighted / total) * 100.0 if total else 0.0  # No claims is not perfect evidence.
    coverage = (fields_present / fields_total) * 100.0
    penalty, counts = 0, {}
    for severity, count in findings.items():
        key = str(severity).strip().casefold()
        if key not in PENALTIES:
            raise ValueError(f"unknown finding severity {severity!r}")
        _count(count, f"finding count for {severity!r}")
        penalty += PENALTIES[key] * count
        counts[key] = count
    raw = (0.6 * evidence + 0.4 * coverage) * SOURCE_GATE[gate] - penalty
    capped = max(0, min(100, raw))
    if counts.get("critical"):
        capped, status = min(capped, 39), "Blocked"
    elif counts.get("material"):
        capped, status = min(capped, 59), "Restricted"
    else:
        status = "Passed"
    value = round(capped)  # Half to even, as the script's `int(round(..))`; an int result.
    return Score(value, _band(value), status)


def _table_rows(lines: list[str]) -> list[list[str]]:
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in lines
        if line.startswith("|")
    ]
    return [row for row in rows if not all(re.fullmatch(r":?-+:?", cell) for cell in row)]


def _lines(text: str) -> tuple[list[str], list[bool]]:
    """The text's lines, and for each whether it is a fence marker or inside a fence: fenced text
    is an example, not the table (as prose_checks reads it). A marker line is blanked."""
    lines: list[str] = []
    fenced: list[bool] = []
    inside = False
    for line in text.splitlines():
        marker = line.lstrip().startswith(FENCE)
        inside ^= marker
        lines.append("" if marker else line.rstrip())
        fenced.append(inside or marker)
    return lines, fenced


def inputs(text: str) -> dict[str, str]:
    """The table's rows by input name. `Absent` when there is no section, `ValueError` (its
    message the reason) when the section is not a well-formed table; `from_handoff` turns both
    into a `Refused`."""
    lines, fenced = _lines(text)
    at = [i for i, line in enumerate(lines) if line == f"### {HEADING}" and not fenced[i]]
    if not at:
        raise Absent(f"there is no `### {HEADING}` section")
    if len(at) > 1:
        raise Unreadable(f"`### {HEADING}` is written more than once", SHOWN_TWICE)
    body: list[str] = []
    for i in range(at[0] + 1, len(lines)):
        if fenced[i]:
            continue
        if lines[i].startswith("#"):
            break
        body.append(lines[i])
    rows = _table_rows(body)
    if not rows or tuple(rows[0]) != HEADER:
        raise Unreadable(f"`### {HEADING}` needs a table headed `| {' | '.join(HEADER)} |`")
    if _is_blocked_row(text, rows):
        raise Blocked
    found: dict[str, str] = {}
    for row in rows[1:]:
        if len(row) != len(HEADER):
            raise Unreadable(f"a `{HEADING}` row needs 2 cells: {' | '.join(row)}")
        if row[0] not in INPUT_ROWS:
            raise Unreadable(f"`{row[0]}` is not an input; the rows are {', '.join(INPUT_ROWS)}")
        if row[0] in found:
            raise Unreadable(f"`{row[0]}` is stated twice")
        found[row[0]] = row[1]
    missing = [name for name in INPUT_ROWS if name not in found]
    if missing:
        raise Unreadable(
            f"the `{HEADING}` table has no row for {', '.join(missing)}", SHOWN_MISSING
        )
    return found


def from_handoff(text: str) -> Score | Refused:
    """The score of a handoff's inputs table, or the reason there is none."""
    try:
        found = inputs(text)
        for name in COUNT_ROWS:
            if not re.fullmatch(r"\d+", found[name]):
                raise Unreadable(
                    f"`{name}` is `{found[name]}`, not a whole number of 0 or more", SHOWN_NOT_WHOLE
                )
            if len(found[name]) > (MAX_FIELD_DIGITS if name in FIELD_ROWS else MAX_DIGITS):
                raise Unreadable(
                    f"`{name}` has too many digits; state the real count",
                    SHOWN_RANGE,
                )
        n = {name: int(found[name]) for name in COUNT_ROWS}
        return score(
            {name: n[name] for name in LINEAGE_ROWS},
            n[PRESENT_ROW],
            n[TOTAL_ROW],
            found[GATE_ROW],
            {name: n[name] for name in FINDING_ROWS},
        )
    except Absent as error:
        return Refused(str(error), absent=True)
    except Blocked as error:
        return Refused(str(error), shown=error.shown, blocked=True)
    except Unreadable as error:
        return Refused(str(error), shown=error.shown)
    except ValueError as error:  # `score` refusing a value that is outside what it allows
        return Refused(str(error), shown=SHOWN_RANGE)
