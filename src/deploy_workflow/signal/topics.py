"""Topics: a named keyword rule over stories, matched through the full-text index, and follows."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime

from deploy_workflow.signal.store import KINDS, StoreError, _utc_text, _write_transaction

MAX_KEYWORD = 60


def fts_phrase(text: str) -> str:
    """`text` as one quoted FTS5 phrase, so query syntax in it is plain text."""
    return '"' + text.replace('"', '""') + '"'


def _clean_keywords(keywords: Sequence[str]) -> list[str]:
    cleaned = [keyword.strip() for keyword in keywords]
    if not cleaned:
        raise StoreError("a topic needs at least one keyword")
    for keyword in cleaned:
        if not 1 <= len(keyword) <= MAX_KEYWORD:
            raise StoreError(f"a keyword must be 1 to {MAX_KEYWORD} characters, got {keyword!r}")
    return cleaned


def _clean_kinds(kinds: Sequence[str]) -> list[str]:
    for kind in kinds:
        if kind not in KINDS:
            raise StoreError(f"invalid kind {kind!r}; expected one of {', '.join(KINDS)}")
    return list(kinds)


def _matches(db: sqlite3.Connection, story_id: int, topic: sqlite3.Row) -> bool:
    """Whether the story meets the topic's rule; one phrase query per keyword."""
    kinds = json.loads(topic["kinds"])
    if kinds:
        kind = db.execute(
            "SELECT src.kind FROM stories s JOIN sources src ON src.id = s.source_id WHERE s.id=?",
            (story_id,),
        ).fetchone()
        if kind is None or kind["kind"] not in kinds:
            return False
    return any(
        db.execute(
            "SELECT 1 FROM stories_fts WHERE stories_fts MATCH ? AND rowid=?",
            (fts_phrase(keyword), story_id),
        ).fetchone()
        for keyword in json.loads(topic["keywords"])
    )


def _link(db: sqlite3.Connection, topic_id: int, story_id: int) -> None:
    db.execute(
        "INSERT OR IGNORE INTO topic_stories(topic_id, story_id) VALUES(?, ?)",
        (topic_id, story_id),
    )


def match_story(db: sqlite3.Connection, story_id: int) -> list[int]:
    """Topic ids whose rule the story meets; records them. Safe to repeat."""
    with _write_transaction(db):
        found = [
            topic["id"]
            for topic in db.execute("SELECT * FROM topics ORDER BY id").fetchall()
            if _matches(db, story_id, topic)
        ]
        for topic_id in found:
            _link(db, topic_id, story_id)
    return found


def add_topic(
    db: sqlite3.Connection,
    name: str,
    keywords: Sequence[str],
    kinds: Sequence[str],
    created_by: str,
) -> int:
    """Create a topic and match every existing story against it before returning."""
    if not name.strip():
        raise StoreError("name must not be empty")
    cleaned = _clean_keywords(keywords)
    allowed = _clean_kinds(kinds)
    with _write_transaction(db):
        try:
            cur = db.execute(
                "INSERT INTO topics(name, keywords, kinds, created_by, created_at)"
                " VALUES(?, ?, ?, ?, ?)",
                (name, json.dumps(cleaned), json.dumps(allowed), created_by, _utc_text(_now())),
            )
        except sqlite3.IntegrityError as exc:
            raise StoreError(f"topic {name!r} already exists") from exc
        assert cur.lastrowid is not None
        topic = db.execute("SELECT * FROM topics WHERE id=?", (cur.lastrowid,)).fetchone()
        for story in db.execute("SELECT id FROM stories ORDER BY id").fetchall():
            if _matches(db, story["id"], topic):
                _link(db, cur.lastrowid, story["id"])
    return cur.lastrowid


def _now() -> datetime:
    return datetime.now(UTC)


def _require_topic(db: sqlite3.Connection, topic_id: int) -> None:
    if db.execute("SELECT 1 FROM topics WHERE id=?", (topic_id,)).fetchone() is None:
        raise StoreError(f"no topic with id {topic_id}")


def follow(db: sqlite3.Connection, user_name: str, topic_id: int) -> None:
    _require_topic(db, topic_id)
    with db:
        db.execute(
            "INSERT OR IGNORE INTO topic_follows(user_name, topic_id) VALUES(?, ?)",
            (user_name, topic_id),
        )


def unfollow(db: sqlite3.Connection, user_name: str, topic_id: int) -> None:
    _require_topic(db, topic_id)
    with db:
        db.execute(
            "DELETE FROM topic_follows WHERE user_name=? AND topic_id=?", (user_name, topic_id)
        )


def list_topics(db: sqlite3.Connection, user_name: str) -> list[sqlite3.Row]:
    """Every topic with whether `user_name` follows it and how many stories it holds."""
    return db.execute(
        "SELECT t.id, t.name,"
        " EXISTS(SELECT 1 FROM topic_follows f WHERE f.topic_id = t.id AND f.user_name = ?)"
        "  AS following,"
        " (SELECT COUNT(*) FROM topic_stories ts WHERE ts.topic_id = t.id) AS stories"
        " FROM topics t ORDER BY t.id",
        (user_name,),
    ).fetchall()
