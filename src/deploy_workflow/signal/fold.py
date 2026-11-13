"""Keys and rules for deciding that two feed entries are the same story."""

from __future__ import annotations

import re
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit

TITLE_WINDOW = timedelta(hours=48)
MIN_TITLE_WORDS = 4

_TRACKING_NAMES = ("fbclid", "gclid")
_RUN = re.compile(r"[\W_]+")


def _is_tracking(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith("utm_") or lowered in _TRACKING_NAMES


def link_key(link: str) -> str:
    """Host without `www.`, path without a trailing slash, tracking parameters dropped."""
    parts = urlsplit(link.strip())
    host = (parts.hostname or "").removeprefix("www.")
    if parts.port is not None:
        host = f"{host}:{parts.port}"
    kept = sorted(
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _is_tracking(k)
    )
    query = f"?{urlencode(kept)}" if kept else ""
    return f"{host}{parts.path.rstrip('/')}{query}"


def title_key(title: str) -> str:
    """Case-folded title with every run of non-alphanumeric characters as one space."""
    return _RUN.sub(" ", title.casefold()).strip()
