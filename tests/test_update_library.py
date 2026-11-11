"""The update script: the static Credit OS library, written only to library/, from fixtures."""

import json
import re
import sys
from pathlib import Path

import pytest
from library_fixtures import make_run, method

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library

from deploy_workflow.library_index import Refused

PREFIX = "window.CREDIT_OS_DATA="
HOSTILE = '</script><script>alert(1)</script><!-- & "quoted"  '


@pytest.fixture(autouse=True)
def stand_in_method(monkeypatch):
    """The synthetic runs' method stands in for the launcher's current one."""
    monkeypatch.setattr("deploy_workflow.library_index.current_method", lambda: method())


def tree(folder: Path) -> dict[str, bytes]:
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def data_of(workspace: Path) -> dict:
    text = (workspace / "library/data.js").read_text(encoding="utf-8")
    assert text.startswith(PREFIX) and text.rstrip().endswith(";")
    return json.loads(text.removeprefix(PREFIX).rstrip().removesuffix(";"))


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def test_writes_static_library(tmp_path):
    make_run(tmp_path, "run-a")
    before = tree(tmp_path)
    library = update_library.update_library(tmp_path)
    after = tree(tmp_path)
    assert [r["id"] for r in library.runs] == ["run-a"]
    # Only library/ is written; nothing else in the workspace changes, no temporary folder is left.
    assert {k: v for k, v in after.items() if not k.startswith("library/")} == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["library", "runs"]
    for name in ("index.html", "data.js", "static-boot.js", "screen.css", "fonts/OFL.txt"):
        assert (tmp_path / "library" / name).is_file()
    assert not [k for k in after if k.endswith(".test.cjs")]
    # The delivered report is retired (decision 1): no copy of it, no adapter, no reports list.
    assert not [k for k in after if k.startswith("library/reports/") or "report-adapter" in k]
    data = data_of(tmp_path)
    assert data["catalogue"]["real"][0]["id"] == "run-a"
    assert "reports" not in data["workspace"]
    assert not [s for s in strings(data) if s.startswith("/files/")]
    assert "../runs/run-a/" in "\n".join(strings(data))
    assert not [s for s in strings(data) if "sha256=" in s and s.startswith("../")]
    page = (tmp_path / "library/index.html").read_text(encoding="utf-8")
    assert "default-src 'none'" in page and "connect-src 'none'" in page
    assert re.findall(r'\b(?:src|href)="(?:https?:)?//', page) == []


def test_the_runs_own_files_are_not_changed_or_copied(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    before = tree(tmp_path)
    update_library.update_library(tmp_path)
    after = tree(tmp_path)
    assert {k: v for k, v in after.items() if not k.startswith("library/")} == before
    assert (run_dir / "deliveries").is_dir()
    assert not any(p.name == "report.html" for p in (tmp_path / "library").rglob("*"))


def test_refuses_library_symlink(tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    workspace = tmp_path / "workspace"
    (workspace / "runs").mkdir(parents=True)
    (workspace / "library").symlink_to(elsewhere)
    with pytest.raises(Refused, match="is a link or a file"):
        update_library.update_library(workspace)
    assert list(elsewhere.iterdir()) == []


def test_empty_workspace(tmp_path):
    library = update_library.update_library(tmp_path)
    assert library.runs == [] and library.excluded == []
    assert data_of(tmp_path)["catalogue"]["real"] == []
    assert (tmp_path / "library/index.html").is_file()


def test_unlisted_run_contributes_nothing(tmp_path):
    make_run(tmp_path, "run-a")
    half = make_run(tmp_path, "run-half", issuer_id="zzz", issuer_name="Zeta Synthetic")
    next(half.glob("completed-*.json")).unlink()  # Not complete, so library_index does not list it.
    (tmp_path / "runs/legacy").mkdir()
    library = update_library.update_library(tmp_path)
    assert [r["id"] for r in library.runs] == ["run-a"]
    assert {name for name, _ in library.excluded} == {"run-half", "legacy"}
    data = data_of(tmp_path)
    # Run activity names the excluded folder and its reason; nothing else carries it.
    assert [name for name, _ in data["activity"]["excluded"]] == ["legacy", "run-half"]
    listed = json.dumps({k: v for k, v in data.items() if k != "activity"})
    assert "run-half" not in listed and "Zeta Synthetic" not in json.dumps(data)
    assert not (tmp_path / "library/reports").exists()


def test_hostile_run_text_cannot_leave_the_data_file(tmp_path):
    make_run(tmp_path, "run-a", issuer_name=HOSTILE)
    update_library.update_library(tmp_path)
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    assert "</script" not in text and "<!--" not in text
    assert data_of(tmp_path)["catalogue"]["real"][0]["name"] == HOSTILE


def test_a_rebuild_replaces_the_library_whole(tmp_path):
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    (tmp_path / "library/stale.txt").write_text("old")
    update_library.update_library(tmp_path)
    assert not (tmp_path / "library/stale.txt").exists()
    assert (tmp_path / "library/index.html").is_file()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["library", "runs"]


def test_a_failed_build_keeps_the_previous_library(tmp_path, monkeypatch):
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    before = tree(tmp_path / "library")

    def broken(*args):
        raise RuntimeError("cannot build")

    monkeypatch.setattr(update_library, "workspace_store", broken)
    with pytest.raises(RuntimeError, match="cannot build"):
        update_library.update_library(tmp_path)
    assert tree(tmp_path / "library") == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["library", "runs"]


def test_the_command_reports_what_it_listed_and_why_others_are_not_shown(tmp_path, capsys):
    make_run(tmp_path, "run-a")
    (tmp_path / "runs/legacy").mkdir()
    assert update_library.main(["--workspace", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Listed 1 run(s) on the current methodology." in out
    assert "  legacy: not a CP-OS launcher run (no workflow.json)" in out
    assert str(tmp_path.resolve() / "library/index.html") in out


def test_a_missing_workspace_is_refused(tmp_path):
    with pytest.raises(Refused, match="Workspace not found"):
        update_library.update_library(tmp_path / "absent")


def test_the_command_turns_a_refusal_into_an_exit(tmp_path):
    with pytest.raises(SystemExit, match="Workspace not found"):
        update_library.main(["--workspace", str(tmp_path / "absent")])


def test_data_js_carries_excluded_runs(tmp_path):
    make_run(tmp_path, "run-a")
    half = make_run(tmp_path, "run-half", issuer_id="zzz", issuer_name="Zeta Synthetic")
    next(half.glob("completed-*.json")).unlink()
    library = update_library.update_library(tmp_path)
    activity = data_of(tmp_path)["activity"]
    assert activity["excluded"] == [[name, reason] for name, reason in library.excluded]
    assert [name for name, _ in activity["excluded"]] == ["run-half"]
    assert activity["excluded"][0][1]  # library_index's own reason, not empty
    assert all(isinstance(i, str) for i in activity["issues"])


def test_data_js_carries_state_placement_and_words(tmp_path):
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    workspace = data_of(tmp_path)["workspace"]
    (output,) = [o for o in workspace["outputs"].values() if o["module"] == "CP-1"]
    assert output["state"] == {"established": True, "declared": None}
    assert len(output["placement"]) == len(workspace["handoffs"][output["sha256"]])
    assert set(output["words"]) == {"view", "reference", "calculations", "limits", "audit"}


def count_work(monkeypatch) -> dict[str, int]:
    """Wrap each reader of a delivery so one build's view.json reads and delivery checks count."""
    from credit_os import store

    import deploy_workflow.credit_os_catalogue as cat
    import deploy_workflow.library_index as index

    counts = {"view_reads": 0, "delivery_checks": 0}

    def reading(real):
        def read(folder, relative, *rest):
            counts["view_reads"] += relative.endswith("view.json")
            return real(folder, relative, *rest)

        return read

    def listing(real):
        def listed(folder, delivery, name):
            counts["view_reads"] += name == "view.json"
            return real(folder, delivery, name)

        return listed

    def checking(real):
        def check(*args, **kwargs):
            counts["delivery_checks"] += 1
            return real(*args, **kwargs)

        return check

    monkeypatch.setattr(index, "read_inside", reading(index.read_inside))
    monkeypatch.setattr(cat, "read_inside", reading(cat.read_inside))
    monkeypatch.setattr(store, "listed_bytes", listing(store.listed_bytes))
    real_check = index.delivery_folder
    for module in (index, cat):
        monkeypatch.setattr(module, "delivery_folder", checking(real_check))
    return counts


def test_one_build_verifies_each_delivery_once_and_reads_its_view_twice(tmp_path, monkeypatch):
    make_run(tmp_path, "run-a")
    counts = count_work(monkeypatch)
    update_library.update_library(tmp_path)
    # The library side reads view.json once, the store side once; the delivery is checked once.
    assert counts == {"view_reads": 2, "delivery_checks": 1}


def test_a_tampered_view_is_still_refused_in_a_build(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    (view,) = run_dir.glob("deliveries/*/view.json")
    view.write_bytes(view.read_bytes() + b" ")
    library = update_library.update_library(tmp_path)
    assert library.runs == [] and library.deliveries == {}
    assert "view.json no longer has its recorded sha256" in library.excluded[0][1]


# ---- Fix round 1 (2026-11-10): the run's own dependency edges and module times. Synthetic runs.
def record_of(tmp_path: Path, events: list[dict] | str | None, requested=("CP-0", "CP-1", "CP-1A")):
    run_dir = tmp_path / "runs" / "r1"
    run_dir.mkdir(parents=True)
    workflow = {"run": {"requested_modules": list(requested)}}
    (run_dir / "workflow.json").write_text(json.dumps(workflow), encoding="utf-8")
    if isinstance(events, list):
        lines = "".join(json.dumps(e) + "\n" for e in events)
        (run_dir / "events.jsonl").write_text(lines, encoding="utf-8")
    elif isinstance(events, str):
        (run_dir / "events.jsonl").write_text(events, encoding="utf-8")
    store = {"runs": {"r1": {"folder": "r1"}}, "issues": []}
    before = tree(run_dir)
    update_library.run_records(tmp_path, store)
    assert tree(run_dir) == before, "the run folder is only read"
    return store["runs"]["r1"].get("record"), store["issues"]


EVENTS = [
    {"at": "2026-01-01T10:00:00Z", "event": "module_started", "module": "CP-0"},
    {"at": "2026-01-01T10:05:00Z", "event": "module_accepted", "module": "CP-0"},
    {"at": "2026-01-01T10:06:00Z", "event": "module_started", "module": "CP-1A"},
    {"at": "2026-01-01T10:07:00Z", "event": "turn", "module": "CP-1A", "turn": 1},
]


def test_a_run_record_has_the_recorded_event_order_with_its_times(tmp_path):
    record, issues = record_of(tmp_path, EVENTS)
    assert issues == []
    assert "edges" not in record
    started = "2026-01-01T10:00:00Z"
    assert record["timed"] is True and record["steps"] == [
        {"module": "CP-0", "started": started, "accepted": "2026-01-01T10:05:00Z"},
        {"module": "CP-1A", "started": "2026-01-01T10:06:00Z", "accepted": None},
        {"module": "CP-1", "started": None, "accepted": None},
    ], "recorded start order first, then the modules never started, in plan order; no time invented"


def test_a_run_without_an_event_log_has_the_plan_order_and_no_times(tmp_path):
    record, issues = record_of(tmp_path, None)
    assert issues == [] and record["timed"] is False
    assert [s["module"] for s in record["steps"]] == ["CP-0", "CP-1", "CP-1A"]
    assert all(s["started"] is None and s["accepted"] is None for s in record["steps"])


def test_a_run_without_a_workflow_record_has_no_run_record(tmp_path):
    store = {"runs": {"r1": {"folder": "r1"}}, "issues": []}
    (tmp_path / "runs" / "r1").mkdir(parents=True)
    update_library.run_records(tmp_path, store)
    assert "record" not in store["runs"]["r1"] and store["issues"] == []


def test_an_unreadable_event_log_draws_no_time_and_names_the_failure(tmp_path):
    record, issues = record_of(tmp_path, '{"event": "module_started"\nnot json\n{}\n')
    assert record["timed"] is False and record["steps"]
    assert any("r1: events.jsonl could not be read" in i for i in issues)
    assert record["eventsIssue"] == "ValueError", (
        "the record says the log failed, not that it is absent"
    )


def test_a_run_with_no_log_carries_no_event_failure(tmp_path):
    record, _ = record_of(tmp_path, None)
    assert "eventsIssue" not in record


@pytest.mark.parametrize("line", ["[1]", '"text"', "null", "3"])
def test_a_json_line_that_is_not_an_object_names_the_failure_and_does_not_stop_the_build(
    tmp_path, line
):
    good = json.dumps(EVENTS[0])
    record, issues = record_of(tmp_path, f"{line}\n{good}\n")
    assert record["timed"] is False and record["eventsIssue"] == "ValueError"
    assert any("r1: events.jsonl could not be read" in i for i in issues)


def test_handoffs_zip_holds_the_delivered_markdown_byte_for_byte(tmp_path):
    import zipfile

    run_dir = make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    delivered = next((run_dir / "deliveries").iterdir())
    with zipfile.ZipFile(tmp_path / "library/downloads/run-a/handoffs.zip") as archive:
        assert archive.namelist() == ["CP-0.md", "CP-1.md"]
        for name in archive.namelist():
            assert archive.read(name) == (delivered / name).read_bytes()
    zip_path = data_of(tmp_path)["workspace"]["runs"]["run-a"]["evidence"]["zip"]
    assert (tmp_path / "library" / zip_path).is_file()


def test_each_handoff_and_instruction_is_a_library_file_the_evidence_links_to(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    delivered = next((run_dir / "deliveries").iterdir())
    library = tmp_path / "library"
    evidence = data_of(tmp_path)["workspace"]["runs"]["run-a"]["evidence"]
    assert [h["href"] for h in evidence["handoffs"]] == [
        "downloads/run-a/CP-0.md",
        "downloads/run-a/CP-1.md",
    ]
    for handoff in evidence["handoffs"]:
        assert (library / handoff["href"]).read_bytes() == (
            delivered / handoff["name"]
        ).read_bytes()
    instructions = evidence["record"]["instructions"]
    assert [i["href"] for i in instructions] == [
        "downloads/run-a/instructions/CP-0.md",
        "downloads/run-a/instructions/CP-1.md",
    ]
    for row in instructions:
        assert (library / row["href"]).read_bytes() == (
            run_dir / f"instructions/{row['module']}.md"
        ).read_bytes()


def test_an_instruction_file_that_changed_during_the_build_is_refused(tmp_path, monkeypatch):
    run_dir = make_run(tmp_path, "run-a")
    (run_dir / "instructions/CP-0.md").write_text("changed\n")
    with pytest.raises(Refused, match="instructions/CP-0.md changed during the build"):
        update_library.update_library(tmp_path)
