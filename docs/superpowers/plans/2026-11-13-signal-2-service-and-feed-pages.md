# Signal slice 2: service and feed pages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A running Signal service whose feed page shows stored stories (Latest, For you, Saved, each topic), with search, save and topic following, and keeps itself fresh with a background ingest loop.

**Architecture:** Slice 1's store and ingest stay as they are. This slice adds topics and personal marks to the store, a query module for the feed, an identity seam, a standard-library HTTP service with the run start page's request rules, and a static page (HTML, CSS, JavaScript files, no inline script) that calls a small JSON API and polls for new stories. No AI, no groups or threads, no settings pages.

**Tech Stack:** Python 3.13 standard library (`http.server`, `sqlite3` FTS5, `threading`), plain JavaScript and CSS with the library's brand tokens and fonts, pytest, hypothesis, `node --test` for page logic, the repo's Chrome harness for browser tests.

**Spec:** `docs/superpowers/specs/2026-11-13-signal-design.md` (sections 5.1, 5.2, 5.4, 5.6, 5.11, 7, 9 step 2). Mockup: `docs/design/mockups/signal.html`. Builds on slice 1 (`docs/superpowers/plans/2026-11-13-signal-1-store-and-ingest.md`, PRs 101 and 102).

## Global Constraints

- No new dependency. No build toolchain: the page is hand-written files served as they are.
- One shared instance: `python -m deploy_workflow.signal --root <root> serve --host <address> --port <port>`; `127.0.0.1` by default; a wildcard address (`0.0.0.0`, `::`) is refused.
- Request rules, same as the run start page (`src/deploy_workflow/run_start/service.py` module docstring): `Host` must be exactly the started `<host>:<port>` (plus `localhost:<port>` for `127.0.0.1`), else 403; every non-GET must carry `Origin: http://<Host>`, else 403; a present `Sec-Fetch-Site` other than `same-origin` or `none` is 403 except a top-level navigation; every response carries `Cross-Origin-Resource-Policy: same-origin` and `X-Content-Type-Options: nosniff`; JSON bodies need `Content-Length` and are at most 64 KiB; one request per connection.
- Page policy, stricter than run start: `Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`. No inline script, no inline style attribute, no third-party origin.
- The service serves only its own page files and API. It serves no file from `<root>`.
- All feed and user text is inserted with `textContent` or escaped; never `innerHTML` with data. "Open source" links: `target="_blank" rel="noopener noreferrer"`, and only `http:`/`https:` links are rendered as links.
- Identity is not authentication (spec 5.2): a typed display name in a cookie; the role comes from the `users` table; an unknown name is a `reader`. Everything a user can do in this slice (save, follow, search) is personal and open to readers. No owner or writer action is exposed over HTTP.
- No AI call anywhere. Cards show no AI line, no signal bars, no stage tracker and no rating move; those arrive with slice 5. A card's kind is its source's kind (`regulator`, `news`, `ratings`, `research`).
- Order is by published time, newest first ("Latest"). The "Top" order needs signal strength and group activity and is not in this slice; the page shows no Top/Latest toggle.
- Background loop: one ingest pass every 60 seconds in its own thread with its own database connection; each request uses its own connection. A pass that raises is logged and the loop continues at the next tick; the failure is visible at `/api/status`.
- Design rules (owner, 2026-11-13): each kind of information has its own component; nothing looks lifted from Markdown; no flat grid. The mockup is the reference. Before Task 5 the controller reads the live pages of any component taken from the eight approved libraries and names them in the task brief; none is used from memory. Every view has an empty, a loading and an error state.
- Accessibility: landmarks and labels as in the mockup, full keyboard use, visible focus, text contrast at least 4.5:1, `prefers-reduced-motion` respected, no information by colour alone.
- No stub or fake value stands in for real behaviour. No catch-all hides a failure. Tests that replace the network or the clock say so in their names. Expected values in tests come from this plan; the implementer does not edit them or weaken a comparison.
- No suppression comments (`noqa`, `type: ignore`, `nosec`, `pragma: no cover`).
- Gates: `uv run pytest tests/test_signal_*.py -q` (quote the glob), `node --test src/deploy_workflow/signal/web/render.test.cjs`, `uv run python tools/quality_gate.py`; all exit 0. Browser tests carry `pytest.mark.browser` and follow `tests/test_library_page_browser.py`'s harness.
- Every task report ends with `Not verified:`. Ledger line per task: `agent=<name> fix-rounds=<n> gates-first-pass=<y|n|n/a>`.
- Two pull requests, planned from the start: 2a = Tasks 1 to 4 (store, queries, identity, service); 2b = Tasks 5 to 7 (page, browser proof, packaging and records). Each should stay near the 800-line guideline; say so in the report if a task alone exceeds 400.

## Review Focus

1. Search text typed by a user reaches SQLite's FTS5 query language: `"`, `*`, `NEAR`, `AND`, a lone `-`, unbalanced quotes or an empty string must return results or nothing, never an error and never operator behaviour. Test in Task 2.
2. A story title or summary containing markup (`<img onerror=…>`, `</script>`) or a `javascript:` link must render as text and never as a link or element. Tests in Task 5 (render logic) and Task 6 (real browser).
3. A display name with markup, control characters, 500 characters, or only spaces: stored and shown safely, cut to 60 characters, empty refused. Test in Task 3.
4. A page on another site must not be able to save, follow or set a name through a user's browser: a POST with a foreign or missing `Origin` changes nothing. Test in Task 4.
5. The ingest loop and page requests write the same database at once: a save during a pass must succeed, and a pass that raises must not stop later passes. Test in Task 4.

## File structure

| File | Responsibility |
|---|---|
| `src/deploy_workflow/signal/store.py` (modify) | migration 2: `topics`, `topic_stories`, `topic_follows`, `saves`; pass time in `meta` |
| `src/deploy_workflow/signal/topics.py` | topic rules: create, match stories, follow |
| `src/deploy_workflow/signal/feedview.py` | read side: feed pages, counts, search, save |
| `src/deploy_workflow/signal/identity.py` | `current_user`, name cleaning, cookie value |
| `src/deploy_workflow/signal/service.py` | HTTP server, request rules, routes, loop thread |
| `src/deploy_workflow/signal/cli.py` (modify) | `topics add|list`, `serve` |
| `src/deploy_workflow/signal/ingest.py` (modify) | record pass time; match new stories to topics |
| `src/deploy_workflow/signal/web/index.html`, `signal.css`, `signal.js`, `render.js`, `render.test.cjs` | the page; `render.js` is pure functions from JSON to DOM |
| `tests/test_signal_topics.py`, `_feedview.py`, `_identity.py`, `_service.py`, `_page_browser.py` | one test file per unit |
| `apps/issuer-library/packaging/runtime.py`, `build.py` (modify) | `Start signal.cmd`, ship the page files |
| `src/deploy_workflow/run_start/service.py`, `docs/templates/context-form.html` (modify) | rail link to Signal when configured |

---

### Task 1: Topics and personal marks in the store

**Files:** modify `store.py`, `ingest.py`, `cli.py`; create `topics.py`; tests `tests/test_signal_topics.py`, additions to `tests/test_signal_cli.py`.

**Interfaces:**
- Consumes: slice 1 `open_db`, `StoreError`, `add_story`, `run_due`, `KINDS`, the `stories_fts` index.
- Produces:
  - Migration 2 (appended to `MIGRATIONS`; migration 1 is not edited): `topics(id, name UNIQUE, keywords, kinds, created_by, created_at)`; `topic_stories(topic_id, story_id, UNIQUE(topic_id, story_id))`; `topic_follows(user_name, topic_id, UNIQUE(user_name, topic_id))`; `saves(user_name, story_id, saved_at, UNIQUE(user_name, story_id))`.
  - `topics.add_topic(db, name: str, keywords: Sequence[str], kinds: Sequence[str], created_by: str) -> int` — at least one keyword; each keyword 1 to 60 characters after stripping; `kinds` empty means every kind, else each in `KINDS`; `StoreError` otherwise. Matches all existing stories before returning.
  - `topics.match_story(db, story_id: int) -> list[int]` — topic ids whose rule the story meets (any keyword found as a phrase in title or summary, case-insensitive, via the FTS index; and the story's source kind allowed); writes `topic_stories`; idempotent.
  - `topics.follow(db, user_name: str, topic_id: int) -> None`, `topics.unfollow(...) -> None` (both idempotent; unknown topic is `StoreError`), `topics.list_topics(db, user_name: str) -> list[sqlite3.Row]` with columns `id, name, following (0/1), stories (count)`.
  - `store.set_meta(db, key: str, value: str) -> None`, `store.get_meta(db, key: str) -> str | None`.
  - `ingest.run_due` calls `topics.match_story` for each story `add_story` reports as `"new"`, and sets meta `last_pass_at` to `now` (UTC ISO text) at the end of every pass, including a pass with nothing due.
  - CLI: `topics add <name> --keywords "<a>,<b>" [--kinds regulator,news] --by <name>`; `topics list` (id, story count, name).
- A keyword is passed to FTS5 as a quoted phrase with embedded `"` doubled; this helper is `topics.fts_phrase(text: str) -> str` and Task 2 reuses it.

- [ ] **Step 1: Write the failing tests**

```python
def test_topic_matches_existing_and_later_stories(db_two_sources):   # source 1 regulator, source 2 news
    t0 = datetime(2026, 11, 13, 9, tzinfo=UTC)
    add_story(db_two_sources, 1, Entry("Authority opens merger review", "https://a.org/1", t0, "wholesale access remedy"), t0)
    tid = add_topic(db_two_sources, "Competition", ["merger review", "remedy"], [], "ak")
    assert rows(db_two_sources, "SELECT story_id FROM topic_stories WHERE topic_id=?", tid) == [(1,)]
    add_story(db_two_sources, 2, Entry("Operator plans merger", "https://b.org/1", t0, ""), t0)
    assert match_story(db_two_sources, 2) == []                      # "merger" alone is not the phrase "merger review"
    add_story(db_two_sources, 2, Entry("Second MERGER REVIEW opened", "https://b.org/2", t0, ""), t0)
    assert match_story(db_two_sources, 3) == [tid]
    assert match_story(db_two_sources, 3) == [tid]                   # idempotent
    assert count(db_two_sources, "topic_stories") == 2

def test_topic_kind_filter(db_two_sources):
    t0 = datetime(2026, 11, 13, 9, tzinfo=UTC)
    tid = add_topic(db_two_sources, "Reg only", ["review"], ["regulator"], "ak")
    add_story(db_two_sources, 2, Entry("News review of the year", "https://b.org/1", t0, ""), t0)
    add_story(db_two_sources, 1, Entry("Regulator review opens", "https://a.org/1", t0, ""), t0)
    assert match_story(db_two_sources, 1) == [] and match_story(db_two_sources, 2) == [tid]

@pytest.mark.parametrize("keywords,kinds", [([], []), ([" "], []), (["x" * 61], []), (["ok"], ["blog"])])
def test_bad_topic_rules_are_refused(db_two_sources, keywords, kinds):
    with pytest.raises(StoreError):
        add_topic(db_two_sources, "T", keywords, kinds, "ak")

@pytest.mark.parametrize("keyword", ['say "hello"', "a*", "NEAR", "x AND y", "-", "(", "col:on"])
def test_keywords_with_query_syntax_are_plain_text(db_two_sources, keyword):
    add_topic(db_two_sources, f"T {keyword}", [keyword], [], "ak")   # must not raise

@given(st.text(min_size=1, max_size=60).filter(lambda s: s.strip()))
def test_any_keyword_is_accepted_without_error(keyword):
    with fresh_db() as db:
        add_topic(db, "T", [keyword], [], "ak")

def test_follow_is_personal_and_idempotent(db_two_sources):
    tid = add_topic(db_two_sources, "Competition", ["review"], [], "ak")
    follow(db_two_sources, "ak", tid); follow(db_two_sources, "ak", tid)
    assert [(r["id"], r["following"]) for r in list_topics(db_two_sources, "ak")] == [(tid, 1)]
    assert [(r["id"], r["following"]) for r in list_topics(db_two_sources, "ml")] == [(tid, 0)]
    unfollow(db_two_sources, "ak", tid); unfollow(db_two_sources, "ak", tid)
    assert list_topics(db_two_sources, "ak")[0]["following"] == 0
    with pytest.raises(StoreError):
        follow(db_two_sources, "ak", 999)

def test_pass_records_its_time_and_matches_new_stories_with_recorded_feed(db_a):   # one approved source, id 1
    tid = add_topic(db_a, "Opens", ["opens review"], [], "ak")
    run_due(db_a, NOW, recorded(RSS))                                # RSS from test_signal_feeds: "Authority opens review"
    assert get_meta(db_a, "last_pass_at") == NOW.isoformat()
    assert count(db_a, "topic_stories") == 1
    run_due(db_a, NOW + timedelta(seconds=30), recorded(RSS))        # nothing due
    assert get_meta(db_a, "last_pass_at") == (NOW + timedelta(seconds=30)).isoformat()

def test_a_slice_1_database_gains_the_new_tables(tmp_path):
    db = open_db(tmp_path)
    assert db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "2"
```

Add to `tests/test_signal_cli.py`: `topics add Competition --keywords "merger review,remedy" --by ak` exits 0 and `topics list` prints one line containing `Competition`; `topics add X --keywords "" --by ak` exits 2 with one line.

- [ ] **Step 2:** `uv run pytest tests/test_signal_topics.py -q` — expected: import error.
- [ ] **Step 3:** Implement. `fts_phrase` wraps in double quotes and doubles embedded quotes; a keyword that FTS tokenises to nothing (for example `-` or `(`) matches no story and is not an error.
- [ ] **Step 4:** `uv run pytest tests/test_signal_topics.py tests/test_signal_cli.py tests/test_signal_ingest.py tests/test_signal_store.py -q` — all pass.
- [ ] **Step 5:** Commit `feat(signal): topics, follows and saves in the store`.

### Task 2: Feed queries

**Files:** create `src/deploy_workflow/signal/feedview.py`; test `tests/test_signal_feedview.py`.

**Interfaces:**
- Consumes: Task 1 tables and `topics.fts_phrase`.
- Produces:
  - `PAGE = 30`; `MAX_QUERY = 100` (characters).
  - `@dataclass(frozen=True) class Card: id: int; title: str; link: str; summary: str; source: str; kind: str; published_at: str; other_sources: int; saved: bool; topics: tuple[str, ...]`
  - `@dataclass(frozen=True) class Page: cards: tuple[Card, ...]; next_before: str | None` — `next_before` is the cursor for the following page, `None` on the last page.
  - `feed(db, user_name: str, view: str, *, kind: str | None = None, query: str = "", before: str | None = None) -> Page` — `view` is `"latest"`, `"foryou"` (stories in topics the user follows), `"saved"`, or `"topic:<id>"`; `kind` filters by source kind; `query` filters by search text; ordered by `published_at` then `id`, both descending; `before` is an opaque cursor `"<published_at>|<id>"`. `ViewError(ValueError)` for an unknown view, kind, malformed cursor or unknown topic.
  - `new_count(db, user_name: str, view: str, since: str) -> int` — stories in the view with `fetched_at` later than `since`.
  - `save(db, user_name: str, story_id: int) -> None`, `unsave(...) -> None` — idempotent; unknown story is `ViewError`.
  - Search: the query is cut to `MAX_QUERY`, split on whitespace, each term passed as an FTS5 quoted phrase (all terms must match); an empty query means no search filter; a query whose terms all tokenise to nothing returns an empty page.
  - `other_sources` is the number of distinct other sources that carried the story (`COUNT(DISTINCT duplicate_source_id)`).

- [ ] **Step 1: Write the failing tests** (fixture `db_feed`: sources 1 regulator "Authority", 2 news "Wire"; 35 stories from source 1 titled `Story 01`..`Story 35` at one-minute steps ending `2026-11-13T09:35Z`; one story from source 2 "Wire piece on remedy" at `09:36Z`; `Story 35` also carried by source 2 under another link; topic "Remedy" keyword `remedy`)

```python
def test_latest_pages_by_30_newest_first(db_feed):
    first = feed(db_feed, "ak", "latest")
    assert len(first.cards) == 30 and first.cards[0].title == "Wire piece on remedy"
    assert first.cards[1].title == "Story 35" and first.cards[1].other_sources == 1
    second = feed(db_feed, "ak", "latest", before=first.next_before)
    assert [c.title for c in second.cards] == [f"Story {n:02d}" for n in range(6, 0, -1)]
    assert second.next_before is None

def test_kind_filter_and_card_fields(db_feed):
    page = feed(db_feed, "ak", "latest", kind="news")
    (card,) = page.cards
    assert (card.source, card.kind, card.published_at, card.saved, card.topics) == (
        "Wire", "news", "2026-11-13T09:36:00+00:00", False, ("Remedy",))

def test_foryou_is_followed_topics_only(db_feed):
    assert feed(db_feed, "ak", "foryou").cards == ()
    follow(db_feed, "ak", 1)
    assert [c.title for c in feed(db_feed, "ak", "foryou").cards] == ["Wire piece on remedy"]
    assert feed(db_feed, "ml", "foryou").cards == ()

def test_topic_view_and_unknown_topic(db_feed):
    assert len(feed(db_feed, "ak", "topic:1").cards) == 1
    with pytest.raises(ViewError):
        feed(db_feed, "ak", "topic:99")

def test_save_is_personal_idempotent_and_listed(db_feed):
    save(db_feed, "ak", 5); save(db_feed, "ak", 5)
    assert [c.id for c in feed(db_feed, "ak", "saved").cards] == [5]
    assert feed(db_feed, "ml", "saved").cards == ()
    assert next(c for c in feed(db_feed, "ak", "latest", before="2026-11-13T09:06:00+00:00|6").cards if c.id == 5).saved
    unsave(db_feed, "ak", 5); unsave(db_feed, "ak", 5)
    assert feed(db_feed, "ak", "saved").cards == ()
    with pytest.raises(ViewError):
        save(db_feed, "ak", 9999)

def test_search_matches_all_terms(db_feed):
    assert [c.title for c in feed(db_feed, "ak", "latest", query="wire remedy").cards] == ["Wire piece on remedy"]
    assert feed(db_feed, "ak", "latest", query="wire absent").cards == ()

@pytest.mark.parametrize("query", ['"', 'a"b', "*", "NEAR", "x AND", "-", "(", "title:x", "\x00", "ß" * 300])
def test_search_text_is_never_query_syntax(db_feed, query):
    feed(db_feed, "ak", "latest", query=query)                       # must not raise

@given(st.text(max_size=200))
def test_any_search_text_returns_a_page(query):
    with feed_db() as db:
        assert isinstance(feed(db, "ak", "latest", query=query), Page)

@pytest.mark.parametrize("bad", [dict(view="top"), dict(view="latest", kind="blog"), dict(view="latest", before="x"),
                                 dict(view="topic:abc")])
def test_bad_requests_raise_view_error(db_feed, bad):
    with pytest.raises(ViewError):
        feed(db_feed, "ak", **bad)

def test_new_count(db_feed):                                         # every fixture story fetched at 09:40Z
    assert new_count(db_feed, "ak", "latest", "2026-11-13T09:39:00+00:00") == 36
    assert new_count(db_feed, "ak", "latest", "2026-11-13T09:40:00+00:00") == 0
```

- [ ] **Step 2:** run — import error. **Step 3:** implement (one SQL builder for the four views; no string formatting of user values into SQL). **Step 4:** `uv run pytest tests/test_signal_feedview.py -q` passes. **Step 5:** commit `feat(signal): feed queries, search and saves`.

### Task 3: Identity

**Files:** create `src/deploy_workflow/signal/identity.py`; test `tests/test_signal_identity.py`.

**Interfaces:**
- Produces:
  - `COOKIE = "signal_name"`; `MAX_NAME = 60`
  - `clean_name(raw: str) -> str` — Unicode NFC, control and format characters removed, runs of whitespace to one space, stripped, cut to `MAX_NAME`; `IdentityError(ValueError)` if the result is empty.
  - `@dataclass(frozen=True) class User: name: str; role: str`
  - `current_user(db, cookie_header: str | None) -> User | None` — `None` when there is no usable cookie; else the cleaned name and `store.role_of` (unknown name: `reader`).
  - `cookie_for(name: str) -> str` — the `Set-Cookie` value: `signal_name=<percent-encoded name>; Path=/; Max-Age=31536000; SameSite=Strict; HttpOnly`.
- This module is the whole seam the landing-page project replaces.

- [ ] **Step 1: tests**

```python
@pytest.mark.parametrize("raw,want", [
    ("  A.  Kovac ", "A. Kovac"), ("A\tK\n", "A K"), ("x​y\x00z", "xyz"),
    ("<b>Eve</b>", "<b>Eve</b>"), ("é" * 500, "é" * 60), ("é", "é"),
])
def test_clean_name(raw, want):
    assert clean_name(raw) == want

@pytest.mark.parametrize("raw", ["", "   ", "\x00​", "\n\t"])
def test_empty_names_are_refused(raw):
    with pytest.raises(IdentityError):
        clean_name(raw)

def test_cookie_round_trip_and_role(db):
    add_user(db, "A. Kovac", "writer")
    header = cookie_for("A. Kovac").split(";")[0]
    assert current_user(db, header) == User("A. Kovac", "writer")
    assert current_user(db, cookie_for("Nobody").split(";")[0]) == User("Nobody", "reader")
    assert current_user(db, None) is None and current_user(db, "other=1") is None
    assert current_user(db, "signal_name=%00%20") is None

def test_cookie_attributes():
    assert cookie_for("A; B").startswith("signal_name=A%3B%20B; ")
    assert all(part in cookie_for("x") for part in ("Path=/", "SameSite=Strict", "HttpOnly", "Max-Age=31536000"))

@given(st.text(max_size=300))
def test_any_cookie_header_is_safe(header):
    with fresh_db() as db:
        user = current_user(db, header)
        assert user is None or (0 < len(user.name) <= 60 and user.role == "reader")
```

- [ ] **Steps 2-5:** run (import error), implement, `uv run pytest tests/test_signal_identity.py -q` passes, commit `feat(signal): display-name identity behind one seam`.

### Task 4: Service

**Files:** create `src/deploy_workflow/signal/service.py`; modify `cli.py` (`serve` command); test `tests/test_signal_service.py`. Read `src/deploy_workflow/run_start/service.py` first: reuse its approach (`_Server`, `_Reply`, `_check_origin`, `_hosts`, `_wildcard`, body limits) by writing the same rules here; do not import from or change that module.

**Interfaces:**
- Consumes: Tasks 1 to 3; `ingest.run_due`.
- Produces:
  - `make_server(root: Path, host: str, port: int) -> ThreadingHTTPServer`; `serve(root: Path, host: str, port: int, *, tick: float = 60.0) -> int` (starts the loop thread, serves until interrupted); `Loop` object with `run_once(now: datetime) -> None` and `last_error: str | None` so tests drive it without sleeping.
  - Routes (JSON answers `application/json; charset=utf-8`; a refusal is `{"error": "<plain sentence>"}`):
    - `GET /` → `web/index.html` with the page policy. `GET /static/<name>` → only `signal.css`, `signal.js`, `render.js`, and the brand files listed in a module constant (`brand.css`, the seven `.woff2` fonts, `symbol.svg`), read from `src/deploy_workflow/signal/web/` and `apps/issuer-library/credit_os/web/`; any other name is 404. `Cache-Control: no-cache`.
    - `GET /api/me` → `{"name": str, "role": str}` or `{"name": null}`. `POST /api/me` body `{"name": str}` → 200 with `Set-Cookie`, or 400 for an empty name.
    - `GET /api/feed?view=&kind=&q=&before=` → `{"cards": [Card fields…], "next_before": str | null}`; 400 with the `ViewError` text; 401 `{"error": "choose a display name first"}` when there is no user.
    - `GET /api/feed/new?view=&since=` → `{"count": int}`.
    - `POST /api/stories/<id>/save`, `DELETE /api/stories/<id>/save` → `{"saved": bool}`; 404 for an unknown story.
    - `GET /api/topics` → `[{"id", "name", "following", "stories"}]`; `POST|DELETE /api/topics/<id>/follow` → `{"following": bool}`; 404 for an unknown topic.
    - `GET /api/status` → `{"last_pass_at": str | null, "sources": {"approved": int, "failing": int}, "loop_error": str | null}`.
    - Anything else 404; other methods 405.
  - Unexpected failure: 500 `{"error": "the service failed; see its log"}`, cause to the log only.
  - CLI: `serve --host <address> --port <port>` (defaults `127.0.0.1`, `8766`); a wildcard host exits 2 with the run start page's message.

- [ ] **Step 1: tests** (fixture `svc`: `make_server(root, "127.0.0.1", 0)` on a thread, with the Task 2 `db_feed` data in `root`; helper `call(method, path, *, body=None, raw=None, origin=<same origin by default>, cookie=None, host=None, headers=None) -> (status, headers, json_or_text)` using `http.client`, no real network beyond loopback)

```python
def test_page_and_static_files_with_strict_policy(svc):
    status, headers, text = svc.call("GET", "/")
    assert status == 200 and "script-src 'self'" in headers["Content-Security-Policy"]
    assert "'unsafe-inline'" not in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff" and headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert svc.call("GET", "/static/signal.js")[0] == 200
    for path in ("/static/../store.py", "/static/store.py", "/static/%2e%2e/cli.py", "/signal/signal.db", "/static/"):
        assert svc.call("GET", path)[0] == 404

def test_name_then_feed(svc):
    assert svc.call("GET", "/api/feed?view=latest")[0] == 401
    status, headers, _ = svc.call("POST", "/api/me", body={"name": "  A.  Kovac "})
    assert status == 200 and headers["Set-Cookie"].startswith("signal_name=A.%20Kovac;")
    cookie = headers["Set-Cookie"].split(";")[0]
    assert svc.call("GET", "/api/me", cookie=cookie)[2] == {"name": "A. Kovac", "role": "reader"}
    status, _, data = svc.call("GET", "/api/feed?view=latest", cookie=cookie)
    assert status == 200 and len(data["cards"]) == 30 and data["next_before"]
    assert set(data["cards"][0]) == {"id", "title", "link", "summary", "source", "kind", "published_at",
                                    "other_sources", "saved", "topics"}
    assert svc.call("GET", "/api/feed?view=top", cookie=cookie)[0] == 400
    assert svc.call("POST", "/api/me", body={"name": "   "})[0] == 400

def test_save_and_follow_round_trip(svc, cookie):
    assert svc.call("POST", "/api/stories/5/save", cookie=cookie)[2] == {"saved": True}
    assert [c["id"] for c in svc.call("GET", "/api/feed?view=saved", cookie=cookie)[2]["cards"]] == [5]
    assert svc.call("DELETE", "/api/stories/5/save", cookie=cookie)[2] == {"saved": False}
    assert svc.call("POST", "/api/stories/9999/save", cookie=cookie)[0] == 404
    assert svc.call("POST", "/api/topics/1/follow", cookie=cookie)[2] == {"following": True}
    assert svc.call("GET", "/api/topics", cookie=cookie)[2][0]["following"] == 1
    assert svc.call("POST", "/api/topics/99/follow", cookie=cookie)[0] == 404

@pytest.mark.parametrize("origin", [None, "http://evil.example", "https://127.0.0.1:{port}", "null"])
def test_a_write_from_another_origin_changes_nothing(svc, cookie, origin):
    assert svc.call("POST", "/api/stories/5/save", cookie=cookie, origin=origin)[0] == 403
    assert svc.call("POST", "/api/me", body={"name": "Eve"}, origin=origin)[0] == 403
    assert svc.call("GET", "/api/feed?view=saved", cookie=cookie)[2]["cards"] == []

def test_other_host_names_and_cross_site_reads_are_refused(svc, cookie):
    assert svc.call("GET", "/", host="evil.example")[0] == 403
    assert svc.call("GET", "/api/feed?view=latest", cookie=cookie, headers={"Sec-Fetch-Site": "cross-site"})[0] == 403

def test_bodies_are_capped_and_must_be_json(svc):
    assert svc.call("POST", "/api/me", raw=b"x" * (64 * 1024 + 1))[0] == 413
    assert svc.call("POST", "/api/me", raw=b"{not json")[0] == 400
    assert svc.call("POST", "/api/me", raw=b"[]")[0] == 400

def test_search_text_cannot_break_the_api(svc, cookie):
    for q in ['"', "*", "NEAR(", "%00", "a" * 5000]:
        assert svc.call("GET", "/api/feed?view=latest&q=" + urllib.parse.quote(q), cookie=cookie)[0] == 200

def test_loop_pass_updates_status_and_survives_a_failing_pass_with_recorded_feed(svc_with_loop):
    loop, call = svc_with_loop          # one approved source; fetch replaced: first call raises RuntimeError, later calls return RSS
    loop.run_once(NOW)
    assert call("GET", "/api/status")[2]["loop_error"]            # the failure is visible
    loop.run_once(NOW + timedelta(seconds=60))
    status = call("GET", "/api/status")[2]
    assert status["loop_error"] is None and status["sources"] == {"approved": 1, "failing": 0}
    assert status["last_pass_at"] == (NOW + timedelta(seconds=60)).isoformat()

def test_a_save_during_a_pass_succeeds(svc_with_loop, cookie):
    loop, call = svc_with_loop          # fetch replaced by one that blocks on an Event mid-pass
    with pass_in_progress(loop):
        assert call("POST", "/api/stories/1/save", cookie=cookie)[0] == 200

def test_wildcard_host_is_refused():
    assert main(["--root", "x", "serve", "--host", "0.0.0.0"]) == 2
```

- [ ] **Steps 2-5:** run (import error); implement; `uv run pytest tests/test_signal_service.py tests/test_signal_cli.py -q` passes; quality gate exit 0; commit `feat(signal): HTTP service with the feed API and the ingest loop`.
- [ ] **Step 6: PR 2a.** Open the pull request for Tasks 1 to 4 (base: the slice 1 branch or `main` once slice 1 is merged).

### Task 5: The page

**Files:** create `src/deploy_workflow/signal/web/index.html`, `signal.css`, `signal.js`, `render.js`, `render.test.cjs`. Work from `docs/design/mockups/signal.html`; reuse its layout and tokens, drop what this slice does not have.

**Screen map (each kind of information has its own component):**

| Information | Component | Notes |
|---|---|---|
| Where am I | Icon rail, Signal active | as the mockup; links to Start a run and Issuer library only when the service is given their address (Task 7) |
| Views | Channel list: For you, Latest, Saved, then Topics | topic rows carry a follow toggle (star button, `aria-pressed`) and a story count; no Groups or Digests sections in this slice |
| Who am I | Name chip at the foot of the channel list | role shown as a small label; "not a login" note on hover and focus |
| First visit | Name dialog | one field, cannot be dismissed empty |
| Filters | Kind chips (All, Regulators, News, Ratings, Research) and a search field | search is debounced 300 ms; `/` focuses it |
| Freshness | "Sources checked N min ago" line; "N new stories" pill | static text from `/api/status`; the pill appears from the 45-second poll and loads the new stories when pressed |
| A story | Card per kind: regulator, ratings, news, research | same skeleton, different kind label and accent token per kind (label text carries the meaning, not colour); source monogram, relative time with the full time as `title`, headline, summary, topic tags, "Also in N other sources", Save toggle, Open source |
| More stories | "Show older" button | uses `next_before`; no infinite scroll |
| Nothing to show | Empty state per view | For you: "Follow a topic to fill this view" with the topic list; Saved: "Stories you save appear here"; search: "No story matches …"; Latest with no sources: "No approved sources yet" |
| Waiting | Skeleton cards | three placeholders; no spinner; respects reduced motion |
| Trouble | Inline error band | plain sentence and a Retry button; the last good list stays on screen |

No thread column, no post box, no AI line, no signal bars, no stage tracker, no settings link in this slice.

**Interfaces:**
- `render.js` exports (CommonJS for the test, attached to `window.SignalRender` in the page): `card(doc, story, now) -> Element`, `emptyState(doc, view, query) -> Element`, `relativeTime(iso, now) -> string`, `safeLink(url) -> string | null` (returns the URL only for `http:` or `https:`).
- `relativeTime`: under 1 minute "just now"; under 60 minutes "N min ago"; under 24 hours "N h ago"; under 7 days "N d ago"; else the date as `13 Nov 2026`. A future time is "just now".
- `signal.js` holds state and calls the API; it contains no HTML strings with data.

- [ ] **Step 1: `render.test.cjs`** (run with `node --test`; use a minimal DOM double as `apps/issuer-library/credit_os/web/components.test.cjs` does)

```js
test('relativeTime', () => {
  const now = new Date('2026-11-13T12:00:00Z');
  assert.equal(relativeTime('2026-11-13T11:59:40Z', now), 'just now');
  assert.equal(relativeTime('2026-11-13T11:15:00Z', now), '45 min ago');
  assert.equal(relativeTime('2026-11-13T03:00:00Z', now), '9 h ago');
  assert.equal(relativeTime('2026-11-10T12:00:00Z', now), '3 d ago');
  assert.equal(relativeTime('2026-11-01T12:00:00Z', now), '1 Nov 2026');
  assert.equal(relativeTime('2026-11-14T12:00:00Z', now), 'just now');
});
test('safeLink allows only http and https', () => {
  assert.equal(safeLink('https://a.org/x'), 'https://a.org/x');
  for (const bad of ['javascript:alert(1)', 'data:text/html,x', ' JAVASCRIPT:alert(1)', 'file:///etc/passwd', '//a.org/x', ''])
    assert.equal(safeLink(bad), null);
});
test('a card renders hostile text as text', () => {
  const el = card(doc, {id: 1, title: '<img src=x onerror=alert(1)>', summary: '</script><b>x</b>', link: 'javascript:alert(1)',
                        source: '<i>S</i>', kind: 'news', published_at: '2026-11-13T11:00:00Z', other_sources: 2, saved: false,
                        topics: ['<u>T</u>']}, new Date('2026-11-13T12:00:00Z'));
  assert.equal(el.querySelectorAll('img, b, i, u, script').length, 0);
  assert.ok(el.textContent.includes('<img src=x onerror=alert(1)>'));
  assert.equal(el.querySelector('a[href]'), null);                 // no link for a javascript: URL
  assert.ok(el.textContent.includes('Also in 2 other sources'));
});
test('a card links out safely and marks its kind in words', () => {
  const el = card(doc, {id: 2, title: 'T', summary: '', link: 'https://a.org/x', source: 'Authority', kind: 'regulator',
                        published_at: '2026-11-13T11:00:00Z', other_sources: 0, saved: true, topics: []}, new Date('2026-11-13T12:00:00Z'));
  const a = el.querySelector('a[href]');
  assert.equal(a.getAttribute('rel'), 'noopener noreferrer'); assert.equal(a.getAttribute('target'), '_blank');
  assert.ok(el.textContent.includes('Regulator'));
  assert.equal(el.querySelector('[data-action="save"]').getAttribute('aria-pressed'), 'true');
  assert.ok(!el.textContent.includes('other sources'));
});
```

- [ ] **Step 2:** `node --test src/deploy_workflow/signal/web/render.test.cjs` — fails (module missing).
- [ ] **Step 3:** Write `render.js`, then `index.html`, `signal.css`, `signal.js`. No `style=` attributes and no `<script>` or `<style>` blocks in `index.html` (the policy forbids them). CSS uses the tokens in `apps/issuer-library/credit_os/web/brand.css` and `screen.css` `:root`; body text at least 13px, labels at least 12px.
- [ ] **Step 4:** `node --test …/render.test.cjs` passes; add it to the `node --test` line in `.github/workflows/checks.yml`.
- [ ] **Step 5:** Commit `feat(signal): feed page`.

### Task 6: Browser proof

**Files:** create `tests/test_signal_page_browser.py` (marked `browser`), following the Chrome harness in `tests/test_library_page_browser.py` (read how it finds Chrome, runs a node script and reads results; reuse its helpers by import, do not copy them).

Each test starts the real service on loopback with the Task 2 fixture data plus one story whose title is `<img src=x onerror="window.__xss=1">` and whose link is `javascript:window.__xss=1`.

- [ ] **Step 1: tests, each asserting on the live DOM**
  - First visit shows the name dialog; an empty name keeps it open; "A. Kovac" closes it and the chip shows the name and "Reader".
  - Latest shows 30 cards, newest first; "Show older" adds the rest; no console error; `window.__xss` is undefined; the hostile title is visible as text; that card has no link.
  - A kind chip filters; typing `wire remedy` in search leaves one card; clearing restores 30; `/` focuses the search field.
  - Save toggles `aria-pressed`, and the story is listed under Saved after a reload.
  - Following the topic from the channel list makes it appear under For you; an empty For you shows its empty state text.
  - With the service stopped mid-session, the next action shows the error band with Retry and keeps the cards.
  - The page makes no request to any other origin and the response policy has no `unsafe-inline` (read from the response).
  - Keyboard only: Tab reaches channel list, search, first card's Save and Open source in that order; focus is visible (computed outline or box-shadow not `none`).
  - At 375 px width there is no horizontal scroll and the channel list is reachable from a "Channels" button.
  - Contrast: for every text node in the first three cards and the channel list, computed colour against background is at least 4.5:1 (use the harness's contrast helper if it has one; else compute in the node script).
- [ ] **Step 2:** `uv run pytest tests/test_signal_page_browser.py -q -m browser` — passes on a machine with Chrome; the report states where it ran.
- [ ] **Step 3:** Screenshots of Latest (desktop and 375 px) and the empty For you state saved under `docs/design/mockups/signal-slice2-*.png` for the owner; commit `test(signal): browser proof of the feed page`.

### Task 7: Packaging, the rail link and the records

**Files:** modify `apps/issuer-library/packaging/runtime.py` and `build.py`, `tests/test_issuer_library_packaging.py`, `src/deploy_workflow/run_start/service.py`, `docs/templates/context-form.html`, `tests/test_run_start_service.py`, `README.md`, `VERIFICATION.md`. This task touches the run start service, which can start paid runs: it gets a security review as well as the task review.

- [ ] **Step 1: packaging.** Add `Start signal.cmd <shared folder> [address]` beside `Start run page.cmd` in `runtime.py`, same shape and usage text, running `python -m deploy_workflow.signal --root <folder> serve --host <address> --port 8766`; make `build.py` ship `src/deploy_workflow/signal/web/`. Extend the packaging test with the new wrapper's expected lines and the shipped files. Run `uv run pytest tests/test_issuer_library_packaging.py -q`.
- [ ] **Step 2: rail link, test first.** `run_start` gains `--signal-url <url>`: accepted only if it parses as `http://<host>:<port>/` with no path, query, fragment or userinfo; anything else exits 2. `GET /` then serves the start page with a Signal link in the rail; without the option the page is byte-identical to today. The link is added by replacing one marker comment in `docs/templates/context-form.html` with a fixed anchor whose `href` is the validated URL, HTML-escaped. Tests in `tests/test_run_start_service.py`: with the option the served page contains `id="rail-signal"` and the exact URL once; without it the page has no `rail-signal`; `--signal-url "javascript:alert(1)"`, `"http://a/b"`, `"http://u@a:1/"`, `"https://a:1/"` and `'http://a:1/"><script>'` each exit 2. The existing run start tests pass unchanged.
- [ ] **Step 3: live proof, free.** With the two feeds the owner's corpus lists (CMA cases, BEREC), on a throwaway root: propose, approve, `topics add`, start `serve`, open the page in the browser pane, set a name, follow the topic, save a story, search; record what was seen and one screenshot. Label it "live fetch of two public feeds, no model call, no cost".
- [ ] **Step 4: records.** README "Signal" section: the `serve` command, `Start signal.cmd`, what the page does and does not do in this slice, known limits (not a login; no AI; Latest order only). One `VERIFICATION.md` entry at the tip (scope, gates with exit codes, browser proof and where it ran, live proof, `Not verified:`), keeping the file under 1,000 lines. The reader check in `AGENTS.md` applies to the issuer report and is not owed here; say so in the entry.
- [ ] **Step 5:** all gates; commit `feat(signal): package the service and link it from the run start rail`; open PR 2b.

---

## Not in this plan

Groups, threads, sharing and notifications (slice 3); settings pages, including topic management in the browser (slice 4); the AI line, signal strength, kinds from the model, the Top order and cost control (slice 5); digests (slice 6); the landing page and real login; a Signal link in the static issuer library.

## Open for the owner before or during the build

1. Port 8766 for Signal and a second `.cmd` wrapper are designer's calls.
2. The page has no Top/Latest toggle until slice 5 supplies signal strength; say if a recency-only "Top" is wanted sooner.
3. Topics are created from the command line in this slice; the first topic list is yours to supply (or approve one drawn from the corpus sectors).
