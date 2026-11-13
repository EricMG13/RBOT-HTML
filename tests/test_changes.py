"""CP-8 in a run: which earlier run it compares with, what only it is given, the comparison pack
Python computes, and the check of its handoff. Synthetic and hand-written: every expected value
below was written from the fixtures by hand, not computed by the code under test. A fake provider
proves wiring only, not analytical quality."""

import ast
import dataclasses
import hashlib
import importlib.util
import json
import re
import shutil
from decimal import Decimal
from pathlib import Path

import pytest
from library_fixtures import make_run, method
from test_cpos_launch import (
    AS_OF,
    ISSUER,
    PATHWAY_MODULES,
    ROOT,
    RULING,
    answer,
    context_file,
    covenant_answer,
    good_task,
    issuer_folder,
    prepare_routes,
    provider,
)

from deploy_workflow import library_index
from deploy_workflow.changes import (
    FIRST_RUN,
    _not_a_base,
    build_pack,
    find_prior,
    observations,
    workspace_of,
)
from deploy_workflow.changes_check import cp8_issues, page_verdicts
from deploy_workflow.owners.cpos import HandoffPlan
from deploy_workflow.owners.cpos_launch import LaunchRefused, main, prepare
from deploy_workflow.prose_checks import bottom_line_text, is_earlier_format

SNAPSHOT_MODULES = PATHWAY_MODULES["credit_snapshot"]
PRIOR_ID = "prior-1"
ME = {"issuer_name": "Northbridge Synthetic Group", "case_kind": "public"}  # the fixtures' run
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
            **ME,
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
        **ME,
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
        **ME,
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


def chosen(workspace, skipped=None, *, issuer_id="nbg", only=None, **me):
    found = find_prior(
        workspace,
        folder="cur",
        issuer_id=issuer_id,
        **{**ME, **me},
        pathway="credit_snapshot",
        as_of="2025-03-31",
        method=method(),
        only=only,
        skipped=skipped,
    )
    return None if found is None else found[0].folder


def test_a_prior_run_is_the_same_issuer_name_and_case_kind_and_the_reason_is_recorded(tmp_path):
    make_run(tmp_path, "private", as_of="2024-12-01", case_kind="private")
    make_run(tmp_path, "renamed", as_of="2024-12-02", issuer_name="Some Other Company plc")
    make_run(
        tmp_path,
        "upper",
        as_of="2024-12-03",
        issuer_id="NBG",  # the same ID in another case
        issuer_name="  northbridge   SYNTHETIC group ",  # the same name, folded
    )
    skipped: list[str] = []
    assert chosen(tmp_path, skipped) == "upper"
    assert skipped == [
        "private: its case kind is 'private', not 'public'",
        "renamed: its issuer name is 'Some Other Company plc', not 'Northbridge Synthetic Group'",
    ]
    # A candidate that fails a test is never used, even when it is the only one.
    only_private = tmp_path / "second"
    make_run(only_private, "private", as_of="2024-12-01", case_kind="private")
    assert chosen(only_private) is None


def test_a_run_launched_with_an_explicit_module_subset_is_not_a_comparison_base(tmp_path):
    make_run(tmp_path, "subset", as_of="2024-12-31", selection="explicit")
    make_run(tmp_path, "full", as_of="2024-11-30", selection="preset")
    skipped: list[str] = []
    assert chosen(tmp_path, skipped) == "full"  # though the subset run is the later one
    assert skipped == ["subset: it was launched with an explicit module subset"]


def test_an_older_run_without_a_recorded_selection_is_a_base_only_with_the_leading_module(tmp_path):
    make_run(tmp_path, "old", as_of="2024-12-31", selection=None)  # ran CP-0 and CP-1 only
    skipped: list[str] = []
    assert chosen(tmp_path, skipped) is None
    assert skipped == ["old: it records no module selection and did not run CP-2"]


@pytest.mark.parametrize(
    ("pathway", "lead"),
    [
        ("credit_snapshot", "CP-2"),
        ("covenant_refinancing", "CP-2"),
        ("earnings_update", "CP-1B"),
        ("short_snapshot", "CP-L10"),
    ],
)
def test_the_lead_module_of_each_pathway_decides_an_older_run(pathway, lead):
    me = {"issuer_name": "A", "case_kind": "public", "pathway": pathway}
    run = {"issuer_name": "a", "case_kind": "public"}
    assert _not_a_base({}, run, (lead, "CP-0"), me) is None
    assert (
        _not_a_base({}, run, ("CP-0", "CP-1"), me)
        == f"it records no module selection and did not run {lead}"
    )
    assert _not_a_base({"selection": "preset"}, run, ("CP-0",), me) is None
    assert _not_a_base({"selection": "explicit"}, run, (lead,), me) is not None
    assert "not understood" in (_not_a_base({"selection": "all"}, run, (lead,), me) or "")


def test_a_prior_handoff_that_is_not_utf8_means_no_cp8_and_the_reason_is_recorded(
    tmp_path, monkeypatch
):
    import library_fixtures

    real = library_fixtures.put

    def put(path, raw):
        if path.name == "1.response.md" and "/CP-1/" in str(path):
            raw = raw.replace(
                b"CP-1 bottom line.", b"CP-1 bottom line \xa3."
            )  # a cp1252 pound sign
        return real(path, raw)

    monkeypatch.setattr(library_fixtures, "put", put)
    make_run(tmp_path, "prior", as_of="2024-12-31")
    assert library_index.build_library(
        tmp_path, tmp_path / "library", method()
    ).runs  # it is listed
    skipped: list[str] = []
    assert chosen(tmp_path, skipped) is None
    assert skipped == ["prior: its delivered CP-1 handoff is not valid UTF-8"]


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
    # sol-medium holds its whole 1,050,000-token context at USD 5/M plus 32,000 output tokens at
    # USD 15/M, however long the request: 5.25 + 0.48 (written from the price table by hand).
    assert prepared.hold == Decimal("5.73")


def two_priors(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, "older", as_of="2024-09-30", pathway=PATHWAY)
    make_run(workspace, "newer", as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    return workspace, context, folder


def test_the_run_the_approval_named_is_the_one_compared_with(tmp_path):
    workspace, context, folder = two_priors(tmp_path)
    named = prepare(
        context, folder, workspace / "runs/cur", config="sol-medium", cap="50", prior="older"
    )
    assert named.prior is not None
    assert named.prior.folder == "older"  # not "newer", which a search would find
    searched = prepare(context, folder, workspace / "runs/cur2", config="sol-medium", cap="50")
    assert searched.prior is not None
    assert searched.prior.folder == "newer"


def test_an_approval_that_named_no_earlier_run_is_a_first_run_whatever_is_listed_since(tmp_path):
    workspace, context, folder = two_priors(tmp_path)
    first = prepare(
        context, folder, workspace / "runs/cur", config="sol-medium", cap="50", prior="none"
    )
    assert first.prior is None
    assert "CP-8" not in first.ordered
    assert first.plan.changes_note == f"changes: {FIRST_RUN}"


def test_a_named_run_that_is_no_longer_available_goes_without_cp8_and_says_so(tmp_path):
    workspace, context, folder = two_priors(tmp_path)
    gone = prepare(
        context, folder, workspace / "runs/cur", config="sol-medium", cap="50", prior="deleted"
    )
    assert gone.prior is None
    assert "CP-8" not in gone.ordered
    assert gone.plan.changes_note == (
        "changes: not compared: the earlier run named at approval is no longer available"
    )
    # A named run that is listed but no longer passes the tests is as unavailable, with the reason.
    make_run(workspace, "subset", as_of="2025-01-31", pathway=PATHWAY, selection="explicit")
    out = prepare(
        context, folder, workspace / "runs/cur2", config="sol-medium", cap="50", prior="subset"
    )
    assert out.prior is None
    assert out.plan.changes_note == (
        "changes: not compared: the earlier run named at approval is no longer available "
        "(not used: subset: it was launched with an explicit module subset)"
    )


@pytest.mark.parametrize("name", ["../x", "-x", "a b", "", "--live"])
def test_a_prior_that_is_not_a_run_folder_name_is_refused(tmp_path, name):
    workspace, context, folder = two_priors(tmp_path)
    with pytest.raises(LaunchRefused, match="--prior"):
        prepare(context, folder, workspace / "runs/cur", config="sol-medium", cap="50", prior=name)


def test_the_launcher_takes_the_prior_flag_and_runs_as_it_names(tmp_path, capsys):
    workspace, context, folder = two_priors(tmp_path)

    def launch(name: str, prior: str) -> str:
        argv = [
            *("--context", str(context), "--sources", str(folder)),
            *("--config", "sol-medium", "--cap", "50", "--no-library"),
            *("--out", str(workspace / "runs" / name), "--prior", prior),
        ]
        assert main(argv) == 0
        return capsys.readouterr().out

    assert "CP-8 compares with the credit_snapshot run as of 2024-09-30" in launch("a", "older")
    assert f"Changes:  {FIRST_RUN}" in launch("b", "none")


def test_the_selection_is_recorded_for_a_run_and_left_out_of_an_older_manifest(tmp_path):
    workspace, context, folder = two_priors(tmp_path)
    preset = prepare(context, folder, workspace / "runs/a", config="sol-medium", cap="50")
    assert preset.plan.selection == "preset"
    assert json.loads((workspace / "runs/a/workflow.json").read_text())["selection"] == "preset"
    subset = prepare(
        context,
        folder,
        workspace / "runs/b",
        config="sol-medium",
        cap="50",
        modules=("CP-0", "CP-1"),
    )
    assert subset.plan.selection == "explicit"
    document = json.loads(preset.plan.model_dump_json())
    del document["selection"]
    older = HandoffPlan.model_validate_json(json.dumps(document))
    assert older.selection is None
    assert "selection" not in json.loads(older.model_dump_json())  # an older manifest is unchanged


def test_the_scope_and_omitted_sections_do_not_say_what_changed_was_not_produced_when_cp8_runs(
    tmp_path,
):
    workspace, context, folder = two_priors(tmp_path)
    with_cp8 = prepare(context, folder, workspace / "runs/a", config="sol-medium", cap="50")
    assert with_cp8.ordered[-1] == "CP-8"
    assert "what-changed" not in with_cp8.omitted
    assert "what-changed" not in with_cp8.layout.scope
    assert "CP-8's handoff, delivered whole" in with_cp8.layout.scope
    assert [r for r in with_cp8.layout.routes if r.module_id == "CP-8"] == []
    without = prepare(
        context, folder, workspace / "runs/b", config="sol-medium", cap="50", prior="none"
    )
    assert "what-changed" in without.omitted
    assert "Sections not produced: what-changed" in without.layout.scope


def test_cp8_is_left_out_with_a_note_when_its_first_request_would_not_fit_the_cap(tmp_path):
    """opus-medium holds 8 USD per million input tokens. The earlier run's CP-1 handoff is 200 KB,
    so CP-8's first request, estimated from the earlier handoffs (this run's are unwritten) holds
    more than 3.5 USD; the other modules' calls hold no more than about 3."""
    workspace = tmp_path / "ws"
    make_run(
        workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY, cp1_extra="\n" + "x" * 200_000
    )
    context, folder = snapshot_context(tmp_path)
    out = workspace / "runs/cur"
    prepared = prepare(context, folder, out, config="opus-medium", cap="3.5")
    assert "CP-8" not in prepared.ordered
    assert prepared.prior is None
    assert prepared.plan.changes_note is not None
    assert prepared.plan.changes_note.startswith(
        "changes: not compared: CP-8's first request (about "
    )
    assert "estimated from the earlier run's handoff sizes" in prepared.plan.changes_note
    assert prepared.plan.changes_note.endswith(
        "over the cap USD 3.5; the run is planned without CP-8"
    )
    assert not [n for n in prepared.plan.sources if n.startswith("prior/")]
    # With a cap that holds it, CP-8 is planned.
    big = prepare(context, folder, workspace / "runs/cur2", config="opus-medium", cap="10")
    assert big.ordered[-1] == "CP-8"
    assert big.hold > Decimal(4)


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


def test_cp8s_instructions_state_its_basis_forms_and_no_other_module_does(tmp_path):
    workspace = tmp_path / "ws"
    make_run(workspace, PRIOR_ID, as_of="2024-12-31", pathway=PATHWAY)
    context, folder = snapshot_context(tmp_path)
    prepared = prepare(context, folder, workspace / "runs/cur", config="sol-medium", cap="50")
    texts = {
        m: (workspace / "runs/cur" / spec.path).read_text()
        for m, spec in prepared.plan.instructions.items()
    }
    forms = (
        "`<plain module name> (<code>)` for a handoff of this run",
        "`<plain module name> (<code>), earlier run`",
        "`Run comparison`",
        "never named in a Basis line",
    )
    assert all(f in texts["CP-8"] for f in forms)
    for module, text in texts.items():
        if module != "CP-8":
            assert not any(f in text for f in forms) and "Run comparison" not in text


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


def balance(fcf: str, period: str) -> str:
    return (
        f"### Reported cash flow\n\n| Line item | FY2022 | {period} | Reporting unit |\n"
        "| --- | --- | --- | --- |\n"
        f"| Free cash flow | 1 | {fcf} | US$m |\n\n"
    )


def netdebt(gross: str, cash: str, net: str, period: str, basis: str = "Gross debt: loans.") -> str:
    """CP-1's net debt table (owner, 2026-11-12): hand-written cells, no arithmetic here."""
    return (
        "### Net debt data\n\n"
        "| Period | Gross debt | Cash | Net debt | Reporting unit | Basis and limitation |\n"
        f"| --- | --- | --- | --- | --- | --- |\n| {period} | {gross} | {cash} | {net} | US$m "
        f"| {basis} |\n\n"
    )


MEASURE_KEYS = [
    "leverage",
    "net_leverage",
    "coverage",
    "cash",
    "undrawn",
    "gross_debt",
    "net_debt",
    "free_cash_flow",
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


@pytest.mark.parametrize(
    "pathway",
    [
        *("relative_value", "distressed_restructuring", "portfolio_decision", "short_snapshot"),
        *("earnings_update", "covenant_refinancing"),
    ],
)
def test_a_pack_built_from_the_cp1_handoff_of_each_formerly_unasked_pathway_states_measures(
    tmp_path, pathway
):
    """Owner, 2026-11-12: these four pathways now ask CP-1 for the chart tables (M3). The canned
    CP-1 answer is the launcher test's, written from the checker's own table headers."""
    prepared, _, context = good_task(tmp_path, "CP-1", pathway)
    raw = answer(context, list(prepared.plan.layout.routes))
    pack = build_pack(
        _prior().model_copy(update={"pathway": pathway}),
        {"CP-1": raw},
        {"CP-1": raw},
        as_of=AS_OF,
        pathway=pathway,
    )
    found = measures_of(pack)
    assert {"leverage", "net_leverage", "coverage", "cash", "undrawn"} <= set(found)
    assert found["leverage"]["current"]["value"] == "3.60"
    assert found["net_leverage"]["current"]["value"] == "3.25"
    assert found["coverage"]["current"]["value"] == "3.40"
    assert (found["cash"]["current"]["value"], found["undrawn"]["current"]["value"]) == (
        "275",
        "400",
    )
    assert "maturity_profile" in pack, pack["omitted"]


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
        + balance("60", "FY2023")
        + netdebt("2,100", "300", "1,800", "FY2023", "Gross debt: loans and finance leases."),
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
        + balance("70", "FY2024")
        + netdebt("2,000", "250", "1,750", "FY2024", "Gross debt: loans only."),
    )
    pack = pair_pack(prior, current)
    found = measures_of(pack)
    assert pack["schema"] == "cpos-changes/3"
    assert [m["key"] for m in pack["measures"]] == MEASURE_KEYS
    # Same definition text ("Reported."): Python's difference, 3.60 - 4.20.
    assert found["leverage"]["comparable"] == "yes"
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
    assert found["net_leverage"]["comparable"] == "no"
    assert found["net_leverage"]["reason"] == "a value is not stated"
    # Present in one run only.
    assert found["coverage"]["prior"] is None
    assert found["coverage"]["current"]["value"] == "3.40"
    assert (found["coverage"]["comparable"], found["coverage"]["difference"]) == ("no", None)
    assert found["coverage"]["reason"] == "the earlier run does not state it"
    # A definition text that differs after normalisation: Python still computes the difference,
    # both texts are in the pack and CP-8 judges ("judge").
    assert found["cash"]["comparable"] == "judge"
    assert (found["cash"]["prior"]["value"], found["cash"]["current"]["value"]) == ("300", "250")
    assert found["cash"]["difference"] == "-50"
    assert found["cash"]["prior"]["definition"] == "Cash excluding restricted cash."
    assert found["cash"]["current"]["definition"] == "Cash on another basis."
    assert (found["undrawn"]["comparable"], found["undrawn"]["difference"]) == ("judge", "-50")
    # Free cash flow is a row read from CP-1's tables when it states a unit (no definition text in
    # either run, so the same); gross and net debt come from the net debt table, whose basis text
    # differs here (a judgement, the difference stands).
    assert (found["free_cash_flow"]["comparable"], found["free_cash_flow"]["difference"]) == (
        "yes",
        "10",
    )
    assert (found["gross_debt"]["comparable"], found["gross_debt"]["difference"]) == (
        "judge",
        "-100",
    )
    assert (found["net_debt"]["prior"]["value"], found["net_debt"]["current"]["value"]) == (
        "1,800",
        "1,750",
    )
    assert (found["net_debt"]["comparable"], found["net_debt"]["difference"]) == ("judge", "-50")
    assert found["net_debt"]["unit"] == "US$m"
    # The net debt change is left out with its reason; the maturity profile is built.
    assert "net_debt_change" not in pack
    assert "net_debt_bridge" not in pack
    assert pack["omitted"] == {
        "net_debt_change": "gross debt is not comparable under one definition (judge)"
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
    prior_net: str = "1,800", current_net: str = "1,750", prior_basis: str = "Gross debt: loans."
) -> dict:
    prior = handoff(
        "CP-1",
        "Earlier.",
        tables=liquidity("| FY2023 | 300 | 450 | US$m | Cash. |")
        + balance("60", "FY2023")
        + netdebt("2,100", "300", prior_net, "FY2023", prior_basis),
    )
    current = handoff(
        "CP-1",
        "Now.",
        tables=liquidity("| FY2024 | 250 | 400 | US$m | Cash. |")
        + balance("70", "FY2024")
        + netdebt("2,000", "250", current_net, "FY2024"),
    )
    return pair_pack(prior, current)


def test_the_net_debt_change_is_built_when_both_runs_state_it_under_one_definition():
    pack = bridge_pack()
    # 1,800 = 2,100 - 300 and 1,750 = 2,000 - 250; gross fell 100, cash fell 50.
    assert pack["net_debt_change"] == {
        "unit": "US$m",
        "prior_net_debt": "1800",
        "change_in_gross_debt": "-100",
        "change_in_cash": "-50",
        "current_net_debt": "1750",
        "convention": (
            "net debt = gross debt - cash: an increase in cash reduces net debt, a decrease "
            "raises it; a two-point identity of the stated balances, not an analysis of what "
            "drove the change"
        ),
        "same_period": False,
        "prior_period": "FY2023",
        "current_period": "FY2024",
        "prior_gross_debt": "2100",
        "prior_cash": "300",
        "current_gross_debt": "2000",
        "current_cash": "250",
    }
    assert "net_debt_bridge" not in pack
    assert pack["omitted"] == {
        "maturity_profile": "a run has no debt maturities table with one unit"
    }


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"current_net": "1,700"}, "a run's net debt is not its gross debt less its cash"),
        (
            {"prior_basis": "Gross debt: loans and leases."},
            "gross debt is not comparable under one definition (judge)",
        ),
    ],
)
def test_the_net_debt_change_is_omitted_with_its_reason(kwargs, reason):
    pack = bridge_pack(**kwargs)
    assert "net_debt_change" not in pack
    assert pack["omitted"]["net_debt_change"] == reason


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
    assert pack["schema"] == "cpos-changes/3"
    assert pack["prior"] == {
        "run": "p",
        "as_of": "2024-12-31",
        "pathway": "credit_snapshot",
        "format": "current",
        "methods_changed": [],
        "selection": None,
    }
    assert pack["current"] == {
        "as_of": "2025-03-31",
        "pathway": "credit_snapshot",
        "format": "current",
        "selection": None,
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
    # Refs are given in module order, then the order in the handoff; every item has its own ref.
    assert pack["limitations"] == {
        "earlier": [
            {
                "ref": "E1",
                "module": "CP-1",
                "text": "Segment data is not supplied, so segment margins are not assessed.",
            },
            {"ref": "E2", "module": "CP-2", "text": "Old limitation text."},
        ],
        "current": [
            {
                "ref": "C1",
                "module": "CP-1",
                "text": "Segment data is not supplied so segment margins are not assessed",
            },
            {
                "ref": "C2",
                "module": "CP-2",
                "text": "The covenant package is not supplied, so covenant headroom is unknown.",
            },
        ],
    }


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
        tables=balance("60", "FY2023") + balance("70", "FY2023"),
    )
    assert "free_cash_flow" not in observations(twice)  # two rows of one label: not guessed
    unitless = "## Findings\n\n| Line item | FY2023 |\n| --- | --- |\n| Net debt | 1,800 |\n"
    assert observations(unitless) == {}


def test_the_bottom_line_and_format_helpers():
    new = handoff("CP-2", "First paragraph here.\nStill the first.\n\nSecond paragraph.")
    assert bottom_line_text(new) == "First paragraph here. Still the first."
    assert is_earlier_format(new) is False
    old = earlier_handoff("CP-2", "Old.", "Lim.")
    assert is_earlier_format(old) is True
    assert bottom_line_text(old) is None


def liq(prior_cell: str, current_cell: str, prior_basis="Cash.", current_basis="Cash.") -> dict:
    prior = handoff(
        "CP-1", "x", tables=liquidity(f"| FY2023 | {prior_cell} | 843 | US$m | {prior_basis} |")
    )
    current = handoff(
        "CP-1", "x", tables=liquidity(f"| FY2024 | {current_cell} | 843 | US$m | {current_basis} |")
    )
    return measures_of(pair_pack(prior, current))["cash"]


def test_a_new_period_with_an_unchanged_definition_is_comparable_whatever_pages_it_cites():
    leverage_row = "| {p} | {a} | 5.00 | x | Gross debt / EBITDA {n}. Pages {pg}. |"
    prior = handoff(
        "CP-1",
        "x",
        tables=leverage(leverage_row.format(p="FY2023", a="6.50", n="3,500", pg="60-62")),
    )
    current = handoff(
        "CP-1",
        "x",
        tables=leverage(leverage_row.format(p="FY2024", a="6.01", n="3,813", pg="63 and 65")),
    )
    found = measures_of(pair_pack(prior, current))["leverage"]
    assert (found["comparable"], found["difference"]) == ("yes", "-0.49")
    # The real basis cells of the issuer library's TDG pair differ in the pages cited only.
    real_basis = "reported cash and available revolving commitments, after letters of credit."
    real_prior = "Annual filing pages 120 and 152; " + real_basis
    real_now = "Annual filing pages 118 and 150; " + real_basis
    same = liq("3472", "6261", real_prior, real_now)
    assert (same["comparable"], same["difference"]) == ("yes", "2789")
    # A different definition is for CP-8 to judge: the difference stands, both texts are given.
    other = liq("3472", "6261", real_prior, real_now.replace("after letters", "before letters"))
    assert (other["comparable"], other["difference"]) == ("judge", "2789")
    assert other["current"]["definition"].endswith("before letters of credit.")


def test_identical_values_under_one_definition_give_a_zero_difference():
    same = liq("6261", "6261")
    assert (same["comparable"], same["difference"]) == ("yes", "0")


def test_a_unit_that_differs_or_a_value_that_is_missing_gives_no_difference():
    prior = handoff("CP-1", "x", tables=liquidity("| FY2023 | 6261 | 843 | US$m | Cash. |"))
    bn = handoff("CP-1", "x", tables=liquidity("| FY2024 | 6.3 | 0.8 | US$bn | Cash. |"))
    found = measures_of(pair_pack(prior, bn))["cash"]
    assert (found["comparable"], found["difference"]) == ("no", None)
    assert found["reason"] == "the unit differs or is not stated"
    gap = liq("0", "Not supplied: not stated")
    assert (gap["comparable"], gap["difference"], gap["reason"]) == (
        "no",
        None,
        "a value is not stated",
    )  # a zero is a value; a stated gap is not one


@pytest.mark.parametrize(
    ("prior_cell", "current_cell", "difference"),
    [
        ("(120)", "100", "220"),  # a bracketed figure is negative
        ("\u2212120", "100", "220"),  # so is one with a Unicode minus
        ("6.5x", "6.0x", "-0.5"),  # a unit mark beside the figure is not part of the value
        ("12%", "13.5%", "1.5"),
        ("1,234.5", "1,300", "65.5"),
    ],
)
def test_the_figure_forms_a_handoff_writes_are_read(prior_cell, current_cell, difference):
    found = liq(prior_cell, current_cell)
    assert (found["comparable"], found["difference"]) == ("yes", difference)


def test_an_ambiguous_row_says_so_rather_than_that_the_run_does_not_state_it():
    twice = handoff(
        "CP-1",
        "x",
        tables=balance("60", "FY2023") + balance("70", "FY2023"),
    )
    once = handoff("CP-1", "x", tables=balance("70", "FY2024"))
    found = measures_of(pair_pack(twice, once))["free_cash_flow"]
    assert found["comparable"] == "no"
    assert found["reason"] == "the earlier run states it in more than one row"
    assert found["prior"] is None


def test_the_maturities_table_must_sit_directly_under_its_heading():
    table = (
        "| Period | Debt maturing | Reporting unit | Basis and limitation |\n"
        "| --- | --- | --- | --- |\n"
    )
    right = handoff("CP-1", "x", tables=maturities("| FY2026 | 500 | US$m | Schedule. |"))
    # The same columns under another heading, with the real heading far above another table.
    elsewhere = handoff(
        "CP-1",
        "x",
        tables="### Chart data: debt maturities\n\nNot supplied.\n\n### Other\n\n"
        + table
        + "| FY2026 | 450 | US$m | Other. |\n\n",
    )
    assert "maturity_profile" in pair_pack(right, right)
    pack = pair_pack(right, elsewhere)
    assert "maturity_profile" not in pack
    assert pack["omitted"]["maturity_profile"] == "a run has no debt maturities table with one unit"


# --- the checker ---------------------------------------------------------------------------------

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
COVER_NOW = {
    "label": "EBITDA / cash interest",
    "unit": "x",
    "value": "3.60",
    "period": "FY2024",
    "definition": None,
}
PACK = {
    "measures": [
        {
            "key": "leverage",
            "label": "Total debt / EBITDA",
            "unit": "x",
            "comparable": "yes",
            "reason": None,
            "prior": LEVERAGE_PRIOR,
            "current": {**LEVERAGE_PRIOR, "value": "3.60", "period": "FY2024"},
            "difference": "-0.60",
            "same_period": False,
        },
        {
            "key": "cash",
            "label": "Cash",
            "unit": "US$m",
            "comparable": "judge",
            "reason": "the definition text differs after normalisation",
            "prior": CASH_PRIOR,
            "current": {**CASH_PRIOR, "value": "250", "period": "FY2024", "definition": "Other."},
            "difference": "-50",
            "same_period": False,
        },
        {
            "key": "coverage",
            "label": "EBITDA / cash interest",
            "unit": "x",
            "comparable": "no",
            "reason": "the earlier run does not state it",
            "prior": None,
            "current": COVER_NOW,
            "difference": None,
            "same_period": False,
        },
    ],
    "modules": [
        {"module": "CP-2", "ran_prior": True, "ran_current": True},
        {"module": "CP-DR", "ran_prior": True, "ran_current": False},
        {"module": "CP-2E", "ran_prior": False, "ran_current": True},
    ],
    "limitations": {
        "earlier": [
            {"ref": "E1", "module": "CP-2", "text": "The covenant package was not supplied."},
            {"ref": "E2", "module": "CP-1", "text": "Segment data is not supplied."},
        ],
        "current": [
            {"ref": "C1", "module": "CP-2E", "text": "Hedging data is not supplied."},
            {"ref": "C2", "module": "CP-1", "text": "Segment data are not supplied."},
        ],
    },
}
CASH_ROW = (
    "| Cash | 300 US$m (FY2023) | 250 US$m (FY2024) | New period "
    "| Same definition: cash fell by 50 US$m. |"
)
CLOSED_ROW = (
    "| E1 | — | The covenant package gap. | Closed "
    "| The Macro handoff (CP-2E) now shows the package. |"
)
REGISTERS = """## Findings

### What changed: the issuer

| Measure or fact | Earlier | Current | Cause | Effect on the credit view |
| --- | --- | --- | --- | --- |
| Total debt / EBITDA | 4.20x (FY2023) | 3.60x (FY2024) | New period | Leverage fell by 0.60x. |
@@CASH@@

### What changed: the analysis

| Module | Status | Cause | Why |
| --- | --- | --- | --- |
| Credit view (CP-2) | Strengthened | New period | Leverage fell. |
| Research (CP-DR) | Not run this time | Method change | The research module was not selected. |
| Macro (CP-2E) | New | New source | The module was added. |

### Limitations ledger

| Earlier ref | Current ref | Limitation | Status | What closed it |
| --- | --- | --- | --- | --- |
@@CLOSED@@
| — | C1 | A hedging data gap. | New | — |
| E2 | C2 | Segment data is missing. | Remaining | — |

## Calculations
""".replace("@@CASH@@", CASH_ROW).replace("@@CLOSED@@", CLOSED_ROW)


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
            "| Total debt / EBITDA | 4.20x (FY2023) | 3.60x (FY2024) |",
            "| Total debt / EBITDA | 3.60x (FY2023) | 4.20x (FY2024) |",
            "earlier figure 3.60",
        ),  # the pack's values in the wrong columns
        (
            "| Total debt / EBITDA | 4.20x (FY2023) | 3.60x (FY2024) |",
            "| Leverage | 3.60x (FY2023) | 4.20x (FY2024) |",
            "name a pack measure",
        ),  # a row with figures that names no pack measure, whatever its values
        ("| Cash |", "| Cash balance |", "name a pack measure"),
        ("| 4.20x (FY2023) |", "| -4.20x (FY2023) |", "earlier figure -4.20"),  # the sign counts
        ("by 0.60x", "by -0.60x", "-0.60"),  # a difference printed with the wrong sign
        ("Leverage fell by 0.60x.", "Leverage rose by 0.60x.", "direction"),
        ("300 US$m (FY2023)", "300 US$bn (FY2023)", "unit"),  # the scale is part of the value
        (
            "Same definition: cash fell by 50 US$m.",
            "Same definition: cash fell by 50 US$m; it was 9999M.",
            "9999",
        ),  # the month exemption is for periods of 1M to 12M only
        (
            "Leverage fell by 0.60x.",
            "Leverage fell by 0.60x; debt was 333 US$m.",
            "333",
        ),  # a value of another measure is not this row's
        # A definition the pack leaves to CP-8's judgement: one of the two words is required.
        ("Same definition: cash fell by 50 US$m.", "Cash fell by 50 US$m.", "Same definition"),
        (
            "Same definition: cash fell by 50 US$m.",
            "Not comparable: cash fell by 50 US$m.",
            "difference",
        ),  # not comparable: the difference is not printed
        (
            "Same definition: cash fell by 50 US$m.",
            "Not comparable: the definition differs, so cash weakened.",
            "trend",
        ),  # not comparable: no trend is drawn
        (
            "Same definition: cash fell by 50 US$m.",
            "Same definition, and not comparable: cash fell by 50 US$m.",
            "only one",
        ),
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
    ],
)
def test_the_checker_refuses_each_broken_cp8_handoff(old, new, fragment):
    found = issues_after(old, new)
    assert found, "accepted"
    assert any(fragment.lower() in issue.lower() for issue in found), found


def test_a_fact_row_without_figures_is_free_text_and_one_with_a_figure_names_a_measure():
    fact = "| Refinancing | Not announced | Announced | New source | Maturities were extended. |\n"
    text = REGISTERS.replace(
        "\n### What changed: the analysis", fact + "\n### What changed: the analysis", 1
    )
    assert cp8_issues(text, PACK) == ()
    figured = fact.replace("Announced", "Announced, 500 US$m")
    again = REGISTERS.replace(
        "\n### What changed: the analysis", figured + "\n### What changed: the analysis", 1
    )
    assert any("500" in i for i in cp8_issues(again, PACK))  # not held in the pack or a handoff


def test_a_measure_the_pack_cannot_compare_is_stated_as_not_stated_or_not_comparable():
    row = (
        "| EBITDA / cash interest | not stated | 3.60x (FY2024) | New source "
        "| The earlier run does not state it, so it is not comparable. |\n"
    )
    text = REGISTERS.replace(
        "\n### What changed: the analysis", row + "\n### What changed: the analysis", 1
    )
    assert cp8_issues(text, PACK) == ()
    bare = row.replace("The earlier run does not state it, so it is not comparable.", "Cover rose.")
    again = REGISTERS.replace(
        "\n### What changed: the analysis", bare + "\n### What changed: the analysis", 1
    )
    assert any("not comparable" in i.lower() for i in cp8_issues(again, PACK))
    wrong = row.replace("not stated |", "2.90x (FY2023) |")
    third = REGISTERS.replace(
        "\n### What changed: the analysis", wrong + "\n### What changed: the analysis", 1
    )
    assert any("earlier figure 2.90" in i for i in cp8_issues(third, PACK))


def test_a_judged_row_that_says_not_comparable_may_give_both_values_and_no_difference():
    text = REGISTERS.replace(
        "Same definition: cash fell by 50 US$m.", "Not comparable: the definitions differ."
    )
    assert cp8_issues(text, PACK) == ()


def test_a_difference_printed_in_a_reader_passage_or_in_the_gaps_must_be_the_packs():
    passage = "## Findings\n\n### Bottom line\n\nLeverage fell from 4.20x to 3.60x, by 0.60x.\n\n"
    good = REGISTERS.replace("## Findings\n\n", passage, 1)
    assert cp8_issues(good, PACK) == ()
    wrong = good.replace("by 0.60x.\n", "by 0.65x.\n", 1)
    assert any("0.65" in i for i in cp8_issues(wrong, PACK))
    not_a_difference = good.replace("by 0.60x.\n", "by 4.20x.\n", 1)
    assert any("4.20" in i and "difference" in i for i in cp8_issues(not_a_difference, PACK))
    gaps = REGISTERS + "\n## Gaps\n\nCash fell by 55 US$m between the runs.\n"
    assert any("55" in i for i in cp8_issues(gaps, PACK))
    fine = REGISTERS + "\n## Gaps\n\nThe earlier cover figure is not stated.\n"
    assert cp8_issues(fine, PACK) == ()


@pytest.mark.parametrize(
    ("old", "new", "fragment"),
    [
        (
            CLOSED_ROW,
            "| E1 | — | The covenant package gap. | Closed | — |",
            "Closed",
        ),
        (
            "(CP-2E) now shows",
            "(CP-DR) now shows",
            "Closed",
        ),  # evidence must be a module of the current run
        ("The Macro handoff (CP-2E) now shows the package.", "Resolved.", "Closed"),
        (
            "| — | C1 | A hedging data gap. | New |",
            "| — | C1 | A hedging data gap. | Remaining |",
            "New",
        ),
        (
            "| E2 | C2 | Segment data is missing. | Remaining |",
            "| E2 | C2 | Segment data is missing. | Closed |",
            "Remaining",
        ),
        (
            "| E2 | C2 | Segment data is missing. | Remaining |",
            "| E2 | C2 | Segment data is missing. | Unknown |",
            "Unknown",
        ),
        ("| E2 | C2 |", "| E9 | C2 |", "E9"),  # a ref the pack does not hold
        ("| — | C1 |", "| — | C1, C9 |", "C9"),
        ("| E2 | C2 |", "| C2 | E2 |", "Earlier ref"),  # a ref in the other column
    ],
)
def test_the_checker_refuses_each_broken_ledger_row(old, new, fragment):
    found = issues_after(old, new)
    assert found, "accepted"
    assert any(fragment.lower() in issue.lower() for issue in found), found


def test_a_reworded_limitation_is_paired_by_meaning_through_its_refs():
    # The pack's two texts differ in words; CP-8 pairs them and writes its own: Remaining.
    assert PACK["limitations"]["earlier"][1]["text"] != PACK["limitations"]["current"][1]["text"]
    assert cp8_issues(REGISTERS, PACK) == ()
    split = REGISTERS.replace(
        "| E2 | C2 | Segment data is missing. | Remaining | — |",
        "| E2 | — | Segment data was missing. | No longer stated | — |\n"
        "| — | C2 | Segment data is missing again. | New | — |",
    )
    assert cp8_issues(split, PACK) == ()


def test_a_closed_limitation_names_a_module_of_the_current_run_and_a_gone_one_names_none():
    text = REGISTERS.replace(
        CLOSED_ROW,
        "| E1 | — | The covenant package gap. | No longer stated | — |",
    )
    assert cp8_issues(text, PACK) == ()


def test_a_ref_appears_in_exactly_one_row_and_only_in_the_two_ref_columns():
    macro = "| — | C1 | A hedging data gap. | New | — |\n"
    assert any("C1" in i and "found 0" in i for i in issues_after(macro, ""))
    assert any("C1" in i and "found 2" in i for i in issues_after(macro, macro + macro))
    both = "| E2 | C2 | Segment data is missing. | Remaining | — |\n"
    assert any("E2" in i and "found 0" in i for i in issues_after(both, ""))
    assert any("E2" in i and "found 2" in i for i in issues_after(both, both + both))
    # A ref in a sentence, or in the Limitation cell, is refused.
    in_sentence = REGISTERS.replace("Leverage fell.", "Leverage fell, as E1 shows.")
    assert any("E1" in i and "only in" in i for i in cp8_issues(in_sentence, PACK))
    in_cell = REGISTERS.replace("A hedging data gap.", "A gap like C2.")
    assert any("C2" in i and "only in" in i for i in cp8_issues(in_cell, PACK))


def test_a_ledger_row_needs_a_limitation_in_words():
    empty = REGISTERS.replace("| A hedging data gap. |", "| — |")
    assert any("Limitation" in i for i in cp8_issues(empty, PACK))


@pytest.mark.parametrize(
    ("old", "new", "fragment"),
    [
        ("### What changed: the issuer", "### What changed: the lot", "exactly once"),
        ("| Measure or fact | Earlier |", "| Measure | Earlier |", "exactly these columns"),
        ("| Earlier ref | Current ref |", "| Earlier | Current |", "exactly these columns"),
    ],
)
def test_a_register_that_is_missing_or_has_other_columns_is_refused(old, new, fragment):
    found = issues_after(old, new)
    assert any(fragment in issue for issue in found), found


def test_a_missing_module_row_and_a_duplicate_row_are_refused():
    macro = "| Macro (CP-2E) | New | New source | The module was added. |\n"
    assert any("CP-2E needs exactly one row (found 0)" in i for i in issues_after(macro, ""))
    assert any(
        "CP-2E needs exactly one row (found 2)" in i for i in issues_after(macro, macro + macro)
    )


def test_a_register_with_a_header_and_no_row_or_no_table_is_refused():
    cut = REGISTERS[: REGISTERS.index("| E1 |")] + "\n## Calculations\n"
    assert any("needs exactly one row" in i for i in cp8_issues(cut, PACK))
    bare = REGISTERS[: REGISTERS.index("| Earlier ref")] + "\n## Calculations\n"
    assert any("holds no table" in i for i in cp8_issues(bare, PACK))


def test_a_row_for_no_material_change_is_accepted_with_cause_none():
    text = REGISTERS.replace(
        REGISTERS[
            REGISTERS.index("| Total debt") : REGISTERS.index("### What changed: the analysis")
        ],
        "| No material change | — | — | None | Nothing material moved. |\n\n",
    )
    assert cp8_issues(text, PACK) == ()


# --- round 2: one period with two values, what a reader is told ----------------------------------

SAME = {**PACK["measures"][0]}
SAME.update(
    prior={**LEVERAGE_PRIOR, "value": "6.57", "definition": "EBITDA reported 3,813."},
    current={**LEVERAGE_PRIOR, "value": "6.01", "definition": "Other.", "period": "FY2023"},
    difference="-0.56",
    comparable="judge",
    same_period=True,
)
SAME["current"]["period"] = "FY2023"  # the earlier run's period too (LEVERAGE_PRIOR's)
PACK2 = {**PACK, "measures": [SAME, *PACK["measures"][1:]]}
LEVERAGE_ROW = (
    "| Total debt / EBITDA | 4.20x (FY2023) | 3.60x (FY2024) | New period "
    "| Leverage fell by 0.60x. |"
)


def with_row(row: str, passage: str = "", gaps: str = "") -> str:
    text = REGISTERS.replace(LEVERAGE_ROW, row)
    return text.replace("## Findings\n\n", "## Findings\n\n" + passage, 1) + gaps


def same_period_row(effect: str, cause: str = "Unresolved") -> str:
    return f"| Total debt / EBITDA | 6.57x (FY2023) | 6.01x (FY2023) | {cause} | {effect} |"


@pytest.mark.parametrize(
    ("effect", "cause", "fragment"),
    [
        ("Not comparable: EBITDA basis differs.", "Unresolved", None),
        ("Not comparable: EBITDA basis differs.", "Correction", None),
        ("Same definition; the earlier run misstated EBITDA.", "Correction", None),
        ("Same definition; the method now adds back leases.", "Method change", None),
        ("Same definition; the earlier run misstated EBITDA.", "New period", "same period"),
        ("Same definition.", "Unresolved", "Correction"),  # a same-definition move needs a reason
        ("Not comparable: basis differs.", "New source", "same period"),
        ("Leverage moved.", "Correction", "Not comparable"),
    ],
)
def test_a_measure_of_one_period_with_two_values_is_a_definition_or_a_correction(
    effect, cause, fragment
):
    found = cp8_issues(with_row(same_period_row(effect, cause)), PACK2)
    if fragment is None:
        assert found == ()
    else:
        assert any(fragment.lower() in issue.lower() for issue in found), found


@pytest.mark.parametrize(
    "passage",
    [
        "Leverage fell by 0.56x.",  # the difference of a not-comparable row
    ],
)
def test_a_not_comparable_or_same_period_difference_never_reaches_a_reader_passage(passage):
    row = same_period_row("Not comparable: EBITDA basis differs.")
    found = cp8_issues(with_row(row, passage + "\n\n"), PACK2)
    assert found, "accepted"
    assert cp8_issues(with_row(row, "Leverage is 6.57x earlier and 6.01x now.\n\n"), PACK2) == ()


def test_a_correction_may_be_described_by_a_sentence_that_names_it():
    row = same_period_row("Same definition; the earlier run misstated EBITDA.", "Correction")
    said = "Leverage fell from 6.57x to 6.01x after the correction of EBITDA.\n\n"
    assert cp8_issues(with_row(row, said), PACK2) == ()


def test_a_not_comparable_difference_is_printed_nowhere_not_in_the_gaps_either():
    row = same_period_row("Not comparable: EBITDA basis differs.")
    gaps = "\n## Gaps\n\nThe measure moved by 0.56x between the runs.\n"
    assert any("0.56" in i for i in cp8_issues(with_row(row, gaps=gaps), PACK2))


@pytest.mark.parametrize(
    "sentence",
    [
        "Leverage fell by 0.70x.",
        "Leverage fell 8.5%.",
        "A 0.70x move in leverage.",
        "Leverage is 0.70 turns lower.",
        "An 8.5% reduction in leverage.",
        "Leverage fell from 4.20x to 3.50x.",
        "Leverage is now 3.50x.",
        "Leverage is 400 US$m.",
    ],
)
def test_every_figure_of_a_reader_passage_is_held_in_the_pack_or_either_runs_handoffs(sentence):
    text = REGISTERS.replace(
        "## Findings\n\n", f"## Findings\n\n### Bottom line\n\n{sentence}\n\n", 1
    )
    assert cp8_issues(text, PACK), "accepted"


def test_a_reader_figure_may_be_a_pack_value_or_one_a_register_row_prints():
    ok = "Leverage is 3.60x now and was 4.20x. Cash is 250 US$m, so 300 US$m before."
    text = REGISTERS.replace("## Findings\n\n", f"## Findings\n\n### Bottom line\n\n{ok}\n\n", 1)
    assert cp8_issues(text, PACK) == ()
    # A figure the sentence does not tie to a measure is allowed only if the pack or a row holds it.
    free = REGISTERS.replace(
        "## Findings\n\n", "## Findings\n\n### Bottom line\n\nA figure of 3.60 is held.\n\n", 1
    )
    assert cp8_issues(free, PACK) == ()
    wrong = free.replace("3.60 is held", "3.61 is held")
    assert cp8_issues(wrong, PACK)


def test_a_ref_in_lower_case_in_a_sentence_is_caught():
    text = REGISTERS.replace("Leverage fell.", "Leverage fell, as e1 shows.")
    assert any("E1" in i and "only in" in i for i in cp8_issues(text, PACK))


def test_a_definition_is_the_same_only_with_the_same_instrument_years():
    notes = "debt incl. notes 2027"
    assert liq("1", "1", notes, "debt incl. notes 2029 and 2031")["comparable"] == "judge"
    assert liq("1", "1", notes, notes)["comparable"] == "yes"
    assert (
        liq("1", "1", "debt due 2027, pages 12 and 14", "debt due 2027, pages 18 and 20")[
            "comparable"
        ]
        == "yes"
    )  # page numbers still do not count
    assert liq("1", "1", "loan maturing 2030", "loan maturing 2031")["comparable"] == "judge"


def test_the_pack_says_whether_both_runs_state_a_measure_for_one_period_and_follows_a_pointer():
    early = leverage(
        "| FY2024 | 6.57 | 4.93 | x | Gross debt over reported EBITDA 3,813. Pages 63, 71. |"
    )
    now = leverage(
        "| FY2023 | 5.87 | 4.84 | x | C01-C04; gross principal over EBITDA As Defined. |",
        "| FY2024 | 6.01 | 4.51 | x | C01-C04; identical definition; cash before settlement. |",
    )
    found = measures_of(
        pair_pack(handoff("CP-1", "x", tables=early), handoff("CP-1", "x", tables=now))
    )
    lev = found["leverage"]
    assert (lev["same_period"], lev["comparable"], lev["difference"]) == (True, "judge", "-0.56")
    assert lev["current"]["definition_resolved"] is True
    assert lev["current"]["definition"] == "C01-C04; gross principal over EBITDA As Defined."
    assert lev["current"]["definition_written"] == (
        "C01-C04; identical definition; cash before settlement."
    )
    assert lev["prior"]["definition_resolved"] is False
    assert lev["prior"]["definition_written"] is None
    # Another period for each run: not the same period, and a calculation ID alone is not followed.
    moved = measures_of(
        pair_pack(
            handoff("CP-1", "x", tables=leverage("| FY2023 | 5.87 | 4.84 | x | C01-C04; basis. |")),
            handoff("CP-1", "x", tables=now),
        )
    )["leverage"]
    assert moved["same_period"] is False
    assert moved["prior"]["definition_resolved"] is False
    assert moved["prior"]["definition"] == "C01-C04; basis."
    # A pointer with no earlier row to point to is left as written.
    lone = measures_of(
        pair_pack(
            handoff("CP-1", "x", tables=early),
            handoff(
                "CP-1", "x", tables=leverage("| FY2024 | 6.01 | 4.51 | x | Identical definition. |")
            ),
        )
    )["leverage"]
    assert lone["current"]["definition_resolved"] is False
    assert lone["current"]["definition"] == "Identical definition."


def test_cp8_is_never_the_library_summary_when_cp2_is_absent():
    from deploy_workflow.credit_os_catalogue import summary_fields

    def module(name: str) -> dict:
        return {
            "id": name,
            "summary": {"bottom_line": f"{name} says", "limitation": f"{name} limit"},
        }

    run = {"modules": [module("CP-0"), module("CP-1"), module("CP-8")]}
    assert summary_fields(run) == ("CP-1 says", ["CP-1 limit"])
    assert summary_fields({"modules": [module("CP-8")]}) == ("", [])
    with_cp2 = {"modules": [module("CP-2"), module("CP-8")]}
    assert summary_fields(with_cp2) == ("CP-2 says", ["CP-2 limit"])


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
        "| Earlier ref | Current ref | Limitation | Status | What closed it |",
        "| --- | --- | --- | --- | --- |",
        # The earlier run's CP-0 and CP-1 each stated "Synthetic fixture only." (E1, E2).
        "| E1, E2 | — | Synthetic fixture only. | No longer stated | — |",
    ]
    number = 0  # C1, C2 ...: module order, then order in the handoff
    for module in modules:
        for text in LIMITATION_LINE.findall(context["handoffs"][module]["markdown"]):
            number += 1
            lines.append(f"| — | C{number} | {text} | New | — |")
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
    assert found["leverage"]["comparable"] == "yes"  # "Synthetic." in both runs
    assert found["cash"]["comparable"] == "judge"  # "Earlier basis." against "Synthetic."
    assert found["cash"]["difference"] == "-25"
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


def wrong_cp8():
    """A provider whose CP-8 answers print a current figure the pack does not hold."""
    good = provider.answer
    provider.answer = lambda context: (
        good(context).replace("3.60x (FY2024)", "3.70x (FY2024)")
        if context["module_id"] == "CP-8"
        else good(context)
    )


@pytest.mark.usefixtures("provider")
def test_a_cp8_that_is_not_accepted_loses_only_itself_and_the_run_says_why(tmp_path, capsys):
    """Owner, 2026-11-12: CP-8 is optional to completion. Its refusal is the one fail-open: the
    delivery of every other module stands and the reason is recorded in four places."""
    _, out, argv = run_with_prior(tmp_path)
    wrong_cp8()
    assert main(argv) == 0
    err = capsys.readouterr().err
    reason = "changes: not produced \u2014 cpos_live_not_accepted: CP-8 not accepted within bounds"
    assert reason in err  # 1. stderr
    # The loop sent the answer back, naming the figure, before it gave up.
    sent_back = " ".join(p.read_text() for p in (out / "live/modules").glob("*/*.tools.json"))
    assert "REJECTED" in sent_back
    assert "current figure 3.70 is not the pack's current value (3.60)" in sent_back
    (receipt,) = (out / "deliveries").glob("*/delivery.json")
    assert not (receipt.parent / "CP-8.md").exists()
    assert not (receipt.parent / "changes.json").exists()
    assert {m: (receipt.parent / f"{m}.md").is_file() for m in SNAPSHOT_MODULES} == dict.fromkeys(
        SNAPSHOT_MODULES, True
    )
    completed = json.loads(next(out.glob("completed-*.json")).read_text())  # 2. completion record
    assert completed["changes"] == reason
    assert "CP-8" not in completed["modules"]
    manifest = json.loads(next(out.glob("delivery-*.json")).read_text())  # 3. delivery manifest
    assert manifest["changes_note"] == reason
    assert "CP-8" not in manifest["handoffs"]
    events = [json.loads(line) for line in (out / "events.jsonl").read_text().splitlines()]
    assert {
        "event": "changes_not_produced",
        "reason": reason.removeprefix("changes: not produced \u2014 "),
    } in [  # 4. event
        {k: v for k, v in e.items() if k != "at"} for e in events
    ]
    assert events[-1]["event"] == "delivered"
    scope = manifest["layout"]["scope"]
    assert "Changes since the last run (CP-8): " + reason in scope
    assert "delivered whole" not in scope  # one true thing: CP-8's handoff was not produced


@pytest.mark.usefixtures("provider")
def test_a_relaunch_after_a_cp8_refusal_leaves_the_delivery_and_makes_no_call(tmp_path, capsys):
    _, out, argv = run_with_prior(tmp_path)
    wrong_cp8()
    assert main(argv) == 0
    capsys.readouterr()
    calls = list(provider.calls)
    before = tree(out / "deliveries")
    completed = sorted(p.name for p in out.glob("completed-*.json"))
    assert main(argv) == 0
    assert provider.calls == calls  # no new call, CP-8's included
    assert tree(out / "deliveries") == before
    assert sorted(p.name for p in out.glob("completed-*.json")) == completed
    err = capsys.readouterr().err
    assert "recorded by the earlier launch of this run; no new call" in err


@pytest.mark.usefixtures("provider")
def test_another_modules_failure_is_not_masked_by_the_cp8_fail_open(tmp_path, capsys):
    _, out, argv = run_with_prior(tmp_path)
    good = provider.answer
    provider.answer = lambda context: (
        "not a handoff" if context["module_id"] == "CP-1" else good(context)
    )
    assert main(argv) == 1
    assert "Stopped:" in capsys.readouterr().err
    assert not (out / "deliveries").exists()
    assert "CP-8" not in {c[0] for c in provider.calls}


def test_only_cp8s_two_refusals_are_survived():
    from deploy_workflow.model.budget import BudgetExhausted, OverrunStop
    from deploy_workflow.owners.cpos import _cp8_unaccepted

    assert _cp8_unaccepted(RuntimeError("cpos_live_not_accepted: CP-8 not accepted within bounds"))
    assert _cp8_unaccepted(ValueError("cpos_module_failed: CP-8: a figure"))
    assert _cp8_unaccepted(BudgetExhausted("the reservation would pass the cap"))
    assert not _cp8_unaccepted(RuntimeError("cpos_live_stopped: error; charge=None; overrun=False"))
    assert not _cp8_unaccepted(OverrunStop("charged above the hold"))
    assert not _cp8_unaccepted(ValueError("cpos_interrupted: response not retained for CP-8"))
    assert not _cp8_unaccepted(
        RuntimeError("cpos_live_not_accepted: CP-4 not accepted within bounds")
    )


@pytest.mark.usefixtures("provider")
def test_a_pack_that_cannot_be_built_delivers_without_cp8(tmp_path, capsys, monkeypatch):
    """The pack builder is made to fail as it does on a handoff text it cannot read."""
    _, out, argv = run_with_prior(tmp_path)

    def builder(prior, as_of, pathway, selection):
        def build(sources, handoffs):
            raise ValueError("a handoff is not readable")

        return build

    monkeypatch.setattr("deploy_workflow.owners.cpos.pack_builder", builder)
    assert main(argv) == 0
    assert "CP-8" not in {c[0] for c in provider.calls}
    completed = json.loads(next(out.glob("completed-*.json")).read_text())
    assert completed["changes"] == (
        "changes: not produced \u2014 the comparison pack could not be built "
        "(a handoff is not readable)"
    )
    assert "not produced" in capsys.readouterr().err


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
    assert "| Total debt / EBITDA | 4.20x (FY2023) | 3.60x (FY2024) | New period |" in handoff
    assert "### Limitations ledger" in handoff


# --- round 3: mechanical invariants only; a period is the same by date or fiscal year -------------


@pytest.mark.parametrize(
    ("prior", "current", "expected"),
    [
        ("FY2024", "FY2024", True),
        ("FY2024 / 2024-09-30", "FY2024", True),
        ("FY2024", "FY2024 / 2024-09-30", True),
        ("FY2024 / 2024-09-30", "2024-09-30", True),
        ("2024-09-30", "2024-09-30", True),
        ("FY2024 / 2024-09-30", "FY2024 / 2024-12-31", False),
        ("2024-09-30", "2024-12-28", False),
        ("FY2024", "2024-09-30", False),
        ("FY2023", "FY2024", False),
        ("H1 FY2024", "FY2024", False),
        ("LTM Q3 FY2024", "FY2024", False),
        ("Q1 FY2024", "FY2024 / 2024-09-30", False),
        ("FY2024 pro forma", "FY2024", False),
        ("FY2024 restated", "FY2024", False),
    ],
)
def test_a_period_is_the_same_only_on_the_same_date_or_fiscal_year(prior, current, expected):
    from deploy_workflow.changes import same_period

    assert same_period(prior, current) is expected


def test_two_period_ends_of_one_fiscal_year_are_not_the_same_period_in_the_pack():
    early = leverage("| FY2024 / 2024-09-30 | 6.57 | 4.93 | x | Gross debt over EBITDA 3,813. |")
    now = leverage("| FY2024 / 2024-12-31 | 6.01 | 4.51 | x | Gross debt over EBITDA 3,813. |")
    found = measures_of(
        pair_pack(handoff("CP-1", "x", tables=early), handoff("CP-1", "x", tables=now))
    )
    assert found["leverage"]["same_period"] is False


def _held_measure(key, label, values, definition=None, unit="x"):
    prior, current, difference = values
    side = {"label": label, "unit": unit, "definition": definition}
    return {
        "key": key,
        "label": label,
        "unit": unit,
        "comparable": "judge",
        "reason": "the definition text differs; CP-8 judges",
        "prior": {**side, "value": prior, "period": "FY2024"},
        "current": {**side, "value": current, "period": "FY2024"},
        "difference": difference,
        "same_period": True,
    }


# The real pair (a TDG run in the earlier format against one in the current format, both FY2024),
# copied by hand: leverage 6.57 -> 6.01 and coverage 3.29 -> 3.60 are one period with two values.
REAL = {
    "measures": [
        _held_measure("leverage", "Total debt / EBITDA", ("6.57", "6.01", "-0.56")),
        _held_measure(
            "coverage",
            "EBITDA / cash interest",
            ("3.29", "3.60", "0.31"),
            "EBITDA 3,813 / cash interest paid, net 1,158.",
        ),
        _held_measure("cash", "Cash", ("6261", "6261", "0"), unit="US$m"),
        _held_measure(
            "undrawn",
            "Undrawn committed facilities",
            ("843", "843", "0"),
            "Revolving borrowings available after 67 of letters of credit.",
            "US$m",
        ),
    ],
    "maturity_profile": {
        "unit": "US$m",
        "rows": [
            {"period": p, "prior": v, "current": v, "difference": "0"}
            for p, v in (
                ("FY2025", "93"),
                ("FY2026", "92"),
                ("FY2027", "92"),
                ("FY2028", "6637"),
                ("FY2029", "4768"),
                ("Thereafter", "12637"),
            )
        ],
    },
    "modules": [{"module": "CP-2", "ran_prior": True, "ran_current": True}],
    "limitations": {
        "earlier": [{"ref": "E1", "module": "CP-2", "text": "Segment data is not supplied."}],
        "current": [{"ref": "C1", "module": "CP-2", "text": "Segment data are not supplied."}],
    },
}
REAL_CURRENT = "# CP-1\n\nNew senior secured term loan of USD 3,000 million; test below 7.0x.\n"
REAL_PRIOR = "# CP-1\n\nThe earlier run listed 20 limitations.\n"
REAL_REGISTERS = """## Findings

### Key findings

@@SENTENCE@@

### What changed: the issuer

| Measure or fact | Earlier | Current | Cause | Effect on the credit view |
| --- | --- | --- | --- | --- |
| Total debt / EBITDA | 6.57x | 6.01x | Unresolved | Not comparable. |
| EBITDA / cash interest | 3.29x | 3.60x | Unresolved | Not comparable. |
| Cash | 6,261 US$m | 6,261 US$m | None | Same definition. |
| Undrawn committed facilities | 843 US$m | 843 US$m | None | Same definition. |
@@FACT@@

### What changed: the analysis

| Module | Status | Cause | Why |
| --- | --- | --- | --- |
| Credit view (CP-2) | Unchanged | Presentation | @@WHY@@ |

### Limitations ledger

| Earlier ref | Current ref | Limitation | Status | What closed it |
| --- | --- | --- | --- | --- |
| E1 | C1 | Segment data is missing. | Remaining | — |

## Calculations
@@GAPS@@"""


def real_text(sentence="Nothing changed.", fact="", why="The format differs.", gaps=""):
    text = REAL_REGISTERS.replace("@@SENTENCE@@", sentence).replace("@@FACT@@", fact)
    return text.replace("@@WHY@@", why).replace("@@GAPS@@", gaps)


REAL_HELD = (REAL_CURRENT, REAL_PRIOR)
ORDINARY_SENTENCES = [
    (
        "The credit picture is about the same since the earlier run: cash is unchanged at USD "
        "6,261 million and undrawn facilities at USD 843 million."
    ),
    (
        "The change is the analysis's, not the issuer's: both runs read the same FY2024 accounts "
        "as of 2024-09-30."
    ),
    (
        "Maturities are unchanged, with USD 6,637 million due in FY2028 and USD 4,768 million in "
        "FY2029."
    ),
    "Nothing falls due before 2028 beyond about USD 93 million a year.",
    "The current run adds USD 3,000 million of new secured debt raised after the year end.",
    "Eight modules ran in both runs and 12 ran only now.",
    "The earlier run listed 20 limitations; the current run lists 11.",
    "Leverage is 6.01x on EBITDA as defined against 6.57x on reported EBITDA, not comparable.",
    "A covenant test below 7.0x would change the view.",
    "Interest of USD 1,158 million is covered by EBITDA of USD 3,813 million.",
    "Undrawn facilities of USD 843 million are after USD 67 million of letters of credit.",
    "The 2027 notes and 2029 notes are unchanged in amount.",
]


def test_the_real_pair_mini_pack_with_valid_registers_is_accepted():
    assert cp8_issues(real_text(), REAL, REAL_HELD) == ()


@pytest.mark.parametrize("sentence", ORDINARY_SENTENCES)
def test_ordinary_sentences_about_the_real_pair(sentence):
    assert cp8_issues(real_text(sentence), REAL, REAL_HELD) == ()


def test_a_rounded_figure_is_refused_and_a_figure_nobody_holds_is_refused():
    rounded = "Cash was unchanged over 12 months at USD 6.3 billion."
    assert any("6.3" in i for i in cp8_issues(real_text(rounded), REAL, REAL_HELD))
    new_debt = ORDINARY_SENTENCES[4]
    assert any("3000" in i for i in cp8_issues(real_text(new_debt), REAL, ()))
    threshold = ORDINARY_SENTENCES[8]
    assert any("7.0" in i for i in cp8_issues(real_text(threshold), REAL, (REAL_PRIOR,)))


@pytest.mark.parametrize(
    ("where", "text", "fragment"),
    [
        ("sentence", "Leverage is 0.56 turns lower.", "difference"),
        ("sentence", "Leverage: −0.56x.", "difference"),
        ("sentence", "Leverage is 6.01x now. That is a fall of 0.56x.", "difference"),
        ("sentence", "Coverage rose by 0.31x.", "difference"),
        ("gaps", "Leverage differs by 0.56x between the runs.", "difference"),
        ("sentence", "Leverage is about 0.6x lower.", "0.6"),
        ("why", "Coverage is now 0.47x better.", "0.47"),
        ("gaps", "The headroom is USD 412 million.", "412"),
    ],
)
def test_a_withheld_difference_or_unheld_figure_is_refused(where, text, fragment):
    fields = {
        "sentence": {"sentence": text},
        "gaps": {"gaps": f"\n## Gaps\n\n{text}\n"},
        "why": {"why": text},
    }[where]
    found = cp8_issues(real_text(**fields), REAL, REAL_HELD)
    assert any(fragment in issue for issue in found), found


FACT_LOAN = "| New term loan | — | USD 3,000 million | New source | Adds secured debt. |\n"


def test_a_fact_row_may_carry_a_held_amount_and_never_a_pack_measures_value():
    assert cp8_issues(real_text(fact=FACT_LOAN), REAL, REAL_HELD) == ()
    assert any("3000" in i for i in cp8_issues(real_text(fact=FACT_LOAN), REAL, ()))
    leverage_row = "| Gross leverage | 6.57x | 6.01x | New source | Moved. |\n"
    found = cp8_issues(real_text(fact=leverage_row), REAL, REAL_HELD)
    assert any("name a pack measure by its exact label" in i for i in found), found


def test_the_checks_of_both_layers_agree_on_a_sentence_and_the_fact_row_that_holds_its_figure():
    from deploy_workflow.prose_checks import figure_issues

    text = real_text(ORDINARY_SENTENCES[4], fact=FACT_LOAN)
    assert figure_issues(text) + cp8_issues(text, REAL, REAL_HELD) == ()


def test_the_launch_checker_gives_cp8_both_runs_handoffs_to_hold_figures(tmp_path):
    from test_cpos_launch import good_task

    from deploy_workflow.owners.cpos_launch import checker

    prepared, task, _ = good_task(tmp_path, "CP-8")
    sentence = "The current run adds USD 3,000 million; a covenant test below 7.0x would change it."
    text = real_text(sentence).encode()
    sources = {**task.sources, "changes.json": json.dumps(REAL).encode()}
    check = checker(prepared.layout)

    def refused(handoffs, extra):
        fresh = dataclasses.replace(task, handoffs=handoffs, sources={**sources, **extra})
        said = " ".join(check(fresh, text))
        return {n for n in ("3000", "7.0") if f"the figure {n} is held in neither" in said}

    assert refused({"CP-1": b"# upstream"}, {}) == {"3000", "7.0"}
    assert refused({"CP-1": b"# up", "CP-2": b"Term loan USD 3,000 million."}, {}) == {"7.0"}
    assert refused({"CP-1": b"# up"}, {"prior/CP-2.md": b"Covenant below 7.0x."}) == {"3000"}


@pytest.mark.parametrize(
    "row",
    [
        "| Leverage change | — | 0.56x | New source | Lower debt. |",
        "| Leverage change | — | fell by 0.56x | New source | Lower debt. |",
        "| Leverage change | — | −0.56x | Unresolved | Lower debt. |",
        "| Coverage move | — | 0.31x | New source | Better cover. |",
        "| Leverage fell by 0.56x | — | — | Unresolved | Lower debt. |",
    ],
)
def test_a_difference_of_the_pack_is_never_printed_in_a_fact_row(row):
    found = cp8_issues(real_text(fact=row + "\n"), REAL, REAL_HELD)
    assert any("difference" in i for i in found), found
    assert cp8_issues(real_text(fact=FACT_LOAN), REAL, REAL_HELD) == ()


SEAM_FILE = Path(__file__).parent / "fixtures" / "changes-seam" / "rows.json"
SEAM = json.loads(SEAM_FILE.read_text())


def _seam_row(cells):
    return "| " + " | ".join(cells) + " |"


def test_the_seam_fixture_states_the_packs_measures():
    for key, measure in SEAM["measures"].items():
        assert measure == next(m for m in PACK["measures"] if m["key"] == key)


def _seam_text(case):
    leverage = next(r for r in REGISTERS.splitlines() if r.startswith("| Total debt / EBITDA"))
    old = {"leverage": leverage, "cash": CASH_ROW}[case["measure"]]
    quiet = "| Credit view (CP-2) | Unchanged | None | No change. |"
    first = _seam_row(case["cells"])
    first = first.removesuffix(" |") if case.get("unclosed") else first
    rows = "\n".join([first, *(_seam_row(r) for r in case.get("extra_rows", []))])
    return REGISTERS.replace(old, rows, 1).replace(
        "| Credit view (CP-2) | Strengthened | New period | Leverage fell. |", quiet, 1
    )


@pytest.mark.parametrize("case", SEAM["measure_rows"], ids=lambda c: c["name"])
def test_the_checker_accepts_a_measure_row_only_in_the_form_the_tab_reads(case):
    found = cp8_issues(_seam_text(case), PACK)
    assert (found == ()) is case["accepted"]
    assert any(case["refusal"] in i for i in found) if "refusal" in case else True


@pytest.mark.parametrize("case", SEAM["measure_rows"], ids=lambda c: c["name"])
def test_the_page_verdict_of_a_measure_is_the_one_the_fixture_states(case):
    """One reader: the verdict the page shows is derived here, by the checker's own reading of the
    register; for a handoff the checker accepts it is the verdict written beside the row."""
    got = page_verdicts(_seam_text(case), PACK)["measures"][case["measure"]]["kind"]
    assert got == case["page"]
    if case["accepted"]:
        assert case["page"] == case["verdict"]


@pytest.mark.parametrize("case", SEAM["module_cells"], ids=lambda c: c["name"])
def test_the_page_reads_a_module_row_only_where_the_checker_does(case):
    text = REGISTERS.replace("| Credit view (CP-2) |", f"| {case['cell']} |", 1)
    modules = page_verdicts(text, PACK)["modules"]
    if case["accepted"]:
        assert modules["CP-2"]["status"] == case["status"]
    else:
        assert "CP-2" not in modules


def test_the_page_reads_the_ledger_counts_and_a_missing_register_as_nothing():
    got = page_verdicts(REGISTERS, PACK)
    assert got["ledger"] == [["Closed", 1], ["Remaining", 1], ["New", 1], ["No longer stated", 0]]
    none = page_verdicts("## Findings\n\nNo registers.\n", PACK)
    assert none["ledger"] is None
    assert none["modules"] == {}
    assert none["measures"]["leverage"]["kind"] == "comparable"  # the pack says yes
    assert none["measures"]["cash"]["kind"] == "unjudged"  # the pack leaves it to CP-8
    assert page_verdicts(None, PACK)["measures"]["coverage"] == {
        "kind": "not_comparable",
        "label": "Not comparable",
        "reason": "the earlier run does not state it",
        "analysis_change": None,
    }


@pytest.mark.parametrize("case", SEAM["module_cells"], ids=lambda c: c["name"])
def test_the_checker_accepts_a_module_cell_only_in_the_form_the_tab_reads(case):
    text = REGISTERS.replace("| Credit view (CP-2) |", f"| {case['cell']} |", 1)
    assert (cp8_issues(text, PACK) == ()) is case["accepted"]


# --- the first real CP-8 run (tdg-proof-snapshot-opus-002): four defects read from its output -----
# Expected texts below are copied by hand from that run's accepted CP-8 handoff and CP-1 handoffs.

REAL_BASIS = "Basis: changes.json; prior/CP-1.md, page 4"  # the real handoff's Basis line
EARLIER_BASIS = (
    "Basis: Run comparison; Financial data foundation (CP-1), earlier run; Downside pathway (CP-2A)"
)


def _with_basis(basis: str) -> str:
    passage = f"### Bottom line\n\nAbout the same.\n{basis}\n\n"
    return with_row(LEVERAGE_ROW, passage=passage)


def test_cp8s_basis_line_accepts_the_comparison_and_an_earlier_run_handoff_by_name():
    assert cp8_issues(_with_basis(EARLIER_BASIS), PACK) == ()
    assert cp8_issues(_with_basis("Basis: Run comparison."), PACK) == ()  # the optional full stop


@pytest.mark.parametrize(
    ("basis", "fragment"),
    [
        (REAL_BASIS, "changes.json"),
        ("Basis: Run comparison; changes.json", "changes.json"),
        ("Basis: prior/CP-1.md", "prior/"),
        ("Basis: Financial data foundation (CP-1), prior/CP-1.md", "prior/"),
        ("Basis: Financial data foundation (CP-1), earlier run, page 4", "page"),
        ("Basis: Financial data foundation (CP-1), earlier run, pages 4–5", "page"),
        ("Basis: Financial data foundation (CP-1), p. 4", "page"),
        ("Basis: Financial data foundation (CP-1), pp. 4-5", "page"),
    ],
)
def test_cp8s_basis_line_refuses_pipeline_file_names_and_a_page_of_a_handoff(basis, fragment):
    found = cp8_issues(_with_basis(basis), PACK)
    assert any("Basis" in i and fragment in i for i in found), found


def test_the_library_reads_the_two_cp8_basis_forms_in_a_cp8_handoff_only_and_exactly():
    from deploy_workflow.credit_os_chips import basis_locators

    line = "Basis: Run comparison; Financial data foundation (CP-1), earlier run"
    assert basis_locators(line, {}, "CP-8") == []
    for module in (None, "CP-2"):  # no other module has an earlier run or a comparison pack
        assert len(basis_locators(line, {}, module)) == 2
    for item in (
        "annual-report.pdf, page 4 (CP-1), earlier run",
        "Run comparison, page 4",
        "Financial data foundation (CP-99), earlier run",  # no such module
        "Financial data foundation (CP-1), earlier run, page 4",
    ):
        (gap,) = basis_locators(f"Basis: {item}", {"annual-report.pdf": "k"}, "CP-8")
        assert gap["kind"] == "gap", item


ZERO = {**PACK["measures"][0]}
ZERO.update(
    comparable="judge",
    prior={**LEVERAGE_PRIOR, "value": "6.01", "period": "FY2024", "definition": "Gross."},
    current={**LEVERAGE_PRIOR, "value": "6.01", "period": "FY2024", "definition": "Gross, again."},
    difference="0.00",
    same_period=True,
)
PACK_ZERO = {**PACK, "measures": [ZERO, *PACK["measures"][1:]]}
ZERO_EFFECT = (
    "Same definition: difference 0.00x at the same date, so the leverage view is unchanged."
)


def zero_issues(cause: str, effect: str = ZERO_EFFECT) -> tuple[str, ...]:
    row = f"| Total debt / EBITDA | 6.01x (FY2024) | 6.01x (FY2024) | {cause} | {effect} |"
    return cp8_issues(REGISTERS.replace(LEVERAGE_ROW, row), PACK_ZERO)


def test_an_unchanged_measure_has_cause_none_and_unresolved_is_refused_for_it():
    assert zero_issues("None") == ()
    found = zero_issues("Unresolved")  # what the real handoff wrote
    assert any("`None`" in i and "Total debt / EBITDA" in i for i in found), found
    assert any("Cause 'New period'" in i for i in zero_issues("New period"))


def test_a_zero_difference_said_not_comparable_may_keep_unresolved():
    assert zero_issues("Unresolved", "Not comparable: the definition of gross debt differs.") == ()


def test_none_stays_refused_for_a_measure_with_a_difference():
    row = LEVERAGE_ROW.replace("New period", "None")
    found = cp8_issues(REGISTERS.replace(LEVERAGE_ROW, row), PACK)
    assert any("Cause 'None'" in i for i in found), found


PRESET_PACK = {**PACK, "prior": {"selection": "preset"}, "current": {"selection": "preset"}}
CHANGED_SET = "The pathway's module set changed between the runs."
REAL_WHY = "It ran only this time, and the pack does not say why the earlier run did not select it."


def module_issues(pack: dict, cause_a: str, why_a: str, cause_b: str, why_b: str):
    text = REGISTERS.replace(
        "| Research (CP-DR) | Not run this time | Method change | The research module was not "
        "selected. |",
        f"| Research (CP-DR) | Not run this time | {cause_a} | {why_a} |",
    ).replace(
        "| Macro (CP-2E) | New | New source | The module was added. |",
        f"| Macro (CP-2E) | New | {cause_b} | {why_b} |",
    )
    return cp8_issues(text, pack)


def test_modules_that_appear_or_go_between_two_preset_runs_are_a_method_change():
    ok = "Method change"
    assert module_issues(PRESET_PACK, ok, CHANGED_SET, ok, CHANGED_SET) == ()
    for cause in ("Unresolved", "New source", "New period"):
        found = module_issues(PRESET_PACK, ok, CHANGED_SET, cause, CHANGED_SET)
        assert any("CP-2E" in i and "`Method change`" in i for i in found), (cause, found)
        found = module_issues(PRESET_PACK, cause, CHANGED_SET, ok, CHANGED_SET)
        assert any("CP-DR" in i and "`Method change`" in i for i in found), (cause, found)


def test_the_phrase_the_pack_does_not_say_is_refused_between_two_preset_runs():
    found = module_issues(PRESET_PACK, "Method change", CHANGED_SET, "Method change", REAL_WHY)
    assert any("CP-2E" in i and "does not say" in i for i in found), found


@pytest.mark.parametrize(
    "pack",
    [
        {**PACK, "prior": {"selection": "preset"}, "current": {"selection": "explicit"}},
        {**PACK, "prior": {"selection": None}, "current": {"selection": "explicit"}},
        PACK,  # a pack of the earlier shape records no selection
    ],
)
def test_where_a_run_was_not_a_preset_the_cause_stays_unresolved(pack):
    assert module_issues(pack, "Unresolved", REAL_WHY, "Unresolved", REAL_WHY) == ()


def test_a_prior_with_no_recorded_selection_counts_as_a_preset_run():
    """tdg-reader-format-001's manifest has no `selection` key; it was a base because it ran the
    pathway's lead module. The pack states null as recorded; the rule still fires."""
    pack = {**PACK, "prior": {"selection": None}, "current": {"selection": "preset"}}
    found = module_issues(pack, "Unresolved", REAL_WHY, "Unresolved", REAL_WHY)
    assert any("CP-DR" in i and "`Method change`" in i for i in found), found
    assert any("CP-2E" in i and "does not say" in i for i in found), found
    assert module_issues(pack, "Method change", CHANGED_SET, "Method change", CHANGED_SET) == ()


def test_a_prior_without_a_recorded_selection_is_stated_null_in_the_pack(tmp_path):
    make_run(tmp_path, "old", as_of="2024-12-31", selection=None, modules=("CP-0", "CP-1", "CP-2"))
    found = find_prior(
        tmp_path,
        folder="cur",
        issuer_id="nbg",
        **ME,
        pathway="credit_snapshot",
        as_of="2025-03-31",
        method=method(),
    )
    assert found is not None and found[0].selection is None
    pack = build_pack(
        found[0],
        {"CP-1": "x"},
        {"CP-1": "x"},
        as_of="2025-03-31",
        pathway="credit_snapshot",
        selection="preset",
    )
    assert pack["prior"]["selection"] is None  # null stays null: no value is invented


def test_the_pack_states_both_selections_and_the_schema_says_so():
    prior = _prior().model_copy(update={"selection": "preset"})
    pack = build_pack(
        prior,
        {"CP-1": "x"},
        {"CP-1": "x"},
        as_of="2025-03-31",
        pathway="credit_snapshot",
        selection="preset",
    )
    assert pack["schema"] == "cpos-changes/3"
    assert pack["prior"]["selection"] == "preset"
    assert pack["current"]["selection"] == "preset"
    unknown = build_pack(
        _prior(), {"CP-1": "x"}, {"CP-1": "x"}, as_of="2025-03-31", pathway="credit_snapshot"
    )
    assert (unknown["prior"]["selection"], unknown["current"]["selection"]) == (None, None)


def test_a_found_prior_run_carries_the_selection_its_manifest_recorded(tmp_path):
    make_run(tmp_path, "full", as_of="2024-12-31", selection="preset")
    found = find_prior(
        tmp_path,
        folder="cur",
        issuer_id="nbg",
        **ME,
        pathway="credit_snapshot",
        as_of="2025-03-31",
        method=method(),
    )
    assert found is not None and found[0].selection == "preset"


# D3. The two real CP-1 handoffs state gross debt, in two layouts no exact rule reads together.
REAL_PRIOR_DEBT = (
    "| Statement label / metric | FY2024 | FY2023 | Unit and quantity / status | Source |\n"
    "|---|---:|---:|---|---|\n"
    "| Gross financial debt including finance leases and securitization | 25068 | 19913 "
    "| USD million; calculated C01; principal, not net carrying value | f.jsonl, pages 144–145 |\n"
    "| Net financial debt | 18807 | 16441 | USD million; calculated C02; gross debt less "
    "reported cash, no dividend adjustment | f.jsonl, page 120 |\n"
)
REAL_CURRENT_DEBT = (
    "| Metric | FY2024 | FY2023 | Definition / identity | Source |\n"
    "|---|---|---|---|---|\n"
    "| Total debt (gross, incl. securitization), USD m | 25,068 | 19,913 "
    "| Calculations C01, C03 | calculation C01 |\n"
    "| Net debt (reported balance sheet), USD m | 18,807 | 16,441 "
    "| Calculations C02, C04 | calculation C02 |\n"
)


def test_the_net_debt_change_reason_says_what_the_comparison_reads_not_that_debt_is_unstated():
    pack = pair_pack(
        handoff("CP-1", "Earlier.", tables=REAL_PRIOR_DEBT),
        handoff("CP-1", "Now.", tables=REAL_CURRENT_DEBT),
    )
    assert "net_debt_change" not in pack
    assert pack["omitted"]["net_debt_change"] == (
        "gross debt is not read from either run's CP-1 (the comparison reads the Gross debt "
        'column of the CP-1 "Net debt data" table)'
    )


def test_a_pack_from_two_runs_with_the_net_debt_table_states_the_hand_computed_change():
    """Hand-computed: 2,100 - 300 = 1,800 and 2,000 - 250 = 1,750; gross fell 100, cash fell 50."""
    pack = bridge_pack()
    assert pack["net_debt_change"]["prior_net_debt"] == "1800"
    assert pack["net_debt_change"]["change_in_gross_debt"] == "-100"
    assert pack["net_debt_change"]["change_in_cash"] == "-50"
    assert pack["net_debt_change"]["current_net_debt"] == "1750"
    found = measures_of(pack)
    assert (found["gross_debt"]["comparable"], found["net_debt"]["comparable"]) == ("yes", "yes")


@pytest.mark.parametrize(("lacking", "run"), [("prior", "earlier"), ("current", "current")])
def test_a_run_without_the_net_debt_table_leaves_the_change_out_and_names_that_run(lacking, run):
    with_table = handoff(
        "CP-1",
        "x",
        tables=liquidity("| FY2024 | 250 | 400 | US$m | Cash. |")
        + netdebt("2,000", "250", "1,750", "FY2024"),
    )
    without = handoff("CP-1", "x", tables=liquidity("| FY2023 | 300 | 450 | US$m | Cash. |"))
    prior, current = (without, with_table) if lacking == "prior" else (with_table, without)
    pack = pair_pack(prior, current)
    assert "net_debt_change" not in pack
    assert pack["omitted"]["net_debt_change"] == (
        f"gross debt cannot be compared (the {run} run does not state it)"
    )


def test_the_net_debt_change_takes_all_three_figures_from_the_net_debt_table_row_alone():
    """Each run's liquidity table also states a later period; the change must not read it.
    Hand-computed: 2,100 - 300 = 1,800 and 2,000 - 200 = 1,800; gross fell 100, cash fell 100."""
    earlier = handoff(
        "CP-1",
        "Earlier.",
        tables=liquidity(
            "| FY2023 | 300 | 450 | US$m | Cash. |\n| FY2024 | 250 | 400 | US$m | Cash. |"
        )
        + netdebt("2,100", "300", "1,800", "FY2023"),
    )
    later = handoff(
        "CP-1",
        "Now.",
        tables=liquidity("| FY2025 | 999 | 400 | US$m | Cash. |")
        + netdebt("2,000", "200", "1,800", "FY2025"),
    )
    pack = pair_pack(earlier, later)
    # Shown: both rows are internally consistent and the periods differ between the runs, which
    # the pack states in each measure's period; the liquidity table's cash plays no part.
    assert {k: v for k, v in pack["net_debt_change"].items() if k != "convention"} == {
        "unit": "US$m",
        "prior_net_debt": "1800",
        "change_in_gross_debt": "-100",
        "change_in_cash": "-100",
        "current_net_debt": "1800",
        "same_period": False,
        "prior_period": "FY2023",
        "current_period": "FY2025",
        "prior_gross_debt": "2100",
        "prior_cash": "300",
        "current_gross_debt": "2000",
        "current_cash": "200",
    }
    assert "net_debt_change" not in pack["omitted"]


def test_a_net_debt_row_that_does_not_add_up_is_omitted_with_a_true_reason():
    earlier = handoff("CP-1", "x", tables=netdebt("2,100", "300", "1,700", "FY2023"))
    later = handoff("CP-1", "y", tables=netdebt("2,000", "250", "1,750", "FY2024"))
    pack = pair_pack(earlier, later)
    assert (
        pack["omitted"]["net_debt_change"] == "a run's net debt is not its gross debt less its cash"
    )


def test_a_net_debt_row_without_its_cash_is_omitted_naming_the_cash():
    gap = "Not supplied: not read"
    earlier = handoff("CP-1", "x", tables=netdebt("2,100", gap, "1,800", "FY2023"))
    later = handoff("CP-1", "y", tables=netdebt("2,000", "250", "1,750", "FY2024"))
    pack = pair_pack(earlier, later)
    assert pack["omitted"]["net_debt_change"] == "cash cannot be compared (a value is not stated)"


# --- one period's net debt change (owner, 2026-11-12): the analysis changed, not the issuer ---


def _bridge(prior_period, current_period, current=("2,000", "250", "1,750")):
    prior = handoff("CP-1", "Earlier.", tables=netdebt("2,100", "300", "1,800", prior_period))
    now = handoff("CP-1", "Now.", tables=netdebt(*current, current_period))
    return pair_pack(prior, now)


@pytest.mark.parametrize(
    ("prior_period", "current_period", "flag"),
    [
        ("FY2024", "FY2024", True),
        ("FY2024", "FY2024 / 2024-09-30", True),  # one period, written two ways
        ("FY2023", "FY2024", False),
    ],
)
def test_the_net_debt_change_says_whether_both_rows_are_one_period(
    prior_period, current_period, flag
):
    change = _bridge(prior_period, current_period)["net_debt_change"]
    assert change["same_period"] is flag
    assert (change["prior_period"], change["current_period"]) == (prior_period, current_period)
    # the stated balances of each row, read and not computed
    assert (change["prior_gross_debt"], change["prior_cash"]) == ("2100", "300")
    assert (change["current_gross_debt"], change["current_cash"]) == ("2000", "250")


def test_equal_net_debt_rows_of_one_period_are_flagged_with_zero_differences():
    change = _bridge("FY2024", "FY2024", ("2,100", "300", "1,800"))["net_debt_change"]
    assert change["same_period"] is True
    assert (change["change_in_gross_debt"], change["change_in_cash"]) == ("0", "0")


def _nd_measure(key, label, values, difference, same_period=True):
    prior, current = values
    side = {**CASH_PRIOR, "label": label, "period": "FY2024"}
    return {
        "key": key,
        "label": label,
        "unit": "US$m",
        "comparable": "yes",
        "reason": None,
        "prior": {**side, "value": prior},
        "current": {**side, "value": current},
        "difference": difference,
        "same_period": same_period,
    }


def _ndpack(same_period=True, with_flag=True):
    change = {
        "unit": "US$m",
        "prior_net_debt": "6190",
        "change_in_gross_debt": "-110",
        "change_in_cash": "-30",
        "current_net_debt": "6110",
        "convention": "net debt = gross debt - cash",
    }
    if with_flag:
        change |= {
            "same_period": same_period,
            "prior_period": "FY2024",
            "current_period": "FY2024",
            "prior_gross_debt": "7100",
            "prior_cash": "910",
            "current_gross_debt": "6990",
            "current_cash": "880",
        }
    return {
        **PACK,
        "measures": [
            *PACK["measures"],
            _nd_measure("gross_debt", "Gross debt", ("7100", "6990"), "-110", same_period),
            _nd_measure("net_debt", "Net debt", ("6190", "6110"), "-80", same_period),
        ],
        "net_debt_change": change,
    }


@pytest.mark.parametrize(
    "sentence",
    [
        "Net debt fell by 80 US$m.",
        "Gross debt fell by 110 US$m.",
        "Cash fell by 30 US$m.",
        "Cash is 30 US$m lower.",
    ],
)
def test_a_same_period_net_debt_difference_is_printed_in_no_passage(sentence):
    assert cp8_issues(with_row(LEVERAGE_ROW, sentence + "\n\n"), _ndpack()), "accepted"


def test_the_two_values_of_a_same_period_net_debt_may_be_stated():
    said = "Net debt is 6,190 US$m earlier and 6,110 US$m now; cash is 910 and 880 US$m.\n\n"
    assert cp8_issues(with_row(LEVERAGE_ROW, said), _ndpack()) == ()


@pytest.mark.parametrize("pack", [_ndpack(same_period=False), _ndpack(with_flag=False)])
def test_a_net_debt_change_of_two_periods_or_without_the_flag_may_be_said_to_have_moved(pack):
    assert cp8_issues(with_row(LEVERAGE_ROW, "Cash fell by 30 US$m.\n\n"), pack) == ()


# --- a withheld difference is printed in no register cell but its own issuer row's Effect ------
# (owner, 2026-11-12: "fine, PR and merge"). Expectations hand-written.

WHY_CELL = "| The module was added. |"
LEDGER_CELL = "| A hedging data gap. |"
NC_ROW = same_period_row("Not comparable: EBITDA basis differs.")


def _in_cell(handoff: str, cell: str, sentence: str) -> str:
    assert cell in handoff
    return handoff.replace(cell, f"| {sentence} |", 1)


def _no_pack():
    measure = {**SAME, "comparable": "no", "same_period": False, "reason": "Definitions differ."}
    return {**PACK, "measures": [measure, *PACK["measures"][1:]]}


WITHHELD_KINDS = {
    "pack marks no": (_no_pack(), with_row(NC_ROW), "Leverage fell by 0.56x.", "0.56"),
    "said Not comparable": (PACK2, with_row(NC_ROW), "Leverage fell by 0.56x.", "0.56"),
    "same period, no Same definition": (
        PACK2,
        with_row(same_period_row("Leverage moved.")),
        "Leverage fell by 0.56x.",
        "0.56",
    ),
    "net debt, cash": (_ndpack(), with_row(LEVERAGE_ROW), "Cash fell by 30 US$m.", "30"),
    "net debt, net debt": (
        _ndpack(),
        with_row(LEVERAGE_ROW),
        "Net debt is 80 US$m lower.",
        "80",
    ),
    "net debt, gross debt": (
        _ndpack(),
        with_row(LEVERAGE_ROW),
        "Gross debt fell by 110 US$m.",
        "110",
    ),
}


@pytest.mark.parametrize("kind", list(WITHHELD_KINDS))
@pytest.mark.parametrize("cell", [WHY_CELL, LEDGER_CELL], ids=["analysis Why", "ledger"])
def test_a_withheld_difference_is_refused_in_the_analysis_register_and_the_ledger(kind, cell):
    pack, handoff, sentence, figure = WITHHELD_KINDS[kind]
    found = cp8_issues(_in_cell(handoff, cell, sentence), pack)
    assert any(figure in i and "difference" in i for i in found), found


def test_a_same_definition_correction_may_print_its_own_difference_in_its_issuer_row():
    row = same_period_row("Same definition; leverage is 0.56x lower after the correction.")
    assert cp8_issues(with_row(row.replace("Unresolved", "Correction")), PACK2) == ()


def test_the_exemption_is_that_measures_issuer_row_only():
    row = same_period_row("Same definition; leverage is 0.56x lower after the correction.")
    handoff = with_row(row.replace("Unresolved", "Correction"))
    assert cp8_issues(handoff, PACK2) == ()
    found = cp8_issues(_in_cell(handoff, WHY_CELL, "Leverage fell by 0.56x."), PACK2)
    assert any("0.56" in i and "difference" in i for i in found), found
    fact = "| Refinancing | — | — | New source | Net debt fell by 80 US$m. |"
    found = cp8_issues(with_row(LEVERAGE_ROW + "\n" + fact), _ndpack())
    assert any("80" in i and "difference" in i for i in found), found


def _zero_pack():
    pack = _ndpack()
    pack["net_debt_change"] |= {
        "change_in_cash": "0",
        "current_cash": "910",
        "change_in_gross_debt": "0",
        "current_gross_debt": "7100",
        "current_net_debt": "6190",
    }
    pack["measures"] = [m for m in pack["measures"] if m["key"] not in ("gross_debt", "net_debt")]
    return pack


def _own_value_pack():
    pack = _ndpack()
    pack["net_debt_change"] |= {"prior_cash": "60", "current_cash": "30", "change_in_cash": "-30"}
    return pack


@pytest.mark.parametrize(
    ("pack", "handoff", "sentence"),
    [
        (PACK2, with_row(NC_ROW), "Leverage is 6.57x earlier and 6.01x now."),
        (_ndpack(), with_row(LEVERAGE_ROW), "Net debt is 6,190 US$m earlier and 6,110 US$m now."),
        (_zero_pack(), with_row(LEVERAGE_ROW), "Net debt is 6,190 US$m in both runs."),
        (_ndpack(same_period=False), with_row(LEVERAGE_ROW), "Cash fell by 30 US$m."),
        (_ndpack(), with_row(LEVERAGE_ROW), "Total debt / EBITDA was 4.20x earlier."),
        (_own_value_pack(), with_row(LEVERAGE_ROW), "Cash is 60 US$m earlier and 30 US$m now."),
    ],
    ids=["both values", "net debt values", "zero", "unflagged", "other measure", "own value"],
)
@pytest.mark.parametrize("cell", [WHY_CELL, LEDGER_CELL], ids=["analysis Why", "ledger"])
def test_a_register_cell_stating_values_or_a_quotable_difference_is_still_accepted(
    pack, handoff, sentence, cell
):
    assert cp8_issues(_in_cell(handoff, cell, sentence), pack) == ()


_POST_BS_HEAD = (
    "### Post-balance-sheet adjustments\n\n"
    "| Event | Date | Amount | Pro forma net debt | Pro forma net leverage "
    "| Reporting unit | Basis and limitation |\n| --- | --- | --- | --- | --- | --- | --- |\n"
)
_POST_BS_NONE = (
    _POST_BS_HEAD + "| None found in the sources read | — | — | — | — | US$m | Read. |\n\n"
)
_POST_BS_EVENT = (
    _POST_BS_HEAD
    + "| Notes issued | 2025-02-05 | 500 | 1625 | 3.4 | US$m | Proceeds not applied. |\n\n"
)


@pytest.mark.parametrize("where", ["after", "before"])
@pytest.mark.parametrize("table", [_POST_BS_NONE, _POST_BS_EVENT], ids=["none row", "event row"])
def test_the_post_balance_sheet_table_leaves_the_changes_pack_unchanged(table, where):
    """Decision 10: the table is CP-1's and adds no measure; the pack ignores it in any place."""

    def cp1(gross: str, cash: str, net: str, period: str, with_table: bool) -> str:
        nd = netdebt(gross, cash, net, period)
        if not with_table:
            return "## Findings\n\n" + nd
        return "## Findings\n\n" + (nd + table if where == "after" else table + nd)

    base = pair_pack(
        cp1("1500", "300", "1200", "FY2023", False), cp1("1400", "275", "1125", "FY2024", False)
    )
    got = pair_pack(
        cp1("1500", "300", "1200", "FY2023", True), cp1("1400", "275", "1125", "FY2024", True)
    )
    assert got == base
    found = measures_of(got)
    assert set(found) == set(measures_of(base))
    assert not any("pro_forma" in key for key in found)
    # Hand-written from the fixture: gross debt 1500 -> 1400 and net debt 1200 -> 1125, US$m.
    assert (found["gross_debt"]["prior"]["value"], found["gross_debt"]["current"]["value"]) == (
        "1500",
        "1400",
    )
    assert found["gross_debt"]["difference"] == "-100"
    assert (found["net_debt"]["prior"]["value"], found["net_debt"]["current"]["value"]) == (
        "1200",
        "1125",
    )
    assert found["net_debt"]["difference"] == "-75"
    assert found["net_debt"]["unit"] == "US$m"


# --- a withheld difference without a unit is refused too (owner, 2026-11-12: "Yes, fix both") ---
# A whole number below 100 without a unit is a count everywhere but here: for the withheld-
# difference rule only, a bare number equal in magnitude to a withheld size is refused (same
# lines, same exemptions as with a unit). Expectations hand-written. Recorded limits: a bare count
# equal to a withheld size ("30 limitations" while a difference of 30 is withheld) is refused, and
# a size written in words ("thirty") is not read.

NC_CASH = (
    "| Cash | 300 US$m (FY2023) | 250 US$m (FY2024) | Unresolved "
    "| Not comparable: the definition changed. |"
)
GAPS = "\n## Gaps\n\n{}\n"


def _cash_pack(mark):
    cash = {**PACK["measures"][1], "comparable": mark}
    return {**PACK, "measures": [PACK["measures"][0], cash, *PACK["measures"][2:]]}


def _cash_nc_text(**kw):
    return with_row(LEVERAGE_ROW, **kw).replace(CASH_ROW, NC_CASH)


def _lever_text(**kw):
    return with_row(LEVERAGE_ROW, **kw)


def _nc_text(**kw):
    return with_row(NC_ROW, **kw)


BARE_KINDS = {
    "pack marks no": (_cash_pack("no"), _cash_nc_text, "Cash fell by 50."),
    "said Not comparable": (PACK, _cash_nc_text, "Cash fell by 50."),
    "same period flagged": (PACK2, _nc_text, "Leverage fell by 0.56."),
    "net debt, cash": (_ndpack(), _lever_text, "Cash fell by 30."),
    "net debt, net debt": (_ndpack(), _lever_text, "Net debt is 80 lower."),
}


def _bare_places(build, sentence):
    return {
        "passage": build(passage=sentence + "\n\n"),
        "gaps": build(gaps=GAPS.format(sentence)),
        "why": _in_cell(build(), WHY_CELL, sentence),
        "ledger": _in_cell(build(), LEDGER_CELL, sentence),
    }


@pytest.mark.parametrize("kind", list(BARE_KINDS))
@pytest.mark.parametrize("place", ["passage", "gaps", "why", "ledger"])
def test_a_withheld_difference_without_a_unit_is_refused_wherever_one_with_a_unit_is(kind, place):
    pack, build, sentence = BARE_KINDS[kind]
    assert cp8_issues(build(), pack) == ()
    found = cp8_issues(_bare_places(build, sentence)[place], pack)
    assert any("difference" in i and "reword" in i for i in found), found


@pytest.mark.parametrize("sentence", ["Cash moved -30.", "Cash fell by -30.", "Cash fell by 30 ."])
def test_a_signed_or_spaced_bare_withheld_difference_is_refused(sentence):
    found = cp8_issues(with_row(LEVERAGE_ROW, sentence + "\n\n"), _ndpack())
    assert any("30" in i and "difference" in i for i in found), found


def test_the_refusal_names_the_figure_and_the_measure():
    found = cp8_issues(with_row(LEVERAGE_ROW, "Cash fell by 30.\n\n"), _ndpack())
    assert any("figure 30" in i and "difference of Cash" in i for i in found), found


def test_a_bare_decimal_withheld_difference_is_refused():
    found = cp8_issues(with_row(LEVERAGE_ROW, "Leverage fell by 0.56.\n\n"), PACK2)
    assert any("0.56" in i and "difference" in i for i in found), found


@pytest.mark.parametrize(
    "sentence",
    [
        "The three facilities are secured.",
        "Twelve of 12 modules ran.",
        "The pack lists 7 limitations.",
    ],
)
def test_a_bare_count_that_equals_no_withheld_size_is_accepted(sentence):
    assert cp8_issues(with_row(LEVERAGE_ROW, sentence + "\n\n"), _ndpack()) == ()


def test_a_module_code_or_list_number_is_no_bare_count():
    pack = _ndpack()
    pack["net_debt_change"] |= {"change_in_cash": "-2", "current_cash": "908"}
    text = with_row(LEVERAGE_ROW, "1. The credit view (CP-2) ran.\n\n")
    assert cp8_issues(text, pack) == ()


def test_a_bare_withheld_difference_is_accepted_in_its_own_issuer_row():
    row = same_period_row("Same definition; leverage is 0.56 lower after the correction.")
    assert cp8_issues(with_row(row.replace("Unresolved", "Correction")), PACK2) == ()
    net = (
        "| Net debt | 6190 US$m (FY2024) | 6110 US$m (FY2024) | Correction "
        "| Same definition; net debt is 80 lower after the correction. |"
    )
    assert cp8_issues(with_row(LEVERAGE_ROW + "\n" + net), _ndpack()) == ()
    elsewhere = net.replace("Net debt |", "Refinancing |")
    found = cp8_issues(with_row(LEVERAGE_ROW + "\n" + elsewhere), _ndpack())
    assert any("80" in i and "difference" in i for i in found), found


def test_a_bare_size_equal_to_the_measures_own_value_is_accepted():
    pack = _ndpack()
    pack["net_debt_change"] |= {"prior_cash": "60", "current_cash": "30", "change_in_cash": "-30"}
    assert cp8_issues(with_row(LEVERAGE_ROW, "Cash is 60 earlier and 30 now.\n\n"), pack) == ()


def test_a_zero_difference_withholds_nothing():
    said = "Net debt is 6,190 in both runs; 0 changed.\n\n"
    assert cp8_issues(with_row(LEVERAGE_ROW, said), _zero_pack()) == ()


def test_a_bare_count_is_still_no_figure_of_a_held_line():
    # K10 is untouched: an unheld whole number below 100 is still a count.
    said = "Seven covenants are tested.\n\nThere are 77 of them.\n\n"
    assert cp8_issues(with_row(LEVERAGE_ROW, said), PACK) == ()


# --- fix round 1: a line-start number is a list marker only on a real list item ---------------


@pytest.mark.parametrize(
    ("passage", "size"),
    [
        ("Gross debt changed by a total of\n110. The rest holds.\n\n", "110"),
        ("Gross debt changed by a total of\n110) in all.\n\n", "110"),
        ("Cash fell by\n30. The rest holds.\n\n", "30"),
        ("Liquidity is about\n437. That is new.\n\n", "437"),
    ],
)
def test_a_number_starting_a_continuation_line_is_a_figure(passage, size):
    found = cp8_issues(with_row(LEVERAGE_ROW, passage), _ndpack())
    assert any(size in i for i in found), found


def test_a_number_starting_a_fact_rows_effect_cell_is_a_figure():
    row = "| Refinancing | — | — | New source | 80. Net debt is lower. |"
    found = cp8_issues(with_row(LEVERAGE_ROW + "\n" + row), _ndpack())
    assert any("80" in i and "difference" in i for i in found), found


@pytest.mark.parametrize(
    "passage",
    [
        "80. Net debt is the largest item.\n\n",
        "Findings follow.\n\n80. Net debt is the largest item.\n\n",
        "1. First point.\n80. Net debt is the largest item.\n\n",
    ],
)
def test_a_real_list_item_number_equal_to_a_withheld_size_is_accepted(passage):
    assert cp8_issues(with_row(LEVERAGE_ROW, passage), _ndpack()) == ()


@pytest.mark.parametrize(
    "sentence",
    [
        "The period ends 30 September 2024.",
        "The period ends 30th Sep 2024.",
        "The period ends September 30 2024.",
        "The period ends Sep 30 2024.",
    ],
)
def test_a_day_of_month_equal_to_a_withheld_size_is_no_size(sentence):
    assert cp8_issues(with_row(LEVERAGE_ROW, sentence + "\n\n"), _ndpack()) == ()


def test_a_number_near_but_not_beside_a_month_is_still_a_size():
    said = "Cash fell by 30 in September.\n\n"
    found = cp8_issues(with_row(LEVERAGE_ROW, said), _ndpack())
    assert any("30" in i and "difference" in i for i in found), found


def test_the_verdict_words_doubled_in_another_cell_and_the_effect_cell_are_refused():
    row = (
        "| Total debt / EBITDA | Not comparable: 6.57x (FY2023) | 6.01x (FY2023) | Unresolved "
        "| Not comparable: EBITDA basis differs. |"
    )
    found = cp8_issues(with_row(row), PACK2)
    assert any("Earlier cell" in i and "not comparable" in i for i in found), found


# --- the withheld-size limits: wrapped bullets, dates need a year, numbers in words ---------------


def _says(passage, pack=None):
    return cp8_issues(with_row(LEVERAGE_ROW, passage + "\n\n"), pack or _ndpack())


@pytest.mark.parametrize(
    "passage",
    [
        "- Cash fell by\n30. The rest holds.",
        "  - Cash fell by\n  30. The rest holds.",
        "* Cash fell by\n30) The rest holds.",
        "- First point.\n80. Net debt is the largest item.",
    ],
)
def test_a_number_wrapped_onto_a_line_after_a_bullet_is_a_figure(passage):
    assert any("figure " in i for i in _says(passage))


@pytest.mark.parametrize(
    "passage",
    [
        "- item\n1. first sub-item",
        "Findings.\n\n30. A numbered item.",
        "1. First.\n30. A numbered item.",
    ],
)
def test_a_list_marker_after_a_bullet_one_or_elsewhere_is_no_figure(passage):
    assert _says(passage) == ()


@pytest.mark.parametrize(
    "sentence",
    [
        "Cash fell by 30 March-to-September.",
        "Cash fell by 30 Mar-to-Sep.",
        "Cash fell by 30 March quarter on March quarter.",
        "Cash fell by 30 May be restated.",
        "The period ends 30 September.",
    ],
)
def test_a_day_beside_a_month_without_a_year_is_a_number(sentence):
    assert any("figure 30" in i for i in _says(sentence))


@pytest.mark.parametrize(
    "sentence",
    [
        "The period ends 30 September 2024.",
        "The period ends 30th Sep 2024.",
        "The period ends September 30 2024.",
        "The period ends Sep 30, 2024.",
        "The period ends September 30, 2024.",
        "The period ends 30 September, 2024.",
    ],
)
def test_a_day_of_a_complete_date_is_no_size(sentence):
    assert _says(sentence) == ()


def test_a_full_date_on_a_line_hides_no_other_figure():
    found = _says("September 30, 2024 US$m 437 is held nowhere.")
    assert any("437" in i and "held in neither" in i for i in found), found
    assert _says("September 30, 2024 US$m 7,100 is the gross debt.") == ()
    found = _says("On 30 September 2024 cash fell by 30 US$m.")
    assert any("figure 30" in i for i in found), found


def _cash_163_pack():
    pack = _ndpack()
    pack["net_debt_change"] |= {"change_in_cash": "-163", "current_cash": "747"}
    return pack


@pytest.mark.parametrize(
    ("sentence", "pack"),
    [
        ("Cash fell by thirty.", None),
        ("Cash fell by THIRTY.", None),
        ("Net debt is eighty lower.", None),
        ("Gross debt changed by one hundred and ten.", None),
        ("Gross debt changed by One Hundred Ten.", None),
        ("Cash fell by one hundred and sixty-three.", _cash_163_pack()),
        ("Cash fell by one hundred sixty three.", _cash_163_pack()),
        ("Cash fell by one hundred sixty-three.", _cash_163_pack()),
    ],
)
def test_a_withheld_size_written_in_words_is_refused(sentence, pack):
    found = _says(sentence, pack)
    assert any("difference" in i and "reword" in i for i in found), found


def test_a_large_withheld_size_in_words_is_refused():
    pack = _ndpack()
    pack["net_debt_change"] |= {"change_in_cash": "-2005", "current_cash": "-1095"}
    for sentence in ("Cash fell by two thousand five.", "Cash fell by two thousand and five."):
        assert any("figure 2005" in i for i in _says(sentence, pack)), sentence
    pack["net_debt_change"] |= {"change_in_cash": "-250000", "current_cash": "-249090"}
    assert any("figure 250000" in i for i in _says("It fell by two hundred fifty thousand.", pack))


@pytest.mark.parametrize(
    "sentence",
    [
        "Cash fell by forty.",
        "Cash fell by thirty-one.",
        "The one covenant is tested.",
        "The thirtieth covenant is tested.",
        "A hundred covenants and a dozen facilities.",
        "Cash fell by thirty point five.",
        "Cash fell by twenty and forty.",
    ],
)
def test_a_number_in_words_that_is_no_withheld_size_is_accepted(sentence):
    assert _says(sentence) == ()


def test_the_word_one_is_never_read_as_a_size():
    pack = _ndpack()
    pack["net_debt_change"] |= {"change_in_cash": "-1", "current_cash": "909"}
    assert _says("One facility matured, and no one asked.", pack) == ()


def test_a_size_in_words_is_accepted_in_its_own_issuer_row():
    net = (
        "| Net debt | 6190 US$m (FY2024) | 6110 US$m (FY2024) | Correction "
        "| Same definition; net debt is eighty lower after the correction. |"
    )
    assert cp8_issues(with_row(LEVERAGE_ROW + "\n" + net), _ndpack()) == ()
    elsewhere = net.replace("Net debt |", "Refinancing |")
    found = cp8_issues(with_row(LEVERAGE_ROW + "\n" + elsewhere), _ndpack())
    assert any("80" in i and "difference" in i for i in found), found


def _cash_pack(change: str, cash: str):
    pack = _ndpack()
    pack["net_debt_change"] |= {"change_in_cash": change, "current_cash": cash}
    return pack


@pytest.mark.parametrize(
    ("sentence", "pack", "size"),
    [
        ("On 30 June 4370 US$m was drawn.", None, "4370"),
        ("At March 12 4370 US$m of debt matured.", None, "4370"),
        ("At 30 June 1006 US$m of cash was used.", _cash_pack("-1006", "-96"), "1006"),
        ("March 12 1006 is the cash change.", _cash_pack("-1006", "-96"), "1006"),
        ("It was due on 31 December 2100 US$m.", None, "2100"),
    ],
)
def test_a_four_digit_figure_after_a_yearless_date_is_still_read(sentence, pack, size):
    found = _says(sentence, pack)
    assert any(size in i for i in found), found


@pytest.mark.parametrize(
    ("sentence", "pack"),
    [
        ("Cash is zero point five of the facility.", _cash_pack("-5", "905")),
        ("Two thirds of the debt is fixed.", _cash_pack("-2", "908")),
        ("Two-thirds of the debt is fixed.", _cash_pack("-2", "908")),
        ("Two and a half turns of leverage.", _cash_pack("-2", "908")),
        ("The twenty-first covenant test.", _cash_pack("-20", "890")),
        ("The thirty-first covenant test.", None),
        ("The one hundred and first covenant test.", _cash_pack("-100", "810")),
        ("Three quarters of the debt is fixed.", _cash_pack("-3", "907")),
    ],
)
def test_a_decimal_fraction_or_ordinal_in_words_is_not_read_in_part(sentence, pack):
    assert _says(sentence, pack) == ()


@pytest.mark.parametrize(
    ("sentence", "pack", "size"),
    [
        ("Cash fell by thirty and second-lien debt was repaid.", None, "30"),
        ("Cash fell by thirty and first-lien leverage rose.", None, "30"),
        ("Cash fell by thirty and half the facility was drawn.", None, "30"),
        (
            "Gross debt fell by one hundred and ten and a quarter of the notes were repaid.",
            None,
            "110",
        ),
        ("Cash fell by thirty quarter-on-quarter.", None, "30"),
        ("Cash fell by thirty second-lien loans.", None, "30"),
        ("At that point thirty was drawn from cash.", None, "30"),
        ("Cash showed a thirty-point swing.", None, "30"),
        ("Cash is point five of the facility.", _cash_pack("-5", "905"), "5"),
    ],
)
def test_a_spelled_size_beside_an_ordinal_looking_word_is_still_read(sentence, pack, size):
    found = _says(sentence, pack)
    assert any(f"figure {size} is the difference" in i for i in found), found


@pytest.mark.parametrize(
    ("sentence", "pack"),
    [
        ("The thirty-first covenant test.", None),
        ("Two thirds of the debt is fixed.", _cash_pack("-2", "908")),
        ("Two halves of the debt are fixed.", _cash_pack("-2", "908")),
        ("The one hundred and first covenant test.", _cash_pack("-100", "810")),
        ("Cash is zero point five of the facility.", _cash_pack("-5", "905")),
    ],
)
def test_a_spelled_ordinal_fraction_or_decimal_is_still_not_read(sentence, pack):
    assert _says(sentence, pack) == ()


@pytest.mark.parametrize("hyphen", ["‐", "‑", "‒", "–", "—", "―"])
def test_a_unicode_hyphen_does_not_split_a_spelled_size(hyphen):
    found = _says(f"Cash fell by thirty{hyphen}five.", _cash_pack("-35", "875"))
    assert any("figure 35" in i for i in found), found


# --- the year problem, the counts and a spelled size across lines (owner, 2026-11-12: "fix 1 and
# 2"; controller rulings R1 to R3). Expectations hand-written from the rulings.


def _hold(text, pack=None, held=()):
    return cp8_issues(with_row(LEVERAGE_ROW, text + "\n\n"), pack or _ndpack(), held)


@pytest.mark.parametrize(
    "sentence",
    [
        "Cash fell by 2010 US$m.",
        "Cash fell by US$2010m.",
        "Cash fell by USD 2010.",
        "Cash fell by 2010m.",
        "Cash fell by 2010 million.",
        "Cash fell by 2010 USDm.",
    ],
)
def test_a_year_shaped_withheld_size_with_a_unit_is_refused(sentence):
    found = _hold(sentence, _cash_pack("-2010", "-1100"))
    assert any("figure 2010 is the difference" in i and "reword" in i for i in found), found


@pytest.mark.parametrize(
    ("sentence", "size"),
    [
        ("Cash fell by 2010 US$m.", "2010"),
        ("Cash fell by US$2010m.", "2010"),
        ("Cash was 2010.5 US$m.", "2010.5"),
        ("Cash was USD 1913.", "1913"),
        ("Cash was 1913 million.", "1913"),
    ],
)
def test_a_year_shaped_figure_with_a_unit_held_nowhere_is_refused(sentence, size):
    found = _hold(sentence)
    assert any(f"figure {size} is held in neither" in i for i in found), found


def test_a_year_shaped_figure_in_a_table_body_row_is_a_figure_and_in_a_header_row_is_not():
    table = "| Item | {} |\n| --- | --- |\n| Cash | {} |"
    body = table.format("Value", "2010 US$m")
    found = _hold(body, _cash_pack("-2010", "-1100"))
    assert any("figure 2010 is the difference" in i for i in found), found
    header = table.format("2024 / 2023 US$m", "not stated")
    assert _hold(header) == ()


@pytest.mark.parametrize(
    "sentence",
    [
        "The September 2024 US$4,216 million balance is a declared distribution.",
        "H1 2025 USD 30,199 thousand of dividends were paid.",
        "Debt due July 2025\u2013June 2026 USD 22,873 thousand is spread out.",
        "At 30 September 2024 US$m 437 was drawn.",
        "In 2024 cash was flat.",
        "FY2024 US$m is the unit.",
        "FY 2024 is the year.",
        "Fiscal 2024 was flat.",
        "Both 2023 and 2024 were flat.",
        "Q3 2024 US$m is the unit.",
    ],
)
def test_a_year_is_no_figure_with_a_marker_a_bare_or_a_currency_for_the_next_number(sentence):
    assert _hold(sentence, held=("4,216 30,199 22,873 437",)) == ()


def test_the_year_beside_a_figure_is_not_read_only_the_figure_is():
    found = _hold("Leverage was flat (2023: 6.57x).")
    assert any("figure 6.57 is held in neither" in i for i in found), found
    assert not any("2023" in i for i in found), found
    assert _hold("Leverage was flat (2023: 6.57x).", held=("6.57",)) == ()


@pytest.mark.parametrize(
    "sentence",
    [
        "All 30 modules ran in both runs.",
        "thirty sources were read.",
        "See page 30.",
        "Note 30 describes the facility.",
        "The loan matures in 30 months.",
        "The handoff states 30 limitations.",
        "Cash fell by 30 days.",
    ],
)
def test_a_count_beside_a_count_noun_or_a_reference_word_is_no_withheld_size(sentence):
    assert _hold(sentence) == ()


@pytest.mark.parametrize(
    "sentence",
    [
        "Cash fell by 30.",
        "Cash fell by thirty.",
        "A change of 30 in cash.",
        "30 new modules ran.",
        "Cash fell by 30 quarter-on-quarter.",
        "Cash fell by 30 US$m.",
        "Cash fell by 30 times.",
    ],
)
def test_a_bare_number_beside_no_count_noun_is_still_a_withheld_size(sentence):
    found = _hold(sentence)
    assert any("figure 30 is the difference" in i for i in found), found


@pytest.mark.parametrize(
    "sentence",
    [
        "Gross debt changed by one hundred\nand ten.",
        "Gross debt changed by one hundred and\nten.",
        "Gross debt changed by one\nhundred ten.",
    ],
)
def test_a_spelled_size_broken_across_lines_is_read_and_reported_once(sentence):
    found = [i for i in _hold(sentence) if "figure 110" in i]
    assert len(found) == 1, found


@pytest.mark.parametrize(
    "text",
    [
        "Debt is one hundred\n\nten.",
        "Debt is one hundred\n| Cash | ten |",
        "Debt is one hundred\n- ten",
        "Debt is one hundred\n### ten",
        "Debt is one hundred\nand then nothing.",
    ],
)
def test_a_spelled_number_is_not_joined_over_a_blank_line_row_heading_or_item(text):
    assert _hold(text) == ()


# --- fix round 1 of the counts branch: a year before a comma, ISO dates whole, two nouns dropped,
# a count noun on the next line, a table delimiter without outer pipes, a code after a year.
# Expectations hand-written from the controller's rulings.


@pytest.mark.parametrize(
    "sentence",
    [
        "In 2024, the issuer refinanced its notes.",
        "Revenue grew in 2023, 2024 and 2025.",
        "The notes due 2029, 2031 and 2032 were extended.",
        "By December 2025, Q3 2024, and 2026, cash held.",
    ],
)
def test_a_year_before_a_comma_is_a_year_and_no_figure(sentence):
    assert _hold(sentence) == ()


def test_a_year_before_a_comma_leaves_the_figure_after_it_read():
    found = _hold("In 2024, US$437m was drawn.")
    assert any("figure 437 is held in neither" in i for i in found), found
    assert not any("2024" in i for i in found), found
    assert _hold("In 2024, US$437m was drawn.", held=("437",)) == ()


def test_a_year_before_a_comma_in_a_table_row_and_a_header_row_is_a_year():
    table = "| Item | {} |\n| --- | --- |\n| Cash | {} |"
    assert _hold(table.format("2024, 2025 US$m", "not stated")) == ()
    found = _hold(table.format("Value", "In 2024, 2025 and 2026"))
    assert not any("held in neither" in i for i in found), found


def test_a_year_before_a_comma_in_held_evidence_holds_no_figure():
    held = ("On September 19, 2024, the Company completed the issuance of $3,000 million.",)
    found = _hold("Cash was US$2024m in both runs.", held=held)
    assert any("figure 2024 is held in neither" in i for i in found), found
    assert _hold("Cash was US$3,000m in both runs.", held=held) == ()


def test_a_comma_is_part_of_a_number_only_as_a_thousands_separator():
    held = ("The facility is 2,024 and 1,913 US$m.",)
    assert _hold("Cash was US$2,024m and US$1,913m.", held=held) == ()
    found = _hold("Cash was US$2,024m.", held=("In 2024, nothing.",))
    assert any("figure 2024 is held in neither" in i for i in found), found


@pytest.mark.parametrize(
    "sentence",
    [
        "The LTM 2023-10-01 through 2024-09-30 base.",
        "Cash was stated at Q3 2024-09-30 in both runs.",
        "As of September 2024-09-30 data.",
        "H1 2024-06 was flat.",
    ],
)
def test_an_iso_date_is_exempt_as_a_whole_after_a_period_marker_or_month(sentence):
    assert _hold(sentence) == ()


@pytest.mark.parametrize(
    "sentence",
    [
        "Cash shows a 30 difference between the runs.",
        "Cash shows a thirty difference.",
        "Cash records a 30 change.",
        "Cash records a thirty change.",
        "Cash shows 30 differences.",
    ],
)
def test_change_and_difference_are_not_count_nouns(sentence):
    found = _hold(sentence)
    assert any("figure 30 is the difference" in i for i in found), found


@pytest.mark.parametrize(
    "sentence", ["Both runs used thirty\nmodules.", "Both runs used 30\nmodules."]
)
def test_a_count_noun_on_the_next_line_of_the_paragraph_makes_a_count(sentence):
    assert _hold(sentence) == ()


@pytest.mark.parametrize(
    "text",
    [
        "Cash fell by 30\n\nmodules.",
        "Cash fell by 30\n- modules",
        "Cash fell by 30\n### modules",
        "Cash fell by thirty\n| modules |",
        "Cash fell by thirty\n\nmodules.",
    ],
)
def test_a_count_noun_over_a_blank_line_heading_row_or_item_makes_no_count(text):
    found = _hold(text)
    assert any("figure 30 is the difference" in i for i in found), found


def test_a_table_delimiter_without_outer_pipes_still_marks_the_header():
    assert _hold("| Item | 2024 US$m |\n--- | ---\n| Cash | 5 |") == ()


def test_a_code_after_a_year_with_no_scale_or_number_is_no_unit():
    assert _hold("In 2024 USD strengthened against the euro.") == ()
    for sentence in ("Cash was 2010 USDm.", "Cash was 2010 US$m.", "Cash was 2010 USD million."):
        found = _hold(sentence)
        assert any("figure 2010 is held in neither" in i for i in found), (sentence, found)
    found = _hold("Cash was 2010 USD 31.")
    assert any("figure 31 is held in neither" in i for i in found), found
    assert not any("2010" in i for i in found), found


@pytest.mark.parametrize(
    "text",
    [
        "2010 USD millions",
        "2010 USD mn",
        "2010 EUR billions",
        "2010 USD thousands",
        "2010 US$ million",
        "2010 US$ millions",
        "2010 US$m",
        "2010 USDm",
        "2010 USD m",
        "2010USD Millions",
    ],
)
def test_a_year_shaped_number_with_a_plural_or_mn_scale_is_a_figure(text):
    from deploy_workflow.changes_check import _figures

    assert [str(f.size) for f in _figures(text)] == ["2010"], text


@pytest.mark.parametrize("text", ["In 2024 USD strengthened", "2024 US$4,216 million"])
def test_a_year_before_a_currency_of_the_next_number_stays_a_year(text):
    from deploy_workflow.changes_check import _figures

    assert "2024" not in [str(f.size) for f in _figures(text)], text


def test_a_hyphenated_number_after_a_month_year_is_not_cut_mid_number():
    from deploy_workflow.changes_check import _figures

    assert [str(f.size) for f in _figures("September 2024-437")] == ["437"]
    assert _figures("FY 2024-25") == []


@pytest.mark.parametrize("row", ["| - | -", "| - | - |", "| -- | --- |"])
def test_a_row_of_short_dash_cells_is_no_table_separator(row):
    text = f"| Item | Cash 2010 US$m |\n{row}\n| a | b |"
    found = _hold(text, _cash_pack("-2010", "-1100"))
    assert any("figure 2010 is the difference" in i for i in found), (row, found)


def test_a_range_of_two_years_reads_no_figure_and_k10_accepts_it():
    from deploy_workflow.changes_check import _figures

    text = "Finance lease obligations, 2025-2045 maturities"
    assert _figures(text) == []
    assert _hold(text) == ()


_YEARISH = re.compile(r"(?<![\d,.])(?:19|20)\d{2}(?:\.\d+)?(?![\d,])")


@pytest.mark.parametrize(
    "text",
    [
        "2010 US$m",
        "2010m",
        "2010 million",
        "2010 USDm",
        "1913 million",
        "2010.5 US$m",
        "US$2010m",
        "USD 2010",
        "USD 1913",
        "2010 USD millions",
        "2010 USD mn",
        "2010 EUR billions",
        "2010 USD thousands",
        "2010 US$ million",
        "2010 US$ millions",
        "2010 USD m",
        "2010USD Millions",
        "2010bn",
        "2010x",
        "2010%",
        "2024 bn",
        "2024 mn",
        "2024 EUR m.",
        "2024 thousand employees",
        "2010 m",
        "2024 x",
        "2024 %",
        "2024 percent",
        "2024 bps",
        "2010m-2011m",
        "In 2024 k.",
        "In 2024 $ millions were raised",
        "In 2024 £ billions",
        "2024 £bn",
        "2010 US$M",
        "2010 $MM",
        "2010 €M",
        "2010 US$BN",
        "2010 $K",
        "2010 USD M",
        "2010 USDM",
        "In 2024 USD mm",
        "cash of US$1913 million and liquidity",
        "FY2024 USD 2045 million; FY2023",
        "CP-1's US$2038 million total",
    ],
)
def test_a_19xx_20xx_number_with_a_unit_ending_its_word_is_a_figure(text):
    from deploy_workflow.changes_check import _figures

    sizes = [str(f.size) for f in _figures(text)]
    assert any(t in sizes for t in _YEARISH.findall(text)), (text, sizes)


@pytest.mark.parametrize(
    "text",
    [
        "In 2024 m&a activity rose.",
        "The 2024 k-shaped recovery helped.",
        "In 2024 millions of customers switched.",
        "In 2024 USD millionaires bought bonds.",
        "In 2024 € m-commerce grew.",
        "In 2024 millions switched.",
        "In 2024 thousands left.",
        "In 2024 millions, not thousands, switched.",
        "2010 millions",
        "Cash was 2010 millions.",
        "In 2024 million-dollar deals rose.",
        "In 2024 m/m growth slowed.",
        "In 2024 bn-dollar deals.",
        "In 2024 x-ray use rose.",
        "In 2024 percentages rose.",
        "In 2024 USD billionaires",
        "In 2024 $US rose",
        "In 2024 €m-commerce grew.",
        "In 2024 ABCm rose",
        "In 2024 bps-style",
        "In 2024 thousandths",
        "2010 USD m&a",
        "In 2024 USD M&A deals",
        "In 2024 kWh fell",
        "2024 US$ 5m",
        "In 2024 USD strengthened against the euro.",
        "2024 US$4,216 million",
        "Cash was 2010 USD 31.",
        "H1 2025 USD 30,199 thousand",
        "In 2024, the issuer refinanced.",
        "2024 M&A",
        "2024 Mn",
        "2024 management",
        "2024 markets",
        "FY2024 m",
        "2024 USD mid-market",
        "2025 OEM build rates",
        "2024 AND 2023",
        "2024 M",
        "2024 K",
    ],
)
def test_a_19xx_20xx_number_before_a_word_that_only_starts_like_a_unit_is_a_year(text):
    from deploy_workflow.changes_check import _figures

    sizes = [str(f.size) for f in _figures(text)]
    assert not [t for t in _YEARISH.findall(text) if t in sizes], (text, sizes)


def test_a_percent_hyphen_word_after_a_small_number_is_still_a_unit():
    from deploy_workflow.changes_check import _figures

    assert [str(f.size) for f in _figures("30 percent-owned", counts=False)] == ["30"]


def test_no_module_level_name_in_the_checker_is_assigned_twice():
    # A second `_UNITS = ...` once silently replaced a regex with a dict; the quality gate
    # checks changed lines only and did not see it.
    from deploy_workflow import changes_check

    source = Path(changes_check.__file__).read_text(encoding="utf-8")
    names = [
        target.id
        for node in ast.parse(source).body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(target, ast.Name)
    ]
    assert sorted({name for name in names if names.count(name) > 1}) == []


@pytest.mark.parametrize(
    ("text", "counts", "expected"),
    [
        ("Drawn EUR437m.", True, ["437"]),
        ("Cash fell by USD2010m.", True, ["2010"]),
        ("Cash was USD2010.", True, ["2010"]),
        ("Drawn USD437.", True, ["437"]),
        ("Drawn USD5.", False, ["5"]),
        ("Drawn (EUR437m) and GBP12m.", True, ["437", "12"]),
        ("Drawn XEUR437.", True, []),
        ("Ref ABC123 only.", True, []),
        ("Ref foo.USD437 only.", True, []),
        ("See Q3 and H1 and FY2024 and CP-2 results.", False, []),
        ("A USD-denominated bond.", True, []),
        ("A EUR-denominated bond of EUR437m.", True, ["437"]),
    ],
)
def test_digits_glued_to_a_currency_code_are_a_figure(text, counts, expected):
    from deploy_workflow.changes_check import _figures

    assert [str(f.size) for f in _figures(text, counts=counts)] == expected


@pytest.mark.parametrize(
    "text",
    [
        "2010 C$m",
        "C$2010m",
        "2010 A$m",
        "2010 R$m",
        "2010 S$m",
        "2010 HK$ million",
        "2010 NZ$m",
        "2010 SAR m",
        "SAR 2010",
        "2010 USD mln",
        "2010 USD bln",
        "2010 USD '000",
        "2010 USD ’000",
        "2010 mln",
        "2010 bln",
        "HK$1913 million",
        "In 2024 SAR 2010 total",
        "2010 PHP m",
        "2010 AED m",
    ],
)
def test_more_currency_and_scale_forms_make_a_year_shaped_number_a_figure(text):
    from deploy_workflow.changes_check import _figures

    sizes = [str(f.size) for f in _figures(text)]
    assert any(t in sizes for t in _YEARISH.findall(text)), (text, sizes)


@pytest.mark.parametrize(
    "text",
    [
        "In 2024 C$ strengthened",
        "In 2024 mln-dollar deals",
        "In 2024 bln-dollar deals",
        "2024 AND 2023",
        "In 2024 SAR strengthened",
        "In 2024 mlnx rose",
        "In 2024 USD '000s of customers",
        "In 2024 HK$ fell",
    ],
)
def test_a_year_beside_a_currency_or_scale_lookalike_stays_a_year(text):
    from deploy_workflow.changes_check import _figures

    sizes = [str(f.size) for f in _figures(text)]
    assert not [t for t in _YEARISH.findall(text) if t in sizes], (text, sizes)


def test_a_currency_after_a_year_belongs_to_the_next_number():
    from deploy_workflow.changes_check import _figures

    assert [str(f.size) for f in _figures("2024 SAR 5,000")] == ["5000"]


def test_a_small_number_with_mln_or_bln_is_a_figure_not_a_count():
    from deploy_workflow.changes_check import _figures

    assert [str(f.size) for f in _figures("up 30 mln and 7 bln", counts=False)] == ["30", "7"]
    assert _figures("30 mlnx", counts=False) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("EUR 2029s, 480bp", ["480"]),
        ("USD2029s and 7%", ["7"]),
        ("the 2031s fell 5%", ["5"]),
        ("the EUR 2031s", []),
        ("EUR 2029s", []),
        ("$2029s, 100bp", ["100"]),
        ("EUR 2029 s", ["2029"]),
        ("EUR 2029secured", ["2029"]),
        ("EUR 2029", ["2029"]),
        ("EUR 2029sx", ["2029"]),
    ],
)
def test_a_year_number_followed_by_s_is_a_bond_name_also_after_a_currency(text, expected):
    from deploy_workflow.changes_check import _figures

    assert [str(f.size) for f in _figures(text)] == expected


def test_a_bond_name_is_not_held_evidence():
    from deploy_workflow.changes_check import _held_sizes

    assert _held_sizes(["Notes: EUR 2029s, 480bp."]) == frozenset({Decimal(480)})


def test_the_currency_code_list_holds_the_fixed_set():
    from deploy_workflow.changes_check import _CODES

    wanted = [
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "SEK", "NOK",
        "DKK", "PLN", "CZK", "HUF", "TRY", "ZAR", "BRL", "MXN", "CNY", "CNH",
        "HKD", "SGD", "INR", "KRW", "TWD", "THB", "IDR", "MYR", "PHP", "SAR",
        "AED", "QAR", "KWD", "ILS", "EGP", "NGN", "CLP", "COP", "PEN", "ARS",
    ]  # fmt: skip
    assert sorted(_CODES.split("|")) == sorted(wanted)
