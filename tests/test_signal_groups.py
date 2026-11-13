from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from deploy_workflow.signal import store
from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.groups import (
    Forbidden,
    add_member,
    can_see,
    create_group,
    join,
    leave,
    list_groups,
    members,
    remove_member,
    require_visible,
)
from deploy_workflow.signal.identity import User, clean_name
from deploy_workflow.signal.store import (
    StoreError,
    add_story,
    add_user,
    open_db,
    propose_source,
    set_source_state,
)

AK = User("ak", "writer")
ML = User("ml", "writer")
RD = User("rd", "reader")
T0 = datetime(2026, 11, 13, 9, tzinfo=UTC)


def team_db(tmp_path):
    """Users ak and ml (writers) and rd (reader); two approved sources with one story each."""
    db = open_db(tmp_path)
    for user in (AK, ML, RD):
        add_user(db, user.name, user.role)
    for number, kind in ((1, "regulator"), (2, "news")):
        propose_source(db, f"Source {number}", kind, f"https://s{number}.org/f", "ak")
        set_source_state(db, number, "approved")
        entry = Entry(f"Story {number}", f"https://s{number}.org/{number}", T0, f"summary {number}")
        assert add_story(db, number, entry, T0) == "new"
    return db


def rows(db, sql, *params):
    return [tuple(r) for r in db.execute(sql, params).fetchall()]


def count(db, table):
    return db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


@pytest.fixture
def db(tmp_path):
    return team_db(tmp_path)


def test_a_writer_creates_a_group_and_is_its_first_member(db):
    gid = create_group(db, AK, "  TMT analysts ", "everyone", [], T0)
    assert [tuple(r) for r in list_groups(db, "ak")] == [(gid, "TMT analysts", "everyone", 1, 1, 0)]
    assert members(db, "rd", gid) == ["ak"]


@pytest.mark.parametrize("user", [RD, User("nobody", "reader")])
def test_a_reader_cannot_create_a_group(db, user):
    with pytest.raises(Forbidden):
        create_group(db, user, "X", "everyone", [], T0)
    assert count(db, "groups") == 0


@pytest.mark.parametrize(
    "name,visibility,topics",
    [
        ("", "everyone", []),
        ("x" * 61, "everyone", []),
        ("ok", "secret", []),
        ("ok", "everyone", [99]),
    ],
)
def test_bad_group_input_is_refused(db, name, visibility, topics):
    with pytest.raises(StoreError):
        create_group(db, AK, name, visibility, topics, T0)
    assert count(db, "groups") == 0


def test_group_names_are_unique_ignoring_case(db):
    create_group(db, AK, "TMT", "everyone", [], T0)
    with pytest.raises(StoreError):
        create_group(db, ML, "tmt", "invited", [], T0)


def test_an_invited_group_is_invisible_to_non_members(db):
    gid = create_group(db, AK, "Deal team", "invited", [], T0)
    assert list_groups(db, "ml") == [] and not can_see(db, "ml", gid)
    for call in (
        lambda: require_visible(db, "ml", gid),
        lambda: members(db, "ml", gid),
        lambda: join(db, "ml", gid, T0),
        lambda: add_member(db, ML, gid, "ml", T0),
    ):
        with pytest.raises(StoreError, match="^no such group$"):
            call()
    with pytest.raises(StoreError, match="^no such group$"):
        require_visible(db, "ml", 999)  # same text as a missing group
    assert add_member(db, AK, gid, " ml ", T0) == "ml" and can_see(db, "ml", gid)


def test_a_reader_member_cannot_add_or_remove_members(db):
    gid = create_group(db, AK, "Deal team", "invited", [], T0)
    add_member(db, AK, gid, "rd", T0)
    for call in (
        lambda: add_member(db, RD, gid, "x", T0),
        lambda: remove_member(db, RD, gid, "ak"),
    ):
        with pytest.raises(Forbidden):
            call()
    assert members(db, "rd", gid) == ["ak", "rd"]


def test_join_and_leave_are_idempotent_and_open_groups_only(db):
    gid = create_group(db, AK, "TMT", "everyone", [], T0)
    join(db, "rd", gid, T0)
    join(db, "rd", gid, T0)
    assert members(db, "ak", gid) == ["ak", "rd"]
    leave(db, "rd", gid)
    leave(db, "rd", gid)
    assert members(db, "ak", gid) == ["ak"]


def test_migration_3_applies_to_a_slice_2_database_and_keeps_its_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "MIGRATIONS", store.MIGRATIONS[:2])
    old = team_db(tmp_path)
    old.execute("INSERT INTO saves(user_name, story_id, saved_at) VALUES('rd', 1, 'x')")
    old.commit()
    assert rows(old, "SELECT value FROM meta WHERE key='schema_version'") == [("2",)]
    old.close()
    monkeypatch.undo()
    new = open_db(tmp_path)
    assert rows(new, "SELECT value FROM meta WHERE key='schema_version'") == [("3",)]
    assert count(new, "stories") == 2
    assert rows(new, "SELECT user_name, story_id FROM saves") == [("rd", 1)]
    for table in ("groups", "group_members", "group_topics", "threads", "comments"):
        assert count(new, table) == 0
    for table in ("reactions", "read_marks"):
        assert count(new, table) == 0
    new.close()


@given(st.text(max_size=80))
def test_any_group_name_is_stored_cleaned_or_refused(name):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as folder:
        db = open_db(Path(folder))
        try:
            try:
                gid = create_group(db, AK, name, "everyone", [], T0)
            except StoreError:
                assert count(db, "groups") == 0
                return
            assert rows(db, "SELECT name FROM groups WHERE id=?", gid) == [(clean_name(name),)]
        finally:
            db.close()
