"""The library's store: every retained handoff in a workspace, parsed for reading.

Reads files only. Nothing here runs analysis, calls a provider or changes a workspace.
The server imports this on each page load, so it imports only the standard library.
"""

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple
from urllib.parse import quote

from credit_os.cashflow import (
    ADD_BACK_ROW_LIMIT,
    ADJUSTED,
    CARRYING,
    CASH,
    CASHFLOW_CELL_BUDGET,
    CASHFLOW_ERRORS,
    CASHFLOW_FILES,
    CASHFLOW_LABELS,
    CASHFLOW_NOTES,
    CELL_OPS,
    CODE_SPAN,
    COMPONENT_MISSING,
    CREDIT,
    DEBT,
    DEBT_SENIOR_NEEDED,
    DEBT_TOTAL_NEEDED,
    DOWNSIDE_CASE,
    DOWNSIDE_NOTES,
    FENCE_LINE,
    FISCAL_HEADER,
    FISCAL_YEAR_LIMIT,
    FORECAST_CASES,
    FORECAST_YEAR_LIMIT,
    FY_PLACEHOLDER,
    HEAD_ROWS,
    HEADING_START,
    HISTORY_COLUMN_LIMIT,
    HISTORY_GROUPS,
    HISTORY_KEYS,
    HISTORY_LABELS,
    HISTORY_LIMIT_CHARS,
    HISTORY_LIMIT_COUNT,
    HISTORY_NOTES,
    HISTORY_PRIOR_KINDS,
    HISTORY_SCHEMA,
    INCOME,
    LABEL_LIMIT,
    LENGTH_DIFFERS,
    LTM_NEEDED,
    LTM_NOTE,
    MARKS,
    MONTHS_SHORT,
    NO_DOWNSIDE,
    NO_LINE,
    NO_VALUE,
    PRINTED_DASH,
    PRIOR_MISSING,
    PRIOR_NOT_YEAR,
    PROXY,
    Q1_NOTE,
    QUARTER_COLUMN_LIMIT,
    QUARTER_DAYS,
    QUARTER_HEADER,
    QUARTER_LENGTH_SLACK,
    REASON_PHRASES,
    REGISTER_DATE,
    SEPARATOR,
    SEPARATOR_CELL,
    STRESS_ON_DOWNSIDE_DRIVERS,
    TABLE_NUMBER,
    TABLE_ROW,
    TABLE_ROW_LIMIT,
    TAIL_ROWS,
    TOTAL_AT_EDGE,
    TOTAL_ROWS,
    TOTAL_WORD,
    UNIT_ROW_LIMIT,
    UNITS_LIMIT,
    YEAR_DAYS,
    CashflowBudget,
    CashflowInputs,
    CashflowLimit,
    Cell,
    CellContext,
    Column,
    Fiscal,
    Forecast,
    GridAsk,
    History,
    PeriodKey,
    Recorded,
    RowKey,
    RowSpec,
    SecuredDebt,
    Span,
    Spec,
    Table,
    absent_cell,
    add_back_labels,
    add_cells,
    amount_cell,
    capped,
    cashflow_notes,
    cashflow_of,
    cashflow_or_issues,
    cashflow_rows,
    cashflow_units,
    cell_count,
    check_history_priors,
    checked_entries,
    derive,
    display_amount,
    every,
    first_year_prior,
    fiscal_columns,
    fiscal_inputs,
    fiscal_year_ends,
    forecast_columns,
    forecast_inputs,
    grid_cell,
    grid_cells,
    held_cell,
    history_column_input,
    history_columns,
    history_inputs,
    history_limits,
    holds_carrying_value,
    inline_comments,
    lengths_differ,
    listed_add_backs,
    listed_labels,
    main_cases,
    markdown_table,
    markdown_tables,
    no_downside_column,
    not_modelled_cell,
    op_growth,
    op_key,
    op_margin,
    op_needs_ltm,
    op_prefer,
    op_quarter,
    op_senior,
    op_sum,
    op_table,
    op_table_sum,
    optional_text,
    period_key,
    plain_label,
    quarter_columns,
    quarter_held,
    quarter_inputs,
    quarter_numbers,
    read_cashflow,
    recorded_units,
    register_date,
    row_part,
    secured_debt,
    shown_lines,
    source_cell,
    span_days,
    spec_cell,
    table_cell,
    table_cells,
    table_holding,
    table_row,
    total_kind,
    twelve_months,
    unavailable_cell,
    units_caption,
)
from credit_os.evidence import (
    CALL_FIELDS,
    EXTENSION_WORDS,
    SHA_TEXT,
    EvidenceReads,
    document_dates,
    file_type,
    has_sources_section,
    instruction_rows,
    names_file,
    run_calls,
    run_downloads,
    run_evidence,
    run_hashes,
    run_json,
    sources_section_text,
    stored_text,
)
from credit_os.handoff_fields import (
    BULLET,
    CHART_FIRST_COLUMNS,
    CHART_LAST_COLUMNS,
    CHART_PREFIX,
    COMMITTEE_STATUS,
    CONFIDENCE_NOT_ASSESSABLE,
    DIRECTIONS,
    EVENT_HEADERS,
    EVENT_PREFIX,
    EVENT_SHAPES,
    EVENT_STATUS,
    EVIDENCE_HEADING,
    LEVEL_TWO_PLACEMENT,
    MAP_EDGES,
    MAP_HEADERS,
    MAP_PREFIX,
    MONEY_HEADINGS,
    MONEY_UNIT,
    PAIR_KINDS,
    PLAIN_AMOUNT,
    READER_TABLES,
    ROW_CHARTS,
    STATED_GAP,
    STEP_HEADERS,
    WORD_GROUPS,
    placements,
    reader_fields,
    report_fields,
    section_words,
)
from credit_os.source import (
    CHUNK,
    EQUITY_HEADERS,
    HANDOFF_NAME,
    ISO_DATE,
    MODEL_FILE_LIMIT,
    MONTHS,
    UnreadableFile,
    describe,
    display_date,
    equity_block,
    parse_source,
    physical_lines,
    regular_chunks,
    sections_of,
    sha256,
    source_table_cells,
    structured,
    table_block,
    text_block,
    text_or_none,
    valid_date,
)
from deploy_workflow import confidence as confidence_score

# The names moved to the sibling modules, re-exported: callers and tests read and patch them here.
__all__ = [
    "ADD_BACK_ROW_LIMIT",
    "ADJUSTED",
    "BULLET",
    "CALL_FIELDS",
    "CARRYING",
    "CASH",
    "CASHFLOW_CELL_BUDGET",
    "CASHFLOW_ERRORS",
    "CASHFLOW_FILES",
    "CASHFLOW_LABELS",
    "CASHFLOW_NOTES",
    "CELL_OPS",
    "CHART_FIRST_COLUMNS",
    "CHART_LAST_COLUMNS",
    "CHART_PREFIX",
    "CHUNK",
    "CODE_SPAN",
    "COMMITTEE_STATUS",
    "COMPONENT_MISSING",
    "CONFIDENCE_NOT_ASSESSABLE",
    "CREDIT",
    "DEBT",
    "DEBT_SENIOR_NEEDED",
    "DEBT_TOTAL_NEEDED",
    "DIRECTIONS",
    "DOWNSIDE_CASE",
    "DOWNSIDE_NOTES",
    "EQUITY_HEADERS",
    "EVENT_HEADERS",
    "EVENT_PREFIX",
    "EVENT_SHAPES",
    "EVENT_STATUS",
    "EVIDENCE_HEADING",
    "EXTENSION_WORDS",
    "FENCE_LINE",
    "FISCAL_HEADER",
    "FISCAL_YEAR_LIMIT",
    "FORECAST_CASES",
    "FORECAST_YEAR_LIMIT",
    "FY_PLACEHOLDER",
    "HANDOFF_NAME",
    "HEADING_START",
    "HEAD_ROWS",
    "HISTORY_COLUMN_LIMIT",
    "HISTORY_GROUPS",
    "HISTORY_KEYS",
    "HISTORY_LABELS",
    "HISTORY_LIMIT_CHARS",
    "HISTORY_LIMIT_COUNT",
    "HISTORY_NOTES",
    "HISTORY_PRIOR_KINDS",
    "HISTORY_SCHEMA",
    "INCOME",
    "ISO_DATE",
    "LABEL_LIMIT",
    "LENGTH_DIFFERS",
    "LEVEL_TWO_PLACEMENT",
    "LTM_NEEDED",
    "LTM_NOTE",
    "MAP_EDGES",
    "MAP_HEADERS",
    "MAP_PREFIX",
    "MARKS",
    "MODEL_FILE_LIMIT",
    "MONEY_HEADINGS",
    "MONEY_UNIT",
    "MONTHS",
    "MONTHS_SHORT",
    "NO_DOWNSIDE",
    "NO_LINE",
    "NO_VALUE",
    "PAIR_KINDS",
    "PLAIN_AMOUNT",
    "PRINTED_DASH",
    "PRIOR_MISSING",
    "PRIOR_NOT_YEAR",
    "PROXY",
    "Q1_NOTE",
    "QUARTER_COLUMN_LIMIT",
    "QUARTER_DAYS",
    "QUARTER_HEADER",
    "QUARTER_LENGTH_SLACK",
    "READER_TABLES",
    "REASON_PHRASES",
    "REGISTER_DATE",
    "ROW_CHARTS",
    "SEPARATOR",
    "SEPARATOR_CELL",
    "SHA_TEXT",
    "STATED_GAP",
    "STEP_HEADERS",
    "STRESS_ON_DOWNSIDE_DRIVERS",
    "TABLE_NUMBER",
    "TABLE_ROW",
    "TABLE_ROW_LIMIT",
    "TAIL_ROWS",
    "TOTAL_AT_EDGE",
    "TOTAL_ROWS",
    "TOTAL_WORD",
    "UNITS_LIMIT",
    "UNIT_ROW_LIMIT",
    "WORD_GROUPS",
    "YEAR_DAYS",
    "CashflowBudget",
    "CashflowInputs",
    "CashflowLimit",
    "Cell",
    "CellContext",
    "Column",
    "EvidenceReads",
    "Fiscal",
    "Forecast",
    "GridAsk",
    "History",
    "PeriodKey",
    "Recorded",
    "RowKey",
    "RowSpec",
    "SecuredDebt",
    "Span",
    "Spec",
    "Table",
    "UnreadableFile",
    "absent_cell",
    "add_back_labels",
    "add_cells",
    "amount_cell",
    "capped",
    "cashflow_notes",
    "cashflow_of",
    "cashflow_or_issues",
    "cashflow_rows",
    "cashflow_units",
    "cell_count",
    "check_history_priors",
    "checked_entries",
    "derive",
    "describe",
    "display_amount",
    "display_date",
    "document_dates",
    "equity_block",
    "every",
    "file_type",
    "first_year_prior",
    "fiscal_columns",
    "fiscal_inputs",
    "fiscal_year_ends",
    "forecast_columns",
    "forecast_inputs",
    "grid_cell",
    "grid_cells",
    "has_sources_section",
    "held_cell",
    "history_column_input",
    "history_columns",
    "history_inputs",
    "history_limits",
    "holds_carrying_value",
    "inline_comments",
    "instruction_rows",
    "lengths_differ",
    "listed_add_backs",
    "listed_labels",
    "main_cases",
    "markdown_table",
    "markdown_tables",
    "names_file",
    "no_downside_column",
    "not_modelled_cell",
    "op_growth",
    "op_key",
    "op_margin",
    "op_needs_ltm",
    "op_prefer",
    "op_quarter",
    "op_senior",
    "op_sum",
    "op_table",
    "op_table_sum",
    "optional_text",
    "parse_source",
    "period_key",
    "physical_lines",
    "placements",
    "plain_label",
    "quarter_columns",
    "quarter_held",
    "quarter_inputs",
    "quarter_numbers",
    "read_cashflow",
    "reader_fields",
    "recorded_units",
    "register_date",
    "regular_chunks",
    "report_fields",
    "row_part",
    "run_calls",
    "run_downloads",
    "run_evidence",
    "run_hashes",
    "run_json",
    "section_words",
    "sections_of",
    "secured_debt",
    "sha256",
    "shown_lines",
    "source_cell",
    "source_table_cells",
    "sources_section_text",
    "span_days",
    "spec_cell",
    "stored_text",
    "structured",
    "table_block",
    "table_cell",
    "table_cells",
    "table_holding",
    "table_row",
    "text_block",
    "text_or_none",
    "total_kind",
    "twelve_months",
    "unavailable_cell",
    "units_caption",
    "valid_date",
]

HERE = Path(__file__).resolve().parent
REPO = next((p for p in (HERE, HERE.parent) if (p / "src").is_dir()), HERE.parents[2])
OUTPUT_SKIP = re.compile(r"instructions|prompt|calculations|verification")
INPUT_NAME = re.compile(r"selected-input|peer-inputs|delivery|-request\.md")
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


WEB_RUN = re.compile(r"web-[a-f0-9]{32}")


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
    result = confidence_score.from_handoff(raw.decode("utf-8-sig", "replace"))
    if isinstance(result, confidence_score.Refused):
        return {} if result.absent else {"confidence": {"missing": result.shown}}
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
