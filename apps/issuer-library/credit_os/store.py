"""The library's store: every retained handoff in a workspace, parsed for reading.

Reads files only. Nothing here runs analysis, calls a provider or changes a workspace.
The server imports this on each page load, so it imports only the standard library.
"""

import csv
import datetime
import decimal
import hashlib
import json
import os
import re
import stat
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple, NotRequired, TypedDict
from urllib.parse import quote

from deploy_workflow import confidence

HERE = Path(__file__).resolve().parent
REPO = next((p for p in (HERE, HERE.parent) if (p / "src").is_dir()), HERE.parents[2])
OUTPUT_SKIP = re.compile(r"instructions|prompt|calculations|verification")
INPUT_NAME = re.compile(r"selected-input|peer-inputs|delivery|-request\.md")
HANDOFF_NAME = re.compile(r"CP-[A-Z0-9]+")
OUTPUT_SEPARATORS = ("-", "_", ".", " ")
AEROSPACE = "Aerospace & defense"
# Reading labels written by hand.
# Route key: (folder under runs/, issuer, title, run label, sector, period).
CURATED_RUNS: dict[str, tuple[str, ...]] = {
    "tdg-002": (
        "tdg-002",
        "TransDigm Group",
        "TransDigm Group",
        "TDG-002",
        AEROSPACE,
        "FY2024 historical evidence · later events separately dated",
    ),
    "tdg-003": (
        "tdg-003",
        "TransDigm Group",
        "TransDigm Group",
        "TDG-003",
        AEROSPACE,
        "FY2024 and quarter ended 28 December 2024",
    ),
    "tdg-004": (
        "tdg-004",
        "TransDigm Group",
        "TransDigm Group",
        "TDG-004",
        AEROSPACE,
        "19 September 2024 indenture · 6% secured notes due 2033",
    ),
    "tdg-guidance": (
        "tdg-guidance-001",
        "TransDigm Group",
        "TransDigm Group",
        "TDG-GUIDANCE",
        AEROSPACE,
        "7 November 2024 guidance · FY2025 outlook",
    ),
    "tdg-peers-2024": (
        "tdg-peers-2024-001",
        "TransDigm Group",
        "TransDigm & peers",
        "TDG-PEERS-2024",
        AEROSPACE,
        "Each company’s own FY2024 · unmatched fiscal dates",
    ),
    "tdg-run-comparison": (
        "tdg-run-comparison-001",
        "TransDigm Group",
        "TransDigm Group",
        "TDG-RUN-COMPARISON",
        AEROSPACE,
        "Build 2 compared with build 6 · 30 September 2024 financial base",
    ),
    "ford-otosan-2024": (
        "ford-otosan-2024-001",
        "Ford Otosan",
        "Ford Otosan",
        "FORD-OTOSAN-2024",
        "Automotive",
        "11 April 2024 · historical case",
    ),
    "frontier-2020": (
        "frontier-2020-001",
        "Frontier",
        "Frontier",
        "FRONTIER-2020",
        "Telecommunications",
        "29 June 2020 disclosure · historical case",
    ),
}
# The TransDigm builds kept under deliverables/ (history in README.md, VERIFICATION.md): a curated
# pin's compared deliverables must be among them.
CURATED_BUILDS = (
    "tdg-fy2024-snapshot",
    "tdg-fy2024-snapshot-2",
    "tdg-fy2024-snapshot-3",
    "tdg-fy2024-snapshot-4",
    "tdg-fy2024-snapshot-5",
    "tdg-fy2024-snapshot-6",
    "tdg-fy2024-snapshot-7",
)
SAFE_FOLDER = re.compile(r"[\w. -]+")
MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)


def valid_date(text: str) -> bool:
    """A real YYYY-MM-DD calendar date (not merely that shape)."""
    try:
        return bool(ISO_DATE.fullmatch(text)) and bool(datetime.date.fromisoformat(text))
    except ValueError:
        return False


def display_date(iso: Any) -> Any:
    """`31 December 2024` for a valid YYYY-MM-DD calendar date; any other text unchanged."""
    if not isinstance(iso, str) or not ISO_DATE.fullmatch(iso):
        return iso
    try:
        day = datetime.date.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


WEB_RUN = re.compile(r"web-[a-f0-9]{32}")


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


def physical_lines(text: str) -> list[str]:
    """The text's lines split on newlines only (`\\r\\n` and a lone `\\r` count as one), as
    delivery's `physical_lines` does, so a "line N" citation is the line a reader opens."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines[-1]:
        lines.pop()
    return lines


EQUITY_HEADERS = [
    "Reported equity movement",
    "Common shares (individual)",
    "Common stock par",
    "APIC",
    "Accumulated deficit",
    "Accumulated other comprehensive loss",
    "Treasury shares (individual)",
    "Treasury stock value",
    "Noncontrolling interests",
    "Total",
]


def equity_block(lines: list[str], i: int) -> tuple[dict[str, Any], int]:
    """The retained equity statement at `lines[i]` (the ```text fence): a delimited
    transcription, not prose. Its explicitly supplied column order governs this table."""
    start = i + 1
    rows = []
    i += 1
    while i < len(lines) and lines[i] != "```":
        label, values = lines[i].split(":", 1)
        row = [label] + [c.strip() for c in values.split("|")]
        if len(row) != len(EQUITY_HEADERS):
            raise ValueError(f"Malformed equity transcription at {i + 1}")
        rows.append({"line": i + 1, "cells": row})
        i += 1
    if i == len(lines):
        raise ValueError("Unclosed equity transcription")
    block = {
        "type": "table",
        "line": start,
        "headers": list(EQUITY_HEADERS),
        "rows": rows,
        "financial": True,
    }
    return block, i + 1


def source_table_cells(value: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", value.strip().strip("|"))]


def table_block(lines: list[str], i: int) -> tuple[dict[str, Any], int]:
    """The pipe table whose header is `lines[i]`; the separator row follows it."""
    start = i + 1
    headers = source_table_cells(lines[i])
    i += 2
    rows = []
    while i < len(lines) and lines[i].startswith("|"):
        row = source_table_cells(lines[i])
        if len(row) != len(headers):
            raise ValueError(f"Malformed table at line {i + 1}")
        rows.append({"line": i + 1, "cells": row})
        i += 1
    return {"type": "table", "line": start, "headers": headers, "rows": rows}, i


def text_block(lines: list[str], i: int) -> tuple[dict[str, Any], int]:
    """The paragraph starting at `lines[i]`, up to a blank line or the next structure.
    A line opening with three backticks starts a fenced block: one block up to its closing
    fence, blank lines and structure markers inside it kept. A fence closes only before the next
    `## ` or `### ` heading line; otherwise it is unclosed and is a paragraph. A fence line ends
    the paragraph before it."""
    start = i + 1
    if lines[i].startswith("```"):
        heads = (n for n in range(i + 1, len(lines)) if lines[n].startswith(("## ", "### ")))
        stop = next(heads, len(lines))
        close = next((n for n in range(i + 1, stop) if lines[n].rstrip() == "```"), None)
        if close is not None:
            return {
                "type": "text",
                "line": start,
                "end": close + 1,
                "text": "\n".join(lines[i : close + 1]),
            }, close + 1
    parts = [lines[i]]
    i += 1
    while (
        i < len(lines)
        and lines[i].strip()
        and not lines[i].startswith(("#", "|", "- ", "<!-- table-id:", "```"))
        and not re.match(r"\d+\. ", lines[i])
    ):
        parts.append(lines[i])
        i += 1
    return {"type": "text", "line": start, "end": i, "text": "\n".join(parts)}, i


def parse_source(text: str) -> list[dict[str, Any]]:
    """Keep every nonblank body line in one typed block with its source locator."""
    lines = physical_lines(text)
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    i = 0
    first = next((n for n, line in enumerate(lines) if line.strip()), None)
    if first is not None and lines[first] == "---":
        close = next((n for n in range(first + 1, len(lines)) if lines[n] == "---"), None)
        if close is not None:
            # YAML front matter: kept whole as the leading section, never dropped.
            body = [line for line in lines[first + 1 : close] if line.strip()]
            current = {"heading": "Front matter", "level": 2, "line": first + 1, "blocks": []}
            if body:
                start = next(n for n in range(first + 1, close) if lines[n].strip())
                end = max(n for n in range(first + 1, close) if lines[n].strip()) + 1
                current["blocks"].append(
                    {
                        "type": "text",
                        "line": start + 1,
                        "end": end,
                        "text": "\n".join(lines[start:end]),
                    }
                )
            sections.append(current)
            current = None  # a stray body line after the marker is not front matter: it raises
            i = close + 1
    while i < len(lines):
        line = lines[i]
        heading = re.match(r"^(#{1,4}) (.+)$", line)
        if heading:
            current = {"heading": heading[2], "level": len(heading[1]), "line": i + 1, "blocks": []}
            sections.append(current)
            i += 1
        elif not line.strip() or re.fullmatch(r"<!-- table-id: [\w.-]+ -->", line):
            # Blank, or a transport identifier preserved in the downloadable original.
            i += 1
        elif current is None:
            raise ValueError("Body before first heading")
        else:
            if line == "```text" and current["heading"].startswith("T4.4 —"):
                block, i = equity_block(lines, i)
            elif (
                line.startswith("|")
                and i + 1 < len(lines)
                and re.fullmatch(r"\|[\s:|\-]+\|", lines[i + 1])
            ):
                block, i = table_block(lines, i)
            else:
                block, i = text_block(lines, i)
            current["blocks"].append(block)
    return sections


# The one size limit for a delivered or uploaded file in this language. The Go server states the
# same 64 MiB as `maxFileBytes` (model.go); change the two together.
MODEL_FILE_LIMIT = 64 * 1024 * 1024
CHUNK = 1024 * 1024


class UnreadableFile(OSError):
    """A path that is not a plain, bounded file: absent is OSError; this is everything else."""


def regular_chunks(
    path: str | Path, follow: bool = True, limit: int = MODEL_FILE_LIMIT
) -> Iterator[bytes]:
    """The bytes of a regular file of at most `limit` bytes, in chunks.

    The kind and size are read from the open descriptor, so a path swapped for a FIFO after a
    check is still refused; the open never blocks on a FIFO.
    """
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    if not follow:
        flags |= getattr(os, "O_NOFOLLOW", 0)
        if Path(path).is_symlink():
            raise UnreadableFile("a link")
    try:
        descriptor = os.open(path, flags)
    except ValueError as error:  # An embedded NUL.
        raise UnreadableFile("an invalid path") from error
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise UnreadableFile("not a regular file")
        if info.st_size > limit:
            raise UnreadableFile("over the size limit")
        handle = os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise
    with handle:
        total = 0
        while chunk := handle.read(CHUNK):
            total += len(chunk)
            if total > limit:
                raise UnreadableFile("over the size limit")
            yield chunk


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for chunk in regular_chunks(path):
        digest.update(chunk)
    return digest.hexdigest()


def listed_bytes(folder: Path, delivery: dict[str, Any], name: str) -> bytes | None:
    """The bytes of folder/name when a plain file (no link) with the sha256 delivery.json lists."""
    try:
        data = b"".join(regular_chunks(folder / name, follow=False))
    except (OSError, UnreadableFile):
        return None
    return data if hashlib.sha256(data).hexdigest() == delivery["files"][name] else None


def recorded_revisions(run_dir: Path, issues: list[str]) -> list[tuple[str, str]]:
    """The earlier run ids this run records: cap.json `replayed_from_run` (a rerun of it) and
    research/attachments.json `supersedes`. Read only. A missing file records nothing; one that
    cannot be read is named in `issues`."""
    found: list[tuple[str, str]] = []
    for name, key, word in (
        ("cap.json", "replayed_from_run", "Rerun of"),
        ("research/attachments.json", "supersedes", "Supersedes"),
    ):
        try:
            raw = b"".join(regular_chunks(run_dir / name, follow=False))
            earlier = json.loads(raw.decode("utf-8")).get(key)
        except FileNotFoundError:
            continue
        except (OSError, ValueError, AttributeError, TypeError, RecursionError) as error:
            issues.append(f"{run_dir.name}: {name} could not be read ({describe(error)})")
            continue
        if isinstance(earlier, str) and earlier:
            found.append((word, earlier))
    return found


def describe(error: BaseException) -> str:
    """An error as its type and a short reason; never the repr, which can hold file bytes."""
    if isinstance(error, UnicodeDecodeError):
        return f"UnicodeDecodeError: {error.reason}"
    return f"{type(error).__name__}: {str(error)[:80]}"


def delivery_json(folder: Path) -> dict[str, Any]:
    """folder/delivery.json read bounded and without following a link; raises when unreadable."""
    loaded: dict[str, Any] = json.loads(
        b"".join(regular_chunks(folder / "delivery.json", follow=False)).decode("utf-8")
    )
    return loaded


def listed_view(folder: Path, delivery: dict[str, Any]) -> dict[str, Any]:
    """folder/view.json when a plain file with the hash delivery.json lists; raises otherwise."""
    if not isinstance(delivery.get("files"), dict):
        raise TypeError("files is not an object")
    raw = listed_bytes(folder, delivery, "view.json")
    if raw is None:
        raise UnreadableFile("view.json is not the plain file its delivery record lists")
    view: dict[str, Any] = json.loads(raw.decode("utf-8"))
    return view


def locate_quote(
    sections: list[dict[str, Any]], locator: dict[str, Any], owner: str
) -> dict[str, Any]:
    """Return a block's opening sentences verbatim, or fail the build."""
    for section in sections:
        if not section["heading"].startswith(locator["heading"]):
            continue
        for block in section["blocks"]:
            flat = re.sub(
                r"\s+", " ", block.get("text", "").replace("**", "").replace("`", "")
            ).strip()
            if flat.startswith(locator["startsWith"]):
                ends = [m.end() for m in re.finditer(r"[.!?](?:\*\*)?(?=\s|$)", block["text"])]
                text = block["text"][: ends[locator["sentences"] - 1]]
                if text.count("**") % 2:
                    raise ValueError(f"{owner}: quote {locator} cuts through bold text")
                return {"line": block["line"], "text": text}
    raise ValueError(f"{owner}: quote locator no longer matches {locator}")


def output_label(module: str, path: Path, siblings: list[Path]) -> tuple[str, int | None]:
    """Name a saved output from its file; a label never ranks it as accepted or primary."""
    rest = path.name.removeprefix(module).removesuffix(".md")
    # At most one separator follows the module code; a name with nothing else is its own label.
    stem = (rest[1:] if rest[:1] in OUTPUT_SEPARATORS else rest) or (path.name if rest else module)
    attempt = re.fullmatch(r"(?:(.+)-)?attempt-(\d+)", stem)
    if not attempt:
        repeated = sum(s.name == path.name for s in siblings) > 1
        delivered = repeated and path.parent.parent.name == "deliveries"
        return stem[0].upper() + stem[1:] + (
            f" · delivery {path.parent.name[:8]}" if delivered else ""
        ), None
    # Siblings in the same series share the file name up to "attempt-", taken literally.
    head = re.escape(path.name.removesuffix(f"attempt-{attempt[2]}.md"))
    total = sum(bool(re.fullmatch(rf"{head}attempt-\d+\.md", s.name)) for s in siblings)
    counted = f"attempt {attempt[2]} of {total}"
    return (f"{attempt[1].capitalize()} · {counted}" if attempt[1] else counted.capitalize()), int(
        attempt[2]
    )


def default_output(
    folder: str, sources: list[str], pinned: str | None, attempts: dict[str, int | None]
) -> str | None:
    """Pinned file, else the only file, else the highest attempt; unnumbered variants pick none."""
    if pinned:
        return pinned
    if len(sources) == 1:
        return f"{folder}/{sources[0]}"
    numbered = [(attempts[s], s) for s in sources if attempts[s] is not None]
    return f"{folder}/{max(numbered)[1]}" if numbered else None


def locate_row(
    sections: list[dict[str, Any]], locator: dict[str, Any], owner: str
) -> dict[str, Any]:
    """Return the retained table cell that states the output's unit, or fail the build."""
    for row in (row for s in sections for b in s["blocks"] for row in b.get("rows", [])):
        if row["cells"][0] == locator["row"]:
            if locator["unit"] not in row["cells"][1]:
                raise ValueError(
                    f"{owner}: basis row {locator['row']} does not state {locator['unit']}"
                )
            return {"line": row["line"], "text": row["cells"][1], "unit": locator["unit"]}
    raise ValueError(f"{owner}: basis locator no longer matches {locator}")


def pinned_fields(
    sections: list[dict[str, Any]], config: dict[str, Any], module: str
) -> dict[str, Any]:
    """Curated fields of a pinned output; a locator that no longer matches fails the build."""
    fields = {
        "period": config["period"],
        "scope": config["scope"],
        "compare": config.get("compare"),
    }
    if "call" in config:
        fields["call"] = locate_quote(sections, config["call"], module)
    if "basis" in config:
        fields["basis"] = locate_row(sections, config["basis"], module)
    visual = config.get("visual")
    if visual:
        if not any(
            b["type"] == "table" and b["line"] == visual["table"]
            for s in sections
            for b in s["blocks"]
        ):
            raise ValueError(f"{module}: visual table locator no longer matches")
        quote = visual.get("noteQuote")
        fields["visual"] = (
            {**visual, "quote": locate_quote(sections, quote, module)} if quote else visual
        )
    return fields


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
STATED_GAP = re.compile(r"Not supplied:\s*\S")


def _bridge_amounts(table: dict[str, Any]) -> list[decimal.Decimal] | None:
    """A step table's stated amounts when it is a bridge that reconciles, else None.

    Mirrors the launcher's check (cpos_launch.py `_bridge_issues`; the store imports the standard
    library only): every Amount a plain signed number, and the opening plus the stated changes equal
    to the closing. Each amount has at most the table's own decimals, so the sum is exact."""
    cells = [row["cells"][1] for row in table["rows"]]
    if len(cells) < 2 or not all(PLAIN_AMOUNT.fullmatch(c) for c in cells):
        return None
    values = [decimal.Decimal(c.replace(",", "")) for c in cells]
    return values if sum(values[:-1], decimal.Decimal(0)) == values[-1] else None


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
    reasons = list(dict.fromkeys(c.partition(":")[2].strip() for c in cells))
    return {**_chart_head(section, table), "gap": "; ".join(reasons)}


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
        if roles["kind"] == "stack" and any(
            not STATED_GAP.match(r["cells"][3]) and r["cells"][-2] != "US$m" for r in rows
        ):
            return None
        units = {row["cells"][-2] for row in rows}
        # A single stated unit is the figure's; rows in different units each state their own.
        return {**roles, "unit": units.pop() if len(units) == 1 else "", "columns": list(numeric)}
    return None


def _chart_head(section: dict[str, Any], table: dict[str, Any]) -> dict[str, Any]:
    # Only the first letter is raised: an acronym in the heading keeps its case.
    title = section["heading"].removeprefix(CHART_PREFIX)
    return {"title": title[:1].upper() + title[1:], "table": table["line"]}


def _period_cells_ok(section: dict[str, Any], table: dict[str, Any]) -> bool:
    """Owner period and step tables use US$m, except cells explicitly stating a gap."""
    fixed = table["headers"][0] == "Step" or section["heading"] in (
        "Chart data: revenue and EBITDA",
        "Chart data: refinancing need",
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
    stated = all(c and not STATED_GAP.match(c) for c in cells)
    kind = EVENT_STATUS.match(cells[4])
    return bool(
        dated
        and stated
        and kind
        and (published == "\u2014" or valid_date(published))
        and published != when
    )


def _event_lane(section: dict[str, Any]) -> dict[str, Any] | None:
    """A calendar lane from an `Events: <lane>` table in its fixed shape, else None. A table of
    only stated gaps is a lane with its reason and no events."""
    tables = [b for b in section["blocks"] if b["type"] == "table"]
    if len(tables) != 1 or tables[0]["headers"] != EVENT_HEADERS or not tables[0]["rows"]:
        return None
    rows = [row["cells"] for row in tables[0]["rows"]]
    lane = {"lane": section["heading"].removeprefix(EVENT_PREFIX), "table": tables[0]["line"]}
    if all(STATED_GAP.match(c) for cells in rows for c in cells):
        return {**lane, "gap": rows[0][0].partition(":")[2].strip()}
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
        return {**drawn, "gap": rows[0][0].partition(":")[2].strip()}
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


def sections_of(text: str) -> list[dict[str, Any]]:
    """parse_source, typed as a list of section dicts."""
    sections: list[dict[str, Any]] = parse_source(text)
    return sections


def structured(raw: bytes, strict: bool) -> tuple[list[dict[str, Any]], str | None]:
    """Typed blocks. In the app a handoff the parser refuses stays readable as one flagged block.

    A UTF-8 byte-order mark, which Windows editors often write, is not part of the first heading.
    """
    try:
        return sections_of(raw.decode("utf-8-sig")), None
    except ValueError as error:
        if strict:
            raise
        text = raw.decode("utf-8-sig", "replace")
        block = {"type": "text", "line": 1, "end": text.count("\n") + 1, "text": text}
        return [{"heading": "Unstructured handoff", "level": 1, "line": 1, "blocks": [block]}], str(
            error
        )


def linked(folder: Path) -> bool:
    """A symbolic link or Windows junction: either can lead a folder out of its run."""
    return folder.is_symlink() or folder.is_junction()


class Handoff(NamedTuple):
    """One handoff file as read once: the parsed text and every hash shown come from these bytes."""

    module: str
    raw: bytes
    sha256: str


def handoff_files(run_dir: Path) -> dict[Path, Handoff]:
    """Handoffs at the run root, then those the launcher delivered; each distinct file once."""
    found: dict[Path, Handoff] = {}
    seen: set[str] = set()
    base = run_dir.resolve()
    for path in [*sorted(run_dir.glob("CP-*.md")), *sorted(run_dir.glob("deliveries/*/CP-*.md"))]:
        # The server serves regular files only, so a link out of the run is not a handoff either:
        # not a linked file, not a linked or junctioned delivery folder, nothing resolving outside.
        if (
            # Windows matches these patterns regardless of case; the names here do not.
            (match := HANDOFF_NAME.match(path.name))
            and path.name.endswith(".md")
            and not OUTPUT_SKIP.search(path.name)
            and path.is_file()
            and not path.is_symlink()
            and (path.parent == run_dir or not linked(path.parent))
            and path.resolve().is_relative_to(base)
        ):
            # Bounded: a handoff over the server's read cap raises; the run is hidden and reported.
            raw = b"".join(regular_chunks(path))
            digest = hashlib.sha256(raw).hexdigest()
            if digest not in seen:
                seen.add(digest)
                found[path] = Handoff(match[0], raw, digest)
    return found


def confidence_fields(raw: bytes) -> dict[str, Any]:
    """`confidence` for an output whose handoff has a `### Confidence inputs` section: the score
    Python computes from it, or why there is none. A handoff without the section (every earlier
    run) gets no field at all. Lossy decoding only touches bytes that cannot be in the table."""
    result = confidence.from_handoff(raw.decode("utf-8-sig", "replace"))
    if isinstance(result, confidence.Refused):
        return {} if result.absent else {"confidence": {"missing": result.reason.replace("`", "")}}
    return {"confidence": {"value": result.value, "band": result.band}}


class Handoffs:
    """Each distinct handoff parsed once, by digest, however many runs hold the same bytes."""

    def __init__(self, strict: bool) -> None:
        self.strict = strict
        self.parsed: dict[str, tuple[list[dict[str, Any]], str | None]] = {}

    def read(self, digest: str, raw: bytes) -> tuple[list[dict[str, Any]], str | None]:
        """The sections and parse problem of these bytes; the problem is each output's to report."""
        if digest not in self.parsed:
            self.parsed[digest] = structured(raw, self.strict)
        return self.parsed[digest]


def collect_runs(
    root: Path,
    shown: dict[str, tuple[str, ...]],
    catalog: dict[str, Any],
    link: Callable[[str, str, str], str],
    handoffs: Handoffs,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, str],
    list[str],
]:
    """Parse every saved output of every shown run; each file keeps its own identity.

    The parsed sections are not in the records: they stay in `handoffs` by digest, so a handoff
    saved in many runs is parsed once and held once. A caller that sends the records sends
    `handoffs.parsed` beside them. Pass one `Handoffs` across calls to share it.
    """
    strict = handoffs.strict
    runs: dict[str, Any] = {}
    outputs: dict[str, Any] = {}
    inputs: dict[str, Any] = {}
    pins: dict[str, str] = {}
    issues: list[str] = []
    for key, (folder, issuer, title, label, sector, period) in shown.items():
        run_dir = root / "runs" / folder

        # The default binds this run's folder.
        def relative(path: Path, base: Path = run_dir) -> str:
            return path.relative_to(base).as_posix()

        grouped: dict[str, dict[str, list[Path]]] = {}
        read = handoff_files(run_dir)
        for path, handoff in read.items():
            kind = "inputs" if INPUT_NAME.search(path.name) else "outputs"
            grouped.setdefault(handoff.module, {"outputs": [], "inputs": []})[kind].append(path)
        modules: dict[str, Any] = {}
        first: str | None = None
        for module, files in grouped.items():
            config = catalog.get(module, {})
            pinned: str | None = None
            labels = {
                relative(f): output_label(module, f, files["outputs"]) for f in files["outputs"]
            }
            for path in files["outputs"]:
                name = relative(path)
                output_id = f"{folder}/{name}"
                digest = read[path].sha256
                sections, problem = handoffs.read(digest, read[path].raw)
                record: dict[str, Any] = {
                    "id": output_id,
                    "run": key,
                    "module": module,
                    "source": name,
                    "file": f"{folder}--{name.replace('/', '--')}",
                    "href": link(folder, name, digest),
                    "label": labels[name][0],
                    "sha256": digest,
                    "case": f"{title} · {label}",
                    "period": period,
                    "scope": "Retained module output",
                    "firstHeading": config.get("firstHeading"),
                }
                record.update(reader_fields(sections))
                record.update(report_fields(sections, record["summary"]))
                record.update(confidence_fields(read[path].raw))
                if record["issue"]:
                    issues.append(f"{output_id}: {record['issue']}")
                if problem:
                    record["parseError"] = problem
                    issues.append(f"{output_id}: shown unstructured ({problem})")
                if config.get("path") == output_id:
                    try:
                        record.update(pinned_fields(sections, config, module))
                        pins[module] = pinned = output_id
                        first = first or module
                    except (ValueError, KeyError, IndexError) as error:
                        if strict:
                            raise
                        issues.append(f"{module}: curated pin dropped: {error}")
                outputs[output_id] = record
            for path in files["inputs"]:
                name = relative(path)
                digest = read[path].sha256
                inputs[f"{folder}/{name}"] = {
                    "module": module,
                    "run": key,
                    "source": name,
                    "file": f"{folder}--{name.replace('/', '--')}",
                    "href": link(folder, name, digest),
                    "sha256": digest,
                }
            sources_here = [relative(f) for f in files["outputs"]]
            modules[module] = {
                "outputs": [f"{folder}/{s}" for s in sources_here],
                "inputs": [f"{folder}/{relative(f)}" for f in files["inputs"]],
                "default": default_output(
                    folder, sources_here, pinned, {s: labels[s][1] for s in sources_here}
                )
                if sources_here
                else None,
            }
        with_outputs = [module for module in modules if modules[module]["outputs"]]
        recorded = recorded_run(run_dir, issues)
        runs[key] = {
            "runId": recorded.get("run_id"),
            "revisions": [
                {"word": word, "id": run_id, "run": None}
                for word, run_id in recorded_revisions(run_dir, issues)
            ],
            "folder": folder,
            "issuer": issuer,
            "title": title,
            "run": label,
            "sector": sector,
            "period": period,
            "pathway": recorded.get("pathway") or None,
            "asOf": recorded.get("as_of") or None,
            "first": first or (with_outputs[0] if with_outputs else "W-Overview"),
            "modules": modules,
        }
    return runs, outputs, inputs, pins, issues


# Each folder's (delivery.json, listed view.json), or describe(error) when it cannot be read.
Manifests = dict[str, "tuple[dict[str, Any], dict[str, Any]] | str"]


def curated_builds(catalogue: dict[str, Any], manifests: Manifests) -> set[str]:
    """Names of the curated TransDigm builds the library holds as verified deliverables.

    A build is curated when its folder is deliverables/<name> for a name in CURATED_BUILDS and its
    view.json records TransDigm Group as the issuer: a folder that merely has the name is not one.
    Only delivery.json and view.json (the `manifests`) are read; no report file is needed.
    """
    builds = set()
    for found in delivery_identities(Path(), catalogue, manifests):
        name = Path(found["folder"]).name
        if (
            found["folder"] == f"deliverables/{name}"
            and name in CURATED_BUILDS
            and str(found["issuer_name"]).startswith("TransDigm Group")
        ):
            builds.add(name)
    return builds


def register_of(sections: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The section whose heading names an assumption register, or CP-2G's register id T2H.3
    (the method fixes the id, not the wording): heading, intro, table rows."""
    for section in sections:
        heading = section["heading"].casefold()
        if "assumption register" not in heading and not heading.startswith("t2h.3"):
            continue
        text = next((b["text"] for b in section["blocks"] if b["type"] == "text"), None)
        table = next((b for b in section["blocks"] if b["type"] == "table"), None)
        return {
            "heading": section["heading"],
            "intro": text,
            "headers": table["headers"] if table else [],
            "rows": [row["cells"] for row in table["rows"]] if table else [],
        }
    return None


def text_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def source_location(root: Path, path: Any) -> Path | None:
    """The file a model source names, only if it is runs/<folder>/<file> inside root."""
    if not isinstance(path, str) or "\\" in path or ":" in path:
        return None
    parts = PurePosixPath(path).parts
    if len(parts) < 3 or parts[0] != "runs" or PurePosixPath(path).is_absolute():
        return None
    if ".." in parts:
        return None
    try:
        resolved = (root / path).resolve()
    except (ValueError, OSError):  # An embedded NUL or an unresolvable path is an invalid source.
        return None
    return resolved if resolved.is_relative_to(root.resolve()) else None


def model_sources(
    root: Path,
    delivery: dict[str, Any],
    outputs: dict[str, Any],
    folder: str | None = None,
    issues: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Each source a model declares, whether its file has the declared bytes, and the output.

    A source whose path is not a confined runs/<folder>/<file> or whose hash is not 64 lowercase hex
    keeps its row with sha256 and changed null; its file is never opened. A source that is not a
    regular file of at most 64 MiB is likewise kept with nulls and named in the issues; an absent
    file stays "changed". The issues are appended to `issues`, prefixed with `folder`.
    """
    rows: list[dict[str, Any]] = []
    issues = [] if issues is None else issues
    declared_sources = delivery.get("sources")
    for role, source in (declared_sources if isinstance(declared_sources, dict) else {}).items():
        source = source if isinstance(source, dict) else {}
        path, declared = source.get("path"), source.get("sha256")
        location = source_location(root, path)
        valid = (
            location is not None
            and isinstance(declared, str)
            and re.fullmatch(r"[0-9a-f]{64}", declared) is not None
        )
        row = {
            "role": role,
            "path": path if isinstance(path, str) else None,
            "sha256": declared if valid else None,
            "changed": None,
            "run": None,
            "output": None,
        }
        if location is not None and valid:
            try:
                row["changed"] = sha256(location) != declared
            except UnreadableFile:
                row["sha256"] = None
                issues.append(f"{folder}: source {role} is not a readable file")
            except OSError:
                row["changed"] = True
            held = outputs.get(str(path).removeprefix("runs/"))
            match = held if held and held["sha256"] == declared else None
            if match and row["sha256"] is not None:
                row["run"], row["output"] = match["run"], match["id"]
        else:
            issues.append(f"{folder}: source {role} has an invalid path or hash")
        rows.append(row)
    return rows


CASHFLOW_FILES = ("forecast_exact.json", "calculation.json", "annual.md", "quarter.md")
# The CP-1 handoff table labels the cash flow reader matches, exactly as the handoffs print them
# (TDG wording). To read another issuer's handoffs, add or change its labels here; nothing else in
# the reader names a handoff label. Matching is exact and case-sensitive except the debt register,
# which is matched case-insensitively (see secured_debt).
CASHFLOW_LABELS = {
    "revenue": "NET SALES",
    "cogs": "COST OF SALES",
    "gross_profit": "GROSS PROFIT",
    "selling_admin": "SELLING AND ADMINISTRATIVE EXPENSES",
    "amortization": "AMORTIZATION OF INTANGIBLE ASSETS",
    "operating_income": "INCOME FROM OPERATIONS",
    "segment_revenue": "Net Sales",
    "total_prefix": "Total",
    "da": "Depreciation and amortization expense",
    "issuer_ebitda": "EBITDA",
    "adjusted_ebitda": "Total Company EBITDA As Defined",
    "interest_net": "Interest expense-net",
    "pretax_income": "Income from continuing operations before income taxes",
    "secured_securitization": "Trade receivable securitization",
    "secured_term_loans": "Term loans aggregate",
    "secured_notes": "secured notes",
    "unsecured_notes": "subordinated",
    "unsecured": "unsecured",
    "label_header": "Label",
    "period_header": "Period",
    "period_end_header": "End",
}
# Inputs beyond these are refused before any cell is built (see CashflowLimit).
QUARTER_COLUMN_LIMIT = 40
FORECAST_YEAR_LIMIT = 20
FISCAL_YEAR_LIMIT = 20
UNIT_ROW_LIMIT = 200
ADD_BACK_ROW_LIMIT = 200
TABLE_ROW_LIMIT = 2000
QUARTER_DAYS = 100
QUARTER_LENGTH_SLACK = 7
FORECAST_CASES = (
    ("REFERENCE", "Base case"),
    ("UPSIDE", "Upside"),
    ("DOWNSIDE_DRIVERS", "Downside (CP-2G drivers)"),
    ("DOWNSIDE", "Downside stress (shock on base drivers)"),
)
NO_VALUE = "the model's source table has no value for this period"
PRINTED_DASH = "printed as \u2014 in the source"
PRIOR_MISSING = "prior-year period not in the handoffs"
COMPONENT_MISSING = "a component is not in the handoffs"
REASON_PHRASES = {
    "NOT_SOURCED": "not reported in the source",
    "NOT_STATED": COMPONENT_MISSING,
    "ZERO_OR_NEGATIVE_DENOMINATOR": "a divisor is zero or negative",
    "COMPONENT_MISSING": COMPONENT_MISSING,
    "PRIOR_PERIOD_MISSING": PRIOR_MISSING,
    "REGISTER_DATE_DIFFERS": "secured-debt carrying values are recorded at another date",
    "UNCLASSIFIED_ROW": "the debt register has a row that cannot be classified",
    "WINDOW_MISSING": "last-twelve-months Adj EBITDA cannot be built from the handoffs",
}
LTM_NEEDED = "needs last-twelve-months Adj EBITDA for this quarter, which is not recorded"
DEBT_TOTAL_NEEDED = "needs quarter-end total carrying debt, which the model does not derive"
DEBT_SENIOR_NEEDED = (
    "needs quarter-end senior secured carrying debt, which the model does not derive"
)
MONTHS_SHORT = {name[:3]: number for number, name in enumerate(MONTHS, 1)}
Q1_NOTE = "Q1 is the first quarter of the fiscal year, so it is also the year to date."
CASHFLOW_NOTES = (
    Q1_NOTE,
    "Pro forma: no pro forma period is recorded in the handoffs.",
    (
        "Base case is the model's reference case: a conditional illustration, not an "
        "evidence-supported central issuer forecast."
    ),
    "n.m. \u2014 not modelled: the calculation record does not project this line.",
    (
        "EBITDA (EBIT + D&A) differs from the issuer's reported EBITDA, which also deducts "
        "refinancing costs and includes other income or expense."
    ),
    (
        "Adj EBITDA is the issuer's EBITDA As Defined, a non-GAAP measure; in the forecast it is "
        "the model's earnings on that basis, not issuer guidance."
    ),
    (
        "Leverage uses carrying debt including securitization; senior secured debt is the term "
        "loans, secured notes and securitization at carrying value. Ratios are shown for fiscal "
        "years only."
    ),
)
FISCAL_ONLY_RATIOS = "Ratios are shown for fiscal years only."
TWELVE_MONTH_RATIOS = "Leverage is shown for twelve-month periods only."
LTM_NOTE = (
    "LTM is the last fiscal year when that is the latest period CP-1 labels; otherwise the last "
    "fiscal year plus the year to date less the prior year to date."
)
HISTORY_LIMIT_COUNT = 200
HISTORY_LIMIT_CHARS = 2000
# The prior a history column of a kind may name, as the period history writes them.
HISTORY_PRIOR_KINDS = {"QUARTER": "QUARTER", "YTD": "PYTD", "FY": "FY", "LTM": "PRIOR_LTM"}
FY_PLACEHOLDER = "Fiscal year"  # the id of the fiscal-year column when CP-1 prints no year
NO_LINE = "the period history does not carry this line"
LENGTH_DIFFERS = "the prior-year period has a different length"
PRIOR_NOT_YEAR = "the prior fiscal year is not twelve months"
YEAR_DAYS = range(364, 372)  # a 52- or 53-week year, both ends counted
HISTORY_SCHEMA = "cpos-history/1"
HISTORY_COLUMN_LIMIT = 60
HISTORY_GROUPS = {
    "QUARTER": "Quarter",
    "YTD": "Year to date",
    "PYTD": "Year to date",
    "FY": "Fiscal year",
    "LTM": "Last twelve months",
    "PRIOR_LTM": "Last twelve months",
    "PF": "Pro forma",
}
HISTORY_KEYS = frozenset(("id", "kind", "label", "prior", "reason", "start", "end", "values"))
QUARTER_HEADER = re.compile(r"(\d{4}-\d{2}-\d{2})[–-](\d{4}-\d{2}-\d{2})", re.ASCII)
FISCAL_HEADER = re.compile(r"FY\d{4}", re.ASCII)
TABLE_NUMBER = re.compile(r"(\()?((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(\))?", re.ASCII)
SEPARATOR_CELL = re.compile(r":?-+:?")
CARRYING = re.compile(r"carrying\s+(\d[\d,]*(?:\.\d+)?)", re.ASCII)
REGISTER_DATE = re.compile(r"\b([A-Z][a-z]{2}) (\d{1,2}), (\d{4})\b", re.ASCII)


class Cell(TypedDict):
    """One grid cell. `status` is value, na (not available, with a reason) or nm (not modelled)."""

    exact: str | None
    display: str
    reason: str | None
    status: str


PeriodKey = tuple[str, ...]
Span = tuple[str, ...]  # (start, end) ISO dates of a quarter column
SecuredDebt = tuple[datetime.date, decimal.Decimal | None, str | None]
Spec = tuple[Any, ...]  # (operation name, *its arguments); see CELL_OPS
RowKey = str | tuple[str, str]
Forecast = list[tuple[str, list[dict[str, Any]]]]  # (case name, that case's years)
Fiscal = list[tuple[str, dict[str, Any]]]  # (fiscal year label, its values)
History = tuple[list[dict[str, Any]], list[str]]  # (validated history columns, their limits)
Recorded = tuple[Fiscal, dict[str, dict[str, Any]], History | None]


class Table(TypedDict):
    """A Markdown table: its header, rows by first-found label, and column index by period."""

    header: list[str]
    rows: dict[str, list[str]]
    periods: dict[PeriodKey, int]
    repeated: str | None
    interrupted: str | None


class Column(TypedDict):
    """A grid column; `prior` is the index of its prior-year column."""

    label: str
    group: str
    kind: str
    record: dict[str, Any] | None
    start: str | None
    end: str | None
    period: PeriodKey | None
    prior: int | None
    ytd: bool
    length_differs: NotRequired[bool]
    prior_not_year: NotRequired[bool]
    unavailable: NotRequired[str]


def display_amount(exact: str, kind: str) -> str:
    """An exact decimal string as the reader sees it: half-up, money in brackets when negative."""
    with decimal.localcontext(decimal.Context(prec=200)) as context:
        value = decimal.Decimal(exact)
        if not value.is_finite():
            raise ValueError(f"not a finite decimal: {exact!r}")
        if kind in ("percent", "multiple"):
            scaled = value * 100 if kind == "percent" else value
            two = scaled.quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP, context)
            if two == 0:
                two = abs(two)  # a negative that rounds to zero is not shown as -0.00
            return f"{two:,.2f}{'%' if kind == 'percent' else 'x'}"
        rounded = value.quantize(decimal.Decimal(1), decimal.ROUND_HALF_UP, context)
        if rounded == 0:
            return "0"  # a negative that rounds to zero is not shown as -0 or in brackets
        return f"({-rounded:,})" if rounded < 0 else f"{rounded:,}"


def cashflow_units(handoff: str) -> str | None:
    """The first '<ISO currency> millions|billions|thousands' phrase of the Request section."""
    request = re.search(
        r"^## Request[ \t]*\r?\n(.*?)(?=^## |\Z)", handoff, re.MULTILINE | re.DOTALL
    )
    phrase = (
        re.search(r"\b[A-Z]{3}\s+(?:millions|billions|thousands)\b", request.group(1))
        if request
        else None
    )
    return re.sub(r"\s+", " ", phrase.group(0)) if phrase else None


UNITS_LIMIT = 40


def recorded_units(exact: Any) -> str | None:
    """The `units` the forecast record states for its published figures, or None when it states
    none. `scale` and `units` are recorded together. `units` is a printable text of 1 to
    UNITS_LIMIT characters with something visible in it (no control, bidi-control or newline
    character); anything else is not shown: TypeError."""
    if not isinstance(exact, dict):
        return None
    units = exact.get("units")
    if (units is None) != (exact.get("scale") is None):
        raise TypeError("scale and units are not recorded together")
    if units is None:
        return None
    if not isinstance(units, str) or not 1 <= len(units) <= UNITS_LIMIT:
        raise TypeError("units is not a short text")
    if not units.isprintable() or not units.strip():
        raise TypeError("units is not printable text")
    return units


def units_caption(units: str | None, handoff: str | None) -> str | None:
    """The record's own statement of its units; without one, the Request section's phrase."""
    if units is not None:
        return units
    return cashflow_units(handoff) if handoff is not None else None


class CashflowBudget(Exception):
    """A grid larger than the cells left in the workspace's budget; raised before any cell."""


class CashflowLimit(Exception):
    """A cash flow input larger than the reader accepts; names the file and what was too large."""

    def __init__(self, file: str, what: str, found: int, limit: int) -> None:
        super().__init__(f"{file} exceeds the cash flow model's limits ({what}, {found} > {limit})")


def grid_cell(
    exact: str | None, display: str, reason: str | None = None, status: str = "value"
) -> Cell:
    return {"exact": exact, "display": display, "reason": reason, "status": status}


def amount_cell(exact: str, kind: str) -> Cell:
    return grid_cell(exact, display_amount(exact, kind))


def absent_cell() -> Cell:
    return unavailable_cell(NO_VALUE)


def unavailable_cell(reason: str | None) -> Cell:
    return grid_cell(None, "n.a.", reason, "na")


def not_modelled_cell() -> Cell:
    return grid_cell(None, "n.m.", "not modelled in the calculation record", "nm")


def held_cell(held: dict[str, Any], kind: str, negate: bool = False) -> Cell:
    """A calculation record's {amount, reason}; an amount of null is n.a. with its reason."""
    exact = held["amount"]
    if exact is None:
        reason, note = held.get("reason"), held.get("note")
        words = REASON_PHRASES.get(reason, reason) if isinstance(reason, str) else None
        if reason == "WINDOW_MISSING" and isinstance(note, str) and note:
            words = f"{words}: {note[:LABEL_LIMIT]}"  # the cause the delivery recorded
        return unavailable_cell(words)
    if negate:
        value = decimal.Decimal(exact).copy_negate()
        exact = "0" if value == 0 else str(value)
    return amount_cell(exact, kind)


def checked_entries(record: dict[str, Any], skip: tuple[str, ...] = ()) -> None:
    """Every entry of a calculation record but `skip` is {amount: text|null, reason: text|null}."""
    for key, held in record.items():
        if key in skip:
            continue
        if not isinstance(held, dict) or not {"amount", "reason"} <= held.keys():
            raise TypeError(f"{key} is not an amount and a reason")
        exact, reason = held["amount"], held["reason"]
        if not (reason is None or isinstance(reason, str)):
            raise TypeError(f"the reason of {key} is not text")
        if exact is None:
            continue
        if not isinstance(exact, str) or len(exact) > 200:
            raise ValueError("an amount is not a decimal string")
        display_amount(exact, "money")  # a non-finite or out-of-range amount raises here
        display_amount(exact, "percent")


def source_cell(text: str, kind: str) -> Cell:
    """A Markdown table cell as the handoff printed it."""
    if text == "":
        return absent_cell()
    if text == "\u2014":
        return unavailable_cell(PRINTED_DASH)
    found = TABLE_NUMBER.fullmatch(text) if len(text) <= 40 else None
    if found is None or bool(found.group(1)) != bool(found.group(3)):
        return unavailable_cell("source cell is not a number")
    digits = found.group(2).replace(",", "")
    negative = found.group(1) and decimal.Decimal(digits) != 0
    return amount_cell(f"-{digits}" if negative else digits, kind)


def table_cells(line: str) -> list[str]:
    """The cells of a table row; an escaped pipe (backslash, pipe) is text inside a cell."""
    inner = line.strip().removeprefix("|").removesuffix("|")
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", inner)]


MARKS = re.compile(r"[*_()]")
TOTAL_AT_EDGE = re.compile(r"(?:(?:sub)?totals?\b.*|.*\b(?:sub)?totals?)")
TOTAL_WORD = re.compile(r"\b(?:sub)?totals?\b")
SEPARATOR = re.compile(r"[ \t]*(?=[^-]*-)(?=.*\|)[ \t:|-]+")
TABLE_ROW = re.compile(r" {0,3}(\|.*?)\s*")
CODE_SPAN = re.compile(r"(`+).+?\1")
FENCE_LINE = re.compile(r"[ \t]*(?:`{3,}|~{3,})")
HEADING_START = re.compile(r" {0,3}(#{1,6})(?:[ \t]|$)")


def plain_label(label: str) -> str:
    """A register row label as classified, delivery's `_plain` written again: emphasis marks and
    parentheses removed, whitespace runs one space, trailing `:` and `.` stripped, casefolded."""
    text = " ".join(MARKS.sub("", label).split())
    return text.rstrip(":.").strip().casefold()


def total_kind(low: str) -> str | None:
    """`edge` when the whole word total or subtotal starts or ends the plain label (a subtotal),
    `inner` when it sits elsewhere (a row that cannot be classified), else None."""
    if TOTAL_AT_EDGE.fullmatch(low):
        return "edge"
    return "inner" if TOTAL_WORD.search(low) else None


def table_row(line: str) -> str | None:
    """The row text of a line that starts with '|' after at most three spaces (four is code),
    without trailing whitespace; None for any other line."""
    found = TABLE_ROW.fullmatch(line)
    return None if found is None else found[1]


def inline_comments(line: str) -> tuple[str, bool]:
    """`line` without its complete HTML comments, and whether one is still open at its end.
    Code spans are blanked before looking for `<!--`; `<!-->` and `<!--->` are whole comments."""
    kept = ""
    while True:
        masked = CODE_SPAN.sub(lambda m: "x" * len(m[0]), line)
        opener = masked.find("<!--")
        if opener < 0:
            return kept + line, False
        if masked.startswith(">", opener + 4):
            end = opener + 5
        elif masked.startswith("->", opener + 4):
            end = opener + 6
        elif (closer := masked.find("-->", opener + 4)) >= 0:
            end = closer + 3
        else:
            return kept + line[:opener], True
        kept, line = kept + line[:opener], line[end:]


def shown_lines(lines: list[str]) -> list[str]:
    """The lines as a Markdown viewer shows them (delivery's `_shown` written again): comments
    removed, fenced code blanked, line numbers kept. A comment never closed hides the rest."""
    shown, fenced, opened = [], False, False
    for line in lines:
        if opened:
            end = line.find("-->")
            text, opened = ("", True) if end < 0 else inline_comments(line[end + 3 :])
            shown.append(text)
            continue
        found = HEADING_START.match(line)
        fenced = fenced and not (found and len(found[1]) == 2)
        toggled = FENCE_LINE.match(line) is not None
        fenced ^= toggled
        if fenced or toggled:
            shown.append("")
            continue
        text, opened = inline_comments(line)
        shown.append(text)
    return shown


def period_key(header: str) -> PeriodKey | None:
    quarter = QUARTER_HEADER.fullmatch(header)
    if quarter:
        try:
            for part in quarter.groups():
                datetime.date.fromisoformat(part)
        except ValueError:
            return None
        return ("q",) + quarter.groups()
    return ("fy", header) if FISCAL_HEADER.fullmatch(header) else None


def holds_carrying_value(row: list[str]) -> bool:
    return len(row) > 1 and len(row[1]) <= 4000 and CARRYING.search(row[1]) is not None


def markdown_table(lines: list[str], file: str) -> Table:
    """One run of '|' lines: header, optional separator, rows. Rows are found by their label."""
    header = table_cells(lines[0])
    separated = len(lines) > 1 and all(SEPARATOR_CELL.fullmatch(c) for c in table_cells(lines[1]))
    if len(lines) - 1 - separated > TABLE_ROW_LIMIT:
        raise CashflowLimit(file, "table rows", len(lines) - 1 - separated, TABLE_ROW_LIMIT)
    body = [table_cells(line) for line in lines[1 + separated :]]
    label_header = CASHFLOW_LABELS["label_header"]
    label_column = header.index(label_header) if label_header in header else 0
    rows: dict[str, list[str]] = {}
    repeated: str | None = None
    folded: set[str] = set()
    for row in body:
        if label_column < len(row):
            # Case-insensitive, as the debt classification is.
            # A later row of a label already seen is dropped by `rows`: that matters when it holds a
            # carrying value, not for a blank label or a note row.
            label = row[label_column]
            dropped = plain_label(label) in folded and label != ""
            if dropped and repeated is None and holds_carrying_value(row):
                repeated = label
            folded.add(plain_label(label))
            rows.setdefault(row[label_column], row)
    periods: dict[PeriodKey, int] = {}
    for index, name in enumerate(header):
        key = period_key(name)
        if key is not None:
            periods.setdefault(key, index)
    return {
        "header": header,
        "rows": rows,
        "periods": periods,
        "repeated": repeated,
        "interrupted": None,
    }


def markdown_tables(text: str, file: str) -> list[Table]:
    """The tables of a Markdown text as a viewer shows it; `file` names it in a limit error. A table
    is its header and raw rows; `interrupted` when hiding changed one or '|' text outside code
    follows before the next `#` heading without its own separator row (delivery's rule). Rows after
    a split table are never merged: they read under its header, with no period and its problem."""
    tables: list[Table] = []
    raw = physical_lines(text)
    shown = shown_lines(raw)
    at, head, problem = 0, "", None  # the header and problem of a split table
    while at < len(raw):
        if table_row(shown[at]) is None:
            at += 1
            continue
        end = at + 1
        while end < len(raw) and table_row(raw[end]) is not None:
            end += 1
        rows = [row for row in map(table_row, shown[at:end]) if row is not None]
        follows = problem is not None and not SEPARATOR.fullmatch("".join(shown[at + 1 : at + 2]))
        table = markdown_table([head, *rows] if follows else rows, file)
        stop = next((i for i in range(end, len(raw)) if HEADING_START.match(shown[i])), len(raw))
        more = next((i for i in range(end, stop) if "|" in CODE_SPAN.sub("", shown[i])), stop)
        split = more < stop and not SEPARATOR.fullmatch("".join(shown[more + 1 : more + 2]))
        if any(shown[i] != raw[i] for i in range(at, more + 1 if split else end)):
            table["interrupted"] = "interrupted by a comment"
        elif split:
            table["interrupted"] = "split by a blank line or a comment"
        if follows:
            table["periods"], table["interrupted"] = {}, problem
        head, problem = head if follows else rows[0], table["interrupted"] if split else None
        tables.append(table)
        at = end
    return tables


def table_holding(tables: list[Table], label: str) -> Table | None:
    return next((table for table in tables if label in table["rows"]), None)


def table_cell(
    table: Table | None, label: str, period: PeriodKey | None, kind: str = "money"
) -> Cell:
    row = None if table is None else table["rows"].get(label)
    index = None if table is None or period is None else table["periods"].get(period)
    if row is None or index is None or index >= len(row):
        return absent_cell()
    return source_cell(row[index], kind)


def add_back_labels(table: Table | None) -> list[str]:
    """The rows between 'Interest expense-net' and the pre-tax income row of a bridge."""
    start = CASHFLOW_LABELS["interest_net"]
    if table is None or start not in table["rows"]:
        return []
    labels = list(table["rows"])
    labels = labels[labels.index(start) + 1 :]
    end = CASHFLOW_LABELS["pretax_income"]
    labels = labels[: labels.index(end)] if end in labels else labels
    return [label for label in labels if label]


def register_date(text: str) -> datetime.date | None:
    found = REGISTER_DATE.search(text)
    if found is None or found.group(1) not in MONTHS_SHORT:
        return None
    try:
        return datetime.date(int(found.group(3)), MONTHS_SHORT[found.group(1)], int(found.group(2)))
    except ValueError:
        return None


def secured_debt(tables: list[Table]) -> SecuredDebt | None:
    """(register date, secured carrying total, problem) of the annual debt register, or None.

    Labels match case-insensitively. Secured: the securitization, the term loans aggregate, and
    secured notes. Unsecured: subordinated or unsecured notes. Total rows are subtotals. Any other
    row with a `carrying <n>` value cannot be classified: the total is then None and the problem
    names the label. None when the register date or a secured carrying value is missing.
    """
    names = CASHFLOW_LABELS
    anchor = names["secured_term_loans"].casefold()
    debt = next(
        (t for t in tables if any(plain_label(label) == anchor for label in t["rows"])), None
    )
    if debt is None or len(debt["header"]) < 2:
        return None
    when = register_date(debt["header"][1])
    if when is None:
        return None
    required = {names["secured_securitization"].casefold(), names["secured_term_loans"].casefold()}
    secured_notes = re.compile(r"(?<![a-z])" + re.escape(names["secured_notes"]))
    total, incomplete, unclassified = decimal.Decimal(0), False, None
    named: set[str] = set()
    for label, row in debt["rows"].items():
        low = plain_label(label)
        kind = total_kind(low)
        if kind == "edge":
            continue
        unsecured = names["unsecured_notes"] in low or names["unsecured"] in low
        secured = kind is None and (
            low in required or (secured_notes.search(low) and not unsecured)
        )
        carrying = CARRYING.search(row[1]) if len(row) > 1 and len(row[1]) <= 4000 else None
        if not secured:
            if carrying is not None and not unsecured and unclassified is None:
                unclassified = label[:LABEL_LIMIT]
            continue
        if carrying is None:
            incomplete = True
            continue
        total += decimal.Decimal(carrying.group(1).replace(",", ""))
        named.add(low)
    if debt["interrupted"] is not None:
        return (
            when,
            None,
            f"the debt register ({debt['header'][1][:LABEL_LIMIT]}) is {debt['interrupted']}",
        )
    if debt["repeated"] is not None:
        return (
            when,
            None,
            f"the debt register repeats a row label: {debt['repeated'][:LABEL_LIMIT]}",
        )
    if unclassified is not None:
        return (
            when,
            None,
            f"the debt register has a row that cannot be classified: {unclassified}",
        )
    return (when, total, None) if required <= named and not incomplete else None


def fiscal_year_ends(tables: list[Table]) -> dict[str, str]:
    """FY label -> ISO end date from the annual period register (headed Period ... End)."""
    names = CASHFLOW_LABELS
    period_name, end_name = names["period_header"], names["period_end_header"]
    register = next(
        (t for t in tables if period_name in t["header"] and end_name in t["header"]), None
    )
    if register is None:
        return {}
    period, end = register["header"].index(period_name), register["header"].index(end_name)
    return {
        row[period]: row[end]
        for row in register["rows"].values()
        if len(row) > max(period, end) and FISCAL_HEADER.fullmatch(row[period])
    }


def derive(kind: str, operands: list[Cell], compute: Callable[..., decimal.Decimal]) -> Cell:
    """A value from other cells under prec=28; n.m. or a gap in an operand carries through."""
    if any(operand["status"] == "nm" for operand in operands):
        return not_modelled_cell()
    exacts = [operand["exact"] for operand in operands]
    values = [decimal.Decimal(exact) for exact in exacts if exact is not None]
    if len(values) != len(exacts):
        return unavailable_cell(COMPONENT_MISSING)
    try:
        with decimal.localcontext(decimal.Context(prec=28)):
            result = compute(*values)
    except (decimal.DivisionByZero, decimal.InvalidOperation):
        return unavailable_cell("a divisor is zero")
    try:
        return amount_cell("0" if result == 0 else str(result), kind)
    except (ArithmeticError, ValueError):
        return unavailable_cell("the value cannot be displayed")


def forecast_inputs(exact: Any) -> tuple[Forecast, list[str], list[str]]:
    """(source years by case, scope limits, the cases' keys in step) of the forecast record;
    validated here."""
    cases: Forecast = []
    keys: list[str] = []
    for key, name in FORECAST_CASES:
        if key not in exact["outputs"]:
            continue
        years = exact["outputs"][key]["years"]
        if len(years) > FORECAST_YEAR_LIMIT:
            raise CashflowLimit(
                CASHFLOW_FILES[0], f"forecast years in {key}", len(years), FORECAST_YEAR_LIMIT
            )
        for year in years:
            if not isinstance(year["year"], int):
                raise TypeError("year is not a number")
            checked_entries(year, ("year", "planning_start", "planning_end"))
        cases.append((name, years))
        keys.append(key)
    limits = exact["scope_limits"]
    if not isinstance(limits, list) or not all(isinstance(item, str) for item in limits):
        raise TypeError("scope_limits is not a list of text")
    return cases, limits, keys


DOWNSIDE_CASE = "Downside case"
DOWNSIDE_NOTES = {
    "DOWNSIDE": "Downside case is the stress case: a shock applied to the base-case drivers.",
    "DOWNSIDE_DRIVERS": (
        "Downside case is CP-2G's own downside drivers; no CP-2A shock was supplied."
    ),
    None: "Downside case: no downside case was computed in this run.",
}
NO_DOWNSIDE = "no downside case was computed in this run"


def main_cases(cases: Forecast, keys: list[str]) -> tuple[Forecast, Forecast, str]:
    """(main, other, note): the main grid's Base case and one Downside case, the other cases.

    A case with no years is not computed: it is never the Downside and opens no group.
    The Downside case is the CP-2A shock (DOWNSIDE) when computed, else CP-2G's own downside
    drivers; it is shown as "Downside case". `keys` are the cases' keys in step with `cases`.
    """
    named = {key: case for key, case in zip(keys, cases, strict=True) if case[1]}  # computed only
    chosen = next((key for key in ("DOWNSIDE", "DOWNSIDE_DRIVERS") if key in named), None)
    main: Forecast = [named["REFERENCE"]] if "REFERENCE" in named else []
    if chosen is not None:
        main.append((DOWNSIDE_CASE, named[chosen][1]))
    other = [case for key, case in named.items() if key not in ("REFERENCE", chosen)]
    return main, other, DOWNSIDE_NOTES[chosen]


def cell_count(rows: int, columns: int) -> int:
    """The cells of a grid of `rows` x `columns`: the one count the budget is charged by."""
    return rows * columns


def grid_cells(grid: dict[str, Any]) -> int:
    """The cells a model's Forecast grid holds, main and other cases together."""
    held = cell_count(len(grid["rows"]), len(grid["columns"]))
    if grid["other"] is not None:
        held += cell_count(len(grid["other"]["rows"]), len(grid["other"]["columns"]))
    return held


def fiscal_inputs(record: Any) -> Fiscal:
    """[(fiscal year label, its values)] in the record's annual_periods order; validated here."""
    labels = record["annual_periods"]
    if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
        raise TypeError("annual_periods is not a list of text")
    if len(labels) > FISCAL_YEAR_LIMIT:
        raise CashflowLimit(CASHFLOW_FILES[1], "fiscal years", len(labels), FISCAL_YEAR_LIMIT)
    years: Fiscal = []
    for label in labels:
        values = record["values"][label]
        checked_entries(values)
        years.append((label, values))
    return years


def quarter_inputs(record: Any) -> dict[str, dict[str, Any]]:
    """The record's derived quarter values by window text; absent is empty; validated here."""
    quarters = record.get("quarters", {})
    if not isinstance(quarters, dict):
        raise TypeError("quarters is not a mapping of windows")
    for held in quarters.values():
        if not isinstance(held, dict):
            raise TypeError("a quarter window is not a mapping")
        checked_entries(held)
    return quarters


def optional_text(value: Any, what: str) -> None:
    if not (value is None or (isinstance(value, str) and len(value) <= LABEL_LIMIT)):
        raise TypeError(f"{what} is not short text")


def history_column_input(column: Any) -> None:
    """One history column's own fields are the right types and bounds; validated here."""
    if not isinstance(column, dict) or column.keys() != HISTORY_KEYS:
        raise TypeError("a history column does not have the recorded fields")
    for name in ("id", "label"):
        if not isinstance(column[name], str) or not 0 < len(column[name]) <= LABEL_LIMIT:
            raise TypeError(f"the {name} of a history column is not short text")
    if column["kind"] not in HISTORY_GROUPS:
        raise ValueError("a history column has an unknown kind")
    for name in ("prior", "reason"):
        optional_text(column[name], f"the {name} of a history column")
    if column["reason"] == "":
        raise ValueError("the reason of a history column is empty")
    if column["reason"] is not None and column["reason"].isspace():
        raise ValueError("the reason of a history column is only whitespace")
    for name in ("start", "end"):
        if column[name] is not None and not (
            isinstance(column[name], str) and valid_date(column[name])
        ):
            raise ValueError(f"the {name} of a history column is not a date")
    if not isinstance(column["values"], dict):
        raise TypeError("the values of a history column are not a mapping")
    checked_entries(column["values"])


def history_limits(record: Any) -> list[str]:
    """The history record's scope limits ([] without a record); validated here."""
    if "history" not in record:
        return []
    limits = record["history"].get("limits") if isinstance(record["history"], dict) else None
    if not isinstance(limits, list) or not all(isinstance(item, str) for item in limits):
        raise TypeError("history limits is not a list of text")
    if len(limits) > HISTORY_LIMIT_COUNT or any(len(i) > HISTORY_LIMIT_CHARS for i in limits):
        raise ValueError("history limits are more or longer than the record allows")
    return limits


def history_inputs(record: Any) -> list[dict[str, Any]] | None:
    """The validated history columns of calculation.json, or None when it has no `history`.

    The record is written by another process: its version, column count, ids, kinds, priors, dates
    and values are checked before any is used; a record that fails is malformed as a whole.
    """
    if "history" not in record:
        return None
    history = record["history"]
    if not isinstance(history, dict) or history.get("schema_version") != HISTORY_SCHEMA:
        raise ValueError("the history record has an unknown version")
    columns = history["columns"]
    if not isinstance(columns, list):
        raise TypeError("history columns is not a list")
    capped(columns, "history columns", HISTORY_COLUMN_LIMIT, CASHFLOW_FILES[1])
    for column in columns:
        history_column_input(column)
    ids = [column["id"] for column in columns]
    if len(set(ids)) != len(ids):
        raise ValueError("history column ids repeat")
    check_history_priors(columns)
    return columns


def check_history_priors(columns: list[dict[str, Any]]) -> None:
    """Ids and kinds agree on fiscal years; a prior is a column of the kind the history pairs."""
    kinds = {column["id"]: column["kind"] for column in columns}
    for column in columns:
        name, kind, prior = column["id"], column["kind"], column["prior"]
        is_year_id = re.fullmatch(r"FY\d+", name, re.ASCII) is not None
        placeholder = kind == "FY" and name == FY_PLACEHOLDER and prior is None
        if is_year_id != (kind == "FY") and not placeholder:
            raise ValueError("a history column's id and kind disagree on a fiscal year")
        if kind == "FY" and not placeholder and FISCAL_HEADER.fullmatch(name) is None:
            raise ValueError("a fiscal-year history column's id is not FY and a year")
        if prior is not None and (
            prior == name or prior not in kinds or HISTORY_PRIOR_KINDS.get(kind) != kinds.get(prior)
        ):
            raise ValueError("a history column's prior is not a column of the kind that follows")
        year_prior = kind == "FY" and prior is not None and prior != FY_PLACEHOLDER
        if year_prior and prior != f"FY{int(name[2:]) - 1}":
            raise ValueError("a fiscal year's prior is not the year before it")


def history_columns(history: list[dict[str, Any]]) -> list[Column]:
    """One column per history entry, in the record's order; its prior is that entry's index."""
    index = {column["id"]: at for at, column in enumerate(history)}
    columns: list[Column] = []
    for entry in history:
        column = Column(
            label=entry["label"],
            group=HISTORY_GROUPS[entry["kind"]],
            kind="h",
            record=entry["values"],
            start=entry["start"],
            end=entry["end"],
            period=None,
            prior=None if entry["prior"] is None else index[entry["prior"]],
            ytd=False,
        )
        if entry["reason"] is not None:
            column["unavailable"] = entry["reason"]
        if column["prior"] is not None and lengths_differ(entry, history[column["prior"]]):
            column["length_differs"] = True
        columns.append(column)
    return columns


def lengths_differ(entry: dict[str, Any], prior: dict[str, Any]) -> bool:
    """Both periods are dated and their lengths differ by more than the quarter slack."""
    if None in (entry["start"], entry["end"], prior["start"], prior["end"]):
        return False
    gap = span_days(entry["start"], entry["end"]) - span_days(prior["start"], prior["end"])
    return abs(gap) > QUARTER_LENGTH_SLACK


def span_days(start: str, end: str) -> int:
    return (datetime.date.fromisoformat(end) - datetime.date.fromisoformat(start)).days


def quarter_numbers(quarters: list[Span], ends: dict[str, str] | None) -> list[int | None]:
    """Per quarter, the fiscal year it opens (as Q1) or None.

    A quarter opens fiscal year N+1 when it spans at most QUARTER_DAYS days and starts the day
    after the end the period register records for FY N. Anything else is neither Q1 nor year to
    date.
    """
    openings: dict[datetime.date, int] = {}
    for label, end in (ends or {}).items():
        try:
            day = datetime.date.fromisoformat(end) + datetime.timedelta(days=1)
            openings.setdefault(day, int(label.removeprefix("FY")) + 1)
        except (ValueError, OverflowError):
            continue  # a register row with an unreadable end opens no fiscal year
    numbers: list[int | None] = []
    longest: dict[int, tuple[int, int]] = {}
    for index, (start, end) in enumerate(quarters):
        days = span_days(start, end)
        number = (
            openings.get(datetime.date.fromisoformat(start)) if 0 <= days <= QUARTER_DAYS else None
        )
        numbers.append(number)
        if number is not None and days > longest.get(number, (-1, 0))[0]:
            longest[number] = (days, index)
    # One Q1 per fiscal year: the longest span; the other candidates are plain date ranges.
    return [
        number if number is not None and longest[number][1] == index else None
        for index, number in enumerate(numbers)
    ]


def quarter_columns(quarters: list[Span], ends: dict[str, str] | None) -> list[Column]:
    """One column per quarter; a Q1 (year to date) has the previous year's Q1 as prior."""
    numbers = quarter_numbers(quarters, ends)
    first_quarter: dict[int, int] = {}
    for index, number in enumerate(numbers):
        if number is not None:
            first_quarter.setdefault(number, index)
    columns: list[Column] = []
    for (start, end), number in zip(quarters, numbers, strict=True):
        prior = None if number is None else first_quarter.get(number - 1)
        column = Column(
            label=f"{start}–{end}" if number is None else f"Q1 FY{number} (YTD)",
            group="Quarter",
            kind="q",
            record=None,
            start=start,
            end=end,
            period=("q", start, end),
            prior=prior,
            ytd=number is not None,
        )
        if prior is not None and abs(span_days(start, end) - span_days(*quarters[prior])) > (
            QUARTER_LENGTH_SLACK
        ):
            column["length_differs"] = True
        columns.append(column)
    return columns


def fiscal_columns(columns: list[Column], fiscal: Fiscal) -> dict[str, int]:
    """Append one column per fiscal year; returns each label's column index."""
    fiscal_index: dict[str, int] = {}
    for label, values in fiscal:
        found = FISCAL_HEADER.fullmatch(label)
        columns.append(
            Column(
                label=label,
                group="Fiscal year",
                kind="fy",
                record=values,
                start=None,
                end=None,
                period=("fy", label),
                prior=fiscal_index.get(f"FY{int(label[2:]) - 1}") if found else None,
                ytd=False,
            )
        )
        fiscal_index.setdefault(label, len(columns) - 1)
    return fiscal_index


def twelve_months(column: Column) -> bool:
    """A column CP-1 does not date, or dates as a 52- or 53-week year, is a full year."""
    if column["start"] is None or column["end"] is None:
        return True
    return span_days(column["start"], column["end"]) + 1 in YEAR_DAYS


def first_year_prior(fiscal_index: dict[str, int], year: int, on_base: bool) -> int | None:
    """The fiscal-year column a case's first year grows on, in `fiscal_index`.

    With the period history (`on_base`) that is the column of the first year's own number, the
    forecast's base year, when the history has one; otherwise the year before it.
    """
    prior = fiscal_index.get(f"FY{year}") if on_base else None
    return fiscal_index.get(f"FY{year - 1}") if prior is None else prior


def forecast_columns(
    columns: list[Column], cases: Forecast, fiscal_index: dict[str, int], on_base: bool = False
) -> None:
    """Append one column per forecast year of each case.

    The prior of a year is the same case's year before it; of a case's first year, a fiscal year
    of `fiscal_index` (see first_year_prior); a prior that is not that year is None.
    """
    for name, years in cases:
        case_index: dict[int, int] = {}
        for year in years:
            prior = case_index.get(year["year"] - 1)
            first = prior is None and not case_index
            if first:
                prior = first_year_prior(fiscal_index, year["year"], on_base)
            columns.append(
                Column(
                    label=f"FY{year['year']}E",
                    group=name,
                    kind="fc",
                    record=year,
                    start=text_or_none(year.get("planning_start")),
                    end=text_or_none(year.get("planning_end")),
                    period=None,
                    prior=prior,
                    ytd=False,
                )
            )
            if first and on_base and prior is not None and not twelve_months(columns[prior]):
                columns[-1]["prior_not_year"] = True
            case_index.setdefault(year["year"], len(columns) - 1)


class CashflowInputs(NamedTuple):
    """What every cell of one model's grid reads: tables, the debt register, fiscal-year ends."""

    tables: dict[str, Table | None]
    secured: SecuredDebt | None
    ends: dict[str, str]
    quarters: dict[str, dict[str, Any]]


class CellContext(NamedTuple):
    """The one argument of a cell operation: inputs, the cell's column, position and row kind."""

    inputs: CashflowInputs
    column: Column
    at: int
    grid: dict[RowKey, list[Cell]]
    kind: str


def add_cells(cells: list[Cell], kind: str = "money") -> Cell:
    return derive(kind, cells, lambda a, b: a + b)


def op_table(c: CellContext, name: str, label: str) -> Cell:
    return table_cell(c.inputs.tables[name], label, c.column["period"], c.kind)


def op_table_sum(c: CellContext, name: str, first: str, second: str) -> Cell:
    table = c.inputs.tables[name]
    cells = [table_cell(table, label, c.column["period"], c.kind) for label in (first, second)]
    return add_cells(cells, c.kind)


def op_key(c: CellContext, key: str, negate: bool = False) -> Cell:
    record = c.column["record"]
    if record is None:
        raise ValueError(f"the {c.column['label']} column holds no record to read {key} from")
    return held_cell(record[key], c.kind, negate) if key in record else spec_cell(None, c)


def op_sum(c: CellContext, *rows: RowKey) -> Cell:
    return add_cells([c.grid[row][c.at] for row in rows], c.kind)


def op_growth(c: CellContext, source: RowKey) -> Cell:
    """YoY growth of an earlier row against the same row in the column's prior-year column."""
    current = c.grid[source][c.at]
    if current["status"] == "nm":
        return not_modelled_cell()
    if c.column["prior"] is None:
        return unavailable_cell(PRIOR_MISSING)
    if c.column.get("length_differs"):
        return unavailable_cell(LENGTH_DIFFERS)
    if c.column.get("prior_not_year"):
        return unavailable_cell(PRIOR_NOT_YEAR)
    prior = c.grid[source][c.column["prior"]]
    return derive("percent", [current, prior], lambda a, b: a / b - 1)


def op_margin(c: CellContext, source: RowKey) -> Cell:
    return derive("percent", [c.grid[source][c.at], c.grid["revenue"][c.at]], lambda a, b: a / b)


def op_prefer(c: CellContext, key: str, fallback: Spec) -> Cell:
    """The calculation record's own value for the key when it holds one, else the derivation."""
    record = c.column["record"]
    if record is not None and key in record:
        return held_cell(record[key], c.kind)
    return spec_cell(fallback, c)


def quarter_held(c: CellContext, key: str) -> dict[str, Any] | None:
    """The record's entry for the key in this quarter column's window (either dash), or None."""
    column = c.column
    if column["kind"] != "q" or column["start"] is None or column["end"] is None:
        return None
    for dash in ("\u2013", "-"):
        window = c.inputs.quarters.get(f"{column['start']}{dash}{column['end']}")
        if window is not None and key in window:
            held: dict[str, Any] = window[key]
            return held
    return None


def op_quarter(c: CellContext, key: str, fallback: Spec | None = None) -> Cell:
    """The record's quarter value for this column's window, else the fallback, else n.a."""
    held = quarter_held(c, key)
    if held is not None:
        return held_cell(held, c.kind)
    return spec_cell(fallback, c) if fallback is not None else absent_cell()


def op_needs_ltm(c: CellContext, debt_needed: str = DEBT_TOTAL_NEEDED) -> Cell:
    held = quarter_held(c, "ltm_adj_ebitda")
    return unavailable_cell(LTM_NEEDED if held is None or held["amount"] is None else debt_needed)


def op_senior(c: CellContext) -> Cell:
    """Secured carrying values over Adj EBITDA, for the fiscal year ending on the register date."""
    if c.inputs.secured is None:
        return unavailable_cell(COMPONENT_MISSING)
    when, total, problem = c.inputs.secured
    if c.inputs.ends.get(c.column["label"]) != when.isoformat():
        return unavailable_cell(
            f"secured-debt carrying values are recorded only at {display_date(when.isoformat())}"
        )
    if problem is not None or total is None:
        return unavailable_cell(problem)
    return derive("multiple", [c.grid["adj"][c.at]], lambda a: total / a)


CELL_OPS: dict[str, Callable[..., Cell]] = {
    "table": op_table,
    "table-sum": op_table_sum,
    "key": op_key,
    "sum": op_sum,
    "growth": op_growth,
    "margin": op_margin,
    "ltm": op_needs_ltm,
    "quarter": op_quarter,
    "senior": op_senior,
    "prefer": op_prefer,
}


def spec_cell(spec: Spec | None, cell: CellContext) -> Cell:
    """One cell from its row's spec for the column's kind (None: n.a., or n.m. in forecast).

    A history column with a reason gives every row n.a. with that reason, derived rows included.
    """
    column = cell.column
    if column["kind"] == "h" and "unavailable" in column:
        return unavailable_cell(column["unavailable"])
    if spec is None:
        if column["kind"] == "h":
            return unavailable_cell(NO_LINE)
        return not_modelled_cell() if column["kind"] == "fc" else absent_cell()
    return CELL_OPS[spec[0]](cell, *spec[1:])


def every(spec: Spec) -> tuple[Spec, Spec, Spec]:
    return (spec, spec, spec)


# Rows the grid shows as totals (the ones a reader adds up to): by row key.
TOTAL_ROWS = frozenset(
    (
        "revenue",
        "gp",
        "ebit",
        "ebitda",
        "adj",
        "cfo",
        "fcf",
        "closing-cash",
        "liquidity",
        "closing-debt",
        "net-debt",
    )
)


class RowSpec(NamedTuple):
    """A grid row as data; a None spec shows n.a. (history) or n.m. (forecast)."""

    key: RowKey
    band: str
    label: str
    kind: str
    quarter: Spec | None
    fiscal: Spec | None
    forecast: Spec | None


# Rows as data: (id, band, label, kind, quarter spec, fiscal-year spec, forecast spec).
INCOME = "Profitability"
HEAD_ROWS = (
    RowSpec(
        "revenue",
        "Revenue",
        "Revenue",
        "money",
        ("table", "income", CASHFLOW_LABELS["revenue"]),
        ("key", "revenue"),
        ("key", "revenue"),
    ),
    RowSpec(
        "revenue-growth",
        "Revenue",
        "Revenue YoY growth",
        "percent",
        ("growth", "revenue"),
        ("prefer", "revenue_growth", ("growth", "revenue")),
        ("growth", "revenue"),
    ),
    RowSpec(
        "cogs",
        INCOME,
        "COGS (cost of sales)",
        "money",
        ("table", "income", CASHFLOW_LABELS["cogs"]),
        ("key", "cogs"),
        None,
    ),
    RowSpec(
        "gp",
        INCOME,
        "Gross profit",
        "money",
        ("table", "income", CASHFLOW_LABELS["gross_profit"]),
        ("key", "gross_profit"),
        None,
    ),
    RowSpec(
        "gp-margin",
        INCOME,
        "Gross profit margin",
        "percent",
        ("margin", "gp"),
        ("prefer", "gross_margin", ("margin", "gp")),
        ("margin", "gp"),
    ),
    RowSpec(
        "opex",
        INCOME,
        "Opex (selling and administrative, amortization of intangibles)",
        "money",
        (
            "table-sum",
            "income",
            CASHFLOW_LABELS["selling_admin"],
            CASHFLOW_LABELS["amortization"],
        ),
        ("key", "opex_magnitude"),
        None,
    ),
    RowSpec(
        "ebit",
        INCOME,
        "EBIT (income from operations)",
        "money",
        ("table", "income", CASHFLOW_LABELS["operating_income"]),
        ("key", "ebit_reported"),
        None,
    ),
    RowSpec(
        "da",
        INCOME,
        "D&A (depreciation and amortization)",
        "money",
        ("table", "bridge", CASHFLOW_LABELS["da"]),
        ("key", "cash_flow_DA"),
        None,
    ),
    RowSpec(
        "ebitda",
        INCOME,
        "EBITDA (EBIT + D&A)",
        "money",
        ("sum", "ebit", "da"),
        ("key", "operating_ebitda"),
        None,
    ),
    RowSpec(
        "issuer",
        INCOME,
        "Issuer EBITDA (reported)",
        "money",
        ("table", "bridge", CASHFLOW_LABELS["issuer_ebitda"]),
        ("key", "issuer_ordinary_ebitda"),
        None,
    ),
)
ADJUSTED = "Adjusted EBITDA"
PROXY = "Earnings to cash proxy"
CASH = "Cash and liquidity"
DEBT = "Debt"
CREDIT = "Credit metrics"
TAIL_ROWS = (
    RowSpec(
        "adj",
        ADJUSTED,
        "Adj EBITDA (EBITDA As Defined)",
        "money",
        ("table", "qdef", CASHFLOW_LABELS["adjusted_ebitda"]),
        ("key", "issuer_as_defined"),
        ("key", "ebitda"),
    ),
    RowSpec(
        "adj-margin",
        ADJUSTED,
        "Adj EBITDA margin",
        "percent",
        ("margin", "adj"),
        ("prefer", "adj_ebitda_margin", ("margin", "adj")),
        ("margin", "adj"),
    ),
    RowSpec(
        "adj-growth",
        ADJUSTED,
        "Adj EBITDA YoY growth",
        "percent",
        ("growth", "adj"),
        ("prefer", "adj_ebitda_growth", ("growth", "adj")),
        ("growth", "adj"),
    ),
    RowSpec(
        "ltm-adj",
        ADJUSTED,
        "LTM Adj EBITDA (As Defined)",
        "money",
        ("quarter", "ltm_adj_ebitda"),
        ("key", "issuer_as_defined"),
        None,
    ),
    RowSpec(
        "interest",
        PROXY,
        "Cash interest",
        "money",
        None,
        ("key", "interest_cash"),
        ("key", "interest"),
    ),
    RowSpec("tax", PROXY, "Cash taxes", "money", None, ("key", "tax_cash"), None),
    RowSpec(
        "tax-wc",
        PROXY,
        "Cash taxes and working capital, combined",
        "money",
        None,
        None,
        ("key", "tax_wc"),
    ),
    RowSpec("cfo", PROXY, "Model cash from operations", "money", None, None, ("key", "cfo")),
    RowSpec(
        "capex",
        PROXY,
        "Capital expenditure (outflow)",
        "money",
        None,
        ("key", "capex_signed", True),
        ("key", "capex"),
    ),
    RowSpec(
        "fcf", PROXY, "Cash proxy (not issuer free cash flow)", "money", None, None, ("key", "fcf")
    ),
    RowSpec("dividends", CASH, "Distributions", "money", None, None, ("key", "dividends")),
    RowSpec("repayment", CASH, "Debt repayment", "money", None, None, ("key", "repayment")),
    RowSpec("opening-cash", CASH, "Opening cash", "money", None, None, ("key", "opening_cash")),
    RowSpec(
        "closing-cash",
        CASH,
        "Closing cash",
        "money",
        None,
        ("key", "cash"),
        ("key", "closing_cash"),
    ),
    RowSpec("undrawn", CASH, "Undrawn facility", "money", None, None, ("key", "undrawn")),
    RowSpec("liquidity", CASH, "Accessible liquidity", "money", None, None, ("key", "liquidity")),
    RowSpec("opening-debt", DEBT, "Opening debt", "money", None, None, ("key", "opening_debt")),
    RowSpec(
        "closing-debt",
        DEBT,
        "Closing debt (carrying value)",
        "money",
        None,
        ("key", "carrying_debt"),
        ("key", "closing_debt"),
    ),
    RowSpec(
        "net-debt",
        DEBT,
        "Net debt (all modelled cash deducted)",
        "money",
        None,
        ("key", "net_carrying_debt"),
        ("key", "net_debt"),
    ),
    RowSpec(
        "senior",
        CREDIT,
        "Senior secured leverage (secured debt / Adj EBITDA)",
        "multiple",
        ("quarter", "senior_secured_multiple", ("ltm", DEBT_SENIOR_NEEDED)),
        ("prefer", "senior_secured_multiple", ("senior",)),
        None,
    ),
    RowSpec(
        "total-leverage",
        CREDIT,
        "Total leverage (debt / Adj EBITDA)",
        "multiple",
        ("ltm",),
        ("key", "gross_carrying_multiple"),
        ("key", "total_leverage"),
    ),
    RowSpec(
        "net-leverage",
        CREDIT,
        "Net leverage (net debt / Adj EBITDA)",
        "multiple",
        ("ltm",),
        ("key", "net_carrying_multiple"),
        ("key", "net_leverage"),
    ),
    RowSpec(
        "coverage",
        CREDIT,
        "Interest coverage (Adj EBITDA / cash interest)",
        "multiple",
        None,
        ("key", "issuer_earnings_cash_interest"),
        ("key", "coverage"),
    ),
    RowSpec(
        "cash-to-debt",
        CREDIT,
        "Cash proxy / closing debt",
        "percent",
        None,
        None,
        ("key", "fcf_to_debt"),
    ),
)


# A free-text label copied from a handoff into the grid is cut to this many characters.
LABEL_LIMIT = 200


def capped(found: Any, what: str, limit: int, file: str) -> None:
    if len(found) > limit:
        raise CashflowLimit(file, what, len(found), limit)


def listed_labels(tables: dict[str, Table | None]) -> list[str]:
    """Business units (rows `Total <unit>`) of the annual, then the quarter, segment table."""
    units: dict[str, None] = {}
    prefix = CASHFLOW_LABELS["total_prefix"] + " "
    for name, file in (("aseg", CASHFLOW_FILES[2]), ("qseg", CASHFLOW_FILES[3])):
        table = tables[name]
        for label in () if table is None else table["rows"]:
            if label.startswith(prefix) and label.removeprefix(prefix):
                units.setdefault(label.removeprefix(prefix))
        capped(units, "business-unit rows", UNIT_ROW_LIMIT, file)
    return list(units)


def listed_add_backs(tables: dict[str, Table | None]) -> list[str]:
    """The annual add-back labels in order, then any quarter-only label."""
    labels = dict.fromkeys(add_back_labels(tables["adef"]))
    capped(labels, "add-back rows", ADD_BACK_ROW_LIMIT, CASHFLOW_FILES[2])
    labels.update(dict.fromkeys(add_back_labels(tables["qdef"])))
    capped(labels, "add-back rows", ADD_BACK_ROW_LIMIT, CASHFLOW_FILES[3])
    return list(labels)


def cashflow_rows(tables: dict[str, Table | None]) -> list[RowSpec]:
    """The grid's rows in presentation order: units, the fixed head, add-backs, the fixed tail."""
    rows: list[RowSpec] = []
    for unit in listed_labels(tables):
        total = f"{CASHFLOW_LABELS['total_prefix']} {unit}"
        rows.append(
            RowSpec(
                ("unit", unit),
                "Revenue",
                unit[:LABEL_LIMIT],
                "money",
                ("table", "qseg", total),
                ("table", "aseg", total),
                None,
            )
        )
        rows.append(
            RowSpec(
                ("growth", unit),
                "Revenue",
                f"{unit[:LABEL_LIMIT]} YoY growth",
                "percent",
                *every(("growth", ("unit", unit))),
            )
        )
    rows.extend(HEAD_ROWS)
    for label in listed_add_backs(tables):
        rows.append(
            RowSpec(
                ("add-back", label),
                "Add-backs to issuer EBITDA",
                label[:LABEL_LIMIT],
                "money",
                ("table", "qdef", label),
                ("table", "adef", label),
                None,
            )
        )
    return rows + list(TAIL_ROWS)


def cashflow_notes(year_to_date: bool, with_history: bool) -> list[str]:
    if with_history:  # CP-1's labelled periods replace the Q1 and pro forma notes
        rest = [
            note.replace(FISCAL_ONLY_RATIOS, TWELVE_MONTH_RATIOS) for note in CASHFLOW_NOTES[2:]
        ]
        return [LTM_NOTE, *rest]
    return [note for note in CASHFLOW_NOTES if year_to_date or note != Q1_NOTE]


def no_downside_column() -> Column:
    """The main grid's last column when no downside case was computed: n.a. in every row."""
    return Column(
        label="Downside",
        group=DOWNSIDE_CASE,
        kind="h",
        record=None,
        start=None,
        end=None,
        period=None,
        prior=None,
        ytd=False,
        unavailable=NO_DOWNSIDE,
    )


def row_part(rows: list[dict[str, Any]], part: slice) -> list[dict[str, Any]]:
    """The rows with only the cells of the columns in `part`."""
    return [{**row, "cells": row["cells"][part]} for row in rows]


def cashflow_of(
    forecast: tuple[Forecast, list[str], list[str]],
    recorded: Recorded,
    statements: tuple[list[Table], list[Table]],
    units: str | None,
    budget: int,
) -> dict[str, Any]:
    """History from the parsed annual and quarter tables and the forecast record, as a grid.

    `units` is the caption of the grid's amounts (see `units_caption`).

    `recorded` ends with the history (CP-1's period columns and their limits) or None; with it
    those columns replace the quarter and fiscal-year columns and read each row's forecast spec.

    Raises CashflowBudget, before computing any cell, when rows x columns passes `budget`.
    """
    cases, limits, keys = forecast
    main, other, downside_note = main_cases(cases, keys)
    fiscal, quarters, history = recorded
    annual, quarter = statements
    names = CASHFLOW_LABELS
    tables: dict[str, Table | None] = {
        "income": table_holding(quarter, names["cogs"]),
        "qseg": table_holding(quarter, names["segment_revenue"]),
        "aseg": table_holding(annual, names["segment_revenue"]),
        "bridge": table_holding(quarter, names["issuer_ebitda"]),
        "qdef": table_holding(quarter, names["adjusted_ebitda"]),
        "adef": table_holding(annual, names["adjusted_ebitda"]),
    }
    ends = fiscal_year_ends(annual)
    inputs = CashflowInputs(tables, secured_debt(annual), ends, quarters)
    income = tables["income"]
    periods = sorted({key[1:] for key in income["periods"] if key[0] == "q"}) if income else []
    capped(periods, "quarter columns", QUARTER_COLUMN_LIMIT, CASHFLOW_FILES[3])
    layout = [RowSpec._make(spec) for spec in cashflow_rows(tables)]  # a plain 7-tuple row works
    if history is None:
        columns = quarter_columns(periods, ends)
        fiscal_index = fiscal_columns(columns, fiscal)
    else:
        columns = history_columns(history[0])
        fiscal_index = {c["id"]: at for at, c in enumerate(history[0]) if c["kind"] == "FY"}
    on_base = history is not None
    forecast_columns(columns, main, fiscal_index, on_base)
    if not any(c["group"] == DOWNSIDE_CASE for c in columns):
        columns.append(no_downside_column())
    main_count = len(columns)
    forecast_columns(columns, other, fiscal_index, on_base)  # priors read the main grid's history
    if cell_count(len(layout), len(columns)) > budget:
        raise CashflowBudget(
            "the cash flow model is not shown; the workspace's cash flow models exceed "
            f"{CASHFLOW_CELL_BUDGET:,} cells"
        )
    grid: dict[RowKey, list[Cell]] = {}
    rows = []
    for spec in layout:
        pick = {"q": spec.quarter, "fy": spec.fiscal, "fc": spec.forecast, "h": spec.forecast}
        grid[spec.key] = [
            spec_cell(pick[column["kind"]], CellContext(inputs, column, index, grid, spec.kind))
            for index, column in enumerate(columns)
        ]
        rows.append(
            {
                "band": spec.band,
                "label": spec.label,
                "kind": spec.kind,
                "total": spec.key in TOTAL_ROWS,
                "cells": grid[spec.key],
            }
        )
    year_to_date = any(column["ytd"] for column in columns[:main_count])
    shown = [
        {
            "label": c["label"],
            "group": c["group"],
            "start": c["start"],
            "end": c["end"],
            "ytd": c["ytd"],
        }
        for c in columns
    ]
    return {
        "units": units,
        "columns": shown[:main_count],
        "rows": row_part(rows, slice(0, main_count)),
        "other": None
        if main_count == len(columns)
        else {"columns": shown[main_count:], "rows": row_part(rows, slice(main_count, None))},
        "notes": [*cashflow_notes(year_to_date, history is not None), downside_note],
        "limits": limits if history is None else [*limits, *history[1]],
    }


# Across every model of one page load; a model whose grid would pass it is listed without a grid.
CASHFLOW_CELL_BUDGET = 250_000

# Errors a malformed input file or layout can raise; each is reported, never ends the store.
CASHFLOW_ERRORS = (
    OSError,
    ValueError,
    KeyError,
    TypeError,
    AttributeError,
    IndexError,
    ArithmeticError,
    RecursionError,
    MemoryError,
)


def read_cashflow(
    files: dict[str, bytes], handoff: str | None, budget: int | None = None
) -> tuple[dict[str, Any] | None, tuple[str, str] | None]:
    """(grid, None), or (None, (kind, text)).

    Kind "file" (text: the input that cannot be read), "limit" (text: the limit message, or the
    budget message when the grid passes `budget`, which no cell was computed for) or "layout"
    (text: describe(error) of the failure while laying out). `budget` is the cells left to this
    grid; None means the whole CASHFLOW_CELL_BUDGET, read when called.

    Documented fail-open: an input the reader cannot read or lay out leaves the model listed with
    no grid and a Workspace issue naming the file or the cause. A model too large to parse
    (MemoryError) or nested too deep (RecursionError) is reported the same way, not allowed to end
    the store.
    """
    stage = CASHFLOW_FILES[0]
    try:
        exact = json.loads(files[stage].decode("utf-8"))
        forecast = forecast_inputs(exact)
        units = recorded_units(exact)
        stage = CASHFLOW_FILES[1]
        record = json.loads(files[stage].decode("utf-8"))
        fiscal = fiscal_inputs(record)
        quarter_values = quarter_inputs(record)
        columns = history_inputs(record)
        history = None if columns is None else (columns, history_limits(record))
        stage = CASHFLOW_FILES[2]
        annual = markdown_tables(files[stage].decode("utf-8"), stage)
        stage = CASHFLOW_FILES[3]
        quarter = markdown_tables(files[stage].decode("utf-8"), stage)
    except CashflowLimit as error:
        return None, ("limit", str(error))
    except CASHFLOW_ERRORS:
        return None, ("file", stage)
    try:
        left = CASHFLOW_CELL_BUDGET if budget is None else budget
        recorded = (fiscal, quarter_values, history)
        return cashflow_of(
            forecast, recorded, (annual, quarter), units_caption(units, handoff), left
        ), None
    except (CashflowLimit, CashflowBudget) as error:
        return None, ("limit", str(error))
    except CASHFLOW_ERRORS as error:
        return None, ("layout", describe(error))


class GridAsk(NamedTuple):
    """What a model's grid is built from besides its files: its handoff text and its cell budget
    (None: the whole CASHFLOW_CELL_BUDGET)."""

    handoff: str | None
    budget: int | None


def cashflow_or_issues(
    folder: str,
    files: dict[str, Any],
    inputs: dict[str, bytes | None],
    ask: GridAsk,
    issues: list[str],
) -> dict[str, Any] | None:
    """The model's cash flow grid, or None with one issue for each of the four unusable files."""
    present: dict[str, bytes] = {}
    for name in CASHFLOW_FILES:
        data = inputs[name]
        if data is not None:
            present[name] = data
            continue
        what = "does not match its delivery record" if name in files else "is missing or unreadable"
        issues.append(f"{folder}: {name} {what}")
    if len(present) != len(CASHFLOW_FILES):
        return None
    cashflow, problem = read_cashflow(present, ask.handoff, ask.budget)
    if problem is not None:
        kind, text = problem
        issues.append(
            {
                "file": f"{folder}: {text} is missing or unreadable",
                "limit": f"{folder}: {text}",
                "layout": f"{folder}: the cash flow model could not be laid out ({text})",
            }[kind]
        )
    return cashflow


MANIFEST_ERRORS = (
    OSError,
    ValueError,
    KeyError,
    TypeError,
    AttributeError,
    RecursionError,
    MemoryError,
)


def model_manifests(root: Path, folders: Iterable[str]) -> Manifests:
    """Each folder's (delivery.json, listed view.json), read once, or describe(error) when it
    cannot be read. Documented fail-open: a folder that cannot be read is reported by its readers
    (a Workspace issue or no identity), never ends the store."""
    found: Manifests = {}
    for folder in folders:
        if folder in found:
            continue
        try:
            delivery = delivery_json(root / folder)
            found[folder] = (delivery, listed_view(root / folder, delivery))
        except MANIFEST_ERRORS as error:
            found[folder] = describe(error)
    return found


def available_folders(catalogue: dict[str, Any]) -> list[str]:
    """Every available artifact folder of the catalogue, once, in catalogue order."""
    return list(
        dict.fromkeys(
            artifact["folder"]
            for run in catalogue["real"]
            for artifact in run.get("artifacts") or []
            if artifact.get("available")
        )
    )


def shown_models(
    root: Path, catalogue: dict[str, Any], manifests: Manifests | None = None
) -> tuple[set[str], list[str]]:
    """The one available model folder shown per name (the route id), and the issues for the others.

    A folder is listed once however many runs list it. When folders share a name, the run's own
    delivery (runs/<run_id>/deliveries/<name>, its view.json recording that run) is kept, else the
    first by path; each dropped folder is named in an issue that says which one is shown. Only the
    kept folder is read in full. `manifests` are the folders' model_manifests, read when omitted.
    """
    manifests = (
        model_manifests(root, available_folders(catalogue)) if manifests is None else manifests
    )
    by_name: dict[str, list[str]] = {}
    for run in catalogue["real"]:
        for artifact in run.get("artifacts") or []:
            folder = artifact["folder"]
            if artifact.get("available") and artifact.get("kind") == "model":
                names = by_name.setdefault(Path(folder).name, [])
                if folder not in names:
                    names.append(folder)

    def own(folder: str) -> bool:
        parts = PurePosixPath(folder).parts
        if len(parts) != 4 or parts[0] != "runs" or parts[2] != "deliveries":
            return False
        # Documented fail-open: an unreadable view.json means "not known to be the run's own"; the
        # model read in catalogue_models reports the same failure as a Workspace issue.
        manifest = manifests.get(folder)
        if not isinstance(manifest, tuple):
            return False
        try:
            recorded = manifest[1]["run"]["run_id"]
        except MANIFEST_ERRORS:
            return False
        return bool(recorded == parts[1])

    shown: set[str] = set()
    issues: list[str] = []
    for name, folders in by_name.items():
        kept = next((f for f in folders if own(f)), None) or min(folders)
        shown.add(kept)
        issues.extend(
            f"{f}: another published model has the same name {name}; {kept} is shown"
            for f in sorted(folders)
            if f != kept
        )
    return shown, issues


def run_folder_of(folder: str) -> str | None:
    """x of a runs/<x>/deliveries/<id> folder, else None."""
    parts = PurePosixPath(folder).parts
    return parts[1] if len(parts) == 4 and parts[0] == "runs" and parts[2] == "deliveries" else None


SourcesOf = Callable[[str, dict[str, Any]], tuple[list[dict[str, Any]], list[str]]]


class ModelReads(NamedTuple):
    """What reading a model needs beyond its folder: the root, the issuer keys and the once-per-
    load sources of a model (see catalogue_models)."""

    root: Path
    keys: dict[str, str]
    sources_of: SourcesOf


def read_model(
    reads: ModelReads,
    artifact: dict[str, Any],
    manifest: tuple[dict[str, Any], dict[str, Any]] | str,
    issues: list[str],
    budget: int | None = None,
) -> dict[str, Any] | None:
    """One published model with its grid, or None with an issue when its record cannot be read.

    `manifest` is the model_manifests entry; `reads.sources_of(folder, delivery)` gives the
    model's (source rows, their issues); `budget` is the grid cells left (see read_cashflow).
    """
    root, keys, sources_of = reads
    folder = artifact["folder"]
    if isinstance(manifest, str):
        issues.append(f"{folder}: could not be read ({manifest})")
        return None
    delivery, view = manifest
    # Documented fail-open: reported in Settings; the other models stay readable. A model too
    # large to parse (MemoryError) is reported the same way, never ends the store.
    try:
        identity = view["run"]
        run_id = identity["run_id"]
        issuer_key = report_issuer_key(keys, identity.get("issuer_id"))
        sources, source_issues = sources_of(folder, delivery)
        issues.extend(source_issues)
        register = handoff_text = None
        files = delivery["files"]
        if "forecast.md" in files:
            handoff = listed_bytes(root / folder, delivery, "forecast.md")
            if handoff is None:
                issues.append(f"{folder}: forecast.md does not match its delivery record")
            else:
                handoff_text = handoff.decode("utf-8")
                register = register_of(sections_of(handoff_text))
        inputs = {
            name: listed_bytes(root / folder, delivery, name) if name in files else None
            for name in CASHFLOW_FILES
        }
        previous = delivery.get("previous_directory")
    except MANIFEST_ERRORS as error:
        issues.append(f"{folder}: could not be read ({describe(error)})")
        return None
    cashflow = cashflow_or_issues(folder, files, inputs, GridAsk(handoff_text, budget), issues)
    mode, qualification = view.get("mode"), view.get("analytical_qualification")
    return {
        "id": Path(folder).name,
        "issuerKey": issuer_key,
        "mode": mode if isinstance(mode, str) else None,
        "qualification": qualification if isinstance(qualification, str) else None,
        "runId": run_id if isinstance(run_id, str) else None,
        "runFolder": run_folder_of(folder),
        "scope": text_or_none(delivery.get("scope")),
        "inputContract": text_or_none(delivery.get("input_contract")),
        "revisionNote": text_or_none(delivery.get("presentation_repair")),
        "previous": Path(previous).name if isinstance(previous, str) else None,
        "href": artifact["href"] + "&embedded=1",
        "download": artifact["href"] + "&download=1",
        "files": [
            {"name": n, "href": f"/files/{quote(f'{folder}/{n}')}?sha256={h}&download=1"}
            for n, h in sorted(files.items())
        ],
        "sources": sources,
        "register": register,
        "cashflow": cashflow,
    }


def run_shows(
    artifact: dict[str, Any],
    manifest: tuple[dict[str, Any], dict[str, Any]] | str,
    keys: dict[str, str],
    sources_of: SourcesOf,
    runs: dict[str, dict[str, Any]],
) -> bool:
    """Whether a run's Forecast lists this model: the same issuer key and the run named by the
    model's run_id or by one of its sources (the rule of views.js runModels)."""
    folder = artifact["folder"]
    # Documented fail-open: a record that cannot be read is not shown by a run; read_model reports
    # the same failure as a Workspace issue.
    if isinstance(manifest, str):
        return False
    delivery, view = manifest
    try:
        identity = view["run"]
        key = report_issuer_key(keys, identity.get("issuer_id"))
        if key is None:
            return False
        held = {route for route, run in runs.items() if run["issuerKey"] == key}
        own = (identity["run_id"], run_folder_of(folder))
        if any(runs[route]["folder"] in own for route in held):
            return True
        return any(row["run"] in held for row in sources_of(folder, delivery)[0])
    except MANIFEST_ERRORS:
        return False


class WorkspaceReads(NamedTuple):
    """What the store has read before the models: outputs, issuer keys, runs, model manifests."""

    outputs: dict[str, Any]
    keys: dict[str, str]
    runs: dict[str, dict[str, Any]]
    manifests: Manifests


def catalogue_models(
    root: Path,
    catalogue: dict[str, Any],
    prior: WorkspaceReads,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Published models the server verified, each once, with why and from what they were built.

    The models share one budget of CASHFLOW_CELL_BUDGET grid cells. Models some run shows
    (runs: the store's runs) are laid out first, then the rest, each in delivery path
    order; a model whose grid would pass the budget is listed without one, with an issue and
    without computing any of its cells. Each folder's manifest (`prior.manifests`) and each
    model's sources are read once.
    """
    outputs, keys, runs, manifests = prior
    shown, issues = shown_models(root, catalogue, manifests)
    held: dict[str, tuple[list[dict[str, Any]], list[str]] | Exception] = {}

    def sources_of(folder: str, delivery: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
        if folder not in held:
            found: list[str] = []
            try:
                held[folder] = (model_sources(root, delivery, outputs, folder, found), found)
            except MANIFEST_ERRORS as error:
                held[folder] = error
        result = held[folder]
        if isinstance(result, Exception):
            raise result
        return result

    listed: list[dict[str, Any]] = []
    done: set[str] = set()
    for run in catalogue["real"]:
        for artifact in run.get("artifacts") or []:
            folder = artifact["folder"]
            model = artifact.get("available") and artifact.get("kind") == "model"
            if model and folder in shown and folder not in done:
                done.add(folder)
                listed.append(artifact)
    built: dict[int, dict[str, Any]] = {}
    cells = 0
    reads = ModelReads(root, keys, sources_of)
    unshown = {
        i
        for i, artifact in enumerate(listed)
        if not run_shows(artifact, manifests[artifact["folder"]], keys, sources_of, runs)
    }
    for position in sorted(range(len(listed)), key=lambda i: (i in unshown, listed[i]["folder"])):
        artifact = listed[position]
        model = read_model(
            reads, artifact, manifests[artifact["folder"]], issues, CASHFLOW_CELL_BUDGET - cells
        )
        if model is None:
            continue
        grid = model["cashflow"]
        if grid is not None:
            cells += grid_cells(grid)
        built[position] = model
    return [built[position] for position in sorted(built)], issues


def visual_catalogue() -> list[dict[str, str]]:
    with (REPO / "docs/visualisations/catalogue.csv").open(encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def recorded_run(run_dir: Path, issues: list[str] | None = None) -> dict[str, str]:
    """The text fields of the launcher's own manifest; a run without a readable one records none.

    Documented fail-open: a manifest that cannot be read records nothing and, when `issues` is
    given, is named there by type and reason (never its bytes). A run with no manifest is normal.
    """
    try:
        raw = b"".join(regular_chunks(run_dir / "workflow.json", follow=False))
        manifest = json.loads(raw.decode("utf-8"))
        return {key: value for key, value in manifest["run"].items() if isinstance(value, str)}
    except FileNotFoundError:
        return {}
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        RecursionError,
        MemoryError,
    ) as error:
        if issues is not None:
            issues.append(f"{run_dir.name}: workflow.json could not be read ({describe(error)})")
        return {}


def delivery_identity(folder: str, manifest: dict[str, Any]) -> dict[str, Any] | str:
    """A deliverable's recorded run and issuer, or the reason its view.json states none."""
    try:
        identity = manifest["run"]
        run_id, name = identity["run_id"], identity["issuer_name"]
        issuer_id = identity.get("issuer_id") or None
    except MANIFEST_ERRORS as error:
        return f"view.json states no run identity ({describe(error)})"
    if not (isinstance(run_id, str) and isinstance(name, str) and name):
        return "view.json states no run identity (run_id and issuer_name must be text)"
    valid_id = issuer_id if isinstance(issuer_id, str) else None
    return {"folder": folder, "run_id": run_id, "issuer_id": valid_id, "issuer_name": name}


def delivery_identities(
    root: Path, catalogue: dict[str, Any], manifests: Manifests | None = None
) -> list[dict[str, Any]]:
    """What each available (hash-verified) deliverable says about its own run and issuer.

    A deliverable whose view.json cannot be read, or states no run identity, is skipped here;
    workspace_store names it in Workspace issues, so the failure is reported once and no run
    takes an identity from it. `manifests` are the folders' model_manifests, read when omitted.
    """
    manifests = (
        model_manifests(root, available_folders(catalogue)) if manifests is None else manifests
    )
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for run in catalogue["real"]:
        for artifact in run.get("artifacts") or []:
            folder = artifact["folder"]
            if not artifact.get("available") or folder in seen:
                continue
            seen.add(folder)
            manifest = manifests.get(folder)
            if isinstance(manifest, tuple) and isinstance(
                identity := delivery_identity(folder, manifest[1]), dict
            ):
                found.append(identity)
    return sorted(found, key=lambda item: item["folder"])


def squeezed(text: str) -> str:
    """A name compared as a reader reads it: case and runs of spaces do not count."""
    return " ".join(text.split()).casefold()


def named_run_id(
    name: str, issuer_id: str | None, delivered: list[dict[str, Any]]
) -> tuple[str | None, str | None]:
    """A named run's ID and the issue to report, from what its deliverables say.

    Deliverables agree when their case-folded IDs agree, whatever they call the issuer. If they
    disagree, the ID the run has stays and the disagreement is reported. If they agree on an ID
    but call the issuer something other than the run's name, the ID is taken and the names are
    reported.
    """
    if len({(item["issuer_id"] or "").casefold() for item in delivered}) > 1:
        return issuer_id, "deliverables name different issuers; no issuer ID taken"
    if not delivered:
        return issuer_id, None
    others = sorted(
        {
            item["issuer_name"]
            for item in delivered
            if squeezed(item["issuer_name"]) != squeezed(name)
        }
    )
    taken = issuer_id or delivered[0]["issuer_id"]
    issue = (
        f"deliverables name the issuer {', '.join(repr(o) for o in others)}, not {name!r}; "
        + ("issuer ID kept" if taken else "no issuer ID recorded")
        if others
        else None
    )
    return taken, issue


def recorded_identity(
    run_dir: Path, run: dict[str, Any], curated_name: str | None, delivered: list[dict[str, Any]]
) -> tuple[str | None, str | None, str | None]:
    """A run's recorded issuer (name, ID) and, if its deliverables disagree, the issue to report.

    Name: curated, else the launcher manifest, else a catalogue name unlike the folder, else what
    its deliverables agree on. ID: manifest, else the catalogue's issuer, else the deliverables'.
    """
    manifest = recorded_run(run_dir)
    name = (
        curated_name
        or manifest.get("issuer_name")
        or (run["name"] if run["name"] != run["id"] else None)
    )
    seeded = run.get("issuer")
    issuer_id = manifest.get("issuer_id") or (seeded if seeded != "Unclassified" else None)
    said: dict[tuple[str, Any], dict[str, Any]] = {}
    # In folder order, so the first deliverable's spelling of the ID is kept.
    for item in delivered:
        said.setdefault(((item["issuer_id"] or "").casefold(), item["issuer_name"]), item)
    if name:
        return name, *named_run_id(name, issuer_id, delivered)
    if len(said) > 1:
        return None, issuer_id, "deliverables name different issuers; issuer left unrecorded"
    if said:
        (agreed,) = said.values()
        return agreed["issuer_name"], issuer_id or agreed["issuer_id"], None
    return None, issuer_id, None


def ids_by_name(named: dict[str, tuple[str, str | None]]) -> dict[str, dict[str, str]]:
    """Each recorded name's IDs as recorded, by case-folded ID."""
    carried: dict[str, dict[str, str]] = {}
    for _, (name, issuer_id) in sorted(named.items()):  # run-path order, not insertion order
        if issuer_id:
            carried.setdefault(name, {}).setdefault(issuer_id.casefold(), issuer_id)
    return carried


def issuer_groups(
    recorded: dict[str, tuple[str | None, str | None]], issues: list[str] | None = None
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """Group runs by issuer. recorded maps run key to (name or None, ID or None).

    Runs with a name join when they share a case-folded ID. A name joins runs without an ID to the
    one ID that carries it; two different IDs are never joined through a name. A name carried by
    several IDs leaves its runs without an ID in a group of their own and, when `issues` is given,
    adds one issue naming the IDs. Returns the identity fields of every run and a map from each
    case-folded ID to its group's key.
    """
    named = {key: (name, issuer_id) for key, (name, issuer_id) in recorded.items() if name}
    carried = ids_by_name(named)
    if issues is not None:
        issues.extend(
            f"issuer name {name} is recorded with different issuer IDs: "
            + ", ".join(sorted(ids.values(), key=lambda i: (i.casefold(), i)))
            for name, ids in sorted(carried.items())
            if len(ids) > 1
        )
    parent = {key: key for key in named}

    def root_of(key: str) -> str:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    first: dict[tuple[str, str], str] = {}
    for key, (name, issuer_id) in named.items():
        # An ID joins its runs; a run without an ID joins its name's one ID, else other such runs.
        if issuer_id:
            token = ("id", issuer_id.casefold())
        else:
            holders = carried.get(name, {})
            token = ("id", next(iter(holders))) if len(holders) == 1 else ("name", name)
        parent[root_of(key)] = root_of(first.setdefault(token, key))
    members: dict[str, list[str]] = {}
    for key in named:
        members.setdefault(root_of(key), []).append(key)
    fields: dict[str, dict[str, Any]] = {
        key: {"issuerKey": None, "issuerHeading": None, "issuerTerms": []} for key in recorded
    }
    keys: dict[str, str] = {}
    for group in members.values():
        names = Counter(named[key][0] for key in group)
        heading = min(names, key=lambda name: (-names[name], name.casefold(), name))
        ids = {known for key in group if (known := named[key][1])}
        folded = {issuer_id.casefold() for issuer_id in ids}
        group_key = f"id:{min(folded)}" if folded else f"name:{heading}"
        keys |= dict.fromkeys(folded, group_key)
        for key in group:
            fields[key] = {
                "issuerKey": group_key,
                "issuerHeading": heading,
                "issuerTerms": sorted({*names, *ids}),
            }
    return fields, keys


def report_issuer_key(keys: dict[str, str], issuer_id: Any) -> str | None:
    """The key of the group holding a report's issuer ID, or one built from that ID alone."""
    if not isinstance(issuer_id, str) or not issuer_id:
        return None
    return keys.get(issuer_id.casefold(), f"id:{issuer_id.casefold()}")


def run_row(root: Path, run: dict[str, Any], name: str | None = None) -> tuple[str, ...]:
    """Labels for a run with no curated ones: the launcher's own manifest, else the catalogue."""
    folder = run["id"]
    identity = recorded_run(root / "runs" / folder)
    issuer = name or identity.get("issuer_name") or run["name"]
    period = (
        f"As of {display_date(identity['as_of'])}"
        if identity.get("as_of")
        else run.get("period") or "Period not recorded"
    )
    # A web run's folder is 32 hex characters; eight are enough to tell runs apart on screen.
    label = folder.upper()[:12] if WEB_RUN.fullmatch(folder) else folder.upper()
    return (folder, issuer, issuer, label, run.get("sector") or "Unclassified", period)


def shown_runs(
    root: Path, catalogue: dict[str, Any], issues: list[str], manifests: Manifests | None = None
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str | None, str | None]]]:
    """The runs to show by route key, and each one's recorded (issuer name, issuer ID).

    A folder that cannot be linked or that takes a retained case's route key is named in `issues`.
    """
    curated = {row[0]: (key, row) for key, row in CURATED_RUNS.items()}
    shown: dict[str, tuple[str, ...]] = {}
    recorded: dict[str, tuple[str | None, str | None]] = {}
    delivered: dict[str, list[dict[str, Any]]] = {}
    for item in delivery_identities(root, catalogue, manifests):
        delivered.setdefault(item["run_id"], []).append(item)
    route_keys = {curated[run["id"]][0] for run in catalogue["real"] if run["id"] in curated}
    for run in catalogue["real"]:
        folder = run["id"]
        if folder.startswith("delivery:"):
            continue
        if not SAFE_FOLDER.fullmatch(folder):
            issues.append(f"{folder}: folder name cannot be linked; rename it to show this run")
            continue
        if folder in route_keys and folder not in curated:
            # The route key names the retained case in links and pins: never replace it.
            issues.append(f"{folder}: name is a retained case's route key; rename it to show it")
            continue
        key, row = curated.get(folder) or (folder, None)
        name, issuer_id, problem = recorded_identity(
            root / "runs" / folder, run, row[1] if row else None, delivered.get(folder, [])
        )
        if problem:
            issues.append(f"runs/{folder}: {problem}")
        shown[key] = row or run_row(root, run, name)
        recorded[key] = (name, issuer_id)
    return shown, recorded


SHA_TEXT = re.compile(r"[0-9a-f]{64}")
EXTENSION_WORDS = re.compile(r"((?:\.[A-Za-z]+)+)$")
CALL_FIELDS = (
    ("module", "module_id"),
    ("attempt", "attempt"),
    ("started", "started_at"),
    ("http_status", "http_status"),
    ("error_class", "error_class"),
    ("settled_usd", "settled_usd"),
)


def stored_text(value: Any) -> str | None:
    """A stored string as it is; anything else is missing, never a made-up value."""
    return value if isinstance(value, str) else None


def run_json(path: Path, issues: list[str], what: str) -> Any:
    """A run file's JSON, or None with an issue naming why not (a documented fail-open: the
    Evidence page then lacks that part; the failure is in Workspace issues)."""
    try:
        return json.loads(b"".join(regular_chunks(path, follow=False)).decode("utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        issues.append(f"{what} could not be read ({describe(error)})")
        return None


def file_type(name: str) -> str | None:
    """The file's trailing alphabetic extension words as written (`pdf`, `htm.jsonl`)."""
    found = EXTENSION_WORDS.search(name)
    return found[1][1:] if found else None


def sources_section_text(sections: list[dict[str, Any]]) -> str:
    """Every cell and paragraph under the handoff's `## Sources` heading (its subsections too)."""
    parts: list[str] = []
    inside = False
    for section in sections:
        if section["level"] <= 2:
            inside = section["level"] == 2 and section["heading"].strip() == "Sources"
        if not inside:
            continue
        for block in section["blocks"]:
            if block["type"] == "text":
                parts.append(block["text"])
            elif block["type"] == "table":
                parts.extend(block["headers"])
                parts.extend(cell for row in block["rows"] for cell in row["cells"])
    return "\n".join(parts)


def names_file(sources_text: str, name: str) -> bool:
    """Whether the Sources text names the file exactly: the whole name, with only the start or end
    of the text, white space, `|` or `,` on either side. `report.pdf` is not named by
    `annual-report.pdf`."""
    return re.search(rf"(?<![^\s|,]){re.escape(name)}(?![^\s|,])", sources_text) is not None


def has_sources_section(sections: list[dict[str, Any]]) -> bool:
    """Whether the handoff has a `## Sources` heading at all (even an empty one)."""
    return any(s["level"] == 2 and s["heading"].strip() == "Sources" for s in sections)


def document_dates(sections: list[dict[str, Any]]) -> dict[str, str]:
    """The Document date a handoff's table records for a file: in a table with `Source` and
    `Document date` columns, the date cell of the row whose Source cell is exactly the file name,
    copied as written. A blank cell, or one reading "not stated" (any case, surrounding space
    ignored), records nothing, so a later module that saw the date supplies it; no date is parsed
    or read from a file name."""
    found: dict[str, str] = {}
    for section in sections:
        for block in section["blocks"]:
            if block["type"] != "table":
                continue
            heads = [h.strip() for h in block["headers"]]
            if "Source" not in heads or "Document date" not in heads:
                continue
            name_at, date_at = heads.index("Source"), heads.index("Document date")
            for row in block["rows"]:
                date = row["cells"][date_at].strip()
                if date and date.casefold() != "not stated":
                    found.setdefault(row["cells"][name_at].strip(), date)
    return found


def run_calls(run_dir: Path, folder: str, issues: list[str]) -> list[dict[str, Any]]:
    """live/calls.jsonl as recorded: one row per call with the fields as stored. A file that is not
    UTF-8 text lists no call and is named in the issues (documented fail-open: no byte is replaced
    with a guess)."""
    try:
        raw = b"".join(regular_chunks(run_dir / "live" / "calls.jsonl", follow=False))
    except FileNotFoundError:
        return []
    except OSError as error:
        issues.append(f"{folder}: live/calls.jsonl could not be read ({describe(error)})")
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        bad = raw[: error.start].count(b"\n") + 1
        issues.append(
            f"{folder}: live/calls.jsonl is not UTF-8 text (line {bad}); no call is listed"
        )
        return []
    calls: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            call = json.loads(line)
        except ValueError:
            call = None
        if not isinstance(call, dict):
            issues.append(f"{folder}: live/calls.jsonl line {number} is not a call record")
            continue
        calls.append({key: call.get(field) for key, field in CALL_FIELDS})
    return calls


def run_hashes(run_dir: Path, workflow: dict[str, Any], issues: list[str]) -> list[dict[str, Any]]:
    """The hashes a run records: its supplied files and instructions (workflow.json), then its
    delivery manifest and completion record, hashed from the files themselves."""
    rows: list[dict[str, Any]] = []
    for part in ("sources", "instructions"):
        entries = workflow.get(part)
        for name, entry in (entries if isinstance(entries, dict) else {}).items():
            entry = entry if isinstance(entry, dict) else {}
            label = name if part == "sources" else str(entry.get("path") or name)
            rows.append({"name": label, "sha256": stored_text(entry.get("sha256"))})
    for pattern in ("delivery-*.json", "completed-*.json"):
        for path in sorted(run_dir.glob(pattern)):
            try:
                rows.append({"name": path.name, "sha256": sha256(path)})
            except OSError as error:
                issues.append(
                    f"{run_dir.name}: {path.name} could not be hashed ({describe(error)})"
                )
                rows.append({"name": path.name, "sha256": None})
    return rows


def instruction_rows(
    workflow: dict[str, Any], folder: str, issues: list[str]
) -> list[dict[str, Any]]:
    """The instructions each module was sent, as the run's workflow.json records them. A usable
    row links to the copy update_library writes under the library folder (so it opens when the
    library is served too)."""
    entries = workflow.get("instructions")
    rows: list[dict[str, Any]] = []
    for module, entry in (entries if isinstance(entries, dict) else {}).items():
        entry = entry if isinstance(entry, dict) else {}
        path, digest = entry.get("path"), stored_text(entry.get("sha256"))
        parts = PurePosixPath(path).parts if isinstance(path, str) else ()
        safe = (
            isinstance(path, str)
            and bool(parts)
            and not (path.startswith("/") or ".." in parts or "\\" in path or ":" in path)
        )
        usable = safe and digest is not None and SHA_TEXT.fullmatch(digest) is not None
        named = isinstance(module, str) and HANDOFF_NAME.fullmatch(module) is not None
        if not named:
            issues.append(f"{folder}: instructions key {module!r} is not a module code; no link")
        elif not usable:
            issues.append(f"{folder}: instructions for {module} have no usable path or hash")
        usable = usable and named
        rows.append(
            {
                "module": module,
                "href": f"downloads/{quote(folder)}/instructions/{quote(module)}.md"
                if usable
                else None,
                "sha256": digest,
            }
        )
    return rows


def run_downloads(
    run: dict[str, Any], key: str, models: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """The Model and calculation files of the models this run's Forecast lists (the rule of
    views.js runModels), each as a label and a download link."""
    rows: list[dict[str, Any]] = []
    for model in sorted(models, key=lambda m: m["id"]):
        holds = model["issuerKey"] == run["issuerKey"] and (
            (model["runId"] is not None and model["runId"] == run["folder"])
            or model["runFolder"] == run["folder"]
            or any(source["run"] == key for source in model["sources"])
        )
        if not holds:
            continue
        rows.append({"label": f"Model {model['id']}", "href": model["download"]})
        rows.extend(
            {"label": f"{model['id']}: {f['name']}", "href": f["href"]}
            for f in model["files"]
            if f["name"] in ("calculation.json", "forecast_exact.json")
        )
    return rows


class EvidenceReads(NamedTuple):
    """What the store holds when Evidence is built: the workspace root, the outputs, the parsed
    handoffs by hash and the models."""

    root: Path
    outputs: dict[str, Any]
    sections: dict[str, list[dict[str, Any]]]
    models: list[dict[str, Any]]


def run_evidence(
    key: str, run: dict[str, Any], held: EvidenceReads, issues: list[str]
) -> dict[str, Any]:
    """The run's Evidence page, as data: supplied files and who read them, the delivered
    handoffs, the downloads and the run record. Every value is as stored; one the run does not
    record is None."""
    folder = run["folder"]
    run_dir = held.root / "runs" / folder
    workflow = run_json(run_dir / "workflow.json", issues, f"{folder}: workflow.json")
    workflow = workflow if isinstance(workflow, dict) else {}
    handoffs = []
    read_by: dict[str, list[str]] = {}
    no_sources: list[str] = []
    dates: dict[str, str] = {}
    supplied = workflow.get("sources")
    supplied = supplied if isinstance(supplied, dict) else {}
    # The earlier run's handoffs, pinned for CP-8 alone (owner, 2026-11-11), are not issuer files.
    names = [name for name in supplied if name != "context" and not name.startswith("prior/")]
    for module, entry in run["modules"].items():
        output = held.outputs.get(entry["default"] or "")
        if output is None:
            continue
        handoffs.append(
            {
                "module": module,
                "name": f"{module}.md",
                "href": f"downloads/{quote(folder)}/{quote(module)}.md",
            }
        )
        parsed = held.sections[output["sha256"]]
        for name, date in document_dates(parsed).items():
            dates.setdefault(name, date)
        if not has_sources_section(parsed):
            no_sources.append(module)
        text = sources_section_text(parsed)
        for name in names:
            if names_file(text, name):
                read_by.setdefault(name, []).append(module)
    rows = [
        {
            "name": name,
            "sha256": stored_text(supplied[name].get("sha256"))
            if isinstance(supplied[name], dict)
            else None,
            "type": file_type(name),
            "documentDate": dates.get(name),
            "readBy": read_by.get(name, []),
        }
        for name in names
    ]
    cap = workflow.get("provider_cap_usd")
    # No delivered handoff has a Sources section: the run recorded nothing about use, so an
    # unnamed file is "use not recorded", not "not used" (missing is not zero).
    nothing_recorded = len(no_sources) == len(handoffs)
    unnamed = [row for row in rows if not row["readBy"]]
    return {
        "sources": [row for row in rows if row["readBy"]],
        "unused": [] if nothing_recorded else unnamed,
        "unrecorded": unnamed if nothing_recorded else [],
        "noSourcesModules": no_sources,
        "handoffs": handoffs,
        "zip": f"downloads/{quote(folder)}/handoffs.zip" if handoffs else None,
        "downloads": run_downloads(run, key, held.models),
        "record": {
            "hashes": run_hashes(run_dir, workflow, issues),
            "instructions": instruction_rows(workflow, folder, issues),
            "calls": run_calls(run_dir, folder, issues),
            "cap": cap if isinstance(cap, (str, int, float)) else None,
        },
    }


def workspace_store(root: str | Path, catalogue: dict[str, Any]) -> dict[str, Any]:
    """Everything the app reads. A curated pin that stopped matching is dropped, not fatal."""
    root = Path(root)
    catalog = json.loads((HERE / "catalog.json").read_text(encoding="utf-8"))
    issues = list(catalogue.get("issues") or [])
    manifests = model_manifests(root, available_folders(catalogue))
    shown, recorded = shown_runs(root, catalogue, issues, manifests)

    def link(folder: str, relative: str, digest: str) -> str:
        return f"/files/{quote(f'runs/{folder}/{relative}')}?sha256={digest}"

    runs: dict[str, Any] = {}
    outputs: dict[str, Any] = {}
    inputs: dict[str, Any] = {}
    pins: dict[str, Any] = {}
    handoffs = Handoffs(strict=False)
    found: list[str] = []
    for key, row in shown.items():
        # Documented fail-open: one run that cannot be read is hidden and reported in Settings.
        try:
            part = collect_runs(root, {key: row}, catalog, link, handoffs)
        except Exception as error:  # noqa: BLE001
            found.append(f"{row[0]}: could not be read ({describe(error)})")
            continue
        runs |= part[0]
        outputs |= part[1]
        inputs |= part[2]
        pins |= part[3]
        found += part[4]
    # A recorded earlier run is linked only when the library holds a run with that id.
    by_id = {run["runId"]: key for key, run in runs.items() if run["runId"]}
    for run in runs.values():
        for revision in run["revisions"]:
            revision["run"] = by_id.get(revision["id"])
    fields, keys = issuer_groups({key: recorded[key] for key in runs}, found)
    for key, identity in fields.items():
        runs[key].update(identity)
    models, unread = catalogue_models(
        root, catalogue, WorkspaceReads(outputs, keys, runs, manifests)
    )
    found += unread
    held = EvidenceReads(root, outputs, {h: p[0] for h, p in handoffs.parsed.items()}, models)
    for key, run in runs.items():
        run["evidence"] = run_evidence(key, run, held, found)
    # A deliverable that cannot be read is named here (read_model names a model's own folder).
    for folder, manifest in manifests.items():
        reason = manifest if isinstance(manifest, str) else delivery_identity(folder, manifest[1])
        if (
            isinstance(reason, str)
            and (message := f"{folder}: could not be read ({reason})") not in found
        ):
            found.append(message)
    # A compared deliverable is a curated build, not a folder that merely has its name.
    builds = curated_builds(catalogue, manifests)
    for module, config in catalog.items():
        compare = config.get("compare")
        if (
            module in pins
            and compare
            and not (
                compare["recheck"] in outputs
                and {compare["prior"], compare["current"], compare["repaired"]} <= builds
            )
        ):
            del pins[module]
            found.append(
                f"{module}: curated pin dropped: a compared deliverable or recheck is missing"
            )
    return {
        "runs": runs,
        "outputs": outputs,
        # Only what an output shown refers to: a run that failed part-way leaves nothing behind.
        "handoffs": {o["sha256"]: handoffs.parsed[o["sha256"]][0] for o in outputs.values()},
        "inputs": inputs,
        "pins": pins,
        "models": models,
        "visuals": visual_catalogue(),
        "issues": issues + found,
    }


if __name__ == "__main__":
    print(json.dumps(workspace_store(Path(sys.argv[1]), json.load(sys.stdin)), ensure_ascii=False))
