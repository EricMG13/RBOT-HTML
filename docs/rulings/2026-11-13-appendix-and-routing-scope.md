# Appendix and routing scope: modules stop writing routing text and no-consumer registers

by: user
date: 2026-11-13

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line; paid execution still needs its own explicit action. No run has been made with this change.

Owner's words, 2026-11-13: "cut the part of the appendix the modules write"; "inter module
communication should [be] handled by orchestrator, so does not need to be held in the
instructions"; then, asked, "Yes, cut routing text" and "Cut the no-consumer list for the 10
modules measured".

## Decisions

- Every module's instructions carry `ROUTING_RULES`, directly after `TRANSPORT_RULES`
  (`src/deploy_workflow/owners/cpos_launch.py`). It overrides every method instruction to return or
  recommend a next command, keep a Master Index, managed workspace, export record or run command
  sheet, map dependencies, file a research request or brief, or write a register addressed to
  receiving modules (cross-module handoff, consumer actions, analytical consumption, event use,
  downstream readiness) or the tables `cp2g.cp_model_forecast_drivers` and
  `cp2b.cp_model_catalysts`. `## Next module` stays a required heading; its body is the one line
  `The orchestrator selects the next module.`. A restriction on how results may be used is a
  limitation, stated in `### Limitations` or `## Gaps`.
- CP-0's block no longer demands T7 and T8 and says not to write them. Because CP-0's scope section
  also cuts P5, T3 and T5, the block's write list is now P3 and T1, T2, T4 and T6; a missing
  document is stated under `## Gaps`.
- Ten modules (CP-0, CP-1A, CP-DR, CP-2, CP-2A, CP-2E, CP-2G, CP-3, CP-5, CP-6) are told, in the last
  section of their method block, which registers not to write:
  `docs/reuse/selected-methods/CPOS_REGISTER_SCOPE.md`, one `## <module>` section each, every
  register named by its method id and the method's own title. The scope file is the list; it is
  not repeated here. Modules without run data (CP-1, CP-4, CP-8, CP-1B, CP-1C, CP-1D, CP-2D, CP-2H,
  CP-3C, CP-3D, CP-4C, CP-5A, CP-6A, CP-L10) have no section. CP-5A is not a module CP-OS launches
  (its steps are inside CP-5's method).
- The cut rule: a register is listed only if it has a method id and is classified CUT in every row of
  `docs/sweeps/2026-11-13-optimisation-review/appendix-inventory.md` for that id, in both retained
  Sol runs (medium and high), and no row of either run classifies it otherwise. A consumer in either
  run is a consumer, so the lists are the intersection: the sizes below measured for one run are
  upper bounds for this list. Headings the model chose without an id are not listed. CP-1A's
  `ownership_register` is left out: `handoff_delivery.py` line 488 reads a section `Ownership and
  control` into a table of that name. TDR.2 is kept (the peer pack block requires its gap row);
  TDR.4 to TDR.6 are never cut. T2DS.2 and T2B.1 stay (`cp1_references` has later consumers).
- The methods' own validators (`required_register_ids`, `appendix_contract`, the lossless profile,
  `completeness_check.py`) are never run here, but `TRANSPORT_RULES` has a module do their checks
  itself. So `ROUTING_RULES` and each scope section end with one sentence: a register excluded there
  is not required by those checks in this transport, and the module neither restores it nor blocks
  for want of it.
- CP-5 is sent, in its head, a generated note listing for each upstream module in the run that has
  a scope section the registers it was told not to write, and that their absence is not a finding;
  it carries the routing rule too. No other module carries it. CP-6's and CP-8's methods were read
  for a step that audits upstream completeness: neither has one at register level (CP-6's Step 1
  and its `Upstream re-anchor` check that each upstream module is available and that the values
  it consumes are present; CP-8 compares the comparison pack's measures and limitations and says a
  difference of format or headings is not a finding). Nothing was added for them.

## What is superseded

For the registers and routing text named above only, this supersedes decisions 8 ("tables and
registers, unchanged and exact") and H1 and H4 of `2026-11-11-reader-and-issuer-report.md`, which
stay as written for every other register. The Evidence page is unchanged. The Modules page loses
the sections that are no longer written; the figure check still requires every figure in a
reader passage to appear in a table the module writes or in `## Calculations`.

## Measured sizes

From the inventory (class 1, routing and presentation transport): 42.8K and 43.4K handoff
characters a run. From the same inventory, registers with no consumer: 43,694 and 57,221 output
tokens a run, about USD 1.10 and 1.33 a run at list prices. These are the controller's figures,
attributed to the review, not trialled.

For the list this change cuts (the intersection of both runs, with no routing registers), the
characters in the inventory are 166,882 (medium run) and 189,139 (high run), ownership_register
excluded. The list is the intersection of both runs, so by construction the per-run no-consumer
token figures above are upper bounds for it; characters and tokens are not converted here.

## Not accepted

Built, not accepted. No paid run has used it. Acceptance needs one paid before and after run of the
same issuer, and the reader check of one real run against the September VMO2 reference
(`AGENTS.md`), recorded in `VERIFICATION.md` with its scope. The retained-handoff replay is offline
and proves only that CP-OS's checker and delivery take such handoffs.
