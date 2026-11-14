"""SQLite store for Signal users, sources, checks and stories."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.fold import MIN_TITLE_WORDS, TITLE_WINDOW, link_key, title_key

ROLES = ("reader", "writer", "owner")
KINDS = ("regulator", "news", "ratings", "research")
STATES = ("proposed", "approved", "paused")


class StoreError(ValueError):
    """An invalid role, kind, state, empty name or duplicate."""


_MIGRATION_1 = """
CREATE TABLE users(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL
);
CREATE TABLE sources(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL,
    proposed_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE source_checks(
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    at TEXT NOT NULL,
    ok INTEGER NOT NULL,
    reason TEXT NOT NULL,
    etag TEXT,
    modified TEXT,
    new_stories INTEGER NOT NULL
);
CREATE TABLE stories(
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    link_key TEXT NOT NULL,
    title_key TEXT NOT NULL,
    published_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    summary TEXT NOT NULL,
    UNIQUE(source_id, link_key)
);
CREATE TABLE story_duplicates(
    story_id INTEGER NOT NULL REFERENCES stories(id),
    duplicate_source_id INTEGER NOT NULL REFERENCES sources(id),
    link TEXT NOT NULL,
    link_key TEXT NOT NULL,
    published_at TEXT NOT NULL,
    seen_at TEXT NOT NULL,
    UNIQUE(duplicate_source_id, link_key)
);
CREATE INDEX IF NOT EXISTS idx_story_duplicates_link_key ON story_duplicates(link_key);
CREATE VIRTUAL TABLE stories_fts USING fts5(
    title, summary, content='stories', content_rowid='id'
);
CREATE TRIGGER stories_ai AFTER INSERT ON stories BEGIN
    INSERT INTO stories_fts(rowid, title, summary) VALUES (new.id, new.title, new.summary);
END;
CREATE TRIGGER stories_ad AFTER DELETE ON stories BEGIN
    INSERT INTO stories_fts(stories_fts, rowid, title, summary)
    VALUES ('delete', old.id, old.title, old.summary);
END;
CREATE TRIGGER stories_au AFTER UPDATE ON stories BEGIN
    INSERT INTO stories_fts(stories_fts, rowid, title, summary)
    VALUES ('delete', old.id, old.title, old.summary);
    INSERT INTO stories_fts(rowid, title, summary) VALUES (new.id, new.title, new.summary);
END;
"""

_MIGRATION_2 = """
CREATE TABLE topics(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    keywords TEXT NOT NULL,
    kinds TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE topic_stories(
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    story_id INTEGER NOT NULL REFERENCES stories(id),
    UNIQUE(topic_id, story_id)
);
CREATE TABLE topic_follows(
    user_name TEXT NOT NULL,
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    UNIQUE(user_name, topic_id)
);
CREATE TABLE saves(
    user_name TEXT NOT NULL,
    story_id INTEGER NOT NULL REFERENCES stories(id),
    saved_at TEXT NOT NULL,
    UNIQUE(user_name, story_id)
);
CREATE INDEX IF NOT EXISTS idx_story_duplicates_story_id ON story_duplicates(story_id);
CREATE INDEX IF NOT EXISTS idx_stories_published_at_id ON stories(published_at, id);
CREATE INDEX IF NOT EXISTS idx_topic_stories_story_id ON topic_stories(story_id);
CREATE INDEX IF NOT EXISTS idx_stories_link_key ON stories(link_key);
CREATE INDEX IF NOT EXISTS idx_stories_title_key ON stories(title_key);
"""

_MIGRATION_3 = """
CREATE TABLE groups(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_key TEXT NOT NULL UNIQUE,
    visibility TEXT NOT NULL CHECK(visibility IN ('everyone', 'invited')),
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE group_members(
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_name TEXT NOT NULL,
    joined_at TEXT NOT NULL,
    UNIQUE(group_id, user_name)
);
CREATE TABLE group_topics(
    group_id INTEGER NOT NULL REFERENCES groups(id),
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    UNIQUE(group_id, topic_id)
);
CREATE TABLE threads(
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    story_id INTEGER REFERENCES stories(id),
    title TEXT,
    started_by TEXT,
    created_at TEXT NOT NULL,
    last_activity_at TEXT NOT NULL,
    UNIQUE(group_id, story_id),
    CHECK((story_id IS NULL) <> (title IS NULL))
);
CREATE TABLE comments(
    id INTEGER PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    parent_id INTEGER REFERENCES comments(id),
    author TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    edited_at TEXT,
    deleted_at TEXT
);
CREATE TABLE reactions(
    comment_id INTEGER NOT NULL REFERENCES comments(id),
    user_name TEXT NOT NULL,
    key TEXT NOT NULL,
    UNIQUE(comment_id, user_name, key)
);
CREATE TABLE read_marks(
    user_name TEXT NOT NULL,
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    seen_comment_id INTEGER NOT NULL,
    UNIQUE(user_name, thread_id)
);
CREATE INDEX IF NOT EXISTS idx_threads_group_activity ON threads(group_id, last_activity_at, id);
CREATE INDEX IF NOT EXISTS idx_threads_story_id ON threads(story_id);
CREATE INDEX IF NOT EXISTS idx_comments_thread_id ON comments(thread_id, id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_name);
"""

# Ordered; later slices append. Index i holds the script that brings the schema to version i + 1.
MIGRATIONS = [_MIGRATION_1, _MIGRATION_2, _MIGRATION_3]
_BUSY_SECONDS = 30


def _schema_version(db: sqlite3.Connection) -> int:
    has_meta = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'"
    ).fetchone()
    if has_meta is None:
        return 0
    row = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    return int(row[0]) if row else 0


@contextmanager
def _write_transaction(db: sqlite3.Connection) -> Iterator[None]:
    """Hold the write lock: commit when the block ends, roll back if it raises."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield
        db.execute("COMMIT")
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise


def _apply_migration(db: sqlite3.Connection, version: int) -> None:
    """Apply one migration under the write lock; skip it if another opener already did."""
    with _write_transaction(db):
        if _schema_version(db) >= version:
            return
        db.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.executescript(MIGRATIONS[version - 1])
        db.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
            (str(version),),
        )


def _migrate(db: sqlite3.Connection) -> None:
    # executescript leaves an explicit transaction alone only outside legacy transaction control.
    db.autocommit = True
    try:
        for version in range(1, len(MIGRATIONS) + 1):
            if _schema_version(db) < version:
                _apply_migration(db, version)
    finally:
        db.autocommit = sqlite3.LEGACY_TRANSACTION_CONTROL


def _enable_wal(db: sqlite3.Connection) -> None:
    """Switch to WAL. SQLite ignores the busy timeout for this pragma on a fresh file that
    another opener is initialising, so retry on "locked" until the same 30 s deadline."""
    deadline = time.monotonic() + _BUSY_SECONDS
    while True:
        try:
            mode = db.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            break
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc) or time.monotonic() >= deadline:
                raise
            time.sleep(0.02)
    if str(mode).lower() != "wal":
        raise StoreError(f"could not enable WAL mode; database reports {mode!r}")


def open_db(root: Path) -> sqlite3.Connection:
    """Open (creating if needed) `<root>/signal/signal.db` and apply migrations."""
    folder = root / "signal"
    folder.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(folder / "signal.db", timeout=_BUSY_SECONDS)
    try:
        db.row_factory = sqlite3.Row
        _enable_wal(db)
        db.execute("PRAGMA foreign_keys=ON")
        _migrate(db)
    except BaseException:
        db.close()
        raise
    return db


def set_meta(db: sqlite3.Connection, key: str, value: str) -> None:
    with db:
        db.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value))


def get_meta(db: sqlite3.Connection, key: str) -> str | None:
    row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return str(row["value"]) if row else None


def in_range(number: int) -> bool:
    """Whether SQLite can hold the id; anything else is an id no row has."""
    return -(2**63) <= number <= 2**63 - 1


def _utc_text(at: datetime) -> str:
    if at.tzinfo is None or at.utcoffset() is None:
        raise StoreError("time must be timezone-aware")
    return at.astimezone(UTC).isoformat()


def _require(value: str, allowed: tuple[str, ...], what: str) -> None:
    if value not in allowed:
        raise StoreError(f"invalid {what} {value!r}; expected one of {', '.join(allowed)}")


def _require_name(name: str) -> None:
    if not name.strip():
        raise StoreError("name must not be empty")


def add_user(db: sqlite3.Connection, name: str, role: str) -> int:
    _require_name(name)
    _require(role, ROLES, "role")
    try:
        with db:
            cur = db.execute("INSERT INTO users(name, role) VALUES(?, ?)", (name, role))
    except sqlite3.IntegrityError as exc:
        raise StoreError(f"user {name!r} already exists") from exc
    assert cur.lastrowid is not None
    return cur.lastrowid


def role_of(db: sqlite3.Connection, name: str) -> str:
    row = db.execute("SELECT role FROM users WHERE name=?", (name,)).fetchone()
    return str(row["role"]) if row else "reader"


def propose_source(db: sqlite3.Connection, name: str, kind: str, url: str, proposed_by: str) -> int:
    _require_name(name)
    _require(kind, KINDS, "kind")
    if not url.strip():
        raise StoreError("url must not be empty")
    try:
        with db:
            cur = db.execute(
                "INSERT INTO sources(name, kind, url, state, proposed_by, created_at)"
                " VALUES(?, ?, ?, 'proposed', ?, ?)",
                (name, kind, url, proposed_by, _utc_text(datetime.now(UTC))),
            )
    except sqlite3.IntegrityError as exc:
        raise StoreError(f"source url {url!r} already exists") from exc
    assert cur.lastrowid is not None
    return cur.lastrowid


def set_source_state(db: sqlite3.Connection, source_id: int, state: str) -> None:
    _require(state, STATES, "state")
    with db:
        cur = db.execute("UPDATE sources SET state=? WHERE id=?", (state, source_id))
    if cur.rowcount == 0:
        raise StoreError(f"no source with id {source_id}")


def sources(db: sqlite3.Connection, state: str | None = None) -> list[sqlite3.Row]:
    if state is None:
        return db.execute("SELECT * FROM sources ORDER BY id").fetchall()
    _require(state, STATES, "state")
    return db.execute("SELECT * FROM sources WHERE state=? ORDER BY id", (state,)).fetchall()


@dataclass(frozen=True)
class Check:
    """The outcome of one fetch of a source."""

    at: datetime
    ok: bool
    reason: str
    etag: str | None
    modified: str | None
    new_stories: int


def record_check(db: sqlite3.Connection, source_id: int, check: Check) -> None:
    stamp = _utc_text(check.at)
    try:
        with db:
            db.execute(
                "INSERT INTO source_checks(source_id, at, ok, reason, etag, modified, new_stories)"
                " VALUES(?, ?, ?, ?, ?, ?, ?)",
                (
                    source_id,
                    stamp,
                    int(check.ok),
                    check.reason,
                    check.etag,
                    check.modified,
                    check.new_stories,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise StoreError(f"no source with id {source_id}") from exc


def last_check(db: sqlite3.Connection, source_id: int) -> sqlite3.Row | None:
    row: sqlite3.Row | None = db.execute(
        "SELECT * FROM source_checks WHERE source_id=? ORDER BY at DESC, id DESC LIMIT 1",
        (source_id,),
    ).fetchone()
    return row


def _earliest_match(
    db: sqlite3.Connection, source_id: int, lkey: str, tkey: str, published: datetime
) -> int | None:
    """Id of the earliest story with this link key (as a story or a folded duplicate), or, from
    another source, this title key within the window. A source never folds into itself by title."""
    rows = db.execute(
        "SELECT id, published_at, link_key = ? AS same_link FROM stories"
        " WHERE link_key = ? OR (title_key = ? AND source_id != ?)"
        " UNION ALL"
        " SELECT s.id, s.published_at, 1 AS same_link FROM story_duplicates d"
        " JOIN stories s ON s.id = d.story_id WHERE d.link_key = ? AND s.source_id != ?",
        (lkey, lkey, tkey, source_id, lkey, source_id),
    ).fetchall()
    long_title = len(tkey.split()) >= MIN_TITLE_WORDS
    found: list[tuple[datetime, int]] = []
    for row in rows:
        at = datetime.fromisoformat(row["published_at"])
        if row["same_link"] or (long_title and abs(at - published) <= TITLE_WINDOW):
            found.append((at, row["id"]))
    return min(found)[1] if found else None


def _fold_or_insert(
    db: sqlite3.Connection, source_id: int, entry: Entry, fetched_at: datetime
) -> Literal["new", "duplicate", "seen"]:
    if entry.published is not None:
        _utc_text(entry.published)  # refuses a time without a zone
    lkey = link_key(entry.link)
    tkey = title_key(entry.title)
    if db.execute(
        "SELECT 1 FROM stories WHERE source_id=? AND link_key=?"
        " UNION ALL SELECT 1 FROM story_duplicates WHERE duplicate_source_id=? AND link_key=?",
        (source_id, lkey, source_id, lkey),
    ).fetchone():
        return "seen"
    published = entry.published
    if published is None or published > fetched_at:
        published = fetched_at
    stamp = _utc_text(published)
    story_id = _earliest_match(db, source_id, lkey, tkey, published)
    if story_id is not None:
        db.execute(
            "INSERT INTO story_duplicates(story_id, duplicate_source_id, link, link_key,"
            " published_at, seen_at) VALUES(?, ?, ?, ?, ?, ?)",
            (story_id, source_id, entry.link, lkey, stamp, _utc_text(fetched_at)),
        )
        return "duplicate"
    db.execute(
        "INSERT INTO stories(source_id, title, link, link_key, title_key, published_at,"
        " fetched_at, summary) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
        (
            source_id,
            entry.title,
            entry.link,
            lkey,
            tkey,
            stamp,
            _utc_text(fetched_at),
            entry.summary,
        ),
    )
    return "new"


def add_story(
    db: sqlite3.Connection, source_id: int, entry: Entry, fetched_at: datetime
) -> Literal["new", "duplicate", "seen"]:
    """Store `entry` unless this source has it ("seen") or another story folds it ("duplicate").

    The check and the write share one write-locked transaction, so two writers cannot both
    insert the same story."""
    with _write_transaction(db):
        return _fold_or_insert(db, source_id, entry, fetched_at)
