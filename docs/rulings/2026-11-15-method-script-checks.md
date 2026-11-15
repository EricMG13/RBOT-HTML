# Method script checks for the next modules, and the cut tables they need restored

by: user
date: 2026-11-15

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line; paid execution still needs its own explicit action. No run has been made with this change.

Owner's words, 2026-11-15: "scope it now, wire the scripts in as checks" (the scope is
`docs/sweeps/2026-11-15-method-scripts/scope.md`; CP-2D and CP-3C were wired first). Shown those two
and the open points, the owner answered: CP-3C's new `### Funding gap` table, "confirmed"; leaving
the method archive out of the quality gate's changed-code scope, "ok"; and, on the modules whose
script inputs live only in registers the 2026-11-13 scope rule cut
(`2026-11-13-appendix-and-routing-scope.md`): "restore the cut tables".

Scope: offline only. No provider was called. Evidence is synthetic handoffs written by hand in the
transport's layout, and, where named, the retained TransDigm excerpts of 2026-11-13.

## What a check is

As for CP-2D and CP-3C (`deploy_workflow.method_scripts`): after a module answers, Python runs the
method's own script, from its registered bytes, on the inputs the handoff's registers state, and
compares the script's result with the figure the handoff states. Currency and scale are read from
the register and must agree; a figure agrees within one unit of its last displayed place (or the
script's own rounding, if coarser). Only a disagreement is an acceptance issue, naming the register,
row, both values and the formula. A missing input, an unread cell, a unit mismatch, an absent or
malformed register, or the script refusing its inputs is "not checked", with its reason, recorded
beside the attempt; never zero, never a pass, never a refusal. Each checked module's instructions
gain one note naming the figures Python recomputes and the rows it needs. Each module's mapping is
its own module beside the harness (`deploy_workflow.method_scripts_<module>`).

## Restoring a cut table

A restored register is removed from that module's section of the project-written
`docs/reuse/selected-methods/CPOS_REGISTER_SCOPE.md`, so the module writes it and the presence check
requires it (as CP-6A's were, `2026-11-15-full-assessment-cp3c-cp6a.md`). Each is restored because
the check reads it, and only then; every other register the 2026-11-13 rule cut stays cut. The
file's manifest sha256 and note, the METHODOLOGY-REVIEW.md appendix row, the module's method pin
(past runs are marked "Earlier methods" for it) and CP-5's upstream note follow.

## Per module

### CP-2E, `rate_fx_sensitivity.py`

- Restored: T2F.4 Unhedged Exposure Table (its rows Total debt, Gross floating-rate debt, Hedged
  floating-rate debt are the script's inputs; Unhedged floating-rate debt and Unhedged debt
  percentage are two of its figures) and T2F.5 Rate Sensitivity Table (the +100 bps cash-interest
  impact is the third). Both were written by both retained Sol runs before the cut.
- Stays cut: T2F.2 Debt & Rate Exposure Register (the instrument list behind T2F.4's gross figure;
  the script does not read it), T2F.8 and T2F.9.
- Checked: Unhedged floating-rate debt = Gross - Hedged; Unhedged debt percentage = Unhedged /
  Total debt (a `%` figure, or a decimal as the method's rule 8 stores it); +100 bps cash-interest
  impact = Unhedged x 1.00%. T2F.4 has no currency or scale column: each amount states its own
  (`USD 1,250m`) or the amount column's header does (`Amount (USD m)`).
- Not checked by design: FX and commodity sensitivities (net exposure and adverse move are free text
  in T2F.6 and T2F.7, not columns) and so the combined impact. Hedged above gross floating-rate
  debt: the script refuses it ("perimeters differ or a hedge is double-counted") rather than report
  zero unhedged exposure; under the harness rule a refusal is "not checked", so such a handoff is
  recorded, not sent back. Whether that should be an acceptance issue is for the owner.

### CP-3, `recovery_waterfall.py`

- Restored: none. Checked against the method, the three registers the scope document named do not
  hold the script's inputs or figures: T3B.2's Amount is carrying value (CP-3A runbook: "every
  instrument Amount uses the canonical carrying-value debt basis"; the retained medium run titled it
  "Carrying-value capital structure dashboard"), not the claim a waterfall allocates; T3B.4's
  Structural Rank is an ordinal; T3B.6's Recovery Sensitivity is a label (Low, Moderate, High,
  Binary, Insufficient Information), and step 6 says "Do not infer recovery values unless supported
  by provided evidence". No CP-3 register holds an enterprise value. So restoring them would cost
  output and check nothing. They stay cut, with T3B.3, T3B.5, T3B.7, T3B.8, T3B.10, T3B.11 and every
  T3C register (CP-3B's portfolio fit is handled elsewhere).
- What the check needs: one new table, `### Recovery waterfall` (rows `Enterprise value` by case,
  `Cost: <label>`, `Claim: <instrument>` in waterfall order with its claim and its recovery % per
  case, `Fulcrum`, `Residual to equity`; columns `Line | Amount | Low | Base | High | Currency |
  Scale`). That is a new model output the owner has not approved for CP-3, so CP-3 is NOT asked for
  it: no note is sent and its instructions are unchanged. The check
  (`deploy_workflow.method_scripts_cp3`) reads the table when a handoff has one, and otherwise
  records every figure as not checked.
- Checked when the table is present: each claim's recovery in each case, the fulcrum in each case,
  the residual to equity in each case (value the claims do not absorb must not be left
  unallocated). A claim listed twice (a guarantee at two entities) is refused by the script as
  double recovery: not checked. The script allocates one pool; it does not split value by entity.
- Decision for the owner: ask CP-3 for the table (its instructions would gain a note like
  CP-3C's, which is 1,088 characters, in `credit_snapshot`, `relative_value` and
  `portfolio_decision`), or leave CP-3 unchecked.

### CP-2G, `credit_metrics.py`

- Restored: none needed. T2H.4, T2H.5 and T2H.6 were never cut (only T2H.1, T2H.2 and T2H.9 are).
- Inputs: T2H.4 `EBITDA`, `FCF`; T2H.5 `opening debt/cash`, `issuance`, `repayment`, `interest`,
  `closing debt/cash`; matched to T2H.6 by period and case. T2H.4 and T2H.5 have no currency or
  scale column: each money column's header states it (`EBITDA (USD m)`) or each cell does.
- Rule for combined cells (decided here): a column whose name joins two figures with `/` holds two
  figures separated by `/`, in the name's order (`4,500 / 300`, `4.5x / 4.2x`). A gap for the whole
  cell is a gap for both; a gap on one side is a gap for that side only; a cell that is not two
  parts states neither figure (not checked, never guessed).
- Checked per T2H.6 row: gross leverage (closing debt / EBITDA) and net leverage ((closing debt -
  closing cash) / EBITDA), both against a positive EBITDA and only for annual periods; coverage
  (EBITDA / |interest|), a disagreement only when the row's definition names EBITDA over interest,
  otherwise not checked, because the method allows fixed-charge coverage, which no column can
  recompute; FCF/debt (annual periods). A multiple stated against non-positive EBITDA disagrees
  with the script's Not Calculable. Per T2H.5 row: opening debt and opening cash against the same
  case's prior closing (consecutive annual years only), a disagreement otherwise; closing debt =
  opening + issuance - repayment, agreed when it rolls, otherwise not checked with the residual
  (the method allows a residual it logs, and T2H.5 has no column for PIK, FX or accretion).
- Not checked by design: the cash roll-forward (dividends and other cash uses are not columns),
  accessible liquidity and liquidity runway (not script figures).
- The owner module `owners/cp2g.py` (the Deploy VII journal path, not wired in) computes the same
  ratios in Decimal from its own forecast (closing debt and cash, EBITDA, interest as a positive
  figure) and rolls cash with dividends, which T2H.5 does not carry.
- Retained evidence: `tests/fixtures/tdg_sol_high_2026_11_13/CP-2G-forecast-block.md` (TransDigm,
  run of 2026-11-13) is the forecast-inputs block only; it has no T2H register, so the check
  records "not checked: the handoff has no T2H.4 register". The full CP-2G handoffs, which wrote
  T2H.4 to T2H.6, are not in this repository.

### CP-4, `covenant_headroom.py`

- Restored: none needed. CP-4 has no register-scope section; T4C.4 is required as the method
  lists it.
- Inputs: T4C.4 `Test`, `Test Type`, `Threshold`, `Current Basis`, `Headroom`, `Status`
  (REF_CP-4A_04). The script is the CP-2H copy registered in the archive (the same bytes CP-4's
  SKILL names).
- Checked per test: Headroom (max-ratio: Threshold - Current Basis; min-ratio: Current Basis -
  Threshold) and Status (Compliant, At threshold, Breached), by the script's own `headroom`.
- Test Type: passed to the script's own `normalise_test_type` as written, or its first word
  (`max-ratio (leverage ceiling)`); a row whose type is blank or that the script does not read is
  not checked, never guessed. Two of the script's aliases are refused here: a bare `maintenance`
  or `incurrence` says when a test applies, not whether it is a ceiling or a floor (a maintenance
  interest-cover test is a floor; the script would read it as max-ratio).
- Units: Threshold, Current Basis and Headroom must each be one figure in one unit, a ratio
  (`5.00x` or a bare figure), a percentage or an amount with its currency and scale; otherwise not
  checked. A comparator before the threshold (`≤ 5.00x`) is read. Status is compared only when it
  states one of the script's three words.
- Not checked by design: maximum additional debt and T4C.5 basket capacity (their inputs are free
  text in `Formula` and `Current Input`), severity (the analyst's).
- Retained evidence: none. CP-4 was blocked at its source gate in both Sol runs (no legal
  documents); synthetic proof only.

## Status

Built and tested offline, module by module. Not accepted: no model has written a restored register
under these instructions; that needs the owner's paid run.
