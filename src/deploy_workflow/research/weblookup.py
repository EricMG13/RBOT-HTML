"""Public web pages and SEC EDGAR data for CP-DR, fetched safely and retained under ``<run>/web/``.

Every request is chosen by a model, so every rule here refuses before a connection is made: the
host must be on the reviewed allowlist (``web_allowlist.json``) or be one of the run's own case
hosts, the URL must be a plain https URL, the run's page and byte budget must not be spent and,
for sec.gov, the owner's contact string must be in the launching environment. The fetch itself is
``webfetch.fetch`` (public addresses only, pinned TLS, bounded redirects and reads); this module
adds the allowlist on every redirect hop, the sec.gov pacing, the content-type rule, retention and
the page's own stated date against the research cutoff.

The resolver, the connector, the clocks, the sleep and the environment are injected through
``Runtime``; its defaults are the production values.
"""

import hashlib
import io
import json
import os
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from deploy_workflow.research import webfetch
from deploy_workflow.research.contracts import ResearchError

ALLOWLIST_PATH = Path(__file__).with_name("web_allowlist.json")
USER_AGENT_ENV = "DEPLOY_WORKFLOW_SEC_USER_AGENT"
FETCH_TOOL = "fetch_page"
MAX_URL_CHARS = 2000
MAX_BODY_BYTES = 5_000_000
MAX_PAGES = 40
MAX_TOTAL_BYTES = 40_000_000
SEC_INTERVAL_S = 0.2
PAGE_CHARS = 12000  # what handoff._pages yields for a text file
MAX_MATCHES = 20
MAX_LISTED = 20
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
TAXONOMIES = ("us-gaap", "ifrs-full", "dei", "srt")
DEFAULT_USER_AGENT = "deploy-workflow-cpdr"
ACCEPT = "text/html, application/xhtml+xml, text/plain, application/json, application/pdf"

STATUS_USABLE = "usable"
STATUS_LATER = "later-event"
STATUS_UNDATED = "undated"

_EXTENSIONS = {
    "text/html": "html",
    "application/xhtml+xml": "html",
    "text/plain": "txt",
    "application/json": "json",
    "application/pdf": "pdf",
}
_META_NAMES = (
    "article:published_time",
    "datepublished",
    "date",
    "dc.date",
    "dcterms.date",
    "pubdate",
)
_HIDDEN_TAGS = frozenset({"script", "style", "noscript", "template"})
_BLOCK_TAGS = frozenset(
    {"p", "div", "br", "li", "ul", "ol", "tr", "table", "section", "article", "header", "footer"}
    | {"h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote", "title", "dd", "dt", "hr"}
)
_CHARSET = re.compile(r"charset\s*=\s*[\"']?([^\s;\"']+)", re.IGNORECASE)
_CIK = re.compile(r"[0-9]{1,10}")
_TAG = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,119}")
_SEC_MESSAGE = (
    f"sec.gov needs a contact string in the {USER_AGENT_ENV} environment variable, which the "
    "owner sets in the launching environment; it is absent or not a plain printable value"
)
_READ_IT = "read it with the paging tools"


@dataclass(frozen=True)
class Refused:
    """A lookup that was not made or not kept; nothing was retained and the budget is unchanged."""

    reason: str


@dataclass(frozen=True)
class Retained:
    """One retained page: the fields of its ``web/index.jsonl`` row."""

    source_id: str
    url: str
    final_url: str
    fetched_at: str
    sha256: str
    bytes: int
    content_type: str
    page_date: str | None
    page_date_source: str | None
    cutoff: str
    status: str
    tool: str
    module: str


@dataclass(frozen=True)
class EdgarResult:
    """An EDGAR lookup: the retained JSON's ``source_id``, a short reading and matches (search)."""

    source_id: str
    summary: str
    items: tuple[dict[str, str], ...] = ()


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class RunScope:
    """What one run fixes: its folder, its research cutoff, the module and its own case hosts."""

    run_dir: Path
    cutoff: date
    module: str
    case_hosts: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Runtime:
    """Everything that touches the outside world; the defaults are the production values."""

    resolver: webfetch.Resolver = webfetch.system_resolver
    connect: webfetch.Connector = webfetch.pinned_connection
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    now: Callable[[], datetime] = _utc_now
    env: Mapping[str, str] = field(default_factory=lambda: os.environ)


class _IndexDamaged(ResearchError):
    pass


def load_domains(path: Path = ALLOWLIST_PATH) -> tuple[str, ...]:
    """The reviewed allowlist's domains, lower-cased."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(str(row["domain"]).lower() for row in data["domains"])


def _normal(host: str) -> str:
    return host.lower().removesuffix(".")


def host_allowed(host: str, domains: tuple[str, ...], case_hosts: frozenset[str]) -> bool:
    """A listed domain or a subdomain of one (label boundary), or exactly a case host."""
    name = _normal(host)
    if not name or "" in name.split("."):
        return False
    if name in case_hosts:
        return True
    return any(name == domain or name.endswith("." + domain) for domain in domains)


def is_sec_host(host: str) -> bool:
    name = _normal(host)
    return name == "sec.gov" or name.endswith(".sec.gov")


def neutralise(text: str) -> str:
    """No ``<<<`` or ``>>>`` survives, so a page cannot forge the handoff tools' delimiters."""
    while "<<<" in text:
        text = text.replace("<<<", "<< <")
    while ">>>" in text:
        text = text.replace(">>>", "> >>")
    return text


def _media_type(content_type: str | None) -> str:
    return (content_type or "").split(";")[0].strip().lower()


def _decode(body: bytes, content_type: str | None) -> str:
    match = _CHARSET.search(content_type or "")
    if match:
        try:
            return body.decode(match.group(1), errors="replace")
        except LookupError:
            pass  # an unknown charset name: fall back to UTF-8 as for an undeclared one
    return body.decode("utf-8", errors="replace")


def _iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


class _PageParser(HTMLParser):
    """Visible text, ``<meta>`` dates, JSON-LD blocks and ``<time datetime>`` of one HTML page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.metas: dict[str, list[str]] = {}
        self.json_ld: list[str] = []
        self.times: list[str] = []
        self._text: list[str] = []
        self._hidden = 0
        self._in_ld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        if tag in _HIDDEN_TAGS:
            self._hidden += 1
        if tag == "script" and "ld+json" in values.get("type", "").lower():
            self._in_ld = True
            self.json_ld.append("")
        if tag in _BLOCK_TAGS:
            self._text.append("\n")
        if self._hidden:
            return
        if tag == "meta":
            self._meta(values)
        elif tag == "time" and values.get("datetime"):
            self.times.append(values["datetime"])

    def _meta(self, values: dict[str, str]) -> None:
        for key in ("property", "name"):
            if values.get(key) and "content" in values:
                self.metas.setdefault(values[key].lower(), []).append(values["content"])

    def handle_endtag(self, tag: str) -> None:
        if tag in _HIDDEN_TAGS and self._hidden:
            self._hidden -= 1
        if tag == "script":
            self._in_ld = False
        if tag in _BLOCK_TAGS:
            self._text.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_ld:
            self.json_ld[-1] += data
        elif not self._hidden:
            self._text.append(re.sub(r"\s+", " ", data))

    def text(self) -> str:
        lines = (line.strip() for line in "".join(self._text).split("\n"))
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _parse_html(body: bytes, content_type: str | None) -> _PageParser:
    parser = _PageParser()
    parser.feed(_decode(body, content_type))
    parser.close()
    return parser


def _json_ld_date(blocks: list[str]) -> date | None:
    for block in blocks:
        try:
            stack: list[Any] = [json.loads(block)]
        except (ValueError, RecursionError):
            continue  # an unreadable block states no date; the other sources are still tried
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                found = _iso_date(node.get("datePublished"))
                if found:
                    return found
                stack.extend(reversed(list(node.values())))
            elif isinstance(node, list):
                stack.extend(reversed(node))
    return None


def _html_date(parser: _PageParser) -> tuple[date | None, str | None]:
    for name in _META_NAMES:
        for value in parser.metas.get(name, []):
            found = _iso_date(value)
            if found:
                return found, f"meta:{name}"
    found = _json_ld_date(parser.json_ld)
    if found:
        return found, "json-ld:datePublished"
    for value in parser.times:
        found = _iso_date(value)
        if found:
            return found, "html:time"
    return None, None


def _stated_date(
    kind: str, body: bytes, content_type: str | None, record: webfetch.FetchRecord
) -> tuple[str | None, str | None]:
    """The page's own stated date and where it came from, else (None, header source or None).

    ``record.published_*`` is ``webfetch.locate_published``'s answer: a body ``Published:`` line,
    or ``Last-Modified``, which is not a stated date and only ever recorded as its source.
    """
    if kind == "html":
        found, source = _html_date(_parse_html(body, content_type))
        if found:
            return found.isoformat(), source
    if kind in ("html", "txt") and record.published_source == webfetch.SOURCE_BODY:
        return record.published_located, record.published_source
    if record.published_source == webfetch.SOURCE_HEADER:
        return None, webfetch.SOURCE_HEADER
    return None, None


def _status(page_date: str | None, cutoff: date) -> str:
    stated = _iso_date(page_date)
    if stated is None:
        return STATUS_UNDATED
    return STATUS_USABLE if stated <= cutoff else STATUS_LATER


def _pdf_pages(body: bytes) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(body))
        return [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
    except (PyPdfError, ValueError) as error:
        # Shown to the model as the page's text, so the failure is visible, not hidden.
        return [f"[this PDF could not be read: {type(error).__name__}]"]


def _pretty_json(text: str) -> str:
    try:
        return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except (ValueError, RecursionError):
        return text  # not valid JSON: the model reads the text as served


def pages_from(body: bytes, content_type: str | None) -> list[str]:
    """The text pages of a retained body, delimiters neutralised."""
    kind = _EXTENSIONS.get(_media_type(content_type), "txt")
    if kind == "pdf":
        return [neutralise(page) for page in _pdf_pages(body)]
    if kind == "html":
        text = _parse_html(body, content_type).text()
    elif kind == "json":
        text = _pretty_json(_decode(body, content_type))
    else:
        text = _decode(body, content_type)
    text = neutralise(text)
    return [text[i : i + PAGE_CHARS] for i in range(0, len(text), PAGE_CHARS)] or [""]


def _read_index(path: Path) -> list[dict[str, Any]]:
    """The retained rows. A torn last line (a crash mid-append) is ignored; other damage raises."""
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    torn = lines.pop() if not raw.endswith("\n") else ""
    rows: list[dict[str, Any]] = []
    for line in [*lines, torn]:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            if line is torn and torn:
                continue
            raise _IndexDamaged("the retained web index is damaged") from None
        if not isinstance(row, dict) or type(row.get("bytes")) is not int:
            raise _IndexDamaged("the retained web index is damaged")
        rows.append(row)
    return rows


@dataclass(frozen=True)
class _Answer:
    """A fetched, accepted response on its way to retention."""

    url: str
    final_url: str
    tool: str
    body: bytes
    media: str
    record: webfetch.FetchRecord


class _GuardedConnection:
    """Adds the per-host User-Agent and notes the address of each request (the final URL)."""

    def __init__(
        self,
        inner: webfetch.ConnectionLike,
        host: str,
        sec_agent: str | None,
        seen: list[str],
    ) -> None:
        self._inner = inner
        self._host = host
        self._sec_agent = sec_agent
        self._seen = seen

    def request(self, method: str, url: str, *, headers: Mapping[str, str]) -> None:
        merged = dict(headers)
        if self._sec_agent is not None:
            merged["User-Agent"] = self._sec_agent
        self._seen.append(f"https://{self._host}{url}")
        self._inner.request(method, url, headers=merged)

    def getresponse(self) -> webfetch.ResponseLike:
        return self._inner.getresponse()

    def close(self) -> None:
        self._inner.close()


class WebLookup:
    """The lookups of one run, retained under ``run_dir/web/``."""

    def __init__(self, scope: RunScope, runtime: Runtime | None = None) -> None:
        self._folder = scope.run_dir / "web"
        self._cutoff = scope.cutoff
        self._module = scope.module
        self._case_hosts = frozenset(_normal(host) for host in scope.case_hosts)
        self._runtime = runtime or Runtime()
        self._domains = load_domains()
        self._last_sec_start: float | None = None

    # ---- the core -------------------------------------------------------------------------

    def fetch_page(self, url: str, tool: str = FETCH_TOOL) -> Retained | Refused:
        """Fetch and retain one page, or refuse with the reason. Refusals retain nothing."""
        split = self._checked_url(url)
        if isinstance(split, Refused):
            return split
        try:
            rows = _read_index(self._folder / "index.jsonl")
            cached = self._cached(rows, url)
        except (_IndexDamaged, TypeError) as error:
            return Refused(str(error) or "the retained web index is damaged")
        if cached is not None:
            return cached
        problem = self._sec_problem(split.host) or self._budget_problem(rows)
        if problem:
            return Refused(problem)
        return self._download(url, tool, sum(int(row["bytes"]) for row in rows))

    def page_text(self, item: Retained) -> list[str]:
        """The retained page as text pages for the paging tools (delimiters neutralised)."""
        ext = _EXTENSIONS.get(_media_type(item.content_type), "txt")
        body = (self._folder / f"{item.sha256}.{ext}").read_bytes()
        return pages_from(body, item.content_type)

    def _checked_url(self, url: str) -> webfetch.SplitUrl | Refused:
        if len(url) > MAX_URL_CHARS:
            return Refused(f"the url is longer than {MAX_URL_CHARS} characters")
        try:
            split = webfetch.check_url(url)
        except webfetch.UrlRefused as refusal:
            return Refused(refusal.reason)
        if split.port != webfetch.DEFAULT_PORT:
            return Refused("a non-default port is not allowed")
        if not self._allowed(split.host):
            return Refused(f"host {split.host} is not on the web allowlist or a named case host")
        return split

    def _allowed(self, host: str) -> bool:
        return host_allowed(host, self._domains, self._case_hosts)

    def _cached(self, rows: list[dict[str, Any]], url: str) -> Retained | None:
        for row in rows:
            if row.get("url") == url:
                try:
                    return Retained(**row)
                except TypeError:
                    raise _IndexDamaged("the retained web index is damaged") from None
        return None

    def _sec_agent(self) -> str | None:
        value = self._runtime.env.get(USER_AGENT_ENV, "").strip()
        printable = value.isascii() and all(" " <= char <= "~" for char in value)
        return value if value and printable else None

    def _sec_problem(self, host: str) -> str | None:
        return _SEC_MESSAGE if is_sec_host(host) and self._sec_agent() is None else None

    def _budget_problem(self, rows: list[dict[str, Any]]) -> str | None:
        if len(rows) >= MAX_PAGES:
            return f"the run's web budget of {MAX_PAGES} retained pages is spent"
        if sum(int(row["bytes"]) for row in rows) >= MAX_TOTAL_BYTES:
            return f"the run's web budget of {MAX_TOTAL_BYTES} retained bytes is spent"
        return None

    def _pace(self) -> None:
        """At least SEC_INTERVAL_S between the starts of two sec.gov requests, redirect hops too."""
        runtime = self._runtime
        now = runtime.clock()
        if self._last_sec_start is not None:
            wait = SEC_INTERVAL_S - (now - self._last_sec_start)
            if wait > 0:
                runtime.sleep(wait)
                now = runtime.clock()
        self._last_sec_start = now

    def _connect(
        self, seen: list[str], target: webfetch.ConnectionTarget
    ) -> webfetch.ConnectionLike:
        agent = None
        if is_sec_host(target.host):
            agent = self._sec_agent()
            if agent is None:
                raise webfetch.FetchRefusal(_SEC_MESSAGE)
            self._pace()
        return _GuardedConnection(self._runtime.connect(target), target.host, agent, seen)

    def _download(self, url: str, tool: str, spent: int) -> Retained | Refused:
        seen: list[str] = []
        record, body, media = webfetch.fetch(
            url,
            manifest_hosts=frozenset(),
            resolver=self._runtime.resolver,
            connect=lambda target: self._connect(seen, target),
            cap=MAX_BODY_BYTES,
            clock=self._runtime.clock,
            host_allowed=self._allowed,
            headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": ACCEPT},
        )
        if record.reason is not None or body is None or record.sha256 is None:
            return Refused(record.reason or f"{url} returned no body")
        problem = self._body_problem(body, media, spent)
        if problem:
            return Refused(problem)
        answer = _Answer(url, seen[-1] if seen else url, tool, body, media or "", record)
        return self._retain(answer)

    def _body_problem(self, body: bytes, media: str | None, spent: int) -> str | None:
        kind = _EXTENSIONS.get(_media_type(media))
        if not _media_type(media):
            return "the response has no content type, so it is not retained"
        if kind is None:
            return f"content type {_media_type(media)[:100]!a} is not allowed"
        if kind == "pdf" and not body.startswith(b"%PDF"):
            return "the response is declared a PDF but is not one"
        if spent + len(body) > MAX_TOTAL_BYTES:
            return f"the page would pass the run's web budget of {MAX_TOTAL_BYTES} retained bytes"
        return None

    def _retain(self, answer: _Answer) -> Retained:
        body, media = answer.body, answer.media
        digest = hashlib.sha256(body).hexdigest()
        kind = _EXTENSIONS[_media_type(media)]
        page_date, source = _stated_date(kind, body, media, answer.record)
        item = Retained(
            source_id=f"web-{digest[:12]}",
            url=answer.url,
            final_url=answer.final_url,
            fetched_at=self._runtime.now().astimezone(UTC).isoformat(),
            sha256=digest,
            bytes=len(body),
            content_type=media,
            page_date=page_date,
            page_date_source=source,
            cutoff=self._cutoff.isoformat(),
            status=_status(page_date, self._cutoff),
            tool=answer.tool,
            module=self._module,
        )
        self._write(f"{digest}.{kind}", body, item)
        return item

    def _write(self, name: str, body: bytes, item: Retained) -> None:
        """The body first, then its index row, so a crash cannot leave a row without a body."""
        self._folder.mkdir(parents=True, exist_ok=True)
        target = self._folder / name
        if not target.exists():
            temporary = self._folder / f".{name}.tmp"
            temporary.write_bytes(body)
            os.replace(temporary, target)
        index = self._folder / "index.jsonl"
        row = json.dumps(asdict(item), ensure_ascii=False) + "\n"
        if index.exists() and not index.read_bytes().endswith(b"\n") and index.stat().st_size:
            row = "\n" + row  # a torn last line is closed off, not extended
        with index.open("ab") as handle:
            handle.write(row.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())

    # ---- SEC EDGAR ------------------------------------------------------------------------

    def company_search(self, query: str) -> EdgarResult | Refused:
        """Up to 20 companies whose ticker equals, or whose name contains, the query."""
        if not 1 <= len(query) <= 100:
            return Refused("the query must be 1 to 100 characters")
        got = self.fetch_page(TICKERS_URL, tool="sec_company_search")
        if isinstance(got, Refused):
            return got
        entries = _ticker_entries(self._json(got))
        if not entries:
            return _unreadable(got)
        needle = query.casefold()
        found = [
            {"cik": f"{cik:010d}", "ticker": ticker, "name": name}
            for cik, ticker, name in entries
            if ticker.casefold() == needle or needle in name.casefold()
        ][:MAX_MATCHES]
        lines = [f"{item['cik']} {item['ticker']} {item['name']}" for item in found]
        head = f"{len(found)} match(es) for the query; the list is retained as {got.source_id}."
        summary = "\n".join([head if found else f"No company matched. {head}", *lines])
        return EdgarResult(got.source_id, neutralise(summary), tuple(found))

    def filing_list(self, cik: str) -> EdgarResult | Refused:
        """The company's recent filings from its submissions document."""
        if not _CIK.fullmatch(cik):
            return Refused("the cik must be 1 to 10 digits")
        url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
        got = self.fetch_page(url, tool="sec_filing_list")
        if isinstance(got, Refused):
            return got
        lines = _filing_lines(self._json(got), self._cutoff)
        if not lines:
            return _unreadable(got)
        head = f"Filings listed (first {MAX_LISTED}) from {got.source_id}: form, date, accession"
        return EdgarResult(got.source_id, neutralise("\n".join([head, *lines])))

    def concept_facts(self, cik: str, tag: str, taxonomy: str = "us-gaap") -> EdgarResult | Refused:
        """One XBRL concept's facts for a company."""
        if not _CIK.fullmatch(cik):
            return Refused("the cik must be 1 to 10 digits")
        if taxonomy not in TAXONOMIES:
            return Refused(f"the taxonomy must be one of {', '.join(TAXONOMIES)}")
        if not _TAG.fullmatch(tag):
            return Refused("the tag must be a letter then letters, digits, _ or -, 120 at most")
        url = (
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{int(cik):010d}/{taxonomy}/{tag}.json"
        )
        got = self.fetch_page(url, tool="sec_concept_facts")
        if isinstance(got, Refused):
            return got
        lines = _fact_lines(self._json(got), self._cutoff)
        if not lines:
            return _unreadable(got)
        head = f"Latest {MAX_LISTED} facts, retained as {got.source_id}"
        return EdgarResult(got.source_id, neutralise("\n".join([head, *lines])))

    def _json(self, item: Retained) -> object:
        raw = (self._folder / f"{item.sha256}.json").read_bytes()
        try:
            return json.loads(_decode(raw, item.content_type))
        except (ValueError, RecursionError):
            return None  # not JSON: the caller reports the unexpected shape


def _unreadable(item: Retained) -> EdgarResult:
    return EdgarResult(
        item.source_id,
        f"The expected fields were not found; the answer is retained as {item.source_id}: "
        f"{_READ_IT}.",
    )


def _ticker_entries(doc: object) -> list[tuple[int, str, str]]:
    values = list(doc.values()) if isinstance(doc, dict) else doc
    entries: list[tuple[int, str, str]] = []
    for value in values if isinstance(values, list) else []:
        if not isinstance(value, dict):
            continue
        cik, ticker, name = value.get("cik_str"), value.get("ticker"), value.get("title")
        if type(cik) is int and 0 <= cik <= 9_999_999_999 and isinstance(ticker, str):
            entries.append((cik, ticker, name if isinstance(name, str) else ""))
    return entries


def _after_cutoff(stated: object, cutoff: date) -> str:
    found = _iso_date(stated)
    return (
        " [after the cutoff: a later event, not a source of figures]"
        if found and found > cutoff
        else ""
    )


def _filing_lines(doc: object, cutoff: date) -> list[str]:
    filings = doc.get("filings") if isinstance(doc, dict) else None
    recent = filings.get("recent") if isinstance(filings, dict) else None
    if not isinstance(recent, dict):
        return []
    columns = [recent.get(key) for key in ("form", "filingDate", "accessionNumber")]
    if not all(isinstance(column, list) for column in columns):
        return []
    return [
        f"{form} {filed} {accession}{_after_cutoff(filed, cutoff)}"
        for form, filed, accession in list(zip(*columns, strict=False))[:MAX_LISTED]
    ]


def _fact_lines(doc: object, cutoff: date) -> list[str]:
    units = doc.get("units") if isinstance(doc, dict) else None
    if not isinstance(units, dict):
        return []
    facts: list[tuple[str, dict[str, Any], str]] = []
    for unit, rows in units.items():
        for row in rows if isinstance(rows, list) else []:
            if isinstance(row, dict) and _iso_date(row.get("end")) and "val" in row:
                facts.append((str(row["end"]), row, str(unit)))
    facts.sort(key=lambda fact: (fact[0], str(fact[1].get("filed", ""))))
    lines = []
    for _end, row, unit in facts[-MAX_LISTED:]:
        parts = [
            f"{key}={row[key]}" for key in ("end", "val", "form", "fy", "fp", "filed") if key in row
        ]
        marker = _after_cutoff(row.get("filed", row["end"]), cutoff)
        lines.append(f"{unit} " + " ".join(parts) + marker)
    return lines
