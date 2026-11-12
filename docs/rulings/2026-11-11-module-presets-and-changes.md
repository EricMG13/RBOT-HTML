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
