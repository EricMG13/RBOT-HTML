# RBOT-HTML

The credit workflow as two Python steps, or one watcher that runs them for a shared folder, with a
static Issuer Library: no web server, no open port and no compiled executable. This is a lean copy of the engine in
[EricMG13/final-workflow](https://github.com/EricMG13/final-workflow), with a fresh history. That
repository keeps the retained runs, deliverables and design work, and the Go application; none of
them are here.

```
Issuer source files → Run workflow (CP-OS runs the analytical modules) → Markdown handoffs →
delivery → runs/<run>/deliveries/<id>/report.html → Update library → library/index.html
```

Excel files are analytical inputs only; no deliverable is an Excel workbook.

The two steps can be run by hand (sections 1 and 2) or by the inbox watcher (section 3), which
starts a paid run for each folder an analyst drops in a shared folder.

## Start here

| What | Where |
|---|---|
| The two steps, the inbox, the library's listing rules and the Windows package | [`apps/issuer-library/README.md`](apps/issuer-library/README.md) |
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
  [the context form](docs/templates/context-form.html), which opens from disk.
- **Issuer folder:** read recursively; PDF, TXT, Markdown, XLSX, CSV, JSON, JSONL and HTML files.
- **Model:** `--config` is `sol-medium`, `sol-high`, `opus-medium`, `deepseek-max`,
  `copilot-sol-medium` or `copilot-opus-medium`.
- **Cap:** a USD ceiling for the run folder; a cap too small for one call is refused offline.

Add `--live --ruling docs/rulings/<file>.md` to start the paid run. The ruling must name the
selected config, and the provider key must be in the launching environment (for Copilot,
`COPILOT_GITHUB_TOKEN`, or `COPILOT_USE_GH_LOGIN=1` to use the gh CLI login (its account pays), and `COPILOT_CLI_PATH`; see `docs/COPILOT.md`). CP-OS runs the modules in
order and publishes `deliveries/<id>/report.html` inside the run folder.

**Web search for the research module.** CP-DR searches the web for the peers only when the
ruling's `configs:` line also lists `web-search` (for example `configs: sol-medium, web-search`),
and only on the OpenAI configs (`sol-medium`, `sol-high`). Each search costs USD 0.01, and each
CP-DR call holds USD 0.16 more for up to 16 searches (`cases/pricing/openai-web-search.json`).
Queries leave the environment, so CP-DR is told to put only public names in them. Without
`web-search` it reads only the run's files. The launcher's `Web:` line says which applies.

## 2. Update the library

```bash
uv run python apps/issuer-library/update_library.py --workspace "$PWD"
```

It rebuilds `library/` (git-ignored) as static files that open from disk: the Credit OS library
and, for each listed run, an issuer report with its tabs (Overview, Modules, Calendar, Forecast,
Reports, Evidence). There are no run controls; new runs are made by the launcher, and
`update_library.py` is the step that shows them. Each run's report is shown from a presented copy
under `library/reports/`; the delivered report in the run folder is never changed. It lists only
runs CP-OS completed with a verified report in which every module ran on the current methodology,
and says why each other run folder is left out.

## 3. Automated: the inbox

One watcher process runs on one machine. Analysts only copy folders. The watcher starts a paid
run for each folder, and the finished report appears in the issuer library.

### What an analyst does

1. Open `inbox\<pathway>\_template\context-form.html` (it opens from disk) and work through its
   stages. The pathway is already chosen, and the form asks only for what that pathway's modules
   use. Its Run readiness panel says what each module is expected to do with your answers. Before
   the download, it asks you to acknowledge any expected limits. Download `context.json`.
2. Make a folder. Put `context.json` and the issuer's source files in it (PDF, TXT, Markdown,
   XLSX, CSV, JSON, JSONL or HTML).
3. Copy the folder into `inbox\<pathway>\`. The pathways are `credit_snapshot`,
   `earnings_update`, `relative_value`, `covenant_refinancing`, `distressed_restructuring` and
   `portfolio_decision`.
4. Open `library.html` in the shared folder. The run appears under Run activity. When it ends,
   the report is in the library and in `issuers\`. If the drop is refused, it is in
   `inbox\failed\` with a `WHY.txt` that says why.

What you will see: the folder leaves the inbox about 2 minutes after the copy stops changing. The
watcher waits that long so it never reads a half-copied folder. It also waits while another
program holds one of the files open. Run activity re-loads every 30 seconds while it is showing.
A drop waits in a queue when 3 runs are going or 30 have started today. Run activity lists it
under Waiting and says why when the daily limit is the cause. A running run's spend counts a call in flight at its full reserved amount, so it can read a little
high until that call settles.

A drop is refused, with the reason in `WHY.txt`, when:

- it has no context file, or more than one;
- the context file is invalid, or names another pathway than the folder it was dropped in;
- it has no source file the launcher can read;
- its `issuer_id` is longer than 40 characters;
- it holds a symbolic link or junction (Windows shortcut files are not links; they are ignored
  like any unsupported file) or a special file;
- it cannot be read;
- the launcher's offline check refuses it (the same check as a run without `--live`).

A loose file, or a folder placed in `inbox\` outside a pathway folder, is refused too, and keeps
its own name inside its `inbox\failed\` folder. Fix the folder and drop it again. Folders and
files whose names start with `.` or `~$` (and `Thumbs.db`, `desktop.ini`) are ignored without a
report. The `inbox\failed\<time>` folder names use the watcher machine's local time; Run
activity shows UTC.

A ready drop that the watcher cannot move out of the inbox (its account lacks the right to move
it, or `_engine` is on another volume) stays where it is. It is logged once in
`_engine\logs\watcher.log`, and Run activity shows a note naming the folder and the error until
the drop is taken in or removed.

A drop is put back in the inbox only if its first record cannot be saved, and never after that.
If it cannot be moved to `inbox\failed\`, it stays in
`_engine\drops\<id>` and Run activity shows it as rejected, with the reason. A file in a drop
that cannot be opened makes the drop rejected with "cannot be read" after the settle time. If the
library cannot be rebuilt, Run activity says so and ended runs wait for it.

After a restart, a run that was being started when the watcher stopped is shown as interrupted
and is not started again; check whether its process is still running before dropping the folder
again. A folder the watcher was taking in when it stopped is shown as rejected, with its files
kept in `_engine\drops\<id>`.

### The shared folder

```
<root>\
  library.html                       opens the issuer library
  inbox\<pathway>\                   analysts drop folders here
  inbox\<pathway>\_template\context-form.html
  inbox\failed\<time> <name>\WHY.txt refused drops, with the reason
  issuers\<Issuer name> (<issuer_id>)\<as-of> <pathway>[-N].html    filed reports
  _engine\                          runs, drops, state, logs, library, activity.js, watcher.lock
```

A filed report is never overwritten: a second report for the same date and pathway is filed as
`-2`, `-3` and so on. The path of `<root>` must be 80 characters or fewer; the watcher refuses a
longer one.

### Start the watcher

From a checkout:

```bash
PYTHONPATH=src uv run python -m deploy_workflow.inbox.watcher --root /path/to/shared-folder
```

On Windows, put `set PYTHONPATH=src` on its own line before the command. The package is not
installed in a checkout, so without `PYTHONPATH` the command fails with `ModuleNotFoundError`.

From the Windows package: `Start watcher.cmd <root>`. Without an argument it uses
`FINAL_WORKFLOW_WORKSPACE`; with neither it prints the usage and exits 1.

The watcher refuses to start when the provider key is missing from its environment
(`OPENAI_API_KEY` for the default `sol-medium`), when the ruling does not allow the config, or when
another watcher already holds `_engine\watcher.lock` for that folder. The watcher holds an
operating-system file lock on that file for as long as it runs. A second watcher on the same
folder is refused with exit code 2 and "another watcher is running on this folder (<host>
<pid>)" (on Windows the holder cannot be read, so the text reads "(no details)"). Run the watcher on one machine only. The lock depends on the file system honouring file
locks: a local disk does; do not rely on it across machines. Press Ctrl-C to stop it; runs already started keep going, and a restarted watcher
picks them up. Its log is `_engine\logs\watcher.log`.

| Flag | Default |
|---|---|
| `--cap` | USD 20 per run |
| `--config` | `sol-medium` |
| `--max-running` | 3 runs at once |
| `--max-per-day` | 30 runs started per local day |
| `--settle-seconds` | 120 |
| `--poll-seconds` | 10 |
| `--ruling` | `docs/rulings/2026-11-09-inbox-automation.md` |

Every live launch passes that standing ruling. The provider key comes only from the environment of
the account that runs the watcher; nothing reads a credential file.

### Start it at boot (Windows)

In Task Scheduler, create a task that runs "At startup" under a service account whose environment
holds the provider key. The action is `Start watcher.cmd <root>` from the package folder. `<root>`
must be a folder on the watcher machine's own disk, shared to analysts: the USD 20 cap depends on
marker files that must not sit on a network or synced path, and the watcher refuses a root that
starts with `\\` or `//`. Use a full local path, not a mapped drive letter (mapped drives do not
exist at start-up). Put the path to `Start watcher.cmd` in quotes, because it holds a space. Do
not end `<root>` with a backslash. The setup person sets the folder permissions:

- analysts: modify on `inbox\`, read on everything else;
- only the watcher's account writes `_engine\`, `issuers\` and `library.html`.

### Limits of the inbox

- Nothing has been run on Windows or over a network share.
- A copy that fails part-way and is left in the inbox looks complete once it stops changing. The
  files the run read are listed in Run activity.
- Two IDs for one issuer make two folders in `issuers\`.
- A run can end slightly above USD 20 after one call overruns the cap.
- A report leaves the library list after a method update (see "Which runs are listed" in the
  library README) but stays in `issuers\`.
- A form copy already in `inbox\<pathway>\_template\` is never replaced. After the form changes,
  delete those copies and restart the watcher; it writes the new form at start.
- Whether USD 20 covers a full pathway on `sol-medium` has not been measured.

## Current limits

- The automated checks cover handoff structure, issuer/date/source/upstream anchors and report
  selectors. They hold no independent expected values, so a listed run has not had analytical
  review, and each report says so in its scope.
- The launcher publishes the report only; the HTML Model, charts and calculation JSON need
  issuer-specific row selectors.
- The Windows package carries no Copilot SDK or runtime: run Copilot configurations from a
  checkout (`docs/COPILOT.md`).
- Nothing in this repository has been run on Windows yet; `Smoke-test.ps1` in the package is the
  offline acceptance check. The inbox watcher has been exercised only through a fake launcher on
  macOS, with no provider called (`VERIFICATION.md`).
- The inbox has its own limits, listed at the end of section 3.

## Repository map

| Folder | Role |
|---|---|
| `src/deploy_workflow/` | CP-OS (`owners/cpos.py`, `owners/cpos_launch.py`), module owners, provider adapters, delivery, and the library's listing rules (`library_index.py`) |
| `src/deploy_vii/` | Analytical code, report renderers and design assets reused by delivery |
| `prompts/`, `docs/reuse/selected-methods/` | The method each module is sent |
| `docs/templates/`, `docs/rulings/` | The context form; rulings that lift the paid-run pause (the inbox's standing one is `2026-11-09-inbox-automation.md`) |
| `src/deploy_workflow/inbox/` | The inbox watcher: drops, runs, filing and run activity |
| `apps/issuer-library/` | `update_library.py`, the Credit OS store and page parts in `credit_os/`, the package's `engine/run_workflow.py` and `packaging/` |
| `tests/`, `cases/`, `tools/` | Tests, their synthetic fixtures, and the quality gate |
