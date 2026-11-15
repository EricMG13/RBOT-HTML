# Method scripts as acceptance checks: what is wired and what remains (2026-11-15)

Owner, 2026-11-15: "scope it now, wire the scripts in as checks. every module has a scripts
folder tied to it. which you should review." Selection: `METHODOLOGY-REVIEW.md`, paragraph "Method
scripts as acceptance checks". Harness: `src/deploy_workflow/method_scripts.py`. This file is the
scope for the modules not yet wired; nothing in it is built.

## How a check works (the pattern the rest follow)

1. The script runs only from the bytes `manifest.json` registers for it (shared `cp_tables.py` and
   `validate_handoff.py` included), compiled in memory; `sys.path`, `sys.modules` and
   `sys.dont_write_bytecode` are restored.
2. Its inputs are read from the handoff's own registers (a `###` heading starting with the method
   id, or a `<!-- table-id: -->` tag); figures are parsed by the script's own `parse_figure`.
3. Currency and scale must match across every row used before anything is compared.
4. A stated figure agrees within one unit of its last displayed decimal place (or the script's
   own rounding, if coarser). Only a disagreement is an acceptance issue (one repair turn); a
   missing input, an unreadable cell, a row outside the formula, an absent register or a script
   failure is "not checked" with its reason, recorded, never zero and never a refusal.
5. Every outcome is kept beside the attempt's review: `requests/<module>/<fingerprint>/<n>.method-checks.json`
   (`kind: method-script-checks/1`). The library's Evidence page does not show it yet.
6. The module's instructions get one note before its method block (`method_scripts.NOTES`) naming
   the figures Python recomputes and how to write their inputs.

## Wired

| Module | Script | Inputs read | Figures checked | Not checked by design |
|---|---|---|---|---|
| CP-2D | `liquidity_bridge.py` | T2E.5 rows (method's names), `Amount`, `Currency and Scale`; T2E.6 `Months to Empty` row | Ending accessible liquidity; Months to Empty when T2E.6's Cash-Burn Basis names the T2E.5 bridge (12 months) | Beginning accessible liquidity as cash + accessible revolver (not a script figure); average monthly burn (T2E.6 states no currency or scale) |
| CP-3C | `funding_gap.py` | T3D.2 `Instrument`, `Amount`, `Currency`, `Scale`, `Years to Maturity`; new `### Funding gap` table (Horizon, Cash, `Facility: <name>` rows, Forecast free cash flow) | Maturities due, Available liquidity, Funding gap (as-of view) | The pro-forma-for-subsequent-events view (T3D.2 is the as-of wall); gross vs carrying conflicts (T3D.2 has no gross column) |

CP-3C's `### Funding gap` table is new: no CP-3C register holds the horizon, the cash, the facility
terms or the gap the script owns (T3D.3 is qualitative). If the owner does not want the table,
remove `CP3C_NOTE` and the check records every CP-3C figure as not checked.

The owner modules `owners/cp2d.py` and `owners/cp3c.py` (the Deploy VII journal path) hold older
hand-written calculations of the same quantities and are not wired in. Where they differ from the
scripts: `cp2d` derives a run-rate annual flow (cash from operations + investing + financing - net
debt issuance) and counts months until cash plus undrawn revolver reaches a minimum cash, in
Decimal to one place (half up), over a 1 to 60 month horizon with dated maturities;
`liquidity_bridge.py` sums the method's eight signed bridge components over the 12-month bridge,
has no minimum cash, and gives Months to Empty as beginning accessible liquidity over the monthly
burn, in floats to two places, none when the burn is not positive. `cp3c` applies resources
sequentially at each maturity (base less minimum cash, plus the run-rate flow to that month, less
amortisation and principal already paid) and has no rule for a facility that expires or is
uncommitted; `funding_gap.py` takes one window: maturities due within it against cash, the undrawn
part of committed facilities that outlive it, and forecast free cash flow, the gap floored at 0,
with a currency guard.

Cost: a disagreement costs a repair write inside the module's call (at most three writes,
`MAX_WRITES`), under the run's USD cap. Worst case per checked module: two extra writes; a module
whose figure still disagrees after them fails acceptance like any other unresolved issue. A
script failure or an unreadable register is "not checked" and costs nothing. The two notes add
2,029 characters to each of `credit_snapshot`, `relative_value` and `covenant_refinancing`.

## Wired next (2026-11-15, second part)

Ruling `docs/rulings/2026-11-15-method-script-checks.md` (owner: "restore the cut tables"). Each
module's mapping is `deploy_workflow.method_scripts_<module>`.

| Module | Script | Registers read | Restored | Note sent |
|---|---|---|---|---|
| CP-2E | `rate_fx_sensitivity.py` | T2F.4, T2F.5 | T2F.4, T2F.5 | yes |
| CP-3 | `recovery_waterfall.py` | a `### Recovery waterfall` table, if present | none (T3B.2, T3B.4, T3B.6 hold no input) | no: owner decision |
| CP-2G | `credit_metrics.py` | T2H.4, T2H.5, T2H.6 | none (never cut) | yes |
| CP-4 | `covenant_headroom.py` | T4C.4 | none | yes |
| CP-1 | `credit_metrics.py` | T4.8 LTM rows, T4.9 free-name rows | none | no: `earnings_update` ceiling |

Next in this document's order: row 4 (`completeness_check.py`), then CP-4C, CP-1C, CP-2H, CP-1B.

## The rest, in the order proposed

Pathways from `PATHWAY_MODULES` (`short_snapshot` deactivated). Evidence: the two retained Sol
runs are TransDigm `credit_snapshot` runs of 2026-11-13, written before the register cut; no
other pathway's module has a retained handoff. "Checkable now" means the inputs and the stated
figure are in registers the module writes in this transport; the extraction rules still need
synthetic proof as for CP-2D and CP-3C, and real column names are unproven until a paid run.

| # | Module (pathways) | Script | What it could check here | Input and output registers | Cut by the scope file? | Evidence | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | CP-2G (credit_snapshot, covenant_refinancing, distressed_restructuring) | `credit_metrics.py` | KPIs per case and period; the debt and cash roll-forward residual | T2H.4 `EBITDA`, `FCF`; T2H.5 opening, issuance, repayment, interest, closing debt and cash -> T2H.6 gross and net leverage, coverage, FCF/debt | No (only T2H.1, T2H.2, T2H.9 are cut) | Both Sol runs wrote T2H.4, T2H.5 and T2H.6 (high run: T2H.5 read by CP-5, T2H.6 by CP-3) | Checkable now; needs a rule for the combined `x/y` cells |
| 2 | CP-4 (credit_snapshot, covenant_refinancing, distressed_restructuring) | `covenant_headroom.py` | Signed covenant headroom and status by test type | T4C.4 `Test Type`, `Threshold`, `Current Basis` -> `Headroom`, `Status` (CP-4A phase; `REF_CP-4A_STEPS.md`) | No CP-4 section | CP-4 was blocked in both Sol runs (no legal documents); synthetic only | T4C.4 checkable now; basket capacity (T4C.5) and maximum additional debt have their inputs only in `Formula` / `Current Input` text |
| 3 | CP-1 (every pathway) | `credit_metrics.py` | LTM derivation and the KPIs `cpos_cp1_check` does not recompute | T4.4 to T4.6 and `Net debt data` -> T4.8 `Full-Year Component`, `Current Stub`, `Prior-Year Stub`, `Derived Value`; T4.9 free-name rows `Numerator Value`, `Denominator Value`, `Calculated Value` | No CP-1 section | Fixture `tdg_sol_high_2026_11_13/CP-1-tables.md` (older layout, no T4.8/T4.9) | Checkable now; `cpos_cp1_check` already recomputes the six fixed T4.9 rows, so this adds T4.8 and the free-name rows. The fixture shows the trap: leverage on principal (25,068 / 3,813 = 6.57) against carrying value (24,880, 6.53), so an operand's identity must be bound |
| 4 | Every module | `completeness_check.py` | Columns, row counts, placeholder cells (below) | The module's own Output profile | Its contract includes the cut registers | Appendix inventory, both Sol runs | Needs the wrapper below |
| 5 | CP-4C (distressed_restructuring) | `recovery_waterfall.py` | Allocation by class, recovery %, fulcrum, low/base/high | T4E.2 claims (`principal`, `accrued`, `PIK`, `priority`); T4E.3 `scenario`, `EV` -> T4E.5 allocation, T4E.6 fulcrum, T4E.7 recovery; launcher `Chart data: recovery by class` and `value allocation` | No | None | Checkable now for a single-pool allocation (the script does not split by entity) |
| 6 | CP-1C (relative_value, distressed_restructuring) | `peer_statistics.py` | Peer min, max, median, Q1, Q3, average under the minimum-N gates; implied EV | T4.3 to T4.5 values and comparability status, T4.7 outliers -> T4.6 `Peer Avg`, `Median`, `Min`, `Max`, `Q1`, `Q3`, `N`; T4.10 implied EV | No | None | Checkable now once the owner fixes the quartile convention (the method names none; the script's is inclusive) |
| 7 | CP-2H (distressed_restructuring) | `covenant_headroom.py` (`trigger_headroom`) | Signed rating-trigger headroom by direction | T2R.4 `trigger direction`, `threshold`, case or period value -> `headroom`, `status` | No | None | Point headroom checkable now; "sustained" needs an observation window no column holds |
| 8 | CP-1B (earnings_update) | `credit_metrics.py` (`growth`) | Percentage change only (absolute change is not in `compute`) | T4.6 `Prior Value`, `Current Value` -> `% Change`; T4.4 YoY columns | No | None | Checkable now (T4.4 only where its YoY pair can be identified) |
| 9 | CP-2E (every pathway but lite_credit_assessment) | `rate_fx_sensitivity.py` | Unhedged floating debt and share; +100 bp cash-interest impact | T2F.4 `Total debt`, `Gross floating-rate debt`, `Hedged floating-rate debt` -> T2F.4 unhedged rows; T2F.5 `Estimated Cash Impact` | Yes: T2F.2, T2F.4, T2F.5 | Both Sol runs wrote T2F.4 and T2F.5 before the cut | Owner decision: restore T2F.4 and T2F.5 or leave unchecked; FX and cost inputs are free text |
| 10 | CP-3 (credit_snapshot, relative_value, portfolio_decision) | `recovery_waterfall.py` | Recovery by class under each EV case; fulcrum movement | Claims T3B.2 `Amount`, `Seniority / Lien`, T3B.4 rank; EV cases: no register; outputs: none (T3B.6 is a label) | Yes: T3B.2, T3B.4, T3B.6, T3B.8, T3C.7 | High run wrote T3B.2 and T3B.6 before the cut | Owner decision: restore the cut registers and add an EV case table, or leave unchecked |
| 11 | CP-3D (relative_value) | `bond_analytics.py` | YTM, YTW (and which leg), spread, break-even default | T3E.1, T3E.2, T3E.5; call prices, years to maturity and a numeric benchmark yield are not columns | No | None | Needs a new table like CP-3C's (owner decision); the engine refuses accrued interest and dated settlement |
| 12 | CP-2G | `liquidity_bridge.py` | Bridge, burn, Months to Empty | No register holds the bridge components or the period | No | - | Needs a new table (owner decision); CP-2D's check covers the method's own bridge |
| 13 | CP-4C | `funding_gap.py` | Funding gap | No CP-4C register holds maturities, cash or facilities | No | - | Needs a new table (owner decision) |
| - | CP-2H | `bond_analytics.py` | - | The method names it nowhere | - | - | Not applicable: drop |
| - | CP-0, CP-1A, CP-1D, CP-2, CP-2A, CP-5, CP-6, CP-DR, CP-L10 | shared scripts only | Rows 4 and the `validate_handoff.py` section | - | - | - | `confidence_score.py` is already re-implemented (`deploy_workflow.confidence`); `validate_research.py` (CP-DR) is not archived: it needs `credit_os_v` |

Proposed order: 1, 2, 3 (the full credit assessment's modules, CP-2G with real register
evidence first), then 4 (it touches every module, so prove it against the retained inventory
before it refuses anything), then 5 to 8 (pathways with no retained run), then the owner
decisions 9 to 13. One module at a time, each as CP-2D was done: map the inputs, synthetic cases
worked by hand, the note in the module's instructions, the checker, the record.

## `completeness_check.py` (shared, cp-os version)

What it adds beyond the launcher's `register_issues` (which checks only that each in-scope
required register's heading or tag exists, and only for the ten modules with a scope section):
each required register's declared columns present (with template-period columns in order), its
`minimum_body_rows`, and, in every critical column, no disqualifying placeholder from
`critical_cell_values_casefold` (`[insufficient information]`, `n/a`, `tbd`,
`not calculable from provided materials`, `unavailable`, an empty cell) or substring. It runs
for every module, not only the ten.

What in this transport conflicts with the SKILL.md profile it reads:
- Cut registers: it requires every `required_registers` entry, including those
  `CPOS_REGISTER_SCOPE.md` cuts (CP-0, CP-1A, CP-DR, CP-2, CP-2A, CP-2E, CP-2G, CP-3, CP-5, CP-6) and
  the routing registers `ROUTING_RULES` forbids (CP-0 T7/T8, CP-1A T2D.10, CP-2A T2B.8/T5.6).
- `unconditional_stable_tables_cp_model`: it demands the CP-MODEL interface tables, which
  `ROUTING_RULES` tells modules not to write (`cp2g.cp_model_forecast_drivers`, `cp2b.cp_model_catalysts`).
- Placeholders: the blocklist marks a run not "full analytical"; in this transport an explicit
  gap is the required answer for missing evidence, so a blocklisted cell is a classification,
  not a refusal. `Not supplied: <reason>` (the transport's gap form) is not on the list.
- Header matching is exact text: a header cell in bold or backticks reads as a missing column.
- Register ids are found by `[PT][0-9]…|TL…` only: the CP-1A registers named by slug
  (`source_classification`, `credit_translation`) are never found.
- The dropped confidence fields are not its subject (that is `validate_handoff.py`).

Smallest adaptation that runs it truthfully (a wrapper, no byte edited): call its `load_contract`
on the module's sent SKILL.md, drop the registers `cpos_launch.required_registers` does not
require (scope cuts and routing registers) and the CP-MODEL tables, then run its own
`find_registers` and `resolve_columns` and the row-count and placeholder loop of its `check` on
what remains; send back a missing column or a short register as an acceptance issue (like
`register_issues`), and record placeholder cells as "not full analytical" without a refusal.
Strip `**`/backticks from header cells before matching. The appendix inventory (two retained Sol
runs) is the evidence to test the column check against before it refuses anything.

## `validate_handoff.py` (shared)

Only its `unfenced_markdown` runs today (`cp_tables` imports it). Its checks, against this
transport:
- Overridden on purpose: the canonical H2 layout (Audit Summary, Analysis, Evidence Trace, Source
  Registry, Gaps & Conflicts; this transport's six are Request, Sources, Findings, Calculations,
  Gaps, Next module, checked by `cpos._checked_handoff`); the front-matter fields
  `confidence_score`, `confidence_band`, `qa_status` and their caps (the module states none;
  `_front_matter_score_issues` refuses them; Python computes the score); `upstream_artifacts_used`
  and `downstream_consumers` (ROUTING_RULES; CP-OS pins upstream handoffs by sha256 itself);
  `run_id`, `reporting_period`, `analysis_date`, `committee_status` and the canonical filename
  (the run record and the checker's as-of date and sha256 anchors carry identity).
- Still applicable, as warnings: its presentation checks (`_presentation_warnings`): a detailed
  table placed before the analytical appendix heading, reader tables wider than its column cap or
  longer than its row cap, raw appendix columns in a reader table, and a table with no prose
  takeaway after it (the transport's `CHART_NOTE_RULE` asks the same for chart tables).
- CP-DR's research fields (`scope_type`, `research_status`, `approved_plan_hash` …) belong to the
  cp-os research envelope, which this transport does not use.

Smallest adaptation: call `_presentation_warnings` on the `## Findings` body read as its
`## Analysis`, record the warnings and refuse nothing; the field checks stay overridden.
