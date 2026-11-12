# TDG FY2024 (as of 2024-09-30): gpt-6.1-sol mixed medium/high vs all-medium, to CP-2

Ruling: `docs/rulings/2026-11-12-tdg-mixed-effort-to-cp2.md`. Historical case; not a current credit view.

## Runs

| Side | Run | Modules | Charged USD |
| --- | --- | --- | --- |
| Mixed | main checkout `runs/cpos-tdg-sol-mixed-cp2-001` (2026-11-12) | 10 requested; 6 accepted; stopped at CP-1D | 3.46 |
| Medium A (primary) | `/private/tmp/claude-501/rbot-live7/runs/tdg-all-001` (2026-11-10) | 20 requested | 4.32 for the same ten |
| Medium B | main checkout `runs/cpos-tdg-sol-medium-all-001` (2026-11-09) | 20 requested; CP-1B, CP-1C, CP-1D, CP-2A Blocked | 3.13 for the same ten |

Mixed: high effort on CP-0, CP-1A, CP-1D, CP-2, CP-2A; medium on CP-1, CP-1B, CP-1C, CP-DR, CP-2E
(`--high-modules`, recorded per call in `live/calls.jsonl`). CP-2, CP-2A and CP-2E never ran.

Stop: CP-1D's draft had one table (draft line 229) with a 7-column header over an 8-column
separator. The checker's message, "Invalid Markdown table header", names no table or line; the
model changed other tables on each of three attempts. Not an effort effect.

Not like for like: module instructions changed after both baselines (reader-voice ruling,
2026-11-11; files 15-112% larger); mixed requested 10 modules, A requested 20 (A's CP-0 covers
more); mixed routes each module only its registered producers' handoffs, so CP-1A had no CP-1
handoff and fed none of CP-1B, CP-1C, CP-DR, CP-1D. One run per setting.

## Cost and size per module

| Module | Effort (mixed) | Mixed: USD / reasoning tokens / words | Medium A |
| --- | --- | --- | --- |
| CP-0 | high | 0.45 / 1,654 / 5,946 | 0.30 / 332 / 4,440 |
| CP-1 | medium | 0.51 / 1,886 / 8,826 | 0.34 / 885 / 9,162 |
| CP-1A | high | 0.45 / 3,588 / 8,920 | 0.29 / 412 / 6,939 |
| CP-1B | medium | 0.58 / 1,709 / 10,093 | 0.52 / 2,810 / 9,425 |
| CP-DR | medium | 0.25 / 949 / 4,729 | 0.33 / 1,409 / 5,215 |
| CP-1C | medium | 0.27 / 516 / 5,211 | 0.35 / 650 / 5,146 |
| CP-1D | high | 0.94 / 7,145 / not accepted | 0.53 / 1,894 / 8,603 |

High modules cost 1.5-1.8x their medium baseline; medium modules moved 0.75-1.5x with no direction.

## Analysis quality (independent read of the handoffs, figures checked against the 10-K)

- CP-0 (high): no gain. Medium A found two real documentary conflicts (Amendment No. 17 title,
  revolver rate wording) that mixed missed; mixed added comparable caveats (pro forma vs reported
  liquidity, guarantor date, preliminary purchase accounting). Medium B also missed A's conflicts,
  so this is within run-to-run noise.
- CP-1A (high): modest gain, confounded. New verified points: debt prepayment is last in the stated
  excess-cash priority order (10-K p.54); government "fair and reasonable" pricing reviews; the
  USD 2,020m vs 2,038m dividend reconciliation. Most of its extra quantification exists because it
  had no CP-1 handoff, and its output reached no downstream module in this run.
- CP-1D (high, unaccepted draft): clear gain in substance. It ties USD 204m of the USD 360m
  add-backs to specific non-cash entries and gives a supported-only EBITDA of USD 4,017m (6.24x);
  medium A withheld a figure and rejected all refinancing costs on recurrence alone. One error:
  it omits the USD 3m Amendment No. 14 write-off (supported refinancing 52, not 49). Never
  accepted or consumed, so no end-to-end benefit is shown.
- Medium controls (CP-1, CP-1B, CP-1C, CP-DR): every checked figure matches across runs; same
  conclusions; status labels and headline basis vary. None shows a need for more than medium:
  CP-1C and CP-DR are limited by missing evidence, not reasoning.

All tabled figures on both sides agree with the 10-K except the USD 3m omission above.

## Verdict

High effort is supported for CP-1D (judgement on add-backs) and not for CP-0. CP-1A is
inconclusive. CP-1, CP-1B, CP-1C and CP-DR are adequate at medium. CP-2 and CP-2A were not tested
in this run; the 2026-11-09 comparison (main checkout `runs/tdg-effort-comparison.md`) remains the
only CP-2 evidence.

Not verified: CP-2, CP-2A, CP-2E under the mixed setting; a second sample of any setting; a
same-code all-medium control; CP-1B, CP-1C and CP-DR were read in part; whether a resumed CP-1D
would pass once the table is fixed.

## Effort map (Balanced), owner instruction 2026-11-12

Rule drawn from the findings: high effort pays where a module weighs evidence and reaches a
judgement; it does not pay where a module inventories, extracts, calculates or is limited by
missing evidence. `BALANCED_HIGH_MODULES` in `src/deploy_workflow/owners/cpos_launch.py`.

| Module | Balanced effort | Basis |
| --- | --- | --- |
| CP-0 source readiness | medium | Measured: gain on 2026-11-09, none on 2026-11-12; within noise |
| CP-1 financial foundation | medium | Measured twice: figures identical, no gain |
| CP-1A business and transaction | high | Measured twice: verified extra issuer points each time; modest |
| CP-1B earnings delta | medium | Measured: adequate |
| CP-1C peer benchmark | medium | Measured: limited by missing peers, not reasoning |
| CP-1D earnings quality | high | Measured: clear gain (unaccepted draft) |
| CP-DR deep research | medium | Measured: limited by missing evidence |
| CP-2 credit synthesis | high | Measured 2026-11-09: largest gain |
| CP-2A downside pathway | high | Inferred (judgement); untested |
| CP-2D liquidity bridge | medium | Inferred (calculation); untested |
| CP-2E macro, FX, hedging | medium | Inferred (calculation); untested |
| CP-2G forward model | medium | Inferred (calculation); untested |
| CP-2H rating migration | medium | Inferred (mapping); untested |
| CP-3 relative value | high | Inferred (judgement); untested |
| CP-3C refinancing risk | high | Inferred (judgement); untested |
| CP-3D market-implied risk | medium | Inferred (evidence-limited); untested |
| CP-4 legal and covenants | high | Inferred (interpretation); untested |
| CP-4C restructuring | high | Inferred (judgement); untested |
| CP-5 evidence trace | medium | Inferred (mechanical check); untested |
| CP-6 committee challenge | high | Inferred (judgement); untested |

Nine of twenty modules run high. Twelve of the twenty rows rest on inference, not a run.
