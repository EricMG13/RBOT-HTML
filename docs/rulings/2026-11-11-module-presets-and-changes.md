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

Superseded for new runs: the short-snapshot part (M6) by `2026-11-13-full-and-lite-credit-assessments.md`.

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

**`changes.json` (schema `cpos-changes/3`, computed by Python before CP-8 is called, given to CP-8 as the
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
verdicts. A measure the pack marks `no`, and a row that begins with `Not comparable`, shows both values and no difference and no line. A `judge` measure with no verdict word shows no difference ("Comparability not judged"). A `yes` measure with no verdict word shows its difference and its line, as the pack states it. (2) Over time compares
the run folder name on both sides (the pack names its prior by folder). (3) A reason the run records for
making no comparison reaches the library verbatim. (4) The published scope no longer says CP-8's handoff is
delivered whole when CP-8 was not produced.

Known limits, recorded: the chart-tables limit (the whole-branch review's finding) is closed by the amendment of 2026-11-12 below. L4: `find_prior` accepts any listed run folder name, including one the launcher
refuses at launch (a space, a leading underscore, non-ASCII); that fails closed with no spend. L5: the
forecast inputs block can vouch for a Key figure when only CP-0, CP-1, CP-MODEL and CP-L10 run.

## Amendment 2026-11-12: one reader of CP-8's registers (branch claude/changes-seams, round 3)

Two earlier rounds aligned the checker and the page rule by rule and each left a divergence, so the page no
longer reads a register for a verdict. `changes_check.page_verdicts` derives, with the checker's own reading
of the registers, a verdict per pack measure, the module rows that have exactly one row, and the ledger
counts; `update_library.changes_data` carries them as `run.changes.verdicts` (null without a pack, with a
note or a problem); `changes.js` displays them: only a `comparable` verdict shows a difference or a line, and
a missing entry, an unknown kind or `verdicts: null` shows both values and neither. A fact row whose label,
after NFKC, with only letters and digits kept and case folded, equals a pack label is refused (a hidden
character cannot leave a `Not comparable` row beside a difference). Delivery computes nothing.

Known limits, recorded: (1) the verbatim register tables are still split by the store's parser, so a row
without its closing pipe, or a second table, stays visible as text although it counts for no verdict. (2) Old
handoffs are re-read only through the checker's per-row rules; their passages are not re-checked against
K9 and K10. (3) A malformed issuer register counts as having no rows, so a measure the pack marks `yes`
still shows the pack's difference.

## Amendment 2026-11-12: every pathway asks CP-1 for the chart tables (owner: "Yes, all pathways")

Asked whether all pathways should ask CP-1 for the chart tables the Changes tab needs, the owner answered
"Yes, all pathways". Until then CP-1 was asked for the four `### Chart data:` tables (leverage, interest cover,
liquidity, debt maturities) only where the pathway's report had the chart blocks: credit_snapshot asked for
all four, earnings_update lacked debt maturities, covenant_refinancing had only debt maturities, and
relative_value, distressed_restructuring, portfolio_decision and short_snapshot had none, so their pack
stated no measure. Now `cpos_launch._owner_tables` asks CP-1, on every pathway, for each of the four tables
its report routes do not already carry, as owner tables (header, plain-number and unit checks identical to
the routed ones; the checker refuses a handoff without them). No report section is added: those tables are
read by the library and the pack, not delivered. CP-1's output grows on those pathways; the USD 20 cap check
admits every preset (largest single hold unchanged; short_snapshot's hold rises from 0.97 to 0.99 on the Opus configs).

## Amendment 2026-11-12: four defects found by reading the first real CP-8 run (branch `claude/changes-real-run-fixes`)

The first real CP-8 (`tdg-proof-snapshot-opus-002`, credit_snapshot on opus-medium, compared with
`tdg-reader-format-001`; recorded in `2026-11-12-credit-snapshot-claude-rerun.md`) was accepted, and reading
it showed four defects. Controller rulings, each implemented with a failing test first:

- **D1, pipeline file names in reader passages.** CP-8's Basis lines read `Basis: changes.json; prior/CP-1.md,
  page 4`. In CP-8's reader passages a Basis item for the comparison pack is exactly `Run comparison`, and for
  a handoff of the earlier run `<plain module name> (<code>), earlier run`, for example `Financial data
  foundation (CP-1), earlier run`; no page number for a handoff. `changes_check` refuses `changes.json`, a
  `prior/` name, a page on a handoff, and `Run comparison` with anything after it, in a CP-8 Basis line only;
  the library's Basis reader (`credit_os_chips.basis_locators`) reads the two forms as items with nothing to
  open instead of a "Basis item not recognised" gap. `## Sources` still lists the real file names and hashes.
  The method (`cp8.md`, "Basis lines") states the forms.
- **D2, an unchanged measure read as a problem.** Every measure with a zero difference carried the cause
  `Unresolved`. An issuer row for a measure whose pack difference is zero, and that is not said `Not
  comparable`, now has the cause `None` and `Unresolved` is refused for it; `None` stays refused for a
  non-zero difference. The library prints CP-8's register verbatim, so `None` shows as written;
  `page_verdicts` does not read the cause of a zero-difference row.
- **D3, "gross debt is not stated in either run".** Both CP-1 handoffs do state gross debt (current: USD 25,068
  million at 2024-09-30), but under labels the pack's exact row rule does not read: the earlier run writes
  `Gross financial debt including finance leases and securitization` with its unit only in a `Unit and quantity
  / status` column text (`USD million; ...`); the current run writes `Total debt (gross, incl.
  securitization), USD m` with the unit after a comma, not in brackets. The rule reads a row labelled exactly
  `Gross debt` or `Total debt` (also `Net debt`, `Free cash flow`) with the unit in brackets after the label
  or in a `Reporting unit` column; the two layouts differ from each other and neither fits, so no exact rule
  reads both and none was added. The reason the pack gives is now true: "gross debt is not read from either
  run's CP-1 (the comparison reads only a table row labelled exactly ...)". Even when read, the two runs'
  basis texts differ, so the pack would mark gross debt `judge` and the net debt change would still be left out
  (it needs `yes`). What CP-1 states for it is set by the 2026-11-12 amendment below (`### Net debt data`).
- **D4, new modules marked `Unresolved`.** The pack (schema now `cpos-changes/3`; the library reads `/2` and
  `/3`) states each run's `selection` (`preset`, `explicit` or null) in `prior` and `current`; a prior run's
  selection is read from its manifest. When a module is `New` or `Not run this time` and both selections are
  `preset` (the prior's may also be null: a run whose manifest predates the field was accepted as a base only
  because it ran the pathway's lead module, so it is a whole-pathway run; the pack states null as recorded),
  the pathway's module set changed between the runs: the cause must be `Method change`, and the words "the
  pack does not say" are refused. With either run an explicit subset, or a pack of the `/2` shape (no
  `selection` key), nothing is required and the cause is `Unresolved` as before. The real earlier run
  (`tdg-reader-format-001`) records no selection: the first version of this rule skipped it (the real CP-8
  was refused 6 times, its four New rows accepted); with it, 14 times (4 D2, 8 D4, 2 D1).

The CP-8 instruction text itself states the Basis forms (`cpos_launch.CP8_BLOCK`, one place; the real draft
had followed the general rule that lists only file names), and the library reads the two CP-8 forms only in
a CP-8 handoff, exactly (`Run comparison`; a plain name with a registered module code, `, earlier run`).

Known limits, recorded, not in this change: pack values print as the handoffs state them (`6261 US$m`, a date in
one run and `FY2024` in the other); CP-DR's web guidance is unproven on Claude; a CP-8 `## Gaps` row may still
say the pack does not say why the earlier run selected fewer modules (the checker reads registers, not gaps);
Free cash flow and net debt are not read from the real CP-1s for the same label reason as gross debt.

## Amendment, 2026-11-12 (owner: "Yes, add it"): CP-1 states gross debt in a table the pack reads

Asked "Have CP-1 state gross debt in a fixed-label row so the net debt change can be shown?", the owner
answered "Yes, add it". The `Gross debt` row cannot sit in an existing chart table: the four are period-row
tables (`Period | <measures> | Reporting unit | Basis and limitation`, cash is a column), the pack's row reader
needs periods across a header, and a gross debt column in the liquidity table would be drawn beside cash on one
axis. The net debt change also needs net debt, not only gross debt. Controller ruling: a fifth small period-row
table on every pathway, with the mechanisms that already exist and no new layout.

- `### Net debt data` (not a `Chart data:` heading, so the library does not draw it, the report does not route it,
  and the library lists it as a reference table under the CP-1 findings). Header `| Period | Gross debt | Cash |
  Net debt | Reporting unit | Basis and limitation |`, US$m, one row per period stated (at least the latest
  balance-sheet date); `Not supplied: <reason>` in a cell as in the other tables. Gross debt is the total debt
  principal as the issuer reports it, and the Basis cell says what it includes (securitization, finance leases):
  that is the definition text the pack carries for comparability. Cash is the liquidity table's figure; net debt is
  gross debt less cash, worked with `calculate`, listed in `## Calculations`.
- The checker adds two rules, named in the instructions: with all three figures stated a row must satisfy net debt =
  gross debt - cash exactly (in Decimal), and a stated cash must equal the Cash of every liquidity row that `same_period`
  (changes.py) calls the same period (`FY2024` and `FY2024 / 2024-09-30` are one period; `2024-09-30` and
  `FY2024` are not).
  A missing table or a wrong header is refused as for the other tables.
- The pack reads `gross_debt`, `net_debt` and, for the net debt change, the table's own Cash column, all from
  one run's latest row of this table, with the period-row reader that reads the chart tables (the liquidity
  table is not read for the change); the exact-label row rule of #66 now reads only `free_cash_flow`. A run without the
  table (every earlier run) states no gross or net debt: the net debt change is left out and `omitted` names
  the run ("gross debt cannot be compared (the earlier run does not state it)"). Older runs stay usable as a CP-8
  base and render as before. The pack computes nothing new.
- Free cash flow is not part of this change. To be read it needs one row labelled exactly `Free cash flow` (or `FCF`)
  with its unit in brackets or a `Reporting unit` column, in a table with periods across a header, and the same
  basis text in both runs.
- Recorded, no code: the library tab shows the net debt change's cash movement without its periods beside the
  liquidity measure. (Done 2026-11-12, see the amendment below.)

Amendment, 2026-11-12 (owner: asked "Flag a same-period net debt restatement as the analysis changing, not the
issuer?", the owner answered "Yes, fix it"). `net_debt_change` carries `same_period` (true when the gross debt, net
debt and cash measures are), the two rows' periods and their stated gross debt and cash (`prior_period`,
`current_period`, `prior_gross_debt`, `prior_cash`, `current_gross_debt`, `current_cash`); read, not computed. The
schema stays `cpos-changes/3`: the keys are additive and a reader ignores keys it does not know; a pack without them
renders and checks as before. The checker withholds the change's differences (gross debt, cash, net debt) from
CP-8's checked lines by K9's own mechanism: gross debt and net debt are measures already; the cash difference is
given to the same functions as a measure-shaped record, so the same exceptions apply. The tab, for a flagged change
with a non-zero difference, shows both runs' balances with periods and "Both runs state net debt for the same date;
the difference is between the two analyses, not a change in the issuer." with no change figure; it also prints the
periods beside the change's cash movement. `cp8.md` states the rule.

Amendment, 2026-11-12 (owner: asked "Close the gap that lets a withheld difference be written in CP-8's Why cell?",
the owner answered "fine, PR and merge"). K9's "register rows" exemption (round 3 (c) above, and the 2026-11-12
net debt amendment's "same exceptions") meant the issuer register row of the same measure; it is narrowed to that.
The only cell that may print a withheld difference is the Effect cell of a pack measure's own issuer row, when the
measure is of one period with two values and its row says `Same definition` with the cause `Correction` or
`Method change`. The analysis register's Why cells, the ledger's cells, fact rows and another measure's row refuse
it, naming the figure and the word "difference"; the net debt change's cash, which has no issuer row, is printed
nowhere. A size equal to a value of the measure itself stays accepted. Same functions (`_withheld_sizes`), per-line
exemption (`_may_print`). `cp8.md` states the rule.

Amendment, 2026-11-12 (owner: asked "Fix the two remaining checker gaps in one small follow-up?", the owner
answered "Yes, fix both"). (A) K9 also refuses a withheld difference written without a unit: a whole number below 100
is a count everywhere but here, and for the withheld-difference rule only a bare number equal in magnitude to a
withheld size is refused, on the same lines and with the same exemptions (the measure's own issuer row under its
condition; a size equal to one of the measure's own values). Counts under K10 are unchanged; for the bare-number reading only, module codes, the number of a line that really
begins a list item (the first line, or after a blank line, a heading or a list item; never a table cell or a line that
continues a paragraph) and a one- or two-digit day beside a month name are not read as numbers. Limits, recorded: a legitimate bare count equal to a withheld size ("30
limitations" while a difference of 30 is withheld) is refused and must be reworded (the message names the figure, the
measure and the word "difference"); a size written in words ("thirty") was not read (closed by the amendment
below). (B) The verdict words `Same
definition` and `Not comparable` are read from the start of the Effect cell only, by the checker and by
`page_verdicts` alike (`_says`); the same words starting another cell of the measure's row are refused, naming the
cell, not ignored. Unchanged: for a measure the pack marks `no`, `Not comparable` is accepted anywhere in its row.
The shared fixture `tests/fixtures/changes-seam/rows.json` gains five cases; no existing case changed.

Amendment, 2026-11-12 (owner: "Fix the limits first"; controller rulings L1 to L4). (L1) After a bulleted item line a
leading number is a list marker only if it is `1` (CommonMark: a list not starting at 1 cannot interrupt a
paragraph), so a hard-wrapped `- Cash fell by` / `30. The rest holds.` is read as a figure; after a blank line, a
heading, the first line or a numbered item the earlier rule stands. (L2) A day beside a month name is a date only when
a four-digit year completes it (`30 September 2024`, `30th Sep 2024`, `September 30 2024`, `Sep 30, 2024`); a day and
month with no year is a number, so "The period ends 30 September." with 30 withheld is refused (accepted cost: reword).
(L3) A complete date is blanked from the line before both readings (the raw K9/K10 reading and the bare reading);
`_FIGURE` is unchanged, so `September 30, 2024` no longer reads `30,`, and an unheld figure on a line that also holds a
date is still refused by K10. (L4) In the bare-number K9 reading only, whole numbers from two to 999,999 in English
words (`thirty`, `one hundred and sixty-three`, `two thousand five`; hyphenated or spaced, any case) are read as the
number they spell, with the same exemptions and message; `one` alone is never read. Remaining limits, recorded: a
legitimate bare count (or a spelled one) equal to a withheld size is refused, since the checker cannot tell a count
from a size; decimals, fractions, ordinals (`thirtieth`), `a hundred` and `a dozen` in words are not read. The two
tests that pinned the old limits (a size in words accepted; `- First point.` then `80. ...` accepted) now assert the
new rulings; no other expectation and no `rows.json` case changed.

Amendment, 2026-11-12 (reviewer findings M1, Low A, Low B). A date's year is `(?:19|20)\d{2}` only, as `_EXEMPT` has it, so
a figure such as `4370` or `1006` straight after a yearless `30 June` is read again. A spelled number is not read when it
directly follows or precedes `point`, or is directly followed (space or hyphen) by an ordinal or fraction word (`first`,
`thirty-first`, `thirds`, `quarters`, `-th`/`-ieth` forms, also after `and`: `one hundred and first`) or by `and a half` /
`and a quarter`. U+2010 to U+2015 count as a hyphen inside a spelled number. Remaining limits: a spelled size broken across
lines (`one hundred` / `and ten`) is not read; a legitimate count equal to a withheld size is refused.
Narrowed (controller rulings, same day): `and` plus an ordinal exempts only a number containing `hundred` or `thousand`;
an ordinal or fraction word hyphen-joined to a following word (`second-lien`, `quarter-on-quarter`) is not an ordinal;
`point` exempts a number only inside number-word `point` number-word (`zero point five`), so `At that point thirty`,
`a thirty-point swing` and a bare `point five` are read (accepted false refusal); `and a half` / `and a quarter` exempt
only when not followed by `of`; `two halves` is not read. When in doubt the number is read.

Amendment, 2026-11-12 (owner: "fix 1 and 2"; controller rulings R1 to R3). (R1) A 19xx/20xx number is a year, not a
figure, in K9 and K10 unless it is a figure by the rules for any number: a currency directly before it (`US$2010m`,
`USD 1913`), a decimal part or thousands separator, a scale or unit directly after it (`2010m`, `2010%`, `1913 million`,
`2010 US$m`, `2010 USDm`). It stays a year when the currency after it is directly followed by a number (that currency is
the next number's: `September 2024 US$4,216 million`), in a table header row (the row above a `| --- |` separator:
`| 2024 / 2023 US$m |` reads nothing; a body row or Effect cell holding `2010 US$m` is a figure), after a month name or a
period marker (`September 2024`, `FY 2024`, `Q3 2024`, `H1 2025`, `fiscal 2024`, `LTM 2024`), and when bare. A currency
code before or after a year is only one of a fixed list (USD, EUR, GBP and similar), so `AND 2023` is no currency.
Held evidence is read the same way, line by line. (R2) In the bare-number K9 reading only (digits and words) a number is
a count when directly followed by a count noun (module, run, measure, source, period, row, item, document, filing, page,
section, table, finding, limitation, assumption, conclusion, handoff, issuer, lender, facility,
tranche, covenant, subsidiary, quarter, month, year, week, day; singular or plural, not hyphen-joined to a further word)
or directly after page, note, section, table, row, item, step or appendix. No pack measure's unit is one of the nouns.
`Cash fell by 30 days` is accepted: `days` is a count noun and no pack measure is measured in days; a unit of the pack
(`30 US$m`) is refused as before. (R3) In the words reading, a spelled number that a paragraph line leaves unfinished and
the next line of the same paragraph continues (`one hundred` / `and ten`) is read joined and reported once; a blank line,
heading, table row or list item between is no join. Remaining limits, recorded: a bare 19xx/20xx number is always a
year (period labels are mandatory, so a bare year is never refused); in prose a list of years sharing one unit
(`2024 / 2023 US$m` outside a header row) is refused, so reword it or put it in a table header; a count with an
adjective before its noun (`30 new modules`), a count noun outside the list, and `times`, `points`, `percent` are
refused; a whole count of 100 or more beside a count noun is still refused by the raw reading (it takes a number of 100 or
more without a unit). The one existing case that
pinned the count limit (`The handoff states 30 limitations.`) now asserts acceptance; no `rows.json` case changed.

Amendment, 2026-11-12 (reviewer findings H1, M1, M2, L1 to L3; controller rulings). (H1) A comma is part of a number only
as a thousands separator (followed by exactly three digits); a 19xx/20xx number before any other comma (`In 2024, the
issuer`, `2023, 2024 and 2025`) is a bare year, in prose, rows, header rows and held evidence (`September 19, 2024,` holds
no 2024). (M1) An ISO date (`YYYY-MM`, `YYYY-MM-DD`) is exempt as a whole, also after a period marker or month name (`Q3
2024-09-30`). (M2) `change` and `difference` are not count nouns: `a 30 difference` and `a thirty change` are refused
again. (L1) A count noun that starts the next line of the same paragraph counts (`thirty` / `modules`); the old limit is
removed. (L2) A table separator row without outer pipes (`--- | ---`) marks the header row above it. (L3) A currency code
after a year is a unit only with a scale after it (`2010 USDm`, `2010 USD million`) or a number (`2025 USD 30,199`):
`In 2024 USD strengthened` reads no figure.
Amendment, 2026-11-12 (fix round 2). (M-A) The scale after a currency code or symbol, with or without a space, is any of
million(s), billion(s), thousand(s), `mn`, `bn`, `m`, `k` (words case-insensitive), so `2010 USD millions` and `2010 US$ million` are figures. (L-A1) The ISO
exemption (`YYYY-MM`, `YYYY-MM-DD`) matches only when its last two digits are not followed by another digit: `September 2024-437` reads 437, and `2025-2045` reads
two years (the 45 once read from `2025-2045` was a fragment, not a figure). Limit: a two-digit number written directly after a year and a hyphen (`FY 2024-30 US$m`) is read as a year range and hides the 30. (L-B) A table separator row
needs at least three dashes in every cell (colons allowed); no real separator row in the retained runs has fewer.

Amendment, 2026-11-12 (fix round 3). One unit test decides whether a 19xx/20xx number is a year or a figure (`_YEAR_UNIT`),
separate from the small-number test (`_UNITED`), so a boundary fixed for one no longer moves the other. A unit must end before a
letter, a digit or `&`, and before a hyphen or slash followed by a letter (`2024 m&a`, `2024 k-shaped`, `2024 m/m` stay years). A
plural scale word (`millions`) counts only after a currency (`2010 USD millions`); alone it is a year (`In 2024 millions of
customers`, and `2010 millions`, which the round-2 test had listed as a figure and is moved). The duplicate `_UNITS` name is gone,
so `mypy --strict` reports no error in the file. Recorded limit: a unit directly followed by a hyphenated word or a
superscript footnote mark (`2010 US$m-equivalent`, `2010 USD million-plus`, `2010 US$m¹`) is not read as a unit, so that
year-shaped number stays a year.
Amendment, 2026-11-12 (owner: "complete 1"; controller rulings C1 to C3). (C1) Digits directly after a currency code of `_CODES`, when the code follows no letter, digit or dot, are a figure carrying that currency (`EUR437m`, `USD2010m`, `USD437`); `XEUR437`, `ABC123`, `FY2024`, `USD-denominated` read as before. A 19xx/20xx number so placed is a figure. (C2) A currency sign may carry a one- to three-letter prefix (`C$`, `A$`, `R$`, `HK$`) in the year rules; `mln` and `bln` are scales wherever `mn` and `bn` are, and `'000` (also `’000`) is a scale after a currency (`2010 C$m`, `2010 USD mln`, `2010 USD '000`, `2010 mln` are figures); `_UNITED` takes `mln` and `bln` so `30 mln` is a figure and no count. `_CODES` now holds the 40 codes USD EUR GBP JPY CHF CAD AUD NZD SEK NOK DKK PLN CZK HUF TRY ZAR BRL MXN CNY CNH HKD SGD INR KRW TWD THB IDR MYR PHP SAR AED QAR KWD ILS EGP NGN CLP COP PEN ARS (it held 22 before). A currency after a year still belongs to the next number (`2024 SAR 5,000` reads 5,000). (C3) A 19xx/20xx number directly followed by `s` and then no letter or digit (`EUR 2029s, 480bp`, `the 2031s`) is a bond or decade name, a year in every reading; `2029 s` and `2029secured` are unchanged. Limits that remain: a small number after a one-letter-prefixed sign (`30 C$m`) is not read as carrying a unit; a code before digits that is really a name (`COP26` after a space) is read as a currency amount.

## Amendment 2026-11-13: prompt-first redesign of CP-8 and the forecast inputs

Owner, 2026-11-13: "all three. remove all the code no longer required if resolved by the prompt." The
controller's answers below (E1 to E12 of the plan `redesign/PLAN.md`) rest on that instruction. Each states what
it supersedes. This amendment is text only; the packages that build it follow it. It authorises no paid call.

- E1 (controller). `Method change` is required for a `New` or `Not run this time` module only when the pack
  records `preset` for both runs. When the earlier run's selection is null, `Method change` or `Unresolved` is
  accepted and any other cause is refused. When either selection is `explicit` the cause is `Unresolved`, as
  before. This supersedes the controller ruling of 2026-11-12 in D4 above, that a null earlier selection counts as
  `preset` (the plan calls it K12). Reason: 36 of 42 retained manifests record no selection, explicit subsets
  among them, so null is not evidence of a preset. The ban on the words "the pack does not say" is dropped with
  it; the Cause list is the rule.
- E2 (controller). On a `Same definition` row with cause `Correction`, the row's own permission to print its
  difference wins over "the net-debt-change cash difference is printed nowhere", on that row only, when the two
  differences are the same number. Elsewhere the size stays withheld.
- E3 (controller, under the owner's instruction). The spelled-number reading is replaced by the instruction (write
  every amount, ratio and difference in digits with its unit; a number word is only for a count of things) plus
  one short form check, W. W runs only when a difference is withheld. It refuses a number word followed by a
  scale, percent, basis-point, `x` or currency word, or preceded by a direction word (with an optional `by` and
  an optional `about`, `roughly` or `nearly`); `times` is not in its list. This supersedes L4 of the amendment
  "Fix the limits first" (2026-11-12), which ordered spelled numbers to be read, and the words reading of the
  2026-11-12 count-noun amendment (R3). Numbered lists and hard-wrapped paragraphs are no longer tolerated by
  the checker: the method says to write `-` bullets and one line per paragraph, item and row; a list number
  equal to a withheld size is refused by the bare reading. Residual limit, recorded: a withheld size written in
  words with neither a unit nor a direction word ("the gap is thirty") passes; the earlier grammar caught it and W
  does not. No retained model-written handoff writes an amount in words.
- E4 (controller). Accepted: exact value cells built from the pack, the Basis whitelist, the `column` key refused,
  `currency` required with `scale`, and the `Net debt data` Period form. Each refusal states the exact text to
  write. The proof run counts first-attempt refusals per form; a form refused more than once is reconsidered, and
  no check is loosened to pass.
- E5 (controller). The Period check applies to `Net debt data` only, not to the leverage, interest-cover and
  liquidity chart tables. Decide again after the proof run.
- E6 (controller). Three reviewer probes cannot flip under this plan and are superseded by the hand-written keys
  in section D of the plan: `probe_cp8.py` P3 (a calculation ID stays refused; the key is the reworded message
  "describe the calculation in words"), `g70/p2_gbp_caption.py` (keyed on a `## Request` phrase that 0 of 38 real
  CP-1 handoffs print; the key is the `currency` test) and `g50/probe_split_tables.py` (demands a value Python
  cannot derive from split tables; the key is the withheld amount with the reason "needs ..., which the table
  holding the named row does not print"). The probes are not edited. This is a recorded exception to "the
  reviewer's probe is the answer key", not a silent one.
- E8 (controller). Accepted, as recorded for PR 76 and the named-rows change: relaunching a run delivered since
  PR 76 whose block names `column`, whose CP-1 has an `LTM Qn YYYY` label, or whose history holds a reworded gap
  reason re-derives a different delivery id. The owner has not said whether the LTH run `20261112-164724-01`
  matters; each package reports whether its change would alter that run's delivery id if the run is reachable, and
  does not touch it.
- E9 (controller). The forecast deletions (the `LTM Qn YYYY` balance path, then the `column` path and per-row
  unit) go ahead in the plan's order, before the proof run, although neither the deleted paths nor the
  replacement instruction has been used by a model. Revert rule: if the proof run's Forecast page shows no
  fiscal-year cash or debt because CP-1 printed balances only in period-row tables, the `column` deletion is
  reverted in one pull request rather than a check loosened.
- E10 (controller). Accepted: runs holding a CP-8 handoff show "Earlier methods" once the CP-8 method text
  changes. It is true.
- E11 (controller). Accepted: deleting the trend word list means a `Not comparable` reason that says "leverage
  rose" with no size passes. No figure is exposed, the method forbids describing movement, and the list refused a
  compliant sentence ("so no trend is drawn") in a real run. The withheld-difference rule still refuses any size.
- E12 (controller). Agreed: these stay in code: a single strict unit cell (the per-row unit reader stays in the
  reading of CP-1 text), facility terms, the Source type cell, date blanking, count nouns, and the Lows the plan
  lists. Each protects a value, period or unit on text the prompted model does not write, or would need the
  parsing it replaces.

Recorded scope: the first real CP-8 (`tdg-proof-snapshot-opus-002`) is the only retained model-written CP-8
after PR 66; every form above is unproven at first attempt until the proof run, and the plan lists what no
retained run demonstrates.

## Amendment, 2026-11-13 (controller, after review)

Four of the records above differ from what was built. The original text stands; this states what was built.

- E3 as built. Check W refuses a number written in words only when a listed unit word directly follows it
  (`thirty million`, `two hundred bps`). The direction-word half described in E3 was built, found in review to
  refuse counts the method allows ("added four new modules") while missing most wordings, and deleted (PR 89).
  Residual limit: any other wording of a withheld size in words passes; the method text, not the checker, keeps
  amounts in digits.
- E9 as built. The `LTM Qn YYYY` balance path was deleted (PR 90). The deletion of the `column` path and the
  per-row unit reader, which E9 places "before the proof run", was NOT made before it: the wrong-scale unit check
  is reachable only through that path and no model has been shown the new instruction, so only the instruction
  changed (PR 91: operands named by `row` and `period`). Decided by the controller on 2026-11-13 under the
  owner's instruction of the same day; the owner may order the deletion at any time. It is to be decided after the
  proof run shows how balances are printed.
- Basis names (not in the original list). No exact-name rule was first built because the model's own names in
  retained handoffs differ from the registry titles; a deny-list was used (PR 87), then the listed name from
  `MODULE_NAMES` was accepted outright after the whole-branch review found the deny-list refused
  `Rates, FX & hedging`.
- Forecast currency (not in the original list). The planned comparison of the block's `currency` with unit cells
  was replaced in review by a presence rule: the stated currency must be named somewhere in the Financial
  foundation handoff, because real handoffs state units in headings (PR 88).
