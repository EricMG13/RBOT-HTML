# Module presets, forecast, Changes section and short snapshot: decisions M1-M7

by: user
date: 2026-11-11

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line; paid execution still needs its own explicit action.

Owner's words, in order:

- "cp-dr should be on every run or cp-1c wont work. so should cp-2e. cp-model and forecast are them
  same. cp-8 - give me some ideas, perhaps compares vs same pathway run etc. cp-10 - re-write to be
  short version of credit shot."
- On web search for CP-DR from the run page: "1. approved". On CP-8 ideas (1 same-pathway previous
  run, 2 view drift over time, 3 limitations ledger): "2. 1,2 and 3". On the short snapshot (own
  pathway of CP-0, CP-1 and one CP-L10 page): "3. approved". "4. allow forecast to function with
  just relevant layer 1 modules. but works better with cp-2g included."
- On four follow-up points (short snapshot gets no CP-DR/CP-2E; CP-2G added to credit_snapshot and
  covenant_refinancing; one paid CP-DR web-search test first, cap USD 10; amend H5 for Overview
  additions): "approved but make cp-8 a section just like forecast, overview and the others. it is
  focused on changes regarding the issuers business and credit profile. as well as, changes
  regarding the modules findings. in short 'what has changed since the last time i looked at this'.
  consider how charts and visuals can be used to present this. and if the methodology should be
  updated."

## Decisions

- M1. CP-DR in every pathway preset except the short snapshot. It orders itself before CP-1C
  (methodology.json dependencies).
- M2. CP-2E in every pathway preset except the short snapshot.
- M3. CP-MODEL means "publish the forecast". It works from layer 1 (CP-1 states base operands and
  run-rate drivers; non-blocking); CP-2G's drivers and cases replace them when CP-2G ran.
  credit_snapshot and covenant_refinancing also gain CP-2G (which needs CP-2A).
- M4. Standing run-start ruling gains `web-search` only after the paid test
  (docs/rulings/2026-11-11-cpdr-web-search-live-test.md) shows the provider accepts it.
- M5. CP-8 runs last in a run when an earlier listed run of the same issuer and pathway exists
  (latest with as-of on or before this run's, ordered by as-of then first call start, earlier
  format included). It is removed from the portfolio_decision preset. Its findings are shown in
  their own section of the issuer report ("Changes"), not on Overview.
- M6. Short Credit Snapshot: pathway id `short_snapshot`, modules CP-0, CP-1, CP-L10.
- M7. Ledger statuses: Closed, Remaining, New, No longer stated.

## Status in the change that records this

Built: M1 and M2 (presets, and CP-2G added to credit_snapshot and covenant_refinancing from M3's
preset list; CP-8 leaves portfolio_decision).

Decided, not yet built: M3 (layer-1 forecast), M4 (standing ruling; waits on the paid test), M5 (CP-8
run and Changes section; only its removal from the preset is done), M6 (short snapshot), M7 (ledger
statuses).

## Amendment 2026-11-12: M5, M7 and the CP-8 half of M8 built (engine and method; no paid call)

Built on `claude/cp8-changes`. The old route that compares two delivered bundles
(`cpos.run_comparison`) is untouched; this is the in-run route. The library's Changes section is a later
task and reads the data contract below.

**Prior-run rule (one function, `deploy_workflow.changes.find_prior`).** Among the runs the issuer
library lists (`library_index.admit_run`: completed, every module answered in its own run; earlier-format
and earlier-methods runs included), those with the same issuer and pathway and an as-of date on or before
this run's, excluding this run's own folder. The latest is chosen by (as-of date, first model-call start,
folder name). None: CP-8 is not planned and the run records `changes: first run of this pathway`. A run
folder outside a `runs` folder searches nothing and records `changes: not compared: ...`. Otherwise
`prepare` plans CP-8 last (registry fan-in, as CP-5's) and copies the prior run's delivered handoffs, CP-8
excluded, into `<run>/prior/<module>.md`, pinned as sources with their hashes. The prior run's folder is
read, never written. A run folder that already holds `workflow.json` keeps the pins it records: a newer
completed run cannot change the manifest and get the relaunch refused. The `prior/*` sources and the
pack go to CP-8 only; no other module's request holds them. CP-8 is not in any preset and cannot be
selected with `--modules`. Its call is one more call under the same cap and holds; the offline cap check
sizes it with the rest. The run start summary passes the `_engine` folder as the workspace and returns
`changes` (and CP-8 in `modules`); the approval page shows a "Changes" row.

**`changes.json` (schema `cpos-changes/1`, computed by Python before CP-8 is called, given to CP-8 as the
source `changes.json`, published unchanged in the delivery).** Every number is a decimal string; missing is
null, never zero.
- `prior`: `{run, as_of, pathway, format: "current"|"earlier", methods_changed: [text]}`; `current`:
  `{as_of, pathway, format}`.
- `measures`: `{key, label, unit, comparable, reason, prior, current, difference}`; `prior` and `current`
  are `{label, unit, value, period, definition}` or null when a run does not state the measure. Measures:
  `leverage`, `net_leverage`, `coverage`, `cash`, `undrawn` (the CP-1 chart-table rows the library
  quotes) and `free_cash_flow`, `gross_debt`, `net_debt` (the one CP-1 table row of that label that states
  its unit, in the label's brackets or a `Reporting unit` column). `comparable` is false when a run does
  not state it or its label, unit or definition text (the table's "Basis and limitation", after
  normalisation) differs; `difference` is current minus prior in Decimal, null unless comparable with both
  values stated.
- `net_debt_bridge` (`unit, prior_net_debt, change_in_gross_debt, change_in_cash, current_net_debt`) and
  `maturity_profile` (`unit, rows[{period, prior, current, difference}]`) only when both runs support
  them; otherwise `omitted` holds a reason for each.
- `modules`: every module of either run, CP-8 excluded: `{module, title, ran_prior, ran_current,
  prior_bottom_line, current_bottom_line}` (first paragraph of `### Bottom line`, Basis line dropped; an
  earlier-format handoff: the Reader summary's Bottom line cell; else null).
- `limitations`: `{key, text, modules, prior, current}` per distinct normalised key (check 7's
  normalisation) over both runs' `### Limitations` items (earlier format: the Reader summary's "Main
  limitation"); a "No limitation changes ..." item is not a limitation.

**Method and check.** `src/deploy_vii/methods/cp8.md` is rewritten (M8): reader passages, then
`### What changed: the issuer`, `### What changed: the analysis` and `### Limitations ledger`. Two kinds of
change are never mixed; every row has one cause from `New period, New source, Method change, Correction,
Presentation, Unresolved` (issuer rows only the first, second and last; `Presentation` only with
`Unchanged`); analysis status `Unchanged, Strengthened, Weakened, Reversed, New, Not run this time`; ledger
status `Closed, Remaining, New, No longer stated` (M7). A removed limitation is `Closed` only when the row
names a current-run module that shows what closed it, else `No longer stated`. CP-8 never calculates:
`deploy_workflow.changes_check` refuses a handoff whose issuer-register figure is not a pack value (decimal,
sign aside; a whole number below 100 in the Effect cell is a count unless it carries a unit), whose
earlier or current cell differs from the pack's value for the measure it names, that gives a difference for
a not-comparable measure, that lacks or doubles a module row or a pack limitation's row, whose statuses
contradict the pack (the ledger status follows from which runs state the limitation), or that uses an
unlisted status or cause. A refusal is a targeted repair inside the existing attempt cap. The nine prose
checks and the reader-figure check apply as to every prose module.

Not decided here: charts and visuals for the Changes section (T5); CP-8's page name on the run page and in
the library still reads "Deliverable comparison" until that task renames both together.
