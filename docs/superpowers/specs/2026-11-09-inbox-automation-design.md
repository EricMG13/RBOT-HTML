# Inbox automation: drop a folder, get a report

Date: 2026-11-09. Status: revised after adversarial review; ready for owner approval.

## Intent

Analysts should not run commands. Today a run needs someone at a terminal to run the launcher,
write a ruling, run it again with `--live`, then run `update_library.py`. The owner wants a
hands-off workflow: an analyst drops an issuer folder into the inbox for a pathway, the run
starts by itself within a budget, its progress shows in the library, and the finished report
appears in a folder for that issuer.

The owner states this is a different build: the project rules that require a separate approval
and a ruling for each paid run do not apply to it. The brake on spend is the cap per run.

## The analyst's journey

1. Get the issuer's source files and fill in that pathway's context template.
2. Put both in one folder and copy it into `inbox/<pathway>/` on the shared folder.
3. Open `library.html` at the root and watch **Run activity**.
4. When the run finishes, open its report from the library, or straight from
   `issuers/<Issuer name> (<issuer_id>)/`.

## Goals

- A folder dropped into `inbox/<pathway>/` starts a live run with no other action.
- The library shows running, queued, finished, failed and rejected work, and keeps itself current.
- Every finished report is filed under the issuer's folder, one file per run.

## Non-goals

- A hosted web app. The library still opens from disk (`file://`).
- OneDrive or SharePoint sync (owner: plain shared folders).
- Approvals, rulings written per run, or other human gates.
- A dollar ceiling across runs (owner: only the per-run cap).
- Automatic retry of a failed or capped run.
- Alerts (Teams, email or other). Analysts watch the library (owner).
- Migrating existing runs. The shared root starts empty (owner).
- Excel deliverables (unchanged project rule).

## Anti-goals: a failure even if it works

- A run starts twice from one drop, or starts while the folder is still being copied.
- A model call starts when its hold does not fit under the $20 cap.
- An existing report in `issuers/` is overwritten or silently replaced.
- A drop disappears without a trace: every drop ends as a run or in `inbox/failed/` with a reason.
- A provider key is written to the shared folder, a log or the page.
- The library shows a run as finished when CP-OS did not complete it with a verified report.
- A run keeps spending while the library shows it as stopped.

## Decisions made with the owner

| Topic | Decision |
| --- | --- |
| Where | A plain shared folder (network share). No OneDrive, no SharePoint. |
| Who runs it | One always-on machine runs a background watcher. Analysts run nothing. |
| Inbox | `inbox/<pathway>/`, one subfolder per pathway: `credit_snapshot`, `earnings_update`, `relative_value`, `covenant_refinancing`, `distressed_restructuring`, `portfolio_decision`. |
| What a drop holds | One folder: the issuer's source files and a context file. |
| Context | One context template per pathway; the pathway comes from the inbox folder. |
| Approvals | None. A drop starts the paid run. |
| Budget | $20 cap per run. No dollar ceiling across runs. |
| Concurrency | More than one run at a time. |
| Write access | Enforced by folder permissions: analysts can write only in `inbox/` and read everything else; only the watcher's account writes `_engine/`, `issuers/` and `library.html`. |
| Existing runs | Not migrated. |
| Library | A single `library.html` at the root. |
| Issuer folders | One folder per issuer under `issuers/`, holding every report for that issuer. |
| Alerts | None. |

## Calls made by the designer (owner may overrule)

- **The shared root is a folder on the always-on machine's own disk, shared to analysts.** The
  watcher and the launcher then work on a local disk. The budget's cap depends on write-once
  marker files with `fsync` in each run folder (`model/budget.py`); those must not sit on a
  network or synced path. If the share has to live on a file server instead, live runs stay on
  the watcher's local disk and a run folder is copied to the share only when it has ended.
- **Up to 3 runs at once** (setting). Further drops wait in arrival order.
- **At most 30 runs started per day** (setting). This is a circuit breaker against a loop or a
  mistaken bulk copy, not a budget. Drops beyond it wait and Run activity says why.
- **Model: `sol-medium` for every pathway**, set once in the watcher's config.
- **A drop is ready when** nothing in it has changed for 2 minutes (setting) **and** every file
  in it can be opened for exclusive access (a file still being copied on Windows cannot).
- **A ready drop is moved out of the inbox** into its run folder before the run starts, so it
  cannot start twice. Run activity lists the files each run read, so an analyst can see a
  short copy.
- **A repeat drop** (same issuer, pathway and as-of date) runs in its own folder with a suffix
  (`-2`, `-3`).
- **Issuer folders are keyed by `issuer_id`** and named `<Issuer name> (<issuer_id>)`. The
  watcher keeps the list of IDs and names it has seen in `_engine/`. A later drop with a known
  ID goes to that folder; if its name differs, Run activity flags it. `issuer_id` is limited to
  40 characters in the context templates.
- **Report file name:** `<as-of date> <pathway>.html` plus the repeat suffix. A name that
  exists is never overwritten.
- **One file per run in `issuers/`, a known limit:** a copied `report.html` loses links to
  sibling files (`model.html`, `calculation.json`). Today's launcher does not publish those.
  When it does, each run's filed output becomes a small folder.
- **The library updates without reloading the page.** On the Run activity view only, the page
  re-loads one small activity script every 30 s. An analyst reading a report inside the library
  is not interrupted.
- **Engine files go in `_engine/`** (`_engine/runs/`, the library's assets and data). Analysts
  can read it, so the library's links into run folders work, but they have no reason to open it.
- **The ruling gate is met by one standing ruling**, `docs/rulings/2026-11-09-inbox-automation.md`,
  naming `sol-medium` and quoting the owner's instruction. The watcher passes it on every launch.
  The launcher's ruling check is not removed or bypassed.

## How it works

```
analyst ─copy─▶ inbox/<pathway>/<folder>
                     │ watcher: wait until ready, check, move
                     ▼
        _engine/runs/<short-id>/   ◀── cpos_launch --live (cap $20, sol-medium)
                     │ events.jsonl (module_started / module_accepted / …)
                     ▼
        _engine/library/activity.js  (small; rewritten on every event)
                     │ when a run ends
                     ▼
        issuers/<Issuer name> (<issuer_id>)/<date> <pathway>.html
        library.html + library data rebuilt
```

### The watcher

- One long-running Python process on the always-on machine, started at boot (Windows Task
  Scheduler or a service wrapper; builder's choice).
- Polls `inbox/*/`. It ignores `inbox/failed/` and the `_template/` folders.
- For each ready drop: check it, move it, launch the run as a separate process with the
  existing launcher (`deploy_workflow.owners.cpos_launch`), and track it. It does not order or
  run modules itself; CP-OS stays the only orchestrator.
- **Each run has a lock file holding its process ID.** On restart the watcher re-adopts a run
  whose process is still alive, and marks a run "interrupted" only when its process is gone.
  A live run always counts against the limit of 3.
- **Two kinds of update.** Each run event rewrites only `activity.js` (written to a temporary
  file, then renamed over the old one). The full library rebuild and the copy into `issuers/`
  happen only when a run ends.
- **Path length.** The watcher names each run folder with a short ID (date, pathway, a short
  issuer key, a counter). A test builds the longest path the engine writes under the configured
  root and fails if it passes 260 characters.

### Checking a drop (rejected → `inbox/failed/<time> <folder>/` with `WHY.txt`)

- No context file, or more than one.
- The context does not validate against that pathway's template, or names a different pathway.
- No source file the launcher can read (PDF, TXT, MD, XLSX, CSV, JSON, JSONL, HTML).
- The launcher's offline preparation fails. The watcher runs the prepare step first (no
  provider call), then the live step.
- Anything else left in the inbox (a loose file, a folder at the wrong level) is rejected the
  same way once it is ready, so nothing sits unreported.

The time prefix keeps two rejected drops with the same name apart.

### Budget

- The launcher enforces the cap by reserving a hold before each call; a call whose hold does not
  fit under $20 does not start, and the run stops as "capped".
- One call can cost more than its hold. The budget code records that as an overrun and stops
  the run. Run activity shows the actual spend, so a run can end slightly above $20; it cannot
  continue above it.

### The library

- `library.html` at the root is the page analysts open; its assets and data are in
  `_engine/library/`.
- It keeps the existing listing rules for finished runs (`library_index.py`): only runs CP-OS
  completed with a verified report on the current methodology. **Known behaviour:** after a
  method update, older runs leave the library list. Their reports stay in `issuers/`, and the
  page says how many filed reports are not listed and why.
Amended 2026-11-11: a run whose methods have since changed is listed and marked 'Earlier methods' (docs/rulings/2026-11-11-reader-and-issuer-report.md).
- **Run activity** shows, from `activity.js`:
  - **Running:** issuer, pathway, drop folder, start time, each module's state (from
    `events.jsonl`), spend against the cap, and the files read.
  - **Queued:** drops waiting for a slot or held by the daily limit.
  - **Finished, failed, capped, rejected, interrupted:** with the time, spend and reason, and a
    link to the report for finished runs.
- The page cannot fetch JSON under `file://`, so activity is a script file, like today's
  `data.js`. All text that came from an analyst or a model (folder names, issuer names, reasons)
  is escaped before it reaches the page.

### Reports opened from `issuers/`

- The file is a copy of the delivered report. The original in the run folder is never changed.
- The report shell already carries its own content security policy that blocks network requests
  (`deploy_vii/assets/shell.html`). A test checks the filed copy still has it.
- The folder name is made safe for Windows (no `\ / : * ? " < > |`, no reserved names such as
  `CON`, no trailing dot or space, a length limit).

### Keys and access

- The provider key is an environment variable of the watcher's service account on the always-on
  machine. It is never in the shared folder, a config file, a log or the page.
- Only administrators log on to that machine. Analysts reach it only through the share.

## Build order and proof

1. **Rules first.** Update `AGENTS.md` to record the owner's change (a drop is the explicit
   action; the standing ruling; the cap per run), and add the standing ruling. Without this the
   build conflicts with the project's own instructions.
2. **A Windows spike before the plan is fixed.** On the real always-on machine: run the
   launcher's offline preparation and the budget's marker writes on a local disk, copy a folder
   into the share from another machine and confirm the "ready" check waits for it, and open
   `library.html` from the share on an analyst machine. Nothing in this repository has run on
   Windows.
3. **One measured live run** of a full pathway on `sol-medium`, to learn whether $20 is enough.
   The only recorded spends are partial `sol-high` runs.
4. Then the watcher, activity view and issuer filing.

**Done means** these pass, using a fake launcher that writes events and spends nothing:

- A drop copied slowly does not start until the copy ends; it then starts exactly once.
- Each rejection reason puts the drop in `inbox/failed/` with the right `WHY.txt`.
- A fourth drop waits while three run; the thirty-first of the day waits with its reason shown.
- Killing and restarting the watcher mid-run re-adopts the live run and starts no duplicate.
- A repeat drop gets a suffix and no filed report is overwritten.
- Hostile folder and issuer names (script tags, `..`, `CON`, 200 characters) are shown as text
  and filed safely.
- The longest engine path stays under 260 characters.
- One real live run, from drop to a report opened from the issuer folder (labelled as one
  issuer and date, not proof of other pathways).

## Constraints

- No credential files. The provider key comes only from the watcher's environment.
- Several runs at once can spend $20 each.
- Provider rate limits: 3 concurrent runs may hit them; lower the setting if retries pile up.
- Never mutate predecessor repositories or historical run folders (unchanged rule).

## Left to the builder

- How to package and start the watcher on Windows, and its settings file format.
- How module state and spend are read for Run activity (`events.jsonl` and the budget's records).
- What each per-pathway context template contains, taken from the existing `context/1` schema
  and `docs/templates/context-form.html`: fields the pathway does not need are left out, and
  the pathway is filled in.
- How today's `library/` output becomes `library.html` + `_engine/library/`.

## Not covered or not verified

- Nothing here has been run on Windows or over a network share (build step 2).
- Whether $20 covers a full pathway on `sol-medium` (build step 3).
- `issuer_id` is typed by the analyst. The watcher flags a known ID with a different name, but
  two different IDs for one issuer still make two folders.
- A copy that fails part-way and is left in the inbox looks complete to the watcher. The list
  of files read in Run activity is the only signal.
- The current limit stands: a listed report has had no analytical review, and says so.
