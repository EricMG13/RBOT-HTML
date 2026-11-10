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
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, get_args

from deploy_vii.business_context import Category
from deploy_vii.contracts import PATHWAY_MODULES, Run
from deploy_vii.live.prompts import STEP_CONTRACTS
from deploy_vii.registry import modules, plan
from deploy_vii.report_view import _spec_of, pathways
from deploy_workflow import platform_io
from deploy_workflow.context import CONTEXT_SOURCE_ID, RunContext, load_context
from deploy_workflow.handoff_delivery import (
    DeliveryRequest,
    HandoffInput,
    MarkdownLayout,
    MarkdownRoute,
    section,
)
from deploy_workflow.docx_text import docx_text
from deploy_workflow.html_text import convert_html
from deploy_workflow.markdown_delivery import (
    STRIP_FIGURES,
    literal_module,
    markdown_files,
    require_issuer,
)
from deploy_workflow.model.adapter import (
    COPILOT_GH_LOGIN_VARIABLE,
    COPILOT_RUNTIME_VARIABLE,
    KEY_VARIABLES,
    LivePauseInForce,
    check_ruling,
)
from deploy_workflow.model.budget import Budget
from deploy_workflow.model.handoff import Check, _pages
from deploy_workflow.model.pricing import price_of, request_reservation_usd
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.owners import cp2g, cpos_forecast
from deploy_workflow.owners.cpos import (
    WEB_SEARCH_GRANT,
    HandoffPlan,
    HandoffTask,
    run_live_handoffs,
    web_search_ruled,
    with_notes,
)
from deploy_workflow.reader_summary import (
    BOTTOM_LINE_WORDS,
    CONFIDENCE,
    FINDING_WORDS,
    LIMITATION_WORDS,
    MAX_FINDINGS,
    reader_issues,
)
from deploy_workflow.run_expectations import Item, edges_for, expectations, guess_kind
from deploy_workflow.workflow import _put

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

_SKILLS = "docs/reuse/selected-methods/skills/"
_VII = "src/deploy_vii/methods/"
# The Confidence Score rules `confidence_score.py` applies; the script cannot run in this transport.
_SCORE = "docs/reuse/selected-methods/CANON_SHARED.md § CP_CONFIDENCE_SCORE.md"
# The method each module runs, per METHODOLOGY-REVIEW.md and what the 2026-11-05 live campaigns
# consumed. prompts/CP-0.md and CP-1-intake.md are TDG case instructions, so they are left out.
# Owner, 2026-11-10 ("Fix all"): each skill is sent every companion its SKILL.md calls mandatory
# or binding (a runbook, a phase's method bundle), copied from cp-os at b57a344 and listed in
# docs/reuse/selected-methods/manifest.json. Companions the SKILL opens only "to resolve an
# ambiguity" (CANON_SHARED.md, the schema and system references) are archived, not sent.
_SELECTED: dict[str, tuple[str, ...]] = {
    "CP-0": (_VII + "cp0.md",),
    "CP-1": ("prompts/CP-1.md",),  # Plus CP1_STEPS; no standalone CP-1 method file exists.
    "CP-1A": (_VII + "cp1a.md",),
    # Deploy V's skill: earnings_delta.md needs the structured runtime's `read_inputs` view, which
    # CP-OS does not give, so it blocked on every CP-OS run (2026-11-09, 2026-11-10).
    "CP-1B": (
        _SKILLS + "cp-1b-earnings-delta/SKILL.md",
        _SKILLS + "cp-1b-earnings-delta/references/REF_CP-1B_STEPS.md",
    ),
    "CP-1C": (
        _SKILLS + "cp-1c-peer-benchmark/SKILL.md",
        _SKILLS + "cp-1c-peer-benchmark/references/REF_CP-1C_STEPS.md",
    ),
    "CP-1D": (_SKILLS + "cp-1d-earnings-quality/SKILL.md",),
    "CP-2": (_VII + "cp2.md",),
    "CP-2A": (
        _SKILLS + "cp-2a-downside-pathway/SKILL.md",
        _SKILLS + "cp-2a-downside-pathway/references/REF_CP-2A_STEPS.md",
        _SKILLS + "cp-2a-downside-pathway/references/REF_CP-2B_STEPS.md",
        _VII + "cp2a.md",
    ),
    "CP-2D": (
        _SKILLS + "cp-2d-liquidity-cash-flow-bridge/SKILL.md",
        _SKILLS + "cp-2d-liquidity-cash-flow-bridge/references/REF_CP-2D_STEPS.md",
    ),
    "CP-2E": (
        _SKILLS + "cp-2e-macro-fx-hedging-sensitivity/SKILL.md",
        _SKILLS + "cp-2e-macro-fx-hedging-sensitivity/references/REF_CP-2E_STEPS.md",
        _SKILLS + "cp-2e-macro-fx-hedging-sensitivity/references/REF_CP-2F_STEPS.md",
    ),
    "CP-2G": (
        _SKILLS + "cp-2g-forward-credit-model/SKILL.md",
        _SKILLS + "cp-2g-forward-credit-model/references/REF_CP-2G_STEPS.md",
    ),
    "CP-2H": (
        _SKILLS + "cp-2h-ratings-migration-trigger/SKILL.md",
        _SKILLS + "cp-2h-ratings-migration-trigger/references/REF_CP-2H_STEPS.md",
    ),
    "CP-3": (
        _SKILLS + "cp-3-relative-value-security-selection/SKILL.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/REF_CP-3_STEPS.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/REF_CP-3A_STEPS.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/CP-3A_RUNBOOK.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/REF_CP-3B_STEPS.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/CP-3B_RUNBOOK.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/CP-3_SCHEMA_REFERENCE.md",
    ),
    "CP-3C": (_VII + "cp3c.md",),
    "CP-3D": (
        _SKILLS + "cp-3d-market-implied-risk/SKILL.md",
        _SKILLS + "cp-3d-market-implied-risk/references/REF_CP-3D_STEPS.md",
    ),
    "CP-4": (
        _SKILLS + "cp-4-legal-covenant-interpreter/SKILL.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/CP-4_RUNBOOK.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/REF_CP-4_STEPS.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/CP-4A_RUNBOOK.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/REF_CP-4A_STEPS.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/CP-4B_RUNBOOK.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/REF_CP-4B_STEPS.md",
    ),
    "CP-4C": (
        _SKILLS + "cp-4c-restructuring-fulcrum/SKILL.md",
        _SKILLS + "cp-4c-restructuring-fulcrum/references/REF_CP-4C_STEPS.md",
    ),
    "CP-5": (
        _SKILLS + "cp-5-evidence-trace-validator/SKILL.md",
        _SKILLS + "cp-5-evidence-trace-validator/references/CP-5_RUNBOOK.md",
        _SKILLS + "cp-5-evidence-trace-validator/references/REF_CP-5_STEPS.md",
        _SKILLS + "cp-5-evidence-trace-validator/references/REF_CP-5A_STEPS.md",
    ),
    "CP-6": (
        _SKILLS + "cp-6-ic-debate-challenge/SKILL.md",
        _SKILLS + "cp-6-ic-debate-challenge/references/REF_CP-6_STEPS.md",
        _SKILLS + "cp-6-ic-debate-challenge/references/REF_CP-6A_STEPS.md",
    ),
    "CP-DR": (
        _SKILLS + "cp-dr-deep-research/SKILL.md",
        _SKILLS + "cp-dr-deep-research/references/REF_CP-DR_STEPS.md",
        _SKILLS + "cp-os-credit-os/references/CP_DR_RESEARCH_BRIEF_V1.md",
        _VII + "cpdr.md",
    ),
}
METHODS: dict[str, tuple[str, ...]] = {
    module: (*paths, _SCORE) if any(p.startswith(_SKILLS) for p in paths) else paths
    for module, paths in _SELECTED.items()
}
CP1_STEPS = ("source_context", "financials", "narrative", "readiness", "quality")
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
# The H3 that opens every module's `## Findings`: prose stating the module's view in plain English
# before any table (owner ruling, 2026-11-05; Deploy V's M365 runs for VMO2 and Wood Mackenzie open
# each module's analysis that way). "Credit view" (CP-1C, CP-2) and "Downside view" (CP-2A) are the
# M365 headings. A module added to METHODS needs an entry here; a test fails otherwise.
# This launcher route only: the owner route (`deploy_vii.cp2_synthesis`, Python-composed
# Markdown) is unchanged.
OPENING: dict[str, str] = {
    "CP-0": "Readiness view",
    "CP-1": "Financial base view",
    "CP-1A": "Business and transaction view",
    "CP-1B": "Earnings delta view",
    "CP-1C": "Credit view",
    "CP-1D": "Earnings quality view",
    "CP-2": "Credit view",
    "CP-2A": "Downside view",
    "CP-2D": "Liquidity view",
    "CP-2E": "Macro and FX view",
    "CP-2G": "Forward model view",
    "CP-2H": "Ratings view",
    "CP-3": "Relative value view",
    "CP-3C": "Funding gap view",
    "CP-3D": "Market-implied view",
    "CP-4": "Covenant view",
    "CP-4C": "Restructuring view",
    "CP-5": "Evidence trace view",
    "CP-6": "Challenge view",
    "CP-DR": "Research view",
}
# Only CP-2 gets READER_STANDARD (owner ruling, 2026-11-05): M365 output did not follow the
# CANON_SHARED rules, so they stay scoped to the one module that had them.
READER_STANDARD_MODULES = frozenset({"CP-2"})
# The user's Microsoft 365 Copilot custom instruction (supplied 2026-11-05, every clause kept):
# a persona that applies to every module (owner ruling, 2026-11-05). ponytail: instructions only.
READER_PERSONA = (
    "You are a senior credit research analyst at a leading credit fund, specialising in high "
    "yield credit and leveraged loans. Your research is used throughout the firm for key "
    "investment decisions; it is presented to senior credit committees and affects portfolio "
    "management. Your findings are institutional-grade, deeply analytical and data-dense, fully "
    "reasoned with explicit links from data to risk to credit implication. Say nothing generic "
    "unless it is tied to issuer-specific mechanics. Write in a detailed, structured style "
    "grounded in the provided data, and say when information is insufficient. State explicitly "
    "when information comes from external sources.\n\n"
)
# For READER_STANDARD_MODULES only: CANON_SHARED.md's reader-facing layer, and two habits of Deploy
# V's M365 handoffs (VMO2 2026-09-20, Wood Mackenzie 2026-08-27): units on amounts, the issuer as
# subject. The checker enforces the opening, not the prose.
READER_STANDARD = (
    "Presentation rules, from the reader-facing standard of Deploy V's CANON_SHARED.md. They "
    "never remove a method duty, category tag, limitation or gap:\n"
    "- In the opening section, state the credit view in plain English in the first sentence. In "
    "90–150 words, give the strongest support, the weakest point and what decides the outcome.\n"
    "- Keep `## Request` to the issuer, as-of date, pathway and scope, in at most three "
    "sentences. Readiness status, revision history and scope disclaimers belong in `## Gaps`.\n"
    "- State each limitation once, where it changes a conclusion, and say what it changes. Do not "
    "repeat a caveat in sentence after sentence.\n"
    "- In prose, give every amount its currency and unit, for example USD 1,250 million, 3.1x "
    "or 61 bp.\n"
    "- Make the issuer, its debt or its creditors the subject of a sentence, not a module. Cite "
    "modules and locators in brackets or tables.\n"
    "- Use plain-English labels. Hashes and raw locators belong in `## Sources` and tables.\n\n"
)


class LaunchRefused(ValueError):
    """The request cannot start; the message says what to change."""


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


# Fixed so any run's charts can be read without issuer-specific row selectors.
CHART_TABLES: dict[str, tuple[str, tuple[str, ...], str]] = {
    "S.1": ("Chart data: leverage", ("Total debt / EBITDA", "Net debt / EBITDA"), "x"),
    "S.2": ("Chart data: interest cover", ("EBITDA / cash interest",), "x"),
    "S.3": ("Chart data: liquidity", ("Cash", "Undrawn committed facilities"), "US$m"),
    "S.4": ("Chart data: debt maturities", ("Debt maturing",), "US$m"),
}
CHART_BLOCKS = frozenset(STRIP_FIGURES) - {"yield-against-maturity"}
NOT_SUPPLIED = "Not supplied:"
PLAIN_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _chart_route(block_id: str, figure: str) -> MarkdownRoute:
    heading, columns, unit = CHART_TABLES[figure]
    return MarkdownRoute(
        module_id="CP-1",
        heading=heading,
        kind="chart",
        block_id=block_id,
        figure_id=figure,
        value_columns=columns,
        orientation="period-rows",
        chart_unit=unit,
    )


@dataclass(frozen=True)
class OwnerTable:
    """A `### Chart data: ...` table an owning module is asked for beside the report's own charts.

    Only the library draws it, so it is not a delivery route. `steps` makes it a bridge: rows are
    steps, the first the opening amount and the last the closing, the rows between signed changes.
    Add a bridge or a period table for any module here and the instructions and the loop's
    validation follow."""

    module_id: str
    figure_id: str
    heading: str
    value_columns: tuple[str, ...]
    chart_unit: str
    steps: bool = False
    rules: str = ""  # The catalogue guard for the view, sent to the module with the table.


# The catalogue's launcher-asked figures (docs/visualisations/catalogue.csv) that are not report
# strip figures: S.5 (CP-1-V05), the liquidity bridge (CP-2D-V01) and the refinancing need
# (CP-3C-V01).
OWNER_TABLES: dict[str, tuple[OwnerTable, ...]] = {
    "CP-1": (
        OwnerTable(
            "CP-1",
            "S.5",
            "Chart data: revenue and EBITDA",
            ("Revenue", "Adjusted EBITDA"),
            "US$m",
            rules=(
                "The Adjusted EBITDA column is the EBITDA measure the method specifies; name its "
                "identity (reported, issuer-adjusted or house-adjusted) in Basis and "
                "limitation, and do not mix identities across rows. Every row is a comparable "
                "period of the same duration; one table must not mix durations (annual with "
                "quarterly or half-year); a period of another duration is "
                "`Not supplied: <reason>`."
            ),
        ),
    ),
    "CP-2D": (
        OwnerTable(
            "CP-2D",
            "CR.2",
            "Chart data: liquidity bridge",
            ("Amount",),
            "US$m",
            steps=True,
            rules=(
                "Only accessible liquidity is bridged: restricted or trapped cash and uncertain "
                "facility access are not accessible liquidity, so exclude them or state each as "
                "its own step. Use the method's signed values and timing; name the basis in "
                "Basis and limitation."
            ),
        ),
    ),
    "CP-3C": (
        OwnerTable(
            "CP-3C",
            "CR.3",
            "Chart data: refinancing need",
            ("Debt maturing", "Committed resources"),
            "US$m",
            rules=(
                "Committed resources exclude a refinancing that is only a suggested path; a "
                "resource shared by more than one need is counted once, never a double-counting. "
                "Name the maturity and funding basis in Basis and limitation."
            ),
        ),
    ),
}


def _owner_table(table: MarkdownRoute | OwnerTable) -> OwnerTable:
    if isinstance(table, OwnerTable):
        return table
    return OwnerTable(
        table.module_id,
        str(table.figure_id),
        table.heading,
        table.value_columns,
        str(table.chart_unit),
    )


def _chart_header(table: MarkdownRoute | OwnerTable) -> list[str]:
    spec = _owner_table(table)
    first = "Step" if spec.steps else "Period"
    return [first, *spec.value_columns, "Reporting unit", "Basis and limitation"]


def _stated_rows(text: str, heading: str) -> list[list[str]]:
    lines = text.splitlines()
    rows = []
    for line in lines[lines.index(heading) + 1 :]:
        if line.startswith("#"):
            break
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def _decimals(number: str) -> int:
    return len(number.partition(".")[2])


def _bridge_issues(heading: str, rows: list[list[str]]) -> list[str]:
    """A step table is a check on what the module stated, never a derivation: nothing is filled.

    Every amount is a plain signed number, or every one is `Not supplied: <reason>` (a bridge the
    module cannot state). Opening plus the stated changes must equal the closing; each amount has
    at most the table's own number of decimals, so the sum is exact and any difference is real."""
    amounts = [row[1] for row in rows]
    unsupplied = [
        a.startswith(NOT_SUPPLIED) and a.removeprefix(NOT_SUPPLIED).strip() for a in amounts
    ]
    if not rows:
        return [f"`{heading}` needs an opening and a closing row."]
    if all(unsupplied):
        return []
    if len(rows) < 2:
        return [f"`{heading}` needs an opening and a closing row."]
    if not all(PLAIN_NUMBER.fullmatch(a) for a in amounts):
        return [
            (
                f"`{heading}`: every Amount must be a plain signed number (a gap is "
                "`Not supplied: <reason>` in every Amount, so no partial bridge is drawn)."
            )
        ]
    values = [Decimal(a.replace(",", "")) for a in amounts]
    opening, *changes, closing = values
    if opening + sum(changes, Decimal(0)) != closing:
        total = opening + sum(changes, Decimal(0))
        return [
            (
                f"`{heading}`: the opening {amounts[0]} plus the stated changes {total:,} does not "
                f"equal the closing {amounts[-1]}; state the missing step or correct the amount. "
                "Nothing is filled in for you."
            )
        ]
    return []


def chart_issues(text: str, table: MarkdownRoute | OwnerTable) -> tuple[str, ...]:
    """A chart table's cells reach the page as they are, so each must already be chart-ready."""
    spec = _owner_table(table)
    heading = f"### {spec.heading}"
    if heading not in text.splitlines():
        return (f"Add `{heading}` inside ## Findings, with its table.",)
    rows = _stated_rows(text, heading)
    header = _chart_header(spec)
    if not rows or rows[0] != header:
        return (f"`{heading}` needs the table headed `| {' | '.join(header)} |`.",)
    issues = []
    stated = []
    for row in rows[2:]:
        if len(row) != len(header):
            issues.append(f"`{heading}` row needs {len(header)} cells: {' | '.join(row)}")
            continue
        period, *values, unit, basis = row
        stated.append(row)
        if not basis:
            issues.append(f"`{heading}` {period}: Basis and limitation is blank.")
        for value in values:
            if value.startswith(NOT_SUPPLIED) and value.removeprefix(NOT_SUPPLIED).strip():
                continue
            if not PLAIN_NUMBER.fullmatch(value):
                issues.append(
                    f"`{heading}` {period}: `{value} |` must be a plain number "
                    "or `Not supplied: <reason>`."
                )
            elif unit != spec.chart_unit:
                issues.append(
                    f"`{heading}` {period}: a number in {unit} cannot be charted as "
                    f"{spec.chart_unit}; write `Not supplied: reported in {unit}`."
                )
    if spec.steps and not issues:
        issues += _bridge_issues(heading, stated)
    return tuple(issues)


# The lines the report states above the call, front-most first: the Reader summary's first table
# (instructed by READER_SECTION_RULES) of each module that is in the run, and CP-6's instructed
# `Final Action Bias:` paragraph. Nothing is read that no instruction asks the module to write.
FRONT_TITLES = {
    "CP-6": "Committee decision",
    "CP-5": "Evidence validation",
    "CP-2": "Fundamental credit",
    "CP-0": "Source readiness",
}
READER_SUMMARY_HEADER = "Bottom line | Confidence | Main limitation"


def _front_routes(ordered: tuple[str, ...]) -> tuple[MarkdownRoute, ...]:
    routes = [
        MarkdownRoute(
            module_id=module_id,
            heading="Reader summary",
            kind="table",
            block_id="front",
            table_header=READER_SUMMARY_HEADER,
            label=title,
        )
        for module_id, title in FRONT_TITLES.items()
        if module_id in ordered
    ]
    if "CP-6" in ordered:
        routes.append(
            MarkdownRoute(
                module_id="CP-6",
                heading="Action Bias Determination",
                kind="prose",
                block_id="front",
                prefix="Final Action Bias:",
                label="Committee action bias",
            )
        )
    return tuple(routes)


HTML_MODEL_SCOPE = "The HTML Model and calculation JSON are not published by this launcher."
FORECAST_SCOPE = (
    "The HTML Model is not published by this launcher. A forecast table is published beside the "
    "report when the CP-2G handoff's inputs block validates; Python computes its figures from the "
    "inputs the handoff states, and the inputs are not independently reviewed."
)


def _layout(
    run: Run, ordered: tuple[str, ...], aliases: tuple[str, ...], config: str
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
        if owner is None or spec.kind == "chart" or block_id == SECOND_RUN_ONLY:
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
        "anchors, source and upstream references and report selectors; analytical accuracy has "
        "not been independently reviewed. "
        + (FORECAST_SCOPE if {"CP-1", "CP-2G"} <= set(ordered) else HTML_MODEL_SCOPE)
        + f" Sections not produced: {', '.join(omitted) or 'none'}."
    )
    layout = MarkdownLayout(
        blocks=tuple(dict.fromkeys(r.block_id for r in routes)),
        routes=tuple(routes),
        scope=scope,
        title=f"{run.issuer_name} — {preset.title}",
        issuer_aliases=aliases,
        front=_front_routes(ordered),
    )
    return layout, tuple(omitted)


READER_SECTION_RULES = (
    "Write `### Reader summary` after the analysis is finished and place it first under "
    "`## Findings`. It restates conclusions already in this handoff in plain language for a "
    "credit analyst: add no new fact, figure or conclusion. Use no module codes, table IDs or "
    "hashes. Every number must match the handoff exactly. Use these two tables, one row in the "
    f"first (bottom line at most {BOTTOM_LINE_WORDS} words, main limitation at most "
    f"{LIMITATION_WORDS}) and 1 to {MAX_FINDINGS} rows in the second (each finding and creditor "
    f"impact at most {FINDING_WORDS} words). Confidence is one of {', '.join(CONFIDENCE)}.\n\n"
    "| Bottom line | Confidence | Main limitation |\n| --- | --- | --- |\n\n"
    "| Finding | Creditor impact | Confidence |\n| --- | --- | --- |\n\n"
)


# Every module (owner, 2026-11-10, "Fix all"). Retained run cpos-tdg-sol-medium-all-001 and the
# 2026-11-10 inbox run: CP-1D, CP-3 and CP-5 blocked only for want of an acceptance receipt or a
# helper script's output, neither of which exists in this transport; only CP-2G had been told so.
TRANSPORT_RULES = (
    "Acceptance, helper scripts and entry values in this transport: CP-OS checked every handoff it "
    "supplies before passing it on, and pins each by its sha256. That check is the acceptance, "
    "validation and lineage the method asks of an upstream handoff: do not block for want of an "
    "acceptance receipt, invocation digest, settled-head verification or fresh snapshot. The "
    "method's helper scripts (`prepare_invocation.py`, `validate_handoff.py`, "
    "`confidence_score.py`, `completeness_check.py` and any other `scripts/*.py`) cannot be run "
    "here: record each as not run, do its check or arithmetic yourself (with `calculate`, by the "
    "rules in the method block), and do not block for it. A companion file the method names that "
    "is not in the method block below is unavailable: say so where the method relies on it, and do "
    "not block the module for it. CP-OS supplies only the handoffs of the modules the registry "
    "names as this module's producers (CP-5: every analyst before it); an upstream module the "
    "method names that is not supplied is unavailable in the same way. Nobody can answer a "
    "question during this run: take each entry "
    "value from the context and the supplied handoffs, then the method's declared safe default; "
    "where neither gives it the value is missing, so block only the decision the method ties to "
    "it. A supplied handoff that itself reports Blocked or a gap is a real limitation: restrict "
    "only the work that depends on it. Missing evidence still blocks exactly what the method says "
    "it blocks.\n\n"
)
# CP-2A only. Its two methods disagree on who sets the stress sizes; run tdg-forecast-005 followed
# the SKILL, gave no shock, and CP-2G had no stress case to compute. cp2a.md is the later
# correction (LEAD adaptation, ruling Q2), and the owner allowed labelled judgment for CP-2G's
# drivers on 2026-11-10 ("Yes, allow judgment").
STRESS_BLOCK = (
    "Stress design: where the method sections below differ on stress magnitudes, "
    "`src/deploy_vii/methods/cp2a.md` governs. You choose the base period, the scenarios, the "
    "shock sizes and the watch levels as labelled analyst assumptions (`Analyst Interpretation`, "
    "confidence never High), each anchored to a stated figure (a decline the sources report, a "
    "calculated break point, a disclosed rate exposure): name the anchor and what the assumption "
    "leaves out. A labelled, anchored assumption is not the invented or unsupported stress "
    "magnitude the other sections forbid; an unlabelled or unanchored one still is. State at least "
    "one scenario as a pair, an EBITDA decline and a cash-interest rate increase, each a fraction "
    "from 0 to 1 with at most four decimal places, so a forward model can apply it.\n\n"
)
# CP-DR and CP-1C, when the context's peer source is CP-DR and both run (cpdr.md, "The peer pack").
# Owner, 2026-11-10: "Cp-1c is supposed to get that information from cp-dr by default".
PEER_PACK_BLOCK = (
    "Peer pack: the context sets `valuation.peer_source` to `cp_dr_public` and CP-1C is in this "
    "run, so this run requests the peer pack with CP-1C as its consumer. Inside `## Findings` "
    "write TDR.4 (candidate peers), TDR.5 (alignment observations: period, definition, currency, "
    "segment) and TDR.6 (located figures, one row per peer and operand: `revenue`, `ebitda`, "
    "`debt`, `interest`, `ffo`, each with unit, currency, period end, source locator and a "
    "verbatim quote), as `src/deploy_vii/methods/cpdr.md` describes them. "
    "Use every source this run holds "
    "that is not the issuer's own document, and any research or web tool this environment gives "
    "you. Name no peer and type no figure from memory. Where no peer evidence can be reached, "
    "still write the three tables, each with one row saying what was searched and that nothing "
    "was found.\n\n"
)
PEER_READER_BLOCK = (
    "Peer source: the context sets `valuation.peer_source` to `cp_dr_public`, so take the peer set "
    "and its figures from the CP-DR handoff's TDR.4, TDR.5 and TDR.6 before any other discovery. "
    "You own inclusion, comparability, normalisation and every statistic. Block the benchmark for "
    "want of peers only when those tables hold no usable peer, and say so.\n\n"
)
# Goes into CP-2G's instructions before METHOD_MARK, never into the method block.
FORECAST_BLOCK = (
    f"Forecast inputs: write `{cpos_forecast.HEADING}` inside `## Findings`, holding exactly "
    "one fenced json block and no other fence. You state "
    "inputs only; Python computes every forecast figure, so put no forecast figure in the block. "
    '`base` holds exactly these ten operands in USD millions, each `{"amount": "<decimal>", '
    '"reason": null}` copied exactly as CP-1 prints it (outflows as positive magnitudes), or '
    '`{"amount": null, "reason": "<why CP-1 does not state it>"}`: '
    f"{', '.join(cp2g.OPERAND_METRIC)}. `base_drivers` is the method's base-case driver "
    "submission (revenue_growth, ebitda_margin, capex_pct_revenue, tax_wc_pct_revenue, "
    "interest_rate, dividends, debt_repayment; each with `values` for the three forecast years, "
    "`category`, `rationale` and `limitation`). Each driver's `values` are three decimal strings, "
    'one per forecast year (for example ["0.05", "0.04", "0.03"]), each rounded to at most four '
    'decimal places (a ratio of 0.48022670 is written "0.4802"); `category` is exactly one of '
    f"{', '.join(f'`{c}`' for c in get_args(Category))}. When the method gives no forecast "
    "(for example a blocked dependency), still write the block, with every driver's `values` as "
    "`[null, null, null]`. `downside_shock` is "
    '`{"ebitda_decline": "<0 to 1>", "rate_increase": "<0 to 1>"}` from the CP-2A '
    "scenario, or null when no shock was supplied; Python applies it to the base drivers. "
    "`upside_drivers` and `downside_drivers` are your own upside and downside cases: each holds "
    "only the drivers that differ from base, in the same driver form (every other driver is "
    "inherited from base), or null when you set no such case. "
    "`years` is three consecutive fiscal years, each "
    '`{"year": <int>, "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}`. '
    "`scope_limits` is a list of text limits. Set `schema_version` to "
    f"`{cpos_forecast.SCHEMA_VERSION}`.\n\n"
    # Live run tdg-forecast-001 (2026-11-10): with no command qualifier the method's entry protocol
    # found no forecast horizon and blocked, and it named the helper scripts as a second gate.
    "Entry values: this run's command is `Run CP-2G [forecast horizon: the three fiscal years "
    "after the base period] [base period: the current period the context names] "
    "[cases: base/upside/downside]`. CP-OS has locked these: do not ask for them and do not block "
    "the forecast for them. The horizon is the block's `years`. The method's helper scripts "
    "(`prepare_invocation.py`, `validate_handoff.py`, the scoring script) cannot be run in this "
    "transport: record each as not run. That, and the lack of an acceptance receipt for a handoff "
    "CP-OS supplied, is not a reason to block.\n\n"
    # Owner, 2026-11-10 ("Yes, allow judgment"): run tdg-forecast-002 gave no driver at all
    # because the filings carry no numeric three-year guidance.
    "Drivers: give a value for every driver in every forecast year. Where the sources state a "
    "number, use it under its category. Where they do not, give your own judgment as "
    "`Analyst Interpretation`, anchored to a stated figure (the midpoint of a guidance range, "
    "CP-1's latest-year ratio carried forward, a scheduled maturity or a declared payment): name "
    "the anchor in `rationale` and what the judgment leaves out in `limitation`. A judgment is "
    "an input to a mechanical forecast, not a finding. Leave a driver's values null, as "
    "`Insufficient Information`, only when no stated figure can anchor it.\n\n"
)


BRIDGE_RULES = (
    " Each row is one step: the first row is the opening amount and the last row is the closing "
    "amount; the rows between are the signed changes the method states (a negative number for an "
    "outflow), in the order the method states them. The opening plus those changes must reconcile "
    "to the closing at the precision the table states, or the table is sent back: state the "
    "missing step, never a plug. If the bridge cannot be stated, write `Not supplied: <reason>` "
    "in every Amount."
)


def _selector(route: MarkdownRoute | OwnerTable) -> str:
    if isinstance(route, OwnerTable) or route.kind == "chart":
        spec = _owner_table(route)
        return (
            f"- `### {spec.heading}`: exactly one Markdown table headed "
            f"`| {' | '.join(_chart_header(spec))} |`, one row per "
            f"{'step' if spec.steps else 'period'}. "
            f"Value cells are plain numbers in {spec.chart_unit}, with that as the Reporting unit, "
            "or `Not supplied: <reason>`. An issuer reporting in another currency or scale writes "
            "`Not supplied: reported in <unit>` in monetary cells. Basis and limitation is never "
            "blank."
            + (BRIDGE_RULES if spec.steps else "")
            + (f" {spec.rules}" if spec.rules else "")
        )
    what = (
        "exactly one populated Markdown table under it." if route.kind == "table" else "prose only."
    )
    return f"- `### {route.heading}`: {what}"


def method_sections(module: str) -> list[tuple[str, str]]:
    """The selected method a module is sent, as (name, text) sections in instruction order.

    Each section is written into the instructions under a ``=== name sha256 hex ===`` heading, so
    a run's retained instructions record exactly which method it ran.
    """
    sections = [(name, _method_file(name)) for name in METHODS[module]]
    if module == "CP-1":
        sections += [(f"STEP_CONTRACTS[{step}]", STEP_CONTRACTS[step]) for step in CP1_STEPS]
    return sections


def _method_file(name: str) -> str:
    """A method file's text; `path § heading` gives that `## heading` section alone."""
    path, _, heading = name.partition(" § ")
    text = (ROOT / path).read_text(encoding="utf-8")
    if not heading:
        return text
    start = text.index(f"## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start:] if end < 0 else text[start : end + 1]


# The method block follows this line and runs to the end of a module's instructions.
METHOD_MARK = "Selected method, verbatim:\n\n"


def method_heading(name: str, text: str) -> str:
    """The heading that names one method section and the sha256 of its text."""
    return f"=== {name} sha256 {_sha(text.encode())} ==="


def method_text(module: str) -> str:
    """The method block exactly as a module's instructions carry it."""
    return "\n\n".join(
        f"{method_heading(name, text)}\n{text}" for name, text in method_sections(module)
    )


def _instructions(
    run: Run,
    module: str,
    routes: Sequence[MarkdownRoute],
    *,
    run_type: str,  # Plan 3 (Primary scope) reads these two; no instruction byte uses them yet.
    legal_documents: str,
) -> bytes:
    asked: list[MarkdownRoute | OwnerTable] = [r for r in routes if r.module_id == module]
    selectors = "\n".join(_selector(r) for r in (*asked, *OWNER_TABLES.get(module, ())))
    method = method_text(module)
    opening = OPENING.get(module)
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
        + "A handoff is rejected unless it does all of this:\n"
        f"- name {run.issuer_name} in `## Request`, and state the as-of date {run.as_of} there;\n"
        "- list each issuer source it relied on in `## Sources`, with its exact name and sha256;\n"
        "- list each supplied handoff in `## Sources`, with its module and exact sha256"
        + (
            f";\n- place `### {opening}` directly after `### Reader summary`, once: prose that "
            "states the view, before any table.\n\n"
            if opening
            else ".\n\n"
        )
        + READER_SECTION_RULES
        + READER_PERSONA
        + (READER_STANDARD if module in READER_STANDARD_MODULES else "")
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
    """A pathway's analytical modules. Owner, 2026-11-10: CP-1C takes its peers from CP-DR by
    default, and no pathway lists CP-DR, so CP-DR joins a pathway that has CP-1C whenever the
    context names it as the peer source. Explicit --modules are run as given."""
    chosen = tuple(m for m in PATHWAY_MODULES[settings.run.pathway] if m not in NOT_ANALYTICAL)
    peers_from_research = settings.valuation.peer_source == "cp_dr_public"
    if "CP-1C" in chosen and "CP-DR" not in chosen and peers_from_research:
        return (*chosen, "CP-DR")
    return chosen


def prepare(  # noqa: PLR0913 - one keyword per run setting
    context: Path,
    sources: Path,
    out: Path | None,
    *,
    config: str,
    cap: Decimal | str,
    modules: Sequence[str] | None = None,
) -> Prepared:
    """Check everything and write the manifest and instructions; a refusal writes nothing."""
    context_path = Path(context).expanduser().resolve()
    folder = Path(sources).expanduser().resolve()
    raw_context = context_path.read_bytes()
    settings = load_context(raw_context)
    requested = tuple(modules) if modules else pathway_modules(settings)
    ordered = plan(requested)  # Refuses an unknown module, naming it.
    if unknown := [m for m in ordered if m not in METHODS]:
        raise LaunchRefused(f"--modules: no launchable method for {', '.join(unknown)}")
    run = Run(
        run_id=f"{settings.identity.issuer_id}-{settings.run.as_of}-{settings.run.pathway}-{config}",
        issuer_id=settings.identity.issuer_id,
        issuer_name=settings.identity.issuer_name,
        as_of=date.fromisoformat(settings.run.as_of),
        case_kind=settings.run.case_kind,
        pathway=settings.run.pathway,
        requested_modules=requested,
    )
    directory = (ROOT / "runs" / run.run_id if out is None else Path(out)).expanduser().resolve()
    if directory.is_relative_to(folder):
        raise LaunchRefused(f"--out {directory}: must be outside the issuer folder")
    pinned, converted, ignored, covers = _issuer_files(folder, context_path, directory)
    aliases = tuple(a for a in settings.identity.aliases if a.strip())
    layout, omitted = _layout(run, ordered, aliases, config)
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
    forecast = {"CP-1", "CP-2G"} <= set(ordered)
    peer_pack = settings.valuation.peer_source == "cp_dr_public" and {"CP-DR", "CP-1C"} <= set(
        ordered
    )
    for module, block, wanted in (
        ("CP-2G", FORECAST_BLOCK, forecast),
        ("CP-2A", STRESS_BLOCK, True),
        ("CP-DR", PEER_PACK_BLOCK, peer_pack),
        ("CP-1C", PEER_READER_BLOCK, peer_pack),
    ):
        if wanted and module in texts:
            head, mark, method = texts[module].partition(METHOD_MARK.encode())
            texts[module] = head + block.encode() + mark + method
    guesses = {key: guess_kind(name, pages) for key, (name, pages) in covers.items()}
    items = expectations(
        ordered, tuple(guesses.values()), settings, edges_for(ordered), omitted=omitted
    )
    documents = tuple(
        {
            "source": key,
            "kind": g.kind,
            "signal": g.signal,
            "executed": g.executed,
            "period_end": g.period_end,
        }
        for key, g in guesses.items()
    )
    request = HandoffPlan(
        run=run,
        sources={
            **pinned,
            CONTEXT_SOURCE_ID: HandoffInput(
                path=os.path.relpath(context_path, directory), sha256=_sha(raw_context)
            ),
        },
        instructions={
            m: HandoffInput(path=f"instructions/{m}.md", sha256=_sha(text))
            for m, text in texts.items()
        },
        layout=layout,
        publish_forecast=forecast,
        execution="live-provider",
        max_attempts=1,
        provider_cap_usd=Decimal(cap),
    )
    # The loop's own bound for the first call of the largest module; later calls hold more.
    hold = request_reservation_usd(
        price_of(config), max(map(len, texts.values())) + 4096, MAX_OUTPUT_TOKENS
    )
    if request.provider_cap_usd < hold:
        raise LaunchRefused(f"--cap {cap}: one {config} call holds up to USD {hold:.2f}")
    raw = request.model_dump_json(indent=2).encode()
    manifest = directory / "workflow.json"
    if manifest.exists() and manifest.read_bytes() != raw:
        raise LaunchRefused(f"--out {directory}: holds a different request; choose a new --out")
    for relative, content in converted.items():
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
        issues += reader_issues(text)
        opening = OPENING.get(task.module_id)
        if opening and not _opens_with(text.splitlines(), opening):
            issues.append(
                f"Place ### {opening} directly after ### Reader summary, once: prose that "
                "states the view, before any table."
            )
        routes = tuple(r for r in layout.routes if r.module_id == task.module_id)
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
            issues.append(f"The report adapter refused this handoff: {error}")
        for route in routes:
            if route.kind == "chart":
                issues += chart_issues(text, route)
        for owned in OWNER_TABLES.get(task.module_id, ()):
            issues += chart_issues(text, owned)
        return (*issues, *_forecast_issues(task, text))

    return check


def _forecast_issues(task: HandoffTask, text: str) -> tuple[str, ...]:
    """Live run tdg-forecast-004 (2026-11-10): a forecast block delivery cannot parse is sent
    back for repair here, not dropped after payment. Declining (all null) stays the method's call
    and is accepted, so a model that cannot fix the block has a way to finish the run."""
    if task.module_id != "CP-2G" or "CP-1" not in task.handoffs:
        return ()
    try:
        cpos_forecast.parse(text, task.handoffs["CP-1"].decode("utf-8"))
    except ValueError as error:
        if "gives no forecast drivers" not in str(error):
            fix = "Correct the block; if you cannot, set every driver's values to "
            return (
                f"Forecast inputs: {error}. {fix}[null, null, null] and say why in scope_limits.",
            )
    return ()


def _opens_with(lines: list[str], heading: str) -> bool:
    """`## Findings` starts with `### Reader summary`, then the one `### heading`, whose first
    content is a paragraph: a line opening with a letter, a quote mark or bold, not a table, list,
    fence, comment or heading.
    """
    try:
        findings = [line for _, line in section(lines, "Findings") if line.strip()]
        body = [line.strip() for _, line in section(lines, heading) if line.strip()]
    except ValueError:  # Missing or repeated.
        return False
    first = body[0] if body else ""
    headings = [line for line in findings if line.startswith("### ")]
    return (
        findings[:1] == ["### Reader summary"]
        and headings[1:2] == [f"### {heading}"]
        and (first[:1].isalpha() or first.startswith(("**", '"', "“")))
    )


def _cap(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"{text!r} is not an amount") from None
    if not value.is_finite() or value <= 0:
        raise argparse.ArgumentTypeError("the cap must be a positive amount in USD")
    return value


def _web_line(prepared: Prepared, ruling: Path | None) -> tuple[str, ...]:
    """Whether the research module searches the web, when it runs."""
    if "CP-DR" not in prepared.ordered:
        return ()
    if web_search_ruled(ruling):
        return (f"Web:      CP-DR searches the web (the ruling lists {WEB_SEARCH_GRANT})",)
    why = "the ruling does not list" if ruling is not None else "no ruling lists"
    return (f"Web:      off: CP-DR reads only this run's files ({why} {WEB_SEARCH_GRANT})",)


def _readiness(prepared: Prepared, config: str, ruling: Path | None = None) -> str:
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
            f"Report:   {', '.join(prepared.layout.blocks)}",
            f"Omitted:  {', '.join(prepared.omitted) or 'none'}",
            f"Manifest: {prepared.manifest}",
            *_web_line(prepared, ruling),
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m deploy_workflow.owners.cpos_launch",
        description="Prepare a CP-OS run; add --live and --ruling to start the paid run.",
    )
    parser.add_argument("--context", type=Path, required=True, help="context/1 JSON file")
    parser.add_argument("--sources", type=Path, required=True, help="folder of issuer files")
    parser.add_argument("--config", choices=tuple(CONFIGS), required=True, help="model and effort")
    parser.add_argument("--cap", type=_cap, required=True, help="USD ceiling for this run folder")
    parser.add_argument("--modules", nargs="+", help="default: the context's pathway preset")
    parser.add_argument("--max-turns", type=int, default=32, help="model turns per module")
    parser.add_argument("--out", type=Path, help="run folder; default runs/<run id>")
    parser.add_argument("--live", action="store_true", help="make paid provider calls")
    parser.add_argument("--ruling", type=Path, help="docs/rulings/<file>.md naming this config")
    parser.add_argument(
        "--no-library",
        action="store_true",
        help="do not rebuild the library; the inbox watcher does",
    )
    return parser


def update_library_at(workspace: Path) -> Any:
    """Rebuild ``workspace/library`` with the library app's ``update_library``, loaded by file
    location: the checkout keeps it in ``apps/issuer-library``, the Windows package beside the
    engine's ``src``. Returns None, after a note, when neither exists."""
    for path in (ROOT / "update_library.py", ROOT / "apps/issuer-library/update_library.py"):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("update_library", path)
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load {path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.update_library(workspace)
    print(f"Library not updated: update_library.py not found. {_library_command(workspace)}")
    return None


def _library_command(workspace: Path) -> str:
    return f"Run: python apps/issuer-library/update_library.py --workspace {workspace}"


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
    """Write this process's ID to the file the inbox watcher names, atomically (same folder)."""
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
        prepared = prepare(
            args.context,
            args.sources,
            args.out,
            config=args.config,
            cap=args.cap,
            modules=args.modules,
        )
    except (ValueError, OSError, LivePauseInForce) as error:
        print(error, file=sys.stderr)
        return 2
    print(_readiness(prepared, args.config, args.ruling), flush=True)
    if not args.live:
        print("No provider was called. Add --live --ruling <file> to start the paid run.")
        return 0
    try:
        report = run_live_handoffs(
            prepared.manifest,
            prepared.directory,
            ruling=args.ruling,
            check=checker(prepared.layout),
            max_turns=args.max_turns,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            on_handoff=lambda task, _: print(f"Accepted: {task.module_id}", flush=True),
            config=args.config,
        )
    except (ValueError, RuntimeError) as error:
        print(
            f"Stopped: {with_notes(error)}\nRetained work is in {prepared.directory}",
            file=sys.stderr,
        )
        return 1
    spent = Budget(prepared.plan.provider_cap_usd, prepared.directory / "live").spent
    print(f"Report:   {report}\nCharged:  USD {spent}")
    if not args.no_library:
        _refresh_library(prepared.directory)
    print("Automated checks only: review the handoffs against the sources before relying on this.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
