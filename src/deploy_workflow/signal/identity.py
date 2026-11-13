"""Display-name identity for Signal: a name in a cookie, the role from the store.

This is not authentication. The cookie is a claim; the role is looked up in the
store. The module is the whole seam the landing-page project replaces.
"""

from __future__ import annotations

import sqlite3
import unicodedata
from dataclasses import dataclass
from urllib.parse import quote, unquote

from deploy_workflow.signal.store import role_of

COOKIE = "signal_name"
MAX_NAME = 60
_MAX_AGE = 31536000
_WHITESPACE_CONTROLS = {"\t": " ", "\n": " ", "\r": " "}


class IdentityError(ValueError):
    """The display name is empty once cleaned."""


@dataclass(frozen=True)
class User:
    name: str
    role: str


def _printable(ch: str) -> str:
    if ch in _WHITESPACE_CONTROLS:
        return " "
    return "" if unicodedata.category(ch) in ("Cc", "Cf", "Cs") else ch


def _clean(raw: str) -> str:
    text = unicodedata.normalize("NFC", "".join(_printable(ch) for ch in raw))
    return " ".join(text.split())[:MAX_NAME].strip()


def clean_name(raw: str) -> str:
    """Return the cleaned display name; IdentityError when nothing is left."""
    name = _clean(raw)
    if not name:
        raise IdentityError("display name is empty")
    return name


def _cookie_value(header: str) -> str | None:
    """First `signal_name` value in a Cookie header; a plain split is safe on any text."""
    for part in header.split(";"):
        key, sep, value = part.partition("=")
        if sep and key.strip() == COOKIE:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
            return value
    return None


def current_user(db: sqlite3.Connection, cookie_header: str | None) -> User | None:
    if not cookie_header:
        return None
    value = _cookie_value(cookie_header)
    if value is None:
        return None
    # errors="replace" makes invalid UTF-8 decode to U+FFFD instead of raising.
    name = _clean(unquote(value, errors="replace"))
    if not name:
        return None
    return User(name, role_of(db, name))


def cookie_for(name: str) -> str:
    """The Set-Cookie value for a display name."""
    encoded = quote(clean_name(name), safe="")
    return f"{COOKIE}={encoded}; Path=/; Max-Age={_MAX_AGE}; SameSite=Strict; HttpOnly"
