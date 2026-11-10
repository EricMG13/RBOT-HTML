# Issuer Library: two Python steps and static pages

No web server, no port, no compiled executable. Both steps run with a checkout's Python
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

The watcher (below) runs both steps for a shared folder, so analysts do neither by hand.

`library/` is the Credit OS library (one row per listed run) and, for each run, its issuer report
with tabs for Overview, Modules, Calendar, Forecast, Reports and Evidence. It has no run controls:
runs are made by step 1 and shown by step 2. `data.js` holds the catalogue and the workspace store
as data; `reports/<run>/<delivery>/report.html` is each run's delivered report with the library's
presentation added before its last `</body>` (the original in the run folder is never changed;
downloads point at it). Links to run files are relative (`../runs/...`). The page opens from disk
(`file://`) and blocks every network request through its content security policy. Its hashes are
checked when it is built: update it after new runs. The page parts are `credit_os/web/`; the
store and its sources are listed in `credit_os/SOURCE.md`.

## Automated: the inbox

`Start watcher.cmd <root>` in the package (or
`python -m deploy_workflow.inbox.watcher --root <root>` from a checkout) watches
`<root>\inbox\<pathway>\`. Analysts fill in `_template\context-form.html`, put the downloaded
`context.json` and the source files in a folder, and copy it into the pathway folder. The root
README (section 3) has the full steps.

- **What happens:** a drop that has not changed for 2 minutes is moved out of the inbox, checked,
  and started as a paid run. A refused drop goes to `inbox\failed\<time> <name>\` with a
  `WHY.txt`. The finished report is filed as `issuers\<Issuer name> (<issuer_id>)\<as-of>
  <pathway>[-N].html` and `library.html` in `<root>` opens the library, which is built in
  `<root>\_engine\library`.
- **Limits and defaults:** USD 20 per run, `sol-medium`, 3 runs at once, 30 runs started per day,
  120 s settle, 10 s poll. Each is a watcher flag.
- **Key and ruling:** the provider key comes only from the environment of the account that runs
  the watcher. Every launch passes `engine\docs\rulings\2026-11-09-inbox-automation.md`.
- **One watcher per root:** `_engine\watcher.lock` refuses a second. The root path must be 80
  characters or fewer.
- **At boot:** Task Scheduler, "At startup", under a service account whose environment holds the
  key, running `Start watcher.cmd <root>`. Give analysts modify on `inbox\` and read elsewhere;
  only the watcher's account writes `_engine\`, `issuers\` and `library.html`.
- **Run activity** on the library page re-loads every 30 s while it is showing. A running run's
  spend counts a call in flight at its full reserved amount, so it can read slightly high.
- **Known limits:** nothing has been run on Windows or over a network share; a copy that fails
  part-way and is left in the inbox looks complete (the files read are listed in Run activity);
  two IDs for one issuer make two folders; a run can end slightly above USD 20 after one
  overrunning call; a report leaves the library list after a method update but stays in
  `issuers\`; the form copies use system fonts; whether USD 20 covers a full pathway on
  `sol-medium` is not measured.

## Which runs are listed

`src/deploy_workflow/library_index.py` lists a folder under `<workspace>/runs/` only when both
hold:

- **Completed by CP-OS:** a `completed-<sha256>.json` record named by its own hash, of the
  launcher's report kind, names a `delivery-<sha256>.json` manifest named by its own hash; one
  `deliveries/<id>/` folder holds exactly the files its `delivery.json` lists, with those hashes,
  including the report the completion record names; the handoffs still have their hashes; the
  completion record, the manifest and the delivered copies name the same modules and handoffs; and
  the manifest, the delivered `view.json` and `workflow.json` name the same run. The report is not
  rebuilt, so a later renderer change does not unlist a run.
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

## Windows package

`python apps/issuer-library/packaging/build.py` makes `artifacts/issuer-library/Issuer-Library-<arch>.zip`
for amd64 and arm64: the official embeddable Python 3.13.15 and the pinned wheels, each verified
against its SHA-256 digest at build time; the engine's `src`, methods and prompts; the update
script, the Credit OS store and page parts; `Run workflow.cmd`, `Update library.cmd`,
`Start watcher.cmd` and `Smoke-test.ps1`. It ships one ruling, the inbox watcher's standing one;
any other paid run needs a ruling written in `engine\docs\rulings`. It ships no Copilot SDK or
runtime either, so run the Copilot configurations from a checkout. The bundled Python's
`python313._pth` lists `engine\src`, because the embeddable Python ignores `PYTHONPATH`.

The package is a pilot build, not a signed enterprise release, and it has not been run on Windows.
Run `Smoke-test.ps1` on the target host as acceptance: it checks the bundled Python, an offline run
review and a library update in a temporary folder, and calls no provider. IT can sign the
interpreter and wrap the launch scripts in its own signed shortcuts.
