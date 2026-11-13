from datetime import UTC, datetime

import pytest

from deploy_workflow.signal.feeds import FeedError, parse_feed

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Authority opens review</title><link>https://example.org/a</link>
<pubDate>Fri, 13 Nov 2026 09:00:00 +0100</pubDate>
<description>&lt;p&gt;Phase&amp;nbsp;two   begins &amp;amp; ends.&lt;/p&gt;</description></item>
<item><title></title><link>https://example.org/b</link></item>
<item><title>Bad link</title><link>javascript:alert(1)</link></item>
<item><title>No date</title><link>https://example.org/c</link></item>
</channel></rss>"""

ATOM = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Rating action</title>
<link rel="self" href="https://example.org/self"/><link href="https://example.org/r"/>
<updated>2026-11-12T18:30:00Z</updated><summary>Downgrade.</summary></entry></feed>"""


def test_rss_entries():
    got = parse_feed(RSS)
    assert [e.title for e in got] == ["Authority opens review", "No date"]
    assert got[0].link == "https://example.org/a"
    assert got[0].published == datetime(2026, 11, 13, 8, 0, tzinfo=UTC)
    assert got[0].summary == "Phase two begins & ends."  # the non-breaking space collapses too
    assert got[1].published is None


def test_atom_entry():
    (e,) = parse_feed(ATOM)
    assert (e.title, e.link, e.summary) == ("Rating action", "https://example.org/r", "Downgrade.")
    assert e.published == datetime(2026, 11, 12, 18, 30, tzinfo=UTC)


def test_summary_is_cut_to_300_on_a_word_boundary():
    body = RSS.replace(
        b"&lt;p&gt;Phase&amp;nbsp;two   begins &amp;amp; ends.&lt;/p&gt;", b"word " * 100
    )
    s = parse_feed(body)[0].summary
    assert len(s) <= 300 and s.endswith("word") and s == " ".join(["word"] * 60)


@pytest.mark.parametrize(
    "body",
    [
        b'<?xml version="1.0"?><!DOCTYPE rss [<!ENTITY a "b">]><rss/>',
        b"<!doctype rss><rss/>",
    ],
)
def test_dtd_or_entities_are_refused(body):
    with pytest.raises(FeedError, match="DTD or entities"):
        parse_feed(body)


@pytest.mark.parametrize("body", [b"not xml", b"<html><body/></html>", b""])
def test_non_feeds_are_refused(body):
    with pytest.raises(FeedError):
        parse_feed(body)


def _rss(item: str, head: str = "") -> bytes:
    return (f'{head}<rss version="2.0"><channel><item>{item}</item></channel></rss>').encode()


@pytest.mark.parametrize("bom", [True, False])
def test_utf16_dtd_is_refused_by_the_parser(bom):
    text = (
        '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE rss [<!ENTITY x "INJECTED">]>'
        '<rss version="2.0"><channel><item><title>&x;</title>'
        "<link>https://e.org/a</link></item></channel></rss>"
    )
    body = text.encode("utf-16") if bom else text.encode("utf-16-le")
    with pytest.raises(FeedError, match="DTD or entities"):
        parse_feed(body)


@pytest.mark.parametrize(
    "item",
    [
        "<pubDate>Fri, 31 Dec 9999 23:59:59 -0100</pubDate>",
        "<pubDate>0001-01-01T00:00:00+01:00</pubDate>",
        "<pubDate>9999-12-31T23:59:59-01:00</pubDate>",
    ],
)
def test_out_of_range_dates_give_none(item):
    (e,) = parse_feed(_rss("<title>t</title><link>https://e.org/a</link>" + item))
    assert e.published is None


def test_atom_out_of_range_date_gives_none():
    body = ATOM.replace(b"2026-11-12T18:30:00Z", b"9999-12-31T23:59:59-01:00")
    assert parse_feed(body)[0].published is None


@pytest.mark.parametrize("enc", ["shift_jis", "no-such-enc"])
def test_bad_encoding_declarations_are_feed_errors(enc):
    body = f'<?xml version="1.0" encoding="{enc}"?><rss version="2.0"><channel/></rss>'
    with pytest.raises(FeedError, match="encoding"):
        parse_feed(body.encode())


def test_nested_title_and_xhtml_text_are_read():
    (e,) = parse_feed(
        _rss(
            '<title><a href="https://e.org/a">Linked <b>head</b></a></title>'
            "<link>https://e.org/a</link>"
        )
    )
    assert e.title == "Linked head"
    atom = (
        b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:x="http://www.w3.org/1999/xhtml">'
        b'<entry><title type="xhtml"><x:div>Rated <x:b>down</x:b></x:div></title>'
        b'<link href="https://e.org/r"/><summary type="xhtml"><x:div>Cut.</x:div></summary>'
        b"</entry></feed>"
    )
    (a,) = parse_feed(atom)
    assert (a.title, a.summary) == ("Rated down", "Cut.")


def test_script_and_style_text_is_dropped_from_summary():
    desc = "&lt;style&gt;p{color:red}&lt;/style&gt;&lt;script&gt;evil()&lt;/script&gt;Kept"
    (e,) = parse_feed(
        _rss(f"<title>t</title><link>https://e.org/a</link><description>{desc}</description>")
    )
    assert e.summary == "Kept"


def test_iso_date_in_rss_is_accepted():
    (e,) = parse_feed(
        _rss("<title>t</title><link>https://e.org/a</link><pubDate>2026-11-12T18:30:00Z</pubDate>")
    )
    assert e.published == datetime(2026, 11, 12, 18, 30, tzinfo=UTC)


def test_entity_at_the_boundary_is_not_cut_mid_entity():
    desc = "a " * 149 + "&amp;&amp; tail"  # the first '&' decodes to character 299
    (e,) = parse_feed(
        _rss(f"<title>t</title><link>https://e.org/a</link><description>{desc}</description>")
    )
    assert "&amp" not in e.summary and "&&" in e.summary and len(e.summary) <= 300


def test_entries_with_malformed_links_are_skipped():
    links = [
        "https://example.org:abc/x",
        "https://[::1/x",
        "http://example.org:99999/x",
        "https:///x",
        "https://example.org/good",
    ]
    items = "".join(
        f"<item><title>Story {i}</title><link>{u}</link></item>" for i, u in enumerate(links)
    )
    body = f"<rss version='2.0'><channel>{items}</channel></rss>".encode()
    assert [e.link for e in parse_feed(body)] == ["https://example.org/good"]
