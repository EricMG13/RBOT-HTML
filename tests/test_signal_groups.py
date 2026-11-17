from datetime import UTC, datetime

import pytest
from hypothesis import given
from hypothesis import strategies as st

from deploy_workflow.signal import store
from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.groups import (
    Act,
    Forbidden,
    _name_key,
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
    gid = create_group(db, Act(AK, T0), "  TMT analysts ", "everyone", [])
    assert [tuple(r) for r in list_groups(db, "ak")] == [(gid, "TMT analysts", "everyone", 1, 1, 0)]
    assert members(db, "rd", gid) == ["ak"]


@pytest.mark.parametrize("user", [RD, User("nobody", "reader")])
def test_a_reader_cannot_create_a_group(db, user):
    with pytest.raises(Forbidden):
        create_group(db, Act(user, T0), "X", "everyone", [])
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
        create_group(db, Act(AK, T0), name, visibility, topics)
    assert count(db, "groups") == 0


def test_group_names_are_unique_ignoring_case(db):
    create_group(db, Act(AK, T0), "TMT", "everyone", [])
    with pytest.raises(StoreError):
        create_group(db, Act(ML, T0), "tmt", "invited", [])


def test_an_invited_group_is_invisible_to_non_members(db):
    gid = create_group(db, Act(AK, T0), "Deal team", "invited", [])
    assert list_groups(db, "ml") == [] and not can_see(db, "ml", gid)
    for call in (
        lambda: require_visible(db, "ml", gid),
        lambda: members(db, "ml", gid),
        lambda: join(db, "ml", gid, T0),
        lambda: add_member(db, Act(ML, T0), gid, "ml"),
    ):
        with pytest.raises(StoreError, match="^no such group$"):
            call()
    with pytest.raises(StoreError, match="^no such group$"):
        require_visible(db, "ml", 999)  # same text as a missing group
    assert add_member(db, Act(AK, T0), gid, " ml ") == "ml" and can_see(db, "ml", gid)


def test_a_reader_member_cannot_add_or_remove_members(db):
    gid = create_group(db, Act(AK, T0), "Deal team", "invited", [])
    add_member(db, Act(AK, T0), gid, "rd")
    for call in (
        lambda: add_member(db, Act(RD, T0), gid, "x"),
        lambda: remove_member(db, RD, gid, "ak"),
    ):
        with pytest.raises(Forbidden):
            call()
    assert members(db, "rd", gid) == ["ak", "rd"]


def test_join_and_leave_are_idempotent_and_open_groups_only(db):
    gid = create_group(db, Act(AK, T0), "TMT", "everyone", [])
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
                gid = create_group(db, Act(AK, T0), name, "everyone", [])
            except StoreError:
                assert count(db, "groups") == 0
                return
            assert rows(db, "SELECT name FROM groups WHERE id=?", gid) == [(clean_name(name),)]
        finally:
            db.close()


def test_a_name_of_sixty_visible_characters_with_controls_is_accepted(db):
    gid = create_group(db, Act(AK, T0), "x" * 30 + "\x00\x01" + "y" * 30, "everyone", [])
    assert rows(db, "SELECT name FROM groups WHERE id=?", gid) == [("x" * 30 + "y" * 30,)]


def test_name_length_is_judged_after_nfc(db):
    decomposed = "é" * 40  # 80 code points, 40 after NFC
    gid = create_group(db, Act(AK, T0), decomposed, "everyone", [])
    assert rows(db, "SELECT name FROM groups WHERE id=?", gid) == [("é" * 40,)]
    with pytest.raises(StoreError):  # 60 raw characters, 120 once composed
        create_group(db, Act(AK, T0), "क़" * 60, "everyone", [])
    assert count(db, "groups") == 1


@pytest.mark.parametrize(
    "first,second",
    [
        ("Télécoms", "TÉLÉCOMS"),
        ("Télécoms", "Télécoms"),
        ("Ωmega desk", "ωmega desk"),
        ("Straße", "STRASSE"),
    ],
)
def test_group_names_are_unique_across_unicode_case_and_forms(db, first, second):
    create_group(db, Act(AK, T0), first, "invited", [])
    with pytest.raises(StoreError, match="^that group name is taken$"):
        create_group(db, Act(ML, T0), second, "everyone", [])
    assert count(db, "groups") == 1


def test_an_invited_group_keeps_a_writer_member(db):
    gid = create_group(db, Act(AK, T0), "Deal team", "invited", [])
    add_member(db, Act(AK, T0), gid, "rd")
    for call in (lambda: leave(db, "ak", gid), lambda: remove_member(db, AK, gid, "ak")):
        with pytest.raises(StoreError, match="^an invited group needs a writer member$"):
            call()
    assert members(db, "ak", gid) == ["ak", "rd"]
    add_member(db, Act(AK, T0), gid, "ml")
    leave(db, "ak", gid)
    assert members(db, "ml", gid) == ["rd", "ml"]
    open_group = create_group(db, Act(ML, T0), "Open", "everyone", [])
    leave(db, "ml", open_group)
    assert members(db, "rd", open_group) == []


@pytest.mark.parametrize("gid", [2**63 - 1, 2**63, -(2**63) - 1])
def test_ids_outside_the_sqlite_range_are_missing_ids(db, gid):
    assert can_see(db, "ak", gid) is False
    assert list_groups(db, "ak") == []
    leave(db, "ak", gid)
    for call in (
        lambda: require_visible(db, "ak", gid),
        lambda: members(db, "ak", gid),
        lambda: join(db, "ak", gid, T0),
        lambda: add_member(db, Act(AK, T0), gid, "x"),
        lambda: remove_member(db, AK, gid, "x"),
    ):
        with pytest.raises(StoreError, match="^no such group$"):
            call()
    with pytest.raises(StoreError):
        create_group(db, Act(AK, T0), "T", "everyone", [gid])
    assert count(db, "groups") == 0


@pytest.mark.parametrize(
    ("first", "second"),
    [("x\u03b0", "x\u03ab\u0301"), ("x\u1fd2", "x\u03aa\u0300"), ("x\u1fd7", "x\u03aa\u0342")],
)
def test_names_equal_after_case_folding_and_compatibility_share_one_key(first, second):
    assert _name_key(first) == _name_key(second)
