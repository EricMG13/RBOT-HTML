"""Fetch feed bytes from owner-approved addresses; the only place Signal uses the network.

Rules: https only; the host must be a plain DNS name (no IP literal, userinfo, percent
escape or non-ASCII); every address it resolves to must be public (NAT64 and IPv4-compatible
IPv6 forms included); 10-second timeout per socket operation; 2 MB body cap; conditional
requests with ETag / Last-Modified; environment and system proxies are ignored; at most three
redirect hops, each re-checked with the same rules.

Total deadline: the exchange (address checks, DNS, connect, TLS, headers, every hop and the
body) runs on a worker thread; fetch waits at most TOTAL_SECONDS for it, then shuts down the
connection the worker holds and returns within a further CLOSE_SECONDS.

Known ceilings:
- The owner approves only the start address. Up to three redirect hops go to hosts nobody
  approved, protected only by the same rules.
- The address check and the connection are two separate DNS lookups, so a host that changes
  its answer between them (DNS rebinding) passes. The owner approving each source by hand is
  the control for that.
- The standard library cannot interrupt a DNS lookup, a TCP connect or a TLS handshake. When
  the deadline falls in one of them, fetch still returns on time. After the deadline no new
  connection is opened (each connection attempt and each redirect hop checks first), but a
  worker caught inside one lookup, connect or handshake ends only when that single step ends
  (the system resolver's timeout; 10 s per resolved address; 10 s for the handshake), then
  closes. A connection is shut down at the deadline only once it is held: after the TLS
  handshake on the default path, after the response headers with an injected opener.
"""

import contextlib
import functools
import http.client
import ipaddress
import queue
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

TIMEOUT_SECONDS = 10
TOTAL_SECONDS = 10
CLOSE_SECONDS = 0.5
MAX_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
CHUNK_BYTES = 64 * 1024
USER_AGENT = "Mozilla/5.0 (compatible; signal-feed/1.0)"
_ERROR_TEXT_LIMIT = 200

Resolver = Callable[[str], Iterable[str]]

_LABEL = r"(?:[a-z0-9]|[a-z0-9][a-z0-9-]{0,61}[a-z0-9])"
_NETLOC = re.compile(rf"({_LABEL}(?:\.{_LABEL})+)(?::[0-9]{{1,5}})?")
_EMBEDDING_V4 = (ipaddress.ip_network("64:ff9b::/96"), ipaddress.ip_network("::/96"))


class FetchRefused(ValueError):
    """A fetch rule was broken; the message names the rule."""


def _short(error: object) -> str:
    return str(error)[:_ERROR_TEXT_LIMIT]


def _resolve(host: str) -> Iterable[str]:
    return [str(info[4][0]) for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)]


def _plain_host(netloc: str) -> str:
    # ASCII only before lower-casing: U+212A (Kelvin sign) would otherwise become "k".
    match = _NETLOC.fullmatch(netloc.lower()) if netloc.isascii() else None
    if match is None or len(match.group(1)) > 253:
        raise FetchRefused("feed address must use a plain host name")
    host = match.group(1)
    try:
        socket.inet_aton(host)
    except OSError:
        numeric = host.rsplit(".", 1)[-1].isdigit()
    else:
        numeric = True
    if numeric:
        raise FetchRefused("feed address must use a plain host name")
    return host


def _check_public(host: str, address: str) -> None:
    # Scope ids on IPv6 literals ("fe80::1%en0") are not part of the address.
    parsed = ipaddress.ip_address(address.split("%", 1)[0])
    if not parsed.is_global or any(parsed in net for net in _EMBEDDING_V4):
        raise FetchRefused(f"{host} resolves to {address}, which is not a public address")


def _check(url: str, resolve: Resolver) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise FetchRefused(f"only https addresses are fetched, not {parts.scheme or 'none'}")
    if not parts.netloc:
        raise FetchRefused("address has no host")
    host = _plain_host(parts.netloc)
    try:
        addresses = list(resolve(host))
    except OSError as error:
        raise FetchRefused(f"could not resolve {host}: {_short(error)}") from error
    if not addresses:
        raise FetchRefused(f"{host} resolved to no address")
    for address in addresses:
        _check_public(host, address)


def check_address(url: str, resolve: Resolver | None = None) -> None:
    """Raise FetchRefused unless url is https, a plain host name, resolving only to public IPs."""
    try:
        _check(
            url, _resolve if resolve is None else resolve
        )  # looked up now, so tests can replace it
    except FetchRefused:
        raise
    except ValueError as error:
        raise FetchRefused(f"feed address is not valid: {_short(error)}") from error


@dataclass(frozen=True)
class Fetched:
    """body is None means the server answered 304 Not Modified."""

    body: bytes | None
    etag: str | None
    modified: str | None


def _check_deadline(deadline: float | None) -> None:
    if deadline is not None and time.monotonic() > deadline:
        raise FetchRefused(f"feed took longer than {TOTAL_SECONDS} seconds")


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, resolve: Resolver, deadline: float | None) -> None:
        self._resolve = resolve
        self._deadline = deadline

    def redirect_request(
        self, req: urllib.request.Request, *args: Any
    ) -> urllib.request.Request | None:
        # urllib passes (fp, code, msg, headers, newurl); fp is the 3xx response. Close it
        # first: urllib would otherwise read its body whole, outside the size cap.
        fp, newurl = args[0], args[-1]
        try:
            hops = sum(getattr(req, "redirect_dict", {}).values())
            if hops >= MAX_REDIRECTS:
                raise FetchRefused(f"more than {MAX_REDIRECTS} redirects")
            _check_deadline(self._deadline)
            check_address(newurl, self._resolve)
            _check_deadline(self._deadline)  # the lookup may have ended after the deadline
        finally:
            fp.close()
        return super().redirect_request(req, *args)


def redirect_handler(
    resolve: Resolver = _resolve, deadline: float | None = None
) -> urllib.request.HTTPRedirectHandler:
    """A redirect handler that re-checks every hop and stops after MAX_REDIRECTS."""
    return _CheckedRedirects(resolve, deadline)


class _Watch:
    """The connections one fetch holds, so the caller can shut them down at the deadline.

    Each is held as a duplicate descriptor, closed only under the lock, so a shutdown can never
    reach a descriptor number the worker has closed and the system has reused.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._held: list[socket.socket] = []
        self._expired = False

    def hold(self, fileno: int) -> None:
        # Borrow the descriptor, then duplicate it with the socket-aware fromfd (os.dup does not
        # take Windows socket handles). Borrowing first means a descriptor that is not a socket
        # raises before anything is duplicated (fromfd alone leaks its duplicate). The borrowed
        # object is detached, never closed: the connection stays the worker's.
        borrowed = socket.socket(fileno=fileno)
        try:
            # fromfd, not borrowed.dup(): dup ends in settimeout(None), which would switch the
            # shared descriptor to blocking and take the worker's per-read timeout away.
            held = socket.fromfd(fileno, borrowed.family, borrowed.type, borrowed.proto)
        finally:
            borrowed.detach()
        with self._lock:
            self._held.append(held)
            if self._expired:
                _shut(held)

    def check(self) -> None:
        """Raise FetchRefused once the deadline has passed and the connections were cut."""
        with self._lock:
            expired = self._expired
        if expired:
            raise FetchRefused(f"feed took longer than {TOTAL_SECONDS} seconds")

    def expire(self) -> None:
        with self._lock:
            self._expired = True
            for held in self._held:
                _shut(held)

    def release(self) -> None:
        with self._lock:
            for held in self._held:
                held.close()
            self._held.clear()


def _shut(held: socket.socket) -> None:
    # The peer may already have closed it (ENOTCONN); the connection is down either way.
    with contextlib.suppress(OSError):
        held.shutdown(socket.SHUT_RDWR)


class _HeldConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, *, watch: _Watch, **kwargs: Any) -> None:
        super().__init__(host, **kwargs)
        self._watch = watch
        self._create_connection = self._open_socket

    def _open_socket(
        self, address: tuple[str, int], timeout: float | None, source_address: Any = None
    ) -> socket.socket:
        """socket.create_connection, refused once the watch has expired."""
        self._watch.check()
        # Looked up here so the deadline can be checked between the lookup and the connect:
        # create_connection repeats the lookup (normally answered from the resolver's cache)
        # and cannot be interrupted once it starts.
        # A failed lookup is not reported here: create_connection repeats it and raises the error.
        with contextlib.suppress(OSError):
            socket.getaddrinfo(address[0], address[1], type=socket.SOCK_STREAM)
        self._watch.check()
        opened = socket.create_connection(address, timeout, source_address)
        try:
            self._watch.check()  # the connect itself may have ended after the deadline
        except FetchRefused:
            opened.close()
            raise
        return opened

    def connect(self) -> None:
        self._watch.check()
        super().connect()
        self._watch.hold(self.sock.fileno())


class _HeldHTTPS(urllib.request.HTTPSHandler):
    def __init__(self, watch: _Watch) -> None:
        super().__init__()
        self._watch = watch

    def https_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        return self.do_open(functools.partial(_HeldConnection, watch=self._watch), req)


def _default_opener(resolve: Resolver, deadline: float, watch: _Watch) -> Callable[..., Any]:
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), redirect_handler(resolve, deadline), _HeldHTTPS(watch)
    ).open


def _hold_response(response: Any, watch: _Watch) -> None:
    try:
        watch.hold(response.fileno())
    except (AttributeError, OSError, ValueError):
        # No socket under this response (an in-memory body): nothing to cut at the deadline;
        # fetch still returns on time, and the worker ends with that body.
        return


def _read_capped(response: Any, deadline: float) -> bytes:
    reader = getattr(response, "read1", response.read)
    chunks: list[bytes] = []
    total = 0
    while True:
        _check_deadline(deadline)
        chunk = bytes(reader(min(CHUNK_BYTES, MAX_BYTES + 1 - total)))
        if not chunk:
            _check_deadline(deadline)  # a cut connection also reads as the end of the body
            return b"".join(chunks)
        total += len(chunk)
        if total > MAX_BYTES:
            raise FetchRefused("feed is larger than 2 MB")
        chunks.append(chunk)


@dataclass(frozen=True)
class _Job:
    url: str
    etag: str | None
    modified: str | None
    resolve: Resolver
    opener: Callable[..., Any] | None


def _exchange(job: _Job, deadline: float, watch: _Watch) -> Fetched:
    """Runs on the fetch thread: address check, request, every hop and the capped body."""
    url, etag, modified, resolve = job.url, job.etag, job.modified, job.resolve
    check_address(url, resolve)
    _check_deadline(deadline)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if etag:
        request.add_header("If-None-Match", etag)
    if modified:
        request.add_header("If-Modified-Since", modified)
    opener = job.opener
    open_url = opener if opener is not None else _default_opener(resolve, deadline, watch)
    try:
        response = open_url(request, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as error:
        error.close()
        if error.code == 304:
            return Fetched(None, etag, modified)
        raise FetchRefused(f"server answered HTTP {error.code}") from error
    except (urllib.error.URLError, OSError, http.client.HTTPException) as error:
        raise FetchRefused(f"fetch failed: {_short(error)}") from error
    with contextlib.closing(response):
        status = response.status
        if status == 304:
            return Fetched(None, etag, modified)
        if status != 200:
            raise FetchRefused(f"server answered HTTP {status}")
        _hold_response(response, watch)
        try:
            body = _read_capped(response, deadline)
        except (OSError, http.client.HTTPException) as error:
            raise FetchRefused(f"fetch failed: {_short(error)}") from error
        return Fetched(body, response.headers.get("ETag"), response.headers.get("Last-Modified"))


def _work(
    exchange: Callable[[], Fetched],
    watch: _Watch,
    results: "queue.SimpleQueue[Fetched | ValueError | None]",
) -> None:
    outcome: Fetched | ValueError | None = None
    try:
        outcome = exchange()
    except ValueError as error:  # FetchRefused, and the address errors fetch turns into one
        outcome = error
    finally:
        watch.release()
        results.put(outcome)  # None: a bug escaped, and threading.excepthook prints it


def _fetch(
    url: str,
    etag: str | None,
    modified: str | None,
    resolve: Resolver,
    opener: Callable[..., Any] | None,
) -> Fetched:
    deadline = time.monotonic() + TOTAL_SECONDS
    watch = _Watch()
    results: queue.SimpleQueue[Fetched | ValueError | None] = queue.SimpleQueue()
    job = _Job(url, etag, modified, resolve, opener)
    exchange = functools.partial(_exchange, job, deadline, watch)
    worker = threading.Thread(
        target=_work, args=(exchange, watch, results), name="signal-fetch", daemon=True
    )
    worker.start()
    try:
        outcome = results.get(timeout=TOTAL_SECONDS)
    except queue.Empty:
        raise FetchRefused(f"feed took longer than {TOTAL_SECONDS} seconds") from None
    finally:
        watch.expire()
        worker.join(CLOSE_SECONDS)
    if outcome is None:
        raise RuntimeError("the fetch thread failed; its traceback is on standard error")
    if isinstance(outcome, ValueError):
        raise outcome
    return outcome


def fetch(
    url: str,
    etag: str | None,
    modified: str | None,
    *,
    resolve: Resolver = _resolve,
    opener: Callable[..., Any] | None = None,
) -> Fetched:
    """Fetch url conditionally; raise FetchRefused for any broken rule, error or bad status."""
    try:
        return _fetch(url, etag, modified, resolve, opener)
    except FetchRefused:
        raise
    except ValueError as error:
        raise FetchRefused(f"feed address could not be used: {_short(error)}") from error
