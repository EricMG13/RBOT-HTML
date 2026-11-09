"""Drop handling: layout, readiness, claim, check, reject."""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

from deploy_workflow.inbox.drops import (
    PATHWAYS,
    DropRejected,
    Layout,
    ReadyTracker,
    candidates,
    check,
    claim,
    ensure_layout,
    reject,
    signature,
    unlocked,
)

_BASE = json.loads(Path("cases/context/research-minimal.json").read_text(encoding="utf-8"))


def ctx(pathway: str = "credit_snapshot") -> bytes:
    body = json.loads(json.dumps(_BASE))
    body["run"]["pathway"] = pathway
    return json.dumps(body).encode()


CTX_SNAPSHOT = ctx("credit_snapshot")


def make(parent: Path, files: dict[str, bytes], name: str = "acme") -> Path:
    folder = parent / name
    for rel, data in files.items():
        target = folder / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return folder


def drop(layout: Layout, pathway: str, name: str, files: dict[str, bytes]) -> Path:
    return make(layout.inbox / pathway, files, name)


@pytest.fixture
def layout() -> Iterator[Layout]:
    # pytest's tmp_path is longer than the 80-character root limit on macOS.
    with tempfile.TemporaryDirectory(prefix="ib", dir="/tmp") as short:
        yield ensure_layout(Path(short))


def test_layout_creates_every_folder(layout):
    for folder in (layout.inbox, layout.failed, layout.issuers, layout.runs, layout.drops):
        assert folder.is_dir()
    assert layout.state.is_dir() and layout.logs.is_dir()
    assert layout.engine == layout.root / "_engine"
    for pathway in PATHWAYS:
        assert (layout.inbox / pathway).is_dir()


def test_layout_refuses_a_long_root(tmp_path):
    with pytest.raises(ValueError):
        ensure_layout(tmp_path / ("x" * 90))


def test_not_ready_until_unchanged_for_the_settle_time(layout):
    now = [0.0]
    tracker = ReadyTracker(120, lambda: now[0])
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    assert tracker.ready(entry) is False
    now[0] = 119
    assert tracker.ready(entry) is False
    (entry / "b.pdf").write_bytes(b"2")  # the copy is still arriving
    now[0] = 200
    assert tracker.ready(entry) is False
    now[0] = 320
    assert tracker.ready(entry) is True


def test_old_file_times_do_not_make_a_fresh_drop_ready(layout):
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    os.utime(entry / "a.pdf", (0, 0))
    assert ReadyTracker(120, lambda: 0.0).ready(entry) is False


def test_a_vanished_entry_is_not_ready(layout):
    assert ReadyTracker(0, lambda: 0.0).ready(layout.inbox / "credit_snapshot" / "gone") is False


def test_signature_rows(layout):
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"12", "sub/b.txt": b"3"})
    rows = signature(entry)
    assert [(r[0], r[1]) for r in rows] == [("a.pdf", 2), ("sub/b.txt", 1)]
    single = layout.inbox / "one.pdf"
    single.write_bytes(b"xyz")
    assert [(r[0], r[1]) for r in signature(single)] == [("one.pdf", 3)]


def test_unlocked_for_normal_and_read_only_files(tmp_path):
    plain = tmp_path / "a.pdf"
    plain.write_bytes(b"1")
    assert unlocked(plain) is True
    plain.chmod(0o444)
    assert unlocked(plain) is True


def test_claim_moves_once(layout):
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    moved = claim(layout, entry, "20261109-134102-01")
    assert moved == layout.drops / "20261109-134102-01" and not entry.exists()
    assert claim(layout, entry, "20261109-134102-02") is None


def test_candidates_lists_entries_and_strays(layout):
    a = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    (layout.inbox / "credit_snapshot" / "_template").mkdir()
    stray = layout.inbox / "loose.pdf"
    stray.write_bytes(b"1")
    got = candidates(layout)
    assert ("credit_snapshot", a) in got
    assert ("", stray) in got
    assert all(path.name not in ("_template", "failed") for _, path in got)
    assert all(path.name not in PATHWAYS for _, path in got)


def test_a_symlink_in_the_inbox_is_a_stray_to_reject(layout, tmp_path):
    outside = make(tmp_path / "outside", {"context.json": CTX_SNAPSHOT, "a.pdf": b"1"})
    link = layout.inbox / "credit_snapshot" / "linked"
    link.symlink_to(outside, target_is_directory=True)
    assert ("credit_snapshot", link) in candidates(layout)
    with pytest.raises(DropRejected, match="not a folder"):
        check(link, "credit_snapshot")
    assert signature(link) == ()
    moved = claim(layout, link, "c1")
    assert moved is not None and moved.is_symlink() and outside.is_dir()
    assert (outside / "a.pdf").exists()


def test_a_symlinked_file_inside_a_drop_is_not_a_source(tmp_path):
    secret = tmp_path / "secret.pdf"
    secret.write_bytes(b"s")
    folder = make(tmp_path, {"context.json": CTX_SNAPSHOT, "a.pdf": b"1"})
    (folder / "link.pdf").symlink_to(secret)
    assert check(folder, "credit_snapshot").files == ("a.pdf",)


def reject_case(tmp_path: Path, files: dict[str, bytes], pathway: str, reason: str) -> None:
    folder = make(tmp_path, files)
    with pytest.raises(DropRejected, match=re.escape(reason)):
        check(folder, pathway)


@pytest.mark.parametrize(
    ("files", "pathway", "reason"),
    [
        ({"a.pdf": b"1"}, "credit_snapshot", "no context file"),
        (
            {"c1.json": CTX_SNAPSHOT, "c2.json": CTX_SNAPSHOT, "a.pdf": b"1"},
            "credit_snapshot",
            "more than one context file: c1.json, c2.json",
        ),
        (
            {"context.json": CTX_SNAPSHOT, "a.pdf": b"1"},
            "earnings_update",
            "context names pathway credit_snapshot, dropped in earnings_update",
        ),
        (
            {"context.json": CTX_SNAPSHOT, "~$a.xlsx": b"1", "_notes.pdf": b"1", "x.zip": b"1"},
            "credit_snapshot",
            "no source file the launcher can read",
        ),
        (
            {"context.json": CTX_SNAPSHOT, "a.pdf": b"1"},
            "",
            "not inside a pathway folder",
        ),
        (
            {"context.json": b'{"schema": "context/1"}', "a.pdf": b"1"},
            "credit_snapshot",
            "context file: ",
        ),
    ],
)
def test_check_rejects_with_the_reason(tmp_path, files, pathway, reason):
    reject_case(tmp_path, files, pathway, reason)


def test_check_rejects_a_file(tmp_path):
    f = tmp_path / "a.pdf"
    f.write_bytes(b"1")
    with pytest.raises(DropRejected, match="not a folder"):
        check(f, "credit_snapshot")


def test_context_may_have_any_name_and_other_json_is_a_source(tmp_path):
    checked = check(
        make(tmp_path, {"Acme ctx.json": CTX_SNAPSHOT, "data.json": b"{}", "a.pdf": b"1"}),
        "credit_snapshot",
    )
    assert checked.context.name == "Acme ctx.json" and checked.files == ("a.pdf", "data.json")
    assert checked.run.run.pathway == "credit_snapshot"


def test_hidden_parts_are_not_sources(tmp_path):
    folder = make(tmp_path, {"context.json": CTX_SNAPSHOT, ".h/a.pdf": b"1", "ok/b.pdf": b"1"})
    assert check(folder, "credit_snapshot").files == ("ok/b.pdf",)


def make_drop(layout: Layout, tag: str) -> Path:
    return make(layout.inbox / "credit_snapshot", {"a.pdf": tag.encode()}, f"drop-{tag}")


def test_reject_keeps_two_drops_with_one_name_apart(layout):
    now = datetime(2026, 11, 9, 13, 41, 2)
    first = reject(layout, make_drop(layout, "a"), "acme", "no context file", now)
    second = reject(layout, make_drop(layout, "b"), "acme", "no context file", now)
    assert first.name == "2026-11-09 134102 acme" and second.name == "2026-11-09 134102 acme (2)"
    assert "no context file" in (first / "WHY.txt").read_text(encoding="utf-8")
    assert (first / "a.pdf").exists() and first.parent == layout.failed


def test_reject_a_stray_file(layout):
    stray = layout.inbox / "loose.pdf"
    stray.write_bytes(b"1")
    dest = reject(layout, stray, "loose.pdf", "not a folder", datetime(2026, 11, 9, 1, 2, 3))
    assert dest.is_dir() and (dest / "loose.pdf").exists() and (dest / "WHY.txt").exists()
