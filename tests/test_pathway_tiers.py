"""Lite, Full and Deep credit assessments and the cap per pathway (ruling
2026-11-15-pathway-tiers-and-caps). Every expectation is written by hand: module lists, orders and
caps are copied from the owner's choices and the registry's dependency text, not from the code under
test. Offline: the launcher prepares, nothing is sent to any provider; spend is a test budget."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast, get_args

import pytest
from inbox_fixtures import CONTEXT, layout, settings

from deploy_vii.contracts import PATHWAY_CAP_USD, PATHWAY_MODULES, PathwayId
from deploy_vii.registry import dependencies, plan
from deploy_vii.report_view import pathways
from deploy_workflow.inbox import runs
from deploy_workflow.inbox.activity import snapshot
from deploy_workflow.inbox.runs import Record
from deploy_workflow.inbox.scheduler import Scheduler
from deploy_workflow.model.budget import Budget, BudgetExhausted
from deploy_workflow.owners.cpos_launch import main
from deploy_workflow.run_start import submissions
from deploy_workflow.run_start.submissions import Answers, Refused

pytest_plugins = ["inbox_fixtures"]

ROOT = Path(__file__).resolve().parents[1]
DEEP = "deep_credit_assessment"
D = Decimal

# Owner, 2026-11-13 and 2026-11-15: Lite and Full as they were.
LITE = ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-2A")
FULL = (
    *("CP-0", "CP-1", "CP-MODEL", "CP-1A", "CP-DR", "CP-2", "CP-2A", "CP-2D", "CP-2E"),
    *("CP-2G", "CP-4", "CP-3C", "CP-3", "CP-5", "CP-6"),
)
# Owner, 2026-11-15: "Deep = all": Full plus every specialist module.
SPECIALISTS = {"CP-1B", "CP-1C", "CP-1D", "CP-2H", "CP-3D", "CP-4C"}
# The order worked out from methodology.json's required and optional inputs: CP-1B and CP-DR after
# CP-1; CP-1C after CP-DR (optional, its peers); CP-1D after CP-1B; CP-2 after CP-1A, CP-1B, CP-1C,
# CP-1D and CP-DR; CP-4 after CP-1A and CP-1D; CP-2A after CP-2; CP-2E after CP-2; CP-2D after CP-2;
# CP-2G after CP-2A and CP-2D; CP-2H after CP-2G; CP-3D after CP-2H; CP-3C after CP-2D, CP-2A, CP-4
# and CP-3D; CP-4C after CP-4, CP-2G, CP-2A, CP-3C and CP-1C; CP-3 after everything it may read;
# CP-5 after every analyst; CP-6 after CP-5. Ties keep methodology.json's order.
DEEP_ORDER = (
    *("CP-0", "CP-1", "CP-1A", "CP-1B", "CP-DR", "CP-1C", "CP-1D", "CP-2", "CP-4", "CP-2A"),
    *("CP-2E", "CP-2D", "CP-2G", "CP-2H", "CP-3D", "CP-3C", "CP-4C", "CP-3", "CP-5", "CP-6"),
)
PURPOSE = (
    "earnings_update",
    "relative_value",
    "covenant_refinancing",
    "distressed_restructuring",
    "portfolio_decision",
)
# Owner, 2026-11-15: "Deep max $40, Full $25 and Lite $15"; the purpose pathways keep USD 20.
CAPS = {
    "lite_credit_assessment": D(15),
    "credit_snapshot": D(25),
    DEEP: D(40),
    **{p: D(20) for p in PURPOSE},
    "short_snapshot": D(20),
}
# What one GPT Sol call holds, whatever its size (pricing.request_reservation_usd at the configured
# context ceiling): 1,050,000 tokens at the dearest input rate USD 5 a million, plus 32,000 output
# tokens at the long-context output rate USD 15 a million is 5.25 + 0.48 = 5.73.
SOL_HOLD = D("5.73")
_NOW = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)


def test_lite_and_full_keep_their_modules() -> None:
    assert PATHWAY_MODULES["lite_credit_assessment"] == LITE
    assert PATHWAY_MODULES["credit_snapshot"] == FULL


def test_deep_is_full_plus_every_specialist() -> None:
    deep = PATHWAY_MODULES[DEEP]
    assert len(deep) == len(set(deep)) == 21
    assert set(deep) == set(FULL) | SPECIALISTS


def test_deep_runs_in_the_registrys_planned_order() -> None:
    assert tuple(m for m in plan(PATHWAY_MODULES[DEEP]) if m != "CP-MODEL") == DEEP_ORDER


@pytest.mark.parametrize(
    ("first", "then"),
    [
        ("CP-DR", "CP-3"),  # CP-3's enterprise value by default from peer multiples (owner)
        ("CP-1C", "CP-3"),
        ("CP-DR", "CP-1C"),
        ("CP-1C", "CP-2"),
        ("CP-1B", "CP-1D"),
        ("CP-2G", "CP-2H"),
        ("CP-2H", "CP-3D"),
        ("CP-2D", "CP-3C"),
        ("CP-4", "CP-4C"),
        ("CP-2G", "CP-4C"),
        ("CP-2A", "CP-4C"),
        ("CP-3C", "CP-4C"),
        ("CP-4C", "CP-3"),
    ],
)
def test_each_added_module_comes_after_what_it_reads(first: str, then: str) -> None:
    assert DEEP_ORDER.index(first) < DEEP_ORDER.index(then)


def test_cp3_is_sent_cp1cs_handoff_and_cp5_and_cp6_close_the_run() -> None:
    producers = dependencies(DEEP_ORDER)
    assert {"CP-1C", "CP-1D", "CP-2H", "CP-3D", "CP-3C", "CP-4C"} <= producers["CP-3"]
    assert {"CP-4", "CP-2G", "CP-2A", "CP-3C", "CP-1C"} <= producers["CP-4C"]
    assert producers["CP-5"] == set(DEEP_ORDER[:-2])  # every analyst handoff
    assert DEEP_ORDER[-2:] == ("CP-5", "CP-6")


def test_deeps_report_has_fulls_sections_and_one_per_added_module() -> None:
    by_id = {p.id: p for p in pathways()}
    full, deep = by_id["credit_snapshot"].blocks, by_id[DEEP].blocks
    assert by_id[DEEP].title == "Deep credit assessment"
    assert set(full) <= set(deep) and len(deep) == 24
    added = {
        "downside-stress",
        "break-points",
        "headline-results",
        "earnings-quality",
        "peer-positioning",
        "liquidity-runway",
        "forward-credit-path",
        "rating-triggers",
        "covenant-tests-headroom",
        "recovery-by-class",
        "refinancing-paths",
        "market-against-fundamentals",
    }
    assert set(deep) - set(full) == added
    assert deep[-1] == "what-changed"
    # Offered in this order on the run start page: Lite, Full, Deep, then the purpose pathways.
    assert [p.id for p in pathways()][:3] == ["lite_credit_assessment", "credit_snapshot", DEEP]


def test_one_cap_per_pathway() -> None:
    assert dict(PATHWAY_CAP_USD) == CAPS
    assert set(PATHWAY_CAP_USD) == set(get_args(PathwayId)) == set(PATHWAY_MODULES)


@pytest.mark.parametrize(
    ("pathway", "calls"),
    [
        # Each call holds 5.73 and costs 3.00; a call is made while spent + 5.73 <= cap.
        ("lite_credit_assessment", 4),  # 9.00 + 5.73 = 14.73 <= 15; 12.00 + 5.73 > 15
        ("credit_snapshot", 7),  # 18.00 + 5.73 = 23.73 <= 25; 21.00 + 5.73 > 25
        (DEEP, 12),  # 33.00 + 5.73 = 38.73 <= 40; 36.00 + 5.73 > 40
        ("relative_value", 5),  # 12.00 + 5.73 = 17.73 <= 20; 15.00 + 5.73 > 20
    ],
)
def test_a_run_stops_at_its_pathways_cap(tmp_path: Path, pathway: str, calls: int) -> None:
    budget = Budget(PATHWAY_CAP_USD[cast(PathwayId, pathway)], tmp_path)
    made = 0
    with pytest.raises(BudgetExhausted):
        while True:
            budget.reserve(f"call-{made}", SOL_HOLD, None, config_id="sol-medium")
            budget.settle(f"call-{made}", D("3.00"))
            made += 1
    assert made == calls
    assert budget.spent == D("3.00") * calls


def _context(tmp_path: Path, pathway: str) -> Path:
    """SYNTHETIC: the research-minimal case's context for this pathway."""
    data = json.loads(json.dumps(CONTEXT))
    data["run"].update(pathway=pathway, as_of="2025-03-31")
    data["identity"].update(issuer_name="Northbridge Synthetic Ltd", issuer_id="nbg")
    path = tmp_path / f"{pathway}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("pathway", "cap"),
    [("lite_credit_assessment", "15"), ("credit_snapshot", "25"), (DEEP, "40")],
)
def test_the_launcher_defaults_to_the_pathways_cap(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], pathway: str, cap: str
) -> None:
    issuer = tmp_path / "issuer"
    issuer.mkdir()
    (issuer / "annual.txt").write_text("Net sales were 100.", encoding="utf-8")
    out = tmp_path / "out"
    argv = ["--context", str(_context(tmp_path, pathway)), "--sources", str(issuer)]
    assert main([*argv, "--config", "sol-medium", "--out", str(out), "--no-library"]) == 0
    manifest = json.loads((out / "workflow.json").read_text(encoding="utf-8"))
    assert manifest["provider_cap_usd"] == cap
    printed = capsys.readouterr().out
    assert f"Cap:      USD {cap} (hold per call: {SOL_HOLD})" in printed
    assert "No provider was called." in printed


def _answers(pathway: str) -> Answers:
    context = json.loads(json.dumps(CONTEXT))
    context["run"].update(pathway=pathway, as_of="2026-11-09")
    context["identity"].update(issuer_id="acme", issuer_name="Acme Corp")
    body: dict[str, Any] = {
        "context": context,
        "modules": [],
        "max_turns": 32,
        "level": "basic",
        "model": "gpt",
        "effort": "balanced",
        "submitted_by": "analyst",
    }
    return cast(Answers, body)


def _upload(root: Path) -> str:
    sid = submissions.new(layout(root))
    (submissions.files_folder(layout(root), sid) / "a.txt").write_bytes(b"Net sales were 100.")
    return sid


def test_each_submission_carries_and_launches_at_its_pathways_cap(root: Path) -> None:
    w = Scheduler(settings(root))
    try:
        for pathway, cap in (
            ("lite_credit_assessment", "15"),
            ("credit_snapshot", "25"),
            (DEEP, "40"),
            ("relative_value", "20"),
        ):
            answers, sid = _answers(pathway), _upload(root)
            got = submissions.summary(layout(root), sid, answers)
            assert (got["error"], got["cap"]) == ("", cap), pathway
            record = w.submit(sid, answers, str(got["digest"]))
            assert record.cap == cap
            argv = runs.command(layout(root), record, Path("c.json"), launcher=("L",), ruling=None)
            assert argv[argv.index("--cap") + 1] == cap
            shown = snapshot(layout(root), [record], now=_NOW)["runs"][0]
            assert shown["cap"] == cap
    finally:
        w.close()


def test_a_summary_issued_before_per_pathway_caps_must_be_made_again(root: Path) -> None:
    """A summary made before this change recorded no cap (it showed USD 20): Submit refuses it."""
    answers, sid = _answers(DEEP), _upload(root)
    got = submissions.summary(layout(root), sid, answers)
    issued = layout(root).uploads / sid / "issued"
    digest, prior, cap_line = issued.read_text(encoding="ascii").split()
    assert cap_line == "cap=40"
    issued.write_text(f"{digest}\n{prior}\n", encoding="ascii")  # as the earlier service wrote it
    w = Scheduler(settings(root))
    try:
        with pytest.raises(Refused, match="not the one the summary showed; review the summary"):
            w.submit(sid, answers, str(got["digest"]))
        assert runs.load_all(layout(root)) == []
    finally:
        w.close()


@pytest.mark.parametrize(
    ("pathway", "cap"),
    [
        # A record queued before this change: never more than USD 20 (what its summary showed),
        # nor more than its pathway's cap now.
        ("lite_credit_assessment", "15"),
        ("credit_snapshot", "20"),
        (DEEP, "20"),
        ("portfolio_decision", "20"),
    ],
)
def test_a_record_queued_before_per_pathway_caps_launches_at_no_more_than_was_approved(
    root: Path, pathway: str, cap: str
) -> None:
    record = Record("r1", pathway, "Acme", "queued", "t")
    assert record.cap == ""
    argv = runs.command(layout(root), record, Path("c.json"), launcher=("L",), ruling=None)
    assert argv[argv.index("--cap") + 1] == cap


@pytest.mark.parametrize(
    ("pathway", "cap"),
    [
        (DEEP, "41"),
        (DEEP, "0"),
        (DEEP, "NaN"),
        (DEEP, "forty"),
        ("credit_snapshot", "40"),
        (DEEP, 0),
    ],
)
def test_a_hand_edited_cap_above_the_pathways_is_refused(
    root: Path, pathway: str, cap: Any
) -> None:
    """A cap that is not an amount within the pathway's (a number where text belongs included)."""
    record = Record("r1", pathway, "Acme", "queued", "t", cap=cap)
    with pytest.raises(ValueError, match="is not an amount above zero and at most"):
        runs.command(layout(root), record, Path("c.json"), launcher=("L",), ruling=None)
    assert snapshot(layout(root), [record], now=_NOW)["runs"][0]["cap"] is None


def test_an_unknown_pathway_has_no_cap(root: Path) -> None:
    with pytest.raises(ValueError, match="has no cap"):
        runs.cap_of(Record("r1", "no_such_pathway", "Acme", "queued", "t"))
    # A pathway that is not even text (a hand-edited record) must not stop the activity poll.
    odd = Record("r2", cast(str, ["credit_snapshot"]), "Acme", "queued", "t")
    assert snapshot(layout(root), [odd], now=_NOW)["runs"][0]["cap"] is None


def _launch_argv(tmp_path: Path, pathway: str, *extra: str) -> list[str]:
    issuer = tmp_path / "issuer"
    issuer.mkdir(exist_ok=True)
    (issuer / "annual.txt").write_text("Net sales were 100.", encoding="utf-8")
    argv = ["--context", str(_context(tmp_path, pathway)), "--sources", str(issuer)]
    return [*argv, "--config", "sol-medium", "--out", str(tmp_path / "out"), "--no-library", *extra]


@pytest.mark.parametrize(
    ("pathway", "asked", "ruled"),
    [
        ("lite_credit_assessment", "500", "15"),
        ("lite_credit_assessment", "15.01", "15"),
        ("credit_snapshot", "40", "25"),  # Deep's cap on a Full context: the context is what runs
        (DEEP, "40.5", "40"),
        ("relative_value", "25", "20"),
    ],
)
def test_the_launcher_refuses_a_cap_above_the_pathways(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], pathway: str, asked: str, ruled: str
) -> None:
    """Owner: "Hard cap per pathway". Every launch ends at the launcher, so it holds there."""
    assert main(_launch_argv(tmp_path, pathway, "--cap", asked)) == 2
    assert f"--cap {asked}: above the {pathway} cap of USD {ruled}" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_the_launcher_takes_a_lower_cap_and_names_the_cap_of_a_folder_it_cannot_resume(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A folder started under the earlier USD 20 resumes only at that cap; its cap never rises."""
    assert main(_launch_argv(tmp_path, "credit_snapshot", "--cap", "20")) == 0
    manifest = tmp_path / "out/workflow.json"
    held = manifest.read_bytes()
    assert json.loads(held)["provider_cap_usd"] == "20"
    capsys.readouterr()
    assert main(_launch_argv(tmp_path, "credit_snapshot")) == 2  # the default is now USD 25
    refusal = capsys.readouterr().err
    assert "the folder was started at a cap of USD 20, not USD 25" in refusal
    assert "resume it with --cap 20" in refusal
    assert manifest.read_bytes() == held
    assert main(_launch_argv(tmp_path, "credit_snapshot", "--cap", "20")) == 0


def test_start_up_refuses_a_cap_table_above_the_ruled_figures(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ruled figures are written twice (`startup.RULED_CAPS_USD`): raising one in the table
    alone, or adding a pathway with no ruled figure, stops the service from starting."""
    from deploy_workflow.inbox import startup
    from deploy_workflow.inbox.scheduler import StartupRefused

    assert startup.RULED_CAPS_USD == {p: int(c) for p, c in CAPS.items()}  # CAPS is hand-written
    Scheduler(settings(root)).close()
    for pathway, cap, words in (
        (
            "lite_credit_assessment",
            D(400),
            "lite_credit_assessment cap USD 400 is above the ruled USD 15",
        ),
        (DEEP, D("40.01"), "deep_credit_assessment cap USD 40.01 is above the ruled USD 40"),
        ("new_pathway", D(5), "new_pathway cap USD 5 has no ruled figure"),
        ("credit_snapshot", D("NaN"), "credit_snapshot cap USD NaN is above the ruled USD 25"),
    ):
        monkeypatch.setattr(startup, "PATHWAY_CAP_USD", {**CAPS, pathway: cap})
        with pytest.raises(StartupRefused, match=words):
            Scheduler(settings(root))
    monkeypatch.setattr(startup, "PATHWAY_CAP_USD", {**CAPS, DEEP: D(30)})  # lower is allowed
    Scheduler(settings(root)).close()
