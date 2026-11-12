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

Decided, not yet built at the time of that change: M3 to M7; see the amendment of 2026-11-12 at the end.

## Amendment 2026-11-12: M5, M7 and the CP-8 half of M8 built (engine and method; no paid call)

Built on `claude/cp8-changes`. The old route that compares two delivered bundles
(`cpos.run_comparison`) is untouched; this is the in-run route. The library's Changes section is a later
task and reads the data contract below.

**Prior-run rule (one function, `deploy_workflow.changes.find_prior`).** Among the runs the issuer
library lists (`library_index.admit_run`: completed, every module answered in its own run; earlier-format
and earlier-methods runs included), a candidate has the same issuer ID (compared without regard to case),
the same pathway, the same case kind, an issuer name equal after case and whitespace folding, and an as-of
date on or before this run's, and is not this run's own folder. A candidate that fails the name or the case
kind is never used and the reason is recorded once (`changes: ... (not used: <run>: <reason>)`). A run
launched with an explicit module subset is not a comparison base: the manifest records
`selection: "preset"|"explicit"` (omitted for a manifest that predates it, which stays byte-identical); an
older run without it is a base only if it delivered its pathway's lead module (CP-2; CP-1B for an earnings
update; CP-L10 for a short snapshot). Every delivered handoff of the chosen run is checked as readable UTF-8
when it is pinned; an unreadable one means no CP-8 and the reason is recorded. The latest candidate is chosen
by (as-of date, first model-call start, folder name). None: CP-8 is not planned and the run records
`changes: first run of this pathway`. A run folder outside a `runs` folder searches nothing and records
`changes: not compared: ...`. Otherwise `prepare` plans CP-8 last (registry fan-in, as CP-5's) and copies the
prior run's delivered handoffs, CP-8 excluded, into `<run>/prior/<module>.md`, pinned as sources with their
hashes. The prior run's folder is read, never written. A run folder that already holds `workflow.json` keeps
the pins it records: a newer completed run cannot change the manifest and get the relaunch refused. The
`prior/*` sources and the pack go to CP-8 only; no other module's request holds them. CP-8 is not in any
preset and cannot be selected with `--modules`.

**The approval binds the earlier run.** The run start summary names what CP-8 compares with (the run's id,
as-of date and pathway, or "first run") and returns it with `changes` (and CP-8 in `modules`); the approval
page shows a "Changes" row. That choice is folded into the digest the approval carries (`issued` keeps it
beside the digest) and into the run record (`Record.prior`); the service starts the launcher with
`--prior <run folder>` or `--prior none` and the launcher uses exactly that run. If the named run is no
longer listed, or no longer passes the tests above, the run proceeds without CP-8 and records
`changes: not compared: the earlier run named at approval is no longer available`. A launch from the command
line without the flag searches as before. (The run page's "start from an earlier run", `?from=`, only copies
documents and answers and carries no run id; it is not used for this.)

**The cap and CP-8.** CP-8's call is one more call under the same cap and holds. The offline check sizes it on
its real first request: the loop inlines this run's handoffs, which are not written yet, so the earlier run's
handoff of the same module stands in for each (the mean of the earlier handoffs for a module that run lacks),
plus the instructions and a fixed allowance; the note names the figure as an estimate. If that hold does not
fit the cap, or the estimate is over the model's context, the run is planned without CP-8 and `prepare` says
so (`changes: not compared: CP-8's first request ... over the cap ...; the run is planned without CP-8`); a
resumed run folder is refused instead. (CP-5's offline hold is still sized on its instructions alone; that
predates this work and is not changed here.)

**CP-8 is optional to completion (the one fail-open).** If CP-8 is not accepted within its bounds, or its
call does not fit the cap, or the pack cannot be built from the handoffs, the run delivers without CP-8 and
records `changes: not produced \u2014 <reason>` in the completion record, a `changes_not_produced` run event,
the delivery manifest's `changes_note` and stderr, and the delivery's scope says so. Another module's failure,
and any other fault of CP-8's call (a provider stop, an overrun, an interrupted or already started call),
still stops the run. A relaunch of such a run folder leaves the delivery as it is, makes no new call and
says so.

**`changes.json` (schema `cpos-changes/2`, computed by Python before CP-8 is called, given to CP-8 as the
source `changes.json`, published unchanged in the delivery).** Every number is a decimal string; missing is
null, never zero.
- `prior`: `{run, as_of, pathway, format: "current"|"earlier", methods_changed: [text]}`; `current`:
  `{as_of, pathway, format}`.
- `measures`: `{key, label, unit, comparable, reason, prior, current, difference}`; `prior` and `current`
  are `{label, unit, value, period, definition}` or null when a run does not state the measure. Measures:
  `leverage`, `net_leverage`, `coverage`, `cash`, `undrawn` (the CP-1 chart-table rows the library
  quotes) and `free_cash_flow`, `gross_debt`, `net_debt` (the one CP-1 table row labelled `free cash flow` or `fcf`, `gross debt` or `total debt`, `net debt`,
  that states its unit; no synonym table is added, and a row that is absent is omitted with that as the
  reason). Python always computes `difference` (current minus prior, Decimal)
  when both values are stated and the units are equal. `comparable` is `"no"` when the units differ or a
  value or run is missing (no difference), `"yes"` when the label and the definition texts (the table's
  "Basis and limitation") are equal once digits, page and locator words and punctuation are removed, and
  otherwise `"judge"`: the difference is given, both definition texts are in the pack, and CP-8 writes for
  that row either `Same definition` or `Not comparable` with a reason; with `Not comparable` it prints no
  difference and draws no trend. The checker enforces this. Figures are read with a Unicode minus, a
  bracketed negative and a trailing `x` or `%`.
- `net_debt_change` (`unit, prior_net_debt, change_in_gross_debt, change_in_cash, current_net_debt,
  convention`): only when both runs state gross debt, net debt and cash in one unit under one definition and
  each run's net debt is its gross debt less its cash. An increase in cash reduces net debt. It compares two
  balances; it does not say what drove the change. A bridge by drivers (cash generated, acquisitions,
  distributions, new borrowing) is not built: it is valid only when the current run's reporting period
  equals the gap between the two runs, and the handoffs do not say so. `maturity_profile` (`unit,
  rows[{period, prior, current, difference}]`) from the table directly under CP-1's "Chart data: debt
  maturities" heading, only when both runs have one in one unit. `omitted` holds a reason for each of the two
  left out.
- `modules`: every module of either run, CP-8 excluded: `{module, title, ran_prior, ran_current,
  prior_bottom_line, current_bottom_line}` (first paragraph of `### Bottom line`, Basis line dropped; an
  earlier-format handoff: the Reader summary's Bottom line cell; else null).
- `limitations`: `{earlier: [{ref, module, text}], current: [{ref, module, text}]}` over both runs'
  `### Limitations` items (earlier format: the Reader summary's "Main limitation"; a "No limitation changes
  ..." item is not a limitation). Refs are `E1`, `E2` ... (earlier) and `C1`, `C2` ... (current), in module
  order then order in the handoff. CP-8 pairs them by meaning; Python does not.

**Method and check.** `src/deploy_vii/methods/cp8.md` is rewritten (M8): reader passages, then
`### What changed: the issuer`, `### What changed: the analysis` and `### Limitations ledger` (columns
`Earlier ref | Current ref | Limitation | Status | What closed it`). Two kinds of change are never mixed;
every row has one cause from `New period, New source, Method change, Correction, Presentation,
Unresolved` (issuer rows only the first, second and last; `Presentation` only with `Unchanged`); analysis
status `Unchanged, Strengthened, Weakened, Reversed, New, Not run this time`; ledger status `Closed,
Remaining, New, No longer stated` (M7). A removed limitation is `Closed` only when the row names a
current-run module that shows what closed it, else `No longer stated`. CP-8 never calculates:
`deploy_workflow.changes_check` refuses a handoff in which an issuer row whose Earlier or Current cell holds a
figure does not name a pack measure by its exact label (a row without figures is a fact row), a row that does
name one does not print that measure's value, sign and unit in the right column, a difference printed
anywhere (reader passages and `## Gaps` included) is not a pack difference or is written in the wrong
direction, a `judge` row says neither or both of `Same definition` and `Not comparable`, a `Not comparable`
row prints the difference or a trend, a module has no row or two, a limitation ref is in no row or in more
than one or in a sentence or a wrong column, a ledger status contradicts its refs, or a status or cause is
unlisted. Fix round 2 (2026-11-12): each measure also states `same_period` (computed by Python: both runs
name the same fiscal year) and each definition `definition_resolved` / `definition_written`: an `identical
definition` or `same measure` pointer is followed to the earlier period's basis in the same table, a pointer
by calculation ID is not. For a measure with `same_period` true and a non-zero difference the issuer did
not change: its issuer row must say `Not comparable`, or `Same definition` with the cause `Correction` or
`Method change` (issuer rows may then carry those two causes); `New period` and `New source` are refused.
The difference of a measure whose row says `Not comparable` (or the pack marks `no`) is printed nowhere,
and that of a same-period non-zero measure only in the register rows. (Round 2's sentence-level word
tests and its figure rule were replaced in round 3, below.) A year after an
instrument word (`notes 2027`, `due 2030`) is kept in the definition key. A ref in any case in a sentence
is refused. CP-8 is never the library's lead or summary module (`summary_fields`). Known limits, kept:
`Closed` evidence is checked for
presence of a current-run module, not for substance; issuer names must match exactly after case and
whitespace folding (the approval shows the reason when they do not). A refusal is a targeted repair inside
the existing attempt cap. Fix round 3 (2026-11-12, controller-approved after a root-cause investigation: round 2 policed the meaning of
free prose with sentence-level word lists, each leaky and each refusing correct sentences). The word lists
(`ALIASES`, the correction/restatement escape, the per-sentence trend test) are deleted; the check reads
structure, lists and numbers only. (a) `same_period` is `changes.same_period`: a period is `FY2024`,
`FY2024 / 2024-09-30` or `2024-09-30`; two dates are the same only if equal, otherwise only the same fiscal year
is; `H1 FY2024`, `LTM Q3 FY2024`, `FY2024 pro forma` are never the same as `FY2024`. (b) A figure written in
a checked line (all but Request, Sources, Calculations and Next module; of an issuer row the Effect cell) must
be held in the evidence: the pack's values, the figures of its definition texts, the handoffs CP-8 was sent
(`cp8_issues(text, pack, held)`, the caller passes this run's handoffs and the `prior/*.md` sources) and the earlier
run's; a rounded or worked-out figure and an unstated threshold are refused. (c) The difference of a measure
that is `no`, said `Not comparable`, or of one period with two values is printed in no checked line (a same-period
measure said `Same definition` may print it in register rows). (d) A fact row may carry figures a handoff states,
never a pack measure's value (`name a pack measure by its exact label`) nor any difference of the pack, in any cell including the label (a difference belongs to its measure's own row). Known limits, kept: a movement in words
for a withheld measure ("Leverage improved.") is not checked mechanically (the method text, the enforced register
row beside it and a human reader carry it); a held figure proves a number exists in the evidence, not what it
means (on the real pair "about 0.6x lower" passes because 0.6 is a weight in a current handoff); fact-row figures
are not tied to their column's run; `FY2024` against a bare date is treated as different; "56 basis points" is not
read as a figure; a `Same definition` row with a contradicting sentence is accepted.
The nine prose checks and the
reader-figure check apply as to every prose module. The module's display name, on the run page and in the
library, is "Changes since the last run".

Charts and visuals for the Changes section (T5): built, see the last amendment.

## Amendment 2026-11-12: M6 built (Short Credit Snapshot)

Owner approved 2026-11-11 ("3. approved"). Pathway id `short_snapshot`, label "Short Credit Snapshot",
modules CP-0, CP-1 and CP-L10 and nothing else (no CP-DR, CP-2E, CP-MODEL, CP-2G or CP-2). CP-8 is not
excluded: it runs last when an earlier run of the same issuer and `short_snapshot` pathway exists, as for
any pathway, and an older run without a recorded selection counts as a base only if it delivered CP-L10.
It is selectable on the run start page and context form and is one of the library's pathways; the six
other presets are unchanged.

**CP-L10 is rewritten** (`src/deploy_vii/methods/cpl10.md`), replacing the two-quarter change screen
(TL10.1 to TL10.5), whose Python owner is not run by CP-OS. It is a prose module: the four reader
passages, then `### Key figures`, exactly one table `Measure | Value | Period | Source` whose every figure
is copied exactly from CP-1's handoff (CP-L10 calculates nothing new; a figure CP-1 does not state is
`Not supplied: <reason>`, never zero), then the usual `## Sources`. It is one page: about 350 words of prose
and six to ten rows. CP-L10 owns one report block, `key-figures`. The launcher applies the same checks as
for any prose module (the nine prose checks and the fidelity check: a figure in a reader passage must be in
a table of the handoff with the same sign, unit and scale). Fix round 1: the launcher also refuses a Key figures table whose header is not exactly
`Measure | Value | Period | Source` or whose Value cell holds a figure the CP-1 handoff it was sent does not state
(same sign, unit and scale; `prose_checks.key_figures_issues`). Fix round 2: the sign must match exactly, exactly one table is allowed under the heading, and a missing CP-1 handoff is a refusal, not a skip.
Known limits: a figure is proven to exist in
CP-1, not that it is the right measure or period; a unit CP-1 carries only in a column header (`Reporting unit`) is not matched, so a bare CP-1 `3.1` accepts `3.1x`, because CP-1's own tables write plain numbers with a separate unit column; that rests on the reader's check of a real run.
CP-L10 leads the Overview of a short snapshot (amendment to H5 in
`2026-11-11-reader-and-issuer-report.md`). The library names the pathway "Short credit snapshot".

## Amendment 2026-11-12: built, and the seams the whole-branch review found

Built: M1 and M2 presets (#49), the layer-1 forecast of M3 (#50), web search of M4 (#51), CP-8 with its
checker and pack, M5 and M7 (#55), the Changes tab, the issuer library's page for M8 (#56), and the Short
Credit Snapshot, M6 (#57). Two departures from M8 part 5 as built: Over time lists runs of the same
pathway only, not every run of the issuer; its lead line is the lead module's bottom line, not a committee
conclusion.

Whole-branch review fixes (branch claude/changes-seams): (1) one reading of CP-8's registers. The checker
(`changes_check`) now accepts only the forms the tab reads: a verdict word (`Same definition`, `Not
comparable`) starts a cell of the issuer row (the word elsewhere in the row is refused, except for a measure
the pack marks `no`), the issuer row's label is the pack's label exactly (bold or code marks aside), and the
Module cell of the analysis register ends with the code in brackets, as `Credit view (CP-2)`.
`tests/fixtures/changes-seam/rows.json` is read by a Python test and a node test with the same expected
verdicts. When the tab cannot read a verdict it shows no difference and no line. (2) Over time compares
the run folder name on both sides (the pack names its prior by folder). (3) A reason the run records for
making no comparison reaches the library verbatim. (4) The published scope no longer says CP-8's handoff is
delivered whole when CP-8 was not produced.

Known limits, recorded (owner decision pending on the first): four pathways (relative_value,
distressed_restructuring, portfolio_decision, short_snapshot) never ask CP-1 for the chart tables the pack
reads (`cpos_launch.py` layout rule), so their pack states no measure and their Changes tab says so; the
layout rule is unchanged. L4: `find_prior` accepts any listed run folder name, including one the launcher
refuses at launch (a space, a leading underscore, non-ASCII); that fails closed with no spend. L5: the
forecast inputs block can vouch for a Key figure when only CP-0, CP-1, CP-MODEL and CP-L10 run.
