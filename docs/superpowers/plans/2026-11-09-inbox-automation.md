# Inbox Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An analyst copies an issuer folder into `inbox/<pathway>/` on a shared folder; a watcher starts the paid run within a USD 20 cap, the library shows its progress, and the report is filed under the issuer's folder.

**Architecture:** One long-running Python process (`deploy_workflow.inbox.watcher`) polls the inbox, moves each ready drop out of it, and starts the existing launcher (`cpos_launch`) as a child process per run. It keeps one JSON record per drop, writes a small `activity.js` the library page re-loads, and rebuilds the library only when a run ends. CP-OS stays the only orchestrator; the watcher never orders or runs modules.

**Tech Stack:** Python 3.13 standard library only (`subprocess`, `ctypes`, `json`, `pathlib`); the existing launcher, `update_library.py` and Credit OS page (plain JS, tested with `node --test`). No new dependency.

**Spec:** `docs/superpowers/specs/2026-11-09-inbox-automation-design.md`

## Global Constraints

- No new dependency. No credential files: the provider key comes only from the watcher's environment.
- Cap `Decimal("20")` per run; config `sol-medium`; at most 3 runs at once; at most 30 runs started per local calendar day; a drop is ready after 120 s unchanged; poll every 10 s. All six are watcher settings with these defaults.
- The launcher's ruling check is not removed or bypassed. Every live launch passes `docs/rulings/2026-11-09-inbox-automation.md`.
- Only the watcher writes `_engine/`, `issuers/` and `library.html`. A filed report is never overwritten. A run folder's delivered report is never changed.
- Text from an analyst or a model (folder names, issuer names, reasons) is escaped before it reaches a page.
- No stub or fake value stands in for real behaviour. No catch-all that hides a failure unless the fail-open is documented and logged. Each task's test assertions are its answer key: the implementer does not edit or weaken them.
- Per task run only that task's tests (`uv run pytest tests/<file> -q`, `node --test <file>`), then `uv run python tools/quality_gate.py`. Every task report ends with a `Not verified:` line.
- Sensitive code (spend limits, ordering, concurrency, escaping): Tasks 2, 4, 5, 6 and 7 get an `mx-adversary` review as well as the task review.
- Ship as three stacked PRs to stay under 800 changed lines each: A = Tasks 1–3, B = Tasks 4, 5 and 7, C = Tasks 6, 8 and 9.
- Commit messages end with `Co-Authored-By: Claude <noreply@anthropic.com>`.

## Shared-folder layout (fixed by this plan)

```
<root>/                         MAX_ROOT = 80 characters
├─ library.html                 redirect to _engine/library/index.html
├─ inbox/<pathway>/             six pathway folders, each with _template/context-form.html
├─ inbox/failed/<time> <name>/  rejected drops, each with WHY.txt
├─ issuers/<Issuer name> (<issuer_id>)/<as-of> <pathway>[-N].html
└─ _engine/                     the library's "workspace"
   ├─ runs/<claim-id>/          launcher --out; claim-id = YYYYMMDD-HHMMSS-NN (UTC)
   ├─ drops/<claim-id>/         the moved drop (sources + context)
   ├─ state/<claim-id>.json     one record per drop; state/issuers.json
   ├─ logs/<claim-id>.log, logs/watcher.log
   ├─ library/                  built by update_library.py, unchanged layout
   └─ activity.js               window.RUN_ACTIVITY=…; rewritten on every change
```

Two deliberate differences from the spec's wording: the drop moves to `_engine/drops/<claim-id>/`, not inside the run folder (the launcher owns the run folder's contents), and the run folder is named by a timestamp claim ID, not by issuer (the ID is needed before the context is read).

## Review Focus

1. **The context file has another name, or the drop holds other JSON files.** Expected: the context is the one top-level `.json` file that carries the `context/1` schema marker; other JSON files are sources. → Task 2.
2. **A drop holds only files the launcher ignores** (`~$` Office lock files, names starting `_` or `.`, unsupported types). Expected: rejected with "no source file the launcher can read", not a run on nothing. → Task 2.
3. **A run stops producing events** (provider stall). Expected: after 60 minutes without a new event the run shows as "stalled" in Run activity; it still holds its slot and is not killed. → Task 5.
4. **A state or activity write fails** (disk full, file held open by a reader). Expected: the watcher logs it to `logs/watcher.log`, keeps running, and retries on the next poll; no run is lost or started twice. → Task 7.
5. **The same folder name arrives twice**, in one pathway or two, while the first is still running. Expected: two separate runs and no collision anywhere. → Task 2 and Task 7.

---

### Task 1: Rules, standing ruling, launcher `--no-library`

**Files:**
- Modify: `AGENTS.md` (the "Paid execution is a separate, explicit action" bullet)
- Create: `docs/rulings/2026-11-09-inbox-automation.md`
- Modify: `.gitignore` (add `.superpowers/`)
- Modify: `src/deploy_workflow/owners/cpos_launch.py` (`_parser`, `main`)
- Test: `tests/test_cpos_launch.py`

**Interfaces:**
- Produces: launcher flag `--no-library` (skips `_refresh_library`); the ruling path above.

- [ ] **Step 1: Write the failing test** in `tests/test_cpos_launch.py`

```python
def test_no_library_flag_is_accepted_and_defaults_off():
    base = ["--context", "c.json", "--sources", "s", "--config", "sol-medium", "--cap", "20"]
    assert cpos_launch._parser().parse_args(base).no_library is False
    assert cpos_launch._parser().parse_args([*base, "--no-library"]).no_library is True

def test_standing_ruling_lifts_the_pause_for_sol_medium_only():
    ruling = cpos_launch.ROOT / "docs/rulings/2026-11-09-inbox-automation.md"
    check_ruling("sol-medium", ruling)
    with pytest.raises(LivePauseInForce):
        check_ruling("sol-high", ruling)
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_launch.py -q -k "no_library or standing_ruling"` — Expected: FAIL (no attribute `no_library`; ruling unreadable).
- [ ] **Step 3: Add `--no-library`** (`action="store_true"`, help "do not rebuild the library; the inbox watcher does"). In `main`, call `_refresh_library` only when it is not set.
- [ ] **Step 4: Write the ruling.** Exactly one each of `lifts: live-provider-pause`, `by: user`, `date: 2026-11-09`, `configs: sol-medium`. Body: the owner's words, quoted ("this is a different build, those rules are subject to change. analysts will provide the files. budget limit and no approvals. this is automated workflow." and "$20 cap per run"); scope: live launches started by `deploy_workflow.inbox.watcher` from a folder dropped into `inbox/<pathway>/`, USD 20 per run folder, key from the watcher's environment only.
- [ ] **Step 5: Edit `AGENTS.md`.** Replace the last sentence of the credentials bullet with: "Paid execution is a separate, explicit action after offline readiness. For the inbox watcher (`deploy_workflow.inbox.watcher`) the explicit action is an analyst placing a folder in `inbox/<pathway>/`, under the standing ruling `docs/rulings/2026-11-09-inbox-automation.md` and a USD 20 cap per run (owner, 2026-11-09). The build itself does not run providers."
- [ ] **Step 6: Run the tests** — Expected: PASS. Run `uv run python tools/quality_gate.py` — Expected: exit 0.
- [ ] **Step 7: Commit** `feat(launch): --no-library; standing ruling and rule for the inbox watcher`

---

### Task 2: Drops — layout, readiness, claim, check, reject

**Files:**
- Create: `src/deploy_workflow/inbox/__init__.py` (empty), `src/deploy_workflow/inbox/drops.py`
- Test: `tests/test_inbox_drops.py`

**Interfaces:**
- Consumes: `deploy_vii.contracts.PATHWAY_MODULES`; `deploy_workflow.context.load_context`, `SCHEMA`, `RunContext`; `cpos_launch.SOURCE_SUFFIXES`.
- Produces:

```python
PATHWAYS: tuple[str, ...]            # tuple(PATHWAY_MODULES)
MAX_ROOT = 80

@dataclass(frozen=True)
class Layout:
    root: Path
    # properties: inbox, failed, issuers, engine, runs, drops, state, logs (paths in the layout above)

def ensure_layout(root: Path) -> Layout            # creates every folder; ValueError if len(str(root.resolve())) > MAX_ROOT
def signature(entry: Path) -> tuple[tuple[str, int, int], ...]   # sorted (relative posix path, size, mtime_ns); a file is one row
def unlocked(path: Path) -> bool
class ReadyTracker:
    def __init__(self, settle_seconds: float, clock: Callable[[], float]) -> None
    def ready(self, entry: Path) -> bool
def candidates(layout: Layout) -> list[tuple[str, Path]]         # (pathway, entry); pathway "" for a stray entry
def claim(layout: Layout, entry: Path, claim_id: str) -> Path | None
class DropRejected(ValueError): ...
@dataclass(frozen=True)
class Checked:
    context: Path
    run: RunContext
    files: tuple[str, ...]                                         # readable sources, relative posix paths, sorted
def check(drop: Path, pathway: str) -> Checked
def reject(layout: Layout, drop: Path, name: str, reason: str, now: datetime) -> Path
```

Decisions the tests do not fully determine:
- **Readiness uses the watcher's own clock, not file times.** A Windows copy keeps the source's old modified time, so "modified more than 2 minutes ago" is true for a half-copied folder. `ReadyTracker` remembers each entry's signature and when it first saw that signature; `ready` is true when the signature has been the same for `settle_seconds` **and** `unlocked` is true for every file.
- `unlocked` opens the file `r+b`. It returns `False` only for an `OSError` whose `winerror` is 32 or 33 (sharing or lock violation). Any other error (a read-only file) falls back to opening `rb`; `False` only if that fails too.
- `candidates` lists every entry in each `inbox/<pathway>/` except `_template`, plus every entry directly in `inbox/` that is not a pathway folder or `failed`; those strays get pathway `""`.
- `claim` is one `os.rename` to `drops/<claim_id>`; it returns `None` on `OSError` (still held open, or already taken).
- `check` rejects, with these exact reasons: pathway `""` → `"not inside a pathway folder"`; a file, not a folder → `"not a folder"`; no context → `"no context file"`; more than one → `"more than one context file: <names>"`; `load_context` refusal → `"context file: <the refusal text>"`; `run.run.pathway != pathway` → `"context names pathway <x>, dropped in <pathway>"`; no readable source → `"no source file the launcher can read"`. A context file is a top-level `*.json` that parses to an object whose `"schema"` value equals `context.SCHEMA` (`"context/1"`). A readable source has a suffix in `SOURCE_SUFFIXES`, is not the context, and no path part starts with `.`, `_` or `~$` (the launcher's own rule in `_issuer_files`).
- `reject` moves the drop to `inbox/failed/<YYYY-MM-DD HHMMSS> <name>/`, adding ` (2)`, ` (3)` if that exists, and writes `WHY.txt` there (UTF-8, the reason and one line saying to fix the folder and drop it again).

- [ ] **Step 1: Write the failing tests** in `tests/test_inbox_drops.py`. A helper `drop(tmp, pathway, name, files)` builds a drop; `CONTEXT` is a valid `context/1` body taken from an existing fixture under `tests/fixtures`, with `run.pathway` set per test.

```python
def test_layout_refuses_a_long_root(tmp_path):
    with pytest.raises(ValueError):
        ensure_layout(tmp_path / ("x" * 90))

def test_not_ready_until_unchanged_for_the_settle_time(layout):
    now = [0.0]; tracker = ReadyTracker(120, lambda: now[0])
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    assert tracker.ready(entry) is False
    now[0] = 119; assert tracker.ready(entry) is False
    (entry / "b.pdf").write_bytes(b"2")            # the copy is still arriving
    now[0] = 200; assert tracker.ready(entry) is False
    now[0] = 320; assert tracker.ready(entry) is True

def test_old_file_times_do_not_make_a_fresh_drop_ready(layout):
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    os.utime(entry / "a.pdf", (0, 0))
    assert ReadyTracker(120, lambda: 0.0).ready(entry) is False

def test_claim_moves_once(layout):
    entry = drop(layout, "credit_snapshot", "acme", {"a.pdf": b"1"})
    moved = claim(layout, entry, "20261109-134102-01")
    assert moved == layout.drops / "20261109-134102-01" and not entry.exists()
    assert claim(layout, entry, "20261109-134102-02") is None

@pytest.mark.parametrize(("files", "pathway", "reason"), [
    ({"a.pdf": b"1"}, "credit_snapshot", "no context file"),
    ({"c1.json": CTX_SNAPSHOT, "c2.json": CTX_SNAPSHOT, "a.pdf": b"1"}, "credit_snapshot", "more than one context file: c1.json, c2.json"),
    ({"context.json": CTX_SNAPSHOT, "a.pdf": b"1"}, "earnings_update", "context names pathway credit_snapshot, dropped in earnings_update"),
    ({"context.json": CTX_SNAPSHOT, "~$a.xlsx": b"1", "_notes.pdf": b"1", "x.zip": b"1"}, "credit_snapshot", "no source file the launcher can read"),
    ({"context.json": CTX_SNAPSHOT, "a.pdf": b"1"}, "", "not inside a pathway folder"),
])
def test_check_rejects_with_the_reason(tmp_path, files, pathway, reason): ...   # pytest.raises(DropRejected, match=re.escape(reason))

def test_context_may_have_any_name_and_other_json_is_a_source(tmp_path):
    checked = check(make(tmp_path, {"Acme ctx.json": CTX_SNAPSHOT, "data.json": b"{}", "a.pdf": b"1"}), "credit_snapshot")
    assert checked.context.name == "Acme ctx.json" and checked.files == ("a.pdf", "data.json")

def test_reject_keeps_two_drops_with_one_name_apart(layout):
    now = datetime(2026, 11, 9, 13, 41, 2)
    first = reject(layout, make_drop(layout, "a"), "acme", "no context file", now)
    second = reject(layout, make_drop(layout, "b"), "acme", "no context file", now)
    assert first.name == "2026-11-09 134102 acme" and second.name == "2026-11-09 134102 acme (2)"
    assert "no context file" in (first / "WHY.txt").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run** `uv run pytest tests/test_inbox_drops.py -q` — Expected: FAIL (module not found).
- [ ] **Step 3: Implement `drops.py`** to the interfaces and decisions above.
- [ ] **Step 4: Run the tests** — Expected: PASS. Quality gate — exit 0.
- [ ] **Step 5: Commit** `feat(inbox): drop layout, readiness, claim, check and reject`

---

### Task 3: Filing — safe names, issuer folders, report copies

**Files:**
- Create: `src/deploy_workflow/inbox/filing.py`
- Test: `tests/test_inbox_filing.py`

**Interfaces:**
- Consumes: `Layout` (Task 2).
- Produces:

```python
def safe_name(text: str, limit: int = 80) -> str
def issuer_folder(layout: Layout, issuer_id: str, issuer_name: str) -> tuple[Path, bool]   # (folder, name_differs)
def file_report(layout: Layout, report: Path, *, issuer_id: str, issuer_name: str, as_of: str, pathway: str) -> Path
```

Decisions:
- `safe_name`: replace each of `\ / : * ? " < > |` and control characters with a space, collapse whitespace, strip trailing dots and spaces, cut to `limit`, strip again; if the result (case-folded, before any dot) is a Windows reserved name (`CON PRN AUX NUL COM1–COM9 LPT1–LPT9`) or empty, prefix `_`.
- The registry is `_engine/state/issuers.json`: `{issuer_id: folder name}`, written with a temporary file and `os.replace`. The first run for an ID fixes the folder name `safe_name(f"{issuer_name} ({issuer_id})")`. A later call with the same ID returns that folder; `name_differs` is true when `safe_name` of the new name gives a different folder name. If a new ID's folder name is already taken by another ID, add ` 2`, ` 3`.
- `file_report` copies bytes to `<as_of> <pathway>.html`, then `<as_of> <pathway>-2.html`, `-3`, opening with mode `"xb"` so an existing file is never overwritten.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize(("raw", "safe"), [
    ("Acme Corp.", "Acme Corp"), ('A/B:C*?"<>|D', "A B C D"), ("CON", "_CON"), ("nul.txt", "_nul.txt"),
    ("  ", "_"), ("x" * 200, "x" * 80), ("../../etc", ".. .. etc"),
])
def test_safe_name(raw, safe): assert safe_name(raw) == safe

def test_one_folder_per_issuer_id(layout):
    first, differs = issuer_folder(layout, "acme", "ACME Corp")
    again, differs_again = issuer_folder(layout, "acme", "Acme Corp.")
    other, _ = issuer_folder(layout, "acme-2", "ACME Corp")
    assert first.name == "ACME Corp (acme)" and differs is False
    assert again == first and differs_again is True
    assert other.name == "ACME Corp (acme-2)" and other != first

def test_repeat_report_gets_a_suffix_and_nothing_is_overwritten(layout, tmp_path):
    report = tmp_path / "report.html"; report.write_bytes(b"one")
    kw = dict(issuer_id="acme", issuer_name="Acme", as_of="2026-11-09", pathway="earnings_update")
    first = file_report(layout, report, **kw); report.write_bytes(b"two"); second = file_report(layout, report, **kw)
    assert first.name == "2026-11-09 earnings_update.html" and first.read_bytes() == b"one"
    assert second.name == "2026-11-09 earnings_update-2.html" and second.read_bytes() == b"two"
```

- [ ] **Step 2: Run** `uv run pytest tests/test_inbox_filing.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement `filing.py`.**
- [ ] **Step 4: Run the tests** — PASS. Quality gate — exit 0.
- [ ] **Step 5: Commit** `feat(inbox): issuer folders keyed by ID; reports filed without overwrite`

---

### Task 4: Runs — records, launch, liveness, outcome

**Files:**
- Create: `src/deploy_workflow/inbox/runs.py`, `tests/fixtures/fake_launcher.py`
- Test: `tests/test_inbox_runs.py`

**Interfaces:**
- Consumes: `Layout`, `Checked` (Task 2); `deploy_workflow.run_events.read_events`, `EVENTS`.
- Produces:

```python
Status = Literal["queued", "running", "finished", "failed", "capped", "rejected", "interrupted"]

@dataclass
class Record:
    id: str; pathway: str; folder: str; status: Status; claimed_at: str
    issuer_id: str = ""; issuer_name: str = ""; as_of: str = ""; files: tuple[str, ...] = ()
    started_at: str = ""; ended_at: str = ""; pid: int = 0
    reason: str = ""; report: str = ""; name_differs: bool = False     # report: posix path relative to root

def save(layout: Layout, record: Record) -> None        # state/<id>.json; temporary file then os.replace
def load_all(layout: Layout) -> list[Record]            # sorted by id; issuers.json is skipped
def alive(pid: int) -> bool
def command(layout: Layout, record: Record, context: Path, *, launcher: Sequence[str], config: str,
            cap: Decimal, ruling: Path | None) -> list[str]
def prepare(layout: Layout, record: Record, context: Path, *, launcher, config, cap) -> str   # "" on success, else the refusal text
def start(layout: Layout, record: Record, context: Path, *, launcher, config, cap, ruling: Path) -> subprocess.Popen[bytes]
def outcome(layout: Layout, record: Record, exit_code: int | None) -> tuple[Status, str]
```

Decisions:
- `command` returns `[*launcher, "--context", <context>, "--sources", drops/<id>, "--config", config, "--cap", str(cap), "--out", runs/<id>, "--no-library"]`, plus `"--live", "--ruling", <ruling>` when `ruling` is given.
- `prepare` runs it without a ruling (`subprocess.run`, output appended to `logs/<id>.log`); a non-zero exit returns the last non-empty stderr line (or `"launcher exited <n>"`).
- `start` appends stdout and stderr to `logs/<id>.log` and passes the environment through unchanged. On Windows it sets `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` so a Ctrl-C to the watcher does not stop its runs.
- **`alive` must not use `os.kill(pid, 0)` on Windows: there it terminates the process.** On Windows use `ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)` (SYNCHRONIZE) and `WaitForSingleObject(handle, 0) == 0x102` (still running), then `CloseHandle`. Elsewhere `os.kill(pid, 0)`: `ProcessLookupError` → false, `PermissionError` → true. `pid <= 0` → false. `# ponytail: a reused process ID reads as alive; add the creation time if that ever bites.`
- `outcome` reads `runs/<id>/events.jsonl` and decides, in this order: a `delivered` event → `("finished", "")`; a `stopped` event → `("capped", "stopped at the cap")` when its `reason` is `"budget"`, else `("failed", f"stopped: {reason}")`; no such event and `exit_code` is an int → `("failed", f"launcher exited {exit_code}; see logs/{id}.log")`; `exit_code is None` (an adopted run whose process is gone) → `("interrupted", "the run's process ended without a result")`. A missing or unreadable event file counts as no events.
- `tests/fixtures/fake_launcher.py` accepts the launcher's flags. It reads `FAKE_PLAN` (JSON in the environment): `{"prepare_exit": 0, "prepare_error": "", "events": [["module_started", {"module": "CP-0"}], …], "sleep": 0.0, "exit": 0}`. Without `--live` it prints `prepare_error` to stderr and exits `prepare_exit`. With `--live` it appends each event with `run_events.append_event(out, name, **fields)`, sleeps, and exits. It calls no provider and writes no spend.

- [ ] **Step 1: Write the failing tests**

```python
def test_records_round_trip_in_id_order(layout):
    save(layout, Record("20261109-000002-01", "credit_snapshot", "b", "queued", "t2"))
    save(layout, Record("20261109-000001-01", "earnings_update", "a", "running", "t1", pid=7, files=("a.pdf",)))
    assert [r.id for r in load_all(layout)] == ["20261109-000001-01", "20261109-000002-01"]
    assert load_all(layout)[0].files == ("a.pdf",) and load_all(layout)[0].pid == 7

def test_command_for_prepare_and_live(layout):
    record = Record("id1", "credit_snapshot", "acme", "queued", "t")
    base = command(layout, record, Path("c.json"), launcher=["py", "-m", "x"], config="sol-medium", cap=Decimal("20"), ruling=None)
    assert base == ["py", "-m", "x", "--context", "c.json", "--sources", str(layout.drops / "id1"), "--config", "sol-medium",
                    "--cap", "20", "--out", str(layout.runs / "id1"), "--no-library"]
    live = command(layout, record, Path("c.json"), launcher=["py"], config="sol-medium", cap=Decimal("20"), ruling=Path("r.md"))
    assert live[-3:] == ["--live", "--ruling", "r.md"]

def test_alive_for_this_process_and_not_for_an_exited_one():
    child = subprocess.Popen([sys.executable, "-c", "pass"]); child.wait()
    assert alive(os.getpid()) is True and alive(child.pid) is False and alive(0) is False

@pytest.mark.parametrize(("events", "exit_code", "expected"), [
    ([("module_started", {"module": "CP-0"}), ("delivered", {})], 0, ("finished", "")),
    ([("stopped", {"reason": "budget"})], 1, ("capped", "stopped at the cap")),
    ([("stopped", {"reason": "checker"})], 1, ("failed", "stopped: checker")),
    ([], 2, ("failed", "launcher exited 2; see logs/id1.log")),
    ([("module_started", {"module": "CP-0"})], None, ("interrupted", "the run's process ended without a result")),
])
def test_outcome(layout, events, exit_code, expected): ...

def test_prepare_returns_the_refusal_text(layout, fake_env):
    fake_env({"prepare_exit": 2, "prepare_error": "--sources: cannot read a.pdf: bad"})
    assert prepare(layout, RECORD, CTX, launcher=FAKE, config="sol-medium", cap=Decimal("20")) == "--sources: cannot read a.pdf: bad"
```

- [ ] **Step 2: Run** `uv run pytest tests/test_inbox_runs.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement `runs.py` and the fake launcher.**
- [ ] **Step 4: Run the tests** — PASS. Quality gate — exit 0.
- [ ] **Step 5: Commit** `feat(inbox): run records, launcher process control and outcomes`

---

### Task 5: Activity data

**Files:**
- Create: `src/deploy_workflow/inbox/activity.py`
- Test: `tests/test_inbox_activity.py`

**Interfaces:**
- Consumes: `Layout`, `Record`; `cpos_launch.plan`, `NOT_ANALYTICAL`; `PATHWAY_MODULES`; `model.budget.read_reservation_snapshot`; `update_library.embedded_json`'s rule (copy the one-line escape: `json.dumps(..., ensure_ascii=True, allow_nan=False).replace("<", "\\u003c")`).
- Produces:

```python
STALLED_AFTER = 3600        # seconds without a new event
def module_states(pathway: str, events: Sequence[Mapping[str, Any]]) -> list[list[str]]     # [[module, "done"|"running"|"waiting"], …] + [["Report", …]]
def spent(run_dir: Path) -> Decimal | None                                                  # None = could not be read
def snapshot(layout: Layout, records: Sequence[Record], *, cap: Decimal, now: datetime, held: str = "") -> dict[str, Any]
def write(layout: Layout, data: Mapping[str, Any]) -> None                                  # _engine/activity.js
```

Decisions:
- Modules listed are `plan(tuple(m for m in PATHWAY_MODULES[pathway] if m not in NOT_ANALYTICAL))`, in that order. `module_accepted` → done; `module_started` without it → running; else waiting. The final `"Report"` entry is running after `delivery_started`, done after `delivered`.
- `spent`: `Decimal(0)` when `run_dir / "live"` does not exist. Otherwise, over `read_reservation_snapshot(run_dir / "live")`: the sum of `settled_usd` for status `settled` or `overrun`, plus `usd` (the full hold) for status `unknown` or `None`. Any error reading → `None`; an unknown spend is never shown as zero.
- `snapshot` returns `{"updated": <ISO UTC>, "cap": str(cap), "held": held, "runs": [...]}`. Each run is the record's fields plus `"modules"` and `"spent"` (a string, or `null`) for records that have a run folder, and `"stalled": true` when status is `running` and the last event (or `started_at` when there are none) is older than `STALLED_AFTER`. Order: running, then queued, then the rest newest first; keep the latest 200 ended records.
- `write` emits `window.RUN_ACTIVITY=<escaped json>;window.onRunActivity&&window.onRunActivity();\n` to a temporary file in `_engine/`, then `os.replace`.

- [ ] **Step 1: Write the failing tests**

```python
def test_module_states_follow_the_events():
    events = [{"event": "module_started", "module": "CP-0"}, {"event": "module_accepted", "module": "CP-0"},
              {"event": "module_started", "module": "CP-1"}]
    states = dict(module_states("earnings_update", events))
    assert states["CP-0"] == "done" and states["CP-1"] == "running" and states["CP-5"] == "waiting" and states["Report"] == "waiting"

def test_spend_counts_settled_charges_and_full_unknown_holds(tmp_path):
    # write three reservations with the Budget API: settled 1.25, settled 0.40, unknown hold 2.00
    assert spent(run_dir) == Decimal("3.65")

def test_spend_is_zero_before_any_call_and_unknown_when_unreadable(tmp_path):
    assert spent(tmp_path) == Decimal(0)
    (tmp_path / "live").write_text("not a folder")
    assert spent(tmp_path) is None

def test_snapshot_marks_a_silent_run_as_stalled(layout):
    record = Record("id1", "credit_snapshot", "acme", "running", "t", started_at="2026-11-09T10:00:00Z")
    late = snapshot(layout, [record], cap=Decimal("20"), now=datetime(2026, 11, 9, 11, 0, 1, tzinfo=UTC))
    soon = snapshot(layout, [record], cap=Decimal("20"), now=datetime(2026, 11, 9, 10, 59, 0, tzinfo=UTC))
    assert late["runs"][0]["stalled"] is True and "stalled" not in soon["runs"][0]

def test_written_script_cannot_close_its_element(layout):
    write(layout, {"runs": [{"folder": "</script><img src=x>"}]})
    text = (layout.engine / "activity.js").read_text(encoding="utf-8")
    assert text.startswith("window.RUN_ACTIVITY=") and "<" not in text
```

- [ ] **Step 2: Run** `uv run pytest tests/test_inbox_activity.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement `activity.py`.**
- [ ] **Step 4: Run the tests** — PASS. Quality gate — exit 0.
- [ ] **Step 5: Commit** `feat(inbox): run activity data from records, events and the budget journal`

---

### Task 6: Run activity on the page

**Files:**
- Modify: `apps/issuer-library/credit_os/web/index.html` (add `<script src="../activity.js"></script>` before `static-boot.js`)
- Modify: `apps/issuer-library/credit_os/web/views.js` (`activityView`, new `liveActivityView`)
- Modify: `apps/issuer-library/credit_os/web/screen.js` (the 30 s re-load), `screen.css` (chips)
- Test: `apps/issuer-library/credit_os/web/static.test.cjs`

**Interfaces:**
- Consumes: `window.RUN_ACTIVITY` in the shape Task 5's `snapshot` returns; `esc` and the report-list classes already in `views.js`.
- Produces: `liveActivityView(live)` → HTML string; `window.onRunActivity()`.

Decisions:
- `activityView` puts `liveActivityView(window.RUN_ACTIVITY)` above its existing content. With no `RUN_ACTIVITY` (a library built without the watcher) it adds nothing, and the missing script must not stop the page.
- Sections, in order: **Running** (issuer name, pathway, drop folder, start time, one chip per module with class `chip-done|chip-running|chip-waiting`, `USD <spent> of <cap>` or `spend could not be read`, "stalled" when set, and the files read in a collapsed `<details>`); **Waiting** (queued; shows `held` when set); **Ended** (status word, time, spend, reason; a finished run links to `../../` + its `report` with each path segment passed through `encodeURIComponent`; `name_differs` adds "issuer name differs from earlier runs"). Every value goes through `esc`.
- Re-load: while the Run activity view is showing, every 30 000 ms append a new `<script src="../activity.js?t=<Date.now()>">` to `<head>` and remove the previous one. `window.onRunActivity` re-renders only that view, and only when it is the one showing. No other view starts the timer; the page never reloads itself.

- [ ] **Step 1: Write the failing tests** in `static.test.cjs`, following the file's existing way of loading `views.js`:

```js
test('live run activity shows spend, chips and escapes names', () => {
  const html = liveActivityView({cap:'20', held:'', runs:[
    {id:'a', status:'running', pathway:'earnings_update', folder:'<img src=x onerror=1>', issuer_name:'Acme',
     started_at:'2026-11-09T13:41:00Z', spent:'3.10', files:['a.pdf'], modules:[['CP-0','done'],['CP-1','running'],['Report','waiting']]},
    {id:'b', status:'finished', pathway:'credit_snapshot', folder:'x', issuer_name:'Initech', spent:'8.42',
     report:'issuers/Initech (ini)/2026-11-09 credit_snapshot.html'},
    {id:'c', status:'running', pathway:'credit_snapshot', folder:'y', issuer_name:'Z', spent:null, modules:[]}]});
  assert.ok(!html.includes('<img'));
  assert.ok(html.includes('USD 3.10 of 20') && html.includes('spend could not be read'));
  assert.ok(html.includes('chip-done') && html.includes('chip-running') && html.includes('chip-waiting'));
  assert.ok(html.includes('href="../../issuers/Initech%20(ini)/2026-11-09%20credit_snapshot.html"'));
});
test('no live activity adds nothing', () => { assert.strictEqual(liveActivityView(undefined), ''); });
```

- [ ] **Step 2: Run** `node --test apps/issuer-library/credit_os/web/static.test.cjs` — Expected: FAIL (`liveActivityView` not defined).
- [ ] **Step 3: Implement** the view, the timer and the chip styles.
- [ ] **Step 4: Run** the node tests and `uv run pytest tests/test_update_library.py -q` — PASS (the built page still passes its existing checks with the extra script tag).
- [ ] **Step 5: Commit** `feat(library): live run activity that re-loads without reloading the page`

---

### Task 7: The watcher

**Files:**
- Create: `src/deploy_workflow/inbox/watcher.py`
- Modify: `src/deploy_workflow/owners/cpos_launch.py` (rename `_update_library` → `update_library_at`, keep behaviour)
- Test: `tests/test_inbox_watcher.py`

**Interfaces:**
- Consumes: everything Tasks 2–5 produce; `cpos_launch.update_library_at(workspace: Path) -> Library | None`; `tests/fixtures/fake_launcher.py`.
- Produces:

```python
@dataclass(frozen=True)
class Settings:
    root: Path
    config: str = "sol-medium"
    cap: Decimal = Decimal("20")
    max_running: int = 3
    max_per_day: int = 30
    settle_seconds: float = 120
    poll_seconds: float = 10
    ruling: Path = ROOT / "docs/rulings/2026-11-09-inbox-automation.md"
    launcher: tuple[str, ...] = (sys.executable, "-m", "deploy_workflow.owners.cpos_launch")

class Watcher:
    def __init__(self, settings: Settings, *, clock: Callable[[], float] = time.time,
                 now: Callable[[], datetime] = lambda: datetime.now().astimezone()) -> None
    def step(self) -> None
    def run_forever(self) -> None

def main(argv: Sequence[str] | None = None) -> int     # python -m deploy_workflow.inbox.watcher --root <folder> [--max-running N …]
```

Decisions:
- **Start-up:** `ensure_layout`; `check_ruling(config, ruling)` and the provider key variable must be set, else exit 2 with the reason (a watcher that cannot launch must not sit there claiming drops); write `library.html` (a `<meta http-equiv="refresh" content="0; url=_engine/library/index.html">` page with a plain link) if it is missing; write each `inbox/<pathway>/_template/context-form.html` (Task 8) if missing; rebuild the library once; load records. A `running` record whose `alive(pid)` is true is adopted (tracked without a `Popen`); one whose process is gone gets `outcome(..., None)`.
- **`step`, in this order:**
  1. **Reap.** For each running record: a child that exited → `outcome(layout, record, exit_code)`; an adopted one that is no longer alive → `outcome(layout, record, None)`. Save.
  2. **Finish.** If any run ended in this step, call `update_library_at(layout.engine)` once. A record whose outcome was `finished` stays `finished` only if its ID is among the library's listed runs (`Library.runs` is a list of dicts with `"id"`; `Library.excluded` is `(folder, reason)` pairs); then `file_report` its `deliveries/*/report.html` and store `report` and `name_differs`. If it is not listed, it becomes `failed` with reason `"not listed: <the library's reason for that folder>"` and nothing is filed.
  3. **Scan.** For each `candidates` entry that `ReadyTracker.ready`: `claim` with ID `<UTC %Y%m%d-%H%M%S>-<NN>` (NN counts up within the second); `check`; then `prepare`. A `DropRejected` or a non-empty `prepare` text → `reject` and save a `rejected` record with the reason. Otherwise save a `queued` record with issuer, as-of and files.
  4. **Start.** While running < `max_running` and runs whose `started_at` is on today's local date < `max_per_day`, start the oldest queued record (`start`), set `pid`, `started_at`, `running`. When the daily limit holds queued work, `held` is `"daily limit of 30 runs reached; waiting until tomorrow"`.
  5. **Publish.** `activity.write(layout, activity.snapshot(...))`.
- **Failures.** An `OSError` while handling one drop or one record is caught there, written to `logs/watcher.log` with the ID and traceback, and the loop goes on; the next poll retries. Nothing else is caught. A record is saved before its process is started and again after, so a crash between the two leaves a `queued` record, never a second start of a running one.
- `run_forever` calls `step` then sleeps `poll_seconds`, until `KeyboardInterrupt`; it does not stop its child runs on exit.
- A root longer than 80 characters is refused by `ensure_layout`; the path-length test below proves that 80 is enough.

- [ ] **Step 1: Write the failing tests.** A fixture builds `Settings(root, settle_seconds=0, launcher=(sys.executable, FAKE))`, sets a fake provider key, and a helper `pump(watcher, until)` calls `step` until a condition holds (5 s limit).

```python
def test_a_drop_becomes_a_filed_report_exactly_once(root, fake_env, listed):
    fake_env({"events": DELIVERED}); listed("*")                     # library lists the run; report.html written by the fake
    make_drop(root, "credit_snapshot", "acme"); w = Watcher(settings(root))
    pump(w, lambda: status(root) == ["finished"])
    assert not (root / "inbox/credit_snapshot/acme").exists()
    assert [p.name for p in (root / "issuers/Acme Corp (acme)").iterdir()] == ["2026-11-09 credit_snapshot.html"]
    for _ in range(5): w.step()
    assert len(load_all(layout(root))) == 1

def test_a_drop_still_arriving_does_not_start(root, fake_env):
    now = [0.0]; w = Watcher(settings(root, settle_seconds=120), clock=lambda: now[0])
    make_drop(root, "credit_snapshot", "acme"); w.step(); now[0] = 60; w.step()
    assert load_all(layout(root)) == []

def test_rejected_drop_lands_in_failed_with_its_reason(root):
    make_drop(root, "earnings_update", "acme", context_pathway="credit_snapshot"); w = Watcher(settings(root)); w.step()
    [failed] = (root / "inbox/failed").iterdir()
    assert "context names pathway credit_snapshot, dropped in earnings_update" in (failed / "WHY.txt").read_text()
    assert status(root) == ["rejected"]

def test_the_fourth_drop_waits_for_a_slot(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 2}); [make_drop(root, "credit_snapshot", f"d{i}", issuer=f"i{i}") for i in range(4)]
    w = Watcher(settings(root)); w.step()
    assert sorted(status(root)) == ["queued", "running", "running", "running"]

def test_the_daily_limit_holds_the_next_run_until_tomorrow(root, fake_env):
    day = [datetime(2026, 11, 9, 23, 0).astimezone()]
    w = Watcher(settings(root, max_per_day=1), now=lambda: day[0]); fake_env({"events": DELIVERED})
    make_drop(root, "credit_snapshot", "a", issuer="a"); pump(w, lambda: "finished" in status(root))
    make_drop(root, "credit_snapshot", "b", issuer="b"); w.step()
    assert "queued" in status(root) and "daily limit" in activity_js(root)
    day[0] = datetime(2026, 11, 10, 0, 1).astimezone(); w.step()
    assert "queued" not in status(root)

def test_a_restart_adopts_a_live_run_and_starts_no_duplicate(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 3}); make_drop(root, "credit_snapshot", "acme")
    Watcher(settings(root)).step()                                   # run is now a live child of a watcher we drop
    second = Watcher(settings(root)); second.step()
    assert status(root) == ["running"] and len(list((root / "_engine/runs").iterdir())) == 1
    pump(second, lambda: status(root) != ["running"])
    assert status(root) in (["finished"], ["interrupted"])           # adopted: decided from the events, not an exit code

def test_same_folder_name_twice_gives_two_runs(root, fake_env):
    fake_env({"events": DELIVERED, "sleep": 1})
    make_drop(root, "credit_snapshot", "acme"); make_drop(root, "earnings_update", "acme", context_pathway="earnings_update")
    w = Watcher(settings(root)); w.step()
    assert len(load_all(layout(root))) == 2 and len(list((root / "_engine/drops").iterdir())) == 2

def test_a_finished_run_the_library_does_not_list_is_not_filed(root, fake_env, listed):
    fake_env({"events": DELIVERED}); listed(None, reason="no completion record")
    make_drop(root, "credit_snapshot", "acme"); w = Watcher(settings(root)); pump(w, lambda: status(root) == ["failed"])
    assert not (root / "issuers").exists() or not any((root / "issuers").iterdir())
    assert "not listed: no completion record" in load_all(layout(root))[0].reason

def test_a_failed_activity_write_is_logged_and_the_watcher_goes_on(root, fake_env, monkeypatch):
    def full(*_): raise OSError("disk full")
    with monkeypatch.context() as patch:
        patch.setattr(activity, "write", full)
        w = Watcher(settings(root)); w.step()                        # this write fails; step must not raise
    w.step()                                                         # the real write is back
    assert "disk full" in (root / "_engine/logs/watcher.log").read_text() and (root / "_engine/activity.js").is_file()

def test_start_up_refuses_without_the_provider_key(root, monkeypatch):
    monkeypatch.delenv(KEY_VARIABLES[CONFIGS["sol-medium"].provider], raising=False)
    assert main(["--root", str(root)]) == 2

def test_longest_engine_path_fits_under_an_80_character_root(tmp_path):
    root = tmp_path / ("r" * (80 - len(str(tmp_path)) - 1)); layout = ensure_layout(root)
    library_fixtures.make_run(layout.engine, "20261109-134102-01"); update_library_at(layout.engine)
    assert max(len(str(p)) for p in root.rglob("*")) < 260
```

The `listed` fixture replaces `cpos_launch.update_library_at` with a function returning a small object whose `runs` and `excluded` name the run as asked; the last test uses the real one.

- [ ] **Step 2: Run** `uv run pytest tests/test_inbox_watcher.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement `watcher.py`**; rename `_update_library` and its one caller.
- [ ] **Step 4: Run** `uv run pytest tests/test_inbox_watcher.py tests/test_cpos_launch.py -q` — PASS. Quality gate — exit 0.
- [ ] **Step 5: Commit** `feat(inbox): the watcher — claim, prepare, launch, limit, file, publish`

---

### Task 8: A context form per pathway

**Files:**
- Modify: `docs/templates/context-form.html` (honour a fixed pathway)
- Modify: `src/deploy_workflow/inbox/drops.py` (add `write_templates`)
- Test: `tests/test_inbox_drops.py`, `tests/test_library_page_browser.py` (one `browser`-marked test)

**Interfaces:**
- Produces: `write_templates(layout: Layout, form: Path) -> None` — for each pathway, writes `inbox/<pathway>/_template/context-form.html` if missing: the form's bytes with ` data-pathway="<pathway>"` added to its opening `<html lang="en">` tag. Task 7's start-up calls it with `ROOT / "docs/templates/context-form.html"`.

Decisions:
- In the form, when `document.documentElement.dataset.pathway` is set: the pathway select takes that value, is disabled, and a change of run type no longer changes it. The form's existing per-pathway behaviour then shows only the steps that pathway needs. With no attribute the form behaves exactly as today, and the JSON it builds is unchanged in both cases.

- [ ] **Step 1: Write the failing tests**

```python
def test_each_pathway_gets_a_form_fixed_to_it(layout):
    write_templates(layout, ROOT / "docs/templates/context-form.html")
    for pathway in PATHWAYS:
        html = (layout.inbox / pathway / "_template/context-form.html").read_text(encoding="utf-8")
        assert f'data-pathway="{pathway}"' in html and html.count("data-pathway=") == 1

@pytest.mark.browser
def test_fixed_pathway_is_selected_and_locked(page, layout):
    write_templates(layout, ROOT / "docs/templates/context-form.html")
    page.goto((layout.inbox / "earnings_update/_template/context-form.html").as_uri())
    select = page.locator("#s1-pathway")
    assert select.input_value() == "earnings_update" and select.is_disabled()
```

- [ ] **Step 2: Run** `uv run pytest tests/test_inbox_drops.py -q -k pathway_gets` — Expected: FAIL.
- [ ] **Step 3: Implement** `write_templates` and the form change.
- [ ] **Step 4: Run** the test — PASS; run the browser test where a browser is available, else record it under `Not verified:`. Quality gate — exit 0.
- [ ] **Step 5: Commit** `feat(inbox): a context form fixed to each pathway`

---

### Task 9: Package, documents, branch checks

**Files:**
- Create: `apps/issuer-library/packaging/Start watcher.cmd`
- Modify: `apps/issuer-library/packaging/build.py`, `tests/test_issuer_library_packaging.py`
- Modify: `README.md`, `apps/issuer-library/README.md`, `VERIFICATION.md`

- [ ] **Step 1: Write the failing test** — the built package lists `Start watcher.cmd`, and its `engine/src/deploy_workflow/inbox/watcher.py` and `engine/docs/rulings/2026-11-09-inbox-automation.md` (the package ships no other ruling: change the assertion at `tests/test_issuer_library_packaging.py:158` from an empty `docs/rulings` to exactly that one file).
- [ ] **Step 2: Run** `uv run pytest tests/test_issuer_library_packaging.py -q` — Expected: FAIL.
- [ ] **Step 3: Implement.** `Start watcher.cmd [root]` runs the bundled Python with `-m deploy_workflow.inbox.watcher --root <root>`; without an argument it uses `FINAL_WORKFLOW_WORKSPACE`, else it prints the usage and exits 1. It sets no key.
- [ ] **Step 4: Documents.** Root `README.md`: a section "Automated: the inbox" with the analyst's four steps, the layout, the settings and their defaults, how to start the watcher at boot with Task Scheduler under a service account that holds the provider key, the folder permissions (analysts: modify on `inbox/`, read elsewhere), and the known limits (a copy that fails part-way looks complete; two IDs for one issuer make two folders; a run can end slightly above USD 20 after one overrunning call; reports leave the library list after a method update but stay in `issuers/`). Update "Current limits" and the two-step text. `apps/issuer-library/README.md`: the same in brief.
- [ ] **Step 5: Run** the packaging test — PASS. Then the branch checks, once: `uv run python tools/quality_gate.py`; `uv run pytest tests/test_inbox_drops.py tests/test_inbox_filing.py tests/test_inbox_runs.py tests/test_inbox_activity.py tests/test_inbox_watcher.py tests/test_cpos_launch.py tests/test_update_library.py tests/test_issuer_library_packaging.py -q`; `node --test apps/issuer-library/credit_os/web/static.test.cjs apps/issuer-library/credit_os/web/calendar.test.cjs`. All exit 0. Run `confidence-review` and `rewrite-tournament` (post-edit) on the branch diff, and the whole-branch review.
- [ ] **Step 6: Add the `VERIFICATION.md` entry**, labelled with its real scope: synthetic runs through a fake launcher on macOS; no provider called; nothing run on Windows.
- [ ] **Step 7: Commit** `feat(package): Start watcher.cmd; inbox documents and verification record`

---

### Task 10: Owner checkpoints on the always-on machine (not automated)

These need the real Windows machine, the share and the provider key. They are the owner's to run; the build is "built, not proven on Windows" until they pass.

- [ ] **Windows smoke:** unpack the package on the always-on machine and run `Smoke-test.ps1`. Expected: passes (bundled Python, offline run review, library update).
- [ ] **Budget on a local disk:** `python -m pytest tests/model/test_budget.py -q` from a checkout on that machine. Expected: pass. This is the first run of the cap's marker files on Windows.
- [ ] **Ready check over the share:** start the watcher with `--settle-seconds 120`, copy a 500 MB folder into `inbox\credit_snapshot\` from an analyst machine. Expected: Run activity shows nothing for that drop until the copy ends plus 2 minutes.
- [ ] **Permissions:** from an analyst account, creating a file in `issuers\` or `_engine\` is refused; in `inbox\` it works.
- [ ] **Library from the share:** an analyst opens `library.html`; Run activity updates within 30 s without the page reloading; a finished run's report opens.
- [ ] **One measured live run:** drop one real issuer folder into one pathway. Record the spend. Expected: completes under USD 20; if it stops at the cap, raise the cap setting or choose a smaller pathway before going further. Label the result as that issuer, date and pathway only.
