"""Read side of Signal: feed pages, search, new-story counts and saves."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import NotRequired, TypedDict, Unpack

from deploy_workflow.signal.store import KINDS, _utc_text, _write_transaction
from deploy_workflow.signal.topics import fts_phrase

PAGE = 30
MAX_QUERY = 100


class ViewError(ValueError):
    """An unknown view, kind, topic or story, or a malformed cursor."""


@dataclass(frozen=True)
class Card:
    id: int
    title: str
    link: str
    summary: str
    source: str
    kind: str
    published_at: str
    other_sources: int
    saved: bool
    topics: tuple[str, ...]


@dataclass(frozen=True)
class Page:
    cards: tuple[Card, ...]
    next_before: str | None
    newest: int  # highest story id in the whole store when the page was read; 0 if empty


class Filters(TypedDict):
    """Optional keyword arguments of `feed`."""

    kind: NotRequired[str | None]
    query: NotRequired[str]
    before: NotRequired[str | None]


_FOLLOWED = (
    "EXISTS(SELECT 1 FROM topic_stories ts JOIN topic_follows f ON f.topic_id = ts.topic_id"
    " WHERE ts.story_id = s.id AND f.user_name = ?)"
)
_SAVED = "EXISTS(SELECT 1 FROM saves v WHERE v.story_id = s.id AND v.user_name = ?)"
_IN_TOPIC = "EXISTS(SELECT 1 FROM topic_stories ts WHERE ts.story_id = s.id AND ts.topic_id = ?)"


MAX_ID = 2**63 - 1


def _id(number: str, what: str) -> int:
    """A decimal id that SQLite can hold, else ViewError."""
    if (
        not number.isascii()
        or not number.isdecimal()
        or len(number) > len(str(MAX_ID))  # before int(): a huge digit string raises ValueError
        or int(number) > MAX_ID
    ):
        raise ViewError(f"invalid {what} {number!r}")
    return int(number)


def _instant(text: str, what: str) -> str:
    """The stored UTC text of a zoned ISO time, else ViewError."""
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ViewError(f"malformed {what} {text!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ViewError(f"{what} {text!r} has no time zone")
    try:
        return _utc_text(parsed)
    except OverflowError as exc:  # a year-1 or year-9999 time with an offset leaves the UTC range
        raise ViewError(f"{what} {text!r} is out of range") from exc


def _after(after: object) -> int:
    """A story id cursor: an int from 0 to MAX_ID, else ViewError."""
    if isinstance(after, bool) or not isinstance(after, int) or not 0 <= after <= MAX_ID:
        raise ViewError(f"invalid after {after!r}")
    return after


@contextmanager
def _snapshot(db: sqlite3.Connection) -> Iterator[None]:
    """One read transaction, so every read inside it sees the same committed state."""
    db.execute("BEGIN")
    try:
        yield
    finally:
        if db.in_transaction:
            db.execute("ROLLBACK")


def _newest(db: sqlite3.Connection) -> int:
    return int(db.execute("SELECT COALESCE(MAX(id), 0) FROM stories").fetchone()[0])


def _view_clause(
    db: sqlite3.Connection, user_name: str, view: str
) -> tuple[str | None, list[object]]:
    """The fixed SQL condition for a validated view, with its parameters."""
    if view == "latest":
        return None, []
    if view == "foryou":
        return _FOLLOWED, [user_name]
    if view == "saved":
        return _SAVED, [user_name]
    prefix, _, number = view.partition(":")
    if prefix == "topic" and number.isascii() and number.isdecimal():
        topic_id = _id(number, "topic id")
        if db.execute("SELECT 1 FROM topics WHERE id=?", (topic_id,)).fetchone() is None:
            raise ViewError(f"no topic with id {topic_id}")
        return _IN_TOPIC, [topic_id]
    raise ViewError(f"unknown view {view!r}")


def _cursor(before: str) -> tuple[str, int]:
    stamp, bar, number = before.rpartition("|")
    if not bar:
        raise ViewError(f"malformed cursor {before!r}")
    return _instant(stamp, "cursor time"), _id(number, "cursor id")


def _search_match(query: str) -> str | None:
    terms = query[:MAX_QUERY].split()
    return " ".join(fts_phrase(term) for term in terms) if terms else None


def _topic_names(db: sqlite3.Connection, story_id: int) -> tuple[str, ...]:
    rows = db.execute(
        "SELECT t.name FROM topic_stories ts JOIN topics t ON t.id = ts.topic_id"
        " WHERE ts.story_id=? ORDER BY t.id",
        (story_id,),
    ).fetchall()
    return tuple(row["name"] for row in rows)


def _card(db: sqlite3.Connection, row: sqlite3.Row) -> Card:
    return Card(
        id=row["id"],
        title=row["title"],
        link=row["link"],
        summary=row["summary"],
        source=row["source"],
        kind=row["kind"],
        published_at=row["published_at"],
        other_sources=row["other_sources"],
        saved=bool(row["saved"]),
        topics=_topic_names(db, row["id"]),
    )


_CARD_SELECT = (
    "SELECT s.id, s.title, s.link, s.summary, s.published_at, src.name AS source,"
    " src.kind AS kind,"
    " (SELECT COUNT(DISTINCT d.duplicate_source_id) FROM story_duplicates d"
    "  WHERE d.story_id = s.id) AS other_sources,"
    " EXISTS(SELECT 1 FROM saves me WHERE me.story_id = s.id AND me.user_name = ?) AS saved"
    " FROM stories s JOIN sources src ON src.id = s.source_id"
)


def card_for(db: sqlite3.Connection, user_name: str, story_id: int) -> Card:
    """The card of one story as the user sees it, else ViewError."""
    row = (
        db.execute(_CARD_SELECT + " WHERE s.id = ?", (user_name, story_id)).fetchone()
        if 0 <= story_id <= MAX_ID
        else None
    )
    if row is None:
        raise ViewError(f"no story with id {story_id}")
    return _card(db, row)


def feed(
    db: sqlite3.Connection,
    user_name: str,
    view: str,
    **filters: Unpack[Filters],
) -> Page:
    """One page of stories, newest first. Raises ViewError for an invalid request."""
    with _snapshot(db):
        return _read_page(db, user_name, view, filters)


def _read_page(db: sqlite3.Connection, user_name: str, view: str, filters: Filters) -> Page:
    kind = filters.get("kind")
    before = filters.get("before")
    conditions: list[str] = []
    params: list[object] = []
    clause, clause_params = _view_clause(db, user_name, view)
    if clause is not None:
        conditions.append(clause)
        params += clause_params
    if kind is not None:
        if kind not in KINDS:
            raise ViewError(f"unknown kind {kind!r}")
        conditions.append("src.kind = ?")
        params.append(kind)
    match = _search_match(filters.get("query", ""))
    if match is not None:
        conditions.append("s.id IN (SELECT rowid FROM stories_fts WHERE stories_fts MATCH ?)")
        params.append(match)
    if before is not None:
        stamp, story_id = _cursor(before)
        conditions.append("(s.published_at < ? OR (s.published_at = ? AND s.id < ?))")
        params += [stamp, stamp, story_id]
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    rows = db.execute(
        _CARD_SELECT + where + " ORDER BY s.published_at DESC, s.id DESC LIMIT ?",
        [user_name, *params, PAGE + 1],
    ).fetchall()
    cards = tuple(_card(db, row) for row in rows[:PAGE])
    more = len(rows) > PAGE
    last = cards[-1] if more else None
    return Page(cards, f"{last.published_at}|{last.id}" if last else None, _newest(db))


def new_count(db: sqlite3.Connection, user_name: str, view: str, after: int) -> int:
    """Stories in the view with an id above `after`, the `newest` of an earlier page."""
    floor = _after(after)
    clause, params = _view_clause(db, user_name, view)
    where = " AND " + clause if clause is not None else ""
    row = db.execute(
        "SELECT COUNT(*) FROM stories s WHERE s.id > ?" + where, [floor, *params]
    ).fetchone()
    return int(row[0])


def _require_story(db: sqlite3.Connection, story_id: int) -> None:
    if db.execute("SELECT 1 FROM stories WHERE id=?", (story_id,)).fetchone() is None:
        raise ViewError(f"no story with id {story_id}")


def save(db: sqlite3.Connection, user_name: str, story_id: int) -> None:
    with _write_transaction(db):
        _require_story(db, story_id)
        db.execute(
            "INSERT OR IGNORE INTO saves(user_name, story_id, saved_at) VALUES(?, ?, ?)",
            (user_name, story_id, _utc_text(datetime.now().astimezone())),
        )


def unsave(db: sqlite3.Connection, user_name: str, story_id: int) -> None:
    with _write_transaction(db):
        _require_story(db, story_id)
        db.execute("DELETE FROM saves WHERE user_name=? AND story_id=?", (user_name, story_id))
