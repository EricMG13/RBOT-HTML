"""Groups and membership, and the one rule that decides which groups a user can see."""

from __future__ import annotations

import sqlite3
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from deploy_workflow.signal.identity import IdentityError, User, clean_name, cleaned
from deploy_workflow.signal.store import StoreError, _utc_text, _write_transaction, in_range

VISIBILITIES = ("everyone", "invited")
MAX_NAME = 60
_NO_GROUP = "no such group"


@dataclass(frozen=True)
class Act:
    """Who is acting and when."""

    user: User
    now: datetime


class Forbidden(Exception):
    """The user may not do this; the service answers 403."""


# A group the user can see: open to everyone, or the user is a member. Binds the user name once.
_VISIBLE = (
    "(g.visibility = 'everyone' OR EXISTS("
    "SELECT 1 FROM group_members vm WHERE vm.group_id = g.id AND vm.user_name = ?))"
)
_NEEDS_WRITER = "an invited group needs a writer member"


def _clean(raw: str) -> str:
    text = cleaned(raw)
    if not text:
        raise StoreError("display name is empty")
    return text


def _member_name(raw: str) -> str:
    try:
        return clean_name(raw)
    except IdentityError as exc:
        raise StoreError(str(exc)) from exc


def _name_key(name: str) -> str:
    return unicodedata.normalize("NFKC", name).casefold()


def may_post(user: User) -> bool:
    return user.role in ("writer", "owner")


def create_group(
    db: sqlite3.Connection, by: Act, name: str, visibility: str, topic_ids: Sequence[int]
) -> int:
    user = by.user
    if not may_post(user):
        raise Forbidden("only writers and the owner can create groups")
    group_name = _clean(name)
    if len(group_name) > MAX_NAME:
        raise StoreError(f"a group name is at most {MAX_NAME} characters")
    if visibility not in VISIBILITIES:
        raise StoreError(f"invalid visibility {visibility!r}; expected one of everyone, invited")
    stamp = _utc_text(by.now)
    with _write_transaction(db):
        for topic_id in topic_ids:
            if (
                not in_range(topic_id)
                or db.execute("SELECT 1 FROM topics WHERE id=?", (topic_id,)).fetchone() is None
            ):
                raise StoreError(f"no topic with id {topic_id}")
        try:
            cur = db.execute(
                "INSERT INTO groups(name, name_key, visibility, created_by, created_at)"
                " VALUES(?, ?, ?, ?, ?)",
                (group_name, _name_key(group_name), visibility, user.name, stamp),
            )
        except sqlite3.IntegrityError as exc:
            raise StoreError("that group name is taken") from exc
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
    if not in_range(group_id):
        return False
    row = db.execute(
        "SELECT 1 FROM groups g WHERE g.id = ? AND " + _VISIBLE, (group_id, user_name)
    ).fetchone()
    return row is not None


def require_visible(db: sqlite3.Connection, user_name: str, group_id: int) -> sqlite3.Row:
    """The group row; a missing group and a hidden one raise the same error."""
    if not can_see(db, user_name, group_id):
        raise StoreError(_NO_GROUP)
    row: sqlite3.Row = db.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
    return row


def can_manage(db: sqlite3.Connection, user: User, group_id: int) -> bool:
    return may_post(user) and can_see(db, user.name, group_id)


def join(db: sqlite3.Connection, user_name: str, group_id: int, now: datetime) -> None:
    """Join an open group; an invited group is only joined by being added (or already in)."""
    stamp = _utc_text(now)
    with _write_transaction(db):
        require_visible(db, user_name, group_id)
        db.execute(
            "INSERT OR IGNORE INTO group_members(group_id, user_name, joined_at) VALUES(?, ?, ?)",
            (group_id, user_name, stamp),
        )


def _drop_member(db: sqlite3.Connection, group_id: int, user_name: str) -> None:
    """Delete one membership; refuse (the caller's transaction rolls back) when that leaves an
    invited group with no manager: a member whose stored role is writer or owner, or its creator
    (who held that power when the group was made)."""
    if not in_range(group_id):
        return
    removed = db.execute(
        "DELETE FROM group_members WHERE group_id=? AND user_name=?", (group_id, user_name)
    ).rowcount
    if not removed:
        return
    orphaned = db.execute(
        "SELECT 1 FROM groups g WHERE g.id = ? AND g.visibility = 'invited' AND NOT EXISTS("
        "SELECT 1 FROM group_members m LEFT JOIN users u ON u.name = m.user_name"
        " WHERE m.group_id = g.id"
        " AND (u.role IN ('writer', 'owner') OR m.user_name = g.created_by))",
        (group_id,),
    ).fetchone()
    if orphaned:
        raise StoreError(_NEEDS_WRITER)


def leave(db: sqlite3.Connection, user_name: str, group_id: int) -> None:
    with _write_transaction(db):
        _drop_member(db, group_id, user_name)


def add_member(db: sqlite3.Connection, by: Act, group_id: int, name: str) -> str:
    actor = by.user
    stamp = _utc_text(by.now)
    with _write_transaction(db):
        require_visible(db, actor.name, group_id)
        if not may_post(actor):
            raise Forbidden("only writers and the owner can manage members")
        member = _member_name(name)
        db.execute(
            "INSERT OR IGNORE INTO group_members(group_id, user_name, joined_at) VALUES(?, ?, ?)",
            (group_id, member, stamp),
        )
    return member


def remove_member(db: sqlite3.Connection, actor: User, group_id: int, name: str) -> None:
    with _write_transaction(db):
        require_visible(db, actor.name, group_id)
        if not may_post(actor):
            raise Forbidden("only writers and the owner can manage members")
        _drop_member(db, group_id, _member_name(name))


def list_groups(db: sqlite3.Connection, user_name: str) -> list[sqlite3.Row]:
    """Visible groups by name: id, name, visibility, member flag, member and thread counts."""
    return db.execute(
        "SELECT g.id, g.name, g.visibility,"
        " EXISTS(SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_name = ?)"
        "  AS member,"
        " (SELECT COUNT(*) FROM group_members m WHERE m.group_id = g.id) AS members,"
        " (SELECT COUNT(*) FROM threads t WHERE t.group_id = g.id) AS threads"
        " FROM groups g WHERE " + _VISIBLE + " ORDER BY g.name_key, g.id",
        (user_name, user_name),
    ).fetchall()


def members(db: sqlite3.Connection, user_name: str, group_id: int) -> list[str]:
    require_visible(db, user_name, group_id)
    found = db.execute(
        "SELECT user_name FROM group_members WHERE group_id=? ORDER BY joined_at, rowid",
        (group_id,),
    ).fetchall()
    return [str(row["user_name"]) for row in found]
