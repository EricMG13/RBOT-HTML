import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.feedview import Page, ViewError, feed, new_count, save, unsave
from deploy_workflow.signal.store import add_story, open_db, propose_source, set_source_state
from deploy_workflow.signal.topics import add_topic, follow

FETCHED = datetime(2026, 11, 13, 9, 40, tzinfo=UTC)
LAST = datetime(2026, 11, 13, 9, 35, tzinfo=UTC)


def build_feed_db(root: Path):
    """Two sources, 35 regulator stories one minute apart, a newer wire story, one link fold."""
    db = open_db(root)
    for name, kind, url in (
        ("Authority", "regulator", "https://a.org/f"),
        ("Wire", "news", "https://w.org/f"),
    ):
        set_source_state(db, propose_source(db, name, kind, url, "x"), "approved")
    for n in range(1, 36):
        entry = Entry(
            f"Story {n:02d}",
            f"https://a.org/{n}",
            LAST - timedelta(minutes=35 - n),
            f"Summary {n}",
        )
        add_story(db, 1, entry, FETCHED)
    # Same link as source 1's Story 35: a link fold (titles under four words never fold by title).
    same_link = Entry("Story 35", "https://a.org/35", LAST, "Summary 35")
    assert add_story(db, 2, same_link, FETCHED) == "duplicate"
    wire = Entry(
        "Wire piece on remedy", "https://w.org/1", LAST + timedelta(minutes=1), "About a remedy"
    )
    add_story(db, 2, wire, FETCHED)
    add_topic(db, "Remedy", ["remedy"], [], "x")
    return db


@pytest.fixture
def db_feed(tmp_path):
    db = build_feed_db(tmp_path)
    yield db
    db.close()


@contextmanager
def feed_db():
    with tempfile.TemporaryDirectory() as folder:
        db = build_feed_db(Path(folder))
        try:
            yield db
        finally:
            db.close()


def test_latest_pages_by_30_newest_first(db_feed):
    first = feed(db_feed, "ak", "latest")
    assert len(first.cards) == 30 and first.cards[0].title == "Wire piece on remedy"
    assert first.cards[1].title == "Story 35" and first.cards[1].other_sources == 1
    second = feed(db_feed, "ak", "latest", before=first.next_before)
    assert [c.title for c in second.cards] == [f"Story {n:02d}" for n in range(6, 0, -1)]
    assert second.next_before is None


def test_kind_filter_and_card_fields(db_feed):
    page = feed(db_feed, "ak", "latest", kind="news")
    (card,) = page.cards
    assert (card.source, card.kind, card.published_at, card.saved, card.topics) == (
        "Wire",
        "news",
        "2026-11-13T09:36:00+00:00",
        False,
        ("Remedy",),
    )


def test_foryou_is_followed_topics_only(db_feed):
    assert feed(db_feed, "ak", "foryou").cards == ()
    follow(db_feed, "ak", 1)
    assert [c.title for c in feed(db_feed, "ak", "foryou").cards] == ["Wire piece on remedy"]
    assert feed(db_feed, "ml", "foryou").cards == ()


def test_topic_view_and_unknown_topic(db_feed):
    assert len(feed(db_feed, "ak", "topic:1").cards) == 1
    with pytest.raises(ViewError):
        feed(db_feed, "ak", "topic:99")


def test_save_is_personal_idempotent_and_listed(db_feed):
    save(db_feed, "ak", 5)
    save(db_feed, "ak", 5)
    assert [c.id for c in feed(db_feed, "ak", "saved").cards] == [5]
    assert feed(db_feed, "ml", "saved").cards == ()
    before = "2026-11-13T09:06:00+00:00|6"
    assert next(c for c in feed(db_feed, "ak", "latest", before=before).cards if c.id == 5).saved
    unsave(db_feed, "ak", 5)
    unsave(db_feed, "ak", 5)
    assert feed(db_feed, "ak", "saved").cards == ()
    with pytest.raises(ViewError):
        save(db_feed, "ak", 9999)


def test_search_matches_all_terms(db_feed):
    found = feed(db_feed, "ak", "latest", query="wire remedy").cards
    assert [c.title for c in found] == ["Wire piece on remedy"]
    assert feed(db_feed, "ak", "latest", query="wire absent").cards == ()


@pytest.mark.parametrize(
    "query", ['"', 'a"b', "*", "NEAR", "x AND", "-", "(", "title:x", "\x00", "ß" * 300]
)
def test_search_text_is_never_query_syntax(db_feed, query):
    feed(db_feed, "ak", "latest", query=query)  # must not raise


@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None, max_examples=50)
@given(st.text(max_size=200))
def test_any_search_text_returns_a_page(query):
    with feed_db() as db:
        assert isinstance(feed(db, "ak", "latest", query=query), Page)


@pytest.mark.parametrize(
    "bad",
    [
        {"view": "top"},
        {"view": "latest", "kind": "blog"},
        {"view": "latest", "before": "x"},
        {"view": "topic:abc"},
    ],
)
def test_bad_requests_raise_view_error(db_feed, bad):
    with pytest.raises(ViewError):
        feed(db_feed, "ak", **bad)


def test_new_count(db_feed):  # every fixture story fetched at 09:40Z
    assert new_count(db_feed, "ak", "latest", "2026-11-13T09:39:00+00:00") == 36
    assert new_count(db_feed, "ak", "latest", "2026-11-13T09:40:00+00:00") == 0


@pytest.mark.parametrize(
    "bad",
    [
        {"view": "topic:99999999999999999999"},
        {"view": "latest", "before": "2026-11-13T09:00:00+00:00|99999999999999999999"},
        {"view": "latest", "before": "2026-11-13T09:00:00|5"},
    ],
)
def test_oversized_ids_and_zoneless_cursor_raise_view_error(db_feed, bad):
    with pytest.raises(ViewError):
        feed(db_feed, "ak", **bad)


def test_new_count_compares_instants_not_text(db_feed):
    assert new_count(db_feed, "ak", "latest", "2026-11-13T04:40:00-05:00") == 0


@pytest.mark.parametrize("since", ["garbage", "", "2026-11-13T09:39:00"])
def test_new_count_refuses_unparseable_or_zoneless_since(db_feed, since):
    with pytest.raises(ViewError):
        new_count(db_feed, "ak", "latest", since)
