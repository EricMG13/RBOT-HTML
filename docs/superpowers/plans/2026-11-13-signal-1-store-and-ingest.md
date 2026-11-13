# Signal slice 1: store and ingest — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A command-line Signal that stores users and sources in SQLite, fetches approved feeds safely, folds duplicate stories and reports each source's health.

**Architecture:** A new package `src/deploy_workflow/signal/` of small modules with one job each: `store` (SQLite), `feeds` (parse), `fetch` (network rules), `fold` (duplicate keys), `ingest` (one pass over due sources, health), `cli` (commands). No HTTP server and no AI in this slice; slices 2 to 6 of the spec add them on this store.

**Tech Stack:** Python 3.13 standard library only (`sqlite3` with FTS5, `urllib.request`, `xml.etree.ElementTree`, `html.parser`, `ipaddress`, `argparse`), pytest, hypothesis.

**Spec:** `docs/superpowers/specs/2026-11-13-signal-design.md` (sections 5.2, 5.3, 6, 7, 9 step 1; the FTS index of 5.4 is created here, topics are slice 2).

## Global Constraints

- No new dependency. Standard library plus what `pyproject.toml` already pins.
- Database file: `<root>/signal/signal.db`, WAL mode, `PRAGMA foreign_keys=ON`.
- Roles: exactly `reader`, `writer`, `owner`. Source kinds: exactly `regulator`, `news`, `ratings`, `research`. Source states: exactly `proposed`, `approved`, `paused`.
- Nothing is fetched from a source that is not `approved`.
- Fetch rules (as amended after the security audit): `https` only; the host must be a plain DNS name (no IP literals, `%`, userinfo); every address it resolves to must be public, NAT64 and IPv4-compatible IPv6 included; 10 seconds per socket operation and 10 seconds for the whole fetch; at most 3 redirect hops in total, each re-checked, redirect bodies not read; no proxies; 2 MB (2 × 1024 × 1024 bytes) body cap; at most one check per source every 600 seconds; conditional requests with `ETag` and `Last-Modified`.
- A feed with a DTD or entity declaration is rejected.
- Stored per story: source, title, link, published time, summary cut to 300 characters. No article body is fetched or stored.
- Folding: same normalised link, or same normalised title from a different source within 48 hours (controller ruling after review of real feeds: a source never folds into itself by title). Entries whose link does not split cleanly or has no host are skipped at parse time.
- Health states: `healthy`, `quiet` (no item in 7 days), `failing` (last check failed). Items per week for 6 weeks.
- A failing source is recorded with its reason and never stops the pass. No catch-all may hide a failure: every caught error is written to `source_checks.reason`.
- No stub or fake value stands in for real behaviour. Tests that replace the network pass a fetch function and say so in their names (`..._with_recorded_feed`).
- Expected values in tests come from this plan; the implementer does not edit them or weaken a comparison.
- Never write outside `<root>/signal/`. No credential files.
- Before completion: `uv run python tools/quality_gate.py` exits 0; run only `tests/test_signal_*.py` while working.
- Every task report ends with a `Not verified:` line. Ledger line per task: `agent=<name> fix-rounds=<n> gates-first-pass=<y|n|n/a>`.
- PR at most 800 changed lines.

## Review Focus

1. A feed address that redirects to a private address (cloud metadata, `localhost`): the fetch must refuse the redirect hop, not only the first address. Test in Task 3.
2. Generic short titles ("Press release", "Statement") from different sources on the same day: they must not fold into one story. Title folding applies only to normalised titles of 4 or more words. Test in Task 4.
3. A story with no date, or a date in the future: it is stored with the fetch time as its published time, so it cannot sit at the top of "Latest" for ever. Test in Task 2 (parse returns `None`) and Task 5 (ingest substitutes).
4. The same feed served twice (no `ETag` support): the second pass adds no story and no duplicate record. Test in Task 5.
5. A feed whose summary is HTML with markup and entities: stored summary is plain text, whitespace collapsed, at most 300 characters, never cut inside an entity. Test in Task 2.

Known ceiling, not closed in this slice: the address check and the connection are two lookups, so a host that changes its DNS answer between them (DNS rebinding) passes. The owner approving each source by hand is the control. Record this in the `fetch.py` module docstring.

## File structure

| File | Responsibility |
|---|---|
| `src/deploy_workflow/signal/__init__.py` | empty |
| `src/deploy_workflow/signal/__main__.py` | `sys.exit(main())` |
| `src/deploy_workflow/signal/store.py` | schema, migrations, users, sources, stories, checks |
| `src/deploy_workflow/signal/feeds.py` | bytes of RSS 2.0 or Atom to entries |
| `src/deploy_workflow/signal/fetch.py` | address rule, conditional GET, size and time limits |
| `src/deploy_workflow/signal/fold.py` | link and title normalisation |
| `src/deploy_workflow/signal/ingest.py` | one pass over due sources; health |
| `src/deploy_workflow/signal/cli.py` | `users`, `sources`, `ingest`, `stories` commands |
| `tests/test_signal_store.py`, `_feeds.py`, `_fetch.py`, `_fold.py`, `_ingest.py`, `_cli.py` | one test file per module |

---

### Task 1: Store

**Files:**
- Create: `src/deploy_workflow/signal/__init__.py`, `src/deploy_workflow/signal/store.py`
- Test: `tests/test_signal_store.py`

**Interfaces:**
- Produces:
  - `open_db(root: Path) -> sqlite3.Connection` — creates `<root>/signal/signal.db`, applies migrations, `row_factory = sqlite3.Row`.
  - `ROLES`, `KINDS`, `STATES`: tuples of the exact strings in Global Constraints.
  - `add_user(db, name: str, role: str) -> int`; `role_of(db, name: str) -> str` (unknown name returns `"reader"`).
  - `propose_source(db, name: str, kind: str, url: str, proposed_by: str) -> int`
  - `set_source_state(db, source_id: int, state: str) -> None`
  - `sources(db, state: str | None = None) -> list[sqlite3.Row]`
  - `@dataclass(frozen=True) class Check: at: datetime; ok: bool; reason: str; etag: str | None; modified: str | None; new_stories: int` and `record_check(db, source_id: int, check: Check) -> None`
  - `last_check(db, source_id: int) -> sqlite3.Row | None`
  - `StoreError(ValueError)` for an invalid role, kind, state, empty name or duplicate.
- Tables in migration 1: `meta(key, value)` holding `schema_version`; `users(id, name UNIQUE, role)`; `sources(id, name, kind, url UNIQUE, state, proposed_by, created_at)`; `source_checks(id, source_id, at, ok, reason, etag, modified, new_stories)`; `stories(id, source_id, title, link, link_key, title_key, published_at, fetched_at, summary, UNIQUE(source_id, link_key))`; `story_duplicates(story_id, duplicate_source_id, link, seen_at, UNIQUE(story_id, duplicate_source_id, link))`; `stories_fts` (FTS5 over `title`, `summary`, content table `stories`, kept in step by triggers). All times stored as UTC ISO-8601 text.

- [ ] **Step 1: Write the failing tests**

```python
def test_open_db_creates_file_in_wal_mode(tmp_path):
    db = open_db(tmp_path)
    assert (tmp_path / "signal" / "signal.db").is_file()
    assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1

def test_open_db_twice_keeps_data(tmp_path):
    add_user(open_db(tmp_path), "A. Kovac", "writer")
    assert role_of(open_db(tmp_path), "A. Kovac") == "writer"

def test_unknown_name_is_a_reader(tmp_path):
    assert role_of(open_db(tmp_path), "nobody") == "reader"

@pytest.mark.parametrize("role", ["admin", "", "Writer"])
def test_invalid_role_is_refused(tmp_path, role):
    with pytest.raises(StoreError):
        add_user(open_db(tmp_path), "X", role)

def test_proposed_source_is_not_approved(tmp_path):
    db = open_db(tmp_path)
    sid = propose_source(db, "Authority", "regulator", "https://example.org/feed", "A. Kovac")
    assert [r["id"] for r in sources(db, "proposed")] == [sid]
    assert sources(db, "approved") == []
    set_source_state(db, sid, "approved")
    assert [r["id"] for r in sources(db, "approved")] == [sid]

def test_same_url_cannot_be_proposed_twice(tmp_path):
    db = open_db(tmp_path)
    propose_source(db, "A", "news", "https://example.org/feed", "x")
    with pytest.raises(StoreError):
        propose_source(db, "B", "news", "https://example.org/feed", "y")

def test_fts_finds_a_story_by_title_word(tmp_path):
    db = open_db(tmp_path)
    sid = propose_source(db, "A", "news", "https://example.org/feed", "x")
    db.execute("INSERT INTO stories(source_id,title,link,link_key,title_key,published_at,fetched_at,summary)"
               " VALUES(?,?,?,?,?,?,?,?)",
               (sid, "Wholesale access remedy", "https://e.org/1", "e.org/1", "wholesale access remedy",
                "2026-11-13T09:00:00+00:00", "2026-11-13T09:05:00+00:00", ""))
    hits = db.execute("SELECT rowid FROM stories_fts WHERE stories_fts MATCH 'remedy'").fetchall()
    assert len(hits) == 1
```

- [ ] **Step 2: Run** `uv run pytest tests/test_signal_store.py -q` — expected: collection error, `deploy_workflow.signal.store` not found.
- [ ] **Step 3: Implement `store.py`** with the interfaces above. Migrations are an ordered list of SQL scripts applied inside one transaction each, from `meta.schema_version` upward; later slices append to the list.
- [ ] **Step 4: Run** the same command — expected: all pass.
- [ ] **Step 5: Commit** `feat(signal): SQLite store for users, sources and stories`

### Task 2: Feed parsing

**Files:**
- Create: `src/deploy_workflow/signal/feeds.py`
- Test: `tests/test_signal_feeds.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Entry: title: str; link: str; published: datetime | None; summary: str`
  - `parse_feed(body: bytes) -> list[Entry]` — RSS 2.0 (`channel/item`) and Atom (`entry`, namespace `http://www.w3.org/2005/Atom`).
  - `FeedError(ValueError)` — message is shown to the owner, so plain words.
  - `SUMMARY_LIMIT = 300`

Rules the tests pin: body containing `<!DOCTYPE` or `<!ENTITY` (any case) raises `FeedError("feed declares a DTD or entities")` before parsing; unparseable XML or a root that is neither `rss` nor Atom `feed` raises `FeedError`; an entry with an empty title or a link that is not `http`/`https` is skipped; Atom link is the `href` of the `link` with `rel` absent or `alternate`; RSS date via `email.utils.parsedate_to_datetime`, Atom date from `published` else `updated` via `datetime.fromisoformat`; an unparseable or missing date gives `None`; dates are returned in UTC; summary comes from RSS `description` or Atom `summary`, tags removed with `html.parser.HTMLParser`, entities decoded, whitespace collapsed to single spaces, cut to 300 characters on a word boundary with no trailing space.

- [ ] **Step 1: Write the failing tests**

```python
RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Authority opens review</title><link>https://example.org/a</link>
<pubDate>Fri, 13 Nov 2026 09:00:00 +0100</pubDate>
<description>&lt;p&gt;Phase&amp;nbsp;two   begins &amp;amp; ends.&lt;/p&gt;</description></item>
<item><title></title><link>https://example.org/b</link></item>
<item><title>Bad link</title><link>javascript:alert(1)</link></item>
<item><title>No date</title><link>https://example.org/c</link></item>
</channel></rss>"""

ATOM = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Rating action</title>
<link rel="self" href="https://example.org/self"/><link href="https://example.org/r"/>
<updated>2026-11-12T18:30:00Z</updated><summary>Downgrade.</summary></entry></feed>"""

def test_rss_entries():
    got = parse_feed(RSS)
    assert [e.title for e in got] == ["Authority opens review", "No date"]
    assert got[0].link == "https://example.org/a"
    assert got[0].published == datetime(2026, 11, 13, 8, 0, tzinfo=UTC)
    assert got[0].summary == "Phase two begins & ends."   # the non-breaking space collapses too
    assert got[1].published is None

def test_atom_entry():
    (e,) = parse_feed(ATOM)
    assert (e.title, e.link, e.summary) == ("Rating action", "https://example.org/r", "Downgrade.")
    assert e.published == datetime(2026, 11, 12, 18, 30, tzinfo=UTC)

def test_summary_is_cut_to_300_on_a_word_boundary():
    body = RSS.replace(b"&lt;p&gt;Phase&amp;nbsp;two   begins &amp;amp; ends.&lt;/p&gt;", b"word " * 100)
    s = parse_feed(body)[0].summary
    assert len(s) <= 300 and s.endswith("word") and s == " ".join(["word"] * 60)

@pytest.mark.parametrize("body", [
    b'<?xml version="1.0"?><!DOCTYPE rss [<!ENTITY a "b">]><rss/>',
    b'<!doctype rss><rss/>',
])
def test_dtd_or_entities_are_refused(body):
    with pytest.raises(FeedError, match="DTD or entities"):
        parse_feed(body)

@pytest.mark.parametrize("body", [b"not xml", b"<html><body/></html>", b""])
def test_non_feeds_are_refused(body):
    with pytest.raises(FeedError):
        parse_feed(body)
```

- [ ] **Step 2: Run** `uv run pytest tests/test_signal_feeds.py -q` — expected: import error.
- [ ] **Step 3: Implement `feeds.py`.**
- [ ] **Step 4: Run** — expected: all pass.
- [ ] **Step 5: Commit** `feat(signal): parse RSS 2.0 and Atom feeds`

### Task 3: Fetch rules

**Files:**
- Create: `src/deploy_workflow/signal/fetch.py`
- Test: `tests/test_signal_fetch.py`

**Interfaces:**
- Produces:
  - `TIMEOUT_SECONDS = 10`; `MAX_BYTES = 2 * 1024 * 1024`; `MAX_REDIRECTS = 3`
  - `FetchRefused(ValueError)` — message names the rule broken.
  - `check_address(url: str, resolve: Callable[[str], Iterable[str]] = _resolve) -> None` — raises `FetchRefused` unless the scheme is `https`, there is a host, and every resolved address has `ipaddress.ip_address(a).is_global`. `_resolve` uses `socket.getaddrinfo`.
  - `@dataclass(frozen=True) class Fetched: body: bytes | None; etag: str | None; modified: str | None` — `body is None` means HTTP 304.
  - `fetch(url: str, etag: str | None, modified: str | None, *, resolve=_resolve, opener: Callable[..., Any] | None = None) -> Fetched` — sends `If-None-Match` / `If-Modified-Since` when given; a redirect handler calls `check_address` on every hop and refuses after `MAX_REDIRECTS`; reads at most `MAX_BYTES + 1` bytes and raises `FetchRefused("feed is larger than 2 MB")` if the extra byte arrives; network errors and non-200/304 statuses raise `FetchRefused` with the status or error text.

- [ ] **Step 1: Write the failing tests** (no network: `resolve` and a local `http.server` on `127.0.0.1` driven through an injected opener for the size and conditional cases)

```python
PUBLIC = lambda host: ["93.184.216.34"]

@pytest.mark.parametrize("url", ["http://example.org/feed", "ftp://example.org/f", "https:///nohost", "file:///etc/passwd"])
def test_only_https_with_a_host(url):
    with pytest.raises(FetchRefused):
        check_address(url, resolve=PUBLIC)

@pytest.mark.parametrize("addr", ["127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "::1", "fc00::1", "0.0.0.0"])
def test_non_public_addresses_are_refused(addr):
    with pytest.raises(FetchRefused, match="public"):
        check_address("https://feeds.example.org/x", resolve=lambda h: [addr])

def test_one_private_address_among_public_is_refused():
    with pytest.raises(FetchRefused):
        check_address("https://feeds.example.org/x", resolve=lambda h: ["93.184.216.34", "10.0.0.1"])

def test_public_https_passes():
    check_address("https://feeds.example.org/x", resolve=PUBLIC)

def test_redirect_to_a_private_address_is_refused(redirecting_opener):
    # opener answers 302 Location: https://internal.example/ ; resolve maps internal.example -> 10.0.0.1
    with pytest.raises(FetchRefused, match="public"):
        fetch("https://feeds.example.org/x", None, None, resolve=_map, opener=redirecting_opener)

def test_body_over_two_megabytes_is_refused(big_opener):
    with pytest.raises(FetchRefused, match="2 MB"):
        fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=big_opener)

def test_conditional_headers_are_sent_and_304_returns_no_body(recording_opener):
    got = fetch("https://feeds.example.org/x", '"abc"', "Fri, 13 Nov 2026 09:00:00 GMT", resolve=PUBLIC, opener=recording_opener)
    assert recording_opener.headers["If-none-match"] == '"abc"'
    assert recording_opener.headers["If-modified-since"] == "Fri, 13 Nov 2026 09:00:00 GMT"
    assert got == Fetched(None, '"abc"', "Fri, 13 Nov 2026 09:00:00 GMT")

def test_200_returns_body_and_validators(recording_opener_200):
    got = fetch("https://feeds.example.org/x", None, None, resolve=PUBLIC, opener=recording_opener_200)
    assert (got.body, got.etag) == (b"<rss/>", '"v2"')
```

The `opener` fixtures are small callables defined in the test file that take a `urllib.request.Request` and a timeout and return an object with `status`, `headers` and `read(n)`; the redirect fixture exercises the real redirect handler by building the opener with `urllib.request.build_opener(fetch.redirect_handler(resolve), <fake HTTPS handler>)`. `fetch.py` therefore also exposes `redirect_handler(resolve) -> urllib.request.HTTPRedirectHandler`.

- [ ] **Step 2: Run** `uv run pytest tests/test_signal_fetch.py -q` — expected: import error.
- [ ] **Step 3: Implement `fetch.py`**, with the DNS-rebinding ceiling in the module docstring.
- [ ] **Step 4: Run** — expected: all pass.
- [ ] **Step 5: Commit** `feat(signal): fetch feeds over https from public addresses only`

### Task 4: Folding

**Files:**
- Create: `src/deploy_workflow/signal/fold.py`
- Modify: `src/deploy_workflow/signal/store.py` (add `add_story`)
- Test: `tests/test_signal_fold.py`

**Interfaces:**
- Consumes: `store.open_db`, `feeds.Entry`.
- Produces:
  - `link_key(link: str) -> str` — lower-case host without a leading `www.`, plus path without a trailing `/`, plus the query with parameters named `utm_*`, `fbclid`, `gclid` removed and the rest sorted; no scheme, no fragment.
  - `title_key(title: str) -> str` — `casefold()`, every run of non-alphanumeric characters to one space, stripped.
  - `TITLE_WINDOW = timedelta(hours=48)`; `MIN_TITLE_WORDS = 4`
  - `store.add_story(db, source_id: int, entry: Entry, fetched_at: datetime) -> Literal["new", "duplicate", "seen"]` — `seen`: this source already has this `link_key` (nothing written). `duplicate`: another story has the same `link_key`, or the same `title_key` with `MIN_TITLE_WORDS` or more words and a published time within `TITLE_WINDOW`; a `story_duplicates` row is written against the earliest such story. `new`: a `stories` row is written; `published_at` is `entry.published`, or `fetched_at` when that is `None` or later than `fetched_at`.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("a,b", [
    ("https://www.Example.org/news/1/", "http://example.org/news/1"),
    ("https://example.org/n?id=7&utm_source=x&fbclid=y", "https://example.org/n?id=7"),
    ("https://example.org/n?b=2&a=1#top", "https://example.org/n?a=1&b=2"),
])
def test_link_key_equates(a, b):
    assert link_key(a) == link_key(b)

def test_link_key_keeps_meaningful_query():
    assert link_key("https://example.org/n?id=7") != link_key("https://example.org/n?id=8")

def test_title_key():
    assert title_key("  Authority opens  in-depth review — Northwave! ") == "authority opens in depth review northwave"

@given(st.text())
def test_title_key_is_idempotent(t):
    assert title_key(title_key(t)) == title_key(t)

def test_same_link_from_two_sources_folds(db2):   # db2: fixture with sources 1 and 2
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    assert add_story(db2, 1, Entry("A long enough headline here", "https://e.org/1", t, ""), t) == "new"
    assert add_story(db2, 2, Entry("Different words entirely now", "https://www.e.org/1/", t, ""), t) == "duplicate"
    assert db2.execute("SELECT count(*) FROM stories").fetchone()[0] == 1
    assert db2.execute("SELECT count(*) FROM story_duplicates").fetchone()[0] == 1

def test_same_title_within_48_hours_folds_and_after_does_not(db2):
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_story(db2, 1, Entry("Authority opens in-depth review", "https://a.org/1", t, ""), t)
    near, far = t + timedelta(hours=47), t + timedelta(hours=49)
    assert add_story(db2, 2, Entry("Authority opens in depth review", "https://b.org/9", near, ""), near) == "duplicate"
    assert add_story(db2, 2, Entry("Authority opens in depth review", "https://b.org/10", far, ""), far) == "new"

def test_short_generic_titles_do_not_fold(db2):
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_story(db2, 1, Entry("Press release", "https://a.org/1", t, ""), t)
    assert add_story(db2, 2, Entry("Press release", "https://b.org/1", t, ""), t) == "new"

def test_same_source_same_link_is_seen_and_writes_nothing(db2):
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    e = Entry("A long enough headline here", "https://e.org/1", t, "")
    add_story(db2, 1, e, t)
    assert add_story(db2, 1, e, t) == "seen"
    assert db2.execute("SELECT count(*) FROM story_duplicates").fetchone()[0] == 0

def test_missing_or_future_date_becomes_fetch_time(db2):
    now = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_story(db2, 1, Entry("No date on this story", "https://e.org/1", None, ""), now)
    add_story(db2, 1, Entry("Future date on this story", "https://e.org/2", now + timedelta(days=400), ""), now)
    got = [r[0] for r in db2.execute("SELECT published_at FROM stories ORDER BY id")]
    assert got == [now.isoformat(), now.isoformat()]
```

- [ ] **Step 2: Run** `uv run pytest tests/test_signal_fold.py -q` — expected: import error.
- [ ] **Step 3: Implement `fold.py` and `store.add_story`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_signal_fold.py tests/test_signal_store.py -q` — expected: all pass.
- [ ] **Step 5: Commit** `feat(signal): fold duplicate stories by link and title`

### Task 5: Ingest pass and source health

**Files:**
- Create: `src/deploy_workflow/signal/ingest.py`
- Test: `tests/test_signal_ingest.py`

**Interfaces:**
- Consumes: `store.sources`, `store.last_check`, `store.record_check`, `store.Check`, `store.add_story`, `feeds.parse_feed`, `feeds.FeedError`, `fetch.fetch`, `fetch.Fetched`, `fetch.FetchRefused`.
- Produces:
  - `MIN_INTERVAL = timedelta(seconds=600)`; `QUIET_AFTER = timedelta(days=7)`; `HEALTH_WEEKS = 6`
  - `FetchFn = Callable[[str, str | None, str | None], Fetched]`
  - `run_due(db, now: datetime, fetch_fn: FetchFn | None = None) -> list[tuple[int, bool, str]]` (`None` means `fetch.fetch`, looked up at call time) — for each `approved` source with no check newer than `now - MIN_INTERVAL`: fetch with the last check's validators, parse, `add_story` each entry, `record_check`. Returns `(source_id, ok, reason)` per source checked. Catches only `FetchRefused` and `FeedError`; their message is the reason. A successful check's reason is `"<n> new"`, counting `add_story` results equal to `"new"`. A 304 is `ok` with reason `"not modified"` and keeps the previous validators.
  - `@dataclass(frozen=True) class Health: state: Literal["healthy", "quiet", "failing", "never checked"]; last_check: datetime | None; last_item: datetime | None; per_week: tuple[int, ...]; reason: str` — `per_week` has `HEALTH_WEEKS` counts, oldest first, of this source's stories by `published_at` in the six 7-day windows ending at `now`.
  - `health(db, source_id: int, now: datetime) -> Health` — `failing` if the last check failed; else `quiet` if no story from this source in `QUIET_AFTER`; else `healthy`.

- [ ] **Step 1: Write the failing tests** (the fetch function is a recorded feed, named so)

```python
NOW = datetime(2026, 11, 13, 9, tzinfo=UTC)

def recorded(body, etag='"v1"'):
    calls = []
    def fn(url, etag_in, modified_in):
        calls.append((url, etag_in, modified_in))
        return Fetched(body, etag, None)
    fn.calls = calls
    return fn

def test_only_approved_sources_are_fetched_with_recorded_feed(db):
    a = propose_source(db, "A", "news", "https://a.org/f", "x"); set_source_state(db, a, "approved")
    propose_source(db, "B", "news", "https://b.org/f", "x")            # stays proposed
    p = propose_source(db, "P", "news", "https://p.org/f", "x"); set_source_state(db, p, "paused")
    fn = recorded(RSS)
    assert run_due(db, NOW, fn) == [(a, True, "2 new")]
    assert [c[0] for c in fn.calls] == ["https://a.org/f"]

def test_source_is_not_checked_again_within_600_seconds_with_recorded_feed(db_a):
    fn = recorded(RSS)
    run_due(db_a, NOW, fn)
    assert run_due(db_a, NOW + timedelta(seconds=599), fn) == []
    assert len(run_due(db_a, NOW + timedelta(seconds=600), fn)) == 1

def test_second_pass_sends_validators_and_adds_nothing_with_recorded_feed(db_a):
    fn = recorded(RSS)
    run_due(db_a, NOW, fn)
    assert run_due(db_a, NOW + timedelta(hours=1), fn)[0][2] == "0 new"
    assert fn.calls[1][1] == '"v1"'
    assert db_a.execute("SELECT count(*) FROM stories").fetchone()[0] == 2
    assert db_a.execute("SELECT count(*) FROM story_duplicates").fetchone()[0] == 0

def test_failing_source_is_recorded_and_others_still_run(db):
    bad = propose_source(db, "Bad", "news", "https://bad.org/f", "x"); set_source_state(db, bad, "approved")
    good = propose_source(db, "Good", "news", "https://good.org/f", "x"); set_source_state(db, good, "approved")
    def fn(url, e, m):
        if "bad" in url:
            raise FetchRefused("feed is larger than 2 MB")
        return Fetched(RSS, None, None)
    assert run_due(db, NOW, fn) == [(bad, False, "feed is larger than 2 MB"), (good, True, "2 new")]
    assert health(db, bad, NOW).state == "failing"
    assert health(db, bad, NOW).reason == "feed is larger than 2 MB"

def test_unparseable_feed_is_failing_with_the_parser_reason(db_a):
    run_due(db_a, NOW, recorded(b"not xml"))
    assert health(db_a, 1, NOW).state == "failing"

def test_an_unexpected_error_is_not_swallowed(db_a):
    def fn(url, e, m):
        raise RuntimeError("bug")
    with pytest.raises(RuntimeError):
        run_due(db_a, NOW, fn)

def test_health_states_and_weekly_counts(db_a):
    assert health(db_a, 1, NOW).state == "never checked"
    run_due(db_a, NOW, recorded(RSS))          # RSS items: one dated 13 Nov 08:00Z, one undated -> NOW
    h = health(db_a, 1, NOW)
    assert (h.state, h.per_week) == ("healthy", (0, 0, 0, 0, 0, 2))
    later = NOW + timedelta(days=8)
    run_due(db_a, later, recorded(RSS))
    assert health(db_a, 1, later).state == "quiet"
    assert health(db_a, 1, later).per_week == (0, 0, 0, 0, 2, 0)
```

`RSS` is the Task 2 constant, imported from `tests/test_signal_feeds.py`. `db` is `open_db(tmp_path)`; `db_a` adds one approved source with id 1.

- [ ] **Step 2: Run** `uv run pytest tests/test_signal_ingest.py -q` — expected: import error.
- [ ] **Step 3: Implement `ingest.py`.**
- [ ] **Step 4: Run** — expected: all pass.
- [ ] **Step 5: Commit** `feat(signal): ingest pass over due sources and source health`

### Task 6: Command line, package wrapper and records

**Files:**
- Create: `src/deploy_workflow/signal/cli.py`, `src/deploy_workflow/signal/__main__.py`
- Modify: `README.md` (a "Signal" section: the commands below and that the AI pass, pages and login are later slices), `VERIFICATION.md` (one entry: scope, commands run, exit codes, `Not verified:` line)
- Test: `tests/test_signal_cli.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `main(argv: Sequence[str] | None = None) -> int`, run as `python -m deploy_workflow.signal --root <root> <command>`:
  - `users add <name> --role <reader|writer|owner>`
  - `sources propose <name> --kind <kind> --url <url> --by <name>` — runs `check_address` first and refuses a bad address with its reason
  - `sources approve <id>` / `sources pause <id>`
  - `sources list` — one line per source: id, state, health state, last item time, name
  - `ingest` — one `run_due` pass at the current UTC time; prints one line per source checked; exit 0 even when a source fails (the failure is the printed line and the stored reason)
  - `ingest --loop` — a pass every 60 seconds until interrupted
  - `stories [--limit N]` — newest first: published time, source name, title, and `(+N)` when duplicates were folded
  - Exit 2 with a one-line message on `StoreError` or `FetchRefused`; argparse handles usage errors.

- [ ] **Step 1: Write the failing tests**

```python
def run(tmp_path, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = main(["--root", str(tmp_path), *args])
    return code, out.getvalue()

def test_propose_approve_list(tmp_path, monkeypatch):
    monkeypatch.setattr("deploy_workflow.signal.cli.check_address", lambda url: None)
    assert run(tmp_path, "sources", "propose", "Authority", "--kind", "regulator", "--url", "https://a.org/f", "--by", "ak")[0] == 0
    code, out = run(tmp_path, "sources", "list")
    assert code == 0 and "proposed" in out and "never checked" in out and "Authority" in out
    assert run(tmp_path, "sources", "approve", "1")[0] == 0
    assert "approved" in run(tmp_path, "sources", "list")[1]

def test_proposing_a_private_address_is_refused(tmp_path):
    code, out = run(tmp_path, "sources", "propose", "X", "--kind", "news", "--url", "https://127.0.0.1/f", "--by", "ak")
    assert code == 2 and "plain host name" in out
    assert run(tmp_path, "sources", "list")[1].strip() == ""

def test_invalid_role_exits_2(tmp_path):
    assert run(tmp_path, "users", "add", "X", "--role", "admin")[0] == 2

def test_ingest_and_stories_with_recorded_feed(tmp_path, monkeypatch):
    monkeypatch.setattr("deploy_workflow.signal.cli.check_address", lambda url: None)
    monkeypatch.setattr("deploy_workflow.signal.ingest.fetch.fetch", lambda u, e, m: Fetched(RSS, None, None))
    run(tmp_path, "sources", "propose", "Authority", "--kind", "regulator", "--url", "https://a.org/f", "--by", "ak")
    run(tmp_path, "sources", "approve", "1")
    code, out = run(tmp_path, "ingest")
    assert code == 0 and "2 new" in out
    code, out = run(tmp_path, "stories")
    lines = out.splitlines()
    assert len(lines) == 2 and all("Authority" in line for line in lines)   # source name on both
    assert "No date" in out and "Authority opens review" in out
```

`cli.py` imports `check_address` by name (`from deploy_workflow.signal.fetch import check_address`) so the tests can replace it. Argparse choices already reject an invalid `--role` with exit 2; keep the `StoreError` path for names.

- [ ] **Step 2: Run** `uv run pytest tests/test_signal_cli.py -q` — expected: import error.
- [ ] **Step 3: Implement `cli.py` and `__main__.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_signal_store.py tests/test_signal_feeds.py tests/test_signal_fetch.py tests/test_signal_fold.py tests/test_signal_ingest.py tests/test_signal_cli.py -q` — expected: all pass.
- [ ] **Step 5: Run** `uv run python tools/quality_gate.py` — expected: exit 0.
- [ ] **Step 6: Live proof, free, labelled as such.** With the owner's go-ahead for one public regulator feed address of their choice: `propose`, `approve`, `ingest`, `stories`, `sources list`. Paste the commands and output into the `VERIFICATION.md` entry. If no address is supplied, the entry's `Not verified:` line says no real feed was fetched.
- [ ] **Step 7: Update `README.md` and `VERIFICATION.md`; commit** `feat(signal): command line for users, sources, ingest and stories`

---

## Not in this plan (later slices, each its own plan)

Service and feed pages (2); groups, threads, notifications (3); settings pages (4); AI pass and cost control, after the ruling (5); digests (6). The `Start signal.cmd` package wrapper arrives with the service in slice 2, since slice 1 has nothing to keep running for users.
