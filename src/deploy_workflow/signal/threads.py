"""Threads, comments and reactions inside groups.

Order of checks everywhere: visibility (a hidden group answers like a missing one), then role,
then input."""

from __future__ import annotations

import sqlite3
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from deploy_workflow.signal import feedview
from deploy_workflow.signal.groups import (
    VISIBLE,
    Act,
    Forbidden,
    can_see,
    may_post,
    require_visible,
)
from deploy_workflow.signal.identity import User
from deploy_workflow.signal.store import (
    StoreError,
    _utc_text,
    _write_transaction,
    in_range,
    role_of,
)

EDIT_WINDOW = timedelta(minutes=15)
MAX_TEXT = 4000
MAX_TITLE = 120
MAX_COMMENTS = 500
REACTIONS = ("up", "eyes", "check", "question")
PAGE = 30
_NO_THREAD = "no such thread"
_NO_COMMENT = "no such comment"


@dataclass(frozen=True)
class Reaction:
    key: str
    count: int
    mine: bool


@dataclass(frozen=True)
class Comment:
    id: int
    parent_id: int | None
    author: str
    role: str
    text: str
    created_at: str
    edited: bool
    removed: bool
    reactions: tuple[Reaction, ...]
    mine: bool
    editable: bool


@dataclass(frozen=True)
class ThreadView:
    id: int
    group_id: int
    group: str
    story: feedview.Card | None
    title: str | None
    started_by: str | None
    comments: tuple[Comment, ...]
    can_post: bool


@dataclass(frozen=True)
class Unread:
    replies: int
    threads: int
    by_group: dict[int, int]


@dataclass(frozen=True)
class ThreadRow:
    id: int
    kind: Literal["story", "note"]
    title: str
    source: str | None
    source_kind: str | None
    started_by: str | None
    comments: int
    last_activity_at: str
    unread: bool


def _normalised(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    kept = "".join(
        ch for ch in text if ch == "\n" or unicodedata.category(ch) not in ("Cc", "Cf", "Cs")
    )
    return unicodedata.normalize("NFC", kept).strip()


def clean_text(raw: str, limit: int) -> str:
    """Plain text as stored: controls (except newline), format and surrogate characters dropped,
    newlines unified, NFC, trimmed. Empty or longer than `limit` is refused, never cut."""
    text = _normalised(raw)
    if not text:
        raise StoreError("text is empty")
    if len(text) > limit:
        raise StoreError(f"text is longer than {limit} characters")
    return text


def _thread_row(db: sqlite3.Connection, user_name: str, thread_id: int) -> sqlite3.Row:
    """The thread row when its group is visible; a missing and a hidden thread look the same."""
    row = (
        db.execute("SELECT * FROM threads WHERE id=?", (thread_id,)).fetchone()
        if in_range(thread_id)
        else None
    )
    if row is None or not can_see(db, user_name, row["group_id"]):
        raise StoreError(_NO_THREAD)
    result: sqlite3.Row = row
    return result


def _comment_row(db: sqlite3.Connection, user_name: str, comment_id: int) -> sqlite3.Row:
    """The comment row when its thread's group is visible, else "no such comment"."""
    row = (
        db.execute(
            "SELECT c.*, t.group_id FROM comments c JOIN threads t ON t.id = c.thread_id"
            " WHERE c.id=?",
            (comment_id,),
        ).fetchone()
        if in_range(comment_id)
        else None
    )
    if row is None or not can_see(db, user_name, row["group_id"]):
        raise StoreError(_NO_COMMENT)
    result: sqlite3.Row = row
    return result


def _insert_comment(
    db: sqlite3.Connection, by: Act, thread_id: int, parent_id: int | None, text: str
) -> int:
    """Append a comment (the caller holds the write transaction and has cleaned the text)."""
    stamp = _utc_text(by.now)
    taken = db.execute("SELECT COUNT(*) FROM comments WHERE thread_id=?", (thread_id,)).fetchone()
    if taken[0] >= MAX_COMMENTS:
        raise StoreError("this thread is full")
    cur = db.execute(
        "INSERT INTO comments(thread_id, parent_id, author, text, created_at)"
        " VALUES(?, ?, ?, ?, ?)",
        (thread_id, parent_id, by.user.name, text, stamp),
    )
    db.execute(
        "UPDATE threads SET last_activity_at = MAX(last_activity_at, ?) WHERE id=?",
        (stamp, thread_id),
    )
    comment_id = cur.lastrowid
    assert comment_id is not None
    return comment_id


def share_story(
    db: sqlite3.Connection, by: Act, group_id: int, story_id: int, note: str | None
) -> tuple[int, bool]:
    """Put a story in a group: `(thread_id, joined)`, joined when the thread already existed."""
    user, stamp = by.user, _utc_text(by.now)
    with _write_transaction(db):
        require_visible(db, user.name, group_id)
        if not may_post(user):
            raise Forbidden("only writers and the owner can share stories")
        exists = (
            in_range(story_id)
            and db.execute("SELECT 1 FROM stories WHERE id=?", (story_id,)).fetchone()
        )
        if not exists:
            raise StoreError(f"no story with id {story_id}")
        text = _normalised(note) if note is not None else ""
        if len(text) > MAX_TEXT:
            raise StoreError(f"text is longer than {MAX_TEXT} characters")
        cur = db.execute(
            "INSERT OR IGNORE INTO threads(group_id, story_id, started_by, created_at,"
            " last_activity_at) VALUES(?, ?, ?, ?, ?)",
            (group_id, story_id, user.name, stamp, stamp),
        )
        joined = cur.rowcount == 0
        if joined:
            found = db.execute(
                "SELECT id FROM threads WHERE group_id=? AND story_id=?", (group_id, story_id)
            ).fetchone()
            thread_id = int(found["id"])
        else:
            assert cur.lastrowid is not None
            thread_id = cur.lastrowid
        if text:
            _insert_comment(db, by, thread_id, None, text)
    return thread_id, joined


def start_note(db: sqlite3.Connection, by: Act, group_id: int, title: str, text: str) -> int:
    """A thread with no story; the text is its first comment."""
    user, stamp = by.user, _utc_text(by.now)
    with _write_transaction(db):
        require_visible(db, user.name, group_id)
        if not may_post(user):
            raise Forbidden("only writers and the owner can start notes")
        clean_title = clean_text(title, MAX_TITLE)
        body = clean_text(text, MAX_TEXT)
        cur = db.execute(
            "INSERT INTO threads(group_id, title, started_by, created_at, last_activity_at)"
            " VALUES(?, ?, ?, ?, ?)",
            (group_id, clean_title, user.name, stamp, stamp),
        )
        thread_id = cur.lastrowid
        assert thread_id is not None
        _insert_comment(db, by, thread_id, None, body)
    return thread_id


def auto_post(
    db: sqlite3.Connection, story_id: int, topic_ids: Sequence[int], now: datetime
) -> list[int]:
    """A thread for the story in each group carrying one of the topics, unless one exists.
    Returns the new thread ids."""
    if not topic_ids:
        return []
    stamp = _utc_text(now)
    marks = ", ".join("?" * len(topic_ids))
    created: list[int] = []
    with _write_transaction(db):
        groups = db.execute(
            "SELECT DISTINCT gt.group_id FROM group_topics gt"
            " WHERE gt.topic_id IN (" + marks + ")"
            " AND EXISTS(SELECT 1 FROM stories WHERE id=?) ORDER BY gt.group_id",
            [*topic_ids, story_id],
        ).fetchall()
        for row in groups:
            cur = db.execute(
                "INSERT OR IGNORE INTO threads(group_id, story_id, started_by, created_at,"
                " last_activity_at) VALUES(?, ?, NULL, ?, ?)",
                (row["group_id"], story_id, stamp, stamp),
            )
            if cur.rowcount and cur.lastrowid is not None:
                created.append(cur.lastrowid)
    return created


def add_comment(
    db: sqlite3.Connection, by: Act, thread_id: int, text: str, parent_id: int | None
) -> int:
    user = by.user
    with _write_transaction(db):
        _thread_row(db, user.name, thread_id)
        if not may_post(user):
            raise Forbidden("only writers and the owner can comment")
        body = clean_text(text, MAX_TEXT)
        if parent_id is not None:
            parent = (
                db.execute(
                    "SELECT thread_id, parent_id FROM comments WHERE id=?", (parent_id,)
                ).fetchone()
                if in_range(parent_id)
                else None
            )
            if parent is None or parent["thread_id"] != thread_id:
                raise StoreError("no such comment in this thread to reply to")
            if parent["parent_id"] is not None:
                raise StoreError("replies nest one level; reply to the top-level comment")
        return _insert_comment(db, by, thread_id, parent_id, body)


def edit_comment(db: sqlite3.Connection, by: Act, comment_id: int, text: str) -> None:
    user, stamp = by.user, _utc_text(by.now)
    with _write_transaction(db):
        row = _comment_row(db, user.name, comment_id)
        if row["author"] != user.name or row["deleted_at"] is not None:
            raise Forbidden("only the author can edit a comment, and not a removed one")
        if by.now - datetime.fromisoformat(row["created_at"]) > EDIT_WINDOW:
            raise Forbidden("a comment can be edited for 15 minutes")
        body = clean_text(text, MAX_TEXT)
        db.execute(
            "UPDATE comments SET text=?, edited_at=? WHERE id=?",
            (body, stamp, comment_id),
        )


def delete_comment(db: sqlite3.Connection, by: Act, comment_id: int) -> None:
    """Remove a comment: it keeps its place, loses its text and reactions. Repeating is safe."""
    user, stamp = by.user, _utc_text(by.now)
    with _write_transaction(db):
        row = _comment_row(db, user.name, comment_id)
        if row["author"] != user.name:
            raise Forbidden("only the author can delete a comment")
        if row["deleted_at"] is not None:
            return
        db.execute(
            "UPDATE comments SET text='', deleted_at=? WHERE id=?",
            (stamp, comment_id),
        )
        db.execute("DELETE FROM reactions WHERE comment_id=?", (comment_id,))


def _reaction_target(db: sqlite3.Connection, user: User, comment_id: int, key: str) -> None:
    row = _comment_row(db, user.name, comment_id)
    if not may_post(user):
        raise Forbidden("only writers and the owner can react")
    if key not in REACTIONS:
        raise StoreError(f"invalid reaction {key!r}; expected one of {', '.join(REACTIONS)}")
    if row["deleted_at"] is not None:
        raise StoreError("that comment was removed")


def react(db: sqlite3.Connection, user: User, comment_id: int, key: str) -> None:
    with _write_transaction(db):
        _reaction_target(db, user, comment_id, key)
        db.execute(
            "INSERT OR IGNORE INTO reactions(comment_id, user_name, key) VALUES(?, ?, ?)",
            (comment_id, user.name, key),
        )


def unreact(db: sqlite3.Connection, user: User, comment_id: int, key: str) -> None:
    with _write_transaction(db):
        _reaction_target(db, user, comment_id, key)
        db.execute(
            "DELETE FROM reactions WHERE comment_id=? AND user_name=? AND key=?",
            (comment_id, user.name, key),
        )


def _reactions(
    db: sqlite3.Connection, thread_id: int, user_name: str
) -> dict[int, tuple[Reaction, ...]]:
    found = db.execute(
        "SELECT r.comment_id, r.key, COUNT(*) AS n, MAX(r.user_name = ?) AS mine"
        " FROM reactions r JOIN comments c ON c.id = r.comment_id WHERE c.thread_id=?"
        " GROUP BY r.comment_id, r.key",
        (user_name, thread_id),
    ).fetchall()
    by_comment: dict[int, dict[str, Reaction]] = {}
    for row in found:
        by_comment.setdefault(row["comment_id"], {})[row["key"]] = Reaction(
            row["key"], row["n"], bool(row["mine"])
        )
    return {
        comment_id: tuple(keyed[key] for key in REACTIONS if key in keyed)
        for comment_id, keyed in by_comment.items()
    }


def _comments(
    db: sqlite3.Connection, thread_id: int, user: User, now: datetime
) -> tuple[Comment, ...]:
    reactions = _reactions(db, thread_id, user.name)
    roles: dict[str, str] = {}
    out: list[Comment] = []
    for row in db.execute(
        "SELECT * FROM comments WHERE thread_id=? ORDER BY id", (thread_id,)
    ).fetchall():
        author = row["author"]
        if author not in roles:
            roles[author] = role_of(db, author)
        removed = row["deleted_at"] is not None
        mine = author == user.name
        out.append(
            Comment(
                id=row["id"],
                parent_id=row["parent_id"],
                author=author,
                role=roles[author],
                text=row["text"],
                created_at=row["created_at"],
                edited=row["edited_at"] is not None,
                removed=removed,
                reactions=reactions.get(row["id"], ()),
                mine=mine,
                editable=mine
                and not removed
                and now - datetime.fromisoformat(row["created_at"]) <= EDIT_WINDOW,
            )
        )
    return tuple(out)


def read_thread(db: sqlite3.Connection, user: User, thread_id: int, now: datetime) -> ThreadView:
    _utc_text(now)  # refuse a naive time here, as every other entry point does
    with feedview._snapshot(db):
        thread = _thread_row(db, user.name, thread_id)
        group = require_visible(db, user.name, thread["group_id"])
        story = (
            feedview.card_for(db, user.name, thread["story_id"])
            if thread["story_id"] is not None
            else None
        )
        return ThreadView(
            id=thread["id"],
            group_id=group["id"],
            group=group["name"],
            story=story,
            title=thread["title"],
            started_by=thread["started_by"],
            comments=_comments(db, thread["id"], user, now),
            can_post=may_post(user),
        )


def _before(before: str) -> tuple[str, int]:
    stamp, comma, number = before.rpartition(",")
    if not comma:
        raise feedview.ViewError(f"malformed cursor {before!r}")
    return feedview._instant(stamp, "cursor time"), feedview._id(number, "cursor id")


# A thread that is new to the user (alias t; binds the user name three times): in a group they
# belong to, made at or after they joined, started by someone else (not automatic), never read.
_NEW_THREAD = (
    "(t.started_by IS NOT NULL AND t.started_by <> ?"
    " AND EXISTS(SELECT 1 FROM group_members m WHERE m.group_id = t.group_id AND m.user_name = ?"
    "  AND t.created_at >= m.joined_at)"
    " AND NOT EXISTS(SELECT 1 FROM read_marks r WHERE r.user_name = ? AND r.thread_id = t.id))"
)

_ROWS = (
    "SELECT t.id, t.story_id, COALESCE(s.title, t.title) AS title, src.name AS source,"
    " src.kind AS source_kind, t.started_by, t.last_activity_at,"
    " (SELECT COUNT(*) FROM comments c WHERE c.thread_id = t.id AND c.deleted_at IS NULL)"
    "  AS comments,"
    " (" + _NEW_THREAD + " OR EXISTS(SELECT 1 FROM comments c WHERE c.thread_id = t.id"
    "  AND c.deleted_at IS NULL AND c.author <> ? AND c.id > COALESCE((SELECT r.seen_comment_id"
    "   FROM read_marks r WHERE r.user_name = ? AND r.thread_id = t.id), 0))) AS unread"
    " FROM threads t LEFT JOIN stories s ON s.id = t.story_id"
    " LEFT JOIN sources src ON src.id = s.source_id WHERE t.group_id = ?"
)


def thread_list(
    db: sqlite3.Connection, user_name: str, group_id: int, before: str | None
) -> tuple[tuple[ThreadRow, ...], str | None]:
    """One page of a group's threads by last activity, newest first, and the next cursor."""
    with feedview._snapshot(db):
        require_visible(db, user_name, group_id)
        sql = _ROWS
        params: list[object] = [user_name] * 5 + [group_id]
        if before is not None:
            stamp, thread_id = _before(before)
            sql += " AND (t.last_activity_at < ? OR (t.last_activity_at = ? AND t.id < ?))"
            params += [stamp, stamp, thread_id]
        found = db.execute(
            sql + " ORDER BY t.last_activity_at DESC, t.id DESC LIMIT ?", [*params, PAGE + 1]
        ).fetchall()
    page = tuple(
        ThreadRow(
            id=row["id"],
            kind="story" if row["story_id"] is not None else "note",
            title=row["title"],
            source=row["source"],
            source_kind=row["source_kind"],
            started_by=row["started_by"],
            comments=row["comments"],
            last_activity_at=row["last_activity_at"],
            unread=bool(row["unread"]),
        )
        for row in found[:PAGE]
    )
    last = page[-1] if len(found) > PAGE else None
    return page, f"{last.last_activity_at},{last.id}" if last else None


def mark_read(db: sqlite3.Connection, user_name: str, thread_id: int) -> None:
    """Mark everything in the thread seen; the mark only ever rises."""
    with _write_transaction(db):
        _thread_row(db, user_name, thread_id)
        newest = db.execute(
            "SELECT COALESCE(MAX(id), 0) FROM comments WHERE thread_id=?", (thread_id,)
        ).fetchone()[0]
        db.execute(
            "INSERT INTO read_marks(user_name, thread_id, seen_comment_id) VALUES(?, ?, ?)"
            " ON CONFLICT(user_name, thread_id) DO UPDATE SET"
            " seen_comment_id = MAX(seen_comment_id, excluded.seen_comment_id)",
            (user_name, thread_id, newest),
        )


_UNREAD_THREADS = (
    "SELECT t.group_id AS gid, COUNT(*) AS n FROM threads t WHERE "
    + _NEW_THREAD
    + " GROUP BY t.group_id"
)
_UNREAD_REPLIES = (
    "SELECT t.group_id AS gid, COUNT(*) AS n FROM comments c"
    " JOIN comments p ON p.id = c.parent_id JOIN threads t ON t.id = c.thread_id"
    " JOIN groups g ON g.id = t.group_id"
    " WHERE " + VISIBLE + " AND c.deleted_at IS NULL AND c.author <> ? AND p.author = ?"
    " AND c.id > COALESCE((SELECT r.seen_comment_id FROM read_marks r"
    "  WHERE r.user_name = ? AND r.thread_id = t.id), 0)"
    " GROUP BY t.group_id"
)


def unread(db: sqlite3.Connection, user_name: str) -> Unread:
    """New threads in the user's groups and replies to the user's comments, not yet read."""
    with feedview._snapshot(db):
        new_threads = db.execute(_UNREAD_THREADS, (user_name, user_name, user_name)).fetchall()
        replies = db.execute(
            _UNREAD_REPLIES, (user_name, user_name, user_name, user_name)
        ).fetchall()
    by_group: dict[int, int] = {}
    for row in (*new_threads, *replies):
        by_group[row["gid"]] = by_group.get(row["gid"], 0) + row["n"]
    return Unread(
        replies=sum(row["n"] for row in replies),
        threads=sum(row["n"] for row in new_threads),
        by_group=by_group,
    )
