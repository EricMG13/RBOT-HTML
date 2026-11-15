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

## The rest, in the order proposed

(The per-module table is being compiled from the skills and the retained-run inventory; it follows in the next commit.)

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
