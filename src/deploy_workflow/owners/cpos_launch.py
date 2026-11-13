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
from collections import Counter
from collections.abc import Mapping, Sequence
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
from deploy_workflow import confidence, platform_io
from deploy_workflow.changes import (
    DELIVERED_WHOLE,
    PACK_NAME,
    PRIOR_PREFIX,
    PriorRun,
    describe,
    describe_run,
    find_prior,
    prior_sources,
    same_period,
    workspace_of,
)
from deploy_workflow.changes_check import cp8_issues
from deploy_workflow.context import CONTEXT_SOURCE_ID, RunContext, load_context
from deploy_workflow.credit_os_catalogue import chart_row, period_order
from deploy_workflow.docx_text import docx_text
from deploy_workflow.handoff_delivery import (
    DeliveryRequest,
    HandoffInput,
    MarkdownLayout,
    MarkdownRoute,
)
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
from deploy_workflow.model.handoff import (
    BYTES_PER_TOKEN_BOUND,
    REQUEST_OVERHEAD,
    WEB_SEARCH_CALLS_PER_TURN,
    WEB_SEARCH_CASE_KINDS,
    Check,
    _pages,
    web_search_offered,
)
from deploy_workflow.model.pricing import (
    ContextTooLong,
    price_of,
    request_reservation_usd,
    web_search_usd,
)
from deploy_workflow.model.turn import MODEL_EFFORTS, dump_json
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.owners import cp2g, cpos_forecast
from deploy_workflow.owners.cpos import (
    WEB_SEARCH_GRANT,
    HandoffPlan,
    HandoffTask,
    run_live_handoffs,
    web_search_ruled,
    web_search_run,
    with_notes,
)
from deploy_workflow.prose_checks import (
    DATA_MODULES,
    READER_HEADINGS,
    figure_issues,
    key_figures_issues,
    prose_issues,
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


_SKILLS = "docs/reuse/selected-methods/skills/"
_VII = "src/deploy_vii/methods/"
# The Confidence Score rules `confidence_score.py` applies; the script cannot run in this transport.
_SCORE = "docs/reuse/selected-methods/CANON_SHARED.md § CP_CONFIDENCE_SCORE.md"
# The method each module runs, per METHODOLOGY-REVIEW.md and what the 2026-11-05 live campaigns
# consumed. prompts/CP-0.md and CP-1-intake.md are TDG case instructions, so they are left out.
# Owner, 2026-11-10 ("Fix all"): each skill is sent every companion its SKILL.md calls mandatory
# or binding (a runbook, a phase's method bundle), copied from cp-os at b57a344 and listed in
# docs/reuse/selected-methods/manifest.json. Companions the SKILL opens only "to resolve an
# ambiguity" (the schema and system references) are archived, not sent. CANON_SHARED.md is sent
# only as the two reader-layer sections of READER_LAYER, to every prose module (ruling
# 2026-11-11, decision 8); the rest of it is archived.
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
    # Owner, 2026-11-11: the Short Credit Snapshot's one page, read from CP-1's handoff alone.
    "CP-L10": (_VII + "cpl10.md",),
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
    # Owner, 2026-11-11: what has changed since the last run (replaces the deliverable comparison).
    "CP-8": (_VII + "cp8.md",),
    "CP-DR": (
        _SKILLS + "cp-dr-deep-research/SKILL.md",
        _SKILLS + "cp-dr-deep-research/references/REF_CP-DR_STEPS.md",
        _SKILLS + "cp-os-credit-os/references/CP_DR_RESEARCH_BRIEF_V1.md",
        _VII + "cpdr.md",
    ),
}
_CANON = "docs/reuse/selected-methods/CANON_SHARED.md"
# The reader-facing layer every prose module is sent (not the data modules).
READER_LAYER = (
    f"{_CANON} § Reader-facing research layer",
    f"{_CANON} § Credit-research reading order",
)
METHODS: dict[str, tuple[str, ...]] = {
    module: (
        *((*paths, _SCORE) if any(p.startswith(_SKILLS) for p in paths) else paths),
        *(() if module in DATA_MODULES else READER_LAYER),
    )
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
# The user's Microsoft 365 Copilot custom instruction (supplied 2026-11-05, every clause kept),
# plus the one line the 2026-11-11 ruling (decision 8) adds: a persona that applies to every module.
READER_PERSONA = (
    "You are a senior credit research analyst at a leading credit fund, specialising in high "
    "yield credit and leveraged loans. Your research is used throughout the firm for key "
    "investment decisions; it is presented to senior credit committees and affects portfolio "
    "management. Your findings are institutional-grade, deeply analytical and data-dense, fully "
    "reasoned with explicit links from data to risk to credit implication. Say nothing generic "
    "unless it is tied to issuer-specific mechanics. Write in a detailed, structured style "
    "grounded in the provided data, and say when information is insufficient. State explicitly "
    "when information comes from external sources. Lead with the judgement; use data to support "
    "it, not to narrate it.\n\n"
)
# Reader passages (ruling 2026-11-11, H1-H3, decision 8): the checker enforces the mechanical
# checks of `prose_checks`, not the judgement.
PROSE_PASSAGES = (
    "Reader passages. The reader is a portfolio manager or credit committee member who has not "
    "read the source documents. After the analysis is finished, open `## Findings` with these "
    "four sections, each exactly once, in this order, before any other `## Findings` content:\n"
    "- `### Bottom line`: one or two paragraphs. The first sentence states this module's view "
    "and its consequence for creditors, in at most 45 words. Start it with a word, not a figure "
    "or a symbol. The whole Bottom line is at most 180 words.\n"
    "- `### Key findings`: one paragraph or one list item per finding, each starting with the "
    "judgement; give figures only where they move the view.\n"
    "- `### Contrary evidence and what would change the view`: prose giving the strongest "
    "evidence against the view and what would change it.\n"
    "- `### Limitations`: a bulleted list, one limitation per item, each saying which "
    "conclusion it changes and how. A limitation that changes no conclusion goes in the "
    "`## Gaps` table instead; if no limitation changes a conclusion, write one item naming "
    "this module: `- No limitation changes the conclusions of <plain module name>.` CP-OS "
    "refuses a limitation that any handoff accepted earlier in "
    "this run already states, so word each limitation for this module's own conclusion.\n"
    "Everything else in `## Findings` (method sections, registers, tables, report selectors) "
    "follows `### Limitations`; registers are written as tables, and all of its content is "
    "exact. If this module is blocked, write only "
    "`### Bottom line` of these four sections; a blocked module's `### Bottom line` begins "
    "exactly `Not assessable: ` followed by why (the exact words that mark it blocked), and a "
    'module that is not blocked must not use the words "not assessable" in its Bottom line. '
    "The report selectors below are still each written exactly once even if blocked: a "
    "table selector keeps its exact table header with one row stating not assessable "
    "(as a table row, in its table), and a prose selector holds one sentence saying so. Where the "
    "credit-research reading order's opening H3 or front sequence (the 90-150 word view, "
    "quantified drivers and front metrics table) differs from these passages, these passages "
    "govern; its table and appendix rules still apply after `### Limitations`, except that the "
    "report selectors' exact headings and table headers govern over the reader layer's table "
    "rules (6 columns and 8 body rows).\n\n"
)
DATA_PASSAGE = (
    "Reader passage. The reader is a portfolio manager or credit committee member who has not "
    "read the source documents. Open `## Findings` with `### Bottom line`: one or two "
    "paragraphs whose first sentence states this module's view and its consequence for "
    "creditors, in at most 45 words; the whole Bottom line is at most 180 words. If this module "
    "is blocked, its `### Bottom line` begins exactly "
    "`Not assessable: ` followed by why (the exact words that mark it blocked); a module that "
    'is not blocked must not use the words "not assessable" in its Bottom line. Your tables '
    "follow as the main content, unchanged and exact.\n\n"
)
# Display names of the modules, the same pairs as `groups` in apps/issuer-library/credit_os/web/
# screen.js (a test compares them). Decision 11 of 2026-11-12: a module is named in prose by this
# name, never by its code, and the launcher sends the list so the model does not invent names.
MODULE_NAMES = {
    "CP-0": "Source readiness",
    "CP-1A": "Business & governance",
    "CP-DR": "Research questions",
    "CP-1": "Financial foundation",
    "CP-1B": "Earnings changes",
    "CP-L10": "Short credit snapshot",
    "CP-1D": "Earnings quality",
    "CP-1C": "Peer benchmark",
    "CP-2D": "Liquidity",
    "CP-3C": "Refinancing & LME",
    "CP-2": "Fundamental credit",
    "CP-2A": "Downside",
    "CP-2G": "Forward credit model",
    "CP-2E": "Rates, FX & hedging",
    "CP-2H": "Ratings & triggers",
    "CP-4": "Legal & covenants",
    "CP-4A": "Covenant capacity",
    "CP-4B": "Structural priority",
    "CP-4D": "Intercreditor control",
    "CP-4C": "Recovery & fulcrum",
    "CP-3": "Security selection",
    "CP-3D": "Market-implied risk",
    "CP-6": "Committee decision",
    "CP-5": "Evidence validation",
    "CP-8": "Changes since the last run",
}
VOICE_RULES = (
    "- Write evidence, risk mechanism and credit implication as ordinary sentences, never as "
    "labels (no `Evidence:`, `Mechanic:` or `Implication:` lead-ins). This overrides method "
    "templates that write `Evidence:`, `Risk Mechanic:`, `Credit Implication:` or similar "
    "labels in prose or registers: write those as sentences.\n"
    "- In the reader passages write no module code, page number, bracket, chip, hash, or "
    "table, register or calculation ID in a sentence. Name a source in words only when it "
    "matters to the argument.\n"
    "- End a paragraph or list item that rests on a source, an upstream handoff or a "
    "calculation with a Basis line: its last line, with no blank line before it, starting "
    "exactly `Basis: `, items separated by `; `, with an optional final full stop. An item is "
    "`<source file name>`, `<source file name>, page <n>` or `<source file name>, pages "
    "<n>–<m>` (the file name exactly as listed in `## Sources`); `<plain module name> (<code>)` "
    "for an upstream handoff, for example `Liquidity (CP-2D)`; or `calculation <id>` for a row "
    "of this handoff's `## Calculations`, whose table has a column headed `ID` or ending ` ID` "
    "holding that id. A paragraph that rests on none of these has no Basis line. Write the "
    "Basis line on one line, never wrapped.\n"
    "- In the reader passages give every figure its currency or unit, with at most two "
    "decimals: `USD 1,250 million`, `$3.2bn`, `3.1x`, `61 bp`, `45%`, `18 months`. The accepted "
    "units are exactly: %, x, bp, bps, basis points, percentage points, pp, times, notch(es), "
    "day(s), week(s), month(s), quarter(s), year(s), or a currency code or symbol before the "
    "figure; the scale words thousand, million, billion, trillion, k, m and bn are accepted "
    "only with a currency. Any other number (a count of 100 or more, a model, section or "
    "index number) does not belong in a reader sentence: reword it in words or put it in a "
    "table. Never round an exact value to fit the two-decimal rule: an exact value with more "
    "decimals stays in a table. A coupon with more than two decimals (6.375%) is named by "
    'the note\'s maturity and rank instead ("the 2029 secured notes"). Keep a figure and its '
    "currency on one line. Years, dates, "
    "period labels (`Q3`, `FY2024`, `LTM`, `9M`) and whole counts below 100 need no unit. "
    "Write a range with the unit on both ends (`100 bp to 150 bp`). This overrides any method "
    "rule against bare figures or for `{ref|unit}` references in text fields: those belong to "
    "the JSON transport.\n"
    "- Every figure in a reader passage must also appear in the handoff's tables or "
    "`## Calculations` with the same sign, unit and scale.\n"
    "- In reader passages, when the documents do not state an item, say so in words; the "
    "`[Insufficient Information]` tag belongs in tables only. In sentence text write "
    '"not established" in plain words instead of the tag.\n'
    "- A table that cites sources has a column headed `Source` naming the file and page in the "
    "Basis item form. Raw locators, hashes and IDs stay in `## Sources`, "
    "tables and Basis lines. Write a register as a table; a register written as bullets or prose "
    "follows the sentence rules (no bracket tag, no page locator, no ID).\n"
    "- Keep `## Request` to the issuer, as-of date, pathway and scope, in at most three "
    "sentences.\n"
    "- When you quote year-end net debt, net leverage or cash from Financial foundation and its "
    "`Post-balance-sheet adjustments` table has a row for an event, state the pro forma figure "
    "beside it, with its unit and the event's date. When the table says none was found, add "
    "nothing. When Financial foundation does not state the pro forma figure, say it is not "
    "established; never work one out yourself.\n"
    "- In every sentence under `## Findings`, `## Calculations` and `## Gaps`, write for the "
    "reader, not for the pipeline. Write no module code, page locator, bracket or hash, and "
    'none of these words: "handoff", "this transport", "the pack", "fact pack", "source pack", '
    '"canonical", "re-anchor", "helper script", "upstream module", "downstream" before module, '
    "owner, work, analysis or use, a snake_case token or a CAPS_WITH_UNDERSCORE token. Name "
    "the document (for example the 2024 annual report), the module by its plain name or the "
    "analysis instead. Tables, fenced blocks, Basis lines and the chart, map, event and "
    "forecast input sections are not sentence text.\n"
    "- Refer to another module only by its plain name from this list, never by its code or "
    "an invented name: "
    + "; ".join(MODULE_NAMES.values())
    + ". In a Basis item the form stays `<plain module name> (<code>)`.\n"
    "\n"
)
# Sent only to a module that is asked for a chart table or a map (decision 11 of 2026-11-12).
CHART_NOTE_RULE = (
    "After each `### Chart data:` table write one sentence stating the main qualification a "
    'reader needs to read the figures correctly, or "No qualification." if there is none.\n\n'
)
MAP_TEXT_RULE = "Text in a map node or edge is at most 60 characters.\n\n"
# Sent only to a module whose method carries the score (decision 9 of 2026-11-12).
CONFIDENCE_RULE = (
    f"Write the inputs for your confidence score in `### {confidence.HEADING}`, listed with the "
    "report selectors below; the score and band are computed from it by Python, and the section "
    "is a data section, not sentence text. A blocked module writes one row in it instead, "
    "`| Not assessable | Not supplied: <reason> |`, and no score is computed.\n\n"
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
    prior: PriorRun | None = None  # The earlier run CP-8 compares with, when one is listed.
    changes: str = ""  # The one line the run records about that comparison.


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


def read_documents(folder: Path) -> Reading:
    """What the launcher makes of each file in ``folder``, before any context exists. Writes
    nothing; refuses a folder or file the launcher would refuse, with the launcher's own text."""
    source = Path(folder).expanduser().resolve()
    _, _, ignored, covers = _issuer_files(source, source.parent / ".no-context", source.parent)
    return Reading(_documents(covers)[1], ignored)


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

    heading: str
    value_columns: tuple[str, ...]
    chart_unit: str
    steps: bool = False
    rules: str = ""  # The catalogue guard for the view, sent to the module with the table.
    # A row table (debt stack, headroom, limits) states its own header up to the Reporting unit:
    # `numbers` are plain numbers or a stated gap (`in_unit`, default all, are in the Reporting
    # unit); `choices` fix a column's words; `may_gap` text columns may be a stated gap; `ranked`
    # is a column of whole numbers that must not fall down the rows.
    columns: tuple[str, ...] = ()
    numbers: tuple[str, ...] = ()
    in_unit: tuple[str, ...] = ()
    choices: tuple[tuple[str, tuple[str, ...]], ...] = ()
    may_gap: tuple[str, ...] = ()
    ranked: str = ""
    noun: str = "period"
    dates: tuple[str, ...] = ()  # YYYY-MM-DD calendar dates (or a stated gap).
    ordered: tuple[str, ...] = ()  # Stated numbers that must not fall left to right.
    counts: tuple[str, ...] = ()  # Whole numbers of zero or more (or a stated gap).
    not_before: tuple[str, ...] = ()  # (later, earlier) date columns: the first may not precede.
    one_unit: bool = False  # Every row states the same Reporting unit (one scale for the figure).
    series: str = ""  # A column whose distinct words are the figure's series, at most MAX_SERIES.
    unique: tuple[str, ...] = ()  # Columns whose values together name a row once.
    optional: bool = False  # The module writes the table only if the handoff supplies its case.
    events: bool = False  # A dated-event table: no unit or basis columns; dates by precision.
    edges: bool = False  # A node/edge map table: no unit or basis columns; an edge type's words.
    none_text: str = (
        ""  # The words of an Event cell that states none: the one row `_states_none` takes.
    )
    scored: bool = False  # The confidence inputs table: its rows are `confidence`'s, not columns.

    @property
    def bare(self) -> bool:
        """A table with no Reporting unit or Basis and limitation columns."""
        return self.events or self.edges


NET_DEBT_HEADING = "Net debt data"  # not a `Chart data:` heading: the library does not draw it
NET_DEBT = OwnerTable(
    NET_DEBT_HEADING,
    ("Gross debt", "Cash", "Net debt"),
    "US$m",
    rules=(
        "Gross debt is the total debt principal as the issuer reports it, and the Basis and "
        "limitation cell says what gross debt includes (for example securitization, finance "
        "leases). Cash is the same figure as the Cash column of the `Chart data: liquidity` table "
        "for that period. Net debt is gross debt less cash, worked with `calculate` and listed in "
        "`## Calculations`. Write one row per period you state, at least the latest balance-sheet "
        "date. `Period` is the fiscal period `FY2024`, the balance-sheet date `2024-09-30`, or "
        "both as `FY2024 / 2024-09-30`: one of these forms for every row of the table, each "
        "period once, and no other word in the cell (say `pro forma` or `reported` in the Basis "
        "and limitation cell). A row whose three figures are all stated is refused if net debt "
        "differs from gross "
        "debt less cash by any amount, and a row is refused if its cash differs from the "
        "liquidity table's for the same period; a figure you cannot state is "
        "`Not supplied: <reason>`."
    ),
)


def _decimal(cell: str) -> Decimal | None:
    return Decimal(cell.replace(",", "")) if PLAIN_NUMBER.fullmatch(cell) else None


def _unorderable_period(lines: list[str], rows: list[list[str]]) -> str | None:
    """The Period cell that keeps the pack from ordering the net debt table, or None when the
    table orders. The pack's own reader (`chart_row`) decides; only its ValueError is caught. The
    cell named is the first the reader's `period_order` rejects, else the first whose form differs
    from the first row's or that repeats an earlier one; a row of the wrong width is
    `chart_issues`'s, not this check's."""
    try:
        chart_row(lines, NET_DEBT_HEADING, prefix="")
    except ValueError:
        pass
    else:
        return None
    ordered: list[tuple[str, tuple[int, ...]]] = []
    for row in (r for r in rows[2:] if len(r) == len(rows[0])):
        key = period_order(row[0])
        if key is None:
            return row[0]
        ordered.append((row[0], key))
    for number, (period, key) in enumerate(ordered):
        if key[0] != ordered[0][1][0] or any(key == earlier for _, earlier in ordered[:number]):
            return period
    return None


def _net_debt_issues(text: str) -> tuple[str, ...]:
    """Each stated row of the net debt table holds net debt = gross debt - cash exactly, and its
    cash is the liquidity table's for the same period; its Period cells are ones the pack can
    order. A figure that is not stated is not checked; the table's own shape is `chart_issues`'s."""
    heading, liquidity = f"### {NET_DEBT_HEADING}", "### Chart data: liquidity"
    lines = text.splitlines()
    rows = _stated_rows(text, heading) if heading in lines else []
    if not rows or rows[0] != _chart_header(NET_DEBT):
        return ()
    liquid = _stated_rows(text, liquidity) if liquidity in lines else []
    cash_of = [(row[0], row[1]) for row in liquid[2:] if len(row) == 5 and liquid[0][1] == "Cash"]
    issues = []
    unordered = _unorderable_period(lines, rows)
    if unordered is not None:
        issues.append(
            f"`{heading}` Period `{unordered}` cannot be ordered: write `FY2024`, `2024-09-30` or "
            "`FY2024 / 2024-09-30`, one form for the whole table and each period once; put any "
            "other word in the Basis and limitation cell."
        )
    for row in rows[2:]:
        if len(row) != len(rows[0]):
            continue
        period, gross, cash, net = (row[0], *(_decimal(c) for c in row[1:4]))
        if gross is not None and cash is not None and net is not None and net != gross - cash:
            issues.append(
                f"`{heading}` {period}: net debt {row[3]} is not gross debt {row[1]} less cash "
                f"{row[2]}; correct the row, nothing is filled in for you."
            )
        for other, shown in cash_of:
            stated = _decimal(shown)
            if (
                cash is not None
                and stated is not None
                and same_period(period, other)
                and cash != stated
            ):
                issues.append(
                    f"`{heading}` {period}: cash {row[2]} is not the Cash {shown} stated "
                    f"for {other} in `{liquidity}`; correct whichever is wrong, and let this row's "
                    "Period carry the balance-sheet date so it matches one liquidity row."
                )
    return tuple(issues)


POST_BS_NONE = "None found in the sources read"
POST_BS = OwnerTable(
    "Post-balance-sheet adjustments",
    (),
    "",
    columns=("Event", "Date", "Amount", "Pro forma net debt", "Pro forma net leverage"),
    numbers=("Amount", "Pro forma net debt", "Pro forma net leverage"),
    in_unit=("Amount", "Pro forma net debt"),
    dates=("Date",),
    noun="event",
    none_text=POST_BS_NONE,
    rules=(
        "One row per event after the balance-sheet date that changes net debt, such as an issue, "
        "repayment, acquisition, disposal or dividend that the sources state. Date is the event "
        "date: YYYY-MM-DD only when the source states the day; when it gives only a month, "
        "quarter or year, write `Not supplied: the source states <what it gives> only` and never "
        "invent a day. Amount is the event's effect on net debt, a plain number without a sign "
        "when net debt rises and with a minus sign when it falls; Pro forma net debt is "
        "year-end net debt after the event, both in the Reporting unit; Pro forma net leverage is "
        "the same net debt over the same EBITDA as the year-end net leverage, as times without "
        "an `x`. "
        "Work each figure with `calculate`; a figure you cannot state is `Not supplied: "
        "<reason>`; Basis and limitation names the event's source and what is not yet reflected. "
        "Do not add a pro forma row to any chart or net debt table."
    ),
)


def _owner_tables(module: str, routes: Sequence[MarkdownRoute]) -> tuple[OwnerTable, ...]:
    """The tables a module is asked for beside its report routes. CP-1 is on every pathway asked
    for all four chart tables CP-8's pack reads (owner, 2026-11-12, "Yes, all pathways"): those
    its report's chart blocks do not already route are asked as owner tables, with no new
    report section. It is also asked for the net debt table (owner, 2026-11-12, "Yes, add it")."""
    tables = OWNER_TABLES.get(module, ())
    if module != "CP-1":
        return tables
    routed = {r.heading for r in routes}
    chart = tuple(
        OwnerTable(h, cols, unit) for h, cols, unit in CHART_TABLES.values() if h not in routed
    )
    return (*chart, NET_DEBT, POST_BS, *tables)


DIRECTIONS = ("Passes below", "Passes at or below", "Passes above", "Passes at or above")


# The catalogue's launcher-asked figures (docs/visualisations/catalogue.csv) that are not report
# strip figures: S.5 (CP-1-V05), the liquidity bridge (CP-2D-V01) and the refinancing need
# (CP-3C-V01).
OWNER_TABLES: dict[str, tuple[OwnerTable, ...]] = {
    "CP-1": (
        OwnerTable(
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
        OwnerTable(
            "Chart data: debt stack",
            (),
            "US$m",
            rules=(
                "Rows run in legal rank order, most senior first. Ranking is the legal rank as "
                "a plain whole number (1 is most senior; equal ranks share a number); a "
                "facility whose legal rank no source states is left out and named under Gaps. "
                "Secured is Yes or No. Cumulative leverage is the stated cumulative debt "
                "through that facility over the common EBITDA denominator, as times without an "
                "`x`; state it only for a positive common EBITDA denominator, else "
                "`Not supplied: <reason>`. Name each facility's guarantor or obligor scope in "
                "Basis and limitation. An enterprise value is not a sourced fact merely because "
                "it is a chart marker: add no enterprise value row unless a source states it."
            ),
            columns=("Facility", "Ranking", "Secured", "Amount", "Cumulative leverage"),
            numbers=("Amount", "Cumulative leverage"),
            in_unit=("Amount",),
            choices=(("Secured", ("Yes", "No")),),
            ranked="Ranking",
            noun="facility",
        ),
        OwnerTable(
            "Chart data: EBITDA bridge",
            ("Amount",),
            "US$m",
            steps=True,
            rules=(
                "The first row is the reported measure and the last row is the specified "
                "adjusted measure the method names; name both in Basis and limitation. The "
                "rows between are the signed adjustments the method states, each as stated: do "
                "not manufacture intermediate adjustments from the endpoints. If the method "
                "states only the endpoints, or its adjustments do not reconcile them, write "
                "`Not supplied: <reason>` in every Amount."
            ),
        ),
    ),
    "CP-2H": (
        OwnerTable(
            "Chart data: rating triggers",
            (),
            "",
            rules=(
                "Agency names the agency and Trigger the trigger as the agency states it; "
                "Threshold and Current are the same metric on the same basis, in the Reporting "
                "unit; Direction says which side passes (the trigger is not reached). No rating "
                "probability is stated or implied. Where only a synthetic-source frame exists, "
                "write `Not supplied: <reason>` in Threshold and Current and state the "
                "synthetic-source limitation in Basis and limitation; name the agency basis of "
                "an agency-adjusted metric."
            ),
            columns=("Agency", "Trigger", "Threshold", "Current", "Direction"),
            numbers=("Threshold", "Current"),
            choices=(("Direction", DIRECTIONS),),
            noun="trigger",
        ),
    ),
    "CP-4": (
        OwnerTable(
            "Chart data: covenant headroom",
            (),
            "",
            rules=(
                "One row per covenant test the handoff settles. Preserve the quantity and the "
                "strictness of each test: Direction says which side passes, as the covenant "
                "defines it. Threshold and Current are the same quantity in the Reporting unit. "
                "Headroom is the stated headroom with its unit, as the method states it, never "
                "worked out here. The chart is not a legal compliance opinion."
            ),
            columns=("Test", "Threshold", "Current", "Headroom", "Direction"),
            numbers=("Threshold", "Current"),
            choices=(("Direction", DIRECTIONS),),
            may_gap=("Headroom",),
            noun="test",
        ),
    ),
    "CP-6": (
        OwnerTable(
            "Chart data: portfolio limits",
            (),
            "",
            rules=(
                "Rows come from the selected portfolio evaluation: Current exposure, Proposed "
                "exposure and Limit value are its stated figures in one Reporting unit; name the "
                "NAV denominator in Basis and limitation. Proposed exposure is `Not supplied: "
                "<reason>` when no proposal is evaluated. This module owns the interpretation; "
                "delivery only renders it. Do not state invented holdings or a new analytical "
                "owner's result."
            ),
            columns=("Limit", "Current exposure", "Proposed exposure", "Limit value"),
            numbers=("Current exposure", "Proposed exposure", "Limit value"),
            noun="limit",
        ),
    ),
    "CP-2D": (
        OwnerTable(
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


PAIR_COLUMNS = ("Measure", "Prior period", "Prior", "Current period", "Current")
PAIR_GAPS = ("Prior period", "Current period")
PEER_COLUMNS = ("Metric", "Issuer", "Peer low", "Peer median", "Peer high", "Peer count")
PEER_NUMBERS = PEER_COLUMNS[1:]
PEER_BOUNDS = PEER_COLUMNS[2:5]
YIELD_COLUMNS = (
    "Instrument",
    "Maturity date",
    "Yield",
    "Spread",
    "Quote date",
    "Source class",
)


def _peer_range(heading: str, rules: str) -> OwnerTable:
    return OwnerTable(
        heading,
        (),
        "",
        rules=rules,
        columns=PEER_COLUMNS,
        numbers=PEER_NUMBERS,
        in_unit=PEER_NUMBERS[:-1],
        ordered=PEER_BOUNDS,
        counts=("Peer count",),
        noun="metric",
    )


PEER_RULES = (
    "Issuer, Peer low, Peer median and Peer high are the stated values of the method's settled "
    "observations; Peer count is the number of included peers behind the range, a plain "
    "number. Name the excluded peers, each with its reason, in Basis and limitation. A value "
    "that is not settled is `Not supplied: <reason>`, never zero. No other dispersion statistic "
    "is stated. "
)
# The catalogue's other launcher-asked figures: CP-1B (EU.1, EU.2), CP-1C (RV.3a, RV.3b), CP-3D
# (RV.1, a report strip figure that delivery does not ask for as a chart).
OWNER_TABLES |= {
    "CP-1B": (
        OwnerTable(
            "Chart data: prior and current results",
            (),
            "",
            rules=(
                "Pair only compatible quantities: Prior and Current are the same measure on a "
                "comparable perimeter and duration, otherwise `Not supplied: <reason>`. Every "
                "row states one Reporting unit; margin belongs on a separate percent panel, not "
                "in this table. Name the EBITDA identity (reported, issuer-adjusted or "
                "house-adjusted) in Basis and limitation. Prior period and Current period are "
                "the periods as the source labels them."
            ),
            columns=PAIR_COLUMNS,
            numbers=PAIR_COLUMNS[2::2],
            may_gap=PAIR_GAPS,
            one_unit=True,
            noun="measure",
        ),
        OwnerTable(
            "Chart data: margin and KPI changes",
            (),
            "",
            rules=(
                "A margin (the method's T1B.1 margin) and any sourced segment or KPI pair the "
                "handoff actually supplies; do not invent a KPI series. Prior and Current are "
                "the stated values, in the Reporting unit the row states. Percent change and "
                "percentage-point change remain distinct: no change is stated, and it is "
                "not worked out here. One row is one pair, a comparison and not a trend."
            ),
            columns=PAIR_COLUMNS,
            numbers=PAIR_COLUMNS[2::2],
            may_gap=PAIR_GAPS,
            noun="measure",
        ),
    ),
    "CP-1C": (
        _peer_range(
            "Chart data: peer range \u2014 percent metrics",
            PEER_RULES + "Percent metrics only (EBITDA margin, FFO / debt); multiples stay out "
            "of the percent table.",
        ),
        _peer_range(
            "Chart data: peer range \u2014 multiples",
            PEER_RULES + "Multiples only (total leverage, coverage); name the issuer and peer "
            "definitions in Basis and limitation, and do not calendarise or FX-convert peers. "
            "Percentages stay out of this table.",
        ),
    ),
    "CP-3D": (
        OwnerTable(
            "Chart data: yield against maturity",
            (),
            "",
            rules=(
                "One row per instrument with a quote. Yield is on the one yield measure named in "
                "Basis and limitation; YTM, discount margin and spread are never mixed in one "
                "table, so a row on another measure is `Not supplied: <reason>` in Yield. "
                "Spread is stated as the source gives it, with its unit. Maturity date and "
                "Quote date are YYYY-MM-DD dates; Source class names the quote's source class."
            ),
            columns=YIELD_COLUMNS,
            numbers=("Yield",),
            may_gap=("Spread",),
            dates=("Maturity date", "Quote date"),
            not_before=("Maturity date", "Quote date"),
            noun="instrument",
        ),
    ),
}

# CP-4C (DR.2 to DR.5). A value allocation is a step table the bridge check reads unchanged: the
# first row is the enterprise value (the opening), the costs and each class's distribution are the
# negative changes, and the last row is the value not distributed (the closing), so the opening
# plus the changes reconcile to it exactly. Available value is the running position after the
# costs and is stated in the text, not as a row the check would add twice.
MAX_SERIES = 3
ALLOCATION_RULES = (
    " Scenario identity is the label of its source valuation row; name it in Basis and "
    "limitation of the first row. The first row is the enterprise value as stated. The next rows "
    "are the costs and deductions, each a negative change. Then each class's distribution is a "
    "negative change, in the order the method states them: assume no legal pool order. The last "
    "row is the value not distributed after the last distribution (0 when all is allocated), so "
    "that the first row plus the changes reconcile to it. Available value is the running position "
    "after the costs: state it in Basis and limitation of the last cost row, not as a row. Do "
    "not invent an absent downside or stress case."
)


def _allocation(scenario: int) -> OwnerTable:
    ask = " Ask for this scenario only if the handoff supplies it." if scenario > 1 else ""
    rest = ALLOCATION_RULES if scenario == 1 else " The rules of scenario 1 apply."
    return OwnerTable(
        f"Chart data: value allocation \u2014 scenario {scenario}",
        ("Amount",),
        "US$m",
        steps=True,
        rules=f"Scenario {scenario} of the handoff's valuation rows.{ask}{rest}",
        optional=scenario > 1,
    )


OWNER_TABLES["CP-4C"] = (
    OwnerTable(
        "Chart data: recovery by class",
        (),
        "",
        rules=(
            "One row per class and scenario the handoff supplies; do not invent an absent "
            "downside or stress case. Claim and Recovery are the stated amounts in the Reporting "
            "unit, one unit for every row. Recovery % is the recovery percentage as the owner "
            "states it, a plain number without a percent sign, never worked out here from "
            "Recovery and Claim. Cap a recovery only as the method caps it; keep the entity and "
            "collateral pools and the legal limitations in Basis and limitation. This is the "
            "single enterprise value slice, not a complete multi-entity waterfall. At most 3 "
            "distinct scenarios, as the value allocation has three."
        ),
        columns=("Class", "Scenario", "Claim", "Recovery", "Recovery %"),
        numbers=("Claim", "Recovery", "Recovery %"),
        in_unit=("Claim", "Recovery"),
        one_unit=True,
        series="Scenario",
        unique=("Class", "Scenario"),
        noun="class and scenario",
    ),
    *(_allocation(n) for n in (1, 2, 3)),
)


# Package 5: one dated-event table asked of each lane's owning module (the Calendar tab draws a lane
# per module that supplies one). Lane name and catalogue guard; the header and checks are shared.
EVENT_COLUMNS = (
    *("Event date", "Date precision", "Published", "Event"),
    *("Status", "Source", "Credit relevance"),
)
EVENT_RULES = (
    "One row per dated event the handoff states. Event date is written at the precision the "
    "source gives and Date precision names it: `day` YYYY-MM-DD, `month` YYYY-MM, `quarter` "
    "YYYY-Qn, `year` YYYY. Never write a day the source does not state, and infer no day from a "
    "coarser date. Published is the publication date (YYYY-MM-DD) when it differs from the event "
    "date, else `\u2014` (never repeat the event date there). Status starts with `Historical`, "
    "`Scheduled` or `Scenario`, then ` \u2014 ` and the source's own words, e.g. `Scenario \u2014 "
    "modelled downgrade trigger`. Record each event once, in the lane of the module that owns "
    "it; another module refers to it in Credit relevance, it does not repeat the row. Source "
    "names the document and locator; Credit relevance says why the event matters. An event "
    "with no stated date has no row. A user-entered reminder's Status is `User reminder`. "
)
EVENT_LANES: dict[str, tuple[str, str]] = {
    "CP-0": (
        "Sources",
        (
            "Publication date, reporting period and import timestamp are different dates; the "
            "Event date is the date the event states, never the import timestamp. Unknown dates "
            "stay unplaced."
        ),
    ),
    "CP-1A": (
        "Issuer history",
        (
            "Separate announced, completed, cancelled and subsequent events in Status; never "
            "fold a later payment into an earlier financial period."
        ),
    ),
    "CP-1B": (
        "Earnings and guidance",
        (
            "Reporting-period end is not the release date. No guessed next earnings date: a future "
            "date only if the source explicitly schedules it."
        ),
    ),
    "CP-DR": (
        "Research catalysts",
        (
            "Retained supplied evidence only, with the impacted consumer in Credit relevance; "
            "date-free themes stay a watchlist, not a row."
        ),
    ),
    "CP-2D": (
        "Financing",
        (
            "Maturities, dated obligations and funding-gap windows. Maturity is not a refinancing "
            "commitment. Do not double-count a facility CP-1 and CP-3C both state."
        ),
    ),
    "CP-2E": (
        "Hedges",
        (
            "Hedge expiries and dated terms the handoff actually retains. Notional is not "
            "effectiveness or fair value. No row without a stated date."
        ),
    ),
    "CP-2H": (
        "Ratings",
        (
            "Separate an observed rating action, a scheduled review and a modelled trigger in "
            "Status. A historical action only if the handoff states it."
        ),
    ),
    "CP-3": (
        "Instruments",
        (
            "Sourced maturity, call/put, coupon/reset and offer deadlines, with the security "
            "identity in Event. Do not create coupon schedules or option-exercise assumptions. "
            "Unknown dates stay unplaced."
        ),
    ),
    "CP-3C": (
        "Refinancing",
        (
            "Source-dated maturities, call windows and explicit deadlines. Show analyst milestones "
            "separately from contractual deadlines, in Status; preserve contingent triggers."
        ),
    ),
    "CP-4": (
        "Legal",
        (
            "A fixed deadline only when the source or legal module establishes the triggering date "
            "and calculation; otherwise state the relative condition under Gaps, with no dated row."
        ),
    ),
    "CP-6": (
        "Decision and watch",
        (
            "Explicit decision and assigned review dates with sources. Undated conditions stay a "
            "watchlist. A user-entered reminder is labelled `User reminder` in Status, separate "
            "from a sourced issuer event."
        ),
    ),
}
for _module, (_lane, _guard) in EVENT_LANES.items():
    OWNER_TABLES[_module] = (
        *OWNER_TABLES.get(_module, ()),
        OwnerTable(
            f"Events: {_lane}",
            (),
            "",
            rules=EVENT_RULES + _guard,
            columns=EVENT_COLUMNS,
            choices=(("Date precision", ("day", "month", "quarter", "year")),),
            events=True,
        ),
    )


DASHES = ("\u2014", "-", "\u2013")  # An Evidence cell that is only a dash states nothing.
EDGE_COLUMNS = ("From", "Relationship", "Edge type", "To", "Evidence")
EDGE_RULES = (
    "One row per edge the handoff states, From and To each one named node: the same name for the "
    "same node in every row. Edge type is exactly one of the words listed; Relationship and "
    "Evidence are stated in your own words from the source, never blank. No weights, "
    "probabilities, coordinates or likelihoods; no edge the handoff does not state. "
)
FACTS = ("Documentary Fact", "Management Language", "Analyst Interpretation")
NARROW = (
    "The current narrow registers alone do not establish a complete graph: draw an edge only "
    "from the broader handoff, with the applicable document and jurisdiction in Evidence. "
)
# Heading, owner, edge types, the catalogue guard (docs/visualisations/catalogue.csv).
MAPS: tuple[tuple[str, str, tuple[str, ...], str], ...] = (
    (
        "Map: ownership and control",
        "CP-1A",
        ("Ownership", "Legal control", "Guarantee", "Other stated"),
        (
            "Undisclosed percentages stay unknown. Ownership, legal control and guarantees use "
            "different labelled edges. No inferred sponsor willingness."
        ),
    ),
    (
        "Map: operating model to credit",
        "CP-1A",
        (*FACTS, "Insufficient Information"),
        (
            "Evidence to mechanism to credit implication; every edge stated in the handoff. No "
            "weighted cash-flow arrows without amounts."
        ),
    ),
    (
        "Map: credit-risk transmission",
        "CP-2",
        (*FACTS, "Insufficient Information"),
        (
            "Driver to mechanism to creditor outcome. Only stated causal links, in qualitative "
            "categories. Do not invent likelihood or impact coordinates."
        ),
    ),
    (
        "Map: stress scenario",
        "CP-2A",
        ("Assumption", "Test outcome", "Explanation"),
        (
            "Branches describe computed conditions, not probabilities. No forecast date from a "
            "static stress."
        ),
    ),
    (
        "Map: legal entities",
        "CP-4",
        ("Ownership", "Guarantee", "Security", "Structural claim"),
        NARROW + "Require explicit edges, applicable document and jurisdiction.",
    ),
    (
        "Map: intercreditor",
        "CP-4",
        ("Payment rank", "Security rank", "Enforcement control", "Standstill", "Release"),
        NARROW + "Economic ranking and enforcement control are different edges; no numerical "
        "recovery without CP-4C inputs.",
    ),
    (
        "Map: support and contradiction",
        "CP-5",
        ("Supports", "Contradicts", "Unresolved"),
        (
            "Labelled edges for support, contradiction and unresolved between claim, source and "
            "derived-fact identities. No automatic causal or confidence weight based on edge count."
        ),
    ),
)
CONFIDENCE = OwnerTable(confidence.HEADING, (), "", scored=True)
for _module, _paths in METHODS.items():
    if _SCORE in _paths:  # The method carries the score the module may not state: it states inputs.
        OWNER_TABLES[_module] = (*OWNER_TABLES.get(_module, ()), CONFIDENCE)
for _heading, _module, _types, _guard in MAPS:
    OWNER_TABLES[_module] = (
        *OWNER_TABLES.get(_module, ()),
        OwnerTable(
            _heading,
            (),
            "",
            rules=f"{EDGE_RULES}Edge type words: {', '.join(_types)}. {_guard}",
            columns=EDGE_COLUMNS,
            choices=(("Edge type", _types),),
            edges=True,
        ),
    )


def _owner_table(table: MarkdownRoute | OwnerTable) -> OwnerTable:
    if isinstance(table, OwnerTable):
        return table
    return OwnerTable(
        table.heading,
        table.value_columns,
        str(table.chart_unit),
    )


def _chart_header(table: MarkdownRoute | OwnerTable) -> list[str]:
    spec = _owner_table(table)
    first = "Step" if spec.steps else "Period"
    leading = list(spec.columns) or [first, *spec.value_columns]
    if spec.bare:
        return leading
    return [*leading, "Reporting unit", "Basis and limitation"]


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


def _stated_gap(cell: str) -> bool:
    return cell.startswith(NOT_SUPPLIED) and bool(cell.removeprefix(NOT_SUPPLIED).strip())


def _number_issue(spec: OwnerTable, name: str, cell: str, unit: str) -> str | None:
    if _stated_gap(cell):
        return None
    if not PLAIN_NUMBER.fullmatch(cell):
        return f"{name} `{cell}` must be a plain number or `Not supplied: <reason>`."
    if spec.chart_unit and name in (spec.in_unit or spec.numbers) and unit != spec.chart_unit:
        return (
            f"{name} in {unit} cannot be charted as {spec.chart_unit}; "
            f"write `Not supplied: reported in {unit}`."
        )
    return None


def _iso_date(cell: str) -> bool:
    try:
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", cell)) and bool(date.fromisoformat(cell))
    except ValueError:
        return False


def _order_issue(spec: OwnerTable, header: list[str], row: list[str]) -> str | None:
    """The stated numbers of `ordered` columns must not fall left to right (a gap is skipped)."""
    stated = [
        row[header.index(n)] for n in spec.ordered if PLAIN_NUMBER.fullmatch(row[header.index(n)])
    ]
    values = [Decimal(cell.replace(",", "")) for cell in stated]
    if values == sorted(values):
        return None
    return f"{' <= '.join(spec.ordered)} must hold in that order; stated {', '.join(stated)}."


def _dates_issue(spec: OwnerTable, header: list[str], row: list[str]) -> str | None:
    """A stated maturity before its own quote date is a matured instrument, sent back."""
    later, earlier = (row[header.index(name)] for name in spec.not_before)
    if _iso_date(later) and _iso_date(earlier) and later < earlier:
        return f"{spec.not_before[0]} {later} is before {spec.not_before[1]} {earlier}."
    return None


EVENT_SHAPES = {"month": r"\d{4}-(?:0[1-9]|1[0-2])", "quarter": r"\d{4}-Q[1-4]", "year": r"\d{4}"}
EVENT_STATUS = re.compile(
    r"(?:Historical|Scheduled|Scenario) \u2014 \S|User reminder(?: \u2014 \S|$)"
)
EVENT_KINDS = "Historical, Scheduled or Scenario"
EVENT_FORMS = {"day": "YYYY-MM-DD", "month": "YYYY-MM", "quarter": "YYYY-Qn", "year": "YYYY"}


def _event_issues(spec: OwnerTable, header: list[str], row: list[str]) -> list[str]:
    """An event date must be in the form its precision names, never a coarser or finer one."""
    if not spec.events:
        return []
    cells = dict(zip(header, row, strict=True))
    precision, stated, published = cells["Date precision"], cells["Event date"], cells["Published"]
    issues = []
    if precision in EVENT_FORMS and not _stated_gap(stated):
        legal = (
            _iso_date(stated)
            if precision == "day"
            else re.fullmatch(EVENT_SHAPES.get(precision, ""), stated)
        )
        if not legal:
            issues.append(
                f"Event date `{stated}` must be {EVENT_FORMS[precision]} at precision {precision}."
            )
    if published != "\u2014" and not _stated_gap(published) and not _iso_date(published):
        issues.append(f"Published `{published}` must be YYYY-MM-DD or \u2014.")
    if published == stated:
        issues.append("Published repeats the event date: write \u2014 when it is the event date.")
    if not _stated_gap(cells["Status"]) and not EVENT_STATUS.match(cells["Status"]):
        issues.append(
            f"Status `{cells['Status']}` must start with {EVENT_KINDS} and ` \u2014 `, "
            "or be `User reminder`."
        )
    return issues


def _cell_issue(spec: OwnerTable, name: str, cell: str, unit: str) -> str | None:
    """What is wrong with one cell of a row table, or None. Nothing is repaired or worked out."""
    allowed = dict(spec.choices).get(name)
    if name in ("Basis and limitation", "Reporting unit"):
        issue = None if cell else f"{name} is blank."
    elif spec.edges and name == "Evidence" and cell in DASHES:
        issue = f"{name} `{cell}` is not evidence: write where the source names its source."
    elif name in spec.counts:
        legal = _stated_gap(cell) or re.fullmatch(r"\d+", cell)
        issue = None if legal else f"{name} `{cell}` must be a whole number of 0 or more."
    elif name in spec.numbers:
        issue = _number_issue(spec, name, cell, unit)
    elif name in spec.dates:
        issue = (
            None
            if _stated_gap(cell) or _iso_date(cell)
            else f"{name} `{cell}` must be YYYY-MM-DD; when the source states no day, write "
            "`Not supplied: the source states <what it gives> only`."
        )
    elif allowed is not None:
        issue = None if cell in allowed else f"{name} `{cell}` must be one of {', '.join(allowed)}."
    elif name == spec.ranked:
        legal = re.fullmatch(r"[1-9]\d*", cell)
        issue = None if legal else f"{name} `{cell}` must be a plain positive whole number."
    elif not cell or (_stated_gap(cell) and name not in spec.may_gap):
        issue = f"{name} is blank or not stated."
    else:
        issue = None
    return issue


def _states_none(spec: OwnerTable, header: list[str], rows: list[list[str]]) -> bool:
    """The one escape for every owner table: each row's cells before the Reporting unit (every cell
    of a bare table) are stated gaps, so the module states none; the unit and basis stay stated."""
    tail = 0 if spec.bare else 2
    if spec.none_text and len(rows) == 1 and rows[0][:1] == [spec.none_text]:
        return (
            len(rows[0]) == len(header)
            and all((c in DASHES or _stated_gap(c)) for c in rows[0][1 : len(header) - tail])
            and all(rows[0][len(header) - tail :])
        )
    return bool(rows) and all(
        len(row) == len(header)
        and all(_stated_gap(c) for c in row[: len(row) - tail])
        and all(row[len(row) - tail :])
        for row in rows
    )


def _near_none_issues(spec: OwnerTable, heading: str, event: str) -> list[str]:
    """An Event that is the none text with other case or punctuation is not the none row: it
    would pass as an event with gaps, so the module is told the exact text."""
    if not spec.none_text or event == spec.none_text:
        return []
    if event.casefold().strip(" .") != spec.none_text.casefold():
        return []
    advice = f"`{spec.none_text}` and the other cells as asked; any other Event names an event."
    return [f"`{heading}`: to state that there is no event, write the Event exactly {advice}"]


def _row_table_issues(
    spec: OwnerTable, heading: str, header: list[str], rows: list[list[str]]
) -> list[str]:
    """A row table's rows against its fixed header, cell by cell, in the order stated."""
    issues = []
    ranks = []
    if _states_none(spec, header, rows):
        return []  # The module states none: valid, and nothing is drawn.
    for row in rows:
        if len(row) != len(header):
            issues.append(f"`{heading}` row needs {len(header)} cells: {' | '.join(row)}")
            continue
        issues += _near_none_issues(spec, heading, row[0])
        unit = row[-2]
        for name, cell in zip(header, row, strict=True):
            problem = _cell_issue(spec, name, cell, unit)
            if problem:
                issues.append(f"`{heading}` {row[0] or 'row'}: {problem}")
        issues += [f"`{heading}` {row[0]}: {p}" for p in _event_issues(spec, header, row)]
        order = _order_issue(spec, header, row) if spec.ordered else None
        if order:
            issues.append(f"`{heading}` {row[0]}: {order}")
        matured = _dates_issue(spec, header, row) if spec.not_before else None
        if matured:
            issues.append(f"`{heading}` {row[0]}: {matured}")
        if spec.ranked and row[header.index(spec.ranked)].isdecimal():
            ranks.append(int(row[header.index(spec.ranked)]))
    if ranks != sorted(ranks):
        issues.append(
            f"`{heading}`: rows must run in rank order, most senior first (ranks {ranks})."
        )
    if not rows:
        issues.append(f"`{heading}` needs at least one row.")
    seen = (
        {row[header.index(spec.series)] for row in rows if len(row) == len(header)}
        if spec.series
        else ()
    )
    if len(seen) > MAX_SERIES:
        issues.append(f"`{heading}`: at most {MAX_SERIES} distinct {spec.series} values are drawn.")
    keys = Counter(
        tuple(row[header.index(n)] for n in spec.unique)
        for row in rows
        if spec.unique and len(row) == len(header)
    )
    issues.extend(
        f"`{heading}`: {' / '.join(key)} is stated twice; one row names it once."
        for key, count in sorted(keys.items())
        if count > 1
    )
    if spec.one_unit and len({row[-2] for row in rows if len(row) == len(header)}) > 1:
        issues.append(f"`{heading}`: every row states one Reporting unit, as one scale is drawn.")
    return issues


def _misheaded(text: str, heading: str) -> tuple[str, ...]:
    """An optional table written under a near-miss heading (a hyphen for the dash, other case) is
    sent back naming the exact heading; otherwise its absence is the module's decision."""

    def plain(line: str) -> str:
        return " ".join(re.sub("[\u2010-\u2015-]", "-", line).lower().split())

    near = [line for line in text.splitlines() if plain(line) == plain(f"### {heading}")]
    return (f"Write the heading exactly as `### {heading}`, not `{near[0]}`.",) if near else ()


def _absent_issues(text: str, spec: OwnerTable, heading: str) -> tuple[str, ...]:
    near = _misheaded(text, spec.heading) if spec.optional or spec.bare else ()
    if spec.optional or near:  # An optional case not supplied is not asked for, nor drawn.
        return near
    return (f"Add `{heading}` inside ## Findings, with its table.",)


def _confidence_issues(text: str, heading: str) -> tuple[str, ...]:
    """`confidence` reads the table; a refusal is its reason, nothing is repaired. A blocked
    module's one not-assessable row is the form it was asked to write, so it is no refusal."""
    got = confidence.from_handoff(text)
    if isinstance(got, confidence.Refused) and not got.blocked:
        return (f"`{heading}`: {got.reason}.",)
    return ()


def chart_issues(text: str, table: MarkdownRoute | OwnerTable) -> tuple[str, ...]:
    """A chart table's cells reach the page as they are, so each must already be chart-ready."""
    spec = _owner_table(table)
    heading = f"### {spec.heading}"
    if heading not in text.splitlines():
        return _absent_issues(text, spec, heading)
    if spec.scored:
        return _confidence_issues(text, heading)
    rows = _stated_rows(text, heading)
    header = _chart_header(spec)
    if not rows or rows[0] != header:
        return (f"`{heading}` needs the table headed `| {' | '.join(header)} |`.",)
    if spec.columns:
        return tuple(_row_table_issues(spec, heading, header, rows[2:]))
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


# Every module (owner, 2026-11-10, "Fix all"). Retained run cpos-tdg-sol-medium-all-001 and the
# 2026-11-10 inbox run: CP-1D, CP-3 and CP-5 blocked only for want of an acceptance receipt or a
# helper script's output, neither of which exists in this transport; only CP-2G had been told so.
TRANSPORT_RULES = (
    "Acceptance, helper scripts and entry values in this transport: CP-OS checked every handoff it "
    "supplies before passing it on, and pins each by its sha256. That check is the acceptance, "
    "validation and lineage the method asks of an upstream handoff: do not block for want of an "
    "acceptance receipt, invocation digest, settled-head verification or fresh snapshot. The "
    "method's helper scripts (`prepare_invocation.py`, `validate_handoff.py`, "
    "`completeness_check.py` and any other `scripts/*.py`) cannot be run "
    "here: do each check or calculation yourself, with `calculate` and by the rules in the "
    "method block, and do not block for it. Never mention the scripts, the tooling or anything "
    "that could not be run anywhere in the handoff. Do not state a confidence score, a "
    "confidence band or a QA status: this overrides the method's `qa_status`, confidence score "
    "and band fields, its Audit Summary score and its helper-script steps, so leave those fields "
    "and steps out. Python computes any score and band the report shows; a claim's own "
    "confidence label, where the method asks for one, is still written. A companion file "
    "the method names that "
    "is not in the method block below is unavailable; do not block the module for it. CP-OS "
    "supplies only the handoffs of the modules the registry "
    "names as this module's producers (CP-5: every analyst before it); an upstream module the "
    "method names that is not supplied is unavailable in the same way. Where the method relies on "
    "something unavailable, say in the Limitations passage or under `## Gaps`, in plain words, "
    "what could not be established and why it matters, without naming the file, script or "
    "module code. Nobody can answer a "
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
UNIT_RULE = (
    "State `currency` and `scale` in every block, as the statements print them (`1000` for "
    "thousands, `1` for millions), and state every amount in the block in that one unit "
    "exactly as printed; an amount printed in the other unit is stated as missing, with the "
    "reason, not converted. "
)
FORECAST_BLOCK = (
    f"Forecast inputs: write `{cpos_forecast.HEADING}` inside `## Findings`, holding exactly "
    "one fenced json block and no other fence. You state "
    "inputs only; Python computes every forecast figure, so put no forecast figure in the block. "
    "`currency` is the three-letter code of the currency CP-1's statement tables are printed in "
    "(`USD`, `GBP`, `EUR`), and `scale` is `1` when they print millions of it and `1000` when "
    "they print thousands; every amount in this block is stated in that one currency and unit, "
    "exactly as CP-1 prints it, and Python divides by `scale`, so every published figure is "
    "millions of that currency. Do not convert an amount yourself. "
    + UNIT_RULE
    + '`base` holds exactly these ten operands, each `{"amount": "<decimal>", '
    '"reason": null, "row": "<label>", "period": "<header>"}` or '
    '`{"amount": null, "reason": "<why CP-1 does not state it>"}`: '
    f"{', '.join(cp2g.OPERAND_METRIC)}. "
    "`row` is the exact first-cell text of the row of one of the CP-1 handoff's tables that you "
    "read the amount from, and `period` the exact header text of that table's column (for "
    'example `"row": "Net sales", "period": "FY2024"`). Name the cell of every operand that has '
    "an amount: `row` and `period`, or in a table with one row per period (CP-1's `Chart data:` "
    "tables and `Net debt data`) `row` and `column`, the row being the period exactly as printed "
    'and the column the measure\'s exact header (`{"amount": "<decimal>", "reason": null, '
    '"row": "FY2024", "column": "Cash"}`); leave out `period` there. '
    "Those tables are in US$ million: at `scale` 1000 do not name them; state that operand as "
    "missing with the reason. "
    "`interest` is interest paid in cash in the base period; where CP-1 prints only interest "
    "expense you may name that cell and must say in `scope_limits` that interest is interest "
    "expense, not cash paid. "
    'Copy the amount as that cell prints it (with `"scale": 1000` a cell printing '
    '2,620,995 is `"2620995"`; at most nine digits and one decimal place); for interest, taxes '
    "and capex "
    "write the positive magnitude whatever sign the cell shows; for working capital write the "
    "cell's value with its sign reversed (a cell printing (45), an investment, is 45; a cell "
    "printing 45 or +45, a release, is -45). A figure in CP-1's prose, a basis line or its "
    "sources is not a cell: an amount CP-1 prints in no table cell is stated as missing, with "
    "the reason. An amount CP-1 prints only in the other unit (for example revolver availability "
    "in millions where the statements are in thousands) is stated as missing, with the "
    "reason; do not rescale it. Where CP-1 prints the amount under more than one column, name "
    "a column headed by a reporting period (`FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`): the "
    "Forecast page shows history only for a line named under such a header, or in a row "
    "labelled with one. `base_drivers` is "
    "the method's base-case driver "
    "submission (revenue_growth, ebitda_margin, capex_pct_revenue, tax_wc_pct_revenue, "
    "interest_rate, dividends, debt_repayment; each with `values` for the three forecast years, "
    "`category`, `rationale` and `limitation`). Each driver's `values` are three decimal strings, "
    'one per forecast year (for example ["0.05", "0.04", "0.03"]), each rounded to at most four '
    'decimal places (a ratio of 0.48022670 is written "0.4802"); the `dividends` and '
    '`debt_repayment` values are amounts in the block\'s unit (with `"scale": 1000`, 20 '
    'million is `"20000"`, at most one decimal place) and every other driver is a ratio and is '
    "never scaled; `category` is exactly one of "
    f"{', '.join(f'`{c}`' for c in get_args(Category))}. When the method gives no forecast "
    "(for example a blocked dependency), still write the block, with every driver's `values` as "
    "`[null, null, null]`. `downside_shock` is "
    '`{"ebitda_decline": "<0 to 1>", "rate_increase": "<0 to 1>"}` from the CP-2A '
    "scenario, or null when no shock was supplied; Python applies it to the base drivers. "
    "`upside_drivers` and `downside_drivers` are your own upside and downside cases: each holds "
    "only the drivers that differ from base, in the same driver form (every other driver is "
    "inherited from base), or null when you set no such case. "
    "`facilities` is optional: state it when CP-1 prints the debt facilities' balances and rate "
    "terms, otherwise write null. Each row is "
    '`{"name", "balance", "fixed_rate_pct", "spread_pct", "floor_pct", "reference_rate", '
    '"annual_amortisation", "maturity"}`. `balance` is in the block\'s unit and `fixed_rate_pct`, '
    "`spread_pct` and `floor_pct` are percents, each copied exactly as CP-1 prints it; CP-1 must "
    'print each rate with its % sign (a 9.500% coupon is "9.500"). A fixed-rate facility states '
    "`fixed_rate_pct` and null for the other rate fields; a floating-rate facility states "
    "`spread_pct`, `floor_pct` or null, and `reference_rate`, your assumed reference rate for "
    "each forecast year as three decimal fractions "
    '(4% is "0.04", not "4"); the reference rate (or the floor, when higher) plus the spread '
    "must be between 0% and 30% in every year. The facilities' "
    "scheduled repayments over the three years must not exceed base debt. "
    "`annual_amortisation` is in the block's unit, a year, or null when CP-1 states none; "
    "`maturity` is YYYY-MM-DD or null. A row's `balance` is its drawn principal. Leave out a "
    "facility whose balance CP-1 prints only in the other unit. At most 40 rows; names are "
    "unique ignoring case; balances may total at most 1.25 times base debt; `fixed_rate_pct` is "
    "at most 30, `spread_pct` at most 20 and `floor_pct` at most 10; `reference_rate` values have "
    "at most four decimal places. When `facilities` is stated Python computes cash interest on "
    "those facilities and scheduled repayment from it; debt not in a row bears interest at your "
    "`interest_rate` driver and is not repaid; the `debt_repayment` driver is not used, so do "
    "not vary it in `upside_drivers` or `downside_drivers`. "
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
    "transport: do each check yourself, with `calculate`, and do not mention the scripts in the "
    "handoff. That, and the lack of an acceptance receipt for a handoff "
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
# Goes into CP-1's instructions whenever a forecast is wanted, with or without CP-2G: the period
# table lets Python date-check the last twelve months. CP-1 states no new figure in it.
PERIOD_TABLE_BLOCK = (
    "Period table: inside `## Findings`, print one table whose header is exactly "
    "`| Period | Start | End |`, with one row for every period column header you use in your "
    "financial tables. `Period` is that header's text exactly as you print it (for example "
    "`9M 2025` or `FY2024`); `Start` and `End` are the period's first and last day as "
    "YYYY-MM-DD. Head period columns as `FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`, the year "
    "being the fiscal year the period belongs to. Print each statement line once, in one table "
    "that has a column for every period you state for it; a line split across two tables "
    "cannot be combined. Where a table states its unit, write it as the three-letter currency "
    "code and `millions` or `thousands` (`USD millions`), the same in every statement table. "
    "Python uses this table to check that the "
    "last twelve months are twelve months and to date a balance printed under an `LTM Qn YYYY` "
    "label; add no figure to it. Where another table labels a row or column `LTM Qn YYYY`, give "
    "that exact label a row in this table with its Start and End dates. "
    "Print a balance (debt, cash, undrawn facilities) at a period's end under that period's "
    "column as a plain number: the `H1 2025` column holds the 30 June 2025 balance. Put the date "
    "in the row label or the Source, not in the cell.\n\n"
)
# Goes into CP-1's instructions when the forecast is published without CP-2G (owner, 2026-11-11:
# "allow forecast to function with just relevant layer 1 modules"). Same JSON shape as
# FORECAST_BLOCK, so cpos_forecast has one code path; the model still computes nothing.
LAYER1_FORECAST_BLOCK = (
    f"Forecast inputs: write `{cpos_forecast.HEADING}` inside `## Findings`, holding exactly "
    "one fenced json block and no other fence, after your tables. You state inputs only; Python "
    "computes every forecast figure, so put no forecast figure in the block. `currency` is the "
    "three-letter code of the currency your statement tables are printed in (`USD`, `GBP`, "
    "`EUR`), and `scale` is `1` when they print millions of it and `1000` when they print "
    "thousands; every amount in this block is stated in that one currency and unit, exactly as "
    "your tables print it, and Python divides by `scale`, so every published figure is millions "
    "of that currency. Do not convert an amount yourself. "
    + UNIT_RULE
    + '`base` holds exactly these ten operands, each `{"amount": "<decimal>", "reason": null, '
    '"row": "<label>", "period": "<header>"}` or '
    '`{"amount": null, "reason": "<why you do not state it>"}`: '
    f"{', '.join(cp2g.OPERAND_METRIC)}. `row` is the exact first-cell text of the row of one of "
    "your own tables that you read the amount from, and `period` the exact header text of that "
    'table\'s column (for example `"row": "Net sales", "period": "FY2024"`). '
    "Name the cell of every operand that has an amount: `row` and `period`, or in a table with "
    "one row per period (your `Chart data:` tables and `Net debt data`) `row` and `column`, "
    "the row being the period exactly as printed and the column the measure's exact header "
    '(`{"amount": "<decimal>", "reason": null, "row": "FY2024", "column": "Cash"}`); leave out '
    "`period` there. "
    "Those tables are in US$ million: at `scale` 1000 do not name them; state that operand as "
    "missing with the reason. "
    "`interest` is interest paid in cash in the base period; where CP-1 prints only interest "
    "expense you may name that cell and must say in `scope_limits` that interest is interest "
    "expense, not cash paid. "
    'Copy the amount as that cell prints it (with `"scale": 1000` a cell printing 2,620,995 is '
    '`"2620995"`; at most nine digits and one decimal place); for interest, taxes and capex '
    "write the positive magnitude whatever sign the cell shows; for working capital write the "
    "cell's value with its sign reversed (a cell printing (45), an investment, is 45; a cell "
    "printing 45 or +45, a release, is -45). Print your tables as "
    "you normally would; add nothing for this block. A figure in prose, a basis line or the "
    "sources is not a cell. An amount your tables print only in the other unit is stated as "
    "missing, with the reason. Where your tables print the amount under more than one column, "
    "name a column headed by a reporting period (`FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`): "
    "the Forecast page shows history only for a line named under such a header, or in a row "
    "labelled with one. "
    "`base_drivers` is a run-rate base case and nothing more "
    "(revenue_growth, ebitda_margin, capex_pct_revenue, tax_wc_pct_revenue, interest_rate, "
    "dividends, debt_repayment; each with `values` for the three forecast years, `category`, "
    "`rationale` and `limitation`). Anchor every driver to a figure you state: carry the latest "
    "year's ratio forward, or use a scheduled maturity or a declared payment, and name the anchor "
    "in `rationale`. Add no analyst judgement beyond that run-rate. Each driver's `values` are "
    'three decimal strings, one per forecast year (for example ["0.05", "0.04", "0.03"]), each '
    "rounded to at most four decimal places; the `dividends` and `debt_repayment` values are "
    'amounts in the block\'s unit (with `"scale": 1000`, 20 million is `"20000"`, at '
    "most one decimal place) and every other driver is a ratio and is never scaled; `category` "
    "is exactly one of "
    f"{', '.join(f'`{c}`' for c in get_args(Category))}. Leave a driver's values null, as "
    "`Insufficient Information`, when no stated figure can anchor it; when none can, set every "
    "driver's `values` to `[null, null, null]`. Set `downside_shock`, `upside_drivers` and "
    "`downside_drivers` to null: there are no cases and no shock in this forecast. `years` is "
    'three consecutive fiscal years after the base period, each `{"year": <int>, "start": '
    '"YYYY-MM-DD", "end": "YYYY-MM-DD"}`. `scope_limits` is a list of text limits. Set '
    f"`schema_version` to `{cpos_forecast.SCHEMA_VERSION}`. This block does not change your "
    "findings or any table.\n\n"
)


# Goes into CP-8's instructions: which earlier run it compares with and where the pack is.
CP8_BLOCK = (
    "This run compares with an earlier run of the same issuer and pathway: {prior}. The "
    "comparison pack is source `changes.json` and the earlier run's delivered handoffs are the "
    "sources `prior/<module>.md`; the current run's handoffs are supplied as usual. Write the "
    "registers exactly as the method says. CP-OS checks every issuer row that holds a figure "
    "against the pack measure it names, every difference you print against the pack's, every "
    "module and every limitation ref of the pack for exactly one row, and the fixed Status and "
    "Cause lists, and sends the handoff back if one fails. The earlier run's handoffs and the "
    "pack are evidence for this module alone.\n"
    "For this module the Basis item forms above are replaced by these three: `<plain module "
    "name> (<code>)` for a handoff of this run, `<plain module name> (<code>), earlier run` for "
    "a handoff of the earlier run, and `Run comparison` for the comparison pack, with no page "
    "for a handoff. The files `changes.json` and `prior/<module>.md` are listed in `## "
    "Sources` and are never named in a Basis line.\n\n"
)
BRIDGE_RULES = (
    " Each row is one step: the first row is the opening amount and the last row is the closing "
    "amount; the rows between are the signed changes the method states (a negative number for an "
    "outflow), in the order the method states them. The opening plus those changes must reconcile "
    "to the closing at the precision the table states, or the table is sent back: state the "
    "missing step, never a plug. If the bridge cannot be stated, write `Not supplied: <reason>` "
    "in every Amount."
)


CURRENCY_RULE = (
    "An issuer reporting in another currency or scale writes "
    "`Not supplied: reported in <unit>` in monetary cells. "
)


def _and_list(names: Sequence[str]) -> str:
    return f"{', '.join(names[:-1])} and {names[-1]}" if len(names) > 1 else "".join(names)


def _none_rule(spec: OwnerTable) -> str:
    """The one sentence every row table (not a step table, which has its own) is sent for the case
    that its module has nothing to report; `_states_none` accepts exactly that row."""
    if not spec.columns:
        return ""
    if spec.none_text:
        return (
            f" If no such event is stated, write one row whose Event is exactly `{spec.none_text}` "
            f"(no other punctuation or wording), whose {_and_list(spec.columns[1:])} are each "
            "`\u2014`, with Reporting unit and Basis and limitation stated (say which sources "
            "were read)."
        )
    cells = "every cell" if spec.bare else "every cell before Reporting unit"
    return (
        f" If the handoff supplies none, write one row whose {cells} is `Not supplied: <reason>`"
        f"{'' if spec.bare else ', with Reporting unit and Basis and limitation stated'}: "
        "the module "
        "states none, and the page shows it as not established for this run."
    )


def _selector(route: MarkdownRoute | OwnerTable) -> str:
    if isinstance(route, OwnerTable) or route.kind == "chart":
        spec = _owner_table(route)
        if spec.scored:
            return (
                f"- `### {spec.heading}`: exactly one Markdown table headed "
                f"`| {' | '.join(confidence.HEADER)} |`, with one row for each of these inputs, "
                f"named exactly: {', '.join(confidence.INPUT_ROWS)}. "
                f"{', '.join(confidence.LINEAGE_ROWS)} are whole numbers (0 where none) of the "
                "material claims whose strongest evidence is of that lineage class; "
                f"{confidence.PRESENT_ROW} and {confidence.TOTAL_ROW} are whole numbers of the "
                "required fields (the source gate and the method's required schema fields) "
                f"present and in all, {confidence.TOTAL_ROW} at least 1 and not below "
                f"{confidence.PRESENT_ROW}; {confidence.GATE_ROW} is `pass`, `partial` or `fail`; "
                f"{', '.join(confidence.FINDING_ROWS)} are whole numbers of unresolved findings of "
                "that severity. Write no score, band or status."
            )
        if spec.bare:
            return (
                f"- `### {spec.heading}`: exactly one Markdown table headed "
                f"`| {' | '.join(_chart_header(spec))} |`, one row per "
                f"{'edge' if spec.edges else 'dated event'}. "
                f"Every cell is stated, never blank. {spec.rules}{_none_rule(spec)}"
            )
        others = [n for n in spec.numbers if spec.in_unit and n not in spec.in_unit]
        counted = [n for n in spec.numbers if n not in others]
        numbers = f" ({', '.join(counted)})" if counted else ""
        where = "in the Reporting unit the row states"
        if spec.chart_unit:
            where = f"in {spec.chart_unit}, with that as the Reporting unit"
        rest = (
            f" {', '.join(others)} is a plain number in the unit its rule states." if others else ""
        )
        return (
            f"- `### {spec.heading}`: exactly one Markdown table headed "
            f"`| {' | '.join(_chart_header(spec))} |`, one row per "
            f"{'step' if spec.steps else spec.noun}. "
            f"Value cells{numbers} are plain numbers {where}, or `Not supplied: <reason>`.{rest} "
            + (CURRENCY_RULE if spec.chart_unit else "")
            + f"{'Every other cell is stated, never blank. ' if spec.columns else ''}"
            "Basis and limitation is never blank."
            + (BRIDGE_RULES if spec.steps else "")
            + (f" {spec.rules}" if spec.rules else "")
            + _none_rule(spec)
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


CP3_MODE_LABELS = {
    "clo_screening": "CLO Screening",
    "single_name_rv": "Single-Name RV",
    "capital_structure_rv": "Capital-Structure RV",
    "watchlist_monitoring": "Watchlist Monitoring",
}
CP3_MODE_BLOCK = (
    "The user selected the execution mode {label} (source `context`, module_options.cp3_mode). "
    "Use it at Step 1; do not choose another.\n\n"
)
DEEP_DEBATE_BLOCK = (
    "The user explicitly asks for a full debate (source `context`, "
    "module_options.cp6_deep_debate). Deep Debate Mode is ON.\n\n"
)
SOURCES_RULES = (
    "Write the issuer sources in `## Sources` as a table with the columns "
    "`Source | Document | Document date | sha256 | Use`. `Source` is the exact file name as "
    "supplied "
    "(it is the key that joins the row to the file; never shorten or reword it). `Document` says "
    'in plain words what the document is, for example "Annual report on Form 10-K for the year '
    'ended 30 September 2024". `Document date` is the date the document was filed or published '
    'if the document states it, otherwise "not stated". `sha256` is the exact hash and `Use` '
    "says what this module used it for. Do not list the run settings (the context file) as a "
    "source. A web page found by search is listed by the rules of this module's web section, "
    "which add a Source type cell.\n\n"
)
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
        + "A handoff is rejected unless it does all of this:\n"
        f"- name {run.issuer_name} in `## Request`, and state the as-of date {run.as_of} there;\n"
        "- list each issuer source it relied on in `## Sources`, naming the exact file and its "
        "sha256;\n"
        "- list each supplied handoff in `## Sources`, with its module and exact sha256.\n\n"
        + SOURCES_RULES
        + READER_PERSONA
        + (DATA_PASSAGE if module in DATA_MODULES else PROSE_PASSAGES)
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
    Owner, 2026-11-11: CP-DR and CP-2E are in every preset (CP-1C needs CP-DR's peers), so the
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
        ("CP-1", LAYER1_FORECAST_BLOCK, forecast and "CP-2G" not in ordered),
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
        ("CP-6", DEEP_DEBATE_BLOCK, options.cp6_deep_debate),
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
        ordered, tuple(guesses.values()), settings, edges_for(ordered), omitted=omitted
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
        raise LaunchRefused(f"--out {directory}: holds a different request; choose a new --out")
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
    issues = [i for owned in _owner_tables(module, routes) for i in chart_issues(text, owned)]
    return [*issues, *_net_debt_issues(text)] if module == "CP-1" else issues


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
        issues += _owned_issues(task.module_id, routes, text)
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
    return _unstated_currency(inputs)


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
            f"Changes:  {prepared.changes.removeprefix('changes: ') or 'not recorded'}",
            f"Manifest: {prepared.manifest}",
            *_web_line(prepared, config, ruling),
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
        "--prior",
        help="the earlier run to compare with: its run folder name, or `none` for a first run "
        "(the run start service passes what the approval named; default: search)",
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
        prepared = prepare(
            args.context,
            args.sources,
            args.out,
            config=args.config,
            cap=args.cap,
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
    except (ValueError, OSError, LivePauseInForce) as error:
        print(error, file=sys.stderr)
        return 2
    print(_readiness(prepared, args.config, args.ruling), flush=True)
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
        )
    except (ValueError, RuntimeError) as error:
        print(
            f"Stopped: {with_notes(error)}\nRetained work is in {prepared.directory}",
            file=sys.stderr,
        )
        return 1
    spent = Budget(prepared.plan.provider_cap_usd, prepared.directory / "live").spent
    print(f"Delivery: {receipt}\nCharged:  USD {spent}")
    if not args.no_library:
        _refresh_library(prepared.directory)
    print("Automated checks only: review the handoffs against the sources before relying on this.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
