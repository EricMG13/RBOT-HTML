import sqlite3
import threading
from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st
from test_signal_groups import AK, ML, RD, T0, count, rows, team_db

from deploy_workflow.signal import feedview
from deploy_workflow.signal.groups import Act, Forbidden, create_group
from deploy_workflow.signal.store import StoreError, open_db
from deploy_workflow.signal.threads import (
    EDIT_WINDOW,
    MAX_COMMENTS,
    MAX_TEXT,
    MAX_TITLE,
    REACTIONS,
    add_comment,
    auto_post,
    clean_text,
    delete_comment,
    edit_comment,
    react,
    read_thread,
    share_story,
    start_note,
    thread_list,
    unreact,
)

MIN = timedelta(minutes=1)


@pytest.fixture
def db(tmp_path):
    return team_db(tmp_path)


@pytest.fixture
def gid(db):
    return create_group(db, Act(AK, T0), "TMT", "everyone", [])


def test_first_share_starts_a_thread_and_a_second_share_joins_it(db, gid):
    assert share_story(db, Act(AK, T0), gid, 1, "Heavier than we assumed.") == (1, False)
    assert share_story(db, Act(ML, T0 + MIN), gid, 1, None) == (1, True)
    assert share_story(db, Act(ML, T0 + 2 * MIN), gid, 1, "Agree.") == (1, True)
    view = read_thread(db, RD, 1, T0 + 3 * MIN)
    assert [(c.author, c.text) for c in view.comments] == [
        ("ak", "Heavier than we assumed."),
        ("ml", "Agree."),
    ]
    assert view.story.id == 1 and view.started_by == "ak" and view.can_post is False


def test_two_shares_at_once_make_one_thread(tmp_path):
    first = team_db(tmp_path)
    gid = create_group(first, Act(AK, T0), "TMT", "everyone", [])
    barrier = threading.Barrier(2)
    results, errors = [], []

    def run(user):
        try:
            conn = open_db(tmp_path)
            barrier.wait()
            results.append(share_story(conn, Act(user, T0), gid, 1, None))
        except (StoreError, sqlite3.Error) as exc:
            errors.append(exc)

    workers = [
        threading.Thread(target=run, args=(AK,)),
        threading.Thread(target=run, args=(ML,)),
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    assert errors == []
    assert count(first, "threads") == 1
    assert sorted(joined for _, joined in results) == [False, True]


def test_a_reader_cannot_share_post_react_edit_or_delete(db, gid):
    tid, _ = share_story(db, Act(AK, T0), gid, 1, "note")
    for call in (
        lambda: share_story(db, Act(RD, T0), gid, 2, None),
        lambda: start_note(db, Act(RD, T0), gid, "T", "x"),
        lambda: add_comment(db, Act(RD, T0), tid, "x", None),
        lambda: react(db, RD, 1, "up"),
        lambda: edit_comment(db, Act(RD, T0), 1, "x"),
        lambda: delete_comment(db, Act(RD, T0), 1),
    ):
        with pytest.raises(Forbidden):
            call()
    assert count(db, "threads") == 1 and count(db, "comments") == 1 and count(db, "reactions") == 0


def test_an_invited_groups_thread_does_not_exist_for_a_non_member(db):
    gid = create_group(db, Act(AK, T0), "Deal team", "invited", [])
    tid, _ = share_story(db, Act(AK, T0), gid, 1, "private")
    for call in (
        lambda: read_thread(db, ML, tid, T0),
        lambda: add_comment(db, Act(ML, T0), tid, "x", None),
        lambda: read_thread(db, ML, 999, T0),
        lambda: read_thread(db, ML, 2**70, T0),
    ):
        with pytest.raises(StoreError, match="^no such thread$"):
            call()
    for call in (
        lambda: react(db, ML, 1, "up"),
        lambda: edit_comment(db, Act(ML, T0), 1, "x"),
        lambda: delete_comment(db, Act(ML, T0), 1),
        lambda: react(db, ML, 2**70, "up"),
    ):
        with pytest.raises(StoreError, match="^no such comment$"):
            call()
    for call in (
        lambda: thread_list(db, "ml", gid, None),
        lambda: share_story(db, Act(ML, T0), gid, 2, None),
        lambda: start_note(db, Act(ML, T0), gid, "T", "x"),
    ):
        with pytest.raises(StoreError, match="^no such group$"):
            call()


def test_replies_nest_one_level(db, gid):
    tid, _ = share_story(db, Act(AK, T0), gid, 1, "top")  # comment 1
    r = add_comment(db, Act(ML, T0), tid, "reply", 1)  # comment 2
    with pytest.raises(StoreError):
        add_comment(db, Act(AK, T0), tid, "reply to a reply", r)
    other, _ = share_story(db, Act(AK, T0), gid, 2, "other thread")  # comment 3
    with pytest.raises(StoreError):
        add_comment(db, Act(AK, T0), other, "wrong thread", 1)
    delete_comment(db, Act(AK, T0), 1)
    assert add_comment(db, Act(ML, T0), tid, "after removal", 1) == 4


@pytest.mark.parametrize(
    "after,allowed",
    [(timedelta(minutes=15), True), (timedelta(minutes=15, seconds=1), False)],
)
def test_the_edit_window_is_15_minutes_inclusive(db, gid, after, allowed):
    assert EDIT_WINDOW == timedelta(minutes=15)
    tid, _ = share_story(db, Act(AK, T0), gid, 1, "first")
    if allowed:
        edit_comment(db, Act(AK, T0 + after), 1, "second")
    else:
        with pytest.raises(Forbidden):
            edit_comment(db, Act(AK, T0 + after), 1, "second")
    (c,) = read_thread(db, AK, tid, T0 + after).comments
    assert (c.text, c.edited) == (("second", True) if allowed else ("first", False))
    assert c.editable is allowed or after > EDIT_WINDOW


def test_only_the_author_edits_or_deletes_and_a_removed_comment_keeps_its_place(db, gid):
    tid, _ = share_story(db, Act(AK, T0), gid, 1, "mine")
    react(db, ML, 1, "eyes")
    for call in (
        lambda: edit_comment(db, Act(ML, T0), 1, "x"),
        lambda: delete_comment(db, Act(ML, T0), 1),
    ):
        with pytest.raises(Forbidden):
            call()
    delete_comment(db, Act(AK, T0 + timedelta(days=30)), 1)
    delete_comment(db, Act(AK, T0 + timedelta(days=30)), 1)
    c = read_thread(db, AK, tid, T0).comments[0]
    assert (c.removed, c.text, c.reactions, c.author) == (True, "", (), "ak")
    assert rows(db, "SELECT text FROM comments WHERE id=1") == [("",)]
    assert count(db, "reactions") == 0
    with pytest.raises(Forbidden):
        edit_comment(db, Act(AK, T0), 1, "back")
    with pytest.raises(StoreError):
        react(db, ML, 1, "up")


def test_reactions_are_a_fixed_set_counted_per_key_and_idempotent(db, gid):
    tid, _ = share_story(db, Act(AK, T0), gid, 1, "x")
    react(db, AK, 1, "up")
    react(db, AK, 1, "up")
    react(db, ML, 1, "up")
    react(db, ML, 1, "eyes")
    got = read_thread(db, AK, tid, T0).comments[0].reactions
    assert tuple((r.key, r.count, r.mine) for r in got) == (("up", 2, True), ("eyes", 1, False))
    assert REACTIONS == ("up", "eyes", "check", "question")
    with pytest.raises(StoreError):
        react(db, AK, 1, "fire")
    unreact(db, ML, 1, "up")
    unreact(db, ML, 1, "up")
    got = read_thread(db, AK, tid, T0).comments[0].reactions
    assert tuple((r.key, r.count) for r in got) == (("up", 1), ("eyes", 1))


def test_a_comment_carries_its_authors_current_role(db, gid):
    tid, _ = share_story(db, Act(ML, T0), gid, 1, "x")
    db.execute("UPDATE users SET role='owner' WHERE name='ml'")
    db.commit()
    assert read_thread(db, RD, tid, T0).comments[0].role == "owner"


@pytest.mark.parametrize(
    "raw,stored", [("  hi \r\n there\x00\u202e ", "hi \n there"), ("e\u0301", "\u00e9")]
)
def test_text_is_cleaned(raw, stored):
    assert clean_text(raw, MAX_TEXT) == stored


@pytest.mark.parametrize("raw", ["", "   ", "\u200b", "x" * 4001])
def test_empty_or_oversized_text_is_refused(raw):
    with pytest.raises(StoreError):
        clean_text(raw, MAX_TEXT)


def test_a_title_over_the_limit_is_refused_not_cut(db, gid):
    with pytest.raises(StoreError):
        start_note(db, Act(AK, T0), gid, "t" * (MAX_TITLE + 1), "x")
    assert count(db, "threads") == 0


def test_markup_is_stored_as_typed(db, gid):
    tid = start_note(
        db, Act(AK, T0), gid, "<b>t</b>", "<img src=x onerror=alert(1)> javascript:alert(1)"
    )
    view = read_thread(db, AK, tid, T0)
    assert view.title == "<b>t</b>" and view.comments[0].text.startswith("<img")
    assert view.story is None


def test_the_501st_comment_is_refused(db, gid):
    tid, _ = share_story(db, Act(AK, T0), gid, 1, "first")
    for number in range(MAX_COMMENTS - 1):
        add_comment(db, Act(AK, T0), tid, f"c{number}", None)
    assert count(db, "comments") == MAX_COMMENTS
    with pytest.raises(StoreError, match="^this thread is full$"):
        add_comment(db, Act(ML, T0), tid, "one too many", None)
    with pytest.raises(StoreError, match="^this thread is full$"):
        share_story(db, Act(ML, T0), gid, 1, "one too many")
    assert count(db, "comments") == MAX_COMMENTS


def test_thread_list_is_by_last_activity_and_pages_by_30(db, gid):
    for number in range(31):
        start_note(db, Act(AK, T0 + number * MIN), gid, f"note {number}", "x")
    add_comment(db, Act(ML, T0 + 60 * MIN), 1, "bump", None)
    first, cursor = thread_list(db, "rd", gid, None)
    assert [row.id for row in first][:2] == [1, 31] and len(first) == 30
    assert cursor is not None
    second, end = thread_list(db, "rd", gid, cursor)
    assert [row.id for row in second] == [2] and end is None
    assert first[0].kind == "note" and first[0].title == "note 0" and first[0].comments == 2
    assert first[0].unread is True and thread_list(db, "ak", gid, None)[0][1].unread is False


def test_a_story_thread_lists_the_story_title_and_source(db, gid):
    share_story(db, Act(AK, T0), gid, 2, None)
    ((row,), _) = thread_list(db, "ak", gid, None)
    assert (row.kind, row.title, row.source, row.comments) == ("story", "Story 2", "Source 2", 0)


def test_a_malformed_cursor_is_refused(db, gid):
    with pytest.raises(feedview.ViewError):
        thread_list(db, "ak", gid, "nonsense")


def test_auto_post_makes_one_unattributed_thread_per_matching_group(db):
    first = create_group(db, Act(AK, T0), "A", "everyone", [])
    second = create_group(db, Act(AK, T0), "B", "invited", [])
    db.execute(
        "INSERT INTO topics(name, keywords, kinds, created_by, created_at)"
        " VALUES('x', '[]', '[]', 'ak', 'now')"
    )
    db.execute("INSERT INTO group_topics(group_id, topic_id) VALUES(?, 1)", (first,))
    db.execute("INSERT INTO group_topics(group_id, topic_id) VALUES(?, 1)", (second,))
    db.commit()
    assert auto_post(db, 1, [1, 1], T0) == [1, 2]
    assert auto_post(db, 1, [1], T0) == []
    assert auto_post(db, 1, [], T0) == []
    assert auto_post(db, 999, [1], T0) == []
    assert rows(db, "SELECT group_id, story_id, started_by FROM threads ORDER BY id") == [
        (first, 1, None),
        (second, 1, None),
    ]


@given(st.text(max_size=200))
def test_any_text_is_cleaned_or_refused_never_an_error(raw):
    try:
        text = clean_text(raw, MAX_TEXT)
    except StoreError:
        return
    import unicodedata

    assert text and all(
        ch == "\n" or unicodedata.category(ch) not in ("Cc", "Cf", "Cs") for ch in text
    )
