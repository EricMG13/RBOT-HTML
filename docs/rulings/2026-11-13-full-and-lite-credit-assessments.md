# Full and lite credit assessments; short credit snapshot deactivated

by: user
date: 2026-11-13

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line; paid execution still needs its own explicit action. No lite run has been made.

Owner's words, 2026-11-13: "create full credit snapshot (full credit assessment) and a shorter version
(lite credit assessment) to replace L10"; "L10 - keep it wired but deactivated"; "add cp-2a to lite";
"cost - test locally first, but also consider prompt and output size"; "Yes, build it".

## Decisions

- Full credit assessment is the existing `credit_snapshot` pathway. Its id stays `credit_snapshot`
  (CP-8 matches earlier runs on the id; a new id would orphan them). Only its display title changes.
  Its modules and report blocks are unchanged.
- Lite credit assessment is a new pathway, id `lite_credit_assessment`. Preset: CP-0, CP-1, CP-1A,
  CP-2, CP-2A (no CP-MODEL, no forecast). CP-8 runs last when an earlier lite run of the same issuer exists, as for every
  pathway. Its report holds nine blocks: key findings, company operating model, the Model chart strip,
  credit metrics, strengths and weaknesses, company profile, transaction summary, downside stress and
  break points.
- The short credit snapshot (`short_snapshot`, CP-L10) stays wired and is deactivated: the run-start page
  does not offer it, and a new run of it is refused at the launcher, the run-start summary and the inbox
  submit, with the message "The short credit snapshot is deactivated. Use the lite credit assessment."
  Kept: the pathway id, its preset, `src/deploy_vii/methods/cpl10.md`, the Key figures check,
  its lead module, the library's display of past runs, and the lower-level functions that build its
  instructions. Nothing is deleted.
- This supersedes, for new runs, the short-snapshot part (M6) of
  `2026-11-11-module-presets-and-changes.md`. That record is not deleted.

## Controller rulings, told to the owner, which the owner can reverse

- Lite has no CP-MODEL and publishes no forecast, as the approved plan said ("No CP-MODEL, so no
  forecast is published"). An earlier controller ruling kept CP-MODEL on the belief that the lite chart
  strip and credit metrics blocks need it; the whole-branch review disproved that, and this ruling
  reverses it. The launcher routes `model-chart-strip` and `financials-credit-metrics` to CP-1 with or
  without CP-MODEL, and a five-module lite run delivers the same nine blocks. The Forecast page states
  that no forecast was published for a lite run, as it does for past short-snapshot runs. The chart strip
  and credit metrics are still delivered, routed to CP-1. Adding CP-MODEL back would add a CP-1-only
  base-case forecast (as `relative_value` and `portfolio_decision` have) at about 5,700 more characters
  of CP-1 prompt (measured 5,717) plus a period table and a JSON block of output; no live model has yet
  written that block. It is one preset entry to reverse. The "CP-MODEL follows CP-1 when the composition
  holds Model-owned blocks" rule in `contracts.py` is a convention that no test or runtime check
  enforces; lite is a deliberate exception.
- The `model_testing/configs.py` case list has no lite case. It drives paid stage plans and needs an
  issuer case folder, which is not chosen. Deferred until the paid lite run.
- An earlier owner ruling (M1, M2) put CP-DR and CP-2E in every preset. Lite has neither, by the owner's
  2026-11-13 composition.

## Prompt size

Instruction characters per pathway (head plus method, CP-8 excluded), measured after merging `main`
(Task 1 report, fix round 1); lite's figure is re-measured after CP-MODEL was removed from it. Each ceiling is a test; lite's 420,000 was given.

| pathway | measured | ceiling |
| --- | --- | --- |
| lite_credit_assessment | 392,429 | 420,000 |
| credit_snapshot | 1,273,692 | 1,340,000 |
| covenant_refinancing | 1,092,608 | 1,155,000 |
| distressed_restructuring | 1,125,583 | 1,186,500 |
| earnings_update | 519,288 | 546,000 |
| portfolio_decision | 903,136 | 955,500 |
| relative_value | 1,018,568 | 1,071,000 |
| short_snapshot | 140,400 | 157,500 |

## Cost

Baseline, run `tdg-proof-snapshot-opus-002` (configuration opus-medium: every module at medium effort),
per module in USD: CP-0 0.7486, CP-1 1.1002, CP-1A 1.0643,
CP-2 0.7788, CP-2A 1.3824; the five total 5.07. That run was measured before the 2026-11-13 method change
that enlarged the prompts of CP-0, CP-1A and CP-2, so 5.07 is an estimate for a lite run today. The old
short snapshot run `tdg-proof-short-opus-001` cost USD 1.95. No lite run has been made, so lite's cost is
an estimate, not a measurement. The run-start page's default configuration runs some modules at high
effort, so a run started from the page can cost more than 5.07. CP-8 runs from the second lite run of an
issuer and adds its own cost, which is not in 5.07.

## Status

Built and tested offline. A synthetic lite run with no model reaches a verified delivery with all nine
blocks populated and no forecast published
(`test_the_lite_pathway_runs_end_to_end_to_a_verified_delivery_with_a_synthetic_provider`).
Not accepted: AGENTS.md requires a reader check of one real run against the September VMO2 reference for a
presentation change, and no real lite run has been read.
