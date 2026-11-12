"""Submissions: uploads, limits, the offline summary and the digest an approval is bound to."""

from __future__ import annotations

import io
import json
import logging
import os
import shutil
import tempfile
import threading
import time
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from test_cpos_launch import context_file, issuer_folder

from deploy_workflow.inbox.layout import Layout, ensure_layout
from deploy_workflow.owners.cpos_launch import prepare, read_documents
from deploy_workflow.run_start import submissions
from deploy_workflow.run_start.submissions import (
    STALE_SECONDS,
    Answers,
    Refused,
    add_file,
    digest,
    files_folder,
    new,
    reading,
    remove_file,
    summary,
    sweep,
)


@pytest.fixture
def layout() -> Iterator[Layout]:
    # pytest's tmp_path is longer than the 80-character root limit on macOS.
    with tempfile.TemporaryDirectory(prefix="ib", dir="/tmp") as short:
        yield ensure_layout(Path(short))


def answers_for(tmp_path: Path, **change: object) -> Answers:
    context = json.loads(context_file(tmp_path).read_text())
    base: dict[str, object] = {
        "context": context,
        "modules": [],
        "max_turns": 32,
        "level": "basic",
        "submitted_by": "analyst",
    }
    base.update(change)
    return base  # type: ignore[return-value]


def upload_issuer(layout: Layout, tmp_path: Path) -> tuple[str, Path]:
    sid = new(layout)
    source = issuer_folder(tmp_path)
    for path in sorted(source.rglob("*")):
        if path.is_file():
            rel = path.relative_to(source).as_posix()
            data = path.read_bytes()
            add_file(layout, sid, rel, io.BytesIO(data), len(data))
    return sid, source


def put(layout: Layout, sid: str, name: str, data: bytes = b"abc") -> str:
    return add_file(layout, sid, name, io.BytesIO(data), len(data))


def test_an_uploaded_folder_is_read_as_the_launcher_reads_it(layout, tmp_path):
    sid, source = upload_issuer(layout, tmp_path)
    got = reading(layout, sid)
    expected = read_documents(source)
    assert got["error"] == ""
    assert got["documents"] == list(expected.documents) and got["documents"]
    assert got["ignored"] == list(expected.ignored)


def test_a_new_submission_is_32_hex_and_other_ids_are_refused(layout):
    sid = new(layout)
    assert len(sid) == 32 and int(sid, 16) >= 0
    assert files_folder(layout, sid) == layout.uploads / sid / "files"
    for bad in ("../" + sid, sid.upper(), sid[:-1], "0" * 32, ""):
        with pytest.raises(Refused):
            files_folder(layout, bad)


def test_a_cut_off_upload_leaves_nothing(layout):
    sid = new(layout)
    with pytest.raises(Refused):
        add_file(layout, sid, "a.pdf", io.BytesIO(b"abc"), 10)
    assert list(files_folder(layout, sid).iterdir()) == []
    assert [p.name for p in (layout.uploads / sid).iterdir()] == ["files"]


def test_only_length_bytes_are_read(layout):
    sid = new(layout)
    body = io.BytesIO(b"abcdef")
    put_name = add_file(layout, sid, "a.txt", body, 3)
    assert (files_folder(layout, sid) / put_name).read_bytes() == b"abc"
    assert body.tell() == 3


@pytest.mark.parametrize(
    "name",
    ["../x.pdf", "/etc/x.pdf", "a/../../x.pdf", "C:\\x.pdf", "", "context.json", ".", "a//b.pdf"],
)
def test_an_unsafe_name_is_refused(layout, name):
    sid = new(layout)
    with pytest.raises(Refused):
        put(layout, sid, name)
    assert not any(files_folder(layout, sid).rglob("*"))
    assert not (layout.uploads / sid / "x.pdf").exists()


def test_a_nested_context_json_is_an_ordinary_file(layout):
    sid = new(layout)
    assert put(layout, sid, "sub/context.json") == "sub/context.json"


def test_a_reserved_and_a_non_ascii_name_are_stored_safely(layout):
    sid = new(layout)
    assert put(layout, sid, "CON.pdf") == "_CON.pdf"
    assert put(layout, sid, "Geschäftsbericht 2024.pdf") == "Geschäftsbericht 2024.pdf"
    assert put(layout, sid, "x\\y/z.txt") == "x/y/z.txt"
    assert (files_folder(layout, sid) / "x/y/z.txt").is_file()


def test_two_names_that_become_one_keep_the_later_file(layout):
    sid = new(layout)
    assert put(layout, sid, "a:b.pdf", b"first") == "a b.pdf"
    assert put(layout, sid, "a b.pdf", b"second") == "a b.pdf"
    folder = files_folder(layout, sid)
    assert [p.name for p in folder.iterdir()] == ["a b.pdf"]
    assert (folder / "a b.pdf").read_bytes() == b"second"


def test_a_file_cannot_become_a_folder_or_the_reverse(layout):
    sid = new(layout)
    put(layout, sid, "a")
    with pytest.raises(Refused):
        put(layout, sid, "a/b.txt")
    put(layout, sid, "d/x.txt")
    with pytest.raises(Refused):
        put(layout, sid, "d")
    assert sorted(
        p.relative_to(files_folder(layout, sid)).as_posix()
        for p in files_folder(layout, sid).rglob("*")
    ) == ["a", "d", "d/x.txt"]


def test_the_file_count_size_and_total_limits_refuse(layout, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_FILES", 2)
    monkeypatch.setattr(submissions, "MAX_FILE", 5)
    monkeypatch.setattr(submissions, "MAX_TOTAL", 8)
    sid = new(layout)
    put(layout, sid, "a.txt", b"12345")
    with pytest.raises(Refused):  # one file over the size limit
        put(layout, sid, "big.txt", b"123456")
    with pytest.raises(Refused):  # total would be 10 > 8
        put(layout, sid, "b.txt", b"12345")
    put(layout, sid, "b.txt", b"123")  # exactly 8
    with pytest.raises(Refused):  # a third file
        put(layout, sid, "c.txt", b"1")
    put(layout, sid, "a.txt", b"1")  # replacing frees the old size and is not a new file
    assert sorted(p.name for p in files_folder(layout, sid).iterdir()) == ["a.txt", "b.txt"]
    assert not [p for p in (layout.uploads / sid).iterdir() if p.name != "files"]


class Meeting(io.RawIOBase):
    """A body whose read waits for the other uploads, so the reservations overlap."""

    def __init__(self, data: bytes, barrier: threading.Barrier) -> None:
        self.data, self.barrier = data, barrier

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        self.barrier.wait()
        out, self.data = self.data, b""
        return out


def test_concurrent_uploads_hold_the_count_limit(layout, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_FILES", 2)
    sid = new(layout)
    barrier = threading.Barrier(2, timeout=10)  # the two admitted uploads are in flight together
    real_stored = submissions._stored

    def slow(root, **kwargs):  # widens the check-then-reserve window: only the lock closes it
        found = real_stored(root, **kwargs)
        time.sleep(0.05)
        return found

    monkeypatch.setattr(submissions, "_stored", slow)
    outcomes: list[str] = []

    def work(i: int) -> None:
        try:
            add_file(layout, sid, f"f{i}.txt", Meeting(b"abc", barrier), 3)
            outcomes.append("ok")
        except Refused:
            outcomes.append("refused")
        except threading.BrokenBarrierError:  # a third admitted upload: a failure, not a refusal
            outcomes.append("broken barrier")

    threads = [threading.Thread(target=work, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(outcomes) == 8  # every worker reported, and none raised
    assert sorted(set(outcomes)) == ["ok", "refused"]
    assert outcomes.count("ok") == 2
    assert len(list(files_folder(layout, sid).iterdir())) == 2


def test_a_file_can_be_removed_and_a_bad_name_is_refused(layout):
    sid = new(layout)
    put(layout, sid, "d/x.txt")
    remove_file(layout, sid, "d/x.txt")
    assert list(files_folder(layout, sid).iterdir()) == []
    for bad in ("d/x.txt", "../files", ""):
        with pytest.raises(Refused):
            remove_file(layout, sid, bad)


def test_the_summary_is_the_launchers_forecast(layout, tmp_path):
    sid, source = upload_issuer(layout, tmp_path)
    answers = answers_for(tmp_path)
    s = summary(layout, sid, answers, config="sol-medium", cap=Decimal(20))
    ref = tmp_path / "ref"
    ref.mkdir()
    expected = prepare(context_file(tmp_path), source, ref / "out", config="sol-medium", cap="20")
    assert s["error"] == ""
    assert s["items"] == list(expected.expectations) and s["items"]
    assert s["modules"] == list(expected.ordered)
    assert s["omitted"] == list(expected.omitted)
    assert s["ignored"] == list(expected.ignored)
    assert s["digest"] == digest(layout, sid, answers)


def test_the_summary_checks_the_cap_as_the_standing_ruling_will_run_it(
    layout, tmp_path, monkeypatch
):
    sid, _ = upload_issuer(layout, tmp_path)
    seen = []

    def watching(*args, **kwargs):
        seen.append(kwargs["web_search"])
        return prepare(*args, **kwargs)

    monkeypatch.setattr(submissions, "prepare", watching)
    assert (
        summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))["error"]
        == ""
    )
    assert seen == [True]  # the standing ruling lists web-search


def test_the_summary_is_for_the_module_list_the_digest_covers(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    s = summary(
        layout,
        sid,
        answers_for(tmp_path, modules=["CP-0", "CP-1"]),
        config="sol-medium",
        cap=Decimal(20),
    )
    assert s["error"] == ""
    assert "CP-5" not in s["modules"] and "CP-1" in s["modules"]


def test_a_refused_context_or_folder_comes_back_as_the_error_with_no_digest(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    bad = answers_for(tmp_path)
    bad["context"] = {"schema": "nonsense"}
    s = summary(layout, sid, bad, config="sol-medium", cap=Decimal(20))
    assert s["error"] and "digest" not in s
    empty = new(layout)
    s = summary(layout, empty, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))
    assert s["error"] and "digest" not in s


def test_the_digest_changes_with_a_file_the_context_the_modules_or_the_turns_only(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    base = answers_for(tmp_path)
    first = digest(layout, sid, base)
    assert len(first) == 64
    assert digest(layout, sid, answers_for(tmp_path, level="advanced", submitted_by="x")) == first
    assert digest(layout, sid, answers_for(tmp_path, max_turns=40)) != first
    assert digest(layout, sid, answers_for(tmp_path, modules=["CP-0"])) != first
    changed = answers_for(tmp_path)
    changed["context"]["identity"]["issuer_name"] = "Other"
    assert digest(layout, sid, changed) != first
    put(layout, sid, "annual.txt", b"Net sales were 101.")
    after_edit = digest(layout, sid, base)
    assert after_edit != first
    put(layout, sid, "extra.txt")
    assert digest(layout, sid, base) != after_edit
    remove_file(layout, sid, "extra.txt")
    assert digest(layout, sid, base) == after_edit
    put(layout, sid, "same-bytes-a.txt", b"same")
    before_rename = digest(layout, sid, base)
    remove_file(layout, sid, "same-bytes-a.txt")
    put(layout, sid, "same-bytes-b.txt", b"same")  # the same bytes under another name
    assert digest(layout, sid, base) != before_rename


def test_the_summary_leaves_no_run_folder_and_no_temporary_file(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    before = sorted(p.relative_to(layout.root).as_posix() for p in layout.root.rglob("*"))
    assert (
        summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))["error"]
        == ""
    )
    bad = answers_for(tmp_path)
    bad["context"] = {}
    assert summary(layout, sid, bad, config="sol-medium", cap=Decimal(20))["error"]
    after = sorted(p.relative_to(layout.root).as_posix() for p in layout.root.rglob("*"))
    assert after == before


def test_stale_uploads_are_swept_and_fresh_ones_kept(layout):
    old, fresh = new(layout), new(layout)
    put(layout, old, "a.txt")
    now = (layout.uploads / old).stat().st_mtime + STALE_SECONDS + 10
    os.utime(layout.uploads / fresh, (now, now))
    stray = layout.uploads / "not-a-submission"
    stray.mkdir()
    sweep(layout, now)
    assert not (layout.uploads / old).exists()
    assert (layout.uploads / fresh).is_dir()
    assert stray.is_dir()


# ---- review round 1 ----


def test_a_file_landing_while_the_summary_is_made_gives_no_digest(layout, tmp_path, monkeypatch):
    sid, _ = upload_issuer(layout, tmp_path)
    real = submissions.prepare

    def racing(*args, **kwargs):
        out = real(*args, **kwargs)
        put(layout, sid, "late.txt", b"late")
        return out

    monkeypatch.setattr(submissions, "prepare", racing)
    got = summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))
    assert "digest" not in got
    assert got["error"] == (
        "the documents changed while the summary was being made; open the summary again"
    )


@pytest.mark.parametrize(
    "change",
    [
        {"modules": ["NOPE"]},
        {"modules": [1]},
        {"modules": None},
        {"modules": ["CP-0"] * 41},
        {"modules": ["x" * 13]},
        {"context": [1]},
        {"max_turns": "32"},
        {"max_turns": True},
        {"max_turns": 0},
        {"max_turns": 65},
        {"level": "expert"},
        {"submitted_by": 5},
        {"submitted_by": "x" * 81},
    ],
)
def test_hostile_answers_are_refusals_not_exceptions(layout, tmp_path, change):
    sid, _ = upload_issuer(layout, tmp_path)
    answers = answers_for(tmp_path, **change)
    got = summary(layout, sid, answers, config="sol-medium", cap=Decimal(20))
    assert got["error"] and "digest" not in got
    if change != {"modules": ["NOPE"]}:  # a well-formed name the launcher refuses, not the shape
        with pytest.raises(Refused):
            digest(layout, sid, answers)
    assert list(layout.state.iterdir()) == []


def test_answers_need_exactly_the_five_keys(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    answers = answers_for(tmp_path)
    extra = {**answers, "more": 1}
    missing = {k: v for k, v in answers.items() if k != "level"}
    for bad in (extra, missing, "x", None):
        with pytest.raises(Refused):
            digest(layout, sid, bad)  # type: ignore[arg-type]


def test_a_lone_surrogate_in_the_context_is_a_refusal(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    answers = answers_for(tmp_path)
    answers["context"]["identity"]["issuer_name"] = "\ud800"
    with pytest.raises(Refused):
        submissions.context_bytes(answers)
    got = summary(layout, sid, answers, config="sol-medium", cap=Decimal(20))
    assert got["error"] and "digest" not in got
    with pytest.raises(Refused):
        digest(layout, sid, answers)


def test_there_is_a_ceiling_on_unfinished_submissions(layout, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_OPEN", 3)
    for _ in range(3):
        new(layout)
    with pytest.raises(Refused, match="too many unfinished submissions"):
        new(layout)
    assert len(list(layout.uploads.iterdir())) == 3


def test_a_sealed_submission_is_not_an_open_one(layout, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_OPEN", 1)
    sid = new(layout)
    submissions.seal(layout, sid)
    assert new(layout)


def test_the_store_total_is_held_across_submissions(layout, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_STORE", 10)
    one, two = new(layout), new(layout)
    put(layout, one, "a.txt", b"123456")
    with pytest.raises(Refused, match="stor"):
        put(layout, two, "b.txt", b"12345")  # 11 > 10 over both
    put(layout, two, "b.txt", b"1234")
    put(layout, one, "a.txt", b"1")  # a replacement frees the old bytes
    assert not [p for p in (layout.uploads / two).iterdir() if p.name != "files"]


def test_a_refused_upload_leaves_no_reservation_entry(layout, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_TOTAL", 3)
    sid = new(layout)
    with pytest.raises(Refused):
        put(layout, sid, "a.txt", b"abcd")
    assert sid not in submissions._PENDING


def test_summaries_run_one_at_a_time(layout, tmp_path, monkeypatch):
    sid, _ = upload_issuer(layout, tmp_path)
    real = submissions.prepare
    state = {"now": 0, "peak": 0}
    guard = threading.Lock()

    def counting(*args, **kwargs):
        with guard:
            state["now"] += 1
            state["peak"] = max(state["peak"], state["now"])
        try:
            return real(*args, **kwargs)
        finally:
            with guard:
                state["now"] -= 1

    monkeypatch.setattr(submissions, "prepare", counting)
    answers = answers_for(tmp_path)
    threads = [
        threading.Thread(
            target=summary,
            args=(layout, sid, answers),
            kwargs={"config": "sol-medium", "cap": Decimal(20)},
        )
        for _ in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert state["peak"] == 1


def _failing_rmtree(path, *args, **kwargs):
    raise PermissionError(13, "held open", str(path))


def test_a_failed_summary_cleanup_is_logged_and_the_result_stands(
    layout, tmp_path, monkeypatch, caplog
):
    sid, _ = upload_issuer(layout, tmp_path)
    monkeypatch.setattr(submissions.shutil, "rmtree", _failing_rmtree)
    with caplog.at_level(logging.WARNING, logger=submissions.log.name):
        got = summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))
    assert got["error"] == "" and got["digest"]
    left = [p for p in layout.state.iterdir() if p.name.startswith("summary-")]
    assert len(left) == 1
    assert any(left[0].name in r.getMessage() for r in caplog.records)
    monkeypatch.undo()
    old = left[0].stat().st_mtime - STALE_SECONDS - 10
    os.utime(left[0], (old, old))
    sweep(layout, left[0].stat().st_mtime + STALE_SECONDS + 100)
    assert not left[0].exists()  # the sweep retries a leftover


def test_a_failed_sweep_removal_is_logged_and_the_sweep_goes_on(layout, monkeypatch, caplog):
    old, other = new(layout), new(layout)
    now = (layout.uploads / old).stat().st_mtime + STALE_SECONDS + 10
    monkeypatch.setattr(submissions.shutil, "rmtree", _failing_rmtree)
    with caplog.at_level(logging.WARNING, logger=submissions.log.name):
        sweep(layout, now)
    assert (layout.uploads / old).exists() and (layout.uploads / other).exists()
    assert any(old in r.getMessage() for r in caplog.records)
    assert any(other in r.getMessage() for r in caplog.records)


# seal


def test_seal_freezes_the_uploads_and_unseal_restores_them(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    answers = answers_for(tmp_path)
    before = digest(layout, sid, answers)
    sealed = submissions.seal(layout, sid)
    assert sealed == layout.uploads / sid / "sealed" and sealed.is_dir()
    assert not (layout.uploads / sid / "files").exists()
    assert files_folder(layout, sid) == sealed
    assert submissions.seal(layout, sid) == sealed  # again: the same folder
    assert digest(layout, sid, answers) == before
    assert reading(layout, sid)["documents"]
    got = summary(layout, sid, answers, config="sol-medium", cap=Decimal(20))
    assert got["error"] == "" and got["digest"] == before
    for call in (
        lambda: put(layout, sid, "new.txt"),
        lambda: remove_file(layout, sid, "annual.txt"),
    ):
        with pytest.raises(Refused, match="has been submitted"):
            call()
    submissions.unseal(layout, sid)
    assert files_folder(layout, sid) == layout.uploads / sid / "files"
    assert digest(layout, sid, answers) == before
    put(layout, sid, "new.txt")
    submissions.unseal(layout, sid)  # not sealed: nothing happens


def test_seal_is_refused_while_an_upload_is_in_flight(layout):
    sid = new(layout)
    started, release = threading.Event(), threading.Event()

    class Held(io.RawIOBase):
        def readable(self) -> bool:
            return True

        def read(self, size: int = -1) -> bytes:
            started.set()
            assert release.wait(10)
            return b"abc"

    thread = threading.Thread(target=lambda: add_file(layout, sid, "a.txt", Held(), 3))
    thread.start()
    assert started.wait(10)
    with pytest.raises(Refused, match="upload is still in progress"):
        submissions.seal(layout, sid)
    release.set()
    thread.join()
    assert (files_folder(layout, sid) / "a.txt").read_bytes() == b"abc"
    submissions.seal(layout, sid)


def test_an_upload_that_meets_the_seal_is_refused_and_leaves_nothing(layout, monkeypatch):
    sid = new(layout)
    real = submissions._parts

    def sealing(name):
        submissions.seal(layout, sid)  # the seal lands after the upload began
        return real(name)

    monkeypatch.setattr(submissions, "_parts", sealing)
    with pytest.raises(Refused, match="has been submitted"):
        put(layout, sid, "late.txt")
    assert list((layout.uploads / sid / "sealed").iterdir()) == []
    assert [p.name for p in (layout.uploads / sid).iterdir()] == ["sealed"]
    assert sid not in submissions._PENDING


# ride-alongs


def test_a_link_inside_the_files_folder_is_not_followed(layout, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "y.pdf").write_bytes(b"victim")
    (outside / "secret.txt").write_bytes(b"secret")
    sid = new(layout)
    files = files_folder(layout, sid)
    os.symlink(outside, files / "sub")
    with pytest.raises(Refused):
        put(layout, sid, "sub/x.pdf")
    with pytest.raises(Refused):
        remove_file(layout, sid, "sub/y.pdf")
    assert sorted(p.name for p in outside.iterdir()) == ["secret.txt", "y.pdf"]
    os.unlink(files / "sub")
    os.symlink(outside / "secret.txt", files / "leak.txt")
    with pytest.raises(Refused):
        digest(layout, sid, answers_for(tmp_path))
    got = reading(layout, sid)
    assert got["error"] and got["documents"] == []


def test_a_files_folder_that_is_a_link_is_an_unknown_submission(layout, tmp_path):
    sid = new(layout)
    real = layout.uploads / sid / "files"
    real.rmdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    os.symlink(elsewhere, real)
    with pytest.raises(Refused):
        files_folder(layout, sid)
    with pytest.raises(Refused):
        put(layout, sid, "a.txt")


def test_a_name_with_a_lone_surrogate_is_refused_and_leaves_nothing(layout):
    sid = new(layout)
    for name in ("\ud800.pdf", "\udc80.pdf", "d\ud800/x.pdf"):
        with pytest.raises(Refused):
            put(layout, sid, name)
        with pytest.raises(Refused):
            remove_file(layout, sid, name)
    assert list(files_folder(layout, sid).iterdir()) == []
    assert [p.name for p in (layout.uploads / sid).iterdir()] == ["files"]


def test_a_remove_cannot_run_inside_an_upload_into_the_same_folder(layout, monkeypatch):
    sid = new(layout)
    put(layout, sid, "d/one.pdf")
    real = os.replace
    held: list[threading.Thread] = []

    def remover() -> None:
        remove_file(layout, sid, "d/one.pdf")

    def slow_replace(src, dst):
        if str(dst).endswith("two.pdf"):
            thread = threading.Thread(target=remover)
            thread.start()
            thread.join(0.3)
            assert thread.is_alive()  # the lock holds the remove off until the upload is placed
            held.append(thread)
        return real(src, dst)

    monkeypatch.setattr(submissions.os, "replace", slow_replace)
    put(layout, sid, "d/two.pdf")
    held[0].join(10)
    assert sorted(p.name for p in (files_folder(layout, sid) / "d").iterdir()) == ["two.pdf"]


def test_two_removes_of_one_name_give_one_refusal(layout):
    sid = new(layout)
    put(layout, sid, "x.pdf")
    results: list[str] = []

    def work() -> None:
        try:
            remove_file(layout, sid, "x.pdf")
            results.append("ok")
        except Refused:
            results.append("refused")

    threads = [threading.Thread(target=work) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["ok"] + ["refused"] * 5


def test_the_sweep_leaves_a_submission_with_an_upload_in_flight(layout):
    sid = new(layout)
    started, release = threading.Event(), threading.Event()

    class Held(io.RawIOBase):
        def readable(self) -> bool:
            return True

        def read(self, size: int = -1) -> bytes:
            started.set()
            assert release.wait(10)
            return b"abc"

    result: list[object] = []

    def up() -> None:
        try:
            result.append(add_file(layout, sid, "big.pdf", Held(), 3))
        except (Refused, OSError) as error:
            result.append(error)

    thread = threading.Thread(target=up)
    thread.start()
    assert started.wait(10)
    now = (layout.uploads / sid).stat().st_mtime + STALE_SECONDS + 10
    sweep(layout, now)
    assert (layout.uploads / sid).is_dir()
    release.set()
    thread.join()
    assert result == ["big.pdf"]


def test_a_summary_records_the_digest_it_returns_and_an_error_clears_it(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    assert submissions.issued(layout, sid) == ""
    first = summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))
    assert first["error"] == ""
    assert submissions.issued(layout, sid) == first["digest"]
    second = summary(
        layout, sid, answers_for(tmp_path, max_turns=8), config="sol-medium", cap=Decimal(20)
    )
    assert second["digest"] != first["digest"]
    assert submissions.issued(layout, sid) == second["digest"]  # replaced, not appended
    bad = answers_for(tmp_path)
    bad["context"] = {"schema": "nonsense"}
    assert summary(layout, sid, bad, config="sol-medium", cap=Decimal(20))["error"]
    assert submissions.issued(layout, sid) == ""
    assert not (layout.uploads / sid / "issued").exists()


def test_an_issued_digest_is_not_part_of_the_files_and_survives_the_seal(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    got = summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))
    assert "issued" not in os.listdir(files_folder(layout, sid))
    submissions.seal(layout, sid)
    assert submissions.issued(layout, sid) == got["digest"]
    assert digest(layout, sid, answers_for(tmp_path)) == got["digest"]


def test_issued_is_refused_for_an_unknown_submission(layout):
    with pytest.raises(Refused):
        submissions.issued(layout, "0" * 32)


# ---- review round 2 ----


def test_what_a_submitted_submission_leaves_behind_is_not_an_open_one(layout, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_OPEN", 1)
    sid = new(layout)
    submissions.seal(layout, sid)
    os.rename(layout.uploads / sid / "sealed", layout.drops / "run")
    (layout.uploads / sid / "issued").write_text("0" * 64 + "\n")
    assert submissions._open_folders(layout) == []
    assert new(layout)


def test_release_removes_the_leftover_folder_but_never_live_uploads(layout):
    done, live = new(layout), new(layout)
    submissions.seal(layout, done)
    os.rename(layout.uploads / done / "sealed", layout.drops / "run")
    (layout.uploads / done / "issued").write_text("x\n")
    submissions.release(layout, live)  # still has files/: kept
    submissions.release(layout, done)
    submissions.release(layout, "../x")  # not an id: nothing happens
    assert (layout.uploads / live / "files").is_dir()
    assert not (layout.uploads / done).exists()


def test_a_failed_release_is_logged_and_does_not_raise(layout, monkeypatch, caplog):
    sid = new(layout)
    os.rmdir(layout.uploads / sid / "files")
    monkeypatch.setattr(submissions.shutil, "rmtree", _failing_rmtree)
    with caplog.at_level(logging.WARNING, logger=submissions.__name__):
        submissions.release(layout, sid)
    assert "could not remove" in caplog.text


def test_a_sealed_or_files_link_is_an_unknown_submission(layout, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "a.txt").write_bytes(b"Net sales were 100.")
    sid = new(layout)
    os.symlink(outside, layout.uploads / sid / "sealed")
    for call in (
        lambda: files_folder(layout, sid),
        lambda: submissions.seal(layout, sid),
        lambda: digest(layout, sid, answers_for(tmp_path)),
        lambda: reading(layout, sid),
        lambda: summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20)),
    ):
        with pytest.raises(Refused, match="unknown submission"):
            call()
    assert not submissions._is_sealed(layout.uploads / sid)
    assert (outside / "a.txt").is_file() and not (outside / "sealed").exists()


def test_a_digest_taken_while_a_seal_renames_the_folder_still_covers_the_files(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    answers = answers_for(tmp_path)
    expected = digest(layout, sid, answers)
    real = submissions.files_folder
    calls = []

    def stale(lay, x):
        root = real(lay, x)
        if not calls:  # the first look resolves files/, then the seal lands before the walk
            calls.append(1)
            submissions.seal(lay, x)
        return root

    submissions.files_folder = stale
    try:
        got = digest(layout, sid, answers)
    finally:
        submissions.files_folder = real
    assert got == expected


def test_a_file_that_vanishes_while_the_summary_reads_it_is_the_changed_error(
    layout, tmp_path, monkeypatch
):
    sid, _ = upload_issuer(layout, tmp_path)

    def vanishing(*args, **kwargs):
        remove_file(layout, sid, "annual.txt")
        raise FileNotFoundError(2, "gone")

    monkeypatch.setattr(submissions, "prepare", vanishing)
    got = summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))
    assert got == {"error": submissions._CHANGED}
    assert submissions.issued(layout, sid) == ""


def test_a_summary_racing_the_removal_of_its_folder_is_refused_not_an_oserror(
    layout, tmp_path, monkeypatch
):
    """Ported from probe r2_issued_release_race.py (it imports the removed drops module)."""
    sid, _ = upload_issuer(layout, tmp_path)
    real_folder = submissions._folder
    real_summarise = submissions._summarise
    armed = []

    def summarise(*args, **kwargs):
        got = real_summarise(*args, **kwargs)
        armed.append(True)
        return got

    def folder(lay, name):
        got = real_folder(lay, name)
        if armed:  # the scheduler's move and release land between the check and the lock
            shutil.rmtree(got)
        return got

    monkeypatch.setattr(submissions, "_summarise", summarise)
    monkeypatch.setattr(submissions, "_folder", folder)
    with pytest.raises(Refused, match="unknown submission"):
        summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))


def test_an_oserror_while_the_summary_reads_is_logged_not_passed_off_as_a_change(
    layout, tmp_path, caplog
):
    """Ported from probe r2_summary_permission.py (it imports the removed drops module)."""
    sid, _ = upload_issuer(layout, tmp_path)
    victim = next(p for p in files_folder(layout, sid).rglob("*") if p.is_file())
    victim.chmod(0)
    try:
        with caplog.at_level(logging.WARNING, logger=submissions.__name__):
            got = summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))
    finally:
        victim.chmod(0o600)
    assert got == {"error": submissions._CHANGED}
    assert "PermissionError" in caplog.text or "Permission denied" in caplog.text


def test_a_failed_temporary_unlink_releases_the_reservation_and_refuses(
    layout, monkeypatch, caplog
):
    sid = new(layout)
    real = Path.unlink

    def failing(self, missing_ok=False):
        if self.name.startswith(".part-") and self.exists():
            raise PermissionError(13, "held open", str(self))
        return real(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", failing)
    with caplog.at_level(logging.WARNING, logger=submissions.__name__), pytest.raises(Refused):
        add_file(layout, sid, "a.txt", io.BytesIO(b"ab"), 3)  # cut short: the temp file stays
    assert "temporary upload" in caplog.text
    assert sid not in submissions._PENDING
    monkeypatch.undo()
    submissions.seal(layout, sid)  # not blocked by a leaked reservation


def test_the_servers_path_is_not_in_a_reading_or_summary_error(layout, tmp_path):
    sid = new(layout)
    put(layout, sid, "a.bin", b"\x00\x01 not a document")
    root = str(files_folder(layout, sid))
    seen = [reading(layout, sid)["error"]]
    seen.append(
        summary(layout, sid, answers_for(tmp_path), config="sol-medium", cap=Decimal(20))["error"]
    )
    assert all(seen), seen
    for text in seen:
        assert root not in text and str(layout.uploads) not in text
    assert any("the uploaded documents" in text for text in seen), seen


def test_the_digest_ignores_a_top_level_context_json_only(layout, tmp_path):
    sid, _ = upload_issuer(layout, tmp_path)
    answers = answers_for(tmp_path)
    before = digest(layout, sid, answers)
    (files_folder(layout, sid) / "context.json").write_bytes(b"{}")
    assert digest(layout, sid, answers) == before
    (files_folder(layout, sid) / "sub").mkdir()
    (files_folder(layout, sid) / "sub" / "context.json").write_bytes(b"{}")
    assert digest(layout, sid, answers) != before


def test_the_sweep_keeps_a_submission_it_is_told_to_keep(layout):
    kept, gone = new(layout), new(layout)
    now = (layout.uploads / kept).stat().st_mtime + STALE_SECONDS + 10
    sweep(layout, now, keep={kept})
    assert (layout.uploads / kept).is_dir()
    assert not (layout.uploads / gone).exists()
    sweep(layout, now)
    assert not (layout.uploads / kept).exists()


def test_an_issuer_id_over_the_limit_is_refused_by_the_summary(layout, tmp_path):
    # The folder watcher refused such an ID when it checked a drop; the summary now does.
    sid, _ = upload_issuer(layout, tmp_path)
    answers = answers_for(tmp_path)
    answers["context"]["identity"]["issuer_id"] = "a" * 41
    got = summary(layout, sid, answers, config="sol-medium", cap=Decimal(20))
    assert got["error"] == "issuer_id is 41 characters; use at most 40"
    assert "digest" not in got
    answers["context"]["identity"]["issuer_id"] = "a" * 40
    assert summary(layout, sid, answers, config="sol-medium", cap=Decimal(20))["error"] == ""
