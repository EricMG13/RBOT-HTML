# CP-1 runs the Deploy V method, adapted, and its figures are checked in code at acceptance

by: user
date: 2026-11-13

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line; paid execution still needs its own explicit action. No run has been made with this method.

Owner's words, 2026-11-13: "Gate CP-1 in code, then run_script for calculations (Recommended)";
"Catch at handoff only, for now (Recommended)"; "given handoffs are used for analysis correcting and
validating key modules should have downstream impact (cp-1 financials etc)"; "2. carrying value
3. needs to be adapted for deploy v format and your current WIP". The Deploy V module scripts were
written "to stop the model from self validation and calculation"; CP-OS runs none of them.

## Decisions (owner)

- Method source: `caos-databricks/vendor/deploy-v/skills/cp-1-canonical-data-foundation` at
  `dfff264` (documents last changed `a14f9051`, `b283233c`, `cc9c3e58`; Deploy V `c4d2e35` is the
  ancestry). Archived byte for byte, then changed by named edits recorded in
  `docs/reuse/selected-methods/manifest.json` and `METHODOLOGY-REVIEW.md`.
- Debt basis: total debt, net debt and leverage use balance-sheet carrying value. The maturity
  ladder stays contractual principal and carries a stated reconciliation to the carrying total.
- EBITDA: reported EBITDA is the primary denominator; adjusted EBITDA is shown beside it and
  labelled when the issuer states it.
- CP-1's figures are checked in code when its handoff is written, through the existing rejection
  path. Nothing downstream re-checks them.
- Prompt-size ceilings (`INSTRUCTION_BUDGET`) are not raised.
- Own currency (2026-11-13, relayed by the coordinator session). Question put: "PR 111, non-USD
  issuer: state leverage in the issuer's own currency, or keep it as a gap?" Owner: "Yes". The
  coordinator read this as the first choice and told the owner so; it is built on that reading.
  CP-1's money tables (net debt, the money charts, the debt reconciliation, the register's fixed
  rows) are in the money unit: `US$m` when the statements are in USD, otherwise the statements'
  currency code and `m` (`GBPm`), in millions even where a statement prints thousands. The ties
  run in that currency. Nothing is converted and no FX is computed.
- Adjusted-only EBITDA (2026-11-13, relayed by the coordinator session). Question put: "PR 111,
  adjusted-only EBITDA: allow headline leverage on adjusted EBITDA, labelled as such, or keep it
  empty?" Owner: "First choice". Reported EBITDA stays primary whenever the issuer states it. An
  issuer that states only adjusted EBITDA heads the leverage and interest-cover columns with the
  adjusted metric names, tied to the adjusted register rows; the header is the label every reader
  draws. A reported figure is never fabricated.

## Decisions (controller, for the owner to confirm or reverse)

- What CP-1 is sent: the edited SKILL, runbook and step file, then `prompts/CP-1.md` (unchanged),
  the confidence score section and a launcher block stating what the check refuses. The five
  `STEP_CONTRACTS` sections (about 24,000 characters written for the earlier JSON runtime) are no
  longer sent. An audit of what they held found one rule a check depends on (the sign of cash
  interest, now stated) and these lost rules, left for the owner: a refund on an outflow line is
  recorded as missing; a page is never called absent when the extraction lists it; a claim's
  lineage class is never stronger than its record.
- Step 13 of the method ("Model Workbook Interface") is dropped as the workbook step: its tagged
  tables, table ids and CP-MODEL readiness. Its analytical rules are kept, restated in the steps
  they belong to: cash conventions, the debt instruments table, the add-back bridge, period
  derivation, the reconciliation list, segments, operating KPIs, pro forma adjustments.
- Leases: total debt is the debt the issuer's balance sheet carries. Lease liabilities on their
  own balance-sheet lines are not added; an obligation the issuer carries inside its debt lines
  stays in and is named (TDG: 262 of finance leases inside 24,880). Deploy V's model register
  excluded every lease from `total_debt`; this differs and is the controller's reading of
  "carrying value".
- Cash interest paid is written as a positive amount; the three activity totals are signed.
- CP-1 always writes the Period table (`| Period | Start | End |`). The check finds a fiscal year by
  the date its period ends, never by the form of a Period cell or by year arithmetic. An issuer
  whose fiscal label and year-end date fall in different years writes the date alone in its Period
  cells (`period_order` refuses `FY2024 / 2025-02-01`; that predates this change).
- Each table the check reads must appear exactly once in the handoff, inside `## Findings`, so the
  check, the charts and the Changes page read the same table.
- The check (`src/deploy_workflow/owners/cpos_cp1_check.py`) refuses: a missing required table (six:
  the three statements, the calculation register, the debt reconciliation, the Period table) or
  fixed row (counted by code); an unreadable operand; a leverage or cover figure that is not its
  stated numerator over its stated denominator, to two places; a chart figure that differs from
  the calculation register; operands that differ from the net debt table or the statement lines
  for the fiscal year; net debt cash that differs from balance-sheet cash; statement totals that
  do not tie (assets to liabilities and equity; operating, investing, financing and FX to the
  change in cash; opening plus change to closing); a ladder that does not sum to the stated
  principal; principal plus reconciling items that is not the carrying value; a carrying value
  that is not the gross debt. A figure stated on one side of a tie and missing on the other is
  refused. Missing is never read as zero.
- Limits of the check, by design: it proves CP-1's tables agree with each other, not with the
  filing. `FX Effect on Cash`, `Temporary Equity` and `Reconciling items` are each stated once and
  can absorb an error. Interim rows have no statement tie (their EBITDA is a last-twelve-months
  figure), so an interim reported row could carry an adjusted EBITDA unnoticed. The money tables
  of other modules (CP-2D, CP-3C, CP-4C) stay `US$m`, so a non-USD issuer's cells there read
  `Not supplied:`; the run-start form says so. Any three-letter code in the statements' `Unit`
  is taken as a currency. `Unit` accepts `millions` and `thousands` only. A register with none of
  the six fixed metric rows passes when the charts are gaps.
- Adjusted-only, the controller's defaults: periods are not mixed (if reported EBITDA is stated
  for any period, the reported headers are used and a period with only adjusted EBITDA is a gap
  in the chart); a reporting currency entered at run start that differs from the statements is
  not flagged.
- Library, as the code stands (corrected 2026-11-14; an earlier version of this record said
  adjusted leverage was kept out of the screening filters, which was wrong). An adjusted-only
  run's leverage, net leverage and interest cover are stored under the same metric keys as a
  reported run's, with the adjusted name as `label`. The library's range filters and sort read
  the number only, so an adjusted multiple is filtered and ranked beside reported ones. The run
  card names the adjusted measure and the list view marks the figure `adj.` (full name on hover).
  Open for the owner: whether adjusted figures stay in the leverage filters and sort.
- On the Changes page a run on reported EBITDA against a run on adjusted EBITDA is "not
  comparable", with both labels in the reason; no difference is printed.
- Instruction size. The method text CP-1 is sent was shortened by 5,851 characters (duplicate
  statements and wording; four rules a first cut made vaguer were restored after review), the
  share agreed with the T4 session, which cut its own text. With T4 and `main` merged in, the
  tightest pathways are earnings_update (545,009 of 546,000) and short_snapshot (155,712 of
  157,500).
- `calculate` gains `difference` and `product`; both refuse a result that 38 digits cannot hold
  exactly. `sum` is unchanged.

## Consequences

- A CP-1 handoff retained from before the check does not pass it and is not resumable: a relaunch
  into a run folder prepared before this change is refused at launch (the folder holds a different
  request), and a retained CP-1 replayed into a new run is refused by the check. Either way it
  needs a new run. Both retained TDG handoffs fail
  (none of the six required tables; ladders of 24,319 and 24,806 against a stated principal of
  25,068, short by 749 and 262; leverage on principal over adjusted EBITDA).
- Earlier runs state leverage on principal over adjusted EBITDA (TDG FY2024: 6.01x total, 4.51x
  net, 3.60x cover). On carrying value over reported EBITDA the same year is 6.53x, 4.88x and
  3.29x. The Changes page will show this as a method change against any earlier run, not as a
  change in the issuer.
- Forecast, charts, Overview and Changes read CP-1's tables, so a paid run is needed before this
  is accepted. That run is the owner's separate action.
- CP-1 now carries the confidence score section and owes `### Confidence inputs`.
- T7 (`run_script`) builds on the `calculate` change; the check's fixed row names are the
  interface a script would read.

## Open after the whole-branch review (for the owner)

- Fixed in a fourth round the owner approved (`8424d1b`, adversarial re-review: pass): rows of
  different checked tables are matched by the period the Period table dates, so `FY2024` in a
  chart, `FY2024 / 2024-09-30` and `2024-09-30` are one period, and a correct handoff with an
  interim balance sheet is no longer refused.
- Decided by the owner and built (see the two owner decisions above): a non-USD issuer states
  leverage in its own currency, and an adjusted-only issuer states headline leverage on adjusted
  EBITDA. The run expectation `chart-strip-usd`, which asserted the earlier behaviour, is removed.
- No model output has yet passed the check. It asks for exact headings, a 13-column register,
  exact row names and plain numbers within three writes (`MAX_WRITES`); if a real CP-1 cannot do
  that, every run stops at the second module. A paid run is the owner's separate action.
- Lower: two fiscal labels given the same End in the Period table are treated as one period (a
  self-contradictory Period table is not refused); the Period table has no heading rule (ask for `### Period table`); a blocked CP-1 still
  has to write a period column header and a `Unit`; a second table under a statement heading is
  not read; a register header one letter off hides the register's other issues until the next
  write; an `LTM` statement column is refused and nothing says it belongs in the derived-period
  table; the Changes page cannot read free cash flow from the statement tables' `Unit` column;
  a unit such as `US$m (thousands)` is told to move the note to Basis, which
  keeps a thousands figure under a millions unit (predates this change);
  two `calculate` tests are weaker than they should be (one accepts either an error or a null;
  one uses `sum` as its oracle); the money-unit pattern is written in both delivery and the
  library store; one manifest `edit` string names two sentences as added before saying they were
  later dropped; `prompts/CP-1.md`, which now carries three rules the method no longer repeats,
  still opens "not connected to the imported runtime".
- Size: the check module and the branch are well over the 800-line guideline. The rewrite tournament's verdict was to keep the design; its optional
  simplifications remove about 85 lines.
