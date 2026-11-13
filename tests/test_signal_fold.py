from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.fold import link_key, title_key
from deploy_workflow.signal.store import (
    StoreError,
    add_story,
    open_db,
    propose_source,
    set_source_state,
)


@pytest.fixture
def db2(tmp_path: Path) -> sqlite3.Connection:
    db = open_db(tmp_path)
    for n in (1, 2):
        sid = propose_source(db, f"S{n}", "news", f"https://s{n}.example/feed", "tester")
        set_source_state(db, sid, "approved")
    return db


@pytest.mark.parametrize(
    "a,b",
    [
        ("https://www.Example.org/news/1/", "http://example.org/news/1"),
        ("https://example.org/n?id=7&utm_source=x&fbclid=y", "https://example.org/n?id=7"),
        ("https://example.org/n?b=2&a=1#top", "https://example.org/n?a=1&b=2"),
    ],
)
def test_link_key_equates(a: str, b: str) -> None:
    assert link_key(a) == link_key(b)


def test_link_key_keeps_meaningful_query() -> None:
    assert link_key("https://example.org/n?id=7") != link_key("https://example.org/n?id=8")


def test_title_key() -> None:
    got = title_key("  Authority opens  in-depth review — Northwave! ")
    assert got == "authority opens in depth review northwave"


@given(st.text())
def test_title_key_is_idempotent(t: str) -> None:
    assert title_key(title_key(t)) == title_key(t)


def test_same_link_from_two_sources_folds(db2: sqlite3.Connection) -> None:
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    first = Entry("A long enough headline here", "https://e.org/1", t, "")
    second = Entry("Different words entirely now", "https://www.e.org/1/", t, "")
    assert add_story(db2, 1, first, t) == "new"
    assert add_story(db2, 2, second, t) == "duplicate"
    assert db2.execute("SELECT count(*) FROM stories").fetchone()[0] == 1
    assert db2.execute("SELECT count(*) FROM story_duplicates").fetchone()[0] == 1


def test_same_title_within_48_hours_folds_and_after_does_not(db2: sqlite3.Connection) -> None:
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_story(db2, 1, Entry("Authority opens in-depth review", "https://a.org/1", t, ""), t)
    near, far = t + timedelta(hours=47), t + timedelta(hours=49)
    e_near = Entry("Authority opens in depth review", "https://b.org/9", near, "")
    e_far = Entry("Authority opens in depth review", "https://b.org/10", far, "")
    assert add_story(db2, 2, e_near, near) == "duplicate"
    assert add_story(db2, 2, e_far, far) == "new"


def test_short_generic_titles_do_not_fold(db2: sqlite3.Connection) -> None:
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_story(db2, 1, Entry("Press release", "https://a.org/1", t, ""), t)
    assert add_story(db2, 2, Entry("Press release", "https://b.org/1", t, ""), t) == "new"


def test_same_source_same_link_is_seen_and_writes_nothing(db2: sqlite3.Connection) -> None:
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    e = Entry("A long enough headline here", "https://e.org/1", t, "")
    add_story(db2, 1, e, t)
    assert add_story(db2, 1, e, t) == "seen"
    assert db2.execute("SELECT count(*) FROM story_duplicates").fetchone()[0] == 0


def test_missing_or_future_date_becomes_fetch_time(db2: sqlite3.Connection) -> None:
    now = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_story(db2, 1, Entry("No date on this story", "https://e.org/1", None, ""), now)
    future = Entry("Future date on this story", "https://e.org/2", now + timedelta(days=400), "")
    add_story(db2, 1, future, now)
    got = [r[0] for r in db2.execute("SELECT published_at FROM stories ORDER BY id")]
    assert got == [now.isoformat(), now.isoformat()]


def test_same_source_same_title_different_links_do_not_fold(db2: sqlite3.Connection) -> None:
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    first = Entry("Town and Country Planning notice", "https://a.org/1", t, "")
    second = Entry("Town and Country Planning notice", "https://a.org/2", t, "")
    other = Entry("Town and Country Planning notice", "https://b.org/1", t, "")
    assert add_story(db2, 1, first, t) == "new"
    assert add_story(db2, 1, second, t) == "new"
    assert add_story(db2, 2, other, t) == "duplicate"


def test_naive_published_time_is_a_store_error(db2: sqlite3.Connection) -> None:
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    entry = Entry("A long enough headline here", "https://e.org/1", datetime(2026, 11, 13, 9), "")
    with pytest.raises(StoreError, match="timezone"):
        add_story(db2, 1, entry, t)
    assert db2.execute("SELECT count(*) FROM stories").fetchone()[0] == 0


def test_folded_undated_entry_stays_folded_on_later_passes(db2: sqlite3.Connection) -> None:
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    title = "Authority opens in-depth review of Northwave"
    add_story(db2, 1, Entry(title, "https://a.org/1", t, ""), t)
    undated = Entry(title, "https://b.org/9", None, "")
    assert add_story(db2, 2, undated, t) == "duplicate"
    for hours in (1, 47, 49, 72):
        assert add_story(db2, 2, undated, t + timedelta(hours=hours)) == "seen"
    assert db2.execute("SELECT count(*) FROM stories").fetchone()[0] == 1
    row = db2.execute("SELECT link_key, published_at FROM story_duplicates").fetchone()
    assert (row["link_key"], row["published_at"]) == ("b.org/9", t.isoformat())
