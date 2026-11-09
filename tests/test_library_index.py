"""Which runs the Issuer Library lists. Synthetic run folders (tests/library_fixtures.py) prove the
admission rules; one CP-OS run with a fake provider proves the rules accept what CP-OS writes; one
copy of a retained live run proves the hash chain on real CP-OS output."""

import json
import os
import shutil
from pathlib import Path

import pytest
from library_fixtures import (
    make_run,
    method,
    method_block,
    put,
    rewrite_completion,
    rewrite_manifest,
    sha,
)

from deploy_workflow import library_index
from deploy_workflow.library_index import build_library, current_method

ROOT = Path(__file__).resolve().parents[1]


def listed(workspace: Path, version: str = "") -> library_index.Library:
    return build_library(workspace, workspace / "library", method(version))


def reasons(library: library_index.Library) -> dict[str, str]:
    return dict(library.excluded)


def test_completed_run_on_the_current_method_is_listed_with_its_recorded_values(tmp_path):
    make_run(tmp_path, "run-a")
    library = listed(tmp_path)
    assert library.excluded == []
    (run,) = library.runs
    assert (run["id"], run["issuer_id"], run["as_of"], run["pathway"]) == (
        "run-a",
        "nbg",
        "2025-03-31",
        "credit_snapshot",
    )
    assert [m["id"] for m in run["modules"]] == ["CP-0", "CP-1"]
    assert run["modules"][0]["execution"] == "Model provider"
    assert run["modules"][0]["summary"] == {
        "bottom_line": "CP-0 bottom line.",
        "confidence": "Medium",
        "limitation": "Synthetic fixture only.",
        "findings": [
            {"finding": "One observed item.", "impact": "None assessed.", "confidence": "Low"}
        ],
    }
    # 0.10 + 0.20 recorded, kept as an exact decimal; links are relative to library/.
    assert run["execution"]["spend_usd"] == "0.30"
    assert run["execution"]["unknown_charges"] == 0
    assert run["execution"]["started_at"] == "2026-11-01T10:00:00Z"
    assert run["execution"]["models"] == ["gpt-6.1-sol · medium"]
    assert run["report"]["href"].startswith("../runs/run-a/deliveries/")
    assert run["modules"][1]["href"].startswith("../runs/run-a/requests/CP-1/")
    assert (tmp_path / "library" / run["report"]["href"]).resolve().is_file()
    assert run["latest"] is True and run["latest_shared_with"] == 0


def test_a_changed_method_section_leaves_the_run_out_and_names_it(tmp_path):
    make_run(tmp_path, "run-a", version="")
    library = listed(tmp_path, version=" Amended.")
    assert library.runs == []
    assert reasons(library) == {
        "run-a": "CP-0: not on the current methodology (methods/cp0.md changed)"
    }


def test_a_module_with_no_current_method_is_not_assumed_current(tmp_path):
    run = make_run(tmp_path, "run-a")
    shutil.copytree(run / "requests/CP-1", run / "requests/CP-9")  # unused; CP-9 is not recorded
    library = build_library(tmp_path, tmp_path / "library", (lambda m: None, lambda m: []))
    assert reasons(library) == {"run-a": "CP-0: no current method is selected for this module"}


@pytest.mark.parametrize(
    ("execution", "reason"),
    [
        ("retained-response-replay", "reused from an earlier run"),
        ("synthetic", "synthetic"),
        ("unknown", "recorded as 'unknown'"),
    ],
)
def test_a_module_not_answered_in_this_run_leaves_it_out(tmp_path, execution, reason):
    make_run(tmp_path, "run-a", execution=execution)
    assert reasons(listed(tmp_path)) == {
        "run-a": f"CP-0: {reason}; its methodology is not this run's"
    }


def test_runs_without_a_launcher_record_or_completion_are_left_out(tmp_path):
    (tmp_path / "runs/legacy").mkdir(parents=True)
    (tmp_path / "runs/legacy/CP-1.md").write_text("old handoff")
    run = make_run(tmp_path, "unfinished")
    next(run.glob("completed-*.json")).unlink()
    assert reasons(listed(tmp_path)) == {
        "legacy": "not a CP-OS launcher run (no workflow.json)",
        "unfinished": "not completed: no completion record",
    }


def test_a_completion_record_that_does_not_match_its_name_is_refused(tmp_path):
    run = make_run(tmp_path, "run-a")
    record = next(run.glob("completed-*.json"))
    record.write_text(record.read_text().replace("12", "13"))
    assert reasons(listed(tmp_path)) == {
        "run-a": f"{record.name} does not have the sha256 its name states"
    }


def test_other_completion_kinds_are_not_report_runs(tmp_path):
    run = make_run(tmp_path, "run-a")
    rewrite_completion(run, lambda r: r.update(kind="cpos-handoff-snapshot/1"))
    assert reasons(listed(tmp_path)) == {
        "run-a": "not a report run of the current launcher "
        "(completion kind ['cpos-handoff-snapshot/1'])"
    }


def test_a_changed_report_is_not_listed(tmp_path):
    run = make_run(tmp_path, "run-a")
    (report,) = run.glob("deliveries/*/report.html")
    report.write_text("<p>edited</p>")
    path = report.relative_to(run).as_posix()
    assert reasons(listed(tmp_path)) == {"run-a": f"{path} no longer has its recorded sha256"}


def test_a_delivery_of_another_report_is_not_the_completed_one(tmp_path):
    run = make_run(tmp_path, "run-a")
    rewrite_completion(run, lambda r: r.update(report_sha256="0" * 64))
    assert reasons(listed(tmp_path)) == {
        "run-a": "no delivery folder holds the report the completion record names"
    }


def test_a_changed_delivered_file_is_not_listed(tmp_path):
    run = make_run(tmp_path, "run-a")
    (copy,) = run.glob("deliveries/*/CP-1.md")
    copy.write_text("edited")
    folder = copy.parent.relative_to(run).as_posix()
    assert reasons(listed(tmp_path)) == {
        "run-a": f"{folder}/CP-1.md no longer has its recorded sha256"
    }


def test_an_extra_file_in_the_delivery_is_not_listed(tmp_path):
    run = make_run(tmp_path, "run-a")
    (receipt,) = run.glob("deliveries/*/delivery.json")
    (receipt.parent / "extra.html").write_text("added")
    folder = receipt.parent.relative_to(run).as_posix()
    assert reasons(listed(tmp_path)) == {
        "run-a": f"{folder} does not hold exactly the files its delivery.json lists"
    }


def test_a_handoff_changed_after_delivery_is_not_listed(tmp_path):
    run = make_run(tmp_path, "run-a")
    (handoff,) = run.glob("requests/CP-1/*/1.response.md")
    handoff.write_text("edited")
    path = handoff.relative_to(run).as_posix()
    assert reasons(listed(tmp_path)) == {"run-a": f"{path} no longer has its recorded sha256"}


def test_a_changed_request_record_is_not_the_request_sent(tmp_path):
    run = make_run(tmp_path, "run-a")
    (record,) = run.glob("requests/CP-0/*/1.request.json")
    request = json.loads(record.read_text())
    request["instructions"] = request["instructions"].replace("# CP-0 method", "# CP-0 amended")
    record.write_text(json.dumps(request, sort_keys=True, indent=2))
    path = record.relative_to(run).as_posix()
    assert reasons(listed(tmp_path)) == {
        "run-a": f"{path} is not the request its folder was named for"
    }


def test_edited_instruction_pins_cannot_stand_in_for_the_request_sent(tmp_path):
    """workflow.json is not in the hash chain, so its pins are not what is checked."""
    run = make_run(tmp_path, "run-a", version=" Old.")
    current = "Selected method, verbatim:\n\n" + method_block("CP-0") + "\n"
    put(run / "instructions/CP-0.md", current.encode())
    workflow = json.loads((run / "workflow.json").read_text())
    workflow["instructions"]["CP-0"]["sha256"] = sha(current.encode())
    (run / "workflow.json").write_text(json.dumps(workflow))
    assert reasons(listed(tmp_path)) == {
        "run-a": "CP-0: not on the current methodology (methods/cp0.md changed)"
    }


def test_a_method_section_sent_then_dropped_from_the_method_is_not_current(tmp_path):
    extra = "\n\n=== methods/cp0-old-step.md sha256 " + "1" * 64 + " ===\nAn old step."
    make_run(tmp_path, "run-a", sent_extra=extra)
    assert reasons(listed(tmp_path)) == {
        "run-a": "CP-0: not on the current methodology (methods/cp0-old-step.md no longer selected)"
    }


def test_a_module_only_the_manifest_names_is_not_left_unchecked(tmp_path):
    run = make_run(tmp_path, "run-a")
    rewrite_manifest(
        run,
        lambda m: m["handoffs"].update(
            {"CP-2": {"path": "requests/CP-2/missing/1.response.md", "sha256": "0" * 64}}
        ),
    )
    assert reasons(listed(tmp_path)) == {
        "run-a": "the completion record and the delivery manifest name different modules"
    }


def test_a_delivered_copy_that_differs_from_the_handoff_is_refused(tmp_path):
    run = make_run(tmp_path, "run-a")
    (receipt,) = run.glob("deliveries/*/delivery.json")
    (receipt.parent / "CP-1.md").write_text("another handoff")
    files = json.loads(receipt.read_text())
    files["files"]["CP-1.md"] = sha(b"another handoff")
    receipt.write_text(json.dumps(files))
    assert reasons(listed(tmp_path)) == {
        "run-a": "the delivery's copy of CP-1's handoff is not the one it names"
    }


def test_a_hidden_file_in_the_delivery_counts_as_an_extra_file(tmp_path):
    run = make_run(tmp_path, "run-a")
    (receipt,) = run.glob("deliveries/*/delivery.json")
    (receipt.parent / ".DS_Store").write_bytes(b"\0")
    folder = receipt.parent.relative_to(run).as_posix()
    assert reasons(listed(tmp_path)) == {
        "run-a": f"{folder} does not hold exactly the files its delivery.json lists"
    }


def test_a_folder_without_a_receipt_is_not_taken_for_the_delivery(tmp_path):
    run = make_run(tmp_path, "run-a")
    (run / "deliveries/0-unfinished").mkdir()
    assert [r["id"] for r in listed(tmp_path).runs] == ["run-a"]


def test_a_run_whose_identity_is_not_stated_is_not_listed(tmp_path):
    run = make_run(tmp_path, "run-a")
    workflow = json.loads((run / "workflow.json").read_text())
    del workflow["run"]["issuer_id"]
    (run / "workflow.json").write_text(json.dumps(workflow))
    assert reasons(listed(tmp_path)) == {
        "run-a": "workflow.json does not state the run's issuer_id"
    }


def test_malformed_records_leave_one_run_out_and_the_rest_listed(tmp_path):
    odd = make_run(tmp_path, "odd-fields")
    workflow = json.loads((odd / "workflow.json").read_text())
    workflow["run"]["requested_modules"] = 5
    (odd / "workflow.json").write_text(json.dumps(workflow))
    rewrite_completion(odd, lambda r: r.update(provider_cap_usd="NaN"))
    deep = make_run(tmp_path, "deep-json")
    (deep / "workflow.json").write_text("[" * 100_000 + "]" * 100_000)
    make_run(tmp_path, "good")
    library = listed(tmp_path)
    runs = {r["id"]: r for r in library.runs}
    assert sorted(runs) == ["good", "odd-fields"]
    assert (runs["odd-fields"]["requested_modules"], runs["odd-fields"]["cap_usd"]) == ([], None)
    assert reasons(library) == {"deep-json": "unreadable run record (RecursionError)"}


def test_a_request_record_marked_as_reused_is_not_this_runs_answer(tmp_path):
    run = make_run(tmp_path, "run-a")
    (record,) = run.glob("requests/CP-0/*/1.request.json")
    request = json.loads(record.read_text())
    request["retained_response_sha256"] = "0" * 64
    inputs = {k: v for k, v in request.items() if k not in {"attempt", "feedback"}}
    folder = record.parent.with_name(sha(json.dumps(inputs, sort_keys=True).encode()))
    record.parent.rename(folder)
    (folder / "1.request.json").write_text(json.dumps(request, sort_keys=True, indent=2))
    old = record.parent.name
    rewrite_manifest(
        run,
        lambda m: m["handoffs"]["CP-0"].update(
            path=m["handoffs"]["CP-0"]["path"].replace(old, folder.name)
        ),
    )
    rewrite_completion(
        run, lambda r: r["modules"].update({"CP-0": r["modules"]["CP-0"].replace(old, folder.name)})
    )
    path = (folder / "1.request.json").relative_to(run).as_posix()
    assert reasons(listed(tmp_path)) == {"run-a": f"{path} is not a request answered in this run"}


def test_a_delivery_for_another_issuer_is_not_listed(tmp_path):
    make_run(tmp_path, "run-a", view_issuer="other")
    assert reasons(listed(tmp_path)) == {
        "run-a": "the delivered report names a different run (issuer_id)"
    }


@pytest.mark.parametrize(
    "path", ["../outside.md", "/etc/passwd", "requests/./x.md", ".hidden/x", "a//b.md", "a\\b.md"]
)
def test_handoff_paths_must_stay_inside_the_run(tmp_path, path):
    run = make_run(tmp_path, "run-a")
    manifest_file = next(run.glob("delivery-*.json"))
    manifest = json.loads(manifest_file.read_text())
    manifest["handoffs"]["CP-0"]["path"] = path
    manifest_file.unlink()
    raw = json.dumps(manifest, indent=2).encode()
    new_sha = put(run / f"delivery-{sha(raw)}.json", raw)

    def change(record):
        record["delivery_manifest_sha256"] = new_sha
        record["modules"]["CP-0"] = path

    rewrite_completion(run, change)
    assert reasons(listed(tmp_path)) == {"run-a": f"{path!r} is not a path inside the run"}


def test_a_linked_handoff_is_not_followed(tmp_path):
    run = make_run(tmp_path, "run-a")
    (handoff,) = run.glob("requests/CP-0/*/1.response.md")
    outside = tmp_path / "outside.md"
    outside.write_bytes(handoff.read_bytes())
    handoff.unlink()
    os.symlink(outside, handoff)
    path = handoff.relative_to(run).as_posix()
    assert reasons(listed(tmp_path)) == {"run-a": f"{path} is a link"}


def test_a_linked_run_folder_is_reported_and_not_followed(tmp_path):
    run = make_run(tmp_path, "run-a")
    os.symlink(run, tmp_path / "runs/run-b")
    (tmp_path / "runs/notes.txt").write_text("not a run")
    library = listed(tmp_path)
    assert [r["id"] for r in library.runs] == ["run-a"]
    assert reasons(library) == {"run-b": "a link to another folder; not followed"}


def test_spend_keeps_zero_missing_and_unknown_apart(tmp_path):
    make_run(tmp_path, "tiny", settled=("0.00000050",))
    make_run(tmp_path, "zero-places", settled=("0.00000000",))
    make_run(tmp_path, "zero", settled=("0",))
    make_run(tmp_path, "unknown", settled=("0.25", None))
    run = make_run(tmp_path, "none", settled=())
    (run / "live/calls.jsonl").unlink()
    spend = {r["id"]: r["execution"] for r in listed(tmp_path).runs}
    assert (spend["zero"]["spend_usd"], spend["zero"]["unknown_charges"]) == ("0", 0)
    assert spend["tiny"]["spend_usd"] == "0.00000050"  # Never 5.0E-7.
    assert spend["zero-places"]["spend_usd"] == "0.00000000"
    assert (spend["unknown"]["spend_usd"], spend["unknown"]["unknown_charges"]) == ("0.25", 1)
    assert (spend["none"]["spend_usd"], spend["none"]["calls"]) == (None, 0)


def test_latest_is_per_issuer_by_evidence_date_and_ties_are_shown(tmp_path):
    make_run(tmp_path, "a-old", as_of="2024-12-31")
    make_run(tmp_path, "a-new-1", as_of="2025-03-31")
    make_run(tmp_path, "a-new-2", as_of="2025-03-31")
    make_run(tmp_path, "b-only", issuer_id="zzz", issuer_name="Zeta Synthetic", as_of="2020-06-30")
    runs = {r["id"]: r for r in listed(tmp_path).runs}
    assert {k: (r["latest"], r["latest_shared_with"]) for k, r in runs.items()} == {
        "a-old": (False, 0),
        "a-new-1": (True, 1),
        "a-new-2": (True, 1),
        "b-only": (True, 0),
    }
    order = [r["id"] for r in listed(tmp_path).runs]
    assert order == ["a-new-1", "a-new-2", "a-old", "b-only"]


def test_a_run_cpos_completed_with_a_fake_provider_is_listed(tmp_path, monkeypatch):
    """CP-OS really prepares, runs (fake provider) and delivers; the library must accept its
    files. Synthetic answers: this proves the file contract, not any analysis."""
    import test_cpos_launch as launch_tests

    from deploy_workflow.owners import cpos_launch

    provider = launch_tests.provider.__wrapped__(monkeypatch)
    out = tmp_path / "ws/runs/fake-run"
    argv = launch_tests.launch(tmp_path, "--live", "--ruling", str(launch_tests.RULING))
    argv[argv.index("--out") + 1] = str(out)
    argv += ["--modules", "CP-1"]
    routes = list(
        cpos_launch.prepare(
            tmp_path / "context.json",
            tmp_path / "issuer",
            tmp_path / "preview",
            config="sol-medium",
            cap="50",
            modules=("CP-1",),
        ).plan.layout.routes
    )
    provider.answer = lambda context: launch_tests.answer(context, routes)
    assert cpos_launch.main(argv) == 0
    library = build_library(tmp_path / "ws", tmp_path / "ws/library", current_method())
    assert library.excluded == []
    (run,) = library.runs
    assert [m["id"] for m in run["modules"]] == ["CP-0", "CP-1"]
    assert run["modules"][0]["summary"]["bottom_line"] == launch_tests.READER_BOTTOM_LINE

    # The same run is left out once a method it ran on changes.
    sections = cpos_launch.method_sections

    def amended(module):
        return (
            [(n, t + "\nAmended.") for n, t in sections(module)]
            if module == "CP-1"
            else (sections(module))
        )

    monkeypatch.setattr(cpos_launch, "method_sections", amended)
    library = build_library(tmp_path / "ws", tmp_path / "ws/library", current_method())
    assert dict(library.excluded) == {
        "fake-run": "CP-1: not on the current methodology (prompts/CP-1.md, "
        + ", ".join(f"STEP_CONTRACTS[{s}]" for s in cpos_launch.CP1_STEPS)
        + " changed)"
    }

    # And once a step it was sent is dropped from the method (a scope reduction).
    monkeypatch.setattr(cpos_launch, "method_sections", sections)
    monkeypatch.setattr(cpos_launch, "CP1_STEPS", cpos_launch.CP1_STEPS[:-1])
    library = build_library(tmp_path / "ws", tmp_path / "ws/library", current_method())
    assert dict(library.excluded) == {
        "fake-run": "CP-1: not on the current methodology (STEP_CONTRACTS[quality] no longer "
        "selected)"
    }


def test_the_hash_chain_holds_on_a_retained_live_run(tmp_path):
    """Retained data: a copy of a live gpt-6.1-sol run (2026-11-06). Its own recorded method text
    stands in for the current one, so this proves the completion and delivery checks on real CP-OS
    output; it says nothing about which methodology is current today."""
    name = "web-04cd5a5d02ea7d1dea714a8a6632cd21"
    shutil.copytree(ROOT / "runs" / name, tmp_path / "runs" / name)
    run_dir = tmp_path / "runs" / name

    def recorded(module):
        path = run_dir / "instructions" / f"{module}.md"
        text = path.read_text(encoding="utf-8")
        return text.split("Selected method, verbatim:\n\n", 1)[1][:-1]

    library = build_library(tmp_path, tmp_path / "library", (recorded, lambda m: []))
    (run,) = library.runs
    assert (run["issuer_id"], run["as_of"], run["execution"]["config"]) == (
        "tdg",
        "2024-09-30",
        "sol-medium",
    )
    assert run["report"]["sha256"] == (
        "7bf8a4821cec15071c9ecd72e2191bfdfca28b060d1747b1b4ac004d53bd3c54"
    )
    assert [m["summary"] is not None for m in run["modules"]] == [True, True, True]
