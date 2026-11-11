# Staged Run Start Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the inbox watcher and folder drop with a served start page: the analyst uploads the documents, answers staged context questions limited by what the documents support, approves a summary, and Submit starts one paid run.

**Architecture:** One standard-library HTTP service (`deploy_workflow.run_start`) holds the provider key. It stores uploads, runs the launcher's own offline reading and preparation for the summary, and hands an approved submission to a scheduler. The scheduler is today's `Watcher` without its inbox scanning: it starts runs within the limits, reaps them, files reports and publishes Run activity. The existing context form becomes the start page and posts to the service instead of downloading a file.

**Tech Stack:** Python 3.13 standard library (`http.server`, `threading`, `hashlib`, `secrets`), the existing launcher (`owners/cpos_launch.py`), pytest, headless Chrome for page tests (as `tests/test_library_page_browser.py`).

**Spec:** `docs/superpowers/specs/2026-11-11-staged-run-start-design.md`

## Global Constraints

- Standard library only. No new dependency.
- No test calls a provider. Use `tests/fixtures/fake_launcher.py` and `tests/fixtures/canned_provider_launcher.py`.
- Nothing is copied from `~/Documents/Final-workflow-PY`. Do not read it while building.
- Cap USD 20 per run; at most 3 running and 30 a day; config `sol-medium` only.
- Upload limits: 50 MiB a file, 500 files, 512 MiB in total, enforced while receiving.
- Default bind address `127.0.0.1`.
- The provider key is never written to a response or a log.
- `context/1` existing fields and key order are unchanged. The only new field is optional `module_options`, omitted when empty.
- The launcher's recognition of a file decides the forecast. No per-file label enters the context.
- The watcher is removed only after Task 7 passes (Submit starts a run end to end).
- Per task: `uv run pytest <the task's test files> -q` (Bash timeout 300 s) and `uv run python tools/quality_gate.py`. Both exit 0.
- No stub or fake value standing in for real behaviour. No catch-all that hides a failure unless documented and logged. Each task report ends with a `Not verified:` line.
- Agents: implement with `mx-feature`. Review Tasks 3, 4 and 5 with `mx-precise` and `mx-adversary` (security, money, concurrency); the others with `mx-precise`. Whole-branch review with `mx-architect`, then `confidence-review` and `rewrite-tournament` once on the branch diff.
- The branch deletes about 1,500 lines of watcher code and tests. Task 8 is its own commit so the review can read additions and deletions apart.

## Review Focus

1. **Submit sent twice at once** (double click, two tabs): exactly one run. Test in Task 4.
2. **An upload cut off part-way**: the partial file is not stored and does not count toward the limits. Test in Task 3.
3. **The service restarts with a queued run and unsubmitted uploads**: the queued run starts once; the uploads are still there for the analyst. Test in Task 4.
4. **File names**: two uploads whose safe names collide, a Windows-reserved name (`CON.pdf`), a non-ASCII name, and a top-level `context.json`. Tests in Task 3.
5. **The page is reloaded mid-way**: answers and the uploaded files are still shown. Test in Task 6.

---

### Task 1: `module_options` in the context and the two instruction lines

**Files:**
- Modify: `src/deploy_workflow/context.py` (types near line 46; `RunContext` at 277; validation in `load_context`)
- Modify: `src/deploy_workflow/owners/cpos_launch.py` (`prepare`, the block loop after `_instructions`)
- Test: `tests/test_context_module_options.py`, `tests/test_cpos_launch.py`

**Interfaces:**
- Produces:
  ```python
  Cp3Mode = Literal["", "clo_screening", "single_name_rv", "capital_structure_rv", "watchlist_monitoring"]
  class ModuleOptions(Contract):
      cp3_mode: Cp3Mode = ""
      cp6_deep_debate: bool = False
  # RunContext gains, last: module_options: ModuleOptions = ModuleOptions()
  CP3_MODE_BLOCK: str   # "The user selected the execution mode {label} (source `context`, module_options.cp3_mode). Use it at Step 1; do not choose another.\n\n"
  DEEP_DEBATE_BLOCK: str  # "The user explicitly asks for a full debate (source `context`, module_options.cp6_deep_debate). Deep Debate Mode is ON.\n\n"
  ```
  Labels: `CLO Screening`, `Single-Name RV`, `Capital-Structure RV`, `Watchlist Monitoring`.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_context_without_module_options_loads_and_equals_the_default():
    ctx = load_context(FIXTURE_BYTES)            # cases/context/research-minimal
    assert ctx.module_options == ModuleOptions()

def test_module_options_are_read():
    ctx = load_context(with_key(FIXTURE, "module_options", {"cp3_mode": "single_name_rv", "cp6_deep_debate": True}))
    assert ctx.module_options.cp3_mode == "single_name_rv" and ctx.module_options.cp6_deep_debate is True

@pytest.mark.parametrize("bad", [{"cp3_mode": "fast"}, {"cp6_deep_debate": "yes"}, {"cp9": 1}])
def test_a_wrong_module_option_is_refused(bad):
    with pytest.raises(ContextRefused):
        load_context(with_key(FIXTURE, "module_options", bad))
```

In `tests/test_cpos_launch.py`:

```python
def test_the_chosen_cp3_mode_and_deep_debate_reach_their_instructions(tmp_path):
    prepared = prepare(context_with_options(tmp_path, cp3_mode="single_name_rv", cp6_deep_debate=True), SOURCES, tmp_path / "out", config="sol-medium", cap="20")
    assert "Single-Name RV" in (prepared.directory / "instructions/CP-3.md").read_text()
    assert "Deep Debate Mode is ON" in (prepared.directory / "instructions/CP-6.md").read_text()

def test_without_options_the_instructions_are_byte_identical_to_before(tmp_path):
    # same context without module_options: no instruction file contains either block
```

Use a pathway that runs CP-3 and CP-6 (`portfolio_decision`).

- [ ] **Step 2: Run** `uv run pytest tests/test_context_module_options.py tests/test_cpos_launch.py -q -k "module_option or cp3_mode or byte_identical"`. Expected: FAIL (`ModuleOptions` not defined).
- [ ] **Step 3: Implement** the types and the two blocks. Insert the blocks through the existing `(module, block, wanted)` loop in `prepare`, which places a block before `METHOD_MARK`.
- [ ] **Step 4: Run** the same command and `uv run pytest tests/test_context_form.py -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(context): optional module_options for CP-3 mode and CP-6 deep debate`

---

### Task 2: The launcher's document reading as one public call

**Files:**
- Modify: `src/deploy_workflow/owners/cpos_launch.py` (`_issuer_files` at 327, `prepare` at 1644)
- Test: `tests/test_cpos_launch.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class Reading:
      documents: tuple[dict[str, Any], ...]  # keys: source, kind, signal, executed, period_end (as Prepared.documents)
      ignored: tuple[str, ...]               # names the launcher skips without reading
  def read_documents(folder: Path) -> Reading   # raises LaunchRefused with the launcher's own text
  ```
  `prepare` builds `Prepared.documents` through the same helper, so the two cannot differ.

- [ ] **Step 1: Write the failing tests**

```python
def test_read_documents_gives_what_prepare_gives(tmp_path):
    reading = read_documents(SOURCES)
    prepared = prepare(CONTEXT, SOURCES, tmp_path / "out", config="sol-medium", cap="20")
    assert reading.documents == prepared.documents and reading.ignored == prepared.ignored

def test_read_documents_lists_a_skipped_file_and_refuses_an_empty_one(tmp_path):
    # folder with a.pdf (valid), deck.pptx, _notes.txt -> ignored == ("_notes.txt", "deck.pptx")
    # folder with only an empty .txt -> LaunchRefused, message names the file
```

- [ ] **Step 2: Run** `uv run pytest tests/test_cpos_launch.py -q -k read_documents`. Expected: FAIL (not defined).
- [ ] **Step 3: Implement.** `read_documents` writes nothing: pass `_issuer_files` a context path that does not exist and a directory outside `folder`.
- [ ] **Step 4: Run** `uv run pytest tests/test_cpos_launch.py -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(launcher): read_documents, the offline document reading on its own`

---

### Task 3: Submissions: uploads, limits, summary and digest

**Files:**
- Create: `src/deploy_workflow/run_start/__init__.py` (empty), `src/deploy_workflow/run_start/submissions.py`
- Modify: `src/deploy_workflow/inbox/drops.py` (`Layout` gains `uploads` → `engine / "uploads"`; `ensure_layout` creates it)
- Test: `tests/test_run_start_submissions.py`

**Interfaces:**
- Consumes: `cpos_launch.read_documents`, `cpos_launch.prepare`, `context.load_context`, `filing.safe_name`.
- Produces:
  ```python
  MAX_FILE = 50 * 1024 * 1024
  MAX_FILES = 500
  MAX_TOTAL = 512 * 1024 * 1024
  STALE_SECONDS = 24 * 3600
  class Refused(ValueError): ...
  class Answers(TypedDict):
      context: dict[str, Any]      # a context/1 object, as the page's build() makes it
      modules: list[str]           # [] = the pathway's modules
      max_turns: int               # 32 unless Advanced changes it
      level: str                   # "basic" | "standard" | "advanced"
      submitted_by: str
  def new(layout: Layout) -> str                     # 32 hex characters; folder uploads/<id>/files
  def files_folder(layout: Layout, sid: str) -> Path  # Refused unless sid is 32 hex and exists
  def add_file(layout: Layout, sid: str, name: str, body: BinaryIO, length: int) -> str  # the stored relative name
  def remove_file(layout: Layout, sid: str, name: str) -> None
  def reading(layout: Layout, sid: str) -> dict[str, Any]   # {"documents": [...], "ignored": [...], "error": ""}
  def summary(layout: Layout, sid: str, answers: Answers, *, config: str, cap: Decimal) -> dict[str, Any]
      # {"digest": str, "error": "", "modules": [...ordered], "items": [...Prepared.expectations],
      #  "documents": [...], "ignored": [...], "omitted": [...]}
  def digest(layout: Layout, sid: str, answers: Answers) -> str   # sha256 hex
  def context_bytes(answers: Answers) -> bytes   # json.dumps(context, indent=2, ensure_ascii=False) + "\n"
  def sweep(layout: Layout, now: float) -> None  # deletes uploads/<id> not modified for STALE_SECONDS
  ```
- Rules the tests pin:
  - `add_file` writes to a temporary name in the submission folder and renames on success. It reads at most `length` bytes; a body shorter than `length`, a `length` over `MAX_FILE`, a 501st file, or a total over `MAX_TOTAL` raises `Refused` and leaves nothing behind.
  - A name is split on `/` and `\`; each part goes through `filing.safe_name`; an empty part, `.`, `..`, a leading `/` or a drive letter raises `Refused`. A top-level `context.json` raises `Refused`. A name that already exists is replaced.
  - `summary` validates the context with `load_context`, writes it to a temporary folder outside the files, calls `prepare(..., out=<a fresh temporary folder>)`, and removes both. `ContextRefused` and `LaunchRefused` come back as `error`, with no digest.
  - `digest` covers: `context_bytes`, each stored file's relative name and SHA-256 in sorted order, `modules`, `max_turns`. It does not cover `level` or `submitted_by`.

- [ ] **Step 1: Write the failing tests**

```python
def test_an_uploaded_folder_is_read_as_the_launcher_reads_it(layout): ...
    # add the files of tests' TDG source fixture; reading()["documents"] == list(read_documents(folder).documents)
def test_a_cut_off_upload_leaves_nothing(layout):
    with pytest.raises(Refused): add_file(layout, sid, "a.pdf", io.BytesIO(b"abc"), 10)
    assert list(files_folder(layout, sid).iterdir()) == []
@pytest.mark.parametrize("name", ["../x.pdf", "/etc/x.pdf", "a/../../x.pdf", "C:\\x.pdf", "", "context.json"])
def test_an_unsafe_name_is_refused(layout, name): ...
def test_a_reserved_and_a_non_ascii_name_are_stored_safely(layout):
    assert add_file(layout, sid, "CON.pdf", ...) == "_CON.pdf"
    assert add_file(layout, sid, "Geschäftsbericht 2024.pdf", ...) == "Geschäftsbericht 2024.pdf"
def test_two_names_that_become_one_keep_the_later_file(layout): ...   # 'a:b.pdf' then 'a b.pdf'
def test_the_file_count_size_and_total_limits_refuse(layout, monkeypatch): ...  # monkeypatch the three constants small
def test_the_summary_is_the_launchers_forecast(layout):
    s = summary(layout, sid, answers, config="sol-medium", cap=Decimal(20))
    assert s["error"] == "" and s["items"] == list(prepare(ctx_file, folder, tmp, config="sol-medium", cap="20").expectations)
def test_a_refused_context_or_folder_comes_back_as_the_error_with_no_digest(layout): ...
def test_the_digest_changes_with_a_file_the_context_the_modules_or_the_turns_only(layout): ...
    # changing level or submitted_by keeps it
def test_the_summary_leaves_no_run_folder_and_no_temporary_file(layout): ...
def test_stale_uploads_are_swept_and_fresh_ones_kept(layout): ...
```

- [ ] **Step 2: Run** `uv run pytest tests/test_run_start_submissions.py -q`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `submissions.py`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `feat(run-start): submissions with upload limits, summary and approval digest`

---

### Task 4: The scheduler accepts an approved submission

**Files:**
- Modify: `src/deploy_workflow/inbox/watcher.py` (add `submit`; a lock around `step`)
- Modify: `src/deploy_workflow/inbox/runs.py` (`Record` at 28, `command` at 134)
- Test: `tests/test_run_start_scheduler.py`

**Interfaces:**
- Consumes: `submissions.digest`, `submissions.files_folder`, `submissions.context_bytes`, `Answers`.
- Produces:
  ```python
  # runs.Record gains, with defaults so saved records still load:
  submission: str = ""; modules: tuple[str, ...] = (); max_turns: int = 32; level: str = ""; submitted_by: str = ""
  # runs.command appends "--modules", *record.modules when set, and "--max-turns", str(record.max_turns) when not 32.
  class Watcher:
      lock: threading.Lock                     # held by step() and submit()
      def submit(self, sid: str, answers: Answers, approved_digest: str) -> Record
  ```
- `submit`, under the lock:
  1. If a record with `submission == sid` exists, return it.
  2. Recompute the digest; if it differs from `approved_digest`, raise `submissions.Refused("the documents or answers changed after approval; review the summary again")`.
  3. Write `context.json` into the files folder, save a `Record` (`status="queued"`, `prepared=True`, `folder` = issuer name, the new fields set), then rename the files folder to `layout.drops / record.id`. The record is saved before the rename, as the watcher does for a claim.
  4. Return the record. The next `step()` starts it within `max_running` and `max_per_day`.
- `_recover` treats a queued record whose `drops/<id>` is missing but whose `uploads/<sid>/files` exists as an unfinished step 3 and completes the rename.

- [ ] **Step 1: Write the failing tests** (fixtures `root`, `fake_env`, `settings`, `pump` are in `tests/test_inbox_watcher.py`; move them to a new `tests/inbox_fixtures.py` both files import, since there is no `tests/conftest.py`)

```python
def test_a_submission_becomes_one_running_run_with_its_context(root, fake_env): ...
    # record.status == "running" after pump; drops/<id>/context.json == context_bytes(answers)
def test_submit_twice_and_from_two_threads_gives_one_run(root, fake_env):
    # 8 threads call submit(sid, answers, d); all return the same record.id; one record on disk
def test_a_changed_file_or_answer_after_approval_is_refused_and_nothing_starts(root, fake_env): ...
def test_the_fourth_submission_waits_and_the_daily_limit_holds(root, fake_env): ...
def test_modules_and_turns_reach_the_launcher_command(root):
    assert command(...)[-4:] == ["--modules", "CP-0", "CP-1", ...] or contains "--max-turns", "16"
def test_a_restart_starts_a_queued_submission_once_and_keeps_unsubmitted_uploads(root, fake_env): ...
def test_a_restart_between_record_and_rename_finishes_the_move(root, fake_env): ...
def test_a_record_saved_before_this_change_still_loads(root): ...
```

- [ ] **Step 2: Run** `uv run pytest tests/test_run_start_scheduler.py -q`. Expected: FAIL (`submit` missing).
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `uv run pytest tests/test_run_start_scheduler.py tests/test_inbox_watcher.py tests/test_inbox_runs.py tests/test_inbox_activity.py -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(run-start): the scheduler takes an approved submission, once`

---

### Task 5: The HTTP service

**Files:**
- Create: `src/deploy_workflow/run_start/service.py`, `src/deploy_workflow/run_start/__main__.py`
- Create: `docs/rulings/2026-11-11-run-start-submit.md`
- Modify: `src/deploy_workflow/inbox/startup.py` (`STANDING_RULING` at 26; the refusal text at 82)
- Test: `tests/test_run_start_service.py`

**Interfaces:**
- Consumes: `submissions.*`, `Watcher`, `Settings`, `startup.check_launchable`, `startup.take_lock`.
- Produces:
  ```python
  def make_server(watcher: Watcher, host: str, port: int) -> ThreadingHTTPServer
  def main(argv: Sequence[str] | None = None) -> int   # --root (required) --host 127.0.0.1 --port 8765 --max-running --max-per-day
  ```
  `main` runs the server in a daemon thread and `watcher.step()` every `poll_seconds` in the main thread, and calls `submissions.sweep` each poll. Exit codes as the watcher's `main`.
- Requests (paths are the builder's choice; the page in Task 6 uses whatever this task documents in its module docstring): the start page; create a submission; upload one file (raw body, `Content-Length` required, name in the query string); remove a file; the reading; the summary; submit; one run's activity; and read-only files under `layout.engine / "library"`.
- Rules the tests pin:
  - Every request other than GET must carry `Origin` equal to `http://<Host header>`, and `Host` must be the address the service was started on. Otherwise 403 and no change.
  - `submissions.Refused` → 400 with the text. Unknown submission → 404. A body without `Content-Length` → 411.
  - A library path that resolves outside `layout.engine / "library"` → 404.
  - No response body or header contains the value of the provider key variable.
- The ruling file, exactly:
  ```markdown
  # Standing ruling: run start page live launches on sol-medium

  lifts: live-provider-pause
  by: user
  date: 2026-11-11
  configs: sol-medium

  The user was asked: "The explicit paid action would become 'Submit after an approved summary',
  at the same USD 20 cap", and said: "2. Approved". On the service: "one users CLI will provide for
  all other users".

  Scope: live launches started by `deploy_workflow.run_start` from a submission whose summary the
  analyst approved, USD 20 per run folder, on sol-medium only. The provider key comes from the
  service's environment only; no credential file is read. Replaces 2026-11-09-inbox-automation.md.
  ```
  Check the header keys against `model/adapter.py` `check_ruling` (170-200) and the 2026-11-09 file before committing.

- [ ] **Step 1: Write the failing tests** (start `make_server` on port 0 with the fake launcher; use `urllib.request`)

```python
def test_upload_read_summarise_submit_and_see_the_run(service): ...
    # the run reaches "running"; submit again returns the same run id
def test_a_post_without_or_with_a_foreign_origin_changes_nothing(service): ...   # 403; no submission folder
def test_a_request_for_another_host_name_is_refused(service): ...               # Host: evil.example -> 403
@pytest.mark.parametrize("path", ["/library/../state/x", "/library/%2e%2e/logs/watcher.log"])
def test_the_library_route_serves_nothing_outside_the_library(service, path): ...
def test_an_over_limit_upload_is_refused_while_receiving(service, monkeypatch): ...  # MAX_FILE small; 400; nothing stored
def test_submit_with_a_stale_digest_is_refused(service): ...
def test_no_response_carries_the_provider_key(service, monkeypatch): ...   # key set to a marker string
def test_start_up_refuses_without_the_key_or_with_a_second_instance(root, monkeypatch): ...
```

- [ ] **Step 2: Run** `uv run pytest tests/test_run_start_service.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement.** `BaseHTTPRequestHandler` with one method per request; JSON in and out; no framework.
- [ ] **Step 4: Run** `uv run pytest tests/test_run_start_service.py tests/test_inbox_watcher.py -q`. Expected: PASS (the watcher's own start-up test now names the new ruling; update its expectation).
- [ ] **Step 5: Commit** `feat(run-start): the local service and its standing ruling`

---

### Task 6: The start page: pathway and level, documents, legal

**Files:**
- Modify: `docs/templates/context-form.html` (`STAGES` at 1223; pathway cards 1676; sources stage; `build()` at 954)
- Modify: `tests/test_context_form.py`, `tests/test_library_page_browser.py` (`FORM_PROBE`)
- Test: `tests/test_run_start_page.py`

**Interfaces:**
- Consumes: Task 5's requests; `module_options` from Task 1.
- Produces, in the page: `STAGES = ['pathway', 'documents', 'issuer', 'legal', 'market', 'valuation', 'assumptions', 'review']`; a global `LEVEL` (`'basic' | 'standard' | 'advanced'`); `build()` still returns the `context/1` object, now with `module_options` when set.
- Decisions:
  - **Pathway stage:** the six pathway cards, then the three level buttons, then the submitter's name. The run type moves to the issuer stage. Research questions join the assumptions stage (shown from Standard).
  - **Level:** Basic shows `pathway, documents, issuer, legal, review`. Standard adds `market`, `valuation` (peer source, own peers, CP-3 mode, Deep Debate; not valuation basis or own multiple) and research questions. Advanced adds everything else, plus module subset and turns on the pathway stage. A stage holding an error or a loaded answer is always shown (existing rule).
  - **Documents stage:** a folder picker (`<input type="file" webkitdirectory multiple>`) and a file picker. Files upload one at a time; the top folder name is stripped. The list shows each file with the launcher's kind, period end and executed reading, "not recognised", or "will not be read" with the reason. The newest period end fills the newest-document date.
  - **Legal stage:** a file selector over the uploaded files plus "No agreement in these documents". `executed` and `draft` are disabled until a file is selected. If the reading's kind for that file is not in `AGREEMENTS` (`credit_agreement`, `indenture`), or its `executed` reading contradicts the answer, a limit is added to the review, naming the file.
  - **Attachments:** bridge, portfolio workbook and prior case become file selectors over the uploaded files; none selected writes `false`.
  - **Reload:** the submission id, level and answers are kept in `localStorage`, read and written inside `try/catch`; the page renders without it.
  - **Research source:** where CP-DR runs, the valuation stage shows "Research reads the supplied files only" as fixed text, not a choice.
  - Removed: the load-a-file control, the folder scan, the "Before you drop" checklist, the legal confirmation tick, CP-2E pins.
- `tests/test_context_form.py` keeps every drift test. Add: `STAGES` equals the list above; the CP-3 mode values equal `typing.get_args(context.Cp3Mode)` without `""`; `AGREEMENTS` equals `run_expectations.AGREEMENTS`.

- [ ] **Step 1: Write the failing tests** (`tests/test_run_start_page.py`: start the Task 5 service with the fake launcher, drive the page in headless Chrome as `tests/test_library_page_browser.py` does, skip when Chrome is absent in the same way)

```python
def test_basic_shows_five_stages_and_standard_and_advanced_add_theirs(page): ...
def test_executed_cannot_be_chosen_until_an_uploaded_file_is_selected(page): ...
def test_a_file_the_launcher_does_not_recognise_as_an_agreement_adds_a_limit(page): ...
def test_an_as_of_date_before_the_newest_period_end_adds_a_limit(page): ...
def test_a_skipped_file_is_listed_as_will_not_be_read(page): ...
def test_the_three_levels_build_the_same_context_for_the_same_answers(page): ...
def test_basic_builds_the_defaults_the_form_had(page):
    # build() on Basic with the research-minimal answers == cases/context/research-minimal context, plus cutoff
def test_a_reload_keeps_the_answers_and_the_uploaded_files(page): ...
def test_changing_level_keeps_answers(page): ...
```

- [ ] **Step 2: Run** `uv run pytest tests/test_run_start_page.py tests/test_context_form.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement.** Keep `build()`'s key order; `module_options` is the last key and absent when both values are default.
- [ ] **Step 4: Run** `uv run pytest tests/test_run_start_page.py tests/test_context_form.py tests/test_library_page_browser.py -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(run-start): staged page with levels, uploaded documents and file-bound legal answer`

---

### Task 7: Summary, approval and Submit on the page

**Files:**
- Modify: `docs/templates/context-form.html` (`renderReview` at 1539, `syncDownload` at 1577, the download handler near 1870)
- Test: `tests/test_run_start_page.py`

**Interfaces:**
- Consumes: Task 5's summary, submit and activity requests.
- Decisions:
  - Entering the review stage requests the summary. Its `items` replace the page's own forecast in the review (the side panel keeps the page's live forecast while editing).
  - The review lists, per module in run order: outcome, reason, and a link to the stage that fixes it. On Basic and Standard it lists each defaulted input with its default. It shows pathway, issuer, dates, file count, `sol-medium`, the USD 20 cap, and `omitted` as the report sections this run does not fill.
  - A Gap or Limited whose fix is in a stage the level hides shows "Answer this now", which opens that stage without changing `LEVEL`.
  - One tick per remaining limit; a summary `error` blocks approval and links to its stage.
  - **Approve** enables **Submit**. Any later change to an answer or file clears the approval and the digest.
  - Submit sends the digest. On success the page shows the run's id, state and module progress, refreshed every 10 seconds, with a link to Run activity. On a refused digest it returns to the review with the service's text.
  - The Submit button is disabled from the first click until the response arrives.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_review_shows_the_services_forecast_per_module(page): ...
def test_a_limit_must_be_ticked_before_approval_and_an_error_blocks_it(page): ...
def test_basic_lists_its_defaults_and_offers_answer_this_now(page): ...
def test_editing_after_approval_clears_it(page): ...
def test_submit_starts_one_run_and_the_page_shows_its_progress(page): ...
def test_a_double_click_on_submit_starts_one_run(page): ...
```

Add one journey with `tests/fixtures/canned_provider_launcher.py` in place of the fake launcher:

```python
def test_upload_to_filed_report_with_the_real_launcher(page, tmp_path):
    # upload the fixture folder, Basic, approve, submit; pump until the run is "finished";
    # the report is under issuers/ and the library lists the run
```

- [ ] **Step 2: Run** `uv run pytest tests/test_run_start_page.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `uv run pytest tests/test_run_start_page.py tests/test_run_start_service.py -q`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(run-start): summary, approval and submit`

---

### Task 8: Remove the watcher's inbox, and update packaging, docs and CI

**Files:**
- Rename: `src/deploy_workflow/inbox/watcher.py` → `src/deploy_workflow/inbox/scheduler.py` (class `Watcher` → `Scheduler`); update imports in `run_start/` and tests
- Create: `src/deploy_workflow/inbox/layout.py` (`Layout` without `inbox` and `failed`, `MAX_ROOT`, `ensure_layout` without the inbox folders)
- Delete: `src/deploy_workflow/inbox/drops.py`, `tests/test_inbox_drops.py`
- Modify: `src/deploy_workflow/inbox/startup.py` (`write_pages` no longer writes templates; lock file stays `watcher.lock` so an old watcher and the service exclude each other), `activity.py`, `filing.py`, `runs.py` (import `Layout` from `layout`)
- Rename: `tests/test_inbox_watcher.py` → `tests/test_inbox_scheduler.py`; delete its drop, settle, reject and unreadable-folder tests; keep limits, restart, lock, rebuild and filing tests, driven through `submit`
- Modify: `apps/issuer-library/packaging/runtime.py` (98-121: `Start watcher.cmd` → `Start run page.cmd <root> [host]`, running `-m deploy_workflow.run_start`; ship the new ruling), `tests/test_issuer_library_packaging.py`
- Modify: `.github/workflows/checks.yml` (44-45), `AGENTS.md`, `README.md`, `apps/issuer-library/README.md`, `docs/templates/README.md`, `VERIFICATION.md`

**Decisions:**
- Removed from the scheduler: `_scan`, `_claim`, `_watch_unreadable`, `_note_unmovable`, `_unmovable_notes`, `_put_back`, `_reject`, `_reject_unrecorded_folders`, `_prepare_queued`, `_prepare`, the `ReadyTracker`, `settle_seconds`, and `watcher.main` with its parser.
- `AGENTS.md`, the paid-execution sentence becomes: "For the run start page (`deploy_workflow.run_start`) the explicit action is an analyst choosing Submit on a summary they approved, under the standing ruling `docs/rulings/2026-11-11-run-start-submit.md` and a USD 20 cap per run (owner, 2026-11-11)."
- READMEs: replace the inbox sections with: start the service, open the address, the nine stages, the three levels, the limits, what Basic defaults, and that the service has no login.
- An existing `<root>/inbox/` folder is left alone and never read.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_layout_makes_no_inbox(tmp_path):
    ensure_layout(tmp_path); assert not (tmp_path / "inbox").exists()
def test_the_package_ships_the_run_page_starter_and_the_new_ruling(...): ...   # in test_issuer_library_packaging.py
def test_nothing_imports_the_removed_modules():
    # no file under src/ or apps/ contains "inbox.drops" or "inbox.watcher"
```

- [ ] **Step 2: Run** `uv run pytest tests/test_inbox_scheduler.py tests/test_issuer_library_packaging.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** the renames, deletions and document changes.
- [ ] **Step 4: Run** `uv run pytest tests/test_inbox_scheduler.py tests/test_inbox_runs.py tests/test_inbox_activity.py tests/test_inbox_filing.py tests/test_run_start_submissions.py tests/test_run_start_scheduler.py tests/test_run_start_service.py tests/test_run_start_page.py tests/test_context_form.py tests/test_cpos_launch.py tests/test_issuer_library_packaging.py tests/test_library_page_browser.py -q` and `uv run python tools/quality_gate.py`. Expected: PASS, exit 0.
- [ ] **Step 5: Commit** `refactor(run-start): remove the inbox watcher and folder drop`

---

## After the last task

- Whole-branch review (`mx-architect`), then `confidence-review` and `rewrite-tournament` (post-edit) once on the branch diff.
- One `VERIFICATION.md` entry: what ran, with exit codes, labelled as offline with stand-in launchers.
- **Not verified by this plan:** that CP-3 and CP-6 honour `module_options` (needs a paid run); the service on Windows; more than two analysts submitting at once; the page in browsers other than Chrome.
