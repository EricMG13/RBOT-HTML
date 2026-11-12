"""The CP Confidence Score, computed by Python from the inputs table a module writes.

The formula, weights, caps and bands are those of CANON_SHARED.md (CP_CONFIDENCE_SCORE.md) and of
the archived `confidence_score.py`, whose float arithmetic and `round` (half to even) are kept
exactly. A module states inputs only; it never writes the score or the band. Pure functions."""

import re
from dataclasses import dataclass
from typing import NamedTuple

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
FINDING_ROWS = ("CRITICAL", "MATERIAL", "MINOR")
COUNT_ROWS = (*LINEAGE_ROWS, PRESENT_ROW, TOTAL_ROW, *FINDING_ROWS)
INPUT_ROWS = (*LINEAGE_ROWS, PRESENT_ROW, TOTAL_ROW, GATE_ROW, *FINDING_ROWS)
HEADER = ("Input", "Value")


class Score(NamedTuple):
    value: int
    band: str
    status: str


@dataclass(frozen=True)
class Refused:
    """No score: `reason` says why in words; `absent` is true when the section is not there at
    all (nothing was asked of the module), false when it is there and wrong."""

    reason: str
    absent: bool = False


class Absent(ValueError):
    """The handoff has no confidence inputs section at all."""


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
        if count < 0:
            raise ValueError(f"negative claim count for {name!r}")
        weighted += LINEAGE_WEIGHTS[key] * count
        total += count
    evidence = (weighted / total) * 100.0 if total else 0.0  # No claims is not perfect evidence.
    coverage = (fields_present / fields_total) * 100.0
    penalty, counts = 0, {}
    for severity, count in findings.items():
        key = str(severity).strip().casefold()
        if key not in PENALTIES:
            raise ValueError(f"unknown finding severity {severity!r}")
        if count < 0:
            raise ValueError(f"negative finding count for {severity!r}")
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
    return [row for row in rows if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)]


def inputs(text: str) -> dict[str, str]:
    """The table's rows by input name. `Absent` when there is no section, `ValueError` (its
    message the reason) when the section is not a well-formed table; `from_handoff` turns both
    into a `Refused`."""
    lines = [line.rstrip() for line in text.splitlines()]
    at = [i for i, line in enumerate(lines) if line == f"### {HEADING}"]
    if not at:
        raise Absent(f"there is no `### {HEADING}` section")
    if len(at) > 1:
        raise ValueError(f"`### {HEADING}` is written more than once")
    body: list[str] = []
    for line in lines[at[0] + 1 :]:
        if line.startswith("#"):
            break
        body.append(line)
    rows = _table_rows(body)
    if not rows or tuple(rows[0]) != HEADER:
        raise ValueError(f"`### {HEADING}` needs a table headed `| {' | '.join(HEADER)} |`")
    found: dict[str, str] = {}
    for row in rows[1:]:
        if len(row) != len(HEADER):
            raise ValueError(f"a `{HEADING}` row needs 2 cells: {' | '.join(row)}")
        if row[0] not in INPUT_ROWS:
            raise ValueError(f"`{row[0]}` is not an input; the rows are {', '.join(INPUT_ROWS)}")
        if row[0] in found:
            raise ValueError(f"`{row[0]}` is stated twice")
        found[row[0]] = row[1]
    missing = [name for name in INPUT_ROWS if name not in found]
    if missing:
        raise ValueError(f"the `{HEADING}` table has no row for {', '.join(missing)}")
    return found


def from_handoff(text: str) -> Score | Refused:
    """The score of a handoff's inputs table, or the reason there is none."""
    try:
        found = inputs(text)
        for name in COUNT_ROWS:
            if not re.fullmatch(r"\d+", found[name]):
                raise ValueError(f"`{name}` is `{found[name]}`, not a whole number of 0 or more")
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
    except ValueError as error:
        return Refused(str(error))
