"""Groups and membership, and the one rule that decides which groups a user can see."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import datetime

from deploy_workflow.signal.identity import IdentityError, User, clean_name
from deploy_workflow.signal.store import StoreError, _utc_text, _write_transaction

VISIBILITIES = ("everyone", "invited")
MAX_NAME = 60
_NO_GROUP = "no such group"


class Forbidden(Exception):
    """The user may not do this; the service answers 403."""


def _clean(raw: str) -> str:
    try:
        return clean_name(raw)
    except IdentityError as exc:
        raise StoreError(str(exc)) from exc


def _may_manage(user: User) -> bool:
    return user.role in ("writer", "owner")


def create_group(
    db: sqlite3.Connection,
    user: User,
    name: str,
    visibility: str,
    topic_ids: Sequence[int],
    now: datetime,
) -> int:
    if not _may_manage(user):
        raise Forbidden("only writers and the owner can create groups")
    cleaned = _clean(name)
    if len(" ".join(name.split())) > MAX_NAME:
        raise StoreError(f"a group name is at most {MAX_NAME} characters")
    if visibility not in VISIBILITIES:
        raise StoreError(f"invalid visibility {visibility!r}; expected one of everyone, invited")
    stamp = _utc_text(now)
    with _write_transaction(db):
        for topic_id in topic_ids:
            if db.execute("SELECT 1 FROM topics WHERE id=?", (topic_id,)).fetchone() is None:
                raise StoreError(f"no topic with id {topic_id}")
        try:
            cur = db.execute(
                "INSERT INTO groups(name, visibility, created_by, created_at) VALUES(?, ?, ?, ?)",
                (cleaned, visibility, user.name, stamp),
            )
        except sqlite3.IntegrityError as exc:
            raise StoreError(f"group {cleaned!r} already exists") from exc
        group_id = cur.lastrowid
        assert group_id is not None
        for topic_id in topic_ids:
            db.execute(
                "INSERT OR IGNORE INTO group_topics(group_id, topic_id) VALUES(?, ?)",
                (group_id, topic_id),
            )
        db.execute(
            "INSERT INTO group_members(group_id, user_name, joined_at) VALUES(?, ?, ?)",
            (group_id, user.name, stamp),
        )
    return group_id


def can_see(db: sqlite3.Connection, user_name: str, group_id: int) -> bool:
    """The group exists and is open to everyone, or the user is a member."""
    row = db.execute(
        "SELECT g.visibility = 'everyone' OR EXISTS("
        " SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_name = ?) AS seen"
        " FROM groups g WHERE g.id = ?",
        (user_name, group_id),
    ).fetchone()
    return row is not None and bool(row["seen"])


def require_visible(db: sqlite3.Connection, user_name: str, group_id: int) -> sqlite3.Row:
    """The group row; a missing group and a hidden one raise the same error."""
    if not can_see(db, user_name, group_id):
        raise StoreError(_NO_GROUP)
    row: sqlite3.Row = db.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
    return row


def can_manage(db: sqlite3.Connection, user: User, group_id: int) -> bool:
    return _may_manage(user) and can_see(db, user.name, group_id)


def join(db: sqlite3.Connection, user_name: str, group_id: int, now: datetime) -> None:
    """Join an open group; an invited group is only joined by being added (or already in)."""
    stamp = _utc_text(now)
    with _write_transaction(db):
        require_visible(db, user_name, group_id)
        db.execute(
            "INSERT OR IGNORE INTO group_members(group_id, user_name, joined_at) VALUES(?, ?, ?)",
            (group_id, user_name, stamp),
        )


def leave(db: sqlite3.Connection, user_name: str, group_id: int) -> None:
    with _write_transaction(db):
        db.execute(
            "DELETE FROM group_members WHERE group_id=? AND user_name=?", (group_id, user_name)
        )


def add_member(db: sqlite3.Connection, actor: User, group_id: int, name: str, now: datetime) -> str:
    stamp = _utc_text(now)
    with _write_transaction(db):
        require_visible(db, actor.name, group_id)
        if not _may_manage(actor):
            raise Forbidden("only writers and the owner can manage members")
        cleaned = _clean(name)
        db.execute(
            "INSERT OR IGNORE INTO group_members(group_id, user_name, joined_at) VALUES(?, ?, ?)",
            (group_id, cleaned, stamp),
        )
    return cleaned


def remove_member(db: sqlite3.Connection, actor: User, group_id: int, name: str) -> None:
    with _write_transaction(db):
        require_visible(db, actor.name, group_id)
        if not _may_manage(actor):
            raise Forbidden("only writers and the owner can manage members")
        db.execute(
            "DELETE FROM group_members WHERE group_id=? AND user_name=?",
            (group_id, _clean(name)),
        )


def list_groups(db: sqlite3.Connection, user_name: str) -> list[sqlite3.Row]:
    """Visible groups by name: id, name, visibility, member flag, member and thread counts."""
    return db.execute(
        "SELECT g.id, g.name, g.visibility,"
        " EXISTS(SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_name = ?)"
        "  AS member,"
        " (SELECT COUNT(*) FROM group_members m WHERE m.group_id = g.id) AS members,"
        " (SELECT COUNT(*) FROM threads t WHERE t.group_id = g.id) AS threads"
        " FROM groups g"
        " WHERE g.visibility = 'everyone' OR EXISTS("
        "  SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_name = ?)"
        " ORDER BY g.name COLLATE NOCASE, g.id",
        (user_name, user_name),
    ).fetchall()


def members(db: sqlite3.Connection, user_name: str, group_id: int) -> list[str]:
    require_visible(db, user_name, group_id)
    found = db.execute(
        "SELECT user_name FROM group_members WHERE group_id=? ORDER BY joined_at, rowid",
        (group_id,),
    ).fetchall()
    return [str(row["user_name"]) for row in found]
