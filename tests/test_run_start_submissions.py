"""Submissions: uploads, limits, the offline summary and the digest an approval is bound to."""

from __future__ import annotations

import io
import json
import os
import tempfile
import threading
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from test_cpos_launch import context_file, issuer_folder

from deploy_workflow.inbox.drops import Layout, ensure_layout
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
    sid, _ = upload_issuer(layout, tmp_path)
    got = reading(layout, sid)
    expected = read_documents(files_folder(layout, sid))
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


def test_concurrent_uploads_hold_the_count_limit(layout, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_FILES", 3)
    sid = new(layout)
    outcomes: list[str] = []

    def work(i: int) -> None:
        try:
            put(layout, sid, f"f{i}.txt")
            outcomes.append("ok")
        except Refused:
            outcomes.append("refused")

    threads = [threading.Thread(target=work, args=(i,)) for i in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert outcomes.count("ok") == 3
    assert len(list(files_folder(layout, sid).iterdir())) == 3


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
