"""Fetch rules for Signal: https only, public addresses only, size cap, conditional requests."""

import email.message
import http.client
import io
import os
import socket
import threading
import time
import urllib.error
import urllib.request
import urllib.response
from collections.abc import Callable, Iterable, Iterator
from typing import Any

import pytest

from deploy_workflow.signal import fetch as fetch_module
from deploy_workflow.signal.fetch import Fetched, FetchRefused, check_address, fetch


def PUBLIC(host: str) -> Iterable[str]:
    return ["93.184.216.34"]


def _map(host: str) -> Iterable[str]:
    return ["10.0.0.1"] if host == "internal.example" else ["93.184.216.34"]


class FakeResponse:
    def __init__(self, status: int, body: bytes = b"", headers: dict[str, str] | None = None):
        self.status = status
        self.headers = email.message.Message()
        for name, value in (headers or {}).items():
            self.headers[name] = value
        self._body = io.BytesIO(body)

    def read(self, n: int = -1) -> bytes:
        return self._body.read(n)

    def close(self) -> None:
        self._body.close()


class RecordingOpener:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.headers: dict[str, str] = {}
        self.timeout: float | None = None

    def __call__(self, request: urllib.request.Request, timeout: float) -> FakeResponse:
        self.headers = dict(request.headers)
        self.timeout = timeout
        return self.response


@pytest.fixture
def big_opener() -> RecordingOpener:
    return RecordingOpener(FakeResponse(200, b"x" * (2 * 1024 * 1024 + 1)))


@pytest.fixture
def exact_opener() -> RecordingOpener:
    return RecordingOpener(FakeResponse(200, b"x" * (2 * 1024 * 1024)))


@pytest.fixture
def recording_opener() -> RecordingOpener:
    return RecordingOpener(FakeResponse(304))


@pytest.fixture
def recording_opener_200() -> RecordingOpener:
    return RecordingOpener(FakeResponse(200, b"<rss/>", {"ETag": '"v2"'}))


class _Body(io.BytesIO):
    """Response body that counts what was read; like http.client, reads nothing once closed."""

    consumed = 0

    def read(self, size: int | None = -1) -> bytes:
        if self.closed:
            return b""
        data = super().read(size)
        self.consumed += len(data)
        return data


class _Reply(urllib.response.addinfourl):
    """addinfourl with the `msg` attribute urllib's error processor reads."""

    msg = "reply"


class FakeHTTPS(urllib.request.BaseHandler):
    """Stands in for the HTTPS handler: answers each URL from a table, never connects."""

    handler_order = 100  # ahead of the real HTTPS handler, so nothing connects

    def __init__(self, table: dict[str, tuple[int, str | None]]):
        self.table = table
        self.seen: list[str] = []
        self.bodies: list[_Body] = []
        self.on_open: Callable[[], None] = lambda: None

    def https_open(self, req: urllib.request.Request) -> Any:
        self.seen.append(req.full_url)
        code, location = self.table[req.full_url]
        headers = email.message.Message()
        if location:
            headers["Location"] = location
        self.on_open()
        body = _Body(b"<rss/>" if code == 200 else b"r" * (5 * 1024 * 1024))
        self.bodies.append(body)
        return _Reply(body, headers, req.full_url, code)


def _real_opener(table: dict[str, tuple[int, str | None]]) -> tuple[Any, FakeHTTPS]:
    fake = FakeHTTPS(table)
    built = urllib.request.build_opener(fetch_module.redirect_handler(_map), fake)
    return built.open, fake


@pytest.mark.parametrize(
    "url",
    ["http://example.org/feed", "ftp://example.org/f", "https:///nohost", "file:///etc/passwd"],
)
def test_only_https_with_a_host(url):
    with pytest.raises(FetchRefused):
        check_address(url, resolve=PUBLIC)


@pytest.mark.parametrize(
    "addr", ["127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "::1", "fc00::1", "0.0.0.0"]
)
def test_non_public_addresses_are_refused(addr):
    with pytest.raises(FetchRefused, match="public"):
        check_address("https://feeds.example.org/x", resolve=lambda h: [addr])


def test_one_private_address_among_public_is_refused():
    with pytest.raises(FetchRefused):
        check_address(
            "https://feeds.example.org/x", resolve=lambda h: ["93.184.216.34", "10.0.0.1"]
        )


def test_public_https_passes():
    check_address("https://feeds.example.org/x", resolve=PUBLIC)


def test_unresolvable_host_is_refused():
    def fail(host: str) -> Iterable[str]:
        raise OSError("name not known")

    with pytest.raises(FetchRefused, match="name not known"):
        check_address("https://feeds.example.org/x", resolve=fail)


def test_redirect_to_a_private_address_is_refused():
    opener, fake = _real_opener({"https://feeds.example.org/x": (302, "https://internal.example/")})
    with pytest.raises(FetchRefused, match="public"):
        fetch("https://feeds.example.org/x", None, None, resolve=_map, opener=opener)
    assert fake.seen == ["https://feeds.example.org/x"]


def test_redirect_to_http_is_refused():
    opener, _ = _real_opener({"https://feeds.example.org/x": (302, "http://feeds.example.org/y")})
    with pytest.raises(FetchRefused, match="https"):
        fetch("https://feeds.example.org/x", None, None, resolve=_map, opener=opener)


def test_redirect_to_a_public_https_address_is_followed():
    opener, fake = _real_opener(
        {
            "https://feeds.example.org/x": (302, "https://other.example.org/y"),
            "https://other.example.org/y": (200, None),
        }
    )
    got = fetch("https://feeds.example.org/x", None, None, resolve=_map, opener=opener)
    assert got.body == b"<rss/>"
    assert fake.seen == ["https://feeds.example.org/x", "https://other.example.org/y"]


def test_more_than_three_redirects_are_refused():
    table = {
        f"https://feeds.example.org/{i}": (302, f"https://feeds.example.org/{i + 1}")
        for i in range(10)
    }
    opener, fake = _real_opener(table)
    with pytest.raises(FetchRefused, match="more than 3 redirects"):
        fetch("https://feeds.example.org/0", None, None, resolve=_map, opener=opener)
    assert fake.seen == [f"https://feeds.example.org/{i}" for i in range(4)]


def test_alternating_urls_do_not_get_more_hops():
    table = {
        "https://feeds.example.org/a": (302, "https://feeds.example.org/b"),
        "https://feeds.example.org/b": (302, "https://feeds.example.org/a"),
    }
    opener, fake = _real_opener(table)
    with pytest.raises(FetchRefused, match="more than 3 redirects"):
        fetch("https://feeds.example.org/a", None, None, resolve=_map, opener=opener)
    assert len(fake.seen) == 4


def test_redirect_response_body_is_never_read():
    opener, fake = _real_opener(
        {
            "https://feeds.example.org/x": (302, "https://other.example.org/y"),
            "https://other.example.org/y": (200, None),
        }
    )
    fetch("https://feeds.example.org/x", None, None, resolve=_map, opener=opener)
    assert fake.bodies[0].consumed == 0
    assert fake.bodies[0].closed


def test_refused_redirect_response_is_closed():
    opener, fake = _real_opener({"https://feeds.example.org/x": (302, "https://internal.example/")})
    with pytest.raises(FetchRefused):
        fetch("https://feeds.example.org/x", None, None, resolve=_map, opener=opener)
    assert fake.bodies[0].closed


class _Clock:
    """Replaces time.monotonic so a test can move time without waiting."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.offset = 0.0
        real = time.monotonic
        monkeypatch.setattr(fetch_module.time, "monotonic", lambda: real() + self.offset)


class _SlowResponse(FakeResponse):
    def __init__(self, clock: _Clock):
        super().__init__(200, b"x" * 100)
        self.clock = clock

    def read(self, n: int = -1) -> bytes:
        self.clock.offset += 6
        return super().read(1)


def test_body_that_trickles_past_the_total_deadline_is_refused(monkeypatch):
    opener = RecordingOpener(_SlowResponse(_Clock(monkeypatch)))
    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=opener)


def test_redirect_hop_after_the_total_deadline_is_refused(monkeypatch):
    clock = _Clock(monkeypatch)
    fake = FakeHTTPS(
        {
            "https://feeds.example.org/x": (302, "https://other.example.org/y"),
            "https://other.example.org/y": (200, None),
        }
    )
    fake.on_open = lambda: setattr(clock, "offset", clock.offset + 16)

    def default_opener(resolve: Any, deadline: float, watch: Any) -> Any:
        # the real wiring from fetch to the handler, with only the HTTPS layer faked
        return urllib.request.build_opener(
            fetch_module.redirect_handler(resolve, deadline), fake
        ).open

    monkeypatch.setattr(fetch_module, "_default_opener", default_opener)
    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        fetch("https://feeds.example.org/x", None, None, resolve=_map)
    assert fake.seen == ["https://feeds.example.org/x"]


@pytest.mark.parametrize("location", ["https://[::1", "https://[feeds.example.org]/feed"])
def test_malformed_redirect_location_is_refused(location):
    opener, _ = _real_opener({"https://feeds.example.org/x": (302, location)})
    with pytest.raises(FetchRefused):
        fetch("https://feeds.example.org/x", None, None, resolve=_map, opener=opener)


def test_non_ascii_start_path_is_refused():
    def encoding_opener(request: urllib.request.Request, timeout: float) -> Any:
        request.full_url.encode("ascii")  # what http.client does to the request line
        return FakeResponse(200)

    with pytest.raises(FetchRefused):
        fetch(
            "https://feeds.example.org/actualités",
            None,
            None,
            resolve=PUBLIC,
            opener=encoding_opener,
        )


@pytest.mark.parametrize(
    "url", ["https://[::1/x", f"https://{'a' * 64}.invalid/x", "https://a..invalid/x"]
)
def test_unparseable_addresses_are_refused_with_the_real_resolver(url):
    with pytest.raises(FetchRefused):
        check_address(url)


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
    ],
)
def test_host_must_be_a_plain_name(url):
    with pytest.raises(FetchRefused, match="plain host name"):
        check_address(url, resolve=PUBLIC)


def test_plain_host_with_port_and_hyphen_passes():
    check_address("https://feeds-1.example.org:8443/x", resolve=PUBLIC)


def test_redirect_to_a_percent_encoded_host_is_refused():
    opener, _ = _real_opener(
        {"https://feeds.example.org/x": (302, "https://cdn%2einternal.attacker.test/feed")}
    )
    with pytest.raises(FetchRefused, match="plain host name"):
        fetch("https://feeds.example.org/x", None, None, resolve=_map, opener=opener)


def test_environment_proxy_is_ignored(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)
    connected: list[Any] = []

    def refuse(address: Any, *args: Any, **kwargs: Any) -> Any:
        connected.append(address)
        raise OSError("no network in tests")

    monkeypatch.setattr(socket, "create_connection", refuse)
    with pytest.raises(FetchRefused):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC)
    assert connected
    assert all(address[0] == "feeds.example.org" for address in connected)


def test_http_error_text_from_the_server_is_not_copied():
    def failing(request: urllib.request.Request, timeout: float) -> Any:
        reason = "<script>" + "Z" * 5000
        raise urllib.error.HTTPError(request.full_url, 500, reason, email.message.Message(), None)

    with pytest.raises(FetchRefused) as refused:
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=failing)
    assert str(refused.value) == "server answered HTTP 500"


def test_other_error_text_is_cut():
    def failing(request: urllib.request.Request, timeout: float) -> Any:
        raise OSError("Q" * 5000)

    with pytest.raises(FetchRefused) as refused:
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=failing)
    assert len(str(refused.value)) < 300


@pytest.mark.parametrize(
    "addr", ["64:ff9b::a9fe:a9fe", "64:ff9b::7f00:1", "::a9fe:a9fe", "::7f00:1", "64:ff9b::808:808"]
)
def test_ipv6_forms_embedding_ipv4_are_refused(addr):
    with pytest.raises(FetchRefused, match="public"):
        check_address("https://feeds.example.org/x", resolve=lambda h: [addr])


def test_body_over_two_megabytes_is_refused(big_opener):
    with pytest.raises(FetchRefused, match="2 MB"):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=big_opener)


def test_body_of_exactly_two_megabytes_is_accepted(exact_opener):
    got = fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=exact_opener)
    assert got.body is not None and len(got.body) == 2 * 1024 * 1024


def test_conditional_headers_are_sent_and_304_returns_no_body(recording_opener):
    got = fetch(
        "https://feeds.example.org/x",
        '"abc"',
        "Fri, 13 Nov 2026 09:00:00 GMT",
        resolve=PUBLIC,
        opener=recording_opener,
    )
    assert recording_opener.headers["If-none-match"] == '"abc"'
    assert recording_opener.headers["If-modified-since"] == "Fri, 13 Nov 2026 09:00:00 GMT"
    assert recording_opener.timeout == 10
    assert "Mozilla" in recording_opener.headers["User-agent"]
    assert got == Fetched(None, '"abc"', "Fri, 13 Nov 2026 09:00:00 GMT")


def test_no_conditional_headers_when_none_given(recording_opener_200):
    fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=recording_opener_200)
    assert "If-none-match" not in recording_opener_200.headers
    assert "If-modified-since" not in recording_opener_200.headers


def test_200_returns_body_and_validators(recording_opener_200):
    got = fetch(
        "https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=recording_opener_200
    )
    assert (got.body, got.etag) == (b"<rss/>", '"v2"')


def test_other_status_is_refused_with_the_status():
    opener = RecordingOpener(FakeResponse(500))
    with pytest.raises(FetchRefused, match="500"):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=opener)


def test_network_error_is_refused_with_its_text():
    def failing(request: urllib.request.Request, timeout: float) -> Any:
        raise TimeoutError("timed out")

    with pytest.raises(FetchRefused, match="timed out"):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=failing)


def test_private_start_address_is_refused_before_any_request():
    called: list[int] = []

    def opener(request: urllib.request.Request, timeout: float) -> Any:
        called.append(1)
        return FakeResponse(200)

    with pytest.raises(FetchRefused, match="public"):
        fetch("https://internal.example/x", None, None, resolve=_map, opener=opener)
    assert not called


def test_host_case_is_ignored():
    check_address("https://WWW.Example.org/feed", resolve=PUBLIC)


def test_non_ascii_letters_that_lowercase_to_ascii_are_refused():
    # U+212A KELVIN SIGN lower-cases to "k"; the name connected to must be the name checked.
    with pytest.raises(FetchRefused, match="plain host name"):
        check_address("https://\u212aeeds.example.org/feed", resolve=PUBLIC)


SHORT = 0.5  # TOTAL_SECONDS in these tests
LATE = SHORT + 1.0  # a fetch still running at this point has outrun the deadline


def _workers() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name == "signal-fetch"]


@pytest.fixture
def short_deadline(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(fetch_module, "TOTAL_SECONDS", SHORT)
    yield
    for worker in _workers():  # nothing may outlive the patches below
        worker.join(5)


class _DrippingOpener:
    """An opener answering over a socket pair: head at once, one byte of drip per `every` s."""

    def __init__(self, head: bytes, drip: bytes, tail: bytes, every: float = 0.2) -> None:
        self.head, self.drip, self.tail, self.every = head, drip, tail, every
        self.responses: list[http.client.HTTPResponse] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> http.client.HTTPResponse:
        ours, theirs = socket.socketpair()
        ours.settimeout(timeout)  # what http.client sets: a per-operation timeout
        threading.Thread(target=self._serve, args=(theirs,), daemon=True).start()
        response = http.client.HTTPResponse(ours)
        response.begin()
        ours.close()  # as urllib does: the response's file keeps the connection open
        self.responses.append(response)
        return response

    def _serve(self, theirs: socket.socket) -> None:
        with theirs:
            try:
                theirs.sendall(self.head)
                for byte in self.drip:
                    time.sleep(self.every)
                    theirs.sendall(bytes([byte]))
                theirs.sendall(self.tail)
            except OSError:
                pass  # the client shut the connection


CHUNKED = b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n"


@pytest.mark.parametrize(
    ("head", "tail"),
    [
        (CHUNKED + b"6;", b"\r\n<rss/>\r\n0\r\n\r\n"),  # chunk-size line extension dripped
        (CHUNKED + b"6\r\n<rss/>\r\n0\r\nX-T: ", b"\r\n\r\n"),  # trailer dripped
    ],
    ids=["chunk-extension", "trailer"],
)
def test_chunk_framing_dripped_past_the_deadline_is_refused_on_time(short_deadline, head, tail):
    opener = _DrippingOpener(head, b"y" * 15, tail)
    start = time.monotonic()
    with pytest.raises(FetchRefused, match="longer than"):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=opener)
    assert time.monotonic() - start < LATE


def test_cut_leaves_no_worker_and_closes_the_response(short_deadline):
    opener = _DrippingOpener(CHUNKED + b"6\r\n<rss/>\r\n0\r\nX-T: ", b"y" * 15, b"\r\n\r\n")
    with pytest.raises(FetchRefused):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=opener)
    assert not _workers()
    assert all(response.isclosed() for response in opener.responses)


def test_connect_attempts_across_addresses_stop_at_the_deadline(monkeypatch, short_deadline):
    monkeypatch.setattr(fetch_module, "TIMEOUT_SECONDS", 1)
    silent = ("127.0.0.1", 9)

    def getaddrinfo(host: str, port: int, *args: Any, **kwargs: Any) -> list[Any]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", silent)] * 3

    def connect(self: socket.socket, address: Any) -> None:
        # a dropped SYN: the attempt waits out this socket's own timeout
        time.sleep(self.gettimeout() or 0)
        raise TimeoutError("timed out")

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", connect)
    start = time.monotonic()
    with pytest.raises(FetchRefused, match="longer than"):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC)
    assert time.monotonic() - start < LATE


def test_slow_address_lookup_stops_at_the_deadline_and_never_connects(short_deadline):
    opened: list[str] = []

    def slow(host: str) -> Iterable[str]:
        time.sleep(2)
        return ["93.184.216.34"]

    def opener(request: urllib.request.Request, timeout: float) -> Any:
        opened.append(request.full_url)
        raise OSError("tests make no connection")

    start = time.monotonic()
    with pytest.raises(FetchRefused, match="longer than"):
        fetch("https://feeds.example.org/x", None, None, resolve=slow, opener=opener)
    assert time.monotonic() - start < LATE
    for worker in _workers():
        worker.join(5)
    assert opened == []


class _EndsLate:
    """A body whose end arrives after the deadline (time moved by a patched clock)."""

    status = 200

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.headers = email.message.Message()
        self.offset = 0.0
        real = time.monotonic
        monkeypatch.setattr(fetch_module.time, "monotonic", lambda: real() + self.offset)

    def read(self, n: int = -1) -> bytes:
        self.offset += 11
        return b""

    def close(self) -> None:
        pass


def test_body_end_reached_after_the_deadline_is_refused(monkeypatch):
    response = _EndsLate(monkeypatch)
    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        fetch(
            "https://feeds.example.org/x",
            None,
            None,
            resolve=PUBLIC,
            opener=lambda request, timeout: response,
        )


def test_successful_fetch_leaves_no_worker():
    got = fetch(
        "https://feeds.example.org/x",
        None,
        None,
        resolve=PUBLIC,
        opener=_DrippingOpener(
            b"HTTP/1.1 200 OK\r\nContent-Length: 6\r\nConnection: close\r\n\r\n<rss/>", b"", b""
        ),
    )
    assert got == Fetched(b"<rss/>", None, None)
    assert not _workers()


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_a_bug_in_the_fetch_thread_is_not_a_refusal():
    def broken(request: urllib.request.Request, timeout: float) -> Any:
        raise KeyError("bug")

    with pytest.raises(Exception) as raised:
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=broken)
    assert not isinstance(raised.value, FetchRefused)


@pytest.mark.skipif(not os.path.isdir("/dev/fd"), reason="counts open descriptors via /dev/fd")
def test_holding_a_descriptor_that_is_not_a_socket_fails_without_leaking_one(tmp_path):
    watch = fetch_module._Watch()
    with open(tmp_path / "plain", "wb") as plain:
        before = len(os.listdir("/dev/fd"))
        for _ in range(20):
            with pytest.raises(OSError):
                watch.hold(plain.fileno())
        assert len(os.listdir("/dev/fd")) == before


@pytest.mark.skipif(not hasattr(os, "get_blocking"), reason="reads the descriptor's blocking flag")
def test_holding_a_connection_leaves_its_timeout_and_blocking_state_unchanged():
    ours, theirs = socket.socketpair()
    with ours, theirs:
        ours.settimeout(0.3)
        watch = fetch_module._Watch()
        watch.hold(ours.fileno())
        assert ours.gettimeout() == 0.3
        assert not os.get_blocking(ours.fileno())  # a timeout means non-blocking underneath
        start = time.monotonic()
        with pytest.raises(TimeoutError):  # a stalled read still times out per operation
            ours.recv(1)
        assert time.monotonic() - start < 2
        watch.release()
    plain, other = socket.socketpair()
    with plain, other:
        watch = fetch_module._Watch()
        watch.hold(plain.fileno())
        assert plain.gettimeout() is None
        assert os.get_blocking(plain.fileno())
        watch.release()


def test_an_expired_watch_refuses_to_connect_and_creates_no_socket(monkeypatch):
    lookups: list[str] = []

    def getaddrinfo(host: str, port: int, *args: Any, **kwargs: Any) -> list[Any]:
        lookups.append(host)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 9))]

    def forbidden(self: socket.socket, address: Any) -> None:
        raise AssertionError("a connection was attempted after the deadline")

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    watch = fetch_module._Watch()
    watch.expire()
    connection = fetch_module._HeldConnection("feeds.example.org", watch=watch, timeout=1)
    with pytest.raises(FetchRefused, match="longer than"):
        connection.connect()
    assert lookups == []
    assert connection.sock is None


def test_a_lookup_that_ends_after_the_deadline_opens_no_connection(monkeypatch):
    watch = fetch_module._Watch()

    def getaddrinfo(host: str, port: int, *args: Any, **kwargs: Any) -> list[Any]:
        watch.expire()  # the deadline falls while the lookup runs
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 9))]

    def forbidden(self: socket.socket, address: Any) -> None:
        raise AssertionError("a connection was attempted after the deadline")

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    connection = fetch_module._HeldConnection("feeds.example.org", watch=watch, timeout=1)
    with pytest.raises(FetchRefused, match="longer than"):
        connection.connect()
    assert connection.sock is None


def test_a_slow_redirect_hop_lookup_ending_after_the_deadline_makes_no_connection(monkeypatch):
    clock = _Clock(monkeypatch)
    fake = FakeHTTPS(
        {
            "https://feeds.example.org/x": (302, "https://other.example.org/y"),
            "https://other.example.org/y": (200, None),
        }
    )

    def slow_hop(host: str) -> Iterable[str]:
        if host == "other.example.org":
            clock.offset += 16  # the lookup outlives the deadline
        return ["93.184.216.34"]

    def default_opener(resolve: Any, deadline: float, watch: Any) -> Any:
        return urllib.request.build_opener(
            fetch_module.redirect_handler(resolve, deadline), fake
        ).open

    monkeypatch.setattr(fetch_module, "_default_opener", default_opener)
    with pytest.raises(FetchRefused, match="longer than 10 seconds"):
        fetch("https://feeds.example.org/x", None, None, resolve=slow_hop)
    assert fake.seen == ["https://feeds.example.org/x"]


def test_a_connection_that_completes_after_the_deadline_is_closed_and_refused(monkeypatch):
    watch = fetch_module._Watch()
    ours, theirs = socket.socketpair()

    def late(address: Any, timeout: Any, source_address: Any = None) -> socket.socket:
        watch.expire()  # the deadline falls while the connect runs
        return ours

    monkeypatch.setattr(socket, "create_connection", late)
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [])
    connection = fetch_module._HeldConnection("feeds.example.org", watch=watch, timeout=1)
    with theirs, pytest.raises(FetchRefused, match="longer than"):
        connection.connect()
    assert ours.fileno() == -1  # closed
