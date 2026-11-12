# Ruling: changes from the section-by-section review of module output

Date: 2026-11-12. Owner instructions, in order, in the session that ran the review:
"review your suggestions given the approval to alter methodology"; "add those to the changes too"
(the helper scripts and the source references); "why charts in tables when they should be
charts"; "consolidated changes into a plan and complete it". This record states what those
instructions were taken to decide. It amends `2026-11-11-reader-and-issuer-report.md` where said.

Evidence: `reviews/2026-11-12-module-output-adversarial/` (one reviewer per section of the real run
`tdg-proof-snapshot-opus-002`, TDG, as of 2024-09-30, credit snapshot; presentation only, findings
not second-checked) and two read-only traces of the causes in the code. Findings the traces refuted
are listed at the end and are not acted on.

## Decisions

Library (display only; stored handoffs, routes and file names are unchanged)

1. A chart, map or timeline is shown once, as a drawing in its panel. Its `Chart data:`, `Map:` or
   `Events:` section is no longer printed again in the body or listed under "On this page"; the
   numbers stay as the drawing's "Table form" fold, and prose written in that section is the
   drawing's caption. A chart with no numbers gets a card saying "Not established for this run"
   with the reason, as maps and timelines already do. Section routes keep working.
2. On a new-format module page, `## Request`, `## Next module` and front matter move to an
   "Evidence & audit" fold at the end of the page. Front matter is drawn as stated lines, not as a
   paragraph, and its `filename` line is not drawn (it names the handoff with a module code; the
   download carries the file). `## Sources`, `## Calculations` and `## Gaps` stay on the page.
3. Source references resolve. A source listed in `## Sources` is known to the page, so a figure,
   a Basis link, a table row and a `Source` cell open the inspector on the file and page. The
   `Source` cell text stays exactly as written (ruling H4). A Basis item may name several pages of
   one file separated by commas (`<file>, pages 71, 121`); this extends ruling H3. The row marker
   reads "Row", not "Handoff"; the count reads "unresolved citations", not "citations without a page".
4. A register id at the start of a heading is dropped whether or not a dash follows it; no heading,
   outline entry or search label says "a method step". A register id that carries a module code
   (`CP-3B-MON-001`) is shown without the code part.
5. A negative amount is one clickable figure, sign and currency included. A fenced block is drawn
   as a block. A table wider than its box shows that it scrolls and can be scrolled from the keyboard.
6. Drawings: bridge labels do not overprint; the debt stack is coloured by ranking and security,
   with a legend; a timeline has year ticks, an as-of line, a numbered key and no hidden point;
   map text wraps on words and edge labels do not collide.

Method and checks (new runs only; all in the launcher's shared text, which sits before the method
block, so existing runs are not marked "Earlier methods")

7. The reader's vocabulary applies to every section the Modules page shows, not only the four
   reader passages (this replaces drafting choice 4 of the 2026-11-11 ruling). In sentence text
   under `## Findings`, `## Calculations` and `## Gaps`: no module code, page locator, bracket or
   hash (checks 2 to 5), and no pipeline wording (new check 10: "handoff", "this transport", "the
   pack", "fact pack", "source pack", "canonical", "re-anchor", "helper script", "upstream module",
   "downstream" before module/owner/work/analysis/use, snake_case tokens, CAPS_WITH_UNDERSCORE
   tokens). Words with an ordinary credit meaning (consumer, producer, upstream, transport) are
   not banned on their own. Tables, fences, Basis lines, and the chart, map, event and forecast
   input sections are not sentence text. The register-id check (6) stays on the reader passages.
8. Bottom line shape (controller's values, not the owner's): the first sentence is at most 45
   words and the whole passage at most 180 words. Whether the sentence states the view stays a
   reading judgement.
9. Helper scripts: a module does not mention scripts it cannot run and does not state a confidence
   score, band or QA status. A module whose method carries the confidence score writes a
   `### Confidence inputs` table (lineage counts, fields present and required, source gate,
   findings by severity); Python computes the score and band by the method's own formula
   (`CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`) and the module page shows it. No completeness
   script exists in the archive, so none is ported: the checker's required sections are the
   completeness check.
10. Financial foundation writes `### Post-balance-sheet adjustments` (event, date, amount, pro
    forma net debt, pro forma net leverage, or one row saying none was found). A module that
    quotes year-end net debt, net leverage or cash from it states the pro forma figure beside it
    when that table has a row. No pro forma row is added to the chart or net debt tables (a row
    that is not a period drops the measure from the Changes comparison).
11. `## Sources` names each source with its exact file name (the join key, unchanged), a plain
    description of the document and its document date; the run settings are not listed as a
    source. A module refers to another module by its plain name, from a list the launcher sends.
    A chart table is followed by one sentence giving the figure's main qualification; map node
    and edge text is at most 60 characters.

## Not acted on

- Basis links "missing": refuted. Every paragraph with a Basis line shows figures or a link.
- "All bridge steps one colour": by design (colour by sign).
- The bottom line set wholly in headline type: this is the recorded redesign decision (controller
  ruling 2 of 2026-11-12 and a pinned browser test). Left for the owner.
- Replacing file names with plain names in `Source` cells and Basis items: they are join keys and
  ruling H4 requires them exact.
- A machine block or new H2 for routing text: the six H2 headings are read by name in four places.

## Limits

No paid run was made. Decisions 7 to 11 are proven only offline until one is; tighter checks mean
more refused drafts within the three writes a module has, and a run interrupted before this change
may refuse to resume.
