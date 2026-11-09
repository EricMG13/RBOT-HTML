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
    write_templates,
)

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "docs/templates/context-form.html"
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


def test_a_symlinked_file_inside_a_drop_rejects_the_drop(tmp_path):
    # Round 1 (H3): the launcher follows links, so a drop holding one is refused, not trimmed.
    secret = tmp_path / "secret.pdf"
    secret.write_bytes(b"s")
    folder = make(tmp_path, {"context.json": CTX_SNAPSHOT, "a.pdf": b"1"})
    (folder / "link.pdf").symlink_to(secret)
    with pytest.raises(DropRejected, match="contains a link or special file: link.pdf"):
        check(folder, "credit_snapshot")


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


# ---- Fix round 1 -------------------------------------------------------------------------------

NOW = datetime(2026, 11, 9, 13, 41, 2)


def test_h1_reject_does_not_write_through_a_why_symlink(layout, tmp_path):
    victim = tmp_path / "records.json"
    victim.write_text("keep", encoding="utf-8")
    entry = make(layout.drops, {"a.pdf": b"1"}, "d1")
    (entry / "WHY.txt").symlink_to(victim)
    dest = reject(layout, entry, "acme", "no context file", NOW)
    assert victim.read_text(encoding="utf-8") == "keep"
    assert "no context file" in (dest / "WHY (2).txt").read_text(encoding="utf-8")


def test_h1_reject_does_not_write_through_a_why_hard_link(layout, tmp_path):
    victim = tmp_path / "report.html"
    victim.write_bytes(b"<p>filed</p>")
    entry = make(layout.drops, {"a.pdf": b"1"}, "d1")
    os.link(victim, entry / "WHY.txt")
    dest = reject(layout, entry, "acme", "no context file", NOW)
    assert victim.read_bytes() == b"<p>filed</p>"
    assert (dest / "WHY (2).txt").exists()


def test_h1_reject_with_a_folder_named_why(layout):
    entry = make(layout.drops, {"WHY.txt/x.pdf": b"1", "WHY (2).txt": b"mine"}, "d1")
    dest = reject(layout, entry, "acme", "no context file", NOW)
    assert (dest / "WHY.txt" / "x.pdf").exists()
    assert (dest / "WHY (2).txt").read_bytes() == b"mine"
    assert "no context file" in (dest / "WHY (3).txt").read_text(encoding="utf-8")


def test_h2_a_pathway_folder_that_is_a_link_is_not_listed(layout, tmp_path):
    run = make(layout.runs, {"events.jsonl": b"{}"}, "20261101-090000-01")
    (layout.inbox / "credit_snapshot").rmdir()
    (layout.inbox / "credit_snapshot").symlink_to(layout.runs, target_is_directory=True)
    assert all(path.parent != layout.inbox / "credit_snapshot" for _, path in candidates(layout))
    assert candidates(layout) == []
    assert run.exists()


def test_h2_reject_refuses_when_failed_is_a_link(layout):
    layout.failed.rmdir()
    layout.failed.symlink_to(layout.runs, target_is_directory=True)
    entry = make(layout.drops, {"a.pdf": b"1"}, "d1")
    with pytest.raises(OSError, match="failed"):
        reject(layout, entry, "acme", "no context file", NOW)
    assert entry.exists() and list(layout.runs.iterdir()) == []


def test_h3_a_link_or_special_file_rejects_the_drop(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("s", encoding="utf-8")
    folder = make(tmp_path, {"context.json": CTX_SNAPSHOT, "a.txt": b"1", "z/b.txt": b"2"})
    (folder / "z" / "notes.txt").symlink_to(secret)
    (folder / "dirlink").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(DropRejected, match="contains a link or special file: dirlink"):
        check(folder, "credit_snapshot")


def test_h4_deeply_nested_json_is_an_ordinary_source(tmp_path):
    folder = make(
        tmp_path, {"context.json": CTX_SNAPSHOT, "a.pdf": b"1", "data.json": b"[" * 200_000}
    )
    assert check(folder, "credit_snapshot").files == ("a.pdf", "data.json")


def test_h4_an_oversized_json_is_not_a_context(tmp_path, monkeypatch):
    monkeypatch.setattr("deploy_workflow.inbox.drops.MAX_BYTES", 10)
    folder = make(tmp_path, {"big.json": CTX_SNAPSHOT, "a.pdf": b"1"})
    with pytest.raises(DropRejected, match="no context file"):
        check(folder, "credit_snapshot")


def test_h4_a_lone_surrogate_in_the_reason_is_written(layout):
    entry = make(layout.drops, {"a.pdf": b"1"}, "d1")
    dest = reject(layout, entry, "acme", "context file: key \ud800 is bad", NOW)
    assert "bad" in (dest / "WHY.txt").read_text(encoding="utf-8")


def fifo_drop(layout: Layout, mode: int) -> Path:
    entry = make(layout.inbox / "credit_snapshot", {"context.json": CTX_SNAPSHOT}, "acme")
    os.mkfifo(entry / "a.pdf", mode)
    return entry


def ready_within(tracker: ReadyTracker, entry: Path) -> list[bool]:
    """Call ``ready`` on a thread so a blocking open fails the test instead of hanging it."""
    import threading

    result: list[bool] = []
    worker = threading.Thread(target=lambda: result.append(tracker.ready(entry)), daemon=True)
    worker.start()
    worker.join(5)
    assert not worker.is_alive()
    return result


@pytest.mark.parametrize("mode", [0o644, 0o444])
def test_m5_a_fifo_neither_blocks_readiness_nor_passes_check(layout, mode):
    entry = fifo_drop(layout, mode)
    now = [0.0]
    tracker = ReadyTracker(120, lambda: now[0])
    tracker.ready(entry)
    now[0] = 200.0
    assert ready_within(tracker, entry) == [True]
    with pytest.raises(DropRejected, match="contains a link or special file: a.pdf"):
        check(entry, "credit_snapshot")


def test_m6_a_redropped_folder_must_settle_again(layout):
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    now = [0.0]
    tracker = ReadyTracker(120, lambda: now[0])
    tracker.ready(entry)
    now[0] = 130.0
    assert tracker.ready(entry) is True
    now[0] = 90_000.0  # claimed and dropped again with the same rows
    assert tracker.ready(entry) is False


def test_m6_a_gone_entry_is_forgotten(layout):
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    tracker = ReadyTracker(120, lambda: 0.0)
    tracker.ready(entry)
    os.remove(entry / "a.pdf")
    entry.rmdir()
    assert tracker.ready(entry) is False
    assert entry not in tracker._seen


def test_m7_reserved_folders_match_without_regard_to_case(layout):
    drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    (layout.inbox / "Notes").mkdir()
    (layout.inbox / "Credit_Snapshot2").mkdir()
    (layout.inbox / "CREDIT_SNAPSHOT").mkdir(exist_ok=True)
    (layout.inbox / "Failed").mkdir(exist_ok=True)
    (layout.inbox / "credit_snapshot" / "_Template").mkdir()
    names = {path.name for _, path in candidates(layout)}
    assert names == {"acme", "Notes", "Credit_Snapshot2"}


def test_l8_a_missing_entry_is_never_ready_even_after_settling(layout):
    gone = layout.inbox / "credit_snapshot" / "gone"
    now = [0.0]
    tracker = ReadyTracker(120, lambda: now[0])
    tracker.ready(gone)
    now[0] = 200.0
    assert tracker.ready(gone) is False


def test_l9_a_listing_error_is_not_swallowed(layout, monkeypatch):
    entry = drop(layout, "credit_snapshot", "acme", {"sub/a.pdf": b"1"})
    real = os.scandir

    def broken(path):
        if str(path).endswith("sub"):
            raise PermissionError("denied")
        return real(path)

    monkeypatch.setattr(os, "scandir", broken)
    with pytest.raises(OSError, match="denied"):
        signature(entry)
    assert ReadyTracker(0, lambda: 0.0).ready(entry) is False


def test_l10_claim_does_not_replace_an_existing_target(layout):
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    (layout.drops / "c1").mkdir()
    assert claim(layout, entry, "c1") is None
    assert entry.exists()


def test_l11_finder_and_explorer_files_are_not_drops(layout):
    for rel in ("credit_snapshot/.DS_Store", ".DS_Store", "credit_snapshot/Thumbs.db"):
        (layout.inbox / rel).write_bytes(b"x")
    (layout.inbox / "Desktop.ini").write_bytes(b"x")
    (layout.inbox / "~$lock.xlsx").write_bytes(b"x")
    assert candidates(layout) == []


def test_each_pathway_gets_a_form_fixed_to_it(layout):
    write_templates(layout, FORM)
    for pathway in PATHWAYS:
        html = (layout.inbox / pathway / "_template/context-form.html").read_text(encoding="utf-8")
        assert f'data-pathway="{pathway}"' in html and html.count("data-pathway=") == 1


def test_a_form_already_there_is_kept(layout):
    target = layout.inbox / "earnings_update/_template/context-form.html"
    target.parent.mkdir()
    target.write_bytes(b"analyst edit")
    write_templates(layout, FORM)
    assert target.read_bytes() == b"analyst edit"
    assert (layout.inbox / "credit_snapshot/_template/context-form.html").is_file()


def test_templates_refuse_links(layout):
    elsewhere = layout.root / "elsewhere"
    elsewhere.mkdir()
    (layout.inbox / "credit_snapshot/_template").symlink_to(elsewhere)
    with pytest.raises(OSError, match="link"):
        write_templates(layout, FORM)
    assert list(elsewhere.iterdir()) == []
    (layout.inbox / "credit_snapshot/_template").unlink()
    target = layout.inbox / "credit_snapshot/_template/context-form.html"
    target.parent.mkdir()
    target.symlink_to(elsewhere / "missing")
    with pytest.raises(OSError, match="link"):
        write_templates(layout, FORM)
    assert not (elsewhere / "missing").exists()


def test_an_unmarkable_form_is_refused(layout, tmp_path):
    form = tmp_path / "context-form.html"
    form.write_text("<html><body></body></html>", encoding="utf-8")
    with pytest.raises(ValueError, match="html lang"):
        write_templates(layout, form)
    assert not (layout.inbox / "credit_snapshot/_template").exists()
