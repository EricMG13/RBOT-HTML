# RBOT-HTML

The credit workflow as two Python steps, with a static Issuer Library: no server, no open port and
no compiled executable. This is a lean copy of the engine in
[EricMG13/final-workflow](https://github.com/EricMG13/final-workflow), with a fresh history. That
repository keeps the retained runs, deliverables and design work, and the Go application; none of
them are here.

```
Issuer source files → Run workflow (CP-OS runs the analytical modules) → Markdown handoffs →
delivery → runs/<run>/deliveries/<id>/report.html → Update library → library/index.html
```

Excel files are analytical inputs only; no deliverable is an Excel workbook.

## Start here

| What | Where |
|---|---|
| The two steps, the library's listing rules and the Windows package | [`apps/issuer-library/README.md`](apps/issuer-library/README.md) |
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
`COPILOT_GITHUB_TOKEN`, or `COPILOT_USE_CLI_LOGIN=1` to use the Copilot CLI sign-in, and `COPILOT_CLI_PATH`; see `docs/COPILOT.md`). CP-OS runs the modules in
order and publishes `deliveries/<id>/report.html` inside the run folder.

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

## Current limits

- The automated checks cover handoff structure, issuer/date/source/upstream anchors and report
  selectors. They hold no independent expected values, so a listed run has not had analytical
  review, and each report says so in its scope.
- The launcher publishes the report only; the HTML Model, charts and calculation JSON need
  issuer-specific row selectors.
- The Windows package carries no Copilot SDK or runtime: run Copilot configurations from a
  checkout (`docs/COPILOT.md`).
- Nothing in this repository has been run on Windows yet; `Smoke-test.ps1` in the package is the
  offline acceptance check.

## Repository map

| Folder | Role |
|---|---|
| `src/deploy_workflow/` | CP-OS (`owners/cpos.py`, `owners/cpos_launch.py`), module owners, provider adapters, delivery, and the library's listing rules (`library_index.py`) |
| `src/deploy_vii/` | Analytical code, report renderers and design assets reused by delivery |
| `prompts/`, `docs/reuse/selected-methods/` | The method each module is sent |
| `docs/templates/`, `docs/rulings/` | The context form; rulings that lift the paid-run pause |
| `apps/issuer-library/` | `update_library.py`, the Credit OS store and page parts in `credit_os/`, the package's `engine/run_workflow.py` and `packaging/` |
| `tests/`, `cases/`, `tools/` | Tests, their synthetic fixtures, and the quality gate |
