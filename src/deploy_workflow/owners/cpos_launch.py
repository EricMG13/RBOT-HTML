"""Start a CP-OS run from a context file, an issuer folder and a selected model.

Without ``--live`` this only prepares: it pins the inputs, writes ``workflow.json`` with the module
instructions, prints the plan and calls no provider. ``--live`` passes that manifest to
``cpos.run_live_handoffs``, which keeps ordering, retention, resume, budget and delivery.

The generic check here covers handoff structure, issuer/date/source/upstream anchors and report
selectors. It has no independent expected values, so a passing run is not analytical review; every
report says so in its scope. CP-1 fills the chart strip from fixed tables. ponytail: the HTML Model
needs issuer-specific row selectors; add it when a run can derive those from CP-1's actual tables.
"""

import argparse
import functools
import hashlib
import importlib.util
import json
import logging
import os
import re
import sys
import tempfile
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from deploy_vii.contracts import (
    DEACTIVATED_MESSAGE,
    DEACTIVATED_PATHWAYS,
    PATHWAY_CAP_USD,
    PATHWAY_MODULES,
    PathwayId,
    Run,
)
from deploy_vii.registry import dependencies, modules, plan
from deploy_vii.report_view import _spec_of, pathways
from deploy_workflow import (
    method_scripts,
    method_scripts_completeness,  # noqa: F401 - registers the shared check
    platform_io,
)
from deploy_workflow.changes import (
    DELIVERED_WHOLE,
    PACK_NAME,
    PRIOR_PREFIX,
    PriorRun,
    describe,
    describe_run,
    find_prior,
    prior_sources,
    workspace_of,
)
from deploy_workflow.changes_check import cp8_issues
from deploy_workflow.context import CONTEXT_SOURCE_ID, RunContext, load_context
from deploy_workflow.credit_os_chips import MODULE_NAMES
from deploy_workflow.docx_text import docx_text
from deploy_workflow.handoff_delivery import (
    BLANK_SPLITS,
    DeliveryRequest,
    HandoffInput,
    MarkdownLayout,
    MarkdownRoute,
    table_faults,
)
from deploy_workflow.html_text import convert_html
from deploy_workflow.markdown_delivery import (
    STRIP_FIGURES,
    literal_module,
    markdown_files,
    require_issuer,
)
from deploy_workflow.model import copilot as copilot_route
from deploy_workflow.model.adapter import (
    COPILOT_GH_LOGIN_VARIABLE,
    COPILOT_RUNTIME_VARIABLE,
    KEY_VARIABLES,
    LivePauseInForce,
    check_ruling,
)
from deploy_workflow.model.budget import Budget
from deploy_workflow.model.configs import CONFIGS
from deploy_workflow.model.handoff import (
    BYTES_PER_TOKEN_BOUND,
    REQUEST_OVERHEAD,
    WEB_LOOKUP_MODULES,
    WEB_SEARCH_CALLS_PER_TURN,
    WEB_SEARCH_CASE_KINDS,
    Check,
    _pages,
    recorded_web_lookup,
    settled_web_lookup,
    web_lookup_offered,
    web_search_offered,
)
from deploy_workflow.model.pricing import (
    ContextTooLong,
    price_of,
    request_reservation_usd,
    web_search_usd,
)
from deploy_workflow.model.turn import MODEL_EFFORTS, dump_json
from deploy_workflow.owners import cpos_forecast
from deploy_workflow.owners.cpos import (
    WEB_SEARCH_GRANT,
    HandoffPlan,
    HandoffTask,
    run_live_handoffs,
    web_search_ruled,
    web_search_run,
    with_notes,
)
from deploy_workflow.owners.cpos_cp1_check import cp1_issues as _cp1_issues
from deploy_workflow.owners.cpos_cp1_check import money_unit
from deploy_workflow.owners.cpos_launch_methods import (
    _APPENDIX,
    _SCORE,
    METHODS,
    REGISTER_SCOPE,
    REGISTER_SCOPE_MODULES,
)
from deploy_workflow.owners.cpos_launch_prompts import (
    APPENDIX_HEADING_NOTE,
    CHART_NOTE_RULE,
    CONFIDENCE_RULE,
    CP0_BLOCK,
    CP1_CHECK_BLOCK,
    CP3_MODE_BLOCK,
    CP3_MODE_LABELS,
    CP6A_BLOCK,
    CP8_BLOCK,
    CURRENCY_RULE,
    DATA_PASSAGE,
    DEEP_DEBATE_BLOCK,
    FORECAST_BLOCK,
    LAYER1_FORECAST_BLOCK,
    MAP_TEXT_RULE,
    METHOD_MARK,
    PEER_PACK_BLOCK,
    PEER_READER_BLOCK,
    PERIOD_REQUIRED_BLOCK,
    PERIOD_TABLE_BLOCK,
    POSTURE_HEADING,
    POSTURES,
    PRESENCE_RULE,
    PROSE_PASSAGES,
    READER_PERSONA,
    ROUTING_RULES,
    SOURCES_RULES,
    STRESS_BLOCK,
    TRANSPORT_RULES,
    UPSTREAM_SCOPE_NOTE,
    VOICE_RULES,
    _and_list,
    _none_rule,
    _selector,
)
from deploy_workflow.owners.cpos_launch_review import _charge_notes, _print_review, _review_lines
from deploy_workflow.owners.cpos_launch_tables import (
    CHART_BLOCKS,
    CHART_TABLES,
    CURRENCY_CODES,
    DEBT_RECON,
    DIRECTIONS,
    EDGE_RULES,
    EVENT_COLUMNS,
    EVENT_LANES,
    EVENT_STATUS,
    MAPS,
    MONEY,
    NET_DEBT,
    NO_MONEY,
    OWNER_TABLES,
    POST_BS,
    OwnerTable,
    _chart_header,
    _chart_route,
    _net_debt_issues,
    _owner_tables,
    chart_issues,
)
from deploy_workflow.portfolio_workbook import NOT_COLLECTED, PortfolioCheck
from deploy_workflow.portfolio_workbook import check as portfolio_check
from deploy_workflow.portfolio_workbook import instructions as portfolio_instructions
from deploy_workflow.portfolio_workbook import readiness_lines as portfolio_lines
from deploy_workflow.prose_checks import (
    DATA_MODULES,
    READER_HEADINGS,
    figure_issues,
    findings_sentences,
    key_figures_issues,
    prose_issues,
)
from deploy_workflow.research.intake import effective_cutoff
from deploy_workflow.research.weblookup import USER_AGENT_ENV, bare_host_problem, usable_user_agent
from deploy_workflow.run_expectations import Item, edges_for, expectations, guess_kind
from deploy_workflow.workflow import _put

log = logging.getLogger(__name__)
# Names moved to the cpos_launch_* modules that callers and tests still import from here. Patch
# a moved name in its own module: a patch here does not reach the moved code that reads it.
__all__ = [
    "APPENDIX_HEADING_NOTE",
    "CHART_BLOCKS",
    "CHART_NOTE_RULE",
    "CHART_TABLES",
    "CONFIDENCE_RULE",
    "CP0_BLOCK",
    "CP1_CHECK_BLOCK",
    "CP3_MODE_BLOCK",
    "CP3_MODE_LABELS",
    "CP6A_BLOCK",
    "CP8_BLOCK",
    "CURRENCY_CODES",
    "CURRENCY_RULE",
    "DATA_PASSAGE",
    "DEBT_RECON",
    "DEEP_DEBATE_BLOCK",
    "DIRECTIONS",
    "EDGE_RULES",
    "EVENT_COLUMNS",
    "EVENT_LANES",
    "EVENT_STATUS",
    "FORECAST_BLOCK",
    "LAYER1_FORECAST_BLOCK",
    "MAPS",
    "MAP_TEXT_RULE",
    "METHODS",
    "METHOD_MARK",
    "MODULE_NAMES",
    "MONEY",
    "NET_DEBT",
    "NO_MONEY",
    "OWNER_TABLES",
    "PEER_PACK_BLOCK",
    "PEER_READER_BLOCK",
    "PERIOD_REQUIRED_BLOCK",
    "PERIOD_TABLE_BLOCK",
    "POSTURES",
    "POSTURE_HEADING",
    "POST_BS",
    "PRESENCE_RULE",
    "PROSE_PASSAGES",
    "READER_PERSONA",
    "REGISTER_SCOPE",
    "REGISTER_SCOPE_MODULES",
    "ROUTING_RULES",
    "SOURCES_RULES",
    "STRESS_BLOCK",
    "TRANSPORT_RULES",
    "UPSTREAM_SCOPE_NOTE",
    "VOICE_RULES",
    "_APPENDIX",
    "_SCORE",
    "OwnerTable",
    "_and_list",
    "_charge_notes",
    "_chart_header",
    "_chart_route",
    "_net_debt_issues",
    "_none_rule",
    "_owner_tables",
    "_print_review",
    "_review_lines",
    "_selector",
    "chart_issues",
]

ROOT = Path(__file__).resolve().parents[3]
HTML_SUFFIXES = frozenset({".htm", ".html"})
# Converted to text pages, pinned as ``<name>.jsonl``: HTML filings and Word documents.
CONVERTED_SUFFIXES = HTML_SUFFIXES | {".docx"}
PAGE_CHARS = 3000  # cp-os's page for an HTML filing: eight pages per read is at most about 24 KB.
SOURCE_SUFFIXES = frozenset(
    {".pdf", ".htm", ".html", ".docx", ".txt", ".md", ".xlsx", ".csv", ".json", ".jsonl"}
)
NOT_ANALYTICAL = frozenset({"CP-MODEL", "CP-8"})  # In the presets; each has its own route.
FIRST_PAGES = 3  # Pages of each source kept for the offline document guess (page 1 is the cover).
Cover = tuple[str, tuple[str, ...]]  # A source's file name and its first pages.
MAX_OUTPUT_TOKENS = 32000  # What the retained live campaigns ran with.
# Anthropic spends thinking tokens out of the same limit: in tdg-proof-snapshot-opus-001 CP-4's
# 7,431 thinking tokens plus its handoff did not fit in 32,000, the turn stopped on max_tokens
# inside write_handoff and the module was lost. Documented model maximum 128,000
# (cases/pilot-fixes/limits.json); handoff.py bounds a request at 64,000.
ANTHROPIC_MAX_OUTPUT_TOKENS = 64000


def output_limit(config: str) -> int:
    """The output limit a launch asks of `config`; the per-call hold is priced from it too.
    The Copilot Anthropic config is not covered: its hold already uses the model maximum."""
    return (
        ANTHROPIC_MAX_OUTPUT_TOKENS
        if CONFIGS[config].provider == "anthropic"
        else MAX_OUTPUT_TOKENS
    )


# Report sections whose registered producer is the Model or nothing: the first module present in
# the run writes them. Everything else uses the section's registered producers. The order follows
# the routes the retained pathway reports actually published.
BLOCK_OWNERS: dict[str, tuple[str, ...]] = {
    "binding-limitations": ("CP-6",),
    "capital-structure": ("CP-4", "CP-3"),
    "compensation-preference": ("CP-3",),
    "covenant-levers": ("CP-4",),
    "credit-view": ("CP-2", "CP-3"),
    "distress-gate": ("CP-2A",),
    "ebitda-adjustments": ("CP-1D",),
    "funding-gap-lme": ("CP-3C", "CP-2G"),
    "historical-performance": ("CP-1D",),
    "instrument-decision": ("CP-3", "CP-6", "CP-4C"),
    "loan-hy-relative-value": ("CP-3",),
    "portfolio-fit": ("CP-3", "CP-6"),
    "portfolio-recommendation": ("CP-6",),
    "recommendation-portfolio-fit": ("CP-3",),
    "restructuring-paths": ("CP-4C",),
    "thesis-catalysts-challenge": ("CP-6",),
    "transaction-summary": ("CP-1A",),
    "watch-items": ("CP-1B",),
}
# CP-8 owns this section and compares two completed deliveries; a single run has nothing to compare.
SECOND_RUN_ONLY = "what-changed"


class LaunchRefused(ValueError):
    """The request cannot start; the message says what to change."""


def refuse_deactivated(pathway: str) -> None:
    """Refuse a new run of a deactivated pathway. The one refusal every launch entry point calls
    (the command line, the run-start summary and the inbox's submit); `prepare` and the readers of
    past runs do not, so retained runs and the pathway's instructions keep working."""
    if pathway in DEACTIVATED_PATHWAYS:
        raise LaunchRefused(DEACTIVATED_MESSAGE)


@dataclass(frozen=True)
class Prepared:
    directory: Path
    manifest: Path
    plan: HandoffPlan
    layout: MarkdownLayout
    ordered: tuple[str, ...]
    ignored: tuple[str, ...]  # Files in the folder that no module can read.
    omitted: tuple[str, ...]  # Pathway report sections this run does not produce.
    hold: Decimal  # What one call of the largest module counts against the cap while in flight.
    documents: tuple[dict[str, Any], ...] = ()  # Each pinned source's guessed kind (offline).
    expectations: tuple[Item, ...] = ()  # What the run is expected to do (offline forecast).
    prior: PriorRun | None = None  # The earlier run CP-8 compares with, when one is listed.
    changes: str = ""  # The one line the run records about that comparison.
    portfolio: PortfolioCheck = NOT_COLLECTED  # The portfolio workbook found and its checks.


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _html_page_rows(name: str, raw: bytes) -> bytes:
    """An HTML filing's or Word document's text as the page rows ``_pages`` reads, in cp-os's page
    size and headed by the file's identity. As raw bytes a filing is mostly markup and a Word file
    a ZIP archive. Empty when the file has no text."""
    word = name.lower().endswith(".docx")
    text = docx_text(raw) if word else convert_html(raw).text
    if not text.strip():
        return b""
    pages: list[str] = []
    page = f"{'Text' if word else 'Visible text'} of {name}, sha256 {_sha(raw)}.\n"
    for line in text.splitlines():
        # convert_html runs prose together on one line, so a line alone can exceed many pages.
        for piece in textwrap.wrap(line, PAGE_CHARS - 1, replace_whitespace=False):
            if len(page) + len(piece) + 1 > PAGE_CHARS:
                pages.append(page)
                page = ""
            page += piece + "\n"
    pages.append(page)
    rows = (json.dumps({"page": n, "text": body}) for n, body in enumerate(pages, 1))
    return "\n".join(rows).encode() + b"\n"


def _issuer_files(
    folder: Path, context: Path, directory: Path
) -> tuple[dict[str, HandoffInput], dict[str, bytes], tuple[str, ...], dict[str, Cover]]:
    """Every readable file in ``folder``, the converted texts to write, the files left out and each
    pinned source's name and first pages (for the offline document guess). A
    file a module could not read stops the launch here, because the same failure during a run
    would come after the module was marked as started and could not be resumed."""
    if not folder.is_dir():
        raise LaunchRefused(f"--sources {folder}: not a folder")
    pinned: dict[str, HandoffInput] = {}
    converted: dict[str, bytes] = {}
    ignored: list[str] = []
    origins: dict[str, str] = {}
    covers: dict[str, Cover] = {}
    for path in sorted(folder.rglob("*")):
        name = path.relative_to(folder).as_posix()
        parts = path.relative_to(folder).parts
        if any(part.startswith(".") for part in parts) or not path.is_file() or path == context:
            continue
        # "~$" marks Office's lock file beside a document someone has open.
        if path.suffix.lower() not in SOURCE_SUFFIXES or any(
            p.startswith(("_", "~$")) for p in parts
        ):
            ignored.append(name)
            continue
        raw = path.read_bytes()
        is_html = path.suffix.lower() in CONVERTED_SUFFIXES
        key = f"{name}.jsonl" if is_html else name
        if key in origins:  # An HTML filing's text is pinned as `<name>.jsonl`, a real file name.
            raise LaunchRefused(
                f"--sources: {origins[key]} and {name} would both be source {key}; "
                "rename or remove one"
            )
        origins[key] = name
        try:
            readable = _html_page_rows(name, raw) if is_html else raw
            pages = _pages(key, readable)
        except Exception as error:  # Any parser failure refuses, naming the file.
            raise LaunchRefused(f"--sources: cannot read {name}: {error}") from error
        if not any(page.strip() for page in pages):
            raise LaunchRefused(f"--sources: {name} has no extractable text (scanned image?)")
        covers[key] = (name, tuple(pages[:FIRST_PAGES]))
        if is_html:
            converted[f"source-text/{key}"] = readable
            pinned[key] = HandoffInput(path=f"source-text/{key}", sha256=_sha(readable))
        else:
            pinned[key] = HandoffInput(path=os.path.relpath(path, directory), sha256=_sha(raw))
    if not pinned:
        raise LaunchRefused(f"--sources {folder}: no readable issuer file")
    return pinned, converted, tuple(ignored), covers


@dataclass(frozen=True)
class Reading:
    documents: tuple[dict[str, Any], ...]  # Each pinned source's guess, as Prepared.documents.
    ignored: tuple[str, ...]  # Names the launcher skips without reading.


def _documents(
    covers: dict[str, Any],
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    """Each source's guess, and the same guesses as ``Prepared.documents`` rows."""
    guesses = {key: guess_kind(name, pages) for key, (name, pages) in covers.items()}
    rows = tuple(
        {
            "source": key,
            "kind": g.kind,
            "signal": g.signal,
            "executed": g.executed,
            "period_end": g.period_end,
        }
        for key, g in guesses.items()
    )
    return guesses, rows


def _portfolio_files(pinned: Mapping[str, HandoffInput], folder: Path) -> dict[str, bytes]:
    """The bytes of each pinned `.xlsx` and `.csv` source (its name is its path in the issuer
    folder), as pinned: a file changed since it was hashed refuses the launch rather than be
    checked in a state the run would not read."""
    found: dict[str, bytes] = {}
    for name, pin in pinned.items():
        if name.lower().endswith((".xlsx", ".csv")):
            raw = (folder / name).read_bytes()
            if _sha(raw) != pin.sha256:
                raise LaunchRefused(f"--sources: {name} changed while it was read; try again")
            found[name] = raw
    return found


def read_documents(folder: Path) -> Reading:
    """What the launcher makes of each file in ``folder``, before any context exists. Writes
    nothing; refuses a folder or file the launcher would refuse, with the launcher's own text."""
    source = Path(folder).expanduser().resolve()
    _, _, ignored, covers = _issuer_files(source, source.parent / ".no-context", source.parent)
    return Reading(_documents(covers)[1], ignored)


HTML_MODEL_SCOPE = "The HTML Model and calculation JSON are not published by this launcher."
LAYER1_FORECAST_SCOPE = (
    "The HTML Model is not published by this launcher. A forecast table is published with the "
    "issuer report in the library when the CP-1 handoff's run-rate inputs block validates; it "
    "comes from the financial foundation's run-rate figures, with no cases and no stress, and "
    "is better with CP-2G. Python computes its figures from the inputs the handoff states, and "
    "the inputs are not independently reviewed."
)
FORECAST_SCOPE = (
    "The HTML Model is not published by this launcher. A forecast table is published with the "
    "issuer report in the library when the CP-2G handoff's inputs block validates; Python "
    "computes its figures from the inputs the handoff states, and the inputs are not "
    "independently reviewed."
)


def _layout(
    run: Run, ordered: tuple[str, ...], aliases: tuple[str, ...], config: str, *, forecast: bool
) -> tuple[MarkdownLayout, tuple[str, ...]]:
    preset = next(p for p in pathways() if p.id == run.pathway)
    routes: list[MarkdownRoute] = []
    omitted: list[str] = []
    for block_id in preset.blocks:
        spec = _spec_of(block_id)
        owners = BLOCK_OWNERS.get(block_id, spec.producers)
        owner = next((m for m in owners if m in ordered), None)
        if owner == "CP-1" and block_id in CHART_BLOCKS:
            routes += [_chart_route(block_id, figure) for figure in STRIP_FIGURES[block_id]]
            continue
        if block_id == SECOND_RUN_ONLY:  # CP-8's handoff is delivered whole, not routed here
            if "CP-8" not in ordered:
                omitted.append(block_id)
            continue
        if owner is None or spec.kind == "chart":
            omitted.append(block_id)
            continue
        routes.append(
            MarkdownRoute(
                module_id=owner,
                heading=spec.title,
                kind="prose" if spec.kind == "prose" else "table",
                block_id=block_id,
            )
        )
    if not routes:
        raise LaunchRefused(
            f"--modules {' '.join(ordered)}: fills no {preset.title} report section"
        )
    scope = (
        f"User-launched {preset.title} run for {run.issuer_name} as of {run.as_of}, using {config} "
        "on the selected issuer folder. Automated checks cover handoff structure, issuer and date "
        "anchors, source and upstream references and issuer-report section selectors; analytical "
        "accuracy has not been independently reviewed. "
        + (
            HTML_MODEL_SCOPE
            if not forecast
            else FORECAST_SCOPE
            if "CP-2G" in ordered
            else LAYER1_FORECAST_SCOPE
        )
        + f" Sections not produced: {', '.join(omitted) or 'none'}."
        + (DELIVERED_WHOLE if "CP-8" in ordered else "")
    )
    layout = MarkdownLayout(
        blocks=tuple(dict.fromkeys(r.block_id for r in routes)),
        routes=tuple(routes),
        scope=scope,
        title=f"{run.issuer_name} — {preset.title}",
        issuer_aliases=aliases,
        front=(),
    )
    return layout, tuple(omitted)


def method_sections(module: str) -> list[tuple[str, str]]:
    """The selected method a module is sent, as (name, text) sections in instruction order.

    Each section is written into the instructions under a ``=== name sha256 hex ===`` heading, so
    a run's retained instructions record exactly which method it ran.
    """
    return [(name, _method_file(name)) for name in METHODS[module]]


def _method_file(name: str) -> str:
    """A method file's text; `path § heading` gives the one heading line of any level
    `#{2,6} heading` and everything under it, to the next heading of the same or higher level."""
    path, _, heading = name.partition(" § ")
    text = (ROOT / path).read_text(encoding="utf-8")
    if not heading:
        return text
    found = list(re.finditer(rf"^(#{{2,6}}) {re.escape(heading)}\n", text, re.MULTILINE))
    if len(found) != 1:
        raise ValueError(f"{path}: expected one heading {heading!r}, found {len(found)}")
    start, level = found[0].start(), len(found[0][1])
    after = re.compile(rf"^#{{1,{level}}} ", re.MULTILINE).search(text, found[0].end())
    return text[start:] if after is None else text[start : after.start()]


def method_heading(name: str, text: str) -> str:
    """The heading that names one method section and the sha256 of its text."""
    return f"=== {name} sha256 {_sha(text.encode())} ==="


def method_text(module: str) -> str:
    """The method block exactly as a module's instructions carry it."""
    return "\n\n".join(
        f"{method_heading(name, text)}\n{text}" for name, text in method_sections(module)
    )


def register_scope(module: str) -> str:
    """The registers a module's scope section says not to write, as the section names them
    (`<id> <title>; <id> <title>`)."""
    section = dict(method_sections(module))[f"{REGISTER_SCOPE} § {module}"]
    return section.partition("do not write ")[2].partition(". Any figure")[0]


# The routing registers each module's scope section names (ROUTING_RULES tells it not to write
# them); the presence check never requires them. Per module: ids collide across modules.
ROUTING_REGISTERS = (
    ("CP-0", ("T7", "T8")),
    ("CP-1A", ("T2D.10", "downstream_readiness")),
    ("CP-2A", ("T2B.8", "T5.6")),
)
_REQUIRED_KEY = re.compile(r"^(\s*)- \*\*required_register_ids\*\*:(.*)$")
_REGISTER_ID = re.compile(r"[A-Za-z]\w*(?:\.\w+)*")
_MISSING_REGISTERS = (
    "Missing registers: {ids}. The method requires each of them and CP-OS does not cut them. "
    "Write each as its own register: a `###` heading that starts with its id (`### {first} - "
    "<title>`, the id may be in bold or backticks) or a `<!-- table-id: ... {first} -->` tag above "
    "its table. A register with nothing to "
    "report is still written, with one row `Not supplied: <reason>` (or the method's own "
    "placeholder row), never left out. A module that stops at its gate says so with "
    "`module_status: Blocked` in the front matter and writes the gate register only; it is not "
    "asked for the others."
)


def _listed_ids(lines: list[str]) -> list[str]:
    """The ids of every `required_register_ids` entry in a method file, in order (the entry is
    one `;` line or, as `structured below`, the deeper bullets under it)."""
    ids: list[str] = []
    for number, line in enumerate(lines):
        key = _REQUIRED_KEY.match(line)
        if not key:
            continue
        body = [key[2]]
        for later in lines[number + 1 :]:
            if not later.lstrip().startswith("- ") or len(later) - len(later.lstrip()) <= len(
                key[1]
            ):
                break
            body.append(later.lstrip()[2:])
        ids += [p.strip() for p in ";".join(body).split(";")]
    return [i for i in ids if _REGISTER_ID.fullmatch(i) and i != "none"]


@functools.cache
def required_registers(module: str) -> tuple[str, ...]:
    """The registers a module's handoff must carry: the method's `required_register_ids` (CP-0:
    less what CP0_BLOCK says the launcher did), less the module's scope section and the routing
    registers. Derived from the method text the module is sent; empty outside the ten modules."""
    if module not in REGISTER_SCOPE_MODULES:
        return ()
    listed: list[str] = []
    for name, text in method_sections(module):
        if not name.startswith(REGISTER_SCOPE):
            listed += _listed_ids(text.split("\n"))
    out = {part.strip().split(" ")[0] for part in register_scope(module).split(";")}
    if module == "CP-0":
        launcher = re.search(r"Do not write the registers ([^.]*)\.", CP0_BLOCK)
        if launcher is None:
            raise ValueError("CP0_BLOCK no longer says which registers the launcher made")
        out |= set(re.findall(r"\bP\d+\b", launcher[1]))
    out |= set(dict(ROUTING_REGISTERS).get(module, ()))
    return tuple(dict.fromkeys(i for i in listed if i not in out))


def _blocked_at_gate(text: str) -> bool:
    """`module_status: Blocked` in the front matter: the method's own stop ("Module Status =
    Blocked, STOP"); the retained CP-4 handoff writes its source gate and nothing else. One rule
    with the method-script checks (`method_scripts.blocked`)."""
    return method_scripts.blocked(text)


def _has_register(text: str, ident: str) -> bool:
    """A `###` heading that starts with the id (optionally after a number such as `1.`, and the id
    in bold or backticks), or with a list of ids that includes it, or a `<!-- table-id: ... -->` tag
    whose last part is the id. Each id in the list is id-shaped (a dotted id, a bare `T1`/`P3`, a
    snake_case slug): a prose word before it makes the heading another register's (`Table T2.1:`
    stays refused). An id in a table cell or mid-heading is a citation, not the register."""
    wrap = r"(?:\*\*|`)?"
    token = (
        r"(?:[A-Z]+\d\w*(?:\.\w+)*|[A-Z][A-Za-z]*(?:\.\w+)+|[a-z]+(?:_[a-z]+)+)"  # id-shaped only
    )
    lead = rf"{wrap}{token}{wrap}(?:\s*[,&/]\s*|\s+and\s+)"
    heading = rf"^#{{2,6}} (?:\d+[.)] )?(?:{lead})*{wrap}{re.escape(ident)}(?!\w|\.\d)"
    tag = rf"^<!-- table-id: (?:\S*\.)?{re.escape(ident)} -->\s*$"
    return any(re.search(p, text, re.MULTILINE) for p in (tag, heading))


def register_issues(module: str, text: str) -> tuple[str, ...]:
    """One issue naming every in-scope required register the handoff lacks; none for a module
    outside the ten or one blocked at its gate. A register's body is not judged."""
    required = required_registers(module)
    if not required or _blocked_at_gate(text):
        return ()
    missing = [i for i in required if not _has_register(text, i)]
    if not missing:
        return ()
    return (_MISSING_REGISTERS.format(ids=", ".join(missing), first=missing[0]),)


_POSTURE = re.compile(rf"Final Sizing Posture: (?:{'|'.join(map(re.escape, POSTURES))})(?![\w-])")


def posture_issues(module: str, text: str) -> tuple[str, ...]:
    """CP-6's portfolio debate decision (`CP6A_BLOCK`): a `### Portfolio posture` section under
    `## Findings` whose first sentence is the method's `Final Sizing Posture: <posture>`
    formulation with one of its six postures, read with Markdown emphasis removed. None for any
    other module or a blocked CP-6."""
    if module != "CP-6" or _blocked_at_gate(text):
        return ()
    lines = findings_sentences(text, POSTURE_HEADING)
    if not lines:
        missing = (
            "Write the portfolio debate's posture, binding constraint and memo under "
            f"`### {POSTURE_HEADING}` in `## Findings`, after `### Limitations`."
        )
        return (missing,)
    if not _POSTURE.match(re.sub(r"[*_`]", "", lines[0]).lstrip()):  # emphasis is not wording
        unstated = (
            f"Start `### {POSTURE_HEADING}` with the method's formulation `Final Sizing Posture: "
            f"<posture>.`, the posture one of {', '.join(POSTURES)}."
        )
        return (unstated,)
    return ()


def upstream_scope_note(ordered: Sequence[str]) -> str:
    """What CP-5 is told about the handoffs it audits: the registers each module of the run planned
    before it was told not to write. Empty when the run has no CP-5 or none of them has a scope
    section."""
    if "CP-5" not in ordered:
        return ""
    upstream = ordered[: ordered.index("CP-5")]
    lines = [f"- {m}: {register_scope(m)}." for m in upstream if m in REGISTER_SCOPE_MODULES]
    return UPSTREAM_SCOPE_NOTE.format(lines="\n".join(lines)) if lines else ""


def _instructions(
    run: Run,
    module: str,
    routes: Sequence[MarkdownRoute],
    *,
    run_type: str,  # Plan 3 (Primary scope) reads these two; no instruction byte uses them yet.
    legal_documents: str,
) -> bytes:
    asked: list[MarkdownRoute | OwnerTable] = [r for r in routes if r.module_id == module]
    # A report selector named like a reader passage (CP-2's `Key findings`) is that passage: it
    # is written once, as the passage, or the section would repeat and delivery would refuse it.
    named = [r.heading for r in asked if r.heading in READER_HEADINGS]
    asked = [r for r in asked if r.heading not in named]
    selectors = "\n".join(_selector(r) for r in (*asked, *_owner_tables(module, routes)))
    if named:
        selectors += (
            f"\n- {', '.join(f'`### {h}`' for h in named)}: the reader passage of that name is "
            "this report selector; write it once, not twice, and write it even if this module is "
            "blocked (state that nothing is assessable)."
        )
    first, shared, rest = selectors.partition(EDGE_RULES)
    selectors = first + shared + rest.replace(EDGE_RULES, "")
    method = method_text(module)
    return (
        f"# {module} for {run.issuer_name} ({run.issuer_id}), as of {run.as_of}\n\n"
        f"Pathway: {run.pathway}. Run the complete selected method below on this issuer's supplied "
        "sources and the current handoffs CP-OS supplies. Markdown transport overrides the "
        "method's JSON, typed-ID, connector and fact-chip mechanics; keep every analytical duty. "
        "Any issuer named in the method is an example, never evidence for this run.\n\n"
        f"Source `{CONTEXT_SOURCE_ID}` holds the user's dated settings and inputs for this run. It "
        "is not issuer evidence. Do not treat a value it leaves blank as zero.\n\n"
        "Find what this module needs with search_source, then read only those pages. Do not read "
        "whole filings: reads stop once this module's context is full.\n\n"
        "Use calculate for all new arithmetic. Keep exact amounts, units, currencies, periods, "
        "source locators and limitations. Absent evidence stays an explicit gap.\n\n"
        + TRANSPORT_RULES
        + ROUTING_RULES
        + (PRESENCE_RULE if module in REGISTER_SCOPE_MODULES else "")
        + "A handoff is rejected unless it does all of this:\n"
        f"- name {run.issuer_name} in `## Request`, and state the as-of date {run.as_of} there;\n"
        "- list each issuer source it relied on in `## Sources`, naming the exact file and its "
        "sha256;\n"
        "- list each supplied handoff in `## Sources`, with its module and exact sha256.\n\n"
        + SOURCES_RULES
        + READER_PERSONA
        + (DATA_PASSAGE if module in DATA_MODULES else PROSE_PASSAGES)
        + (APPENDIX_HEADING_NOTE if _APPENDIX in METHODS[module] else "")
        + VOICE_RULES
        + (CHART_NOTE_RULE if "### Chart data:" in selectors else "")
        + (MAP_TEXT_RULE if "### Map:" in selectors else "")
        + (CONFIDENCE_RULE if _SCORE in METHODS[module] else "")
        + (
            "Report selectors, each exactly once inside `## Findings`, using these exact "
            f"headings. They place content in the report and are not analytical completion:\n"
            f"{selectors}\n\n"
            if selectors
            else ""
        )
        + f"{METHOD_MARK}{method}\n"
    ).encode()


def pathway_modules(settings: RunContext) -> tuple[str, ...]:
    """A pathway's analytical modules: its preset less the modules that have their own route.
    Owner, 2026-11-11: CP-DR and CP-2E are in every preset except ``short_snapshot`` and
    ``lite_credit_assessment``, which have neither (CP-1C needs CP-DR's peers), so the
    context's peer source no longer adds a module. Explicit --modules are run as given."""
    return tuple(m for m in PATHWAY_MODULES[settings.run.pathway] if m not in NOT_ANALYTICAL)


UNAVAILABLE = "the earlier run named at approval is no longer available"
_RUN_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
NO_PRIOR = "none"  # `--prior none`: the approval named no earlier run ("first run")
# Request bytes CP-8's first request holds beside the instructions and the inlined handoffs: the
# run record, the module roles, the tool list and the framing (an allowance, measured on no run).
REQUEST_ALLOWANCE = 16_384


def _held_manifest(directory: Path) -> HandoffPlan | None:
    """The manifest a run folder already holds, or None when there is none or it cannot be read
    (the request built from the new inputs then differs from it and is refused)."""
    manifest = directory / "workflow.json"
    if not manifest.is_file():
        return None
    try:
        return HandoffPlan.model_validate_json(manifest.read_bytes())
    except ValueError:
        return None


def _cp8_hold(  # noqa: PLR0913 - the sizes of CP-8's first request
    config: str,
    cap: Decimal,
    instructions: int,
    ordered: Sequence[str],
    earlier: Mapping[str, bytes],
    held: HandoffPlan | None,
) -> Decimal:
    """What CP-8's first call counts against the cap, on its estimated first request (the loop's
    own bound: the request's bytes over `BYTES_PER_TOKEN_BOUND`, plus its overhead). A call that
    does not fit leaves CP-8 out of a new run (`_Cp8DoesNotFit`) and refuses a resumed one."""
    size = _cp8_request_bytes(instructions, ordered, earlier)
    words = (
        f"CP-8's first request (about {size:,} request bytes, estimated from the earlier run's "
        "handoff sizes because this run's are not written yet)"
    )
    try:
        hold = request_reservation_usd(
            price_of(config),
            -(-size // BYTES_PER_TOKEN_BOUND) + REQUEST_OVERHEAD,
            output_limit(config),
        )
    except ContextTooLong as error:
        problem = f"{words} is over the model's context ({error})"
    else:
        if hold <= cap:
            return hold
        problem = f"{words} would hold up to USD {hold:.2f}, over the cap USD {cap}"
    if held is not None:
        raise LaunchRefused(f"--cap: {problem}")
    raise _Cp8DoesNotFit(f"changes: not compared: {problem}; the run is planned without CP-8")


def _earlier_run(  # noqa: PLR0913 - the identity of the run and the approved choice
    directory: Path,
    workspace: Path | None,
    held: HandoffPlan | None,
    *,
    issuer_id: str,
    issuer_name: str,
    case_kind: str,
    pathway: str,
    as_of: str,
    choice: str | None = None,
) -> tuple[PriorRun | None, str | None, dict[str, bytes]]:
    """The earlier run CP-8 compares with, the line recorded about it, and the pinned copies of its
    handoffs to write (source name -> bytes).

    ``choice`` is the approval's: ``NO_PRIOR`` ("first run"), the folder name of the run it named,
    or None (a launch from the command line, which searches). A named run is used exactly, if it is
    still listed and passes the same tests as a searched one; otherwise the run proceeds without
    CP-8 and says so.

    ``held`` is the manifest the run folder already holds: it keeps what that manifest records, so
    a newer completed run appearing since cannot change it and get the relaunch refused; the copies
    are read back from the folder and checked against their pins. A manifest this launcher cannot
    read is not resumed here: the request built below then differs from it and is refused."""
    if held is not None:
        copies = {}
        for name in () if held.prior is None else prior_sources(held.prior):
            raw = (directory / held.sources[name].path).read_bytes()
            if _sha(raw) != held.sources[name].sha256:
                raise LaunchRefused(f"--out {directory}: the pinned earlier handoff {name} changed")
            copies[name] = raw
        return held.prior, held.changes_note, copies
    if (directory / "workflow.json").is_file():
        return None, None, {}
    if workspace is None:
        return None, "changes: not compared: the run folder is not inside a runs folder", {}
    if choice == NO_PRIOR:
        return None, describe(None), {}
    skipped: list[str] = []
    found = find_prior(
        workspace,
        folder=directory.name,
        issuer_id=issuer_id,
        issuer_name=issuer_name,
        case_kind=case_kind,
        pathway=pathway,
        as_of=as_of,
        only=choice,
        skipped=skipped,
    )
    why = f" (not used: {'; '.join(skipped)})" if skipped else ""
    if found is None:
        head = f"changes: not compared: {UNAVAILABLE}" if choice is not None else describe(None)
        return None, head + why, {}
    prior, handoffs = found
    return (
        prior,
        describe(prior) + why,
        {f"{PRIOR_PREFIX}{m}.md": raw for m, raw in handoffs.items()},
    )


def _cap_differs(held: HandoffPlan | None, request: HandoffPlan) -> str:
    """Why a run folder's request differs, when its cap is the cause: a folder started at another
    cap (the USD 20 before per-pathway caps) resumes only at that cap, never at a higher one."""
    if held is None or held.provider_cap_usd == request.provider_cap_usd:
        return ""
    return (
        f" (the folder was started at a cap of USD {held.provider_cap_usd}, not USD "
        f"{request.provider_cap_usd}; resume it with --cap {held.provider_cap_usd})"
    )


class _Cp8DoesNotFit(Exception):
    """CP-8's first request would hold more than the cap; ``prepare`` plans the run without it."""

    def __init__(self, note: str) -> None:
        super().__init__(note)
        self.note = note


def _cp8_request_bytes(
    instructions: int, ordered: Sequence[str], earlier: Mapping[str, bytes]
) -> int:
    """An estimate of the bytes of CP-8's first request.

    The loop inlines every handoff CP-8 is sent (this run's accepted ones, as JSON text) in its
    first request, and they are not written yet when the cap is checked. The earlier run's handoff
    of the same module stands in for each (the mean of the earlier handoffs for a module that run
    did not have); the instructions, the module roles and the tool list are `REQUEST_ALLOWANCE`."""
    sizes = {
        name: len(dump_json({"markdown": raw.decode("utf-8", "replace")}))
        for name, raw in earlier.items()
    }
    mean = sum(sizes.values()) // len(sizes) if sizes else 0
    inlined = sum(sizes.get(f"{PRIOR_PREFIX}{m}.md", mean) for m in ordered if m != "CP-8")
    return instructions + inlined + REQUEST_ALLOWANCE


def prepare(  # noqa: PLR0913 - one keyword per run setting
    context: Path,
    sources: Path,
    out: Path | None,
    *,
    config: str,
    cap: Decimal | str,
    modules: Sequence[str] | None = None,
    web_search: bool = False,
    workspace: Path | None = None,
    prior: str | None = None,
) -> Prepared:
    """Check everything and write the manifest and instructions; a refusal writes nothing.

    ``prior`` is the approval's choice of earlier run (`_earlier_run`): ``NO_PRIOR``, the folder
    name of the run the approval named, or None to search. When CP-8's own first request would not
    fit the cap (`_cp8_request_bytes`), the run is planned without CP-8 and the note says so.

    ``workspace`` is where earlier runs are looked for (``<workspace>/runs``): by default the folder
    holding the ``runs`` folder the run folder is in. When the library lists an earlier run of the
    same issuer and pathway (`deploy_workflow.changes.find_prior`), CP-8 is planned last and that
    run's handoffs are pinned for it alone; a run folder that already holds a manifest keeps the
    pins that manifest records.

    ``web_search`` is whether the run's ruling lists ``web-search``: the research module's calls
    then hold the search fee too, as the live loop holds it, so the cap is checked against the
    same hold."""
    if prior is not None and prior != NO_PRIOR and not _RUN_NAME.fullmatch(prior):
        raise LaunchRefused(f"--prior: {prior!r} is neither `none` nor the name of a run folder")

    def attempt(left_out: str | None) -> Prepared:
        return _prepare(
            context,
            sources,
            out,
            config=config,
            cap=cap,
            modules=modules,
            web_search=web_search,
            workspace=workspace,
            choice=prior,
            left_out=left_out,
        )

    try:
        return attempt(None)
    except _Cp8DoesNotFit as unfit:
        return attempt(unfit.note)


def _prepare(  # noqa: PLR0913, PLR0915 - `prepare`'s body: one keyword per setting
    context: Path,
    sources: Path,
    out: Path | None,
    *,
    config: str,
    cap: Decimal | str,
    modules: Sequence[str] | None,
    web_search: bool,
    workspace: Path | None,
    choice: str | None,
    left_out: str | None,
) -> Prepared:
    """`prepare`; ``left_out`` is the note of a run planned without CP-8 because its call did not
    fit the cap."""
    context_path = Path(context).expanduser().resolve()
    folder = Path(sources).expanduser().resolve()
    raw_context = context_path.read_bytes()
    settings = load_context(raw_context)
    chosen = tuple(modules) if modules else tuple(PATHWAY_MODULES[settings.run.pathway])
    # CP-MODEL means "publish the forecast" (owner, 2026-11-11); it makes no model call.
    model_wanted = "CP-MODEL" in chosen
    requested = tuple(m for m in (modules or pathway_modules(settings)) if m != "CP-MODEL")
    if "CP-8" in requested:
        raise LaunchRefused(
            "--modules: CP-8 is planned automatically when an earlier run of this issuer and "
            "pathway is listed; it cannot be selected"
        )
    run_id = f"{settings.identity.issuer_id}-{settings.run.as_of}-{settings.run.pathway}-{config}"
    directory = (ROOT / "runs" / run_id if out is None else Path(out)).expanduser().resolve()
    if directory.is_relative_to(folder):
        raise LaunchRefused(f"--out {directory}: must be outside the issuer folder")
    held = _held_manifest(directory)
    prior, note, earlier = _earlier_run(
        directory,
        workspace if workspace is not None else workspace_of(directory),
        held,
        issuer_id=settings.identity.issuer_id,
        issuer_name=settings.identity.issuer_name,
        case_kind=settings.run.case_kind,
        pathway=settings.run.pathway,
        as_of=settings.run.as_of,
        choice=choice,
    )
    if left_out is not None:
        prior, note, earlier = None, left_out, {}
    # How the modules were chosen decides whether a later run may compare with this one; a run
    # folder that holds a manifest keeps what it records (an older one records nothing).
    preset = set(PATHWAY_MODULES[settings.run.pathway]) - {"CP-8"}
    selection = (
        held.selection
        if held is not None
        else "explicit"
        if modules and set(modules) != preset
        else "preset"
    )
    # CP-8 follows every other module, so it is the last of the plan.
    requested = (*requested, *(("CP-8",) if prior is not None else ()))
    planned = plan((*requested, *(("CP-MODEL",) if model_wanted else ())))  # Refuses unknowns.
    ordered = tuple(m for m in planned if m != "CP-MODEL")
    requested = requested or ordered
    if unknown := [m for m in ordered if m not in METHODS]:
        raise LaunchRefused(f"--modules: no launchable method for {', '.join(unknown)}")
    run = Run(
        run_id=run_id,
        issuer_id=settings.identity.issuer_id,
        issuer_name=settings.identity.issuer_name,
        as_of=date.fromisoformat(settings.run.as_of),
        case_kind=settings.run.case_kind,
        pathway=settings.run.pathway,
        requested_modules=requested,
    )
    pinned, converted, ignored, covers = _issuer_files(folder, context_path, directory)
    if clash := [name for name in pinned if name.startswith(PRIOR_PREFIX)]:
        raise LaunchRefused(
            f"--sources: {', '.join(clash)} would be taken for an earlier run's handoff; rename it"
        )
    portfolio = portfolio_check(
        _portfolio_files(pinned, folder),
        pathway=settings.run.pathway,
        declared=settings.attachments.portfolio_workbook,
        run_date=run.as_of,
    )
    aliases = tuple(a for a in settings.identity.aliases if a.strip())
    forecast = "CP-1" in ordered and (model_wanted or "CP-2G" in ordered)
    layout, omitted = _layout(run, ordered, aliases, config, forecast=forecast)
    texts = {
        m: _instructions(
            run,
            m,
            layout.routes,
            run_type=settings.run.run_type,
            legal_documents=settings.attachments.legal_documents,
        )
        for m in ordered
    }
    options = settings.module_options
    peer_pack = settings.valuation.peer_source == "cp_dr_public" and {"CP-DR", "CP-1C"} <= set(
        ordered
    )
    for module, block, wanted in (
        ("CP-2G", FORECAST_BLOCK, forecast),
        ("CP-1", PERIOD_TABLE_BLOCK, forecast),
        ("CP-1", PERIOD_REQUIRED_BLOCK, not forecast),
        ("CP-1", CP1_CHECK_BLOCK, True),
        ("CP-1", LAYER1_FORECAST_BLOCK, forecast and "CP-2G" not in ordered),
        ("CP-0", CP0_BLOCK, True),
        ("CP-5", upstream_scope_note(ordered), True),
        ("CP-2A", STRESS_BLOCK, True),
        ("CP-DR", PEER_PACK_BLOCK, peer_pack),
        ("CP-1C", PEER_READER_BLOCK, peer_pack),
        (
            "CP-3",
            CP3_MODE_BLOCK.format(label=CP3_MODE_LABELS[options.cp3_mode])
            if options.cp3_mode
            else "",
            bool(options.cp3_mode),
        ),
        ("CP-6", CP6A_BLOCK, True),
        ("CP-6", DEEP_DEBATE_BLOCK, options.cp6_deep_debate),
        *((m, note, True) for m, note in method_scripts.NOTES.items()),
        *(
            (told, text, bool(text))
            for told in ("CP-0", "CP-3", "CP-6")
            for text in (portfolio_instructions(portfolio, told, run.as_of),)
        ),
        (
            "CP-8",
            CP8_BLOCK.format(prior=describe_run(prior)) if prior is not None else "",
            prior is not None,
        ),
    ):
        if wanted and module in texts:
            head, mark, method = texts[module].partition(METHOD_MARK.encode())
            texts[module] = head + block.encode() + mark + method
    guesses, documents = _documents(covers)
    items = expectations(
        ordered,
        tuple(guesses.values()),
        settings,
        edges_for(ordered),
        omitted=omitted,
        portfolio=portfolio,
    )
    request = HandoffPlan(
        run=run,
        sources={
            **pinned,
            CONTEXT_SOURCE_ID: HandoffInput(
                path=os.path.relpath(context_path, directory), sha256=_sha(raw_context)
            ),
            **{
                name: HandoffInput(path=path, sha256=_sha(earlier[name]))
                for name, path in (prior_sources(prior) if prior is not None else {}).items()
            },
        },
        instructions={
            m: HandoffInput(path=f"instructions/{m}.md", sha256=_sha(text))
            for m, text in texts.items()
        },
        layout=layout,
        publish_forecast=forecast,
        prior=prior,
        changes_note=note,
        selection=selection,
        execution="live-provider",
        max_attempts=1,
        provider_cap_usd=Decimal(cap),
    )
    # The loop's own bound for the first call of the largest module; later calls hold more.
    hold = max(
        request_reservation_usd(price_of(config), len(text) + 4096, output_limit(config))
        + (
            web_search_usd(WEB_SEARCH_CALLS_PER_TURN)
            if web_search_offered(web_search, module, settings.run.case_kind)
            else 0
        )
        for module, text in texts.items()
        if module != "CP-8"
    )
    if request.provider_cap_usd < hold:
        raise LaunchRefused(f"--cap {cap}: one {config} call holds up to USD {hold:.2f}")
    if prior is not None:
        hold = max(
            hold,
            _cp8_hold(config, request.provider_cap_usd, len(texts["CP-8"]), ordered, earlier, held),
        )
    raw = request.model_dump_json(indent=2).encode()
    manifest = directory / "workflow.json"
    if manifest.exists() and manifest.read_bytes() != raw:
        raise LaunchRefused(
            f"--out {directory}: holds a different request{_cap_differs(held, request)}; "
            "choose a new --out"
        )
    for relative, content in (*converted.items(), *earlier.items()):
        _put(directory / relative, content)
    for module, text in texts.items():
        _put(directory / "instructions" / f"{module}.md", text)
    _put(manifest, raw)
    return Prepared(
        directory,
        manifest,
        request,
        layout,
        ordered,
        ignored,
        omitted,
        hold,
        documents,
        tuple(items),
        prior,
        note or "",
        portfolio,
    )


def without_for(ordered: Sequence[str], items: Sequence[Item]) -> dict[str, list[str]]:
    """For each declaration-based Will refuse module: itself and, transitively, every ordered module
    that requires it (a registry required dependency; optional and restricted consumers stay), in
    run order. An inherited Will refuse offers nothing: its producer does."""
    required = {m.module_id: set(m.required) for m in modules()}
    result: dict[str, list[str]] = {}
    for item in items:
        if item["outcome"] != "will_refuse" or item["inherited_from"] or item["scope"] == "run":
            continue
        removed = {item["scope"]}
        grew = True
        while grew:
            grew = False
            for module in ordered:
                if module not in removed and required.get(module, set()) & removed:
                    removed.add(module)
                    grew = True
        result[item["scope"]] = [m for m in ordered if m in removed]
    return result


def _owned_issues(module: str, routes: Sequence[MarkdownRoute], text: str) -> list[str]:
    """The tables a module is asked for beside its report routes, checked; for CP-1 also the net
    debt table's arithmetic."""
    money = money_unit(text)
    issues = [
        i for owned in _owner_tables(module, routes) for i in chart_issues(text, owned, money=money)
    ]
    return [*issues, *_net_debt_issues(text), *_cp1_issues(text)] if module == "CP-1" else issues


_FRONT_SCORE_KEY = re.compile(r"(confidence_score|confidence_band|qa_status)\s*:")


def _front_matter_score_issues(text: str) -> tuple[str, ...]:
    """The method's own front matter carries a score, band and QA status; the module states none
    (decision 9 of 2026-11-12: Python computes them). Only those three keys in the block that
    opens the handoff (`---` on its first line to the next `---`) are read, nothing in the body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ()
    issues = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if found := _FRONT_SCORE_KEY.match(line):
            issues.append(
                f"Remove `{found[1]}` from the front matter: a module states no confidence "
                "score, band or QA status."
            )
    return tuple(issues)


def checker(layout: MarkdownLayout) -> Check:
    """Anchors and report selectors for one module's answer, so a defect is repaired inside the
    module's loop rather than found at delivery after every module was paid for."""

    def check(task: HandoffTask, raw: bytes) -> tuple[str, ...]:
        text = raw.decode("utf-8")
        issues = []
        if task.run.as_of.isoformat() not in text:
            issues.append(f"State the as-of date {task.run.as_of} in ## Request.")
        for name, handoff in task.handoffs.items():
            if _sha(handoff) not in text:
                issues.append(f"List the current {name} handoff with its exact sha256.")
        evidence = {_sha(v) for k, v in task.sources.items() if k != CONTEXT_SOURCE_ID}
        if not any(digest in text for digest in evidence):
            issues.append("List each issuer source relied on with its exact name and sha256.")
        issues += prose_issues(text, {m: v.decode("utf-8") for m, v in task.accepted.items()})
        issues += figure_issues(text)
        issues += _front_matter_score_issues(text)
        if task.module_id == "CP-L10":
            issues += _key_figure_issues(task, text)
        if task.module_id == "CP-8":
            sent = [*task.handoffs.values()] + [
                raw for name, raw in task.sources.items() if name.startswith(PRIOR_PREFIX)
            ]
            issues += cp8_issues(
                text, json.loads(task.sources[PACK_NAME]), [item.decode("utf-8") for item in sent]
            )
        routes = tuple(r for r in layout.routes if r.module_id == task.module_id)
        faults = table_faults(text)  # every malformed table, so one review names them all
        try:
            if routes:
                own = layout.model_copy(
                    update={
                        "blocks": tuple(dict.fromkeys(r.block_id for r in routes)),
                        "routes": routes,
                        "front": tuple(r for r in layout.front if r.module_id == task.module_id),
                    }
                )
                with tempfile.TemporaryDirectory() as temporary:
                    (Path(temporary) / "answer.md").write_bytes(raw)
                    answer = HandoffInput(path="answer.md", sha256=_sha(raw))
                    delivery = DeliveryRequest(
                        run=task.run, handoffs={task.module_id: answer}, layout=own
                    )
                    markdown_files(delivery, Path(temporary))
            else:
                require_issuer(task.run, layout.issuer_aliases, task.module_id, text.splitlines())
                literal_module(task.module_id, raw)
        except ValueError as error:
            # its table error, listed below: the same text, or with the scan's hint after it
            listed = any(f in (str(error), str(error) + BLANK_SPLITS) for f in faults)
            if not listed:
                issues.append(f"The report adapter refused this handoff: {error}")
        issues += faults
        for route in routes:
            if route.kind == "chart":
                issues += chart_issues(text, route, money=money_unit(text))
        issues += _owned_issues(task.module_id, routes, text)
        issues += register_issues(task.module_id, text)
        issues += posture_issues(task.module_id, text)
        upstream = method_scripts.upstream_texts(task.handoffs)  # a copied figure is compared
        issues += method_scripts.issues(task.module_id, text, upstream)
        issues += method_scripts.shared_issues(task.module_id, text)  # `completeness_check.py`
        return (*issues, *_forecast_issues(task, text))

    return check


def _key_figure_issues(task: HandoffTask, text: str) -> tuple[str, ...]:
    """CP-L10's Key figures against the CP-1 handoff it was sent; none sent is a refusal."""
    if "CP-1" not in task.handoffs:
        missing = "Key figures cannot be checked against the financial foundation: no CP-1 handoff."
        return (missing,)
    return key_figures_issues(text, task.handoffs["CP-1"].decode("utf-8"))


# The refusals about a facility: the two `parse` raises itself (`_check_facilities`, `_to_millions`)
# and a schema refusal whose own first path is `facilities` (or the unique-names rule, which the
# schema reports at the root). A model-written key or quoted text that merely contains `facilit`
# is not one.
_FACILITY_REFUSAL = re.compile(
    r"^[\w-]+: (?:facility |scheduled repayments total |\w+_drivers states debt_repayment"
    r"|forecast inputs: (?:\d+ problems; first: )?"
    r"(?:facilities[.:]|\(root\): Value error, facility names must be unique))"
)
_BOTH_KEYS = re.compile(
    r"^[\w-]+: forecast inputs: (?:\d+ problems; first: )?base\.(\w+): Value error, an operand "
    r"names the `period` header or the `column` header, not both"
)
_BOTH_KEY_OPERAND = re.compile(
    r"base\.(\w+): Value error, an operand names the `period` header or the `column` header, "
    r"not both"
)
_UNNAMED_AT_SCALE = re.compile(r"^[\w-]+: a block at scale 1000 must name the row and period")


def _forecast_issues(task: HandoffTask, text: str) -> tuple[str, ...]:
    """Live run tdg-forecast-004 (2026-11-10): a forecast block delivery cannot parse is sent
    back for repair here, not dropped after payment. Declining (all null) stays the method's call
    and is accepted, so a model that cannot fix the block has a way to finish the run."""
    if task.module_id != "CP-2G" or "CP-1" not in task.handoffs:
        return ()
    try:
        inputs = cpos_forecast.parse(text, task.handoffs["CP-1"].decode("utf-8"))
    except ValueError as error:
        message = str(error)
        stem = message.removesuffix(".")  # the sentences below add their own full stop
        operand = re.search(r"^[\w-]+: base (\w+)\b", message)
        if operand:  # a wrong row label should not cost the forecast
            name = operand.group(1)
            fix = f"Correct the row, period, column or amount of {name}; "
            fix += f"if you cannot, state {name} "
            missing = "as missing: amount null, no row, period or column, and the reason."
            return (f"Forecast inputs: {stem}. {fix}{missing}",)
        if re.match(r"^[\w-]+: the handoff gives no forecast drivers", message):
            return ()  # declining stays the method's call
        both = _BOTH_KEYS.match(message)
        if both:
            names = list(dict.fromkeys(_BOTH_KEY_OPERAND.findall(message)))
            who = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"
            advice = f"State either `period` or `column` for {who}, not both."
            return (f"Forecast inputs: {stem}. {advice}",)
        if _UNNAMED_AT_SCALE.match(message):
            fix = "Name the row and the period or column of each base operand; if you cannot, "
            advice = (
                f"{fix}set every driver's values to [null, null, null] and say why in scope_limits."
            )
        elif _FACILITY_REFUSAL.match(message):
            fallback = "write `facilities` as null and keep the drivers."
            advice = f"Correct the facilities; if you cannot, {fallback}"
        else:
            fix = "Correct the block; if you cannot, set every driver's values to "
            advice = f"{fix}[null, null, null] and say why in scope_limits."
        return (f"Forecast inputs: {stem}. {advice}",)
    return (*_unstated_currency(inputs), *_shock_issues(task, inputs))


# A Share as cp2g writes one: 0, 1, 0.d to 0.dddd or 1.0 to 1.0000, and nothing numeric after it
# (so 20%, 0.31606, 1.5000, +0.30 and **0.20** are not read).
_SHARE_CELL = re.compile(r"^(?:0\.\d{1,4}|1\.0{1,4}|0|1)(?![\d.%])")
_PERCENT = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)%")
_SCENARIO_MARKER = "<!-- table-id: T2DS.1 -->"
_MAX_LISTED_SCENARIOS = 8


def _t2ds_rows(cp2a: str) -> tuple[list[list[str]], str]:
    """The rows of table T2DS.1 (header, divider, data) and the reason when there are none."""
    lines = cp2a.replace("\r\n", "\n").split("\n")
    marker = [i for i, line in enumerate(lines) if line.strip() == _SCENARIO_MARKER]
    if len(marker) != 1:
        return [], f"the marker of table T2DS.1 appears {len(marker)} times"
    tail = lines[marker[0] + 1 :]
    rows: list[list[str]] = []
    for n, line in enumerate(tail):
        if line.startswith("|"):
            if "\\|" in line:
                return [], "a table line holds an escaped pipe"
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif rows or line.strip():  # blank lines before the table are skipped
            if rows and "|" in next((after for after in tail[n:] if after.strip()), ""):
                return [], "a line with a pipe follows the table's last pipe line"
            break
    if len(rows) > 1 and not all(re.fullmatch(r"[-: ]+", cell) for cell in rows[1]):
        return [], "the second table row is not a divider"
    return rows, "" if len(rows) > 2 else "table T2DS.1 has no data rows"


def _t2ds_columns(header: list[str]) -> tuple[int, int] | None:
    cells = [cell.lower() for cell in header]
    found = [[i for i, cell in enumerate(cells) if name in cell] for name in _SCENARIO_COLUMNS]
    if any(len(each) != 1 for each in found) or found[0] == found[1]:
        return None
    return found[0][0], found[1][0]


_SCENARIO_COLUMNS = ("ebitda decline", "interest increase")


def _share(cell: str) -> str | None:
    found = _SHARE_CELL.match(cell)
    if found is None:
        return None
    percent = Decimal(found.group(0)) * 100
    rest = _PERCENT.sub(lambda m: "" if Decimal(m[1]) == percent else "0", cell[found.end() :])
    return None if re.search(r"\d", rest) else found.group(0)


def _t2ds_pairs(rows: list[list[str]], columns: tuple[int, int]) -> list[tuple[str, str]] | str:
    """Every data row's two Shares, or the reason a row does not give them."""
    pairs = []
    for row in rows[2:]:  # the header and its divider are not scenarios
        read = [_share(row[i]) if i < len(row) else None for i in columns]
        if read[0] is None or read[1] is None:
            return f"a scenario row has a cell that does not open with a Share: {str(row)[:200]}"
        pairs.append((read[0], read[1]))
    return pairs


def _cp2a_scenarios(cp2a: str) -> tuple[tuple[str, str], ...]:
    """The (EBITDA decline, cash-interest increase) pairs of CP-2A's table T2DS.1, each as the
    Share its cell opens with. Empty (the check does not run) unless Python read the whole table
    without doubt: one marker, one cell for each column, every data row long enough and both its
    cells opening with a Share, and at least one row that is not the zero control. Documented
    fail-open: a repair round costs a paid call, so a block is sent back only for a table Python
    read completely; the reason is logged at WARNING."""
    rows, why = _t2ds_rows(cp2a)
    columns = _t2ds_columns(rows[0]) if not why else None
    if not why and columns is None:
        why = "the header lacks exactly one EBITDA decline cell and one interest increase cell"
    pairs = _t2ds_pairs(rows, columns) if columns else []
    if isinstance(pairs, str):
        why, pairs = pairs, []
    if not why and all(Decimal(s) == 0 and Decimal(k) == 0 for s, k in pairs):
        why = "no scenario row is other than the zero control"
    if why:
        log.warning("CP-2A scenarios not checked against downside_shock: %s", why)
        return ()
    return tuple(pairs)


def _shock_issues(task: HandoffTask, inputs: cpos_forecast.ForecastInputs) -> tuple[str, ...]:
    """The block's `downside_shock` must be one of CP-2A's stated scenarios (owner ruling
    2026-11-13). Documented fail-open, logged at WARNING with its reason (`_cp2a_scenarios`): when
    CP-2A is not sent, or Python did not read the whole of its T2DS.1 table, nothing is checked
    and the block is not sent back."""
    stated = inputs.downside_shock
    if stated is None:
        return ()
    if "CP-2A" not in task.handoffs:
        log.warning("CP-2A scenarios not checked against downside_shock: CP-2A is not sent")
        return ()
    scenarios = _cp2a_scenarios(task.handoffs["CP-2A"].decode("utf-8"))
    pair = (Decimal(stated.ebitda_decline), Decimal(stated.rate_increase))
    if not scenarios or pair in {(Decimal(s), Decimal(k)) for s, k in scenarios}:
        return ()
    shown = scenarios[:_MAX_LISTED_SCENARIOS]
    listed = "; ".join(f"{s} / {k}" for s, k in shown)
    if len(scenarios) > len(shown):
        listed += f"; and {len(scenarios) - len(shown)} more"
    issue = (
        f"Forecast inputs: `downside_shock` ({stated.ebitda_decline} / {stated.rate_increase}) "
        "is not a CP-2A scenario. It must copy one CP-2A scenario unchanged: `rate_increase` is "
        "that scenario's proportional increase in cash interest (0 to 1), never a yield change. "
        f"CP-2A's table T2DS.1 states (EBITDA decline / cash-interest increase): {listed}. "
        "If you cannot copy one of them, set `downside_shock` to null."
    )
    return (issue,)


def _unstated_currency(inputs: cpos_forecast.ForecastInputs) -> tuple[str, ...]:
    """Reading a block without `currency` stays USD (blocks that predate the field); a block
    written now that states `scale` says which currency its statements are printed in."""
    if inputs.scale is None or inputs.currency is not None:
        return ()
    asked = "state `currency`: the three-letter code of the currency CP-1 reports its figures in"
    return (f"Forecast inputs: {asked}.",)


def _cap(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"{text!r} is not an amount") from None
    if not value.is_finite() or value <= 0:
        raise argparse.ArgumentTypeError("the cap must be a positive amount in USD")
    return value


def run_cap(pathway: PathwayId, asked: Decimal | None) -> Decimal:
    """The cap a launch runs at: the pathway's (`PATHWAY_CAP_USD`), or a lower one asked for.

    Owner, 2026-11-15: "Hard cap per pathway". Every launch ends here (the run start service
    passes `--cap` too), so a cap above the pathway's is refused whoever asks; the pathway is the
    context's, which is what runs."""
    ceiling = PATHWAY_CAP_USD[pathway]
    if asked is None:
        return ceiling
    if asked > ceiling:
        raise LaunchRefused(
            f"--cap {asked}: above the {pathway} cap of USD {ceiling} "
            "(docs/rulings/2026-11-15-pathway-tiers-and-caps.md); a lower cap is allowed"
        )
    return asked


def _web_line(prepared: Prepared, config: str, ruling: Path | None) -> tuple[str, ...]:
    """Whether the research module searches the web, when it runs."""
    if "CP-DR" not in prepared.ordered:
        return ()
    kind = prepared.plan.run.case_kind
    if web_search_ruled(ruling) and CONFIGS[config].provider != "openai":
        return ("Web:      off: web search is offered on GPT Sol only, not on this config",)
    if web_search_ruled(ruling) and kind not in WEB_SEARCH_CASE_KINDS:
        return (f"Web:      off: {kind} case",)
    if web_search_ruled(ruling):
        return (f"Web:      CP-DR searches the web (the ruling lists {WEB_SEARCH_GRANT})",)
    why = "the ruling does not list" if ruling is not None else "no ruling lists"
    return (f"Web:      off: CP-DR reads only this run's files ({why} {WEB_SEARCH_GRANT})",)


def _lookup_lines(
    prepared: Prepared,
    setting: str,
    hosts: Sequence[str],
    env: Mapping[str, str],
    recorded: str | None = None,
) -> tuple[str, ...]:
    """Whether the research module may fetch public pages and SEC EDGAR data, when it runs: the
    one rule (`web_lookup_offered`) and its reason, or what the run folder recorded when it was
    started (`recorded`). The contact string's value is never printed."""
    module = WEB_LOOKUP_MODULES[0]
    if module not in prepared.ordered:
        return ()
    kind = prepared.plan.run.case_kind
    on = recorded == "on" if recorded is not None else web_lookup_offered(setting, module, kind)
    if recorded is not None:
        head = f"Lookup:   {recorded} (as recorded when this run folder was started)"
    elif setting == "default":
        why = f"{kind} case default"
        head = (
            f"Lookup:   on: {module} may fetch allowlisted public pages and SEC EDGAR ({why})"
            if on
            else f"Lookup:   off: {kind} case (default); --web-lookup on forces it"
        )
    else:
        head = f"Lookup:   {setting} (forced by --web-lookup {setting})"
    if on and hosts:
        head += f"; case hosts: {', '.join(hosts)}"
    refused = (
        (f"SEC:      sec.gov lookups will be refused: {USER_AGENT_ENV} is not set",)
        if on and usable_user_agent(env) is None
        else ()
    )
    return (head, *refused)


def _first_prompt_lines(prepared: Prepared, config: str) -> tuple[str, ...]:
    """Readiness warnings, GitHub Copilot configs only: each module whose first prompt, estimated
    in tokens, plus the output budget passes the share of the route's limit at which the runtime
    starts to summarise its context. A warning only: nothing is refused.

    What can be estimated before the run: the instructions (exact) and the request's fixed part
    (`REQUEST_ALLOWANCE`). The handoffs a module is sent do not exist yet; where an earlier run
    of the issuer is pinned (CP-8's comparison) its handoffs stand in for them, otherwise they are
    left out and the estimate is a floor. `HandoffExecutor` checks each module again, on its real
    first prompt, before its first call (event ``first_prompt_near_limit``)."""
    chosen = CONFIGS[config]
    if chosen.provider != "copilot" or chosen.model not in copilot_route.TOKEN_LIMITS:
        return ()
    earlier = {
        name: (prepared.directory / pin.path).read_bytes()
        for name, pin in prepared.plan.sources.items()
        if name.startswith(PRIOR_PREFIX)
    }
    producers = dependencies(prepared.ordered)
    lines: list[str] = []
    unsized = False
    for module in prepared.ordered:
        sent = [m for m in prepared.ordered if m in producers[module] and m != "CP-8"]
        instructions = (prepared.directory / prepared.plan.instructions[module].path).stat()
        tokens = copilot_route.prompt_tokens_estimate(
            _cp8_request_bytes(instructions.st_size, sent, earlier)
        )
        basis = "instructions only"
        if sent and earlier:
            basis = "handoffs sized from the earlier run's"
        unsized = unsized or bool(sent and not earlier)
        limit = copilot_route.near_limit(chosen.model, tokens, output_limit(config))
        if limit is not None:
            share = int(copilot_route.COMPACTION_SHARE * 100)
            lines.append(
                f"Context:  {module}: first prompt about {tokens:,} tokens ({basis}) plus "
                f"{output_limit(config):,} output is over {share}% of the {limit:,}-token limit; "
                "GitHub Copilot may summarise the context (recorded and charged)"
            )
    if unsized:
        lines.append(
            "Context:  handoffs not written yet are not counted; each module's first prompt is "
            "checked again before its first call (event first_prompt_near_limit)"
        )
    return tuple(lines)


def _readiness(
    prepared: Prepared,
    config: str,
    ruling: Path | None = None,
    *,
    web_lookup: str = "default",
    web_hosts: Sequence[str] = (),
) -> str:
    selected = CONFIGS[config]
    run = prepared.plan.run
    names = (n for n in prepared.plan.sources if n != CONTEXT_SOURCE_ID)
    return "\n".join(
        (
            f"Run:      {run.run_id}",
            f"Model:    {config} = {selected.provider} {selected.model}, effort {selected.effort}",
            f"Cap:      USD {prepared.plan.provider_cap_usd} (hold per call: {prepared.hold:.2f})",
            f"Modules:  {', '.join(prepared.ordered)}",
            f"Sources:  {', '.join(names)}",
            f"Ignored:  {', '.join(prepared.ignored) or 'none'}",
            *portfolio_lines(prepared.portfolio),
            f"Report:   {', '.join(prepared.layout.blocks)}",
            f"Omitted:  {', '.join(prepared.omitted) or 'none'}",
            f"Changes:  {prepared.changes.removeprefix('changes: ') or 'not recorded'}",
            f"Manifest: {prepared.manifest}",
            *_web_line(prepared, config, ruling),
            *_lookup_lines(
                prepared,
                web_lookup,
                web_hosts,
                os.environ,
                recorded_web_lookup(prepared.directory / "live" / "loop.json"),
            ),
            *_first_prompt_lines(prepared, config),
        )
    )


# Evidence: runs/tdg-mixed-effort-comparison.md. CP-1D and CP-2 measured gains, CP-1A modest; the
# rest (CP-2A, CP-3, CP-3C, CP-4, CP-4C, CP-6) are inferred judgement modules and untested.
# CP-0, CP-1, CP-1B, CP-1C, CP-DR measured adequate at medium; CP-2D, CP-2E, CP-2G, CP-2H, CP-3D
# and CP-5 stay at medium, untested.
BALANCED_HIGH_MODULES = (
    "CP-1A",
    "CP-1D",
    "CP-2",
    "CP-2A",
    "CP-3",
    "CP-3C",
    "CP-4",
    "CP-4C",
    "CP-6",
)


def _high_efforts(
    config: str,
    modules: Sequence[str],
    ordered: Sequence[str] | None = None,
    flag: str = "--high-modules",
) -> dict[str, str]:
    """The per-module effort map for ``flag``; refuses what the model cannot run."""
    selected = CONFIGS[config]
    if "high" not in MODEL_EFFORTS[selected.model] or selected.effort == "high":
        raise LaunchRefused(
            f"{flag} needs a config whose model allows high and runs another effort, not {config}"
        )
    if ordered is not None and (stray := [m for m in modules if m not in ordered]):
        raise LaunchRefused(f"--high-modules names modules outside this run: {', '.join(stray)}")
    return {m: "high" for m in modules}


def _web_host(text: str) -> str:
    """A ``--web-host`` value: a bare host name, in lower case."""
    problem = bare_host_problem(text)
    if problem is not None:
        raise argparse.ArgumentTypeError(problem)
    return text.lower()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m deploy_workflow.owners.cpos_launch",
        description="Prepare a CP-OS run; add --live and --ruling to start the paid run.",
    )
    parser.add_argument("--context", type=Path, required=True, help="context/1 JSON file")
    parser.add_argument("--sources", type=Path, required=True, help="folder of issuer files")
    parser.add_argument("--config", choices=tuple(CONFIGS), required=True, help="model and effort")
    parser.add_argument(
        "--cap",
        type=_cap,
        help="USD ceiling for this run folder: at most, and by default, the pathway's cap",
    )
    parser.add_argument("--modules", nargs="+", help="default: the context's pathway preset")
    parser.add_argument("--max-turns", type=int, default=32, help="model turns per module")
    parser.add_argument("--out", type=Path, help="run folder; default runs/<run id>")
    parser.add_argument("--live", action="store_true", help="make paid provider calls")
    parser.add_argument("--ruling", type=Path, help="docs/rulings/<file>.md naming this config")
    parser.add_argument(
        "--prior",
        help="the earlier run to compare with: its run folder name, or `none` for a first run "
        "(the run start service passes what the approval named; default: search)",
    )
    parser.add_argument(
        "--web-lookup",
        choices=("default", "on", "off"),
        default="default",
        help="CP-DR's page and SEC EDGAR lookups: on for a public case by default, off otherwise; "
        "on or off forces it",
    )
    parser.add_argument(
        "--web-host",
        action="append",
        default=[],
        type=_web_host,
        metavar="HOST",
        help="an investor-relations host of this case to add to the lookup allowlist (repeatable)",
    )
    parser.add_argument(
        "--high-modules",
        nargs="+",
        default=(),
        metavar="MODULE",
        help="send these modules at high effort; the rest keep the config's effort",
    )
    parser.add_argument(
        "--balanced",
        action="store_true",
        help="send high effort to the balanced effort map's modules in this run",
    )
    parser.add_argument(
        "--no-library",
        action="store_true",
        help="do not rebuild the library; the run start service does",
    )
    return parser


def update_library_at(workspace: Path) -> Any:
    """Rebuild ``workspace/library`` with the library app's ``update_library`` module: a checkout
    installs it (the issuer-library package), the Windows package lists its folder in the bundled
    Python's path file. Returns None, after a note, when it is not installed."""
    try:
        module = importlib.import_module("update_library")
    except ModuleNotFoundError as error:
        if error.name != "update_library":
            raise
        print(f"Library not updated: update_library.py not found. {_library_command(workspace)}")
        return None
    return module.update_library(workspace)


def _library_command(workspace: Path) -> str:
    return f"Run: uv run python apps/issuer-library/update_library.py --workspace {workspace}"


def _refresh_library(directory: Path) -> None:
    """Rebuild the library once a run's report is published. Fail-open, by design: the report is
    already published and the run complete, so a library failure is printed to stderr with the
    manual command and never changes the exit code or the report. Only the failures a refused or
    failed build raises are caught: update_library refuses with library_index.Refused (a
    ValueError), and the build can raise OSError, ValueError or ImportError if it cannot load."""
    if directory.parent.name != "runs":
        print(f"Library not updated: {directory} is not inside a runs folder.")
        return
    workspace = directory.parent.parent
    try:
        library = update_library_at(workspace)
    except (OSError, ValueError, ImportError) as error:
        print(
            f"Library not updated: {error or type(error).__name__}\n{_library_command(workspace)}",
            file=sys.stderr,
        )
        return
    if library is not None:
        print(f"Library:  {workspace / 'library' / 'index.html'} ({len(library.runs)} run(s))")


def _record_own_pid() -> None:
    """Write this process's ID to the file the run start service names, atomically (same folder)."""
    target = os.environ.get("DEPLOY_WORKFLOW_PID_FILE")  # the name inbox.runs sets
    if not target:
        return
    platform_io.write_atomic(Path(target), str(os.getpid()), sync=True)


def main(argv: Sequence[str] | None = None) -> int:
    try:  # first: a run that cannot be tracked must not start
        _record_own_pid()
    except OSError as error:
        print(f"cannot record this run's process ID: {error}", file=sys.stderr)
        return 2
    args = _parser().parse_args(argv)
    try:
        if args.live and args.ruling is None:
            raise LaunchRefused(
                f"--live needs --ruling docs/rulings/<file>.md naming {args.config}"
            )
        if args.ruling is not None:
            check_ruling(args.config, args.ruling)
        key = KEY_VARIABLES[CONFIGS[args.config].provider]
        cli_login = CONFIGS[args.config].provider == "copilot" and (
            os.environ.get(COPILOT_GH_LOGIN_VARIABLE) == "1"
        )
        if args.live and not (os.environ.get(key) or cli_login):
            extra = (
                f" (or {COPILOT_GH_LOGIN_VARIABLE}=1)"
                if CONFIGS[args.config].provider == "copilot"
                else ""
            )
            raise LaunchRefused(f"--live needs {key}{extra} in the launching environment")
        copilot_live = args.live and CONFIGS[args.config].provider == "copilot"
        if copilot_live and not Path(os.environ.get(COPILOT_RUNTIME_VARIABLE, "")).is_file():
            raise LaunchRefused(f"--live needs {COPILOT_RUNTIME_VARIABLE} to name an existing file")
        if args.balanced and args.high_modules:
            raise LaunchRefused("--balanced and --high-modules cannot be combined")
        if args.balanced or args.high_modules:
            _high_efforts(
                args.config,
                args.high_modules,
                flag="--balanced" if args.balanced else "--high-modules",
            )
        context = load_context(Path(args.context).expanduser().read_bytes())
        refuse_deactivated(context.run.pathway)
        prepared = prepare(
            args.context,
            args.sources,
            args.out,
            config=args.config,
            cap=run_cap(context.run.pathway, args.cap),
            modules=args.modules,
            web_search=web_search_run(args.config, args.ruling),
            prior=args.prior,
        )
        efforts = (
            _high_efforts(
                args.config,
                [m for m in BALANCED_HIGH_MODULES if m in prepared.ordered],
                flag="--balanced",
            )
            if args.balanced
            else _high_efforts(args.config, args.high_modules, prepared.ordered)
            if args.high_modules
            else {}
        )
        recorded = recorded_web_lookup(prepared.directory / "live" / "loop.json")
        lookup = settled_web_lookup(
            args.web_lookup, prepared.ordered, prepared.plan.run.case_kind, recorded
        )
    except (ValueError, OSError, LivePauseInForce) as error:
        print(error, file=sys.stderr)
        return 2
    print(
        _readiness(
            prepared, args.config, args.ruling, web_lookup=args.web_lookup, web_hosts=args.web_host
        ),
        flush=True,
    )
    if efforts:
        print(
            f"Effort:   high for {', '.join(efforts)}; {CONFIGS[args.config].effort} otherwise",
            flush=True,
        )
    if not args.live:
        print("No provider was called. Add --live --ruling <file> to start the paid run.")
        return 0
    try:
        receipt = run_live_handoffs(
            prepared.manifest,
            prepared.directory,
            ruling=args.ruling,
            check=checker(prepared.layout),
            max_turns=args.max_turns,
            max_output_tokens=output_limit(args.config),
            on_handoff=lambda task, _: print(f"Accepted: {task.module_id}", flush=True),
            config=args.config,
            effort_by_module=efforts,
            on_notice=lambda line: print(line, flush=True),
            web_lookup=lookup,
            web_hosts=tuple(args.web_host),
            lookup_cutoff=effective_cutoff(prepared.plan.run.as_of, context.run.cutoff),
        )
    except (ValueError, RuntimeError) as error:
        print(
            f"Stopped: {with_notes(error)}\nRetained work is in {prepared.directory}",
            file=sys.stderr,
        )
        _print_review(prepared.directory, sys.stderr)
        return 1
    spent = Budget(prepared.plan.provider_cap_usd, prepared.directory / "live").spent
    print(f"Delivery: {receipt}\nCharged:  USD {spent}")
    _print_review(prepared.directory, sys.stdout)
    if not args.no_library:
        _refresh_library(prepared.directory)
    print("Automated checks only: review the handoffs against the sources before relying on this.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
