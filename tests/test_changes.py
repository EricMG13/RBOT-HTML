"""CP-8 in a run: which earlier run it compares with, what only it is given, the comparison pack
Python computes, and the check of its handoff. Synthetic and hand-written: every expected value
below was written from the fixtures by hand, not computed by the code under test. A fake provider
proves wiring only, not analytical quality."""

import hashlib
import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest
from library_fixtures import make_run, method
from test_cpos_launch import (
    AS_OF,
    ISSUER,
    PATHWAY_MODULES,
    ROOT,
    RULING,
    context_file,
    covenant_answer,
    issuer_folder,
    prepare_routes,
    provider,
)

from deploy_workflow import library_index
from deploy_workflow.changes import (
    FIRST_RUN,
    build_pack,
    find_prior,
    observations,
    workspace_of,
)
from deploy_workflow.changes_check import cp8_issues
from deploy_workflow.owners.cpos import HandoffPlan
from deploy_workflow.owners.cpos_launch import LaunchRefused, main, prepare
from deploy_workflow.prose_checks import bottom_line_text, is_earlier_format

SNAPSHOT_MODULES = PATHWAY_MODULES["credit_snapshot"]
PRIOR_ID = "prior-1"
PATHWAY = "credit_snapshot"  # its CP-1 states the leverage, cover and liquidity tables


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def tree(folder: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()
    }


# --- the prior run: one rule ----------------------------------------------------------------------


def test_the_prior_run_is_the_latest_listed_run_of_the_same_issuer_and_pathway_on_or_before(
    tmp_path,
):
    make_run(tmp_path, "a-dec", as_of="2024-12-31")
    make_run(tmp_path, "b-mar", as_of="2025-03-31")
    make_run(tmp_path, "c-jun", as_of="2025-06-30")  # later than the current run
    make_run(tmp_path, "d-other-issuer", as_of="2025-03-30", issuer_id="other")
    make_run(tmp_path, "e-other-pathway", as_of="2025-03-30", pathway="earnings_update")
    make_run(tmp_path, "f-replayed", as_of="2025-03-30", execution="retained-response-replay")

    def prior(as_of: str, folder: str = "cur") -> str | None:
        found = find_prior(
            tmp_path,
            folder=folder,
            issuer_id="nbg",
            pathway="credit_snapshot",
            as_of=as_of,
            method=method(),
        )
        return None if found is None else found[0].folder

    assert prior("2025-03-31") == "b-mar"  # the same as-of date counts as "on or before"
    assert (
        prior("2025-03-30") == "a-dec"
    )  # the other issuer, other pathway and replayed run are not candidates
    assert prior("2025-07-01") == "c-jun"
    assert prior("2024-12-30") is None
    assert prior("2025-03-31", folder="b-mar") == "a-dec"  # never the run itself


def test_runs_of_one_as_of_date_are_ordered_by_their_first_call(tmp_path):
    make_run(tmp_path, "x-early", as_of="2025-03-31", first_call="2026-11-01T09:00:00Z")
    make_run(tmp_path, "a-late", as_of="2025-03-31", first_call="2026-11-05T09:00:00Z")
    found = find_prior(
        tmp_path,
        folder="cur",
        issuer_id="nbg",
        pathway="credit_snapshot",
        as_of="2025-03-31",
        method=method(),
    )
    assert found is not None
    assert found[0].folder == "a-late"  # started later, though its name sorts first
    assert found[0].started_at == "2026-11-05T09:00:00Z"


def test_an_earlier_format_run_is_found_with_its_delivered_handoffs_and_flagged(tmp_path):
    run_dir = make_run(tmp_path, "old", as_of="2024-12-31")
    found = find_prior(
        tmp_path,
        folder="cur",
        issuer_id="nbg",
        pathway="credit_snapshot",
        as_of="2025-03-31",
        method=method("changed"),  # the method since changed: the library marks it
    )
    assert found is not None
    prior, handoffs = found
    assert prior.earlier_format is True  # its handoffs open with a Reader summary
    assert prior.methods_changed != ()
    assert prior.modules == ("CP-0", "CP-1")
    (delivered,) = (run_dir / "deliveries").iterdir()
    assert handoffs == {m: (delivered / f"{m}.md").read_bytes() for m in ("CP-0", "CP-1")}


def test_the_workspace_is_the_folder_holding_runs():
    assert workspace_of(Path("/w/runs/r1")) == Path("/w")
    assert workspace_of(Path("/w/out")) is None


# --- prepare: pins, CP-8 last, first run, resume ----------------------------------------


def snapshot_context(tmp_path: Path, pathway: str = PATHWAY) -> tuple[Path, Path]:
    return context_file(tmp_path, pathway), issuer_folder(tmp_path)


def test_a_listed_prior_run_pins_its_handoffs_for_cp8_and_cp8_runs_last(tmp_path):
    workspace = tmp_path / "ws"
    run_dir = make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    before = tree(run_dir)
    context, folder = snapshot_context(tmp_path)
    prepared = prepare(context, folder, workspace / "runs/cur", config="sol-medium", cap="50")
    assert prepared.ordered == (*SNAPSHOT_MODULES, "CP-8")
    assert prepared.plan.run.requested_modules[-1] == "CP-8"
    (delivered,) = (run_dir / "deliveries").iterdir()
    pins = {n: s for n, s in prepared.plan.sources.items() if n.startswith("prior/")}
    assert set(pins) == {"prior/CP-0.md", "prior/CP-1.md"}
    for name, pin in pins.items():
        raw = (delivered / name.removeprefix("prior/")).read_bytes()
        assert pin.sha256 == sha(raw)
        assert (workspace / "runs/cur" / pin.path).read_bytes() == raw
    assert prepared.plan.prior is not None
    assert (prepared.plan.prior.folder, prepared.plan.prior.as_of) == (PRIOR_ID, "2024-12-31")
    assert prepared.changes.startswith("changes: CP-8 compares with the credit_snapshot run")
    assert "earlier format" in prepared.changes
    assert tree(run_dir) == before  # the prior run's folder is read, never written


def test_no_earlier_run_means_no_cp8_and_a_recorded_first_run(tmp_path):
    (tmp_path / "ws/runs").mkdir(parents=True)
    make_run(tmp_path / "ws", "other-pathway", as_of="2024-12-31", pathway="earnings_update")
    context, folder = snapshot_context(tmp_path)
    prepared = prepare(context, folder, tmp_path / "ws/runs/cur", config="sol-medium", cap="50")
    assert prepared.ordered == SNAPSHOT_MODULES
    assert prepared.prior is None
    assert prepared.plan.changes_note == f"changes: {FIRST_RUN}"
    assert not [n for n in prepared.plan.sources if n.startswith("prior/")]


def test_a_run_folder_outside_a_runs_folder_says_nothing_was_compared(tmp_path):
    context, folder = snapshot_context(tmp_path)
    prepared = prepare(context, folder, tmp_path / "out", config="sol-medium", cap="50")
    assert "CP-8" not in prepared.ordered
    assert prepared.plan.changes_note == (
        "changes: not compared: the run folder is not inside a runs folder"
    )


def test_an_explicit_workspace_serves_a_run_folder_that_is_elsewhere(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    prepared = prepare(
        context,
        folder,
        tmp_path / "summary/run",
        config="sol-medium",
        cap="50",
        workspace=workspace,
    )
    assert prepared.ordered[-1] == "CP-8"


def test_cp8_cannot_be_selected(tmp_path, capsys):
    context, folder = snapshot_context(tmp_path)
    with pytest.raises(LaunchRefused, match="CP-8 is planned automatically"):
        prepare(
            context,
            folder,
            tmp_path / "out",
            config="sol-medium",
            cap="50",
            modules=("CP-4", "CP-8"),
        )
    assert not (tmp_path / "out").exists()


def test_the_offline_cap_check_holds_cp8s_call_when_it_is_planned(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    prepared = prepare(context, folder, workspace / "runs/cur", config="sol-medium", cap="50")
    sizes = {
        m: (workspace / "runs/cur" / spec.path).stat().st_size
        for m, spec in prepared.plan.instructions.items()
    }
    assert (
        "CP-8" in sizes
    )  # its instructions exist, so its call is among those the hold is sized by
    assert prepared.hold > 0


def test_cp8s_instructions_carry_the_method_and_the_earlier_run(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    prepared = prepare(context, folder, workspace / "runs/cur", config="sol-medium", cap="50")
    text = (workspace / "runs/cur" / prepared.plan.instructions["CP-8"].path).read_text()
    assert "### What changed: the issuer" in text
    assert "### Limitations ledger" in text
    assert "source `changes.json`" in text
    assert "the credit_snapshot run as of 2024-12-31" in text
    others = [
        (workspace / "runs/cur" / spec.path).read_text()
        for m, spec in prepared.plan.instructions.items()
        if m != "CP-8"
    ]
    assert not any("changes.json" in t for t in others)


def test_a_resume_keeps_its_pins_when_a_newer_run_has_appeared(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    out = workspace / "runs/cur"
    first = prepare(context, folder, out, config="sol-medium", cap="50")
    manifest = (out / "workflow.json").read_bytes()
    make_run(workspace, "newer", as_of="2025-02-28", pathway=PATHWAY)
    again = prepare(context, folder, out, config="sol-medium", cap="50")  # not refused
    assert (out / "workflow.json").read_bytes() == manifest
    assert again.prior == first.prior
    assert again.prior is not None
    assert again.prior.folder == PRIOR_ID
    # A fresh run folder meets the newer run.
    fresh = prepare(context, folder, workspace / "runs/cur2", config="sol-medium", cap="50")
    assert fresh.prior is not None
    assert fresh.prior.folder == "newer"


def test_a_resume_refuses_a_pinned_copy_that_changed(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    out = workspace / "runs/cur"
    prepare(context, folder, out, config="sol-medium", cap="50")
    (out / "prior/CP-1.md").write_bytes(b"changed")
    with pytest.raises(LaunchRefused, match="pinned earlier handoff prior/CP-1.md changed"):
        prepare(context, folder, out, config="sol-medium", cap="50")


def test_an_issuer_file_cannot_take_a_prior_source_name(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    (folder / "prior").mkdir()
    (folder / "prior/CP-1.md").write_text("Net sales were 100.")
    with pytest.raises(LaunchRefused, match="prior/CP-1.md"):
        prepare(context, folder, workspace / "runs/cur", config="sol-medium", cap="50")


def test_a_manifest_that_names_prior_sources_without_a_prior_run_is_refused(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    prepared = prepare(context, folder, workspace / "runs/cur", config="sol-medium", cap="50")
    document = json.loads(prepared.plan.model_dump_json())
    del document["prior"]
    with pytest.raises(ValueError, match="cpos_prior"):
        HandoffPlan.model_validate_json(json.dumps(document))


# --- the pack -------------------------------------------------------------------------------------


def handoff(
    module: str, bottom: str, limitations: str = "- No limitation changes it.", tables: str = ""
) -> str:
    return (
        f"# {module}\n\n## Request\n\n{ISSUER} as of {AS_OF}.\n\n## Sources\n\nNone.\n\n"
        f"## Findings\n\n### Bottom line\n\n{bottom}\n\n### Key findings\n\nA finding.\n\n"
        "### Contrary evidence and what would change the view\n\nNothing.\n\n"
        f"### Limitations\n\n{limitations}\n\n{tables}\n"
        "## Calculations\n\nNone.\n\n## Gaps\n\nNone.\n\n## Next module\n\nNone.\n"
    )


def earlier_handoff(module: str, bottom: str, limitation: str) -> str:
    return (
        f"# {module}\n\n## Request\n\n{ISSUER}.\n\n## Findings\n\n### Reader summary\n\n"
        f"| Bottom line | Confidence | Main limitation |\n| --- | --- | --- |\n"
        f"| {bottom} | Medium | {limitation} |\n\n"
        "| Finding | Creditor impact | Confidence |\n| --- | --- | --- |\n| One. | Two. | Low |\n\n"
        "## Sources\n\nNone.\n"
    )


def leverage(*rows: str) -> str:
    return (
        "### Chart data: leverage\n\n"
        "| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit "
        "| Basis and limitation |\n"
        "| --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n\n"
    )


def liquidity(row: str) -> str:
    return (
        "### Chart data: liquidity\n\n"
        "| Period | Cash | Undrawn committed facilities | Reporting unit | Basis and limitation |\n"
        f"| --- | --- | --- | --- | --- |\n{row}\n\n"
    )


def maturities(*rows: str) -> str:
    return (
        "### Chart data: debt maturities\n\n"
        "| Period | Debt maturing | Reporting unit | Basis and limitation |\n"
        "| --- | --- | --- | --- |\n" + "\n".join(rows) + "\n\n"
    )


def balance(debt: str, net: str, fcf: str, period: str, label: str = "Total debt") -> str:
    return (
        f"### Reported balance sheet\n\n| Line item | FY2022 | {period} | Reporting unit |\n"
        "| --- | --- | --- | --- |\n"
        f"| {label} | 1 | {debt} | US$m |\n| Net debt | 1 | {net} | US$m |\n"
        f"| Free cash flow | 1 | {fcf} | US$m |\n\n"
    )


MEASURE_KEYS = [
    "leverage",
    "net_leverage",
    "coverage",
    "cash",
    "undrawn",
    "free_cash_flow",
    "gross_debt",
    "net_debt",
]


def measures_of(pack: dict) -> dict[str, dict]:
    return {m["key"]: m for m in pack["measures"]}


def pair_pack(prior_cp1: str, current_cp1: str) -> dict:
    return build_pack(
        _prior(),
        {"CP-1": prior_cp1},
        {"CP-1": current_cp1},
        as_of="2025-03-31",
        pathway="credit_snapshot",
    )


def _prior():
    from deploy_workflow.changes import PriorRun

    return PriorRun(
        folder="p",
        run_id="nbg-2024-12-31-credit_snapshot",
        as_of="2024-12-31",
        pathway="credit_snapshot",
        earlier_format=False,
        methods_changed=(),
        started_at=None,
        modules=("CP-1",),
    )


def test_the_pack_computes_differences_and_marks_what_cannot_be_compared():
    prior = handoff(
        "CP-1",
        "Earlier.",
        tables=leverage(
            "| FY2022 | 4.60 | 4.10 | x | Reported. |",
            "| FY2023 | 4.20 | Not supplied: not stated | x | Reported. |",
        )
        + liquidity("| FY2023 | 300 | 450 | US$m | Cash excluding restricted cash. |")
        + maturities("| FY2026 | 500 | US$m | Schedule. |", "| FY2027 | 100 | US$m | Schedule. |")
        + balance("2,100", "1,800", "60", "FY2023"),
    )
    current = handoff(
        "CP-1",
        "Now.",
        tables=leverage("| FY2024 | 3.60 | 3.25 | x | Reported. |")
        + "### Chart data: interest cover\n\n"
        "| Period | EBITDA / cash interest | Reporting unit | Basis and limitation |\n"
        "| --- | --- | --- | --- |\n| FY2024 | 3.40 | x | Reported. |\n\n"
        + liquidity("| FY2024 | 250 | 400 | US$m | Cash on another basis. |")
        + maturities(
            "| FY2026 | 450 | US$m | Schedule. |",
            "| FY2027 | Not supplied: the schedule ends | US$m | Schedule. |",
            "| FY2028 | 1,250 | US$m | Schedule. |",
        )
        + balance("2,000", "1,750", "70", "FY2024", label="Gross debt"),
    )
    pack = pair_pack(prior, current)
    found = measures_of(pack)
    assert [m["key"] for m in pack["measures"]] == MEASURE_KEYS
    # Same definition: Python's difference, 3.60 - 4.20.
    assert found["leverage"]["comparable"] is True
    assert (found["leverage"]["prior"]["value"], found["leverage"]["current"]["value"]) == (
        "4.20",
        "3.60",
    )
    assert (found["leverage"]["prior"]["period"], found["leverage"]["current"]["period"]) == (
        "FY2023",
        "FY2024",
    )
    assert found["leverage"]["difference"] == "-0.60"
    # A missing value stays missing, never zero, and gives no difference.
    assert found["net_leverage"]["prior"]["value"] is None
    assert found["net_leverage"]["current"]["value"] == "3.25"
    assert found["net_leverage"]["difference"] is None
    assert found["net_leverage"]["reason"] == "a value is not stated"
    # Present in one run only.
    assert found["coverage"]["prior"] is None
    assert found["coverage"]["current"]["value"] == "3.40"
    assert (found["coverage"]["comparable"], found["coverage"]["difference"]) == (False, None)
    assert found["coverage"]["reason"] == "the earlier run does not state it"
    # A definition text that differs: both values, no difference.
    assert found["cash"]["comparable"] is False
    assert found["cash"]["reason"] == "the definition text differs"
    assert (found["cash"]["prior"]["value"], found["cash"]["current"]["value"]) == ("300", "250")
    assert found["cash"]["difference"] is None
    assert found["undrawn"]["comparable"] is False
    # Rows read from CP-1's tables when they state a unit: free cash flow, and a label that differs.
    assert found["free_cash_flow"]["difference"] == "10"
    assert found["gross_debt"]["comparable"] is False
    assert found["gross_debt"]["reason"] == "the label differs"
    assert (found["net_debt"]["prior"]["value"], found["net_debt"]["current"]["value"]) == (
        "1,800",
        "1,750",
    )
    assert found["net_debt"]["difference"] == "-50"
    assert found["net_debt"]["unit"] == "US$m"
    # The bridge is left out with its reason; the maturity profile is built.
    assert "net_debt_bridge" not in pack
    assert pack["omitted"] == {
        "net_debt_bridge": "gross debt cannot be compared (the label differs)"
    }
    assert pack["maturity_profile"] == {
        "unit": "US$m",
        "rows": [
            {"period": "FY2026", "prior": "500", "current": "450", "difference": "-50"},
            {"period": "FY2027", "prior": "100", "current": None, "difference": None},
            {"period": "FY2028", "prior": None, "current": "1,250", "difference": None},
        ],
    }


def bridge_pack(
    prior_net: str = "1,800", current_net: str = "1,750", cash_basis: str = "Cash."
) -> dict:
    prior = handoff(
        "CP-1",
        "Earlier.",
        tables=liquidity(f"| FY2023 | 300 | 450 | US$m | {cash_basis} |")
        + balance("2,100", prior_net, "60", "FY2023"),
    )
    current = handoff(
        "CP-1",
        "Now.",
        tables=liquidity("| FY2024 | 250 | 400 | US$m | Cash. |")
        + balance("2,000", current_net, "70", "FY2024"),
    )
    return pair_pack(prior, current)


def test_the_net_debt_bridge_is_built_when_both_runs_state_it_under_one_definition():
    pack = bridge_pack()
    # 1,800 = 2,100 - 300 and 1,750 = 2,000 - 250; gross fell 100, cash fell 50.
    assert pack["net_debt_bridge"] == {
        "unit": "US$m",
        "prior_net_debt": "1800",
        "change_in_gross_debt": "-100",
        "change_in_cash": "-50",
        "current_net_debt": "1750",
    }
    assert pack["omitted"] == {
        "maturity_profile": "a run has no debt maturities table with one unit"
    }


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"current_net": "1,700"}, "a run's net debt is not its gross debt less its cash"),
        (
            {"cash_basis": "Cash excluding restricted cash."},
            "cash cannot be compared (the definition text differs)",
        ),
    ],
)
def test_the_net_debt_bridge_is_omitted_with_its_reason(kwargs, reason):
    pack = bridge_pack(**kwargs)
    assert "net_debt_bridge" not in pack
    assert pack["omitted"]["net_debt_bridge"] == reason


def test_the_pack_lists_every_module_and_limitation_of_either_run():
    prior = {
        "CP-1": handoff(
            "CP-1",
            "Earlier data view.",
            "- Segment data is not supplied, so segment margins are not assessed.",
        ),
        "CP-2": earlier_handoff("CP-2", "Old CP-2 view.", "Old limitation text."),
        "CP-DR": handoff(
            "CP-DR", "Old research view.", "- No limitation changes the conclusions of research."
        ),
    }
    current = {
        "CP-1": handoff(
            "CP-1",
            "Current data view.",
            "- Segment data is not supplied so segment margins are not assessed",
        ),
        "CP-2": handoff(
            "CP-2",
            "The current credit view is stronger.\nBasis: annual.txt, page 2",
            "- The covenant package is not supplied, so covenant headroom is unknown.\n"
            "- No limitation changes the conclusions of the credit view.",
        ),
        "CP-2E": handoff("CP-2E", "Macro view."),
    }
    pack = build_pack(_prior(), prior, current, as_of="2025-03-31", pathway="credit_snapshot")
    assert pack["schema"] == "cpos-changes/1"
    assert pack["prior"] == {
        "run": "p",
        "as_of": "2024-12-31",
        "pathway": "credit_snapshot",
        "format": "current",
        "methods_changed": [],
    }
    assert pack["current"] == {
        "as_of": "2025-03-31",
        "pathway": "credit_snapshot",
        "format": "current",
    }
    assert pack["modules"] == [
        {
            "module": "CP-1",
            "title": "Canonical data foundation",
            "ran_prior": True,
            "ran_current": True,
            "prior_bottom_line": "Earlier data view.",
            "current_bottom_line": "Current data view.",
        },
        {
            "module": "CP-2",
            "title": "Fundamental credit synthesizer",
            "ran_prior": True,
            "ran_current": True,
            "prior_bottom_line": "Old CP-2 view.",  # earlier format: the Reader summary cell
            "current_bottom_line": "The current credit view is stronger.",  # Basis line dropped
        },
        {
            "module": "CP-2E",
            "title": "Macro fx hedging sensitivity",
            "ran_prior": False,
            "ran_current": True,
            "prior_bottom_line": None,
            "current_bottom_line": "Macro view.",
        },
        {
            "module": "CP-DR",
            "title": "Deep research",
            "ran_prior": True,
            "ran_current": False,
            "prior_bottom_line": "Old research view.",
            "current_bottom_line": None,
        },
    ]
    assert pack["limitations"] == [
        {
            "key": "segment data is not supplied so segment margins are not assessed",
            "text": "Segment data is not supplied so segment margins are not assessed",
            "modules": ["CP-1"],
            "prior": True,
            "current": True,
        },
        {
            "key": "old limitation text",
            "text": "Old limitation text.",
            "modules": ["CP-2"],
            "prior": True,
            "current": False,
        },
        {
            "key": "the covenant package is not supplied so covenant headroom is unknown",
            "text": "The covenant package is not supplied, so covenant headroom is unknown.",
            "modules": ["CP-2"],
            "prior": False,
            "current": True,
        },
    ]


def test_a_prior_cp8_handoff_is_not_compared():
    pack = build_pack(
        _prior(),
        {"CP-8": handoff("CP-8", "Earlier changes.")},
        {"CP-1": handoff("CP-1", "Now.")},
        as_of="2025-03-31",
        pathway="credit_snapshot",
    )
    assert [m["module"] for m in pack["modules"]] == ["CP-1"]


def test_an_ambiguous_or_unitless_row_is_not_a_measure():
    twice = handoff(
        "CP-1",
        "x",
        tables=balance("2,100", "1,800", "60", "FY2023")
        + balance("2,200", "1,900", "70", "FY2023"),
    )
    assert "net_debt" not in observations(twice)  # two rows of one label: not guessed
    unitless = "## Findings\n\n| Line item | FY2023 |\n| --- | --- |\n| Net debt | 1,800 |\n"
    assert observations(unitless) == {}


def test_the_bottom_line_and_format_helpers():
    new = handoff("CP-2", "First paragraph here.\nStill the first.\n\nSecond paragraph.")
    assert bottom_line_text(new) == "First paragraph here. Still the first."
    assert is_earlier_format(new) is False
    old = earlier_handoff("CP-2", "Old.", "Lim.")
    assert is_earlier_format(old) is True
    assert bottom_line_text(old) is None


# --- the checker ----------------------------------------------------------------------------------

LEVERAGE_PRIOR = {
    "label": "Total debt / EBITDA",
    "unit": "x",
    "value": "4.20",
    "period": "FY2023",
    "definition": None,
}
CASH_PRIOR = {
    "label": "Cash",
    "unit": "US$m",
    "value": "300",
    "period": "FY2023",
    "definition": "Cash.",
}
PACK = {
    "measures": [
        {
            "key": "leverage",
            "label": "Total debt / EBITDA",
            "comparable": True,
            "reason": None,
            "prior": LEVERAGE_PRIOR,
            "current": {**LEVERAGE_PRIOR, "value": "3.60", "period": "FY2024"},
            "difference": "-0.60",
        },
        {
            "key": "cash",
            "label": "Cash",
            "comparable": False,
            "reason": "the definition text differs",
            "prior": CASH_PRIOR,
            "current": {**CASH_PRIOR, "value": "250", "period": "FY2024", "definition": "Other."},
            "difference": None,
        },
    ],
    "modules": [
        {"module": "CP-2", "ran_prior": True, "ran_current": True},
        {"module": "CP-DR", "ran_prior": True, "ran_current": False},
        {"module": "CP-2E", "ran_prior": False, "ran_current": True},
    ],
    "limitations": [
        {
            "key": "old limitation text",
            "text": "Old limitation text.",
            "prior": True,
            "current": False,
        },
        {"key": "new one", "text": "New one.", "prior": False, "current": True},
        {"key": "both", "text": "Both.", "prior": True, "current": True},
    ],
}
REGISTERS = """## Findings

### What changed: the issuer

| Measure or fact | Earlier | Current | Cause | Effect on the credit view |
| --- | --- | --- | --- | --- |
| Total debt / EBITDA | 4.20x (FY2023) | 3.60x (FY2024) | New period | Leverage fell by 0.60x. |
| Cash | 300 US$m (FY2023) | 250 US$m (FY2024) | New period | Not comparable: definition differs. |

### What changed: the analysis

| Module | Status | Cause | Why |
| --- | --- | --- | --- |
| Credit view (CP-2) | Strengthened | New period | Leverage fell. |
| Research (CP-DR) | Not run this time | Method change | The research module was not selected. |
| Macro (CP-2E) | New | New source | The module was added. |

### Limitations ledger

| Limitation | Status | What closed it |
| --- | --- | --- |
| Old limitation text. | Closed | The Macro handoff (CP-2E) now shows the package. |
| New one. | New | — |
| Both. | Remaining | — |

## Calculations
"""


def issues_after(old: str, new: str) -> tuple[str, ...]:
    assert old in REGISTERS
    return cp8_issues(REGISTERS.replace(old, new, 1), PACK)


def test_a_complete_cp8_handoff_is_accepted():
    assert cp8_issues(REGISTERS, PACK) == ()


@pytest.mark.parametrize(
    ("old", "new", "fragment"),
    [
        ("3.60x (FY2024)", "3.70x (FY2024)", "3.70"),  # a figure the pack does not hold
        ("4.20x (FY2023)", "4.30x (FY2023)", "4.30"),
        ("by 0.60x", "by 0.65x", "0.65"),  # a difference Python did not compute
        (
            "definition differs.",
            "definition differs, so cash fell by 50 US$m.",
            "50",
        ),  # a difference for a not-comparable measure
        ("| Not comparable: definition", "| Definition", "not comparable"),
        (
            "| New period | Leverage fell by",
            "| Method change | Leverage fell by",
            "Method change",
        ),  # an analysis cause in the issuer register
        ("Strengthened | New period", "Strengthened | Presentation", "Presentation"),
        ("Strengthened", "Improved", "Improved"),  # a status outside the fixed list
        (
            "| New | New source |",
            "| Strengthened | New source |",
            "CP-2E",
        ),  # a module that did not run before
        ("| Not run this time |", "| Weakened |", "CP-DR"),
        (
            "| Credit view (CP-2) | Strengthened",
            "| Credit view | Strengthened",
            "does not name one module",
        ),
        (
            "| New source | The module was added.",
            "| Wrong cause | The module was added.",
            "Wrong cause",
        ),
        (
            "| Old limitation text. | Closed | The Macro handoff (CP-2E) now shows the package. |",
            "| Old limitation text. | Closed | — |",
            "Closed",
        ),
        (
            "(CP-2E) now shows",
            "(CP-DR) now shows",
            "Closed",
        ),  # evidence must be a module of the current run
        ("The Macro handoff (CP-2E) now shows the package.", "Resolved.", "Closed"),
        ("| New one. | New |", "| New one. | Remaining |", "the pack says New"),
        ("| Both. | Remaining |", "| Both. | Closed |", "the pack says Remaining"),
        ("| Both. | Remaining |", "| Both. | Unknown |", "Unknown"),
        ("| Old limitation text. |", "| Some other limitation. |", "not a limitation in the pack"),
    ],
)
def test_the_checker_refuses_each_broken_cp8_handoff(old, new, fragment):
    found = issues_after(old, new)
    assert found, "accepted"
    assert any(fragment.lower() in issue.lower() for issue in found), found


def test_a_missing_module_row_a_duplicate_row_and_a_missing_ledger_row_are_refused():
    macro = "| Macro (CP-2E) | New | New source | The module was added. |\n"
    assert any("CP-2E needs exactly one row (found 0)" in i for i in issues_after(macro, ""))
    assert any(
        "CP-2E needs exactly one row (found 2)" in i for i in issues_after(macro, macro + macro)
    )
    both = "| Both. | Remaining | — |\n"
    assert any("needs exactly one row (found 0)" in i for i in issues_after(both, ""))
    assert any("needs exactly one row (found 2)" in i for i in issues_after(both, both + both))


@pytest.mark.parametrize(
    ("old", "new", "fragment"),
    [
        ("### What changed: the issuer", "### What changed: the lot", "exactly once"),
        ("| Measure or fact | Earlier |", "| Measure | Earlier |", "exactly these columns"),
    ],
)
def test_a_register_that_is_missing_or_has_other_columns_is_refused(old, new, fragment):
    found = issues_after(old, new)
    assert any(fragment in issue for issue in found), found


def test_a_register_with_a_header_and_no_row_or_no_table_is_refused():
    cut = REGISTERS[: REGISTERS.index("| Old limitation text.")] + "\n## Calculations\n"
    assert any("needs exactly one row" in i for i in cp8_issues(cut, PACK))
    bare = REGISTERS[: REGISTERS.index("| Limitation | Status")] + "\n## Calculations\n"
    assert any("holds no table" in i for i in cp8_issues(bare, PACK))


def test_a_row_for_no_material_change_is_accepted_with_cause_none():
    text = REGISTERS.replace(
        REGISTERS[
            REGISTERS.index("| Total debt") : REGISTERS.index("### What changed: the analysis")
        ],
        "| No material change | — | — | None | Nothing material moved. |\n\n",
    )
    assert cp8_issues(text, PACK) == ()


# --- a run: isolation, the pack in the delivery, CP-8 accepted -------------------------

PRIOR_TABLES = (
    "\n### Chart data: leverage\n\n"
    "| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit | Basis and limitation |\n"
    "| --- | --- | --- | --- | --- |\n| FY2023 | 4.20 | 3.85 | x | Synthetic. |\n\n"
    "### Chart data: liquidity\n\n"
    "| Period | Cash | Undrawn committed facilities | Reporting unit | Basis and limitation |\n"
    "| --- | --- | --- | --- | --- |\n| FY2023 | 300 | 450 | US$m | Earlier basis. |\n"
)
LIMITATION_LINE = re.compile(r"^- (Synthetic data only in the .*)$", re.MULTILINE)


def cp8_answer(context: dict) -> str:
    """CP-8's answer to the pair of runs below, hand-written. The ledger rows are read off the
    handoffs CP-OS supplied (every current limitation is new; the earlier one is not stated)."""
    modules = list(context["handoffs"])
    lines = ["# CP-8", "", "## Request", f"{ISSUER} as of {AS_OF}.", "", "## Sources", ""]
    lines += [f"- {n} {h}" for n, h in context["sources"].items()]
    lines += [f"- {n} {h['sha256']}" for n, h in context["handoffs"].items()]
    lines += [
        "",
        "## Findings",
        "",
        "### Bottom line",
        "",
        (
            "Credit metrics improved since the earlier run, which eases creditor exposure, "
            "and the change is the issuer's, not the analysis'."
        ),
        "",
        "### Key findings",
        "",
        "Leverage fell from 4.20x to 3.60x because a new period was reported.",
        "",
        "### Contrary evidence and what would change the view",
        "",
        "Nothing in the comparison contradicts the view; a weaker cash position would.",
        "",
        "### Limitations",
        "",
        "- The earlier run was in the earlier format, so wording differences are not compared.",
        "",
        "### What changed: the issuer",
        "",
        "| Measure or fact | Earlier | Current | Cause | Effect on the credit view |",
        "| --- | --- | --- | --- | --- |",
        (
            "| Total debt / EBITDA | 4.20x (FY2023) | 3.60x (FY2024) | New period "
            "| Leverage fell by 0.60x. |"
        ),
        (
            "| Net debt / EBITDA | 3.85x (FY2023) | 3.25x (FY2024) | New period "
            "| Net leverage fell by 0.60x. |"
        ),
        (
            "| Cash | 300 US$m (FY2023) | 275 US$m (FY2024) | Unresolved "
            "| Not comparable: definition differs. |"
        ),
        "",
        "### What changed: the analysis",
        "",
        "| Module | Status | Cause | Why |",
        "| --- | --- | --- | --- |",
    ]
    for module in modules:
        old = module in ("CP-0", "CP-1")
        lines.append(
            f"| Module ({module}) | {'Unchanged' if old else 'New'} | "
            f"{'Presentation' if old else 'Method change'} | "
            f"{'Only the format differs.' if old else 'The earlier run did not include it.'} |"
        )
    lines += [
        "",
        "### Limitations ledger",
        "",
        "| Limitation | Status | What closed it |",
        "| --- | --- | --- |",
        "| Synthetic fixture only. | No longer stated | — |",
    ]
    for module in modules:
        for text in LIMITATION_LINE.findall(context["handoffs"][module]["markdown"]):
            lines.append(f"| {text} | New | — |")
    lines += [
        "",
        "## Calculations",
        "",
        "None.",
        "",
        "## Gaps",
        "",
        "None.",
        "",
        "## Next module",
        "",
        "None.",
        "",
    ]
    return "\n".join(lines)


def run_with_prior(tmp_path: Path) -> tuple[Path, Path, list[str]]:
    workspace = tmp_path / "ws"
    make_run(
        workspace,
        PRIOR_ID,
        as_of="2024-12-31",
        pathway=PATHWAY,
        cp1_extra=PRIOR_TABLES,
    )
    context, folder = snapshot_context(tmp_path)
    routes = prepare_routes(tmp_path, "sol-medium", modules=None)
    out = workspace / "runs/cur"
    argv = [
        *("--context", str(context), "--sources", str(folder)),
        *("--config", "sol-medium", "--cap", "50", "--out", str(out)),
        *("--live", "--ruling", str(RULING), "--no-library"),
    ]
    provider.answer = lambda context: (
        cp8_answer(context) if context["module_id"] == "CP-8" else covenant_answer(context, routes)
    )
    return workspace, out, argv


@pytest.mark.usefixtures("provider")
def test_a_run_with_a_prior_run_gives_cp8_alone_the_earlier_handoffs_and_delivers_the_pack(
    tmp_path,
):
    workspace, out, argv = run_with_prior(tmp_path)
    assert main(argv) == 0
    assert tuple(c[0] for c in provider.calls) == (*SNAPSHOT_MODULES, "CP-8")

    # What each module was sent: the earlier run's handoffs and the pack reach CP-8 only.
    sent = {}
    for record in (out / "requests").glob("*/*/1.request.json"):
        asked = json.loads(record.read_text())
        sent[asked["module_id"]] = set(asked["sources"])
    assert set(sent) == {*SNAPSHOT_MODULES, "CP-8"}
    for module, names in sent.items():
        held = {n for n in names if n.startswith("prior/") or n == "changes.json"}
        assert held == (
            {"prior/CP-0.md", "prior/CP-1.md", "changes.json"} if module == "CP-8" else set()
        ), module
    # The delivery carries the pack, byte for byte as CP-8 was given it.
    receipt = next((out / "deliveries").glob("*/delivery.json"))
    pack = json.loads((receipt.parent / "changes.json").read_text())
    assert json.loads(receipt.read_text())["files"]["changes.json"] == sha(
        (receipt.parent / "changes.json").read_bytes()
    )
    assert (out / "inputs" / sha((receipt.parent / "changes.json").read_bytes())).is_file()
    found = measures_of(pack)
    assert (found["leverage"]["difference"], found["net_leverage"]["difference"]) == (
        "-0.60",
        "-0.60",
    )
    assert found["cash"]["comparable"] is False
    assert (found["cash"]["prior"]["value"], found["cash"]["current"]["value"]) == ("300", "275")
    assert found["coverage"]["prior"] is None
    assert pack["prior"]["run"] == PRIOR_ID
    # CP-8's accepted handoff is delivered and recorded.
    assert (receipt.parent / "CP-8.md").is_file()
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["changes"].startswith("changes: CP-8 compares with the credit_snapshot run")
    assert "CP-8" in completed["modules"]
    # The library lists the run with its new module.
    library = library_index.build_library(workspace, workspace / "library")
    listed = {r["id"]: r for r in library.runs}
    assert "cur" in listed, library.excluded
    assert [m["id"] for m in listed["cur"]["modules"]][-1] == "CP-8"


@pytest.mark.usefixtures("provider")
def test_a_wrong_cp8_answer_is_sent_back_and_a_run_that_cannot_fix_it_stops(tmp_path, capsys):
    _, out, argv = run_with_prior(tmp_path)
    good = provider.answer
    provider.answer = lambda context: (
        good(context).replace("3.60x (FY2024)", "3.70x (FY2024)")
        if context["module_id"] == "CP-8"
        else good(context)
    )
    assert main(argv) == 1
    assert "CP-8 not accepted" in capsys.readouterr().err
    # The loop sent it back, naming the figure; no delivery was made.
    sent_back = " ".join(p.read_text() for p in (out / "live/modules").glob("*/*.tools.json"))
    assert "REJECTED" in sent_back
    assert "the figure 3.70 is not in the comparison pack" in sent_back
    assert not (out / "deliveries").exists()


@pytest.mark.usefixtures("provider")
def test_a_relaunch_after_a_newer_run_appeared_resumes_without_a_call(tmp_path):
    workspace, _, argv = run_with_prior(tmp_path)
    assert main(argv) == 0
    sent = list(provider.calls)
    make_run(workspace, "newer", as_of="2025-02-28", pathway=PATHWAY)
    assert main(argv) == 0
    assert provider.calls == sent


@pytest.mark.usefixtures("provider")
def test_a_first_run_delivers_no_pack_and_makes_no_cp8_call(tmp_path):
    workspace = tmp_path / "ws"
    context, folder = snapshot_context(tmp_path)
    routes = prepare_routes(tmp_path, "sol-medium", modules=None)
    out = workspace / "runs/cur"
    provider.answer = lambda context: covenant_answer(context, routes)
    argv = [
        *("--context", str(context), "--sources", str(folder)),
        *("--config", "sol-medium", "--cap", "50", "--out", str(out)),
        *("--live", "--ruling", str(RULING), "--no-library"),
    ]
    assert main(argv) == 0
    assert tuple(c[0] for c in provider.calls) == SNAPSHOT_MODULES
    receipt = next((out / "deliveries").glob("*/delivery.json"))
    assert not (receipt.parent / "changes.json").exists()
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["changes"] == f"changes: {FIRST_RUN}"
    shutil.rmtree(workspace)


def test_the_canned_launcher_delivers_the_pack_and_an_accepted_cp8_handoff(tmp_path, monkeypatch):
    """The suite's canned provider (fixtures/canned_provider_launcher.py) answers CP-8 from the
    pack CP-OS pinned; the real checker accepts it and the delivery carries the pack."""
    spec = importlib.util.spec_from_file_location(
        "canned_provider_launcher", ROOT / "tests/fixtures/canned_provider_launcher.py"
    )
    assert spec is not None and spec.loader is not None
    canned = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(canned)
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY, cp1_extra=PRIOR_TABLES)
    context, folder = snapshot_context(tmp_path)
    out = workspace / "runs/cur"
    argv = [
        *("--context", str(context), "--sources", str(folder)),
        *("--config", "sol-medium", "--cap", "50", "--out", str(out)),
        *("--live", "--ruling", str(RULING), "--no-library"),
    ]
    assert canned.main(argv) == 0
    receipt = next((out / "deliveries").glob("*/delivery.json"))
    pack = json.loads((receipt.parent / "changes.json").read_text())
    assert measures_of(pack)["leverage"]["difference"] == "-0.60"  # hand-written above
    handoff = (receipt.parent / "CP-8.md").read_text()
    assert "| Total debt / EBITDA | 4.20 (FY2023) | 3.60 (FY2024) | New period |" in handoff
    assert "### Limitations ledger" in handoff
