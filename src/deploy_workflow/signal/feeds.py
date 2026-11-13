"""Parse RSS 2.0 and Atom feed bytes into entries. Standard library only.

Feed bytes are untrusted: a DTD or entity declaration is refused before parsing, and
no article body is fetched; only the feed's own title, link, date and summary are read.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit

SUMMARY_LIMIT = 300
_ATOM = "{http://www.w3.org/2005/Atom}"
_DTD = re.compile(rb"<!(DOCTYPE|ENTITY)", re.IGNORECASE)


_DTD_MESSAGE = "feed declares a DTD or entities"


class FeedError(ValueError):
    """The feed cannot be read; the message is shown to the owner."""


class _RefuseDoctype(ET.TreeBuilder):
    """Tree builder that refuses any doctype, whatever the body's encoding."""

    def doctype(self, name: str, pubid: str, system: str) -> None:
        raise FeedError(_DTD_MESSAGE)


@dataclass(frozen=True)
class Entry:
    title: str
    link: str
    published: datetime | None
    summary: str


class _TextOnly(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def _summary(raw: str) -> str:
    parser = _TextOnly()
    parser.feed(raw)
    parser.close()
    text = " ".join("".join(parser.parts).split())
    if len(text) <= SUMMARY_LIMIT:
        return text
    head = text[: SUMMARY_LIMIT + 1]
    if " " not in head:
        return text[:SUMMARY_LIMIT]
    return head.rsplit(" ", 1)[0].rstrip()


def _utc(moment: datetime) -> datetime:
    # A date with no zone is read as UTC.
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def _iso_date(text: str) -> datetime | None:
    try:
        return _utc(datetime.fromisoformat(text.strip()))
    except (ValueError, OverflowError):
        return None


def _rss_date(text: str) -> datetime | None:
    try:
        return _utc(parsedate_to_datetime(text))
    except (ValueError, OverflowError):
        return _iso_date(text)


def _text(parent: ET.Element, tag: str) -> str:
    child = parent.find(tag)
    return "".join(child.itertext()).strip() if child is not None else ""


def _usable_link(link: str) -> bool:
    """An http(s) link whose host is present and whose port, if any, parses."""
    if not link.lower().startswith(("http://", "https://")):
        return False
    try:
        parts = urlsplit(link)
        return bool(parts.hostname) and (parts.port is None or parts.port > 0)
    except ValueError:
        return False


def _make(title: str, link: str, date: datetime | None, summary: str) -> Entry | None:
    if not title or not _usable_link(link):
        return None
    return Entry(title, link, date, _summary(summary))


def _rss_entry(item: ET.Element) -> Entry | None:
    pub = _text(item, "pubDate")
    date = _rss_date(pub) if pub else None
    return _make(
        " ".join(_text(item, "title").split()),
        _text(item, "link"),
        date,
        _text(item, "description"),
    )


def _atom_link(entry: ET.Element) -> str:
    for link in entry.findall(f"{_ATOM}link"):
        if link.get("rel") in (None, "alternate"):
            return (link.get("href") or "").strip()
    return ""


def _atom_entry(entry: ET.Element) -> Entry | None:
    stamp = _text(entry, f"{_ATOM}published") or _text(entry, f"{_ATOM}updated")
    date = _iso_date(stamp) if stamp else None
    return _make(
        " ".join(_text(entry, f"{_ATOM}title").split()),
        _atom_link(entry),
        date,
        _text(entry, f"{_ATOM}summary"),
    )


def parse_feed(body: bytes) -> list[Entry]:
    """Return the readable entries of an RSS 2.0 or Atom feed, in feed order."""
    if _DTD.search(body):
        raise FeedError(_DTD_MESSAGE)
    try:
        parser = ET.XMLParser(target=_RefuseDoctype())
        parser.feed(body)
        root = parser.close()
    except ET.ParseError as exc:
        raise FeedError("feed is not valid XML") from exc
    except FeedError:
        raise
    except (ValueError, LookupError) as exc:
        raise FeedError(f"feed uses an unsupported text encoding ({exc})") from exc
    if root.tag == "rss":
        found = (_rss_entry(item) for item in root.findall("channel/item"))
    elif root.tag == f"{_ATOM}feed":
        found = (_atom_entry(entry) for entry in root.findall(f"{_ATOM}entry"))
    else:
        raise FeedError("document is neither an RSS 2.0 nor an Atom feed")
    return [entry for entry in found if entry is not None]
