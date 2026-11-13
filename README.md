# RBOT-HTML

The credit workflow as two Python steps, or one run page service that starts them for analysts, with a
static Issuer Library that opens from disk. The only server is the run page service (section 3);
there is no compiled executable. This is a lean copy of the engine in
[EricMG13/final-workflow](https://github.com/EricMG13/final-workflow), with a fresh history. That
repository keeps the retained runs, deliverables and design work, and the Go application; none of
them are here.

```
Issuer source files → Run workflow (CP-OS runs the analytical modules) → Markdown handoffs →
delivery → runs/<run>/deliveries/<id>/ (no delivered page) → Update library → library/index.html
```

Excel files are analytical inputs only; no deliverable is an Excel workbook.

The owner's ruling of 2026-11-11 ([`docs/rulings/2026-11-11-reader-and-issuer-report.md`](docs/rulings/2026-11-11-reader-and-issuer-report.md))
retires the delivered `report.html` as a deliverable: a report becomes one run shown natively in the
issuer library (Report history, then Overview, Modules, Forecast and Evidence), with the HTML Model,
charts and calculation JSON as parts of it. New runs publish no delivered `report.html`; the library
shows each run natively, and earlier runs keep the page they were delivered with.

The two steps can be run by hand (sections 1 and 2) or from the run start page (section 3), where
an analyst uploads the issuer's documents, answers staged questions and approves a summary; Submit
starts a paid run.

## Start here

| What | Where |
|---|---|
| The two steps, the run start page, the library's listing rules and the Windows package | [`apps/issuer-library/README.md`](apps/issuer-library/README.md) |
| Project rules | [`AGENTS.md`](AGENTS.md) |
| Which method revision each module uses | [`METHODOLOGY-REVIEW.md`](METHODOLOGY-REVIEW.md) |
| Running the models through GitHub Copilot | [`docs/COPILOT.md`](docs/COPILOT.md) |
| Quality gate and test schedule | [`docs/QUALITY-GATE.md`](docs/QUALITY-GATE.md) |
| Verification record | [`VERIFICATION.md`](VERIFICATION.md) |

## Set up

Python 3.13 and uv 0.12.5:

```bash
uv sync --locked
```

## 1. Run the workflow

Without `--live` this only prepares: it reads every file, writes the pinned manifest and module
instructions, prints the plan and calls no provider.

```bash
uv run python -m deploy_workflow.owners.cpos_launch \
  --context path/to/context.json \
  --sources path/to/issuer-folder \
  --config copilot-sol-medium \
  --cap 12 \
  --out runs/my-first-run
```

- **Context file:** a `context/1` file, such as one from
  the run start page (section 3), which builds one from your answers.
- **Issuer folder:** read recursively; PDF, Word (.docx), TXT, Markdown, XLSX, CSV, JSON, JSONL and
  HTML files.
- **Model:** `--config` is `sol-medium`, `sol-high`, `opus-medium`, `deepseek-max`,
  `copilot-sol-medium` or `copilot-opus-medium`.
- **Cap:** a USD ceiling for the run folder; a cap too small for one call is refused offline.

Add `--live --ruling docs/rulings/<file>.md` to start the paid run. The ruling must name the
selected config, and the provider key must be in the launching environment (for Copilot,
`COPILOT_GITHUB_TOKEN`, or `COPILOT_USE_GH_LOGIN=1` to use the gh CLI login (its account pays), and `COPILOT_CLI_PATH`; see `docs/COPILOT.md`). CP-OS runs the modules in
order and publishes the delivery (handoff files, model and calculation outputs, no report page) under `deliveries/<id>/` inside the run folder.

**Web search for the research module.** CP-DR searches the web for the peers only when the
ruling's `configs:` line also lists `web-search` (for example `configs: sol-medium, web-search`),
and only on the OpenAI configs (`sol-medium`, `sol-high`). Each search costs USD 0.01, and each
CP-DR call holds USD 0.16 more for up to 16 searches (`cases/pricing/openai-web-search.json`).
Queries leave the environment, so CP-DR is told to put only public names in them. Without
`web-search` it reads only the run's files. The launcher's `Web:` line says which applies. Runs started
from the run start page search the web for CP-DR: the standing ruling lists `web-search` (2026-11-12). The
offline cap check holds the same USD 0.16 for each CP-DR call as the live loop.

## 2. Update the library

```bash
uv run python apps/issuer-library/update_library.py --workspace "$PWD"
```

It rebuilds `library/` (git-ignored) as static files that open from disk: the Credit OS library
and, for each listed run, an issuer report with its tabs (Report history, Overview, Modules,
Forecast, Evidence). There are no run controls; new runs are made by the launcher, and
`update_library.py` is the step that shows them. Every page is built from the run's own handoffs:
the library presents no delivered report and has no Calendar or Reports tab, and nothing is
written under `library/reports/`. Evidence's handoff and instruction downloads are byte-for-byte
copies under `library/downloads/<run>/`; the run folder is never changed. It lists only runs
CP-OS completed (the completion record, delivery manifest and delivered files still match the
hashes they record) in which every module was answered in that run, and says why each other
run folder is left out. A run whose module methods have since changed is listed and marked
"Earlier methods".

## 3. The run start page

One service process runs on one machine and serves a start page. Analysts upload the issuer's
documents, answer staged questions, approve a summary and choose Submit, which starts a paid run.
The finished report appears in the issuer library. Analysts never handle a context file.

### Start the service

From a checkout:

```bash
PYTHONPATH=src uv run python -m deploy_workflow.run_start --root /path/to/shared-folder --host <address> --port 8765
```

On Windows, put `set PYTHONPATH=src` on its own line before the command. The package is not
installed in a checkout, so without `PYTHONPATH` the command fails with `ModuleNotFoundError`.

From the Windows package: `Start run page.cmd <root> [address]`. Without a folder it uses
`FINAL_WORKFLOW_WORKSPACE`; with neither it prints the usage and exits 1. Without an address it
uses `127.0.0.1`, which only this machine can reach.

To serve colleagues, the hosting user passes this machine's own network address as `--host`
(or as the second argument of `Start run page.cmd`). Analysts then open `http://<address>:8765/` in
Chrome. `0.0.0.0` is refused: the service accepts only requests addressed to the address it was
given. The same address also serves the issuer library and Run activity, read-only.

The service refuses to start (exit code 2) when the provider key is missing from its environment
(`OPENAI_API_KEY` for the default `sol-medium`), when the standing ruling
`docs/rulings/2026-11-11-run-start-submit.md` does not allow the config, when `<root>` is a network
path or longer than 80 characters, or when another service already holds `_engine\watcher.lock`
for that folder (the file keeps its old name so an old folder watcher and this service exclude each
other). Use a folder on this machine's own disk, shared to analysts if needed: the USD 20 cap
depends on marker files that must not sit on a network or synced path. The provider key comes only
from the environment of the account that runs the service; nothing reads a credential file.
Press Ctrl-C to stop it; runs already started keep going, and a restarted service picks them up.
Its log is `_engine\logs\watcher.log`. `--max-running` and `--max-per-day` change the two limits
below; the USD 20 cap is the ruling's and cannot be raised.

### There is no login

Anyone who can reach the address can use the page. These limits stand in for a login:

- USD 20 a run, at most 3 runs going at once and 30 started a day;
- at most 30 submissions waiting for a slot, and 50 unfinished submissions open at once;
- uploads of at most 50 MiB a file, 500 files and 512 MiB in total; an unsubmitted upload is
  deleted after 24 hours.

State-changing requests must carry an `Origin` that matches the service's own address. The page
asks for the submitter's name, which is recorded and shown in Run activity; it is self-declared
and proves nothing.

### What an analyst does

Open the address and work through five steps. A group of questions appears only when a module in
the run uses it, and a later step stays locked while an earlier one has an error.

1. **Documents.** Choose the issuer's folder, or add files; the files upload and the launcher's own
   offline reading says what it recognises in each (kind, period end, whether a legal document reads
   as executed) and which files it will not read. Documents shows only what was read. Once a purpose
   is chosen, each kind the pathway uses and the folder lacks is listed from Purpose on, in the
   readiness column, as a limitation with the module it affects.
2. **Purpose.** Pick one of `credit_snapshot`, `earnings_update`, `relative_value`,
   `covenant_refinancing`, `distressed_restructuring`, `portfolio_decision` or
   `lite_credit_assessment` (the Lite credit assessment: CP-0, CP-1, CP-1A, CP-2 and CP-2A; no
   forecast is published). `credit_snapshot` is titled "Full credit assessment". The short credit
   snapshot (`short_snapshot`, CP-0, CP-1 and one CP-L10 page) is deactivated: it is not offered and
   a new run of it is refused; the lite credit assessment is the short option. Each row lists its
   modules. Pick Basic,
   Standard or Advanced, and enter your name. At Advanced the module list and the turns per module
   are here too.
3. **Confirm.** Issuer name and ID (at most 40 characters), as-of date, periods and currency. An
   as-of date before the newest document is a limit for the whole run, and you must tick it on the
   summary. Legal, where CP-4, CP-2A or CP-4C runs: choose the uploaded agreement file, or say there
   is none. `executed` and `draft` can be chosen only by selecting a file.
4. **More context.** Standard and Advanced (at Basic only for a primary run, a held answer, an error
   or "Answer this now"): market and ratings; peers, valuation and module modes (the peer source,
   your own peers, the Relative value mode and Deep Debate for the Committee module); research
   questions at Standard; pinned assumptions at Advanced. What shows depends on the pathway: the
   lite credit assessment shows four steps at Basic and Standard (Documents, Purpose, Confirm and
   Start) and five at Advanced, which adds More context; the other pathways show four at Basic and
   five at Standard and Advanced. A primary run still shows More context with its deal terms (Market)
   at every level.
5. **Start.** The summary: the forecast for each module in run order (Ready, Check, Gap, Limited or
   Will refuse), with the reason and the step that fixes it, and each defaulted input with its
   default. The table joins the launcher's forecast and the page's own rules; where both speak of a
   module it shows the worse outcome and both reasons. Approval needs one tick for every Gap,
   Limited and Will refuse item, from either source, and for every Check that has a fix (a step to
   go to: "I have checked this"). Ready, Note and a Check with nothing you can do need none. A
   legal answer the launcher's reading disagrees with, and an as-of date before the newest
   document, are Limited for the whole run. On an earnings run, fewer than two recognised reporting
   periods is a Check that links to Documents. An error blocks approval. Submit starts the run; the
   page moves to its progress in Run activity.

Submit is refused if a file, an answer, the module list or the turns changed after the summary, and
a submission starts at most one run however many times Submit is sent.

**The three levels.** A level changes how much is asked, never what a module needs.

| Level | Asked | Defaulted |
|---|---|---|
| Basic | Documents, Purpose, Confirm and Start | See below |
| Standard | Basic, plus More context where the pathway has it (market inputs, peers and module settings, research questions); none for the lite credit assessment (a primary run still shows More context with its deal terms) | Pinned assumptions, valuation basis, own multiple |
| Advanced | Everything: also pinned assumptions, valuation basis and own multiple, deal terms, guarantors, aliases, sponsor, the module subset and turns per module | Nothing |

Basic defaults: peer source `cp_dr_public` (the research module finds the peers from public
sources), valuation basis `auto`, no quotes or ratings, no pinned assumptions, no research
questions, the Relative value mode left to the model, and Deep Debate off. The summary lists each
defaulted input with its default. Deal terms stay required for a Primary run at every level.
Changing level keeps the answers already given.

**What the summary is.** Its forecast is the launcher's own offline reading of the uploaded files
and your answers; no model is called. A paid run can still differ from it.

### The shared folder

```
<root>\
  library.html                       opens the issuer library
  issuers\<Issuer name> (<issuer_id>)\<as-of> <pathway>[-N].html    filed reports
  _engine\                          runs, drops, uploads, state, logs, library, activity.js, watcher.lock
```

`_engine\drops\<id>` holds each submitted run's source files and its `context.json`. A filed report
is never overwritten: a second report for the same date and pathway is filed as `-2`, `-3` and so
on. A `<root>\inbox\` folder left by the earlier folder watcher is never created, read or changed;
runs it recorded still load and show in Run activity. Every one it had queued (a record with no
submission) is marked failed, with the reason, the first time the service starts, and is never
started; submit it again from the page.

Run activity re-loads every 30 seconds while it is showing. Run activity does not show spend; the USD 20 cap is shown on the run start page before Submit, and a finished run's provider cap and settled amounts are on its Evidence page.
A run waits when 3 are going or 30 have started today; Run activity lists it under Waiting and says why
when the daily limit is the cause. After a restart, a run that was being started when the service
stopped is shown as interrupted and is not started again; check whether its process is still
running before submitting it again. If the library cannot be rebuilt, Run activity says so and
ended runs wait for it.

### Start it at boot (Windows)

In Task Scheduler, create a task that runs "At startup" under a service account whose environment
holds the provider key. The action is `Start run page.cmd <root> <address>` from the package
folder. `<root>` must be a full local path on this machine's own disk, not a mapped drive letter
(mapped drives do not exist at start-up), and must not start with `\\` or `//`. Put the path to
`Start run page.cmd` in quotes, because it holds a space. Do not end `<root>` with a backslash.
The setup person sets the folder permissions: analysts use the page and need no access to the
folder (read access only if they open `library.html` from it); only the service's account writes
`_engine\`, `issuers\` and `library.html`.

### Limits of the run start page

- Library download links of the form `../runs/...` are not served by the service.
- Windows, and browsers other than Chrome, are not verified.
- Whether the Relative value and Committee modules honour the new mode settings
  (`module_options`) is not proven until a paid run.
- Two IDs for one issuer make two folders in `issuers\`.
- A run can end slightly above USD 20 after one call overruns the cap.
- A report leaves the library list after a method update (see "Which runs are listed" in the
  library README) but stays in `issuers\`.
- Whether USD 20 covers a full pathway on `sol-medium` has not been measured.

## 4. Signal (news feed, command line only)

Signal collects stories from news, regulator and ratings feeds that the owner has approved, folds
duplicate stories and keeps them in a local SQLite store under `<root>/signal/`. Slice 1 is the
store and the command line; pages, the AI pass, digests and login are later slices.

```
python -m deploy_workflow.signal --root <root> users add <name> --role <reader|writer|owner>
python -m deploy_workflow.signal --root <root> sources propose <name> --kind <kind> --url <url> --by <name>
python -m deploy_workflow.signal --root <root> sources approve <id>     # or: sources pause <id>
python -m deploy_workflow.signal --root <root> sources list
python -m deploy_workflow.signal --root <root> ingest                   # add --loop for a pass every 60 s
python -m deploy_workflow.signal --root <root> stories --limit 20
```

Only approved sources are fetched. Design: `docs/superpowers/specs/2026-11-13-signal-design.md`.
Candidate sources: `docs/signal/sources.json` (85 checked on 2026-11-13, 60 meet tier A (fetched and parsed with dated items); none
is approved until the owner approves it).

Known limits: DNS, connect and TLS handshake cannot be interrupted (the worker may outlive a timed-out fetch until its own timeout), DNS rebinding is not defended against, and two ingest passes running at once may both fetch a due source.

## Current limits

- The automated checks cover handoff structure, issuer/date/source/upstream anchors and report
  selectors. They hold no independent expected values, so a listed run has not had analytical
  review, and each report says so in its scope.
- The launcher publishes the report only; the HTML Model, charts and calculation JSON need
  issuer-specific row selectors.
- The Windows package carries no Copilot SDK or runtime: run Copilot configurations from a
  checkout (`docs/COPILOT.md`).
- Nothing in this repository has been run on Windows yet; `Smoke-test.ps1` in the package is the
  offline acceptance check. The run start page and its scheduler have been exercised only through
  fake and canned launchers on macOS, with no provider called (`VERIFICATION.md`).
- The run start page has its own limits, listed at the end of section 3.

## Repository map

| Folder | Role |
|---|---|
| `src/deploy_workflow/` | CP-OS (`owners/cpos.py`, `owners/cpos_launch.py`), module owners, provider adapters, delivery, and the library's listing rules (`library_index.py`) |
| `src/deploy_vii/` | Analytical code, report renderers and design assets reused by delivery |
| `prompts/`, `docs/reuse/selected-methods/` | The method each module is sent |
| `docs/templates/`, `docs/rulings/` | The run start page's form; rulings that lift the paid-run pause (the run page's standing one is `2026-11-11-run-start-submit.md`) |
| `src/deploy_workflow/inbox/`, `src/deploy_workflow/run_start/` | The scheduler (starts, reaps and files runs), run records, filing and run activity; the start page's service and its uploads |
| `apps/issuer-library/` | `update_library.py`, the Credit OS store and page parts in `credit_os/`, the package's `engine/run_workflow.py` and `packaging/` |
| `tests/`, `cases/`, `tools/` | Tests, their synthetic fixtures, and the quality gate |
