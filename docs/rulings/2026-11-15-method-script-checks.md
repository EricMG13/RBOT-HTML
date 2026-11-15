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

### CP-1, `credit_metrics.py`

- Restored: none needed. CP-1 has no register-scope section.
- How the work divides with `owners/cpos_cp1_check.py`: that check already recomputes the six fixed
  T4.9 rows (`Total debt / EBITDA`, `Net debt / EBITDA`, `EBITDA / cash interest` and their
  adjusted twins), binding each operand to the figure it must be (debt from `Net debt data`,
  EBITDA and cash interest from the statements) and the two-place print. The script check leaves
  those six rows to it (a test pins the two lists equal) and takes the rest: T4.9 rows with a free
  `Metric Name` whose `Formula` is a quotient (`Calculated Value` against the script's `ratio` of
  the row's own `Numerator Value` and `Denominator Value`, as a ratio or in percent, or its
  `growth`, n / d - 1, for a change; on a disagreement the form nearest the stated figure is
  reported), and T4.8 rows whose `Derived Period Type` is LTM (`Derived Value` against the script's
  `derive_periods`: Full-Year Component + Current Stub - Prior-Year Stub).
- The operand-identity trap: for a free-name row only the arithmetic is bound, not which debt or
  EBITDA the operands are. On the retained TransDigm figures (FY2024, USD millions), a row of
  principal 25,068 over EBITDA 3,813 stating 6.57 agrees with its own division, although the
  method's debt is carrying value (24,880, giving 6.53); the same row stating 6.57 over 24,880
  disagrees. The fixed rows, where the operand is bound, are `cpos_cp1_check`'s.
- Units: T4.9's `Currency` and `Unit` must be stated (they describe both operands). T4.8 has no
  currency or scale column: an LTM row is compared only when its cells or column headers state
  one, and the same one; otherwise not checked. Not checked by design: other derived types (Q2, Q3,
  Q4, YTD; T4.8's three component columns do not say which periods they hold), and free-name rows
  that are sums or differences.
- Note: CP-1 runs in every pathway, and `earnings_update`'s instructions measured 545,907 of its
  546,000-character ceiling; the note (500 characters) takes them to 546,407. The owner
  approved raising that ceiling by the note's length (see the owner's answers). The note sent:
  "Python checks two kinds of your figures after you answer, with the method's own
  `credit_metrics.py` (you cannot run it): each T4.8 LTM Derived Value (Full-Year Component +
  Current Stub - Prior-Year Stub) and each free-name T4.9 Calculated Value (Numerator Value /
  Denominator Value, or the change n / d - 1). State T4.8's currency and scale in each cell or
  column header (`USD 1,250m`). A figure that disagrees is sent back for repair; one whose input
  is missing is not checked, never read as zero."
- Retained evidence: `tests/fixtures/tdg_sol_high_2026_11_13/CP-1-tables.md` (TransDigm, run of
  2026-11-13) is the older CP-1 layout, written before T4.8 and T4.9: the check records both as not
  checked (no register). Its key-metrics row `Total debt / unadjusted EBITDA` 6.57 is principal
  25,068 / EBITDA 3,813 (carrying value 24,880 gives 6.53): a basis difference from the method's
  carrying-value rule, in a layout that predates it, not an arithmetic error.

## CP-3's portfolio-fit registers, restored on the owner's instruction (not for a script check)

Owner, 2026-11-15, relayed by the coordinating session: "restore the CP-3 portfolio-fit tables".
This answers the CP-3B item left open by `2026-11-15-full-assessment-portfolio-workbook.md` (not
edited here).

- Restored: T3C.1 Portfolio Input Gate + Module Status, T3C.2 Portfolio Fit Register, T3C.3
  Position Sizing Posture Table, T3C.5 Concentration and Correlation Register, T3C.6 Liquidity and
  Implementation Assessment, T3C.7 Downside Budget and Recovery Sensitivity, T3C.8 Monitoring
  Triggers (portfolio), T3C.9 Gaps Ledger (portfolio): every T3C id the 2026-11-13 rule cut (T3C.4
  was never cut). Both retained Sol runs wrote all eight before the cut; the inventory classes each
  CUT (no consumer then), so rule R1 alone would still cut them.
- Unconditional, per module, in every pathway that runs CP-3 (`credit_snapshot`, `relative_value`,
  `portfolio_decision`), whether or not a workbook is supplied. The method agrees: CP-3B's gate
  (`REF_CP-3B_01`) "Always executes", and with portfolio inputs missing it gives "generic
  portfolio-fit logic, retain[s] the gaps and avoid[s] a numeric sizing recommendation"; its
  discipline forbids inventing mandate limits or holdings. So without a workbook the registers hold
  that generic logic and the gaps, not sizing.
- What stays cut for CP-3: T3.1, T3.4, T3.5, T3.7, T3.9, T3.10 and T3B.2 to T3B.8, T3B.10, T3B.11
  (none restored for a script check; see CP-3 above).
- No script checks them; this is a restore only. The presence check now requires them (a CP-3
  handoff without one is sent back once, naming it, unless CP-3 is blocked at its gate).
- Instruction size: CP-3's scope section and CP-5's upstream note each shorten by 322 characters in
  the three pathways (`credit_snapshot` 1,464,698 to 1,464,054 of 1,483,647; `relative_value`
  1,059,626 to 1,058,982 of 1,071,000; `portfolio_decision` 940,825 to 940,181 of 955,500). Output
  grows instead: the two retained Sol runs wrote these eight registers in 9,367 (medium) and 12,314
  (high) characters, about 2,500 to 3,300 more output tokens for CP-3, and CP-5 and CP-6 (and CP-8
  when listed) read that much more of CP-3's handoff. Not measured under these instructions.

## Review fixes (2026-11-15, after the coordinating session's adversarial review)

An independent review ran adversarial handoffs through the checks and found correct handoffs
refused; each case was reproduced, fixed and tested with hand-worked expectations.

- Rounding of the displayed inputs, for every check (CP-2D and CP-3C included): a stated figure
  agrees within one unit of its last displayed place (or the script's own rounding step), plus the
  bound the inputs' half-last-place rounding puts on the recomputed figure: for a sum or
  difference, the sum of the inputs' half-units; for a quotient n / d, the first-order bound
  (h_n + |n / d| h_d) / |d|; for a share or percentage, the same scaled. A figure computed from
  unrounded inputs is no longer refused for the rounding of the inputs it displays; a figure wrong
  by more than the bound still disagrees (tested per module). Two CP-2D expectations changed with
  the rule: the ending's tolerance on nine whole-number inputs is 5.5, not 1; Months to Empty's on
  the test bridge is 2.08, so 48.2 against 48 now agrees and 50.2 disagrees.
- One vocabulary of null words for every check (`Not Calculable`, `Not meaningful`, `n.m.`, `n/m`,
  `nm`, `n.c.`), alone or followed by its explanation (`Not meaningful (negative EBITDA)`).
- A money cell wholly in brackets is a negative amount (`(USD 30m)` as `USD (30)m`).
- CP-2E: the +100 bps impact's sign is fixed by neither the method nor the note, so its magnitude is
  compared and a stated outflow's sign is kept in the record. An amount row with no readable unit
  now stops only the checks that use it.
- CP-1: a denominator at or below zero: a null word agrees; a figure over zero disagrees (the script
  gives none); a figure over a negative denominator disagrees for a leverage, coverage or
  debt-based quotient (the script's positive-denominator convention) and is not checked for any
  other (a growth or margin may have a negative base). The row's own words choose the form: growth
  (`- 1`, growth, change) or ratio, percent only when the formula says `x 100` or `%` or the figure
  carries `%`; a figure is no longer accepted by matching another form.
- CP-2G: a leverage or FCF/debt mismatch is not checked when the row's `definition IDs` cell names
  another basis (covenant or agency EBITDA, lease-adjusted, IFRS 16, pro forma, run-rate,
  principal, face value, average debt), as coverage already was. Known limit: the method's
  definition ids (REF_CP-2G_B: "separate definition IDs for reported EBITDA, CP-1 normalized EBITDA,
  covenant EBITDA and agency-adjusted metrics") are opaque labels whose meaning is in the handoff's
  definition-lock prose, so an id alone (`D4`) is not recognised and such a row is still compared;
  the forward model "normally uses CP-1 definitions", the EBITDA T2H.4 states. An unread T2H.6
  column no longer discards T2H.5's roll-forward outcomes.
- CP-4: Status is not decided when the recomputed headroom is within its inputs' rounding of zero
  (a stated Breached from an unrounded input at the threshold is not sent back).
- CP-3 (not asked): a fulcrum named with a note (`Senior Notes (partial)`) is read as the claim.

## Decisions for the owner, and the owner's answers

Asked through the coordinating session; the owner's words, 2026-11-15, to the numbered list (1 CP-3
has no enterprise value to read; 2 raise the `earnings_update` ceiling for CP-1's note; 3 send back
hedged above gross; 4 the cost of the restores): "1. cp-dr or cp-1c is supposed to do by default
using peer multiples 2. approved 3. approved 4. its is fine".

1. CP-3: investigated and asked back (below, "CP-3's enterprise value"); then built.
2. CP-1's note is sent (`CP1_NOTE`, 500 characters, in every pathway). The `earnings_update`
   ceiling (`INSTRUCTION_BUDGET` in `tests/test_cpos_launch.py`) is the owner's 546,000 plus that
   measured 500: 546,500 (545,907 before, 546,407 after on the test input). No other ceiling moved.
3. Hedged floating-rate debt above gross is sent back. It is recorded with its own status,
   `contradicted`: two stated rows contradict each other and the script refuses them ("perimeters
   differ or a hedge is double-counted"), so nothing is recomputed, which a `disagreed` record
   would misstate. The issue names both rows and the script's reason; the three figures are not
   checked. Only that refusal is sent back: every other refusal of a script (a negative amount, a
   test type it does not read, a missing input) stays "not checked".
4. No action.

## CP-3's enterprise value (owner, 2026-11-15: "1. yes 2. yes 3. yes")

What the method says (archive; Deploy-V `c4d2e35` and cp-os `b57a344`, read only, the same
revisions): CP-1C computes an implied EV range in T4.10 (REF_CP-1C_06C: "Low = minimum peer multiple
x borrower metric; Median = median ...; High = maximum ...") and twice forbids its use as a recovery
input (06C: "indicative context ONLY, NOT recovery estimate (recovery belongs to CP-4 / CP-4A)";
Valuation Discipline 8). CP-DR's peer pack carries no multiple (TDR.6: revenue, ebitda, debt,
interest, ffo). CP-4B's runbook: "CP-3A owns the dollar waterfall"; no CP-3 register states an EV.
No text names a default multiple. In this transport CP-3 receives CP-1C only in `relative_value`.
The real cp-os TransDigm run of 2026-11-04 had no EV anywhere: "`recovery_waterfall.py` was not run
because no enterprise value is sourced".

Asked (1) whether CP-3 may take T4.10's Low, Median and High as its EV cases where it receives
CP-1C, overriding CP-1C's rule for CP-3's use only; (2) whether, without CP-1C or a usable multiple,
CP-3 states its own cases with their basis; (3) whether wiring CP-1C upstream of CP-3 everywhere
waits for the pathway restructure, the owner answered "1. yes 2. yes 3. yes". The coordinating
session reads 3 as the pathway part waiting; no pathway's modules or order changed.

- Override, for CP-3's use only: CP-1C's 06C and Valuation Discipline 8 do not stop CP-3 from
  taking T4.10's implied EV range as its enterprise-value cases. CP-1C's own text and handoff are
  unchanged (an archived method file). CP-3's note says the implied EV is indicative, not a
  valuation, and that the recoveries carry that limitation, for its limitations paragraph.
- CP-3 is asked for `### Recovery waterfall` (`CP3_NOTE`, 1,274 characters): `Enterprise value`,
  `EV multiple`, `EV metric` and `EV basis` rows per case (Low, Base, High), then costs, claims in
  priority order with their recovery %, `Fulcrum`, `Residual to equity`. Where it was sent CP-1C's
  T4.10, the cases are T4.10's Low, Median and High, the basis naming `CP-1C T4.10` and the method;
  otherwise its own cases with their basis from the evidence it was given.
- No supportable EV: each `Enterprise value` cell `Not supplied: <reason>`. Recorded as not checked
  with the reason, never sent back: a recovery analysis with no defensible value must be able to
  say so, as the 2026-11-04 run did, without the check pressing for a number.
- Sent back (status `missing`): the table absent with no statement (unless CP-3 stopped at its
  gate, `module_status: Blocked`), and an EV figure with no `EV basis`.
- Checked per case: EV = multiple x metric by CP-1C's own `peer_statistics.implied_ev` (none on a
  metric at or below zero), within the stated place plus the product's rounding bound; where the
  basis begins `CP-1C T4.10`, the multiple against the T4.10 CP-3 was actually sent (the checker
  passes each module the upstream handoffs it was sent; see the review fixes below); CP-1C not
  sent is not checked. Then the waterfall as before.
- Instruction size: CP-3 only, +1,274 characters (then 1,334 after the review fixes) in each of
  `credit_snapshot`, `relative_value` and `portfolio_decision`, each within its ceiling. No
  ceiling moved.
- Review fixes (second adversarial review, about 150 handoffs; each case reproduced first):
  - The copy is claimed by the basis's leading token only: an `EV basis` beginning `CP-1C T4.10`
    (optionally its method, `EV/EBITDA`). A basis that mentions T4.10 to set it aside, or as a
    comparison, is CP-3's own case. The copy compares multiples, not values: CP-3's `EV multiple`
    against T4.10's implied EV for the case over its borrower metric (needs no unit; CP-3 may
    apply T4.10's multiples to its own metric). A T4.10 that states no figure for the case leaves
    the copy not checked; CP-3's own arithmetic stands or falls by itself. T4.10's median may be
    headed `Base`.
  - Claims that rank equally: `recovery_waterfall.py` allocates strictly by row, so two pari passu
    claims cannot be stated truthfully as two rows. CP-3's note asks for them in one `Claim:` row
    naming them all; the script's class recovery is then each member's. Neither CP-3A's text nor
    the script defines a tie.
  - A fulcrum cell is read as the claim it names: a leading `Claim:` and a trailing note (after a
    dash or in brackets) are not the name; `Not applicable`, `Equity`, `none`, `n/a` say no debt
    claim is the fulcrum; a cell naming no claim is not checked, never a disagreement.
  - The table is found under any heading (any level) or bold line whose words include "recovery
    waterfall", numbering and a trailing note aside, else as the one table with its columns;
    `missing` means it is not in the handoff.
  - `module_status: Blocked` is one rule (`method_scripts.blocked`) for this check and the
    launcher's presence check (`_blocked_at_gate` now calls it): a note after the word, a `#`
    comment and a byte-order mark are read; `Not blocked` is not blocked.
  - Lesser: a row the check does not read (a total) is named in the record and the rest checked,
    unless it states recoveries (it may be a claim not marked `Claim:`); a money row with `—` for
    currency and scale takes the table's unit; `8.5×` and `8.5x (peer median)` read as 8.5; one
    gap vocabulary for every check (`Not supplied`, `Not provided`, `Not available`, `Not
    disclosed`, `[Insufficient Information]`).
  - CP-3's note: 1,334 characters (from 1,274); `credit_snapshot` 1,465,888, `relative_value`
    1,060,816, `portfolio_decision` 942,015, each within its ceiling.
- Known limits: T4.10's own layout (the SKILL's combined `Implied EV/Low/Median/High` or the step
  file's separate columns) is read either way; its borrower metric must be one figure in its
  cell, or the copy is not checked. `credit_snapshot` and `portfolio_decision` have no CP-1C until the restructure,
  so CP-3 states its own cases or none there.

## `completeness_check.py`, every module (2026-11-15, row 4 of the scope)

Harness `deploy_workflow.method_scripts_completeness`; registered with `register_shared`, so it runs
on every module's handoff after the module's own script check. Its outcomes go into the same
`<attempt>.method-checks.json` record; its issues reach the launcher through `shared_issues`.

- What the script checks (cp-os b57a344, archived `scripts/completeness_check.py`, sha256
  `a9841a74`): from the `## Output profile` of the module's SKILL.md, each required register's
  declared columns, its `minimum_body_rows`, its critical columns against the blocklist
  (`critical_cell_values_casefold`: empty, `n/a`, `tbd`, `[insufficient information]`, ...), and the
  CP-MODEL interface tables. Its own `load_contract` reads the contract from the archived SKILL.md
  the module is sent (sha256-pinned); its `is_template_column` reads `Period 1…N`.
- Overlap with the launcher: `register_issues` already sends back an in-scope register that is
  absent (ten modules). This check never repeats that: a register it cannot find as a table under
  its heading is "not checked", whatever the reason.
- Not contradicting the cuts: for the ten modules with a scope section only the registers
  `cpos_launch.required_registers` requires are judged (scope cuts, routing registers and CP-0's
  launcher-made P registers are recorded as "not required in this transport"). The CP-MODEL tables
  are never read (ROUTING_RULES forbids them). A declared column naming a downstream or receiving
  module (`downstream_use`, `Downstream Impact`, `downstream module`) is never required: ROUTING_RULES
  tells every module not to map downstream dependencies.
- Sent back (status `missing`), one issue per register: a declared column absent from every table
  under a required register's heading, for the ten modules only. Header cells are read as labels
  (emphasis, case, `_`, `.`, hyphens, `?` and a plural `s` aside; `&` and `+` as `and`; a trailing
  bracketed unit such as `(USD m)` aside); a joined header holds each part (`Currency and scale`
  holds `currency`); a joined declared name is present as its parts (`evidence/date` as two
  columns); a header that starts with the name counts (`Principal amount`); extra columns and any
  order are allowed. Not sent back: a register whose every row states a gap (`Not supplied:
  <reason>` or `[Insufficient Information]` beside at most a label), a register written as rows
  (a missing column's name is a row label), and a blocked module (`module_status: Blocked`).
- Recorded, never sent back (status `noted`, new): a placeholder in a critical column (in this
  transport an explicit gap is the required answer, so it classifies the run as not full
  analytical), fewer rows than the method's minimum (CP-2's T2.12 asks for 8 triggers; the evidence
  may support fewer, and the presence rule's gap form is one row), a template register with no
  period column, a malformed contract list, and, for every module outside the ten, a missing
  column: those modules have no presence check and no retained handoff to calibrate against.
- Calibration (real): the two retained CP-2E handoffs (`tests/fixtures/esg/CP-2E-h3.md`, `-h4.md`,
  TransDigm, 2026-11-13 Sol runs) send nothing back: 14 in-scope registers each with every declared
  column; h3's 7 placeholder cells (T2F.3, T2F.5, T2F.6, T2G.4) are noted, the same cells the
  script's own CLI reports. No other module has a retained full handoff in this repository, so the
  column rule is unproven on real CP-0, CP-1A, CP-DR, CP-2, CP-2A, CP-2G, CP-3, CP-5 and CP-6 output.
- Modules with no contract: CP-1's SKILL.md (caos-databricks) declares no Output profile (one "not
  checked" outcome); CP-L10 and CP-8 are sent no SKILL.md (no record unless another check applies).
- No note is sent: TRANSPORT_RULES already tells every module to do the completeness check itself,
  and `earnings_update` has 93 characters left under its ceiling.
- The launcher's synthetic integration answers for CP-2E (T2F.5) and CP-2G (T2H.4 to T2H.6) were
  partial tables; they now carry every declared column (`Not supplied` where synthetic), since a
  handoff without them would be sent back.

## Status

Built and tested offline, module by module. Not accepted: no model has written a restored register
under these instructions; that needs the owner's paid run.
