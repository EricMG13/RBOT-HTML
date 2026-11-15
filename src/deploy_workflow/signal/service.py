"""Signal's HTTP service: the feed API, its page files and the background ingest loop.

Plain ``http.server``; no framework. The service has no login and may be reachable from other
machines, so every request is hostile input. The rules are those of the run start page's service,
implemented once in ``deploy_workflow.http_base`` for both; what Signal adds or sets differently
(the per-address ceiling, the connection deadline, the page policy on every
response, the JSON object rule) is passed to that base here. Every request is checked before any
body byte is read:

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
import logging
import re
import sqlite3
import sys
import threading
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from deploy_workflow import http_base
from deploy_workflow.http_base import WILDCARD_MESSAGE
from deploy_workflow.http_base import Reply as _Reply
from deploy_workflow.http_base import refuse as _refuse
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
_NEEDS_NAME = "choose a display name first"

_WEB = Path(__file__).resolve().parent / "web"


def find_brand() -> Path:
    """The folder holding brand.css, fonts and brand/: ``web`` in the installed ``credit_os``
    package (the issuer library). Without that package the import fails by name; with it and a
    missing file, start-up names the file."""
    from importlib.resources import files  # Kept to this function: the only package-data lookup.

    return Path(str(files("credit_os").joinpath("web")))


_BRAND = find_brand()
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
    return _Reply(200, {"cards": cards, "next_before": page.next_before, "newest": page.newest})


MAX_AFTER_DIGITS = len(str(feedview.MAX_ID))


def _feed_new(req: _Req) -> _Reply:
    after = req.param("after")
    if not (after.isascii() and after.isdecimal() and len(after) <= MAX_AFTER_DIGITS):
        raise _refuse(400, f"invalid after {after!r}")
    try:
        count = feedview.new_count(req.db, req.person.name, req.param("view"), int(after))
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


class _Server(http_base.Server):
    root: Path
    loop: Loop | None = None

    def connection_limits(self) -> tuple[int, int | None]:
        return MAX_CONNECTIONS, MAX_PER_ADDRESS


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
    return http_base.listed_file(
        (PAGE, _HTML) if path == "/" else STATIC.get(path[len("/static/") :])
    )


class Handler(http_base.Handler):
    timeout = SOCKET_TIMEOUT
    server_version = "Signal"
    logger = log
    # The page policy on every response, the replies http.server writes itself included.
    response_headers = (("Content-Security-Policy", _POLICY), ("X-Frame-Options", "DENY"))

    def connection_deadline(self) -> float:
        return 2 * SOCKET_TIMEOUT

    @property
    def _service(self) -> _Server:
        return cast(_Server, self.server)

    def do_GET(self) -> None:
        self.serve_request(self._dispatch)

    do_POST = do_DELETE = do_PUT = do_PATCH = do_HEAD = do_OPTIONS = do_GET

    def read_body(self, length: int) -> bytes:
        try:
            return self.rfile.read(length)
        except OSError as error:  # the body stalled past the socket timeout or the peer reset
            log.info("%s %s: request body did not arrive (%s)", self.command, self.path, error)
            raise _refuse(400, "the request body did not arrive") from None

    def _json_body(self) -> dict[str, Any]:
        body = self.json_body(MAX_JSON)
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


def _require_files() -> None:
    missing = [str(path) for path, _ in [(PAGE, ""), *STATIC.values()] if not path.is_file()]
    if missing:
        raise StartError("page files missing: " + ", ".join(missing))


def make_server(
    root: Path, host: str, port: int, *, loop: Loop | None = None
) -> ThreadingHTTPServer:
    """A server bound to ``host:port`` (port 0 picks one); not yet serving.

    Raises ValueError for a wildcard host and StartError for a missing page file, before binding."""
    if http_base.wildcard(host):
        raise ValueError(WILDCARD_MESSAGE)
    _require_files()
    server = _Server((host, port), Handler)
    server.root, server.loop = root, loop
    return server


def serve(root: Path, host: str, port: int, *, tick: float = 60.0) -> int:
    """Run the service and its ingest loop until interrupted; 2 when it cannot start."""
    if not 0 <= port <= 65535:
        print("--port must be from 0 to 65535", file=sys.stderr)
        return 2
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    loop = Loop(root)
    try:
        server = make_server(root, host, port, loop=loop)
    except (ValueError, StartError) as error:  # wildcard address, missing page file
        print(error, file=sys.stderr)
        return 2
    except (OSError, OverflowError) as error:  # the address cannot be bound
        print(f"cannot listen on {host}:{port}: {error}", file=sys.stderr)
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
