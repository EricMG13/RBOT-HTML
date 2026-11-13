from __future__ import annotations

import multiprocessing as mp
import sqlite3
from datetime import UTC, datetime
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Barrier
from pathlib import Path

import pytest

from deploy_workflow.signal.store import (
    Check,
    StoreError,
    add_user,
    last_check,
    open_db,
    propose_source,
    record_check,
    role_of,
    set_source_state,
    sources,
)


def test_open_db_creates_file_in_wal_mode(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    assert (tmp_path / "signal" / "signal.db").is_file()
    assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_open_db_twice_keeps_data(tmp_path: Path) -> None:
    add_user(open_db(tmp_path), "A. Kovac", "writer")
    assert role_of(open_db(tmp_path), "A. Kovac") == "writer"


def test_unknown_name_is_a_reader(tmp_path: Path) -> None:
    assert role_of(open_db(tmp_path), "nobody") == "reader"


@pytest.mark.parametrize("role", ["admin", "", "Writer"])
def test_invalid_role_is_refused(tmp_path: Path, role: str) -> None:
    with pytest.raises(StoreError):
        add_user(open_db(tmp_path), "X", role)


def test_proposed_source_is_not_approved(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    sid = propose_source(db, "Authority", "regulator", "https://example.org/feed", "A. Kovac")
    assert [r["id"] for r in sources(db, "proposed")] == [sid]
    assert sources(db, "approved") == []
    set_source_state(db, sid, "approved")
    assert [r["id"] for r in sources(db, "approved")] == [sid]


def test_same_url_cannot_be_proposed_twice(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    propose_source(db, "A", "news", "https://example.org/feed", "x")
    with pytest.raises(StoreError):
        propose_source(db, "B", "news", "https://example.org/feed", "y")


def test_fts_finds_a_story_by_title_word(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    sid = propose_source(db, "A", "news", "https://example.org/feed", "x")
    db.execute(
        "INSERT INTO stories(source_id,title,link,link_key,title_key,published_at,fetched_at,"
        "summary) VALUES(?,?,?,?,?,?,?,?)",
        (
            sid,
            "Wholesale access remedy",
            "https://e.org/1",
            "e.org/1",
            "wholesale access remedy",
            "2026-11-13T09:00:00+00:00",
            "2026-11-13T09:05:00+00:00",
            "",
        ),
    )
    hits = db.execute("SELECT rowid FROM stories_fts WHERE stories_fts MATCH 'remedy'").fetchall()
    assert len(hits) == 1


def test_invalid_kind_state_and_empty_name_are_refused(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    with pytest.raises(StoreError):
        propose_source(db, "A", "blog", "https://e.org/f", "x")
    with pytest.raises(StoreError):
        propose_source(db, " ", "news", "https://e.org/f", "x")
    with pytest.raises(StoreError):
        add_user(db, "", "reader")
    sid = propose_source(db, "A", "news", "https://e.org/f", "x")
    with pytest.raises(StoreError):
        set_source_state(db, sid, "deleted")
    with pytest.raises(StoreError):
        sources(db, "deleted")
    with pytest.raises(StoreError):
        set_source_state(db, sid + 99, "approved")


def test_duplicate_user_is_refused(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    add_user(db, "A", "owner")
    with pytest.raises(StoreError):
        add_user(db, "A", "reader")


def test_last_check_returns_latest_in_utc(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    sid = propose_source(db, "A", "news", "https://e.org/f", "x")
    assert last_check(db, sid) is None
    t1 = datetime(2026, 11, 13, 9, 0, tzinfo=UTC)
    t2 = datetime(2026, 11, 13, 10, 0, tzinfo=UTC)
    record_check(db, sid, Check(t1, False, "timeout", None, None, 0))
    record_check(db, sid, Check(t2, True, "", "etag1", "Mon", 3))
    row = last_check(db, sid)
    assert row is not None
    assert row["at"] == "2026-11-13T10:00:00+00:00"
    assert (row["ok"], row["etag"], row["modified"], row["new_stories"]) == (1, "etag1", "Mon", 3)


def test_naive_check_time_is_refused(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    sid = propose_source(db, "A", "news", "https://e.org/f", "x")
    with pytest.raises(StoreError):
        record_check(db, sid, Check(datetime(2026, 11, 13, 9, 0), True, "", None, None, 0))


def _open_when_ready(root: str, barrier: Barrier, results: Queue[str]) -> None:
    barrier.wait(timeout=20)
    try:
        db = open_db(Path(root))
        version = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
        db.close()
        results.put(f"ok {version}")
    except (sqlite3.Error, StoreError) as exc:  # reported to the parent, which asserts on it
        results.put(f"{type(exc).__name__}: {exc}")


def test_concurrent_first_open_all_succeed(tmp_path: Path) -> None:
    for trial in range(8):
        root = tmp_path / str(trial)
        barrier = mp.Barrier(4)
        results = mp.Queue()
        procs = [
            mp.Process(target=_open_when_ready, args=(str(root), barrier, results))
            for _ in range(4)
        ]
        for p in procs:
            p.start()
        got = [results.get(timeout=60) for _ in procs]
        for p in procs:
            p.join(30)
        assert got == ["ok 2"] * 4


def test_fts_follows_title_update_and_delete(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    sid = propose_source(db, "A", "news", "https://e.org/f", "x")
    sql = (
        "INSERT INTO stories(source_id,title,link,link_key,title_key,published_at,fetched_at,"
        "summary) VALUES(?,?,?,?,?,?,?,?)"
    )
    for n, title in enumerate(["alpha remedy", "beta ruling"]):
        db.execute(
            sql,
            (
                sid,
                title,
                f"l{n}",
                f"k{n}",
                title,
                "2026-11-13T09:00:00+00:00",
                "2026-11-13T09:00:00+00:00",
                "",
            ),
        )

    def hits(word: str) -> int:
        q = "SELECT rowid FROM stories_fts WHERE stories_fts MATCH ?"
        return len(db.execute(q, (word,)).fetchall())

    db.execute("UPDATE stories SET title='gamma access' WHERE link_key='k0'")
    assert (hits("alpha"), hits("gamma")) == (0, 1)
    db.execute("DELETE FROM stories WHERE link_key='k1'")
    assert hits("beta") == 0


def test_link_first_seen_as_a_folded_duplicate_folds_again(tmp_path: Path) -> None:
    from datetime import timedelta

    from deploy_workflow.signal.feeds import Entry
    from deploy_workflow.signal.store import add_story

    db = open_db(tmp_path)
    for n in (1, 2, 3):
        sid = propose_source(db, f"S{n}", "news", f"https://s{n}.example/feed", "tester")
        set_source_state(db, sid, "approved")
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    title = "Authority opens in depth review of Northwave"
    assert add_story(db, 1, Entry(title, "https://e.org/l1", t, ""), t) == "new"
    later = t + timedelta(hours=2)
    assert add_story(db, 2, Entry(title, "https://e.org/l2", later, ""), later) == "duplicate"
    other = Entry("Completely different words appear now", "https://e.org/l2", later, "")
    assert add_story(db, 3, other, later) == "duplicate"
    assert db.execute("SELECT count(*) FROM stories").fetchone()[0] == 1
    rows = db.execute("SELECT story_id FROM story_duplicates").fetchall()
    assert [r["story_id"] for r in rows] == [1, 1]


def test_story_duplicates_link_key_has_an_index(tmp_path: Path) -> None:
    db = open_db(tmp_path)
    plan = db.execute(
        "EXPLAIN QUERY PLAN SELECT story_id FROM story_duplicates WHERE link_key = ?", ("k",)
    ).fetchall()
    assert any("idx_story_duplicates_link_key" in row["detail"] for row in plan)


def test_a_storys_own_source_is_never_recorded_as_its_duplicate(tmp_path: Path) -> None:
    from datetime import timedelta

    from deploy_workflow.signal.feeds import Entry
    from deploy_workflow.signal.store import add_story

    db = open_db(tmp_path)
    for n in (1, 2):
        sid = propose_source(db, f"S{n}", "news", f"https://s{n}.example/feed", "tester")
        set_source_state(db, sid, "approved")
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    later = t + timedelta(hours=2)
    title = "Authority opens in depth review of Northwave"
    assert add_story(db, 1, Entry(title, "https://e.org/l1", t, ""), t) == "new"
    assert add_story(db, 2, Entry(title, "https://e.org/l2", later, ""), later) == "duplicate"
    again = Entry("Completely different words appear now", "https://e.org/l2", later, "")
    assert add_story(db, 1, again, later) == "new"
    assert db.execute("SELECT count(*) FROM stories").fetchone()[0] == 2
    assert db.execute("SELECT count(*) FROM story_duplicates").fetchone()[0] == 1
    own = db.execute(
        "SELECT count(*) FROM story_duplicates d JOIN stories s ON s.id = d.story_id"
        " WHERE d.duplicate_source_id = s.source_id"
    ).fetchone()[0]
    assert own == 0
