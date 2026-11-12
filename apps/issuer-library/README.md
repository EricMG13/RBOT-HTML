# Issuer Library: two Python steps and static pages

The library is static pages: it needs no server and opens from disk. (The run start page, below,
is a separate service.) There is no compiled executable. Both steps run with a checkout's Python
(`uv sync --locked`) or the Windows package's bundled Python.

1. **Run the workflow**: `Run workflow.cmd` in the package, or
   `python -m deploy_workflow.owners.cpos_launch` from a checkout, with the launcher's options
   (root `README.md`). Without `--live` it only prepares and reviews; `--live` with a ruling is
   the paid run, which publishes the report inside the run folder.
2. **Update the library**: `Update library.cmd [workspace]` in the package, or
   `python apps/issuer-library/update_library.py --workspace <folder>`. It rebuilds
   `<workspace>/library/` and the wrapper opens `library/index.html`. Without an argument the
   wrapper uses `FINAL_WORKFLOW_WORKSPACE`, else `Documents\FinalWorkflow`. The script writes
   nothing but `library/` (built beside it, then swapped in whole), and refuses to write through a
   `library` link.

The run start page's service (below) runs both steps for a shared folder, so analysts do neither
by hand.

`library/` is the Credit OS library (one row per listed run) and, for each run, its issuer report
with tabs for Report history, Overview, Modules, Forecast and Evidence, in that order. Overview
selects each module's own bottom line, key findings and limitations and the nearest dates; Modules
is the flat navigator and each module's page (its charts, maps and timeline included); Forecast is
the cash flow model and the chart index; Evidence lists the source files used, the handoffs (each
downloadable), the calculation and Model files and the run record. The Report history tab is
the issuer's history: one row per run of that issuer, latest as-of date first, with its
pathway, the modules it ran, its status and an "Earlier format" mark for a run whose handoffs
predate the reader format; each row opens that run's Overview. Every run page carries one line
under the tabs naming the run it shows (as-of date, pathway, run code) with a link back to the
history. The left rail is Start a run, Issuer library, Run activity and Search. The library holds
no copy of any delivered report and shows none: an old `#W-Reports/...` or `#W-Calendar/...` link
opens the run's Report history. It has no run controls: runs are made by step 1 and shown by step 2.
`data.js` holds the catalogue and the workspace store as data. Evidence's handoff and instruction
downloads (and "Download all", a zip) are written under `library/downloads/<run>/` as the bytes the
build hash-checked, so they also open when the library is served; other links to run files are
relative (`../runs/...`) and the run start page's service does not serve those. The page opens from disk
(`file://`) and blocks every network request through its content security policy. Its hashes are
checked when it is built: update it after new runs. The page parts are `credit_os/web/`; the
store and its sources are listed in `credit_os/SOURCE.md`.

## Automated: the run start page

`Start run page.cmd <root> [address]` in the package (or
`PYTHONPATH=src uv run python -m deploy_workflow.run_start --root <root> --host <address> --port 8765`
from a checkout) serves the start page. Analysts open `http://<address>:8765/`, upload the issuer's
documents, answer the staged questions, approve the summary and choose Submit; Submit starts a
paid run. The root README (section 3) has the stages, the three levels and the steps.

The summary joins the launcher's forecast with the page's own rules (the worse outcome per module,
both reasons). Approval needs a tick for every Gap, Limited and Will refuse item from either
source, and for every Check that has a fix (a stage to go to); Ready, Note and a Check with
nothing the analyst can do need none. An as-of date before the newest document and a legal answer
the launcher's reading disagrees with are Limited for the whole run.

- **Address:** `127.0.0.1` unless one is given; pass this machine's own address to serve
  colleagues. `0.0.0.0` is refused. The service also serves the library and Run activity,
  read-only; only files under `library/` are served, so `../runs/...` links are not.
- **What happens:** Submit saves the run's record, moves the uploaded files to `_engine\drops\<id>`
  with the `context.json` the page built, and the scheduler starts it as a paid run within the
  limits. The finished report is filed as `issuers\<Issuer name> (<issuer_id>)\<as-of>
  <pathway>[-N].html` and `library.html` in `<root>` opens the library, which is built in
  `<root>\_engine\library`. A `<root>\inbox\` folder from the earlier folder watcher is never read.
- **No login; the limits stand in for one:** USD 20 per run, `sol-medium`, 3 runs at once, 30 runs
  started per day (`--max-running`, `--max-per-day`), 30 submissions waiting, 50 unfinished
  submissions, and uploads of at most 50 MiB a file, 500 files and 512 MiB in total.
- **Key and ruling:** the provider key comes only from the environment of the account that runs
  the service. Every live launch passes the standing ruling `2026-11-11-run-start-submit.md`: in
  the package at `engine\docs\rulings`, from a checkout at `docs\rulings`.
- **One service, one machine:** it holds an operating-system file lock on `_engine\watcher.lock`
  (the name is kept so an old folder watcher and the service exclude each other) while it runs. A
  second one on the same root is refused with exit code 2 ("another run page service (or an old
  folder watcher) is running on this folder"). Run it on one machine only; the lock depends on the
  file system honouring file locks (a local disk does; do not rely on it across machines; on
  Windows the refusal reads "(no details)"). The root must be a folder on this machine's own disk,
  shared to analysts if needed, because the USD 20 cap depends on marker files that must not sit on
  a network or synced path; a root starting with `\\` or `//` is refused. The root path must be 80
  characters or fewer.
- **Waiting runs:** a run waits when 3 are going or 30 have started today; Run activity lists it
  under Waiting and names the daily limit when that is the cause. After a restart, a run that was
  being started when the service stopped is shown as interrupted and is not started again; check
  whether its process is still running before submitting it again. Runs and records the folder
  watcher left still load and show in Run activity; every run it had queued (a record with no
  submission) is marked failed, with the reason, at the service's first start and is never started. If the library cannot be rebuilt, Run activity says so and ended runs
  wait for it.
- **At boot:** Task Scheduler, "At startup", under a service account whose environment holds the
  key, running `Start run page.cmd <root> <address>`. Only the service's account writes `_engine\`,
  `issuers\` and `library.html`.
- **Run activity** on the library page re-loads every 30 s while it is showing. A running run's
  spend counts a call in flight at its full reserved amount, so it can read slightly high.
- **Known limits:** Windows and browsers other than Chrome are not verified; whether the Relative
  value and Committee modules honour the new mode settings is not proven until a paid run; two IDs
  for one issuer make two folders; a run can end slightly above USD 20 after one overrunning call;
  a report leaves the library list after a method update but stays in `issuers\`; whether USD 20
  covers a full pathway on `sol-medium` is not measured.

## Which runs are listed

`src/deploy_workflow/library_index.py` lists a folder under `<workspace>/runs/` only when both
hold:

- **Completed by CP-OS:** a `completed-<sha256>.json` record named by its own hash, of the
  launcher's report kind, names a `delivery-<sha256>.json` manifest named by its own hash; one
  `deliveries/<id>/` folder holds exactly the files its `delivery.json` lists, with those hashes,
  including the report the completion record names; the handoffs still have their hashes; the
  completion record, the manifest and the delivered copies name the same modules and handoffs; and
  the manifest, the delivered `view.json` and `workflow.json` name the same run. The report is not
  rebuilt, so a later renderer change does not unlist a run. The library shows a run from its
  handoffs and presents no delivered report (ruling 2026-11-11, decisions 1 to 3).
- **On the current methodology:** every module was answered in this run (not reused from another
  run, not synthetic). The request record beside its accepted answer still has the fingerprint
  CP-OS named its folder by (`cpos.request_fingerprint`), so it holds the instructions actually
  sent, and their method block is exactly what the launcher sends that module today
  (`cpos_launch.method_text`): no section changed, added or dropped.

Every other folder is left out, with its reason in the command output and in a collapsed list at
the end of the page; a linked folder is reported and not followed. Each listed run shows its
evidence date, pathway, model and effort, exact recorded spend (unknown charges counted, never
zeroed), its scope statement, and each module's reader summary quoted from the handoff. "Latest"
is per issuer by evidence date; runs sharing that date are all marked and counted.

## Starting a run from Report history

When the library is served over http, an issuer's Report history has a "Start a run" link above its
table; it works only when that server is the run start service. It opens the start page from the latest
run listed (`/?from=<run id>`): the issuer ID is locked to that run's, its documents are copied into
the new submission, and its pathway, answers, module subset and turns per module fill the form. Each
carried-over answer, the pathway, the module box and the turns input carries a "from run <id>" mark
beside it, and the review lists them in one block; editing one removes its mark. Each carried
document is marked "carried over from run <id>" and removable; a file the analyst uploads over a
carried name is theirs and is not marked. Not carried, and not marked: the as-of and cutoff dates
and periods, the submitter (the analyst's own name is kept), and the answers that depend on a chosen
file (the agreement, bridge, portfolio and prior-case files). A subset naming a module the pathway
lacks is not carried at all. When the earlier run has no usable stored answers, only the issuer name
and ID are carried and nothing the analyst typed is cleared. "This is a different issuer" drops the
carry (the level and the analyst's own uploads stay). If the browser still holds a submitted run,
the link shows that run's progress with "Run <from> has not been started from yet: this page is
showing run <stored id>." and "Start another run" then starts from `<from>`; when the stored run has
already ended, the page starts from `<from>` at once. The link is absent when the library is opened
from disk. The start page also says when a typed issuer ID already has runs (and, if the typed name
differs from the filed one, shows the filed name), and a failed, capped, rejected or interrupted
run's progress view offers "Start again from this run".

## Windows package

`python apps/issuer-library/packaging/build.py` makes `artifacts/issuer-library/Issuer-Library-<arch>.zip`
for amd64 and arm64: the official embeddable Python 3.13.15 and the pinned wheels, each verified
against its SHA-256 digest at build time; the engine's `src`, methods and prompts; the update
script, the Credit OS store and page parts; `Run workflow.cmd`, `Update library.cmd`,
`Start run page.cmd` and `Smoke-test.ps1`. It ships one ruling, the run page's standing one;
any other paid run needs a ruling written in `engine\docs\rulings`. It ships no Copilot SDK or
runtime either, so run the Copilot configurations from a checkout. The bundled Python's
`python313._pth` lists `engine\src`, because the embeddable Python ignores `PYTHONPATH`.

The package is a pilot build, not a signed enterprise release, and it has not been run on Windows.
Run `Smoke-test.ps1` on the target host as acceptance: it checks the bundled Python, an offline run
review and a library update in a temporary folder, and calls no provider. IT can sign the
interpreter and wrap the launch scripts in its own signed shortcuts.
