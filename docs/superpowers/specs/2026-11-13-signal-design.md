# Signal: shared feed of external research with group threads

Status: draft for owner approval, 2026-11-13. Mockup: `docs/design/mockups/signal.html`
(invented sample content; open it in a browser, "Signal settings" switches views).

Lines marked **(call)** are the designer's choices, not owner decisions. The owner may overrule
any of them.

## 1. Intent

Analysts follow many outside sources by hand and discuss them in scattered places. Signal
brings relevant external research from qualified, reputable sources into one modern feed, and
lets analysts share stories into group threads (for example "TMT analysts") and comment on
them. It is a news feed, not an analysis tool: it is not tied to an issuer, a run or the issuer
library. Query (new research from run data with SQL and AI) is a different feature.

"Regulators" means sector and competition regulators and regulation news that may affect
issuers, for example a competition authority's case on a telecoms operator. It does not mean
financial-market supervisors only.

## 2. Goals, non-goals, anti-goals

Goals

- One feed of stories from an owner-approved source list, with duplicates folded.
- Groups with threads: share a story or a note to a group, comment and reply.
- Topics: saved rules that sort stories into channels.
- A cheap, fast AI pass per story: one "why it matters" line, a signal strength, and tags.
- Digests: each user builds scheduled briefs (daily, weekly, monthly) from one standard form.
- Settings for groups, thread rules, sources, topics, digests, notifications, and AI and cost.
- Three powers: readers read; writers post, comment, and manage groups and topics; the owner
  approves sources and sets the AI spend cap.

Non-goals for this build (on the to-do list, each its own design later)

- The landing page with invite codes and passcodes. Login is applied there, not in Signal.
- Analyst review of completed runs (a run card in the feed, a human-judgement thread, and an
  "Analyst review" section in the issuer report with its history).
- Outlook mail as a source (enterprise environment only).
- Sources that publish no feed (page scraping, paid APIs).
- Email delivery of digests. Linking stories to library issuers. Case timelines across stories.

Anti-goals (a failure even if it works)

- A story from an unapproved source reaching anyone's feed.
- AI text that a reader could mistake for a colleague's comment, or the reverse.
- Storing or showing full article text.
- Any AI call made because someone opened or refreshed a page.
- AI spend without a cap.
- A flat, repetitive page, or anything that looks lifted from Markdown.

## 3. Constraints

- Python 3.13 standard library plus the already-pinned dependencies. No new dependency.
- SQLite is the store. DuckDB 1.4.4 is also approved by the owner but Signal does not use it
  **(call)**: Signal's load is small concurrent writes, which is SQLite's job.
- Ships in the same Windows package as the workflow; no build toolchain, no compiled front end.
- No credential files. Provider keys come only from the launching environment.
- Paid model calls need a standing ruling in `docs/rulings/` and a cap, as Submit has.
- Never write into run folders or predecessor repositories.
- The project quality gate, targeted tests, confidence-review and rewrite-tournament apply.
- Owner design rules of 2026-11-13: each kind of information gets its own component; UI
  components are sourced only from the eight approved libraries, live pages read first. The
  mockup borrows from Preline's activity-feed and workspace blocks.
- PRs stay within 800 changed lines, so the build lands in slices (section 9).

## 4. Approaches considered

| | What | Trade-off |
|---|---|---|
| A. House style | Standard-library server, SQLite with FTS5, own feed parser, plain JavaScript pages, existing model adapter | No new dependencies; feed parsing and UI are hand-built |
| B. Feed library | A, with `lemon24/reader` (BSD-3) for fetch, store and search | Less feed code; a dependency chain, a decision record, a second schema |
| C. Modern stack | Web framework, React, push updates | Polished UI fastest; new toolchain, breaks the packaging |

Chosen: **A (call)**. The owner replied to the three options by approving SQLite and DuckDB
1.4.4 and did not name a letter; A is the designer's reading of that. The approved source list
is short and mostly regular feeds; if awkward feeds appear, the parser module can be swapped
for B's library.

## 5. Design

### 5.1 Shape

A separate service, `python -m deploy_workflow.signal --root <root> --host <address> --port
<port>` **(call)**, in the style of `deploy_workflow.run_start.service`: standard-library HTTP
server, `127.0.0.1` by default, `0.0.0.0` refused. It owns one SQLite file,
`<root>/signal/signal.db`, in WAL mode. Its pages are plain HTML, CSS and JavaScript using the
library's brand tokens, fonts and icons. The run start page's rail gains a Signal link when
the service is started with Signal's address **(call)**. The issuer library's generated pages
are not changed in this build, so no delivery code is touched and no reader check is owed; a
Signal link in the library rail is deferred to the landing-page project.

One background loop in the service does two jobs: fetch due sources, and run due digests. Due
times live in SQLite, so a restart loses nothing. Pages poll for new items and comments every
30 to 60 seconds; there is no push channel.

### 5.2 Who the user is (until the landing page exists)

All identity goes through one function, `current_user(request) -> User(name, role)`. Interim
implementation **(call)**: on first visit the user types a display name, kept in a cookie. The
owner adds names and roles from the command line (`... signal users add "A. Kovac" --role
writer`); an unknown name is a reader. This is not authentication: anyone on the network can
type a writer's name. The page says so in settings. The landing-page project replaces this one
function and nothing else.

Because a typed name proves nothing, the owner's powers are not in the browser in this build
**(call)**: approving or pausing a source and setting the AI cap are command-line actions on
the server (`... signal sources approve <id>`, `... signal ai cap <amount>`). The Sources and
"AI and cost" settings sections show the same information read-only, with the proposal box
still open to writers. The Approve button and the switches in the mockup's owner sections
arrive with the landing page.

One shared instance serves everyone **(call)**: it runs on the machine that runs the run
start page, started by a `Start signal.cmd` wrapper in the Windows package beside
`Start run page.cmd`, and takes the same `--host` rule. It must stay running for fetches and
digests to happen; a digest whose time passed while it was down runs once at the next start.

### 5.3 Sources and ingest

- A source has a name, a kind (regulator, news, ratings, research), a feed address and a
  state: proposed, approved, paused. Writers propose; only the owner approves. Nothing is
  fetched from a proposed source.
- Fetch rules: `https` only; the host must be a plain DNS name (no IP-address literals) that
  resolves only to public addresses, checked at fetch time and at each of at most three
  redirect hops; 10 seconds for the whole fetch; no proxies; 2 MB cap; conditional requests
  (`ETag`, `Last-Modified`); each source at most every 10 minutes **(call)**.
- Parsing: RSS 2.0 and Atom with `xml.etree.ElementTree`. A feed with a DTD or entity
  declarations is rejected. A feed that fails to parse marks the source "Failing" in settings
  with the reason; it never fails silently.
- Stored per story: source, title, link, published time, and the feed's own summary cut to 300
  characters. No article body is fetched or stored.
- Folding: a story whose normalised link matches an existing one, or whose normalised title
  matches one from a different source in the previous 48 hours (titles of four or more words
  only), joins that story as "also in N other sources".
- Source health in settings: last check, last item, items per week for six weeks, and a state
  of healthy, quiet (no item in 7 days) or failing.

### 5.4 Topics and search

A topic is a name plus a rule: keywords and optional source kinds. Rules run as FTS5 queries
over title and summary when a story arrives. The same index backs the search box. No AI.

Writers create and edit topics. Every user, readers included, chooses which topics to follow
**(call)**; a new user follows none. "The user's topics" everywhere in this document means the
topics that user follows, and "the user's groups" means the groups they are a member of.

### 5.5 The AI pass

One small-model call per batch of new stories (up to 20 per call **(call)**), through the
project's existing model adapter and a provider it already supports. Input: title and stored
summary only. Output, validated with pydantic, per story:

- `why`: one sentence, at most 240 characters.
- `signal`: 1, 2 or 3.
- `tags`: from a fixed sector and theme list kept in the repository.
- `kind`: news, regulatory case, rating action, or other; and where the text states them, a
  case stage (opened, initial review, in-depth review, decision) or a rating move (from, to).

Rules: feed text is untrusted data inside the prompt; every output field is rendered as plain
text and marked "AI"; a story whose output fails validation is stored without AI fields and
shows no AI line (logged, visible as a count in settings). The stage tracker and the rating
move appear only when the model returned them. Nothing here runs on page view.

### 5.6 The feed

- Views: For you (stories in the user's topics and groups), Latest, Saved, each topic, each
  group. Filter chips by kind and "shared by colleagues".
- Order for "Top": signal strength, decayed by age, raised by shares and comments in the
  user's groups. Deterministic, no AI, one tested function. "Latest" is by published time.
- Card per kind, as in the mockup: regulatory case (stage tracker), rating action (from and
  to), news (duplicates folded), digest (dark card, numbered points). Every card: source,
  time, kind, signal bars, the AI line, tags, and Comment, Share to group, Save, Open source.
- "Sources checked N min ago" is a static line from the last loop time.

### 5.7 Groups and threads

- A group has a name, visibility (everyone, or invited members), members, and optional topics
  whose stories post into it automatically. Writers create and manage groups.
- A thread belongs to one group and starts from a shared story or from a note. One thread per
  story per group: a second share joins the existing thread. Comments nest one level.
- A comment can be edited for 15 minutes and is then marked edited. A deleted comment leaves
  a "removed" line. Threads quiet for 90 days can be archived (searchable, read-only); that
  switch is off by default. These are per-group settings with the defaults above.
- Comment text is plain text with links made clickable; no HTML, no Markdown.
- Reactions as in the mockup are **(call)** limited to a small fixed set.

### 5.8 Digests

A digest is a user's saved brief plus a schedule. The form is the same for everyone:

- Covers: groups and topics.
- Runs: daily, weekly (day) or monthly (day of month), at a time.
- Brief: the standard template with five editable parts (subject, period, number of points,
  what to list as upcoming, look-ahead days).
- Length: short or standard.

A run gathers the stored title, AI line and link of stories in scope for the period (highest
signal first, capped at 60 **(call)**), makes one model call, and stores a structured result:
numbered points, each with the ids of the stories behind it. It renders as a digest card and a
digest page with links to those stories, and lands in the user's Signal inbox with an unread
dot. "Run once now" runs it immediately. Five digests per user **(call)**. If no story is in
scope the digest says nothing material happened without calling the model.

### 5.9 Notifications

Per user, two switches per event (raise the count on the rail; pin to the top of the feed)
for: replies to my comments, new threads in my groups, high-signal stories in my topics, a
digest is ready. Counts come from the polling endpoint.

### 5.10 Cost control

The owner sets a monthly cap. Spend never passes it **(call)**: before each call Signal
reserves the call's worst-case cost with the project's existing pricing
(`deploy_workflow.model.pricing`) and makes the call only if the reservation fits under the
cap; after the call it records the actual cost in SQLite. Reuse `deploy_workflow.model.budget`
if its per-run shape fits a monthly ledger, otherwise a small ledger of the same
reserve-then-settle design. A call whose cost cannot be established (a provider that reports
none and has no price entry) counts as its full reservation and switches the AI pass off
until the owner clears it; it is never counted as zero.

At the cap, stories still arrive without the AI line and digests pause, and settings say so.
The ruling uses the existing `check_ruling` format and names the model config ids Signal may
use. The cap and the ruling are preconditions for switching the AI pass on; with no ruling or
no key the service runs with AI off and the feed still works.

### 5.11 Safety

- All feed and user text is escaped on output; the pages carry a content security policy that
  allows no inline script and no third-party origin.
- "Open source" links open in a new tab with `rel="noopener noreferrer"`.
- Writes require a same-origin check and a request size limit.
- The service serves only its own pages and API; it serves no file from `<root>`.

## 6. Data (tables, one line each)

`users`, `sources`, `source_checks`, `stories` (+ FTS5 index), `story_duplicates`,
`story_ai`, `topics`, `topic_stories`, `topic_follows`, `groups`, `group_members`, `group_topics`, `threads`,
`comments`, `reactions`, `saves`, `digests`, `digest_runs`, `notification_settings`,
`read_marks`, `ai_usage`, `settings`. Column design is left to the builder.

## 7. Testing

- Feed parsing, folding, topic rules, ranking and schedule arithmetic: unit tests against
  fixture feeds and expected values written independently of the code; property tests for
  ranking order and next-run times.
- Fetch rules: tests that private addresses, non-`https` addresses, oversized bodies and
  entity-bearing feeds are refused.
- AI pass and digests: tests run against recorded model responses and are labelled as such.
  A live proof (real feeds, real model, retained responses) is a separate, explicit paid step
  after the ruling.
- Pages: browser tests for the feed, a thread, and each settings section, at desktop and
  narrow widths.

## 8. Left to the builder

Column and index design; API routes and payload shapes; module layout under
`src/deploy_workflow/signal/` and the page files; the exact ranking weights; the fixed tag
list; the small-model choice per provider; polling details; empty, loading and error states
for each view (they must exist and follow the design rules).

## 9. Build order

1. Store, sources, ingest loop, folding, source health; command line for users and sources.
2. Feed pages: views, cards without AI fields, search, save.
3. Groups, threads, comments, sharing, notifications.
4. Settings pages.
5. AI pass and cost control (after the ruling).
6. Digests.

## 10. Open for the owner

1. The monthly AI cap figure and the standing ruling for Signal's model calls.
2. The first approved source list. Which sector regulators publish a feed is not yet checked.
3. Whether approach A is confirmed.
