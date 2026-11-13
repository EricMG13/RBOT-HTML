"""Command line for Signal users, sources, ingest passes and stories."""

from __future__ import annotations

import argparse
import sqlite3
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from deploy_workflow.signal.fetch import FetchRefused, check_address
from deploy_workflow.signal.identity import IdentityError, clean_name
from deploy_workflow.signal.ingest import health, run_due
from deploy_workflow.signal.service import serve
from deploy_workflow.signal.store import (
    KINDS,
    ROLES,
    StoreError,
    add_user,
    open_db,
    propose_source,
    set_source_state,
    sources,
)
from deploy_workflow.signal.topics import add_topic, list_topics

LOOP_SECONDS = 60
_STORIES_SQL = """
SELECT s.id, s.title, s.published_at, src.name AS source_name,
       (SELECT COUNT(DISTINCT d.duplicate_source_id) FROM story_duplicates d
        WHERE d.story_id = s.id) AS folded
FROM stories s JOIN sources src ON src.id = s.source_id
ORDER BY s.published_at DESC, s.id DESC
LIMIT ?
"""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m deploy_workflow.signal")
    parser.add_argument("--root", type=Path, required=True, help="folder holding signal/")
    commands = parser.add_subparsers(dest="command", required=True)

    users = commands.add_parser("users").add_subparsers(dest="action", required=True)
    add = users.add_parser("add")
    add.add_argument("name")
    add.add_argument("--role", choices=ROLES, required=True)

    srcs = commands.add_parser("sources").add_subparsers(dest="action", required=True)
    propose = srcs.add_parser("propose")
    propose.add_argument("name")
    propose.add_argument("--kind", choices=KINDS, required=True)
    propose.add_argument("--url", required=True)
    propose.add_argument("--by", required=True)
    for action in ("approve", "pause"):
        srcs.add_parser(action).add_argument("id", type=int)
    srcs.add_parser("list")

    topics = commands.add_parser("topics").add_subparsers(dest="action", required=True)
    new_topic = topics.add_parser("add")
    new_topic.add_argument("name")
    new_topic.add_argument("--keywords", required=True, help="comma-separated phrases")
    new_topic.add_argument("--kinds", default="", help="comma-separated; empty means every kind")
    new_topic.add_argument("--by", required=True)
    topics.add_parser("list")

    ingest = commands.add_parser("ingest")
    ingest.add_argument("--loop", action="store_true", help="a pass every 60 seconds")

    serving = commands.add_parser("serve", help="the feed service and its ingest loop")
    serving.add_argument("--host", default="127.0.0.1")
    serving.add_argument("--port", type=int, default=8766)

    stories = commands.add_parser("stories")
    stories.add_argument("--limit", type=int, default=20)
    return parser


def _stamp(value: datetime | None, missing: str = "") -> str:
    return missing if value is None else value.astimezone(UTC).strftime("%Y-%m-%d %H:%M")


def _list_sources(db: sqlite3.Connection) -> None:
    now = datetime.now(UTC)
    for row in sources(db):
        status = health(db, row["id"], now)
        why = f"  ({status.reason})" if status.state == "failing" else ""
        print(
            f"{row['id']}  {row['state']}  {status.state}  "
            f"{_stamp(status.last_item, 'no items')}  {row['name']}{why}"
        )


def _ingest_pass(db: sqlite3.Connection) -> None:
    names = {row["id"]: row["name"] for row in sources(db)}
    for source_id, ok, reason in run_due(db, datetime.now(UTC)):
        print(f"{names[source_id]}: {'ok' if ok else 'failed'}: {reason}")


def _ingest(db: sqlite3.Connection, loop: bool) -> None:
    _ingest_pass(db)
    try:
        while loop:
            time.sleep(LOOP_SECONDS)
            _ingest_pass(db)
    except KeyboardInterrupt:
        print("stopped")


def _stories(db: sqlite3.Connection, limit: int) -> None:
    for row in db.execute(_STORIES_SQL, (limit,)):
        when = _stamp(datetime.fromisoformat(row["published_at"]))
        folded = f" (+{row['folded']})" if row["folded"] else ""
        print(f"{when}  {row['source_name']}  {row['title']}{folded}")


def _split(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


def _topics(db: sqlite3.Connection, args: argparse.Namespace) -> None:
    if args.action == "add":
        add_topic(db, args.name, _split(args.keywords), _split(args.kinds), args.by)
    else:
        for row in list_topics(db, ""):
            print(f"{row['id']}  {row['stories']}  {row['name']}")


def _dispatch(args: argparse.Namespace) -> None:
    db = open_db(args.root)
    try:
        if args.command == "users":
            add_user(db, clean_name(args.name), args.role)
        elif args.command == "sources":
            if args.action == "propose":
                check_address(args.url)
                propose_source(db, args.name, args.kind, args.url, args.by)
            elif args.action == "list":
                _list_sources(db)
            else:
                state = "approved" if args.action == "approve" else "paused"
                set_source_state(db, args.id, state)
        elif args.command == "topics":
            _topics(db, args)
        elif args.command == "ingest":
            _ingest(db, args.loop)
        else:
            _stories(db, args.limit)
    finally:
        db.close()


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command; 2 on a usage error, a store error or a refused address."""
    try:
        args = _parser().parse_args(argv)
    except SystemExit as exit_:
        return exit_.code if isinstance(exit_.code, int) else 2
    if args.command == "serve":
        return serve(args.root, args.host, args.port)
    try:
        _dispatch(args)
    except (StoreError, FetchRefused, IdentityError) as error:
        print(f"error: {error}")
        return 2
    return 0
