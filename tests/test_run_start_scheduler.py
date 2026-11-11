"""The scheduler takes an approved submission and starts exactly one run for it.

Child processes are the fake launcher (tests/fixtures/fake_launcher.py): no provider, no spend.
"""

from __future__ import annotations

import io
import json
import os
import threading
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from inbox_fixtures import CONTEXT, layout, pump, settings

from deploy_workflow.inbox import runs
from deploy_workflow.inbox import watcher as watcher_module
from deploy_workflow.inbox.runs import Record, load_all
from deploy_workflow.inbox.watcher import Watcher
from deploy_workflow.run_start import submissions
from deploy_workflow.run_start.submissions import Answers, Refused, context_bytes

pytest_plugins = ["inbox_fixtures"]

PATHWAY = "credit_snapshot"


def answers_for(**change: Any) -> Answers:
    context = json.loads(json.dumps(CONTEXT))
    context["run"]["pathway"] = PATHWAY
    context["run"]["as_of"] = "2026-11-09"
    context["identity"]["issuer_id"] = "acme"
    context["identity"]["issuer_name"] = "Acme Corp"
    base: dict[str, Any] = {
        "context": context,
        "modules": [],
        "max_turns": 32,
        "level": "basic",
        "submitted_by": "analyst",
    }
    base.update(change)
    return cast(Answers, base)


def upload(root: Path, payload: bytes = b"Net sales were 100.") -> str:
    lay = layout(root)
    sid = submissions.new(lay)
    (submissions.files_folder(lay, sid) / "a.txt").write_bytes(payload)
    return sid


def approved(root: Path, sid: str, answers: Answers) -> str:
    """The digest the service issues for these answers: only ``summary`` can make one."""
    got = submissions.summary(
        layout(root), sid, answers, config=settings(root).config, cap=settings(root).cap
    )
    assert got["error"] == "", got["error"]
    return str(got["digest"])


def test_a_submission_becomes_one_running_run_with_its_context(root, fake_env):
    fake_env({"sleep": 30})
    answers = answers_for(modules=["CP-0", "CP-1"], max_turns=16, submitted_by="eg")
    sid = upload(root)
    w = Watcher(settings(root))
    record = w.submit(sid, answers, approved(root, sid, answers))
    assert record.status == "queued"
    assert record.prepared
    assert (record.pathway, record.folder, record.issuer_id) == (PATHWAY, "Acme Corp", "acme")
    assert (record.issuer_name, record.as_of) == ("Acme Corp", "2026-11-09")
    assert (record.submission, record.modules, record.max_turns) == (sid, ("CP-0", "CP-1"), 16)
    assert (record.level, record.submitted_by) == ("basic", "eg")
    pump(w, lambda: [r.status for r in load_all(layout(root))] == ["running"])
    drop = layout(root).drops / record.id
    assert (drop / "context.json").read_bytes() == context_bytes(answers)
    assert (drop / "a.txt").is_file()
    assert not (layout(root).uploads / sid / "files").exists()
    assert not (layout(root).uploads / sid / "sealed").exists()
    w.close()


def test_submit_twice_and_from_two_threads_gives_one_run(root, fake_env):
    fake_env({"sleep": 30})
    answers = answers_for()
    sid = upload(root)
    d = approved(root, sid, answers)
    w = Watcher(settings(root))
    found: list[Record] = []
    failures: list[BaseException] = []

    def call() -> None:
        try:
            found.append(w.submit(sid, answers, d))
        except BaseException as error:  # noqa: BLE001 - collected and asserted below
            failures.append(error)

    threads = [threading.Thread(target=call) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert not failures
    assert len(found) == 8
    assert len({r.id for r in found}) == 1
    assert len(load_all(layout(root))) == 1
    assert len(list(layout(root).drops.iterdir())) == 1
    pump(w, lambda: [r.status for r in load_all(layout(root))] == ["running"])
    assert w.submit(sid, answers, d).id == found[0].id  # after it has started, still the same
    assert len(load_all(layout(root))) == 1
    w.close()


def test_a_changed_file_or_answer_after_approval_is_refused_and_nothing_starts(root, fake_env):
    fake_env({"sleep": 30})
    answers = answers_for()
    sid = upload(root)
    d = approved(root, sid, answers)
    w = Watcher(settings(root))
    (submissions.files_folder(layout(root), sid) / "a.txt").write_bytes(b"Net sales were 999.")
    with pytest.raises(Refused, match="changed after approval"):
        w.submit(sid, answers, d)
    (submissions.files_folder(layout(root), sid) / "a.txt").write_bytes(b"Net sales were 100.")
    with pytest.raises(Refused, match="changed after approval"):
        w.submit(sid, answers_for(max_turns=8), d)
    with pytest.raises(Refused, match="changed after approval"):
        w.submit(sid, answers_for(modules=["CP-0"]), d)
    w.step()
    w.step()
    assert load_all(layout(root)) == []
    assert list(layout(root).drops.iterdir()) == []
    files = submissions.files_folder(layout(root), sid)
    assert (files / "a.txt").is_file()
    assert not (files / "context.json").exists()
    w.submit(sid, answers, d)  # the unchanged submission is still accepted
    w.close()


def _submit_n(root: Path, w: Watcher, count: int) -> list[Record]:
    out = []
    for n in range(count):
        answers = answers_for()
        sid = upload(root, f"Net sales were {n}.".encode())
        out.append(w.submit(sid, answers, approved(root, sid, answers)))
    return out


def test_the_fourth_submission_waits(root, fake_env):
    fake_env({"sleep": 30})
    w = Watcher(settings(root, max_running=3))
    records = _submit_n(root, w, 4)
    w.step()
    w.step()
    by_id = {r.id: r.status for r in load_all(layout(root))}
    assert sorted(by_id.values()) == ["queued", "running", "running", "running"]
    assert by_id[records[3].id] == "queued"  # the earliest id starts first
    w.close()


def test_the_daily_limit_holds(root, fake_env):
    fake_env({"sleep": 30})
    w = Watcher(settings(root, max_running=3, max_per_day=2))
    _submit_n(root, w, 3)
    w.step()
    w.step()
    assert sorted(r.status for r in load_all(layout(root))) == ["queued", "running", "running"]
    assert "daily limit of 2" in (root / "_engine/activity.js").read_text(encoding="utf-8")
    w.close()


def test_modules_and_turns_reach_the_launcher_command(root):
    lay = layout(root)
    record = Record("r1", PATHWAY, "Acme", "queued", "t", modules=("CP-0", "CP-1"), max_turns=16)
    argv = runs.command(
        lay,
        record,
        Path("c.json"),
        launcher=("L",),
        config="sol-medium",
        cap=Decimal(20),
        ruling=None,
    )
    at = argv.index("--modules")
    assert argv[at : at + 3] == ["--modules", "CP-0", "CP-1"]
    at = argv.index("--max-turns")
    assert argv[at : at + 2] == ["--max-turns", "16"]
    plain = runs.command(
        lay,
        Record("r2", PATHWAY, "Acme", "queued", "t"),
        Path("c.json"),
        launcher=("L",),
        config="sol-medium",
        cap=Decimal(20),
        ruling=None,
    )
    assert "--modules" not in plain
    assert "--max-turns" not in plain


def test_a_restart_starts_a_queued_submission_once_and_keeps_unsubmitted_uploads(root, fake_env):
    fake_env({"sleep": 30})
    answers = answers_for()
    sid = upload(root)
    other = upload(root, b"Net sales were 1 (never submitted).")
    first = Watcher(settings(root))
    record = first.submit(sid, answers, approved(root, sid, answers))
    first.close()
    second = Watcher(settings(root))
    pump(second, lambda: [r.status for r in load_all(layout(root))] == ["running"])
    second.step()
    second.step()
    [only] = load_all(layout(root))
    assert only.id == record.id
    assert (submissions.files_folder(layout(root), other) / "a.txt").is_file()
    assert second.submit(sid, answers, "stale-after-restart").id == record.id
    second.close()


def test_a_restart_between_record_and_rename_finishes_the_move(root, fake_env, monkeypatch):
    fake_env({"sleep": 30})
    answers = answers_for()
    sid = upload(root)
    d = approved(root, sid, answers)
    first = Watcher(settings(root))
    drops = layout(root).drops
    real_rename = os.rename

    def cut_short(src: Any, dst: Any, *a: Any, **k: Any) -> None:
        if Path(dst).parent == drops:
            raise OSError("cut short")
        real_rename(src, dst, *a, **k)

    monkeypatch.setattr(watcher_module.os, "rename", cut_short)
    with pytest.raises(OSError, match="cut short"):
        first.submit(sid, answers, d)
    monkeypatch.undo()
    [saved] = load_all(layout(root))
    assert saved.status == "queued"
    assert not (drops / saved.id).exists()
    first.close()
    second = Watcher(settings(root))
    assert (drops / saved.id / "context.json").read_bytes() == context_bytes(answers)
    assert (drops / saved.id / "a.txt").is_file()
    pump(second, lambda: [r.status for r in load_all(layout(root))] == ["running"])
    assert len(load_all(layout(root))) == 1
    second.close()


def test_a_record_saved_before_this_change_still_loads(root):
    lay = layout(root)
    Watcher(settings(root)).close()
    old = {
        "id": "20261101-000000-01",
        "pathway": PATHWAY,
        "folder": "acme",
        "status": "finished",
        "claimed_at": "2026-11-01T00:00:00Z",
        "files": ["a.txt"],
        "prepared": True,
    }
    (lay.state / "20261101-000000-01.json").write_text(json.dumps(old), encoding="utf-8")
    [record] = load_all(lay)
    assert (record.submission, record.modules, record.max_turns) == ("", (), 32)
    assert (record.level, record.submitted_by) == ("", "")


# -- fix round 1: what reaches the launcher, what an approval covers --------------------------


def _write_issued(root: Path, sid: str, value: str) -> None:
    (layout(root).uploads / sid / "issued").write_text(value + "\n", encoding="ascii")


HOSTILE_MODULES = {
    "cap": ["CP-0", "--cap", "1000"],
    "sources": ["CP-0", "--sources", "/etc"],
    "out": ["CP-0", "--out", "/tmp/x"],
}


@pytest.mark.parametrize("which", sorted(HOSTILE_MODULES))
def test_a_module_that_is_not_a_method_is_refused_even_when_the_digest_was_issued(
    root, fake_env, which
):
    fake_env({"sleep": 30})
    answers = answers_for(modules=HOSTILE_MODULES[which])
    sid = upload(root)
    d = submissions.digest(layout(root), sid, answers)
    _write_issued(root, sid, d)  # as if a summary had issued it: the module check stands alone
    w = Watcher(settings(root))
    with pytest.raises(Refused, match="unknown module"):
        w.submit(sid, answers, d)
    w.step()
    assert load_all(layout(root)) == []
    assert (submissions.files_folder(layout(root), sid) / "a.txt").is_file()  # not sealed
    w.close()


def test_a_digest_the_service_never_issued_is_refused(root, fake_env):
    fake_env({"sleep": 30})
    answers = answers_for()
    sid = upload(root)
    own = submissions.digest(layout(root), sid, answers)  # a client can compute this itself
    w = Watcher(settings(root))
    with pytest.raises(Refused, match="changed after approval"):
        w.submit(sid, answers, own)
    assert load_all(layout(root)) == []
    assert submissions.files_folder(layout(root), sid).name == "files"  # unsealed again
    w.submit(sid, answers, approved(root, sid, answers))  # a summary makes it acceptable
    w.close()


@pytest.mark.parametrize("turns", [0, -1, True, "7", 1.5, 10**12])
def test_max_turns_outside_one_to_sixty_four_is_refused(root, fake_env, turns):
    fake_env({"sleep": 30})
    sid = upload(root)
    w = Watcher(settings(root))
    with pytest.raises(Refused):
        w.submit(sid, answers_for(max_turns=turns), "x")
    assert load_all(layout(root)) == []
    w.close()


def test_an_upload_landing_inside_the_submit_window_is_refused_and_never_reaches_the_run(
    root, fake_env, monkeypatch
):
    fake_env({"sleep": 30})
    answers = answers_for()
    sid = upload(root)
    d = approved(root, sid, answers)
    w = Watcher(settings(root))
    real_save = runs.save
    outcomes: list[BaseException | None] = []

    def save(lay: Any, record: Record) -> None:
        real_save(lay, record)
        if record.submission == sid and not outcomes:  # right after the record, before the rename
            body = b"Net sales were 5."
            try:
                submissions.add_file(layout(root), sid, "late.txt", io.BytesIO(body), len(body))
                outcomes.append(None)
            except Refused as refusal:
                outcomes.append(refusal)

    monkeypatch.setattr(watcher_module.runs, "save", save)
    record = w.submit(sid, answers, d)
    monkeypatch.undo()
    assert len(outcomes) == 1 and isinstance(outcomes[0], Refused)
    drop = layout(root).drops / record.id
    assert sorted(p.name for p in drop.iterdir()) == ["a.txt", "context.json"]
    w.close()


def _cut_short_submit(root: Path, w: Watcher, monkeypatch: pytest.MonkeyPatch) -> str:
    """Upload, approve and submit with the rename into drops cut short; the submission's ID."""
    answers = answers_for()
    sid = upload(root)
    d = approved(root, sid, answers)
    drops = layout(root).drops
    real_rename = os.rename

    def cut_short(src: Any, dst: Any, *a: Any, **k: Any) -> None:
        if Path(dst).parent == drops:
            raise OSError("cut short")
        real_rename(src, dst, *a, **k)

    monkeypatch.setattr(watcher_module.os, "rename", cut_short)
    with pytest.raises(OSError, match="cut short"):
        w.submit(sid, answers, d)
    monkeypatch.undo()
    return sid


def test_after_a_cut_short_rename_the_uploads_no_longer_accept_changes(root, fake_env, monkeypatch):
    fake_env({"sleep": 30})
    w = Watcher(settings(root))
    sid = _cut_short_submit(root, w, monkeypatch)
    body = b"Net sales were 7."
    with pytest.raises(Refused):
        submissions.add_file(layout(root), sid, "later.txt", io.BytesIO(body), len(body))
    w.close()


@pytest.mark.parametrize("restart", [False, True])
def test_a_move_finished_after_the_documents_changed_fails_the_run_and_moves_nothing(
    root, fake_env, monkeypatch, restart
):
    fake_env({"sleep": 30})
    w = Watcher(settings(root))
    sid = _cut_short_submit(root, w, monkeypatch)
    [saved] = load_all(layout(root))
    assert saved.digest  # the record keeps what was approved
    (layout(root).uploads / sid / "sealed" / "later.txt").write_bytes(b"Net sales were 8.")
    if restart:
        w.close()
        w = Watcher(settings(root))
    w.step()
    w.step()
    [after] = load_all(layout(root))
    assert after.status == "failed"
    assert after.reason == "the submitted documents changed before the run could start"
    assert not (layout(root).drops / saved.id).exists()
    assert w._children == {}
    w.close()


def test_a_poisoned_record_fails_alone_and_the_next_run_still_starts(root, fake_env, caplog):
    fake_env({"sleep": 30})
    w = Watcher(settings(root))
    first, second = _submit_n(root, w, 2)
    w._put(replace(first, modules=("--cap", "1000")))  # a hand-edited record
    with caplog.at_level("ERROR"):
        w.step()
        w.step()
    by_id = {r.id: r for r in load_all(layout(root))}
    assert by_id[first.id].status == "failed"
    assert by_id[first.id].reason
    assert by_id[second.id].status == "running"
    assert w._children.keys() == {second.id}
    w.close()


@pytest.mark.parametrize("sid", ["", "x", "A" * 32, "0" * 31, "0" * 33, 5, None])
def test_a_malformed_submission_id_is_refused_before_any_record_is_looked_at(root, fake_env, sid):
    lay = layout(root)
    Watcher(settings(root)).close()
    (lay.drops / "20261101-000000-01").mkdir()  # a folder with no record: recovery records it
    w = Watcher(settings(root))
    with pytest.raises(Refused, match="unknown submission"):
        w.submit(sid, answers_for(), "anything")  # type: ignore[arg-type]
    w.close()


def test_a_transient_move_failure_is_retried_not_failed(root, fake_env, monkeypatch):
    fake_env({"sleep": 30})
    lay = layout(root)
    answers = answers_for()
    sid = upload(root)
    d = approved(root, sid, answers)
    w = Watcher(settings(root))
    real_rename = os.rename
    failures = [2]  # submit's rename and the first poll's rename fail

    def flaky(src: Any, dst: Any, *a: Any, **k: Any) -> None:
        if Path(dst).parent == lay.drops and failures[0]:
            failures[0] -= 1
            raise OSError("transient")
        real_rename(src, dst, *a, **k)

    monkeypatch.setattr(watcher_module.os, "rename", flaky)
    with pytest.raises(OSError):
        w.submit(sid, answers, d)
    w.step()
    [mid] = load_all(lay)
    assert mid.status == "queued", f"{mid.status}: {mid.reason}"
    w.step()
    monkeypatch.undo()
    [rec] = load_all(lay)
    assert rec.status in ("queued", "running"), f"{rec.status}: {rec.reason}"
    pump(w, lambda: [r.status for r in load_all(lay)] == ["running"])
    w.close()


def test_a_queued_submission_with_neither_folder_fails(root, fake_env):
    fake_env({"sleep": 30})
    answers = answers_for()
    sid = upload(root)
    w = Watcher(settings(root))
    record = w.submit(sid, answers, approved(root, sid, answers))
    os.rename(layout(root).drops / record.id, layout(root).root / "gone")
    w.step()
    [after] = load_all(layout(root))
    assert after.status == "failed"
    w.close()


# ---- review round 2 ----


def test_fifty_submissions_in_a_day_do_not_block_a_new_one(root, fake_env, monkeypatch):
    fake_env({"sleep": 30})
    monkeypatch.setattr(submissions, "MAX_OPEN", 3)
    w = Watcher(settings(root, max_running=3))
    _submit_n(root, w, 4)  # more than MAX_OPEN, all submitted
    lay = layout(root)
    assert submissions._open_folders(lay) == []
    assert submissions.new(lay)
    assert not [p for p in lay.uploads.iterdir() if (p / "sealed").exists()]
    w.close()


def test_a_failed_removal_of_the_moved_uploads_folder_is_logged_and_the_run_goes_on(
    root, fake_env, monkeypatch, caplog
):
    fake_env({"sleep": 30})
    w = Watcher(settings(root))
    answers = answers_for()
    sid = upload(root)
    real = submissions.shutil.rmtree

    def busy(path: Any, *a: Any, **k: Any) -> None:
        if Path(path).name == sid:  # only the uploads folder: the summary's cleanup still works
            raise OSError("busy")
        real(path, *a, **k)

    monkeypatch.setattr(submissions.shutil, "rmtree", busy)
    with caplog.at_level("WARNING", logger=submissions.__name__):
        record = w.submit(sid, answers, approved(root, sid, answers))
    assert "could not remove" in caplog.text
    assert (layout(root).drops / record.id / "a.txt").is_file()
    assert submissions._open_folders(layout(root)) == []
    w.close()


def test_a_cut_short_rename_finished_by_a_poll_also_removes_the_uploads_folder(
    root, fake_env, monkeypatch
):
    fake_env({"sleep": 30})
    w = Watcher(settings(root))
    sid = _cut_short_submit(root, w, monkeypatch)
    w.step()
    assert not (layout(root).uploads / sid).exists()
    w.close()


def test_a_planted_sealed_link_is_refused_by_submit_and_never_becomes_a_run(root, fake_env):
    fake_env({"sleep": 30})
    lay = layout(root)
    sid = upload(root)
    answers = answers_for()
    digest = approved(root, sid, answers)
    outside = root / "outside"
    outside.mkdir()
    (outside / "a.txt").write_bytes(b"Net sales were 100.")  # the same bytes: the digest matches
    (lay.uploads / sid / "sealed").symlink_to(outside, target_is_directory=True)
    w = Watcher(settings(root))
    with pytest.raises(Refused):
        w.submit(sid, answers, digest)
    assert load_all(lay) == []
    assert not any(p.is_symlink() for p in lay.drops.iterdir())
    w.close()


def test_a_record_that_cannot_become_a_command_uses_no_daily_slot(root, fake_env):
    fake_env({"sleep": 30})
    w = Watcher(settings(root, max_running=3, max_per_day=2))
    first, second, third = _submit_n(root, w, 3)
    w._put(replace(first, modules=("--cap", "1000")))
    w.step()
    w.step()
    by_id = {r.id: r for r in load_all(layout(root))}
    assert by_id[first.id].status == "failed" and by_id[first.id].started_at == ""
    assert w._children.keys() == {second.id, third.id}  # the limit of 2 still held two runs
    w.close()


def test_the_recheck_of_a_cut_short_move_never_touches_context_json(root, fake_env, monkeypatch):
    fake_env({"sleep": 30})
    w = Watcher(settings(root))
    sid = _cut_short_submit(root, w, monkeypatch)
    context = layout(root).uploads / sid / "sealed" / "context.json"
    before = context.read_bytes()
    real = submissions.digest
    seen = []

    def killed(lay, s, answers):
        seen.append(context.read_bytes())
        raise KeyboardInterrupt  # a kill inside the recheck

    monkeypatch.setattr(submissions, "digest", killed)
    with pytest.raises(KeyboardInterrupt):
        w.step()
    monkeypatch.setattr(submissions, "digest", real)
    assert seen == [before] and context.read_bytes() == before
    w.step()
    [record] = load_all(layout(root))
    assert record.status == "running"
    w.close()


def test_the_sweep_does_not_delete_the_files_of_a_queued_submission(root, fake_env, monkeypatch):
    fake_env({"sleep": 30})
    w = Watcher(settings(root))
    sid = _cut_short_submit(root, w, monkeypatch)
    stale = (layout(root).uploads / sid).stat().st_mtime + submissions.STALE_SECONDS + 10
    real_rename = os.rename

    def refuse(src: Any, dst: Any, *a: Any, **k: Any) -> None:
        if Path(dst).parent == layout(root).drops:
            raise OSError("still cut short")
        real_rename(src, dst, *a, **k)

    monkeypatch.setattr(watcher_module.os, "rename", refuse)
    w.clock = lambda: stale
    w.step()
    assert (layout(root).uploads / sid / "sealed" / "a.txt").is_file()
    assert [r.status for r in load_all(layout(root))] == ["queued"]
    monkeypatch.undo()
    w.step()
    w.step()
    assert [r.status for r in load_all(layout(root))] == ["running"]
    w.close()


def test_a_full_queue_refuses_a_submission_before_sealing_it(root, fake_env, monkeypatch):
    fake_env({"sleep": 30})
    monkeypatch.setattr(watcher_module, "MAX_QUEUED", 2)
    w = Watcher(settings(root, max_running=1))
    _submit_n(root, w, 2)
    answers = answers_for()
    sid = upload(root)
    digest = approved(root, sid, answers)
    with pytest.raises(Refused, match="too many runs are waiting; try again later"):
        w.submit(sid, answers, digest)
    assert (layout(root).uploads / sid / "files" / "a.txt").is_file()  # not sealed, not moved
    assert len(load_all(layout(root))) == 2
    w.step()  # one starts, one slot frees up in the queue
    w.step()
    assert w.submit(sid, answers, digest).status == "queued"
    w.close()
