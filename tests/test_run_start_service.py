"""The start page's HTTP service, run for real on port 0 over the fake launcher: no provider.

Every request is hostile input: these tests pin the host and origin checks, the library route's
boundary, the upload limits, the approval digest and that no response carries the provider key.
"""

from __future__ import annotations

import errno
import json
import logging
import os
import shutil
import socket
import struct
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

import pytest
from inbox_fixtures import CONTEXT, KEY, layout, pump, settings, submit_run

from deploy_workflow.inbox.runs import load_all
from deploy_workflow.inbox.scheduler import Scheduler
from deploy_workflow.run_start import service, submissions

pytest_plugins = ["inbox_fixtures"]

PATHWAY = "credit_snapshot"
MARKER = "sk-marker-value-that-must-never-leave-the-service"


def answers_for(**change: Any) -> dict[str, Any]:
    context = json.loads(json.dumps(CONTEXT))
    context["run"]["pathway"] = PATHWAY
    context["run"]["as_of"] = "2026-11-09"
    context["identity"]["issuer_id"] = "acme"
    context["identity"]["issuer_name"] = "Acme Corp"
    base: dict[str, Any] = {
        "context": context,
        "modules": [],
        "max_turns": 32,
        "level": "basic",
        "model": "gpt",
        "effort": "balanced",
        "submitted_by": "analyst",
    }
    base.update(change)
    return base


@dataclass
class Reply:
    status: int
    headers: Any
    body: bytes

    def json(self) -> Any:
        return json.loads(self.body)


@dataclass
class Service:
    watcher: Scheduler
    server: ThreadingHTTPServer
    root: Path

    @property
    def host(self) -> str:
        return f"127.0.0.1:{self.server.server_address[1]}"

    def call(
        self,
        method: str,
        path: str,
        body: bytes | dict[str, Any] | None = None,
        *,
        origin: str | None = "",
        headers: dict[str, str] | None = None,
    ) -> Reply:
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        request = urllib.request.Request(f"http://{self.host}{path}", data=data, method=method)
        if origin == "":
            origin = f"http://{self.host}"
        if origin is not None and method != "GET":
            request.add_header("Origin", origin)
        for name, value in (headers or {}).items():
            request.add_header(name, value)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return Reply(response.status, response.headers, response.read())
        except urllib.error.HTTPError as error:
            return Reply(error.code, error.headers, error.read())

    def new(self) -> str:
        made = self.call("POST", "/api/submissions")
        assert made.status == 200, made.body
        return str(made.json()["id"])

    def upload(self, sid: str, name: str, payload: bytes) -> Reply:
        quoted = urllib.parse.quote(name, safe="")
        return self.call("POST", f"/api/submissions/{sid}/files?name={quoted}", payload)


@pytest.fixture
def service_factory(root: Path, fake_env: Callable[[dict[str, Any]], None]) -> Iterator[Any]:
    started: list[Service] = []

    def start(host: str = "127.0.0.1") -> Service:
        fake_env({"sleep": 30})
        watcher = Scheduler(settings(root))
        server = service.make_server(watcher, host, 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        started.append(Service(watcher, server, root))
        return started[-1]

    yield start
    for item in started:
        item.server.shutdown()
        item.server.server_close()
        item.watcher.close()


@pytest.fixture
def svc(service_factory: Callable[[], Service]) -> Service:
    return service_factory()


def test_upload_read_summarise_submit_and_see_the_run(svc):
    page = svc.call("GET", "/")
    assert page.status == 200
    assert page.headers["Content-Type"].startswith("text/html")
    assert b"<title" in page.body
    sid = svc.new()
    stored = svc.upload(sid, "notes/a.txt", b"Net sales were 100.")
    assert (stored.status, stored.json()["name"]) == (200, "notes/a.txt")
    reading = svc.call("GET", f"/api/submissions/{sid}/reading").json()
    assert reading["error"] == "" and reading["documents"], reading
    answers = answers_for()
    got = svc.call("POST", f"/api/submissions/{sid}/summary", answers)
    assert got.status == 200
    summary = got.json()
    assert summary["error"] == "" and summary["digest"], summary
    body = {"answers": answers, "digest": summary["digest"]}
    first = svc.call("POST", f"/api/submissions/{sid}/submit", body)
    assert first.status == 200, first.body
    run_id = first.json()["run"]
    again = svc.call("POST", f"/api/submissions/{sid}/submit", body)
    assert again.json()["run"] == run_id
    pump(svc.watcher, lambda: [r.status for r in load_all(layout(svc.root))] == ["running"])
    activity = svc.call("GET", f"/api/runs/{run_id}")
    assert activity.status == 200
    seen = activity.json()
    assert (seen["id"], seen["status"], seen["pathway"]) == (run_id, "running", PATHWAY)
    assert seen["issuer_name"] == "Acme Corp"
    assert {"reason", "started_at", "ended_at", "report", "modules"} <= set(seen)
    assert "digest" not in seen and "submitted_by" not in seen
    assert svc.call("GET", "/api/runs/20200101-000000-01").status == 404
    after = svc.upload(sid, "late.txt", b"x")
    assert after.status == 404  # submitted: its folder is now the run's, uploads find nothing


def test_a_post_without_or_with_a_foreign_origin_changes_nothing(svc):
    for origin in (None, "http://evil.example", f"https://{svc.host}", f"http://{svc.host}/"):
        made = svc.call("POST", "/api/submissions", origin=origin)
        assert made.status == 403, origin
    assert not list(layout(svc.root).uploads.iterdir())
    sid = svc.new()
    kept = svc.call("POST", f"/api/submissions/{sid}/files?name=a.txt", b"abc", origin=None)
    assert kept.status == 403
    assert not any(submissions.files_folder(layout(svc.root), sid).iterdir())
    assert (
        svc.call("DELETE", f"/api/submissions/{sid}/files?name=a.txt", origin="null").status == 403
    )


def test_a_request_for_another_host_name_is_refused(svc):
    assert svc.call("GET", "/", headers={"Host": "evil.example"}).status == 403
    assert svc.call("GET", "/", headers={"Host": "evil.example:1"}).status == 403
    port = svc.host.rsplit(":", 1)[1]
    assert (
        svc.call("GET", "/", headers={"Host": f"localhost:{port}"}).status == 200
    )  # loopback alias
    made = svc.call(
        "POST", "/api/submissions", headers={"Host": "evil.example"}, origin="http://evil.example"
    )
    assert made.status == 403
    assert not list(layout(svc.root).uploads.iterdir())


def test_a_service_started_on_another_name_has_no_loopback_alias(service_factory):
    other = service_factory("localhost")
    port = other.server.server_address[1]
    assert other.call("GET", "/", headers={"Host": f"localhost:{port}"}).status == 200
    assert other.call("GET", "/", headers={"Host": f"127.0.0.1:{port}"}).status == 403


def _raw(svc: Service, request: bytes) -> bytes:
    with socket.create_connection(("127.0.0.1", svc.server.server_address[1]), timeout=10) as s:
        s.sendall(request)
        received = b""
        while chunk := s.recv(4096):
            received += chunk
    return received


def test_a_body_without_content_length_is_refused(svc):
    head = (
        f"POST /api/submissions HTTP/1.1\r\nHost: {svc.host}\r\nOrigin: http://{svc.host}\r\n"
        "Transfer-Encoding: chunked\r\n\r\n0\r\n\r\n"
    )
    assert _raw(svc, head.encode()).startswith(b"HTTP/1.0 411")
    sid = svc.new()
    upload = (
        f"POST /api/submissions/{sid}/files?name=a.txt HTTP/1.1\r\nHost: {svc.host}\r\n"
        f"Origin: http://{svc.host}\r\n\r\n"
    )
    assert _raw(svc, upload.encode()).startswith(b"HTTP/1.0 411")
    summary = (
        f"POST /api/submissions/{sid}/summary HTTP/1.1\r\nHost: {svc.host}\r\n"
        f"Origin: http://{svc.host}\r\n\r\n"
    )
    assert _raw(svc, summary.encode()).startswith(b"HTTP/1.0 411")


def test_json_bodies_are_capped_and_must_be_json(svc):
    sid = svc.new()
    path = f"/api/submissions/{sid}/summary"
    head = (
        f"POST {path} HTTP/1.1\r\nHost: {svc.host}\r\nOrigin: http://{svc.host}\r\n"
        f"Content-Length: {1024 * 1024 + 1}\r\n\r\n"
    )
    assert _raw(svc, head.encode()).startswith(b"HTTP/1.0 413")  # judged before any body byte
    assert svc.call("POST", path, b"x" * 1024 * 1024).status == 400  # at the cap: read, not JSON
    assert svc.call("POST", path, b"{not json").status == 400
    assert svc.call("POST", path, b"[" * 200_000).status == 400  # nesting past the parser's depth
    assert svc.call("POST", path, b"\xff\xfe").status == 400
    assert svc.call("POST", path, b'["not an object"]').status == 200  # a refusal text in the body
    refusal = svc.call("POST", path, b'["not an object"]').json()
    assert refusal["error"] and "digest" not in refusal


@pytest.mark.parametrize("path", ["/library/../state/x", "/library/%2e%2e/logs/watcher.log"])
def test_the_library_route_serves_nothing_outside_the_library(svc, path):
    (layout(svc.root).state / "x").write_text("secret", encoding="utf-8")
    log = layout(svc.root).logs / "watcher.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("secret", encoding="utf-8")
    reply = svc.call("GET", path)
    assert reply.status == 404
    assert b"secret" not in reply.body


def test_the_library_route_does_not_follow_a_link_out_and_serves_its_own_files(svc):
    library = layout(svc.root).engine / "library"
    library.mkdir(parents=True, exist_ok=True)
    (library / "index.html").write_text("<p>hi</p>", encoding="utf-8")
    (library / "data.js").write_text("window.x=1;", encoding="utf-8")
    (library / "out").symlink_to(layout(svc.root).state)
    (layout(svc.root).state / "inner.txt").write_text("secret", encoding="utf-8")
    ok = svc.call("GET", "/library/index.html")
    assert ok.status == 200 and ok.body == b"<p>hi</p>"
    assert ok.headers["X-Content-Type-Options"] == "nosniff"
    assert ok.headers["Content-Type"].startswith("text/html")
    script = svc.call("GET", "/library/data.js")
    assert "javascript" in script.headers["Content-Type"]
    assert svc.call("GET", "/library/out/inner.txt").status == 404
    assert svc.call("GET", "/library/%00").status == 404
    assert svc.call("GET", "/library/%ff").status == 404
    assert svc.call("GET", "/library//etc/hosts").status == 404
    assert svc.call("GET", "/library/missing.html").status == 404


def test_an_over_limit_upload_is_refused_while_receiving(svc, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_FILE", 10)
    sid = svc.new()
    refused = svc.upload(sid, "big.txt", b"x" * 11)
    assert refused.status == 400
    assert "at most" in refused.json()["error"]
    assert not any(submissions.files_folder(layout(svc.root), sid).iterdir())
    # the length is judged from the header before any body byte: a huge claim with no body
    head = (
        f"POST /api/submissions/{sid}/files?name=a.txt HTTP/1.1\r\nHost: {svc.host}\r\n"
        f"Origin: http://{svc.host}\r\nContent-Length: 99999999999\r\n\r\n"
    )
    assert _raw(svc, head.encode()).startswith(b"HTTP/1.0 400")
    assert svc.upload(sid, "ok.txt", b"x" * 10).status == 200


def test_upload_names_are_decoded_strictly_and_refused_when_unsafe(svc):
    sid = svc.new()
    bad = svc.call("POST", f"/api/submissions/{sid}/files?name=%ff", b"x")
    assert bad.status == 400
    assert svc.call("POST", f"/api/submissions/{sid}/files", b"x").status == 400
    assert svc.upload(sid, "../x.txt", b"x").status == 400
    assert svc.upload(sid, "context.json", b"x").status == 400
    assert svc.upload(sid, "é a.txt", b"x").json()["name"].endswith("a.txt")
    removed = svc.call("DELETE", f"/api/submissions/{sid}/files?name=missing.txt")
    assert removed.status == 400
    names = svc.call("GET", f"/api/submissions/{sid}/reading").json()
    assert names["error"] == ""
    stored = next(submissions.files_folder(layout(svc.root), sid).iterdir()).name
    assert (
        svc.call(
            "DELETE", f"/api/submissions/{sid}/files?name={urllib.parse.quote(stored, safe='')}"
        ).status
        == 200
    )
    assert not any(submissions.files_folder(layout(svc.root), sid).iterdir())


def test_an_unknown_submission_is_404_and_a_wrong_route_is_404(svc):
    unknown = "0" * 32
    assert svc.call("GET", f"/api/submissions/{unknown}/reading").status == 404
    assert svc.call("POST", f"/api/submissions/{unknown}/summary", answers_for()).status == 404
    assert svc.upload(unknown, "a.txt", b"x").status == 404
    submit = {"answers": answers_for(), "digest": "a" * 64}
    assert svc.call("POST", f"/api/submissions/{unknown}/submit", submit).status == 404
    assert svc.call("GET", "/api/nothing").status == 404
    assert svc.call("GET", "/api/submissions/not-an-id/reading").status == 404
    assert svc.call("PUT", "/api/submissions", b"{}").status in (404, 405, 501)


def test_submit_with_a_stale_digest_is_refused(svc):
    sid = svc.new()
    svc.upload(sid, "a.txt", b"Net sales were 100.")
    answers = answers_for()
    digest = svc.call("POST", f"/api/submissions/{sid}/summary", answers).json()["digest"]
    svc.upload(sid, "b.txt", b"another document")  # changes after the summary
    stale = svc.call(
        "POST", f"/api/submissions/{sid}/submit", {"answers": answers, "digest": digest}
    )
    assert stale.status == 400
    assert "changed after approval" in stale.json()["error"]
    assert not load_all(layout(svc.root))
    missing = svc.call("POST", f"/api/submissions/{sid}/submit", {"answers": answers})
    assert missing.status == 400
    guessed = svc.call("POST", f"/api/submissions/{sid}/submit", {"answers": answers, "digest": 7})
    assert guessed.status == 400
    assert not load_all(layout(svc.root))


def test_no_response_carries_the_provider_key(svc, monkeypatch):
    monkeypatch.setenv(KEY, MARKER)
    sid = svc.new()
    svc.upload(sid, "a.txt", b"Net sales were 100.")
    answers = answers_for()
    replies = [
        svc.call("GET", "/"),
        svc.call("GET", f"/api/submissions/{sid}/reading"),
        svc.call("POST", f"/api/submissions/{sid}/summary", answers),
        svc.call("POST", "/api/submissions", origin="http://evil.example"),
        svc.call("GET", "/api/runs/none"),
        svc.call("GET", "/api/runs/none/inputs"),
        svc.call("GET", "/api/issuers/acme"),
        svc.call("POST", f"/api/submissions/{sid}/carry", {"run": "none"}),
        svc.call("GET", "/library/../x"),
        svc.call("POST", f"/api/submissions/{sid}/submit", {"answers": answers, "digest": "x"}),
    ]
    for reply in replies:
        assert MARKER.encode() not in reply.body
        assert MARKER not in str(reply.headers)


def test_an_unexpected_error_is_a_fixed_500_that_is_logged(svc, monkeypatch, caplog):
    def boom(*_args: Any, **_kwargs: Any) -> str:
        raise RuntimeError(f"secret {MARKER}")

    monkeypatch.setattr(submissions, "new", boom)
    monkeypatch.setenv(KEY, MARKER)
    with caplog.at_level("ERROR", logger=service.log.name):
        reply = svc.call("POST", "/api/submissions")
    assert reply.status == 500
    assert MARKER.encode() not in reply.body and b"RuntimeError" not in reply.body
    assert reply.json() == {"error": "the service failed; see its log"}
    assert any(r.exc_info for r in caplog.records)


def test_the_page_is_served_with_a_same_origin_policy(svc):
    page = svc.call("GET", "/")
    policy = page.headers["Content-Security-Policy"]
    assert "default-src 'none'" in policy
    assert "script-src 'self' 'unsafe-inline'" in policy
    assert "connect-src 'self'" in policy
    assert "https:" not in policy and "http:" not in policy
    assert page.headers["X-Content-Type-Options"] == "nosniff"
    assert (
        svc.call("GET", "/api/runs/x").headers["Content-Type"] == "application/json; charset=utf-8"
    )


def test_a_stalled_connection_times_out(service_factory, monkeypatch):
    monkeypatch.setattr(service.Handler, "timeout", 0.3)
    stalled = service_factory()
    port = stalled.server.server_address[1]
    with socket.create_connection(("127.0.0.1", port), timeout=10) as idle:
        started = time.monotonic()
        assert idle.recv(10) == b""  # the server closed it; the client sent nothing
        assert time.monotonic() - started < 5
    assert service.SOCKET_TIMEOUT == 60 and service.Handler.timeout == 0.3


def _library(svc: Service) -> Path:
    library = layout(svc.root).engine / "library"
    library.mkdir(parents=True, exist_ok=True)
    return library


def test_a_linked_index_html_is_not_served_from_outside_the_library(svc):
    library = _library(svc)
    (layout(svc.root).state / "inner.txt").write_text("secret", encoding="utf-8")
    (library / "d").mkdir()
    (library / "d" / "index.html").symlink_to(layout(svc.root).state / "inner.txt")
    for path in ("/library/d/", "/library/d", "/library/d/index.html"):
        reply = svc.call("GET", path)
        assert reply.status == 404 and b"secret" not in reply.body, path
    (library / "e").mkdir()
    (library / "e" / "index.html").write_text("<p>e</p>", encoding="utf-8")
    assert svc.call("GET", "/library/e/").body == b"<p>e</p>"


def test_a_foreign_site_cannot_read_a_library_file(svc):
    library = _library(svc)
    (library / "data.js").write_text("window.x=1;", encoding="utf-8")
    for site in ("cross-site", "same-site", "bogus"):
        got = svc.call("GET", "/library/data.js", headers={"Sec-Fetch-Site": site})
        assert got.status == 403 and b"window" not in got.body, site
    for site in ("same-origin", "none"):
        assert svc.call("GET", "/library/data.js", headers={"Sec-Fetch-Site": site}).status == 200
    foreign = svc.call("GET", "/library/data.js", headers={"Origin": "http://evil.example"})
    assert foreign.status == 403
    own = svc.call("GET", "/library/data.js", headers={"Origin": f"http://{svc.host}"})
    assert own.status == 200
    assert svc.call("GET", "/library/data.js").status == 200  # no header: not a browser
    page = svc.call("GET", "/", headers={"Sec-Fetch-Site": "cross-site"})
    assert page.status == 403
    blocked = svc.call("POST", "/api/submissions", headers={"Sec-Fetch-Site": "cross-site"})
    assert blocked.status == 403 and not list(layout(svc.root).uploads.iterdir())


def test_every_response_carries_a_same_origin_resource_policy(svc):
    _library(svc)
    (_library(svc) / "a.html").write_text("<p>a</p>", encoding="utf-8")
    replies = [
        svc.call("GET", "/"),
        svc.call("GET", "/library/a.html"),
        svc.call("GET", "/library/missing"),
        svc.call("GET", "/api/runs/none"),
        svc.call("POST", "/api/submissions"),
        svc.call("GET", "/", headers={"Host": "evil.example"}),
        svc.call("GET", "/", headers={"Sec-Fetch-Site": "cross-site"}),
    ]
    assert [r.headers["Cross-Origin-Resource-Policy"] for r in replies] == ["same-origin"] * 7


def test_the_start_page_cannot_be_framed_and_a_library_page_cannot_call_the_api(svc):
    _library(svc)
    (_library(svc) / "a.html").write_text("<p>a</p>", encoding="utf-8")
    page = svc.call("GET", "/")
    assert "frame-ancestors 'none'" in page.headers["Content-Security-Policy"]
    assert page.headers["X-Frame-Options"] == "DENY"
    shown = svc.call("GET", "/library/a.html")
    assert shown.headers["Content-Security-Policy"] == (
        "connect-src 'none'; form-action 'none'; frame-ancestors 'self'"
    )
    assert shown.headers["X-Frame-Options"] == "SAMEORIGIN"


def test_connections_beyond_the_ceiling_are_closed_at_once(service_factory, monkeypatch):
    monkeypatch.setattr(service, "MAX_CONNECTIONS", 2)
    held = service_factory()
    port = held.server.server_address[1]
    idle = [socket.create_connection(("127.0.0.1", port), timeout=10) for _ in range(2)]
    try:
        deadline = time.monotonic() + 5
        while cast(service._Server, held.server).active_connections < 2:
            assert time.monotonic() < deadline
            time.sleep(0.01)
        with socket.create_connection(("127.0.0.1", port), timeout=5) as extra:
            assert extra.recv(10) == b""  # closed with no handler thread and no reply
        idle.pop().close()  # a freed slot is usable again
        deadline = time.monotonic() + 5
        while held.call("GET", "/api/runs/none").status != 404:
            assert time.monotonic() < deadline
            time.sleep(0.05)
    finally:
        for sock in idle:
            sock.close()


def test_a_request_target_that_is_not_a_path_is_refused(svc):
    for target in (
        f"http://{svc.host}/api/submissions",
        "http://evil.example/api/submissions",
        "*",
    ):
        head = f"POST {target} HTTP/1.1\r\nHost: {svc.host}\r\nOrigin: http://{svc.host}\r\n"
        got = _raw(svc, (head + "Content-Length: 0\r\n\r\n").encode())
        assert got.startswith(b"HTTP/1.0 400"), target
    assert not list(layout(svc.root).uploads.iterdir())


def test_the_activity_file_is_served_under_the_library_rules(svc):
    engine = layout(svc.root).engine
    (engine / "activity.js").write_text("window.A=1;", encoding="utf-8")
    got = svc.call("GET", "/activity.js")
    assert got.status == 200 and got.body == b"window.A=1;"
    assert "javascript" in got.headers["Content-Type"]
    assert got.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert got.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert svc.call("GET", "/activity.js", headers={"Sec-Fetch-Site": "cross-site"}).status == 403
    (engine / "activity.js").unlink()
    secret = layout(svc.root).state / "inner.txt"
    secret.write_text("secret", encoding="utf-8")
    (engine / "activity.js").symlink_to(secret)
    assert svc.call("GET", "/activity.js").status == 404


def test_the_loop_leaves_the_sweep_to_the_watcher(root, monkeypatch):
    watcher = Scheduler(settings(root))
    calls: list[Any] = []
    real = submissions.sweep

    def counted(*args: Any, **kwargs: Any) -> Any:
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(submissions, "sweep", counted)

    def stop(_seconds: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(service.time, "sleep", stop)
    try:
        with pytest.raises(KeyboardInterrupt):
            service._loop(watcher)
    finally:
        watcher.close()
    assert len(calls) == 1  # step() sweeps once; the loop adds none


def test_the_scheduler_sweep_removes_a_stale_upload_and_keeps_a_queued_one(root, monkeypatch):
    """A queued run's files are still under ``uploads`` only while its move to the run folder is
    unfinished (a failed rename); that folder is kept however old it is."""
    scheduler = Scheduler(settings(root, max_running=0))  # nothing starts: the run stays queued
    real_rename = os.rename

    def refuse_the_move(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
        if Path(dst).parent == layout(root).drops:
            raise PermissionError(13, "held open", str(dst))
        real_rename(src, dst, *args, **kwargs)

    try:
        stale = submissions.new(layout(root))
        old = layout(root).uploads / stale
        monkeypatch.setattr(os, "rename", refuse_the_move)
        with pytest.raises(PermissionError):
            submit_run(scheduler, root)
        (record,) = load_all(layout(root))
        held = layout(root).uploads / record.submission
        assert record.status == "queued" and held.exists()
        past = time.time() - submissions.STALE_SECONDS - 100
        os.utime(old, (past, past))
        os.utime(held, (past, past))
        scheduler.step()
        assert not old.exists()
        assert held.exists() and load_all(layout(root))[0].status == "queued"
    finally:
        monkeypatch.undo()
        scheduler.close()


def test_a_library_file_swapped_for_a_link_after_the_check_is_not_served(svc, monkeypatch):
    """Ported from probe t5r1_library_race.py (it imports the removed Watcher): the swap is made
    deterministic at the moment the route has resolved the path and before it reads it."""
    library = _library(svc)
    secret = layout(svc.root).state / "secret.txt"
    secret.write_text("SECRET-OUTSIDE-LIBRARY", encoding="utf-8")
    target = library / "r.txt"
    target.write_text("plain", encoding="utf-8")
    real_resolve = Path.resolve
    seen: list[Path] = []

    def resolving(self: Path, strict: bool = False) -> Path:
        got = real_resolve(self, strict=strict)
        if got == real_resolve(target) and self == target:
            seen.append(self)
            if len(seen) == 2:  # the check has its answer: now the swap
                target.unlink()
                target.symlink_to(secret)
        return got

    monkeypatch.setattr(Path, "resolve", resolving)
    got = svc.call("GET", "/library/r.txt")
    monkeypatch.undo()
    assert len(seen) == 2 and target.is_symlink()
    assert b"SECRET" not in got.body and got.status == 404


def test_the_library_serves_a_plain_file_and_not_a_link_or_a_folder(svc):
    library = _library(svc)
    (library / "real.html").write_text("<p>real</p>", encoding="utf-8")
    (library / "alias.html").symlink_to(library / "real.html")
    assert svc.call("GET", "/library/real.html").body == b"<p>real</p>"
    assert service._read_regular(library) is None
    assert service._read_regular(library / "missing") is None


def test_every_reply_the_http_server_writes_itself_carries_the_policy_headers(svc):
    """Ported from probe t5r1_corp_every_response.py."""
    host = svc.host
    cases = {
        "HEAD": f"HEAD / HTTP/1.1\r\nHost: {host}\r\n\r\n",
        "OPTIONS": f"OPTIONS / HTTP/1.1\r\nHost: {host}\r\n\r\n",
        "PUT": f"PUT / HTTP/1.1\r\nHost: {host}\r\nContent-Length: 0\r\n\r\n",
        "bad version": f"GET / HTTP/9.x\r\nHost: {host}\r\n\r\n",
        "long request line": "GET /" + "a" * 70000 + f" HTTP/1.1\r\nHost: {host}\r\n\r\n",
    }
    for label, request in cases.items():
        head = _raw(svc, request.encode()).split(b"\r\n\r\n", 1)[0].lower()
        assert b"cross-origin-resource-policy: same-origin" in head, label
        assert b"x-content-type-options: nosniff" in head, label
        assert head.count(b"x-content-type-options") == 1, label


@pytest.mark.parametrize(
    "host", ["0.0.0.0", "0", "00", "0.0", "0.0.0", "0x0", "000.000.000.000", "::", "::ffff:0.0.0.0"]
)
def test_no_spelling_of_a_wildcard_address_starts_the_service(root, capsys, host):
    """Ported from probe t5r1_wildcard_spellings.py."""
    assert service.main(["--root", str(root), "--port", "0", "--host", host]) == 2
    assert "pass this machine's own address" in capsys.readouterr().err


def test_a_failed_thread_start_gives_its_connection_slot_back(service_factory, monkeypatch):
    """Ported from probe t5r1_thread_start_leak.py."""
    held = service_factory()
    port = held.server.server_address[1]
    real_start = threading.Thread.start
    budget = [3]

    def start(self: threading.Thread) -> None:
        if getattr(self, "_target", None).__name__ == "process_request_thread" and budget[0] > 0:  # type: ignore[union-attr]
            budget[0] -= 1
            raise RuntimeError("can't start new thread")
        real_start(self)

    monkeypatch.setattr(threading.Thread, "start", start)
    for _ in range(3):
        with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
            client.recv(10)
    monkeypatch.undo()
    deadline = time.monotonic() + 5
    while cast(service._Server, held.server).active_connections:
        assert time.monotonic() < deadline, "a slot leaked"
        time.sleep(0.01)
    assert held.call("GET", "/api/runs/none").status == 404


def test_a_client_that_resets_the_connection_mid_upload_is_not_a_500(svc, caplog):
    sid = svc.new()
    port = svc.server.server_address[1]
    with caplog.at_level(logging.INFO, logger=service.__name__):
        client = socket.create_connection(("127.0.0.1", port), timeout=10)
        client.sendall(
            (
                f"POST /api/submissions/{sid}/files?name=a.txt HTTP/1.1\r\nHost: {svc.host}\r\n"
                f"Origin: http://{svc.host}\r\nContent-Length: 1000\r\n\r\nabc"
            ).encode()
        )
        client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        client.close()  # a reset, not a close
        deadline = time.monotonic() + 5
        while "connection lost" not in caplog.text and "short" not in caplog.text:
            assert time.monotonic() < deadline, caplog.text
            time.sleep(0.02)
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR], caplog.text
    assert svc.call("GET", "/api/runs/none").status == 404  # the service goes on


def test_a_top_level_navigation_is_served_even_when_cross_site(svc):
    navigate = {"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document"}
    for site in ("cross-site", "same-site"):
        got = svc.call("GET", "/", headers={"Sec-Fetch-Site": site, **navigate})
        assert got.status == 200, site
        assert got.headers["X-Frame-Options"] == "DENY"
    # every other cross-site request stays refused
    _library(svc)
    (_library(svc) / "a.html").write_text("<p>a</p>", encoding="utf-8")
    cross = {"Sec-Fetch-Site": "cross-site"}
    refused = [
        {**cross, "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "iframe"},  # framing
        {**cross, "Sec-Fetch-Mode": "navigate"},
        {**cross, "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "document"},
        {**cross, "Sec-Fetch-Mode": "no-cors", "Sec-Fetch-Dest": "script"},
        {**cross, "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "document", "Origin": "http://e"},
    ]
    for headers in refused:
        assert svc.call("GET", "/", headers=headers).status == 403, headers
        assert svc.call("GET", "/library/a.html", headers=headers).status in (403,), headers
    post = svc.call("POST", "/api/submissions", headers={**cross, **navigate})
    assert post.status == 403 and not list(layout(svc.root).uploads.iterdir())


def test_on_port_80_host_and_origin_may_leave_the_port_out(svc):
    server = cast(service._Server, svc.server)
    server.allowed_hosts, server.advertised_port = service._hosts("127.0.0.1", 80), 80
    assert svc.call("GET", "/", headers={"Host": "127.0.0.1"}).status == 200
    assert svc.call("GET", "/", headers={"Host": "localhost"}).status == 200
    assert svc.call("GET", "/", headers={"Host": "127.0.0.1:80"}).status == 200
    bare = svc.call(
        "POST", "/api/submissions", headers={"Host": "127.0.0.1"}, origin="http://127.0.0.1"
    )
    assert bare.status == 200
    with_port = svc.call(
        "POST", "/api/submissions", headers={"Host": "127.0.0.1:80"}, origin="http://127.0.0.1"
    )
    assert with_port.status == 200
    for host in ("evil.example", "127.0.0.1:81"):
        assert svc.call("GET", "/", headers={"Host": host}).status == 403
    foreign = svc.call(
        "POST", "/api/submissions", headers={"Host": "127.0.0.1"}, origin="http://evil"
    )
    assert foreign.status == 403


def test_off_port_80_a_host_without_a_port_is_still_refused(svc):
    assert svc.call("GET", "/", headers={"Host": "127.0.0.1"}).status == 403


def test_a_wildcard_address_is_refused_at_start_up(root, capsys):
    for host in ("0.0.0.0", "::"):
        assert service.main(["--root", str(root), "--port", "0", "--host", host]) == 2
        assert "pass this machine's own address, not 0.0.0.0" in capsys.readouterr().err


def test_start_up_refuses_without_the_key_or_with_a_second_instance(root, monkeypatch, capsys):
    argv = ["--root", str(root), "--port", "0"]
    monkeypatch.delenv(KEY)
    assert service.main(argv) == 2
    assert KEY in capsys.readouterr().err
    monkeypatch.setenv(KEY, "test-key-not-real")
    first = Scheduler(settings(root))
    try:
        assert service.main(argv) == 2
        assert "another run page service" in capsys.readouterr().err
    finally:
        first.close()
    assert service.main([*argv, "--max-running", "0"]) == 2
    assert service.main([*argv, "--port", "70000"]) == 2


def test_start_up_refuses_a_root_path_that_is_too_long(root, capsys):
    long_root = root / ("d" * 90)
    long_root.mkdir()
    assert service.main(["--root", str(long_root), "--port", "0"]) == 2
    assert "use a shorter path" in capsys.readouterr().err


@pytest.mark.parametrize(
    "error", [TimeoutError("share"), OSError(errno.ETIMEDOUT, "network share")]
)
def test_a_timeout_met_by_the_service_is_a_500_not_a_client_leaving(
    svc, monkeypatch, caplog, error
):
    """A share timeout during a route, not while reading the body, is the service's failure."""
    sid = svc.new()

    def timed_out(*_args: Any, **_kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(submissions, "summary", timed_out)
    with caplog.at_level(logging.INFO, logger=service.__name__):
        reply = svc.call("POST", f"/api/submissions/{sid}/summary", answers_for())
    assert reply.status == 500 and reply.json() == {"error": "the service failed; see its log"}
    assert any(r.levelno >= logging.ERROR and r.exc_info for r in caplog.records), caplog.text
    assert "connection lost" not in caplog.text


def test_a_fifo_at_a_library_path_is_refused_without_waiting(tmp_path):
    fifo = tmp_path / "data.js"
    os.mkfifo(fifo)
    seen: list[object] = []
    reader = threading.Thread(target=lambda: seen.append(service._read_regular(fifo)), daemon=True)
    reader.start()
    reader.join(5)
    assert not reader.is_alive(), "reading a FIFO blocked the handler"
    assert seen == [None]


def test_a_library_file_is_opened_in_binary_mode_where_the_platform_has_the_flag(
    tmp_path, monkeypatch
):
    """Windows corrupts a file opened without O_BINARY; the project's own opener adds it."""
    from deploy_workflow import platform_io

    asked: list[tuple[str, ...]] = []
    real = platform_io.flags

    def spy(*names: str) -> int:
        asked.append(names)
        return real(*names)

    monkeypatch.setattr(platform_io, "flags", spy)
    target = tmp_path / "a.bin"
    target.write_bytes(b"\x1a\r\n\x00x")
    assert service._read_regular(target) == b"\x1a\r\n\x00x"
    assert ("O_BINARY",) in asked
    link = tmp_path / "link.bin"
    link.symlink_to(target)
    assert service._read_regular(link) is None  # the link refusal is kept


def test_main_stops_on_interrupt_and_releases_the_folder_lock(root, fake_env, monkeypatch):
    """What the deleted ``Scheduler.run_forever`` test pinned, now at the loop's owner."""
    from deploy_workflow.inbox import scheduler as scheduler_module

    fake_env({"sleep": 30})

    def interrupt(_scheduler: Any) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(service, "_loop", interrupt)
    assert service.main(["--root", str(root), "--port", "0", "--host", "127.0.0.1"]) == 0
    scheduler_module.Scheduler(settings(root)).close()  # the lock was released


def _finished_run(svc: Service, fake_env: Callable[[dict[str, Any]], None], payload: bytes) -> str:
    fake_env({"events": [["delivered", {}]]})
    sid = svc.new()
    assert svc.upload(sid, "notes/a.txt", payload).status == 200
    answers = answers_for()
    summary = svc.call("POST", f"/api/submissions/{sid}/summary", answers).json()
    body = {"answers": answers, "digest": summary["digest"]}
    run_id = str(svc.call("POST", f"/api/submissions/{sid}/submit", body).json()["run"])
    lay = layout(svc.root)
    pump(
        svc.watcher,
        lambda: (
            [r.status for r in load_all(lay) if r.id == run_id] == ["finished"]
            and (lay.drops / run_id / "context.json").is_file()
        ),
        limit=60,
    )
    return run_id


def test_an_earlier_runs_inputs_are_read_and_its_files_carried(svc, fake_env):
    run = _finished_run(svc, fake_env, b"Net sales were 100.")
    got = svc.call("GET", f"/api/runs/{run}/inputs")
    assert got.status == 200 and got.json()["context"]["run"]["as_of"] == ""
    sid = svc.new()
    carried = svc.call("POST", f"/api/submissions/{sid}/carry", {"run": run})
    assert carried.status == 200 and carried.json()["kept"] == []
    reading = svc.call("GET", f"/api/submissions/{sid}/reading").json()
    assert reading["error"] == "" and reading["documents"], reading
    assert [f["name"] for f in got.json()["files"]] == ["notes/a.txt"]
    assert carried.json()["carried"] == ["notes/a.txt"]
    assert [d["source"] for d in reading["documents"]] == [f["name"] for f in got.json()["files"]]


def test_inputs_and_carry_for_an_unknown_run_are_404(svc):
    unknown = "20200101-000000-01"
    assert svc.call("GET", f"/api/runs/{unknown}/inputs").status == 404
    sid = svc.new()
    reply = svc.call("POST", f"/api/submissions/{sid}/carry", {"run": unknown})
    assert reply.status == 404 and reply.json() == {"error": "unknown run"}
    assert not any(submissions.files_folder(layout(svc.root), sid).iterdir())
    known = svc.call("POST", "/api/submissions/" + "0" * 32 + "/carry", {"run": unknown})
    assert known.status == 404


def test_a_carry_for_an_unknown_submission_is_404(svc, fake_env):
    run = _finished_run(svc, fake_env, b"Net sales were 100.")
    reply = svc.call("POST", "/api/submissions/" + "0" * 32 + "/carry", {"run": run})
    assert reply.status == 404 and reply.json() == {"error": "unknown submission"}


def test_a_carry_without_or_with_a_foreign_origin_copies_nothing(svc, fake_env):
    run = _finished_run(svc, fake_env, b"Net sales were 100.")
    sid = svc.new()
    for origin in (None, "http://evil.example", f"https://{svc.host}", "null"):
        reply = svc.call("POST", f"/api/submissions/{sid}/carry", {"run": run}, origin=origin)
        assert reply.status == 403, origin
    assert not any(submissions.files_folder(layout(svc.root), sid).iterdir())


@pytest.mark.parametrize("body", [{"run": "../x"}, {"run": 3}, [], {}, {"run": ""}, {"run": "a/b"}])
def test_a_carry_body_that_is_not_a_run_id_is_400(svc, body):
    sid = svc.new()
    reply = svc.call("POST", f"/api/submissions/{sid}/carry", json.dumps(body).encode())
    assert reply.status == 400, reply.body
    assert not any(submissions.files_folder(layout(svc.root), sid).iterdir())


def test_a_carry_from_a_run_without_stored_documents_is_400(svc, fake_env):
    run = _finished_run(svc, fake_env, b"Net sales were 100.")
    shutil.rmtree(layout(svc.root).drops / run)
    sid = svc.new()
    reply = svc.call("POST", f"/api/submissions/{sid}/carry", {"run": run})
    assert reply.status == 400
    assert reply.json() == {"error": "that run has no stored documents"}


def test_an_issuer_id_is_looked_up_and_an_unsafe_one_is_404(svc, fake_env):
    _finished_run(svc, fake_env, b"Net sales were 100.")
    assert svc.call("GET", "/api/issuers/acme").json()["runs"] == 1
    assert svc.call("GET", "/api/issuers/nobody").json()["runs"] == 0
    assert svc.call("GET", "/api/issuers/..%2Fx").status == 404
    assert svc.call("GET", "/api/issuers/Acme").status == 404
    assert svc.call("GET", "/api/issuers/" + "a" * 41).status == 404


def test_the_inputs_route_does_not_serve_file_content(svc, fake_env):
    secret = b"Net sales were 424242 and the secret phrase is plover."
    run = _finished_run(svc, fake_env, secret)
    reply = svc.call("GET", f"/api/runs/{run}/inputs")
    assert reply.status == 200
    assert b"plover" not in reply.body and b"424242" not in reply.body
    assert reply.json()["files"] == [{"name": "notes/a.txt", "size": len(secret)}]


RAIL_MARKER = b"<!--rail-signal-->"
FORM_PAGE = Path(__file__).resolve().parents[1] / "docs/templates/context-form.html"


def test_without_a_signal_url_the_page_is_the_template_without_its_marker(svc):
    template = FORM_PAGE.read_bytes()
    assert template.count(RAIL_MARKER) == 1
    page = svc.call("GET", "/").body
    assert page == template.replace(RAIL_MARKER, b"")
    assert b"rail-signal" not in page and RAIL_MARKER not in page


def test_a_signal_url_adds_one_rail_link_after_the_activity_link(root, fake_env, monkeypatch):
    fake_env({"sleep": 30})
    watcher = Scheduler(settings(root))
    server = service.make_server(watcher, "127.0.0.1", 0, signal_url="http://10.1.2.3:8766/")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        host = f"127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(f"http://{host}/", timeout=20) as response:
            page = response.read().decode()
        policy = response.headers["Content-Security-Policy"]
    finally:
        server.shutdown()
        server.server_close()
        watcher.close()
    assert page.count('id="rail-signal"') == 1
    assert page.count("http://10.1.2.3:8766/") == 1
    assert "<!--rail-signal-->" not in page
    link = page[page.index('<a id="rail-signal"') :]
    assert link.startswith('<a id="rail-signal" href="http://10.1.2.3:8766/" title="Signal">')
    assert '<path d="M5 20v-4M10 20v-8M15 20V8M20 20V4"/>' in link.split("</a>")[0]
    assert '<span class="sr-only">Signal</span></a>' in link
    assert page.index('id="rail-activity"') < page.index('id="rail-signal"')
    assert "10.1.2.3" not in policy


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "http://a/b",
        "http://u@a:1/",
        "http://u:p@a:1/",
        "https://a:1/",
        'http://a:1/"><script>',
        "http://a/",
        "http://a:0/",
        "http://a:99999/",
        "http://a:1/?x",
        "http://a:1/#x",
        "http://a:1/ ",
        "http://a b:1/",
        "http://a:1/'",
        "http://a:1/<",
        "http://é:1/",
        "HTTP://a:1/",
        "http://[::1]:1/",
        "http://[vF.example]:8766/",
        "",
    ],
)
def test_a_signal_url_that_is_not_a_plain_http_host_and_port_is_refused(root, capsys, url):
    assert service.main(["--root", str(root), "--port", "0", "--signal-url", url]) == 2
    assert "--signal-url" in capsys.readouterr().err


@pytest.mark.parametrize("raw", ["javascript:alert(1)", "data:text/html,x", "http://[::1]:1/"])
def test_make_server_refuses_a_signal_url_before_binding(raw, monkeypatch):
    opened: list[object] = []
    monkeypatch.setattr(service, "_Server", lambda *args: opened.append(args))
    with pytest.raises(ValueError, match="--signal-url"):
        service.make_server(Path("unused"), "127.0.0.1", 0, signal_url=raw)
    assert opened == []  # no socket was asked for


def test_an_accepted_signal_url_reaches_the_server_normalised_through_main(
    root, fake_env, monkeypatch
):
    fake_env({"sleep": 30})
    real, seen = service.make_server, []

    def capture(scheduler: Any, host: str, port: int, signal_url: str = "") -> Any:
        seen.append(signal_url)
        return real(scheduler, host, port, signal_url)

    def interrupt(_scheduler: Any) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(service, "make_server", capture)
    monkeypatch.setattr(service, "_loop", interrupt)
    argv = ["--root", str(root), "--port", "0", "--signal-url", "http://A:1"]
    assert service.main(argv) == 0
    assert seen == ["http://a:1/"]


@pytest.mark.parametrize(
    ("given", "stored"),
    [
        ("http://a:1", "http://a:1/"),
        ("http://Box.example:8766/", "http://box.example:8766/"),
        ("http://10.0.0.5:65535/", "http://10.0.0.5:65535/"),
    ],
)
def test_an_accepted_signal_url_is_stored_normalised(given, stored):
    assert service.signal_link(given) == stored
