"""What a parsed handoff gives its output record: the reader summary, chart, event and map
tables (`reader_fields`) and where each section is read (`report_fields`).

Part of the library's store (`credit_os.store`, which re-exports every name here).
"""

import decimal
import re
from typing import Any

from credit_os.source import (
    valid_date,
)

READER_TABLES = [
    ["Bottom line", "Confidence", "Main limitation"],
    ["Finding", "Creditor impact", "Confidence"],
]
CHART_PREFIX = "Chart data: "
CHART_LAST_COLUMNS = ["Reporting unit", "Basis and limitation"]
CHART_FIRST_COLUMNS = ("Period", "Step")  # Periods are columns over time; steps are a bridge.
STEP_HEADERS = ["Step", "Amount", *CHART_LAST_COLUMNS]
DIRECTIONS = ("Passes below", "Passes at or below", "Passes above", "Passes at or above")
# Row tables the launcher asks for (cpos_launch.py OWNER_TABLES with `columns`): the exact leading
# header, the drawn kind with its column roles, the numeric columns and the columns of fixed words.
BULLET = {"kind": "bullet", "direction": 4}  # Direction is the last column before the unit.
ROW_CHARTS: tuple[tuple[tuple[str, ...], dict[str, Any], tuple[int, ...], dict[int, Any]], ...] = (
    (
        ("Facility", "Ranking", "Secured", "Amount", "Cumulative leverage"),
        {"kind": "stack", "label": 0, "rank": 1, "secured": 2, "amount": 3, "leverage": 4},
        (3, 4),
        {2: ("Yes", "No")},
    ),
    (
        ("Test", "Threshold", "Current", "Headroom", "Direction"),
        {**BULLET, "label": [0], "threshold": 1, "current": 2, "headroom": 3},
        (1, 2),
        {3: "gap", 4: DIRECTIONS},
    ),
    (
        ("Agency", "Trigger", "Threshold", "Current", "Direction"),
        {**BULLET, "label": [0, 1], "threshold": 2, "current": 3, "headroom": None},
        (2, 3),
        {4: DIRECTIONS},
    ),
    (
        ("Limit", "Current exposure", "Proposed exposure", "Limit value"),
        {"kind": "limits", "label": 0, "current": 1, "proposed": 2, "limit": 3},
        (1, 2, 3),
        {},
    ),
    (
        ("Measure", "Prior period", "Prior", "Current period", "Current"),
        {"kind": None, "label": 0, "sub": [1, 3], "periods": [1, 3], "prior": 2, "current": 4},
        (2, 4),
        {1: "gap", 3: "gap"},
    ),
    (
        ("Metric", "Issuer", "Peer low", "Peer median", "Peer high", "Peer count"),
        {"kind": "range", "label": 0, "issuer": 1, "low": 2, "median": 3, "high": 4, "count": 5},
        (1, 2, 3, 4),
        {5: "count"},
    ),
    (
        ("Instrument", "Maturity date", "Yield", "Spread", "Quote date", "Source class"),
        {
            "kind": "scatter",
            "label": 0,
            "date": 1,
            "yield": 2,
            "spread": 3,
            "quoted": 4,
            "source": 5,
        },
        (2,),
        {1: "date", 3: "gap", 4: "date"},
    ),
    (
        ("Class", "Scenario", "Claim", "Recovery", "Recovery %"),
        {
            "kind": "recovery",
            "label": 0,
            "scenario": 1,
            "claim": 2,
            "recovery": 3,
            "percent": 4,
        },
        (2, 3, 4),
        {},
    ),
)
# The two tables of the pair header differ only by heading: the results are grouped columns (one
# unit, so one scale), the margin and KPI changes a dumbbell per row.
PAIR_KINDS = {
    f"{CHART_PREFIX}prior and current results": "grouped",
    f"{CHART_PREFIX}margin and KPI changes": "dumbbell",
}


def _reader_summary(section: dict[str, Any]) -> dict[str, Any] | None:
    """The section's values, or None when it does not hold its two tables."""
    tables = [b for b in section["blocks"] if b["type"] == "table"]
    if [t["headers"] for t in tables] != READER_TABLES:
        return None
    calls, findings = (t["rows"] for t in tables)
    if len(calls) != 1 or not findings or any(len(r["cells"]) != 3 for r in calls + findings):
        return None
    bottom_line, confidence, limitation = calls[0]["cells"]
    return {
        "bottomLine": bottom_line,
        "confidence": confidence,
        "limitation": limitation,
        "line": calls[0]["line"],
        "findings": [
            {
                "finding": r["cells"][0],
                "impact": r["cells"][1],
                "confidence": r["cells"][2],
                "line": r["line"],
            }
            for r in findings
        ],
    }


PLAIN_AMOUNT = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
# CP-1's money tables state the issuer's own currency: `US$m`, or its code and `m` (`GBPm`).
MONEY_UNIT = re.compile(r"US\$m|[A-Z]{3}m", re.ASCII)
MONEY_HEADINGS = ("Chart data: revenue and EBITDA", "Chart data: EBITDA bridge")
STATED_GAP = re.compile(r"Not supplied:\s*\S")


def _bridge_amounts(table: dict[str, Any]) -> list[decimal.Decimal] | None:
    """A step table's stated amounts when it is a bridge that reconciles, else None.

    Mirrors the launcher's check (cpos_launch.py `_bridge_issues`; the store imports the standard
    library and `deploy_workflow.confidence` only): every Amount a plain signed number, and the
    opening plus the stated changes equal to the closing. Each amount has at most the table's own
    decimals, so the sum is exact."""
    cells = [row["cells"][1] for row in table["rows"]]
    if len(cells) < 2 or not all(PLAIN_AMOUNT.fullmatch(c) for c in cells):
        return None
    values = [decimal.Decimal(c.replace(",", "")) for c in cells]
    return values if sum(values[:-1], decimal.Decimal(0)) == values[-1] else None


def _gap_reasons(cells: list[str]) -> str:
    """Each distinct reason of `Not supplied: <reason>` cells, once, in the order stated."""
    return "; ".join(dict.fromkeys(c.partition(":")[2].strip() for c in cells))


def _chart_gap(section: dict[str, Any]) -> dict[str, Any] | None:
    """A fixed owner table explicitly stating no data; preserve its reason without a chart."""
    tables = [b for b in section["blocks"] if b["type"] == "table"]
    if len(tables) != 1 or not tables[0]["rows"]:
        return None
    table = tables[0]
    headers, rows = table["headers"], [r["cells"] for r in table["rows"]]
    step = headers == STEP_HEADERS
    known = tuple(headers[:-2]) in {leading for leading, *_ in ROW_CHARTS}
    if not (step or known) or headers[-2:] != CHART_LAST_COLUMNS:
        return None
    if any(len(row) != len(headers) or not all(row[-2:]) for row in rows):
        return None
    cells = [c for row in rows for c in (row[1:2] if step else row[:-2])]
    if not all(STATED_GAP.match(c) for c in cells):
        return None
    return {**_chart_head(section, table), "gap": _gap_reasons(cells)}


def _row_relations_ok(rows: list[dict[str, Any]], kind: str | None) -> bool:
    """Cross-cell constraints mirrored from the launcher; no value is filled or recomputed."""
    cells = [r["cells"] for r in rows]
    if kind == "range":
        values = [
            [decimal.Decimal(c.replace(",", "")) for c in row[2:5] if PLAIN_AMOUNT.fullmatch(c)]
            for row in cells
        ]
        return all(v == sorted(v) for v in values)
    if kind == "scatter":
        return all(not (valid_date(r[1]) and valid_date(r[4])) or r[1] >= r[4] for r in cells)
    if kind == "recovery":
        keys = [(r[0], r[1]) for r in cells]
        return len({r[1] for r in cells}) <= 3 and len(keys) == len(set(keys))
    return True


def _row_cell_ok(cell: str, column: int, numeric: tuple[int, ...], words: dict[int, Any]) -> bool:
    """Mirrors the launcher's cell check for a row table: a plain number or a stated gap in a
    numeric column, one of the fixed words in a word column, anything stated elsewhere."""
    if column in numeric:
        return bool(PLAIN_AMOUNT.fullmatch(cell) or STATED_GAP.match(cell))
    if words.get(column) == "date":
        return bool(valid_date(cell) or STATED_GAP.match(cell))
    if words.get(column) == "count":  # A whole number of peers, zero included.
        return bool(re.fullmatch(r"\d+", cell) or STATED_GAP.match(cell))
    if words.get(column) == "gap":
        return bool(cell)
    if column in words:
        return cell in words[column]
    return bool(cell and not STATED_GAP.match(cell))


def _ranks_in_order(rows: list[dict[str, Any]], column: int) -> bool:
    """Legal rank is a positive whole number that never falls down the rows (as the launcher)."""
    ranks = [row["cells"][column] for row in rows]
    if not all(re.fullmatch(r"[1-9]\d*", rank) for rank in ranks):
        return False
    return [int(r) for r in ranks] == sorted(int(r) for r in ranks)


def _row_chart(table: dict[str, Any]) -> dict[str, Any] | None:
    """A debt stack, headroom or portfolio-limit table that is in its fixed shape, else None."""
    headers, rows = table["headers"], table["rows"]
    for leading, roles, numeric, words in ROW_CHARTS:
        if tuple(headers[:-2]) != leading or headers[-2:] != CHART_LAST_COLUMNS:
            continue
        if any(len(row["cells"]) != len(headers) for row in rows):
            return None
        stated = all(
            _row_cell_ok(cell, at, numeric, words)
            for row in rows
            for at, cell in enumerate(row["cells"][:-2])
        ) and all(row["cells"][-2] and row["cells"][-1] for row in rows)
        if not stated or ("rank" in roles and not _ranks_in_order(rows, roles["rank"])):
            return None
        if not _row_relations_ok(rows, roles["kind"]):
            return None
        amount_units = {r["cells"][-2] for r in rows if not STATED_GAP.match(r["cells"][3])}
        if roles["kind"] == "stack" and (
            len(amount_units) > 1 or not all(map(MONEY_UNIT.fullmatch, amount_units))
        ):
            return None  # The debt stack is one money unit: the issuer's own currency.
        units = {row["cells"][-2] for row in rows}
        # A single stated unit is the figure's; rows in different units each state their own.
        return {**roles, "unit": units.pop() if len(units) == 1 else "", "columns": list(numeric)}
    return None


def _chart_head(section: dict[str, Any], table: dict[str, Any]) -> dict[str, Any]:
    # Only the first letter is raised: an acronym in the heading keeps its case.
    title = section["heading"].removeprefix(CHART_PREFIX)
    return {"title": title[:1].upper() + title[1:], "table": table["line"]}


def _period_cells_ok(section: dict[str, Any], table: dict[str, Any]) -> bool:
    """Owner period and step tables use US$m (CP-1's revenue and EBITDA and EBITDA bridge, the
    issuer's one money unit), except cells explicitly stating a gap."""
    fixed = table["headers"][0] == "Step" or section["heading"] in (
        "Chart data: revenue and EBITDA",
        "Chart data: refinancing need",
    )
    if fixed and section["heading"] in MONEY_HEADINGS:
        stated = {
            r["cells"][-2]
            for r in table["rows"]
            for c in r["cells"][1:-2]
            if not STATED_GAP.match(c)
        }
        return (
            len(stated) <= 1
            and all(map(MONEY_UNIT.fullmatch, stated))
            and all(
                STATED_GAP.match(c) or PLAIN_AMOUNT.fullmatch(c)
                for r in table["rows"]
                for c in r["cells"][1:-2]
            )
        )
    return not fixed or all(
        STATED_GAP.match(c) or (PLAIN_AMOUNT.fullmatch(c) and r["cells"][-2] == "US$m")
        for r in table["rows"]
        for c in r["cells"][1:-2]
    )


def _chart_table(section: dict[str, Any]) -> dict[str, Any] | None:
    """What the app needs to draw the section's table, or None when it is not the fixed shape."""
    tables = [b for b in section["blocks"] if b["type"] == "table"]
    if len(tables) != 1 or not tables[0]["rows"]:
        return None
    table = tables[0]
    headers = table["headers"]
    if any(len(r["cells"]) != len(headers) or not all(r["cells"][-2:]) for r in table["rows"]):
        return None
    if headers[0] not in CHART_FIRST_COLUMNS:
        head = _chart_head(section, table)
        drawn = _row_chart(table)
        if drawn and drawn["kind"] is None:  # The pair header: its heading says how it is drawn.
            kind = PAIR_KINDS.get(section["heading"])
            grouped = kind == "grouped" and not drawn["unit"]  # One scale needs one unit.
            drawn = None if kind is None or grouped else {**drawn, "kind": kind}
        if drawn and drawn["kind"] == "recovery" and not drawn["unit"]:
            drawn = None  # The recoveries share one scale, so one unit.
        return drawn and {**head, **drawn}
    if (
        len(headers) < 4
        or headers[-2:] != CHART_LAST_COLUMNS
        or not _period_cells_ok(section, table)
    ):
        return None
    valued = [r for r in table["rows"] if any(PLAIN_AMOUNT.fullmatch(c) for c in r["cells"][1:-2])]
    chart = {
        **_chart_head(section, table),
        "unit": (valued or table["rows"])[0]["cells"][-2],
        "columns": list(range(1, len(headers) - 2)),
    }
    if headers[0] == "Step":
        if headers != STEP_HEADERS or _bridge_amounts(table) is None:
            return None
        chart |= {"kind": "waterfall", "amount": 1}
    return chart


EVENT_PREFIX = "Events: "
EVENT_HEADERS = [
    *("Event date", "Date precision", "Published", "Event"),
    *("Status", "Source", "Credit relevance"),
]
EVENT_SHAPES = {
    "month": re.compile(r"\d{4}-(?:0[1-9]|1[0-2])", re.ASCII),
    "quarter": re.compile(r"\d{4}-Q[1-4]", re.ASCII),
    "year": re.compile(r"\d{4}", re.ASCII),
}


EVENT_STATUS = re.compile(
    r"(?:Historical|Scheduled|Scenario) \u2014 \S|User reminder(?: \u2014 \S|$)"
)


def _event_row_ok(cells: list[str]) -> bool:
    """Mirrors the launcher's check: every cell stated, the date in the form its precision names."""
    when, precision, published = cells[:3]
    shape = EVENT_SHAPES.get(precision)
    dated = valid_date(when) if precision == "day" else bool(shape and shape.fullmatch(when))
    stated = all(c and not STATED_GAP.match(c) for i, c in enumerate(cells) if i != 2)
    kind = EVENT_STATUS.match(cells[4])
    # Published is a date, a legacy dash, or a stated gap (the document cited states no date).
    published_ok = (
        published == "\u2014" or valid_date(published) or bool(STATED_GAP.match(published))
    )
    return bool(dated and stated and kind and published_ok)


def _event_lane(section: dict[str, Any]) -> dict[str, Any] | None:
    """A calendar lane from an `Events: <lane>` table in its fixed shape, else None. A table of
    only stated gaps is a lane with its reason and no events."""
    tables = [b for b in section["blocks"] if b["type"] == "table"]
    if len(tables) != 1 or tables[0]["headers"] != EVENT_HEADERS or not tables[0]["rows"]:
        return None
    rows = [row["cells"] for row in tables[0]["rows"]]
    lane = {"lane": section["heading"].removeprefix(EVENT_PREFIX), "table": tables[0]["line"]}
    if all(STATED_GAP.match(c) for cells in rows for c in cells):
        return {**lane, "gap": _gap_reasons([c for cells in rows for c in cells])}
    return {**lane, "gap": None} if all(_event_row_ok(cells) for cells in rows) else None


MAP_PREFIX = "Map: "
MAP_HEADERS = ["From", "Relationship", "Edge type", "To", "Evidence"]
_FACTS = ("Documentary Fact", "Management Language", "Analyst Interpretation")
# Mirrors the launcher's MAPS (cpos_launch.py): each map's own words for an edge type.
MAP_EDGES = {
    "ownership and control": ("Ownership", "Legal control", "Guarantee", "Other stated"),
    "operating model to credit": (*_FACTS, "Insufficient Information"),
    "credit-risk transmission": (*_FACTS, "Insufficient Information"),
    "stress scenario": ("Assumption", "Test outcome", "Explanation"),
    "legal entities": ("Ownership", "Guarantee", "Security", "Structural claim"),
    "intercreditor": (
        "Payment rank",
        "Security rank",
        "Enforcement control",
        "Standstill",
        "Release",
    ),
    "support and contradiction": ("Supports", "Contradicts", "Unresolved"),
}


def _edge_map(section: dict[str, Any]) -> dict[str, Any] | None:
    """A node/edge map from a `Map: <name>` table in its fixed shape, else None. Every edge type is
    one of the map's own words and every other cell is stated; a table of only stated gaps is a
    map with its reason and no edge."""
    name = section["heading"].removeprefix(MAP_PREFIX)
    tables = [b for b in section["blocks"] if b["type"] == "table"]
    if name not in MAP_EDGES or len(tables) != 1 or tables[0]["headers"] != MAP_HEADERS:
        return None
    rows = [row["cells"] for row in tables[0]["rows"]]
    drawn = {"name": name, "table": tables[0]["line"]}
    if rows and all(STATED_GAP.match(c) for cells in rows for c in cells):
        return {**drawn, "gap": _gap_reasons([c for cells in rows for c in cells])}
    stated = all(c and not STATED_GAP.match(c) for cells in rows for c in cells)
    stated = stated and all(cells[4] not in ("\u2014", "-", "\u2013") for cells in rows)
    legal = stated and all(cells[2] in MAP_EDGES[name] for cells in rows)
    return {**drawn, "gap": None} if rows and legal else None


def reader_fields(sections: list[dict[str, Any]]) -> dict[str, Any]:
    """A handoff's reader section and chart tables; a malformed one is named, the handoff reads."""
    charts: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    summary, events, maps, problems = None, [], [], []
    for section in sections:
        heading = section["heading"]
        if heading == "Reader summary":
            summary = _reader_summary(section)
            if summary is None:
                problems.append("Reader summary is not in its two tables")
        elif heading.startswith(EVENT_PREFIX):
            lane = _event_lane(section)
            if lane:
                events.append(lane)
            else:
                problems.append(f"{heading} is not in its fixed table")
        elif heading.startswith(MAP_PREFIX):
            edge_map = _edge_map(section)
            if edge_map:
                maps.append(edge_map)
            else:
                problems.append(f"{heading} is not in its fixed table")
        elif heading.startswith(CHART_PREFIX):
            chart = _chart_gap(section) or _chart_table(section)
            if chart:
                (gaps if "gap" in chart else charts).append(chart)
            else:
                problems.append(f"{heading} is not in its fixed table")
    return {
        "summary": summary,
        "charts": charts,
        "chartGaps": gaps,
        "events": events,
        "maps": maps,
        "issue": "; ".join(problems) or None,
    }


# Evidence & audit by heading (R31a); Python decides it and the page reads the placement.
EVIDENCE_HEADING = re.compile(
    r"^front matter$|^request$|^sources?$|source register|source-context"
    r"|supplied (current )?handoffs?|technical audit",
    re.IGNORECASE,
)
LEVEL_TWO_PLACEMENT = {"Calculations": "calculations", "Gaps": "limits"}
CONFIDENCE_NOT_ASSESSABLE = "not assessable"
COMMITTEE_STATUS = re.compile(r"^committee_status:[ \t]*(\S.*)$", re.MULTILINE)
WORD_GROUPS = ("view", "reference", "calculations", "limits", "audit")


def _is_evidence(sections: list[dict[str, Any]], index: int) -> bool:
    """The section's own heading, or an ancestor heading at level 2 or more, is evidence."""
    section = sections[index]
    level = section["level"]
    if EVIDENCE_HEADING.search(section["heading"].strip()):
        return True
    for earlier in reversed(sections[:index]):
        if earlier["level"] >= level or earlier["level"] < 2:
            continue
        if EVIDENCE_HEADING.search(earlier["heading"].strip()):
            return True
        level = earlier["level"]
    return False


def placements(sections: list[dict[str, Any]]) -> list[str]:
    """Where each section is read: consumed, view, reference, calculations, limits or audit.

    By the section's level-2 parent (itself when it is one). Only Findings is split further, and a
    section under any other level-2 heading, or under none, is audit (R34).
    """
    result: list[str] = []
    parent = ""
    for index, section in enumerate(sections):
        if section["level"] <= 2:
            parent = section["heading"] if section["level"] == 2 else ""
        heading = section["heading"]
        if parent in LEVEL_TWO_PLACEMENT:
            result.append(LEVEL_TWO_PLACEMENT[parent])
        elif parent != "Findings":
            result.append("audit")
        elif heading == "Reader summary" or heading.startswith(CHART_PREFIX):
            result.append("consumed")
        elif _is_evidence(sections, index):
            result.append("audit")
        elif any(block["type"] == "table" for block in section["blocks"]):
            result.append("reference")
        else:
            result.append("view")
    return result


def section_words(section: dict[str, Any]) -> int:
    """Whitespace-separated words of the section's prose and table cells; not its heading."""
    total = 0
    for block in section["blocks"]:
        if block["type"] == "text":
            total += len(block["text"].split())
        elif block["type"] == "table":
            total += sum(len(cell.split()) for row in block["rows"] for cell in row["cells"])
    return total


def report_fields(sections: list[dict[str, Any]], summary: dict[str, Any] | None) -> dict[str, Any]:
    """An output's state, section placement and word count per placement, for the run report."""
    established = None
    if summary is not None:
        confidence = str(summary["confidence"]).strip().casefold()
        established = not confidence.startswith(CONFIDENCE_NOT_ASSESSABLE)
    declared = None
    # parse_source emits YAML front matter only as the first section, at level 2; a later heading
    # of the same name is ordinary body, not the block.
    lead = sections[0] if sections else None
    if lead is not None and lead["heading"] == "Front matter" and lead["level"] == 2:
        text = "\n".join(b["text"] for b in lead["blocks"] if b["type"] == "text")
        match = COMMITTEE_STATUS.search(text)
        declared = match.group(1).strip() if match else None
    placement = placements(sections)
    words = dict.fromkeys(WORD_GROUPS, 0)
    for where, section in zip(placement, sections, strict=True):
        if where in words:
            words[where] += section_words(section)
    return {
        "state": {"established": established, "declared": declared},
        "placement": placement,
        "words": words,
    }
