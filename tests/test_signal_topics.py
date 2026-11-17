import json
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import test_signal_ingest
from hypothesis import given
from hypothesis import strategies as st
from test_signal_feeds import RSS
from test_signal_ingest import NOW, recorded

from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.ingest import run_due
from deploy_workflow.signal.store import (
    StoreError,
    add_story,
    get_meta,
    open_db,
    propose_source,
)
from deploy_workflow.signal.topics import (
    add_topic,
    follow,
    list_topics,
    match_story,
    unfollow,
)

# Slice 1 fixtures, reused as they are (pytest registers them by this module's names).
db = test_signal_ingest.db
db_a = test_signal_ingest.db_a


@contextmanager
def fresh_db():
    with tempfile.TemporaryDirectory() as folder:
        db = open_db(Path(folder))
        try:
            yield db
        finally:
            db.close()


@pytest.fixture
def db_two_sources(tmp_path):
    db = open_db(tmp_path)
    propose_source(db, "Authority", "regulator", "https://a.org/f", "x")
    propose_source(db, "Paper", "news", "https://b.org/f", "x")
    return db


def rows(db, sql, *params):
    return [tuple(r) for r in db.execute(sql, params).fetchall()]


def count(db, table):
    return db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_topic_matches_existing_and_later_stories(db_two_sources):
    t0 = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_story(
        db_two_sources,
        1,
        Entry("Authority opens merger review", "https://a.org/1", t0, "wholesale access remedy"),
        t0,
    )
    tid = add_topic(db_two_sources, "Competition", ["merger review", "remedy"], [], "ak")
    assert rows(db_two_sources, "SELECT story_id FROM topic_stories WHERE topic_id=?", tid) == [
        (1,)
    ]
    add_story(db_two_sources, 2, Entry("Operator plans merger", "https://b.org/1", t0, ""), t0)
    assert match_story(db_two_sources, 2) == []
    add_story(
        db_two_sources, 2, Entry("Second MERGER REVIEW opened", "https://b.org/2", t0, ""), t0
    )
    assert match_story(db_two_sources, 3) == [tid]
    assert match_story(db_two_sources, 3) == [tid]
    assert count(db_two_sources, "topic_stories") == 2


def test_topic_kind_filter(db_two_sources):
    t0 = datetime(2026, 11, 13, 9, tzinfo=UTC)
    tid = add_topic(db_two_sources, "Reg only", ["review"], ["regulator"], "ak")
    add_story(db_two_sources, 2, Entry("News review of the year", "https://b.org/1", t0, ""), t0)
    add_story(db_two_sources, 1, Entry("Regulator review opens", "https://a.org/1", t0, ""), t0)
    assert match_story(db_two_sources, 1) == [] and match_story(db_two_sources, 2) == [tid]


@pytest.mark.parametrize(
    "keywords,kinds", [([], []), ([" "], []), (["x" * 61], []), (["ok"], ["blog"])]
)
def test_bad_topic_rules_are_refused(db_two_sources, keywords, kinds):
    with pytest.raises(StoreError):
        add_topic(db_two_sources, "T", keywords, kinds, "ak")


@pytest.mark.parametrize("keyword", ['say "hello"', "a*", "NEAR", "x AND y", "-", "(", "col:on"])
def test_keywords_with_query_syntax_are_plain_text(db_two_sources, keyword):
    add_topic(db_two_sources, f"T {keyword}", [keyword], [], "ak")


@given(st.text(min_size=1, max_size=60).filter(lambda s: s.strip()))
def test_any_keyword_is_accepted_without_error(keyword):
    with fresh_db() as db:
        add_topic(db, "T", [keyword], [], "ak")


def test_nul_in_a_keyword_is_plain_text_and_does_not_poison_matching(db_two_sources):
    t0 = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_topic(db_two_sources, "Nul", ["a\x00b"], [], "ak")
    add_story(db_two_sources, 1, Entry("Authority review", "https://a.org/1", t0, ""), t0)
    assert match_story(db_two_sources, 1) == []
    add_topic(db_two_sources, "Nul again", ["a\x00b"], [], "ak")


def test_follow_is_personal_and_idempotent(db_two_sources):
    tid = add_topic(db_two_sources, "Competition", ["review"], [], "ak")
    follow(db_two_sources, "ak", tid)
    follow(db_two_sources, "ak", tid)
    assert [(r["id"], r["following"]) for r in list_topics(db_two_sources, "ak")] == [(tid, 1)]
    assert [(r["id"], r["following"]) for r in list_topics(db_two_sources, "ml")] == [(tid, 0)]
    unfollow(db_two_sources, "ak", tid)
    unfollow(db_two_sources, "ak", tid)
    assert list_topics(db_two_sources, "ak")[0]["following"] == 0
    with pytest.raises(StoreError):
        follow(db_two_sources, "ak", 999)


def test_pass_records_its_time_and_matches_new_stories_with_recorded_feed(db_a):
    tid = add_topic(db_a, "Opens", ["opens review"], [], "ak")
    assert tid == 1
    run_due(db_a, NOW, recorded(RSS))
    assert get_meta(db_a, "last_pass_at") == NOW.isoformat()
    assert count(db_a, "topic_stories") == 1
    run_due(db_a, NOW + timedelta(seconds=30), recorded(RSS))
    assert get_meta(db_a, "last_pass_at") == (NOW + timedelta(seconds=30)).isoformat()


def test_a_slice_1_database_gains_the_new_tables(tmp_path):
    db = open_db(tmp_path)
    assert db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "3"
    names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"topics", "topic_stories", "topic_follows", "saves"} <= names


def test_add_topic_links_exactly_what_the_per_story_path_links(tmp_path):
    database = open_db(tmp_path)
    try:
        words = [
            *("merger", "remedy", "spectrum", "auction", "roaming"),
            *("broadband", "tariff", "licence", "appeal", "fine"),
        ]
        base = datetime(2026, 1, 1, tzinfo=UTC)
        with database:
            for index, kind in enumerate(("regulator", "news", "research")):
                database.execute(
                    "INSERT INTO sources(name, kind, url, state, proposed_by, created_at)"
                    " VALUES(?, ?, ?, 'approved', 'x', ?)",
                    (f"S{index}", kind, f"https://s{index}.org/f", base.isoformat()),
                )
            rows = []
            for i in range(2000):
                at = (base + timedelta(minutes=i)).isoformat()
                title = " ".join(words[(i * k + k) % len(words)] for k in (1, 3, 7))
                summary = " ".join(words[(i * k + 2) % len(words)] for k in (2, 5, 9))
                link = f"https://s{i % 3}.org/{i}"
                rows.append((i % 3 + 1, title, link, link, title, at, at, summary))
            database.executemany(
                "INSERT INTO stories(source_id, title, link, link_key, title_key, published_at,"
                " fetched_at, summary) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
        keywords = ["merger", "spectrum auction", 'say "tariff"', "no such word"]
        kinds = ["regulator", "research"]
        first = add_topic(database, "New path", keywords, kinds, "x")
        with database:
            second = database.execute(
                "INSERT INTO topics(name, keywords, kinds, created_by, created_at)"
                " VALUES('Old path', ?, ?, 'x', ?)",
                (json.dumps(keywords), json.dumps(kinds), base.isoformat()),
            ).lastrowid
        for story_id in range(1, 2001):
            match_story(database, story_id)

        def linked(topic_id):
            return {
                row[0]
                for row in database.execute(
                    "SELECT story_id FROM topic_stories WHERE topic_id=?", (topic_id,)
                )
            }

        assert linked(first) == linked(second)
        assert 0 < len(linked(first)) < 2000
    finally:
        database.close()
