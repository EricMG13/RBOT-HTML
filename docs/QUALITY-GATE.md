# Quality gate for changed code

`tools/quality_gate.py` holds new and changed Python code to a readability,
maintainability, complexity and typing standard without requiring a rewrite of the
existing code. It runs on pull requests (`.github/workflows/checks.yml`), by hand
("Run workflow": off a PR it checks the last commit, `HEAD~1`) and locally:

```bash
uv run python tools/quality_gate.py            # compares with origin/main
uv run python tools/quality_gate.py --base main --json
```

## Scope: changed code, not changed files

The gate diffs the working tree against `--base`. In scope are every changed line and
the whole body of every function (decorators included) that a changed line falls in.
A new file is in scope whole. Findings outside that scope are dropped, so a one-line
edit in a 60-branch legacy function reports the function's complexity, while an edit
elsewhere in the same file does not. Standard library only (`ast`, `subprocess`,
`git diff -U0`); the checkers are the dev dependencies the repo already pins.

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
node --test apps/issuer-library/static/logic.test.cjs
```

- `checks.yml`, on every pull request and by hand: the changed-code gate above; the fast tests
  (`-m "not live and not browser"`, the files listed in the workflow) with the known failures in
  `tests/known-failures.txt` deselected; and the page logic under Node.
- `weekly-tests.yml`, every Sunday at 01:00 UTC and by hand: the whole suite, slow files
  included, with the same markers and deselections. A failure there that is not in
  `tests/known-failures.txt` is new.
- The browser check of the generated page (`tests/test_library_page_browser.py`, marker
  `browser`) needs Node with the `playwright` package; it is run by hand.
- Paid provider runs are never part of CI. They are an explicit command with a ruling
  (`docs/COPILOT.md`, `README.md`).
