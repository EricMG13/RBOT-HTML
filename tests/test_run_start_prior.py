"""Reading an earlier run's inputs from the run records (no provider: the fake launcher)."""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from dataclasses import replace

import pytest
from inbox_fixtures import layout, pump, settings, submit_run

from deploy_workflow.inbox import runs
from deploy_workflow.inbox.layout import ensure_layout
from deploy_workflow.inbox.scheduler import Scheduler
from deploy_workflow.run_start import prior, submissions

pytest_plugins = ["inbox_fixtures"]


@pytest.fixture
def scheduler(root, fake_env) -> Iterator[Scheduler]:
    fake_env({"events": [["delivered", {}]]})
    w = Scheduler(settings(root))
    try:
        yield w
    finally:
        w.close()


def test_inputs_blank_the_dates_and_list_the_files_without_the_context(scheduler, root):
    record = submit_run(scheduler, root, "acme")
    pump(scheduler, lambda: (layout(root).drops / record.id / "context.json").is_file())
    got = prior.inputs(layout(root), record.id)
    assert set(got) == {
        "run", "issuer_id", "issuer_name", "pathway", "context",
        "files", "level", "modules", "max_turns",
    }  # fmt: skip
    assert got["issuer_id"] == "acme" and got["run"] == record.id
    run = got["context"]["run"]
    assert [run[k] for k in ("as_of", "cutoff", "current_period", "prior_period")] == [""] * 4
    assert got["context"]["identity"]["issuer_id"] == "acme"
    assert got["files"] == [{"name": "a.txt", "size": len(b"Net sales were 100 for acme.")}]


def test_a_record_without_a_source_folder_gives_identity_only(scheduler, root):
    record = submit_run(scheduler, root, "acme")
    pump(scheduler, lambda: (layout(root).drops / record.id).is_dir())
    shutil.rmtree(layout(root).drops / record.id)
    got = prior.inputs(layout(root), record.id)
    assert got["context"] is None and got["files"] == [] and got["issuer_id"] == "acme"


def test_an_unknown_run_is_refused(root):
    with pytest.raises(submissions.Refused, match="^unknown run$"):
        prior.inputs(layout(root), "20261111-000000-01")


def test_a_linked_source_folder_or_context_is_not_read(scheduler, root, tmp_path):
    record = submit_run(scheduler, root, "acme")
    context = layout(root).drops / record.id / "context.json"
    pump(scheduler, context.is_file)
    outside = tmp_path / "outside.json"
    outside.write_text(context.read_text())
    context.unlink()
    context.symlink_to(outside)
    got = prior.inputs(layout(root), record.id)
    assert got["context"] is None
    assert prior.source(layout(root), record.id)[1] is None
    # The whole folder linked elsewhere is not read either.
    folder = layout(root).drops / record.id
    real = tmp_path / "elsewhere"
    shutil.move(str(folder), str(real))
    (real / "context.json").unlink()
    (real / "context.json").write_text(outside.read_text())
    folder.symlink_to(real, target_is_directory=True)
    got = prior.inputs(layout(root), record.id)
    assert got["context"] is None and got["files"] == []


def test_issuer_counts_finished_runs_and_names_the_latest(scheduler, root):
    first = submit_run(scheduler, root, "acme")
    second = submit_run(scheduler, root, "acme", payload=b"Net sales were 200.")
    submit_run(scheduler, root, "other")
    lay = layout(root)

    def done() -> bool:
        return all(r.status == "finished" for r in runs.load_all(lay))

    pump(scheduler, done, limit=60)
    later = max(first.id, second.id)
    got = prior.issuer(lay, "acme")
    assert got == {
        "runs": 2, "latest_as_of": "2026-11-09",
        "latest_run": later, "issuer_name": "Acme Corp",
    }  # fmt: skip
    assert prior.issuer(lay, "nobody") == {
        "runs": 0, "latest_as_of": "", "latest_run": "", "issuer_name": "",
    }  # fmt: skip


def test_the_latest_run_is_the_greatest_as_of_then_the_greatest_id(root):
    lay = ensure_layout(root)
    base = runs.Record(id="x", pathway="p", folder="f", status="failed", claimed_at="")
    for rid, as_of, status in (
        ("20261101-000000-01", "2026-11-05", "finished"),
        ("20261102-000000-01", "2026-11-09", "failed"),
        ("20261103-000000-01", "2026-11-09", "finished"),
        ("20261104-000000-01", "2026-11-01", "finished"),
    ):
        runs.save(
            lay,
            replace(base, id=rid, as_of=as_of, status=status, issuer_id="acme", issuer_name=rid),
        )
    got = prior.issuer(lay, "acme")
    assert got["runs"] == 3 and got["latest_as_of"] == "2026-11-09"
    assert got["latest_run"] == "20261103-000000-01"
    assert got["issuer_name"] == "20261103-000000-01"


def test_files_are_listed_when_the_context_is_not_usable(scheduler, root, caplog):
    record = submit_run(scheduler, root, "acme")
    context = layout(root).drops / record.id / "context.json"
    pump(scheduler, context.is_file)
    context.write_text("[]")
    got = prior.inputs(layout(root), record.id)
    assert got["context"] is None
    assert got["files"] == [{"name": "a.txt", "size": len(b"Net sales were 100 for acme.")}]
    assert "not an object" in caplog.text
    context.write_text('{"run": 1, "identity": {}}')
    assert prior.inputs(layout(root), record.id)["context"] is None
    assert "lacks a run or identity object" in caplog.text


def test_a_refused_listing_is_named_in_the_reply_and_a_good_one_has_no_error(scheduler, root):
    record = submit_run(scheduler, root, "acme")
    folder = layout(root).drops / record.id
    pump(scheduler, (folder / "context.json").is_file)
    assert "error" not in prior.inputs(layout(root), record.id)
    (folder / "linked.txt").symlink_to(folder / "a.txt")
    got = prior.inputs(layout(root), record.id)
    assert got["files"] == [] and "linked.txt" in got["error"]
    assert str(folder) not in got["error"]
