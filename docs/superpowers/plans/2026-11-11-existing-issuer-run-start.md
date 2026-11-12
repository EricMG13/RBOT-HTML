# Run Start on an Existing Issuer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An analyst starts a run from an earlier run of the same issuer: the issuer ID is locked, the earlier documents and answers are carried over, and only what changed is asked.

**Architecture:** The service gains three routes: read an earlier run's inputs, copy its source files into a new submission, and look an issuer ID up in the run records. The start page reads `?from=<run id>`, calls them, and fills the form with its existing `fill()`. Summary, digest, seal, Submit and the launcher are untouched.

**Tech Stack:** Python standard library only (`http.server`, `shutil`, `json`); plain JavaScript in `docs/templates/context-form.html` and `apps/issuer-library/credit_os/web/views.js`; pytest; headless Chrome for the page tests.

**Spec:** `docs/superpowers/specs/2026-11-11-existing-issuer-run-start-design.md` (adds to `2026-11-11-staged-run-start-design.md`).

## Global Constraints

- No new dependency. No provider call in any test; use the canned launcher fixtures in `tests/inbox_fixtures.py`.
- No change to `context/1`, `context.py`, the launcher, the digest, the seal, the scheduler or the limits (50 MiB a file, 500 files, 512 MiB in total; 3 running, 30 a day, USD 20 per run).
- No stub or fake value standing in for real behaviour. No catch-all that hides a failure.
- Every state-changing request needs the matching `Origin` (the existing `_check_origin`).
- A run ID is matched against `[0-9A-Za-z._-]{1,80}` and looked up in the run records before any path is built from it.
- Page copy, exact: "carried over from run <id>", "from run <id>", "This issuer exists: N runs, latest as-of <date>", "this is a different issuer", "Start again from this run", "Start a run".
- Each task ends with `uv run python tools/quality_gate.py` exiting 0 and a report whose last line is `Not verified:`.
- Tests run targeted only, each within 300 seconds.
- **Pre-flight (controller, before Task 1):** the CP-8 redesign from the Pause session changes `run_start/submissions.py` and `context-form.html`. If it has merged, rebase onto it and re-check every line number below against the tip. If it has not, build on `main` and omit Task 4 step 7 (the CP-8 summary lines).

## Review Focus

1. A carry from a run whose source folder holds a symlink: refused, nothing copied (Task 1).
2. A carry into a submission that already holds a file of the same name: the stored file is kept and reported, not replaced (Task 1).
3. `?from=` naming a run started before the service (a record, no source folder): the page locks ID and name and says nothing else was carried (Task 3).
4. A reload after `?from=`: the lock and the "from run" marks survive; the files are not copied a second time (Task 3).
5. `?from=` with an ID the service does not hold: the page starts blank and says so; it does not fail silently (Task 3).

---

## File Structure

| File | Responsibility |
|---|---|
| `src/deploy_workflow/run_start/prior.py` (new) | Read an earlier run's inputs and an issuer's runs from the run records |
| `src/deploy_workflow/run_start/submissions.py` | `listing()` and `carry()`: copy a source folder into a submission within the limits |
| `src/deploy_workflow/run_start/service.py` | The three routes |
| `docs/templates/context-form.html` | `?from=`, locked ID, marks, carried files, existing-issuer notice, "Start again from this run" |
| `apps/issuer-library/credit_os/web/views.js` | "Start a run" on Report history |

---

### Task 1: Read an earlier run's inputs and carry its files

**Files:**
- Create: `src/deploy_workflow/run_start/prior.py`
- Modify: `src/deploy_workflow/run_start/submissions.py` (after `remove_file`, line 357)
- Test: `tests/test_run_start_prior.py` (new), `tests/test_run_start_submissions.py`
- Modify: `.github/workflows/checks.yml:46-47` (add `tests/test_run_start_prior.py` to the run-start test list)

**Interfaces:**
- Consumes: `runs.load_all(layout) -> list[Record]`; `Layout.drops`; `submissions._stored`, `add_file`, `_folder`, `_usable_root`, `_LOCK`, `_PENDING`, `Refused`.
- Produces:
  - `submissions.listing(source: Path) -> dict[str, int]`: relative posix name to size of every regular file under `source` except a top-level `context.json`; `Refused` on any link.
  - `submissions.carry(layout: Layout, sid: str, source: Path) -> dict[str, list[str]]`: returns `{"carried": [...], "kept": [...]}`, names sorted.
  - `prior.source(layout: Layout, run_id: str) -> tuple[Record, Path | None]`: `Refused("unknown run")` when no record has that ID; the path is `layout.drops / record.id` when it is a real folder holding a regular `context.json`, else `None`.
  - `prior.inputs(layout: Layout, run_id: str) -> dict[str, Any]` with exactly the keys `run`, `issuer_id`, `issuer_name`, `pathway`, `context`, `files`, `level`, `modules`, `max_turns`. `context` is `None` and `files` is `[]` when there is no source folder. `files` is a list of `{"name": str, "size": int}` sorted by name.
  - `prior.issuer(layout: Layout, issuer_id: str) -> dict[str, Any]` with keys `runs` (count of records with that `issuer_id` and status `finished`), `latest_as_of`, `latest_run`, `issuer_name` (of the record with the greatest `as_of`, any status; `""` when there is none).

- [ ] **Step 1: Write the failing tests for `prior`**

In `tests/test_run_start_prior.py`, using `root`, `fake_env`, `settings`, `submit_run`, `layout` from `inbox_fixtures` (see `tests/test_run_start_scheduler.py` for the fixture pattern that makes a `Scheduler`):

```python
def test_inputs_blank_the_dates_and_list_the_files_without_the_context(scheduler, root):
    record = submit_run(scheduler, root, "acme")
    pump(scheduler, lambda: (layout(root).drops / record.id / "context.json").is_file())
    got = prior.inputs(layout(root), record.id)
    assert set(got) == {"run", "issuer_id", "issuer_name", "pathway", "context",
                        "files", "level", "modules", "max_turns"}
    assert got["issuer_id"] == "acme" and got["run"] == record.id
    run = got["context"]["run"]
    assert [run[k] for k in ("as_of", "cutoff", "current_period", "prior_period")] == [""] * 4
    assert got["context"]["identity"]["issuer_id"] == "acme"
    assert got["files"] == [{"name": "a.txt", "size": len(b"Net sales were 100 for acme.")}]

def test_a_record_without_a_source_folder_gives_identity_only(scheduler, root):
    record = submit_run(scheduler, root, "acme")
    pump(scheduler, lambda: (layout(root).drops / record.id).is_dir())
    shutil.rmtree(layout(root).drops / record.id)
    got = prior.inputs(layout(root), record.id)
    assert got["context"] is None and got["files"] == [] and got["issuer_id"] == "acme"

def test_an_unknown_run_is_refused(root):
    with pytest.raises(submissions.Refused, match="^unknown run$"):
        prior.inputs(layout(root), "20261111-000000-01")

def test_a_linked_source_folder_or_context_is_not_read(scheduler, root): ...
    # replace drops/<id>/context.json with a symlink to a file outside: context is None

def test_issuer_counts_finished_runs_and_names_the_latest(scheduler, root):
    # two runs for "acme" taken to finished with as_of 2026-11-09, one for "other"
    got = prior.issuer(layout(root), "acme")
    assert got == {"runs": 2, "latest_as_of": "2026-11-09",
                   "latest_run": <id of the later record>, "issuer_name": "Acme Corp"}
    assert prior.issuer(layout(root), "nobody") == {
        "runs": 0, "latest_as_of": "", "latest_run": "", "issuer_name": ""}
```

Ties on `as_of` go to the greater run ID (IDs are timestamps).

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_run_start_prior.py -q`
Expected: FAIL, `ModuleNotFoundError: deploy_workflow.run_start.prior`

- [ ] **Step 3: Write the failing tests for `listing` and `carry`**

In `tests/test_run_start_submissions.py`:

```python
def _source(tmp_path, **files):  # name -> bytes; also writes context.json
    ...

def test_carry_copies_every_file_but_the_context(lay, tmp_path):
    src = _source(tmp_path, **{"a.txt": b"one", "sub/b.txt": b"two"})
    sid = submissions.new(lay)
    assert submissions.carry(lay, sid, src) == {"carried": ["a.txt", "sub/b.txt"], "kept": []}
    assert submissions.listing(submissions.files_folder(lay, sid)) == {"a.txt": 3, "sub/b.txt": 3}

def test_carry_keeps_a_name_already_stored(lay, tmp_path):
    # upload a.txt = b"mine" first; carry a source with a.txt = b"theirs" and c.txt
    # result {"carried": ["c.txt"], "kept": ["a.txt"]}; a.txt still reads b"mine"

def test_a_carry_over_a_limit_copies_nothing(lay, tmp_path, monkeypatch):
    monkeypatch.setattr(submissions, "MAX_FILES", 2)
    # source of three files -> Refused matching "more than 2 files"; files folder stays empty
    # repeat with MAX_TOTAL = 4 and two 3-byte files -> Refused matching "in total"; empty

def test_a_carry_from_a_folder_holding_a_link_copies_nothing(lay, tmp_path): ...
    # Refused matching "is a link"; files folder stays empty

def test_a_carry_into_a_sealed_submission_is_refused(lay, tmp_path): ...
    # Refused("this submission has been submitted")

def test_the_digest_of_carried_files_equals_the_digest_of_the_same_files_uploaded(lay, tmp_path):
    # sid_a: carry(src); sid_b: add_file each of the same names and bytes
    # submissions.digest(lay, sid_a, answers) == submissions.digest(lay, sid_b, answers)
```

- [ ] **Step 4: Run to verify they fail**

Run: `uv run pytest tests/test_run_start_submissions.py -q -k "carry or carried"`
Expected: FAIL, `AttributeError: module ... has no attribute 'carry'`

- [ ] **Step 5: Implement `listing` and `carry` in `submissions.py`**

- `listing`: `_stored(source, strict=True)` without the top-level `context.json` key (compare with `casefold()`).
- `carry`: take `listing(source)`. Under `_LOCK`, with `_usable_root(folder)`: split names into kept (already in `_stored(root)`) and to-copy; refuse with the existing texts (`f"more than {MAX_FILES} files"`, `f"more than {MAX_TOTAL // (1024 * 1024)} MB in total"`) when stored plus pending plus to-copy exceeds a limit; refuse a single file over `MAX_FILE` with the existing text. Release the lock, then copy each file by calling `add_file(layout, sid, name, handle, size)` with the file opened `"rb"`. If any `add_file` raises, remove the files this call added (`remove_file`) and re-raise. `# ponytail:` comment: the pre-check and the copies are not one atomic step; `add_file` re-checks each file, and the rollback restores the folder.

- [ ] **Step 6: Implement `prior.py`**

`inputs` reads `context.json` with `json.loads`; anything that is not an object with object-valued `run` and `identity` gives `context: None`. Blank `run.as_of`, `run.cutoff`, `run.current_period`, `run.prior_period` to `""`. `level`, `modules` (as a list) and `max_turns` come from the record.

- [ ] **Step 7: Run all of this task's tests**

Run: `uv run pytest tests/test_run_start_prior.py tests/test_run_start_submissions.py -q`
Expected: PASS

- [ ] **Step 8: Gate and commit**

```bash
uv run python tools/quality_gate.py
git add src/deploy_workflow/run_start/prior.py src/deploy_workflow/run_start/submissions.py tests/test_run_start_prior.py tests/test_run_start_submissions.py .github/workflows/checks.yml
git commit -m "feat(run-start): read an earlier run's inputs and carry its files into a submission"
```

---

### Task 2: The three routes

**Files:**
- Modify: `src/deploy_workflow/run_start/service.py:118-120` (patterns), `:334-357` (`_get`), `:358-371` (`_post`), `:380-385` (`_guarded`)
- Test: `tests/test_run_start_service.py`

**Interfaces:**
- Consumes: Task 1's `prior.inputs`, `prior.issuer`, `prior.source`, `submissions.carry`.
- Produces:
  - `GET /api/runs/<id>/inputs` -> 200 with `prior.inputs`; 404 `unknown run`.
  - `GET /api/issuers/<issuer id>` -> 200 with `prior.issuer`. The ID pattern is `[a-z0-9-]{1,40}`; anything else is the existing 404 for a wrong route.
  - `POST /api/submissions/<sid>/carry` with JSON `{"run": "<id>"}` -> 200 with `submissions.carry`'s result; 404 `unknown run` or `unknown submission`; 400 with the text `that run has no stored documents` when `prior.source` gives no folder; 400 for any other `Refused`.

- [ ] **Step 1: Write the failing tests**

Using the file's `svc` fixture and its request helper (see `test_upload_read_summarise_submit_and_see_the_run` for how a run is made and read back):

```python
def test_an_earlier_runs_inputs_are_read_and_its_files_carried(svc):
    # make a run as test_upload_read_summarise_submit_and_see_the_run does; wait for drops/<id>
    got = svc.get(f"/api/runs/{run}/inputs")
    assert got.status == 200 and got.json["context"]["run"]["as_of"] == ""
    sid = svc.post("/api/submissions").json["id"]
    carried = svc.post(f"/api/submissions/{sid}/carry", {"run": run})
    assert carried.status == 200 and carried.json["kept"] == []
    names = [d["name"] for d in svc.get(f"/api/submissions/{sid}/reading").json["documents"]]
    assert names == [f["name"] for f in got.json["files"]]

def test_inputs_and_carry_for_an_unknown_run_are_404(svc): ...
def test_a_carry_without_or_with_a_foreign_origin_copies_nothing(svc): ...   # 403, as uploads
def test_a_carry_body_that_is_not_a_run_id_is_400(svc): ...   # {"run": "../x"}, {"run": 3}, []
def test_a_carry_from_a_run_without_stored_documents_is_400(svc): ...
def test_an_issuer_id_is_looked_up_and_an_unsafe_one_is_404(svc):
    assert svc.get("/api/issuers/acme").json["runs"] == 1          # after the run finishes
    assert svc.get("/api/issuers/nobody").json["runs"] == 0
    assert svc.get("/api/issuers/..%2Fx").status == 404
def test_the_inputs_route_does_not_serve_file_content(svc):
    # the reply's text does not contain the uploaded file's bytes
```

Extend `test_no_response_carries_the_provider_key` to request the three new routes.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_run_start_service.py -q -k "inputs or carry or issuer"`
Expected: FAIL with 404 where 200 is expected

- [ ] **Step 3: Implement the routes**

Add `carry` to the `_SUBMISSION` action group; add `_RUN_INPUTS = re.compile(r"/api/runs/([0-9A-Za-z._-]{1,80})/inputs")` and `_ISSUER = re.compile(r"/api/issuers/([a-z0-9-]{1,40})")`. `_guarded` maps both `unknown submission` and `unknown run` to 404. The carry body must be an object whose `run` is a string matching the `_RUN` ID pattern.

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_run_start_service.py -q`
Expected: PASS

- [ ] **Step 5: Gate and commit**

```bash
uv run python tools/quality_gate.py
git add src/deploy_workflow/run_start/service.py tests/test_run_start_service.py
git commit -m "feat(run-start): routes for an earlier run's inputs, the carry and the issuer lookup"
```

---

### Task 3: The page starts from an earlier run

**Files:**
- Modify: `docs/templates/context-form.html` (`restore()` at :2081, `save()` at :2071, `resetAll()` at :2401, the issuer ID field at :374, `renderDocs()` at :1981, `renderReview()` near :1800)
- Modify: `tests/test_run_start_page.py:134` (`Page.run` gains `path: str = "/"`, appended to `self.base`)
- Test: `tests/test_run_start_page.py`

**Interfaces:**
- Consumes: Task 2's routes; the page's `call()`, `fill(o, files, quiet)`, `uploadFiles`, `refreshReading`, `renderDocs`, `syncNewest`, `loadMsg`, `save`.
- Produces (page globals later tasks use):
  - `CARRIED = {run: '', files: new Set(), fields: new Set(), locked: false}`.
  - `async function startFrom(runId)`: returns `true` when the run was found.
  - `function unlockIssuer()`.
  - The carried state is saved in `extra.carried` as `{run, files: [...], fields: [...], locked}` and restored by `restore()`.

- [ ] **Step 1: Write the failing tests**

Add a fixture that finishes a run for issuer `acme` with the fake launcher before the page loads (the scheduler from `_serving`, `submit_run`, `pump`), and yields `(page, run_id)`. Tests load `page.run(body, path=f"/?from={run_id}")`. Probe bodies return plain objects:

```python
def test_from_locks_the_issuer_id_and_carries_the_documents(page_from):
    got = page.run("""
      return {id: $('i-issuer_id').value, locked: $('i-issuer_id').readOnly,
              rows: rows(), asOf: $('d-as_of').value, run: CARRIED.run};""", path=...)
    assert got["id"] == "acme" and got["locked"] is True and got["run"] == run_id
    assert any("a.txt" in r[0] and "carried over from run " + run_id in " ".join(r) for r in got["rows"])
    assert got["asOf"] != "2026-11-09"   # the earlier run's as-of date is not carried

def test_a_run_started_from_another_cannot_build_a_different_issuer_id(page_from):
    # type('i-issuer_id', 'other') -> build().identity.issuer_id is still 'acme'
    # click the "this is a different issuer" control -> readOnly false, rows() empty,
    # CARRIED.run === '', and the service's reading for SUB lists no document

def test_carried_answers_are_marked_and_an_edit_removes_the_mark(page_from):
    # an input filled from the earlier context has a sibling/attribute text "from run <id>";
    # after type() on it, the mark is gone and CARRIED.fields no longer has its key

def test_an_executed_agreement_is_not_carried_as_a_file_choice(page_from_executed):
    # earlier context has legal_documents 'executed'; after ?from=, build() gives 'none'
    # and radio('executed').disabled is true until a file is chosen

def test_a_reload_keeps_the_lock_and_does_not_carry_twice(page_from):
    # first run(path=?from=) then run(path="/") with the same profile:
    # locked still true, rows() has each file once, CARRIED.run unchanged

def test_from_a_run_without_stored_documents_locks_identity_only(page_from_bare):
    # drops/<id> removed before load: id and name filled, locked, rows() empty,
    # the load message contains "No documents or answers were kept for run"

def test_from_an_unknown_run_starts_blank_and_says_so(page):
    # path="/?from=20990101-000000-01": i-issuer_id empty and not readOnly,
    # the load message contains "Run 20990101-000000-01 was not found"

def test_the_review_lists_what_was_carried_over(page_from):
    # after review(): the element #rv-carried is shown, names run_id, the file count
    # and each label still in CARRIED.fields
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_run_start_page.py -q -k "from or carried or reload_keeps_the_lock"`
Expected: FAIL (`CARRIED is not defined`)

- [ ] **Step 3: Implement**

- `restore()`: read `new URLSearchParams(location.search).get('from')`. When it matches `/^[0-9A-Za-z._-]{1,80}$/` and no saved submission and no saved run exist, call `startFrom`. When a saved submission exists, restore it as today (this is the reload case) and ignore `from`.
- `startFrom`: `GET /api/runs/<id>/inputs`; on 404 show "Run <id> was not found. This is a blank start." and return `false`. Otherwise create the submission, `POST .../carry` when `files` is non-empty, `refreshReading()`, then `fill(context, {}, true)` when `context` is an object, else set only the issuer name and ID. Set `LEVEL` from `level` when it is in `RANK`. Do not set the submitter. Set `CARRIED`; `fields` is every `data-k` that `fill` gave a non-empty value, except `pathway`.
- Lock: `$('i-issuer_id').readOnly = CARRIED.locked`. Add a button with the text "this is a different issuer" beside it, shown only while locked; `unlockIssuer()` deletes each carried file from the service (`removeFile`), clears `CARRIED`, calls `resetAll()` and `update()`.
- Marks: one `<small class="from-run">from run <id></small>` after each input whose key is in `CARRIED.fields`; the page's existing delegated `input`/`change` handler removes the key and the mark.
- `renderDocs`: a file in `CARRIED.files` shows "carried over from run <id>" in its row.
- `renderReview`: a block `#rv-carried` after `#rv-defaults`: the run ID, the count of carried files, and the labels of the fields still carried. Hidden when `CARRIED.run` is empty.
- `save`/`restore`: `extra.carried` as in Interfaces. `resetAll()` does not clear `CARRIED` (only `unlockIssuer` and `startAgain` do).

- [ ] **Step 4: Run to verify they pass, and that nothing else moved**

Run: `uv run pytest tests/test_run_start_page.py tests/test_context_form.py -q`
Expected: PASS

- [ ] **Step 5: Gate and commit**

```bash
uv run python tools/quality_gate.py
git add docs/templates/context-form.html tests/test_run_start_page.py
git commit -m "feat(run-start): start a run from an earlier run: locked issuer ID, carried documents and answers"
```

---

### Task 4: Existing-issuer notice, start again, and the library link

**Files:**
- Modify: `docs/templates/context-form.html` (stage 3 issuer fields near :374; the progress view `renderRun` at :1858 and `startAgain` at :2494)
- Modify: `apps/issuer-library/credit_os/web/views.js:808-822` (`historyView`)
- Modify: `apps/issuer-library/README.md`, `VERIFICATION.md`
- Test: `tests/test_run_start_page.py`, `tests/test_library_page_browser.py`

**Interfaces:**
- Consumes: Task 2's `GET /api/issuers/<id>`; Task 3's `startFrom`, `CARRIED`; `views.js` `servedOverHttp()`, `historyRows`, `contexts[key].folder` (the run's folder name, which is the service's run ID).

- [ ] **Step 1: Write the failing page tests**

```python
def test_typing_an_existing_issuer_id_shows_the_notice_and_offers_the_carry(page_with_run):
    # blank start; type('i-issuer_name','Acme Corp') (the ID fills to 'acme'); settle
    # #issuer-exists text == "This issuer exists: 1 runs, latest as-of 2026-11-09"
    # clicking its button gives the same state as ?from=: locked, rows() lists a.txt

def test_an_unknown_issuer_id_shows_no_notice(page): ...          # #issuer-exists hidden

def test_a_different_typed_name_is_named_against_the_filed_one(page_with_run):
    # type name 'Acme Holdings', id 'acme' -> notice also contains 'filed as "Acme Corp"'

def test_a_failed_run_offers_start_again_from_this_run(page):
    # submit with fake_env making the launcher fail; wait for the progress view to show failed
    # #run-again is shown with text "Start again from this run"; clicking it leaves the
    # progress view and gives locked === true and CARRIED.run === the failed run's ID

def test_a_finished_or_running_run_does_not_offer_start_again(page): ...   # #run-again hidden
```

The notice says "1 runs" as written: the spec fixes the wording as "N runs".

- [ ] **Step 2: Write the failing library test**

In `tests/test_library_page_browser.py`, following its existing history-view tests:

```python
def test_report_history_links_start_a_run_to_the_latest_run_when_served(...):
    # served over http: the history view has a link with text "Start a run" and
    # href "/?from=<folder of the first row>" (rows are latest as-of first)
def test_report_history_has_no_start_link_from_a_file(...):       # file:// : no such link
```

- [ ] **Step 3: Run to verify they fail**

Run: `uv run pytest tests/test_run_start_page.py tests/test_library_page_browser.py -q -k "notice or start_again or start_a_run or filed_one or start_link"`
Expected: FAIL

- [ ] **Step 4: Implement**

- Notice: on a change of the issuer ID while not locked, and when the ID matches `/^[a-z0-9-]{1,40}$/`, `GET /api/issuers/<id>`; when `runs > 0` or `latest_run` is set, show `#issuer-exists` with the exact sentence, the filed name when it differs from the typed one, and a button "carry over from its latest run" that calls `startFrom(latest_run)`. A failed lookup shows nothing and logs to the console; the run is not blocked by it.
- Start again: `renderRun` shows `#run-again` when `r.status` is one of `failed`, `capped`, `rejected`, `interrupted`. Its click calls the existing `startAgain()` and then `startFrom(RUN's ID)`.
- Library: in `historyView`, when `servedOverHttp()` and there is at least one row, add `<a class="start-run" href="/?from=${encodeURIComponent(first.folder)}">Start a run</a>` above the table, passed through `esc`.

- [ ] **Step 5: Run to verify they pass**

Run: `uv run pytest tests/test_run_start_page.py tests/test_library_page_browser.py -q`
Expected: PASS

- [ ] **Step 6: Docs and the reader check**

- `apps/issuer-library/README.md`: one paragraph on starting a run from Report history and what is and is not carried over.
- `VERIFICATION.md`: one entry with the scope (fake launcher, no provider, macOS Chrome), the test commands and their exit codes, and the reader check `AGENTS.md` requires for a presentation change: one real run's Report history read against the September VMO2 reference with the new link present. Keep the file under 1,000 lines.

- [ ] **Step 7: CP-8 summary lines (only when the CP-8 redesign has merged)**

The summary reply then names the run CP-8 compares against. Show in the review, from that reply and nothing computed on the page: "Changes since run <id> (as-of <date>)" or "First run of this pathway", and, when `CARRIED.run` differs from that run, both IDs. Test: one page test per sentence. Take the reply's field names from the merged CP-8 code; do not invent them.

- [ ] **Step 8: Gate and commit**

```bash
uv run python tools/quality_gate.py
git add docs/templates/context-form.html apps/issuer-library/credit_os/web/views.js apps/issuer-library/README.md VERIFICATION.md tests/test_run_start_page.py tests/test_library_page_browser.py
git commit -m "feat(run-start): existing-issuer notice, start again from a failed run, Start a run on Report history"
```

---

## After the last task

- Run once on the branch: `confidence-review`, `rewrite-tournament` (post-edit, on `carry`, `prior.inputs` and `startFrom`), `ponytail-review`, and the whole-branch review.
- Sensitive code: Tasks 1 and 2 (a network-reachable service copying files). Their review includes `mx-adversary`.
- Not proven by this plan: Windows behaviour of the copy; more than two analysts carrying from one run at once; that old source folders are never removed; a library run the service did not start is invisible to the existing-issuer notice.
