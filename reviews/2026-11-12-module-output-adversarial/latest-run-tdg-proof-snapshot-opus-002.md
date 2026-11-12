# Adversarial review of the latest module output, section by section

Date: 2026-11-12. Review only: no code, handoff or run folder was changed; no provider was called.

## The run

- Run: `tdg-proof-snapshot-opus-002`. Issuer: TransDigm Group Incorporated (TDG). As of 2024-09-30.
  Pathway: credit snapshot. Real paid run on opus-medium, 2026-11-12 12:12 to 13:09 UTC, 13 of 13
  modules accepted and delivered (VERIFICATION.md, "First real CP-8 run read").
- Why it is the latest: it is the most recent run folder on this machine with a completion record
  (searched `runs/` in the main checkout, the other sessions' scratch workspaces and RBOT-Query's
  corpus). `cpos-tdg-sol-mixed-cp2-001` (01:11 to 01:51 UTC the same day) is older and stopped
  unpublished after six modules. `tdg-reader-format-001` (11 Nov) is older; it was reviewed first by
  mistake and its findings are in `earlier-run-tdg-reader-format-001.md` beside this file.
- Not under the newest method changes: the library lists this run as "earlier methods". The
  financial-foundation net debt table, the forecast named rows and thousands scale, and the
  changes-module fixes were merged after it ran. No run exists under those changes; one needs a
  new paid run.
- Run folder (read-only, in another session's scratch space, so it may be cleaned up):
  `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002`.
- How it was read: a copy of the run was built into a scratch library with this checkout at main's
  tip (`a873f6f`, so the redesign pass 1 is included). Each section was captured from the Modules
  page at 1440 px in headless Chrome.

## Method

- 185 sections, one read-only reviewer (mx-precise) per section, each applying the
  adversarial-reviewer skill on two subjects: (1) credit narrative: tone, style and layout;
  (2) charts and visuals: layout and style.
- A section is one heading as the Modules page lists it under "On this page", with three groupings:
  the folded "Analytical appendix" registers are one section per module (split in two or three
  where long); Request, Next module and front matter are one section; a "Chart data", "Events" or
  "Map" section was judged together with its drawing in the Charts, Timeline or Maps panel.
- Severity: High = would mislead the reader's credit judgement, breaks a house rule, or the visual is
  unreadable or wrong. Medium = slows or confuses the reader. Low = polish.
- Limits: the reviewers judged presentation, not analytical accuracy; figures were not re-checked
  against the filings. Findings were not verified by a second reviewer, so some will be wrong or
  duplicated across neighbouring sections. I confirmed two renderer findings myself: the
  "a method step" placeholder exists in `views.js` and `screen.js`, and the EBITDA bridge labels
  overlap (seen on the earlier run's page). Only 1440 px in Chrome was captured; hover, the
  inspector, print and other widths were not.

## Result

1,281 findings: 295 High, 643 Medium, 343 Low. 103 of 185 sections were given BLOCK, 82 CONCERNS,
none CLEAN (the skill requires each of three personas to find something, so CLEAN is rare by
construction).

## Patterns that repeat across modules

Counts are keyword matches over the findings, so approximate.

Credit narrative

1. Pipeline language reaches the reader in every module (about 170 High findings, 13 of 13
   modules): "handoff", "upstream", "consumer", "canonical", "the pack", "transport", status
   values such as READY_WITH_LIMITATIONS, snake_case field names, script names. Worst in Sources
   notes, Calculations, Gaps, Next module and the registers.
2. Whole sections exist for the pipeline, not the reader: Request, Next module, front matter,
   "Module status", "Consumer readiness and command sheet", QA validation. Front matter is printed
   as one run-on line and shows a file name with a module code (Committee decision, Evidence
   validation, Rates, FX & hedging).
3. Sources are named by raw file names, accession numbers and 64-character hashes (13 modules);
   a run-settings row called "context" is listed as a source in most Sources tables.
4. Self-graded status and scores confuse the verdict (13 modules, about 49 High): undefined
   confidence formulas (E, C, S, P), "Passed" beside checks that were not run, a clearance that
   reads as a pass while the same page records blocked or must-fix items.
5. The year-end cash and net leverage are repeated without the USD 4,216 million dividend paid
   18 days later (11 modules): net leverage 4.51x is shown where the same run also gives 5.55x pro
   forma, and several pages quote leverage on different bases without saying which governs.
6. Judgement is often not first inside a passage: the verdict sits at the end of a long paragraph,
   after caveats (about 50 sections). Bottom lines of 150 to 230 words with 50 to 60 word opening
   sentences are common.
7. Module-code replacement produces broken sentences: "Downside downside pathway",
   "Security selection-MON-001", module names repeated in brackets, lists of modules "not in this
   run" that are in it.

Charts and visuals

1. Register codes are replaced by the literal words "a method step" (7 modules, 16 High): every
   register heading and "On this page" entry starts with it, and two entries can read the same.
2. Wide tables are clipped at the right edge with no scroll cue (9 modules); the Source column is
   usually the one lost, which is where the house rule says references live.
3. Basis links are reported missing on some paragraphs and bullets (all 13 modules). CORRECTION
   (2026-11-12): part of this is by design. Under decision 7 of the reader ruling a paragraph that
   has a clickable figure shows no separate Basis link, and at least one High finding (Rates, FX &
   hedging, Limitations) flags exactly that case. Only a paragraph with a Basis line, no figure and
   no link is a defect; each such finding must be checked in triage before it is acted on.
4. Timelines are unlabelled dots: no event labels, no year ticks, no as-of marker, same-week events
   drawn on top of each other (every module with a timeline).
5. Maps break node text mid-word, cut it with an ellipsis, overlap edge labels, and one map is cut
   off before its end node (Business & governance, Fundamental credit, Downside, Evidence
   validation).
6. Charts carry "Handoff" chips and calculation codes, and "citation without a page" where the
   handoff gives a page (all seven Financial foundation charts).
7. EBITDA bridge: category labels print on top of each other and every step is the same blue.
   Debt stack: colours repeat with no link to rank or security.
8. Charts state the figure without its main qualification (leverage, liquidity and maturities
   charts versus the dividend and the USD 487 million securitization due 2025-07-11).
9. The covenant headroom and portfolio limits charts have no slot and no "not established" note
   when there is no data, unlike timeline and maps.
10. The bottom line is set entirely in large bold headline type, so a two-paragraph bottom line is
    an 800 px wall; negative amounts lose their minus sign inside the figure chip; a fenced JSON
    block renders as one run-on paragraph (Forward credit model).

## Proposed changes (owner approved changing the methodology, 2026-11-12)

Not built. Each item needs the triage step first: one verified defect per item, wrong and duplicate
findings struck.

Method and handoff contract (proved by one paid run)

1. Prose checks cover every section the Modules page shows, not only the four reader passages.
2. Request, Next module, front matter, module status, QA validation and readiness tables stop being
   findings; routing and status go in one machine block the page never renders.
3. Registers are named by title only (no codes in headings), keep a visible Source column and stay
   folded. They are not removed.
4. Sources table: document name, type, period and filing date. Hashes come from the run record.
   Run settings are not a source.
5. Helper scripts: the methods stop telling the model to run or report on scripts it cannot run.
   The orchestrator computes the completeness check and the confidence score in Python from the
   accepted handoff. A check that was not run is never reported as passed. (Today the model has no
   tool that executes code, is told to record each script as not run and do the check by hand, and
   then reports a hand-counted score beside a passed status.)
6. Financial foundation states one governing leverage basis and a post-year-end row; other modules
   quote that row.
7. Bottom line: one-sentence verdict first, then at most two short paragraphs, enforced by the checker.
8. Other modules are named in words in reader text, so no code replacement is needed on screen.
9. Chart, timeline and map tables carry what the drawing needs: short labels, rank and security
   for the debt stack, one qualification line per chart shown as its caption, an as-of row, a
   length limit on node and edge text, and "not established" with the reason when there is no data.

Library

10. Source references, to match decision 7 of the reader ruling:
    - a table's Source cell is a link that opens the source file at the page, in plain words;
    - the row chip no longer reads "Handoff" and no longer points only at the handoff row;
    - "citation without a page" is not shown where the row states pages (seen on the revenue and
      EBITDA chart rows, which state pages 71 and 121; cause not traced);
    - a paragraph with a Basis line, no figure and no Basis link gets its link, with a test that
      counts both sides;
    - not verified here: whether the inspector shows the quoted passage and opens the source at
      the page.
11. Charts are shown as charts once. Today each chart is drawn in the Charts panel at the top of
    the module page and the same data is printed again further down as a table under a
    "Chart data: ..." heading, which "On this page" also lists. The table stays only as the
    "Table form" fold under its chart; the body copy and the "Chart data:" label go.
12. Drawing defects: clipped wide tables, label collisions on maps and the EBITDA bridge, the minus
    sign outside the figure chip, fenced blocks, headline type on the whole bottom line,
    "a method step" (removed by item 3 for new runs, still needed for existing ones).

## Counts by module

| Module | Sections | High | Medium | Low | Sections blocked |
|---|---|---|---|---|---|
| Source readiness (CP-0) | 11 | 16 | 40 | 19 | 8 |
| Business & governance (CP-1A) | 16 | 26 | 53 | 33 | 6 |
| Research questions (CP-DR) | 14 | 25 | 45 | 25 | 6 |
| Financial foundation (CP-1) | 19 | 28 | 61 | 39 | 12 |
| Fundamental credit (CP-2) | 12 | 20 | 43 | 20 | 6 |
| Downside (CP-2A) | 14 | 22 | 56 | 23 | 8 |
| Forward credit model (CP-2G) | 13 | 21 | 51 | 22 | 9 |
| Rates, FX & hedging (CP-2E) | 16 | 25 | 61 | 32 | 7 |
| Legal & covenants (CP-4) | 11 | 12 | 34 | 21 | 6 |
| Security selection (CP-3) | 15 | 26 | 56 | 28 | 12 |
| Committee decision (CP-6) | 16 | 27 | 50 | 31 | 6 |
| Evidence validation (CP-5) | 17 | 35 | 54 | 27 | 10 |
| Changes since the last run (CP-8) | 11 | 12 | 39 | 23 | 7 |

By subject: narrative High: 234; narrative Medium: 462; narrative Low: 133; visual High: 61; visual Medium: 181; visual Low: 210.

## Source readiness (CP-0)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-0/49103856766826f1d85d8b782f3f3963c36b80eaa14981e8091d8f2b3ea7b124/1.response.md`

### Bottom line

Kind: reader passage · handoff lines 20-27 · verdict **BLOCK**

- Narrative: The bottom line puts the judgement first, as the house order requires, but the judgement is hedged and buried in long sentences full of pipeline vocabulary. Its headline creditor fact (the special dividend) is wrongly called post-period and understated by USD 132 million against the 10-K (pp.56, 63, 120, 170).
- Visual: This section has no chart of its own. On the page it reads as a 23-line wall of large bold type with no Basis links rendered and monospace figures mid-sentence, and the module timeline sits directly under it, unlabelled and with no as-of marker. The screenshot starts below the section's heading, so the heading was not judged.

1. **High · narrative** (Saboteur)
   - Where: 1.response.md line 22: "the post-period special dividend of USD 4,216 million paid on 2024-10-18, which is the most consequential creditor event in the pack"
   - Problem: The 10-K shows this dividend was declared before year-end and booked at 2024-09-30 as dividends payable of 4,216 (p.120; p.170: "accrued as of September 30, 2024"). The total cash paid was USD 4,348 million once the USD 132 million of dividend equivalents is added (p.56, p.63). Calling it "post-period" and quoting only 4,216 understates the cash drain on the USD 6,261 million year-end cash this module reports, and a reader may treat that cash as unencumbered.
   - Fix: Say the dividend was declared and accrued at year-end and paid on 2024-10-18, give the total cash outflow of USD 4,348 million including dividend equivalents, and point to the filing's pro forma liquidity after the payment.
2. **High · narrative** (New reader, Auditor)
   - Where: 1.response.md lines 22 and 25: "The pinned pack is sufficient" / "prior-deliverable work" / "even though the run settings mark legal documents as executed" / "the prior-versus-current comparison without a prior deliverable to compare against"
   - Problem: "Pinned pack", "prior-deliverable work", "run settings" and "prior-versus-current comparison" are pipeline words, not reader language. This breaks the house rule, and a portfolio manager cannot tell what they mean without knowing the workflow.
   - Fix: Use plain reader terms: "the filings provided", "comparison with an earlier analysis", "the analyst's run settings". Otherwise leave the reader-facing bottom line out of the run mechanics.
3. **Medium · narrative** (Saboteur)
   - Where: 1.response.md line 22: "legal, market-value and prior-deliverable work can proceed only within explicit bounds"; line 25: "even though the run settings mark legal documents as executed"
   - Problem: The judgement is hedged: the bounds are called "explicit" but the first paragraph never states them. The "even though" clause leaves the reader unsure whether executed legal documents exist and were withheld, or never existed, which changes how far covenant conclusions can be trusted.
   - Fix: Open with one direct sentence on what the evidence supports and what it does not. State plainly that the executed agreements exist but were not supplied, and that covenant headroom therefore cannot be measured.
4. **Medium · narrative** (New reader)
   - Where: 1.response.md line 22: "The pinned pack is sufficient for a filing-grounded credit snapshot ... rather than executed agreements." (about 60 words in one sentence); line 25 (about 100 words in two sentences)
   - Problem: The bottom line runs to two dense paragraphs of about 180 words and uses compound sentences of 60 words or more. The one takeaway a committee member needs is buried, and the second paragraph is a limitations list that crowds out the judgement.
   - Fix: Cut it to two or three short sentences: the judgement first, then the single limitation that matters most. Move the remaining limits into the module's limitations or gaps section.
5. **Medium · visual** (Auditor)
   - Where: Screenshot CP-0_bottom-line.png, crop x330-1420 y200-1020 (scratchpad/tmp/CP-0-001-a.png): the two bottom-line paragraphs
   - Problem: Both bottom-line paragraphs have Basis lines in the handoff (lines 23 and 26, also present in library data.js) but no "Basis" affordance is rendered under them. The paragraphs further down the same page do show a "Basis" link, so the reader cannot trace the bottom line's sources.
   - Fix: Render each bottom-line paragraph's Basis link the same way as the other passages on the page.
6. **Medium · visual** (New reader)
   - Where: Screenshot CP-0_bottom-line.png, y about 230-920 (original px): the bottom-line block
   - Problem: About 180 words are set entirely in large bold display type (about 22 px bold) across 23 lines. The whole block is one wall of emphasis with no hierarchy, so nothing stands out and it is tiring to read.
   - Fix: Set only the lead judgement sentence in the large bold style and the rest in regular body weight, or cap the lead at two or three lines as in the VMO2 reference.
7. **Low · visual** (Auditor)
   - Where: Screenshot CP-0_bottom-line.png, Timeline strip just below the bottom line (y about 925-1010 original px)
   - Problem: The timeline sits directly under the last bottom-line line with almost no gap. Its dots have no labels and only the end dates (2023-11-27, 2027-11-15) are shown. The single lane is labelled "Sources" and the caption reads "Dated events by module", which is pipeline wording. Nothing marks the 2024-09-30 as-of date on an axis that runs to 2027.
   - Fix: Add spacing above the strip, label or tooltip each event in reader terms, mark the as-of date, and rename the caption to something like "Key dates".
8. **Low · visual** (New reader)
   - Where: Screenshot CP-0_bottom-line.png: inline figures "USD 4,216 million", "7.25x", "5.00x", "7.50x" within the bold sans text
   - Problem: Figures switch to a lighter monospace face with a dotted underline in the middle of large bold sans text. This breaks the reading rhythm and makes the key numbers look weaker than the words around them.
   - Fix: Keep figures in the paragraph's face and weight, with a subtle affordance (for example, a hover only) for the value-trace link.

### Key located evidence for downstream owners

Kind: prose/table · handoff lines 47-67 · verdict **BLOCK**

- Narrative: The figures I checked agree with each other (7,267 = 6,261 + 843 + 163). However, the heading and the closing paragraph speak to the pipeline rather than the reader, and the cash and liquidity rows invite an overstated view of liquidity because the dividend caveat sits after the table and gives no amount.
- Visual: The section is a single clean table followed by one paragraph and has no chart. Readability suffers from the long repeated source filenames and the redundant per-row 'Basis' chips; nothing is clipped or overlapping.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: line 47: "### Key located evidence for downstream owners"; shown as the section heading and in the left 'On this page' list (CP-0_s-47.png, top of content column and sidebar)
   - Problem: 'Downstream owners' is pipeline vocabulary, which the house standard says is not reader language. It shows on screen as both a heading and a navigation entry, and a portfolio manager does not know who the 'owners' are.
   - Fix: Use a reader heading such as 'Key figures located in the filings', with no reference to the pipeline.
2. **High · narrative** (Saboteur)
   - Where: line 57: "Cash and cash equivalents | USD 6,261 million | 2024-09-30" and line 58: "Cash liquidity (company-defined) | USD 7,267 million" vs line 62: "Special dividend ... USD 4,216 million plus dividend equivalents USD 132 million, accrued at 2024-09-30"
   - Problem: The cash and liquidity rows show year-end figures and do not say that about USD 4,348 million of that cash left on 2024-10-18. The warning only appears in a paragraph after the table and gives no amount. A reader who scans the table overstates creditor liquidity by roughly two thirds.
   - Fix: Flag the dividend outflow in the cash and liquidity rows themselves (or add a post-dividend line) and state the amount in the paragraph after the table.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 65: "Two presentation traps must be carried into the financial foundation. The debt note shows the receivables securitization as a separate short-term line above a gross total that excludes it"
   - Problem: The paragraph is an instruction to another module ('carried into the financial foundation'), not a judgement for the reader. The section therefore gives no bottom line on what these figures mean for credit.
   - Fix: Open with the reader's point (debt is understated by USD 487 million if the securitization is left out, and cash is overstated by the accrued dividend), with no hand-to-module wording.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 61: "Springing revolver covenant | 7.50x (8.00x for four quarters after a material acquisition), tested if revolver usage exceeds 40% (USD 364 million)"
   - Problem: The row never names the ratio the 7.50x applies to (for example first-lien or net leverage), so the reader cannot judge the covenant headroom. The incremental-debt row next to it does name its ratios.
   - Fix: Name the tested ratio and its basis in the Located value cell.
5. **Medium · visual** (New reader, Auditor)
   - Where: Key located evidence table, Source column (CP-0_s-47.png, x≈900–1160, y≈255–950 in displayed scale)
   - Problem: Every row repeats the same 60-character filing filename with its accession number. The filename wraps to 2–3 lines and takes about a third of the table width, which makes the row heights uneven and pulls the eye away from the values.
   - Fix: Show a short source label (for example 'FY2024 10-K, p. 44') and keep the full filename in the Sources list.
6. **Low · narrative** (Saboteur)
   - Where: line 53: "Interest expense-net | USD 1,286 million | FY2024"; line 63: "Debt and note fair values | Carrying and fair value per instrument, Level 1 and Level 2"
   - Problem: Interest expense has no FY2023 comparative, while sales and EBITDA have one. The fair-value row sits under 'Located value' but gives no value, so the table is not consistent.
   - Fix: Give comparatives the same way in every row, and either quote the aggregate carrying and fair values or move that row to a coverage note.
7. **Low · visual** (Auditor)
   - Where: Item column 'Basis' chip on every row, e.g. 'Net sales Basis', 'Debt, gross (debt note total, excluding securitization line) Basis' (CP-0_s-47.png, x≈300–480)
   - Problem: A 'Basis' link chip is appended to each Item label even though the table already has a Source column. This duplicates the reference, makes the labels read oddly and forces extra line wraps.
   - Fix: Drop the per-row Basis chip in tables that already carry a Source column.

### Consumer readiness and command sheet

Kind: prose/table · handoff lines 68-84 · verdict **BLOCK**

- Narrative: The section is an internal routing table shown to the reader. It uses pipeline vocabulary and enum values, has no judgement line, and tells the reader the change comparison should not run when it did run in this run.
- Visual: Module codes are correctly replaced with names, but long raw filenames in the Source column, orphan Basis chips and plain styling of the one blocking status make a tall, low-signal table.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 83: "| CP-8 | CONDITIONAL | Needs a prior deliverable to compare | Context states no prior case attached ... | DO NOT RUN until a prior deliverable is supplied or scope is changed |"; screenshot CP-0_s-68.png, last table row (y~1280-1395)
   - Problem: The table tells the reader that 'Changes since the last run' must not run, but the module did run in this run (runs/tdg-proof-snapshot-opus-002/requests/CP-8 exists, and the left nav lists 'Changes since the last run'). The page header also shows '3 runs'. Two parts of the same page disagree, so the reader cannot tell whether the change comparison can be trusted.
   - Fix: Make the readiness verdict match what actually ran, or flag on screen that the module ran against this readiness verdict and say what that means for its reliability.
2. **High · narrative** (New reader, Auditor)
   - Where: line 68 heading "Consumer readiness and command sheet"; line 70 headers "Consumer | Readiness | ... | Bounded limitations carried | Command"; cells "READY_WITH_LIMITATIONS", "RUN"
   - Problem: This section uses pipeline language throughout: 'consumer', 'command sheet', raw enum values such as READY_WITH_LIMITATIONS and CONDITIONAL, and RUN/DO NOT RUN instructions. That breaks the house rule against pipeline vocabulary, and a portfolio manager gets no credit meaning from it.
   - Fix: Retitle the section in reader terms (e.g. 'What the evidence supports, by analysis'), write the readiness values in plain words, and drop the Command column or restate it as the effect on the reader.
3. **Medium · narrative** (Auditor, Saboteur)
   - Where: lines 68-84, the whole section is one table with no lead sentence
   - Problem: The section has no judgement sentence. The reader has to scan 12 rows to work out that every analysis except one runs with limitations, and which limitations matter for the credit view (no executed credit agreement, no quotes or ratings, no Q1 filing).
   - Fix: Open with one judgement line saying which gaps limit the credit view most, then the table.
4. **Medium · narrative** (New reader)
   - Where: line 74 "context, page 1" (also lines 81-83); line 73 "Context deal terms blank"; line 76 "Context stress assumptions blank; method defaults apply"
   - Problem: 'Context' is an internal run-request artifact, not a document the reader can find. As a Source it points nowhere, and 'context assumptions blank' and 'method defaults apply' mean nothing to someone outside the pipeline.
   - Fix: Name the source in reader terms (e.g. 'run request: no deal terms supplied') and say which default assumption was used.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-0_s-68.png, Source column x~1030-1150 (screen), every row
   - Problem: The raw filename 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl' wraps over four to five lines in every row. It makes each row two to three times taller, so the 12-row table runs about 1,200 px for little information, and it exposes a pipeline file extension (.jsonl).
   - Fix: Show a short source label (e.g. 'FY2024 10-K, p. 44, 50, 144-145') with the full identifier in a tooltip or the Sources list.
6. **Low · visual** (Auditor)
   - Where: CP-0_s-68.png, first column, grey 'Basis' label under each analysis name (e.g. 'Financial foundation Basis', 'Fundamental credit Basis')
   - Problem: Every row has an orphan 'Basis' chip that runs into the analysis name and reads as part of it (e.g. 'Changes since the last run Basis'). It repeats what the Source column already gives.
   - Fix: Remove the per-row Basis chip in tables that already carry a Source column, or set it clearly apart from the name.
7. **Low · visual** (Saboteur)
   - Where: CP-0_s-68.png, Readiness and Command columns
   - Problem: The one exceptional row (CONDITIONAL / DO NOT RUN) has the same plain grey text as the eleven routine rows, so nothing draws the eye to the only blocking status.
   - Fix: Use a status chip or colour that separates ready, limited and conditional, with a text label as well as colour.

### Events: Sources

Kind: timeline · handoff lines 95-107 · verdict **BLOCK**

- Narrative: The table is in date order and sources sit in the Source column as the house rule requires, but the heading, one relevance cell and the Status wording use internal or filing language, and the two halves of the special dividend use different units.
- Visual: The timeline strip is visible and not folded away, but two key subsequent events overlap into one dot, and the strip has no labels, no as-of line and no ticks; the table under it wastes width on constant columns and wrapped file names.

1. **High · visual** (Saboteur, Auditor)
   - Where: Timeline strip 'Sources' lane, rendered at /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-0-007-a.png (crop of CP-0-007-top.png, y 960-1070); handoff lines 103-104
   - Problem: There are 8 dated events but only 7 dots. The 2024-10-16 securitization drawdown and the 2024-10-18 USD 4,216 million special dividend fall on the same pixels (x≈377 and x≈393 overlap). The two most important subsequent events for creditors look like one marker.
   - Fix: Split or stack events that fall within a few pixels of each other, or show a count badge, so every row in the table has its own visible marker.
2. **High · visual** (New reader, Saboteur)
   - Where: Timeline strip, CP-0-007-a.png: only endpoint labels '2023-11-27' and '2027-11-15', unlabelled dots, no as-of marker
   - Problem: The dots have no labels, there are no intermediate date ticks and there is no line at the 2024-09-30 as-of date. A committee reader cannot tell which dots are before and which after the balance-sheet date, or what any dot is, without hovering. The compact view also drops the legend that explains point versus span.
   - Fix: Add an as-of reference line, year ticks and short visible event labels (or a numbered key tied to the table) so the strip can be read without hovering.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 100: "Sets current covenant baseline that legal work must use"
   - Problem: This Credit relevance cell tells a downstream module what to do; it says nothing to the reader about credit. That is pipeline wording leaking onto the page, against the house reader standard.
   - Fix: State the credit meaning, such as which covenant terms the 2024-03-22 amendment set, not an instruction to other work.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 95: "### Events: Sources" (and the timeline lane name 'Sources', subtitle 'Dated events by module')
   - Problem: The heading and lane name use the internal lane label: 'Sources' here means this module, not source documents. The subtitle 'Dated events by module' uses pipeline vocabulary. A reader will expect a list of documents, not a debt and dividend calendar.
   - Fix: Use a reader heading such as 'Key dated events: dividends, financing and maturities'.
5. **Medium · narrative** (Saboteur)
   - Where: line 105: "Scheduled — extend the maturity date to July 11, 2025"; line 100: "Historical — most recent amendment that impacted the restrictive covenants"
   - Problem: The Status cells paste filing phrases instead of giving a status. The maturity row says 'extend the maturity date', which reads as if an extension is planned, not as a facility due in July 2025. That blurs the nearest refinancing need.
   - Fix: Make Status a plain state (Paid / Declared / Drawn / Due) and leave filing wording to the Basis link.
6. **Medium · narrative** (Saboteur)
   - Where: line 102: "Special cash dividend of USD 75.00 per share declared" vs line 104: "Special dividend of USD 4,216 million and dividend equivalents of USD 132 million paid"
   - Problem: The declaration is given per share and the payment in total USD, and the rows are not linked to each other. The reader cannot see that they are the same distribution, or that the 2024-09-30 cash balance is already committed to it. The cash-distortion point in line 102's relevance is left for the reader to work out.
   - Fix: Give both rows the same unit (total USD), and cross-reference the declaration to its payment in the Credit relevance cells.
7. **Medium · visual** (New reader)
   - Where: Events: Sources table, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots2/CP-0_s-95.png, Event date and Source columns (top 200-940 at display scale)
   - Problem: Dates break mid-value ('2023-11-' / '27 Basis'), while the raw file-name Source column takes about a quarter of the width and wraps over 4-5 lines in every row. Date precision is 'day' in every row and Published is '—' in every row, so two columns carry nothing and squeeze the Event and Credit relevance columns.
   - Fix: Keep dates on one line, shorten the Source to a readable label such as 'FY2024 10-K, p.63' with the full ID kept in Sources, and collapse columns that hold the same value in every row.
8. **Low · narrative** (Saboteur)
   - Where: line 99: "Debt-funded distribution history relevant to extraction appetite"
   - Problem: The row calls the 2023 dividend 'debt-funded', but the cited event text gives only the per-share amount and total paid. Nothing in the row supports that characterisation.
   - Fix: Either cite the financing that funded it or describe it only as a shareholder distribution.

### Gaps

Kind: prose/table · handoff lines 117-129 · verdict **CONCERNS**

- Narrative: The Gaps table records the real limits (no executed credit agreement or indentures, no guarantor exhibit, no market data) but gives no bottom line first. It also leaks pipeline vocabulary ('consumers', 'context', 'pack', 'method defaults', '[Insufficient Information]') into text the reader sees.
- Visual: There is no chart. The 8-row, 5-column table is legible at 1440 px, but long raw file names wrap in the Source column, severity has no visual distinction, and the inline Basis links make row heights ragged.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 119 header "| Gap | Severity | Affected consumers | Remediation | Source |"; shown on screen as the column 'Affected consumers' (CP-0_s-117.png, Gaps table header, about y 1420 at full resolution)
   - Problem: 'Consumers' is pipeline vocabulary that the house standard bans from the reader's screen. The column lists modules, not credit topics, so a committee member cannot tell what the gap means for the credit view.
   - Fix: Rename the column to something like 'Analysis affected' and state the credit area at risk (covenants, recovery, relative value) instead of a list of modules.
2. **High · narrative** (Saboteur, New reader)
   - Where: Line 117–121: the section opens straight into the table "| Executed credit agreement, amendments and indentures not in pack although context marks legal documents as executed | High |"
   - Problem: The section gives no bottom line. The judgement that the High gap (no executed credit agreement or indentures) restricts the covenant, recovery and decision work to filing summaries sits in row one, cell four, and nothing says how much this weakens the final view. Two personas caught this, so it moves up from Medium.
   - Fix: Open with one judgement sentence that names the gap that matters most for the credit view and says what it limits, then show the table.
3. **Medium · narrative** (New reader, Auditor)
   - Where: Line 124–126: "Source" cells "context, page 1"; line 121 "not in pack although context marks legal documents as executed"; line 126 "Use method defaults and label them"
   - Problem: 'Context', 'pack', 'method defaults' and the bracketed tag '[Insufficient Information]' are internal labels. A reader cannot follow 'context, page 1' back to any document, so three rows have no source a reader can use.
   - Fix: Name the source in reader terms (for example 'run request: no market data supplied') and replace the internal tags with plain wording.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 125: "| No prior deliverable [Insufficient Information] | High for CP-8 | CP-8 | Supply prior case or re-scope CP-8 | context, page 1 |" (rendered 'High for Changes since the last run')
   - Problem: A workflow-scheduling note gets a 'High' severity next to real credit gaps. That inflates the apparent seriousness and puts it on the same scale as the missing legal documents. On screen, the severity cell wraps to four lines.
   - Fix: Keep severity for gaps that affect the credit view and move process notes, such as no earlier run to compare against, into a separate plain line.
5. **Medium · narrative** (New reader)
   - Where: Line 127: "Not needed while htm filing controls"; line 128: "Owners read them directly"
   - Problem: The remediation text is pipeline shorthand ('htm filing controls', 'owners'). A reader cannot tell whether these gaps leave the view exposed.
   - Fix: State in plain words why the gap does not change the view (for example 'the 10-K text covers the same content').
6. **Medium · visual** (New reader, Auditor)
   - Where: Gaps table, Source column, CP-0_s-117.png crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-0-009-a.png (Source cells, e.g. 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 61–62, 109–112')
   - Problem: Raw file names with accession numbers and a '.jsonl' extension take up about a quarter of the table's width and wrap over two or three lines. The text is hard to read and exposes the pipeline's file format.
   - Fix: Show a short document label (for example 'FY2024 10-K, pp. 61–62, 109–112') and keep the full file name in a tooltip or in Sources.
7. **Low · visual** (Saboteur)
   - Where: Gaps table, Severity column, CP-0_s-117.png full-resolution y 1440–2200
   - Problem: High, Medium and Low appear as plain grey text with no colour or chip. The single High row looks the same as the Low rows on a quick scan.
   - Fix: Show severity as a chip or with weight or colour, and sort the rows so High comes first, which the table already mostly does.
8. **Low · visual** (Auditor)
   - Where: Gaps table, Gap column, the trailing 'Basis' link in every cell (crop CP-0-009-a.png, e.g. 'executed Basis', 'absent / Basis' on its own line)
   - Problem: The inline 'Basis' link is attached to the end of the Gap text and sometimes wraps onto its own line, which adds ragged height to the rows. It also duplicates the Source column.
   - Fix: Drop the per-cell Basis link in tables that already have a Source column, or give it a fixed position.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 130-133 · verdict **BLOCK**

- Narrative: Both passages are run plumbing: model instructions and scheduling text, not credit narrative. On screen they carry a doubled phrase ("Source readiness source readiness"), pipeline vocabulary, and a Next module claim that Changes since the last run will not run. The run proves that claim false: the comparison module ran against tdg-reader-format-001.
- Visual: There is no chart, map or timeline in this unit. The two plain paragraphs render legibly, with no clipping, but nothing visually separates them from analytical prose, and they open and close the module page.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Line 132: "CP-8 stays DO NOT RUN until a prior deliverable is supplied." (rendered: "Changes since the last run stays DO NOT RUN until a prior deliverable is supplied."); see also gap line 125 "No prior deliverable [Insufficient Information]"
   - Problem: This contradicts the run itself. The run folder holds requests/CP-8/ad4831.../1.response.md, which compares against the earlier run tdg-reader-format-001, and a prior/ folder with CP-0..CP-6 handoffs. The Changes since the last run module sits in the same left nav. A reader is told the change comparison is invalid, or never happened, on the same page set that shows it.
   - Fix: Source readiness should see the prior run supplied by the orchestrator and say Changes since the last run is ready against tdg-reader-format-001, or the stale line should be suppressed when the comparison module ran.
2. **High · narrative** (New reader, Auditor)
   - Where: Request, line 3 as rendered (shot CP-0_s-1.png, y~225): "Source readiness source readiness for TransDigm Group Incorporated (TDG)..."
   - Problem: Swapping the module code for its display name puts the phrase twice in the first words the reader sees. That is a visible rendering defect, and it shows the module code was in the narrative sentence to begin with.
   - Fix: The replacement should give one clean phrase (e.g. "Source readiness for TransDigm..."), or the handoff should not open with the module code.
3. **Medium · narrative** (Auditor, New reader)
   - Where: Line 3: "Scope is to inventory the pinned source pack, freeze the effective source set, and state readiness and the source-to-module map for CP-1, CP-1A, CP-DR, ... without any credit conclusion."
   - Problem: This is pipeline vocabulary ("pinned source pack", "freeze the effective source set", "source-to-module map") and the instruction sent to the model, shown to a portfolio manager. It runs to roughly 70 words in one sentence and lists 12 module names, so it tells a credit reader nothing about the issuer.
   - Fix: Fold Request out of the reader view, or reduce it to one plain sentence on which filings were checked for TDG as of 30 September 2024.
4. **Medium · narrative** (Auditor, Saboteur)
   - Where: Line 132: "CP-1 should run next on the effective source set... CP-DR may run in parallel for quotes, ratings and peers."
   - Problem: Next module gives scheduling orders to the orchestrator ("should run next", "may run in parallel", shouty "DO NOT RUN"). It is not reader language, and the reader cannot act on it after the run has finished.
   - Fix: Hide Next module from the Modules page, or restate it as a reader limitation (e.g. which sources later sections rely on, and for which periods).
5. **Low · visual** (New reader)
   - Where: CP-0_s-130.png, bottom (y~1880-1940) and CP-0_s-1.png top (y~195-280): Request and Next module paragraphs
   - Problem: Two plumbing paragraphs bracket the module page as full-width body text, styled the same as analytical prose, so nothing marks them as run metadata. Request sits first, ahead of the content the reader came for, and Next module is the last thing they read.
   - Fix: Show run metadata in a muted, collapsible 'Run notes' block apart from the analysis, the way the VMO2 reference keeps the reading order to analysis first.

### Sources

Kind: prose/table · handoff lines 5-17 · verdict **BLOCK**

- Narrative: The Sources section is a reference table plus one sentence, so the bottom-line-first order does not apply. Its wording still leaks pipeline language ("handoffs", "producer modules", "context", "Role in this run") and gives an ambiguous page count for the PDF row.
- Visual: The section has no chart, map or timeline. The three-column table renders cleanly and is legible, but hash and file-name columns no reader can use take most of its width, and the section sits mid-page before the analysis.

1. **High · narrative** (Auditor, New reader)
   - Where: line 16: "Supplied upstream handoffs: none (CP-0 has no producer modules in this run)." Rendered as "Supplied upstream handoffs: none (Source readiness has no producer modules in this run)." (CP-0_s-5.png, just below the Sources table)
   - Problem: The renderer swaps the module code for its name but leaves "handoffs" and "producer modules", which the house standard bans as pipeline vocabulary. A portfolio manager gets nothing from this sentence.
   - Fix: Drop the line from the reader view, or reword it in reader terms, e.g. "This is the first step; it relies only on the filings listed above."
2. **Medium · narrative** (Saboteur)
   - Where: line 13: "Duplicate (PDF reproduction of the FY2024 annual filing); htm filing retained as controlling, 160 pages"
   - Problem: "160 pages" comes straight after "htm filing retained as controlling", so it reads as the page count of the htm filing. Line 9 gives that filing 181 pages, so the same table appears to give two page counts for one document.
   - Fix: Put the page count next to the document it describes, e.g. "PDF reproduction, 160 pages, of the FY2024 annual filing; the htm filing is the controlling source".
3. **Medium · narrative** (New reader, Saboteur)
   - Where: line 14: "| context | f7b95e1ff471b475… | User run settings only; not issuer evidence |"
   - Problem: An internal settings file called "context" sits in the source list next to SEC filings, with a hash. This is pipeline material, not a source, and listing it among the sources blurs which evidence the analysis actually rests on.
   - Fix: Leave run settings out of the reader's Sources table; if they must be disclosed, add one plain sentence such as "Analyst run settings (as-of date, fiscal years) are not issuer evidence."
4. **Medium · visual** (New reader, Auditor)
   - Where: Sources table, sha256 column and Source column (CP-0_s-5.png, roughly y=215-710, x=300-1160 in the displayed image)
   - Problem: A column of 64-character hashes takes up about 40% of the table width, and the Source column shows raw machine file names ("…_tdg-20240930.htm.jsonl", "…a841225transdigmgroupbookm.pdf"). A credit reader cannot use either, and they squeeze the one useful column, Role, into narrow wrapped lines.
   - Fix: Name each document in reader terms ("10-K, FY ended 30 Sep 2024, filed …"), move the hashes and file names to the Evidence page or a folded detail, and give the Role column the width.
5. **Low · narrative** (New reader)
   - Where: line 7: "| Source | sha256 | Role in this run |" and line 10: "Retained: Q3 FY2024 quarterly filing (quarter and 9M YTD)"
   - Problem: The column headers "sha256" and "Role in this run", and the bare status word "Retained", are process language. They tell the reader how the run handled the file, not what the document is or what it may be used for.
   - Fix: Use headers such as "Document", "Period covered" and "Use in this analysis".
6. **Low · visual** (Auditor)
   - Where: Page order in the 'On this page' nav and the body (CP-0_s-5.png, left nav y=350-660; Sources heading at y=198)
   - Problem: Sources is placed after Request and before the analysis sections (Effective source set, Source assessment, …), so the reader meets a hash table before any judgement on readiness, and the reference list falls in the middle of the page instead of at the end.
   - Fix: Render Sources after the findings sections, as the VMO2 reference does, so the page runs judgement first and references last.

### Source assessment

Kind: prose/table · handoff lines 36-46 · verdict **BLOCK**

- Narrative: The table is honest and does not drop limitations or missing values ('blanks are not zero'). But it speaks to later modules rather than the reader: internal file names, a 'context' row, and imperative cells such as 'Must not replace as-of figures'. It also implies quarterly coverage that only the cover pages support.
- Visual: There is no chart in this section. The one visual is an 8-column table that overflows the content pane: the Source column is clipped at the right edge, and narrow columns wrap to one or two words per line, making the rows very tall.

1. **High · visual** (Auditor, New reader)
   - Where: Source assessment table, Source column; screenshot CP-0_s-36.png, x 1240-1440, y 270-1160 (crop at /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-0-003-a.png)
   - Problem: The table is wider than the content pane, so the Source column is cut off at the right edge mid-identifier, e.g. 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 1–181' shows as 'TDG_2024-09-30_10-I / 000083_tdg-20240930 / 181'. Nothing on screen shows the column scrolls. The house standard puts source references in exactly this column, so the reader cannot read them.
   - Fix: Fit the 8-column table to the pane, for example by wrapping long identifiers, narrowing or merging columns, or showing a visible horizontal-scroll cue, so every Source cell is fully readable without leaving the page.
2. **Medium · narrative** (New reader, Auditor)
   - Where: line 40: 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 1–181'; line 45: '| context | User settings | Not issuer evidence | ... | Run parameters |'
   - Problem: Sources are shown as pipeline file names with SEC accession numbers and a '.htm.jsonl' extraction suffix, and a row called 'context' for 'User settings' / 'Run parameters'. This is pipeline vocabulary that a credit committee reader cannot interpret, and it makes the Source column long enough to cause the clipping above.
   - Fix: Give readers a document title such as '10-K FY2024 (filed Nov-2024), p. 1–181', and rename or drop the run-settings row so internal file names stay off the page.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: line 41: 'Identity confirmed; available for quarter and YTD figures' with Source '...tdg-20240629.htm.jsonl, page 1' (same pattern at line 42)
   - Problem: The Coverage column reads as if the quarterly filings support quarter and YTD figures, but the cited basis is page 1 only. Only the cover page was checked, so a reader could overrate how much quarterly evidence was actually read.
   - Fix: Say plainly that only identity was checked (cover page) and that no quarterly figures were taken from these filings.
4. **Medium · narrative** (Auditor, New reader)
   - Where: line 43: 'Must not replace as-of figures'; line 44: 'Duplicate; not used as fallback'; line 41: 'quarter versus YTD distinction must be preserved'
   - Problem: The Limitations and Coverage cells are written as orders to later modules, not as limits a reader should weigh. This is pipeline-instruction wording leaking into the issuer report.
   - Fix: Phrase each cell as a reader-facing limitation, e.g. 'Post as-of: used for subsequent events only'.
5. **Medium · visual** (New reader, Auditor)
   - Where: Source assessment table; screenshot CP-0_s-36.png, y 250-1260 (Limitations and Coverage columns)
   - Problem: With 8 columns squeezed into the pane, the Limitations column wraps to one or two words per line (e.g. 'Credit / agreement / and / indentures'). Rows become 150-250 px tall, and the 6-row table fills about 1,050 px of a 2,400 px page.
   - Fix: Cut or merge low-value columns (for example Currency/unit, which is 'USD millions' in five of six rows) so Limitations gets enough width to read as a sentence.
6. **Low · narrative** (Saboteur)
   - Where: lines 38-45, section opens directly with the table '| Source | Document family and authority | Entity / perimeter | ...'
   - Problem: The section has no lead sentence. The reader has to work out the judgement that matters (one audited controlling filing, legal documents missing) from eight dense columns.
   - Fix: Open with one sentence saying which source controls and what material gap the table shows.
7. **Low · visual** (New reader)
   - Where: first-column 'Basis' chip under each source name (e.g. 'FY2024 annual filing (htm) Basis'); screenshot CP-0_s-36.png, x 370-420, y 395, 695, 835, 1010, 1150, 1330
   - Problem: Each row has an unexplained grey 'Basis' label next to the source name, even though the row already has a Source column. Its purpose is unclear, and it looks like stray text.
   - Fix: Remove the Basis chip from table rows that already have a Source column, or label it so its action is clear.

### Conflicts and duplicates

Kind: prose/table · handoff lines 85-94 · verdict **CONCERNS**

- Narrative: The section is a provenance table written in pipeline vocabulary ("pinned jsonl hash", "downstream") with its only judgement placed after the table and limited to "pages reviewed", so the reader is not told up front whether any conflict affects the credit view.
- Visual: The three-row table renders cleanly with no overlap or clipping. Its weaknesses are the raw file-identifier Source column, which wraps mid-token and takes a quarter of the width, and an unstyled "Basis" label under each item name that reads as stray text.

1. **High · narrative** (Auditor, New reader)
   - Where: Handoff line 90: "The htm annual filing text names an underlying htm sha256 different from the pinned jsonl hash | Pinned jsonl hash controls this run; the internal hash describes the original htm"; line 91: "downstream should cite the precise figure"
   - Problem: The rows use pipeline language the house standard keeps off the page: "pinned jsonl hash", "sha256", "htm", "controls this run" and "downstream" (which means other modules). A portfolio manager cannot tell what this row means or whether it matters to credit.
   - Fix: Write each row in reader terms, e.g. "the 10-K and the PDF annual report are the same document; the 10-K is used". Drop the file-hash row or move it to the Evidence page, and remove instructions aimed at other modules.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: Handoff line 93: "No conflict between a management claim and a filed statement was found in the pages reviewed." (sits after the table)
   - Problem: The judgement comes last, after the table, which is the reverse of the judgement-first order. "in the pages reviewed" also limits the scope without saying which pages were reviewed, so a reader may take the clean result as covering the whole filing.
   - Fix: Open the section with a one-line bottom line: no conflict that affects the credit view, with the review scope stated. Put the table after it.
3. **Medium · narrative** (Saboteur)
   - Where: Handoff line 91: "Liquidity table shows USD 163 million available; debt section states USD 162.5 million | Same fact at different precision"
   - Problem: The row presents USD 162.5 million as securitization availability at 30 September 2024 but does not say this capacity was fully drawn on 2024-10-16 (line 103). A reader skimming this table could count it as headroom that was already gone after the period end.
   - Fix: Add the date basis (as at 2024-09-30) to the row and note that the capacity was drawn after the period end, or point to that event.
4. **Medium · visual** (New reader, Auditor)
   - Where: Conflicts and duplicates table, Source column, shots2/CP-0_s-85.png crop (340,220)-(1400,580) saved as tmp/CP-0-006-a.png
   - Problem: The Source column prints raw file identifiers such as "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 1". They wrap mid-token ("tdg-" / "20240930") and take about a quarter of the table width. The ".jsonl" suffix is an internal format the reader does not need.
   - Fix: Show a short reader label (e.g. "10-K FY2024, p. 55, 62") with the full identifier on hover or on the Evidence page.
5. **Medium · visual** (New reader)
   - Where: Item column, each row, tmp/CP-0-006-a.png: "Duplicate annual filing / Basis", "Underlying file hash / Basis", "Securitization availability rounding / Basis"
   - Problem: A grey "Basis" label sits under every item name with no affordance. It reads as part of the item text, and in the wrapped third row it becomes a third line. It also repeats what the Source column already gives.
   - Fix: Show Basis as a distinct control (icon or button style) aligned the same way in every row, or drop it where the row already has a Source column.
6. **Low · narrative** (New reader)
   - Where: Handoff line 89: "PDF annual report reproduces the htm annual filing (same cover, file number, MD&A text) | htm retained as controlling; PDF not used as fallback"
   - Problem: The row never says why the duplicate matters to credit. With no effect on the view, it is provenance housekeeping that dilutes a section the reader expects to flag real disagreements.
   - Fix: Add a short effect note ("no effect on figures") or fold the duplicate and hash rows into one housekeeping line under the bottom line.

### Calculations

Kind: prose/table · handoff lines 108-116 · verdict **BLOCK**

- Narrative: The section is process reporting, not credit narrative: it shows script names and pipeline terms to the reader, implies a manual validation with no stated scope, and labels a by-design omission as \"Not calculable\".
- Visual: There is no chart, map or timeline in this section; the full-width paragraph and the sparse three-column table with code-styled IDs take up space and add little.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 110: "The helper scripts the method names (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py and other scripts) were not run in this transport"; also rendered in CP-0_s-108.png, crop y~1150-1230
   - Problem: Shows the reader script filenames, including pipeline vocabulary ("handoff" in validate_handoff.py), plus internal terms like "transport", "the method", "pinned hashes" and "page locators". That breaks the house rule against pipeline language, and a portfolio manager cannot act on any of it.
   - Fix: Hide the tooling detail from the reader, or restate it in one plain sentence (e.g. that automated source checks were not run and the source files were checked by hand).
2. **Medium · narrative** (Saboteur)
   - Where: Line 110: "their structural checks were done by hand against the pinned hashes and page locators" and line 115: "Not run: unavailable in this transport; checks performed manually"
   - Problem: This says the source checks passed when the automated checks did not run. The manual check has no stated scope and no outcome, so a committee could treat the source set as validated with nothing behind that view.
   - Fix: Say which checks were done by hand and what they found, or call the source validation a limitation rather than a completed check.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 114: "| C0 | Numeric calculations | Not calculable: not permitted at CP-0; none performed |"
   - Problem: "Not calculable" tells the reader the figures could not be computed, which hints at a problem with the data. The real reason is that this stage is not allowed to calculate ("not permitted"). The status contradicts itself and could make a reader doubt figures that are fine.
   - Fix: Use one accurate status, such as "Not performed at this stage by design", with no wording that suggests the data is defective.
4. **Medium · narrative** (New reader)
   - Where: Lines 108-116, whole "## Calculations" section
   - Problem: The section adds nothing to the credit view: one paragraph and a two-row table say nothing was calculated, and the reader still has to scroll past them between Events and Gaps. Its first sentence explains the method instead of saying what this means for the reader.
   - Fix: Shrink it to one line (e.g. "No figures were calculated; all values above are quoted from the filings"), or fold it into the module's limitations.
5. **Medium · visual** (New reader, Auditor)
   - Where: Calculations paragraph, CP-0_s-108.png crop (330,1120)-(1410,1360), saved as tmp/CP-0-008-a.png
   - Problem: The paragraph runs across the full ~1080 px content width, about 180 characters per line, which is well past a comfortable line length and makes three lines of process text hard to scan. Unlike the neighbouring sections, it also has no Basis chip, so the claim that checks were done by hand points to no evidence.
   - Fix: Limit prose to a readable width (about 75-90 characters) and give the paragraph a Basis line, or cut it as suggested above.
6. **Low · narrative** (Auditor)
   - Where: Line 112-115 table IDs "C0", "C1"
   - Problem: The row IDs C0 and C1 are internal labels that nothing else on the page uses, so the reader gains nothing from them.
   - Fix: Remove the ID column, or use IDs only where something else on the page refers to them.
7. **Low · visual** (Auditor)
   - Where: C0/C1 table, tmp/CP-0-008-a.png
   - Problem: The table is three columns wide with a lot of empty space, and the ID column is set in a small, grey monospace that reads as code. A boxed table is a heavy layout for two status lines.
   - Fix: Show the two statuses as plain inline text, or as a compact two-column list without the code-styled ID column.

### Effective source set and identity

Kind: prose/table · handoff lines 28-35 · verdict **CONCERNS**

- Narrative: The two paragraphs keep sources out of the sentences, with each reference in its Basis line. But the first paragraph is a long inventory with no judgement up front, pipeline wording such as "downstream", "htm" and "extract" reaches the reader, and the non-guarantor gap is stated without saying whether it matters.
- Visual: This section has no chart, map or timeline. Its on-page layout is two full-width prose paragraphs whose roughly 175-character lines and faint inline Basis markers slow reading; the heading and the section's place in the page order are fine.

1. **Medium · narrative** (Saboteur, New reader)
   - Where: line 30: "The controlling annual filing identifies the registrant as TransDigm Group Incorporated, a Delaware company listed on the New York Stock Exchange under TDG, for the fiscal year ended September 30, 2024; the two FY2024 quarterly filings..."
   - Problem: The paragraph has no judgement up front. It opens with a cover-page inventory, and its one real point, that the PDF was treated as a duplicate without a page-by-page check, comes at the end of a sentence of about 65 words. The two-sentence paragraph runs to about 115 words.
   - Fix: Open with the conclusion (the identity is confirmed and the FY2024 annual filing is the controlling source; the PDF is an unverified duplicate), then give the period coverage in short sentences.
2. **Medium · narrative** (New reader, Auditor)
   - Where: line 33: "The entity boundary matters for every downstream claim"; line 30: "as the htm annual filing ... its last pages extract as blank"; heading line 28: "Effective source set and identity"
   - Problem: Pipeline and file-processing wording reaches the reader: "downstream claim", "htm", "extract as blank" and the heading's "effective source set". A portfolio manager reads these as internal processing language, not credit language.
   - Fix: Use reader terms, for example "every later conclusion", "the SEC annual filing", "the PDF's final pages are blank" and a heading such as "Sources used and issuer identity".
3. **Medium · narrative** (Saboteur)
   - Where: line 33: "That combined summary is usable for structural-subordination work, but the list of obligors sits in a guarantor exhibit that was not supplied, so non-guarantor identity remains a gap."
   - Problem: The passage says the non-guarantor perimeter is unknown but does not say whether that gap is material. It gives no sense of the non-guarantors' share of assets or earnings from the combined summary, so a committee member cannot tell whether structural subordination is a real risk or a footnote.
   - Fix: State what the combined summary does or does not show about the non-guarantor share, with its period and unit, or say plainly that it cannot be sized.
4. **Medium · visual** (New reader, Auditor)
   - Where: Section prose block, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots2/CP-0_s-28.png, crop x330-1440 y220-450 (scratchpad/tmp/CP-0-002-a.png)
   - Problem: Each line runs the full roughly 1,100 px content width in small type, about 170-180 characters per line. That is far past a comfortable measure, so the dense first paragraph reads as a five-line wall.
   - Fix: Limit prose width to about 75-95 characters per line (for example a max-width on module paragraphs) while tables keep the full width.
5. **Low · narrative** (Auditor)
   - Where: line 30: "full containment was not verified page by page, its last pages extract as blank, and no shareholder letter or image content was found or inspected"
   - Problem: "Found or inspected" merges two different states, absent and not looked at. The reader cannot tell whether the PDF has no letter or whether nobody checked.
   - Fix: Say separately whether a shareholder letter or images exist and whether they were reviewed.
6. **Low · visual** (Auditor)
   - Where: Inline "Basis" chips at the end of both paragraphs, same crop (scratchpad/tmp/CP-0-002-a.png)
   - Problem: The "Basis" marker is pale grey text attached to the last word of the paragraph. Its contrast is low and nothing marks it as clickable, so the paragraph's source is easy to miss. There is also almost no gap between the two paragraphs.
   - Fix: Give the Basis marker enough contrast and a visible link or chip style, and add normal paragraph spacing.

## Business & governance (CP-1A)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-1A/1483b229586860fc7840722ed8b33b40936e2427d7445526bc6e8cf57b11fe9d/1.response.md`

### Events: Issuer history

Kind: timeline · handoff lines 92-107 · verdict **BLOCK**

- Narrative: The facts I checked match the 10-K (page 53 refinancing amounts and dates). But the history leaves out both special dividends and the March repricing, refers them to another module in pipeline language, and fills the Status column with source fragments, not judgement.
- Visual: The timeline drawing squeezes 31 years onto one unlabelled strip, so nine fiscal 2024 events merge into one blob. The table is legible, but raw file-name sources, wrapped dates, a Basis chip that repeats the Source column and an empty Published column crowd it.

1. **High · narrative** (Saboteur, New Reader (promoted))
   - Where: line 98: "the 2023-11-27 dividend is recorded in the source readiness lane"; line 105: "Funds the special dividend declared the same day and paid 2024-10-18, both recorded in the source readiness lane"
   - Problem: Both special dividends are left out of the issuer history and pointed to another module (USD 35.00 in November 2023, USD 75.00 in September 2024, about USD 4.3bn in total, the year's main credit-negative events). So did the 2024-03-22 repricing and Tranche K extension (line 100). A reader of this timeline sees the debt raised but not where the money went.
   - Fix: List the dividend declaration and payment events, and the March 2024 repricing, as their own rows with amount and date, so the history is complete on this page.
2. **High · narrative** (Auditor, New Reader (promoted))
   - Where: line 98 / 100 / 105: "recorded in the source readiness lane"
   - Problem: "Source readiness lane" is pipeline vocabulary that refers to another module's internal structure. It is shown on screen in the Credit relevance column, which breaks the house rule against module and pipeline wording.
   - Fix: Remove the cross-module pointers from Credit relevance and keep only the creditor consequence.
3. **High · visual** (Saboteur, Auditor (promoted))
   - Where: Timeline panel, 'Issuer history' row; /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-020-a.png (crop of CP-1A_timeline.png, x 320-1440, y 200-330)
   - Problem: The timeline is a single unlabelled strip that runs from 1993 to 2024: one hollow box at 1993, one dot for 2022, and nine 2023-24 events drawn as one solid blue blob at the right edge. It has no event labels, no intermediate ticks and no legend, so the reader cannot tell any fiscal 2024 financing, acquisition or dividend step apart. It adds nothing beyond the table and looks like a rendering fault.
   - Fix: Scale the axis to the dense period, with the 1993 origin shown as a break or marker, and label or space each event so every fiscal 2024 step can be seen and read.
4. **Medium · narrative** (New Reader)
   - Where: line 100: "Historical — redeem all of its outstanding notes"; line 102: "Historical — repriced and amended and extended"
   - Problem: The Status column repeats 'Historical' on every row and adds a verbatim source fragment that is often ungrammatical ('redeem all of its'). It reads as extraction residue, not a status.
   - Fix: Use a plain status vocabulary (Completed / Authorised / Subsequent to as-of date) or drop the column.
5. **Medium · narrative** (Saboteur)
   - Where: line 106: "| 2024-Q4 | quarter | — | Fiscal first quarter 2025: 252,800 shares repurchased for USD 316 million"; timeline axis end '2024-12-31'
   - Problem: Calendar 'Q4 2024' and 'fiscal first quarter 2025' are mixed in one row. This post-as-of event (after 2024-09-30) is not marked as subsequent in the date or the chart, and the axis runs past the as-of date without a marker. A reader can take it as within-period.
   - Fix: Mark events after 30 September 2024 as subsequent in the date cell and on the chart (e.g. an as-of line), and use one period convention.
6. **Medium · visual** (New Reader, Auditor (promoted from Low))
   - Where: Events: Issuer history table, Source column and Event date column; CP-1A_s-92.png, y≈215-1240 (display), table spanning x 297-1158
   - Problem: Every row repeats the 60-character raw file name 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page N'. Each wraps to four lines and takes the widest column. The Event date column is so narrow that ISO dates split mid-string ('2022-01-' / '27'). Each date also carries a 'Basis' chip that repeats the Source column.
   - Fix: Show sources as a short reader citation such as '10-K FY2024, p.53', widen the date column so dates do not wrap, and drop either the Basis chip or the Source column.
7. **Medium · visual** (New Reader)
   - Where: line 94 header: "| Event date | Date precision | Published | Event | Status |"; CP-1A_s-92.png table header
   - Problem: The 'Published' column is '—' in all 11 rows, so it is empty. 'Date precision' (year/day/quarter) is pipeline metadata. Together they take about a fifth of the table width and give the reader nothing.
   - Fix: Drop columns that are empty throughout and fold precision into the date itself (e.g. '1993', 'Q4 2024').
8. **Low · visual** (Auditor)
   - Where: Timeline axis label '1993-01-01' in CP-1A-020-a.png
   - Problem: The axis start shows a day-precision date, 1993-01-01, for an event the table records only to the year. That is false precision.
   - Fix: Label year-precision anchors as '1993'.

### Map: operating model to credit

Kind: map · handoff lines 120-130 · verdict **BLOCK**

- Narrative: The six links are traceable and the arithmetic checks (52.56%, USD 1,880m, USD -2,505m, 69%, about 40%). But the evidence-category labels overstate how certain the derived claims are, the table has no source references, and its jargon and sign conventions slow a credit reader.
- Visual: The map is visible, not folded, but cannot be read: node text is truncated and split mid-number, the edge labels are clipped and show evidence categories instead of the relationships, and the table is repeated in monospace link styling.

1. **High · narrative** (Saboteur, Auditor)
   - Where: L128 'New secured debt of USD 3,000 million | Funded about 69.00% of the September special dividend | Documentary Fact'; L127 'Excess cash goes to equity before lenders | Management Language'
   - Problem: The 69.00% is an analyst calculation (3,000 / 4,348), yet the row labels it Documentary Fact, although the evidence cell says the dividend was 'funded by new secured debt and cash'. 'Excess cash goes to equity before lenders' is an inference from the stated hierarchy, yet it is labelled Management Language. The labels overstate how certain the claims are.
   - Fix: Label derived or inferred rows Analyst Interpretation and state the calculation basis for the 69%.
2. **High · visual** (Auditor, New reader)
   - Where: Maps panel, 'Operating model to credit' drawing: CP-1A_maps.png crop x340-1400, y1250-1560 (scratchpad/tmp/CP-1A-022-a.png)
   - Problem: Every node label is cut off with an ellipsis or broken mid-word ('Proprietary, aftermark et-heavy', 'Funding gap of USD -2, 505 million met by new...', 'Defense sales of USD 3 ,143 million', 'about 4 0% of sales'). The edge labels run over the node borders and are clipped ('alyst Interpretati', 'Management Languag'), so the reader cannot read figures or conclusions from the drawing.
   - Fix: Wrap node text at word boundaries, never split a number, size the nodes to fit their full label, and leave enough gap between nodes for the whole edge label.
3. **High · visual** (Saboteur, New reader)
   - Where: Maps panel, 'Operating model to credit' drawing: the edges are labelled 'Management Language', 'Documentary Fact', 'Analyst Interpretation' (CP-1A-022-a.png)
   - Problem: The arrows carry the evidence category instead of the relationship ('Supports pricing power', 'Fell short of acquisitions and dividends paid'), so the drawing does not say how the operating model leads to the credit outcome. That causal reading is the only reason to have the map.
   - Fix: Label each arrow with its Relationship text and show the evidence category by line style plus a legend.
4. **Medium · narrative** (Auditor)
   - Where: L122 '| From | Relationship | Edge type | To | Evidence |' (no Source column; e.g. L125 'Capex USD 165 million against operating cash flow USD 2,045 million')
   - Problem: The table cites figures but has no Source column and no filing or page reference. The reader cannot trace the USD 2,347 million, USD 2,038 million or USD 4,348 million amounts without opening the Fact register.
   - Fix: Add a Source column (filing and page) to each row, as the Fact register directly below does.
5. **Medium · narrative** (New reader)
   - Where: L122 column header 'Edge type' with values 'Management Language', 'Documentary Fact', 'Analyst Interpretation'
   - Problem: 'Edge type' is graph and pipeline vocabulary, and the capitalised evidence categories are internal register labels the page never explains to a portfolio manager.
   - Fix: Rename the column to something like 'Basis of link', use plain-language values (stated by management / reported figure / our judgement), and explain them once.
6. **Medium · narrative** (Saboteur)
   - Where: L126 'Funding gap of USD -2,505 million met by new debt'
   - Problem: A 'gap' with a negative sign is a double negative: a reader can take it as a surplus, or be unsure which way the sign runs. The period (fiscal 2024) is also missing from the node itself.
   - Fix: Write 'Fiscal 2024 funding shortfall of USD 2,505 million, met by new debt'.
7. **Low · narrative** (Saboteur)
   - Where: L124 'EBITDA As Defined margin of 52.56%'; L128 'Funded about 69.00%'
   - Problem: Two-decimal precision on a non-GAAP margin, and 'about' paired with 69.00%, suggests more exactness than exists. The 52.56% is also not labelled as a management measure for fiscal 2024.
   - Fix: Use '52.6% (fiscal 2024, management's adjusted measure)' and 'about 69%'.
8. **Low · visual** (New reader)
   - Where: CP-1A_s-120.png y~190-610 (section table) vs CP-1A_maps.png y~1580-2080 ('Edges of the map, as stated')
   - Problem: The same six-row table appears twice on the Modules page. The Maps-panel copy sets From/To in monospace and every Relationship as an underlined link, which reads like code and is denser than the section copy.
   - Fix: Show the table once below the drawing, in the page's normal proportional type, with relationships as plain text.

### Analytical appendix — complete canonical registers

Kind: register appendix · handoff lines 131-197 · verdict **BLOCK**

- Narrative: This register appendix is data and owes no judgement-first order, but its reader-facing cells carry pipeline routing (the Consumers table), an internal tool name with unscaled scores, and code-style enums and cross-reference IDs a credit reader cannot resolve.
- Visual: The assigned screenshot CP-1A_s-131.png shows the page top because the appendix heading is not rendered and has no anchor. In my own render at 1440 px (/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-023-s-133.png), the Governance register's Source column is cut off, and long .jsonl file names make the Fact register tall and heavy. Not verified: whether a horizontal scrollbar appears in a non-headless browser with scrollbars always shown, and how the empty Basis buttons behave when clicked.

1. **High · narrative** (New reader, Auditor (promoted))
   - Where: Consumers table, lines 183-196: "| CP-0 | Complete (producer) | Nothing further; events recorded in its lane are referenced, not repeated"; "Canonical KPIs must treat accrued dividend"; "Use method defaults"; "Rely on legal module bounds"; "Supply prior case"
   - Problem: The whole table is routing between pipeline modules. Module codes are replaced by page names on screen ("Source readiness", "Financial foundation"), but "producer", "canonical", "fact pack", "Gaps G-list" and the instructions to other modules are pipeline vocabulary that a credit committee reader cannot use.
   - Fix: Keep the Consumers routing table off the reader's Modules page, or reduce it to a reader-facing list of open evidence gaps.
2. **High · narrative** (Auditor, New reader (promoted))
   - Where: line 163: "The score_governance tool returned Shareholder extraction risk 5, Leverage tolerance 3, Acquisition appetite 3, other dimensions Not Scorable, composite Not Scorable ... tool scoring does not certify the evidence."
   - Problem: This sentence names an internal tool and gives scores with no scale or direction (is 5 the worst?). It then closes with a disclaimer that undercuts the scores, so the reader cannot tell whether governance risk is high or merely tool-flagged.
   - Fix: State the governance risk in reader terms with its scale (for example, "extraction risk 5 of 5, highest"), say why the composite could not be scored, and drop the tool name.
3. **High · visual** (Saboteur, Auditor (promoted))
   - Where: Governance and behaviour register table, in my own render /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-023-a.png (crop of CP-1A-023-s-133.png, y 1640-2300). The DOM has 9 header cells ending in "Source" (handoff line 157).
   - Problem: At 1440 px the table ends at "Evidence quality". The Source column, which is the only place this register's references live under the house rule, is pushed off the right edge with no scroll cue, so the reader sees "High" evidence-quality ratings with no visible source.
   - Fix: Fit all nine columns, for example by narrowing Kind/Topic or wrapping Source, or show a visible horizontal-scroll affordance so the Source column can always be seen.
4. **Medium · narrative** (New reader, Auditor (promoted))
   - Where: line 159-161: "| G1 | behaviour_flag |" / "| G2 | governance_topic |"; line 175: "(calculation K18)"; line 178: "Conflict X1 does not change the direction"; line 148: "| F12 | Transaction | Live deal terms in run settings | Insufficient Information | context |"
   - Problem: Reader cells contain code-style enums (behaviour_flag), internal cross-reference IDs (K18, X1) and run-configuration wording ("run settings", Source "context"). A reader without the pipeline cannot resolve any of these.
   - Fix: Use plain labels ("Behaviour flag", "Governance topic"), say what K18 and X1 stand for in words, and phrase F12 as "no pending transaction terms were supplied".
5. **Medium · visual** (New reader)
   - Where: Fact register Source column, lines 137-153: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 4" repeated in 15 of 17 rows; render crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-023-b.png
   - Problem: Every source is a raw extraction file name with an accession number and a .jsonl suffix. Each one wraps to three lines and roughly doubles the row height, and "page 164" of a .jsonl file does not lead the reader to a page of the filing.
   - Fix: Show a short document label (for example, "FY2024 10-K, p. 164") and keep the file identifier in the link or tooltip.
6. **Medium · visual** (Auditor, Saboteur)
   - Where: Handoff line 131 heading "### Analytical appendix — complete canonical registers". There is no element with id s-131 in the rendered DOM (/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-023.dom.html). The "On this page" list goes from "Map: operating model to credit" straight to "Fact register".
   - Problem: The appendix heading is dropped, so the registers flow straight on from the narrative maps with nothing marking them as reference material. Headings also jump from h3 to h5. The assigned screenshot CP-1A_s-131.png consequently shows the page top, not this section.
   - Fix: Render a plain appendix heading (for example, "Appendix: registers", without "canonical") at the correct heading level so it has an anchor and an entry in On this page.
7. **Low · narrative** (Saboteur)
   - Where: lines 152-153: "| F17 | Operating model | Ratio of earnings to fixed charges 2.7x in FY2024 (FY2023 also disclosed)" followed by "| F16 | Timeline |"
   - Problem: F17 comes before F16. The F17 row also says FY2023 is "also disclosed" without giving the value, so the comparison it implies is missing.
   - Fix: Order the IDs and give the FY2023 ratio, or state that it was not extracted.
8. **Low · visual** (New reader)
   - Where: "Basis" buttons under every row ID in the Fact, Governance, Conflicts, Credit translations and Consumers tables (DOM shows data-basis="[]"; the Consumers rows read "Source readiness Basis"), crop CP-1A-023-b.png
   - Problem: Each row has a Basis control that duplicates the row's own Source column and carries an empty basis list. In the Consumers table it runs into the consumer name and adds visual noise.
   - Fix: Show the Basis control only where it adds a reference not already in the row.

### Sources

Kind: prose/table · handoff lines 5-18 · verdict **BLOCK**

- Narrative: The Sources section has the right content and is in the right place, but in L13 and L17 it speaks in pipeline language ("handoff", "this module", "context", "run settings") and names documents by internal file names instead of titles and periods.
- Visual: There is no chart; the two tables render cleanly and nothing is clipped, but the sha256 column takes most of the width and makes the Source names wrap over three lines, and the second table repeats the same value in two columns.

1. **High · narrative** (Auditor, New reader)
   - Where: L13 "| Supplied handoff | Module | sha256 |" and L17 "were not relied on by this module (the annual filing controls and the PDF is a duplicate per the source readiness handoff)"
   - Problem: Pipeline words reach the reader: the table header says "Supplied handoff" and the note says "this module" and "source readiness handoff". The house standard bans "handoff" as reader language, and a PM does not know what a "module" or a "handoff" is.
   - Fix: Rename the second table and reword the note in reader terms (e.g. "Prior analysis relied on: Source readiness review"; "not used here because the annual report on Form 10-K controls and the PDF duplicates it").
2. **High · narrative** (New reader, Auditor)
   - Where: L11 "| context | f7b95e1f... | Run settings only; not issuer evidence; deal terms blank |"
   - Problem: A pipeline input called "context" is listed as a source even though the text says it is not issuer evidence. "Run settings" and "deal terms blank" are internal wording, and a reader can take "deal terms blank" to mean a deal exists with missing terms.
   - Fix: Take the run-settings row out of the reader's Sources table, or state it plainly as "No live transaction was supplied for this review".
3. **Medium · narrative** (New reader, Saboteur)
   - Where: L9 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" and L10 "TDG_2024-12-28_10-Q_0001260221-25-000014_tdg-20241228.htm.jsonl"
   - Problem: Sources are identified by raw internal file names (accession numbers and a .htm.jsonl extension), not document titles. The reader has to work out that the second file is the Q1 FY2025 10-Q, dated after the 30 September 2024 as-of date.
   - Fix: Show each source as a document title with its period (e.g. "Form 10-K, fiscal year ended 30 Sep 2024"; "Form 10-Q, quarter ended 28 Dec 2024 (after the as-of date)"), and keep the file identity as secondary.
4. **Medium · visual** (New reader, Saboteur)
   - Where: Sources table, shot CP-1A_s-5.png crop (340,220)-(1400,670), saved as scratchpad/tmp/CP-1A-011-a.png; sha256 column L7-L11, L13-L15
   - Problem: The 64-character sha256 hashes take about 40% of the table width. That squeezes the Source column, so each filename wraps over three lines, and the hashes mean nothing to a credit reader.
   - Fix: Move the hashes to the Evidence page or a fold, or shorten them, and give the width to a readable document name and the use column.
5. **Low · narrative** (Saboteur)
   - Where: L17 "The two FY2024 quarterly filings and the PDF annual report were not relied on"
   - Problem: The excluded documents are not named or dated, so a reader cannot check which quarters were left out or confirm that the PDF really duplicates the 10-K.
   - Fix: Name the excluded filings by quarter-end date in one line.
6. **Low · visual** (Auditor)
   - Where: Supplied-handoff table, shot CP-1A_s-5.png crop region y≈320-385 (scratchpad/tmp/CP-1A-011-a.png)
   - Problem: The first two columns both show "Source readiness" because the module code was swapped for its name, so the column repeats itself and the row's purpose is unclear.
   - Fix: Collapse it to one named column, or fold the row into the main Sources table as one line.

### Key findings

Kind: reader passage · handoff lines 29-43 · verdict **CONCERNS**

- Narrative: The judgement leads each bullet, but the section uses an overstated 71% 'insulated' share and treats defense inconsistently. It also puts source references in its sentences and packs paragraph-length bullets with ratios the reader cannot check.
- Visual: The section is prose bullets with no chart. Its visual weaknesses are the heavy monospace number chips that break up the text and a narrow column that leaves the right third of the page empty.

1. **High · narrative** (Saboteur, New reader)
   - Where: L31: "commercial and non-aerospace aftermarket sales of USD 2,487 million and defense sales of USD 3,143 million, so roughly 71% of sales sit in channels that are not tied to new aircraft build rates"
   - Problem: Defense sales include defense OEM content, which does depend on new military aircraft build rates. The 71% figure (2,487 + 3,143 over 7,940) therefore overstates how much revenue is insulated, and it is the main support for the 'lowers default risk' conclusion. Bullet 3 (L35) then calls defense 'the main end-market exposure', so the same 40% is presented as durable in one bullet and as the main risk in the next.
   - Fix: Count only aftermarket in the insulated share, or say that defense mixes OEM and aftermarket, and reconcile how defense is treated in bullets 1 and 3.
2. **High · narrative** (Auditor)
   - Where: L31: "this is management's characterisation, but the segment table independently shows"; L33: "which the filing itself lists among its risks through government audits and investigations"
   - Problem: References to sources ('the segment table', 'the filing itself') sit inside narrative sentences. The house rule keeps source references in the Basis line only.
   - Fix: State the fact and its standing (for example 'audited segment data show…', 'a disclosed risk') and leave the document pointer in the Basis line.
3. **Medium · narrative** (New reader)
   - Where: L31: "Revenue durability is strong and rests on proprietary, sole-source content with long aftermarket tails. Management estimates about 90%..." (bullet of about 110 words)
   - Problem: Each bullet is a full paragraph of 60 to 110 words. Bullets 1 and 4 carry four or five figures plus a mechanism, so the scannable key-findings format becomes a wall of text.
   - Fix: Keep each bullet to a judgement sentence plus at most two supporting figures, and move the remaining figures to the tables below.
4. **Medium · narrative** (Saboteur)
   - Where: L37: "Fiscal 2024 special dividend declarations totalled USD 6,368 million of cash payments ... the September dividend was 69.00% covered by the concurrent USD 3,000 million of new senior secured debt"
   - Problem: 'Declarations totalled ... cash payments' mixes declared and paid amounts. The September dividend amount (the denominator of 69.00%) is never stated in the bullet, and 'covered by debt' turns the usual meaning of coverage upside down. A reader cannot check the ratio and may read it as a comfort metric.
   - Fix: State the September dividend amount and phrase the ratio as 'about 69% funded by the new secured debt', with declared and paid kept apart.
5. **Medium · narrative** (Saboteur, New reader)
   - Where: L41: "the dividend left on 2024-10-18, the remaining securitization capacity was drawn on 2024-10-16 ... cash liquidity falling to USD 3,308 million by 2024-12-28"
   - Problem: The bullet gives no amount for the securitization draw and no starting point for the fall in liquidity (USD 6,261 million at year end appears only in the bottom line). It also lists 10-18 before 10-16, so the size and sequence of the post-period drain is unclear.
   - Fix: Order the events by date, give the amount drawn, and state the fall as 'from USD 6,261 million at 2024-09-30 to USD 3,308 million at 2024-12-28'.
6. **Medium · visual** (New reader, Auditor (promoted from Low))
   - Where: Key findings bullets, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots2/CP-1A_key-findings.png crop x330-1440, y220-900 (/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-013-a.png)
   - Problem: Every figure is set in bold monospace with a dotted underline inside proportional body text. Bullet 1 has six such chips and bullet 4 has four, which breaks the reading rhythm, and 'USD 3,000 million' wraps onto its own line start.
   - Fix: Show figures in the body typeface (tabular numerals) with a subtle link cue, and keep each amount and its unit unbroken.
7. **Low · narrative** (New reader)
   - Where: L33: "EBITDA As Defined rose from 51.56% of sales"; L39: "term loan margins were cut to Term SOFR plus 2.75% and 2.50%"
   - Problem: 'EBITDA As Defined' is the issuer's non-GAAP term and is never explained. The two term-loan margins are not tied to named tranches. Ratios carry two decimals (51.56%, 69.00%), which suggests false precision in a qualitative bullet.
   - Fix: Gloss EBITDA As Defined once as the company's adjusted EBITDA, name the tranches, and round ratios to one decimal or whole percent in prose.
8. **Low · visual** (Auditor)
   - Where: Key findings column, CP-1A_key-findings.png region x330-1440, y220-1150 (full-resolution)
   - Problem: The prose column stops at about x 1010 of a 1390 px content area. The right third of the page is empty beside long bullets, which makes the section taller than it needs to be.
   - Fix: Use the spare width for a margin figure or summary chip, or keep the measure but tighten the bullets so the block is shorter.

### Map: ownership and control

Kind: map · handoff lines 108-119 · verdict **CONCERNS**

- Narrative: The ownership map is a 7-row edge table. It has pipeline wording, an inconsistent guarantor perimeter between two rows, and no stated credit judgement on structural subordination.
- Visual: The Ownership and control drawing is visible and follows the table, but its node labels split mid-word, the guarantee edges merge into one ambiguous arrowhead, and the edge table is repeated in a second monospace, link-styled form in the Maps panel.

1. **High · narrative** (Auditor, New reader)
   - Where: line 112: "Hold the listed common stock; individual percentages not disclosed in the pack" / "Listed on the New York Stock Exchange per source readiness; no holder register supplied"
   - Problem: "per source readiness" names an internal module and "the pack" and "no holder register supplied" are pipeline language about what the run was given. The house rule bars this wording. A committee reader cannot tell whether the holder data is undisclosed by the issuer or just missing from this run.
   - Fix: Say what the issuer discloses (e.g. NYSE-listed; the annual filing gives no holder percentages) and keep any provenance in the Basis line or Sources.
2. **High · visual** (Auditor, New reader)
   - Where: Ownership and control drawing, CP-1A_maps.png crop x340-1400,y220-600 (tmp/CP-1A-021-a.png): nodes read "TransDigm Group Incorp orated", "TD Group Board of Dire ctors", "Domestic Restricted Su bsidiaries"
   - Problem: Node labels wrap at a fixed character count and split words, so three of the six entity names break mid-word. This is the reader's first look at the group structure. Promoted from Medium because two personas caught it.
   - Fix: Wrap node labels only at word boundaries, or widen the nodes, so every entity name reads whole.
3. **Medium · narrative** (Saboteur)
   - Where: line 116: "TransDigm UK | Guarantees 2028 secured notes and subordinated notes" vs line 117: "Same guarantor group across all secured notes as of the filing date"
   - Problem: Line 116 limits TransDigm UK's guarantee to the 2028 secured notes and the subordinated notes. Line 117 says the same guarantor group stands behind all secured notes. The two rows disagree on the guarantee perimeter, and that perimeter decides creditor recovery.
   - Fix: State one consistent guarantor perimeter for each debt class and give the exception explicitly where it applies.
4. **Medium · narrative** (Saboteur)
   - Where: lines 108-118, the whole map table: e.g. line 115 "TransDigm Group Incorporated | Guarantees secured and subordinated notes | Guarantee | TransDigm Inc."
   - Problem: The map lists edges but never gives the credit reading: who issues the debt (TransDigm Inc.), where creditors sit against the operating subsidiaries, and whether any subsidiaries are outside the guarantee. A committee member has to work out structural subordination alone. The notes and term loans do not appear as nodes at all.
   - Fix: Open the map with a one-line judgement on what the structure means for creditor claims, and show the debt instruments or the issuer role on the drawing.
5. **Medium · visual** (New reader, Auditor)
   - Where: Ownership and control drawing (tmp/CP-1A-021-a.png): three dotted 'Guarantee' curves and the parent's 'Guarantee' edge converge on one arrowhead at TransDigm Inc., with two stacked 'Guarantee' labels floating mid-canvas
   - Problem: Four guarantee edges merge into a single arrowhead and the floating labels do not show which curve they belong to. The reader cannot trace which guarantor covers what, and the drawing does not carry the instrument scope that the table gives (e.g. 2028 notes only).
   - Fix: Route the guarantee edges to separate entry points, attach each label to its own line, and put the covered instruments in the label.
6. **Medium · visual** (Auditor)
   - Where: CP-1A_maps.png 'Edges of the map, as stated' table (y≈600-1240) vs CP-1A_s-108.png 'Map: ownership and control' table (y≈230-750)
   - Problem: The same seven-row edge table appears twice on the Modules page in two styles. The Maps panel version uses monospace bold From/To cells and underlined Relationship text that looks like hyperlinks. The duplication and the mixed typography slow the reader and suggest the cells are clickable.
   - Fix: Show the edge table once, beside its drawing, in the page's normal table typography and without link styling on plain text.
7. **Low · narrative** (New reader)
   - Where: line 110: "| From | Relationship | Edge type | To | Evidence |"; panel heading "Edges of the map, as stated"
   - Problem: "Edge type" and "Edges of the map" are graph-tool vocabulary, not credit language. "TD Group" (line 114) is used next to "TransDigm Group Incorporated" and is never defined.
   - Fix: Use reader headings such as "Link" or "Type of link", and give the parent one name throughout.
8. **Low · narrative** (Auditor)
   - Where: line 113: "Annual filing defines TD Group as holding all of the outstanding capital stock of TransDigm Inc."
   - Problem: The Evidence column attributes facts in narrative sentences ("Annual filing defines…", "Filing lists…") instead of keeping the source in a Source column or the Basis line, and it gives no page reference that would let anyone check the claim.
   - Fix: State the fact in the Evidence cell and move the filing and page reference to a Source column or the Basis line.

### Calculations

Kind: prose/table · handoff lines 198-222 · verdict **CONCERNS**

- Narrative: This is a data appendix and owes no bottom-line ordering. Its arithmetic checks (K15 = -2,505; K16 = 69.00%; K18 ≈ 70.9%), but it opens with pipeline language and labels the same USD 4,348 million dividend as FY2024, September and October cash, which conflicts with the 2,038 paid in FY2024.
- Visual: The section has no chart. It is one wide table that is readable but inflated to about 1,200 px by a three-line raw .jsonl filename in every Source cell, with mixed bold-monospace and regular result styling and an orphan 'Basis' chip in each ID cell.

1. **High · narrative** (Saboteur, New reader)
   - Where: L212 "K9 | FY2024 special dividend declarations, cash payments | 2,020 + 4,348 | USD 6,368 million" vs L215 "Year-end cash less October dividend payments ... 6,261 − 4,348" vs L219 "New secured debt as share of September dividend payments | 3,000 / 4,348"
   - Problem: The same USD 4,348 million is labelled a FY2024 cash payment (K9), an October payment (K12) and a September payment (K16). K15 then uses a different 'dividends paid FY2024' of 2,038. A reader can't tell how much cash left in FY2024 and how much in FY2025, and the 6,368 figure reads as cash paid in the year.
   - Fix: Label 4,348 consistently as 'declared September 2024, paid October 2024 (FY2025)', name K9 'declared in FY2024', and say how it relates to the 2,038 paid in FY2024.
2. **High · narrative** (Auditor, New reader)
   - Where: L200 "Helper scripts named by the method (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py) were not run in this transport; their arithmetic ... done with the calculate tool and by hand."
   - Problem: This sentence is pipeline vocabulary (script names, 'transport', 'calculate tool', 'method') and it sits on screen as the section's opening sentence. The reader gets nothing from it.
   - Fix: Delete the sentence, or cut it to a limitation in reader terms ('figures recomputed from the filing; not independently re-run'), and keep only the units-and-period line.
3. **Medium · narrative** (Saboteur, Auditor)
   - Where: L208 "52.56% (0.525566750629722921914357682619647355)" and L209 "51.56% (0.515565679574791192103264996203492787)"
   - Problem: A 36-digit raw quotient sits beside the rounded margin. It claims false precision, crowds the Result column and shows calculator output to a committee reader.
   - Fix: Show the rounded percentage only, the same way as K8, K13 and K14.
4. **Medium · narrative** (New reader)
   - Where: L207 "K4 | Channel sum check | 2,487 + 3,143 + 2,120 + 190"; L204 "1,198 + 1,289"
   - Problem: The Inputs are bare numbers with no labels. The reader can't tell which addend is aerospace and which is non-aerospace, or what the 190 in the 'sum check' is, without opening the filing.
   - Fix: Name each input briefly in the Calculation or Inputs cell, for example 'aerospace 1,198 + non-aerospace 1,289' and 'other 190'.
5. **Medium · visual** (New reader, Auditor)
   - Where: Calculations table, Source column, every row; CP-1A_s-198.png x~950-1160, y~290-1480 (display coords)
   - Problem: Every row repeats the same raw filename 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl'. It wraps over three lines and makes each row three lines tall, so the 18-row table runs about 1,200 px. The '.jsonl' file name is internal storage, not a document a reader recognises.
   - Fix: Show a reader label such as 'FY2024 10-K, p.164' and let the Sources section carry the full identifier.
6. **Low · narrative** (Saboteur)
   - Where: L218 "K15 | Operating cash flow less capex, acquisitions and dividends paid FY2024 | 1,880 − 2,347 − 2,038 | USD -2,505 million | ... page 123"
   - Problem: The shortfall appears as 'USD -2,505 million' with no plain word for what it is (the bottom line calls it a funding gap). The cited page (123) also differs from the cash-flow page (52) used for its 1,880 input.
   - Fix: Label it 'funding shortfall USD 2,505 million' and cite both pages its inputs come from.
7. **Low · visual** (Auditor)
   - Where: Result column K8, K13, K14, K16, K17 (bold monospace '20.58%', '39.58%', '2.08%', '69.00%', '31.32%') vs regular 'USD 2,487 million'; CP-1A_s-198.png y~760-1400
   - Problem: Percentages render in bold monospace and USD results in regular sans. The mixed styling suggests some results are emphasised when none are, and it makes the column look uneven.
   - Fix: Render every result in one typographic style, right-aligned or with tabular figures.
8. **Low · visual** (New reader)
   - Where: ID column, grey 'Basis' label under every K-number; CP-1A_s-198.png x~305-340
   - Problem: Each ID cell has an orphan 'Basis' chip that opens or says nothing visible. It adds noise and its meaning is unclear in a table that already has a Source column.
   - Fix: Drop the chip from table rows that already carry a Source column, or make clear what it opens.

### Bottom line

Kind: reader passage · handoff lines 21-28 · verdict **CONCERNS**

- Narrative: The bottom line leads with a clear judgement and keeps sources in the Basis lines, not in the sentences, as the house standard requires. Its weaknesses: the shortfall is given as a negative 'gap' (USD -2,505 million), 'edge of debt capacity' has no leverage figure behind it, 'EBITDA As Defined' is never explained, and the opening sentences run to 50-60 words.
- Visual: There is no chart in this section. On the page, the bottom line is two long paragraphs in heavy bold display type broken up by monospace figure chips. The chip for the shortfall leaves its minus sign outside the chip, and the section heading is hidden under the sticky bar when the page is scrolled to the section.

1. **High · narrative** (Saboteur, New reader (promoted from Medium))
   - Where: line 23: "did not cover acquisitions and dividends paid, leaving a funding gap of USD -2,505 million that was met with new debt"; screenshot CP-1A_bottom-line.png crop (330,200)-(1040,940), tmp/CP-1A-012-a.png
   - Problem: A 'gap' given as a negative number is a double negative: a reader can take '-2,505' as a surplus, or wonder whether the gap is 2,505 or something else. On screen it is worse. The value chip wraps only '2,505 million' and leaves 'USD -' outside it in body type, so the highlighted figure (the one whose Basis the reader opens) reads as a positive 2,505.
   - Fix: State the shortfall as a positive amount with the direction in words (for example 'a shortfall of USD 2,505 million'), and make the figure chip include the sign whenever a signed value is shown.
2. **Medium · narrative** (Saboteur)
   - Where: line 23: "whose owners deliberately run it at the edge of its debt capacity, so creditors are lending against durable cash generation"
   - Problem: The bottom line's strongest claim, 'edge of its debt capacity', has no leverage measure behind it. The paragraph gives only the change in debt ('total debt rose by USD 5,130 million'), not a debt level or a debt/EBITDA multiple, so the committee cannot test the claim from the bottom line.
   - Fix: Anchor the 'edge of capacity' judgement to one stated leverage figure, with its period and basis, or soften the wording to what the numbers shown actually support.
3. **Medium · narrative** (New reader)
   - Where: line 23: "In fiscal 2024 net sales rose to USD 7,940 million with an EBITDA As Defined margin of 52.56%"
   - Problem: 'EBITDA As Defined' is the company's own adjusted measure, capitalised as a defined term but never explained. A reader who has not read the 10-K does not know it adds back items, so may compare the 52.56% with a peer's reported EBITDA margin.
   - Fix: Say once, in plain words, that this is the company's adjusted EBITDA (after add-backs), so the reader does not treat it as a comparable reported margin.
4. **Medium · visual** (New reader, Auditor (promoted from Low))
   - Where: Bottom line block, CP-1A_bottom-line.png y≈230-920 (original px), tmp/CP-1A-012-a.png
   - Problem: Two paragraphs of about 110 words each are set in a large, heavy bold display face. That makes a wall of bold text with no emphasis left to give. Each dotted-underlined monospace figure chip breaks the rhythm, and several chips wrap to the start of a line ('USD 7,940 million', 'USD 1,880 million', 'USD 4,348 million'), which makes the lines ragged.
   - Fix: Show the bottom line as a lead paragraph at modestly larger regular or medium weight (as in the VMO2 reference lede), and keep the figure chips in the same visual weight as the surrounding text.
5. **Low · narrative** (New reader)
   - Where: line 23: "TransDigm is a high-margin, aftermarket-heavy aerospace components franchise whose owners deliberately run it at the edge of its debt capacity, so creditors are lending against durable cash generation that is routinely recycled into acquisitions and debt-funded special dividends rather than into debt reduction."
   - Problem: The opening judgement is a single 50-word sentence that strings together three ideas. The first paragraph of line 26 does the same with a 60-word sentence. A first-time reader has to parse the sentences before getting the verdict.
   - Fix: Split the judgement into short sentences: first the business quality, then the financial policy, then what that means for creditors.
6. **Low · narrative** (Saboteur)
   - Where: line 26: "total payments of about USD 4,348 million left in October 2024, so the year-end cash balance of USD 6,261 million overstates what remained for creditors"
   - Problem: The passage says the year-end cash overstates what remained but does not say what did remain. The reader has to subtract the two figures themselves (and the result also mixes the period-end and October dates).
   - Fix: State the cash left after the dividend, with its date (or point to the 2024-12-28 liquidity figure), so the conclusion carries its own number.
7. **Low · visual** (Auditor)
   - Where: CP-1A_bottom-line.png top of content pane, y≈220-240 (original px)
   - Problem: When the page is scrolled to the Bottom line anchor, the text starts straight under the sticky run bar with no 'Bottom line' heading visible. The heading appears to sit behind the bar, so the reader lands on unlabelled bold text.
   - Fix: Offset the anchor scroll by the height of the sticky header so the section heading stays visible above the passage.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 44-48 · verdict **CONCERNS**

- Narrative: The passage puts its judgement first and keeps sources out of the sentences, but its contrary case leans on a fixed-rate share with no visible support and on a ratio with no prior-year value, and its view-change triggers are too vague for a committee to monitor.
- Visual: This section has no chart; the prose block reads cleanly, but it mixes three styles for its figures, hides its Basis line, and leaves the right half of the column empty.

1. **High · narrative** (Saboteur + Auditor (promoted))
   - Where: L46: "the earnings-to-fixed-charges ratio improved to 2.7x, and roughly 77% of gross debt is fixed rate"
   - Problem: "Improved to 2.7x" gives no FY2023 value, although the fact register (L152, F17) says FY2023 was disclosed, so the reader cannot see how large the improvement was. The 77% fixed-rate figure appears in no fact or calculation row. It shows up only in a consumer note at L190 that also says "Hedge detail not read", so a figure that carries the counter-case has no visible support in the stated Basis (pages 52–55; K14).
   - Fix: Give the FY2023 ratio next to 2.7x, and either tie 77% to a fact row with its page and date or drop it from the contrary case.
2. **Medium · narrative** (Saboteur)
   - Where: L46: "The view would soften if the company redirected excess cash to debt prepayment or used buyback and dividend capacity without new borrowing for several years; it would harden if ... EBITDA growth slowed"
   - Problem: The triggers have no thresholds or time frame ("several years", "growth slowed", "started to compress"). A committee cannot tell when the view has actually changed. The phrase "used buyback and dividend capacity without new borrowing" is also ambiguous, because it could describe a continued payout and still be counted as a softening.
   - Fix: State each trigger as a measurable condition, for example debt prepaid as a share of free cash flow over a named period, or a margin or EBITDA-growth level against the FY2024 52.56% base.
3. **Medium · narrative** (New reader + Auditor (promoted))
   - Where: L46: whole passage, one 120-word-plus paragraph beginning "The strongest evidence against an extraction-led reading is..."
   - Problem: The contrary evidence and the view-change triggers sit in one dense block. "Extraction-led reading" is house shorthand the reader has to translate. The sentence "Repricing term loans down twice in fiscal 2024" relies on the transaction table further down the page to make sense.
   - Fix: Split it into two short paragraphs (contrary evidence, then what would change the view), say plainly "the view that owners extract cash at creditors' expense", and name the two repricings (March and June 2024).
4. **Medium · visual** (Auditor + New reader (promoted))
   - Where: shots2/CP-1A_contrary-evidence.png, crop tmp/CP-1A-014-a.png, region x 330-1100, y 260-480 (original px)
   - Problem: Within one sentence, the figures render in three different styles. USD 1,375 million, USD 2,045 million, 2.08% and 2.7x are underlined monospace chips, 77% is a dotted-underline proportional figure, and "twice" has no mark at all. The reader gets mixed signals about which numbers are calculated or sourced, and the wide monospace chips break the line rhythm.
   - Fix: Give every sourced figure in a sentence one consistent treatment, and use a clearly different marker only for a figure without support.
5. **Low · narrative** (Saboteur)
   - Where: L46: "the business has repeatedly generated the earnings to carry this structure: operating cash flow rose from USD 1,375 million to USD 2,045 million"
   - Problem: "Repeatedly" is backed by only two fiscal years, and the operating cash flow figures carry no periods (FY2023 to FY2024) in the sentence.
   - Fix: Label the periods (FY2023, FY2024) and drop or justify "repeatedly".
6. **Low · visual** (Auditor)
   - Where: shots2/CP-1A_contrary-evidence.png, section block y 230-480 (original px)
   - Problem: The paragraph's Basis line (L47) does not show on the page under the passage, so a reader cannot see what supports the counter-case without hovering over the chips. The text column also uses only about half of the 1440 px width, which leaves a large empty area to the right.
   - Fix: Show the Basis line as a small muted line under the paragraph, as in the VMO2 reference, so the sources stay out of the sentence but remain visible.

### Limitations

Kind: reader passage · handoff lines 49-55 · verdict **BLOCK**

- Narrative: The limitations are specific and in the right place after contrary evidence, but they contradict two things the module asserts earlier: debt capacity in the bottom line (High) and audited support for revenue durability in Key findings (Medium). They also leave out the non-GAAP basis of the headline margin, and they use pipeline wording ('the pack', 'pages reviewed').
- Visual: The section has no chart. Its four bullets render cleanly at a readable line length, but the last bullet runs into the Timeline panel heading with almost no space, and the Limitations heading has the same visual weight as the panel heading, so the end of the prose is not marked.

1. **High · narrative** (Saboteur, Auditor)
   - Where: L51: "the remaining restricted-payment and incremental-debt capacity cannot be quantified from the pages reviewed, so the size of the next possible recapitalisation is unknown and the extraction view could be either understated or overstated." (vs L23 bottom line: "owners deliberately run it at the edge of its debt capacity")
   - Problem: The bottom line says outright that the company is run at the edge of its debt capacity. This limitation says that capacity cannot be measured, and that the main view could be wrong in either direction. A committee reading the bottom line first takes away a capacity claim that the module itself says it cannot support.
   - Fix: Either qualify the bottom line so that 'edge of debt capacity' clearly describes stated policy and conduct rather than measured covenant headroom, or have the limitation name the bottom-line claim it limits and say which way the risk most likely runs.
2. **Medium · narrative** (Saboteur)
   - Where: L53: "the segment table supports the aftermarket figure only in a line that combines commercial and non-aerospace aftermarket, so the durability conclusion carries management-language weight rather than audited support." (vs L31: "the segment table independently shows ... so roughly 71% of sales sit in channels that are not tied to new aircraft build rates")
   - Problem: Key findings presents the segment-table split (about 71% of sales) as independent support from the filing. This limitation says the same conclusion rests on management estimates, not audited support. The page contradicts itself on how strong the revenue-durability evidence is.
   - Fix: State once, consistently, which part of the durability view rests on filed channel figures (about 71%) and which rests only on management estimates (about 90% proprietary, about 55% aftermarket).
3. **Medium · narrative** (Saboteur)
   - Where: L49-55, Limitations as a whole (the four bullets); compare L33 "EBITDA As Defined rose from 51.56% of sales in fiscal 2023 to 52.56%" and L142 add-backs "non-cash compensation USD 217 million, acquisition costs USD 70 million, refinancing costs USD 58 million"
   - Problem: The bottom line and the margin finding rest on EBITDA As Defined, a company-defined non-GAAP measure with at least USD 345 million of add-backs. The limitations never say so, so a reader who skips the appendix treats 52.56% as a reported, comparable margin.
   - Fix: Add a limitation saying the headline margin is a company-defined measure with add-backs whose recurrence was not assessed, and how that bounds the margin-resilience judgement.
4. **Medium · narrative** (New reader, Auditor)
   - Where: L51/L52: "cannot be quantified from the pages reviewed" / "the pages reviewed do not give"; L54: "no shareholder register or proxy is in the pack"; L53: "carries management-language weight"; L54: "The ownership map stops at the public listing"
   - Problem: 'The pack' and 'pages reviewed' describe the pipeline's input set, not the issuer. 'Management-language' echoes an internal evidence-category label. 'The ownership map' points the reader to another panel to make sense of the sentence. A reader who has not read the sources cannot tell whether a document does not exist or simply was not supplied.
   - Fix: Say in plain terms what is missing and why (for example, 'the proxy statement was not among the documents supplied'), and drop the internal category wording.
5. **Medium · visual** (Auditor)
   - Where: Screenshot CP-1A_limitations.png, crop (320,200)-(1440,720) at full resolution: last Limitations bullet ending "conclusion rests on board actions alone." and the "Timeline" heading directly below
   - Problem: The last bullet runs into the Timeline panel heading with about 10 px of space and no divider. The Limitations heading and the Timeline heading are the same size and weight, so nothing on screen marks where the written assessment ends and the charts begin.
   - Fix: Put clear vertical space or a rule between the end of the prose sections and the Timeline/Maps panels, and give panel headings a level distinct from prose sub-headings.
6. **Low · narrative** (New reader)
   - Where: L51: "The judgement that further debt-funded distributions are likely is a reading of conduct and stated priorities, not a measure of what the documents still permit; ..." (each of L51-L54 is one 45-60 word sentence joined by semicolons)
   - Problem: All four bullets have the same shape: a long single sentence with no leading phrase. The reader cannot scan which conclusion each one limits or which matters most, even though the Gaps table rates the executed-documents gap High and the others Medium.
   - Fix: Open each bullet with a short phrase naming the conclusion it limits, and order the bullets by how far each could move the credit view.

### Analytical read-through

Kind: prose/table · handoff lines 56-60 · verdict **CONCERNS**

- Narrative: The paragraph puts its judgement first and is clear, but it says owners drive the policy, which the module's own Limitations say cannot be shown. It also comes after Sources and repeats the Bottom line.
- Visual: This section has no chart, map or timeline. It is one wide paragraph with a faint inline Basis link, and the table it introduces looks like a separate section.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Line 58: "an owner-chosen financial policy that keeps gross debt high by recycling cash and fresh secured debt to equity" (compare line 54: "whether any holder or group influences the payout policy cannot be established")
   - Problem: The section blames the leverage on the owners, but the module's own Limitations (line 54) say no shareholder register or proxy was reviewed and owner influence cannot be established. A committee member could read this as evidence of sponsor-style control when the evidence shows only board actions.
   - Fix: Say what the evidence supports, e.g. a "board-chosen" or "management-chosen" financial policy, or name the ownership evidence it relies on.
2. **Medium · narrative** (Auditor, New reader)
   - Where: Line 56 heading "### Analytical read-through", placed after Limitations and Sources (lines 49–54; the page's On-this-page list runs Bottom line … Limitations, Timeline, Maps, Request, Sources, Analytical read-through)
   - Problem: This judgement-first summary appears after Sources, outside the required order, and largely repeats the Bottom line (line 23). A reader meets the same conclusion twice, and the second time it is cut off from the findings it summarises.
   - Fix: Fold the business-risk-low / financial-policy-risk-high framing into the Bottom line and keep this block only as a one-line lead-in to the operating table, or retitle it in plain reader language.
3. **Medium · narrative** (Saboteur)
   - Where: Line 59: "Basis: TDG_2024-09-30_10-K_..._tdg-20240930.htm.jsonl, pages 52, 164"
   - Problem: The Basis points to the cash-flow and segment pages, but the central claim, that fresh secured debt was recycled to equity, rests on the financing and dividend pages. The Bottom line (line 24) cites pages 52–54 for the same claim. So the cited source does not support the sentence's main judgement.
   - Fix: Cite the pages that support the debt-funded distribution claim (pages 53–54 and the dividend calculation) in this Basis line.
4. **Low · narrative** (New reader)
   - Where: Line 58: "For a creditor the business risk is low and the financial-policy risk is high; the second dominates committee framing because it is discretionary and recurring."
   - Problem: "Committee framing" is process wording, and "low" and "high" are given with no scale or anchor such as leverage or a rating. A reader cannot tell how high "high" is.
   - Fix: Give the anchor (for example, the leverage or secured-debt multiple that drives the high financial-policy risk) and drop the process wording.
5. **Low · visual** (Auditor, New reader)
   - Where: Screenshot CP-1A_s-56.png, region x≈350–1390, y≈230–315 (paragraph under "Analytical read-through" with the trailing grey "Basis" link)
   - Problem: The paragraph runs the full content width, about 190 characters per line, which slows reading. The source is reduced to a small low-contrast grey "Basis" word at the end of the text, easy to miss.
   - Fix: Cap the prose measure to about 90–110 characters and give the Basis marker enough contrast to be seen as a link.
6. **Low · visual** (New reader)
   - Where: Screenshot CP-1A_s-56.png, headings "Analytical read-through" (y≈235) and "Company and operating model" (y≈355)
   - Problem: The paragraph says "The table below shows…", but the table sits under a separate heading of the same level. On the page the lead-in and its table look like two unrelated sections.
   - Fix: Put the table directly under the read-through (or make its heading subordinate) so the lead-in and table read as one unit.

### Company and operating model

Kind: prose/table · handoff lines 61-73 · verdict **BLOCK**

- Narrative: The table has the right shape, but it marks prior-year end-market figures as 'Not calculated' although they are on the cited page, its end-market rows do not reconcile to net sales, and its Change column is inconsistent and in one place wrong ('level change shown' when it is not).
- Visual: There is no chart in this section. The table renders cleanly at 1440 px with no clipping, but internal .jsonl source filenames fill and wrap the widest column, the many 'Not calculated' cells dominate the middle columns, and the section has no lead line under its heading.

1. **High · narrative** (Saboteur, New reader)
   - Where: L67-69: "Commercial and non-aerospace aftermarket sales | USD 2,487 million | Not calculated: comparator not needed for the view | Not calculated: comparator not needed" (same on Defense and OEM rows)
   - Problem: The FY2023 figures sit on the same cited page 164 (aftermarket 1,057+1,112 = 2,169; defense 1,569+993 = 2,562; OEM 690+989 = 1,679), so the table holds back available data. That data shows aftermarket grew about 15%, slower than OEM at about 26% and defense at about 23%, which complicates the 'aftermarket-anchored' durability case. The reader cannot see the mix shift.
   - Fix: Fill in the FY2023 values and changes for the three end-market rows from page 164, and leave 'Not calculated' only where the source truly lacks the data.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: L67-69: the three end-market rows (2,487 / 3,143 / 2,120) next to L65 "Net sales | USD 7,940 million"
   - Problem: The three rows add up to USD 7,750 million, not USD 7,940 million. Page 164 shows the USD 190 million gap is the Non-aviation segment, but the table never says the rows cover Power & Control plus Airframe only, so a reader adding them up finds an unexplained hole.
   - Fix: Label the rows as 'Power & Control + Airframe' or add a Non-aviation USD 190 million row so the end-market rows reconcile to net sales.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: L70: "Operating cash flow | USD 2,045 million | USD 1,375 million | Not calculated: level change shown"; L71 same; L72 "Not calculated: not needed | Not calculated"
   - Problem: 'Level change shown' is false because the Change cell shows no change. The Change column also mixes three kinds of value: the amount and percentage for sales, a margin pair for EBITDA, and placeholders elsewhere. FY2023 cash flow less capex (1,375 - 139 = 1,236) is trivially available but marked 'not needed'.
   - Fix: Give every row the same Change form (amount and % year on year, or a stated margin row) and fill the cells the figures already support.
4. **Medium · narrative** (Saboteur)
   - Where: L72: "Operating cash flow less capex | USD 1,880 million | ... | Insufficient to fund acquisitions and dividends without new debt"
   - Problem: The table gives no acquisition or dividend amounts (the transaction section further down gives the CPI acquisition at about USD 1,385 million and the USD 75.00/share special dividend), so this credit conclusion cannot be checked against anything on the row.
   - Fix: State the acquisition and distribution totals the USD 1,880 million is set against, with their source, in the row or the Basis line.
5. **Medium · visual** (Auditor, New reader)
   - Where: Source column, every row, shots2/CP-1A_s-61.png region x~960-1150, y~255-785 (display coords)
   - Problem: Each Source cell prints the internal extract filename 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 164'. That is pipeline vocabulary (.jsonl, accession string) rather than a reader citation, and it wraps to three lines, so it doubles every row's height and gives the widest column to the least useful content.
   - Fix: Show a reader citation such as 'FY2024 10-K, p.164' (the full identifier can sit in a tooltip or in Sources).
6. **Low · narrative** (New reader)
   - Where: L66: "EBITDA As Defined (management measure)"
   - Problem: The row does not say what 'As Defined' adjusts for, or that it is a non-GAAP add-back measure. A reader may take the 52.56% margin as a reported operating margin.
   - Fix: Add a short qualifier such as 'non-GAAP, after management add-backs' to the label or the Basis line.
7. **Low · visual** (New reader, Auditor)
   - Where: Operating measure column, the grey 'Basis' chip after each label, shots2/CP-1A_s-61.png y~260-760
   - Problem: The table has no lead sentence under its own heading, because the bottom line ('The table below shows...') sits in the previous section. The repeated grey 'Basis' chips beside each label are unexplained to a first-time reader.
   - Fix: Give the section a one-line takeaway above the table, and give the Basis chip a visible affordance or legend.

### Company profile

Kind: prose/table · handoff lines 74-86 · verdict **CONCERNS**

- Narrative: The facts are terse and mostly sourced, but they carry no judgement. They use internal evidence-class labels, cite an internal module as a source, give two aftermarket shares that do not reconcile, and leave out periods for most figures.
- Visual: The table is clean and readable, with no clipping or overlap. A repeated raw .jsonl file name dominates the width, and the inline 'Basis' chips blur into the row labels. Not verified: the 10-K source pages themselves (the 55% basis, the leadership-claim wording and the as-of dates for customers and workforce were not checked against the filing), and no view other than the supplied screenshot was rendered.

1. **High · narrative** (Auditor, New reader)
   - Where: line 79: "| Country and listing | Delaware company, New York Stock Exchange (TDG) | Documentary Fact | Source readiness (CP-0) |"; rendered in CP-1A_s-74.png profile table, Source cell "Source readiness"
   - Problem: The Source cell names an internal module instead of a document. In the handoff it also carries the module code (CP-0); on screen the code is removed, but "Source readiness" is still pipeline vocabulary, and the reader cannot trace the fact to a filing.
   - Fix: Cite the filing and page the module read (e.g. the 10-K cover page) in the Source column. Never cite a module.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: line 81: "Commercial aftermarket about 31%, commercial OEM about 27%, defense about 40%, non-aerospace about 2%" vs line 82: "About 90% proprietary, about 55% aftermarket"
   - Problem: Two rows apart, the table gives aftermarket as about 31% and then as about 55%, with no explanation that the 55% presumably includes defense aftermarket. A reader who has not seen the 10-K sees two aftermarket shares that disagree, and the aftermarket share drives the margin story.
   - Fix: State the basis of the 55% (commercial plus defense aftermarket, per the filing) in the same cell, so both shares can be reconciled on the page.
3. **Medium · narrative** (Auditor)
   - Where: line 83: "Top ten about 42% of sales; none above 10%"; line 84: "About 16,600 employees; about 17% unionised"
   - Problem: Only the End markets row names a period (FY2024). The customer concentration, workforce, proprietary share and aftermarket share have no fiscal year or as-of date, which breaks the rule that periods are exact.
   - Fix: Give each figure its period or as-of date (e.g. "FY2024" or "at 30 September 2024") as the filing states it.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 78: "Documentary Fact (leadership claim is Management Language)"; Category column throughout
   - Problem: "Documentary Fact" and "Management Language" are internal evidence-class labels, and the reader is never told what they mean. The Business row's note also refers to a "leadership claim" that does not appear anywhere in the Fact text.
   - Fix: Use plain reader labels (e.g. "Reported" / "Company estimate"), and either show the leadership claim with its qualifier or drop the parenthetical.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-1A_s-74.png crop (340,220)-(1400,800), Source column
   - Problem: The same raw internal file name "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" repeats on 7 of 8 rows. It wraps over two lines and takes about a quarter of the table width, and the .jsonl extension shows pipeline storage rather than a document the reader can recognise.
   - Fix: Show a short reader label (e.g. "10-K FY2024, p. 9") with the full identifier in a tooltip or in Sources.
6. **Low · narrative** (Saboteur)
   - Where: line 74-86: "### Company profile" table with columns "Item | Fact | Category | Source"
   - Problem: The table has no credit judgement: no lead sentence, and no consequence column like the operating table just above it. The reader has to work out alone why 42% top-ten concentration or 17% unionisation matters to a creditor.
   - Fix: Add a short creditor-consequence column or a one-line takeaway, matching the 'Creditor consequence' column in the preceding table.
7. **Low · visual** (New reader)
   - Where: CP-1A_s-74.png crop, Item column: "Country and listing Basis", "Customers Basis"
   - Problem: The grey "Basis" chip sits inline with the row label, so it reads as part of the item name ("Workforce Basis"). It also duplicates the Source column next to it.
   - Fix: Separate the chip visually (an icon or a right-aligned link), or drop it from tables that already have a Source column.

### Transaction summary and new debt issues

Kind: prose/table · handoff lines 87-91 · verdict **CONCERNS**

- Narrative: The section has a real credit point (secured new money pushes subordinated creditors down the recovery order) but puts it last, opens with pipeline wording, and leaves its two conclusions without the balances and maturity figures that would support them.
- Visual: There is no chart. The section shows on the page as one dense full-width paragraph with monospace figure buttons and no table for the debt issues its heading names. The Basis line (10-K pages 53–54) is not printed by design; it is reachable through the figure buttons (reader.js:306-324). This was confirmed in the source code, not by clicking in the browser.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 89: "No live transaction was supplied in the run settings, so the transaction context is the fiscal 2024 financing..." ... "The mechanism matters because both new-money issues were secured, so secured claims grew ahead of the subordinated notes"
   - Problem: The paragraph opens with pipeline wording the reader does not use ("live transaction", "run settings"). The credit judgement (secured debt is growing ahead of the subordinated notes, so loss given default for subordinated creditors rises) only arrives in the last sentence, after about 150 words of transaction listing. That breaks the judgement-first rule, and a reader who skims will miss the point.
   - Fix: Open with the credit judgement on subordination and refinancing risk, put the financing history after it as evidence, and replace the run-settings sentence with reader language such as "No pending transaction; this covers fiscal 2024 financing".
2. **Medium · narrative** (Saboteur)
   - Where: line 89: "The company completed about USD 21,000 million of debt financing transactions in the year, most of it refinancing"
   - Problem: The USD 21,000 million total counts repricings and extensions as "financing transactions" and is not split. A committee member could read it as debt raised, when the passage identifies only USD 5,000 million of new money (USD 2,000 million plus USD 3,000 million).
   - Fix: Split the total into new money, refinancing and repricing/extension, each with its amount, or drop the headline total.
3. **Medium · narrative** (Saboteur)
   - Where: line 89: "so secured claims grew ahead of the subordinated notes ... refinancing risk before fiscal 2028 is low, but loss given default for subordinated creditors rises with each such step"
   - Problem: Both conclusions rest on figures the section never gives: no secured or subordinated balances at 30 September 2024 and no maturity amounts by year. "Low before fiscal 2028" is asserted without the maturity profile, and the events table on the same page mentions a 2028 maturity concentration.
   - Fix: State the secured and subordinated debt amounts at period end and the nearest maturity amounts, so the reader can size both claims.
4. **Medium · narrative** (New reader)
   - Where: line 89: "which was issued concurrently with the USD 75.00 per share special dividend"
   - Problem: The dividend is given only per share, with no total cash amount. The reader cannot compare the distribution with the USD 3,000 million raised alongside it, and that comparison is the debt-funded-payout point the paragraph is making.
   - Fix: Give the aggregate special dividend in USD million next to the per-share figure, with its period.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-1A_s-87.png, region x 340-1400, y 220-400 (crop CP-1A-019-a.png): the single nine-line paragraph under "Transaction summary and new debt issues"
   - Problem: The section is one block of about 190 words in roughly 175-character lines across the full content width. The heading promises "new debt issues", but there is no table for them, so the reader has to pull six instruments out of the running text.
   - Fix: Keep a short judgement paragraph and add a compact debt-issues table (instrument, date, amount, coupon, rank, use of proceeds, Source), with a narrower text measure.
6. **Low · narrative** (New reader)
   - Where: line 89: "an add-on to the 2029 secured notes redeemed the 2027 senior subordinated notes that carried a 7.50% coupon, and term loans were repriced and extended"
   - Problem: Amounts and coupons are missing for most instruments named: the add-on size, the USD 550 million redeemed (it appears only in the events table), and the coupons on the 2029, 2031 and 2032 notes. The terms "Tranche J" and "Tranche L" are used without explanation.
   - Fix: Give each named instrument its amount and coupon, or point the reader to a debt-issues table that does.
7. **Low · visual** (Auditor)
   - Where: CP-1A_s-87.png crop CP-1A-019-a.png: inline figures "USD 21,000 million", "7.50%", "6.00%", "USD 75.00" set in monospace with dotted underline
   - Problem: Eight monospace, underlined figure buttons in one paragraph break the reading rhythm and give equal visual weight to coupons and headline totals. Nothing on the page signals that each figure opens its source.
   - Fix: Draw the figure buttons in the body typeface with a quieter affordance, so the numbers read as text but stay clickable.

### Gaps

Kind: prose/table · handoff lines 223-234 · verdict **CONCERNS**

- Narrative: The table lists the real missing evidence plainly: the ownership register, the acquisition contribution, the credit documents and the covenant bridge. But it uses pipeline vocabulary ("consumer", "run settings", "context", "not separately run"), does not lead with its one High gap, and logs as a gap a trivial check that would correct K18 from 70.90% to 70.91%.
- Visual: The section has no chart; it is a five-column table that renders legibly at 1440 px. The raw .jsonl file names wrapping in the Source column inflate row height, and the inconsistently placed "Basis" chips and identical styling for High and Low severities weaken scanning.

1. **High · narrative** (Auditor, New reader)
   - Where: L225 header "Affected conclusion or consumer"; L232 "Live deal terms blank in run settings | Low | ... | None needed for snapshot | context"; L233 "exact sum of K1 and K2 over net sales not separately run"; L229 Source "Source readiness (CP-0)"
   - Problem: Pipeline wording reaches the reader. The house standard bans "consumer". "Run settings", "snapshot", "not separately run" and a Source cell reading "context" describe the tool, not the issuer. "Source readiness" names a module as if it were a source document.
   - Fix: Rename the column "Affected conclusion", word each gap as missing issuer evidence (e.g. "No live transaction terms supplied"), and cite a real document or "Not available" in Source.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: L229 "Executed credit agreement and indentures (restricted-payment and incremental capacity) [Insufficient Information] | High | Size of future recapitalisations" (third of seven rows; screenshot CP-1A_s-223.png, Gaps table)
   - Problem: The only High gap sits third, between Medium rows, and the table follows no severity order. In the render, High looks exactly like Low. A reader skimming the table can miss that the size of future debt-funded dividends cannot be judged without these documents.
   - Fix: Sort the rows High to Low, or lead with a one-line statement of the High gap, so the most decision-relevant gap comes first.
3. **Medium · narrative** (Saboteur)
   - Where: L233 "K18 adds rounded shares; exact sum of K1 and K2 over net sales not separately run | Low | None; figure stated as about 71%" (with L221 "70.90%, about 71%")
   - Problem: The check this row says was not run takes one division: (2,487 + 3,143) / 7,940 = 70.91%, not the 70.90% printed in K18. A trivial calculation is logged as a gap instead of being done, and the printed figure is off at two decimals.
   - Fix: Compute the share from the unrounded inputs (70.91%) in K18 and drop this row.
4. **Medium · visual** (New reader, Auditor)
   - Where: Gaps table Source column, crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-025-a.png (full shot y≈1650-2230)
   - Problem: Each source shows the raw internal file name "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl", wrapped over three or four lines. It makes every row the tallest in the table and shows the reader a pipeline artefact (.jsonl) instead of a document name.
   - Fix: Show a short reader label such as "FY2024 10-K, p. 164", with the full identifier in a tooltip or in Sources.
5. **Low · narrative** (New reader)
   - Where: L227-231 "[Insufficient Information]" appended to five of seven gap descriptions
   - Problem: The bracketed tag repeats in nearly every row and adds no information in a table already titled Gaps. It reads as an internal status code and lengthens the cells.
   - Fix: Drop the tag, or make it a separate status column if it distinguishes some gaps from others.
6. **Low · visual** (New reader)
   - Where: Gaps table, Gap column: "Basis" chip under rows 1, 2, 7 and inline after rows 4 and 5; absent on rows 3 and 6 (crop CP-1A-025-a.png)
   - Problem: A small grey "Basis" label floats inside the Gap cell at varying positions, on some rows and not others, and does not say what it opens. It reads as stray text.
   - Fix: Place the Basis control in a fixed spot (or its own narrow column) and show it consistently, or not at all where no basis exists.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 235-238 · verdict **CONCERNS**

- Narrative: Both parts of this section are run plumbing: an internal brief and a next-step instruction. They put pipeline wording (fact pack, credit_snapshot pathway, run next) in front of the reader, and the Next module text promises an acquisition-adjusted margin analysis that the run never delivers (CP-1 line 294 leaves it as a gap).
- Visual: There is no chart, map or timeline in this section; both parts are plain paragraphs that render cleanly with no clipping. They have the same weight as the analysis in body style and page navigation, so metadata is not visually set apart from judgement.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: Line 237: "CP-1 should run next, taking the segment and channel split, the year-end dividend accrual and the securitization treatment from this fact pack, and locating the acquired-business contribution..." (rendered as "Financial foundation should run next...", CP-1A_s-235.png bottom, y about 1890-1940)
   - Problem: The whole Next module section is an instruction to the orchestrator about which module runs next and what it consumes. Words like "run next" and "fact pack" are pipeline vocabulary, and the section tells a portfolio manager nothing about TDG credit. That breaks the house rule against pipeline language.
   - Fix: Keep module-routing text out of the reader page, or replace it with a reader-facing pointer such as "Acquisition contribution to FY2024 growth is still open; see Gaps".
2. **Medium · narrative** (Saboteur)
   - Where: Line 237: "locating the acquired-business contribution so that margin durability can be separated from acquisition effects"
   - Problem: This promises that the next section will separate organic margin durability from acquisition effects. The run's Financial foundation handoff does not do this: CP-1/*.response.md line 294 lists "Acquired-EBITDA pro forma for FY2024 acquisitions not disclosed" as a gap and passes it on again. A committee reader could assume the 20.58% growth and 52.56% margin were adjusted for acquisitions when they were not.
   - Fix: State plainly that the acquisition contribution was not separated anywhere in this run, and link it to the open Gap rather than to a future step.
3. **Medium · narrative** (New reader, Auditor (promoted))
   - Where: Line 3: "Business and transaction fact pack (CP-1A) for TransDigm Group Incorporated, as of 2024-09-30, on the credit_snapshot pathway." (rendered at the top of CP-1A_s-1.png, y about 195-260)
   - Problem: The rendered Request is the module's internal brief. "fact pack" and the snake_case "credit_snapshot pathway" are pipeline labels, and the ISO date 2024-09-30 conflicts with the header's "As of 30 September 2024". The CP-1A code is replaced on screen, but the rest of the run plumbing still reaches the reader.
   - Fix: Turn the Request into a one-line reader scope note ("Scope: business, FY2024 financing and dividends, ownership, governance; no peer ranking, instrument view or recovery conclusion") with a reader date format and no pathway label.
4. **Medium · visual** (New reader, Auditor (promoted))
   - Where: "On this page" navigation, CP-1A_s-1.png and CP-1A_s-235.png left rail, y about 540-915 ("Request", "Consumers", "Next module")
   - Problem: The page navigation gives Request, Consumers and Next module the same weight as the analytical headings. Two of the run-plumbing entries sit at the end of the list, mixed in with Gaps and Calculations, which adds noise for the reader.
   - Fix: Drop the plumbing headings from the reader navigation, or group them under a collapsed "Run details" entry that is visually set apart from the analysis.
5. **Low · narrative** (Saboteur)
   - Where: Line 3: "with no peer ranking, instrument recommendation or recovery conclusion"
   - Problem: This is the only judgement-relevant content in the Request: the module deliberately draws no relative-value or recovery conclusion. It comes last in a run-plumbing paragraph that readers are likely to skip.
   - Fix: Lead the scope note with what the section does not conclude, so a reader does not look for a recovery view here.
6. **Low · visual** (Auditor)
   - Where: CP-1A_s-1.png, "Request" block, y about 190-265, directly under the module tab strip with the analytical read-through further down
   - Problem: The Request paragraph is set in the same body style and heading level as the analytical sections. Nothing on screen marks it as run metadata, so it reads as though it were the module's opening judgement.
   - Fix: Render run metadata in a muted caption or metadata style so the analytical read-through visually leads.

## Research questions (CP-DR)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-DR/cf778865cd7ba4168937bb03559f9e6214258c76c4a2616cbd51165a96feb4fe/1.response.md`

### Bottom line

Kind: reader passage · handoff lines 21-28 · verdict **CONCERNS**

- Narrative: The bottom line comes first and does carry a judgement, but it is about how adequate the evidence is rather than about credit. It uses pipeline vocabulary ('locked questions', 'coverage', 'legs of the snapshot', instructions to 'the credit view'), and its 55% aftermarket figure has no basis while the same page shows 31%.
- Visual: This section has no chart. Visually it is two long paragraphs in large bold type that read as a wall, with mixed number styles, no Basis affordance for the bottom-line paragraphs, and the section heading scrolled out of view.

1. **High · narrative** (Saboteur, New reader)
   - Where: Line 23: "about 90% proprietary products, about 55% aftermarket revenue" vs line 34 (same page): "About 31% of FY2024 sales came from the commercial aftermarket"
   - Problem: The bottom line gives a 55% aftermarket share with no basis, and a few lines later the reader sees 31% aftermarket. A reader who has not read the 10-K cannot tell that 55% presumably counts defense and commercial aftermarket together. That could lead them to misjudge how exposed revenue is to the high-margin, flight-hour-driven channel.
   - Fix: State the basis and period on the 55% figure (for example, total aftermarket including defense, FY2024 net sales) so it lines up with the 31% commercial aftermarket split in Key findings.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 23: "so the credit view must not borrow any sector valuation or peer-relative argument from this research"; line 26: "Coverage is 33.33% of the locked questions" ... "the relative-value and peer-benchmark legs of the snapshot remain open"
   - Problem: The bottom line is written as instructions to downstream modules and uses pipeline words ('locked questions', 'coverage', 'legs of the snapshot', 'the credit view', 'this research'). The house standard bans these on screen, and a portfolio manager is not the one who 'borrows' from one module into another.
   - Fix: Say it in reader terms: what the evidence does and does not let a committee conclude about TDG's credit, and that no peer or market-valuation evidence was available.
3. **Medium · narrative** (Saboteur)
   - Where: Line 23: "each of these is the issuer's own account, so the demand and regulation answers are adequate as primary evidence while the competition, structure and metric-comparison answers stay limited to the issuer's view"
   - Problem: The opening judgement is about how adequate the evidence is, not about credit. The one credit claim ('earnings base is durable') is qualified in the same sentence, and in the next paragraph the 'durability thesis rests on one evidence family'. A reader who stops after the bottom line does not learn whether the sector picture supports or weakens TDG's credit, or by how much.
   - Fix: Open with one direct credit sentence (for example, that sector demand and certification barriers support debt service capacity, subject to single-source evidence) and then give the evidence caveat.
4. **Medium · narrative** (New reader)
   - Where: Line 23 (first paragraph, two sentences of about 60 and 75 words); line 26: "Coverage is 33.33% of the locked questions (two of six answered), because no research items were supplied and the run has no web access, so ..."
   - Problem: Each bottom-line paragraph is one or two very long sentences that chain clauses with 'but', 'so', 'while' and ';'. '33.33%' is false precision for 2/6. 'Research items', 'evidence family' and 'web access' describe how the run was set up, not the issuer.
   - Fix: Break the bottom line into short sentences, one claim each, and write 'two of six questions answered' without the run-configuration explanation.
5. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-DR_bottom-line.png, region x 330-1100, y 200-860 (crop tmp/CP-DR-028-a.png)
   - Problem: Both bottom-line paragraphs, about 180 words, are set in large bold display type that runs to roughly 20 lines. A bold block that size reads as a wall and loses the emphasis a short lead should carry. The percentages switch between proportional (90%, 55%) and monospaced (16.2%, 33.33%) figures inside the same bold text.
   - Fix: Use the large bold style only for a one- or two-sentence lead, set the supporting paragraph at body size, and keep one figure style for numbers inside prose.
6. **Medium · visual** (Auditor)
   - Where: Screenshot CP-DR_bottom-line.png: the two bottom-line paragraphs (y 200-860) show no Basis affordance, while Key findings bullets 3 and 6 show a 'Basis' chip (y about 1335 and 1710)
   - Problem: The handoff has Basis lines for both bottom-line paragraphs (lines 24 and 27), but the page shows no Basis chip or line for them. The 'Basis' chip appears on only some Key findings bullets. The reader therefore cannot reach the source for the headline numbers, and source access looks inconsistent from one paragraph to the next.
   - Fix: Show the Basis affordance the same way on every paragraph that has a Basis line, the bottom-line paragraphs included.
7. **Low · visual** (New reader)
   - Where: Screenshot CP-DR_bottom-line.png, top of the content column (y about 185-200)
   - Problem: When the page is scrolled to this section, the 'Bottom line' heading sits above the visible area and the text starts with no heading, so the only cue to which section is in view is the highlighted entry in the left 'On this page' list.
   - Fix: Leave scroll-margin so that jumping to a section keeps its heading visible above the first line of text.

### Key findings

Kind: reader passage · handoff lines 29-48 · verdict **CONCERNS**

- Narrative: The section leads each bullet with a judgement and keeps sources out of the sentences, but bullet 1 makes an unsupported causal claim about the margin, internal pipeline wording leaks into bullets 5 and 6, and the channel growth figures do not add up to the total without explanation.
- Visual: The section is a clean six-bullet list in a readable column with no chart, but the monospace, dotted-underlined figures disrupt the prose, and the Basis control shows on only two bullets, so source access looks inconsistent.

1. **High · narrative** (Saboteur)
   - Where: line 31: "Because aftermarket is the higher-margin channel, its continued growth is the main reason EBITDA As Defined margin held above 52% in FY2024."
   - Problem: By the bullet's own figures, aftermarket grew slowest of the three channels (12.0%, against 18.9% for defense and 20.4% for commercial OEM), so the mix moved away from aftermarket. Calling it the "main reason" margin held is a causal claim the cited evidence does not support, and it inflates the pricing-power case a committee will lean on.
   - Fix: State the margin and the mix facts without the causal claim, or source the attribution to management's own explanation and point out that the mix moved away from aftermarket.
2. **High · narrative** (New reader; Auditor)
   - Where: line 46: "No sector trading level, spread, rating or peer quote exists in the pack or context... Source readiness marked this research ready... with no research items and no web access"; line 43: "possible from this module"
   - Problem: Pipeline vocabulary reaches the reader: "pack", "context", "Source readiness marked this research ready", "research items", "web access", "this module", "the valuation-context question". A PM does not know these internal objects, and the house rule bars pipeline language from reader text.
   - Fix: Say it in reader terms, e.g. no market trading levels, spreads, ratings or peer data were available for this review, so relative value cannot be judged from it.
3. **Medium · narrative** (Saboteur)
   - Where: line 31: "Organic sales grew USD 1,067 million, or 16.2%, with defense up USD 486 million (18.9%), commercial OEM up USD 294 million (20.4%) and commercial aftermarket up USD 253 million (12.0%)"
   - Problem: The three channels add up to USD 1,033 million, not 1,067, and the USD 34 million gap is never explained. The comparison period (FY2024 against FY2023) is also unstated, so a careful reader will suspect an arithmetic error.
   - Fix: Name the remaining USD 34 million (presumably non-aerospace) and state that this is FY2024 against FY2023 organic growth.
4. **Medium · narrative** (New reader)
   - Where: line 31: "its continued growth is the main reason EBITDA As Defined margin held above 52%" (term defined only later, line 43: "The headline metric is a management-defined EBITDA As Defined that adds back...")
   - Problem: The first bullet uses "EBITDA As Defined", the issuer's non-GAAP metric, four bullets before the section explains it. A reader first meets the 52% margin without knowing it rests on management add-backs.
   - Fix: Flag the term as management's adjusted EBITDA at first use, or move the metric bullet ahead of the first bullet that uses it.
5. **Medium · visual** (New reader; Auditor)
   - Where: Key findings bullets, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-DR-029-a.png (crop of CP-DR_key-findings.png, x 330-1100, y 220-1100)
   - Problem: The figures are drawn in a bold monospace face with a dotted underline ("USD 1,067 million", "USD 4,279 million") inside proportional body text. This breaks the reading rhythm, widens the gaps between words, and in bullet 5 wraps "USD 106 million" onto its own line start.
   - Fix: Show linked figures in the body font with a light underline or tint, so they read as prose and stay clickable.
6. **Low · narrative** (New reader)
   - Where: line 37: "Competition is described as fragmented, protected mainly by certification cost rather than by market concentration, and the documents give no market shares. The issuer says its niches face several competitors..."
   - Problem: Each bullet runs 60 to 85 words and puts the issuer's account and the counter-argument in one block. In bullet 3 the most important point for credit, that the issuer "may have to adjust prices", comes last.
   - Fix: Keep each bullet to its judgement plus one or two supporting facts, and lead bullet 3 with the pricing-pressure tension.
7. **Low · visual** (Auditor)
   - Where: Key findings bullets 1, 2, 4 and 5 against bullets 3 and 6 ("Basis" chip), same crop
   - Problem: Only two of the six bullets show a Basis control. In the other four, the source for claims without a figure (e.g. bullet 4's FAA and EU certification and government contract rights) is reachable only by clicking an unrelated figure such as "40%". To the reader those bullets look unsourced.
   - Fix: Show a Basis control on every bullet that has a Basis line, in addition to the clickable figures.

### Limitations

Kind: reader passage · handoff lines 54-60 · verdict **BLOCK**

- Narrative: Limitations is correctly placed after contrary evidence and its bullets carry no inline source references, but it is written in pipeline vocabulary and overstates coverage with "all six answers". It also states its decisive point, low confidence in every answer, last, and the Executive answer's "Answered/adoptable" table contradicts it.
- Visual: There is no chart in this section. It renders as a four-bullet list at a narrower measure than the neighbouring prose, with almost no gap before the following Timeline heading. The typography is otherwise legible and nothing is clipped.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: L59: "Pack sources carry no separate publication date or independence family beyond the issuer, and the module's local lineage caps readiness below full research readiness, so every answer is limited in confidence to Low."
   - Problem: This is pipeline vocabulary the reader cannot decode: "Pack sources", "independence family", "the module's local lineage", "caps readiness", "full research readiness". Line 56 adds "one evidence family" and line 58 adds "this module". The house standard bars pipeline and module wording on screen, and a committee member cannot tell what actually limits the work.
   - Fix: Say the plain cause, e.g. that every source is the issuer's own undated filing and nothing independent was available, so confidence in each answer is low.
2. **High · narrative** (Saboteur)
   - Where: L56: "All six answers rest on one evidence family, the issuer's own annual filing"; compare L57 "The valuation-context answer is missing" and L71 "Valuation context | Not found | ... | context"
   - Problem: The count disagrees with the rest of the page. Only five questions have any answer from the filing; valuation context was not found and is sourced to "context", not the 10-K. Saying "all six answers" overstates how much was answered.
   - Fix: Say that five of the six questions were answered, fully or partly, from the issuer's annual filing alone, and that valuation context was not answered.
3. **Medium · narrative** (Saboteur)
   - Where: L59: "so every answer is limited in confidence to Low." vs L72/L74 "Answered | FY2024 channel growth adoptable" and "Certification barrier and government contract rights adoptable"
   - Problem: The limitation most relevant to a credit decision, that every answer has low confidence, comes last and contradicts the Executive answer table. That table marks demand and regulation as "Answered" and "adoptable" with no confidence qualifier. A reader who skims the table will act on findings this section downgrades.
   - Fix: Put the Low-confidence rating first in Limitations and make the answer-state table carry the same confidence level.
4. **Medium · narrative** (Auditor)
   - Where: L57: "the fundamental view and any later relative-value work must not use a sector valuation argument sourced to this research." and L56 "the durability thesis the fundamental credit view may adopt carries that single-source risk"
   - Problem: These clauses tell other analysis stages what they may use, not what the reader should conclude. Directions between modules leaking onto the page are pipeline wording under the house standard.
   - Fix: State the consequence for the reader instead, e.g. that this research gives no sector valuation benchmark for TDG's debt.
5. **Medium · visual** (Auditor, Saboteur)
   - Where: /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots2/CP-DR_limitations.png, region x 330-1440, y 210-640 (crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-DR-031-a.png)
   - Problem: The last bullet ("confidence to Low.") runs straight into the next "Timeline" heading with almost no vertical gap. The Request, Sources and Executive answer headings all have a full section gap, so the boundary of the section and its key closing statement are visually blurred.
   - Fix: Put the same space after Limitations as after the other sections, so the Timeline heading starts a distinct block.
6. **Low · narrative** (New reader)
   - Where: L58: "this module cannot say whether TransDigm's EBITDA As Defined is more or less aggressive than peers' adjusted EBITDA"
   - Problem: "EBITDA As Defined" is the issuer's own adjusted-EBITDA term and is not explained in this section. A reader who arrives from the side navigation's "Limitations" link meets it cold, and "this module" is self-reference.
   - Fix: Gloss the term briefly as management's adjusted EBITDA and replace "this module" with "this research".
7. **Low · visual** (New reader)
   - Where: Same crop: Limitations bullets wrap at about x 830 of 1200 (displayed), while Request and Executive answer prose below spans the full content width to about x 1150
   - Problem: The bullet list uses a narrower measure than the neighbouring prose on the same page. The inconsistency makes this section look like a different component and leaves a large empty band on the right.
   - Fix: Give the bullets the same text measure as the other prose sections, or apply one deliberate reading width across all prose.

### Executive answer

Kind: prose/table · handoff lines 61-75 · verdict **CONCERNS**

- Narrative: The executive answer is a second bottom line placed after Limitations and is addressed to the downstream module ("may adopt", "Consequence for Fundamental credit", "Complete with Gaps"), not to the credit committee, and its "Answered" states are not tied to the Low-confidence limitation.
- Visual: The section is a single paragraph plus a clean four-column table; legibility is fine, but raw .jsonl filenames dominate the Source column and duplicate Basis chips cause ragged wrapping.

1. **High · narrative** (Auditor, New reader)
   - Where: L63: "CP-2 may adopt the demand and regulation findings as primary-sourced, issuer-attributed context. It should treat the competition and structure points as management's view" (rendered as "Fundamental credit may adopt..."); table header L67 "Consequence for CP-2"
   - Problem: The section is written as an instruction to the next module rather than to the reader. The renderer swaps the code for a name, but the inter-module wording ("adopt", "adoptable", "Consequence for Fundamental credit", "input from this run") still leaks onto the page, against the house rule.
   - Fix: Address the credit committee directly, e.g. "Demand and regulation findings are reliable issuer-sourced context; competition and structure are management's view only", and rename the column "What it means for the credit view".
2. **High · narrative** (Auditor, Saboteur)
   - Where: L61 "### Executive answer" placed after L54 "### Limitations"; L63 "Coverage is 33.33%; status is Complete with Gaps."
   - Problem: A second bottom-line summary appears after Limitations, so the passage order breaks the judgement-first rule and the page has two competing bottom lines. It ends on internal status vocabulary ("Complete with Gaps") and a bare percentage the reader cannot interpret.
   - Fix: Fold this summary into the Bottom line at the top, or drop it, and say "2 of 6 questions fully answered" instead of the status code and the 33.33%.
3. **Medium · narrative** (Saboteur)
   - Where: L72 "| Market demand | Answered | FY2024 channel growth adoptable |" and L74 "| Regulation | Answered |" vs L59 "every answer is limited in confidence to Low"
   - Problem: The table marks two questions "Answered" with no confidence qualifier, while the Limitations say every answer is Low confidence and single-source. A reader who scans only the table will overrate the demand evidence that the contrary-evidence passage (L51) disputes.
   - Fix: Add a confidence column, or label the state "Answered (issuer only, low confidence)", so the table carries the limitation.
4. **Medium · narrative** (Saboteur)
   - Where: L63: "The filing shows FY2024 organic growth of 16.2% across defense, commercial OEM and aftermarket, an estimated 90% proprietary and 55% aftermarket revenue base"
   - Problem: It is unclear whether 16.2% is group organic growth or the rate for each channel, and the 90% and 55% are given without a basis (net sales? management estimate?). Line 63 is a narrative paragraph with no Basis line, so the reader cannot trace these figures.
   - Fix: State "group organic net sales growth of 16.2% in FY2024", name 90%/55% as management's estimated share of net sales, and add a Basis line under the paragraph.
5. **Medium · visual** (New reader, Auditor)
   - Where: Executive answer table, Source column, CP-DR_s-61.png crop (340,220)-(1400,810) → scratchpad/tmp/CP-DR-032-a.png
   - Problem: Every Source cell repeats the raw ingest filename "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl", which wraps over two lines and takes about 40% of the table width. One row shows only "context", which means nothing to the reader.
   - Fix: Render the source as a short reader label, e.g. "FY2024 10-K, pp. 9–10", and show "No source available" instead of "context".
6. **Low · narrative** (Saboteur, New reader)
   - Where: Table rows L69–L74 order: Competition, Metric definitions, Valuation context, Market demand, Industry structure, Regulation
   - Problem: The rows follow the internal question list, not importance or answer state. The two answered questions sit at rows 4 and 6, and the unanswered valuation row sits in the middle.
   - Fix: Order the rows by answer state (Answered, Partly, Not found) or by credit relevance.
7. **Low · visual** (New reader)
   - Where: Executive answer table, Question column "Competition Basis", "Metric definitions Basis" chips (scratchpad/tmp/CP-DR-032-a.png)
   - Problem: Each question carries a "Basis" chip as well as a Source column. The duplicate wraps under the label in five of six rows, giving ragged row heights and two competing provenance cues.
   - Fix: Drop the per-row Basis chip where the table already has a Source column, or put it in that column.

### Approved scope and research brief (materialised)

Kind: prose/table · handoff lines 76-93 · verdict **BLOCK**

- Narrative: This section is a run-configuration table with no judgement in it. It leaks pipeline vocabulary (hash, script name, transport, handoff, internal keys), shows a run ID that conflicts with the page header, and turns the code-to-name swap into the duplicated phrase "Fundamental credit fundamental credit view".
- Visual: The two-column table is legible and well spaced with no clipping. But a Basis chip on every metadata row is noise, and the "(materialised)" heading puts internal wording into the nav and breaks the analytical reading order.

1. **High · narrative** (Auditor, New reader)
   - Where: Lines 80-92: "| mode | linked |", "| cp0_sha256 | 4e5e4b7b...", "| approved_plan_hash | Not calculable: prepare_invocation.py not run in this transport; the brief is pinned by this handoff's hash instead |"
   - Problem: The whole section is pipeline metadata shown to the reader: snake_case field keys, a SHA-256 hash, a script name, "transport", "handoff", "cp_dr_public", "context run.cutoff". The house standard bans pipeline vocabulary on screen, and a credit committee member gets nothing from any of these rows.
   - Fix: Keep this table out of the reader-facing Modules page, or cut it down to two or three plain-language rows (subject, as-of date, evidence limited to the issuer's own filings, no peer pack).
2. **High · narrative** (Saboteur, Auditor)
   - Where: Line 81: "| run_id | tdg-2024-09-30-credit_snapshot-opus-medium |" (shown under the page header 'Showing run: ... TDG-PROOF-SNAPSHOT-OPUS-002', CP-DR_s-76.png top)
   - Problem: The run identifier in the table differs from the run identifier in the page header. A reader checking provenance sees two runs on one page and cannot tell which one produced this analysis.
   - Fix: Show one run identity: drop the module's internal run_id, or make it match the run the page says it is showing.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: Line 84: "Sector context for the CP-2 fundamental credit view on the credit_snapshot pathway", rendered as "Sector context for the Fundamental credit fundamental credit view on the credit_snapshot pathway" (CP-DR-033-a.png row decision_context)
   - Problem: When the module code is replaced by its display name, the result is a duplicated, ungrammatical phrase. The pathway key "credit_snapshot" also stays as a raw identifier.
   - Fix: Have the source text name the consumer in plain words so the code-to-name swap leaves a clean sentence, e.g. 'Sector context for the fundamental credit view (credit snapshot)'.
4. **Medium · narrative** (New reader)
   - Where: Line 91: "| peer_pack | false: context peer source is cp_dr_public but CP-1C is not among the requested modules |"; line 89: "| authorization_basis | Existing task instruction to run CP-DR on this issuer |"
   - Problem: The row that matters most to a reader (there is no peer comparison in this run) is written as a boolean plus internal source keys, so the reader cannot see that it limits the valuation and metric-definition answers.
   - Fix: State the limitation once in reader language, e.g. 'No peer data was supplied, so peer valuation and peer metric definitions are not covered', and keep it under Limitations.
5. **Medium · visual** (Auditor, New reader)
   - Where: Approved scope table, every Field cell carries a 'Basis' chip (CP-DR_s-76.png, x≈300-1160, y≈215-705 at display scale; crop CP-DR-033-a.png)
   - Problem: Each of the 12 metadata rows has a Basis chip, so the chip appears 12 times in a row and means nothing on rows like 'budget standard' or a hash. This weakens the Basis convention elsewhere on the page.
   - Fix: Attach Basis chips only to rows that carry an evidential claim, or drop them from configuration tables.
6. **Low · visual** (Auditor)
   - Where: Heading 'Approved scope and research brief (materialised)' (line 76; CP-DR_s-76.png y≈198) and its 'On this page' nav entry
   - Problem: "(materialised)" is internal build vocabulary in the heading and the side nav. The section also sits between Executive answer and Workstream plan, so configuration interrupts the analytical reading order.
   - Fix: Rename it plainly (e.g. 'Scope') and move it to the end of the module with the other run details.

### Causal synthesis and scenarios

Kind: prose/table · handoff lines 105-109 · verdict **CONCERNS**

- Narrative: The causal chain itself is coherent, but the paragraph does not lead with a judgement. Its key figures have no name or period, and module/pipeline wording leaks into it ("This module", "Downside owns that", "Financial foundation's measure").
- Visual: The section has no chart. It is a single dense full-width block of text with linked figures in mixed typefaces. The app hides the Basis line by design (ruling H3) and figures open the inspector, so the missing printed Basis line is not a defect.

1. **High · narrative** (Saboteur, New reader)
   - Where: L107: "That supports a margin above 52%, and the margin funds cash interest about 3.6x over (CP-1's measure)... leverage rises from CP-1's pro forma net 5.55x."
   - Problem: The three numbers a committee will act on have no name, period or basis on the page. Which margin is 52% (EBITDA As Defined? FY2024?), which coverage ratio is 3.6x, and net debt over what measure is 5.55x? The reader has to open another module to learn what each figure means.
   - Fix: Name each figure in the sentence, e.g. "FY2024 EBITDA As Defined margin of 52%", "EBITDA As Defined / cash interest 3.6x", "pro forma net debt / EBITDA As Defined 5.55x at 30 Sep 2024".
2. **High · narrative** (Auditor)
   - Where: L107: "This module supplies no quantified stress; CP-2A owns that." rendered as "This module supplies no quantified stress; Downside owns that." plus "(Financial foundation's measure)"
   - Problem: Pipeline wording reaches the reader. "This module", one module "owning" work and a parenthetical credit to another module are workflow mechanics, not credit language, and that breaks the house rule on pipeline vocabulary.
   - Fix: Remove the ownership sentence and the module attribution, or say it in reader terms, e.g. "The size of this stress is quantified in the Downside section", and keep where the figure comes from in the Basis line.
3. **Medium · narrative** (Saboteur)
   - Where: L107: "The chain from sector to credit runs through the aftermarket."
   - Problem: The paragraph opens with a mechanism, not a judgement, and never states what the chain means for credit. It does not say whether the aftermarket moat offsets 5.55x leverage, or how far the margin could fall before coverage becomes a problem. The reader has to infer the conclusion.
   - Fix: Open with a one-sentence credit judgement on how resilient the aftermarket-driven cash flow is against the leverage, then lay out the causal chain as support.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Heading L105 "Causal synthesis and scenarios" vs L107 "The downside path starts with an initiating condition such as a passenger traffic shock..."
   - Problem: The heading promises scenarios, but the section gives one qualitative downside path. It has no base or upside case and no indicative magnitude, so a reader could take the section as a scenario analysis it is not.
   - Fix: Rename the heading to match the content (e.g. "How the aftermarket drives credit, and the downside path") or set out the named scenarios briefly.
5. **Medium · visual** (New reader, Auditor)
   - Where: Paragraph block, screenshot CP-DR_s-105.png, crop CP-DR-035-a.png (x 330-1420, y 210-450 original px)
   - Problem: The section is one unbroken block of about 190 words and nine sentences at full content width (roughly 170 characters a line). The sector chain, the downside path and the triggers run together, so the triggers, which are the actionable part, get lost.
   - Fix: Split the block into short paragraphs (upside chain, downside transmission, observable triggers) or put the triggers in a short list, and narrow the text measure.
6. **Low · narrative** (New reader)
   - Where: L107: "so EBITDA As Defined falls faster than sales"
   - Problem: "EBITDA As Defined" is the issuer's adjusted metric, but the passage does not say it is adjusted, so a reader who has not seen the filing may treat it as reported EBITDA.
   - Fix: Add a short gloss the first time it appears in this section, e.g. "EBITDA As Defined (the issuer's adjusted EBITDA)".
7. **Low · visual** (Auditor)
   - Where: Crop CP-DR-035-a.png: "52%" in proportional bold vs "3.6x" and "5.55x" in monospace with dotted underline
   - Problem: The three linked figures in one sentence use different fonts. Two ratios are monospace like code and the margin is in the body font, which looks inconsistent and makes the ratios look like technical tokens.
   - Fix: Render every inspectable figure in the same body typeface with the same link affordance.

### Events: Research catalysts

Kind: timeline · handoff lines 110-115 · verdict **BLOCK**

- Narrative: The single-row table puts a historical fact under a 'catalysts' title. Its credit-relevance cell talks about which modules use the fact instead of what it means for the credit, and the 12.0% growth figure has no period or basis.
- Visual: The timeline shows only an unlabelled bar a full month wide, with no event text and no as-of reference, so it is unreadable without the table; the table itself loses width to metadata columns and a raw .jsonl source file name.

1. **High · narrative** (Auditor, New reader)
   - Where: line 114: "CP-2 and CP-2A use it as the demand baseline" (rendered on screen as "Fundamental credit and Downside use it as the demand baseline")
   - Problem: The Credit relevance cell describes how later modules consume the fact, which is pipeline producer/consumer wording. It does not say what the fact means for the credit. A committee reader learns nothing from which module uses it.
   - Fix: State the credit implication directly, e.g. that aftermarket demand above pre-pandemic levels supports margin and interest cover, and drop the reference to which module uses it.
2. **High · visual** (Saboteur, Auditor)
   - Where: Timeline panel, 'Research catalysts' row: CP-DR_timeline.png crop (320,190)-(1440,340), saved as /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-DR-036-a.png
   - Problem: The only event is drawn as one empty pale bar running the full width from 2024-02-01 to 2024-02-29. It has no event label, no marker and no as-of (2024-09-30) reference. A month-precision point event therefore looks like a month-long duration, and the reader cannot tell what the bar stands for without the table.
   - Fix: Draw the event as a labelled marker spanning its month (e.g. 'Feb 2024: RPKs pass 2019 levels'), on an axis that also shows the as-of date.
3. **Medium · narrative** (Saboteur)
   - Where: line 114: "Marks the aftermarket demand recovery behind 12.0% commercial aftermarket organic growth"
   - Problem: The 12.0% figure has no period (FY2024? year on year?) and no basis. The cell also asserts that the RPK recovery caused it, which the cited page-11 statement does not state.
   - Fix: Give the period and basis of the 12.0% (e.g. 'FY2024 vs FY2023, issuer-reported') and present the link as context, not as established causation.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 110-114: "### Events: Research catalysts" with a single row whose Status is "Historical — Since February 2024..."
   - Problem: The section title promises catalysts, but its only entry is a historical fact seven months before the as-of date. The forward triggers named just above (build-rate statements, government audit or repayment claims) are not listed. A reader could conclude there are no dated catalysts to watch.
   - Fix: Either list the forward triggers with expected dates or explicitly state that no dated forward catalyst was found in the supplied sources.
5. **Medium · narrative** (New reader)
   - Where: line 114: "Historical — Since February 2024, both domestic and international RPKs have surpassed 2019 (i.e., pre-pandemic) levels"
   - Problem: The Status cell repeats the Event cell almost word for word and adds an undefined abbreviation (RPKs). The reader reads the same sentence twice in two six-line wrapped cells.
   - Fix: Reduce Status to a one-word state (e.g. 'Historical') and keep the event wording, with the term spelled out, in the Event cell only.
6. **Medium · visual** (New reader, Auditor)
   - Where: Events table, Source column: CP-DR_s-110.png region x 820-960, y 255-325 (display scale): "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 11"
   - Problem: The Source cell shows a raw pipeline file name with a .jsonl extension, broken mid-token across five lines. The reader needs 'TransDigm FY2024 10-K, p. 11'.
   - Fix: Render the source as a short human citation (document, period, page), with the file identity behind a link or tooltip.
7. **Low · visual** (New reader)
   - Where: Events table, columns 'Date precision' = "month" and 'Published' = "—" (line 114; CP-DR_s-110.png y 225-360)
   - Problem: Two of seven columns hold internal metadata (precision flag, an empty published date). They take width from Event and Credit relevance, which wrap to six lines.
   - Fix: Fold the precision into the date display (e.g. 'Feb 2024') and drop the empty Published column so the substantive cells read on one or two lines.

### Analytical appendix — complete canonical registers

Kind: register appendix · handoff lines 116-167 · verdict **BLOCK**

- Narrative: The registers carry accurate, sourced facts, but they read as machine output: snake_case field names, enum codes, module routing and run-setup vocabulary. The \"UNRESOLVED (partly…)\" labels also understate what the evidence actually establishes.
- Visual: There is no chart in this section. The three tables are very long, the claims table clips its right-hand columns and squeezes the claim text into a narrow column, and the appendix heading is dropped, so the reference material blends into the analysis.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: L122 "| question_id | question | decision_relevance | consumer_module_id | after_module_id | evidence_needed | completion_test |"; L135 "claim_type ... source_type | independence_family | entity_period_unit_perimeter"; cells "source_characterisation", "attributed_view", "UNRESOLVED (not_found)" (L163)
   - Problem: All three registers reach the screen with raw snake_case field names and enum codes, including the pipeline word "consumer" and module routing ("after_module_id"). I confirmed this in the rendered DOM (tmp/CP-DR-037.html) and the screenshot CP-DR-037-s-118.png. The house standard says pipeline vocabulary is not reader language, and a PM cannot tell what "attributed_view" or "entity_period_unit_perimeter" means.
   - Fix: Render plain-English column heads and status words (e.g. "Used by", "Claim type: issuer's view / fact / gap", "Not found"), or keep these registers off the reader page.
2. **High · visual** (Auditor + New reader (promoted))
   - Where: Table "Claims and located evidence", scratchpad/tmp/CP-DR-037-s-118.png, y≈990-3600 (full-res), right edge x≈1300-1390
   - Problem: The 10-column evidence table is wider than the content pane. "independence_family" is clipped to "Issuer FY2 / annual filin", and "entity_period_unit_perimeter" is off-screen entirely. The claim column is about 120 px wide, so one quote wraps to 15-20 lines and 17 rows fill more than 2,500 px.
   - Fix: Drop or merge the low-value columns (source_date, source_type, independence_family, perimeter) so the claim column gets width and the table fits the pane without horizontal clipping.
3. **Medium · narrative** (Saboteur)
   - Where: L161 "UNRESOLVED (partly; issuer-attributed view only)"; L165 "UNRESOLVED (partly; issuer-attributed) | High for the sector; low for the issuer's own mix"
   - Problem: Two of the four questions marked UNRESOLVED hold located primary facts: the issuer's mix and its own EBITDA definition both rate "low" uncertainty. With the 33.33% coverage headline, this makes the evidence base look weaker than it is. "UNRESOLVED (partly…)" is also self-contradictory, so the reader cannot tell "partly answered" from "not found".
   - Fix: Use a three-way status the reader can parse (Answered / Partly answered: issuer view only / Not found) and keep it consistent with the coverage figure.
4. **Medium · narrative** (Auditor)
   - Where: L124 "CP-2 (CP-1C named by method but not requested in this run) | CP-1"; L161 proposed_consequence "CP-2 may cite the moat only as management's view; no pricing-power conclusion should rest on this module"
   - Problem: TDR.1 and the proposed_consequence column are workflow routing: which module consumes the answer, which runs first, and what a later module may do. On screen this reads "Fundamental credit (Peer benchmark named by method but not requested in this run)" and "Financial foundation". It is instruction to other modules, not credit content, and "module"/"method" wording leaks to the reader.
   - Fix: Remove the routing columns from the reader view, and phrase the consequence as what it means for the credit view (e.g. "Moat rests on management's account only").
5. **Medium · narrative** (Saboteur + New reader (promoted))
   - Where: L144 "Gap: context quotes, ratings, peers and issuer market fields are blank; no research items; no web access; no sector spread in pack | inference | context | context, page 1"
   - Problem: The source cell reads "context, page 1", which is not a document a reader can trace. "pack", "context", "research items" and "web access" are run-setup terms. The Source column therefore holds a pipeline label where the house standard wants a source identity.
   - Fix: State the gap as "No market data (spreads, ratings, peer quotes) was available for this review" and leave Source as an explicit "None available".
6. **Medium · visual** (New reader)
   - Where: Source column, every row E1-E17 (L137-153): "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"; CP-DR-037-s-118.png x≈850-990
   - Problem: The same machine filename (accession number and ".jsonl" extension) repeats 14 times and wraps to 5 lines per row. It takes width from the claim column and tells the reader nothing beyond "FY2024 10-K".
   - Fix: Show a short reader label ("FY2024 annual report (10-K)") with the page, and keep the file identity in Sources.
7. **Medium · visual** (Auditor)
   - Where: Rendered page: heading "Analytical appendix — complete canonical registers" (L116) absent from DOM; route #CP-DR/s-116 resolves to page top (supplied shot CP-DR_s-116.png shows only the module head)
   - Problem: The renderer drops the appendix heading, so the three registers (about 4,000 px of reference tables) appear under "Events: Research catalysts" as peers of the analysis. Nothing tells the reader they have left the argument and entered a reference appendix, and the section's own route lands on the top of the page.
   - Fix: Render a visible appendix divider (e.g. "Appendix: research registers") that the section route can land on, and set the appendix tables apart visually from the analysis.
8. **Low · narrative** (Saboteur)
   - Where: L164 "organic sales up 16.2%, led by commercial OEM (20.4%) and defense (18.9%), with commercial aftermarket up 12.0%"
   - Problem: "Led by" ranks by percentage, but defense added the most dollars (USD 486m vs 294m, L146), and aftermarket is the margin driver. The ranking can steer the reader's sense of what drove the year.
   - Fix: Rank by dollar contribution, or say plainly that the order is by growth rate.

### Calculations

Kind: prose/table · handoff lines 168-186 · verdict **CONCERNS**

- Narrative: This is a data subsection and the arithmetic checks out (R02 16.2%, R06 residual 34, R07 4.4% and the R08-R10 chain all recompute). It still opens with pipeline internals and ends in an unexplained confidence score coded with internal status labels, so a credit reader cannot tell what the score means for reliance on the module.
- Visual: There is no chart in this section. The ten-row Calculations table is legible and fits the page width without clipping, but the Result column mixes bold monospace and regular fonts arbitrarily, and the Basis chips appear on only some rows.

1. **High · narrative** (Auditor + New reader)
   - Where: Line 170: "Helper scripts named by the method (prepare_invocation.py, validate_handoff.py, validate_research.py, confidence_score.py, completeness_check.py) were not run in this transport; ... The approved plan hash is not calculable without the invocation helper."
   - Problem: The section opens with pipeline internals (script filenames, "transport", "calculate tool", "approved plan hash", "invocation helper"). The house standard bars pipeline vocabulary from reader text, and a portfolio manager gets nothing from it.
   - Fix: Drop the paragraph from the reader view, or reduce it to one plain sentence saying the figures below were recomputed independently from the annual filing.
2. **High · narrative** (Saboteur + New reader)
   - Where: Lines 181-183, R08-R10: "R09 × S (partial source gate, 0.7) − P (one MATERIAL finding, 15) | 58.975 − 15 | 43.975, integer score 44; band Low; qa_status Restricted"
   - Problem: A confidence score of 44 ("band Low", "qa_status Restricted") is derived from undefined coefficients (E, C, S, P, "partial source gate", "MATERIAL finding") and internal status codes. The reader cannot tell what the score measures or whether Low should change the credit view. The weights (0.6/0.4, 0.7, 15) appear with no rationale, which makes the number look more precise than it is.
   - Fix: State in one plain sentence what the score means for reliance on this module, e.g. 'low confidence: sector and valuation questions unanswered', and keep the scoring arithmetic and status codes out of the reader table or define each term.
3. **Medium · narrative** (Saboteur)
   - Where: Line 181, R08: "Evidence quality E: (5 directly sourced × 1.0 + 1 calculated × 0.9 + 2 insufficient × 0) / 8 material claims | 5.9 / 8"
   - Problem: The eight "material claims" and their classification are not identified anywhere in the section, and the Inputs cell gives no period or source even though the column header promises "(period, source)". The input to the score cannot be traced or checked.
   - Fix: List the eight claims by evidence ID (or point to the claims table rows) in the Inputs cell so that the 5/1/2 split can be verified.
4. **Medium · narrative** (New reader)
   - Where: Line 174, R01: "ANSWERED questions / locked questions | 2 / 6 (this brief) | 0.3333333333 (33.33%) | fraction"; line 175 "0.1620349279 (16.2%, matches printed)"
   - Problem: Results are printed to ten decimal places as a "fraction" with the percentage in parentheses. The table also uses internal terms ("locked questions", "this brief", "matches printed") that a reader who has not seen the pipeline cannot interpret.
   - Fix: Show results in the reader's unit (33.3%, 16.2%) and use plain wording such as 'questions answered of 6 asked' and 'agrees with the reported figure'.
5. **Medium · visual** (Auditor)
   - Where: Calculations table, CP-DR_s-168.png crop x340-1400, y830-1460 (scratchpad/tmp/CP-DR-038-a.png): Result cells for R04 "100", R05 "67", R09 "84.25"
   - Problem: Three Result values render in bold monospace while the other seven are in the regular body font. The emphasis is arbitrary: it highlights trivial checks (100%) over the score that actually matters (R10).
   - Fix: Render every Result cell in one typographic style, with numbers right-aligned or tabular in a consistent font.
6. **Low · narrative** (Saboteur)
   - Where: Line 185: "R05 was summed by hand from two located shares (27 + 40) and is shown for traceability"
   - Problem: This contradicts line 170, which says the checks were done with the calculate tool. It also adds process commentary rather than meaning: R05's 67% has no stated credit relevance here.
   - Fix: Either say why 67% matters (exposure to OEM build rates and defense budgets) or drop the process note.
7. **Low · visual** (Auditor + New reader)
   - Where: Calculations table, CP-DR_s-168.png, Calc ID column: "Basis" chips under R02-R07 but none on R01, R08, R09, R10
   - Problem: The Basis affordance appears on only some rows and wraps under the ID in a narrow column. A reader cannot tell why R08-R10, the score rows, have no basis to open.
   - Fix: Show the Basis link consistently on every row, or mark rows without a source basis explicitly, e.g. 'derived from R08'.

### Gaps

Kind: prose/table · handoff lines 187-200 · verdict **BLOCK**

- Narrative: The table lists real gaps (no sector valuation, no peer EBITDA definitions, no market-share data), but it opens with no judgement, mixes process items with credit-material gaps, uses pipeline vocabulary (TDR codes, handoff, transport, consumers), and ends with an internal QA status log that a credit reader cannot use.
- Visual: The section has no chart, map or timeline. It is one 4-column table, readable at 1440 px with adequate spacing, plus a dense paragraph. The weak points are a Source column of raw file ids that wraps to three lines and inline Basis links that sometimes wrap alone and make rows uneven.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: line 199: "source mode supplied_only honoured; ... readiness RESEARCH_READY_WITH_LIMITATIONS; confidence score 44, band Low, qa_status Restricted (one MATERIAL finding: valuation context not found); committee_status Requires More Work."
   - Problem: The paragraph under the table is an internal QA log. It is full of pipeline status codes (supplied_only, RESEARCH_READY_WITH_LIMITATIONS, qa_status, committee_status) and self-certifications ("no prompt-like instruction found in sources"). It shows on screen as one dense paragraph. The one fact that matters to credit (no valuation context, low confidence) is buried in the middle of it.
   - Fix: Remove the QA log from the reader view and replace it with one plain sentence: confidence is low because sector valuation and peer data were not available.
2. **High · narrative** (Auditor, New reader (promoted))
   - Where: line 194: "TDR.4–6 not composed; CP-1C not in run despite peer source cp_dr_public"; line 195: "Plan-hash continuity checked only by this handoff's pinned hash | None in this transport"; line 192: "consumers carry no sector valuation"
   - Problem: Several cells use pipeline vocabulary the house standard forbids: register codes (TDR.4–6), an internal source id (cp_dr_public), "handoff", "transport", "consumers", plan hash. The renderer swapped CP-1C for "Peer benchmark" but left the rest. A committee member cannot read rows 4 and 5.
   - Fix: Drop the process-only rows (plan hash, helper validation) from the reader table and write the peer row in reader terms, e.g. "No peer comparison was run, so leverage cannot be ranked against peers."
3. **Medium · narrative** (Saboteur)
   - Where: lines 189-197: the Gaps table opens directly with "| No research items supplied and no web access [Insufficient Information] |" and has no lead sentence or ranking
   - Problem: The section starts with no bottom line. Credit-material gaps (no sector spreads, ratings or quotes; no peer EBITDA definitions) sit at the same weight as process items (plan hash) and a trivial residual ("Minor; does not change the demand answer"). A reader cannot tell which gaps limit the credit view.
   - Fix: Open with one judgement sentence naming the gaps that limit the credit view (valuation and peer comparability), and order the rows by credit materiality.
4. **Medium · narrative** (New reader)
   - Where: line 197: "Minor; does not change the demand answer"; line 196: "Competition and structure answers remain qualitative"; line 192: "Valuation-context question not found"
   - Problem: The Effect cells refer to internal research questions ("the demand answer", "valuation-context question") that the reader only knows from another part of the page. They describe the effect on the module's process, not on the credit view of TransDigm.
   - Fix: State each effect in credit terms, e.g. "TransDigm's spread cannot be compared with the sector", not "question not found".
5. **Medium · visual** (New reader, Auditor (promoted))
   - Where: Gaps table, Source column, CP-DR_s-187.png, crop CP-DR-039-a.png (rows 1-7, right column): "context, page 1" and "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 9–10"
   - Problem: The Source column shows a raw file name, with an EDGAR accession number and a .jsonl extension, that wraps across three lines. Five rows cite "context, page 1", which means nothing to a reader. The column tells the reader nothing about which document backs each row.
   - Fix: Show a reader label such as "FY2024 annual report (10-K), pp. 9–10" and "Run scope (no research supplied)", and keep the file id in the Basis detail.
6. **Low · visual** (Auditor)
   - Where: Gaps table, Gap column, CP-DR-039-a.png: "Basis" chip after "[Insufficient Information]" (rows 1 and 3, where it wraps onto its own line), and after each other Gap cell
   - Problem: The Basis link sits inline in the Gap cell, after a bracketed status tag. In rows 1 and 3 it wraps alone onto a third line, so it reads like a stray word and makes the rows uneven. The "[Insufficient Information]" brackets are also an internal tag rendered as plain text.
   - Fix: Show the gap status as a styled chip or a separate column, and place the Basis link consistently, e.g. right-aligned or under the cell, so it never wraps alone.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 201-204 · verdict **CONCERNS**

- Narrative: Both passages in this unit, the Request (line 3) and the Next module (line 203), are run plumbing addressed to the pipeline, not the reader: they leak pipeline vocabulary, read awkwardly after module-code substitution, and carry the one reader-relevant judgement (what may be relied on) in routing language.
- Visual: There is no chart, map or timeline in this section; it is two plain-text blocks, positioned mid-page (Request) and at the page end under the QA paragraph (Next module), with no visual hierarchy separating usable guidance from audit text.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: line 3: "CP-DR deep research for TransDigm Group Incorporated (TDG), as of 2024-09-30, on the credit_snapshot pathway. ... the six default sector questions of the local method ... answered from the pinned source pack for CP-2" (rendered in CP-DR_s-1.png as "Research questions deep research for ... pinned source pack for Fundamental credit")
   - Problem: The Request paragraph shown to the reader is run plumbing: it contains pipeline vocabulary ("credit_snapshot pathway", "local method", "pinned source pack", "default sector questions"), and the module-code substitution produces a broken sentence ("Research questions deep research for") that names another module as the owner of a source pack. A portfolio manager cannot tell what is being asked or why.
   - Fix: Show one plain sentence of scope (for example, which six sector questions were answered from TDG's FY2024 10-K only, with no outside research), or move the request record off the reader page.
2. **High · narrative** (Auditor + Saboteur (promoted))
   - Where: line 203: "CP-2 should proceed and may adopt the market-demand and regulation answers as primary-sourced, issuer-attributed context... those questions stay UNRESOLVED and block only the CP-2 conclusions that would depend on them."
   - Problem: The 'Next module' passage gives one module routing instructions for another ("should proceed", "may adopt", "block"), so pipeline wording reaches the reader under a pipeline heading. It is also the only place on the page that says which answers may be relied on, but it never names the conclusions that are blocked. A committee reader could miss that valuation and peer leverage comparability are missing.
   - Fix: Tell the reader directly which findings are issuer-sourced fact, which are management's view and that no valuation or peer comparison exists, under a reader heading such as 'How to use these answers', and keep the routing note out of the Modules page.
3. **Medium · narrative** (New reader)
   - Where: line 203: "it should take no sector valuation or peer comparison from this module; those questions stay UNRESOLVED"
   - Problem: "from this module" and the upper-case status "UNRESOLVED" are internal register labels, not prose. The on-screen "Fundamental credit" is a module name that is not linked, so the reader must go to another page to understand it.
   - Fix: Write the status in sentence case ('not answered') and refer to the analysis by what it does (the credit assessment), with a link if it is meant to be followed.
4. **Medium · narrative** (Saboteur)
   - Where: CP-DR_s-1.png, Request block at y≈195–260 (display), placed after Bottom line/Key findings/Limitations/Timeline and before Sources and Executive answer
   - Problem: The scope statement sits mid-page between the judgement passages and a second 'Executive answer'. The reader meets scope limits (no web, no peers) after the conclusions, and the page appears to give two answers.
   - Fix: Fold the scope facts into the Limitations passage the reader already meets, and drop the separate Request block from the reader's reading order.
5. **Low · visual** (Auditor)
   - Where: CP-DR_s-201.png, 'Next module' heading and paragraph at y≈1870–1945 (display), directly under the dense 'QA validation (manual)' paragraph
   - Problem: The section is a bare heading plus a wall-width paragraph with no chip, callout or Basis line. It ends the page as one block with the code-filled QA paragraph above it, so the one usable instruction is visually indistinguishable from audit residue.
   - Fix: Give the reader-facing usage guidance a distinct visual treatment (a callout or a short list) and separate it clearly from the audit/QA text.
6. **Low · visual** (New reader)
   - Where: CP-DR_s-1.png, Request paragraph at y≈215–260 (display), full content width (~860 px)
   - Problem: The Request text runs across the full content column as three dense lines with underscore identifiers ("credit_snapshot"), which reads as a system log rather than page content.
   - Fix: Keep any scope line to one short sentence without code-style identifiers.

### Sources

Kind: prose/table · handoff lines 5-18 · verdict **CONCERNS**

- Narrative: The text is short and factual, and its scope note (which filings were not relied on, and why) is useful. But pipeline words ("Supplied handoff", "this handoff", "cp_dr_public", "ev-*", "URL rows", "Pinned") leak to the reader, against the house standard.
- Visual: The two tables are clean and the column labels are legible. But 64-character hashes take the most width and the 10-K is shown as a five-line raw filename with a stray Basis chip, so the reader cannot see at a glance what the source is or when it is dated. Not verified: other routes or a live render (only the given 1440x2400 screenshot was read), and whether the hashes match the run's files.

1. **High · narrative** (Auditor, New reader)
   - Where: L12 table header "| Supplied handoff | Module | sha256 |"; L17 "so no external source was used anywhere in this handoff."; L10 "peer source cp_dr_public" (screenshot CP-DR_s-5.png, Sources block y~400-540)
   - Problem: Pipeline vocabulary reaches the reader on screen: "Supplied handoff" is a column header, "this handoff" closes the note, and "cp_dr_public" puts a module code (CP-DR) on the page. The house standard bans both.
   - Fix: Use reader words such as "Earlier analysis used" and "this module", and describe the peer setting in plain language (e.g. "public peer data, not supplied") with no internal identifier.
2. **Medium · visual** (New reader, Saboteur)
   - Where: L9 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" with the sha256 column; crop CP-DR-027-a.png, Source and sha256 columns
   - Problem: The only issuer source appears as a raw ingest filename broken over five lines. Two 64-character hashes take the widest column. Nowhere does the table say in plain words that the source is TransDigm's Form 10-K for the fiscal year ended 30 September 2024, so a committee reader cannot tell what the evidence is or how old it is without decoding an accession number.
   - Fix: Lead with a readable title and date ("Form 10-K, FY ended 30 Sep 2024, filed Nov 2024"), and move the hash and filename to a narrow, muted or collapsible audit detail.
3. **Medium · visual** (Saboteur, Auditor)
   - Where: Row "context | f7b95e1f... | Run settings only (...) not issuer evidence" (L10); crop CP-DR-027-a.png row 2
   - Problem: Run configuration is listed as a source, next to the 10-K and with equal weight. Yet the Bottom line's coverage claim ("Basis: context; calculation R01") rests on it. A reader skimming the table may take "context" for a document.
   - Fix: Split run settings out of the source list into a labelled "Scope of this research" line, so the Sources table holds documents only.
4. **Low · narrative** (Saboteur)
   - Where: Page TOC on CP-DR_s-5.png: "Request", "Sources", then "Executive answer", "Approved scope and research brief (materialised)", ...
   - Problem: Sources sits in the middle of the page and is followed by a long appendix that cites sources again. A reader looking for the end-of-module source list does not find it at the end.
   - Fix: Render Sources as the closing block of the module (after the appendix tables), as in the VMO2 reference reading order.
5. **Low · visual** (New reader)
   - Where: Supplied handoff table rows "Source readiness | Source readiness" and "Financial data foundation | Financial foundation" (L14-15; crop CP-DR-027-a.png lower table)
   - Problem: After renaming, the Module column repeats the first column almost word for word, which wastes width and makes the reader wonder whether these are two different things.
   - Fix: Drop one of the two name columns, or show the module's display name once with the date of the run that produced it.
6. **Low · visual** (Auditor)
   - Where: "Basis" chip inside the Source cell "...20240930.htm.jsonl Basis" and "(ev-∗)" in the note (L17); crop CP-DR-027-a.png
   - Problem: A Basis chip sits on the source itself, where it is circular, and the internal research-item pattern "ev-*" renders with an odd asterisk glyph. Both are leftover machinery with no meaning for the reader.
   - Fix: Remove the Basis chip from Sources rows, and say "no outside research was supplied" instead of quoting an item-ID pattern.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 49-53 · verdict **CONCERNS**

- Narrative: The passage puts its judgement first and draws its contrary evidence from the issuer's own filing, which is the right approach. But it ends on an unsourced leverage figure (6x) that disagrees with the module's own 5.55x (line 107), it adds two exposures under an \"or\" (67%), and it packs evidence and untestable triggers into one 230-word paragraph. Not verified: the inspector content behind the 67% and 6x links was not opened in a browser; I judged it from the Basis line and the calculation table (lines 52, 178).
- Visual: The section has no chart, map or timeline. It is one prose block, readable and not clipped, with faint dotted figure links and a narrower measure than the rest of the module page (the Research catalysts timeline below it belongs to another unit and was not judged).

1. **High · narrative** (Saboteur + Auditor)
   - Where: line 51: "would weaken the certification-moat argument and, with it, the case for tolerating leverage near 6x." (Basis line 52: "pages 10–11, 24; calculation R05")
   - Problem: The 6x figure gives no metric (gross or net, EBITDA As Defined or reported), no period and no basis. Its Basis items do not support it: R05 is the 27 + 40 = 67% sales share (line 178), and pages 10–11 and 24 are risk text. The same module page also states "CP-1's pro forma net 5.55x" (line 107), so the reader sees two leverage figures that disagree, and the one in the judgement passage has no source.
   - Fix: Quote the leverage figure the module actually relies on (pro forma net 5.55x, EBITDA As Defined, FY2024) and add Financial data foundation (CP-1) to the Basis line, or drop the number.
2. **Medium · narrative** (Saboteur)
   - Where: line 51: "a fall in commercial OEM build rates or a defense funding reprioritisation would hit about 67% of sales"
   - Problem: 67% is the sum of both exposures (27% OEM + 40% defense, R05), but the sentence joins them with "or", so either shock alone appears to touch two-thirds of sales. Line 34 on the same page puts a commercial downturn at "nearly three-fifths", which a reader cannot reconcile without the calculation table.
   - Fix: Give each shock its own share (commercial OEM about 27%, defense about 40%, about 67% combined) and say which grouping the key findings' three-fifths refers to.
3. **Medium · narrative** (New reader + Auditor)
   - Where: line 51: a single paragraph of about 230 words, from "The strongest evidence against the durable-demand view" to "leverage near 6x."
   - Problem: Contrary evidence, the creditor impact and three separate view-change triggers are packed into one block of 16 rendered lines. The heading promises two things, but the reader cannot see where the evidence ends and the triggers begin.
   - Fix: Split it into one paragraph of contrary evidence and a short list of the conditions that would change the view, each with its direction.
4. **Medium · narrative** (Saboteur)
   - Where: line 51: "The view would change if independent industry data showed passenger traffic or fleet utilisation rolling over, or if peer disclosures showed aftermarket price competition."
   - Problem: The triggers have no threshold or observable measure (how far, over what period) and do not say which way the view would move. A committee cannot monitor "rolling over".
   - Fix: Give each trigger a measurable signal, for example commercial aftermarket organic growth turning negative in the quarterly filings (which the module names at line 107), and the resulting direction of the view.
5. **Low · visual** (Auditor + New reader)
   - Where: Screenshot CP-DR_contrary-evidence.png, crop (340,220)-(1440,620) saved as tmp/CP-DR-030-a.png: the 67% and 6x figures
   - Problem: The dotted underline under 67% and 6x is the only sign that a basis exists (by the ruling, the Basis line is not printed). The underline is faint, and the 6x inspector cannot show a supporting source because none is given, so the visible cue leads to nothing useful.
   - Fix: Use a slightly stronger figure-link style, and make every underlined figure open a basis item that actually supports it.
6. **Low · visual** (Auditor)
   - Where: Screenshot CP-DR_contrary-evidence.png, y≈190–500 (displayed) versus the Request, Sources and Executive answer blocks below
   - Problem: This passage is set in a narrow column (about 540 px) with a wide empty band to the right, while later sections on the same page run the full content width in a smaller font. The page therefore switches measure and type size within one module.
   - Fix: Keep one reading measure and one body size for all reader passages on the module page.

### Workstream plan

Kind: prose/table · handoff lines 94-104 · verdict **BLOCK**

- Narrative: This is a planning table without a lead judgement. It uses internal codes and pipeline words, and its Outcome column reports whether work finished rather than whether each hypothesis held, which hides credit-relevant results such as the missing valuation anchor and the open sceptic's case.
- Visual: The section has no chart, only one clean bordered 7-column table. It is readable at 1440 px, but the unexplained grey 'Basis' labels, a slug that breaks at its hyphen, a cramped Outcome column and a heading size that differs from neighbouring sections weaken it. Not verified: what the 'Basis' label opens when clicked (judged from the static screenshot only), and the VMO2 reference screenshots were not opened.

1. **High · narrative** (New reader + Auditor (promoted from Medium))
   - Where: L98-103: "| WS-1 | competition; industry-structure |", "| WS-3 | valuation-context | Market | Pack holds no trading data | Search of pack and context |", "| WS-A | adversarial lane | Sceptic |"
   - Problem: The reader sees internal codes (WS-1 to WS-A), hyphenated slugs where questions should be ('metric-definitions', 'valuation-context'), and pipeline wording ('pack', 'adversarial lane', 'Completion test'). The house standard treats this as non-reader language. The real questions only appear in the 'Locked questions' table further down, so the reader has to scroll on to decode this one.
   - Fix: Put each workstream's plain-English question in the Question column, drop or explain the WS codes, and say 'the supplied documents' instead of 'pack' and 'contrary-view review' instead of 'adversarial lane'.
2. **Medium · narrative** (Saboteur)
   - Where: L101-103: "| Growth broad-based across channels | ... | Answered |" and "| Management account overstates moat | ... | Done |"
   - Problem: The Outcome column says whether the work was finished, not whether the hypothesis held. 'Answered' and 'Done' read like confirmation, so a committee member can't tell whether the sceptic's case (moat overstated) was supported or rejected. That is the credit-relevant result.
   - Fix: Have Outcome state the verdict on each hypothesis (supported, contradicted or unresolved), with the key evidence in a few words.
3. **Medium · narrative** (Saboteur)
   - Where: L100: "| WS-3 | valuation-context | Market | Pack holds no trading data | Search of pack and context | Located sector level or spread | Not found |"
   - Problem: The missing market and spread context is written as a 'hypothesis' and closed as 'Not found', with no judgement on what it means. The reader is not told that the sector view has no valuation anchor, and that limitation is easy to miss in a planning table.
   - Fix: Say plainly that no trading level or spread was available and that the view therefore has no market cross-check, and point to Limitations.
4. **Medium · narrative** (New reader)
   - Where: L94-96: "### Workstream plan" followed directly by the 7-column table header "| Workstream | Question | Perspective | Hypothesis | Disconfirming test | Completion test | Outcome |"
   - Problem: The section starts with a dense method table and no lead sentence. Nothing tells the reader what was settled, what stayed open, or why this table matters to the credit view, so judgement does not come first.
   - Fix: Open with one sentence giving the result, e.g. which questions were answered, which were partly answered and which were not, before the table.
5. **Medium · visual** (New reader + Auditor (promoted from Low))
   - Where: Workstream plan table, CP-DR_s-94.png, crop x 340-1400, y 220-740 (scratchpad/tmp/CP-DR-034-a.png): grey 'Basis' label under every WS id
   - Problem: Each row shows a small grey 'Basis' label under the workstream code, but the table has no Source column. Nothing shows whether 'Basis' is a link, a fold or a caption, so a reader can't tell where each row's evidence lives.
   - Fix: Show the row's source in a visible Source column, or style 'Basis' as an obvious expandable control with the source behind it.
6. **Low · narrative** (Auditor)
   - Where: L99: "| WS-2 | metric-definitions | Analyst comparability | Headline metric is a heavily adjusted EBITDA | Peer definitions | Issuer and at least one peer definition located | Partly: peer definitions not found |"
   - Problem: The disconfirming test needs peer definitions, but the run excluded outside evidence (L87 'supplied_only', L91 peer_pack false). The test could never be met, and the 'Partly' outcome doesn't say why, so it looks like a search gap rather than a scope limit.
   - Fix: Say the peer comparison was out of scope for this run, not merely not found.
7. **Low · visual** (New reader)
   - Where: Workstream plan table, CP-DR_s-94.png, row WS-1, Question cell: 'competition; / industry- / structure'
   - Problem: In a narrow column the slug breaks at its hyphen over three lines, so the reader sees fragments like 'industry-'. Seven equal-weight columns leave little room for the key Outcome column, whose text also wraps ('Partly: peer / definitions not / found').
   - Fix: Narrow or drop the Perspective and Completion test columns so the Question and Outcome columns can show their text on one or two lines.
8. **Low · visual** (Auditor)
   - Where: CP-DR_s-94.png: heading 'Workstream plan' (large, y~199) compared with the neighbouring 'Locked questions and recipients' (smaller bold, y~992)
   - Problem: Sibling sections on the same page render at different heading sizes, so it is unclear whether the later tables belong under the Workstream plan or stand on their own.
   - Fix: Render sibling sections at one heading level.

## Financial foundation (CP-1)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-1/60f5e223f0ac25d067396f089d11e6dd3c3afedd5eb3e9076a92c749b2acc1c6/1.response.md`

### Period table

Kind: prose/table · handoff lines 28-41 · verdict **CONCERNS**

- Narrative: This is a data table with a one-line footnote. It carries no judgement, does not say which periods are reported and which are forecast, has no Source column, and its footnote uses extraction jargon ('instants', 'duration start') about tables further down the page.
- Visual: The table is clean but oversized: three short columns stretched across the full width, a 'Basis' chip on every row that has no source behind it, ISO dates that do not match the page's long-date style, and no visual difference between the audited and future rows. The section has no chart.

1. **High · narrative** (Saboteur, New reader)
   - Where: Lines 34-38: "| FY2025 | 2024-10-01 | 2025-09-30 |" through "| FY2029 | 2028-10-01 | 2029-09-30 |" (as of 2024-09-30)
   - Problem: Five of the seven rows are future fiscal years, but nothing in the table marks them as forecast or projection periods. They sit in the same format as the audited FY2023 and FY2024 rows, so a reader can assume reported data exists for FY2025 to FY2029. Only FY2023 and FY2024 have audited figures in this module.
   - Fix: Add a column such as Status that reads Reported (audited) or Forecast period, or split the table into reported and projection periods.
2. **High · narrative** (Auditor, Saboteur)
   - Where: Lines 30-38: table headers "| Period | Start | End |", with no Source column
   - Problem: The house standard puts table sources in a Source column. This table has none, so the reader cannot see that the fiscal-year boundaries come from the 10-K. The future-year boundaries are an assumed continuation, not a sourced fact, and the table does not say so.
   - Fix: Add a Source column: the annual filing for FY2023 and FY2024, and a stated assumption for FY2025 to FY2029 (fiscal year continues to end 30 September).
3. **Medium · narrative** (New reader)
   - Where: Line 40: "Balance-sheet columns headed FY2024 and FY2023 are instants at 2024-09-30 and 2023-09-30; they carry no duration start."
   - Problem: 'Instants' and 'duration start' are data-extraction (XBRL) terms, not credit-committee language. The note also describes balance-sheet tables further down the page, not this table, so the reader meets it before the tables it explains.
   - Fix: Use plain words ("Balance-sheet figures are as at 30 September of each year") and put the note with the balance-sheet extract it describes.
4. **Medium · narrative** (Saboteur)
   - Where: Section heading "### Period table" (line 28), placed straight after the Bottom line
   - Problem: The first table after the bottom line is a calendar of fiscal-year boundaries, with no judgement or explanation of why it matters. That pushes the credit figures further down the page, and the reader is never told what the table is for (for example, that TDG's fiscal year ends 30 September and forecast periods follow that pattern).
   - Fix: Fold this into a one-line note that the fiscal year ends 30 September, or move the table to a reference position after the financial tables.
5. **Medium · visual** (Auditor, New reader)
   - Where: Period table: every Period cell shows a 'Basis' chip ("FY2023 Basis" ... "FY2029 Basis"); CP-1_s-28.png, crop x 340-1400, y 220-610 (scratchpad/tmp/CP-1-043-a.png)
   - Problem: Each of the seven rows has a Basis button. The table and the handoff give no source for any row, and in views.js the row buttons are built with an empty items list. The reader gets seven buttons that look like evidence but lead to none.
   - Fix: Hide the row Basis chip when the row has no source, or add the source so the chip resolves to the filing.
6. **Low · visual** (Auditor)
   - Where: Period table, CP-1_s-28.png, y ~260-570 (original px): three narrow columns spread across about 1,050 px
   - Problem: Three short columns stretched across the full content width leave large empty gaps between the period label and its dates. The eye has to travel across empty space to match each row.
   - Fix: Size the table to its content (compact width) or merge Start and End into one 'Fiscal year' column.
7. **Low · visual** (New reader)
   - Where: Period table date cells "2022-10-01" / "2023-09-30" against the page header "As of 30 September 2024" (CP-1_s-28.png)
   - Problem: The table uses ISO dates while the page header and the rest of the report use the long date form, so the same page shows two date styles.
   - Fix: Render the dates in the report's reader format (for example, 1 Oct 2022 to 30 Sep 2023).

### Financials and credit metrics

Kind: prose/table · handoff lines 110-149 · verdict **BLOCK**

- Narrative: The figures I re-derived reconcile (margins, gross and net debt, leverage, cover, liquidity), but the section has no bottom line, its definitions are calculation codes, and its secured-net leverage nets cash that the October dividend removed. Sources and missing-value labels are pipeline wording, not reader language.
- Visual: There is no chart in this section. The table renders cleanly but is a single 36-row block with no grouping, three-line wrapped file-name sources, left-aligned figures and a repeated Basis chip, so it is slow to scan.

1. **High · narrative** (Saboteur)
   - Where: line 138: "Secured debt less cash / EBITDA As Defined (house, not covenant) | 3.22x" read against line 147 "Incurrence tests ... 7.25x net; 5.00x secured net" and line 131 "Net debt pro forma for 2024-10-18 dividend"
   - Problem: Secured net leverage of 3.22x nets the full USD 6,261m of cash, and USD 4,348m of that cash left 18 days later as the October dividend. Recomputed on pro forma cash of USD 1,913m, it is (19,702-1,913)/4,173, about 4.26x. The table gives a pro forma figure for total net leverage but not for secured net leverage, so a reader comparing 3.22x with the 5.00x secured incurrence test sees about twice the real headroom.
   - Fix: Add a pro forma secured-net-leverage row next to the 3.22x figure, as the table already does for total net leverage, or label 3.22x as before the October dividend.
2. **High · narrative** (New reader + Auditor (promoted))
   - Where: line 114 Source: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 121"; line 115 "Calculation C18 | calculation C18"
   - Problem: Every Source cell shows either a raw pipeline file name (an accession number plus a .htm.jsonl extract suffix) or an internal calculation code (C01-C35). Neither is reader language: the code tells a portfolio manager nothing without opening another page, and it appears twice per row.
   - Fix: Show sources as the reader would cite them ("FY2024 10-K, p.121"), and replace calculation codes with the formula or a short label, keeping any code link out of the visible text.
3. **Medium · narrative** (New reader)
   - Where: line 119 "EBITDA margin (issuer EBITDA) | 48.02% | Not calculated | Calculation C34"; line 125 "FCF after dividends paid, USD m | -158 | Not calculated | Calculation C17"
   - Problem: In the "Definition / identity" column, about 25 of 36 rows say only "Calculation Cnn", so the column gives no definition. For example, the reader cannot tell which dividends make FCF negative (-158) or what the numerator and denominator are.
   - Fix: Put the identity itself in the Definition column (for example "FCF 1,880 less dividends paid in FY2024") for every derived row.
4. **Medium · narrative** (Saboteur)
   - Where: line 103 "includes dividend equivalent payments, current, 180" vs line 145 "Dividend paid 2024-10-18 / dividend equivalents, USD m | 4,216 / 132"
   - Problem: The page shows two dividend-equivalent amounts (180 and 132) without reconciling them. The 132 sits in the FY2024 column although it was paid on 2024-10-18, after the period end. A reader cannot tell which amount drives the pro forma net debt and liquidity rows.
   - Fix: State in the row that 132 is the part paid with the October dividend, out of the 180 accrued, and label the column entry as a subsequent event.
5. **Medium · narrative** (Auditor)
   - Where: lines 110-148: section opens directly with the table header "| Metric | FY2024 | FY2023 | Definition / identity | Source |"
   - Problem: This 36-row credit-metric table is the module's core data, but no sentence states the bottom line (leverage 6.0x gross, 4.5x net, rising to 5.55x pro forma; interest cover 3.6x). The reader has to build the judgement from 36 undifferentiated rows.
   - Fix: Open the section with a one- or two-sentence bottom line giving the key leverage, cover and liquidity figures and the direction since FY2023.
6. **Medium · narrative** (New reader + Auditor (promoted from Low))
   - Where: line 115 "Not calculable: FY2022 comparatives not used"; line 119 "Not calculated"; line 131 "n/a"; line 143 "Not supplied: not read"; line 146 "Not read"
   - Problem: Missing values are written in five different ways. "Not supplied: not read" and "Not read" are pipeline wording that describes the tool's process, not the issuer, and they leave unclear whether a value is missing in the filing or was simply not read.
   - Fix: Use one reader-facing convention for missing values, with a short reason only where it matters to the credit view (for example "not disclosed" or "not computed for FY2023").
7. **Medium · visual** (New reader + Auditor (promoted from Low))
   - Where: Financials and credit metrics table, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots2/CP-1_s-110.png, full height (crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1-048-a.png)
   - Problem: The table runs past a full 2400 px screen as one block of 36 rows. Reported figures, leverage, coverage, liquidity and covenant terms are mixed with no group headings. The Source column wraps the long file name over three lines on most rows, which doubles the row height, while the FY columns are mostly empty space.
   - Fix: Split the rows into labelled groups (P&L and cash flow, debt and leverage, coverage, liquidity, covenant terms) and shorten the source text so most rows fit on one line.
8. **Low · visual** (Auditor)
   - Where: FY2024/FY2023 columns, CP-1-048-a.png crop rows "7,940 / 6,585", "20.58% / Not calculable..."
   - Problem: Figures are left-aligned in a monospace font next to wrapped text such as "Not calculable: FY2022 comparatives not used", so magnitudes do not line up for comparison down the column. A grey "Basis" chip is repeated after every metric name and adds noise without saying what it opens.
   - Fix: Right-align numeric cells and keep missing-value text short; show the Basis affordance only once, or on hover.

### Chart data: revenue and EBITDA

Kind: chart · handoff lines 150-156 · verdict **BLOCK**

- Narrative: The figures match the handoff exactly, but the section is a bare data table with no bottom line: its heading is an internal label, the measure has three names, and the source is a raw internal file name inside a mixed basis/limitation cell rather than a Source column.
- Visual: The chart is visible and its bars, values and legend are correct, but it shows the pipeline word \"Handoff\" on screen, says the citations have no page when the handoff gives pages 71 and 121, hides the acquisition caveat in the folded table, and leaves about 40% of the card empty. Not verified: rendered DOM or contrast values (judged from the screenshots only); how the renderer produces the \"without a page\" chip.

1. **High · narrative** (Auditor, New reader)
   - Where: line 154: "Annual; Adjusted EBITDA is the issuer-adjusted EBITDA As Defined; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 71, 121"
   - Problem: The source sits inside a mixed "Basis and limitation" cell, not in a Source column. It is printed as a raw internal file name (accession number plus .htm.jsonl) that a portfolio manager cannot read, and it fills most of the cell.
   - Fix: Split it into a Basis/limitation column and a Source column that reads "TransDigm FY2024 Form 10-K, pp. 71, 121".
2. **High · visual** (Auditor, Saboteur)
   - Where: Revenue and EBITDA chart, chip row under each period: "Handoff" chip and "2 citations without a page" (CP-1_charts.png, crop scratchpad/tmp/CP-1-049-a.png, y~290-300). Handoff line 154: "...tdg-20240930.htm.jsonl, pages 71, 121"
   - Problem: The chart puts the pipeline word "Handoff" on screen, which the house rule forbids. It also says the two citations have no page, but the handoff gives pages 71 and 121 for both rows. A reader would wrongly conclude the figures cannot be traced to the filing.
   - Fix: Drop the "Handoff" chip and show each citation as the filing with its pages (10-K FY2024, pp. 71, 121), so the chip matches the table.
3. **Medium · narrative** (Saboteur)
   - Where: line 155: "includes FY2024 acquisitions from closing only"; chart "Revenue and EBITDA" shows 6585 to 7940 with no note
   - Problem: The bars show about 21% revenue growth and about 23% EBITDA growth with no caveat. The fact that part of FY2024 comes from acquisitions appears only in the table, which is folded under "Table form", so the chart invites the reader to read the growth as organic.
   - Fix: Put the acquisition-inclusion limitation in a visible chart footnote or caption next to the FY2024 bars.
4. **Medium · narrative** (New reader)
   - Where: line 150: "### Chart data: revenue and EBITDA"; line 152 header "Adjusted EBITDA"; line 154 "issuer-adjusted EBITDA As Defined"
   - Problem: "Chart data:" is an internal label, not reader language. The same measure carries three names on one screen (title "EBITDA", column "Adjusted EBITDA", basis "EBITDA As Defined"), so the reader cannot tell whether they are one figure or several.
   - Fix: Title the section as the reader's topic ("Revenue and EBITDA As Defined, FY2023–FY2024") and use one name for the measure throughout.
5. **Medium · narrative** (Saboteur)
   - Where: lines 154-155: "| FY2023 | 6585 | 3395 | US$m |" / "| FY2024 | 7940 | 4173 | US$m |"
   - Problem: The section gives no bottom line: the growth and the margin (51.6% to 52.6%) are left for the reader to work out. The figures also lack thousands separators, while the same module prints "USD 3,813 million" and "7,267", so number formats are inconsistent on one page.
   - Fix: Open with a one-line bottom line giving growth and margin, and format amounts as 6,585 / 3,395, matching the rest of the module.
6. **Low · narrative** (New reader)
   - Where: line 154: "| FY2023 |"; line 155: "| FY2024 |"
   - Problem: The section never says that TransDigm's fiscal year ends on 30 September, so FY2024 could be read as a calendar year.
   - Fix: State the fiscal year end once ("FY ending 30 September") in the caption or the basis.
7. **Low · visual** (Auditor)
   - Where: Revenue and EBITDA chart, CP-1_charts.png crop scratchpad/tmp/CP-1-049-a.png (plot area ends at x~670 of 1050)
   - Problem: The plot has no y-axis or zero label and fills only about 60% of the card's width, leaving the right third empty. The table headers "Revenue" and "Adjusted EBITDA" are set in a monospace code font next to sans-serif headers (CP-1-049-b.png).
   - Fix: Extend the plot to the full card width and set all column headers in one typeface.

### Chart data: EBITDA bridge

Kind: chart · handoff lines 157-170 · verdict **BLOCK**

- Narrative: This section is a data table with no bottom-line sentence. The reader sees pipeline file names and calculation codes. The credit point that USD 360 million of issuer add-backs separates 3,813 from 4,173 appears only inside a Basis cell.
- Visual: The bridge's bars are scaled from zero and do reconcile, but the x-axis labels overlap and cannot be read. There is no subtotal bar, and every step is the same colour, so the chart cannot be read alone.

1. **High · visual** (Auditor, New reader)
   - Where: EBITDA bridge chart, x-axis category labels, CP-1_charts.png region approx x350-1400, y860-900 (crop scratchpad/tmp/CP-1-050-a.png)
   - Problem: The nine category labels are printed on top of each other in monospace text. Only 'Net income (reported, US GAAP) FY2024' at the start and 'EBITDA As Defined FY2024' at the end can be read, so the reader cannot tell which floating bar is D&A, interest, tax or which add-back.
   - Fix: Use short labels (for example 'D&A', 'Interest', 'Tax', 'Acq./integration', 'Stock comp', 'Refinancing', 'Other'), wrapped or angled, or switch to a horizontal bridge so that every bar has a label of its own that can be read.
2. **High · visual** (Saboteur, New reader)
   - Where: line 164: "Income tax provision | 500 | US$m | Issuer adjustment as printed; subtotal is issuer EBITDA USD 3,813 million (calculation C35)"; the chart shows no 3,813 bar
   - Problem: The bridge goes straight from net income to the issuer's own 4,173 figure, and every step is drawn in the same blue. The GAAP-to-EBITDA items (D&A, interest, tax) cannot be told apart from USD 360 million of management add-backs (acquisition costs, stock compensation, refinancing, other), which is about 9% of the closing figure. The only place the 3,813 subtotal appears is a Basis cell.
   - Fix: Add a drawn subtotal bar for issuer EBITDA of 3,813 after tax, and give the issuer add-back steps a separate colour, with a legend entry, from the standard EBITDA components.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 169: "Closing issuer-adjusted measure; reconciles exactly (calculations C35, C36)"; also line 164 "(calculation C35)"
   - Problem: The reader sees internal calculation register codes (C35, C36) with no explanation, and these are not reader language under the house standard. 'Reconciles exactly' is pipeline-check wording and gives no credit judgement.
   - Fix: Remove the codes from the reader-facing cell, or turn them into a labelled link to the calculation, and state the reconciliation in plain words (for example 'adds back to the 10-K figure').
4. **Medium · narrative** (New reader)
   - Where: line 161: "Opening reported measure; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 71"
   - Problem: The source is given as a raw pipeline file name with an accession number and a .jsonl extension. A committee member cannot read it, and on screen it wraps across two lines of the Basis column.
   - Fix: Show the source as 'TransDigm FY2024 Form 10-K, p. 71', with a link to the evidence record.
5. **Medium · narrative** (Saboteur)
   - Where: lines 157-169, the section as a whole (table only; no sentence that states a judgement)
   - Problem: The section never says what the bridge means for credit: how large the issuer's add-backs are relative to EBITDA, or that leverage elsewhere on the page is measured on the adjusted 4,173 rather than 3,813. A reader looking at the table alone could take 4,173 as clean EBITDA.
   - Fix: Open the section with a one-line bottom line, for example that issuer add-backs of USD 360 million take EBITDA from 3,813 to 4,173 and that this adjusted figure is the leverage denominator.
6. **Low · narrative** (Auditor)
   - Where: line 163: "Interest expense-net" vs line 142 "interest expense—net"
   - Problem: The same line item is written with a hyphen in one place and an em dash in another on the same page.
   - Fix: Use the filing's label consistently ('Interest expense—net').
7. **Low · visual** (Auditor)
   - Where: EBITDA bridge chart value labels '1715', '1286', '4173' (crop CP-1-050-a.png) and table Amount column lines 161-169
   - Problem: Amounts appear without thousands separators (1715, 4173), while the neighbouring Basis text uses 'USD 3,813 million'. This makes them harder to scan and inconsistent on the same page.
   - Fix: Format every amount with thousands separators (1,715; 4,173) in both the chart and the table.
8. **Low · visual** (New reader)
   - Where: EBITDA bridge chart, the three-column list of linked step names under the plot (CP-1_charts.png approx y920-990), and the 'Reporting unit' column repeating 'US$m' on all nine rows (CP-1_s-157.png top table)
   - Problem: The citation link list repeats all nine step names, and the unit column repeats the same value in every row. Both add vertical clutter without adding information, given that the chart header already reads 'US$m'.
   - Fix: Fold the citations into a single compact source line or the Table form, and put the unit in the column header (Amount, US$m).

### Chart data: leverage

Kind: chart · handoff lines 171-177 · verdict **BLOCK**

- Narrative: This is a data section, so it owes only the figures and their basis. The numbers are internally consistent (gross 6.01x and net 4.51x reconcile to USD 6,261m cash, and 5.55x pro forma reconciles). However, the key qualification, that pro forma net leverage is worse than the prior year, is buried in a Basis cell, and the headers do not name the adjusted EBITDA basis. Not verified: I did not check that this run folder is the latest run built under the latest code changes; this unit only reviews the copy supplied in ws2.
- Visual: The leverage bar chart is visible (not folded away), is zero-based with correctly proportioned bars, and its labels are readable. However, it shows a misleading net-leverage decline without the 5.55x pro forma figure, its chips expose "Handoff" and C-codes, and the plot leaves about a third of the card width empty.

1. **High · visual** (Saboteur, Auditor)
   - Where: Leverage chart, CP-1_charts.png crop (340,1060)-(1400,1450): FY2024 Net debt / EBITDA bar labelled 4.51; handoff line 176 "net figure uses year-end cash still holding the USD 4,216 million accrued dividend, 5.55x pro forma (calculation C11)"
   - Problem: The chart shows net leverage falling from 4.84x to 4.51x, but the only qualification, that the year-end cash includes a USD 4,216 million dividend paid on 2024-10-18 and pro forma net leverage is 5.55x, appears in the table's Basis cell. It does not appear in the chart, its legend or its note. A committee member reading the chart sees deleveraging where the pro forma position has worsened (4.84x to 5.55x). I checked this: (6.01x x 4,173 - 6,261 + 4,216 + 132) / 4,173 = 5.55x.
   - Fix: Plot FY2024 pro forma net leverage, 5.55x, as its own marked bar or point, or put a note directly under the chart, so the drawing itself shows the dividend effect.
2. **High · visual** (Auditor, New reader)
   - Where: Leverage chart chips under each period, CP-1_charts.png crop: "Handoff ●" and "Financial foundation · C07 · C08 ●" / "Financial foundation · C05 · C06 ●"
   - Problem: The chips put the pipeline word "Handoff" and internal calculation codes (C05-C08) on screen. The house standard forbids both as reader language, and the codes mean nothing to a reader who does not know the pipeline.
   - Fix: Label the provenance chips in reader terms, such as "Company 10-K FY2024, p. 55" or "Our calculation: gross debt / EBITDA As Defined", and keep calculation IDs behind the link.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: Line 173: "| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit |" with line 175 "over EBITDA As Defined"
   - Problem: The column headers and the chart legend say plain "EBITDA". The denominator is actually the issuer-adjusted EBITDA As Defined (USD 4,173m), not issuer EBITDA (USD 3,813m), and this is stated only in the Basis cell. A reader comparing with peers or with covenant tests will misread the basis. On issuer EBITDA, gross leverage would be about 6.6x.
   - Fix: Name the denominator in the header and legend, for example "Total debt / EBITDA As Defined (issuer-adjusted)".
4. **Medium · narrative** (Auditor, New reader)
   - Where: Section heading line 171 "### Chart data: leverage" and table at lines 173-176 rendered under it in CP-1_s-171.png (top of page)
   - Problem: The reader sees a heading that names a pipeline artifact ("Chart data") over a table that repeats the chart's four numbers. It has no judgement line, and gross leverage rising from 5.87x to 6.01x goes unremarked. The table looks like intermediate material rather than reader content.
   - Fix: Show these figures as the chart's "Table form" fold only, or give the section a reader heading such as "Leverage, FY2023-FY2024" with a one-line bottom line first.
5. **Low · visual** (Auditor)
   - Where: Leverage table, CP-1_s-171.png region approx (300,215)-(1160,345): monospaced column headers "Total debt / EBITDA", unit column "x", and "Basis" printed under each Period
   - Problem: The headers mix a code font with the sans-serif table text. The bare "x" unit column wastes width and the values carry no "x" suffix. The stray "Basis" label under FY2023 and FY2024 reads as part of the period.
   - Fix: Use one header typeface, print values as "5.87x" and drop the unit column, and give the Basis link a clearly separate treatment.
6. **Low · visual** (Saboteur)
   - Where: Leverage chart, CP-1_charts.png crop: plot area ends about two-thirds across the card; header reads "x · As of 30 September 2024"
   - Problem: The plot leaves about a third of the card's width empty on the right and has no y-axis or gridline. The card header's "As of 30 September 2024" sits above an FY2023 series dated 2023-09-30, and "x" alone is a cryptic unit label.
   - Fix: Stretch the plot to the card width, add a light zero-based axis labelled "times (x)", and drop the single as-of date or show it per period.

### Chart data: debt maturities

Kind: chart · handoff lines 192-202 · verdict **BLOCK**

- Narrative: The table's figures add up exactly: 93+92+92+6,637+4,768+12,637 = 24,319. However, the section has no bottom line or reader title, gives no fiscal year-end, and leaves its one material caveat (the USD 487 million FY2025 securitization) in a Basis cell.
- Visual: The Debt maturities chart is visible (not folded away) and labelled with US$m and its as-of date. It understates FY2025 maturities because the securitization is left out without a mark, it draws the cumulative \"Thereafter\" bucket as a single year, and its chips show pipeline vocabulary (\"Handoff\") plus a false \"citation without a page\".

1. **High · visual** (Saboteur, Auditor)
   - Where: Debt maturities chart, FY2025 bar labelled 93 (CP-1_charts.png, crop x340-1400 y2215-2640, saved as scratchpad/tmp/CP-1-054-a.png); handoff line 196: "excludes the securitization borrowings of USD 487 million maturing 2025-07-11"
   - Problem: The chart shows FY2025 maturities as 93 with no mark or note for the USD 487 million securitization due 2025-07-11, which the table excludes. The chart therefore puts real next-year maturities at about one sixth of their size (93 against roughly 580). The only caveat sits in the table's Basis cell, and the chart does not show it.
   - Fix: Show the USD 487 million securitization maturity in FY2025 as a separately labelled bar segment or chart footnote, so the near-term figure is not understated where the reader looks first.
2. **High · visual** (Auditor, New reader)
   - Where: Debt maturities chart, chip row under every bar: "Handoff" and "1 citation without a page" (scratchpad/tmp/CP-1-054-a.png, y~290-320)
   - Problem: "Handoff" is pipeline vocabulary on screen, which the house standard forbids. "1 citation without a page" contradicts the handoff, where every row cites "page 153" (lines 196-201). The chip tells a committee reader the figures are unsourced when they are sourced.
   - Fix: Remove the "Handoff" chip from the reader view and fix the citation chips so that page 153 of the 10-K shows as a sourced page.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: line 192-201: the section is only the heading "### Chart data: debt maturities" and a six-row table; no sentence states what the schedule means
   - Problem: Neither the section nor the chart states a bottom line, for example that about USD 23.6 billion of USD 24.3 billion falls in FY2028 or later, with a USD 6.6 billion wall in FY2028. The reader has to add up the rows to find the credit point. The heading "Chart data" is also a producer label, not reader language.
   - Fix: Open with a one-sentence bottom line on maturity concentration and refinancing timing, and give the section a reader title such as "Debt maturities".
4. **Medium · narrative** (New reader)
   - Where: line 198: "2027 subordinated notes mature 2027-11-15, in FY2028"
   - Problem: The section never says TransDigm's fiscal year ends 30 September. A reader cannot see why notes due in calendar 2027 sit in FY2028, or why the FY2027 bar is only 92.
   - Fix: State the fiscal year-end (30 September) once in the table caption or chart subtitle.
5. **Medium · visual** (Saboteur)
   - Where: Debt maturities chart, "Thereafter" bar 12637 drawn at the same width and spacing as single fiscal years (scratchpad/tmp/CP-1-054-a.png, right-most bar)
   - Problem: "Thereafter" combines every year from FY2030 onward into one bar and draws it like a single year, so it looks like the largest one-year wall. The chart does not say which years it covers.
   - Fix: Separate or relabel the bar, for example "FY2030+ (cumulative)", with a visual break or a different style so it is not read as one year.
6. **Low · narrative** (Auditor)
   - Where: line 201: "total USD 24,319 million reconciles to gross debt less finance leases (calculation C37); page 153"
   - Problem: Every row cites only "page 153" without naming the document, and "calculation C37" is an internal register code. The reader needs to find the Calculations table further down the page to make sense of it.
   - Fix: Name the source document, the FY2024 10-K, in the Basis or Source cell, and describe the reconciliation in words with the calculation link kept as a reference.
7. **Low · visual** (New reader, Auditor)
   - Where: Table rows (CP-1_s-192.png, y~255-460 at display scale): "6637", "12637", next to Basis text "USD 24,319 million"; chart caption "Missing values have no bar."
   - Problem: Amounts have no thousands separators, while the Basis text on the same row uses them. The "Debt maturing" header is set in monospace while the other headers are not. The "Missing values have no bar" footnote is boilerplate here, since this chart has no missing values.
   - Fix: Format amounts as 6,637 and 12,637, match the header typography, and show the missing-value footnote only when a value is actually missing.

### Chart data: debt stack

Kind: chart · handoff lines 203-219 · verdict **BLOCK**

- Narrative: This is a data table plus a one-line exclusion note: the figures match the source table (amounts sum to USD 24,302 million, which is 5.82x over USD 4,173 million), but the section has no bottom line, its unit labelling is inconsistent, and its cumulative leverage is not reconciled to the 6.01x shown in the leverage chart.
- Visual: The Debt stack chart is visible (not folded), but its repeating four-colour palette hides the secured/subordinated split, it has no axis, totals or segment labels, and its source chips show pipeline wording ('Handoff', 'upstream module') to the reader.

1. **High · visual** (Saboteur, Auditor)
   - Where: Debt stack chart, CP-1_charts.png crop x340-1400 y2650-3380 (stacked bar and row swatches)
   - Problem: The segment colours repeat a four-colour cycle with no link to rank or security. Term loans (secured, rank 1), 2031 secured notes and the 4.625% 2029 senior subordinated notes all share the same bright blue. The bar also has no axis, no segment amounts, no total and no marker where secured debt ends and subordinated debt begins, so a reader cannot see the priority structure, which is the point of the chart.
   - Fix: Colour segments by rank (one hue for secured, another for subordinated), mark the secured/subordinated break with its cumulative leverage (4.72x, then 5.82x), and label the total.
2. **High · visual** (Auditor, New reader)
   - Where: Debt stack chart rows, chips 'Handoff ●' and 'Financial foundation · C38 ●' to 'C47', and legend 'Chip dot: ● issuer page · ● handoff row · ● upstream module · ○ gap' (CP-1_charts.png, y≈2700-3370)
   - Problem: The words 'Handoff', 'handoff row' and 'upstream module' are pipeline vocabulary shown to the reader. This breaks the house rule, and the chips tell a portfolio manager nothing about the instrument.
   - Fix: Replace the chips with reader-language source links (filing and page), or drop them from the chart rows.
3. **Medium · narrative** (Saboteur)
   - Where: line 216: '4.875% 2029 senior subordinated notes | 2 | No | 750 | 5.82 | US$m | Same guarantor scope; cumulative over EBITDA As Defined USD 4,173 million'
   - Problem: The stack ends at 5.82x, but the leverage chart on the same page shows 6.01x total debt / EBITDA. The difference (USD 24,302 million in the stack against USD 25,068 million gross debt) is explained only by the unquantified exclusion note at line 218, so the page shows two disagreeing leverage figures.
   - Fix: State the excluded amounts (USD 487 million securitization, plus finance leases) in the note and reconcile 5.82x to 6.01x in one sentence.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 207: 'Term loans (Tranches I, J, K, L), matures 2028–2032 | 1 | Yes | 8702 | 2.09'; line 208: 'order within rank 1 is by maturity, not priority'
   - Problem: The running cumulative leverage across rank-1 rows implies the term loans sit ahead of the secured notes at 2.09x. They rank pari passu. The only caveat sits in row 2's Basis cell, where a reader scanning the leverage column will miss it.
   - Fix: Show one cumulative leverage figure per rank (secured 4.72x, then total 5.82x), or put the pari passu caveat in a note above the table.
5. **Medium · narrative** (New reader, Auditor)
   - Where: line 205: '| Facility | Ranking | Secured | Amount | Cumulative leverage | Reporting unit | Basis and limitation |'
   - Problem: The section has no bottom-line sentence, though a data module owes one (for example, how much debt is secured and secured leverage). 'Ranking' 1/2 is never defined. The 'Reporting unit' column says US$m on every row while 'Cumulative leverage' is a multiple, and its basis (gross debt over EBITDA As Defined USD 4,173 million) appears only in the last row.
   - Fix: Open with a one-line bottom line, define the ranking (1 = senior secured, 2 = senior subordinated), and put the unit on each value column header (US$m; x over EBITDA As Defined FY2024).
6. **Low · narrative** (Auditor, New reader)
   - Where: line 203: '### Chart data: debt stack'; line 218: 'are excluded from the stack; see Gaps.'
   - Problem: 'Chart data:' is production labelling, not a reader heading. 'see Gaps' sends the reader elsewhere to learn why the revolver and securitization are left out.
   - Fix: Title the section 'Debt stack by priority' and give the reason for each exclusion inline in the note.
7. **Low · visual** (New reader)
   - Where: Modules page table, CP-1_s-203.png region y≈220-870: monospace headers 'Ranking', 'Amount', 'Cumulative leverage' beside proportional headers; amounts '8702' with no separator beside 'USD 4,173 million' in the Basis cells
   - Problem: The headers mix typefaces and the numbers are formatted inconsistently on the same row, which makes the table look unfinished and slows reading. A 'Basis' tag repeats under every facility name.
   - Fix: Use one header typeface, thousands separators on amounts, and one Basis cue per table rather than per row.

### Calculations

Kind: prose/table · handoff lines 229-283 · verdict **CONCERNS**

- Narrative: The 48-row table's arithmetic checks out where spot-checked (C17, C24, C28, C37), but the section opens with pipeline wording and an inline source file name. It also never says which of several competing leverage and interest-cover ratios is the headline.
- Visual: The table is legible and fits the page width, but result formatting is inconsistent (no thousands separators, ten-decimal ratios, uneven bold). The \"Basis\" labels appear unevenly and are unexplained, which makes a long table harder to scan.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 231: "Helper scripts named by the method (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py and other scripts) were not run in this transport; their checks were done by hand and all arithmetic used the calculate tool."
   - Problem: This is pipeline vocabulary (script names, "method", "transport", "calculate tool") and it is the first thing the reader sees in the section, shown on screen in the shot's intro paragraph. A credit committee member cannot make sense of it, and it reads as a process caveat that weakens confidence in every row below.
   - Fix: Remove the process note from the reader view, or turn it into one plain limitation such as "Figures recomputed from the FY2024 annual report; not independently audited".
2. **High · narrative** (Auditor)
   - Where: Line 231: "All monetary inputs USD millions from the annual filing (TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl)."
   - Problem: A raw source file name sits inside a narrative sentence, which breaks the rule that source references live only in Basis lines, Source columns or ## Sources. The table also has no Source column, so the page numbers in "Inputs" have no named document beside them.
   - Fix: Move the document reference into a Source column or the Basis line and name it in reader terms ("FY2024 10-K"), keeping the sentence to the unit statement.
3. **Medium · narrative** (Saboteur)
   - Where: Lines 239-246 and 264: C05 "6.0071890726 (6.01x)", C09 "6.5743509048 (6.57x)", C11 "5.5487658759 (5.55x)", C12 "3.6036269430 (3.60x)", C30 "3.2449455677 (3.24x)"
   - Problem: The section gives four gross or net leverage figures and two FY2024 interest-cover figures (3.60x on cash interest, 3.24x on interest expense) and never says which is the headline or why. A reader skimming the table can quote the wrong one.
   - Fix: Mark which ratio feeds the bottom line, or group the rows under short labelled sub-heads (headline leverage, alternative definitions, pro forma for the dividend).
4. **Medium · narrative** (New reader)
   - Where: Lines 272-281: "C38 | Cumulative / EBITDA As Defined | 8,702 / 4,173 | 2.0853103283 | x" through C47
   - Problem: Ten rows say only "Cumulative" and do not name the instrument the cumulative debt runs through. To learn what 2.09x or 5.82x refers to, the reader has to cross-reference the debt-stack table in another section. Unlike C05-C30, these rows also show no rounded ratio.
   - Fix: Name each cumulative step (e.g. "through 2029 secured notes") and show the ratio to two decimals, as the other rows do.
5. **Medium · visual** (New reader, Saboteur)
   - Where: Result column, screenshot CP-1_s-229.png, whole table (e.g. C01 "25068", C05 "6.0071890726 (6.01x)", C38 "2.0853103283" in bold)
   - Problem: USD m results print with no thousands separator (25068), while the Inputs column next to them uses separators (25,068). Ratios print to ten decimal places. Bold is applied to some rows (USD m, C38-C47) and not to others (C05-C14). The eye is drawn to unrounded noise rather than to the figure that matters.
   - Fix: Format results the same way across the table: thousands separators for USD m, two-decimal x and one- or two-decimal %, with full precision left in the calculation JSON.
6. **Medium · visual** (Auditor, New reader)
   - Where: ID column, crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1-057-a.png: "C01 Basis", "C05 Basis", while C06 has none
   - Problem: A grey "Basis" label appears under some IDs and not others. Nothing explains what it means or whether it can be clicked, so rows with and without it look like they differ in quality of support.
   - Fix: Either show a consistent, clearly labelled source cell on every row, or style "Basis" as an obvious control with a legend.
7. **Low · narrative** (Saboteur)
   - Where: Line 244: "C10 | C02 + dividend paid + dividend equivalents paid | 18,807 + 4,216 + 132 (paid 2024-10-18, p.63)"
   - Problem: The dividend was paid after the 2024-09-30 as-of date, but the formula reads like a historical cash item. The fact that C10/C11 are pro forma shows only in the date inside the inputs cell.
   - Fix: Label C10, C11 and C28 explicitly as "pro forma for the October 2024 special dividend" in the Formula cell.
8. **Low · visual** (New reader)
   - Where: Unit column, lines 252, 256, 265: "0.2057706910 (20.58%) | fraction"
   - Problem: The unit reads "fraction" while the reader-facing value in brackets is a percent, so the unit cell contradicts what the reader sees.
   - Fix: Label these rows "%" and show the percent as the result.

### Gaps

Kind: prose/table · handoff lines 284-295 · verdict **BLOCK**

- Narrative: The Gaps content is substantive: the missing covenant documents and the quarterly figures are correctly flagged as the binding limits. But it opens with no judgement, routes actions to pipeline modules, uses internal tags, and is inconsistent about whether the securitization facility is in total debt.
- Visual: This section has no chart; it is a clean four-column table that is readable overall. The problems are stray inline \"Basis\" chips in the Gap column and three-line wrapped raw filenames in the Source column that inflate row height.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: Source column, lines 290-294: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 62–63" (same string on 5 of 7 rows); screenshot CP-1_s-284.png, Gaps table Source column (x 950-1155, y 1545-1850 displayed)
   - Problem: The reader sees the pipeline's internal extract filename, including an EDGAR accession number and a `.jsonl` extension, where a document citation should be. It wraps over three lines in every row and means nothing to a PM. Rows 288-289 instead cite "Source readiness", which is a module, not a document.
   - Fix: Give a reader citation such as "FY2024 10-K, pp. 62–63", and for the first two rows name the missing document rather than the module.
2. **High · narrative** (Auditor + New reader (promoted))
   - Where: line 292 "CP-4 to confirm from documents"; line 294 "CP-1D or CP-2 to assess"; line 289 "Q1 FY2024 filing absent per CP-0" … "in a later pass"; line 293 "Liquidity chart FY2023 undrawn cell not supplied"
   - Problem: The Action and Effect cells send the reader to pipeline steps: on screen they show as module names ("Legal & covenants to confirm", "Earnings quality or Fundamental credit to assess", "per Source readiness"), plus "later pass" and "cell not supplied". That is workflow routing, not reader language, and the house rule bans pipeline vocabulary.
   - Fix: State each action as what is needed and why it matters to credit (e.g. "Read the revolver lien terms in the credit agreement"), with no module routing and no pass or cell wording.
3. **Medium · narrative** (Saboteur)
   - Where: line 290 "Securitization facility legal rank not stated | Excluded from debt stack; USD 487 million collateralised by domestic trade receivables, matures 2025-07-11" vs line 291 "Excluded from debt stack, included in total debt"
   - Problem: The finance-lease row says it is still in total debt, but the securitization row does not, though C01 (line 235) does include the USD 487 million in the 25,068 total debt. The maturity schedule also leaves it out (line 196). A reader can conclude that a facility due in nine months is outside both leverage and maturities.
   - Fix: Say in the Effect cell that the USD 487 million is in total debt and leverage but outside the ranked stack and the maturity chart.
4. **Medium · narrative** (Saboteur)
   - Where: line 288 "Covenant-defined net debt, secured net debt and Consolidated EBITDA ... cannot be computed; house ratios are not covenant ratios" (Gaps table, no lead sentence at line 284-286)
   - Problem: The table has no judgement first. Nothing says which gap matters most to the credit view: no covenant headroom can be assessed at about 5.5x pro forma net leverage. All seven rows read with equal weight, including "None needed for snapshot".
   - Fix: Open with one sentence naming the gap that limits the credit view most and what it blocks, then order the rows by materiality.
5. **Medium · narrative** (New reader)
   - Where: line 288 "[Insufficient Information]"; line 292 "Rank 1 pari passu treatment rests on \"senior secured\" labels"
   - Problem: "[Insufficient Information]" is a bracketed internal status tag that appears on only two rows. "Rank 1" refers to the module's own debt-stack numbering, which a reader on this table cannot decode.
   - Fix: Drop the bracket tag (or make it a consistent status column) and write "first-lien pari passu treatment" instead of "Rank 1".
6. **Medium · visual** (Auditor + New reader (promoted))
   - Where: Gaps table, Gap column, screenshot CP-1_s-284.png crop y 1545-1850 displayed: "stated Basis", "rank not stated Basis", "list not read Basis", "not read Basis", "pages read Basis"
   - Problem: An orphan "Basis" chip sits inline at the end of the gap text in five rows, with nothing beside it. It reads as part of the sentence and is a stray artifact on two-line wraps (row 6 puts it alone on its own line).
   - Fix: Remove the chip from the table cells, or make it a clearly styled, aligned control that opens the basis it refers to.
7. **Low · visual** (Auditor)
   - Where: Gaps table column widths, screenshot CP-1_s-284.png y 1355-1860 displayed
   - Problem: The unbroken filename forces the Source column to wrap to three lines with mid-token breaks ("10-" / "K_0001260221-24-000083_tdg-"). That doubles the row height and leaves the Action column cramped beside a wide Effect column.
   - Fix: Once citations are short, rebalance the columns so each row fits on one or two lines.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 296-299 · verdict **CONCERNS**

- Narrative: Both passages are run plumbing: the Request uses pipeline terms and a raw pathway identifier, and Next module is routing between modules shown to the reader; its figures (23,155 and 2,919) match C10 and C28 but carry no definition or basis.
- Visual: The section has no chart, map or timeline, only two plain paragraphs whose typography is clean; the visual issues are their equal billing in the page navigation and that Next module ends the page unmarked below dense tables.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 3: "CP-1 canonical financial data and KPI foundation for TransDigm Group Incorporated (TDG), as of 2024-09-30, on the credit_snapshot pathway. ... the house calculations downstream modules draw on." Rendered in CP-1_s-1.png (Request, y~220-260) as "Financial foundation canonical financial data and KPI foundation..."
   - Problem: Pipeline vocabulary reaches the screen: "canonical", the raw identifier "credit_snapshot pathway" (with its underscore), and "downstream modules draw on". Swapping the module name in for the CP-1 code also produces the stuttering phrase "Financial foundation canonical financial data and KPI foundation". This breaks the house rule against pipeline wording on screen (promoted because two personas caught it).
   - Fix: Write the Request as a plain scope statement for the reader, e.g. "Audited FY2024 and FY2023 figures for TransDigm as of 30 September 2024 (credit snapshot): ...", with no pipeline terms or raw identifiers.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 298: "CP-1A and CP-2 can proceed on this foundation, carrying the pro forma dividend adjustment ... as the creditor-relevant as-of position"; rendered in CP-1_s-296.png (Next module, y~1895-1940) as "Business & governance and Fundamental credit can proceed on this foundation"
   - Problem: The whole Next module paragraph is routing between modules, telling other modules what to carry. A portfolio manager gets nothing from it, and it shows on the page under a reader heading "Next module". It breaks the house rule against pipeline or module wording leaking to the reader (promoted because two personas caught it).
   - Fix: Keep the routing note out of the reader view, or rewrite it as a reader statement: "The as-of position used for credit is pro forma for the 18 October 2024 dividend: net debt USD 23,155 million, liquidity USD 2,919 million; covenant ratios cannot be computed without the credit agreement."
3. **Medium · narrative** (Saboteur)
   - Where: Line 298: "carrying the pro forma dividend adjustment (net debt USD 23,155 million, liquidity USD 2,919 million) as the creditor-relevant as-of position"
   - Problem: The figure has no definition, no date for the dividend and no Basis. On the same page the Calculations table shows a different house net debt, C26 = 13,441 (CP-1_s-296.png y~440). A reader who meets 23,155 here without knowing it is C10 (total debt plus the 2024-10-18 dividend) could mix up the two measures.
   - Fix: Name the measure and date ("total net debt pro forma for the USD 4,348 million dividend paid 18 October 2024") and put the C10/C28 reference in a Basis line.
4. **Low · visual** (New reader)
   - Where: CP-1_s-1.png left rail "On this page" (y~450-980): "Request" and "Next module" listed as peers of "Bottom line" and the statements
   - Problem: The navigation gives two plumbing sections the same billing as the analysis. "Next module" closes the page with a two-line paragraph straight under a 30-row calculation table and the Gaps table, with nothing setting it apart.
   - Fix: Drop these entries from the reader navigation, or group them under a muted "Run scope" item, so the page ends on findings and gaps.
5. **Low · visual** (Auditor)
   - Where: CP-1_s-1.png Request block (y~195-265) followed directly by the Sources table with full sha256 columns (y~315-530)
   - Problem: The Request paragraph is laid out cleanly, but it opens straight into 64-character hashes, so the reader's first view after the charts is machine identifiers. This is an adjacent layout effect; the hash table is outside this unit.
   - Fix: Show the scope sentence as a short caption under the module title and keep the hash columns in Evidence.

### Sources

Kind: prose/table · handoff lines 5-17 · verdict **BLOCK**

- Narrative: The Sources section is a fact table plus one footnote, so the judgement-first order does not apply to it. But its wording leaks pipeline language ("Supplied handoff", "pinned pack", "this pass"), names the controlling filing only by its extraction file name, and buries the fact that the pro forma figures were not checked against the available Q1 FY2025 filing.
- Visual: The section is two bordered tables and a full-width footnote. The tables are clean and legible, but the sha256 hash column takes most of the width and wraps the source name over three lines, and the second table repeats the same label in two columns. There is no chart in this section.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 12: "| Supplied handoff | Module | sha256 |" (rendered as the "Supplied handoff" table header, CP-1_s-5.png y~385); line 16: "Sources in the pinned pack not relied on here"
   - Problem: Pipeline words show on screen: "handoff" is named in the house standard as not reader language, and "pinned pack" and "in this pass" are internal run terms. A reader who does not know the pipeline cannot tell what a "supplied handoff" is or why it counts as a source.
   - Fix: Label the table something like "Other analysis relied on" and describe the unused filings plainly, e.g. "Filings available but not used here", with no run or pipeline wording.
2. **Medium · narrative** (New reader, Auditor)
   - Where: Line 9: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"
   - Problem: The source is named only by its extraction file name (accession number, .htm.jsonl), not as a document the reader knows, such as "Form 10-K for fiscal year ended 30 September 2024". The reader has to decode a file path to learn which filing controls every figure.
   - Fix: Lead with a plain document name (form, fiscal year, filing date), with the file identity secondary or on the Evidence page.
3. **Medium · narrative** (Saboteur)
   - Where: Line 16: "the Q1 FY2025 quarterly filing (subsequent events taken from the annual filing instead)"
   - Problem: The bottom line's pro forma leverage of 5.55x and liquidity of USD 2,919 million depend on the October 2024 dividend. The Q1 FY2025 filing that would confirm the actual payment and post-payment balance sheet was available but not used, and that choice appears only in the Sources footnote. A committee could read the pro forma figures as confirmed when they are estimated from the annual filing's subsequent-event note.
   - Fix: State in the limitations next to the pro forma figures that they rest on the annual filing's subsequent-event disclosure and were not checked against the available Q1 FY2025 filing.
4. **Medium · visual** (New reader, Saboteur)
   - Where: Sources table, sha256 column, CP-1_s-5.png region x 300-1160, y 215-365 (both tables)
   - Problem: 64-character sha256 hashes take about 40% of the table width. That squeezes the Source column, so the filing name wraps over three lines. A credit reader gets nothing from a hash, and it pushes the useful "Use in this module" text into a narrow column on the right.
   - Fix: Drop the hash from the reader view, or move it to a hover/fold or the Evidence page, so Source and Use take the full width.
5. **Low · narrative** (New reader)
   - Where: Line 10: "| context | f7b95e1f... | Run settings (as-of, current period fy-2024, prior fy-2023, USD); not issuer evidence |"
   - Problem: A source row called "context" that is "not issuer evidence" is run configuration presented as a source, and it uses internal period tokens ("fy-2024").
   - Fix: Remove run settings from the reader's source list, or turn them into one plain sentence: "Figures as of 30 September 2024 in USD; current year FY2024, prior FY2023."
6. **Low · visual** (Auditor)
   - Where: Supplied handoff table, CP-1_s-5.png y~375-435: columns "Supplied handoff" and "Module" both read "Source readiness"
   - Problem: With module codes stripped, the two columns now show the same text, so one column is redundant and the table looks broken.
   - Fix: Collapse to a single name column (or drop the table into a sentence), since the module name and the input name are the same.

### Bottom line

Kind: reader passage · handoff lines 20-27 · verdict **BLOCK**

- Narrative: The bottom line puts its judgement first and its figures check out (6.01x, 4.51x, 5.55x, 4.72x, 52.56%, -158 and USD 2,919 million all reconcile to the handoff's calculations). But it ends in pipeline wording ("foundation ... downstream use ... the pack"), calls company-defined liquidity "cash liquidity", and the first paragraph is too dense for a reader who has not seen the 10-K.
- Visual: The section has no chart of its own, only two paragraphs. They are set entirely in large bold type in a half-width column with heavy monospace figure tokens, and a line break separates the minus sign from \"158 million\". The charts below the section belong to other units and were not judged.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 25: "The foundation is ready for downstream use with two restrictions: covenant-defined ratios cannot be computed because the credit agreement is not in the pack, and no quarterly or last-twelve-month trend is built here."
   - Problem: "Foundation", "downstream use", "the pack" and "built here" are pipeline words, and they close the bottom line a portfolio manager reads. The house rule bars this wording from the reader, and it gives a committee member nothing about the credit.
   - Fix: Give the two limits in reader terms, e.g. covenant ratios are not assessed because the credit agreement was not reviewed, and the analysis uses fiscal-year figures only with no quarterly or LTM trend. Drop the readiness statement.
2. **Medium · narrative** (Saboteur)
   - Where: Line 22: "pro forma cash liquidity falls from USD 7,267 million to USD 2,919 million"
   - Problem: The USD 7,267 million is not cash. The handoff's own table (line 143) builds it as cash 6,261 + revolver 843 + securitization 163, so it is company-defined liquidity. A reader who sees "cash liquidity" next to "year-end cash balance" will take 7,267 as the cash figure and understate how much of the 2,919 is undrawn committed lines. The calculation behind 2,919 (C28) is also missing from the Basis line on line 23.
   - Fix: Call it "liquidity (cash plus undrawn revolver and securitization)" and add C28 to the Basis line.
3. **Medium · narrative** (New reader)
   - Where: Line 22: "TransDigm enters FY2025 as a highly levered but strongly cash-generative credit whose leverage is set by shareholder distributions rather than operations: total debt is 6.01x FY2024 EBITDA As Defined and net debt 4.51x..."
   - Problem: The first paragraph is about 150 words in two sentences and carries 12 figures, so the judgement in the first clause gets lost. "EBITDA As Defined" appears four times and is never explained as management's adjusted non-GAAP EBITDA.
   - Fix: Keep the one-sentence judgement up front, split the pro forma leverage and the FCF-versus-dividend points into short sentences, and say once that EBITDA As Defined is the company's adjusted (non-GAAP) EBITDA.
4. **Medium · visual** (Saboteur, Auditor)
   - Where: Screenshot CP-1_bottom-line.png, first paragraph, crop region x 330-1440, y 180-720 (CP-1-042-a.png): line break at "leaving USD -" / "158 million"
   - Problem: The minus sign and "USD" sit outside the monospace figure token, and the line breaks between them. The highlighted figure on the next line therefore reads as a positive "158 million", which is exactly the sign a committee needs to see. Raised by both personas, so promoted from Low.
   - Fix: Render the negative value as one unbreakable figure token that includes the sign, e.g. "USD −158 million" or "a USD 158 million shortfall".
5. **Medium · visual** (New reader)
   - Where: Screenshot CP-1_bottom-line.png, y about 190-970 (display coords): both bottom-line paragraphs
   - Problem: About 370 words are set entirely in large bold display type, in a column about 550 px wide that leaves the right half of the 1440 px page empty. Every word carries the same weight, so the judgement sentence does not stand out. The dotted-underlined monospace figures every few words make the text read in bursts and stretch the section to roughly 780 px of dense bold.
   - Fix: Set only the opening judgement sentence in lead or bold style and the rest in body weight, as in the VMO2 reference, and keep figure styling quieter.
6. **Low · narrative** (Saboteur)
   - Where: Line 25: "scheduled maturities are USD 93 million to USD 92 million a year until FY2028, when USD 6,637 million falls due"
   - Problem: "93 million to 92 million" reads like a range typed backwards and does not say which years. The real message, a near-term maturity cliff of USD 6,637 million in FY2028, is buried behind it.
   - Fix: Lead with the FY2028 wall and give the small annual amounts as "about USD 92-93 million a year in FY2025-FY2027".
7. **Low · narrative** (New reader)
   - Where: Line 25: "no maintenance test outside the springing revolver test at 7.50x and incurrence tests at 7.25x net and 5.00x secured net leverage"
   - Problem: "Springing", "maintenance" and "incurrence" tests are packed into one clause with three thresholds. The clause also does not say that 7.25x net leverage compares with the 5.55x pro forma figure, which is the point about headroom.
   - Fix: State the headroom directly, e.g. pro forma net leverage 5.55x against a 7.25x incurrence limit, and give the covenant mechanics in a short second sentence.

### Source context

Kind: prose/table · handoff lines 42-49 · verdict **CONCERNS**

- Narrative: This is a data table with no prose. It shows pipeline wording (the "context" row, "Extraction support", the .jsonl file names), and its page citation does not cover the debt note and non-GAAP items it lists.
- Visual: No chart is in scope. The 8-column table wraps heavily and wastes vertical space, the raw file names break mid-token, and two columns share the header "Source".

1. **High · narrative** (Auditor, New reader)
   - Where: line 48: "| context | Not issuer evidence | Run settings | as-of 2024-09-30 | USD | n/a | Settings only; blanks are not zero | context |"
   - Problem: This row describes the run's internal settings, not a source. It shows the pipeline term "context" as both the source name and its citation, and adds a "blanks are not zero" processing note. A reader who has not seen the sources cannot tell what document it means.
   - Fix: Remove the run-settings row from the reader table, or move the as-of date into the section header as plain text.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 46: "Income statement, balance sheet, cash flow statement, non-GAAP reconciliation, debt note, guarantor summary | ... | ...tdg-20240930.htm.jsonl, pages 120–123"
   - Problem: The row lists the non-GAAP reconciliation, debt note and guarantor summary but cites only pages 120–123. The same handoff cites those items elsewhere: pages 55 and 62–63 and 70–71 (lines 117, 143, 225, 290), pages 144–145 and 153 (lines 128, 196), and page 59 (line 47). A reader checking the debt note against this citation would not find it.
   - Fix: Give each statement kind in this row its own page range, or split the row so that each cited range covers what it claims.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 46: "Supports extraction; statement rows read directly" and "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"
   - Problem: The "Extraction support" column and the raw .jsonl file name with its accession number are pipeline vocabulary. A portfolio manager reads them as noise rather than as a citation of the 10-K.
   - Fix: Cite the source as "Form 10-K FY2024, pp. x–y" and rename or drop the extraction column, for example as "Use" with "Full statements" / "Obligor-group context only".
4. **Medium · visual** (New reader, Saboteur)
   - Where: Source context table, CP-1_s-42.png crop (340,220)-(1400,740), saved as tmp/CP-1-044-a.png
   - Problem: Eight narrow columns force every cell to wrap into four to eight lines; the file name breaks mid-token at "TDG_2024-09-/30_10-/K_...". The section reads as a tall, sparse block where three rows take about 400 px.
   - Fix: Cut the table to about five columns (Source, Perimeter, Statements, Periods, Basis) with a short human citation, so each row fits in two or three lines.
5. **Low · narrative** (New reader)
   - Where: line 47: "TransDigm Inc. issuer with TD Group, TransDigm UK and domestic restricted subsidiaries, excluding non-guarantors"
   - Problem: "TD Group" and "restricted subsidiaries" are not defined here. The table also never says why a combined, non-consolidated guarantor summary matters for credit (structural position of the obligor group).
   - Fix: Spell out TransDigm Group Incorporated, and add a few words saying this is the notes' obligor group.
6. **Low · visual** (Auditor)
   - Where: Source context table header row and first column, tmp/CP-1-044-a.png
   - Problem: Two columns are both headed "Source". The "Basis" chip sits under each source name in the first column, which suggests a link to an evidence basis for a row that is itself the source.
   - Fix: Rename the first column, for example "Document", and leave the Basis chip off rows whose citation is already in the Source column.

### Reported income statement (as printed, expenses as positive magnitudes)

Kind: prose/table · handoff lines 50-70 · verdict **CONCERNS**

- Narrative: The figures are correct (the subtotals and the 149+163=312 D&A tie in both years) and the voice is neutral. But the note under the table is a reconciliation memo with no credit judgement, it carries calculation IDs in the sentence, and its D&A figures have no period.
- Visual: The table is legible and the numbers are right-aligned in tabular figures. The redundant two-line file-name Source column and the Sign convention column take most of the width and double the row height, and subtotals are not visually set apart.

1. **High · narrative** (Auditor, New reader)
   - Where: line 68: "it reconciles exactly in both years (calculations C19 and C20), with no unresolved difference"
   - Problem: Internal calculation IDs sit inside the narrative sentence and render as code-style chips (CP-1_s-50.png, y~915). This breaks the rule that references live only in the Basis line, and C19/C20 mean nothing to a reader who has not seen the pipeline.
   - Fix: Drop the parenthetical from the sentence and leave C19/C20 in the Basis line, which already lists them (line 69).
2. **Medium · narrative** (Saboteur)
   - Where: line 68: "All amounts USD millions. The expense block between gross profit and income from operations is selling and administrative expenses plus amortisation of intangible assets"
   - Problem: The only prose under the table opens with a unit note and an arithmetic check, not a credit point. The things a committee needs from these figures (net sales up ~21% to 7,940; interest expense of 1,286 taking ~36% of operating income) are never stated, so the reader has to work them out.
   - Fix: Open with a one-sentence bottom line on growth, margin and interest burden, then put the reconciliation and D&A notes after it.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: line 68: "Total D&A of USD 312 million used in EBITDA ... and the USD 2 million gap (product certification costs, by the label) is retained, not resolved."
   - Problem: The D&A figures have no fiscal year, although the table beside them shows two years. "Retained, not resolved" and "by the label" are process wording, so the reader cannot tell whether the 2 million difference affects EBITDA.
   - Fix: Label the figures FY2024 and say in plain words that the 2 million is product-certification amortisation and is included in EBITDA D&A.
4. **Medium · visual** (New reader, Auditor)
   - Where: Source column, every row, CP-1_s-50.png x~850-1160, y~250-880: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 121"
   - Problem: The same long internal file name is repeated on all 13 rows and wraps onto two lines, which doubles the row height. It is the widest column in the table and tells the reader nothing new. The ".jsonl" extraction-file name is pipeline detail, not a document a reader recognises.
   - Fix: Give the source once as "FY2024 Form 10-K, p.121" in a caption or a short column, and keep per-row detail behind the Basis chip.
5. **Low · narrative** (New reader)
   - Where: line 52-66 Sign convention column: "Outflow printed as magnitude", "Signed", "Parentheses = income"
   - Problem: The column repeats a data-entry convention on every row in technical wording ("Signed", "magnitude"), and the section heading already says expenses are positive.
   - Fix: Replace the column with a single caption line on sign convention.
6. **Low · visual** (New reader)
   - Where: Line column, CP-1_s-50.png y~250-880: "NET SALES", "INCOME FROM CONTINUING OPERATIONS BEFORE INCOME TAXES"
   - Problem: Every line is in full capitals and subtotals look the same as expense lines (no bold or rule), so Gross profit, Income from operations and Net income do not stand out when scanning.
   - Fix: Set the lines in sentence case and give subtotal rows bold weight or a top rule.
7. **Low · visual** (Auditor)
   - Where: paragraph under the table, CP-1-045-a.png: "USD 312 million", "USD 149 million", "USD 163 million"
   - Problem: Amounts in the prose are set in an underlined monospace face, while the rest of the sentence is in the body font, so the paragraph reads like code. There is also no visible Basis affordance for the paragraph, although every table row has one.
   - Fix: Show prose numbers in the body font, with any link affordance kept subtle, and add a Basis chip for the paragraph like the row chips.

### Reported cash flow extract (signed as printed)

Kind: prose/table · handoff lines 71-90 · verdict **CONCERNS**

- Narrative: The figures look exact and signs and the printed dash are kept, but the section is a table with only a units note: no judgement, no investing subtotal, and one combined slash row.
- Visual: The table is clean and readable at 1440 px, but its numbers are left-aligned (the balance-sheet table below is right-aligned), the combined repayments cell breaks the column, and a repeated two-line .jsonl source string doubles the height of every row.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 89: "All amounts USD millions." (the only text after the table at lines 73-87)
   - Problem: The section gives 13 rows and no judgement. FY2024 operating cash of 2,045 against capex (165), acquisitions (2,347) and dividends (2,038) means cash after dividends and M&A was deeply negative and paid for with debt. The text never says so, so the reader has to work out the credit point alone. The neighbouring income-statement extract (line 68) does carry an explanatory paragraph.
   - Fix: Add a one-sentence bottom line under the table, with its own Basis line, saying how FY2024 operating cash compares with capex, acquisitions and the dividend, and that net borrowing funded the gap.
2. **Medium · narrative** (Saboteur)
   - Where: lines 75-85: operating "2,045" and financing "3,171" totals are given; no net cash used in investing activities row appears; "Net increase in cash and cash equivalents | 2,789 | 471"
   - Problem: The table shows the operating and financing totals but not the investing total. The reader cannot reconcile to the 2,789 net increase in cash and may take the selected investing lines for the whole investing outflow.
   - Fix: Add the printed net cash used in investing activities subtotal so the three subtotals reconcile to the change in cash, or say that the extract is selective.
3. **Medium · narrative** (New reader)
   - Where: line 82: "Repayments of senior secured notes / subordinated notes / term loans | (4,400) / (550) / (4,403) | (1,122) / (1,459) / (7,334)"
   - Problem: Packing three instruments and six figures into one row with slashes makes the reader match positions to work out which repayment is which. It also hides that total repayments (9,353 in FY2024) were far smaller than the 14,188 of new notes and term loans.
   - Fix: Give each instrument its own row, or add a total repayments row next to the proceeds rows so net new borrowing can be read off directly.
4. **Medium · visual** (Auditor, New reader)
   - Where: Cash flow table, FY2024/FY2023 columns; CP-1_s-71.png crop (340,220)-(1400,1100) saved as tmp/CP-1-046-a.png
   - Problem: Numbers in this table are left-aligned, so the digits do not line up. The balance-sheet table directly below right-aligns its numbers, so the page is inconsistent. The repayments row prints three values in a smaller, non-bold proportional font that wraps over two lines and breaks the column.
   - Fix: Right-align both period columns in tabular figures, and split the combined repayments row into three rows with one value per cell.
5. **Medium · visual** (New reader, Auditor)
   - Where: Source column, every row (lines 75-87): "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 123"; screenshot right column
   - Problem: The same internal file name, including the pipeline's .jsonl extension, appears 13 times and wraps onto two lines in every row. It doubles the table's height and shows the reader pipeline file names where a document name belongs.
   - Fix: Show a reader label such as "FY2024 10-K, p. 123", and state the source once when every row shares it.
6. **Low · narrative** (New reader)
   - Where: line 71: "Reported cash flow extract (signed as printed)"; line 86: "(supplemental, magnitude)"; line 83: "— (printed dash)"
   - Problem: "Signed as printed", "magnitude" and "printed dash" are extraction vocabulary, not language a portfolio manager uses. Each one makes the reader stop and decode the sign convention.
   - Fix: Use a plain heading such as "Cash flow statement (FY2024 10-K)" with one note on signs: "outflows in parentheses; cash paid for interest and taxes shown as positive amounts".
7. **Low · visual** (Auditor)
   - Where: "Basis" chip after every line label; CP-1_s-71.png table rows
   - Problem: Every row label ends with a grey "Basis" chip. Thirteen identical chips add noise, and some wrap onto a second line (for example the securitization row), which makes rows taller.
   - Fix: Show the Basis link once for the table, or as an icon-only cue that never wraps.

### Chart data: interest cover

Kind: chart · handoff lines 178-184 · verdict **BLOCK**

- Narrative: The section is a two-row data table whose figures are exact and agree with line 140 (3.60x and 2.93x). However, it has a pipeline-style heading, states no bottom line, and shows only the most favourable cover measure, without the 3.24x and 3.29x alternatives the module itself calculated.
- Visual: The bar chart is legible and proportional from a zero baseline: bar heights 139/113 match the 3.60/2.93 ratio. However, the chip row shows the banned 'Handoff' label and bare calculation codes, and the unit and date labelling and the use of card width are weak.

1. **High · visual** (Auditor, New reader)
   - Where: Interest cover chart, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots2/CP-1_charts.png, chip row under the FY2023 and FY2024 bars (crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1-052-a.png, y about 285-305)
   - Problem: Each bar has a 'Handoff' chip and a 'Financial foundation · C13' / '· C12' chip. 'Handoff' is pipeline vocabulary the house standard bans from the screen, and the bare calculation codes mean nothing to a reader who does not know the pipeline. Two personas caught this, so it was promoted from Medium.
   - Fix: Remove the 'Handoff' chip and label the provenance in reader terms, e.g. 'Calculated: EBITDA As Defined ÷ cash interest paid, 10-K FY2024', with the calculation reference kept in the table's Basis column only.
2. **Medium · narrative** (Saboteur)
   - Where: line 182-183: "| FY2024 | 3.60 | x | EBITDA As Defined over cash paid for interest, net; calculation C12 |" (compare line 142: "EBITDA As Defined / interest expense—net | 3.24x")
   - Problem: The chart and its table show only the cash-interest cover (3.60x FY2024). The same module calculates 3.24x on interest expense-net and 3.29x on issuer EBITDA, and neither is noted here. A committee reading the chart sees the most favourable of three cover measures with nothing to say it is the high end.
   - Fix: Add one line to the Basis or a chart note saying that cover on interest expense-net is 3.24x and on issuer EBITDA is 3.29x for FY2024, so the reader sees the range.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 178: "### Chart data: interest cover"
   - Problem: The heading 'Chart data:' describes the pipeline's purpose, not the content, and it shows in the page's on-this-page index and section title. The section also states no bottom line, such as whether cover improved and what it means, which a data module still owes.
   - Fix: Retitle it 'Interest cover, FY2023-FY2024' and open with a one-sentence bottom line, e.g. cash interest cover rose from 2.93x to 3.60x.
4. **Low · visual** (Auditor)
   - Where: Interest cover chart header 'x · As of 30 September 2024', /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1-052-a.png, top right
   - Problem: The unit is a bare 'x' and the header gives a single as-of date over two fiscal-year periods. The chart has no y-axis, and the plot fills only about two thirds of the card width, leaving empty space on the right.
   - Fix: Label the unit as 'times (x)', write the date as 'Fiscal years to 30 September', and either span the full card width or add a light axis.
5. **Low · visual** (New reader)
   - Where: Table 'Chart data: interest cover', /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots2/CP-1_s-178.png, top region (y about 190-310 displayed)
   - Problem: The column header 'EBITDA / cash interest' is set in monospace while the other headers are in the sans face. The unit 'x' sits in its own column away from the values, and each period cell carries a stray 'Basis' chip, which adds visual noise to a two-row table.
   - Fix: Use the sans face for every header, print the values as '2.93x' and '3.60x', and drop the separate unit column for this ratio table.

### Chart data: liquidity

Kind: chart · handoff lines 185-191 · verdict **BLOCK**

- Narrative: The table is a data section with no bottom line on liquidity. Its most important limitation, that FY2024 cash includes the 4,216 dividend paid in October, is buried at the end of a cell, and the section uses pipeline wording ("not read in this pass", C29, a .jsonl file name) where the reader should see plain language.
- Visual: The two-period bar chart is clean and readable, with a legend, unit and as-of date. However, the FY2024 cash bar overstates the cash actually available, the chips show pipeline terms ('Handoff') and a citation count that conflicts with the table, and the table's FY2023 gap cell wraps a monospace sentence inside a numeric column.

1. **High · visual** (Saboteur, New reader)
   - Where: Liquidity chart, FY2024 Cash bar labelled 6261 (CP-1_charts.png, crop x340-1400 y1820-2210, saved as scratchpad/tmp/CP-1-053-a.png); handoff line 190: "cash includes the accrued USD 4,216 million dividend paid 2024-10-18"
   - Problem: The chart shows FY2024 cash of 6,261 and says nothing about the dividend. About 4,216 of that cash was paid out 18 days after the year end, so the bar suggests liquidity almost doubled when it actually fell. The caveat appears only at the end of a long Basis cell in the table, which is folded on the Charts panel. The 163 of securitization capacity counted as undrawn was also drawn in October 2024.
   - Fix: Show the pro forma cash after the dividend (or mark the bar as including committed outflows) directly on the chart, using the same treatment as the 5.55x pro forma leverage.
2. **Medium · narrative** (Auditor, New reader)
   - Where: Line 189: "Not supplied: FY2023 revolver and securitization availability not read in this pass"
   - Problem: "Not read in this pass" is pipeline language that describes how the run worked, not the issuer. It also leaves the reader unable to tell whether FY2023 headroom was lower, the same or simply unknown, so the two years cannot be compared on total liquidity.
   - Fix: State the gap in reader terms (for example, FY2023 undrawn facilities not disclosed in the sources used) and say that total liquidity cannot be compared year on year.
3. **Medium · narrative** (Auditor)
   - Where: Line 189: "Cash at 2023-09-30; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 120"; line 190: "Revolver 843 plus securitization 163 (calculation C29)"
   - Problem: A raw internal file name ending in .jsonl and an internal calculation code (C29) appear inside a narrative 'Basis and limitation' cell. The house standard puts sources in a Source column or in Sources, and the raw file name means nothing to a portfolio manager.
   - Fix: Move the reference to a Source column that names the document as the reader would (FY2024 10-K, p.120), and keep only the plain-language limitation in this cell.
4. **Medium · visual** (New reader, Auditor)
   - Where: Liquidity chart chips: "Handoff", "? Not supplied", "1 citation without a page" under FY2023 and FY2024 (CP-1-053-a.png)
   - Problem: "Handoff" is pipeline vocabulary that shows on screen. The FY2023 chip says "1 citation without a page", but the FY2023 row cites page 120, so the chip seems to contradict the table. The empty 'n.a.' slot and the chip say the same thing in two different words.
   - Fix: Replace the chips with reader-facing source labels that match the table's citation, and use one term for the missing FY2023 value.
5. **Medium · visual** (Auditor)
   - Where: Table on CP-1_s-185.png, top of section: the 'Undrawn committed facilities' FY2023 cell
   - Problem: In a right-aligned numeric column, the long 'Not supplied...' sentence is set in bold monospace and wraps over three lines. It is the most prominent text in the table and makes the row hard to read.
   - Fix: Show a short gap marker in the numeric cell (for example 'n.a.') and move the explanation into the limitation cell, set in normal text.
6. **Low · narrative** (New reader)
   - Where: Line 185 heading "### Chart data: liquidity"; lines 189-190 "3472" / "6261" vs "USD 4,216 million"
   - Problem: "Chart data" is a build label rather than a reader heading, and the section has no one-line conclusion on liquidity. Numbers in the table have no thousands separators while the text in the same rows uses them.
   - Fix: Give the section a reader heading with a one-sentence bottom line on liquidity, and format all amounts the same way (6,261).
7. **Low · visual** (Auditor)
   - Where: Liquidity chart, right ~35% of the card empty (CP-1-053-a.png x~680-1050); stray 'Basis' tag under each Period cell in CP-1_s-185.png
   - Problem: With only two periods, the plot leaves a large empty area on the right. A loose 'Basis' label sits under each period name in the table and does not explain itself.
   - Fix: Let the two-period chart fill the card width, or centre it, and label or remove the 'Basis' tags.

### Readiness for downstream use

Kind: prose/table · handoff lines 220-228 · verdict **BLOCK**

- Narrative: The section is a pipeline routing table that tells later modules what they may use. It is not credit judgement for a portfolio manager, and its one material fact (the post-year-end special dividend) appears only as an unquantified restriction.
- Visual: There is no chart. The four-row table renders cleanly with no clipping and module codes replaced by names. However, raw .jsonl file names make the Source column wrap to three lines, and the Status column has no visual cue to separate "Restricted" from "Ready with limitations".

1. **High · narrative** (Auditor, New reader (promoted from Medium))
   - Where: L220 "### Readiness for downstream use" and L222 table header "| Use | Status | What supports it | What restricts it | Source |" with rows naming other modules (rendered as "Fundamental credit view (Fundamental credit), IC debate (Committee decision)")
   - Problem: The whole section tells the pipeline which later modules may use this data. A portfolio manager has no use for that, and "downstream use" is pipeline-to-consumer vocabulary the house standard bans. The module codes are swapped for names on screen, but the framing is still pipeline routing, not credit analysis.
   - Fix: Recast the section as reader-facing data limits (for example "What this data can and cannot support": no quarterly or LTM trend, covenant net debt not computable, credit agreement not available) without naming modules, or move it out of the reader view.
2. **Medium · narrative** (Saboteur)
   - Where: L225 "Pro forma dividend adjustment must be carried; hedge notionals not read"
   - Problem: The most material credit fact in this table is buried in a terse restriction cell with no amount or date. That fact is the USD 4,216m special dividend paid after year-end, which moves net leverage from 4.51x to 5.55x (C06 vs C11). A reader skimming this table would not know net leverage on a post-dividend basis is about 1x higher.
   - Fix: State the adjustment with its amount, date and leverage effect (for example "special dividend USD 4,216m paid Oct 2024 lifts net leverage from 4.51x to 5.55x"), or point to where the module states it.
3. **Medium · narrative** (Auditor, New reader)
   - Where: L227 Source cell "context" and restriction "No quotes or ratings in context; fair values not read here"; L226 "Credit agreement not in pack"
   - Problem: "context" is not a source reference, and "in context", "in pack" and "not read here" are pipeline language about what the model was fed. A reader cannot tell what document, if any, supports the relative-value row.
   - Fix: Name the actual source (for example the FY2024 10-K debt note) or write "No source: market quotes and ratings not provided", and replace "pack"/"context" with "not among the documents reviewed".
4. **Medium · visual** (New reader, Auditor)
   - Where: Source column, screenshot CP-1_s-220.png, crop CP-1-056-a.png (x 790-1050, rows 1-3): "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 120–123"
   - Problem: Each Source cell shows a raw internal file name with an accession number and a .jsonl extension. It wraps to three lines and makes the Source column the widest-reading column in the table. The reader cannot use the file name, and it doubles the row height.
   - Fix: Render the source as a short reader citation such as "FY2024 10-K, pp. 120–123" and keep the file identity in the Sources section or as a tooltip.
5. **Low · narrative** (New reader)
   - Where: L224 "Fundamental credit view (CP-2), IC debate (CP-6)"
   - Problem: "IC" is an undefined abbreviation. "Basis" chips sit inline after each Use label without explaining what they open.
   - Fix: Write "investment committee" in full and place the Basis link where the house layout puts it, under the row or in a consistent column.
6. **Low · visual** (Saboteur)
   - Where: Status column, crop CP-1-056-a.png (x 250-330): "Ready with limitations" x3, "Restricted" x1
   - Problem: "Restricted" for legal and covenants is styled exactly like "Ready with limitations", so the one limiting status does not stand out. Three of four rows share a hedged label that separates nothing.
   - Fix: Give the status a visual cue (a chip or weight) and make the labels specific enough to tell the rows apart.

### Reported balance sheet extract (instants)

Kind: prose/table · handoff lines 91-109 · verdict **CONCERNS**

- Narrative: This is a data section, so it has no judgement-first prose. Its only sentence (L108) contradicts itself, and the table never connects the year-end cash to the USD 4,216 million dividend owed against it, which risks overstating liquidity.
- Visual: There is no chart in this section. The table is readable and the figures are internally consistent: total liabilities plus the deficit equals total assets. It is held back by a wrapping internal file-name Source column, numeric columns aligned in different directions, unmarked subtotals, and units given only in the footnote.

1. **Medium · narrative** (Saboteur)
   - Where: L95 "Cash and cash equivalents | 6,261 | 3,472" and L102 "Dividends payable | 4,216 | — (printed dash)"
   - Problem: The cash line and the USD 4,216 million dividend payable sit seven rows apart and nothing links them, so a reader can take USD 6,261 million as available liquidity when about two-thirds of it is already owed to shareholders. The net debt in the next table (USD 18,807 million) also uses the full cash balance.
   - Fix: Put one line under the table saying cash net of the declared dividend payable (USD 2,045 million), or place the two rows next to each other.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: L108 "Goodwill and other intangibles of USD 13,865 million are not computed here as a total; equity is a deficit, so book-equity ratios are not meaningful."
   - Problem: The sentence prints a total and in the same breath says it is not computed here, which contradicts itself. It also leaves out the point a credit reader needs: intangibles are about 54% of total assets, and tangible equity is much deeper in deficit than the reported USD (6,283) million.
   - Fix: Either drop the disclaimer or state the intangible share of assets plainly. Any tangible-equity figure must come from a declared calculation, not be invented in delivery.
3. **Medium · visual** (Auditor, New reader)
   - Where: Source column, every row; screenshot CP-1_s-91.png, table region x~970-1400, y~280-1000 (crop CP-1-047-a.png)
   - Problem: Every row repeats the internal ingestion file name "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl". That is pipeline vocabulary (.jsonl, accession string), not something a reader cites. It also wraps every row onto two lines and takes about 40% of the table width.
   - Fix: Show the source as a reader label such as "10-K FY2024, p.120", with the file identity only in ## Sources.
4. **Medium · visual** (Auditor)
   - Where: FY2024 vs FY2023 columns; crop CP-1-047-a.png, x~450-600
   - Problem: FY2024 figures are right-aligned and FY2023 figures are left-aligned. Digits do not line up across years, so (6,283) vs (1,978) and 98 vs 71 are hard to compare at a glance.
   - Fix: Right-align every numeric column the same way.
5. **Low · narrative** (New reader)
   - Where: L91 "### Reported balance sheet extract (instants)"; L102 "— (printed dash)"
   - Problem: "(instants)" is data-tagging jargon, and "— (printed dash)" is extraction-provenance language. Both are opaque to a portfolio manager, and the dash note wraps awkwardly onto two lines in the cell.
   - Fix: Use a heading like "Balance sheet at 30 September 2024 and 2023", and show nil as a plain dash, with any missing-vs-zero note in the footnote.
6. **Low · narrative** (New reader)
   - Where: L103 "Accrued and other current liabilities (includes dividend equivalent payments, current, 180)"
   - Problem: An unlabelled figure of 180, with no unit or period, is embedded in the row label. It reads as an internal note, not a line as printed.
   - Fix: Move the USD 180 million dividend-equivalent component into a footnote with unit and date.
7. **Low · visual** (Auditor, New reader)
   - Where: Row labels, e.g. "Total assets Basis", "Total liabilities Basis"; crop CP-1-047-a.png, label column
   - Problem: A grey "Basis" chip follows every line label without any explanation. Subtotals (Total current assets, Total assets, Total liabilities, deficit) get the same weight as detail lines. The units are given only in a footnote below the table.
   - Fix: Visually mark subtotals (bold or a rule), put "USD m" in the column headers, and make the Basis affordance self-explanatory or less prominent.

## Fundamental credit (CP-2)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-2/b15f8ebbdefe7f4184545cfbf45afcc95dc5a380bd03e49c95c46a69e93b4ffc/1.response.md`

### Bottom line

Kind: reader passage · handoff lines 24-31 · verdict **CONCERNS**

- Narrative: The judgement comes first and is clear, but the liquidity figures do not reconcile across the page, 'fallen' gets the direction of the stated numbers wrong, and internal terms ('house-basis', 'the pack') hide the basis of the headline default-risk cushion.
- Visual: This section has no chart; the Bottom line is set as a long, heavy bold display block in a narrow column with the right third of the page empty, and its heading is not visible at the jump-to position.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Line 26: "pro forma cash liquidity falls to USD 2,919 million from the reported USD 7,267 million" vs line 42: "Cash of USD 6,261 million still included the accrued dividend. After the October payment, cash liquidity is USD 2,919 million"
   - Problem: The same page gives two different starting points for 'cash liquidity', USD 7,267 million and USD 6,261 million. 7,267 − 4,348 = 2,919, but 6,261 − 4,348 = 1,913, so a reader who checks the arithmetic from the key finding cannot reproduce the bottom-line figure. The difference is probably undrawn facilities, but the page never says so. The Bottom line also calls 7,267 'cash liquidity', which overstates cash.
   - Fix: Name the measure once (for example, cash plus undrawn revolver and securitization) and show its parts, so that 7,267, 6,261 and 2,919 reconcile wherever they appear.
2. **High · narrative** (Saboteur)
   - Where: Line 42 (read with the Bottom line's line 26): "After the October payment, cash liquidity is USD 2,919 million on a pro forma basis. By 2024-12-28 it had fallen to USD 3,308 million"
   - Problem: USD 3,308 million is higher than the USD 2,919 million pro forma figure stated in the Bottom line, so 'fallen' gets the direction wrong. A committee member would read liquidity as getting worse when the stated numbers show it rising, helped by the securitization draw.
   - Fix: State the direction the numbers actually show, and the reason, for example 'rose to USD 3,308 million after a full securitization draw, net of USD 316 million of buybacks'.
3. **High · narrative** (New reader, Auditor)
   - Where: Line 29: "Earnings would have to fall 23.47% before house-basis pro forma net leverage reached the 7.25x incurrence level ... are not documented in the pack"
   - Problem: 'House-basis' and 'the pack' are internal working terms, not reader language. A portfolio manager cannot tell which net-debt and EBITDA definitions are meant, or what 'the pack' is, without going to another page. Because this sentence carries the headline default-risk cushion, the vague basis weakens the main conclusion.
   - Fix: Say it plainly, for example 'on the company's EBITDA As Defined and our net-debt measure, not the credit agreement's definitions', and replace 'the pack' with 'the filings reviewed'.
4. **Medium · narrative** (Saboteur)
   - Where: Line 26: "Total debt is 6.01x FY2024 EBITDA As Defined. Net debt pro forma for the special dividend paid on 2024-10-18 is 5.55x"
   - Problem: The Bottom line places a reported gross multiple next to a pro forma net multiple and never gives the reported net figure (4.51x, which only appears at line 49). A reader can easily take 6.01x to 5.55x as deleveraging, when the dividend actually raised net leverage from 4.51x.
   - Fix: Give gross and net on the same basis, reported and pro forma, for example net 4.51x reported rising to 5.55x pro forma, gross 6.01x unchanged.
5. **Medium · narrative** (New reader)
   - Where: Lines 26-29: two Bottom line paragraphs of about 230 words with 13 figures, ending "so the view cannot say how large the next recapitalisation could be."
   - Problem: The Bottom line is a dense, figure-heavy summary that repeats most of the key findings (6.01x, 5.55x, 2,919, 3.60x, 23.47%, 7.25x) rather than stating the judgement in two or three sentences. It also ends on a limitation, which blurs the 'judgement first, limitations last' order.
   - Fix: Cut the Bottom line to the judgement plus the two or three figures that carry it, and leave the supporting numbers and the sizing limitation to Key findings and Limitations.
6. **Medium · visual** (New reader, Auditor)
   - Where: CP-2_bottom-line.png, Bottom line block at about y 190-800 (displayed scale), x 295-850
   - Problem: Both Bottom line paragraphs are set in large bold display type, about 22 lines of heavy bold, with dotted-underline monospace figures inside. The result is a slab that is hard to scan, and the bold loses its emphasis because everything is bold. The text column is also only about 550 px wide on a 1440 px page, leaving the right third empty.
   - Fix: Set only the first judgement sentence as the bold lead, render the rest in body weight, and widen the column or use the right-hand space.
7. **Low · visual** (Auditor)
   - Where: CP-2_bottom-line.png, top of content at about y 190: the Bottom line paragraph starts directly under the run bar
   - Problem: In this view no 'Bottom line' heading is visible above the passage, while 'Key findings' and the sections below it have headings. The reader who jumps here from 'On this page' therefore sees no label for the passage, which is probably hidden under the sticky run bar when scrolled.
   - Fix: Offset the scroll anchor so the 'Bottom line' heading stays visible below the sticky header.

### Key findings

Kind: reader passage · handoff lines 32-46 · verdict **BLOCK**

- Narrative: The section leads each bullet with a bold judgement and keeps sources out of the narrative sentences. It fails on internal consistency: FY2025 maturities leave out the securitization, the liquidity figures move the opposite way to the word 'fallen' and use undefined measures, and pipeline words like 'pack' and 'house basis' reach the reader.
- Visual: This prose section has no chart; its layout is clean, but negative amounts split the sign and currency outside the figure chip, and heavy monospace chips crowd the bullets.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 40: "Scheduled maturities are USD 93 million in FY2025 and USD 92 million in each of FY2026 and FY2027, then USD 6,637 million in FY2028. That FY2028 wall is the first real refinancing test."
   - Problem: The Bottom line (line 29) says the USD 93 million excludes the securitization, but this finding drops that qualifier. Line 42 says the USD 487 million securitization matures on 2025-07-11, which falls in FY2025. FY2025 maturities are understated about sixfold, and calling FY2028 the 'first real refinancing test' contradicts the July 2025 maturity two bullets later.
   - Fix: State the FY2025 maturities including the USD 487 million securitization due 2025-07-11, or keep the 'outside the securitization' qualifier and say how that facility will be rolled.
2. **High · narrative** (Saboteur, New reader)
   - Where: line 42: "Cash of USD 6,261 million still included the accrued dividend. After the October payment, cash liquidity is USD 2,919 million on a pro forma basis. By 2024-12-28 it had fallen to USD 3,308 million"
   - Problem: USD 3,308 million is higher than the USD 2,919 million in the sentence before it, so 'fallen' is wrong as the reader meets it. The paragraph also gives cash as USD 6,261 million while the Bottom line (line 26) gives 'reported USD 7,267 million' cash liquidity, and neither passage says what separates the two measures.
   - Fix: Name each measure and its components (cash only, or cash plus undrawn facilities), and describe the move from USD 2,919 million to USD 3,308 million in the right direction against a stated reference point.
3. **High · visual** (Saboteur, Auditor)
   - Where: Figure chips in finding 1, screenshot CP-2_key-findings.png crop (340,220)-(1020,620), saved as scratchpad/tmp/CP-2-062-a.png: "USD -158 million" and "USD -2,505 million"
   - Problem: For negative amounts, the currency and minus sign render as plain text outside the highlighted chip, so the chip itself reads '158 million' and '2,505 million'. A reader scanning the highlighted figures sees positive values where the free cash flow is negative.
   - Fix: Render a negative amount as one chip with currency and sign inside it (e.g. 'USD -158 million' or 'USD (158) million'), matching the positive-amount chips.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 44: "measured on a house basis only ... The covenant definitions of net debt and Consolidated EBITDA are not in the pack"; line 36: "about 71% of sales on the segment table"
   - Problem: 'House basis', 'the pack' and 'the segment table' are internal working vocabulary. A portfolio manager who has not seen the inputs cannot tell what 'house basis' means or which pack or table is meant, and 'pack' leaks pipeline language onto the page.
   - Fix: Say it plainly, e.g. 'measured on the company's EBITDA As Defined and reported net debt; the credit agreement definitions were not available', and 'per the company's segment disclosure'.
5. **Medium · narrative** (New reader)
   - Where: lines 40 and 44: "EBITDA As Defined covered net cash interest 3.60x"; "Pro forma net leverage of 5.55x sits 1.70x below the 7.25x incurrence level. EBITDA As Defined would have to fall 23.47%"
   - Problem: These figures repeat the Bottom line (line 29: 3.60x, 23.47%, 7.25x) almost word for word, and liquidity (2,919) is also stated twice. The key findings restate the judgement instead of adding evidence, which lengthens a section already dense with figures.
   - Fix: Keep each figure in one place: give the headline in the Bottom line and only the supporting detail or new evidence in the matching key finding.
6. **Medium · narrative** (Saboteur)
   - Where: line 36: "That mix supports debt service through an OEM downturn. Because the mix figures are largely management's estimates, this support is qualified rather than proven."
   - Problem: The finding closes by hedging its own conclusion, which leaves the committee unsure whether business quality is a credit strength to rely on. The same caveat already sits in Limitations (line 57).
   - Fix: State the judgement once and firmly, and leave the evidence-quality caveat to the Limitations section.
7. **Low · visual** (New reader, Auditor)
   - Where: Key findings block, CP-2_key-findings.png y≈230-1180 (displayed): six bullets of 4-7 lines, each carrying 4-8 underlined monospace figure chips
   - Problem: Every number is a bold monospace chip with a dotted underline, so dense bullets such as finding 2 (eight chips) and finding 6 (seven chips) read as a wall of highlights and the bold lead sentence loses prominence. The chips also clash with the proportional body font.
   - Fix: Lighten the chip styling, e.g. no monospace and a subtle underline only on hover, so the bold judgement leads and the figures support it.

### Map: credit-risk transmission

Kind: map · handoff lines 120-133 · verdict **BLOCK**

- Narrative: The nine edges (lines 122-132) read clearly one by one, but the section has no opening judgement, does not mark which edges are risks and which are supports, and lets pipeline words ('handoff', 'fact pack') into the Evidence column.
- Visual: The drawing has all nine edges and stays visible on the page, but node text breaks mid-word and is truncated, edge labels overlap into garbage ('AnaDocumentaryrFaction'), there is no legend, and the edge table appears twice, the second time in monospace.

1. **High · narrative** (Saboteur)
   - Where: line 131: '| Defense and commercial OEM exposure | Government audits or build-rate cuts would compress sales and margin | Analyst Interpretation | High EBITDA As Defined margin |'
   - Problem: This edge is a threat to the margin, but the map draws it as the same plain arrow into 'High EBITDA As Defined margin' as the supporting edge from the proprietary product base. Positive and negative effects look identical, so a reader can take defense exposure as a support for margin. The same applies to the gap edge at line 132, where 'Missing executed credit documents' is drawn as a cause of 'Debt-funded shareholder distributions'.
   - Fix: Show the direction of effect (supports or erodes) on each edge, or point the risk edge at a risk node such as 'margin compression', and show information gaps as an annotation rather than a causal arrow.
2. **High · visual** (Auditor, New reader)
   - Where: Maps panel, 'Credit-risk transmission' drawing; CP-2_maps.png crop x340-1400, y250-590 (saved as scratchpad/tmp/CP-2-067-a.png)
   - Problem: The edge labels collide and get clipped. Labels read 'AnaDocumentaryrFaction' (two labels drawn on top of each other), 'alyst=Interpretati' and 'ufficient Information', and the 'Management Language' label runs into the node next to it. The reader cannot tell which evidence type belongs to which arrow.
   - Fix: Lay out the edge labels so none overlap or get clipped (or show the evidence type through line style plus a legend), and keep every label fully readable inside the map frame.
3. **High · visual** (New reader, Auditor)
   - Where: Same drawing, node boxes: 'Proprietary aftermarke t-heavy product base', 'Capital allocation hie rarchy ranking prepaym...', 'Higher loss given defa ult for subordinated c...', 'Debt-funded shareholde r distributions', 'Reduced liquidity buff er'
   - Problem: Node text breaks in the middle of words and is cut off with an ellipsis. The most important end point, loss given default for subordinated creditors, cannot be read in full on the map.
   - Fix: Wrap node text only at word boundaries and size the boxes (or shorten the labels) so every node title shows in full without truncation.
4. **Medium · narrative** (Auditor, Saboteur)
   - Where: line 120-122: '### Map: credit-risk transmission' followed directly by '| From | Relationship | Edge type | To | Evidence |'
   - Problem: The section opens straight into a nine-row table with no judgement sentence, so the reader has to work out the conclusion alone. That conclusion is that financial policy outweighs business strength and the result is a higher loss given default for subordinated creditors. This breaks the judgement-first standard.
   - Fix: Open with one bottom-line sentence that says what the transmission chain means for the subordinated creditor before the table.
5. **Medium · narrative** (Auditor, New reader)
   - Where: line 128: 'Secured share of funded notes and term loans computed in this handoff'; line 124: 'as carried by the fact pack'; line 132: 'Source readiness gap on credit agreement and indentures'
   - Problem: Pipeline vocabulary ('handoff', 'fact pack', 'financial data foundation', 'Source readiness gap') reaches the reader in the Evidence column. The Evidence cells also name internal stages rather than the underlying filing or calculation.
   - Fix: Replace these with reader terms that name the actual source, such as 'calculated from the FY2024 annual filing' or 'credit agreement and indentures not available'.
6. **Medium · visual** (New reader)
   - Where: Maps panel, 'Edges of the map, as stated' table; CP-2_maps.png y≈610-1410 (full-res), and the in-section table in CP-2_s-120.png y≈260-890
   - Problem: The same nine-edge table is printed twice on the page: once in this section and again under the map. The Maps panel copy uses monospace type, with blue underlined link-styled Relationship text that is not a link, which is hard to scan and looks like code.
   - Fix: Show the edge table once, in the page's normal proportional body type, and use link styling only for real links.
7. **Low · visual** (Auditor)
   - Where: Credit-risk transmission drawing, line styles (solid, dashed, dotted, dash-dot); scratchpad/tmp/CP-2-067-a.png
   - Problem: Four line styles stand for the evidence categories, but the map has no legend, so the reader cannot decode them once the overlapping labels become unreadable.
   - Fix: Add a small legend that maps each line style to its evidence type.
8. **Low · visual** (New reader)
   - Where: CP-2_s-120.png in-section table, From column: 'Proprietary aftermarket-heavy product base Basis' (every row)
   - Problem: Every From cell ends with a bare 'Basis' chip, but the table already has an Evidence column. The chip adds clutter and its meaning is unclear for a map edge.
   - Fix: Drop the per-row Basis chip in map edge tables or merge it into the Evidence column.

### Credit view

Kind: prose/table · handoff lines 60-111 · verdict **BLOCK**

- Narrative: The lede gives the judgement first, and the tables' Creditor consequence column is useful. But one liquidity row is internally inconsistent: the note's arithmetic gives 1,913, the value shows 2,919, and \"cash liquidity\" is never defined as including committed lines. Pipeline wording (\"upstream\") also explains missing values, and several Source cells give only calculation IDs.
- Visual: The three visible tables are legible and the column order holds, but self-repeating Source names, a Basis link on every row and inconsistent bold-monospace emphasis make rows tall and push the eye to the reported leverage (4.51x) rather than the pro forma figure (5.55x). The fourth table falls below the screenshot and was judged from the handoff only.

1. **High · narrative** (Saboteur, New reader)
   - Where: Line 94: "Cash liquidity, pro forma October dividend | USD 2,919 million | 2024-10-18 pro forma | Cash USD 6,261 million less USD 4,348 million paid" (with line 93 "Cash liquidity, reported | USD 7,267 million")
   - Problem: The note's arithmetic gives USD 1,913 million, not the USD 2,919 million shown. 2,919 is 7,267 less 4,348, and 7,267 includes USD 843 million of undrawn revolver and USD 163 million of securitization availability (CP-1 line 143). The table calls both figures "cash liquidity" without saying they include committed lines, so a reader can take the post-dividend cash buffer to be about USD 1 billion larger than it is.
   - Fix: Label 7,267 and 2,919 as cash plus undrawn revolver and securitization availability, and correct the note to 7,267 less 4,348 (or show pro forma cash of USD 1,913 million as its own row).
2. **High · narrative** (Auditor, New reader)
   - Where: Lines 70, 71, 84, 85: "Not calculated upstream"; line 99: "Hedge detail not read upstream"; line 67: "Not calculable: FY2022 not used"
   - Problem: Six table cells give pipeline wording ("upstream", "not read", "not used") as the reason a value is missing, where the reader needs a fact about the issuer or the evidence. This breaks the house rule against pipeline vocabulary on screen, and it does not tell a portfolio manager whether the number exists in the filings.
   - Fix: Say in reader terms why each value is missing, e.g. "Not disclosed" or "Not computed for this review; prior-year balance needed", and keep missing distinct from zero.
3. **Medium · narrative** (New reader, Auditor)
   - Where: Lines 72, 83–87 Source cells: "calculation S01", "calculation S12", "calculation S02", "calculation S06", "calculation S09"
   - Problem: Calculation register IDs are the whole Source entry for six of the most decision-relevant rows: payout coverage, secured share and covenant headroom. The ruling asks for table Source columns "in plain words", and a reader cannot tell what S06 rests on without opening another page.
   - Fix: Name the source in words (e.g. "House calculation from the annual filing") and keep the calculation ID only as the link target.
4. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-2_s-60.png, Source column of all three visible tables (x≈1025–1150): "Financial data foundation (Financial foundation)"; "Business and transaction fact pack (Business & governance)"
   - Problem: The renderer replaces the module code with a second module name, so every Source cell repeats itself and wraps to three or four lines. Most rows end up twice the height they need, and the reader gets two names for one source.
   - Fix: Show one plain-words source name per cell, e.g. "Financial foundation", so each row fits on one or two lines.
5. **Medium · visual** (Saboteur)
   - Where: Screenshot CP-2_s-60.png, leverage table (y≈880–1420 display): "6.01x", "4.51x", "26.02%" in bold monospace versus "5.55x; USD 23,155 million" and "1.70x; 23.47% EBITDA cushion" in plain text
   - Problem: Figure emphasis is inconsistent. The reported 4.51x, which the table itself says "Overstates deleveraging", is bold and highlighted, while the 5.55x pro forma figure the lede calls the creditor-relevant position is plain. The eye goes to the wrong leverage number.
   - Fix: Style figures the same way in every cell, including cells that combine values, or give the pro forma 5.55x at least the same weight as the reported multiple.
6. **Medium · visual** (New reader)
   - Where: Screenshot CP-2_s-60.png, first column of every row: a grey "Basis" link after each measure label (e.g. "Net sales growth Basis", "Free cash flow (CFO less capex) Basis")
   - Problem: A Basis link on every one of the 23 visible rows clutters the measure column, pushes labels onto a second line, and repeats what the Source column already says. The ruling reserves the quiet "Basis" link for paragraphs with no figure.
   - Fix: Drop the per-row Basis link in tables where a Source column exists, or make the figure itself the inspector link.
7. **Low · narrative** (New reader)
   - Where: Lines 105–110 Category column: "Management Language" / "Documentary Fact"
   - Problem: These title-case evidence-class labels read as internal taxonomy. A committee reader has to work out that "Management Language" means an unverified company estimate.
   - Fix: Use plain words such as "Company estimate" and "Reported in filings".
8. **Low · narrative** (Saboteur)
   - Where: Line 83: "Total debt incl. October securitization draw / EBITDA As Defined | 6.05x; USD 25,230.5 million"
   - Problem: This one debt figure carries half-million precision while every other amount on the page is rounded to whole millions. That suggests a precision the table does not otherwise claim, and it breaks the page's unit convention.
   - Fix: Show the amount in the same whole-million convention as the other rows, or say why the half million matters.

### Analytical appendix — complete canonical registers

Kind: register appendix · handoff lines 134-187 · verdict **BLOCK**

- Narrative: The registers are compact and mostly consistent with the reader passages (5.55x, 3.60x, USD 4,348 million, 81.07%, 23.47% all agree). However, module readiness talk leaks onto the page, judgements are labelled Documentary Fact, and the appendix duplicates the key findings and the gaps without adding a reader-facing purpose.
- Visual: The supplied screenshot never reached the section because the appendix heading has no anchor (no s-134 in the DOM), so I judged a fresh full-height render (tmp/CP-2-068-full.png, cropped to tmp/CP-2-068-a.png and -b.png). There the tables are legible and well spaced, but the headings read 'a method step …', the appendix title is missing, and every row carries a redundant 'Basis' chip.

1. **High · narrative** (Auditor, New reader)
   - Where: line 184: 'CP-1A readiness judgment of CP-2 is Ready with limitations (signal), citing payment capacity'; line 140: 'CP-1A readiness for CP-2 is Ready with limitations, so confidence is capped below High'; line 182: 'CP-4 bounds conclusions to filing summaries'
   - Problem: On screen these become 'Business & governance readiness judgment of Fundamental credit is Ready with limitations (signal)' and 'Legal & covenants bounds conclusions…'. That is still pipeline status talk about modules gating each other ('readiness', 'Ready with limitations', '(signal)'), not a credit limitation a committee member can act on, and the house rule bars it.
   - Fix: State the underlying evidence gap in reader terms, e.g. 'payment-capacity terms are summarised in the filing only, so confidence stays Medium', with no module names or readiness states.
2. **High · visual** (Auditor, New reader, Saboteur)
   - Where: Sub-headings rendered as 'a method step Credit assessment', 'a method step Thesis, strengths and weaknesses', 'a method step Key findings', 'a method step Key credit risks', 'a method step Gaps ledger' (handoff lines 136-178 '#### T2.1 Credit assessment' etc.); tmp/CP-2-068-a.png y~965-1905 and tmp/CP-2-068-b.png y~268-586; also in the On-this-page list in shots2/CP-2_s-134.png x~95-260 y~780-880
   - Problem: The register codes T2.x are swapped for the garbled internal phrase 'a method step', which is pipeline language and reads as a rendering bug. The section's own heading 'Analytical appendix — complete canonical registers' (line 134) is missing from the page entirely: the DOM has no s-134 anchor, so the five registers look like loose continuations of 'Map: credit-risk transmission', and the route #CP-2/s-134 lands on the top of the module (the supplied screenshot shows the page head, not this section).
   - Fix: Render a reader heading for the appendix (e.g. 'Supporting tables') with its own anchor, and give each register plain titles ('Credit assessment', 'Key credit risks') without 'a method step' or T-codes.
3. **Medium · narrative** (Saboteur)
   - Where: line 161: '| 1 | Financial policy is the main credit driver and points to recurring debt-funded extraction | Documentary Fact |'; line 163: 'Secured debt dominates and grows with each recapitalisation | Documentary Fact'; line 151: 'W1 | Weakness | Extraction-oriented financial policy | … | Documentary Fact'
   - Problem: Forward-looking judgements ('main credit driver', 'points to recurring', 'grows with each recapitalisation') are labelled Documentary Fact. A reader will give a projection the weight of a filed fact, and the label contradicts the Analyst Interpretation tag that the same thesis carries in TH1 (line 146).
   - Fix: Tag forward-looking or evaluative rows as Analyst Interpretation and keep Documentary Fact for the figures themselves.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: lines 157-187 (Key findings, Thesis/strengths/weaknesses, Gaps ledger) against the reader passages above and the separate 'Gaps' table that follows (tmp/CP-2-068-b.png y~1665-2000)
   - Problem: The appendix repeats the Key findings, the strengths and weaknesses, and the gaps that already appear on the page, and the Gaps ledger GP1-GP5 is then re-stated almost row for row in the later 'Gaps' table with different wording ('Confidence capped below High' vs 'Confidence capped at Medium'). The reader has to reconcile two versions of the same list.
   - Fix: Show each register once: either drop the appendix rows that duplicate the reader passages and the Gaps table, or fold them into a single list.
5. **Medium · narrative** (New reader)
   - Where: line 154: 'Only a springing revolver test at 7.50x; house pro forma net leverage 1.70x below the 7.25x incurrence level'; line 175: 'house headroom of 23.47% EBITDA cushion consumed'; line 186: 'No quarterly or LTM figures'
   - Problem: 'Springing', 'incurrence level', 'house' basis, 'EBITDA As Defined', 'LTM' and 'extraction' are left undefined. The severity scale Critical/Material/Minor (lines 172-186) and the inline '[Insufficient Information]' tags are also unexplained. A committee reader cannot tell what 'house' measures against.
   - Fix: Define 'house basis' and the covenant terms once in plain words where they first appear, and give the severity scale a one-line key.
6. **Medium · visual** (New reader, Auditor)
   - Where: Every table row's ID/first cell carries a grey 'Basis' chip (e.g. 'TH1 Basis', 'RK1 Basis', 'GP1 Basis'), tmp/CP-2-068-a.png y~1030-1880 and tmp/CP-2-068-b.png y~0-900
   - Problem: The chip repeats beside a table that already has its own Basis column, or (in Key credit risks and Gaps ledger) has no Basis column at all. It adds clutter to every row and gives no clue what it opens.
   - Fix: Drop the per-row chip where the table has a Basis or Source column; otherwise label it clearly (e.g. 'Sources') and place it consistently.
7. **Low · narrative** (Saboteur)
   - Where: line 149: 'Cash interest cover 3.60x; about 77% fixed rate'; line 152: 'Secured debt USD 19,702 million, 81.07% of notes and term loans'; line 140: 'near-term default risk is low on 3.60x cash interest cover'
   - Problem: The register cells drop the period or date (FY2024, 2024-09-30) that the reader passages carry, so a reader landing on the table cannot tell which period or balance-sheet date the figures belong to.
   - Fix: Add the period or as-of date to each figure in the register cells.
8. **Low · visual** (Auditor)
   - Where: Basis cells such as 'Financial data foundation (Financial foundation); Business and transaction fact pack (Business & governance)', tmp/CP-2-068-a.png y~1030-1880
   - Problem: Every source is printed twice (document name plus module name in brackets), which doubles the width of the Basis column and pushes the wide six-column tables into four- and five-line rows.
   - Fix: Print one reader-facing source name per reference.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 219-222 · verdict **BLOCK**

- Narrative: Both passages are run plumbing that reaches the reader: pipeline words (\"handoffs\", \"credit_snapshot pathway\"), an instruction from one module to another, and a stuttering label substitution. Neither passage carries credit judgement, so the ordering rule does not apply to them.
- Visual: The section has no chart, map or timeline. Both passages render as plain, readable paragraphs with no clipping or overlap, but their headings look the same as the analytical headings and are listed in the reader TOC.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: Line 3: "built from the supplied CP-0, CP-1, CP-1A and CP-DR handoffs"; rendered in CP-2_s-1.png, Request paragraph (y~225-260) as "...Business & governance and Research questions handoffs"
   - Problem: "handoffs" is pipeline vocabulary that the house standard bans from reader text, and it is printed on screen. A committee reader has no idea what a handoff is, or that these are other sections of the same report.
   - Fix: Render this as reader language, e.g. "built from the Source readiness, Financial foundation, Business & governance and Research questions sections of this report".
2. **High · narrative** (Auditor, New reader (promoted))
   - Where: Line 221: "CP-2A should build the downside pathway starting from pro forma net leverage of 5.55x ... CP-4 should bound the payment and incurrence capacity left open here."; rendered at the bottom of CP-2_s-219.png under "Next module"
   - Problem: The section is an instruction from one module to another ("Downside should build...", "Legal & covenants should bound..."), shown to the reader under the pipeline heading "Next module". It is run plumbing, not credit analysis. The reader is also told that payment capacity will be bounded, while the nav marks Legal & covenants "Not assessable".
   - Fix: Leave the inter-module instruction out of the reader page, or recast it as a reader-facing "Open questions" line that points to where (or whether) those questions are answered.
3. **Medium · narrative** (New reader, Saboteur (promoted from Low))
   - Where: CP-2_s-1.png Request paragraph (y~225): "Fundamental credit fundamental credit synthesis for TransDigm Group Incorporated (TDG)"; source line 3: "CP-2 fundamental credit synthesis"
   - Problem: Replacing the code CP-2 with its display label makes the opening words stutter ("Fundamental credit fundamental credit"). That reads as a defect in the first sentence the reader meets in this section.
   - Fix: Make the code-to-label substitution context-aware so that it renders "Fundamental credit synthesis for TransDigm...".
4. **Medium · narrative** (Auditor)
   - Where: Line 3: "as of 2024-09-30, on the credit_snapshot pathway"
   - Problem: "credit_snapshot pathway" is an internal identifier, underscore included, and "pathway" is pipeline vocabulary. The ISO date also clashes with the page header's "30 September 2024".
   - Fix: Write "credit snapshot review as of 30 September 2024", or drop the scope line now that the run bar already states it.
5. **Medium · visual** (Auditor, New reader)
   - Where: CP-2_s-1.png, On this page TOC (x~95-260, y~515-950) and the Request heading at y~198; CP-2_s-219.png, Next module heading at y~1880
   - Problem: "Request" and "Next module" are styled exactly like the analytical headings ("Credit view", "Gaps") and appear in the reader's page TOC. Plumbing therefore carries the same visual weight as the analysis, and the Request block wedges between Maps and Credit view.
   - Fix: Move run-scope and next-step plumbing into a collapsed or muted run-details strip, or drop it from the TOC, so that the analytical headings stand alone.
6. **Low · narrative** (Saboteur)
   - Where: Line 221: "pro forma liquidity of USD 2,919 million"
   - Problem: Elsewhere (lines 42, 94, 153) USD 2,919 million is "cash liquidity", set against USD 7,267 million of reported liquidity. Dropping "cash" here invites a reader to take it as total liquidity, revolver included.
   - Fix: Use the same label as the body: "pro forma cash liquidity of USD 2,919 million (after the October dividend)".

### Sources

Kind: prose/table · handoff lines 5-21 · verdict **CONCERNS**

- Narrative: The Sources section uses pipeline vocabulary (handoff, upstream), raw storage filenames, an internal settings row and two names for each earlier analysis, and its closing note names filings that the table does not list.
- Visual: The section is two bordered tables plus a note, with no chart. Wide sha256 columns squeeze the Source column, so filenames wrap over four lines, and the block sits mid-page rather than at the end.

1. **High · narrative** (Auditor, New reader (promoted from Medium))
   - Where: line 9 "relied on through the CP-1, CP-1A and CP-DR handoffs' page-cited figures, not read directly"; line 13 header "Supplied handoff"; line 20 "evidence is upstream only ... reach this synthesis only through the supplied handoffs"
   - Problem: Pipeline words the house standard bans ("handoff", "upstream", "Supplied handoff") appear in the reader-facing Sources table and its note, and the on-screen table header (CP-2_s-5.png, y~385 in crop) shows them. The module codes are swapped for labels on screen, but the vocabulary is not.
   - Fix: Describe these inputs as the earlier analyses in this report (for example "Earlier analysis used" and "figures taken from the Financial foundation analysis, which cites the filing by page"), with no pipeline vocabulary.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 20 "The pinned issuer filings (FY2024 annual filing, Q2, Q3 FY2024 and Q1 FY2025 quarterly filings, PDF annual report) reach this synthesis"
   - Problem: The note names five filings, but the Sources table above lists only two (the FY2024 10-K and the Q1 FY2025 10-Q). The reader cannot tell which filings back the numbers below, so the provenance on one page contradicts itself.
   - Fix: Either list every filing the module relies on in the Sources table or make the note name only the filings in the table.
3. **Medium · narrative** (New reader)
   - Where: line 9 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"; line 11 "context | ... | Run settings only (as-of 2024-09-30, FY2024 current, FY2023 prior, USD); not issuer evidence; blanks not treated as zero"
   - Problem: Sources are named by internal storage filenames (accession numbers, .htm.jsonl), and one row is an internal "context" settings file that is not a source. A reader cannot tell what the document is or why a settings file sits among the evidence.
   - Fix: Name each source as a document a reader recognises (form, period, filing date) and drop the run-settings row, or state the as-of date and currency once in prose.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: Supplied handoff table lines 15-18, e.g. "Business and transaction fact pack | CP-1A" rendered as "Business and transaction fact pack | Business & governance"; "Deep research" vs "Research questions"
   - Problem: Each earlier analysis is shown under two different names in adjacent columns, and the left-nav uses the second name. The reader has to work out that "Deep research" and "Research questions" are the same page.
   - Fix: Use one name per analysis, matching the navigation, and drop the redundant column.
5. **Medium · visual** (New reader, Auditor (promoted from Low))
   - Where: Sources and Supplied handoff tables, sha256 columns, CP-2_s-5.png x~480-890, y~255-640 (crop CP-2-060-a.png)
   - Problem: Two 64-character sha256 columns take about 40% of the table width but mean nothing to a portfolio manager. Because of them the Source column is so narrow that the raw filenames wrap over four lines each.
   - Fix: Show the reader a plain filing label (for example "Form 10-K, FY2024, filed 2024-11") and move hashes into a fold or a tooltip, so the use column has room.
6. **Low · visual** (Auditor)
   - Where: Page order, On this page nav in CP-2_s-5.png (left rail): "Limitations, Maps, Request, Sources, Credit view, Strengths and weaknesses..."
   - Problem: The Sources block sits mid-page, between the judgement sections and the supporting Credit view tables, so the reader runs into a hash table before the analysis that backs the bottom line.
   - Fix: Put Sources at the end of the module page, after the analysis and gaps, as in the VMO2 reading order.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 47-51 · verdict **CONCERNS**

- Narrative: The section is in its correct place in the order (after Key findings, before Limitations) and sets out both contrary readings. However, its key contrary figure (4.51x) is the pre-dividend number with no basis, the four jobs are merged into one 200-word paragraph, and the change-the-view triggers have no thresholds.
- Visual: The section has no chart, map or timeline, only one prose block. Its layout and line length are readable, but the monospace figure chips break the reading rhythm and no paragraph-level Basis control is visible.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 49: "net leverage on the reported balance sheet fell to 4.51x from 4.84x because EBITDA grew faster than debt"
   - Problem: The headline contrary figure is pre-dividend: the reported 2024-09-30 cash still held the accrued USD 4,348 million October payout (line 42), and the Bottom line puts pro forma net leverage at 5.55x. The passage gives no basis (EBITDA As Defined, house net debt) and no pro forma caveat, so a committee reading only this paragraph sees deleveraging where the module's own view is releveraging. Because the same 'leverage' word appears with 4.51x here and 5.55x and 6.01x above, the figures also look inconsistent on one page.
   - Fix: State that 4.51x is the reported, pre-payout figure on the EBITDA As Defined / house net-debt basis, and give the 5.55x pro forma comparison in the same sentence.
2. **Medium · narrative** (New reader, Auditor)
   - Where: lines 49: "The strongest evidence against a high financial-risk reading ... Against the business-quality reading, the filing concedes ... Several things would soften the view ... The view would harden if ..."
   - Problem: One paragraph of about 200 words does four jobs: contrary evidence on financial risk, contrary evidence on business quality, softening triggers and hardening triggers. On screen it reads as a 14-line wall of text in which the 'what would change the view' half, the part a committee acts on, is buried in the last five lines.
   - Fix: Split it into a contrary-evidence paragraph (one for each reading) and a separate short list of soften and harden triggers.
3. **Medium · narrative** (Saboteur)
   - Where: line 49: "a sustained period in which payouts were funded only from free cash flow ... if another distribution were funded with secured debt while EBITDA growth slowed"
   - Problem: None of the triggers is measurable. There is no length for 'sustained', no level of EBITDA growth or margin, and no leverage or secured-debt multiple (for example against the 5.55x pro forma or the 4.72x secured figure). A committee cannot tell when the view has changed.
   - Fix: Tie each trigger to a measurable threshold the module already holds, such as a pro forma net leverage level, a secured-debt multiple or the payout-to-free-cash-flow ratio.
4. **Medium · narrative** (Saboteur)
   - Where: line 49: "Operating cash flow rose from USD 1,375 million to USD 2,045 million. Interest cover improved even as debt rose"
   - Problem: The operating cash flow figures have no period (FY2023 to FY2024). The interest-cover claim has no figure or basis, although the module holds 3.60x from 2.93x on a net cash basis (line 40). A figure without its period or basis breaks the house rule that values and periods are exact.
   - Fix: Add 'FY2023 to FY2024' to the cash flow figures and state the cover as 'EBITDA As Defined / net cash interest 3.60x from 2.93x'.
5. **Low · narrative** (Auditor)
   - Where: line 49: "Against the business-quality reading, the filing concedes that competition is significant and that prices may have to adjust."
   - Problem: Naming 'the filing' as the speaker puts a source reference into a narrative sentence, which the house standard keeps for the Basis line. The Basis lists only module handoffs, so the reader cannot tell which filing is meant.
   - Fix: State the risk as a judgement ('competition is significant and pricing may have to adjust') and leave the source to the Basis line.
6. **Low · visual** (New reader, Auditor)
   - Where: CP-2_contrary-evidence.png, crop of the section at 330-1100 x 210-640 (saved as /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2-063-a.png): figure chips "USD 1,375 million", "4.51x", "40%"
   - Problem: Figures are set in a bold monospace face with a dotted underline inside proportional body text. This breaks the reading rhythm and makes the chips look like code or links. Only some numbers get the treatment: 'FY2024' and 'FY2028' do not, so the reader cannot tell which numbers are traceable.
   - Fix: Keep figure chips in the body typeface with a subtle underline or tint, so traceable numbers stand out without looking like code.
7. **Low · visual** (Auditor)
   - Where: CP-2_contrary-evidence.png, section block y≈230-600: no visible Basis control under the paragraph
   - Problem: Line 50 carries a Basis line, but the page shows no Basis marker for the paragraph; the source is reachable only through the figure chips (reader.js:324 drops the paragraph button whenever figures exist). A reader looking for this paragraph's sources finds nothing in view.
   - Fix: Show a paragraph-level Basis control even when the paragraph has figure chips.

### Strengths and weaknesses

Kind: prose/table · handoff lines 112-119 · verdict **BLOCK**

- Narrative: The judgement is clear (strong business, aggressive policy), but the section has three problems. The 81.07% secured share is dated 30 September 2024, yet the wording places it after the October recapitalisation. Leverage and cover figures appear without their period or basis. Both paragraphs are dense blocks of several points each, with internal shorthand such as "house basis".
- Visual: The section contains no chart, map or timeline; it renders as two long prose paragraphs. Neither paragraph shows the Basis line that the source carries, although the map table directly below shows a Basis chip on every row. Inline monospaced figure chips break up the body text.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 117: "paid USD 4,348 million to equity in October 2024 with USD 3,000 million of same-day secured debt ... secured debt is now 81.07% of funded notes and term loans"
   - Problem: Calculation S02 (line 195) is 19,702 / 24,302 at 2024-09-30, which is before the October USD 3,000 million secured issue. The word "now", placed straight after the October recapitalisation, makes a reader take 81.07% as the post-dividend position. That understates the secured share the committee is actually judging.
   - Fix: Date the figure ("81.07% at 30 September 2024, before the October secured issue") or give the pro forma share if one has been computed.
2. **Medium · narrative** (Saboteur)
   - Where: line 114: "keeps interest cover at 3.60x even at 6.01x gross leverage"
   - Problem: The sentence pairs a FY2024 gross multiple (6.01x) with an unnamed cover ratio, while the weaknesses paragraph and the rest of the module anchor on 5.55x pro forma net. The same section therefore gives two leverage bases with no period or definition, and the ratio behind 3.60x (EBITDA As Defined to cash interest?) is never named.
   - Fix: Name the ratio and the period for each figure, e.g. "FY2024 EBITDA As Defined / cash interest 3.60x; FY2024 total debt / EBITDA As Defined 6.01x".
3. **Medium · narrative** (New reader)
   - Where: line 117: "the incurrence levels sit 1.70x above pro forma net leverage on a house basis"
   - Problem: The passage never says which instrument's incurrence test is meant, and "house basis" is internal shorthand. A reader who has not seen the filings cannot tell that 7.25x is the level, or that the covenant definitions are missing. Line 44 explains this; this sentence does not.
   - Fix: State the level and the caveat in plain words: "pro forma net leverage of 5.55x is 1.70x below the 7.25x debt-incurrence level, measured on our own definitions because the covenant definitions are not available".
4. **Medium · narrative** (New reader)
   - Where: line 117: "The weaknesses are financial-policy side. The company ranks prepayment last, paid USD 4,348 million ... Defense exposure brings government pricing and audit risk ..."
   - Problem: One paragraph of about 120 words carries five separate weaknesses: payout policy, secured layering, weak maintenance protection, defense audit exposure and the equity deficit. Line 114 does the same for the strengths. The reader cannot scan them or weigh one against another, and the defense point is not a financial-policy item at all, despite the opening sentence.
   - Fix: Split each paragraph into short, one-point sentences or a list ordered by credit weight, and move the defense item out from under the "financial-policy" heading claim.
5. **Medium · visual** (Auditor, New reader)
   - Where: shots2/CP-2_s-112.png, region x 330-1440, y 210-500 (crop tmp/CP-2-066-a.png): both paragraphs
   - Problem: Lines 115 and 118 each carry a Basis line, but the rendered section shows no Basis chip or line under either paragraph. The map rows directly below each show a "Basis" chip. The reader cannot see where these paragraphs come from, which breaks the rule that source references sit in each paragraph's Basis line.
   - Fix: Show the Basis line or chip under each prose paragraph in the same way the table rows below show theirs.
6. **Low · narrative** (New reader)
   - Where: line 114: "produces an EBITDA As Defined margin of 52.56%"
   - Problem: "EBITDA As Defined" is the company's adjusted measure, but this section neither defines it nor flags it as company-adjusted. A reader may compare it with a reported EBITDA margin.
   - Fix: Mark it once as the company's adjusted EBITDA measure, with a pointer to where it is defined.
7. **Low · visual** (Auditor)
   - Where: shots2/CP-2_s-112.png, crop tmp/CP-2-066-a.png: inline figures such as "USD 4,348 million", "81.07%", "1.70x"
   - Problem: Every figure is set in a monospaced, dotted-underline chip in the middle of proportional body text. This breaks the reading rhythm of dense paragraphs, and "USD 3,000 million" is wide enough to force awkward line breaks.
   - Fix: Keep the figure in the body font and mark it with a lighter cue, such as a subtle underline only, so the prose reads as prose.

### Calculations

Kind: prose/table · handoff lines 188-206 · verdict **CONCERNS**

- Narrative: This is a data section, so it owes only a bottom line. It has none: it opens with pipeline and script language and leaves the 7.25x/7.50x thresholds and the net versus gross leverage choice unexplained, although the arithmetic checks out (4,216+132=4,348; 19,702+4,600=24,302).
- Visual: There is no chart; the table is clean and readable at 1440 px, but results mix bold-monospace unrounded figures with regular rounded ones, and stray \"Basis\" labels appear under S05 and S08.

1. **High · narrative** (Auditor, New reader)
   - Where: L190: "Helper scripts named by the method (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py and other scripts) were not run in this transport; their checks were done by hand and all new arithmetic used the calculate tool."
   - Problem: The section opens with pipeline internals (script filenames, "transport", "calculate tool", and "handoffs" as rendered on screen) instead of anything about the credit. This breaks the house rule against pipeline vocabulary and is meaningless to a committee reader. Two personas caught it, so it is promoted to High.
   - Fix: Drop the script and transport sentence, or move it to an internal log, and open with one reader sentence on what these figures establish.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: L197-205: "S04 | EBITDA level at which pro forma net debt equals 7.25x ... S10 | 7.25x less pro forma net leverage"
   - Problem: The 7.25x and 7.50x thresholds that drive the 23.47%/26.02% EBITDA cushions and 1.70x headroom are never explained (house limit? rating trigger?). The intro only says "House ratios are not covenant ratios", so a reader cannot tell what breaking the threshold would mean.
   - Fix: Name what each threshold represents in one clause, for example in the Formula column or a single lead sentence.
3. **Medium · narrative** (Saboteur)
   - Where: L203-205: "7.25 − 5.5487658759 (CP-1 C11)" vs "S12 | S11 / EBITDA As Defined | 25,230.5 / 4,173 | 6.0461298826 (6.05x)"
   - Problem: Two leverage figures sit side by side: 5.55x pro forma net and 6.05x gross plus the October draw. Nothing says which one the view and the headroom rest on, or how the 5.55x is derived (its inputs are not shown). A reader could compare the 6.05x against the 7.25x headroom by mistake.
   - Fix: Label S10 and S12 explicitly as net versus gross, and add one sentence saying which multiple anchors the view.
4. **Medium · narrative** (New reader, Auditor)
   - Where: L194: "4,348 (paid 2024-10-18, CP-1A K12 inputs; 4,216 + 132 per CP-1) / 1,880 (FY2024, CP-1 C15)"
   - Problem: Internal register codes (K12, C15, C23, C24, C10, C11, C01) and module names stand in for sources in the Inputs column. As rendered ("Financial foundation C15"), the reader cannot trace them to a document without another page.
   - Fix: Cite the filing and statement/note (for example, FY2024 10-K cash flow statement) in a Source column and drop the register codes.
5. **Medium · visual** (Auditor, New reader)
   - Where: Calculations table, shots2/CP-2_s-188.png crop (340,840)-(1400,1700), rows S04, S05, S07, S08, S11 Result cells
   - Problem: Result typography is inconsistent. USD m results render in bold monospace with 10 decimals and no rounded value ("3193.7931034483", "25230.5" with no thousands separator), while ratio results use a regular font with a rounded figure in parentheses. Precision to 1e-10 USD m is false precision for a reader.
   - Fix: Render every result in one style, rounded to reader precision (for example, USD 3,194 million), with thousands separators.
6. **Medium · visual** (Auditor, Saboteur)
   - Where: Calculations table rows S05 and S08, ID column, shots2/CP-2_s-188.png crop: "S05 Basis", "S08 Basis"
   - Problem: A stray "Basis" label appears under the IDs of S05 and S08 only. It is not in the handoff lines 198/201, has no content and looks like a rendering artefact, possibly matching the word in "EBITDA As Defined less S04". It suggests a basis that is not there.
   - Fix: Show Basis labels only where a Basis line exists, and fix the renderer's match on these rows.
7. **Low · narrative** (Saboteur)
   - Where: L199: "S06 | S05 / EBITDA As Defined | 979.2068965517 / 4,173 | 0.2346529826 (23.47%) | fraction"
   - Problem: The Unit column says "fraction" while the reader-facing figure is a percentage, and "x" is used for both a payout multiple (S01) and leverage (S12). These small unit mismatches slow cross-checking.
   - Fix: Set the unit to % for S02, S03, S06 and S09, and keep x for multiples.
8. **Low · narrative** (Auditor)
   - Where: L190: "Inputs are USD millions from the CP-1 and CP-1A handoffs, which cite the FY2024 annual filing."
   - Problem: A source reference sits in a narrative sentence, which the house standard reserves for Basis lines, Source columns and ## Sources.
   - Fix: Move the filing citation to a Source column or the module's Sources list, and keep the units statement.

### Gaps

Kind: prose/table · handoff lines 207-218 · verdict **CONCERNS**

- Narrative: The section is a single gaps table with no prose. It does put the most material gap (executed credit documents) first, but several rows use pipeline status wording, and it contradicts and duplicates the gaps ledger directly above it.
- Visual: The table renders cleanly at 1440 px with no clipping or overlap, and no module codes leak. However, the Source column is padded with doubled internal module names and the Gap column wraps on the repeated bracketed tags.

1. **High · narrative** (New reader, Auditor)
   - Where: line 212: "CP-1A readiness of CP-2 Ready with limitations | Confidence capped at Medium | Carry; resolve with documents" (rendered as "Business & governance readiness of Fundamental credit Ready with limitations", shot CP-2_s-207.png, Gaps table row 2)
   - Problem: The row is pipeline status talk: one module's readiness signal about another module. A portfolio manager cannot tell what is missing, which confidence is capped, or why. "Carry" is internal workflow wording, not an action the reader can take.
   - Fix: Name the missing evidence (for example payment-capacity terms) and say which conclusion is held at Medium confidence because of it, in reader language.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: Gaps table (lines 207-218) vs the 'a method step Gaps ledger' table GP1-GP5 directly above it in shot CP-2_s-207.png (y~355-680 vs y~1435-1845)
   - Problem: The page has two gap lists for the same module, and their wording and fields differ. GP2 says "Confidence capped below High" where the Gaps table says "capped at Medium". GP5 says "Leverage uses FY2024 annual earnings" where the Gaps table says "Annual EBITDA used at pro forma date". Only the ledger has Severity, and only the Gaps table has the hedge and shareholder rows. The reader cannot tell which list is authoritative or complete.
   - Fix: Keep one gaps table on the page that holds all seven gaps with a severity for each, and drop or merge the other.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 216: "Hedge notionals not read upstream | Fixed-rate share taken as approximate | CP-2E to read derivatives note"
   - Problem: "upstream" is pipeline vocabulary. The Action tells another module what to do (rendered as "Rates, FX & hedging to read derivatives note") instead of naming the missing evidence. The Effect also does not say how approximate the fixed-rate share is or which way the error could cut on interest-rate risk.
   - Fix: Say that the derivatives note's hedge notionals were not used, and state the effect on the fixed-rate share and rate sensitivity in reader terms.
4. **Medium · narrative** (Saboteur)
   - Where: line 211: "Extraction capacity and covenant headroom unsized; house ratios only"
   - Problem: This is the most material gap, but the passage does not say what it means for the view. "house ratios only" is undefined in this section, and elsewhere on the page (RK4) a "house headroom of 23.47%" appears that a reader could mistake for covenant headroom. Only the last row (line 217) states whether a gap changes the view.
   - Fix: For each gap, state in plain words whether it could change the conclusion, and say explicitly that the 23.47%/26.02% cushions are not covenant headroom.
5. **Medium · visual** (Auditor, New reader)
   - Where: Source column of the Gaps table, shot CP-2_s-207.png x~985-1150, y~1495-1840 (for example "Business and transaction fact pack (Business & governance)", "Financial data foundation (Financial foundation)", "Source readiness")
   - Problem: The Source column cites internal module names instead of documents. Each name also repeats in a parenthetical alias, so the column wraps to two lines on almost every row and gives the reader no document to check.
   - Fix: Cite the underlying document or filing (or 'not in pack') in the Source column, each named once without the duplicate alias.
6. **Low · visual** (New reader)
   - Where: Gap column cells, shot CP-2_s-207.png x~300-560, rows 1, 3, 4 and 5 ("...absent [Insufficient / Information]")
   - Problem: The bracketed status tag repeats on four of seven rows and wraps across lines, which bulks out the narrow Gap column and adds register wording the reader does not need.
   - Fix: Show the status as a short chip or a separate Status column, or drop it where the Gap text already says the item is absent.

### Limitations

Kind: reader passage · handoff lines 52-59 · verdict **CONCERNS**

- Narrative: The five limitations are specific and each is tied to a named conclusion. But two use pipeline language ("upstream registers", "built upstream"), "house net debt" is never defined, and the headroom caveats never say whether the low near-term default risk call still holds.
- Visual: The section is a plain, readable bullet list with no chart of its own and no clipping. Its weaknesses are page placement (analytical tables render after it) and bullets with no lead-ins, which are hard to scan. The Credit-risk transmission map beneath it belongs to a different unit and was not judged here.

1. **Medium · narrative** (Auditor, New reader)
   - Where: line 56: "earnings contributed by the FY2024 acquisitions are not disclosed in the upstream registers"; line 58: "No quarterly or last-twelve-month figures were built upstream" (shown verbatim in CP-2_limitations.png, bullets 3 and 5)
   - Problem: "Upstream" and "registers" are pipeline words, not reader language. A portfolio manager cannot tell whether the gap is in the issuer's disclosure or only in the analysis inputs, which changes how much weight to give it.
   - Fix: Say where the gap actually is (for example "the FY2024 annual filing does not disclose acquired earnings" or "quarterly figures were not prepared for this review"), without pipeline terms.
2. **Medium · narrative** (Saboteur)
   - Where: line 55: "Pro forma acquisition add-backs could make the covenant headroom larger, and different netting could make it smaller. The 23.47% EBITDA cushion is therefore an indicator, not a covenant test." together with line 58: "the view uses FY2024 annual earnings for leverage at the October 2024 pro forma date"
   - Problem: Two limitations both weaken the 5.55x / 23.47% headroom that supports the "near-term default risk is low" call. Neither says which way the net effect most likely goes, or whether the low-risk judgement still holds. "Larger or smaller" leaves the committee with no direction.
   - Fix: Add one sentence saying whether the low near-term default risk call survives these caveats and which direction of error is more likely.
3. **Medium · narrative** (New reader)
   - Where: line 55: "use the company's EBITDA As Defined and house net debt, not the covenant definitions"; line 54: "The view that extraction is likely to recur cannot be sized"
   - Problem: "House net debt" is not defined anywhere in the module. The reader cannot tell what is netted, so cannot judge the stated error. "Extraction" is analyst shorthand for debt-funded payouts to shareholders, and the reader has to infer it.
   - Fix: Define house net debt in a short clause (what cash is netted, at what date), and name the thing being sized as debt-funded dividends and buybacks.
4. **Low · visual** (Auditor)
   - Where: CP-2_limitations.png, "On this page" sidebar (approx. y 640-1140 original px): "Limitations" is followed by "Maps, Request, Sources, Credit view, Strengths and weaknesses"; handoff line 60 "### Credit view" follows Limitations
   - Problem: Analytical content (Credit view tables, Strengths and weaknesses) renders after Limitations and after Sources. Limitations is therefore not the closing passage of the analysis, which breaks the house reading order of bottom line, findings, contrary evidence, limitations.
   - Fix: Render Limitations after all analytical passages and tables, immediately before Request and Sources.
5. **Low · visual** (New reader)
   - Where: CP-2_limitations.png, Limitations block (approx. x 350-1010, y 225-650 original px), five undifferentiated grey bullets
   - Problem: Unlike Key findings, these bullets have no bold lead-in naming the conclusion each one qualifies (extraction, headroom, margin durability, business quality, earnings period). A scanning reader must read every line to find the caveat on a given conclusion.
   - Fix: Open each bullet with a short bold label naming the conclusion it limits, as the Key findings bullets do.

## Downside (CP-2A)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-2A/12f53f9c85569117da3121a4c68269e998863dd8780fafbf86af76c5c41086e3/1.response.md`

### Stress design and status

Kind: prose/table · handoff lines 90-126 · verdict **BLOCK**

- Narrative: Lines 90-126 are methods and status material, but they are written for the pipeline, not a credit committee. The register-code paragraph is garbled on screen, the confidence statement uses internal scoring fields, and the tables show ten-decimal figures and s/k fractions under internal scenario IDs. A source reference also sits in a narrative sentence.
- Visual: There is no chart in this section; three tables carry it. The Stressed flows and metrics table is cut off on the right (three columns off-screen), has an empty band under s00 and mixes monospace and normal headers. Basis chips are repeated on every row.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 94: "Two method texts disagree. The SKILL output profile defines registers T2B.1 to T2B.9 and T5.1 to T5.7 ... stay in this handoff, as the absorbed CP-2B phase requires." On screen (CP-2A_s-90.png, y~270-320) it reads "defines registers a method step to method steps to a method step"
   - Problem: This paragraph is the model's notes on its own method: SKILL, register codes, handoff, absorbed phase. The label replacement on screen also makes it nonsense. A credit reader gets nothing from it.
   - Fix: Drop the paragraph from the reader view, or replace it with one plain sentence saying the scenario and break-point tables follow the analyst's stress method.
2. **High · narrative** (Auditor, New reader, Saboteur)
   - Where: Line 98: "Helper scripts were not run and were replaced by a hand count: 10 material claims ... give E 86. C is 90 ... S is 0.7 ... qa_status is Passed with limitations, and committee_status is Draft Only."
   - Problem: The confidence statement is written in internal scoring and field names: E, C, S, qa_status, committee_status, "helper scripts". A committee member cannot tell what 61/100 rests on, or whether "Draft Only" limits how far they can rely on the module.
   - Fix: Give confidence as Medium (61/100) with one plain sentence on why: no covenant definitions, no hedge schedule, no executed credit documents. Leave out the scoring internals and field names.
3. **High · narrative** (Saboteur, New reader)
   - Where: Lines 113-114: "| SC1 | 3,547.05 | 1,187.9922 | 1,224.0578 | 7.0672812619 (7.07x) | 6.5279598540 (6.53x) | 2.9857519267 (2.99x) | 0.0488294958 (4.88%)"
   - Problem: The table shows raw calculator output to ten decimal places, with the rounded figure in brackets. This suggests precision the analysis does not have, it uses different precision from the s00 row and the summary table, and it shows FCF / total debt as a raw fraction.
   - Fix: Show each value once, rounded to the same precision as the summary table (USD m to one decimal or whole, ratios to two decimals with x, shares as %).
4. **High · narrative** (Auditor)
   - Where: Line 116: "The control row s00 reconciles exactly to CP-1 calculations C05, C11, C12 and C31."
   - Problem: Source references (calculation IDs and a module name) sit inside a narrative sentence, which breaks the house rule that references live only in Basis lines, Source columns and Sources.
   - Fix: Put the reconciliation references in a Basis line or in the s00 row's Source cell, and keep the sentence plain: "The base row matches the reported FY2024 figures."
5. **High · visual** (Auditor, New reader)
   - Where: Stressed flows and metrics table, CP-2A_s-90.png crop x 300-1160, y 785-1015 (display coords)
   - Problem: The table is cut off at the right edge: the "PF net debt / EBI…" header is truncated, and the EBITDA / cash interest, FCF / total debt and Source columns are off-screen. The s00 row also has a tall empty band beneath it.
   - Fix: Fit the table to the column width: fewer or narrower columns, ratios shown only as rounded x or % values. Keep the Source column visible and keep row heights consistent.
6. **Medium · narrative** (New reader, Saboteur)
   - Where: Lines 104-106: "| s00 | 0 | 0 |" / "| SC1 | 0.1500 | 0.0259 |" / "| SC2 | 0.3100 | 0.0518 |" with headers "EBITDA decline s" and "Cash-interest increase k"
   - Problem: The shocks appear as unlabelled decimals (s, k) under internal scenario IDs (s00, SC1, SC2). Everywhere else in the module they are 15% / 31% and Moderate / Severe. The reader has to work out the mapping and the units.
   - Fix: Label the scenarios Base / Moderate / Severe and give the shocks as percentages (15%, 2.59%), matching the summary table above.
7. **Medium · narrative** (Auditor, Saboteur)
   - Where: Line 96: "Module status: Completed with Limitations. Primary fragility is commercial aftermarket volume and its margin gearing. The fastest downside path runs from..."
   - Problem: "Module status" is pipeline wording. The rest of the paragraph repeats the Bottom line and Downside view almost word for word, and it sits under a methods heading near the end, so the page reads as repetitive.
   - Fix: Remove the status label and the repeated transmission path. Keep this section to stress design only (base period, operands, scenario definitions).
8. **Low · visual** (New reader)
   - Where: Scenario definitions and Break points tables, CP-2A_s-90.png y 480-740 and 1080-1305 (display coords)
   - Problem: Every row has a "Basis" chip next to its ID, even where the row already has a Source column. Some headers are set in monospace ("EBITDA decline s", "EBITDA decline at break") and others in the normal face, so the tables look inconsistent. The Source cells repeat "Fundamental credit synthesis (Fundamental credit)".
   - Fix: Use one header typeface. Drop the Basis chip where a Source column already exists, and name each source once.

### Analytical appendix — complete canonical registers (part 1 of 2: from 'T2B.1 Source Register')

Kind: register appendix · handoff lines 127-234 · verdict **CONCERNS**

- Narrative: This is a data-register appendix, not prose, so the house order does not apply. The figures I spot-checked are consistent, e.g. 1,880 − 0.15×4,173 − 30 ≈ 1,224 and 6,637×0.02 = 132.74. The text still exposes pipeline language (handoff, consumer, canonical, downstream module), internal IDs and unexplained algebra, and it has no bottom line for the reader.
- Visual: The tables render cleanly with a light grid, but the headings read "a method step ...", the code substitution produces broken labels ("Gap Gap 5", "Downside-DP-001"), the headers are raw snake_case, and long JSONL filenames wrap and stretch the rows. The appendix also floods the On this page navigation with about 18 placeholder entries. Not verified: the part of the section below the Fragility Map, checked only through the DOM text dump (tmp/CP-2A-081-dom.html), not through a full-resolution screenshot crop.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: Line 219 "#### T2B.8 Cross-Module Handoff Register"; line 221 headers "Downstream Module | Handoff Item | Why It Matters | Required Consumer Action"; rendered as "a method step Cross-Module Handoff Register" (DOM dump tmp/CP-2A-081-dom.html)
   - Problem: Pipeline vocabulary reaches the page: the reader sees "handoff", "consumer" and module-to-module routing ("Liquidity", "Rates, FX & hedging" told to "Build runway against SC1 and SC2 FCF"). This is a list of instructions between modules, not credit analysis, and the house standard bans these words.
   - Fix: Keep the cross-module routing register off the reader page, or retitle it as open follow-up questions with no handoff or consumer wording.
2. **High · visual** (Auditor + Saboteur (promoted))
   - Where: Rendered headings "a method step Source Register", "a method step Business Model Snapshot", "a method step Fragility Map" (shot CP-2A_s-129.png, y≈195, 762, 1740) and the matching On this page entries
   - Problem: The renderer swaps the register codes (T2B.1 and the rest) for the placeholder "a method step", so every heading and table-of-contents entry carries meaningless filler. About 18 of these entries crowd the side navigation.
   - Fix: Render each table under a plain reader title (e.g. "Source register") without the code or the placeholder, and collapse the appendix to one navigation entry.
3. **High · visual** (Auditor + New reader (promoted))
   - Where: Rendered cells "Gap Gap 5" (from line 150 "Gap CP-2A-GAP-005"), "Downside-DP-001" (line 184 "CP-2A-DP-001"), "HO-Financial foundation" (line 134 "HO-CP-1"), "Financial data foundation (Financial foundation)" (line 149); shot y≈1386, 405
   - Problem: Code substitution produces broken or duplicated labels: "Gap Gap 5", hybrid IDs like "Downside-DP-005" and "Downside-MON-...", and module names repeated in brackets. Internal row IDs remain on screen in the Pathway, Monitoring and Handoff tables.
   - Fix: Drop internal row and gap IDs from reader tables, or map them to one clean reader label with no doubled words.
4. **Medium · narrative** (Saboteur)
   - Where: Line 199 "SC1 stressed metrics | s 0.15, k 0.0259 | E(1−s), I(1+k), F − Es − Ik | FCF USD 1,224.0578 million; 7.07x; 6.53x; 2.99x"
   - Problem: Unexplained algebra symbols (s, k, E, I, F) and four-decimal precision on USD millions suggest more accuracy than a proportional stress supports. The ratios in the Result cell are unlabelled (which is total leverage, net leverage, cover?).
   - Fix: Label each result (total leverage 7.07x, pro forma net 6.53x, interest cover 2.99x), round FCF to whole USD millions, and define the stress inputs in words.
5. **Medium · narrative** (Saboteur + New reader (promoted))
   - Where: Line 127 "### Analytical appendix — complete canonical registers" (lines 129-234, nine dense tables)
   - Problem: The appendix repeats the module's findings at a much higher density, with no bottom line telling the committee what to take from it. Small inconsistencies across tables are easy to miss (e.g. "FCF before distributions" in T2B.4 vs "FCF" elsewhere). The word "canonical" is pipeline language.
   - Fix: Open the appendix with a one-line statement of what it supports, drop "canonical" from the title, and keep only the registers a reader needs to check the conclusions.
6. **Medium · visual** (New reader + Auditor (promoted))
   - Where: T2B.1 headers, line 131: "source_document_id | source_document_name | source_quality | period | entity_covered | data_supplied | limitation | downstream_use"; shot y≈225
   - Problem: Raw snake_case field names are shown as column headers. "downstream_use" ("Base operands and control row") and the row "CTX | context | Settings only" describe the pipeline, not the issuer.
   - Fix: Use plain-English column titles, and remove the CTX settings row and the downstream-use column from the reader's view.
7. **Medium · visual** (New reader)
   - Where: Source Trace cells, e.g. line 145 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 9"; shot CP-2A_s-129.png y≈930-1260
   - Problem: The ingested JSONL filename wraps across four or five lines in narrow 7- and 8-column tables, so rows are tall and hard to scan. A reader would recognise "FY2024 10-K, p. 9".
   - Fix: Show the source by its document title ("FY2024 annual report (10-K), p. 9") and keep the file identity in the Sources list.
8. **Low · narrative** (New reader)
   - Where: Line 228 "FY2028 wall at up to 8.71x gross leverage | Refinancing and LME vulnerability | Assess A&E or exchange risk"; line 182 "PD/LGD/RV/Monitoring Consequence"
   - Problem: Undefined abbreviations (LME, A&E, RV, RPK, LGD) are used without expansion.
   - Fix: Spell out each abbreviation at first use in the appendix or link it to a glossary.

### Analytical appendix — complete canonical registers (part 2 of 2: from 'T2B.9 Gaps Ledger')

Kind: register appendix · handoff lines 235-330 · verdict **CONCERNS**

- Narrative: This is a data register appendix with no prose, so judgement-first ordering does not apply. Its wording still leaks pipeline language ("Cross-Module Handoff", "Responsible Module", undefined DP/MON IDs, CP codes at lines 295-319). It also has two misreadable ratings: the ambiguous "Consequence for Confidence: High" and a "Critical" probability rating on a dividend that has already been paid.
- Visual: The section has no charts, only tables. In the screenshot they are legible and well spaced. Every heading carries the filler "a method step", each row has an empty "Basis" chip, and three-line raw .jsonl filenames dominate the Source Document column. The screenshot ends at the Probability / Impact Matrix header, so T5.5-T5.7 and the catalyst table were judged from the handoff text only.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: Line 239 "CP-2A-DP-004; CP-2A-MON-003", rendered as "Downside-DP-004; Downside-MON-003"; line 302 "T5.6 Watchlist & Cross-Module Handoff", with columns "Receiving Module | Handoff Content" (line 304); line 319 "relayed by CP-2"
   - Problem: The reader sees internal pathway and monitor IDs (DP-004, MON-003) that are never defined, plus the pipeline words "Cross-Module Handoff" and "Responsible/Receiving Module". In the handoff, lines 295-309 also give module codes (CP-4, CP-3C, CP-2D). A committee member cannot tell what is being watched or by whom.
   - Fix: Replace the IDs with short descriptions of the pathway or monitor ("FY2028 refinancing pathway", "covenant watch level"), and rename the watchlist columns in reader terms ("Follow-up in", "What to check").
2. **High · visual** (Auditor + New reader (promoted))
   - Where: Screenshot CP-2A_s-235.png, every table heading and the sidebar: "a method step Gaps Ledger", "a method step Event Source Register", "a method step Catalyst Calendar", and in Gap 5's row "a method step input-cost row" (from handoff line 235 "#### T2B.9 Gaps Ledger", line 243 "T2B.2 input-cost row")
   - Problem: The renderer swaps register codes (T2B.9, T5.1) for the literal words "a method step". That puts meaningless filler in front of every heading, in about 15 sidebar entries and inside a table cell. It is pipeline vocabulary that has been hidden badly, not removed.
   - Fix: Drop the code and show only the plain heading ("Gaps ledger", "Event source register"), and point Gap 5 to a readable section name such as "Stress transmission: input-cost row".
3. **Medium · narrative** (Saboteur)
   - Where: Line 237-239 column "Consequence for Confidence" with value "High" for "Executed credit agreement and indentures"
   - Problem: "High" under "Consequence for Confidence" reads two ways: a large loss of confidence, or high confidence. For the most important gap (the missing covenant documents) a reader could take it to mean the watch levels are reliable.
   - Fix: Label the column "Impact of gap on confidence" and state the direction, e.g. "High: watch levels unconfirmed".
4. **Medium · narrative** (Saboteur)
   - Where: Line 273 "EV-01 | Special dividend paid | High | Liquidity; LGD | High" and line 284 "EV-01 | Special dividend paid | High | High | Critical"
   - Problem: An event already paid on 2024-10-18 is given a forward "Probability: High" and the headline "Critical" risk rating. That mixes a crystallised fact with the actual forward risk (another debt-funded distribution), so the reader cannot tell what is being rated.
   - Fix: Rate the forward risk explicitly ("Recurrence of a debt-funded distribution") and mark the paid dividend as occurred, not probable.
5. **Medium · narrative** (New reader)
   - Where: Lines 247-330: T5.1 Event Source Register, T5.2 Catalyst Calendar, T5.3 Event Risk Register, T5.4 Probability / Impact Matrix, T5.5 Monitoring Priority Table, T5.6 Watchlist, plus cp2b.cp_model_catalysts
   - Problem: The same six events (special dividend, securitization draw and maturity, 2027 notes, FY2028 wall, buybacks) are repeated across seven tables with small column changes. The result is a long run of tables with no lead sentence telling the reader which one matters.
   - Fix: Merge these into one event table (date, event, probability, impact, monitoring trigger, source) under a one-line lead stating the main event risk.
6. **Medium · visual** (New reader)
   - Where: Screenshot CP-2A_s-235.png, Event Source Register, Source Document column (y≈720-1100): "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 63" repeated in all six rows
   - Problem: Raw extraction filenames with a .jsonl suffix and accession numbers wrap over three lines in each row. They make the widest column of the table and say less than "FY2024 annual report (10-K), p.63". The same strings come back in the snake_case table at line 323 ("event_date_or_window", "source_id", status "READY").
   - Fix: Show a short document label in Source columns ("10-K FY2024, p.63"), and give the last table reader headers with no READY status column.
7. **Medium · visual** (Auditor)
   - Where: Screenshot CP-2A_s-235.png, every ID cell in all four visible tables: "Gap 1 / Basis", "EV-01 / Basis", "2024-10-16 Basis"
   - Problem: Every row carries a grey "Basis" chip with no visible content. It doubles the row height and adds noise, and since these tables already have Source columns the reader cannot tell what it refers to.
   - Fix: Show the Basis chip only where a row has basis content not already in its Source column, or put it in one consistent trailing column.
8. **Low · visual** (Auditor)
   - Where: Screenshot CP-2A_s-235.png, Catalyst Calendar and Event Risk Register Source column: "Financial data foundation (Financial foundation)"; Gap 7 follow-up source "Research questions or market data"
   - Problem: The module-name mapping duplicates labels in parentheses. It also turns an internal module (CP-DR) into a "follow-up source" named after a library page instead of an actual document such as rating agency reports.
   - Fix: Show one label per source, and name the real document to obtain ("rating agency reports, bond quotes").

### Gaps

Kind: prose/table · handoff lines 364-374 · verdict **BLOCK**

- Narrative: The Gaps table mixes pipeline housekeeping with the one material limitation, which is that the credit agreement is absent so the leverage break points are not on covenant definitions. That limitation is understated, and its effect, action and source cells use internal language and point to modules rather than issuer evidence.
- Visual: The four-column table is clean, evenly spaced and fits the 1440 px page with no clipping. The visual defects are a stray Basis chip and a raw bracketed tag in one Gap cell, and a raw .jsonl filename wrapping in the Source column.

1. **High · narrative** (Auditor, New reader)
   - Where: line 368: "CP-1B handoff not supplied" (rendered "Earnings changes handoff not supplied"); line 369: "Helper scripts not run | Confidence and completeness counted by hand | Re-run when tooling available"; line 370: "Research adoption table not applicable"
   - Problem: Three of the six rows describe the pipeline's own plumbing rather than the credit, using pipeline vocabulary ("handoff", "helper scripts", "tooling", "research adoption table"). That breaks the house rule against pipeline wording, and a portfolio manager gets nothing from these rows.
   - Fix: Drop the process rows or move them to a run log. Keep only gaps that limit the credit view, written in reader language (for example, "No interim earnings update; uses FY2024 annual figures").
2. **High · narrative** (Saboteur, New reader)
   - Where: line 371: "Executed credit documents absent [Insufficient Information] | Watch levels house-basis | Supply credit agreement"
   - Problem: This is the gap that matters most. Without the credit agreement, the 7.25x/7.50x watch and break levels are not on the governing covenant definitions. Yet the table gives it the same weight as trivial process rows, and its effect is the opaque phrase "house-basis". Nothing tells the committee how far the break points could move or that covenant headroom is unconfirmed.
   - Fix: Put the material gaps first, and state the effect in plain terms (for example, "Leverage break points use our own EBITDA definition, not the credit agreement's; covenant headroom is unconfirmed").
3. **Medium · narrative** (Auditor, New reader)
   - Where: lines 368-373 Source column: "Source readiness (CP-0)" (rendered "Source readiness"), "context", "context", "Source readiness"
   - Problem: Only one row cites an actual issuer document. The rest give a module name or the bare word "context", which is not a source a reader can check, so the Source column looks evidenced when it is not.
   - Fix: Cite the document or page that establishes each gap, or write "none, absence of document" explicitly instead of a module name or "context".
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 373: "Liquidity runway, covenant tests, maturity stress and working capital held at base (method exclusions) | Deferred to CP-2D, CP-4, CP-3C and CP-2G | Downstream owners"; line 372 Action: "CP-2E to read derivatives note"
   - Problem: The Effect and Action cells route the reader to other modules ("Downstream owners", "Rates, FX & hedging to read derivatives note") and use internal terms ("held at base", "method exclusions"). They do not say what the downside view leaves out, for example that the stress cases assume no liquidity or covenant pressure.
   - Fix: State the consequence for this downside view in reader terms (for example, "Stress cases do not test liquidity runway or covenants; see Liquidity page"), without owner or module routing.
5. **Medium · narrative** (Saboteur)
   - Where: line 372: "Hedge note not read [Insufficient Information] | Rate accelerator approximate"
   - Problem: "Rate accelerator approximate" does not say which way the error runs or how large it could be. The SC1/SC2 interest shocks (0.0259/0.0518 per point) feed the coverage ratios above, so a reader cannot tell whether the stressed cover of 2.36x is overstated.
   - Fix: Say what the approximation assumes (for example, "assumes no hedging; actual cash-interest sensitivity may be lower") and which stressed metrics it affects.
6. **Medium · visual** (Auditor, New reader)
   - Where: Gaps table, shot CP-2A_s-364.png crop y≈1740-2230 (/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2A-084-a.png): Gap cell "Hedge note not read [Insufficient Information] Basis"
   - Problem: A stray "Basis" chip sits inside the Gap cell of one row only. The bracketed "[Insufficient Information]" register tag shows as raw text. Both look like rendering artefacts in a table that otherwise has a dedicated Source column.
   - Fix: Render the evidence label as a consistent chip or column across rows. Drop the stray Basis link from the Gap cell, since the Source column already carries the reference.
7. **Low · visual** (New reader)
   - Where: Gaps table Source column, hedge row: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73" (same crop)
   - Problem: The raw ingestion filename, with its accession number and .jsonl extension, wraps over two lines. It is the only document reference in the column and is unreadable as a citation.
   - Fix: Show a reader label such as "10-K FY2024, p. 73" and keep the file identity in a tooltip or in Sources.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 375-378 · verdict **BLOCK**

- Narrative: Both passages are pipeline material shown to the reader. The Request opens with a garbled \"Downside downside pathway\" label substitution and a snake_case pathway name. Next module is a set of module-to-module instructions in s/k notation, with units that contradict the page and a promised recheck by a module marked Not assessable.
- Visual: This section has no chart, map or timeline, only two plain paragraphs. Typography is clean, but the Request block sits mid-page between Maps and the Downside view at full heading weight, and the Next module parameters are buried in running text.

1. **High · narrative** (New reader + Auditor)
   - Where: Handoff line 3: "CP-2A downside pathway, with the absorbed CP-2B event and catalyst register ... on the credit_snapshot pathway." Rendered (CP-2A_s-1.png, Request, y~220-330): "Downside downside pathway, with the absorbed Downside event and catalyst register"
   - Problem: The display layer replaces module codes with labels, so the first sentence on the page reads "Downside downside pathway" and "absorbed Downside event and catalyst register", which is garbled. "credit_snapshot pathway" and "absorbed ... register" are pipeline wording the house standard bars from the page.
   - Fix: Use a plain-language scope sentence (for example "Downside stress and dated-event watchlist for TDG, credit snapshot as of 30 September 2024") with no substituted code labels or snake_case pathway names.
2. **High · narrative** (Auditor + Saboteur)
   - Where: Handoff line 377: "CP-2E should read the derivatives note ... CP-2G should carry SC1 and SC2 (s 0.1500 / k 0.0259 and s 0.3100 / k 0.0518) ... CP-4 should recompute". Rendered (CP-2A_s-375.png, Next module, y~2230-2340)
   - Problem: This section consists of instructions from one module to another ("Rates, FX & hedging should read...", "Forward credit model should carry..."), which is pipeline language a credit committee reader has no use for. The undefined s/k notation and the 0.0259 fraction contradict the "2.59%" shown for the same shock in the Downside view table.
   - Fix: Turn it into a reader-facing "What to watch next" line (for example "Hedge roll-off could raise the 2.59%-per-point interest sensitivity; covenant break points await the credit agreement"), using the page's own % units and no s/k or SC codes.
3. **Medium · narrative** (Saboteur)
   - Where: Handoff line 377: "CP-4 should recompute the 7.25x and 7.50x break points on the governing definitions once the documents are supplied." Rendered as "Legal & covenants should recompute..."; the nav in the same screenshot marks Legal & covenants "Not assessable"
   - Problem: The reader is told a module will confirm the 7.25x/7.50x levels, but the left nav on the same page shows that module as Not assessable in this run, so the recheck will not happen. Calling the levels "break points" also contradicts the page's own description of them as house-basis "watch levels".
   - Fix: Say plainly that the 7.25x/7.50x levels are house-basis watch levels, not covenant tests, and remain unconfirmed until the credit agreement is obtained.
4. **Medium · visual** (New reader + Auditor)
   - Where: CP-2A_s-1.png, "On this page" nav and body, y~700-760 (Request heading placed after Timeline/Maps, before Sources and Downside view)
   - Problem: A "Request" block (the prompt scope sent to the model) is shown as a reader-facing section with the same heading weight as the analysis, placed between the Maps panel and the main Downside view. That breaks the reading flow and exposes pipeline plumbing on screen.
   - Fix: Fold Request and Next module into a small provenance or scope footnote after Gaps, or drop them from the Modules page, so analysis sections read consecutively.
5. **Low · visual** (New reader)
   - Where: CP-2A_s-375.png, Next module paragraph, y~2230-2340
   - Problem: Parameter strings such as "(s 0.1500 / k 0.0259 and s 0.3100 / k 0.0518)" are set in running proportional text with no table or units, so the figures are hard to scan and easy to misread. This contrasts with the monospace value chips used elsewhere on the page.
   - Fix: If scenario parameters must appear, show them as labelled percentages in the existing value-chip style or point to the scenario table.

### Sources

Kind: prose/table · handoff lines 5-19 · verdict **BLOCK**

- Narrative: The Sources passage is provenance metadata in pipeline register: "Supplied handoff", "named upstream by the method", ".jsonl" filenames, "context". It also buries the key caveat that every shock is an analyst assumption.
- Visual: The two tables render cleanly, with no clipping. But 64-character hashes take most of the width, a stray Basis chip and duplicated module columns add noise, and the block sits mid-page instead of closing the module.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 12 table header "| Supplied handoff | Module | sha256 |" and line 18 "CP-1B is named upstream by the method but was not supplied, so it is unavailable for this run." (rendered: "Earnings changes is named upstream by the method but was not supplied")
   - Problem: Pipeline vocabulary is on screen: the column header "Supplied handoff", and "named upstream by the method" / "not supplied". The house standard rules these out as reader language. A PM cannot tell what "Earnings changes" is, or whether missing it matters to the downside view. The rendered sentence is also ungrammatical ("Earnings changes is named").
   - Fix: Head the table as the earlier analysis it relies on, and say plainly that the earnings-bridge analysis was not available and what it would have added.
2. **Medium · narrative** (New reader, Auditor)
   - Where: Line 9 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" and line 10 "context"
   - Problem: The sources are named by internal file identifiers: a raw .jsonl filename that wraps over four lines on screen, and a source called "context". A reader can't recognise the first as the FY2024 annual report on Form 10-K, or the second as run settings.
   - Fix: Name each source in reader terms, e.g. "Annual report on Form 10-K, fiscal year ended 30 Sep 2024" and "Run settings (analyst inputs)", with the file identifier secondary or hidden.
3. **Medium · narrative** (Saboteur)
   - Where: Line 10 "stress assumptions blank, so the shocks below are analyst assumptions; not issuer evidence"
   - Problem: The disclosure that every stress shock is an analyst assumption, not issuer guidance or stress inputs, is buried in a table cell in Sources, in shorthand ("stress assumptions blank"). A committee member reading the bottom line's 23.47% / 31% figures could take them as sourced scenarios.
   - Fix: Carry the analyst-assumption status of the shocks in the Limitations passage and the scenario table in plain words, and keep only a neutral description here.
4. **Medium · visual** (New reader, Auditor)
   - Where: Both Sources tables, sha256 column (CP-2A_s-5.png, y≈220-700; crop CP-2A-072-a.png)
   - Problem: Five full 64-character hashes take the widest columns of both tables. They mean nothing to a credit reader and squeeze the useful "Use in this module" text into a narrow, six-line cell.
   - Fix: Drop the hashes from the reader view, or shorten them to a small tooltip or footnote, and give the width to the description of use.
5. **Medium · visual** (Auditor)
   - Where: On this page nav and body order: "Limitations, Timeline, Maps, Request, Sources, Downside view, Map: stress scenario, Catalyst view..." (CP-2A_s-5.png left nav and body)
   - Problem: Sources sits mid-page, with the Downside view, its summary table, a second stress map and the Catalyst view below it. The reader meets a provenance table halfway through the analysis instead of at the end, where the house reading order puts it.
   - Fix: Render Sources as the module page's closing block, after all analytical passages, tables and visuals.
6. **Low · narrative** (New reader)
   - Where: Line 9 "all other figures through CP-0, CP-1 and CP-2 page citations" (rendered "through Source readiness, Financial foundation and Fundamental credit page citations")
   - Problem: The renamed module labels read as an awkward compound noun. A reader can't tell that the figures come from the 10-K pages cited by those earlier sections.
   - Fix: Say "all other figures are taken from the earlier sections, which cite the filing page by page".
7. **Low · visual** (Auditor, New reader)
   - Where: Source column chip "…20240930.htm.jsonl Basis" (crop CP-2A-072-a.png, first row) and Supplied-handoff table columns "Financial data foundation | Financial foundation"
   - Problem: A stray "Basis" chip sits on a Sources row, where no Basis line belongs. The second table repeats each module name in two columns, with inconsistent labels ("Financial data foundation" vs "Financial foundation", "Fundamental credit synthesis" vs "Fundamental credit").
   - Fix: Remove the Basis chip from Sources rows and show each earlier analysis once, under the same label the left navigation uses.

### Bottom line

Kind: reader passage · handoff lines 22-29 · verdict **CONCERNS**

- Narrative: The bottom line does put its judgement first ("Leverage headroom, not liquidity or debt service, breaks first"), but leverage measures change mid-passage, key terms (incurrence level, EBITDA As Defined) are undefined, and the second paragraph ends on pipeline wording ("the pack") with an ambiguous "Neither".
- Visual: The section has no chart. Visually it is two all-bold display paragraphs with monospace chips, its heading is hidden under the sticky bar after the anchor jump, and no Basis line is visible on screen.

1. **High · narrative** (Saboteur + New reader (promoted))
   - Where: L24 "net leverage reaches 7.25x after a 23.47% fall" / L27 "total leverage reaches 8.71x and pro forma net leverage 8.04x. That leverage would have to be refinanced"
   - Problem: The bottom line moves between three leverage measures (pro forma net, total, pro forma net again) and the 7.25x and 7.50x thresholds without saying which measure each threshold applies to. "That leverage" in L27 could mean either 8.71x or 8.04x, so a committee member cannot tell how far the severe case sits above the 7.25x level.
   - Fix: Use one leverage measure throughout the bottom line, or name the measure each time and say which one the 7.25x and 7.50x levels are tested on.
2. **Medium · narrative** (New reader)
   - Where: L24 "push leverage through the 7.25x incurrence level"; L24 "7.50x after a 26.02% fall"; L24 "EBITDA As Defined"
   - Problem: "Incurrence level" and "EBITDA As Defined" are never defined. The 7.50x level is given a figure but no meaning, so the reader cannot tell what crossing it would trigger (a restricted payment block? a different covenant?).
   - Fix: Explain in a short clause what the 7.25x and 7.50x levels govern and that EBITDA As Defined is the company's adjusted EBITDA.
3. **Medium · narrative** (Auditor + Saboteur (promoted))
   - Where: L27 "made worse if a further debt-funded distribution is layered on before the shock. Neither can be sized from the pack."
   - Problem: "The pack" is internal pipeline wording. "Neither" has no clear referent: it could mean market access and the distribution, or something else. The paragraph therefore ends on an unexplained caveat instead of its judgement.
   - Fix: Name what cannot be sized and why in reader terms (for example, "future market access and the size of any further payout are not knowable from FY2024 filings"), or move it to Limitations.
4. **Medium · narrative** (Saboteur)
   - Where: L27 "cash interest rises 5.18%. The business still generates USD 526.39 million of free cash flow and covers cash interest 2.36x"
   - Problem: The 5.18% interest increase has no stated driver: is it a rate shock, and of what size? The free cash flow figure has no period (annual, FY2024 basis) and says nothing on whether it is before or after distributions, although L24 uses the "before distributions" measure.
   - Fix: State the rate assumption behind 5.18%, and label the USD 526.39 million as annual free cash flow before distributions on the FY2024 base.
5. **Medium · visual** (New reader + Auditor (promoted))
   - Where: CP-2A_bottom-line.png, crop CP-2A-073-a.png (x 320-1440, y 180-860): both Bottom line paragraphs
   - Problem: Two paragraphs of about 150 words are set entirely in large bold display type across 17 lines, with monospace dotted-underline number chips inside the bold text. The result is a dense wall that is slow to scan, and nothing stands out because everything is emphasised.
   - Fix: Show only the lead judgement sentence in display weight and set the rest of the bottom line in body weight, as in the VMO2 reference.
6. **Medium · visual** (Auditor)
   - Where: CP-2A_bottom-line.png top (y ~180-200 original): the section anchored from "On this page > Bottom line"
   - Problem: The "Bottom line" heading is not visible: the jump lands the first bold line directly under the sticky run bar, so the heading sits hidden behind it. The reader cannot see which passage they are in.
   - Fix: Offset the scroll anchor by the sticky header's height so the section heading stays visible after the jump.
7. **Low · narrative** (Saboteur)
   - Where: L24 "after a 23.47% fall ... 26.02% fall ... 45.05% fall ... 72.25% fall"
   - Problem: The break points are given to two decimals, but the shocks are analyst assumptions on a proportional EBITDA model that the module's own Limitations call optimistic. The decimals suggest a precision the method lacks.
   - Fix: Round the break points to whole percentages in the bottom line and keep the exact values in the break-point table.
8. **Low · visual** (Auditor)
   - Where: CP-2A_bottom-line.png, y ~200-860, region right of x ~1020 (original px)
   - Problem: No Basis line is visible under either Bottom line paragraph, unlike the handoff's L25 and L28. The right third of the content column is empty white space next to the dense bold block.
   - Fix: Show each paragraph's Basis as a small muted line (or a visible link) under the paragraph, and use the spare width for a narrower or wider measure.

### Key findings

Kind: reader passage · handoff lines 30-42 · verdict **BLOCK**

- Narrative: The findings are judgement-first, but the moderate-scenario bullet says the incurrence level is crossed when the module's own figures (6.53x net, 7.07x total, against 7.25x) and tables say it is not, and the liquidity bullet's \"covers amortisation\" quietly leaves out the USD 487 million securitization.
- Visual: There is no chart in this section. It is a clean bulleted list with bold lead sentences, but a negative value's sign falls outside its figure chip, USD values use a code-style monospace chip unlike the other figures, and no Basis lines are visible.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 34: "lifts total leverage to 7.07x and pro forma net leverage to 6.53x ... The incurrence watch level is the first threshold crossed, which closes the debt-funded route to further payouts"
   - Problem: Both figures are below the 7.25x incurrence level, and the module's own tables say this scenario stays under it (line 173: "Watch levels not reached"; line 199: "Below watch levels"). The bullet still reads as if the moderate scenario breaches the level and closes the payout route, so a committee could believe a 15% shock already uses up covenant capacity.
   - Fix: State plainly that the 15% plus one-point case stays below 7.25x (headroom of about 0.7x), and that the level is crossed only at a 23.47% decline.
2. **Medium · narrative** (Saboteur, New Reader)
   - Where: line 38: "scheduled maturities are USD 93 million to USD 92 million a year, plus the USD 487 million securitization due 2025-07-11. Even the severe scenario's free cash flow of USD 526.39 million covers amortisation."
   - Problem: The descending range "93 to 92" hides that FY2025 is USD 93 million and FY2026 and FY2027 are USD 92 million each (line 154). FY2025 needs USD 580 million including the securitization, which is more than the severe-case USD 526.39 million free cash flow, so "covers amortisation" is true only if the securitization is renewed. The bullet does not say that.
   - Fix: Give each year's maturity, then state that the severe-case free cash flow covers term amortisation but not the securitization, which depends on renewal by 2025-07-11.
3. **Medium · narrative** (New Reader)
   - Where: line 34: "Free cash flow before distributions is still USD 1,224.06 million and cover is 2.99x. The incurrence watch level"; line 36: "Refinancing the FY2028 cluster"
   - Problem: The section does not define "cover" (it means EBITDA As Defined to cash interest), "incurrence watch level" or "EBITDA As Defined", and it does not say these are house figures rather than covenant figures. The scenario ("A 15% fall") is never named as the moderate case, so a reader who has not read the sources cannot connect it to the scenarios mentioned elsewhere on the page.
   - Fix: On first use, say "interest cover (EBITDA As Defined / cash interest)", call the 15% case the moderate scenario, and give a short gloss for the incurrence level.
4. **Medium · narrative** (Saboteur)
   - Where: line 32: "Aftermarket carries higher gross margins than OEM, so a volume loss there cuts EBITDA by more than its sales share. The proportional shocks used here may therefore understate the earnings loss."
   - Problem: The first finding ends with a hedge that undercuts every figure in the bullets after it. It gives no margin figure and does not say that the mix split is undisclosed (line 212: "Mix split not disclosed"), so the reader cannot judge how large the understatement is. "First operating break" also sits awkwardly beside the bottom line's "leverage headroom ... breaks first".
   - Fix: Say directly that the size of the gearing cannot be measured because the margin by channel is not disclosed, and label this as the driver, separate from the leverage break.
5. **Medium · visual** (Auditor, New Reader)
   - Where: Financial policy bullet, shots2/CP-2A_key-findings.png crop (330,690)-(1040,990), saved as tmp/CP-2A-074-a.png: "USD -158 million"
   - Problem: The minus sign and "USD" are drawn outside the figure chip, and only "158 million" is chipped. A reader scanning the highlighted figures sees a positive 158 million. Line 40's phrasing "free cash flow of USD 1,880 million was already USD -158 million after dividends paid" makes the negative harder to read still.
   - Fix: Render the whole signed value inside one chip (for example "USD −158 million" or "a USD 158 million shortfall").
6. **Low · visual** (Auditor)
   - Where: Key findings block, shots2/CP-2A_key-findings.png, y≈190-820 (displayed)
   - Problem: USD amounts are set in a monospaced, bold, dotted-underline code font, while percentages and multiples use a lighter proportional chip. The prose looks like code, line rhythm becomes uneven, and the two kinds of figure look like different things.
   - Fix: Use one proportional-font figure style for all values, as the VMO2 reference does.
7. **Low · visual** (Auditor)
   - Where: Key findings bullets, shots2/CP-2A_key-findings.png: none of the five bullets shows its Basis line (the handoff has them at lines 33, 35, 37, 39, 41)
   - Problem: The reader cannot see any sourcing for the five findings on the page. Whether the Basis lines are hidden or moved elsewhere by design could not be confirmed from this view.
   - Fix: Show each finding's Basis line under its bullet in muted type, or confirm that the design keeps sources in the chip tooltips.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 43-47 · verdict **CONCERNS**

- Narrative: The passage does give real contrary evidence and named triggers. But its main mitigant is argued against the moderate scenario, which the module's own table shows never breaches. Unquantified claims and internal wording ("house figure", "watch levels") are packed into one ~210-word paragraph.
- Visual: This section has no chart. It renders as one long paragraph in a column about 540 px wide that leaves the right half of the page empty. No Basis line is visible, the typeface switches for two chipped figures, and the Issuer events heading sits flush against the last Limitations bullet.

1. **High · narrative** (Saboteur)
   - Where: line 45: "management could use the free cash flow it would otherwise distribute to repay debt, which would hold leverage below the watch levels in the moderate scenario."
   - Problem: The module's own summary table (line 67-68) puts the moderate scenario at 7.07x total and 6.53x pro forma net leverage, which is already below the 7.25x and 7.50x watch levels with no debt repayment. The best mitigant is therefore argued against a scenario that never breaches, and the scenario that does breach (severe, 8.04x net) gets no answer. A committee reader could take this as evidence that deleveraging fixes the stress when it was never tested where it matters.
   - Fix: Point the deleveraging argument at the severe scenario, or at the 23.47% break point, and say how much retained free cash flow would be needed to stay under 7.25x.
2. **Medium · narrative** (New reader, Auditor)
   - Where: line 45: one ~210-word paragraph from "The strongest evidence against a leverage-led downside..." to "...renew the securitization by 2025-07-11."
   - Problem: Three different jobs sit in one block of text on the page: contrary evidence, what would soften the view (two triggers) and what would harden it (four triggers). The reader has to pick the monitor list out of running prose, and the hardening triggers come last, where they are easiest to miss.
   - Fix: Keep the contrary-evidence paragraph short and put the softening and hardening triggers in two short lists, or as separate labelled sentences.
3. **Medium · narrative** (New reader)
   - Where: line 45: "put covenant-defined leverage well below the house figure" and "hold leverage below the watch levels"
   - Problem: "House figure" is internal analyst wording, and the section never defines "watch levels" (the 7.25x incurrence and 7.50x levels) or "moderate scenario" (a 15% EBITDA fall). A reader who lands on this anchor from the page index cannot tell what is being measured against what.
   - Fix: Name the measure ("our EBITDA As Defined leverage") and give the watch levels and scenario size inline, e.g. "below the 7.25x incurrence level in the 15% scenario".
4. **Medium · narrative** (Saboteur)
   - Where: line 45: "and capex is low. About 40% of sales is defense" ... "commercial aftermarket sales falling in any quarter"
   - Problem: "Capex is low" has no figure. The 40% defense share has no period or basis. "Falling in any quarter" has no measure (year-on-year or sequential). The two strongest mitigants and the main hardening trigger therefore cannot be checked or monitored as written.
   - Fix: Give the FY2024 capex amount or capex/sales, state the 40% as FY2024 net sales, and define the aftermarket trigger as year-on-year quarterly growth below zero.
5. **Medium · visual** (Auditor)
   - Where: CP-2A_contrary-evidence.png, crop CP-2A-075-a.png (y 210-940): the paragraph ends at "by 2025-07-11." and goes straight to Limitations, with no Basis line shown
   - Problem: The handoff carries a Basis line (line 46: 10-K page 9; Financial data foundation; calculation D17), but nothing on screen tells the reader where the passage's claims come from. Only two figures carry dotted-underline chips, and the traffic, capex and securitization claims carry no visible source. The house rule puts sources in each paragraph's Basis line.
   - Fix: Render the paragraph's Basis line under it in reader terms (for example "Annual report 2024, p.9; Financial foundation; stress calculation"), with no module codes or calc IDs.
6. **Low · visual** (Auditor, New reader)
   - Where: CP-2A_contrary-evidence.png, crop CP-2A-075-a.png: last Limitations bullet "...conditional on no new recapitalisation." directly above the "Issuer events" heading (about y 690-707 in the crop)
   - Problem: The next section's heading sits flush against the last Limitations bullet with almost no gap, while Contrary evidence and Limitations have generous spacing above them. The reader cannot easily see where the downside prose ends and the timeline begins.
   - Fix: Give the Issuer events heading the same top margin as the other section headings.
7. **Low · visual** (New reader)
   - Where: CP-2A_contrary-evidence.png, crop CP-2A-075-a.png: figures "45.05%" and "40%" in a bold monospace chip within proportional body text
   - Problem: Only two of the paragraph's figures and dates are set as monospace chips. The switch in typeface breaks the reading line, and it implies that only those two numbers are sourced or checked.
   - Fix: Either chip every sourced figure in the paragraph or mark the chips with a subtler style in the body font.

### Downside view

Kind: prose/table · handoff lines 55-70 · verdict **BLOCK**

- Narrative: The lead-in sentence at line 60 says both scenarios cross the watch levels, but the table beneath it shows the moderate case below them. The section also restates the bottom line after Limitations and Sources, which breaks the house reading order, and its threshold and interest-shock units are ambiguous.
- Visual: The section is a prose block and a 6-column summary table, with no chart in this section. The table is readable, but it mixes typefaces, left-aligns its figures, wraps USD amounts and Source cells onto two lines, and sets the Basis chip inline in the labels.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 60: "The summary table shows that leverage crosses the watch levels long before cash flow or interest cover fails, in both analyst scenarios."
   - Problem: The table directly below contradicts this lead-in. The moderate scenario reaches only 7.07x total and 6.53x pro forma net leverage, both under the 7.25x and 7.50x watch levels, and the table's own row (line 68) says only the "Severe case breaches". A reader who trusts the sentence will think a 15% shock already breaches the watch levels. (Promoted from Medium because two personas caught it.)
   - Fix: Say that only the severe scenario crosses the watch levels, and that the moderate scenario keeps leverage below them while cash flow and interest cover stay well clear.
2. **Medium · narrative** (Auditor)
   - Where: line 55 heading "### Downside view", which sits after "### Limitations" (line 48); on the page it comes after Request and Sources (left "On this page" list, shot CP-2A_s-55.png)
   - Problem: A second bottom-line paragraph, which repeats the 23.47%, 45.05%, 8.71x and USD 6,637 million figures, appears after Limitations and Sources. That breaks the house order of bottom line, findings, contrary evidence, then limitations. The reader meets the judgement twice and meets the scenario table only after the caveats.
   - Fix: Fold this paragraph and its summary table into the Bottom line and Key findings at the top, or make it one data block placed before Limitations with no restated judgement.
3. **Medium · narrative** (Saboteur, New Reader)
   - Where: line 64: "EBITDA As Defined decline / cash interest increase | 0 / 0 | 15% / 2.59% | 31% / 5.18%"
   - Problem: "2.59%" and "5.18%" are percent increases in cash interest (one and two percentage points of SOFR). In a column of percentages beside a 15% decline, they read as interest-rate rises. The control column "0 / 0" has no unit. The row puts two different measures into one cell, so the reader cannot tell the size of the rate shock.
   - Fix: Split this into two rows with explicit units, for example "Rate rise (percentage points): 0 / 1 / 2" and "Cash interest increase (% of FY2024 cash interest): 0% / 2.59% / 5.18%".
4. **Medium · narrative** (New Reader)
   - Where: line 57: "crosses the 7.25x incurrence level at a 23.47% decline"; line 68: "breaches the 7.25x and 7.50x watch levels"
   - Problem: The same threshold is called an "incurrence level" in the prose and a "watch level" in the table. Neither term is defined here, and the 7.50x level is never explained. Limitations (line 50) concede these are house definitions, not covenant tests, so "incurrence level" overstates them as a covenant trigger.
   - Fix: Use one term, say once what 7.25x and 7.50x are (house watch levels, not tested covenant ratios), and keep the word "incurrence" only if it is the covenant's own test.
5. **Medium · visual** (Auditor, New Reader)
   - Where: Summary table, shot CP-2A_s-55.png crop x340-1400, y220-850 (scratchpad/tmp/CP-2A-077-a.png)
   - Problem: The ratio rows are set in a bold monospace face, while the USD rows and percentages are in a regular proportional face, all left-aligned. Columns of figures therefore do not line up, and the ratios look emphasised as if they were the key result. USD amounts wrap onto two lines ("USD 3,547.05 / million"), and so do the Source cells ("calculation / D01"), which doubles the row heights. (Promoted from Low because two personas caught it.)
   - Fix: Use one numeric typeface for every figure, right-align the scenario columns, and state units in the header (USD million) so cells stop wrapping.
6. **Low · narrative** (New Reader)
   - Where: lines 64-69 Source column: "calculation D01" ... "calculation D08"; line 57: "gross leverage of 8.71x" vs line 67 "Total debt / EBITDA As Defined | ... | 8.71x"
   - Problem: The Source column cites internal calculation IDs that a reader cannot resolve without opening another page. The prose calls the 8.71x figure "gross leverage" while the table calls it "Total debt / EBITDA As Defined", so the reader has to match the two by hand.
   - Fix: Name the calculation in plain words (for example "Stressed leverage calculation, FY2024 base") and use one label for 8.71x in both places.
7. **Low · narrative** (Saboteur)
   - Where: line 57: "The main monitor is commercial aftermarket sales growth together with any debt-funded distribution. Covenant definitions and hedge maturities would sharpen the timing."
   - Problem: The paragraph runs to nine sentences and ends on an unsized caveat. Meanwhile the 23.47% break point is stated as a firm trigger, although Limitations calls it "a direction, not a test date". The confidence of the headline figure is not visible where the reader takes it in.
   - Fix: Shorten the paragraph and qualify the 23.47% figure where it appears (house definition, timing approximate) instead of in a trailing sentence.
8. **Low · visual** (New Reader)
   - Where: Summary table Measure column, e.g. "EBITDA As Defined decline / cash interest increase Basis", shot CP-2A_s-55.png y≈385-430
   - Problem: The grey "Basis" chip sits inline at the end of each measure label and wraps onto its own line, so it reads as part of the row name and lengthens every row.
   - Fix: Move the Basis control into its own narrow column or icon, out of the label text.

### Map: stress scenario

Kind: map · handoff lines 71-84 · verdict **BLOCK**

- Narrative: The nine rows match the Downside view figures (23.47%, 26.02%, 45.05%, USD 6,637 million, USD 132.74 million), but the section has no lead judgement, uses graph jargon in its headers, and labels an unsupported loss-given-default inference as a test outcome.
- Visual: The drawing on the Maps panel is clipped on the right and drops the terminal node, it breaks node labels mid-word, it overlaps edge labels and it has no legend; the section anchor itself shows only a table that repeats the one under the drawing.

1. **High · visual** (Saboteur, Auditor)
   - Where: Maps panel, 'Stress scenario' drawing; CP-2A_maps.png crop (340,220)-(1440,530), saved as /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2A-078-a.png
   - Problem: The drawing is cut off at the right edge. The last edge label reads only 'Test' and the end node 'Higher loss given default for subordinated notes' (line 83) is not shown at all. The reader therefore never sees the creditor consequence the whole pathway leads to.
   - Fix: Fit the full graph inside the panel width, or wrap it into rows, so that every node, including the terminal loss-given-default node, and every edge label is visible.
2. **Medium · narrative** (Saboteur)
   - Where: line 83: 'A two-point coupon reset on the FY2028 cluster adds USD 132.74 million a year of interest | Test outcome | Higher loss given default for subordinated notes'
   - Problem: The tested result is extra annual interest, but the map labels the step to higher subordinated loss given default as a 'Test outcome'. No calculation measures recovery or loss given default, so an assertion is presented as a computed result.
   - Fix: Label this link as an explanation or judgement, or have the module calculate recovery and state the loss-given-default effect with its basis.
3. **Medium · narrative** (Auditor, New reader)
   - Where: lines 71-73: '### Map: stress scenario' followed directly by '| From | Relationship | Edge type | To | Evidence |'
   - Problem: The section opens straight into a nine-row table with no lead sentence stating what the map shows. The reader has to rebuild the transmission chain row by row.
   - Fix: Open with one sentence that gives the conclusion: leverage watch levels break first, at a 23.47% EBITDA decline, then FY2028 refinancing pressure follows, while free cash flow stays positive.
4. **Medium · narrative** (New reader)
   - Where: line 73 column headers 'From | Relationship | Edge type | To' and type values 'Assumption / Explanation / Test outcome'
   - Problem: 'Edge type', 'From' and 'To' are graph vocabulary, not credit language. 'Test outcome' does not tell a committee member that the row is a break-point calculation.
   - Fix: Rename the columns to reader terms such as 'Driver', 'Effect', 'Link basis' and 'Calculated result', or explain the categories once in the lead sentence.
5. **Medium · visual** (New reader, Auditor)
   - Where: Maps panel drawing, node boxes 'EBITDA As Defined decl ine', 'Free cash flow reducti on', 'Debt service maintaine d', 'FY2028 refinancing pre ssure', 'Debt-funded shareholde r distribution' (crop CP-2A-078-a.png)
   - Problem: Node labels wrap in the middle of words, and the edge labels 'Test outcome' and 'Explanation' sit on top of crossing lines or under node borders. The core nodes are hard to read.
   - Fix: Wrap node text only at word boundaries, widen the boxes, and place edge labels clear of lines and other labels.
6. **Medium · visual** (New reader, Auditor)
   - Where: Maps panel drawing: solid, dashed and dotted connectors (crop CP-2A-078-a.png)
   - Problem: Assumption, explanation and test-outcome links use three different line styles, but there is no legend. Where labels overlap or are clipped, the reader cannot tell which links are analyst assumptions and which are calculated results.
   - Fix: Add a small legend that maps each line style to its edge type, in reader words.
7. **Medium · visual** (New reader, Auditor)
   - Where: CP-2A_s-71.png (section shows only the table) and CP-2A_maps.png (the same edge table appears twice: 'Edges of the map, as stated' under the drawing, and again at 'Map: stress scenario' below Downside view)
   - Problem: At its own anchor, the section titled 'Map' shows no map, only a table. The same nine rows are printed twice on the page in two typographic styles, one with blue underlined monospace Relationship cells and one with plain text, so the reader re-reads identical content.
   - Fix: Show the drawing once at the section anchor with a single edge table, in one consistent body-text style.

### Catalyst view

Kind: prose/table · handoff lines 85-89 · verdict **CONCERNS**

- Narrative: The paragraph leads with its judgement, as the standard requires, and keeps source references out of the sentences. But the "already past" timing conflicts with the 30 September 2024 as-of date, the 2027-notes-in-FY2028 wording reads as a contradiction, and the neutral call for secured creditors has no support.
- Visual: The section has no chart, only one dense prose block. The handoff's Basis line for this paragraph is missing from the page, although Basis chips appear elsewhere on the same page.

1. **High · visual** (Auditor, Saboteur)
   - Where: Line 88 "Basis: Source readiness (CP-0); Financial data foundation (CP-1); Fundamental credit synthesis (CP-2)"; screenshot CP-2A_s-85.png, crop (330,210)-(1440,420) saved as tmp/CP-2A-079-a.png
   - Problem: The handoff has a Basis line for this paragraph, but the page shows no Basis chip under it. Other paragraphs on the same page do show one, such as "The control row s00 reconciles ... Basis". The reader has no way to trace the USD 4,216 million, USD 2,919 million, USD 487 million or USD 6,637 million figures to a source.
   - Fix: Show the paragraph's Basis line as a Basis chip, as the page already does for the control-row sentence, with the module names in reader language.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 87 "The highest-impact dated event is already past: the USD 4,216 million special dividend paid on 2024-10-18"
   - Problem: The page is dated "As of 30 September 2024", so a dividend paid on 18 October 2024 falls after that date and inside the twelve-month window. "Already past" judges it from the filing or run date, not the as-of date, and blurs whether it belongs in forward catalysts or in the pro forma starting point.
   - Fix: Call the dividend an event after the period end that is already reflected in the pro forma liquidity and leverage, and keep "next twelve months" measured from 30 September 2024.
3. **Medium · narrative** (New reader)
   - Where: Line 87 "the 2027 senior subordinated notes mature on 2027-11-15, inside the USD 6,637 million FY2028 cluster that is the refinancing failure point in the downside pathway"
   - Problem: A reader who doesn't know that TDG's fiscal year ends in September will read "2027 notes ... inside the FY2028 cluster" as a contradiction. "Downside pathway" and "refinancing failure point" are internal model terms that the paragraph never defines.
   - Fix: Say that FY2028 runs from October 2027 to September 2028, and describe the cluster as the debt maturities the stress case cannot refinance below 7.25x, in plain words.
4. **Medium · narrative** (Saboteur)
   - Where: Line 87 "neutral for secured creditors over the next twelve months" ... "It has a high probability of renewal and low impact, but it is short-dated secured funding that was fully drawn after year end."
   - Problem: The neutral call for secured creditors gets no support in the paragraph. The securitization sentence rates renewal "high probability" and then gives the reason it may not be, so the judgement cancels itself and the reader can't tell which way it cuts.
   - Fix: Give the reason for the secured-creditor call in one clause, and state the securitization risk once with its direction, for example low impact because it is USD 487 million against USD 2,919 million of pro forma liquidity.
5. **Low · narrative** (New reader)
   - Where: Line 87 "together with dividend equivalents, which took pro forma liquidity to USD 2,919 million"
   - Problem: "Dividend equivalents" is an undefined term, and the paragraph doesn't say whether USD 2,919 million is liquidity after both payments or after the dividend alone.
   - Fix: Define dividend equivalents (payments to holders of equity awards) and give the combined cash outflow next to the resulting liquidity.
6. **Low · visual** (Auditor, New reader)
   - Where: Catalyst view paragraph, screenshot CP-2A_s-85.png crop tmp/CP-2A-079-a.png
   - Problem: The paragraph is a single block of about 150 words and seven sentences, covering the bias, a past event, a near-term maturity, a long-dated maturity and the absence of catalysts. The amounts are set in a monospace, dotted-underline style, while the dates beside them are not, which makes the lines read unevenly.
   - Fix: Split the paragraph into the bias sentence and a short dated list or table (date, event, amount, impact on secured and subordinated creditors), and set the amounts in the body font.

### Calculations

Kind: prose/table · handoff lines 331-363 · verdict **BLOCK**

- Narrative: The section opens with pipeline tooling and gives no judgement. A 24-row table at 10-decimal precision uses undefined scenario codes and points to another module's row IDs, so a committee reader cannot see what the stress arithmetic means.
- Visual: There is no chart. The one visual is the calculations table: its Result column mixes bold monospace and regular type and drops thousands separators, its wide Inputs column leaves empty space, and its 24 rows have no grouping.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 333: "The helper scripts (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py) were not run in this transport. Their checks were done by hand, and all new arithmetic used the calculate tool."
   - Problem: The section opens on pipeline internals: script filenames, "transport" and "calculate tool". None of this is reader language, and it takes the place where the reader should get the section's point.
   - Fix: Remove the tooling sentence, or move it to Limitations in plain words ("figures were checked by hand"), and open with what the calculations show.
2. **Medium · narrative** (Saboteur)
   - Where: Lines 331-362: the section is the 24-row table D01-D24 plus line 362, "The watch-level break points of 23.47% and 26.02% are CP-2 calculations S06 and S09 and are carried, not recomputed."
   - Problem: No sentence says what the arithmetic means. The decision-relevant results are left as raw rows for the reader to find: SC2 leverage 8.71x (D13), SC2 interest cover 2.36x (D15), the 45.05% FCF-zero break (D17) and cash of USD 1,913m after the dividend (D20).
   - Fix: Open with a one- or two-sentence bottom line naming the severe-case leverage and cover and the break points, then give the table as support.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: Line 360: "D24 | Confidence score | E = 8.6 / 10 = 0.86 (86); 0.6 × 86 + 0.4 × 90 = 51.6 + 36 = 87.6; × 0.7 check 61.32 / 87.6 = 0.7 | 61 (Medium)"
   - Problem: The labels SC1, SC2, k, s, E, the 90 input and the 0.7 multiplier are never defined. The confidence score cannot be read without knowing the internal scoring method, and a pipeline self-score sits in the same table as credit metrics.
   - Fix: Define SC1/SC2 by their EBITDA and rate shocks in the row labels, and move the confidence score out of the credit-metrics table or explain its components in words.
4. **Medium · narrative** (Auditor)
   - Where: Line 362: "...are CP-2 calculations S06 and S09 and are carried, not recomputed" (rendered as "Fundamental credit calculations S06 and S09" with code chips)
   - Problem: The reader is pointed to another module's internal row IDs to find where two watch levels come from. "Carried, not recomputed" is pipeline vocabulary, and the reader has to open another page.
   - Fix: State what the 23.47% and 26.02% break points measure, and put their origin in a Basis or Source cell rather than in the sentence.
5. **Medium · narrative** (Saboteur, New reader)
   - Where: Lines 337-359, e.g. line 342: "D06 | SC1 total debt / EBITDA | 25,068 / 3,547.05 | 7.0672812619 | x" and line 345: "0.0488294958 | fraction"
   - Problem: Results are given to 10 decimal places, which is false precision. Ratios are mixed between raw fractions (D09 0.0488) and fractions with percentages (D17 45.05%), so the reader converts units row by row.
   - Fix: Round to the reporting precision (7.07x, 4.9%) and show every ratio in one unit family.
6. **Medium · visual** (Auditor)
   - Where: Calculations table, Result column; CP-2A_s-331.png, crop region x 340-1400, y 520-1100 (scratchpad/tmp/CP-2A-083-a.png)
   - Problem: The Result column mixes two typefaces. D02-D16, D18, D20, D21 and D23 render in bold monospace without thousands separators ("3547.05", "1224.0578"). D01, D17, D19, D22 and D24 render in regular proportional type. The Inputs column uses separators ("3,547.05"), so the same number looks different in adjacent cells.
   - Fix: Render every Result cell in one style, right-aligned, with the same thousands separators as Inputs.
7. **Low · narrative** (Auditor)
   - Where: Line 333: "Inputs are in USD millions for FY2024 from CP-1, which cites the annual filing; the rate sensitivity is from the annual filing, page 73."
   - Problem: The source references (annual filing, page 73) sit in the narrative sentence, which the house standard reserves for Basis lines, Source columns and Sources. On screen "CP-1" also becomes "Financial foundation" in running text.
   - Fix: Keep the unit and period statement in the sentence and move the page 73 citation into the Basis line or a Source column.
8. **Low · visual** (New reader)
   - Where: Calculations table layout, CP-2A_s-331.png region y 520-1410
   - Problem: The Inputs column is very wide, leaving a large empty gap before Result, while Formula labels such as "SC2 reduction check; stressed EBITDA" wrap. The 24 rows fill most of a screen with no grouping between the SC1, SC2 and break-point blocks.
   - Fix: Narrow Inputs, give Formula more width, and add group sub-headers (Moderate stress, Severe stress, Break points) to the table.

### Limitations

Kind: reader passage · handoff lines 48-54 · verdict **CONCERNS**

- Narrative: The section follows the house order and each limitation states which way it biases the result, but two numbers are left ambiguous or watered down: the unnamed 8.71x measure, and the 23.47% break point recast as 'a direction' only here. Internal words like 'house net debt' and 'pathway' leak through to the reader.
- Visual: Plain bullet list at a readable line length with no chart in this section; the main visual defect is that the next section's heading ('Issuer events') sits tight under the last bullet at the same weight, so the section boundary disappears.

1. **Medium · narrative** (Saboteur, New Reader)
   - Where: 1.response.md:51 "That makes the scenario free cash flow and leverage the optimistic end of each scenario's outcome, so the severe-case leverage of 8.71x may be understated."
   - Problem: The 8.71x figure is total (gross) debt / EBITDA As Defined (table line 67). The break points and watch-level breaches use pro forma net leverage (8.04x, line 68), but this bullet does not say which measure it means. The sentence also calls the result 'the optimistic end' and then hedges with 'may be understated', so it is unclear how firmly the reader should discount it.
   - Fix: Name the measure (total debt / EBITDA As Defined, 8.71x, and the net figure if it matters) and state the bias plainly, without the extra hedge.
2. **Medium · narrative** (Saboteur)
   - Where: 1.response.md:50 "so a 23.47% decline to the incurrence watch level could sit earlier or later on the governing tests... it is a direction, not a test date."
   - Problem: The bottom line (line 57) and key findings give the break point to two decimals (23.47%) as a firm threshold. Here the same figure is downgraded to 'a direction' with no indication of how far off the covenant tests might be. A committee reading only the bottom line will take false precision away.
   - Fix: Say in which direction the covenant definitions are likely to move the break point and by roughly how much, or carry the caveat into the bottom line so the precision is not overstated there.
3. **Medium · narrative** (New Reader, Auditor)
   - Where: 1.response.md:50-53 "house net debt", "the governing tests", "the rate accelerator in the pathway", "The pathway therefore cannot show", "break points", "no added mix effect"
   - Problem: 'House net debt', 'pathway', 'governing tests' and 'mix effect' are internal analysis vocabulary. They are not defined anywhere in this section, so a portfolio manager who has not read the method cannot tell what 'house' net debt excludes or what 'the pathway' is.
   - Fix: Use reader terms (e.g. 'our net debt measure (gross debt less cash)', 'this downside analysis', 'the credit agreement's leverage tests', 'a shift toward lower-margin sales').
4. **Medium · visual** (Auditor, New Reader)
   - Where: Screenshot CP-2A_limitations.png, crop CP-2A-076-a.png, region x330-1440, y540-575 (last Limitations bullet into the 'Issuer events' heading)
   - Problem: The next heading, 'Issuer events', sits only about 10px below the last bullet and is the same size and weight as 'Limitations'. It reads as a continuation or sub-item of the Limitations list rather than a new section, and the reader loses the boundary between the module's caveats and the event timeline.
   - Fix: Give the section break the same top margin used above other section headings (or add a divider), so Limitations visibly ends before the timeline begins.
5. **Low · narrative** (New Reader)
   - Where: 1.response.md:50 "This changes how much the first-break conclusion should be trusted as a covenant timing signal: it is a direction, not a test date."
   - Problem: This is a self-referential meta-sentence about trust in the analysis rather than a direct statement of the consequence, and it makes the longest bullet in the section longer still.
   - Fix: Replace it with one direct clause, e.g. 'Treat the 23.47% as indicative of direction, not as the covenant trigger.'
6. **Low · narrative** (Auditor)
   - Where: 1.response.md:52 "The swap, cap and collar notionals and expiry dates were not read, so if hedges roll off before FY2028, the rate accelerator in the pathway is understated."
   - Problem: 'Were not read' describes the process (what the analyst did not open) rather than the evidence gap facing the reader. The bullet also does not say whether hedge data was available in the filing, so the reader cannot tell whether this is a data gap or a scope choice.
   - Fix: State the gap as evidence ('hedge notionals and expiry dates are not covered in this analysis') and say whether the filing discloses them.
7. **Low · visual** (Saboteur)
   - Where: Screenshot CP-2A_limitations.png, crop CP-2A-076-a.png, the Limitations block as a whole
   - Problem: The four caveats are rendered as equal-weight grey-bullet paragraphs, each 3 to 4 lines long, with no lead phrase. A reader skimming cannot see which limitation bears on which conclusion (break-point timing, severe-case leverage, rate risk, FY2028 failure point).
   - Fix: Open each bullet with a short bold lead naming the conclusion it qualifies, matching the bold-lead pattern already used in Key findings.

## Forward credit model (CP-2G)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-2G/e796971da51b4f4a9610b9c3601a09545f65b72b4612b4f5e158d99e6ab39e51/1.response.md`

### Forecast inputs (machine-readable)

Kind: prose/table · handoff lines 97-148 · verdict **BLOCK**

- Narrative: This is a raw JSON data block, not prose, so the judgement-first order does not apply; it still shows unit-less figures, schema keys, internal labels and citations inside sentences to a reader who should never see it in this form.
- Visual: There is no chart; the block renders as one unformatted monospace wall with literal stray backticks and numbers split across lines, so the fence rendering is broken and the section cannot be read.

1. **High · narrative** (Saboteur + New reader (promoted))
   - Where: L103-112: "revenue": {"amount": "7940", "reason": null}, ... "debt": {"amount": "24880", "reason": null}, "cash": {"amount": "6261"
   - Problem: The base figures carry no currency, unit or period (USD million, FY2024, or the 2024-09-30 instant for debt and cash), and the drivers are bare decimals ("0.5256", "0.0259"). A reader has to guess the scale, which breaks the rule that values, periods and units must be exact.
   - Fix: Anything shown to the reader states the currency, unit and period for each base figure, and gives the drivers as percentages with their year.
2. **High · narrative** (Auditor)
   - Where: L101 "schema_version": "cpos-forecast-inputs/1"; L107 "is captured in the tax_wc driver"; heading L97 "Forecast inputs (machine-readable)"
   - Problem: The reader sees pipeline vocabulary: a schema id, snake_case keys (base_drivers, tax_wc_pct_revenue, downside_shock), null and "machine-readable". The house standard bars pipeline language from the reader's page.
   - Fix: Remove the raw schema from the Modules page; if the inputs must appear, show them as a labelled assumptions table in plain words.
3. **High · visual** (Auditor + New reader (promoted))
   - Where: Screenshot CP-2G_s-97.png, section top, approx. y 220-1140 (full-res crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2G-093-a.png); handoff lines 99-147 (```json fence)
   - Problem: The ```json fenced block does not render as a code block. It shows as one reflowed monospace paragraph about 50 lines long, with a literal "``json {" at the start and "} ``" at the end, and line breaks fall inside numbers ("\" 4173", "\"24880 \""). Nobody can read it, and it shows the page's fence handling is broken.
   - Fix: Render the fence as a preformatted block with its original line breaks, or better, leave this machine block off the reader's Modules page and keep it only as data feeding the Forecast page.
4. **Medium · narrative** (Saboteur)
   - Where: L123 "downside_shock": {"ebitda_decline": "0.15", "rate_increase": "0.0259"} vs L142 "rate_increase 0.0259 is CP-2A's proportional cash-interest increase for a one-point rate rise, not a 2.59 percentage-point rate change"
   - Problem: The figure that is easiest to misread ("rate_increase 0.0259" reads as a 2.59-point rate rise) is only corrected in the last lines of the wall of text, far from the value. A committee member skimming the block could take the downside rate shock as 2.59 points.
   - Fix: State the meaning right next to the value, e.g. "cash interest +2.59% (equivalent to a 1-point rate rise)".
5. **Medium · narrative** (Auditor)
   - Where: L115 "organic growth of 16.2% and commercial aftermarket organic growth of 12.0% (annual filing page 45)"; L116 "margin 52.56% (calculation C21) carried forward"; L140 "(CP-1 C48)"
   - Problem: Source references and internal calculation codes (C21, C22, C48, "annual filing page 45") sit inside the rationale sentences rather than in a Basis line or Source column. On screen the C-codes render as small chips mid-sentence.
   - Fix: Move citations and calculation ids into a Source/Basis column and keep the rationale text free of references.
6. **Medium · narrative** (New reader)
   - Where: L142 "Downside shock is CP-2A scenario SC1" (on screen: "Downside scenario SC1"); L107 "Financial foundation prints no working-capital change line"
   - Problem: Internal labels such as "scenario SC1" and module names used as if they were documents ("Financial foundation prints...", "not separable in Financial foundation") assume the reader knows the pipeline. A reader who has not seen the other pages cannot interpret them.
   - Fix: Describe the scenario and the data source in plain words (e.g. "the 15% EBITDA / higher-rate stress", "the reported financials").
7. **Low · narrative** (Saboteur)
   - Where: L115 "organic growth of 16.2%" vs L125 "FY2024 organic growth 16.26% (7,629 over 6,562)"
   - Problem: The same FY2024 organic growth figure appears at two precisions in one block, which makes a careful reader wonder whether they are two different measures.
   - Fix: Use one figure, labelling the printed value and the computed value consistently.

### Analytical appendix — complete canonical registers (part 1 of 2: from 'T2H.1 Source and upstream gate')

Kind: register appendix · handoff lines 149-240 · verdict **BLOCK**

- Narrative: This is a data register, so it owes no judgement-first prose. But two numbers mislead: the downside case doesn't apply the stated SC1 shock, and FY2024 FCF/debt uses a different debt base from later years. Pipeline vocabulary and 8-decimal false precision also make it hard for a committee reader to use.
- Visual: The screenshot covers only the Source, Bridge and Assumption tables (T2H.1–T2H.3, part of the register); the Operating forecast, Debt roll-forward and Credit metrics tables (T2H.4–T2H.6) were judged from the response file alone. The tables render cleanly and readably at 1440 px. The faults are the 'a method step' placeholder headings, a 'Basis' chip on every row label, and mixed value typography.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 198: "A-17 | downside shock SC1 | downside | FY2025–FY2027 | EBITDA -0.15; cash interest +0.0259 ... CP-2A moderate scenario passed to engine on base drivers"; line 221: "FY2025 | downside | 24,880 / 6,261 | 0 (A-15) | 93 | 1,291.27"
   - Problem: A-17 is listed as a downside-case assumption, but the downside rows don't apply it. Downside EBITDA is exactly 7,543 x 0.5156 = 3,889.17, with no 15% cut. Cash interest is the base 1,291.27 (backed out of FCF: 3,889.17 - 921.75 - 156.89 - 1,519.25 = 1,291.27). So the downside coverage of 3.01x and the trough of 3,576 in T2H.6 come from an unshocked case. A committee would read them as stressed figures.
   - Fix: Either apply SC1 in the downside rows, or label A-17 as a separate scenario on base drivers and keep it out of the 'downside' case column, so the reader knows which numbers are stressed.
2. **High · narrative** (Saboteur)
   - Where: line 231: "FY2024 | actual / pro forma | 5.96x / 5.50x pro forma | 3.60x | 7.50%"; line 239: "DEF-2 debt is balance-sheet carrying value."
   - Problem: FY2024 FCF/debt of 7.50% equals 1,880 / 25,068, which is gross principal. On the carrying value of 24,880 named in DEF-2 it is 7.56%. FY2025 onwards uses carrying debt (2,050.36 / 24,787 = 8.27%). So one column mixes two debt bases, which overstates the improvement from FY2024 to FY2025.
   - Fix: Compute every FCF/debt figure on the one debt basis that DEF-2 states, or footnote the FY2024 exception.
3. **High · narrative** (Auditor, New reader)
   - Where: line 155: "CP-0 / tdg-2024-09-30-credit_snapshot-opus-medium / FY2024 | Supplied, pinned sha256 4e5e4b7b | Consumer readiness: CP-2G READY_WITH_LIMITATIONS"; line 198: "passed to engine on base drivers"; line 149 "complete canonical registers"
   - Problem: Pipeline vocabulary reaches the screen: run ids, sha256 pins, 'Consumer readiness', READY_WITH_LIMITATIONS, 'upstream gate', 'engine', 'canonical', and HO-* handoff ids (shown as 'HO-Financial foundation'). It also uses raw snake_case labels (source_id, evidence_id, revenue_growth, analyst_judgment). The house standard forbids this vocabulary, and a portfolio manager cannot read it.
   - Fix: Replace these with plain reader labels (for example 'Prior analysis: financial foundation', 'Analyst judgement', 'Revenue growth'), and drop hashes, run ids and readiness codes from the reader view.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 183: "A-02 | revenue_growth | upside | FY2025–FY2027 | 0.1626 / 0.12 / 0.10"; lines 202-237 (T2H.4–T2H.6 list only base and downside rows)
   - Problem: An upside case is defined (A-02, and 'upside inherits' in A-04/A-10), but no upside forecast, roll-forward or metric rows appear. The reader can't tell whether the upside case was modelled or dropped.
   - Fix: Show the upside rows, or state in the register that upside was defined but not run.
5. **Medium · narrative** (New reader, Saboteur)
   - Where: line 207: "FY2027 | base | 9,998.6832 | 5,255.30788992 | 52.56% | 2,751.79830288 | 207.97261056 | 2,543.82569232"; line 220: "24,603 / 8,552.69546432 | 9,395.69546432"
   - Problem: USD-million forecasts are printed to as many as 8 decimal places. The inputs are rounded judgement rates such as 0.10 and 0.08, so this precision is false. It also makes the tables hard to scan and compare.
   - Fix: Round the reader-facing forecast and roll-forward values to whole USD millions (or one decimal), and keep full precision only in the machine-readable output.
6. **Medium · visual** (Auditor, New reader)
   - Where: Screenshot CP-2G_s-151.png, table headings at y~195, 678, 1405 (displayed): "a method step Source and upstream gate", "a method step Historical-to-base bridge", "a method step Assumption register"; the same text in the left 'On this page' list
   - Problem: Removing the T2H.x code left the placeholder 'a method step' in front of every heading and in the side navigation. It reads as a broken template, and 'upstream gate' stays in the heading.
   - Fix: Render the headings as plain titles (for example 'Sources and inputs', 'Historical-to-base bridge', 'Assumption register') without the placeholder prefix.
7. **Low · narrative** (New reader)
   - Where: line 166: "Organic growth | FY2024 16.2% printed (16.26% computed) | Anchor only | None | Company measure | SRC-10K-FY24, calculation G07"
   - Problem: References to internal calculations (G07, C21, D01 to D23) and definition codes (DEF-1 to DEF-5) need another page to decode. The DEF codes are only explained below the metrics table, after earlier tables have already used them.
   - Fix: Spell out each definition where it is first used, or put a short key above the first table that cites the codes.
8. **Low · visual** (Auditor)
   - Where: Screenshot CP-2G_s-151.png, first column of every row (for example "A-01 Basis", "HO-Source readiness Basis", "Revenue, USD m Basis"), and the value/range column of the Assumption register (y~1765-1975 displayed)
   - Problem: A grey 'Basis' chip is attached to every row label and wraps in narrow cells. The value column also mixes plain text ('0.10 / 0.08 / 0.06') with bold monospace ('0.5256'). Both make the tables noisy and inconsistent.
   - Fix: Show the Basis link once per table or as a quieter icon, use one typeface for all values, and show fractions as percentages.

### Analytical appendix — complete canonical registers (part 2 of 2: from 'T2H.7 Shocks and breakpoints')

Kind: register appendix · handoff lines 241-324 · verdict **BLOCK**

- Narrative: This is a register appendix, so no bottom-line-first order is owed. Its content still misleads in places: omitted flows appear as READY zeros, the upside case and the base-case stress shock have no figures, and one liquidity sentence is garbled. Pipeline vocabulary and raw machine-register headers also leak to the reader.
- Visual: The section has no chart. Its three breakpoint and gap tables render cleanly with Basis chips, but their captions read \"a method step ...\". The drivers register overflows the page width: status is clipped and the source columns sit off-screen. Its value cells wrap to seven lines, so the table runs to several screens.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 269: "Acquisitions, buybacks (316 in Q1 FY2025), option proceeds (245 in FY2024), FX ... Roll-forward closes only because these are set to nil" vs lines 283/286: "acquisitions_disposals | — | BASE | FY2025 | 2025 | 0 | CURRENCY_MM | A-14 | READY"
   - Problem: The gaps register says these flows were omitted and set to nil (one of them, 316 of buybacks, is already known), but the drivers register shows them as 0 with status READY. That presents missing data as a confirmed zero and hides it from the reader.
   - Fix: Mark the omitted flows as not modelled, with a gap status rather than READY, or carry the known 316 buyback, so that missing is never shown as zero.
2. **High · narrative** (Saboteur, New reader)
   - Where: line 247: "Computed by the CP-OS engine; CP-2A static result 6.53x pro forma net" and line 258: "upside | Engine-computed from A-02 | FY2027"
   - Problem: Two rows leave the result to the engine and give no figure: the base-case stress shock and the whole upside trajectory. The reader gets no number to judge. On screen this reads "Computed by the Run activity engine", which is pipeline wording.
   - Fix: Print the computed breakpoint and the upside FY2027 leverage, or state plainly that they are not available and why.
3. **High · visual** (Auditor, New reader)
   - Where: Forecast drivers table, CP-2G_s-241.png, crop CP-2G-095-a.png (x 340-1440, y 1840-2400)
   - Problem: The status column is cut off at "NOT_APPLICA", and the source_id, source_locator and as_of columns are pushed off-screen. The Source column the house standard requires is not visible. Each value cell wraps over seven monospace lines, so 42 near-identical rows run to several screens.
   - Fix: Fit the table to the page width, or allow horizontal scrolling with a visible cue. Collapse the 18 not-applicable division rows into one note, and keep Source visible.
4. **Medium · narrative** (Saboteur)
   - Where: line 249: "Liquidity falls by 487; base FY2025 liquidity still 4,226.36 after repayment would require separate calculation"
   - Problem: The sentence is garbled. It gives a liquidity figure and then says that figure would need a separate calculation, so the reader cannot tell whether 4,226.36 is before or after the 487 repayment.
   - Fix: State one figure with its basis: FY2025 accessible liquidity before and after the 487 repayment, in USD millions.
5. **Medium · narrative** (Auditor, New reader)
   - Where: line 246: "Debt-funded payout route closes; house basis only"; line 266: "tax_wc driver blends taxes"; line 267: "None; logged"; line 251 heading "Trajectory and handoff"
   - Problem: Pipeline vocabulary reaches the reader: "handoff", "logged", the variable name tax_wc and the internal phrase "house basis". The breakpoint tables also name no units: USD millions is never stated in T2H.7 through T2H.9.
   - Fix: Replace the internal terms with reader language, such as "our estimate, not the credit agreement definition", and give a units line under each table.
6. **Medium · narrative** (New reader)
   - Where: lines 278-321: column headers "driver_id | slot_id | case | period_id | fiscal_year | value | unit | assumption_id | status" and values "PERCENT_DECIMAL", "CURRENCY_MM", "NOT_APPLICABLE"
   - Problem: The register is shown in its raw machine-readable form, with snake_case headers and enum codes, and every row shows status and unit codes. A committee member cannot read it, and it adds no judgement.
   - Fix: Show readable headers and units ("USD m", "%"), or move the machine register out of the reader view.
7. **Medium · visual** (Auditor, New reader)
   - Where: Table captions "a method step Shocks and breakpoints", "a method step Trajectory and handoff", "a method step Conflicts and gaps" in CP-2G_s-241.png, and the same entries in the On this page list
   - Problem: The register code (T2H.7) has been swapped for the template phrase "a method step", leaving a lower-case, ungrammatical caption that tells the reader nothing. The drivers table has no caption at all.
   - Fix: Use plain captions such as "Shocks and breakpoints", and give the drivers table a reader title such as "Forecast inputs".
8. **Low · narrative** (Auditor)
   - Where: line 323: "group revenue growth (A-01, A-03) carries the forecast. A dash in slot_id marks a slot the method leaves blank for currency drivers."
   - Problem: The note explains the method's internal slot rules rather than the credit consequence, and the assumption IDs A-01 and A-03 are not defined on screen.
   - Fix: Say in one line that the forecast is at group level only because no segment split was available.

### Forward credit view

Kind: prose/table · handoff lines 56-79 · verdict **BLOCK**

- Narrative: The judgement is clear and comes first, but the section repeats the bottom line after Limitations. It also uses pipeline wording, cites trough figures the table does not contain, and uses an ambiguous \"2x\" for the leverage gap.
- Visual: The table is visible and readable, but its FY2024 column mixes actual and pro forma values with different alignment and fonts, decimal precision varies across rows, and each row carries both a Basis chip and an internal calculation ID.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 77: "It inherits every other base driver and is computed by the orchestrator's engine from the inputs block, not reproduced here. The downside pathway's moderate shock ... is passed to the engine as the downside shock on base drivers. The analyst downside above is a separate, named-driver case."
   - Problem: This is pipeline language ("orchestrator's engine", "inputs block", "passed to the engine") shown to the reader, which breaks the house rule. It also tells the reader that an upside case and a second downside exist, but their numbers are not on this page, so the reader cannot see them and has two different things both called "downside".
   - Fix: Either show the upside and the shock case as table columns with reader-facing names, or cut the paragraph down to one plain sentence saying the scenario results are on the Forecast page.
2. **High · narrative** (Saboteur, New reader)
   - Where: Line 64: "The table shows that both cases keep coverage and liquidity sound, while leverage diverges by about 2x by FY2027, depending on payouts and margin."
   - Problem: The table shows net leverage of 3.05x (base) against 5.02x (downside) in FY2027. That is a gap of about 2 turns, but downside leverage is about 1.65 times base, not double. A reader can take "2x" either way and get the size of the gap wrong.
   - Fix: Give the gap in turns with both endpoints, for example "net leverage of 3.05x base against 5.02x downside in FY2027, about 2 turns apart".
3. **Medium · narrative** (Saboteur, Auditor)
   - Where: Line 58: "The incurrence ceiling of 7.25x is never approached, so the documents impose no discipline."
   - Problem: Limitations (line 53: "covenant definitions are not in the pack"; line 54: "a house-basis distance, not a governing-test headroom") say the covenant test was not measured on its governing definition. This sentence states the conclusion as settled fact. "Incurrence ceiling" is also never defined for a reader who has not seen the credit documents.
   - Fix: Qualify the conclusion inside the sentence, for example "on our leverage basis, not the covenant definition", and say in a few words what the 7.25x incurrence test limits.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 58: "Free cash flow stays above USD 1,519.25 million a year even in the downside, and interest cover stays above 3.01x ... holds it between 5.02x and 5.65x."
   - Problem: The figures that carry the judgement (1,519.25 downside free cash flow, 3.01x cover trough, 5.65x FY2026 peak) are not in the table beside them. The table has no FY2026 column and its only downside column shows 1,641.27, 3.16x and 5.02x. The reader cannot check the troughs, and the table caption calls the cases "sound" from columns that leave out the worst year.
   - Fix: Add downside columns for FY2025 and FY2026 (or a trough row), so every figure in the prose can be found in the table.
5. **Medium · narrative** (Saboteur)
   - Where: Lines 72-73: "| Gross debt / EBITDA (carrying debt) | 5.96x |" next to "| Net debt / EBITDA (carrying debt) | 5.50x pro forma |" and line 71: "| Closing cash, USD m | 1,913 pro forma |"
   - Problem: One FY2024 column mixes actual values (gross leverage, revenue) with pro forma values after the October payout (cash, net leverage, liquidity). The rows in that column are not on the same basis, and the actual year-end cash of USD 6,261 million is hidden. A reader comparing gross with net leverage, or cash with debt, will mix the two bases.
   - Fix: Split the column into "FY2024 actual" and "FY2024 pro forma for October 2024 payout", or give every row on one stated basis.
6. **Medium · narrative** (Auditor, New reader)
   - Where: Lines 56-62, "### Forward credit view", placed after "### Limitations" (line 48) and repeating the Bottom line at line 24 ("net leverage ... to 3.05x by FY2027 ... peaks at 5.65x in FY2026")
   - Problem: The section restates the bottom line and the key findings after Limitations and after the Sources entry in the page navigation. The page therefore gives judgement, then limitations, then judgement again. The module's only summary table also sits below its caveats instead of next to the bottom line.
   - Fix: Move the forecast table up to the Bottom line or Key findings, and drop the repeated prose or cut it to one sentence that introduces the table.
7. **Medium · visual** (Auditor, New reader)
   - Where: Forward credit view table, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2G-091-a.png (crop 340,220-1400,880 of CP-2G_s-56.png)
   - Problem: The FY2024 column is left-aligned while every other numeric column is right-aligned. In the same column, the "pro forma" cells use a proportional font and the others use monospace, so the numbers do not line up. Precision also varies across a row ("8,734" next to "9,998.68"), and two decimals on USD millions suggests more precision than the forecast has.
   - Fix: Right-align all numeric columns in one numeric font, round USD m values to whole millions consistently, and move "pro forma" into the column header or a footnote marker.
8. **Low · visual** (New reader)
   - Where: Forward credit view table rows, CP-2G_s-56.png, Source column ("calculation G09" to "calculation G26") and the "Basis" chip after each Measure label
   - Problem: Each row has a "Basis" chip and also a Source cell, and the Source cell shows an internal calculation ID that a reader cannot interpret from this page. That adds visual noise without telling the reader where the number comes from.
   - Fix: Keep one source pointer per row, labelled in reader terms (for example "Model, base case"), and drop the duplicate chip.

### Module status and QA validation

Kind: prose/table · handoff lines 80-96 · verdict **BLOCK**

- Narrative: This section (lines 80-96) is pipeline QA bookkeeping: field names, filename conventions, script names and the downstream module list. It opens with process status, not a credit judgement on how far to trust the forecast, and its \"Passed\" overstates checks the model graded itself.
- Visual: The table is readable and well spaced, but every row carries the same uninformative \"Basis\" chip, results are not visually differentiated, and the paragraph's own Basis line is not visible under it.

1. **High · narrative** (Auditor + New reader)
   - Where: line 82: "committee_status is Draft Only and qa_status is Passed ... The method's filename convention gives tdg, the module code and the date 20240930. Downstream consumers are the rating-transition, restructuring..."
   - Problem: The paragraph shows raw field names (committee_status, qa_status), the file-naming convention and the house-banned word "consumers" to the reader. None of it bears on credit, and it breaks the no-pipeline-vocabulary rule.
   - Fix: Keep one reader sentence on status and confidence ("Draft; confidence low (58/100) because segment, working-capital and covenant data are missing") and drop the field names, the filename convention and the downstream-module list.
2. **High · narrative** (Saboteur + Auditor)
   - Where: lines 82 and 94-95: "qa_status is Passed, with no QA finding raised" ... "| 9 Markdown contract and helper scripts | Not run | ... unavailable in this transport; checks done by hand |"
   - Problem: A green "Passed, no QA finding" sits beside a self-graded check and five validation scripts that were not run. A committee member may read that as independent validation that did not happen. Row 9 also exposes script filenames and the word "transport".
   - Fix: Say plainly that these are the model's own checks and that the automated validation was not run, then take the script names and transport wording off the page.
3. **Medium · narrative** (Saboteur)
   - Where: line 89: "| 3 Cash and debt roll-forward | Pass with stated omissions | Identity closes with zero residual by construction; omitted flows listed as gaps |"
   - Problem: A residual that is zero "by construction" cannot fail, so "Pass" here proves nothing. The omitted flows that matter (working capital, acquisitions, refinancing) are not named in this row.
   - Fix: Show this as a limitation that names the flows left out of the cash bridge, not as a Pass.
4. **Medium · narrative** (New reader)
   - Where: line 82: "The Confidence Score is 58, Low, counted by hand because the scoring script was not run: E is 81 from 10 material claims ... C is 85 ... and S is 0.7 (partial)"
   - Problem: E, C and S are never defined, and the reader cannot see how 81, 85 and 0.7 give 58. The section opens with process status rather than a judgement on how far to trust the forecast.
   - Fix: Lead with the judgement on how far to trust the forecast, name the three components in plain words with a one-line formula, or show only the score and its main drivers.
5. **Medium · narrative** (New reader)
   - Where: lines 87, 90, 93: "pinned by sha256" ... "DEF-1 to DEF-5 used in every period and case" ... "Working capital left null in the inputs block"
   - Problem: The table notes use internal labels (sha256 pinning, DEF-1..DEF-5, "inputs block") that a reader cannot decode without another page. Several tests (1, 2, 4, 9) are build hygiene, not credit content.
   - Fix: Keep only the tests that change how far a reader trusts the numbers (definitions, perimeter, nulls, downside), written in plain words, and move the build checks to the method steps.
6. **Medium · visual** (Auditor + New reader)
   - Where: QA test table, CP-2G_s-80.png crop x340-1400, y220-880 (/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2G-092-a.png)
   - Problem: Every test name ends in the same grey "Basis" chip, so all nine rows carry an identical label that tells the reader nothing and runs into the test text. No Basis line shows under the paragraph above, so it is unclear where "context; calculation G31" went.
   - Fix: Show the paragraph's Basis line once under the paragraph and drop the repeated per-row chip, or give the table a real Source column.
7. **Low · visual** (Saboteur)
   - Where: Result column of the QA table, same crop
   - Problem: "Pass", "Pass with stated omissions" and "Not run" share the same plain grey text, so the one test that was not run and the one with omissions look no different from the clean passes.
   - Fix: Set a qualified or not-run result apart with a status chip or weight, so it stands out on a quick scan.
8. **Low · visual** (New reader)
   - Where: Paragraph above the table, same crop: the inline code-styled tokens "0.7" and "20240930"
   - Problem: Two values are drawn as underlined monospace tokens in the middle of the prose, which makes a filename date look like a key figure and breaks the reading line.
   - Fix: Show values in body type in prose and keep monospace for genuine code only.

### Calculations

Kind: prose/table · handoff lines 325-364 · verdict **BLOCK**

- Narrative: This is a data/calculation appendix, so it owes no bottom line. As it renders, though, it opens with pipeline tooling notes, lists the multi-year results with no year labels, and leans on internal labels (tax_wc, D20, C12, G-ids). A reader who has not seen the sources cannot audit the forecast from it.
- Visual: The section has no chart, only one wide five-column table that takes up the whole screenshot. The table is readable and does not clip, but it is visually dense. Over-precise unformatted numbers, uneven bolding and a stray \"Basis\" tag in the ID column all slow the eye.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 327: "Helper scripts (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py, credit_metrics.py) were not run in this transport; their arithmetic was done with the calculate tool. Multiplications were performed as division by a calculated reciprocal."
   - Problem: The reader sees the section open on script file names, "transport" and "calculate tool", and in the screenshot (shots2/CP-2G_s-325.png, top of the section) this is the first thing under the heading. This breaks the house ban on pipeline wording, and none of it helps a credit reader.
   - Fix: Open with one reader sentence on what the table is (the arithmetic behind the base and downside forecast, USD millions) and drop the tooling notes from the reader view.
2. **High · narrative** (Saboteur, New reader)
   - Where: Line 339: "G09 | Revenue × (1 + growth), base | 7,940 × 1.10; × 1.08; × 1.06 | 8734; 9432.72 (9,432.72); 9998.6832 (9,998.68)" (same pattern G10–G26)
   - Problem: Rows G09–G26 give three values separated by semicolons with no fiscal year on any of them, and the table has no period column. A reader has to guess that they are FY2025/FY2026/FY2027. The leverage path (G22 "5.40x; 4.98x; 4.68x") cannot be read against time without that guess.
   - Fix: Label each value with its year (or split each scenario into FY2025, FY2026 and FY2027 columns) so every figure carries its period.
3. **Medium · narrative** (Saboteur)
   - Where: Line 350: "G20 | Same, downside | 6,261 + 1,519.2498 − 4,348 − 93; + 1,524.0765 − 2,038 − 92"
   - Problem: The formula says "Same", but the downside takes out a further 2,038 dividend in FY2026 and the base does not (base FY2026 dividends are 0, line 292). Part of the base/downside cash and net-leverage gap (G19–G21, G23) therefore comes from a payout assumption, not from operations, and the label hides this.
   - Fix: Name the extra FY2026 downside dividend in the G20 formula text so that the reader can see the scenarios differ on payout as well as on trading.
4. **Medium · narrative** (New reader, Auditor)
   - Where: Line 338: "G08 | Margin − tax_wc − capex share"; line 357: "pro forma cash 1,913 from CP-2A D20" (rendered "Downside D20"); line 363: "CP-1 calculations C12, C15, C28 and C31"
   - Problem: Internal variable and register labels (tax_wc, D20, C12/C15/C28/C31, and the G-ids used as operands such as "G12 − G13") are reader-facing. A credit committee member cannot resolve them without opening another module.
   - Fix: Replace the internal labels with plain names (for example "tax and working-capital share", "pro forma cash after the FY2025 special dividend") and keep the cross-references in a Source column.
5. **Medium · narrative** (Saboteur)
   - Where: Line 359: "G29 | Downside FY2027 EBITDA at 7.25x net; further decline | 20,320.401528 / 7.25 = 2,802.814"; line 361: "G31 | Confidence score | E: sum of weights 8.1 over 10 claims = 81; (6 × 81 + 4 × 85) / 10 = 82.6; × 0.7"
   - Problem: The 7.25x threshold behind the 30.70% EBITDA-cushion result is not identified here as a covenant, a house limit or anything else. The confidence score formula uses unexplained terms ("E", the 85, the × 0.7 haircut). Those are the two most decision-relevant outputs, and the reader cannot judge them.
   - Fix: Say in the formula cell what 7.25x is (and its basis), and say what each term of the confidence score stands for.
6. **Medium · visual** (New reader, Saboteur)
   - Where: Calculations table, shots2/CP-2G_s-325.png Result column rows G11–G26 (y≈700–1550 in display); e.g. line 341 "5255.30788992 (5,255.31)"
   - Problem: Results are printed to 6–10 decimals without thousands separators, and the rounded figure sits in brackets, sometimes only for some of the three values (G12, G16, G17, G21 have no rounded version). This makes a dense wall of digits, and the rounded figure the reader needs is hard to find.
   - Fix: Show the rounded figure (one or two decimals, with thousands separators) as the primary value and drop the long-precision figure or move it out of the reader table.
7. **Low · narrative** (Saboteur)
   - Where: Line 358: "Base 8,552.69546432 − 6,637; downside 6,637 − 4,282.598472 | Base surplus 1915.69546432 (1,915.70); downside shortfall 2354.401528"
   - Problem: The subtraction order reverses between the scenarios so that both results print as positive, and only the words surplus/shortfall carry the sign. G07 also shows "16.26% growth; printed 16.2%" and leaves the difference unexplained.
   - Fix: Use one sign convention (a negative value for a shortfall) and say in one clause why the printed 16.2% differs.
8. **Low · visual** (Auditor)
   - Where: Calculations table, crop scratchpad/tmp/CP-2G-096-a.png: stray "Basis" label under ID G07 and G27; bold applied only to 22315, 970, 431, 188
   - Problem: In the ID column a "Basis" tag appears under two IDs with no explanation. Bold falls only on the single-integer results, which suggests these four results are more important when they are not.
   - Fix: Remove the stray Basis tag from the ID cell (or explain it) and style all results the same way.

### Sources

Kind: prose/table · handoff lines 5-19 · verdict **BLOCK**

- Narrative: The Sources section shows the reference lists, but its prose leaks pipeline language ("producers", "re-anchored", "handoff", "named by the method"). It also does not say why it excluded the Q1 FY2025 filing or the Fundamental credit input, both of which matter to a forward view.
- Visual: The section is two bordered tables and a note, with no chart. The layout is clean, but most of the width goes to sha256 hashes and a raw file name that wraps, while the useful 'Use in this module' column is squeezed.

1. **High · narrative** (Auditor, New reader)
   - Where: line 18: "CP-1B, CP-2 and CP-2E are advisory or named by the method but were not supplied as producers to this module, so they are unavailable here" (rendered with plain names)
   - Problem: The reader sees pipeline vocabulary ("producers", "this module", "named by the method", "supplied"), which the house standard bans from reader language. It also hides the credit point: this forward model was built without the Fundamental credit view, Earnings changes, or Rates, FX & hedging.
   - Fix: In plain words, say which analyses this forecast did not draw on and what that leaves out (for example, no rate-sensitivity input), with no process wording.
2. **Medium · narrative** (Saboteur)
   - Where: line 18: "The Q2 and Q3 FY2024 quarterly filings, the Q1 FY2025 quarterly filing and the PDF annual report were not relied on."
   - Problem: The section says a post-period filing (Q1 FY2025) was available but not used, and gives no reason and no consequence. A committee cannot tell whether the FY2025 base case ignores actuals that could already confirm or refute it.
   - Fix: Give the reason in one clause (for example, it is outside the as-of date) and say whether leaving it out affects the FY2025 figures.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 9: "all other figures re-anchored through CP-1 with its page citations"; line 12 header "Supplied handoff"; line 10 "context ... Run settings only ... forecast assumptions blank"
   - Problem: The reader sees pipeline terms the standard names as non-reader language: "re-anchored", "handoff" (as a column header), and a source called "context" that is really run settings. A source row that is "not issuer evidence" should not be in an evidence table at all.
   - Fix: Use plain labels such as "Taken from the Financial foundation with its page references" and "Analysis drawn on", and drop the run-settings row or move it to a note.
4. **Medium · visual** (New reader, Auditor (promoted from Low))
   - Where: Sources and Supplied handoff tables, sha256 columns, CP-2G_s-5.png crop y≈220-720 (tmp/CP-2G-086-a.png)
   - Problem: Two of the three table columns are 64-character hex hashes. They take most of the width and mean nothing to a portfolio manager, while the useful 'Use in this module' column is squeezed into a narrow wrap. The hash check in the ruling covers only sentences, so these tables get past it.
   - Fix: Hide the hashes behind the inspector or a details link, and give the source name and its use the width.
5. **Low · narrative** (Auditor)
   - Where: Page order in On this page: "Limitations, Request, Sources, Forward credit view, Module status and QA validation..."
   - Problem: Sources comes in the middle of the module page, before the main forward-credit table and QA material, so the evidence list breaks the reading flow. It is not the closing reference block the reader expects.
   - Fix: Put Sources at the end of the module page, after the analytical sections.
6. **Low · visual** (New reader)
   - Where: Source cell "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl Basis", CP-2G_s-5.png crop (tmp/CP-2G-086-a.png) top-left
   - Problem: The only issuer document is shown as a raw stored file name that breaks across four lines mid-token. A stray "Basis" chip under it looks like part of the file name.
   - Fix: Show a readable document title (TransDigm 10-K, FY ended 30 Sep 2024) and keep the stored file name in the inspector, as the ruling allows.
7. **Low · visual** (Saboteur)
   - Where: Supplied handoff table rows "Financial data foundation | Financial foundation", "Downside pathway | Downside", "Source readiness | Source readiness"
   - Problem: The two name columns repeat each other with slightly different wording, so the same input appears under two names on one row. Neither name matches the navigator label exactly in every case.
   - Fix: Use one column with the module's navigator name.

### Bottom line

Kind: reader passage · handoff lines 22-29 · verdict **CONCERNS**

- Narrative: The bottom line puts the judgement first and its arithmetic holds (8,552.70 - 6,637 = 1,915.70; 6,637 - 4,282.60 = 2,354.40). It presents the no-payout base case and the 3.01x cover floor without the caveats its own Limitations attach, and it uses covenant terms the reader cannot decode on this page.
- Visual: The section has no chart. It renders as two paragraphs set entirely in bold display type with monospace figure chips, and neither paragraph shows its Basis line.

1. **High · narrative** (Saboteur, New reader)
   - Where: Line 24: "In the base case, net leverage on carrying debt goes from 5.50x pro forma for the October 2024 dividend to 3.05x by FY2027."
   - Problem: The bottom line calls 3.05x the "base case" and does not say it assumes no payouts at all. The module's own Limitations (line 52) call this figure "an upper bound on deleveraging, not a central expectation", and Key findings (line 34) say a recurring USD 2,038 million dividend is "the more likely policy". A committee reader takes "base case" to mean the expected path and will anchor on 3.05x.
   - Fix: In the same sentence, say the base case assumes no further distributions and is the best-case deleveraging path, not the expected one, or lead with the policy-adjusted leverage instead.
2. **Medium · narrative** (Saboteur)
   - Where: Line 24: "net leverage peaks at 5.65x in FY2026, with interest cover never below 3.01x."
   - Problem: The interest-cover floor is stated flatly. Limitations (line 51) say coverage in every case is "the optimistic end of the range" because FY2024 interest was net of interest income on a large cash balance. The bottom line therefore overstates how firm the 3.01x floor is.
   - Fix: Qualify the 3.01x floor in the bottom line as optimistic, for example "at least 3.01x on FY2024 net interest, likely lower".
3. **Medium · narrative** (New reader)
   - Where: Line 27: "Neither case crosses the 7.25x incurrence level inside the horizon, so the documented debt-funded payout route stays open throughout."
   - Problem: The sentence does not say which instrument the "7.25x incurrence level" belongs to, what "the documented debt-funded payout route" is, or that it is not a maintenance covenant. A reader who has not read the indentures cannot tell why staying below 7.25x is bad for creditors without reading the Key findings.
   - Fix: Name the test in plain words, for example "the debt agreements let TransDigm borrow to pay dividends while net leverage stays below 7.25x", so the creditor-adverse point makes sense on its own.
4. **Medium · visual** (Auditor)
   - Where: Screenshot CP-2G_bottom-line.png, bottom-line block, roughly x 296-840, y 190-700 (display scale): no Basis line appears under either paragraph (handoff lines 25 and 28)
   - Problem: The house standard puts source references in each paragraph's Basis line, but neither bottom-line paragraph shows one, so its figures (5.50x, 5.65x, USD 2,354.40 million) have no visible source trace. The handoff Basis lines also carry module codes ("Financial data foundation (CP-1); Downside pathway (CP-2A)"), so they would break the no-CP-code rule if shown verbatim.
   - Fix: Render each paragraph's Basis line beneath it in small type, with the module codes replaced by reader names and calculation IDs linked to the Evidence page.
5. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-2G_bottom-line.png, the two bottom-line paragraphs set at about 22 px bold display size, roughly y 190-700 (display scale)
   - Problem: About 150 words (handoff lines 24 and 27) are set entirely in large bold headline type. The page becomes a wall of emphasis in which nothing stands out, and the key judgement sentence ("the trajectory is set by financial policy, not by operations") carries no more weight than the figures around it.
   - Fix: Set only the opening judgement sentence in display type and the rest of the bottom line in regular body weight, as in the VMO2 reference.
6. **Low · visual** (Auditor)
   - Where: Screenshot CP-2G_bottom-line.png, monospace dotted-underline figure chips inside the bold headline, e.g. "USD 2,354.40 million" and "USD 1,915.70 million" around y 600-690 (display scale)
   - Problem: Monospace chips in a proportional bold display face make the lines ragged and force breaks before the chips ("with / USD 1,915.70 million to spare"). The two-decimal millions also suggest more precision than a judgement-driven forecast supports.
   - Fix: In the headline, set figures in the running typeface with a lighter underline and round them to the nearest USD million.

### Key findings

Kind: reader passage · handoff lines 30-42 · verdict **CONCERNS**

- Narrative: The findings are arithmetically consistent (I re-checked 6,637 - 4,282.60 = 2,354.40; 8,552.70 - 6,637 = 1,915.70; 4,348 / 2,050.36 is about 2.1x), but the judgement is buried. The 7.25x headroom claim is undercut by its own limitation, and gross and net leverage are mixed across adjacent bullets.
- Visual: The section has no chart. It is a five-bullet list with bold lead sentences that reads cleanly in width and spacing, but monospace number chips crowd the text and are applied inconsistently against Limitations, and no Basis lines show on screen.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 36: "Even the downside leaves the 7.25x incurrence level unbreached... FY2027 EBITDA As Defined would have to fall a further 30.70%... the covenant package is unlikely to force discipline before FY2028."
   - Problem: The finding presents 7.25x and the 30.70% cushion as covenant headroom, but Limitations (line 54) says the figure is "a house-basis distance, not a governing-test headroom" and that covenant definitions are not available. The caveat cancels the claim, and it sits two sections below where the reader will not see it. An incurrence test also never forces discipline on its own, so the closing sentence misdescribes how the protection works.
   - Fix: State in the bullet itself that the 7.25x comparison uses the model's own EBITDA and carrying debt, not the covenant definition, and that an incurrence test only blocks new debt or payouts. Do not imply a maintenance-style discipline.
2. **Medium · narrative** (Saboteur)
   - Where: line 32: "The base-case deleveraging is real arithmetic, but it should not be read as a forecast of policy."
   - Problem: The first finding a committee member reads disowns the headline base case (3.05x net) without saying which path the analyst expects. The judgement only arrives indirectly in the next bullet ("recurrence is the more likely policy") and in Limitations ("an upper bound on deleveraging").
   - Fix: Lead with the expected outcome (leverage likely held near 5.5x if payouts recur) and give the 3.05x base case as the no-payout upper bound.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: line 38: "must be raised in the market at the leverage the downside leaves, which is 6.08x gross." vs line 36: "Net leverage peaks at 5.65x in FY2026"
   - Problem: Adjacent bullets switch between gross and net leverage. Within one section the reader sees 5.96x to 4.68x gross, 3.05x net, 5.65x net and 6.08x gross with no year or case alignment. A reader can take 6.08x as contradicting the stated 5.65x peak.
   - Fix: Name the measure (gross or net), case and year for every leverage figure, or pair gross and net consistently, so a peak claim cannot be read against a higher number.
4. **Medium · narrative** (New reader)
   - Where: line 32: "Revenue growth of 10%, 8% and 6% at the FY2024 margin of 52.56%"; line 32: "Management gave no guidance in the pack"
   - Problem: "The FY2024 margin" does not say which margin (52.56% is an EBITDA As Defined margin). "In the pack" is internal workflow wording. Undefined terms like "EBITDA As Defined" (line 36) and "carrying debt" (line 32) are left for the reader to decode.
   - Fix: Say "EBITDA As Defined margin of 52.56%" and "in the filings reviewed", and gloss EBITDA As Defined and carrying debt once on first use.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-2G_key-findings.png, Key findings block, roughly y 220-835 (display coordinates)
   - Problem: Every figure is set as an underlined monospace chip: up to eight per bullet, against proportional body text. The paragraphs read as a mottled wall in which the bold lead sentence and the key numbers compete. Limitations directly below shows the same kind of figures (3.05x, 30.70%, 7.25x) as plain text, so the treatment is inconsistent within one page.
   - Fix: Use a lighter number treatment (proportional tabular figures with a subtle hover underline) applied the same way across Key findings and Limitations.
6. **Low · narrative** (New reader)
   - Where: line 34: "In FY2025 the declared USD 4,348 million dividend and dividend equivalents absorb more than twice the base-case free cash flow... A debt-funded payout of the same size would leave net leverage unchanged but raise gross debt"
   - Problem: Each bullet packs four to five sentences and six to eight figures. The last sentence is a separate point (the effect of a debt-funded payout) that weakens the bullet's single message.
   - Fix: Keep each bullet to its headline claim plus two or three supporting figures, and move the secondary mechanics to a sentence of their own or to Limitations.
7. **Low · visual** (Auditor)
   - Where: CP-2G_key-findings.png, Key findings bullets, roughly y 220-835; handoff lines 33, 35, 37, 39, 41 (Basis lines)
   - Problem: No Basis line shows under any bullet on screen, although the handoff carries one per bullet. A reader cannot see where a finding comes from without hovering a chip, which runs against the rule that sources live in each paragraph's Basis line.
   - Fix: Show each bullet's Basis as a small muted line, or a fold row, under the bullet, using the reader-facing module names.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 43-47 · verdict **CONCERNS**

- Narrative: The section is a single dense paragraph. Its judgement (leverage likely stays near 5.5x) is buried mid-paragraph behind a counter-argument that mostly restates the base case. Several triggers and facts lack figures or plain explanation.
- Visual: There is no chart in this section, only one prose block. It reads cleanly, but figure highlighting is inconsistent, the paragraph's Basis line is not visible on screen, and its text column is narrower than later sections on the page.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 45: "The opposite case is stronger on the evidence." ... "The view would harden on any new special dividend that exceeds that year's free cash flow"
   - Problem: The section's judgement, that leverage is more likely to stay high than fall faster, sits as the eighth sentence of a single 190-word paragraph. "Opposite case" and "harden" do not say which direction they mean, so a reader skimming the opening could take away the counter-argument (faster deleveraging) as the module's view.
   - Fix: Open with the judgement in plain direction words (e.g. leverage is more likely to stay near 5.5x than fall to 3x), then give the counter-argument, and name the direction each trigger moves the view.
2. **Medium · narrative** (Saboteur)
   - Where: line 45: "A business converting USD 2,050.36 million of free cash flow in the first forecast year could retire the FY2028 cluster from cash if management chose to."
   - Problem: Placed next to one year's free cash flow, the claim suggests that a single year retires the USD 6,637 million FY2028 cluster. It only works on three years of retained cash, which is what the base case already assumes (line 27: covered with USD 1,915.70 million to spare). The counter-argument therefore restates the base case instead of showing that the base case understates deleveraging.
   - Fix: Show the cumulative retained cash against the USD 6,637 million cluster, and say what the counter-case adds beyond the base case (e.g. faster growth or prepayment).
3. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 45: "defence is a large share of sales, which partly hedges a commercial shock" ... "none of the buybacks reported after the period"
   - Problem: Two facts the argument rests on have no figure, unit or period: the defence share of sales and the size of the post-period buybacks. The reader cannot weigh the hedge or the extra cash use against the USD 2,347 million of acquisitions quoted beside them.
   - Fix: Give the defence share as a percentage of FY2024 sales and the buyback amount and date, or mark each one as not quantified in the pack.
4. **Medium · narrative** (New reader)
   - Where: line 45: "early refinancing of the 2027 subordinated notes without upsizing" ... "on no extension of the securitization by 2025-07-11"
   - Problem: The passage does not say what the securitization facility is, its size, or why its 2025-07-11 expiry matters. It also does not explain how calendar-2027 notes relate to the "FY2028 cluster". A reader who has not read the sources has to look elsewhere to see why these are triggers.
   - Fix: Add a short clause for each trigger: the facility size and what an expiry would do to liquidity, and that the 2027 notes fall in the FY2028 maturity cluster, with dates written in reader style.
5. **Medium · narrative** (New reader, Auditor)
   - Where: line 45: whole paragraph, "The strongest counter-argument is ... by 2025-07-11."
   - Problem: The counter-argument, the evidence for it, three triggers that would move the view toward it, the opposing case, and three triggers that would harden the view are all in one unbroken block. The two lists of triggers are buried in running prose and are hard to find again.
   - Fix: Split it into a short counter-argument paragraph and a judgement paragraph, then list the triggers in two short lists ("would ease the view" and "would harden the view").
6. **Low · visual** (Auditor)
   - Where: screenshot CP-2G_contrary-evidence.png, region x 330-1100, y 210-580 (crop CP-2G-089-a.png)
   - Problem: Only some figures get the monospace, dotted-underline style. 16.2%, USD 2,050.36 million, USD 2,347 million and 5.50x are marked, but "2027", "FY2024" and "2025-07-11" are not. The heavy monospace also breaks the rhythm of the proportional prose.
   - Fix: Use one consistent, lighter figure style (e.g. tabular proportional numerals with the underline only), applied to every value the reader can trace.
7. **Low · visual** (Auditor, New reader)
   - Where: screenshot CP-2G_contrary-evidence.png: section block about 540 px wide (y 190-460 at display scale) compared with the full-width Request and Forward credit view blocks lower down the page
   - Problem: The paragraph's Basis line (handoff line 46) does not appear under the passage on screen, so the reader cannot see where the claims come from. The text column is also narrower than the sections further down the same page, so the measure changes from one section to the next.
   - Fix: Show the Basis line (or a visible Basis chip) under the paragraph, as in the tables, and keep one text width for all prose sections on the module page.

### Gaps

Kind: prose/table · handoff lines 365-378 · verdict **BLOCK**

- Narrative: The Gaps table names real limitations, but pipeline wording (handoffs, helper scripts, operand/driver labels, module-directed actions) and the missing bias direction or materiality leave a credit reader unable to tell which gaps change the leverage, liquidity and covenant view.
- Visual: The table is legible, with no clipping or overlap, but the Source column shows doubled labels such as \"Financial data foundation (Financial foundation)\" and a bare \"context\", and the rows have no materiality cue. Not verified: no other viewport widths or the VMO2 reference screenshots were checked, and I did not check whether the renderer's code-to-name substitution causes the doubled source labels.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: L376 "CP-2 and CP-1B handoffs not supplied | No integrated business-driver or earnings-delta input | None for snapshot | context"; L377 "Helper scripts not run | Confidence and completeness counted by hand"; L372 "wc operand null; blended in tax_wc driver"; L370 "Facilities block null"
   - Problem: Pipeline vocabulary reaches the page. The screenshot still shows "handoffs not supplied", "Helper scripts not run", "wc operand null; blended in tax_wc driver" and "Facilities block null", which breaks the rule against handoff, operand and driver jargon. A portfolio manager cannot tell what is missing from the credit view.
   - Fix: Restate each row in credit terms, e.g. working capital is not modelled separately and is folded into the tax assumption, or interest uses one blended rate because facility coupons and spreads were not extracted, and drop the tooling row or recast it as a limit on the confidence score.
2. **Medium · narrative** (Saboteur)
   - Where: L375 "Post-period buybacks and securitization draw not modelled | Cash and debt paths omit known post-period flows | Next run with Q1 FY2025 actuals"
   - Problem: The row does not say which way the omission moves the numbers or by roughly how much. Buybacks lower cash and a securitization draw adds debt, so net leverage and the base surplus over FY2028 maturities (1,915.70, L358) are both flattered. A committee reading the surplus has no warning of that bias.
   - Fix: State the direction of the bias (net leverage understated, liquidity overstated) and the order of magnitude if the filings give it, and name the affected metrics.
3. **Medium · narrative** (Saboteur + New reader (promoted))
   - Where: L365-377 Gaps table as a whole (9 rows, no lead sentence)
   - Problem: The judgement is buried. The table lists nine gaps with equal weight and no sentence on which ones actually threaten the forecast's conclusion. Missing guidance (every driver is a judgment) and the house-basis breakpoints sit at the same level as tooling notes.
   - Fix: Add a one-line bottom line above the table naming the one or two gaps that matter for the leverage and covenant view, and order the rows by materiality.
4. **Medium · narrative** (New reader)
   - Where: L373 "Executed credit documents absent [Insufficient Information] | Breakpoints on house basis | Supply credit agreement"
   - Problem: "Breakpoints on house basis" is undefined. The reader cannot tell that the covenant distances (7.25x incurrence, 7.50x springing) were measured on the analyst's own definitions rather than the credit agreement's, or that headroom could differ.
   - Fix: Say in plain words that covenant headroom uses the analyst's leverage definition, not the agreement's, so the reported distance to 7.25x and 7.50x may differ.
5. **Medium · narrative** (Auditor)
   - Where: L370 "CP-1 to print coupons and spreads"; L371 "CP-1 to publish allocation"; L372 "CP-1 to extract cash flow working-capital lines"
   - Problem: The Action column gives instructions to internal modules, rendered as "Financial foundation to print coupons and spreads". These are workflow tasks, not actions a credit reader can take or weigh.
   - Fix: Phrase each action as the evidence that would close the gap, e.g. "facility coupons and spreads from the credit agreement", not as a module instruction.
6. **Medium · visual** (Auditor + New reader (promoted))
   - Where: Screenshot CP-2G_s-365.png, Gaps table Source column (crop CP-2G-097-a.png, rows 2-4 and 7-9): "Financial data foundation (Financial foundation)", "Downside pathway (Downside)", "context"
   - Problem: The renderer's substitution of names for module codes produces doubled labels such as "Financial data foundation (Financial foundation)". Rows 8-9 show a bare lowercase "context", which names no source at all. The Source column looks broken and wraps for no reason.
   - Fix: Show one reader-facing source name per cell, matching the left-nav label, and replace "context" with the real basis or leave it as an explicit dash.
7. **Low · narrative** (New reader)
   - Where: L369 "Management guidance absent [Insufficient Information]"; L373 "Executed credit documents absent [Insufficient Information]"
   - Problem: The bracketed "[Insufficient Information]" tag is an internal classification label. It repeats what "absent" already says.
   - Fix: Drop the bracket tag or turn it into a consistent visual chip used across the library.
8. **Low · visual** (Saboteur)
   - Where: Screenshot CP-2G_s-365.png, Gaps table header row and rows 1-9 (approx. y 1690-2215 at full resolution)
   - Problem: The table renders cleanly with readable row spacing and no clipping, but it carries no severity or materiality marker. Gaps that move the credit view look identical to tooling notes, so the eye has no entry point.
   - Fix: Add a small materiality chip or emphasis on the rows that affect leverage, liquidity or covenant conclusions.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 379-382 · verdict **BLOCK**

- Narrative: The section is run plumbing. The scope sentence is clear apart from a doubled label and a raw pathway token, but the Next module paragraph is orchestration routing written in pipeline vocabulary, and it contradicts the sidebar's covenant status.
- Visual: The section has no chart, map or timeline, only two short prose blocks. They are legible and not clipped, but they are styled the same as the analysis, so the reader cannot tell they are administrative.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 381: "CP-2H and CP-4C (not requested in this run) and CP-MODEL are the standing downstream consumers of this forecast." Rendered as "Ratings & triggers and Recovery & fulcrum (not requested in this run) and Cash flow model are the standing downstream consumers of this forecast." (CP-2G_s-379.png, y about 2280-2330 at full resolution)
   - Problem: The renderer swaps the module codes for names, but the sentence is still pipeline orchestration language. The house standard bans "consumer" and "not requested in this run" as reader language. It also names two modules that have no page in the sidebar, so the reader cannot follow them.
   - Fix: Either drop the routing sentence from the reader view, or turn it into plain reader language about which open questions remain and where the answers will appear.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 381: "CP-4 should run next and recompute the 7.25x incurrence distance and the 7.50x springing test on governing definitions against the downside FY2026 peak and FY2027 path."
   - Problem: The reader is told Legal & covenants "should run next", but the sidebar on the same page already lists Legal & covenants with a "Not assessable" chip. The reader could take this as covenant headroom that will be confirmed, when the covenant module in this run could not assess it.
   - Fix: State that covenant headroom is unconfirmed in this run because the credit agreement was not supplied, and match the Legal & covenants status shown in the sidebar.
3. **Medium · narrative** (New reader)
   - Where: Line 381: "recompute the 7.25x incurrence distance and the 7.50x springing test on governing definitions"
   - Problem: The two thresholds do not name the ratio (net or gross, secured or total, which EBITDA definition) or the instrument they come from. "Governing definitions" and "incurrence distance" are shorthand that a reader who has not read the filings cannot decode.
   - Fix: Name the ratio, the definition basis and the instrument behind each threshold once, in plain words.
4. **Medium · narrative** (Auditor, Saboteur)
   - Where: Line 3: "CP-2G forward credit model for TransDigm Group Incorporated (TDG), as of 2024-09-30, on the credit_snapshot pathway." Rendered as "Forward credit model forward credit model for TransDigm..." (CP-2G_s-1.png, crop at full resolution x 340-1400, y 220-330)
   - Problem: Substituting the code for its name produces a doubled phrase on screen. The raw pipeline token "credit_snapshot pathway" also reaches the reader. The opening line looks machine-generated and undermines trust in the page.
   - Fix: Render a single clean label (for example "Forward credit model for TransDigm ... as of 30 September 2024, credit snapshot") with no raw identifier.
5. **Low · visual** (New reader)
   - Where: Request block (CP-2G_s-1.png, y about 230-310) and Next module block (CP-2G_s-379.png, y about 2240-2330)
   - Problem: Both run-plumbing blocks are set in the same heading weight and body text as the analytical sections. Request sits between Limitations and Forward credit view in the page order, so nothing tells the reader it is administrative rather than analysis.
   - Fix: Visually de-emphasise or collapse the scope/request and routing blocks (smaller muted type or a labelled note style) so the analysis reads as the main content.

### Limitations

Kind: reader passage · handoff lines 48-55 · verdict **CONCERNS**

- Narrative: The limitations are substantive and in the right register, but four of the five bullets leave their effect unquantified or rest on pipeline and internal terms. The coverage caveat undercuts a bottom-line floor without saying by how much.
- Visual: The section has no chart. It renders as a plain five-bullet list in a narrow column with no lead phrases, and its numbers are styled differently from the rest of the page. It is readable and nothing is clipped.

1. **Medium · narrative** (Saboteur, Auditor)
   - Where: L51: "so FY2025 net interest may be higher after the October 2024 payout. Coverage and free cash flow in every case are therefore the optimistic end of the range." (against L24 "interest cover never below 3.01x")
   - Problem: The limitation says every coverage and free cash flow figure is the optimistic end of the range, but it gives no size. The bottom line still states "never below 3.01x" as a floor with no qualification. A committee reading the bottom line takes 3.01x as a floor that this bullet quietly withdraws.
   - Fix: Put a number on the bias, for example the FY2024 interest income or an implied gross-interest coverage, or mark the 3.01x in the bottom line as a ceiling on net-interest basis.
2. **Medium · narrative** (New reader, Auditor)
   - Where: L50: "because the pack holds no management guidance"; L53: "covenant definitions are not in the pack"; L54: "the financial foundation's EBITDA As Defined ... a house-basis distance, not a governing-test headroom"
   - Problem: "the pack", "the financial foundation" (a module name), "house-basis" and "governing-test headroom" are pipeline and internal terms. A portfolio manager who has not seen the workflow does not know them. The house rule says they are not reader language.
   - Fix: Say "the filings reviewed", "the company's reported EBITDA As Defined" and "our measure, not the credit agreement's definition".
3. **Medium · narrative** (New reader, Saboteur)
   - Where: L53: "Revolver usage above 40% springs the 7.50x test, and covenant definitions are not in the pack, so the liquidity troughs are not tested against any borrowing condition."
   - Problem: The 7.50x springing test is introduced in a limitation without saying what it measures, which facility it governs or the USD threshold (40% = USD 364m per T2H.8). The October securitization draw is mentioned without its amount (USD 163m). Without these the reader cannot judge whether the USD 3,576m liquidity trough is at risk.
   - Fix: Name the test (for example, first-lien leverage maintenance test on the revolver), give the USD 364m trigger and the USD 163m securitization draw, and state whether any modelled case reaches that usage.
4. **Medium · narrative** (Saboteur)
   - Where: L50: "A 1% change in growth moves FY2027 EBITDA by roughly that share of revenue times the margin."
   - Problem: This sensitivity is a formula, not a figure. It does not say whether "1%" is a percentage point per year or cumulative, and it gives no USD or leverage effect. The "low precision" warning therefore has no magnitude.
   - Fix: State the result, for example "each 1 percentage point of annual growth moves FY2027 EBITDA by about USD X m and net leverage by about Y x".
5. **Medium · narrative** (Auditor)
   - Where: Lines 48-55 "### Limitations", followed at L56 by "### Forward credit view" with the summary table and new conclusions
   - Problem: Limitations is not the last reader passage. The judgement-bearing Forward credit view and its metrics table come after it on the page, which breaks the house order (bottom line, key findings, contrary evidence, limitations). The bullets also carry factual claims (the 40% / 7.50x springing test, interest net of interest income) with no Basis line.
   - Fix: Move the Forward credit view and its table up into the findings before Limitations, and give the factual limitation claims a Basis line.
6. **Low · visual** (New reader)
   - Where: Limitations bullet list, CP-2G_limitations.png region x330-1440, y210-750 (crop CP-2G-090-a.png)
   - Problem: Five bullets of three to four lines each, all the same weight and with no bold lead phrase (unlike Key findings). The list is set in a column about 650 px wide that leaves roughly 40% of the content width empty, so the reader cannot scan which limitation matters most.
   - Fix: Give each bullet a short bold lead, as Key findings does (for example "Interest cost understated"), and use the same text width as the surrounding sections.
7. **Low · visual** (Auditor)
   - Where: Limitations bullets in CP-2G_limitations.png (3.05x, 7.50x, 30.70%, 7.25x) compared with the Forward credit view below (monospace chips on 3.05x, 7.25x, 5.65x)
   - Problem: Figures in Limitations are plain text, while the same figures a few hundred pixels lower are styled as underlined monospace chips. The inconsistency makes the same numbers look like different kinds of value.
   - Fix: Style numeric values the same way throughout the module page.

## Rates, FX & hedging (CP-2E)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-2E/6e6adc1d42a32ae08e9e064b54d07035726f3ff441f0f5a6234ecac3c01cda6c/1.response.md`

### Analytical appendix — complete canonical registers (part 1 of 2: from 'T2F.1 Source register')

Kind: register appendix · handoff lines 133-213 · verdict **BLOCK**

- Narrative: This is a data appendix, so no bottom line is owed. I checked the arithmetic (9,189 / 25,068 = 36.66%; 5,789 = 9,189 − 3,400; 57.89 / 1,880 = 3.08%; 91.89 / 1,880 = 4.89%; fair values 57 / 10) and it holds. The text still exposes pipeline wording and internal codes, and leaves the module's headline sensitivity conflicting with management's estimate with no explanation.
- Visual: The section has no chart. Its registers render as over-wide tables clipped at the right edge, losing the Credit Implication and Source columns, under broken 'a method step …' headings, with cells wrapping to one or two words per line.

1. **High · narrative** (Auditor)
   - Where: line 140-142: "Upstream handoff, CP-OS accepted" (rendered 'Upstream handoff, Run activity accepted'); line 137 headers "source_document_id | source_document_name | source_quality | … | downstream_use"; line 139 "T2F.2–T2F.8; T2G.1–T2G.7" (rendered 'method steps')
   - Problem: Pipeline vocabulary reaches the reader: 'Upstream handoff', 'accepted', snake_case field names and a 'downstream_use' column whose every value renders as the empty phrase 'method steps'. The house standard forbids all of these.
   - Fix: Use reader headers (Document, Quality, Period, Coverage, What it supplies, Limitation, Source), describe upstream rows as the earlier analysis sections they are, and drop the downstream_use column.
2. **High · narrative** (Saboteur)
   - Where: line 192: "+100 bp, management disclosure | Company estimate on term loans and securitization | Item 7A | About USD 30 million a year | Conflicts with M06 by USD 27.89 million; unexplained"
   - Problem: The module's headline rate sensitivity (USD 57.89 million per 100 bp, line 191) is almost double the company's own figure, and the gap is left 'unexplained'. T2F.8 (line 218) then puts both numbers side by side. A committee member cannot tell which to use, and the larger one is carried forward as the base case.
   - Fix: State which figure the view relies on and why (for example, whether management's estimate nets the in-the-money cap and swaps differently), or carry the conflict as an explicit limitation on the headline number.
3. **High · visual** (Auditor + New reader (promoted))
   - Where: T2F.2 Debt and rate exposure register and T2F.1 Source register, screenshot CP-2E_s-135.png, right edge x≈1000-1440, y≈980-1400 (crop tmp/CP-2E-109-a.png)
   - Problem: The tables are wider than the content pane and clipped on the right. 'Credit Impli…' (the only judgement column in T2F.2) is cut mid-word, and the Source column of T2F.1 is truncated ('TDG_2024-09…', 'Business and transaction fac…'). No scrollbar or other sign shows that more columns exist.
   - Fix: Fit each register to the pane (drop or merge the trace columns, or wrap them) so the Credit Implication and Source columns are fully visible without hidden horizontal scroll.
4. **High · visual** (Auditor + New reader (promoted))
   - Where: Table headings 'a method step Source register', 'a method step Debt and rate exposure register', 'a method step Hedging register' (screenshot y≈196, 822, 1638) and the same labels in the On-this-page list
   - Problem: Replacing the register code (T2F.1 etc.) has left the heading text 'a method step …', which is broken English. It appears on every table and in the side navigation, which makes the page look machine-generated.
   - Fix: Show plain titles ('Source register', 'Debt and rate exposure') with no leftover substitution text.
5. **Medium · narrative** (Auditor)
   - Where: line 174: "…can trigger default and accelerated settlement under the swaps, cap and collars (TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175, 177–178)."
   - Problem: A raw filename source reference sits inside a narrative sentence. The house rule allows references only in Basis lines, Source columns and the Sources section.
   - Fix: Move the reference to a Basis line under the paragraph and leave the sentence free of citations.
6. **Medium · narrative** (New reader)
   - Where: line 162: "Coverage Status … Effective where supported"; line 182: "calculation M02; calculation M08"; line 151: "Item 7A; CP-1A F9"
   - Problem: Internal labels the reader cannot resolve without another page fill the table: calculation IDs (M01-M27), fact codes (F9, C24, C01), the unexplained status 'Effective where supported', and the 'Source Trace' column next to a separate 'Source' column. Together they make dense tables denser.
   - Fix: Remove the Source Trace column and calculation/fact IDs from the reader view, and replace 'Effective where supported' with a plain status such as 'In force at 30 Sep 2024'.
7. **Medium · visual** (New reader + Saboteur (promoted))
   - Where: screenshot CP-2E_s-135.png, T2F.2 and T2F.3 rows y≈870-1610 and 1690-1950
   - Problem: With 9-11 narrow columns, cells wrap to one or two words per line ('Adjusted / Term / SOFR / (one-, / three- or / six- / month)'). Single rows reach 150-200 px tall, and the 10-row hedging register runs past the screenshot. Notional, strike and maturity can no longer be compared at a glance.
   - Fix: Give numeric columns (Notional, Rate/Strike, Maturity) fixed narrow widths, move long qualifiers into a footnote or the Limitation column, and keep each row to about three lines.
8. **Low · narrative** (New reader)
   - Where: line 151: "Term SOFR + 2.75% (I, K); + 2.50% (J, L); weighted average rate with securitization 6.5%"
   - Problem: The cell mixes a margin with an all-in weighted average rate and gives no period for the 6.5%. A reader may take 6.5% for a margin, or for the term loans alone.
   - Fix: Split the margin and the all-in weighted average rate (with its date) into separate, labelled values.

### Sources

Kind: prose/table · handoff lines 18-33 · verdict **CONCERNS**

- Narrative: The Sources section is reference material, not judgement. It fails on reader language ("Supplied handoff", "context", "blank stress assumptions") and contradicts itself: "Business & governance" is shown both as a supplied input and as content not referenced.
- Visual: There is no chart in this section. Its two tables are dominated by 64-character hashes and a raw file ID that wraps to five lines, one table has a duplicated name column, and the section sits in the middle of the findings instead of at the end.

1. **High · narrative** (Saboteur + Auditor)
   - Where: Line 32: "CP-2C (governance) and CP-DR content are not referenced for this module's conclusions." Rendered as "Business & governance (governance) and Research questions content are not referenced" (CP-2E_s-18.png, y~600-620). The table above (line 29) renders CP-1A as Module "Business & governance"
   - Problem: The label substitution maps both CP-2C and CP-1A to "Business & governance". On screen, the sentence says that module's content was not used, while the table directly above lists it as a supplied input and the Basis lines cite it. A reader cannot tell which inputs the conclusions rest on.
   - Fix: Give the governance module a distinct reader name (or state that it was not supplied in this run), so that no on-page label means two different inputs.
2. **High · narrative** (Auditor + New reader)
   - Where: Line 25: "| Supplied handoff | Module | sha256 |" and line 23: "| context | f7b95e1f… | Run settings only (as-of 2024-09-30, FY2024 current, USD); not issuer evidence; blank stress assumptions not treated as zero |"
   - Problem: "Supplied handoff" is pipeline vocabulary that the house standard bans. "context" is listed as a source with a hash, and "blank stress assumptions" refers to run settings the reader never sees. Neither tells a credit committee member anything about the evidence.
   - Fix: Head the table in reader terms (for example "Earlier analysis relied on"), and drop the run-settings row or state its content (as-of date, currency) in plain words.
3. **Medium · visual** (New reader + Auditor)
   - Where: Both Sources tables, sha256 columns (CP-2E_s-18.png crop CP-2E-099-a.png, x~250-730 and x~480-970)
   - Problem: 64-character hashes take the widest column in both tables. Because of them, the source name wraps to five lines ("TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"), while the useful "Use in this module" text is squeezed. Hashes are integrity metadata, not reader content.
   - Fix: Show a readable document name (for example "FY2024 annual report (10-K), filed 2024-11") and fold the hashes and file IDs into a collapsed or provenance-only view.
4. **Medium · visual** (New reader)
   - Where: Supplied-handoff table, columns "Supplied handoff" vs "Module" (rows "Source readiness | Source readiness", "Financial data foundation | Financial foundation")
   - Problem: The two columns repeat nearly the same name in every row, so the table spends a column on duplication and adds one more name for each input.
   - Fix: Merge them into one column that uses the same name as the left-hand module navigation.
5. **Medium · visual** (Saboteur + Auditor)
   - Where: "On this page" nav and page flow: Limitations, Timeline, Front matter, Request, Sources, then Macro and hedging view, Credit implication, Events (CP-2E_s-18.png, nav y~620-830; body y~195-770)
   - Problem: Sources is placed in the middle of the analysis: after it, the page resumes with the "Macro and hedging view" and "Credit implication" findings. The reader has to pass through a block of hashes to reach judgement content, and the reading order departs from the house order of findings first and sources at the end.
   - Fix: Render Sources (and Request) after all findings subsections, at the foot of the module, as in the VMO2 reference.
6. **Low · narrative** (New reader)
   - Where: Line 32: "the PDF annual report (duplicate per CP-0) and the Q1 FY2025 quarterly filing were not relied on; a search of the Q1 FY2025 filing for collar notionals returned no hits, so post-period hedge changes are a gap"
   - Problem: A material limitation (whether hedges were renewed after year end, which bears directly on the hedge-cliff conclusion) is stated in the Sources footnote in process language ("returned no hits", "duplicate per") instead of only in Limitations.
   - Fix: Keep Sources to a list of what was used and leave the post-period hedge gap to the Limitations passage, which already states it.

### Limitations

Kind: reader passage · handoff lines 66-80 · verdict **CONCERNS**

- Narrative: The section comes in the right place, after contrary evidence. Each bullet ties a gap to its effect, but bullet 1 contradicts itself on direction, the list never says whether the caveats change the Moderate view, and "this module" and "pages read" leak to the reader.
- Visual: The section is a plain bullet list of readable width with no chart of its own. On screen, bullets 2 and 3 have lost their Basis chips, figure-chip styling is uneven, and the Timeline heading butts against the last bullet.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 68: "if the hedges were tied to tranches since repriced or extended, the effective coverage, and therefore the unhedged amount driving the moderate risk level, would be larger than shown."
   - Problem: The sentence says coverage and the unhedged amount would both be larger, which cannot both be true: more coverage means less unhedged debt. A committee member cannot tell whether this limitation makes the USD 5,789 million exposure too high or too low.
   - Fix: Say which way the measured unhedged amount would move (larger or smaller than USD 5,789 million) and why, as one direction-consistent statement.
2. **High · visual** (Auditor, Saboteur)
   - Where: Screenshot CP-2E_limitations.png, crop CP-2E-103-a.png (Limitations bullets 2 and 3); handoff lines 71 and 73 both carry Basis lines
   - Problem: The Basis chip is printed on bullets 1, 4, 5 and 6 but missing on bullets 2 (USD 30 million vs USD 57.89 million) and 3 (Term SOFR and collar ceilings). These are the two bullets with figure chips, so their source references (page 73 and calculation M13; page 176) are lost on screen. That breaks the rule that every paragraph keeps its Basis line.
   - Fix: Render the Basis chip on every limitation bullet, including those with inline figure chips, so each one can be traced to its source like its neighbours.
3. **Medium · narrative** (Saboteur)
   - Where: line 70: "the free-cash-flow erosion could be half what this module states"; line 72: "which may overstate forward sensitivity"; line 78: "any re-hedging since then would weaken the cliff argument"
   - Problem: Three of the six limitations say the main risk may be overstated, but none says whether, together, they could move the Moderate macro risk level. That leaves the reader to weigh the caveats against the bottom line alone.
   - Fix: Close the list with one sentence on whether these limitations, taken together, leave the Moderate view intact or bias it, and in which direction.
4. **Medium · narrative** (Auditor, New reader)
   - Where: line 70: "could be half what this module states"; line 72: "so this module cannot say whether the collar ceilings"; lines 74 and 78: "in the pages read"
   - Problem: "This module" and "the pages read" are pipeline and process wording. A portfolio manager does not know what a module is or which pages were read.
   - Fix: Use reader language such as "this analysis" or "the annual filing does not disclose", with no reference to the production process.
5. **Medium · narrative** (Auditor)
   - Where: lines 78-79: "Hedge activity after 2024-09-30 was not located in the first-quarter fiscal 2025 filing ... Basis: TDG_2024-09-30_10-K_..., page 176"
   - Problem: The claim is about a search of the Q1 FY2025 filing, but its Basis cites only the FY2024 annual filing page 176. That page cannot support a statement about what the later filing does or does not contain.
   - Fix: Cite the Q1 FY2025 filing that was searched (the Gaps table already names it) in this bullet's Basis line, or narrow the claim to what page 176 supports.
6. **Low · narrative** (New reader)
   - Where: line 72: "whether the collar ceilings of 3.50% and 4.50% would be in the money in 2025 to 2027; post-2025 protection is treated as zero inside the band"
   - Problem: "Collar ceilings", "in the money", "inside the band" and "as-of date" are not explained in this section. The reader has to go back to the key findings to understand that hedges pay only when rates are above the ceiling.
   - Fix: Add a short plain-language explanation, e.g. that the collars pay out only if Term SOFR rises above 3.50% or 4.50%.
7. **Low · visual** (Auditor)
   - Where: Screenshot CP-2E_limitations.png, crop CP-2E-103-a.png: last Limitations bullet and the "Timeline" heading directly below it
   - Problem: The Timeline heading sits right under the last bullet with almost no gap, so it reads as part of the Limitations list rather than a new block. Monospace bold figure chips appear only in bullets 2 and 3, which makes the typography uneven within one list.
   - Fix: Add the standard section spacing before the Timeline heading, and style inline figures the same way in every bullet of the list.

### Macro and hedging view

Kind: prose/table · handoff lines 81-93 · verdict **BLOCK**

- Narrative: The judgement comes first and its numbers reconcile (57.89/1,880 = 3.08%, 91.89/1,880 = 4.89%, 5,789/25,068 = 23.09%), but the section repeats the bottom line after Limitations, out of the house order. Its prose also calls the exposure small and leaves out the forward USD 77.89–91.89 million figures that its own table and Events rows show.
- Visual: This section has no chart, just a dense paragraph and a five-column table. The table is legible but wraps dates, puts Basis chips inside the row labels, and styles figures differently from the prose.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 83: "so a 100 bp rise costs USD 30 million to USD 57.89 million a year, small against 3.60x cash interest cover. The risk is in timing"
   - Problem: The headline sensitivity quotes only today's range and calls it small, but the same section's table (line 89) gives USD 91.89 million once swaps and cap lapse, and the Events table (line 106) gives USD 77.89 million after 2025-03-31. The forward cost the paragraph itself calls the risk never appears in the prose, so a reader who skims stops at 'small'.
   - Fix: In the opening sentences, state the forward figures (USD 77.89 million after 2025-03-31 and USD 91.89 million after 2025-09-30, with their share of FY2024 free cash flow) next to today's range, so the judgement rests on the exposure the section calls decisive.
2. **High · narrative** (Auditor, New reader)
   - Where: line 81: "### Macro and hedging view", placed after "### Limitations" (line 66) and followed by "### Overall macro and hedging view (Step 10)" (line 111)
   - Problem: A second bottom-line verdict ('sensitivity is Moderate') comes after Limitations, which breaks the house order of bottom line, key findings, contrary evidence, limitations. A third restatement follows two sections later, so the reader meets the judgement three times in different words.
   - Fix: Fold this view and its table into Bottom line or Key findings ahead of Limitations, and drop the duplicate restatements.
3. **Medium · narrative** (New reader)
   - Where: line 92: "| Inflation | Most contracts bar cost recovery | Margin 52.56% vs 51.56% | No commodity hedges disclosed |"
   - Problem: The margin is not identified (EBITDA As Defined? gross?) and its periods are missing (FY2024 vs FY2023 only appears in the trace table further down). It also sits in the 'Forward point' column although it is history, not a forward point.
   - Fix: Label it, for example 'EBITDA As Defined margin FY2024 52.56% vs FY2023 51.56%', and put it in a column whose heading fits historical evidence.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: line 83: "small against 3.60x cash interest cover"; line 83: "supported effectiveness ends with the swaps"; line 89: "Conflict unexplained"
   - Problem: The 3.60x ratio has no stated numerator or period (it is EBITDA As Defined over cash interest, FY2024), and a USD cost is weighed against a ratio with no link between them. 'Supported effectiveness' and 'Conflict unexplained' are internal shorthand: the reader cannot tell that the conflict means our USD 57.89 million against management's USD 30 million, and that sits in a 'Hedge limitation' column it does not belong to.
   - Fix: Name the ratio and its period, say how much it would fall after +100 bp, and replace the shorthand with plain words ('our figure is about double management's; the filing does not explain the gap').
5. **Medium · narrative** (New reader)
   - Where: line 83: "TransDigm's macro and hedging sensitivity is Moderate. About 77% of gross debt ... largely bar cost recovery."
   - Problem: One paragraph of about 150 words carries rates, hedge timing, monitoring triggers, FX and inflation, with eight percentages packed into it. On screen it is a nine-line wall of text, and the monitoring trigger is buried in the middle.
   - Fix: Split it into a two-sentence judgement and then short paragraphs, or bullets, for rate timing, the monitoring trigger, and FX/inflation.
6. **Medium · visual** (Auditor, New reader)
   - Where: Table in /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2E-104-a.png, Forward point column row 1 and Exposure column
   - Problem: The date breaks across lines ('after 2025-' / '03-31'), and the grey 'Basis' chips sit inline in the Exposure cells ('Unhedged floating-rate debt Basis', '+100 bp cash interest Basis'), where they read as part of the row label. The table has no Source column, so the Basis chip is the only route to sources and is easy to miss.
   - Fix: Keep dates from wrapping (non-breaking or a wider column), and move Basis into its own Source column or out of the label cell.
7. **Low · narrative** (Auditor)
   - Where: line 91: "Foreign sales USD 2.9bn (36.52%)"
   - Problem: Every other amount in the section is in USD million. 'bn' with one decimal place breaks the unit convention and the precision used everywhere else.
   - Fix: Show the amount in USD million at the source precision, matching the rest of the table.
8. **Low · visual** (Saboteur)
   - Where: Prose paragraph in /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2E-104-a.png, top 140 px
   - Problem: Eleven figures appear in bold monospace with a dotted underline, so the paragraph looks like code. The table below shows the same figures in plain text, so the two styles disagree on one screen.
   - Fix: Use one quiet figure style for both prose and table, or reserve the emphasis for the one or two figures that carry the judgement.

### Overall macro and hedging view (Step 10)

Kind: prose/table · handoff lines 111-117 · verdict **BLOCK**

- Narrative: The section is an end-of-module summary that repeats the bottom line a third time, out of house order and with a sensitivity figure that disagrees with the earlier range. It is labelled with pipeline step numbering and followed by a run-status stamp in internal vocabulary.
- Visual: There is no chart, map or table in this section. It is one dense paragraph plus a status line set in the same style, and its figure styling (monospace pills) is inconsistent between the two. The Basis line could not be seen in the screenshot.

1. **High · narrative** (Auditor, New reader)
   - Where: line 116: "CP-2E Completed with Limitations. Macro Risk Level: Moderate. Key Gaps: tranche-level hedge linkage; reconciliation of management's USD 30 million sensitivity; ..." (rendered as "Rates, FX & hedging Completed with Limitations...", CP-2E_s-111.png y~300-330)
   - Problem: A run-status stamp is printed to the reader as body prose. 'Completed with Limitations', 'Macro Risk Level' and 'Key Gaps' are internal status-register wording, and the module name now opens a sentence that has no verb. It repeats the limitations a fourth time.
   - Fix: Drop the status line from the reader page, or show it as a labelled status chip in the module header, and leave the gaps to the Limitations list.
2. **High · narrative** (Auditor, New reader)
   - Where: line 111: "### Overall macro and hedging view (Step 10)" (heading and 'On this page' nav entry, CP-2E_s-111.png top and left rail y~885)
   - Problem: '(Step 10)' is method/pipeline numbering, which the house standard says must not reach the reader. It also appears in the page's navigation as its own entry.
   - Fix: Remove the step number from the heading and the nav label.
3. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 113: "a 100 bp rate move would affect cash interest by about USD 57.89 million on our calculation (management: about USD 30 million)" vs line 83 "a 100 bp rise costs USD 30 million to USD 57.89 million a year"
   - Problem: This is the third restatement of the bottom line (after lines 38 and 83), and it comes after Limitations and Events, which breaks the judgement-first order. The restatements also disagree. Line 83 gives a range, this one gives a point estimate, and this one leaves out the forward USD 77.89–91.89 million sensitivity that drives the hedge-cliff argument.
   - Fix: Keep one bottom line at the top. If this summary stays, make it repeat the same range and the forward figure exactly, and place it so it doesn't follow the limitations.
4. **Medium · narrative** (New reader)
   - Where: line 113: "a gradual FCF and interest-cover drag after the 2025 swap expiries and a hedge cliff on 2027-09-30 ahead of the term loans, which raises refinancing sensitivity into the FY2028 wall"
   - Problem: 'FCF' is never spelled out and 'the FY2028 wall' has no amount here (the USD 6,637 million appears only in the trace table below). The drag is also never given a number, although lines 50 and 89 have one (4.14%–4.89% of FCF; cover 3.60x).
   - Fix: Spell out free cash flow and give the wall's size and the drag's size in the sentence that makes the claim.
5. **Medium · narrative** (Saboteur)
   - Where: line 113: "FX and raw-material risk appear manageable because management states a 10% currency move is immaterial ... though neither is backed by a disclosed currency or cost breakdown."
   - Problem: The judgement is hedged ('appear') and then undercut in the same sentence, so a reader can't tell whether FX and inflation are cleared or still open. The sentence also stacks a limitation into the judgement paragraph.
   - Fix: State the view plainly (e.g. secondary to the rate risk) and leave the missing-breakdown caveat to Limitations.
6. **Low · narrative** (Saboteur)
   - Where: line 113: "would affect cash interest by about USD 57.89 million on our calculation"
   - Problem: 'About' paired with two-decimal precision, beside management's rounded USD 30 million, suggests a confidence the module itself disowns (line 70: the 'range rather than a point').
   - Fix: Round to about USD 58 million, or show the exact figure without 'about'.
7. **Low · visual** (Auditor, New reader)
   - Where: CP-2E_s-111.png crop CP-2E-107-a.png (section paragraph and status line, x 330-1420, y 220-420)
   - Problem: Figures in the paragraph use monospace pill styling with dotted underlines. The same 'USD 30 million' in the status line just below is plain text. The status line has the same weight and type as the analytical paragraph, so it reads as more analysis. The Basis line in the handoff (line 114) can't be seen in this view.
   - Fix: Use one figure style throughout the section, set any status information apart from the prose, and make the Basis reference visible below the paragraph as on other prose sections.
8. **Low · visual** (New reader)
   - Where: CP-2E_s-111.png, section block y~190-330 followed immediately by 'Upstream re-anchor and method trace' table
   - Problem: The section is one dense six-line paragraph with no break between bottom line, implication and gaps. Directly below it comes a method-trace table whose heading uses pipeline vocabulary ('re-anchor'), so the reader moves from conclusion into internals with no separation.
   - Fix: Split the paragraph into a short judgement and a short implication, and fold or visually separate the method trace that follows.

### Upstream re-anchor and method trace

Kind: prose/table · handoff lines 118-132 · verdict **BLOCK**

- Narrative: This section is internal provenance and process trace. It shows pipeline vocabulary, script and reference filenames, register codes and a garbled code substitution to the reader, and it buries the module's confidence rating at the end of an undefined formula.
- Visual: The table fits the 1440 px page without clipping and is legible. However, register-code chips, Basis chips placed in the wrong column, a repetitive Source column and a dense paragraph below it make the section look like a log rather than a reader table.

1. **High · narrative** (Auditor + New reader)
   - Where: line 131: "Helper scripts (prepare_invocation.py, rate_fx_sensitivity.py, confidence_score.py, completeness_check.py, validate_handoff.py) were not run in this transport; ... Companion files REF_CP-2E_* and REF_CP-2F_* ... CANON_SHARED sections"
   - Problem: The paragraph is pipeline housekeeping shown to the reader: script filenames, "transport", "handoff", REF_CP-2E_*/REF_CP-2F_* (which shows module codes on screen), CANON_SHARED, "seventeen required registers" and "source gate". It is visible as-is in CP-2E_s-118.png under the table. A portfolio manager cannot act on any of it.
   - Fix: Take this paragraph off the reader page. If something matters for credit, such as the sensitivity having been computed by hand, say it in plain words in Limitations.
2. **High · narrative** (Auditor + New reader)
   - Where: line 118: "### Upstream re-anchor and method trace" (also the left-hand 'On this page' entry in CP-2E_s-118.png)
   - Problem: The heading and the page's table-of-contents entry both use "re-anchor" and "upstream". These are pipeline terms the house standard bans, and the reader has no idea what a "method trace" is.
   - Fix: Rename it as a reader heading such as "Figures used from other sections", or move it to the appendix.
3. **Medium · narrative** (Saboteur + Auditor)
   - Where: line 131: "Confidence Score 62 (Medium): E = 91 (ten material claims...), C = 85 ..., S = 0.7 (source gate partial...), P = 0; score = (0.6 × 91 + 0.4 × 85) × 0.7 = 62.02."
   - Problem: The module's confidence rating is the one judgement here that bears on credit, yet it sits at the end of a wall of text after script names. The formula's E, C, S and P are never defined, P = 0 is unexplained, and so the reader cannot tell how far to trust the module's view. (The arithmetic checks out: 88.6 × 0.7 = 62.02.)
   - Fix: State the confidence level and the main reason for it in one plain sentence at the top of Limitations, and drop the internal formula.
4. **Medium · narrative** (Saboteur)
   - Where: line 126: "| CP-1 | EBITDA As Defined / cash interest (C12); margins (C21, C22) | 3.60x; 52.56% vs 51.56% | FY2024 / FY2023 |"
   - Problem: One row packs in two measures and two periods. Which margin is meant (EBITDA? gross?) is not said, and the 3.60x cover could be read against FY2023. That is ambiguity about the very interest-cover figure the rate-sensitivity view depends on.
   - Fix: Split this into separate rows (interest cover FY2024; the named margin FY2024; the named margin FY2023), each with its unit and period.
5. **Medium · narrative** (New reader + Auditor)
   - Where: line 122: "Identity, effective source set, CP-2E readiness | READY_WITH_LIMITATIONS; derivatives note left to CP-2E"; rendered at line 131 as "No Research questions research question was assigned to this module"
   - Problem: A raw status enum (READY_WITH_LIMITATIONS), "effective source set" and a module referring to itself all appear on screen. Replacing the code CP-DR has turned line 131 into the garbled phrase "Research questions research question".
   - Fix: Show readiness in plain words ("sources sufficient, with limitations"), drop the self-reference, and fix the garbled sentence or delete it.
6. **Medium · visual** (New reader + Auditor)
   - Where: Table in CP-2E_s-118.png, top region (y≈215–640 displayed): Datapoint column chips "C01", "C15", "C28", "C12", "C21, C22", "C24"
   - Problem: Register codes appear as monospace chips inside reader-facing labels. They mean nothing to the reader, and they make labels such as "EBITDA As Defined / cash interest (C12); margins (C21, C22)" harder to read.
   - Fix: Remove the internal register codes from the visible labels, or keep them only behind the Basis link.
7. **Low · visual** (Auditor)
   - Where: Table in CP-2E_s-118.png, 'Upstream module' and 'Source' columns (x≈300–1160, y≈245–635 displayed)
   - Problem: The "Basis" chip sits in the first column next to the section name rather than with the source. The Source column repeats the section name ("Financial data foundation (Financial foundation)") on six rows, which uses width without telling the reader anything.
   - Fix: Attach the Basis link to the Source cell and drop the duplicated 'Upstream module' column, or shorten the Source text.
8. **Low · visual** (New reader)
   - Where: Paragraph below the table in CP-2E_s-118.png (y≈655–745 displayed)
   - Problem: About 130 words run in a single block, with filenames and a formula and no break. On screen it reads as an error log rather than as analysis.
   - Fix: If any of it stays, break it into one or two short plain sentences.

### Analytical appendix — complete canonical registers (part 2 of 2: from 'T2F.8 Macro sensitivity summary')

Kind: register appendix · handoff lines 214-304 · verdict **BLOCK**

- Narrative: The registers are dense but factually consistent with the rest of the module; the problems are reader-facing pipeline vocabulary (line 295 \"source gate\", module-ownership columns), a buried risk-level judgement, and the 57.89 versus 30 sensitivity conflict, which the summary softens.
- Visual: There is no chart in this appendix section, only tables. On screen, code substitution produces \"a method step\" headings and empty Impact cells, raw .jsonl filenames inflate the row heights, and a repeated inline \"Basis\" chip clutters the first column.

1. **High · narrative** (Auditor; Saboteur)
   - Where: Line 295: "ESG confidence: module Confidence Score 62 (Medium), driven by self-reported disclosure and partial source gate."
   - Problem: This puts pipeline vocabulary ("module", "source gate") and an internal score with no defined scale in front of the reader. The ruling bans that, and a committee member cannot tell what 62 measures or what a "partial source gate" means for the credit view. The library data stores the line verbatim, so it renders on screen.
   - Fix: State the confidence in reader terms, for example "Medium confidence: emissions data are self-reported and unassured, and not all source documents were available", with no score or gate wording.
2. **High · visual** (New reader; Auditor)
   - Where: Line 230 "| G1 | Tranche-level hedge designation | ... | T2F.3, T2F.4 hedged amount |"; lines 232-236 Impact column "T2F.5", "T2F.6", "T2F.7", "T2F.2"; headings line 214/226. Screenshot CP-2E_s-214.png, Gaps ledger table and all section headings (y≈195-1340 at 1200 scale)
   - Problem: The renderer replaces every register code with the literal phrase "a method step", so headings read "a method step Macro sensitivity summary" and the Gaps ledger's Impact on Output column reads "method steps hedged amount", "a method step point estimate" and, for G5-G7, just "a method step". The reader cannot tell which table a gap affects, so the column no longer carries any information.
   - Fix: Map each register code to its reader-facing table title (for example "Rate sensitivity table") in both headings and cells, not to a generic placeholder.
3. **Medium · narrative** (Saboteur)
   - Where: Line 218: "USD 57.89 million per 100 bp (management about USD 30 million); 3.08% of FCF | Modest; cover stays above 3x"
   - Problem: The summary puts the model figure next to management's estimate, which is roughly half of it, but drops the word "unexplained" (and the USD 27.89 million gap) that T2F.5 records. "cover stays above 3x" does not say which cover ratio, which period, or before or after the shock. A reader could take 57.89 as settled and "Modest" as tested.
   - Fix: Name the ratio and period behind "3x", and flag the 30 versus 57.89 difference as unreconciled, pointing to the gap entry, in the same cell.
4. **Medium · narrative** (Auditor; New reader)
   - Where: Line 228 header "Downstream Module Affected"; line 222 "Owned by CP-2A stress" (rendered "Owned by Downside stress"); line 240 header "Module Status"; line 261 "is owned by CP-2C, which is not supplied in this run"
   - Problem: Column headers and cells describe how the pipeline divides the work (which module owns what, what was supplied in this run) rather than the credit. The screenshot shows "Downstream Module Affected" and "Owned by Downside stress" on screen. Promoted because two personas caught it.
   - Fix: Relabel these as reader concepts, for example "Also affects" with page names, "Assessed in the Downside page", and "Governance not assessed in this report".
5. **Medium · visual** (New reader; Saboteur)
   - Where: Source column in T2F.8 and T2G.2/T2G.3 tables, for example line 218 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73"; screenshot CP-2E_s-214.png right-hand column y≈250-810
   - Problem: The raw ingestion filename (an accession number plus a .jsonl extension) wraps to five lines in every row, which makes each row three to five times taller and pushes the analytical columns into narrow strips. The Source Trace column next to it shows internal IDs such as "calculation M06", which mean nothing without the separate Calculations register.
   - Fix: Show a short document label, for example "FY2024 10-K, p. 73", with the full identifier in the Evidence page or a tooltip, and link the calculation IDs to their register row.
6. **Low · narrative** (Saboteur)
   - Where: Line 224: "Macro Risk Level: Moderate."
   - Problem: The section's only judgement sits after a five-row table, as an unbolded line with no basis, so it reads as a footnote rather than a conclusion. Judgement-first ordering is inverted here.
   - Fix: Put the risk level and its one-line reason above the table, or bold it with a Basis line.
7. **Low · narrative** (Saboteur)
   - Where: Line 219: "Swaps end 2025; collars end 2027-09-30"
   - Problem: Elsewhere in the module the swaps step down on two dated steps (2025-03-31 and 2025-09-30), but here they collapse to a bare year while the collars get an exact date. That understates how soon the first step-down falls in the cliff timing.
   - Fix: Give both swap end dates exactly, matching the rate sensitivity rows.
8. **Low · visual** (New reader)
   - Where: "Basis" chip after the first cell of every row (for example "Hedge cliff Basis", "G1 Basis"); screenshot CP-2E_s-214.png first column throughout
   - Problem: An unexplained grey "Basis" label repeats in every row of every table. It is unclear whether it is a control or a label, and it breaks the row-label text, for example in "Physical climate risk to facilities (storms, fires, sea level, water) Basis".
   - Fix: Use one consistent, labelled affordance (an icon with an accessible name, or a single column) rather than inline text repeated in each row label.

### Calculations

Kind: prose/table · handoff lines 339-372 · verdict **BLOCK**

- Narrative: The section is a data appendix whose only sentence is pipeline process text. Its labels lean on internal IDs and undefined scores. One percentage (M04, unhedged debt against total debt) can be misread as the unhedged share of floating debt, which understates rate exposure.
- Visual: There is no chart. The table renders cleanly with right-aligned values, but it has 27 ungrouped rows, a monospace Result header that does not match the other headers, a redundant % unit column, and a wide Item-Result gap. It also duplicates the register immediately above it.

1. **High · narrative** (Auditor, New reader)
   - Where: L341: "All new arithmetic used the calculate tool; the full register with IDs M01 to M27 is in the Calculations register inside Findings ... Helper scripts were not run in this transport."
   - Problem: The only prose in the section describes how the pipeline ran ("calculate tool", "Helper scripts", "this transport", "inside Findings"), not anything about the credit. The house standard bars pipeline wording from reader text, and a portfolio manager gets nothing from this sentence.
   - Fix: Remove the process sentence. If the section stays, open it with one reader sentence saying what the figures show, e.g. the rate sensitivity per 100 bp and the hedge cliff.
2. **High · narrative** (Saboteur)
   - Where: L348: "| M04 | Unhedged debt percentage | 23.09% | % |" next to L352: "| M08 | Hedged share of floating debt | 37.00% | % |"
   - Problem: M04 is 5,789 / 25,068, so it measures unhedged debt against total debt. M08 just below measures hedged debt against floating debt. Read side by side, the two suggest 23% of floating debt is unhedged, when the real figure is 63%, which understates the rate exposure.
   - Fix: Name the denominator on every percentage row, e.g. "Unhedged floating debt / total debt", and consider adding the unhedged share of floating debt.
3. **Medium · narrative** (New reader)
   - Where: L357-361: "| M13 | Calculated minus management sensitivity | 27.89 |" ... "| M14 | M06 / FCF | 3.08% |" ... "| M15 | M06 / pro forma liquidity |"
   - Problem: Several item labels are internal cross-references (M06, M07, M10) or leave out the comparator. FCF and pro forma liquidity have no period or amount. The reader has to go to the register above to decode the rows, and still cannot tell which FCF year is meant.
   - Fix: Write each item in plain words with its basis and period, e.g. "+100 bp cost on unhedged debt as % of FY2024 free cash flow (USD 1,880m)".
4. **Medium · narrative** (New reader, Auditor)
   - Where: L369-371: "| M25 | Evidence score E | 91 | score |" / "| M26 | Weighted E and C | 88.6 | score |" / "| M27 | Confidence score | 62.02 | score |"
   - Problem: The undefined internal scoring (E, C, a "score" unit) sits inside a credit-figures table. C and S are never explained, so these three rows mean nothing to a committee member and look like analytical results.
   - Fix: Move the confidence scoring out of the credit calculations table, or define it in one plain sentence with its scale.
5. **Medium · narrative** (Saboteur, Auditor)
   - Where: L343-371, the Calculations table (header "| ID | Item | Result | Unit |")
   - Problem: The table restates the register shown directly above it (its M24-M27 rows are visible at the top of the screenshot) but drops the inputs and has no Source column. So the reader sees the same 27 IDs twice, and the second copy has no traceable basis.
   - Fix: Keep one register with its inputs and a Source column, or cut this summary to the handful of figures the conclusions rely on.
6. **Medium · narrative** (Saboteur)
   - Where: L345: "| M01 | Gross floating-rate debt | 9189 | USD m |"; L366: "| M22 | Secured notes | 11000 | USD m |"
   - Problem: Amounts appear without thousands separators (9189, 5789, 7789, 11000), while the register above and the narrative use 9,189 and 2,938. Units also switch from "fraction" in the register to "%" here. The inconsistent number format invites misreading on the same page.
   - Fix: Format all USD m amounts with thousands separators and use one unit convention across both tables.
7. **Low · visual** (Auditor, New reader)
   - Where: Calculations table, CP-2E_s-339.png, roughly y 530-1610 (original px)
   - Problem: The table is one ungrouped block of 27 rows. The Result header is set in a monospace face unlike the other headers. The Unit column repeats "%" for values that already carry a % sign. And the wide gap between Item and Result pushes values far from their labels at 1440 px.
   - Fix: Group the rows (rates, FX, structure, confidence), narrow the Item-Result gap, and drop the redundant % unit.
8. **Low · visual** (New reader)
   - Where: On-this-page navigation, CP-2E_s-339.png, roughly y 1770-1800 (original px): "Calculations register" followed by "Calculations"
   - Problem: The page navigation lists two near-identically named sections next to each other, so the reader cannot tell which one holds the figures with sources.
   - Fix: Show one calculations section in the navigation, or give the two clearly different names.

### Front matter + Request + Next module

Kind: run plumbing · handoff lines 1-13, 14-17, 387-390 · verdict **BLOCK**

- Narrative: This section is run plumbing: it puts a module code (CP-2E in the filename), raw metadata, a garbled code-substituted scope sentence and routing instructions to other modules in front of the reader. None of it is reader language under the house standard.
- Visual: There is no chart in this section. The front matter is rendered as an unlabelled run-on line of snake_case pairs, and the Next module is a dense two-line paragraph that closes the page. Both sit in an over-long sidebar index where plumbing is mixed with analysis.

1. **High · narrative** (Auditor, New reader)
   - Where: Front matter, handoff lines 2-11 as rendered: "issuer_id: tdg module_id: Rates, FX & hedging analysis_date: 2024-09-30 filename: tdg_CP-2E_20240930.md qa_status: Passed confidence_score: 62" (CP-2E_s-1.png, crop CP-2E-114-a.png)
   - Problem: The module code CP-2E is printed on screen inside the filename value, breaking the no-module-code rule. The rest of the block is raw pipeline metadata (snake_case keys, filename, qa_status) that the reader has no use for.
   - Fix: Hide the front-matter block from the Modules page, or show only reader-relevant fields (as-of date, confidence 62/Medium, draft status) under plain labels with no filename or ids.
2. **High · narrative** (Saboteur, New reader)
   - Where: Front matter line 6-9: "qa_status: Passed ... committee_status: Draft Only" (CP-2E_s-1.png, top of section)
   - Problem: The page shows 'Passed' and 'Draft Only' side by side with no explanation. A committee member may read 'Passed' as sign-off on a module that is only a draft at Medium confidence.
   - Fix: Either drop the internal QA flag or state plainly that the module is a draft not yet approved by committee, with confidence 62 (Medium).
3. **Medium · narrative** (New reader, Auditor)
   - Where: Request line 16 as rendered: "Rates, FX & hedging macro, FX, hedging and absorbed ESG/transition (Rates, FX & hedging) sensitivity for TransDigm Group Incorporated (TDG)"
   - Problem: Replacing the codes with display names produced a garbled, circular sentence: the module name appears twice and the absorbed ESG module (CP-2F) is shown as 'Rates, FX & hedging'. The terms 'credit_snapshot pathway' and 'subsequent events flagged and not blended' are pipeline wording.
   - Fix: Write a one-sentence plain scope, e.g. rates, FX, hedging, inflation and credit-material ESG exposure for TDG at FY2024 year-end, with later events reported separately.
4. **Medium · narrative** (Auditor, New reader)
   - Where: Next module line 389 as rendered: "Forward credit model should carry the hedge-cliff schedule into the forecast ... Committee decision should take the hedge cliff as the macro debate item" (CP-2E_s-387.png, bottom)
   - Problem: These are routing instructions between modules, which is pipeline language. The 'Next module' heading means nothing to a credit committee member, and the passage ends the page on plumbing rather than judgement.
   - Fix: Hide the Next module section from the reader view, or rewrite it as a plain 'Feeds into' note under the bottom line.
5. **Medium · visual** (Auditor, New reader)
   - Where: Front matter block, CP-2E_s-1.png y≈195-245 (crop CP-2E-114-a.png)
   - Problem: The key-value metadata is flattened into one run-on paragraph, so keys and values are hard to tell apart. The block also takes prominent space mid-page and in the 'On this page' list, between Timeline and Request.
   - Fix: Remove the block from the reader page or render it as a compact labelled strip; do not list it in the page index.
6. **Low · narrative** (Saboteur)
   - Where: Next module line 389: "applying the USD 57.89 million to USD 91.89 million per 100 bp sensitivity path"
   - Problem: The range is stated with no period or basis. 57.89 is the unhedged sensitivity at FY2024 year-end and 91.89 is the fully unhedged sensitivity after 2027-09-30, while the 77.89 step after 2025-03-31 is left out. Management's 'about USD 30 million' figure is also missing here.
   - Fix: Tie each sensitivity figure to its date (FY2024 57.89, after 2025-03-31 77.89, after 2027-09-30 91.89) and note the management figure.
7. **Low · visual** (Saboteur)
   - Where: On this page sidebar, CP-2E_s-1.png and CP-2E_s-387.png x≈95-260, y≈600-1545
   - Problem: The sidebar lists about 35 entries, with plumbing (Front matter, Request, Upstream re-anchor and method trace, Next module, many 'a method step ...' entries) mixed in with the analysis. The reader's sections are hard to find.
   - Fix: Show only the reader sections in the page index and group the method and plumbing sections under one collapsed heading.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 61-65 · verdict **CONCERNS**

- Narrative: The section names counter-arguments on both sides and gives change triggers, as the standard asks, but it puts everything in one long paragraph, never says how much the contrary evidence weighs, uses the ambiguous word "rating", and leaves the triggers unquantified and the collar-floor reasoning muddled.
- Visual: The section has no chart. It renders as a readable single text column, but the paragraph's Basis link is missing on screen (as are those of Limitations bullets 2 and 3), the monospace value chips sit awkwardly in the prose, and the Timeline below starts without spacing.

1. **High · visual** (Auditor, Saboteur)
   - Where: Screenshot CP-2E_contrary-evidence.png, crop CP-2E-102-a.png (x330-1440, y220-1100): the contrary paragraph ends "...fell below the 75% policy floor." with no Basis link; handoff line 64 carries "Basis: TDG_2024-09-30_10-K... pages 73, 175–178; Business and transaction fact pack (CP-1A); calculation M21"
   - Problem: The page drops this paragraph's Basis line, so the reader cannot trace the 75% policy, the 2.00%/2.50% floors or the USD 47 million hedge asset to a source. The ruling says source references live in the Basis line. The same drop shows on Limitations bullets 2 and 3 (handoff lines 71, 73). In this screenshot only the paragraphs with value chips lose their Basis link, which points to a renderer defect, not a handoff gap.
   - Fix: Render the Basis link on every paragraph whose handoff has a Basis line, including paragraphs that contain value chips.
2. **Medium · narrative** (New reader, Saboteur)
   - Where: line 63: "The strongest case for a lower rating of macro risk is that the company targets at least 75% fixed-rate debt as policy"
   - Problem: On a credit page, "rating" reads as the issuer's credit rating, but here it means this module's Moderate macro-risk level. A committee member could take the passage as a call on the credit rating.
   - Fix: Name the measure plainly, e.g. "the case for a Low rather than Moderate macro-risk level", and use the same term in both directions.
3. **Medium · narrative** (Saboteur)
   - Where: line 63: "the collars' floors of 2.00% and 2.50% mean falling rates, which drove the hedge asset down to a net USD 47 million in FY2024, would cost little while removing most of the exposure"
   - Problem: The reasoning does not hold together. Below a collar floor the company pays the floor rate, so falling rates cap its benefit rather than "remove most of the exposure". The sentence also folds the FY2024 hedge-asset move into a forward-looking claim, so the reader cannot tell what the contrary point actually is.
   - Fix: State the contrary point in one clear claim: what falling rates do to cash interest with the floors in place, quantified or marked as not quantified.
4. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 63: "The view would move to Low if new swaps were disclosed that extend fixed coverage past 2027-09-30, and to High if term-loan debt grew materially while the hedge share fell below the 75% policy floor."
   - Problem: The triggers come last in a 190-word paragraph. The High trigger turns on an unquantified "materially", and the Low trigger names no amount of new coverage, so neither can be monitored.
   - Fix: Put the triggers in their own short sentences or bullets, each with a threshold (an amount of term-loan growth, a notional of extending swaps).
5. **Medium · narrative** (New reader, Auditor)
   - Where: line 63: one paragraph from "The strongest case for a lower rating..." to "...below the 75% policy floor."
   - Problem: The case for lower risk, the case for higher risk and the change triggers share one dense block, and the paragraph never says which way the evidence leans or how much weight it carries against the Moderate view. That is not judgement first, and it slows the reader.
   - Fix: Open with one sentence on the net weight of the contrary evidence, then give the lower case, the higher case and the triggers as three short paragraphs or bullets.
6. **Low · narrative** (New reader)
   - Where: line 63: "Management's own sensitivity is about half ours" and "a further secured recapitalisation funded with term loans, as in September 2024"
   - Problem: "Ours" is unexplained in-house voice, and the passage assumes the reader knows the figures (USD 30 million vs USD 57.89 million) and the September 2024 recapitalisation from other sections.
   - Fix: Restate the two sensitivity figures inline and name the September 2024 transaction in a few words.
7. **Low · visual** (Auditor)
   - Where: Screenshot CP-2E_contrary-evidence.png, crop CP-2E-102-a.png: monospace dotted-underline chips "USD 47 million", "2.00%", "75%" inside proportional body text
   - Problem: The monospace value chips set inside running prose break the reading rhythm and make "USD 47 million" visibly wider than the words around it. The Limitations list then runs straight into the Timeline heading with no gap.
   - Fix: Set value chips in the body font weight or tabular figures rather than full monospace, and add standard section spacing before the next block.

### Credit implication

Kind: prose/table · handoff lines 94-98 · verdict **CONCERNS**

- Narrative: The ESG content leads with a judgement and avoids citations in the prose. However, it sits under a generic \"Credit implication\" heading in a rates and hedging module, which hides the module's real credit implication (the hedge cliff). It is also one dense paragraph, calls a non-credit point \"decisive\", and uses handoff and search-process wording.
- Visual: The section is a single prose block, with no chart or table. The layout is readable at 1440 px, but the paragraph's Basis line (L97) is not rendered and only one figure (50%) gets the value-chip styling.

1. **High · narrative** (Saboteur, New reader (promoted from Medium))
   - Where: L94-96 "### Credit implication" / "No ESG or transition factor is credit-material for TransDigm at 2024-09-30; the highest-priority factor is regulation that would materially restrict air travel"
   - Problem: The only section titled "Credit implication" in the Rates, FX & hedging module covers ESG alone. It says nothing about the hedge cliff, even though the module's bottom line (L41: "The credit-relevant macro risk is therefore the hedge cliff") and the section just before it make that the main finding. A committee member who jumps to "Credit implication" reads that nothing is credit-material and misses the 2025 swap expiries and the 2027-09-30 end of all hedges.
   - Fix: Retitle the section to say it covers ESG and transition risk (e.g. "ESG and transition: credit implication"), or open it with the module's rate and hedge-cliff implication before the ESG view.
2. **Medium · narrative** (Saboteur)
   - Where: L96 "The decisive uncertainty is that the emissions target of at least a 50% Scope 1 and Scope 2 reduction by 2031 against a fiscal 2019 baseline is self-reported, with no assurance located."
   - Problem: The paragraph has already said that carbon cost is immaterial and that no debt term is linked to the target. Calling the lack of assurance on that target "decisive" contradicts this and inflates a non-credit point. It also competes with the stated real driver, air-travel regulation.
   - Fix: Present the unassured target as a limitation, or name an uncertainty that could actually change the ESG view (enacted air-travel restriction) as the decisive one.
3. **Medium · narrative** (New reader)
   - Where: L96 the whole paragraph, opening "No ESG or transition factor is credit-material ... rather than through its own operations." (first sentence about 60 words)
   - Problem: The section is one block of about 180 words in five long sentences, joined by semicolons. The judgement, the main watch factor, the dismissed factors and the limitation all run together, so a reader cannot pick out the watch item quickly.
   - Fix: Lead with a short judgement sentence, then give each factor (air travel, carbon, physical sites, sustainability-linked debt) its own short sentence or a compact list.
4. **Medium · narrative** (Auditor)
   - Where: L96 "The single ESG driver handed to the committee debate is air-travel regulation as a watch factor on aftermarket revenue."; also "No sustainability-linked loan or bond terms were located" and "no assurance located"
   - Problem: "Handed to the committee debate" is pipeline handoff wording. "Were located" / "located" describes the model's search process rather than the issuer, which does not meet the reader-language rule.
   - Fix: State the conclusion directly (e.g. "Air-travel regulation is the one ESG factor to watch, through aftermarket revenue"), and put search scope in limitations as "not disclosed in the FY2024 annual filing".
5. **Medium · visual** (Auditor, New reader)
   - Where: Screenshot CP-2E_s-94.png, crop (340,210)-(1400,420) at /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2E-105-a.png; handoff L97 "Basis: TDG_2024-09-30_10-K_..., pages 24–26"
   - Problem: The handoff has a Basis line for this paragraph (L97), but nothing shows between the paragraph and the "Events: Hedges" heading: no Basis line and no Basis chip, unlike the table rows below. On screen the paragraph has no visible source.
   - Fix: Render the paragraph's Basis line, or a Basis affordance, under the prose as the table rows already do.
6. **Low · visual** (Auditor)
   - Where: Screenshot CP-2E_s-94.png crop region above: "at least a 50% Scope 1" (only "50%" in monospace with a dotted underline); "at 2024-09-30" in plain text
   - Problem: Only one figure in the paragraph is styled as a value chip. The dates 2031 and fiscal 2019 are plain, and the prose date is ISO (2024-09-30) while the page header says "30 September 2024". The inconsistent typography makes the reader ask why one number is special.
   - Fix: Apply one consistent value style to every figure and date in the paragraph, and use the header's date format in the prose.

### Events: Hedges

Kind: timeline · handoff lines 99-110 · verdict **CONCERNS**

- Narrative: The figures agree with each other (USD 77.89m and 91.89m sensitivity steps; collar notional of USD 2,888m), but the section has no bottom line, overstates the collar cover at 2025-09-30, and leaks 'lane' and module wording. Not verified: the figures were checked against the module's own Macro and hedging view, not against page 176 of the 10-K.
- Visual: The timeline is drawn as five unlabelled, same-styled dots with no as-of marker, and the events table spends its width on constant columns and repeated raw file names while the dates wrap.

1. **High · visual** (Saboteur, Auditor)
   - Where: Timeline panel, 'Hedges' row: CP-2E_timeline.png crop (340,200)-(1440,320), saved at /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2E-106-a.png
   - Problem: The timeline shows five identical blue dots. Only the two end dates (2023-03-31, 2027-09-30) are labelled, and there is no as-of (2024-09-30) marker. Nothing separates the historical start from the four scheduled expiries, and the points carry no event text or notional, so a reader cannot see the 2025 swap cliff or the 2027 end of the hedge book, which are the point of this section.
   - Fix: Label each point with its date and a short event (such as 'USD 2,000m swaps mature'), mark the as-of date, and style historical and scheduled events differently.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: L101: "Notional is shown for identification only; it is not effectiveness or fair value."
   - Problem: The section opens with a caveat and gives no judgement. The credit message (fixed hedges end 2025-09-30 and all hedges end 2027-09-30, before the 2028-2032 term loans) appears only in the last cells of the table's last column.
   - Fix: Open with one bottom-line sentence on the hedge cliff and its timing, then the caveat, then the table.
3. **Medium · narrative** (Saboteur)
   - Where: L107: "Last fixed-rate hedge ends; all floating debt exposed inside collar band"
   - Problem: This overstates the collar cover. On the module's own figures, about USD 7.8 billion is floating, and collars at that date cover only USD 2,938 million. The remaining debt has no floor or cap at all, so 'all floating debt' being 'inside collar band' is wrong for most of the exposure.
   - Fix: State that the USD 2,938 million under collars is protected only above the cap, and that the rest of the floating debt is fully unhedged.
4. **Medium · narrative** (Auditor, New reader)
   - Where: L109: "...term loans maturing 2028 to 2032 and the FY2028 maturity wall in the CP-1 lane" (rendered as "in the Financial foundation lane")
   - Problem: 'lane' is pipeline vocabulary, and the handoff names a module code. On screen the reader is sent to an internal module rather than given the fact (the module puts the FY2028 wall at USD 6,637 million).
   - Fix: Give the FY2028 maturity amount directly and drop the module and lane reference.
5. **Medium · visual** (New reader, Auditor)
   - Where: Events: Hedges table, Event date / Date precision / Published / Source columns: CP-2E_s-99.png crop (340,220)-(1440,560), saved at /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2E-106-b.png
   - Problem: The narrowest column holds the dates, which break mid-value ('2023-03-' / '31 Basis'). Meanwhile 'Date precision' ('day' in every row) and 'Published' ('—' in every row) take width while carrying no information. The Source column repeats the same raw file name 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl' five times over five or six lines, which makes every row tall.
   - Fix: Drop the constant columns, keep dates on one line, and show the source as a short label such as 'FY2024 10-K, p.176'.
6. **Low · narrative** (New reader)
   - Where: L105: "Historical — effective date of the interest rate swap and cap agreements"
   - Problem: The Status cells repeat the Event text ('maturity date and effective date per hedge table'), so each row is read twice for no new information.
   - Fix: Reduce Status to 'Historical' or 'Scheduled'.
7. **Low · visual** (Auditor)
   - Where: Timeline panel header 'Dated events by module': CP-2E_timeline.png crop at /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2E-106-a.png
   - Problem: 'by module' is pipeline wording shown to the reader. The timeline also sits in a separate panel far above this table.
   - Fix: Use a reader caption such as 'Hedge start and expiry dates' and place the timeline beside the events table.

### Calculations register

Kind: prose/table · handoff lines 305-338 · verdict **CONCERNS**

- Narrative: The arithmetic I checked is correct: the M02, M09, M11, M12, M22 and M24 sums all hold. The problems are traceability. One input is unlabelled (4,600). The trailing derivative sentence points to the wrong row, and the calculation it describes is missing from the register. Internal confidence-scoring rows and other modules' calculation IDs leak to a reader who has not seen the sources.
- Visual: This is a dense 27-row table with no chart. Result typography is inconsistent (bold mono USD without separators next to plain 10-decimal fractions), a 'Basis' tag repeats on every row, and the whole register is repeated immediately below as a second table.

1. **High · narrative** (Saboteur, Auditor)
   - Where: L337: "Net derivative asset of USD 47 million ... less USD 10 million liability (page 177), stated as calculation M21's companion figure; no other new arithmetic was performed."
   - Problem: The 57 − 10 = 47 subtraction is not in the register, and it is tied to M21 (FX forwards / net sales, L329), which has nothing to do with the derivative asset. The page citation also sits inside a narrative sentence. A reader who checks the contrary-evidence figure is sent to the wrong row, and the claim 'no other new arithmetic' is contradicted in the same sentence.
   - Fix: Add the net derivative position as its own numbered register row with its source in the Inputs column, and remove the false cross-reference and the in-sentence page citation.
2. **Medium · narrative** (New reader, Saboteur)
   - Where: L330-331: "M22 | Secured notes | ... = 11000" / "M23 | Fixed notes / total debt | (11,000 + 4,600) / 25,068"
   - Problem: The 4,600 input in M23 has no label or origin in the register (it is the subordinated notes figure from L127/L154). M23 also treats 'Secured notes' (M22) as all fixed-rate without saying so. A reader cannot check the 62.23% fixed share from this table.
   - Fix: Name and source every input in the Inputs column (e.g. 'subordinated notes 4,600, Financial foundation') and say that the secured notes counted here are fixed-coupon.
3. **Medium · narrative** (New reader, Auditor)
   - Where: L333-335: "M25 | Evidence score E | sum of claim weights 9.1 over 10 claims" ... "M27 | (M26) × S 0.7 | 620.2 / 10 | 62.02 (score 62)"
   - Problem: Rows M25 to M27 are the pipeline's internal confidence-scoring formula: E, C and S are undefined, C = 85 never appears, and M27's input '620.2 / 10' does not match its formula '× 0.7'. This is internal machinery mixed in with the credit arithmetic.
   - Fix: Move the confidence-score arithmetic out of the reader-facing credit register, or define E, C and S and show the inputs that match each formula.
4. **Medium · narrative** (Auditor, New reader)
   - Where: L312: "5,789 / 25,068 (CP-1 C01)" rendered as "(Financial foundation C01)"; also L322-323 "C15", "C28"
   - Problem: The module name is translated on screen, but another module's internal calculation IDs (C01, C15, C28) still reach the reader, in a small monospace chip. A reader cannot resolve them without going to another page.
   - Fix: Name the figure instead of its ID, e.g. 'total debt 25,068, Financial foundation'.
5. **Medium · visual** (Auditor, New reader)
   - Where: Calculations register table, shots2/CP-2E_s-305.png rows y≈260-1110 (crop tmp/CP-2E-111-a.png), Result and Unit columns
   - Problem: The Result column mixes styles. USD values are bold monospace with no thousands separator ('9189', '11000'), while the Inputs column next to them shows '9,189'. Ratios are plain text with 10-decimal fractions plus a percentage, with the Unit shown as 'fraction'. Results are left-aligned, so magnitudes cannot be scanned.
   - Fix: Show results in one right-aligned numeric style with thousands separators, ratios as percentages to two decimals, and units that match.
6. **Medium · visual** (New reader, Saboteur)
   - Where: shots2/CP-2E_s-305.png: register (y≈200-1125) immediately followed by 'Calculations' table (y≈1195 onward) repeating M01-M27
   - Problem: The same 27 calculations appear twice in a row, under different units (fraction vs %) and different labels. That doubles the scroll length, and the reader has to work out whether the two tables agree. The second table's intro is also pipeline language ('calculate tool', 'Helper scripts were not run in this transport').
   - Fix: Show a single register that carries both the plain-language item label and the formula, and drop the transport/tool wording.
7. **Low · narrative** (New reader)
   - Where: L327: "2,900 / 7,940 (pages 26; CP-1)"; L317: "M01 − remaining swap − cap"
   - Problem: There is a typo ('pages 26'), and the shorthand 'remaining swap − cap' does not say which instruments roll off or when. The plain-language label for that row appears only in the duplicate table ('Unhedged after 2025-03-31').
   - Fix: Fix the citation and put the dated description of the instruments in the Formula cell.
8. **Low · visual** (Auditor)
   - Where: Register ID column, shots2/CP-2E_s-305.png x≈310-370, every row 'M01 Basis' ... 'M27 Basis'
   - Problem: Every row has a grey 'Basis' tag that carries no information. Repeated 27 times, it is visual noise in the ID column.
   - Fix: Remove the tag, or show it only where it links to a distinct basis.

### Gaps

Kind: prose/table · handoff lines 373-386 · verdict **CONCERNS**

- Narrative: This is a ledger table with no judgement-first lead. Its rows carry module codes, the word \"handoff\", jargon and unquantified effects, so the reader cannot tell which gap threatens the hedge-cliff view.
- Visual: There is no chart in this section. The table has clean rules and spacing, but long raw source file names in the Source column, inline \"Basis\" chips that appear on some rows only, and garbled code-to-name text make it hard to scan.

1. **High · narrative** (Auditor, New reader)
   - Where: Handoff lines 383 and 385: "T2F.2 coupon cells summarised | CP-4 or CP-3 to confirm | Financial data foundation (CP-1)" and "CP-2C governance handoff not supplied". Rendered in CP-2E_s-373.png, Gaps table rows 7 and 9.
   - Problem: The module writes internal register and module codes, and the screen's code-to-name substitution turns them into garbled text: "a method step coupon cells summarised", "Business & governance governance handoff not supplied" and "Financial data foundation (Financial foundation)". The pipeline word "handoff" also reaches the reader. Both break the house rule against pipeline wording.
   - Fix: Write these rows in reader language, for example "Coupons summarised from the financial data, not re-checked note by note" and "Governance review not available for this run", with no codes left for the screen to substitute.
2. **Medium · narrative** (Saboteur)
   - Where: Line 378: "Management's about USD 30 million sensitivity unreconciled | Sensitivity is a range | Issuer explanation"
   - Problem: The effect says the sensitivity "is a range" but gives neither the range nor its basis (USD 30 million from management against USD 57.89m to USD 91.89m per 100 bp from the module, a difference of 27.89m). A committee reader cannot tell how much the gap matters. "Management's about USD 30 million" is also ungrammatical.
   - Fix: State the two figures, their unit and period (USD m of annual interest per +100 bp) and say which one the module relies on.
3. **Medium · narrative** (Saboteur)
   - Where: Line 380: "Post-period hedge activity not located | Cliff dates as of year end only | Read FY2025 quarterly derivatives notes | TDG_2024-12-28_10-Q_...jsonl"
   - Problem: The Source cell names a FY2025 10-Q, yet the gap says post-period activity was "not located" and the action is to read the FY2025 quarterly notes. The reader cannot tell whether that 10-Q was read, and so whether the March 2025 hedge cliff still holds.
   - Fix: Say plainly whether the Q1 FY2025 10-Q was read and found silent or was not read, and leave the Source cell empty if it was not read.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 379: "Term SOFR at as-of not in sources | Collar moneyness unknown | CP-DR market data, labelled external | context"
   - Problem: Without the rate level the reader cannot tell whether the collars were in the money, which bears directly on the hedge-cliff conclusion, yet the row is given the same weight as ESG polish. The rows are not ordered by credit impact. "Moneyness" and "as-of" are jargon, and the action renders as "Research questions market data", which is not something a reader can do.
   - Fix: Order the gaps by effect on the credit view, write the effect in plain terms (whether the hedges were paying out at year end is unknown) and state the action as an outside data need.
5. **Medium · narrative** (Auditor)
   - Where: Lines 383-385 Action cells: "CP-4 or CP-3 to confirm" (rendered "Legal & covenants or Security selection to confirm") and the Source cell "context" (lines 379, 385)
   - Problem: The Action column routes work between modules instead of telling the reader what evidence is missing. "context" in the Source column cites no document, so it is not a source.
   - Fix: State actions as the evidence needed (for example "Indenture coupon schedule"), and mark source-less rows "No source document" rather than "context".
6. **Medium · visual** (New reader, Auditor)
   - Where: Gaps table, Source column, CP-2E_s-373.png, crop CP-2E-113-a.png, y about 1630-2250 original px
   - Problem: Raw file identifiers such as "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176" wrap over two lines in most rows. They take the widest column and mean nothing to a portfolio manager.
   - Fix: Show a short document label in the Source column (for example "FY2024 10-K, p. 176") and keep the file identifier in a tooltip or on the Evidence page.
7. **Low · visual** (Auditor)
   - Where: Gaps table, Gap column, CP-2E-113-a.png: grey "Basis" chips after rows 1, 2, 5, 6 and 8 only
   - Problem: An unexplained "Basis" tag sits inline after some gap descriptions and not others. It reads like a stray word in the sentence.
   - Fix: Drop the chip in tables that already have a Source column, or show it the same way on every row with a clear affordance.

### Bottom line

Kind: reader passage · handoff lines 36-43 · verdict **CONCERNS**

- Narrative: The passage opens with its judgement ('Moderate macro and hedging sensitivity') and keeps sources out of the sentences, but its numbers describe the static hedge book while the stated risk is the 2025 to 2027 hedge cliff, and it brings in a post-period dividend without giving the amount or the base.
- Visual: This section has no chart; the bottom line is set entirely in large bold display type, its heading is hidden under the sticky bar when the page is scrolled to it, and neither paragraph shows a Basis link.

1. **Medium · narrative** (Saboteur)
   - Where: line 38: "a 100 bp rise in Term SOFR adds about USD 57.89 million ... even the higher figure is 3.08% of FY2024 free cash flow and 1.98% of pro forma liquidity"
   - Problem: The bottom line names the hedge cliff as the risk, but its only numbers are for the static year-end hedge book. The forward exposure that the thesis depends on (USD 77.89m / 4.14% after March 2025 and USD 91.89m / 4.89% after September 2025, line 50) appears only in Key findings, so a reader who stops here takes away the smallest number.
   - Fix: Put the post-roll-off sensitivity (USD 91.89 million, 4.89% of FY2024 free cash flow, from October 2025) next to the year-end figure in the bottom line, since the conclusion rests on it.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: line 38: "lands on a liquidity base already cut by the October 2024 special dividend ... 1.98% of pro forma liquidity"
   - Problem: The passage mixes a post-period event (October 2024 dividend) into a 30 September 2024 bottom line without saying how big the dividend was or what 'pro forma' adjusts for, although the module's own scope says subsequent events are 'flagged and not blended' (line 16). The reader cannot tell what the 1.98% is measured against.
   - Fix: State the dividend amount and the liquidity base it is measured against (the year-end figure and the pro forma figure), and label the pro forma figure clearly as a post-period adjustment.
3. **Medium · visual** (Auditor, New reader)
   - Where: CP-2E_bottom-line.png, content column y≈190–700 (crop CP-2E-100-a.png)
   - Problem: The whole bottom line, about 210 words in two paragraphs, is set in large bold display type, which makes a wall of heavy text roughly 500 px tall. The first sentence alone is 69 words. Bold is supposed to signal the judgement, but here it applies to everything, so the one-line verdict ('Moderate macro and hedging sensitivity') does not stand out.
   - Fix: Keep only the opening verdict sentence in display weight and set the supporting figures and the FX/commodity paragraph in body type, or split the first sentence into two.
4. **Medium · visual** (Auditor)
   - Where: CP-2E_bottom-line.png and crop CP-2E-100-a.png, top of content column (y≈180–200) and the end of both bottom-line paragraphs
   - Problem: With the page scrolled to this section, the 'Bottom line' heading is hidden under the sticky run bar, where clipped chips are also visible at the right. Neither bottom-line paragraph shows a Basis link, even though the handoff has Basis lines (lines 39, 42) and a 'Basis' link is rendered after the last key finding. The reader cannot get to the source for the headline figures.
   - Fix: Offset the anchor scroll so the heading clears the sticky bar, and show the Basis link after each bottom-line paragraph as the Key findings do.
5. **Low · narrative** (New reader)
   - Where: line 38: "adds about USD 57.89 million of annual cash interest on our calculation, against management's own figure of about USD 30 million"
   - Problem: 'About' paired with two-decimal precision overstates how precise a figure that is simply 100 bp times USD 5,789 million can be. The bottom line also leaves the conflict with management's figure, nearly double, unexplained, and does not point to the later finding that the gap is unexplained.
   - Fix: Round to about USD 58 million and add a few words saying the gap with management's figure is unexplained and treated as the downside case.
6. **Low · narrative** (Auditor)
   - Where: CP-2E_bottom-line.png left 'On this page' nav (outside this section): "Upstream re-anchor and method trace", "a method step Source register"
   - Problem: Pipeline vocabulary ('re-anchor', 'method step', 'register') appears on screen next to this section, which breaks the house language rule. It sits outside the reviewed passage, so it is not counted against the section.
   - Fix: Relabel these nav entries in reader language or hide them from the reader view.
7. **Low · visual** (Auditor)
   - Where: CP-2E_bottom-line.png, inline figures in bottom line (e.g. 'USD 5,789 million', '1.98%')
   - Problem: Figures switch into monospace with a dotted underline inside bold proportional display type, which breaks the line rhythm at large size (e.g. '1.98%' at a line start). The column also uses only about 560 px of the 1440 px viewport and leaves a large empty area on the right.
   - Fix: Use tabular-figure styling in the running font for inline numbers within display-size passages, or reduce the emphasis styling at that size.

### Key findings

Kind: reader passage · handoff lines 44-60 · verdict **CONCERNS**

- Narrative: The judgements are present and the arithmetic reconciles: 5,789 = 9,189 - 3,400, 37.00%, 23.09%, and 3.08% / 4.14% / 4.89% of USD 1,880 million FCF. The problems are a mislabelled margin period, spurious precision with \"about\", circular or accounting-first lead sentences, and an undefined 3.60x cover.
- Visual: There is no chart in this section. The page is long bulleted prose with many dotted-underlined monospace figure buttons: readable at full resolution but dense. Basis controls are inconsistent (shown only on figure-free paragraphs, by design in reader.js:306-324), and the page has wide unused right-hand space.

1. **Medium · narrative** (Saboteur)
   - Where: Line 56: "a risk greater in the high-inflation years FY2023 and FY2024; yet the EBITDA As Defined margin rose from 51.56% to 52.56% across that period"
   - Problem: In the CP-2 handoff, 51.56% is the FY2023 margin and 52.56% is FY2024. That is a single year-on-year change, yet this bullet presents it as evidence across both inflationary years (and line 41 says "margins expanded through two inflationary years"). The reader gets an overstated case that pricing offsets inflation.
   - Fix: Name the periods exactly (FY2023 51.56% to FY2024 52.56%, one year) and add the FY2022 margin, or limit the claim to one year.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 50: "a 100 bp move inside the collar band costs about USD 77.89 million a year"; line 52: "disagree by USD 27.89 million"; line 38: "adds about USD 57.89 million"
   - Problem: The figures are just 1% of principal, but they carry two decimals and the word "about". That signals a precision the estimate does not have, and a USD 27.89 million "disagreement" with management's rounded "about USD 30 million" looks exact when it is not. The unconditional "costs" also leaves out the Limitations caveat that the Term SOFR level, and so where rates sit in the band, is unknown.
   - Fix: Round to about USD 58 / 78 / 92 million, state the gap as roughly USD 28 million, and add "if Term SOFR stays inside the band" where each figure first appears.
3. **Medium · narrative** (Saboteur, Auditor)
   - Where: Line 48: "Hedge effectiveness is supported only to 2025, after which protection becomes conditional and then ends before the debt it covers."
   - Problem: The bullet opens on the accounting term "hedge effectiveness", and its own last sentence says that designation is not proof of economic coverage, so the lead contradicts the closing point. "Conditional" is never explained, and the collars' floors (2.00% / 2.50%), which make falling rates a cost, appear only later in Contrary evidence.
   - Fix: Lead with economic coverage (fixed protection ends 2025-09-30; after that, only collar ceilings until 2027-09-30, against term loans to 2028-2032), and name the floors in this bullet.
4. **Medium · narrative** (New reader)
   - Where: Line 46: "The largest unhedged exposure is the term-loan and securitization floating base that is not covered by swaps or the cap."
   - Problem: The lead sentence is circular (the unhedged exposure is the part not hedged). It gives neither the size nor the credit consequence, so the judgement only arrives four figures later. The rest of the bullet is a reconciliation ("fixed-equivalent share we derive, 76.91%") rather than a finding.
   - Fix: Open with the judgement and the number, e.g. USD 5,789 million (23% of debt) floats unhedged at year end, then give the arithmetic.
5. **Medium · narrative** (New reader)
   - Where: Line 50: "The mechanism for creditors is a slow erosion of the 3.60x cash interest cover, not a liquidity break."
   - Problem: 3.60x is not defined here (CP-2 defines it as EBITDA As Defined / net cash interest, FY2024), and the bullet never says how far the cover falls under the 77.89 or 91.89 million cases. The conclusion "slow erosion" is therefore asserted, not shown.
   - Fix: Give the ratio's definition and period, plus the resulting cover under the post-swap case, in one clause.
6. **Low · narrative** (New reader, Auditor)
   - Where: Line 54: "approximately USD 2.9bn, 36.52% of net sales ... forwards of USD 120 million ... cover 4.14% of foreign sales"; line 58: "in the pages read"
   - Problem: Units mix (bn vs million throughout), an approximate base carries a two-decimal ratio, and 4.14% also appears on line 50 for a different ratio (share of free cash flow). "In the pages read" and "covenant-currency mismatch" are process and analyst shorthand rather than reader language.
   - Fix: Use USD million consistently, round ratios built on approximate bases, and replace "in the pages read" with "in the FY2024 10-K".
7. **Low · visual** (New reader, Auditor)
   - Where: Key findings bullets 1-2, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2E-101-a.png (shot region x330-1440, y220-860)
   - Problem: Bullets of 90-110 words carry up to 14 dotted-underlined monospace figure buttons each. The mixed monospace/proportional type breaks the reading line, and a line wrap strands an opening parenthesis ("USD 9,189 million (" / "USD 8,702 million"). Six bullets have no visible Basis control, and only the last, figure-free bullet shows one, so a reader cannot tell that the sources for the qualitative claims (e.g. "most contracts do not permit recovery") sit behind the figure buttons.
   - Fix: Keep figures in the body typeface with a subtle underline, prevent a figure button from wrapping away from its parenthesis, and give each bullet a consistent way to reach its Basis.
8. **Low · visual** (Auditor)
   - Where: CP-2E_key-findings.png, whole Key findings block (display y190-1200)
   - Problem: The prose column is about 550 px wide on a 1440 px page, and roughly 340 px of empty space sits to its right. Seven dense bullets have no bold lead-in, so the section reads as a wall of text that a reader cannot scan for the seven conclusions.
   - Fix: Bold each bullet's opening judgement sentence (as the CP-2 handoff does) so the findings can be scanned down the left edge.

## Legal & covenants (CP-4)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-4/aeddb90620d1f11de1d6c90e8ee119663ad970b6bcc0515e5c98b3850c3f6dd1/1.response.md`

### Sources

Kind: prose/table · handoff lines 5-20 · verdict **BLOCK**

- Narrative: The Sources section is data. It is complete and keeps source references where they belong (no references in narrative sentences, no CP codes on screen), but it uses pipeline language a portfolio manager would not recognise: 'Supplied handoff', 'context', 'Run settings', 'Legal file gate', 'per source readiness'. It also lists sources by their internal filenames.
- Visual: Two stacked tables with different column grids, where the sha256 hash columns take most of the width. The filenames wrap over four lines and the useful 'Use in this module' text is squeezed. Contrast and spacing are otherwise clean, and nothing is clipped.

1. **High · narrative** (Auditor, New reader)
   - Where: line 13: "| Supplied handoff | Module | sha256 |" (rendered as the table header "Supplied handoff" in CP-4_s-5.png, second Sources table, y~505 at display scale)
   - Problem: "Handoff" is pipeline vocabulary, which the house standard bars from reader-facing text, and it appears as a visible column header. A portfolio manager cannot tell what a "supplied handoff" is or why it sits among the sources. Two personas caught it, so it is promoted from Medium.
   - Fix: Label the table in reader terms (for example 'Earlier analysis relied on') and drop the pipeline wording.
2. **High · narrative** (Auditor, New reader)
   - Where: line 11: "| context | f7b95e1ff471... | Run settings: legal documents flagged \"executed\" but no document attached; not issuer evidence |"
   - Problem: An internal run-configuration row ('context', 'Run settings', 'flagged') is listed as a source. This is pipeline state, not evidence the reader can check, and a committee member cannot make sense of 'flagged executed but no document attached'. Two personas caught it, so it is promoted.
   - Fix: Leave run configuration out of the reader's Sources table; if the missing executed documents matter, state that as a limitation in plain words.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 9: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" and line 10: "TDG_2024-12-28_10-Q_0001260221-25-000014_tdg-20241228.htm.jsonl"
   - Problem: Sources are named by internal ingest filenames (accession number plus .htm.jsonl) rather than as documents, for example 'FY2024 annual report (10-K), filed Nov 2024'. The reader has to decode a file path to learn what was read.
   - Fix: Show each source as document type, fiscal period and filing date, and keep the filename only as a secondary reference if one is needed.
4. **Medium · narrative** (Auditor)
   - Where: line 9: "Legal file gate: exhibit index (credit agreement, amendments, guarantee and collateral agreement, indentures incorporated by reference only)..."
   - Problem: 'Legal file gate' is method vocabulary (the house standard lists 'gate' as non-reader language) and it opens the column that tells the reader what the source was used for.
   - Fix: Describe the use in plain terms, for example 'Checked whether the executed debt documents are in the filing; filing summaries of covenants, guarantees and ranking'.
5. **Medium · visual** (New reader, Saboteur)
   - Where: Sources table, sha256 column, CP-4_s-5.png region x 470-880, y 220-475 (display scale)
   - Problem: Each 64-character hash takes about 35% of the table width. That pushes the 'Use in this module' column into a narrow wrap and splits the source filenames over four lines, so the only reader-useful content is squeezed by audit data the reader never uses.
   - Fix: Remove the hash from the reader view, or shorten it to a few characters or a tooltip, and give the width to the source's name and its use.
6. **Low · narrative** (Saboteur)
   - Where: line 19: "Not relied on: the Q2 and Q3 FY2024 quarterly filings and the PDF annual report (duplicate per source readiness)."
   - Problem: 'Per source readiness' points the reader to another module to understand why filings were excluded. It also never says that the 10-Q that was relied on (period ending 2024-12-28) falls after the 2024-09-30 as-of date.
   - Fix: Say in plain words that the excluded filings duplicate the annual report or predate it, and mark the December 2024 10-Q as a post-period check.
7. **Low · visual** (New reader)
   - Where: Supplied-handoff table, Module column, CP-4_s-5.png y 530-585 (display scale): "Source readiness | Source readiness", "Financial foundation | Financial foundation", "Business and transaction fact pack | Business & governance"
   - Problem: The Module column repeats the first column in two rows and contradicts it in the third ('Business and transaction fact pack' vs 'Business & governance'). That spends a whole column and makes the reader wonder whether these are two different things.
   - Fix: Keep one name per row that matches the left navigation label.

### Events: Legal

Kind: timeline · handoff lines 58-63 · verdict **BLOCK**

- Narrative: The section adds no analysis. Its one sentence of prose (line 62) uses pipeline words ('lanes', 'fact pack', 'settled') and gives a reason that does not apply to event dates. It also leaves out a covenant-affecting amendment the module itself dates 2024-03-22, so a missing timeline reads as an empty one.
- Visual: There is no drawn timeline. The table and the Timeline panel are both empty states: a seven-column grid filled with the same repeated placeholder and an orphan Basis chip, and a small grey 'Not established for this run' row whose heading collides with the bottom-line text above it. The supplied timeline screenshot scrolled past the panel, so I judged the panel from my own headless render.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 62: "Not supplied: amendment and issuance dates are already recorded in the source readiness and fact pack lanes; no legal event is settled here"
   - Problem: The section leaves the legal timeline empty even though the same module's Legal file gate gives a dated legal event ("Most recent covenant-affecting amendment dated 2024-03-22", shown on screen in CP-4_timeline.png) and says the 10-K lists the note issuances. A committee reading the timeline sees "Not established for this run" and may conclude that no recent amendment or refinancing exists. Missing is presented as if it were none.
   - Fix: List the filing-dated events the module already holds (the 2024-03-22 amendment and the note issuances), each with its 10-K Source cell and the Status 'unverified issuer summary', and keep 'not assessable' for the provision-level content only.
2. **High · narrative** (Auditor, New reader)
   - Where: line 62: "already recorded in the source readiness and fact pack lanes; no legal event is settled here"
   - Problem: "lanes", "fact pack", "source readiness" and "settled" are pipeline vocabulary, which the house standard bars from reader text. They also send the reader to other pages to find the events, so the section cannot be read on its own.
   - Fix: Say in plain words what is absent and why (for example, 'No legal events dated: the executed agreements are not in the source set'), with no references to internal stages.
3. **Medium · narrative** (Saboteur)
   - Where: line 62, Event date / Date precision / Published / Event / Status / Source cells: "Not supplied: not assessable, no executed governing document available"
   - Problem: The stated reason is wrong for this table. Event dates (amendments, issuances, maturities) come from public filings and do not need the executed credit agreement, so the caveat shuts off evidence the module had. A reader takes the missing executed documents as a reason that does not hold here.
   - Fix: Give the reason that applies to event dating, or none if the events are listed, and keep the 'no executed document' limitation for the covenant reading.
4. **Medium · visual** (New reader, Auditor)
   - Where: Events: Legal table, CP-4_s-58.png, region x 296-1158, y 215-365 (displayed); crop scratchpad/tmp/CP-4-120-c.png
   - Problem: The same 13-word placeholder is repeated in six of seven columns, wrapping to six lines per cell. The result is a dense block that carries one fact. A 'Basis' chip is attached to a placeholder in the Event date cell, so it points to evidence for a value that does not exist.
   - Fix: When the table has no rows, show one full-width line ('No dated legal events established') with its reason, and drop the empty seven-column grid and the orphan Basis chip.
5. **Medium · visual** (Auditor)
   - Where: Timeline panel, rendered scratchpad/tmp/CP-4-120-top.png (crop scratchpad/tmp/CP-4-120-b.png): "Timeline" heading directly under the last line of the bottom-line paragraph
   - Problem: The Timeline heading sits flush against the large bold bottom-line text with no top margin, so it reads as part of that paragraph. The panel is also only a single 'Not established for this run' row in small grey type, which is easy to miss. The supplied timeline-route screenshot (CP-4_timeline.png) scrolled past the panel, so the panel itself is not visible in it.
   - Fix: Add section spacing above the Timeline heading, matching the spacing above Maps and Request, and make the empty-state line readable at body size.
6. **Low · narrative** (New reader)
   - Where: line 60 headers: "Date precision | Published | ... | Status"; section title "Events: Legal"; panel label "Dated events by module"
   - Problem: "Date precision", "Published" and "Dated events by module" are schema labels with no meaning for a portfolio manager, and "Events: Legal" reads like an internal field name rather than a heading.
   - Fix: Use reader headings such as 'Legal and financing events' and 'Date', and drop 'by module' from the panel label.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 105-108 · verdict **CONCERNS**

- Narrative: Both passages are run plumbing: line 3 is the request sent to the module and lines 105-107 are an instruction to the next modules. They read as pipeline text, not as credit writing for a committee reader. The useful caveat (treat covenants as unassessed, not benign) is already in the bottom line at line 24.
- Visual: The section has no chart, map or timeline, only two plain full-width paragraphs. They render legibly with no clipping or contrast problem; the one visual issue is that the Request block sits mid-page with the same heading weight as the analysis.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 3: "with its absorbed restricted-group, intercreditor and covenant-capacity phases ... Pathway: credit_snapshot. Scope is ... gated on an executed credit agreement or indenture being in the source set." (shown as-is in CP-4_s-1.png, Request block)
   - Problem: The text on screen uses pipeline vocabulary: "absorbed ... phases", the snake_case pathway code "credit_snapshot", "gated" and "source set". This breaks the house rule that pipeline wording stays off the page. A portfolio manager cannot tell what an "absorbed phase" or a "gate" means.
   - Fix: Show the request in reader language, e.g. "Legal and covenant review of TransDigm as of 30 September 2024 (credit snapshot); requires the signed credit agreement or indentures", or keep this run metadata off the Modules page.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 105-107: "## Next module ... The next selected modules (relative value, evidence trace, committee debate) should treat every covenant ... as unassessed ... this module should be rerun once..."
   - Problem: This whole passage is an instruction from one module to the next, shown to the reader under a pipeline heading ("Next module", also listed in On this page). Its module names also differ from the library's navigation labels (Security selection, Evidence validation, Committee decision), so the reader cannot match "evidence trace" or "committee debate" to any page.
   - Fix: Keep the module-to-module note off the reader page, or retitle it as a reader action ("What would change this view: the documents to obtain") and use the library's own module names.
3. **Medium · narrative** (Saboteur)
   - Where: Line 107: "rely only on the filing summaries flagged above"
   - Problem: Line 25 labels these summaries "unverified issuer summary ... not as a legal conclusion". Here they are the one thing downstream readers are told to rely on, with no word that they are unverified. A committee member reading only the closing paragraph could treat the 7.25x/5.00x/7.50x figures as tested covenant terms.
   - Fix: Repeat the qualifier where the summaries are mentioned, e.g. "rely only on the unverified issuer summaries in the legal file table".
4. **Low · narrative** (New reader)
   - Where: Line 107: "rely only on the filing summaries flagged above"
   - Problem: "Flagged above" points the reader somewhere vague. The summaries sit several screens up, in the Legal file gate table, under its "Filing-summary content held for the next run" column.
   - Fix: Name the table and column the reader should look at.
5. **Low · visual** (Auditor)
   - Where: CP-4_s-1.png, Request heading and paragraph (approx. y 190-260 display px) sitting between Maps and Sources; On this page list entries "Request" and "Next module"
   - Problem: The run-metadata paragraph (Request) gets the same heading weight and position as the analytical sections. It appears mid-page, after the bottom line, timeline and maps, as if it were a finding. The reader gets no visual signal that this is run context rather than analysis.
   - Fix: Show the request as a small, muted context line at the top of the module, or in a collapsed metadata strip, not as a peer heading in the reading order.

### Bottom line

Kind: reader passage · handoff lines 23-30 · verdict **CONCERNS**

- Narrative: The judgement comes first (\"Not assessable\") and the facts are correct (6,294 / 0.7927 ≈ 7,940, which leaves 1,646 in non-guarantors), but pipeline vocabulary (gate, method, run settings, transport, next run) and very long sentences bury the no-comfort warning and the subordination point.
- Visual: The section has no chart. It is laid out as about 230 words of large bold type, its heading is hidden under the sticky header, the Basis chip for the paragraph that holds the figures is missing, and the Timeline heading sits too close below it.

1. **High · visual** (Auditor, Saboteur)
   - Where: Handoff line 29 "Basis: TDG_2024-09-30_10-K_..., pages 22, 58–59, 61–62; calculation L1; calculation L2"; screenshot CP-4_bottom-line.png, crop of y≈1000–1120 (scratchpad/tmp/CP-4-116-a.png and CP-4-116-b.png)
   - Problem: The second paragraph carries the section's only figures (7.25x, 5.00x, 7.50x, USD 364 million, 79.27%, USD 1,646 million), and the handoff gives it a Basis line. On screen the paragraph ends at "but they cannot size either." with no Basis chip, and the "Timeline" heading follows straight after. Only the first paragraph shows its Basis chip, so the reader cannot trace any of the numbers.
   - Fix: Render a Basis chip for every paragraph that has a Basis line in the handoff, including the last paragraph of a section.
2. **Medium · narrative** (New reader, Auditor)
   - Where: Line 25: "the method's legal file gate is blocking ... the acquisition route the method offers for public filers (pulling the exhibits from EDGAR) cannot be used in this transport"
   - Problem: Pipeline wording reaches the reader: "method", "legal file gate", "source set", "run settings" and "transport". The house standard names "gate" as non-reader language. A credit committee member learns why the pipeline stopped, not why the documents are unavailable.
   - Fix: Say in plain terms that the executed loan and note documents were not provided and could not be retrieved, and drop the gate, transport and run-settings vocabulary.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: Line 25: "Not assessable: no executed governing document available. The source set holds no executed credit agreement, amendment, guarantee ... cannot be used in this transport." (one paragraph, ~110 words, one 75-word sentence)
   - Problem: The one judgement that matters to a creditor, "creditors must not treat the absence of a legal finding as comfort", sits at the end of a 75-word sentence after a list of missing documents and a description of process. The paragraph then ends on a process detail.
   - Fix: Open with "Not assessable" and the no-comfort warning as two short sentences, then give the list of missing documents.
4. **Medium · narrative** (New reader, Auditor)
   - Where: Line 28: "What the filing itself says is held below as unverified issuer summary, for the next run to test against the executed text, not as a legal conclusion"
   - Problem: "Held below" and "for the next run to test" are workflow wording: the reader is not running the next run, and "below" points to nothing in this paragraph. The qualifier is stacked three times before the first fact, which buries the facts on structural subordination and covenants.
   - Fix: Lead with the key fact, for example "USD 1,646 million of sales sit in non-guarantor subsidiaries, structurally ahead of all notes", and give the "issuer summary, not verified against the documents" qualifier once.
5. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-4_bottom-line.png, y≈190–1080 (whole Bottom line block); crop scratchpad/tmp/CP-4-116-a.png
   - Problem: Both paragraphs, about 230 words, are set in large bold display type across about 900 px. That is a wall of heavy text, and nothing on the screen separates the verdict ("Not assessable") from the supporting detail. The "Bottom line" heading is hidden under the sticky run bar when the page is scrolled to this anchor, so the section has no visible title.
   - Fix: Keep display weight for the one-line verdict only, set the rest in body type, and offset the anchor so the section heading clears the sticky header.
6. **Low · narrative** (Saboteur)
   - Where: Line 28: "the only maintenance test is a springing 7.50x net leverage test on the revolver once usage exceeds USD 364 million"
   - Problem: The Legal file gate table (line 41) gives this test as "7.50x (8.00x for four quarters after a material acquisition) above 40% usage". The bottom line leaves out the 8.00x step-up, so a reader who sees only the bottom line gets a tighter covenant than the filing describes.
   - Fix: Add "(8.00x for four quarters after a material acquisition)" so the bottom line matches the table.
7. **Low · visual** (Auditor)
   - Where: Screenshot CP-4_bottom-line.png, y≈1080–1100 (crop scratchpad/tmp/CP-4-116-b.png): last line of the paragraph followed directly by "Timeline"
   - Problem: The "Timeline" heading sits about 10 px below the last line of the Bottom line, with no section spacing, so it reads as part of the passage.
   - Fix: Put the standard spacing between sections after the Bottom line block.

### Legal file gate

Kind: prose/table · handoff lines 31-45 · verdict **BLOCK**

- Narrative: The table content is factual and properly caveated (\"Unverified summary\", missing kept distinct from zero). But the section reads as a pipeline status report: the heading and Effect cells say \"gate\" and \"module Blocked\", there is no judgement-first lead, and it carries a date ambiguity (L35) and an amount ambiguity (L41).
- Visual: The section has no chart, only an 8-row, 5-column table. It is legible and has no clipping or overlap, but repeated raw filenames wrap to 4-5 lines in the Source column, which roughly doubles row height, and Basis chips duplicate the Source column.

1. **High · narrative** (Auditor, New reader)
   - Where: L31 heading "### Legal file gate"; L35 Effect "Gate fails; module Blocked"; L44 "Module status: Blocked (legal covenant phase, restricted-group phase, intercreditor phase and covenant-capacity phase)... Helper scripts were not run (see Calculations)."
   - Problem: The heading, the Effect cells and the closing line use pipeline vocabulary that the house rule bans on screen: "gate", "module Blocked", internal phase names and "Helper scripts". A PM learns that a process stopped, but not what this means for creditors.
   - Fix: Retitle the section (for example "Governing documents available"), and have Effect and the closing line state the credit consequence ("covenant capacity cannot be sized") with no gate, module, phase or script wording.
2. **Medium · narrative** (Saboteur)
   - Where: L35 "Executed credit agreement (second amended and restated, 2014, with amendments up to the September 2024 amendment)" vs "Most recent covenant-affecting amendment dated 2024-03-22"
   - Problem: The same row names a September 2024 amendment and gives 2024-03-22 as the latest covenant-affecting amendment, without saying why the September amendment does not count. A reader could conclude the dates conflict or that a later covenant change was missed.
   - Fix: Say in one clause what the September 2024 amendment changed and why it is not covenant-affecting, or drop it from the label.
3. **Medium · narrative** (Saboteur)
   - Where: L41 "7.50x (8.00x for four quarters after a material acquisition) above 40% usage, USD 364 million"
   - Problem: The cell does not say what USD 364 million is: the 40% trigger amount, the facility size or drawn usage. Bottom line L28 reads it as "once usage exceeds USD 364 million". The trigger for the only maintenance test is therefore ambiguous.
   - Fix: Label the amount explicitly (for example "tested when revolver usage exceeds 40% of commitments, i.e. USD 364 million") and give its date.
4. **Medium · narrative** (New reader)
   - Where: L33-44 table opens directly under heading; judgement only at L44 "Module status: Blocked"
   - Problem: The section has no lead sentence. The reader must read eight dense rows before reaching the conclusion, and the conclusion arrives as a status code, which inverts the house rule of judgement first.
   - Fix: Open with one sentence of judgement (no executed debt document is available, so no covenant or capacity view is possible; the issuer summaries below are unverified), then show the table.
5. **Medium · visual** (New reader, Auditor)
   - Where: Source column, all rows, shots2/CP-4_s-31.png region x~980-1160, y~255-1020 (display coords)
   - Problem: Each row repeats the raw filename "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl", wrapped over 4-5 lines. This makes every row about twice as tall as its content, and the internal ".jsonl" and accession string mean nothing to the reader.
   - Fix: Show a short reader label ("FY2024 10-K, pp. 61, 109-112") and keep the full identity in ## Sources.
6. **Low · narrative** (New reader)
   - Where: L39 "Guarantor group combined net sales USD 6,294 million (79.27% of consolidated)" and Source "...; calculation L1"
   - Problem: The figure has no period (FY2024 is implied but not stated). "calculation L1" is an internal label the reader cannot resolve on this page.
   - Fix: Add "FY2024" to the value and name the calculation in reader terms, or point to the Calculations section by name.
7. **Low · visual** (Auditor)
   - Where: "Basis" chips after each Gate item (e.g. "Executed credit agreement ... amendment) Basis"), shots2/CP-4_s-31.png left column y~255-1000
   - Problem: Every row carries both a Basis chip and a full Source column, so the reference appears twice and adds noise to the first column.
   - Fix: Use one reference mechanism per table row: the Source column, or the chip, not both.

### Capital structure

Kind: prose/table · handoff lines 46-51 · verdict **BLOCK**

- Narrative: The section is a single \"not assessable\" row with no judgement. It leaks pipeline wording (\"handoff\", \"this module\") and sends the reader elsewhere instead of stating what the filing does disclose about ranking.
- Visual: There is no chart. The page renders the one-row table cleanly with no clipping, but the status is not visually flagged and the inline Basis chip blurs the item label.

1. **High · narrative** (Auditor, New reader)
   - Where: line 50: "The instrument list and principal amounts are in the financial foundation handoff; this module adds no legal ranking because the executed documents are absent"
   - Problem: The reader sees pipeline wording: "handoff" is a listed banned term, and "this module" is internal vocabulary. The cell also sends a reader who has not read the sources to another page for the instrument list, without a link or a source reference. Two personas caught this, so it was promoted.
   - Fix: In reader language, name where the instrument list and amounts can be seen (the Financial foundation page, with a link) and drop the words "handoff" and "this module".
2. **Medium · narrative** (Saboteur)
   - Where: line 50: "Legal capital structure (rank, guarantor and collateral reach by instrument) | Not assessable: no executed governing document available"
   - Problem: The section gives no bottom line. It says nothing about what the 10-K does disclose: the notes are secured or subordinated, and guarantors make up 79.27% of sales. The Calculations block on the same page computes the secured share as 81.07% (L8) and secured notes as USD 11,000 million (L7). A committee member reading only this section would conclude that nothing is known about ranking, while the page itself holds the disclosed perimeter.
   - Fix: Open with one judgement sentence: what the filing discloses about secured versus subordinated debt and guarantor reach, then what cannot be confirmed without the executed documents.
3. **Medium · narrative** (Auditor)
   - Where: line 48: "| Item | Status | Basis and limitation |"
   - Problem: The table has no Source column, and its only basis is a pointer to another module. The house standard puts source references in tables' Source columns, so the reader cannot trace the "Not assessable" status to the 10-K pages that cite the absent documents (pages 61, 104–112 in the Legal file gate above).
   - Fix: Add a Source column with the 10-K page references that show the governing documents are incorporated by reference only.
4. **Low · visual** (New reader)
   - Where: Capital structure table, CP-4_s-46.png, top region about y=230–360 (original px)
   - Problem: A one-row, three-column table fills the full width. The status is set in the same plain grey text as the other cells, with no chip, although the left nav uses a "Not assessable" chip for the module. The "Basis" chip sits inline after the Item text, where it reads as part of the item name.
   - Fix: Show the status as the same "Not assessable" chip used in the nav, and set the Basis chip apart from the item label (its own line or a muted style).

### Chart data: covenant headroom

Kind: chart · handoff lines 52-57 · verdict **CONCERNS**

- Narrative: Saying the headroom is not assessable is honest and properly qualified. The table, though, hides the 7.50x threshold that is disclosed elsewhere on the page, uses a pipeline heading, and repeats one placeholder five times instead of saying it once.
- Visual: No covenant headroom chart is drawn and none is announced: the Charts view shows Timeline and Maps placeholders but no headroom chart slot. On the section itself, an empty five-column table of repeated text dominates.

1. **High · visual** (Auditor, Saboteur)
   - Where: Charts route screenshot CP-4_charts.png (whole page); the module top shows 'Timeline' and 'Maps' placeholders ('Not established for this run') but no Charts block; 'On this page' list has Timeline and Maps but no Charts entry
   - Problem: The covenant headroom chart has no visible slot on the module page. Timeline and maps each say 'Not established for this run', but the headroom chart just disappears. A committee reader cannot tell whether headroom was tested and left out, or never attempted, and headroom is the most decision-relevant legal visual.
   - Fix: Put a visible 'Covenant headroom: not established for this run (no executed credit agreement)' placeholder in a Charts block next to Timeline and Maps, as the other empty visuals have.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: line 56: '| Not supplied: not assessable, no executed governing document available | Not supplied: ... | ... | x (net debt to trailing four-quarter EBITDA As Defined) | The filing summarises a springing 7.50x revolver test'
   - Problem: Threshold and Direction say 'Not supplied', yet the same page states the 7.50x springing maximum (8.00x after a material acquisition, above 40% / USD 364 million usage) at lines 28 and 41, and the Basis cell names 7.50x. The table hides a known threshold, and a maximum-leverage test obviously runs one way. Only the current ratio and the headroom are truly unknown.
   - Fix: Fill Test, Threshold and Direction from the issuer summary, labelled unverified (e.g. 'Springing revolver net leverage; 7.50x max, unverified issuer summary'), and keep 'not established' only in Current and Headroom.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 52: '### Chart data: covenant headroom'
   - Problem: 'Chart data:' is a pipeline label for a chart feed, not a reader heading. It appears both in the section heading and in the 'On this page' navigation.
   - Fix: Title it for the reader, e.g. 'Covenant headroom', and let the delivery layer decide whether it is drawn as a chart.
4. **Medium · visual** (New reader, Auditor)
   - Where: CP-4_s-52.png, table under 'Chart data: covenant headroom' (top ~y 215-365 displayed): the same 9-line phrase is wrapped in five narrow columns
   - Problem: The one empty row repeats 'Not supplied: not assessable, no executed governing document available' five times in five narrow columns. That makes a tall block of identical text and buries the single informative cell, Basis and limitation.
   - Fix: Collapse the empty row to one sentence spanning the table, or show a short dash plus one shared footnote, so the reason appears once.
5. **Low · narrative** (New reader)
   - Where: line 56: 'x (net debt to trailing four-quarter EBITDA As Defined)' and 'not established for this run and not a compliance opinion'
   - Problem: 'EBITDA As Defined' is capitalised as if it were a defined term, with no explanation. 'for this run' is pipeline wording. The cell also leaves out the one disclosed fact a reader would want here: the filing states compliance at 2024-09-30 (line 42).
   - Fix: Say 'covenant-defined EBITDA (credit agreement definition, not seen)', drop 'for this run', and note that the issuer reports compliance at 2024-09-30 with the tested ratio undisclosed.
6. **Low · visual** (Auditor)
   - Where: CP-4_s-52.png, Test column first cell: small grey 'Basis' chip trailing 'available'
   - Problem: The low-contrast 'Basis' chip sits inline at the end of wrapped placeholder text. It is easy to miss and reads as part of the sentence.
   - Fix: Give the Basis chip enough contrast and put it in a consistent position, e.g. on its own line or as a row-end icon.

### Calculations

Kind: prose/table · handoff lines 76-90 · verdict **BLOCK**

- Narrative: The calculations are arithmetically correct (I recomputed L1-L8), but the section opens on pipeline vocabulary and a process failure rather than a credit judgement, and the guarantor-perimeter conclusion is never stated.
- Visual: The table is clean and readable in its layout, but the Result column mixes eight-decimal ratios, bold monospace amounts with no unit and a single USD-labelled value. Raw .jsonl file names fill the Source column, and the Basis chips are inconsistent.

1. **High · narrative** (Auditor + New reader)
   - Where: line 78: "Helper scripts named by the method (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py, covenant_headroom.py) were not run in this transport. Confidence: qa_status Blocked, so the score is capped at 39"
   - Problem: The section's lead paragraph is pipeline vocabulary: script file names, "transport", "qa_status Blocked" and an internal score cap of 39. It appears verbatim on the Modules page (screenshot CP-4_s-76.png, y≈640-700) and means nothing to a credit committee reader. This breaks the house rule against pipeline wording.
   - Fix: Replace it with one reader-language sentence, for example: covenant headroom and basket capacity could not be calculated because the executed credit documents were not available, so only the guarantor perimeter is sized here.
2. **Medium · narrative** (Saboteur + Auditor)
   - Where: line 78: "The calculations below only size the guarantor perimeter the filing discloses. All inputs USD millions, FY2024 or 2024-09-30."
   - Problem: There is no bottom line. The credit point the numbers support is never stated: about 21% of sales (USD 1,646 million) and about 22% of assets sit outside the guarantor group, and about 81% of the principal counted in L8 is secured. The section opens with what failed, not with a judgement, so the reader has to work out the structural-subordination point alone.
   - Fix: Open with a one-sentence judgement on how much value is outside the guarantor group and how much of the debt is secured, then state the limitation.
3. **Medium · narrative** (Saboteur)
   - Where: line 89: "L8 | Secured principal (term loans and secured notes) / secured plus subordinated principal | 19,702 / 24,302 | 0.81071517 (81.07%) | Financial foundation (CP-1)"
   - Problem: L8 is the most decision-relevant ratio, but its inputs are not broken down: the term-loan amount and the subordinated total do not appear, unlike L7. The denominator leaves out any debt that is neither secured nor subordinated, and the row does not say so. A reader cannot check the 81% or tell what it covers.
   - Fix: Break 19,702 into term loans plus the L7 secured notes (11,000), give the 4,600 subordinated amount, and state what debt the denominator excludes.
4. **Medium · visual** (New reader + Auditor)
   - Where: Calculations table, Result column, crop CP-4-123-a.png (L1-L8); line 86 "19888", line 88 "11000", line 82 "0.79269521 (79.27%)"
   - Problem: The results are formatted three different ways. Ratios carry eight decimals. L5 and L7 appear as bold monospace numbers with no thousands separator and no unit. L2 alone says "(USD 1,646 million)". This makes the column hard to scan, and L5 and L7 look like code.
   - Fix: Show every result in one style with its unit: percentages to one or two decimals, amounts as "USD 19,888 million", in the same font as the rest of the table.
5. **Medium · visual** (New reader)
   - Where: Source column, lines 82/85/86/88: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 59"; lines 83-84 "Same"
   - Problem: The source cell is a raw internal file name (an accession number plus a .jsonl extraction artefact) that wraps over three lines and takes up most of the row height. "Same" makes the reader look up to an earlier row to find the source.
   - Fix: Cite the source as "TDG FY2024 10-K, p. 59 (guarantor condensed financials)" and repeat it in every row instead of writing "Same".
6. **Low · narrative** (Saboteur)
   - Where: line 87: "0.77730009 (77.73%); combined (not consolidated) basis, indicative only"
   - Problem: The caveat that cuts the L6 ratio to "indicative only" sits inside the Result cell, where a skimming reader taking the 77.73% will miss it. It also does not say which way the mismatched basis biases the figure.
   - Fix: Move the basis caveat to the formula or a note line and say whether the combined basis overstates or understates the guarantor share.
7. **Low · visual** (New reader + Auditor)
   - Where: Calculations table ID column, crop CP-4-123-a.png: "Basis" chip under L1, L4, L5, L7 only
   - Problem: An unexplained grey "Basis" label appears under some row IDs and not others. The reader cannot tell what it means or why L2, L3, L6 and L8 have none.
   - Fix: Either make the chip self-explanatory (for example, a link to the source passage) and use it consistently, or remove it from this table.

### Gaps

Kind: prose/table · handoff lines 91-104 · verdict **BLOCK**

- Narrative: The table is thorough about what is missing, but it gives no judgement first and speaks in pipeline terms (module Blocked, phase, selected in this run), so it reads as a run log rather than a credit limitation.
- Visual: The section is one five-column table that renders cleanly with no clipping or overlap, but a repeated bracketed tag in the narrow first column makes the rows tall and dense. There is no chart, map or timeline in this section.

1. **High · narrative** (Auditor, New reader)
   - Where: L95 "Module Blocked; no covenant register, score or capacity"; L103 "Refinancing module not selected in this run ... Run when selected"; L102 "Optional; via the research module labelled external"; L98/L100 "Intercreditor phase not assessable", "Covenant-capacity phase not assessable"
   - Problem: The table uses pipeline and run-configuration language (module, Blocked, phase, selected in this run, research module labelled external, score) that the house standard bars from reader text. A portfolio manager cannot tell what a 'phase' or 'score' is, or why a module 'not selected' is a credit gap.
   - Fix: Describe each impact as what the reader cannot know about the credit (for example 'no view on covenant headroom or debt-incurrence capacity'), and remove run-selection rows or reword them as analysis not performed.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: Gaps table, L95-L103: nine rows given in a flat list, each ending '[Insufficient Information]', with no line saying which missing document changes the credit view most
   - Problem: The section opens straight into a table with no judgement first. It does not say that the missing credit agreement and intercreditor agreement leave covenant protection and recovery ranking entirely unassessed. A committee member skimming could read the list as housekeeping, not as a material blind spot.
   - Fix: Open with one judgement sentence on what the gaps mean for the credit view, then order or mark the rows by how much each one matters.
3. **Medium · narrative** (New reader)
   - Where: L95 "Controls incurrence, restricted payments, EBITDA definition, amendment thresholds and the springing test"; L101 "including the UK guarantor"
   - Problem: 'Springing test' is jargon the reader is never given, and 'the UK guarantor' brings in a fact that nothing on the page explains or sources. The reader would need another document to follow either.
   - Fix: Use plain wording such as 'the revolver's leverage test that applies only when drawn', and either give a basis for the UK guarantor or drop it.
4. **Medium · narrative** (Saboteur)
   - Where: L101 "Governing law and jurisdiction ... | Not stated |"; L103 "Not assessable regardless of documents"
   - Problem: 'Not stated' is not an impact on the output, and 'regardless of documents' contradicts the table's premise that attaching documents closes each gap. Both make the reader guess at what is actually unknown.
   - Fix: State the concrete effect, for example 'enforceability of the guarantees not assessed', and explain the refinancing row's scope in reader terms.
5. **Medium · visual** (New reader, Auditor)
   - Where: Gaps table, screenshot /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots2/CP-4_s-91.png, approx y 1125-1845 (display px)
   - Problem: The narrow first column carries the repeated '[Insufficient Information]' tag in eight of nine rows. Each gap name wraps over three or four lines, which nearly doubles row height and turns a 9-row table into a dense block about 720 px tall.
   - Fix: Drop the repeated tag, or show it once as a chip or column header, so each gap name fits on one or two lines.
6. **Low · narrative** (Auditor)
   - Where: L99 "About a fifth of sales sits outside the guarantor group (calculation L3)"
   - Problem: The only figure in the table sits in a narrative cell, with an internal calculation ID as its reference and no period or basis. The table also has no Source column, although the house standard puts table references in Source columns.
   - Fix: Give the figure with its period (about 21% of FY2024 net sales) and put the reference in a Source column or Basis line, not in the sentence.
7. **Low · narrative** (New reader)
   - Where: Required follow-up column, L95-L103: "Attach executed indentures", "Request latest certificate", "Run when selected"
   - Problem: These follow-ups are operator instructions to the pipeline user, not actions a credit committee member can take or weigh, so the column means little to the stated reader.
   - Fix: Phrase follow-ups as what the analyst or issuer must provide, or fold them into the section's 'what would change the view' statement.

### Map: legal entities

Kind: map · handoff lines 64-69 · verdict **CONCERNS**

- Narrative: This is a data section, so it owes only a bottom line. Its single row gives the reason nothing was drawn, but it omits the guarantor/non-guarantor split that the filing does establish and the same page calculates (L1-L3), and it uses graph vocabulary ("edge").
- Visual: No map is drawn. The Maps panel shows a two-line "Not established for this run" placeholder, which is visible and not folded. In the module body, a five-column table repeats one placeholder sentence in four cells, padding a page that already carries three identical empty tables.

1. **Medium · narrative** (Saboteur)
   - Where: line 68: "Not supplied: guarantor exhibit, guarantee and collateral agreement and indentures absent, so no edge with applicable document and jurisdiction can be drawn"
   - Problem: The map says nothing about the entity structure. Yet the same page sizes the guarantor group from the 10-K: guarantors hold 79.27% of sales (L1), and USD 1,646 million, 20.73% of sales, sits outside the guarantor group (L2, L3; Gaps: "About a fifth of sales sits outside the guarantor group"). A reader who stops at the map may conclude that structural subordination is wholly unknown.
   - Fix: Give the map one row saying what the filing does establish: the guarantor group against the non-guarantor group, with the 79.27% / 20.73% split and its 10-K page. Mark entity-level edges as not assessable.
2. **Medium · narrative** (New reader, Auditor)
   - Where: line 66: "| From | Relationship | Edge type | To | Evidence |" and line 68: "no edge with applicable document and jurisdiction can be drawn"
   - Problem: "Edge" and "Edge type" are graph-model vocabulary, not language a credit committee uses. The heading prefix "Map:" names a rendering slot rather than telling the reader what the content is.
   - Fix: Write in reader terms, e.g. "guarantee / ownership link" and "Legal entity structure", and keep internal schema words off the page.
3. **Medium · visual** (New reader, Auditor)
   - Where: Map: legal entities table, CP-4_s-64.png, region y≈190-330 (display scale): five-column table whose From, Relationship, Edge type and To cells each repeat "Not supplied: not assessable, no executed governing document available"
   - Problem: One sentence is spread across a five-column grid, repeated four times. It looks like data but holds none, and it wastes vertical space. The intercreditor map, Events: Legal and covenant headroom tables directly around it repeat the same pattern, so the reader wades through four identical blocks.
   - Fix: When no edge exists, collapse the section to a single-line gap statement with its reason, and drop the empty column grid.
4. **Low · visual** (Auditor)
   - Where: Maps panel, CP-4_maps.png, crop CP-4-121-a.png (x 330-1440, y 200-420): "Legal entities / Not established for this run / not assessable, no executed governing document available"
   - Problem: The Maps panel calls this state "Not established for this run", while the section table calls it "Not supplied: not assessable". The panel's sub-line is lowercase small grey text. Two labels for one state, and the reason is hard to read.
   - Fix: Use one wording for this state across the panel and the section, and set the reason as a sentence with readable contrast.
5. **Low · visual** (New reader)
   - Where: Map: legal entities table, From cell, CP-4_s-64.png: "governing document available Basis"
   - Problem: A "Basis" chip sits on a cell that says nothing was supplied. It suggests a source backs an empty value, and it sits on only one of the four identical cells.
   - Fix: Point the Basis chip to the source that shows the document is absent (the 10-K exhibit index), or remove it from placeholder rows.

### Map: intercreditor

Kind: map · handoff lines 70-75 · verdict **CONCERNS**

- Narrative: The section (handoff lines 70-75) is one row of 'not supplied' boilerplate with no stated credit consequence and some graph jargon ('Edge type', 'edge'). The 'not established' status itself is correct, and missing is not shown as zero.
- Visual: There is no drawn map: the Maps panel shows a two-line empty state and the module body repeats it as a five-column table, with mismatched wording, an inline Basis chip and tiny low-contrast reason text. Not verified: whether this run and these screenshots reflect the latest code changes (the relayed request); I reviewed only the supplied run copy and shots.

1. **Medium · narrative** (Saboteur, New reader)
   - Where: line 74: "| Not supplied: not assessable, no executed governing document available | Not supplied: not assessable, no executed governing document available | ... | Not supplied: intercreditor agreement referenced but absent"
   - Problem: The phrase is repeated word for word in four of the five cells, and the section never states a judgement. A committee reader learns that nothing could be drawn but not what that means for credit: who controls enforcement between the term lenders and the secured noteholders is unknown, even though line 89 says secured debt is 81% of principal. The implication only appears much further down, in the Gaps table.
   - Fix: Collapse the row to one full-width 'Not assessable' line and lead with one judgement sentence on the credit consequence (for example, that enforcement control and release rank between the secured classes are unverified), with the reason in its Basis line.
2. **Medium · narrative** (New reader, Auditor)
   - Where: line 72: "| From | Relationship | Edge type | To | Evidence |"; line 74: "no payment-rank, security-rank, enforcement-control, standstill or release edge can be drawn"
   - Problem: 'Edge type' and 'edge can be drawn' are graph-model wording, not reader language. A portfolio manager has to work out that 'edge' means a ranking or control relationship between creditor classes.
   - Fix: Rename the column to something like 'Ranking / control term' and write 'no payment, security, enforcement, standstill or release ranking can be established' instead of 'edge'.
3. **Medium · visual** (Auditor, Saboteur)
   - Where: CP-4_maps.png Maps panel, top (crop CP-4-122-a.png: 'Intercreditor / Not established for this run / not assessable, no executed governing document available') vs CP-4_s-70.png 'Map: intercreditor' table at y~350-480
   - Problem: The same empty intercreditor map shows twice on one page with two different empty-state phrases ('Not established for this run' in the Maps panel, 'Not supplied: not assessable' in the table). That reads as two different statuses and spends vertical space twice on nothing.
   - Fix: Use one empty-state wording in both places, and show the empty intercreditor map once (the Maps panel) instead of repeating it as a five-column table.
4. **Low · visual** (Auditor)
   - Where: CP-4_s-70.png, 'Map: intercreditor' table, From cell: "Not supplied: not assessable, no executed governing document available Basis"
   - Problem: The Basis chip sits inline at the end of the first cell's text, so it reads as the last word of the sentence. It applies to the whole row, not to the From cell.
   - Fix: Put the Basis link on its own line under the row, or give it a clearly separated chip style, as row-level provenance.
5. **Low · visual** (New reader)
   - Where: CP-4_s-70.png 'Map: intercreditor' table (y~365-480): five equal-width columns; the Evidence column at ~240 px holds the only informative text
   - Problem: With equal column widths, four columns of identical boilerplate each wrap to four lines, while the one cell that says something is squeezed into the same narrow width. The eye goes to the repetition, not the content.
   - Fix: When every cell but Evidence is the same 'not supplied' value, render a single spanning row so the evidence text gets the full width.
6. **Low · visual** (Auditor)
   - Where: CP-4-122-a.png Maps panel caption 'not assessable, no executed governing document available' (small grey lowercase text under 'Not established for this run')
   - Problem: The reason line is set in very small, low-contrast grey type, yet it is the only explanation the reader gets for the empty map.
   - Fix: Set the reason at body size with standard text contrast, sentence-cased.

## Security selection (CP-3)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-3/ccef34b927f316eb26b4d56da3700d1779f0966239dafc5935b729acb8a120df/1.response.md`

### Analytical appendix — complete canonical registers (part 2 of 3: from 'T3B.1 Instrument source register')

Kind: register appendix · handoff lines 197-293 · verdict **BLOCK**

- Narrative: This part of the register appendix is data-dense and mostly exact, but the reader meets placeholder headings ('a method step …'), snake_case and pipeline vocabulary, and one leverage comparison on mismatched bases that drives the priming-risk call.
- Visual: The section has no chart. Its wide registers overflow the content column with the Source and Fixed/Floating columns clipped and no scroll cue, rows run 4-10 lines tall, and the coupon styling is inconsistent.

1. **High · narrative** (Auditor, New reader)
   - Where: Register headings and cross-references, e.g. line 197 '#### T3B.1 Instrument source register', line 203 'T3B.4, T3B.5', line 278 'T3B.4; T3B.7', line 289 'T3B.5 row 2'; rendered as 'a method step Instrument source register', 'method steps', 'a method step row 2' (shots2/CP-3_s-197.png top and table rows; DOM dump tmp/CP-3-136.html)
   - Problem: The renderer replaces the register codes with the placeholder 'a method step'. Every heading in this section and in the 'On this page' list reads 'a method step …', and the downstream_use, Source Trace and Evidence ID cells say 'method steps' or 'a method step row 2', which point nowhere. Hiding the internal codes left text that no reader can follow.
   - Fix: Give each heading a plain title such as 'Instrument source register', and write each cross-reference as the readable name of the table and row it points to (or drop it).
2. **High · narrative** (Auditor, New reader)
   - Where: Line 199 '| source_document_id | source_document_name | source_quality | period | entity_covered | data_supplied | limitation | downstream_use | Source |'; lines 203-204 'Handoff reporting Blocked', 'Source readiness lane', 'Validated handoff'
   - Problem: The raw snake_case column names and pipeline words ('handoff', 'lane', 'Blocked') go straight to a credit committee reader, which breaks the house rule against pipeline vocabulary. The row id 'HO-CP-4' shows on the page as 'HO-Legal & covenants'.
   - Fix: Use reader column titles (Document, Quality, Period, Entity, Data supplied, Limitation) and describe the legal input as 'Legal review incomplete: executed documents not available'.
3. **High · narrative** (Saboteur)
   - Where: Line 254 'Moderate: 5.00x secured net incurrence vs 4.72x gross secured today, definitions unread'
   - Problem: This compares a net-leverage covenant capacity with a gross leverage figure, so the 0.28x headroom it implies is on mixed bases and probably understates the room to add pari secured debt. That drives the 'Moderate' priming call. Line 290 then says 'approaching 5.00x house basis' without saying which basis.
   - Fix: State secured leverage on the same net basis as the covenant (or say plainly that headroom cannot be measured), and give the basis and period on the trigger.
4. **High · visual** (Auditor, New reader)
   - Where: Instrument source register and Capital structure dashboard tables, shots2/CP-3_s-197.png, right edge x≈1300-1440 (displayed ~1100-1160)
   - Problem: Both tables run past the content column. The Source column is cut mid-filename ('TDG_2024 30_10- K_0001260… pages 59–'), and 'Fixed / Floa(ting)' and 'Floating, pa(rtly hedged)' are clipped, with no visible scroll cue. The 11-column dashboard wraps every cell into 4-10 lines, so one instrument row is about 120-180 px tall.
   - Fix: Shorten source cells to a short document label plus page, cut or merge low-value columns (Currency is all USD), and show a visible horizontal-scroll cue or sticky first column.
5. **Medium · narrative** (Saboteur)
   - Where: Line 272 'Current yield 4.78% below secured 5.92%; pull-to-par uncounted'
   - Problem: The comparison sets the current yield of one subordinated note against the current yield of one secured series (the 2033s at 101.40) and labels the latter 'secured'. A reader could take this as an inverted subordination pickup, even though current yield ignores price-to-par and call effects.
   - Fix: Name the exact instruments compared, and either drop the comparison or label it as not indicative of relative value until yield-to-worst is available.
6. **Medium · narrative** (New reader)
   - Where: Line 261 'Financial data foundation (CP-1)', rendered 'Financial data foundation (Financial foundation)'; line 252 'Source (CP-4 / CP-4A / CP-3C)' rendered 'Source (Legal & covenants / Covenant capacity / Refinancing & LME)'; line 254 'CP-3C not supplied'
   - Problem: Once codes are swapped for names, the source labels repeat themselves, and the cells that refer to other analyses ('Refinancing & LME not supplied') name internal analyses rather than evidence. LME is never defined.
   - Fix: Cite the document or analysis once by its reader name, and spell out 'liability management exercise' the first time it appears.
7. **Medium · visual** (Auditor)
   - Where: Capital structure dashboard Coupon / Margin column, shots2/CP-3_s-197.png rows 2028-2027 notes ('6.75%', '6.375%', '5.50%')
   - Problem: Fixed coupons render in bold monospace, while the floating margins in the same column ('Term SOFR plus 2.25%') render in regular body type. The inconsistent styling signals a difference in meaning that does not exist.
   - Fix: Render every Coupon / Margin cell in the same face and weight.
8. **Low · visual** (Auditor)
   - Where: First cell of each row, shots2/CP-3_s-197.png e.g. 'SRC-10K-DEBT Basis', '2028 secured notes Basis'
   - Problem: A 'Basis' chip sits inside every instrument-name cell. In narrow cells it wraps beneath the name and doubles the row label's height, adding visual noise in a dense register.
   - Fix: Move the Basis chip into a narrow dedicated column or show it on hover/focus so the instrument name stays on one line.

### Analytical appendix — complete canonical registers (part 3 of 3: from 'T3B.11 Gaps ledger')

Kind: register appendix · handoff lines 294-385 · verdict **BLOCK**

- Narrative: This register appendix is in effect a data section, so it owes no bottom-line order of its own. Its narrative fails the reader standard because the reference substitution leaves the placeholder \"a method step\" in headings and traces, a mangled ID \"Security selection-MON-00x\", and \"handoff\" and config-flag wording on screen.
- Visual: The section has no chart, map or timeline, only stacked bordered tables. They read cleanly except the Concentration register, which is clipped at the right edge (\"Sourc\" / \"a met step\") and pads the page with rows of \"Not provided\".

1. **High · narrative** (New reader + Auditor (promoted))
   - Where: Every Source Trace / Evidence cell, e.g. line 321 "| T3B.8 |", line 336 "T3.3 Refinancing", line 308 "This handoff, T3.7"; rendered in CP-3_s-294.png as "a method step", "a method step Refinancing", "This handoff, a method step"
   - Problem: The renderer replaces the register codes with the placeholder "a method step", so every trace in these 12 tables points to nothing the reader can find. "This handoff" is pipeline vocabulary that the ruling bans. The traceability these columns exist for is gone.
   - Fix: Resolve each internal reference to a reader-visible target (the named table heading or Sources entry, as a link), or drop the column, and never print "a method step" or "handoff".
2. **High · narrative** (Auditor + New reader (promoted))
   - Where: Table headings, line 294 "#### T3B.11 Gaps ledger" and line 304 "#### T3C.1 Portfolio input gate", rendered as "a method step Gaps ledger", "a method step Portfolio input gate" (CP-3_s-294.png, headings and the On-this-page list)
   - Problem: Every heading and every on-page nav entry starts with the meaningless prefix "a method step", and "gate" is listed pipeline vocabulary. The nav now shows two identical entries named "a method step Gaps ledger" (T3B.11 and T3C.9) and two named "a method step Monitoring triggers", which the reader cannot tell apart.
   - Fix: Show plain, distinct headings (for example "Instrument gaps" and "Portfolio gaps", "Portfolio inputs") with no placeholder prefix.
3. **High · narrative** (Auditor)
   - Where: Line 373 "| CP-3B-MON-001 | Special dividend with secured issuance |", rendered (headless DOM dump tmp/CP-3-137.html) as "Security selection-MON-001"
   - Problem: The module-code substitution leaves a mangled internal ID ("Security selection-MON-001/002/003") as the first column of the trigger table. It is an internal register key, not reader language.
   - Fix: Show a short trigger name or a plain sequence number (as the gaps table already shows "Gap 1"), not a derived pipeline ID.
4. **High · visual** (Auditor + New reader (promoted))
   - Where: "Concentration and correlation register" table, CP-3_s-294.png, approximately x 1100-1160 and y 1470-1900 (displayed scale)
   - Problem: The 8-column table overflows its card: the last header is cut to "Sourc" and every cell in the column reads "a met / step". There is no visible scroll cue, so the column is unreadable.
   - Fix: Fit the table to the content width (wrap or drop the trace column) or show an explicit horizontal-scroll affordance.
5. **Medium · narrative** (Auditor + Saboteur (promoted))
   - Where: Line 310 "| Mandate constraints | Missing | context (portfolio_workbook false) |" and line 315 "Module status: Completed with Limitations; output mode: Generic Portfolio-Fit Logic."
   - Problem: Raw config flags ("portfolio_workbook false", "context") in a Source column and a module-status/output-mode line are pipeline wording on screen. The status line also sits loose between tables, where it reads as a conclusion.
   - Fix: Write the source as "No portfolio data supplied" and move or drop the module-status line in favour of the page's own limitations passage.
6. **Medium · narrative** (New reader)
   - Where: Line 298 "| A1 | YTW, spreads, DM per instrument | Compensation adequacy | All Unclear; no Preferred |" and line 301 "| A4 | Recovery / EV | Fulcrum | Ordinal labels only | Valuation module |"
   - Problem: YTW, DM, EV, LME and LGD are not defined. Telegraphic cells ("Fulcrum", "Ordinal labels only", "Same | Same" on line 329) and "Valuation module" / "Run refinancing/LME module" as follow-ups depend on knowing the pipeline.
   - Fix: Spell out each abbreviation on first use, write each cell as a short readable clause, and name follow-ups as analyses rather than modules.
7. **Medium · visual** (New reader + Saboteur (promoted))
   - Where: Lines 343-349, Concentration register: seven rows of "Not provided | Not provided | Not provided | Not Provided ... Cannot test" (CP-3_s-294.png y 1500-1900)
   - Problem: About 400 px of the page holds 28 identical "Not provided" cells. They bury the one real message (no portfolio data, so concentration cannot be tested), and the wall of text slows the reader.
   - Fix: Collapse the register to one stated gap line (or a single row) when every exposure input is missing.
8. **Low · visual** (Saboteur)
   - Where: "Portfolio input gate" table, Source column, CP-3_s-294.png y 540-560: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 59–60"
   - Problem: A raw ingest filename (.htm.jsonl) wraps across two lines in the Source column, where the reader expects a document title.
   - Fix: Show the document as "TDG 10-K FY2024, pp. 59–60", linked to the Sources entry.

### Analytical appendix — complete canonical registers (part 1 of 3: from 'T3.1 Source register')

Kind: register appendix · handoff lines 104-196 · verdict **BLOCK**

- Narrative: The section is internal register material shown to the reader almost unedited: process notes, module codes, snake_case headers and pipeline words, with no judgement first. Its real content (definition conflicts, unscorable composite) is buried.
- Visual: There is no chart in this section. The two wide tables clip their Source column at the card edge, wrap into very tall rows, and carry garbled 'a method step' headings and cross-references from the code scrubber.

1. **High · narrative** (Auditor, Saboteur)
   - Where: line 106: 'Helper scripts (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py, recovery_waterfall.py) were not run in this transport ... CP-1A X1 dividend equivalents ... CP-2G debt basis'
   - Problem: This appendix preface (present as a text block in library data.js, line 106) shows script filenames, the word 'transport', module codes CP-1A, CP-0 and CP-2G, and the register code 'X1'. All of these break the house rule against module codes and pipeline vocabulary. The useful content is buried: the USD 188 million carrying-versus-gross debt difference and the dividend-equivalent conflict.
   - Fix: Drop the process notes and keep a one-line reader statement of the two definition conflicts, with amounts and the basis used.
2. **High · visual** (Auditor, New reader)
   - Where: Table headings and cells in CP-3_s-108.png: 'a method step Source register' (heading, y~195), 'a method step Issuer / security scorecard' (y~1143), downstream_use cells 'method steps', 'a method step policy factor', 'method steps limited'; the 'On this page' list repeats 'a method step ...' about 30 times. Handoff lines 108, 112-120 hold 'T3.1 Source register', 'T3B.2, T3B.3, T3.5', 'T3.3 policy factor'.
   - Problem: The code scrubber replaces register codes with 'a method step', which gives garbled headings and makes cross-references meaningless: 'a method step policy factor' points nowhere, and the reader cannot tell which table a row feeds. The scrub swaps one leak for nonsense.
   - Fix: Give each register a plain reader title (e.g. 'Source register', 'Issuer scorecard') and turn cross-references into named links to those titles, with no placeholder text.
3. **High · visual** (Auditor, New reader)
   - Where: T3.1 Source register and T3.3 scorecard, right-hand Source column in CP-3_s-108.png, x~1320-1440 (crop CP-3-135-a.png)
   - Problem: The Source column is clipped at the card edge: 'TDG_2024-30_10-K_0001260...', 'Source reac', 'Business an transaction pack (Busin governance'. The reader cannot read the source reference, and nothing shows that the table scrolls sideways.
   - Fix: Fit the table to the column width by shortening source labels to the reader form (e.g. 'Annual report FY2024, pp. 59-60'), or show a visible horizontal-scroll cue.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 110: '| source_document_id | source_document_name | source_quality | period | entity_covered | data_supplied | limitation | downstream_use | Source |'; line 114 'Validated handoff'; line 113 'Gate for RV and portfolio phases'
   - Problem: The reader sees snake_case field names, and the cells contain 'handoff', 'gate', 'phases' and 'not available in this transport' (line 120). This is pipeline language that a credit committee member cannot interpret.
   - Fix: Use title-case reader headings (Document, Quality, Period, Entity, Data used, Limitation, Used in), and describe internal inputs as 'earlier analysis: Financial foundation'.
5. **Medium · narrative** (Saboteur)
   - Where: line 126-135: '| Weight | Raw Score 1–5 | Weighted Score |' with every row 'Not supplied: no mandate weights' and 'Not Scorable: no weights'
   - Problem: Two of the ten columns say the same 'not scorable' message in every row, which pads the table into tall, narrow cells. The scale direction is never stated: a 5 on Financial policy is the worst score, but a reader could take 5 of 5 as strong.
   - Fix: State the scale direction once ('1 = strongest, 5 = weakest'), and replace the two empty columns with one sentence above the table.
6. **Medium · narrative** (Saboteur)
   - Where: line 106 'complete canonical registers'; Modules page side list 'Analytical appendix — complete canonical registers'
   - Problem: 'Canonical registers' is pipeline vocabulary, and the appendix has no bottom line. The reader is not told what the appendix shows or that every security ends as 'Requires More Work' because no yields were supplied.
   - Fix: Rename the appendix (e.g. 'Supporting tables') and open it with one sentence of judgement that points the reader to the conclusion.
7. **Medium · visual** (New reader)
   - Where: T3.3 scorecard rows in CP-3_s-108.png y~1210-2000 (Evidence and 'Not supplied: no mandate weights' cells)
   - Problem: Ten columns force word-by-word wrapping, so each row is 5-9 lines tall. The six scorecard rows take more than a full screen, and the raw score, the only judgement in the table, gets lost among them.
   - Fix: Cut the columns to Factor, Score, Confidence, Evidence and Implication so that each row fits in two or three lines.
8. **Low · visual** (Auditor)
   - Where: First column chips 'SRC-10K Basis', 'HO-Source readiness Basis', 'Business Basis' in CP-3_s-108.png x~310-420
   - Problem: A grey 'Basis' tag is attached to every first-column cell and means nothing in a table context. Internal IDs such as 'SRC-10K' and 'HO-' prefixes are shown to the reader.
   - Fix: Remove the Basis tag from table cells and hide internal document IDs.

### Key findings

Kind: reader passage · handoff lines 33-47 · verdict **BLOCK**

- Narrative: The section puts its judgement first and stays in a credit register, but three of the six bold headlines (lines 37, 39, 41) say more than their own caveats allow. The last bullet is a missing-input note in workflow vocabulary that belongs in Limitations.
- Visual: There is no chart in this section. The bulleted list has clean spacing, but only the last of six bullets shows a Basis chip on screen, so five findings appear without sources, and the monospace-underlined figures crowd the text.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 41: "On running income, the junior paper pays less than the senior paper, and that is the first question to settle when yields arrive."
   - Problem: The bold headline says the subordinated notes pay less than the secured notes, but it rests on current yield. The same bullet then concedes that pull-to-par on notes priced at about 96.7% is left out. A skimming committee member takes away 'junior is under-compensated', which the text itself says it cannot support. Raised by two personas, so promoted to High.
   - Fix: Make the headline the judgement the evidence supports: on coupon income alone the junior notes yield less, and the total-return answer waits for yield-to-worst.
2. **High · visual** (Auditor, New reader)
   - Where: Handoff lines 36, 38, 40, 42, 44 each carry a 'Basis:' line; screenshot CP-3_key-findings.png region x340-1100, y220-1060 (crop scratchpad/tmp/CP-3-128-a.png)
   - Problem: The page shows a 'Basis' chip only after the last bullet ('...generic logic only. Basis'). The first five findings, which hold every figure in the section (20.73%, 5.55x, 87.25%→96.67%, 5.92% vs 4.78%, USD 2,354.40 million), have no visible Basis on screen. A reader cannot trace any of them, and the one chip that does appear looks as if it covers the whole list. Raised by two personas, so promoted to High.
   - Fix: Give each bullet its own visible Basis chip after its text, as the prose paragraphs have, so every finding shows its sources.
3. **Medium · narrative** (Saboteur)
   - Where: line 37: "Fundamentals support holding the credit at this leverage..."; line 27: "TransDigm's debt earns Requires More Work"
   - Problem: 'Support holding the credit' reads like a hold recommendation and conflicts with the module's actual call of Requires More Work. The reader gets two different verdicts on the same page.
   - Fix: Phrase the bullet as a credit-capacity finding (the fundamentals can carry the stack) rather than a position call, so it matches the recommendation.
4. **Medium · narrative** (New reader)
   - Where: line 37: "Pro forma net leverage is 5.55x and cash interest cover 3.60x"
   - Problem: Neither ratio states its period or what 'pro forma' adjusts for, so it is unclear whether 5.55x includes the October 2024 payout described in the next sentence. The 4.72x–5.82x range of EBITDA As Defined in the bottom line uses a different basis, and the reader cannot reconcile the two.
   - Fix: State the period and the pro forma adjustment beside each ratio (for example, FY2024 EBITDA As Defined, pro forma for the October 2024 dividend debt).
5. **Medium · narrative** (Saboteur)
   - Where: line 39: "The fair values show the market priced the subordinated notes up during FY2024 despite the extra secured debt. ... the credit and rate effects cannot be separated, and the reading stays directional."
   - Problem: The headline asserts a credit signal that the last sentence of the same bullet withdraws. The caveat cancels the finding, and a skimmer keeps only the bold claim.
   - Fix: Put the qualification into the headline (subordinated prices rose with falling rates, and the evidence cannot show a subordination penalty either way) or drop it to a limitation.
6. **Medium · narrative** (Auditor, New reader)
   - Where: line 45: "No sizing posture can be supported. No mandate, holdings, limits or trading evidence was supplied, so portfolio fit is generic logic only." Basis: context
   - Problem: 'Sizing posture' and 'generic logic only' are workflow wording, and the Basis 'context' names a run-settings file, not evidence. The bullet also states a missing input, not a finding, and it repeats Limitations line 60.
   - Fix: Move this point to Limitations only, in reader terms (no portfolio mandate or holdings were provided, so position size is not assessed).
7. **Low · narrative** (New reader)
   - Where: line 43: "USD 2,650 million matures on 2027-11-15, inside the FY2028 cluster ... FY2027 cash falls USD 2,354.40 million short of FY2028 maturities"
   - Problem: A 2027 maturity sitting in FY2028 needs the September fiscal year-end explained. Giving the downside shortfall to the cent (2,354.40) suggests a precision that a scenario output does not have.
   - Fix: Add 'TransDigm's fiscal year ends 30 September' once, and round the scenario shortfall to the nearest USD 10 million or so.
8. **Low · visual** (Auditor)
   - Where: screenshot CP-3_key-findings.png, bullets 2 and 5 (crop scratchpad/tmp/CP-3-128-a.png y~230-320, 650-720)
   - Problem: Every figure is set in monospace with a dashed underline. In bullet 2 there are five such figures in four lines, which makes the text look spotty and breaks line rhythm ('USD 4,348 million' wraps to begin its own line). The bold lead-ins also run to two lines, so they read as sentences rather than headings.
   - Fix: Set figures in proportional tabular numerals with a lighter cue, and keep each bold lead-in to one line.

### Limitations

Kind: reader passage · handoff lines 53-61 · verdict **BLOCK**

- Narrative: The section is in the right place in the reading order and states its gaps directly. But line 55 contradicts the bottom line's secured lean, the call-cap risk that undercuts that lean appears only here, and pipeline or label vocabulary ("for this run", "workbook", "sizing posture", "Requires More Work") reaches the reader.
- Visual: This section has no chart. It is a readable bulleted list with comfortable line height, but it is set in a narrower column than the rest of the page and runs straight into the Timeline heading with almost no gap.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 55: "A conditional secured preference becomes Requires More Work for the whole stack until yield-to-worst and comparable levels are supplied."
   - Problem: This contradicts the bottom line (line 30), which says "the default lean is towards secured paper". It turns an analytical lean into a status label, so the committee cannot tell whether a secured preference stands. The capitalised labels "Requires More Work", "Unclear" and "Preferred" are internal rating vocabulary, and the reader has not been told what they mean.
   - Fix: Say in plain words whether the secured lean holds pending yield-to-worst, using the same wording as the bottom line, and say what each label means the first time it is used.
2. **High · narrative** (Saboteur, New reader)
   - Where: line 58: "Call schedules for the notes were not read. The secured notes trading above par may be capped by their call prices, which would overstate their price upside and understate the case for discounted subordinated notes."
   - Problem: This limitation works directly against the module's main lean towards secured paper (line 30). It sits only in the last section and is not reflected in the bottom line or in the contrary-evidence passage. A reader who stops at the bottom line comes away with a secured preference that has not been tested for call caps.
   - Fix: Carry the call-cap risk into the contrary-evidence passage (or as a qualifier on the bottom-line lean), and keep the limitation here as the record that the call schedules were not read.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 59: "No enterprise valuation or recovery waterfall exists for this run."; line 57: "No loan-market workbook was available"; line 60: "the sizing posture is Requires More Work"
   - Problem: "for this run", "workbook" and "sizing posture" describe the pipeline and its inputs rather than the credit, and the house standard says pipeline vocabulary is not reader language. A portfolio manager does not know what run or workbook is meant.
   - Fix: Describe each missing item as missing evidence (e.g. "no recovery analysis or enterprise valuation was available", "no loan-market pricing") and say "position size" in plain terms.
4. **Medium · narrative** (New reader)
   - Where: line 59: "The recovery sensitivity labels are ordinal (secured before subordinated)"; line 57: "The term-loan relative-value label stays Unclear"
   - Problem: These bullets refer to labels in the Recommendation table. On the page that table is drawn after the Timeline, Request and Sources blocks, so the reader meets the caveat before the thing it qualifies. "Ordinal" is also jargon for this reader.
   - Fix: Name the table these caveats qualify, or say directly that the recovery ranking is relative only and cannot show whether the subordinated notes would recover anything.
5. **Medium · visual** (Auditor)
   - Where: CP-3_limitations.png, crop of the Limitations block (original about y 250–640) with the Timeline directly below
   - Problem: The last bullet sits almost directly on the "Timeline" heading, with almost no vertical gap, so the timeline reads as part of the Limitations list. The heading also has much less space above it than the other section headings on the page (Request, Sources, Recommendation).
   - Fix: Give the Timeline heading the same top margin as the other section headings so Limitations ends visibly before it.
6. **Low · narrative** (New reader)
   - Where: line 56: "may reflect falling rates rather than credit, so it stays directional and does not move the recommendation."
   - Problem: This repeats almost word for word the caveat already given in Key findings (line 39: "the credit and rate effects cannot be separated, and the reading stays directional"), which adds length without adding information.
   - Fix: Keep the caveat in one place, or shorten this bullet to the point that the year-end prices are not executable quotes.
7. **Low · visual** (Saboteur, Auditor)
   - Where: CP-3_limitations.png, Limitations bullets: text column width compared with the Recommendation and Relative value prose below
   - Problem: The Limitations bullets wrap at about 60% of the content width, while the prose further down the same page runs full width. The measure changes from one section to the next, and Limitations looks like a narrower, less important side panel.
   - Fix: Use one text measure for all reader passages on the module page.

### Recommendation

Kind: prose/table · handoff lines 62-75 · verdict **BLOCK**

- Narrative: The section reaches a clear judgement, but it is buried in a 60-word opening sentence, drops the secured-paper lean stated in the Bottom line, and is followed by an internal status block full of pipeline field names shown to the reader.
- Visual: There is no chart in this section. The four-row table is legible and fits the width, but number styling is inconsistent within the price column, the two repeated columns add no information, and the status paragraph is not visually separated from the analysis.

1. **High · narrative** (Auditor, New reader)
   - Where: line 74: "Module status: Ready with Limitations. Execution mode: Capital-Structure RV. ... committee_status: Requires More Work. qa_status: Passed (no QA finding raised; helper scripts not run). Confidence Score 56, band Low (calculation R25)." (shot CP-3_s-62.png, crop y≈730-830)
   - Problem: An internal status block is shown to the reader as a prose paragraph. It contains snake_case field names, pipeline wording ('helper scripts not run', 'Execution mode', 'phase', 'output mode Generic Portfolio-Fit Logic') and an unexplained 'Confidence Score 56'. Because the renderer swaps the module codes for names, it also reads 'Security selection Completed with Limitations' three times with different gap lists, which makes no sense to a reader.
   - Fix: Keep this status line off the reader page (or move it to a metadata panel), and state the confidence level in plain words inside the bottom line if it matters.
2. **High · narrative** (Saboteur, Auditor)
   - Where: line 64: "Monitoring should focus on any new special dividend or secured issuance, the refinancing of the 2027 subordinated notes..." vs line 30: "If yield-to-worst data arrives, the default lean is towards secured paper."
   - Problem: The Recommendation drops the conditional secured-over-subordinated preference that the Bottom line states. The table gives every tranche the same 'Unclear / Requires More Work', so a committee member who reads only this section sees no instrument preference at all and could treat the classes as interchangeable.
   - Fix: Carry the conditional preference (secured first; subordinated only if yield-to-worst shows a clear pickup) into the Recommendation sentence and the table's Recommendation column.
3. **Medium · narrative** (New reader)
   - Where: line 64: "TransDigm debt is Requires More Work because the fundamental profile is a low-business-risk, high-financial-policy-risk credit that can carry its stack, while relative value is Unclear for want of yields, spreads and comparables, and the subordinated notes sit beneath..."
   - Problem: The opening sentence runs to about 60 words, chains three clauses and uses a status label as a predicate ('is Requires More Work'). The judgement gets lost, and the paragraph largely repeats the Bottom line.
   - Fix: Open with one short judgement sentence (for example, 'No tranche can be recommended yet; secured paper is the provisional lean'), then give the reasons in separate short sentences.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: line 64: "lifts net leverage towards the 7.25x incurrence level"; line 69: "Moderate" / line 71: "High" under "Recovery sensitivity"
   - Problem: The 7.25x figure has no stated ratio basis or covenant source, so the reader can't tell which test it is. The Recovery sensitivity grades are ordinal labels with no scale or definition, and the Limitations section admits no recovery waterfall exists. Without that context, 'Moderate' for secured debt suggests a precision the run doesn't have.
   - Fix: Name the covenant test behind 7.25x (ratio, net or gross, and which agreement), and define the recovery labels as ordinal ranking only in the column header or a table note.
5. **Medium · narrative** (Auditor)
   - Where: line 64: "renewal of the securitization by 2025-07-11"; line 65: "Basis: Fundamental credit synthesis (CP-2); Forward credit model (CP-2G); Legal and covenant interpretation (CP-4)"
   - Problem: The securitization renewal date and the 7.25x level are not traceable to the issuer filing. The Basis cites only upstream modules by code, and on screen the paragraph shows no Basis chip at all, so the reader cannot check these figures.
   - Fix: Render the paragraph's Basis line on screen and cite the filing page for the securitization date and the incurrence ratio.
6. **Medium · visual** (Saboteur, Auditor)
   - Where: Recommendation table, Market level column, CP-3_s-62.png crop x≈480-800, y≈410-600
   - Problem: '99.91%' and '99.51%' are rendered bold monospace (the verified-figure style), while '101.40% to 105.80%; 103.50% aggregate' and '96.67% and 97.20%' are plain text. Prices in the same column therefore look as if they carry different levels of verification, which they do not.
   - Fix: Use one style for every price in the column: either all verified-figure chips or all plain.
7. **Low · visual** (New reader)
   - Where: Recommendation table, Relative value and Recommendation columns, CP-3_s-62.png y≈400-600
   - Problem: The last two columns repeat the same 'Unclear' / 'Requires More Work' in every row, and 'Requires More Work' wraps onto two lines. That is wasted width in a wide table that shows no differentiation between tranches.
   - Fix: Collapse the uniform values into a single caption above the table and give the space to a column that differs by tranche, such as the conditional preference or the price change during FY2024.
8. **Low · visual** (Auditor)
   - Where: Status paragraph below the table, CP-3_s-62.png y≈610-690
   - Problem: The status block is set in the same body type as the analysis immediately below the table, so it looks like part of the recommendation and adds an undifferentiated four-line wall of text.
   - Fix: Remove it from the reader view, or visually separate it as muted metadata.

### Events: Instruments

Kind: timeline · handoff lines 86-103 · verdict **BLOCK**

- Narrative: This is a data section with no prose to judge. Its table omits the two nearest dated refinancing tests that the module's own key findings and monitoring triggers name (the 2027-11-15 subordinated notes and the 2025-07-11 securitization), and a third of its columns carry no information.
- Visual: The timeline strip is unlabelled and monochrome, has overlapping dots and starts in 2028. The table is dominated by repeated five-line file names and dates that wrap mid-value.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 90: "Part of the FY2028 cluster with the 2027 subordinated notes recorded in the source readiness lane"; the table runs 2028-08-15 to 2033-01-15 (lines 90-102)
   - Problem: The table leaves out the 2027-11-15 maturity of the USD 2,650 million 5.50% subordinated notes, which line 43 calls "the refinancing hinge of the stack". It also leaves out the 2025-07-11 securitization renewal (USD 487 million) flagged at line 182. A reader using this table as the maturity schedule sees nothing before August 2028 and misses the two nearest refinancing tests. The cell admits the omission only through pipeline wording.
   - Fix: Add rows for 2025-07-11 (securitization) and 2027-11-15 (2027 subordinated notes) so the table is the full dated schedule, and remove the reference to another module's lane.
2. **High · visual** (Saboteur, New reader)
   - Where: Timeline strip 'Instruments', CP-3_timeline.png, crop CP-3-134-a.png (original y≈230-300)
   - Problem: The strip has 13 identical blue dots with no labels, no amounts and no year ticks, only the two end dates 2028-08-15 and 2033-01-15. The first two dots overlap. Secured, subordinated and loan maturities cannot be told apart. Because it starts in 2028, it reinforces the missing 2027 hinge and 2025 securitization maturities.
   - Fix: Add year ticks, colour or mark each dot by rank (secured, subordinated, loan, facility), label or size each dot by amount, separate the dots that overlap, and include the pre-2028 maturities.
3. **Medium · narrative** (New reader, Auditor)
   - Where: lines 88-102: columns 'Date precision' (all 'day'), 'Published' (all '—'), 'Status' (all 'Scheduled — maturity date')
   - Problem: Three of seven columns hold the same value in every row and tell the reader nothing. 'Date precision' is pipeline vocabulary. They take width from the event and credit-relevance text.
   - Fix: Drop the constant columns, or fold them into a single note above the table, and give the width to amount, rank and credit relevance.
4. **Medium · narrative** (Saboteur)
   - Where: line 97: "Secured note maturity"; line 101: "Secured note maturity"; line 96: "Secured loan maturity"
   - Problem: Several 'Credit relevance' cells only restate the event type and give no judgement. Other cells carry real ones, such as the FY2028 cluster or the dividend recap. The reader cannot tell which maturities matter.
   - Fix: Give each row a credit consequence (for example refinancing size relative to the cluster, or rank exposure), or leave the cell blank rather than repeat the event.
5. **Medium · visual** (New reader)
   - Where: Events: Instruments table, CP-3_s-86.png rows 2028-08-15 to 2033-01-15 (display y≈215-1320); Source column
   - Problem: The same 60-character file name 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 59/60' wraps to five lines in all 13 rows. It uses the widest column and makes each row about four times taller than its content needs. The dates also wrap mid-value ('2028-08-' / '15') next to a 'Basis' chip.
   - Fix: Show a short source label such as '10-K FY2024, p. 59' and keep dates on one line so the table reads as a schedule.
6. **Low · narrative** (Saboteur)
   - Where: line 93: "Committed liquidity must be extended before FY2029 notes"
   - Problem: The revolver matures on 2029-02-27, after the 2029-01-15 subordinated notes and before the 2029-03-01 secured notes. 'Before FY2029 notes' is ambiguous about which maturities the revolver has to backstop, and in which fiscal year.
   - Fix: Name the specific maturities the revolver has to cover, with their dates.
7. **Low · visual** (Auditor)
   - Where: CP-3_timeline.png: the timeline strip sits above 'Request' (original y≈230), while the Events: Instruments table is about 1,800 px lower
   - Problem: The timeline and the table that explains it are separated by Request, Sources, Recommendation and Relative value. The reader cannot match a dot to its row without scrolling back and forth.
   - Fix: Place the timeline directly above or beside the Events: Instruments table, or link each dot to its row.

### Gaps

Kind: prose/table · handoff lines 418-430 · verdict **BLOCK**

- Narrative: The Gaps table is the right shape for the limitations step, but it reads as a pipeline work list: tooling and rerun steps, "context" sources, internal rating labels. It also does not rank which gaps actually prevent a recommendation.
- Visual: The table renders legibly at 1440 px with no overlap or clipping. However, raw .jsonl filenames wrap across three lines in the Source column, and a stray "Basis" chip attaches to two gap names.

1. **High · narrative** (Auditor, New reader)
   - Where: L429 "Helper scripts not run | Confidence, completeness, recovery waterfall scripts | Checks and score done by hand | Rerun when tooling available"; also L423 "Open the enterprise workbook in a connected run", L424 "Attach and rerun legal module", L426 "Valuation or restructuring module"
   - Problem: These rows describe the pipeline (scripts, tooling, connected runs, modules, reruns), not the credit. A committee reader cannot act on them, and the house rule bars pipeline vocabulary on screen.
   - Fix: Drop the tooling row, or restate it as its reader consequence (e.g. that the confidence score is unchecked), and phrase follow-ups as the data or analysis needed rather than module or rerun steps.
2. **High · narrative** (Auditor, Saboteur)
   - Where: Source column, L422/423/427/429: "context" (5 of 8 rows, including L424/L426 module names "Legal and covenant interpretation (CP-4)" / "Financial data foundation (CP-1)")
   - Problem: "context" is an internal request label, not a source. Rows that point to other modules cite pipeline stages, not evidence. The reader cannot trace why a gap exists, and the Source column ends up empty of real sources.
   - Fix: Use a reader-facing source (e.g. "Not in the files supplied" or the specific document), or leave the cell as an explicit gap, and never show "context".
3. **Medium · narrative** (New reader)
   - Where: L422 "RV Unclear for all tranches; no Preferred"; L424 "Priming and release capacity unscored; Structural Only confidence"; L427 "Sizing Requires More Work"; L422 "YTW"
   - Problem: Internal capitalised rating labels (Unclear, Preferred, Structural Only, Requires More Work) and the undefined abbreviations RV and YTW mean nothing to a reader without this module's scale definitions.
   - Fix: Spell out what each effect means for the recommendation in plain words (e.g. "no tranche can be ranked on value"), and define or expand RV and YTW.
4. **Medium · narrative** (Saboteur)
   - Where: L422-429 row order, with the tag "[Insufficient Information]" only on L422, L424 and L427; L425 "Above-par secured prices may be capped"
   - Problem: The table is not ordered by materiality and does not say which gaps decide the call. Market compensation and legal documents block the recommendation outright, but they sit alongside identifier and tooling gaps. The tag also appears on only three rows, although call schedules and recovery inputs are equally missing. The call-schedule row's effect is hedged ("may be capped") with no size.
   - Fix: Order rows by impact on the recommendation, apply the missing-data tag consistently, and say for each gap whether it changes the view.
5. **Medium · visual** (Auditor, New reader)
   - Where: Gaps table, Source column, rows Call schedules and Security identifiers (tmp/CP-3-139-a.png, right column, about y 350-610)
   - Problem: The raw filename "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" wraps over three lines and exposes an internal .jsonl extract name instead of a document a reader recognises.
   - Fix: Render the source as "TransDigm FY2024 10-K, p. 146" (the document title plus page).
6. **Medium · visual** (Auditor)
   - Where: Gaps table, Gap column: "Call schedules Basis" and "Security identifiers / Basis" (tmp/CP-3-139-a.png, left column, about y 350 and 567)
   - Problem: A grey "Basis" chip appears next to the gap name on only the two rows whose Source is a file. It looks like part of the gap title and has no meaning in a gaps table, so the column reads inconsistently.
   - Fix: Suppress the Basis chip in Gaps tables, or show it uniformly in the Source cell where the reader expects a reference.
7. **Low · visual** (New reader)
   - Where: Gaps table header and rows (shots2/CP-3_s-418.png, y about 1590-2215 at full resolution)
   - Problem: The table is otherwise clean: five columns, generous row padding, no clipping. But it carries no visual weighting, so the two gaps that block the recommendation look the same as the minor ones.
   - Fix: Emphasise blocking gaps (for example, bold the effect text or add a status chip) so the reader's eye goes to them first.

### Sources

Kind: prose/table · handoff lines 5-22 · verdict **BLOCK**

- Narrative: This section is a source list, not analysis, but pipeline vocabulary ('handoff', 'transport', 'method block'), a garbled code-replacement phrase and an internal 'context' row reach the reader, and it breaks the house language rule.
- Visual: The two tables are clean and readable in type and spacing, but hash columns take most of their width, the second table repeats module names in two columns, and the raw .jsonl filename wraps over four lines; there is no chart in this section.

1. **High · narrative** (Auditor, New reader)
   - Where: line 12 "| Supplied handoff | Module | sha256 |"; line 21 "Not available in this transport: ... companion step files beyond the method block, and upstream ... handoffs (not supplied)." (rendered on screen in CP-3_s-5.png, Sources block)
   - Problem: Pipeline words the house standard bans ('handoff', 'transport', 'companion step files', 'method block', 'upstream') appear on the reader's page as a column header and in the closing paragraph. A credit committee member cannot tell what these words mean.
   - Fix: Use reader language, e.g. 'Earlier analysis used' for the table header, and say plainly which data the reader does not have (no peer levels, no ratings, no recovery work).
2. **Medium · narrative** (New reader, Saboteur)
   - Where: line 21 "the CP-3A/CP-3B companion step files beyond the method block", rendered as "the Security selection/Security selection companion step files beyond the method block" (CP-3_s-5.png, paragraph under the second table)
   - Problem: Replacing the module codes with names produced a repeated, meaningless phrase. The reader cannot tell what is missing, which hides the fact that peer benchmark, ratings and recovery inputs were not available for a relative-value call.
   - Fix: Name each missing input once, in plain words, and say why it matters to the relative-value conclusion; drop the internal step-file reference completely.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: line 10 "| context | f7b95e1f... | Run settings: quotes, ratings, peers, issuer market data blank; portfolio workbook not attached; not issuer evidence |"
   - Problem: An internal input named 'context', with a hash, is listed as a source even though the row itself says it is not evidence. It also hides here, in a terse table cell, the most important limitation for relative value: no quotes, ratings or peer data.
   - Fix: Remove 'context' as a source row and state the missing market data in the module's Limitations, where the reader looks for it.
4. **Medium · visual** (New reader, Auditor)
   - Where: Both Sources tables, sha256 column (CP-3_s-5.png, crop CP-3-126-a.png, y≈40-580)
   - Problem: 64-character hashes take about 40% of each table's width. This pushes the useful 'Use in this module' text into a narrow, six-line column. The hashes mean nothing to a portfolio manager.
   - Fix: Move hashes to the Evidence page or a tooltip and give the width to the source description.
5. **Medium · visual** (New reader)
   - Where: Second table, 'Supplied handoff' vs 'Module' columns, e.g. "Financial data foundation | Financial foundation", "Fundamental credit synthesis | Fundamental credit" (CP-3-126-a.png, y≈320-580)
   - Problem: Two columns show almost the same name for each row, so the table repeats itself without telling the reader anything more. The difference between the two names looks like an error.
   - Fix: Show one column with the module's page name (linked) and, if useful, what this module took from it.
6. **Low · narrative** (New reader)
   - Where: line 21 "Not relied on: the Q2, Q3 FY2024 and Q1 FY2025 quarterly filings and the PDF annual report (duplicate per source readiness). Not available in this transport: ..."
   - Problem: Two different lists (excluded on purpose vs unavailable) run together in one dense paragraph, and 'duplicate per source readiness' is shorthand only someone who knows the pipeline would understand.
   - Fix: Split it into two short labelled lists: 'Excluded (duplicates of the 10-K)' and 'Not available'.
7. **Low · visual** (New reader, Auditor)
   - Where: First table, Source cell "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl Basis" (CP-3-126-a.png, y≈90-165)
   - Problem: The raw ingestion filename (with the .jsonl extension) wraps over four lines, followed by an unexplained 'Basis' chip. The reader sees a file path, not 'TransDigm FY2024 Form 10-K'.
   - Fix: Show a readable document title (issuer, form, fiscal year, filing date) and keep the filename for the Evidence page.
8. **Low · visual** (Auditor)
   - Where: On this page navigation: "Request, Sources, Recommendation, Relative value, Portfolio Fit" (CP-3_s-5.png, left nav y≈905-990)
   - Problem: Sources sits in the middle of the module, with Recommendation, Relative value and Portfolio Fit coming after it. The reader reaches the source list before the analysis it supports, which is not the reading order of the VMO2 reference.
   - Fix: Put Sources after all analytical passages, at the end of the module's reader content.

### Bottom line

Kind: reader passage · handoff lines 25-32 · verdict **BLOCK**

- Narrative: The bottom line comes first and has a judgement. But that judgement is internal scale labels, not a stance, and it leaves out the module's own key fact that the junior notes currently pay less than the secured notes. Its leverage band has no measure, period or basis label. Source references correctly sit in the Basis lines and are reached through the figure chips (reader.js:322-324), not in the sentences.
- Visual: This section has no chart, map or timeline. The layout problems are about 16 lines of heavy bold display text with mixed monospace figure chips, an empty right third of the page, a heading hidden under the sticky bar at the anchor, and pipeline words in the side navigation.

1. **High · narrative** (Saboteur, New reader (promoted from Medium))
   - Where: line 27: "TransDigm's debt earns Requires More Work with relative value Unclear: the fundamentals can carry the structure, but the pack holds no yields, spreads, peer levels or loan-market data"
   - Problem: The opening judgement is two capitalised labels from an internal rating scale ("Requires More Work", "Unclear"), and the page never says what they mean or what the reader should do now: hold, avoid or wait. "Earns" makes a non-decision sound like a rating. "The pack" is pipeline wording.
   - Fix: Open with a plain-English stance that a committee can act on, e.g. no tranche can be preferred on value yet and secured paper is preferred on structure alone, and translate or define the labels; say "the filings supplied" instead of "the pack".
2. **Medium · narrative** (Saboteur)
   - Where: line 30: "If yield-to-worst data arrives, the default lean is towards secured paper. Subordinated notes should be considered only if their pickup clearly pays for that position."
   - Problem: The bottom line implies a subordinated pickup exists to be tested. It leaves out the module's own finding (line 41) that on current yield the junior notes pay less (4.78% against 5.92%) and that year-end prices show no subordination penalty (line 39). A reader who stops at the bottom line misses the fact that most affects the decision.
   - Fix: State in the bottom line that on the only data available the subordinated notes currently pay less running income than the secured notes, so the secured lean costs nothing on today's evidence.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: line 30: "Secured debt of USD 19,702 million ranks ahead of USD 4,600 million of subordinated notes, which therefore sit between 4.72x and 5.82x of EBITDA As Defined."
   - Problem: The reader is not told this is a gross attachment/detachment band, which EBITDA period it uses, or whether the debt is before or after the October 2024 USD 3,000 million secured issue. "EBITDA As Defined" is not defined. The same page also quotes 5.55x pro forma net leverage (line 37), a second basis with no label.
   - Fix: Name the measure (gross leverage through the subordinated class), its period and date, and its relation to the 5.55x pro forma net figure, and define EBITDA As Defined in a few words.
4. **Medium · narrative** (New reader)
   - Where: line 27: first sentence, about 60 words, from "TransDigm's debt earns Requires More Work" to "ahead of the subordinated notes."
   - Problem: One sentence carries the verdict, two labels, the data gap and the financial-policy concern. With the first paragraph's price list and the second paragraph's leverage band, the bottom line runs to about 16 lines of display type, which is too long for a reader looking for the call.
   - Fix: Split it: one short verdict sentence, one sentence on why value cannot be judged, then the evidence.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-3_bottom-line.png, main column y≈190–700 (cropped to tmp/CP-3-127-a.png)
   - Problem: Both bottom-line paragraphs are set in large heavy bold, about 16 lines, a wall of emphasis with no hierarchy between verdict and supporting evidence. Monospace, dotted-underlined figure chips inside the bold display font break the line rhythm, and the right third of the page is empty.
   - Fix: Set only the verdict sentence in display weight and the supporting sentences in body weight, using the width more evenly, as in the VMO2 reference.
6. **Medium · visual** (Auditor)
   - Where: CP-3_bottom-line.png, left 'On this page' navigation y≈1030–1880 and run bar y≈162
   - Problem: Next to this section the screen shows pipeline vocabulary: "Analytical appendix — complete canonical registers", "a method step Portfolio input gate", about 30 lowercase "a method step …" entries, and the run id "TDG-PROOF-SNAPSHOT-OPUS-002". The house standard forbids "canonical" and "gate" as reader language.
   - Fix: Rename or collapse the method-step entries into reader headings and drop "canonical" and "gate" from the visible navigation.
7. **Low · narrative** (Saboteur)
   - Where: line 27: "It puts the six secured note series at 103.50% of par in aggregate"
   - Problem: The aggregate hides the 101.40% to 105.80% spread across series. It also leaves out the limitation (line 58) that call prices may cap the above-par secured notes, which bears directly on comparing these prices.
   - Fix: Give the range next to the aggregate, or note briefly that above-par secured prices may be capped by call levels.
8. **Low · visual** (Auditor)
   - Where: CP-3_bottom-line.png, top of main column y≈180–200
   - Problem: At the section anchor the "Bottom line" heading does not show: the text starts directly under the sticky run bar, so the reader lands mid-section with no heading.
   - Fix: Offset the anchor scroll by the sticky header height so the section heading stays visible.

### Relative value

Kind: prose/table · handoff lines 76-80 · verdict **CONCERNS**

- Narrative: The paragraph puts its judgement first and the price figures match the appendix, but it uses pipeline wording ('the pack', 'workbook could not be opened here'), it leaves out the module's own finding that junior paper yields less than senior, and it does not mark that the prices are fair-value estimates rather than traded quotes.
- Visual: The section renders as one dense paragraph with monospace, underlined figures, and unlike the Portfolio Fit paragraph below it, it shows no Basis link even though the handoff has one.

1. **High · visual** (Auditor, Saboteur)
   - Where: Relative value paragraph, shots2/CP-3_s-76.png crop x330-1420 y210-340 (tmp/CP-3-132-a.png); handoff line 79 "Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 172–173; context; calculation R02; calculation R04; calculation R08; calculation R10"
   - Problem: The handoff has a Basis line for this paragraph, but the page shows no Basis link after it. The Portfolio Fit paragraph directly below does show one. The reader cannot trace the four quoted prices to the filing or to the calculations, so the house rule that sources live in each paragraph's Basis line is broken on screen.
   - Fix: Render the paragraph's Basis link like the neighbouring paragraphs do, so every quoted price can be traced to its source page and calculation.
2. **Medium · narrative** (Saboteur)
   - Where: line 78: "These prices mostly reflect coupon differences, so they say nothing about compensation per unit of risk."
   - Problem: This dismisses all the price evidence, yet the module's own appendix (T3.5, line 145 onward) records current yield of 4.78% on the 2029 subordinated notes against 5.92% on the 2033 secured notes. That is a negative junior pickup, the one relative-value signal the committee most needs. The claim that prices reflect coupons also has no stated basis.
   - Fix: State the coupon-over-price comparison the module already computed (junior paper yielding less than senior), with its coupon-over-price-only caveat, instead of saying the prices tell nothing.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 78: "The pack has no yields, spreads ... and the maintained loan-market workbook could not be opened here."
   - Problem: "The pack", "the maintained loan-market workbook" and "could not be opened here" describe the pipeline's own process, not the issuer. A portfolio manager does not know what pack or workbook is meant, or why its absence matters.
   - Fix: Say in reader terms which market data was unavailable as of 2024-09-30 (yields, spreads, loan bids, peer levels), with no reference to internal files or the run environment.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 78: "They show secured notes at 101.40% to 105.80% of par, subordinated notes at 96.67% to 99.51% and term loans at 99.91%."
   - Problem: These are the issuer's year-end fair-value disclosures, and the term-loan figure is a Level 2 estimate, not a traded quote (T3.5 line 147 says so). The sentence presents them alongside each other as though they were comparable market prices. The ranges also hide which subordinated series sits at 99.51% (the 2027 notes) and which sit at 96.67% and 97.20% (the 2029 notes).
   - Fix: Label these as fair-value disclosures that cannot be traded on, mark the term-loan figure as a Level 2 estimate, and tie each price to its series.
5. **Low · narrative** (New reader)
   - Where: line 78: "Relative value is Unclear for every tranche."
   - Problem: The capitalised "Unclear" is an internal rating label used as if it were a word in the sentence. The judgement is also only that no view is possible, and the paragraph never says which way the limited evidence leans.
   - Fix: Give the plain-English judgement first (for example, that no tranche can be shown to pay enough for its risk on this evidence) and keep the label for the table.
6. **Low · visual** (Auditor)
   - Where: Relative value paragraph, tmp/CP-3-132-a.png: figures 101.40%, 105.80%, 96.67%, 99.51%, 99.91% in monospace with dotted underline
   - Problem: Five monospace, underlined figures inside a seven-line justified paragraph break up the reading line. With no table, the reader has to pull a four-tranche price comparison out of running text.
   - Fix: Put the per-tranche prices in a small table with a Source column, or keep the figures in body type within the sentence.

### Calculations

Kind: prose/table · handoff lines 386-417 · verdict **BLOCK**

- Narrative: The arithmetic I checked is correct: R11 = 11,385, R12 = 4,526, R21 = 24,605, the principals 11,000 / 4,600 / 24,302, and R18, R19 and R25. The problem is that the section reads as an internal ledger. It has no bottom line, it leaks pipeline wording ("calculate tool", "lineage weights", "register cells", Source "context"), and it mixes current and prior-year prices.
- Visual: There is no chart in this section. The six-column table renders cleanly and is readable at 1440 px. Its Source column of wrapped raw file names and its ten-decimal results make it long and dense: about 1,350 px for 25 rows.

1. **High · narrative** (Auditor, New reader)
   - Where: L414-416: "Confidence E: sum of lineage weights over 10 material claims" / "6E + 4C with C = 70 (critical register cells gap-bound for market, legal, portfolio fields)" / "(0.6E + 0.4C) × S, S = 0.7 partial, P = 0"; Source column "context"
   - Problem: These rows use internal scoring language ("lineage weights", "critical register cells", "gap-bound") and leave E, C, S and P undefined, so a reader who has not seen the pipeline cannot use the "55.72 (56, Low)" confidence result. Their Source is the pipeline word "context", not a document a reader could check.
   - Fix: Name each factor in plain words (evidence quality, completeness, scope), state what Low confidence means for the recommendation, and cite a real basis or mark the row as a method assumption.
2. **Medium · narrative** (Auditor, New reader)
   - Where: L392 Source: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 145, 172" (repeated in R05, R11, R15-R21); screenshot CP-3_s-386.png, Source column y≈300-1400
   - Problem: The Source column shows raw extraction file names, including the internal ".jsonl" suffix and the accession number. Each one wraps to three lines and tells the reader less than "FY2024 10-K, p.172" would.
   - Fix: Show a reader label such as "TDG FY2024 10-K (30 Sep 2024), pp. 145, 172" and keep the file identity in the Sources list.
3. **Medium · narrative** (New reader)
   - Where: L388: "All arithmetic used the calculate tool. Inputs USD millions from the annual filing at 2024-09-30 unless stated; prices are fair value divided by gross principal"
   - Problem: The section opens with a pipeline detail ("the calculate tool") and never says what the 25 rows show for credit. It does not say that the secured notes carry fair values above par (103.50%), that the subordinated notes sit below par (98.39%), or why that matters, so the reader gets a raw ledger.
   - Fix: Drop the tool reference and open with one sentence on what the figures show, for example the secured-versus-subordinated price gap and that these are issuer fair values, not market quotes.
4. **Medium · narrative** (Saboteur)
   - Where: L406-408: "R15 | 4.625% 2029 notes FV / principal, 2023-09-30" / "R16 | 4.875% 2029 notes, 2023-09-30" / "R17 | 5.50% 2027 notes, 2023-09-30"
   - Problem: Prior-year (2023-09-30) prices are mixed into a table whose intro says all inputs are 2024-09-30 "unless stated". The only marker is a date suffix in the Formula text, and R16/R17 drop the "FV / principal" wording, so 87.20% can be misread as a current price.
   - Fix: Give the prior-year rows their own labelled group or a Period column, and use the same formula wording on every row.
5. **Medium · narrative** (Saboteur)
   - Where: L409-411: "R18 | Current yield, 4.625% 2029 notes | 0.04625 / R04 | 0.0478448276 (4.78%) | fraction"
   - Problem: The yields are labelled "Current yield" but are computed on issuer fair-value prices, not market quotes. Only the intro line carries that caveat, so in a relative-value module a reader can take 4.78% and 5.92% as market compensation.
   - Fix: Label these rows "Current yield on issuer fair value (not market)" in the Formula or Unit cell itself.
6. **Low · visual** (Auditor)
   - Where: CP-3_s-386.png Result column, R11/R12/R21 (y≈828, 893, 1369): "11385", "4526", "24605"
   - Problem: The USD sums are bold and have no thousands separators, while their Inputs cells use separators ("11,385"). Fraction results show ten decimal places ahead of the percentage, so the useful figure sits second and wraps to two lines.
   - Fix: Show results as "11,385" and "99.91%" first, with full precision at most secondary, and format all rows the same way.
7. **Low · visual** (New reader)
   - Where: CP-3_s-386.png Source column R13/R14/R22 (y≈926-990, 1435): "Same; Legal and covenant interpretation (Legal & covenants)"
   - Problem: "Same" depends on scanning back up a 25-row table, and the cross-module reference repeats itself in two forms. The "Basis" chip under the ID appears on only some rows, which looks inconsistent.
   - Fix: Repeat a short source label on every row instead of "Same", and use one name for each cited module.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 431-434 · verdict **BLOCK**

- Narrative: Both passages are run plumbing, not analysis. The Request opens with a garbled sentence produced by the module-name substitution and shows the raw pathway id. Next module is a set of instructions to other modules in pipeline language, and it is the only place the secured-over-subordinated lean appears.
- Visual: There is no chart in this section. Both blocks are plain paragraphs that render cleanly with no clipping, but the Request block sits mid-page between Timeline and Recommendation, and the Next module note looks no different from the analytical prose.

1. **High · narrative** (Auditor, New reader)
   - Where: Next module, line 433: "CP-5 should validate the evidence trace for this handoff's fair-value prices and structural claims, and CP-6 should debate a Requires More Work stance" (shown in CP-3_s-431.png, bottom, as "Evidence validation should validate the evidence trace for this handoff's...")
   - Problem: This paragraph gives orders from one module to the next, and the reader sees it. It uses pipeline vocabulary ("handoff", "rerun", other modules as actors) that the house standard bans. A committee member gets nothing from it they can act on.
   - Fix: Hide the Next module section on reader pages, or rewrite it as a reader-facing 'what would change this view' line with no module names and no word 'handoff'.
2. **Medium · narrative** (New reader, Saboteur)
   - Where: Request, line 3: "CP-3 relative value and security selection, including instrument preference..." rendered in CP-3_s-1.png top as "Security selection relative value and security selection, including..."
   - Problem: The display layer replaces the module code with its name, which leaves a garbled, repeated opening phrase as the first sentence the reader meets in this section.
   - Fix: Make the name substitution use the grammar of the sentence, e.g. 'Relative value and security selection, including...'. Do not prefix the module name onto a sentence that already names the task.
3. **Medium · narrative** (Auditor)
   - Where: Request, line 3: "Pathway: credit_snapshot."
   - Problem: The pathway appears as a snake_case internal identifier. It is pipeline wording, not reader language, and the run banner above already says "Credit snapshot".
   - Fix: Drop the pathway clause from the reader view, or show it as 'Credit snapshot'.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Next module, line 433: "CP-6 should debate a Requires More Work stance with Unclear relative value, testing whether a secured-over-subordinated lean is justified"
   - Problem: The secured-over-subordinated lean surfaces only here, in a closing note about the workflow, and only as something to be debated. The recommendation table rates every tranche the same "Requires More Work"/"Unclear". A reader who stops at the table misses the module's real tilt. A reader who gets this far finds the tilt neither endorsed nor rejected.
   - Fix: State the lean, and how firmly it is held, in the bottom line or recommendation where the judgement belongs, rather than only in a routing note.
5. **Medium · visual** (Auditor, New reader)
   - Where: CP-3_s-1.png, left 'On this page' rail, and the Request block at y≈190-265 sitting between Timeline and Recommendation
   - Problem: Request and Sources appear in the middle of the page: after Limitations and Timeline, before Recommendation and Relative value. The scope statement interrupts the judgement passages instead of framing them or sitting in the appendix.
   - Fix: Put the Request/scope line at the top of the module, or move it to the appendix with Sources, so Recommendation follows straight on from the judgement passages.
6. **Low · narrative** (New reader)
   - Where: Next module, line 433: "CP-3 should be rerun once quotes, call schedules and the executed legal documents are supplied."
   - Problem: This repeats the Required follow-up column of the Gaps table directly above, so the reader gets the same list twice.
   - Fix: Keep the follow-up list in the Gaps table only.
7. **Low · visual** (Saboteur)
   - Where: CP-3_s-431.png, Next module at y≈1870-1945, immediately after the dense Gaps table
   - Problem: The routing note is set in the same body style and weight as the analytical prose, so nothing marks it as non-analytical. It reads like part of the conclusion.
   - Fix: If it is kept at all, set it apart visually (muted, collapsed or labelled as workflow) so it is not mistaken for analysis.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 48-52 · verdict **CONCERNS**

- Narrative: The passage does present a real contrary case with conditions that would change the view, but it uses an unsourced single-B peer frame, drops periods and the leverage basis, leaves its triggers unquantified, and is one dense paragraph that opens against a workflow label rather than a stated view.
- Visual: This section has no chart; it is plain prose with readable contrast and line length, but its Basis line is not visible on the page, and spacing before the next Timeline block is cramped.

1. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 50: "peer levels for single-B subordinated aerospace paper do not exceed them"
   - Problem: The rating bucket that sets the peer test is stated as fact, but the module's own Sources row (line 10) says ratings are blank in this run, and the only "Single-B" in the run is a placeholder example in the CP-3 instructions (instructions/CP-3.md:72). A committee would read this as an evidenced rating.
   - Fix: Either cite a sourced rating in the Basis line, or name the peer set as an assumption that has to be confirmed once ratings are supplied.
2. **Medium · narrative** (Saboteur)
   - Where: line 50: "net leverage peaks at 5.65x and interest cover never falls below 3.01x"
   - Problem: No periods and no leverage basis are given. The source (CP-2G response line 36) puts the peak in FY2026 and the cover trough in FY2025, measured on carrying debt. Elsewhere on the same page leverage is 5.55x pro forma and 4.72x–5.82x of EBITDA As Defined, so a reader cannot tell whether these figures are comparable.
   - Fix: Give each figure its fiscal year and its leverage definition, matching the forward model.
3. **Medium · narrative** (Saboteur)
   - Where: line 50: "That case wins if yield-to-worst shows the subordinated notes clearly above the secured notes ... The opposite case wins if the subordinated pickup over secured paper is thin"
   - Problem: The triggers that would change the view have no thresholds: "clearly above" and "thin" are not quantified in basis points. The opposite case also needs a thin pickup AND a new secured dividend together, so a reader cannot tell what market print would actually flip the recommendation.
   - Fix: State each trigger as a measurable test, such as a subordinated-over-secured yield-to-worst pickup above or below a stated number of basis points, and say whether the conditions are joint or separate.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 50: "The strongest case against Requires More Work is that the fundamentals already do most of the job." ... "push a secured preference into an Avoid on the subordinated class"
   - Problem: The opening argues against a workflow status label ("Requires More Work") instead of stating the view being challenged, which is that the secured layer is preferred. All nine sentences, covering contrary evidence and both directions of change, sit in one unbroken paragraph of about 170 words.
   - Fix: Open by naming the view being contested in plain words, then split the passage into the contrary evidence and two short 'what would change the view' conditions.
5. **Medium · visual** (Auditor)
   - Where: Screenshot CP-3_contrary-evidence.png, crop (330,200)-(1440,1100) saved as scratchpad/tmp/CP-3-129-a.png: paragraph ends at "Avoid on the subordinated class." and goes straight to the Limitations heading
   - Problem: The handoff's Basis line (line 51: "Forward credit model (CP-2G); Fundamental credit synthesis (CP-2); calculation R04") is in data.js but no Basis line or chip appears under the paragraph on screen. Table rows on the same page do show a "Basis" chip, so this passage's sources cannot be seen.
   - Fix: Show the paragraph's Basis line (as reader names, with no CP codes), the same way table rows show their Basis chip.
6. **Low · narrative** (Saboteur)
   - Where: line 50: "The discounted subordinated notes also mature within about five years"
   - Problem: From the 2024-09-30 as-of date, the January 2029 notes mature in about 4.3 years and the 2027 notes in about 3. The pull-to-par that drives the contrary case is never quantified, so the case rests on an unmeasured benefit.
   - Fix: Give the actual maturity dates and the approximate annual pull-to-par implied by the 96.67% price.
7. **Low · visual** (New reader)
   - Where: Screenshot CP-3_contrary-evidence.png, y approx 980-1010 (scaled): last Limitations bullet "exit risk cannot be assessed for any tranche." immediately followed by the "Timeline" heading
   - Problem: There is almost no space between the end of Limitations and the next block's heading, unlike the gap above "Limitations". The section boundary is easy to miss.
   - Fix: Use the same vertical spacing before the Timeline heading as between the other section headings.
8. **Low · visual** (New reader)
   - Where: Same crop: inline values "USD 2,038 million", "5.65x", "3.01x" set in bold monospace with dotted underline inside the prose
   - Problem: Monospace bold figures in the middle of a sentence break the reading rhythm and look like code. The prose column also fills only about 60% of the content width, leaving a wide empty band beside it.
   - Fix: Show inline figures in the body face (tabular numerals, optionally semibold) and keep the dotted underline only as the provenance cue.

### Portfolio Fit

Kind: prose/table · handoff lines 81-85 · verdict **CONCERNS**

- Narrative: The paragraph is short, plain and in the right register, but it opens with the data gap instead of the judgement, leaves out the module's sizing posture and gives an internal \"context\" as its basis.
- Visual: The section is a heading and one paragraph with no chart. It renders cleanly, but the page places it after Sources, the heading case is inconsistent and the lines are very long.

1. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 83: "No mandate, holdings, concentration limits or trading data were supplied, so portfolio fit is generic and no numeric size is given. Generically, the secured notes and term loans fit a defensive senior secured role once compensation is shown."
   - Problem: The paragraph opens with the data gap instead of the view, and the module's actual sizing posture ("Requires More Work", line 75) never appears here. The only judgement given depends on a condition the run cannot test ("once compensation is shown"), so a skimming reader can take away "secured paper fits" as a positive call.
   - Fix: Lead with the posture (Requires More Work, no size), then the conditional fit by tranche, then the missing mandate and market levels as the reason.
2. **Medium · narrative** (New reader, Auditor)
   - Where: line 85: "Basis: context"
   - Problem: The only basis given is the internal word "context". It names no document or input, and a reader who has not seen the pipeline cannot tell that it means the run settings with the mandate left blank.
   - Fix: Name the basis in reader terms, for example "run settings: no portfolio mandate, holdings or limits supplied", or cite the relevant register row.
3. **Medium · visual** (Auditor, New reader)
   - Where: CP-3_s-81.png, left 'On this page' navigation (y about 900-1000 display px): Limitations, Timeline, Request, Sources, Recommendation, Relative value, Portfolio Fit
   - Problem: In the handoff, Portfolio Fit is a judgement subsection under Findings (lines 23-85). On the page it comes after Request and Sources, so the reader meets the source list before this judgement. That breaks the house order, where Sources closes the module.
   - Fix: Render Recommendation, Relative value and Portfolio Fit inside the findings block, before Request and Sources, as the handoff orders them.
4. **Low · narrative** (New reader, Saboteur)
   - Where: line 83: "The subordinated notes fit only a yield-carry role sized for policy-driven loss given default."
   - Problem: "Policy-driven loss given default" is shorthand that is neither explained nor given a number. The reader has to infer that it refers to dividend-recap-driven subordination, and gets no LGD range for sizing.
   - Fix: Say in plain words that the subordinated recovery depends on management's secured-funded payouts, and point to the recovery sensitivity if one exists.
5. **Low · visual** (Auditor)
   - Where: CP-3-133-a.png (crop of CP-3_s-81.png, x 330-1440, y 210-340): heading "Portfolio Fit" and paragraph
   - Problem: The heading uses title case while its neighbours use sentence case ("Relative value", "Events: Instruments"). The paragraph also runs the full content width, about 170 characters per line, which is slow to read. It then runs straight into a 12-row events table with no visual break.
   - Fix: Use sentence case ("Portfolio fit"), limit the prose to a readable measure (about 90-100 characters), and leave clear space before the next block.

## Committee decision (CP-6)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-6/26e68bc473935c4728e0a27c372af1a4241998ffdbffc34443d8dc57715c2ae1/1.response.md`

### Analytical appendix — complete canonical registers (part 1 of 2: from 'Source gate register')

Kind: register appendix · handoff lines 139-226 · verdict **BLOCK**

- Narrative: The register tables are well structured, but the section opens with a paragraph of process text, an unexplained scoring scale, sources that cannot be traced and leverage figures that are not reconciled. Together these would slow or mislead a committee reader.
- Visual: There is no chart in this section. The three tables are spaced readably and labels are not clipped, but value typography is inconsistent, a \"Basis\" chip repeats on every row, and the sidebar shows pipeline wording (\"canonical\", \"a method step ...\"). Not verified: the T6A.4, T6A.6 and T6A.7 tables and the line 141 paragraph fall below or above the screenshot; I judged them from the handoff text and data.js only.

1. **High · narrative** (Auditor, New reader)
   - Where: line 141: "Helper scripts (`prepare_invocation.py`, `validate_handoff.py`, `confidence_score.py`, `completeness_check.py`) were not run in this transport... all eight required registers (T6A.4, T6A.6, T6A.7, T6A.11, T6E.4..." (the same paragraph also has "CP-6 and CP-6A schema", "S = 0.7 (gate partial)", "qa_status Restricted", "`cpdr.adoptions`")
   - Problem: The appendix opens with a paragraph of pipeline internals: script names, "transport", register codes, module codes, "gate" and field names. This breaks the house vocabulary rule. The one reader-relevant fact in it, Confidence 53 (Low) and Restricted status, is buried in a formula. The text is in the page data (data.js), but the screenshot starts below it, so I did not see it on screen.
   - Fix: Remove the process paragraph from the reader page, or reduce it to one plain sentence giving the confidence level and the reason it is restricted.
2. **High · narrative** (Saboteur, New reader)
   - Where: line 213: "| Dimension | Score (1-5) | Bull Evidence | Bear Evidence | Chair Assessment | Source |"; line 221: "| Sponsor / governance alignment | 5 | ... | Bear clearly superior on documented conduct |"
   - Problem: The 1-5 scale has no stated direction. In fact 5 means the bear case wins, but a credit committee reader would naturally take 5 on "Sponsor / governance alignment" as strong alignment, which inverts the finding. The numeric column also carries long "Not scored: [Insufficient Information] — ..." text.
   - Fix: State the scale in the header (e.g. "1 = bull clearly stronger … 5 = bear clearly stronger") and use a short "n/s" mark in the score column, with the reason given in the assessment cell.
3. **High · narrative** (Auditor, New reader)
   - Where: line 153: "| Market data, ratings, mandate, holdings | Missing | RV and portfolio dimensions unscored | context |"; line 161: "Financial data foundation (CP-1); calculation X01"
   - Problem: Several Source cells read "context", which is not a source, or "calculation X01"–"X05", internal IDs the reader cannot resolve without another page. On screen, other cells repeat the source name ("Financial data foundation (Financial foundation)"). The Source column therefore fails its purpose of letting a reader trace the figure.
   - Fix: Name a real source or write "Not supplied in this run", and label calculations by what they compute (e.g. "Calculation: pro forma liquidity ÷ obligations").
4. **High · visual** (Auditor, New reader)
   - Where: Screenshot CP-6_s-143.png, 'On this page' sidebar (displayed ~x95-250, y1150-1490): "Analytical appendix — complete canonical registers", "a method step Bear cross-examination", "a method step Chair scoring", "a method step Gaps ledger" (twice)
   - Problem: The navigation shows "canonical", a banned pipeline word, plus a machine substitution ("a method step") in place of the T6A/T6E codes. As a result, two different entries both read "a method step Gaps ledger", and a reader cannot tell them apart.
   - Fix: Give the headings reader titles (e.g. "Appendix: supporting tables", "Bear cross-examination", "Debate gaps", "Allocation gaps") with no code or placeholder prefix.
5. **Medium · narrative** (Saboteur)
   - Where: line 162: "6.01x total, 5.55x pro forma net; payouts reset leverage | Strong"; line 193: "6.01x / 5.96x; 5.55x"; line 194: "Reported net leverage FY2023 / FY2024 | 4.84x / 4.51x"
   - Problem: The same page gives four leverage figures (6.01x, 5.96x, 5.55x, 4.51x) on different bases with no reconciliation. The reported figures (4.84x to 4.51x) show leverage falling, which contradicts "payouts reset leverage", so a reader can pick whichever number suits a view.
   - Fix: Add one reconciling line or note per figure stating which leverage basis drives the view and why the reported 4.51x differs from the house 5.55x–6.01x.
6. **Medium · narrative** (Saboteur)
   - Where: line 205: "Secured net incurrence at 5.00x against 4.72x gross secured today per filing summary; priming and uptier capacity unread"
   - Problem: The sentence compares a net test with a gross figure. The 4.72x is not in the figure register directly above it, so the reader cannot check it and may take the 0.28x gap as true headroom.
   - Fix: Compare like with like (secured net against the 5.00x net test), and add the figure, its basis and its source to the figure register.
7. **Medium · narrative** (New reader)
   - Where: line 209: "Bull defence: Claim 1 Partially Rebutted (...). Claim 2 Fully Rebutted for the period before FY2028 (...). Claim 3 Failed (...)"; line 152: "RV Unclear; no Preferred instrument; sizing Requires More Work"
   - Problem: It is unclear who rebutted whom: "Claim 2 Fully Rebutted" reads as the bull claim being refuted when it means the bear attack was rebutted. Undefined shorthand (RV, LME, LGD, FCF, "house-basis watch levels") and status labels in Title Case need another page to decode.
   - Fix: Phrase outcomes from the reader's side (e.g. "Bear attack on liquidity rebutted before FY2028") and spell out each abbreviation at first use.
8. **Low · visual** (Auditor)
   - Where: Screenshot CP-6_s-143.png, Figure register (displayed ~y1185-1985), Value column and Figure column
   - Problem: Ratios and percentages (52.56%, 3.60x, 3.82x, 31%, 2.27x, 20.73%) are set in bold monospace while USD amounts and compound values use regular sans, so similar values look different. A grey "Basis" chip is appended to every row label in all three tables and reads as part of the label ("Financial foundation Basis").
   - Fix: Use one numeric style for every value cell, and show the basis link as a separate, visually distinct control rather than trailing text.

### Events: Decision and watch

Kind: timeline · handoff lines 133-138 · verdict **BLOCK**

- Narrative: The section's only row is a set of 'Not supplied' placeholders that leaks pipeline wording ('lanes', 'fact pack'). It also calls watch triggers undated when it states their dates in the same cell, so the reader is left with no dated watch point behind a Watchlist decision.
- Visual: The module page shows a dense seven-column table of repeated 'Not supplied' text, and the timeline panel's Decision and watch row is empty ('Not established for this run') even though dated triggers (2025-07-11, 2027-09-30) are known.

1. **High · narrative** (Saboteur)
   - Where: Line 137, Credit relevance cell: "watch conditions (secured-funded payout, 2027 subordinated refinancing, securitization renewal by 2025-07-11, hedge end 2027-09-30) are undated triggers or events already recorded in other lanes"
   - Problem: The row calls these watch items undated, but two of them carry exact dates in the same cell, and the 2027 subordinated notes date (2027-11-15) appears in the pre-debate thesis map on the same page. The decision-and-watch log therefore has no dated entries, so a committee on Watchlist sees no point at which to revisit.
   - Fix: List the dated watch conditions (2025-07-11 securitization renewal, 2027-09-30 hedge end, 2027-11-15 subordinated maturity) as event rows with their source, and keep 'Not supplied' only for the committee review date.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 137, Event cell: "Not supplied: dated issuer events are owned by the source readiness, fact pack, macro and relative-value lanes"
   - Problem: Pipeline vocabulary ('owned by', 'lanes', 'fact pack', 'source readiness') appears in reader-facing text and breaks the house rule. A portfolio manager cannot tell what a 'lane' is or where to find those events.
   - Fix: Use reader language, for example 'Issuer events are shown in the Timeline page', or drop the clause.
3. **High · visual** (Saboteur, Auditor)
   - Where: Timeline panel, CP-6_timeline.png, crop y≈200-330 (tmp/CP-6-151-a.png): row 'Decision and watch — Not established for this run / no committee decision or assigned review date is stated in any supplied source'
   - Problem: The timeline draws no point for this module, even though known dated watch triggers (2025-07-11, 2027-09-30) exist. A reader scanning the timeline concludes there is nothing to watch on the calendar.
   - Fix: Plot the dated watch triggers on the Decision and watch row, with an empty-state note only for the missing committee review date.
4. **Medium · narrative** (Saboteur)
   - Where: Line 137, Event date cell: "Not supplied: no committee decision or assigned review date is stated in any supplied source"
   - Problem: The module's own decision is Watchlist (line 114/124), yet the section gives no review date and no trigger that would end the watch. The committee gets a posture with no time bound.
   - Fix: State the review trigger the module already names (for example sight of the credit agreement's restricted-payment capacity, or market levels) as the undated watch event, so the watch has a defined exit.
5. **Medium · visual** (New reader)
   - Where: Events: Decision and watch table, CP-6_s-133.png, region x≈300-1160, y≈215-365 (display coordinates)
   - Problem: The table has seven columns with one row, and every cell repeats a variant of 'Not supplied: no dated decision event'. The result is a dense grey block that carries one fact, and it takes the reader longer to read than the timeline panel's one-line empty state.
   - Fix: Show a single-line empty state, or render only the dated watch rows, instead of a full table of repeated 'Not supplied' cells.
6. **Low · visual** (Auditor)
   - Where: Events table, CP-6_s-133.png, Event date cell 'supplied source Basis' (display y≈330) and Source column 'Not supplied: no dated decision event'
   - Problem: A 'Basis' chip is attached to a cell that asserts absence, and the Source column holds a placeholder sentence rather than a source. This dilutes the convention that Source columns cite evidence.
   - Fix: Leave the Source column as an em dash or 'none' and drop the Basis chip from empty-state rows.
7. **Low · visual** (Auditor)
   - Where: Timeline panel header 'Dated events by module', CP-6_timeline.png crop tmp/CP-6-151-a.png; section heading 'Events: Decision and watch' (line 133)
   - Problem: 'by module' is pipeline wording on screen. The 'Events:' prefix reads as a data-table label, in the same style as the adjacent 'Chart data: portfolio limits', rather than as a reader heading.
   - Fix: Use reader headings such as 'Dated events by topic' and 'Decision and watch dates'.

### Calculations

Kind: prose/table · handoff lines 310-326 · verdict **BLOCK**

- Narrative: The section has no bottom line. It opens and closes with pipeline wording, leaks register codes, and gives an undefined confidence score. I re-checked all eight results and the arithmetic is correct.
- Visual: The table sits cleanly within the page grid and is legible at 1440 px, but over-precise results wrap the Result column and two cells are styled as code. There is no chart in this section; the neighbouring "a method step Gaps ledger" heading is outside this unit.

1. **High · narrative** (Auditor, New reader)
   - Where: L312 "All new arithmetic used the calculate tool. Inputs are USD millions or fractions taken from the supplied handoffs"; L325 "Helper scripts named by the method were not run in this transport; their checks and arithmetic are recorded above and in the appendix note."
   - Problem: The reader sees pipeline language: "calculate tool", "handoffs", "helper scripts named by the method", "transport" and "appendix note". This breaks the house rule on reader language. Neither sentence tells a committee member anything about TDG.
   - Fix: Replace both sentences with one sentence of judgement on what the arithmetic shows, for example near-term maturity cover, and state the basis (FY2024 annual filing, USD m) in a Basis line.
2. **High · narrative** (Auditor, New reader)
   - Where: L316-319 "(schedule at 2024-09-30; Financial data foundation (CP-1))", "(pro forma 2024-10-18; CP-1 C28)", "(CP-3 R18, R19)"; rendered as "Financial data foundation (Financial foundation))" and "Financial foundation C28", "Security selection R18, R19"
   - Problem: Internal register row codes (C28, R18, R19) reach the reader. The module-name substitution also prints the source name twice, with doubled closing parentheses. Source references sit inside the Inputs cells instead of a Source column.
   - Fix: Add a Source column that names the document and period (for example "FY2024 10-K debt maturity schedule"), and take register codes and duplicated module labels out of the Inputs cell.
3. **High · narrative** (New reader, Saboteur)
   - Where: L321-323 "Confidence E: sum of lineage weights over ten claims | 3 × 1.0 + 4 × 0.9 + 2 × 0.4 + 1 × 0 | 7.4, so E = 74"; "0.6E + 0.4C, C = 80"; "X07 × S, S = 0.7 ... 53.48 (score 53, Low)"
   - Problem: E, C and S, "lineage weights" and the 0–100 scale with a "Low" band are never defined. A committee member cannot tell what the score 53 measures, why S = 0.7, or whether "Low" means low confidence or low risk. That ambiguity could swing the decision.
   - Fix: Name each component in plain words (evidence strength, coverage, source restriction), give the scale and band cut-offs, and say in one line what "53, Low" means for the decision.
4. **Medium · narrative** (Saboteur)
   - Where: L319 "Current yield 4.625% 2029 subordinated notes − current yield 2033 secured notes | 0.0478448276 − 0.0591715976 ... -0.0113267700 (-1.13 pp) | fraction"
   - Problem: The table shows a negative subordinated-minus-secured spread and gives no caveat. Current yield (coupon over price) ignores maturity and call features, so a reader may conclude that subordination is mispriced. The Unit column says "fraction", but the Result column shows percentage points.
   - Fix: Label the metric as current yield rather than yield-to-worst, give the bond prices and their date, state the result in percentage points with a matching unit, and add one clause on why the spread should not be read as a relative-value signal.
5. **Medium · narrative** (Auditor)
   - Where: L318 "FY2028 maturities / pro forma liquidity | 6,637 / 2,919"; L320 "Pro forma liquidity − X01 | 2,919 − 764"; L321-323
   - Problem: The column header promises "Inputs (period, origin)", but X03, X05, X06, X07 and X08 give neither a period nor a source. X03 does not say which date the FY2028 maturity figure is taken from.
   - Fix: Give every row its period and origin, or a Source column entry, especially the FY2028 maturity schedule date.
6. **Medium · visual** (New reader, Saboteur)
   - Where: Calculations table, Result column; scratchpad/tmp/CP-6-154-a.png rows X02, X03, X04
   - Problem: Ten-decimal results such as "3.8206806283 (3.82x)" and "-0.0113267700 (-1.13 pp)" show false precision and push the readable figure onto a second line. The narrow Result column then wraps most rows.
   - Fix: Show only the rounded figure (3.82x, -1.13 pp, USD 2,155m), keep the full precision in the calculation JSON, and widen the Result column.
7. **Low · visual** (Auditor)
   - Where: Calculations table rows X07 Result "76.4" and X08 Inputs "0.7"; scratchpad/tmp/CP-6-154-a.png
   - Problem: Two cells render in bold monospace, apparently from code-span markup, while every other number is in the body font. This draws the eye to the wrong values, and "C28" also renders in a different typeface.
   - Fix: Remove the code formatting so all table figures share one numeric style.
8. **Low · visual** (New reader)
   - Where: Calculations table, ID column "X01"-"X08" and Formula cells "Pro forma liquidity / X01", "X07 × S"
   - Problem: The formulas refer to internal IDs, so the reader has to trace back through rows to learn that X01 is near-term maturities of USD 764 million. The ID column takes width but adds no meaning for the reader.
   - Fix: Write the formulas in words (for example "Pro forma liquidity / FY2025–27 maturities and securitisation") and narrow or drop the ID column.

### Front matter + Request + Next module

Kind: run plumbing · handoff lines 1-15, 16-19, 339-342 · verdict **CONCERNS**

- Narrative: This section is run plumbing, not credit narrative. Every part of it leaks pipeline wording onto the reader page: raw YAML keys, a filename containing the module code, an incoherent 'Committee decision ... absorbed Committee decision' sentence, and a 'DO NOT RUN' note that contradicts the Changes module shown in the nav.
- Visual: The section has no chart, map or timeline. Its layout is an unformatted metadata paragraph and a plain process paragraph. The front matter wall of text buries the status values a committee reader needs.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: Front matter, handoff lines 1-14 ("filename: tdg_CP-6_20240930.md qa_status: Restricted confidence_score: 53 ... limitation_flags: [SOURCE_LIMITED_NOT_COMMITTEE_READY]"), rendered under 'Front matter' in CP-6_s-1.png, y about 228-318 at full size
   - Problem: The YAML metadata reaches the reader verbatim: snake_case field names, a filename that shows the module code 'CP-6' on screen, and an all-caps flag code. All of these break the house rule against module codes and pipeline vocabulary on screen.
   - Fix: Hide the front matter, or show only reader-labelled values (for example 'Confidence: 53, Low; Committee status: Restricted') with no filename, field keys or flag codes.
2. **High · narrative** (Auditor + New reader (promoted))
   - Where: Line 18: "CP-6 investment-committee debate and challenge, with the absorbed CP-6A portfolio debate ... adversarial challenge of the supplied upstream handoffs"; on screen it reads "Committee decision investment-committee debate ... with the absorbed Committee decision portfolio debate"
   - Problem: Both codes were swapped for the same display name, so the sentence on screen repeats itself and makes no sense. 'absorbed', 'upstream handoffs' and 'Pathway: credit_snapshot' are pipeline language a portfolio manager cannot parse.
   - Fix: Write the request as one plain sentence about the question the committee answers (the action bias and portfolio posture for TDG at 30 September 2024, with no new evidence and no position size), with no module names, 'handoffs' or snake_case pathway.
3. **High · narrative** (Saboteur + Auditor (promoted))
   - Where: Line 341: "CP-8 is the next selected module but should stay conditional: source readiness recorded DO NOT RUN until a prior deliverable is supplied"; on screen "Changes since the last run is the next selected module..." (CP-6_s-339.png, y about 2270-2330 at full size)
   - Problem: The page says the Changes comparison should not run. Yet CP-8 did run in this run (requests/CP-8 exists), and the left nav shows 'Changes since the last run'. The reader is told the comparison is invalid while it is shown to them. The text is also scheduling language ('selected module', 'rerun', all-caps DO NOT RUN), not credit content.
   - Fix: Remove run-scheduling text from the reader page, or replace it with one reader sentence on what extra evidence (executed debt documents, yield-to-worst, ratings, mandate) would update this view, in line with what actually ran.
4. **Medium · visual** (New reader + Saboteur (promoted))
   - Where: 'Front matter' block, CP-6_s-1.png, y about 228-318 at full size
   - Problem: Fourteen key:value pairs run together as one three-line wall of text with no separators. The most decision-relevant values (Watchlist, confidence 53 Low, Restricted, Requires More Work) are buried and unstyled, mid-page after Timeline.
   - Fix: Show these status values as labelled chips or a short two-column key-value table near the bottom line, or not at all.
5. **Low · visual** (Auditor)
   - Where: 'Next module' paragraph, CP-6_s-339.png, y about 2270-2330 at full size
   - Problem: The section ends the module page with a bare process note in body type, so the page's last line is plumbing rather than the credit view.
   - Fix: End the module on Gaps or Limitations and drop the Next module heading from the reader view.

### Sources

Kind: prose/table · handoff lines 20-40 · verdict **CONCERNS**

- Narrative: The narrative is mostly provenance. Its main fault is line 39: after module codes are swapped for names it says Downside and Business & governance were unavailable, which contradicts the table above it, and it uses the pipeline words "handoff" and "upstream modules".
- Visual: This section has no charts. It is two bordered tables in which hash columns take most of the width, the source names are a raw filename and "context" with a stray Basis chip, and the section sits in the middle of the page ahead of the Decision rather than at the end.

1. **High · narrative** (Saboteur, New reader)
   - Where: Handoff line 39: "Modules the method names but that are not in this run (CP-1B, CP-1C, CP-2B, CP-2C, CP-2D, CP-3A, CP-3B, CP-3C, CP-4A as separate handoffs) are unavailable; the CP-3A and CP-3B phases are read as absorbed". Rendered in shot CP-6_s-20.png (crop tmp/CP-6-141-a.png, y~690-785) as "(Earnings changes, Peer benchmark, Downside, Business & governance, Liquidity, Security selection, Security selection, Refinancing & LME, Covenant capacity ...)" and "the Security selection and Security selection phases"
   - Problem: When the page swaps module codes for display names, the list of modules "not in this run" includes Downside and Business & governance. The supplied-input table directly above lists both as present, and Security selection appears twice. The reader is told that downside and governance evidence both was and was not used, and the absorbed-phase sentence ends up saying nothing.
   - Fix: Give each missing module its own distinct, correct name (for example the liquidity bridge or the governance overlay) so that no name in the missing list matches a supplied module, and name the two absorbed relative-value phases differently.
2. **High · visual** (Auditor, New reader)
   - Where: Sources tables, shot CP-6_s-20.png, crop tmp/CP-6-141-a.png: column header "Supplied handoff" and cell "relied on only through the page-cited figures in the supplied handoffs" (line 24); "handoffs are cited by upstream modules" (line 39)
   - Problem: "Handoff" and "upstream modules" are pipeline words the house standard keeps off the reader's screen. Here they appear as a table header and in two passages.
   - Fix: Use reader language, such as "Earlier analysis relied on" with plain section names, and do not mention the pipeline's transport.
3. **Medium · narrative** (New reader)
   - Where: Line 24: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"; line 25: "portfolio workbook false; legal documents flagged executed but none attached"
   - Problem: The reader is shown a raw ingestion filename and a settings flag ("portfolio workbook false") instead of a plain description of the source, such as "TransDigm FY2024 Form 10-K (filed November 2024)".
   - Fix: Name the source as a document a reader would recognise, with its form, period and filer, and describe missing inputs in words rather than as flag values.
4. **Medium · visual** (New reader, Auditor)
   - Where: Both Sources tables, sha256 column (lines 22-37); crop tmp/CP-6-141-a.png, central column ~40% of the table width
   - Problem: Sixty-four-character hashes take up the widest column in both tables. They mean nothing to a portfolio manager, and they squeeze the filing filename into four wrapped lines.
   - Fix: Move the hashes to the Evidence page or into a collapsed provenance detail, and keep a human-readable source name and its use on the Modules page.
5. **Medium · visual** (Auditor, Saboteur)
   - Where: Sources table row "context | f7b95e1f... | Read directly (page 1): quotes, ratings, peers..." (line 25); rendered as "context Basis" in crop tmp/CP-6-141-a.png y~195
   - Problem: The internal input name "context" is shown as the source, and a stray "Basis" chip sits next to it inside a Sources table cell. Neither is reader language, and the chip has nothing to link to here.
   - Fix: Label the row as "Run settings (no market, rating or mandate data supplied)" and do not render Basis chips inside the Sources tables.
6. **Low · visual** (New reader)
   - Where: Supplied-input table, columns "Supplied handoff" and "Module" (lines 27-37), e.g. "Source readiness | Source readiness", "Downside pathway | Downside"
   - Problem: The first two columns repeat almost the same name on every row, so two of the table's three columns carry one piece of information.
   - Fix: Merge them into one name column, and use the space for what each input contributed to the decision.
7. **Low · visual** (Auditor)
   - Where: Page order in shot CP-6_s-20.png: "Sources" heading (y~198) sits above "Decision", "Debate record", "Portfolio debate"; the on-page TOC lists Request, Sources, Decision ...
   - Problem: Sources is rendered in the middle of the page, ahead of the Decision and debate passages, rather than closing the module. The reader meets provenance tables before the decision they support.
   - Fix: Render Sources after the module's narrative sections, as the house reading order does.

### Debate record

Kind: prose/table · handoff lines 100-116 · verdict **BLOCK**

- Narrative: The debate content is substantive, but the section opens with pipeline readiness wording rather than the verdict, leaves key multiples without a period or case, and puts the core argument in one oversized paragraph.
- Visual: This section has no chart. As laid out on the page, it is five dense full-width paragraphs, and three of them lack the Basis chip the handoff provides. Spacing and headings are otherwise clean.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 102: "The source gate returns Ready with Limitations. ... the legal handoff is present but reports Blocked; market data, mandate data, ratings, the liquidity bridge ... are absent."
   - Problem: The section opens with pipeline vocabulary ("source gate", "handoff", status codes "Ready with Limitations", "Blocked") that the house standard bans from reader text. It also leads with an input-readiness inventory, not the debate's verdict, so the judgement is not first.
   - Fix: Open with the debate verdict in reader language (for example, that the bull wins near-term liquidity, the bear wins policy and legal control, and price is untested), then state the missing evidence as plain limits without pipeline terms.
2. **High · visual** (Auditor, Saboteur)
   - Where: Screenshot CP-6_s-100.png, crop (340,220)-(1400,660): paragraphs "The central controversy...", "The bull's three claims..." and "In defence, the bull..." carry no Basis chip, although handoff lines 106, 109 and 112 each have a Basis line
   - Problem: Three of the five paragraphs are shown without their Basis, so the reader cannot trace 52.56%, 3.60x, 8.71x, 7.25x/5.00x or 3.82x to a source. This breaks the rule that each paragraph's Basis line carries its references.
   - Fix: Render a Basis chip at the end of every paragraph that has a Basis line in the handoff, as the first and last paragraphs already do.
3. **Medium · narrative** (Saboteur)
   - Where: Line 105: "an EBITDA As Defined margin of 52.56% and cover of 3.60x"; line 108: "to leverage of 8.71x"; line 111: "pro forma liquidity 3.82x obligations"
   - Problem: The figures have no period or full basis on first use. "cover" does not say cash interest cover for FY2024, 8.71x is the severe-case total leverage but reads like an actual figure, and 3.82x does not say which obligations, or over what horizon. A committee member could take the stress leverage as reported leverage.
   - Fix: Name each metric, its period and its case on first use (for example, "FY2024 cash interest cover of 3.60x", "severe-case total leverage of 8.71x", "obligations due before FY2028").
4. **Medium · narrative** (New reader)
   - Where: Line 108: "The bull's three claims are that cash conversion is durable ... The bear's legal-control attack finds only a springing revolver test, incurrence levels of 7.25x net and 5.00x secured net, and collateral..." (about 170 words)
   - Problem: One paragraph packs three claims, three counter-attacks, a five-link stress chain and a legal-control attack. It becomes a wall of text that hides which side wins each point.
   - Fix: Split it into short claim-and-rebuttal pairs (or a three-row claim, attack and outcome table), so each outcome is readable at a glance.
5. **Medium · narrative** (New reader)
   - Where: Line 102: "Each absence is carried as a limit on the Chair's claims"; line 108: "The bull's three claims"; line 114: "payout of the October size"
   - Problem: The section relies on internal personas ("Chair", "bull", "bear") and an unquantified referent ("the October size"), so a reader new to the pipeline has to look elsewhere to understand who argues what and how large the payout was.
   - Fix: Introduce the debate framing once in plain words, and give the October payout as an amount with its date and currency.
6. **Low · narrative** (Saboteur)
   - Where: Line 114: "Resolved favourably ... the bias moves to Starter Position in the secured layer; resolved adversely ... the subordinated notes move to Avoid and the secured layer stays at Watchlist."
   - Problem: This what-would-change-the-view passage is useful, but it sits last in a record that opens with input status. The decision trigger is buried below three paragraphs of argument.
   - Fix: Move the single greatest uncertainty and its two outcomes up, directly after the verdict sentence.
7. **Low · visual** (Auditor)
   - Where: Screenshot CP-6_s-100.png, crop (340,220)-(1400,660): inline figures 52.56%, 3.60x, 8.71x, 7.25x, 5.00x, 3.82x
   - Problem: The figures are set mid-sentence in a monospace face with a dotted underline, which breaks the reading rhythm of the prose and suggests a link or tooltip without saying what it holds.
   - Fix: Use the body typeface for inline figures (tabular numerals if needed) and keep a figure-trace affordance only where it opens something the reader can use.

### Analytical appendix — complete canonical registers (part 2 of 2: from 'T6A.7 Debate resolution matrix')

Kind: register appendix · handoff lines 227-309 · verdict **BLOCK**

- Narrative: Lines 227-309 are dense register tables. Pipeline vocabulary (portfolio_workbook, rerun module, priority item 12) and undefined debate labels (CIO, RV, Bull/Bear Sustained) leak through, and a sign-ambiguous yield gap risks inverting the junior-compensation point.
- Visual: There is no chart in this section. The rendered tables have broken \"a method step\" headings and duplicate nav entries, and the Source text overflows the card in the seven-column compliance table. The screenshot covers only down to the end of the Compliance cross-examination table, so CIO scoring, Allocation matrix, Exact constraint and the second Gaps ledger were judged from the handoff only.

1. **High · narrative** (Auditor, New reader)
   - Where: line 294: "portfolio_workbook false; quotes, ratings and peers blank"; line 293: "Data quality (priority item 12)"; line 242: "Attach documents; rerun legal module"; line 247: "Run refinancing and LME module"
   - Problem: Raw configuration fields, an internal priority-list number and module/rerun instructions reach the reader. The house rule says pipeline vocabulary is not reader language.
   - Fix: Describe each gap in reader terms, e.g. "no portfolio mandate or holdings supplied" and "obtain executed credit agreement and indentures", with no field names or module reruns.
2. **High · visual** (Auditor, New reader)
   - Where: Headings at lines 227, 238, 252, 264, 280, 299 ("#### T6A.7 Debate resolution matrix") render as "a method step Debate resolution matrix", "a method step Gaps ledger" etc.; CP-6_s-227.png y≈195, 678, 1276 and in the On this page nav
   - Problem: The register code is not dropped as views.js:50 intends; it is replaced, so every table heading and nav entry starts with the meaningless phrase "a method step", and two entries both read "a method step Gaps ledger".
   - Fix: Drop a register code that comes before its own title, so the heading reads "Debate resolution matrix", and tell the two gaps ledgers apart (credit debate and allocation).
3. **Medium · narrative** (Saboteur)
   - Where: line 257: "Junior running yield -1.13 pp below senior" (also line 222)
   - Problem: A negative number followed by "below" is a double negative, so it reads as if the junior yield were 1.13 pp above senior. That flips the compensation argument the row is making.
   - Fix: State the sign once, e.g. "junior running yield 1.13 pp below senior (coupon over price)".
4. **Medium · narrative** (New reader)
   - Where: line 264 "T6E.6 CIO scoring"; line 254 "RV Bullet Attacked"; line 231 "Bull Sustained"; line 243 "no Starter Position"; line 262 "RV defence: Bullet 1 Insufficient Information; Bullet 2 Partially Rebutted"
   - Problem: The tables use undefined debate-process labels (CIO, RV, Bull/Bear Sustained, Starter Position, Partially Rebutted) as outcomes. A committee member who has not seen the debate format cannot tell what each verdict means for the credit.
   - Fix: Spell out abbreviations and replace process verdicts with plain judgements (e.g. "bear case holds: repeat debt-funded payouts are likely").
5. **Medium · visual** (Auditor)
   - Where: Compliance cross-examination table, Source column, Bullet 2 row; crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-6-153-a.png (orig x 1000-1440, y 1540-2080)
   - Problem: The seven-column table makes the Source column so narrow that "calculation" runs past the table's right border, and the cells wrap to one or two words per line (Bullet 1 runs 11 lines).
   - Fix: Give the Source column a minimum width, or move sources into each row's Basis fold, so nothing overflows the card.
6. **Low · narrative** (Saboteur)
   - Where: line 260: "Compliance attack summary: the officer cannot evidence any breach because no mandate data exist, so the attack succeeds only as a data-quality and legal-recovery challenge"
   - Problem: The judgement comes after three wide tables, below the place the reader needs it. It also says the attack "succeeds" and in the same sentence that it proves nothing binding, which hedges the conclusion.
   - Fix: Open the subsection with a one-line bottom line, e.g. "No portfolio limit can be tested; the real objections are junior-note recovery and missing market data".
7. **Low · visual** (Auditor)
   - Where: Source cells, e.g. "Financial data foundation (Financial foundation); calculation X02" and "context", CP-6_s-227.png y≈258-620 and 889-939
   - Problem: The renamed module labels repeat themselves in parentheses. "context" and "calculation X02" are internal identifiers, not sources a reader can look up.
   - Fix: Name each source once, in reader terms (e.g. "FY2024 annual report, via financial foundation", "run settings: no mandate supplied").

### Gaps

Kind: prose/table · handoff lines 327-338 · verdict **BLOCK**

- Narrative: The Gaps table (handoff lines 327-338) is mostly pipeline housekeeping in internal vocabulary, with \"context\" as the source. The two gaps that change the decision (no executed debt documents capping the stance at Watchlist, and no mandate leaving posture undecided) are not ranked above tooling notes.
- Visual: The section has no chart, map or timeline. The table renders legibly at 1440 px, with four balanced columns, no clipping and adequate contrast. However, it sits directly under a near-duplicate gaps ledger, which clutters the page and the sidebar navigation, and its Source cells carry redundant parenthetical names.

1. **High · narrative** (Auditor, New reader)
   - Where: L334 "Deep-research and forward-model handoffs not supplied to this module | Their figures used only as restated in supplied handoffs | None for this run"; L335 "Liquidity bridge, refinancing/LME and valuation modules not in run | ... | Run when selected"; L337 "Helper scripts and schema references unavailable | Score and completeness checked by hand | Rerun when tooling available"; L331 "Attach and rerun legal module"
   - Problem: Three of the seven rows are about the pipeline, not the issuer. "Handoffs", "this module", "modules not in run", "helper scripts", "schema references", "rerun" and "Run when selected" are pipeline vocabulary the house standard bans from the reader's page. A committee member cannot tell what evidence is actually missing about TransDigm.
   - Fix: Say each gap as missing credit evidence (for example: no liquidity bridge, refinancing path or recovery valuation was prepared, so runway and recovery claims rest on the filing alone), and drop the tooling row or move it to an internal log.
2. **High · narrative** (Auditor, Saboteur)
   - Where: Source column, L332 "Obtain, labelled external | context", L333 "Supply constraints workbook | context", L335 "Run when selected | context", L337 "... | context"
   - Problem: Four of the seven Source cells say only "context". This is an internal placeholder, not a source the reader can identify or check, so the Source column does not do the job the house rule gives it.
   - Fix: Name the actual basis (for example, the run request: no mandate file, ratings or market quotes were supplied) or mark the cell as a stated absence rather than "context".
3. **Medium · narrative** (Saboteur, New reader)
   - Where: L331-L337 table order: "Executed debt documents absent ... bias capped at Watchlist" sits beside "Helper scripts and schema references unavailable" with no ranking
   - Problem: Nothing ranks the gaps or states which one changes the decision. The gap that caps the stance at Watchlist (no executed debt documents) and the missing mandate that leaves posture at "Requires More Work" carry the same weight as a tooling note, so the judgement is buried.
   - Fix: Open with one line saying which gaps would move the committee view, and order the rows by decision impact.
4. **Medium · narrative** (New reader)
   - Where: L336 "Evidence trace clearance Restricted | Committee use requires stated debt basis and Unclear RV | Carry restrictions"
   - Problem: The words "evidence trace clearance", "Restricted", "stated debt basis", "Unclear RV" and "Carry restrictions" are internal status labels and an undefined abbreviation. A reader without the pipeline cannot act on this row.
   - Fix: State in plain words what the committee may and may not rely on (for example, debt figures must be quoted with their measurement basis, and relative value is not established).
5. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-6_s-327.png: the 'a method step Gaps ledger' table (y≈610-950, displayed scale) immediately followed by 'Gaps' (y≈1465-1865); the sidebar lists 'a method step Gaps ledger' twice plus 'Gaps'
   - Problem: The same missing items (mandate, holdings, market levels, ratings, legal documents) appear in a second, differently worded gap table on the same screen. The duplicate has its own headings, and the 'a method step' label leaks method wording into the table title and the navigation. The reader cannot tell which list is authoritative.
   - Fix: Show one consolidated gaps table per module, with a reader-language heading and a single sidebar entry.
6. **Low · narrative** (Auditor)
   - Where: L331-L333 "absent [Insufficient Information]"
   - Problem: The bracketed tag "[Insufficient Information]" is a register label appended to the prose. It appears on only three rows, which suggests the other rows differ in some way when they do not.
   - Fix: Drop the bracketed tag, or make it a consistent status column applied to every row.
7. **Low · visual** (Auditor)
   - Where: CP-6-155-a.png crop, Source column: "Evidence trace validation (Evidence validation)" and "Legal and covenant interpretation (Legal & covenants)"
   - Problem: The renderer's display-name substitution appends a redundant parenthetical name to each module source. The cell wraps onto two lines and repeats itself.
   - Fix: Render a single reader-facing source name per cell.

### Bottom line

Kind: reader passage · handoff lines 43-50 · verdict **CONCERNS**

- Narrative: The call (Watchlist, judgement first) is right and the figures reconcile (4,216+132=4,348; 19,702/24,302=81.07%; 2,919/764=3.82x; 2,919-764=2,155). However, the bottom line is too long, leaves periods off its figures, leaves out the FY2028 refinancing wall, and speaks in debate-process vocabulary.
- Visual: The section has no chart: it is two paragraphs set entirely in bold headline type with no visible section label. The first paragraph's Basis chip does not render, and the nav beside it shows banned pipeline vocabulary.

1. **High · visual** (New reader, Saboteur)
   - Where: Bottom line block, shots2/CP-6_bottom-line.png crop y 230-1040 (tmp/CP-6-142-a.png); handoff lines 45 and 48, about 230 words
   - Problem: Both bottom-line paragraphs, about 230 words in all with an opening sentence of about 60 words, are set in large bold headline type and fill about 800 px. The reader gets a bold wall of text with no visual difference between the call (Watchlist) and the supporting figures, and the call is lost.
   - Fix: Show only the one-sentence call at headline size, set the rest in body type, and keep the bottom line short enough to read in one glance.
2. **Medium · narrative** (Saboteur)
   - Where: Line 45: "an EBITDA As Defined margin of 52.56%, cash interest cover of 3.60x and pro forma liquidity of USD 2,919 million that covers the USD 764 million due before FY2028 3.82x"
   - Problem: None of these figures gives its period or date: 52.56% and 3.60x are FY2024, and the liquidity is pro forma at the October 2024 dividend date (the module's own limitation at line 75). The trailing '3.82x' hangs without saying it is a liquidity-to-maturities ratio.
   - Fix: Tag each figure with its period or date and say plainly that liquidity covers maturities due before FY2028 3.82 times.
3. **Medium · narrative** (Saboteur)
   - Where: Line 45: "make near-term default remote ... The bear case wins on policy and recovery"
   - Problem: The bottom line never names the refinancing risk that the module's own key finding (line 55) calls the outcome of the bear case: severe-case leverage of 8.71x going into the USD 6,637 million FY2028 maturity cluster. A reader who stops at the headline sees 'default remote' with no time limit and no maturity wall.
   - Fix: Define 'near-term' as before FY2028 and name the FY2028 refinancing cluster in the bottom line as the risk that limits the call.
4. **Medium · narrative** (New reader, Auditor)
   - Where: Line 45/48: "the action bias that survives the challenge"; "The bull case wins on durability"; "the two dimensions that would justify committing capital, compensation and documented legal capacity, have no evidence in the pack"; "the portfolio debate ends at Requires More Work"
   - Problem: The passage speaks in the internal debate process ('survives the challenge', 'dimensions', 'the pack', 'portfolio debate', 'compensation' used as a scoring label) and leaves 'EBITDA As Defined' and 'springing revolver test' undefined. A credit committee member who has not seen the method cannot follow it.
   - Fix: State the conclusion in plain credit terms (for example, missing market yields and missing loan agreements) and gloss the issuer-defined EBITDA and the springing test in a few words.
5. **Medium · visual** (Auditor)
   - Where: Line 46 "Basis: Financial data foundation (CP-1); Business and transaction fact pack (CP-1A); Fundamental credit synthesis (CP-2); calculation X01; calculation X02"; rendered DOM section#bottom-line has 2 paragraphs but only 1 basis-link button
   - Problem: The first paragraph's Basis line is dropped on screen. Only the second paragraph ends with a 'Basis' chip, so the headline paragraph that carries the call and eight figures has no visible paragraph-level source link (its sources survive only on the individual figure buttons).
   - Fix: Show a Basis chip after every paragraph that has a Basis line, including the first paragraph of the headline block.
6. **Low · narrative** (Auditor)
   - Where: Line 48: "Yield-to-worst showing the junior class paid over secured paper, together with documents confirming bounded secured capacity, would move the bias to a Starter Position ... would move the subordinated notes to Avoid."
   - Problem: The bottom line already states the what-would-change-the-view triggers, which the 'Contrary evidence and what would change the view' section (line 68) then repeats. This blurs the house order and lengthens the headline.
   - Fix: Leave the triggers to the contrary-evidence section and keep the bottom line to the call and its decisive reasons.
7. **Low · visual** (New reader)
   - Where: shots2/CP-6_bottom-line.png crop y 220-1040: no visible 'Bottom line' heading (DOM h4 is class sr-only); left 'On this page' nav (crop b, y 0-660) lists 'a method step Bear cross-examination', 'complete canonical registers', 'Source gate register'
   - Problem: The section starts with no visible label, so the reader cannot tell this is the module's verdict. The section nav next to it shows pipeline vocabulary ('canonical', 'gate', 'a method step') that the house standard bans from the screen.
   - Fix: Give the headline block a visible 'Bottom line' label and replace the nav's method-step and register titles with reader-language headings.
8. **Low · visual** (Auditor)
   - Where: shots2/CP-6_bottom-line.png crop y 440-640: monospace dotted-underlined figures such as 'USD 2,919 million', 'USD 4,348 million' inside bold display text; right column x 1030-1420 empty
   - Problem: Monospace figure buttons set at headline size break the line rhythm and make long amounts very wide. About 400 px of empty right gutter forces the oversized text into a narrow, tall column.
   - Fix: Set figure links in the surrounding typeface at body size, or use the free width so the headline block is not a narrow tall column.

### Key findings

Kind: reader passage · handoff lines 51-65 · verdict **CONCERNS**

- Narrative: The findings are ordered judgement-first with bold leads and the arithmetic reconciles (2.31x, 2.27x, 2,155). They rely on debate and pipeline vocabulary, though, and leave leverage basis ambiguous on a page that tells the committee to use one basis.
- Visual: The section has no chart. As a bulleted list it reads cleanly, but it shows a lone stray \"Basis\" label, hides the sources of the other bullets, splits a minus sign from its value chip, and sits in a narrower column than the rest of the page.

1. **High · narrative** (Saboteur, Auditor)
   - Where: L63 "Leverage must be quoted on one basis (6.01x gross against 5.96x carrying)" vs L55 "total leverage reaches 8.71x" and L68 "Reported net leverage fell from 4.84x to 4.51x"
   - Problem: The section tells the committee to quote leverage on one basis but does not say which. The same page then gives 6.01x gross, 5.96x carrying, 8.71x "total" and 4.51x "reported net", so a reader cannot tell which figure the Watchlist call rests on.
   - Fix: Name the one leverage basis the committee should use. Label every leverage figure on the page with that basis, or flag it as a different basis with its period.
2. **Medium · narrative** (New reader, Auditor)
   - Where: L53 "The bull sustains the near-term default question."; L59 "The pack holds issuer fair-value prices only"; L61 "neither the trader's inclusion case nor the compliance officer's breach case"; L63 "the trace restrictions attached"
   - Problem: The bold lead sentences use internal debate and pipeline wording (bull/bear "sustains", "the pack", the trader and compliance-officer roles, "trace restrictions"). A PM who has not seen the debate cannot tell what was concluded about the credit.
   - Fix: Open each finding with a plain credit judgement, e.g. "Payment default before FY2028 is remote". Replace "pack", the role names and "trace" with reader language.
3. **Medium · visual** (Auditor, New reader)
   - Where: Screenshot CP-6_key-findings.png, Key findings bullets, about y 270-1080 (crop tmp/CP-6-143-a.png)
   - Problem: Only the fifth bullet shows a stray grey "Basis" label after "stated." The other five show no Basis at all. The reader gets one unexplained label and no visible source trail for the bullets that carry most of the numbers.
   - Fix: Render the Basis line the same way under every bullet: visible, or a consistent labelled toggle on all six.
4. **Medium · visual** (Saboteur)
   - Where: L57 "free cash flow after dividends paid was USD -158 million"; screenshot crop tmp/CP-6-143-a.png, bullet 3 line 3
   - Problem: The minus sign is drawn outside the figure chip ("USD -" in body text, "158 million" in the chip). The highlighted value reads as a positive USD 158 million, which is the key negative-cash-flow fact behind the bear case.
   - Fix: Put the sign inside the chip ("USD -158 million"), or write it as "a USD 158 million deficit".
5. **Low · narrative** (Saboteur)
   - Where: L59 "yield 4.78% on coupon over price against 5.92% on the 2033 secured notes, a running-yield shortfall of -1.13 pp"
   - Problem: The figures shown differ by 1.14 pp, not 1.13. "Shortfall of -1.13" is also a double negative that could be read as a pickup.
   - Fix: State "1.14 pp less running yield than the secured notes", consistent with the rounded figures shown, or show enough decimals to reconcile.
6. **Low · narrative** (New reader)
   - Where: L57 "The October payout was 2.31x FY2024 free cash flow of USD 1,880 million, free cash flow after dividends paid was USD -158 million, prepayment ranks last ... with non-guarantor subsidiaries producing 20.73% of sales ahead of both."
   - Problem: One 60-word sentence packs five separate facts (payout cover, cash flow after dividends, allocation order, subordination, structural subordination) into a single bullet. It is hard to take in at committee speed.
   - Fix: Split the bullet into two or three short sentences: payout funding, then the junior position in the structure.
7. **Low · visual** (Auditor)
   - Where: Screenshot CP-6_key-findings.png, text column x about 297-840 vs Timeline/Front matter/Sources full width to x about 1160
   - Problem: The findings run in a narrow column with about 320 px of empty space to the right. The blocks below on the same page span full width, so the layout looks inconsistent. Dotted-underlined monospace chips on every number add visual noise in dense bullets.
   - Fix: Use one content width for the whole module page and a lighter treatment for inline figures.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 66-70 · verdict **CONCERNS**

- Narrative: Judgement comes first, and the section opens on the strongest contrary case as the standard requires. But it uses a different leverage basis from the one the module itself mandates and gives an upgrade trigger that doesn't match the Bottom line. It is also one 200-word paragraph that buries the actionable triggers.
- Visual: This is a single prose block with no chart. The reading column is comfortable and the spacing is clean, but the Basis line is not visible on the page and thresholds are styled as register figures. (Crop saved at /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-6-144-a.png.) Not verified: whether the Basis opens on click (the inspector was not exercised), and whether 4.51x and 6.01x reconcile as net versus gross in the upstream handoffs (CP-1 was not read).

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 68: "Reported net leverage fell from 4.84x to 4.51x in FY2024" ... "if commercial aftermarket sales turned negative while leverage was still above 6x."
   - Problem: The module's own trace restriction (line 63: "Leverage must be quoted on one basis (6.01x gross against 5.96x carrying)") is broken here. The section quotes a third basis (reported net, 4.51x) and then sets a downgrade trigger at an unlabelled "6x". A committee member cannot tell whether TDG is already through that trigger (6.01x gross) or well below it (4.51x net).
   - Fix: Quote leverage on the one basis the committee is told to use, and state that basis and its current value next to the 6x trigger.
2. **Medium · narrative** (Saboteur)
   - Where: line 68: "That case wins if yield-to-worst on the secured notes and term-loan discount margins are at or above comparable single-B aerospace and leveraged-loan levels" vs line 48: "Yield-to-worst showing the junior class paid over secured paper ... would move the bias to a Starter Position"
   - Problem: Two different conditions are given for the same upgrade to a Starter Position in the secured layer: secured yields against peers here, and the junior-versus-secured spread in the Bottom line. The reader can't tell which test the committee should watch.
   - Fix: State one upgrade test (or say plainly that both must hold) and use the same wording in the Bottom line and in this section.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: line 68: "at or above comparable single-B aerospace and leveraged-loan levels"
   - Problem: The benchmark assumes a single-B rating category, but the module's own Sources row (line 25) says ratings and peers are blank in this run. The trigger therefore rests on a rating and peer set that the pack does not establish.
   - Fix: Name the benchmark as something still to be supplied (rating and peer set unknown), or drop the single-B label.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 68: one paragraph of about 200 words, from "The strongest case against Watchlist is..." to "...while leverage was still above 6x."
   - Problem: One wall of text does three separate jobs: the contrary case, the conditions that would move the view to a Starter Position, and the conditions that would move it to Avoid. The upgrade and downgrade triggers, which are what a committee acts on, are buried at the end of long sentences.
   - Fix: Keep the contrary case as a short paragraph and give the upgrade and downgrade triggers as two short lists the reader can scan.
5. **Low · narrative** (New reader)
   - Where: line 68: "waiting costs carry" ... "with the legal gap handled by the size rather than by waiting" ... "EBITDA As Defined falls 45.05%"
   - Problem: "Carry", "the legal gap" and the issuer-specific "EBITDA As Defined" are left undefined. The 45.05% breakeven gives no base year, and the term-loan repricings and the move in subordinated-note prices carry no figures.
   - Fix: Define the terms in plain words, give the base period for the 45.05% breakeven, and quantify or drop the repricing and price-move claims.
6. **Low · visual** (Auditor, New reader)
   - Where: Screenshot CP-6_contrary-evidence.png, region 330-1440 x 210-640 (crop CP-6-144-a.png): the paragraph ends at "above 6x." with no visible Basis line before Limitations
   - Problem: The handoff's Basis line (line 69: CP-1, CP-2A, CP-3, CP-2) does not appear on the page, and nothing visibly signals that the paragraph's sources can be opened. A reader cannot see what the contrary case rests on.
   - Fix: Show a small Basis line or a visible sources cue under the paragraph, as the house standard places references in the Basis line.
7. **Low · visual** (Auditor)
   - Where: Same crop: figure chips "4.84x", "4.51x", "45.05%", "6x" in monospace with dotted underline inside proportional body text
   - Problem: A threshold ("6x") gets the same register-figure styling as reported values, so it looks like a sourced data point. The switch to a monospace font mid-sentence also breaks the line rhythm.
   - Fix: Reserve figure-chip styling for register values, and render thresholds or trigger levels as plain text.

### Decision

Kind: prose/table · handoff lines 79-99 · verdict **CONCERNS**

- Narrative: The decision itself is clear and backed by evidence, but it sits after Limitations and Sources, opens with a roughly 90-word sentence under an internal label, and uses debate-procedure vocabulary (Chair, guardrail, figure register) that a committee reader cannot interpret.
- Visual: The driver table is readable and well spaced at 1440 px. However, its Source column shows garbled duplicate names and bare calculation IDs, Basis links duplicate the Source column, figure styling is inconsistent, and the opening paragraph's Basis link does not render.

1. **High · narrative** (Auditor, New reader)
   - Where: Page order in the 'On this page' rail of CP-6_s-79.png (left, y~1000-1040 at displayed scale): 'Limitations, Timeline, Front matter, Request, Sources, Decision, Debate record...'; handoff line 79 '### Decision' follows '### Limitations' (line 71)
   - Problem: The committee's actual decision (Watchlist) is placed after Limitations, Timeline, Front matter, Request and Sources, so the judgement comes after the reference material, and Sources is no longer the closing section. This breaks the house order (judgement first, sources last). A reader skimming the top of the page meets caveats before the decision.
   - Fix: Put the Decision (bias plus its driver table) next to the bottom line at the top of the module, and keep Sources as the final reader section.
2. **Medium · narrative** (New reader, Saboteur)
   - Where: line 81: "Final Action Bias: Watchlist. The decision is driven by documented free cash flow, cash interest cover of 3.60x and pro forma liquidity of USD 2,919 million against an owner policy that funded..."
   - Problem: The second sentence runs to about 90 words and packs five figures, two causal clauses and three implications into one chain, so the reader cannot separate why Watchlist from what it implies. 'Final Action Bias' is an internal label, not reader language.
   - Fix: Open with a plain judgement ('We place TDG on Watchlist'), then give the bull drivers, the bear drivers and the blocker each in its own short sentence.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 97: "the Chair applies the guardrail for sound credit with missing market data and unresolved legal leakage and does not move to Starter Position"; line 84: "values come from the figure register in the appendix"
   - Problem: 'the Chair', 'the guardrail', 'debate winner is Neither' and 'figure register' are the debate procedure's internal vocabulary. A committee member cannot tell what rule was applied, and the text sends them to an appendix to make sense of it.
   - Fix: State the rule in plain terms (no step up to a position while price and documentation are unevidenced) and drop the references to the procedure and the register.
4. **Medium · narrative** (Saboteur)
   - Where: line 89: "| Pro forma liquidity / obligations before FY2028 | 3.82x | Bull | Runway to FY2028 is covered | calculation X02 |"; line 94: "| Secured share of funded notes and term loans | 81.07% | Bear |"
   - Problem: Several drivers give no date or basis: the 'obligations' in 3.82x are not defined (which maturities, what period), and 81.07% has no as-of date (pre- or post-October issuance). Ratios like these can be read in either direction and are the figures that decide the bias.
   - Fix: Add the as-of date and the numerator/denominator definition to each driver label (for example 'Secured share of funded debt, pro forma Oct-2024').
5. **Medium · visual** (Auditor, Saboteur)
   - Where: Decision driver table, Source column, CP-6-146-a.png (crop 340,220-1440,940): 'Financial data foundation (Financial foundation)', 'Downside pathway (Downside)', 'calculation X02', 'calculation X03', 'calculation X04'
   - Problem: The Source cells show duplicated, garbled labels where module codes were swapped for names ('Downside pathway (Downside)'), alongside bare internal IDs ('calculation X02') that the reader cannot resolve. Each row also has a 'Basis' link next to the driver, which duplicates the Source column.
   - Fix: Show one clean, reader-named source per row (for example 'Calculation: liquidity vs obligations to FY2028') and keep either the Basis link or the Source column, not both.
6. **Medium · visual** (Auditor)
   - Where: CP-6_s-79.png, Decision first paragraph ending '...nor its ceiling can be tested.' (displayed y~225-305); handoff line 82 'Basis: Financial data foundation (CP-1); Business and transaction fact pack (CP-1A); ...'
   - Problem: The handoff gives the opening decision paragraph a Basis line, but no Basis link is drawn after it on screen, while the closing paragraph (line 97) shows one. The headline decision paragraph is the only prose in the section with no visible sourcing.
   - Fix: Render the Basis link for the opening Decision paragraph, as the page does for every other paragraph.
7. **Low · narrative** (Saboteur)
   - Where: line 90: "USD 526.39 million / 2.36x"; line 95: "Junior minus senior running yield | -1.13 pp | Bear (weakly)"
   - Problem: Cent-level precision on a stress-case cash flow overstates certainty. The negative junior pickup is labelled 'weakly' without saying why (running yield on price, not yield to worst), so a reader may over-read or dismiss it.
   - Fix: Round stress outputs to the nearest USD million and add a short qualifier to the yield row (for example 'coupon/price, not yield to worst').
8. **Low · visual** (Auditor)
   - Where: Decision driver table, Figure column, CP-6-146-a.png: '3.60x', '8.71x', '81.07%' in bold monospace chips vs 'USD 526.39 million / 2.36x' and '-1.13 pp' in plain text
   - Problem: Figure styling is inconsistent: the two composite or negative figures lose the chip treatment, so they look like a different kind of value and are easier to skip. The paired figure also wraps across two lines.
   - Fix: Style every figure cell the same way, and split the severe-case FCF and cover into separate rows.

### Portfolio debate

Kind: prose/table · handoff lines 117-121 · verdict **CONCERNS**

- Narrative: The judgement comes first, but the paragraph leaks pipeline and role-play language ("canonical set", "persona", "twelfth item in the priority order"), and its label, "Requires More Work", is not reconciled with the "Watchlist" in the next section.
- Visual: The section has no chart, map or timeline. It is a single readable prose block with a Basis link and no clipping or overlap, but the verdict has no visual emphasis.

1. **High · narrative** (Auditor, New reader)
   - Where: L119: "Requires More Work maps to Requires More Work in the canonical set." (also visible on screen, CP-6_s-117.png, Portfolio debate paragraph, line 3)
   - Problem: This is pipeline vocabulary ("canonical set") shown to the reader, which breaks the house rule. The sentence also says nothing: it maps the label onto itself.
   - Fix: Delete the sentence. The posture label in the first sentence is enough.
2. **Medium · narrative** (New reader, Auditor)
   - Where: L119: "Neither persona wins: the trader's pitch rests on issuer fair values and coupon-over-price yields, and the compliance attack rests on credit risks"
   - Problem: "Persona", "the trader" and "the compliance officer" are internal debate roles that the reader was never introduced to. A committee member cannot tell whose views these are or why they matter.
   - Fix: Describe the two arguments by what they say, for example "the case for buying" and "the case against on mandate grounds", and leave out the role-play framing.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: L119: "The exact portfolio constraint is data quality, the twelfth item in the priority order, because no higher-priority limit can be evidenced."
   - Problem: The passage cites a "priority order" and its "twelfth item" from a method list the reader cannot see. That makes the binding constraint sound like a ranked finding, when it only means the data is missing.
   - Fix: State it plainly: the binding constraint is missing mandate, holdings, rating and market data. Name the inputs that would allow a sizing decision.
4. **Medium · narrative** (Saboteur)
   - Where: L119: "Final Sizing Posture: Requires More Work." vs L124: "The committee should press three questions before accepting Watchlist."
   - Problem: Two adjacent sections give different headline labels, "Requires More Work" and "Watchlist", with nothing explaining that one is a sizing posture and the other a credit decision. A reader may think the module contradicts itself, or not know which one is the recommendation.
   - Fix: Add a short clause that ties sizing (Requires More Work) to the overall decision (Watchlist), so the reader sees both are consistent.
5. **Low · narrative** (Auditor)
   - Where: L120: "Basis: context; Relative value and security selection (CP-3)"
   - Problem: "context" is not a source the reader can identify. It is an internal label for run settings or the absence of inputs.
   - Fix: Name the actual basis, for example "Run settings: no portfolio workbook supplied".
6. **Low · visual** (New reader, Auditor)
   - Where: CP-6_s-117.png, Portfolio debate block (approx. y 230-350 in the 1440 px original)
   - Problem: The verdict "Final Sizing Posture: Requires More Work" sits inline in a seven-line block with the same weight as the rest of the text. The judgement is not visually set apart from the reasoning, so a skimming reader can miss it.
   - Fix: Show the posture as a lead sentence or chip, styled like the decision labels elsewhere on the page, with the reasoning in a short paragraph below it.

### Chart data: portfolio limits

Kind: chart · handoff lines 127-132 · verdict **CONCERNS**

- Narrative: The section is a one-row data table in which every substantive value is "Not supplied". It states no bottom line, and its only explanatory cell leaks pipeline wording (`portfolio_workbook as false`, "the module", "the page"), which breaks the reader-language rule.
- Visual: No portfolio-limits chart is drawn: the charts-route screenshot shows the module page with no such chart. What renders is a clean but mostly empty six-column table under a "Chart data" heading, with a wrapped, orphaned Basis chip and wasted row height.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 131: "The run settings record portfolio_workbook as false and no NAV denominator is available; the module states no limit, and the page shows portfolio limits as not established for this run"
   - Problem: The reader sees pipeline wording on screen: a raw config field name (`portfolio_workbook as false`), "run settings", "the module" and "the page". This breaks the house rule against pipeline vocabulary, and a portfolio manager cannot read `portfolio_workbook as false`.
   - Fix: State it in reader terms, e.g. that no mandate, holdings or portfolio size was provided, so no portfolio limit or NAV share can be measured.
2. **Medium · narrative** (Saboteur)
   - Where: Line 131: Reporting unit cell "% of NAV" beside "no NAV denominator is available"
   - Problem: The table states a definite reporting unit (% of NAV) for limits and exposures that do not exist, and in the same row it says NAV is unavailable. A skimming reader may take this to mean a NAV-based limit framework was applied.
   - Fix: Mark the unit as not established, or drop it, when neither the limit nor the denominator was supplied.
3. **Medium · narrative** (New reader, Auditor)
   - Where: Line 131: four cells starting "Not supplied: no mandate...", "Not supplied: no holdings...", "Not supplied: no proposal evaluated; posture is Requires More Work", "Not supplied: no limit stated..."
   - Problem: The section has no bottom line. A wide, six-column table carries one empty row, so the reader must parse four "Not supplied" cells to learn one fact. That fact (no sizing or limit conclusion is possible) is already stated under Portfolio debate. "Requires More Work" also appears inside a data cell, which mixes the posture judgement into an exposure column.
   - Fix: Lead with one judgement sentence (portfolio limits not established; no sizing conclusion possible) and drop the empty row, or reduce it to one gap line.
4. **Medium · visual** (Auditor, Saboteur)
   - Where: Heading "Chart data: portfolio limits" (line 127); CP-6_s-127.png top, crop CP-6-150-a.png; CP-6_charts.png shows the module page with no portfolio-limits chart
   - Problem: "Chart data" is a pipeline label. It promises a chart, but there is none: the reader gets a one-row table where every value is "Not supplied". The label refers to a visual that does not exist.
   - Fix: Use a reader heading such as "Portfolio limits", and say in one line that no chart is drawn because no limit or exposure was supplied.
5. **Low · narrative** (Auditor)
   - Where: Line 129 header: "| Limit | Current exposure | Proposed exposure | Limit value | Reporting unit | Basis and limitation |"
   - Problem: The table has no Source column, so its source reference (the run settings) sits inside the prose of the Basis and limitation cell, contrary to the house placement rule for tables.
   - Fix: Add a Source column naming the input checked, and keep the Basis and limitation cell for the limitation only.
6. **Low · visual** (New reader)
   - Where: CP-6_s-127.png, Limit cell (crop CP-6-150-a.png, left column): "Basis" chip wrapped onto its own line under "workbook attached"
   - Problem: The narrow first column wraps the cell to five lines, and the Basis chip drops beneath the text where it looks orphaned. Most of the row height is empty space next to short cells.
   - Fix: Widen the first column or shorten the gap text so the cell and its chip sit on one or two lines.

### Limitations

Kind: reader passage · handoff lines 71-78 · verdict **CONCERNS**

- Narrative: Lines 71-78 place limitations correctly, after Contrary evidence and before the Decision, with no source references in the sentences, but they are written in debate-internal vocabulary (Chair, bear, scored dimensions) and their two-way caveats are not tied back to how firm the Watchlist call remains.
- Visual: The section is a plain five-bullet list with a readable measure and no chart of its own; its only visual defect is the missing gap before the Timeline heading that follows it (the raw \"Front matter\" key:value dump just below is a neighbouring section and is not judged here).

1. **Medium · narrative** (New reader)
   - Where: line 73: "The Chair left relative value and portfolio fit unscored, so the debate's overall score is provisional and the Watchlist bias rests on seven scored dimensions"; also line 74 "The bear's legal-control attack", line 76 "the portfolio debate defaults to data quality"
   - Problem: The limitations are written in the internal debate's terms: the Chair, the bear, the debate's score, seven unnamed scored dimensions, the portfolio debate. A portfolio manager who has not read the Debate record cannot tell what was scored or what "one step either way" means.
   - Fix: State each limitation in terms of the credit view: what evidence is missing, which conclusion it weakens, and how. Name the scored factors, or drop the count.
2. **Medium · narrative** (Saboteur)
   - Where: line 73: "once compensation is scored the bias could move one step either way, to Starter Position or to Avoid on the junior class"; line 74: "a judgement on missing protection rather than a demonstrated exploit"
   - Problem: Read together, these two bullets say the Watchlist call rests on an unscored compensation factor that could push it either way, and on a legal finding that was inferred rather than shown. That undercuts the conclusion without saying how much weight Watchlist can still bear, so a committee could read the call as a coin-toss.
   - Fix: Open the section with one sentence on how robust the Watchlist call is despite these gaps, then list the gaps, so the caveats qualify the judgement instead of cancelling it.
3. **Medium · visual** (Auditor)
   - Where: Screenshot CP-6_limitations.png, region x330-1440, y560-760 (crop CP-6-145-a.png): the last Limitations bullet ends at about y=640 and the "Timeline" heading sits about 10 px below it
   - Problem: No section spacing separates the end of Limitations from the next "Timeline" heading. Other headings on the page get roughly 30-40 px. The timeline row therefore reads as part of the limitations list.
   - Fix: Give the timeline block the same top margin as the other section headings, so Limitations visibly ends before it.
4. **Low · narrative** (New reader)
   - Where: line 75: "The liquidity defence that defeats the bear's payment-default chain uses the pro forma position at the October 2024 dividend date and a static single-year stress, with no month-by-month runway; the conclusion ... does not extend to the refinancing year itself."
   - Problem: Each bullet is a single sentence of 45 to 55 words joined by a semicolon. That is dense for a limitations list the reader is meant to scan.
   - Fix: Split each bullet into the gap first, then a short sentence on its effect on the view.

### Committee challenge

Kind: prose/table · handoff lines 122-126 · verdict **CONCERNS**

- Narrative: The section takes a real position: it challenges the Watchlist call on three specific points. But it is one unbroken paragraph in internal debate vocabulary ("the bull", "the Chair", posture labels), and the two quantitative claims it relies on are either undefined (23.47%) or unquantified (the subordinated prices and yields). No source references leak into the sentences; the Basis line is kept separate.
- Visual: There is no chart in this section. It shows as a single full-width text block whose line length is well beyond a readable width, and only two inline figures carry a faint dotted-underline Basis control.

1. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 124: "so the distance of 23.47% of EBITDA to that level must not be read as distribution headroom"
   - Problem: The 23.47% has no stated period, leverage basis or direction. It appears to be the EBITDA cushion from about 5.55x pro forma net leverage to 7.25x (5.55/7.25 ≈ 76.5%), but the reader cannot tell that, or whether it means EBITDA can fall 23.47% or debt can rise. The one figure the paragraph warns about is the one it leaves undefined.
   - Fix: State it as "EBITDA could fall 23.47% (FY2024, pro forma net leverage of 5.55x against the 7.25x net incurrence level) before that level is reached" so the warning is attached to a defined figure.
2. **Medium · narrative** (Saboteur)
   - Where: Line 124: "their prices rose towards par through FY2024 while secured debt grew, and their running yield sits below the newest secured notes, so either rates explain the move or the market is not charging for dilution"
   - Problem: The second challenge rests on price and yield comparisons but gives no prices, yields, dates or instruments. It then ends on an either/or with no lean, so the committee gets a suspicion of mispricing it can neither size nor act on.
   - Fix: Give the start and end prices and the two running yields with their instruments and dates (or say they are absent), and say which explanation the evidence favours.
3. **Medium · narrative** (New reader)
   - Where: Line 124: "the bull's strongest point is ... could take a Starter Position now; the Chair's answer is that the secured notes were priced above par at year end with call schedules unread"
   - Problem: "the bull", "the Chair", "Watchlist" and "Starter Position" are the internal debate's roles and capitalised posture labels, used here without explanation. "call schedules unread" and "at year end" (fiscal or calendar?) assume the reader knows the pipeline and its file set.
   - Fix: Use the reader's terms ("the case for buying", "the recommendation", "the call schedules were not in the documents supplied", "at 30 September 2024"), and define the posture labels on first use or link them to the Decision section.
4. **Medium · narrative** (New reader, Auditor)
   - Where: Lines 124: "The committee should press three questions before accepting Watchlist. First, ... Second, ... Third, ... The committee should also note that the year-end hedge book ends on 2027-09-30"
   - Problem: Three separate challenges and a fourth unrelated warning (the hedge expiry before the FY2028 refinancing) are packed into one paragraph of about 260 words. A committee member cannot scan it, and the hedge cliff, arguably the most concrete risk here, is buried as an afterthought in the last sentence.
   - Fix: Split it into a one-line lead and a numbered list of questions, each starting with its question, and give the hedge-expiry point its own item or move it to the findings.
5. **Medium · visual** (New reader)
   - Where: Screenshot CP-6_s-122.png, region x 330–1440, y 210–440 (Committee challenge paragraph)
   - Problem: The paragraph runs about 1,000 px wide, roughly 180–190 characters per line, as one unbroken nine-line block. That is far beyond a comfortable line length and gives the eye no entry points, unlike the tables directly below.
   - Fix: Cap prose width at about 75–90 characters per line, or break the block into the numbered items so the page shows where each challenge starts.
6. **Low · visual** (Auditor)
   - Where: Screenshot CP-6_s-122.png, crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-6-149-a.png: inline figures "7.25x" and "23.47%"
   - Problem: Only two figures carry the Basis control (bold monospace with a faint dotted underline). The paragraph cites four sources (line 125), but the price, yield and hedge-date claims have no visible source cue. The dotted underline is low-contrast and is the only sign that a figure is clickable.
   - Fix: Give the Basis control a clearer affordance (a visible underline or icon with enough contrast) and make sure the paragraph's sources are reachable from the claims that are not figures, for example with a paragraph-end Basis button.

## Evidence validation (CP-5)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-5/8e197024c22d08fa48bf7155dc2076068ea474657922d1a7ce3f3af18ba90607/1.response.md`

### Front matter + Request + Next module

Kind: run plumbing · handoff lines 1-13, 14-17, 374-377 · verdict **BLOCK**

- Narrative: This unit is pipeline plumbing (metadata, the module's request and routing to the next module). The reader sees it with module codes, pipeline vocabulary and a garbled code-substituted sentence, and none of it carries the credit judgement the house standard asks for.
- Visual: There is no chart, map or timeline here. The front matter renders as an unbroken line of snake_case key: value pairs, including a filename with the CP-5 code, and the Request and Next module sections are plain paragraphs that look like reader content.

1. **High · narrative** (Saboteur, New reader)
   - Where: Front matter lines 7-11: "confidence_score: 0 / confidence_band: Insufficient Information / committee_status: Restricted ... module_status: Ready with Limitations"
   - Problem: With no explanation, a confidence score of 0 and 'Insufficient Information' sit next to 'Ready with Limitations', so the reader can't tell whether this trace supports a committee decision. The clamp from -11.51 that explains the 0 appears only in the V17 table much further down.
   - Fix: Give one plain-language status sentence (e.g. restricted clearance, score clamped to zero because of the missing legal and market inputs), or drop the raw fields so the bottom line carries the judgement.
2. **High · narrative** (Auditor, New reader)
   - Where: Request line 16 as rendered: "Evidence validation evidence-trace validation, with the absorbed Evidence validation research-integrity grade ... across the ten supplied upstream handoffs"
   - Problem: Replacing both CP-5 and CP-5A with the display name produces a garbled, repeated sentence. 'Handoffs', 'upstream', 'absorbed', 'credit_snapshot pathway' and 'Top 5 traceability' are pipeline words, not reader language.
   - Fix: Rewrite as one reader sentence: what was checked (the top five credit drivers against the FY2024 annual report) and why (to decide whether the analysis can go to committee), with no module or pipeline terms.
3. **High · narrative** (Auditor, Saboteur)
   - Where: Next module lines 374-377 as rendered: "Committee decision should run next, using a Restricted clearance ... Changes since the last run stays conditional on a prior deliverable, as source readiness recorded."
   - Problem: This whole section is pipeline routing (which module runs next, a conditional prior deliverable, reruns) shown to a credit committee reader. Once module codes are replaced by page names, it reads as if pages run and as if the 'Changes since the last run' page is conditional.
   - Fix: Don't show Next module on the reader page; move any reader-relevant parts (re-review once executed debt documents and market levels arrive) into Limitations or what-would-change-the-view.
4. **High · visual** (Auditor, New reader)
   - Where: Front matter, CP-5_s-1.png top of main column (crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-5-173-a.png): "issuer_id: tdg module_id: Evidence validation ... filename: tdg_CP-5_20240930.md qa_status: Restricted confidence_score: 0" (handoff lines 1-12)
   - Problem: The YAML front matter is printed to the reader as one run-on line of snake_case keys with no separators, and it shows a module code on screen ("tdg_CP-5_20240930.md") and pipeline field names (module_id, qa_status, traceability_scope). Both break the house rules and the line can't be read.
   - Fix: Keep front matter off the page, or show only the reader-relevant status fields as labelled chips (clearance, confidence band, scope), with no filename or key names.
5. **Medium · narrative** (Saboteur)
   - Where: Next module line 376: "quote leverage on one stated basis, carry relative value as Unclear, and not treat 7.25x as a distribution gate"
   - Problem: The passage says to use one basis but doesn't name it (gross 6.01x or carrying 5.96x), and 7.25x appears with no metric, period or covenant context. The reader is left without the decision it points to.
   - Fix: State the chosen leverage basis and value, and say what 7.25x measures (e.g. the incremental-facility ratio test) wherever it is cited.
6. **Low · visual** (New reader)
   - Where: CP-5_s-1.png side navigation 'On this page': "Front matter", "Request", ... "Next module", and items such as "a method step Source Register"
   - Problem: The page index lists the plumbing sections next to the reader sections, so the reader is drawn to non-analytical content. The run-on front matter block also sits right under the Maps heading with no visual break.
   - Fix: Hide the plumbing sections from the reader view and from the page index, leaving the index to the analytical sections.

### Remediation priority map

Kind: prose/table · handoff lines 112-129 · verdict **BLOCK**

- Narrative: The section lists remediation items with no judgement first. It is written in pipeline vocabulary and module-coded IDs, and it puts the leverage-basis Material issue in an internal-pipeline bucket, which contradicts the clearance decision that follows.
- Visual: The section has no chart, map or timeline; it renders as a plain bulleted list whose priority-bucket labels look like body text and whose long lines run the full page width, so the page shows no hierarchy of urgency.

1. **High · narrative** (Auditor, New reader)
   - Where: L119-121: "Must-fix before the canonical Markdown handoff is consumed downstream: - CP5-002: ... gross principal shown as the logged delta, and have consumers cite one basis. - CP5-006: Hedge handoff to add a calculation row"
   - Problem: The section is written in pipeline language a committee member does not use: "canonical Markdown handoff", "consumed downstream", "consumers", "logged delta", "Hedge handoff", "rerun the legal module" (L116), "fact pack" (L127), "downside handoff's event registers ... catalyst-phase IDs" (L128). The ruling bans this vocabulary on screen. Promoted because two personas raised it.
   - Fix: Say each remediation as what the reader will see differently (for example, "leverage will be quoted on one debt basis throughout"), and drop the bucket and items that are only about how modules talk to each other.
2. **High · narrative** (Saboteur)
   - Where: L120: "CP5-002: Adopt carrying-value debt as the headline basis..." filed under L119 "Must-fix before the canonical Markdown handoff is consumed downstream"; compare L134 "The leverage-basis drift (CP5-002) and the market-data gap (CP5-004) restrict how leverage and relative value can be presented. For committee use, these four Material issues must be disclosed"
   - Problem: The map lists three must-fix items before committee, but the clearance decision directly below names four Material issues that restrict committee use. The leverage-basis drift is filed as an internal-pipeline fix, so a reader using this map as the checklist would take leverage to committee without the basis disclosure.
   - Fix: Put all four Material issues under the before-committee bucket, consistent with the clearance decision, and mark each item Material or Minor.
3. **High · narrative** (Auditor, New reader)
   - Where: L115-128: identifiers "CP5-001" through "CP5-007" opening every bullet, e.g. L115 "CP5-001: Forward credit model and downside pathway to restate the 7.25x references"
   - Problem: Every item starts with an ID built from the module code (CP5-xxx). The house rule bans module codes on screen, and the reader has nowhere to look these IDs up. Promoted because two personas raised it.
   - Fix: Replace the IDs with short plain-language issue names (for example, "Covenant-test wording" or "Missing legal documents"), or with neutral numbers defined on the page.
4. **Medium · narrative** (Saboteur)
   - Where: L114-117 "Must-fix before committee:" opens straight into bullets; no lead sentence
   - Problem: The section has no judgement first. The reader is not told which single fix matters most, which one changes a credit view, or that none of them changes a conclusion (that point only arrives at L134). The "priority" in the title is not explained.
   - Fix: Open with one sentence giving the bottom line, for example that the missing legal documents are the only gap that limits sizing and that no fix changes the credit conclusion, then the ranked list.
5. **Medium · narrative** (New reader)
   - Where: L115: "restate the 7.25x references as house-basis distances to the incremental-facility test"; L121: "add a calculation row for the net derivative asset or remove the figure"
   - Problem: Several items rely on context the reader doesn't have. "house-basis distances" is undefined, the 7.25x figure has no stated basis, and "the figure" for the net derivative asset gives no value, unit or period. The reader cannot tell what is wrong or how much it matters.
   - Fix: For each item, state the figure involved with its unit and period and say in one clause why it is misleading as it stands.
6. **Medium · visual** (Auditor, New reader)
   - Where: Screenshot CP-5_s-112.png, crop (330,220)-(1440,620) saved as scratchpad/tmp/CP-5-165-a.png: bucket labels "Must-fix before committee:", "Monitoring follow-up:", "Formatting / hygiene:"
   - Problem: The four priority buckets are drawn as plain body-weight text lines with no spacing above them, so they read like ordinary list text. Nothing on screen shows priority or severity, so the map has no visual hierarchy. Promoted because two personas raised it.
   - Fix: Show the buckets as sub-headings (or a compact table with Priority, Issue, Severity and Credit effect columns) with space between groups, so the before-committee items stand out.
7. **Low · narrative** (Saboteur)
   - Where: L124: "CP5-003 and CP5-004: re-audit on receipt of documents or yield-to-worst levels."
   - Problem: Two issues already listed as must-fix before committee appear again under monitoring, with no trigger date or owner. That blurs whether they block committee use or are being watched.
   - Fix: Fold the re-audit trigger into the original must-fix bullets and drop the duplicate bucket.
8. **Low · visual** (Saboteur)
   - Where: Screenshot CP-5_s-112.png, crop scratchpad/tmp/CP-5-165-a.png: bullets L115-L116 wrap to two lines at roughly 1,050 px measure
   - Problem: The long bullets run the full content width, about 170 characters per line, which is past a comfortable reading width for dense remediation text.
   - Fix: Cap prose and list width at about 80-100 characters, or shorten each item to one line.

### QA validation

Kind: prose/table · handoff lines 140-145 · verdict **BLOCK**

- Narrative: The section is pipeline QA process rather than credit narrative: it names scripts, files and module codes, and the 0/100 confidence score is left unreconciled with the \"Pass with Remediation\" clearance a few lines above.
- Visual: The section has no chart. It renders as an undifferentiated text block whose register-code replacement is garbled, it does not call out the key score, and the table directly below is clipped on the right.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 144: "Confidence Score: 0 / 100 (Band: Insufficient Information). qa_status: Restricted. committee_status: Restricted." read against line 132 "CLEARANCE DECISION: Pass with Remediation" and line 138 "evidence traceability is Ready with Remediation"
   - Problem: On the same page the module says the evidence passes and is ready with remediation, then scores its confidence at 0 out of 100 with "Insufficient Information", and does not reconcile the two. A committee member cannot tell whether the evidence base is usable or worthless.
   - Fix: State one judgement first, for example "usable with restrictions", and explain in one sentence why the arithmetic score floors at 0 (penalties of 69 points against a raw 57.49) without overturning the clearance, or drop the score from reader view.
2. **High · narrative** (Auditor, New reader)
   - Where: line 142: "The helper scripts `prepare_invocation.py`, `validate_handoff.py`, `confidence_score.py` and `completeness_check.py` were not run in this transport. Their checks were done by hand."
   - Problem: The whole paragraph is pipeline process: script filenames, "transport", "method block", "runbook and step bundles", CANON_SHARED, CP-5_SCHEMA_REFERENCE.md and other files carrying module codes. None of it is reader language, and on-screen module codes (CP-5, CP-5A) break the house rule.
   - Fix: Move process provenance off the reader page, or reduce it to one plain sentence on any effect on reliability, such as "automated completeness checks were not run; the review was done manually".
3. **High · narrative** (Auditor, Saboteur)
   - Where: line 142: "All 17 required registers (T5B.1 to T5B.8, T5.1 to T5.9) are present below", rendered on screen as "(a method step to method steps to a method step)" (CP-5_s-140.png, top paragraph)
   - Problem: Replacing the register codes on screen produced unreadable text ("a method step to method steps to a method step"). The source text leaks register codes, and the rendered text is broken.
   - Fix: Say "All 17 required evidence tables are present below" with no codes, and make sure the substitution never produces gibberish.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: line 144: "The inputs were E = 76, C = 91.30, S = 0.7 and P = 69 (four MATERIAL at 15 each, three MINOR at 3 each). Pre-penalty score 57.49, after penalty -11.51, clamped to 0."
   - Problem: The variables E, C, S and P are never defined, so the reader cannot follow the calculation. "The Material cap of at most 59 is met" is trivially true once the score is 0 and tells the reader nothing.
   - Fix: Name each input in words (for example evidence coverage 76%) or leave the formula out, and drop the cap sentence.
5. **Medium · narrative** (Auditor)
   - Where: line 144: "qa_status: Restricted. committee_status: Restricted."
   - Problem: Raw snake_case field labels and shouted capitals ("MATERIAL", "MINOR") are machine register, not committee prose. The restriction is also repeated after the clearance decision already stated it.
   - Fix: Say once, in plain words, "Committee use: restricted", with the reason.
6. **Medium · narrative** (Auditor)
   - Where: lines 140-145, the whole "### QA validation" section
   - Problem: The section opens with process rather than a judgement, and its only conclusion (the score) comes last and contradicts the earlier verdict. It breaks the judgement-first standard.
   - Fix: Open with a one-line bottom line on whether the QA result changes how far the reader should trust the analysis, and put any detail after it.
7. **Medium · visual** (Auditor, New reader)
   - Where: CP-5_s-140.png, the paragraph block (crop CP-5-168-a.png, y≈220-330) and the heading below it, "a method step Source Register"
   - Problem: The section is a dense block of text with four inline monospace filenames and a long list of .md filenames, and nothing visually marks the key result, the 0/100 score. The heading that follows repeats the broken "a method step" label, as do about 15 entries in the On this page navigation.
   - Fix: Show the result as a short labelled status line or chip at the top of the section, remove the code-styled filenames, and give the register headings plain names.
8. **Low · visual** (Auditor)
   - Where: CP-5_s-140.png, the Source Register table directly under the section, right edge at x≈1390 (original px)
   - Problem: The table's last column (Source) is cut off at the card edge ("TDG_20…", "Busines…") with no visible sign that it scrolls, and several cells wrap to 8 or more lines.
   - Fix: Show a scroll cue or fit the columns so the Source column is fully visible.

### Gaps

Kind: prose/table · handoff lines 363-373 · verdict **BLOCK**

- Narrative: The Gaps table leaves out the two material gaps (executed debt documents and market data) that drive the Restricted clearance, lists only harmless or pipeline-internal items, and its rendered module names contradict the page's own navigation.
- Visual: There is no chart in this section. The table renders cleanly with no clipping, but the column widths squeeze the Effect column and nothing visually separates material gaps from hygiene ones.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Gaps table lines 365-372 (six rows: quarterly filings, PDF annual report, upstream calcs, schema references, unsupplied modules, full scope); none names the executed debt documents or market data
   - Problem: The run's two material gaps are missing from this table: the executed debt documents (line 257 CP-5-GAP-001, line 331 CP5-003) and market levels (line 332 CP5-004). Those gaps drive the Restricted clearance and the zero confidence score. Every row that is listed reads 'no conclusion changes' or 'None', so a reader who stops here will conclude the gaps don't matter.
   - Fix: Lead the table with the executed-document and market-data gaps and their effect (payout and priming capacity unsized, relative value Unclear, clearance Restricted), then list the hygiene gaps below them.
2. **High · narrative** (New reader, Auditor)
   - Where: line 370 "CP-5 and CP-5A schema and system references, other CANON_SHARED sections | Unavailable companions; registers built from the output profile columns | None in this transport | context"
   - Problem: This row is about pipeline internals, not credit. On screen it reads "Evidence validation and Evidence validation schema and system references, other CANON_SHARED sections". That shows the label mapping collapsing CP-5A into the same name, and it leaks CANON_SHARED, 'transport', 'registers' and 'output profile columns' to the reader.
   - Fix: Drop this row from the reader view, or record it in an internal QA note; it has no credit effect.
3. **High · narrative** (Saboteur, New reader)
   - Where: line 371 "Modules named by the method but not supplied (CP-1B, CP-1C, CP-2C, CP-2D, CP-3C, CP-4C, CP-6A) | Not producers in this run; no trace possible for them"
   - Problem: On screen the codes become "Earnings changes, Peer benchmark, Business & governance, Liquidity, Refinancing & LME, Recovery & fulcrum, Committee decision". The page's own navigation lists Business & governance and Committee decision as modules in this run, and the Next module paragraph says Committee decision runs next. The table therefore contradicts the page. 'Producers' is also pipeline vocabulary.
   - Fix: Give each sub-module a distinct reader name, or say plainly which analyses (for example liquidity or recovery) this run does not cover and what that leaves unassessed.
4. **Medium · narrative** (Saboteur)
   - Where: line 369 "Upstream calculations outside the top drivers not re-performed (stress D-series, hedge M-series, forecast G-series) | Accepted on their self-checks; noted as a limitation on secondary figures"
   - Problem: The row admits the stress, hedging and forecast figures went unchecked but frames that as affecting only 'secondary figures', without saying which committee numbers rest on them. 'D-series / M-series / G-series' are internal labels that mean nothing to the reader.
   - Fix: Name the reader-facing figures that were not independently checked (for example downside leverage or forecast FCF) and drop the series labels.
5. **Medium · narrative** (Auditor, New reader)
   - Where: lines 370-372 Source column "context"
   - Problem: Three rows give 'context' as their source. That is a run-settings identifier, not evidence a reader can locate. Line 24 states it is 'not issuer evidence'.
   - Fix: Use a readable source label (for example 'Run settings') or leave the cell as an explicit dash when the gap has no document source.
6. **Low · narrative** (New reader)
   - Where: line 363-365 "## Gaps" followed directly by the table
   - Problem: The section opens straight into a table with no lead sentence giving the judgement. The reader has to infer which gaps matter.
   - Fix: Add one opening sentence naming the gap that governs the clearance.
7. **Low · visual** (New reader, Auditor)
   - Where: Gaps table, CP-5_s-363.png approx. y 1455-1845 (display coordinates)
   - Problem: The Gap column takes about 40% of the width while Effect and Action wrap to three lines in narrow columns. Effect is the column that carries the judgement, yet it is the hardest to scan, and every row has the same visual weight, so nothing marks a material gap.
   - Fix: Rebalance the column widths toward Effect and add a severity chip or column so material gaps stand out.

### Sources

Kind: prose/table · handoff lines 18-40 · verdict **BLOCK**

- Narrative: This section is an audit list, not prose, so the reading order does not apply. Its main failures are pipeline vocabulary ('Supplied handoff', 'Pinned', 'absorbed into this run'), internal file names, and the missing legal documents being buried in a 'context' row.
- Visual: There is no chart in this section. Two bordered tables render cleanly with no clipping, but 64-character hash columns take most of the width, and the second table repeats each module name in two inconsistent forms.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: Line 26 table header "| Supplied handoff | Module | sha256 |" and line 39 "Pinned sources not relied on ... CP-5A has no separate handoff: it is absorbed into this run." (rendered: "Evidence validation has no separate handoff: it is absorbed into this run.")
   - Problem: Pipeline words ('handoff', 'pinned', 'absorbed into this run') reach the reader in a column header and the closing note. Because the renderer swapped CP-5A for the page's own name, the note now says the page the reader is on 'has no separate handoff', which tells a committee member nothing.
   - Fix: Head the table 'Earlier analyses relied on', say 'Files supplied but not used:' and drop the absorbed-module sentence from the reader view.
2. **High · visual** (New reader, Auditor (promoted))
   - Where: Both Sources tables, sha256 column; CP-5_s-18.png crop x 340-1400, y 220-1160 (/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-5-157-a.png)
   - Problem: The widest column on the page holds 64-character hashes that a portfolio manager cannot use. It squeezes the useful 'Use in this module' column into a tall, narrow block and pushes the filing name into four broken lines.
   - Fix: Remove the hashes from the reader view, or fold them into a provenance tooltip or the Evidence page, and give the width to the filing description and page list.
3. **Medium · narrative** (New reader)
   - Where: Line 22 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"; line 24 "context"
   - Problem: The sources are named by internal file names (accession number, .htm.jsonl extension) and by a lowercase 'context' row. A reader cannot tell at a glance that these are the FY2024 Form 10-K, the Q1 FY2025 10-Q and the run settings.
   - Fix: Show a reader label such as 'Form 10-K, fiscal year to 30 Sep 2024 (filed Nov 2024)', and leave the file identity in a secondary line or tooltip.
4. **Medium · narrative** (Saboteur)
   - Where: Line 24 "Run settings only (as-of, pathway, blank quotes, ratings, peers, legal documents flagged executed but not attached); not issuer evidence"
   - Problem: The fact that drives the Restricted clearance is that the executed legal documents and all market quotes are missing. Here it sits in a parenthetical in a row labelled 'context', next to the jargon 'pathway' and 'flagged executed'.
   - Fix: State the absence plainly in the row's use column: 'No credit agreement, indentures, market prices, ratings or peer levels were supplied.'
5. **Medium · visual** (New reader)
   - Where: Supplied-handoff table, rows "Deep research | Research questions" and "Business and transaction fact pack | Business & governance"; CP-5-157-a.png y 570-620
   - Problem: Each row gives the same analysis two different names: the first column uses the handoff title and the 'Module' column uses the navigation name. So the reader sees 'Deep research' cited in Basis lines but 'Research questions' in the side menu, and other rows simply repeat themselves.
   - Fix: Use one column with the navigation name, linked to that module, so the names in the Basis lines and the menu match.
6. **Low · narrative** (Saboteur)
   - Where: Line 23 "Not read by this module; its subsequent-event figures are traced only through the business and transaction fact pack's page citations"
   - Problem: A filing dated after the 30 Sep 2024 as-of date is listed with no date warning. A reader may take its figures as checked by this validation when they are second-hand.
   - Fix: Label the row 'After the as-of date; figures not re-checked here' at the start of the cell.
7. **Low · visual** (Auditor)
   - Where: Sources table, first row Source cell "...tdg-20240930.htm.jsonl Basis" chip; CP-5-157-a.png x 0-200, y 80-170
   - Problem: A 'Basis' chip appears on the 10-K row only, not on the 10-Q or context rows, so its meaning inside a sources table is unclear.
   - Fix: Show the chip on every row or none, or label what it opens.

### Bottom line

Kind: reader passage · handoff lines 43-50 · verdict **BLOCK**

- Narrative: The bottom line does open with a judgement, but the judgement concerns how far the evidence can be trusted, not the credit, and that is wrapped in shorthand. The second paragraph is mostly scoring vocabulary and states a zero confidence score that conflicts with \"traceable enough for committee use\".
- Visual: The section has no chart, map or timeline. On the page, the first paragraph's Basis chip is missing even though the data carries it, both paragraphs are set as heavy bold display text with figures that break the lines unevenly, and the right third of the column is empty.

1. **High · narrative** (New reader, Auditor)
   - Where: line 48: "The research-integrity grade is Pass with Remediation… Three minor hygiene defects add to these. Under the confidence formula the per-finding penalty more than absorbs the evidence score, so the confidence score clamps to zero and sits in the lowest band"
   - Problem: Half of the bottom line describes the internal scoring and process. It uses "research-integrity grade", "Pass with Remediation", "confidence formula", "per-finding penalty", "evidence score", "clamps to zero", "lowest band" and "hygiene defects", and it lists defects "in the forward model and the downside pathway" and "between modules". A committee member gets pipeline language, not a credit judgement.
   - Fix: Say in reader terms what the committee may rely on and what it must not, e.g. which numbers are safe to use and which conclusions wait for the debt documents and market prices. Leave the scoring mechanics to a lower section.
2. **High · visual** (Saboteur, Auditor)
   - Where: CP-5_bottom-line.png, first bold paragraph ending "…and the USD 6,637 million FY2028 maturity cluster." (crop x 330-1040, y 240-560; scratchpad/tmp/CP-5-158-a.png); handoff line 46 "Basis: TDG_2024-09-30_10-K_… pages 54, 63, 145, 153; calculation V07; calculation V08"
   - Problem: The first paragraph has no Basis chip on the page. data.js still holds its Basis line (pages 54, 63, 145, 153; V07; V08), so the renderer drops it. Only the second paragraph shows "Basis". As a result, the six headline figures (USD 4,216m, 132m, 3,000m, 19,702m, 4,600m, 6,637m) show no source on screen, which breaks the rule that every paragraph carries a Basis line.
   - Fix: Render a Basis chip after every paragraph that has a Basis line, including the first block of a lead (bold) bottom line.
3. **Medium · narrative** (Saboteur)
   - Where: line 45 "Traceable enough for committee use with disclosed restrictions" vs line 48 "the confidence score clamps to zero and sits in the lowest band"; line 76 "The scoring script was not run, so the zero confidence score is a hand application"
   - Problem: The bottom line gives two opposite signals: the run is fit for committee use, yet its confidence is zero and in the lowest band ("Insufficient Information"). It does not say which one governs. It also states the zero as fact, although the Limitations say it was worked out by hand and could move.
   - Fix: Lead with the single verdict that governs (Restricted, and what that permits). Then either state the zero score with its hand-calculated qualification or drop it from the bottom line.
4. **Medium · narrative** (New reader)
   - Where: line 45: "yet the payout and debt capacity that decides how far the extraction thesis can run has no governing document behind it, so creditors should treat the policy-risk view as proven by conduct and unsized by contract"
   - Problem: The opening is one sentence of more than 70 words. Its credit point is that dividend and debt capacity cannot be sized from the documents, and that point sits in the middle of the sentence behind undefined shorthand ("extraction thesis", "policy-risk view", "proven by conduct and unsized by contract"). A reader who has not seen the other modules has to decode it.
   - Fix: Split it into a short verdict sentence and a plain-language sentence on the unknown restricted-payment capacity and why it matters to creditors.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-5_bottom-line.png, both bottom-line paragraphs (x 296-850, y 190-840 at display scale): about 22 px bold display type with monospace dotted-underlined figures
   - Problem: Both paragraphs are set in the large bold lead style, so about 160 words of bold text fill most of the first screen. The scoring-mechanics paragraph gets the same weight as the verdict. Monospace figures inside the bold proportional text cause ragged breaks, e.g. "the" left alone before "USD 3,000 million", and "re-" hyphenated over a line break.
   - Fix: Keep the bold lead for the one-sentence judgement only. Set the following sentences in body type and keep the figure styling consistent with the surrounding text.
6. **Low · narrative** (Saboteur)
   - Where: line 45: "USD 132 million of dividend equivalents paid on 2024-10-18" vs line 61: "Dividend equivalents of USD 132 million in the annual filing against USD 131 million in the next quarterly filing"
   - Problem: The bottom line calls USD 132 million "confirmed", but the key findings on the same page treat it as an open source conflict. The payment dates (2024-10-18) are after the 30 September 2024 as-of date and are not labelled as subsequent events.
   - Fix: Note the open 132 vs 131 conflict, or label the figure with its source, and mark the post-as-of payments as subsequent events.
7. **Low · visual** (Auditor)
   - Where: CP-5_bottom-line.png, right of the text column (x about 860-1180, y 180-1960) and the top band (y about 180-195)
   - Problem: About a third of the content width is empty beside the text. The section's own "Bottom line" heading is scrolled under the sticky run bar, and partial grey bars show at the top right, so the reader lands on a bold block with no visible heading.
   - Fix: Keep the section heading visible below the sticky bar when jumping to a section, and use or narrow the empty right column.

### Key findings

Kind: reader passage · handoff lines 51-65 · verdict **BLOCK**

- Narrative: The findings are substantive, and the conclusions agree with the bottom line (Restricted, payout capacity unsized). However, the section leaks pipeline vocabulary (handoff, canonical, orphan claim, module blocked), opens with reassurance rather than the decisive defect, and leaves the sensitivity and leverage figures without basis or period.
- Visual: The section has no chart. It is laid out as a readable single column of bullets, but a Basis chip appears only on the first of six bullets, and figure chips are styled inconsistently with the Limitations list below them.

1. **High · narrative** (Auditor, New reader)
   - Where: L53 "Every handoff that uses the capacity driver carries a stated limitation, so no orphan claim is triggered."; L55 "the financial foundation and its consumers headline" / "the method's canonical basis is carrying value"; L57 "the legal module is blocked"; L63 "two handoffs" / "the hedge handoff" / "the same table IDs this module owns"
   - Problem: The section uses pipeline vocabulary the house standard bans: handoff (four times), consumers, canonical, "orphan claim", "module is blocked", "table IDs this module owns". A committee member who does not know the pipeline cannot read these, and the screenshot shows them on the page unchanged.
   - Fix: Restate each point in reader terms, e.g. 'every section that relies on payout capacity states the limitation', 'the house basis is carrying value', 'the legal review could not be completed', and drop the internal table-ID hygiene point or describe its effect on the reader.
2. **High · visual** (Auditor, Saboteur)
   - Where: CP-5_key-findings.png, Key findings list (crop CP-5-159-a.png, y≈220–1130). The handoff has Basis lines at L56, L58, L60, L62 and L64.
   - Problem: Only the first bullet shows a 'Basis' chip. Bullets 2 to 6 show none, although each has a Basis line in the handoff (for example L58: filing pages 34, 62 and the legal, forward-model and downside sections). As a result, the source references for the leverage-basis, payout-overstatement, relative-value, conflict and hygiene findings are not visible to the reader.
   - Fix: Render each bullet's Basis line as a Basis chip, as the first bullet already does, so that every key finding carries its own source reference on screen.
3. **Medium · narrative** (Saboteur)
   - Where: L53 "The top-driver lineage holds where it matters most." (first bullet), against L57 "its timing and gating as written is unsupported and must be reworded before committee use." (third bullet)
   - Problem: The list opens with reassurance and buries the finding that drives the Restricted clearance in third place: two modules overstate the documented payout-capacity gate. A reader who skims the first bullet comes away with a softer view than the bottom line's 'not for unrestricted use'.
   - Fix: Order the key findings by credit consequence, putting the unsupported 7.25x payout-gate statements and the missing executed documents first and the lineage confirmation last.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: L61 "management's rate sensitivity of about USD 30 million against the hedge module's USD 57.89 million"; L55 "two multiples for the same date"
   - Problem: Neither sensitivity figure states what shock it measures (basis points, annual interest expense or pre-tax income) or its period, so the reader cannot tell whether the near-2x gap is a real conflict or a definitional one. The leverage bullet also never names the date or the EBITDA period behind 6.01x and 5.96x.
   - Fix: State the shock size, measure and period for each sensitivity figure, and the as-of date and EBITDA basis for the leverage multiples, in the sentence where each appears.
5. **Medium · narrative** (New reader)
   - Where: L57 "Two modules overstate what the documents permit. The forward model says the documented debt-funded payout route stays open below 7.25x, and the downside pathway says crossing 7.25x closes it. The filing ties 7.25x and 5.00x only to..."
   - Problem: Bullets run to 4–8 rendered lines. They also lean on undefined terms ('top-driver lineage', 're-perform', 'directly sourced' versus 'calculated', 'hygiene', 'Unclear' as a label) and on the 7.25x and 5.00x thresholds without saying which ratio they measure. Without the other pages, the reader cannot follow.
   - Fix: Open each bullet with a one-sentence judgement, then add at most two short supporting sentences that name the ratio behind each threshold and use plain words for the validation status.
6. **Low · visual** (Auditor)
   - Where: CP-5_key-findings.png: Key findings bullets (y≈440–880) compared with the Limitations bullets (y≈1290–1550)
   - Problem: Figures in Key findings appear as monospace chips with dotted underlines ('USD 132 million', '7.25x'), which breaks the line rhythm of the proportional text, while the same thresholds in Limitations ('7.25x, 5.00x and 7.50x') are plain text. The same figure therefore looks different on one page.
   - Fix: Style figures the same way across all passages of a module, using a lighter treatment that keeps the body font, as in the VMO2 reference.

### Map: support and contradiction

Kind: map · handoff lines 78-93 · verdict **CONCERNS**

- Narrative: The table rows are specific and carry exact figures with page references in an Evidence column, but the section has no lead judgement. It also uses pipeline vocabulary in the evidence cells and labels a 0.05x debt-basis difference as a contradiction.
- Visual: The map is visible in the Maps panel, but node labels break mid-word and truncate the key figures. Edge labels in one colour, with no legend, can be read against the wrong rows, and the duplicate edge table there is set in monospace with link-style underlines.

1. **High · visual** (Saboteur, Auditor)
   - Where: Support and contradiction map, CP-5_maps.png, region x340-1400 y270-1070 (crop scratchpad/tmp/CP-5-162-a.png): node labels "Annual filing financin g disclosure", "Gross-basis leverage 6 .01x", "Management rate sensit ivity of about USD 30 ...", "Annual filing dividend equivalents of USD 13...", "Calculated rate sensit ivity of USD 57.89 mil..."
   - Problem: Node text wraps at a fixed character count, so words and numbers break mid-token ("6 .01x") and the figures that carry the contradiction are cut off ("USD 30 ...", "USD 13...", "USD..."). A reader cannot see either side of the 132 vs 131 or 30 vs 57.89 conflict on the drawing.
   - Fix: Wrap only at word boundaries and widen the nodes or use short labels, so every number in a node shows in full and is never truncated.
2. **High · visual** (Saboteur, Auditor)
   - Where: Same map, edge labels in the middle column, e.g. "Contradicts" level with the "Annual filing EBITDA reconciliation" row and "Unresolved" level with the "Annual filing dividend-restriction statement" row (crop y~190 and y~460)
   - Problem: Edge labels sit at curve midpoints, which line up with the wrong source rows, and crossing edges share one monochrome colour. A reader can attach "Contradicts" to the EBITDA reconciliation or "Unresolved" to the dividend-restriction statement. There is no legend for solid, dashed and dotted lines.
   - Fix: Colour-code or legend the three edge types and anchor each label to its own edge, or lay the map out so that no edges cross.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 89: "Legal module blocked at its file gate"; line 90: "hedge module conflict logged"; line 91: "Logged by the fact pack, not reconciled"; line 92: "context quotes blank"
   - Problem: The Evidence column uses pipeline words ("module", "file gate", "fact pack", "logged", "context quotes") that a portfolio manager cannot decode. The house standard bans this vocabulary.
   - Fix: State the evidence in reader terms, e.g. "Executed credit agreement and indentures not supplied" or "No market yield or spread quotes supplied".
4. **Medium · narrative** (Saboteur)
   - Where: line 85: "Carrying-value leverage 5.96x | Uses balance-sheet carrying debt instead of gross principal for the same date | Contradicts | Gross-basis leverage 6.01x"
   - Problem: This is a 0.05x difference in debt basis, not evidence against the leverage figure. Labelling it "Contradicts" next to real conflicts, such as the restricted-payment wording, inflates how contested leverage looks.
   - Fix: Use a separate edge type such as "Basis difference", or note in the row that both figures are correct on their own basis.
5. **Medium · narrative** (New reader)
   - Where: line 78-80: "### Map: support and contradiction" followed directly by "| From | Relationship | Edge type | To | Evidence |"
   - Problem: The section opens with an 11-row table and no sentence saying what it shows or what the committee should take from it (for example, that four contradictions and two unresolved gaps remain). "Edge type" is graph jargon. Under a heading that says "Map", the section page shows only a table, because the drawing sits in a separate Maps panel.
   - Fix: Lead with one judgement sentence summarising the support and contradiction count, rename "Edge type" to "Effect", and point the reader to the drawing.
6. **Medium · visual** (Auditor, New reader)
   - Where: Maps panel table "Edges of the map, as stated", CP-5_maps.png y~1100-2250
   - Problem: The From, Relationship and To columns are set in monospace, and every Relationship cell is underlined in blue like a hyperlink. This is dense and hard to read, and it differs from the proportional table that repeats the same rows in the section (CP-5_s-78.png top).
   - Fix: Render the edge table in the page's normal table style without link styling, or drop it from the Maps panel because the section already carries it.
7. **Low · visual** (Auditor)
   - Where: CP-5_s-78.png, map table From column: "Annual filing dividend disclosure Basis", "Issuer fair-value table Basis"
   - Problem: Every From cell ends in a grey "Basis" chip with no visible meaning, even though the Evidence column already carries the source. This adds clutter in the first column.
   - Fix: Show the Basis chip only where it opens a reference that the row does not already give, or give it a clearer label.
8. **Low · visual** (Auditor)
   - Where: Support and contradiction map, CP-5_maps.png y~290-1060
   - Problem: The two node columns take up only the middle third of a full-width panel, which leaves large empty margins while the node text gets truncated.
   - Fix: Use the available width for wider nodes instead of empty side space.

### Traceability conclusion

Kind: prose/table · handoff lines 94-107 · verdict **CONCERNS**

- Narrative: The section starts with a judgement, but that judgement is about the run and its modules rather than the credit. The leverage row does not state its debt basis and conflicts with the carrying-value basis the same page recommends, and filenames and internal status codes make it hard to read for someone who has not seen the sources.
- Visual: The table is clean and fits the page width, but the status column has no visual differentiation, the source filenames wrap mid-token, and the inline "Basis" text looks like part of the driver labels; the section has no chart, map or timeline.

1. **High · narrative** (Auditor, New reader)
   - Where: L96: "The run is traceable enough for a restricted committee decision ... The provenance gap that matters most ... two modules have written as if the incremental-facility test gated distributions."
   - Problem: The bottom line is about "the run" and its modules, not about the credit. Pipeline words ("run", "modules", "provenance", "trace", and "restricted" used as an internal clearance label) reach the reader, which breaks the house ban on module and pipeline wording. A reader who never saw the pipeline cannot tell what "restricted" allows, or which analysis is wrong.
   - Fix: Open with the credit consequence in reader terms, for example which conclusions a committee can rely on and which it cannot. Name the affected analyses (forward model, downside case) and leave out run and module vocabulary.
2. **High · narrative** (Saboteur, Auditor)
   - Where: L103: "Leverage 6.01x total, 5.55x pro forma net | Calculated | Yes | Remediation Needed | One debt basis must be chosen; 0.05x drift"
   - Problem: The headline leverage is the gross 6.01x. On the same page the remediation map (L120) says the carrying-value basis (5.96x, L85) should be the headline. The table never says which basis 6.01x uses, "pro forma" has no transaction or date, and "0.05x drift" has no comparator. A committee could anchor on a figure this module itself says should be replaced.
   - Fix: State the basis and date of each multiple in the cell (gross principal 6.01x against carrying value 5.96x; pro forma for what), and say which one the reader should use.
3. **Medium · narrative** (New reader)
   - Where: L102/L105 Source cells: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 54, 63"; L103: "calculation V01; calculation V02; calculation V04"
   - Problem: The sources are raw extraction filenames (.jsonl) and internal calculation IDs. A portfolio manager cannot map these to a document or a calculation without another page.
   - Fix: Show a reader label such as "FY2024 Form 10-K, pp. 54, 63" and a named calculation (for example "Gross leverage calc."), with the IDs linked rather than printed.
4. **Medium · narrative** (New reader)
   - Where: L100-L106 column values: "Directly Sourced", "Calculated", "Insufficient Information", "Committee-Ready", "Remediation Needed"
   - Problem: These Title Case codes come from an internal method taxonomy and are never defined here. "Remediation Needed" does not tell the reader whether the figure is usable, and "Lineage class" is jargon.
   - Fix: Rename the columns and values in plain terms (for example "How we know" and "Usable for committee? Yes / With caveat / No") or add a one-line legend.
5. **Medium · visual** (Saboteur, Auditor)
   - Where: Traceability conclusion table, CP-5_s-94.png crop (340,220)-(1400,810) saved as scratchpad/tmp/CP-5-163-a.png
   - Problem: The status column is plain grey text: "Committee-Ready" and "Remediation Needed" look identical. The two rows that are not committee-ready (leverage, covenant capacity) do not stand out, so a quick scan suggests everything is fine.
   - Fix: Render the status as a coloured chip or icon with a text label, so the two problem rows are visible at a glance.
6. **Low · narrative** (Saboteur)
   - Where: L96: "All five top drivers reach either a re-read page ... or a re-performed calculation, except covenant and payout capacity"; L98: "The table summarises each top driver's lineage and what it means for the committee."
   - Problem: "All five ... except" means four, so the reader has to recount, and the table intro sentence repeats the heading without adding anything.
   - Fix: Say "Four of the five top drivers ..." and drop the filler sentence before the table.
7. **Low · visual** (New reader)
   - Where: Source column, rows 1 and 4, scratchpad/tmp/CP-5-163-a.png (Source cells wrap as "TDG_2024-09-30_10- / K_0001260221-24-000083_tdg- / 20240930.htm.jsonl")
   - Problem: The long filename breaks mid-token over three lines, which makes the rows taller and hard to read. Meanwhile the narrow Yes/No "Re-performed" column leaves empty space.
   - Fix: Shorten the source label so it fits on one line, and narrow or merge the Re-performed column into the status column.
8. **Low · visual** (New reader)
   - Where: Driver cells: "Debt-funded special dividend Basis", "Covenant and payout capacity Basis" in scratchpad/tmp/CP-5-163-a.png
   - Problem: The grey "Basis" affordance sits inline after the driver text and reads like part of the label ("dividend Basis"). It has no visible chip border or icon to show that it is a control.
   - Fix: Style "Basis" as a distinct chip or icon set apart from the cell text.

### Module status and scope

Kind: prose/table · handoff lines 108-111 · verdict **BLOCK**

- Narrative: The section is one paragraph of pipeline housekeeping (handoffs, VE-015, cpdr.adoptions, issuer_id) with no judgement first, and its status label disagrees with the clearance and overall-traceability labels next to it.
- Visual: There is no chart. The section renders as one dense, unlabelled 5-line block with a code-font token, and no key-value or chip layout would let a reader pick out the status at a glance.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 110: "Module Status: Ready with Limitations (the legal module reports Blocked; executed legal documents and market data are absent)."; also line 132 "CLEARANCE DECISION: Pass with Remediation" and line 138 "evidence traceability is Ready with Remediation"
   - Problem: Three neighbouring sections give three different status labels (Ready with Limitations, Pass with Remediation, Ready with Remediation) and never say how they relate. A committee reader cannot tell which one is the verdict or whether "Limitations" is milder than "Remediation".
   - Fix: Use one status label for the module throughout and put it first. If a second grade is really needed, define it once with its relationship to the first.
2. **High · narrative** (Auditor, New reader)
   - Where: line 110: "Entity key: issuer_id tdg available and consistent across all ten handoffs ... Orphan-claim check (VE-015): not triggered ... so no `cpdr.adoptions` rows are required."
   - Problem: The paragraph is written in pipeline vocabulary that the house standard bans from the page: "handoffs", "issuer_id", the register code VE-015, the table name cpdr.adoptions, "this module" and "Traceability Scope: Top 5 (default; full scope not requested)". The rendered page shows all of it, with cpdr.adoptions in code font.
   - Fix: Rewrite it for the reader: every analysis covers TransDigm at 30 September 2024 on FY2024, every weak claim carries its caveat, and only the five main credit drivers were traced. Drop the IDs, table names and the research-adoption sentence.
3. **Medium · narrative** (Saboteur)
   - Where: line 110: "Orphan-claim check (VE-015): not triggered, because every committee-facing claim classed Weak Lineage or Insufficient Information carries a limitation in its originating handoff."
   - Problem: This reassures the reader that every claim is properly caveated. Two paragraphs earlier, though, the module says two modules "have written as if the incremental-facility test gated distributions" (line 96), which is the CP5-001 must-fix. The clean pass blurs a known overstatement.
   - Fix: Qualify the pass by naming the open overstatement that still needs rewording, so the clean check does not read as an all-clear.
4. **Medium · narrative** (New reader)
   - Where: line 110: "consistent across all ten handoffs"
   - Problem: The reader is told "ten" sources were checked, but the module list beside the text shows 14 modules and the page never says which ten. The count cannot be checked from the page.
   - Fix: Name the analyses covered, or say "every earlier analysis in this run", rather than giving an unexplained count.
5. **Medium · narrative** (New reader, Auditor)
   - Where: line 110, whole paragraph: five run-in labels ("Module Status:", "Traceability Scope:", "Entity key:", "Orphan-claim check (VE-015):", "Research adoption:") in one block
   - Problem: The paragraph is configuration metadata, not judgement. It does not open with what the status means for the committee, and it sits between the traceability conclusion and the remediation map, so it breaks the reasoning between them. It has no Basis line.
   - Fix: Lead with one judgement sentence (usable for a restricted decision; the legal and market gaps limit it), or move this housekeeping into the limitations or appendix area.
6. **Medium · visual** (New reader, Auditor)
   - Where: screenshot CP-5_s-108.png, region x 330-1420, y 210-350 (crop CP-5-164-a.png): the paragraph under "Module status and scope"
   - Problem: Five label-value pairs are run together as one 5-line justified block with no bold labels and no line breaks, so the eye cannot find the status or the scope. The monospace "cpdr.adoptions" token stands out as code on a reader page.
   - Fix: Show the status and scope as a short key-value list or a status chip, with labels set apart and no code-font tokens.
7. **Low · visual** (Saboteur)
   - Where: screenshot CP-5_s-108.png, top of the content column (status paragraph) next to the "Legal & covenants" sidebar chip "Not assessable"
   - Problem: The sidebar marks the legal module "Not assessable", while this paragraph says it "reports Blocked". Two words for the same state appear on the same screen.
   - Fix: Use the same state label in the paragraph as in the sidebar chip.

### Clearance decision

Kind: prose/table · handoff lines 130-135 · verdict **CONCERNS**

- Narrative: The section is short, but its verdict says pass and nothing blocked, while the same module records a Blocked legal module and a 0/100 confidence score, and it shows internal issue codes and unexplained shorthand to the reader.
- Visual: There is no chart, map or timeline in this section. It renders as a heading plus two legible text paragraphs with no clipping, but the verdict and restriction get no visual emphasis.

1. **High · narrative** (Saboteur, Auditor)
   - Where: L132 "CLEARANCE DECISION: Pass with Remediation." with L134 "No defect changes a credit conclusion, so nothing is blocked." (L110 says "the legal module reports Blocked"; L115 files CP5-001 under "Must-fix before committee")
   - Problem: The verdict reads as a pass and says nothing is blocked. The same module records a Blocked legal module and four must-fix-before-committee items, and two sections later it scores confidence at "0 / 100 (Band: Insufficient Information)" (L144). A committee member who reads only this verdict would take the evidence as cleared.
   - Fix: Open with a judgement that matches the restriction and the 0/100 score (e.g. restricted use, pending the legal documents) and reconcile the 'nothing is blocked' wording with the Blocked legal module.
2. **High · narrative** (New reader, Auditor)
   - Where: L134 "The legal-capacity overstatement (CP5-001) and the absent legal documents (CP5-003) restrict use ... The leverage-basis drift (CP5-002) and the market-data gap (CP5-004)"
   - Problem: Internal issue codes that look like module codes appear on screen in narrative sentences (visible in CP-5_s-130.png, top paragraph). The house rule bars CP-style codes from the reader's view. The reader cannot decode them without another section.
   - Fix: Name each issue in plain words and keep the codes out of the reader-facing text, or confine them to a register column.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: L134 "the capacity driver is unsized, leverage is shown on a stated basis, relative value is Unclear, and the 7.25x figure is not a distribution gate."
   - Problem: "7.25x" has no metric, basis or period. "Capacity driver", "stated basis" and "gate" are unexplained shorthand, so the four required disclosures cannot be repeated accurately by a reader who has not read the sources.
   - Fix: State each disclosure fully: which leverage ratio 7.25x is and on what basis, which debt basis leverage uses, and what capacity is unsized.
4. **Medium · narrative** (Auditor, New reader)
   - Where: L132 "CLEARANCE DECISION: Pass with Remediation. Critical Issues: 0. Material Issues: 4. Minor Issues: 3. Committee Use: Restricted."
   - Problem: The bottom line is a key-value status string with an all-caps label and capitalised status terms, not a judgement-first sentence. "Pass with Remediation" also conflicts with the module status "Ready with Limitations" (L110) and "Ready with Remediation" (L138), giving three labels for one state.
   - Fix: Write one plain sentence verdict using a single consistent status term, then give the counts.
5. **Low · visual** (Auditor, New reader)
   - Where: CP-5_s-130.png, region y about 190-300 (Clearance decision heading and two paragraphs)
   - Problem: The module's decisive verdict is set as plain body text, the same weight as the paragraph after it. There is no chip or emphasis for 'Restricted', so the restriction does not stand out from the dense traceability and QA text that follows.
   - Fix: Show the clearance outcome and the committee-use restriction as a visible status chip or bolded lead line, as other status cues on the page are shown.

### Analytical appendix — complete canonical registers (part 1 of 2: from 'T5B.1 Source Register')

Kind: register appendix · handoff lines 146-240 · verdict **BLOCK**

- Narrative: The registers' figures check out arithmetically (I re-derived 6.01x, 5.55x, 81.07%, 69.00%, 2.31x, 23.47%, 24,319 and 57.89). The text fails the house standard because pipeline vocabulary and codes reach the reader ("handoff", "canon", "consumer", VE-015, CP5-001), the leverage claim status contradicts itself across tables, and the section has no opening bottom line.
- Visual: This section has no chart. As laid out on the page, the renderer turns every register heading and 17 contents entries into "a method step ...", the wide tables cut off the Source column at the card edge, and raw .jsonl filenames plus a "Basis" chip on every row crowd the narrow columns.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 155 "Handoff pinned by CP-OS" (rendered "Handoff pinned by Run activity", with ids "HO-Source readiness"); line 236 "Gross-principal basis used where canon requires carrying value"; line 235 "limitation stated in every consumer, so VE-015 not triggered"; line 210 "No clause-level support; see CP5-001"
   - Problem: Pipeline wording that the house standard bans reaches the reader on screen: "handoff", "pinned", "canon", "consumer", the internal rule code VE-015, the issue code CP5-001, row ids C23/C24/G2/F14/GP1, and "HO-" source ids. A credit committee member cannot decode any of it.
   - Fix: Describe upstream sources in reader terms (for example "Financial foundation analysis, this run"), replace "canon" with the stated house leverage basis, and drop rule and issue codes or replace them with plain cross-references.
2. **High · visual** (Auditor, New reader)
   - Where: Line 148 "#### T5B.1 Source Register" (and 166, 176, 189, 212, 230), shown on screen as "a method step Source Register" (CP-5_s-148.png, y~235 and y~688; left "On this page" list y~245-772). Also line 197 "CP-1 C23, C24; CP-3 T3B.2", rendered as "Financial foundation C23 , C24 ; Security selection a method step"
   - Problem: The code-stripping renderer turns register ids into the placeholder "a method step". Every register heading and 17 table-of-contents entries now begin with that meaningless phrase, and table cells contain garbled fragments such as "Security selection a method step". The reader cannot tell the registers apart by their headings.
   - Fix: Show each register under a plain title ("Source register", "Credit driver ranking" and so on) with no placeholder, and remove or translate internal row ids inside cells, never replacing them with "a method step".
3. **Medium · narrative** (Saboteur)
   - Where: Line 171 "Leverage 6.01x total, 5.55x pro forma net"; line 181 "Leverage 6.01x and 5.55x | CP-1 | ... | Partially Supported | Medium | Remediation Needed"; line 216 "Supported; basis differs from canon | High"; line 236 "Headline leverage 6.01x and 5.55x | Gross-principal basis used where canon requires carrying value"
   - Problem: Four tables on the same page grade the same leverage figure three different ways: as the ranked headline driver, as Partially Supported/Medium/Remediation Needed, as Supported/High, and as a Material flag saying the headline uses the wrong basis. The 5.96x/5.50x carrying-basis figures appear only in a Limitation cell, so a committee member scanning the ranking takes away 6.01x.
   - Fix: Use one claim status and one headline basis for leverage across T5B.2, T5B.3 and T5B.5, and show the alternative multiple next to it with its basis named.
4. **Medium · narrative** (New reader)
   - Where: Line 157 "Payout and issuance facts, conflict X1"; line 158 "Business-quality context, RV gap"; line 170 "Sets the thesis and the subordinated-LGD concern"; line 146 "complete canonical registers"
   - Problem: The section opens straight into six dense registers. There is no one-line statement of what the reader should take from them, and it uses undefined shorthand (X1, RV, LGD) and the internal word "canonical" in its title.
   - Fix: Open the appendix with a one-sentence bottom line on what the registers show (for example how many drivers are fully traced and which are not), title it in plain words, and spell out abbreviations on first use.
5. **Medium · visual** (New reader, Auditor)
   - Where: T5B.1 Source Register and T5B.2 Credit Driver Ranking tables, CP-5_s-148.png x 1330-1390, y 255-1180 (Source column) and y 1700-2400
   - Problem: The 9- and 10-column tables do not fit the 1440 px page. The Source column is cut off at the card edge ("TDG_20 / 30_10- / K_0001", "Busines / transact"), and the other columns are squeezed into 5-9 line wraps that make each row a tall block of text.
   - Fix: Fit the tables to the page width: drop or merge columns that repeat each other (Source Document Name repeats Source; Source Trace repeats Source), or give the table a visible horizontal scroll affordance so no cell is cut off.
6. **Medium · visual** (New reader)
   - Where: Line 152 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" shown as Source Document Name and again in the Source column (CP-5_s-148.png y 300-460), repeated in nearly every row of T5B.2 to T5B.6
   - Problem: Raw extraction filenames (with accession number and a .jsonl suffix) are used as document names. They fill the narrow columns with unbreakable strings, and a reader expects to see "FY2024 Form 10-K".
   - Fix: Show a reader-facing document title ("TransDigm FY2024 annual report (10-K), p. 145") and keep the filename out of view.
7. **Low · visual** (Auditor)
   - Where: "Basis" chip after every first-column id: "SRC-10K Basis", "CTX Basis", "1 Basis", "2 Basis" (CP-5_s-148.png x 370-470, y 300-1180 and y 1750-2150)
   - Problem: A grey "Basis" link is attached to every row id, so the id column reads as "1 Basis" and "HO-Downside Basis". This adds noise, and nothing on screen says what the chip opens.
   - Fix: Show the basis affordance once (as a column header icon or on row hover) rather than as a word fused to each id.

### Analytical appendix — complete canonical registers (part 2 of 2: from 'T5B.7 Auditability Assessment')

Kind: register appendix · handoff lines 241-336 · verdict **CONCERNS**

- Narrative: This is an appendix of registers, so the bottom-line-first order does not apply, but module and issue codes, pipeline terms (handoff, canonical, YAML, transport H2) and mixed severity scales still reach the reader.
- Visual: The section has no chart. The tables render cleanly with good contrast, but the \"a method step\" headings, the doubled source labels and the Basis chip on every row add clutter, and 7-8 narrow columns make the cells wrap heavily.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 266 header "| Module | Handoff canonical `.md` / run_id | ... | Envelope / Headings Status |"; line 268 "sha256 4e5e4b7b; run tdg-2024-09-30-credit_snapshot-opus-medium | ... | Transport H2 set present; no YAML" (shot CP-5_s-241.png, Input Module Register, y≈1530-1990)
   - Problem: The Input Module Register prints pipeline vocabulary on screen: "handoff", "canonical", a literal backtick `.md`, sha256 prefixes, "Transport H2 set" and "YAML". It also shows an internal run id that does not match the run label in the page header (TDG-PROOF-SNAPSHOT-OPUS-002). A credit reader cannot interpret any of it.
   - Fix: Show module name, scope, source quality and review status in reader words. Drop or fold the hash, run id and envelope/YAML columns, or add a single line saying all inputs come from this run.
2. **High · narrative** (Auditor, Saboteur)
   - Where: Line 257 "Driver 5 Insufficient Information; CP5-001 and CP5-003"; line 258 "RV Unclear; CP5-004"; lines 269-277 Notes "CP5-002 debt basis", "Feeds CP5-003"; lines 329-335 Issue IDs "CP5-001" to "CP5-007"
   - Problem: Gap IDs were rewritten to "Gap 1" to "Gap 6", but the issue IDs CP5-00x still appear on screen in Impact and Notes cells (visible in the Gaps Ledger and Input Module Register). That is module-code wording the house rule bans, and the reader has to jump to the Issue Log to decode it.
   - Fix: Rewrite the issue IDs the same way the gap IDs were (e.g. "Issue 1") or name the issue inline, such as "payout-route wording".
3. **Medium · narrative** (Auditor)
   - Where: Line 279 "Module Status (QA phase): Ready with Limitations. CP-5 evidence trace: this handoff. External-source usage: none in any handoff"; line 311 "The leverage-basis difference is logged once, under T5.3."
   - Problem: These narrative sentences contain a module code (CP-5), the word "handoff" and a register code (T5.3). All three are on the house list of terms that are not reader language.
   - Fix: Say "Evidence review status: ready with limitations; no external sources were used" and point to the math audit by its plain title.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 234 "Material" / line 257 "High" / line 285 "MATERIAL" / line 245 "Ready with Remediation" / line 285 "Restricts Committee Use"
   - Problem: The appendix grades severity on several incompatible scales: Material/Minor, MATERIAL/MINOR, High/Medium/Low and Committee-Ready/Ready with Remediation. Gap 1 is "High" while the same issue is "MATERIAL" in the Issue Log. A committee member cannot tell whether these are the same grade.
   - Fix: Use one severity scale for every register, or add a one-line key mapping the scales to each other.
5. **Medium · visual** (New reader, Auditor)
   - Where: Register headings "a method step Auditability Assessment", "a method step Gaps Ledger", "a method step Input Module Register" and the On-this-page list (shot CP-5_s-241.png, y≈190, 905, 1505 and left nav y≈1200-1645)
   - Problem: Replacing the T5B.x/T5.x codes produced headings that read as broken English ("a method step ..."). Repeated sixteen times in the page navigation, they bury the useful titles.
   - Fix: Use the plain register title only, e.g. "Auditability assessment" or "Gaps ledger".
6. **Medium · visual** (New reader, Auditor)
   - Where: Source column "Financial data foundation (Financial foundation)", "Business and transaction fact pack (Business & governance)", "Downside pathway (Downside)", plus a "Basis" chip in every first-column cell (shot CP-5_s-241.png, Input Module Register and Auditability tables)
   - Problem: Rewriting the source labels left doubled names with parentheses, which pad the narrow Source column to 4-5 wrapped lines. A grey "Basis" chip sits beside every row label, but the Source column already gives the basis.
   - Fix: Show one module name per source cell, and drop the per-row Basis chip in tables that already have a Source column.
7. **Low · visual** (New reader)
   - Where: Auditability Assessment, Gaps Ledger and Input Module Register tables, 7-8 columns each (shot CP-5_s-241.png full height)
   - Problem: Each register is 7-8 narrow columns of 3-7-line wrapped fragments, followed by eight more such tables. The appendix reads as a wall of grids with no lead-in sentence saying what each register shows.
   - Fix: Add a one-line lead-in per register and merge or drop low-value columns (e.g. Risk Mechanic vs Credit Implication) so cells wrap less.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 66-70 · verdict **CONCERNS**

- Narrative: The passage meets the house standard on placement and order: it follows Key findings, comes before Limitations, and keeps its sources off the page. However, \"consuming handoff\" and \"the run\" leak pipeline vocabulary, it argues report quality more than credit, it buries the one credit trigger at the end, and it reads as a single 190-word block.
- Visual: The section has no chart. It is one paragraph in a readable column of about 75 characters, followed by clear heading spacing. The only typographic problem is the bold monospace \"0.05x\" chip, the single way into the inspector.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: line 68: "the leverage drift is 0.05x, and every consuming handoff states its legal and market limitations openly"; also "The strongest case that the run is already committee-ready" and "the run adopted a single debt basis"
   - Problem: "handoff" and "consuming" are pipeline vocabulary the house standard bans, and "the run" names the workflow, not the issuer or its credit case. They are printed on screen (shot CP-5_contrary-evidence.png, paragraph at y~270-560), so the reader is asked to judge the pipeline instead of TransDigm's credit.
   - Fix: Say "every section of this report that uses these figures states its legal and market limitations", and say "this analysis" or "the report" instead of "the run".
2. **Medium · narrative** (Saboteur)
   - Where: line 68: "On that reading, the material findings are disclosure rather than substance and a Pass would be defensible. That case would win if the forward model and downside pathway reworded their payout-route statements as house-basis indicators"
   - Problem: Most of the passage argues that the report itself could be upgraded through internal rewording and a choice of debt basis. The one trigger that bears on credit, restricted-payment or priming capacity in the executed documents, comes last. A committee could read "a Pass would be defensible" as near-clearance, although the bottom line restricts use.
   - Fix: Lead with the credit-relevant trigger (what the executed documents could show about payout and priming capacity), then give the report-quality remedies as secondary.
3. **Medium · narrative** (New reader)
   - Where: line 68: whole passage, one paragraph of about 190 words, from "The strongest case that the run is already committee-ready" to "misread of creditor rights."
   - Problem: The contrary case, two routes to clearance and the downside trigger are packed into one 14-line block with sentences of up to 50 words. The reader cannot pick out what would improve the view and what would worsen it.
   - Fix: Split it into three short paragraphs: the contrary case, what would lift the restriction, and what would worsen the view.
4. **Medium · narrative** (New reader)
   - Where: line 68: "reworded their payout-route statements as house-basis indicators", "the extraction sizing and the secured-over-subordinated lean", "a Pass would be defensible", "leverage drift is 0.05x"
   - Problem: Several terms are not defined in this section: "house-basis indicators", "extraction sizing", "secured-over-subordinated lean", the grade "Pass" and "leverage drift" (the 6.01x gross versus 5.96x carrying-value gap). The reader must go back to Key findings to decode them.
   - Fix: Use plain words: "the 0.05x gap between leverage on gross debt (6.01x) and on balance-sheet debt (5.96x)", "the preference for secured over subordinated notes", "how much more debt-funded payout is possible".
5. **Low · narrative** (New reader)
   - Where: line 68: "together those clear two of the four material issues, ... would clear the other two"
   - Problem: "The four material issues" are listed only in the Bottom line, so here the reader has to count against another passage to see which remedy clears which issue.
   - Fix: Name the issues inline, briefly: "the legal-capacity overstatement and the two leverage bases", then "the missing legal documents and market levels".
6. **Low · visual** (Auditor)
   - Where: CP-5_contrary-evidence.png, crop CP-5-160-a.png, line 3 of the paragraph: "0.05x" chip
   - Problem: The only clickable figure appears in bold monospace with a dotted underline, so it stands out against the body text. It is also the only way into the paragraph's Basis items (filing pages 34–173, calculation V04), most of which have nothing to do with 0.05x.
   - Fix: Use body-weight type for the inline figure. Because the paragraph's sources go well beyond that one figure, also give it the quiet "Basis" link.

### Limitations

Kind: reader passage · handoff lines 71-77 · verdict **CONCERNS**

- Narrative: The section is in the house order: it comes after contrary evidence and before the appendix material, and it carries no source references in the prose. But every bullet is written in pipeline language about the module's own process, not as a caveat a credit committee can use, and the most decision-relevant gap is not first.
- Visual: The section has no chart, map or timeline of its own (the Maps panel below belongs to the next section). The plain bullet list renders cleanly and legibly, with nothing clipped or overlapping, but it is a dense, uniform text block with no scan aids and a narrow measure.

1. **High · narrative** (Auditor, New reader (promoted from Medium))
   - Where: L74 "this module cannot test whether the filing's own summary..."; L75 "traced only to the fact pack's page citations; their lineage is accepted as upstream-sourced"; L76 "The scoring script was not run"
   - Problem: The limitations are written as notes about the pipeline, not as credit caveats. They use "this module", "fact pack", "upstream-sourced", "lineage", "scoring script" and the taxonomy labels "Calculated classification" and "directly sourced", and the house standard says this vocabulary is not reader language. A committee member cannot tell what the caveat means for the credit.
   - Fix: Restate each limitation as what remains unverified about TDG and what that means for the view, without naming tools, modules or classification labels.
2. **Medium · narrative** (Saboteur)
   - Where: L73 "the stress, hedge and forecast arithmetic is accepted on its own self-checks, so the Calculated classification of those secondary figures is assumed rather than proven"
   - Problem: The bullet does not name which committee-facing numbers are unverified. Examples are the 15% and 31% stress EBITDA declines, the USD 57.89 million rate sensitivity and the FY2025-FY2027 forecast paths. A reader could rely on the downside and forecast figures as checked as firmly as the drivers in the Bottom line, which "re-perform exactly".
   - Fix: Name the unverified figure families (stress scenarios, hedge sensitivity, forecast paths) so the reader knows which numbers carry only the producing analysis's own check.
3. **Medium · narrative** (New reader)
   - Where: L74 "whether the filing's own summary of the 7.25x, 5.00x and 7.50x thresholds is accurate"
   - Problem: The bullet lists three multiples with no metric or purpose. It does not say they are the net leverage and secured net leverage tests for incremental debt and the springing revolver test, so a reader who has not seen the covenant section cannot tell what is untested.
   - Fix: Give each threshold its metric and what it governs, in a few words, the first time it appears.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: L76 "the zero confidence score is a hand application of the published formula; a different penalty treatment could move the band"
   - Problem: The bullet admits an internal score could change, but it does not say what the score measures, what band it might move to, or whether that matters to the decision. That adds doubt without telling the reader how to act on it. It is a tooling caveat, not a limitation on the TDG view.
   - Fix: Either drop the bullet from the reader view or state in one plain sentence that the clearance (restricted use) does not depend on the score.
5. **Low · narrative** (Saboteur)
   - Where: L75 "the post-period buyback and liquidity figures are traced only to the fact pack's page citations"
   - Problem: The bullet gives no figures and no period. The USD 316 million of buybacks and the USD 3,308 million of liquidity at 2024-12-28 are not stated, so the reader cannot see which liquidity numbers carry the weaker verification.
   - Fix: Name the affected figures with their unit and date, for example liquidity at 2024-12-28.
6. **Low · narrative** (Saboteur)
   - Where: L73-L76 bullet order, starting "Re-performance covered the inputs..."
   - Problem: The bullets are not ranked by credit consequence. The decision-relevant gap (no executed debt documents, so payout and priming capacity cannot be sized) comes second, behind a scope note on arithmetic. Each bullet is one 45-60-word sentence that joins three clauses with semicolons and "so".
   - Fix: Lead with the legal-documents gap and split each bullet into a short claim followed by its consequence.
7. **Low · visual** (New reader, Auditor)
   - Where: Limitations block, CP-5_limitations.png, crop region x 320-1440, y 200-620 (tmp/CP-5-161-a.png)
   - Problem: Four bullets of 3-4 lines each in the same weight form a grey wall with no bold lead phrase to scan. The text column stops at about 60% of the content width, which leaves a wide empty band on the right.
   - Fix: Give each bullet a short bold lead-in naming the gap (for example "Debt documents not provided") so a reader can scan the block.

### Overall traceability view

Kind: prose/table · handoff lines 136-139 · verdict **CONCERNS**

- Narrative: This is a one-paragraph summary (L136-139). It contradicts the grades printed around it (Ready with Limitations, Pass with Remediation, 0/100 Insufficient Information), repeats the earlier Traceability conclusion, and opens with taxonomy counts and labels instead of the credit consequence.
- Visual: The section has no chart, map or table, only one dense paragraph. It is laid out cleanly, but it sits at the edge of method material ('QA validation', 'a method step Source Register'), and the left nav shows it as a near-duplicate of 'Traceability conclusion'.

1. **High · narrative** (Saboteur, Auditor)
   - Where: L138 "Overall, evidence traceability is Ready with Remediation." against L110 "Module Status: Ready with Limitations", L132 "CLEARANCE DECISION: Pass with Remediation" and L144 "Confidence Score: 0 / 100 (Band: Insufficient Information)"
   - Problem: The page gives four different headline grades within about ten lines. Directly below this section the reader sees a 0/100 'Insufficient Information' score, so 'Ready' and 'Insufficient' contradict each other with no reconciliation, and a committee member cannot tell which grade governs. Promoted from Medium because two personas caught it.
   - Fix: Use one reader-facing grade, worded the same everywhere, and say in a single clause why the confidence score clamps to zero although the figures re-perform.
2. **Medium · narrative** (New reader)
   - Where: L138 "Of the Top 5 material credit drivers, 2 are directly sourced, 2 are calculated, 0 are assumption-based, 0 are analyst inferences, and 1 are weak-lineage, untraced, conflicting, or insufficient-information items."
   - Problem: The sentence lists method taxonomy counts, including empty categories, in internal class labels. It has a grammar slip ('1 are') and uses 'Top 5' as a scope code. The one item that matters, covenant and payout capacity with no supporting document, is never named.
   - Fix: Name the one untraced driver (covenant and payout capacity), state that the other four trace to the filing or re-performed calculations, and drop the zero categories.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: L138 "The most important provenance gap is the absence of the executed credit agreement and indentures. It matters because restricted-payment and incremental-debt capacity determine..." (it repeats L96 'Traceability conclusion')
   - Problem: This paragraph restates the 'Traceability conclusion' at L96 almost word for word, and it sits after the clearance decision, deep in the method material. The reader meets the same judgement twice, and the late copy uses a different grade label.
   - Fix: Remove this section or merge it into the Traceability conclusion so the judgement appears once, near the top.
4. **Medium · visual** (Auditor, New reader)
   - Where: Screenshot CP-5_s-136.png, the section block (y about 190-280 in the downsized view) and the page around it
   - Problem: The section is one dense four-line paragraph. Right below it the page runs into 'QA validation', which names script filenames, and a table titled 'a method step Source Register'. The visual run from this conclusion into pipeline material gives the reader no break or cue that the analysis has ended. The left nav also lists this heading next to 'Traceability conclusion', which looks like a duplicate entry.
   - Fix: Show the judgement once as a short, separated paragraph, and visually set the method appendix that follows apart from the reader content (or fold it away).
5. **Low · narrative** (Auditor)
   - Where: L138 "evidence traceability is Ready with Remediation" ... "with Restricted use"
   - Problem: The paragraph opens with a status label (judgement by category) instead of the credit consequence. The consequence the reader needs, that the extraction thesis is directional and conduct-based only, comes in the last sentence.
   - Fix: Lead with the consequence: the extraction thesis can go to committee only as a directional, conduct-based view; then give the reason.

### Calculations

Kind: prose/table · handoff lines 337-362 · verdict **BLOCK**

- Narrative: This is a data/calculations section, so no prose order is owed. The arithmetic checks out (V04, V07, V11 and V17 were re-added by hand). The section's problems are pipeline vocabulary on screen, a payout mislabelled 'September' against an October date, and an unreconciled 749 between the maturity schedule and gross debt.
- Visual: The table is legible at 1440 px and nothing is clipped. The Result column's formatting is inconsistent: ten decimals, missing thousands separators, bolding with no stated meaning and percentages under the unit 'fraction'. A 'Basis' label also appears under only some row IDs.

1. **High · narrative** (Auditor, New reader)
   - Where: L339 "All arithmetic used the calculate tool."; L361 "Helper scripts (`prepare_invocation.py`, `validate_handoff.py`, `confidence_score.py`, `completeness_check.py`) were not run in this transport"; L357 "upstream handoffs, entity key, absorbed QA phase"; L359 "qa_status Restricted"
   - Problem: Tool, script, transport, handoff, gate and field-name vocabulary reaches the reader on screen, which breaks the house rule that keeps pipeline wording out of the report. A portfolio manager cannot act on any of it.
   - Fix: Remove the tool and script sentences and describe V15 to V17 in reader terms, for example 'evidence completeness' and 'clearance: Restricted'.
2. **Medium · narrative** (Saboteur)
   - Where: L353 "V11 | Maturity schedule sum | 93 + 92 + 92 + 6,637 + 4,768 + 12,637 (page 153) | 24319 (USD 24,319 million)" against L343 gross 25,068 and L345 carrying 24,880
   - Problem: The table gives three different debt totals (25,068, 24,880 and 24,319). Only the 188 gross-to-carrying gap is reconciled (V05). The 749 between the maturity sum and gross debt is never explained, so a reader cannot tell whether the maturity schedule is missing debt.
   - Fix: Add a row or a one-line note that reconciles the maturity schedule total to gross total debt, or name what it excludes.
3. **Medium · narrative** (Saboteur)
   - Where: L350 "Dividend + dividend equivalents paid 2024-10-18"; L351 "October payout / FY2024 FCF"; L352 "Concurrent secured issue / September payout | 3,000 / 4,348"
   - Problem: V10 calls the same USD 4,348 million payout the 'September payout', while V08 and V09 date it to October (2024-10-18, after the 30 September as-of date). This leaves the reader unsure whether there were one or two distributions and whether it came before or after the balance-sheet date.
   - Fix: Use one label and date for the payout throughout, and mark it as a post-period event.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: L359 "-11.5147826087 (-11.51), clamped to 0; band Insufficient Information; qa_status Restricted"
   - Problem: The module's clearance outcome (a confidence score of 0, 'Insufficient Information') sits in the last cell of a 17-row arithmetic table, with an undefined penalty 'P = 4 × 15 + 3 × 3'. The reader is not told what the 15 and 3 weights or the 0.7 'partial' S stand for.
   - Fix: Name the score's components (E, C, S, P) in words once above the table and point the reader to where the clearance judgement is stated.
5. **Medium · narrative** (New reader)
   - Where: L339 "(0.42 × 76 = 31.92 is exact by hand; S × 0.4 × C used 588 / 23)"; L344 "(CP-1 C10; page 63)"; L351 "(CP-1 C15)"
   - Problem: The intro's aside is cryptic: 0.42 = 0.6 × 0.7 and 588/23 are never explained. Upstream register codes (C10, C15) are shown on screen as 'Financial foundation C10', and 'Pro forma net debt' does not say pro forma for what.
   - Fix: Drop the by-hand aside, cite the upstream figure by name instead of register code, and state the pro forma basis of the 23,155.
6. **Medium · visual** (New reader, Auditor)
   - Where: Calculations table, CP-5_s-337.png, Result column (approx. x 870-1090, y 480-1350 in the 1200-px view; crop CP-5-171-a.png)
   - Problem: The Result column mixes ten-decimal raw values ('6.0071890726'), unseparated integers ('24880', '4348'), restated values ('USD 19,702 million') and percentages under the unit 'fraction'. '188' and '-7' alone are set in bold with no meaning attached, and '-7' uses a hyphen where the inputs use a true minus.
   - Fix: Show one rounded, thousands-separated value per row in the stated unit, with no unexplained bold and with consistent minus signs.
7. **Low · visual** (Auditor)
   - Where: Calculations table ID column, CP-5_s-337.png, e.g. 'V01 Basis', 'V06 Basis', 'V10 Basis' versus bare 'V04', 'V05', 'V09', 'V14'-'V17' (crop CP-5-171-a.png)
   - Problem: A grey 'Basis' label sits under some row IDs and not others, with no visible content or explanation, so it reads as stray chrome inside a data table.
   - Fix: Either render the basis as a visible column or affordance applied to every row, or remove the label from the ID cell.

## Changes since the last run (CP-8)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002/requests/CP-8/ad48310b6570654572ef68b17d8e4432de761c74b3124d457354b995caf61c65/1.response.md`

### Limitations ledger

Kind: prose/table · handoff lines 95-138 · verdict **CONCERNS**

- Narrative: The ledger is complete: all 43 current references and all 11 earlier references appear exactly once. But its count contradicts the key findings (six remaining, not seven), its 'No longer stated' rows look as if the limitations were resolved, and several rows use pipeline vocabulary instead of credit language, all in a 40-row table with no lead judgement.
- Visual: The table renders cleanly and readably, but a stray 'Basis' chip in the Earlier ref column wraps and misaligns rows, and a mostly empty 'What closed it' column takes width from the limitation text, so the table runs past two screens.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Ledger lines 99-109: six rows are 'Remaining' (E1, E2, E5, E7, E8, E10). Key findings line 52 says 'seven earlier limitations carry over in meaning, one closed when the stress work was done, and four are simply no longer stated'
   - Problem: The ledger shows 6 earlier limitations remaining, 1 closed and 4 no longer stated, which is 11 in total. The key finding on the same page says seven carry over. A committee member who checks the count gets two different numbers for the same set.
   - Fix: The key-findings count should match the ledger's Status column exactly: six remaining, one closed, four no longer stated.
2. **High · narrative** (Saboteur, New reader)
   - Where: line 109: 'E11 | — | Open quality findings on the leverage basis and a disputed confidence grade limit what the committee can treat as settled. | No longer stated | —' (also E3 line 101)
   - Problem: 'No longer stated', with a dash under 'What closed it', reads as if the limitation went away. Yet the contrary-evidence passage (line 57) says the evidence trace still finds modules overstating effects 'under remediation'. E3, the exclusion of acquisitions from internal-control testing, is a fact from the filing that the later run cannot have cured. The reader may treat live caveats as resolved.
   - Fix: For each 'No longer stated' row, say whether the limitation still applies (for example 'Still applies, not restated' or 'Superseded by Cx') rather than leaving the reader to infer it closed.
3. **High · narrative** (Auditor, New reader)
   - Where: line 107: 'Required-field contracts for earlier producers are absent, so upstream confidence scores cannot be re-graded comparably.'; line 135: 'The trace's confidence score was applied by hand without the scoring script.'
   - Problem: These rows use pipeline language ('required-field contracts', 'producers', 'upstream', 'scoring script'), which the house standard bars from reader text. A portfolio manager cannot tell what limitation on the credit view these rows describe. E6 ('governing factor weights... composite score and credit tier', line 104) and C8 ('one evidence family', line 115) are similar.
   - Fix: Restate each in credit terms (what the reader cannot rely on and why), or move process-only limitations out of the reader ledger into a methods note.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: lines 97-137: 40 rows, keyed 'Earlier ref'/'Current ref' as 'E1'...'E11' and 'C1'...'C43'
   - Problem: The section opens straight into a 40-row table with no lead sentence. The rows are in reference-number order, not by importance to the credit, so the material limitations (no executed documents C36/C40, no market levels E5, no ratings C43) sit among process caveats. The E/C codes are defined nowhere on the page, so the reader cannot use them.
   - Fix: Open with one sentence giving the judgement on what the limitation changes mean, and group or order the rows by credit materiality, with the reference codes de-emphasised or explained.
5. **Medium · visual** (New reader, Auditor)
   - Where: Limitations ledger table, CP-8_s-95.png, Earlier ref column (crop CP-8-181-a.png, x 340-460): 'E1 Basis', 'E10 / Basis' wrapped, '— Basis' on every new row
   - Problem: Every row has an unexplained 'Basis' chip next to the earlier reference, including rows with no earlier reference ('— Basis'). It wraps to a second line for E10 and E11, which breaks the column's alignment. The Current ref column has no chip, so the reader cannot tell what 'Basis' links to or why it sits there.
   - Fix: Show a source link only where a row has a source and label it plainly, or put it in its own Source column so the ref columns stay one line and aligned.
6. **Low · narrative** (Auditor)
   - Where: line 102: 'CP-2A: its static stress shows free cash flow before distributions reaching zero only after a 45.05% fall'
   - Problem: The handoff cell starts with a module code. The page renders it as 'Downside:', so no code reaches the screen, but the closure cites its source in the narrative cell rather than in a Source column, contrary to the standard's placement rule.
   - Fix: Put the closing module or source in a Source column and keep the cell to the finding.
7. **Low · visual** (Auditor)
   - Where: Limitations ledger table, CP-8_s-95.png, 'What closed it' column (x ~1030-1390)
   - Problem: The widest column on the right is a dash in 39 of 40 rows; only E4 fills it. Meanwhile the Limitation text is squeezed into about 300 px and wraps to three lines, which makes the table longer than two screens.
   - Fix: Narrow or collapse 'What closed it' (for example fold the closing note into the Status cell) so the limitation text gets the width.

### Sources

Kind: prose/table · handoff lines 5-28 · verdict **BLOCK**

- Narrative: The Sources section (lines 5-27) lists only internal artifacts: hashes, the comparison file and the earlier run's financial foundation. It is written in pipeline vocabulary, does not name the earlier run being compared, and buries a material scope limit in its last sentence.
- Visual: Both Sources tables are clean and legible, without clipping, but the 64-character hash columns dominate the width and push the useful text into narrow wraps. The section sits mid-page, ahead of the comparison tables, where it delays the reader.

1. **High · narrative** (Auditor, New reader)
   - Where: line 12 table header "| Supplied handoff | Module | sha256 |"; line 10 "prior/CP-1.md ... read to resolve the pack's definition pointers" (rendered "prior/Financial foundation handoff"); line 27 "issuer facts reach it only through the pack and the handoffs of both runs"
   - Problem: Pipeline words the house standard bans ("handoff", "pack", "definition pointers", "this module") are shown to the reader in a column header, a source name and the closing sentence. Because two personas caught it, it moves up from Medium to High.
   - Fix: Name each source in reader terms (for example "Earlier run, financial foundation section" and "Run comparison data") and rewrite line 27 without pipeline words.
2. **Medium · narrative** (Saboteur)
   - Where: line 9 "changes.json ... Comparison pack (cpos-changes/2)"; line 10 "prior/CP-1.md"; lines 12-25 table of 12 supplied handoffs
   - Problem: The Sources list never names the earlier run this page is compared against (tdg-reader-format-001 and its run date appear only in the Request, line 3). It also does not say that the 12 hashed sources are the current run's. A committee reader cannot tell from the Sources section which two runs were compared, or whether they are the latest.
   - Fix: In each source row, name the run it comes from: the earlier run with its id and run date, and the current run.
3. **Medium · narrative** (New reader)
   - Where: line 10 "calculations C01 to C04 and C06 read to resolve the pack's definition pointers for leverage, coverage and undrawn facilities"; line 9 "earlier and current limitation refs"
   - Problem: The reader is given internal calculation IDs, a schema version ("cpos-changes/2") and "refs" with no definitions, and has to open another module to decode them.
   - Fix: State which measures were taken from the earlier run (leverage, interest cover, undrawn facilities) and drop the internal IDs and the schema tag.
4. **Medium · narrative** (Saboteur)
   - Where: line 27 "No issuer filing was read by this module ... The other earlier-run handoffs were not opened because the pack's bottom lines and limitation texts were sufficient."
   - Problem: This scope limit decides how far the comparison can be relied on: it says that only one of the earlier run's sections was actually read. It is buried as a trailing sentence under a hash table rather than stated in Limitations.
   - Fix: Move the statement that only the earlier run's financial foundation was read into the Limitations passage, in plain wording, and leave the Sources section as a list of sources.
5. **Medium · visual** (New reader, Auditor)
   - Where: Sources tables, shot CP-8_s-5.png, crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-8-174-a.png (y 220-1040)
   - Problem: The 64-character sha256 strings take about 40-45% of each table's width, set in the proportional body font. In the first table this squeezes "Use in this module" into three-line wraps. Hashes carry no meaning for a portfolio manager and dominate the section visually.
   - Fix: Truncate the hash, or hide it behind a tooltip or monospace detail chip, so the source name and its use carry the table.
6. **Medium · visual** (Auditor)
   - Where: "On this page" navigation and page flow in CP-8_s-5.png: Limitations, Request, Sources, then What changed: the issuer
   - Problem: The Sources and Request blocks are placed between the judgement passages and the core comparison tables. The reader therefore passes about 700 px of hash tables before reaching "What changed: the issuer". The house order puts sources in the closing reference position, not in the middle of the findings.
   - Fix: Render Sources after the comparison tables and the ledger, at the end of the module, as the ruling's reading order expects.
7. **Low · visual** (New reader)
   - Where: Supplied handoff table, CP-8_s-5.png, e.g. row "Financial data foundation | Financial foundation", "Investment committee debate | Committee decision"
   - Problem: The first two columns repeat the same module under two different names, and the labels differ from those used elsewhere in the section. This adds width without adding information, and the second name for each module is never explained.
   - Fix: Keep one column, using the sidebar display name.
8. **Low · visual** (Auditor)
   - Where: First Sources table, row 2, "calculations C01 to C04 and C06" rendered as inline code chips (crop CP-8-174-a.png, y≈175-195)
   - Problem: Internal IDs are styled as monospace chips, which draws attention to tokens the reader cannot use, inside an otherwise plain-text cell.
   - Fix: Remove the IDs, or render them as plain text if they must remain.

### Bottom line

Kind: reader passage · handoff lines 31-37 · verdict **BLOCK**

- Narrative: The bottom line opens with a judgement as the standard requires. It then says liquidity did not move, which the module's own findings say cannot be inferred, and it leaves out the Watchlist relabel and the harsher wording that a committee would want to see at the top.
- Visual: This section has no chart, map or timeline. The bottom line runs about 130 words in bold display type, shows no Basis chip for its sources, and switches inline figures to a lighter monospace face.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Line 35: "The only measure that differs, undrawn committed facilities, differs because ... so it is not comparable and implies no movement in the issuer's liquidity."
   - Problem: The sentence says the figures are not comparable and then concludes there is no movement in liquidity. Figures on different definitions support no conclusion either way. The module's own Key findings (line 49, "no change in committed liquidity can be inferred") and Limitations (line 65, liquidity-unchanged "rests on the cash balance only, not on committed headroom") both say this. So the bottom line claims more than the analysis supports, and a committee would read committed headroom as confirmed stable.
   - Fix: State that the two undrawn figures (843 vs 1006 US$m) cannot be compared, so this comparison cannot say whether committed headroom moved; only the cash balance is unchanged.
2. **Medium · narrative** (Saboteur)
   - Where: Line 33: "About the same: the credit picture for TransDigm has not changed ... none of them overturns the earlier conclusions."
   - Problem: The bottom line leaves out what changed that a committee would act on. The committee stance is now labelled Watchlist (line 46). The financial policy is now called "deliberately aggressive and high risk" (line 57). The evidence check found two of the new modules overstated the effect on distributions (line 57). A reader of the bottom line alone gets a clean "same credit" with nothing qualifying it.
   - Fix: Add one clause to the bottom line naming the Watchlist label and the harsher policy wording, and saying why they do not change the conclusion.
3. **Medium · narrative** (New reader, Auditor)
   - Where: Line 33: "every difference between them is the analysis's, not the issuer's ... the four modules added this time quantify the downside, hedging and forward path that the earlier run could only describe"
   - Problem: The judgement is framed in pipeline terms ("runs", "the analysis's", "four modules added this time") and never names the four new analyses. A portfolio manager has to go to Key findings to learn what was added.
   - Fix: Name the added work in reader terms (downside stress, rates/FX and hedging, forward model, deep research) and refer to the earlier review by its date, not as a "run".
4. **Medium · narrative** (New reader, Saboteur)
   - Where: Line 35: "total debt at 6.01x EBITDA As Defined, net debt at 4.51x and cash interest cover at 3.60x"
   - Problem: The ratios have no period or date in the bottom line (only "the same date"), and "EBITDA As Defined" is the issuer's covenant-style adjusted measure, which is never explained to a reader who has not read the filings.
   - Fix: Anchor the ratios to FY2024 (30 September 2024) and gloss EBITDA As Defined in a few words the first time it appears.
5. **Medium · visual** (Auditor)
   - Where: Screenshot CP-8_bottom-line.png, region x 320-1440, y 200-800 (crop CP-8-175-a.png): area below the second bottom-line paragraph
   - Problem: The handoff's bottom-line Basis line (line 36: "Basis: changes.json; prior/CP-1.md, page 4") does not appear on screen. No Basis chip follows either paragraph, so the page's headline claim shows no source. Under the house standard, references belong in the Basis line.
   - Fix: Show the bottom line's Basis chip after the bottom-line block, as the Key findings bullets do.
6. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-8_bottom-line.png, y ~230-770: two bottom-line paragraphs set in large bold display type
   - Problem: About 130 words over two paragraphs are all set in the large bold lede style, about 25 lines in a narrow column. The judgement ("About the same") does not stand out from supporting detail, and the block reads as a wall of headline text.
   - Fix: Keep only the first judgement sentence or paragraph in display type and set the supporting second paragraph in body type.
7. **Low · narrative** (New reader)
   - Where: Line 33: "Creditors should read this run as the same credit, low business risk with leverage set by debt-funded distributions, examined more deeply: the four modules ..."
   - Problem: The 60-word sentence chains three ideas with a comma splice and a colon, so the reader has to parse it twice.
   - Fix: Split it into a short judgement sentence and a separate sentence on what the new work added.
8. **Low · visual** (Auditor)
   - Where: Screenshot CP-8_bottom-line.png crop CP-8-175-a.png, line "total debt at 6.01x EBITDA As Defined, net debt at 4.51x and cash interest cover at 3.60x"
   - Problem: Figures inside the bold lede switch to a lighter monospace face with a dotted underline. This breaks the line's weight and rhythm and makes the numbers look lighter than the surrounding text.
   - Fix: Render inline figures in the lede at the lede's weight (tabular numerals) and keep the dotted underline as the only marker.

### Key findings

Kind: reader passage · handoff lines 38-54 · verdict **BLOCK**

- Narrative: The section puts its judgement first, but it is written in the tool's own vocabulary ("pack", "modules", "calculation pointers"), and it waves off two possible negatives, the Watchlist move and the dropped internal-control caveat, as neutral.
- Visual: There is no chart in this section; the bullet layout is clean, but bullets 1 and 2 have lost their Basis chips, and the narrow column and monospace figure chips are minor polish issues.

1. **High · narrative** (Auditor, New reader (promoted from Medium))
   - Where: L40 "under definitions that match once the earlier run's calculation pointers are followed, and the pack shows no fact, refinancing or rating action"; L46 "Every module that ran both times reached the same credit conclusion... the legal module is still blocked"; L52 "Most current limitations belong to the four new modules"
   - Problem: The findings are written in the tool's own vocabulary ("the pack", "calculation pointers", "module", "legal module", "stress work"). A committee member who does not know the pipeline cannot tell what "the pack" is or which analyses "modules" are, and the house standard keeps pipeline wording off the page.
   - Fix: Name the analyses the way a reader knows them (legal and covenant review, downside case, committee view) and say "the comparison of the two runs" instead of "the pack" or "calculation pointers".
2. **Medium · narrative** (Saboteur)
   - Where: L46 "the committee's stance is now labelled Watchlist where the earlier run said requires more work, which is a change of label with the same consequence for capital."
   - Problem: A move to Watchlist is waved off as a relabel inside a finding that says nothing changed. The next section (L57) admits a reader could take it as a weakening, so the page plays down a possible negative signal before it argues the case.
   - Fix: State the Watchlist move as a finding of its own, with the reason it is or is not a weaker stance, instead of folding it into the same-conclusion bullet.
3. **Medium · narrative** (Saboteur)
   - Where: L52 "four are simply no longer stated, including the earlier run's note that internal-control testing excluded the recent acquisitions."
   - Problem: The bullet's lead says limitations grew "rather than because evidence got worse", but its last clause reports that a control-testing caveat disappeared without explanation. A reader may take the caveat as resolved when no one has said so, which is the unresolved difference this section should explain.
   - Fix: Say whether each dropped limitation was resolved or only left out, and keep the internal-control caveat as open unless the evidence closes it.
4. **Medium · visual** (Auditor)
   - Where: Key findings bullets 1 and 2, shots2/CP-8_key-findings.png crop (330,220)-(1060,900), saved as tmp/CP-8-176-a.png
   - Problem: Bullets 3 to 5 end with a "Basis" chip, but bullets 1 and 2 show none, even though the handoff has Basis lines for them at L41 and L44. The two bullets that carry the numbers (6.01x, 4.51x, 3.60x, 45.05%) look unsourced on the page.
   - Fix: Render a Basis chip on every bullet that has a Basis line, including bullets with linked figures.
5. **Low · narrative** (New reader)
   - Where: L40 "leverage of 6.01x, net leverage of 4.51x and cover of 3.60x carry a difference of zero"
   - Problem: This bullet gives the ratios without their denominator or period. Only the Bottom line above names EBITDA As Defined and FY2024, and the bullet mostly repeats that Bottom line paragraph.
   - Fix: Attach the basis (EBITDA As Defined, FY2024) to the figures or drop the restated numbers and lead with the consequence.
6. **Low · narrative** (New reader)
   - Where: L43 "putting free cash flow before distributions at zero only after a 45.05% fall in EBITDA As Defined, which confirms rather than alters the earlier view"
   - Problem: The bullets run 60 to 80 words, with semicolon chains, and quote a stress threshold to two decimals. That is heavy going on a page about changes and gives the figure more precision than it supports.
   - Fix: Split each bullet into a judgement sentence and one supporting sentence, and round the stress threshold to about 45%.
7. **Low · visual** (Auditor)
   - Where: Key findings block, shots2/CP-8_key-findings.png, prose column at x about 300-840 (display) against a content area running to about 1160
   - Problem: The text column fills about half the content width, leaving a wide empty band on the right. The linked figures switch to a bold monospace face with a dotted underline in the middle of sentences, which breaks the line rhythm.
   - Fix: Use the same figure styling as the September VMO2 reference (proportional numerals, a subtle link cue) and check whether the column width matches it.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 55-59 · verdict **BLOCK**

- Narrative: The paragraph does argue a contrary case and rebut it, but it hides the key contrary number (5.55x pro forma net leverage against the 4.51x shown everywhere else on the page), leaves the admitted overstatement unresolved, uses workflow vocabulary, and gives no concrete, directional triggers for what would change the view.
- Visual: There is no chart in this section; visually it is one dense 12-line text block with a faint inline Basis chip, followed on the page by provenance and hash tables that push the comparison tables down.

1. **High · narrative** (Saboteur, New reader)
   - Where: L57: "the financial foundation now headlines net leverage pro forma for the October 2024 dividend rather than the reported figure"
   - Problem: The headline figure in the current run is 5.55x (CP-1 handoff L22/L134), but this passage never gives it. On the same page the bottom line and the issuer table say net leverage is an identical 4.51x in both runs. A committee member sees 'unchanged 4.51x' while the current run's own headline is about one turn higher, and the passage does not show the gap.
   - Fix: State the pro forma figure with its basis and date (5.55x, net of the USD 4,216m special dividend paid 2024-10-18) next to the reported 4.51x, so the reader can see what 'headlines' means in numbers.
2. **Medium · narrative** (Saboteur)
   - Where: L57: "The evidence trace also found that two of the new modules overstated what the incurrence level does to distributions, so part of the added depth is itself under remediation."
   - Problem: This admits that two of the new analyses contain a known overstatement, but the 'Against that' rebuttal only answers the wording point. It never says whether the overstatement affects the bottom line's claim that the new modules 'confirm' the earlier view. The caveat is left hanging, and the reader cannot tell which conclusions to discount.
   - Fix: Name the two analyses, say which direction the overstatement runs, and state whether the bottom line still holds without them.
3. **Medium · narrative** (New reader, Auditor)
   - Where: L57: "part of the added depth is itself under remediation"; "the incurrence level"; "The comparison would show a real change only with a later run"
   - Problem: 'Under remediation', 'run', 'comparison' and 'evidence trace' are workflow vocabulary, not credit language. 'Incurrence level' is undefined debt-document jargon that a reader without the sources cannot decode.
   - Fix: Use reader terms, such as 'flagged as wrong and being corrected' and 'the debt-incurrence test in the indentures (the leverage level below which new debt is permitted)', and describe the next review rather than the next run.
4. **Medium · narrative** (Saboteur, Auditor)
   - Where: L57: "or with the executed debt documents or market levels that both runs lack, which could move the legal, relative-value and committee conclusions."
   - Problem: The 'what would change the view' half has no direction or trigger. It says what inputs are missing, but not what finding in them would make the credit view better or worse, such as a debt-incurrence capacity size, a spread level or an EBITDA drop. As written it cannot act as a watch trigger.
   - Fix: Give one or two concrete triggers with direction, for example a first-quarter FY2025 net leverage above X, or documents showing payment capacity of Y, and say what each would do to the view.
5. **Medium · narrative** (New reader)
   - Where: L57: the entire passage, one paragraph of about 210 words beginning "The strongest case that the view has in fact moved..."
   - Problem: Three jobs (the contrary case, the rebuttal, and what would change the view) are packed into a single 12-line block on screen. The section heading promises two parts, but the reader cannot find where 'what would change the view' starts.
   - Fix: Split into a contrary-evidence paragraph and a separate short 'What would change the view' paragraph or bullets, each with its own Basis.
6. **Low · visual** (Auditor)
   - Where: CP-8_contrary-evidence.png, crop CP-8-177-a.png (x 340-1100, y 220-580): grey 'Basis' chip at the end of the paragraph
   - Problem: The only source pointer is a small, low-contrast grey word glued to the last line of a dense block. It is easy to miss, and because it is a single chip the reader cannot tell which of the three cited sources supports which claim.
   - Fix: Render the Basis on its own line below the paragraph at readable contrast, which splitting the paragraph would also make one Basis per claim group.
7. **Low · visual** (New reader)
   - Where: CP-8_contrary-evidence.png, y 180-480 (section) followed by Request/Sources at y 750-1500
   - Problem: After this section and Limitations, the page drops straight into Request and a sha256 hash table before the 'What changed' tables. The reader must scroll past pipeline provenance to reach the evidence this passage argues from.
   - Fix: Keep the 'What changed' tables directly after the narrative, and move Request and the hash tables to the end or into a fold.

### What changed: the issuer

Kind: prose/table · handoff lines 67-77 · verdict **CONCERNS**

- Narrative: The table puts the key judgement in the Effect column (nothing changed at the issuer, and the undrawn figure is a definition difference), but the Cause column ('Unresolved' on every row) and the mixed period labels contradict that judgement on the page.
- Visual: This section has no chart. The table renders cleanly with good contrast, but the unexplained 'Basis' tags, values wrapped by narrow columns and long boilerplate Effect cells bury the one row that differs.

1. **High · narrative** (Saboteur, Auditor)
   - Where: L71-75 Cause column: "Unresolved" on every measure row, e.g. L71 "| 6.01x (FY2024) | 6.01x (FY2024) | Unresolved | Same definition: ... difference 0.00x"
   - Problem: Identical values with matching definitions are labelled 'Unresolved', which reads as an open, unexplained difference. That contradicts the Effect cell in the same row and the bottom line (L33: 'every difference between them is the analysis's'). The only row that actually differs, undrawn facilities (L75), is a definition change that the module itself explains, yet it is also labelled 'Unresolved'.
   - Fix: Label the four identical rows 'No change' and the undrawn-facilities row 'Definition', so the Cause column agrees with the Effect text and the bottom line.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: L75 "neither a new period nor a new source accounts for the two values."
   - Problem: The cell ends by ruling out the comparison's internal cause categories (period, source) instead of stating the cause it already gave: a definition change. A reader takes away 'unexplained' when the explanation is one clause earlier, and the category wording is pipeline vocabulary.
   - Fix: End the cell on the judgement: 'definition change, not a liquidity movement; committed headroom cannot be compared'.
3. **Medium · narrative** (Saboteur)
   - Where: L74 "| Cash | 6261 US$m (2024-09-30) | 6261 US$m (FY2024) |" and L75 "843 US$m (2024-09-30) | 1006 US$m (FY2024)"
   - Problem: In the same row the same date is written two ways, a calendar date for Earlier and a fiscal-year label for Current. This suggests the periods differ when the module says they are identical, and it is most misleading on the one row whose values do differ.
   - Fix: Use one period label, such as 'FY2024 (30 Sep 2024)', in both columns of every row.
4. **Medium · narrative** (New reader)
   - Where: L71-74 repeated "Same definition: ... difference 0.00x at the same date, so there is no issuer change to attribute"
   - Problem: Four 30-50 word cells repeat the same no-change boilerplate, so the one row that matters (undrawn facilities) is buried under identical text. The Effect column becomes a wall of text that the reader has to read through to find the single exception.
   - Fix: Shorten the identical rows to 'Unchanged; same definition' plus any row-specific warning, such as cash flattered by the accrued dividend, and keep the detail for the row that differs.
5. **Medium · visual** (New reader, Auditor)
   - Where: What changed: the issuer table, shots2/CP-8_s-67.png region x350-1400 y220-800 (crop tmp/CP-8-179-a.png): the 'Basis' tag after each row label
   - Problem: Every row label carries an unexplained grey 'Basis' tag that wraps onto its own line under short labels ('Total debt / EBITDA', 'No material change'). The table has no Source column, so the reader cannot tell what 'Basis' points to without clicking.
   - Fix: Give the table a Source column or a labelled source icon, and keep row labels on one line.
6. **Low · narrative** (New reader)
   - Where: L76 "| No material change | — | — | None | No issuer fact (facility, refinancing, disposal, rating action or guidance) differs ..."
   - Problem: A conclusion is placed in the table as a fake measure row with dash values and its own 'Basis' tag. A reader scanning the Measure column may take it for a metric whose data is missing.
   - Fix: Move the no-other-change statement into a one-line note under the table.
7. **Low · visual** (Auditor)
   - Where: Same table, Earlier/Current columns: "6.01x / (FY2024)", "6261 US$m / (2024-09-30)"
   - Problem: The narrow value columns break every value from its period onto a second line, while the Effect column takes about 60% of the width. Large amounts print without thousands separators ('6261', '1006').
   - Fix: Widen the value columns or put the period in the header so each value fits on one line, and format amounts as 6,261 and 1,006.

### What changed: the analysis

Kind: prose/table · handoff lines 78-94 · verdict **CONCERNS**

- Narrative: The table is readable and its sentences are short, but it undersells real changes (the new Watchlist label and pro forma figure are classed Presentation/Unchanged), uses four rows on one repeated selection sentence instead of the new modules' conclusions, and lets pipeline words through ("pack", "blocked", "select", "defects").
- Visual: There is no chart; the table renders cleanly at 1440 px with readable spacing, wrapping and contrast, but the doubled module names and the undifferentiated Status text weaken scanning.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 93: "Investment committee debate (CP-6) | Unchanged | Presentation | Both runs withhold any position pending market and legal evidence; the current run labels the stance Watchlist." (also line 83: "the current run adds a pro forma figure for the same point")
   - Problem: The committee row now carries a Watchlist label, and the foundation row adds a new pro forma leverage figure. Both are still classed as Unchanged with cause Presentation, so a reader scanning the Status column misses a new stance label and a new number. Line 87's "the current wording is sharper" says something changed but not what.
   - Fix: Give rows that add a label or a figure their own status (for example "Changed: stance labelled" or "Changed: figure added"), and say in Why what is new and whether it moves the view.
2. **Medium · narrative** (New reader, Saboteur)
   - Where: lines 85, 88-90: "Deep research (CP-DR) | New | Unresolved | It ran only this time, and the pack does not say why the earlier run did not select it." (same sentence four times)
   - Problem: Four of twelve rows repeat one sentence about run selection. None of them says what the new analysis concluded, so the reader learns nothing about the credit from a third of the table (for example, the downside stress result appears only further down in the ledger).
   - Fix: Cover the scope difference once in a lead note, and use each New row's Why for the module's one-line bottom line.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 86: "The module is blocked in both runs because no executed governing document is in the pack."; also lines 82, 85, 92: "the pack", "select it", "open defects"
   - Problem: "module is blocked", "the pack", "select" and "open defects" are pipeline words, not reader language. A portfolio manager does not know what a pack is or what blocking a module means.
   - Fix: Use reader wording, such as "Covenant analysis could not be done in either run because the signed indentures and credit agreement were not among the documents", and say "source documents" instead of "pack".
4. **Medium · narrative** (New reader)
   - Where: Module column, screenshot CP-8_s-78.png top table (y=300-780): "Financial data foundation (Financial foundation)", "Investment committee debate (Committee decision)" next to "Relative value and security selection" with no alias
   - Problem: Removing the module codes left double names on screen: each internal module title is followed by the side-menu label in brackets, and two rows (Forward credit model, Relative value) do not follow that pattern. The reader has to reconcile three naming schemes against the left menu ("Security selection", "Committee decision").
   - Fix: Show one name per row, the same label the left menu uses.
5. **Low · narrative** (Saboteur)
   - Where: lines 80-93 Cause column: every row reads either "Presentation" or "Unresolved"
   - Problem: The Cause column has only two values and Status already implies them, so it carries almost no information. The section also opens straight into the table with no bottom-line sentence (for example, that no analytical conclusion changed and four analyses were added).
   - Fix: Open with a one-sentence bottom line for the table, and keep Cause only where it separates causes (new period, new source, method change).
6. **Low · visual** (Auditor, New reader)
   - Where: Screenshot CP-8_s-78.png, "What changed: the analysis" table, Status column (x~540-600, y=250-780)
   - Problem: The New and Unchanged statuses are the same plain grey text and the rows keep run order. The four New rows are scattered through the table and do not stand out on a scan.
   - Fix: Show Status as a chip or with weight (New highlighted), or group the New rows together.

### Calculations

Kind: prose/table · handoff lines 139-147 · verdict **BLOCK**

- Narrative: The section is a process note, not credit analysis. It leaks pipeline vocabulary (script filenames, transport, handoff, pack, ledger), says a manual completeness check was done without giving its result, and gives awkward sentences where the module name was swapped in.
- Visual: There is no chart, map or timeline. The section is one three-line paragraph and a two-row ID/Item/Status table. It renders cleanly (no clipping, adequate contrast), but the table repeats the prose and spends a full-width box on internal K0/K1 codes.

1. **High · narrative** (Auditor, New reader)
   - Where: L141: "The method's helper scripts (prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py) were not run in this transport"; also "comparison pack", "handoff of either run", "ledger row", "pack measure"
   - Problem: The paragraph is written in pipeline vocabulary: script filenames, "transport", "handoff", "pack", "ledger". The house standard names "handoff" as non-reader language. A portfolio manager cannot tell what any of these terms mean or why they matter.
   - Fix: Say in reader terms that the comparison only copies figures from the two runs and that its consistency checks were done manually, with no file names or transport/handoff/pack wording.
2. **Medium · narrative** (Saboteur)
   - Where: L141: "the completeness check (one analysis row per pack module, every limitation ref in exactly one ledger row, one issuer row per pack measure) was done by hand."
   - Problem: The paragraph says a manual check was done but never gives the result: whether it passed or found omissions. The reader is left to assume the comparison is complete, which the section does not actually state.
   - Fix: State the outcome first (for example, that every module, limitation and measure was accounted for, or which were missing) before saying how it was checked.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: L141: "CP-8 makes no calculation" (rendered as "Changes since the last run makes no calculation"); L145 rendered "None performed: Changes since the last run never calculates"
   - Problem: Replacing the module code with the page title gives ungrammatical sentences in which a page title is the subject. A reader can misread them as "nothing has changed since the last run".
   - Fix: Write "This comparison performs no calculations" so the subject reads as natural English after the module name is swapped in.
4. **Low · narrative** (Auditor)
   - Where: L139-147: section order (Calculations after Limitations ledger, before Gaps), with no judgement-first lead
   - Problem: A process-assurance note sits among the reader sections without a bottom-line sentence, and the K0/K1 table repeats the prose word for word. It adds length without giving the reader anything to act on.
   - Fix: Collapse the section into one judgement-first sentence (figures copied, not recalculated, and manually checked with result X), or move it into Limitations.
5. **Low · visual** (New reader, Auditor)
   - Where: Calculations table (ID / Item / Status), shot CP-8_s-139.png, crop of the region y≈1500-1740 at full resolution, saved as scratchpad/tmp/CP-8-182-a.png
   - Problem: A full-width three-column table holds two rows that repeat the paragraph above it. The ID column shows internal codes "K0"/"K1" in small monospace that mean nothing to the reader, and the middle and right columns leave large empty gaps.
   - Fix: Drop the table, or drop the internal ID column and fold the two statuses into the lead sentence, so the section takes two lines instead of a boxed grid.

### Gaps

Kind: prose/table · handoff lines 148-159 · verdict **BLOCK**

- Narrative: The Gaps table is a process log in pipeline vocabulary ("pack", "handoff", "transport", "register row") with no judgement on whether the gaps matter. It mixes credit-relevant gaps (the debt/cash bridge, undrawn facilities) with internal process rows.
- Visual: The table renders cleanly (four readable columns, consistent row spacing, no clipping). It is marred by a stray "Basis" chip in the Gap cell of the undrawn-facilities row and by file-name sources ("changes.json", "context") in the Source column.

1. **High · narrative** (Auditor, New reader)
   - Where: L153 "Not carried as pack measures under those exact labels | No register row for them; both runs' free cash flow is stated in their own handoffs only"; L157 "The current source-readiness handoff marked this comparison conditional on a prior deliverable"; L158 "Not run in this transport"
   - Problem: The table speaks pipeline language the house standard bans: "handoff", "pack", "register row", "transport", "helper scripts", and "Run activity" in the rendered row 6. A credit committee reader cannot tell what was actually missing from the comparison.
   - Fix: Say each gap in reader terms, e.g. "free cash flow, gross debt and net debt were not compared between the two runs; each run reports its own free cash flow", and keep all process words off the page.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: L150-L158 Gaps table as a whole, with no lead sentence before "| Gap | What the pack could not compare | Effect | Source |"
   - Problem: No sentence says whether these gaps weaken the change conclusions, for example that debt and cash movement between runs is unverified. The reader has to work out the credit meaning from seven loosely ordered rows.
   - Fix: Open with one judgement sentence saying which gaps matter to the comparison (the debt/cash bridge and the facilities change), and list those rows first.
3. **Medium · narrative** (Saboteur)
   - Where: L152 "Net debt change omitted | Gross debt is not stated under that label in either run, so no balance bridge of debt and cash was built" and L153 "Free cash flow, gross debt and net debt measures"
   - Problem: Two rows cover the same missing debt measures and give different reasons (the label is absent from the filing vs. the measure is not carried in the comparison). The phrase "not stated under that label" can be misread as gross debt being undisclosed for a company whose debt is plainly reported.
   - Fix: Merge the two rows into one gap that states plainly that the debt and cash movement between runs was not compared and why, and that leverage was compared only as a ratio.
4. **Medium · narrative** (New reader)
   - Where: L155 "Modules without an earlier counterpart | Deep research, downside pathway, macro and hedging, forward model"
   - Problem: "Modules" is internal wording, and the names do not match the page navigation ("Research questions", "Downside", "Rates, FX & hedging", "Forward credit model"), so the reader cannot find the sections referred to.
   - Fix: Call them analyses that are new in this run, and use the exact section names shown in the left navigation.
5. **Medium · narrative** (Auditor)
   - Where: L157 "Source readiness instruction | ... | No effect on the comparison | Source readiness (CP-0)"; L158 "Helper scripts | Not run in this transport | Completeness checked by hand | context"
   - Problem: These two rows are process notes with no credit effect. The helper-scripts row repeats Calculations K1. Both use up reader attention, and the module code in L157 depends on the renderer to strip it.
   - Fix: Drop both rows from the reader table, or record them once as a limitation in plain words.
6. **Medium · visual** (New reader, Auditor)
   - Where: Gaps table, row "Undrawn committed facilities", Gap column; shots2/CP-8_s-148.png crop (340,1740)-(1400,2250), saved as tmp/CP-8-183-a.png
   - Problem: A stray grey "Basis" chip sits next to the gap name "Undrawn committed facilities" and on no other row. It has no meaning in this table and looks like a broken label.
   - Fix: Remove the chip from table cells, or show the basis only in the Source column.
7. **Medium · visual** (Auditor, New reader)
   - Where: Gaps table, Source column: "changes.json" (rows 1-5), "context" (row 7), "prior/Financial foundation handoff, page 4" (row 3); same crop
   - Problem: The Source column shows internal file names and "context" rather than identities a reader can trace. "prior/Financial foundation handoff" is a path, not a document.
   - Fix: Cite reader-facing sources such as "Run of <date>, Financial foundation, page 4" or "Comparison of the two runs", and never show file names.
8. **Low · narrative** (New reader)
   - Where: L156 "New-module rows carry cause Unresolved"
   - Problem: "Unresolved" appears as a capitalised status code that is not defined on this page.
   - Fix: Say "the reason these analyses were added is not recorded" in plain words.

### Request + Next module

Kind: run plumbing · handoff lines 1-4, 160-163 · verdict **BLOCK**

- Narrative: This is run plumbing and does not owe the bottom-line ladder, but it shows pipeline wording to the reader ("credit_snapshot", "handoffs", "comparison pack", "runs last", "can be delivered"), and it names the baseline run only by an internal id with no date.
- Visual: Both sections are plain paragraphs with no chart, map or timeline; they render cleanly at full width with readable spacing, but run identifiers are styled inconsistently and the plumbing headings sit in the main page navigation. Not verified: rendering at other widths, other screenshots of this module, and the baseline run's handoff.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 3: "on the credit_snapshot pathway, against the earlier credit_snapshot run ... (tdg-reader-format-001). ... explained from the comparison pack and both runs' handoffs" (rendered as-is in CP-8_s-1.png, Request paragraph, y~215-265)
   - Problem: The house rule bans pipeline vocabulary on screen, and the reader-facing Request shows a snake_case pathway token ("credit_snapshot"), a raw run id, "comparison pack" and "handoffs". The renderer swaps "CP-8" for the module name but leaves the rest of this wording in place. The New reader persona also caught this, which promoted it from Medium.
   - Fix: Describe the scope in reader terms, for example 'compared with the earlier credit snapshot of the same date (run of <date>), using both runs' module write-ups', with no snake_case tokens or internal terms.
2. **Medium · narrative** (Auditor)
   - Where: Line 162: "None: CP-8 runs last. The run can be delivered with this comparison;" (rendered "None: Changes since the last run runs last." in CP-8_s-160.png, Next module, y~1915-1940)
   - Problem: The paragraph is pipeline sequencing and delivery-status text ("runs last", "can be delivered"). Substituting the module name produces the clumsy "Changes since the last run runs last", and the 'Next module' heading also shows up in the On this page navigation.
   - Fix: Keep only the reader-useful clause, that a later period, executed debt documents or market levels would be needed to show issuer change, and drop or hide the sequencing sentence and the 'Next module' label.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 3: "against the earlier credit_snapshot run of the same issuer and as-of date (tdg-reader-format-001)"
   - Problem: The earlier run appears only as an internal id, with no run date or method version. On a page titled 'Changes since the last run', a committee reader cannot tell which run is the baseline or when it was produced, so they cannot weigh whether the methods have moved since.
   - Fix: Name the baseline run by its run date and show that date beside the id, matching how the page header labels the current run ("30 September 2024 · Credit snapshot").
4. **Low · visual** (New reader)
   - Where: CP-8_s-1.png: header bar 'TDG-PROOF-SNAPSHOT-OPUS-002' (uppercase monospace, y~162) versus Request body '(tdg-reader-format-001)' (lowercase body font, y~240)
   - Problem: The two run identifiers use different case and typefaces, so the reader cannot easily see that they are the same kind of label and that one is the baseline for the other.
   - Fix: Render run identifiers in one consistent style, the header bar's style, wherever they appear, or replace them with dated labels.
5. **Low · visual** (Auditor)
   - Where: CP-8_s-1.png, On this page navigation (x~95-260, y~880-1150): 'Request' and 'Next module' listed beside 'Bottom line', 'Key findings'
   - Problem: Plumbing sections get the same navigation weight as the reader's analytical ladder. Both are plain text blocks with no visual distinction from the analysis, which pulls the eye to non-analytical material.
   - Fix: Group plumbing sections (Request, Calculations, Next module) under a muted or collapsed 'About this comparison' entry, and leave the analytical sections as the primary navigation.

### Limitations

Kind: reader passage · handoff lines 60-66 · verdict **CONCERNS**

- Narrative: The four limitations are judgement-first and specific, but the liquidity bullet contradicts the Bottom line, two bullets use pipeline words ('pack', 'modules'), and the October 2024 payout is mentioned but never defined.
- Visual: There is no chart in this section. It renders as a clean bulleted list, but the date wraps at its hyphen, the prose column is narrow, and the section is followed by Request text and hash tables that push the evidence tables down by about 800 px.

1. **Medium · narrative** (Saboteur)
   - Where: line 65: "Undrawn facilities are on different definitions in the two runs, so the conclusion that liquidity is unchanged rests on the cash balance only, not on committed headroom."
   - Problem: This contradicts the Bottom line (line 35), which says the undrawn difference "implies no movement in the issuer's liquidity", so the page asserts and withdraws the same claim. The cash it now rests on is also the 6261 US$m that line 74 says still holds the accrued October 2024 dividend. A committee member could take 'liquidity unchanged' as a statement about headroom after the payout.
   - Fix: Have the limitation and the Bottom line say the same thing: only the cash balance can be compared, that balance is before the October 2024 dividend, and committed headroom cannot be compared.
2. **Medium · narrative** (New reader, Auditor)
   - Where: line 63: "The pack could not compare net debt balances, so the conclusion that net leverage is unchanged rests on the two runs' ratios alone"; line 64: "The four modules added this time have no earlier counterpart"
   - Problem: "The pack" (the internal comparison pack) and "modules" are pipeline words a portfolio manager has no referent for. "The four modules" also makes the reader go back to Key findings to learn which four analyses are meant.
   - Fix: Use reader language, for example 'the comparison could not reconcile net debt balances', and name the four new analyses (downside, rates and hedging, forward model, deep research) in the bullet itself.
3. **Medium · visual** (Auditor, New reader (promoted from Low))
   - Where: shots2/CP-8_limitations.png, from the end of Limitations (y about 410) to 'What changed: the issuer' (y about 1225, at the 1200-px display scale)
   - Problem: Right after the Limitations section comes 'Request' (with 'credit_snapshot pathway', 'tdg-reader-format-001' and 'handoffs'), then two tables of sha256 hashes. That puts about 800 px of pipeline material between the reader's prose and the evidence tables that back it. The hashes and run IDs are not reader material, and the issuer comparison table ends up buried below them.
   - Fix: Move Request and the hash tables below the evidence tables (or into a collapsed provenance area), so that Limitations is followed directly by 'What changed: the issuer'.
4. **Low · narrative** (New reader)
   - Where: line 62: "it says nothing about the October 2024 payout's aftermath beyond what each run states."
   - Problem: Neither this section nor the rest of the page says what the October 2024 payout was (size, form). The limitation also points to 'what each run states' without saying what that is, so a reader cannot judge how much the caveat matters.
   - Fix: Name the payout once in plain terms (a special dividend paid in October 2024) and say what the limitation actually leaves unknown, for example leverage and cash after the payment.
5. **Low · narrative** (Saboteur)
   - Where: line 62: "the conclusion that the issuer did not change holds by construction"
   - Problem: This states that the module's headline finding is true by design, yet the Bottom line opens 'About the same' as though it were an empirical result. A reader who skims the top can over-read it as evidence that the credit is stable.
   - Fix: Put the 'by construction' qualification into the Bottom line's first sentence as well, so the judgement and its scope reach the reader together.
6. **Low · visual** (Auditor)
   - Where: tmp/CP-8-178-a.png (crop of shots2/CP-8_limitations.png, x 320-1440, y 210-640): first bullet breaks "2024-" / "09-30"
   - Problem: The ISO date wraps at its hyphen across two lines, which makes it harder to read. The Limitations text column is also capped at about 60% width, leaving a wide empty band on the right, while the tables below run full width.
   - Fix: Stop dates from breaking (a non-breaking hyphen or nowrap on dates), and keep a consistent text measure for the module's prose and the tables around it.
