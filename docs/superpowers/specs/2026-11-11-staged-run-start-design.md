# Staged run start: design (2026-11-11)

Replaces the inbox watcher and folder drop. Status: for owner approval.

## Amendment 2026-11-12: four steps, documents first

Owner, 2026-11-12: step order "Four steps"; prefill "Today's prefill". Record:
`docs/design/2026-11-12-run-start-four-steps.md`.

- The stages of section 4 are now groups shown under five steps: Documents (documents), Purpose
  (pathway), Confirm (issuer and dates, legal), More context (market, valuation, assumptions) and
  Start (review). A step is shown when the level shows any of its groups.
- Decision 4, "Stage 1 is pathway selection", is replaced: the page opens on Documents, and Purpose
  follows once a file is read.
- Basic asks Documents, Purpose, Confirm and Start. More context appears at Basic only for a primary
  run, a held answer, an error or "Answer this now".
- Standard adds the market, valuation and research-question groups under More context; Advanced asks
  everything, as section 5 says.
- The short snapshot shows Documents, Purpose, Confirm and Start at every level.
- Every other rule of this spec stands: the levels' defaults, locks after an error, the summary and
  its ticks, Submit, the USD 20 cap. No field moved between groups.

## 1. Intent

Paid runs are repeated because of human error. Most of it is context that is missing or wrong, or
an analyst who does not know what the supplied documents cannot support. Examples on record:

- `tdg-forecast-003`: the context said `executed` for a folder of public filings. CP-2A blocked,
  CP-2G never ran, and a second paid run was needed.
- `cpos-tdg-sol-medium-all-001`: the as-of date was before the newest filing, so CP-2G excluded it.

Today the analyst fills in a form, downloads `context.json`, puts it in a folder and drops the
folder in `inbox/<pathway>/`. The form cannot see the documents, so every statement about them is
unchecked until a paid module reads them.

The new flow: the analyst opens one page, picks a pathway and a level, supplies the documents, and
answers the context questions stage by stage. Each stage is limited to what the documents can
support. A summary forecasts each module's outcome. The analyst approves it, and Submit starts the
run. The analyst never handles a context file.

## 2. Goals, non-goals, anti-goals

**Goals**
- No paid run starts with a context error the page could have caught.
- The analyst sees each document limitation before approving, with the module it affects.
- One run per approved submission.

**Non-goals**
- No change to the launcher's analysis, the module methods, delivery or the library's listing rules.
- No change to the `context/1` fields that exist today (new optional fields only, section 6).
- No model call before Submit. The build itself runs no provider.
- No login system (section 8).

**Anti-goals** (failure even if it works)
- A summary that forecasts Ready for a module the documents cannot support.
- A level that hides a missing input: Basic must not make a gap invisible.
- A run started without an approved summary, or started twice.
- Copying final-workflow's New run code or markup. It was reviewed for what it got wrong only: it
  asked for context first and the folder second, so declarations stayed unchecked against the files.

## 3. Owner decisions (2026-11-11)

1. A local service replaces "no web server, no port". One user starts it from the command line and
   it serves all other users. The provider key is in that process's environment only.
2. The explicit paid action is now Submit after an approved summary, at USD 20 per run. This
   replaces the folder drop named in `AGENTS.md` and `docs/rulings/2026-11-09-inbox-automation.md`.
3. The start page offers each module's modes and qualifiers, and three levels: Basic, Standard,
   Advanced.
4. Stage 1 is pathway selection. (replaced 2026-11-12, see the amendment)

## 4. Stages

| # | Stage | Shown at | What the analyst does |
|---|---|---|---|
| 1 | Pathway and level | all | Picks one of the six pathways (each card lists its modules), then Basic, Standard or Advanced |
| 2 | Documents | all | Picks the issuer folder; the files upload and are checked; labels each file's type |
| 3 | Issuer and dates | all | Confirms issuer name and ID, as-of date, periods, currency |
| 4 | Legal | where CP-4, CP-2A or CP-4C runs | Points to the agreement file, or says there is none |
| 5 | Market and ratings | Standard, Advanced | Quotes, deal talk, ratings |
| 6 | Peers, valuation and module modes | Standard, Advanced | Peer source, own peers, CP-3 mode, Deep Debate |
| 7 | Assumptions and questions | questions: Standard; pinned assumptions: Advanced | Research questions; CP-2A, CP-2D, CP-3C, CP-3D, CP-4C values |
| 8 | Summary | all | Reads the forecast, ticks each remaining limit, approves |
| 9 | Submit | all | Starts the run; the page moves to its progress |

Rules that hold across stages:
- A stage is shown only when a module in the run uses it, as the current form does. Within that, the
  level decides whether it is asked or defaulted.
- Later stages stay locked while an earlier one has an error.
- Every input names the modules that use it and what is lost without it (existing "Used by" chips).
- The existing form's rules, notes, module forecast and copied tables (`build()`, readiness panel,
  `tests/test_context_form.py`) carry over unchanged unless this document says otherwise.

### Stage 2: Documents

- The browser sends each file to the service; nothing is read from a path the analyst types.
- The service runs the launcher's own offline reading on the uploaded files
  (`cpos_launch._issuer_files`, `run_expectations.guess_kind`), before any other question is
  asked. It adds no second classifier.
- Each file is listed with what the launcher recognises: its kind, its period end (financial
  reports), whether a legal document reads as executed, or "not recognised".
- Files the launcher would skip without saying so are listed as "will not be read", with the
  reason: a suffix outside `SOURCE_SUFFIXES` (for example `.pptx`, `.xls`), or a name starting
  `_` or `~$`. `.docx` is read. A file the launcher refuses (empty, over 50 MiB, an `X.htm`
  beside an `X.htm.jsonl`) is an error on this stage.
- Upload limits, enforced while receiving (my call; the launcher has none beyond 50 MiB a file):
  50 MiB a file, 500 files, 512 MiB in total.
- The newest period end found is shown and feeds stage 3. The analyst may correct it.
- Each kind the pathway uses and the folder lacks is listed as a limitation with the module it
  affects, for example: "No credit agreement recognised. Legal & covenants will stop; Downside
  will be Limited. A 10-K exhibit index is not the agreement."
- The launcher's recognition decides the forecast. The analyst cannot relabel a file into Ready
  (see stage 4).

### Stage 3: Issuer and dates

- The as-of date defaults to the newest document's date. An as-of date before it is a limit the
  analyst must tick, naming the modules that will exclude the later documents.
- The attachment answers (bridge, portfolio workbook, prior case) become "which file is it?",
  chosen from the uploaded files. No file chosen means `false`.

### Stage 4: Legal

- `executed` and `draft` can be chosen only by selecting an uploaded file as the agreement. With
  no file selected, the only answer is `none`, and the consequence is shown.
- If the launcher does not recognise the selected file as a legal document, or reads it as a
  draft where the analyst says executed, the forecast keeps the launcher's reading and the
  disagreement is a limit the analyst must tick. No per-file label is added to `context/1`.
- This replaces the confirmation tick and the file-name folder check.

### Stage 8: Summary

- The service runs the launcher's offline preparation (no provider call) on the uploaded files and
  the built context. A refusal is shown with the stage that fixes it; nothing is started.
- The page shows, per module in run order: Ready, Check, Gap, Limited or Will refuse, with the
  reason and a link to the stage that fixes it. On Basic and Standard, each defaulted input is
  listed with its default.
- It also shows the pathway, issuer, dates, file count, model (sol-medium), the USD 20 cap, and
  the report sections this run fills and does not fill.
- Approval needs one tick per remaining limit. Errors block approval.
- A Gap or Limited caused by an input the level skipped offers "answer this now", which opens that
  one stage without changing the level.

### Stage 9: Submit

- Approval is bound to a digest of the built context, the uploaded files' hashes, the module
  subset and the turns per module. Submit sends the digest; the service refuses if any has
  changed since the summary.
- The summary's offline preparation is the run's one offline check. The uploaded files cannot
  change after approval, so a queued run starts without a second check and stays queued across a
  service restart.
- A submission starts at most one run, however many times Submit is sent.
- The service writes `context.json` into the run's source folder as the run's record.
- The run is queued or started under the existing limits (3 running, 30 a day, USD 20 per run).
  The page then shows that run's progress from Run activity.

## 5. Levels

A level changes how much is asked, never what a module needs.

| Level | Asked | Defaulted |
|---|---|---|
| Basic | Stages 1 to 4, 8, 9 | Peer source `cp_dr_public`, valuation basis `auto`, no quotes or ratings, no pinned assumptions, no questions, CP-3 mode left to the model, Deep Debate off |
| Standard | Basic plus stage 5, stage 6 without valuation detail, and research questions | Pinned assumptions, valuation basis, own multiple |
| Advanced | Everything: also pinned assumptions, valuation basis and own multiple, deal terms, guarantors, aliases, sponsor, module subset, turns per module | Nothing |

- Deal terms stay required for a Primary run at every level (existing rule).
- Changing level keeps answers already given.
- The level, module subset and turns are saved on the run record, not in the context.
- CP-2E is in no pathway, so its pinned assumptions are not shown at any level. They were reachable
  only through a loaded file, and loading a file is removed.

## 6. Module modes and qualifiers

Found by a keyword search of `docs/reuse/selected-methods/skills/*/SKILL.md`,
`src/deploy_vii/methods/` and `context.py`, not a full read of every method file.

| Module | Setting | On the page |
|---|---|---|
| CP-3 Relative value | Execution mode: CLO Screening, Single-Name RV, Capital-Structure RV, Watchlist Monitoring | Stage 6, Standard up; default "let the module decide" |
| CP-6 Committee decision | Deep Debate (opt-in in its method) | Stage 6, Standard up; default off |
| CP-1C Peer benchmark | Peer source; valuation basis; LTM or NTM | Existing fields; basis at Advanced |
| CP-2A, CP-2D, CP-3C, CP-3D, CP-4C | Pinned assumptions | Existing fields; Advanced |
| CP-4 Legal | executed, draft, none | Stage 4 |
| CP-DR Research | Source mode: supplied only, web only, hybrid | Shown as fixed "supplied files only"; web needs its own ruling and is out of scope |
| Whole run | Module subset, turns per module (default 32) | Advanced; dependencies of a chosen module are added |
| Whole run | Model | Fixed sol-medium by the ruling; shown, not offered |

No setting was found for CP-0, CP-1, CP-1A, CP-1B, CP-1D, CP-2, CP-2G, CP-2H or CP-5.

**Carrying the two new settings.** `context/1` gains one optional object, omitted when empty so
existing files load and re-save unchanged:

```json
"module_options": {"cp3_mode": "single_name_rv", "cp6_deep_debate": true}
```

`context.py` validates it. The context is already pinned as a source every module reads as the
user's settings; CP-3's and CP-6's instructions gain one line each telling the module to take the
mode from it when present. Whether the models honour it is proven only by a later paid run.

## 7. The service

- One process, Python standard library only, started as
  `python -m deploy_workflow.run_start --root <root> --host <address> --port <port>`. The default
  host is `127.0.0.1`; the hosting user passes the machine's network address to serve others.
- It refuses to start under the same conditions as the watcher: no provider key, no standing
  ruling, cap above USD 20, path of `<root>` too long, or another instance holding the lock.
- It serves the start page, the uploads, the summary, Submit, and the built library folder
  read-only, so other users can open the Issuer library and Run activity from the same address.
- It takes over the watcher's remaining duties: start prepared runs within the limits, reap ended
  runs, file reports, rebuild the library, publish Run activity, and recover after a restart.
- Folder layout under `<root>`: `_engine/` as today (runs, drops as the uploaded source folders,
  state, logs, library). `inbox/` is no longer created or read.

**Trust boundary.** The service is reachable by anyone on the network segment.
- Uploaded names are reduced to a safe file name; nothing is written outside the submission folder.
- The launcher's size and count limits are enforced while receiving, not after.
- State-changing requests must carry an `Origin` matching the service's own address.
- The key is never sent to a browser or written to a log.
- Unsubmitted uploads older than 24 hours are deleted.

## 8. Access (my call, owner may overrule)

No login. The controls are the USD 20 cap per run and the limits of 3 running and 30 a day. Stage 1
asks for the submitter's name, which is recorded on the run and shown in Run activity. It is
self-declared and proves nothing. An access code or login is a later addition if misuse appears.

## 9. Removed, kept, changed

**Removed**
- `src/deploy_workflow/inbox/watcher.py` and `drops.py` (the settle timer, claiming, `inbox/failed`
  and `WHY.txt`, the `_template` copies), with `tests/test_inbox_watcher.py` and
  `tests/test_inbox_drops.py`.
- `Start watcher.cmd` in `apps/issuer-library/packaging/runtime.py`.
- The form's Download step, "Before you drop" checklist, load-a-file control and legal tick.

**Kept**
- `inbox/runs.py`, `activity.py`, `filing.py` and `startup.py` (records, start, outcome, Run
  activity, filing, lock, launch checks). The package keeps its name; renaming it is churn.
- From `drops.py`: `Layout`, `ensure_layout` and the root-length check, moved to a kept module.
  `write_templates` and its call in `startup.write_pages` go.
- The launcher, `context.py`, the library and its static pages.

**Changed**
- `docs/templates/context-form.html` becomes the start page: same rules and readiness panel, new
  stages 1, 2, 4, 8 and 9, levels, and Submit in place of Download.
- New ruling `docs/rulings/2026-11-11-run-start-submit.md`, which `startup.STANDING_RULING` names.
  The owner approved it in this session on 2026-11-11 ("2. Approved", to "Submit after an approved
  summary, at the same USD 20 cap"). The file quotes those words with `by: user`, the date and
  `configs: sol-medium`, as `check_ruling` requires. The 2026-11-09 ruling stays as history.
- `AGENTS.md`: the paid-execution sentence names Submit after an approved summary.
- `README.md`, `apps/issuer-library/README.md`, `docs/templates/README.md`, `.github/workflows/checks.yml`.

## 10. Verification the plan must include

- Each stage-2 and stage-4 rule has a test that fails without it, including: `executed` cannot be
  built without a labelled agreement file; an as-of date before the newest document needs a tick.
- Submit with a changed file or context is refused; a repeated Submit starts one run.
- A path-traversal upload name and an over-limit upload are refused.
- The three levels build the same context for the same answers; Basic's defaults equal the
  current form's defaults.
- Tests use the existing canned launcher fixtures. No test calls a provider.
- Not proven by this build: that CP-3 and CP-6 honour `module_options`; Windows behaviour of the
  service; several users submitting at once beyond a two-submission test.

## 11. Left to the builder

- Request paths, the upload wire format and the page's internal structure.
- How watcher code that is kept is moved (in place or into the new module).
- The order of the work, provided the watcher is removed only after Submit starts a run end to end.
