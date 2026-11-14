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
from test_signal_groups import AK, ML, T0, team_db

from deploy_workflow.signal import service
from deploy_workflow.signal.cli import main
from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.fetch import Fetched, FetchRefused
from deploy_workflow.signal.groups import Act, create_group, join
from deploy_workflow.signal.service import Loop, make_server
from deploy_workflow.signal.store import add_story, open_db, propose_source, set_source_state
from deploy_workflow.signal.threads import share_story

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


def _tree(base: Path, *parts: str) -> Path:
    web = base.joinpath(*parts)
    (web / "brand").mkdir(parents=True)
    (web / "brand.css").write_text("x")
    return web


def test_brand_files_are_found_in_the_repository_layout(tmp_path):
    web = _tree(tmp_path, "apps", "issuer-library", "credit_os", "web")
    assert service.find_brand(tmp_path) == web


def test_brand_files_are_found_in_the_packaged_layout(tmp_path):
    web = _tree(tmp_path, "credit_os", "web")  # engine/credit_os/web beside engine/src
    assert service.find_brand(tmp_path) == web


def test_brand_lookup_with_no_candidate_names_the_first_so_start_fails_loudly(tmp_path):
    assert service.find_brand(tmp_path) == (
        tmp_path / "apps" / "issuer-library" / "credit_os" / "web"
    )


def test_the_real_layout_has_the_brand_files():
    assert (service.find_brand(Path(service.__file__).resolve().parents[3]) / "brand.css").is_file()


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
        "threads",
    }
    assert svc.call("GET", "/api/feed?view=top", cookie=cookie)[0] == 400
    assert svc.call("POST", "/api/me", body={"name": "   "})[0] == 400


def test_me_without_a_name_and_status_need_no_name(svc):
    assert svc.call("GET", "/api/me")[2] == {"name": None}
    assert svc.call("GET", "/api/status")[0] == 200


def test_every_other_api_route_needs_a_name(svc):
    for method, path in (
        ("GET", "/api/feed?view=latest"),
        ("GET", "/api/feed/new?view=latest&after=0"),
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


def test_feed_carries_the_newest_story_id(svc, cookie):
    assert svc.call("GET", "/api/feed?view=latest", cookie=cookie)[2]["newest"] == 36


def test_new_count(svc, cookie):
    assert svc.call("GET", "/api/feed/new?view=latest&after=0", cookie=cookie)[2] == {"count": 36}
    assert svc.call("GET", "/api/feed/new?view=latest&after=36", cookie=cookie)[2] == {"count": 0}
    assert svc.call("GET", "/api/feed/new?view=latest", cookie=cookie)[0] == 400
    assert svc.call("GET", "/api/feed/new?after=0", cookie=cookie)[0] == 400
    assert svc.call("GET", "/api/feed/new?view=latest&after=x", cookie=cookie)[0] == 400
    assert svc.call("GET", "/api/feed/new?view=latest&after=-1", cookie=cookie)[0] == 400
    assert svc.call("GET", f"/api/feed/new?view=latest&after={'9' * 20}", cookie=cookie)[0] == 400
    assert (
        svc.call("GET", "/api/feed/new?view=latest&since=2026-11-13T09:00:00Z", cookie=cookie)[0]
        == 400
    )


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


def test_loop_pass_updates_status_and_recovers_from_a_failing_source_with_recorded_feed(
    svc_with_loop,
):
    # one approved source; fetch replaced: first call raises RuntimeError, later calls RSS
    loop, call = svc_with_loop
    loop.run_once(NOW)
    status = call("GET", "/api/status")[2]  # the source is recorded failing; the pass completes
    assert status["loop_error"] is None and status["sources"] == {"approved": 1, "failing": 1}
    assert status["last_pass_at"] == NOW.isoformat()
    later = NOW + timedelta(seconds=601)
    loop.run_once(later)
    status = call("GET", "/api/status")[2]
    assert status["loop_error"] is None and status["sources"] == {"approved": 1, "failing": 0}
    assert status["last_pass_at"] == later.isoformat()


def test_a_pass_that_raises_at_loop_level_is_shown_by_type_only_with_recorded_feed(
    svc_with_loop, monkeypatch
):
    loop, call = svc_with_loop
    good_run_due = service.ingest.run_due

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("secret")

    monkeypatch.setattr(service.ingest, "run_due", boom)
    loop.run_once(NOW)  # must not raise
    shown = call("GET", "/api/status")[2]["loop_error"]
    assert shown and "RuntimeError" in shown and "secret" not in shown
    monkeypatch.setattr(service.ingest, "run_due", good_run_due)
    loop.run_once(NOW + timedelta(seconds=601))
    assert call("GET", "/api/status")[2]["loop_error"] is None


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


def test_a_taken_port_names_the_address_and_exits_2(tmp_path, capsys):
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        port = taken.getsockname()[1]
        assert service.serve(tmp_path, "127.0.0.1", port) == 2
    message = capsys.readouterr().err.strip()
    assert message.startswith(f"cannot listen on 127.0.0.1:{port}: ") and "\n" not in message


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


def test_a_trickling_connection_is_closed_at_the_deadline(svc, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=service.log.name)
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
    cut = [r for r in caplog.records if "connection deadline reached" in r.getMessage()]
    assert len(cut) == 1
    assert cut[0].levelno == logging.INFO and cut[0].getMessage().startswith("127.0.0.1 ")
    assert cut[0].exc_info is None


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


# ---- groups and threads (slice 3, task 4) ----

TABLES = ("groups", "group_members", "threads", "comments", "reactions", "read_marks")


class Site(Live):
    """A server over a team database (users ak and ml are writers, rd a reader)."""

    def __init__(self, server: ThreadingHTTPServer, root: Path) -> None:
        super().__init__(server)
        self.root = root

    def counts(self) -> dict[str, int]:
        db = open_db(self.root)
        try:
            return {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABLES}
        finally:
            db.close()


def _team(root: Path, *, seeded: bool) -> None:
    """The team's users, sources and stories; seeded adds group 1 "TMT" (everyone; ak made it, ml
    joined at T0) with thread 1 (story 1, ak's note "look", at T0 + 1 minute) and group 2 "Inner"
    (invited; ak the only member) with thread 2 (story 2, ak's note "secret note")."""
    db = team_db(root)
    if seeded:
        tmt = create_group(db, Act(AK, T0), "TMT", "everyone", [])
        join(db, ML.name, tmt, T0)
        later = T0 + timedelta(minutes=1)
        share_story(db, Act(AK, later), tmt, 1, "look")
        inner = create_group(db, Act(AK, T0), "Inner", "invited", [])
        share_story(db, Act(AK, later), inner, 2, "secret note")
    db.close()


@pytest.fixture
def site(tmp_path: Path) -> Iterator[Site]:
    _team(tmp_path, seeded=False)
    live = Site(make_server(tmp_path, "127.0.0.1", 0), tmp_path)
    yield live
    live.close()


@pytest.fixture
def world(tmp_path: Path) -> Iterator[Site]:
    _team(tmp_path, seeded=True)
    live = Site(make_server(tmp_path, "127.0.0.1", 0), tmp_path)
    yield live
    live.close()


@pytest.fixture
def world_loop(tmp_path: Path) -> Iterator[tuple[Loop, Site]]:
    _team(tmp_path, seeded=True)
    loop = Loop(tmp_path)
    live = Site(make_server(tmp_path, "127.0.0.1", 0, loop=loop), tmp_path)
    yield loop, live
    live.close()


AK_C, ML_C, RD_C, ZZ_C = (f"signal_name={n}" for n in ("ak", "ml", "rd", "zz"))
NEW_GROUP = {"name": "New", "visibility": "everyone", "topics": []}

# Every POST and DELETE route of the table, on the world's visible group 1, thread 1, comment 1.
WRITES = [
    ("POST", "/api/groups", NEW_GROUP),
    ("POST", "/api/groups/1/members", {}),
    ("POST", "/api/groups/1/members", {"name": "rd"}),
    ("DELETE", "/api/groups/1/members", {}),
    ("DELETE", "/api/groups/1/members", {"name": "ak"}),
    ("POST", "/api/groups/1/threads", {"story_id": 2, "note": "n"}),
    ("POST", "/api/groups/1/threads", {"title": "T", "text": "x"}),
    ("POST", "/api/threads/1/read", {}),
    ("POST", "/api/threads/1/comments", {"text": "hi"}),
    ("POST", "/api/comments/1", {"text": "changed"}),
    ("DELETE", "/api/comments/1", None),
    ("POST", "/api/comments/1/reactions/up", None),
    ("DELETE", "/api/comments/1/reactions/up", None),
]
# Open to readers (status 200): a person joining or leaving an everyone-group themself, and the
# read route. Every other write is refused to a reader with 403.
OPEN_TO_READERS = [
    ("POST", "/api/groups/1/members", {}),
    ("DELETE", "/api/groups/1/members", {}),
    ("POST", "/api/threads/1/read", {}),
]

# The invited group's ids in the world are group 2, thread 2, comment 2; 999999 is missing.
HIDDEN_READS = [
    ("GET", "/api/groups/{g}", None),
    ("GET", "/api/groups/{g}/threads", None),
    ("GET", "/api/threads/{t}", None),
]
HIDDEN_WRITES = [
    ("POST", "/api/groups/{g}/members", {}),
    ("POST", "/api/groups/{g}/members", {"name": "ml"}),
    ("DELETE", "/api/groups/{g}/members", {}),
    ("DELETE", "/api/groups/{g}/members", {"name": "ak"}),
    ("POST", "/api/groups/{g}/threads", {"story_id": 1}),
    ("POST", "/api/groups/{g}/threads", {"title": "T", "text": "x"}),
    ("POST", "/api/threads/{t}/read", {}),
    ("POST", "/api/threads/{t}/comments", {"text": "x"}),
    ("POST", "/api/comments/{c}", {"text": "x"}),
    ("DELETE", "/api/comments/{c}", None),
    ("POST", "/api/comments/{c}/reactions/up", None),
    ("DELETE", "/api/comments/{c}/reactions/up", None),
]


def test_a_writer_creates_a_group_shares_a_story_and_a_reader_reads_the_thread_with_recorded_feed(
    site,
):
    status, _, made = site.call(
        "POST", "/api/groups", cookie=AK_C, body=NEW_GROUP | {"name": "TMT"}
    )
    assert (status, made) == (200, {"id": 1})
    status, _, shared = site.call(
        "POST", "/api/groups/1/threads", cookie=AK_C, body={"story_id": 1, "note": "look"}
    )
    assert (status, shared) == (200, {"thread_id": 1, "joined": False})
    status, _, thread = site.call("GET", "/api/threads/1", cookie=RD_C)
    assert status == 200
    assert thread["comments"][0]["text"] == "look"
    assert thread["can_post"] is False
    status, _, rows = site.call("GET", "/api/groups/1/threads", cookie=RD_C)
    assert status == 200 and rows["threads"][0]["source_kind"] == "regulator"
    status, _, page = site.call("GET", "/api/feed?view=latest", cookie=RD_C)
    card = next(c for c in page["cards"] if c["id"] == 1)
    expected = {"id": 1, "group": "TMT", "comments": 1, "shared_by": "ak", "note": "look"}
    assert status == 200 and card["threads"] == [expected]


@pytest.mark.parametrize("method,path,body", WRITES)
def test_a_reader_is_refused_every_write_and_nothing_changes(world, method, path, body):
    for who in (RD_C, ZZ_C):  # rd is a reader; zz is no one the store knows, so a reader too
        before = world.counts()
        status, _, reply = world.call(method, path, cookie=who, body=body)
        if (method, path, body) in OPEN_TO_READERS:
            assert status == 200, reply
            moves = ("group_members", "read_marks")  # what joining, leaving and reading write
            after = world.counts()
            assert {t: n for t, n in after.items() if t not in moves} == {
                t: n for t, n in before.items() if t not in moves
            }
        else:
            assert status == 403 and list(reply) == ["error"], reply
            assert world.counts() == before


@pytest.mark.parametrize("method,path,body", WRITES)
def test_every_write_without_this_sites_origin_is_refused(world, method, path, body):
    before = world.counts()
    status, _, _ = world.call(
        method, path, cookie=AK_C, body=body, origin="http://elsewhere.test:{port}"
    )
    assert status == 403
    assert world.counts() == before


@pytest.mark.parametrize("method,path,body", HIDDEN_READS + HIDDEN_WRITES)
def test_a_hidden_group_answers_exactly_like_a_missing_one(world, method, path, body):
    before = world.counts()
    hidden = path.format(g=2, t=2, c=2)
    missing = path.format(g=999999, t=999999, c=999999)
    seen = world.call(method, hidden, cookie=ML_C, body=body)
    gone = world.call(method, missing, cookie=ML_C, body=body)
    assert seen[0] == 404
    assert (seen[0], seen[2]) == (gone[0], gone[2])
    assert world.counts() == before


def test_a_hidden_group_is_absent_from_lists_counts_and_cards(world):
    groups = world.call("GET", "/api/groups", cookie=ML_C)[2]
    assert [g["id"] for g in groups["groups"]] == [1]
    unread = world.call("GET", "/api/unread", cookie=ML_C)[2]
    assert set(unread["by_group"]) <= {"1"}
    everything = json.dumps(
        [groups, unread, world.call("GET", "/api/feed?view=latest", cookie=ML_C)[2]]
    )
    assert "Inner" not in everything and "secret note" not in everything
    cards = world.call("GET", "/api/feed?view=latest", cookie=ML_C)[2]["cards"]
    assert next(c for c in cards if c["id"] == 2)["threads"] == []
    own = world.call("GET", "/api/feed?view=latest", cookie=AK_C)[2]["cards"]
    assert [t["group"] for t in next(c for c in own if c["id"] == 2)["threads"]] == ["Inner"]


@pytest.mark.parametrize(
    "body",
    [
        b"[]",
        b'{"text": 5}',
        b'{"text": ""}',
        b'{"parent": "1", "text": "x"}',
        b'{"text": "' + b"x" * 4001 + b'"}',
    ],
)
def test_a_malformed_comment_is_a_400_not_a_500(world, body):
    before = world.counts()
    status, _, reply = world.call("POST", "/api/threads/1/comments", cookie=AK_C, raw=body)
    assert status == 400 and list(reply) == ["error"]
    assert world.counts() == before


@pytest.mark.parametrize(
    "path,body",
    [
        ("/api/groups/1/threads", {"story_id": True}),
        ("/api/groups/1/threads", {"story_id": 1.0}),
        ("/api/groups/1/threads", {"story_id": "1"}),
        ("/api/groups/1/threads", {"story_id": 1, "note": 5}),
        ("/api/groups/1/threads", {"story_id": 1, "title": "T", "text": "x"}),
        ("/api/groups/1/threads", {}),
        ("/api/groups/1/threads", {"title": "T"}),
        ("/api/groups/1/threads", {"story_id": 1, "extra": 1}),
        ("/api/groups", {"name": "N", "visibility": "everyone", "topics": [True]}),
        ("/api/groups", {"name": "N", "visibility": "everyone", "topics": "1"}),
        ("/api/groups", {"name": 5, "visibility": "everyone"}),
        ("/api/groups", {"name": "N", "visibility": None}),
        ("/api/groups", {"name": "N", "visibility": "everyone", "topics": [999]}),
        ("/api/threads/1/comments", {"text": "x", "parent": True}),
        ("/api/threads/1/comments", {"text": "x", "parent": 1.0}),
        ("/api/groups/1/members", {"name": 5}),
        ("/api/comments/1", {"text": None}),
    ],
)
def test_wrong_types_and_shapes_are_a_400_never_a_500(world, path, body):
    before = world.counts()
    status, _, reply = world.call("POST", path, cookie=AK_C, body=body)
    assert status == 400 and list(reply) == ["error"], reply
    assert world.counts() == before


def test_a_comment_posted_during_an_ingest_pass_succeeds_with_recorded_feed(world_loop):
    loop, site = world_loop  # the loop's fetch function blocks on an Event mid-pass
    with pass_in_progress(loop):
        status, _, made = site.call(
            "POST", "/api/threads/1/comments", cookie=AK_C, body={"text": "during"}
        )
        assert status == 200 and "id" in made
    assert loop.last_error is None


def test_unread_rides_the_poll_and_clears_on_read(world):
    unread = world.call("GET", "/api/unread", cookie=ML_C)[2]
    assert unread == {"replies": 0, "threads": 1, "total": 1, "by_group": {"1": 1}}
    assert world.call("GET", "/api/groups", cookie=ML_C)[2]["groups"][0]["unread"] == 1
    status, _, read = world.call("POST", "/api/threads/1/read", cookie=ML_C, body={})
    assert status == 200 and read["unread"]["total"] == 0
    assert world.call("GET", "/api/groups", cookie=ML_C)[2]["groups"][0]["unread"] == 0


def test_reading_a_thread_does_not_record_it_as_read(world):
    world.call("GET", "/api/threads/1", cookie=ML_C)
    assert world.call("GET", "/api/unread", cookie=ML_C)[2]["total"] == 1


def test_group_list_and_detail_carry_what_the_page_needs(world):
    listed = world.call("GET", "/api/groups", cookie=RD_C)[2]
    assert listed["can_create"] is False
    assert listed["groups"] == [
        {
            "id": 1,
            "name": "TMT",
            "visibility": "everyone",
            "member": False,
            "members": 2,
            "threads": 1,
            "unread": 0,
        }
    ]
    assert world.call("GET", "/api/groups", cookie=AK_C)[2]["can_create"] is True
    detail = world.call("GET", "/api/groups/1", cookie=ML_C)[2]
    assert detail == {
        "id": 1,
        "name": "TMT",
        "visibility": "everyone",
        "member": True,
        "can_manage": True,
        "members": ["ak", "ml"],
    }
    assert world.call("GET", "/api/groups/1", cookie=RD_C)[2]["can_manage"] is False


def test_members_are_joined_added_and_removed_and_the_reply_is_the_list(world):
    assert world.call("POST", "/api/groups/1/members", cookie=RD_C, body={})[2] == {
        "members": ["ak", "ml", "rd"]
    }
    assert world.call("DELETE", "/api/groups/1/members", cookie=RD_C, body={})[2] == {
        "members": ["ak", "ml"]
    }
    assert world.call("POST", "/api/groups/2/members", cookie=AK_C, body={"name": "ml"})[2] == {
        "members": ["ak", "ml"]
    }
    assert world.call("DELETE", "/api/groups/2/members", cookie=AK_C, body={"name": "ml"})[2] == {
        "members": ["ak"]
    }
    status, _, refused = world.call("DELETE", "/api/groups/2/members", cookie=AK_C, body={})
    assert status == 400 and "writer" in refused["error"]  # the last writer cannot leave


def test_threads_page_comments_and_reactions_round_trip(world):
    rows = world.call("GET", "/api/groups/1/threads", cookie=ML_C)[2]
    assert rows["next_before"] is None and [r["id"] for r in rows["threads"]] == [1]
    assert world.call("GET", "/api/groups/1/threads?before=bad", cookie=ML_C)[0] == 400
    made = world.call(
        "POST", "/api/threads/1/comments", cookie=ML_C, body={"text": "a", "parent": 1}
    )
    assert made[2] == {"id": 2 + 1}  # comments 1 and 2 exist already (thread 2's note is 2)
    assert world.call("POST", "/api/comments/3/reactions/eyes", cookie=AK_C)[2] == {}
    assert world.call("POST", "/api/comments/3/reactions/nope", cookie=AK_C)[0] == 400
    thread = world.call("GET", "/api/threads/1", cookie=AK_C)[2]
    reactions = thread["comments"][1]["reactions"]
    assert reactions == [{"key": "eyes", "count": 1, "mine": True}]
    assert world.call("POST", "/api/comments/3", cookie=ML_C, body={"text": "b"})[2] == {}
    assert world.call("DELETE", "/api/comments/3", cookie=ML_C)[2] == {}
    assert world.call("GET", "/api/threads/1", cookie=AK_C)[2]["comments"][1]["removed"] is True


def test_feed_shared_accepts_only_one(world):
    shared = world.call("GET", "/api/feed?view=latest&shared=1", cookie=ML_C)[2]["cards"]
    assert [c["id"] for c in shared] == [1]  # ak shared story 1 into ml's group
    assert world.call("GET", "/api/feed?view=latest&shared=1", cookie=AK_C)[2]["cards"] == []
    for value in ("0", "true", "", "2"):
        assert world.call("GET", f"/api/feed?view=latest&shared={value}", cookie=ML_C)[0] == 400


SURROGATE_ROUTES = [
    ("POST", "/api/groups"),
    ("POST", "/api/groups/1/members"),
    ("DELETE", "/api/groups/1/members"),
    ("POST", "/api/groups/1/threads"),
    ("POST", "/api/threads/1/comments"),
    ("POST", "/api/comments/1"),
    ("POST", "/api/threads/1/read"),
]


@pytest.mark.parametrize("method,path", SURROGATE_ROUTES)
def test_a_field_name_that_is_a_lone_surrogate_is_an_ordinary_400(world, method, path):
    before = world.counts()
    status, _, reply = world.call(method, path, cookie=ZZ_C, raw=b'{"\\ud800": 1}')
    assert status == 400 and list(reply) == ["error"]
    assert "\ud800" not in json.dumps(reply, ensure_ascii=False)  # no client text in a refusal
    assert world.call("GET", "/api/groups", cookie=AK_C)[0] == 200
    assert world.counts() == before


def test_a_refusal_that_cannot_be_encoded_is_the_documented_500_and_is_logged(
    world, monkeypatch, caplog
):
    def echo(*args, **kwargs):
        raise service.store.StoreError("\ud800 is not a thing")  # a store text echoing input

    monkeypatch.setattr(service.groups, "list_groups", echo)
    with caplog.at_level(logging.ERROR, logger=service.log.name):
        status, _, reply = world.call("GET", "/api/groups", cookie=AK_C)
    assert (status, reply) == (500, {"error": "the service failed; see its log"})
    assert any(r.exc_info for r in caplog.records)
    monkeypatch.undo()
    assert world.call("GET", "/api/groups", cookie=AK_C)[0] == 200


@pytest.mark.parametrize("raw", [b"[]", b'{"a": 1}', b'{"text": "x"}', b"5"])
def test_the_read_route_needs_an_empty_json_object(world, raw):
    before = world.counts()
    status, _, reply = world.call("POST", "/api/threads/1/read", cookie=ML_C, raw=raw)
    assert status == 400 and list(reply) == ["error"]
    assert world.counts() == before
    assert world.call("POST", "/api/threads/1/read", cookie=ML_C, raw=b"{}")[0] == 200


def test_leaving_an_invited_group_as_a_non_last_member_hides_it_from_the_leaver(world):
    world.call("POST", "/api/groups/2/members", cookie=AK_C, body={"name": "ml"})
    status, _, reply = world.call("DELETE", "/api/groups/2/members", cookie=ML_C, body={})
    assert (status, reply) == (200, {"members": []})
    db = open_db(world.root)
    try:
        gone = db.execute("SELECT 1 FROM group_members WHERE group_id=2 AND user_name='ml'")
        assert gone.fetchone() is None
    finally:
        db.close()
    assert world.call("GET", "/api/groups/2", cookie=ML_C)[0] == 404


@pytest.mark.parametrize("method,path,body", WRITES)
def test_every_write_with_no_origin_header_is_refused(world, method, path, body):
    before = world.counts()
    status, _, _ = world.call(method, path, cookie=AK_C, body=body, origin=None)
    assert status == 403
    assert world.counts() == before
