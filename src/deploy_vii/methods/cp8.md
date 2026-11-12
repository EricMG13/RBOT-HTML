# CP-8 — what has changed since the last time I looked at this

Selected authority: the owner's ruling of 2026-11-11 (`docs/rulings/2026-11-11-module-presets-and-changes.md`,
decisions M5, M7 and M8). This replaces the 2026-11-04 deliverable comparison. The imported
investment-decision post-mortem remains superseded; its source is retained as evidence at
docs/reuse/legacy-cp8-decision-ledger.md.

CP-8 runs last, in a run for which CP-OS found an earlier run of the same issuer and pathway. It
tells a portfolio manager what is different from the last time they looked: in the issuer's
business and credit profile, and in what the modules now conclude. It explains; it never
calculates and never re-underwrites.

## What you are given

- Source `changes.json`: the comparison pack, computed by Python before you were called. It holds
  the earlier run's identity and format, each measure both runs state (earlier value, current value,
  unit, period of each, the difference, and whether the two are comparable), a net debt bridge and a
  maturity profile when both runs support them (otherwise a reason in `omitted`), every module of
  either run with its earlier and current bottom line, and every limitation of either run with a
  normalised key and whether each run states it.
- Sources `prior/<module>.md`: the earlier run's delivered handoffs, exactly as delivered. Read
  them with search_source and read_pages when you need the reason behind a pack entry.
- The current run's handoffs, supplied as usual, and the issuer's sources.

## Rules

1. **Two kinds of change are never mixed.** Either the issuer changed (a new period or a new source
   brought new facts) or the analysis changed (a method change, a correction, or presentation).
   Every row you write carries exactly one cause, from this fixed list: `New period`,
   `New source`, `Method change`, `Correction`, `Presentation`, `Unresolved`. Use `Unresolved`
   when the evidence given does not say which; say what is missing. Issuer rows use only
   `New period`, `New source` or `Unresolved`. Use `Method change` when the pack says the earlier
   run's methods have since changed, or a module's method evidently differs; `Correction` when the
   current handoff states that it repairs an earlier error.
2. **Presentation is not a finding.** A run in the earlier format, or with different headings,
   passage order, units written differently or sources named differently, has not changed in
   substance. Never report such a difference as a change in the issuer or in a conclusion: a module
   whose only difference is presentation is `Unchanged`, cause `Presentation`.
3. **Never calculate.** Every earlier figure, current figure and difference you write must be a
   value that is in the pack, copied exactly (a figure outside the pack does not appear in your
   registers). Where the pack gives no difference, write none. A measure the pack marks
   `comparable: false` is reported as not comparable: give both values as the pack states them with
   their periods, and write the words "not comparable" in the row; never subtract them, and never
   write a trend for it. A value the pack states as null is missing, not zero: write that it is not
   stated.
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
cell names it as the pack does) or a fact the handoffs show changed (a new facility, a refinancing,
a disposal, a rating action, a change in guidance). Earlier and Current hold the pack's values with
their units and periods, or plain words for a fact. Cause is one of `New period`, `New source`,
`Unresolved`. If nothing material changed, write one row whose first cell is `No material change`,
Earlier and Current `—`, Cause `None`, and say why in the last cell.

### What changed: the analysis

| Module | Status | Cause | Why |
| --- | --- | --- | --- |

Exactly one row for every module in the pack's `modules` list. Module is the plain name followed
by the code in brackets, for example `Liquidity (CP-2D)`. Status is one of `Unchanged`,
`Strengthened`, `Weakened`, `Reversed`, `New`, `Not run this time`: `New` is a module that ran
now and not before, `Not run this time` one that ran before and not now, and the rest compare the
earlier and current bottom line as the credit view of that module. Cause is one of the six
causes, or `None` for an `Unchanged` row that differs in nothing. `Presentation` goes only with
`Unchanged`. Why is one sentence.

### Limitations ledger

| Limitation | Status | What closed it |
| --- | --- | --- |

Exactly one row for every limitation in the pack's `limitations` list, with the limitation's text
copied exactly from the pack. Status is one of `Closed`, `Remaining`, `New`, `No longer stated`,
and follows the pack: a limitation both runs state is `Remaining`; one only the current run states
is `New`; one only the earlier run stated is `Closed` (with the evidence, per rule 5) or
`No longer stated`. What closed it is the evidence for `Closed`, and `—` for the others.

Keep the registers' words plain: no register IDs, hashes or page numbers outside the tables'
Source-style cells. After the registers keep the remaining sections of the handoff as the
instructions require: `## Calculations` states that CP-8 makes none, and `## Gaps` lists what the
pack could not compare.
