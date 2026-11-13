"""Signal's HTTP service: the feed API, its page files and the background ingest loop.

Plain ``http.server``; no framework. The service has no login and may be reachable from other
machines, so every request is hostile input. The rules are those of the run start page's service,
written again here. Every request is checked before any body byte is read:

* ``Host`` must be exactly ``<host>:<port>`` as started (and ``localhost:<port>`` when the host is
  ``127.0.0.1``); otherwise 403. On port 80 the port may be left out of ``Host`` and ``Origin``.
* A request target must be a path (it starts with ``/``): an absolute URI is 400.
* Every request other than GET must carry ``Origin: http://<Host>``; otherwise 403 and no change.
  A GET that carries ``Origin`` must carry the same value. Any request whose ``Sec-Fetch-Site`` is
  present and is not ``same-origin`` or ``none`` is 403, except a top-level navigation: a GET with
  ``Sec-Fetch-Mode: navigate`` and ``Sec-Fetch-Dest: document``. A request with neither header (not
  a browser) is served.
* Every response carries ``Cross-Origin-Resource-Policy: same-origin``, ``nosniff`` and the page
  policy ``Content-Security-Policy`` (same-origin scripts, styles, fonts and connections, ``data:``
  images for the brand marks, no framing, no inline script or style).
* At most ``MAX_CONNECTIONS`` connections are open, and at most ``MAX_PER_ADDRESS`` per remote
  address; one beyond either is closed at once. A connection is shut down ``2 * SOCKET_TIMEOUT``
  seconds after it opens, however it trickles. An HTTP/0.9 request line is closed without a reply.
* A JSON body needs ``Content-Length`` (else 411), is at most 64 KiB (else 413) and must be a JSON
  object (else 400). Every connection serves one request and closes.

The service serves only its own page files and API. Static names come from the fixed ``STATIC``
allowlist (URL name -> file and type); a request path is compared with those names and is never
joined to a directory, so no file under the data root is reachable.

Identity is a display name in a cookie, not authentication. Every API route except ``/api/me`` and
``/api/status`` needs a name (401 otherwise). No owner or writer action is exposed. Each request
opens its own database connection and closes it; the ingest loop has its own.

A refusal is ``{"error": "<plain sentence>"}``; an unexpected failure is 500
``{"error": "the service failed; see its log"}``, its cause in the log only.
"""

from __future__ import annotations

import dataclasses
import ipaddress
import json
import logging
import re
import socket
import sqlite3
import sys
import threading
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from deploy_workflow.signal import feedview, identity, ingest, store, topics
from deploy_workflow.signal.ingest import FetchFn

__all__ = ["STATIC", "Handler", "Loop", "StartError", "make_server", "serve"]

log = logging.getLogger(__name__)

MAX_JSON = 64 * 1024
# Seconds one socket read may wait. It is per read, so a client trickling bytes would never hit it;
# the absolute limit is the connection deadline, 2 * SOCKET_TIMEOUT from accept (Handler.setup).
SOCKET_TIMEOUT = 60
# Each connection holds a thread for up to the deadline; a few colleagues use the service.
MAX_CONNECTIONS = 64
MAX_PER_ADDRESS = 16  # one remote address may hold this many of the MAX_CONNECTIONS
MAX_PARAMS = 20
_POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; "
    "img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; "
    "frame-ancestors 'none'"
)
_JSON = "application/json; charset=utf-8"
_FAILED = "the service failed; see its log"
_NEEDS_NAME = "choose a display name first"
WILDCARD_MESSAGE = (
    "--host: pass this machine's own address, not 0.0.0.0 (no Host header would match)"
)

_WEB = Path(__file__).resolve().parent / "web"
# Located from the repository; a later task handles the packaged layout.
_BRAND = Path(__file__).resolve().parents[3] / "apps" / "issuer-library" / "credit_os" / "web"
PAGE = _WEB / "index.html"
_HTML = "text/html; charset=utf-8"
_CSS = "text/css; charset=utf-8"
_JS = "text/javascript; charset=utf-8"
_FONTS = (
    "RedHatDisplay-Bold.woff2",
    "RedHatDisplay-SemiBold.woff2",
    "RedHatMono-Medium.woff2",
    "RedHatMono-SemiBold.woff2",
    "RedHatText-Medium.woff2",
    "RedHatText-Regular.woff2",
    "RedHatText-SemiBold.woff2",
)
STATIC: dict[str, tuple[Path, str]] = {
    "signal.css": (_WEB / "signal.css", _CSS),
    "signal.js": (_WEB / "signal.js", _JS),
    "render.js": (_WEB / "render.js", _JS),
    "brand.css": (_BRAND / "brand.css", _CSS),
    "brand/symbol.svg": (_BRAND / "brand" / "symbol.svg", "image/svg+xml"),
    **{f"fonts/{name}": (_BRAND / "fonts" / name, "font/woff2") for name in _FONTS},
}


class StartError(Exception):
    """The service cannot start: a page or brand file it serves is missing."""


class _Reply(Exception):  # control flow: it carries the response, not a failure
    def __init__(self, status: int, body: Any, headers: dict[str, str] | None = None) -> None:
        super().__init__(status)
        self.status, self.body, self.headers = status, body, headers or {}


def _refuse(status: int, text: str) -> _Reply:
    return _Reply(status, {"error": text})


class Loop:
    """The background ingest loop: one pass per tick over the approved sources that are due."""

    def __init__(self, root: Path, fetch_fn: FetchFn | None = None) -> None:
        self.root = root
        self.fetch_fn = fetch_fn
        self.last_error: str | None = None

    def run_once(self, now: datetime) -> None:
        """One pass on this thread's own connection; a failing pass is logged and recorded."""
        try:
            db = store.open_db(self.root)
            try:
                ingest.run_due(db, now, self.fetch_fn)
            finally:
                db.close()
        except Exception as error:
            # The one documented fail-open of the loop: whatever a pass raises (a bug, a locked
            # store) must not end the service, so the traceback goes to the log, the failure is
            # shown by /api/status (its type only, never the cause), and the next tick tries
            # again. KeyboardInterrupt and SystemExit (BaseException) are not caught.
            log.exception("ingest pass failed")
            self.last_error = f"the last ingest pass failed ({type(error).__name__}); see the log"
        else:
            self.last_error = None

    def run_until(self, stop: threading.Event, tick: float) -> None:
        while True:
            self.run_once(datetime.now(UTC))
            if stop.wait(tick):
                return


@dataclass
class _Req:
    """What a route handler may use: its own connection, who asked, and the request's parts."""

    db: sqlite3.Connection
    user: identity.User | None
    groups: tuple[str, ...]
    params: dict[str, str]
    body: Callable[[], dict[str, Any]]
    loop: Loop | None

    @property
    def person(self) -> identity.User:
        if self.user is None:
            raise _refuse(401, _NEEDS_NAME)
        return self.user

    def param(self, name: str) -> str:
        if name not in self.params:
            raise _refuse(400, f"the request needs {name}")
        return self.params[name]


def _me(req: _Req) -> _Reply:
    if req.user is None:
        return _Reply(200, {"name": None})
    return _Reply(200, {"name": req.user.name, "role": req.user.role})


def _set_me(req: _Req) -> _Reply:
    name = req.body().get("name")
    if not isinstance(name, str):
        raise _refuse(400, "the request needs a name")
    try:
        cleaned, cookie = identity.clean_name(name), identity.cookie_for(name)
    except identity.IdentityError as error:
        raise _refuse(400, str(error)) from None
    return _Reply(
        200, {"name": cleaned, "role": store.role_of(req.db, cleaned)}, {"Set-Cookie": cookie}
    )


def _feed(req: _Req) -> _Reply:
    filters: feedview.Filters = {}
    if "kind" in req.params:
        filters["kind"] = req.params["kind"]
    if "q" in req.params:
        filters["query"] = req.params["q"]
    if "before" in req.params:
        filters["before"] = req.params["before"]
    try:
        page = feedview.feed(req.db, req.person.name, req.param("view"), **filters)
    except feedview.ViewError as error:
        raise _refuse(400, str(error)) from None
    cards = [dataclasses.asdict(card) for card in page.cards]
    return _Reply(200, {"cards": cards, "next_before": page.next_before})


def _feed_new(req: _Req) -> _Reply:
    try:
        count = feedview.new_count(req.db, req.person.name, req.param("view"), req.param("since"))
    except feedview.ViewError as error:
        raise _refuse(400, str(error)) from None
    return _Reply(200, {"count": count})


def _story(
    req: _Req, action: Callable[[sqlite3.Connection, str, int], None], saved: bool
) -> _Reply:
    try:
        action(req.db, req.person.name, int(req.groups[0]))
    except feedview.ViewError as error:
        raise _refuse(404, str(error)) from None
    return _Reply(200, {"saved": saved})


def _topic(req: _Req, action: Callable[[sqlite3.Connection, str, int], None], on: bool) -> _Reply:
    try:
        action(req.db, req.person.name, int(req.groups[0]))
    except store.StoreError as error:
        raise _refuse(404, str(error)) from None
    return _Reply(200, {"following": on})


def _save(req: _Req) -> _Reply:
    return _story(req, feedview.save, True)


def _unsave(req: _Req) -> _Reply:
    return _story(req, feedview.unsave, False)


def _follow(req: _Req) -> _Reply:
    return _topic(req, topics.follow, True)


def _unfollow(req: _Req) -> _Reply:
    return _topic(req, topics.unfollow, False)


def _topics(req: _Req) -> _Reply:
    rows = topics.list_topics(req.db, req.person.name)
    keys = ("id", "name", "following", "stories")
    return _Reply(200, [{key: row[key] for key in keys} for row in rows])


def _status(req: _Req) -> _Reply:
    now = datetime.now(UTC)
    approved = store.sources(req.db, "approved")
    failing = sum(ingest.health(req.db, row["id"], now).state == "failing" for row in approved)
    return _Reply(
        200,
        {
            "last_pass_at": store.get_meta(req.db, "last_pass_at"),
            "sources": {"approved": len(approved), "failing": failing},
            "loop_error": req.loop.last_error if req.loop is not None else None,
        },
    )


@dataclass(frozen=True)
class _Route:
    method: str
    pattern: re.Pattern[str]
    handler: Callable[[_Req], _Reply]
    open_to_all: bool = False  # only /api/me and /api/status work without a display name


_ID = "([0-9]{1,18})"  # ASCII digits only (a str pattern's \d also matches other scripts)
_ROUTES = (
    _Route("GET", re.compile("/api/me"), _me, open_to_all=True),
    _Route("POST", re.compile("/api/me"), _set_me, open_to_all=True),
    _Route("GET", re.compile("/api/status"), _status, open_to_all=True),
    _Route("GET", re.compile("/api/feed"), _feed),
    _Route("GET", re.compile("/api/feed/new"), _feed_new),
    _Route("POST", re.compile(f"/api/stories/{_ID}/save"), _save),
    _Route("DELETE", re.compile(f"/api/stories/{_ID}/save"), _unsave),
    _Route("GET", re.compile("/api/topics"), _topics),
    _Route("POST", re.compile(f"/api/topics/{_ID}/follow"), _follow),
    _Route("DELETE", re.compile(f"/api/topics/{_ID}/follow"), _unfollow),
)


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    root: Path
    allowed_hosts: frozenset[str]
    advertised_port: int = 0
    loop: Loop | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.active_connections = 0
        self._per_address: dict[str, int] = {}
        self._count = threading.Lock()
        super().__init__(*args, **kwargs)

    def verify_request(self, request: Any, client_address: Any) -> bool:
        with self._count:
            address = str(client_address[0])
            if (
                self.active_connections >= MAX_CONNECTIONS
                or self._per_address.get(address, 0) >= MAX_PER_ADDRESS
            ):
                return False  # closed by the server loop with no handler thread
            self.active_connections += 1
            self._per_address[address] = self._per_address.get(address, 0) + 1
        return True

    def _release(self, client_address: Any) -> None:
        address = str(client_address[0])
        with self._count:
            self.active_connections -= 1
            if self._per_address[address] <= 1:
                del self._per_address[address]
            else:
                self._per_address[address] -= 1

    def process_request(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request(request, client_address)
        except BaseException:
            # the handler thread never ran (the OS refused it), so it cannot release
            self._release(client_address)
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._release(client_address)


def _params(query: str) -> dict[str, str]:
    """The query's parameters, blanks kept, the first of a repeated one."""
    try:
        found = urllib.parse.parse_qs(
            query, keep_blank_values=True, errors="strict", max_num_fields=MAX_PARAMS
        )
    except (UnicodeDecodeError, ValueError):  # not UTF-8, or too many fields
        raise _refuse(400, "the query string is not valid") from None
    return {name: values[0] for name, values in found.items()}


def _static(path: str) -> _Reply:
    """The page for ``/`` or the allowlisted file for ``/static/<name>``; the path is compared with
    the allowlist's names and never joined to a directory."""
    entry = (PAGE, _HTML) if path == "/" else STATIC.get(path[len("/static/") :])
    if entry is None:
        raise _refuse(404, "not found")
    return _Reply(
        200, entry[0].read_bytes(), {"Content-Type": entry[1], "Cache-Control": "no-cache"}
    )


class Handler(BaseHTTPRequestHandler):
    timeout = SOCKET_TIMEOUT
    server_version = "Signal"
    sys_version = ""
    _deadline: threading.Timer | None = None

    def setup(self) -> None:
        super().setup()
        # The absolute limit on this connection: the socket timeout is per read and a trickling
        # client never reaches it, so a timer shuts the socket down 2 * SOCKET_TIMEOUT after accept.
        self._deadline = threading.Timer(2 * SOCKET_TIMEOUT, self._expire, args=(self.connection,))
        self._deadline.daemon = True
        self._deadline.start()

    @staticmethod
    def _expire(connection: socket.socket) -> None:
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError:  # already closed by the handler or the peer: nothing left to cut
            pass

    def finish(self) -> None:
        if self._deadline is not None:
            self._deadline.cancel()
        super().finish()

    @property
    def _service(self) -> _Server:
        return cast(_Server, self.server)

    def log_message(self, format: str, *args: Any) -> None:
        log.info("%s %s", self.address_string(), format % args)

    def do_GET(self) -> None:
        self._serve()

    do_POST = do_DELETE = do_PUT = do_PATCH = do_HEAD = do_OPTIONS = do_GET

    def _serve(self) -> None:
        if self.request_version == "HTTP/0.9":
            self.close_connection = True  # no headers exist to check and none can be sent
            log.info("%s: HTTP/0.9 request closed", self.address_string())
            return
        try:
            if not self.path.startswith("/"):
                raise _refuse(400, "the request target must be a path")
            self._check_origin()
            if self.headers.get("Transfer-Encoding") is not None:
                raise _refuse(411, "a body needs Content-Length")
            self._send(self._dispatch(urllib.parse.urlsplit(self.path)))
        except _Reply as reply:
            self._send(reply)
        except Exception:
            # The one catch-all of a request, documented: whatever a handler raises becomes a 500
            # with fixed text. The traceback goes to the log; neither it nor the exception text
            # reaches the client. KeyboardInterrupt and SystemExit (BaseException) are not caught.
            log.exception("%s %s", self.command, self.path)
            self._send(_refuse(500, _FAILED))

    def _check_origin(self) -> None:
        hosts = self.headers.get_all("Host") or []
        if len(hosts) != 1 or hosts[0] not in self._service.allowed_hosts:
            raise _refuse(403, "this address is not the one the service was started on")
        site = self.headers.get_all("Sec-Fetch-Site")
        if site is not None and site not in (["same-origin"], ["none"]) and not self._navigation():
            raise _refuse(403, "the request came from another site")
        origins = self.headers.get_all("Origin") or []
        acceptable = [f"http://{hosts[0]}"]
        if self._service.advertised_port == 80 and hosts[0].endswith(":80"):
            acceptable.append(f"http://{hosts[0][:-3]}")  # browsers leave the default port out
        if (self.command != "GET" or origins) and not (
            len(origins) == 1 and origins[0] in acceptable
        ):
            raise _refuse(403, "the request did not come from the service's own page")

    def _navigation(self) -> bool:
        """A top-level navigation to a document: only a GET with both fetch-metadata values."""
        return (
            self.command == "GET"
            and self.headers.get_all("Sec-Fetch-Mode") == ["navigate"]
            and self.headers.get_all("Sec-Fetch-Dest") == ["document"]
        )

    def end_headers(self) -> None:
        # Here, not in _send, so the replies http.server writes itself (501, 400, 414) carry them.
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy", _POLICY)
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def _send(self, reply: _Reply) -> None:
        if isinstance(reply.body, bytes):
            data, headers = reply.body, reply.headers
        else:
            data = json.dumps(reply.body, ensure_ascii=False).encode("utf-8")
            headers = {"Content-Type": _JSON, "Cache-Control": "no-store", **reply.headers}
        try:
            self.send_response(reply.status)
            self.send_header("Content-Length", str(len(data)))
            for name, value in headers.items():
                self.send_header(name, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        except OSError as error:  # the peer went away or stalled: nothing more can be said to it
            log.info("%s %s: reply not delivered (%s)", self.command, self.path, error)

    def _json_body(self) -> dict[str, Any]:
        values = self.headers.get_all("Content-Length") or []
        if not values:
            raise _refuse(411, "a body needs Content-Length")
        text = values[0].strip()
        if len(values) != 1 or not (text.isascii() and text.isdigit()) or len(text) > 15:
            raise _refuse(400, "Content-Length is not a length")
        length = int(text)
        if length > MAX_JSON:
            raise _refuse(413, f"a request body is at most {MAX_JSON // 1024} KiB")
        try:
            data = self.rfile.read(length)
        except OSError as error:  # the body stalled past the socket timeout or the peer reset
            log.info("%s %s: request body did not arrive (%s)", self.command, self.path, error)
            raise _refuse(400, "the request body did not arrive") from None
        if len(data) != length:
            raise _refuse(400, "the request body ended early")
        try:
            body = json.loads(data.decode("utf-8"))
        except (ValueError, RecursionError):  # bad UTF-8, bad JSON, or nesting past the parser
            raise _refuse(400, "the request body is not valid JSON") from None
        if not isinstance(body, dict):
            raise _refuse(400, "the request body must be a JSON object")
        return body

    def _dispatch(self, url: urllib.parse.SplitResult) -> _Reply:
        path = url.path
        if path == "/" or path.startswith("/static/"):
            if self.command != "GET":
                raise _Reply(405, {"error": "method not allowed"}, {"Allow": "GET"})
            return _static(path)
        allowed: list[str] = []
        for route in _ROUTES:
            found = route.pattern.fullmatch(path)
            if found is None:
                continue
            if route.method == self.command:
                return self._api(route, found.groups(), url.query)
            allowed.append(route.method)
        if allowed:
            raise _Reply(405, {"error": "method not allowed"}, {"Allow": ", ".join(allowed)})
        raise _refuse(404, "not found")

    def _api(self, route: _Route, groups: tuple[str, ...], query: str) -> _Reply:
        params = _params(query)
        db = store.open_db(self._service.root)  # this request's own connection
        try:
            user = identity.current_user(db, self.headers.get("Cookie"))
            if user is None and not route.open_to_all:
                raise _refuse(401, _NEEDS_NAME)
            request = _Req(db, user, groups, params, self._json_body, self._service.loop)
            return route.handler(request)
        finally:
            db.close()


def _wildcard(host: str) -> bool:
    """True when ``host`` is empty or resolves to an address that means every interface."""
    if not host:
        return True
    try:
        found = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError):
        return False  # not an address: binding it fails with its own message
    for *_, sockaddr in found:
        address = ipaddress.ip_address(str(sockaddr[0]).partition("%")[0])
        mapped = getattr(address, "ipv4_mapped", None)
        if address.is_unspecified or (mapped is not None and mapped.is_unspecified):
            return True
    return False


def _hosts(host: str, port: int) -> frozenset[str]:
    names = [host, "localhost"] if host == "127.0.0.1" else [host]
    allowed = {f"{name}:{port}" for name in names}
    if port == 80:
        allowed.update(names)  # a browser leaves the default port out of Host
    return frozenset(allowed)


def _require_files() -> None:
    missing = [str(path) for path, _ in [(PAGE, ""), *STATIC.values()] if not path.is_file()]
    if missing:
        raise StartError("page files missing: " + ", ".join(missing))


def make_server(
    root: Path, host: str, port: int, *, loop: Loop | None = None
) -> ThreadingHTTPServer:
    """A server bound to ``host:port`` (port 0 picks one); not yet serving.

    Raises ValueError for a wildcard host and StartError for a missing page file, before binding."""
    if _wildcard(host):
        raise ValueError(WILDCARD_MESSAGE)
    _require_files()
    server = _Server((host, port), Handler)
    port = server.server_address[1]
    server.root, server.allowed_hosts, server.advertised_port = root, _hosts(host, port), port
    server.loop = loop
    return server


def serve(root: Path, host: str, port: int, *, tick: float = 60.0) -> int:
    """Run the service and its ingest loop until interrupted; 2 when it cannot start."""
    if not 0 <= port <= 65535:
        print("--port must be from 0 to 65535", file=sys.stderr)
        return 2
    loop = Loop(root)
    try:
        server = make_server(root, host, port, loop=loop)
    except (ValueError, StartError, OSError, OverflowError) as error:  # wildcard, files, address
        print(error, file=sys.stderr)
        return 2
    try:
        store.open_db(root).close()  # a store that cannot be opened fails here, not per request
    except (OSError, sqlite3.Error, store.StoreError) as error:
        server.server_close()
        print(f"cannot open the store under {root}: {error}", file=sys.stderr)
        return 2
    stop = threading.Event()
    worker = threading.Thread(target=loop.run_until, args=(stop, tick), daemon=True)
    worker.start()
    print(f"serving http://{host}:{server.server_address[1]}/", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=5)
    return 0
