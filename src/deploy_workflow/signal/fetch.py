"""Fetch feed bytes from owner-approved addresses; the only place Signal uses the network.

Built on ``research.webfetch`` (the repository's pinned fetcher): its public-address rule, its
pinned TLS connection and its deadline-bounded socket. Signal adds only what feeds need:
conditional requests, 304, the feed ``Accept`` value and the refusal of NAT64 and
IPv4-compatible IPv6 forms.

Rules:
- https only; the host must be a plain DNS name (no IP literal, userinfo, percent escape or
  non-ASCII). The host is resolved once per hop; every address it resolves to must be public
  (``webfetch.is_public``, and NAT64 and IPv4-compatible IPv6 forms are refused too).
- The connection goes to the first checked address, with the certificate verified for the host
  name. Nothing looks the name up again, so a host that changes its answer after the check
  cannot change where the request goes.
- Redirects (301, 302, 303, 307, 308) are followed by this module's own loop, at most
  MAX_REDIRECTS in all, never through a proxy. A target must be https, a plain host name and
  the default port; each hop is resolved, checked and pinned like the first. A redirect
  response's body is not read, and the conditional headers go to the first address only.
- 10 seconds per socket operation (TIMEOUT_SECONDS); one TOTAL_SECONDS deadline for the whole
  fetch, every hop, headers and body included; a 2 MB body cap; a body shorter than its
  declared Content-Length, and any Content-Encoding other than identity, are refused.

Known ceiling: the one system DNS lookup per hop cannot be interrupted by the standard library.
A lookup that hangs ends only at the resolver's own timeout, after which the deadline is checked
and no connection is opened once it has passed.
"""

import http.client
import ipaddress
import re
import socket
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from deploy_workflow.research import webfetch
from deploy_workflow.research.webfetch import ConnectionLike, ConnectionTarget, ResponseLike

TIMEOUT_SECONDS = 10
TOTAL_SECONDS = 10
MAX_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
USER_AGENT = "Mozilla/5.0 (compatible; signal-feed/1.0)"
ACCEPT = (
    "application/atom+xml, application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5"
)
_DEFAULT_PORT = 443
_CHUNK_BYTES = 64 * 1024
_ERROR_TEXT_LIMIT = 200
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})

Resolver = Callable[[str], Iterable[str]]
Connector = Callable[[ConnectionTarget], ConnectionLike]
Clock = Callable[[], float]

_LABEL = r"(?:[a-z0-9]|[a-z0-9][a-z0-9-]{0,61}[a-z0-9])"
_NETLOC = re.compile(rf"({_LABEL}(?:\.{_LABEL})+)(?::[0-9]{{1,5}})?")
_DIGITS = re.compile(r"[0-9]{1,18}")
_VALIDATOR = re.compile(r"[\x20-\x7e]{1,256}")
_EMBEDDING_V4 = (ipaddress.ip_network("64:ff9b::/96"), ipaddress.ip_network("::/96"))


class FetchRefused(ValueError):
    """A fetch rule was broken; the message names it, in at most 200 characters."""

    def __init__(self, reason: object) -> None:
        super().__init__(_short(reason))


@dataclass(frozen=True)
class Fetched:
    """body is None means the server answered 304 Not Modified."""

    body: bytes | None
    etag: str | None
    modified: str | None


@dataclass(frozen=True)
class _Place:
    host: str
    port: int
    path: str


@dataclass(frozen=True)
class Wiring:
    """The connector and clock a fetch uses; the defaults are the production values."""

    connect: Connector | None = None  # None: webfetch.pinned_connection
    clock: Clock = time.monotonic


@dataclass(frozen=True)
class _Budget:
    """What one fetch uses: the resolver, connector and clock, and its one deadline."""

    resolve: Resolver
    connect: Connector
    clock: Clock
    deadline: float

    def check(self) -> None:
        if self.clock() > self.deadline:
            raise FetchRefused(f"feed took longer than {TOTAL_SECONDS} seconds")


def _short(error: object) -> str:
    return " ".join(str(error).split())[:_ERROR_TEXT_LIMIT]


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


def _locate(url: str, *, redirect: bool) -> _Place:
    """The host, port and request path of an acceptable https address."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as error:
        raise FetchRefused(f"feed address is not valid: {_short(error)}") from error
    if parts.scheme != "https":
        raise FetchRefused("only https addresses are fetched")
    if not parts.netloc:
        raise FetchRefused("address has no host")
    host = _plain_host(parts.netloc)
    if redirect and port not in (None, _DEFAULT_PORT):
        raise FetchRefused("a redirect must use the default port")
    path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    if not path.isascii():
        raise FetchRefused("feed address path must be ASCII")
    return _Place(host, port or _DEFAULT_PORT, path)


def _is_public(address: str) -> bool:
    if not webfetch.is_public(address):
        return False
    # Scope ids on IPv6 literals ("fe80::1%en0") are not part of the address.
    parsed = ipaddress.ip_address(address.split("%", 1)[0])
    return not any(parsed in net for net in _EMBEDDING_V4)


def _checked(host: str, resolve: Resolver) -> list[str]:
    """Resolve once; every address must be public. Returns them in order."""
    try:
        addresses = list(resolve(host))
    except OSError as error:
        raise FetchRefused(f"could not resolve {host}: {_short(error)}") from error
    if not addresses:
        raise FetchRefused(f"{host} resolved to no address")
    for address in addresses:
        if not _is_public(address):
            raise FetchRefused(f"{host} resolves to {address}, which is not a public address")
    return addresses


def check_address(url: str, resolve: Resolver | None = None) -> None:
    """Raise FetchRefused unless url is https, a plain host name, resolving only to public IPs."""
    # The resolver is looked up now, so tests can replace it.
    _checked(_locate(url, redirect=False).host, _resolve if resolve is None else resolve)


def _declared_length(response: ResponseLike) -> int | None:
    """The declared length, None if none that http.client would use; refuses the forms it would."""
    raw = response.getheader("Content-Length")  # repeated headers arrive joined with ", "
    declared = (raw or "").strip()
    if _DIGITS.fullmatch(declared):
        return int(declared)
    if "," in declared:
        raise FetchRefused("the response declared an unusable length")
    try:
        usable = (
            int(declared) >= 0
        )  # "+1000", "1_000", 19 digits: http.client reads these as lengths
    except ValueError:
        return None  # http.client ignores what int() rejects
    if usable:
        raise FetchRefused("the response declared an unusable length")
    return None


def _read_body(response: ResponseLike, budget: _Budget) -> bytes:
    declared = _declared_length(response)
    if declared is not None and declared > MAX_BYTES:
        raise FetchRefused("feed is larger than 2 MB")
    chunks: list[bytes] = []
    got = 0
    while got <= MAX_BYTES:
        chunk = response.read(min(_CHUNK_BYTES, MAX_BYTES + 1 - got))
        budget.check()
        if not chunk:
            break
        chunks.append(chunk)
        got += len(chunk)
    if got > MAX_BYTES:
        raise FetchRefused("feed is larger than 2 MB")
    if declared is not None and got < declared:
        raise FetchRefused(f"the response ended early ({got} of {declared} bytes)")
    return b"".join(chunks)


def _redirect_url(current: str, response: ResponseLike, hops: int) -> str:
    if hops >= MAX_REDIRECTS:
        raise FetchRefused(f"more than {MAX_REDIRECTS} redirects")
    location = (response.getheader("Location") or "").strip()
    if not location:
        raise FetchRefused("the redirect has no usable location")
    try:
        return urljoin(current, location)
    except ValueError as error:
        raise FetchRefused("the redirect has no usable location") from error


def _validator(response: ResponseLike, name: str) -> str | None:
    value = response.getheader(name)
    return value if value is not None and _VALIDATOR.fullmatch(value) else None


def _answer(
    response: ResponseLike,
    etag: str | None,
    modified: str | None,
    budget: _Budget,
    *,
    redirected: bool,
) -> Fetched:
    if response.status == 304:
        if redirected:
            raise FetchRefused("a redirect target answered 304, but it was sent no validators")
        # Decision (controller ruling): a clean validator in the 304 replaces the one sent.
        return Fetched(
            None,
            _validator(response, "ETag") or etag,
            _validator(response, "Last-Modified") or modified,
        )
    if response.status != 200:
        raise FetchRefused(f"server answered HTTP {response.status}")
    encoding = (response.getheader("Content-Encoding") or "").strip().lower()
    if encoding not in ("", "identity"):
        raise FetchRefused("feed uses a content encoding")
    body = _read_body(response, budget)
    if redirected:  # validators belong to the first address only
        return Fetched(body, None, None)
    return Fetched(body, _validator(response, "ETag"), _validator(response, "Last-Modified"))


def _stored(value: str | None) -> str | None:
    return value if value is not None and _VALIDATOR.fullmatch(value) else None


def fetch(
    url: str,
    etag: str | None,
    modified: str | None,
    *,
    resolve: Resolver | None = None,
    wiring: Wiring | None = None,
) -> Fetched:
    """Fetch url conditionally; raise FetchRefused for any broken rule, error or bad status."""
    wiring = wiring or Wiring()
    etag = _stored(etag)  # a stored value is held to what a server may send
    modified = _stored(modified)
    budget = _Budget(
        _resolve if resolve is None else resolve,  # looked up now, so tests can replace it
        webfetch.pinned_connection if wiring.connect is None else wiring.connect,
        wiring.clock,
        wiring.clock() + TOTAL_SECONDS,
    )
    try:
        return _follow(url, etag, modified, budget)
    except FetchRefused:
        raise
    except http.client.HTTPException as error:  # its text can carry what the server sent
        raise FetchRefused(f"fetch failed: {type(error).__name__}") from error
    # ValueError: http.client refusing a header value or a request line it cannot encode.
    except (OSError, ValueError) as error:
        raise FetchRefused(f"fetch failed: {_short(error) or type(error).__name__}") from error


def _follow(url: str, etag: str | None, modified: str | None, budget: _Budget) -> Fetched:
    current = url
    hops = 0
    while True:
        place = _locate(current, redirect=hops > 0)
        budget.check()
        address = _checked(place.host, budget.resolve)[0]
        budget.check()  # the lookup may have ended after the deadline
        headers = {
            "Host": place.host if place.port == _DEFAULT_PORT else f"{place.host}:{place.port}",
            "User-Agent": USER_AGENT,
            "Accept": ACCEPT,
            "Accept-Encoding": "identity",
            "Connection": "close",
        }
        if hops == 0:  # the validators belong to the first address only
            if etag:
                headers["If-None-Match"] = etag
            if modified:
                headers["If-Modified-Since"] = modified
        target = ConnectionTarget(
            place.host, address, place.port, TIMEOUT_SECONDS, budget.deadline, budget.clock
        )
        connection = budget.connect(target)
        try:
            connection.request("GET", place.path, headers=headers)
            response = connection.getresponse()
            budget.check()
            if response.status not in _REDIRECT_STATUSES:
                return _answer(response, etag, modified, budget, redirected=hops > 0)
            current = _redirect_url(current, response, hops)
        finally:
            connection.close()
        hops += 1
