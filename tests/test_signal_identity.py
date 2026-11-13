"""Tests for the Signal display-name identity seam."""

from __future__ import annotations

import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from deploy_workflow.signal.identity import (
    IdentityError,
    User,
    clean_name,
    cookie_for,
    current_user,
)
from deploy_workflow.signal.store import add_user, open_db


@pytest.fixture
def db(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    conn = open_db(tmp_path)
    yield conn
    conn.close()


@contextmanager
def fresh_db() -> Iterator[sqlite3.Connection]:
    with tempfile.TemporaryDirectory() as tmp:
        conn = open_db(Path(tmp))
        try:
            yield conn
        finally:
            conn.close()


@pytest.mark.parametrize(
    "raw,want",
    [
        ("  A.  Kovac ", "A. Kovac"),
        ("A\tK\n", "A K"),
        ("x\u200by\x00z", "xyz"),
        ("<b>Eve</b>", "<b>Eve</b>"),
        ("é" * 500, "é" * 60),
        ("é", "é"),
    ],
)
def test_clean_name(raw: str, want: str) -> None:
    assert clean_name(raw) == want


@pytest.mark.parametrize("raw", ["", "   ", "\x00\u200b", "\n\t"])
def test_empty_names_are_refused(raw: str) -> None:
    with pytest.raises(IdentityError):
        clean_name(raw)


def test_cookie_round_trip_and_role(db: sqlite3.Connection) -> None:
    add_user(db, "A. Kovac", "writer")
    header = cookie_for("A. Kovac").split(";")[0]
    assert current_user(db, header) == User("A. Kovac", "writer")
    assert current_user(db, cookie_for("Nobody").split(";")[0]) == User("Nobody", "reader")
    assert current_user(db, None) is None and current_user(db, "other=1") is None
    assert current_user(db, "signal_name=%00%20") is None


def test_cookie_attributes() -> None:
    assert cookie_for("A; B").startswith("signal_name=A%3B%20B; ")
    assert all(
        part in cookie_for("x")
        for part in ("Path=/", "SameSite=Strict", "HttpOnly", "Max-Age=31536000")
    )


def test_clean_name_drops_invisible_characters_before_composing() -> None:
    raw = "e\u200b\u0301"
    assert clean_name(raw) == "é"
    assert clean_name(clean_name(raw)) == clean_name(raw)


def test_lone_surrogate_is_dropped(db: sqlite3.Connection) -> None:
    assert clean_name("Eve\ud800") == "Eve"
    assert cookie_for(clean_name("Eve\ud800")).startswith("signal_name=Eve; ")
    assert current_user(db, "signal_name=Eve\ud800") == User("Eve", "reader")


def test_quoted_cookie_value_loses_one_pair_of_quotes(db: sqlite3.Connection) -> None:
    assert current_user(db, 'signal_name="Al"') == User("Al", "reader")


@settings(deadline=None, max_examples=100)
@given(st.text(max_size=200))
def test_clean_name_is_stable_through_the_cookie(raw: str) -> None:
    try:
        name = clean_name(raw)
    except IdentityError:
        return
    assert clean_name(name) == name
    with fresh_db() as db:
        user = current_user(db, cookie_for(name).split(";")[0])
    assert user is not None and user.name == name


@settings(deadline=None, max_examples=50)
@given(st.text(max_size=300))
def test_any_cookie_header_is_safe(header: str) -> None:
    with fresh_db() as db:
        user = current_user(db, header)
        assert user is None or (0 < len(user.name) <= 60 and user.role == "reader")
