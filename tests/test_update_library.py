"""The update script: the static Credit OS library, written only to library/, from fixtures."""

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import test_changes as seam
from library_fixtures import make_run, method, with_changes, without_report

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library

from deploy_workflow.changes_check import cp8_issues
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


def test_checked_bytes_refuses_a_link_even_when_the_hash_matches(tmp_path):
    # The store never lists a linked handoff; this is the guard for a file swapped for a link after
    # the store read it (the bytes and so the hash still match).
    import hashlib

    target = tmp_path / "elsewhere.md"
    target.write_bytes(b"handoff\n")
    link = tmp_path / "CP-0.md"
    link.symlink_to(target)
    with pytest.raises(Refused, match="not a plain file"):
        update_library.checked_bytes(
            link, hashlib.sha256(b"handoff\n").hexdigest(), "run-a/CP-0.md"
        )


def test_a_symlinked_delivered_handoff_is_not_copied(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    (delivered,) = (run_dir / "deliveries").iterdir()
    real = delivered / "CP-0.md"
    elsewhere = tmp_path / "elsewhere.md"
    elsewhere.write_bytes(real.read_bytes())
    real.unlink()
    real.symlink_to(elsewhere)
    update_library.update_library(tmp_path)
    assert not (tmp_path / "library/downloads/run-a/CP-0.md").exists()


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
    assert "Listed 1 run(s)." in out
    assert "  legacy: not a CP-OS launcher run (no workflow.json)" in out
    assert str(tmp_path.resolve() / "library/index.html") in out


def test_a_missing_workspace_is_refused(tmp_path):
    with pytest.raises(Refused, match="Workspace not found"):
        update_library.update_library(tmp_path / "absent")


def test_the_command_turns_a_refusal_into_an_exit(tmp_path):
    with pytest.raises(SystemExit, match="Workspace not found"):
        update_library.main(["--workspace", str(tmp_path / "absent")])


def test_a_run_with_no_delivered_report_page_is_listed_with_every_page_and_an_earlier_run_still_is(
    tmp_path,
):
    """M1: the library lists a run from its handoffs; no report.html is needed or written."""
    make_run(tmp_path, "run-old", issuer_id="old", issuer_name="Old Synthetic", report_page=True)
    new = make_run(tmp_path, "run-new", report_page=False)
    assert not list(new.glob("deliveries/*/report.html"))
    library = update_library.update_library(tmp_path)
    assert sorted(r["id"] for r in library.runs) == ["run-new", "run-old"]
    assert library.excluded == []
    assert not [p for p in tree(tmp_path) if p.startswith("library/reports")]
    data = data_of(tmp_path)
    assert sorted(r["id"] for r in data["catalogue"]["real"]) == ["run-new", "run-old"]
    workspace = data["workspace"]
    (run,) = [r for r in workspace["runs"].values() if r["folder"] == "run-new"]
    assert sorted(run["modules"]) == ["CP-0", "CP-1"]
    outputs = [o for o in workspace["outputs"].values() if o["run"] == run["folder"]]
    assert sorted(o["module"] for o in outputs) == ["CP-0", "CP-1"]
    assert all(o["firstHeading"] and o["sha256"] in workspace["handoffs"] for o in outputs)
    evidence = run["evidence"]
    assert [h["module"] for h in evidence["handoffs"]] == ["CP-0", "CP-1"]
    assert evidence["record"] is not None and evidence["zip"]
    # The earlier run's own file list names its report.html as stored; the new run's names none.
    assert not [s for s in strings(run) if "report.html" in s]


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


def test_data_js_carries_the_method_changes_of_each_listed_run(tmp_path, monkeypatch):
    make_run(tmp_path, "run-a", version="")
    make_run(tmp_path, "run-b", version=" Amended.", issuer_id="zzz", issuer_name="Zeta Synthetic")
    monkeypatch.setattr("deploy_workflow.library_index.current_method", lambda: method(" Amended."))
    library = update_library.update_library(tmp_path)
    assert library.excluded == []
    changes = {
        r["folder"]: r["methodChanges"] for r in data_of(tmp_path)["workspace"]["runs"].values()
    }
    assert changes == {
        "run-a": ["CP-0: methods/cp0.md changed", "CP-1: prompts/CP-1.md changed"],
        "run-b": [],
    }


def test_a_store_run_that_is_not_a_listed_run_is_refused_not_shown_as_current():
    listed = SimpleNamespace(runs=[{"id": "run-a", "method_changes": []}])
    store = {"runs": {"x": {"folder": "run-z"}}}
    with pytest.raises(KeyError):
        update_library.method_changes(store, listed)


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


def test_a_download_outside_the_library_folder_is_refused(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    with pytest.raises(Refused, match="outside the library folder"):
        update_library.write_download(library, library / "../escaped.md", b"x")
    assert not (tmp_path / "escaped.md").exists()
    update_library.write_download(library, library / "downloads/ok.md", b"x")
    assert (library / "downloads/ok.md").read_bytes() == b"x"


# ---- The Changes tab's data: each run carries what its delivery says about the comparison.
PACK = {
    "schema": "cpos-changes/2",
    "prior": {"run": "nbg-2024-09-30-credit_snapshot", "as_of": "2024-09-30"},
    "measures": [{"key": "cash", "comparable": "yes", "difference": "0"}],
}
NOTE = "changes: not produced \u2014 cpos_live_not_accepted: CP-8 not accepted within bounds"


def changes_of(workspace: Path, folder: str) -> dict:
    runs = data_of(workspace)["workspace"]["runs"]
    return next(run["changes"] for run in runs.values() if run["folder"] == folder)


def current_run(workspace: Path, folder: str, **spec) -> Path:
    """A run with a current-kind delivery; returns its run folder."""
    return without_report(make_run(workspace, folder, **spec)).parent.parent


def test_a_run_that_records_no_comparison_is_not_a_first_run(tmp_path):
    current_run(tmp_path, "old")
    update_library.update_library(tmp_path)
    assert changes_of(tmp_path, "old") == {
        "lead": "CP-2",
        "first_run": False,
        "pack": None,
        "note": None,
        "problem": None,
        "verdicts": None,
    }


def test_a_first_run_is_the_run_that_records_it(tmp_path):
    with_changes(current_run(tmp_path, "first"), first=True)
    update_library.update_library(tmp_path)
    assert changes_of(tmp_path, "first") == {
        "lead": "CP-2",
        "first_run": True,
        "pack": None,
        "note": None,
        "problem": None,
        "verdicts": None,
    }


@pytest.mark.parametrize(
    "line",
    [
        "changes: first run of this pathway (not used: prior-1: its issuer name is another's)",
        "changes: not compared: the earlier run named at approval is no longer available",
        "changes: not compared: CP-8's first request would be over the cap",
    ],
)
def test_a_reason_the_run_records_for_no_comparison_reaches_the_library_verbatim(tmp_path, line):
    with_changes(current_run(tmp_path, "reasoned"), line=line)
    update_library.update_library(tmp_path)
    assert changes_of(tmp_path, "reasoned") == {
        "lead": "CP-2",
        "first_run": False,
        "pack": None,
        "note": line,
        "problem": None,
        "verdicts": None,
    }


@pytest.mark.parametrize(
    ("pathway", "lead"),
    [("earnings_update", "CP-1B"), ("short_snapshot", "CP-L10"), ("relative_value", "CP-2")],
)
def test_the_lead_module_of_the_pathway_travels_with_the_run(tmp_path, pathway, lead):
    current_run(tmp_path, "r", pathway=pathway)
    update_library.update_library(tmp_path)
    assert changes_of(tmp_path, "r")["lead"] == lead


def test_the_published_pack_is_carried_unchanged(tmp_path):
    with_changes(current_run(tmp_path, "later"), pack=json.dumps(PACK).encode())
    update_library.update_library(tmp_path)
    got = changes_of(tmp_path, "later")
    assert got["pack"] == PACK
    assert got["note"] is None
    assert got["problem"] is None


def test_a_cp8_that_was_not_produced_carries_its_recorded_reason(tmp_path):
    with_changes(current_run(tmp_path, "later"), note=NOTE)
    update_library.update_library(tmp_path)
    got = changes_of(tmp_path, "later")
    assert got["note"] == NOTE
    assert got["pack"] is None


@pytest.mark.parametrize(
    ("raw", "why"),
    [
        (b"{not json", "is not valid JSON"),
        (json.dumps({**PACK, "schema": "cpos-changes/1"}).encode(), "schema 'cpos-changes/1'"),
        (b"[1]", "is not a JSON object"),
    ],
)
def test_a_pack_that_cannot_be_read_is_said_so_and_is_never_a_first_run(tmp_path, raw, why):
    with_changes(current_run(tmp_path, "later"), pack=raw)
    update_library.update_library(tmp_path)
    got = changes_of(tmp_path, "later")
    assert got["pack"] is None
    assert why in got["problem"]
    issues = data_of(tmp_path)["workspace"]["issues"]
    assert any(i.startswith("later: ") and "changes.json" in i and why in i for i in issues)


# ---- One reader: the library carries the verdicts the Changes tab shows, read by the CP-8 checker.
SEAM_PACK = {
    **seam.PACK,
    "schema": "cpos-changes/2",
    "prior": {"run": "earlier", "as_of": "2024-09-30"},
}


def run_with_cp8(workspace: Path, text: str) -> Path:
    """A current run whose delivery lists the comparison pack (as `changes.json`) and whose CP-8
    handoff is `text`."""
    run = without_report(
        make_run(workspace, "later", modules=("CP-0", "CP-1", "CP-8"), cp8=text)
    ).parent.parent
    with_changes(run, pack=json.dumps(SEAM_PACK).encode())
    return run


@pytest.mark.parametrize("case", seam.SEAM["measure_rows"], ids=lambda c: c["name"])
def test_the_library_carries_the_verdict_of_every_seam_case_the_fixture_states(tmp_path, case):
    text = seam._seam_text(case)
    run_with_cp8(tmp_path, text)
    update_library.update_library(tmp_path)
    verdicts = changes_of(tmp_path, "later")["verdicts"]
    assert verdicts["measures"][case["measure"]]["kind"] == case["page"]
    assert (cp8_issues(text, SEAM_PACK) == ()) is case["accepted"]


def test_the_library_carries_the_modules_and_the_ledger_counts_of_the_handoff(tmp_path):
    run_with_cp8(tmp_path, seam.REGISTERS)
    update_library.update_library(tmp_path)
    verdicts = changes_of(tmp_path, "later")["verdicts"]
    assert verdicts["modules"]["CP-2"] == {
        "status": "Strengthened",
        "cause": "New period",
        "why": "Leverage fell.",
    }
    assert verdicts["ledger"] == [
        ["Closed", 1],
        ["Remaining", 1],
        ["New", 1],
        ["No longer stated", 0],
    ]
    assert verdicts["measures"]["coverage"]["reason"] == "the earlier run does not state it"


@pytest.mark.parametrize("kind", ["no handoff", "no pack", "a note"])
def test_the_library_carries_no_verdicts_without_a_pack_and_a_handoff(tmp_path, kind):
    run = without_report(
        make_run(
            tmp_path,
            "later",
            modules=("CP-0", "CP-1") if kind == "no handoff" else ("CP-0", "CP-1", "CP-8"),
            cp8=seam.REGISTERS,
        )
    ).parent.parent
    if kind == "no handoff":
        with_changes(run, pack=json.dumps(SEAM_PACK).encode())
    else:
        with_changes(run, note=NOTE if kind == "a note" else None)
    update_library.update_library(tmp_path)
    assert changes_of(tmp_path, "later")["verdicts"] is None


def test_a_cp8_output_that_is_not_utf8_is_a_stated_problem_not_a_silent_null(tmp_path, monkeypatch):
    run_with_cp8(tmp_path, seam.REGISTERS)
    real = update_library.checked_bytes
    monkeypatch.setattr(
        update_library,
        "checked_bytes",
        lambda path, digest, label: b"\xff\xfe" if "CP-8" in label else real(path, digest, label),
    )
    update_library.update_library(tmp_path)
    got = changes_of(tmp_path, "later")
    assert got["verdicts"] is None
    assert "CP-8" in got["problem"] and "not valid UTF-8" in got["problem"]
    issues = data_of(tmp_path)["workspace"]["issues"]
    assert any(i.startswith("later: ") and "not valid UTF-8" in i for i in issues)
