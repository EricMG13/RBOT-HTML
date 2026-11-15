# Quality gate for changed code

`tools/quality_gate.py` holds new and changed Python code to a readability,
maintainability, complexity and typing standard without requiring a rewrite of the
existing code. It runs on pull requests (`.github/workflows/checks.yml`), by hand
("Run workflow": off a PR it checks the last commit, `HEAD~1`) and locally:

```bash
uv run python tools/quality_gate.py            # compares with origin/main
uv run python tools/quality_gate.py --base main --json
uv run python tools/quality_gate.py --checks code      # or imports; all is the default
```

## Scope: changed code, not changed files

The gate diffs the working tree against `--base`. In scope are every changed line and
the whole body of every function (decorators included) that a changed line falls in.
A new file is in scope whole. A moved file (git `diff -B -M`: a rename, or a copy whose old
name now holds something else, such as an alias) is compared with the file it was moved from, so
moving legacy code does not put all of it in scope; a plain copy is new code. Findings outside
that scope are dropped, so a one-line
edit in a 60-branch legacy function reports the function's complexity, while an edit
elsewhere in the same file does not. Standard library only (`ast`, `subprocess`,
`git diff -U0`); the checkers are the dev dependencies the repo already pins.
Lines moved verbatim out of another file into a new file are not changed lines either: a run
of at least three lines that stands, line for line and in order, among the consecutive lines
another file lost. Splitting a file therefore brings only the new files' imports and any edited
function into scope; an edit inside a moved function still brings that whole function in, and the
same text pasted into a file that already existed is an edit of that file. Code that only moved
(by either rule) is still checked for names that no longer resolve (ruff's `F` rules), because a
move can break code without changing a line of it.

## Checks and thresholds

| Check | Threshold | Source of the threshold |
|---|---|---|
| `ruff check` with `tools/ruff-gate.toml` | the repo's rule set plus E501 (100 columns), C901, PLR0911, PLR0912, PLR0913, PLR0915 | repo `pyproject.toml`; pylint design limits at ruff's defaults (returns 6, branches 12, arguments 5, statements 50) |
| McCabe complexity (C901) | 15 | pydantic-ai (`mccabe max-complexity = 15`); ruff's default 10 is exceeded by 180 existing functions, Home Assistant uses 25 |
| `ruff format` | no change in scope | repo formatter settings |
| `mypy` | strict, errors in scope; `tests/` excluded | repo `[tool.mypy] strict = true`; tests are typed by convention only |

Comparable projects read for the thresholds: pydantic-ai (C90 at 15, mypy and pyright
strict), Home Assistant (PL and C selected, complexity 25, PLR09xx ignored), OpenBB
(PLR selected, max-args 8, max-branches 26, max-returns 9), LangChain core (`ALL`
minus C90 and PLR09), Code Climate defaults (complexity 5, 25-line methods, 4 arguments),
SonarQube S3776 cognitive complexity 15.

## Import direction (whole tree)

A second step runs `lint-imports` (import-linter, a dev dependency) on the contracts in
`.importlinter`. Import direction is a property of the whole tree, so this step is not limited
to the changed code; it reports one finding per broken contract, with lint-imports' report of the
offending import chains. Every import counts: module level, inside a function and under
`TYPE_CHECKING`. In CI it is its own step of the `changed-code` job.

- `deploy_vii`, the engine, imports neither `deploy_workflow` nor `credit_os` (no exceptions).
  A module the engine needs moves down into `deploy_vii`; its old `deploy_workflow` name stays as
  an alias of the moved module, so existing imports and monkeypatches keep working.
- `deploy_workflow` is layered, top to bottom: services (`run_start`, `inbox`, `signal`);
  orchestration (`owners.cpos_launch`, `owners.cpos`);
  delivery (library index, changes, Markdown and handoff delivery, rendering, `owners.cpos_cp1_check`);
  analytical (`owner_workflow`, `earnings*`, `financial_workflow`, the module owners, and the
  runtime they share in one import cycle: `host`, `workflow`, `model`, `prompts`, `research`,
  `tools`, `run_inputs`, `run_events`); engine (context, platform, text, series and period helpers,
  `owners.pins`). The layers come from the import graph, not from a target design.
- The contract is exhaustive: a new module of `deploy_workflow` or of `deploy_workflow.owners`
  fails until it is listed in a layer (for owners, in both contracts;
  `tests/test_quality_gate.py` checks that they agree).
- Ignored imports are debt. Each is listed in `.importlinter` with what would remove it; the list
  may only shrink.
- Not covered: the declared run-time cycle between `deploy_workflow` and the issuer library.

## Baseline this gate does not try to clear

Measured in EricMG13/final-workflow, from which this repository's engine was copied.

Measured at `a313b50` on `src`, `apps` and `workflow.py`: 180 functions above
complexity 10 (62 above 15, 15 above 25); 160 with more than 5 arguments, 94 with
more than 12 branches, 56 with more than 50 statements, 33 with more than 6 returns;
356 lines over 100 columns; 46 files `ruff format` would change (27 of them in `src`);
mypy strict reports 33 errors in `src` and 110 with `apps/issuer-library/engine`.
That is why the gate is scoped to changed code. Reducing the baseline is separate work.

## Reading a report

```
src/x.py:120: ruff C901 `f` is too complex (17 > 15)
src/x.py:131: mypy return-value Incompatible return value type ...  [return-value]
src/x.py:140: format FMT ruff format would change
quality gate: 3 finding(s) in 2 changed file(s), 212 line(s) in scope
```

Exit 1 while findings remain, 2 when the gate itself could not run (unknown base ref,
tool missing). A `# noqa` or `# type: ignore[...]` with a reason is the escape hatch, and
the reviewer sees it in the diff.

## Fast tests while working, the full suite weekly

While working, run the targeted tests for what changed, each run within a few minutes
(`timeout 300`), for example:

```bash
uv run pytest tests/test_library_index.py tests/test_update_library.py tests/test_cpos_launch.py -q
node --test apps/issuer-library/credit_os/web/reader.test.cjs apps/issuer-library/credit_os/web/static.test.cjs apps/issuer-library/credit_os/web/calendar.test.cjs
```

- `checks.yml`, on every pull request and by hand: the changed-code gate and the import
  direction above; the fast tests (`-m "not live and not browser"`, the files listed in the
  workflow) with the known failures in `tests/known-failures.txt` deselected; and the page logic
  under Node.
- `weekly-tests.yml`, every Sunday at 01:00 UTC and by hand: the whole suite, slow files
  included, with the same markers and deselections. A failure there that is not in
  `tests/known-failures.txt` is new.
- The browser check of the generated page (`tests/test_library_page_browser.py`, marker
  `browser`) needs Node with the `playwright` package; it is run by hand.
- Paid provider runs are never part of CI. They are an explicit command with a ruling
  (`docs/COPILOT.md`, `README.md`).
