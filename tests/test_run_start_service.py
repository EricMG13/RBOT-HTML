"""The start page's HTTP service, run for real on port 0 over the fake launcher: no provider.

Every request is hostile input: these tests pin the host and origin checks, the library route's
boundary, the upload limits, the approval digest and that no response carries the provider key.
"""

from __future__ import annotations

import json
import socket
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from inbox_fixtures import CONTEXT, KEY, layout, pump, settings

from deploy_workflow.inbox.runs import load_all
from deploy_workflow.inbox.watcher import Watcher
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
    watcher: Watcher
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
        host: str | None = None,
    ) -> Reply:
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        request = urllib.request.Request(f"http://{self.host}{path}", data=data, method=method)
        if origin == "":
            origin = f"http://{self.host}"
        if origin is not None and method != "GET":
            request.add_header("Origin", origin)
        if host is not None:
            request.add_header("Host", host)
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
        watcher = Watcher(settings(root))
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
    assert svc.call("GET", "/", host="evil.example").status == 403
    assert svc.call("GET", "/", host="evil.example:1").status == 403
    port = svc.host.rsplit(":", 1)[1]
    assert svc.call("GET", "/", host=f"localhost:{port}").status == 200  # loopback alias
    made = svc.call("POST", "/api/submissions", host="evil.example", origin="http://evil.example")
    assert made.status == 403
    assert not list(layout(svc.root).uploads.iterdir())


def test_a_service_started_on_another_name_has_no_loopback_alias(service_factory):
    other = service_factory("localhost")
    port = other.server.server_address[1]
    assert other.call("GET", "/", host=f"localhost:{port}").status == 200
    assert other.call("GET", "/", host=f"127.0.0.1:{port}").status == 403


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


def test_a_stalled_connection_times_out(svc):
    assert service.Handler.timeout == 60


def test_start_up_refuses_without_the_key_or_with_a_second_instance(root, monkeypatch, capsys):
    argv = ["--root", str(root), "--port", "0"]
    monkeypatch.delenv(KEY)
    assert service.main(argv) == 2
    assert KEY in capsys.readouterr().err
    monkeypatch.setenv(KEY, "test-key-not-real")
    first = Watcher(settings(root))
    try:
        assert service.main(argv) == 2
        assert "another watcher is running" in capsys.readouterr().err
    finally:
        first.close()
    assert service.main([*argv, "--max-running", "0"]) == 2
    assert service.main([*argv, "--port", "70000"]) == 2
