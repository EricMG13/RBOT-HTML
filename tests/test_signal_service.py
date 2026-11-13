"""Signal's HTTP service, run for real on a loopback port over a seeded store.

Every request is hostile input: these tests pin the host and origin checks, the static allowlist,
the body limits, the display-name rule and that the ingest loop survives a failing pass. Tests whose
fetch is replaced say so in their names; nothing here reaches beyond loopback.
"""

from __future__ import annotations

import http.client
import json
import logging
import socket
import sqlite3
import threading
import time
import urllib.parse
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from test_signal_feeds import RSS
from test_signal_feedview import build_feed_db

from deploy_workflow.signal import service
from deploy_workflow.signal.cli import main
from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.fetch import Fetched, FetchRefused
from deploy_workflow.signal.service import Loop, make_server
from deploy_workflow.signal.store import add_story, open_db, propose_source, set_source_state

NOW = datetime(2026, 11, 13, 10, 0, tzinfo=UTC)
SAME = object()  # "the page's own origin", the default for a request that is not a GET


class Live:
    """A server on a thread and the helper that talks to it."""

    def __init__(self, server: ThreadingHTTPServer) -> None:
        self.server = server
        self.port = server.server_address[1]
        self.thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        )
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=10)

    def call(self, method: str, path: str, **request: Any) -> tuple[int, Any, Any]:
        """Keywords: body (JSON object), raw (bytes), origin (default: the page's own; None for
        none; ``{port}`` is filled in), cookie, host, headers."""
        sent = {"Host": request.get("host") or f"127.0.0.1:{self.port}"}
        origin = request.get("origin", SAME)
        if origin is SAME:
            origin = f"http://127.0.0.1:{self.port}"
        if origin is not None and method != "GET":
            sent["Origin"] = str(origin).replace("{port}", str(self.port))
        if request.get("cookie"):
            sent["Cookie"] = request["cookie"]
        sent.update(request.get("headers") or {})
        body, raw = request.get("body"), request.get("raw")
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            connection.request(method, path, body=data, headers=sent)
            response = connection.getresponse()
            text = response.read().decode("utf-8", errors="replace")
            kind = response.getheader("Content-Type") or ""
            return response.status, response.headers, json.loads(text) if "json" in kind else text
        finally:
            connection.close()


@pytest.fixture
def svc(tmp_path: Path) -> Iterator[Live]:
    build_feed_db(tmp_path).close()
    live = Live(make_server(tmp_path, "127.0.0.1", 0))
    yield live
    live.close()


@pytest.fixture
def cookie() -> str:
    return "signal_name=Reader"


def _recorded_feed_fn() -> Any:
    calls: list[str] = []

    def fetch(url: str, etag: str | None, modified: str | None) -> Fetched:
        calls.append(url)
        if len(calls) == 1:
            raise RuntimeError("the feed host fell over")
        return Fetched(RSS, None, None)

    return fetch


@pytest.fixture
def svc_with_loop(tmp_path: Path) -> Iterator[tuple[Loop, Any]]:
    db = open_db(tmp_path)
    set_source_state(
        db, propose_source(db, "Authority", "regulator", "https://a.org/f", "x"), "approved"
    )
    add_story(db, 1, Entry("Story one", "https://a.org/1", NOW, "Summary"), NOW)
    db.close()
    loop = Loop(tmp_path, fetch_fn=_recorded_feed_fn())
    live = Live(make_server(tmp_path, "127.0.0.1", 0, loop=loop))
    yield loop, live.call
    live.close()


@contextmanager
def pass_in_progress(loop: Loop) -> Iterator[None]:
    """Hold one pass inside its fetch (a recorded feed behind an Event) while the body runs."""
    entered, release = threading.Event(), threading.Event()

    def blocked(url: str, etag: str | None, modified: str | None) -> Fetched:
        entered.set()
        assert release.wait(timeout=20)
        return Fetched(RSS, None, None)

    loop.fetch_fn = blocked
    worker = threading.Thread(target=loop.run_once, args=(NOW,))
    worker.start()
    try:
        assert entered.wait(timeout=20)
        yield
    finally:
        release.set()
        worker.join(timeout=20)
    assert not worker.is_alive()


def test_page_and_static_files_with_strict_policy(svc):
    status, headers, _ = svc.call("GET", "/")
    assert status == 200 and "script-src 'self'" in headers["Content-Security-Policy"]
    assert "'unsafe-inline'" not in headers["Content-Security-Policy"]
    assert (
        headers["X-Content-Type-Options"] == "nosniff"
        and headers["Cross-Origin-Resource-Policy"] == "same-origin"
    )
    assert svc.call("GET", "/static/signal.js")[0] == 200
    for path in (
        "/static/../store.py",
        "/static/store.py",
        "/static/%2e%2e/cli.py",
        "/signal/signal.db",
        "/static/",
    ):
        assert svc.call("GET", path)[0] == 404


def test_page_policy_is_exact_and_on_every_response(svc):
    policy = (
        "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; "
        "frame-ancestors 'none'"
    )
    for path in ("/", "/static/signal.css", "/api/me", "/nowhere"):
        assert svc.call("GET", path)[1]["Content-Security-Policy"] == policy
    assert svc.call("GET", "/")[2].lstrip().lower().startswith("<!doctype html>")


def test_brand_files_are_served_with_their_types(svc):
    for name, kind in (
        ("brand.css", "text/css"),
        ("fonts/RedHatText-Regular.woff2", "font/woff2"),
        ("brand/symbol.svg", "image/svg+xml"),
    ):
        status, headers, _ = svc.call("GET", "/static/" + name)
        assert status == 200 and headers["Content-Type"].startswith(kind)
        assert headers["Cache-Control"] == "no-cache"
    assert svc.call("GET", "/static/fonts/OFL.txt")[0] == 404
    assert svc.call("GET", "/static/fonts/../brand.css")[0] == 404


def test_a_missing_brand_file_fails_at_start(tmp_path, monkeypatch):
    monkeypatch.setitem(service.STATIC, "gone.css", (tmp_path / "gone.css", "text/css"))
    with pytest.raises(service.StartError, match="gone.css"):
        make_server(tmp_path, "127.0.0.1", 0)


def test_name_then_feed(svc):
    assert svc.call("GET", "/api/feed?view=latest")[0] == 401
    status, headers, _ = svc.call("POST", "/api/me", body={"name": "  A.  Kovac "})
    assert status == 200 and headers["Set-Cookie"].startswith("signal_name=A.%20Kovac;")
    cookie = headers["Set-Cookie"].split(";")[0]
    assert svc.call("GET", "/api/me", cookie=cookie)[2] == {"name": "A. Kovac", "role": "reader"}
    status, _, data = svc.call("GET", "/api/feed?view=latest", cookie=cookie)
    assert status == 200 and len(data["cards"]) == 30 and data["next_before"]
    assert set(data["cards"][0]) == {
        "id",
        "title",
        "link",
        "summary",
        "source",
        "kind",
        "published_at",
        "other_sources",
        "saved",
        "topics",
    }
    assert svc.call("GET", "/api/feed?view=top", cookie=cookie)[0] == 400
    assert svc.call("POST", "/api/me", body={"name": "   "})[0] == 400


def test_me_without_a_name_and_status_need_no_name(svc):
    assert svc.call("GET", "/api/me")[2] == {"name": None}
    assert svc.call("GET", "/api/status")[0] == 200


def test_every_other_api_route_needs_a_name(svc):
    for method, path in (
        ("GET", "/api/feed?view=latest"),
        ("GET", "/api/feed/new?view=latest&since=2026-11-13T00:00:00%2B00:00"),
        ("POST", "/api/stories/5/save"),
        ("DELETE", "/api/stories/5/save"),
        ("GET", "/api/topics"),
        ("POST", "/api/topics/1/follow"),
        ("DELETE", "/api/topics/1/follow"),
    ):
        status, _, data = svc.call(method, path)
        assert (status, data) == (401, {"error": "choose a display name first"}), path


def test_paging_follows_the_cursor(svc, cookie):
    first = svc.call("GET", "/api/feed?view=latest", cookie=cookie)[2]
    second = svc.call(
        "GET",
        "/api/feed?view=latest&before=" + urllib.parse.quote(first["next_before"]),
        cookie=cookie,
    )[2]
    assert len(second["cards"]) == 6 and second["next_before"] is None


def test_feed_parameters(svc, cookie):
    assert svc.call("GET", "/api/feed", cookie=cookie)[0] == 400
    assert (
        svc.call("GET", "/api/feed?view=latest&kind=news", cookie=cookie)[2]["cards"][0]["kind"]
        == "news"
    )
    assert svc.call("GET", "/api/feed?view=latest&kind=bogus", cookie=cookie)[0] == 400
    assert svc.call("GET", "/api/feed?view=latest&before=junk", cookie=cookie)[0] == 400
    # a repeated parameter uses the first
    assert svc.call("GET", "/api/feed?view=saved&view=latest", cookie=cookie)[2]["cards"] == []
    assert svc.call("GET", "/api/feed?view=%ff", cookie=cookie)[0] == 400
    assert svc.call("GET", "/api/feed?q=remedy&view=latest", cookie=cookie)[2]["cards"][0][
        "title"
    ].startswith("Wire")


def test_new_count(svc, cookie):
    since = urllib.parse.quote("2026-11-13T09:00:00+00:00")
    assert svc.call("GET", f"/api/feed/new?view=latest&since={since}", cookie=cookie)[2] == {
        "count": 36
    }
    assert svc.call("GET", "/api/feed/new?view=latest", cookie=cookie)[0] == 400
    assert svc.call("GET", f"/api/feed/new?since={since}", cookie=cookie)[0] == 400
    assert svc.call("GET", "/api/feed/new?view=latest&since=yesterday", cookie=cookie)[0] == 400


def test_save_and_follow_round_trip(svc, cookie):
    assert svc.call("POST", "/api/stories/5/save", cookie=cookie)[2] == {"saved": True}
    assert [
        c["id"] for c in svc.call("GET", "/api/feed?view=saved", cookie=cookie)[2]["cards"]
    ] == [5]
    assert svc.call("DELETE", "/api/stories/5/save", cookie=cookie)[2] == {"saved": False}
    assert svc.call("POST", "/api/stories/9999/save", cookie=cookie)[0] == 404
    assert svc.call("POST", "/api/topics/1/follow", cookie=cookie)[2] == {"following": True}
    assert svc.call("GET", "/api/topics", cookie=cookie)[2][0]["following"] == 1
    assert svc.call("POST", "/api/topics/99/follow", cookie=cookie)[0] == 404
    assert svc.call("DELETE", "/api/topics/1/follow", cookie=cookie)[2] == {"following": False}
    topic = svc.call("GET", "/api/topics", cookie=cookie)[2][0]
    assert set(topic) == {"id", "name", "following", "stories"} and topic["following"] == 0


@pytest.mark.parametrize("ident", ["abc", "-1", "5.0", "1" * 19, "%D9%A5", "5%20", ""])
def test_ids_in_paths_are_ascii_digits_of_at_most_18(svc, cookie, ident):
    assert svc.call("POST", f"/api/stories/{ident}/save", cookie=cookie)[0] == 404
    assert svc.call("POST", f"/api/topics/{ident}/follow", cookie=cookie)[0] == 404


def test_an_eighteen_digit_story_id_is_an_unknown_story(svc, cookie):
    assert svc.call("POST", "/api/stories/" + "9" * 18 + "/save", cookie=cookie)[0] == 404


@pytest.mark.parametrize(
    "origin", [None, "http://evil.example", "https://127.0.0.1:{port}", "null"]
)
def test_a_write_from_another_origin_changes_nothing(svc, cookie, origin):
    assert svc.call("POST", "/api/stories/5/save", cookie=cookie, origin=origin)[0] == 403
    assert svc.call("POST", "/api/me", body={"name": "Eve"}, origin=origin)[0] == 403
    assert svc.call("GET", "/api/feed?view=saved", cookie=cookie)[2]["cards"] == []


def test_other_host_names_and_cross_site_reads_are_refused(svc, cookie):
    assert svc.call("GET", "/", host="evil.example")[0] == 403
    assert (
        svc.call(
            "GET", "/api/feed?view=latest", cookie=cookie, headers={"Sec-Fetch-Site": "cross-site"}
        )[0]
        == 403
    )


def test_host_rules_and_fetch_metadata(svc, cookie):
    assert svc.call("GET", "/api/me", host=f"localhost:{svc.port}")[0] == 200
    assert svc.call("GET", "/api/me", host="127.0.0.1")[0] == 403
    assert svc.call("GET", "/api/me", host=f"evil.example:{svc.port}")[0] == 403
    for site in ("same-origin", "none"):
        assert svc.call("GET", "/api/me", headers={"Sec-Fetch-Site": site})[0] == 200
    navigation = {
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
    }
    assert svc.call("GET", "/", headers=navigation)[0] == 200
    assert svc.call("GET", "/api/me", headers=navigation)[0] == 200
    assert svc.call("POST", "/api/stories/5/save", cookie=cookie, headers=navigation)[0] == 403
    assert svc.call("GET", "/api/me", headers={"Origin": "http://evil.example"})[0] == 403


def test_bodies_are_capped_and_must_be_json(svc):
    assert svc.call("POST", "/api/me", raw=b"x" * (64 * 1024 + 1))[0] == 413
    assert svc.call("POST", "/api/me", raw=b"{not json")[0] == 400
    assert svc.call("POST", "/api/me", raw=b"[]")[0] == 400
    assert svc.call("POST", "/api/me", body={"name": 5})[0] == 400


def test_a_json_body_needs_content_length(svc):
    connection = http.client.HTTPConnection("127.0.0.1", svc.port, timeout=20)
    connection.putrequest("POST", "/api/me", skip_accept_encoding=True)
    connection.putheader("Origin", f"http://127.0.0.1:{svc.port}")
    connection.endheaders()
    assert connection.getresponse().status == 411
    connection.close()


def test_search_text_cannot_break_the_api(svc, cookie):
    for q in ['"', "*", "NEAR(", "%00", "a" * 5000]:
        assert (
            svc.call("GET", "/api/feed?view=latest&q=" + urllib.parse.quote(q), cookie=cookie)[0]
            == 200
        )


def test_unknown_paths_and_methods(svc, cookie):
    assert svc.call("GET", "/api/nothing", cookie=cookie)[0] == 404
    assert svc.call("GET", "/nothing")[0] == 404
    assert svc.call("DELETE", "/api/me", cookie=cookie)[0] == 405
    assert svc.call("POST", "/api/feed?view=latest", cookie=cookie)[0] == 405
    assert svc.call("PUT", "/api/me", cookie=cookie)[0] == 405
    assert svc.call("POST", "/")[0] == 405
    assert svc.call("GET", "/api/stories/5/save", cookie=cookie)[0] == 405


def test_an_unexpected_failure_is_a_plain_500(svc, cookie, monkeypatch, caplog):
    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("secret-cause")

    monkeypatch.setattr(service.feedview, "feed", boom)
    status, _, data = svc.call("GET", "/api/feed?view=latest", cookie=cookie)
    assert (status, data) == (500, {"error": "the service failed; see its log"})
    assert "secret-cause" in caplog.text


def test_the_service_serves_no_file_from_the_root(svc):
    for path in ("/signal/signal.db", "/signal.db", "/static/signal.db", "/..%2fsignal/signal.db"):
        assert svc.call("GET", path)[0] in (403, 404)


def test_loop_pass_updates_status_and_survives_a_failing_pass_with_recorded_feed(svc_with_loop):
    # one approved source; fetch replaced: first call raises RuntimeError, later calls RSS
    loop, call = svc_with_loop
    loop.run_once(NOW)
    assert call("GET", "/api/status")[2]["loop_error"]  # the failure is visible
    assert "fell over" not in call("GET", "/api/status")[2]["loop_error"]
    loop.run_once(NOW + timedelta(seconds=60))
    status = call("GET", "/api/status")[2]
    assert status["loop_error"] is None and status["sources"] == {"approved": 1, "failing": 0}
    assert status["last_pass_at"] == (NOW + timedelta(seconds=60)).isoformat()


def test_a_save_during_a_pass_succeeds(svc_with_loop, cookie):
    loop, call = svc_with_loop  # fetch replaced by one that blocks on an Event mid-pass
    with pass_in_progress(loop):
        assert call("POST", "/api/stories/1/save", cookie=cookie)[0] == 200


def test_status_counts_a_failing_source_with_recorded_feed(svc_with_loop):
    loop, call = svc_with_loop

    def refused(url: str, etag: str | None, modified: str | None) -> Fetched:
        raise FetchRefused("not a feed")

    loop.fetch_fn = refused
    loop.run_once(NOW)
    assert call("GET", "/api/status")[2]["sources"] == {"approved": 1, "failing": 1}
    assert call("GET", "/api/status")[2]["loop_error"] is None


def test_a_wildcard_host_is_refused_at_start(tmp_path):
    with pytest.raises(ValueError, match="own address"):
        make_server(tmp_path, "0.0.0.0", 0)
    assert not (tmp_path / "signal").exists()


def test_wildcard_host_is_refused():
    assert main(["--root", "x", "serve", "--host", "0.0.0.0"]) == 2


def _raw(svc: Live, data: bytes) -> socket.socket:
    sock = socket.create_connection(("127.0.0.1", svc.port), timeout=10)
    sock.sendall(data)
    return sock


def _closed_within(sock: socket.socket, seconds: float) -> bool:
    """True when the server closed the connection (EOF or reset) within ``seconds``."""
    sock.settimeout(seconds)
    try:
        while sock.recv(4096):
            pass
    except (ConnectionResetError, BrokenPipeError):
        return True
    except TimeoutError:
        return False
    return True


def test_a_trickling_connection_is_closed_at_the_deadline(svc, monkeypatch):
    monkeypatch.setattr(service, "SOCKET_TIMEOUT", 0.5)
    monkeypatch.setattr(service.Handler, "timeout", 5)  # per-read timeout longer than the deadline
    host = f"127.0.0.1:{svc.port}"
    sock = _raw(svc, f"GET /api/status HTTP/1.1\r\nHost: {host}\r\nX-Pad: ".encode())
    stop = threading.Event()

    def trickle() -> None:
        while not stop.is_set():
            try:
                sock.sendall(b"a")
            except OSError:
                return
            time.sleep(0.1)

    thread = threading.Thread(target=trickle, daemon=True)
    thread.start()
    try:
        assert _closed_within(sock, 4)
    finally:
        stop.set()
        thread.join(timeout=5)
        sock.close()
    assert svc.call("GET", "/api/status")[0] == 200


def test_one_address_has_a_share_of_the_connection_ceiling(svc, monkeypatch):
    monkeypatch.setattr(service, "MAX_PER_ADDRESS", 3)
    held = [_raw(svc, b"") for _ in range(3)]
    try:
        time.sleep(0.3)
        extra = _raw(svc, b"")
        assert _closed_within(extra, 3)
        extra.close()
        assert all(not _closed_within(sock, 0.3) for sock in held)
    finally:
        for sock in held:
            sock.close()
    time.sleep(0.3)
    assert svc.call("GET", "/api/status")[0] == 200


def test_a_short_body_is_a_refusal_not_a_traceback(svc, monkeypatch, caplog):
    monkeypatch.setattr(service.Handler, "timeout", 1)
    caplog.set_level(logging.INFO)
    host = f"127.0.0.1:{svc.port}"
    head = f"POST /api/me HTTP/1.1\r\nHost: {host}\r\nOrigin: http://{host}\r\n"
    sock = _raw(svc, (head + 'Content-Length: 50\r\n\r\n{"na').encode())
    sock.settimeout(10)
    reply = sock.recv(4096)
    sock.close()
    time.sleep(0.2)
    assert reply.split(b"\r\n")[0].split()[1] == b"400"
    assert b"the request body did not arrive" in reply
    assert not [record for record in caplog.records if record.exc_info]


def test_an_http_09_request_line_gets_no_500(svc, caplog):
    sock = _raw(svc, b"GET /api/me\r\n")
    sock.settimeout(10)
    reply = b""
    while chunk := sock.recv(4096):
        reply += chunk
    sock.close()
    time.sleep(0.2)
    assert b"the service failed" not in reply and b" 500 " not in reply
    assert not [record for record in caplog.records if record.exc_info]


def test_a_save_waits_for_a_held_write_lock(svc_with_loop, cookie, tmp_path):
    _, call = svc_with_loop
    other = sqlite3.connect(
        tmp_path / "signal" / "signal.db", isolation_level=None, check_same_thread=False
    )
    other.execute("BEGIN IMMEDIATE")
    release = threading.Timer(0.5, lambda: other.execute("COMMIT"))
    release.start()
    try:
        started = time.monotonic()
        assert call("POST", "/api/stories/1/save", cookie=cookie)[0] == 200
        assert time.monotonic() - started >= 0.3  # it did wait for the lock
    finally:
        release.join()
        other.close()
