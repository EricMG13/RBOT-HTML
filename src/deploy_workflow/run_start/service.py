"""The start page's HTTP service: the upload store and the scheduler behind one local address.

The process holds the provider key and can start paid runs (USD 20 cap each), has no login and is
reachable from other machines, so every request is hostile input. Plain ``http.server``; no
framework. Every request is checked before any body byte is read:

* ``Host`` must be exactly ``<host>:<port>`` as started (and ``localhost:<port>`` when the host is
  ``127.0.0.1``); otherwise 403.
* A request target must be a path (it starts with ``/``): an absolute URI is 400.
* Every request other than GET must carry ``Origin: http://<Host>``; otherwise 403 and no change.
  A GET that carries ``Origin`` must carry the same value. Any request whose ``Sec-Fetch-Site`` is
  present and is not ``same-origin`` or ``none`` is 403: a page on another site cannot read the
  library through an analyst's browser. A request with neither header (not a browser) is served.
* Every response carries ``Cross-Origin-Resource-Policy: same-origin`` and ``nosniff``.
* At most ``MAX_CONNECTIONS`` connections are open; one beyond that is closed at once.
* A body needs ``Content-Length`` (else 411). JSON bodies are at most 1 MiB (else 413) and must be
  one JSON value (else 400). An upload's length is at most ``submissions.MAX_FILE`` (else 400,
  judged from the header). Every connection serves one request and closes.

Requests. JSON answers carry ``Content-Type: application/json; charset=utf-8``. A refusal is
``{"error": "<plain sentence>"}`` with 400, an unknown submission or run is 404, an unexpected
failure is 500 ``{"error": "the service failed; see its log"}`` (its cause goes to the log only).

``GET /``
    The start page (docs/templates/context-form.html) as served HTML, with a
    ``Content-Security-Policy`` that allows only same-origin scripts, styles, fonts, images and
    connections, plus the page's inline script and style (and ``data:`` images its CSS uses).
``POST /api/submissions``
    No body. 200 ``{"id": "<32 hex>"}``: a new, empty submission. 400 when too many are open.
``POST /api/submissions/<id>/files?name=<percent-encoded UTF-8 path>``
    The body is the file's raw bytes; ``Content-Length`` is required. 200 ``{"name": "<stored
    name>"}``. The name may hold ``/`` for folders. A name already stored is replaced. 400 for a
    bad or undecodable name, a missing ``name``, a limit, or a submission already submitted.
``DELETE /api/submissions/<id>/files?name=<percent-encoded UTF-8 path>``
    No body. 200 ``{"name": "<name>"}``; 400 when it is not stored or the submission is sealed.
``GET /api/submissions/<id>/reading``
    200 ``{"documents": [...], "ignored": [...], "error": ""}``: what the launcher makes of each
    uploaded file offline. ``error`` is a sentence when the files cannot be read.
``POST /api/submissions/<id>/summary``
    Body: the answers object ``{"context", "modules", "max_turns", "level", "submitted_by"}``.
    200 ``{"error": "", "digest", "modules", "items", "documents", "ignored", "omitted"}``, the
    launcher's own forecast and the digest to approve; or 200 ``{"error": "<sentence>"}`` with no
    digest when the answers or files are refused. Only the latest digest issued is accepted.
``POST /api/submissions/<id>/submit``
    Body: ``{"answers": <the answers object>, "digest": "<digest of the latest summary>"}``.
    200 ``{"run": "<run id>", "status": "queued"}``. Repeating it returns the same run. 400 when
    the digest is not the one issued for exactly the files and answers now held.
``GET /api/runs/<run id>``
    200 ``{"id", "status", "reason", "started_at", "ended_at", "issuer_name", "pathway",
    "report", "modules"}``. ``modules`` is ``[[module, "done"|"running"|"waiting"], ...]`` in
    plan order, then ``["Report", ...]``; ``stalled`` is added (true) when no event for an hour.
    ``report`` is a path under the library folder, relative to the root, once filed.
``GET /library/<path>``
    A read-only file under ``_engine/library``. The final path (``index.html`` appended for a
    folder) is resolved with links followed and must be a regular file inside the library: 404 for
    anything else, and for a path that does not decode as UTF-8. The type comes from the file name.
    The page is served with ``connect-src 'none'; form-action 'none'; frame-ancestors 'self'`` and
    ``X-Frame-Options: SAMEORIGIN``, so its own script cannot call this API.
``GET /activity.js``
    ``_engine/activity.js`` (the library's Run activity, loaded as ``../activity.js``), under the
    same rules and headers as a library file; it must itself be in ``_engine``.

``main`` runs this server in a daemon thread and the watcher's ``step`` every poll in the main
thread; ``step`` also sweeps stale uploads. ``--host`` must be this machine's own address: a
wildcard address (``0.0.0.0``, ``::``) can never equal a ``Host`` header and is refused.
"""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import re
import sys
import threading
import time
import urllib.parse
from collections.abc import Sequence
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, BinaryIO, cast

from deploy_workflow.inbox import activity, runs, startup
from deploy_workflow.inbox.drops import Layout
from deploy_workflow.inbox.watcher import Settings, Watcher
from deploy_workflow.run_start import submissions
from deploy_workflow.run_start.submissions import Answers

__all__ = ["Handler", "main", "make_server"]

log = logging.getLogger(__name__)

MAX_JSON = 1024 * 1024
SOCKET_TIMEOUT = 60  # seconds a connection may stall; a stalled upload cannot hold a thread
# Each connection holds a thread for up to SOCKET_TIMEOUT. The service is used by a few colleagues,
# so 64 is far above real use and low enough that idle sockets cannot exhaust threads or memory.
MAX_CONNECTIONS = 64
_POLICY = (
    "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
    "font-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
)
_LIBRARY_POLICY = "connect-src 'none'; form-action 'none'; frame-ancestors 'self'"
_JSON = "application/json; charset=utf-8"
_FAILED = "the service failed; see its log"
_UNKNOWN = "unknown submission"  # the text submissions raises for an id it does not hold
_SUBMISSION = re.compile(r"/api/submissions/([^/]+)/(files|reading|summary|submit)")
_RUN = re.compile(r"/api/runs/([0-9A-Za-z._-]{1,80})")
_RUN_FIELDS = (
    "id",
    "status",
    "reason",
    "started_at",
    "ended_at",
    "issuer_name",
    "pathway",
    "report",
    "modules",
    "stalled",
)
_LIBRARY = "/library/"


class _Reply(Exception):  # control flow: it carries the response, not a failure
    def __init__(self, status: int, body: Any, headers: dict[str, str] | None = None) -> None:
        super().__init__(status)
        self.status, self.body, self.headers = status, body, headers or {}


def _refuse(status: int, text: str) -> _Reply:
    return _Reply(status, {"error": text})


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    watcher: Watcher
    allowed_hosts: frozenset[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.active_connections = 0
        self._count = threading.Lock()
        super().__init__(*args, **kwargs)

    def verify_request(self, request: Any, client_address: Any) -> bool:
        with self._count:
            if self.active_connections >= MAX_CONNECTIONS:
                return False  # closed by the server loop with no handler thread
            self.active_connections += 1
        return True

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self._count:
                self.active_connections -= 1


class Handler(BaseHTTPRequestHandler):
    timeout = SOCKET_TIMEOUT
    server_version = "RunStart"
    sys_version = ""

    # -- plumbing ---------------------------------------------------------------------------

    @property
    def _service(self) -> _Server:
        return cast(_Server, self.server)

    @property
    def _layout(self) -> Layout:
        return self._service.watcher.layout

    def log_message(self, format: str, *args: Any) -> None:
        log.info("%s %s", self.address_string(), format % args)

    def do_GET(self) -> None:
        self._serve(self._get)

    def do_POST(self) -> None:
        self._serve(self._post)

    def do_DELETE(self) -> None:
        self._serve(self._delete)

    def _serve(self, route: Any) -> None:
        try:
            if not self.path.startswith("/"):
                raise _refuse(400, "the request target must be a path")
            self._check_origin()
            if self.headers.get("Transfer-Encoding") is not None:
                raise _refuse(411, "a body needs Content-Length")
            route(urllib.parse.urlsplit(self.path))
            raise _refuse(404, "not found")
        except _Reply as reply:
            self._send(reply)
        except Exception:
            # The only catch-all, documented: whatever a handler raises becomes a 500 with fixed
            # text. The traceback goes to the log; neither it, the exception text nor any
            # environment value (the provider key) reaches the client. KeyboardInterrupt and
            # SystemExit (BaseException) are not caught.
            log.exception("%s %s", self.command, self.path)
            self._send(_refuse(500, _FAILED))

    def _check_origin(self) -> None:
        hosts = self.headers.get_all("Host") or []
        if len(hosts) != 1 or hosts[0] not in self._service.allowed_hosts:
            raise _refuse(403, "this address is not the one the service was started on")
        site = self.headers.get_all("Sec-Fetch-Site")
        if site is not None and site not in (["same-origin"], ["none"]):
            raise _refuse(403, "the request came from another site")
        origins = self.headers.get_all("Origin") or []
        if (self.command != "GET" or origins) and origins != [f"http://{hosts[0]}"]:
            raise _refuse(403, "the request did not come from the service's own page")

    def _send(self, reply: _Reply) -> None:
        if isinstance(reply.body, bytes):
            data = reply.body
            headers = reply.headers
        else:
            data = json.dumps(reply.body, ensure_ascii=False).encode("utf-8")
            headers = {"Content-Type": _JSON, "Cache-Control": "no-store", **reply.headers}
        try:
            self.send_response(reply.status)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Content-Length", str(len(data)))
            for name, value in headers.items():
                self.send_header(name, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        except OSError as error:  # the peer went away or stalled: nothing more can be said to it
            log.info("%s %s: reply not delivered (%s)", self.command, self.path, error)

    def _length(self) -> int:
        """``Content-Length`` as a number; 411 when absent, 400 when it is no length."""
        values = self.headers.get_all("Content-Length") or []
        if self.headers.get("Transfer-Encoding") is not None or not values:
            raise _refuse(411, "a body needs Content-Length")
        text = values[0].strip()
        if len(values) != 1 or not (text.isascii() and text.isdigit()) or len(text) > 15:
            raise _refuse(400, "Content-Length is not a length")
        return int(text)

    def _json_body(self) -> Any:
        length = self._length()
        if length > MAX_JSON:
            raise _refuse(413, f"a request body is at most {MAX_JSON // 1024} KiB")
        data = self.rfile.read(length)
        if len(data) != length:
            raise _refuse(400, "the request body ended early")
        try:
            return json.loads(data.decode("utf-8"))
        except (ValueError, RecursionError):  # bad UTF-8, bad JSON, or nesting past the parser
            raise _refuse(400, "the request body is not valid JSON") from None

    def _name(self, query: str) -> str:
        try:
            found = urllib.parse.parse_qs(query, keep_blank_values=True, errors="strict")
        except UnicodeDecodeError:
            raise _refuse(400, "the file name is not valid UTF-8") from None
        names = found.get("name", [])
        if len(names) != 1:
            raise _refuse(400, "the request needs exactly one name")
        return names[0]

    # -- routes -----------------------------------------------------------------------------

    def _get(self, url: urllib.parse.SplitResult) -> None:
        path = url.path
        if path == "/":
            page = startup.FORM.read_bytes()
            raise _Reply(
                200,
                page,
                {
                    "Content-Type": "text/html; charset=utf-8",
                    "Content-Security-Policy": _POLICY,
                    "X-Frame-Options": "DENY",
                },
            )
        if path.startswith(_LIBRARY):
            self._file(self._layout.engine / "library", path[len(_LIBRARY) :], direct=False)
        if path == "/activity.js":
            self._file(self._layout.engine, "activity.js", direct=True)
        found = _SUBMISSION.fullmatch(path)
        if found and found[2] == "reading":
            raise _Reply(200, self._guarded(lambda: submissions.reading(self._layout, found[1])))
        run = _RUN.fullmatch(path)
        if run:
            raise _Reply(200, self._run(run[1]))

    def _post(self, url: urllib.parse.SplitResult) -> None:
        if url.path == "/api/submissions":
            raise _Reply(200, {"id": self._guarded(lambda: submissions.new(self._layout))})
        found = _SUBMISSION.fullmatch(url.path)
        if not found:
            return
        sid, action = found[1], found[2]
        if action == "files":
            self._upload(sid, self._name(url.query))
        if action == "summary":
            answers = self._json_body()
            raise _Reply(200, self._guarded(lambda: self._summary(sid, answers)))
        if action == "submit":
            self._submit(sid, self._json_body())

    def _delete(self, url: urllib.parse.SplitResult) -> None:
        found = _SUBMISSION.fullmatch(url.path)
        if found and found[2] == "files":
            name = self._name(url.query)
            self._guarded(lambda: submissions.remove_file(self._layout, found[1], name))
            raise _Reply(200, {"name": name})

    def _guarded(self, action: Any) -> Any:
        """The result of ``action``; a ``Refused`` becomes its 400 (404 for an unknown id)."""
        try:
            return action()
        except submissions.Refused as refusal:
            raise _refuse(404 if str(refusal) == _UNKNOWN else 400, str(refusal)) from None

    def _upload(self, sid: str, name: str) -> None:
        length = self._length()
        stored = self._guarded(
            lambda: submissions.add_file(
                self._layout, sid, name, cast(BinaryIO, self.rfile), length
            )
        )
        raise _Reply(200, {"name": stored})

    def _summary(self, sid: str, answers: Any) -> dict[str, Any]:
        settings = self._service.watcher.settings
        return submissions.summary(
            self._layout, sid, answers, config=settings.config, cap=settings.cap
        )

    def _submit(self, sid: str, body: Any) -> None:
        if not isinstance(body, dict) or not isinstance(body.get("digest"), str):
            raise _refuse(400, "the request needs the answers and the digest of the summary")
        record = self._guarded(
            lambda: self._service.watcher.submit(
                sid,
                cast(Answers, body.get("answers")),
                body["digest"],  # checked by submit
            )
        )
        raise _Reply(200, {"run": record.id, "status": record.status})

    def _run(self, run_id: str) -> dict[str, Any]:
        record = next((r for r in runs.load_all(self._layout) if r.id == run_id), None)
        if record is None:
            raise _refuse(404, "unknown run")
        settings = self._service.watcher.settings
        shown = activity.snapshot(self._layout, [record], cap=settings.cap, now=datetime.now(UTC))[
            "runs"
        ][0]
        # A run with no folder yet has no events: every module waits.
        shown.setdefault("modules", activity.module_states(record.pathway, []))
        return {key: shown[key] for key in _RUN_FIELDS if key in shown}

    def _file(self, base: Path, relative: str, *, direct: bool) -> None:
        """Serve a regular file inside ``base``; anything else is a 404.

        The final path is decided first (``index.html`` appended for a folder), then resolved with
        links followed, and that resolved path is what is checked and read. ``direct`` also
        requires the file to sit in ``base`` itself.
        """
        root = base.resolve()
        try:
            wanted = root / urllib.parse.unquote(relative, errors="strict").lstrip("/")
            if wanted.resolve().is_dir():
                wanted = wanted / "index.html"
            target = wanted.resolve()
            inside = target.is_relative_to(root) and target.is_file()
            inside = inside and (not direct or target.parent == root)
            data = target.read_bytes() if inside else b""
        except (UnicodeDecodeError, ValueError, OSError):  # not UTF-8, a NUL, a loop of links
            inside = False
        if not inside:
            raise _refuse(404, "not found")
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        raise _Reply(
            200,
            data,
            {
                "Content-Type": kind,
                "Content-Security-Policy": _LIBRARY_POLICY,
                "X-Frame-Options": "SAMEORIGIN",
            },
        )


def make_server(watcher: Watcher, host: str, port: int) -> ThreadingHTTPServer:
    """A server bound to ``host:port`` (port 0 picks one); not yet serving."""
    server = _Server((host, port), Handler)
    allowed = {f"{host}:{server.server_address[1]}"}
    if host == "127.0.0.1":
        allowed.add(f"localhost:{server.server_address[1]}")
    server.watcher, server.allowed_hosts = watcher, frozenset(allowed)
    return server


def _parser() -> argparse.ArgumentParser:
    defaults = Settings(Path("."))
    parser = argparse.ArgumentParser(prog="python -m deploy_workflow.run_start")
    parser.add_argument("--root", type=Path, required=True, help="the shared folder")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--max-running", type=int, default=defaults.max_running)
    parser.add_argument("--max-per-day", type=int, default=defaults.max_per_day)
    return parser


def _loop(watcher: Watcher) -> None:
    while True:
        watcher.step()  # which also sweeps the stale uploads, keeping the queued ones
        time.sleep(watcher.settings.poll_seconds)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not 0 <= args.port <= 65535:
        print("--port must be from 0 to 65535", file=sys.stderr)
        return 2
    if args.max_running < 1 or args.max_per_day < 1:
        print("--max-running and --max-per-day must be at least 1", file=sys.stderr)
        return 2
    if args.host in ("", "0.0.0.0", "::"):
        print(
            "--host: pass this machine's own address, not 0.0.0.0 (no Host header would match)",
            file=sys.stderr,
        )
        return 2
    settings = Settings(args.root, max_running=args.max_running, max_per_day=args.max_per_day)
    try:
        watcher = Watcher(settings)
    except (ValueError, OSError) as error:  # StartupRefused, a long root, an unreadable record
        print(error, file=sys.stderr)
        return 2
    try:
        server = make_server(watcher, args.host, args.port)
    except (OSError, OverflowError) as error:  # the address is taken or is not one
        watcher.close()
        print(f"cannot listen on {args.host}:{args.port}: {error}", file=sys.stderr)
        return 2
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"serving http://{args.host}:{server.server_address[1]}/", file=sys.stderr)
    try:
        _loop(watcher)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        watcher.close()
    return 0
