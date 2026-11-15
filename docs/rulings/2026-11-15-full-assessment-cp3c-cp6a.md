# CP-3C and CP-6A are part of the full credit assessment

by: user
date: 2026-11-15

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line; paid execution still needs its own explicit action. No run has been made with this change.

Owner's words, 2026-11-15, in a sibling session: "6A should be included", then, asked to clarify:
"module cp-6A within cp-6 should be fully functional and cp-3c. they are part of full credit
assessment". Asked by the coordinating session what to do with that, the owner chose: add both now,
offline; proof stays offline (tests and instruction diffs); a paid run to confirm real model output
is a separate step the owner starts.

Scope: offline only. No provider was called. The full credit assessment is the `credit_snapshot`
pathway (`2026-11-13-full-and-lite-credit-assessments.md`).

## What was true before

- CP-3C (Refinancing & LME) ran in `relative_value` and `covenant_refinancing` only. Its registry
  entry requires CP-0, CP-1 and CP-2D; CP-2D requires CP-0, CP-1 and CP-2. `credit_snapshot` had
  neither. In `relative_value` CP-3C owns no report block either: its handoff reaches the reader on
  its module page and through Overview's selection.
- CP-6 was already sent the CP-6A method in full: its SKILL's "Absorbed phase — CP-6A, binding on
  every CP-6 run" and `REF_CP-6A_STEPS.md`. But the register-scope section CP-6 is sent last
  (`docs/reuse/selected-methods/CPOS_REGISTER_SCOPE.md § CP-6`, ruling
  `2026-11-13-appendix-and-routing-scope.md`) told it not to write CP-6A's four registers, T6E.4
  Compliance cross-examination, T6E.6 CIO scoring, T6E.7 Decision matrix and T6E.11 portfolio debate
  gaps ledger, because no later module, check or library page read them in the two retained Sol runs.
  Nothing asked for or checked CP-6A's Final Sizing Posture, Exact Portfolio Constraint or CIO memo.
- Retained evidence (TransDigm, as of 30 September 2024, the two full assessments of 2026-11-13 on
  GPT Sol medium and high, made before that cut): the appendix inventory
  (`docs/sweeps/2026-11-13-optimisation-review/appendix-inventory.md`) lists, in both CP-6 handoffs,
  the RV Trader pitch, T6E.4, the RV Trader defense, T6E.6, T6E.7, the posture, exact constraint and
  CIO memo, and T6E.11, every one classed CUT (no consumer). So the model wrote CP-6A when the
  method alone asked, and its absence afterwards is the instructions' doing. Those handoffs are not in
  this repository; `tests/fixtures/tdg_sol_high_2026_11_13` holds only CP-1, CP-2A and CP-2G
  excerpts of the high run, no CP-6.

## Decisions

- `credit_snapshot` preset (`src/deploy_vii/contracts.py`): CP-0, CP-1, CP-MODEL, CP-1A, CP-DR,
  CP-2, CP-2A, CP-2D, CP-2E, CP-2G, CP-4, CP-3C, CP-3, CP-5, CP-6. CP-2D is listed because CP-3C
  requires it, as `relative_value` and `covenant_refinancing` list it. Run order: CP-0, CP-1, CP-1A,
  CP-DR, CP-4, CP-2, CP-2A, CP-2E, CP-2D, CP-2G, CP-3C, CP-3, CP-5, CP-6 (CP-8 last when an earlier
  run is listed). CP-2D and CP-3C now reach CP-2G, CP-3, CP-5 and CP-6 as optional producers, as
  the registry already defines; CP-5 stays CP-6's upstream gate, and CP-6 is not CP-5's input.
- The full assessment's report blocks are unchanged: no block of it is owned by CP-2D or CP-3C. Their
  handoffs reach the reader on their module pages and in Overview, as CP-3C's does in
  `relative_value`. Their instructions are byte-identical to `relative_value`'s apart from the
  pathway name.
- CP-6A: CP-6's register-scope section no longer names T6E.4, T6E.6, T6E.7 and T6E.11, so the
  presence check requires them as it requires T6A.4 and T6A.7. T6A.6 and T6A.11 (the issuer
  debate's own scoring table and gaps ledger) stay cut: the instruction was about CP-6A. The file is
  project-written; its manifest sha256 and the METHODOLOGY-REVIEW.md appendix row are updated.
- CP-6's instructions carry a block (`CP6A_BLOCK`): the portfolio debate's Final Sizing Posture,
  Exact Portfolio Constraint and CIO memo go in one `### Portfolio posture` section of
  `## Findings`, after `### Limitations`, whose first sentence is the method's own formulation
  (`Final Sizing Posture: <posture>.`, one of the method's six postures); the posture and binding
  constraint are one of the Key findings. At acceptance `posture_issues` refuses a CP-6 handoff that
  is not blocked and lacks the section or that first sentence. The reader sentence checks (no module
  code, page locator, bracket, hash or pipeline wording outside Basis lines) apply to the section as
  to every section the Modules page shows.
- The CP-6 change applies wherever CP-6 runs: `credit_snapshot` and `portfolio_decision`. The scope
  section is per module, and the portfolio debate is the core of the portfolio decision; nothing
  argued for a difference.
- Library: no code change. CP-6's module page draws the Portfolio posture section and T6E.4, T6E.6
  and T6E.7 as findings, with no ids or file names; T6E.11 (a ledger) is drawn on Evidence. CP-3C's
  page and Overview draw its passages.
- Run start page: its module tables (`PATHWAYS`, `RUN_ORDER`, CP-6's `EDGES`) follow the preset. Its
  pathway description lists no modules and is unchanged. It shows no USD forecast, only the cap.
- Prompt-size ceiling for `credit_snapshot` (`INSTRUCTION_BUDGET`): the owner's 1,340,000 plus the
  measured addition, 143,647 characters (1,316,558 before, 1,460,205 after on the test input), so
  1,483,647. `portfolio_decision` (939,644) stays inside its 955,500.

## Cost

No run has measured CP-2D or CP-3C in this transport. Estimate from the measured TDG full
assessments of 2026-11-13 (GPT Sol through GitHub Copilot, 13 modules with CP-8, made before the
register cut): USD 8.62 at medium and 11.37 at high. Two more modules at the median measured
analytical module (USD 0.44 medium, 0.66 high), CP-5 reading two more handoffs (about a fifth more
of its 2.26 and 2.80) and small additions to CP-6, CP-8 and CP-6A's tables give about USD 1.5 more
at medium and 2.1 at high, so roughly 10 and 13.5 a run: inside the USD 20 cap on GPT Sol. On Claude
Opus the only full run measured cost USD 19.45 (2026-11-12, before the cut); the same addition at
Opus prices could take a full run to or past USD 20, and the cap would then stop it before CP-6 or
CP-8. That is for the owner to weigh.

## Left open

- A paid run: no model has produced a CP-3C or CP-6A handoff for this pathway under these
  instructions. The owner starts it.
- Mandate and exposure inputs: the full assessment does not ask for the portfolio workbook (only
  `portfolio_decision` does), and the method's `REF_CP-6A_Portfolio_Debate_Inputs.xlsx` was never
  archived (a deployment placeholder). By the method's own rules CP-6A then cannot claim sizing
  within limits and its exact constraint is not established; the posture will usually be Requires
  More Work. Whether the full assessment should collect the workbook is the owner's decision.
- CP-3B input: CP-6A's gate names CP-3B (portfolio fit and sizing, inside CP-3's method) for a full
  run; CP-3's scope section cuts T3C.1 to T3C.3 and T3C.5 to T3C.9. Restoring them is outside this
  instruction.
- The Opus cost above.
- The Deploy VII journal path (`owner_workflow`, `cp6_committee`, which binds no T6E table) is not
  changed: another session is removing that code, and the CP-OS launcher is the active path.

## Status

Built and tested offline. Tests pin the preset and run order, refuse a CP-6 handoff without a CP-6A
register or the posture section or formulation, and check the library pages against the synthetic
handoffs they draw. Not accepted: acceptance needs the paid run.
