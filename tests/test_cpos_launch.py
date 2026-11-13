"""User-launched CP-OS runs. A fake provider proves wiring only, not model or analytical quality."""

import dataclasses
import hashlib
import json
import os
import re
import types
import typing
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from deploy_vii.registry import plan
from deploy_vii.report_view import ReportView
from deploy_workflow.context import Cp3Mode
from deploy_workflow.handoff_delivery import (
    HEADINGS,
    DeliveryRequest,
    HandoffInput,
    verify_delivery,
)
from deploy_workflow.markdown_delivery import markdown_files
from deploy_workflow.model.adapter import (
    AdapterReply,
    LiveAdapter,
    LivePauseInForce,
    check_ruling,
)
from deploy_workflow.model.handoff import _pages
from deploy_workflow.model.providers import build
from deploy_workflow.model.turn import Compaction, ToolCall, Turn, Usage, hosted_kind
from deploy_workflow.owners import cpos_forecast, cpos_launch
from deploy_workflow.owners.cpos import (
    HandoffPlan,
    HandoffTask,
    RetainedHandoff,
    _checked_handoff,
    _handoff,
    run_live_handoffs,
)
from deploy_workflow.owners.cpos_launch import (
    METHODS,
    LaunchRefused,
    checker,
    main,
    prepare,
    refuse_deactivated,
    without_for,
)
from deploy_workflow.run_events import read_events
from deploy_workflow.run_expectations import RULES, Item

ROOT = Path(__file__).resolve().parents[1]
RULING = ROOT / "docs/rulings/2026-11-05-live-loop-tests.md"  # configs: sol-medium
ISSUER = "Northbridge Synthetic Group"
AS_OF = "2025-03-31"

# Written by hand from the registry's dependency rules and the block titles on the Front Page.
COVENANT_MODULES = (
    *("CP-0", "CP-1", "CP-1A", "CP-DR", "CP-4", "CP-2", "CP-2A", "CP-2E", "CP-2D", "CP-2G"),
    *("CP-3C", "CP-5"),
)
COVENANT_ROUTES = {
    ("covenant-tests-headroom", "CP-4", "Covenant tests and headroom", "table"),
    ("liquidity-runway", "CP-2D", "Liquidity and cash runway", "table"),
    ("funding-gap", "CP-2D", "Funding gap", "table"),
    ("red-flags", "CP-4", "Red flags", "table"),
    ("lender-protection-score", "CP-4", "Lender protection score", "table"),
    ("refinancing-paths", "CP-3C", "Refinancing paths", "table"),
    ("capacity", "CP-4", "Capacity and baskets", "table"),
    ("lme-creditor-exposure", "CP-3C", "LME capacity and creditor exposure", "table"),
    ("ebitda-definition", "CP-4", "EBITDA definition", "table"),
    ("documents-structure", "CP-4", "Documents and structure", "table"),
    ("maturity-wall", "CP-1", "Chart data: debt maturities", "chart"),
}
# Run order for each pathway (registry.plan over the preset, CP-MODEL and CP-8 removed; required
# producers such as CP-1A are added). Owner, 2026-11-11: CP-DR and CP-2E are in every preset except
# the lite credit assessment (listed here) and the deactivated short snapshot (SHORT_SNAPSHOT).
PATHWAY_MODULES = {
    "credit_snapshot": (
        *("CP-0", "CP-1", "CP-1A", "CP-DR", "CP-4", "CP-2", "CP-2A", "CP-2E", "CP-2G", "CP-3"),
        *("CP-5", "CP-6"),
    ),
    "earnings_update": ("CP-0", "CP-1", "CP-1B", "CP-DR", "CP-2E", "CP-1D", "CP-5"),
    "relative_value": (
        *("CP-0", "CP-1", "CP-1A", "CP-3D", "CP-DR", "CP-1C", "CP-2", "CP-2E", "CP-2D", "CP-3C"),
        *("CP-3", "CP-5"),
    ),
    "covenant_refinancing": COVENANT_MODULES,
    "distressed_restructuring": (
        *("CP-0", "CP-1", "CP-1A", "CP-DR", "CP-4", "CP-1C", "CP-2", "CP-2A", "CP-2E", "CP-2G"),
        *("CP-2H", "CP-4C", "CP-5"),
    ),
    "portfolio_decision": (
        *("CP-0", "CP-1", "CP-1A", "CP-DR", "CP-2", "CP-2E", "CP-3", "CP-5", "CP-6"),
    ),
    "lite_credit_assessment": ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-2A"),
}
# The owner's preset answer key (2026-11-11), hand-written as sets: what each pathway requests.
PRESET_ANSWER_KEY = {
    "credit_snapshot": "CP-0 CP-1 CP-MODEL CP-1A CP-DR CP-2 CP-2A CP-2E CP-2G CP-4 CP-3 CP-5 CP-6",
    "earnings_update": "CP-0 CP-1 CP-MODEL CP-1B CP-1D CP-DR CP-2E CP-5",
    "relative_value": "CP-0 CP-1 CP-MODEL CP-1C CP-DR CP-2 CP-2D CP-2E CP-3 CP-3C CP-3D CP-5",
    "covenant_refinancing": (
        "CP-0 CP-1 CP-MODEL CP-1A CP-DR CP-2 CP-2A CP-2D CP-2E CP-2G CP-4 CP-3C CP-5"
    ),
    "distressed_restructuring": (
        "CP-0 CP-1 CP-1A CP-1C CP-DR CP-2 CP-2A CP-2E CP-2G CP-2H CP-4 CP-4C CP-5"
    ),
    "portfolio_decision": "CP-0 CP-1 CP-MODEL CP-DR CP-2 CP-2E CP-3 CP-5 CP-6",
    # Owner, 2026-11-11 ("3. approved"): its own pathway of CP-0, CP-1 and one CP-L10 page; it gets
    # no CP-DR, CP-2E, CP-MODEL or CP-2G.
    "short_snapshot": "CP-0 CP-1 CP-L10",
    # The lite credit assessment (owner): the credit snapshot's CP-1, CP-1A and CP-2 sections plus
    # CP-2A's two downside blocks. No CP-MODEL (ruling 2026-11-13): the chart strip and credit
    # metrics are routed to CP-1 and no forecast is published.
    "lite_credit_assessment": "CP-0 CP-1 CP-1A CP-2 CP-2A",
}
SHORT_SNAPSHOT = ("CP-0", "CP-1", "CP-L10")
# Run order of the lite pathway and its report blocks, written by hand from the Front Page: the
# credit snapshot's blocks that CP-1, CP-1A and CP-2 write, then CP-2A's two downside blocks.
LITE_MODULES = ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-2A")
LITE_BLOCKS = (
    "key-findings",
    "company-operating-model",
    "model-chart-strip",
    "financials-credit-metrics",
    "strengths-weaknesses",
    "company-profile",
    "transaction-summary",
    "downside-stress",
    "break-points",
)
# The credit snapshot's own blocks and modules, unchanged by the lite pathway (hand-written).
FULL_BLOCKS = (
    *("key-findings", "company-operating-model", "model-chart-strip", "capital-structure"),
    *("financials-credit-metrics", "strengths-weaknesses", "relative-value", "company-profile"),
    *("transaction-summary", "portfolio-fit", "committee-challenge", "what-changed"),
)
DEACTIVATED = "The short credit snapshot is deactivated. Use the lite credit assessment."


def context_file(tmp_path: Path, pathway: str = "covenant_refinancing") -> Path:
    data = json.loads((ROOT / "cases/cpdr-context-cutoff/context.json").read_text())
    data["run"].update(pathway=pathway, as_of=AS_OF, cutoff="")
    data["identity"].update(issuer_name=ISSUER, issuer_id="nbg")
    path = tmp_path / "context.json"
    path.write_text(json.dumps(data))
    return path


def issuer_folder(tmp_path: Path) -> Path:
    folder = tmp_path / "issuer"
    (folder / "filings").mkdir(parents=True)
    (folder / "annual.txt").write_text("Net sales were 100.")
    (folder / "filings/notes.md").write_text("Notes mature in 2030.")
    (folder / ".DS_Store").write_bytes(b"\xff\xfe")
    (folder / "chart.png").write_bytes(b"\x89PNG")
    return folder


READER_BOTTOM_LINE = "The synthetic issuer shows one observed item."
# Hand-written and synthetic: they prove the chart path, not any analysis.
CHART_TABLES = {
    "Chart data: leverage": """| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit | Basis and limitation |
| --- | --- | --- | --- | --- |
| FY2023 | 3.75 | 3.00 | x | Synthetic. |
| FY2024 | 2.80 | 2.25 | x | Synthetic. |""",
    "Chart data: interest cover": """| Period | EBITDA / cash interest | Reporting unit | Basis and limitation |
| --- | --- | --- | --- |
| FY2023 | 3.20 | x | Synthetic. |
| FY2024 | 4.00 | x | Synthetic. |""",
    "Chart data: liquidity": """| Period | Cash | Undrawn committed facilities | Reporting unit | Basis and limitation |
| --- | --- | --- | --- | --- |
| FY2023 | 300 | 450 | US$m | Synthetic. |
| FY2024 | 275 | 400 | US$m | Synthetic. |""",
    "Chart data: debt maturities": """| Period | Debt maturing | Reporting unit | Basis and limitation |
| --- | --- | --- | --- |
| FY2026 | 500 | US$m | Synthetic. |
| FY2027 | Not supplied: the schedule stops here | US$m | Synthetic. |
| FY2028 | 1,250 | US$m | Synthetic. |""",
}
NET_DEBT_TABLE = """\
| Period | Gross debt | Cash | Net debt | Reporting unit | Basis and limitation |
| --- | --- | --- | --- | --- | --- |
| FY2023 | 1500 | 300 | 1200 | US$m | Synthetic; gross debt includes finance leases. |
| FY2024 | 1400 | 275 | 1125 | US$m | Synthetic; gross debt includes finance leases. |"""
POST_BS_HEADER = (
    "| Event | Date | Amount | Pro forma net debt | Pro forma net leverage | Reporting unit "
    "| Basis and limitation |"
)
POST_BS_NONE = (
    POST_BS_HEADER
    + "\n| --- | --- | --- | --- | --- | --- | --- |\n"
    + "| None found in the sources read | \u2014 | \u2014 | \u2014 | \u2014 | US$m "
    "| Synthetic; the annual report and its notes were read. |"
)
POST_BS_EVENT = (
    POST_BS_HEADER
    + "\n| --- | --- | --- | --- | --- | --- | --- |\n"
    + "| Notes issued after year end | 2024-11-05 | 500 | 1625 | 3.4 | US$m "
    "| Synthetic; proceeds not yet applied. |"
)
NON_USD_TABLES = {
    "Chart data: liquidity": """| Period | Cash | Undrawn committed facilities | Reporting unit | Basis and limitation |
| --- | --- | --- | --- | --- |
| FY2024 | Not supplied: reported in EUR m | Not supplied: reported in EUR m | EUR m | Synthetic. |""",
    "Chart data: debt maturities": """| Period | Debt maturing | Reporting unit | Basis and limitation |
| --- | --- | --- | --- |
| FY2026 | Not supplied: reported in EUR m | EUR m | Synthetic. |""",
}


# Synthetic and hand-written: the tables an owner module is asked for beside the report's own
# charts (S.5, the liquidity bridge, the refinancing need). They prove the route, not any analysis.
def synthetic_table(header: str, *rows: str) -> str:
    return "\n".join([header, "| --- |" + " --- |" * (header.count("|") - 2), *rows])


# CP-1's checked tables (the acceptance check of CP-1's figures). Synthetic and consistent with the
# net debt table and the chart tables above: reported EBITDA 400 / 500, cash interest 125 / 125,
# total debt and cash as the net debt table states them; every other line is a stated gap. The
# register states each chart figure worked from those operands (two-sided ties, R1), the Period
# cells are the net debt table's, and the reconciliation states only the carrying value.
GAP = "Not supplied: synthetic"
FIGURES = {
    ("T4.4 Income statement", "EBITDA (Reported)"): ("400", "500"),
    ("T4.5 Cash flow statement", "Cash Interest Paid"): ("125", "125"),
    ("T4.6 Balance sheet", "Total Debt"): ("1500", "1400"),
    ("T4.6 Balance sheet", "Cash & Equivalents"): ("300", "275"),
}
CP1_CHECKED = {
    heading: synthetic_table(
        "| Line item | FY2023 | FY2024 | Unit | Basis | Source |",
        *(
            f"| {row} | {' | '.join(FIGURES.get((heading, row), (GAP, GAP)))} "
            "| USD millions | Synthetic. | annual.txt |"
            for row in rows
        ),
    )
    for heading, rows in {
        "T4.4 Income statement": ("EBITDA (Reported)",),
        "T4.5 Cash flow statement": (
            "Net Cash from Operating Activities",
            "Net Cash from Investing Activities",
            "Net Cash from Financing Activities",
            "Net Cash Change",
            "Opening Cash",
            "Closing Cash",
            "Cash Interest Paid",
        ),
        "T4.6 Balance sheet": (
            "Total Assets",
            "Total Liabilities",
            "Total Equity",
            "Total Debt",
            "Cash & Equivalents",
        ),
    }.items()
}
CP1_CHECKED["T4.9 Calculation register"] = synthetic_table(
    "| Metric Name | Formula | Numerator Value | Numerator Source | Denominator Value "
    "| Denominator Source | Period | Currency | Unit | Calculated Value | Calculation Status "
    "| Evidence Quality Tier | Limitations |",
    *(
        f"| {name} | n / d | {num} | annual.txt | {den} | annual.txt | {period} | USD | US$m "
        f"| {value} | Stated | Tier 3 | Synthetic. |"
        for name, rows in (
            ("Total debt / EBITDA", (("1500", "400", "3.75"), ("1400", "500", "2.80"))),
            ("Net debt / EBITDA", (("1200", "400", "3.00"), ("1125", "500", "2.25"))),
            ("EBITDA / cash interest", (("400", "125", "3.20"), ("500", "125", "4.00"))),
        )
        for period, (num, den, value) in zip(("FY2023", "FY2024"), rows, strict=True)
    ),
)
CP1_CHECKED["Debt principal to carrying value"] = synthetic_table(
    "| Period | Contractual principal | Reconciling items | Carrying value | Reporting unit "
    "| Basis and limitation |",
    f"| FY2024 | {GAP} | {GAP} | 1400 | US$m | Synthetic. |",
)
# The Period table the acceptance check needs (R11): the statement columns' dates, so a Net debt
# row dated by the day is found to be a fiscal year (or not).
CP1_CHECKED["Period table"] = synthetic_table(
    "| Period | Start | End |",
    "| FY2023 | 2022-10-01 | 2023-09-30 |",
    "| FY2024 | 2023-10-01 | 2024-09-30 |",
)
PERIOD_HEAD = "| Period | {} | Reporting unit | Basis and limitation |"
DEBT_STACK_HEAD = (
    "| Facility | Ranking | Secured | Amount | Cumulative leverage | Reporting unit "
    "| Basis and limitation |"
)
DEBT_STACK_ROWS = (
    "| Senior secured term loan | 1 | Yes | 1,200 | 2.4 | US$m | Synthetic. |",
    "| Senior notes | 2 | No | 800 | 4.0 | US$m | Synthetic. |",
    (
        "| Subordinated notes | 3 | No | Not supplied: balance not stated "
        "| Not supplied: no balance | US$m | Synthetic. |"
    ),
)
COVENANT_HEAD = (
    "| Test | Threshold | Current | Headroom | Direction | Reporting unit | Basis and limitation |"
)
COVENANT_ROWS = (
    "| Net leverage | 5.0 | 4.2 | 0.8x | Passes at or below | x | Synthetic. |",
    "| Interest cover | 2.0 | 2.6 | 0.6x | Passes at or above | x | Synthetic. |",
    (
        "| Minimum liquidity | 100 | Not supplied: not stated | Not supplied: no current "
        "| Passes at or above | US$m | Synthetic. |"
    ),
)
TRIGGER_HEAD = (
    "| Agency | Trigger | Threshold | Current | Direction | Reporting unit | Basis and limitation |"
)
TRIGGER_ROWS = (
    (
        "| Synthetic agency | Downgrade review: net leverage | 5.5 | 4.2 | Passes below | x "
        "| Synthetic. |"
    ),
)
LIMITS_HEAD = (
    "| Limit | Current exposure | Proposed exposure | Limit value | Reporting unit "
    "| Basis and limitation |"
)
LIMITS_ROWS = (
    "| Single-issuer limit | 3.0 | 4.0 | 5.0 | % NAV | Synthetic. |",
    "| High-yield bucket | 12.0 | Not supplied: no proposal | 15.0 | % NAV | Synthetic. |",
)
PAIR_HEAD = (
    "| Measure | Prior period | Prior | Current period | Current | Reporting unit "
    "| Basis and limitation |"
)
PEER_HEAD = (
    "| Metric | Issuer | Peer low | Peer median | Peer high | Peer count | Reporting unit "
    "| Basis and limitation |"
)
YIELD_HEAD = (
    "| Instrument | Maturity date | Yield | Spread | Quote date | Source class | Reporting unit "
    "| Basis and limitation |"
)
RECOVERY_HEAD = (
    "| Class | Scenario | Claim | Recovery | Recovery % | Reporting unit | Basis and limitation |"
)
ALLOCATION_HEAD = "| Step | Amount | Reporting unit | Basis and limitation |"
ALLOCATION_ONE = "Chart data: value allocation \u2014 scenario 1"
ALLOCATION_TWO = "Chart data: value allocation \u2014 scenario 2"
OWNER_TABLES = {
    "CP-4C": {
        "Chart data: recovery by class": synthetic_table(
            RECOVERY_HEAD,
            "| Senior secured | Base | 1,200 | 1,080 | 90 | US$m | Synthetic. |",
            "| Senior secured | Downside | 1,200 | 720 | 60 | US$m | Synthetic. |",
            "| Unsecured | Base | 800 | 120 | 15 | US$m | Synthetic. |",
            "| Unsecured | Downside | 800 | Not supplied: no downside value "
            "| Not supplied: no downside value | US$m | Synthetic. |",
        ),
        ALLOCATION_ONE: synthetic_table(
            ALLOCATION_HEAD,
            "| Enterprise value | 2,000 | US$m | Synthetic base case. |",
            "| Restructuring costs | -100 | US$m | Synthetic. Available value 1,900. |",
            "| Senior secured distribution | -1,080 | US$m | Synthetic. |",
            "| Unsecured distribution | -120 | US$m | Synthetic. |",
            "| Value not distributed | 700 | US$m | Synthetic. |",
        ),
        ALLOCATION_TWO: synthetic_table(
            ALLOCATION_HEAD,
            "| Enterprise value | 1,500 | US$m | Synthetic downside case. |",
            "| Restructuring costs | -100 | US$m | Synthetic. Available value 1,400. |",
            "| Senior secured distribution | -720 | US$m | Synthetic. |",
            "| Unsecured distribution | -80 | US$m | Synthetic. |",
            "| Value not distributed | 600 | US$m | Synthetic. |",
        ),
    },
    "CP-1B": {
        "Chart data: prior and current results": synthetic_table(
            PAIR_HEAD,
            "| Revenue | FY2023 | 2,100 | FY2024 | 2,250 | US$m | Synthetic. |",
            "| Adjusted EBITDA | FY2023 | 410 | FY2024 | Not supplied: not stated | US$m "
            "| Synthetic. |",
        ),
        "Chart data: margin and KPI changes": synthetic_table(
            PAIR_HEAD,
            "| EBITDA margin | FY2023 | 19.5 | FY2024 | 21.0 | % | Synthetic. |",
            "| Subscribers | FY2023 | 1.2 | FY2024 | 1.4 | m | Synthetic. |",
        ),
    },
    "CP-1C": {
        "Chart data: peer range — percent metrics": synthetic_table(
            PEER_HEAD,
            "| EBITDA margin | 21.0 | 12.0 | 18.5 | 26.0 | 7 | % | Synthetic. |",
            "| FFO / debt | Not supplied: not stated | 8.0 | 15.0 | 22.0 | 6 | % | Synthetic. |",
        ),
        "Chart data: peer range — multiples": synthetic_table(
            PEER_HEAD, "| Total debt / EBITDA | 4.2 | 2.5 | 3.4 | 5.1 | 7 | x | Synthetic. |"
        ),
    },
    "CP-3D": {
        "Chart data: yield against maturity": synthetic_table(
            YIELD_HEAD,
            "| Synthetic 2028 note | 2028-06-15 | 6.4 | +310 bp | 2024-12-31 | Dealer quote "
            "| % | Synthetic. |",
            "| Synthetic 2031 note | 2031-03-01 | Not supplied: no quote "
            "| Not supplied: no quote | 2024-12-31 | Dealer quote | % | Synthetic. |",
        ),
    },
    "CP-1": {
        "Chart data: revenue and EBITDA": synthetic_table(
            PERIOD_HEAD.format("Revenue | Adjusted EBITDA"),
            "| FY2023 | 2,100 | 410 | US$m | Synthetic. |",
            "| FY2024 | 2,250 | Not supplied: the measure is not stated | US$m | Synthetic. |",
        ),
        "Chart data: debt stack": synthetic_table(DEBT_STACK_HEAD, *DEBT_STACK_ROWS),
        "Chart data: EBITDA bridge": synthetic_table(
            "| Step | Amount | Reporting unit | Basis and limitation |",
            "| Reported EBITDA | 410 | US$m | Synthetic. |",
            "| Restructuring add-back | 30 | US$m | Synthetic. |",
            "| Disposal | -10 | US$m | Synthetic. |",
            "| Issuer-adjusted EBITDA | 430 | US$m | Synthetic. |",
        ),
    },
    "CP-2H": {
        "Chart data: rating triggers": synthetic_table(TRIGGER_HEAD, *TRIGGER_ROWS),
    },
    "CP-4": {
        "Chart data: covenant headroom": synthetic_table(COVENANT_HEAD, *COVENANT_ROWS),
    },
    "CP-6": {
        "Chart data: portfolio limits": synthetic_table(LIMITS_HEAD, *LIMITS_ROWS),
    },
    "CP-2D": {
        "Chart data: liquidity bridge": synthetic_table(
            "| Step | Amount | Reporting unit | Basis and limitation |",
            "| Opening accessible liquidity | 900 | US$m | Synthetic. |",
            "| Free cash flow | 120 | US$m | Synthetic. |",
            "| Debt repayment | -450 | US$m | Synthetic. |",
            "| Closing accessible liquidity | 570 | US$m | Synthetic. |",
        ),
    },
    "CP-3C": {
        "Chart data: refinancing need": synthetic_table(
            PERIOD_HEAD.format("Debt maturing | Committed resources"),
            "| FY2026 | 500 | 300 | US$m | Synthetic. |",
            "| FY2027 | 1,250 | Not supplied: no commitment is stated | US$m | Synthetic. |",
        ),
    },
}
# Package 5 (2026-11-10): every lane's dated-event table. Synthetic rows; the answer key is here.
EVENT_HEAD = (
    "| Event date | Date precision | Published | Event | Status | Source | Credit relevance |"
)
EVENT_ROWS = (
    "| 2025-03-31 | day | 2024-11-07 | Synthetic note | Scheduled — matures | Filing p.1 | Wall |",
    "| 2025-06 | month | 2025-05-01 | Synthetic call | Historical — noted | Memo | Cost |",
    "| 2025-Q3 | quarter | 2024-11-07 | Synthetic review | Scenario — modelled | Memo | Rating |",
    "| 2026 | year | 2024-11-07 | Synthetic maturity | Scheduled — maturity | Filing p.2 | Wall |",
)
EVENT_LANES = {  # module -> (lane name, a phrase of its catalogue guard the instructions carry)
    "CP-0": ("Sources", "import timestamp"),
    "CP-1A": ("Issuer history", "never fold a later payment"),
    "CP-1B": ("Earnings and guidance", "No guessed next earnings date"),
    "CP-DR": ("Research catalysts", "date-free themes"),
    "CP-2D": ("Financing", "Maturity is not a refinancing commitment"),
    "CP-2E": ("Hedges", "not effectiveness or fair value"),
    "CP-2H": ("Ratings", "modelled trigger"),
    "CP-3": ("Instruments", "option-exercise"),
    "CP-3C": ("Refinancing", "analyst milestones"),
    "CP-4": ("Legal", "relative condition"),
    "CP-6": ("Decision and watch", "user-entered reminder"),
}
for _module, (_lane, _) in EVENT_LANES.items():
    OWNER_TABLES.setdefault(_module, {})[f"Events: {_lane}"] = synthetic_table(
        EVENT_HEAD, *EVENT_ROWS
    )
# Package 6 (2026-11-10): the node/edge maps. Synthetic rows; vocabularies are the owner's ruling.
EDGE_HEAD = "| From | Relationship | Edge type | To | Evidence |"
FACT_TYPES = ("Documentary Fact", "Management Language", "Analyst Interpretation")
MAPS = {  # heading -> (owner, edge types, phrases of its catalogue guard the instructions carry)
    "Map: ownership and control": (
        "CP-1A",
        ("Ownership", "Legal control", "Guarantee", "Other stated"),
        ("Undisclosed percentages stay unknown", "No inferred sponsor willingness"),
    ),
    "Map: operating model to credit": (
        "CP-1A",
        (*FACT_TYPES, "Insufficient Information"),
        ("No weighted cash-flow arrows without amounts",),
    ),
    "Map: credit-risk transmission": (
        "CP-2",
        (*FACT_TYPES, "Insufficient Information"),
        ("Only stated causal links", "likelihood or impact coordinates"),
    ),
    "Map: stress scenario": (
        "CP-2A",
        ("Assumption", "Test outcome", "Explanation"),
        ("not probabilities", "No forecast date from a static stress"),
    ),
    "Map: legal entities": (
        "CP-4",
        ("Ownership", "Guarantee", "Security", "Structural claim"),
        ("narrow registers alone do not establish a complete", "applicable document"),
    ),
    "Map: intercreditor": (
        "CP-4",
        ("Payment rank", "Security rank", "Enforcement control", "Standstill", "Release"),
        ("narrow registers alone do not establish a complete", "no numerical recovery"),
    ),
    "Map: support and contradiction": (
        "CP-5",
        ("Supports", "Contradicts", "Unresolved"),
        ("edge count",),
    ),
}
for _heading, (_module, _types, _) in MAPS.items():
    OWNER_TABLES.setdefault(_module, {})[_heading] = synthetic_table(
        EDGE_HEAD, f"| Synthetic A | Synthetic link | {_types[0]} | Synthetic B | Synthetic p.1 |"
    )
SCORED = (
    "CP-0",
    "CP-1",
    "CP-1A",
    "CP-1B",
    "CP-1C",
    "CP-1D",
    "CP-2",
    "CP-2A",
    "CP-2D",
    "CP-2E",
    "CP-2G",
    "CP-2H",
    "CP-3",
    "CP-3C",
)
SCORED += ("CP-3D", "CP-4", "CP-4C", "CP-5", "CP-6", "CP-DR")
UNSCORED = ("CP-L10", "CP-8")
CONFIDENCE_ROWS = (
    "| Directly Sourced | 8 |\n| Calculated | 2 |\n| Assumption-Based | 2 |\n"
    "| Analyst Inference | 0 |\n| Weak Lineage | 0 |\n| Untraced | 0 |\n| Conflicting | 0 |\n"
    "| Insufficient Information | 0 |\n| Fields present | 95 |\n| Fields total | 100 |\n"
    "| Source gate | pass |\n| CRITICAL | 0 |\n| MATERIAL | 0 |\n| MINOR | 1 |"
)
for _module in SCORED:  # Every module whose method carries the score writes its inputs table.
    OWNER_TABLES.setdefault(_module, {})["Confidence inputs"] = synthetic_table(
        "| Input | Value |", *CONFIDENCE_ROWS.splitlines()
    )
OWNER_PATHWAY = {
    "CP-3": "portfolio_decision",
    "CP-DR": "relative_value",
    "CP-4C": "distressed_restructuring",
    "CP-2H": "distressed_restructuring",
    "CP-6": "portfolio_decision",
    "CP-1B": "earnings_update",
    "CP-1C": "relative_value",
    "CP-3D": "relative_value",
}
OWNER_HEADERS = {
    "CP-4C": RECOVERY_HEAD,
    "CP-1B": PAIR_HEAD,
    "CP-1C": PEER_HEAD,
    "CP-3D": YIELD_HEAD,
    "CP-1": PERIOD_HEAD.format("Revenue | Adjusted EBITDA"),
    "CP-2D": "| Step | Amount | Reporting unit | Basis and limitation |",
    "CP-3C": PERIOD_HEAD.format("Debt maturing | Committed resources"),
    "CP-2H": TRIGGER_HEAD,
    "CP-4": COVENANT_HEAD,
    "CP-6": LIMITS_HEAD,
}


# Data modules owe only `### Bottom line` (ruling 2026-11-11, H2). A copy, not an import: the
# answer key stays independent of prose_checks.DATA_MODULES.
DATA_MODULE_IDS = frozenset({"CP-0", "CP-PARSE", "CP-1", "CP-1C"})
PASSAGES = (
    "### Key findings\n\nThe synthetic issuer's cover is thin at 3.1x.\n"
    "Basis: annual.txt, page 2\n\n"
    "### Contrary evidence and what would change the view\n\n"
    "Nothing supplied contradicts the view; a USD 1,250 million refinancing would.\n\n"
    "### Limitations\n\n- Synthetic data only in the {case} case, so no conclusion carries "
    "weight.\n"
)


def answer(context: dict, plan_routes: list) -> str:
    lines = [f"# {context['module_id']}", "", "## Request", f"{ISSUER} as of {AS_OF}.", ""]
    lines += ["## Sources", ""]
    lines += [f"- {n} {h}" for n, h in context["sources"].items()]
    lines += [f"- {n} {h['sha256']}" for n, h in context["handoffs"].items()]
    lines += ["", "## Findings", "", "### Bottom line", "", READER_BOTTOM_LINE, ""]
    if context["module_id"] not in DATA_MODULE_IDS:
        # Check 7: one limitation per module. Digits are spelled out: a bare figure in a passage
        # must be held in a table (fidelity check).
        case = context["module_id"].replace("-", " ").lower()
        words = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
        for digit, word in enumerate(words):
            case = case.replace(str(digit), f" {word} ")
        case = " ".join(case.split())
        lines += [*PASSAGES.format(case=case).splitlines(), ""]
    passages = {"Bottom line", "Key findings", "Contrary evidence and what would change the view"}
    own = [r for r in plan_routes if r.module_id == context["module_id"]]
    own = [r for r in own if r.heading not in passages]  # A selector so named is the passage.
    for route in own:
        lines += [f"### {route.heading}", ""]
        if route.kind == "chart":
            lines += [CHART_TABLES[route.heading], ""]
        elif route.kind == "table":
            lines += ["| Item | Value |", "| --- | --- |", "| Observed | 1 |", ""]
        else:
            lines += ["A located finding.", ""]
    if context["module_id"] == "CP-1":  # Every pathway asks CP-1 for all four chart tables.
        routed = {r.heading for r in own}
        for heading, table in CHART_TABLES.items():
            if heading not in routed:
                lines += [f"### {heading}", "", table, ""]
    if context["module_id"] == "CP-1":  # ... and the net debt table (owner, 2026-11-12).
        lines += ["### Net debt data", "", NET_DEBT_TABLE, ""]
        lines += [part for h, t in CP1_CHECKED.items() for part in (f"### {h}", "", t, "")]
        lines += ["### Post-balance-sheet adjustments", "", POST_BS_NONE, ""]
    for heading, table in OWNER_TABLES.get(context["module_id"], {}).items():
        lines += [f"### {heading}", "", table, ""]
    for heading in ("Calculations", "Gaps", "Next module"):
        held = heading == "Calculations" and context["module_id"] not in DATA_MODULE_IDS
        # The passage figures (fidelity check) are held in a table outside the passages.
        table = [
            "| Item | Value |",
            "| --- | --- |",
            "| Cover | 3.1x |",
            "| Refinancing | USD 1,250 million |",
        ]
        lines += [f"## {heading}", "", *(table if held else ["None."]), ""]
    return "\n".join(lines)


@pytest.fixture
def provider(monkeypatch):
    """Fake provider that answers each module and records every call it receives."""
    calls = []
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")

    def complete(self, request, **kwargs):
        context = json.loads(request.messages[1].text)
        calls.append((context["module_id"], self.config_id, request.effort))
        if any(hosted_kind(t) for t in request.tools):
            provider.searched.append(context["module_id"])
        provider.systems.setdefault(context["module_id"], request.messages[0].text)
        # The real provider body builder must accept what the handoff loop sends this model.
        provider.models.add(json.loads(build(self._model, request, "not-a-real-key").body)["model"])
        turn = Turn(
            "",
            (ToolCall(str(len(calls)), "write_handoff", {"markdown": provider.answer(context)}),),
            Usage(
                input_tokens=10,
                cached_read_tokens=0,
                cache_write_tokens=0,
                output_tokens=5,
                reasoning_tokens=0,
            ),
            "tool_use",
            provider.reported,
            "fake",
            200,
            # OpenRouter's charge is the billed amount; the others price from token counts.
            billed_usd=Decimal("0.01") if self.config_id == "deepseek-max" else None,
        )
        return AdapterReply(
            "ok",
            turn,
            None,
            200,
            None,
            None,
            1,
            2,
            turn.usage,
            billed_usd=turn.billed_usd,
            compactions=provider.compactions.get(context["module_id"], ()),
        )

    monkeypatch.setattr(LiveAdapter, "complete", complete)
    provider.calls = calls
    provider.compactions = {}  # module -> the compactions its call reports (Copilot only)
    provider.searched = []
    provider.systems = {}
    provider.models = set()
    provider.reported = "fake"
    provider.answer = lambda context: pytest.fail("no answer set")
    return provider


def launch(tmp_path: Path, *extra: str, pathway: str = "covenant_refinancing") -> list[str]:
    return [
        *("--context", str(context_file(tmp_path, pathway))),
        *("--sources", str(issuer_folder(tmp_path))),
        *("--config", "sol-medium", "--cap", "50", "--out", str(tmp_path / "out")),
        *extra,
    ]


def test_folder_files_are_pinned_and_unusable_ones_reported(tmp_path):
    folder = issuer_folder(tmp_path)
    prepared = prepare(
        context_file(tmp_path), folder, tmp_path / "out", config="sol-medium", cap="50"
    )
    assert set(prepared.plan.sources) == {"annual.txt", "filings/notes.md", "context"}
    assert prepared.plan.sources["annual.txt"].sha256 == (
        hashlib.sha256(b"Net sales were 100.").hexdigest()
    )
    assert prepared.ignored == ("chart.png",)
    # Relative, like the retained manifests, so a run folder still resolves from another checkout.
    pin = prepared.plan.sources["annual.txt"]
    assert not Path(pin.path).is_absolute()
    assert (tmp_path / "out" / pin.path).resolve() == (folder / "annual.txt").resolve()
    assert not Path(prepared.plan.sources["context"].path).is_absolute()


def test_underscore_folders_are_reported_rather_than_silently_dropped(tmp_path):
    folder = issuer_folder(tmp_path)
    (folder / "_archive").mkdir()
    (folder / "_archive/old.txt").write_text("Old filing.")
    prepared = prepare(
        context_file(tmp_path), folder, tmp_path / "out", config="sol-medium", cap="50"
    )
    assert "_archive/old.txt" in prepared.ignored
    assert "_archive/old.txt" not in prepared.plan.sources


@pytest.mark.parametrize(
    ("name", "raw"),
    [
        ("filing.htm", "<html><head><title>Skip</title></head><body><p>Net sales were 100.</p>"),
        ("filings/8-K.HTML", "<html><body><p>Net sales were 100.</p><script>x()</script></body>"),
        ("legacy.html", b"<html><meta charset='windows-1252'><p>Net sales were 100. Caf\xe9</p>"),
    ],
)
def test_html_filings_reach_the_model_as_visible_text(tmp_path, name, raw):
    folder = issuer_folder(tmp_path)
    (folder / name).parent.mkdir(exist_ok=True)
    original = raw if isinstance(raw, bytes) else raw.encode()
    (folder / name).write_bytes(original)
    prepared = prepare(
        context_file(tmp_path), folder, tmp_path / "out", config="sol-medium", cap="50"
    )
    key = name + ".jsonl"
    pinned = (tmp_path / "out" / prepared.plan.sources[key].path).read_bytes()
    assert prepared.plan.sources[key].sha256 == hashlib.sha256(pinned).hexdigest()
    text = "\n".join(_pages(key, pinned))
    assert "Net sales were 100." in text
    assert "<p>" not in text and "x()" not in text and "Skip" not in text
    # The filed document stays identifiable from what the model reads.
    assert name in text and hashlib.sha256(original).hexdigest() in text


def test_word_documents_reach_the_model_as_text(tmp_path):
    from test_docx_text import docx, para

    folder = issuer_folder(tmp_path)
    original = docx(para("<w:t>Net sales were 100.</w:t>"))
    (folder / "lender memo.docx").write_bytes(original)
    prepared = prepare(
        context_file(tmp_path), folder, tmp_path / "out", config="sol-medium", cap="50"
    )
    key = "lender memo.docx.jsonl"
    pinned = (tmp_path / "out" / prepared.plan.sources[key].path).read_bytes()
    assert prepared.plan.sources[key].sha256 == hashlib.sha256(pinned).hexdigest()
    text = "\n".join(_pages(key, pinned))
    assert "Net sales were 100." in text and "<w:" not in text
    assert "lender memo.docx" in text and hashlib.sha256(original).hexdigest() in text
    assert "lender memo.docx" not in prepared.ignored


@pytest.mark.parametrize("html", ["10-K.html", "filings/8-K.HTM"])
def test_html_filing_and_a_file_named_like_its_text_refuse_instead_of_overwriting(tmp_path, html):
    # S01-A01/C03: an HTML filing is pinned as `<name>.jsonl`. Before the fix a real file of that
    # name replaced the filing's entry without a word (the filing vanished from the sources and
    # was not listed as ignored). Expected, by hand: LaunchRefused naming both files and the
    # shared source key, and no request written.
    folder = issuer_folder(tmp_path)
    (folder / html).write_text("<html><body><p>FY2025 revenue 1,234</p></body></html>")
    (folder / f"{html}.jsonl").write_text(json.dumps({"page": 1, "text": "older extract"}) + "\n")
    expected = f"--sources: {html} and {html}.jsonl would both be source {html}.jsonl"
    with pytest.raises(LaunchRefused, match=re.escape(expected)):
        prepare(context_file(tmp_path), folder, tmp_path / "out", config="sol-medium", cap="50")
    assert not (tmp_path / "out" / "workflow.json").exists()


def test_html_filings_use_the_page_size_of_the_cp_os_loop(tmp_path):
    # cp-os PAGE_CHARS is 3,000. convert_html runs prose together (102,760 characters on one line of
    # the TDG 10-K), so long lines are split too, and no read of eight pages passes about 24 KB.
    folder = issuer_folder(tmp_path)
    paragraphs = "".join(f"<p>Line {n} of the filing.</p>" for n in range(5000))
    long_line = "y" * 5000
    (folder / "filing.htm").write_text(f"<html><body>{paragraphs}<p>{long_line}</p></body></html>")
    prepared = prepare(
        context_file(tmp_path), folder, tmp_path / "out", config="sol-medium", cap="50"
    )
    key = "filing.htm.jsonl"
    pages = _pages(key, (tmp_path / "out" / prepared.plan.sources[key].path).read_bytes())
    assert len(pages) > 30
    assert max(map(len, pages)) <= 3000
    text = "".join(pages)
    assert text.replace("\n", "").count("y") == 5000  # Nothing lost where a long line splits.
    assert [f"Line {n} of" in text for n in (0, 2500, 4999)] == [True, True, True]
    assert text.index("Line 0 of") < text.index("Line 2500 of") < text.index("Line 4999 of")


def test_context_file_inside_the_folder_is_not_counted_as_issuer_evidence(tmp_path):
    folder = issuer_folder(tmp_path)
    inside = folder / "context.json"
    inside.write_text(context_file(tmp_path).read_text())
    prepared = prepare(inside, folder, tmp_path / "out", config="sol-medium", cap="50")
    assert set(prepared.plan.sources) == {"annual.txt", "filings/notes.md", "context"}


def blank_pdf(path: Path) -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(100, 100)
    with path.open("wb") as stream:
        writer.write(stream)


@pytest.mark.parametrize(
    ("damage", "reason"),
    [
        (lambda f: (f / "bad.txt").write_bytes(b"\xff\xfe\x00"), "bad.txt"),
        (lambda f: (f / "fake.pdf").write_bytes(b"%PDF-broken"), "fake.pdf"),
        (lambda f: blank_pdf(f / "scan.pdf"), "scan.pdf"),
    ],
)
def test_unreadable_source_refused_before_anything_is_written(tmp_path, capsys, damage, reason):
    argv = launch(tmp_path)
    damage(tmp_path / "issuer")
    assert main(argv) == 2
    assert reason in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("folder", ["missing", "empty", "a-file"])
def test_folder_must_hold_usable_files(tmp_path, capsys, folder):
    (tmp_path / "empty").mkdir()
    (tmp_path / "a-file").write_text("x")
    code = main(
        [
            *("--context", str(context_file(tmp_path)), "--sources", str(tmp_path / folder)),
            *("--config", "sol-medium", "--cap", "50", "--out", str(tmp_path / "out")),
        ]
    )
    assert code == 2
    assert folder in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_context_sets_run_identity_modules_and_report_routes(tmp_path):
    prepared = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    run = prepared.plan.run
    assert (run.issuer_id, run.issuer_name, run.as_of.isoformat()) == ("nbg", ISSUER, AS_OF)
    assert run.pathway == "covenant_refinancing"
    assert "CP-MODEL" not in run.requested_modules
    assert prepared.ordered == COVENANT_MODULES
    assert prepared.plan.execution == "live-provider"
    assert {
        (r.block_id, r.module_id, r.heading, r.kind) for r in prepared.plan.layout.routes
    } == COVENANT_ROUTES
    assert "maturity-wall" not in prepared.omitted


def test_selected_method_and_report_selectors_reach_the_instructions(tmp_path):
    prepared = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    text = (tmp_path / "out" / prepared.plan.instructions["CP-4"].path).read_text()
    method = ROOT / "docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/SKILL.md"
    assert method.read_text() in text
    assert hashlib.sha256(method.read_bytes()).hexdigest() in text
    assert "### Covenant tests and headroom" in text
    assert "search_source" in text  # runs/cpos-launch-live-001 read whole filings unprompted.
    assert ISSUER in text and AS_OF in text


def test_instructions_ask_for_the_reader_passages_and_keep_the_method_verbatim(tmp_path):
    prepared = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    text = (tmp_path / "out" / prepared.plan.instructions["CP-4"].path).read_text()
    assert "### Reader summary" not in text and "Reader summary" not in text
    assert "open `## Findings` with these four sections" in text
    method = ROOT / "docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/SKILL.md"
    assert method.read_text() in text
    assert hashlib.sha256(method.read_bytes()).hexdigest() in text
    assert text.index("`### Bottom line`") < text.index(method.read_text())


def test_explicit_modules_narrow_the_run_and_keep_dependencies(tmp_path):
    prepared = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
        modules=("CP-4",),
    )
    assert prepared.ordered == ("CP-0", "CP-1", "CP-4")
    assert "liquidity-runway" in prepared.omitted


@pytest.mark.parametrize("module", ["CP-MEMO", "CP-OS", "NOPE"])
def test_modules_without_a_launchable_method_are_refused(tmp_path, capsys, module):
    assert main([*launch(tmp_path), "--modules", module]) == 2
    assert module in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("cap", ["0", "-1", "nan", "inf", "lots"])
def test_cap_must_be_a_positive_finite_amount(tmp_path, cap):
    argv = launch(tmp_path)
    argv[argv.index("--cap") + 1] = cap
    with pytest.raises(SystemExit) as stopped:
        main(argv)
    assert stopped.value.code == 2


def test_modules_that_fill_no_report_section_are_refused(tmp_path, capsys):
    # CP-1A has no section in the covenant report, and completion needs a populated deliverable.
    assert main([*launch(tmp_path), "--modules", "CP-1A"]) == 2
    assert "report section" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_cap_too_small_for_one_call_is_refused_offline(tmp_path, capsys):
    # gpt-6.1-sol holds USD 5.73 per call at 32,000 output tokens (seen from the live budget).
    argv = launch(tmp_path)
    argv[argv.index("--cap") + 1] = "5"
    assert main(argv) == 2
    assert "--cap" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_the_offline_cap_check_holds_the_research_modules_search_fee_when_it_will_search(tmp_path):
    # The live loop holds USD 0.16 more for each CP-DR call when the ruling lists web-search
    # (16 calls at USD 0.01; tests/test_handoff_loop.py). The offline check holds the same.
    context, folder = context_file(tmp_path), issuer_folder(tmp_path)

    def hold(cap: str, out: str, **extra: bool) -> Decimal:
        return prepare(
            context,
            folder,
            tmp_path / out,
            config="sol-medium",
            cap=cap,
            modules=("CP-DR",),
            **extra,
        ).hold

    plain = hold("50", "a")
    assert hold("50", "b", web_search=True) - plain == Decimal("0.16")
    between = str(plain + Decimal("0.05"))  # fits one call without search, not with it
    hold(between, "c")
    with pytest.raises(LaunchRefused, match="--cap"):
        hold(between, "d", web_search=True)


def with_case_kind(path: Path, kind: str) -> Path:
    data = json.loads(path.read_text())
    data["run"]["case_kind"] = kind
    path.write_text(json.dumps(data))
    return path


STANDING = ROOT / "docs/rulings/2026-11-11-run-start-submit.md"


def search_holds(tmp_path: Path, kind: str) -> tuple[Decimal, Decimal, list[str], str]:
    """The CP-DR hold without and with the ruling's search, the launcher's argv and its Web line."""
    argv = launch(tmp_path, "--modules", "CP-DR", "--ruling", str(STANDING))
    context = with_case_kind(tmp_path / "context.json", kind)
    holds = [
        prepare(
            context,
            tmp_path / "issuer",
            tmp_path / name,
            config="sol-medium",
            cap="50",
            modules=("CP-DR",),
            web_search=searching,
        ).hold
        for name, searching in (("plain", False), ("search", True))
    ]
    return holds[0], holds[1], argv, kind


def test_a_synthetic_case_holds_no_search_fee_and_the_launcher_says_why(tmp_path, capsys):
    # One rule (model/handoff.py web_search_offered): the offline check holds what the loop holds.
    plain, searching, argv, _ = search_holds(tmp_path, "synthetic")
    assert searching == plain
    assert main(argv) == 0
    assert "Web:      off: synthetic case" in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["public", "private"])
def test_a_public_or_private_case_holds_the_search_fee_and_the_launcher_says_it_searches(
    tmp_path, capsys, kind
):
    plain, searching, argv, _ = search_holds(tmp_path, kind)
    assert searching - plain == Decimal("0.16")
    assert main(argv) == 0
    assert "Web:      CP-DR searches the web" in capsys.readouterr().out


def test_a_ruling_that_lists_web_search_makes_the_command_line_check_the_search_hold(
    tmp_path, capsys
):
    base = launch(tmp_path, "--modules", "CP-DR")
    plain = prepare(
        tmp_path / "context.json",
        tmp_path / "issuer",
        tmp_path / "probe",
        config="sol-medium",
        cap="50",
        modules=("CP-DR",),
    )
    base[base.index("--cap") + 1] = str(plain.hold + Decimal("0.05"))
    standing = ROOT / "docs/rulings/2026-11-11-run-start-submit.md"
    assert main([*base, "--ruling", str(RULING)]) == 0  # no web-search in this ruling
    base[base.index("--out") + 1] = str(tmp_path / "out2")
    assert main([*base, "--ruling", str(standing)]) == 2
    assert "--cap" in capsys.readouterr().err


def test_cap_is_sized_for_the_largest_module_not_the_smallest(tmp_path, capsys):
    # claude-opus-5-5 holds about USD 1.5 for CP-3's 105 KB instructions, USD 0.7 for CP-2's 6 KB.
    argv = launch(tmp_path, pathway="credit_snapshot")
    argv[argv.index("sol-medium")] = "opus-medium"
    argv[argv.index("--cap") + 1] = "1"
    assert main(argv) == 2
    assert "--cap" in capsys.readouterr().err


def test_invalid_context_is_refused_with_its_problem(tmp_path, capsys):
    argv = launch(tmp_path)
    (tmp_path / "context.json").write_text('{"schema": "wrong"}')
    assert main(argv) == 2
    assert "schema" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_without_live_nothing_is_sent_and_the_plan_is_shown(tmp_path, provider, capsys):
    assert main(launch(tmp_path)) == 0
    printed = capsys.readouterr().out
    assert provider.calls == []
    assert not (tmp_path / "out/live").exists()
    assert "gpt-6.1-sol" in printed and "medium" in printed
    assert "CP-4" in printed and "annual.txt" in printed and "chart.png" in printed
    assert "maturity-wall" in printed
    assert "5.73" in printed  # The per-call hold, seen from the live budget.


@pytest.mark.parametrize("missing", ["ruling", "key", "config-not-in-ruling"])
def test_live_gates_refuse_before_any_provider_call(
    tmp_path, provider, monkeypatch, capsys, missing
):
    argv = [*launch(tmp_path), "--live", "--ruling", str(RULING)]
    if missing == "ruling":
        argv = argv[:-2]
    elif missing == "key":
        monkeypatch.delenv("OPENAI_API_KEY")
    else:
        argv[argv.index("sol-medium")] = "sol-high"
    assert main(argv) == 2
    error = capsys.readouterr().err
    assert {"ruling": "--ruling", "key": "OPENAI_API_KEY", "config-not-in-ruling": "sol-high"}[
        missing
    ] in error
    assert "not-a-real-key" not in error
    assert provider.calls == []


@pytest.mark.parametrize(
    ("config", "key", "model", "effort"),
    [
        ("sol-medium", "OPENAI_API_KEY", "gpt-6.1-sol", "medium"),
        ("sol-high", "OPENAI_API_KEY", "gpt-6.1-sol", "high"),
        ("opus-medium", "ANTHROPIC_API_KEY", "claude-opus-5-5", "medium"),
        ("deepseek-max", "OPENROUTER_API_KEY", "deepseek/deepseek-v4.1-flash-1017", "max"),
    ],
)
def test_selected_model_and_effort_reach_every_provider_request(
    tmp_path, provider, monkeypatch, config, key, model, effort
):
    from deploy_workflow.model import adapter

    monkeypatch.setenv(key, "not-a-real-key")
    monkeypatch.setattr(adapter, "LIVE_RULINGS_ROOT", tmp_path)
    ruling = tmp_path / "all-configs.md"
    ruling.write_text(
        "lifts: live-provider-pause\nby: user\ndate: 2026-11-05\n"
        "configs: sol-medium sol-high opus-medium deepseek-max\n"
    )
    argv = [*launch(tmp_path), "--modules", "CP-4", "--live", "--ruling", str(ruling)]
    argv[argv.index("sol-medium")] = config
    routes = prepare_routes(tmp_path, config)
    provider.answer = lambda context: answer(context, routes)
    assert main(argv) == 0
    assert [c[0] for c in provider.calls] == ["CP-0", "CP-1", "CP-4"]
    assert {(c[1], c[2]) for c in provider.calls} == {(config, effort)}
    assert provider.models == {model}
    records = [
        json.loads(line)
        for log in (tmp_path / "out/live").rglob("*.jsonl")
        for line in log.read_text().splitlines()
    ]
    assert len(records) == 3
    assert {(r["requested_model"], r["requested_effort"]) for r in records} == {(model, effort)}
    assert {r["provider"] for r in records} == {key.split("_")[0].lower()}


def prepare_routes(
    tmp_path: Path, config: str, modules: tuple[str, ...] | None = ("CP-4",)
) -> list:
    return list(
        prepare(
            tmp_path / "context.json",
            tmp_path / "issuer",
            tmp_path / "preview",
            config=config,
            cap="50",
            modules=modules,
        ).plan.layout.routes
    )


KEY_FIGURES = (
    "| Measure | Value | Period | Source |\n| --- | --- | --- | --- |\n"
    "| Interest cover | 3.1x | FY2024 | Canonical data foundation (CP-1) |\n"
    "| Refinancing due | USD 1,250 million | FY2024 | Canonical data foundation (CP-1) |"
)


def short_snapshot_answer(context: dict, routes: list) -> str:
    """CP-L10's answer in the new format, hand-written: the four reader passages, a Key figures
    table whose Source column names CP-1, and no calculation. CP-0 and CP-1 answer as usual."""
    if context["module_id"] == "CP-1":  # the figures CP-L10 copies
        held = (
            "| Item | Value |\n| --- | --- |\n| Cover | 3.1x |\n| Refinancing | USD 1,250 million |"
        )
        return answer(context, routes).replace(
            "## Calculations\n\nNone.", f"## Calculations\n\n{held}", 1
        )
    if context["module_id"] != "CP-L10":
        return answer(context, routes)
    lines = ["# CP-L10", "", "## Request", f"{ISSUER} as of {AS_OF}.", "", "## Sources", ""]
    lines += [f"- {n} {h}" for n, h in context["sources"].items()]
    lines += [f"- {n} {h['sha256']}" for n, h in context["handoffs"].items()]
    lines += [
        *("", "## Findings", "", "### Bottom line", ""),
        (
            "Creditors are covered today but only just: cover is thin at 3.1x, so the near-term "
            "refinancing decides the view."
        ),
        "Basis: annual.txt, page 2",
        *("", "### Key findings", ""),
        "Cover is thin at 3.1x, which leaves little room for a weaker year.",
        "Basis: annual.txt, page 2",
        *("", "### Contrary evidence and what would change the view", ""),
        "Nothing supplied contradicts the view; a USD 1,250 million refinancing would.",
        *("", "### Limitations", ""),
        "- Only the financial statements were read, so the business view is not tested here.",
        *("", "### Key figures", "", KEY_FIGURES),
        *("", "## Calculations", "", "None.", "", "## Gaps", "", "None.", "", "## Next module"),
        *("", "None.", ""),
    ]
    return "\n".join(lines)


def test_short_snapshot_plans_exactly_cp0_cp1_and_cp_l10_in_order(tmp_path):
    """Owner, 2026-11-11: its own pathway of CP-0, CP-1 and one CP-L10 page; no CP-DR, CP-2E,
    CP-MODEL or CP-2G (the others' exception). The expected order is written by hand."""
    prepared, _ = all_instructions(tmp_path, "short_snapshot")
    assert tuple(prepared.plan.instructions) == SHORT_SNAPSHOT
    assert prepared.plan.run.requested_modules == ("CP-0", "CP-1", "CP-L10")
    assert prepared.ordered == SHORT_SNAPSHOT
    assert {r.module_id for r in prepared.plan.layout.routes} == {"CP-L10"}
    assert prepared.layout.title.endswith("Short Credit Snapshot")


def test_the_other_presets_do_not_gain_cp_l10():
    from deploy_vii.contracts import PATHWAY_MODULES as PRESETS

    assert all("CP-L10" not in m for p, m in PRESETS.items() if p != "short_snapshot")


def test_cp_l10_is_a_prose_module_sent_the_reader_passages_and_its_own_method(tmp_path):
    _, texts = all_instructions(tmp_path, "short_snapshot")
    head, _, method = texts["CP-L10"].partition(cpos_launch.METHOD_MARK)
    method = " ".join(method.split())
    assert "### Key findings" in head and "### Contrary evidence" in head
    assert "### Key figures" in head
    assert "short version of the credit snapshot" in method
    assert "copied exactly from the CP-1 handoff" in method
    assert "financial change screen" not in method.lower()


def test_a_short_snapshot_still_runs_end_to_end_through_the_lower_level_functions(
    tmp_path, provider, capsys
):
    """The launcher refuses a new short-snapshot run (`main`); `prepare` and `run_live_handoffs`,
    which read past and retained runs, still carry it to a verified delivery."""
    launch(tmp_path, pathway="short_snapshot")  # writes the context and the issuer folder
    prepared = prepare(
        tmp_path / "context.json",
        tmp_path / "issuer",
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    routes = list(prepared.plan.layout.routes)
    provider.answer = lambda context: short_snapshot_answer(context, routes)
    run_live_handoffs(
        prepared.manifest,
        prepared.directory,
        ruling=RULING,
        check=checker(prepared.layout),
        config="sol-medium",
    )
    out = tmp_path / "out"
    assert tuple(c[0] for c in provider.calls) == SHORT_SNAPSHOT
    delivered = next((out / "deliveries").glob("*/delivery.json"))
    assert verify_delivery(next(out.glob("delivery-*.json")), delivered.parent) == delivered
    assert "Short Credit Snapshot" in json.loads(delivered.read_text())["scope"]


def short_snapshot_issues(
    tmp_path, change, cp1=b"# upstream\nCover 3.1x; refinancing USD 1,250 million."
):
    prepared, task, context = good_task(tmp_path, "CP-L10", "short_snapshot")
    task = dataclasses.replace(task, handoffs={"CP-1": cp1})
    context["handoffs"] = {"CP-1": {"sha256": hashlib.sha256(cp1).hexdigest()}}
    raw = change(short_snapshot_answer(context, list(prepared.plan.layout.routes)))
    return _checked_handoff(task, raw.encode(), checker(prepared.layout))


def test_the_checker_accepts_a_good_short_snapshot(tmp_path):
    assert short_snapshot_issues(tmp_path, lambda raw: raw) == ()


def test_a_key_figure_that_cp1_never_states_is_refused_naming_it(tmp_path):
    """The figure is in the Key figures table and the Bottom line, so the fidelity check alone
    accepts it; the Key figures check holds it to the CP-1 handoff the module was sent."""
    issues = short_snapshot_issues(tmp_path, lambda raw: raw.replace("3.1x", "9.9x"))
    assert any("Key figures" in i and "9.9" in i for i in issues), issues


def test_the_good_short_snapshot_passes_the_key_figures_check(tmp_path):
    assert short_snapshot_issues(tmp_path, lambda raw: raw) == ()


def test_a_key_figure_that_drops_cp1s_sign_is_refused(tmp_path):
    cp1 = b"# upstream\nChange -3.1x; refinancing USD 1,250 million."
    issues = short_snapshot_issues(tmp_path, lambda raw: raw, cp1=cp1)
    assert any("Key figures" in i and "3.1x" in i for i in issues), issues


def test_a_second_key_figures_table_is_refused(tmp_path):
    extra = "\n\n" + KEY_FIGURES.replace("3.1x", "9.9x")
    issues = short_snapshot_issues(
        tmp_path, lambda raw: raw.replace(KEY_FIGURES, KEY_FIGURES + extra)
    )
    assert any("Key figures" in i and "9.9x" in i for i in issues), issues
    assert any("exactly one table" in i for i in issues), issues


def test_no_cp1_handoff_means_the_key_figures_are_refused_not_skipped(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-L10", "short_snapshot")
    task = dataclasses.replace(task, handoffs={})
    context["handoffs"] = {}
    raw = short_snapshot_answer(context, list(prepared.plan.layout.routes))
    issues = _checked_handoff(task, raw.encode(), checker(prepared.layout))
    assert any("cannot be checked" in i for i in issues), issues


def test_a_key_figures_table_with_other_columns_is_refused(tmp_path):
    bad = "| Thing | Number |\n| --- | --- |\n| Interest cover | 3.1x |"
    issues = short_snapshot_issues(tmp_path, lambda raw: raw.replace(KEY_FIGURES, bad))
    assert any("Key figures" in i and "Measure | Value | Period | Source" in i for i in issues)


@pytest.mark.parametrize(
    ("change", "complaint"),
    [
        # Check 8 (figures in a reader passage are held in a table): 4.5x is in no table.
        (lambda raw: raw.replace("cover is thin at 3.1x, so", "cover is thin at 4.5x, so"), "4.5"),
        # Check 1: the Bottom line must lead.
        (lambda raw: raw.replace("### Bottom line", "### Summary"), "Prose check 1"),
        # Check 2: a module code in a sentence.
        (lambda raw: raw.replace("little room", "little room per CP-1"), "Prose check 2"),
        # The report selector: the Key figures table is required.
        (lambda raw: raw.replace("### Key figures", "### Figures"), "Key figures"),
    ],
)
def test_the_checker_refuses_a_short_snapshot_that_breaks_the_reader_checks(
    tmp_path, change, complaint
):
    issues = short_snapshot_issues(tmp_path, change)
    assert any(complaint in i for i in issues), issues


# --- The lite and full credit assessments; the deactivated short snapshot ---------------


def test_the_lite_preset_is_cp0_cp1_cp1a_cp2_cp2a_with_no_cp_model():
    from deploy_vii.contracts import PATHWAY_MODULES as PRESETS

    assert PRESETS["lite_credit_assessment"] == LITE_MODULES
    assert "CP-MODEL" not in PRESETS["lite_credit_assessment"]
    # Owner, 2026-11-13: lite has neither CP-DR nor CP-2E.
    assert not {"CP-DR", "CP-2E"} & set(PRESETS["lite_credit_assessment"])


def test_the_lite_pathway_plans_exactly_cp0_cp1_cp1a_cp2_cp2a_in_order(tmp_path):
    prepared, _ = all_instructions(tmp_path, "lite_credit_assessment")
    assert tuple(prepared.plan.instructions) == LITE_MODULES
    assert prepared.ordered == LITE_MODULES
    assert prepared.plan.run.requested_modules == LITE_MODULES
    assert prepared.layout.title.endswith("Lite credit assessment")


def test_every_lite_block_is_routed_to_a_module_in_the_run(tmp_path):
    from deploy_vii.report_view import pathways

    lite = next(p for p in pathways() if p.id == "lite_credit_assessment")
    assert lite.blocks == LITE_BLOCKS
    assert lite.title == "Lite credit assessment"
    prepared, _ = all_instructions(tmp_path, "lite_credit_assessment")
    assert prepared.omitted == ()
    assert prepared.layout.blocks == LITE_BLOCKS
    assert {r.module_id for r in prepared.layout.routes} <= set(LITE_MODULES)
    by_block = {r.block_id: r.module_id for r in prepared.layout.routes}
    assert by_block["key-findings"] == "CP-2"
    assert by_block["company-operating-model"] == "CP-1A"
    assert by_block["downside-stress"] == by_block["break-points"] == "CP-2A"
    # No CP-MODEL: the chart strip and credit metrics are CP-1's, and its instruction asks for
    # neither the period table nor the layer-1 forecast block (ruling 2026-11-13).
    assert by_block["model-chart-strip"] == by_block["financials-credit-metrics"] == "CP-1"
    assert prepared.plan.publish_forecast is False
    cp1 = (prepared.directory / "instructions/CP-1.md").read_text()
    assert cpos_launch.LAYER1_FORECAST_BLOCK not in cp1
    assert cpos_launch.PERIOD_TABLE_BLOCK not in cp1


def test_the_credit_snapshot_is_the_full_credit_assessment_with_its_modules_and_blocks_unchanged():
    from deploy_vii.contracts import PATHWAY_MODULES as PRESETS
    from deploy_vii.report_view import pathways

    full = next(p for p in pathways() if p.id == "credit_snapshot")
    assert full.title == "Full credit assessment"
    assert full.blocks == FULL_BLOCKS
    assert tuple(PRESETS["credit_snapshot"]) == (
        *("CP-0", "CP-1", "CP-MODEL", "CP-1A", "CP-DR", "CP-2", "CP-2A", "CP-2E", "CP-2G"),
        *("CP-4", "CP-3", "CP-5", "CP-6"),
    )


def test_the_launcher_refuses_a_new_short_snapshot_run_with_the_message(tmp_path, capsys):
    argv = launch(tmp_path, pathway="short_snapshot")
    assert main(argv) == 2
    assert DEACTIVATED in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_the_helper_refuses_only_a_deactivated_pathway():
    with pytest.raises(LaunchRefused, match=re.escape(DEACTIVATED)):
        refuse_deactivated("short_snapshot")
    for pathway in (*PRESET_ANSWER_KEY, "unknown"):
        if pathway != "short_snapshot":
            refuse_deactivated(pathway)


def test_the_short_snapshot_instructions_still_build_through_the_lower_level_function(tmp_path):
    _, texts = all_instructions(tmp_path, "short_snapshot")
    assert tuple(texts) == SHORT_SNAPSHOT


def test_the_lite_pathway_runs_end_to_end_to_a_verified_delivery_with_a_synthetic_provider(
    tmp_path, provider, capsys
):
    """A synthetic run: a fake provider answers from hand-written text, so this proves the wiring,
    the checks and the delivered layout, and no model or analytical quality."""
    argv = launch(tmp_path, "--live", "--ruling", str(RULING), pathway="lite_credit_assessment")
    routes = list(
        prepare(
            tmp_path / "context.json",
            tmp_path / "issuer",
            tmp_path / "preview",
            config="sol-medium",
            cap="50",
        ).plan.layout.routes
    )
    # No CP-MODEL and no CP-2G: CP-1 writes no forecast block, and none is published.
    provider.answer = lambda context: answer(context, routes)
    assert main(argv) == 0
    seen = capsys.readouterr()
    # Nothing was requested, so nothing is reported as withheld (as for a short-snapshot run).
    assert "Model not published" not in seen.err
    out = tmp_path / "out"
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["cp_forecast_published"] is False and completed["forecast_failure"] is None
    assert completed["cp_model_published"] is False
    assert tuple(c[0] for c in provider.calls) == LITE_MODULES
    receipt = next((out / "deliveries").glob("*/delivery.json"))
    assert verify_delivery(next(out.glob("delivery-*.json")), receipt.parent) == receipt
    delivered = json.loads(receipt.read_text())
    assert "Lite credit assessment" in delivered["scope"]
    assert "Sections not produced: none." in delivered["scope"]
    report = ReportView.model_validate_json((receipt.parent / "report-view.json").read_text())
    assert tuple(block.block_id for block in report.blocks) == LITE_BLOCKS


# Prompt-size budget: the most characters (head plus method text, CP-8 left out) each pathway's
# instructions may total. An answer key of literal numbers: the lite and full credit assessments'
# are the owner's; each other pathway's is its measured total (2026-11-13: covenant_refinancing
# 1,091,950; distressed_restructuring 1,124,925; earnings_update 518,628; portfolio_decision
# 902,476; relative_value 1,017,908; short_snapshot 140,075) rounded up to the next 10,000 plus 5%.
# credit_snapshot measured 1,273,034 and lite_credit_assessment 392,429 (CP-MODEL removed).
INSTRUCTION_BUDGET = {
    "lite_credit_assessment": 420_000,
    "credit_snapshot": 1_340_000,
    "covenant_refinancing": 1_155_000,
    "distressed_restructuring": 1_186_500,
    "earnings_update": 546_000,
    "portfolio_decision": 955_500,
    "relative_value": 1_071_000,
    "short_snapshot": 157_500,
}


def test_the_budget_names_every_pathway():
    from deploy_vii.contracts import PATHWAY_MODULES as PRESETS

    assert set(INSTRUCTION_BUDGET) == set(PRESETS)


@pytest.mark.parametrize("pathway", sorted(INSTRUCTION_BUDGET))
def test_a_pathways_instructions_stay_within_their_size_budget(tmp_path, pathway):
    _, texts = all_instructions(tmp_path, pathway)
    total = sum(len(text) for module, text in texts.items() if module != "CP-8")
    ceiling = INSTRUCTION_BUDGET[pathway]
    assert total <= ceiling, (
        f"{pathway}: the instructions grew to {total:,} characters, {total - ceiling:,} over "
        f"the {ceiling:,} budget"
    )


@pytest.mark.parametrize("pathway", sorted(PATHWAY_MODULES))
def test_every_pathway_runs_end_to_end_to_a_verified_report(tmp_path, provider, capsys, pathway):
    argv = launch(tmp_path, "--live", "--ruling", str(RULING), pathway=pathway)
    routes = list(
        prepare(
            tmp_path / "context.json",
            tmp_path / "issuer",
            tmp_path / "preview",
            config="sol-medium",
            cap="50",
        ).plan.layout.routes
    )
    # CP-2G after CP-1 must write a forecast block; the declined one publishes no model.
    provider.answer = lambda context: (
        forecast_answer(context, routes, REAL_DECLINED_BLOCK)
        if context["module_id"] == "CP-2G"
        else answer(context, routes)
    )
    assert main(argv) == 0
    out = tmp_path / "out"
    assert tuple(c[0] for c in provider.calls) == PATHWAY_MODULES[pathway]
    receipt = next((out / "deliveries").glob("*/delivery.json"))
    assert verify_delivery(next(out.glob("delivery-*.json")), receipt.parent) == receipt
    assert str(receipt) in capsys.readouterr().out
    assert "not been independently reviewed" in json.loads(receipt.read_text())["scope"]
    assert not (receipt.parent / "model.html").exists()
    # The delivery renders no report page: the issuer library's pages are the report.
    assert not (receipt.parent / "report.html").exists()
    modules = json.loads((receipt.parent / "view.json").read_text())["modules"]
    live = (
        "Produced by a live model run and accepted by the CP-OS check; "
        "not native contract acceptance."
    )
    assert {m["limitations"][0] for m in modules} == {live}
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["execution"] == "live-provider"
    assert completed["cp_model_published"] is False


@pytest.mark.parametrize(("extra", "refreshed"), [((), True), (("--no-library",), False)])
def test_main_refreshes_the_library_only_without_no_library(
    tmp_path, provider, monkeypatch, extra, refreshed
):
    """A finished offline run on the fake provider; only the library refresh is stubbed."""
    refreshes = []
    monkeypatch.setattr(cpos_launch, "_refresh_library", refreshes.append)
    argv = launch(tmp_path, "--modules", "CP-4", "--live", "--ruling", str(RULING), *extra)
    routes = prepare_routes(tmp_path, "sol-medium")
    provider.answer = lambda context: answer(context, routes)
    assert main(argv) == 0
    assert provider.calls
    assert refreshes == ([tmp_path / "out"] if refreshed else [])


def test_rejected_module_stops_the_run_without_a_report(tmp_path, provider, capsys):
    argv = launch(tmp_path, "--modules", "CP-4", "--live", "--ruling", str(RULING))
    provider.answer = lambda context: "## Request\n\nNot a handoff."
    assert main(argv) == 1
    assert "CP-0" in capsys.readouterr().err
    assert not (tmp_path / "out/deliveries").exists()
    assert not list((tmp_path / "out").glob("completed-*.json"))


def test_issuer_name_from_the_context_is_carried_exactly_and_renders_no_page(tmp_path, provider):
    argv = launch(tmp_path, "--modules", "CP-4", "--live", "--ruling", str(RULING))
    hostile = "A</script><script>alert(1)</script>"
    path = tmp_path / "context.json"
    data = json.loads(path.read_text())
    data["identity"]["issuer_name"] = hostile
    path.write_text(json.dumps(data))
    routes = prepare_routes(tmp_path, "sol-medium")
    provider.answer = lambda context: answer(context, routes).replace(ISSUER, hostile)
    assert main(argv) == 0
    folder = next((tmp_path / "out/deliveries").glob("*/delivery.json")).parent
    assert json.loads((folder / "view.json").read_text())["run"]["issuer_name"] == hostile
    assert not list(folder.glob("*.html"))  # no page is rendered for the name to inject into


def test_interrupted_module_is_never_resent_because_its_charge_is_unknown(
    tmp_path, provider, monkeypatch, capsys
):
    argv = launch(tmp_path, "--modules", "CP-4", "--live", "--ruling", str(RULING))
    sent = []

    def fails_after_sending(self, request, **kwargs):
        sent.append(request)
        raise ConnectionError("connection lost after the request left")

    monkeypatch.setattr(LiveAdapter, "complete", fails_after_sending)
    assert main(argv) == 1
    assert "cpos_live_stopped" in capsys.readouterr().err
    assert main(argv) == 1
    assert "cpos_interrupted" in capsys.readouterr().err
    assert len(sent) == 1


# Written by hand from src/deploy_vii/methodology.json (required, plus optional producers this
# run selects; CP-5 takes every analyst before it), not from the registry code.
COVENANT_PRODUCERS = {
    "CP-0": [],
    "CP-1": ["CP-0"],
    "CP-1A": ["CP-0"],
    "CP-DR": ["CP-0", "CP-1"],
    "CP-2": ["CP-0", "CP-1", "CP-1A", "CP-DR"],
    "CP-4": ["CP-0", "CP-1", "CP-1A"],
    "CP-2A": ["CP-0", "CP-1", "CP-2"],
    "CP-2E": ["CP-0", "CP-1", "CP-1A", "CP-2"],
    "CP-2D": ["CP-0", "CP-1", "CP-2"],
    "CP-2G": ["CP-0", "CP-1", "CP-2A", "CP-2D"],
    "CP-3C": ["CP-0", "CP-1", "CP-1A", "CP-2A", "CP-2D", "CP-4"],
    "CP-5": [
        *("CP-0", "CP-1", "CP-1A", "CP-2", "CP-2A", "CP-2D", "CP-2E", "CP-2G", "CP-3C", "CP-4"),
        "CP-DR",  # CP-5 takes every analyst before it.
    ],
}


def covenant_answer(context: dict, routes: list) -> str:
    """The covenant pathway now runs CP-2G (owner, 2026-11-11), which must end in a forecast
    block; the declined one publishes no model."""
    if context["module_id"] == "CP-2G":
        return forecast_answer(context, routes, REAL_DECLINED_BLOCK)
    return answer(context, routes)


def test_each_module_is_sent_only_its_producers_handoffs(tmp_path, provider):
    # Run tdg-all-001 (2026-11-10) sent every module every earlier handoff: the first request
    # grew to 1 MB by CP-5, and six modules had all their source reads refused.
    argv = launch(tmp_path, "--live", "--ruling", str(RULING))
    routes = prepare_routes(tmp_path, "sol-medium", modules=None)
    sent = {}

    def answering(context):
        sent[context["module_id"]] = sorted(context["handoffs"])
        return covenant_answer(context, routes)

    provider.answer = answering
    assert main(argv) == 0
    assert sent == COVENANT_PRODUCERS


def test_answers_pinned_to_their_producers_are_replayed_unsent(tmp_path, provider):
    """CP-OS replays a retained answer whose pins are exactly the producers it is sent."""
    argv = launch(tmp_path, "--live", "--ruling", str(RULING))
    routes = prepare_routes(tmp_path, "sol-medium", modules=None)
    provider.answer = lambda context: covenant_answer(context, routes)
    assert main(argv) == 0
    sent = list(provider.calls)
    out = tmp_path / "out"
    pins = {}
    for record in (out / "requests").glob("*/*/1.request.json"):
        asked = json.loads(record.read_text())
        assert sorted(asked["handoffs"]) == COVENANT_PRODUCERS[asked["module_id"]]
        response = (record.parent / "1.response.md").read_bytes()
        path = f"retained/{asked['module_id']}.md"
        (out / path).parent.mkdir(exist_ok=True)
        (out / path).write_bytes(response)
        pins[asked["module_id"]] = RetainedHandoff(
            path=path,
            sha256=hashlib.sha256(response).hexdigest(),
            source_hashes=asked["sources"],
            upstream=asked["handoffs"],
        )
    request = HandoffPlan.model_validate_json((out / "workflow.json").read_bytes())
    manifest = out / "workflow-retained.json"
    manifest.write_text(request.model_copy(update={"retained_handoffs": pins}).model_dump_json())
    cpos_launch.run_live_handoffs(
        manifest,
        tmp_path / "again",
        ruling=RULING,
        check=checker(request.layout),
        max_turns=4,
        max_output_tokens=cpos_launch.MAX_OUTPUT_TOKENS,
    )
    assert provider.calls == sent


def test_second_launch_resumes_without_sending_anything(tmp_path, provider):
    argv = launch(tmp_path, "--modules", "CP-4", "--live", "--ruling", str(RULING))
    routes = prepare_routes(tmp_path, "sol-medium")
    provider.answer = lambda context: answer(context, routes)
    assert main(argv) == 0
    sent = list(provider.calls)
    assert main(argv) == 0
    assert provider.calls == sent


def test_changed_folder_cannot_reuse_a_run_directory(tmp_path, capsys):
    argv = launch(tmp_path)
    assert main(argv) == 0
    (tmp_path / "issuer/new-filing.txt").write_text("Later filing.")
    assert main(argv) == 2
    assert "--out" in capsys.readouterr().err
    manifest = json.loads((tmp_path / "out/workflow.json").read_text())
    assert "new-filing.txt" not in manifest["sources"]


def test_run_directory_inside_the_issuer_folder_is_refused(tmp_path, capsys):
    argv = launch(tmp_path)
    argv[argv.index("--out") + 1] = str(tmp_path / "issuer/run")
    assert main(argv) == 2
    assert "--out" in capsys.readouterr().err
    assert not (tmp_path / "issuer/run").exists()


def good_task(tmp_path: Path, module: str = "CP-2", pathway: str | None = None):
    pathway = pathway or OWNER_PATHWAY.get(module, "covenant_refinancing")
    prepared = prepare(
        context_file(tmp_path, pathway),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    upstream = {"CP-1": b"# upstream"}
    task = HandoffTask(
        prepared.plan.run,
        module,
        b"",
        {"annual.txt": b"Net sales", "context": b"{}"},
        upstream,
        1,
        (),
    )
    context = {
        "module_id": module,
        "sources": {"annual.txt": hashlib.sha256(b"Net sales").hexdigest()},
        "handoffs": {"CP-1": {"sha256": hashlib.sha256(b"# upstream").hexdigest()}},
    }
    return prepared, task, context


def test_checker_accepts_a_complete_handoff(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-4")
    raw = answer(context, list(prepared.plan.layout.routes)).encode()
    assert _checked_handoff(task, raw, checker(prepared.layout)) == ()


@pytest.mark.parametrize(
    ("old", "new", "complaint"),
    [
        (ISSUER, "Someone Else", "selected issuer"),
        (AS_OF, "2024-01-01", AS_OF),
        (hashlib.sha256(b"# upstream").hexdigest(), "gone", "CP-1"),
        ("annual.txt " + hashlib.sha256(b"Net sales").hexdigest(), "nothing", "source"),
        ("### Red flags", "### Other", "Red flags"),
        (
            "### Red flags\n\n| Item | Value |\n| --- | --- |\n| Observed | 1 |",
            "### Red flags",
            "Red flags",
        ),
    ],
)
def test_checker_rejects_each_missing_anchor(tmp_path, old, new, complaint):
    prepared, task, context = good_task(tmp_path, "CP-4")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new).encode(), checker(prepared.layout))
    assert any(complaint in issue for issue in issues), issues


def test_module_without_report_sections_still_needs_the_issuer(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-0")
    raw = answer(context, []).replace(ISSUER, "Someone Else").encode()
    assert any(
        "selected issuer" in i for i in _checked_handoff(task, raw, checker(prepared.layout))
    )


PERSONA = (
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
PROSE_BLOCK_START = (
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
    "conclusion it changes and how."
)
DATA_BLOCK = (
    "Reader passage. The reader is a portfolio manager or credit committee member who has not "
    "read the source documents. Open `## Findings` with `### Bottom line`: one or two "
    "paragraphs whose first sentence states this module's view and its consequence for "
    "creditors, in at most 45 words; the whole Bottom line is at most 180 words. If this module "
    "is blocked, its `### Bottom line` begins exactly "
    "`Not assessable: ` followed by why (the exact words that mark it blocked); a module that "
    'is not blocked must not use the words "not assessable" in its Bottom line. Your tables '
    "follow as the main content, unchanged and exact.\n\n"
)
READER_LAYER_SECTIONS = (
    "docs/reuse/selected-methods/CANON_SHARED.md § Reader-facing research layer",
    "docs/reuse/selected-methods/CANON_SHARED.md § Credit-research reading order",
)
CANON_APPENDIX_SECTION = "docs/reuse/selected-methods/CANON_SHARED.md § Analytical appendix"


def all_texts(tmp_path: Path) -> dict[str, str]:
    prepared = prepare(
        context_file(tmp_path, "relative_value"),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    return {
        module: (tmp_path / "out" / ref.path).read_text()
        for module, ref in prepared.plan.instructions.items()
    }


def test_the_persona_and_its_added_line_reach_every_module(tmp_path):
    for module, text in all_texts(tmp_path).items():
        assert PERSONA in text, module


def test_prose_modules_get_four_passages_and_data_modules_only_the_bottom_line(tmp_path):
    texts = all_texts(tmp_path)
    assert {"CP-0", "CP-1", "CP-1C"} <= set(texts) and "CP-2" in texts
    for module, text in texts.items():
        head = text.partition(cpos_launch.METHOD_MARK)[0]
        assert (
            "- Write evidence, risk mechanism and credit implication as ordinary sentences" in head
        )
        assert "End a paragraph or list item that rests on a source" in head
        assert "Cite modules and locators in brackets" not in text, module
        if module in DATA_MODULE_IDS:
            assert DATA_BLOCK in head, module
            assert "Reader passages. " not in head, module
        else:
            assert PROSE_BLOCK_START in head, module
            assert "Where the credit-research reading order's opening H3 or front sequence" in head
            assert DATA_BLOCK not in head, module
        assert "place `### " not in text and "### Reader summary" not in text, module


def test_a_report_selector_named_like_a_passage_is_the_passage_and_is_asked_once(tmp_path):
    prepared = prepare(
        context_file(tmp_path, "credit_snapshot"),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    named = [r for r in prepared.plan.layout.routes if r.heading == "Key findings"]
    assert [(r.module_id, r.kind) for r in named] == [("CP-2", "prose")]
    text = (tmp_path / "out" / prepared.plan.instructions["CP-2"].path).read_text()
    assert "- `### Key findings`: the reader passage of that name is this report selector" in text
    assert "- `### Key findings`: prose only." not in text


def test_a_blocked_module_is_told_to_keep_its_report_selectors(tmp_path):
    prepared, _, _ = good_task(tmp_path, "CP-2", "credit_snapshot")
    text = (tmp_path / "out" / prepared.plan.instructions["CP-2"].path).read_text()
    head = text.partition(cpos_launch.METHOD_MARK)[0]
    assert "write only `### Bottom line` of these four sections" in head
    assert "still each written exactly once even if blocked" in head
    assert "even if this module is blocked" in head  # the CP-2 collision line


def test_the_voice_and_precedence_rules_cover_method_labels_and_the_front_sequence(tmp_path):
    head = all_texts(tmp_path)["CP-2"].partition(cpos_launch.METHOD_MARK)[0]
    assert "`Evidence:`, `Risk Mechanic:`, `Credit Implication:`" in head
    assert "write those as sentences" in head
    assert "front sequence (the 90-150 word view, quantified drivers and front metrics" in head
    assert "its table and appendix rules still apply after `### Limitations`" in head


def test_the_limitation_instruction_says_repeats_across_the_run_are_refused(tmp_path):
    head = all_texts(tmp_path)["CP-2"].partition(cpos_launch.METHOD_MARK)[0]
    assert "any handoff accepted earlier in this run" in head
    assert "word each limitation for this module's own conclusion" in head
    assert "Do not repeat a limitation that a supplied handoff" not in head


def test_the_canon_reader_layer_goes_to_prose_modules_only(tmp_path):
    for module, names in METHODS.items():
        sent = [name for name, _ in cpos_launch.method_sections(module)]
        for section in READER_LAYER_SECTIONS:
            assert (section in names) == (section in sent) == (module not in DATA_MODULE_IDS)
    body = dict(cpos_launch.method_sections("CP-2"))
    assert body[READER_LAYER_SECTIONS[0]].startswith("#### Reader-facing research layer\n")
    assert body[READER_LAYER_SECTIONS[1]].startswith("##### Credit-research reading order\n")


def test_a_heading_section_ends_at_the_next_heading_of_the_same_or_higher_level():
    score = "docs/reuse/selected-methods/CANON_SHARED.md § CP_CONFIDENCE_SCORE.md"
    text = (ROOT / "docs/reuse/selected-methods/CANON_SHARED.md").read_text()
    start = text.index("## CP_CONFIDENCE_SCORE.md\n")
    end = text.find("\n## ", start + 1)
    assert cpos_launch._method_file(score) == text[start : end + 1]  # as before the generalisation
    reading = cpos_launch._method_file(READER_LAYER_SECTIONS[1])
    assert reading.startswith("##### Credit-research reading order\n")
    assert "\n##### " not in reading and "\n#### " not in reading


def test_a_method_heading_that_is_missing_or_repeated_is_refused():
    with pytest.raises(ValueError, match="expected one heading"):
        cpos_launch._method_file("docs/reuse/selected-methods/CANON_SHARED.md § No such heading")


def test_the_checker_accepts_a_good_prose_answer_and_a_good_data_answer(tmp_path):
    for module in ("CP-4", "CP-1"):
        (tmp_path / module).mkdir()
        prepared, task, context = good_task(tmp_path / module, module)
        raw = answer(context, list(prepared.plan.layout.routes))
        assert ("### Key findings" in raw) == (module not in DATA_MODULE_IDS)
        assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == (), module


def prose_issues_of(tmp_path, module, change, **task_fields):
    prepared, task, context = good_task(tmp_path, module)
    raw = change(answer(context, list(prepared.plan.layout.routes)))
    task = dataclasses.replace(task, **task_fields)
    return _checked_handoff(task, raw.encode(), checker(prepared.layout))


def test_the_checker_rejects_a_missing_bottom_line(tmp_path):
    issues = prose_issues_of(
        tmp_path,
        "CP-4",
        lambda raw: raw.replace("### Bottom line\n\n" + READER_BOTTOM_LINE + "\n\n", ""),
    )
    assert any(i.startswith("Prose check 1") for i in issues), issues


def test_the_checker_rejects_a_module_code_in_a_key_finding(tmp_path):
    issues = prose_issues_of(
        tmp_path,
        "CP-4",
        lambda raw: raw.replace("cover is thin at 3.1x", "cover is thin at 3.1x per CP-2D"),
    )
    assert any(i.startswith("Prose check 2") and "CP-2D" in i for i in issues), issues


def test_the_checker_rejects_pipeline_wording_after_the_reader_passages(tmp_path):
    issues = prose_issues_of(
        tmp_path,
        "CP-4",
        lambda raw: raw.replace(
            "## Calculations", "## Calculations\n\nThe helper scripts were not run.", 1
        ),
    )
    assert any(
        i.startswith("Prose check 10") and 'in section "Calculations"' in i for i in issues
    ), issues


def test_the_checker_rejects_a_bare_figure(tmp_path):
    issues = prose_issues_of(
        tmp_path, "CP-4", lambda raw: raw.replace("cover is thin at 3.1x", "debt is 1,250")
    )
    assert any(i.startswith("Prose check 8") and "1,250" in i for i in issues), issues


def test_a_limitation_repeated_from_an_accepted_handoff_is_rejected(tmp_path):
    limitation = "Synthetic data only in the cp four case, so no conclusion carries weight."
    accepted = {"CP-2": f"## Findings\n\n### Limitations\n\n- {limitation}\n".encode()}
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    plain = prose_issues_of(tmp_path / "a", "CP-4", lambda raw: raw)
    assert not any(i.startswith("Prose check 7") for i in plain), plain
    issues = prose_issues_of(tmp_path / "b", "CP-4", lambda raw: raw, accepted=accepted)
    assert any(i.startswith("Prose check 7") for i in issues), issues


def test_accepted_handoffs_stay_out_of_the_request_fingerprint(tmp_path):
    (tmp_path / "task").mkdir()
    prepared, task, context = good_task(tmp_path / "task", "CP-4")
    raw = answer(context, list(prepared.plan.layout.routes)).encode()
    folders = []
    for name, accepted in (("plain", {}), ("with", {"CP-2": b"# accepted"})):
        shown = dataclasses.replace(task, accepted=accepted)
        _handoff(shown, tmp_path / name, lambda _task: raw, lambda *_: (), 1)
        folders.append(sorted(p.name for p in (tmp_path / name / "requests" / "CP-4").iterdir()))
    assert folders[0] == folders[1] and len(folders[0]) == 1


def test_every_selected_method_file_exists():
    assert all(
        (ROOT / path.split(" § ")[0]).is_file() for files in METHODS.values() for path in files
    )


# --- module method gaps (owner, 2026-11-10: "Fix all ... Keep a copy of the methodology") --------
SKILLS = "docs/reuse/selected-methods/skills/"
# Written from each SKILL.md's own words ("mandatory, not optional", "binding method for the ...
# phase", "they bind every run", "Read ...; materialize its run-specific brief"), not from METHODS.
BINDING_COMPANIONS = {
    "CP-0": ("cp-0-source-readiness/references/REF_CP-0_STEPS.md",),
    "CP-1": (
        "cp-1-canonical-data-foundation/references/REF_CP-1_STEPS.md",
        "cp-1-canonical-data-foundation/references/CP-1_RUNBOOK.md",
    ),
    "CP-1B": (
        "cp-1b-earnings-delta/SKILL.md",
        "cp-1b-earnings-delta/references/REF_CP-1B_STEPS.md",
    ),
    "CP-1A": (
        "cp-1a-business-transaction-fact-pack/references/REF_CP-1A_STEPS.md",
        "cp-1a-business-transaction-fact-pack/references/REF_CP-2C_STEPS.md",
    ),
    "CP-2": ("cp-2-fundamental-credit-synthesizer/references/REF_CP-2_STEPS.md",),
    "CP-2A": ("cp-2a-downside-pathway/references/REF_CP-2A_STEPS.md",),
    "CP-3C": (
        "cp-3c-refinancing-lme-risk/references/REF_CP-3C_STEPS.md",
        "cp-3c-refinancing-lme-risk/references/CP-3C_RUNBOOK.md",
    ),
    "CP-3": (
        "cp-3-relative-value-security-selection/references/CP-3A_RUNBOOK.md",
        "cp-3-relative-value-security-selection/references/CP-3B_RUNBOOK.md",
        "cp-3-relative-value-security-selection/references/REF_CP-3B_STEPS.md",
        "cp-3-relative-value-security-selection/references/CP-3_SCHEMA_REFERENCE.md",
    ),
    "CP-4": (
        "cp-4-legal-covenant-interpreter/references/CP-4_RUNBOOK.md",
        "cp-4-legal-covenant-interpreter/references/CP-4A_RUNBOOK.md",
        "cp-4-legal-covenant-interpreter/references/REF_CP-4A_STEPS.md",
        "cp-4-legal-covenant-interpreter/references/CP-4B_RUNBOOK.md",
        "cp-4-legal-covenant-interpreter/references/REF_CP-4B_STEPS.md",
    ),
    "CP-5": ("cp-5-evidence-trace-validator/references/CP-5_RUNBOOK.md",),
    "CP-6": ("cp-6-ic-debate-challenge/references/REF_CP-6A_STEPS.md",),
    "CP-DR": ("cp-os-credit-os/references/CP_DR_RESEARCH_BRIEF_V1.md",),
}
SKILL_MODULES = [
    *(
        "CP-0",
        "CP-1",
        "CP-1A",
        "CP-1B",
        "CP-1C",
        "CP-1D",
        "CP-2",
        "CP-2A",
        "CP-2D",
        "CP-2E",
        "CP-2G",
        "CP-2H",
        "CP-3",
        "CP-3C",
        "CP-3D",
    ),
    *("CP-4", "CP-4C", "CP-5", "CP-6", "CP-DR"),
]


def test_each_module_is_sent_the_companions_its_method_calls_binding():
    for module, names in BINDING_COMPANIONS.items():
        for name in names:
            assert SKILLS + name in METHODS[module], (module, name)


def selector_headings(text):
    """The `### ...` headings of the selector list ("Report selectors, each exactly once")."""
    block = text.partition("Report selectors, each exactly once")[2].partition(
        cpos_launch.METHOD_MARK
    )[0]
    return re.findall(r"^- `(### [^`]+)`", block, flags=re.MULTILINE)


def test_cp2_and_cp1a_run_the_deploy_v_skills_not_the_deploy_vii_stand_ins(tmp_path):
    """Owner, 2026-11-13 ("Build rec. 1, then run"): the 18-step CP-2 skill and the CP-1A skill
    with its CP-2C bundle are sent; the short JSON-transport stand-ins are not."""
    cp2 = cpos_launch.method_text("CP-2")
    for phrase in (
        "# CP-2 \u2014 FundamentalCreditSynthesizer",
        "#### Workflow \u2014 18 Steps",
        "business profile vs typical leveraged-credit issuers in the sector",
    ):
        assert phrase in cp2, phrase
    for phrase in (
        "You receive no source text",
        "no peer ranking",
        "src/deploy_vii/methods/cp2.md",
    ):
        assert phrase not in cp2, phrase
    cp1a = cpos_launch.method_text("CP-1A")
    assert "# CP-1A Business Transaction Fact Pack" in cp1a
    assert "## Absorbed phase \u2014 CP-2C, binding on every CP-1A run" in cp1a
    assert "## REF_CP-2C_01_SourceGateReadiness.md" in cp1a  # a line of REF_CP-2C_STEPS.md
    for phrase in ("src/deploy_vii/methods/cp1a.md", "Python owns every figure"):
        assert phrase not in cp1a, phrase
    # Selectors read from the prepared text before the change; Confidence inputs is the addition.
    _, texts = all_instructions(tmp_path)
    expected = {
        "CP-2": ["### Map: credit-risk transmission"],
        "CP-1A": [
            "### Events: Issuer history",
            "### Map: ownership and control",
            "### Map: operating model to credit",
        ],
    }
    for module, old in expected.items():
        got = selector_headings(texts[module])
        assert sorted(got) == sorted([*old, "### Confidence inputs"]), module
        assert "`### Confidence inputs`" in texts[module].partition(cpos_launch.METHOD_MARK)[0]


def test_cp3c_runs_the_deploy_v_skill_not_the_deploy_vii_stand_in():
    """The stand-in (cp3c.md) forced the liability-management path to Insufficient Information
    and barred every digit from text; the Deploy V skill assesses legal capacity, sponsor
    willingness, the path taxonomy and a scenario map."""
    text = cpos_launch.method_text("CP-3C")
    for heading in (
        "# CP-3C Refinancing and Liability-Management Risk",
        "## REF_CP-3C_04_LegalCapacityForLME.md",
        "## REF_CP-3C_05_SponsorGovernanceWillingness.md",
        "## Refinancing / LME Path Taxonomy (12 paths)",
        "## REF_CP-3C_10_ScenarioMap.md",
    ):
        assert heading in text, heading
    for phrase in (
        "Text carries no figure and no digit",
        "The liability-management path is Insufficient Information",
        "src/deploy_vii/methods/cp3c.md",
    ):
        assert phrase not in text, phrase
    # The r17 edit: register T3D.2 carries Scale, in the skill and in the step file.
    assert "Currency`|`Scale`|`Maturity Date`" in text
    assert "        - Currency\n        - Scale\n        - Maturity Date\n" in text


def test_cp0_runs_the_deploy_v_skill_not_the_json_stand_in(tmp_path):
    """The stand-in (cp0.md) asks for a ReadinessReview matching a JSON Schema and applies a
    digit rule to `analysis[].text`; this transport is Markdown. CP-0 now gets Deploy V's skill
    and its step file, and a project block that says what the launcher already did."""
    _, texts = all_instructions(tmp_path, modules=("CP-0", "CP-1", "CP-2A"))
    text = texts["CP-0"]
    head, _, method = text.partition(cpos_launch.METHOD_MARK)
    for heading in (
        "## Runbook \u2014 binding method, inline",
        "#### Source hierarchy",
        # run_expectations cites this sentence as the source of its management-claims rule.
        (
            "1 \u2014 controlling/primary filings, executed legal documents and official "
            "schedules; 2 \u2014 issuer/agency releases, presentations, certificates and reports;"
        ),
        "#### T8 recommended-run command contract",
        (
            "- **required_register_ids**: T1; T2; T3; T4; T5; T6; T7; T8; "
            "P1; P2; P3; P4; P5; P6; P7; P8"
        ),
        "## REF_CP-0_I_DownstreamReadiness.md",
        "**Recommended Run Command Sheet**",
    ):
        assert heading in method, heading
    for phrase in ("ReadinessReview", "JSON Schema", "src/deploy_vii/methods/cp0.md"):
        assert phrase not in text, phrase
    # The management-claims expectation cites the sentence the CP-0 method text sent carries,
    # not the stand-in's wording: the citation and the sent text must agree.
    cited = next(r for r in RULES if r.key == "run-financials-management-claims").basis
    source_hierarchy = (
        "1 \u2014 controlling/primary filings, executed legal documents and official "
        "schedules; 2 \u2014 issuer/agency releases, presentations, certificates and reports;"
    )
    assert source_hierarchy in cited
    assert source_hierarchy in method
    assert "cp0.md" not in cited
    # The project block: sent to CP-0 only, in the head before the method.
    for words in (
        "already listed, hashed and pinned the sources",
        "Do not write the registers P1, P2, P4, P6, P7 and P8",
        "Write P3 and P5",
        "T1 input gate, T2 source register, T3 source hierarchy",
        "T8 recommended run command sheet",
        "the minimum missing documents",
        "only for a source the effective-source set does not carry",
        "never a readiness ground and never a `CONDITIONAL` condition",
        "The package, parse and hash checks were done by the launcher: record no result for them",
        "the objective is the selected pathway's use case",
        "record it in T1",
    ):
        assert words in head, words
    assert all(
        "already listed, hashed and pinned" not in t.partition(cpos_launch.METHOD_MARK)[0]
        for name, t in texts.items()
        if name != "CP-0"
    )
    assert "HOST SOURCE PREPARATION" not in text
    # CP-0 is a data module and is now scored: it owes the bottom line and the confidence inputs.
    assert "`### Confidence inputs`" in head


CPDR_QUESTIONS = (
    "`competition`",
    "`metric-definitions`",
    "`valuation-context`",
    "`market-demand`",
    "`industry-structure`",
    "`regulation`",
)
OPEN_WEB_SENTENCE = "There is no open-web discovery in this host. Never substitute"
PACK_TOOLS_ONLY_QUOTE = "returned by `read_pages` or `search_source`; `period_end`"
PACK_TOOLS_ONLY_READ = "read only with `list_sources`, `read_pages` and `search_source`. Item text"


def test_cpdr_runs_one_method_text_the_cp_os_version_2_skill():
    """The versions report (CP-DR, conflicts 1-7): the v1 skill plus `cpdr.md` disagreed on who
    writes the tables, the tool names and the answer states. One text now: cp-os version 2.0."""
    text = cpos_launch.method_text("CP-DR")
    assert "src/deploy_vii/methods/cpdr.md" not in text
    assert "Version: 2.0 | Date: 2026-11-04 | Method cp-dr/2026-10-31" in text
    at = [text.index(question) for question in CPDR_QUESTIONS]
    assert at == sorted(at)
    assert "Never type an amount that is not inside the quote" in text
    for phrase in ("Python composes the tables", "search_pack", "answered/partly/not_found"):
        assert phrase not in text, phrase
    # Named edit 2b (caos-databricks vendor/deploy-v): a gap row is typed `gap`, and missing
    # evidence is Complete with Gaps, never Blocked; the step bundle says the same.
    assert "whose `claim_type` is `gap`" in text
    assert "whose `claim_type` is `source_characterisation`" not in text
    assert "Missing evidence makes a question UNRESOLVED and the run Complete with Gaps" in text
    assert "Missing evidence alone is never `Blocked`." in text
    assert "a gap row, which records a search that found nothing, takes `gap`" in text


def test_cpdr_open_web_limit_is_conditional_on_the_web_search_rules(tmp_path, provider):
    """Named edit 2a. The skill said there is no open-web discovery in this host while the project
    offers `web_search` with WEB_SEARCH_RULES appended to the system text. The condition is named as
    the model receives it: the paragraph that begins "web_search reaches public web pages"."""
    from deploy_workflow.model.handoff import WEB_SEARCH_RULES

    assert WEB_SEARCH_RULES.lstrip().startswith("web_search reaches public web pages")
    assert OPEN_WEB_SENTENCE not in cpos_launch.method_text("CP-DR")
    root = tmp_path / "rulings"
    root.mkdir()
    for name, configs in (("on.md", "sol-medium, web-search"), ("off.md", "sol-medium")):
        lines = (
            "lifts: live-provider-pause",
            "by: user",
            "date: 2026-11-10",
            f"configs: {configs}",
        )
        (root / name).write_text("\n".join(lines) + "\n")
    assert main(launch(tmp_path, "--ruling", str(RULING), pathway="relative_value")) == 0
    routes = prepare_routes(tmp_path, "sol-medium", modules=None)
    provider.answer = lambda context: answer(context, routes)
    manifest = tmp_path / "out/workflow.json"
    layout = HandoffPlan.model_validate_json(manifest.read_bytes()).layout
    systems = {}
    for name in ("on.md", "off.md"):
        provider.systems.clear()
        cpos_launch.run_live_handoffs(
            manifest,
            tmp_path / name,
            ruling=root / name,
            check=checker(layout),
            max_turns=4,
            max_output_tokens=cpos_launch.MAX_OUTPUT_TOKENS,
            rulings_root=root,
        )
        systems[name] = provider.systems["CP-DR"]
    for name, granted in (("on.md", True), ("off.md", False)):
        system = systems[name]
        assert (WEB_SEARCH_RULES in system) is granted
        assert OPEN_WEB_SENTENCE not in system
        condition = "unless this run's instruction carries the paragraph that begins \"web_search"
        assert condition in system
        for question in CPDR_QUESTIONS:
            assert question in system
        assert "Never type an amount that is not inside the quote" in system
        # Named edit 2a-4: the reading and TDR.6 quote clauses no longer name pack tools alone.
        assert PACK_TOOLS_ONLY_QUOTE not in system
        assert PACK_TOOLS_ONLY_READ not in system
        assert 'or, when the paragraph that begins "web_search reaches' in system
        assert "Python composes the tables" not in system
        assert "search_pack" not in system


# ---- Deploy V methods plan, Task 5A (2026-11-13): CP-2D, CP-4 and CP-4C send the caos-databricks
# versions (vendor/deploy-v, repo HEAD dfff264) with named edits: the `qa_status` map sentence of
# common rule 10 (all three) and CP-4C's LITE profile text are removed. Each module: one sentence
# of the new text is in the built instruction, one sentence of the old text and each removed
# sentence are not.
def test_cp2d_instruction_carries_the_six_column_months_to_empty_register(tmp_path):
    text = instruction_text(tmp_path, "CP-2D")
    assert (
        "T2E.6: `Calculation`|`Result`|`Formula / Inputs`|`Cash-Burn Basis`|`Status`|`Source Trace`"
        in text
    )
    assert (
        "where the period is cash-generative (average monthly burn at or below zero) there is no "
        "runway to exhaust and `Result` is `Not Calculable`" in text
    )
    assert (
        "T2E.5: `Bridge Item`|`Amount`|`Currency and Scale`|`Source / Calculation`|`Status`"
        "|`Credit Comment`|`Source Trace`" in text
    )
    assert "T2E.6: Months to Empty result (numeric) + calculation basis narrative" not in text
    assert "`qa_status` follows the run's own status" not in text  # the named edit


def test_cp4_instruction_asks_for_the_reason_form_of_the_placeholder(tmp_path):
    text = instruction_text(tmp_path, "CP-4")
    assert (
        "write `[Insufficient Information] — ` and name the missing document (for example "
        "`[Insufficient Information] — intercreditor agreement not in the source set`), never "
        "the bare placeholder" in text
    )
    assert "`[Insufficient Information]` where the document is not provided." not in text
    assert "`qa_status` follows the run's own status" not in text  # the named edit


def test_cp4c_instruction_answers_no_distress_gate_with_not_applicable(tmp_path):
    text = instruction_text(tmp_path, "CP-4C")
    assert (
        "Without a documented distress gate the module builds no restructuring scenario and "
        "returns `Not Applicable` (Phase 1), which is a complete answer; only an unresolved "
        "scope holds the run." in text
    )
    assert "Requires a validated handoff from CP-0, CP-1, CP-2A, CP-2G and CP-4" in text  # E4
    # Named edit E4 (2026-11-13): the profile distinction no longer exists in the text.
    assert "In FULL_CREDIT_32, requires" not in text
    assert "in both profiles" not in text
    assert "Optional upstream, used when present: CP-2A, CP-2G, CP-4." not in text
    for gone in (  # the named edits: caos-only profile text and the qa_status map
        "LITE_CREDIT_22",
        "UPGRADE",
        "`qa_status` follows the run's own status",
    ):
        assert gone not in text, gone


def test_a_handoff_in_the_new_register_shapes_passes_the_chart_checks():
    """Nothing in the CP-OS checker reads T2E.5, `Months to Empty` or a CP-4C `Not Applicable`
    answer: `chart_issues` reads only the `### Chart data:` tables. A cash-generative CP-2D and a
    CP-4C with no distress gate state every chart amount as `Not supplied: <reason>`."""
    gap = "Not supplied: the period is cash-generative, there is no runway"
    text = "### Chart data: liquidity bridge\n\n" + synthetic_table(
        ALLOCATION_HEAD,
        f"| Opening liquidity | {gap} | US$m | S. |",
        f"| Closing liquidity | {gap} | US$m | S. |",
    )
    bridge = next(t for t in cpos_launch.OWNER_TABLES["CP-2D"])
    assert cpos_launch.chart_issues(text, bridge) == ()
    na = "Not supplied: no documented distress gate, CP-4C returned Not Applicable"
    recovery = f"### {RECOVERY}\n\n" + synthetic_table(
        RECOVERY_HEAD, f"| {na} | {na} | {na} | {na} | {na} | US$m | S. |"
    )
    spec = next(t for t in cpos_launch.OWNER_TABLES["CP-4C"] if t.heading == RECOVERY)
    assert cpos_launch.chart_issues(recovery, spec) == ()


# ---- Deploy V methods plan, Task 5B (2026-11-13): seven sent skills take one small named
# correction each from caos-databricks vendor/deploy-v (repo HEAD dfff264) or cp-os 115f664. Each
# module: one sentence of the new text is in the built instruction and the sentence it replaced is
# not. Nothing in the CP-OS checker reads a T2.10 Direction, a T2H.3 `case`, a T1D `NONE` row or
# the skills' critical-cell blocklist (`chart_issues` reads only the `### Chart data:` tables).
def blocklist_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if "critical_cell_values_casefold" in line]


def test_cp5_instruction_says_cp6_runs_after_cp5_and_is_not_its_input(tmp_path):
    text = instruction_text(tmp_path, "CP-5")
    assert (
        "**Downstream (QA gate):** CP-6 and CP-6A run only after this handoff is accepted (the "
        "catalog's CP-5 \u2192 CP-6 QA gate); they are never CP-5's input" in text
    )
    assert "CP-6 and CP-6A run after CP-5 and are not its input" in text
    for gone in (  # the sentences that said CP-5 reads CP-6 and CP-6A
        "All analytical modules (CP-1 through CP-4A, CP-6, CP-6A), CP-5A QA output",
        "all analytical modules (CP-1 through CP-4A, CP-6, CP-6A)",
        "(especially CP-3, CP-6, CP-6A)",
    ):
        assert gone not in text, gone


def test_cp6_instruction_says_its_qa_gate_is_cp5_upstream_of_it(tmp_path):
    text = instruction_text(tmp_path, "CP-6")
    assert (
        "Its QA gate is CP-5: CP-6 runs only after CP-5's handoff is accepted (Passed or "
        "Restricted), so CP-5 is upstream of CP-6 and never its consumer." in text
    )
    assert (
        "**Upstream (QA gate):** CP-5, CP-5A (accepted before this module runs; "
        "CP-5 is never its consumer)" in text
    )
    assert "UP (QA gate): CP-5, CP-5A | DOWN (Analytical): CP-6A" in text
    assert "UP (QA gate): CP-5, CP-5A | DOWN (Analytical): (terminal L6 module)" in text
    assert "**Downstream (QA):** CP-5, CP-5A" not in text  # the stale header lines
    assert "DOWN (QA): CP-5, CP-5A" not in text


def test_cp2_instruction_splits_a_mixed_direction_and_gives_none_supported_a_row(tmp_path):
    text = instruction_text(tmp_path, "CP-2")
    assert (
        "A driver that cuts both ways is split into a Positive row and a Negative row, each "
        "with its own `Credit Implication` (canon: Mixed->split); `Mixed` is never a Direction."
        in text
    )
    assert "`Driver` `None supported`, `Evidence` naming what was reviewed" in text
    assert "- Direction: Positive / Negative / Mixed" not in text
    assert "**values**: Positive; Negative; Mixed" not in text


def test_cp1d_instruction_gives_an_empty_cp1_bridge_one_none_row_per_register(tmp_path):
    prepared, *_ = good_task(tmp_path, "CP-1D", "earnings_update")  # CP-1D's pathway
    text = (tmp_path / "out" / prepared.plan.instructions["CP-1D"].path).read_text()
    assert (
        "T1D.1\u2013T1D.4 then each carry one row stating that no add-back exists (`Add-Back ID` "
        "`NONE`" in text
    )
    assert "T1D.4 bridges reported EBITDA to itself, and Steps 5\u20137 still run." in text
    assert "present in T1D.1 (one `NONE` row when the bridge is empty); achievability" in text
    assert "present in T1D.1; achievability" not in text


def test_cp2g_instruction_says_the_assumption_register_carries_base_and_downside_rows(tmp_path):
    text = instruction_text(tmp_path, "CP-2G")
    assert (
        "In the assumption register (T2H.3) each row's `case` is `base`, `upside` or `downside` "
        "(any capitalisation, and the word may lead a longer label such as `Base case`), and the "
        "register carries rows for both `base` and `downside`." in text
    )
    assert "or `analyst_judgment`. Store exact source and locator" not in text


def test_cp2h_blocklist_no_longer_refuses_unknown(tmp_path):
    (line,) = blocklist_lines(instruction_text(tmp_path, "CP-2H"))
    assert "unknown" not in line
    assert line.endswith(
        "; n/a; tbd; not calculable from provided materials; not assessable; unavailable"
    )


def test_cp3_blocklists_no_longer_refuse_not_assessable(tmp_path):
    text = instruction_text(tmp_path, "CP-3")
    # CP-3's own list and the CP-3A and CP-3B copies, each a value line of the method text
    lines = [x for x in text.splitlines() if "[insufficient information]; insufficient" in x]
    assert len(lines) == 3
    for line in lines:
        assert "not assessable" not in line
        assert line.endswith(
            "; n/a; tbd; unknown; not calculable from provided materials; unavailable"
        )


CP1_DIR = ROOT / "docs/reuse/selected-methods/skills/cp-1-canonical-data-foundation"
CP1_FILES = (
    "SKILL.md",
    "references/CP-1_RUNBOOK.md",
    "references/REF_CP-1_STEPS.md",
    "references/CP-1_SCHEMA_REFERENCE.md",
    "references/CP-1_SYSTEM_REFERENCE.md",
)
# The byte-for-byte copies of caos-databricks vendor/deploy-v at dfff264 (the answer key for the
# `source_sha256` of every edited entry); the schema and system references stay unedited.
CP1_SOURCE_SHA256 = dict(
    zip(
        CP1_FILES,
        (
            "35b865705f9cb4a001c8a227767319bc3f34d274c3659164176ab2e70bf3a345",
            "7934e8c562832b8320243cbf08e84b16575a0d2e4974fd918bf094b300fcd4ad",
            "e9552f0d2b128cbe27ec58cdc2360e0e67c96a9f6ec21a140854f310de201bc1",
            "356e87cb37a5ed86c96b15a913f42b8aafee544cd70e4f8f2fde01ce58cc7b72",
            "7af64a9047ffa05e996dbb4cb1741b9a815744ecb7eb7bd3b134a4bccf9d2cd0",
        ),
        strict=True,
    )
)
CP1_SENT = CP1_FILES[:3]


def cp1_method() -> str:
    return "\n".join((CP1_DIR / name).read_text(encoding="utf-8") for name in CP1_SENT)


def test_cp1_runs_the_deploy_v_method_not_the_structured_runtime_stand_ins():
    """Owner, 2026-11-13: CP-1 is sent caos dfff264's skill, runbook and step file (edited), not
    the 26 KB of STEP_CONTRACTS written for the JSON runtime."""
    text = cpos_launch.method_text("CP-1")
    for heading in (
        "# CP-1 Canonical Data Foundation",
        "# CP-1 runbook",
        *(f"## REF_CP-1_{n}" for n in ("01_", "02_", "03_", "04_", "05_", "06_", "07_")),
        *(f"## REF_CP-1_{n}" for n in ("08_", "09_", "10_", "11_", "12_")),
        "## Anti-patterns",
        "## Discipline",
        "## Calculation status (8 values)",
        "## Evidence hierarchy",
        "## Null and derived-period rules",
        "## Event and liability discipline",
        "## Metrics",
    ):
        assert heading in text, heading
    for phrase in (
        "Every `amount` is a JSON number",
        "STEP_CONTRACTS",
        "source_context",
    ):
        assert phrase not in text, phrase
    assert [n for n, _ in cpos_launch.method_sections("CP-1")][: len(CP1_SENT) + 1] == [
        *(SKILLS + "cp-1-canonical-data-foundation/" + name for name in CP1_SENT),
        "prompts/CP-1.md",
    ]


def test_cp1_method_has_no_workbook_routing_script_or_front_matter_text():
    text = cp1_method()
    for phrase in (
        "REF_CP-1_13",
        "Model Workbook",
        "orkbook",
        "CP-MODEL",
        "T4.14",
        "T4.15",
        "T4.19",
        "table-id",
        "cp1.",
        "DEBT_TOTAL_EX_LEASES",
        ".xlsx",
        "Run CP-1",
        "recommended next command",
        "CREDIT_OS_V_MODULE_CATALOG",
        "prepare_invocation",
        "validate_handoff",
        "completeness_check",
        "confidence_score.py",
        "credit_metrics.py",
        "Automated QA validation",
        "qa_status",
        "Confidence Score",
        "Microsoft 365",
        "Feeds CP-1B",
        "Downstream Module",
        "CP-1B",
        "CP-2G",
        "CP-4A",
        "CP-5A",
        "cpdr.adoptions",
        "CP_DR_RESEARCH_BRIEF",
        "[SubjectKey]",
        "Audit Summary",
        "QA Validation",
        "Gaps & Conflicts",
        "Analytical appendix",
    ):
        assert phrase not in text, phrase
    # The null spelling the host's system prompt bars (method wrote `null`, `—`, empty cells).
    for phrase in ("write `null`", "Store **null**", "Store null", "explicit null", "null + gap"):
        assert phrase not in text, phrase
    # CP-OS, not the method, orders modules and writes the next-module section.
    assert "Run command" not in text and "Dependencies" not in text


def test_cp1_method_states_the_project_conventions_the_checks_hold():
    text = cp1_method()
    for phrase in (
        "`Not supplied: <reason>`",
        "`Not calculable: <reason>`",
        "never `null`, an empty cell or a dash",
        "no snake_case or capitalised underscore tokens, no register ids",
        'not the words "canonical" or "handoff"',
        "Each register below is a `###` heading inside `## Findings`; gaps go under `## Gaps`",
        "CP-1 is a data module: `### Bottom line` opens `## Findings`",
        "T4.7 is retired",
        "This method does not rename, merge or drop any of them",
    ):
        assert phrase in text, phrase
    for kept in (
        "`Chart data:` tables",
        "`Net debt data`",
        "`Post-balance-sheet adjustments`",
        "`### Financials and credit metrics`",
        "the Period table",
        "`### Confidence inputs`",
    ):
        assert kept in text, kept
    # Every editing-out of the method's wording leaves the sentence rules to the sentences only.
    assert "Debt principal to carrying value" not in text  # the launcher block names that table


def test_cp1_method_names_the_operand_tables_the_check_reads():
    text = cp1_method()
    for heading in (
        "### T4.4 Income statement",
        "### T4.5 Cash flow statement",
        "### T4.6 Balance sheet",
        "### T4.9 Calculation register",
    ):
        assert f"`{heading}`" in text or f"Output `{heading}`" in text, heading
    assert "The first column is headed `Line item`" in text
    assert "`Unit` (the currency code and `millions` or `thousands`" in text
    for row in (
        "`EBITDA (Reported)`",
        "`EBITDA (Adjusted)`",
        "`Net Cash from Operating Activities`",
        "`Net Cash from Investing Activities`",
        "`Net Cash from Financing Activities`",
        "`Net Cash Change`",
        "`Opening Cash`",
        "`Closing Cash`",
        "`Cash Interest Paid`",
        "`FX Effect on Cash`",
        "`Total Assets`",
        "`Total Liabilities`",
        "`Total Equity`",
        "`Total Debt`",
        "`Cash & Equivalents`",
        "`Temporary Equity`",
    ):
        assert row in text, row
    assert (
        "`Metric Name` | `Formula` | `Numerator Value` | `Numerator Source` | "
        "`Denominator Value` | `Denominator Source` | `Period` | `Currency` | `Unit` | "
        "`Calculated Value` | `Calculation Status` | `Evidence Quality Tier` | `Limitations`"
    ) in text
    for name in (
        "`Total debt / EBITDA`",
        "`Net debt / EBITDA`",
        "`EBITDA / cash interest`",
        "`Total debt / adjusted EBITDA`",
        "`Net debt / adjusted EBITDA`",
        "`Adjusted EBITDA / cash interest`",
    ):
        assert name in text, name
    assert "`Unit` is `US$m`" in text
    assert (
        "`Net Cash Change` excludes nothing: it is operating plus investing plus financing" in text
    )
    assert "plus the FX effect" in text
    # T4.7 stays retired: no table by that name is asked for.
    assert "### T4.7" not in text


def test_cp1_method_states_the_debt_and_ebitda_basis():
    text = cp1_method()
    for phrase in (
        "debt totals use carrying values",
        "Principal and commitment are kept separately and are not substitutes",
        "Lease liabilities the issuer presents on their own balance-sheet lines are not added",
        "A lease or other obligation the issuer carries inside its debt lines stays in",
        "Reported EBITDA is the primary denominator",
        "adjusted EBITDA beside it, labelled, when the issuer states it",
        "gross principal is never the leverage denominator",
        "The carrying-against-principal difference is always one row here",
    ):
        assert phrase.lower() in text.lower(), phrase
    # The method no longer prefers or treats adjusted EBITDA as the primary denominator.
    # Wording the source did contain (Canon Core debt basis, and its example with locators).
    assert "Canonical debt basis" not in text
    assert "Source: AR p.45" not in text
    assert "A lease liability is not in total debt" not in text


STEP13_RULES = (
    # (rule, phrase the sent text must hold)
    ("outflows negative", "Outflows are negative and inflows positive"),
    ("cash interest and tax are cash paid", "cash paid, not accrued expense"),
    ("lease and interest cash classification", "lease principal paid (financing activities"),
    ("debt instruments table", "### T4.18 Debt instruments"),
    ("carrying and principal separate", "carrying value and principal are separate columns"),
    ("no inference from the name", "never inferred from the instrument name"),
    ("not stated is not evidence of ranking", "it is not evidence of either"),
    ("bullet amortisation is 0", "0 for a bullet"),
    ("financing cost adjustment row", "`Financing cost adjustment` row"),
    ("instruments reconcile to Total Debt", "plus that row reconcile to `Total Debt`"),
    ("one row per add-back, issuer label", "one row per add-back with the issuer's own label"),
    ("realisation never inferred", "that is never inferred from the classification"),
    (
        "add-backs never merged, no plug",
        "Add-backs are never merged, and no plug or balancing line",
    ),
    ("bridge feeds the host table", "write no second bridge table"),
    ("reported quarter first", "a reported discrete quarter comes first"),
    ("Q3 from 9M less H1", "Q3 is 9M less H1 only when the quarters are absent"),
    ("Q4 from FY less 9M, labelled", "Q4 is FY less 9M only when no Q4 is reported"),
    ("reported year not replaced", "A reported fiscal year is never replaced by a sum of quarters"),
    ("balance-sheet LTM is the latest end", "last-twelve-months figure is the latest period end"),
    ("reconciliation list", "segment revenue to reported revenue, the EBITDA bridge"),
    ("difference never forced to zero", "it is never forced to zero"),
    (
        "segment corporate and eliminations",
        "Corporate and eliminations are one separate row per period",
    ),
    ("operating KPI series", "never join non-comparable series"),
    ("pro forma only when a source states it", "never construct one the source does not state"),
    ("pro forma out of period figures", "They stay out of period figures"),
    ("evidence tier labels", "2a unaudited with auditor review"),
    ("no independent recommendation", "No independent credit recommendation"),
)


def test_cp1_method_restates_step_13s_analytical_rules_without_its_tagged_tables():
    text = cp1_method()
    for rule, phrase in STEP13_RULES:
        assert phrase in text, rule


def test_cp1_example_sentences_carry_no_bracket_label_and_no_page_locator():
    """The host prose checks 3 and 4 refuse both in a sentence; the method names where they go."""
    text = cp1_method()
    for label in ("[Normalized]", "[Calculated]", "[Analyst Judgement]"):
        assert label not in text, label
    assert not re.search(r"\bpp?\.\s*\d|\bpages?\s+\d", text, re.IGNORECASE)
    assert "Page locators go in `Source` columns and Basis lines, never in a sentence" in text
    assert "never inside a sentence: reported (with its source)" in text


def test_cp1_method_files_are_archived_with_hashes_and_named_edits():
    manifest = json.loads((ROOT / "docs/reuse/selected-methods/manifest.json").read_text())
    entries = {e["archive_path"]: e for e in manifest["files"]}
    for name in CP1_FILES:
        entry = entries[f"docs/reuse/selected-methods/skills/cp-1-canonical-data-foundation/{name}"]
        data = (CP1_DIR / name).read_bytes()
        assert entry["sha256"] == hashlib.sha256(data).hexdigest(), name
        if name in CP1_SENT:
            assert entry["edited_copy_of"].endswith(
                "caos-databricks/vendor/deploy-v/skills/cp-1-canonical-data-foundation/" + name
            ), name
            assert entry["exact_copy_found_at"] is None
            assert entry["source_sha256"] == CP1_SOURCE_SHA256[name], name
            assert entry["source_sha256"] != entry["sha256"], name
            edit = entry["edit"]
            assert "dfff264" in edit and "source_sha256" in edit, name
        else:  # archived, not sent: byte-for-byte
            assert entry["sha256"] == CP1_SOURCE_SHA256[name], name
            assert entry["exact_copy_found_at"].endswith(name), name
            assert "edited_copy_of" not in entry
    edits = " ".join(entries[f"{CP1_DIR.relative_to(ROOT)}/{n}"]["edit"] for n in CP1_SENT)
    for named in (
        "(a) workbook",
        "(b) routing",
        "(c) runbook",
        "(d) project conventions",
        "(e) operand tables",
        "(f) debt basis and EBITDA",
        "(g) step 13's analytical rules restated without its tagged tables",
        "expense-block reconciliation",
        "compare to the precision",
        "a balance sheet is an instant",
        "never replace a directly reported period",
        "prohibited conclusion, reader question and decision drivers",
        "FFO/Debt trajectory",
        "WC inclusion",
    ):
        assert named in edits, named


def test_cp1_sent_method_fits_the_size_the_pathway_budgets_leave():
    """The answer key: the sent skill files total at most 33,000 characters, so the launcher
    block that follows (about 3,500) and the score section (2,172) keep every pathway inside its
    ceiling (the pathway budget test itself is the size-budget test above)."""
    assert len(cp1_method()) <= 33_000


def test_cp1b_runs_the_deploy_v_method_not_the_structured_runtime_step():
    """Live runs 2026-11-09 and 2026-11-10: CP-1B blocked both times for want of a `read_inputs`
    view with `pairs`, which only the older structured runtime gives."""
    text = cpos_launch.method_text("CP-1B")
    assert "read_inputs" not in text and "earnings_delta.md" not in text
    assert "# CP-1B Earnings Delta" in text


def test_skill_modules_carry_the_confidence_score_rules_their_script_would_apply():
    section = "docs/reuse/selected-methods/CANON_SHARED.md § CP_CONFIDENCE_SCORE.md"
    for module in SKILL_MODULES:
        names = [name for name, _ in cpos_launch.method_sections(module)]
        assert names.count(section) == 1, module
        body = dict(cpos_launch.method_sections(module))[section]
        assert body.startswith("## CP_CONFIDENCE_SCORE.md\n")
        assert "score = clamp( (0.6 * E + 0.4 * C) * S - P , 0 , 100 )" in body
        assert "CP_LIMITATION_TAXONOMY" not in body  # the next canon section is not swept in
    assert [name for name, _ in cpos_launch.method_sections("CP-L10")][1:] == [
        *READER_LAYER_SECTIONS,
        CANON_APPENDIX_SECTION,
    ]


def test_the_method_archive_lists_every_sent_file_with_its_hash():
    manifest = json.loads((ROOT / "docs/reuse/selected-methods/manifest.json").read_text())
    listed = {entry["archive_path"]: entry["sha256"] for entry in manifest["files"]}
    for files in METHODS.values():
        for name in files:
            path = name.split(" § ")[0]
            if path.startswith("docs/reuse/selected-methods/"):
                assert listed.get(path) == hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), (
                    path
                )


def all_instructions(tmp_path, pathway="distressed_restructuring", modules=None, peer_source=None):
    context = context_file(tmp_path, pathway)
    if peer_source is not None:
        data = json.loads(context.read_text())
        data["valuation"].update(peer_source=peer_source, peers=[])
        context.write_text(json.dumps(data))
    prepared = prepare(
        context,
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
        modules=modules,
    )
    return prepared, {
        m: (tmp_path / "out" / spec.path).read_text()
        for m, spec in prepared.plan.instructions.items()
    }


def test_every_module_is_told_what_stands_for_acceptance_scripts_and_questions(tmp_path):
    """Retained run cpos-tdg-sol-medium-all-001 and the 2026-11-10 inbox run: CP-1D, CP-3 and CP-5
    blocked only because no acceptance receipt or helper-script output exists in this transport.
    Only CP-2G was told that is not a reason to block."""
    # CP-8 is planned by CP-OS when an earlier run exists, never selected (tests/test_changes.py).
    _, texts = all_instructions(tmp_path, modules=tuple(m for m in METHODS if m != "CP-8"))
    assert set(texts) == set(METHODS) - {"CP-8"}
    for module, text in texts.items():
        head = text.partition(cpos_launch.METHOD_MARK)[0]
        for phrase in (
            "That check is the acceptance, validation and lineage the method asks",
            "do not block for want of an acceptance receipt",
            "`prepare_invocation.py`",
            "`validate_handoff.py`",
            "`completeness_check.py`",
            "do each check or calculation yourself",
            "Nobody can answer a question during this run",
            "then the method's declared safe default",
            "block only the decision the method ties to it",
            "is not in the method block below is unavailable",
            "Missing evidence still blocks exactly what the method says it blocks",
        ):
            assert phrase in head, (module, phrase)


# sha256 of method_text(module) at commit 1b41e65, before decisions 7, 9 and 11 changed the shared
# text (computed by calling method_text on that commit). The library marks a run "Earlier
# methods" when the text after METHOD_MARK differs, so the shared-text change must leave every
# one of these as it was. CP-8 alone changed on main after that commit (36a4c52, 184bfbb, 1e46c49:
# src/deploy_vii/methods/cp8.md, the withheld-difference rules); its pin is the merged text.
# CP-1D, CP-2, CP-2G, CP-2H, CP-3, CP-5 and CP-6 changed on 2026-11-13 (Deploy V methods plan,
# Task 5B): each takes one small named correction, so runs made before it are correctly marked
# "Earlier methods" for these seven modules.
# CP-2D, CP-4 and CP-4C changed on 2026-11-13 (Deploy V methods plan, Task 5A): they now send the
# caos-databricks versions with named edits, so runs made before it are correctly marked "Earlier
# methods" for these three modules.
# CP-4C changed again on 2026-11-13 (minors batch, named edit E4): the two phrases that pointed at
# the removed profile distinction (`In FULL_CREDIT_32, ` and ` in both profiles`) are cut.
# CP-3C changed on 2026-11-13 (Deploy V methods plan, Task 2): it now sends Deploy V's skill, so
# runs made before it are correctly marked "Earlier methods" for CP-3C.
# CP-0 changed on 2026-11-13 (Deploy V methods plan, Task 3): it now sends Deploy V's skill, so
# runs made before it are correctly marked "Earlier methods" for CP-0.
# CP-DR changed on 2026-11-13 (Deploy V methods plan, Task 4): it now sends the cp-os version 2.0
# skill with two named edits and no longer sends cpdr.md, so runs made before it are correctly
# marked "Earlier methods" for CP-DR.
# CP-1A and CP-2 changed on 2026-11-13 (owner: "Build rec. 1, then run"): they now send Deploy V's
# skills, so runs made before it are correctly marked "Earlier methods" for these two modules.
# Every prose module changed on 2026-11-13 (Deploy V methods plan, Task 6): the canon's Analytical
# appendix section is now sent after the reader-layer sections. The data modules (CP-0, CP-1,
# CP-1C, CP-PARSE) are unchanged.
# CP-6 changed again on 2026-11-13 (Task 5B fix round 1): its four stale `Downstream (QA)` header
# lines now say CP-5 is its upstream QA gate (caos wording).
# CP-2A changed again on 2026-11-13 (Deploy V methods plan, Task 6): it now sends the CP-OS-only
# copy of the short stress text (tables T2DS.n, two stale statements removed) instead of cp2a.md.
# CP-2A pin changed again on 2026-11-13 (final fix wave): the copy's line-1 comment now says it is
# the CP-OS copy of cp2a.md; nothing else in the file changed.
# CP-8 pin recomputed on 2026-11-13 (merge of origin/main into claude/deploy-v-methods): it is the
# merge of main's CP-8 method change (cp8.md redesign) with this branch's appendix section. Every
# other pin is this branch's value; main changed no other method text.
# CP-1 changed on 2026-11-13 (CP-1 moves to the Deploy V method): it now sends the edited caos
# dfff264 skill, runbook and step file, not the STEP_CONTRACTS sections, so runs made before it are
# correctly marked "Earlier methods" for CP-1. The score section follows, as for every skill module.
# Fix round 1 of that change (the acceptance check's rulings R2, R5, R9) edited the step file again.
METHOD_TEXT_SHA256_AT_1B41E65 = {
    "CP-0": "e8d3e77bc48bc98e2fd8595e7b46ee7fc786e859591cf244325f3508b7d5dac9",
    "CP-1": "30af21ed459c896ff61e5a4c0cb13f064349ae93c74a02ca4371be93e84edf69",
    "CP-1A": "4c8efcfafe748cd01e6c856041349397c77384c3c82566b1f36a429535c01639",
    "CP-1B": "38d9fa7b075d1ce5d0cd21bcc216f57f37369cd4db395b3f1fb65498697a509f",
    "CP-1C": "9353afdbce820f59c2dcabc951fc1ff3813174b3c84e79b47bc22bea97f3bbe8",
    "CP-1D": "d4d1ee4507d743cdb9d98bffd865ca3d012a4b4fb79a92a275cfc6a796bff453",
    "CP-2": "f925b66f13cff7bd7801d1c3cf7120eb1317126c8605bf1ff1875ce62ed3c162",
    "CP-2A": "5caf04f5b39bae89726bcd5929e8f17ca14b7d753f1ac718d58eda27baf9569f",
    "CP-2D": "fe39c49f842c99f6ffd390bd409cbb44adbbe397720d0a0d4d935b52a34a8fda",
    "CP-2E": "ab111a4fb0bd201b84dbec916ccdba6e5df92f60671b2d419949ca34d6118e34",
    "CP-2G": "268a85d82da39c9b7b66474b4052eb23b310f7fc5ce0c9d7efa25766a5699cf2",
    "CP-2H": "f500af91511584f3dda4d0dd10180766dabe19d81de7df12a99b6da2d92e89b4",
    "CP-3": "b84b8a08baa01a24a12f9f5e92a24dc735129a9dfec1449b4d8329833deef123",
    "CP-3C": "d1038d5097955d6bf47ccae01fee07bdc1db0b2e49eb7b77d0153c07b48768ac",
    "CP-3D": "a35a8a1d6f1b7aaecf7e98613e80a04c4c158f9163f315edbd004647463aa698",
    "CP-4": "a769b7456e5661d70cb25388fc4acb444cfd0aecd8f778554f98369ebadc7f7e",
    "CP-4C": "1d96547563190f89b909c37ea47969ecb04a2c794c5971b6db8f7c94c836b1f8",
    "CP-5": "9ac221698cc36a06473ce8cd9c2128c1705da362b289163d4ab54fda0d418d76",
    "CP-6": "115d07e8934f049b920e497834bcf61d53c6fe0cdd0266daf56b87d18d5e1f26",
    "CP-8": "0a0b339a9f9a284328b9a6fb50513a9bd03f2aa58dd45a387fe057b6ce2612c3",
    "CP-DR": "83aa5447c37db42db2e3df91cdd0cfaf491f37c0436fc8257c0d5fb43e735353",
    "CP-L10": "5b0e904dd62e1d1b341ec3d7d1717500d68ce1aee734b347e0dbbdfbe696b006",
}


def test_the_method_block_is_byte_identical_so_no_past_run_is_marked_earlier_methods():
    now = {m: hashlib.sha256(cpos_launch.method_text(m).encode()).hexdigest() for m in METHODS}
    assert now == METHOD_TEXT_SHA256_AT_1B41E65


def screen_module_names():
    source = (ROOT / "apps/issuer-library/credit_os/web/screen.js").read_text()
    groups = source.partition("const groups = [")[2].partition("\n];")[0]
    return dict(re.findall(r"\['(CP-[0-9A-Z]+)','([^']+)'\]", groups))


def test_module_names_equal_the_display_names_screen_js_shows():
    assert cpos_launch.MODULE_NAMES == screen_module_names()
    assert len(cpos_launch.MODULE_NAMES) >= 20


def test_every_module_is_told_the_reader_vocabulary_names_sources_and_chart_notes(tmp_path):
    """Owner decisions 7, 8, 9 and 11 of 2026-11-12: shared text before the method."""
    _, texts = all_instructions(tmp_path, modules=tuple(m for m in METHODS if m != "CP-8"))
    for module, text in texts.items():
        head = text.partition(cpos_launch.METHOD_MARK)[0]
        assert "record each as not run" not in head, module
        for phrase in (
            "Never mention the scripts, the tooling or anything that could not be run",
            "Do not state a confidence score, a confidence band or a QA status",
            (
                "this overrides the method's `qa_status`, confidence score and band fields, its "
                "Audit Summary score and its helper-script steps, so leave those fields and "
                "steps out"
            ),
            (
                "say in the Limitations passage or under `## Gaps`, in plain words, what could "
                "not be established and why it matters, without naming the file, script or "
                "module code"
            ),
            "a register written as bullets or prose follows the sentence rules",
            "Basis lines and the chart, map, event and forecast input sections",
            'write "not established" in plain words instead of the tag',
            "In every sentence under `## Findings`, `## Calculations` and `## Gaps`",
            (
                '"handoff", "this transport", "the pack", "fact pack", "source pack", '
                '"canonical", "re-anchor", "helper script", "upstream module"'
            ),
            "snake_case",
            "Refer to another module only by its plain name from this list",
            "Financial foundation; Earnings changes; Short credit snapshot",
            "`Source | Document | Document date | sha256 | Use`",
            "exact file name as supplied",
            "not stated",
            "Do not list the run settings",
            "at most 45 words",
            "at most 180 words",
        ):
            assert phrase in head, (module, phrase)
        assert "with its exact name and sha256" not in head, module
        assert ("one sentence stating the main qualification" in head) == (
            "### Chart data:"
            in text.partition(cpos_launch.METHOD_MARK)[0].partition(
                "Report selectors, each exactly once"
            )[2]
        ), module
        assert ("at most 60 characters" in head) == (
            "### Map:" in head.partition("Report selectors, each exactly once")[2]
        ), module
    chart = [m for m, t in texts.items() if "one sentence stating the main qualification" in t]
    assert {"CP-1", "CP-2D"} <= set(chart) and any(
        "at most 60 characters" in t for t in texts.values()
    )
    assert all('"No qualification."' in texts[m] for m in chart)


def test_modules_run_after_the_handoffs_their_methods_consume(tmp_path):
    """Retained run cpos-tdg-sol-medium-all-001: CP-2E and CP-2A ran before CP-2, and CP-2A blocked
    with "Required fundamental handoff CP-2 is Not supplied"."""
    prepared, _ = all_instructions(tmp_path, modules=tuple(m for m in METHODS if m != "CP-8"))
    order = list(prepared.plan.instructions)
    for consumer, producers in {
        "CP-2A": ("CP-2", "CP-1B"),  # cp-2a SKILL.md: "Upstream: CP-1, CP-1B, CP-2"
        "CP-2E": ("CP-2", "CP-1", "CP-1A"),  # cp-2e SKILL.md: "Upstream: CP-1, CP-1A, CP-2"
        "CP-1C": ("CP-DR",),  # cpdr.md: CP-1C reads the peer pack
        "CP-2": ("CP-DR",),  # cpdr.md: CP-2 is a named receiver
        "CP-2G": ("CP-2A",),
    }.items():
        for producer in producers:
            assert order.index(producer) < order.index(consumer), (producer, consumer, order)


def test_cp2a_is_told_which_method_governs_the_stress_sizes(tmp_path):
    """The two CP-2A methods sent disagree: cp2a.md has the analyst choose the shock sizes as
    labelled assumptions, the SKILL forbids an "unsupported stress magnitude". Run
    tdg-forecast-005: CP-2A gave no shock, so no stress case was computed."""
    _, texts = all_instructions(tmp_path, modules=("CP-0", "CP-1", "CP-2A", "CP-2G"))
    head = texts["CP-2A"].partition(cpos_launch.METHOD_MARK)[0]
    assert "`CP-2A_STRESS_DESIGN_CPOS.md` governs" in head
    assert "cp2a.md" not in head
    assert "labelled analyst assumptions" in head and "anchored to a stated figure" in head
    assert "an EBITDA decline and a cash-interest rate increase" in head
    assert "at most four decimal places" in head
    assert "Stress design" not in texts["CP-2G"].partition(cpos_launch.METHOD_MARK)[0]


def test_cp1_is_asked_for_the_period_table_whenever_a_forecast_is_wanted(tmp_path):
    # A forecast is wanted with CP-2G, or with CP-MODEL (the layer-1 path, no CP-2G).
    for modules in (("CP-0", "CP-1", "CP-2A", "CP-2G"), ("CP-0", "CP-1", "CP-2A", "CP-MODEL")):
        folder = tmp_path / "-".join(modules)
        folder.mkdir()
        _, texts = all_instructions(folder, modules=modules)
        head = texts["CP-1"].partition(cpos_launch.METHOD_MARK)[0]
        for words in (
            "`| Period | Start | End |`",
            "YYYY-MM-DD",
            "exactly as you print it",
            "`9M 2025`",
            "add no figure",
        ):
            assert words in head
        assert all(
            "| Period | Start | End |" not in text for name, text in texts.items() if name != "CP-1"
        )


def test_cp1_is_asked_for_the_period_table_in_one_sentence_when_no_forecast_is_wanted(tmp_path):
    # R11: the acceptance check needs the table on every run; without a forecast the short
    # sentence asks for it, and no other module is asked.
    _, texts = all_instructions(tmp_path, modules=("CP-0", "CP-1", "CP-2A"))
    head = texts["CP-1"].partition(cpos_launch.METHOD_MARK)[0]
    assert cpos_launch.PERIOD_REQUIRED_BLOCK in head
    assert cpos_launch.PERIOD_TABLE_BLOCK not in head
    assert head.count("| Period | Start | End |") == 1
    assert all("| Period | Start | End |" not in t for n, t in texts.items() if n != "CP-1")


def test_cp1_is_told_to_print_the_period_table_once_when_a_forecast_is_wanted(tmp_path):
    _, texts = all_instructions(tmp_path, modules=("CP-0", "CP-1", "CP-2A", "CP-2G"))
    head = texts["CP-1"].partition(cpos_launch.METHOD_MARK)[0]
    assert cpos_launch.PERIOD_TABLE_BLOCK in head
    assert cpos_launch.PERIOD_REQUIRED_BLOCK not in head
    assert head.count("| Period | Start | End |") == 1


def test_the_presets_are_the_owners_answer_key():
    from deploy_vii.contracts import PATHWAY_MODULES as PRESETS

    assert {p: set(m) for p, m in PRESETS.items()} == {
        p: set(key.split()) for p, key in PRESET_ANSWER_KEY.items()
    }
    assert all(len(m) == len(set(m)) for m in PRESETS.values())


@pytest.mark.parametrize("pathway", sorted(set(PATHWAY_MODULES) - {"lite_credit_assessment"}))
@pytest.mark.parametrize("peer_source", ["cp_dr_public", "user_list", "user_comps", "none"])
def test_cpdr_and_cp2e_are_in_every_pathway_and_run_in_order(tmp_path, pathway, peer_source):
    """Owner, 2026-11-11: "cp-dr should be on every run or cp-1c wont work. so should cp-2e."
    The peer source no longer adds or drops CP-DR; the preset carries it."""
    prepared, _ = all_instructions(tmp_path, pathway, peer_source=peer_source)
    order = list(prepared.plan.instructions)
    assert order == list(PATHWAY_MODULES[pathway])
    assert {"CP-DR", "CP-2E"} <= set(order)
    assert "CP-DR" in prepared.plan.run.requested_modules
    if "CP-1C" in order:
        assert order.index("CP-DR") < order.index("CP-1C")
    if "CP-2" in order:
        assert order.index("CP-2E") > order.index("CP-2")
    if "CP-2G" in order:
        assert order.index("CP-2A") < order.index("CP-2G")


def test_explicit_modules_are_run_as_given(tmp_path):
    prepared, _ = all_instructions(
        tmp_path, "relative_value", modules=("CP-0", "CP-1", "CP-1A", "CP-2", "CP-1C")
    )
    assert "CP-DR" not in prepared.plan.instructions


@pytest.mark.parametrize(
    ("peer_source", "modules", "asked"),
    [
        ("cp_dr_public", ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-DR", "CP-1C"), True),
        ("cp_dr_public", ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-DR"), False),
        ("none", ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-DR", "CP-1C"), False),
    ],
)
def test_cpdr_is_asked_for_the_peer_pack_cp1c_reads_by_default(
    tmp_path, peer_source, modules, asked
):
    """Owner, 2026-11-10: "Cp-1c is supposed to get that information from cp-dr by default"."""
    _, texts = all_instructions(tmp_path, "relative_value", modules, peer_source)
    research = texts["CP-DR"].partition(cpos_launch.METHOD_MARK)[0]
    assert ("this run requests the peer pack" in research) is asked
    if asked:
        for phrase in ("TDR.4", "TDR.5", "TDR.6", "`revenue`, `ebitda`, `debt`, `interest`, `ffo`"):
            assert phrase in research, phrase
        assert "Name no peer and type no figure from memory" in research
        assert "cpdr.md" not in research  # CP-DR is no longer sent that file
        assert "as your method's PEER PACK section describes them" in research
        assert "that row cites its TDR.2 gap row" in research
        assert "whose `peer_id` is `none` (row header `none.none`)" in research
        assert "still write the three tables" in research
        benchmark = texts["CP-1C"].partition(cpos_launch.METHOD_MARK)[0]
        assert "take the peer set and its figures from the CP-DR handoff's TDR.4" in benchmark
        assert "You own inclusion, comparability, normalisation and every statistic" in benchmark
    elif "CP-1C" in texts:
        assert "CP-DR handoff's TDR.4" not in texts["CP-1C"].partition(cpos_launch.METHOD_MARK)[0]


def test_the_bottom_line_is_retained_in_the_accepted_handoff(tmp_path, provider):
    argv = launch(tmp_path, "--live", "--ruling", str(RULING))
    routes = list(
        prepare(
            tmp_path / "context.json",
            tmp_path / "issuer",
            tmp_path / "preview",
            config="sol-medium",
            cap="50",
        ).plan.layout.routes
    )
    provider.answer = lambda context: covenant_answer(context, routes)
    assert main(argv) == 0
    folder = next((tmp_path / "out/deliveries").glob("*/delivery.json")).parent
    handoffs = [p for p in folder.rglob("*.md") if READER_BOTTOM_LINE in p.read_text()]
    assert handoffs, "no accepted handoff in the delivery folder carries the bottom line"


def strip_of(prepared, raw: str, tmp_path: Path, block: str):
    routes = tuple(r for r in prepared.layout.routes if r.module_id == "CP-1")
    own = prepared.layout.model_copy(
        update={
            "blocks": tuple(dict.fromkeys(r.block_id for r in routes)),
            "routes": routes,
            "front": (),
        }
    )
    (tmp_path / "cp-1.md").write_text(raw)
    handoff = HandoffInput(path="cp-1.md", sha256=hashlib.sha256(raw.encode()).hexdigest())
    request = DeliveryRequest(run=prepared.plan.run, handoffs={"CP-1": handoff}, layout=own)
    report = ReportView.model_validate_json(markdown_files(request, tmp_path)["report-view.json"])
    return next(b for b in report.blocks if b.block_id == block)


def test_cp1_chart_tables_become_the_report_chart_strip(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()
    figures = strip_of(prepared, raw, tmp_path, "model-chart-strip").figures
    assert [f.fig_id for f in figures] == ["S.1", "S.2", "S.3", "S.4"]
    assert [m.value for m in figures[0].chart.marks] == [
        Decimal("3.75"),
        Decimal("3.00"),
        Decimal("2.80"),
        Decimal("2.25"),
    ]
    assert [m.value for m in figures[3].chart.marks] == [Decimal(500), None, Decimal(1250)]
    assert figures[3].chart.marks[1].ref_id.startswith("G")


def test_an_all_gaps_non_usd_issuer_passes_with_no_chart_values(tmp_path, monkeypatch):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    monkeypatch.setitem(
        CHART_TABLES, "Chart data: liquidity", NON_USD_TABLES["Chart data: liquidity"]
    )
    monkeypatch.setitem(
        CHART_TABLES, "Chart data: debt maturities", NON_USD_TABLES["Chart data: debt maturities"]
    )
    raw = answer(context, list(prepared.plan.layout.routes))
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()
    figures = strip_of(prepared, raw, tmp_path, "model-chart-strip").figures
    assert all(m.value is None for f in figures[2:] for m in f.chart.marks)


@pytest.mark.parametrize(
    ("old", "new", "complaint"),
    [
        ("| 3.00 |", "| 3.00x |", "3.00x"),
        ("| 300 | 450 | US$m |", "| 300 | 450 | EUR m |", "EUR m"),
        ("| FY2023 | 3.20 | x | Synthetic. |", "| FY2023 | 3.20 | x |  |", "Basis and limitation"),
        ("### Chart data: liquidity", "### Liquidity data", "Chart data: liquidity"),
        ("| Period | Debt maturing |", "| Year | Debt maturing |", "Period"),
        ("| FY2026 | 500 |", "| FY2026 | Not supplied: |", "Not supplied: |"),
    ],
)
def test_checker_refuses_each_broken_chart_table(tmp_path, old, new, complaint):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new).encode(), checker(prepared.layout))
    assert any(complaint in issue for issue in issues), issues


def _header(*columns: str) -> str:
    return (
        "`| " + " | ".join(("Period", *columns, "Reporting unit", "Basis and limitation")) + " |`"
    )


CHART_HEADERS = {
    "Chart data: leverage": _header("Total debt / EBITDA", "Net debt / EBITDA"),
    "Chart data: interest cover": _header("EBITDA / cash interest"),
    "Chart data: liquidity": _header("Cash", "Undrawn committed facilities"),
    "Chart data: debt maturities": _header("Debt maturing"),
}


@pytest.mark.parametrize(
    "pathway",
    [
        *("credit_snapshot", "earnings_update", "relative_value", "covenant_refinancing"),
        *("distressed_restructuring", "portfolio_decision", "short_snapshot"),
        "lite_credit_assessment",
    ],
)
def test_every_pathway_asks_cp1_for_the_four_chart_tables_and_requires_them(tmp_path, pathway):
    """Owner, 2026-11-12, "Yes, all pathways": CP-8's pack reads these tables on each one."""
    prepared, task, context = good_task(tmp_path, "CP-1", pathway)
    text = (tmp_path / "out" / prepared.plan.instructions["CP-1"].path).read_text()
    for heading, header in CHART_HEADERS.items():
        assert text.count(f"`### {heading}`") == 1, heading
        assert header in text, heading
    raw = answer(context, list(prepared.plan.layout.routes))
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()
    for heading in CHART_HEADERS:
        cut = raw.replace(f"### {heading}", "### Dropped")
        issues = _checked_handoff(task, cut.encode(), checker(prepared.layout))
        assert any(heading in issue for issue in issues), (heading, issues)


def test_the_instructions_give_the_exact_chart_table_header(tmp_path):
    prepared, *_ = good_task(tmp_path, "CP-1", "credit_snapshot")
    text = (tmp_path / "out" / prepared.plan.instructions["CP-1"].path).read_text()
    assert (
        "`| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit | Basis and limitation |`"
        in text
    )
    assert "Not supplied: reported in <unit>" in text


def test_a_run_without_cp1_still_omits_the_chart_block(tmp_path):
    prepared = prepare(
        context_file(tmp_path, "credit_snapshot"),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
        modules=("CP-1A",),
    )
    assert "CP-1" not in prepared.ordered
    assert "model-chart-strip" in prepared.omitted


def test_yield_against_maturity_stays_omitted(tmp_path):
    prepared = prepare(
        context_file(tmp_path, "relative_value"),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    assert "yield-against-maturity" in prepared.omitted


def test_the_report_scope_no_longer_says_charts_are_unpublished(tmp_path):
    # Every preset now publishes a forecast (CP-MODEL, or CP-2G): earnings_update from CP-1's
    # run-rate figures (owner, 2026-11-11), credit_snapshot from CP-2G. The scope with no forecast
    # is read on an explicit module list.
    prepared, *_ = good_task(tmp_path, "CP-1", "earnings_update")
    assert "run-rate figures" in prepared.layout.scope
    assert "charts" not in prepared.layout.scope.lower()
    (tmp_path / "b").mkdir()
    bare = prepare(
        context_file(tmp_path / "b", "earnings_update"),
        issuer_folder(tmp_path / "b"),
        tmp_path / "b" / "out",
        config="sol-medium",
        cap="50",
        modules=("CP-1",),
    )
    assert "The HTML Model and calculation JSON are not published" in bare.plan.layout.scope
    (tmp_path / "f").mkdir()
    forecast, *_ = good_task(tmp_path / "f", "CP-1", "credit_snapshot")
    assert "A forecast table is published with the issuer report" in forecast.layout.scope
    assert "charts" not in forecast.layout.scope.lower()


def test_six_handoff_headings_are_still_enforced(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-0")
    raw = answer(context, []).replace("## Gaps", "## Risks").encode()
    assert "## " + HEADINGS[4] in _checked_handoff(task, raw, checker(prepared.layout))[0]


# runs/cpos-launch-live-001 is the retained attempt that the context bound below repairs.
LIVE_CASE = ROOT / "runs/cpos-launch-live-002"
LIVE_MODULES = {"CP-0", "CP-1", "CP-1A"}


def assert_live_evidence(out: Path, cap: Decimal) -> None:
    """Actual provider calls, handoffs consumed downstream, and filed values in the report.

    Expected values were read from the visible text of the filed 10-K's statements, not from any
    run: NET SALES 7,940 and cash 6,261, USD millions, fiscal year ended September 30, 2024.
    """
    records = [json.loads(n) for n in (out / "live/calls.jsonl").read_text().splitlines()]
    assert {r["module_id"] for r in records} == LIVE_MODULES
    assert all(r["requested_model"] == "gpt-6.1-sol" for r in records)
    assert {r["reported_model"] for r in records} == {"gpt-6.1-sol"}
    assert all(r["request_id"] for r in records)
    charged = sum(Decimal(str(r["settled_usd"])) for r in records)
    assert 0 < charged <= cap
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["execution"] == "live-provider"
    assert set(completed["module_execution"]) == LIVE_MODULES
    assert set(completed["module_execution"].values()) == {"live-provider"}
    report = next((out / "deliveries").glob("*/delivery.json"))
    assert verify_delivery(next(out.glob("delivery-*.json")), report.parent) == report
    handoffs = {m: (report.parent / f"{m}.md").read_bytes() for m in LIVE_MODULES}
    digest = {m: hashlib.sha256(raw).hexdigest().encode() for m, raw in handoffs.items()}
    assert digest["CP-0"] in handoffs["CP-1"]
    assert digest["CP-0"] in handoffs["CP-1A"] and digest["CP-1"] in handoffs["CP-1A"]
    for filed in (b"7,940", b"6,261"):
        assert filed in handoffs["CP-1"]
        assert filed in (report.parent / "report-view.json").read_bytes()
    view = json.loads((report.parent / "report-view.json").read_text())
    assert {b["block_id"]: b["state"] for b in view["blocks"]} == {
        "company-operating-model": "populated",
        "model-chart-strip": "populated",
        "financials-credit-metrics": "populated",
        "company-profile": "populated",
        "transaction-summary": "populated",
    }


@pytest.mark.live
def test_live_launch_from_a_context_file_and_issuer_folder():
    """Paid. Historical TDG FY2024 as of 2024-09-30; proves this launch path, not current credit.

    Answers stay in the run folder, so a rerun rechecks them and sends nothing. Needs the provider
    key in the environment and CPOS_LIVE_RULING naming a docs/rulings file that lists sol-medium.
    """
    ruling = os.environ.get("CPOS_LIVE_RULING")
    if not ruling or not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("paid: set CPOS_LIVE_RULING and OPENAI_API_KEY to run")
    # Its own folder: the launcher now asks for more, so answers retained in LIVE_CASE cannot be
    # reused, and that retained run must not change. The USD 12 is the owner-approved maximum.
    out = ROOT / "runs/cpos-reader-live-001"
    cap = Decimal(12)
    code = main(
        [
            *("--context", str(LIVE_CASE / "context.json")),
            *("--sources", str(ROOT / "data/public-corpus/v1/TDG")),
            *("--config", "sol-medium", "--cap", str(cap), "--modules", "CP-1", "CP-1A"),
            *("--out", str(out), "--live", "--ruling", ruling),
        ]
    )
    assert code == 0
    assert_live_evidence(out, cap)


COPILOT_RULING = (
    "lifts: live-provider-pause\nby: user\ndate: 2026-11-01\n"
    "configs: copilot-sol-medium copilot-opus-medium\n"
)


@pytest.fixture
def copilot_ruling(tmp_path, monkeypatch):
    root = tmp_path / "rulings"
    root.mkdir()
    ruling = root / "copilot.md"
    ruling.write_text(COPILOT_RULING, encoding="utf-8")
    monkeypatch.setattr("deploy_workflow.model.adapter.LIVE_RULINGS_ROOT", root)
    return ruling


def copilot_argv(tmp_path, config, *extra):
    argv = launch(tmp_path, *extra)
    argv[argv.index("--config") + 1] = config
    return argv


def test_launcher_reports_copilot_key_variable(tmp_path, monkeypatch, capsys, copilot_ruling):
    monkeypatch.delenv("COPILOT_GITHUB_TOKEN", raising=False)
    argv = copilot_argv(tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling))
    assert main(argv) == 2
    assert "COPILOT_GITHUB_TOKEN" in capsys.readouterr().err


def test_launcher_names_both_copilot_credentials_when_neither_is_set(
    tmp_path, monkeypatch, capsys, copilot_ruling
):
    monkeypatch.delenv("COPILOT_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("COPILOT_USE_GH_LOGIN", "true")
    argv = copilot_argv(tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling))
    assert main(argv) == 2
    err = capsys.readouterr().err
    assert "COPILOT_GITHUB_TOKEN" in err and "COPILOT_USE_GH_LOGIN" in err


def test_copilot_gh_login_opt_in_passes_the_key_check(
    tmp_path, monkeypatch, capsys, copilot_ruling
):
    monkeypatch.delenv("COPILOT_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("COPILOT_USE_GH_LOGIN", "1")
    runtime = tmp_path / "copilot-runtime"
    runtime.write_text("#!/bin/sh\n")
    monkeypatch.setenv("COPILOT_CLI_PATH", str(runtime))
    monkeypatch.setattr(cpos_launch, "run_live_handoffs", lambda m, d, **k: d / "delivery.json")
    argv = copilot_argv(tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling))
    assert main(argv) == 0


def test_copilot_config_without_live_sends_nothing_and_shows_the_plan(
    tmp_path, capsys, monkeypatch
):
    started = []
    monkeypatch.setattr(cpos_launch, "run_live_handoffs", lambda *a, **k: started.append(1))
    assert main(copilot_argv(tmp_path, "copilot-opus-medium")) == 0
    printed = capsys.readouterr().out
    assert "copilot-opus-medium" in printed and "claude-opus-5.5" in printed and started == []


def test_copilot_config_reaches_the_live_run_with_its_config(
    tmp_path, monkeypatch, capsys, copilot_ruling
):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "ghp_" + "Z" * 36)
    runtime = tmp_path / "copilot-runtime"
    runtime.write_text("#!/bin/sh\n")
    monkeypatch.setenv("COPILOT_CLI_PATH", str(runtime))
    seen = {}

    def fake_run(manifest, directory, **kwargs):
        seen.update(kwargs)
        return directory / "delivery.json"

    monkeypatch.setattr(cpos_launch, "run_live_handoffs", fake_run)
    argv = copilot_argv(tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling))
    assert main(argv) == 0
    assert seen["config"] == "copilot-sol-medium" and seen["ruling"] == copilot_ruling


def test_live_copilot_without_a_runtime_path_is_refused_before_any_folder(
    tmp_path, monkeypatch, capsys, copilot_ruling
):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "ghp_" + "Z" * 36)
    monkeypatch.delenv("COPILOT_CLI_PATH", raising=False)
    argv = copilot_argv(tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling))
    assert main(argv) == 2
    assert "COPILOT_CLI_PATH" in capsys.readouterr().err
    assert not Path(argv[argv.index("--out") + 1]).exists()


def test_a_release_note_on_the_stop_is_shown_in_stderr(
    tmp_path, monkeypatch, capsys, copilot_ruling
):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "ghp_" + "Z" * 36)
    runtime = tmp_path / "copilot-runtime"
    runtime.write_text("#!/bin/sh\n")
    monkeypatch.setenv("COPILOT_CLI_PATH", str(runtime))

    def stops(manifest, directory, **kwargs):
        error = RuntimeError("cpos_live_stopped: sent_unknown")
        error.add_note("adapter release also failed: stop failed: OSError")
        raise error

    monkeypatch.setattr(cpos_launch, "run_live_handoffs", stops)
    argv = copilot_argv(tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling))
    assert main(argv) == 1
    assert "adapter release also failed: stop failed: OSError" in capsys.readouterr().err


def test_the_launcher_layout_has_no_front_routes_now_the_reader_summary_is_retired(tmp_path):
    full = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    assert full.plan.layout.front == ()


# --- Expectations carried by prepare ---------------------------------------------------
KEY = json.loads((ROOT / "tests/fixtures/run-expectations/outcome-key.json").read_text())


def declared_context(tmp_path: Path, pathway: str, **attachments: object) -> Path:
    path = context_file(tmp_path, pathway)
    data = json.loads(path.read_text())
    data["attachments"].update(attachments)
    data["identity"]["issue_classification"] = "high_yield"
    path.write_text(json.dumps(data))
    return path


def report_folder(tmp_path: Path) -> Path:
    folder = tmp_path / "issuer"
    folder.mkdir()
    (folder / "annual-report-10-K.txt").write_text("FORM 10-K\nAnnual report for 2024.\n")
    return folder


def prepared_with(tmp_path: Path, context: Path, folder: Path, **extra):
    return prepare(context, folder, tmp_path / "out", config="sol-medium", cap="50", **extra)


def test_prepared_carries_each_pinned_sources_guess_and_the_expectations(tmp_path):
    folder = tmp_path / "issuer"
    folder.mkdir()
    (folder / "agreement.txt").write_text("CREDIT AGREEMENT\nExecution Version\n")
    (folder / "misc.md").write_text("Net sales were 100.")
    prepared = prepared_with(tmp_path, declared_context(tmp_path, "covenant_refinancing"), folder)
    by_source = {d["source"]: d for d in prepared.documents}
    assert set(by_source) == {"agreement.txt", "misc.md"}
    assert set(by_source["agreement.txt"]) == {"source", "kind", "signal", "executed", "period_end"}
    assert by_source["agreement.txt"]["kind"] == "credit_agreement"
    assert by_source["agreement.txt"]["executed"] is True
    assert by_source["misc.md"]["kind"] == "unrecognised"
    assert by_source["misc.md"]["executed"] is None
    assert all(i["id"] and i["outcome"] for i in prepared.expectations)


def test_html_guess_is_keyed_by_the_pinned_text_source_and_skips_the_file_name_header(tmp_path):
    folder = tmp_path / "issuer"
    folder.mkdir()
    (folder / "credit agreement.html").write_text("<html><body><p>Net sales were 100.</p></body>")
    prepared = prepared_with(tmp_path, declared_context(tmp_path, "covenant_refinancing"), folder)
    (document,) = prepared.documents
    assert document["source"] == "credit agreement.html.jsonl"
    # The name says "credit agreement"; the page header naming the file is not cover text, and the
    # name is still a (weaker) signal.
    assert document["signal"].startswith("file name contains")


def test_only_the_first_three_pages_of_each_source_reach_the_guess(tmp_path, monkeypatch):
    seen = {}

    def spy(name, pages):
        seen[name] = list(pages)
        return real(name, pages)

    real = cpos_launch.guess_kind
    monkeypatch.setattr(cpos_launch, "guess_kind", spy)
    folder = tmp_path / "issuer"
    folder.mkdir()
    # Text files are cut into 12,000-character pages: this one has five.
    long = "".join(f"line {n} " + "x" * 3990 + "\n" for n in range(15))
    (folder / "long.txt").write_text(long)
    (folder / "short.md").write_text("Notes mature in 2030.")
    prepared_with(tmp_path, declared_context(tmp_path, "covenant_refinancing"), folder)
    assert len(_pages("long.txt", long.encode())) == 5
    assert seen["long.txt"] == _pages("long.txt", long.encode())[:3]
    assert seen["short.md"] == ["Notes mature in 2030."]


def test_the_declarations_do_not_change_any_instruction_byte(tmp_path):
    def instructions(legal: str, run_type: str) -> dict[str, bytes]:
        out = tmp_path / legal / run_type
        context = declared_context(tmp_path / legal, "covenant_refinancing", legal_documents=legal)
        data = json.loads(context.read_text())
        data["run"]["run_type"] = run_type
        context.write_text(json.dumps(data))
        prepared = prepare(
            context, report_folder(tmp_path / legal), out, config="sol-medium", cap="50"
        )
        return {m: (out / "instructions" / f"{m}.md").read_bytes() for m in prepared.ordered}

    (tmp_path / "executed").mkdir()
    (tmp_path / "none").mkdir()
    assert instructions("executed", "research") == instructions("none", "secondary")


def without_of(prepared) -> list[dict]:
    return [
        {"module": m, "removes": r}
        for m, r in without_for(prepared.ordered, prepared.expectations).items()
    ]


def test_legal_none_will_refuse_offers_run_without_exactly_as_the_key_has_it(tmp_path):
    scenario = next(s for s in KEY["scenarios"] if s["id"] == "a-live-legal-none-will-refuse")
    (tmp_path / "x").mkdir()
    context = declared_context(tmp_path / "x", scenario["pathway"], legal_documents="none")
    prepared = prepared_with(tmp_path, context, report_folder(tmp_path / "x"))
    assert list(prepared.ordered) == scenario["modules"]
    assert without_of(prepared) == scenario["expected"]["without"]
    refusals = [i for i in prepared.expectations if i["outcome"] == "will_refuse"]
    assert [i["scope"] for i in refusals] == ["CP-4"]
    # Plan fact: the files and the refusal are unchanged by the forecast.
    assert prepared.plan.run.pathway == scenario["pathway"]


def test_without_removes_modules_that_require_the_refused_one(tmp_path):
    (tmp_path / "x").mkdir()
    context = declared_context(tmp_path / "x", "distressed_restructuring", legal_documents="none")
    prepared = prepared_with(tmp_path, context, report_folder(tmp_path / "x"))
    # methodology.json: CP-4C requires CP-4; CP-3 and CP-5 list CP-4 only as optional.
    assert "CP-4C" in prepared.ordered
    assert without_for(prepared.ordered, prepared.expectations) == {"CP-4": ["CP-4", "CP-4C"]}


def test_without_follows_required_dependencies_transitively_and_in_run_order():
    ordered = plan(("CP-0", "CP-1", "CP-2A", "CP-2G", "CP-2H", "CP-4C", "CP-5"))
    refused = Item(
        id="CP-2A:declared",
        scope="CP-2A",
        outcome="will_refuse",
        reason="",
        fix="",
        basis="",
        evidence="per method",
        counted=True,
        inherited_from=None,
    )
    # By hand from methodology.json `required`: CP-2G requires CP-2A; CP-2H and CP-4C require CP-2G.
    # CP-5 lists them only as optional and stays.
    expected = {"CP-2A", "CP-2G", "CP-2H", "CP-4C"}
    result = without_for(ordered, [refused])
    assert set(result["CP-2A"]) == expected
    assert result["CP-2A"] == [m for m in ordered if m in expected]
    inherited = Item(**{**refused, "id": "CP-2G:from:CP-2A", "inherited_from": ["CP-2A"]})
    assert without_for(ordered, [inherited]) == {}


def library_launch(tmp_path, monkeypatch, copilot_ruling, update):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "ghp_" + "Z" * 36)
    runtime = tmp_path / "copilot-runtime"
    runtime.write_text("#!/bin/sh\n")
    monkeypatch.setenv("COPILOT_CLI_PATH", str(runtime))
    monkeypatch.setattr(
        cpos_launch,
        "run_live_handoffs",
        lambda manifest, directory, **k: directory / "delivery.json",
    )
    monkeypatch.setattr(cpos_launch, "update_library_at", update)
    argv = copilot_argv(tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling))
    argv[argv.index("--out") + 1] = str(tmp_path / "runs" / "x")
    return main(argv)


def test_completed_run_updates_the_library(tmp_path, monkeypatch, capsys, copilot_ruling):
    calls = []

    class Built:
        runs = ({"id": "x"},)

    def update(workspace):
        calls.append(workspace)
        return Built()

    assert library_launch(tmp_path, monkeypatch, copilot_ruling, update) == 0
    assert calls == [tmp_path] and "Library:" in capsys.readouterr().out


def test_library_failure_keeps_the_run(tmp_path, monkeypatch, capsys, copilot_ruling):
    def update(workspace):
        raise OSError("disk full")

    assert library_launch(tmp_path, monkeypatch, copilot_ruling, update) == 0
    captured = capsys.readouterr()
    assert "disk full" in captured.err
    assert f"python apps/issuer-library/update_library.py --workspace {tmp_path}" in captured.err
    assert f"Delivery: {tmp_path / 'runs' / 'x' / 'delivery.json'}" in captured.out


def test_refresh_library_loads_the_checkout_update_library(tmp_path, capsys):
    """The real file-location loader, no stand-in: an empty workspace gets its library page."""
    (tmp_path / "runs" / "x").mkdir(parents=True)
    cpos_launch._refresh_library(tmp_path / "runs" / "x")
    assert (tmp_path / "library" / "index.html").is_file()
    assert f"Library:  {tmp_path / 'library' / 'index.html'} (0 run(s))" in capsys.readouterr().out


def test_refresh_library_reports_a_real_refusal_and_keeps_going(tmp_path, capsys):
    (tmp_path / "runs" / "x").mkdir(parents=True)
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / "library").symlink_to(tmp_path / "elsewhere")
    cpos_launch._refresh_library(tmp_path / "runs" / "x")
    err = capsys.readouterr().err
    assert "is a link or a file" in err and f"--workspace {tmp_path}" in err


# --- the CP-2G forecast delivery. Synthetic; not analytical review. -------------------------------
# Inputs the fake CP-2G handoff states. Every literal terminates in decimal, so the answer key
# below is exact in fractions; it re-expresses the lease's arithmetic and calls no production code.
BASE = {
    "revenue": "1000",
    "ebitda": "300",
    "interest": "36",
    "taxes": "20",
    "wc": "10",
    "capex": "40",
    "fcf": "194",
    "debt": "600",
    "cash": "100",
    "undrawn": "50",
}


def printed(key: str, amount: str) -> str:
    """How CP-1 prints a base operand. A working capital investment (the operand, an outflow) is
    printed negative, as CP-2G reads it (`Operands.from_cp1` reverses the sign): `(10)` for 10."""
    return f"({amount})" if key == "wc" else amount


PATHS = {
    "revenue_growth": ("0.05", "0.04", "0.03"),
    "ebitda_margin": ("0.30", "0.31", "0.32"),
    "capex_pct_revenue": ("0.04", "0.04", "0.04"),
    "tax_wc_pct_revenue": ("0.10", "0.10", "0.10"),
    "interest_rate": ("0.06", "0.06", "0.06"),
    "dividends": ("20", "20", "20"),
    "debt_repayment": ("50", "50", "50"),
}
# The usual `--out runs/<name>`: the folder name is not the run ID, and the library still shows the
# model under that run.
RUN_ID = "my-first-run"
SHOCK = {"ebitda_decline": "0.20", "rate_increase": "0.10"}
RATIOS = {"total_leverage", "net_leverage", "coverage", "fcf_to_debt"}


def forecast_block(**changes) -> str:
    inputs = {
        "schema_version": "cpos-forecast-inputs/1",
        "base": {k: {"amount": v, "reason": None} for k, v in BASE.items()},
        "base_drivers": {
            name: {
                "values": list(values),
                "category": "Analyst Interpretation",
                "rationale": "Synthetic.",
                "limitation": None,
            }
            for name, values in PATHS.items()
        },
        "downside_shock": SHOCK,
        "years": [
            {"year": 2025 + i, "start": f"{2025 + i}-04-01", "end": f"{2026 + i}-03-31"}
            for i in range(3)
        ],
        "scope_limits": ["Synthetic; not analytical review."],
        **changes,
    }
    return f"### Forecast inputs (machine-readable)\n\n```json\n{json.dumps(inputs)}\n```\n"


def forecast_answer(
    context: dict, routes: list, block: str | None = None, cp1_block: str | None = None
) -> str:
    """CP-1 prints the base amounts (and ends with the layer-1 block when `cp1_block` is given);
    CP-2G ends its findings with the inputs block."""
    text = answer(context, routes)
    if context["module_id"] == "CP-1":
        rows = "\n".join(f"| {k} | {printed(k, v)} |" for k, v in BASE.items())
        # Above the owner's chart table, so the base amounts do not read as rows of that table.
        mark = "### Chart data: revenue and EBITDA"
        # Where another chart table sits above (the covenant pathway), or none, the base table
        # gets a heading of its own.
        alone = mark in text and "### Chart data: debt maturities" not in text
        lead = "" if alone else "### Base operands\n\n"
        mark = mark if mark in text else "## Calculations"
        text = text.replace(mark, f"{lead}| Base | FY2025 |\n| --- | --- |\n{rows}\n\n{mark}", 1)
        if cp1_block is not None:
            text = text.replace("## Calculations", f"{cp1_block}\n## Calculations", 1)
        return text
    if context["module_id"] == "CP-2G" and block is not None:
        return text.replace("## Calculations", f"{block}\n## Calculations", 1)
    return text


def key_case(shock: dict | None, paths: dict = PATHS) -> list[dict[str, Fraction]]:
    """The three forecast years from the stated inputs, in exact fractions."""
    p = {name: [Fraction(v) for v in values] for name, values in paths.items()}
    s, k = (
        (Fraction(shock["ebitda_decline"]), Fraction(shock["rate_increase"])) if shock else (0, 0)
    )
    revenue, debt, cash, undrawn = Fraction(1000), Fraction(600), Fraction(100), Fraction(50)
    years = []
    for t in range(3):
        revenue *= 1 + p["revenue_growth"][t]
        ebitda = revenue * p["ebitda_margin"][t] * (1 - s)
        interest = debt * p["interest_rate"][t] * (1 + k)
        tax_wc = revenue * p["tax_wc_pct_revenue"][t]
        capex = revenue * p["capex_pct_revenue"][t]
        cfo = ebitda - interest - tax_wc
        fcf = cfo - capex
        closing_debt = debt - p["debt_repayment"][t]
        closing_cash = cash + fcf - p["dividends"][t] - p["debt_repayment"][t]
        net_debt = closing_debt - closing_cash
        years.append(
            {
                "revenue": revenue,
                "ebitda": ebitda,
                "interest": interest,
                "tax_wc": tax_wc,
                "capex": capex,
                "cfo": cfo,
                "fcf": fcf,
                "opening_debt": debt,
                "repayment": p["debt_repayment"][t],
                "closing_debt": closing_debt,
                "opening_cash": cash,
                "dividends": p["dividends"][t],
                "closing_cash": closing_cash,
                "undrawn": undrawn,
                "liquidity": closing_cash + undrawn,
                "total_leverage": closing_debt / ebitda,
                "net_debt": net_debt,
                "net_leverage": net_debt / ebitda,
                "coverage": ebitda / interest,
                "fcf_to_debt": fcf / closing_debt,
            }
        )
        debt, cash = closing_debt, closing_cash
    return years


def forecast_run(  # noqa: PLR0913 - one keyword per scenario setting
    tmp_path,
    provider,
    capsys,
    block,
    modules=("CP-2G",),
    cp1_block=None,
    pathway="distressed_restructuring",
):
    argv = launch(tmp_path, "--live", "--ruling", str(RULING), pathway=pathway)
    argv[argv.index("--out") + 1] = str(tmp_path / "runs" / RUN_ID)
    argv += ["--modules", *modules]
    routes = list(
        prepare(
            tmp_path / "context.json",
            tmp_path / "issuer",
            tmp_path / "preview",
            config="sol-medium",
            cap="50",
            modules=modules,
        ).plan.layout.routes
    )
    provider.answer = lambda context: forecast_answer(context, routes, block, cp1_block)
    code = main(argv)
    return code, tmp_path / "runs" / RUN_ID, capsys.readouterr()


def test_cp2g_run_publishes_model_delivery(tmp_path, provider, capsys):
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    receipt = json.loads((folder / "delivery.json").read_text())
    files = {"annual.md", "forecast.md", "forecast_exact.json", "calculation.json", "quarter.md"}
    assert receipt["cp_forecast_published"] is True and receipt["cp_model_published"] is False
    assert files <= set(receipt["files"])
    for name in files:  # hash-checked like the report
        assert receipt["files"][name] == hashlib.sha256((folder / name).read_bytes()).hexdigest()
    assert verify_delivery(next(out.glob("delivery-*.json")), folder) == folder / "delivery.json"
    exact = json.loads((folder / "forecast_exact.json").read_text())
    assert (
        exact["consumed"]["CP-1.md"]
        == hashlib.sha256((folder / "CP-1.md").read_bytes()).hexdigest()
    )
    assert (folder / "annual.md").read_bytes() == (folder / "CP-1.md").read_bytes()
    assert (folder / "forecast.md").read_bytes() == (folder / "CP-2G.md").read_bytes()
    calculation = json.loads((folder / "calculation.json").read_text())
    assert (
        calculation["forecast_exact_sha256"]
        == hashlib.sha256((folder / "forecast_exact.json").read_bytes()).hexdigest()
    )
    for case, shock in (("REFERENCE", None), ("DOWNSIDE", SHOCK)):
        published = exact["outputs"][case]["years"]
        for year, expected in zip(published, key_case(shock), strict=True):
            for name, want in expected.items():
                got = Fraction(year[name]["amount"])
                tolerance = abs(want) * Fraction(1, 10**30) if name in RATIOS else 0
                assert abs(got - want) <= tolerance, (case, year["year"], name)
    first = exact["outputs"]["REFERENCE"]["years"][0]  # hand-written year 1, base case
    for name, text in {
        "revenue": "1050",
        "ebitda": "315",
        "interest": "36",
        "tax_wc": "105",
        "capex": "42",
        "cfo": "174",
        "fcf": "132",
        "closing_debt": "550",
        "closing_cash": "162",
        "liquidity": "212",
    }.items():
        assert first[name]["amount"] == text, name
    down = exact["outputs"]["DOWNSIDE"]["years"][0]  # EBITDA x 0.8, interest x 1.1
    assert [down[n]["amount"] for n in ("ebitda", "interest", "fcf", "closing_cash")] == [
        "252",
        "39.6",
        "65.4",
        "95.4",
    ]
    assert (first["year"], first["planning_start"], first["planning_end"]) == (
        2025,
        "2025-04-01",
        "2026-03-31",
    )
    assert "Model not published" not in seen.err
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["cp_forecast_published"] is True and completed["forecast_failure"] is None


def layer1_block(**changes) -> str:
    """CP-1's block: each stated operand names the label and period header of the cell it read."""
    base = changes.pop("base", None) or {
        k: {"amount": v, "reason": None, "row": k, "period": "FY2025"} for k, v in BASE.items()
    }
    return forecast_block(downside_shock=None, base=base, **changes)


def _operand(amount, row="revenue", period="FY2025"):
    return {"amount": amount, "reason": None, "row": row, "period": period}


def _cp1_doc(revenue_table: str, key: str = "revenue", head: str = "", tail: str = "") -> str:
    """A CP-1 handoff: the other nine operands in a plain table, `key`'s in the given one."""
    rows = "\n".join(f"| {k} | {printed(k, v)} |" for k, v in BASE.items() if k != key)
    return (
        f"# CP-1\n\n## Findings\n\n### Bottom line\n\nText.\n\n### Base operands\n\n{head}"
        f"| Base | FY2025 |\n| --- | --- |\n{rows}\n\n{revenue_table}\n\n__BLOCK__\n"
        f"## Calculations\n\nNone.\n{tail}"
    )


def _parse_layer1(doc: str, key: str = "revenue", **operand):
    base = {k: _operand(v, k) for k, v in BASE.items()}
    base[key] = _operand(**{"row": key, **operand})
    full = doc.replace("__BLOCK__", layer1_block(base=base))
    return cpos_forecast.parse(full, full, "CP-1")


TWO_YEARS = "| Metric | FY2024 | FY2025 |\n| --- | --- | --- |\n| revenue | 900 | 1,000 |"


def test_a_layer1_operand_is_the_cell_at_its_row_and_period():
    inputs = _parse_layer1(_cp1_doc(TWO_YEARS), amount="1000", period="FY2025")
    assert inputs.base["revenue"].amount == "1000"
    assert _parse_layer1(_cp1_doc(TWO_YEARS), amount="900", period="FY2024")


@pytest.mark.parametrize(
    ("table", "operand", "complaint"),
    [
        (TWO_YEARS, {"amount": "900", "period": "FY2025"}, "is not CP-1's cell"),
        (TWO_YEARS, {"amount": "1000", "period": "FY2024"}, "is not CP-1's cell"),
        (TWO_YEARS, {"amount": "1000", "period": "FY2023"}, "no table cell"),
        (
            "| Metric | FY2025 | Growth % |\n| --- | --- | --- |\n| revenue | 1,000 | 12 |",
            {"amount": "12", "period": "FY2025"},
            "is not CP-1's cell",
        ),
        (
            "| Metric | FY2025 | Growth % |\n| --- | --- | --- |\n| revenue | 1,000 | 12% |",
            {"amount": "12", "period": "Growth %"},
            "is not one number",
        ),
        ("| Metric | FY2025 |\n| --- | --- |\n| revenue | (1,000) |", {"amount": "1000"}, "is not"),
        ("| Metric | FY2025 |\n| --- | --- |\n| revenue | 1,000k |", {"amount": "1000"}, "number"),
        ("| Metric | FY2025 |\n| --- | --- |\n| revenue | 1,000m |", {"amount": "1000"}, "number"),
        ("| Metric | FY2025 |\n| --- | --- |\n| revenue | n.a. |", {"amount": "1000"}, "number"),
        (
            "| Metric | FY2025 |\n| --- | --- |\n| revenue | 1,000 |",
            {"amount": "1000", "row": "Revenue"},
            "no table cell",
        ),
        (
            "| Metric | FY2025 |\n| --- | --- |\n| revenue | 1,000 |\n| revenue | 1,100 |",
            {"amount": "1000"},
            "is not one number",
        ),
    ],
    ids=[
        "prior-period-cell",
        "neighbour-period",
        "unknown-period",
        "growth-column",
        "percent-cell",
        "bracket-negative",
        "k-suffix",
        "m-suffix",
        "not-a-number",
        "label-case",
        "ambiguous-label",
    ],
)
def test_a_layer1_operand_that_is_not_its_named_cell_is_refused(table, operand, complaint):
    with pytest.raises(ValueError, match=complaint) as caught:
        _parse_layer1(_cp1_doc(table), **operand)
    assert "CP-1: base revenue" in str(caught.value)


_ROW = "| Metric | FY2025 |\n| --- | --- |\n| revenue | 1234 |"


@pytest.mark.parametrize(
    "doc",
    [
        _cp1_doc("", head=f"```text\n{_ROW}\n```\n\n"),
        _cp1_doc("", tail=f"\n## Sources\n\n{_ROW}\n"),
        _cp1_doc("").replace("Text.", f"Text.\n\n{_ROW}"),
        _cp1_doc("| Metric | FY2025 |\n| revenue | 1234 |"),
        _cp1_doc("", head="Basis: revenue 1,234 per annual report\n\n"),
    ],
    ids=["fenced", "sources", "reader-passage", "no-delimiter", "prose"],
)
def test_a_layer1_operand_outside_cp1s_tables_is_refused(doc):
    with pytest.raises(ValueError, match="no table cell"):
        _parse_layer1(doc, amount="1234")


def test_a_layer1_table_under_a_later_heading_still_counts_after_sources_ends():
    row = "| Metric | FY2025 |\n| --- | --- |\n| revenue | 1,234 |"
    doc = _cp1_doc("", tail=f"\n## Sources\n\nx\n\n## Appendix\n\n{row}\n")
    assert _parse_layer1(doc, amount="1234")


def _wc_doc(cell: str) -> str:
    return _cp1_doc(f"| Metric | FY2025 |\n| --- | --- |\n| Working capital | {cell} |", "wc")


@pytest.mark.parametrize(
    ("cell", "amount"), [("(45)", "45"), ("-45", "45"), ("45", "-45"), ("+45", "-45")]
)
def test_a_layer1_working_capital_is_the_cell_sign_reversed_as_cp2g_reads_it(cell, amount):
    assert _parse_layer1(_wc_doc(cell), "wc", amount=amount, row="Working capital")


@pytest.mark.parametrize(("cell", "amount"), [("45", "45"), ("+45", "45"), ("(45)", "-45")])
def test_a_layer1_working_capital_release_read_as_an_outflow_is_refused(cell, amount):
    with pytest.raises(ValueError, match="is not CP-1's cell"):
        _parse_layer1(_wc_doc(cell), "wc", amount=amount, row="Working capital")


def test_a_layer1_table_in_a_tilde_fence_is_code_and_not_a_cell():
    doc = _cp1_doc("~~~\n" + TWO_YEARS + "\n~~~")
    with pytest.raises(ValueError, match="no table cell"):
        _parse_layer1(doc, amount="1000", period="FY2025")


def test_a_layer1_escaped_pipe_stays_inside_its_cell():
    table = "| Metric | Note | FY2025 |\n| --- | --- | --- |\n| revenue | a \\| 900 | 1,000 |"
    assert _parse_layer1(_cp1_doc(table), amount="1000", period="FY2025")
    with pytest.raises(ValueError, match="is not CP-1's cell"):
        _parse_layer1(_cp1_doc(table), amount="900", period="FY2025")


@pytest.mark.parametrize("printed", ["85", "-85", "(85)", "\u221285", "**(85)**"])
def test_a_layer1_outflow_is_stated_as_a_magnitude_however_cp1_prints_it(printed):
    doc = _cp1_doc(f"| Metric | FY2025 |\n| --- | --- |\n| Interest paid | {printed} |", "interest")
    assert _parse_layer1(doc, "interest", amount="85", row="Interest paid").base["interest"]


def test_a_layer1_outflow_stated_negative_is_refused():
    doc = _cp1_doc("| Metric | FY2025 |\n| --- | --- |\n| Interest paid | -85 |", "interest")
    with pytest.raises(ValueError, match="is not CP-1's cell"):
        _parse_layer1(doc, "interest", amount="-85", row="Interest paid")


@pytest.mark.parametrize(
    ("printed", "amount", "accepted"),
    [("(50)", "50", False), ("(50)", "-50", True), ("50", "-50", False), ("\u221250", "-50", True)],
)
def test_a_layer1_non_outflow_compares_with_its_sign(printed, amount, accepted):
    doc = _cp1_doc(f"| Metric | FY2025 |\n| --- | --- |\n| Free cash flow | {printed} |", "fcf")
    if accepted:
        assert _parse_layer1(doc, "fcf", amount=amount, row="Free cash flow")
    else:
        with pytest.raises(ValueError, match="is not CP-1's cell"):
            _parse_layer1(doc, "fcf", amount=amount, row="Free cash flow")


def test_a_layer1_label_is_compared_without_emphasis_and_a_repeated_row_that_agrees_is_one_cell():
    table = "| Metric | FY2025 |\n| --- | --- |\n|  **Net sales**  | 1,000 |\n| Net sales | 1000 |"
    assert _parse_layer1(_cp1_doc(table), amount="1000", row="Net sales")


@pytest.mark.parametrize(
    "operand",
    [
        {"amount": "1000", "reason": None},
        {"amount": "1000", "reason": None, "row": "revenue"},
        {"amount": None, "reason": "unknown", "row": "revenue", "period": "FY2025"},
    ],
)
def test_a_layer1_operand_must_name_its_cell_exactly_when_it_states_an_amount(operand):
    doc = _cp1_doc("| Metric | FY2025 |\n| --- | --- |\n| revenue | 1,000 |")
    base = {k: _operand(v, k) for k, v in BASE.items()} | {"revenue": operand}
    full = doc.replace("__BLOCK__", layer1_block(base=base))
    with pytest.raises(ValueError, match="CP-1: base revenue"):
        cpos_forecast.parse(full, full, "CP-1")


def _named_cp2g(doc: str, **operands):
    """A CP-2G block that names each operand's cell, parsed against the CP-1 document."""
    base = {k: _operand(v, k) for k, v in BASE.items()} | operands
    return cpos_forecast.parse(forecast_block(base=base), doc.replace("__BLOCK__", ""))


def test_a_cp2g_block_may_name_the_row_and_period_of_every_base_operand():
    inputs = _named_cp2g(_cp1_doc(TWO_YEARS))
    assert (inputs.base["revenue"].row, inputs.base["revenue"].period) == ("revenue", "FY2025")
    assert inputs.downside_shock is not None  # still CP-2G's block: the shock and cases stay


MUST_NAME = (
    "CP-2G: base revenue must name the `row` label and either the `period` header or the "
    "`column` header it was read from"
)


@pytest.mark.parametrize(
    ("operand", "complaint"),
    [
        (
            _operand("900"),
            "CP-2G: base revenue 900 is not CP-1's cell at row `revenue`, period `FY2025` (1,000)",
        ),
        (
            _operand("1000", "Revenue"),
            "CP-2G: base revenue: no table cell of CP-1 is at row `Revenue`, period `FY2025`",
        ),
        (
            _operand("1000", period="FY2023"),
            "CP-2G: base revenue: no table cell of CP-1 is at row `revenue`, period `FY2023`",
        ),
        ({"amount": "1000", "reason": None}, MUST_NAME),
        ({"amount": "1000", "reason": None, "row": "revenue"}, MUST_NAME),
        (
            {"amount": None, "reason": "unknown", "row": "revenue", "period": "FY2025"},
            "CP-2G: base revenue states no amount, so it names no row, period or column",
        ),
    ],
)
def test_a_named_cp2g_operand_that_is_not_its_cell_is_refused(operand, complaint):
    with pytest.raises(ValueError) as caught:
        _named_cp2g(_cp1_doc(TWO_YEARS), revenue=operand)
    assert str(caught.value) == complaint


def test_a_cp2g_block_naming_some_operands_is_refused_at_the_first_one_missing():
    unnamed = {key: {"amount": BASE[key], "reason": None} for key in ("taxes", "capex")}
    with pytest.raises(ValueError) as caught:
        _named_cp2g(_cp1_doc(TWO_YEARS), **unnamed)
    assert (
        str(caught.value)
        == "CP-2G: base taxes must name the `row` label and either the `period` header or the "
        "`column` header it was read from"
    )


def test_a_named_cp2g_amount_printed_only_in_prose_is_refused():
    doc = _cp1_doc("", head="Basis: revenue 1,234 per annual report\n\n").replace("__BLOCK__", "")
    unnamed = {k: {"amount": v, "reason": None} for k, v in BASE.items()}
    unnamed["revenue"] = {"amount": "1234", "reason": None}
    assert cpos_forecast.parse(forecast_block(base=unnamed), doc)  # printed somewhere: as before
    with pytest.raises(ValueError, match="CP-2G: base revenue: no table cell of CP-1"):
        _named_cp2g(doc, revenue=_operand("1234"))


def test_a_named_cp2g_operand_that_is_not_its_cell_is_sent_back_for_repair():
    cp1 = "| Base | FY2025 |\n| --- | --- |\n" + "\n".join(
        f"| {k} | {printed(k, v)} |" for k, v in BASE.items()
    )
    task = types.SimpleNamespace(module_id="CP-2G", handoffs={"CP-1": cp1.encode()})
    base = {k: _operand(v, k) for k, v in BASE.items()}
    assert cpos_launch._forecast_issues(task, forecast_block(base=base)) == ()
    base["capex"] = _operand("40", "Capex")
    (issue,) = cpos_launch._forecast_issues(task, forecast_block(base=base))
    assert issue == (
        "Forecast inputs: CP-2G: base capex: no table cell of CP-1 is at row `Capex`, period "
        "`FY2025`. Correct the row, period, column or amount of capex; if you cannot, state "
        "capex as missing: amount null, no row, period or column, and the reason."
    )


def test_a_refusal_that_is_not_about_a_base_operand_keeps_the_null_every_driver_line():
    cp1 = "| Base | FY2025 |\n| --- | --- |\n" + "\n".join(
        f"| {k} | {printed(k, v)} |" for k, v in BASE.items()
    )
    task = types.SimpleNamespace(module_id="CP-2G", handoffs={"CP-1": cp1.encode()})
    base = {k: _operand(v, k) for k, v in BASE.items()}
    (issue,) = cpos_launch._forecast_issues(task, forecast_block(base=base, years=[1]))
    assert issue.startswith("Forecast inputs: CP-2G: ") and "base " not in issue.split(". ")[0]
    assert issue.endswith(
        ". Correct the block; if you cannot, set every driver's values to "
        "[null, null, null] and say why in scope_limits."
    )


def test_a_cp2g_block_that_names_its_rows_publishes_their_history(tmp_path, provider, capsys):
    base = {k: _operand(v, k) for k, v in BASE.items()}
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block(base=base))
    assert code == 0, seen.err
    assert "Model not published" not in seen.err
    (folder,) = (out / "deliveries").iterdir()
    record = json.loads((folder / "calculation.json").read_text())["history"]
    column = next(c for c in record["columns"] if c["id"] == "FY2025")
    assert column["values"]["revenue"] == {"amount": "1000", "reason": None}
    assert column["values"]["tax_wc"] == {"amount": "30", "reason": None}  # 20 + 10


def test_the_layer1_instruction_asks_for_the_row_and_period_not_for_extra_rows():
    block = cpos_launch.LAYER1_FORECAST_BLOCK
    assert '"row"' in block and '"period"' in block and "exact first-cell text" in block
    assert "Base operands" not in block and "positive magnitude" in block


def test_cp_model_without_cp2g_publishes_a_model_from_cp1s_block(tmp_path, provider, capsys):
    modules = ("CP-1", "CP-MODEL")
    code, out, seen = forecast_run(
        tmp_path,
        provider,
        capsys,
        None,
        modules=modules,
        cp1_block=layer1_block(),
        pathway="covenant_refinancing",
    )
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    cp1 = hashlib.sha256((folder / "CP-1.md").read_bytes()).hexdigest()
    assert (folder / "forecast.md").read_bytes() == (folder / "CP-1.md").read_bytes()
    exact = json.loads((folder / "forecast_exact.json").read_text())
    assert exact["consumed"] == {"CP-1.md": cp1}  # no CP-2G handoff was consumed
    assert list(exact["outputs"]) == ["REFERENCE"]  # no case and no shock
    assert "run-rate inputs the CP-1 handoff stated" in exact["scope_limits"][0]
    first = exact["outputs"]["REFERENCE"]["years"][0]  # the hand-written year 1 of the base case
    assert [first[n]["amount"] for n in ("revenue", "ebitda", "fcf", "closing_debt")] == [
        "1050",
        "315",
        "132",
        "550",
    ]
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["cp_forecast_published"] is True and completed["forecast_failure"] is None


def test_cp2gs_block_wins_when_both_modules_state_one(tmp_path, provider, capsys):
    cp1_paths = {**PATHS, "revenue_growth": ("0.50", "0.50", "0.50")}  # would give 1500 in year 1
    cp1_block = layer1_block(
        base_drivers={
            n: {
                "values": list(v),
                "category": "Analyst Interpretation",
                "rationale": "x",
                "limitation": None,
            }
            for n, v in cp1_paths.items()
        }
    )
    code, out, seen = forecast_run(
        tmp_path,
        provider,
        capsys,
        forecast_block(),
        modules=("CP-2G", "CP-MODEL"),
        cp1_block=cp1_block,
    )
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    assert (folder / "forecast.md").read_bytes() == (folder / "CP-2G.md").read_bytes()
    exact = json.loads((folder / "forecast_exact.json").read_text())
    assert set(exact["consumed"]) == {"CP-1.md", "CP-2G.md"}
    assert exact["outputs"]["REFERENCE"]["years"][0]["revenue"]["amount"] == "1050"
    assert "DOWNSIDE" in exact["outputs"]
    assert "run-rate" not in exact["scope_limits"][0]


@pytest.mark.parametrize(
    ("cp1_block", "reason"),
    [
        (layer1_block(years=[]), "CP-1: forecast inputs: years"),
        (None, "CP-1: needs exactly one `### Forecast inputs (machine-readable)` heading"),
        (forecast_block(), "CP-1: a layer-1 forecast states no shock and no cases"),
        (
            layer1_block(
                base={k: _operand("1234" if k == "revenue" else v, k) for k, v in BASE.items()}
            ),
            "CP-1: base revenue 1234 is not CP-1's cell at row `revenue`, period `FY2025`",
        ),
    ],
)
def test_a_bad_layer1_block_withholds_the_model_and_never_rejects_cp1(
    tmp_path, provider, capsys, cp1_block, reason
):
    code, out, seen = forecast_run(
        tmp_path,
        provider,
        capsys,
        None,
        modules=("CP-1", "CP-MODEL"),
        cp1_block=cp1_block,
        pathway="covenant_refinancing",
    )
    assert code == 0, seen.err  # CP-1 was accepted; the run delivered
    (folder,) = (out / "deliveries").iterdir()
    assert (folder / "delivery.json").is_file() and not (folder / "forecast_exact.json").exists()
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["cp_forecast_published"] is False
    assert reason in completed["forecast_failure"]
    assert f"Model not published: {completed['forecast_failure']}" in seen.err


def test_cp1_gets_the_layer_1_block_only_when_the_forecast_lacks_cp2g(tmp_path):
    def instructions(name, pathway, modules=None):
        folder = tmp_path / name
        folder.mkdir()
        prepared = prepare(
            context_file(folder, pathway),
            issuer_folder(folder),
            folder / "out",
            config="sol-medium",
            cap="50",
            modules=modules,
        )
        return prepared, (folder / "out/instructions/CP-1.md").read_text()

    marker = "### Forecast inputs (machine-readable)"
    for name, pathway, modules in (
        ("preset", "earnings_update", None),  # CP-MODEL in the preset, no CP-2G
        ("explicit", "covenant_refinancing", ("CP-1", "CP-MODEL")),
    ):
        prepared, text = instructions(name, pathway, modules)
        before, _, method = text.partition(cpos_launch.METHOD_MARK)
        assert marker in before and marker not in method, name
        assert prepared.plan.publish_forecast is True, name
        assert "CP-MODEL" not in prepared.ordered, name
    prepared, text = instructions("with-2g", "distressed_restructuring")  # CP-2G in the run
    assert marker not in text and prepared.plan.publish_forecast is True
    assert marker in (tmp_path / "with-2g/out/instructions/CP-2G.md").read_text()
    prepared, text = instructions("bare", "earnings_update", ("CP-1",))  # no CP-MODEL, no CP-2G
    assert marker not in text and prepared.plan.publish_forecast is False


def test_no_cp2g_publishes_no_model(tmp_path, provider, capsys):
    code, out, seen = forecast_run(tmp_path, provider, capsys, None, modules=("CP-2A",))
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    assert not {"forecast_exact.json", "calculation.json", "annual.md"} & {
        p.name for p in folder.iterdir()
    }
    receipt = json.loads((folder / "delivery.json").read_text())
    assert "cp_forecast_published" not in receipt
    assert "publish_forecast" not in json.loads((out / "workflow.json").read_text())
    assert (
        json.loads(next(out.glob("completed-*.json")).read_text())["cp_forecast_published"] is False
    )
    assert "Model not published" not in seen.err


def test_model_publish_failure_keeps_the_delivery(tmp_path, provider, capsys, monkeypatch):
    def refuse(cp1, handoff, source="CP-2G", *, history=False):
        raise ValueError("synthetic failure")

    monkeypatch.setattr(cpos_forecast, "model_files", refuse)
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0
    (folder,) = (out / "deliveries").iterdir()
    assert (folder / "delivery.json").is_file() and not (folder / "forecast_exact.json").exists()
    assert "Model not published: synthetic failure" in seen.err
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["cp_forecast_published"] is False
    assert completed["forecast_failure"] == "synthetic failure"
    assert f"Delivery: {folder / 'delivery.json'}" in seen.out


@pytest.mark.parametrize(
    ("block", "reason"),
    [
        (None, "needs exactly one `### Forecast inputs (machine-readable)` heading"),
        (
            "### Forecast inputs (machine-readable)\n\nnone\n",
            "`### Forecast inputs (machine-readable)` needs exactly one fenced json block",
        ),
        (
            forecast_block().replace('"1000"', '"1001"', 1),
            "base revenue 1001 is not printed in CP-1",
        ),
        (forecast_block(years=[]), "forecast inputs: years"),
        (
            forecast_block(
                years=[
                    {"year": 2025 + i, "start": "2025-04-01", "end": "2028-03-31"} for i in range(3)
                ]
            ),
            (
                "forecast inputs: (root): Value error, each year must start the day after "
                "the previous one ends"
            ),
        ),
    ],
)
def test_an_invalid_or_missing_inputs_block_is_sent_back_for_repair_naming_why(
    tmp_path, block, reason
):
    """Live run tdg-forecast-004 (2026-11-10): a block delivery cannot parse used to be dropped
    after payment. The in-loop check now asks for a repair, or a declined block."""
    issues = cp2g_check(tmp_path, block)
    assert any(f"Forecast inputs: CP-2G: {reason}" in i for i in issues), issues
    ending = (
        "as missing: amount null, no row, period or column, and the reason."
        if "base " in reason
        else ("[null, null, null] and say why in scope_limits.")
    )
    assert all(i.endswith(ending) for i in issues if i.startswith("Forecast inputs")), issues


def test_without_a_shock_only_the_reference_case_is_published(tmp_path, provider, capsys):
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block(downside_shock=None))
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    assert list(json.loads((folder / "forecast_exact.json").read_text())["outputs"]) == [
        "REFERENCE"
    ]


def test_a_new_forecast_run_publishes_the_history_record(tmp_path, provider, capsys):
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    assert "history" in json.loads((folder / "calculation.json").read_text())
    (request,) = out.glob("delivery-*.json")
    assert json.loads(request.read_text())["history"] is True


def test_the_forecast_request_does_not_change_the_identity_of_other_plans(
    tmp_path, provider, capsys
):
    """Existing plans keep their identity.json: the flag is not part of it, and a plan without
    CP-2G does not even carry it."""
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0, seen.err
    identity = json.loads((out / "identity.json").read_text())
    assert "publish_forecast" not in identity and "forecast" not in identity


def test_the_forecast_instructions_come_before_the_method_block_and_leave_it_unchanged(tmp_path):
    prepared = prepare(
        tmp_path / "context.json"
        if (tmp_path / "context.json").exists()
        else context_file(tmp_path, "distressed_restructuring"),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
        modules=("CP-2G",),
    )
    text = (tmp_path / "out/instructions/CP-2G.md").read_text()
    before, _, method = text.partition(cpos_launch.METHOD_MARK)
    assert "### Forecast inputs (machine-readable)" in before
    assert method == cpos_launch.method_text("CP-2G") + "\n"
    other = (tmp_path / "out/instructions/CP-1.md").read_text()
    assert "Forecast inputs" not in other
    assert prepared.plan.publish_forecast is True


UPSIDE = {"revenue_growth": ("0.10", "0.10", "0.10"), "ebitda_margin": ("0.35", "0.35", "0.35")}
DOWNSIDE = {"revenue_growth": ("0", "0", "0"), "dividends": ("0", "0", "0")}


def case_drivers(paths: dict) -> dict:
    return {
        name: {
            "values": list(values),
            "category": "Analyst Interpretation",
            "rationale": "Synthetic case.",
            "limitation": None,
        }
        for name, values in paths.items()
    }


def cased_block(**changes) -> str:
    return forecast_block(
        upside_drivers=case_drivers(UPSIDE), downside_drivers=case_drivers(DOWNSIDE), **changes
    )


def test_cp2g_upside_and_downside_drivers_are_computed_as_their_own_cases(
    tmp_path, provider, capsys
):
    """Owner, 2026-11-10 ("Yes, compute them"): CP-2G's own upside and downside cases are
    computed from the drivers it changes, the rest inherited from base; CP-2A's shock stays a
    separate case on base drivers, never compounded with them."""
    code, out, seen = forecast_run(tmp_path, provider, capsys, cased_block())
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    exact = json.loads((folder / "forecast_exact.json").read_text())
    assert sorted(exact["outputs"]) == ["DOWNSIDE", "DOWNSIDE_DRIVERS", "REFERENCE", "UPSIDE"]
    for case, shock, paths in (
        ("REFERENCE", None, PATHS),
        ("UPSIDE", None, {**PATHS, **UPSIDE}),
        ("DOWNSIDE_DRIVERS", None, {**PATHS, **DOWNSIDE}),
        ("DOWNSIDE", SHOCK, PATHS),
    ):
        for year, expected in zip(
            exact["outputs"][case]["years"], key_case(shock, paths), strict=True
        ):
            for name, want in expected.items():
                got = Fraction(year[name]["amount"])
                tolerance = abs(want) * Fraction(1, 10**30) if name in RATIOS else 0
                assert abs(got - want) <= tolerance, (case, year["year"], name)
    names = ("revenue", "ebitda", "interest", "tax_wc", "capex", "cfo", "fcf", "closing_cash")
    up = exact["outputs"]["UPSIDE"]["years"][0]  # hand-written: growth 0.10, margin 0.35
    assert [up[n]["amount"] for n in names] == [
        "1100",
        "385",
        "36",
        "110",
        "44",
        "239",
        "195",
        "225",
    ]
    down = exact["outputs"]["DOWNSIDE_DRIVERS"]["years"][0]  # hand-written: no growth, no dividends
    assert [down[n]["amount"] for n in names] == [
        "1000",
        "300",
        "36",
        "100",
        "40",
        "164",
        "124",
        "174",
    ]
    assert exact["upside_drivers"]["revenue_growth"]["values"] == ["0.10", "0.10", "0.10"]
    assert exact["downside_drivers"]["dividends"]["values"] == ["0", "0", "0"]


def test_without_case_drivers_the_forecast_record_is_unchanged(tmp_path, provider, capsys):
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    exact = json.loads((folder / "forecast_exact.json").read_text())
    assert sorted(exact["outputs"]) == ["DOWNSIDE", "REFERENCE"]
    assert "upside_drivers" not in exact and "downside_drivers" not in exact


@pytest.mark.parametrize(
    ("changes", "complaint"),
    [
        ({"upside_drivers": {}}, "upside_drivers"),
        ({"downside_drivers": {"ebitda_margin": None}}, "downside_drivers"),
        (
            {"upside_drivers": case_drivers({"ebitda_margin": ("0.48022670", "0.4", "0.4")})},
            "upside_drivers.ebitda_margin",
        ),
        (
            {"upside_drivers": case_drivers({"leverage": ("1", "1", "1")})},
            "upside_drivers.leverage",
        ),
        (
            {"downside_drivers": case_drivers({"dividends": (None, None, None)})},
            "downside_drivers.dividends",
        ),
    ],
)
def test_a_case_override_must_name_a_driver_with_valid_values(changes, complaint):
    with pytest.raises(ValueError) as caught:
        cpos_forecast.parse(forecast_block(**changes), " ".join(BASE.values()))
    assert complaint in str(caught.value)


def test_the_cp2g_instruction_asks_for_the_row_and_period_of_every_base_operand():
    block = cpos_launch.FORECAST_BLOCK
    for words in (
        '"row": "<label>", "period": "<header>"',
        "exact first-cell text",
        "exact header text",
        "of one of the CP-1 handoff's tables",
        "Name the cell of every operand that has an amount by `row` and `period` and nothing else.",
        "positive magnitude",
        "with its sign reversed",
        "is not a cell",
        "`FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`",
    ):
        assert words in block, words
    assert "copied exactly as CP-1 prints it (outflows as positive magnitudes)" not in block


def test_the_forecast_instructions_ask_for_the_cases_as_driver_overrides():
    block = cpos_launch.FORECAST_BLOCK
    assert "`upside_drivers`" in block and "`downside_drivers`" in block
    assert "only the drivers that differ from base" in block


def test_the_library_lists_the_published_forecast_as_a_model(tmp_path, provider, capsys):
    """The launcher's own refresh builds the library: its real methodology check accepts the
    CP-2G instructions and the Forecast data carries the published figures."""
    code, _, seen = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0 and "Library not updated" not in seen.err
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    (model,) = (m for m in data["workspace"]["models"] if m["cashflow"] is not None)
    grid = model["cashflow"]
    assert [c["label"] for c in grid["columns"]][-6:] == ["FY2025E", "FY2026E", "FY2027E"] * 2
    assert [c["group"] for c in grid["columns"]][-6::3] == ["Base case", "Downside case"]


def test_the_library_shows_every_computed_case_in_order(tmp_path, provider, capsys):
    code, _, seen = forecast_run(tmp_path, provider, capsys, cased_block())
    assert code == 0 and "Library not updated" not in seen.err
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    (model,) = (m for m in data["workspace"]["models"] if m["cashflow"] is not None)
    grid = model["cashflow"]
    assert [c["group"] for c in grid["columns"]][-6::3] == ["Base case", "Downside case"]
    assert [c["group"] for c in grid["other"]["columns"]][::3] == [
        "Upside",
        "Downside (CP-2G drivers)",
    ]
    revenue = next(r for r in grid["rows"] if r["label"] == "Revenue")
    other = next(r for r in grid["other"]["rows"] if r["label"] == "Revenue")
    assert [c["exact"] for c in other["cells"][:3]] == ["1100", "1210", "1331"]
    assert [c["exact"] for c in other["cells"][3:6]] == ["1000", "1000", "1000"]
    assert [c["exact"] for c in revenue["cells"][-6:-3]] == ["1050", "1092", "1124.76"]
    assert grid["limits"][0].startswith("Every figure is Python's arithmetic")


def test_a_run_without_cp2g_lists_no_model(tmp_path, provider, capsys):
    code, _, seen = forecast_run(tmp_path, provider, capsys, None, modules=("CP-2A",))
    assert code == 0 and "Library not updated" not in seen.err
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    assert data["workspace"]["models"] == []


def test_delivery_fails_closed_when_the_pinned_handoff_no_longer_yields_the_forecast(
    tmp_path, provider, capsys
):
    """The publish step fails open; a delivery that asks for the forecast never does."""
    code, out, _ = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0
    manifest = next(out.glob("delivery-*.json"))
    request = DeliveryRequest.model_validate_json(manifest.read_text())
    assert request.forecast is True
    handoff = out / request.handoffs["CP-2G"].path
    handoff.write_text(handoff.read_text().replace('"1000"', '"1001"'))
    with pytest.raises(ValueError, match="Changed handoff: CP-2G"):
        markdown_files(request, out)
    for module in ("CP-1", "CP-2G"):  # the exact files are built from both handoffs, bytes equal
        assert module in request.handoffs


@pytest.mark.browser
def test_the_forecast_tab_shows_the_model_only_for_the_run_that_published_one(
    tmp_path, provider, capsys
):
    """Headless Chrome over file://: Forecast shows the Python-computed model, and a run without
    CP-2G shows the not-published notice."""
    from test_library_page_browser import visit

    code, _, seen = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0 and "Library not updated" not in seen.err
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    (model,) = data["workspace"]["models"]
    dom, console = visit(tmp_path / "library/index.html", f"#W-Forecast/{model['id']}?c={RUN_ID}")
    assert console == []
    assert "FY2025E" in dom and "1,050" in dom and "Downside" in dom
    assert "No forecast model was published" not in dom
    other = tmp_path / "other"
    other.mkdir()
    code, _, seen = forecast_run(other, provider, capsys, None, modules=("CP-2A",))
    assert code == 0 and "Library not updated" not in seen.err
    dom, console = visit(other / "library/index.html", f"#W-Forecast/none?c={RUN_ID}")
    assert console == []
    assert "No forecast model was published from this run’s files" in dom


UNFILLED = re.compile(r"\b(undefined|NaN|null|\[object Object\])\b")


@pytest.mark.browser
def test_a_short_snapshot_run_in_the_library_is_listed_with_its_label_and_cp_l10_leads_the_overview(
    tmp_path, provider, capsys
):
    """Owner, 2026-11-11: CP-2 and CP-6 do not run in a short snapshot, so CP-L10 leads (H5)."""
    from test_library_page_browser import visit

    launch(tmp_path, pathway="short_snapshot")  # writes the context and the issuer folder
    prepared = prepare(
        tmp_path / "context.json",
        tmp_path / "issuer",
        tmp_path / "runs" / RUN_ID,
        config="sol-medium",
        cap="50",
    )
    routes = list(prepared.plan.layout.routes)
    provider.answer = lambda context: short_snapshot_answer(context, routes)
    run_live_handoffs(
        prepared.manifest,
        prepared.directory,
        ruling=RULING,
        check=checker(prepared.layout),
        config="sol-medium",
    )
    cpos_launch._refresh_library(prepared.directory)
    assert "Library not updated" not in capsys.readouterr().err
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    assert data["workspace"]["runs"][RUN_ID]["pathway"] == "short_snapshot"
    index = tmp_path / "library/index.html"
    dom, console = visit(index, f"#W-Overview?c={RUN_ID}")
    assert console == []
    shown = re.sub(r"(?s)<(script|style)\b.*?</\1>|<[^>]+>|\s+", " ", dom)
    assert "Short credit snapshot" in shown  # the run label names the pathway as words
    lead = re.search(
        r'(?s)<section class="overview-part" id="overview-lead"[^>]*>.*?</section>', dom
    )
    assert lead is not None
    lead_text = re.sub(r"\s+([,.;:])", r"\1", " ".join(re.sub(r"<[^>]+>", " ", lead[0]).split()))
    assert "Creditors are covered today but only just" in lead_text
    # The key finding is the why grid's, beside the lead rather than inside it.
    why = re.search(r'(?s)<section class="overview-part g24" id="overview-why".*?</section>', dom)
    assert why is not None
    why_text = re.sub(r"\s+([,.;:])", r"\1", " ".join(re.sub(r"<[^>]+>", " ", why[0]).split()))
    assert "Cover is thin at 3.1x" in why_text
    # The Overview no longer names the module that wrote the lead (ruling: no "Written by"); CP-L10
    # leads when its tile (named "Short credit snapshot", opening CP-L10) holds the sentence the
    # lead draws, and no other module's tile does.
    tiles = re.findall(r'(?s)<details class="mt".*?</details>', dom)
    leading = [t for t in tiles if "Creditors are covered today but only just" in t]
    assert len(leading) == 1 and 'class="mt-name">Short credit snapshot<' in leading[0]
    assert 'href="#CP-L10/' in leading[0]
    assert UNFILLED.search(shown) is None, UNFILLED.findall(shown)


@pytest.mark.browser
@pytest.mark.parametrize("pathway", sorted(PATHWAY_MODULES))
def test_each_pathways_run_reaches_the_library_screens(tmp_path, provider, capsys, pathway):
    """Sweep 2026-11-10 (wiring): one run per pathway, launched into runs/, is listed by the real
    library, and its screens and report render with no console message or unfilled value."""
    from test_library_page_browser import visit

    argv = launch(tmp_path, "--live", "--ruling", str(RULING), pathway=pathway)
    argv[argv.index("--out") + 1] = str(tmp_path / "runs" / RUN_ID)
    routes = list(
        prepare(
            tmp_path / "context.json",
            tmp_path / "issuer",
            tmp_path / "preview",
            config="sol-medium",
            cap="50",
        ).plan.layout.routes
    )
    forecast = "CP-2G" in PATHWAY_MODULES[pathway]
    provider.answer = lambda context: (
        forecast_answer(context, routes, forecast_block()) if forecast else answer(context, routes)
    )
    assert main(argv) == 0
    assert "Library not updated" not in capsys.readouterr().err
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    assert list(data["workspace"]["runs"]) == [RUN_ID]
    models = data["workspace"]["models"]
    assert len(models) == forecast
    (delivery,) = (tmp_path / "runs" / RUN_ID / "deliveries").iterdir()
    pages = [
        (tmp_path / "library/index.html", f"#W-{route}?c={RUN_ID}")
        for route in (
            "Overview",
            "Reports/list",
            f"Reports/{delivery.name}",
            "Evidence/sources",
            f"Forecast/{models[0]['id'] if models else 'none'}",
        )
    ]
    for page, route in pages:
        dom, console = visit(page, route)
        shown = re.sub(r"(?s)<(script|style)\b.*?</\1>|<[^>]+>|\s+", " ", dom)
        assert console == [], (route, console)
        assert UNFILLED.search(shown) is None, (route, UNFILLED.findall(shown))
        assert ISSUER in shown, route


@pytest.mark.browser
def test_a_lite_run_fills_the_library_pages_and_its_forecast_page_states_the_gap(
    tmp_path, provider, capsys
):
    """A synthetic lite run (no CP-MODEL, so no forecast) launched into runs/ and read in the real
    library: it is labelled "Lite credit assessment", CP-2 writes the Overview lead, the Forecast
    page says that no forecast was published, and no page shows an unfilled value."""
    from test_library_page_browser import visit

    argv = launch(tmp_path, "--live", "--ruling", str(RULING), pathway="lite_credit_assessment")
    argv[argv.index("--out") + 1] = str(tmp_path / "runs" / RUN_ID)
    routes = list(
        prepare(
            tmp_path / "context.json",
            tmp_path / "issuer",
            tmp_path / "preview",
            config="sol-medium",
            cap="50",
        ).plan.layout.routes
    )
    provider.answer = lambda context: answer(context, routes)
    assert main(argv) == 0
    seen = capsys.readouterr()
    assert "Library not updated" not in seen.err and "Model not published" not in seen.err
    assert tuple(c[0] for c in provider.calls) == LITE_MODULES
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    assert data["workspace"]["runs"][RUN_ID]["pathway"] == "lite_credit_assessment"
    assert data["workspace"]["models"] == []
    index = tmp_path / "library/index.html"
    shown = {}
    for name, route in {
        "Overview": f"#W-Overview/overview?c={RUN_ID}",
        "Changes": f"#W-Changes/changes?c={RUN_ID}",
        "Modules": f"#CP-2A?c={RUN_ID}",
        "Forecast": f"#W-Forecast/none?c={RUN_ID}",
        "Evidence": f"#W-Evidence/sources?c={RUN_ID}",
    }.items():
        dom, console = visit(index, route)
        shown[name] = " ".join(re.sub(r"(?s)<(script|style)\b.*?</\1>|<[^>]+>", " ", dom).split())
        assert console == [], (name, console)
        assert UNFILLED.search(shown[name]) is None, (name, UNFILLED.findall(shown[name]))
        assert ISSUER in shown[name] and "Lite credit assessment" in shown[name], name
    dom, _ = visit(index, f"#W-Overview/overview?c={RUN_ID}")
    # The lead is written by CP-2; the Overview no longer links its writer, so the trace
    # controls of the lead's key findings (the handoff file each was read from) are the evidence.
    lead = re.search(
        r'(?s)<section class="overview-part" id="overview-lead"[^>]*>.*?</section>', dom
    )
    why = re.search(
        r'(?s)<section class="overview-part[^"]*" id="overview-why"[^>]*>.*?</section>', dom
    )
    assert lead is not None and why is not None
    sources = re.findall(r'data-paragraph="([^"]*)"', why[0])
    assert sources and all("/CP-2.md:" in source for source in sources), sources
    assert "First run of this pathway" in shown["Changes"]
    assert "No forecast model was published from this run\u2019s files" in shown["Forecast"]


def test_a_delivery_without_a_forecast_has_no_forecast_key_in_its_receipt(
    tmp_path, provider, capsys
):
    """Existing deliveries reproduce byte for byte: the key is written only when true."""
    code, out, _ = forecast_run(tmp_path, provider, capsys, None, modules=("CP-2A",))
    assert code == 0
    (folder,) = (out / "deliveries").iterdir()
    assert "cp_forecast_published" not in json.loads((folder / "delivery.json").read_text())
    assert "forecast" not in json.loads(next(out.glob("delivery-*.json")).read_text())


# Copied verbatim from the 2026-11-09 sol-medium run (runs/cpos-tdg-sol-medium-all-001, delivery
# abd687ca...c2baa, CP-2G.md): the model declined to forecast, so every driver is all null.
REAL_DECLINED_BLOCK = (
    Path(__file__).parent / "fixtures/sol_medium_run_2026_11_09/CP-2G-forecast-block.md"
).read_text(encoding="utf-8")


def test_a_handoff_that_declines_to_forecast_gets_one_plain_sentence():
    with pytest.raises(ValueError) as caught:
        cpos_forecast.parse(REAL_DECLINED_BLOCK, "CP-1 prints 7,940")
    assert str(caught.value) == (
        "CP-2G: the handoff gives no forecast drivers, so no forecast was computed "
        "(Blocked interface only: CP-2A is explicitly blocked and supplies no scenario; "
        "no forecast figures are submitted.)"
    )


def test_other_contract_failures_report_a_count_and_at_most_three_issues():
    bad = json.loads(forecast_block().split("```json\n")[1].split("\n```")[0])
    for driver in bad["base_drivers"].values():
        driver["category"] = "analyst_judgment"
    block = forecast_block(base_drivers=bad["base_drivers"])
    with pytest.raises(ValueError) as caught:
        cpos_forecast.parse(block, "CP-1 prints 1000 300 36 20 10 40 194 600 100 50")
    message = str(caught.value)
    assert message.startswith("CP-2G: forecast inputs: 7 problems; first: ")
    assert message.count("category") == 3


def test_a_few_problems_are_listed_whole_without_a_count():
    drivers = json.loads(forecast_block().split("```json\n")[1].split("\n```")[0])["base_drivers"]
    drivers["dividends"]["category"] = "analyst_judgment"
    with pytest.raises(ValueError) as caught:
        cpos_forecast.parse(
            forecast_block(base_drivers=drivers), "1000 300 36 20 10 40 194 600 100 50"
        )
    assert str(caught.value).startswith("CP-2G: forecast inputs: base_drivers.dividends.category: ")
    assert "problems" not in str(caught.value)


def test_the_forecast_instructions_name_every_allowed_category_and_the_value_format():
    from typing import get_args

    from deploy_vii.business_context import Category

    allowed = get_args(Category)
    assert len(allowed) == 4
    for value in allowed:
        assert f"`{value}`" in cpos_launch.FORECAST_BLOCK
    assert "three decimal strings" in cpos_launch.FORECAST_BLOCK
    assert "[null, null, null]" in cpos_launch.FORECAST_BLOCK


def test_the_forecast_instructions_lock_the_entry_values_the_method_would_ask_for():
    """Live run tdg-forecast-001 (2026-11-10): CP-2G declared a blocked forecast because the
    method's entry protocol found no forecast horizon and its helper scripts could not be run."""
    block = cpos_launch.FORECAST_BLOCK
    # The three entry stages of the method (forecast_horizon, base_period, cases) are given.
    assert "[forecast horizon: the three fiscal years after the base period]" in block
    assert "[base period: the current period the context names]" in block
    assert "[cases: base/upside/downside]" in block
    assert "do not ask for them and do not block the forecast for them" in block
    # The helper scripts are a transport mechanic here, not an analytical gate.
    for script in ("prepare_invocation.py", "validate_handoff.py"):
        assert script in block
    assert "is not a reason to block" in block
    # Owner, 2026-11-10 ("Yes, allow judgment"): run tdg-forecast-002 left every driver null for
    # want of numeric guidance. A driver without guidance is the analyst's labelled judgment,
    # anchored to a stated figure; null is kept for a driver nothing stated can anchor.
    assert "give your own judgment as `Analyst Interpretation`" in block
    assert "anchored to a stated figure" in block
    assert "name the anchor in `rationale`" in block and "in `limitation`" in block
    assert "only when no stated figure can anchor it" in block


def test_the_forecast_instructions_cap_driver_values_at_four_decimal_places():
    """Live run tdg-forecast-004 (2026-11-10): three ratios came at 38 decimal places."""
    assert "at most four decimal places" in cpos_launch.FORECAST_BLOCK


def cp2g_check(tmp_path, block):
    """The in-loop check of a CP-2G answer holding `block`, with a CP-1 that prints BASE."""
    prepared, task, context = good_task(tmp_path, "CP-2G", "distressed_restructuring")
    cp1 = " ".join(BASE.values()).encode()
    task = dataclasses.replace(task, handoffs={"CP-1": cp1})
    context["handoffs"] = {"CP-1": {"sha256": hashlib.sha256(cp1).hexdigest()}}
    routes = list(prepared.plan.layout.routes)
    raw = forecast_answer(context, routes, block).encode()
    return _checked_handoff(task, raw, checker(prepared.layout))


def test_checker_asks_for_repair_of_an_over_precise_driver(tmp_path):
    drivers = json.loads(forecast_block().split("```json\n")[1].split("\n```")[0])["base_drivers"]
    drivers["ebitda_margin"]["values"][0] = "0.48022670025188916876574307304785894207"
    issues = cp2g_check(tmp_path, forecast_block(base_drivers=drivers))
    assert any("ebitda_margin" in i and "Forecast inputs" in i for i in issues), issues


FACILITY_ROW = {
    "name": "Notes",
    "balance": "400",  # CP-1 here prints no 400, so the row is refused
    "fixed_rate_pct": "6.00",
    "spread_pct": None,
    "floor_pct": None,
    "reference_rate": None,
    "annual_amortisation": None,
    "maturity": None,
}


def test_a_facility_refusal_is_told_it_may_write_facilities_as_null(tmp_path):
    """A row that cannot be corrected must not cost the whole forecast: the repair line offers
    dropping `facilities`, not only nulling every driver."""
    (issue,) = cp2g_check(tmp_path, forecast_block(facilities=[FACILITY_ROW]))
    assert issue == (
        "Forecast inputs: CP-2G: facility Notes balance 400 is not printed in CP-1. "
        "Correct the facilities; if you cannot, write `facilities` as null and keep the drivers."
    )


def test_a_scheduled_repayment_refusal_is_told_the_same():
    cp1 = (" ".join(BASE.values()) + " 700 6.00%").encode()
    task = types.SimpleNamespace(module_id="CP-2G", handoffs={"CP-1": cp1})
    row = {**FACILITY_ROW, "balance": "700", "annual_amortisation": "300"}
    (issue,) = cpos_launch._forecast_issues(task, forecast_block(facilities=[row]))
    assert issue == (
        "Forecast inputs: CP-2G: scheduled repayments total 700, more than base debt 600. "
        "Correct the facilities; if you cannot, write `facilities` as null and keep the drivers."
    )


def test_a_schema_refusal_naming_a_facility_key_is_told_to_null_the_drivers():
    """The facilities line is for the refusals `_check_facilities` raises, not for any refusal whose
    path holds a model-written key containing `facilit`."""
    cp1 = " ".join(BASE.values()).encode()
    task = types.SimpleNamespace(module_id="CP-2G", handoffs={"CP-1": cp1})
    (issue,) = cpos_launch._forecast_issues(task, forecast_block(facility_note="x"))
    assert issue.startswith("Forecast inputs: CP-2G: forecast inputs: facility_note")
    assert issue.endswith(
        "Correct the block; if you cannot, set every driver's values to "
        "[null, null, null] and say why in scope_limits."
    )


def test_checker_accepts_a_valid_or_declined_forecast_block(tmp_path):
    assert cp2g_check(tmp_path, forecast_block()) == ()
    (tmp_path / "declined").mkdir()
    assert cp2g_check(tmp_path / "declined", REAL_DECLINED_BLOCK) == ()


@pytest.mark.parametrize(
    "values", [[{"low": "0.05"}, None, None], [["0.05"], None, None], "null", [], 5, None]
)
def test_odd_driver_values_end_in_value_error_not_type_error(values):
    drivers = json.loads(forecast_block().split("```json\n")[1].split("\n```")[0])["base_drivers"]
    for driver in drivers.values():
        driver["values"] = [None, None, None]
    drivers["dividends"]["values"] = values
    with pytest.raises(ValueError):
        cpos_forecast.parse(forecast_block(base_drivers=drivers), "1000 300")


def test_a_non_object_driver_ends_in_value_error():
    with pytest.raises(ValueError):
        cpos_forecast.parse(forecast_block(base_drivers={"revenue_growth": 5}), "1000")


def test_no_library_flag_is_accepted_and_defaults_off():
    base = ["--context", "c.json", "--sources", "s", "--config", "sol-medium", "--cap", "20"]
    assert cpos_launch._parser().parse_args(base).no_library is False
    assert cpos_launch._parser().parse_args([*base, "--no-library"]).no_library is True


def test_standing_ruling_lifts_the_pause_for_sol_medium_only():
    ruling = cpos_launch.ROOT / "docs/rulings/2026-11-09-inbox-automation.md"
    check_ruling("sol-medium", ruling)
    with pytest.raises(LivePauseInForce):
        check_ruling("sol-high", ruling)


def test_f_the_entry_writes_its_pid_before_any_check(tmp_path, monkeypatch):
    target = tmp_path / "run.pid"
    monkeypatch.setenv("DEPLOY_WORKFLOW_PID_FILE", str(target))
    with pytest.raises(SystemExit):  # argparse refuses the missing arguments: an early check
        main(["--bogus"])
    assert target.read_text(encoding="utf-8") == str(os.getpid())
    assert [p.name for p in tmp_path.iterdir()] == ["run.pid"]  # no temporary file left


def test_g_an_unwritable_pid_file_stops_the_entry_before_anything_else(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("DEPLOY_WORKFLOW_PID_FILE", str(tmp_path / "missing" / "run.pid"))

    def reached(*_a, **_k):
        raise AssertionError("a step after the PID file ran")

    monkeypatch.setattr(cpos_launch, "check_ruling", reached)
    monkeypatch.setattr(cpos_launch, "prepare", reached)
    assert main(["--bogus"]) != 0  # argparse would have raised SystemExit if it had been reached
    assert capsys.readouterr().err.strip() != ""


def test_h_without_the_variable_no_file_is_written(tmp_path, monkeypatch):
    monkeypatch.delenv("DEPLOY_WORKFLOW_PID_FILE", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        main(["--bogus"])
    assert list(tmp_path.iterdir()) == []


def test_web_search_follows_the_ruling_and_reaches_only_the_research_module(
    tmp_path, provider, capsys
):
    root = tmp_path / "rulings"
    root.mkdir()
    for name, configs in (("on.md", "sol-medium, web-search"), ("off.md", "sol-medium")):
        lines = (
            "lifts: live-provider-pause",
            "by: user",
            "date: 2026-11-10",
            f"configs: {configs}",
        )
        (root / name).write_text("\n".join(lines) + "\n")
    assert main(launch(tmp_path, "--ruling", str(RULING), pathway="relative_value")) == 0
    assert "Web:      off" in capsys.readouterr().out  # RULING does not list web-search.
    routes = prepare_routes(tmp_path, "sol-medium", modules=None)
    provider.answer = lambda context: answer(context, routes)
    manifest = tmp_path / "out/workflow.json"
    layout = HandoffPlan.model_validate_json(manifest.read_bytes()).layout
    searched = {}
    for name in ("on.md", "off.md"):
        provider.searched.clear()
        cpos_launch.run_live_handoffs(
            manifest,
            tmp_path / name,
            ruling=root / name,
            check=checker(layout),
            max_turns=4,
            max_output_tokens=cpos_launch.MAX_OUTPUT_TOKENS,
            rulings_root=root,
        )
        searched[name] = list(provider.searched)
    assert searched == {"on.md": ["CP-DR"], "off.md": []}


@pytest.mark.parametrize("module", sorted(OWNER_HEADERS))
def test_the_instructions_ask_each_owner_for_its_own_chart_table(tmp_path, module):
    prepared, *_ = good_task(tmp_path, module)
    text = (tmp_path / "out" / prepared.plan.instructions[module].path).read_text()
    assert f"`{OWNER_HEADERS[module]}`" in text
    constrained = module in {"CP-1", "CP-2D", "CP-3C", "CP-4C"}
    assert ("Not supplied: reported in <unit>" in text) is constrained


def test_a_module_with_no_owner_table_is_not_asked_for_one(tmp_path):
    prepared, *_ = good_task(tmp_path, "CP-5", "covenant_refinancing")
    text = (tmp_path / "out" / prepared.plan.instructions["CP-5"].path).read_text()
    assert "Chart data:" not in text


def test_the_bridge_instruction_states_the_opening_closing_and_sign_rules(tmp_path):
    prepared, *_ = good_task(tmp_path, "CP-2D", "covenant_refinancing")
    text = (tmp_path / "out" / prepared.plan.instructions["CP-2D"].path).read_text()
    for phrase in ("first row is the opening", "last row is the closing", "signed", "reconcile"):
        assert phrase in text, phrase


@pytest.mark.parametrize("module", sorted(OWNER_HEADERS))
def test_checker_accepts_each_owner_chart_table(tmp_path, module):
    prepared, task, context = good_task(tmp_path, module)
    raw = answer(context, list(prepared.plan.layout.routes)).encode()
    assert _checked_handoff(task, raw, checker(prepared.layout)) == ()


@pytest.mark.parametrize(
    ("module", "old", "new", "complaint"),
    [
        ("CP-1", "### Chart data: revenue and EBITDA", "### Revenue data", "revenue and EBITDA"),
        ("CP-1", "| FY2023 | 2,100 |", "| FY2023 | 2.1bn |", "2.1bn"),
        ("CP-1", "| 410 | US$m |", "| 410 | EUR m |", "EUR m"),
        ("CP-3C", "| Period | Debt maturing |", "| Year | Debt maturing |", "Period"),
        ("CP-3C", "| FY2026 | 500 | 300 |", "| FY2026 | 500 | 30% |", "30%"),
        ("CP-3C", "| 300 | US$m | Synthetic. |", "| 300 | US$m |  |", "Basis and limitation"),
        ("CP-2D", "### Chart data: liquidity bridge", "### Liquidity bridge", "liquidity bridge"),
        ("CP-2D", "| Step | Amount |", "| Item | Amount |", "Step"),
        ("CP-2D", "| -450 |", "| (450) |", "(450)"),
        ("CP-2D", "| 120 | US$m |", "| 120 | EUR m |", "EUR m"),
        ("CP-2D", "| 120 |", "| Not supplied: not stated |", "Not supplied"),
        ("CP-2D", "| 570 |", "| 560 |", "does not equal"),
        ("CP-2D", "| Debt repayment | -450 | US$m | Synthetic. |", "", "does not equal"),
        (
            "CP-2D",
            "| Free cash flow | 120 | US$m | Synthetic. |",
            "| Free cash flow | 120 | US$m |  |",
            "Basis",
        ),
    ],
)
def test_checker_sends_back_each_malformed_owner_chart_table(tmp_path, module, old, new, complaint):
    prepared, task, context = good_task(tmp_path, module)
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new).encode(), checker(prepared.layout))
    assert any(complaint in issue for issue in issues), issues


def bridge_table(*amounts: str, unit: str = "US$m") -> str:
    rows = [f"| Step {i} | {a} | {unit} | Synthetic. |" for i, a in enumerate(amounts)]
    return "\n".join(
        [
            "### Chart data: liquidity bridge",
            "",
            "| Step | Amount | Reporting unit | Basis and limitation |",
        ]
        + ["| --- | --- | --- | --- |", *rows]
    )


def bridge_issues(*amounts: str, unit: str = "US$m") -> tuple[str, ...]:
    table = cpos_launch.OWNER_TABLES["CP-2D"][0]
    return cpos_launch.chart_issues(bridge_table(*amounts, unit=unit), table)


def test_a_bridge_reconciles_at_the_precision_the_table_states():
    assert bridge_issues("0.1", "0.2", "0.3") == ()  # Decimal, not float: 0.1 + 0.2 is 0.3.
    assert bridge_issues("1,000.5", "-200.25", "800.25") == ()
    assert bridge_issues("1,000", "-1", "999") == ()
    assert bridge_issues("1,000", "-1", "998.9") != ()


def test_a_bridge_needs_an_opening_and_a_closing_row():
    assert any("opening and a closing" in i for i in bridge_issues("900"))


def test_a_bridge_with_every_amount_not_supplied_is_accepted_and_a_mixed_one_is_not():
    gap = "Not supplied: reported in EUR m"
    assert bridge_issues(gap, gap, gap, unit="EUR m") == ()
    mixed = bridge_issues("900", gap, "900")
    assert any("Not supplied" in i for i in mixed), mixed


def test_a_bridge_check_names_the_stated_and_summed_amounts():
    (issue,) = bridge_issues("900", "-300", "700")
    assert "600" in issue and "700" in issue


@pytest.mark.parametrize(
    ("module", "phrases"),
    [
        ("CP-1", ("issuer-adjusted or house-adjusted", "must not mix durations")),
        ("CP-2D", ("restricted or trapped cash", "uncertain facility access", "own step")),
        ("CP-3C", ("only a suggested path", "double-counting")),
    ],
)
def test_each_owner_table_carries_its_catalogue_guard(tmp_path, module, phrases):
    prepared, *_ = good_task(tmp_path, module)
    text = (tmp_path / "out" / prepared.plan.instructions[module].path).read_text()
    for phrase in phrases:
        assert phrase in text, phrase
    assert "in Basis and limitation" in text


def test_a_bridge_with_a_header_and_no_rows_is_sent_back():
    table = cpos_launch.OWNER_TABLES["CP-2D"][0]
    text = "### Chart data: liquidity bridge\n\n" + synthetic_table(
        "| Step | Amount | Reporting unit | Basis and limitation |"
    )
    assert any("opening and a closing" in i for i in cpos_launch.chart_issues(text, table))


@pytest.mark.parametrize("module", sorted(OWNER_HEADERS))
def test_delivery_presents_each_owner_table_as_a_plain_table_with_its_heading(tmp_path, module):
    """Owner tables are not report charts: delivery lists them as evidence tables, no new chart."""
    prepared, _, context = good_task(tmp_path, module)
    raw = answer(context, list(prepared.plan.layout.routes))
    routes = tuple(r for r in prepared.layout.routes if r.module_id == module)
    blocks = tuple(dict.fromkeys(r.block_id for r in routes))
    own = prepared.layout.model_copy(update={"blocks": blocks, "routes": routes, "front": ()})
    (tmp_path / "h.md").write_text(raw)
    handoff = HandoffInput(path="h.md", sha256=hashlib.sha256(raw.encode()).hexdigest())
    request = DeliveryRequest(run=prepared.plan.run, handoffs={module: handoff}, layout=own)
    files = markdown_files(request, tmp_path)
    for heading, table in OWNER_TABLES[module].items():
        listed = [
            e
            for e in json.loads(files["coverage.json"])["modules"][module]
            if e["heading"] == heading
        ]
        assert [(e["kind"], e["blocks"]) for e in listed] == [("table", ["evidence"])]
        assert "report.html" not in files
        view = files["view.json"].decode()
        assert heading in view
        for cell in table.splitlines()[2].strip("|").split("|"):
            assert cell.strip() in view


# ---- Package 2 (2026-11-10): the credit-structure tables. Every value is synthetic.
STRUCTURE_HEADERS = {
    "Chart data: debt stack": DEBT_STACK_HEAD,
    "Chart data: EBITDA bridge": "| Step | Amount | Reporting unit | Basis and limitation |",
    "Chart data: covenant headroom": COVENANT_HEAD,
    "Chart data: rating triggers": TRIGGER_HEAD,
    "Chart data: portfolio limits": LIMITS_HEAD,
}
STRUCTURE_OWNERS = [
    ("CP-1", "Chart data: debt stack"),
    ("CP-1", "Chart data: EBITDA bridge"),
    ("CP-4", "Chart data: covenant headroom"),
    ("CP-2H", "Chart data: rating triggers"),
    ("CP-6", "Chart data: portfolio limits"),
]


def instruction_text(tmp_path: Path, module: str) -> str:
    prepared, *_ = good_task(tmp_path, module)
    return (tmp_path / "out" / prepared.plan.instructions[module].path).read_text()


@pytest.mark.parametrize(("module", "heading"), STRUCTURE_OWNERS)
def test_each_credit_structure_table_is_asked_of_its_owner_with_its_fixed_header(
    tmp_path, module, heading
):
    text = instruction_text(tmp_path, module)
    assert f"`### {heading}`" in text
    assert f"`{STRUCTURE_HEADERS[heading]}`" in text


@pytest.mark.parametrize(
    ("module", "phrases"),
    [
        ("CP-1", ("legal rank", "positive common EBITDA denominator", "enterprise value")),
        ("CP-1", ("do not manufacture", "specified adjusted measure", "reconcile")),
        ("CP-4", ("strictness", "legal compliance opinion", "which side passes")),
        ("CP-2H", ("rating probability", "synthetic-source limitation", "agency")),
        ("CP-6", ("NAV denominator", "invented holdings", "interpretation")),
    ],
)
def test_each_credit_structure_table_carries_its_catalogue_guard(tmp_path, module, phrases):
    text = instruction_text(tmp_path, module)
    for phrase in phrases:
        assert phrase in text, phrase


@pytest.mark.parametrize(("module", "heading"), STRUCTURE_OWNERS)
def test_checker_accepts_each_credit_structure_table(tmp_path, module, heading):
    prepared, task, context = good_task(tmp_path, module)
    raw = answer(context, list(prepared.plan.layout.routes))
    assert heading in raw
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()


@pytest.mark.parametrize(
    ("module", "old", "new", "complaint"),
    [
        ("CP-1", "| Facility | Ranking |", "| Tranche | Ranking |", "Facility"),
        ("CP-1", "| Senior notes | 2 |", "| Senior notes | senior |", "Ranking"),
        (
            "CP-1",
            "| Senior secured term loan | 1 |",
            "| Senior secured term loan | 3 |",
            "rank order",
        ),
        ("CP-1", "| 1 | Yes |", "| 1 | Maybe |", "Secured"),
        ("CP-1", "| 1,200 |", "| 1.2bn |", "1.2bn"),
        ("CP-1", "| 800 | 4.0 | US$m |", "| 800 | 4.0 | EUR m |", "EUR m"),
        ("CP-1", "| 800 | 4.0 | US$m | Synthetic. |", "| 800 | 4.0 | US$m |  |", "Basis"),
        ("CP-1", "| 430 |", "| 440 |", "does not equal"),
        ("CP-4", "| Test | Threshold |", "| Covenant | Threshold |", "Test"),
        ("CP-4", "| 5.0 | 4.2 |", "| 5.0x | 4.2 |", "5.0x"),
        ("CP-4", "| Passes at or below |", "| Under |", "Direction"),
        ("CP-4", "| 0.8x |", "|  |", "Headroom"),
        (
            "CP-4",
            "| x | Synthetic. |\n| Interest",
            "|  | Synthetic. |\n| Interest",
            "Reporting unit",
        ),
        ("CP-2H", "| Passes below |", "| Passes sometimes |", "Direction"),
        ("CP-6", "| 5.0 |", "| 5% |", "5%"),
        ("CP-6", "| 3.0 | 4.0 |", "| 3.0 | 0.04 bn |", "0.04 bn"),
    ],
)
def test_checker_sends_back_each_malformed_credit_structure_table(
    tmp_path, module, old, new, complaint
):
    prepared, task, context = good_task(tmp_path, module)
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new, 1).encode(), checker(prepared.layout))
    assert any(complaint in issue for issue in issues), issues


def test_the_debt_stack_instruction_keeps_leverage_out_of_the_money_unit(tmp_path):
    text = instruction_text(tmp_path, "CP-1")
    assert "(Amount) are plain numbers in the money unit" in text
    assert "Cumulative leverage is a plain number in the unit its rule states" in text
    assert "(Amount, Cumulative leverage) are plain numbers in the money unit" not in text


# ---- Package 3 (2026-11-10): the comparison tables. Every value is synthetic.
COMPARISON_OWNERS = [
    ("CP-1B", "Chart data: prior and current results"),
    ("CP-1B", "Chart data: margin and KPI changes"),
    ("CP-1C", "Chart data: peer range — percent metrics"),
    ("CP-1C", "Chart data: peer range — multiples"),
    ("CP-3D", "Chart data: yield against maturity"),
]


@pytest.mark.parametrize(("module", "heading"), COMPARISON_OWNERS)
def test_each_comparison_table_is_asked_of_its_owner(tmp_path, module, heading):
    assert f"`### {heading}`" in instruction_text(tmp_path, module)


@pytest.mark.parametrize(
    ("module", "phrases"),
    [
        ("CP-1B", ("Pair only compatible quantities", "comparable perimeter", "percent panel")),
        ("CP-1B", ("percentage-point change", "not worked out here", "one pair")),
        ("CP-1C", ("excluded peers", "never zero", "settled observations")),
        ("CP-1C", ("do not calendarise", "multiples stay out of the percent table", "Peer count")),
        ("CP-3D", ("never mixed", "YTM, discount margin and spread", "source class")),
    ],
)
def test_each_comparison_table_carries_its_catalogue_guard(tmp_path, module, phrases):
    text = instruction_text(tmp_path, module)
    for phrase in phrases:
        assert phrase in text, phrase


@pytest.mark.parametrize(
    ("module", "old", "new", "complaint"),
    [
        ("CP-1B", "| 2,100 |", "| 2.1bn |", "2.1bn"),
        ("CP-1B", "| Measure | Prior period |", "| Item | Prior period |", "Measure"),
        (
            "CP-1B",
            "| Not supplied: not stated | US$m |",
            "| Not supplied: not stated | EUR m |",
            "one Reporting unit",
        ),
        ("CP-1B", "| 19.5 | FY2024 |", "| 19.5 | |", "Current period"),
        ("CP-1C", "| 12.0 | 18.5 | 26.0 |", "| 30.0 | 18.5 | 26.0 |", "order"),
        ("CP-1C", "| 7 | % |", "| seven | % |", "seven"),
        ("CP-1C", "| 2.5 | 3.4 | 5.1 |", "| 2.5 | 3.4 | 5.1x |", "5.1x"),
        ("CP-3D", "| 2028-06-15 |", "| June 2028 |", "June 2028"),
        ("CP-3D", "| 2028-06-15 |", "| 2028-02-31 |", "2028-02-31"),
        ("CP-3D", "| 6.4 |", "| 6.4% |", "6.4%"),
        ("CP-3D", "| 2028-06-15 |", "| 2024-01-01 |", "is before Quote date"),
        ("CP-1C", "| 7 | % |", "| -3 | % |", "whole number"),
        ("CP-1C", "| 7 | % |", "| 2.5 | % |", "whole number"),
        ("CP-3D", "| +310 bp |", "|  |", "Spread"),
        ("CP-3D", "| Dealer quote | % | Synthetic. |", "|  | % | Synthetic. |", "Source class"),
    ],
)
def test_checker_sends_back_each_malformed_comparison_table(tmp_path, module, old, new, complaint):
    prepared, task, context = good_task(tmp_path, module)
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new, 1).encode(), checker(prepared.layout))
    assert any(complaint in issue for issue in issues), issues


@pytest.mark.parametrize(
    ("module", "old", "new"),
    [
        ("CP-3D", "| 2028-06-15 |", "| Not supplied: no maturity stated |"),
        ("CP-1C", "| 12.0 | 18.5 | 26.0 |", "| Not supplied: none | 18.5 | 26.0 |"),
    ],
)
def test_a_stated_gap_is_accepted_for_a_maturity_date_and_for_a_peer_bound(
    tmp_path, module, old, new
):
    prepared, task, context = good_task(tmp_path, module)
    raw = answer(context, list(prepared.plan.layout.routes)).replace(old, new, 1)
    assert new in raw and _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()


# ---- Package 4 (2026-11-10): recovery by class and the value allocation waterfalls. Synthetic.
RECOVERY = "Chart data: recovery by class"
SCENARIO_THREE = "Chart data: value allocation \u2014 scenario 3"


def test_each_recovery_table_is_asked_of_cp_4c_and_only_supplied_scenarios_are(tmp_path):
    text = instruction_text(tmp_path, "CP-4C")
    for heading in (RECOVERY, ALLOCATION_ONE, ALLOCATION_TWO, SCENARIO_THREE):
        assert f"`### {heading}`" in text
    assert text.count("only if the handoff supplies") == 2  # Scenarios 2 and 3, not 1.


@pytest.mark.parametrize(
    "phrases",
    [
        (
            "never worked out here",
            "Recovery %",
            "only as the method caps it",
            "entity and collateral",
        ),
        (
            "not a complete multi-entity waterfall",
            "do not invent an absent downside or stress case",
        ),
        ("Scenario identity", "first row is the enterprise value", "no legal pool order"),
        ("last row is the value not distributed", "Available value", "negative change"),
    ],
)
def test_the_recovery_tables_carry_their_catalogue_guard(tmp_path, phrases):
    text = instruction_text(tmp_path, "CP-4C")
    for phrase in phrases:
        assert phrase in text, phrase


@pytest.mark.parametrize(
    ("old", "new", "complaint"),
    [
        ("| 90 |", "| 90% |", "90%"),
        ("| 1,200 | 1,080 |", "| 1.2bn | 1,080 |", "1.2bn"),
        ("| Class | Scenario |", "| Tranche | Scenario |", "Class"),
        ("| Senior secured | Base |", "| Senior secured |  |", "Scenario"),
        ("| 120 | 15 | US$m |", "| 120 | 15 | % |", "one Reporting unit"),
        ("| -1,080 |", "| -1,070 |", "does not equal"),
        ("| Value not distributed | 700 |", "| Value not distributed | 0 |", "does not equal"),
        (
            "| Senior secured distribution | -1,080 | US$m | Synthetic. |\n",
            "",
            "does not equal",
        ),
        ("| Enterprise value | 2,000 |", "| Enterprise value | 2bn |", "2bn"),
        ("| Step | Amount |", "| Item | Amount |", "Step"),
    ],
)
def test_checker_sends_back_each_malformed_recovery_table(tmp_path, old, new, complaint):
    prepared, task, context = good_task(tmp_path, "CP-4C")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new, 1).encode(), checker(prepared.layout))
    assert any(complaint in issue for issue in issues), issues


def allocation_spec(scenario: int):
    return next(
        t for t in cpos_launch.OWNER_TABLES["CP-4C"] if t.heading.endswith(f"scenario {scenario}")
    )


def test_an_unsupplied_scenario_is_not_required_but_the_first_is():
    absent = "### Findings\n\nNo table."
    assert cpos_launch.chart_issues(absent, allocation_spec(2)) == ()
    assert cpos_launch.chart_issues(absent, allocation_spec(3)) == ()
    assert cpos_launch.chart_issues(absent, allocation_spec(1)) != ()


def test_a_scenario_table_that_is_present_is_checked_even_when_optional():
    text = f"### {ALLOCATION_TWO}\n\n" + synthetic_table(
        ALLOCATION_HEAD, "| Enterprise value | 1 | US$m | S. |"
    )
    assert any(
        "opening and a closing" in i for i in cpos_launch.chart_issues(text, allocation_spec(2))
    )


def test_a_scenario_with_every_amount_not_supplied_is_accepted():
    gap = "Not supplied: no valuation row"
    text = f"### {ALLOCATION_ONE}\n\n" + synthetic_table(
        ALLOCATION_HEAD,
        f"| Enterprise value | {gap} | US$m | S. |",
        f"| Value not distributed | {gap} | US$m | S. |",
    )
    assert cpos_launch.chart_issues(text, allocation_spec(1)) == ()


@pytest.mark.parametrize(
    "heading",
    [
        "Chart data: value allocation - scenario 2",
        "Chart data: value allocation \u2013 scenario 2",
        "chart data: Value Allocation \u2014  Scenario 2",
    ],
)
def test_a_misheaded_optional_scenario_is_sent_back_naming_the_exact_heading(heading):
    text = f"### {heading}\n\n" + synthetic_table(
        ALLOCATION_HEAD,
        "| Enterprise value | 1 | US$m | S. |",
        "| Value not distributed | 1 | US$m | S. |",
    )
    (issue,) = cpos_launch.chart_issues(text, allocation_spec(2))
    assert f"`### {ALLOCATION_TWO}`" in issue


def test_the_exact_heading_and_an_absent_one_are_not_a_misheading():
    absent = "### Chart data: value allocation \u2014 scenario 1\n\nx"
    assert cpos_launch.chart_issues(absent, allocation_spec(2)) == ()


def test_a_recovery_table_with_more_than_three_scenarios_is_sent_back():
    head = RECOVERY_HEAD
    rows = [f"| Senior | S{n} | 10 | 5 | 50 | US$m | S. |" for n in range(4)]
    text = f"### {RECOVERY}\n\n" + synthetic_table(head, *rows)
    spec = next(t for t in cpos_launch.OWNER_TABLES["CP-4C"] if t.heading == RECOVERY)
    assert any("at most 3" in i for i in cpos_launch.chart_issues(text, spec))
    assert cpos_launch.chart_issues(text.replace(rows[-1], ""), spec) == ()


# ---- Package 5 (2026-11-10): the calendar lanes. Every value is synthetic.
def event_spec(module: str):
    heading = f"Events: {EVENT_LANES[module][0]}"
    return next(t for t in cpos_launch.OWNER_TABLES[module] if t.heading == heading)


def event_text(module: str, *rows: str) -> str:
    return f"### Events: {EVENT_LANES[module][0]}\n\n" + synthetic_table(EVENT_HEAD, *rows)


def event_issues(*rows: str, module: str = "CP-1A") -> tuple[str, ...]:
    return cpos_launch.chart_issues(event_text(module, *rows), event_spec(module))


@pytest.mark.parametrize("module", sorted(EVENT_LANES))
def test_every_lane_owner_is_asked_for_its_event_table_with_its_guard(tmp_path, module):
    lane, guard = EVENT_LANES[module]
    if module in OWNER_PATHWAY or module in COVENANT_MODULES:
        prepared, *_ = good_task(tmp_path, module)
        text = (tmp_path / "out" / prepared.plan.instructions[module].path).read_text()
    else:  # CP-2E is in no pathway: only an explicit --modules run reaches it.
        text = cpos_launch._selector(event_spec(module))
    assert f"`### Events: {lane}`" in text and f"`{EVENT_HEAD}`" in text
    assert guard in text and "YYYY-Qn" in text and "Not supplied: <reason>" in text


@pytest.mark.parametrize("module", sorted(EVENT_LANES))
def test_a_good_event_table_is_accepted_for_each_lane(module):
    assert event_issues(*EVENT_ROWS, module=module) == ()


@pytest.mark.parametrize(
    ("row", "complaint"),
    [
        (
            "| 2025-03 | day | 2024-11-07 | E | S | Src | R |",
            "Event date `2025-03` must be YYYY-MM-DD",
        ),
        ("| 2025-02-30 | day | 2024-11-07 | E | S | Src | R |", "must be YYYY-MM-DD"),
        ("| 2025-03-31 | month | 2024-11-07 | E | S | Src | R |", "must be YYYY-MM"),
        ("| 2025-13 | month | 2024-11-07 | E | S | Src | R |", "must be YYYY-MM"),
        ("| 2025-Q5 | quarter | 2024-11-07 | E | S | Src | R |", "must be YYYY-Qn"),
        ("| 2025-Q2 | year | 2024-11-07 | E | S | Src | R |", "must be YYYY"),
        ("| 2025 | week | — | E | S | Src | R |", "Date precision `week` must be one of"),
        ("| 2025-03-31 | day | May 2025 | E | S | Src | R |", "Published `May 2025`"),
        ("| 2025-03-31 | day | 2025-02-30 | E | S | Src | R |", "Published `2025-02-30`"),
        ("| 2025-03-31 | day | 2024-11-07 | | S | Src | R |", "Event is blank"),
        (
            "| 2025-03-31 | day | 2024-11-07 | E | S | Not supplied: none | R |",
            "Source is blank or not",
        ),
        (
            "| Not supplied: undated | day | 2024-11-07 | E | S | Src | R |",
            "Event date is blank or not",
        ),
    ],
)
def test_a_malformed_event_row_is_sent_back(row, complaint):
    issues = event_issues(EVENT_ROWS[0], row)
    assert any(complaint in i for i in issues), issues


# Published is the date of the publication the row is taken from (checker-loop-3, corrected). The
# 2033 maturity is taken from the FY2024 annual report, whose own date is 2024-11-07.
TEN_K_ROW = (
    "| 2033-06-15 | day | {} | 2033 senior secured notes mature | Scheduled \u2014 maturity "
    "| Annual report FY2024, p.145 | Wall |"
)


def test_the_instructions_for_an_events_module_state_the_published_rule():
    text = cpos_launch._selector(event_spec("CP-3"))
    assert "date of the publication the row is taken from" in text
    assert "only when that document states no date" in text


def test_a_published_equal_to_the_event_date_is_accepted_for_a_cited_document():
    row = (
        "| 2025-03-31 | day | 2025-03-31 | Results | Historical \u2014 released | 8-K p.1 | Wall |"
    )
    assert event_issues(row) == ()


def test_the_week_row_with_a_dash_is_refused_for_both_its_precision_and_its_published():
    issues = event_issues("| 2025 | week | \u2014 | E | S | Src | R |")
    assert any("Date precision `week` must be one of" in i for i in issues), issues
    assert any("Published `\u2014`" in i and "Not supplied: <reason>" in i for i in issues), issues


@pytest.mark.parametrize(
    "cell",
    [
        "\u2014",
        "-",
        "Not stated",
        "",
        " ",
        "n/a",
        "TBC",
        "Not supplied:",
        "Not supplied:   ",
        "07/11/2024",
        "2024-11-7",
        "November 7, 2024",
        "2024-11",
        "2024-02-30",
    ],
)
def test_a_published_that_is_not_a_date_or_a_reasoned_gap_is_refused_once_with_the_forms(cell):
    issues = event_issues(TEN_K_ROW.format(cell))
    assert len(issues) == 1 and "Not supplied: <reason>" in issues[0], issues


@pytest.mark.parametrize(
    "cell", ["2024-11-07", "2033-06-15", "Not supplied: the memo states no date"]
)
def test_a_published_date_or_a_reasoned_gap_is_accepted(cell):
    assert event_issues(TEN_K_ROW.format(cell)) == ()


def test_an_event_table_of_only_not_supplied_is_valid_and_a_mixed_one_is_not():
    gap = "Not supplied: the handoff states no dated event"
    assert event_issues(f"| {gap} |" + f" {gap} |" * 6) == ()
    assert event_issues(f"| {gap} |" + f" {gap} |" * 6, EVENT_ROWS[0]) != ()
    assert event_issues(f"| {gap} | day | 2024-11-07 | E | S | Src | R |") != ()


def test_an_event_table_needs_its_exact_header_and_a_row():
    wrong = "### Events: Legal\n\n" + synthetic_table(
        EVENT_HEAD.replace("Event date", "Date"), EVENT_ROWS[0]
    )
    assert any(
        "needs the table headed" in i for i in cpos_launch.chart_issues(wrong, event_spec("CP-4"))
    )
    assert any("at least one row" in i for i in event_issues())
    assert any(
        "Add `### Events: Legal`" in i for i in cpos_launch.chart_issues("x", event_spec("CP-4"))
    )


@pytest.mark.parametrize("heading", ["events: legal", "Events:  Legal", "EVENTS: LEGAL"])
def test_a_misheaded_event_table_is_sent_back_naming_the_exact_heading(heading):
    text = f"### {heading}\n\n" + synthetic_table(EVENT_HEAD, EVENT_ROWS[0])
    (issue,) = cpos_launch.chart_issues(text, event_spec("CP-4"))
    assert "`### Events: Legal`" in issue and heading in issue


def test_the_checker_sends_back_a_handoff_with_a_bad_event_precision(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-4")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert "| 2025-Q3 | quarter |" in raw
    bad = raw.replace("| 2025-Q3 | quarter |", "| 2025-Q3 | day |", 1)
    issues = _checked_handoff(task, bad.encode(), checker(prepared.layout))
    assert any("must be YYYY-MM-DD" in issue for issue in issues), issues
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()


@pytest.mark.parametrize(
    ("status", "ok"),
    [
        ("Historical — completed", True),
        ("Scheduled — due", True),
        ("Scenario — modelled downgrade trigger", True),
        ("Scheduled", False),
        ("Scheduled - due", False),
        ("Expected — due", False),
        ("scheduled — due", False),
        ("Scenario — ", False),
    ],
)
def test_an_event_status_starts_with_its_kind_and_a_dash(status, ok):
    issues = event_issues(f"| 2025-03-31 | day | 2024-11-07 | E | {status} | Src | R |")
    assert (issues == ()) is ok, issues
    assert ok or any("Status" in i for i in issues), issues


def test_a_published_date_equal_to_the_event_date_is_accepted_when_the_document_is_cited():
    # An 8-K or an earnings release is published on its event date: that is a legitimate row, so
    # the old refusal is gone (owner ruling, T1 follow-up). The instruction states the rule.
    assert (
        event_issues("| 2025-03-31 | day | 2025-03-31 | E | Scheduled — due | 8-K p.1 | R |") == ()
    )
    assert event_issues("| 2025-03-31 | day | 2025-03-30 | E | Scheduled — due | Src | R |") == ()
    assert event_issues("| 2025-03 | month | 2025-03-31 | E | Scheduled — due | Src | R |") == ()


def test_a_period_table_unit_and_second_table_get_the_same_advice():
    spec = cpos_launch.OWNER_TABLES["CP-1"][0]
    head = PERIOD_HEAD.format("Revenue | Adjusted EBITDA")
    row = "| FY2024 | 100 | 20 | {} | Basis. |"
    heading = f"### {spec.heading}\n\n"
    issues = cpos_launch.chart_issues(
        heading + synthetic_table(head, row.format("US$m; per year")), spec, money="US$m"
    )
    assert len(issues) == 2  # one per number cell, as before
    assert all("must be exactly `US$m`" in i and "Basis and limitation" in i for i in issues)
    other = cpos_launch.chart_issues(
        heading + synthetic_table(head, row.format("EUR m")), spec, money="US$m"
    )
    assert len(other) == 2 and all("write `Not supplied: reported in EUR m`" in i for i in other)
    second = "| Other | Date |\n| --- | --- |\n| x | 2024-10-18 |"
    text = heading + synthetic_table(head, row.format("US$m")) + "\n" + second
    (two,) = cpos_launch.chart_issues(text, spec, money="US$m")
    assert "a second table under this heading: give it its own ### heading" in two


def test_the_event_rules_say_record_once_and_the_status_kinds():
    text = cpos_launch._selector(event_spec("CP-2H"))
    assert "Record each event once, in the lane of the module that owns it" in text
    assert "another module refers to it in Credit relevance" in text
    assert "`Historical`, `Scheduled` or `Scenario`" in text


# ---- Package 6 (2026-11-10): the node/edge maps. Every value is synthetic.
def map_spec(heading: str):
    module = MAPS[heading][0]
    return next(t for t in cpos_launch.OWNER_TABLES[module] if t.heading == heading)


def map_issues(heading: str, *rows: str) -> tuple[str, ...]:
    text = f"### {heading}\n\n" + synthetic_table(EDGE_HEAD, *rows)
    return cpos_launch.chart_issues(text, map_spec(heading))


@pytest.mark.parametrize("heading", sorted(MAPS))
def test_every_map_owner_is_asked_for_its_edge_table_with_its_vocabulary_and_guard(heading):
    _, types, guards = MAPS[heading]
    text = cpos_launch._selector(map_spec(heading))
    assert f"`### {heading}`" in text and f"`{EDGE_HEAD}`" in text
    assert all(t in text for t in types) and all(g in text for g in guards)
    assert "Not supplied: <reason>" in text and "Basis and limitation" not in text


@pytest.mark.parametrize("heading", sorted(MAPS))
def test_a_good_edge_table_is_accepted_and_an_edge_type_outside_the_vocabulary_is_sent_back(
    heading,
):
    _, types, _ = MAPS[heading]
    good = [f"| A | rel | {t} | B | Src |" for t in types]
    assert map_issues(heading, *good) == ()
    (issue,) = map_issues(heading, "| A | rel | Weighted | B | Src |")
    assert "Edge type `Weighted` must be one of" in issue
    assert any("Edge type" in i for i in map_issues(heading, "| A | rel | ownership | B | Src |"))


def test_an_edge_table_of_only_not_supplied_is_valid_and_a_mixed_or_blank_one_is_not():
    heading = "Map: stress scenario"
    gap = "Not supplied: no scenario stated"
    assert map_issues(heading, f"| {gap} |" + f" {gap} |" * 4) == ()
    assert map_issues(heading, f"| {gap} |" + f" {gap} |" * 4, "| A | r | Assumption | B | S |")
    assert any("From is blank" in i for i in map_issues(heading, "| | r | Assumption | B | S |"))
    assert any(
        "Evidence is blank" in i for i in map_issues(heading, "| A | r | Assumption | B | |")
    )
    assert any("at least one row" in i for i in map_issues(heading))


def test_an_edge_table_needs_its_exact_header_and_a_misheaded_one_names_the_heading():
    heading = "Map: legal entities"
    wrong = f"### {heading}\n\n" + synthetic_table(EDGE_HEAD.replace("From", "Source"), "")
    assert any(
        "needs the table headed" in i for i in cpos_launch.chart_issues(wrong, map_spec(heading))
    )
    missing = cpos_launch.chart_issues("x", map_spec(heading))
    assert any(f"Add `### {heading}`" in i for i in missing)
    near = "### map: Legal entities\n\n" + synthetic_table(
        EDGE_HEAD, "| A | r | Ownership | B | S |"
    )
    (issue,) = cpos_launch.chart_issues(near, map_spec(heading))
    assert f"`### {heading}`" in issue


def test_the_cp4_map_rules_say_the_narrow_registers_alone_do_not_make_a_graph():
    for heading in ("Map: legal entities", "Map: intercreditor"):
        assert "narrow registers alone do not establish" in map_spec(heading).rules


@pytest.mark.parametrize("dash", ["—", "-", "–"])
def test_a_dash_is_not_edge_evidence_and_is_sent_back(dash):
    issues = map_issues("Map: stress scenario", f"| A | r | Assumption | B | {dash} |")
    assert any("Evidence" in i and "names its source" in i for i in issues), issues


# ---- Package 8 (2026-11-10): one "states none" escape for every row table. Synthetic values.
ROW_SPECS = [
    t for tables in cpos_launch.OWNER_TABLES.values() for t in tables if t.columns and not t.bare
]
NONE_GAP = "Not supplied: the handoff states none"


def none_text(spec, *, unit: str = "US$m", basis: str = "Synthetic.") -> str:
    header = cpos_launch._chart_header(spec)
    cells = [NONE_GAP] * (len(header) - 2) + [unit, basis]
    return f"### {spec.heading}\n\n" + synthetic_table(
        "| " + " | ".join(header) + " |", "| " + " | ".join(cells) + " |"
    )


@pytest.mark.parametrize("spec", ROW_SPECS, ids=lambda s: s.heading)
def test_every_row_table_accepts_one_all_gap_row_as_the_module_stating_none(spec):
    assert cpos_launch.chart_issues(none_text(spec), spec) == ()
    assert cpos_launch._selector(spec).count("states none") == 1


@pytest.mark.parametrize("spec", ROW_SPECS, ids=lambda s: s.heading)
def test_an_all_gap_row_still_states_its_unit_and_basis_and_is_not_mixed_with_real_rows(spec):
    assert cpos_launch.chart_issues(none_text(spec, basis=""), spec)
    assert cpos_launch.chart_issues(none_text(spec, unit=""), spec)
    mixed = none_text(spec)
    row = mixed.splitlines()[-1].replace(NONE_GAP, "x", 1)
    assert cpos_launch.chart_issues(mixed + "\n" + row, spec)


def test_a_debt_stack_left_with_no_ranked_facility_may_state_none():
    spec = next(t for t in ROW_SPECS if t.heading == "Chart data: debt stack")
    assert cpos_launch.chart_issues(none_text(spec), spec) == ()
    assert "left out" in spec.rules and "states none" in cpos_launch._selector(spec)


DEBT_UNIT_ROW = "| Term loan | 1 | Yes | 1871 | 4.72 | {} | Equal rank. |"


def debt_stack_issues(*rows: str) -> tuple[str, ...]:
    spec = next(t for t in ROW_SPECS if t.heading == "Chart data: debt stack")
    text = "### Chart data: debt stack\n\n" + synthetic_table(DEBT_STACK_HEAD, *rows)
    return cpos_launch.chart_issues(text, spec, money="US$m")


def test_a_unit_that_starts_with_the_chart_unit_is_told_to_keep_only_the_unit():
    (issue,) = debt_stack_issues(DEBT_UNIT_ROW.format("US$m; leverage in times"))
    assert "must be exactly `US$m`" in issue and "Basis and limitation" in issue
    assert "Not supplied" not in issue


def test_a_real_other_unit_keeps_the_gap_advice_and_the_issue_count():
    (issue,) = debt_stack_issues(DEBT_UNIT_ROW.format("EUR m"))
    assert "write `Not supplied: reported in EUR m`" in issue
    two = debt_stack_issues(
        DEBT_UNIT_ROW.format("US$m; leverage in times"), DEBT_UNIT_ROW.format("US$m; x")
    )
    assert len(two) == 2


@pytest.mark.parametrize("unit", ["US$m / EUR m", "US$m; EUR amounts", "US$m (GBP)"])
def test_a_unit_cell_naming_another_currency_keeps_the_gap_advice(unit):
    (issue,) = debt_stack_issues(DEBT_UNIT_ROW.format(unit))
    assert f"write `Not supplied: reported in {unit}`" in issue
    assert "must be exactly" not in issue


@pytest.mark.parametrize(
    "unit", ["US$m (LTM)", "US$m; PIK interest accrued", "US$m, RCF drawn only", "US$m (TTM basis)"]
)
def test_a_three_letter_acronym_after_the_unit_is_not_another_currency(unit):
    (issue,) = debt_stack_issues(DEBT_UNIT_ROW.format(unit))
    assert "must be exactly `US$m`" in issue
    assert "Not supplied" not in issue


def test_a_second_table_under_one_heading_is_named_not_reported_as_malformed_rows():
    second = (
        "| Transaction-only balance | Date | Amount | Unit | Basis | Source |\n"
        "| --- | --- | ---: | --- | --- | --- |\n"
        "| Pro forma gross debt | 2024-10-18 | 25230.5 | USD millions | C29 | p.63 |"
    )
    spec = next(t for t in ROW_SPECS if t.heading == "Chart data: debt stack")
    first = DEBT_UNIT_ROW.format("US$m")
    text = (
        "### Chart data: debt stack\n\n" + synthetic_table(DEBT_STACK_HEAD, first) + "\n" + second
    )
    (issue,) = cpos_launch.chart_issues(text, spec, money="US$m")
    assert "a second table under this heading: give it its own ### heading" in issue
    assert "needs 7 cells" not in issue


def test_a_repeated_class_and_scenario_row_is_sent_back_but_a_repeated_class_is_not():
    spec = next(t for t in ROW_SPECS if t.heading == RECOVERY)
    one = "| Senior | Base | 100 | 50 | 50 | US$m | S. |"
    other = "| Senior | Downside | 100 | 20 | 20 | US$m | S. |"
    duplicate = f"### {RECOVERY}\n\n" + synthetic_table(RECOVERY_HEAD, one, one)
    assert any("Senior" in i and "twice" in i for i in cpos_launch.chart_issues(duplicate, spec))
    distinct = f"### {RECOVERY}\n\n" + synthetic_table(RECOVERY_HEAD, one, other)
    assert cpos_launch.chart_issues(distinct, spec) == ()


def test_a_user_reminder_status_the_cp6_guard_names_is_accepted_and_a_lookalike_is_not():
    row = "| 2026-01-15 | day | 2024-11-07 | Review | {} | Analyst note | Review date |"
    for status in ("User reminder", "User reminder — due"):
        assert event_issues(row.format(status), module="CP-6") == (), status
    for status in ("User reminders", "user reminder", "User reminder -"):
        assert event_issues(row.format(status), module="CP-6"), status
    guard = cpos_launch.EVENT_LANES["CP-6"][1]
    assert "labelled `User reminder` in Status" in guard


def test_the_currency_sentence_is_sent_only_with_a_unit_constraint():
    sentence = "reported in <unit>"
    for spec in ROW_SPECS:
        # CP-1's money tables state the money unit in the check block instead (C1).
        sent = bool(spec.chart_unit) and spec.chart_unit != cpos_launch.MONEY
        assert (sentence in cpos_launch._selector(spec)) is sent, spec.heading
    bridge = next(
        t
        for ts in cpos_launch.OWNER_TABLES.values()
        for t in ts
        if t.steps and t.chart_unit != cpos_launch.MONEY
    )
    assert sentence in cpos_launch._selector(bridge)


def test_the_value_allocation_rules_are_sent_once_to_their_module(tmp_path):
    text = instruction_text(tmp_path, "CP-4C")
    assert text.count("Scenario identity is the label of its source valuation row") == 1


@pytest.mark.parametrize("module", ["CP-1A", "CP-4"])
def test_shared_edge_rules_are_sent_once_per_module(tmp_path, module):
    text = instruction_text(tmp_path, module)
    assert text.count(cpos_launch.EDGE_RULES) == 1


# --- module_options reach CP-3 and CP-6 -------------------------------------------------------


def context_with_options(tmp_path: Path, **options: object) -> Path:
    path = context_file(tmp_path, "portfolio_decision")
    if options:
        data = json.loads(path.read_text())
        data["module_options"] = options
        path.write_text(json.dumps(data))
    return path


def test_the_chosen_cp3_mode_and_deep_debate_reach_their_instructions(tmp_path):
    prepared = prepare(
        context_with_options(tmp_path, cp3_mode="single_name_rv", cp6_deep_debate=True),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="20",
    )
    cp3 = (prepared.directory / "instructions/CP-3.md").read_text()
    cp6 = (prepared.directory / "instructions/CP-6.md").read_text()
    assert "The user selected the execution mode Single-Name RV" in cp3
    assert "Deep Debate Mode is ON" in cp6
    assert "Deep Debate Mode is ON" not in cp3


def test_without_options_the_instructions_carry_neither_block(tmp_path):
    prepared = prepare(
        context_with_options(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="20",
    )
    for path in (prepared.directory / "instructions").glob("*.md"):
        text = path.read_text()
        assert "The user selected the execution mode" not in text, path.name
        assert "Deep Debate Mode is ON" not in text, path.name


def test_options_only_change_the_instruction_they_name(tmp_path):
    texts = {}
    for name, options in (("plain", {}), ("chosen", {"cp3_mode": "clo_screening"})):
        base = tmp_path / name
        base.mkdir()
        prepared = prepare(
            context_with_options(base, **options),
            issuer_folder(base),
            base / "out",
            config="sol-medium",
            cap="20",
        )
        texts[name] = {
            p.name: p.read_text() for p in (prepared.directory / "instructions").glob("*.md")
        }
    assert texts["plain"].keys() == texts["chosen"].keys()
    changed = {n for n in texts["plain"] if texts["plain"][n] != texts["chosen"][n]}
    assert changed == {"CP-3.md"}


# --- the offline document reading on its own --------------------------------------------------


def test_read_documents_gives_what_prepare_gives(tmp_path):
    folder = issuer_folder(tmp_path)
    reading = cpos_launch.read_documents(folder)
    prepared = prepare(
        context_file(tmp_path), folder, tmp_path / "out", config="sol-medium", cap="20"
    )
    assert reading.documents == prepared.documents and reading.documents
    assert reading.ignored == prepared.ignored


def test_read_documents_lists_a_skipped_file_and_refuses_an_empty_one(tmp_path):
    folder = tmp_path / "mixed"
    folder.mkdir()
    (folder / "a.txt").write_text("Net sales were 100.")
    (folder / "deck.pptx").write_bytes(b"PK")
    (folder / "_notes.txt").write_text("private")
    reading = cpos_launch.read_documents(folder)
    assert reading.ignored == ("_notes.txt", "deck.pptx")
    assert [d["source"] for d in reading.documents] == ["a.txt"]
    assert sorted(p.name for p in folder.iterdir()) == ["_notes.txt", "a.txt", "deck.pptx"]
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "blank.txt").write_text("")
    with pytest.raises(LaunchRefused, match="blank.txt"):
        cpos_launch.read_documents(empty)


@pytest.mark.parametrize(
    ("mode", "label"),
    [
        ("clo_screening", "CLO Screening"),
        ("single_name_rv", "Single-Name RV"),
        ("capital_structure_rv", "Capital-Structure RV"),
        ("watchlist_monitoring", "Watchlist Monitoring"),
    ],
)
def test_each_cp3_mode_names_its_label(tmp_path, mode, label):
    prepared = prepare(
        context_with_options(tmp_path, cp3_mode=mode),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="20",
    )
    cp3 = (prepared.directory / "instructions/CP-3.md").read_text()
    assert f"The user selected the execution mode {label} (source" in cp3


def test_cp3_labels_cover_exactly_the_modes_the_context_allows():
    assert set(cpos_launch.CP3_MODE_LABELS) == set(typing.get_args(Cp3Mode)) - {""}


def test_instruction_states_the_reader_voice_rulings(tmp_path):
    texts = all_texts(tmp_path)
    for module, text in texts.items():
        head = text.partition(cpos_launch.METHOD_MARK)[0]
        assert "begins exactly `Not assessable: `" in head, module
        assert 'must not use the words "not assessable"' in head, module
    prose = next(t for m, t in texts.items() if m not in DATA_MODULE_IDS)
    head = prose.partition(cpos_launch.METHOD_MARK)[0]
    for phrase in (
        "A coupon with more than two decimals (6.375%) is named by the note's maturity and rank",
        (
            "Every figure in a reader passage must also appear in the handoff's tables or "
            "`## Calculations` with the same sign, unit and scale."
        ),
        "the `[Insufficient Information]` tag belongs in tables only",
        "Never round an exact value",
        "basis points, percentage points, pp, times, notch(es), day(s), week(s)",
        "does not belong in a reader sentence",
        "- No limitation changes the conclusions of <plain module name>.",
        "column headed `ID` or ending ` ID`",
        "exact table header with one row stating not assessable",
        "govern over the reader layer's table rules (6 columns and 8 body rows)",
        "Start it with a word, not a figure or a symbol",
        "on one line",
    ):
        assert phrase in head, phrase


def test_checker_rejects_a_reader_number_the_handoff_does_not_hold(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-4")
    raw = answer(context, list(prepared.plan.layout.routes))
    wrong = raw.replace("cover is thin at 3.1x", "leverage is 9.87x")
    issues = _checked_handoff(task, wrong.encode(), checker(prepared.layout))
    assert any(i.startswith("Fidelity check, line ") and '"9.87x"' in i for i in issues)
    assert not any("Prose check 9" in i for i in issues)


def test_high_modules_outside_the_run_are_refused(tmp_path, capsys):
    assert main([*launch(tmp_path), "--modules", "CP-4", "--high-modules", "CP-1A"]) == 2
    assert "CP-1A" in capsys.readouterr().err


def test_high_modules_are_refused_when_the_config_already_runs_high(tmp_path, capsys):
    argv = [*launch(tmp_path), "--high-modules", "CP-4"]
    argv[argv.index("sol-medium")] = "sol-high"
    assert main(argv) == 2
    assert "--high-modules" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_balanced_and_high_modules_together_are_refused_before_any_folder(tmp_path, capsys):
    argv = [*launch(tmp_path), "--balanced", "--high-modules", "CP-4"]
    assert main(argv) == 2
    assert "--balanced" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_balanced_is_refused_when_the_config_already_runs_high(tmp_path, capsys):
    argv = [*launch(tmp_path), "--balanced"]
    argv[argv.index("sol-medium")] = "sol-high"
    assert main(argv) == 2
    assert "--balanced needs a config whose model allows high" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_balanced_is_refused_when_the_model_lacks_high(tmp_path, capsys):
    argv = [*launch(tmp_path), "--balanced"]
    argv[argv.index("sol-medium")] = "deepseek-max"
    assert main(argv) == 2
    err = capsys.readouterr().err
    assert "--balanced needs a config whose model allows high" in err
    assert "--high-modules" not in err
    assert not (tmp_path / "out").exists()


def test_balanced_sends_high_to_the_balanced_modules_in_the_run_only(tmp_path, capsys):
    assert main([*launch(tmp_path), "--balanced", "--modules", "CP-4"]) == 0
    out = capsys.readouterr().out
    assert "Effort:   high for CP-4; medium otherwise" in out


def test_balanced_with_no_balanced_module_in_the_run_prints_no_effort_line(tmp_path, capsys):
    assert main([*launch(tmp_path), "--balanced", "--modules", "CP-1"]) == 0
    assert "Effort:" not in capsys.readouterr().out


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        (("--high-modules", "CP-4"), {"CP-4": "high"}),
        (
            ("--balanced",),
            {"CP-1A": "high", "CP-2": "high", "CP-2A": "high", "CP-3C": "high", "CP-4": "high"},
        ),
        ((), {}),
    ],
)
def test_an_accepted_run_hands_its_effort_map_to_run_live_handoffs(
    tmp_path, monkeypatch, copilot_ruling, flags, expected
):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "ghp_" + "Z" * 36)
    runtime = tmp_path / "copilot-runtime"
    runtime.write_text("#!/bin/sh\n")
    monkeypatch.setenv("COPILOT_CLI_PATH", str(runtime))
    seen = {}

    def fake_run(manifest, directory, **kwargs):
        seen.update(kwargs)
        return directory / "delivery.json"

    monkeypatch.setattr(cpos_launch, "run_live_handoffs", fake_run)
    argv = copilot_argv(
        tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling), *flags
    )
    assert main(argv) == 0
    assert seen["effort_by_module"] == expected


def test_run_live_handoffs_hands_the_effort_map_to_the_executor(tmp_path, monkeypatch):
    from deploy_workflow.model import handoff
    from deploy_workflow.owners import cpos

    seen = {}

    class Stop(Exception):
        pass

    def executor(*args, **kwargs):
        seen.update(kwargs)
        raise Stop

    monkeypatch.setattr(handoff, "HandoffExecutor", executor)
    monkeypatch.setattr(cpos, "live_adapter_for", lambda *a, **k: object())
    prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    with pytest.raises(Stop):
        cpos.run_live_handoffs(
            tmp_path / "out/workflow.json",
            tmp_path / "live",
            ruling=RULING,
            check=lambda *_: (),
            effort_by_module={"CP-4": "high"},
        )
    assert seen["effort_by_module"] == {"CP-4": "high"}


def test_the_service_standing_ruling_lists_web_search_so_runs_from_the_page_search():
    from deploy_workflow.inbox.startup import STANDING_RULING
    from deploy_workflow.owners.cpos import web_search_ruled

    assert web_search_ruled(STANDING_RULING)
    assert not web_search_ruled(RULING)  # a ruling that lists only the config does not


def test_cp2g_is_told_how_to_state_facilities(tmp_path):
    _, texts = all_instructions(tmp_path, modules=("CP-0", "CP-1", "CP-2A", "CP-2G"))
    head = texts["CP-2G"].partition(cpos_launch.METHOD_MARK)[0]
    for word in (
        "`facilities`",
        "1.25 times base debt",
        "drawn principal",
        "fixed_rate_pct",
        "spread_pct",
        "floor_pct",
        "reference_rate",
        "annual_amortisation",
        "maturity",
        "exactly as CP-1 prints",
        "% sign",
        '"0.04"',
    ):
        assert word in head
    assert "`facilities`" not in texts["CP-1"]


def test_web_search_is_ruled_for_openai_configs_only(monkeypatch):
    # The standing ruling lists web-search and both providers' configs; search is OpenAI's tool.
    from deploy_workflow.owners.cpos import web_search_run

    assert web_search_run("sol-medium", STANDING) is True
    assert web_search_run("opus-medium", STANDING) is False
    assert web_search_run("opus-high", STANDING) is False
    assert web_search_run("sol-medium", RULING) is False  # this ruling lists no web-search
    assert web_search_run("sol-medium", None) is False


def test_a_claude_run_under_a_ruling_that_lists_web_search_runs_with_search_off(
    tmp_path, monkeypatch
):
    from deploy_workflow.model import handoff
    from deploy_workflow.owners import cpos

    seen: dict[str, object] = {}

    class Stop(Exception):
        pass

    def recording(*args, **kwargs):
        seen["web_search"] = kwargs["web_search"]
        raise Stop

    monkeypatch.setattr(handoff, "HandoffExecutor", recording)
    monkeypatch.setattr(cpos, "live_adapter_for", lambda *args: object())
    monkeypatch.setattr(cpos, "_release", lambda adapter, executor: None)
    prepared = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="opus-medium",
        cap="50",
        modules=("CP-DR",),
    )
    for config, searching in (("opus-medium", False), ("sol-medium", True)):
        with pytest.raises(Stop):
            cpos.run_live_handoffs(
                prepared.manifest,
                tmp_path / config,
                ruling=STANDING,
                check=lambda *_: (),
                config=config,
                environ={},
            )
        assert seen["web_search"] is searching


def test_a_claude_launch_says_search_is_off_and_holds_no_search_fee(tmp_path, capsys):
    argv = launch(tmp_path, "--modules", "CP-DR", "--ruling", str(STANDING))
    argv[argv.index("sol-medium")] = "opus-medium"
    with_case_kind(tmp_path / "context.json", "public")
    plain = prepare(
        tmp_path / "context.json",
        tmp_path / "issuer",
        tmp_path / "probe",
        config="opus-medium",
        cap="50",
        modules=("CP-DR",),
    )
    argv[argv.index("--cap") + 1] = str(plain.hold + Decimal("0.05"))  # a 0.16 fee would not fit
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert "Web:      off: web search is offered on GPT Sol only" in out
    assert "CP-DR searches the web" not in out


STANDING = ROOT / "docs/rulings/2026-11-11-run-start-submit.md"  # sol and opus configs


@pytest.mark.parametrize(
    ("config", "asked"),
    [
        ("opus-medium", 64000),
        ("opus-high", 64000),
        ("sol-medium", 32000),
        ("sol-high", 32000),
    ],
)
def test_the_launch_asks_anthropic_for_room_after_its_thinking(
    tmp_path, monkeypatch, config, asked
):
    # A real run (tdg-proof-snapshot-opus-001, CP-4) lost its write_handoff call: Anthropic spends
    # thinking tokens out of the output limit, so 7,431 thinking plus the handoff did not fit in
    # 32,000 and the stream stopped on max_tokens inside the tool call. Anthropic configs ask for
    # 64,000; every other config keeps 32,000.
    seen = {}
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.setenv(key, "not-a-real-key")

    def capture(*args, **kwargs):
        seen.update(kwargs)
        raise RuntimeError("stop before any provider call")

    monkeypatch.setattr(cpos_launch, "run_live_handoffs", capture)
    argv = launch(tmp_path, "--live", "--ruling", str(STANDING))
    argv[argv.index("--config") + 1] = config
    main(argv)
    assert seen["max_output_tokens"] == asked


def test_the_offline_hold_follows_the_larger_anthropic_output_limit(tmp_path, monkeypatch):
    # Opus output costs USD 20 per million tokens, so the 32,000 extra output tokens add exactly
    # 32,000 x 20 / 1,000,000 = USD 0.64 to the hold; the input part does not move.
    context, folder = context_file(tmp_path), issuer_folder(tmp_path)

    def hold(config: str, out: str) -> Decimal:
        return prepare(
            context, folder, tmp_path / out, config=config, cap="50", modules=("CP-4",)
        ).hold

    now = hold("opus-medium", "now")
    sol = hold("sol-medium", "sol")
    monkeypatch.setattr(cpos_launch, "output_limit", lambda config: 32000)
    assert now - hold("opus-medium", "old") == Decimal("0.64")
    assert hold("sol-medium", "sol-old") == sol


# --- a refusal quotes at most 80 characters of the block's text; the cell check is exact ---------
def test_a_refusal_quotes_a_long_row_and_period_cut_to_80_characters():
    doc = _cp1_doc(TWO_YEARS)
    long_row, long_period = "revenue" + "x" * 200_000, "FY" + "y" * 200_000
    with pytest.raises(ValueError) as caught:
        _named_cp2g(doc, revenue=_operand("1000", long_row, "FY2025"))
    message = str(caught.value)
    assert len(message) < 400
    assert message == (
        f"CP-2G: base revenue: no table cell of CP-1 is at row `{long_row[:77]}...`, "
        "period `FY2025`"
    )
    with pytest.raises(ValueError) as caught:
        _named_cp2g(doc, revenue=_operand("1000", "revenue", long_period))
    assert str(caught.value) == (
        f"CP-2G: base revenue: no table cell of CP-1 is at row `revenue`, "
        f"period `{long_period[:77]}...`"
    )


def test_a_refusal_quotes_a_long_cell_text_cut_to_80_characters():
    cell = "(" + "9" * 200 + ")"
    doc = _cp1_doc(f"| Metric | FY2025 |\n| --- | --- |\n| revenue | {cell} |")
    with pytest.raises(ValueError) as caught:
        _named_cp2g(doc, revenue=_operand("1000"))
    assert str(caught.value) == (
        "CP-2G: base revenue 1000 is not CP-1's cell at row `revenue`, period `FY2025` "
        f"({cell[:77]}...)"
    )


@pytest.mark.parametrize(
    ("key", "printed_cell", "amount"),
    [
        ("interest", "(45.00000000000000000000000000001)", "45"),  # 31 digits: abs() would round
        ("capex", "45.00000000000000000000000000001", "45"),
        ("wc", "45.00000000000000000000000000001", "-45"),  # the reversed sign rounds too
        ("ebitda", "45.00000000000000000000000000001", "45"),
    ],
)
def test_a_cell_of_more_than_28_digits_is_not_rounded_into_agreement(key, printed_cell, amount):
    doc = _cp1_doc(f"| Metric | FY2025 |\n| --- | --- |\n| {key} | {printed_cell} |", key=key)
    with pytest.raises(ValueError) as caught:
        _named_cp2g(doc, **{key: _operand(amount, key)})
    assert str(caught.value).startswith(
        f"CP-2G: base {key} {amount} is not CP-1's cell at row `{key}`, period `FY2025`"
    )


@pytest.mark.parametrize("name", ["", "   ", "**", " ` ` ", "_*_"])
@pytest.mark.parametrize("which", ["row", "period"])
def test_a_row_or_period_that_is_blank_once_plain_is_refused_as_unnamed(name, which):
    operand = _operand("1000") | {which: name}
    with pytest.raises(ValueError, match=re.escape(MUST_NAME)):
        _named_cp2g(_cp1_doc(TWO_YEARS), revenue=operand)


# --- the whole-branch review's fixes: the repair line, bounded cell lists, the surviving mutants --
OPERAND_END = "as missing: amount null, no row, period or column, and the reason."
FACILITY_END = "write `facilities` as null and keep the drivers."
BLOCK_END = "[null, null, null] and say why in scope_limits."


def _repair_issues(block: str, cp1: str) -> tuple[str, ...]:
    task = types.SimpleNamespace(module_id="CP-2G", handoffs={"CP-1": cp1.encode()})
    return cpos_launch._forecast_issues(task, block)


def _named_base(**changes):
    base = {k: _operand(v, k) for k, v in BASE.items()}
    return base | changes


def _cp1_with_rows(rows: dict[str, str], extra: str = "") -> str:
    body = "\n".join(f"| {rows.get(k, k)} | {printed(k, v)} |" for k, v in BASE.items())
    return f"| Base | FY2025 |\n| --- | --- |\n{body}\n{extra}"


@pytest.mark.parametrize(
    ("key", "amount", "row"),
    [
        ("undrawn", "51", "Revolving credit facility"),  # CP-1's cell is 50
        ("undrawn", "51", "Undrawn committed facilities"),
        ("debt", "601", "Debt after scheduled repayments"),
        ("revenue", "1001", "Guidance gives no forecast drivers"),
    ],
)
def test_the_repair_line_of_a_refused_operand_is_chosen_by_the_refusal_not_the_quoted_row(
    key, amount, row
):
    cp1 = _cp1_with_rows({key: row})
    block = forecast_block(base=_named_base(**{key: _operand(amount, row)}))
    (issue,) = _repair_issues(block, cp1)
    assert issue.endswith(OPERAND_END)
    assert (
        f"Correct the row, period, column or amount of {key}; if you cannot, state {key} " in issue
    )


def test_an_operand_refusal_quoting_the_liquidity_chart_header_gets_the_operand_line():
    chart = (
        "\n| Period | Cash | Undrawn committed facilities | Reporting unit |\n"
        "| --- | --- | --- | --- |\n| FY2025 | 100 | 50 | US$m |\n"
    )
    block = forecast_block(
        base=_named_base(undrawn=_operand("51", "FY2025", "Undrawn committed facilities"))
    )
    (issue,) = _repair_issues(block, _cp1_with_rows({}, chart))
    assert issue.endswith(OPERAND_END) and "amount of undrawn;" in issue


def test_a_facilities_refusal_keeps_the_facilities_line():
    notes = [
        {"name": "Notes", "balance": "400", "fixed_rate_pct": "6.00", "spread_pct": None,
         "floor_pct": None, "reference_rate": None, "annual_amortisation": None,
         "maturity": None}
    ]  # fmt: skip
    block = forecast_block(base=_named_base(), facilities=notes)
    (issue,) = _repair_issues(block, _cp1_with_rows({}))
    assert issue.endswith(FACILITY_END) and issue.count("Correct the facilities;") == 1


def _facility_row(name="Notes", **changes):
    return {**FACILITY_ROW, "name": name, **changes}


SCHEMA_FACILITY_FAULTS = {
    "a coupon above the cap": [_facility_row(fixed_rate_pct="35")],
    "both rate forms stated": [_facility_row(spread_pct="2.5")],
    "a maturity that is not a date": [_facility_row(maturity="2029-02-30")],
    "duplicate facility names": [_facility_row(), _facility_row("NOTES")],
    "a negative balance": [_facility_row(balance="-400")],
    "a forty-first facility": [_facility_row(f"Loan {n}") for n in range(41)],
    "four faulty rows": [_facility_row(f"Loan {n}", balance="-1") for n in range(4)],
}


@pytest.mark.parametrize("name", SCHEMA_FACILITY_FAULTS)
def test_a_schema_refusal_inside_facilities_keeps_the_facilities_line(name):
    block = forecast_block(base=_named_base(), facilities=SCHEMA_FACILITY_FAULTS[name])
    (issue,) = _repair_issues(block, _cp1_with_rows({}))
    assert "forecast inputs: " in issue, issue
    assert issue.endswith(
        "Correct the facilities; if you cannot, write `facilities` as null and keep the drivers."
    )


def test_a_facility_fault_behind_another_schema_fault_keeps_the_block_line():
    block = forecast_block(
        base=_named_base(), years=[1], facilities=[_facility_row(balance="-400")]
    )
    (issue,) = _repair_issues(block, _cp1_with_rows({}))
    assert issue.endswith(BLOCK_END)


def test_a_block_refused_for_another_reason_keeps_the_null_every_driver_line():
    (issue,) = _repair_issues(forecast_block(base=_named_base(), years=[1]), _cp1_with_rows({}))
    assert issue.endswith(BLOCK_END)


def test_a_declined_block_is_accepted_without_an_issue():
    drivers = {name: {"values": [None, None, None], "reason": "no basis"} for name in PATHS}
    block = forecast_block(base=_named_base(), base_drivers=drivers)
    assert _repair_issues(block, _cp1_with_rows({})) == ()


def test_a_row_quoting_the_declined_message_is_still_refused_with_an_issue():
    block = forecast_block(
        base=_named_base(revenue=_operand("1000", "Guidance gives no forecast drivers"))
    )
    with pytest.raises(ValueError, match="gives no forecast drivers"):
        cpos_forecast.parse(block, _cp1_with_rows({}))
    assert len(_repair_issues(block, _cp1_with_rows({}))) == 1


def test_the_not_one_number_refusal_lists_at_most_five_cells_and_the_true_count():
    tables = "\n\n".join(
        f"| T{i} | FY2025 |\n| --- | --- |\n| revenue | {1000 + i} |" for i in range(500)
    )
    doc = _cp1_doc(tables).replace("__BLOCK__", "")
    with pytest.raises(ValueError) as caught:
        _named_cp2g(doc)
    shown = [str(1000 + i) for i in range(5)]
    assert str(caught.value) == (
        "CP-2G: base revenue: row `revenue`, period `FY2025` is not one number in CP-1 "
        f"(500 cells: {shown} and 495 more)"
    )
    assert len(_repair_issues(forecast_block(base=_named_base()), doc)[0]) < 700


def test_exactly_five_cells_are_all_listed():
    tables = "\n\n".join(
        f"| T{i} | FY2025 |\n| --- | --- |\n| revenue | {1000 + i} |" for i in range(5)
    )
    doc = _cp1_doc(tables).replace("__BLOCK__", "")
    with pytest.raises(ValueError) as caught:
        _named_cp2g(doc)
    assert str(caught.value) == (
        "CP-2G: base revenue: row `revenue`, period `FY2025` is not one number in CP-1 "
        "(5 cells: ['1000', '1001', '1002', '1003', '1004'])"
    )


def test_the_cells_of_a_not_one_number_refusal_are_cut_like_every_other_quote():
    a, b = "1" * 200 + " (a)", "2" * 200 + " (b)"
    doc = _cp1_doc(
        f"| Metric | FY2025 |\n| --- | --- |\n| revenue | {a} |\n\n"
        f"| Other | FY2025 |\n| --- | --- |\n| revenue | {b} |"
    )
    with pytest.raises(ValueError) as caught:
        _named_cp2g(doc)
    assert str(caught.value) == (
        "CP-2G: base revenue: row `revenue`, period `FY2025` is not one number in CP-1 "
        f"(2 cells: {[a[:77] + '...', b[:77] + '...']})"
    )


@pytest.mark.parametrize("named", ["row", "period"])
def test_a_block_that_states_only_rows_or_only_periods_is_a_named_block_and_is_refused(named):
    # plan ruling A2: naming some operands but not all is refused; one name on every operand is
    # naming, so the operand missing its other half is the first one named in the message
    base = {k: {"amount": v, "reason": None, named: _operand(v, k)[named]} for k, v in BASE.items()}
    with pytest.raises(ValueError) as caught:
        cpos_forecast.parse(forecast_block(base=base), _cp1_doc(TWO_YEARS).replace("__BLOCK__", ""))
    assert str(caught.value) == MUST_NAME


def test_a_layer1_block_that_names_nothing_is_refused_even_when_every_amount_is_printed():
    plain = {k: {"amount": v, "reason": None} for k, v in BASE.items()}
    full = _cp1_doc(TWO_YEARS).replace("__BLOCK__", layer1_block(base=plain))
    with pytest.raises(ValueError) as caught:
        cpos_forecast.parse(full, full, "CP-1")
    assert str(caught.value) == MUST_NAME.replace("CP-2G", "CP-1", 1)


@pytest.mark.parametrize(
    ("key", "amount"), [("capex", "45"), ("wc", "-45"), ("interest", "45"), ("taxes", "45")]
)
def test_a_cell_of_more_than_38_digits_is_refused_with_a_value_error_and_sent_back(key, amount):
    long = "45." + "0" * 40 + "1"
    doc = _cp1_doc(f"| Metric | FY2025 |\n| --- | --- |\n| {key} | {long} |", key=key)
    doc = doc.replace("__BLOCK__", "")
    block = forecast_block(base=_named_base(**{key: _operand(amount, key)}))
    with pytest.raises(ValueError) as caught:  # nothing but ValueError leaves parse
        cpos_forecast.parse(block, doc)
    assert str(caught.value).startswith(
        f"CP-2G: base {key} {amount} is not CP-1's cell at row `{key}`, period `FY2025`"
    )
    assert len(_repair_issues(block, doc)) == 1


def test_a_refusal_that_mentions_base_later_in_its_text_is_not_an_operand_refusal():
    base = {k: v for k, v in _named_base().items() if k != "fcf"}
    (issue,) = _repair_issues(forecast_block(base=base), _cp1_with_rows({}))
    assert issue.endswith(BLOCK_END)


def test_both_forecast_instructions_ask_for_the_scale():
    for block, tables in (
        (cpos_launch.FORECAST_BLOCK, "CP-1's"),
        (cpos_launch.LAYER1_FORECAST_BLOCK, "your"),
    ):
        for words in (
            (
                "`currency` is the three-letter code of the currency "
                f"{tables} statement tables are printed in (`USD`, `GBP`, `EUR`), and `scale` is "
                "`1` when they print millions of it and `1000` when they print thousands"
            ),
            "so every published figure is millions of that currency",
            "Python divides by `scale`",
            "Do not convert an amount yourself",
            'a cell printing 2,620,995 is `"2620995"`',
            "at most nine digits and one decimal place",
            "only in the other unit",
            "every other driver is a ratio and is never scaled",
        ):
            assert words in block, words
        assert "ten operands in USD millions" not in block and "in millions;" not in block
    assert "`balance` is in the block's unit" in cpos_launch.FORECAST_BLOCK
    assert "`annual_amortisation` is in the block's unit, a year" in cpos_launch.FORECAST_BLOCK
    assert "USD millions a year" not in cpos_launch.FORECAST_BLOCK


def test_both_forecast_instructions_state_what_the_unit_check_enforces():
    for block in (cpos_launch.FORECAST_BLOCK, cpos_launch.LAYER1_FORECAST_BLOCK):
        assert (
            "State `currency` and `scale` in every block, as the statements print them (`1000` for "
            "thousands, `1` for millions), and state every amount in the block in that one unit "
            "exactly as printed; an amount printed in the other unit is stated as missing, with "
            "the reason, not converted." in block
        )
        assert "or absent" not in block


def test_both_forecast_instructions_say_where_a_period_header_may_be_named():
    for block in (cpos_launch.FORECAST_BLOCK, cpos_launch.LAYER1_FORECAST_BLOCK):
        assert "name a column headed by a reporting period" in block


NET_DEBT_HEADER = (
    "`| Period | Gross debt | Cash | Net debt | Reporting unit | Basis and limitation |`"
)


@pytest.mark.parametrize(
    "pathway",
    [
        *("credit_snapshot", "earnings_update", "relative_value", "covenant_refinancing"),
        *("distressed_restructuring", "portfolio_decision", "short_snapshot"),
        "lite_credit_assessment",
    ],
)
def test_every_pathway_asks_cp1_for_the_net_debt_table_and_states_every_rule_the_checker_holds(
    tmp_path, pathway
):
    """Owner, 2026-11-12, "Yes, add it": gross debt in a fixed-label place for CP-8's pack."""
    prepared, task, context = good_task(tmp_path, "CP-1", pathway)
    text = (tmp_path / "out" / prepared.plan.instructions["CP-1"].path).read_text()
    assert text.count("`### Net debt data`") == 1
    assert NET_DEBT_HEADER in text
    assert "total debt principal as the issuer reports it" not in text
    for stated in (
        "Gross debt is total debt at balance-sheet carrying value (current plus long-term",
        "net of issuance costs and discounts), not principal",
        (
            "what gross debt includes (for example securitization and finance leases the issuer "
            "carries within its debt lines) and states the principal total"
        ),
        "beside it. Cash is",
        "the same figure as the Cash column of the `Chart data: liquidity` table",
        "Net debt is gross debt less cash, worked with `calculate`",
        "is refused if net debt differs from gross debt less cash by any amount",
        "refused if its cash differs from the liquidity table's for the same period",
        "`## Calculations`",
        "Not supplied: <reason>",
    ):
        assert stated in text, stated
    raw = answer(context, list(prepared.plan.layout.routes))
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()
    cut = raw.replace("### Net debt data", "### Dropped")
    issues = _checked_handoff(task, cut.encode(), checker(prepared.layout))
    assert any("Net debt data" in issue for issue in issues), issues


@pytest.mark.parametrize(
    ("old", "new", "complaint"),
    [
        # 1500 - 300 = 1200: a net debt of 1199 is refused, naming the row.
        ("| FY2023 | 1500 | 300 | 1200 |", "| FY2023 | 1500 | 300 | 1199 |", "FY2023"),
        # Cash that differs from the liquidity table's 275 for FY2024 is refused.
        ("| FY2024 | 1400 | 275 | 1125 |", "| FY2024 | 1400 | 270 | 1130 |", "liquidity"),
        # `same_period` calls FY2024 and FY2024 / 2024-09-30 one period: the 270 is still refused.
        (
            "| FY2024 | 1400 | 275 | 1125 |",
            "| FY2024 / 2024-09-30 | 1400 | 270 | 1130 |",
            "liquidity",
        ),
        ("| Gross debt | Cash |", "| Total debt | Cash |", "Net debt data"),
        ("| 1500 | 300 | 1200 | US$m |", "| 1500 | 300 | 1200 | EUR m |", "EUR m"),
        ("| 1400 | 275 | 1125 |", "| 1,400.5 | 275 | 1125 |", "FY2024"),
    ],
)
def test_checker_refuses_each_broken_net_debt_table(tmp_path, old, new, complaint):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new).encode(), checker(prepared.layout))
    assert any(complaint in issue for issue in issues), issues


def test_a_net_debt_row_with_a_stated_gap_is_accepted_in_the_form_the_rule_allows(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    gap = "Not supplied: the debt note was not read"
    reg = "| n / d | {} | annual.txt | {} | annual.txt | FY{} | USD | US$m | {} |"
    # Ties are two-sided (R1): a gap in the net debt table needs its balance-sheet line, the
    # register row worked from it and the chart figure beside it to be gaps too.
    for old, new in (
        ("| FY2023 | 1500 | 300 | 1200 |", f"| FY2023 | {gap} | 300 | {gap} |"),
        ("| FY2024 | 1400 | 275 | 1125 |", f"| FY2024 | 1400 | {gap} | {gap} |"),
        ("| Total Debt | 1500 | 1400 |", f"| Total Debt | {gap} | 1400 |"),
        ("| Cash & Equivalents | 300 | 275 |", f"| Cash & Equivalents | 300 | {gap} |"),
        (reg.format(1500, 400, 2023, "3.75"), reg.format(gap, 400, 2023, gap)),
        (reg.format(1200, 400, 2023, "3.00"), reg.format(gap, 400, 2023, gap)),
        (reg.format(1125, 500, 2024, "2.25"), reg.format(gap, 500, 2024, gap)),
        ("| FY2023 | 3.75 | 3.00 | x |", f"| FY2023 | {gap} | {gap} | x |"),
        ("| FY2024 | 2.80 | 2.25 | x |", f"| FY2024 | 2.80 | {gap} | x |"),
    ):
        assert old in raw
        raw = raw.replace(old, new)
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()


POST_BS_HEADING = "### Post-balance-sheet adjustments"
POST_BS_SENTENCE = "state the pro forma figure beside it"


@pytest.mark.parametrize(
    "pathway",
    [
        *("credit_snapshot", "earnings_update", "relative_value", "covenant_refinancing"),
        *("distressed_restructuring", "portfolio_decision", "short_snapshot"),
        "lite_credit_assessment",
    ],
)
def test_cp1_is_asked_for_the_post_balance_sheet_table_and_others_for_the_pro_forma_sentence(
    tmp_path, pathway
):
    """Decision 10 of 2026-11-12: the table is CP-1's; a module quoting year-end figures states
    the pro forma figure beside them; the chart and net debt table rules are unchanged."""
    prepared, _task, _context = good_task(tmp_path, "CP-1", pathway)
    text = (tmp_path / "out" / prepared.plan.instructions["CP-1"].path).read_text()
    assert text.count(f"`{POST_BS_HEADING}`") == 1
    assert f"`{POST_BS_HEADER}`" in text
    assert "None found in the sources read" in text
    assert text.index(POST_BS_HEADING) < text.index(cpos_launch.METHOD_MARK)
    assert NET_DEBT_HEADER in text  # the net debt table rule is unchanged
    assert "Pro forma" not in text.split("`### Net debt data`")[1].split("`### ")[0]
    for heading, columns, _unit in cpos_launch.CHART_TABLES.values():
        assert "Pro forma" not in " ".join(columns), heading
    assert not POST_BS_HEADING.startswith("### Chart data:")
    others = [m for m in prepared.plan.instructions if m != "CP-1"]
    assert others
    for module in others:  # every other module carries the sentence and is not asked for the table
        sent = (tmp_path / "out" / prepared.plan.instructions[module].path).read_text()
        assert POST_BS_SENTENCE in sent, module
        assert POST_BS_HEADING not in sent, module
    assert POST_BS_SENTENCE in text


def test_cp1_handoff_without_the_post_balance_sheet_section_is_refused_naming_it(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    cut = raw.replace(POST_BS_HEADING, "### Dropped")
    issues = _checked_handoff(task, cut.encode(), checker(prepared.layout))
    assert any("Post-balance-sheet adjustments" in issue for issue in issues), issues


@pytest.mark.parametrize(
    ("old", "new", "complaint"),
    [
        ("| Event | Date |", "| Item | Date |", "Post-balance-sheet adjustments"),
        ("| Pro forma net debt |", "| Net debt |", "Post-balance-sheet adjustments"),
        ("| Amount | Pro forma", "| Pro forma", "Post-balance-sheet adjustments"),
    ],
)
def test_checker_refuses_post_balance_sheet_table_with_wrong_columns(tmp_path, old, new, complaint):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new, 1).encode(), checker(prepared.layout))
    assert any(complaint in issue for issue in issues), issues


def test_post_balance_sheet_table_accepts_one_event_row_and_refuses_a_malformed_one(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    event = raw.replace(POST_BS_NONE, POST_BS_EVENT)
    assert event != raw
    assert _checked_handoff(task, event.encode(), checker(prepared.layout)) == ()
    bad_date = event.replace("2024-11-05", "5 November 2024")
    issues = _checked_handoff(task, bad_date.encode(), checker(prepared.layout))
    assert any("Date" in i and "YYYY-MM-DD" in i for i in issues), issues
    bad_number = event.replace("| 1625 |", "| about 1,600m |")
    issues = _checked_handoff(task, bad_number.encode(), checker(prepared.layout))
    assert any("Pro forma net debt" in i for i in issues), issues


PARTIAL_DATE_GAP = "Not supplied: the source states February 2025 only"


def test_post_balance_sheet_instructions_state_the_date_form_and_the_pro_forma_gap_sentence(
    tmp_path,
):
    """A source that gives only a month or quarter must not push the model to invent a day."""
    prepared, _task, _context = good_task(tmp_path, "CP-1", "credit_snapshot")
    text = (tmp_path / "out" / prepared.plan.instructions["CP-1"].path).read_text()
    assert "YYYY-MM-DD only when the source states the day" in text
    assert "Not supplied: the source states <what it gives> only" in text
    assert "month, quarter or year" in text
    assert "<month or quarter>" not in text
    assert "is unavailable; do not block the module for it" in text
    assert "is unavailable, and do not block the module for it" not in text
    assert "When Financial foundation does not state the pro forma figure" in text


def test_the_reader_layer_says_registers_are_tables_and_their_content_exact():
    passages = cpos_launch.PROSE_PASSAGES
    assert "registers are written as tables, and all of its content is exact" in passages
    assert "unchanged and exact" not in passages


def test_post_balance_sheet_partial_date_refusal_names_the_not_supplied_form(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    event = raw.replace(POST_BS_NONE, POST_BS_EVENT)
    partial = event.replace("2024-11-05", "February 2025")
    issues = _checked_handoff(task, partial.encode(), checker(prepared.layout))
    assert any(
        "Date" in i and "Not supplied: the source states <what it gives> only" in i for i in issues
    ), issues
    stated = event.replace("2024-11-05", PARTIAL_DATE_GAP)
    assert _checked_handoff(task, stated.encode(), checker(prepared.layout)) == ()


def test_post_balance_sheet_none_row_needs_its_unit_and_basis(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    blank = raw.replace(
        "| US$m | Synthetic; the annual report and its notes were read. |", "|  |  |"
    )
    issues = _checked_handoff(task, blank.encode(), checker(prepared.layout))
    assert any("Post-balance-sheet adjustments" in i for i in issues), issues


# ---- Task C3 (2026-11-12, decision 9): the confidence score is computed from a table of inputs.
CONFIDENCE_TEXT = f"### Confidence inputs\n\n| Input | Value |\n| --- | --- |\n{CONFIDENCE_ROWS}\n"


def confidence_spec(module: str):
    return next(t for t in cpos_launch.OWNER_TABLES[module] if t.heading == "Confidence inputs")


def test_the_modules_whose_method_carries_the_score_are_the_ones_asked_for_the_table():
    carrying = {m for m, paths in cpos_launch.METHODS.items() if cpos_launch._SCORE in paths}
    assert carrying == set(SCORED)
    for module in SCORED:
        assert confidence_spec(module)
    for module in UNSCORED:
        assert all(
            t.heading != "Confidence inputs" for t in cpos_launch.OWNER_TABLES.get(module, ())
        )


def test_the_table_is_asked_in_one_sentence_of_the_shared_text_and_only_of_scored_modules(tmp_path):
    _, texts = all_instructions(tmp_path, modules=tuple(m for m in METHODS if m != "CP-8"))
    for module in SCORED:
        head = texts[module].partition(cpos_launch.METHOD_MARK)[0]
        assert "`### Confidence inputs`" in head, module
        assert "computed from it" in head and "not sentence text" in head, module
        assert "| Input | Value |" in head and "Source gate" in head, module
    for module in set(UNSCORED) & set(texts):  # CP-8 is planned by CP-OS, not selected.
        head = texts[module].partition(cpos_launch.METHOD_MARK)[0]
        assert "Confidence inputs" not in head, module
    # The existing rule that a module states no score still stands, for every module.
    assert all("Do not state a confidence score" in t for t in texts.values())


def test_a_scoring_modules_draft_without_a_well_formed_table_is_refused():
    spec = confidence_spec("CP-2D")
    assert cpos_launch.chart_issues(CONFIDENCE_TEXT, spec) == ()
    assert cpos_launch.chart_issues("### Other\n\ntext\n", spec) == (
        "Add `### Confidence inputs` inside ## Findings, with its table.",
    )
    no_gate = CONFIDENCE_TEXT.replace("| Source gate | pass |\n", "")
    assert any("Source gate" in i for i in cpos_launch.chart_issues(no_gate, spec))
    word = CONFIDENCE_TEXT.replace("| Calculated | 2 |", "| Calculated | two |")
    assert any("Calculated" in i for i in cpos_launch.chart_issues(word, spec))
    zero = CONFIDENCE_TEXT.replace("| Fields total | 100 |", "| Fields total | 0 |")
    assert any("Fields total" in i for i in cpos_launch.chart_issues(zero, spec))
    other = CONFIDENCE_TEXT.replace("| Input | Value |", "| Name | Amount |")
    assert any("Input | Value" in i for i in cpos_launch.chart_issues(other, spec))
    score = CONFIDENCE_TEXT.replace("| MINOR | 1 |", "| MINOR | 1 |\n| Score | 89 |")
    assert any("Score" in i for i in cpos_launch.chart_issues(score, spec))


# ---- Whole-branch wave (H2): a blocked scoring module obeys the blocked rule and is accepted.
BLOCKED_BOTTOM = "## Findings\n\n### Bottom line\n\nNot assessable: no source file was read.\n\n"
ONE_ROW = (
    "### Confidence inputs\n\n| Input | Value |\n| --- | --- |\n"
    "| Not assessable | Not supplied: blocked |\n"
)


def test_a_blocked_scoring_module_writes_one_not_assessable_row_and_is_accepted():
    spec = confidence_spec("CP-2D")
    assert cpos_launch.chart_issues(BLOCKED_BOTTOM + ONE_ROW, spec) == ()
    assert cpos_launch.chart_issues(BLOCKED_BOTTOM + CONFIDENCE_TEXT, spec) == ()


def test_a_module_that_is_not_blocked_is_refused_for_the_not_assessable_row():
    spec = confidence_spec("CP-2D")
    text = "## Findings\n\n### Bottom line\n\nThe view is stable.\n\n" + ONE_ROW
    (issue,) = cpos_launch.chart_issues(text, spec)
    assert "Not assessable" in issue and "not an input" in issue


def test_the_confidence_text_says_what_a_blocked_module_writes_before_the_method(tmp_path):
    _, texts = all_instructions(tmp_path, modules=("CP-3",))
    head = texts["CP-3"].partition(cpos_launch.METHOD_MARK)[0]
    assert (
        "A blocked module writes one row in it instead, `| Not assessable | Not supplied: "
        "<reason> |`, and no score is computed." in head
    )


# ---- Whole-branch wave (L7): a front-matter score, band or QA status the module states itself.
@pytest.mark.parametrize(
    "key", ["confidence_score: 62", "confidence_band: Medium", "qa_status: Passed"]
)
def test_a_front_matter_score_band_or_qa_status_is_refused(tmp_path, key):
    front = f"---\nissuer_id: nbg\nmodule_id: CP-4\n{key}\n---\n\n"
    issues = prose_issues_of(tmp_path, "CP-4", lambda raw: front + raw)
    name = key.split(":")[0]
    assert any(name in i and "front matter" in i for i in issues), issues


def test_front_matter_without_those_keys_and_the_words_in_body_text_are_not_refused(tmp_path):
    front = "---\nissuer_id: nbg\nmodule_id: CP-4\n---\n\n"
    body = "\n\nThe qa_status: value is not stated.\n"
    issues = prose_issues_of(tmp_path, "CP-4", lambda raw: front + raw + body)
    assert not any("front matter" in i for i in issues), issues


# ---- Whole-branch wave (L4): wording gaps in the shared and per-table text.
def test_a_near_miss_none_row_is_refused_naming_the_exact_text(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert POST_BS_NONE in raw
    for near in ("None found in the sources read.", "none found in the sources read"):
        text = raw.replace("| None found in the sources read |", f"| {near} |")
        assert text != raw
        issues = _checked_handoff(task, text.encode(), checker(prepared.layout))
        assert any("exactly `None found in the sources read`" in i for i in issues), (near, issues)


def test_the_none_rule_names_the_tables_own_columns_and_the_sign_of_amount_is_stated(tmp_path):
    spec = cpos_launch.POST_BS
    rule = cpos_launch._none_rule(spec)
    assert "whose Date, Amount, Pro forma net debt and Pro forma net leverage are each" in rule
    assert "exactly `None found in the sources read` (no other punctuation or wording)" in rule
    assert cpos_launch._and_list(("A", "B", "C")) == "A, B and C"
    assert "without a sign when net debt rises and with a minus sign when it falls" in spec.rules
    assert "cash effect" not in spec.rules
    assert "net debt, net leverage or cash from Financial foundation" in cpos_launch.VOICE_RULES


def test_the_shared_text_names_no_confidence_script_and_separates_the_score_from_claim_labels(
    tmp_path,
):
    _, texts = all_instructions(tmp_path, modules=("CP-3",))
    head = texts["CP-3"].partition(cpos_launch.METHOD_MARK)[0]
    assert "confidence_score.py" not in head
    assert "Python computes any score and band the report shows" in head
    assert "a claim's own confidence label" in head
    assert (
        "list each issuer source it relied on in `## Sources`, naming the exact file and its "
        "sha256;" in head
    )
    assert "as a table with the columns `Source | Document | Document date | sha256 | Use`" in head
    assert "rejected unless it does all of this" in head


# --- Task E4 (2026-11-12 findings 1, 2, 4): the sent texts name `column` and `interest`
S5_SENTENCE = (
    "Name the cell of every operand that has an amount by `row` and `period` and nothing else. "
    "Take a balance from a row under a period column (`FY2024`, `H1 2025`), never from a column "
    "headed `LTM …` and never from a table with one row per period"
)
S5_TAIL = "where CP-1 prints the balance only there, state the operand as missing with that reason."
S5_TAIL_LAYER1 = (
    "where you print the balance only there, state the operand as missing with that reason."
)
INTEREST_SENTENCE = (
    "`interest` is interest paid in cash in the base period; where CP-1 prints only interest "
    "expense you may name that cell and must say in `scope_limits` that interest is interest "
    "expense, not cash paid."
)
BALANCE_SENTENCE = (
    "Print every balance the forecast needs (total debt, cash, undrawn committed facilities) as "
    "a row of a table whose columns are those period headers, each a plain number at that "
    "period's end: the `H1 2025` column holds the 30 June 2025 balance. Put the date in the row "
    "label or the Source, not in the cell. A column headed `LTM …` holds flows only, never a "
    "balance."
)


def _built_instruction(tmp_path, module, modules):
    prepared = prepare(
        context_file(tmp_path, "covenant_refinancing"),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
        modules=modules,
    )
    return (tmp_path / "out" / prepared.plan.instructions[module].path).read_text()


def test_the_cp2g_instruction_sent_states_row_and_period_only_and_what_interest_is(tmp_path):
    text = _built_instruction(tmp_path, "CP-2G", ("CP-1", "CP-2G"))
    assert S5_SENTENCE in text and S5_TAIL in text and INTEREST_SENTENCE in text
    assert '`"column": "Cash"' not in text and "leave out `period` there" not in text


def test_the_layer1_forecast_instruction_sent_states_row_and_period_only_and_what_interest_is(
    tmp_path,
):
    text = _built_instruction(tmp_path, "CP-1", ("CP-1", "CP-MODEL"))
    assert S5_SENTENCE in text and S5_TAIL_LAYER1 in text and INTEREST_SENTENCE in text
    assert '`"column": "Cash"' not in text and "leave out `period` there" not in text


def test_the_period_table_instruction_sent_says_how_to_print_a_balance(tmp_path):
    for modules in (("CP-1", "CP-2G"), ("CP-1", "CP-MODEL")):
        (tmp_path / modules[1]).mkdir()
        text = _built_instruction(tmp_path / modules[1], "CP-1", modules)
        assert BALANCE_SENTENCE in text


COLUMN_CP1 = (
    "| Base | FY2025 |\n| --- | --- |\n"
    + "\n".join(f"| {k} | {printed(k, v)} |" for k, v in BASE.items() if k != "cash")
    + "\n\n| Period | Cash |\n| --- | --- |\n| FY2025 | 100 |\n"
)


def test_a_column_refusal_gets_the_row_period_column_or_amount_repair_line():
    base = _named_base(cash={"amount": "101", "reason": None, "row": "FY2025", "column": "Cash"})
    (issue,) = _repair_issues(forecast_block(base=base), COLUMN_CP1)
    assert "column `Cash`" in issue
    assert "Correct the row, period, column or amount of cash; if you cannot, state cash " in issue
    assert issue.endswith("as missing: amount null, no row, period or column, and the reason.")


def test_an_operand_naming_both_period_and_column_gets_its_own_repair_line():
    both = _operand("100", "FY2025", "FY2025") | {"column": "Cash"}
    (issue,) = _repair_issues(forecast_block(base=_named_base(cash=both)), COLUMN_CP1)
    assert issue.endswith("State either `period` or `column` for cash, not both.")
    assert "set every driver" not in issue


def test_several_operands_naming_both_period_and_column_are_all_named_in_the_repair_line():
    both = _operand("100", "FY2025", "FY2025") | {"column": "Cash"}
    base = _named_base(
        cash=both, undrawn=_operand("50", "FY2025", "FY2025") | {"column": "Undrawn"}
    )
    (issue,) = _repair_issues(forecast_block(base=base), COLUMN_CP1)
    assert issue.endswith("State either `period` or `column` for cash and undrawn, not both.")


def test_the_forecast_instruction_sentences_say_what_python_does():  # whole-branch review L3, L4
    table = cpos_launch.PERIOD_TABLE_BLOCK
    assert "check that the last twelve months are twelve months; add no figure to it." in table
    assert "LTM Qn YYYY" not in table and "to date a balance" not in table
    assert "only to check" not in table and "change no other table" not in table
    shown = "history only for a line named under such a header."
    for block in (cpos_launch.FORECAST_BLOCK, cpos_launch.LAYER1_FORECAST_BLOCK):
        assert shown in block
        assert "Those tables are in US$ million" not in block
        assert "`row` and `column`" not in block
    assert "(your `Chart data:` tables and `Net debt data`)" in cpos_launch.LAYER1_FORECAST_BLOCK
    assert "(CP-1's `Chart data:` tables" in cpos_launch.FORECAST_BLOCK


APPENDIX_RULE = (
    "Place all complete canonical registers below\n"
    "`### Analytical appendix — complete canonical registers` inside\n"
    "`## Analysis`."
)


def test_prose_modules_are_sent_the_canon_analytical_appendix_rule_data_modules_not(tmp_path):
    """The reader-layer canon section stops at the next `####` heading, so the appendix rule that
    PROSE_PASSAGES says "still applies" was cut off and never sent (Task 6, item 1)."""
    for module, text in all_texts(tmp_path).items():
        method = text.partition(cpos_launch.METHOD_MARK)[2]
        assert (APPENDIX_RULE in method) == (module not in DATA_MODULE_IDS), module
        if module not in DATA_MODULE_IDS:
            assert "#### Analytical appendix\n" in method, module


APPENDIX_HEADING_NOTE = (
    "Where the canon's Analytical appendix section says `## Analysis`, this handoff's section is "
    "`## Findings`: write the appendix heading as a `###` heading there, after `### Limitations`; "
    "the other required `###` headings stay `###` and are not nested under it.\n\n"
)


def test_the_appendix_heading_note_goes_with_the_appendix_section_only(tmp_path):
    for module, text in all_texts(tmp_path).items():
        head = text.partition(cpos_launch.METHOD_MARK)[0]
        sent = CANON_APPENDIX_SECTION in METHODS[module]
        assert (APPENDIX_HEADING_NOTE in head) == sent == (module not in DATA_MODULE_IDS), module
        assert APPENDIX_HEADING_NOTE not in text.partition(cpos_launch.METHOD_MARK)[2], module


TABLE_ID = r"T2[A-Z]*\.[0-9]+"
OLD_CP2A_STALE = ("no r14 CP-2A text exists in the repo", "computed in Python")


def cp2a_table_definitions(tmp_path) -> list[str]:
    """Each table ID the sent CP-2A texts define: a bold `**ID Name:**` heading (the step files)
    or an `ID name` item of a `## Tables` list line (the short stress text)."""
    # "/cp2a.md" is the structured runtime's copy, whose T2B.n collide with the step file's: it
    # must not come back.
    sections = {
        name: text
        for name, text in cpos_launch.method_sections("CP-2A")
        if name.endswith(".md") and ("downside-pathway" in name or name.endswith("/cp2a.md"))
    }
    defined = []
    for text in sections.values():
        defined += re.findall(rf"^\*\*({TABLE_ID}) ", text, re.MULTILINE)
        for line in re.findall(r"^## Tables\n(.*)$", text, re.MULTILINE):
            defined += re.findall(rf"(?:^|, )({TABLE_ID}) [a-z]", line)
    return defined


def test_the_cp2a_instruction_defines_each_table_id_once(tmp_path):
    defined = cp2a_table_definitions(tmp_path)
    assert [i for i, n in Counter(defined).items() if n > 1] == []
    assert {f"T2B.{n}" for n in range(1, 10)} <= set(defined)  # the step file's nine
    assert {f"T2DS.{n}" for n in range(1, 10)} <= set(defined)  # the short text's nine


def test_the_cp2a_instruction_no_longer_carries_the_short_texts_stale_statements():
    assert "cp2a.md" not in [n.rsplit("/", 1)[-1] for n, _ in cpos_launch.method_sections("CP-2A")]
    text = cpos_launch.method_text("CP-2A")
    for stale in OLD_CP2A_STALE:
        assert stale not in text


def _appendix_handoff_issues(tmp_path, as_h2: bool):
    """The answer with a register under the canon's appendix heading: as a `###` heading after
    `### Limitations` (what the note tells the model), or as the `## Analysis` H2 the canon says."""
    prepared, task, context = good_task(tmp_path, "CP-2")
    raw = answer(context, list(prepared.plan.layout.routes))
    findings, calc = raw.split("\n## Calculations", 1)
    calc = "\n## Calculations" + calc
    register = (
        "### Analytical appendix — complete canonical registers\n\n"
        "| Register row | Value | Source |\n| --- | --- | --- |\n| Observed | 1 | annual.txt |\n\n"
    )
    if as_h2:
        raw = findings + "\n## Analysis\n\n" + register + calc
    else:
        head, rest = findings.split("### Limitations", 1)
        limitations, sep, tail = rest.partition("\n### ")
        raw = head + "### Limitations" + limitations + "\n" + register + (sep + tail).lstrip("\n")
        raw += calc
    return _checked_handoff(task, raw.encode(), checker(prepared.layout))


def test_the_appendix_as_a_findings_h3_is_accepted_and_as_an_analysis_h2_is_refused(tmp_path):
    """Review probe t6a: the note's reading of the canon passes CP-OS's checks; the canon's own
    `## Analysis` does not (no earlier test exercised either)."""
    (tmp_path / "h3").mkdir()
    (tmp_path / "h2").mkdir()
    assert _appendix_handoff_issues(tmp_path / "h3", as_h2=False) == ()
    issues = _appendix_handoff_issues(tmp_path / "h2", as_h2=True)
    assert issues and "exactly these six H2 headings" in issues[0]


NET_DEBT_PERIOD_SENTENCE = (
    "`Period` is `FY2024 / 2024-09-30` for a fiscal year end (fiscal year, space, slash, space, "
    "the year-end date) and the date alone (`2025-06-30`) for an interim balance sheet: one form "
    "for every row of the table, each period once, and no other word in the cell"
)
UNIT_FORM_SENTENCE = (
    "Where a table states its unit, write it as the three-letter currency code and `millions` or "
    "`thousands` (`USD millions`), the same in every statement table; the `Chart data:` tables "
    "and `Net debt data` keep the unit their own rule gives."
)


def test_the_sent_instructions_prescribe_one_net_debt_period_form_and_the_unit_exemption(tmp_path):
    text = _built_instruction(tmp_path, "CP-1", ("CP-1", "CP-MODEL"))
    assert NET_DEBT_PERIOD_SENTENCE in text and UNIT_FORM_SENTENCE in text
    assert "the balance-sheet date `2024-09-30`, or both as" not in text
    assert "the same in every statement table. Python uses" not in text


def test_the_sent_forecast_instructions_offer_history_only_under_a_period_header_and_say_you(
    tmp_path,
):
    for module, modules in (("CP-2G", ("CP-1", "CP-2G")), ("CP-1", ("CP-1", "CP-MODEL"))):
        (tmp_path / module).mkdir(exist_ok=True)
        text = _built_instruction(tmp_path / module, module, modules)
        assert "history only for a line named under such a header." in text
        assert "labelled with one" not in text
    assert "where you print the balance only there" in text
    assert "where CP-1 prints the balance only there" not in text


def test_cp1_is_told_the_net_debt_period_forms_and_to_print_each_line_once():
    assert NET_DEBT_PERIOD_SENTENCE in cpos_launch.NET_DEBT.rules
    assert "and no other word in the cell (say `pro forma` or `reported` in the Basis" in (
        cpos_launch.NET_DEBT.rules
    )
    text = cpos_launch.PERIOD_TABLE_BLOCK
    assert "Print each statement line once, in one table that has a column for every period" in text
    assert "a line split across two tables cannot be combined" in text
    assert UNIT_FORM_SENTENCE in text


# --- the Net debt data Period is one the pack can order (F1, defect D2.1) -----------------------
def _net_debt_text(*periods):
    rows = "\n".join(f"| {p} | 1400 | 275 | 1125 | US$m | Synthetic. |" for p in periods)
    return (
        "### Net debt data\n\n"
        "| Period | Gross debt | Cash | Net debt | Reporting unit | Basis and limitation |\n"
        "| --- | --- | --- | --- | --- | --- |\n" + rows + "\n"
    )


@pytest.mark.parametrize("period", ["FY2024", "2024-09-30", "FY2024 / 2024-09-30"])
def test_each_stated_form_of_the_net_debt_period_is_accepted(period):
    assert cpos_launch._net_debt_issues(_net_debt_text(period)) == ()


@pytest.mark.parametrize(
    ("periods", "cell"),
    [
        (("2024-09-30 reported",), "2024-09-30 reported"),
        (("FY2024 (2024-09-30)",), "FY2024 (2024-09-30)"),
        (("2024-02-31",), "2024-02-31"),
        (("FY2024", "2025-06-30"), "2025-06-30"),
        (("FY2024", "FY2024"), "FY2024"),
    ],
)
def test_a_net_debt_period_the_pack_cannot_order_is_refused_with_the_form_to_write(periods, cell):
    (issue,) = cpos_launch._net_debt_issues(_net_debt_text(*periods))
    assert issue == (
        f"`### Net debt data` Period `{cell}` cannot be ordered: write "
        "`FY2024 / 2024-09-30` for a fiscal year end or the date alone (`2025-06-30`) for an "
        "interim balance sheet, one form for the whole table and each period once; put any "
        "other word in the Basis and limitation cell."
    )


# ---------------------------------------------------------------- compaction (T3)
#
# The compaction is the real CP-8 one of run tdg-full-copilot-sol-high-001-resume (tests/model/
# _compaction.py): 259,070 tokens before, a charge of 9,963,810,000 nano-AIU x 1E-11 = USD
# 0.0996381.
# Each fake module call is 10 input and 5 output tokens on sol-medium: (10 x 2.00 + 5 x 10.00) / 1M
# = USD 0.00007.

COMPACTED = Compaction(
    kind="complete",
    attempt_id="9adc3933-fffb-4810-a23a-717e91c08200",
    tokens_before=259070,
    tokens_after=42447,
    token_limit=272000,
    success=True,
    usd=Decimal("0.0996381"),
)
COMPACTING = Compaction(kind="start", attempt_id="9adc3933", tokens_before=241349)
REVIEW_CP4 = (
    "Review: CP-4 was written after GitHub Copilot summarised its context (259,070 tokens before); "
    "check its figures against the earlier modules."
)


def charged_line(out: str) -> Decimal:
    (line,) = [n for n in out.splitlines() if n.startswith("Charged:")]
    return Decimal(line.split("USD")[1])


def compacting_run(tmp_path, provider, *found):
    argv = launch(tmp_path, "--modules", "CP-4", "--live", "--ruling", str(RULING))
    routes = prepare_routes(tmp_path, "sol-medium")
    provider.answer = lambda context: answer(context, routes)
    provider.compactions = {"CP-4": found}
    return argv


def accepted_events(tmp_path):
    events = read_events(tmp_path / "out" / "events.jsonl")
    return {e["module"]: e for e in events if e["event"] == "module_accepted"}


def test_a_module_written_after_a_compaction_is_flagged_charged_and_listed(
    tmp_path, provider, capsys
):
    argv = compacting_run(tmp_path, provider, COMPACTING, COMPACTED)
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert out.count("Review:") == 1 and REVIEW_CP4 in out
    accepted = accepted_events(tmp_path)
    assert accepted["CP-4"]["written_after_compaction"] is True
    assert accepted["CP-4"]["compaction_tokens_before"] == 259070
    assert all("written_after_compaction" not in e for m, e in accepted.items() if m != "CP-4")
    # every call 0.00007, and the compaction once: the run's reported charge includes it
    assert charged_line(out) == Decimal("0.00007") * len(provider.calls) + Decimal("0.0996381")
    notes = list((tmp_path / "out/requests/CP-4").glob("*/*.compaction.json"))
    assert len(notes) == 1 and json.loads(notes[0].read_text())["tokens_before"] == 259070


def test_a_resumed_module_keeps_its_flag_and_its_charge_is_not_settled_twice(
    tmp_path, provider, capsys
):
    argv = compacting_run(tmp_path, provider, COMPACTING, COMPACTED)
    assert main(argv) == 0
    first = capsys.readouterr().out
    calls, spent = len(provider.calls), charged_line(first)
    ledger = sorted(p.name for p in (tmp_path / "out/live/owner-run-audit/reservations").iterdir())
    # the second launch resumes: every response is retained, so no call is made
    provider.answer = lambda context: pytest.fail("a retained module was sent again")
    assert main(argv) == 0
    second = capsys.readouterr().out
    assert len(provider.calls) == calls
    assert charged_line(second) == spent
    assert REVIEW_CP4 in second and second.count("Review:") == 1
    assert accepted_events(tmp_path)["CP-4"]["written_after_compaction"] is True
    assert ledger == sorted(
        p.name for p in (tmp_path / "out/live/owner-run-audit/reservations").iterdir()
    )


def test_a_compaction_that_only_started_is_recorded_but_flags_nothing(tmp_path, provider, capsys):
    argv = compacting_run(tmp_path, provider, COMPACTING)
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert "Review:" not in out
    assert all("written_after_compaction" not in e for e in accepted_events(tmp_path).values())
    names = [e["event"] for e in read_events(tmp_path / "out/events.jsonl")]
    assert "context_compaction_started" in names and "context_compacted" not in names
    assert not list((tmp_path / "out/requests").glob("*/*/*.compaction.json"))
    assert charged_line(out) == Decimal("0.00007") * len(provider.calls)


def test_a_run_without_any_compaction_prints_no_review_line(tmp_path, provider, capsys):
    argv = compacting_run(tmp_path, provider)
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert "Review:" not in out and "Context:" not in out
    assert all("written_after_compaction" not in e for e in accepted_events(tmp_path).values())


def test_an_unreadable_compaction_note_still_flags_the_module(tmp_path, provider, capsys):
    argv = compacting_run(tmp_path, provider, COMPACTED)
    assert main(argv) == 0
    (note,) = (tmp_path / "out/requests/CP-4").glob("*/*.compaction.json")
    note.write_text("{not json")
    capsys.readouterr()
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert "Review: CP-4 was written after GitHub Copilot summarised its context;" in out


def test_a_stopped_run_still_lists_the_modules_written_after_a_compaction(
    tmp_path, provider, capsys
):
    """CP-0 is accepted after a compaction; CP-4 is then rejected and the run stops."""
    argv = compacting_run(tmp_path, provider)
    answers = provider.answer
    provider.answer = lambda context: (
        "## Request\n\nNot a handoff." if context["module_id"] == "CP-4" else answers(context)
    )
    provider.compactions = {"CP-0": (COMPACTED,)}
    assert main(argv) == 1
    err = capsys.readouterr().err
    assert err.startswith("Stopped:") and "Review: CP-0 was written after" in err
    assert "Review: CP-4" not in err


def copilot_readiness(tmp_path, monkeypatch, limit):
    from deploy_workflow.model import copilot

    monkeypatch.setattr(copilot, "TOKEN_LIMITS", {"gpt-6.1-sol": limit})
    prepared = prepare(
        context_file(tmp_path), issuer_folder(tmp_path), tmp_path / "out",
        config="copilot-sol-medium", cap="50",
    )  # fmt: skip
    return prepared, cpos_launch._readiness(prepared, "copilot-sol-medium")


def test_readiness_warns_for_each_module_whose_first_prompt_nears_the_copilot_limit(
    tmp_path, monkeypatch
):
    # A limit of 60,000 tokens (80% = 48,000) with the 32,000-token output budget: a module warns
    # when its estimated prompt passes 16,000 tokens. The estimate by hand: the instruction file's
    # bytes + 16,384 (the request's fixed part), over 3.85 bytes per token, rounded up.
    prepared, text = copilot_readiness(tmp_path, monkeypatch, 60_000)
    warned = {}
    for module in prepared.ordered:
        size = (prepared.directory / "instructions" / f"{module}.md").stat().st_size
        tokens = -(-(size + 16384) * 100 // 385)
        warned[module] = tokens
    lines = [n for n in text.splitlines() if n.startswith("Context:  CP-")]
    expected = [m for m, t in warned.items() if t + 32000 > 0.8 * 60_000]
    assert expected  # the instructions alone are enough for some module to warn
    assert [n.split(":")[1].strip() for n in lines] == expected
    for line in lines:
        module = line.split(":")[1].strip()
        assert f"first prompt about {warned[module]:,} tokens (" in line
        assert "over 80% of the 60,000-token limit" in line
    # the handoffs of earlier modules are not written yet: the report says so
    assert "handoffs not written yet are not counted" in text


def test_readiness_is_silent_when_every_first_prompt_is_well_inside_the_limit(
    tmp_path, monkeypatch
):
    _, text = copilot_readiness(tmp_path, monkeypatch, 272_000)
    assert "Context:  CP-" not in text


def test_readiness_has_no_context_lines_off_the_copilot_route(tmp_path):
    prepared = prepare(
        context_file(tmp_path), issuer_folder(tmp_path), tmp_path / "out",
        config="sol-medium", cap="50",
    )  # fmt: skip
    assert "Context:" not in cpos_launch._readiness(prepared, "sol-medium")


def test_a_model_whose_limit_is_not_known_gets_no_first_prompt_estimate(tmp_path):
    prepared = prepare(
        context_file(tmp_path), issuer_folder(tmp_path), tmp_path / "out",
        config="copilot-opus-medium", cap="50",
    )  # fmt: skip
    assert cpos_launch._first_prompt_lines(prepared, "copilot-opus-medium") == ()


# ---------------------------------------------------------------- compaction, fix round 1

DISCLOSURE = (
    "Charged excludes 1 context summary with no reported charge (CP-4); Copilot may bill them."
)


def test_a_started_compaction_with_no_completion_is_disclosed_next_to_the_charge(
    tmp_path, provider, capsys
):
    argv = compacting_run(tmp_path, provider, COMPACTING)
    assert main(argv) == 0
    lines = capsys.readouterr().out.splitlines()
    at = next(i for i, n in enumerate(lines) if n.startswith("Charged:"))
    assert lines[at + 1] == DISCLOSURE
    assert "Review:" not in "\n".join(lines)


def test_the_disclosure_is_not_counted_again_when_the_run_is_relaunched(tmp_path, provider, capsys):
    argv = compacting_run(tmp_path, provider, COMPACTING)
    assert main(argv) == 0
    capsys.readouterr()
    provider.answer = lambda context: pytest.fail("a retained module was sent again")
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert out.count("Charged excludes") == 1 and DISCLOSURE in out


def test_no_uncharged_compaction_means_no_disclosure_line(tmp_path, provider, capsys):
    assert main(compacting_run(tmp_path, provider, COMPACTED)) == 0
    assert "Charged excludes" not in capsys.readouterr().out


def events_dir(tmp_path, *records):
    from deploy_workflow.run_events import append_event

    for name, fields in records:
        append_event(tmp_path, name, **fields)
    return tmp_path


def test_uncharged_summaries_are_counted_once_each_and_modules_listed_once(tmp_path):
    same = {
        "module": "CP-5",
        "call_index": 1,
        "reason": "started, no completion reported",
        "attempt_id": "a",
    }
    events_dir(
        tmp_path,
        ("compaction_uncharged", same),
        ("compaction_uncharged", same),  # the same attempt recorded again
        ("compaction_uncharged", {**same, "module": "CP-8", "call_index": 3, "attempt_id": "b"}),
        ("compaction_uncharged", {**same, "module": "CP-8", "call_index": 5, "attempt_id": "c"}),
    )
    assert cpos_launch._charge_notes(tmp_path) == (
        (
            "Charged excludes 3 context summaries with no reported charge (CP-5, CP-8); "
            "Copilot may bill them."
        ),
    )


def test_late_charges_are_totalled_and_the_modules_named(tmp_path):
    late = {"module": "CP-8", "call_index": 9, "usd": "0.0996381", "attempt_id": "a"}
    events_dir(
        tmp_path,
        ("compaction_charge_late", late),
        ("compaction_charge_late", late),  # again: a relaunch cannot count it twice
        (
            "compaction_charge_late",
            {**late, "module": "CP-6", "usd": "0.1112661", "attempt_id": "b"},
        ),
    )
    assert cpos_launch._charge_notes(tmp_path) == (
        (
            "Charged excludes USD 0.2109042 of context-summary charges reported after their "
            "module ended (CP-8, CP-6); they were not settled."
        ),
    )


def test_a_module_with_several_summaries_in_one_call_is_listed_for_review(tmp_path):
    events_dir(
        tmp_path,
        ("compaction_multiple", {"module": "CP-8", "call_index": 2, "completions": 2}),
    )
    assert cpos_launch._review_lines(tmp_path) == (
        (
            "Review: CP-8 had more than one context summary billed in one call; check the run's "
            "charge."
        ),
    )


def test_an_accepted_repair_that_dropped_values_is_listed_for_review(tmp_path):
    events_dir(
        tmp_path,
        ("values_dropped_on_repair", {"module": "CP-6", "count": 2}),
        ("values_dropped_on_repair", {"module": "CP-2", "count": 1}),
    )
    assert cpos_launch._review_lines(tmp_path) == (
        (
            "Review: CP-6 was accepted after a repair that removed 2 sourced values; the list is "
            "in that module's review.json (dropped_values). Check them."
        ),
        (
            "Review: CP-2 was accepted after a repair that removed 1 sourced value; the list is "
            "in that module's review.json (dropped_values). Check it."
        ),
    )


def test_a_failed_dropped_value_check_is_listed_for_review(tmp_path):
    events_dir(
        tmp_path,
        ("dropped_values_check_failed", {"module": "CP-4", "error": "ValueError: boom"}),
        ("dropped_values_check_failed", {"module": "CP-4", "error": "ValueError: boom"}),
    )
    assert cpos_launch._review_lines(tmp_path) == (
        (
            "Review: CP-4 had a repair whose removed values could not be checked "
            "(dropped_values_error in its review.json); compare the repair with the rejected "
            "draft."
        ),
    )


def test_a_failed_summary_and_an_unended_start_without_ids_are_two_summaries(tmp_path):
    events_dir(
        tmp_path,
        ("context_compaction_started", {"module": "CP-5", "call_index": 1}),
        ("context_compaction_started", {"module": "CP-5", "call_index": 2}),
        ("context_compacted", {"module": "CP-5", "call_index": 3, "usd": "unknown"}),
        (
            "compaction_uncharged",
            {"module": "CP-5", "call_index": 3, "reason": "failed, no usage reported"},
        ),
    )
    assert cpos_launch._charge_notes(tmp_path) == (
        (
            "Charged excludes 2 context summaries with no reported charge (CP-5); "
            "Copilot may bill them."
        ),
    )


def test_the_launcher_prints_the_first_prompt_warning_while_the_run_goes_on(
    tmp_path, monkeypatch, capsys, copilot_ruling
):
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "ghp_" + "Z" * 36)
    runtime = tmp_path / "copilot-runtime"
    runtime.write_text("#!/bin/sh\n")
    monkeypatch.setenv("COPILOT_CLI_PATH", str(runtime))

    def fake_run(manifest, directory, **kwargs):
        kwargs["on_notice"]("Context:  CP-8: first prompt about 231,000 tokens")
        return directory / "delivery.json"

    monkeypatch.setattr(cpos_launch, "run_live_handoffs", fake_run)
    argv = copilot_argv(tmp_path, "copilot-sol-medium", "--live", "--ruling", str(copilot_ruling))
    assert main(argv) == 0
    assert "Context:  CP-8: first prompt about 231,000 tokens" in capsys.readouterr().out


def test_a_note_for_the_separate_cp8_comparison_prints_the_same_review_line(tmp_path, capsys):
    from deploy_workflow.owners import cpos

    response = tmp_path / "requests/CP-8/fp/1.response.md"
    response.parent.mkdir(parents=True)
    response.write_text("x")
    (response.parent / "1.compaction.json").write_text(json.dumps({"tokens_before": 259070}))
    cpos.report_compaction(tmp_path, str(response.relative_to(tmp_path)), "CP-8")
    assert capsys.readouterr().err.strip() == (
        "Review: CP-8 was written after GitHub Copilot summarised its context (259,070 tokens "
        "before); check its figures against the earlier modules."
    )
    cpos.report_compaction(tmp_path, "requests/CP-8/fp/2.response.md", "CP-8")
    assert capsys.readouterr().err == ""


def test_distinct_uncharged_starts_in_one_call_are_counted_apart_and_one_attempt_once(tmp_path):
    base = {"module": "CP-5", "call_index": 3, "reason": "started, no completion reported"}
    events_dir(
        tmp_path,
        ("compaction_uncharged", {**base, "attempt_id": "a"}),
        ("compaction_uncharged", {**base, "attempt_id": "b"}),
        ("compaction_uncharged", {**base, "attempt_id": "b"}),  # the same attempt again
    )
    (line,) = cpos_launch._charge_notes(tmp_path)
    assert line.startswith("Charged excludes 2 context summaries")


def test_a_malformed_late_amount_is_shown_as_unreadable_and_the_rest_still_totals(tmp_path):
    late = {"module": "CP-8", "call_index": 1}
    events_dir(
        tmp_path,
        ("compaction_charge_late", {**late, "usd": "unknown", "attempt_id": "a"}),
        ("compaction_charge_late", {**late, "usd": "0.25", "attempt_id": "b"}),
    )
    (line,) = cpos_launch._charge_notes(tmp_path)
    assert line == (
        "Charged excludes USD 0.25 of context-summary charges reported after their module ended "
        "(CP-8), and 1 amount that could not be read; they were not settled."
    )


def test_a_start_with_no_end_in_the_events_is_disclosed_though_the_run_was_killed(tmp_path):
    began = {"module": "CP-8", "call_index": 2}
    events_dir(
        tmp_path,
        ("context_compaction_started", {**began, "attempt_id": "a"}),
        ("context_compaction_started", {**began, "attempt_id": "b"}),
        ("context_compacted", {**began, "attempt_id": "b", "applied": True, "usd": "0.1"}),
    )
    (line,) = cpos_launch._charge_notes(tmp_path)
    assert line == (
        "Charged excludes 1 context summary with no reported charge (CP-8); Copilot may bill them."
    )


def test_a_start_already_disclosed_is_not_counted_again_from_its_start_event(tmp_path):
    began = {"module": "CP-8", "call_index": 2, "attempt_id": "a"}
    events_dir(
        tmp_path,
        ("context_compaction_started", began),
        ("compaction_uncharged", {**began, "reason": "started, no completion reported"}),
    )
    (line,) = cpos_launch._charge_notes(tmp_path)
    assert line.startswith("Charged excludes 1 context summary ")


def test_a_start_reported_uncharged_then_charged_late_is_only_the_late_charge(tmp_path):
    began = {"module": "CP-8", "call_index": 2, "attempt_id": "a"}
    events_dir(
        tmp_path,
        ("context_compaction_started", began),
        ("compaction_uncharged", {**began, "reason": "started, no completion reported"}),
        ("compaction_charge_late", {**began, "usd": "0.1"}),
    )
    (line,) = cpos_launch._charge_notes(tmp_path)
    assert line.startswith("Charged excludes USD 0.1 ")


def test_attemptless_starts_are_matched_to_attemptless_ends_by_count(tmp_path):
    began = {"module": "CP-8", "call_index": 2}
    events_dir(
        tmp_path,
        ("context_compaction_started", began),
        ("context_compaction_started", began),
        ("context_compacted", {**began, "applied": True, "usd": "0.1"}),
    )
    (line,) = cpos_launch._charge_notes(tmp_path)
    assert line.startswith("Charged excludes 1 context summary ")


# ---- C1 (owner ruling, 2026-11-13): CP-1's money tables are in the issuer's own currency.
def gbp(raw: str) -> str:
    return (
        raw.replace("| USD | US$m |", "| GBP | GBPm |")
        .replace("USD millions", "GBP millions")
        .replace("US$m", "GBPm")
    )


def test_a_gbp_issuers_cp1_handoff_is_accepted_and_its_strip_is_in_gbpm(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = gbp(answer(context, list(prepared.plan.layout.routes)))
    assert "US$" not in raw and "GBPm" in raw
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()
    block = strip_of(prepared, raw, tmp_path, "model-chart-strip")
    liquidity, ladder = block.figures[2], block.figures[3]
    assert liquidity.chart.unit == ladder.chart.unit == "GBPm"
    assert [m.value for m in liquidity.chart.marks][:2] == [Decimal(300), Decimal(450)]
    assert "US$" not in block.model_dump_json()


def test_a_gbp_strip_fact_states_gbp_and_never_usd(tmp_path):
    prepared, _task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = gbp(answer(context, list(prepared.plan.layout.routes)))
    routes = tuple(r for r in prepared.layout.routes if r.module_id == "CP-1")
    own = prepared.layout.model_copy(
        update={
            "blocks": tuple(dict.fromkeys(r.block_id for r in routes)),
            "routes": routes,
            "front": (),
        }
    )
    (tmp_path / "cp-1.md").write_text(raw)
    handoff = HandoffInput(path="cp-1.md", sha256=hashlib.sha256(raw.encode()).hexdigest())
    request = DeliveryRequest(run=prepared.plan.run, handoffs={"CP-1": handoff}, layout=own)
    files = markdown_files(request, tmp_path)
    view = json.loads(files["view.json"])
    typed = [
        f
        for m in view["modules"]
        for f in m["facts"]
        if f["table_id"].startswith("chart-") and f["status"] == "known" and f["unit"] == "MILLIONS"
    ]
    assert typed and {f["currency"] for f in typed} == {"GBP"}
    assert b"US$" not in files["report-view.json"]


def test_a_strip_figure_in_two_units_is_refused_by_the_adapter(tmp_path):
    prepared, _task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = gbp(answer(context, list(prepared.plan.layout.routes)))
    mixed = raw.replace("| FY2024 | 275 | 400 | GBPm |", "| FY2024 | 275 | 400 | EURm |")
    assert mixed != raw
    with pytest.raises(ValueError, match="one unit"):
        strip_of(prepared, mixed, tmp_path, "model-chart-strip")


def test_gbp_tables_under_usd_statements_are_sent_back_naming_the_money_unit(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes)).replace("US$m", "GBPm")
    issues = _checked_handoff(task, raw.encode(), checker(prepared.layout))
    assert any("`US$m`" in i for i in issues), issues


def test_gbp_statements_with_us_dollar_tables_are_sent_back_naming_the_money_unit(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-1", "credit_snapshot")
    raw = answer(context, list(prepared.plan.layout.routes)).replace("USD millions", "GBP millions")
    issues = _checked_handoff(task, raw.encode(), checker(prepared.layout))
    assert any("`GBPm`" in i for i in issues), issues


def test_another_modules_money_table_is_still_refused_in_gbpm(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-2D")
    raw = answer(context, list(prepared.plan.layout.routes))
    assert "| 120 | US$m |" in raw
    issues = _checked_handoff(
        task, raw.replace("| 120 | US$m |", "| 120 | GBPm |").encode(), checker(prepared.layout)
    )
    refused = (
        "`### Chart data: liquidity bridge` Free cash flow: a number in GBPm cannot be charted "
        "as US$m; write `Not supplied: reported in GBPm`."
    )
    assert refused in issues, issues


def test_only_cp1s_money_tables_say_the_money_unit_and_every_other_selector_is_unchanged():
    text = "\n".join(
        cpos_launch._selector(t)
        for module in sorted(cpos_launch.OWNER_TABLES)
        if module != "CP-1"
        for t in cpos_launch.OWNER_TABLES[module]
    )
    # sha256 of these selectors at HEAD c532bb3 (measured before the change, not by this code)
    digest = "4d55db88a6eed14bb347da382d11b7f595a784faeec8466c1b50045b8712ba72"
    assert hashlib.sha256(text.encode()).hexdigest() == digest
    assert "the money unit" not in text
    for table in cpos_launch.OWNER_TABLES["CP-1"]:
        if table.chart_unit != cpos_launch.MONEY:
            continue
        selector = cpos_launch._selector(table)
        assert "the money unit" in selector and "US$m" not in selector, table.heading
        assert cpos_launch.CURRENCY_RULE not in selector
    assert "The money unit is `US$m` when your statements are in USD" in cpos_launch.CP1_CHECK_BLOCK


def test_a_non_usd_reporting_currency_no_longer_limits_the_chart_strip():
    # The owner's C1 ruling reverses the expectation that the strip is US$m only.
    assert "chart-strip-usd" not in {rule.key for rule in RULES}
    key_text = (ROOT / "tests/fixtures/run-expectations/outcome-key.json").read_text()
    assert "chart-strip-usd" not in key_text and "US$m only" not in key_text
