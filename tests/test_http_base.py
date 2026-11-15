"""The shared HTTP base, driven directly through a toy service over real sockets.

Scope: ``deploy_workflow.http_base`` alone. The toy service is started twice, once with each real
service's parameters (``plain`` as the run start service sets them, ``strict`` as Signal sets
them), so every shared check is exercised under both; a check that one service's suite alone used
to cover is here for both. The last tests pin the parameters each real service passes.
"""

from __future__ import annotations

import logging
import socket
import threading
import time
import urllib.parse
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest

from deploy_workflow import http_base
from deploy_workflow.http_base import Reply, refuse
from deploy_workflow.run_start import service as run_start_service
from deploy_workflow.signal import service as signal_service

log = logging.getLogger("toy")
LIMIT = 64  # bytes of JSON the toy accepts


class _Plain(http_base.Server):
    most = (64, None)

    def connection_limits(self) -> tuple[int, int | None]:
        return self.most


class _Strict(_Plain):
    most = (64, 2)


class _PlainHandler(http_base.Handler):
    timeout = 5
    server_version = "Toy"
    logger = log

    def _route(self, url: urllib.parse.SplitResult) -> Reply | None:
        if self.command == "POST" and url.path == "/echo":
            return Reply(200, {"got": self.json_body(LIMIT)})
        if url.path == "/":
            return Reply(200, b"page", {"Content-Type": "text/plain"})
        if url.path == "/boom":
            raise RuntimeError("secret-cause")
        if url.path == "/raised":
            raise refuse(418, "raised")
        return None

    def do_GET(self) -> None:
        self.serve_request(self._route)

    do_POST = do_HEAD = do_GET


class _StrictHandler(_PlainHandler):
    response_headers = (("Content-Security-Policy", "default-src 'none'"), ("X-Extra", "1"))
    closes_http09 = True
    deadline = 30.0

    def connection_deadline(self) -> float:
        return self.deadline

    def read_body(self, length: int) -> bytes:
        try:
            return self.rfile.read(length)
        except OSError:
            raise refuse(400, "the request body did not arrive") from None


class Toy:
    def __init__(self, kind: str) -> None:
        self.kind = kind
        server, handler = (_Strict, _StrictHandler) if kind == "strict" else (_Plain, _PlainHandler)
        self.server = server(("127.0.0.1", 0), handler)
        self.port = self.server.server_address[1]
        self.host = f"127.0.0.1:{self.port}"
        threading.Thread(target=self.server.serve_forever, args=(0.02,), daemon=True).start()

    def raw(self, data: bytes) -> bytes:
        """Everything the service sends back for ``data`` until it closes the connection."""
        with socket.create_connection(("127.0.0.1", self.port), timeout=10) as sock:
            sock.sendall(data)
            chunks = []
            while chunk := sock.recv(65536):
                chunks.append(chunk)
        return b"".join(chunks)

    def ask(
        self, method: str, target: str, headers: dict[str, str] | None = None, body: bytes = b""
    ) -> tuple[int, dict[str, str], bytes]:
        lines = [f"{method} {target} HTTP/1.1"]
        given = {"Host": self.host, **(headers or {})}
        lines += [f"{name}: {value}" for name, value in given.items()]
        return parse(self.raw("\r\n".join(lines).encode() + b"\r\n\r\n" + body))


def parse(answer: bytes) -> tuple[int, dict[str, str], bytes]:
    head, _, body = answer.partition(b"\r\n\r\n")
    first, *rest = head.decode("latin-1").split("\r\n")
    headers = dict(line.split(": ", 1) for line in rest)
    return int(first.split()[1]), headers, body


@pytest.fixture(params=["plain", "strict"])
def toy(request: pytest.FixtureRequest) -> Iterator[Toy]:
    made = Toy(request.param)
    yield made
    made.server.shutdown()
    made.server.server_close()


def own(toy: Toy) -> dict[str, str]:
    return {"Origin": f"http://{toy.host}"}


def error(answer: tuple[int, dict[str, str], bytes]) -> tuple[int, str]:
    import json

    return answer[0], json.loads(answer[2])["error"]


# -- the checks before any body byte ----------------------------------------------------------


def test_a_request_is_served_and_carries_the_fixed_headers(toy):
    status, headers, body = toy.ask("GET", "/")
    assert (status, body) == (200, b"page")
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert headers["Server"].strip() == "Toy"  # no Python version
    assert headers["Content-Length"] == "4"
    assert ("X-Extra" in headers) == (toy.kind == "strict")


def test_the_headers_every_response_carries_come_in_a_fixed_order(toy):
    names = list(toy.ask("GET", "/nothing")[1])
    fixed = ["X-Content-Type-Options", "Cross-Origin-Resource-Policy"]
    extra = ["Content-Security-Policy", "X-Extra"] if toy.kind == "strict" else []
    assert names[-len(fixed + extra) :] == fixed + extra


@pytest.mark.parametrize("target", ["http://evil.example/", "*", "evil.example:80", "//x"[1:2]])
def test_a_target_that_is_not_a_path_is_400_or_served_as_one(toy, target):
    if target == "/":
        assert toy.ask("GET", target)[0] == 200
    else:
        assert error(toy.ask("GET", target)) == (400, "the request target must be a path")


def test_the_target_is_judged_before_the_host(toy):
    answer = toy.ask("GET", "http://evil.example/", {"Host": "evil.example"})
    assert error(answer) == (400, "the request target must be a path")


@pytest.mark.parametrize(
    "host", ["evil.example", "127.0.0.1", "127.0.0.1:1", "LOCALHOST:{port}", " 127.0.0.1:{port} x"]
)
def test_a_host_other_than_the_one_started_on_is_403(toy, host):
    answer = toy.ask("GET", "/", {"Host": host.format(port=toy.port)})
    assert error(answer) == (403, "this address is not the one the service was started on")


def test_localhost_is_answered_for_the_loopback_address(toy):
    assert toy.ask("GET", "/", {"Host": f"localhost:{toy.port}"})[0] == 200


def test_a_missing_or_repeated_host_is_403(toy):
    refused = "this address is not the one the service was started on"
    assert error(parse(toy.raw(b"GET / HTTP/1.1\r\n\r\n"))) == (403, refused)
    twice = f"GET / HTTP/1.1\r\nHost: {toy.host}\r\nHost: {toy.host}\r\n\r\n".encode()
    assert error(parse(toy.raw(twice))) == (403, refused)


@pytest.mark.parametrize("site", ["cross-site", "same-site", "", "SAME-ORIGIN", "none, none"])
def test_a_fetch_from_another_site_is_403(toy, site):
    answer = toy.ask("GET", "/", {"Sec-Fetch-Site": site})
    assert error(answer) == (403, "the request came from another site")


def test_a_repeated_sec_fetch_site_is_403_even_when_each_value_is_allowed(toy):
    head = f"GET / HTTP/1.1\r\nHost: {toy.host}\r\n"
    twice = head + "Sec-Fetch-Site: same-origin\r\nSec-Fetch-Site: none\r\n\r\n"
    assert parse(toy.raw(twice.encode()))[0] == 403


@pytest.mark.parametrize("site", ["same-origin", "none"])
def test_a_same_origin_or_typed_address_fetch_is_served(toy, site):
    assert toy.ask("GET", "/", {"Sec-Fetch-Site": site})[0] == 200


def test_only_a_get_navigation_to_a_document_is_excepted(toy):
    navigate = {"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "navigate"}
    document = {**navigate, "Sec-Fetch-Dest": "document"}
    assert toy.ask("GET", "/", document)[0] == 200
    refused = (403, "the request came from another site")
    assert error(toy.ask("GET", "/", navigate)) == refused  # no destination
    assert error(toy.ask("GET", "/", {**document, "Sec-Fetch-Dest": "iframe"})) == refused
    assert error(toy.ask("GET", "/", {**document, "Sec-Fetch-Mode": "cors"})) == refused
    post = toy.ask("POST", "/echo", {**document, **own(toy), "Content-Length": "2"}, b"{}")
    assert error(post) == refused  # a form posted from another site navigates too


def test_a_navigation_with_a_foreign_origin_is_still_403(toy):
    headers = {
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Origin": "http://evil.example",
    }
    answer = toy.ask("GET", "/", headers)
    assert error(answer) == (403, "the request did not come from the service's own page")


@pytest.mark.parametrize(
    "origin",
    [None, "null", "http://evil.example", "https://{host}", "http://{host}/", "http://{host} "],
)
def test_a_request_other_than_get_needs_the_service_s_own_origin(toy, origin):
    headers = {"Content-Length": "2"}
    if origin is not None:
        headers["Origin"] = origin.format(host=toy.host) + ("x" if origin.endswith(" ") else "")
    answer = toy.ask("POST", "/echo", headers, b"{}")
    assert error(answer) == (403, "the request did not come from the service's own page")


def test_a_repeated_origin_is_403_and_a_get_with_a_foreign_origin_too(toy):
    refused = (403, "the request did not come from the service's own page")
    head = f"POST /echo HTTP/1.1\r\nHost: {toy.host}\r\nContent-Length: 2\r\n"
    twice = head + f"Origin: http://{toy.host}\r\nOrigin: http://{toy.host}\r\n\r\n{{}}"
    assert error(parse(toy.raw(twice.encode()))) == refused
    assert error(toy.ask("GET", "/", {"Origin": "http://evil.example"})) == refused
    assert toy.ask("GET", "/", own(toy))[0] == 200


def test_on_port_80_the_port_may_be_left_out_of_host_and_origin(toy):
    server = cast(http_base.Server, toy.server)
    server.allowed_hosts, server.advertised_port = http_base.hosts("127.0.0.1", 80), 80
    for host in ("127.0.0.1", "localhost", "127.0.0.1:80"):
        assert toy.ask("GET", "/", {"Host": host})[0] == 200, host
    body = {"Content-Length": "2"}
    short = {"Host": "127.0.0.1:80", "Origin": "http://127.0.0.1", **body}
    assert toy.ask("POST", "/echo", short, b"{}")[0] == 200
    wrong = toy.ask(
        "POST", "/echo", {"Host": "127.0.0.1", "Origin": "http://127.0.0.1:80", **body}, b"{}"
    )
    assert wrong[0] == 403  # Origin is compared with the Host as sent, plus only the short form


def test_hosts_lists_exactly_the_names_answered():
    assert http_base.hosts("10.0.0.5", 8765) == {"10.0.0.5:8765"}
    assert http_base.hosts("127.0.0.1", 8765) == {"127.0.0.1:8765", "localhost:8765"}
    assert http_base.hosts("10.0.0.5", 80) == {"10.0.0.5:80", "10.0.0.5"}


def test_every_check_precedes_the_body(toy):
    """A refused request with a body it never sends is answered at once, not after a timeout."""
    cases = [
        ({"Host": "evil.example", **own(toy)}, 403),
        ({"Sec-Fetch-Site": "cross-site", **own(toy)}, 403),
        ({}, 403),
        ({"Transfer-Encoding": "chunked", **own(toy)}, 411),
    ]
    for headers, status in cases:
        began = time.monotonic()
        answer = toy.ask("POST", "/echo", {"Content-Length": "50", **headers})
        assert answer[0] == status, headers
        assert time.monotonic() - began < 2, headers


def test_a_transfer_encoding_is_411_whatever_the_method_or_length(toy):
    refused = (411, "a body needs Content-Length")
    chunked = {"Transfer-Encoding": "chunked"}
    assert error(toy.ask("GET", "/", chunked)) == refused
    both = {**chunked, **own(toy), "Content-Length": "2"}
    assert error(toy.ask("POST", "/echo", both, b"{}")) == refused  # no request smuggling


# -- the replies http.server writes itself ----------------------------------------------------


@pytest.mark.parametrize(
    ("request_bytes", "status"),
    [
        (b"BREW / HTTP/1.1\r\nHost: x\r\n\r\n", 501),
        (b"GET / HTTP/1.1 extra words\r\n\r\n", 400),
        (b"GET /" + b"a" * 70000 + b" HTTP/1.1\r\n\r\n", 414),
        (b"GET / HTTP/1.1\r\n" + b"X: y\r\n" * 200 + b"\r\n", 431),
    ],
)
def test_the_replies_http_server_writes_itself_carry_the_headers(toy, request_bytes, status):
    got, headers, _ = parse(toy.raw(request_bytes))
    assert got == status
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert ("Content-Security-Policy" in headers) == (toy.kind == "strict")


def test_an_http_09_request_line_is_closed_or_refused_by_parameter(toy):
    answer = toy.raw(b"GET /\r\n\r\n")
    if toy.kind == "strict":
        assert answer == b""  # closed with no reply
    else:
        # http.server parses no headers for such a line, so the Host check itself fails: the
        # fixed 500 text, with no status line or headers (HTTP/0.9 has none), and a logged
        # traceback. This is what a service that does not set ``closes_http09`` answers.
        assert answer == b'{"error": "the service failed; see its log"}'
    assert toy.ask("GET", "/")[0] == 200


# -- replies ----------------------------------------------------------------------------------


def test_a_route_that_returns_nothing_is_a_json_404(toy):
    status, headers, body = toy.ask("GET", "/nothing")
    assert (status, body) == (404, b'{"error": "not found"}')
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert headers["Cache-Control"] == "no-store"


def test_a_raised_reply_is_sent_like_a_returned_one(toy):
    assert error(toy.ask("GET", "/raised")) == (418, "raised")


def test_an_unexpected_failure_is_a_fixed_500_logged_on_the_service_s_logger(toy, caplog):
    with caplog.at_level(logging.ERROR, logger=log.name):
        status, _, body = toy.ask("GET", "/boom")
    assert (status, body) == (500, b'{"error": "the service failed; see its log"}')
    assert b"secret-cause" not in body
    assert [r.name for r in caplog.records if r.exc_info] == ["toy"]


def test_head_gets_the_length_and_no_body(toy):
    status, headers, body = toy.ask("HEAD", "/", own(toy))  # not a GET: it needs the Origin
    assert (status, headers["Content-Length"], body) == (200, "4", b"")


def test_every_connection_serves_one_request(toy):
    one = f"GET / HTTP/1.1\r\nHost: {toy.host}\r\nConnection: keep-alive\r\n\r\n".encode()
    assert toy.raw(one + one).count(b"HTTP/1.") == 1


# -- bodies -----------------------------------------------------------------------------------


def post(toy: Toy, body: bytes, length: str | None) -> tuple[int, dict[str, str], bytes]:
    headers = own(toy) if length is None else {**own(toy), "Content-Length": length}
    return toy.ask("POST", "/echo", headers, body)


def test_a_json_body_is_read_and_returned(toy):
    assert post(toy, b'{"a": [1]}', "10")[2] == b'{"got": {"a": [1]}}'
    assert post(toy, b"7", " 1 ")[2] == b'{"got": 7}'  # any one JSON value; blanks around a length


def test_a_body_without_a_length_is_411(toy):
    assert error(post(toy, b"{}", None)) == (411, "a body needs Content-Length")


@pytest.mark.parametrize("length", ["-1", "+2", "0x2", "2.0", "2 2", "", "9" * 16, "٢", "²"])
def test_a_length_that_is_not_a_plain_number_is_400(toy, length):
    head = f"POST /echo HTTP/1.1\r\nHost: {toy.host}\r\nOrigin: http://{toy.host}\r\n"
    request = head.encode() + b"Content-Length: " + length.encode("utf-8") + b"\r\n\r\n{}"
    assert error(parse(toy.raw(request))) == (400, "Content-Length is not a length")


def test_two_lengths_are_400_even_when_equal(toy):
    head = f"POST /echo HTTP/1.1\r\nHost: {toy.host}\r\nOrigin: http://{toy.host}\r\n"
    request = head + "Content-Length: 2\r\nContent-Length: 2\r\n\r\n{}"
    assert error(parse(toy.raw(request.encode()))) == (400, "Content-Length is not a length")


def test_a_body_over_the_limit_is_413_from_the_header_alone(toy):
    began = time.monotonic()
    assert post(toy, b"", str(LIMIT + 1))[0] == 413  # nothing sent, nothing waited for
    assert time.monotonic() - began < 2
    assert post(toy, b'"' + b"a" * (LIMIT - 2) + b'"', str(LIMIT))[0] == 200


def test_a_body_that_ends_early_is_400(toy):
    request = f"POST /echo HTTP/1.1\r\nHost: {toy.host}\r\nOrigin: http://{toy.host}\r\n"
    with socket.create_connection(("127.0.0.1", toy.port), timeout=10) as sock:
        sock.sendall(request.encode() + b"Content-Length: 9\r\n\r\n{}")
        sock.shutdown(socket.SHUT_WR)
        answer = b""
        while chunk := sock.recv(65536):
            answer += chunk
    assert error(parse(answer)) == (400, "the request body ended early")


@pytest.mark.parametrize("body", [b"{", b"\xff", b"1 2", b"[" * 60, b""])
def test_a_body_that_is_not_one_json_value_is_400(toy, body):
    assert error(post(toy, body, str(len(body)))) == (400, "the request body is not valid JSON")


def test_a_body_that_stalls_is_dropped_or_refused_by_parameter(toy, monkeypatch, caplog):
    monkeypatch.setattr(_PlainHandler, "timeout", 0.3)
    head = f"POST /echo HTTP/1.1\r\nHost: {toy.host}\r\nOrigin: http://{toy.host}\r\n"
    with (
        caplog.at_level(logging.INFO, logger=log.name),
        socket.create_connection(("127.0.0.1", toy.port), timeout=10) as sock,
    ):
        sock.sendall(head.encode() + b"Content-Length: 9\r\n\r\n{")
        answer = b""
        while chunk := sock.recv(65536):
            answer += chunk
    if toy.kind == "strict":
        assert error(parse(answer)) == (400, "the request body did not arrive")
    else:
        assert answer == b""  # ClientGone: no reply, one info line, no error
        assert "connection lost" in caplog.text
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


# -- connections ------------------------------------------------------------------------------


def closed(sock: socket.socket, within: float) -> bool:
    sock.settimeout(within)
    try:
        return sock.recv(1) == b""
    except TimeoutError:
        return False


def test_connections_beyond_the_ceiling_are_closed_and_slots_are_returned(toy, monkeypatch):
    monkeypatch.setattr(type(toy.server), "most", (2, None))
    held = [socket.create_connection(("127.0.0.1", toy.port)) for _ in range(2)]
    server = cast(http_base.Server, toy.server)
    try:
        deadline = time.monotonic() + 5
        while server.active_connections < 2:
            assert time.monotonic() < deadline
            time.sleep(0.01)
        with socket.create_connection(("127.0.0.1", toy.port)) as extra:
            assert closed(extra, 3)
        assert not closed(held[0], 0.2)
    finally:
        for sock in held:
            sock.close()
    deadline = time.monotonic() + 5
    while server.active_connections:
        assert time.monotonic() < deadline
        time.sleep(0.01)
    assert server._per_address == {}  # nothing is left counted for the address
    assert toy.ask("GET", "/")[0] == 200


def test_the_ceiling_per_address_applies_only_where_it_is_set(toy):
    held = [socket.create_connection(("127.0.0.1", toy.port)) for _ in range(2)]
    try:
        time.sleep(0.3)
        with socket.create_connection(("127.0.0.1", toy.port)) as extra:
            extra.sendall(f"GET / HTTP/1.1\r\nHost: {toy.host}\r\n\r\n".encode())
            answer = extra.recv(65536)
        assert (answer == b"") == (toy.kind == "strict")  # strict allows two per address
    finally:
        for sock in held:
            sock.close()


def test_a_trickling_connection_is_cut_only_where_a_deadline_is_set(toy, monkeypatch, caplog):
    monkeypatch.setattr(_StrictHandler, "deadline", 0.4)
    caplog.set_level(logging.INFO, logger=log.name)
    with socket.create_connection(("127.0.0.1", toy.port)) as sock:
        sock.sendall(f"GET / HTTP/1.1\r\nHost: {toy.host}\r\nX-Pad: ".encode())
        began = time.monotonic()
        cut = False
        while time.monotonic() - began < 1.5 and not cut:
            try:
                sock.sendall(b"a")
            except OSError:
                cut = True
            cut = cut or closed(sock, 0.1)
    assert cut == (toy.kind == "strict")
    assert ("connection deadline reached" in caplog.text) == (toy.kind == "strict")


def test_a_served_request_cancels_its_deadline(toy, caplog):
    caplog.set_level(logging.INFO, logger=log.name)
    before = threading.active_count()
    assert toy.ask("GET", "/")[0] == 200
    time.sleep(0.2)
    assert threading.active_count() <= before
    assert "connection deadline reached" not in caplog.text


# -- files ------------------------------------------------------------------------------------


def served(base: Path, relative: str, *, direct: bool = False) -> Any:
    try:
        reply = http_base.contained_file(base, relative, direct=direct, headers={"X-Kept": "1"})
    except Reply as refusal:
        return refusal.status, refusal.body
    return reply.status, reply.body, reply.headers


def test_a_contained_file_is_served_with_its_type_then_the_given_headers(tmp_path):
    (tmp_path / "lib" / "sub").mkdir(parents=True)
    (tmp_path / "lib" / "a.js").write_bytes(b"js")
    (tmp_path / "lib" / "sub" / "index.html").write_bytes(b"<p>")
    (tmp_path / "lib" / "odd.zzz").write_bytes(b"?")
    base = tmp_path / "lib"
    status, body, headers = served(base, "a.js")
    assert (status, body) == (200, b"js")
    assert list(headers) == ["Content-Type", "X-Kept"]
    assert headers["Content-Type"] in ("text/javascript", "application/javascript")
    assert served(base, "sub")[1] == b"<p>" and served(base, "sub/")[1] == b"<p>"
    assert served(base, "//a.js")[1] == b"js"  # leading slashes never make an absolute path
    assert served(base, "%61.js")[1] == b"js"
    assert served(base, "odd.zzz")[2]["Content-Type"] == "application/octet-stream"


@pytest.mark.parametrize(
    "relative",
    ["../secret", "sub/../../secret", "%2e%2e/secret", "..%2fsecret", "/../secret", "missing"]
    + ["", "a.js/x", "%ff", "a%00.js", "out", "out/secret", "leak", "loop"],
)
def test_nothing_outside_the_folder_or_not_a_regular_file_is_served(tmp_path, relative):
    base = tmp_path / "lib"
    base.mkdir()
    (tmp_path / "secret").write_bytes(b"secret")
    (base / "a.js").write_bytes(b"js")
    (base / "out").symlink_to(tmp_path)
    (base / "leak").symlink_to(tmp_path / "secret")
    (base / "loop").symlink_to(base / "loop")
    assert served(base, relative) == (404, {"error": "not found"})


def test_a_link_that_stays_inside_is_followed_and_direct_needs_the_folder_itself(tmp_path):
    base = tmp_path / "lib"
    (base / "sub").mkdir(parents=True)
    (base / "sub" / "b.js").write_bytes(b"b")
    (base / "alias.js").symlink_to(base / "sub" / "b.js")
    assert served(base, "alias.js")[1] == b"b"
    assert served(base, "sub/b.js", direct=True) == (404, {"error": "not found"})
    assert served(base, "alias.js", direct=True) == (404, {"error": "not found"})
    (base / "top.js").write_bytes(b"t")
    assert served(base, "top.js", direct=True)[1] == b"t"


def test_a_listed_file_is_served_uncached_and_an_unlisted_name_is_404(tmp_path):
    page = tmp_path / "page.css"
    page.write_bytes(b"css")
    reply = http_base.listed_file((page, "text/css; charset=utf-8"))
    assert (reply.status, reply.body) == (200, b"css")
    assert reply.headers == {"Content-Type": "text/css; charset=utf-8", "Cache-Control": "no-cache"}
    with pytest.raises(Reply) as refusal:
        http_base.listed_file(None)
    assert (refusal.value.status, refusal.value.body) == (404, {"error": "not found"})


@pytest.mark.parametrize("host", ["", "0.0.0.0", "::", "0", "0x0", "::ffff:0.0.0.0"])
def test_every_spelling_of_every_interface_is_a_wildcard(host):
    assert http_base.wildcard(host)


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "10.1.2.3", "not an address", "a" * 300])
def test_an_own_address_or_no_address_is_not_a_wildcard(host):
    assert not http_base.wildcard(host)


# -- what each real service passes ------------------------------------------------------------


def test_the_run_start_service_passes_its_own_parameters():
    handler = run_start_service.Handler
    assert handler.response_headers == ()  # its policies differ per route, so none is global
    assert handler.closes_http09 is True
    assert handler.connection_deadline is http_base.Handler.connection_deadline  # none
    assert handler.read_body is http_base.Handler.read_body  # a lost body is ClientGone
    assert handler.logger is run_start_service.log
    limits = run_start_service._Server.connection_limits(cast(Any, None))
    assert limits == (run_start_service.MAX_CONNECTIONS, None) == (64, None)
    assert run_start_service.MAX_JSON == 1024 * 1024
    assert {name for name in vars(handler) if name.startswith("do_")} == {
        "do_GET",
        "do_POST",
        "do_DELETE",
    }


def test_signal_passes_its_own_parameters():
    handler = signal_service.Handler
    assert dict(handler.response_headers) == {
        "Content-Security-Policy": signal_service._POLICY,
        "X-Frame-Options": "DENY",
    }
    assert handler.closes_http09 is True
    assert handler.connection_deadline(cast(Any, None)) == 2 * signal_service.SOCKET_TIMEOUT == 120
    assert handler.read_body is not http_base.Handler.read_body  # a lost body is a 400
    assert handler.logger is signal_service.log
    limits = signal_service._Server.connection_limits(cast(Any, None))
    assert limits == (64, 16)
    assert signal_service.MAX_JSON == 64 * 1024
