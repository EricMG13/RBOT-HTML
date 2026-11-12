# CP-8 — what has changed since the last time I looked at this

Selected authority: the owner's ruling of 2026-11-11 and its amendment of 2026-11-12
(`docs/rulings/2026-11-11-module-presets-and-changes.md`, decisions M5, M7 and M8). This replaces the
2026-11-04 deliverable comparison. The imported investment-decision post-mortem remains superseded;
its source is retained as evidence at docs/reuse/legacy-cp8-decision-ledger.md.

CP-8 runs last, in a run for which CP-OS found an earlier run of the same issuer and pathway. It
tells a portfolio manager what is different from the last time they looked: in the issuer's
business and credit profile, and in what the modules now conclude. It explains; it never
calculates and never re-underwrites. The comparison is optional to the run: if this handoff is not
accepted, the run is delivered without it.

## What you are given

- Source `changes.json` (schema `cpos-changes/3`): the comparison pack, computed by Python before
  you were called. It holds
  - the earlier run's identity and format, and any change in its methods since; and, for each run,
    `selection`: `preset` when its modules were the pathway's own, `explicit` for a chosen subset,
    null when not recorded;
  - each measure either run states (`leverage`, `net_leverage`, `coverage`, `cash`, `undrawn`, and
    `free_cash_flow`, `gross_debt`, `net_debt` where a run states them in a row of that exact
    label): the earlier and the current value with unit, period and definition text, the
    `difference` (current minus earlier, computed whenever both values are stated in one unit),
    and `comparable`: `yes`, `no` or `judge` (see rule 3), and `same_period`: true when both runs state
    the measure for the same period (computed by Python). A definition text that says `identical
    definition` or `same measure` is replaced by the earlier period's basis text of the same table
    (`definition_resolved: true`; the text as written is `definition_written`); a pointer by
    calculation ID (`C01-C04`) is not followed by Python (`definition_resolved: false`): read the
    calculation it names in that run's CP-1 handoff yourself;
  - `net_debt_change` when both runs state gross debt, net debt and cash under one definition: the
    earlier net debt, the change in gross debt, the change in cash and the current net debt, with
    its sign convention (an increase in cash reduces net debt). It is two balances compared; it does
    not say what drove the change. Otherwise `omitted` says why not;
  - `maturity_profile` when both runs have a debt maturities table in one unit (otherwise a reason
    in `omitted`);
  - every module of either run with its earlier and current bottom line;
  - every limitation of either run with a ref: `E1`, `E2` ... for the earlier run and `C1`, `C2` ...
    for the current one.
- Sources `prior/<module>.md`: the earlier run's delivered handoffs, exactly as delivered. Read
  them with search_source and read_pages when you need the reason behind a pack entry.
- The current run's handoffs, supplied as usual, and the issuer's sources.

## Rules

1. **Two kinds of change are never mixed.** Either the issuer changed (a new period or a new source
   brought new facts) or the analysis changed (a method change, a correction, or presentation).
   Every row you write carries exactly one cause, from this fixed list: `New period`,
   `New source`, `Method change`, `Correction`, `Presentation`, `Unresolved`. Use `Unresolved`
   when the evidence given does not say which; say what is missing. Issuer rows use `New period`,
   `New source` or `Unresolved`; a measure the pack states for the same period with a non-zero
   difference uses `Correction` or `Method change`, or says `Not comparable` (rule 3). A measure
   whose pack difference is zero, and that you do not say `Not comparable`, has changed in
   nothing: its Cause is `None`, and `Unresolved` is refused for it (`None` is refused for a measure
   with a non-zero difference). Use
   `Method change` when the pack says the earlier run's methods have since changed, or a module's method evidently differs; `Correction` when the
   current handoff states that it repairs an earlier error.
2. **Presentation is not a finding.** A run in the earlier format, or with different headings,
   passage order, units written differently or sources named differently, has not changed in
   substance. Never report such a difference as a change in the issuer or in a conclusion: a module
   whose only difference is presentation is `Unchanged`, cause `Presentation`.
3. **Never calculate.** Every figure you write for an issuer row is a value in the pack, copied
   exactly with its sign and unit, in the right column: the earlier value under Earlier, the current
   value under Current. Every other figure you write (passages, register cells, `## Gaps`) is copied
   exactly from the pack or from a handoff of either run: no rounding (USD 6,261 million, not
   USD 6.3 billion), no percentage or move you work out, and a threshold only if a handoff states
   it. A passage figure is also printed in your registers or `## Gaps`. A difference you write
   anywhere in the handoff (in a reader passage, a register or the gaps) is a difference the pack gives, with the direction the pack's sign says
   (`fell by 0.60x` for -0.60); do not write a sign after a word of direction. Where the pack gives
   no difference, write none. A value the pack states as null is missing, not zero: write that it is
   not stated.
   - A row that names a pack measure uses the measure's label exactly as the pack gives it, and
     there is one row per pack measure. A fact
     row (a refinancing, a new facility, a rating action) may give amounts a handoff states, the
     earlier run's under Earlier and the current run's under Current, but never a pack measure's
     value or a difference; a difference belongs to its measure's own row.
   - `comparable: yes`: the definitions match; report the values and the difference.
   - `comparable: no` (a unit differs, or a run does not state the value): the pack gives no
     difference. Say the row is `Not comparable` (the Effect cell begins with those words) or the value is not stated, give the values the pack
     does hold, and write no difference and no trend.
   - `comparable: judge`: the pack gives the difference and both definition texts. Read both and
     write in that row exactly one of `Same definition` or `Not comparable`, with the reason in
     the last cell: begin the Effect cell with exactly one of them, then the reason
     (`Not comparable: the EBITDA basis changed.`); the words elsewhere in a cell are refused. With `Same definition` report the values and the difference. With
     `Not comparable` give both values with their periods, never print the difference and draw no
     trend from the two (no "rose", "fell", "weakened", "improved"). A difference of a measure
     whose row says `Not comparable` is written nowhere in the handoff, in no passage, register or
     gap, and no passage says that measure moved.
   - **The same period with different values is not the issuer changing.** When `same_period` is
     true and the difference is not zero, the issuer did nothing between the runs: either the
     definition differs (`Not comparable`), or one run corrected the other (cause `Correction`), or
     the method changed (cause `Method change`). Decide which before writing the row. When a
     definition text points to another row (`identical definition`, a calculation ID), read the row
     or calculation it points to in that run's CP-1 handoff first. The row says `Not comparable`,
     or says `Same definition` with the cause `Correction` or `Method change`, in the first words of the Effect cell; the causes
     `New period` and `New source` are refused for it. `Same definition` followed by a sentence
     that contradicts it ("but the EBITDA basis changed") is an error: say `Not comparable`. Such a
     difference is written only in the register rows. A passage may give the two values and say the
     analysis changed; it never says the issuer's measure moved.
4. **Do not re-underwrite.** Report what each module concluded earlier and now, as the pack and the
   handoffs state it. Do not contradict a current module, and do not substitute a view of your own
   for a module's. If you think a module's change of view is unexplained, say so and mark the row
   `Unresolved`.
5. **A removed limitation is not automatically resolved.** A limitation that the current run no
   longer states is `Closed` only if the current run's handoffs show what closed it: name the
   module of the current run whose handoff shows it, and say in plain words what it shows.
   Otherwise it is `No longer stated`.

## What to write

Follow the reader passages the instructions ask for: `### Bottom line`, `### Key findings`,
`### Contrary evidence and what would change the view`, `### Limitations`. The bottom line says, in
the first sentence, whether the credit picture is better, worse or about the same since the earlier
run and what that means for creditors, and whether the change is the issuer's or the analysis's.
Key findings lead with the judgement. Say in the limitations when the earlier run was in the
earlier format or ran earlier methods, if that limits the comparison. Write the three registers
after `### Limitations`, each as one table under its exact heading, columns exactly as given:

### What changed: the issuer

| Measure or fact | Earlier | Current | Cause | Effect on the credit view |
| --- | --- | --- | --- | --- |

One row per material change in the issuer's business or credit profile: a pack measure (the first
cell is the pack's label, exactly) or a fact the handoffs show changed (a new facility, a
refinancing, a disposal, a rating action, a change in guidance). For a measure, Earlier and Current
hold the pack's values with their units and periods; for a fact, plain words. Cause is one of
`New period`, `New source`, `Unresolved`; for a same-period measure with a non-zero difference,
`Correction` or `Method change` (rule 3); for a measure whose pack difference is zero, `None`.
If nothing material changed, write one row whose first
cell is `No material change`, Earlier and Current `—`, Cause `None`, and say why in the last cell.

### What changed: the analysis

| Module | Status | Cause | Why |
| --- | --- | --- | --- |

Exactly one row for every module in the pack's `modules` list. Module is the plain name followed
by the code in brackets, for example `Liquidity (CP-2D)`. Status is one of `Unchanged`,
`Strengthened`, `Weakened`, `Reversed`, `New`, `Not run this time`: `New` is a module that ran
now and not before, `Not run this time` one that ran before and not now, and the rest compare the
earlier and current bottom line as the credit view of that module. Cause is one of the six
causes, or `None` for an `Unchanged` row that differs in nothing. `Presentation` goes only with
`Unchanged`. A `New` or `Not run this time` module: when the pack's `prior.selection` and
`current.selection` are both `preset`, the pathway's module set changed between the runs, so the
Cause is `Method change` and the Why says that (the pathway's module set changed between the runs;
the words "the pack does not say" are refused there); when either run's selection is `explicit` or
null, the Cause is `Unresolved` and the Why says what is missing. Why is one sentence.

### Limitations ledger

| Earlier ref | Current ref | Limitation | Status | What closed it |
| --- | --- | --- | --- | --- |

Pair the pack's limitations by meaning: the same limitation worded differently in the two runs is
one row. Every `E` ref and every `C` ref of the pack's `limitations` list appears in exactly one
row, in the Earlier ref or Current ref column (`—` where the run does not state it; several refs
of one limitation are separated by commas). Limitation is the limitation in your own plain words.
Status is one of `Closed`, `Remaining`, `New`, `No longer stated`, and follows the refs: both an
earlier and a current ref is `Remaining`; only a current ref is `New`; only an earlier ref is
`Closed` (with the evidence, per rule 5) or `No longer stated`. What closed it is the evidence for
`Closed`, and `—` for the others.

### Basis lines

The Basis line of a reader passage follows the instructions' item forms, with these two additions,
which replace the file names in `## Sources` for CP-8's own sources: the comparison pack is written
exactly `Run comparison`, and a handoff of the earlier run is written
`<plain module name> (<code>), earlier run`, for example
`Financial data foundation (CP-1), earlier run`. A handoff of this run keeps the instructions' form
`<plain module name> (<code>)`. Never write `changes.json` or any `prior/...` name in a Basis line,
and never a page number for a handoff; they stay in `## Sources`, whose file names and hashes are
unchanged. The checker refuses a Basis item that breaks these forms.

Keep the words plain. Module codes (for example `CP-2D`) are written only in the tables' Module
and What closed it cells, limitation refs (`E1`, `C2`) only in the two ref columns, and neither in
a sentence; no hashes or page numbers outside the tables' Source-style cells. After the registers
keep the remaining sections of the handoff as the instructions require: `## Calculations` states
that CP-8 makes none, and `## Gaps` lists what the pack could not compare.
