"""One ingest pass over the approved sources that are due, and a health summary per source."""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from deploy_workflow.signal import fetch
from deploy_workflow.signal.feeds import FeedError, parse_feed
from deploy_workflow.signal.fetch import Fetched, FetchRefused
from deploy_workflow.signal.store import Check, add_story, last_check, record_check, sources

MIN_INTERVAL = timedelta(seconds=600)
QUIET_AFTER = timedelta(days=7)
HEALTH_WEEKS = 6
_WEEK = timedelta(days=7)

FetchFn = Callable[[str, str | None, str | None], Fetched]


def _is_due(db: sqlite3.Connection, source_id: int, now: datetime) -> bool:
    previous = last_check(db, source_id)
    return previous is None or datetime.fromisoformat(previous["at"]) <= now - MIN_INTERVAL


def _check_source(
    db: sqlite3.Connection, source: sqlite3.Row, now: datetime, fetch_fn: FetchFn
) -> Check:
    previous = last_check(db, source["id"])
    etag = previous["etag"] if previous else None
    modified = previous["modified"] if previous else None
    try:
        fetched = fetch_fn(source["url"], etag, modified)
        if fetched.body is None:
            return Check(now, True, "not modified", etag, modified, 0)
        entries = parse_feed(fetched.body)
    except (FetchRefused, FeedError) as error:
        return Check(now, False, str(error), etag, modified, 0)
    new = sum(1 for entry in entries if add_story(db, source["id"], entry, now) == "new")
    return Check(now, True, f"{new} new", fetched.etag, fetched.modified, new)


def run_due(
    db: sqlite3.Connection, now: datetime, fetch_fn: FetchFn | None = None
) -> list[tuple[int, bool, str]]:
    """Check every approved source with no check in the last MIN_INTERVAL.

    Only a refused fetch or an unreadable feed is recorded as a failed check; any other
    exception is a bug and propagates, leaving no check row for that source."""
    results: list[tuple[int, bool, str]] = []
    for source in sources(db, "approved"):
        if not _is_due(db, source["id"], now):
            continue
        check = _check_source(db, source, now, fetch_fn if fetch_fn is not None else fetch.fetch)
        record_check(db, source["id"], check)
        results.append((source["id"], check.ok, check.reason))
    return results


@dataclass(frozen=True)
class Health:
    state: Literal["healthy", "quiet", "failing", "never checked"]
    last_check: datetime | None
    last_item: datetime | None
    per_week: tuple[int, ...]
    reason: str


def _per_week(published: list[datetime], now: datetime) -> tuple[int, ...]:
    """Counts per 7-day window ending at `now`, oldest first; a window is (start, end]."""
    counts = [0] * HEALTH_WEEKS
    for at in published:
        age = now - at
        if timedelta(0) <= age < HEALTH_WEEKS * _WEEK:
            counts[HEALTH_WEEKS - 1 - age // _WEEK] += 1
    return tuple(counts)


def health(db: sqlite3.Connection, source_id: int, now: datetime) -> Health:
    rows = db.execute(
        "SELECT published_at FROM stories WHERE source_id=?"
        " UNION ALL SELECT published_at FROM story_duplicates WHERE duplicate_source_id=?",
        (source_id, source_id),
    ).fetchall()
    published = [datetime.fromisoformat(row["published_at"]) for row in rows]
    last_item = max(published, default=None)
    previous = last_check(db, source_id)
    if previous is None:
        return Health("never checked", None, last_item, _per_week(published, now), "")
    checked = datetime.fromisoformat(previous["at"])
    state: Literal["healthy", "quiet", "failing"]
    if not previous["ok"]:
        state = "failing"
    elif last_item is None or last_item < now - QUIET_AFTER:
        state = "quiet"
    else:
        state = "healthy"
    return Health(state, checked, last_item, _per_week(published, now), previous["reason"])
