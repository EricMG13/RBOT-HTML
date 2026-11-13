"""Fetch rules for Signal, on injected resolver, connector and clock: nothing touches a network."""

import http.client
import ssl
import time
from collections.abc import Callable, Iterable, Mapping
from typing import Any

import pytest

from deploy_workflow.research import webfetch
from deploy_workflow.research.webfetch import ConnectionTarget
from deploy_workflow.signal import fetch as fetch_module
from deploy_workflow.signal.fetch import (
    MAX_BYTES,
    Fetched,
    FetchRefused,
    Wiring,
    check_address,
    fetch,
)

PUBLIC_IP = "93.184.216.34"
URL = "https://feeds.example.org/x"


def PUBLIC(host: str) -> Iterable[str]:
    return [PUBLIC_IP]


def _map(host: str) -> Iterable[str]:
    return ["10.0.0.1"] if host == "internal.example" else [PUBLIC_IP]


class Reply:
    def __init__(
        self,
        status: int,
        body: bytes = b"",
        headers: Mapping[str, str] | None = None,
        on_read: Callable[[], None] | None = None,
    ) -> None:
        self.status = status
        self.headers = {name.lower(): value for name, value in (headers or {}).items()}
        self.body = body
        self.consumed = 0
        self.on_read = on_read

    def getheader(self, name: str, /) -> str | None:
        return self.headers.get(name.lower())

    def read(self, amt: int) -> bytes:
        if self.on_read is not None:
            self.on_read()
        chunk = self.body[self.consumed : self.consumed + amt]
        self.consumed += len(chunk)
        return chunk


def redirect(location: str | None, status: int = 302) -> Reply:
    return Reply(status, b"r" * 100, {"Location": location} if location else None)


class Wire:
    """A connector that answers each request from a script, in order, and records what it saw."""

    def __init__(self, *replies: Reply | Exception) -> None:
        self.script = list(replies)
        self.targets: list[ConnectionTarget] = []
        self.requests: list[tuple[str, dict[str, str]]] = []
        self.closed = 0
        self.on_response: Callable[[], None] = lambda: None

    def __call__(self, target: ConnectionTarget) -> "Wire":
        self.targets.append(target)
        return self

    def request(self, method: str, url: str, *, headers: Mapping[str, str]) -> None:
        assert method == "GET"
        self.requests.append((url, dict(headers)))

    def getresponse(self) -> Reply:
        self.on_response()
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step

    def close(self) -> None:
        self.closed += 1


class Counting:
    """A resolver that answers from a list, one answer per call, then repeats the last."""

    def __init__(self, *answers: list[str]) -> None:
        self.answers = list(answers)
        self.calls: list[str] = []

    def __call__(self, host: str) -> Iterable[str]:
        self.calls.append(host)
        return self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def run(
    wire: Wire, url: str = URL, etag: str | None = None, modified: str | None = None, **kw: Any
):
    kw.setdefault("resolve", _map)
    clock = kw.pop("clock", time.monotonic)
    return fetch(url, etag, modified, wiring=Wiring(wire, clock), **kw)


def ok() -> Reply:
    return Reply(200, b"<rss/>")


@pytest.mark.parametrize(
    "url",
    ["http://example.org/feed", "ftp://example.org/f", "https:///nohost", "file:///etc/passwd"],
)
def test_only_https_with_a_host(url):
    with pytest.raises(FetchRefused):
        check_address(url, resolve=PUBLIC)


NON_PUBLIC = [
    "127.0.0.1",
    "10.0.0.5",
    "192.168.1.1",
    "169.254.169.254",
    "::1",
    "fc00::1",
    "0.0.0.0",
    "fec0::1",
    "fec0:0:0:ffff::1",
    "ff02::1",
    "ff05::2",
    "224.0.0.1",
    "64:ff9b::a9fe:a9fe",
    "64:ff9b::7f00:1",
    "::a9fe:a9fe",
    "::7f00:1",
    "64:ff9b::808:808",
    "::ffff:127.0.0.1",
]


@pytest.mark.parametrize("addr", NON_PUBLIC)
def test_non_public_addresses_are_refused(addr):
    with pytest.raises(FetchRefused, match="public"):
        check_address(URL, resolve=lambda h: [addr])


@pytest.mark.parametrize("addr", NON_PUBLIC)
def test_a_redirect_hop_to_a_non_public_address_is_refused(addr):
    wire = Wire(redirect("https://other.example.org/y"), ok())

    def resolve(host: str) -> Iterable[str]:
        return [addr] if host == "other.example.org" else [PUBLIC_IP]

    with pytest.raises(FetchRefused, match="public"):
        run(wire, resolve=resolve)
    assert [t.host for t in wire.targets] == ["feeds.example.org"]


def test_one_private_address_among_public_is_refused():
    with pytest.raises(FetchRefused):
        check_address(URL, resolve=lambda h: [PUBLIC_IP, "10.0.0.1"])


def test_public_https_passes():
    check_address(URL, resolve=PUBLIC)
    check_address("https://feeds-1.example.org:8443/x", resolve=PUBLIC)
    check_address("https://WWW.Example.org/feed", resolve=PUBLIC)


def test_check_address_looks_the_resolver_up_at_call_time(monkeypatch):
    monkeypatch.setattr(fetch_module, "_resolve", lambda host: ["10.0.0.1"])
    with pytest.raises(FetchRefused, match="public"):
        check_address(URL)
    with pytest.raises(FetchRefused, match="public"):
        fetch(URL, None, None, wiring=Wiring(Wire(ok())))


def test_unresolvable_host_is_refused():
    def fail(host: str) -> Iterable[str]:
        raise OSError("name not known")

    with pytest.raises(FetchRefused, match="name not known"):
        check_address(URL, resolve=fail)
    with pytest.raises(FetchRefused, match="resolved to no address"):
        check_address(URL, resolve=lambda h: [])


@pytest.mark.parametrize(
    "url",
    [
        "https://cdn%2einternal.attacker.test/",
        "https://user@feeds.example.org/",
        "https://feeds.example.org\\@evil.example/",
        "https://127.0.0.1/",
        "https://[::1]/",
        "https://[::ffff:169.254.169.254]/",
        "https://2130706433/",
        "https://0x7f.1/",
        "https://127.1/",
        "https://münchen.example/",
        "https://localhost/",
        "https://-a.example.org/",
        "https://a-.example.org/",
        "https://a..example.org/",
        "https://feeds.example.org./",
        f"https://{'a' * 64}.example.org/",
        "https://Keeds.example.org/feed",  # Kelvin sign lower-cases to "k"
    ],
)
def test_host_must_be_a_plain_name(url):
    with pytest.raises(FetchRefused, match="plain host name"):
        check_address(url, resolve=PUBLIC)
    wire = Wire(ok())
    with pytest.raises(FetchRefused):
        run(wire, url)
    assert not wire.targets


@pytest.mark.parametrize("url", ["https://[::1/x", "https://feeds.example.org:99999/x"])
def test_unparseable_addresses_are_refused(url):
    with pytest.raises(FetchRefused):
        check_address(url, resolve=PUBLIC)


def test_non_ascii_start_path_is_refused():
    wire = Wire(ok())
    with pytest.raises(FetchRefused):
        run(wire, "https://feeds.example.org/actualités")
    assert not wire.targets


def test_private_start_address_is_refused_before_any_connection():
    wire = Wire(ok())
    with pytest.raises(FetchRefused, match="public"):
        run(wire, "https://internal.example/x")
    assert not wire.targets


# M1: the connection goes to the address that was checked.
def test_no_second_lookup_changes_where_the_request_goes():
    resolver = Counting([PUBLIC_IP, "93.184.216.35"], ["127.0.0.1"])
    wire = Wire(ok())
    run(wire, resolve=resolver)
    assert resolver.calls == ["feeds.example.org"]
    assert [t.ip for t in wire.targets] == [PUBLIC_IP]
    assert wire.targets[0].port == 443
    assert wire.targets[0].timeout == fetch_module.TIMEOUT_SECONDS


def test_each_hop_is_resolved_once_and_pinned_to_its_own_checked_address():
    answers = {"feeds.example.org": ["93.184.216.34"], "other.example.org": ["93.184.216.99"]}
    calls: list[str] = []

    def resolve(host: str) -> Iterable[str]:
        calls.append(host)
        return answers[host]

    wire = Wire(redirect("https://other.example.org/y"), ok())
    run(wire, resolve=resolve)
    assert calls == ["feeds.example.org", "other.example.org"]
    assert [(t.host, t.ip) for t in wire.targets] == [
        ("feeds.example.org", "93.184.216.34"),
        ("other.example.org", "93.184.216.99"),
    ]


def test_the_production_connector_is_pinned_to_the_checked_address(monkeypatch):
    built: list[dict[str, Any]] = []

    class Capture(Wire):
        def __init__(self, host: str, ip: str, **kwargs: Any) -> None:
            super().__init__(ok())
            built.append({"host": host, "ip": ip, **kwargs})

    monkeypatch.setattr(webfetch, "PinnedHTTPSConnection", Capture)
    monkeypatch.setattr(webfetch, "tls_context", lambda: "context")
    got = fetch(URL, None, None, resolve=PUBLIC)
    assert got.body == b"<rss/>"
    assert len(built) == 1
    assert (built[0]["host"], built[0]["ip"], built[0]["port"]) == (
        "feeds.example.org",
        PUBLIC_IP,
        443,
    )
    assert built[0]["timeout"] == fetch_module.TIMEOUT_SECONDS


# Redirects
def test_redirect_to_http_is_refused():
    with pytest.raises(FetchRefused, match="https"):
        run(Wire(redirect("http://feeds.example.org/y")))


def test_redirect_to_a_public_https_address_is_followed_and_its_body_not_read():
    first = redirect("https://other.example.org/y")
    wire = Wire(first, ok())
    got = run(wire)
    assert got.body == b"<rss/>"
    assert [url for url, _ in wire.requests] == ["/x", "/y"]
    assert first.consumed == 0
    assert wire.closed == 2


def test_relative_location_is_resolved_against_the_current_url():
    wire = Wire(redirect("/other?a=1"), ok())
    run(wire, "https://feeds.example.org/dir/x")
    assert wire.requests[1][0] == "/other?a=1"
    assert wire.targets[1].host == "feeds.example.org"


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_each_redirect_status_is_followed(status):
    assert run(Wire(redirect("https://other.example.org/y", status), ok())).body == b"<rss/>"


@pytest.mark.parametrize(
    "location",
    [
        "https://other.example:8443/",
        "https://other.example.org:444/",
        "http://other.example.org/",
        "https://127.0.0.1/",
        "https://[::1]/",
        "https://user@other.example.org/",
        "https://cdn%2einternal.attacker.test/feed",
        "https://[::1",
        "https://[feeds.example.org]/feed",
        "https://internal.example/",
        "",
        None,
    ],
)
def test_unacceptable_redirect_targets_are_refused(location):
    wire = Wire(redirect(location), ok())
    with pytest.raises(FetchRefused):
        run(wire)
    assert len(wire.targets) == 1
    assert wire.closed == 1


def test_an_explicit_default_port_on_a_redirect_is_accepted():
    wire = Wire(redirect("https://other.example.org:443/y"), ok())
    run(wire)
    assert wire.targets[1].port == 443


def test_validators_go_to_the_first_address_only():
    wire = Wire(redirect("https://other.example.org/y"), ok())
    run(wire, etag='"abc"', modified="Fri, 13 Nov 2026 09:00:00 GMT")
    first, second = (headers for _, headers in wire.requests)
    assert first["If-None-Match"] == '"abc"'
    assert first["If-Modified-Since"] == "Fri, 13 Nov 2026 09:00:00 GMT"
    assert "If-None-Match" not in second and "If-Modified-Since" not in second
    assert second["Host"] == "other.example.org"


def test_more_than_three_redirects_are_refused():
    wire = Wire(*[redirect(f"https://feeds.example.org/{i + 1}") for i in range(10)])
    with pytest.raises(FetchRefused, match="more than 3 redirects"):
        run(wire, "https://feeds.example.org/0")
    assert len(wire.targets) == 4


def test_three_redirects_then_the_feed_succeed():
    wire = Wire(*[redirect(f"https://feeds.example.org/{i + 1}") for i in range(3)], ok())
    assert run(wire, "https://feeds.example.org/0").body == b"<rss/>"


# Request headers
def test_headers_sent_on_the_first_request():
    wire = Wire(ok())
    run(wire, etag=None, modified=None)
    ((path, headers),) = wire.requests
    assert path == "/x"
    assert set(headers) == {"Host", "User-Agent", "Accept", "Accept-Encoding", "Connection"}
    assert headers["User-Agent"] == fetch_module.USER_AGENT
    assert headers["Accept-Encoding"] == "identity"


def test_identity_encoding_is_asked_for_on_every_hop():
    wire = Wire(redirect("https://other.example.org/y"), ok())
    run(wire)
    assert [headers["Accept-Encoding"] for _, headers in wire.requests] == ["identity", "identity"]


def test_a_port_on_the_first_address_is_connected_to_and_named_in_host():
    wire = Wire(ok())
    run(wire, "https://feeds-1.example.org:8443/x")
    assert wire.targets[0].port == 8443
    assert wire.requests[0][1]["Host"] == "feeds-1.example.org:8443"


# Status and body
def test_304_returns_no_body_and_the_validators_sent():  # none came back, so the sent ones stay
    wire = Wire(Reply(304))
    got = run(wire, etag='"abc"', modified="Fri, 13 Nov 2026 09:00:00 GMT")
    assert got == Fetched(None, '"abc"', "Fri, 13 Nov 2026 09:00:00 GMT")


def test_304_prefers_the_validators_the_server_sent():
    got = run(Wire(Reply(304, headers={"ETag": '"new"', "Last-Modified": "Sat"})), etag='"abc"')
    assert got == Fetched(None, '"new"', "Sat")


BAD_VALIDATORS = {
    "obs-fold": '"a"\r\n X-Folded: evil',
    "nul": '"a\x00b"',
    "del": '"a\x7fb"',
    "tab": '"a\tb"',
    "empty": "",
    "long": "M" * 60000,
    "just over": "M" * 257,
}


@pytest.mark.parametrize("bad", BAD_VALIDATORS.values(), ids=BAD_VALIDATORS)
def test_a_malformed_validator_on_a_200_is_not_returned(bad):
    got = run(Wire(Reply(200, b"<rss/>", {"ETag": bad, "Last-Modified": bad})))
    assert got == Fetched(b"<rss/>", None, None)


def test_a_validator_of_the_longest_allowed_size_is_returned():
    got = run(Wire(Reply(200, b"<rss/>", {"ETag": "E" * 256})))
    assert got.etag == "E" * 256


def test_validators_on_a_200_after_a_redirect_are_not_returned():
    wire = Wire(
        redirect("https://other.example.org/y"),
        Reply(200, b"<rss/>", {"ETag": '"h"', "Last-Modified": "Sat"}),
    )
    assert run(wire) == Fetched(b"<rss/>", None, None)


def test_a_304_after_a_redirect_is_refused():
    wire = Wire(redirect("https://other.example.org/y"), Reply(304, headers={"ETag": '"h"'}))
    with pytest.raises(FetchRefused, match="304"):
        run(wire, etag='"abc"')


def test_a_304_with_a_malformed_validator_keeps_the_one_sent():
    reply = Reply(304, headers={"ETag": '"a"\r\n X: y', "Last-Modified": "M" * 60000})
    assert run(Wire(reply), etag='"abc"', modified="Fri") == Fetched(None, '"abc"', "Fri")


def test_a_304_with_one_clean_validator_mixes_it_with_the_one_sent():
    reply = Reply(304, headers={"ETag": '"new"', "Last-Modified": "\x00"})
    assert run(Wire(reply), etag='"abc"', modified="Fri") == Fetched(None, '"new"', "Fri")


STORED_BAD = ['"a"\r\n X: y', "x" * 257, "\x00", ""]


@pytest.mark.parametrize("bad", STORED_BAD, ids=["fold", "long", "nul", "empty"])
def test_a_stored_etag_the_module_would_not_accept_is_not_sent_or_returned(bad):
    wire = Wire(Reply(304))
    got = run(wire, etag=bad, modified="Fri")
    assert "If-None-Match" not in wire.requests[0][1]
    assert got == Fetched(None, None, "Fri")


@pytest.mark.parametrize("bad", STORED_BAD, ids=["fold", "long", "nul", "empty"])
def test_a_stored_modified_the_module_would_not_accept_is_not_sent_or_returned(bad):
    wire = Wire(Reply(304))
    got = run(wire, etag='"abc"', modified=bad)
    assert "If-Modified-Since" not in wire.requests[0][1]
    assert got == Fetched(None, '"abc"', None)


def test_valid_stored_validators_are_sent_and_returned():
    wire = Wire(Reply(304))
    got = run(wire, etag='"abc"', modified="Fri")
    headers = wire.requests[0][1]
    assert (headers["If-None-Match"], headers["If-Modified-Since"]) == ('"abc"', "Fri")
    assert got == Fetched(None, '"abc"', "Fri")


def test_200_returns_body_and_validators():
    got = run(Wire(Reply(200, b"<rss/>", {"ETag": '"v2"', "Last-Modified": "Sat"})))
    assert got == Fetched(b"<rss/>", '"v2"', "Sat")


@pytest.mark.parametrize("status", [204, 401, 404, 500])
def test_other_status_is_refused_with_the_status(status):
    with pytest.raises(FetchRefused, match=str(status)):
        run(Wire(Reply(status)))


def test_body_of_exactly_the_cap_is_accepted():
    got = run(Wire(Reply(200, b"x" * MAX_BYTES)))
    assert got.body is not None and len(got.body) == MAX_BYTES


def test_body_one_byte_over_the_cap_is_refused_without_reading_the_rest():
    reply = Reply(200, b"x" * (MAX_BYTES * 3))
    with pytest.raises(FetchRefused, match="2 MB"):
        run(Wire(reply))
    assert reply.consumed == MAX_BYTES + 1


def test_a_declared_length_over_the_cap_is_refused_before_reading():
    reply = Reply(200, b"x" * 10, {"Content-Length": str(MAX_BYTES + 1)})
    with pytest.raises(FetchRefused, match="2 MB"):
        run(Wire(reply))
    assert reply.consumed == 0


def test_a_body_shorter_than_its_declared_length_is_refused():
    with pytest.raises(FetchRefused, match="ended early"):
        run(Wire(Reply(200, b"<rss/>", {"Content-Length": "1000"})))


def test_a_body_matching_its_declared_length_is_accepted():
    assert run(Wire(Reply(200, b"<rss/>", {"Content-Length": "6"}))).body == b"<rss/>"


@pytest.mark.parametrize("length", ["+1000", "1_000", "1" * 19, "5, 5", "٥"])
def test_an_unusable_content_length_is_refused(length):
    with pytest.raises(FetchRefused, match="unusable length"):
        run(Wire(Reply(200, b"<rss/>", {"Content-Length": length})))


@pytest.mark.parametrize("length", ["", "-5", "0x10", "abc"])
def test_a_length_http_client_ignores_is_undeclared(length):
    got = run(Wire(Reply(200, b"<rss/>", {"Content-Length": length})))
    assert got.body == b"<rss/>"


@pytest.mark.parametrize("encoding", ["gzip", "br", "deflate"])
def test_a_content_encoding_is_refused(encoding):
    with pytest.raises(FetchRefused, match="content encoding"):
        run(Wire(Reply(200, b"x", {"Content-Encoding": encoding})))


def test_identity_content_encoding_is_accepted():
    assert run(Wire(Reply(200, b"x", {"Content-Encoding": "Identity"}))).body == b"x"


# Failures
@pytest.mark.parametrize(
    "error",
    [
        OSError("socket broke"),
        TimeoutError("timed out"),
        ssl.SSLCertVerificationError("certificate verify failed"),
        http.client.BadStatusLine("garbage"),
        http.client.IncompleteRead(b"ab", 5),
        ValueError("bad header"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_every_failure_is_a_one_line_refusal(error):
    with pytest.raises(FetchRefused) as refused:
        run(Wire(error))
    assert "\n" not in str(refused.value) and str(refused.value)


def test_a_failure_while_connecting_is_a_refusal():
    def connect(target: ConnectionTarget) -> Any:
        raise OSError("connection refused")

    with pytest.raises(FetchRefused, match="connection refused"):
        fetch(URL, None, None, resolve=PUBLIC, wiring=Wiring(connect))


def _assert_short_line(error, absent=()):
    text = str(error)
    assert len(text) <= 200 and "\n" not in text and "\r" not in text
    assert all(piece not in text for piece in absent)


def test_a_long_scheme_is_not_echoed_and_the_reason_is_short():
    with pytest.raises(FetchRefused) as refused:
        check_address("s" * 60000 + "://feeds.example.org/", resolve=PUBLIC)
    _assert_short_line(refused.value, absent=("sss",))


def test_a_long_host_keeps_every_reason_within_200_characters():
    host = ".".join(["a" * 63] * 3 + ["b" * 61])
    assert len(host) == 253
    for resolve in (lambda h: ["10.0.0.1"], lambda h: []):
        with pytest.raises(FetchRefused) as refused:
            check_address(f"https://{host}/", resolve=resolve)
        _assert_short_line(refused.value)


def test_a_failure_reason_is_200_characters_in_all():
    with pytest.raises(FetchRefused) as refused:
        run(Wire(OSError("Q" * 5000)))
    _assert_short_line(refused.value)
    assert str(refused.value).startswith("fetch failed: ")


def test_a_reply_without_a_status_line_puts_no_server_text_in_the_reason():
    with pytest.raises(FetchRefused) as refused:
        run(Wire(http.client.BadStatusLine("secret-looking body line")))
    _assert_short_line(refused.value, absent=("secret",))
    assert "BadStatusLine" in str(refused.value)


def test_error_text_is_cut_to_one_short_line():
    with pytest.raises(FetchRefused) as refused:
        run(Wire(OSError("Q" * 5000 + "\nline two")))
    _assert_short_line(refused.value)


def test_a_failure_that_is_not_a_fetch_error_is_not_hidden():
    with pytest.raises(KeyError):
        run(Wire(KeyError("bug")))


# Total deadline, on a fake clock
def test_a_clock_past_the_deadline_refuses_before_any_connection():
    clock = Clock()
    wire = Wire(ok())

    def slow(host: str) -> Iterable[str]:
        clock.advance(11)
        return [PUBLIC_IP]

    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        run(wire, resolve=slow, clock=clock)
    assert not wire.targets


def test_a_slow_redirect_hop_lookup_opens_no_second_connection():
    clock = Clock()
    wire = Wire(redirect("https://other.example.org/y"), ok())

    def slow_hop(host: str) -> Iterable[str]:
        if host == "other.example.org":
            clock.advance(11)
        return [PUBLIC_IP]

    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        run(wire, resolve=slow_hop, clock=clock)
    assert [t.host for t in wire.targets] == ["feeds.example.org"]


def test_the_deadline_is_one_for_every_hop_and_handed_to_the_connection():
    clock = Clock()
    wire = Wire(redirect("https://other.example.org/y"), ok())
    run(wire, clock=clock)
    assert {t.deadline for t in wire.targets} == {1000.0 + fetch_module.TOTAL_SECONDS}
    assert all(t.clock is clock for t in wire.targets)


def test_headers_that_arrive_after_the_deadline_are_refused():
    clock = Clock()
    wire = Wire(ok())
    wire.on_response = lambda: clock.advance(11)
    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        run(wire, clock=clock)


def test_a_body_that_trickles_past_the_deadline_is_refused():
    clock = Clock()
    reply = Reply(200, b"x" * 100, on_read=lambda: clock.advance(6))
    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        run(Wire(reply), clock=clock)


def test_a_body_end_reached_after_the_deadline_is_refused():
    clock = Clock()
    reply = Reply(200, b"", on_read=lambda: clock.advance(11))
    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        run(Wire(reply), clock=clock)
