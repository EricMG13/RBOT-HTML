"""The scheduler takes an approved submission and starts exactly one run for it.

Child processes are the fake launcher (tests/fixtures/fake_launcher.py): no provider, no spend.
"""

# ruff: noqa: F811 - fixtures imported from inbox_fixtures are redefined as test parameters

from __future__ import annotations

import json
import os
import threading
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from inbox_fixtures import (
    CONTEXT,
    _no_leaked_log_handlers,  # noqa: F401 - an autouse fixture
    fake_env,  # noqa: F401 - fixtures
    layout,
    listed,  # noqa: F401
    pump,
    root,  # noqa: F401
    settings,
)

from deploy_workflow.inbox import runs
from deploy_workflow.inbox import watcher as watcher_module
from deploy_workflow.inbox.runs import Record, load_all
from deploy_workflow.inbox.watcher import Watcher
from deploy_workflow.run_start import submissions
from deploy_workflow.run_start.submissions import Answers, Refused, context_bytes

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
    return base  # type: ignore[return-value]


def upload(root: Path, payload: bytes = b"%PDF-1.4 not real") -> str:
    lay = layout(root)
    sid = submissions.new(lay)
    (submissions.files_folder(lay, sid) / "a.pdf").write_bytes(payload)
    return sid


def approved(root: Path, sid: str, answers: Answers) -> str:
    return submissions.digest(layout(root), sid, answers)


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
    assert (drop / "a.pdf").is_file()
    assert not (layout(root).uploads / sid / "files").exists()
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
    (submissions.files_folder(layout(root), sid) / "a.pdf").write_bytes(b"%PDF-1.4 changed")
    with pytest.raises(Refused, match="changed after approval"):
        w.submit(sid, answers, d)
    (submissions.files_folder(layout(root), sid) / "a.pdf").write_bytes(b"%PDF-1.4 not real")
    with pytest.raises(Refused, match="changed after approval"):
        w.submit(sid, answers_for(max_turns=8), d)
    with pytest.raises(Refused, match="changed after approval"):
        w.submit(sid, answers_for(modules=["CP-0"]), d)
    w.step()
    w.step()
    assert load_all(layout(root)) == []
    assert list(layout(root).drops.iterdir()) == []
    files = submissions.files_folder(layout(root), sid)
    assert (files / "a.pdf").is_file()
    assert not (files / "context.json").exists()
    w.submit(sid, answers, d)  # the unchanged submission is still accepted
    w.close()


def _submit_n(root: Path, w: Watcher, count: int) -> list[Record]:
    out = []
    for n in range(count):
        answers = answers_for()
        sid = upload(root, f"%PDF-1.4 {n}".encode())
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
    other = upload(root, b"%PDF-1.4 never submitted")
    first = Watcher(settings(root))
    record = first.submit(sid, answers, approved(root, sid, answers))
    first.close()
    second = Watcher(settings(root))
    pump(second, lambda: [r.status for r in load_all(layout(root))] == ["running"])
    second.step()
    second.step()
    [only] = load_all(layout(root))
    assert only.id == record.id
    assert (submissions.files_folder(layout(root), other) / "a.pdf").is_file()
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
    assert (drops / saved.id / "a.pdf").is_file()
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
        "files": ["a.pdf"],
        "prepared": True,
    }
    (lay.state / "20261101-000000-01.json").write_text(json.dumps(old), encoding="utf-8")
    [record] = load_all(lay)
    assert (record.submission, record.modules, record.max_turns) == ("", (), 32)
    assert (record.level, record.submitted_by) == ("", "")
