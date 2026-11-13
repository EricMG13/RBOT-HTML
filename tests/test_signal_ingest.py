from datetime import UTC, datetime, timedelta

import pytest
from test_signal_feeds import RSS

from deploy_workflow.signal.fetch import Fetched, FetchRefused
from deploy_workflow.signal.ingest import health, run_due
from deploy_workflow.signal.store import open_db, propose_source, set_source_state

NOW = datetime(2026, 11, 13, 9, tzinfo=UTC)


@pytest.fixture
def db(tmp_path):
    return open_db(tmp_path)


@pytest.fixture
def db_a(db):
    a = propose_source(db, "A", "news", "https://a.org/f", "x")
    set_source_state(db, a, "approved")
    return db


def recorded(body, etag='"v1"'):
    calls = []

    def fn(url, etag_in, modified_in):
        calls.append((url, etag_in, modified_in))
        return Fetched(body, etag, None)

    fn.calls = calls
    return fn


def test_only_approved_sources_are_fetched_with_recorded_feed(db):
    a = propose_source(db, "A", "news", "https://a.org/f", "x")
    set_source_state(db, a, "approved")
    propose_source(db, "B", "news", "https://b.org/f", "x")  # stays proposed
    p = propose_source(db, "P", "news", "https://p.org/f", "x")
    set_source_state(db, p, "paused")
    fn = recorded(RSS)
    assert run_due(db, NOW, fn) == [(a, True, "2 new")]
    assert [c[0] for c in fn.calls] == ["https://a.org/f"]


def test_source_is_not_checked_again_within_600_seconds_with_recorded_feed(db_a):
    fn = recorded(RSS)
    run_due(db_a, NOW, fn)
    assert run_due(db_a, NOW + timedelta(seconds=599), fn) == []
    assert len(run_due(db_a, NOW + timedelta(seconds=600), fn)) == 1


def test_second_pass_sends_validators_and_adds_nothing_with_recorded_feed(db_a):
    fn = recorded(RSS)
    run_due(db_a, NOW, fn)
    assert run_due(db_a, NOW + timedelta(hours=1), fn)[0][2] == "0 new"
    assert fn.calls[1][1] == '"v1"'
    assert db_a.execute("SELECT count(*) FROM stories").fetchone()[0] == 2
    assert db_a.execute("SELECT count(*) FROM story_duplicates").fetchone()[0] == 0


def test_failing_source_is_recorded_and_others_still_run_with_recorded_feed(db):
    bad = propose_source(db, "Bad", "news", "https://bad.org/f", "x")
    set_source_state(db, bad, "approved")
    good = propose_source(db, "Good", "news", "https://good.org/f", "x")
    set_source_state(db, good, "approved")

    def fn(url, e, m):
        if "bad" in url:
            raise FetchRefused("feed is larger than 2 MB")
        return Fetched(RSS, None, None)

    assert run_due(db, NOW, fn) == [(bad, False, "feed is larger than 2 MB"), (good, True, "2 new")]
    assert health(db, bad, NOW).state == "failing"
    assert health(db, bad, NOW).reason == "feed is larger than 2 MB"


def test_unparseable_feed_is_failing_with_the_parser_reason_with_recorded_feed(db_a):
    run_due(db_a, NOW, recorded(b"not xml"))
    assert health(db_a, 1, NOW).state == "failing"
    assert health(db_a, 1, NOW).reason


def test_an_unexpected_error_is_not_swallowed_with_recorded_feed(db_a):
    def fn(url, e, m):
        raise RuntimeError("bug")

    with pytest.raises(RuntimeError):
        run_due(db_a, NOW, fn)
    assert health(db_a, 1, NOW).state == "never checked"


def test_not_modified_is_ok_and_keeps_validators_with_recorded_feed(db_a):
    run_due(db_a, NOW, recorded(RSS))
    out = run_due(db_a, NOW + timedelta(hours=1), lambda u, e, m: Fetched(None, None, None))
    assert out == [(1, True, "not modified")]
    seen = []

    def fn(u, e, m):
        seen.append(e)
        return Fetched(RSS, e, None)

    run_due(db_a, NOW + timedelta(hours=2), fn)
    assert seen == ['"v1"']


def test_health_states_and_weekly_counts_with_recorded_feed(db_a):
    assert health(db_a, 1, NOW).state == "never checked"
    run_due(db_a, NOW, recorded(RSS))  # one item dated 13 Nov 08:00Z, one undated -> NOW
    h = health(db_a, 1, NOW)
    assert (h.state, h.per_week) == ("healthy", (0, 0, 0, 0, 0, 2))
    later = NOW + timedelta(days=8)
    run_due(db_a, later, recorded(RSS))
    assert health(db_a, 1, later).state == "quiet"
    assert health(db_a, 1, later).per_week == (0, 0, 0, 0, 2, 0)


def test_source_whose_items_all_fold_is_healthy_with_its_items(db):
    body = (
        b'<rss version="2.0"><channel><item><title>Case 1 merger inquiry opened today</title>'
        b"<link>https://r.example.org/cases/1</link>"
        b"<pubDate>Fri, 13 Nov 2026 08:00:00 +0000</pubDate></item></channel></rss>"
    )
    for name in ("cases", "news"):
        sid = propose_source(db, name, "regulator", f"https://r.example.org/{name}.rss", "x")
        set_source_state(db, sid, "approved")
    run_due(db, NOW, recorded(body))
    first, second = health(db, 1, NOW), health(db, 2, NOW)
    assert db.execute("SELECT count(*) FROM story_duplicates").fetchone()[0] == 1
    assert second.state == "healthy"
    assert second.last_item == datetime(2026, 11, 13, 8, tzinfo=UTC)
    assert second.per_week == first.per_week == (0, 0, 0, 0, 0, 1)


def test_story_exactly_seven_days_old_is_in_the_previous_week():
    from deploy_workflow.signal.ingest import _per_week

    assert _per_week([NOW - timedelta(days=7)], NOW) == (0, 0, 0, 0, 1, 0)
