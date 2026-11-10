"""User-launched CP-OS runs. A fake provider proves wiring only, not model or analytical quality."""

import dataclasses
import hashlib
import json
import os
import re
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from deploy_vii.registry import plan
from deploy_vii.report_view import ReportView
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
from deploy_workflow.model.turn import ToolCall, Turn, Usage, hosted_kind
from deploy_workflow.owners import cpos_forecast, cpos_launch
from deploy_workflow.owners.cpos import HandoffPlan, HandoffTask, RetainedHandoff, _checked_handoff
from deploy_workflow.owners.cpos_launch import (
    METHODS,
    LaunchRefused,
    checker,
    main,
    prepare,
    without_for,
)
from deploy_workflow.run_expectations import Item

ROOT = Path(__file__).resolve().parents[1]
RULING = ROOT / "docs/rulings/2026-11-05-live-loop-tests.md"  # configs: sol-medium
ISSUER = "Northbridge Synthetic Group"
AS_OF = "2025-03-31"

# Written by hand from the registry's dependency rules and the block titles on the Front Page.
COVENANT_MODULES = ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-4", "CP-2D", "CP-3C", "CP-5")
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
PATHWAY_MODULES = {
    "credit_snapshot": ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-4", "CP-3", "CP-5", "CP-6"),
    "earnings_update": ("CP-0", "CP-1", "CP-1B", "CP-1D", "CP-5"),
    # The fixture context's peer source is CP-DR, so the two pathways with CP-1C gain CP-DR.
    "relative_value": (
        *("CP-0", "CP-1", "CP-1A", "CP-3D", "CP-DR", "CP-1C", "CP-2", "CP-2D", "CP-3C", "CP-3"),
        "CP-5",
    ),
    "covenant_refinancing": COVENANT_MODULES,
    # CP-2 before CP-2A since 2026-11-10 (cp-2a SKILL.md: "Upstream: CP-1, CP-1B, CP-2").
    "distressed_restructuring": (
        *("CP-0", "CP-1", "CP-1A", "CP-DR", "CP-4", "CP-1C", "CP-2", "CP-2A", "CP-2G", "CP-2H"),
        *("CP-4C", "CP-5"),
    ),
    "portfolio_decision": ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-3", "CP-5", "CP-6"),
}


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
| FY2023 | 4.20 | 3.85 | x | Synthetic. |
| FY2024 | 3.60 | 3.25 | x | Synthetic. |""",
    "Chart data: interest cover": """| Period | EBITDA / cash interest | Reporting unit | Basis and limitation |
| --- | --- | --- | --- |
| FY2023 | 3.10 | x | Synthetic. |
| FY2024 | 3.40 | x | Synthetic. |""",
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
OWNER_TABLES = {
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
OWNER_PATHWAY = {"CP-2H": "distressed_restructuring", "CP-6": "portfolio_decision"}
OWNER_HEADERS = {
    "CP-1": PERIOD_HEAD.format("Revenue | Adjusted EBITDA"),
    "CP-2D": "| Step | Amount | Reporting unit | Basis and limitation |",
    "CP-3C": PERIOD_HEAD.format("Debt maturing | Committed resources"),
    "CP-2H": TRIGGER_HEAD,
    "CP-4": COVENANT_HEAD,
    "CP-6": LIMITS_HEAD,
}


# The H3 a reader meets first in every module (owner ruling 2026-11-05; Deploy V M365 runs). A copy,
# not an import: the answer key stays independent of cpos_launch.OPENING.
OPENING = {
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


def answer(context: dict, plan_routes: list) -> str:
    lines = [f"# {context['module_id']}", "", "## Request", f"{ISSUER} as of {AS_OF}.", ""]
    lines += ["## Sources", ""]
    lines += [f"- {n} {h}" for n, h in context["sources"].items()]
    lines += [f"- {n} {h['sha256']}" for n, h in context["handoffs"].items()]
    lines += ["", "## Findings", "", "### Reader summary", ""]
    lines += ["| Bottom line | Confidence | Main limitation |"]
    lines += ["| --- | --- | --- |", f"| {READER_BOTTOM_LINE} | Low | Synthetic data only. |", ""]
    lines += ["| Finding | Creditor impact | Confidence |", "| --- | --- | --- |"]
    lines += ["| One item was observed. | None for this synthetic case. | Low |", ""]
    own = [r for r in plan_routes if r.module_id == context["module_id"]]
    opening = OPENING.get(context["module_id"])
    if opening:  # The view follows the reader summary, whether or not a report section selects it.
        lines += [f"### {opening}", "", "The issuer's credit view, stated first.", ""]
        own = [r for r in own if r.heading != opening]
    for route in own:
        lines += [f"### {route.heading}", ""]
        if route.kind == "chart":
            lines += [CHART_TABLES[route.heading], ""]
        elif route.kind == "table":
            lines += ["| Item | Value |", "| --- | --- |", "| Observed | 1 |", ""]
        else:
            lines += ["A located finding.", ""]
    for heading, table in OWNER_TABLES.get(context["module_id"], {}).items():
        lines += [f"### {heading}", "", table, ""]
    for heading in ("Calculations", "Gaps", "Next module"):
        lines += [f"## {heading}", "", "None.", ""]
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
            "ok", turn, None, 200, None, None, 1, 2, turn.usage, billed_usd=turn.billed_usd
        )

    monkeypatch.setattr(LiveAdapter, "complete", complete)
    provider.calls = calls
    provider.searched = []
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


def test_instructions_ask_for_a_reader_section_and_keep_the_method_verbatim(tmp_path):
    prepared = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    text = (tmp_path / "out" / prepared.plan.instructions["CP-4"].path).read_text()
    assert "### Reader summary" in text
    assert "| Bottom line | Confidence | Main limitation |" in text
    assert "| Finding | Creditor impact | Confidence |" in text
    assert "first under `## Findings`" in text
    assert "add no new fact, figure or conclusion" in text
    assert "no module codes, table IDs or hashes" in text
    method = ROOT / "docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/SKILL.md"
    assert method.read_text() in text
    assert hashlib.sha256(method.read_bytes()).hexdigest() in text
    assert text.index("### Reader summary") < text.index(method.read_text())


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


@pytest.mark.parametrize("module", ["CP-MODEL", "CP-8", "CP-MEMO", "CP-OS", "CP-L10", "NOPE"])
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
    report = next((out / "deliveries").glob("*/report.html"))
    assert verify_delivery(next(out.glob("delivery-*.json")), report.parent) == report
    assert str(report) in capsys.readouterr().out
    page = report.read_text()
    assert "not been independently reviewed" in page
    assert not (report.parent / "model.html").exists()
    assert page.index('id="delivery-limits"') < page.index('id="call-root"')
    modules = json.loads((report.parent / "view.json").read_text())["modules"]
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


def test_issuer_name_from_the_context_cannot_inject_into_the_report(tmp_path, provider):
    argv = launch(tmp_path, "--modules", "CP-4", "--live", "--ruling", str(RULING))
    hostile = "A</script><script>alert(1)</script>"
    path = tmp_path / "context.json"
    data = json.loads(path.read_text())
    data["identity"]["issuer_name"] = hostile
    path.write_text(json.dumps(data))
    routes = prepare_routes(tmp_path, "sol-medium")
    provider.answer = lambda context: answer(context, routes).replace(ISSUER, hostile)
    assert main(argv) == 0
    report = next((tmp_path / "out/deliveries").glob("*/report.html")).read_text()
    assert "<script>alert(1)" not in report


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
    "CP-2": ["CP-0", "CP-1", "CP-1A"],
    "CP-4": ["CP-0", "CP-1", "CP-1A"],
    "CP-2D": ["CP-0", "CP-1", "CP-2"],
    "CP-3C": ["CP-0", "CP-1", "CP-1A", "CP-2D", "CP-4"],
    "CP-5": ["CP-0", "CP-1", "CP-1A", "CP-2", "CP-2D", "CP-3C", "CP-4"],
}


def test_each_module_is_sent_only_its_producers_handoffs(tmp_path, provider):
    # Run tdg-all-001 (2026-11-10) sent every module every earlier handoff: the first request
    # grew to 1 MB by CP-5, and six modules had all their source reads refused.
    argv = launch(tmp_path, "--live", "--ruling", str(RULING))
    routes = prepare_routes(tmp_path, "sol-medium", modules=None)
    sent = {}

    def answering(context):
        sent[context["module_id"]] = sorted(context["handoffs"])
        return answer(context, routes)

    provider.answer = answering
    assert main(argv) == 0
    assert sent == COVENANT_PRODUCERS


def test_answers_pinned_to_their_producers_are_replayed_unsent(tmp_path, provider):
    """CP-OS replays a retained answer whose pins are exactly the producers it is sent."""
    argv = launch(tmp_path, "--live", "--ruling", str(RULING))
    routes = prepare_routes(tmp_path, "sol-medium", modules=None)
    provider.answer = lambda context: answer(context, routes)
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


def test_cp2_instructions_carry_the_reader_standard_and_its_opening(tmp_path):
    prepared = prepare(
        context_file(tmp_path, "credit_snapshot"),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )

    def read(module: str) -> str:
        return (tmp_path / "out" / prepared.plan.instructions[module].path).read_text()

    cp2 = read("CP-2")
    assert "place `### Credit view` directly after `### Reader summary`" in cp2
    assert "CANON_SHARED.md" in cp2
    assert "State each limitation once" in cp2 and "currency and unit" in cp2
    # The user's Microsoft 365 Copilot custom instruction, which Deploy V's M365 runs carried.
    assert "senior credit research analyst" in cp2 and "senior credit committees" in cp2
    assert "external sources" in cp2
    # The custom instruction is global; the CANON_SHARED reader rules and opening are CP-2's.
    for module in prepared.plan.instructions:
        text = read(module)
        for phrase in (
            "senior credit research analyst",
            "senior credit committees",
            "external sources",
        ):
            assert phrase in text, (module, phrase)
    cp1a = read("CP-1A")
    for phrase in ("CANON_SHARED.md", "State each limitation once"):
        assert phrase not in cp1a, phrase
    assert "open `## Findings` with `### Credit view`" not in cp1a


def test_every_module_has_an_opening_and_its_instructions_require_it(tmp_path):
    assert set(OPENING) == set(METHODS) == set(cpos_launch.OPENING)
    assert cpos_launch.OPENING == OPENING
    prepared = prepare(
        context_file(tmp_path, "credit_snapshot"),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    for module, ref in prepared.plan.instructions.items():
        text = (tmp_path / "out" / ref.path).read_text()
        assert f"place `### {OPENING[module]}` directly after `### Reader summary`" in text, module
        assert ("State each limitation once" in text) == (module == "CP-2"), module


def test_cp2_instructions_place_the_credit_view_after_the_reader_summary(tmp_path):
    prepared = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    read = lambda m: (tmp_path / "out" / prepared.plan.instructions[m].path).read_text()
    assert "place `### Credit view` directly after `### Reader summary`" in read("CP-2")
    assert "first under `## Findings`" in read("CP-2") and "first under `## Findings`" in read(
        "CP-4"
    )


@pytest.mark.parametrize("pathway", ["credit_snapshot", "relative_value"])
def test_checker_accepts_cp2_opening_with_its_view(tmp_path, pathway):
    prepared, task, context = good_task(tmp_path, "CP-2", pathway)
    raw = answer(context, list(prepared.plan.layout.routes))
    assert raw.count("### Credit view") == 1
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()


VIEW = "### Credit view\n\nThe issuer's credit view, stated first.\n\n"


@pytest.mark.parametrize("pathway", ["credit_snapshot", "relative_value"])
@pytest.mark.parametrize(
    ("old", "new"),
    [
        (VIEW, ""),
        ("### Reader summary\n\n", "Preamble before the summary.\n\n### Reader summary\n\n"),
        (VIEW, "### Overview\n\nText.\n\n" + VIEW),
        ("The issuer's credit view, stated first.", "| A | B |\n| --- | --- |\n| x | y |"),
        ("The issuer's credit view, stated first.", "- a bullet, not a paragraph"),
        ("The issuer's credit view, stated first.", "```json\n{}\n```"),
        ("The issuer's credit view, stated first.", "<!-- a comment -->"),
    ],
    ids=[
        "missing",
        "prose-first",
        "other-section-first",
        "table-first",
        "bullet",
        "fence",
        "comment",
    ],
)
def test_checker_rejects_cp2_that_does_not_open_with_its_view(tmp_path, pathway, old, new):
    prepared, task, context = good_task(tmp_path, "CP-2", pathway)
    raw = answer(context, list(prepared.plan.layout.routes))
    assert old in raw
    issues = _checked_handoff(task, raw.replace(old, new).encode(), checker(prepared.layout))
    assert any(
        "Place ### Credit view directly after ### Reader summary" in issue for issue in issues
    ), issues


@pytest.mark.parametrize(
    ("module", "pathway"), [("CP-1A", "credit_snapshot"), ("CP-0", "credit_snapshot")]
)
def test_checker_enforces_the_opening_on_every_module(tmp_path, module, pathway):
    prepared, task, context = good_task(tmp_path, module, pathway)
    raw = answer(context, list(prepared.plan.layout.routes))
    view = f"### {OPENING[module]}\n\nThe issuer's credit view, stated first.\n\n"
    assert view in raw
    assert _checked_handoff(task, raw.encode(), checker(prepared.layout)) == ()
    issues = _checked_handoff(task, raw.replace(view, "").encode(), checker(prepared.layout))
    assert any(
        f"Place ### {OPENING[module]} directly after ### Reader summary" in i for i in issues
    ), issues


def test_every_selected_method_file_exists():
    assert all(
        (ROOT / path.split(" § ")[0]).is_file() for files in METHODS.values() for path in files
    )


# --- module method gaps (owner, 2026-11-10: "Fix all ... Keep a copy of the methodology") --------
SKILLS = "docs/reuse/selected-methods/skills/"
# Written from each SKILL.md's own words ("mandatory, not optional", "binding method for the ...
# phase", "they bind every run", "Read ...; materialize its run-specific brief"), not from METHODS.
BINDING_COMPANIONS = {
    "CP-1B": (
        "cp-1b-earnings-delta/SKILL.md",
        "cp-1b-earnings-delta/references/REF_CP-1B_STEPS.md",
    ),
    "CP-2A": ("cp-2a-downside-pathway/references/REF_CP-2A_STEPS.md",),
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
    *("CP-1B", "CP-1C", "CP-1D", "CP-2A", "CP-2D", "CP-2E", "CP-2G", "CP-2H", "CP-3", "CP-3D"),
    *("CP-4", "CP-4C", "CP-5", "CP-6", "CP-DR"),
]


def test_each_module_is_sent_the_companions_its_method_calls_binding():
    for module, names in BINDING_COMPANIONS.items():
        for name in names:
            assert SKILLS + name in METHODS[module], (module, name)


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
    assert all(" § " not in name for name, _ in cpos_launch.method_sections("CP-2"))


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
    _, texts = all_instructions(tmp_path, modules=tuple(METHODS))
    assert set(texts) == set(METHODS)
    for module, text in texts.items():
        head = text.partition(cpos_launch.METHOD_MARK)[0]
        for phrase in (
            "That check is the acceptance, validation and lineage the method asks",
            "do not block for want of an acceptance receipt",
            "`prepare_invocation.py`",
            "`validate_handoff.py`",
            "`confidence_score.py`",
            "record each as not run",
            "Nobody can answer a question during this run",
            "then the method's declared safe default",
            "block only the decision the method ties to it",
            "is not in the method block below is unavailable",
            "Missing evidence still blocks exactly what the method says it blocks",
        ):
            assert phrase in head, (module, phrase)


def test_modules_run_after_the_handoffs_their_methods_consume(tmp_path):
    """Retained run cpos-tdg-sol-medium-all-001: CP-2E and CP-2A ran before CP-2, and CP-2A blocked
    with "Required fundamental handoff CP-2 is Not supplied"."""
    prepared, _ = all_instructions(tmp_path, modules=tuple(METHODS))
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
    assert "`src/deploy_vii/methods/cp2a.md` governs" in head
    assert "labelled analyst assumptions" in head and "anchored to a stated figure" in head
    assert "an EBITDA decline and a cash-interest rate increase" in head
    assert "at most four decimal places" in head
    assert "Stress design" not in texts["CP-2G"].partition(cpos_launch.METHOD_MARK)[0]


@pytest.mark.parametrize(
    ("pathway", "peer_source", "added"),
    [
        ("relative_value", "cp_dr_public", True),
        ("distressed_restructuring", "cp_dr_public", True),
        ("relative_value", "none", False),
        ("credit_snapshot", "cp_dr_public", False),  # no CP-1C in this pathway
    ],
)
def test_a_pathway_with_cp1c_adds_cpdr_when_cpdr_is_the_peer_source(
    tmp_path, pathway, peer_source, added
):
    """Owner, 2026-11-10: "Cp-1c is supposed to get that information from cp-dr by default". No
    pathway lists CP-DR, so the default peer source used to leave CP-1C without a producer."""
    prepared, _ = all_instructions(tmp_path, pathway, peer_source=peer_source)
    order = list(prepared.plan.instructions)
    assert ("CP-DR" in order) is added
    assert set(order) - {"CP-DR"} == set(PATHWAY_MODULES[pathway]) - {"CP-DR"}
    if added:
        assert order.index("CP-DR") < order.index("CP-1C")
        assert "CP-DR" in prepared.plan.run.requested_modules


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
        benchmark = texts["CP-1C"].partition(cpos_launch.METHOD_MARK)[0]
        assert "take the peer set and its figures from the CP-DR handoff's TDR.4" in benchmark
        assert "You own inclusion, comparability, normalisation and every statistic" in benchmark
    elif "CP-1C" in texts:
        assert "CP-DR handoff's TDR.4" not in texts["CP-1C"].partition(cpos_launch.METHOD_MARK)[0]


def test_checker_rejects_a_handoff_without_a_reader_section(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-4")
    raw = answer(context, list(prepared.plan.layout.routes))
    start = raw.index("### Reader summary")
    missing = raw[:start] + raw[raw.index("### ", start + 4) :]
    issues = _checked_handoff(task, missing.encode(), checker(prepared.layout))
    assert any("Reader summary" in issue for issue in issues)


def test_checker_rejects_a_reader_number_the_handoff_does_not_hold(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-4")
    raw = answer(context, list(prepared.plan.layout.routes))
    wrong = raw.replace(READER_BOTTOM_LINE, "Cover was 9.87x.")
    issues = _checked_handoff(task, wrong.encode(), checker(prepared.layout))
    assert any("9.87" in issue for issue in issues)


def test_the_reader_section_reaches_the_report_unchanged(tmp_path, provider):
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
    provider.answer = lambda context: answer(context, routes)
    assert main(argv) == 0
    report = next((tmp_path / "out" / "deliveries").glob("*/report.html"))
    assert READER_BOTTOM_LINE in (report.parent / "report-view.json").read_text()


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
        Decimal("4.20"),
        Decimal("3.85"),
        Decimal("3.60"),
        Decimal("3.25"),
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
        ("| 3.85 |", "| 3.85x |", "3.85x"),
        ("| 300 | 450 | US$m |", "| 300 | 450 | EUR m |", "EUR m"),
        ("| FY2023 | 3.10 | x | Synthetic. |", "| FY2023 | 3.10 | x |  |", "Basis and limitation"),
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
    prepared, *_ = good_task(tmp_path, "CP-1", "credit_snapshot")
    assert "The HTML Model and calculation JSON are not published" in prepared.layout.scope
    assert "charts" not in prepared.layout.scope.lower()


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
    report = next((out / "deliveries").glob("*/report.html"))
    assert verify_delivery(next(out.glob("delivery-*.json")), report.parent) == report
    handoffs = {m: (report.parent / f"{m}.md").read_bytes() for m in LIVE_MODULES}
    digest = {m: hashlib.sha256(raw).hexdigest().encode() for m, raw in handoffs.items()}
    assert digest["CP-0"] in handoffs["CP-1"]
    assert digest["CP-0"] in handoffs["CP-1A"] and digest["CP-1"] in handoffs["CP-1A"]
    for filed in (b"7,940", b"6,261"):
        assert filed in handoffs["CP-1"]
        assert filed in report.read_bytes()
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
    monkeypatch.setattr(cpos_launch, "run_live_handoffs", lambda m, d, **k: d / "report.html")
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
        return directory / "report.html"

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


def test_launcher_layout_adds_front_routes_only_for_requested_modules(tmp_path):
    full = prepare(
        context_file(tmp_path),
        issuer_folder(tmp_path),
        tmp_path / "out",
        config="sol-medium",
        cap="50",
    )
    # CP-5, CP-2 and CP-0 are in the covenant run, CP-6 is not.
    assert [(r.module_id, r.kind, r.label) for r in full.plan.layout.front] == [
        ("CP-5", "table", "Evidence validation"),
        ("CP-2", "table", "Fundamental credit"),
        ("CP-0", "table", "Source readiness"),
    ]
    assert {(r.heading, r.table_header) for r in full.plan.layout.front} == {
        ("Reader summary", "Bottom line | Confidence | Main limitation")
    }
    assert [r.module_id for r in cpos_launch._front_routes(("CP-0", "CP-1", "CP-4"))] == ["CP-0"]


def test_cp6_front_routes_lead_with_its_summary_then_its_action_bias():
    routes = cpos_launch._front_routes(("CP-0", "CP-2", "CP-6"))
    assert [(r.module_id, r.kind, r.label) for r in routes] == [
        ("CP-6", "table", "Committee decision"),
        ("CP-2", "table", "Fundamental credit"),
        ("CP-0", "table", "Source readiness"),
        ("CP-6", "prose", "Committee action bias"),
    ]
    assert (routes[-1].heading, routes[-1].prefix) == (
        "Action Bias Determination",
        "Final Action Bias:",
    )


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
        cpos_launch, "run_live_handoffs", lambda manifest, directory, **k: directory / "report.html"
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
    assert f"Report:   {tmp_path / 'runs' / 'x' / 'report.html'}" in captured.out


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


def forecast_answer(context: dict, routes: list, block: str | None = None) -> str:
    """CP-1 prints the base amounts; CP-2G ends its findings with the inputs block."""
    text = answer(context, routes)
    if context["module_id"] == "CP-1":
        rows = "\n".join(f"| {k} | {v} |" for k, v in BASE.items())
        # Above the owner's chart table, so the base amounts do not read as rows of that table.
        mark = "### Chart data: revenue and EBITDA"
        mark = mark if mark in text else "## Calculations"
        return text.replace(mark, f"| Base | USD m |\n| --- | --- |\n{rows}\n\n{mark}", 1)
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


def forecast_run(tmp_path, provider, capsys, block, modules=("CP-2G",)):
    argv = launch(tmp_path, "--live", "--ruling", str(RULING), pathway="distressed_restructuring")
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
    provider.answer = lambda context: forecast_answer(context, routes, block)
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
    assert verify_delivery(next(out.glob("delivery-*.json")), folder) == folder / "report.html"
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


def test_model_publish_failure_keeps_the_report(tmp_path, provider, capsys, monkeypatch):
    def refuse(cp1, handoff):
        raise ValueError("synthetic failure")

    monkeypatch.setattr(cpos_forecast, "model_files", refuse)
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block())
    assert code == 0
    (folder,) = (out / "deliveries").iterdir()
    assert (folder / "report.html").is_file() and not (folder / "forecast_exact.json").exists()
    assert "Model not published: synthetic failure" in seen.err
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["cp_forecast_published"] is False
    assert completed["forecast_failure"] == "synthetic failure"
    assert f"Report:   {folder / 'report.html'}" in seen.out


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
    assert all("[null, null, null]" in i for i in issues if i.startswith("Forecast inputs"))


def test_without_a_shock_only_the_reference_case_is_published(tmp_path, provider, capsys):
    code, out, seen = forecast_run(tmp_path, provider, capsys, forecast_block(downside_shock=None))
    assert code == 0, seen.err
    (folder,) = (out / "deliveries").iterdir()
    assert list(json.loads((folder / "forecast_exact.json").read_text())["outputs"]) == [
        "REFERENCE"
    ]


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
    assert [c["label"] for c in grid["columns"]] == ["FY2025E", "FY2026E", "FY2027E"] * 2
    assert [c["group"] for c in grid["columns"]][::3] == [
        "Base case (reference illustration)",
        "Downside stress (shock on base drivers)",
    ]


def test_the_library_shows_every_computed_case_in_order(tmp_path, provider, capsys):
    code, _, seen = forecast_run(tmp_path, provider, capsys, cased_block())
    assert code == 0 and "Library not updated" not in seen.err
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    (model,) = (m for m in data["workspace"]["models"] if m["cashflow"] is not None)
    grid = model["cashflow"]
    assert [c["group"] for c in grid["columns"]][::3] == [
        "Base case (reference illustration)",
        "Upside",
        "Downside (CP-2G drivers)",
        "Downside stress (shock on base drivers)",
    ]
    revenue = next(r for r in grid["rows"] if r["label"] == "Revenue")
    assert [c["exact"] for c in revenue["cells"][3:6]] == ["1100", "1210", "1331"]
    assert [c["exact"] for c in revenue["cells"][6:9]] == ["1000", "1000", "1000"]
    revenue = next(r for r in grid["rows"] if r["label"] == "Revenue")
    assert [c["exact"] for c in revenue["cells"][:3]] == ["1050", "1092", "1124.76"]
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
    for page, route in [*pages, (delivery / "report.html", "")]:
        dom, console = visit(page, route)
        shown = re.sub(r"(?s)<(script|style)\b.*?</\1>|<[^>]+>|\s+", " ", dom)
        assert console == [], (route, console)
        assert UNFILLED.search(shown) is None, (route, UNFILLED.findall(shown))
        assert ISSUER in shown, route


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
    assert "Not supplied: reported in <unit>" in text


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
    (table,) = cpos_launch.OWNER_TABLES["CP-2D"]
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
    (table,) = cpos_launch.OWNER_TABLES["CP-2D"]
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
        page = files["report.html"].decode()
        assert heading in page
        for cell in table.splitlines()[2].strip("|").split("|"):
            assert cell.strip() in page


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
