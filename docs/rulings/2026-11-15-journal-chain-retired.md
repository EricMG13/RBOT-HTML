# The Deploy VII journal chain's harness and runner are retired

by: user
date: 2026-11-15

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line. No provider was called.

Owner's words, 2026-11-15, shown that CP-OS (`python -m deploy_workflow.owners.cpos_launch`) never
calls the Deploy VII `OwnerWorkflow` journal chain, which a harness and tests still exercise, and that
removing it means retiring the `model_testing` harness and about 10,000 lines: "retire it".
AGENTS.md: "CP-OS is this version's active orchestrator ... Do not add a competing orchestration
layer."

## Scope

The map behind this record is a static call graph from the entry points people and workflows use
(`cpos_launch`, `run_start`, `signal`, `update_library.py`, `engine/run_workflow.py`, the packaging
scripts, `tools/*.py`, the three workflows). It follows calls, `getattr` strings, registries of module
objects and lazy imports. The launcher's offline runs and the CI fast list were run beside it as
supporting coverage.

The map found the chain much larger than 10,000 lines. Besides `model_testing`, `run_pathway`,
`replay` and `OwnerWorkflow`, only the chain reaches about 45,000 source lines:

- every owner module (cp0_attachments, cp1a to cpl10, cpdr, pins, valuation_basis, blank);
- `host`, `workflow`, `run_inputs`, `model.loop`, `prompts` and `tools`;
- `financial_workflow`, `statement_*`, `earnings*` and most of `research`.

These hold deterministic checks and calculations that CP-OS does not use on a Markdown handoff. The
coordinating session took that part back to the owner (stage c below). This record covers only
the stages done.

## Removed

- **Stage u: code nothing imports, tests included.** 5,282 lines.
  - `rendering.py` and `financial_rendering.py`.
  - `tools/upstream.py`.
  - `prompts/rules.py`, `prompts/digest.py` and the 28 `prompts/rule_lists/*.json` that only they
    read.
  - `cpos_status.py`.
  - `owners/cpos.run_live_comparison`, which nothing calls. It was the entry point of the
    2026-11-06 comparison ruling; CP-8 now runs as a run's last module.
- **Stage a: the `model_testing` harness.** Its 12 modules and its command line
  (`python -m deploy_workflow.model_testing`). 3,217 lines.
- **Stage b: `run_pathway`, `replay`, `owner_rendering` and `identity_check`.** 3,305 lines.
  `run_pathway` lost its only caller in stage a. The others served only it.

The tests removed are 8, all in `tests/model/test_live_limits.py`: they tested `run_pathway`'s own
output cap and bytes-per-token bounds. No test file was deleted.

## Moved, and kept

- **`CONFIGS`, `ModelConfig` and `Role`** moved from `model_testing/configs.py` to
  `model/configs.py`, unchanged. They are what `--config` and the run start page select.
- **`RunDirBusy` and `_single_writer`** moved from `run_pathway.py` to `model/run_lock.py`. They
  are the run-folder lock CP-OS and the handoff executor take. Their refusal now says "held by
  another run".
- **Ignored imports.** The two `.importlinter` ignored imports these moves made unnecessary are
  deleted.
- **Retained runs.** Nothing the library or CP-8 reads from a retained run was touched. The library
  build from the synthetic fixture is identical, apart from its build time and workspace path.

## Stage c, not done (owner's decision pending)

These remain, reached only by `tests/model` (`test_loop.py`, `test_o5_done_when.py`, part of
`test_live_limits.py` and `test_long_context_pricing.py`) and `tests/test_financial_workflow.py`:

- `OwnerWorkflow`, `model.loop`, `prompts`, `host`, `workflow`, `run_inputs` and `tools`;
- the owner modules, `financial_workflow`, `statement_*`, `earnings*`, `unit_maps`, `pdf_headers`,
  `inline_xbrl`, `context_cites` and `context_periods`;
- `research` apart from `weblookup` and `webfetch`.

Before any of them can go:

- CP-OS takes about 37 definitions from `owners/cp2g.py` (the forecast drivers, operands and
  ratio helpers `cpos_forecast` and `cpos_periods` use) and 8 from `owners/period_basis.py`. These
  must be kept or moved first.
- CP-OS also takes `workflow._put`, `WorkflowError`, `run_scopes.PUBLIC_S1A_MODULES`, and
  `model.loop`'s `_caught`, `redacted_request` and `redacted_turn` (through `model.handoff`).

## Superseded

- **The model_testing case list.** `2026-11-13-full-and-lite-credit-assessments.md` says the
  `model_testing/configs.py` case list "drives paid stage plans and needs an issuer case folder ...
  Deferred until the paid lite run". That sentence is superseded: the case list and its stage plans
  are removed. Paid runs go through CP-OS and its rulings.
- **The METHODOLOGY-REVIEW.md row on execution and ordering.** It says "`run_pathway` and
  `OwnerWorkflow` already do execution and ordering". That row records the review as it was. It is
  not current: CP-OS orders and runs the modules.
