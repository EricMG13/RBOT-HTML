# Ruling: the reader, the voice standard and the issuer report

by: user
date: 2026-11-11

This ruling lifts no pause and authorises no provider call. It changes what a module writes,
what delivery may do with it and what "complete" means. Nothing in the code enforces it yet:
two later sessions build to the "Handoff contract" below.

Why: an adversarial audit on 2026-11-11 found that the output reads as cited, robotic restatement.
No governing document named the reader or a voice standard, completion was defined only as
fidelity, and delivery published module-to-module text verbatim. Evidence on main at `d1c9b91`:

- `src/deploy_workflow/owners/cpos_launch.py:250` scopes the reader standard to CP-2 only
  (`READER_STANDARD_MODULES = frozenset({"CP-2"})`), and lines 277-278 of that standard tells CP-2 to
  "Cite modules and locators in brackets or tables".
- The persona at line 257 asks for findings that are "deeply analytical and data-dense".
- Line 105 says the rest of `CANON_SHARED.md` is "archived, not sent", although
  `docs/reuse/selected-methods/CANON_SHARED.md:257` puts raw source locators in the appendix.
- The reader summary (line 1391) "restates conclusions already in this handoff".
- `src/deploy_workflow/handoff_delivery.py:4`: "Narrative values stay literal".
- The voice reference is the September 2026 M365 outputs for VMO2 (screenshots in
  `~/Documents/VMEDO2 Screenshots`, read-only): prose names sources in words, IDs sit in table
  Source columns and a plain-English source list. The May V4 prompts likewise kept sources in a
  separate citation map.

## Decisions (owner, 2026-11-11, all approved)

1. A report is one run of an issuer, shown natively in the issuer library. The separately
   rendered delivered HTML report is retired entirely.
2. The HTML Model, charts and calculation JSON are kept, as parts of the issuer report, not as
   separate items.
3. Charts sit in the module that owns them; key charts are repeated on Overview. The delivered
   Model appears as an entry in Modules. Calculation JSON is a download in Evidence, and each
   calculated figure opens its steps in the inspector. The Forecast section stays; its job is the
   forward cash flow model.
4. The Report section is the issuer's history: one row per run, newest first, showing date,
   pathway, modules run and status. A partial re-run is its own row. Every page carries a label
   saying which run it shows.
5. The Modules navigator is flat and always open, with no collapsing. It lists only the modules
   that ran in the selected run. Group labels are plain headings. Each entry shows the plain module
   name first and the code second. A module that ran but was blocked is listed and marked "Not
   assessable". The open entry shows an "On this page" outline. Search sits at the top.
6. Overview has no module navigator. It leads with the credit view written by a module that
   already reads the others (CP-6's chair conclusion when CP-6 ran, otherwise CP-2), then one
   reader-written bottom line per module that ran, then the limitations that change a conclusion
   (each once per run), key charts and the nearest dates. Assembly is selection and ordering
   only; the app never rewrites. There is no new synthesis module.
7. Sources in prose: no chips, module codes, page numbers or brackets in sentences. A source is
   named in words only when it matters to the argument. A figure in prose is itself clickable and
   opens the inspector (source file, page, quoted passage, calculation steps). A paragraph with no
   figure gets one quiet "Basis" link. Tables keep a Source column in plain words. Every reference
   the handoff carries stays reachable.
8. The reader is a portfolio manager or credit committee member who has not read the source
   documents. Every module that writes prose owes, in order: the bottom line first (the view and
   its consequence for creditors); key findings, judgement first, with only the figures that move
   the view; the strongest contrary evidence and what would change the view; limitations once,
   only where they change a conclusion, the rest in the gaps table; then tables and registers,
   unchanged and exact. Evidence, then risk mechanism, then credit implication governs the
   reasoning and the registers, written as ordinary sentences, never as labels. The persona text
   is kept with one added line: "Lead with the judgement; use data to support it, not to narrate
   it." Data modules (source readiness, canonical data, peers) keep tables as their main content
   and owe only the bottom line. This replaces the CP-2-only scope.
9. Evidence lists, for the selected run: the source files used (name, type, document date and the
   modules that read each; files supplied but not used listed separately as "Supplied, not used";
   listed only, not downloadable or viewable); the handoffs (one per module, each downloadable,
   plus "download all"); and the calculation and Model downloads.
10. Run internals (hashes, instructions sent, retry and cost log) go in a fourth Evidence list,
    "Run record", closed by default. Run activity shows only runs in progress and the queue.
11. Enforcement: mechanical prose checks block a run and send a targeted repair request, within
    the existing retry and cost cap. Judgement quality is not machine-gated: it is checked by
    reading one real run per change against the September VMO2 reference and recorded in
    `VERIFICATION.md` with its scope. CP-8 adds presentation to what it compares. Fidelity checks
    are unchanged.
12. Sections per issuer: Report (history), then a chosen run's Overview, Modules, Forecast and
    Evidence. The Event calendar is no longer a tab: its timeline appears in the modules that own
    the dates, and the nearest dates appear on Overview. The left rail holds Start a run, Issuer
    library, Run activity and Search; the "Reports" rail entry goes.
13. The work is three sessions, each in its own worktree and pull request: this documents-only
    one first, then module instructions, checks and delivery, and library presentation, in
    parallel. No paid model run in any of them.
14. Existing runs are shown in the new layout without changing stored handoffs. At display time a
    trailing bracket citation or chip moves behind a Basis link, with the wording otherwise
    untouched, and the run is labelled "Earlier format" in the Report history.

## Rulings replaced

- The CP-2-only reader scope (owner ruling, 2026-11-05): `src/deploy_workflow/owners/cpos_launch.py:248-250`
  (`READER_STANDARD_MODULES`) and the matching sentence of the 2026-11-10 selections in
  `METHODOLOGY-REVIEW.md` ("Archived but not sent: the rest of `CANON_SHARED.md` …"). Replaced by
  decision 8. `docs/rulings/2026-11-05-cp2-reader-test.md` stays as the record of that test.
- "Delivery must not invent replacement analysis", read as forbidding any rephrasing:
  `AGENTS.md` (the bullet "Preserve values, periods, units, source references …") and
  `src/deploy_workflow/handoff_delivery.py:4` ("Narrative values stay literal"). Replaced by
  decision 6: delivery still adds no analysis, but selects and orders module-written passages.
- The delivered report as a completion condition: `AGENTS.md` (the bullet "Completion requires
  populated final deliverables …") and the library's listing rule in `README.md` ("runs CP-OS
  completed with a verified report"). Replaced by decisions 1 to 3: completion is the library's
  Overview, Modules, Forecast and Evidence pages populated from the run's handoffs and checked
  against them.

## Handoff contract

This section is what the module-instructions/checks/delivery session and the library session
build to. "Must" is a requirement on the handoff; "the checker" is CP-OS's handoff check; "the
app" is the issuer library.

### H1. Where the reader passages sit

The handoff's H2 sections are unchanged (`## Request`, `## Sources`, `## Findings`,
`## Calculations`, `## Gaps`, `## Next module`). The reader passages are the first content of
`## Findings`, as H3 sections with these exact headings, each exactly once, in this order:

1. `### Bottom line`
2. `### Key findings`
3. `### Contrary evidence and what would change the view`
4. `### Limitations`

Every other `## Findings` content (method sections, registers, tables, report selectors, the
forecast block) follows `### Limitations`, unchanged and exact. These four headings replace
`### Reader summary` and the module-specific opening H3 (`OPENING` in `cpos_launch.py`).

"Reader passages" below means the bodies of these four sections only.

### H2. What each passage holds

- **Bottom line**: one or two paragraphs. The first sentence states the module's view and its
  consequence for creditors. A blocked module still writes this section, saying that it is not
  assessable and why.
- **Key findings**: one paragraph or one list item per finding. Each starts with the judgement;
  figures appear only where they move the view.
- **Contrary evidence and what would change the view**: prose giving the strongest evidence
  against the view and what would change it.
- **Limitations**: a bulleted list, one limitation per item, each saying which conclusion it
  changes and how. A limitation that changes no conclusion goes in the `## Gaps` table instead.

Evidence, risk mechanism and credit implication are written as ordinary sentences, never as
labels (no "Evidence:", "Mechanic:", "Implication:" lead-ins).

**Data modules** (CP-0 source readiness and its alias CP-PARSE, CP-1 canonical data, CP-1C peer
benchmark) owe only `### Bottom line` as the first H3 of `## Findings`; their tables follow as
main content. Every other module that writes prose owes all four passages. A blocked module of
either kind owes only `### Bottom line`.

### H3. The Basis line

The Basis line carries what used to be inline citations.

- Form: the last line of a paragraph or list item (no blank line before it), starting exactly
  `Basis: `, followed by items separated by `; `, with an optional final full stop.
- An item is one of:
  - `<source file name>` or `<source file name>, page <n>` or `<source file name>, pages <n>–<m>`,
    where the file name is exactly as listed in `## Sources`;
  - `<plain module name> (<code>)` for an upstream handoff, e.g. `Liquidity (CP-2D)`;
  - `calculation <id>` for a row of this handoff's `## Calculations`.
- A paragraph that rests on no source, upstream handoff or calculation has no Basis line.
- Within the reader passages, the Basis line is the only place where a source locator, page,
  module code, module name used as a citation, or calculation/register ID may appear.
- The app does not print the Basis line as text. A figure in the paragraph opens the inspector,
  which shows the paragraph's Basis items with the figure's own source, page, quoted passage and
  calculation steps where the handoff carries them. A paragraph with no figure shows one quiet
  "Basis" link.

### H4. Tables and registers

Tables and registers follow the reader passages, unchanged and exact: same rows, columns, IDs,
values and order. A table that cites sources has a column headed `Source` whose cells name the
file and page in plain words, in the item form of H3. Raw locators, hashes and reference columns
stay where the method puts them; the app may show them in the inspector or the Run record, but
never removes them.

### H5. What Overview selects

In this order, selection and ordering only, text unchanged:

1. **Lead**: if CP-6 ran and is not "Not assessable", its `### Bottom line` and
   `### Key findings`. Otherwise, if CP-2 ran and is not "Not assessable", the same two passages
   of CP-2. Otherwise no lead, and Overview says that no credit view module completed.
2. **Bottom lines**: the `### Bottom line` of every other module that ran, in the order CP-OS ran
   them. A blocked module's entry is marked "Not assessable".
3. **Limitations**: every item of every module's `### Limitations`, in module order. Items whose
   normalised text (check 7) is identical are shown once.
4. **Key charts**: the charts whose row in `docs/visualisations/catalogue.csv` names Overview in
   its `placement`, for which the run has data.
5. **Nearest dates**: the next five dated items on or after the run's as-of date, from the
   timelines of the modules that own them.

Amendment 2026-11-12 (owner approved 2026-11-11, "3. approved"): on a Short Credit Snapshot run
(pathway `short_snapshot`: CP-0, CP-1 and CP-L10) CP-L10 is the lead, after CP-6 and CP-2, which do not
run in that pathway: its `### Bottom line` and `### Key findings` lead the Overview and are not repeated
in the bottom lines. Nothing else in H5 changes; CP-L10's `### Key figures` table is a report block, not
Overview content.

### H6. Mechanical prose checks (decision 11)

The checker runs these on the reader passages of every handoff. Excluded from "sentence text":
headings, Basis lines, table rows (lines starting `|`), fenced code and HTML comments. A failure
blocks the handoff and sends a repair request naming the check number, the line and the offending
text, within the existing retry and cost cap; nothing else about retries changes.

1. **Bottom line present**: the first H3 under `## Findings` is `### Bottom line`, and its first
   non-blank line is prose (starts with a letter, a quote mark or `**`; not a table, list, fence,
   comment or heading).
2. **No module code**: sentence text does not match `\bCP-[A-Z0-9]+\b`.
3. **No page locator**: sentence text does not match, case-insensitively,
   `\bpp?\.\s*\d|\bpages?\s+\d|\bpg\.?\s*\d`.
4. **No bracket citation or chip**: sentence text contains none of `[`, `]`, `【`, `】`.
5. **No hash**: sentence text does not match `\b[0-9a-fA-F]{12,}\b` or contain `sha256`
   (case-insensitive).
6. **No register ID**: sentence text contains no token equal to an ID used in the same handoff,
   where an ID is a cell value containing at least one letter and one digit in a table column
   whose header is `ID` or ends in ` ID` (case-insensitive), or an ID in `## Calculations`.
7. **No limitation repeated within the run**: normalise each `### Limitations` item (lower case,
   drop the Basis line, remove punctuation, collapse whitespace). No two items in the run,
   across this handoff and the handoffs already accepted in the run, are identical.
8. **Figures carry unit and currency, at most two decimals**: a figure is a run of digits with
   optional thousands commas and decimal part, not touching a letter or a hyphen-joined letter
   (so `10-K`, `B-1` and `FY2024` are not figures). Exempt: a four-digit year from 1900 to 2099;
   a date (`2024-09-30`, or a day or year next to a month name); a period label (`Q1`–`Q4`,
   `H1`, `H2`, `FY…`, `LTM`, `9M`); a whole number below 100 with no decimal (a count). Every
   other figure must:
   - have at most two digits after the decimal point;
   - be preceded by an ISO currency code and a space (`USD 1,250 million`) or a currency symbol
     (`$`, `€`, `£`, `¥`), or be followed by one of `%`, `x`, `bp`, `bps`, `basis points`,
     `percentage points`, `pp`, `times`, `notch`, `notches`, `day`, `days`, `week`, `weeks`,
     `month`, `months`, `quarter`, `quarters`, `year`, `years`;
   - if followed by `thousand`, `million`, `billion`, `trillion`, `k`, `m` or `bn`, also be
     preceded by a currency code or symbol.

Fidelity check (decision 11, owner 2026-11-11): every figure in a reader passage (the four prose
passages, and a data module's Bottom line) must also appear in the handoff outside the reader
passages (tables, `## Calculations`, other `## Findings` content) with the same sign, unit and
scale: `12.3%` is not `(12.3)%`, `4.1x` is not `4.1%`, `250 thousand` is not `250 million`, and a
number matches only as a whole number. A bare figure matches a held figure with a unit, and the
reverse. On the passage side, dates and period labels are not figures, as in check 8. An owner
ruling of 2026-11-11 adds this fidelity check for the reader passages, based on the retired
Reader-summary figure check. It is a fidelity check that blocks like H6, with a repair request
labelled `Fidelity check:` inside the same retry and cost cap, and it is not one of the eight prose
checks.

Amendment 2026-11-12 (check 9, found by the paid web-search test `tdg-cpdr-web-001`): a ninth prose
check, **no provider citation marker**: the handoff, anywhere in it, contains none of the
provider's delimiters (U+E200, U+E201, U+E202; any other private-use character is left alone) and
nothing that matches `cite\s*turn\d+[a-z]+\d+` (citeturn0view0, citeturn0image0, cite turn0fetch1). The run's CP-DR
handoff carried 54 markers of the form U+E200 `cite` U+E202 `turn123066view0` ... U+E201 that the
eight checks did not catch. A searching module's answer text now has such markers removed
mechanically before it is checked (the count is recorded in the run record; the provider's
retained response is unchanged), and check 9 refuses any other shape within the same retry and cost
cap. The fidelity check stays outside the numbered list, so "ninth" is correct.

Not machine-gated (decision 11): the order and presence of the three passages after Bottom line,
judgement-first wording, and whether a limitation truly changes a conclusion. These are judged
by reading one real run per change against the VMO2 reference, recorded in `VERIFICATION.md`.

### H7. "Earlier format" runs

A run is "Earlier format" when any of its handoffs has a `## Findings` whose first H3 is not
`### Bottom line`. The app labels such a run "Earlier format" in the Report history and shows it
in the new layout without changing stored handoffs: a bracket citation or chip at the end of a
sentence or paragraph moves, verbatim, behind that paragraph's Basis link; all other wording is
untouched. Earlier-format runs have no reader passages, so Overview shows for them only what H5
can select (no lead, bottom lines or limitations unless the headings exist), plus key charts and
nearest dates.

## Choices made in drafting

Where the decisions left a detail open, the simplest option was taken:

1. Fixed passage headings for every module (H1), replacing `### Reader summary` and the
   per-module opening H3, so one checker and one Overview rule serve all modules.
2. The Basis line is the paragraph's last line, may carry the module code in parentheses after
   the plain name, and may cite `calculation <id>`, so the app can resolve it without guessing.
3. A Basis line is written only where a paragraph rests on something; its absence is not a
   blocking check (decision 11 lists none).
4. The prose checks apply to the reader passages only, not to method prose after them.
5. "Data modules" are CP-0 (with CP-PARSE), CP-1 and CP-1C, matching the three named kinds.
6. A blocked module owes only the Bottom line.
7. The Overview lead takes Bottom line and Key findings of CP-6, else CP-2; the lead module's
   bottom line is not repeated in the per-module list.
8. Key charts are the catalogue rows already placed on Overview; nearest dates are the next five.
9. Repetition (check 7) is exact match after normalisation; paraphrases are left to the reading
   check.
10. Figure check exemptions (years, dates, period labels, whole numbers below 100) and a short
    unit list; a non-money count written with a scale word ("12 million shares") fails check 8
    and must be reworded. That is the known ceiling of the check.
11. Currency may be an ISO code or a symbol.
12. "Earlier format" is recognised from the handoffs themselves (H7), with no new manifest field.
13. Report history "date" is the run's as-of date; runs with the same as-of date are ordered by
    start time, newest first.

Amendment 2026-11-11: a run whose methods have since changed is listed and marked "Earlier methods"; replayed, synthetic and unverified runs stay unlisted.

Amendment 2026-11-12 (owner): no module code is shown on screen, in the issuer library (the Modules navigator, Report history, Evidence, module pages, Overview, the inspector and its Basis items) and on the run start page. A reader sees a module's plain name, never its code. This replaces "the code second" in decision 5 and the reading of decision 7 under which new-format text kept its codes on screen. The Basis line form in the stored handoff (H3) and check 2 are unchanged: the handoff still names an upstream module as `Name (code)`, and the page shows the written name. It is display only: stored handoffs, routes, `href`s, download names and saved answer keys do not change, and stored source file names and file paths are shown exactly as stored on every page, even when they hold a `CP-` token. The embedded original Model file (`src/deploy_vii/assets`) is not covered by this change.
