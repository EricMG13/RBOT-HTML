# Signal slice 3: groups and threads — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Writers can make groups, share a story or a note into a group as a thread, comment, reply and react; every user sees the threads of the groups open to them, with an unread count on the rail.

**Architecture:** Slices 1 and 2 stay as they are. This slice adds group, thread, comment, reaction and read-mark tables (migration 3), two store modules (`groups.py`, `threads.py`) that hold every permission and visibility rule, JSON routes on the existing service, and three additions to the existing page: groups in the channel list, a group view (thread list), and a thread panel with a reply box. No AI, no settings pages, no digests.

**Tech Stack:** Python 3.13 standard library (`sqlite3`, `http.server`), plain JavaScript and CSS with the library's brand tokens, pytest, hypothesis, `node --test`, the repo's Chrome harness.

**Spec:** `docs/superpowers/specs/2026-11-13-signal-design.md` (5.2, 5.6, 5.7, 5.9, 5.11, 6, 7, 9 step 3). Mockup: `docs/design/mockups/signal.html` (the `shared` line on a card, the `thread` panel). Builds on main at `ce18c8c` (slices 1 and 2, PRs 101, 102, 106, 109, 115).

## Rulings made in this plan (the spec is silent or defers; each is the owner's to overturn)

| # | Ruling | Why | Cost if wrong |
|---|---|---|---|
| P1 | A share is not stored on its own. The first share starts the thread; a later share with a note adds a comment; without a note it returns the existing thread. | The spec's table list has no shares table; "raised by shares" belongs to the Top order (slice 5). | A shares table and a backfill from thread starters in slice 5. |
| P2 | Per-group thread rules and archiving (spec 5.7, "per-group settings") arrive with slice 4's settings. Here the edit window is the constant 15 minutes and nothing is archived. | No page can change them before slice 4. | Two columns on `groups` in slice 4. |
| P3 | Notification switches (spec 5.9) arrive with slice 4. Here "raise the count on the rail" is on for replies to my comments and new threads in my groups; "pin to the top" is off. | Same. | None; slice 4 adds the table. |
| P4 | Reactions are a fixed set of four on comments only: `up` 👍, `eyes` 👀, `check` ✅, `question` ❓. Reacting is a writer action. | Spec 5.7 "small fixed set"; the mockup shows 👍 and 👀; a reaction is visible to others, so it is posting. | One tuple. |
| P5 | Only its author can edit or delete a comment. | Spec names no moderator. | A rule in `threads.py`. |
| P6 | A thread posted automatically from a group's topic has no starter and does not raise anyone's unread count. | A busy topic would bury the two events the count exists for. | One clause in `unread`. |
| P7 | An invited group is visible only to its members; a writer manages a group only if they can see it. Everyone-groups: any user joins or leaves by themself. Invited groups: a writer member adds and removes names. | Spec 5.7 visibility; least surprising reading. | Rules in `groups.py`. |
| P8 | A thread holds at most 500 comments; a comment is 1 to 4,000 characters; a note title 1 to 120; a group name 1 to 60. The thread panel loads the whole thread, no paging. | Keeps one request and one render per thread. | Paging in the thread route. |
| P9 | No search over comments. | Spec 5.4 indexes stories only. | An FTS table later. |
| P10 | Renaming a group, changing its visibility or topics after creation waits for slice 4. | Settings slice. | None. |
| P11 | (added during the build) The quality gate allows five parameters. The writer actions that take both the user and the time take them as one value, `groups.Act(user: User, now: datetime)`, in the user's position: `create_group`, `add_member`, `share_story`, `start_note`, `add_comment`, `edit_comment`, `delete_comment`. Where a signature or test below shows `USER, ..., now` for these, read `Act(USER, now), ...`. Expected values are unchanged. | Six parameters fail ruff PLR0913 and suppressions are not allowed. | A mechanical change of call sites. |
| P12 | (added during the build) Group names are unique across all groups on a key: the cleaned name, NFKC, case-folded. Creating a group with a taken name answers "that group name is taken" whether or not the creator can see the other group. | One name per group avoids two groups nobody can tell apart; the disclosure is one guessed name, to writers only. This is the one stated exception to "a hidden group is indistinguishable from a missing one". | Names unique per visible set, and a way to tell twins apart. |
| P13 | (added during the build) An invited group always keeps a member who is a writer or the owner: a `leave` or `remove_member` that would break this is refused. | Otherwise nobody, the owner included, can see or manage it and its name stays taken. | One check. |
| P14 | (added during the build) A thread row's unread dot is on when the thread is one `unread()` counts as a new thread for that user, or has a live comment by another author above the user's mark. This replaces Task 3's "no mark, or ...". | The dot and the rail count must agree; the literal rule flagged a user's own and automatic threads. | One clause. |
| P15 | (added during the build) A deleted comment's text is emptied in the table and `secure_delete` is on, so it leaves the database file at the next checkpoint; it can remain in the write-ahead log while other connections are open. The README states this. | Scrubbing the log needs a blocking checkpoint after every delete. | A TRUNCATE checkpoint after delete. |

## Prior art (searched 2026-11-13)

- This repo: `git grep` for `read_marks|reactions|add_comment|group_members|unread` outside `signal/` — no comment or thread store.
- Owner's repos: `gh search code "CREATE TABLE comments" --owner <owner>` and `"thread_id parent_id sqlite3"` — no hits.
- Public: `gh search repos "threaded comments sqlite python"`, `"comments sqlite stdlib http.server"`, `"isso comments"` — nothing stdlib-only. Isso (a comment server with one-level nesting and an edit window) is the known shape but brings its own web stack.
- Decision: build new on Signal's store and service. Not verified: an empty search does not prove nothing exists.

## Global Constraints

- Everything in slice 2's Global Constraints still binds (`docs/superpowers/plans/2026-11-13-signal-2-service-and-feed-pages.md`): no new dependency; request rules; the exact content security policy; `textContent` only; no suppression comments; no stub or fake; no catch-all; tests that replace the network or the clock say so in their names; expected values come from this plan.
- Identity is still not authentication (spec 5.2). This slice is the first to gate HTTP actions on role, so the limit is now real: anyone who can reach the port can type a writer's name, post as them and read an invited group. The page says so beside the reply box and in the group dialog; the README's limits say so. No owner action is added over HTTP.
- Powers (spec 2): readers read; writers and the owner post, comment, react and manage groups. Role comes from `identity.current_user`; an unknown name is a reader.
- One rule decides what a user can see: `groups.can_see`. Every read and write of a group, thread, comment, reaction, count or card goes through it. A group the user cannot see is indistinguishable from one that does not exist: same status (404), same body, on every route.
- A refused write changes nothing and answers 403 with one line of text.
- Migration 3 is appended to `MIGRATIONS`; migrations 1 and 2 are not edited (main is deployed now).
- Comment and note text is plain text. The server stores it cleaned (controls except newline dropped, NFC, trimmed); the page shows it with `textContent` and turns only `http:`/`https:` addresses into links (`rel="noopener noreferrer"`, `target="_blank"`). No HTML, no Markdown.
- Time is passed in: store functions that depend on the clock take `now: datetime` (UTC). The service passes `datetime.now(UTC)`.
- Order: threads by last activity, newest first; comments by id. No Top order (slice 5).
- Polling, no push: the open thread is re-read every 45 seconds and on `visibilitychange`; unread counts ride the existing poll.
- Design rules (owner, 2026-11-13): the screen map below is binding. Before Tasks 5 and 6 the controller reads the live page of each component taken from the eight approved libraries and names it in the task brief; none is used from memory. Nothing looks lifted from Markdown; every view has empty, loading and error states.
- Accessibility as slice 2: landmarks, labels, full keyboard use, visible focus, contrast at least 4.5:1, `prefers-reduced-motion`, no information by colour alone. The thread panel is a labelled `aside`; opening it moves focus to its heading and closing returns focus to the control that opened it.
- Gates: `uv run pytest tests/test_signal_*.py -q` (quote the glob), `node --test src/deploy_workflow/signal/web/render.test.cjs`, `uv run python tools/quality_gate.py`; all exit 0.
- Reviews: `mx-precise` per task; `mx-adversary` also on Tasks 1, 2 and 4 (visibility and permission are security). Every task report ends with `Not verified:`. Ledger line per task: `agent=<name> fix-rounds=<n> gates-first-pass=<y|n|n/a>`.
- Four pull requests, stacked: 3a = Tasks 1 to 3 (store), 3b = Task 4 (routes), 3c = Tasks 5 and 6 (page), 3d = Task 7 (browser proof, records). Slice 2's two PRs came to 2,150 and 2,590 lines against the 800 guideline, mostly tests; report each PR's count and say if one passes 800.

## Review Focus

1. A non-member of an invited group must learn nothing about it: not its name in the channel list, not a thread by guessed id, not a comment, not a count in `/api/unread`, not a thread chip on a feed card, not a different error text. Tests in Tasks 1, 2, 3 and 4.
2. A reader, an unknown name, and a page on another site must not be able to post, edit, delete, react, create a group or add a member; the store is unchanged afterwards. Tests in Tasks 2 and 4.
3. Comment text containing markup, a `javascript:` address, an address with `"` or `<`, right-to-left overrides, 4,001 characters or only spaces: stored cleaned or refused, shown inert, linked only when `http`/`https`. Tests in Task 2 (store), Task 5 (render), Task 7 (browser).
4. Two shares of one story into one group at the same moment make one thread; a comment posted during an ingest pass succeeds. Tests in Tasks 2 and 4.
5. Boundaries of the comment rules: an edit at exactly 15 minutes is allowed and at 15 minutes and 1 second refused; another user's comment; a reply to a reply; a reply whose parent is in another thread; a reply to a removed comment (allowed); a comment on the 501st slot. Tests in Task 2.

## Screen map (binding for Tasks 5 and 6)

| Screen or part | Information | Component |
|---|---|---|
| Channel list, Groups section | groups open to the user, unread per group | list of links with a count badge; lock icon for invited groups; "New group" button for writers |
| Rail | total unread | count badge on the Signal icon |
| Feed card | who shared it where, with the note's first line | the mockup's `shared` line (avatar, names, quote); a chip per thread with its comment count; "Share to group" button |
| Share dialog | choose a group, optional note | `dialog` with a radio list of groups and a text area |
| New group dialog | name, visibility, topics, the identity warning | `dialog` with a text field, a two-option segmented control, topic checkboxes |
| Group view | threads by last activity | thread rows: story threads as a compact quote card (kind, source, title), note threads as a titled note row; comment count, last activity, unread dot; members strip (avatars, count, Join/Leave or Add member) |
| Thread panel | the story or note, comments, replies | header (group, counts); the mockup's `quote` block; comment items with avatar, name, role tag, time, "edited" tag; replies indented one level; a removed comment as a muted one-line placeholder; day dividers |
| Reactions | four fixed reactions with counts | toggle chips under a comment; pressed state by `aria-pressed`, not colour alone |
| Reply box | text, send, the 15-minute edit rule | text area with a character counter that appears at 3,800; Send; for readers the mockup's note "Readers see this thread but not the reply box" in its place |
| Live state | thread refreshed, send in progress | the existing pulse beside "checked N min ago"; a sending state on the button |
| Empty, loading, error | no groups; no threads; thread failed to load | slice 2's `emptyState` and error band, with wording per view |

## File structure

| File | Responsibility |
|---|---|
| `src/deploy_workflow/signal/store.py` (modify) | migration 3 |
| `src/deploy_workflow/signal/groups.py` | groups, members, group topics, `can_see`, `can_manage` |
| `src/deploy_workflow/signal/threads.py` | threads, comments, reactions, read marks, unread counts, text cleaning |
| `src/deploy_workflow/signal/ingest.py` (modify) | post a new story into groups that carry a matching topic |
| `src/deploy_workflow/signal/feedview.py` (modify) | thread chips and the shared line on cards; `shared` filter; groups in For you |
| `src/deploy_workflow/signal/service.py` (modify) | routes |
| `src/deploy_workflow/signal/web/render.js`, `render.test.cjs`, `signal.js`, `signal.css`, `index.html` (modify) | page |
| `tests/test_signal_groups.py`, `test_signal_threads.py`; additions to `test_signal_feedview.py`, `test_signal_ingest.py`, `test_signal_service.py`, `test_signal_page_browser.py` | tests |

Shared test helper, written in Task 1 in `tests/test_signal_groups.py` and imported by later test files: `team_db(tmp_path)` returns a database with users `ak` (writer), `ml` (writer), `rd` (reader); two approved sources (1 regulator, 2 news) with one story each (ids 1, 2) published 2026-11-13 09:00 UTC; and the constants `AK = User("ak", "writer")`, `ML = User("ml", "writer")`, `RD = User("rd", "reader")`, `T0 = datetime(2026, 11, 13, 9, tzinfo=UTC)`.

---

### Task 1: Groups and membership

**Files:** modify `store.py`; create `groups.py`; test `tests/test_signal_groups.py`.

**Interfaces:**
- Consumes: `store.open_db`, `StoreError`, `_write_transaction`, `identity.User`, `identity.clean_name`, `topics`.
- Produces:
  - Migration 3, all tables (later tasks add none):
    - `groups(id, name UNIQUE COLLATE NOCASE, visibility CHECK(visibility IN ('everyone','invited')), created_by, created_at)`
    - `group_members(group_id, user_name, joined_at, UNIQUE(group_id, user_name))`
    - `group_topics(group_id, topic_id, UNIQUE(group_id, topic_id))`
    - `threads(id, group_id, story_id NULL, title NULL, started_by NULL, created_at, last_activity_at, UNIQUE(group_id, story_id), CHECK((story_id IS NULL) <> (title IS NULL)))`
    - `comments(id, thread_id, parent_id NULL, author, text, created_at, edited_at NULL, deleted_at NULL)`
    - `reactions(comment_id, user_name, key, UNIQUE(comment_id, user_name, key))`
    - `read_marks(user_name, thread_id, seen_comment_id, UNIQUE(user_name, thread_id))`
    - indexes: `threads(group_id, last_activity_at, id)`, `threads(story_id)`, `comments(thread_id, id)`, `comments(parent_id)`, `group_members(user_name)`.
  - `groups.Forbidden(Exception)` — the user may not do this; the service answers 403.
  - `groups.VISIBILITIES = ("everyone", "invited")`, `groups.MAX_NAME = 60`.
  - `groups.create_group(db, user: User, name: str, visibility: str, topic_ids: Sequence[int], now: datetime) -> int` — writer or owner, else `Forbidden`; name cleaned like a display name, 1 to 60, unique ignoring case, else `StoreError`; unknown topic id is `StoreError`; the creator becomes a member.
  - `groups.can_see(db, user_name: str, group_id: int) -> bool` — the group exists and is `everyone`, or the user is a member.
  - `groups.require_visible(db, user_name: str, group_id: int) -> sqlite3.Row` — the group row, or `StoreError("no such group")` for both missing and hidden.
  - `groups.can_manage(db, user: User, group_id: int) -> bool` — writer or owner, and `can_see`.
  - `groups.join(db, user_name, group_id, now) -> None` — `everyone` groups only (an invited or missing group is `StoreError("no such group")` unless already a member); idempotent. `groups.leave(db, user_name, group_id) -> None` — idempotent.
  - `groups.add_member(db, actor: User, group_id, name: str, now) -> str` (returns the cleaned name) and `groups.remove_member(db, actor: User, group_id, name: str) -> None` — `require_visible` first, then `can_manage` else `Forbidden`; idempotent.
  - `groups.list_groups(db, user_name: str) -> list[sqlite3.Row]` — visible groups only, by name; columns `id, name, visibility, member (0/1), members, threads`.
  - `groups.members(db, user_name: str, group_id: int) -> list[str]` — `require_visible`; names in join order.

- [ ] **Step 1: Write the failing tests** (`team_db` helper first)

```python
def test_a_writer_creates_a_group_and_is_its_first_member(db):
    gid = create_group(db, AK, "  TMT analysts ", "everyone", [], T0)
    assert [tuple(r) for r in list_groups(db, "ak")] == [(gid, "TMT analysts", "everyone", 1, 1, 0)]
    assert members(db, "rd", gid) == ["ak"]

@pytest.mark.parametrize("user", [RD, User("nobody", "reader")])
def test_a_reader_cannot_create_a_group(db, user):
    with pytest.raises(Forbidden):
        create_group(db, user, "X", "everyone", [], T0)
    assert count(db, "groups") == 0

@pytest.mark.parametrize("name,visibility,topics", [("", "everyone", []), ("x" * 61, "everyone", []),
                                                    ("ok", "secret", []), ("ok", "everyone", [99])])
def test_bad_group_input_is_refused(db, name, visibility, topics):
    with pytest.raises(StoreError):
        create_group(db, AK, name, visibility, topics, T0)

def test_group_names_are_unique_ignoring_case(db):
    create_group(db, AK, "TMT", "everyone", [], T0)
    with pytest.raises(StoreError):
        create_group(db, ML, "tmt", "invited", [], T0)

def test_an_invited_group_is_invisible_to_non_members(db):
    gid = create_group(db, AK, "Deal team", "invited", [], T0)
    assert list_groups(db, "ml") == [] and not can_see(db, "ml", gid)
    for call in (lambda: require_visible(db, "ml", gid), lambda: members(db, "ml", gid),
                 lambda: join(db, "ml", gid, T0), lambda: add_member(db, ML, gid, "ml", T0)):
        with pytest.raises(StoreError, match="^no such group$"):
            call()
    with pytest.raises(StoreError, match="^no such group$"):
        require_visible(db, "ml", 999)                       # same text as a missing group
    assert add_member(db, AK, gid, " ml ", T0) == "ml" and can_see(db, "ml", gid)

def test_a_reader_member_cannot_add_or_remove_members(db):
    gid = create_group(db, AK, "Deal team", "invited", [], T0)
    add_member(db, AK, gid, "rd", T0)
    for call in (lambda: add_member(db, RD, gid, "x", T0), lambda: remove_member(db, RD, gid, "ak")):
        with pytest.raises(Forbidden):
            call()
    assert members(db, "rd", gid) == ["ak", "rd"]

def test_join_and_leave_are_idempotent_and_open_groups_only(db):
    gid = create_group(db, AK, "TMT", "everyone", [], T0)
    join(db, "rd", gid, T0); join(db, "rd", gid, T0); assert members(db, "ak", gid) == ["ak", "rd"]
    leave(db, "rd", gid); leave(db, "rd", gid); assert members(db, "ak", gid) == ["ak"]

def test_migration_3_applies_to_a_slice_2_database_and_keeps_its_rows(tmp_path): ...
    # build with MIGRATIONS[:2], add a story and a save, reopen with all three; both rows remain

@given(st.text(max_size=80))
def test_any_group_name_is_stored_cleaned_or_refused(name): ...
    # never an exception other than StoreError; a stored name equals identity.clean_name(name)
```

- [ ] **Step 2:** Run `uv run pytest tests/test_signal_groups.py -q`; expect failures on the missing module.
- [ ] **Step 3:** Add migration 3 and `groups.py` to the interfaces above. Each write in one `_write_transaction`.
- [ ] **Step 4:** Run the tests and `tests/test_signal_store.py`; expect pass. Run the quality gate.
- [ ] **Step 5:** Commit `feat(signal): groups, membership and the visibility rule`.

### Task 2: Threads, comments and reactions

**Files:** create `threads.py`; modify `ingest.py`; tests `tests/test_signal_threads.py`, additions to `tests/test_signal_ingest.py`.

**Interfaces:**
- Consumes: Task 1; `topics.match_story` (returns topic ids).
- Produces:
  - `threads.EDIT_WINDOW = timedelta(minutes=15)`, `MAX_TEXT = 4000`, `MAX_TITLE = 120`, `MAX_COMMENTS = 500`, `REACTIONS = ("up", "eyes", "check", "question")`.
  - `threads.clean_text(raw: str, limit: int) -> str` — drop characters of category Cc (except `\n`), Cf and Cs; `\r\n` and `\r` become `\n`; NFC; strip; `StoreError` when empty or longer than `limit` (never cut silently).
  - `threads.share_story(db, user: User, group_id: int, story_id: int, note: str | None, now) -> tuple[int, bool]` — `(thread_id, joined)`; `joined` is True when the thread already existed. `require_visible`, then writer else `Forbidden`; unknown story is `StoreError`; a note (when not None and not blank) becomes a comment. One thread per story per group, including under two simultaneous calls (rely on the `UNIQUE` constraint inside one write transaction, not on a read-then-insert).
  - `threads.start_note(db, user: User, group_id: int, title: str, text: str, now) -> int` — the text is the thread's first comment.
  - `threads.auto_post(db, story_id: int, topic_ids: Sequence[int], now) -> list[int]` — for each group carrying one of the topics, a thread for the story with `started_by` NULL unless one exists; returns the new thread ids.
  - `ingest._match_new` calls `auto_post` with the ids `match_story` returned.
  - `threads.add_comment(db, user: User, thread_id: int, text: str, parent_id: int | None, now) -> int` — thread visible (else `StoreError("no such thread")`), writer else `Forbidden`; `parent_id` must be a top-level comment of the same thread, else `StoreError`; a removed parent is allowed; the 501st comment is `StoreError("this thread is full")`; sets the thread's `last_activity_at`.
  - `threads.edit_comment(db, user: User, comment_id: int, text: str, now) -> None` — author only, not removed, `now - created_at <= EDIT_WINDOW`, else `Forbidden`; sets `edited_at`. `threads.delete_comment(db, user: User, comment_id: int, now) -> None` — author only (no time limit); sets `deleted_at`, empties `text`, deletes its reactions; idempotent. A comment the user cannot see is `StoreError("no such comment")` in both.
  - `threads.react(db, user: User, comment_id: int, key: str) -> None`, `threads.unreact(...)` — writer else `Forbidden`; key in `REACTIONS` else `StoreError`; removed comment is `StoreError`; a comment the user cannot see is `StoreError("no such comment")`, checked before the role; idempotent.
  - Read side (frozen dataclasses): `Comment(id, parent_id, author, role, text, created_at, edited, removed, reactions: tuple[Reaction(key, count, mine), ...], mine: bool, editable: bool)`; `ThreadView(id, group_id, group, story: feedview.Card | None, title: str | None, started_by: str | None, comments: tuple[Comment, ...], can_post: bool)`; `ThreadRow(id, kind: "story"|"note", title, source: str | None, started_by, comments: int, last_activity_at, unread: bool)`.
  - `threads.read_thread(db, user: User, thread_id: int, now) -> ThreadView`; `threads.thread_list(db, user_name: str, group_id: int, before: str | None) -> tuple[tuple[ThreadRow, ...], str | None]` — 30 per page, cursor as `feedview` (`<last_activity_at>,<id>`).
  - `role` on a comment is the author's current role from `store.role_of`.

- [ ] **Step 1: Write the failing tests**

```python
def test_first_share_starts_a_thread_and_a_second_share_joins_it(db, gid):       # gid: "TMT", everyone, by AK
    assert share_story(db, AK, gid, 1, "Heavier than we assumed.", T0) == (1, False)
    assert share_story(db, ML, gid, 1, None, T0 + MIN) == (1, True)
    assert share_story(db, ML, gid, 1, "Agree.", T0 + 2 * MIN) == (1, True)
    view = read_thread(db, RD, 1, T0 + 3 * MIN)
    assert [(c.author, c.text) for c in view.comments] == [("ak", "Heavier than we assumed."), ("ml", "Agree.")]
    assert view.story.id == 1 and view.started_by == "ak" and view.can_post is False

def test_two_shares_at_once_make_one_thread(tmp_path): ...
    # two threads, each with its own connection, released by one threading.Barrier; count(threads) == 1,
    # exactly one call returned joined False, neither raised

def test_a_reader_cannot_share_post_react_edit_or_delete(db, gid):
    tid, _ = share_story(db, AK, gid, 1, "note", T0)
    for call in (lambda: share_story(db, RD, gid, 2, None, T0), lambda: start_note(db, RD, gid, "T", "x", T0),
                 lambda: add_comment(db, RD, tid, "x", None, T0), lambda: react(db, RD, 1, "up"),
                 lambda: edit_comment(db, RD, 1, "x", T0), lambda: delete_comment(db, RD, 1, T0)):
        with pytest.raises(Forbidden):
            call()
    assert count(db, "threads") == 1 and count(db, "comments") == 1 and count(db, "reactions") == 0

def test_an_invited_groups_thread_does_not_exist_for_a_non_member(db):
    gid = create_group(db, AK, "Deal team", "invited", [], T0)
    tid, _ = share_story(db, AK, gid, 1, "private", T0)
    for call in (lambda: read_thread(db, ML, tid, T0), lambda: add_comment(db, ML, tid, "x", None, T0),
                 lambda: read_thread(db, ML, 999, T0)):
        with pytest.raises(StoreError, match="^no such thread$"):
            call()
    with pytest.raises(StoreError, match="^no such comment$"):
        react(db, ML, 1, "up")
    with pytest.raises(StoreError, match="^no such group$"):
        thread_list(db, "ml", gid, None)

def test_replies_nest_one_level(db, gid):
    tid, _ = share_story(db, AK, gid, 1, "top", T0)                       # comment 1
    r = add_comment(db, ML, tid, "reply", 1, T0)                          # comment 2
    with pytest.raises(StoreError):
        add_comment(db, AK, tid, "reply to a reply", r, T0)
    other, _ = share_story(db, AK, gid, 2, "other thread", T0)            # comment 3
    with pytest.raises(StoreError):
        add_comment(db, AK, other, "wrong thread", 1, T0)
    delete_comment(db, AK, 1, T0)
    assert add_comment(db, ML, tid, "after removal", 1, T0) == 4          # a removed parent still takes replies

@pytest.mark.parametrize("after,allowed", [(timedelta(minutes=15), True), (timedelta(minutes=15, seconds=1), False)])
def test_the_edit_window_is_15_minutes_inclusive(db, gid, after, allowed): ...
    # allowed: text replaced, view comment.edited True; refused: Forbidden, text unchanged

def test_only_the_author_edits_or_deletes_and_a_removed_comment_keeps_its_place(db, gid):
    tid, _ = share_story(db, AK, gid, 1, "mine", T0)
    react(db, ML, 1, "eyes")
    for call in (lambda: edit_comment(db, ML, 1, "x", T0), lambda: delete_comment(db, ML, 1, T0)):
        with pytest.raises(Forbidden):
            call()
    delete_comment(db, AK, 1, T0 + timedelta(days=30)); delete_comment(db, AK, 1, T0 + timedelta(days=30))
    c = read_thread(db, AK, tid, T0).comments[0]
    assert (c.removed, c.text, c.reactions, c.author) == (True, "", (), "ak")
    assert rows(db, "SELECT text FROM comments WHERE id=1") == [("",)]   # the text is gone from the store

def test_reactions_are_a_fixed_set_counted_per_key_and_idempotent(db, gid): ...
    # react up twice by ak, up by ml, eyes by ml -> (("up", 2, True), ("eyes", 1, False)) for ak, in REACTIONS order;
    # key "fire" is StoreError; unreact twice leaves count 1

@pytest.mark.parametrize("raw,stored", [("  hi \r\n there\x00‮ ", "hi \n there"), ("é", "é")])
def test_text_is_cleaned(raw, stored): assert clean_text(raw, MAX_TEXT) == stored

@pytest.mark.parametrize("raw", ["", "   ", "​", "x" * 4001])
def test_empty_or_oversized_text_is_refused(raw):
    with pytest.raises(StoreError):
        clean_text(raw, MAX_TEXT)

def test_markup_is_stored_as_typed(db, gid):
    tid = start_note(db, AK, gid, "<b>t</b>", '<img src=x onerror=alert(1)> javascript:alert(1)', T0)
    view = read_thread(db, AK, tid, T0)
    assert view.title == "<b>t</b>" and view.comments[0].text.startswith("<img")

def test_the_501st_comment_is_refused(db, gid): ...
def test_thread_list_is_by_last_activity_and_pages_by_30(db, gid): ...   # 31 note threads; a comment on the oldest moves it first

def test_a_new_story_posts_into_groups_that_carry_its_topic_with_recorded_feed(db): ...
    # topic "Competition" (keyword "merger review"); group G1 with the topic, G2 without; run_due with the RSS
    # fixture whose first item matches -> one thread in G1 with started_by NULL, none in G2; a second pass adds none

@given(st.text(max_size=200))
def test_any_text_is_cleaned_or_refused_never_an_error(raw): ...        # only StoreError; result has no Cc but "\n", Cf or Cs
```

- [ ] **Step 2:** Run; expect failures on the missing module.
- [ ] **Step 3:** Implement `threads.py` and the `ingest` call.
- [ ] **Step 4:** Run `uv run pytest tests/test_signal_threads.py tests/test_signal_ingest.py tests/test_signal_groups.py -q` and the quality gate.
- [ ] **Step 5:** Commit `feat(signal): threads, comments and reactions`.

### Task 3: Unread counts and threads on feed cards

**Files:** modify `threads.py`, `feedview.py`; tests: additions to `tests/test_signal_threads.py`, `tests/test_signal_feedview.py`.

**Interfaces:**
- Produces:
  - `threads.mark_read(db, user_name: str, thread_id: int) -> None` — thread visible else `StoreError("no such thread")`; sets the mark to the thread's highest comment id (0 for none); never lowers it.
  - `threads.Unread(replies: int, threads: int, by_group: dict[int, int])`; `threads.unread(db, user_name: str) -> Unread`:
    - `threads`: threads in groups the user is a member of, created at or after their `joined_at`, with a starter who is not the user, and no read mark.
    - `replies`: comments not removed, by another author, whose parent's author is the user, in a thread the user can see, with id above the user's mark for that thread (or no mark).
    - `by_group[g]`: both kinds counted per group; groups with zero are absent.
  - `ThreadRow.unread`: no mark, or a comment by another author above the mark.
  - `feedview.CardThread(id: int, group: str, comments: int, shared_by: str | None, note: str | None)` — `note` is the first 140 characters of the thread's first live comment by its starter. `Card.threads: tuple[CardThread, ...]` — only threads in groups the user can see, by thread id.
  - `Filters` gains `shared: NotRequired[bool]` — only stories with a thread started by someone other than the user in a group the user is a member of ("shared by colleagues").
  - View `foryou` also includes stories with a thread in a group the user is a member of. `new_count` follows the same rule.

- [ ] **Step 1: Write the failing tests**

```python
def test_unread_counts_new_threads_and_replies_and_clears_on_read(db):
    gid = create_group(db, AK, "TMT", "everyone", [], T0); join(db, "ml", gid, T0)
    tid, _ = share_story(db, AK, gid, 1, "look", T0 + MIN)                 # comment 1
    assert unread(db, "ml") == Unread(0, 1, {gid: 1}) and unread(db, "ak") == Unread(0, 0, {})
    add_comment(db, ML, tid, "reply to ak", 1, T0 + 2 * MIN)
    assert unread(db, "ak") == Unread(1, 0, {gid: 1})
    mark_read(db, "ak", tid); mark_read(db, "ml", tid)
    assert unread(db, "ak") == unread(db, "ml") == Unread(0, 0, {})

def test_threads_from_before_joining_and_automatic_threads_are_not_unread(db): ...
def test_a_removed_reply_and_my_own_reply_are_not_unread(db): ...
def test_unread_never_counts_an_invited_group_after_removal_from_it(db): ...
    # ml is added, a reply to ml arrives, ak removes ml -> unread(db, "ml") == Unread(0, 0, {})

def test_cards_carry_only_visible_threads(db):
    open_g = create_group(db, AK, "TMT", "everyone", [], T0)
    closed = create_group(db, AK, "Deal team", "invited", [], T0)
    share_story(db, AK, open_g, 1, "Heavier than we assumed.", T0); share_story(db, AK, closed, 1, "secret", T0)
    card = feed(db, "ml", "latest").cards[-1]                              # story 1
    assert card.threads == (CardThread(1, "TMT", 1, "ak", "Heavier than we assumed."),)
    assert len(feed(db, "ak", "latest").cards[-1].threads) == 2

def test_shared_filter_and_for_you_follow_membership(db): ...
    # ml not a member: shared filter empty, foryou empty; after join: both hold story 1; ak (the sharer) sees
    # story 1 in foryou but not under shared
```

- [ ] **Step 2 to 4:** Run failing, implement, run `tests/test_signal_threads.py tests/test_signal_feedview.py` and the quality gate.
- [ ] **Step 5:** Commit `feat(signal): unread counts and threads on feed cards`. Open PR 3a.

### Task 4: Routes

**Files:** modify `service.py`; tests: additions to `tests/test_signal_service.py`.

**Interfaces:**
- Produces (JSON; ids match `_ID`; every route needs a display name; writes need the same-origin rules already in place):

| Method and path | Body | Reply |
|---|---|---|
| `GET /api/groups` | | `{groups: [{id, name, visibility, member, members, threads, unread}], can_create}` |
| `POST /api/groups` | `{name, visibility, topics: [id]}` | `{id}` |
| `GET /api/groups/<id>` | | `{id, name, visibility, member, can_manage, members: [name]}` |
| `POST`, `DELETE /api/groups/<id>/members` | `{}` for oneself, `{name}` for another | `{members: [name]}` |
| `GET /api/groups/<id>/threads[?before=]` | | `{threads: [ThreadRow], next_before}` |
| `POST /api/groups/<id>/threads` | `{story_id, note?}` or `{title, text}` | `{thread_id, joined}` |
| `GET /api/threads/<id>` | | `ThreadView` as JSON |
| `POST /api/threads/<id>/read` | `{}` | `{unread: Unread}` |
| `POST /api/threads/<id>/comments` | `{text, parent?}` | `{id}` |
| `POST`, `DELETE /api/comments/<id>` | `{text}` / none | `{}` |
| `POST`, `DELETE /api/comments/<id>/reactions/<key>` | none | `{}` (`<key>` matches `[a-z]{1,12}`) |
| `GET /api/unread` | | `{replies, threads, total, by_group}` |
| `GET /api/feed` | adds `shared=1` | cards gain `threads` |

- Status mapping, one place: `groups.Forbidden` → 403 `{"error": "<text>"}`; `StoreError` whose text starts `no such` → 404; any other `StoreError` → 400; a body that is not a JSON object, or a field of the wrong type → 400. The 404 body for a hidden group, thread or comment is byte-for-byte the body for a missing one.
- `GET /api/threads/<id>` does not write; reading is recorded only by the `read` route.

- [ ] **Step 1: Write the failing tests** (use the file's existing `call`/server fixtures; the user is set by the `signal_name` cookie)

```python
def test_a_writer_creates_a_group_shares_a_story_and_a_reader_reads_the_thread_with_recorded_feed(site): ...
    # POST /api/groups as ak -> 200 {id: 1}; POST /api/groups/1/threads {story_id: 1, note: "look"} -> {thread_id: 1, joined: false};
    # GET /api/threads/1 as rd -> 200, comments[0].text == "look", can_post false; GET /api/feed?view=latest as rd ->
    # the card for story 1 has threads == [{id: 1, group: "TMT", comments: 1, shared_by: "ak", note: "look"}]

@pytest.mark.parametrize("method,path,body", WRITES)     # every POST and DELETE route in the table, with a valid body
def test_a_reader_is_refused_every_write_and_nothing_changes(site, method, path, body): ...
    # as rd and as an unknown name: 403; row counts of groups, group_members, threads, comments, reactions unchanged.
    # Exceptions, stated in the test: POST/DELETE members with {} on an everyone-group (self join/leave) and
    # POST /api/threads/<id>/read are open to readers and answer 200.

@pytest.mark.parametrize("method,path,body", WRITES)
def test_every_write_without_this_sites_origin_is_refused(site, method, path, body): ...     # 403, nothing changes

@pytest.mark.parametrize("path", HIDDEN_READS + HIDDEN_WRITES)   # every route, on an invited group's ids, as non-member ml
def test_a_hidden_group_answers_exactly_like_a_missing_one(site, path): ...
    # status 404 and body equal to the same route called with id 999999; /api/groups and /api/unread as ml
    # contain neither the group's id nor its name; /api/feed cards carry no thread of it

@pytest.mark.parametrize("body", [b"[]", b'{"text": 5}', b'{"text": ""}', b'{"parent": "1", "text": "x"}', b'{"text": "' + b"x" * 4001 + b'"}'])
def test_a_malformed_comment_is_a_400_not_a_500(site, body): ...

def test_a_comment_posted_during_an_ingest_pass_succeeds_with_recorded_feed(site): ...
    # the loop's fetch function blocks on an Event mid-pass; POST a comment -> 200; release; the pass finishes ok

def test_unread_rides_the_poll_and_clears_on_read(site): ...
    # as ml (member): GET /api/unread -> total 1; POST /api/threads/1/read -> {unread: {total 0}}; GET /api/groups unread 0
```

- [ ] **Step 2 to 4:** Run failing, implement the routes in the `_ROUTES` table's existing style, run `tests/test_signal_service.py` and the quality gate.
- [ ] **Step 5:** Commit `feat(signal): group and thread routes`. Open PR 3b.

### Task 5: Page logic (pure functions)

**Files:** modify `web/render.js`, `web/render.test.cjs`.

**Interfaces:**
- Consumes: slice 2's `card`, `emptyState`, `relativeTime`, `safeLink`, `initials`, `icon`.
- Produces (each takes `document` first and returns an element; no network, no globals):
  - `linkify(document, text) -> DocumentFragment` — text nodes and `a` elements; a run matching `https?://[^\s<>"']+` is a link only if `safeLink` accepts it; trailing `.,;:!?)` stays outside the link; newlines become `br`.
  - `comment(document, c, now) -> HTMLElement` — avatar, name, role tag (writers and the owner), time, "edited" tag, text via `linkify`, reaction chips (`button`, `aria-pressed`), Reply, and Edit/Delete only when `c.mine` (Edit only when `c.editable`); a removed comment is the one-line placeholder "This comment was removed." with no buttons.
  - `threadPanel(document, view, now) -> HTMLElement` — header, quote block or note title, comments with replies under their parent, a day divider when the date changes, and either the reply box (`view.can_post`) or the reader note.
  - `threadRow(document, row, now)`, `groupItem(document, group)`, `sharedLine(document, cardThread)`, `threadChips(document, card)`.
  - `card` gains the shared line (first thread with a `shared_by`), thread chips and the "Share to group" button.

- [ ] **Step 1: Write the failing tests** in `render.test.cjs` (the file's existing minimal DOM):

```js
test('linkify links only http and https and keeps punctuation outside', () => {
  const f = R.linkify(doc, 'see https://a.org/x). and javascript:alert(1) and <b>');
  assert.deepEqual(links(f), ['https://a.org/x']);
  assert.equal(f.textContent, 'see https://a.org/x). and javascript:alert(1) and <b>');
  assert.equal(elementsNamed(f, 'b').length, 0);
});
test('a link opens in a new tab without an opener', ...);            // target _blank, rel "noopener noreferrer"
test('newlines become line breaks', ...);
test('a removed comment shows the placeholder and no controls', ...);
test('edit and delete appear only on my comments, edit only while editable', ...);
test('a reaction chip states its count and pressed state', ...);     // text "👍 2", aria-pressed "true", aria-label "Thumbs up, 2"
test('replies render under their parent, one level', ...);
test('a reader gets the note in place of the reply box', ...);       // exact text from the mockup
test('a card shows who shared it where with the note and a chip per thread', ...);
test('markup in a group name, title, note or comment is text', ...); // no element created from data
```

- [ ] **Step 2 to 4:** Run `node --test src/deploy_workflow/signal/web/render.test.cjs` failing, implement, run passing.
- [ ] **Step 5:** Commit `feat(signal): thread, comment and group rendering`.

### Task 6: Page wiring

**Files:** modify `web/index.html`, `web/signal.js`, `web/signal.css`.

**Interfaces:**
- Consumes: Task 4's routes, Task 5's functions.
- Produces:
  - Channel list: a Groups section (from `GET /api/groups`) with unread badges; "New group" for writers; the rail badge shows `total` from `GET /api/unread`, fetched on the existing 45-second poll.
  - Address: the view and open thread are kept in the hash (`#group=3`, `#thread=12`) so a reload and the Back button restore them; an id that answers 404 shows the view's empty state, not an error band.
  - Group view: members strip, thread rows, "Start a note" for writers, paging by `next_before`.
  - Thread panel: opens beside the feed at desktop width and over it under 900 px; opening calls the `read` route and updates badges; re-read every 45 seconds and on `visibilitychange` while open; the scroll position and a draft in the reply box survive a re-read.
  - Reply box: Enter adds a line, Ctrl/Cmd+Enter sends; the button shows a sending state and is disabled while sending; a refused send keeps the draft and shows the server's line; the counter appears at 3,800 characters.
  - Share dialog and New group dialog as native `dialog` elements; both state the identity limit in one sentence: "Names are not checked: anyone on this network can post under any name."
  - Edit in place (the comment becomes a text area with Save and Cancel); Delete asks once with a native `confirm`.
  - Focus: opening a dialog or the panel moves focus in; closing returns it to the opener; after a send, focus stays in the reply box.
- No inline script or style; the content security policy is unchanged.

- [ ] **Step 1:** Controller reads the live library pages for the components in the screen map and adds them to the brief.
- [ ] **Step 2:** Implement. There is no unit test at this layer; Task 7 is its proof. Run the node tests and the quality gate.
- [ ] **Step 3:** Start the service on a scratch root (`.claude/launch.json` "signal") and check each row of the screen map by hand in the preview at 1280 and 375 px, light theme; fix what is wrong.
- [ ] **Step 4:** Commit `feat(signal): groups and threads on the page`. Open PR 3c.

### Task 7: Browser proof and records

**Files:** modify `tests/test_signal_page_browser.py`, `tests/browser_signal_driver.cjs` (only if a new driver verb is needed), `README.md`, `VERIFICATION.md`; add `docs/design/mockups/signal-slice3-*.png`.

- [ ] **Step 1: Browser tests** (`pytest.mark.browser`, real service, recorded feeds, headless Chrome):

```python
def test_a_writer_shares_a_story_and_the_thread_opens_with_the_note(...)          # card shows the shared line and a chip
def test_a_reply_and_a_reaction_appear_without_a_reload_for_a_second_user(...)    # two browser contexts; the 45 s timer is driven by visibilitychange
def test_a_reader_sees_the_thread_and_the_note_instead_of_the_reply_box(...)
def test_hostile_comment_text_is_inert_and_only_the_https_address_is_a_link(...)   # no dialog, no new element, one <a>
def test_an_invited_group_is_absent_for_a_non_member_and_its_thread_address_shows_the_empty_state(...)
def test_edit_within_the_window_marks_the_comment_edited_and_delete_leaves_the_placeholder(...)
def test_the_unread_badge_counts_a_reply_and_clears_when_the_thread_is_opened(...)
def test_a_reload_restores_the_open_thread_and_back_closes_it(...)
def test_keyboard_alone_shares_replies_and_closes_with_focus_returned(...)
def test_contrast_of_thread_text_role_tags_and_reaction_chips(...)                 # at least 4.5:1
def test_at_375_px_the_thread_covers_the_feed_and_nothing_scrolls_sideways(...)
def test_the_policy_is_still_exact_and_a_thread_visit_logs_nothing(...)
def test_screenshots_of_the_group_view_and_thread_at_1280_and_375(...)
```

- [ ] **Step 2:** Run `uv run pytest tests/test_signal_page_browser.py -q -m browser` and the whole `tests/test_signal_*.py` set; all pass.
- [ ] **Step 3:** README Signal section: groups, threads, the powers, the limits (names are not checked, so writer actions and invited groups are only as private as the network; 500 comments a thread; no comment search; no per-group rules until settings).
- [ ] **Step 4:** VERIFICATION.md entry (keep the file under 1,000 lines; trim the oldest entry if needed): scope "offline, recorded feeds, headless Chrome on macOS", test counts, gate results, `Not verified:`.
- [ ] **Step 5:** Commit `test(signal): browser proof for groups and threads; records`. Open PR 3d.
- [ ] **Step 6:** Whole-branch review of the four PRs' combined diff (`mx-architect` running `adversarial-reviewer`), after `/sweep refactoring discover changed-update`.

## Not in this slice

Settings pages, per-group thread rules, archiving, notification switches and "pin to the top" (slice 4); AI line, signal bars, Top order (slice 5); digests (slice 6); login (landing-page project); comment search; mentions; file attachments.

## Not verified by this plan

Component choices from the approved libraries (read at brief time, Task 6 Step 1); Windows; browsers other than Chrome; screen readers.
