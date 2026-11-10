# Run report: the run page as the report, modules as its appendix — spec

Owner, 2026-11-09: "decide what is worth show and not, plus how to present it; consider the
markdowns like database" → review `docs/design/2026-11-09-run-page-content-review.md` (BLOCK) →
"Write the spec". Layout rules and the handoff method are open to change in this build.

Amends `docs/design/2026-11-09-module-report-spec.md` (Rendering item 5, the seven anchors,
rulings R28 and R32) and the Overview of `docs/superpowers/specs/2026-11-09-credit-os-static-pages.md`.

## Problem (measured on `cpos-tdg-sol-medium-all-001`)

- 7 of 20 modules reach a conclusion (CP-1, CP-1A, CP-2, CP-2D, CP-2E, CP-3C, CP-DR). The
  Overview gives them the weight of the 13 that say "Not assessable" and leads with CP-6's
  "blocked".
- A module page opens the whole handoff: CP-1's Analysis part is 22,560px. Under `## Findings`,
  CP-1 holds 746 words in sections without a table and 3,000 in sections with one; CP-2E 806
  and 4,103.
- 878 of 1,630 chips say "no page" or "no key".
- Every handoff has the same level-2 skeleton (`Request, Sources, Findings, Calculations, Gaps,
  Next module`; 20 of 20) and the two Reader summary tables. Nothing else is uniform: 178 table
  shapes, 162 used by one module.

## Scope

**Phase A (page and library build only; all three retained runs; no provider call):** the
Overview becomes the run report; the module page splits reading from reference; chips quieten.
**Phase B (handoff contract in `src/deploy_workflow/owners/cpos_launch.py`):** four additions
that make the gaps and status joinable. Proving Phase B needs a new paid run, which is a
separate, explicit owner action; Phase B's page parts fall back to Phase A when the fields are absent.

Out: chart kinds the page cannot already draw, Forecast/Calendar/Reports tabs, the library table, delivery renderers, the
`Finding | Creditor impact | Confidence` header (delivery routes and `store.py` read it as is).

## One rule for "established"

Python (`apps/issuer-library/credit_os/store.py`, beside the reader summary) adds to each output:

```json
"state": {"established": true, "declared": "Requires More Work"}
```

- `established` = the Reader summary's `Confidence` cell is not `Not assessable`; `null` when the
  output has no Reader summary.
- `declared` = the front matter's `committee_status` verbatim, else `null`.

No other signal is used. The page never infers a blocker, a dependency or a status.

## Data contract additions (`data.js`, built by Python)

- `workspace.outputs[id].state` as above.
- `workspace.outputs[id].words`: `{view, reference, calculations, limits, audit}`, word counts by
  the placement rule below.
- Phase B: `workspace.outputs[id].openItems`, `.dependsOn`, `.keyNumbers` (see Phase B).

Section placement, by the handoff's level-2 parent, computed once in Python and read by the page
(replaces the per-module `sectionGroups` guesses for analytical outputs):

| Level-2 parent | Section | Placement |
|---|---|---|
| Findings | `Reader summary`, `Chart data: …` | consumed by band, findings, charts (unchanged) |
| Findings | no table block | `view` |
| Findings | any table block | `reference` |
| Calculations | all | `calculations` |
| Gaps | all | `limits` |
| Front matter, Request, Sources, Next module | all | `audit` |

A section the existing evidence-heading rule (R31a) marks as evidence stays `audit`.

## Run report (Overview tab; replaces `summaryView`'s lead and cards)

Order, one scroll:

1. **Count line.** `7 of 20 modules reach a conclusion · 13 not assessable`, then the run's
   acceptance and qualification badges as today. Outputs with `established: null` are counted
   apart: `· 2 without a reader summary`.
2. **Committee band.** The navy band shows only when CP-6 is established. Otherwise no band:
   CP-6 appears in the not-assessable list like any other module. `CALL_ORDER` is removed.
3. **Credit story.** The seven existing reading groups (`groups` in `screen.js`), in order. Per group:
   - each established module: name (link), the bottom line verbatim, confidence pill, declared
     status when present, every finding row (claim, creditor impact, confidence, resolved chips),
     the main limitation;
   - the group's charts directly under the module that owns them (today's four move under
     CP-1 in Financial performance); the "Missing values have no bar" note prints once per group at most;
   - each not-assessable module: one line — name (link) · `Not assessable` · declared status ·
     the main limitation verbatim. No card, no findings.
   - A group with no established module prints its heading and those lines only.
4. **Findings register.** One table of every finding row from established modules: Group,
   Module, Finding, Creditor impact, Confidence; filters for group and confidence. A checkbox
   `Include not-assessable modules (51)` adds their rows, marked.
5. **Open items.** Phase A: every module's main limitation, one row each, grouped as above, with
   a link to that module's limits part. Phase B: the joined register (below).
6. **Module matrix.** One row per module in group order: name, confidence, declared status
   (`not declared` when null), words to read (`words.view`), words of reference
   (`words.reference + words.calculations`). Phase B adds `Depends on` and `Blocked by`.
7. **Deliverables from this run** and the source inventory link, as today.

Nothing on the run report is written by the page: every sentence is a handoff cell verbatim, and
counts come from Python.

## Module page

Anchors, in order: `head, bottom-line, numbers, findings, analysis, limits, reference,
calculations, audit`. A part with no content is omitted with its "On this page" entry (the
`No key numbers table` line goes).

- **Head:** adds the declared status badge beside the acceptance badge.
- **Analysis** (`view` sections, open, handoff order): prose with resolved chips.
- **Limits** unchanged.
- **Reference** (`<details>` closed; summary `Statements and registers · 14 tables · 212 rows`):
  the `reference` sections, each whole, in handoff order.
- **Calculations** (`<details>` closed): the `calculations` sections, whole.
- **Evidence & audit** unchanged.
- **Not-assessable module:** head, band, findings, limits. Analysis, reference and calculations
  go under one closed `<details>` titled `Full handoff text · <n> words`.
- **Headings:** a leading method code is dropped from the displayed heading and kept in `title`:
  `/^(T\d+[A-Z]?\.\d+|[a-z0-9]+(\.[a-z0-9_]+)+)\s+—\s+/`.
- Nothing is truncated: a closed part renders its sections whole when opened, and a chip or hash
  route into a closed part opens it.

## Chips on the reading path

- `issuer_page` and `upstream` chips render as today; an `issuer_page` chip with
  `quote_found: true` gets the class `verified` and `title="Quote found on page"`.
- `gap` chips labelled `Not supplied` render as today (they are content).
- Other `gap` chips (`no page`, `no key`, `… · ambiguous`) do not render singly. A block that has
  any shows one count after its resolved chips: `3 citations without a page`, which opens the
  inspector's list of them.

## Charts and visualisations

Measured on the medium run: 4 charts, all from CP-1 (`Chart data: leverage`, `interest cover`,
`liquidity`, `debt maturities`). The other six established modules draw nothing. The visuals
catalogue (`workspace.visuals`) lists 91 intended views: 14 with an existing figure, 46 that are
tables by design, 22 new views. The launcher asks only CP-1 for chart tables (`CHART_TABLES`).

One rule, unchanged: a chart is drawn only from a `Chart data: …` table the handoff declares, in
the fixed shape `Period | <value columns> | Reporting unit | Basis and limitation`. The library
build already reads that section from any module (`reader_fields`). The page never charts a
register: T2E.5, T3D.1 and the T2F tables hold the numbers in mixed text cells.

Phase A (no new run):

- **Run report:** each chart sits under its owning module in the credit story. No chart row at the
  top of the page. A group with no chart shows none and says nothing about it.
- **Coverage strip** under the count line (amended 2026-11-10, `2026-11-10-impeccable-pass.md`; was beside): one cell per module in group order, labelled with
  its code, filled when established, hollow when not assessable, each a link. Built from `state`.
- **Module page:** charts stay in the numbers part, above the key-numbers table.
- The 46 catalogue entries marked `Table/content only` are the Reference tables; no chart is
  added for them.

Phase B (launcher asks for three more chart tables; the catalogue's `First` figure producers of
established modules):

| Figure | Module | Section | Value columns | Unit | Drawn as |
|---|---|---|---|---|---|
| S.5 | CP-1 | `Chart data: revenue and EBITDA` | Revenue; Adjusted EBITDA | US$m | bars |
| CR.2 | CP-2D | `Chart data: liquidity bridge` | Amount (row label is the bridge item) | US$m | bridge |
| CR.3 | CP-3C | `Chart data: refinancing need` | Principal payable; Resources at maturity | US$m | bars |

Python sets each chart's `kind` from this table; the page has both renderers
(`comparisonChart`, `bridgeChart`). CP-2E's rate-shock and hedge-cover charts (catalogue priority
`Next`) follow the same route once these three are proven. CP-1A, CP-2 and CP-DR stay chartless:
their catalogue entries are timelines, diagrams and matrices with no renderer.

## Phase B — handoff contract (launcher rules and checks, all modules)

Added to the launcher's shared instructions and its handoff checks, next to
`READER_SECTION_RULES`; module `SKILL.md` files change only where they contradict a rule.

1. **Front matter on every handoff**, with at least `committee_status` (the existing vocabulary:
   Committee Ready, Draft Only, Requires More Work, Insufficient Information, Restricted,
   Blocked), `depends_on` (module codes whose handoff this module read) and `blocked_by` (gap
   ids, empty when none).
2. **One open-items table**, first under `## Gaps`:
   `### Open items` with header `Gap id | Gap | Missing data | Blocks | Required follow-up`.
   A gap that is a missing source reuses the id CP-0 assigned in its readiness register; any
   other gap is `<module>-G<n>`. The page joins rows by `Gap id` and ranks by modules blocked.
3. **Blocked short form.** A handoff whose `committee_status` is Blocked or Insufficient
   Information holds Request, Sources, Reader summary, the opening view paragraph, Open items
   and Next module, and no register of absent data.
4. **Declared key numbers.** Optional `### Key numbers` under `## Findings`, header
   `Measure | Period | Value | Unit | Source`, at most 8 rows. When present the page uses it and
   skips the first-qualifying-table rule (R15, R26).

Dropped from the review's list: typed section headings (the level-2 skeleton already types every
section) and finding ids or tags (the module-to-group map supplies the group; the three-column
header is read by delivery).

## Tests (answer keys from fixtures the implementer does not edit)

- Python: `state` for fixtures with confidence `Medium` → established; `Not assessable` → not;
  no Reader summary → `null`; `declared` verbatim from front matter and `null` without.
  `words` and placement for a fixture with a prose section, a table section, a Calculations
  section and a Sources section.
- `node --test`: the run report prints the count line from `state`; no band when the CP-6
  fixture is not assessable and a band when it is; an established module renders its findings, a
  not-assessable one renders one line and no `.finding`; the register excludes not-assessable
  rows until the checkbox is on; module anchors in the order above with empty parts omitted;
  a not-assessable module has no open `#analysis`; a method-code heading displays without its
  code; a block with two `no page` chips renders one count and no `.chip.gap`.
- Browser (`file://`, 1440 and 1280): no horizontal overflow on the run report; a hash route to
  a section inside closed Reference opens it and scrolls to it; Esc from the inspector restores
  focus.
- Rebuild check on `cpos-tdg-sol-medium-all-001` (key from the review's census, not from the
  code): count line `7 of 20`; established set CP-1, CP-1A, CP-2, CP-2D, CP-2E, CP-3C, CP-DR;
  register 33 rows, 84 with the checkbox; CP-1 `words.view` 746 and `words.reference` 3,000;
  CP-2E 806 and 4,103; no single `no page` chip on any page.

## Risks and open points

- CP-0 reads as not assessable under the one rule, though it is a readiness verdict. It is left
  in the list; an exception would be a second rule.
- The blocked short form conflicts with module methods that require complete registers, and
  some module validators (`validate_handoff.py`) may check for them. Each such module is
  reconciled one at a time against its own output before the rule is switched on for it.
- Phase B is unproven until a paid run retains handoffs written under it.
- The placement rule sends a prose section with one small table to Reference. Accepted: the
  section stays whole and one click away.

## Not in this spec

A page-written summary paragraph; inferred dependencies from module mentions; cross-run
comparison (CP-8); any change to the delivery process.

Not verified: the word counts in the rebuild key come from a scratch census (whitespace-split
words of text blocks and table cells, headings excluded); the Python `words` field must use that
definition or the key is re-measured by a reviewer, not by the implementer. The level-2 skeleton
and the one rule were checked on the medium run only, not the two sol-high runs. The method-code
pattern was written from three observed headings, not run over all headings. No module
`validate_handoff.py` was read against the blocked short form. Phase B has no retained handoff.
Whether delivery's figure routes accept S.5, CR.2 and CR.3 from chart tables was not checked
(`STRIP_FIGURES` lists S.1–S.4 only), and `bridgeChart` reads a pinned fixture table today, so
drawing it from a reader chart is an adaptation, not a reuse.
