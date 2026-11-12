# Adversarial review, section by section: earlier run (secondary)

Date: 2026-11-12. This is NOT the latest run. `tdg-reader-format-001` (TransDigm, as of 2024-09-30,
credit snapshot, sol-medium, 2026-11-11 22:39 to 23:10 UTC, 8 of 8 modules delivered) was reviewed
first by mistake; the latest run's report is `latest-run-tdg-proof-snapshot-opus-002.md` beside this
file, which also states the method, severity scale and limits. Same method here: 126 sections, one
read-only reviewer each. 877 findings: 227 High, 446 Medium, 204 Low; 100 sections BLOCK, 26 CONCERNS.
The repeating patterns are the same as in the latest run's report. Run folder (read-only):
`/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001`.

## Counts by module

| Module | Sections | High | Medium | Low | Sections blocked |
|---|---|---|---|---|---|
| Source readiness (CP-0) | 11 | 18 | 38 | 16 | 8 |
| Financial foundation (CP-1) | 20 | 38 | 67 | 37 | 18 |
| Business & governance (CP-1A) | 17 | 25 | 60 | 31 | 12 |
| Fundamental credit (CP-2) | 14 | 24 | 51 | 26 | 11 |
| Legal & covenants (CP-4) | 12 | 21 | 39 | 16 | 12 |
| Security selection (CP-3) | 17 | 30 | 62 | 30 | 12 |
| Evidence validation (CP-5) | 16 | 32 | 58 | 24 | 16 |
| Committee decision (CP-6) | 19 | 39 | 71 | 24 | 11 |

By subject: narrative High: 185; narrative Medium: 313; narrative Low: 74; visual High: 42; visual Medium: 133; visual Low: 130.

## Source readiness (CP-0)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001/requests/CP-0/331aa2e77a01ca0d054d1d43329f57c7c94fa9aa0557a6f7b8b6956ca306dc27/1.response.md`

### Selected live-consumer readiness and command sheet

Kind: prose/table · handoff lines 69-80 · verdict **BLOCK**

- Narrative: The section is a pipeline readiness and command table with no bottom line, written in banned pipeline vocabulary (consumer, handoff, command, enum codes). Its DO NOT RUN instructions contradict legal and relative-value modules that the same run did produce and show to the reader.
- Visual: It is a single wide table with no chart. Its Source column is clipped at the card edge, so the citations are unreadable. Long filename citations make rows very tall, and status values have no visual distinction.

1. **High · narrative** (Auditor, New reader)
   - Where: line 71 header "| Canonical consumer | Evidence demand and available support | Readiness | Command |"; line 79 "Analytical handoff production remains planner sequencing."; line 76 "prevent the owning workflow"; section title line 69 "Selected live-consumer readiness and command sheet"
   - Problem: The section is written in pipeline language ("canonical consumer", "live-consumer", "command sheet", "handoff", "planner sequencing", "owning workflow", "downstream input acceptance certified"). The house standard bans this vocabulary, and a credit reader cannot tell what a "consumer" or a "command" is.
   - Fix: Retitle and relabel it in reader terms (for example "What the source files can support, by analysis"), with columns such as Analysis, Evidence available, Can it be relied on, Main gap, Source, and drop the handoff and planner wording.
2. **High · narrative** (Saboteur, Auditor)
   - Where: line 76 "CONDITIONAL | DO NOT RUN" (Legal and covenant package) and line 77 "CONDITIONAL | DO NOT RUN" (Relative value and security selection)
   - Problem: The page tells the reader not to run legal/covenant and relative-value work, yet the same library's sidebar lists Legal & covenants and Security selection as completed modules of this run (the run folder has CP-3 and CP-4 outputs). The reader cannot tell whether those modules' conclusions should be trusted or ignored. The label "CONDITIONAL" also reads as partly ready while the command says do not run.
   - Fix: Say what this means for the reader, for example "Legal terms cannot be assessed from these files; treat the Legal & covenants page as summary orientation only", using a readiness label that matches the instruction.
3. **High · visual** (Auditor, New reader)
   - Where: Source column, shots/CP-0_s-69.png, right edge x≈1355-1390 (crop tmp/CP-0-005-a.png)
   - Problem: The Source column is clipped at the card's right edge. Its text wraps to about 4 characters ("TDG_ / 30_10 / K_000 / 0000"), so every citation is unreadable on screen. The very long filename citations also stretch each row to about 300-650 px tall, mostly empty space.
   - Fix: Show sources as short labels (for example "10-K FY2024 p.117-124") in a column wide enough to read without truncation, or move them to the row's Basis link, so the table fits the 1440 px page.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 69-79: the section opens directly with the table at line 71; there is no sentence before it
   - Problem: The section has no bottom line. The reader has to read seven dense rows to learn the judgement: fundamental work is supportable with limits, while legal/covenant and market relative-value conclusions are not.
   - Fix: Open with a one- or two-sentence judgement on what the source set supports and what it cannot support, then show the table.
5. **Medium · narrative** (New reader, Auditor)
   - Where: line 73 "READY_WITH_LIMITATIONS | RUN with restrictions"; line 78 "RUN in planned sequence"
   - Problem: Raw enum codes in upper case with underscores, and run instructions addressed to the pipeline, are shown as reader content. Readiness and Command say the same thing twice in machine form.
   - Fix: Merge Readiness and Command into one plain-English column (for example "Usable, with limits" / "Not assessable from these files").
6. **Medium · visual** (Saboteur)
   - Where: Table rows, shots/CP-0_s-69.png, whole table x≈300-1390, y≈250-2400
   - Problem: The six-column table runs past the screenshot's 2400 px height for seven rows. Readiness and Command values have no visual distinction (no chip or colour), so the two DO NOT RUN rows look the same as the RUN rows and are easy to miss.
   - Fix: Shorten the rows and give the readiness status a visual cue (chip or weight), so the two not-assessable analyses stand out at a glance.
7. **Low · narrative** (New reader)
   - Where: line 77 "Instrument identities, ranks as disclosed, maturities and financial context are available."; line 73 "management add-back bridge and facility/debt carrying values"
   - Problem: The cells are telegraphic fragments full of jargon ("add-back bridge", "ranks as disclosed", "bounded retrospective synthesis"). They are hard to read for someone who has not seen the files.
   - Fix: Write each cell as one short plain sentence saying what is available and what is missing.

### Source classification and authority

Kind: prose/table · handoff lines 26-36 · verdict **BLOCK**

- Narrative: The section is a single table with no judgement sentence. Its two credit-relevant dispositions (the FY2024 10-K was published after the as-of date; the Dec-2024 10-Q is quarantined) are buried in end cells, and the language is pipeline and extraction jargon rather than reader language.
- Visual: There is no chart in this section. The table's fifth column is clipped at the card edge with no visible scroll cue, long repeated filenames take the width, and one row prints escaped raw JSON.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 33: "Quarantine post-as-of operating and transaction facts. Historical comparatives may be cited only with their original period and later-publication caveat"; line 32: "not available contemporaneously at the as-of date."
   - Problem: The section's two judgements that change how a reader uses the numbers are buried in the last cells of their rows. One is that the FY2024 10-K was published after the as-of date. The other is that the subsequent 10-Q is quarantined. The section opens with a bare table, has no lead-in sentence, and gives no judgement first.
   - Fix: Open the section with one judgement sentence (for example, which sources control, which are quarantined and why) before the table, and keep the table as support.
2. **High · visual** (Saboteur, Auditor)
   - Where: Source classification and authority table, CP-0_s-26.png, right edge x~1310-1390 (orig px), y~255-1500; crop scratchpad/tmp/CP-0-002-a.png
   - Problem: The fifth column, "Fidelity limitation and disposition", is cut off at the card edge ("Fidelity limit…", "Quarantine p… and transact…") and nothing on screen shows the table scrolls. That column holds the dispositions that matter most to a credit reader: the Dec-2024 10-Q is quarantined, restricted cash must not be read as unrestricted cash, and the "executed" label does not prove execution.
   - Fix: Make all five columns fit at 1440 px by wrapping the long file names or narrowing the Source column, or move the disposition column next to Source so it can never be clipped.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 28 header "Located exact substring"; line 32 "linearized tables require downstream header and sign checks. Audit authority does not certify extraction fidelity"; line 30 "downstream users must not treat"
   - Problem: The table speaks pipeline and extraction language a portfolio manager does not use: "located exact substring", "linearized tables", "extraction fidelity", "downstream users", "retained", "Separate active historical version". The house standard keeps pipeline vocabulary off the page.
   - Fix: Rename the column (for example, "Quoted text") and restate the limitations in reader terms, such as "table figures need checking against the filing" and "later modules" → "this report".
4. **Medium · visual** (New reader, Auditor)
   - Where: line 35: "“\"as_of\": \"2024-09-30\"”; “\"cutoff\": \"\"”; “\"legal_documents\": \"executed\"”"; rendered at CP-0_s-26.png ~y 1400-1475, column 2
   - Problem: Raw JSON with escaped backslashes from the run configuration is printed to the reader as a quoted source. The row also presents "context", the run settings, as if it were a source document.
   - Fix: Show the settings as plain values (as-of date 30 Sep 2024; no information cut-off set; legal documents labelled executed) in prose or a footnote, not as an escaped JSON quote in a source table.
5. **Medium · visual** (New reader)
   - Where: Source column, lines 30-35, e.g. "TDG_2024-03-30_10-Q_0001260221-24-000046_tdg-20240330.htm.jsonl, pages 1–2; TDG_2024-03-30_10-Q_0001260221-24-000046_tdg-20240330.htm.jsonl, pages 5–6"; CP-0_s-26.png Source column
   - Problem: Each Source cell repeats the same 60-character machine filename twice, wraps over four or five lines, and takes width the clipped disposition column needs. A reader cannot tell at a glance which row is the 10-K and which is a 10-Q.
   - Fix: Lead each row with a short reader label (for example, "10-Q, quarter to 30 Mar 2024") and give the filename once, with combined page ranges.
6. **Low · narrative** (New reader)
   - Where: line 30: "Balance sheets at March 30, 2024 and September 30, 2023; income for thirteen- and twenty-six-week periods and cash flow for twenty-six-week periods, with prior-year comparatives. Financial statements use dollar amounts in millions..."
   - Problem: Cells of 50 to 70 words make each row a wall of text. The units statement (USD millions, except shares and per-share amounts) is repeated in every row instead of being said once.
   - Fix: State the common units once above the table and keep each cell to the period coverage and the one treatment that differs.

### Coverage disposition and exact source-to-consumer map

Kind: prose/table · handoff lines 37-54 · verdict **CONCERNS**

- Narrative: The table is honest about its gaps, but it leads with process instead of a judgement, uses pipeline vocabulary (consumer, lane, quarantined, fidelity gap, fallback) in the heading and cells, and buries the credit-relevant gaps (no executed legal documents, no market inputs, December quarter excluded) in the last rows.
- Visual: The section has no chart, map or timeline; it is one 11-row, 4-column table that runs past a full screen. Long, wrapping raw file names in the Source column make it hard to read, and an empty \"Basis\" chip on every row adds clutter. Module codes are correctly replaced by module names on screen.

1. **High · narrative** (Auditor, New reader)
   - Where: Heading line 37 "Coverage disposition and exact source-to-consumer map"; column header line 41 "Consumers"; line 51 "other consumers only if later-event scope is authorized"; line 51 "Entire post-as-of reporting lane quarantined"
   - Problem: Pipeline vocabulary that the house standard bans reaches the reader. It appears in the section heading, the table header and the cell text ("consumer", "lane", "quarantined", "targeted-read/fidelity gap", "Exact substring:", line 53 "No failed or blocked preparation is used as fallback"). A credit committee member reads this as internal tooling talk, not analysis.
   - Fix: Retitle the section and column in reader terms (e.g. "Which sources support which analysis" / "Used by") and replace the pipeline terms in the cells with plain statements of what was read and what was not.
2. **High · narrative** (Saboteur, Auditor)
   - Where: Line 39 "Every supplied file is retained or quarantined below. Uninspected coverage is expressly recorded as a gap, not silently treated as inspected or excluded."
   - Problem: The section opens with a process statement, not a judgement. The findings that matter for credit are buried in rows 10 and 11 (lines 51 and 53): the December 10-Q is excluded as post-period, there are no executed legal documents, and there are no market inputs. Most of each 10-Q and the PDF has not been read. This breaks the judgement-first order.
   - Fix: Lead with one bottom-line sentence saying what the evidence base does and does not cover (no executed indentures, no market quotes or ratings, December quarter excluded, interim filings only partly read), then show the table.
3. **Medium · narrative** (New reader)
   - Where: Line 53 "CP-1 where relevant; CP-4 critically; CP-3 for absent market inputs" (rendered "Legal & covenants critically; Security selection for absent market inputs")
   - Problem: The module-code-to-name substitution turns these phrases into wording that makes no sense. "Legal & covenants critically" and a module that "consumes" absent inputs leave the reader unable to tell that the legal and relative-value work is impaired by these gaps.
   - Fix: State the consequence directly, e.g. "Legal & covenants and Security selection cannot be completed without these documents and market quotes."
4. **Medium · visual** (New reader, Auditor)
   - Where: Source column, CP-0_s-37.png region x~1040-1390, y~310-1980 (every row)
   - Problem: Raw file names such as "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" wrap across 3 to 6 lines and are repeated in full within the same cell. That makes the Source column the widest and densest column in the table, and it shows an internal file extension (.jsonl) and accession strings instead of document names.
   - Fix: Render each source as a short document label (e.g. "FY2024 10-K, pp. 1–4, 124") and give the full identity once in Sources.
5. **Medium · visual** (Auditor, Saboteur)
   - Where: "Basis" chip after every Coverage unit label, CP-0_s-37.png x~380-570; DOM CP-0.dom.html shows data-basis="[]" on all 11 rows of this table
   - Problem: Every row carries a clickable "Basis" button, and all 11 have an empty basis list. The citations are already in the Source column. The chip therefore promises supporting detail that either duplicates the Source column or is empty, and it clutters the first column.
   - Fix: Drop the Basis chip from table rows where a Source column exists, or populate it with that row's sources.
6. **Medium · visual** (New reader)
   - Where: Whole table, CP-0_s-37.png y~255-1640 (11 rows, 4 dense text columns, ~1,400 px tall)
   - Problem: Every cell is a wall of text: the Disposition column runs to 5 to 7 lines and the Consumers column to 5 to 7 lines. The table takes more than a full screen, and nothing in it (no status chip, bolding or ordering) separates usable sources from gaps.
   - Fix: Add a short status value per row (Usable / Partly read / Excluded / Not supplied) and cut the disposition text to one line, so the reader can scan the gaps.
7. **Low · narrative** (Saboteur)
   - Where: Line 43 "TDG_2024-09-30_10-K_...htm.jsonl, pages 1–4" and line 53 Source "context, page 1"
   - Problem: An HTML filing is cited by "pages", and a run-settings file is cited as "context, page 1" as if it were issuer evidence. The reader cannot tell what "context" is without the Sources table.
   - Fix: Label the run-settings row as "Run settings (not issuer evidence)" and say whether page numbers refer to the filing's printed pages.

### Entity boundaries, versions and conflict handling

Kind: prose/table · handoff lines 55-68 · verdict **BLOCK**

- Narrative: The section holds one credit-relevant point: the issuer is TransDigm Inc., not the parent, and the guarantor perimeter is unproven. That point is wrapped in instructions to later modules and in run-configuration jargon instead of being given to the reader as a judgement.
- Visual: The three-column table fits the page width, but raw .jsonl file names fill the Source column and wrap mid-token. Every row also shows a Basis chip whose basis list is empty in the DOM (data-basis="[]"), and there is no chart in this section.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 57: "Downstream analysis must preserve those distinctions rather than apply consolidated earnings or assets indiscriminately to an instrument's guarantor group." Also the line 60 table header "Assessment and downstream handling"
   - Problem: The section's last sentence, and a table header, are pipeline instructions to later modules ("downstream analysis", "downstream handling"), not a credit judgement for the reader. The real credit point is that bondholders may not have a claim on the earnings or assets of non-guarantor subsidiaries, and that point is never stated. Promoted from Medium because two personas caught it.
   - Fix: Open with the credit consequence: the guarantor perimeter is not established, so consolidated EBITDA and assets may overstate what supports each instrument. Rename the column to reader language such as "Assessment".
2. **High · narrative** (Auditor, New reader)
   - Where: Line 63: "Context executed-legal label versus actual inventory | Configuration says executed; no standalone executed agreement is in the pinned inventory. Actual availability governs readiness." Source: "context, page 1"
   - Problem: This whole row describes the run's own configuration ("context", "configuration", "pinned inventory", "readiness"), not the issuer. Its source, "context, page 1", is an internal input rather than an issuer document. A portfolio manager cannot interpret it. Promoted from Medium because two personas caught it.
   - Fix: Say in plain terms that the executed credit agreement and indentures were not supplied, so covenant terms cannot be read, and cite only issuer documents.
3. **Medium · narrative** (Saboteur)
   - Where: Line 67: "No contradictory financial fact identified in the limited inspected overlap. This is not a whole-pack consistency finding; uninspected portions remain untested."
   - Problem: The row reads as "no conflicts", but its only basis is one page from each document (10-K page 118 and PDF page 103), and the caveat that follows cancels the conclusion. A committee member who skims could take the source pack as consistent.
   - Fix: Lead with the limit: only one page of overlap was compared and consistency across the rest of the pack is untested.
4. **Medium · narrative** (New reader)
   - Where: Line 62: "Complete containment and historical-version equivalence are not established; both remain active." Line 66: "no contemporaneous-information assertion"
   - Problem: Phrases such as "containment", "historical-version equivalence", "remain active", "locators cannot be transferred" and "contemporaneous-information assertion" are process jargon. The reader cannot tell what they mean for the credit view.
   - Fix: Restate each row as what the reader may rely on, e.g. "Use the 10-K as primary; the PDF has not been confirmed identical".
5. **Medium · visual** (Auditor)
   - Where: Table rows, column 1, each "Basis" chip (CP-0_s-55.png, about x 300-460, y 320-850 in the displayed image); the DOM shows data-basis="[]" on every row's basis-link
   - Problem: Every table row shows a Basis button whose basis list is empty, while the Source column already carries the references. The reader gets a control that opens nothing, next to a duplicate of what the Source column already shows.
   - Fix: Hide the row Basis chip when its basis is empty, or when the row already has a Source column.
6. **Medium · visual** (New reader, Saboteur)
   - Where: Source column, every row (CP-0_s-55.png, about x 760-1150, y 320-850 in the displayed image), e.g. "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 118–120; TDG_2024-12-28_10-Q_..."
   - Problem: Raw pipeline file names (.jsonl, SEC accession numbers) take about 40% of the table's width. They wrap at hyphens in the middle of a token ("tdg-" / "20240930") and set each row's height, so the assessments are squeezed into a narrow column.
   - Fix: Show short document labels in the Source column (e.g. "FY2024 10-K, pp. 118–120" or "Q1 FY2025 10-Q, p. 6"), with the full identifier on hover or on the Evidence page.
7. **Low · narrative** (Auditor)
   - Where: Line 57: "The parent and debt issuer must remain separate analytical entities."
   - Problem: The opening sentence is a methodological rule, not a judgement on the issuer. The house order is judgement first, and this opener delays the actual finding: TransDigm Inc. is the issuer, the parent is a holding company and guarantor coverage is incomplete.
   - Fix: Open with the structural fact and its credit significance, then any handling rule.

### Gaps

Kind: prose/table · handoff lines 95-107 · verdict **CONCERNS**

- Narrative: The Gaps table is accurate and specific, but it is written for the pipeline, not a credit committee: it uses banned vocabulary (\"consumers\", \"preparation catalog\", \"downstream\"), its severity labels are not on one ranked scale, and it has no lead judgement on which gaps block which credit conclusions.
- Visual: This section has no chart. The table renders without clipping, but raw .jsonl filenames break across lines, narrow wrapped columns make it very tall, and every row shows a \"Basis\" chip whose basis list is empty.

1. **High · narrative** (Auditor, New reader)
   - Where: Column header line 97 "Affected consumers and exact restriction"; line 102 "All consumers. Search/read success is not full fidelity review."; line 102 "Do not use any future blocked-preparation source as fallback."
   - Problem: The rendered page still uses pipeline words the house standard bans: "consumers" in the column header and in rows 101, 102 and 106, plus "preparation catalog", "coverage manifest", "blocked-preparation source", "downstream" and "certified here". Several Remediation cells are instructions to the pipeline, not information a committee reader can use. Module codes were mapped to names (CP-4 shows as "Legal & covenants"), but this vocabulary was not.
   - Fix: Name the affected analysis in reader terms (for example "Affects: covenant and legal conclusions"), and either drop the instructions aimed at the pipeline from Remediation or rewrite them as the missing document the reader would need.
2. **High · narrative** (Saboteur, Auditor)
   - Where: Severity column, lines 99-106: "Critical for legal workflow" / "Material" / "High for legal/security-level work" / "Bounded"
   - Problem: The four severity labels are not on one ranked scale, and the rows are not sorted by them: G-PERIMETER ("High") comes after two "Material" rows, so a reader cannot tell whether High is above or below Material. A committee member could under-weight the guarantor-perimeter gap, which matters for recovery and for which security sits where.
   - Fix: Use one defined ranked scale (for example Critical / High / Medium / Low), sort the rows by it, and put the scope wording in the restriction column.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: Lines 95-97: "## Gaps" followed directly by the table header "| Gap | Severity | Affected consumers and exact restriction | Remediation | Source |"
   - Problem: There is no lead sentence. The reader is not told which gaps limit the credit view: no executed credit agreement or indentures means covenant headroom and enforceability are not assessable, and no market quotes means there is no relative-value view. The reader has to piece this together from eight dense rows.
   - Fix: Open with a one- or two-sentence judgement naming the two critical gaps and the conclusions they block, then show the table.
4. **Medium · narrative** (New reader)
   - Where: Line 99 "G-LEGAL: Executed governing documents not supplied"; line 102 "G-PARSE: No preparation catalog"; line 106 "G-VERSION: PDF containment not fully tested"
   - Problem: Each gap starts with an internal register code (G-LEGAL, G-PARSE, G-VERSION and so on) that the reader is never told about. Some titles ("PDF containment not fully tested", "No preparation catalog") cannot be understood without knowing how the pipeline works.
   - Fix: Remove the G- codes from the display and title each gap by what is missing in plain terms, for example "Annual report PDF and HTML filing not fully cross-checked for duplicates".
5. **Medium · visual** (New reader, Auditor)
   - Where: Source column, shot CP-0_s-95.png region x 1090-1390, y 300-1910 (original px); lines 99-106, e.g. "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 57–59" and "context, page 1"
   - Problem: The sources are raw ingest filenames with accession numbers and a ".jsonl" extension, broken mid-token across 3-6 lines. The reader cannot read them ("tdg-" / "20240930.htm.jsonl"). "context, page 1" is a pipeline input, not a document the reader can find.
   - Fix: Show sources as short reader labels (for example "FY2024 10-K, pp. 57–59"; "Q1 FY2025 10-Q, p. 6"), with the full identifier in a tooltip or in the Sources section.
6. **Medium · visual** (New reader, Saboteur)
   - Where: Gaps table, shot CP-0_s-95.png region x 355-1390, y 290-1925 (original px); G-LEGAL row Remediation cell (line 99) wraps to about 14 lines
   - Problem: The five-column table leaves Remediation and Severity narrow, so rows run 160-240 px tall and the eight-row table takes about 1,600 px of scroll. The Remediation column is the tallest in most rows even though it matters least to a committee reader.
   - Fix: Give the restriction column the width, move Remediation into an expandable row detail or a narrower secondary column, and cut cells to one or two lines each.
7. **Medium · visual** (Auditor, Saboteur)
   - Where: "Basis" button after each gap title, rendered DOM render/CP-0.dom.html: data-paragraph "...CP-0.md:99" through ":106" all carry data-basis="[]"; shot CP-0_s-95.png region x 370-500 in each row
   - Problem: Every gap row shows a clickable "Basis" chip, but its basis list is empty for all eight rows. The chip promises sources it does not deliver, and it repeats the row's own Source column. Clicking it was not tested.
   - Fix: Hide the Basis chip where the row has no basis entries, or fill it from the row's Source cell, so the chip only appears when it leads somewhere.

### Manual checks and unavailable machinery

Kind: prose/table · handoff lines 108-119 · verdict **BLOCK**

- Narrative: This section has no credit content at all. It is an internal log of tools and process (script names, transport, handoff, enum constants, register codes) that breaks the house rule against pipeline vocabulary on reader pages and gives no judgement or consequence the reader can use.
- Visual: There is no chart, map or timeline here. The three-column table renders cleanly with no clipping, but it gives a process log the same visual weight as the Gaps table, wraps a repeated status phrase down the narrow middle column, and shows a Basis chip with an empty basis list on the PreparedPack row.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: L112-116: "prepare_invocation.py | Not run: unavailable in this transport"; "validate_handoff.py ... write_handoff performs transport checks."; "Other scripts and Python assembler, P3/P5 and T1–T8 companion structures"
   - Problem: The whole section is a log of the pipeline's internal tools: script filenames, "transport", "handoff", "write_handoff" and register codes like P3/P5 and T1–T8. The house standard bans this vocabulary from reader pages, and a portfolio manager cannot act on any of it.
   - Fix: Drop this table from the Modules page, or replace it with one reader-language line on what was not checked automatically and why that matters, for example that source fidelity and completeness were checked by hand rather than by the automated checks.
2. **High · narrative** (Auditor, New reader (promoted))
   - Where: L118: "HTML Model input contract | Not evaluated: not selected | SOURCE_SUFFICIENCY_ONLY; CP_MODEL_INPUT_CONTRACT_NOT_EVALUATED. No normalized quarters or model acceptance claim."
   - Problem: Raw machine status constants are printed on screen, and one of them contains the module code prefix "CP_". "Model input contract" and "model acceptance claim" are internal terms the reader cannot interpret.
   - Fix: Show no enum constants; if it matters, say plainly that this review did not check whether the sources are enough to build the HTML Model.
3. **Medium · narrative** (Saboteur)
   - Where: L112-115: "Not run: unavailable in this transport" repeated for prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py
   - Problem: Four rows of "Not run" read like failed quality controls, but the section never says whether that weakens the credit evidence. A committee member could either distrust the whole snapshot or skip a real limit, such as "No confidence score calculated" at L114. There is no judgement first.
   - Fix: If any of this content is kept, open with one bottom-line sentence stating whether the missing automated checks change how far the reader can rely on the sources, and put that in the Limitations section rather than in a separate tool log.
4. **Medium · visual** (Auditor)
   - Where: Table 'Manual checks and unavailable machinery', row 'PreparedPack / ReadinessReview JSON Schema'; shot CP-0_s-108.png crop (340,1640)-(1400,2180); DOM button data-basis="[]" for CP-0.md:117
   - Problem: A "Basis" chip appears on this one row, but its basis list is empty, so the control opens nothing. Handoff line 117 has no source either. The chip suggests sourcing that does not exist and appears on no other row.
   - Fix: Render a Basis chip only when the row has at least one source reference.
5. **Low · narrative** (Saboteur)
   - Where: L112: "No aggregate pack hash supplied or invented."; L114: "No confidence score calculated or invented"
   - Problem: The "or invented" disclaimers answer a pipeline auditor, not a credit reader, and the defensive register makes the reader wonder why fabrication was ever in question.
   - Fix: State only what is missing and its consequence, without denying fabrication.
6. **Low · visual** (New reader)
   - Where: Table 'Manual checks and unavailable machinery', column 'Execution status'; shot CP-0_s-108.png crop (340,1640)-(1400,2180)
   - Problem: The narrow middle column wraps the same phrase, "Not run: unavailable in this transport", over two lines in four rows. This adds height and visual noise without information, and the section gets the same visual weight as the substantive Gaps table above it.
   - Fix: If the content stays, collapse the repeated status into one sentence above a shorter list, so this section weighs visibly less than Gaps.

### Request + Next module

Kind: run plumbing · handoff lines 1-3, 120-126 · verdict **BLOCK**

- Narrative: Both blocks are pipeline material shown to the reader: the request is the model's prompt and 'Next module' gives routing orders, so neither follows the reader's order of bottom line, findings and limitations, and both use banned pipeline words.
- Visual: There is no chart, map or timeline in this section. The two text blocks are laid out cleanly but placed badly, at the top and bottom of the module page, so the page opens and closes on prompt and routing text.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 122: "Proceed to the financial foundation and business fact-pack workflows ... can follow in planner order with the same restrictions; missing future handoffs are not source-readiness failures."
   - Problem: The 'Next module' passage is pipeline routing. 'fact-pack workflows', 'planner order', 'handoffs', 'promoting any fact' and 'source-readiness failures' are pipeline words the house standard bans, and the passage tells the next model what to do instead of telling the reader anything. Reader language failed for the Auditor and was unreadable for the New reader, so it was promoted from Medium to High.
   - Fix: Hide the 'Next module' section from the Modules page, or rewrite it as one reader sentence on what the evidence supports next (for example, that FY2024 annual and interim filings are enough for the financial analysis).
2. **High · narrative** (Auditor, Saboteur)
   - Where: Line 125: "Do not run the full legal-package or relative-value owners until their missing documentary and market inputs are supplied."
   - Problem: This is an order to the pipeline ('owners', 'run'), not a judgement for the reader. It also hides the fact a credit committee needs most: there are no executed bond or loan terms and no market prices, so covenant and relative-value views cannot be formed. That fact is stated in run-control language at the very bottom of the page. Both personas caught it, so it was promoted from Medium to High.
   - Fix: State the gap as a reader-facing limitation near the top of the page: no executed financing documents and no dated market prices were supplied, so covenant and relative-value conclusions cannot be drawn.
3. **Medium · narrative** (Auditor)
   - Where: Line 2: "TransDigm Group Incorporated, as of 2024-09-30; pathway: credit_snapshot. Assess source readiness ... do not provide a credit or investment conclusion."
   - Problem: The 'Request' section shows the model's prompt text. It includes the internal token 'credit_snapshot' and an instruction to the model ('do not provide a credit or investment conclusion') that means nothing to the reader.
   - Fix: Remove the request from the reader page, or replace it with a plain scope line such as 'Scope: which TransDigm FY2024 filings are usable, and for what'.
4. **Medium · narrative** (New reader)
   - Where: Line 2: "effective-source lineage, temporal and entity boundaries, and evidence availability for the selected financial, business, fundamental, legal, relative-value, validation and committee workflows"
   - Problem: This is one dense sentence of abstract nouns, and it uses '2024-09-30' while the page header says '30 September 2024'. A portfolio manager learns nothing from it.
   - Fix: Use one short sentence in plain words with dates in the page's format.
5. **Medium · visual** (Saboteur, New reader)
   - Where: CP-0_s-1.png: 'On this page' navigation, left rail at y≈330-690 (original ~396-828), with 'Request' placed between 'Timeline' and 'Sources'
   - Problem: The two plumbing blocks set the reading order. 'Request' (prompt text) sits right after the Bottom line and Timeline, and 'Next module' closes the page after the 'Manual checks and unavailable machinery' table. The page therefore opens and closes on pipeline material rather than the judgement or limitations.
   - Fix: Hide both blocks, or fold them into a collapsed run-details area, so the page ends on limitations as the house order requires.
6. **Low · visual** (Auditor)
   - Where: CP-0_s-120.png, 'Next module' block at y≈1835-1940 (original ~2200-2330): two full-width paragraphs ending in a grey 'Basis' chip
   - Problem: The two paragraphs run about 1,050 px wide with no break, which is a long measure for running text. The 'Basis' chips are small grey text that is easy to miss. The section looks the same as analytical passages, so nothing marks it as run plumbing.
   - Fix: If kept, set a narrower text measure and style it visibly as run metadata so it is not read as analysis.

### Sources

Kind: prose/table · handoff lines 4-16 · verdict **BLOCK**

- Narrative: The section is an inventory table plus one closing paragraph. The paragraph is pipeline language, and the table names sources by system file names and hashes rather than in plain English, so it gives a PM little about which documents back the view and when they became available.
- Visual: The bordered table is clean, with no clipping, overflow or contrast problem. But its width goes to a hash column a reader cannot use, the useful Authority and use column is squeezed into narrow wrapping cells, and file names break mid-identifier. The section has no chart.

1. **High · narrative** (Auditor, New reader (promoted from Medium))
   - Where: line 15: "No upstream handoffs were supplied. The individual source pins above define this transport's effective source inventory; no aggregate PreparedPack hash, preparation catalog, coverage manifest or JSON Schema was supplied. Source texts were treated as inert evidence." (rendered verbatim under the table, shot CP-0_s-4.png y~805-835 display)
   - Problem: The whole paragraph is pipeline vocabulary on the reader's page: "handoffs" is named in the house standard as banned, and "source pins", "transport", "PreparedPack hash", "preparation catalog", "coverage manifest", "JSON Schema" and "inert evidence" tell a PM nothing and leak the machinery.
   - Fix: Either drop the paragraph from the reader view or replace it with one plain sentence saying the review used only the six files listed and no outside research.
2. **Medium · narrative** (New reader, Auditor)
   - Where: line 8: "TDG_2024-03-30_10-Q_0001260221-24-000046_tdg-20240330.htm.jsonl" (and every row of the Exact source name column, lines 8-13)
   - Problem: Sources are identified only by raw system file names with EDGAR accession numbers and a .htm.jsonl extension. The ruling's VMO2 reference uses a plain-English source list, so a reader has to decode the file name to learn it is the 10-Q for the quarter ended 30 March 2024.
   - Fix: Lead each row with a plain name (for example "Form 10-Q, quarter ended 30 Mar 2024") and keep the file name as a secondary detail or in the inspector.
3. **Medium · narrative** (Saboteur)
   - Where: lines 8-12: the table gives period-end dates only, e.g. "TDG_2024-09-30_10-K_..." with "SEC annual filing; primary FY2024 financial and business source."
   - Problem: The table shows no filing or publication dates. The point-in-time issue that qualifies the bottom line (the FY2024 10-K was filed 7 Nov 2024, after the 30 Sep 2024 as-of date) is invisible here, so the inventory reads as if every source was available at the as-of date.
   - Fix: Add a period and filing-date column so it is visible in the inventory itself which sources postdate the as-of date.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 11: "SEC quarterly filing; quarantined subsequent-period evidence, with separately labelled historical comparatives available."
   - Problem: "Quarantined" is internal jargon. The row never says plainly that this is the quarter ended 28 Dec 2024, after the as-of date, and must not feed the snapshot. "Historical comparatives available" then partly undoes the exclusion without saying which figures may be used.
   - Fix: State plainly that this filing postdates the as-of date and is excluded, except its 30 Sep 2024 balance-sheet comparative, which is used only with that label.
5. **Medium · visual** (New reader, Saboteur)
   - Where: Sources table, sha256 column, shot CP-0_s-4.png crop x340-1400 y220-850 (scratchpad/tmp/CP-0-000-a.png)
   - Problem: The 64-character hash column takes the widest band of the table, about 40% of its width. It squeezes the only reader-useful column, Authority and use, into a narrow strip that wraps over 4-5 lines, while the hash means nothing to a credit reader.
   - Fix: Move the hashes to the Evidence page or the inspector and give the width to a plain source name, period and filing date, and the authority/use text.
6. **Low · narrative** (New reader)
   - Where: line 13: "| context | f7b95e1f... | Run settings only; not issuer evidence. |"
   - Problem: A run-settings file is listed among the issuer sources with a hash. The row does not say that its cutoff, quote and rating fields are blank, which is the fact that matters to the reader.
   - Fix: Remove the run-settings row from the source list, or relabel it "Run settings (not a source)" and note the blank cutoff, quotes and ratings.
7. **Low · visual** (Auditor)
   - Where: Sources table, Exact source name column, shot CP-0_s-4.png display y~255-600 (e.g. "TDG_2024-03-30_10-Q_0001260221-24- / 000046_tdg-20240330.htm.jsonl")
   - Problem: File names wrap at arbitrary hyphens in the middle of the accession number, so one identifier is split across two lines and hard to scan or copy.
   - Fix: Show a short plain label that does not wrap, with the full identifier on hover or in the inspector.

### Bottom line

Kind: reader passage · handoff lines 19-25 · verdict **BLOCK**

- Narrative: The section draws the right boundary (historical financial view yes, legal terms and relative value no), but pipeline wording (\"downstream\", \"the pack\", \"text extraction\", \"fidelity certification\") breaks a house rule, and the overall status is buried at the end of a caveat-heavy second paragraph. Basis lines sit correctly outside the sentences.
- Visual: There is no chart in this section. The two paragraphs are set entirely in large bold headline type, a heavy wall that leaves right-side white space. The section has no visible heading and almost no gap before the Timeline strip.

1. **High · narrative** (New reader + Auditor)
   - Where: L20 "provided downstream work does not equate filing summaries with executed contractual terms"; L23 "the pack supplies incorporated-by-reference descriptions"; "Text extraction permits located textual use, not a blanket visual or full-document fidelity certification. Source readiness is complete with limitations; downstream analysis is not complete."
   - Problem: Pipeline vocabulary reaches the reader: "downstream work", "downstream analysis", "the pack", "text extraction", "fidelity certification" and the module status "Source readiness is complete". A committee member does not know what the pack is, which work sits downstream, or what a fidelity certification is. The house standard bars pipeline wording from reader text.
   - Fix: Say it in reader terms, e.g. what the committee can and cannot rely on from these filings, with no reference to pipeline stages, packs or extraction.
2. **Medium · narrative** (Saboteur)
   - Where: L23 "contains a subsequent-period quarterly filing, and has no dated security quotes or ratings inputs. The annual statements also became available after the requested balance-sheet date."
   - Problem: The bottom line says the December 2024 10-Q is present but not that it is quarantined (the Sources table says so). It says the annual statements came later but gives no date (filed 7 November 2024). A reader could assume post-as-of figures feed the view, or misjudge the timing.
   - Fix: State in the bottom line that the December 2024 quarter is excluded except for labelled comparatives, and give the 10-K filing date.
3. **Medium · narrative** (Saboteur + New reader)
   - Where: L23 "The strongest qualifications are documentary rather than analytical: ... Source readiness is complete with limitations; downstream analysis is not complete."
   - Problem: The overall status comes as the last sentence of the second paragraph, after five sentences of caveats. The judgement-first order is lost. The reader meets "bounded", "source-grounded" and "documentary rather than analytical" before learning the overall answer: usable for a historical financial view, not for legal terms or relative value.
   - Fix: Open with a one-sentence verdict on what the sources allow and forbid, then give the two or three gaps that matter as short separate sentences or bullets.
4. **Medium · visual** (New reader + Auditor)
   - Where: Bottom-line block, shots/CP-0_bottom-line.png, region x 330-1020, y 220-910 (original px); crop tmp/CP-0-001-a.png
   - Problem: About 190 words across two paragraphs are set in large bold headline type, roughly 19 lines of heavy text. With everything emphasised, nothing stands out, and the block reads as a wall. The text column ends near x≈1020, leaving about 300 px of empty white space to the right.
   - Fix: Show only a short verdict sentence in headline weight and set the qualifications in body weight, or as a short list, at normal measure.
5. **Low · narrative** (New reader)
   - Where: L20 "Creditors can therefore receive a source-grounded historical analysis"
   - Problem: The register is off: the reader is a portfolio manager or committee member, not a "creditor receiving analysis". "Bounded" and "source-grounded" are vague qualifiers that carry no information.
   - Fix: Address the reader's decision directly, e.g. which analyses in this report can be relied on for FY2024.
6. **Low · visual** (Auditor)
   - Where: Bottom-line block, shots/CP-0_bottom-line.png, y≈915-935 (original px): second paragraph's "Basis" button directly above the "Timeline" heading
   - Problem: The Timeline heading sits flush against the last line of the bottom line with almost no gap, so the two sections run together. The "Basis" control is small light-grey text beside 22 px bold type and is easy to miss.
   - Fix: Add section spacing or a divider before Timeline, and give the Basis control enough size and contrast to be noticed.
7. **Low · visual** (New reader)
   - Where: DOM render/CP-0.dom.html line 26: <h4 class="sr-only">Bottom line</h4>; screenshot top shows no visible heading
   - Problem: The section has no visible "Bottom line" label, and in the screenshot the module title is scrolled under the sticky bar. A reader landing from the outline link sees untitled bold text with no cue that it is the verdict.
   - Fix: Show a small visible "Bottom line" label above the headline text, as the outline promises.

### Calculations

Kind: prose/table · handoff lines 89-94 · verdict **BLOCK**

- Narrative: The section says only that no calculations were done. It says it in pipeline vocabulary, and it attributes USD to the run configuration as though that were a source.
- Visual: There is no chart. The one-row table card has an empty Basis link, an internal ID styled like a chip, and a lot of white space for a null result.

1. **High · visual** (Saboteur, Auditor)
   - Where: Calculations table, row C0-NONE, 'Basis' button under the ID; shots/CP-0_s-89.png crop (340,215)-(1400,390); DOM: data-basis="[]" aria-label="Basis for row: C0-NONE"
   - Problem: The row shows a Basis link with an empty basis list. A reader who clicks it to check the row's support gets nothing, so a provenance control is on screen with nothing behind it.
   - Fix: Show the Basis control only when the row has at least one basis entry. Otherwise say plainly that no source applies.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: L93: "FY2024 retrospective evidence scope; USD per context, page 1."
   - Problem: The USD currency claim cites 'context, page 1'. L35 of the same handoff calls this 'User/run configuration, not documentary authority'. A reader without the sources will read it as a filing page.
   - Fix: State the currency as reported in the 10-K and cite the filing in a Source column, or label the claim as a run setting rather than a source.
3. **Medium · narrative** (Auditor, New reader)
   - Where: L91: "Period, currency, quantity and source trace"; L93: "No financial figures transformed, no confidence score invented."
   - Problem: The column mixes scope prose with a source reference instead of using a separate Source column. 'source trace', 'confidence score' and 'invented' are pipeline vocabulary and self-defence for an auditor, not reader language.
   - Fix: Split the column into Period/Currency and Source, and drop the confidence-score and 'invented' wording.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: L93: "C0-NONE | No arithmetic performed | Not applicable: source readiness prohibits normalization, reconciliation and figure calculations."
   - Problem: A full four-column table holds one null row. Its only message is that the module calculated nothing, and it says so in internal terms ('source readiness prohibits'). The reader spends a section learning nothing about the credit.
   - Fix: Replace the table with one plain sentence, e.g. that this review checks which documents are available and computes no figures, or drop the section.
5. **Low · visual** (Auditor)
   - Where: Calculations table ID cell; tmp/CP-0-007-a.png; DOM: <small class="ref">C0</small>-NONE
   - Problem: 'C0' is drawn as a small reference chip that looks like a module code. The internal row ID 'C0-NONE' wraps with the Basis link indented under it, giving a ragged first column.
   - Fix: Hide internal row IDs from the reader, or show a plain row label that has no chip styling.
6. **Low · visual** (New reader)
   - Where: Calculations table, whole card; shots/CP-0_s-89.png y≈215-375 (original px)
   - Problem: The four-column full-width card spends about 150 px on one 'not applicable' row, with wide empty space in the Operation and Result columns. It gives the null result the same visual weight as the Gaps table below it.
   - Fix: Render a null calculations result as a single muted note line, not a table card.

### Events: Sources

Kind: timeline · handoff lines 81-88 · verdict **CONCERNS**

- Narrative: This is a data-type section, so it owes only a plain statement. It says \"no event\" without the filing date the module knows, and it uses lane/workflow pipeline wording instead of reader language.
- Visual: The section is an empty seven-column table that repeats one phrase. Its matching timeline lane renders as a cramped, axis-less \"Not established\" row, and the Timeline jump does not bring it into view.

1. **Medium · narrative** (Saboteur)
   - Where: line 87: "This review assigns no corporate event to the source-readiness lane. Reporting periods, audit signatures and publication metadata above classify evidence"
   - Problem: The section and its timeline lane say no dated event is established. The same module dates the audit and filing elsewhere (Source classification: "Audit signed November 7, 2024; filed November 7, 2024"), and its bottom line rests on the annual statements becoming available after the balance-sheet date. A reader who looks only at the timeline is told the availability date is unknown when the module knows it.
   - Fix: Either list the 10-K filing/audit date (7 Nov 2024) as a dated publication event with its period, or state in one sentence that publication dates are shown in Source classification rather than here.
2. **Medium · narrative** (Auditor, New reader)
   - Where: line 81 heading "Events: Sources"; line 87: "belong to their owning downstream workflows"; rendered timeline subtitle "Dated events by module" and lane label "Sources"
   - Problem: "Lane", "owning downstream workflows" and "by module" are pipeline vocabulary that the house standard keeps out of reader language. The heading "Events: Sources" names an internal lane, not something a credit reader can parse. A PM cannot tell what "Sources" means as an event category.
   - Fix: Use reader wording, e.g. heading "Dated events" and the sentence "Operating, financing and maturity events are covered in the financial and legal sections", without the lane or workflow terms.
3. **Medium · visual** (New reader, Auditor)
   - Where: Events: Sources table, line 85; shots/CP-0_s-81.png region x 340-1400, y 210-370 (crop tmp/CP-0-006-c.png)
   - Problem: A seven-column table repeats "Not supplied: no source-readiness event stated" in every cell of its only row. It takes a full table card to say "nothing here", adds no information and reads like a rendering fault. Missing content is labelled correctly, but the layout buries that one fact under repetition.
   - Fix: Replace the empty table with a single line such as "No dated events for this module", or render a one-cell gap row that spans all columns.
4. **Medium · visual** (Auditor)
   - Where: shots/CP-0_timeline.png (the Timeline jump): the top of the content area shows the "Sources" table, while "Timeline" is highlighted in On this page
   - Problem: When the reader jumps to Timeline, the timeline itself does not appear. The view lands on the Sources section below it, and the timeline is visible only in the full-page render (render/CP-0.png, y about 960-1050), squeezed between the bottom line and Request. The reader who clicks Timeline does not see the timeline.
   - Fix: Make the Timeline anchor land on the timeline block, below the sticky header, so the lane is in view after the jump.
5. **Low · visual** (New reader)
   - Where: render/CP-0.png crop tmp/CP-0-006-a.png, y 955-1050: the "Timeline" heading sits directly under the bottom line's last "Basis"
   - Problem: The timeline block has almost no top spacing after the large bottom-line text. It has no date axis, and its one lane shows a grey "Not established for this run". It reads as an orphaned footer rather than a visual.
   - Fix: Give the timeline block section spacing like the other parts, and when no lane has an event, show one plain-language sentence instead of an empty lane.
6. **Low · visual** (Auditor)
   - Where: line 85 row, rendered "Basis" button (CP-0.dom.html s-81, data-basis="[]")
   - Problem: The row has a Basis link with an empty basis list, so the reader is offered a source trail that leads nowhere.
   - Fix: Hide the Basis control when a row has no basis entries.

## Financial foundation (CP-1)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001/requests/CP-1/d9544ab4098afbb3399ed865fe1399bb8d71f5a1af45a0fa77e4f69ebc11779a/1.response.md`

### Reported balance sheet and funding review

Kind: prose/table · handoff lines 72-105 · verdict **BLOCK**

- Narrative: The section is a full balance-sheet data table with no bottom line. Its notes use pipeline wording, and the FY2023 dividends-payable row contradicts its own note ('0' versus 'material in both periods'). The arithmetic I checked (current assets, current liabilities, total liabilities, equity) reconciles.
- Visual: There is no chart in this section. The table renders legibly but is very tall: the same three-line internal file name repeated in the Source column, no thousands separators, mixed-case labels and unmarked subtotals make it slow to scan.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 89: "Dividends payable | 4216 | 0 | USD million; source prints dash in FY2023; material non-debt funding item in both periods, stories below"
   - Problem: The row shows 0 for FY2023 and says the source printed a dash, then calls the item material in both periods. The figure and its note contradict each other. The reader also cannot tell whether the dash means nil or not reported, which breaks the missing-is-not-zero rule.
   - Fix: Show the FY2023 cell as nil (dash) or as not reported, matching the source, and confine the materiality note to FY2024, where USD 4,216m against USD 6,261m cash is the point.
2. **High · narrative** (Saboteur, New reader)
   - Where: lines 72-104: the section is a 29-row table with no lead sentence under "### Reported balance sheet and funding review"
   - Problem: A section titled 'funding review' gives no judgement. It does not say that the FY2024 cash build is largely committed to a USD 4.2bn dividend payable, or that stockholders' deficit widened from -1,978 to -6,283. A reader skimming the table can take USD 6.3bn of cash as free liquidity.
   - Fix: Open with a one-to-two sentence bottom line on what the balance sheet means for funding (cash net of the declared dividend, deficit trend, debt carrying vs principal) before the table.
3. **High · visual** (Auditor, New reader)
   - Where: Source column, every row, CP-1_s-72.png x~950-1160 across the full height: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 120"
   - Problem: Each row repeats the same 70-character internal file name (an EDGAR accession number plus a pipeline .jsonl extension), and it wraps to three lines. That makes every row about three times taller and pushes the table across several screens. The .jsonl name is pipeline vocabulary, not a citation a reader can use.
   - Fix: Cite a reader label such as "FY2024 10-K, p.120" once in the header or the Basis line, and list the full file identity in ## Sources.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 96: "share counts are not monetary operands"; line 87: "not additional to gross principal in leverage"; lines 89/93: "stories below"
   - Problem: The unit/review notes use internal calculation wording (operands, stories, additional to gross principal). A credit committee member has to decode it, and it carries no analytical judgement.
   - Fix: Rewrite each note in plain credit language (for example 'included in the gross debt figure') or drop notes that only restate the asset/liability class.
5. **Medium · visual** (New reader)
   - Where: Value columns 2024-09-30 / 2023-09-30, CP-1_s-72.png x~500-645, e.g. "10029", "25586", "31869", "-7362"
   - Problem: Five-digit USD-million figures appear without thousands separators, and negatives use a hyphen instead of brackets. Large totals are hard to compare at a glance down a 29-row table.
   - Fix: Format as 10,029 and (7,362), with the unit stated once in the column header.
6. **Low · visual** (Auditor)
   - Where: Printed label column, CP-1_s-72.png, e.g. "PROPERTY, PLANT AND EQUIPMENT—NET", "GOODWILL", "LONG-TERM DEBT" next to "Inventories—Net", "Total liabilities"
   - Problem: Labels mix ALL CAPS and sentence case, copied from the filing's typography. Subtotals and totals (Total current assets, TOTAL ASSETS, Total liabilities) have no bold or rule to set them apart, so the table reads as a flat list.
   - Fix: Normalise label case and set subtotal/total rows in bold or with a top rule, as in the VMO2 reference tables.
7. **Low · visual** (New reader)
   - Where: Unit / quantity and funding review column, CP-1_s-72.png x~665-930: "USD million; asset" repeated on most rows
   - Problem: Every row repeats 'USD million', and most notes only restate the account class. The column takes about a quarter of the width and adds little information.
   - Fix: Put the unit in the header and keep this column only for rows with a real funding comment.

### Chart data: leverage

Kind: chart · handoff lines 106-112 · verdict **BLOCK**

- Narrative: The ratios reconcile: 25,068/4,173 = 6.01x, 18,807/4,173 = 4.51x, 19,913/3,395 = 5.87x and 16,441/3,395 = 4.84x. However, the section has no judgement line, uses internal C-codes as its basis, and buries the fact that FY2024 net leverage depends on cash already owed as a USD 4.2bn dividend.
- Visual: The leverage bar chart is visible and labelled correctly, but it shows pipeline chips ("Handoff", "citation without a page"), has no axis, leaves a large empty area to the right, and uses monospace headers in the data table.

1. **High · narrative** (Saboteur)
   - Where: line 111: "FY2024 | 6.01 | 4.51 | x | C01–C04; identical definition; cash includes funds held before settlement of accrued dividend obligations."
   - Problem: Net debt / EBITDA appears to improve from 4.84x to 4.51x. That improvement depends on netting USD 6,261m of cash, and the same balance sheet shows USD 4,216m of dividends payable (line 89). After that payment, net debt is about 23,023 / 4,173 = 5.5x, so leverage actually worsened. The caveat sits at the end of a basis cell and the chart shows the flattering figure without any qualification.
   - Fix: State the bottom line first: gross leverage rose and net leverage after the accrued dividend is about 5.5x. Either show a post-dividend net figure, or flag the FY2024 net bar as cash that is already committed.
2. **High · narrative** (New reader, Auditor)
   - Where: line 110: "C01–C04; gross principal includes finance leases and securitization; denominator is issuer-adjusted EBITDA As Defined."
   - Problem: "C01–C04" are internal calculation-register codes, the same kind as the banned T3.10 labels. The reader would have to find the Calculations section further down the page to decode them, and the basis cell gives no filing page.
   - Fix: Replace the codes with a reader basis, for example "gross debt principal USD 25,068m / adjusted EBITDA USD 4,173m; annual filing pages 71, 144–145".
3. **High · visual** (Auditor, New reader)
   - Where: Leverage chart, CP-1_charts.png, crop (340,250)-(1400,610): chip "Handoff ●" and "1 citation without a page" under each period
   - Problem: Pipeline vocabulary ("Handoff") appears on screen, against the house rule. "1 citation without a page" tells a committee reader that the ratio is poorly sourced, which a reader cannot interpret or act on.
   - Fix: Remove the Handoff chip and replace the citation note with a plain source reference, such as the annual filing pages behind C01–C04.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 106-108: "### Chart data: leverage" followed directly by the table
   - Problem: The section is a bare data dump headed with pipeline wording ("Chart data"). It has no bottom line, so the reader gets two ratio pairs with no judgement on whether leverage is rising or falling or how high it is.
   - Fix: Give the section a reader title, such as "Leverage", and open with a single judgement sentence before the table.
5. **Low · narrative** (Auditor)
   - Where: line 108: "| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit | Basis and limitation |"
   - Problem: "Total debt" here means gross principal (C01, 25,068). The page also carries a carrying-value total (C13, 24,880), so the label can be misread as the balance-sheet debt total. A "Reporting unit" column that repeats "x" in every row also widens the table for no benefit.
   - Fix: Label the ratio "Gross debt principal / adjusted EBITDA" and put the unit "(x)" in the column header.
6. **Low · visual** (Auditor)
   - Where: Leverage chart, CP-1_charts.png, crop (340,250)-(1400,610)
   - Problem: The plot has no y-axis or gridline, and it fills only about 60% of the card width, leaving the right side empty. The unit "x" appears only in small grey text at the top right.
   - Fix: Stretch the plot across the card and put the unit next to the legend or on a labelled axis.
7. **Low · visual** (New reader)
   - Where: Table, CP-1_s-106.png top (y≈210-360): monospace column headers "Total debt / EBITDA" and stray "Basis" under each Period
   - Problem: The column headers are set in a code-style monospace font that does not match the rest of the table. A detached "Basis" label sits under each period with no visible function.
   - Fix: Set the headers in the table's normal typeface and either drop the orphan "Basis" label or tie it clearly to the basis column.

### Chart data: interest cover

Kind: chart · handoff lines 113-119 · verdict **BLOCK**

- Narrative: This is a two-row data table with no bottom line. It cites only the internal code C03 (no filing page, and the Basis buttons are empty), and its caveats are terse fragments that say what the ratio is not, without saying which way the difference goes or how large it is.
- Visual: The chart is visible and drawn to scale: the bars start at zero and 81.39% height matches 2.93/3.60. But the label drops "net" from the denominator, "Handoff" and "1 citation without a page" chips appear on screen, there is no y-axis, the unit is shown only as "x" in a corner, and the right ~40% of the card is empty.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 117: "C03; issuer-adjusted EBITDA As Defined / cash paid for interest, net. Not gross cash-interest or covenant coverage." (rendered as <small class="ref">C03</small>)
   - Problem: "C03" is an internal calculation register code. A reader can only decode it by finding the Calculations section elsewhere on the page. The table has no Source column, and each row's "Basis" button has data-basis="[]", so it opens an empty basis. Neither interest-cover figure can be traced to a filing page, which breaks the rule that tables carry their sources.
   - Fix: Drop the C03 code from the reader text and add a Source column (or a populated Basis line) giving the 10-K pages for adjusted EBITDA and cash interest paid.
2. **High · visual** (Saboteur, Auditor)
   - Where: Interest cover chart legend and data column header "EBITDA / cash interest" (handoff line 115; CP-1_charts.png crop x350-1400, y615-975; CP-1_s-113.png table header)
   - Problem: The legend and column header drop the word "net", so the bar reads as plain EBITDA/cash-interest cover. The denominator is "cash paid for interest, net" (line 117), and FY2024 net interest is reduced by income on USD 6.3bn of cash. The rise from 2.93x to 3.60x therefore looks like better debt-service capacity when part of it may come from cash yield. The qualification only appears in the folded or adjacent Basis text.
   - Fix: Label the series and column "EBITDA / net cash interest" (or state "net of interest income" in the chart subtitle) so the drawn measure matches its definition.
3. **High · visual** (Auditor, New reader)
   - Where: Chips under each bar: "Handoff ●" and "1 citation without a page" (CP-1_charts.png crop, y~905-935 full-res)
   - Problem: "Handoff" is pipeline vocabulary, which the house standard says must not appear on screen. "1 citation without a page" tells the reader the only citation cannot be traced to a page in the filing, but does not say which source is meant.
   - Fix: Replace the chip with reader language (e.g. "Source") that names the filing and page used for the EBITDA and interest-paid figures.
4. **Medium · narrative** (Saboteur)
   - Where: Lines 113-118: section heading "Chart data: interest cover" followed only by the two-row table
   - Problem: The section gives no judgement. It does not say whether about 3.6x net cash cover is thin or adequate for an issuer at about 6x gross leverage, or that the improvement comes alongside a USD 4.2bn special-dividend accrual. A committee reader gets numbers without a bottom line.
   - Fix: Open with one judgement-first sentence on what the cover level and trend mean for debt-service capacity, then show the table.
5. **Medium · narrative** (New reader)
   - Where: Line 117-118 Basis cells: "Not gross cash-interest or covenant coverage." / "same measure and net cash-interest denominator; full-year flows."
   - Problem: The limitations are telegraphic fragments. They tell the reader what the ratio is not (gross, covenant) without giving the gross or covenant figure or saying which way the difference goes, so the reader cannot judge how much the caveat matters.
   - Fix: State in one plain sentence whether gross or covenant cover would be lower or higher and by roughly how much, or mark it as an explicit gap.
6. **Low · visual** (New reader, Auditor)
   - Where: Interest cover chart header "x · As of 30 September 2024" and the absent y-axis (CP-1_charts.png crop, top-right and plot area)
   - Problem: The only unit is a lone "x" in the card's top-right corner, and the plot has no y-axis or gridline. The "As of 30 September 2024" stamp sits over a chart that also plots FY2023 flows. Two bars take only the left ~60% of the card, leaving a large empty band on the right.
   - Fix: Put the unit next to the series label ("times"), let the bars span the card width, and label the period as "FY2023-FY2024 fiscal years" rather than a single as-of date.
7. **Low · visual** (New reader)
   - Where: CP-1_s-113.png crop: "Reporting unit" column holding only "x", the monospace header "EBITDA / cash interest", and the "Basis" label stacked under each period
   - Problem: A whole column is used for the single character "x". The data header uses a different (monospace) typeface from the other headers. The grey "Basis" under "FY2023" reads like part of the period label rather than a control.
   - Fix: Fold the unit into the value header ("EBITDA / net cash interest (x)"), use one header typeface, and style Basis visibly as a link or drop it when it is empty.

### Sources

Kind: prose/table · handoff lines 4-17 · verdict **BLOCK**

- Narrative: This section is a source inventory, not judgement prose. Its problems are raw file names and hashes where a plain-English list is required, pipeline vocabulary ('handoff', 'pins', 'lineage convention', 'quarantine') on screen, and a meaningless 'context' row.
- Visual: The section has no chart. The table's layout gives most of its width to 64-character hashes and squeezes the 'Use and authority' column, and it sits between the charts and the financial findings.

1. **High · narrative** (Auditor, New reader)
   - Where: lines 8-12, e.g. line 8: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl | d75c469fdb1966dd895c0f6faa6d5179b380d3ed95aa00aca99aa258059edab6 | Primary issuer evidence"
   - Problem: The ruling (decision 7, and line 23) asks for a plain-English source list. This list gives raw pipeline file names (accession numbers, a .jsonl extension, a PDF bookmark file name) and 64-character hashes, so the reader cannot tell which filing is which, or when it was filed, without decoding the strings.
   - Fix: Name each source in words: document type, period, filer and filing date (e.g. 'Form 10-K for fiscal year ended 30 Sep 2024'). Keep the file name and hash reachable through the inspector or Evidence instead of showing them as the main columns.
2. **High · narrative** (Auditor, New reader)
   - Where: line 16: "Source pins match the tool inventory. The supplied upstream handoff is accepted under the transport's lineage convention; no further acceptance receipt is required." and line 14: "Source readiness (CP-0), supplied Markdown handoff"
   - Problem: Pipeline vocabulary appears on screen, and the house standard says it is not reader language: 'handoff', 'pins', 'tool inventory', 'transport's lineage convention', 'acceptance receipt'. The screenshot shows the rendered text 'Source readiness, supplied Markdown handoff' and this whole closing paragraph.
   - Fix: Drop the internal provenance sentence, or replace it with a reader statement such as 'Only the company's own filings were used; no outside research.' Describe the upstream row as the source-readiness review, not as a handoff.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: line 11: "Subsequent-period quarantine inherited from Source readiness; no FY2025 results used."; line 12: "Reproduction classification inherited from Source readiness; not an independent financial observation."; line 9: "no interim amounts promoted"
   - Problem: The 'Use and authority' cells are written in internal classification terms ('quarantine', 'promoted', 'reproduction classification', 'inherited'). A committee member cannot tell what each document was actually used for, or that the December 2024 10-Q postdates the 30 Sep 2024 measurement date.
   - Fix: Say plainly what each document contributes, e.g. 'Filed after the as-of date; not used for figures' or 'Copy of the 10-K; not a separate source'.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 13: "| context | f7b95e1ff471b47547a3ac86cb68e7e7144a06231f6e94de0eee48e0c6828449 | Dated user settings, not issuer evidence. |"
   - Problem: A row named only 'context' with a hash and 'Dated user settings' appears in the source list. It is meaningless to the reader, who could take it for an undisclosed input that affected the analysis.
   - Fix: Remove run settings from the reader's source list, or name what they are in words (e.g. 'Analysis date and scope chosen by the analyst').
5. **Medium · visual** (Auditor, New reader)
   - Where: Sources table, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots/CP-1_s-4.png, region x 355-1390, y 255-1005 (original px)
   - Problem: The sha256 column takes about 40% of the table width with unbroken 64-character strings. This squeezes the only meaningful column, 'Use and authority', into a narrow strip that wraps to 4-5 lines per row. File names also break mid-token at hyphens, which makes the seven-row table about 750 px tall for little reader content.
   - Fix: Remove or collapse the hash column so that the plain-language name and its use get most of the width, with one or two lines per row.
6. **Low · visual** (Auditor)
   - Where: On this page outline and page flow in CP-1_s-4.png (left rail, y≈520-640 original px): 'Bottom line, Charts, Request, Sources, Financials and credit metrics'
   - Problem: The Request echo and a 750 px source-inventory table sit between the charts and the financial findings. This breaks the reader's path from the judgement to its supporting figures.
   - Fix: Place the source list after the analytical sections, at the end of the module, as in the VMO2 reference's separate source list.

### Bottom line

Kind: reader passage · handoff lines 20-26 · verdict **CONCERNS**

- Narrative: The judgement is first and the core figures check against the handoff (25,068/4,173 = 6.01x; 2,045 − 165 = 1,880), but the decisive distribution figures (USD 4,216m + 132m, cash after payment USD 1,913m, FCF after dividends USD -158m) are left out, pipeline readiness language fills half the second paragraph, and a limitation sits inside the bottom line.
- Visual: The section has no chart of its own: it is two paragraphs set entirely in heavy bold with monospace figure chips, taking half the column width, with the heading hidden under the sticky bar after the jump (Basis lines are correctly kept out of the sentences, as data-basis on the figures).

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 21: "Net leverage of approximately 4.51x benefits from cash still held against an accrued distribution; it is not an unqualified measure of creditor protection." and "a large declared distribution remained unpaid"
   - Problem: The bottom line says the 4.51x net leverage is flattered, but it never gives the size of the distribution or the figure after it is paid. The handoff has both: a USD 4,216 million special dividend plus USD 132 million of dividend equivalents, settled 2024-10-18 (line 193), which leaves static cash of USD 1,913 million (C06, line 263). As written, the only net leverage figure a committee member sees is the flattering one, and the caveat only warns them off it.
   - Fix: In the bottom line, state the accrued distribution (USD 4,216m + USD 132m, paid 2024-10-18) and the C06 cash after payment, so the qualification has a number behind it.
2. **High · narrative** (New reader, Auditor)
   - Where: line 24: "The foundation is ready with limitations for annual financial synthesis, not for contractual headroom or a market-relative-value decision."
   - Problem: Half of the second paragraph talks about whether the data is fit for later modules ("foundation", "ready with limitations", "synthesis", "usable historical credit foundation" on line 21), not about the credit. This is pipeline language, and it pushes the reader-facing judgement aside.
   - Fix: Open the paragraph with the credit judgement (coverage up, dividends greater than free cash flow); move the scope statement to the limitations, in reader words ("no covenant headroom or relative-value view is given here").
3. **Medium · narrative** (Saboteur)
   - Where: line 24: "cash dividends and dividend-equivalent payments exceeded internally generated free cash flow. The subsequent payment of liabilities already accrued at year-end demonstrates why liquidity must be examined after committed shareholder uses"
   - Problem: The size of the shortfall (FCF after dividends of USD -158 million, C07, line 264) and the date and amount of the subsequent payment are left out. The paragraph lists C07 in its Basis but never prints the figure, so the reader gets a direction with no magnitude.
   - Fix: Give the USD -158 million FY2024 figure and the dated settlement amount inline, and drop the 'demonstrates why liquidity must be examined' commentary.
4. **Medium · narrative** (Auditor, New reader)
   - Where: line 24: "This is a retrospective FY2024 snapshot using the later-published annual filing, not a representation of the information available to investors on the measurement date."
   - Problem: This limitation sits inside the bottom line, which breaks the house order (bottom line, findings, contrary evidence, limitations). "Measurement date" is internal vocabulary that the reader cannot place.
   - Fix: Move the sentence to the module's limitations and say it plainly ("uses the 10-K filed after 30 September 2024").
5. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-1_bottom-line.png, region x 300-1440, y 180-980 (crop scratchpad/tmp/CP-1-012-a.png)
   - Problem: Both paragraphs (about 180 words) are set entirely in large heavy bold, so nothing stands out: the judgement clause cannot be told apart from the caveats. Mid-sentence monospace figures with dotted underlines break the reading rhythm, and the column fills only about half the width, leaving the right half empty.
   - Fix: Set the bottom line in regular weight, with at most the one-sentence judgement emphasised, and render figures in the body font with a light marker.
6. **Low · narrative** (Saboteur)
   - Where: line 21: "or approximately 6.01x issuer-adjusted EBITDA, versus approximately 5.87x in FY2023. Net leverage of approximately 4.51x"; line 24 "approximately 3.60x"
   - Problem: Each two-decimal ratio carries 'approximately', which hedges figures that are exact calculations (C01–C04) and makes the reader wonder how reliable they are.
   - Fix: Drop 'approximately' from calculated ratios and state the definition once (gross debt / EBITDA As Defined).
7. **Low · visual** (Auditor)
   - Where: Screenshot CP-1_bottom-line.png top edge, y ~180-200 (clipped pill outline at x ~960-1180, under the sticky run bar)
   - Problem: After the anchor jump to 'Bottom line', the section heading and an element beside it are hidden under the sticky 'Showing run' bar, so the reader lands on unlabelled bold text.
   - Fix: Offset the anchor scroll by the sticky header height so the 'Bottom line' heading stays visible.

### Financials and credit metrics

Kind: prose/table · handoff lines 27-71 · verdict **BLOCK**

- Narrative: I recomputed the figures from the table's own rows and they hold: free cash flow 1,880/1,236, net debt 18,807/16,441, leverage 6.01x/5.87x and 4.51x/4.84x, coverage 3.60x/2.93x, and 6.57x. The section still has problems: it opens with notation rules, not a judgement; it exposes internal C-codes and pipeline phrasing; and it shows net leverage improving without the dividend-payable adjustment that its own bottom line says reverses the picture.
- Visual: There is no chart in this section; the visual is a single 37-row, five-column table. Its FY2023 column is misaligned, a repeated two-line file-name Source column dominates the width, and the table has no grouping or thousands separators, so the key credit ratios fall below the first screen.

1. **High · narrative** (Saboteur)
   - Where: line 66: "Net financial debt | 18807 | 16441 | USD million; calculated C02; gross debt less reported cash, no dividend adjustment" and line 68: "Net debt / issuer-adjusted EBITDA | 4.51 | 4.84"
   - Problem: The table shows net leverage improving from 4.84x to 4.51x. The section's own bottom line says this improvement is not real, because cash was still held against an accrued distribution: line 89 shows Dividends payable of USD 4,216m. That caveat is reduced to the words "no dividend adjustment" in a status cell. A committee member scanning the table takes away the opposite of the module's judgement.
   - Fix: Add a dividend-adjusted net debt row and a matching leverage row (with their own unit and basis) next to the reported ones, so the table carries the conclusion stated in the bottom line.
2. **High · narrative** (New reader, Auditor)
   - Where: line 63: "USD million; calculated C08, not a printed subtotal"; line 64 "calculated C05"; line 65 "calculated C01"; line 70 "x; FY2024 denominator sensitivity, C15"
   - Problem: Internal calculation register codes (C01–C15), together with pipeline phrasing such as "printed expense magnitude", "not EBITDA bridge opening" and "reported CFS noncash adjustment", appear on screen. A reader who has not seen the pipeline cannot interpret them. The house rule bars register codes from reader text.
   - Fix: Replace the codes with plain descriptions (e.g. "calculated: SG&A plus amortisation") and keep the calculation identifiers in the Basis/Sources layer only.
3. **Medium · narrative** (Auditor)
   - Where: line 29: "All monetary statement observations below retain the printed amounts in USD million. Positive income-statement expenses and supplemental cash-paid amounts are printed outflow magnitudes..."
   - Problem: The section opens with notation conventions, not a judgement. The reader meets sign rules and a 37-row table before any statement of what the figures mean for credit: leverage up from 5.87x to 6.01x, coverage up to 3.60x, and dividends of USD 2,038m against free cash flow of USD 1,880m.
   - Fix: Open the section with a one-line bottom line on what the table shows for credit, then move the sign and unit conventions to a short note below it.
4. **Medium · narrative** (Saboteur)
   - Where: line 42: "OTHER (INCOME) EXPENSE | -28 | -13 | USD million; printed signed net income within expense block"; line 35 "COST OF SALES | 3268"; line 54 "Capital expenditures | -165"
   - Problem: One table uses three sign conventions. Expenses are positive, cash outflows are negative, and on this expense line a negative number is income. A reader can easily take -28 as a cost, or 3268 and -165 as having opposite cash direction.
   - Fix: Use one sign convention per table, or split the table into labelled income-statement, cash-flow and credit-metric blocks, each with its convention stated once.
5. **Medium · visual** (Auditor, New reader)
   - Where: Table body, FY2023 column; shots/CP-1_s-27.png crop x350–1100, y1750–2400 (tmp/CP-1-013-a.png): "-900", "-38", "-16", "12" share a left edge, while FY2024 is right-aligned
   - Problem: The FY2023 numeric column is left-aligned while FY2024 is right-aligned. Values of different magnitudes and signs (-2441/-900, 25068/19913) do not line up, so year-on-year comparison is slow and error-prone. Promoted because two personas raised it.
   - Fix: Right-align both period columns (tabular figures) to match the alignment the markdown declares (---:).
6. **Medium · visual** (New reader)
   - Where: Source column, every row; shots/CP-1_s-27.png x880–1160: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 121" repeated in about 37 rows
   - Problem: The same 70-character internal file name (with an accession number and a .jsonl extension) wraps onto two lines in every row. It takes about a quarter of the table width, doubles the row height and pushes the 37-row table to over two screens. A "Basis" chip on every label repeats the same information.
   - Fix: Show a short source label (e.g. "FY2024 10-K, p.121") in the Source column and drop the redundant per-row Basis chip, or vice versa.
7. **Low · narrative** (Saboteur)
   - Where: line 70: "Gross debt / issuer-reported EBITDA | 6.57 | Not calculated: comparison uses issuer-adjusted basis"
   - Problem: The FY2023 value is withheld for a reason that does not hold: both inputs are in this table (19,913 and 3,148, about 6.33x). As a result the sensitivity row cannot show its trend.
   - Fix: Either show the FY2023 figure, or give the real reason it is withheld.
8. **Low · visual** (New reader)
   - Where: Table rows lines 34–70, e.g. "NET SALES | 7940", "Gross financial debt ... | 25068 | 19913"; shot y300–2400
   - Problem: Amounts have no thousands separators. All-caps printed labels are mixed with sentence-case labels, and income statement, cash flow and credit ratios all sit in one undivided list, with the key credit ratios at the very bottom, below the first screen.
   - Fix: Use thousands separators, add group subheads (Income statement / Cash flow / Debt and credit metrics), and put the credit-metric rows first or in their own table.

### Chart data: liquidity

Kind: chart · handoff lines 120-126 · verdict **BLOCK**

- Narrative: The section is a two-row data table with no bottom line. Its key limitation, that USD 4,348m of the USD 6,261m 2024 cash was already committed to a dividend paid in October 2024, sits in a vague clause and can lead the reader to the wrong liquidity judgement.
- Visual: The liquidity bar chart is visible and clearly labelled, but it carries banned pipeline chips ("Handoff", "1 citation without a page") that also contradict the cited pages, and the table typography and alignment are inconsistent.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 125: "2024-09-30 | 6261 | 843 | US$m | ... no assumption that accrued distributions are freely retainable." and Liquidity chart, CP-1_charts.png, crop scratchpad/tmp/CP-1-017-a.png
   - Problem: The table and chart show September 2024 cash nearly doubling, from 3,472 to 6,261. The same handoff shows USD 4,216m of special dividend plus USD 132m of dividend equivalents were already accrued and paid on 2024-10-18, which leaves static cash of USD 1,913m (line 263, C06; lines 189 and 193). The only warning is the vague clause "no assumption that accrued distributions are freely retainable", so a reader looking at the chart will think liquidity improved when committed cash is about to leave.
   - Fix: Put the committed USD 4,348m outflow in plain words next to the 2024 figure, as a row or a marked series showing cash after the October settlement, so the chart cannot be read as a liquidity build.
2. **High · visual** (Auditor, New reader)
   - Where: Liquidity chart, CP-1_charts.png region approx x 340-1400, y 1270-1300 (crop CP-1-017-a.png): chips "Handoff ●" and "1 citation without a page" under each period
   - Problem: "Handoff" is pipeline vocabulary the house standard bans from the screen. "1 citation without a page" contradicts the table's Basis column, which cites "Annual filing pages 120 and 152", so the reader is told the figure has no page reference when it has two.
   - Fix: Remove the pipeline chip and show the real source locator (annual filing, pages 120 and 152), or nothing.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: line 120-124: "### Chart data: liquidity" table with columns "Cash | Undrawn committed facilities"; no total
   - Problem: The section is a bare data dump headed with the internal label "Chart data:". It gives no bottom line, and its two series are never added up, although the module computes total liquidity (USD 7,104m in FY2024 against 4,227m) at line 263. The reader has to add the numbers and go looking elsewhere for the judgement.
   - Fix: Give the section a reader heading (for example "Liquidity") and a one-line bottom line with the total and its dividend-adjusted value ahead of the table.
4. **Medium · narrative** (Saboteur)
   - Where: line 124: "Not an all-facility liquidity total." vs line 125: "excludes separately discussed remaining securitization capacity"
   - Problem: The two periods carry different limitation wording. A reader cannot tell whether 2023 also excludes securitization capacity, so the year-on-year comparison is not shown to be like-for-like. The 2024 row also does not give the excluded amount (USD 162.5m, line 194).
   - Fix: Use the same stated basis for both rows, name the excluded facility and give its amount for each date.
5. **Low · visual** (New reader, Auditor)
   - Where: Table "Chart data: liquidity", CP-1_s-120.png region x 340-1400, y 210-440 (crop CP-1-017-b.png)
   - Problem: Column headers "Cash" and "Undrawn committed facilities" render in a monospace face, unlike the other headers. Cash values sit bold under their header while undrawn values are right-aligned far to the right, so the two number columns do not line up. Figures have no thousands separators (6261).
   - Fix: Use one header typeface, right-align both number columns the same way, and format thousands as 6,261.
6. **Low · visual** (Auditor)
   - Where: Liquidity chart, CP-1_charts.png (crop CP-1-017-a.png): x-axis labels "2023-09-30" / "2024-09-30"; plot ends at about 60% of card width
   - Problem: The axis uses ISO dates while the neighbouring charts use FY2023 and FY2024 for the same year-ends. The plot leaves about 40% of the card empty on the right and has no value axis, so comparing scale with the other charts takes extra work.
   - Fix: Label periods consistently with the other charts (for example "30 Sep 2024" or FY2024 year-end) and let the plot fill the card width.

### Chart data: debt stack

Kind: chart · handoff lines 145-162 · verdict **BLOCK**

- Narrative: The figures are internally consistent: the rank-1 rows sum to 19,702, the rank-2 rows add 4,600 for 24,302, and dividing by 4,173 gives 4.72x and 5.82x. But the section gives no judgement first, ends on a caveat-only paragraph, leaves the leverage column without a unit, and cites a .jsonl file and code C14 in its Basis line.
- Visual: The stacked bar's colours cycle without regard to rank, so secured and subordinated tranches share colours, and the bar has no rank divider, segment labels or axis. Every legend row carries a banned "Handoff" chip and a "citations without a page" note that the table's page citations contradict.

1. **High · visual** (Saboteur, Auditor)
   - Where: Debt stack chart, stacked bar and legend swatches, CP-1_charts.png crop x340-1400, y2140-2830 (scratchpad/tmp/CP-1-020-a.png, -b.png)
   - Problem: Segment colours cycle through four colours (blue, navy, grey, slate) in row order and ignore rank. The 2031 Secured Notes and the 4.625% senior subordinated notes due 2029 are the same bright blue, and the 2032 Secured Notes and the 4.875% subordinated notes are the same navy. Nothing on the bar marks where secured debt (rank 1, 4.72x) ends and subordinated debt (rank 2, 5.82x) begins, and the segments carry no amounts and no axis. A reader cannot see the priority structure that the chart exists to show.
   - Fix: Colour each segment by rank or secured status, using one family per rank, and put a labelled divider with the cumulative leverage (4.72x / 5.82x) at each rank boundary.
2. **High · visual** (Auditor, New reader)
   - Where: Every legend row of the Debt stack chart: chip "Handoff ●" and "2 citations without a page" (CP-1_charts.png, right column of rows, y≈2260-2760)
   - Problem: "Handoff" is pipeline vocabulary that the house standard bans from screen. "citations without a page" also contradicts the table, whose Basis column gives "Annual filing pages 58, 145 and 153" for the same rows. That tells the reader the evidence is weaker than it is.
   - Fix: Replace the chip with reader language (for example "Annual filing") and show the page numbers the table already carries.
3. **Medium · narrative** (Saboteur, Auditor)
   - Where: L160 "Equal legal ranks share the same cumulative rank-bucket leverage; ordering pari passu facilities does not create incremental legal priority. This chart omits obligations for which a common legal rank was not established"
   - Problem: The only prose in the section is caveats. There is no bottom line, such as "secured debt alone is 4.72x adjusted EBITDA; through the subordinated notes it is 5.82x". The reader also gets no size for what is omitted, even though the Leverage chart on the same page shows 6.01x total debt / EBITDA for FY2024.
   - Fix: Open with a one-sentence judgement on secured and total ranked leverage, then state the size of the omitted debt (or that it is unquantified) and point to where it is listed, before the limitation.
4. **Medium · narrative** (New reader)
   - Where: L147-149 "Cumulative leverage | Reporting unit" ... "4.72 | US$m"; L149 "Cumulative rank-one debt is USD 19702 million / common FY2024 issuer-adjusted EBITDA"
   - Problem: The leverage column has no unit (x) and no stated denominator. It sits beside a "Reporting unit: US$m" cell, so 4.72 reads as a dollar figure or as each facility's own leverage. The denominator appears only once, buried in row 1 in jargon ("rank-one", "common ... EBITDA").
   - Fix: Head the column "Cumulative leverage (x FY2024 adjusted EBITDA of US$4,173m)" and let "Reporting unit" apply to Amount only.
5. **Medium · narrative** (Auditor)
   - Where: L161 "Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 58; ... calculation C14"
   - Problem: The Basis line shows a raw pipeline file name (.jsonl) and an internal calculation code "C14" that the reader cannot look up. The Basis column inside the table says "Annual filing pages ...", so the section uses two citation styles for the same source.
   - Fix: Cite "Annual report FY2024 (10-K), pages 58, 144-145" and name the calculation in words (secured and total ranked debt / adjusted EBITDA).
6. **Low · narrative** (Auditor)
   - Where: Section heading L145 "### Chart data: debt stack"
   - Problem: "Chart data:" is a production label, not a reader heading. It also appears in the page outline ("Chart data: debt stack") next to the real chart titled "Debt stack".
   - Fix: Title the section for the reader (for example "Debt by legal rank") or fold it into the chart's table form.
7. **Low · visual** (New reader)
   - Where: Table rows L149-158 as rendered, e.g. "8702", "2650", and the Basis column text "USD 19702 million" / "USD 24302 million" (CP-1_s-145.png, Amount column)
   - Problem: Amounts have no thousands separators, and the table repeats the chart row for row while the chart already has a "Table form" fold. The reader gets a second wide 10-row table with a dense Basis column.
   - Fix: Format amounts as 8,702 and so on, and show this table only once, either as the chart's Table form or as the section, not both.

### Earnings, coverage and cash-flow interpretation

Kind: prose/table · handoff lines 174-184 · verdict **BLOCK**

- Narrative: The analysis is sound and the figures match their calculations (C07 -158, C15 6.57x), but the section opens with reconciliation method instead of the judgement. It also omits the comparison figures that would size the earnings-quality and cash-shortfall points, and it uses pipeline instructions ('passed downstream') as its closing voice.
- Visual: This is a prose-only section with no chart. On the page it renders as three full-width dense paragraphs, and only the first has a visible Basis link. The minus sign of -158 also falls outside the highlighted figure chip, which misleads anyone reading the highlighted values.

1. **High · narrative** (Saboteur + Auditor (promoted from Medium))
   - Where: L176: "The operating expense reconciliation is complete for the by-function income statement: cost of sales is above gross profit, while selling and administrative expenses and intangible amortisation exhaust the intervening block..."
   - Problem: The section opens with how the income statement was reconciled, not with a credit judgement. The conclusion that matters (FCF after distributions was negative and adjusted EBITDA flatters leverage) comes only in paragraphs 2 and 3. That breaks the judgement-first order, and a skimming reader gets method before view.
   - Fix: Open with the credit judgement (distributions exceeded free cash flow and add-backs flatter leverage), then the findings, and move the reconciliation mechanics to a Basis/method note or the calculations table.
2. **High · narrative** (Saboteur + New reader (promoted from Medium))
   - Where: L182: "Using unadjusted issuer-reported EBITDA instead raises FY2024 gross leverage to approximately 6.57x."
   - Problem: The sentence says leverage 'raises' to 6.57x but never gives the adjusted figure it rises from (25068/4173, about 6.0x). It also gives no add-back total (USD 360m) and no coverage figure, even though the heading promises coverage. The reader cannot size the earnings-quality gap without leaving the section.
   - Fix: State both leverage figures and the add-back amount side by side (adjusted vs unadjusted, FY2024, x), along with the cash interest cover value this section interprets.
3. **Medium · narrative** (Auditor + New reader)
   - Where: L182: "so the stronger earnings measure must not be passed downstream as a legal-capacity fact"; L176: "Total depreciation and amortisation must not replace the intangible-amortisation line in this reconciliation."
   - Problem: These are pipeline instructions to later modules ('passed downstream', 'must not replace'), not reader language. A credit committee member is being told what the pipeline may do rather than what the evidence means.
   - Fix: Rephrase as a reader-facing limitation, e.g. that neither EBITDA measure is the covenant definition, so capacity under the debt documents is not established here.
4. **Medium · narrative** (Saboteur)
   - Where: L179: "FY2024 free cash flow after cash distributions was USD -158 million, even before acquisitions. Financing inflows, not free cash flow alone, explain the rise in reported cash."
   - Problem: The negative figure appears without its components (FCF USD 1,880m less distributions USD 2,038m), and the financing inflows that explain the cash rise are not quantified. The reader cannot tell whether the shortfall is marginal or structural.
   - Fix: Give the FCF and distribution amounts that make up the -158 and the size of the financing inflow, with period and unit.
5. **Medium · narrative** (Auditor)
   - Where: L176-L183: section has bottom-line-like assertions only; no contrary evidence, what-would-change-the-view or limitations block
   - Problem: The section never says what would change its view, for example evidence that the add-backs are non-recurring or that distributions are one-off (the FY2024 special dividend). It also does not separate contrary evidence from limitations as the house order requires.
   - Fix: Add a short contrary-evidence / what-would-change-the-view sentence (e.g. that the FY2024 special dividend may be non-recurring) after the findings, and then the limitations.
6. **Medium · visual** (Auditor)
   - Where: Screenshot CP-1_s-174.png, section top (approx. x 340-1400, y 215-490 at full res); DOM CP-1.dom.html paragraphs for L179 and L182
   - Problem: Only the first paragraph shows a trailing 'Basis' link. Paragraphs 2 and 3 have none, because their basis is attached only to the figure buttons, so the reader has no visible Basis line for those judgements.
   - Fix: Render a visible Basis link at the end of every paragraph that has a Basis line, whether or not a figure button also carries it.
7. **Medium · visual** (Saboteur + New reader)
   - Where: Screenshot CP-1_s-174.png, paragraph 2, 'USD -158 million' (DOM: 'USD -' as plain text, then a button holding '158 million')
   - Problem: The minus sign sits outside the monospace figure chip, so the highlighted number reads as a positive '158 million'. That reverses the sign of the key cash-flow figure for anyone scanning the highlighted values.
   - Fix: Include the sign inside the figure chip (e.g. '-158 million' or '(158) million') so the highlighted value carries its sign.
8. **Low · visual** (New reader)
   - Where: Screenshot CP-1_s-174.png, three full-width paragraphs (approx. y 215-490), lines of about 1,050 px / 25+ words
   - Problem: Three dense, unbroken paragraphs run the full content width with no lead sentence emphasis or sub-points. The line length is well beyond comfortable reading, and the section reads as a wall of text.
   - Fix: Cap the prose measure (about 75-90 characters) and lead each paragraph with a bold or short judgement sentence.

### Non-debt funding and event stories

Kind: prose/table · handoff lines 185-206 · verdict **BLOCK**

- Narrative: The section is a table register with no judgement-first lead. Internal IDs, a calculation code (C06) and pipeline meta-language leak to the reader, and the sources are given three times.
- Visual: There is no chart; it is a two-table layout. Filenames wrap to five lines in the Source column, digits inside the accession number are rendered as clickable figure buttons, and the duplicate source table makes the section about twice as long as it needs to be.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Lines 187-194 (whole section): the table opens immediately with "| F-DIV24: dividends payable | 2024-09-30 instant | USD 4216 million is a current non-debt claim already declared..."
   - Problem: The section never gives a judgement. A committed cash call of about USD 4.35bn after year-end (the 4216 special dividend plus 132 of dividend equivalents) and a USD 162.5m post-period securitization draw are spread across six table rows with no lead sentence saying what they mean for liquidity and leverage. This is the most material credit fact in the section, and it is left buried.
   - Fix: Open the section with one judgement-first sentence on what the after-year-end distribution and debt draw do to September cash and leverage, then the table as support.
2. **High · narrative** (New reader, Auditor)
   - Where: Line 193: "C06 subtracts only these specified payments from reported cash as a static illustration"; line 196: "The register's source column is supplied below to retain row-level locators."
   - Problem: Internal calculation codes (C06) and pipeline wording ("story register", "row-level locators") reach the reader. Both are house-rule breaches that the reader cannot interpret.
   - Fix: Name the calculation in plain words ("cash after the October dividend payments") and delete the meta-sentence about supplying locators.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: Line 187-194 row labels: "F-DIV24", "F-DIV23", "F-TAX24", "F-TAX23", "E-DISTRIBUTION", "E-SECURITIZATION"; column "Story / reviewed observation"
   - Problem: Internal story IDs and the 'story / reviewed observation' framing are pipeline vocabulary. A PM has to decode the prefixes before reading the row.
   - Fix: Label rows with plain item names and dates (e.g. "Dividends payable, 30 Sep 2024") and title the column "Item".
4. **Medium · narrative** (Saboteur)
   - Where: Line 190: "Source prints a dash, represented as zero in the reported balance sheet... FY2024 distributions demonstrate that a year-end zero is not a prospective covenant restriction."
   - Problem: The row turns a printed dash into a zero, which goes against the missing-is-not-zero rule. It then draws a covenant inference that has nothing to do with the line item, which confuses rather than informs.
   - Fix: State that FY2023 dividends payable were printed as nil (dash) and drop the unrelated covenant inference, or support it with covenant evidence.
5. **Medium · narrative** (New reader, Auditor)
   - Where: Lines 196-205: "Source for every row in the preceding story register: ..." followed by a second Story | Source table repeating the Source column of lines 189-194
   - Problem: Every source appears three times: in the main table's Source column, in the paragraph and in a duplicate six-row table. This doubles the section's length and adds nothing.
   - Fix: Keep the Source column in the main table and remove both the paragraph and the duplicate table.
6. **Medium · visual** (Auditor, New reader)
   - Where: Screenshot CP-1_s-185.png, paragraph under the table (approx. y 1010-1070 full-res): "10-K_0001260221-24-000083" and "page 120" rendered as highlighted figure buttons; DOM shows <button class="figure" data-basis="[]">0001260221</button>
   - Problem: Digits inside the filing filename are styled as clickable figures with an empty basis. The accession number looks like a verified number, and clicking it leads nowhere.
   - Fix: Exclude source filenames and accession numbers from figure detection so only analytical numbers become figure buttons.
7. **Medium · visual** (New reader)
   - Where: Screenshot CP-1_s-185.png, main table Source column (approx. x 1210-1370, y 300-1000 full-res)
   - Problem: The raw filename wraps over five lines in every row, which makes each row twice as tall as its content needs. A grey "Basis" chip also sits after each row label, so the row label column looks cluttered.
   - Fix: Show a short source label ("10-K FY2024, p.120") with the full filename on hover, and keep the Basis chip out of the label text.
8. **Low · narrative** (Saboteur)
   - Where: Line 189: "USD 4216 million ... no double-counting with financial debt is appropriate"; line 193 "USD 4216 million special dividend and USD 132 million"
   - Problem: The large figures have no thousands separator, and "no double-counting ... is appropriate" is ambiguous about what to do with the claim.
   - Fix: Write "USD 4,216 million" and say directly that the claim is a cash use and is not to be added to debt.

### Source context and binding

Kind: prose/table · handoff lines 207-219 · verdict **BLOCK**

- Narrative: The section is written as an internal data-provenance log, with pipeline and tool vocabulary, raw filenames, no judgement-first sentence and a module code in the Basis line, not as reader-facing credit prose.
- Visual: The section has no chart. The four-column table's last column is clipped at the right edge with no scroll cue, and the wrapped raw filenames make the remaining columns dense and tall.

1. **High · narrative** (Auditor, Saboteur)
   - Where: line 217: "Extraction here is from located text with read_pages; extract_statements and the typed book assembler are unavailable. Consequently every observation is manually read, not an extract_statements raw-value record."
   - Problem: Internal tool and pipeline names (read_pages, extract_statements, typed book assembler) reach the reader, which the house standard forbids. The point that matters for credit, that every figure was read by hand with no automated extraction check, sits near the end of the paragraph in tool jargon.
   - Fix: Open the paragraph with a plain-language judgement, for example that all figures were hand-read from the audited FY2024 10-K and how much confidence that supports, and drop the tool names.
2. **High · visual** (Auditor, New reader)
   - Where: Source context and binding table, 4th column 'Extraction suitability and version relationship'; CP-1_s-207.png region x 340-1440, y 220-880 (crop CP-1-024-a.png)
   - Problem: The fourth column is cut off at the card's right edge. The header reads 'Extraction suitability and v' and every cell is truncated mid-word ('Primary audited annual sou', 'does not replace the prima'), with no visible scroll affordance. The column that says which sources are primary, inherited or quarantined cannot be read.
   - Fix: Fit the table to the content width by wrapping or narrowing the long Source column, or show a visible horizontal scroll cue, so all four columns are readable without hidden overflow.
3. **Medium · narrative** (New reader, Auditor)
   - Where: lines 212-215: "Upstream located substring: …" / "Inherited assessment only; quarantined." / heading line 207 "Source context and binding"
   - Problem: The column header and cells use pipeline vocabulary ('upstream', 'located substring', 'inherited assessment', 'quarantined', 'binding') that a portfolio manager cannot interpret. The reader is not told plainly that the December 2024 10-Q falls after the 30 September 2024 as-of date and is kept out of the baseline for that reason.
   - Fix: Rename the heading and column headers in reader language (for example 'Sources used and their role') and state each source's role directly (primary, supporting, or post-period and excluded).
4. **Medium · narrative** (Saboteur)
   - Where: lines 209-217 (section as a whole): table followed by "All financial scopes use the same perimeter string…"
   - Problem: The section has no judgement-first sentence. It opens on a four-column table of raw file identifiers, and the takeaway (one consolidated U.S. GAAP USD-million perimeter, FY2024 10-K primary, interim and PDF copies not independently checked) has to be pieced together from the cells.
   - Fix: Lead with a one- or two-sentence bottom line on source fitness before the table.
5. **Medium · narrative** (Auditor)
   - Where: line 218: "Basis: TDG_2024-09-30_10-K_…, pages 120–124; Source readiness (CP-0)"
   - Problem: The Basis line carries the module code 'CP-0', and the rendered button's data-basis passes it through unchanged ('Source readiness (CP-0)'), so it shows to the reader when Basis is opened. Module codes must not appear on screen.
   - Fix: Reference the module by its reader name only ('Source readiness').
6. **Medium · visual** (New reader)
   - Where: Source column, all five rows, e.g. line 211 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 124"; CP-1-024-a.png left column
   - Problem: The source names are raw machine filenames (accession numbers, .jsonl extensions) that wrap over two or three lines. They take up the widest column and help push the meaningful fourth column off-screen.
   - Fix: Show short reader labels such as 'FY2024 10-K, p.124' or 'Q2 FY2024 10-Q' and keep the full identifier in the Basis popover.
7. **Low · narrative** (New reader)
   - Where: line 211: "Instants 2024-09-30 and 2023-09-30 have no duration start."; line 217: "perimeter string"
   - Problem: 'Instants', 'duration start' and 'perimeter string' are data-modelling terms that do not tell a committee member anything they can use.
   - Fix: Say plainly that balance-sheet figures are as of 30 September 2024 and 30 September 2023, and that the consolidation scope is the group and its subsidiaries.

### Definition and readiness register

Kind: prose/table · handoff lines 220-241 · verdict **BLOCK**

- Narrative: The section is a pipeline readiness checklist, not credit narrative: there is no bottom line, \"Addressed\" opens almost every row, and a routing table follows that is full of internal gap codes and \"consumer\" wording.
- Visual: The section has no chart, only two bordered tables. They are legible with clean spacing, but the raw filenames in the Source column wrap over several lines and make the rows too tall, and an unexplained 'Basis' chip clutters every label cell.

1. **High · narrative** (Auditor, New reader)
   - Where: L233-235: "| Requested consumer | Requirement-by-requirement sufficiency | Command / required action |" ... "Retain G-TIME, G-PERIMETER, G-GOV and G-DETAIL."
   - Problem: The second table is written as pipeline routing. It uses "consumer" as a column header and as "Consumer-specific" (L235, L240), the header "Command", and internal gap codes (G-TIME, G-PERIMETER, G-DEBT, G-LEGAL, G-MARKET, G-TOOLS, G-DETAIL, G-GOV) that are never defined on screen. The rendered DOM confirms they reach the reader (G-PERIMETER appears 6 times). This breaks the house rule against pipeline vocabulary and register codes.
   - Fix: Remove this module-to-module routing table from the reader page, or rewrite it as 'What this supports / what it cannot support' and name each gap in plain words.
2. **High · narrative** (Saboteur, Auditor)
   - Where: L224-231: "Addressed; positive common annual denominator..." / "Addressed historically..." / "Addressed by grouped action list below."
   - Problem: The section has no bottom line. Seven of eight rows open with "Addressed", which reads as a compliance checklist and invites the committee to treat leverage, liquidity and covenants as cleared. The restrictions that actually limit the credit view sit in the third column: not covenant leverage, no numeric covenant headroom, executed definitions absent. Nothing states the judgement first.
   - Fix: Open with one sentence saying what the financial foundation can and cannot support for a credit decision (for example, historical leverage and coverage are usable, covenant headroom is not verified), then the table.
3. **Medium · narrative** (Auditor, Saboteur)
   - Where: L230: "| Key gaps | Addressed by grouped action list below. | Unknown items remain restricted rather than set to zero. | context, page 1 |"
   - Problem: "context, page 1" is not a source document the reader can find. It is an internal input reference shown in the Source column. The row also says "Addressed" for gaps that are, by definition, unresolved. Both items were promoted to Medium because two personas caught them.
   - Fix: Cite a real document in the Source column (or show it as 'not applicable'), and label the row as open gaps, not 'Addressed'.
4. **Medium · narrative** (New reader)
   - Where: L224: "Addressed; positive common annual denominator; gross principal includes term loans..."; L228: "Whole-pack equivalence and uninspected interim/PDF cells are not certified."
   - Problem: The assessments use internal and process language that a portfolio manager cannot read without the pipeline: "positive common annual denominator", "Whole-pack equivalence", "bounded starting point", "bounded trace challenge" (L239), "Source pins". The cells describe how the extraction was done, not what it means for credit.
   - Fix: Restate each cell in credit terms, saying what the measure includes and what it leaves out, and drop the extraction-process wording.
5. **Medium · visual** (New reader, Auditor)
   - Where: Definition and readiness register table, Source column, CP-1_s-220.png around x 930-1160, y 225-900 (displayed scale)
   - Problem: Each Source cell repeats the full raw filename 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl', which wraps across 3-5 lines mid-token. For Coverage, Liquidity and Definition risks it appears twice in one cell. This doubles the row heights, and the source column becomes the visually dominant column. The '.jsonl' extension is internal file plumbing that the reader never needs to see.
   - Fix: Show a short document label (for example 'FY2024 10-K, pp. 144-145') and merge repeated pages of the same document into one citation.
6. **Low · narrative** (Saboteur)
   - Where: L225: "pages 71–71"; L227: "pages 63–63"
   - Problem: Degenerate page ranges look like generation artefacts and weaken trust in the citations.
   - Fix: Print a single page as 'page 71' and 'page 63'.
7. **Low · visual** (New reader)
   - Where: Both tables, first column: 'Leverage Basis', 'Fundamental credit synthesis (Fundamental credit) Basis', CP-1_s-220.png around x 300-460
   - Problem: An unexplained grey 'Basis' chip sits after every row label. In the second table the labels are tautological, e.g. 'Fundamental credit synthesis (Fundamental credit)' and 'Committee challenge (Committee decision)'. Both add noise to a narrow column.
   - Fix: Use a single plain section name per row and make the Basis affordance self-explanatory (an icon with a tooltip, or one legend line).

### Calculations

Kind: prose/table · handoff lines 252-277 · verdict **BLOCK**

- Narrative: This is a data section, and it owes the reader a bottom line it never gives: it opens with engine jargon, buries the rounded figures behind 38-digit outputs and formats numbers inconsistently. The arithmetic itself checks out: C01, C06, C10, C11, C12, C14, C16, C17 and C18 all recompute to the stated results.
- Visual: The section has no chart; it renders as a 4-column table, made tall and dense by repeated raw .jsonl source identifiers that wrap over several lines. Every row also has a Basis button whose payload is empty in the rendered DOM.

1. **High · narrative** (Saboteur, New reader)
   - Where: Line 260 (C03): "FY2024 3.6036269430051813471502590673575129534x; FY2023 2.9267241379310344827586206896551724138x; display 3.60x / 2.93x". The same pattern appears in C04 (l.261), C14 (l.271), C15 (l.272) and C19 (l.276).
   - Problem: The Result column leads with 38-digit kernel output and puts the figure a committee would quote last. In C04 four such strings run together before "Displays 6.01x / 5.87x and 4.51x / 4.84x", so gross and net, and FY2024 and FY2023, are hard to pair, and a reader can misread which leverage is which. C19 gives the EBITDA margin only as a 38-digit fraction (0.5255...) and never as a percentage.
   - Fix: Show the rounded reader figure first (6.01x gross FY2024, 52.6% margin) and move the full-precision values to the calculation JSON or a fold.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 254: "The Decimal-38 kernel was used for every new arithmetic result... Ratios are fractions returned by the kernel, displayed as times where appropriate"
   - Problem: The section opens with pipeline vocabulary ("Decimal-38 kernel", "returned by the kernel", "operands", "instants"), which the house standard excludes from reader language. It also gives no judgement: nothing tells the reader what the calculations show, for example that every reconciliation ties to printed figures or that FY2024 FCF after dividends was negative.
   - Fix: Open with one plain sentence on what the reconciliations establish (all tie to the 10-K; leverage 6.01x gross, 4.51x net on adjusted EBITDA), then state periods and units without the engine vocabulary.
3. **Medium · narrative** (Saboteur)
   - Where: Line 258 (C01): "FY2024 USD 25,068 million; FY2023 USD 19913 million". Also C05 "USD 1,880 million; FY2023 USD 1236 million" and C09 "USD 4,173 million; FY2023 USD 3395 million"
   - Problem: Thousands separators are used for some figures and not others, sometimes in the same cell. On a page this dense, this makes FY2024 and FY2023 magnitudes harder to compare at a glance.
   - Fix: Use one number format throughout (USD 19,913 million).
4. **Medium · narrative** (Saboteur)
   - Where: Line 272 (C15): "Gross debt / issuer-reported unadjusted EBITDA = 25068 / 3813 ... display 6.57x" alongside C04 6.01x and C14 "through subordinated ... 5.82 times"
   - Problem: The section shows three leverage figures for the same date (6.01x, 6.57x, 5.82x). Their definitional differences sit in the Source column ("Definition sensitivity", "excludes unranked obligations"), so a reader scanning the Result column can pick the wrong headline figure. C14 also writes "times" where the other rows write "x".
   - Fix: State which leverage figure is the headline and put each alternative's basis next to its result, with one unit convention (x).
5. **Medium · visual** (Auditor, New reader)
   - Where: Calculations table, Source column, CP-1_s-252.png, x≈1140-1390, y≈370-2400 (e.g. C06 cites the same file three times, about 12 wrapped lines)
   - Problem: The Source column repeats the raw file identifier "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl", broken across lines, in every row. This makes each row 4 to 12 lines tall, and the internal .jsonl extraction name is not language a reader knows. C14 also cites "pages 145–145".
   - Fix: Cite "FY2024 10-K, p. 144–145" (with the full identifier in ## Sources) so rows collapse to two or three lines.
6. **Medium · visual** (Auditor)
   - Where: Every row's ID cell, under C01 to C19: a "Basis" button. The DOM (render/CP-1.dom.html) shows data-basis="[]" for all 19 rows.
   - Problem: Each row shows a Basis control, but its basis payload is empty for every row. The reader gets an affordance that promises provenance and appears to have none behind it, which is a fake-looking control. It also repeats the Source column.
   - Fix: Hide the Basis button when its payload is empty, or fill it with the row's source pins.
7. **Low · visual** (New reader)
   - Where: Calculations table, Definition column, CP-1_s-252.png, e.g. C16/C11 "7940 - 3268 - 980 - 161 - 1286 - 58 + 28; 6585 - 2743 - ..."
   - Problem: FY2024 and FY2023 operand chains share one cell with only a semicolon between them, and the inline chips ("C01") are rendered in a smaller monospace inside the prose. The table reads as an audit dump, not something a committee member can scan.
   - Fix: Split FY2024 and FY2023 into separate lines or columns, and keep the operand chains for the evidence layer.

### Supplemental bridge observations

Kind: prose/table · handoff lines 278-288 · verdict **BLOCK**

- Narrative: This is a bare data table with no bottom line. Its sources are internal extract file names, and it mixes full-year add-backs with year-end balances under the same FY headers. The reader gets six numbers and no judgement.
- Visual: The table is legible: the figures are right-aligned and the rows are spaced evenly. But the Source column is wide and wraps file names onto two lines, every row label carries a 'Basis' link with nothing behind it (empty data-basis), and the repeated unit text adds clutter.

1. **High · narrative** (Saboteur, New reader)
   - Where: Line 278-280: '### Supplemental bridge observations' followed directly by '| Label | FY2024 | FY2023 | Unit / purpose | Source |' (no sentence before or after the table)
   - Problem: The section is a table with no bottom line, so the reader is never told what it means. Two moves go unremarked: non-cash compensation of 217 out of 360 total adjustments (about 60%) inflates adjusted EBITDA, and dividend-equivalent accruals rose from 19 to 180. A committee member skimming the page takes no judgement away from it.
   - Fix: Open with one judgement-first sentence, for example on how much of the 360 add-back is non-cash compensation and what the 180 dividend-equivalent accrual means for near-term cash. The table should then support that sentence.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 282: 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 71' (repeated in all six Source cells, lines 282-287)
   - Problem: The Source column shows the pipeline's internal extract file name, including the '.jsonl' suffix and the accession-number string. This is pipeline wording, not a reference a reader can use. The 'page' is the extract's page number, so the reader cannot match it to the printed 10-K.
   - Fix: Render the source as a reader citation such as 'TransDigm FY2024 10-K, non-GAAP reconciliation (p. 71)' and keep the file identity in the Evidence page.
3. **Medium · narrative** (Saboteur)
   - Where: Line 286: 'Dividend equivalent payments, current | 180 | 19 | USD million; accrued liability detail; only USD 132 million is specified as October payment'
   - Problem: The row says only 132 of the 180 is specified as an October payment. It leaves the other 48 unexplained, and it does not say this is a near-term cash outflow to shareholders on top of the September cash balance. The caveat creates doubt but gives no view.
   - Fix: State what the 48 balance is, or say plainly that it is unknown, and say whether the 180 should be treated as a committed near-term cash use against liquidity.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Lines 280-287: header 'FY2024 | FY2023' applied both to 'reported adjustments' rows (282-285) and to 'accrued liability detail' / 'Contract liabilities, current' rows (286-287)
   - Problem: One table mixes full-year income-statement add-backs with balance-sheet amounts at 30 September under the same 'FY2024/FY2023' headers. The four adjustment rows also never say what they adjust: adjusted EBITDA, from 3,813 to 4,173. A reader can confuse a flow with a year-end balance and cannot see that the four rows sum to the 360 adjustment.
   - Fix: Split the table into 'Adjusted EBITDA add-backs (full year)', with a total row, and 'Other year-end liabilities (at 30 Sep)', or label the period basis on each row.
5. **Medium · visual** (Auditor, New reader)
   - Where: Screenshot CP-1_s-278.png, table region (approx. x 300-1160, y 410-690 displayed); DOM shows each row's 'Basis' button with data-basis="[]"
   - Problem: Every row label carries a 'Basis' link, but its basis list is empty, so the link opens nothing. It also duplicates the Source column next to it. A reader who clicks it expecting evidence gets none, and the extra word clutters each label.
   - Fix: Show the Basis link only when it has content. Where the Source column already carries the reference, drop it.
6. **Low · narrative** (New reader)
   - Where: Line 278: '### Supplemental bridge observations'
   - Problem: 'Bridge observations' is analyst or pipeline shorthand. The heading does not tell a portfolio manager these are EBITDA add-backs and year-end liabilities.
   - Fix: Use a descriptive heading such as 'Adjusted EBITDA add-backs and other year-end liabilities'.
7. **Low · visual** (New reader)
   - Where: Screenshot CP-1_s-278.png crop CP-1-028-a.png: column header 'Label' and the 'Unit / purpose' column repeating 'USD million; reported adjustments' four times
   - Problem: 'Label' is a generic header, and the unit is repeated in every row instead of once in the header. The long two-line file-name Source cells take about a third of the table width, and the 'Unit / purpose' column mixes the unit with commentary.
   - Fix: Name the first column by its content, put 'USD million' in the figure headers, and keep the commentary in a short note column.

### Gaps

Kind: prose/table · handoff lines 289-302 · verdict **BLOCK**

- Narrative: The Gaps table is accurate and careful about missing versus zero, but it is written as analyst and pipeline instructions under internal G-codes. It has no judgement-first line saying the committee cannot conclude on covenant headroom, relative value or recoveries, and one row (G-TOOLS) is pure pipeline vocabulary.
- Visual: The section is a single four-column table with no chart. It reads cleanly at 1440 px, but the Source column is bloated by wrapped .jsonl file names, Basis buttons with empty basis lists appear inconsistently in the severity cell, and severity is not scannable.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 300: "prepare_invocation.py, validate_handoff.py, confidence_score.py, completeness_check.py and other scripts not run: unavailable. extract_statements, companion schemas, retained typed ledgers, narrative/readiness projections and quality-scope block unavailable." Rendered verbatim (shot CP-1_s-289.png, G-TOOLS row, y~1545-1680).
   - Problem: The whole G-TOOLS row is internal pipeline language: script file names, "handoff", "schemas", "invocation digest", "quality-scope block". It breaks the house rule against pipeline vocabulary, and a portfolio manager cannot tell from it what limits the credit view.
   - Fix: Restate the row as its effect on the reader, e.g. that the figures were checked by hand against the filing and no automated completeness score exists, or drop the row from the reader page.
2. **High · narrative** (Saboteur, New reader)
   - Where: Line 293: "G-LEGAL / critical for legal conclusions ... Does not block annual reported financial analysis."; line 294: "G-MARKET / critical for relative value"
   - Problem: Covenant headroom and relative value cannot be judged at all on this run. That is a decision-critical consequence, but it sits in the first cell under internal codes (G-LEGAL, G-MARKET) and ends on a reassurance. Nothing gives a judgement-first line on what the committee can and cannot conclude.
   - Fix: Put one plain bottom-line sentence before the table naming which conclusions are unsupported (covenant capacity, relative value, recoveries), and replace the G-codes with plain labels.
3. **Medium · narrative** (Auditor)
   - Where: Line 295: "All baseline financials and consumers"; header line 291 "Affected values, periods and recipients"; line 300 "All observations and downstream auditability"
   - Problem: "consumers", "recipients" and "downstream" are pipeline terms for other modules, not reader language. The rendered page swaps module codes for names, but the column still describes routing between modules rather than the effect on the credit view.
   - Fix: Rename the column to something like "What it affects" and list the analyses or conclusions affected, not the modules that receive the gap.
4. **Medium · narrative** (New reader)
   - Where: Line 298: "Do not assume missing figures zero. Obtain targeted supporting schedules for runway/FFO, tax timing, noncurrent funding, cash restrictions and add-back recurrence ... perform targeted reads if subsequently required."
   - Problem: The cells read as instructions to an analyst or agent ("Obtain", "perform targeted reads", "omit from ranked chart"), not as findings for a committee reader. They pack undefined shorthand (FFO, RCF, house EBITDA) into 60-word cells.
   - Fix: Write each row as the limitation and its consequence for the view in one or two short sentences, with abbreviations spelled out on first use.
5. **Medium · visual** (Auditor, Saboteur)
   - Where: Gaps table, Gap / severity column, shot CP-1_s-289.png rows G-MARKET to G-GOV (y~880-1520 in the displayed image); DOM data-basis="[]" on every Basis button in this table
   - Problem: Seven rows carry a "Basis" button whose basis list is empty, and three rows (G-LEGAL, G-TOOLS, G-PRIOR-VERSION) have none. The reader gets a control that appears to lead nowhere, placed inconsistently inside the severity cell.
   - Fix: Show a Basis control only when it has content, or remove it from rows that already carry a Source column.
6. **Medium · visual** (New reader)
   - Where: Gaps table, Source column, shot CP-1_s-289.png G-DEBT and G-DETAIL rows (y~1140-1440 in the displayed image): "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 144–145"
   - Problem: The raw extraction file name, ending in .jsonl, is broken over 6 to 8 lines in a narrow column. That makes these rows the tallest on the page and shows an internal artifact name instead of "FY2024 10-K".
   - Fix: Show sources as a short human label (e.g. "10-K FY2024, pp. 144–145") with the full identity kept in Sources or a tooltip.
7. **Low · visual** (New reader)
   - Where: Gaps table, Gap / severity column, shot CP-1_s-289.png (all rows): "G-PRIOR-VERSION / bounded inherited gap" wrapped over four lines
   - Problem: The severity text is fused with the code and wraps in a narrow first column, so severity cannot be scanned. "bounded", "inherited" and "execution limitation" are not a reader-meaningful scale.
   - Fix: Show severity as a separate short chip (Critical / Material / Minor) in its own column, and order the rows by it.

### Chart data: debt maturities

Kind: chart · handoff lines 127-137 · verdict **BLOCK**

- Narrative: The section is a bare data table under an internal 'Chart data' heading with no bottom-line sentence. Its exclusions (finance leases, securitization) and fiscal-year convention sit only in the basis cells, and the FY2027 bucket looks inconsistent with the debt stack's 'due 2027' notes on the same page.
- Visual: The chart is visible and correctly ordered with data labels, but it shows 'Handoff' chips and '1 citation without a page' that contradict the paged source. It also draws the multi-year 'Thereafter' bucket like a single year and has no value axis, so the FY2025-FY2027 bars are hairlines.

1. **High · visual** (Auditor, Saboteur)
   - Where: Debt maturities chart, CP-1_charts.png crop (340,1340)-(1400,1730): a 'Handoff' chip and '1 citation without a page' under each of the six bars. The table row at line 131 cites 'Annual filing page 153'.
   - Problem: The chips put pipeline vocabulary ('Handoff') on screen, which breaks the house rule. They also say every bar's citation has no page, yet the FY2025 basis names page 153. A committee reader is told the figures are weakly sourced when they come from one paged schedule.
   - Fix: Label the chip with a reader term such as 'Annual filing p.153', and carry the page through to every row so no bar is reported as unpaged.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: line 133: "FY2027 | 92 | US$m | Same schedule; the notes maturing in November 2027 fall in FY2028."
   - Problem: On the same page, the debt stack lists '5.50% senior subordinated notes due 2027' at USD 2,650 million, but the maturity chart shows only USD 92 million in FY2027. The fiscal-year end (30 September) is never stated, and the only reconciliation sits in one basis cell that the chart does not show, so a reader sees two figures that seem to disagree.
   - Fix: State once, above the table and in the chart subtitle, that fiscal years end 30 September, so the November 2027 notes fall in FY2028.
3. **Medium · narrative** (Saboteur)
   - Where: line 131: "reported long-term debt principal schedule excludes finance leases and short-term securitization." and line 132: "not a complete all-obligation maturity wall."
   - Problem: Near-term buckets are understated by unquantified exclusions: short-term securitization would fall in FY2025, which shows only USD 93 million. The section gives no total, and its row sum (USD 24,319 million) is never tied to the gross debt behind the 6.01x leverage, so the reader cannot judge how large the gap is.
   - Fix: Add a total row and state, in dollars, the excluded finance-lease and securitization amounts and their likely bucket, or say explicitly that they are unavailable.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 127: "### Chart data: debt maturities", followed directly by the table (lines 129-136) with no lead sentence
   - Problem: The heading is internal ('Chart data'), and the section opens with a raw table without a judgement. The reader is not told the key point: little matures before FY2028, about USD 6.6 billion falls due in FY2028, and FY2024 cash of USD 6,261 million is the relevant comparison.
   - Fix: Rename the heading to a reader title such as 'Debt maturities by fiscal year', and open with a one-sentence bottom line on the first material maturity and how it compares with liquidity.
5. **Medium · visual** (Saboteur, New reader)
   - Where: Debt maturities chart, 'Thereafter' bar labelled 12637, CP-1_charts.png crop right-hand bar
   - Problem: The 'Thereafter' bar combines several years but is drawn at the same width and style as each single fiscal year. As the tallest bar, it reads as a USD 12.6 billion single-year wall after FY2029. The 'not disaggregated' caveat (line 136) appears only in the table, not on the chart.
   - Fix: Draw the 'Thereafter' bar in a distinct style (hatched or separated) and give it a label such as 'FY2030 and later (cumulative)'.
6. **Low · visual** (Auditor)
   - Where: Table 'Chart data: debt maturities', CP-1_s-127.png region y≈215-470: the 'Debt maturing' header in monospace while the other headers are sans-serif; a 'Basis' link after every Period value, wrapping under 'Thereafter'
   - Problem: Header typography is mixed, and the repeated 'Basis' link inside the Period cell wraps and clutters the first column. This duplicates the 'Basis and limitation' column, which already carries the source.
   - Fix: Use one header typeface and move the per-row Basis link into the basis column (or drop it), so the Period column holds only the period.
7. **Low · visual** (Auditor)
   - Where: Debt maturities chart, CP-1_charts.png crop: no y-axis or gridlines; the FY2025-FY2027 bars render as hairlines
   - Problem: There is no value axis, and the first three bars are near-invisible slivers whose size the reader can judge only from the data labels. Large empty space above the bars adds nothing.
   - Fix: Add a light value axis with gridlines in US$m (or a minimum visible bar height), so small maturities still register visually.

### Chart data: revenue and EBITDA

Kind: chart · handoff lines 138-144 · verdict **BLOCK**

- Narrative: The figures match the source table and the calculation rows C09 and C19, but the section is a bare data table. It has no judgement-first bottom line, and its Basis text is hard to follow: pages are not tied to figures, the FY2024 row has no page, and it uses jargon such as 'identity'.
- Visual: The chart is visible, legible and correctly ordered, but it shows the pipeline label 'Handoff' and a 'citation without a page' chip that contradicts the cited pages. It also labels two years of flow data with a single as-of date and leaves a third of the card empty.

1. **High · visual** (Auditor + Saboteur)
   - Where: Revenue and EBITDA chart, under each period and in the Table form Source column: chips 'Handoff' and '1 citation without a page' (shots/CP-1_charts.png, region approx. x350-1400, y1740-2140; crop tmp/CP-1-019-a.png)
   - Problem: 'Handoff' is pipeline vocabulary that the house rule keeps off the reader's screen. '1 citation without a page' contradicts the handoff's Basis text, which cites 'annual filing pages 121 and 71' (line 142), so a reader is told the figures have no page reference when they do.
   - Fix: Label the chip with the reader's source (e.g. 'FY2024 annual filing, p.121 / p.71') and resolve the page so the chip and the Basis text agree.
2. **Medium · narrative** (Saboteur + New Reader)
   - Where: line 142: 'Full fiscal year; issuer-adjusted EBITDA As Defined, annual filing pages 121 and 71.' / line 143: 'Full fiscal year; same issuer-adjusted identity, not acquisition-pro-forma or house-adjusted earnings.'
   - Problem: The section gives two years of revenue and EBITDA with no stated takeaway: it does not say revenue grew about 21% or that the adjusted margin was about 52.6% against 51.6%. It also does not say that this adjusted figure is USD 360m above the reported USD 3813m EBITDA shown in the next section's bridge.
   - Fix: Open with a one-line bottom line giving growth, margin and the adjusted-versus-reported gap before the table.
3. **Medium · narrative** (New Reader)
   - Where: line 142: 'annual filing pages 121 and 71' and line 143: 'same issuer-adjusted identity'
   - Problem: The Basis text does not say which page backs which figure (revenue p.121, EBITDA p.71), and the FY2024 row has no page at all. 'Identity' is internal jargon, and the fiscal year-end (30 September) is never stated for 'FY2023/FY2024'.
   - Fix: Use one Basis line per figure with its own page, say 'fiscal year ended 30 September', and replace 'identity' with 'definition'.
4. **Medium · visual** (Saboteur)
   - Where: Chart header 'US$m · As of 30 September 2024' (crop tmp/CP-1-019-a.png, top right)
   - Problem: Revenue and EBITDA are annual flows covering two fiscal years, but the header labels the whole chart with a single point-in-time date. This blurs period against instant, which the house standard requires to be exact.
   - Fix: Label the chart header 'US$m · fiscal years ended 30 September 2023 and 2024'.
5. **Low · narrative** (Auditor)
   - Where: Section heading 'Chart data: revenue and EBITDA' (line 138)
   - Problem: 'Chart data:' describes how the pipeline uses the table, not what the reader learns, and the module's chart already has its own title.
   - Fix: Rename the heading to a reader title such as 'Revenue and adjusted EBITDA, FY2023–FY2024'.
6. **Low · visual** (Auditor)
   - Where: Revenue and EBITDA chart plot area (crop tmp/CP-1-019-a.png): bars end at about 63% of card width; footnote 'Missing values have no bar.'
   - Problem: The right third of the card is empty, which wastes space and shrinks the bars. The 'Missing values have no bar' note is boilerplate here because no value is missing.
   - Fix: Stretch the plot to the card width and show the missing-value note only when a value is actually missing.
7. **Low · visual** (New Reader)
   - Where: Section table (shots/CP-1_s-138.png, top, approx. y230-410): monospace headers 'Revenue' / 'Adjusted EBITDA' beside sans-serif headers, and values '6585', '7940' with no thousands separator
   - Problem: The headers mix two typefaces. Values print without separators, while the same page prints 'USD 4,173 million' elsewhere, so the formats disagree.
   - Fix: Use one header typeface and thousands separators in every table and chart label.

### Chart data: EBITDA bridge

Kind: chart · handoff lines 163-173 · verdict **BLOCK**

- Narrative: The figures are exact and reconcile (3813+70+217+58+15=4173), but the section is a bare data table with no bottom line, an internal \"C09\" code shows on screen, and four of the six rows have no page locator.
- Visual: The waterfall's scale is zero-based and proportionate, but its x-axis labels for the first four steps overlap and cannot be read. The chart also has no legend for totals versus add-backs, and the table has small typography and chip inconsistencies.

1. **High · visual** (Saboteur, Auditor)
   - Where: EBITDA bridge chart, CP-1_charts.png crop x340-1400 y2840-3280 (scratchpad/tmp/CP-1-021-a.png), x-axis category labels
   - Problem: The labels for the first four steps print on top of each other ("Opening: FY2024 EBITDA", "Acquisition transaction and integration-related expenses", "Non-cash stock and deferred compensation expense", "Refinancing costs") and cannot be read. A reader cannot tell which add-back is 70, 217 or 58 without opening the table form.
   - Fix: Use short wrapped labels with a fixed width per bar (e.g. "Acquisition costs", "Stock comp", "Refinancing") or rotate them, so each label sits under its own bar with no overlap.
2. **Medium · narrative** (Saboteur)
   - Where: line 165-172: table runs from "Opening: FY2024 EBITDA | 3813" to "Closing: FY2024 EBITDA As Defined | 4173" with no lead sentence
   - Problem: There is no bottom line. Add-backs of USD 360m (about 9% of the adjusted figure) carry the headline leverage, and that point is left for the reader to work out. The leverage effect (about 6.57x unadjusted) only appears two paragraphs later.
   - Fix: Open the section with one judgement sentence that gives the total add-backs, their share of the adjusted EBITDA and the leverage they remove.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 172: "Issuer-adjusted measure; C09 reconciles exactly at USD million precision. No house acceptance of the add-backs is implied."
   - Problem: "C09" is an internal calculation register code, and it appears on screen (small caps in CP-1_s-163.png, closing row). The reader has no way to look it up. The heading prefix "Chart data:" is pipeline wording, not a reader title.
   - Fix: Replace the code with plain words ("the steps sum exactly to the reported USD 4,173m") and title the section "EBITDA bridge, FY2024".
4. **Medium · narrative** (Auditor)
   - Where: lines 168-171: "Issuer adjustment as stated; includes integration, relocation, deal costs and inventory step-up." (and the three rows after it)
   - Problem: Only the opening row gives a filing page ("annual filing page 71"). The four add-back rows and the closing row have no page locator, so the table's source column cannot be traced row by row.
   - Fix: Give each adjustment row its filing page (the page-71 reconciliation) in the Basis and limitation column.
5. **Low · narrative** (New reader)
   - Where: line 167: "Opening: FY2024 EBITDA | 3813 | US$m | Issuer-reported unadjusted EBITDA"
   - Problem: The step is labelled plain "FY2024 EBITDA", but the Revenue and EBITDA chart on the same page labels 4173 "Adjusted EBITDA". A reader who skims can take the wrong figure as "EBITDA".
   - Fix: Label the opening step "Reported EBITDA (unadjusted)" and the closing step "Adjusted EBITDA (As Defined)", to match the other chart.
6. **Low · visual** (New reader)
   - Where: EBITDA bridge chart, CP-1-021-a.png: navy total bars vs blue step bars; chip-dot legend at the bottom
   - Problem: The chart has no legend saying that navy means totals and blue means add-backs. The "Chip dot" legend under it explains chips that this chart does not show. The 15 step is a hairline bar and has no y-axis to judge it against.
   - Fix: Add a small total/add-back legend, drop the irrelevant chip legend from this chart, and give the bars a minimum visible height.
7. **Low · visual** (Auditor)
   - Where: CP-1_s-163.png, table header row and Step column (y~228-510 at display scale)
   - Problem: The "Amount" header uses a monospace face unlike the other headers. Amounts have no thousands separator (3813, 4173). A grey "Basis" chip is repeated after every step name, next to a column that is already headed Basis.
   - Fix: Use one header typeface, format amounts as 3,813, and drop the redundant per-row Basis chip or merge it with the column.
8. **Low · visual** (New reader)
   - Where: EBITDA bridge chart, CP-1-021-a.png: link grid below the chart
   - Problem: Below the chart, the six step names are repeated as links in a three-column grid whose order does not follow the bars left to right. This repeats the axis text and makes the reader map labels to bars twice.
   - Fix: Put the source links in bar order, or attach each one to its bar's label.

### Manual quality review

Kind: prose/table · handoff lines 242-251 · verdict **CONCERNS**

- Narrative: The section is a five-row claim-reliability table written in pipeline audit language: it has no opening verdict, no figures behind its two key credit inferences, and \"Manual\" in the heading overstates the review.
- Visual: There is no chart. The table renders cleanly and is readable at 1440 px, but it has no Source column, row Basis buttons with empty basis data, and an inline Basis control that blends into the claim text.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: line 247 "Decimal kernel used; numerator/denominator and scope preserved below."; line 250 "Open material scope defects; block only dependent legal, market and instrument-recovery conclusions."; column header line 244 "Lineage judgment"
   - Problem: The section is written as a pipeline self-audit. "Decimal kernel", "scope defects", "block … dependent conclusions", "Lineage judgment" and the Title Case labels "Directly Sourced" and "Analyst Inference" are internal vocabulary that the house standard keeps off the reader's page. A PM cannot tell what any of it means for the credit.
   - Fix: Restate each row in reader terms, for example "calculated by us from reported figures, not a figure the issuer reports", and rename the columns to something like Claim / How we know it / Caveat.
2. **Medium · narrative** (Saboteur)
   - Where: section heading line 242 "### Manual quality review"
   - Problem: "Manual" tells a committee member that a person checked these claims. Nothing in the section shows that anyone did, so a reader may give the table more weight than it has earned.
   - Fix: Use a heading that matches what the section is, such as "How reliable are the key claims", or say who did the review.
3. **Medium · narrative** (Saboteur)
   - Where: line 248 "Year-end cash is not durable deleveraging | Analyst Inference, supported by sourced accrued liabilities and subsequent settlement"; line 249 "Repeated add-backs weaken confidence in durable earnings"
   - Problem: The two judgements that matter most for credit come with no figure, unit or period. The table never gives the USD 6,261m year-end cash, the USD 4,216m accrued distribution or the USD 360m / 247m add-backs, so the reader cannot size how weak cash or earnings quality is from this section.
   - Fix: Put the deciding amount, with currency, unit and fiscal year, in each judgement row, or point to the Calculations row ID (C06, C09) that sizes it.
4. **Medium · narrative** (New reader)
   - Where: lines 242-250, table starts straight after the heading with no lead sentence
   - Problem: There is no opening judgement. The reader has to work through five rows to infer the overall verdict (reported figures are reliable, two conclusions are inferences, and the legal, market and recovery views cannot be supported), which goes against the judgement-first standard.
   - Fix: Open with one sentence giving the overall reliability verdict and which conclusions elsewhere in the report it restricts.
5. **Medium · narrative** (Saboteur)
   - Where: line 250 "Executed package, market values and complete legal perimeter | Insufficient Information | Open material scope defects; block only dependent legal, market and instrument-recovery conclusions."
   - Problem: The row names a material gap but not which conclusions in this report it invalidates, and the wording reads as an instruction to another stage. A committee member could rely on a recovery or relative-value view without seeing that it is unsupported.
   - Fix: Name the affected conclusions in reader words (no covenant headroom, no market pricing, no recovery estimate) and state them as limits on the view.
6. **Medium · visual** (Auditor)
   - Where: Manual quality review table, CP-1_s-242.png, region approx. x 360-1390, y 255-590 (original px)
   - Problem: The table has no Source column. Each row only has a grey "Basis" button, and in the DOM every one carries data-basis="[]". The row that says "Directly Sourced" therefore shows no source on the page, unlike the Calculations table directly below it.
   - Fix: Add a Source column, or make sure each row's Basis opens the specific filing pages behind the claim.
7. **Low · narrative** (New reader)
   - Where: line 247 "Rounded chart presentation is not a source-reported ratio."
   - Problem: This refers to charts in another part of the page and assumes the reader knows the ratios are self-computed. It needs cross-page context to understand.
   - Fix: Say plainly that the leverage and coverage multiples are our calculations from reported figures, rounded to two decimals in the charts.
8. **Low · visual** (New reader)
   - Where: Manual quality review table, CP-1_s-242.png, first column, e.g. "principal and accrued dividend Basis" (y approx. 310-335 original px)
   - Problem: The inline "Basis" control wraps onto the end of the claim text in the same grey weight. It reads like a stray word in the claim rather than a control, and the rows end up unevenly ragged.
   - Fix: Give Basis its own fixed position, such as a right-aligned icon or a separate narrow column, styled clearly as a link.

### Request + Next module

Kind: run plumbing · handoff lines 1-3, 303-310 · verdict **BLOCK**

- Narrative: This section is run plumbing: the brief given to the model and the routing to downstream modules, shown to the reader in pipeline language. Its one real judgement, that the annual foundation is complete with limitations, is buried in the routing note instead of the bottom line and limitations.
- Visual: The section has no chart, map or timeline. Both blocks render as ordinary h3-plus-paragraph analysis with full nav weight, so nothing on the page marks them as non-analytical. Spacing and typography are otherwise clean, with no clipping.

1. **High · narrative** (Auditor, New reader, Saboteur (promoted))
   - Where: Line 303-305: "## Next module ... Pass the annual financial foundation to the business fact pack and fundamental synthesis"; line 308: "Evidence validation should trace ... the derived metrics to the calculation register"; line 2: "pathway: credit_snapshot. Build the historical consolidated financial ..."
   - Problem: Both passages are instructions between pipeline stages: the brief given to the model and the routing to the next module. They are printed on screen as reader prose, using pipeline vocabulary ("Next module", "pathway: credit_snapshot", "business fact pack", "calculation register", imperative "Pass ..."). A portfolio manager cannot act on them, and they break the house rule against pipeline language.
   - Fix: Keep Request and Next module out of the reader's Modules page, or reduce them to a muted run-metadata line. Move any real judgement into the module's own reader sections.
2. **Medium · narrative** (Saboteur)
   - Where: Line 305: "The annual foundation is complete with limitations, while quarterly normalization, full cash-access analysis and legal denominator testing remain separate unfinished work."
   - Problem: The module's only completeness judgement, and the three open limitations, sit at the very end of the page under a routing heading. A reader who stops at the analysis will not see that cash access and legal denominators are unresolved.
   - Fix: State this completeness judgement and its unfinished items in the bottom line and the Limitations passage, in house order, not in the routing note.
3. **Medium · narrative** (Auditor)
   - Where: Line 309: "Basis: Source readiness (CP-0); TDG_2024-09-30_10-K_...jsonl, page 63"; line 306: "Basis: calculation C04; calculation C06; calculation C15" (rendered in data-basis of CP-1.dom.html)
   - Problem: Opening the Basis popover shows a module code ("CP-0") and internal calculation IDs. A reader cannot resolve these without the pipeline.
   - Fix: Show the reader-facing module name only ("Source readiness"), and make each calculation reference name its metric or link to it.
4. **Medium · narrative** (New reader)
   - Where: Line 305: "Use issuer-adjusted earnings only with their attribution and the unadjusted denominator sensitivity; challenge add-back recurrence rather than treating the reconciliation as house approval." Line 308: "testing the source-to-definition boundary"
   - Problem: Phrases such as "denominator sensitivity", "house approval", "legal denominator testing" and "source-to-definition boundary" are workflow shorthand that a credit committee member cannot decode. Each sentence also packs two or three instructions.
   - Fix: If any of this stays visible, write it in plain credit terms, e.g. say which leverage figure uses adjusted EBITDA and why that matters, with one point per sentence.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-1_s-1.png, top of content (y~190-245) and CP-1_s-303.png, bottom (y~1800-1945); On this page nav lists "Request" and "Next module" alongside analysis sections
   - Problem: Request and Next module use the same h3 heading, body type and nav weight as the analytical sections. On the page, nothing tells the reader that these are run instructions rather than findings. Request is the first prose a reader meets after the charts.
   - Fix: Visually demote or remove these blocks (for example, a muted metadata strip, absent from On this page) so the reader's eye goes from the bottom line straight to the analysis.
6. **Low · visual** (Saboteur)
   - Where: CP-1_s-1.png, Request paragraph (y~215): "as of 2024-09-30" vs page header "As of 30 September 2024"
   - Problem: The same date appears in two formats on one screen, and a snake_case token ("credit_snapshot") sits beside the header's "Credit snapshot".
   - Fix: Use the header's reader formatting for both the date and the pathway, or drop the duplicate line.

## Business & governance (CP-1A)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001/requests/CP-1A/3bde2f75df63a2643aec97cdc158f5e5894edcf0afa689cf6421808c16554bfe/1.response.md`

### Analytical appendix — complete canonical registers

Kind: register appendix · handoff lines 127-207 · verdict **BLOCK**

- Narrative: This is a dense evidence appendix: the content is careful about missing versus zero, but the heading and the rubric text use pipeline wording ("canonical", "governance tool", "high-risk action true"), the score scale is never explained, the conclusion is buried, and several abbreviations are undefined.
- Visual: The section has no chart. Its tables render too densely: long filenames dominate them and wrap badly, and the Transaction register's Source column is visibly cut off at the right edge, so citations cannot be read.

1. **High · narrative** (Auditor + New reader)
   - Where: L127 "### Analytical appendix — complete canonical registers"; L180 "The existing governance tool applied its row checks and rubric ... No analyst-invented score was used."; L139 "financial foundation must calculate from accepted balances if required"
   - Problem: The heading uses "canonical", which is banned pipeline vocabulary, and the same word shows in the On-this-page navigation. Elsewhere the text talks about "the existing governance tool", "Tool score" and "Tool output" (L182, L193), and it hands work to another module ("financial foundation"). Those are internal process terms, not language a credit reader uses.
   - Fix: Rename the heading to something like "Analytical appendix — evidence registers" and describe the rubric and the next steps in reader terms, without naming tools or modules.
2. **High · narrative** (Saboteur + New reader)
   - Where: L184-193 rubric: "Disclosure transparency | 1 | G3" ... "Composite / risk level / action | 5 / High / high-risk action true | Tool output"
   - Problem: The 1-5 scores never say their range or which end is worse. A reader could take "Disclosure transparency 1" as poor disclosure when the text calls it supportive. "high-risk action true" is a raw boolean flag dropped into a committee document.
   - Fix: Add one line stating the scale (1 = lowest risk, 5 = highest) and write the composite as a sentence, for example "Composite 5 of 5: high risk, driven by the debt-funded dividend".
3. **High · visual** (Auditor + New reader)
   - Where: Transaction register, Source column, rows T1-T3: shots/CP-1A_s-127.png, original region x 900-1440, y 1600-2400 (crop scratchpad/tmp/CP-1A-043-a.png)
   - Problem: The Source column runs past the table's right edge, so each citation shows as "K_0001260221-24" and "20240930.htm.jsor" with the end missing. The page-number line also starts at the clip edge. The source reference this register exists to give cannot be fully read.
   - Fix: Wrap or shorten the source identifiers, for example as "10-K FY2024, p. 137" with the full filename in a tooltip or in Sources, so the whole citation fits inside the table.
4. **Medium · narrative** (Saboteur)
   - Where: L129 "The following registers preserve the evidence, classification, uncertainty and creditor transmission behind the view. They do not supply a security recommendation..."
   - Problem: The appendix opens by saying what it does not do and never states its conclusion. The judgement it supports (shareholder-extraction risk 5, high governance risk) first appears inside a table 50 lines down, at L193.
   - Fix: Open with one judgement-first sentence, for example "The registers support a high governance-risk view driven by the USD 4,348 million debt-funded dividend", and then say what the tables hold.
5. **Medium · narrative** (New reader)
   - Where: L148 "acquisition of all stock of FPT"; L149 "SEI"; L150 "CPI's Electron Device Business"; L168 "not classified as a coercive LME"; L139 "DSO"
   - Problem: FPT, SEI, CPI, LME and DSO are never spelled out. A portfolio manager who has not read the 10-K has to look elsewhere to know what was bought or what an LME is.
   - Fix: Spell out each abbreviation on first use (company names in full; liability management exercise; days sales outstanding).
6. **Medium · narrative** (Auditor)
   - Where: L147 "| T0 | Live proposed deal: Not supplied ... | context, page 1 |"; L167 "Source readiness (CP-0); context, page 1"
   - Problem: "context, page 1" is the request context the run was given, not an issuer document, yet it sits in the Source column as if it were evidence. In the rendered page, "Source readiness" is a module name used as a source.
   - Fix: Mark these rows as "No issuer document supplied" in the Source column rather than citing the run's own inputs as a source.
7. **Medium · visual** (New reader + Saboteur)
   - Where: Business fact register and Transaction register, shots/CP-1A_s-127.png full width (original y 330-2400)
   - Problem: The seven-column tables wrap into narrow columns. The Source column repeats a 60-character filename that wraps over five or six lines, and quotes are squeezed to three words a line, so seven B-rows fill about 1,200 px. The reasoning columns are hard to scan, and the next registers (governance, flags, rubric) fall far below the screen.
   - Fix: Shorten the citations and give the reasoning columns the width, or fold the long Verbatim/Limitation text, so each row reads in two or three lines.
8. **Low · visual** (New reader)
   - Where: Every register ID cell, e.g. "B1 Basis", "T0 Basis": shots/CP-1A_s-127.png, ID column x approx 370-420
   - Problem: Each row ID carries a grey "Basis" label, but no Basis line goes with it. It reads as stray markup and makes the reader wonder what it refers to.
   - Fix: Remove the Basis label from register ID cells, or turn it into a working link to that row's source passage.

### Map: ownership and control

Kind: map · handoff lines 97-104 · verdict **BLOCK**

- Narrative: The section is a three-row relationship table with no opening judgement. It leaves out the Domestic Restricted Subsidiary guarantors and the holding-company point, and it puts raw source file names and graph jargon ('edge') in front of the reader.
- Visual: The ownership-and-control drawing hides the parent's 100% ownership edge under its guarantee edge, splits the parent's name mid-word and runs the arrow lines through the edge labels. The edge table is shown twice, once in monospace link styling.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 103: "TransDigm UK | Provides guarantees of the disclosed notes, with rank depending on the obligation | Guarantee | TransDigm Inc."
   - Problem: The filing says the notes are guaranteed by 'TD Group, TransDigm UK and all of TransDigm Inc.'s Domestic Restricted Subsidiaries'. The map leaves out the subsidiary guarantors, who hold the operating assets, and omits the filing's statement that 'TD Group has no significant operations or assets separate from its investment in TransDigm Inc.'. A committee could misread how far the guarantees reach and how much the parent's guarantee is worth.
   - Fix: Add a node and edge for the Domestic Restricted Subsidiaries as guarantors, and state that the parent is a holding company with no separate assets, so the reader can judge guarantee coverage.
2. **High · visual** (Saboteur, Auditor)
   - Where: Maps panel, 'Ownership and control' drawing, CP-1A_maps.png crop (340,250)-(1400,440) at full resolution; also /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-040-a.png
   - Problem: The 100% ownership edge from TransDigm Group Incorporated to TransDigm Inc. is drawn on exactly the same path as the parent's guarantee edge, so only one arrow labelled 'Guarantee' shows. The 'Ownership' label is in the DOM but hidden underneath it. The drawing therefore shows the parent only as a guarantor and leaves out the ownership link, which is the point of an ownership-and-control map.
   - Fix: Draw parallel or offset edges with separate, legible labels, and use a different line style for ownership and for guarantee, so both relationships between the parent and TransDigm Inc. show.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 97-99: "### Map: ownership and control" followed directly by "| From | Relationship | Edge type | To | Evidence |"
   - Problem: The section is a bare edge list with no opening judgement. The reader is never told what the structure means for creditors (who issues the debt, who guarantees it, and whether creditors of the parent's operating subsidiaries rank ahead).
   - Fix: Open with one bottom-line sentence on the issuer/guarantor structure and its creditor consequence, then show the table.
4. **Medium · narrative** (Auditor, New reader)
   - Where: line 101: "The parent holds all outstanding capital stock; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 4–124"
   - Problem: The Evidence column mixes narrative caveats with raw pipeline file names (accession number plus '.htm.jsonl'). The reference 'pages 4–124' covers about 120 pages, so it does not point to anything a reader could check.
   - Fix: Put the caveat in its own column, and in a Source column show a readable citation ('FY2024 10-K, p. 57') with a page range narrow enough to check.
5. **Medium · narrative** (New reader, Auditor)
   - Where: line 102: "this is a filing-summary edge, not a complete executed guarantee map"; Maps panel heading 'Edges of the map, as stated' and column 'Edge type'
   - Problem: 'Edge', 'edge type' and 'filing-summary edge' are graph and pipeline words, not reader language. A portfolio manager has to work out that an 'edge' is a legal relationship.
   - Fix: Use 'Relationship type' and plain wording such as 'summarised from the annual report; the full guarantor list is in the indentures'.
6. **Medium · visual** (New reader, Auditor)
   - Where: Maps panel drawing, node 'TransDigm Group Incorp / orated' and edge labels 'Guarantee', CP-1A-040-a.png top region
   - Problem: The parent's node label breaks mid-word ('Incorp' / 'orated'). Both 'Guarantee' labels sit on top of their arrow lines and are partly struck through. The drawing uses only a narrow middle strip of a wide panel.
   - Fix: Wrap labels at word boundaries or widen the nodes, put edge labels clear of the lines, and use the width of the panel.
7. **Low · visual** (New reader, Saboteur)
   - Where: Maps panel 'Edges of the map, as stated' table under the drawing (CP-1A_maps.png, about y 450-1050 full resolution) vs the Modules-page section table (CP-1A_s-97.png, top)
   - Problem: The same three-row table appears twice: once in the section and again under the Maps drawing. The Maps copy uses underlined blue monospace for the Relationship column and monospace for the From and To entity names, which looks like links or code and is harder to read than the section's own rendering.
   - Fix: Show the edge table once, under the drawing, in the same proportional table type the rest of the page uses, and drop the link-like styling unless the entries really are links.

### Map: operating model to credit

Kind: map · handoff lines 105-115 · verdict **BLOCK**

- Narrative: This section is a table with no lead sentence, so its credit conclusion (refinancing and leverage exposure after a debt-funded payout) sits in the last row. Raw .jsonl source references and graph jargon ("Edge type") take up most of the reader's attention.
- Visual: The map drawing is visible but hard to read: the \"Analyst Interpretation\" edge labels are cut off, node text breaks mid-word, nothing explains the three line styles, and the edge table is repeated in two typographic styles.

1. **High · visual** (Auditor, New reader)
   - Where: Operating model to credit map, CP-1A_maps.png region x340-1400 y1030-1300 (crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-041-a.png)
   - Problem: All three second-column edge labels show only "alyst_Interpretati". The DOM text is "Analyst Interpretation", but it is wider than the gap between nodes, so both ends are cut off and the edge line through the text makes the space look like an underscore. The first-column labels "Management Language" and "Documentary Fact" run into the node borders. Two personas caught this, so it is promoted to High.
   - Fix: Widen the gap between columns or wrap and shorten the edge labels so each one fits fully between its nodes, on a background that hides the edge line behind the text.
2. **High · visual** (Auditor, New reader)
   - Where: Operating model to credit map node boxes, CP-1A_maps.png crop CP-1A-041-a.png: "Installed aircraft com ponents", "Debt-service resilienc e", "Shipment and cost disr uption", "Secured dividend finan cing"
   - Problem: Node labels break in the middle of words, leaving single orphan letters ("resilienc / e", "input / s"). That makes the boxes hard to read and looks broken to a committee reader. Two personas caught this, so it is promoted to High.
   - Fix: Wrap node text at word boundaries, letting the box grow taller or wider to fit the full phrase.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: line 105-107: "### Map: operating model to credit" followed directly by "| From | Relationship | Edge type | To | Evidence |"
   - Problem: The section has no lead sentence. The credit conclusion the chain reaches is "Persistent refinancing and leverage exposure" after a debt-funded payout, but it sits in the last table row, so the reader gets six edges and no judgement. Other sections, such as line 118, open with a judgement.
   - Fix: Open with one bottom-line sentence that states what the chain means for creditors, before the table.
4. **Medium · narrative** (Auditor, New reader)
   - Where: line 113: "USD 3,000 million issuance and approximately USD 4,348 million payment disclosed; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 54–56"
   - Problem: The Evidence column mixes analytical qualification with raw source references, including a pipeline file name ending in ".jsonl" that the reader cannot interpret. The same long reference is repeated in all six rows, twice in row 112, which makes the table wide and dense.
   - Fix: Split Evidence into a short qualification column and a Source column that cites "FY2024 10-K, p. 54–56" in reader terms.
5. **Medium · narrative** (Saboteur)
   - Where: line 113: "New debt and existing cash funded shareholder payments after year-end ... USD 3,000 million issuance and approximately USD 4,348 million payment disclosed"
   - Problem: The most material credit fact in the map, a roughly USD 4.3bn payout funded with USD 3.0bn of new secured debt, has no date ("after year-end"). It is not labelled as a subsequent event to the 30 September 2024 balance sheet, while line 95 dates it to October 2024.
   - Fix: State the period, October 2024 after the FY2024 balance-sheet date, in the row so the payout size, date and funding read together.
6. **Medium · visual** (Saboteur, Auditor)
   - Where: Operating model to credit map: solid, dashed and dotted edges with no legend (DOM has no legend element)
   - Problem: The map uses three line styles that stand for evidence strength (management estimate, analyst inference, documented fact), but nothing explains them. A reader can take a dashed analyst-inference link for a documented causal fact.
   - Fix: Add a small legend that maps each line style to its evidence class, and say in words that dashed links are analyst interpretation.
7. **Low · narrative** (New reader)
   - Where: line 107: "| From | Relationship | Edge type | To | Evidence |" with values "Management Language", "Analyst Interpretation", "Documentary Fact"
   - Problem: "Edge type" is graph jargon, and the title-case classification labels read as internal taxonomy codes rather than reader language.
   - Fix: Rename the column to something like "Basis of link" and use plain lower-case wording such as "management estimate", "our interpretation", "stated in filing".
8. **Low · visual** (New reader, Auditor)
   - Where: CP-1A_s-105.png section table (y~215-720 displayed) vs CP-1A_maps.png "Edges of the map, as stated" table
   - Problem: The same six-row table appears in full twice on the module page, once in the section and once under the map in the Maps panel, with different typography (proportional vs monospace bold underlined). It also puts a stray "Basis" chip in every From cell.
   - Fix: Show the edge table once next to the drawing, in one typographic style, and put the Basis chip where it does not split the From label.

### Calculations

Kind: prose/table · handoff lines 208-219 · verdict **CONCERNS**

- Narrative: The section is a calculation log with no credit judgement. C1–C3 add up correctly (670, 26, 2,919), but C3 mislabels liquidity as cash, C4 just repeats the distribution with a negative sign, and pipeline and tool vocabulary is shown to the reader.
- Visual: The table is visible and tidy, but it is dominated by wrapped raw file names. Its Basis buttons open an empty basis list. Results are left-aligned and wrap, and there is no chart (none is expected for this section).

1. **High · narrative** (Saboteur, Auditor)
   - Where: L216 C3 "sum(7267, -4348) | USD 2,919 million | September 30 reported cash liquidity less subsequent October distribution ... includes availability rather than only cash"
   - Problem: The Period column calls 7,267 "reported cash liquidity", but the limitation in the same row says the figure includes undrawn availability. A reader could take USD 2,919 million as cash on hand after the October distribution. Nothing in the section says how much of it is cash and how much is revolver availability.
   - Fix: Label the figure as total liquidity (cash plus availability) in the Period/quantity cell, so the result means one thing everywhere it appears.
2. **High · narrative** (Auditor, New reader)
   - Where: L210 "All new arithmetic used the existing Decimal-38 kernel. ... No ratio, leverage, run-rate acquisition EBITDA, free-cash-flow normalization or liquidity runway was invented."; L218 "Existing score_governance rubric; no manual arithmetic ... tool output only"
   - Problem: The section opens with pipeline wording ("Decimal-38 kernel", "score_governance", "tool output", "invented") and says what was not done. It never states a credit judgement, so the bottom-line-first rule is broken.
   - Fix: Open with one sentence of credit meaning (for example, how much the October distribution consumed of the FY2024 operating cash flow and of liquidity), and remove the engine, tool and function names.
3. **Medium · narrative** (Saboteur)
   - Where: L217 C4 "sum(2919, -7267) | USD -4,348 million | Payment-adjusted versus reported liquidity change"
   - Problem: C4 subtracts C3's own input back out and returns the distribution with a negative sign. It adds nothing, and to a reader it looks like a second, separate liquidity loss of USD 4.3 billion.
   - Fix: Drop C4, or fold it into C3 as "distribution paid: USD 4,348 million".
4. **Medium · narrative** (New reader)
   - Where: L214-217 "sum(2045, -1375)", "sum(165, -139)"; L218 "G1–G8 and F1–F2", "high-risk action true"
   - Problem: The operands are written as code-style function calls without units or labels, and the result reads like a boolean flag. The G/F identifiers only make sense after reading another table on the page.
   - Fix: Write the operations as "FY2024 operating cash flow USD 2,045m less FY2023 USD 1,375m", and state the governance result in words.
5. **Medium · visual** (Auditor, New reader)
   - Where: Calculations table, ID column "Basis" buttons, shots/CP-1A_s-208.png crop (340,220)-(1400,770); DOM render/CP-1A.dom.html: `aria-label="Basis for row: C1"` with `data-basis="[]"`
   - Problem: Every C row has a Basis button, but the button carries an empty basis list, so it promises a source and opens nothing. The G-CALC row has no button, so the rows are also inconsistent.
   - Fix: Show a Basis button only on rows that have basis content; otherwise leave the Source column to carry the reference.
6. **Medium · visual** (New reader)
   - Where: Source and limitation column, "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 56; reported cash flow, not normalized..." (L214-217), screenshot right column
   - Problem: A raw file name of about 60 characters, wrapped over three lines, takes up most of each cell and hides the limitation the reader actually needs. Mixing the source with the limitation in one column makes both harder to read.
   - Fix: Show a short source label (for example "FY2024 10-K p.56") and put the limitation in its own column or line.
7. **Low · visual** (Auditor)
   - Where: Result column "USD 2,919 million" / "USD -4,348 million" wrapping onto two lines; ID "G-CALC" split as "G- / CALC"
   - Problem: The narrow Result and ID columns wrap the key numbers and the ID, while the operands column has spare width. Numbers are left-aligned, so the column cannot be scanned.
   - Fix: Keep results on one line, right-align the numbers, and give the ID column a non-breaking width.

### Gaps

Kind: prose/table · handoff lines 220-234 · verdict **BLOCK**

- Narrative: The table names real credit gaps but leads with no judgement. Its rows are not ordered by credit impact, its severity column mixes four scales, and pipeline instructions (Python scripts, typed schemas, the Financial foundation module, 'this Markdown module') leak into the reader's text.
- Visual: There is no chart in this section. The table is legible with good contrast, but raw .jsonl filenames inflate row heights, and the Basis chips have empty payloads and appear on only some rows.

1. **High · narrative** (Auditor, New reader)
   - Where: line 233: "Companion definitions and scripts unavailable | Procedural; no substantive conclusion changed | No claim of running unavailable Python or validating unavailable typed schemas | Manual checks below and transport checker used; do not block this Markdown module"
   - Problem: The whole row is about the pipeline (Python scripts, typed schemas, transport checker, Markdown module) and tells the reader nothing about credit. Line 229 adds "Financial foundation must establish accepted gross/net debt" and "business pack does not certify them", and line 233's source is "Selected method and transport instructions". These are instructions between modules shown to a committee reader, which breaks the house rule against pipeline vocabulary.
   - Fix: Drop the procedural row from the reader view and restate the debt row as a credit gap, e.g. that gross/net debt and the maturity profile are not assessed in this section, with no reference to other modules or packs.
2. **High · narrative** (Saboteur, Auditor)
   - Where: line 228: "Executed legal terms and covenant certificate unavailable | Blocking for permission and headroom decisions | ... future legal leakage capacity is not"
   - Problem: The one gap that blocks a credit decision on a high-yield issuer (covenant headroom and leakage capacity) is the fifth of ten rows. It sits under a live-deal row the scope makes irrelevant ("Blocking only for live transaction underwriting"), and there is no lead sentence saying which gaps limit the credit view. Judgement is not first, and a reader skimming the top rows could conclude nothing blocks the assessment.
   - Fix: Open the section with a one-sentence bottom line naming the gaps that limit the credit view, and order the rows by their effect on the credit decision, blocking gaps first.
3. **Medium · narrative** (Saboteur)
   - Where: Severity column, lines 224-233: "Blocking only for live transaction underwriting" / "Material for quantified business stress" / "High for quantified servicing/refinancing, nonblocking for business conclusions" / "Procedural; no substantive conclusion changed"
   - Problem: The column mixes four scales (Blocking, Material, High, Procedural/Nonblocking), each with its own qualifying clause, so gaps cannot be compared or ranked. Line 229 rates one gap both "High" and "nonblocking" at once.
   - Fix: Use one short severity scale (e.g. Blocking / Material / Minor) in the cell and move the qualifier to the 'Conclusion or decision restricted' column.
4. **Medium · narrative** (New reader)
   - Where: line 230: "No complete LME or amendment behavior evidence | Material for creditor-treatment classification"; line 229: "add-back bridge"; line 228: "future legal leakage capacity"
   - Problem: LME (liability management exercise) is never spelled out, and "add-back bridge", "leakage capacity" and "fact pack" (line 224) are shorthand that a portfolio manager without the sources has to decode.
   - Fix: Spell out LME on first use and use plain credit terms (e.g. 'EBITDA adjustments reconciliation', 'capacity to pay out cash to shareholders under the debt documents').
5. **Medium · visual** (Auditor, New reader)
   - Where: Gaps table, Source column, shots/CP-1A_s-220.png crop (350,260)-(1400,1100): "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 131–137; TDG_2024-09-30_10-K_..." (line 226)
   - Problem: The Source cells print raw ingest filenames, including the .jsonl extension and the EDGAR accession number. They break mid-token and wrap over up to 8 lines, which makes these rows the tallest in the table. Other cells say "context, page 1" or "Source readiness", which are internal labels a reader cannot trace to a document.
   - Fix: Render sources as reader labels (e.g. 'FY2024 10-K, pp. 131–137'), and replace 'context'/'Source readiness' with the actual document or 'Analyst request'.
6. **Medium · visual** (Auditor, Saboteur)
   - Where: Gaps table, Gap column 'Basis' chips; render/CP-1A.dom.html s-220: six buttons all with data-basis="[]" (e.g. aria-label="Basis for row: Live-deal inputs absent")
   - Problem: Six of ten rows show a 'Basis' chip whose basis payload is empty, so the control promises supporting evidence it does not have. The other four rows (Debt/maturity, LME, Publication boundary, Companion definitions) have no chip, which suggests a difference between rows that does not exist.
   - Fix: Show a Basis chip only when it carries a basis, or show none in a table that already has a Source column.
7. **Low · visual** (New reader)
   - Where: Gaps table, shots/CP-1A_s-220.png y≈215-1250 (display scale): five columns of 2-8-line wrapped cells across ten rows
   - Problem: The table is a dense wall of text roughly 1,000 px tall, and the narrow Gap column wraps titles like "Controller, voting rights, economic interests, prior ownership and related-party schedules incomplete" over seven lines.
   - Fix: Shorten gap titles to a few words and widen the Gap column at the expense of the Source column once source labels are shortened.

### Manual method checks

Kind: prose/table · handoff lines 235-246 · verdict **BLOCK**

- Narrative: This section is the pipeline's tooling and process log (script names, run status, \"producer/invocation/handoff/canonical/consumer\"). There is no credit judgement in it, and it breaks the house rule on pipeline vocabulary throughout.
- Visual: The three-column table renders cleanly, with no clipping or overflow and readable contrast. The visual problems are that it has a reader-facing heading and nav entry it should not have, and a Status column of repeated text taking up width.

1. **High · narrative** (Auditor, New reader)
   - Where: Handoff lines 239-243: "prepare_invocation.py | Not run: unavailable" ... "validate_handoff.py" ... "confidence_score.py" ... "completeness_check.py" ... "Python composition / other scripts"; rendered as the table on CP-1A_s-235.png, y≈760-1060
   - Problem: The whole section is the pipeline's internal tooling log. It names Python scripts the reader has never heard of and reports their run status, which breaks the rule against pipeline language on screen and tells a credit committee nothing about TransDigm.
   - Fix: Keep this table in the run's internal record and leave it out of the Modules page; if a reader-facing point remains, such as 'no confidence score was calculated', put it in Limitations in plain words.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 244: "Unavailable: not supplied as an upstream producer for this invocation | No block imposed. Direct located issuer facts used; no leverage or accepted canonical KPI claim invented"
   - Problem: "upstream producer", "invocation", "handoff", "canonical" and "No block imposed" are banned pipeline words, and they appear on screen (the module code was swapped for "Financial foundation accepted fact handoff", but the jargon stayed). The one point that matters here is that this module made no leverage claim because no accepted financial figures were available, and the wording hides it.
   - Fix: State it as a limitation in reader language, e.g. that leverage and other financial measures are not assessed here and come from the Financial foundation page.
3. **Medium · narrative** (Auditor, Saboteur)
   - Where: Line 240: "Manually checked required headings, sources, temporal separation, categories, located quotes, arithmetic traces, report selectors and every selected consumer"; line 245: "no unavailable schema, receipt or settled-head requirement imposed"
   - Problem: "report selectors", "consumer", "schema", "receipt" and "settled-head" are pipeline terms. The module also certifies its own quality ('manually checked ... every selected consumer'), which a committee could read as independent validation when nothing independent was done.
   - Fix: Remove self-certification of process from the reader page; any validation claim belongs to the Evidence validation module's findings.
4. **Medium · narrative** (Saboteur)
   - Where: Line 241: "No confidence formula supplied; no numerical confidence invented. Direct dated issuer evidence classified High; management estimates remain Management Language; unsupported topics remain Insufficient"
   - Problem: Confidence labels (High / Management Language / Insufficient) are introduced inside a tooling table, where a reader looking for how much to trust the findings will not find them. They are also not tied to any finding, so they read as a blanket 'High' on the pack.
   - Fix: Show each finding's evidence grade next to that finding in Key findings, and drop the process narration.
5. **Medium · visual** (New reader, Auditor)
   - Where: "On this page" nav entry "Manual method checks" (highlighted, CP-1A_s-235.png left rail y≈978) and the table heading at y≈730
   - Problem: The section gets a first-class heading and nav entry between Gaps and Next module, the same weight as analytical sections, so internal process sits on the reader's path through the page and makes it longer.
   - Fix: Remove the section from the reader page and nav, or at most collapse it into an internal or audit appendix outside the reading order.
6. **Low · visual** (Saboteur)
   - Where: Status column of the Manual method checks table, CP-1A_s-235.png region x≈530-700, y≈790-1150
   - Problem: Five of seven Status cells repeat "Not run: unavailable". The column takes about a fifth of the table width but carries no information, which crowds the one column with text.
   - Fix: If the table survives anywhere, fold the shared status into the heading and give the width to the result column.

### Request + Next module

Kind: run plumbing · handoff lines 1-3, 247-263 · verdict **BLOCK**

- Narrative: Neither section is written for the reader: one is the prompt sent to the model and the other is module routing in pipeline vocabulary ("handoff", "fact pack", "canonical", "upstream"). The one real credit judgement, at line 262, is buried at the end of the page.
- Visual: This section has no charts, maps or timelines. The Next module table renders cleanly (readable contrast, no clipping), but its first column repeats each module name and wraps to three lines, and both sections are styled like analysis in both the body and the side nav.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 2: "TransDigm Group Incorporated, as of 2024-09-30; pathway: credit_snapshot. Establish the business, ownership, historical transaction and issuer-level governance context relevant to creditors"; rendered under the heading "Request" (CP-1A_s-1.png, top of the content column, about y 190-245 at display scale)
   - Problem: This is the instruction sent to the model, shown as reader content. The snake_case pipeline label "pathway: credit_snapshot" appears verbatim on screen (confirmed in render/CP-1A.dom.html), and the ISO date conflicts with the page header's "30 September 2024". A committee reader gets an internal prompt where they expect analysis. Two personas caught this, so it is promoted to High.
   - Fix: Keep the Request out of the reader's Modules page (or move it into a collapsed provenance area), and show the pathway, if at all, as the reader label "Credit snapshot" that the run bar already uses.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 249: "The business and historical transaction fact pack is ready with the bounded restrictions below. Readiness is judged once for each requested module; the rows distinguish usable context from an authorization to complete a missing-evidence-dependent decision." and the table header at line 251, "Readiness from this handoff"
   - Problem: The whole Next module section is routing between modules, written in pipeline vocabulary: "handoff" (rendered in the column header, confirmed in the DOM), "fact pack", "upstream", "rerun", "canonical debt" (line 254), "requested module". This breaks the house rule against pipeline language and tells a portfolio manager nothing about TDG's credit. Two personas caught this, so it is promoted to High.
   - Fix: Remove the module-routing table from the reader view (keep it in the run folder for the orchestrator), or rewrite it as a short reader-facing list of what is still unknown and which part of the report covers it.
3. **Medium · narrative** (Saboteur)
   - Where: Line 262: "The decisive monitoring question is whether future operating cash is retained after investment and distributions, not simply whether the installed aircraft base remains attractive."
   - Problem: This is the module's sharpest credit judgement, and it sits after an 8-row plumbing table at the very end of the page, where a reader skimming past the routing material will miss it. Being phrased as advice to "Downstream work" makes it weaker still.
   - Fix: Move the monitoring question into the Bottom line or the 'what would change the view' passage, worded to the reader rather than to downstream modules.
4. **Medium · visual** (New reader, Auditor)
   - Where: Next module table, 'Selected module' column (CP-1A_s-247.png, display y about 1300-1870, x about 300-420): "Source readiness — Source readiness", "Financial foundation — Financial foundation", "Business & governance — Business and transaction context"
   - Problem: After code substitution the module names render twice, so the narrowest column wraps to three lines and repeats itself. One row is the current module grading its own readiness ("Complete with limitations"), which means nothing to a reader. The result looks like a template artefact and makes the table taller than it needs to be.
   - Fix: If the table stays, render one reader-facing name per row and drop the row where the module grades itself.
5. **Low · narrative** (Saboteur)
   - Where: Line 254: "Establish canonical debt, maturity, EBITDA bridge and period comparisons; do not record October payout as FY2024 cash outflow"
   - Problem: The October payout appears here with no amount, date or nature. Its size, about USD 4,348 million (special dividend and equivalents), is only defined higher up the page (lines 20, 95 and 125). A reader landing on this row cannot gauge how much it matters.
   - Fix: Where the payout is mentioned, give its amount, unit and nature, e.g. the approximately USD 4,348 million special dividend paid in October 2024.
6. **Low · visual** (Auditor)
   - Where: CP-1A_s-1.png: the 'Request' heading and paragraph, and the 'On this page' nav listing 'Request', 'Manual method checks' and 'Next module' alongside the analytical sections
   - Problem: The Request and Next module headings use the same styling as analytical sections like 'Company and operating model', and they sit in the reading order (Request comes straight after Maps). Nothing visually tells the reader which sections are run provenance and which are analysis.
   - Fix: Put provenance sections visibly apart from the analysis, for example grouped at the foot under one muted 'Run details' heading, or leave them out of the reader nav.

### Sources

Kind: prose/table · handoff lines 4-13 · verdict **BLOCK**

- Narrative: The Sources section correctly holds the references, but it uses pipeline wording ("supplied handoff", "pin", "transport", "Module / role", "context"), and it keeps here, instead of in Limitations, the retrospective-evidence caveat that the bottom line depends on.
- Visual: The section is a clean three-row bordered table followed by one paragraph. A hash column a reader cannot use and raw file names that wrap dominate it, and it sits mid-page instead of closing the module. There is no chart, map or timeline in this section.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 12: "The supplied handoff's pin establishes its acceptance and lineage for this transport."; line 6 header "Exact source name or supplied handoff | Module / role"; line 10 "CP-0; supplied accepted handoff" (rendered "Source readiness; supplied accepted handoff", shot CP-1A_s-4.png y~220-450)
   - Problem: Pipeline words the house standard bans from reader text appear on screen: "handoff" (three times), "pin", "acceptance", "lineage", "transport" and the "Module" column header. The rendered page also says "accepted handoff" while the page badge reads "Candidate · not accepted", so the reader sees two statements about acceptance that seem to contradict each other.
   - Fix: Rename the column to "Source" / "Role", describe the readiness input as something like "Source readiness review (earlier step in this run)", and delete the pin/lineage/transport sentence or move it out of the reader view.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: Line 12: "The annual filing is used retrospectively, not as information known on the balance-sheet date; subsequent payments are separated from FY2024 cash flows."
   - Problem: This caveat matters to the credit view: the bottom line relies on the October distribution, which came after the 30 September 2024 balance-sheet date, and on a 10-K filed after that date. But the caveat appears only as the last clause of the Sources paragraph and is missing from Limitations (lines 37-44), so a reader who stops at Limitations never sees it.
   - Fix: Add the retrospective-evidence and post-period-payment caveat as a bullet under Limitations, and keep Sources to a statement of what was used.
3. **Medium · narrative** (New reader)
   - Where: Line 9: "| context | Dated run inputs only; not issuer evidence |"
   - Problem: "context" is an internal input label written in lower case and never defined. The Company profile table below cites "context, page 1" as the source for country and sector, so the reader has to work out what "context" contains and why a non-evidence input backs a stated fact.
   - Fix: Name the input in reader terms (for example "Run set-up: issuer name, sector and as-of date") and say what it supports.
4. **Medium · visual** (New reader, Auditor)
   - Where: Sources table, sha256 column (shot CP-1A_s-4.png, crop CP-1A-031-a.png, right third of the table)
   - Problem: Three 64-character hexadecimal hashes take about a third of the table width under a lower-case "sha256" header. A portfolio manager cannot use them, and they squeeze the source-name column so the file name wraps.
   - Fix: Drop the hash column from the reader view, or put it behind a fold or tooltip, and give the width to a readable source title (for example "TransDigm 10-K, fiscal year ended 30 Sep 2024").
5. **Low · narrative** (Saboteur)
   - Where: Line 12: "Other inventoried issuer sources were not needed for this module."
   - Problem: The run's inventory also held the March and June 2024 10-Qs and a December 2024 10-Q, which falls after the as-of date. The section says they were "not needed" without naming them, so the reader cannot judge whether interim filings would have changed the governance or cash-retention view.
   - Fix: Name the sources left out in one short clause, with the reason each was excluded (for example post as-of date, or superseded by the annual filing).
6. **Low · visual** (Auditor, New reader)
   - Where: Sources table, first column (crop CP-1A-031-a.png, row 1): "TDG_2024-09-30_10-K_0001260221-24-\n000083_tdg-20240930.htm.jsonl"
   - Problem: The raw file name, with its .htm.jsonl extension, wraps in the middle of the accession number. This is the same raw string the reader meets repeated in every Source column below, and it is unreadable as a citation.
   - Fix: Show a short human title with the filing date in the table, and keep the exact file name as secondary text or in a tooltip.
7. **Low · visual** (New reader)
   - Where: On-this-page navigation and page order (shot CP-1A_s-4.png left rail, y~540-560): Sources sits between "Request" and "Company and operating model"
   - Problem: Sources comes in the middle of the page, before the appendix tables that cite it, so it does not work as a closing reference list. A reader scrolling the tables has to scroll back up to find what a citation means.
   - Fix: Render Sources at the end of the module page, after the analytical appendix tables, to match the VMO2 reading order.

### Bottom line

Kind: reader passage · handoff lines 16-22 · verdict **CONCERNS**

- Narrative: The bottom line does put the judgement first and the credit point (earnings are durable, but cash goes to shareholders rather than to deleveraging) is clear, but it runs to two ~90-word paragraphs mixing in Key findings detail, leaves the liquidity measure and the distribution amount undefined, and ends on a list of denials.
- Visual: There is no chart in this section; it is laid out as about 170 words of headline-weight bold with no visible \"Bottom line\" label and no Basis links, unlike every other passage on the page, and its monospace figures clash with the bold type around them.

1. **High · visual** (Auditor, Saboteur)
   - Where: Basis lines at handoff lines 18 and 21 ("Basis: TDG_2024-09-30_10-K..., pages 4–5; ... page 10; ... page 54" and "... pages 54–56; calculation C3"); render/CP-1A.dom.html section#bottom-line; shots/CP-1A_bottom-line.png y≈185–690
   - Problem: Both bottom-line paragraphs render with no Basis link: the section has 0 basis-link elements, while every Key findings and Limitations item has one. The only route to a source is a click on one of the five figure buttons, so claims with no figure, such as "finance a large distribution with new secured debt and existing cash", show no source on the page.
   - Fix: Render each bottom-line paragraph's Basis line as the same trailing Basis link the other passages use, so the module's most important claims carry a visible source.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: line 20: "The filing's cash-liquidity measure falls from USD 7,267 million reported to USD 2,919 million after that payment on an illustrative pro forma basis."
   - Problem: The reader is never told what "cash-liquidity measure" contains (cash alone, or cash plus undrawn revolver) or how large the October distribution was. That leaves them to work out the roughly USD 4,348 million payout from two numbers, and its relationship to the USD 3,000 million financing stays unclear. "Illustrative pro forma" further weakens the module's headline figure without saying what was assumed.
   - Fix: Name the components of the liquidity measure, state the distribution amount and its funding split (new secured debt versus existing cash), and give the one assumption behind the pro forma figure in plain words.
3. **Medium · narrative** (New reader)
   - Where: line 17: "Management estimates proprietary products generated approximately 90% of FY2024 sales and aftermarket activity approximately 55%; designed-in components create recurring replacement demand, while certification requirements impede substitution."
   - Problem: The bottom line repeats business-model detail (channel mix, certification barriers) that belongs in Key findings. Paragraph 2 then opens with a second framing ("The creditor distinction is..."), so the judgement is spread over two long paragraphs of about 90 words each instead of being stated once.
   - Fix: State the judgement once in two or three short sentences (durable earnings, but cash is extracted rather than retained for creditors) and move the mix percentages and certification detail into Key findings.
4. **Medium · visual** (New reader, Auditor)
   - Where: Bottom line block, shots/CP-1A_bottom-line.png y≈185–690 (crop tmp/CP-1A-032-a.png); DOM: <h4 class="sr-only">Bottom line</h4>
   - Problem: About 170 words are set entirely in large heading-weight bold across about 19 lines, with no visible "Bottom line" label (the heading is screen-reader only). The result reads as a wall of bold text rather than a headline judgement, and the reader cannot tell where the conclusion ends and the supporting detail begins.
   - Fix: Keep only the one- or two-sentence judgement in headline weight, set the supporting sentences in body type, and show the "Bottom line" label as the other sections show theirs.
5. **Low · narrative** (Saboteur)
   - Where: line 20: "This is an extraction-oriented capital-allocation finding, not evidence of a coercive liability-management transaction, a contractual breach or imminent default."
   - Problem: The bottom line ends on three denials in report-about-itself wording ("finding"). A skimming reader is left with what the risk is not, which partly undoes the judgement that opens the paragraph.
   - Fix: End on the positive creditor implication (for example, that underwriting should rely on cash retained after allocation decisions) and put the exclusions in a short clause before it.
6. **Low · visual** (Auditor)
   - Where: Figure buttons "USD 3,000 million", "USD 7,267 million", "USD 2,919 million" in tmp/CP-1A-032-a.png y≈420–530; basis popup text "calculation C3"
   - Problem: Figures are set in regular-weight wide monospace with dotted underlines inside bold proportional text, which breaks the line rhythm and makes the key numbers look lighter than the words around them. The figure popup also shows the internal label "calculation C3", which a reader cannot resolve without another page.
   - Fix: Match figure weight and font to the surrounding text, keeping the dotted underline as the only cue, and describe calculations in the popup in words (for example, "reported liquidity less October distribution").

### Key findings

Kind: reader passage · handoff lines 23-32 · verdict **BLOCK**

- Narrative: The four bullets lead with bolded judgements in the right order and keep source references out of the sentences, but bullet 4 leaves the payouts undefined and bullets 2 and 3 give figures without their full split or scale.
- Visual: The section is a clean four-bullet list with readable line length, but bullets 2-4 have lost their Basis links on the page, and the figure chips are monospace and applied inconsistently.

1. **High · visual** (Auditor, New reader (promoted))
   - Where: Key findings bullets 2-4 (handoff lines 26-31, each with its own 'Basis:' line); screenshot CP-1A_key-findings.png, region x340-1040 y220-830 (crop CP-1A-033-a.png); DOM render/CP-1A.dom.html: only bullet 1 ends in a <button>Basis</button>
   - Problem: Only the first bullet shows its Basis link. Bullets 2, 3 and 4 have Basis lines in the handoff (lines 27, 29, 31), but on the page their sources can only be reached through the figure chips (data-basis on each figure button). A reader sees no source for the non-numeric claims, such as the stated excess-cash priorities and the provisional purchase accounting, which breaks the rule that every paragraph has a Basis line.
   - Fix: Show a Basis link at the end of every bullet whose handoff paragraph has a Basis line, whether or not the bullet also contains figure chips.
2. **Medium · narrative** (New reader)
   - Where: line 30: "The issuer paid approximately USD 2,020 million from existing cash in November 2023 before the larger September declaration."
   - Problem: The bullet never says what was paid (a special dividend or distribution to shareholders) or the size of 'the larger September declaration'. Within this section the reader cannot tell that both are shareholder payouts or how big the second one was, which is the evidence behind the bullet's headline.
   - Fix: Name the payment type and give the size and date of the September declaration in the bullet, so the extraction finding stands on its own.
3. **Medium · narrative** (Saboteur)
   - Where: line 26: "Defense contributed approximately 40% of FY2024 sales and commercial OEM approximately 27%; the largest ten customers represented approximately 42%"
   - Problem: A bullet headed 'End-market breadth' leaves out the largest commercial channel, commercial aftermarket at 31% (table line 53). The only figures shown are 40% and 27%, so the reader cannot see the full split. The defense figure also overlaps the 55% aftermarket figure in the Bottom line, a point the table warns about and this bullet does not.
   - Fix: Give the full end-market split (commercial aftermarket, commercial OEM, defense, non-aerospace) and note that defense includes defense aftermarket.
4. **Medium · narrative** (Saboteur)
   - Where: line 28: "FY2024 acquisition spending was USD 2,347 million net of cash acquired."
   - Problem: The bullet gives the figure without the scale a credit reader needs. Acquisition spending exceeded FY2024 operating cash flow of USD 2,045 million, but that comparison appears only later under Contrary evidence. A committee member reading the key finding alone would underrate how much cash acquisitions take.
   - Fix: Set the acquisition spending against the same year's operating cash flow (or free cash flow) inside the bullet.
5. **Low · narrative** (New reader)
   - Where: line 30: "Observed allocation favors equity optionality over automatic debt reduction." and "not capitalize operating cash flow as if it were reserved for creditors"
   - Problem: 'Equity optionality' and 'capitalize operating cash flow' are analyst shorthand. 'Capitalize' can also be read in its accounting sense, which blurs the judgement in the bolded lead.
   - Fix: Say it plainly, e.g. that cash goes to acquisitions and shareholder payouts before debt repayment, and that cash flow should not be treated as available for debt service.
6. **Low · visual** (Auditor)
   - Where: Screenshot CP-1A_key-findings.png crop CP-1A-033-a.png: figure chips 'USD 2,347 million', 'USD 2,020 million' and '40%' versus plain 'approximately 25 years to 30 years' in bullet 1
   - Problem: Some figures render as monospace chips with dotted underlines inside proportional prose, which breaks the reading rhythm. Figures are also marked inconsistently: the service-life figure in bullet 1 is not a chip, so the reader cannot tell which numbers are traceable.
   - Fix: Mark every quantified figure the same way, and use a chip style that matches the body typeface's weight and width.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 33-36 · verdict **BLOCK**

- Narrative: The passage puts judgement first and keeps sources out of the sentences, but its main counterweight has no amount and is checked against zero, its cash-generation figures are not set against the same year's outflows, and the triggers that would change the view cannot be monitored.
- Visual: This section has no chart, map or timeline; it is one wide prose block at a readable line length, but it has no visible Basis link while the Limitations bullets do, and its monospace figure chips break up the body text.

1. **High · narrative** (Saboteur, New reader)
   - Where: 1.response.md:34 "The distribution-adjusted liquidity figure remains positive, so extraction should not be conflated with an inability to fund the business." (also "the remaining funding cushion")
   - Problem: The main counterweight gives no amount, basis or date. The USD 2,919 million illustrative pro forma cash figure appears only in the Bottom line (line 20). A cash balance can never be negative, so "remains positive" tests nothing and makes the cushion look stronger than the paragraph proves.
   - Fix: State the cushion here as a number with its basis and date (for example "USD 2,919 million cash, illustrative pro forma after the October distribution") and compare it with a named need such as annual debt service or the size of the payout, not with zero.
2. **Medium · narrative** (Saboteur)
   - Where: 1.response.md:34 "FY2024 operating cash flow was USD 2,045 million versus USD 1,375 million in FY2023, while capital expenditure was USD 165 million versus USD 139 million."
   - Problem: Cash generation is offered as the counterweight without setting it against the same year's uses the module itself reports: USD 2,347 million of acquisitions (line 28) and the USD 2,020 million November payout (line 30). Free cash flow of about USD 1.9 billion did not cover acquisitions alone, so the counterweight reads stronger than the page's own figures support.
   - Fix: Put the FY2024 cash generation next to that year's acquisition and distribution outflows, so the reader can see how much retention the counterweight actually stands for.
3. **Medium · narrative** (New reader)
   - Where: 1.response.md:34 "Sustained cash retention, debt repayment after acquisitions, and a documented change in allocation priorities would improve the creditor view; weakening aftermarket mix, supply-related shipment delays or further debt-funded payouts would weaken it."
   - Problem: The things that would change the view are put in the last clause of one seven-sentence block, after the contrary evidence, and none of them can be checked: "sustained", "weakening" and "further" have no level, metric or period a committee could monitor.
   - Fix: Split the passage into a contrary-evidence paragraph and a short list of triggers, each with an observable measure and direction (for example net debt reduced after a year with acquisitions, or the aftermarket share of sales below a stated level).
4. **Medium · narrative** (Auditor)
   - Where: 1.response.md:35 Basis line (pages 4, 54–57); render/CP-1A.dom.html section#contrary-evidence has 0 basis-link buttons
   - Problem: This paragraph shows no visible Basis line on screen, while each Limitations bullet below it ends in a "Basis" link. The source can be reached only through the clickable figure chips, so the unquantified claim "Management reports that aftermarket sales historically produced higher gross profit" has no visible source.
   - Fix: Render the paragraph's Basis line as the same trailing "Basis" link the Limitations bullets use.
5. **Low · narrative** (New reader)
   - Where: 1.response.md:34 "so extraction should not be conflated with an inability to fund the business"
   - Problem: "Extraction" and "distribution-adjusted liquidity figure" are the module's own shorthand, defined only by context in the Bottom line. A reader who jumps to this heading from the page navigation meets undefined terms.
   - Fix: Use plain terms here, such as "shareholder distributions" and "cash after the October distribution".
6. **Low · visual** (Auditor)
   - Where: shots/CP-1A_contrary-evidence.png, region x 330-1440, y 200-480 (crop tmp/CP-1A-034-a.png): the figure chips "USD 2,045 million", "USD 1,375 million", "USD 165 million", "USD 139 million"
   - Problem: Each figure is set in bold monospace with a dotted underline inside proportional body text, so four chips in two lines break the reading rhythm and make the line spacing look uneven. The chips also make capex look as important as operating cash flow.
   - Fix: Show figure chips in the body typeface with a light underline or tint, so the figures stay clickable without breaking the line.

### Limitations

Kind: reader passage · handoff lines 37-44 · verdict **BLOCK**

- Narrative: The section is in the right place (last of the four required passages), its sources sit in Basis lines and it uses no CP codes, but it leaves out the two limits that most bound the bottom line: the USD 2,919 million figure includes undrawn availability, and room for future payouts is unknown without the legal documents.
- Visual: This is a plain three-bullet prose list at a readable width with no chart of its own; the only visual faults are that it runs into the Timeline heading below with no separation, and the inline Basis controls are faint grey text.

1. **High · narrative** (Saboteur, Auditor (promoted from Medium))
   - Where: Limitations list, lines 37-43, which omits the caveat on the headline liquidity figure. Bottom line line 20: "The filing's cash-liquidity measure falls from USD 7,267 million reported to USD 2,919 million after that payment on an illustrative pro forma basis." The caveat appears only in calculation C3, line 216: "includes availability rather than only cash, ignores other subsequent movements"
   - Problem: The module's main number is called "cash-liquidity" in the bottom line, but it includes undrawn availability and ignores other movements after the year end. That qualification never reaches the Limitations list, so a reader who stops at Limitations will treat USD 2,919 million as cash on hand.
   - Fix: Add a limitation saying that the USD 2,919 million payment-adjusted figure includes undrawn availability and ignores other movements after 30 September, so it is not the October cash balance.
2. **Medium · narrative** (Saboteur)
   - Where: Limitations, lines 37-43, have no bullet for the legal-capacity gap that Gaps line 228 rates "Blocking for permission and headroom decisions" (also G5, line 166: "no future leakage headroom quantified")
   - Problem: The bottom line rests on future shareholder extraction, yet the most binding limit on that view is missing from Limitations. The executed credit agreement and indentures were not available, so the remaining room for further payouts is unknown. That limit sits only in an appendix table far down the page.
   - Fix: Add a limitation saying that, without the executed debt documents, the module cannot say how much more the issuer may legally pay out, which bounds the extraction conclusion.
3. **Medium · narrative** (New reader, Saboteur (promoted from Low))
   - Where: line 42: "The internal-control opinion excludes the recent acquisitions. Reporting assurance cannot be extended uniformly to the enlarged perimeter"; line 40: "Recent purchases contribute results only from acquisition"
   - Problem: The reader is not told which acquisitions are meant, what they cost or how large the excluded perimeter is. G4 (line 165) gives the size: 9.8% of assets and 2.0% of net sales. Without it the reader cannot weigh the caveat. "Contribute results only from acquisition" is also garbled; it means "from the acquisition date".
   - Fix: Name the four FY2024 acquisitions and the excluded share (9.8% of assets, 2.0% of net sales), and say "from their acquisition dates".
4. **Low · narrative** (New reader)
   - Where: line 38: "not a channel-level margin or price-volume bridge ... the size of the earnings cushion under a mix reversal"; line 42: "enlarged perimeter"
   - Problem: "Price-volume bridge", "mix reversal" and "perimeter" are analyst shorthand. A committee member has to translate them before seeing the credit consequence: no one can size how far earnings fall if aftermarket sales shrink.
   - Fix: State the consequence in plain words first, e.g. "we cannot size how much margin is lost if the aftermarket share falls", then the missing data.
5. **Low · visual** (Auditor)
   - Where: Screenshot CP-1A_limitations.png, crop (330,210)-(1440,560) saved as /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-1A-035-a.png: the last bullet's "Basis" line and the "Timeline" heading
   - Problem: The third bullet ends about 10 px above the "Timeline" heading. There is no space or rule between them, so the end of the prose and the start of the chart panel run together, and the heading looks like part of the list.
   - Fix: Put the usual space between sections (or a rule) between the end of the Limitations list and the Timeline panel.
6. **Low · visual** (Auditor, New reader)
   - Where: Same crop: the inline grey "Basis" buttons at the end of each bullet (DOM class basis-link)
   - Problem: The Basis control is small grey text that runs on from the sentence, with no underline or button look. It reads like a stray word, not a link to the source, and its contrast is weaker than the body text.
   - Fix: Style Basis as an obvious control (link colour, underline or chip) at body-text contrast.

### Company and operating model

Kind: prose/table · handoff lines 45-60 · verdict **CONCERNS**

- Narrative: The section is a one-sentence lead plus an 8-row, 6-column table. The values I checked against the filing are exact (capex 165/139; working-capital uses 84/104/11). The lead names the drivers without giving a verdict, the working-capital row leaves out the FY2023 comparison that would change how it reads, and an unexplained evidence-category taxonomy leaks into the reader's view.
- Visual: There is no chart, map or timeline in this section. The table sits fully visible and fits the 1440 px page, but the raw source file names wrap to five lines and the duplicate Basis chips make it tall and dense (about 840 display px for 8 rows).

1. **High · visual** (New reader + Auditor (promoted from Medium))
   - Where: Source column, every row (lines 52-59), e.g. "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 4–6"; shot CP-1A_s-45.png, table x≈1020-1160, y≈265-1105 (display px)
   - Problem: Every row's Source cell shows the raw pipeline file name, including the SEC accession number and a `.jsonl` extension. It wraps to five lines in each of the 8 rows, so it is the tallest cell in most rows and sets the table's height. A reader is shown a machine artefact instead of a citation, and the same string appears eight times.
   - Fix: Show a reader label such as "FY2024 10-K, pp. 4–6" in the Source column and keep the file identity in `## Sources`.
2. **Medium · narrative** (Saboteur)
   - Where: line 47: "The model ties aircraft installation to subsequent replacement demand, but mix, certification and working-capital timing determine how much of that demand becomes cash."
   - Problem: The section's lead names the factors that matter but gives no verdict on whether TDG converts demand into cash well or badly in FY2024. The reader cannot tell if the operating model is a credit strength or a weakness.
   - Fix: Open with a judgement on FY2024 cash conversion (strong, adequate or weak), then name the drivers.
3. **Medium · narrative** (Saboteur)
   - Where: line 58: "FY2024 cash uses: receivables USD 84 million; inventory USD 104 million; payables USD 11 million" with consequence "Earnings durability does not eliminate cash-conversion volatility"
   - Problem: The figures match the cash-flow statement, but the FY2023 comparatives are left out. Receivables were (212) and inventory (261) in FY2023, so the working-capital drag fell sharply in FY2024. Showing only FY2024 next to a volatility warning makes the drag look like a current deterioration. The Capital spending row just above does show both years.
   - Fix: Give FY2023 working-capital uses alongside FY2024, as the capex row does, and state the direction of change.
4. **Medium · narrative** (New reader + Auditor)
   - Where: Category column, lines 52-59: "Documentary Fact", "Management Language", "Analyst Interpretation"
   - Problem: An internal evidence taxonomy appears as a full column but is never explained to the reader. It is also applied inconsistently: the Cost and certification row (line 56), which contains the filed figure "approximately 4% of sales", is labelled "Analyst Interpretation".
   - Fix: Either drop the column or replace it with a defined, reader-facing label such as "Reported / Management view / Our view", applied to each cell's content.
5. **Low · narrative** (New reader)
   - Where: line 53, Transmission column: "Total aftermarket includes defense aftermarket; it must not be added to the end-market split"
   - Problem: This cell gives an instruction about handling the data instead of explaining how revenue mix turns into cash or risk, which is what the column heading promises. The "must not be added" register reads like a note to the pipeline.
   - Fix: Put the overlap caveat in the evidence cell as a plain clarification, and use the Transmission cell for the cash effect of the aftermarket mix.
6. **Low · visual** (Auditor)
   - Where: Row labels such as "Core activity and products Basis", "Revenue streams Basis"; shot CP-1A_s-45.png, column 1, y≈280-1045
   - Problem: Each row label has a grey "Basis" chip even though the same row already has a Source cell. Together with the "Basis" chip after the lead sentence, the reader sees two citation devices per row, and the chip breaks label words onto extra lines ("Customer concentration / Basis").
   - Fix: Use one citation device per row: keep the Source column and drop the in-label Basis chip.

### Company profile

Kind: prose/table · handoff lines 61-74 · verdict **CONCERNS**

- Narrative: The section opens with a caveat rather than a positive judgement. Its lead claim about the guarantor perimeter has no support in the table. Its Source column cites a pipeline module and an internal \"context\" input.
- Visual: The section has no chart, map or timeline, only a five-column table. That table is readable but crowded by repeated raw file names and duplicate Basis chips, and the narrow first column wraps labels into tall rows.

1. **High · narrative** (Auditor, New reader)
   - Where: line 73: "Source readiness (CP-0); context, page 1" and line 68: "context, page 1; TDG_2024-09-30_10-K_..." (rendered as "Source readiness; context, page 1" in CP-1A_s-61.png, Source column, last row)
   - Problem: The Source column cites a pipeline module ("Source readiness", with the CP-0 code in the handoff) and an internal input called "context, page 1". Neither is a document the reader can open, and the house rule keeps pipeline vocabulary off the page. Two personas caught it, so it is promoted from Medium.
   - Fix: Cite the real document the classification and the missing-ownership statement rest on, or state "Not in the supplied filings" in reader language with no module or input labels.
2. **Medium · narrative** (Saboteur)
   - Where: line 63: "geographical breadth does not make the guarantor perimeter identical to the consolidated business."
   - Problem: The bottom line rests on a guarantor perimeter, but no row in the table says who guarantees the debt or how much of revenue or assets sits outside it. A committee member gets a warning with nothing to size it, and the claim has no support in the section.
   - Fix: Add a row giving the guarantor and non-guarantor split from the filing, or record it as an explicit gap, so the lead sentence is supported in the section.
3. **Medium · narrative** (Saboteur)
   - Where: line 63: "The consolidated parent is not interchangeable with the operating debt issuer, and geographical breadth does not make..."
   - Problem: The lead sentence only says what is not true. It gives no positive judgement on the profile, such as a US-weighted, three-segment aerospace issuer whose debt sits at a 100%-owned subsidiary, so the judgement-first rule is met only in form.
   - Fix: Open with a positive one-sentence credit judgement on the profile, then add the perimeter caveat.
4. **Medium · narrative** (New reader)
   - Where: line 72: "FY2024 United States USD 5,032 million; foreign countries USD 2,908 million; total USD 7,940 million. FY2023: USD 4,265 million; USD 2,320 million; USD 6,585 million, respectively"
   - Problem: Two years of figures are packed into one cell and paired by "respectively". The reader has to decode which number is which, and the obvious credit points (about 37% foreign share, sales growth of about 21%) are not stated.
   - Fix: Split this into a small FY2023/FY2024 table by geography with a share column, or state the share and the change next to the figures.
5. **Medium · visual** (Auditor, New reader)
   - Where: Company profile table, Source column, CP-1A_s-61.png crop x 340-1400, y 220-1000 (scratchpad/tmp/CP-1A-037-a.png)
   - Problem: Each Source cell repeats the raw file name "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl", up to twice per cell. The wrapping makes this the tallest, noisiest column and pushes row heights, while every row also carries a "Basis" chip in Profile item that duplicates it. Two personas caught it, so it is promoted from Low.
   - Fix: Render the source as a short reader label ("FY2024 10-K, p. 124") and keep either the Source column or the Basis chip, not both.
6. **Low · narrative** (New reader)
   - Where: line 68: "United States, Aerospace; run classification, consistent with the described operations but not used as legal-domicile evidence"
   - Problem: "run classification" is pipeline wording, and the caveat about legal domicile is hard for a reader who does not know the system to parse.
   - Fix: Say "US-based aerospace components manufacturer (per the 10-K)" and drop the remark about the classification's origin.
7. **Low · visual** (Auditor)
   - Where: Company profile table, Profile item column, CP-1A_s-61.png at original y about 560-1000
   - Problem: The narrow first column wraps labels such as "Direct operating-company ownership" over four lines and orphans the "Basis" chip onto its own line in the last row. This leaves uneven, tall rows with empty space in the Category column.
   - Fix: Widen the Profile item column (narrow Category, which only ever holds two words) so labels sit on one or two lines.

### Transaction summary and new debt issues

Kind: prose/table · handoff lines 75-82 · verdict **BLOCK**

- Narrative: Both paragraphs (L77, L80) are made up of facts and caveats with no credit judgement, open with input-availability wording, and leave the scale of the debt-funded special dividend and the acquisitions out of the prose, so the reader has to work the conclusion out from the events table below.
- Visual: The section has no chart, map or timeline; on the page it is two dense full-width paragraphs, with a Basis chip on paragraph 1 only and monospace figure buttons that clash with the body type (checked in the s-75 screenshot crop and the rendered DOM).

1. **High · narrative** (Saboteur, Auditor)
   - Where: L77 "No proposed live transaction or deal mandate is supplied. This is a historical business and capital-allocation snapshot, not a financing approval." / L80 "The stated use linked the financing and existing cash to the special dividend and equivalents."
   - Problem: No sentence in the section gives a credit view. It opens with what is absent, and the main fact for a creditor (USD 3,000 million of new senior secured debt raised to help fund a special dividend paid in October) only appears in paragraph 2's third sentence, worded neutrally as "stated use linked". This breaks the judgement-first rule, and a committee member skimming the section could miss that it describes a debt-funded shareholder distribution.
   - Fix: Open with a one-sentence judgement on the September secured debt-funded special dividend and what it means for leverage and creditor priority, then the facts, with the limitations last.
2. **Medium · narrative** (Saboteur)
   - Where: L77 "The issuer completed multiple acquisitions during FY2024 and issued new secured debt concurrently with the September distribution declaration."
   - Problem: "Multiple acquisitions", "new secured debt" and "the September distribution" have no count, amount or per-share figure in the prose, although the same page's events table has them (four acquisitions of about USD 57/171/1,385/647 million, USD 3,000 million of debt, USD 75.00 per share and about USD 4,348 million paid). The reader cannot judge scale from the summary paragraph.
   - Fix: State the acquisition count and total cash, the USD 3,000 million issuance total and the dividend size (per share and aggregate, with dates) in the summary itself.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: L77 "The acquisition notes establish purchase prices, operating destinations and stated funding, but not seller identities in every case, acquisition returns or a fully reconciled financing model. A sponsor is not identified..."; L80 "The filing's illustrative payment-adjusted liquidity is not the actual October closing cash balance... Legal permission... require operative documentation rather than an inference from successful execution."
   - Problem: Five of the ten sentences are caveats or statements of absence, and they sit between and after the facts. The stack of qualifications drowns out the conclusion. "Payment-adjusted liquidity" is mentioned with no value, so the reader is told a number exists without being given it.
   - Fix: Move the caveats into one closing limitations sentence or the module's Limitations section, and either quote the illustrative payment-adjusted liquidity figure with its basis or drop the mention.
4. **Medium · narrative** (New reader, Auditor)
   - Where: L77 "No proposed live transaction or deal mandate is supplied." / "A sponsor is not identified in the supplied transaction evidence."
   - Problem: "Supplied" and "supplied transaction evidence" describe what went into the pipeline, not the issuer. That is workflow language reaching the reader, and the section opens with it.
   - Fix: Write in issuer terms (for example, that the section reviews completed FY2024 transactions and no new transaction is proposed) without mentioning what was supplied.
5. **Medium · visual** (Auditor)
   - Where: Screenshot CP-1A_s-75.png, crop x330-1440, y220-440 (tmp/CP-1A-038-a.png): paragraph 2 ends "...inference from successful execution." with no Basis chip; DOM s-75 second <p> has no basis-link button although handoff L81 carries a Basis line
   - Problem: Paragraph 1 shows a "Basis" chip but paragraph 2 does not; its basis can only be reached through the two figure buttons. A reader cannot see that paragraph 2's non-numeric claims (stated use, timing, legal permission) are sourced, and the two paragraphs follow different conventions.
   - Fix: Render a paragraph-level Basis chip on every prose paragraph that has a Basis line, whether or not it also has figure buttons.
6. **Medium · visual** (New reader)
   - Where: Screenshot CP-1A_s-75.png, y≈190-345 (displayed): two unbroken paragraphs set across the full ~1,100 px content width
   - Problem: Each paragraph runs to roughly 80-90 words at about 150+ characters per line, so the reader gets two dense text blocks with nothing to anchor the eye. A section titled "Transaction summary" offers no sources-and-uses or issuance table even though it covers four acquisitions, a USD 3,000 million issuance and two special dividends.
   - Fix: Narrow the prose measure and give the transaction facts a compact table (instrument, amount, date, use) beneath one or two short judgement sentences.
7. **Low · narrative** (New reader)
   - Where: L77 "The acquisition notes establish purchase prices..."; L80 "the special dividend and equivalents"; L77 "September distribution declaration"
   - Problem: In a section about new debt notes, "acquisition notes" can be read as debt notes rather than the filing's acquisition footnotes. "Equivalents" (dividend equivalents on equity awards) is never defined, and the same event is called both "distribution" and "special dividend".
   - Fix: Say "the acquisition disclosures in the financial statements", define "dividend equivalent payments on equity awards" the first time it appears, and use one term for the special dividend.
8. **Low · visual** (Auditor)
   - Where: Screenshot crop tmp/CP-1A-038-a.png: "USD 1,500 million" figure buttons in paragraph 2
   - Problem: The figure buttons are drawn in bold monospace with a dotted underline, which breaks the line's typography, while comparable figures in paragraph 1 (FY2024, September) and the dividend amounts are plain text. The emphasis therefore looks arbitrary.
   - Fix: Style figure buttons in the body font with a subtle underline, and apply the style to every sourced figure in the section.

### Events: Issuer history

Kind: timeline · handoff lines 83-96 · verdict **BLOCK**

- Narrative: The event table is factually specific and keeps periods and units, but it has no judgement-first lead, leaks pipeline wording ('legal workflow', 'Source readiness (CP-0)') and puts raw ingest filenames in front of the reader.
- Visual: The timeline lane is unreadable: a 1993 outlier squeezes all eight FY2024 events into a blob at the right edge, under axis labels at a precision the events do not have. The companion table wraps dates and spends width on constant columns.

1. **High · visual** (Saboteur, Auditor)
   - Where: Timeline panel, 'Issuer history' lane, CP-1A_timeline.png crop (330,180)-(1440,320) = tmp/CP-1A-039-a.png; DOM marker positions left:97.08% to 99.74%
   - Problem: The 1993 formation marker stretches the axis over 31 years, so all eight FY2024 events (USD 2,020m and USD 4,348m dividends, four acquisitions, the USD 3,000m debt issue) pile into one unreadable blue blob at the right edge, between 97% and 99.7% of the width. The reader cannot see the sequence of dividend, acquisitions and debt-funded payout that the timeline exists to show.
   - Fix: Put the 1993 inception on a broken axis or in a footnote and scale the lane to FY2024 (Oct 2023 to Oct 2024), so each event gets its own legible marker and the post-balance-sheet October payment sits visibly after 30 September.
2. **Medium · narrative** (Auditor, New reader)
   - Where: line 93: 'Completed funding raises debt service and finances shareholder extraction; legal analysis belongs to the legal workflow'
   - Problem: 'belongs to the legal workflow' is pipeline wording that the house standard bars from reader text. It also tells a credit committee member nothing: they get no hint whether the USD 3,000m secured issuance was within permitted capacity.
   - Fix: End the Credit relevance cell at the credit point, and if covenant capacity is unassessed, say so in reader terms (e.g. 'covenant headroom not assessed here; see Legal & covenants').
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 87 onward, Source column: 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 5; Source readiness (CP-0) for publication date' (repeated on all 9 rows)
   - Problem: Each row's source is a raw ingest filename with the internal '.jsonl' extension, plus a pointer to the internal 'Source readiness' step for the publication date. The handoff carries the module code 'CP-0' (stripped on screen, but 'Source readiness for publication date' still renders). The column runs to 5-6 wrapped lines per row and dominates the table.
   - Fix: Cite the source as the reader knows it (e.g. 'FY2024 10-K, p. 39'), with the publication date stated once in the section, not as a per-row pointer to a pipeline step.
4. **Medium · narrative** (Saboteur)
   - Where: lines 83-96: table with no lead sentence; e.g. line 88 'approximately USD 2,020 million from existing cash' and line 95 'Approximately USD 4,348 million special dividend ... paid using new secured debt'
   - Problem: The section opens straight into a 9-row table with no judgement sentence. The committee has to add up the figures themselves to see the credit story: about USD 6.4bn of special dividends around FY2024 against about USD 2.3bn of acquisitions and USD 3.0bn of new secured debt. The bottom line is buried in the rows.
   - Fix: Lead with one bottom-line sentence that states the FY2024 sequence and its net effect on leverage, judgement first, before the table.
5. **Medium · visual** (Saboteur, New reader)
   - Where: Timeline axis labels '1993-01-01' and '2024-10-31', CP-1A_timeline.png top of Timeline panel
   - Problem: The axis endpoints show day-level dates that no event has: formation is year-precision ('1993', line 87) and the last payment is month-precision ('2024-10', line 95). The drawing therefore claims precision the source does not give.
   - Fix: Label the axis ends at the precision of the events they bound (e.g. '1993' and 'Oct 2024'), or label by year ticks.
6. **Medium · visual** (New reader, Auditor)
   - Where: Events: Issuer history table, CP-1A_s-83.png y≈210-1290 (display), Event date and Published columns
   - Problem: The seven-column table wraps dates mid-value ('2023-11-' / '27') and appends a 'Basis' link inside the date cell. It also spends two columns on near-constant values ('day' 8 of 9 times, 'Published 2024-11-07' 9 of 9 times). The result is tall, narrow rows that are hard to scan.
   - Fix: Keep dates on one line, state the publication date once above the table, fold precision into the date format (e.g. '1993', 'Oct 2024'), and free the width for Event and Credit relevance.
7. **Low · narrative** (New reader)
   - Where: line 87 Status: 'Historical — inception of our company in 1993'; line 95 Status: 'Historical — These payments were made in October 2024; subsequent event'
   - Problem: The Status column restates 'Historical' on every row, then quotes the issuer's first-person filing wording ('our company') and fragments that change capitalisation. It adds no information and reads as pasted source text.
   - Fix: Drop the Status column, or reduce it to a short flag such as 'After balance-sheet date' that appears only where it applies.
8. **Low · narrative** (Saboteur)
   - Where: line 87 Credit relevance: 'Establishes long acquisition history, not a guarantee of future returns'
   - Problem: This is boilerplate caveat and carries no credit judgement. A company's formation date does not establish an acquisition history.
   - Fix: Either state the credit point (e.g. a 30-year serial-acquirer model funded with debt) or drop the formation row from a FY2024 credit timeline.

### Cash generation and cash retention

Kind: prose/table · handoff lines 116-126 · verdict **CONCERNS**

- Narrative: The figures match the 10-K, but the liquidity row calls a measure 'cash' when it includes USD 1,006 million of undrawn facilities, and that caveat appears only in the appendix. The bottom line also hedges instead of giving a judgement.
- Visual: This is a prose-and-table section with no chart; the long source filenames dominate the table layout and the figure columns wrap badly.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 125: "Filing-defined cash liquidity | Illustrative after October dividend: USD 2,919 million | September 30 reported: USD 7,267 million | USD -4,348 million | Do not treat reported liquidity as permanently retained cash"
   - Problem: In the 10-K (page 55), USD 7,267 million is USD 6,261 million cash plus USD 843 million revolver and USD 163 million securitization availability. So the 'payment-adjusted' USD 2,919 million is not cash: it implies about USD 1,913 million of cash once undrawn lines are taken out. The row says 'cash' and its consequence is about 'retained cash', and the warning that the figure 'includes availability rather than only cash' appears only in calculation C3 in the appendix (line 216). A committee member will read the actual cash cushion as about USD 1.0 billion larger than it is.
   - Fix: Split the row into cash and cash equivalents (6,261 reported, about 1,913 after the dividend) and undrawn committed availability (1,006), or say in the row that 2,919 includes USD 1,006 million of undrawn facilities.
2. **Medium · narrative** (Saboteur)
   - Where: line 118: "Operating cash generation improved, but the subsequent distribution materially changes the interpretation of reported liquidity; the comparison below is not a forecast or a covenant calculation."
   - Problem: The bottom line never says what the new interpretation is: there is no direction, size or credit judgement on whether the cash left after the dividend is adequate. Half the sentence is a disclaimer, so the reader gets a hedge instead of a view.
   - Fix: Open with the judgement itself (for example, that liquidity after the dividend is roughly 60% lower and mostly undrawn lines, and whether that is adequate against near-term needs), then move the not-a-forecast caveat to a limitation.
3. **Medium · narrative** (New reader)
   - Where: line 121: "| Measure | Latest / payment-adjusted case | Prior / reported case | Change |" with line 125 "Prior / reported case ... September 30 reported: USD 7,267 million"
   - Problem: The column headers combine two different comparisons. Rows 1 and 2 are year-on-year (FY2024 against FY2023), but in row 3 the 'Prior' column holds the current 30 September balance and 'Change' is a pro forma adjustment. A reader scanning down the column will treat 7,267 as an earlier-period figure.
   - Fix: Put the year-on-year cash-flow rows and the pro forma liquidity bridge in separate tables, or label the liquidity row's cells as 'reported 30 Sep 2024' and 'pro forma for October dividend' and mark the change as a pro forma adjustment.
4. **Medium · narrative** (Auditor, New reader)
   - Where: line 119: "Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 55–57; calculation C1; calculation C2; calculation C3; calculation C4"
   - Problem: References use internal pipeline names: a .jsonl extraction filename and the codes C1 to C4. The codes are only defined in the appendix Calculations register, so the reader needs another part of the page to understand them. The same raw filename is repeated in every Source cell (lines 123 to 125).
   - Fix: Cite the document as the reader knows it (for example 'TransDigm FY2024 10-K, pp. 55–57') and either name each calculation in plain words or link it to its register row.
5. **Medium · visual** (New reader, Auditor)
   - Where: Cash generation table, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots/CP-1A_s-116.png, region x 300-1160, y 250-530 (displayed scale)
   - Problem: The Source column is the widest column and wraps the raw .jsonl filename over four lines in every row, while the figure columns are squeezed: 'Increase USD 670 million' and 'USD -4,348 million' each wrap to three lines. Every Measure cell also carries a 'Basis' chip on top of the Source column, which duplicates it. The numbers the reader came for get the least room.
   - Fix: Shorten the source labels so the Source column narrows, give the figure columns room to stay on one line with right-aligned numbers, and drop either the per-row Basis chip or the Source column.
6. **Low · narrative** (Saboteur)
   - Where: line 124: "Continuing reinvestment remains ahead of discretionary allocations"
   - Problem: It is unclear what 'ahead of' means here: priority, amount or timing. No figure in this section supports the claim, and USD 165 million of capex next to a USD 4,348 million distribution suggests the opposite on size.
   - Fix: State the comparison exactly (for example, capex as a share of operating cash flow) or remove the claim.
7. **Low · visual** (Auditor)
   - Where: Change column, row 'Filing-defined cash liquidity': "USD -4,348 million", same screenshot, around y 460-500 (displayed scale)
   - Problem: Within one column the minus sign sits between the currency code and the number, while the other rows use the word 'Increase'. The sign convention is inconsistent and the eye catches the minus late.
   - Fix: Use one convention for the whole column (for example '−USD 4,348 million', or 'Decrease USD 4,348 million').

## Fundamental credit (CP-2)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001/requests/CP-2/d9958cba20ea0c8cbd2dc72a05fbb21a83897e27cc9f59f187518cf2b9dff809/1.response.md`

### Carried financial observations and definition controls

Kind: prose/table · handoff lines 134-148 · verdict **BLOCK**

- Narrative: This is a data-style table plus one methodological paragraph with no bottom line. Internal codes and module names stand in for definitions and sources. The pre-payout net leverage of 4.51x sits uncontested beside the 5.55x post-payout figure computed just above it.
- Visual: The table is visible and readable at 1440 px with clean row spacing. One misaligned period row (maturities), a stray inline Basis chip and left-aligned figures weaken how quickly a reader can scan it.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 139: "| Net leverage | Approximately 4.51x | Approximately 4.84x | CP-1 C04; reported cash netted without payout adjustment |" (versus line 128 C2-03 "display approximately 5.55x")
   - Problem: The table shows net leverage falling from 4.84x to 4.51x, which reads as deleveraging. But that figure nets USD 6,261 million of September cash, and USD 4,348 million of it was paid out in October. The same page computes about 5.55x after the payout, and the table never says which number is the credit view.
   - Fix: Put the post-payout 5.55x in this row or next to it and say in one line which leverage figure the committee should use and why.
2. **High · narrative** (Saboteur, New Reader)
   - Where: line 144: "| Reported long-term scheduled principal | FY2025 USD 93 million | FY2028 USD 6,637 million |"
   - Problem: This row puts two different maturity years under the column headers "FY2024 / latest case" and "FY2023 / comparator". FY2028 is not a FY2023 comparator, so a reader scanning down the columns gets the wrong idea of the maturity profile.
   - Fix: Move the maturity data out of this two-period table into its own row or table labelled by maturity year, or label the cells so they do not sit under the period headers.
3. **High · narrative** (Auditor, New Reader)
   - Where: lines 138-144 Definition / control column: "CP-1 C04; gross principal / issuer-adjusted EBITDA" … "CP-1 C15; issuer-reported EBITDA"; rendered as "Financial foundation C04" (shot CP-2_s-134.png, table rows y≈300-600)
   - Problem: Internal calculation register codes (C03, C04, C15) are shown on screen in every row. They mean nothing to a reader who has not seen the pipeline, and they break the rule against register codes in reader-facing text.
   - Fix: Remove the codes and keep only the plain-language definition.
4. **Medium · narrative** (Auditor, New Reader)
   - Where: line 146: "The financial foundation's liquidity starting point excludes remaining securitization availability, whereas the business pack carries a broader filing-defined liquidity measure. … This synthesis uses reported cash"
   - Problem: The only prose in the section explains the pipeline's internal reconciliation ("financial foundation", "business pack", "This synthesis") and gives no credit judgement. A reader does not learn what liquidity TDG actually has or why the narrower measure matters.
   - Fix: Open with a one-sentence judgement on liquidity, for example cash after the October payout compared with the wider liquidity measure in the filing, and describe the definition difference in terms of the issuer rather than the modules.
5. **Medium · narrative** (New Reader, Auditor)
   - Where: line 136-143 Source column: "Financial foundation (CP-1)" on every row; rendered as "Financial foundation"
   - Problem: Every Source cell names an internal module rather than the 10-K and page. The column adds nothing, and the reader cannot trace a figure without going to another page.
   - Fix: Cite the filing and page in each Source cell (e.g. FY2024 10-K p.71), as the Calculations table above already does.
6. **Medium · narrative** (New Reader, Saboteur)
   - Where: line 140: "EBITDA As Defined / cash paid for interest, net"; line 141: "Unadjusted-denominator gross leverage | Approximately 6.57x | Not supplied: comparator not needed for definition sensitivity"
   - Problem: Three EBITDA labels appear (issuer-adjusted, EBITDA As Defined, issuer-reported) with no note on how they relate. "Unadjusted-denominator" is jargon. The FY2023 cell explains the gap in terms of the pipeline's needs rather than saying what is missing. A reader cannot tell that the 6.01x to 6.57x gap measures how much the add-backs flatter leverage.
   - Fix: Use one defined name for EBITDA, label the row in reader terms (e.g. "Gross leverage on reported EBITDA, before company add-backs"), and write "Not shown" for the missing comparator.
7. **Low · visual** (Auditor)
   - Where: shot CP-2_s-134.png, table row "Unadjusted-denominator gross leverage", stray "Basis" chip under the label (x≈310-420, y≈410-430 in displayed coordinates)
   - Problem: One row has a floating "Basis" link inside the Observation cell and the others do not. The table also left-aligns its numeric columns, which makes the two periods harder to compare.
   - Fix: Remove the per-cell Basis chip or apply it consistently, and right-align the figure columns.
8. **Low · visual** (New Reader)
   - Where: shot CP-2_s-134.png, every value cell ("Approximately 6.01x", "Approximately 5.87x" …)
   - Problem: "Approximately" is repeated in every ratio cell, which adds visual noise and pushes the number away from the start of the cell.
   - Fix: Show the ratios as 6.0x etc. and say once in the header or a note that they are rounded.

### T2.12 — Gaps ledger

Kind: prose/table · handoff lines 151-166 · verdict **BLOCK**

- Narrative: The ledger's content is substantive, but register codes, a `cp1a_refs` column, pipeline terms (handoff, consumer, typed projection, READY) and a closing paragraph that contradicts G2-03's Critical rating keep it from reading as a credit judgement for a committee reader. Not verified: what the empty row Basis popovers show when clicked, and whether the paragraph popover shows the '(CP-1A)' code.
- Visual: The section has no chart, map or timeline. The six-column table is legible and aligned, but the narrow Basis and Source columns wrap to as many as 18 lines, the two columns overlap in content, and the 'Basis' links are inconsistent (missing on G2-01, empty data on the other rows).

1. **High · narrative** (Saboteur, Auditor)
   - Where: L164 "No explicitly Critical gap or Critical disclosure-log item was identified as such in the supplied business handoff." vs L157 "G2-03 / Critical for contractual conclusions"
   - Problem: The closing paragraph says no Critical gap was identified, while the table directly above rates G2-03 as Critical. A committee member skimming the paragraph will conclude nothing critical is open, even though the gap blocks every covenant, guarantor and cash-access conclusion. The paragraph's subject is another module's register, and the reader cannot tell that from the page.
   - Fix: Open the section with a one-line judgement that names G2-03 as the one gap critical to contractual conclusions. Either drop the sentence about the upstream register or reword it so it cannot be read as the opposite.
2. **High · narrative** (Auditor, New reader)
   - Where: L153 header "Basis / cp1a_refs"; L156 "cp1a_refs: B3, B4, B5, B6; CP-1 G-DETAIL"; L158 "X4 ... CP-1 C09, C15, G-DETAIL"; L160 "CP-0 G-TIME; CP-1 E-DISTRIBUTION"
   - Problem: A field name (`cp1a_refs`) and internal register codes (B3, G5, X4, C09, G-DETAIL, G-LEGAL, G-MARKET, E-DISTRIBUTION) are shown on screen in every row. These are pipeline register codes, which the house standard bars, and a reader who has not seen the source documents cannot decode them.
   - Fix: Rename the column to 'Basis' and replace each code with the plain name of the evidence it points to, or move the codes into the Basis popover.
3. **High · narrative** (Auditor, New reader)
   - Where: L164 "...the non-READY signal carried in G2-01; the lack of a separate typed projection is not treated as missing readiness."; L155 "retain the consumer-specific restrictions"; L164 "supplied business handoff"
   - Problem: Pipeline vocabulary reaches the reader: handoff, consumer, typed projection, and the READY / non-READY status codes. The house standard names these terms as not reader language. The closing paragraph reads as a note about the pipeline's own process, not about TransDigm's credit.
   - Fix: Restate in credit terms, for example: 'Business evidence is usable with limits, so confidence is capped at Medium', with no status codes or pipeline terms.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Severity cells L155-L162: "Material", "Critical for contractual conclusions", "Material, bounded", "Nonblocking for retrospective synthesis", "Blocking only for market-relative-value decision", "Bounded"
   - Problem: The eight rows use six different severity labels with no stated scale, so the reader cannot rank the gaps. 'Bounded' and 'Nonblocking for retrospective synthesis' do not say how much the credit view is at risk.
   - Fix: Use one ordered severity scale (for example Critical / Material / Minor) and put the scope qualifier in the 'Why it matters' cell.
5. **Medium · narrative** (New reader, Auditor)
   - Where: L155 "cp1a_refs: Next module / CP-2 — Fundamental credit synthesis; CP-1 Definition and readiness register / Fundamental credit synthesis (CP-2)", rendered as "Next module / Fundamental credit — Fundamental credit synthesis; ... (Fundamental credit)"
   - Problem: G2-01's basis is a self-referential list of module sections. After the module codes are swapped for names it renders as a garbled 18-line cell that points back to this module three times. It gives the reader no evidence.
   - Fix: Cite the evidence behind the readiness judgement (what was missing upstream) in a short Basis entry, or leave the cell empty with the gap stated.
6. **Medium · visual** (New reader, Saboteur)
   - Where: Gaps ledger table, CP-2_s-151.png, region x 350-1440, y 260-1900 (crop tmp/CP-2-059-a.png)
   - Problem: The six-column table squeezes long text into narrow columns. The Basis and Source columns wrap to 10-18 lines per row (G2-01, G2-06) and largely repeat each other, which makes the ledger a tall wall of text. The 'Not supplied' status sits at the end of the 'Missing information' text instead of standing out.
   - Fix: Merge the Basis and Source columns into one short column, widen the 'Missing information' and 'Action' columns, and show 'Not supplied' as a chip or a separate status column.
7. **Medium · visual** (Auditor)
   - Where: Gaps ledger ID column: G2-01 has no 'Basis' link, while G2-02 to G2-08 each show a 'Basis' link (DOM: data-basis="[]" on rows 156-162)
   - Problem: The row Basis buttons are rendered with an empty basis list, so they appear to offer support but carry no data, and G2-01 has no button at all. The control is inconsistent and appears to be empty.
   - Fix: Show a row Basis control only when it has content, and make it consistent across all rows.
8. **Low · narrative** (Auditor)
   - Where: L151-L164: table first, then the L164 paragraph; no bottom-line sentence for the section
   - Problem: The section opens with the table and has no judgement first. The only prose comes after the table and is about the process, so the reader never learns which gaps actually move the credit view.
   - Fix: Add one opening sentence saying which gaps limit the conclusion (stress case, legal terms) and which do not.

### Sources

Kind: prose/table · handoff lines 4-15 · verdict **CONCERNS**

- Narrative: The Sources section shows pipeline vocabulary and internal identifiers to the reader (handoff, transport convention, cp1_facts/cp1a_rows projection) and names sources by file and pipeline names, not as a reader would cite them; the module codes themselves were correctly replaced with names.
- Visual: The table renders cleanly with no clipping, but a hash column of little reader value takes much of the width, one row carries an empty Basis chip, and the section sits mid-page before the remaining analysis.

1. **High · narrative** (Auditor, New reader)
   - Where: line 14: "All supplied handoffs are accepted under the transport convention; no additional receipt or snapshot is required. The context contains no typed cp1_facts, cp1a_rows or cp1a_signals projection, so the supplied Markdown labels and exact register references serve as the basis mapping."
   - Problem: This paragraph is shown to the reader as written and uses pipeline words and internal identifiers (handoff, transport convention, receipt, snapshot, cp1_facts, cp1a_rows, cp1a_signals, projection, basis mapping). That breaks the house rule on reader language, and a portfolio manager cannot interpret it.
   - Fix: Keep one plain sentence for the reader (conclusions rest on the FY2024 annual report as analysed in the Financial foundation and Business & governance modules; no external research) and drop the pipeline bookkeeping or keep it off screen.
2. **High · narrative** (Auditor, New reader)
   - Where: lines 10-12, Module / use column: "Source readiness; supplied accepted handoff", "Financial foundation; supplied accepted handoff", "Business & governance; supplied accepted handoff" (screenshot CP-2_s-4.png, Sources table)
   - Problem: The module codes have been replaced with names, but every row still shows "supplied accepted handoff", which is pipeline vocabulary. The column header "Exact source name or supplied handoff" repeats it.
   - Fix: Describe each row's use in reader terms (e.g. "Prior analysis: financial statements and ratios") and rename the header to "Source".
3. **Medium · narrative** (New reader)
   - Where: line 8: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" and line 9: "context"
   - Problem: The sources carry raw file and pipeline names (an EDGAR accession string with a .jsonl suffix, and a lowercase "context") instead of reader titles. A committee member cannot tell at a glance that the first row is the FY2024 Form 10-K, or what "context" refers to.
   - Fix: Name sources as a reader would cite them ("TransDigm Form 10-K, fiscal year ended 30 September 2024") and say plainly what "context" is, or remove it.
4. **Medium · visual** (Saboteur, Auditor)
   - Where: Sources table, row "context Basis" (screenshot CP-2_s-4.png, about y 330-380 at display scale; DOM button aria-label="Basis for row: context" data-basis="[]")
   - Problem: A Basis chip shows only on the "context" row, and it carries an empty basis (data-basis="[]"). So the reader gets a clickable affordance that points to nothing, on a row that is not issuer evidence. That is a fake value standing in for a real reference.
   - Fix: Add no Basis chip to a row that is itself a source (or to any row with an empty basis), and give the row a reader name instead of "context".
5. **Medium · visual** (New reader, Saboteur)
   - Where: Sources table, sha256 column: "d75c469fdb1966dd895c0f6faa6d5179b380d3ed95aa00aca99aa258059edab6" (line 8) and four similar hashes (screenshot CP-2_s-4.png, right third of the table)
   - Problem: 64-character hashes take about 40% of the table width but tell a credit reader nothing. They squeeze the useful Module / use column into narrow wrapped lines.
   - Fix: Drop the hashes from the reader view, or put them in a collapsed provenance detail, and give the width to the source description and filing date.
6. **Low · narrative** (Saboteur)
   - Where: line 14: "The underlying annual filing is listed for lineage, not as a claim of a fresh source read. Other inventoried issuer files supply no additional observation to this synthesis."
   - Problem: This is stated defensively, from the process's point of view. It does not tell the reader which filing period supports the view or what was left out, so it reads as a hedge rather than a scope statement.
   - Fix: State the scope in one line: which filing and period the view rests on, and that no other documents changed it.
7. **Low · visual** (Auditor)
   - Where: On-this-page rail and page order (screenshot CP-2_s-4.png): "Limitations, Maps, Request, Sources, Strengths and weaknesses, Map: credit-risk transmission, Key credit metrics..."
   - Problem: Sources and the raw Request sit in the middle of the module, so analysis (Strengths and weaknesses, the map, Key credit metrics) comes after the source list. That breaks reading order compared with sources placed last.
   - Fix: Render Sources (and the request text, if kept) after all analytical sections.

### Key findings

Kind: reader passage · handoff lines 25-34 · verdict **BLOCK**

- Narrative: The four bullets are judgement-first with bold leads and sit in the house order (bottom line, key findings, contrary evidence, limitations), but the key extraction finding leaves its distribution unsized and undated, uses internal 'business register' wording, and the maturity and resilience bullets carry vague caveats.
- Visual: There is no chart in this section; the bullet list is legible, but three of the four bullets lose their visible Basis link, the negative figure's minus sign sits outside its chip, and the page index repeats 'Key findings'.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 28: "The business register links USD 3,000 million of new secured financing and existing cash to the subsequent distribution."
   - Problem: The headline judgement ('shareholder extraction') rests on a distribution the bullet never sizes or dates. 'Subsequent' leaves the reader guessing whether it falls inside FY2024. 'The business register' is internal pipeline vocabulary. Without the payout amount and timing, a committee member cannot tell how much debt-funded extraction there was.
   - Fix: State the distribution's per-share and total amount, its declaration and payment dates against the 30 September 2024 balance date, and the debt that funded it. Drop 'business register'.
2. **High · visual** (Auditor)
   - Where: Key findings, bullets 1-3 (handoff lines 26-31, each with its own Basis line at 27, 29, 31); screenshot CP-2_key-findings.png, y 220-600 at 1200 px display. DOM: only the bullet at line 32 gets a button.basis-link
   - Problem: The handoff gives every bullet a Basis line, but the page shows a 'Basis' link only after bullet 4. The bases for bullets 1-3 exist only as data-basis attributes on the figure buttons, so a reader sees no source for the three bullets that carry all the numbers. That breaks the rule that every paragraph has its own Basis line.
   - Fix: Show a Basis link at the end of every bullet whose handoff paragraph has a Basis line, whether or not the bullet contains figures.
3. **Medium · narrative** (Saboteur)
   - Where: line 30: "shows USD 93 million in FY2025 and a much larger USD 6,637 million in FY2028 ... The schedule does not cover every obligation, so it cannot establish a complete maturity holiday."
   - Problem: The headline leads with 'modest' near-term principal, but the bullet skips FY2026-FY2027 and never says which obligations the schedule leaves out. The final caveat is too vague for the reader to size the gap, so the maturity profile reads as more comfortable than the evidence shows.
   - Fix: Give each fiscal year through the large FY2028 maturity, and name the obligations the schedule excludes (for example leases or the revolver), each with an amount or marked as not available.
4. **Medium · narrative** (New reader)
   - Where: line 32: "aerospace customers share utilization, production and procurement risks. Delayed shipments and working-capital absorption can weaken conversion before the installed-base franchise itself deteriorates"
   - Problem: This key finding has no figure, period or example: no aftermarket share, no conversion rate, no working-capital movement. 'Share ... risks' and 'working-capital absorption' are abstract. The reader cannot judge how conditional the 'leverage tolerance' is.
   - Fix: Anchor the condition with one or two dated measures from the financial foundation (for example the FY2024 cash conversion or working-capital change), or say that none was available.
5. **Medium · visual** (Auditor, Saboteur)
   - Where: line 28: "was USD -2,505 million"; DOM renders 'USD -' as plain text and '2,505 million' inside the button.figure chip
   - Problem: The minus sign sits outside the figure chip, so the highlighted and clickable value, and its accessible name, read as a positive 2,505 million. The sign of the only negative figure in the section is cut off from the figure it belongs to.
   - Fix: Put the sign inside the figure token (for example 'USD -2,505 million' or '(USD 2,505 million)'), with the sign and the currency in the chip.
6. **Medium · visual** (New reader)
   - Where: Left rail 'On this page', screenshot CP-2_key-findings.png x 95-260, y 545-790: 'Key findings' appears twice, and 'Maps' appears next to 'Map: credit-risk transmission'
   - Problem: The page index lists two 'Key findings' entries (the reader passage and a later structured block) plus overlapping Map entries. A reader cannot tell which is the judgement and which is supporting detail.
   - Fix: Give each anchor a unique, reader-meaningful label (for example rename or nest the later structured block), and list each map once.
7. **Low · narrative** (New reader)
   - Where: line 26: "issuer-adjusted EBITDA coverage of net cash interest improved to approximately 3.60x ... they do not reserve cash for creditors or establish forward gross-interest coverage."
   - Problem: The metric is built on the most favourable bases (adjusted EBITDA, net cash interest) and the bullet does not say so. 'Forward gross-interest coverage' is analyst shorthand left undefined.
   - Fix: Name the basis in plain words (EBITDA As Defined over interest paid net of interest received) and either give the gross-interest figure or say it was not computed.
8. **Low · visual** (Auditor)
   - Where: Key findings block, screenshot CP-2_key-findings.png, x 295-845 vs 845-1160, y 190-720
   - Problem: Every figure is set in an underlined monospace chip inside proportional prose, which breaks the reading rhythm of dense bullets. The text column takes under half the 1440 px page, leaving a wide empty band on the right while each bullet runs to five or six lines.
   - Fix: Show figures in the body font with a subtle affordance, and widen the prose measure or use the right-hand space so bullets break into shorter lines.

### Key credit metrics

Kind: prose/table · handoff lines 65-79 · verdict **BLOCK**

- Narrative: The lead sentence puts the judgement first. However, the table's two-period headers mislabel the last two rows (reported FY2024 figures appear under FY2023), and pipeline wording ("calculated in this handoff") plus internal codes are shown to the reader.
- Visual: This section is a single six-column table with no chart. It renders cleanly with no clipping, but left-aligned numbers with prefixes and multi-line Change and Source cells make the seven metrics hard to compare at a glance.

1. **High · narrative** (Saboteur, New reader)
   - Where: L70 header "FY2024 / illustrative case | FY2023 / reported case"; L77 "Illustrative USD 1,913 million | Reported USD 6,261 million"; L78 "Illustrative approximately 5.55x | Reported approximately 4.51x"
   - Problem: The column headers mix two comparisons. In the last two rows, the 30 September 2024 reported cash (USD 6,261 million) and net leverage (4.51x) sit under a header that says FY2023, and post-payment pro-forma figures sit under one that says FY2024. A reader scanning by column will take 4.51x as last year's net leverage and 5.55x as this year's actual figure.
   - Fix: Put the post-distribution illustration in its own small table, or give it its own clearly headed columns (reported 30 Sep 2024 vs illustrative after the October payment), so that every column has a single period and basis.
2. **High · narrative** (Auditor)
   - Where: L67 "Changes below are either carried from accepted upstream calculations or calculated in this handoff."
   - Problem: This sentence is shown to the reader and uses pipeline vocabulary ("handoff", "accepted upstream calculations") that the house standard bans. It also tells the reader nothing about credit.
   - Fix: Delete the sentence, or replace it with a reader-facing note such as "Changes are FY2024 minus FY2023 unless marked illustrative."
3. **Medium · narrative** (New reader, Auditor)
   - Where: L74 "Increased; no new rounded-ratio delta calculated"; L76 "Improved; no gross-interest inference"; L78 "Higher after specified cash use; debt unchanged"
   - Problem: In the Change column, the two ratio rows carry internal method caveats where a number should be. The reader has to work out the +0.14x and +0.67x moves alone, and the column is inconsistent: USD rows show figures, ratio rows show prose.
   - Fix: Show the ratio change as a number (e.g. +0.14x, +0.67x, +1.04x illustrative) and put any rounding caveat in a table note.
4. **Medium · narrative** (New reader)
   - Where: L77 "Cash after specified distribution settlement only" / "Specified payments USD 4,348 million"
   - Problem: The section never says what the "specified distribution" is, that the dividend was paid after the 30 September balance-sheet date, or how it was funded. Without reading Bottom line or another module, a reader cannot tell whether the USD 4,348 million is a real outflow or a hypothetical one.
   - Fix: Name the item in the row label, e.g. "Cash after the special dividend and equivalents declared and paid in October 2024 (illustrative)".
5. **Medium · narrative** (Saboteur)
   - Where: L74 "Gross debt / issuer-adjusted EBITDA | Approximately 6.01x" (the metrics table only; 6.57x unadjusted appears at L47)
   - Problem: The headline metrics table shows leverage only on the issuer's adjusted EBITDA. The module itself calls denominator sensitivity a principal weakness (6.57x on unadjusted EBITDA), but a reader who looks only at this table sees the more flattering figure.
   - Fix: Add a row for gross debt / reported unadjusted EBITDA (approximately 6.57x), with its FY2023 comparative if one is available, so both earnings bases sit side by side.
6. **Medium · narrative** (New reader, Auditor)
   - Where: L68 "Basis: Financial foundation (CP-1); calculation C2-01; calculation C2-03; calculation C2-04; calculation C2-05; calculation C2-07"; Source column e.g. L72 "Financial foundation (CP-1), C09; calculation C2-05"
   - Problem: The reader is pointed to internal register and calculation codes (C09, C2-05) that this page never defines. These are the kind of register codes the standard counts as pipeline vocabulary, so the Source column cannot be followed without opening another page.
   - Fix: In the Source column, name the source in reader terms (e.g. "FY2024 10-K cash-flow statement; analyst calculation") and keep the codes only in a link or tooltip.
7. **Medium · visual** (Auditor, New reader)
   - Where: Key credit metrics table, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2-055-a.png (crop 340,220-1400,920 of CP-2_s-65.png)
   - Problem: Numeric columns are left-aligned and carry prefixes ("USD", "Approximately", "Illustrative", "Reported"), so the figures do not line up and cannot be compared down a column. Text in the Change and Source columns wraps to three lines, which makes every row tall and the seven metrics slow to scan.
   - Fix: Right-align the numbers, put units and the approximate/illustrative marker in the header or a footnote, and narrow the Source column so that each metric fits on one or two lines.
8. **Low · visual** (Saboteur)
   - Where: Key credit metrics table, Change column, screenshot CP-2_s-65.png rows 1-2 ("USD 778 million", "USD 5,155 million")
   - Problem: The change figures have no sign or percentage. An increase in debt and an increase in EBITDA look the same, and there is no colour or arrow for direction.
   - Fix: Add an explicit sign and percentage (e.g. +USD 5,155 million, +26%) so the direction and scale of each move are visible.

### Analytical appendix — complete canonical registers

Kind: register appendix · handoff lines 80-119 · verdict **BLOCK**

- Narrative: The registers state clear judgements (the Credit assessment cell is judgement-first). However, they leak internal field names, register codes and pipeline status wording into reader cells, repeat the prose Key findings, and use severity and category columns that never vary.
- Visual: There is no chart, map or timeline in this section; it is four dense six-column tables. The unit screenshot (shots/CP-2_s-80.png) shows the top of the page because the appendix heading and anchor are not rendered, so I judged the layout from full-resolution crops of render/CP-2.png (y 6950-8750), saved as tmp/CP-2-056-a.png and tmp/CP-2-056-b.png. All 18 Basis buttons in those tables are empty.

1. **High · narrative** (Auditor; New reader)
   - Where: Column header "Basis / cp1a_refs" (lines 84, 90, 103, 112) and cells such as "cp1a_refs: B1, B2, B7, T5, T6, T7, F1, X1, X2, X3; CP-1 C01, C03, C04, C05, C06, C15" (line 86); "CP-1 E-DISTRIBUTION, C06" (line 96); "C18 and G-DEBT" (line 107)
   - Problem: All four tables print the internal field name "cp1a_refs" and long strings of register codes (B7, T6, X3, G-DEBT, E-DISTRIBUTION) on screen. The DOM confirms they are rendered as written. These are pipeline identifiers, and a credit committee reader cannot resolve them without opening other modules, which breaks the house rule against pipeline vocabulary.
   - Fix: Name the column "Basis" and replace the register codes with reader-facing evidence names, or move them into the Basis popover so they never show as cell text.
2. **High · visual** (Auditor; Saboteur)
   - Where: Every "Basis" button in the four appendix tables, CP-2.dom.html ids s-82, s-88, s-101, s-110 (18 of 18 carry data-basis="[]"); visible next to each row ID in tmp/CP-2-056-a.png and tmp/CP-2-056-b.png
   - Problem: Every row shows a Basis link, but all 18 links in this section carry empty basis data, so the reader who clicks one gets nothing. The page offers source traceability that it does not deliver, on exactly the rows that hold the committee-facing thesis and risks.
   - Fix: Fill each row's Basis with the sources already in its Source and Basis cells, or remove the button where there is nothing to show.
3. **Medium · narrative** (Saboteur; New reader)
   - Where: "R1 / Material" … "R5 / Material" (lines 114-118); Category column "Analyst Interpretation" on every row of lines 86-118
   - Problem: All five risks carry the same severity, and every row in all four tables has the same Category. The severity column therefore cannot rank the risks, and the reader cannot tell which risk drives the view: Further extraction and Later refinancing concentration look equally weighted. Two columns of every table carry no information.
   - Fix: Rank or differentiate the risks by severity, and drop or collapse any column whose value is the same on every row.
4. **Medium · narrative** (Auditor)
   - Where: "Medium; upstream readiness is Ready with limitations and no combined downturn/post-allocation servicing case is supplied" (line 86, Confidence cell)
   - Problem: The confidence justification uses pipeline status language ("upstream readiness is Ready with limitations", "supplied"), so the reason for Medium confidence is stated in workflow terms rather than credit terms.
   - Fix: State the reason in credit terms, e.g. that no combined downturn and post-payout servicing case has been tested.
5. **Medium · narrative** (Saboteur; New reader)
   - Where: "#### T2.10 — Key findings" (line 101) restating the earlier Key findings bullets, e.g. KF1 "Operating cash generation supports current servicing, but cash allocation determines retained protection" (line 105)
   - Problem: This register repeats the module's prose Key findings and Thesis in different wording. The left navigation therefore lists "Key findings" twice, and the reader meets two non-identical versions of the same conclusions, which invites a check for which one governs.
   - Fix: Keep a single authoritative statement of the findings and either drop the register copy or label it clearly as the supporting table for the prose findings.
6. **Medium · visual** (New reader; Auditor)
   - Where: Handoff heading "### Analytical appendix — complete canonical registers" (line 80); the DOM has no s-80 anchor and no such heading; the unit screenshot shots/CP-2_s-80.png lands at the top of the page
   - Problem: The appendix heading is dropped on render, so the four register tables follow Key credit metrics with no divider, and the reader cannot tell that the main argument has ended and supporting registers have begun. The handoff heading itself uses the pipeline word "canonical registers".
   - Fix: Render a reader-language appendix heading (e.g. "Supporting tables") with an anchor, so the section is visibly separated from the body and can be reached from the navigation.
7. **Low · narrative** (Saboteur)
   - Where: "USD 3,000 million secured financing supported a distribution and equivalents of approximately USD 4,348 million subsequently paid" (line 96); "USD -2,505 million" (line 106)
   - Problem: An exact computed sum (4,216 + 132 = 4,348, per C2-01) is hedged as "approximately", which blurs exact and estimated figures. The negative amount is printed as "USD -2,505 million" rather than as an explicit shortfall.
   - Fix: Present the 4,348 as exact, and write the negative value as a shortfall, e.g. "a USD 2,505 million shortfall".
8. **Low · visual** (New reader)
   - Where: Source column in the Thesis/Key findings/Key credit risks tables, tmp/CP-2-056-a.png and tmp/CP-2-056-b.png right-hand column: "Business and transaction context (Business & governance); Financial foundation"
   - Problem: The six-column tables squeeze the Source and Basis cells into narrow columns of 5-6 wrapped lines. The Source label doubles the module name ("Business and transaction context (Business & governance)") on nearly every row, so row heights are driven by references rather than by the analysis.
   - Fix: Use one short source name per module, and give the statement column the width while the reference columns stay compact.

### Manual checks and unavailable machinery

Kind: prose/table · handoff lines 167-179 · verdict **BLOCK**

- Narrative: The whole section is a pipeline self-audit (script names, the words "handoff" and "producer", and "Not run: unavailable") with no credit content, so it breaks the house rule against pipeline vocabulary on screen; the one useful item, why confidence is Medium, is buried here instead of under Limitations.
- Visual: The table itself renders cleanly with no clipping, overlap or contrast problem, but it gives eight rows of internal machinery full visual weight in the analysis flow and in the "On this page" navigation, and the "not run" status rows look the same as the "performed manually" rows.

1. **High · narrative** (Auditor, New reader)
   - Where: Whole section, lines 167-178, e.g. line 171 "prepare_invocation.py | Not run: unavailable | Matched issuer, date, pathway and source/handoff pins; accepted every supplied upstream handoff"
   - Problem: The entire section is a pipeline self-audit: script filenames, "handoff", "pins", "receipt requirement" and "transport submission" are shown to a credit committee reader. The house rule says pipeline vocabulary is not reader language, and this section contains no credit content at all.
   - Fix: Remove this section from the reader-facing Modules page (keep it in the run record or an internal audit view) and drop its entry from the "On this page" list.
2. **High · narrative** (Auditor, Saboteur)
   - Where: line 178: "Neither producer is blocked; business readiness is restricted and confidence is below High; inherited restrictions are recorded in the gaps ledger rather than recast as new negative findings"
   - Problem: "producer" is a banned pipeline term. The confidence call (Medium, below High) is buried in an internal-checks table rather than stated as judgement in the bottom line or limitations, so a reader skimming the module could miss why confidence is capped.
   - Fix: State the Medium-confidence judgement and its two drivers in reader language under Limitations, and keep pipeline status wording off the page.
3. **Medium · narrative** (New reader)
   - Where: line 176: "r14 SKILL.md, coverage companion and typed composition contracts | Unavailable outside supplied method | No unsupplied columns, schema certification or typed identifier projection claimed"
   - Problem: "r14 SKILL.md", "typed composition contracts", "schema certification" and "typed identifier projection" mean nothing to a portfolio manager and cannot be understood without knowing how the pipeline is built.
   - Fix: If any of this matters to the reader, say it as a plain limitation on the analysis (for example "confidence is a qualitative judgement; no scoring model was applied"); otherwise leave it off the page.
4. **Medium · narrative** (Saboteur)
   - Where: line 173: "confidence_score.py | Not run: unavailable | No scoring formula supplied. Medium is a qualitative judgment"; line 175: "all new arithmetic executed with calculate"
   - Problem: "Not run: unavailable" repeated five times reads like failed validation and may make a committee doubt the figures, while "executed with calculate" names an internal tool and never says which figures it covered. The reader cannot tell whether the numbers were checked.
   - Fix: Replace these rows with one plain sentence on how figures were verified (for example "all derived ratios recomputed from reported amounts") and point to the Calculations table.
5. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-2_s-167.png, table under "Manual checks and unavailable machinery" (about y 1380-1810 in the display, i.e. 1656-2172 in the original)
   - Problem: Eight full-width rows of internal script names sit in the main reading flow between the Gaps ledger and Next module, and the section is also listed in the left "On this page" navigation. This gives internal plumbing the same visual weight as credit analysis.
   - Fix: Remove the block and its navigation entry from the Modules page, or collapse it into a visually de-emphasised run-diagnostics area outside the analysis.
6. **Low · narrative** (Auditor)
   - Where: lines 169-178 table header "Mechanism / check | Status | Manual equivalent / result"
   - Problem: The table has no Source column and the section has no Basis line, so even judged as content it breaks the house rule that every table carries its sources.
   - Fix: If any part is kept for readers, add a Source column or a Basis line, like the neighbouring sections have.
7. **Low · visual** (Saboteur)
   - Where: Screenshot CP-2_s-167.png, Status column (x about 530-640 in the display) of the same table
   - Problem: The Status column shows the same plain-grey "Not run: unavailable" five times with no chip or visual difference from "Performed manually", so the one useful distinction in the table is hard to see. File names are set in body text rather than code style.
   - Fix: If the block is kept anywhere, show status as a chip or with consistent styling and set identifiers in monospace, or reduce it to a one-line summary.

### Request + Next module

Kind: run plumbing · handoff lines 1-3, 180-187 · verdict **BLOCK**

- Narrative: Both passages are run plumbing: the model's request (with the raw pathway code) and routing to the next stages. They do not serve the reader and break the no-pipeline-vocabulary rule, and their only credit point is already stated in Limitations and the gaps ledger.
- Visual: There is no chart, map or timeline in this section. Both parts render as ordinary analysis sections with the same typography, so nothing marks them as metadata, and Request interrupts the page flow between Maps and Sources.

1. **High · narrative** (Auditor, New reader)
   - Where: Request, line 2: "TransDigm Group Incorporated, as of 2024-09-30; pathway: credit_snapshot. Synthesise the fundamental creditor view from the supplied financial foundation and business and transaction registers..."
   - Problem: The reader is shown the instruction the model was given, including the raw pathway code `credit_snapshot`, an imperative to the model ("Synthesise...") and internal terms ("supplied ... registers"). This is pipeline plumbing on a reader page and breaks the house rule against pipeline vocabulary. A portfolio manager gets nothing from it.
   - Fix: Remove the Request section from the reader view, or replace it with a one-line scope statement in reader language (issuer, as-of date, retrospective FY2024 credit snapshot).
2. **High · narrative** (Auditor, New reader)
   - Where: Next module, line 180-182: "## Next module ... Pass the allocation-constrained thesis, static payout-adjusted leverage illustration, earnings-definition sensitivity and bounded maturity interpretation to the legal, relative-value, evidence-validation and committee workflows."
   - Problem: Both the heading "Next module" and the body are about routing between pipeline stages ("Pass ... to the ... workflows"). That is module-to-module communication shown to the reader, which the house standard bans. The reader also has no way to know what "workflows" means here.
   - Fix: Hide the Next module section from the reader page, or retitle it as "Open questions / next analysis" and keep only the reader-relevant follow-up in plain credit language.
3. **Medium · narrative** (Saboteur)
   - Where: Next module, line 182: "Status: Complete with limitations; restricted to historical fundamental synthesis."
   - Problem: The paragraph opens with a run-status label, not a credit judgement. The one point that matters to a committee (historical servicing strength does not size the distance to a funding shortfall) comes last, under a plumbing heading at the bottom of a long page. A skimming reader can take "Complete" as an all-clear.
   - Fix: Drop the status label. The funding-shortfall point already sits in Limitations (line 40) and the gaps ledger (G2-02), so leave it there and do not repeat it here as a routing note.
4. **Medium · narrative** (New reader)
   - Where: Next module, line 185: "Keep contractual permission and market pricing with their owning decisions and unresolved evidence requests. ... it does not turn an observed payout into assumed future legal capacity or missing support evidence into adverse willingness."
   - Problem: This is method self-description: an imperative to other stages ("Keep ... with their owning decisions") followed by stacked negations. A reader cannot tell what it means for the credit view, and "adverse willingness" is undefined jargon.
   - Fix: Either remove it, or state the scope limit plainly in Limitations, e.g. that this section gives no instrument recommendation, recovery view or covenant-capacity conclusion.
5. **Medium · visual** (Auditor)
   - Where: CP-2_s-1.png, top region (y 180-250 displayed) and On this page nav (Maps > Request > Sources); CP-2_s-180.png, bottom region (y 1830-1945 displayed)
   - Problem: Request and Next module use the same h3 and passage styling as the analysis (DOM: class "analysis-section" / "passage-text"). So nothing visually marks them as run metadata. Request also sits mid-page, between the Maps section and Sources, where it breaks the reading flow from the summary into the detail.
   - Fix: If these sections are kept at all, render them as visually subdued run metadata (smaller, muted, or in a footer/details strip) and outside the analytical reading order.
6. **Low · narrative** (Saboteur)
   - Where: Request, line 2: "as of 2024-09-30" versus page header "As of 30 September 2024" (CP-2_s-1.png top right)
   - Problem: The same date is written in two formats on one screen: the raw ISO form in the body and the long form in the header. It is a small inconsistency that flags the body text as machine output.
   - Fix: Use the header's date format throughout the reader-facing text.
7. **Low · visual** (New reader)
   - Where: CP-2_s-180.png, Next module paragraphs (y 1860-1945 displayed)
   - Problem: Two dense paragraphs of roughly 60-70 words each run the full ~860 px content width at small body size. Lines run to about 170 characters, which is hard to scan.
   - Fix: Cap the measure of prose passages at about 75-90 characters or break the passage into short items.

### Bottom line

Kind: reader passage · handoff lines 18-24 · verdict **BLOCK**

- Narrative: The bottom line opens with a judgement and keeps the numbers exact, but it does not name or size the special dividend that drives its key point, does not give the EBITDA basis or period for the leverage figures, and puts its actual credit call fourth, as a coined label.
- Visual: There is no chart in this section. Its layout sets both paragraphs (about 170 words) in large bold display type with no visible section heading, no Basis chip and monospace figure links mixed into the display face. Not verified: whether the figure-button tooltips show the CP-1 code text on screen; only the DOM attributes were checked.

1. **High · narrative** (Saboteur, New reader)
   - Where: Line 22: "Reported net leverage of approximately 4.51x overstates retained balance-sheet protection if read without the declared shareholder use ... settlement of the specified accrued dividend and equivalents reduces cash from USD 6,261 million to USD 1,913 million"
   - Problem: The paragraph never says what the payout is: no amount (the implied USD 4,348 million is left for the reader to work out), no per-share figure, no payment date and no statement that it was paid after the 30 September measurement date. "Declared shareholder use", "specified accrued dividend" and "October balance sheet" assume the reader already knows about the special dividend. A committee member who has not read the 10-K cannot size the event that drives the illustrative 5.55x.
   - Fix: In the paragraph's first sentence, name the special dividend: its amount in USD million, its declaration and payment dates relative to 30 September 2024, and how it was funded.
2. **Medium · narrative** (Saboteur)
   - Where: Line 19: "However, FY2024 gross leverage increased to approximately 6.01x from approximately 5.87x even as issuer-adjusted EBITDA increased."
   - Problem: The bottom line does not say which EBITDA the multiples use. Lines 47 show that 6.01x is on EBITDA As Defined and that unadjusted gross leverage is 6.57x, so the headline uses the more flattering definition without saying so. The comparison period behind 5.87x (FY2023) is implied, not stated. A reader can carry 6.01x into committee as unqualified leverage.
   - Fix: Write the basis and periods in the sentence (gross debt / EBITDA As Defined, FY2024 vs FY2023), and say the unadjusted equivalent is about 6.57x.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 19: "The fundamental view is therefore cash-generative but allocation-constrained, with Medium confidence"
   - Problem: The judgement comes fourth, after three descriptive sentences, and is a coined label rather than a credit call: it gives no direction, no view on whether about 6x leverage is tolerable, and no stance a committee can act on. The paragraph also does not say what "Medium confidence" rests on; the reason only appears in Limitations (line 40).
   - Fix: Open with the stance itself (for example, whether the credit can carry current leverage and in which direction it is moving) and give the confidence reason in a short clause.
4. **Medium · narrative** (Auditor)
   - Where: Lines 20 and 23: "Basis: Financial foundation (CP-1); Business and transaction context (CP-1A)" / "Basis: Financial foundation (CP-1); calculation C2-01; calculation C2-02; calculation C2-03"
   - Problem: The page shows no Basis line for either bottom-line paragraph, although Key findings and Limitations show a "Basis" chip. The handoff's Basis text carries module codes (CP-1, CP-1A) and internal calculation IDs (C2-01 to C2-03), which the house standard bars from the reader's screen. The DOM data-basis attributes on the figure buttons carry "Financial foundation (CP-1)" verbatim.
   - Fix: Show a Basis chip on each bottom-line paragraph, using reader names for the sources and calculations and no CP or C2 codes.
5. **Medium · visual** (New reader)
   - Where: Bottom line block, shots/CP-2_bottom-line.png, about y 230-950 (original pixels)
   - Problem: Both bottom-line paragraphs, about 170 words and 23 lines, are set in large bold display type. The headline judgement and the illustrative pro-forma calculation get the same heavy weight, so nothing stands out and the block reads as a wall of bold.
   - Fix: Keep the display weight for the one-sentence judgement and set the supporting paragraph, including the pro-forma leverage illustration, in body type.
6. **Low · narrative** (New reader)
   - Where: Line 19: "TransDigm combines resilient operating economics with an equity-directed capital structure"
   - Problem: "Equity-directed capital structure" and "allocation-constrained" are coined analyst shorthand that the reader has to decode. Plain words would be quicker: the issuer borrows to fund shareholder payouts and acquisitions.
   - Fix: Replace the coined phrases with a plain statement of the behaviour, such as debt-funded shareholder payouts and acquisitions.
7. **Low · visual** (Auditor)
   - Where: shots/CP-2_bottom-line.png, top of content column (about y 220); DOM <h4 class="sr-only">Bottom line</h4>
   - Problem: The section has no visible heading because "Bottom line" is screen-reader only. Every following section is labelled (Key findings, Contrary evidence, Limitations), so a reader who scrolls or jumps from the On-this-page link lands on unlabelled bold text.
   - Fix: Show a small visible "Bottom line" label, matching the other section headings.
8. **Low · visual** (Auditor)
   - Where: shots/CP-2_bottom-line.png, about y 600-900: monospace dotted-underline figures "USD 6,261 million", "USD 1,913 million", "5.55x" inside bold display text
   - Problem: The interactive figures switch to a wide monospace face inside the large bold sans paragraph. Mixing two faces at display size breaks the reading rhythm and pushes "USD 1,913 million" onto its own line start.
   - Fix: Render figure links in the paragraph's own typeface with a light underline cue, keeping monospace for tables.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 35-38 · verdict **BLOCK**

- Narrative: The passage leads with its judgement and names real counter-evidence, but its triggers for changing the view have no thresholds, and it states two supporting facts without the exact figures the module already holds.
- Visual: This is a prose-only section with no chart. It is readable at a sensible line length, but on screen it lacks the Basis button its siblings carry, and its single figure is set in a jarring monospace style.

1. **High · visual** (Auditor, Saboteur)
   - Where: Line 37 'Basis: Financial foundation (CP-1); Business and transaction context (CP-1A)'; screenshot CP-2_contrary-evidence.png, crop CP-2-051-a.png (x330-1100, y210-600); render/CP-2.dom.html section#contrary-evidence
   - Problem: The paragraph has no visible Basis link on screen. Every neighbouring paragraph (Key findings bullets, Limitations) ends in a 'Basis' button, but section#contrary-evidence contains only a p.passage-text. Its basis exists only as data-basis on the USD 2,045 million figure button, so a reader can reach it only by clicking that number. This breaks the rule that each paragraph carries a Basis line. A future version of this passage with no figure would lose its sources entirely.
   - Fix: Render the paragraph's Basis line as a trailing 'Basis' button, the same way the Key findings and Limitations paragraphs do.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 36: 'The positive case would strengthen with sustained debt repayment and retained cash after acquisitions and distributions... The view would weaken with another debt-funded payout, slower collections or inventory absorption, or an earnings decline'
   - Problem: The triggers that would change the view have no threshold, size or timeframe. They give no leverage level, no coverage floor and no size of payout. Nor does the passage say what the view would move to (for example confidence, outlook or leverage tolerance). A committee cannot tell when the view has actually changed.
   - Fix: Tie each trigger to a measurable marker, such as a gross leverage level, an EBITDA-to-net-cash-interest floor or a payout size, and state which way the view would move.
3. **Medium · narrative** (Saboteur)
   - Where: Line 36: 'coverage of net cash interest improved while the long-term principal schedule remained light near term'
   - Problem: The two other supports for the counterweight are given without figures, although the same module states them exactly: about 3.60x from about 2.93x, and USD 93 million due in FY2025. 'Light near term' is vague and hides the USD 6,637 million FY2028 wall noted two sections earlier. That makes the counter-case look stronger than the numbers show.
   - Fix: Give the coverage ratio and its basis (issuer-adjusted EBITDA over net cash interest, FY2024 versus FY2023) and the FY2025 principal amount, with the FY2028 concentration as the qualifier.
4. **Low · narrative** (New reader)
   - Where: Line 36: 'The strongest counterweight to the allocation concern... against treating the payout as evidence of immediate funding failure'
   - Problem: 'The allocation concern' and 'the payout' rely on the reader having just read the Bottom line. The passage never names the payout (the accrued dividend paid after year-end, funded with USD 3,000 million of new secured debt). A reader who jumps here from the page outline gets no anchor.
   - Fix: Name the payout once in a short clause, such as 'the post-year-end special dividend funded partly by new secured debt'.
5. **Low · narrative** (New reader)
   - Where: Line 36: the single seven-sentence paragraph from 'The strongest counterweight' to 'less dependable.'
   - Problem: Contrary evidence and what would change the view (strengthen and weaken triggers) are packed into one dense block. A reader scanning for the triggers has to parse the whole paragraph.
   - Fix: Split it into a contrary-evidence paragraph and a short 'would strengthen / would weaken' pair.
6. **Low · visual** (Auditor, New reader)
   - Where: Screenshot crop CP-2-051-a.png: figure 'USD 2,045 million' in line 2 of the paragraph
   - Problem: The only figure renders in bold monospace with a dotted underline inside proportional body text. The jump in typeface draws the eye to the number and reads like code rather than an interactive figure. The Limitations block just below uses smaller grey text, which gives the two adjacent reader sections an uneven hierarchy.
   - Fix: Show figures in the body typeface with a subtle underline or tint, and give Limitations the same text size and contrast as the other passages.

### Limitations

Kind: reader passage · handoff lines 39-42 · verdict **CONCERNS**

- Narrative: The section comes in the required order after Contrary evidence and states its judgement on confidence clearly. But it is one jargon-heavy bullet that leaves out several limitations the module itself states, so the reader gets an understated picture of the gaps.
- Visual: The section has no chart. It is a single-bullet list with comfortable line length and spacing. The only visual weakness is the faint inline "Basis" control, and the Maps panel below belongs to the next section.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Line 40: "The supplied evidence has not been combined into an earnings-downturn case with post-allocation cash requirements." (the only bullet, lines 39-41)
   - Problem: The Limitations section has one bullet. Material limits stated elsewhere in the same module are missing from it: the debt schedule "does not cover every obligation" (l.30), the 5.55x figure is "not an actual October balance sheet" (l.22), there is no "forward gross-interest coverage" (l.26), and there was no direct issuer-text read (l.8, l.14). A committee member who reads only this section will think the downturn case is the only gap.
   - Fix: List every limitation that bounds the conclusions here, one short bullet each: the incomplete obligation schedule, the illustrative pro-forma leverage, no forward gross-interest coverage, and evidence taken only from earlier modules.
2. **Medium · narrative** (New reader, Auditor)
   - Where: Line 40: "The supplied evidence has not been combined ... This synthesis can identify the channels ... rather than turning historical coverage into a stress-capacity conclusion."
   - Problem: "Supplied evidence" and "this synthesis" describe the pipeline rather than the issuer. "Post-allocation cash requirements" and "stress-capacity conclusion" are undefined jargon, so the reader cannot tell what is actually missing (a downside EBITDA and cash-flow case after the dividend and acquisitions).
   - Fix: Name the missing analysis in plain credit terms (for example, no downside case testing debt service after the dividend and acquisitions) and drop the self-references to the synthesis.
3. **Medium · narrative** (Saboteur)
   - Where: Line 40: "cannot quantify the distance to a debt-service shortfall; that keeps the overall confidence at Medium"
   - Problem: The limitation does not quantify its effect, and gives no headroom figure from what is available, such as the FY2024 3.60x net cash interest coverage or the cash left after the dividend (USD 1,913 million). The reader cannot judge how far the missing stress case could move the Medium view.
   - Fix: Say how much the missing case matters by anchoring it to the coverage and post-dividend cash figures already stated, with units and period.
4. **Medium · narrative** (Auditor)
   - Where: Line 41: "Basis: Financial foundation (CP-1); Business and transaction context (CP-1A)"; rendered DOM render/CP-2.dom.html button.basis-link data-basis=["Financial foundation (CP-1)","Business and transaction context (CP-1A)"]
   - Problem: The Basis payload carries the module codes CP-1 and CP-1A. Codes are banned on screen, and they will show if the Basis control displays the data-basis strings verbatim. The visible paragraph text is clean.
   - Fix: Remove the module codes from the Basis labels before rendering, keeping only the reader names.
5. **Low · visual** (New reader)
   - Where: shots/CP-2_limitations.png, Limitations block, about x 300-830, y 190-285 (display coords); crop tmp/CP-2-052-a.png
   - Problem: A list with a single bullet holds a four-line sentence. "Basis" is a small grey inline word at the end of the text that reads as faint text rather than a control, so the reader may not see that it opens the sources.
   - Fix: Render a single limitation as a paragraph, or add the missing bullets, and give the Basis control a visible link or chip style.

### Strengths and weaknesses

Kind: prose/table · handoff lines 43-49 · verdict **BLOCK**

- Narrative: The section reads clearly but is out of house order (after Limitations and Sources), duplicates a later table, gives no net verdict, and its leverage terms disagree with the metrics table on the same page.
- Visual: The section is two prose paragraphs with no chart. Layout and spacing are clean, but the second paragraph has lost its Basis link and its two figure chips are styled inconsistently.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 43 "### Strengths and weaknesses" follows "### Limitations" (line 39); screenshot CP-2_s-43.png left 'On this page' list: Limitations, Maps, Request, Sources, then Strengths and weaknesses ... Thesis, strengths and weaknesses
   - Problem: The section sits after Limitations and after the Request and Sources entries, which breaks the required order (bottom line, key findings, contrary evidence, limitations), and Sources is no longer last. A second 'Thesis, strengths and weaknesses' table further down repeats the topic, so the reader meets strengths and weaknesses twice with no explanation of how the two differ.
   - Fix: Fold strengths and weaknesses into Key findings, or place them before Contrary evidence, and keep one strengths/weaknesses treatment above Limitations, with Sources last.
2. **Medium · narrative** (Saboteur)
   - Where: Line 47 "FY2024 gross leverage is approximately 6.57x using issuer-reported unadjusted EBITDA rather than approximately 6.01x using EBITDA As Defined."
   - Problem: The page uses three names for the same earnings measure: 'EBITDA As Defined' here, and 'issuer-adjusted EBITDA' in the Key credit metrics table directly below. The 6.57x unadjusted figure does not appear in that table, and neither ratio gives its numerator (gross debt USD 25,068 million), so the reader cannot check the 0.56x gap.
   - Fix: Use one name for the adjusted earnings measure across the page, and state the debt and the two EBITDA amounts behind both ratios, or add 6.57x to the metrics table.
3. **Medium · narrative** (Saboteur)
   - Where: Line 44 "These features provide room to service debt and absorb timing volatility, provided shipments convert to cash and cash remains available after corporate allocations."; line 47 "That difference does not itself reject any adjustment"
   - Problem: Neither paragraph says how the strengths and weaknesses net out. Each strength carries a condition and each weakness a disclaimer, so a committee reader gets no judgement first on whether the balance supports the current debt load.
   - Fix: Open the section with one sentence giving the net verdict (for example, whether strengths outweigh weaknesses at current leverage), then list the supporting points.
4. **Medium · visual** (Auditor)
   - Where: Line 47-48 "The principal weaknesses are demonstrated debt-funded extraction... before treating growth or acquired earnings as deleveraging." Basis: Financial foundation (CP-1); ...; crop CP-2-053-a.png, second paragraph
   - Problem: The handoff gives this paragraph a Basis line, but the page shows no Basis link after it. Its sources appear only inside the two figure chips, so the first paragraph shows a Basis link and the second does not.
   - Fix: Render a Basis link at the end of every paragraph that has a Basis line, even when the paragraph also contains figure chips.
5. **Low · narrative** (New reader)
   - Where: Line 44 "realized free cash flow and limited near-term principal"; "is not adopted as a quantified stress cushion"
   - Problem: The strengths are stated with no figures (FCF USD 1,880 million and FY2025 principal USD 93 million appear elsewhere). 'Not adopted as a quantified stress cushion' describes the analyst's method rather than saying something about the issuer.
   - Fix: Attach the FY2024 FCF and the FY2025 scheduled principal amounts to the strengths, and replace the method wording with a plain statement that management's stability claim is unquantified.
6. **Low · visual** (New reader)
   - Where: Crop CP-2-053-a.png: figure chips '6.57x' and '6.01x' in second paragraph
   - Problem: The two ratios are set in monospace with a dotted underline, unlike the surrounding text and unlike every number in the tables below. Nothing tells the reader that the chips can be clicked or what they open.
   - Fix: Use one figure style across prose and tables, and give the chips a visible hover or tooltip cue.

### Map: credit-risk transmission

Kind: map · handoff lines 50-64 · verdict **BLOCK**

- Narrative: The edges are carefully hedged (Analyst Interpretation vs Documentary Fact). But the section gives no judgement on what the map concludes, it relies on undefined internal register codes and pipeline phrasing, and it cites the only quantified link (C2-06) without a figure.
- Visual: The diagram is visible and not folded, but it is broken: labels split mid-word, edge labels are clipped and overlap the lines, and edges show the evidence type instead of the relationship. The edge table is also rendered twice on the page in two different typographic styles.

1. **High · visual** (Auditor, New reader)
   - Where: Credit-risk transmission diagram, CP-2_maps.png, region x340-1400 y260-660 (crop at /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-2-054-a.png)
   - Problem: Node labels break mid-word ("Installed aircraft com / ponents", "Debt-service resilienc / e", "Lower debt-capacity co / nfidence", "Denominator sensitivit / y"). Edge labels are clipped at both ends ("alyst Interpretati") and the two "Analyst Interpretation" labels on the converging edges overlap the curves and arrowheads. The drawing reads as broken.
   - Fix: Wrap node text at word boundaries or widen the nodes, and give edge labels enough room (or a legend keyed by line style) so that no label is clipped or crosses a line.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 50-52: "### Map: credit-risk transmission" followed directly by "| From | Relationship | Edge type | To | Evidence |"
   - Problem: The section has no judgement sentence. The reader is not told what the map concludes: three of the paths (dividend financing, acquisitions, earnings adjustments) converge on persistent leverage or lower debt-capacity confidence. This breaks the judgement-first standard.
   - Fix: Open with one bottom-line sentence naming the dominant transmission path to credit risk, then give the table.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 59: "Financial foundation (CP-1), C04 and C06; calculations C2-01 to C2-03 hold other movements constant"; line 54: "B1, B2 and X1 support the installed-base mechanism"
   - Problem: The Evidence column depends on internal register codes (B1, X1, T6, F1, G2, C04, C15, C2-06) that are not defined on the page, and on pipeline phrasing ("operating-model revenue-recognition row", line 57; "no house add-back rejection", line 63). The reader cannot follow any of it without another page.
   - Fix: Name the actual source item (filing section, table, or the specific metric and value) in plain words, and keep codes out of the reader's view or link them.
4. **Medium · narrative** (Saboteur)
   - Where: line 61: "Calculation C2-06 shows the FY2024 shortfall after those uses, not operating cash burn"
   - Problem: This is the one quantified link in the map, and it cites a shortfall without stating the amount, unit or basis. C2-06 does not appear in the adjacent Key credit metrics table, which cites C2-01, C2-03, C2-04, C2-05 and C2-07, so the reader cannot find the figure.
   - Fix: State the FY2024 shortfall in USD million with its basis in the row, or show it in Key credit metrics.
5. **Medium · visual** (Saboteur, New reader)
   - Where: Credit-risk transmission diagram, CP-2_maps.png, same region; edges carry only "Documentary Fact" / "Analyst Interpretation" / "Management Language"
   - Problem: The edges are labelled with the type of evidence, not with the causal claim, and every channel gets the same visual weight. A committee member cannot tell from the drawing which risk matters (for example the 6.57x vs 6.01x denominator gap at line 47) or what each arrow asserts without reading the table.
   - Fix: Label each edge with a short form of its relationship, show the evidence type through line style plus a legend, and mark the channels that are quantified.
6. **Medium · visual** (New reader, Saboteur)
   - Where: CP-2_maps.png: "Edges of the map, as stated" table (y~640-1700) and the section table "Map: credit-risk transmission" (y~2600-3400); CP-2_s-50.png y~190-850
   - Problem: The same 10-row edge table appears twice on one module page. The Maps-panel copy uses a monospace font with a bold, underlined, link-blue Relationship column, while the section copy uses a different style. The duplication and inconsistent typography make the page longer and suggest the two tables differ.
   - Fix: Render the edge table once, under the diagram, in the house table style, and let the section anchor point to it.
7. **Low · narrative** (New reader)
   - Where: line 54: "Business and transaction context (CP-1A)" rendered as "Business and transaction context (Business & governance)" in CP-2_s-50.png Evidence column
   - Problem: Once the module code is replaced, every Evidence cell repeats two names for the same source. That adds noise to the densest column of the table.
   - Fix: Use one reader-facing name for the source.
8. **Low · visual** (Auditor)
   - Where: CP-2_s-50.png, From column of the map table, a "Basis" chip on every row (y~255-820)
   - Problem: Every From cell carries a "Basis" chip even though the table already has an Evidence column, so the reader gets two competing source pointers per row.
   - Fix: Drop the per-row Basis chip where the table has its own Evidence or Source column.

### Calculations

Kind: prose/table · handoff lines 120-133 · verdict **CONCERNS**

- Narrative: The arithmetic checks out (6261−4348=1913; 18807+4348=23155; 23155/4173≈5.549; 5155; 778; −2505; 644), but the section opens with pipeline method wording instead of a judgement, and the operands have no labels, so the reader cannot audit the numbers that drive KF2.
- Visual: The section has no chart. The table renders cleanly with readable contrast, but raw .jsonl filenames make the Source column wrap over 6 to 8 lines, which bloats every row while the Operation column stays mostly empty.

1. **High · narrative** (Auditor, New reader)
   - Where: L122 "New arithmetic uses the Decimal-38 kernel. ... Upstream accepted calculations are carried without claiming fresh execution."; L126 "specified payment amounts together USD 4,348 million, carried from upstream"
   - Problem: The section opens with pipeline wording a reader should not see: "Decimal-38 kernel", "upstream accepted calculations", "fresh execution", "carried from upstream" and "reader passages". This breaks the house rule against pipeline vocabulary, and the opening tells a credit reader nothing about credit.
   - Fix: Keep only the scope facts (USD million, consolidated group, the FY2024 and FY2023 period dates, debt and cash measured at 30 September) and drop the wording about how the figures were computed.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: L131 "C2-06 | sum(1880, -2347, -2038) | USD -2,505 million" (also L126 "sum(6261, -4216, -132)", L127 "sum(18807, 4216, 132)")
   - Problem: The operands are bare numbers with no labels, so a reader cannot tell which figure is FCF, acquisitions or dividends without opening another page. The USD -2,505 million drives key finding KF2, and the reader cannot check it from this table.
   - Fix: Name each operand inline (for example FCF 1,880 − net acquisitions 2,347 − dividends and equivalents 2,038) so each row checks itself.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: L128 "5.5487658758686796069973640067098011023x; display approximately 5.55x"
   - Problem: A ratio printed to 37 decimal places means nothing to a credit reader. It is noise next to the 5.55x that matters and suggests a precision the input data does not have.
   - Fix: Show 5.55x in the Result cell and keep the full-precision value out of the reader table.
4. **Medium · narrative** (Saboteur)
   - Where: L126 "USD 1,913 million; specified payment amounts together USD 4,348 million, carried from upstream"
   - Problem: One Result cell carries two different quantities. A skimming reader can take 4,348 as part of the result, and the cell never says the 1,913 is pro-forma cash after the October dividend payout.
   - Fix: Put only USD 1,913 million in the Result cell and move the 4,348 payment total into the operand description.
5. **Medium · narrative** (Auditor, New reader)
   - Where: L120-L122 "## Calculations" followed directly by method preamble, then table
   - Problem: The section never says what the calculations show. The judgement that distribution-adjusted leverage is about 5.55x against a reported 4.51x, and that cash after payouts is about USD 1.9 billion, appears nowhere in this section. Data modules owe at least a bottom line.
   - Fix: Open with one judgement sentence stating what the adjusted figures change for the credit view, then the table.
6. **Medium · visual** (New reader, Auditor)
   - Where: Calculations table, Source column, shot CP-2_s-120.png, x≈1215-1385, y≈370-1550 (original px)
   - Problem: The raw filing file name "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" wraps over 6 to 8 lines in a narrow column. Every row becomes 3 to 4 times taller than its content, while the Operation column is mostly empty. The .jsonl name is an internal artifact, not a document a reader recognises.
   - Fix: Cite the filing as "FY2024 Form 10-K, p. 63" and widen the Source column or narrow the Operation column so each row fits in about two lines.
7. **Low · visual** (Auditor)
   - Where: Calculations table, ID column, shot CP-2_s-120.png, x≈360-410 (original px), "C2-01 Basis" ... "C2-07 Basis"; L122 "2023-10-01 through 2024-09-30"
   - Problem: Internal calculation IDs (C2-01, C06, C09) appear as row labels and as cross-references the reader cannot resolve. The ISO dates in the preamble do not match the page's "30 September 2024" date style.
   - Fix: Use plain row labels (for example "Cash after payout") and the page's date format.

## Legal & covenants (CP-4)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001/requests/CP-4/38bb6ccc9eb1f488ccd73936c3c5d7c68c3750a59e28b790d986365f2df75f08/1.response.md`

### Sources

Kind: prose/table · handoff lines 21-32 · verdict **BLOCK**

- Narrative: The section's single prose paragraph (line 31) is in pipeline register and leaves open whether unused issuer files could have cleared the block; the table names sources by file and pipeline labels, not in reader terms.
- Visual: The section has no chart, map or timeline. It is a five-row table, legible and with no clipping, but the hash column takes most of the width and forces multi-line wraps in the columns a reader actually needs.

1. **High · narrative** (Auditor, New reader)
   - Where: line 31: "The supplied handoffs are accepted under the transport convention. Their identity, issuer, analysis date and FY2024 retrospective scope match this invocation. Source pins were checked against the tool inventory."
   - Problem: The only prose paragraph in the section is written in pipeline language: handoffs, transport convention, invocation, source pins, tool inventory, upstream inventory, gate decision, visual verification. The house standard says this is not reader language, and a portfolio manager gets nothing usable from it. It is rendered verbatim on screen below the table (CP-4.dom.html, passage-text after the Sources table).
   - Fix: Replace it with one plain sentence saying which documents the view rests on (the FY2024 10-K exhibit index and the earlier source, financial and business analyses) and that no executed indenture or credit agreement was among them, or drop the paragraph.
2. **High · narrative** (Saboteur, Auditor)
   - Where: line 31: "Other pinned issuer files remain in the upstream inventory but were not used directly for this gate decision. No external evidence was acquired; no visual verification is claimed."
   - Problem: The reader is told that other issuer files were available but not used, and the paragraph does not say whether any of them could hold the executed documents whose absence blocks the whole module. A committee member could fairly read this as the block being self-inflicted, which undercuts the 'Not assessable' bottom line. Elsewhere the handoff says 'no Rank 1 text in pinned inventory' (line 75), but that answer is not given here.
   - Fix: State directly that none of the unused issuer files contains an executed credit agreement or indenture, so the reader sees that the block is caused by missing documents and not by skipped ones.
3. **Medium · narrative** (New reader)
   - Where: line 25: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"
   - Problem: The issuer's own filing appears only as a raw pipeline file name (accession number plus a .jsonl extension), which wraps across three lines on screen. The reader is never told in plain terms that this is TransDigm's FY2024 Form 10-K or when it was filed.
   - Fix: Show a human source label such as 'TransDigm Form 10-K, fiscal year ended 30 Sep 2024 (SEC accession 0001260221-24-000083)' and keep the file name out of the reader view.
4. **Medium · narrative** (New reader, Auditor)
   - Where: line 26: "| context | Run settings only; not issuer evidence |"; header line 23: "Exact source name or handoff"
   - Problem: A lowercase 'context' row listing run settings as a source and the column header 'Exact source name or handoff' expose pipeline internals. The reader cannot tell what 'context' is or why configuration sits in a sources list for a credit view.
   - Fix: Remove the run-settings row from the reader table (or label it 'Run configuration (not evidence)'), and rename the header to 'Source'.
5. **Medium · visual** (New reader, Auditor)
   - Where: Sources table, sha256 column; CP-4_s-21.png, region about x 300-1440, y 255-650 (original pixels)
   - Problem: About 40% of the table width goes to 64-character hex hashes that a credit reader cannot use. This squeezes the source-name and use columns into three-line wraps, and the header 'sha256' is jargon.
   - Fix: Drop the hash from the reader view (keep it in the calculation JSON or the Evidence page), or shorten it to a muted tooltip, and give the freed width to the source description.
6. **Low · narrative** (Saboteur)
   - Where: line 21-31: Sources section placed between Request and Capital structure (On this page: Request, Sources, Capital structure...)
   - Problem: The full sources table and its process paragraph come before the module's substantive tables. On the page the reader works through provenance plumbing before reaching the creditor consequences, which dilutes the judgement-first order even though the bottom line appears earlier.
   - Fix: Render Sources at the end of the module page, after Gaps and the forward-looking material, as the closing reference block.
7. **Low · visual** (New reader)
   - Where: Sources table rows 3-5, 'Module / authority and use' column; CP-4_s-21.png, y about 395-525 (displayed)
   - Problem: The rendered rows repeat the source name in the next cell ('Source readiness | Source readiness; supplied accepted handoff...'). The last row names the 'Business and transaction fact pack' but its use cell and the left navigation call it 'Business & governance', so one source carries two names on the same screen.
   - Fix: Use one display name per upstream analysis, matching the navigation, and let the use cell describe only what was taken from it.

### Bottom line

Kind: reader passage · handoff lines 35-38 · verdict **BLOCK**

- Narrative: The bottom line comes first and states a judgement ("not assessable"), but it is written in pipeline language (handoff, run setting, module codes in Basis). It also reads as an issuer fact when it is really a sourcing gap in this run.
- Visual: No chart belongs to this section. The passage is a ten-line wall of bold display type, its heading is hidden under the sticky header when the reader jumps to it, and the next section crowds it.

1. **High · narrative** (Auditor, New reader)
   - Where: L36: "creditors cannot rely on this handoff for contractual debt ... the run setting describing legal attachments as executed does not establish document receipt. Financial and business handoffs remain usable within their own scope"
   - Problem: The reader sees pipeline wording: "handoff" twice and "run setting", plus a sentence about the run's internal configuration contradicting itself. This breaks the house rule against pipeline vocabulary, and a PM can do nothing with the sentence about attachment settings.
   - Fix: Say it in reader terms, e.g. "this assessment" and "the financial and business analysis", and drop the run-configuration sentence or move it to Limitations.
2. **High · narrative** (Auditor)
   - Where: L37 Basis: "context, page 1; Source readiness (CP-0); Financial foundation (CP-1); Business and transaction fact pack (CP-1A)" (rendered DOM data-basis on the Basis button, CP-4.dom.html)
   - Problem: The Basis line carries module codes (CP-0, CP-1, CP-1A) and cites "context, page 1", which is run settings and not issuer evidence. The house rule says no module code appears on screen.
   - Fix: Cite the upstream analyses by reader name only, and leave run settings out of the issuer evidence basis.
3. **Medium · narrative** (Saboteur)
   - Where: L36: "Not assessable: No executed governing document available. ... The annual filing identifies indentures incorporated by reference rather than supplying their operative text"
   - Problem: "No executed governing document available" reads as a fact about TDG. A committee could take it as a documentation red flag about the issuer. The real cause is that this run's inputs did not include the indentures, and the filing itself shows they exist and are incorporated by reference.
   - Fix: State plainly that the indentures exist but were not in this review's inputs, and say what would unblock the view (supplying the referenced indentures and credit agreement).
4. **Medium · narrative** (New reader)
   - Where: L36: "contractual debt or distribution capacity, tested headroom, collateral reach, enforcement control or amendment protection"
   - Problem: The bottom line is one 89-word paragraph that strings five abstract legal concepts together and gives the reader no takeaway sentence about what this means for the TDG credit view now.
   - Fix: Lead with one short judgement sentence (covenant protection is unverified for this review), then list what cannot be relied on in a second, shorter sentence.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-4_bottom-line.png, crop x 320-1440, y 170-560 (scratchpad/tmp/CP-4-063-a.png): the whole 6-sentence paragraph is set in large bold display type
   - Problem: About ten lines of heavy bold headline type form a wall that is hard to scan. Emphasis is spread across all of it, so the actual verdict ("Not assessable") does not stand out from the run-setting commentary.
   - Fix: Set only the verdict phrase or first sentence in display weight and the rest in body text.
6. **Medium · visual** (Auditor)
   - Where: CP-4_bottom-line.png, top of content pane y≈190-230 (1440 scale): the "Bottom line" h4 is not visible, and partial control outlines peek out under the sticky run bar
   - Problem: Jumping to Bottom line via the 'On this page' link puts the section heading under the sticky header, so the reader lands on an unlabelled bold paragraph with clipped UI fragments above it.
   - Fix: Give the anchor a scroll-margin equal to the sticky header height so the section heading stays visible.
7. **Low · narrative** (Auditor)
   - Where: L36: "Not assessable: No executed governing document available."
   - Problem: The second sentence has a capital after the colon and no verb, so it reads as a status code rather than prose.
   - Fix: Write it as a full sentence, e.g. "Not assessable: the executed governing documents were not available to this review."
8. **Low · visual** (Saboteur)
   - Where: CP-4_bottom-line.png y≈520-545 (1440 scale): the "Basis" link sits directly above the "Timeline" heading with almost no gap
   - Problem: The next section's heading butts against the end of the bottom line, so the Basis link and the Timeline heading read as one block.
   - Fix: Add standard section spacing after the bottom-line passage.

### Chart data: covenant headroom

Kind: chart · handoff lines 45-50 · verdict **BLOCK**

- Narrative: The section is a single empty placeholder row that repeats pipeline wording ('executed-document gate failed', 'This module') five times, and only the last cell tells a portfolio manager in its own words that headroom cannot be assessed.
- Visual: No covenant-headroom chart or chart placeholder appears anywhere on the CP-4 page, although Timeline and Maps get 'Not established for this run' placeholders; what the reader gets instead is a raw seven-column 'Chart data' table of identical wrapped cells.

1. **High · narrative** (New reader, Auditor)
   - Where: line 49: "Not supplied: executed-document gate failed" (repeated in five cells)
   - Problem: Pipeline vocabulary ('gate failed', 'executed-document gate') appears five times across one row, and the heading 'Chart data:' is an internal render label. The house standard says 'gate' is not reader language, and a portfolio manager does not learn from it why headroom is missing.
   - Fix: State the gap once in reader terms, e.g. 'Not assessable: the executed credit agreement and indentures were not available, so no covenant test, threshold or headroom can be stated', under a reader heading such as 'Covenant headroom'.
2. **High · visual** (Saboteur, Auditor)
   - Where: Chart data: covenant headroom; CP-4_charts.png full page (no Charts panel; only Timeline y~320-360 and Maps y~380-470 placeholders) and CP-4_s-45.png region (330,210)-(1440,430)
   - Problem: No covenant-headroom chart is drawn anywhere on the module page, and there is no 'Not established for this run' placeholder for it, although Timeline and Maps each get one. The section still says 'This chart is not a legal compliance opinion', which points at a chart the reader cannot find. A missing headroom chart with no stated reason lets a reader assume the panel was dropped, not that headroom is unassessable.
   - Fix: Render a Charts panel with a visible 'Covenant headroom: not established for this run (no executed covenant documents)' placeholder, styled like the Timeline and Maps placeholders, and drop the raw chart-data table from the body.
3. **Medium · narrative** (Saboteur)
   - Where: line 49: "Not established: no test settled" vs "This module settles no covenant test"
   - Problem: The 'Reporting unit' cell says 'Not established' while the other cells say 'Not supplied', and the limitation text uses 'This module', which is pipeline self-reference. A reader cannot tell whether the covenant data is absent from the sources or present but unanalysed, and that difference matters for a credit committee asking whether covenants exist at all.
   - Fix: Use one consistent missing-data label and phrase the limitation about the documents (the governing agreements were not available), not about the module.
4. **Medium · visual** (New reader, Saboteur)
   - Where: CP-4_s-45.png crop (330,210)-(1440,430), Chart data: covenant headroom table
   - Problem: A seven-column table is spent on one row in which five cells repeat the same wrapped four-line string. The only informative text sits in the last column, so the eye has to cross a block of identical noise to reach it.
   - Fix: Collapse the empty row into a single full-width gap note, or one merged cell, that carries the limitation text.
5. **Low · visual** (Auditor)
   - Where: CP-4_s-45.png crop, 'Basis' chip in the Test cell next to the 'Basis and limitation' column
   - Problem: A 'Basis' link chip sits inside the first data cell while a separate 'Basis and limitation' column holds the limitation text, so the table has two different 'Basis' affordances.
   - Fix: Keep one basis location per row (the chip, or a Source column) and rename the prose column 'Limitation'.

### Events: Legal

Kind: timeline · handoff lines 51-56 · verdict **BLOCK**

- Narrative: The section has no bottom line. It is one placeholder sentence repeated seven times, written in pipeline language ("blocked module"), and it leaves unclear whether legal proceedings were checked at all, even though the pinned 10-K's Item 3 disclosure was available.
- Visual: The timeline renders on the page as a seven-column table of identical wrapped placeholders, with a Basis chip that links to an empty basis list. In the timeline screenshot the Timeline panel is scrolled out of view, so only its DOM text could be judged. Not verified: the Timeline panel's drawn appearance (it was hidden under the sticky header in CP-4_timeline.png); I judged it from CP-4.dom.html only.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 55: "Not supplied: no legal event established by this blocked module" (in all seven cells, including Event and Status)
   - Problem: The reader cannot tell whether TDG has no legal events or whether nobody looked. A committee member could read this as a clean litigation record. The pinned FY2024 10-K does contain Item 3 Legal Proceedings ("various claims and legal actions arising in the ordinary course of business ... will not have a material adverse effect"), and that disclosure does not depend on the missing executed indentures.
   - Fix: Open with one judgement-first line that says plainly whether the 10-K legal-proceedings disclosure was reviewed and what it shows, or that it was not reviewed and why. Label it as a gap, not as an absence of events.
2. **High · narrative** (Auditor)
   - Where: line 55: "no legal event established by this blocked module"; Timeline panel (CP-4.dom.html): "Not established for this run / no legal event established by this blocked module"
   - Problem: "Blocked module" is pipeline vocabulary. It describes the workflow's state rather than the issuer, which breaks the house rule against pipeline language on screen. Neighbouring rows also say "executed-document gate failed", so the reader meets internal gate jargon with no definition.
   - Fix: Use reader language, for example "Not assessed: the governing debt documents were not available for this review".
3. **Medium · visual** (New reader)
   - Where: Events: Legal table, CP-4_s-51.png, region about x 300-1160, y 215-345 (display coordinates)
   - Problem: A seven-column table repeats one placeholder sentence in every cell. Each cell wraps to four or five lines, so the reader has to scan seven copies of the same text to learn that the table is empty. That wastes vertical space and hides the message.
   - Fix: When no events exist, show a single full-width empty-state line with the reason in place of a seven-column table of identical placeholders.
4. **Medium · visual** (Auditor)
   - Where: Basis chip under the first cell of Events: Legal, CP-4_s-51.png about y 327; DOM: button class="basis-link" data-basis="[]"
   - Problem: The row has a Basis button whose basis list is empty. It suggests a source trail exists, but clicking it opens nothing. Every Not-supplied row in the neighbouring Map tables has the same empty Basis chip.
   - Fix: Hide the Basis chip when a row has no basis entries, or have it state the reason the row has no source.
5. **Low · visual** (Saboteur)
   - Where: CP-4_timeline.png top region (crop scratchpad/tmp/CP-4-066-a.png): Maps panel visible, Timeline panel scrolled above the sticky header
   - Problem: The same empty state appears twice on one page in two forms: the Timeline panel's "Not established for this run" and this table's "Not supplied: ...". In the supplied screenshot the Timeline panel itself sits out of view under the header, so the reader sees the table without the timeline it belongs to.
   - Fix: Use one empty-state wording for the timeline and its events table, and make the timeline anchor land with the panel's heading visible below the sticky header.

### Analytical appendix — complete canonical registers

Kind: register appendix · handoff lines 69-83 · verdict **BLOCK**

- Narrative: This section is a process register written for the pipeline, not for a credit reader: it uses gate, re-anchor, pin and producer vocabulary, contains a garbled \"method steps plus method steps\" sentence where register codes were replaced, and states its credit consequence last.
- Visual: The supplied screenshot does not capture this section, so the visual review relies on the rendered DOM. That shows the appendix heading dropped, an h5 table title out of sequence with its sibling sections, and six Basis links with empty data. Table cell layout could not be checked in an image.

1. **High · narrative** (Saboteur, New reader (promoted))
   - Where: Line 82: "T4.2, T4.3, T4.9–T4.13, T4D.1–T4D.8, T4F.1–T4F.6 and T4C.2–T4C.9 plus T4C.11–T4C.12 are not authored as completed analytical registers" — rendered in render/CP-4.dom.html (s-71) as "method steps plus method steps are not authored as completed analytical registers"
   - Problem: Replacing the register codes left a garbled sentence. The reader cannot tell which legal analyses (covenants, leakage, intercreditor, restructuring) were skipped, and that is the scope statement for a blocked module.
   - Fix: Name the omitted analyses in reader terms (for example covenant capacity, restricted-payment leakage, intercreditor and recovery mechanics), or write "all substantive legal analyses"; do not leave a code substitution that turns into "method steps plus method steps".
2. **High · narrative** (Auditor, New reader (promoted))
   - Where: Line 71 heading "Legal file gate and upstream re-anchor" (shown in the On this page outline and as the table title); line 73 columns "Re-anchored scope or observation" and "Gate consequence"; line 80 "refinancing/LME producer"
   - Problem: The ruling bans pipeline words such as re-anchor, gate and producer, yet they appear in the section title, the page outline, the column headers and the cells. A credit committee member reads process plumbing where a statement about document availability should be.
   - Fix: Retitle the section and its columns in reader language (for example "Legal documents available", "What the filing shows", "Effect on the legal view") and drop producer/upstream/re-anchor wording.
3. **Medium · narrative** (New reader)
   - Where: Line 75 "Not supplied; no Rank 1 text in pinned inventory"; line 77 "Source readiness, accepted pin in Sources"; line 76 "“legal_documents”: “executed” is not an actual executed attachment"
   - Problem: "Rank 1", "pinned inventory", "accepted pin" and a raw config key are internal vocabulary. A reader who has not seen the pipeline cannot decode them, and LME is never spelled out.
   - Fix: Say "no signed indenture or credit agreement was among the files provided" and "run settings marked legal documents as provided, but none were attached", and spell out liability management exercise.
4. **Medium · narrative** (Saboteur)
   - Where: Line 82: "The source gate terminates the substantive workflow... The selector tables above preserve required report placement without representing completed legal analysis."
   - Problem: The section's only prose opens with a process event, not the credit judgement, and then explains report-placement mechanics. The point that matters (no covenant capacity, leakage or pressure point can be relied on) comes last.
   - Fix: Open with the judgement ("No covenant capacity, leakage route or nearest pressure point is assessed because no signed governing documents were available") and remove the report-placement sentence.
5. **Medium · narrative** (Saboteur)
   - Where: Line 78: "FY2024 carrying debt USD 24,880 million; gross principal USD 25,068 million; issuer EBITDA As Defined USD 4,173 million"
   - Problem: Three headline credit figures sit in a 'blocked' appendix row with no reconciliation. A reader could compute leverage from them, against the module's own warning that they are not covenant inputs.
   - Fix: Keep the figures but add in the row that they are reported financial measures only and must not be used as covenant-defined debt or EBITDA.
6. **Medium · visual** (Auditor)
   - Where: render/CP-4.dom.html s-71: <h5>Legal file gate and upstream re-anchor</h5> after the h3 section headings, followed by <h4>QA Validation</h4>; the H3 "Analytical appendix — complete canonical registers" is not rendered
   - Problem: The appendix's parent heading is dropped and the table is headed h5 between h3 and h4 siblings. Heading levels skip, so the outline and screen readers show the table as orphaned, and nothing marks it as an appendix to the analysis above.
   - Fix: Render a visible appendix heading at the same level as its sibling sections, with the table one level below it, and keep the levels consistent with QA Validation.
7. **Medium · visual** (Auditor)
   - Where: render/CP-4.dom.html s-71 table rows: every row's Basis button has data-basis="[]"
   - Problem: Each of the six rows shows a Basis link that opens an empty basis. The reader is offered a source trail that leads nowhere, while the actual source sits in the Source column.
   - Fix: Fill each row's Basis from its Source cell, or hide the Basis control when it has no entries.
8. **Low · visual** (Auditor)
   - Where: shots/CP-4_s-69.png (whole image, 1440x2400)
   - Problem: The unit's screenshot shows the top of the module page (bottom line through Map: legal entities) and not this section. The appendix sits off-capture between Map: intercreditor and QA Validation (that screenshot opens at QA Validation), so its on-page layout cannot be checked from a capture.
   - Fix: Re-capture with the page scrolled to anchor s-71 so the table's width, wrapping and spacing can be judged.

### QA Validation

Kind: prose/table · handoff lines 84-99 · verdict **BLOCK**

- Narrative: This section is the pipeline's internal tooling and QA log with no bottom line. It leaks a module code and pipeline vocabulary to the reader, and its one material fact (no executed governing documents, so the module is blocked) is buried among rows about scripts that did not run.
- Visual: The section has no chart. The three-column table is legible and well spaced, but nothing styles the Result values, so FAIL looks the same as PASS, and the inline Basis buttons wrap awkwardly next to the check names.

1. **High · narrative** (Auditor, New reader)
   - Where: line 88: "Canonical filename tdg_CP-4_20240930.md; matching issuer/date/pathway; all three supplied handoffs listed with exact pins. No invocation digest invented." (rendered verbatim in CP-4.dom.html and shot CP-4_s-84.png, first row)
   - Problem: A module code (CP-4) appears on screen, along with pipeline vocabulary the house standard bans: canonical, handoffs, pins, invocation digest, re-anchored (line 91), gate, lane, H2 sections, report selectors, transport submission (lines 94-95). The rendering layer rewrote "CP-OS acceptance" to "Run activity acceptance" but missed the filename.
   - Fix: Strip module codes and internal filenames from reader text, and say each check in reader terms (for example "issuer, date and inputs match this run").
2. **High · narrative** (Saboteur, New reader)
   - Where: lines 84-98, whole table, e.g. line 91 "prepare_invocation.py | Not run: unavailable" and line 95 "validate_handoff.py | Not run: unavailable"
   - Problem: The section is the pipeline's internal QA log: six of eleven rows name Python scripts that did not run. It has no bottom-line sentence, so a committee member cannot tell what it means for the credit view. The one judgement that matters, that the analysis is blocked because no executed credit agreement or indenture was supplied, sits in row 2 among tooling noise.
   - Fix: Open with one judgement sentence (legal analysis blocked: no executed governing documents, so there is no covenant view), then either cut the tooling rows to a single line or move them out of the reader page.
3. **Medium · narrative** (Saboteur)
   - Where: line 88: "Identity and lineage | PASS" and line 98: "Subsequent events and graph discipline | PASS for blocked output"
   - Problem: The section opens on a PASS and ends on a PASS, so a skimming reader may come away thinking QA was broadly passed. In fact the module scored 0 out of 100 and its conclusion is Not assessable.
   - Fix: Put the FAIL rows (source documents, intercreditor) first, and state the overall outcome (Blocked, confidence 0/100) above the table.
4. **Medium · narrative** (New reader)
   - Where: line 92: "Applied supplied confidence formula with failed source-gate multiplier; calculation C4-QA records the zero result. This measures analytical readiness, not confidence that the documents are absent from the supplied inventory."
   - Problem: The reader needs another section to decode an internal calculation ID, and the double-negative caveat makes it unclear what the zero score means.
   - Fix: Say in plain terms: confidence is 0 out of 100 because no executed legal documents were available to analyse.
5. **Medium · visual** (Auditor, Saboteur)
   - Where: QA Validation table, Result column, shot CP-4_s-84.png region about x 600-790, y 270-1060 (original px)
   - Problem: PASS, FAIL and "Not run" all render in the same plain body text, with no status chip, colour or weight. The two decisive FAIL rows look exactly like the routine rows, so the most important cells do not stand out.
   - Fix: Show Result values as status chips (as the module's Not assessable chip already does) so FAIL reads differently from PASS and Not run.
6. **Low · visual** (New reader)
   - Where: QA Validation table, Check column "Basis" buttons, shot CP-4_s-84.png e.g. "Executed-document source gate / Basis" and "Intercreditor verification Basis"
   - Problem: The Basis button sits inline after each check name and sometimes wraps to its own line, so it reads as part of the label. It is unclear what a Basis link means for a QA check row.
   - Fix: Put the Basis link in a fixed spot (a narrow end column or a right-aligned icon) so check names read cleanly.

### Calculations

Kind: prose/table · handoff lines 100-107 · verdict **BLOCK**

- Narrative: The section reports one number, a 0/100 readiness score, wrapped in tool traces, field names, a method-file name, a module code and defensive self-attestation. The reader has to infer the real point: no covenant arithmetic was possible without the executed documents.
- Visual: The page has no chart. The one-row, five-column table is dense, wrapped prose with schema-style headers and an inconsistently styled ID. The note below it runs full width with no Basis line, but nothing is clipped or overlapping.

1. **High · narrative** (Auditor, New reader)
   - Where: L104: "Confidence formula: failed source gate S = 0 ... no separate QA penalty assigned. calculate sum("0", "0") = 0." / "qa_status Blocked"
   - Problem: The reader sees pipeline wording: a tool-call trace `calculate sum("0", "0")`, a raw field name `qa_status`, the term "source gate", and an undefined variable S. All of it is internal vocabulary that the house standard says is not reader language, and none of it is explained.
   - Fix: Say it in plain words, e.g. "Readiness score 0 out of 100 (Insufficient Information) because no executed credit agreement or indenture was available", and drop the tool trace and field names.
2. **High · narrative** (Auditor, Saboteur)
   - Where: L104 source-trace cell: "supplied CP_CONFIDENCE_SCORE.md formula and T4.1 source gate" (rendered as "CP_CONFIDENCE_SCORE.md formula and 'Legal file gate and upstream re-anchor' source gate")
   - Problem: A module code (CP_), an internal method file name and the pipeline term "re-anchor" all appear on screen as the 'source'. Two rules are broken: no module codes or pipeline vocabulary, and sources must be real evidence. A committee member cannot trace this to any issuer document.
   - Fix: Cite the issuer evidence the score rests on (the 10-K exhibit index showing no executed agreements) or leave the source as an explicit gap, and keep method-file names off the page.
3. **Medium · narrative** (Saboteur)
   - Where: L104: "Confidence Score 0 / 100; band Insufficient Information" ... "This measures analytical readiness, not confidence that the documents are absent" (L92)
   - Problem: A 'Confidence Score 0 / 100' in a covenant module reads like a credit signal: zero confidence in the covenants, or the worst covenant quality. It actually measures how complete the inputs were, and that qualification sits in the QA table above, not in this row. The number and its label invite a wrong reading.
   - Fix: Label the result as input readiness rather than a confidence or credit view, and put the one-line meaning in this row.
4. **Medium · narrative** (New reader)
   - Where: L106: "No carrying-value/principal difference is recast as a contractual definition conflict because the governing definition has not been examined."
   - Problem: The closing paragraph is a defensive list of things not done, with no judgement first. Its jargon ("gate register", "upstream observations", "recast as a contractual definition conflict") makes the reader work to learn the only takeaway: no covenant headroom was calculated.
   - Fix: Open with the bottom line, e.g. "No covenant headroom or capacity was calculated because the governing documents were not available", then add at most one sentence of qualification.
5. **Medium · narrative** (Auditor)
   - Where: L104 Limitation cell: "no fabricated component counts or full-run completeness claim."
   - Problem: The limitation tells the reader about the model's own integrity ("no fabricated") instead of the limits of the result. That is process self-attestation, not a reader-facing limitation, and it makes the reader wonder why fabrication was ever possible.
   - Fix: State the real limitation: the score cannot change until the executed agreements are obtained.
6. **Medium · visual** (New reader, Auditor)
   - Where: Calculations table, CP-4_s-100.png crop x=340-1440, y=1080-1360 (scratchpad/tmp/CP-4-071-a.png)
   - Problem: Five columns of tightly wrapped prose for a one-row table that holds a single number. The header 'Period, currency, quantity and source trace' is a schema label, and the key result (0/100) is buried inside a wrapped text cell with no emphasis. The ID is drawn in mixed styles: 'C4' as a small ref chip and '-QA' as plain text (DOM: `<small class="ref">C4</small>-QA`).
   - Fix: Show the single result as a short labelled statement or a compact two-column row with the value prominent, use reader headers such as 'Basis' and 'Limitation', and render the ID consistently or hide it.
7. **Low · visual** (Saboteur)
   - Where: Paragraph under the Calculations table, screenshot y≈1090-1120 (display coordinates)
   - Problem: The paragraph runs the full width of the content column with no Basis line, unlike the table rows above. The line length makes it hard to read, and it looks detached from the table it qualifies.
   - Fix: Keep the paragraph to the same measure as the other prose blocks and attach it as a table note or as a Basis-lined paragraph.

### Gaps

Kind: prose/table · handoff lines 108-118 · verdict **BLOCK**

- Narrative: The Gaps table lists the missing evidence correctly, but it is written in pipeline language (gate, module, consumer, predecessor, internal file names) and describes the analysis's limits rather than what the gaps mean for TDG's credit. It gives no judgement on which gap matters most.
- Visual: The section has no chart, only a five-column table. The table renders cleanly, but its dense multi-line cells make it slow to scan, a raw filename in the Source column wraps mid-token, and the Basis chips appear on only two rows.

1. **High · narrative** (Auditor, New reader)
   - Where: L117: "CP_DR_RESEARCH_BRIEF_V1.md, schema references and system references not supplied ... Bounded factual request for a source-acquisition predecessor, with Legal Covenant Interpreter as consumer ... No self-dependency is created"
   - Problem: The whole Research routing row is about the pipeline's own plumbing: an internal file name, "companion-format research brief", "predecessor", "consumer" and "self-dependency". It renders verbatim on screen (shot rows 1700-1830). It tells a credit reader nothing about TDG and breaks the house rule against pipeline vocabulary.
   - Fix: Drop the row from the reader view, or turn it into one plain line saying the executed governing documents still need to be retrieved, which the Governing-document row already says.
2. **High · narrative** (Auditor, Saboteur)
   - Where: L112: "Governing-document gate"; L110 column header "Effect on this module"; L117 "does not add a substantive block"
   - Problem: The row label uses "gate", the column header uses "module" and the cells use "block", all pipeline vocabulary. The Effect column describes what the analysis could not do, not what that means for the credit view: for example, covenant headroom and debt capacity are unknown and the reach of collateral and guarantees is unverified.
   - Fix: Rename the row to "Executed credit agreement and indentures" and the column to "What this leaves unknown for the credit view", and state the credit consequence in each cell.
3. **Medium · narrative** (New reader, Auditor)
   - Where: L112 Source: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 103–104"; L117 "context, page 1; supplied method and tool inventory"; L116 "Supplied source inventory"
   - Problem: The Source column shows an internal .jsonl extraction filename, plus internal references a reader cannot look up ("context, page 1", "supplied method and tool inventory"). A reader cannot trace these to a document.
   - Fix: Cite the document as a reader would know it, e.g. "TDG FY2024 Form 10-K, exhibit index, pp. 103–104", and drop the references to internal inventories.
4. **Medium · narrative** (New reader)
   - Where: L114: "No verified entity-value reach, legal jurisdiction edges, release mechanics, standstill or enforcement control"; L112 "SEC Ex-10.x and Ex-4.x"; L113 "independent-use rules"
   - Problem: The table uses undefined jargon and abbreviations: "entity-value reach", "jurisdiction edges" (graph vocabulary), "ICA" (never spelled out in this section), "Ex-10.x/Ex-4.x" and "independent-use rules". A portfolio manager has to decode these before seeing what is missing.
   - Fix: Spell out the intercreditor agreement and the exhibit types, and replace graph and internal terms with plain wording (e.g. "which subsidiaries guarantee the debt and in which jurisdictions").
5. **Medium · narrative** (Saboteur)
   - Where: L113: "Even after document retrieval, no exact headroom or remaining capacity can be inferred from issuer EBITDA or completed distributions"
   - Problem: Read quickly, "even after document retrieval" suggests headroom stays unknowable even with the documents. The table also never ranks the gaps, so the reader cannot see that the missing executed documents drive the Not assessable status and the other rows follow from it.
   - Fix: Start with a one-line judgement that the missing executed documents are the single gap that leaves covenant headroom unassessable, and say plainly that headroom also needs the compliance certificates.
6. **Medium · visual** (New reader, Auditor)
   - Where: Gaps table, /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/shots/CP-4_s-108.png region y~1400-1830 (crop /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-4-072-a.png)
   - Problem: The five dense text columns wrap most cells to four or six lines, so six rows fill about 650 px of wall-of-text. The Source filename breaks mid-token across four lines ("TDG_2024-09-30_10- / K_0001260221-24- / 000083_tdg- / 20240930.htm.jsonl").
   - Fix: Cut the cells to short phrases, or fold the "Required bounded follow-up" detail into an expandable row, and show short reader-facing source labels that do not wrap mid-identifier.
7. **Low · visual** (Auditor)
   - Where: Gaps table, Gap column, the "Basis" chip on the Governing-document and Research routing rows only (shot y~1250 and ~1765)
   - Problem: Only two of the six rows carry a Basis chip, and in the Gap column it sits inline with the wrapped label ("gate Basis"), so it reads like part of the row name. Why some rows have a basis and others do not is never explained.
   - Fix: Show the Basis affordance consistently (on every row or none), set apart from the label text, e.g. right-aligned or in its own cell.

### Front matter + Request + Next module

Kind: run plumbing · handoff lines 1-17, 18-20, 119-122 · verdict **BLOCK**

- Narrative: There is no credit judgement in these three sections. They are run plumbing shown as reader prose: a raw metadata dump with a visible module code and a conflicting run id, the model's instruction as the Request, and inter-module routing in pipeline vocabulary as Next module.
- Visual: There is no chart, map or timeline here. The visual problem is that the front matter is laid out as one unseparated wall of key: value text in body styling, and the plumbing sections take up space in the page's section list.

1. **High · narrative** (Auditor, New reader)
   - Where: Front matter, line 10 as rendered: "filename: tdg_CP-4_20240930.md committee_status: Blocked qa_status: Blocked confidence_score: 0 confidence_band: Insufficient Information gate_status: Blocked" (CP-4.dom.html #s-1; CP-4_s-1.png y~220-255)
   - Problem: The renderer substituted the module code in module_id but not in filename, so the code "CP-4" appears on screen. The block also prints pipeline keys (issuer_id, module_id, method_version, qa_status, gate_status, run_id) as reader text, which breaks the rule against module codes and pipeline vocabulary.
   - Fix: Do not render front matter as a passage. At most, show reader-facing status fields (as-of date, period, status) as labelled chips in the module header, with no filename and no snake_case keys.
2. **High · narrative** (Saboteur, Auditor)
   - Where: Front matter line 7 "run_id: tdg-2024-09-30-credit_snapshot-sol-medium" vs page header "Showing run: 30 September 2024 · Credit snapshot · TDG-READER-FORMAT-001" (CP-4_s-1.png y~160-230)
   - Problem: The same screen gives two different run identifiers, so a reader cannot tell which run this module belongs to. That undermines provenance for a committee.
   - Fix: Show one run identity, the library's, and drop the module's internal run_id from the page.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: Front matter "committee_status: Blocked ... confidence_score: 0 confidence_band: Insufficient Information" vs sidebar chip "Not assessable" (CP-4_s-1.png sidebar y~510-530)
   - Problem: The module's status appears in three vocabularies (Blocked, Insufficient Information with a score of 0, Not assessable). "confidence_score: 0" could be read as a zero-quality credit rating rather than "no executed documents to assess".
   - Fix: Use one reader status label, with a one-line reason (executed credit agreement and indentures not available), wherever the status appears.
4. **Medium · narrative** (Auditor, New reader)
   - Where: Line 121: "Pass this gate outcome to Relative value and security selection, Evidence validation and Committee challenge; ... then rerun the complete legal workflow; no question response is required during this run."
   - Problem: The 'Next module' text is routing for other modules, full of pipeline vocabulary (gate outcome, accepted handoffs, rerun the workflow, question response). The one credit-relevant warning is buried mid-sentence: do not treat filing-summary rankings, adjusted EBITDA or past distributions as verified legal permissions.
   - Fix: Rephrase for the reader as a judgement-first note on what the committee must not rely on until the executed documents are obtained, or keep this section off the reader page.
5. **Medium · narrative** (Auditor)
   - Where: Line 19: "Interpret the governing legal and covenant package, including restricted-group, guarantee, collateral, intercreditor and capacity mechanics, subject to the executed-document gate."
   - Problem: The Request is the instruction sent to the model, shown to the reader. It uses gate vocabulary and appears as a section ahead of the analysis tables, so the reader meets run plumbing before the content.
   - Fix: Turn it into a one-line scope statement (what this module covers, as of 30 September 2024) without "gate", or move it into a collapsed run-details area.
6. **Medium · visual** (New reader, Auditor)
   - Where: Front matter paragraph, CP-4_s-1.png region x~295-1160, y~215-260
   - Problem: Sixteen key: value pairs run together as one justified paragraph with no separators, so keys and values cannot be told apart (e.g. "module_id: Legal & covenants module_name: Legal Covenant Interpreter"). It is also styled as body text with the same weight as the analysis.
   - Fix: If any metadata is kept, render it as a small definition list or a chip row in muted type, visually separate from the narrative.
7. **Low · visual** (Auditor)
   - Where: On this page nav, CP-4_s-1.png sidebar y~670-690 and CP-4_s-119.png y~935
   - Problem: Front matter, Request and Next module are listed as navigable sections next to the analytical ones, which adds plumbing entries to the reader's table of contents.
   - Fix: Leave run-plumbing sections out of the On this page list.

### Capital structure

Kind: prose/table · handoff lines 39-44 · verdict **BLOCK**

- Narrative: The section is a one-row table that restates the bottom line in pipeline language ("gate failed", "do not promote"). It gives no judgement sentence and no debt quantum under a heading that promises a capital structure.
- Visual: The table is clean, aligned and legible. It spends a full-width five-column grid on one prose row, and its Source cell is a wrapped internal .jsonl file name broken mid-token.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 43, Legal assessment cell: "Not assessable: executed-document gate failed"
   - Problem: "Gate failed" is pipeline vocabulary, which the house standard bans from the page. A committee member reads it as a process failure, not as "the indentures and credit agreement were not available to read".
   - Fix: Say what is missing in reader language, e.g. "Not assessable: the executed indentures and credit agreement were not available".
2. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 43, Creditor consequence cell: "Do not promote the financial debt stack into a verified legal priority or recovery waterfall"
   - Problem: This is an instruction to downstream modules ("do not promote"), not a consequence a creditor can act on. It does not tell the reader what they lose: ranking, security and recovery order cannot be confirmed.
   - Fix: State the creditor consequence directly, e.g. "Ranking, security and recovery order of the debt cannot be confirmed from the documents reviewed".
3. **Medium · narrative** (Saboteur)
   - Where: Line 39 heading "Capital structure" with its single row at line 43: "FY2024 contractual capital structure | Not assessable"
   - Problem: The heading promises a capital structure, but the section gives no instrument, amount or ranking. The only debt figures (USD 24,880 million carrying, USD 25,068 million gross principal) sit further down in the "Legal file gate and upstream re-anchor" table. A reader skimming by heading finds nothing here and may miss them.
   - Fix: Either open with one judgement sentence that gives the known FY2024 debt quantum and says its legal ranking is unverified, or title the section to match what it actually holds.
4. **Medium · visual** (New reader, Auditor)
   - Where: Capital structure table, Source column; shot CP-4_s-39.png, crop x 340-1410, y 210-390 (scratchpad/tmp/CP-4-064-a.png)
   - Problem: The Source cell shows the internal file name "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 103-104". It wraps over three lines, breaks mid-token at "10-/K_", and exposes the pipeline's .jsonl extraction format instead of a document a reader would recognise.
   - Fix: Render the source as a reader-facing citation, e.g. "TransDigm FY2024 Form 10-K, exhibit index, pp. 103-104", and keep the accession detail in Sources.
5. **Low · visual** (New reader)
   - Where: Capital structure table, Scope cell "FY2024 contractual capital structure Basis"; shot CP-4_s-39.png, y about 255-300 (displayed)
   - Problem: The faint grey "Basis" chip sits inline after the scope text and reads as part of the label. A five-column table also carries one row of prose, which forces the eye across about 1,000 px for a single statement.
   - Fix: Show a single-row status as a short sentence or callout, and give the Basis link a clearly distinct style.

### Map: legal entities

Kind: map · handoff lines 57-62 · verdict **BLOCK**

- Narrative: The section is a placeholder. Its only text is a pipeline phrase (\"executed-document gate failed\") repeated in five cells, and it gives no plain-language bottom line on what the missing entity structure means for credit.
- Visual: There is no map drawing. The Maps panel shows a small grey \"Not established for this run\" note, and the section shows a five-column table of identical placeholder cells: visible, not folded away, but it wastes space and repeats the same gap twice.

1. **High · narrative** (Auditor, New reader)
   - Where: line 61: "| Not supplied: executed-document gate failed | Not supplied: executed-document gate failed | ... |" (all five cells); Maps panel CP-4_maps.png top (crop CP-4-067-a.png): "executed-document gate failed"
   - Problem: The only thing the reader is told is "executed-document gate failed". "Gate" is pipeline vocabulary the house standard bans, and the phrase never says in plain terms what is missing (the executed credit agreement and indentures were not in the files). A portfolio manager cannot tell whether this is a system fault or a missing document.
   - Fix: Replace the placeholder with one plain sentence, e.g. that the entity map could not be drawn because the executed credit agreement and indentures were not among the files, without the word gate.
2. **Medium · narrative** (Saboteur)
   - Where: line 59-61: "| From | Relationship | Edge type | To | Evidence |" followed only by "Not supplied: executed-document gate failed"
   - Problem: The section gives no bottom line on what the missing map means for credit. It never says that the issuer/guarantor perimeter, structural subordination and restricted versus unrestricted subsidiaries are unknown. A committee member may read an empty map as "no structural issues" rather than "structure not assessed", which treats missing as zero.
   - Fix: State in one line that the guarantor and restricted-group perimeter is unassessed for this run and that structural-subordination risk stays open.
3. **Medium · narrative** (New reader)
   - Where: line 57/59: "### Map: legal entities" and column header "Edge type"
   - Problem: "Map:" as a heading prefix and the "Edge type" column are graph-builder vocabulary rather than reader language. A credit reader expects something like "Group and guarantor structure" with relationship types such as issuer, guarantor or restricted subsidiary.
   - Fix: Title the section in reader terms (e.g. "Legal entity and guarantor structure") and label the column "Relationship type" or drop it.
4. **Medium · visual** (New reader, Saboteur)
   - Where: Map: legal entities table, CP-4_s-57.png region y≈230-350 (original px), and the same block in CP-4_maps.png y≈1760-1900
   - Problem: A five-column table whose cells all repeat the same placeholder takes up a full table block with headers and carries no information. The repetition looks like a rendering fault, and it appears twice on the page (Maps panel and section).
   - Fix: Show a missing map as a single gap notice spanning the width (heading plus one sentence), not as a table of identical placeholder cells.
5. **Low · visual** (Auditor)
   - Where: CP-4_maps.png Maps panel (crop CP-4-067-a.png): "Not established for this run" vs section table line 61 "Not supplied: ..."
   - Problem: The same absence is worded two ways on one page ("Not established for this run" in the Maps panel, "Not supplied" in the table), and the cause is printed in small grey type that is easy to miss.
   - Fix: Use one wording for the absence in both places, with the reason at body-text size and contrast.
6. **Low · visual** (Auditor)
   - Where: CP-4_s-57.png, first cell "Not supplied: executed-document gate failed Basis"
   - Problem: The Basis chip sits on the first placeholder cell while the Evidence column also reads "Not supplied", so the reader gets a source link on a row that has no evidence.
   - Fix: When the map is a gap notice, put one Basis reference on the notice instead of a per-cell chip.

### Map: intercreditor

Kind: map · handoff lines 63-68 · verdict **BLOCK**

- Narrative: The section has no analysis, only a placeholder repeated across five cells in pipeline wording ("gate failed"). It never says what document is missing or what that means for lien ranking.
- Visual: No map is drawn. The Maps panel shows a short "Not established for this run" note, and the section then repeats it as a full-width table of identical placeholder cells, one of which carries a Basis link with nothing behind it. The layout is legible but redundant.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 67: "| Not supplied: executed-document gate failed | Not supplied: executed-document gate failed | ... |" (all five cells); also the Maps panel caption "executed-document gate failed" (CP-4_maps.png, approx. y 360-390 at full resolution)
   - Problem: The only content in the section is pipeline wording ("gate failed") repeated five times. The house standard bars "gate" as reader language, and the reader is never told what is actually missing: the executed intercreditor agreement, credit agreement and indentures.
   - Fix: Use a single plain-English row or sentence, for example "Not established: the executed intercreditor agreement, credit agreement and indentures were not available for this run", without the word gate.
2. **Medium · narrative** (Saboteur)
   - Where: Line 63-67 "### Map: intercreditor" table holding placeholders only; the consequence appears only far below in QA Validation: "An unexamined ICA is not treated as benign."
   - Problem: The section never gives the credit consequence: lien priority, pari passu ranking and enforcement control between secured lenders are unverified. A reader skimming the empty map could take the absence of drawn edges as an absence of intercreditor risk.
   - Fix: Add one line stating that intercreditor ranking and enforcement terms are unverified and must not be assumed pari passu or benign until the executed agreement is reviewed.
3. **Medium · visual** (New reader, Auditor)
   - Where: Map: intercreditor table, CP-4_s-63.png, crop approx. x 340-1440, y 220-360 (full resolution); same empty map shown again in the Maps panel, CP-4_maps.png approx. y 340-390
   - Problem: The same missing map is shown twice: once as a compact "Not established for this run" note in the Maps panel, and again as a full-width five-column table of identical placeholder cells with a "Map:" heading even though no map is drawn. This takes up space and repeats the same nothing.
   - Fix: When no map exists, keep only the one-line "Not established" note and suppress the empty five-column table, or collapse it into one sentence under the heading.
4. **Low · narrative** (New reader)
   - Where: Line 65 column headers: "| From | Relationship | Edge type | To | Evidence |" and heading "Map: intercreditor"
   - Problem: "Edge type" is graph-model vocabulary rather than credit language, and the lower-case selector-style heading "Map: intercreditor" reads like an internal label.
   - Fix: Use reader headings such as "Intercreditor arrangements" and a column like "Nature of priority or control" instead of "Edge type".
5. **Low · visual** (Auditor)
   - Where: Rendered DOM render/CP-4.dom.html, s-63 row: <button class="basis-link" ... data-basis="[]" aria-label="Basis for row: Not supplied: executed-document gate failed">Basis</button>
   - Problem: A Basis link is drawn on a placeholder row with an empty basis list, so the reader is offered a source trail that leads nowhere.
   - Fix: Hide the Basis control when the row has no basis entries.

## Security selection (CP-3)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001/requests/CP-3/c9c1c598721987ca582298a7d52f6191aa8c193d74f62c274865899acb7b0f4e/1.response.md`

### Events: Instruments

Kind: timeline · handoff lines 75-96 · verdict **BLOCK**

- Narrative: The section is a maturity schedule with no amounts, no judgement first and a closing note in pipeline wording, so the reader gets dates without any sense of how large the refinancing risk is.
- Visual: The timeline is visible but sits far from the table, labels only the two end dates, overlaps the August 2028 points and uses one colour for all instrument classes. The table is padded with constant columns and wrapped file names.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 80: "TransDigm Inc. 2028 secured notes maturity | Scheduled — August 15, 2028 | ... | Secured funding concentration; no call exercise assumed" (same pattern on lines 79-92)
   - Problem: This is a maturity schedule with no principal amount on any of its 14 rows, yet the Credit relevance column claims a "Secured funding concentration" (line 80) and a "calendar-year funding cluster" (line 82). A committee can't size the 2028-2029 wall or check the concentration claim, so it is left to guess how big the refinancing risk is.
   - Fix: Add an amount column (outstanding principal, USD million, as of 2024-09-30, from the 10-K debt note) and quantify any concentration or cluster claim, or write that the amount was not extracted.
2. **High · narrative** (Auditor, Saboteur)
   - Where: line 94: "Publication date is inherited from Source readiness. ... Subsequent distribution settlement and securitization draw remain in the upstream event lane and are excluded from the September debt stack."
   - Problem: The section opens with a bare table and closes on caveats and pipeline wording ("inherited from Source readiness", "upstream event lane"). Nowhere does it say what the schedule means for credit, for example whether the 2028-2029 cluster is a refinancing risk. The judgement-first rule is broken and internal vocabulary reaches the reader.
   - Fix: Open with a one-sentence bottom line on the maturity profile (when the first wall falls and how large it is), and rewrite the closing note in reader language without module or lane names.
3. **High · visual** (Saboteur, Auditor)
   - Where: Timeline, Instruments lane: CP-3_timeline.png, crop x330-1440 y190-320 (scratchpad/tmp/CP-3-081-a.png)
   - Problem: Only the two end dates (2027-11-15, 2033-01-15) are labelled, there are no year ticks, and every dot is the same blue whether the instrument is secured, subordinated, a term loan or the revolver. The 2028-08-15 and 2028-08-24 dots overlap into one blob (left:14.51% and the next point). A reader can't tell which instrument matures when, or see the 2029 cluster's seniority mix, without hovering.
   - Fix: Add yearly ticks, colour or shape the points by instrument class with a legend, and offset or stack points that coincide.
4. **Medium · narrative** (New reader)
   - Where: line 86: "Distinct floating-rate refinancing date"; line 88: "Distinct from Tranche K despite lower contractual margin"; line 84: "Compare only after controlling for security and maturity"
   - Problem: Several Credit relevance cells are analyst instructions or cross-references to data that isn't on the page (margins, coupons for the secured notes) rather than a statement of why the date matters for credit. The reader can't act on "lower contractual margin" because no margin is shown.
   - Fix: State each row's credit relevance in plain terms (seniority, rate type, size) and show any margin or coupon the cell refers to.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-3_timeline.png: Timeline at top (~y200-300) vs Events: Instruments table (~y1500 onward); heading "Dated events by module"
   - Problem: The timeline sits above Front matter, about 1,300 px and five sections away from the table it draws, so the reader can't read the two together. Its caption "Dated events by module" is pipeline wording.
   - Fix: Place the timeline directly above or beside the Events: Instruments table, and caption it in reader terms (e.g. "Debt maturities, FY2024 capital structure").
6. **Medium · visual** (New reader)
   - Where: CP-3_s-75.png Events: Instruments table, columns Date precision / Published / Status / Source (y215-1215 at 1200-px scale)
   - Problem: Three of the seven columns carry no information: Date precision is "day" on every row, Published is "2024-11-07" on every row, and Status repeats the event date in words. The Source column wraps a long file name over three lines on every row. So each row is 3-4 lines tall, the ISO dates break mid-value ("2027-11-/15"), and the table runs about 1,000 px for 14 maturities.
   - Fix: Drop or fold the constant columns into a note, shorten Source to "10-K FY2024, p.59", and let the date column hold the date on one line.
7. **Low · narrative** (New reader)
   - Where: line 94: "excluded from the September debt stack"
   - Problem: "September debt stack" is shorthand for the 30 September 2024 capital structure, and "securitization draw" is not explained in this section.
   - Fix: Write "the debt outstanding at 30 September 2024" and say briefly what the excluded securitization draw is.

### QA Validation

Kind: prose/table · handoff lines 411-427 · verdict **BLOCK**

- Narrative: This section is an internal QA log written in pipeline vocabulary (script names, handoff pins, register IDs, a CP-3 code, undefined E/C/S/P variables). It has no judgement-first statement a credit reader can use, and the confidence result, 24/100, is not stated plainly here.
- Visual: There is no chart. The section is a 10-row, 3-column table followed by a dense paragraph; it is legible but has empty Basis chips on every row, uneven row heights from wrapped chips, and an unbroken text block below.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: L415-421: "prepare_invocation.py | Not run: unavailable | Matched supplied run_id, issuer, as-of, pathway and all five handoff pins"; "validate_handoff.py ... canonical filename, six H2s ... write_handoff supplies transport checks"
   - Problem: The whole table is an internal pipeline log: script filenames, run_id, "handoff pins", "canonical", "H2s", "write_handoff", "full_analytical_complete", register IDs T3/T3B/T3C. None of this is reader language, which breaks the house rule. A credit committee member cannot act on any of it.
   - Fix: Keep this mechanism log out of the Modules page, or reduce it to one reader sentence on what was and was not checked and what that means for reliance.
2. **High · narrative** (Auditor, New reader (promoted))
   - Where: L421: "CP-3A/CP-3B schema/system references, CP-3_SYSTEM_REFERENCE.md, support position-sizing file, CP_DR_RESEARCH_BRIEF_V1.md" (rendered as "Security selection/Security selection schema/system references, CP-3_SYSTEM_REFERENCE.md")
   - Problem: A module code (CP-3) and internal file names are shown on screen. The renderer's code substitution also turns CP-3A/CP-3B into the garbled "Security selection/Security selection", so neither the codes nor their replacement make sense.
   - Fix: Show no module codes or internal file names; if the missing method references matter, describe them in plain words, for example "the security-selection scoring reference was not available".
3. **High · visual** (Auditor, Saboteur (promoted))
   - Where: QA Validation table, every row's "Basis" chip; shot CP-3_s-411.png, region y~240-880 (crop tmp/CP-3-087-a.png); DOM render/CP-3.dom.html rows CP-3.md:415-424 all have data-basis="[]"
   - Problem: Each of the ten rows shows a clickable Basis chip whose basis is empty. It looks like source support but leads to nothing. The confidence census paragraph below has no Basis line at all.
   - Fix: Do not render a Basis chip when the row has no basis; show it as an explicit gap or give the row real support.
4. **Medium · narrative** (Saboteur, New reader (promoted))
   - Where: L426: "E = 60 ... C = 50% ... S = 0.7 partial. One MATERIAL decision-readiness finding incurs P = 15 and Restricted status"
   - Problem: This is a single 150-word wall of text with undefined variables E, C, S and P. It also never states the resulting score. The table above gives "score 24" (L416) with no scale; the scale "24 /100" appears only in the Calculations table. The reader cannot connect 60 and 50% to 24, and may read 60 as the confidence level.
   - Fix: Lead with the outcome (confidence 24/100, Insufficient Information, and why), then list the components in a short labelled table with plain names.
5. **Medium · narrative** (Saboteur)
   - Where: L424: "MATERIAL, no CRITICAL whole-module failure | ... Only dependent decisions withheld; fundamentals gate passes"
   - Problem: Status words such as MATERIAL, CRITICAL, gate and "Passed for bounded use" (L423) read as pass/fail approvals. A skimming reader could take them as clearance, although the recommendation is Requires More Work. The judgement that matters is buried under process vocabulary.
   - Fix: State the reliance conclusion directly: fundamentals usable, while relative value, protection and sizing are not established, so no position call.
6. **Medium · visual** (New reader)
   - Where: QA Validation table, first column; shot CP-3_s-411.png, y~240-880
   - Problem: The Basis chip wraps under long labels ("completeness_check.py", "Unavailable companions", "Recommendation gate", "Evidence quality / material finding"), so row heights are uneven. The code-styled filenames in the label column add visual noise to a table the reader cannot use.
   - Fix: Use short plain-language check names and keep the chip inline or in its own narrow column so that rows align.
7. **Low · visual** (New reader)
   - Where: Census paragraph under the table; shot CP-3_s-411.png, y~890-1030
   - Problem: It is a full-width, roughly 115-character line set as one dense block, with the equation fragment "C = 50%" split across a line break, so it is hard to scan.
   - Fix: Break the census into a small two-column table or a short list so that each component reads on its own.

### Sources

Kind: prose/table · handoff lines 22-35 · verdict **BLOCK**

- Narrative: The Sources section, handoff lines 22-35, is a source table and a provenance paragraph. Module codes are stripped on screen, but pipeline vocabulary remains (handoff, pin, lineage, invocation digest, accepted Blocked legal gate), and two decision-relevant limitations sit inside this paragraph.
- Visual: The section has no chart, map or timeline; it renders as a three-column table and a paragraph. The sha256 hash column takes about a third of the table width and forces the useful columns to wrap, and the raw filename breaks mid-token.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 34: "Every supplied handoff matches tdg, 2024-09-30 and the historical FY2024 scope; its exact pin is the accepted lineage. No new acceptance receipt or invocation digest is required." The same text appears in render/CP-3.dom.html at id s-22.
   - Problem: The reader sees pipeline vocabulary on the page: handoff, pin, lineage, acceptance receipt, invocation digest, and "Source texts are evidence, not instructions; no visual checks are claimed". The house rule bans this language, and a portfolio manager cannot interpret any of it.
   - Fix: Drop the pipeline-provenance sentences from the rendered page and keep only reader-relevant scope statements, such as which filing and period the analysis relies on.
2. **High · narrative** (Auditor, New reader)
   - Where: Table header, line 24: "Exact source name or supplied handoff | Module / authority and use | sha256". Row, line 32: "accepted Blocked legal gate, not a completed protection assessment". Seen in shots/CP-3_s-22.png, top table.
   - Problem: The column headers name "handoff" and "Module", and a row says "accepted Blocked legal gate". These are internal pipeline status words. "accepted Blocked" also reads as a contradiction to someone outside the pipeline.
   - Fix: Rename the columns to reader terms, for example 'Source' and 'What it supplied'. Describe the legal input in plain words, for example 'Legal & covenants analysis: incomplete because the executed debt documents were not available'.
3. **Medium · narrative** (Saboteur)
   - Where: Line 34: "No external research or enterprise market observations were acquired. The annual filing was published after the measurement date; this is retrospective analysis, not contemporaneous trading advice."
   - Problem: Two limitations that matter to the decision sit at the end of a provenance paragraph in Sources: there is no market data at all, and the analysis uses a filing published after the as-of date. A reader who skips Sources misses them, even though they explain why every relative-value conclusion is withheld.
   - Fix: Move these two statements into the module's Limitations passage, or confirm they are there, and leave Sources to list documents only.
4. **Medium · narrative** (New reader)
   - Where: Line 26: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl". Line 27: "context | Dated settings only, not issuer evidence".
   - Problem: The main source is shown as a raw machine filename with a .jsonl extension and not as a document a reader can recognise. The "context" row names an internal configuration input that means nothing to the reader.
   - Fix: Name the source as a document, for example 'TransDigm Form 10-K for fiscal year ended 30 Sep 2024 (filed 7 Nov 2024)', and leave run-configuration inputs off the reader's source list.
5. **Medium · visual** (New reader, Auditor)
   - Where: The sha256 column of the Sources table in shots/CP-3_s-22.png, roughly x 740-1150 and y 220-670 (display coordinates).
   - Problem: 64-character hex hashes take about a third of the table width and carry no meaning for a credit reader. They push the useful columns into narrow cells that wrap onto three lines.
   - Fix: Hide the hash column on the reader page, or move it to a collapsed or Evidence-page view, and give the two descriptive columns the width.
6. **Low · narrative** (New reader)
   - Where: Rendered rows such as "Source readiness | Source readiness; accepted source inventory..." and "Financial foundation | Financial foundation; accepted annual financial facts..." in render/CP-3.dom.html at s-22.
   - Problem: After the module codes were stripped, the second column repeats the first column's name, and every row starts with "accepted". This adds noise and no information.
   - Fix: Show each upstream module's name once and describe in plain terms what it contributed.
7. **Low · narrative** (Auditor)
   - Where: The page's On this page navigation in shots/CP-3_s-22.png, left column: "Request, Sources, Relative value, Portfolio Fit, Events: Instruments...".
   - Problem: Sources appears mid-page, between Request and the remaining analytical sections. A reader who meets Sources expects the analysis to have ended, but more judgement passages follow.
   - Fix: Render Sources after the last analytical section so the reading order is judgement first and references last.
8. **Low · visual** (Auditor)
   - Where: The first table row in shots/CP-3_s-22.png, near y 255-280 (display coordinates): the filename breaks as "TDG_2024-09-30_10-K_0001260221-24-" / "000083_tdg-20240930.htm.jsonl".
   - Problem: The long filename breaks in the middle of a token, so the reader sees a fragmented identifier. The same mid-token break repeats in the Events table Source column directly below.
   - Fix: Use a short document label that wraps at word boundaries.

### Bottom line

Kind: reader passage · handoff lines 38-44 · verdict **BLOCK**

- Narrative: The judgement comes first and is clear (withhold a tranche preference, do not call the debt unattractive), but the prose names source modules in its sentences, leaves the earnings measure undefined, and ends on internal status codes.
- Visual: This section has no chart. As laid out on the page, the bottom line is a 21-line bold display block with a hidden heading and no visible Basis link, so it reads as an unsourced wall of text rather than a headline.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 39: "The financial foundation reports issuer-adjusted earnings of USD 4,173 million ... while the fundamental synthesis identifies equity-directed allocation as the constraint"
   - Problem: The narrative sentence names the source modules ("The financial foundation reports", "the fundamental synthesis identifies"). That puts source references and pipeline module names inside the prose, which the house standard forbids. A reader who has not seen those modules cannot tell what either label means.
   - Fix: State the facts as the module's own judgement and leave attribution to the Basis line.
2. **High · visual** (Auditor, Saboteur)
   - Where: Bottom line block, shots/CP-3_bottom-line.png, region x320-1440 y180-880 (crop scratchpad/tmp/CP-3-075-a.png). DOM: section#bottom-line has no basis-link button
   - Problem: Both bottom-line paragraphs render with no visible Basis link, while every key finding below has one. The sources (the CP-1/CP-2 modules and the 10-K pages 58-60 and 172-173) can be reached only by clicking individual figure buttons. The headline judgement therefore looks unsourced, which breaks the rule that each paragraph has a Basis line.
   - Fix: Show a Basis link after each bottom-line paragraph, the same way the key findings show theirs.
3. **Medium · narrative** (Saboteur)
   - Where: Line 39: "issuer-adjusted earnings of USD 4,173 million for fiscal 2024"
   - Problem: "Issuer-adjusted earnings" does not say which measure this is. The key findings on the same page use "issuer-adjusted EBITDA". A committee member could read USD 4,173 million as net income or as adjusted EBITDA.
   - Fix: Name the measure exactly (for example, issuer-defined EBITDA As Defined, FY2024) and use the same label throughout the page.
4. **Medium · narrative** (New reader, Auditor)
   - Where: Line 42: "Relative value is Unclear and the security recommendation is Requires More Work throughout the identified investable stack."
   - Problem: The sentence ends on capitalised internal status codes ("Unclear", "Requires More Work") and the jargon phrase "identified investable stack". These are rating-workflow labels, not reader language, and they repeat the opening judgement without adding to it.
   - Fix: Close with a plain statement of what the committee can and cannot do now, for example that no tranche preference is supported until prices and legal recovery are verified.
5. **Medium · visual** (New reader, Saboteur)
   - Where: Bottom line block, shots/CP-3_bottom-line.png y195-715 (about 21 lines of bold display type)
   - Problem: Two paragraphs of about 110 words in total are set in large bold headline type, and the visible "Bottom line" heading is hidden (sr-only). The reader faces a 21-line bold wall with no stopping point. The one-sentence judgement gets the same weight as the carrying-debt accounting detail.
   - Fix: Set only the opening judgement sentence as the headline and give the supporting figures normal body weight under a visible Bottom line label.
6. **Low · narrative** (New reader)
   - Where: Line 42: "Accounting carrying debt of USD 24,880 million is the debt-stack basis, not a traded market value; gross principal of USD 25,068 million is retained separately."
   - Problem: "Debt-stack basis" and "retained separately" describe how the pipeline treats the numbers, not what they mean for a creditor. The two debt figures also have no as-of date in the sentence.
   - Fix: Give the date (30 September 2024) and explain briefly why carrying value and principal differ, without the bookkeeping wording.
7. **Low · visual** (Auditor)
   - Where: shots/CP-3_bottom-line.png, top strip y175-185 at right (x~850-1180) and the right half of the content column y195-715
   - Problem: Slivers of the scrolled-away module-head controls show clipped under the sticky run bar. The bold text block also fills only about half the content width, leaving a large empty band to its right. Monospace dotted figure buttons sit inside bold proportional type, which makes the figures look like code.
   - Fix: Clip the head cleanly under the sticky bar and style figure buttons in the surrounding typeface so they read as numbers, not code.

### Key findings

Kind: reader passage · handoff lines 45-54 · verdict **BLOCK**

- Narrative: The four findings come in the right order and each leads with a bold judgement. But the judgements are all about what cannot be concluded, the only numeric finding has no period or basis, and module or pipeline wording ("The fundamental synthesis carries", "supported output") leaks into the narrative sentences.
- Visual: The bullet list is clean and readable at 1440 px. The third bullet has lost its Basis link in rendering (confirmed in the DOM), and the two ratios are styled as monospace code-like buttons that clash with the body text.

1. **High · narrative** (Saboteur, New reader)
   - Where: Line 50: "approximately 3.60x issuer-adjusted EBITDA coverage of net cash interest, alongside a distribution-adjusted static net-leverage illustration of approximately 5.55x"
   - Problem: Neither ratio states its period (FY2024? last twelve months?) or how it was adjusted. "distribution-adjusted static ... illustration" is not defined, so the reader cannot tell whether 5.55x is the actual leverage or a hypothetical one. Both figures are hedged with "approximately" and then dismissed as "illustrative", which leaves the committee with no usable leverage figure. Promoted from Medium because two personas caught it.
   - Fix: Give each ratio its period and a plain-language basis (for example "FY2024 net leverage of 5.55x, including the special dividend"), or move the qualification into the Basis line.
2. **High · visual** (Auditor, Saboteur)
   - Where: Line 50-51: "These are historical and illustrative measures, not price targets or stress recoveries." / "Basis: Fundamental credit synthesis (CP-2)"; shots/CP-3_key-findings.png, crop x340-1100 y220-790 (third bullet)
   - Problem: This is the only bullet with numbers (3.60x, 5.55x), and it is the only one with no Basis link on screen. The DOM goes straight from "stress recoveries." to the next <li>, so the Basis line in the handoff was dropped on the way to the page. A reader cannot trace the two ratios the finding depends on. Promoted from Medium because two personas caught it.
   - Fix: Show the Basis link under every bullet that has a Basis line in the handoff, the numeric one most of all, and have the fidelity check fail when a Basis line is lost.
3. **Medium · narrative** (Auditor)
   - Where: Line 50: "The fundamental synthesis carries approximately 3.60x"; line 52: "No active portfolio, position, risk budget or matched constraints table is identified. The supported output is generic monitoring logic"
   - Problem: The sentences name an internal module ("The fundamental synthesis carries") and use pipeline wording ("supported output", "matched constraints table", "identified"). That is a source reference and pipeline vocabulary inside narrative sentences, which the house standard reserves for Basis lines.
   - Fix: State the fact as the analyst's own finding ("FY2024 EBITDA covers net cash interest 3.6x") and leave the attribution to the Basis line.
4. **Medium · narrative** (Saboteur)
   - Where: Line 52: "**Portfolio action must remain an information-gathering posture.** No active portfolio, position, risk budget or matched constraints table is identified."
   - Problem: This finding is about the inputs the run lacked, not about TransDigm's credit, so it adds nothing to the issuer view. All four findings are also framed as what cannot be concluded. The reader gets no positive or negative credit judgement here, only absences, and that buries the actual view (cash-generative, equity-directed allocation).
   - Fix: Lead each finding with a judgement about the issuer or its instruments, and move the missing-input points to Limitations, where line 64 already makes the same point.
5. **Medium · narrative** (New reader)
   - Where: Line 48: "All four facilities remain in scope without a forced winner."; line 46: "Without verified collateral reach and dilution rules"
   - Problem: "The loans" and "all four facilities" are never named in this section, so a reader who has not seen the 10-K does not know which term loans are meant or when they mature. "Collateral reach", "dilution rules" and "forced winner" are jargon that is not explained.
   - Fix: Name the facilities (for example the term loan tranches and their maturities) and use plain terms for what is unverified (lien coverage, the capacity to add debt ranking alongside it).
6. **Low · narrative** (New reader)
   - Where: Line 52-53: "neither a starter allocation nor a core position nor an instruction to trim an assumed holding is justified." / "Basis: context, page 1"
   - Problem: The Basis is "context, page 1", which the Sources table describes as dated settings, not issuer evidence. That reference means nothing to a reader, and the triple negative is hard to parse.
   - Fix: Give the settings source a reader-facing label (for example "Run settings") and state the point positively ("no position sizing is recommended").
7. **Low · visual** (Auditor)
   - Where: shots/CP-3_key-findings.png, crop y220-790: "3.60x" and "5.55x" rendered as bold monospace buttons with dotted underline
   - Problem: Only these two numbers are styled as monospace buttons, which breaks the reading rhythm of the paragraph. The figures look like code tokens, and nothing on screen says what clicking them does.
   - Fix: Render numbers in the body font with a subtle affordance (for example a tooltip on hover) consistent with other numeric links.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 55-58 · verdict **BLOCK**

- Narrative: The passage is in the right place (after Key findings, before Limitations), but it gives its contrary evidence without numbers, names a module as its source inside the narrative, and lists what would change the view as jargon-heavy process steps with no measurable thresholds.
- Visual: The section has no chart. It is one dense prose block with a low-contrast Basis link, almost no spacing between the Limitations that follow and the Timeline, and a different text width from other prose sections on the page.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 56: "the issuer has realized cash generation, a disclosed hierarchy and dated security-level fair values ... The financial foundation also identifies limited immediate long-term scheduled principal."
   - Problem: The contrary evidence comes with no figures, units or periods: how much cash generation, which fair values at which date, how much principal falls due and by when. "Limited immediate long-term scheduled principal" also contradicts itself. A committee member cannot judge how strong the challenge to the withheld preference is.
   - Fix: Give each piece of contrary evidence with its exact value, unit and period, taken from the module's own figures (for example FY2024 free cash flow of USD 1,880 million, and the principal due in the next N years with its amount).
2. **High · narrative** (Auditor, New reader)
   - Where: line 56: "The financial foundation also identifies limited immediate long-term scheduled principal."
   - Problem: The sentence names an internal module ("The financial foundation") as its source. That puts the source reference in the narrative, which breaks the house rule that sources belong only in the Basis line. It also uses pipeline vocabulary that a reader who does not know the system cannot place.
   - Fix: State the fact directly (for example "Scheduled principal due before FY20XX is limited to USD X million") and leave the attribution to the Basis line.
3. **Medium · narrative** (Saboteur)
   - Where: line 56: "Evidence of retained debt repayment would strengthen conviction; another equity-directed debt increase or deterioration in cash conversion would raise the compensation required."
   - Problem: The triggers that would change the view have no thresholds: no spread or yield level, no leverage or cash-conversion level, no repayment size. The view could therefore never be shown to be wrong, and the committee gets no monitoring trigger it can act on.
   - Fix: Tie each trigger to a measurable threshold the module already has (for example net leverage above or below the 5.55x illustration, or a free-cash-flow conversion level), or state plainly that no threshold can be set and why.
4. **Medium · narrative** (New reader)
   - Where: line 56: "A matched-currency, matched-rank comparison with instrument-level price and yield or discount-margin inputs, followed by verified legal reach and a supported downside waterfall, would allow a genuine preference."
   - Problem: The sentence is dense with analyst jargon ("legal reach", "downside waterfall", "matched-rank", "withholding a preference") and is a list of process steps rather than a judgement about the credit. The section's 150 words sit in one 7-sentence paragraph that mixes contrary evidence with what would change the view.
   - Fix: Split the paragraph into two short blocks, contrary evidence and then what would change the view, written in plain language (for example "comparable bond prices and yields, and confirmation of the secured lenders' collateral claim").
5. **Medium · narrative** (Auditor)
   - Where: line 57 Basis: "Financial foundation (CP-1); Fundamental credit synthesis (CP-2)" (rendered in data-basis of the Basis button, render/CP-3.dom.html)
   - Problem: The Basis popup the reader opens shows the module codes CP-1 and CP-2. The house standard says no CP- code is shown on screen.
   - Fix: Show the reader-facing names only ("Financial foundation", "Fundamental credit") in the Basis content.
6. **Medium · visual** (Auditor, New reader)
   - Where: shots/CP-3_contrary-evidence.png, region x 330-1440, y 210-520 (crop tmp/CP-3-077-a.png) and the Limitations-to-Timeline join near y~760
   - Problem: The passage is one unbroken 11-line block with no paragraph break. The Basis link is small grey text with low contrast that is easy to miss. The section that follows ends with the Timeline heading placed directly under the last Limitations bullet with almost no gap, so this run of prose and the chart run together.
   - Fix: Break the block into the two sub-parts, give the Basis link enough contrast (at least 4.5:1), and put standard section spacing before the Timeline.
7. **Low · narrative** (Saboteur)
   - Where: line 56: "These facts could support a defensible investment once actual compensation and downside protection are established; they do not themselves establish..."
   - Problem: The judgement is hedged twice in one sentence ("could support ... once ... established; do not themselves establish"). The reader cannot tell whether the contrary evidence moves the view at all.
   - Fix: Open with a one-line judgement, for example "This evidence does not change the hold-off on a preference because...", and then give the reasons.
8. **Low · visual** (New reader)
   - Where: shots/CP-3_contrary-evidence.png, contrary-evidence text column (~540 px measure) against the full-width Request/Relative value/Portfolio Fit prose lower on the same page
   - Problem: The prose sections in this module use two different line lengths: a narrow reading column here and full-width lines further down the page. The page looks inconsistent and the full-width blocks are harder to read.
   - Fix: Use one reading measure for all prose sections on the module page.

### Analytical appendix — complete canonical registers (part 1 of 3: from 'Source gate, re-anchor and workflow disposition')

Kind: register appendix · handoff lines 104-206 · verdict **BLOCK**

- Narrative: The appendix reads as a workflow log rather than credit analysis: pipeline vocabulary in the visible heading and body, internal ids, operator instructions and no judgement-first opener all break the house reader standard, though values and limitations are kept exactly.
- Visual: The two definition tables lay out cleanly, but the Source register is clipped at the right, its Source column collapses into an unreadable character-wide strip, and per-row Basis chips add noise. Only one screenshot (to the top of the scorecard) was available, so the tables from line 140 onward (T3.3 to T3.9) were judged from the handoff text only.

1. **High · narrative** (Auditor, New reader)
   - Where: L106 heading "Source gate, re-anchor and workflow disposition"; L108 "Fundamentals clear the module gate ... The legal producer is Blocked ... Generic Portfolio-Fit Logic"; L123 "carrying amount is the canonical stack input"; L137 "Accepted Blocked upstream ... Failed executed-document gate"
   - Problem: Banned pipeline vocabulary (gate, re-anchor, producer, canonical, upstream, execution mode, phase) reaches the screen, in a section heading the reader sees in the page outline (screenshot left nav and body top). A credit committee reader cannot tell that "legal producer is Blocked" means the covenant review could not be done for lack of executed documents.
   - Fix: Rename the heading to something like "Scope and data gaps" and rewrite these passages in reader terms, e.g. "executed credit agreements and indentures were not available, so protection and recovery are not assessed".
2. **High · visual** (Auditor, Saboteur)
   - Where: Source register table, CP-3_s-106.png, x≈1240–1440, y≈1240–2270 (crop CP-3-083-a.png)
   - Problem: The table is wider than the content column: the Source column is clipped at the right edge, so the 10-K filename wraps one or two characters per line ("TD / 30 / K_( / 00 / 20 / pa") over about 20 lines, and the page references can't be read. The headers are raw snake_case field names (source_document_id, data_supplied, downstream_use).
   - Fix: Fit the register to the column width (fewer columns, or the Source column shortened to "10-K FY2024, pp. 58–60, 144–145, 172–173"), use sentence-case headers, and keep every column visible without clipping.
3. **Medium · narrative** (New reader, Saboteur)
   - Where: L110 "cannot be resolved or opened in this transport: the only source tools expose the six pinned sources ... Obtain enterprise access for the factual market-data predecessor; do not request freshness confirmation or a copied development export."
   - Problem: This passage is a set of operator instructions about tooling and connectors, not a reader finding. The point the reader needs (no market prices or peer data were available, so relative value cannot be judged) is buried in the middle of it.
   - Fix: Lead with the one-sentence consequence for the credit view (no quotes or peer data, so every security is Unclear on relative value) and drop the tooling and connector instructions.
4. **Medium · narrative** (New reader, Auditor)
   - Where: L118 "Carrying debt, C13 ... distinct from C01 gross principal"; L122 "new calculation RV-C03 difference USD 188 million"; L132–138 ids "K24", "UP0", "UP1A", "UP4", "CTX"
   - Problem: Internal register ids (C01, C13, RV-C03, K24, UP0–UP4, CTX) are shown on screen as monospace chips with no definition, and "CTX | context | Configuration, not issuer evidence" exposes run configuration as if it were a source.
   - Fix: Replace the ids with plain labels (e.g. "Gross principal", "Carrying debt", "FY2024 10-K") and drop the configuration row from a reader-facing source list.
5. **Medium · narrative** (Saboteur)
   - Where: L108 "Capital-Structure RV is the appropriate execution mode for an issuer-level request covering loans and bonds." (section opener)
   - Problem: The section opens with how the workflow ran, not a judgement. The reader has to get through three paragraphs and two tables before seeing that nothing could be ranked or priced, which is the only credit-relevant outcome of this appendix.
   - Fix: Open the appendix with a one-line bottom line, e.g. "All 13 securities are Unclear / Requires More Work because market prices and executed legal terms are absent", then the registers.
6. **Medium · visual** (New reader)
   - Where: Both definition tables and the source register, CP-3_s-106.png: row labels "Leverage Basis", "Debt basis divergence Basis", "K24 Basis" (y≈425–1830)
   - Problem: Every row label carries a grey "Basis" chip that has no visible meaning in a table, which already has a Source column. It reads like part of the label ("Leverage Basis") and adds noise to every row.
   - Fix: Remove the per-row Basis chip in tables whose Source column already carries the reference, or make it a clearly marked link.
7. **Low · narrative** (Saboteur)
   - Where: L118 "FY2024 USD 24880 million; FY2023 USD 19750 million" vs L122 "carrying debt USD 24,880 million"
   - Problem: The same figure is printed with and without a thousands separator in adjacent tables. This looks like two different numbers on a quick read.
   - Fix: Use one number format (USD 24,880 million) throughout the page, quoted values included.
8. **Low · narrative** (New reader)
   - Where: L116 "Addressed; positive common annual denominator; gross principal includes term loans..."; L112 "No separate upstream register titled Definition Conflict Register was supplied."
   - Problem: "Verbatim upstream statement" cells and the opening sentence about a missing register are workflow bookkeeping. "Addressed; positive common annual denominator" means nothing to a portfolio manager.
   - Fix: State the definition plainly (gross leverage = gross principal of term loans, notes, advances, leases and securitization over EBITDA As Defined) and drop the note about the missing register.

### Analytical appendix — complete canonical registers (part 2 of 3: from 'T3.10 — RV gaps ledger')

Kind: register appendix · handoff lines 207-303 · verdict **CONCERNS**

- Narrative: The register content checks out: secured 19,534, subordinated 4,581, total 24,880 and term-loan principal 8,702 all reconcile. However, the reader meets pipeline vocabulary (producer, gate, handoff, predecessor, a .py filename), snake_case headers, undefined abbreviations, and the bottom line (total debt; no instrument preferred) placed after the tables.
- Visual: This section has no chart, map or timeline. The screenshot shows only the RV gaps ledger, the source register and the top of the capital structure dashboard; the remaining tables, from the Instrument matrix onward, were checked only in the handoff and the rendered DOM text. In the visible part, the wide tables are clipped at the right edge (Source, Fixed/Floating, Source Trace) with no scroll cue, Source cells wrap repeated .jsonl filenames into tall ribbons, and every row carries an unexplained \"Basis\" chip.

1. **High · narrative** (Auditor, Saboteur)
   - Where: L222 "Accepted Blocked producer | ... | Executed-document gate failure"; L274 "Executed-document gate failed"; L221 "T3.5–T3.7 in this handoff" (rendered "in this handoff"); L284 "Recovery_waterfall.py was not run: unavailable"; L211 "Enterprise market-data predecessor"; L257 "legal gate"
   - Problem: The reader sees pipeline language: producer, gate, handoff, predecessor, and a script filename. The rendered DOM confirms this text is on screen. A committee member cannot tell whether "gate failed" means a legal defect at TransDigm or a missing input to the workflow, and that distinction decides how much weight the secured label carries.
   - Fix: Say it in reader terms, e.g. "executed credit agreement and indentures were not available, so legal protection is unassessed", and drop the script name and the stage words.
2. **High · visual** (Auditor, New reader)
   - Where: Instrument phase source register and Capital structure dashboard tables, shots/CP-3_s-207.png, right edge x≈1330–1395 (original px), y≈620–2300
   - Problem: Both tables are wider than the content column and are cut off at the right edge. The Source column shows only "TDG_ 30_1 K_00", Fixed/Floating shows only "Floa"/"Fixe", and in the dashboard the Source Trace and Source columns are not visible at all. There is no visible scroll cue, so the reader loses the source and the rate type without knowing it.
   - Fix: Fit the tables to the column (fewer or merged columns, or a stacked layout per instrument) or show a clear horizontal-scroll affordance, so every column is visible or obviously reachable.
3. **Medium · narrative** (Saboteur)
   - Where: L232 "Tranche I | ... | Not supplied: carrying allocation; not additive to aggregate | ... | Gross principal USD 1,871 million only" (same pattern L233–235)
   - Problem: In the visible Amount column each tranche reads "Not supplied", while the tranche principal (1,871 / 3,632 / 1,699 / 1,500 million) sits only in the clipped Source Trace column. A skimming reader concludes the tranche sizes are unknown, but the filing gives them.
   - Fix: Show the gross principal in the Amount column, labelled as principal, and keep the note on carrying-value allocation as a qualifier.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: L302 "No Preferred, Secondary or Avoid tier is assigned... Preferred: none established. Key Gaps: compensation, legal reach and recovery inputs."; L250 "Total carrying debt is USD 24,880 million."
   - Problem: The section's two decision-relevant facts come after the tables they summarise. The total carrying debt figure appears only below a 17-row, 12-column table, and "no instrument preferred" appears only after nine registers. The judgement does not come first. (Arithmetic checks: 19,534 + 4,581 + 486 + 262 + 17 = 24,880.)
   - Fix: Open the register part with a one-line bottom line (total debt, the secured/subordinated split, no instrument preferred and why), then the tables.
5. **Medium · narrative** (New reader, Auditor)
   - Where: L218 headers "source_document_id | source_document_name | source_quality | ... | downstream_use"; L211–214 "RV", "LGD", "FIGI"; L245 "RCF"; L255 "DM"; L258 "FV", "Level 1"; L248 "Local CMC exposure"; L270 "LME"
   - Problem: The column headers are snake_case field names. Abbreviations (RV, DM, LGD, EV, FV, LME, RCF, CMC, FIGI) and accounting terms (Level 1) are never defined in this section. Row IDs such as K24-STRUCT, INTERNAL-RV, UP-LEGAL and SUB-EVENT are internal labels.
   - Fix: Use plain-English headers, spell out each abbreviation on first use (or give a glossary on the page), and replace the internal row IDs with document names.
6. **Medium · visual** (Auditor, New reader)
   - Where: Source cells, e.g. L236 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 58–59; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145"; shot rows y≈660–1250
   - Problem: Each Source cell repeats the same long .jsonl file name twice. In a narrow column it wraps into a 12-line ribbon that stretches every row and pushes the dashboard off the screen. The .jsonl extension is a pipeline artifact, not a document a reader recognises.
   - Fix: Cite the document once by a reader name ("FY2024 10-K, pp. 58–59, 145") and merge the page ranges in one reference.
7. **Low · narrative** (Saboteur)
   - Where: L225 "no legal/recovery/refinancing overlay from those producers is invented"; L250 "No claim is made that the unranked obligations are pari passu"; L284 "no recovery-based ranking is authored"
   - Problem: Defensive phrasing written for an auditor of the model ("invented", "authored", "no claim is made") replaces a plain statement of what is unknown. This dilutes the register's tone for a credit reader.
   - Fix: State the gap directly, e.g. "Ranking of the securitization, leases and advances against the bonds is unknown."
8. **Low · visual** (New reader)
   - Where: First column of every table, e.g. "RV-G1 Basis", "Tranche I Basis", "K24-STRUCT Basis"; shot y≈250–1830
   - Problem: Every row's first cell carries a grey "Basis" chip (43 in this section). The chip is unexplained and adds noise next to the row label. Its target is not apparent from the page.
   - Fix: Give the chip a self-explaining label or tooltip, or show it only where a row has a distinct basis.

### Analytical appendix — complete canonical registers (part 3 of 3: from 'T3B.10 — Instrument monitoring triggers')

Kind: register appendix · handoff lines 304-403 · verdict **CONCERNS**

- Narrative: This is a register appendix, so the bottom-line-first order applies only lightly. Even so, the registers let pipeline words (producer, gate, predecessor, handoff) and broken trigger IDs reach the reader, leave codes undefined, and bury the one judgement (no position can be sized) under rows that only say 'not supplied'.
- Visual: There is no chart; the section is a run of wide tables that read cleanly at the top but crowd at 8–9 columns, wrap cells to one word a line, run one Source cell into the border, and repeat a 'Basis' chip in every row. The screenshot covers only T3B.10 to T3C.4, so the later tables were judged from the DOM text alone.

1. **High · narrative** (Auditor, New reader)
   - Where: L354 "PF3 Priority uncertainty | Blocked legal producer"; L384 "Legal gate failed"; L320 "Recovery evidence predecessor after legal gate"; L319 "Complete CP-4 documentary predecessor"; L327 "in this handoff" (all confirmed in render/CP-3.dom.html)
   - Problem: Pipeline words the house standard bans (producer, gate, predecessor, handoff) reach the reader in the cells, so a committee member reads 'Blocked legal producer' with no idea that it means the legal covenant analysis could not be completed.
   - Fix: Rewrite those cells in plain reader language, e.g. 'Legal covenant analysis incomplete: guarantees and collateral not verified'.
2. **High · narrative** (Auditor, Saboteur)
   - Where: L390–393 "CP-3B-MON-001 … CP-3B-MON-004" rendered as "Security selection-MON-001"; L399–401 "All executable sizing and MON-003" while gap IDs render as "Gap 1" (render/CP-3.dom.html)
   - Problem: The module-code substitution leaves broken IDs ('Security selection-MON-001'), and the gaps ledger still cites 'MON-003' while the trigger it points to is shown under a different label. The reader cannot follow the cross-reference.
   - Fix: Give triggers and gaps short, stable reader IDs (e.g. 'Trigger 3') and use the same ID wherever they are cited.
3. **Medium · narrative** (New reader)
   - Where: L334 "Portfolio phase status: Completed with Limitations. Output mode: Generic Portfolio-Fit Logic. … No separate intermediate export is required."; L346 "T3C.1; QA confidence calculation"
   - Problem: The note describes the run's own state (phase status, output mode, export) instead of saying what the missing mandate data means for a position, and 'QA confidence calculation' cites an internal step as evidence.
   - Fix: Replace it with one judgement sentence (no mandate or holdings were supplied, so no position size can be set) and drop the export and status wording.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: L308 "F3, F5; T3B.4"; L352 "PF1 Allocation-sensitive buffer … F3, F4"; L318 "INST-G1 … ICA"; L398–402 eleven columns of codes
   - Problem: Codes such as F1–F5, PF1–PF3 and INST-G1–G4, and the abbreviation ICA, are never defined in this section, so the tables can only be read with another page open. The two gap ledgers (instrument gaps and portfolio gaps) also overlap without explanation.
   - Fix: Expand codes to short names at first use (e.g. 'Finding 3: debt-funded payouts') and define ICA, or link each code to its definition.
5. **Medium · narrative** (Saboteur)
   - Where: L360–366 T3C.5, seven rows of "Not supplied | Not calculable … | Not supplied | Not Provided"; L381 "Not calculable: inputs not supplied"
   - Problem: Whole tables of 'not supplied' rows bury the one usable judgement, that no position can be sized or added until mandate, holdings and quotes arrive. The repetition reads as analysis but carries no information.
   - Fix: Collapse the empty concentration and liquidity rows into one stated gap and keep only the rows that carry a directional view.
6. **Medium · visual** (New reader, Auditor)
   - Where: shots/CP-3_s-304.png, Position sizing posture table (approx. y 1740–1980 at original scale) and Risk budget flags; crop tmp/CP-3-085-a.png
   - Problem: The 9-column tables squeeze cells to one or two words a line ('Key Risk' runs to 9 lines), and the Source cell text '(Legal & covenants)' runs into the table's right border.
   - Fix: Cut or merge columns (Source Trace with Source, Evidence with Reason) so each table fits the content width without wrapping words one per line or touching the border.
7. **Low · visual** (Auditor)
   - Where: shots/CP-3_s-304.png, every first-column cell (e.g. 'Senior claim dilution Basis', 'INST-G1 Basis')
   - Problem: Each row label carries a grey 'Basis' chip that crowds the label and wraps it to another line. Together with the table's own Source/Evidence ID columns, the row shows its source twice.
   - Fix: Show the Basis link once per table, or as an icon, rather than as an extra word in every row label.

### Calculations

Kind: prose/table · handoff lines 428-452 · verdict **BLOCK**

- Narrative: The section is a working-paper audit trail, not reader prose. Its first sentence is about tooling, the confidence score that drives the module's restricted stance is buried in kernel traces, and pipeline vocabulary and file codes appear on screen.
- Visual: There is no chart. The two tables lay out cleanly with readable contrast, but the narrow ID column wraps RV-Q IDs, ID typography is inconsistent, Basis chips are inconsistent between rows, and raw file-name sources inflate row height.

1. **High · narrative** (Auditor, New reader)
   - Where: L438 "QA claim census; supplied CP_CONFIDENCE_SCORE.md"; L430 "Every new arithmetic operation used the Decimal-38 kernel... Upstream figures are retained"; L441 "Partial source gate 0.7... qa_status Restricted"; L440 "with sum/ratio kernel"
   - Problem: Pipeline vocabulary reaches the reader on screen: a CP_ file name, 'kernel', 'gate', 'upstream', 'qa_status' and 'QA census'. The house standard forbids module codes and pipeline language. The section's opening sentence describes the tooling rather than the credit.
   - Fix: Remove the tooling and file references and state in plain words what each figure is and where it comes from, e.g. 'house confidence formula'.
2. **High · narrative** (Saboteur, New reader)
   - Where: L440-441 "sum(60,60,60,60,60,60)=360; ratio(360,10)=36 ... sum(56,56,56,56,56,56,56)=392; ratio(392,10)=39.2; sum(39.2,-15)=24.2"
   - Problem: The confidence score of 24/100 ('Insufficient Information', Restricted) is the module's most decision-relevant output. It sits in row RV-Q04, written as repeated-addition kernel traces that hide 0.6E + 0.4C, times 0.7, minus 15. A committee member cannot check it or see that it means no recommendation can be made.
   - Fix: Show the formula in ordinary notation (0.6×60 + 0.4×50 = 56; ×0.7 = 39.2; −15 = 24) and state the score and its meaning once, in a plain line above the table.
3. **Medium · narrative** (Saboteur)
   - Where: L437 "sum(19534, 4581, 486, 17, 262) | USD 24,880 million | Reconciles carrying bucket amounts and ancillary obligations"
   - Problem: Three of the reconciling inputs (486, 17, 262) are not named anywhere. The reader cannot tell which obligations make up USD 765 million of the carrying-debt total, so the reconciliation cannot be checked.
   - Fix: Name each ancillary item, with its amount, in the inputs or limitation cell.
4. **Medium · narrative** (New reader)
   - Where: L451 "Static distribution-adjusted net leverage | Approximately 5.55x | Same debt, specified cash settlement only; not actual October balance"
   - Problem: 'Same debt' and 'specified cash settlement' are undefined, and so is the EBITDA denominator. 'Approximately' is attached to a two-decimal figure. The reader cannot tell what the 5.55x leverage measures or how it differs from reported leverage.
   - Fix: Spell out the debt basis, the EBITDA basis, the date and the distribution adjustment in the Definition cell.
5. **Medium · narrative** (New reader)
   - Where: L434 "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145"; L443-451 "Financial foundation (CP-1), C09"
   - Problem: The Source cells cite raw extraction file names (.htm.jsonl with an accession number) and internal row IDs (C01, C13, C2-03) instead of a document a reader can recognise. On screen they wrap to three or four lines and add nothing for the PM.
   - Fix: Cite as 'TDG FY2024 Form 10-K, p.145' and give the module name with a readable metric label, not internal row codes.
6. **Medium · visual** (Auditor)
   - Where: Calculations table, ID column, screenshot CP-3_s-428.png crop x350-1440 y300-1200 (tmp/CP-3-088-a.png)
   - Problem: The ID column is too narrow: RV-Q01 to RV-Q05 break across two lines as 'RV-' / 'Q01'. The RV-C IDs render 'C01' in small caps, so the same ID scheme looks different between rows. A 'Basis' chip appears under the RV-C rows only, which looks like missing content in the RV-Q rows.
   - Fix: Widen or no-wrap the ID column, use one typeface for IDs, and either show Basis in every row or explain why it is absent.
7. **Low · visual** (Saboteur)
   - Where: Calculations table, columns 'Operation and complete inputs' / 'Result', screenshot CP-3_s-428.png y~690-1000 (display coordinates)
   - Problem: Long chained formulas in the RV-Q03/Q04 rows wrap into four-line cells, while the Result column stacks phrases like '24.2 before integer presentation; Confidence Score 24 /100'. The headline number does not stand out and has an odd space in '24 /100'.
   - Fix: Keep Result to the single value (24/100) and move the qualification to the limitation column.

### Gaps

Kind: prose/table · handoff lines 453-465 · verdict **BLOCK**

- Narrative: The Gaps table holds real decision gaps (market access, legal terms, tranche allocation, portfolio data), but it opens with no bottom line, is written in pipeline language and uses undefined abbreviations, and it mixes internal tooling rows in with the credit gaps.
- Visual: This is a four-column table with no chart. It renders cleanly with no clipping or overlap, but the Basis chips appear on some rows and not others, and raw filenames and doubled module names make the Source column tall and noisy.

1. **High · narrative** (Auditor, New reader)
   - Where: L458 "Legal producer Blocked / MATERIAL for dependent selection"; L462 "Recovery and refinancing producers not supplied / dependent"; L463 "name CP-3 as consumer and factual predecessors, not a self-dependency" (rendered as 'Security selection as consumer')
   - Problem: The table is written in pipeline vocabulary that the house standard bans: "producer", "consumer", "predecessor" (in every row of column 3 and in its header), "self-dependency", "companion" and "transport acceptance". A portfolio manager cannot tell what is actually missing, or who has to supply it.
   - Fix: Name each gap in reader terms (e.g. 'executed credit agreement and intercreditor not reviewed') and say who supplies it in plain language, with no pipeline roles.
2. **High · narrative** (Saboteur, New reader)
   - Where: L463-464 "Research routing companion absent / procedural ... No prescribed-format control brief or adoption table fabricated" and "Companions/scripts unavailable / procedural | No analytical conclusion changes solely because tooling is absent"
   - Problem: Two of the eight rows describe the pipeline's own tooling, not credit gaps. They sit alongside real decision gaps with equal weight, which dilutes the market-access and legal gaps that actually stop a preference.
   - Fix: Drop the procedural tooling rows from the reader table and keep only gaps that change a credit or security decision.
3. **Medium · narrative** (Saboteur)
   - Where: L455-457 header "Gap / severity" and "Market access / MATERIAL | RV and preference remain Unclear / Requires More Work; no switch, curve ranking or executable action"
   - Problem: The section opens straight into a dense table with no bottom line. The reader is never told that security preference and sizing are withheld until market and legal evidence arrive, or that the fundamental view stands. Severity labels (MATERIAL / bounded / dependent / procedural) are internal and not ranked.
   - Fix: Open with one judgement-first sentence on which gaps block a preference and which do not, then order the rows by decision impact using plain severity words.
4. **Medium · narrative** (Auditor, New reader)
   - Where: L460 Source "context, page 1"; L457 "Source/tool inventory; context, page 1"; L464 "Supplied method and tool inventory"
   - Problem: Several Source cells cite internal run artifacts ("context, page 1", "supplied method", "tool inventory") that the reader cannot open or identify. They fail the purpose of a Source column.
   - Fix: Cite a reader-identifiable document (filing, page) or state 'No source document: analyst scope note'.
5. **Medium · narrative** (New reader)
   - Where: L457 "RV ... Sector RV ... Index Statistics and Sector Ratings Average"; L458 "ICA"; L459 "I/J/K/L net carrying amounts"; L462 "EV-based loss/fulcrum or specialized LME overlay"
   - Problem: RV, ICA, EV, LME and the term-loan tranche letters I/J/K/L are never defined, and 'Sector RV' and 'Index Statistics' read as internal tool names. A committee member who has not read the sources cannot decode the requests.
   - Fix: Spell out each abbreviation on first use (relative value, intercreditor agreement, enterprise value, liability management exercise) and name the tranches as Term Loans I-L.
6. **Medium · visual** (Auditor)
   - Where: Gaps table, shots/CP-3_s-453.png crop y~1300-2160 (tmp/CP-3-089-a.png): 'Basis' chips in the Gap / severity column
   - Problem: Five rows (Market access, Loan carrying, Scoring governance, Portfolio and liquidity, Research routing) carry a 'Basis' chip and three do not, with no visible logic. The chip sits inline after the severity word, where it reads as part of the label ("MATERIAL Basis", "bounded Basis").
   - Fix: Either give every row a Basis affordance or none, and set it apart from the severity text, e.g. as its own icon or column.
7. **Low · visual** (Saboteur, Auditor)
   - Where: Gaps table Source column, rows 2 and 6 in tmp/CP-3-089-a.png: "Legal Covenant Interpreter (Legal & covenants)" and "Fundamental credit synthesis (Fundamental credit)"; row 3: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 59 and 145"
   - Problem: Module names show twice in two different forms (an internal agent name plus the display name). The raw filename with a .jsonl extension breaks over five lines and makes the narrow Source column the tallest cell in its row.
   - Fix: Show one display name per module and a short document label (e.g. 'FY2024 10-K, pp. 59, 145').

### Front matter + Request + Next module

Kind: run plumbing · handoff lines 1-18, 19-21, 466-470 · verdict **BLOCK**

- Narrative: This section is run plumbing: raw YAML metadata, model-instruction wording and routing text, including a code substitution that renders \"Security selection or Security selection\". All of it reaches the reader with pipeline vocabulary the house standard bars, and it carries no reader judgement except one buried sentence (withhold preference and sizing).
- Visual: The section has no chart, map or timeline. What is visible is an unformatted key:value paragraph (Front matter) and two dense paragraphs (Next module), placed among the reader sections and listed in the page navigation.

1. **High · narrative** (New reader, Auditor)
   - Where: line 470: "rerun CP-3 using those accepted inputs; a separate CP-3A or CP-3B run is not required". In the rendered page (CP-3_s-466.png, bottom) this reads "a separate Security selection or Security selection run is not required"
   - Problem: When module codes are swapped for display names, CP-3A and CP-3B both become "Security selection", so the rendered sentence is nonsense (I confirmed this in render/CP-3.dom.html). The paragraph is also pipeline instruction, not credit text: "rerun", "accepted inputs", "No answer from the user is assumed during this run", "absent acceptance receipt".
   - Fix: Leave this routing paragraph off the reader page, or reduce it to one plain sentence on what evidence would complete the decision. Code-to-name substitution must never produce two identical names in one phrase.
2. **High · narrative** (Auditor, New reader)
   - Where: lines 2-16: "module_id: CP-3 ... run_id: tdg-2024-09-30-credit_snapshot-sol-medium ... method_version: deploy-v-r14 ... qa_status: Restricted confidence_score: 24"
   - Problem: The raw YAML front matter is printed to the reader as a block of snake_case keys: module_id, qa_status, method_version, execution_mode and filename. That is pipeline vocabulary the house standard bars from the page, and a portfolio manager cannot read it.
   - Fix: Hide the front matter, or show only reader-meaningful status (as-of date, period, confidence 24/100 with its band) as labelled chips in plain words.
3. **Medium · narrative** (Saboteur)
   - Where: line 7: "run_id: tdg-2024-09-30-credit_snapshot-sol-medium", with the page header showing "TDG-READER-FORMAT-001" (CP-3_s-1.png, top bar)
   - Problem: Two different run identifiers appear on the same screen. A reader checking provenance cannot tell which run this module belongs to.
   - Fix: Show one run identity, the one in the library header, and drop the internal run_id from the visible page.
4. **Medium · narrative** (Saboteur)
   - Where: lines 11-15: "module_status: Ready with Limitations committee_status: Requires More Work qa_status: Restricted confidence_score: 24 confidence_band: Insufficient Information"
   - Problem: Five overlapping status labels sit side by side and pull in different directions: Ready, Requires More Work, Restricted and Insufficient Information. No single judgement reaches the committee, and "Ready" could be read as clearance.
   - Fix: State one reader status, for example "Not ready for a security decision; confidence 24/100 (insufficient information)", tied to the bottom line.
5. **Medium · narrative** (Saboteur, New reader)
   - Where: line 468: "Pass this restricted handoff to Evidence validation (CP-5), then Committee challenge (CP-6) in the selected plan. The defensible committee action is to withhold security preference and sizing"
   - Problem: The one committee judgement in this section (withhold preference and sizing) comes second, behind a routing instruction that uses the barred word "handoff". The section ends on internal workflow instead of the credit view.
   - Fix: Lead with the committee action in plain words and drop the routing to other modules.
6. **Medium · visual** (Auditor, New reader)
   - Where: CP-3_s-1.png, Front matter block (top of content, about y 190-260 displayed) and the "On this page" list placing Front matter / Request after Timeline
   - Problem: Front matter appears as an unbroken, justified paragraph of key:value pairs with no separators. It sits in the middle of the reading order, after the analysis sections and before Sources, and is listed in the navigation as if it were reader content.
   - Fix: Remove Front matter, Request and Next module from the visible page and its navigation, or show status as compact chips at the top of the module.
7. **Low · narrative** (New reader)
   - Where: line 20: "TransDigm Group Incorporated, as of 2024-09-30; pathway: credit_snapshot. Assess relative value, security selection, instrument preference and portfolio implementation"
   - Problem: The Request shows the internal token "pathway: credit_snapshot" and is written as an instruction to the model ("Assess ..."), not as a statement to the reader of what the section covers.
   - Fix: Say "Credit snapshot" in plain words and phrase the request as the question this module answers.
8. **Low · visual** (Auditor)
   - Where: CP-3_s-466.png, Next module block (bottom, about y 1815-1945 displayed)
   - Problem: Next module is two dense justified paragraphs set directly below a wide Gaps table, with no visual break. It ends the module on plumbing text at the same weight as the analysis.
   - Fix: If kept, show it as a short muted note visually separated from the analysis.

### Limitations

Kind: reader passage · handoff lines 59-66 · verdict **BLOCK**

- Narrative: The three bullets are hedged and use internal scoring and portfolio jargon. They leave out the two gaps the module itself rates as material (no market data, legal review blocked), and two of them cite an internal settings file as their basis.
- Visual: The section is a plain bulleted list with no chart of its own. It runs into the Timeline heading with almost no gap and wraps narrower than the paragraphs below it.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Line 60: "The security comparison cannot determine the price of moving between secured and subordinated claims or between loan maturities." (Limitations, lines 59-65)
   - Problem: The Limitations list leaves out both gaps the module's own Gaps table marks MATERIAL: market data was not accessible (line 457, also line 68, "The maintained Sector RV source was not accessible") and the legal review was blocked, so collateral reach and recoveries are unverified (line 458). A committee member who reads only this section sees a missing price but not why, and is never told that the secured-versus-subordinated protection is legally unverified.
   - Fix: Give each material gap its own limitation bullet, saying what is missing (market prices or comparables, executed legal documents) and which conclusion it restricts.
2. **Medium · narrative** (New reader)
   - Where: Line 64: "No portfolio-identity-matched constraint observation supports implementation."; line 62: "No governing factor weights or sector-specific scoring anchors ... the composite, normalized score and credit tier are withheld"
   - Problem: These are internal scoring and workflow terms. A portfolio manager cannot tell what a "portfolio-identity-matched constraint observation" or a "scoring anchor" is, or which score is being withheld.
   - Fix: Use plain terms, for example "no portfolio mandate, holdings or limits were supplied" and "no weighting method exists to combine the factors into a single score".
3. **Medium · narrative** (New reader, Auditor)
   - Where: Line 63 and line 65: "Basis: context, page 1"
   - Problem: Two of the three limitations cite "context". The module's own Sources table (line 27) describes that file as "Dated settings only, not issuer evidence". It is an internal file the reader cannot open, so the reader has nothing to check these limitations against.
   - Fix: Point the Basis line at a source the reader can open or name, or state that the input was not supplied, rather than citing an internal settings file.
4. **Medium · narrative** (Saboteur)
   - Where: Line 62: "the composite, normalized score and credit tier are withheld rather than created through equal weighting" vs front matter on the same page (line 14): "confidence_score: 24"
   - Problem: The Limitations section says no score was produced. A few lines further down, the page shows a bare score of 24 with no unit or scale. A reader can take that 24 for the credit score this limitation says was withheld.
   - Fix: In the limitation, say that no credit score was produced and that any confidence figure shown elsewhere measures how complete the evidence is, not credit quality.
5. **Medium · visual** (Auditor)
   - Where: CP-3_limitations.png, region x 330-1440, y 200-560 (crop CP-3-078-a.png): last bullet's "Basis" link directly above the "Timeline" heading
   - Problem: There is almost no vertical space between the third bullet and the "Timeline" heading, so the timeline looks like part of the Limitations block. Every other section break on the page has a visible gap.
   - Fix: Use the same spacing between sections as elsewhere on the page (about one heading-height of space) after the last Limitations bullet.
6. **Low · narrative** (New reader)
   - Where: Line 64: "This prevents a numeric position, a capacity test or a portfolio-specific add or trim instruction even if subsequent security research establishes value."
   - Problem: This repeats Key finding 4 (line 52, "neither a starter allocation nor a core position nor an instruction to trim an assumed holding is justified") almost word for word, which spends the reader's attention on a duplicate while the material gaps go unstated.
   - Fix: Cut it to one short line or merge it into the portfolio-inputs limitation, and use the space for the missing material gaps.
7. **Low · visual** (New reader)
   - Where: CP-3_limitations.png, Limitations bullets (about x 300-830 at displayed scale) vs the Relative value and Portfolio Fit paragraphs below (full width to about x 1150)
   - Problem: The Limitations bullets wrap at about 60% of the width used by the prose sections below, leaving a large empty band on the right. The line widths on one module page do not match.
   - Fix: Use one text width for bullets and paragraphs within a module page.

### Relative value

Kind: prose/table · handoff lines 67-70 · verdict **BLOCK**

- Narrative: The section opens with a verdict ("Unclear"), but it gives no figures, leans on process vocabulary ("source gate", "supplied tools") and points to material that is not below it, so a committee reader gets a refusal with no reasoning they can check.
- Visual: There is no chart; the section is a single dense full-width paragraph with a small grey Basis link. It sits in the page structure after Sources and Request, which hides the main relative-value verdict among the reference material.

1. **High · narrative** (Auditor, New reader)
   - Where: line 68: "The maintained Sector RV source was not accessible through the supplied tools; the single actual access gap and its consequences are recorded in the source gate, without questioning its presumed currency or relevance."
   - Problem: This sentence is written in pipeline language: "source gate", "supplied tools", "maintained Sector RV source" and "presumed currency or relevance" describe the run's own process, not the issuer. A committee reader learns nothing about TDG from it and cannot tell what "the source gate" is or where to find it. Both the house ban on pipeline vocabulary and the New-reader test flag it, so it is promoted to High.
   - Fix: Say in reader terms that no sector peer spread data was available, so TDG's loans and notes could not be compared with peers, and move the access detail to Limitations.
2. **Medium · narrative** (Saboteur)
   - Where: line 68: "Relative value is Unclear for every identified loan and note. Contractual margin is not discount margin, coupon is not yield, and fair value in the financial notes is not an executable price."
   - Problem: The bottom line is a non-judgement, and the section quotes none of the margins, coupons or dated fair values it lists, so the reader cannot see how far the evidence goes. The passage only says what cannot be concluded and never states a provisional lean, so the reader has nothing to weigh.
   - Fix: Start with a one-line judgement and the observable range it rests on (for example, coupon range and fair value as a percentage of par at 30 Sep 2024, each with its unit and date), then say what is missing.
3. **Medium · narrative** (New reader)
   - Where: line 68: "The dated accounting observations are retained below as contrary evidence to a claim that no valuation information exists"
   - Problem: "Retained below" points at nothing nearby. The next blocks are Portfolio Fit and a maturity table with no fair values; the fair-value data sits many sections further down (Relative value table). Framing the data as rebutting "a claim that no valuation information exists" argues with a claim the reader never saw.
   - Fix: Name the table and its heading that holds the dated fair values, and say plainly what they show and why they are not tradeable prices.
4. **Medium · visual** (Auditor, New reader)
   - Where: CP-3_s-67.png top (y≈180-290 in the 1200-px view); DOM: h4 'Relative value' (#s-67) comes after h3 'Sources' and 'Request' in the On this page list
   - Problem: The relative-value judgement is rendered as a subsection after the module's Sources and Request blocks. The reader meets the core security-selection verdict after the reference material, and the heading hierarchy makes it look like part of Sources. This breaks the house reading order, which puts the bottom line first and Sources last.
   - Fix: Show Relative value with the judgement passages (before Limitations or as part of the findings block) and keep Sources as the last reader block.
5. **Low · narrative** (Auditor)
   - Where: line 69: "Basis: ...pages 59–60; ...pages 172–173; context, page 1"
   - Problem: "context, page 1" is an internal input label, not a source a reader can identify or open, and it shows in the Basis popover next to real filing references.
   - Fix: Replace it with the named document the request supplied, or say plainly that it is the analyst's request.
6. **Low · visual** (New reader)
   - Where: CP-3_s-67.png, Relative value paragraph (y≈215-275 in the 1200-px view)
   - Problem: The section is one five-line paragraph set across the full ~860-px text column at small type, with about 170 characters per line. It is dense to read, and the heading case ("Relative value") does not match its neighbour ("Portfolio Fit").
   - Fix: Split the verdict sentence from the explanation, limit the measure to about 90 characters, and use one heading case throughout.

### Fundamental translation and time-aware downside

Kind: prose/table · handoff lines 97-103 · verdict **CONCERNS**

- Narrative: The two paragraphs open with what the analysis is not, carry no figures, use an undefined abbreviation (LME) and workflow language, and do not tell the reader which TDG security this favours.
- Visual: This section has no chart; it is two full-width prose blocks with very long lines and faint inline Basis links, and is hard to scan, though nothing is clipped or overlapping.

1. **High · narrative** (Saboteur, New reader)
   - Where: line 98: "Near-term scheduled long-term principal gives time rather than proof of refinancing access." and line 101: "persistent weakness then complicates refinancing of the later funding concentration"
   - Problem: The section's main credit claims (time before maturities, a later funding concentration) give no amount, date or currency. The reader cannot tell how much runway there is or which maturities make up the 2028-2029 cluster, even though the timeline directly above lists them. This was promoted because two personas raised it.
   - Fix: Anchor each claim to its figure: the near-term principal in USD millions with its period, and the dates and amount of the 2028-2029 maturity cluster.
2. **Medium · narrative** (Saboteur)
   - Where: line 98: "The fundamental profile is cash-generative but allocation-constrained, not a newly assigned formal rating." and line 101: "The downside sequence is conditional, not a numerical stress forecast."
   - Problem: Both paragraphs open by saying what the analysis is not. The judgement comes as a hedge, and no paragraph says what it means for security selection, for example whether to prefer senior secured over subordinated paper. The closing "Business resilience cannot establish either legal loss protection or adequate market compensation" further weakens the bottom line.
   - Fix: Open with a positive judgement on what the fundamentals imply for choosing between TDG's secured and subordinated instruments, then give the scope caveats as limitations.
3. **Medium · narrative** (New reader, Auditor)
   - Where: line 101: "The legal mechanism and severity of any priming remain unverified, so this is not an LME prediction."
   - Problem: "LME" is never spelled out anywhere on the rendered CP-3 page (the DOM has no "liability management"), and "priming" is unexplained jargon. A committee member cannot tell what is being ruled out.
   - Fix: Spell out liability management exercise at first use and say in plain words that new debt could rank ahead of existing lenders.
4. **Medium · narrative** (Auditor, New reader)
   - Where: line 98: "Earnings-definition sensitivity and the separation between reported and retained cash are carried from the fundamental synthesis without re-underwriting them."; heading line 97: "Fundamental translation"
   - Problem: This describes the workflow (what was "carried from" another module, "re-underwriting") rather than the issuer, and the heading "Fundamental translation" is internal method vocabulary. It tells the reader nothing about TDG's credit.
   - Fix: Either state the earnings-definition and cash-retention risks in issuer terms or move the provenance into the Basis line, and retitle the section in reader language, for example "What the fundamentals mean for each security and how a downturn would unfold".
5. **Medium · narrative** (Auditor)
   - Where: line 101: "Observe collections, inventory, cash after allocations, new secured funding and refinancing progress; escalate if cash conversion weakens while equity-directed uses continue."
   - Problem: The causal chain, the junior-debt severity point, the monitoring triggers and the limitation all sit in one roughly 140-word paragraph, mixing findings, what would change the view, and limitations against the house order. The triggers have no thresholds.
   - Fix: Split it into a findings paragraph, a short what-would-change-the-view paragraph with measurable thresholds, and a one-line limitation.
6. **Medium · visual** (New reader)
   - Where: shots/CP-3_s-97.png, region x 340-1440, y 210-470 (both paragraphs; crop tmp/CP-3-082-a.png)
   - Problem: Two dense prose blocks span the full content width at about 180-190 characters per line (paragraph 2 runs to 7 lines) with no emphasis, lead sentence or list, so the key judgement is not scannable.
   - Fix: Cap the prose measure at about 80-100 characters and bold or lift each paragraph's lead judgement so it stands out from the reasoning.
7. **Low · visual** (Auditor)
   - Where: shots/CP-3_s-97.png, y about 270 and 372 (grey inline "Basis" link after each paragraph)
   - Problem: The Basis reference is a small light-grey word run into the last line of text. Its contrast looks low, and it hides that paragraph 2 also cites a 10-K page.
   - Fix: Put Basis on its own line with readable contrast, showing the cited sources.

### Per-security conclusion and final synthesis

Kind: prose/table · handoff lines 404-410 · verdict **CONCERNS**

- Narrative: The conclusion itself is coherent (no recommendation until market, legal and portfolio evidence exist), but it is buried in status labels, repeated three times, and ends in a doubled pipeline status stamp.
- Visual: There is no chart in this section; it renders as three dense full-width paragraphs with no Basis links and no visual difference between the verdict and the status line.

1. **High · narrative** (Auditor, New reader)
   - Where: L409: "CP-3 Completed with Limitations. Recommendation: Requires More Work. RV: Unclear. Key Gaps: ... CP-3B Completed with Limitations. Sizing Posture: Requires More Work." Rendered (shot CP-3_s-404.png, y~370-415): "Security selection Completed with Limitations. ... Security selection Completed with Limitations. Sizing Posture..."
   - Problem: This is a pipeline status stamp printed as reader prose. The module codes are swapped for display names, so CP-3 and CP-3B both become "Security selection" and the sentence appears twice on screen. "Completed with Limitations" and "RV:" are internal status vocabulary, which breaks the house rule against pipeline wording.
   - Fix: Remove the module-completion status line from the reader page, or give the sizing posture as one plain sentence that is not repeated.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: L405: "Each security listed individually in T3.5 is Requires More Work because issuer fundamentals are cash-generative but allocation-constrained, while relative value is Unclear"
   - Problem: The verdict is a capitalised status label used as a predicate ("is Requires More Work", "is Not Scorable", "is Unclear"). It reads as form-filling rather than a judgement and hides the actual call, which is that no position should be taken until market and legal evidence arrive.
   - Fix: Open with a plain-language judgement such as "We cannot recommend any of the 13 TDG instruments yet, because ..." and keep the labels out of the sentences.
3. **Medium · narrative** (New reader, Auditor)
   - Where: L405: "Each security listed individually in T3.5" (rendered as "in “Relative value table”"); L405: "matched compensation"; L407: "weights and supported scoring anchors are absent"
   - Problem: The opening sentence sends the reader to another table to learn which securities are meant. "Matched compensation" and "scoring anchors" are method jargon that a PM who has not read the sources cannot decode.
   - Fix: Name the instrument groups inline and say "spread versus comparable issuers" and "no scoring framework was supplied" in plain words.
4. **Medium · narrative** (Saboteur)
   - Where: L407: "Overall, TransDigm's numeric credit tier is Not Scorable ... Relative value is Unclear ... Final security selection is Requires More Work"
   - Problem: The second paragraph restates the first paragraph's verdict and reasons almost word for word, and the third line restates them again. The same conclusion appears three times with no new information, which dilutes the one actionable point: what evidence would unlock a decision.
   - Fix: Merge the content into one conclusion paragraph followed by one sentence on what would change the view.
5. **Medium · visual** (New reader, Auditor)
   - Where: CP-3_s-404.png, region x 296-1160, y 190-415 (three passage-text paragraphs)
   - Problem: The section is three full-width paragraphs of about 150 characters per line. There is no Basis link on any of them (DOM s-404 has none, while the neighbouring QA table has one on every row), and the status line has the same styling as the analysis. The page's final conclusion therefore reads as a wall of text with no traceable basis.
   - Fix: Limit the line length, give the conclusion a visual callout or verdict chip, and attach a Basis line to each paragraph.
6. **Low · narrative** (Saboteur)
   - Where: L405: "The main downside is deteriorating cash conversion after equity-directed uses, with junior claims additionally exposed to the disclosed senior hierarchy."
   - Problem: The downside is stated with no magnitude, period or unit, such as the size of the senior stack ahead of the subordinated notes. The committee cannot tell whether the risk is material.
   - Fix: Anchor the downside to one quantified figure (for example, senior secured debt ahead of subordinated notes in USD millions at 2024-09-30), with that figure's source reference in the paragraph's Basis line.
7. **Low · visual** (Auditor)
   - Where: CP-3_s-404.png, the whole page and the left-hand "On this page" list
   - Problem: The module's synthesis sits after about 25 appendix registers and is followed directly by a QA Validation table of script names (prepare_invocation.py and others), so the reader meets the conclusion buried between internal registers and tooling diagnostics.
   - Fix: Show this synthesis with the Bottom line at the top of the module page and keep script diagnostics off the reader view.

### Portfolio Fit

Kind: prose/table · handoff lines 71-74 · verdict **CONCERNS**

- Narrative: The judgement (watchlist only, no sizing) does come first. It is wrapped in an internal status label and pipeline wording, though, and it presents missing liquidity data as a risk finding.
- Visual: This section is a single prose paragraph with no chart or table. Its layout is clean, but the line length is too long, the heading case does not match its siblings, and the Basis link is low-contrast.

1. **Medium · narrative** (New reader, Saboteur)
   - Where: line 72: "Overall, TransDigm is Requires More Work for portfolio implementation. Generic fit is watchlist and monitoring only"
   - Problem: The opening sentence drops the internal status label "Requires More Work" in as a predicate, which makes it ungrammatical, and "Generic fit" is a pipeline term ("Generic Portfolio-Fit Logic", line 106). A portfolio manager has to decode the labels before reaching the judgement, which is watch, do not size.
   - Fix: Open with the judgement in plain words, e.g. that TransDigm belongs on a watchlist with no position sized until named evidence arrives, and keep status labels out of the prose.
2. **Medium · narrative** (Saboteur)
   - Where: line 72: "but a portfolio allocation must also survive equity-directed cash use, a cash-conversion setback and uncertain exit liquidity"
   - Problem: "Uncertain exit liquidity" is stated as a risk the allocation must survive, but the module has no trading or liquidity evidence (line 34: no market observations acquired). An absence of data reads as a finding that the paper is illiquid.
   - Fix: Say that exit liquidity is unassessed because no trading data was available, rather than calling it uncertain.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 72: "are prerequisites to implementation rather than reasons to reopen the fundamental analysis."
   - Problem: The closing clause tells the workflow not to reopen an upstream module. It says nothing to the reader, so pipeline reasoning leaks into the narrative and the paragraph ends on process instead of on what would change the view.
   - Fix: End on the reader-facing trigger: which evidence would allow a sized position and in which direction.
4. **Low · narrative** (Auditor)
   - Where: line 73: "Basis: Fundamental credit synthesis (CP-2); context, page 1"
   - Problem: Half of the basis is "context", which line 27 describes as "Dated settings only, not issuer evidence". The watchlist judgement is presented as if a source supports it, when what supports it is the absence of portfolio inputs.
   - Fix: Cite only the evidence actually relied on, and state the missing portfolio inputs as a limitation, not as a source.
5. **Low · visual** (Auditor, New reader)
   - Where: Portfolio Fit heading and paragraph, shots/CP-3_s-71.png region x330-1440, y210-390 (crop tmp/CP-3-080-a.png)
   - Problem: The heading is in Title Case ("Portfolio Fit") while sibling headings and the side nav use sentence case ("Relative value", "Events: Instruments"). The paragraph also runs across the full content width at about 170 characters per line in small type, which is hard to track for a dense four-sentence judgement.
   - Fix: Use sentence case for the heading and cap the prose measure at roughly 90-110 characters so that it matches readable report text.
6. **Low · visual** (New reader)
   - Where: Trailing grey "Basis" link at end of paragraph, shots/CP-3_s-71.png around y=270 (displayed)
   - Problem: The basis appears only as a faint grey word with low contrast against white. The reader cannot see which sources back the portfolio judgement without interacting with it.
   - Fix: Render the Basis line with enough contrast and with its source names visible, or in an obvious expandable control.

## Evidence validation (CP-5)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001/requests/CP-5/2bd6b04939348b590ab9c3557eb4d4c1a37c55f6a2ad5035ce01c9807fac22df/1.response.md`

### Analytical appendix — complete canonical registers (part 2 of 2: from 'T5B.8 — Gaps ledger')

Kind: register appendix · handoff lines 200-296 · verdict **BLOCK**

- Narrative: This appendix is mostly pipeline-integrity bookkeeping, with module codes, pipeline vocabulary and a page reference inside a narrative sentence left in. Its few credit-relevant facts (debt basis USD 25,068m principal vs USD 24,880m carrying; static post-payment cash USD 1,913m) are buried in multi-figure rows.
- Visual: There is no chart in this section. Its visual is a stack of dense 7-8-column tables that wrap cells to 5-7 lines, with Basis chips placed inconsistently and a raw-Markdown header. The text is legible, but the tables read slowly. The screenshot covers only the Gaps ledger through the start of the Math audit; the later tables were judged from the rendered DOM.

1. **High · narrative** (Auditor, New reader)
   - Where: Input module register, line 219-220: "tdg_CP-4_20240930.md; tdg-2024-09-30-credit_snapshot-sol-medium" and "tdg_CP-3_20240930.md; ..."; also issue IDs "CP5-001"/"CP5-002" (lines 236-237, 261, 267, 292-298), rendered as-is (shot CP-5_s-200.png, y~1350-1500)
   - Problem: Module codes are printed on screen inside file names, and the CP5-00x issue IDs are built from the module code. Both break the no-module-code rule, and a reader cannot tell what "CP5-001" refers to without the issue log further down.
   - Fix: Replace the file and run identifiers with the module's reader name and run date, and give the two issues plain labels such as "Debt basis default" and "Security-selection confidence score".
2. **High · narrative** (Auditor, New reader)
   - Where: Line 213 header "Handoff canonical `.md` / run_id" … "Six transport headings present; accepted without additional receipt" (215); "re-anchor dependents" (236); "transported six-H2 format governs instead of legacy headings" (284); "Neither group enters the finding census" (295)
   - Problem: The Input module register and the envelope audit are written almost entirely in pipeline vocabulary: handoff, canonical, producer, transport, envelope, gate, re-anchor, qa_status, run_id. A portfolio manager gets no credit meaning from them.
   - Fix: Remove the pipeline-integrity registers (input register, envelope audit) from the reader page, or rewrite each row as what it means for confidence in the credit figures.
3. **High · narrative** (Auditor)
   - Where: Line 255: "The accounting valuation rows exist and were checked at pages 172–173; it would be incorrect to say the pack contains no valuation information."
   - Problem: A page reference sits inside a narrative sentence, which the house standard forbids. The sentence also argues with an unnamed critic instead of stating a finding.
   - Fix: Move "pages 172–173" to the paragraph's Basis line and state the finding directly: accounting fair values exist, but no executable market prices do.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 222 (rendered): "A missing separate Evidence validation artifact is resolved by the absorbed phase. No unsupplied Committee decision output is treated as an available input."
   - Problem: After codes are replaced with names, the module says its own output is missing and refers to a "Committee decision output". To a reader this is self-contradictory nonsense about process, not credit.
   - Fix: Delete process-sequencing sentences like this from the reader page.
5. **Medium · narrative** (Saboteur)
   - Where: Line 295: "There are no new CRITICAL or MINOR exceptions." against T5.7/T5.8 rows graded "MINOR" (lines 276, 284)
   - Problem: The same page shows two rows graded MINOR and then says there are no MINOR exceptions. The severity scale (CRITICAL/MATERIAL/MINOR) is never defined for the reader, so they cannot tell how much each grade should weigh.
   - Fix: Define the severity scale once, and do not grade rows that are "control record only" (or label them as not findings), so the counts match what is shown.
6. **Medium · narrative** (Saboteur)
   - Where: Gaps ledger, lines 204-209: "Medium impact" (Gap 1-2) … "High impact on trade clearance" (Gap 3-4) in the "Consequence for Confidence" column
   - Problem: The ledger is in ID order, not severity order, so the two High-impact gaps (legal provenance, market evidence), the ones that block trade clearance, sit beneath two Medium ones. The deciding constraint is buried mid-table.
   - Fix: Order the gaps by impact, High first, and say in one sentence above the table that legal and market evidence gaps block any trade, switch or sizing decision.
7. **Medium · visual** (New reader, Auditor)
   - Where: Input module register and Gaps ledger, shot CP-5_s-200.png, regions y~850-1570 and y~205-820 (display coordinates)
   - Problem: Seven- and eight-column tables at 1440 px squeeze cells into narrow columns that wrap to 5-7 lines (e.g. QA Status "Pre/post-audit Restricted; supplied score 24 requires census remediation"). The tables become tall walls that are slow to scan.
   - Fix: Cut each register to the 3-4 columns a reader needs (gap, why it matters, impact, follow-up) so cells fit in one or two lines.
8. **Low · visual** (Auditor)
   - Where: "Basis" chips in first columns, shot CP-5_s-200.png y~250-1500: "Gap 1 / Basis" stacked vs "Fundamental credit Basis" inline (y~1235); header shows literal backticks "`.md`" (y~873)
   - Problem: The Basis chip wraps inconsistently, sometimes on its own line and sometimes inline after the label, and raw Markdown backticks are drawn in a column header. Both look unfinished.
   - Fix: Put the Basis chip in a fixed position (e.g. a dedicated narrow column or a consistent line below the ID) and strip Markdown syntax from headers.

### Clearance decision

Kind: prose/table · handoff lines 306-310 · verdict **BLOCK**

- Narrative: The section reaches the right restrictive conclusion, but it leads with \"Pass\" and depends on internal issue codes and pipeline words (artifact, producer, re-audit), so a reader who has not seen the sources cannot tell what is restricted or why.
- Visual: This section has no chart, map or timeline. It renders as two unstyled text paragraphs: the decision line is in all caps and gets no status emphasis, and it runs straight into the dense QA Validation script table below it. Not verified: I did not compare it against the VMO2 reference screenshots.

1. **High · narrative** (New reader; Auditor)
   - Where: L309: "Supported retrospective historical findings may be discussed with CP5-001 and CP5-002 disclosed, but no full-run investment clearance is granted."
   - Problem: The passage names the two issues that restrict committee use only by internal issue codes built on the module code (CP5-xxx), and the rendered page shows them verbatim. A reader can only learn what has to be disclosed by finding the issue-log table in the appendix (the debt numerator uses principal rather than carrying value; the confidence score lacks a validated field census).
   - Fix: Name the two open issues in plain words and give their effect on the numbers, e.g. which debt figure and which confidence score cannot be relied on, with no internal IDs on screen.
2. **High · narrative** (Saboteur; New reader)
   - Where: L307: "CLEARANCE DECISION: Pass with Remediation. Critical Issues: 0. Material Issues: 2. Minor Issues: 0. Committee Use: Restricted."
   - Problem: The first word the reader meets is "Pass", but the next lines say committee use is restricted, no investment clearance is granted, and no trade or position size is authorised. A skimming committee member can take "Pass" as clearance. The decisive restriction comes last in a run of counters.
   - Fix: Lead with the restriction as the judgement (cleared for historical discussion only; not cleared for investment decisions) and put the pass/issue counts after it.
3. **High · narrative** (Auditor)
   - Where: L309: "neither acceptance of this artifact nor its grade authorizes contractual capacity... Producer correction and targeted re-audit are required for broader clearance."
   - Problem: "artifact", "Producer correction" and "re-audit" are pipeline vocabulary that the house standard bars from reader text. They describe the workflow and say nothing about the issuer, and they leave the reader unsure who has to do what.
   - Fix: Say in reader terms what must change (e.g. the debt figures restated on carrying value and the confidence score recomputed) before the view can be used more widely.
4. **Medium · narrative** (New reader)
   - Where: L309: "The prior legal block and withheld executable preference remain unchanged"
   - Problem: "prior legal block" and "withheld executable preference" are undefined here. The reader cannot tell that the first means legal/covenant capacity could not be assessed and the second means no preferred security or trade view was given without reading other modules.
   - Fix: State in one short clause what is blocked (covenant/legal capacity not assessable) and what is withheld (no preferred bond or trade recommendation).
5. **Medium · visual** (Saboteur; Auditor)
   - Where: Clearance decision block, shots/CP-5_s-306.png, region x330-1440, y210-350 (crop tmp/CP-5-102-a.png)
   - Problem: The decision is a plain body-text line in ALL CAPS that repeats the heading, and the 'Restricted' status gets no visual weight (no chip, bold or status styling). It looks like the routine prose around it and gives the reader no scannable status, so this section's verdict is easy to miss.
   - Fix: Show the outcome as a visually distinct status line or chip (e.g. 'Committee use: Restricted') under a sentence-case heading, without the repeated all-caps label.

### QA Validation

Kind: prose/table · handoff lines 311-336 · verdict **BLOCK**

- Narrative: The section is a pipeline self-audit, built from script names, transport checks, internal issue codes and an undefined E/C/S scoring formula, with no judgement-first lead; its only reader-relevant point (confidence 28, Insufficient Information, restricted use) is buried.
- Visual: The two tables render cleanly with readable spacing and no clipping, but every row has a Basis chip with empty data, and name substitution produced a duplicated 'Evidence validation/Evidence validation' label.

1. **High · narrative** (Auditor, New reader)
   - Where: L315-319 rows 'prepare_invocation.py | Not run: unavailable', 'validate_handoff.py ... Six required transport H2s appear once and in order; report selector appears once ... write_handoff is the transport submission checker'
   - Problem: The whole table is a pipeline self-audit of script names, Markdown transport headings, frontmatter and checker tooling. This breaks the house rule against pipeline vocabulary on screen, and a portfolio manager gets nothing out of it for a credit judgement.
   - Fix: Leave the script and transport checks out of the reader page, or reduce them to one reader-language limitation line, e.g. 'validation was manual; automated checks were not run'.
2. **High · narrative** (Auditor, Saboteur)
   - Where: L335 'Supplied arithmetic reproduces conceptually, but canonical C census fails CP5-002'; L326 'Band is Insufficient Information and qa_status Restricted'
   - Problem: An internal issue code (CP5-002, still visible on screen in the rendered table), the words 'canonical', 'producer-owned' and 'C census', and the field name qa_status all reach the reader. The one consequence that matters, that the security-selection confidence score cannot be relied on, is hidden behind those codes.
   - Fix: Name the issue in plain words, e.g. 'the confidence score's coverage measure is not validated', and drop the codes and field names.
3. **High · visual** (Auditor, Saboteur)
   - Where: QA Validation table and upstream score audit table, every row's 'Basis' chip (CP-5_s-311.png, y≈250-1180); DOM shows data-basis="[]" for prepare_invocation.py, confidence_score.py, Source readiness, Legal & covenants, Security selection, etc.
   - Problem: Every row has a Basis button, but every one of them has empty basis data. The reader is offered a source link that leads nowhere, which is a fake affordance that suggests provenance the section does not have.
   - Fix: Show a Basis chip only when the row has at least one source reference, or fill the row's Source data.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: L326 'The evidence weights are 1.0, 0.9, 0.9, 0.4 and 0.4; E is 72 ... C is 100% ... S = 0.7 ... two MATERIAL penalties of 15 each. Exact result 28.24 is presented as integer 28; the 59 cap does not bind.'
   - Problem: E, C, S, the penalties, the 59 cap and the band are used without the formula or any definition. The reader cannot see how 72, 100% and 0.7 lead to 28.24, and 'C is 100%' reads like full coverage until the next sentence takes it back.
   - Fix: Lead with the conclusion (confidence 28 of 100, Insufficient Information, use restricted) and give the formula and term definitions once in plain words, or leave them out of the reader view.
5. **Medium · narrative** (New reader, Auditor)
   - Where: L311-326 section opens with the table 'Check / mechanism | Execution status | Manual result and boundary' and no lead sentence
   - Problem: The section has no judgement-first sentence. The reader meets nine rows of 'Not run: unavailable' before learning what they mean for confidence in this run, and the house standard puts the bottom line first.
   - Fix: Open with one sentence saying what the validation means for using the analysis, e.g. 'checks were done by hand; two material issues limit committee use'.
6. **Medium · narrative** (New reader)
   - Where: L317 'All seventeen required registers, exact declared columns and minimum rows checked manually ... full analytical completion fails because decision-dependent evidence remains unestablished and critical cells explicitly preserve gaps'
   - Problem: The table cells are dense compound sentences made of internal terms ('registers', 'declared columns', 'critical cells', 'VE-015 trigger', 'Decimal-38'). They take several readings and do not say which credit conclusion is affected.
   - Fix: Cut each cell to a short plain clause saying what passed or failed and which conclusion it affects.
7. **Low · visual** (Auditor)
   - Where: Schema/system companions row, rendered text 'Evidence validation/Evidence validation schema and system reference files not separately supplied' (CP-5_s-311.png, y≈517)
   - Problem: Replacing module codes with names turned 'CP-5/CP-5A' into a stuttering duplicate label that looks like a rendering bug.
   - Fix: Have the name substitution collapse duplicate names, or rewrite the cell without module references.
8. **Low · visual** (New reader)
   - Where: Upstream score audit table rows (CP-5_s-311.png, y≈895-1180), Source readiness, Financial foundation, Business & governance, Fundamental credit, Legal & covenants, Security selection
   - Problem: The 'Supplied numeric grade' column mixes 'Not supplied' prose with values like '0; Insufficient Information; Blocked', so the two real scores (0 and 24) do not stand out in the table.
   - Fix: Put the numeric score and the band in separate columns, with an em dash for not supplied, so the reader can scan the scores.

### Gaps

Kind: prose/table · handoff lines 360-374 · verdict **BLOCK**

- Narrative: The Gaps section is a table plus a process paragraph written for the pipeline, not for a portfolio manager: no judgement first, no ranking of which gaps block the credit view, pipeline vocabulary throughout, and the module codes CP5-001/CP5-002 still on screen.
- Visual: The table renders in full width without clipping (unlike the Calculations table above it), but the narrow Owner and Source columns wrap heavily, and Basis chips appear inconsistently with empty content.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 364-365: "CP-1, then CP-2/CP-3; Open CP5-001" / "CP-3; Open CP5-002" (screenshot CP-5_s-360.png, Gap 1 and Gap 2 Owner / status cells)
   - Problem: The renderer rewrote CP-1 and CP-3 into module names but missed the unhyphenated issue IDs, so the reader still sees the internal codes "Open CP5-001" and "Open CP5-002" on screen (confirmed in CP-5.dom.html). This breaks the no-module-code rule, and the reader has no way to know what those issues are.
   - Fix: Show the issue in plain words (e.g. "Open: debt presentation issue") or link it to a labelled entry in the issue log, with no CP code.
2. **High · narrative** (Auditor, New reader)
   - Where: Line 364-366: "Obtain producer correction and explicit downstream adoption of carrying default with gross bridge"; "Prevents canonical validation"; "Source-acquisition factual predecessor"
   - Problem: Every row is written in pipeline vocabulary (producer, downstream adoption, canonical, schema/gate field census, factual predecessor, consumers). The ruling bans these words as reader language, and a credit committee member cannot tell what is actually missing or why it matters.
   - Fix: Say what evidence is missing and what credit question it leaves open, e.g. "Executed credit agreement and indentures not obtained; recovery and covenant claims cannot be confirmed."
3. **High · narrative** (Saboteur)
   - Where: Line 366-367: "Blocks clearance of contractual/recovery assertions, not audit of historical claims" / "Blocks clearance of preference, executable RV and sizing"
   - Problem: The two gaps that block the credit decision (legal/recovery and relative value/sizing) carry the same weight as housekeeping rows like method tooling and publication cutoff. The section opens with no bottom line, so a committee reader can miss that recovery and position sizing are unsupported.
   - Fix: Open with a one-sentence judgement naming which gaps block the credit view, and order or flag the rows by how much each affects the decision.
4. **Medium · narrative** (New reader)
   - Where: Line 366-369: "ICA/party package"; "executable RV and sizing"; "Top 5 default retained"; "selected-driver trace plus handoff-level lanes"
   - Problem: The undefined abbreviations (ICA, RV) and internal scope labels (Top 5 default, handoff-level lanes) would send the reader to another page to understand the gap.
   - Fix: Spell out intercreditor agreement and relative value, and describe the scope in plain terms (e.g. "only the five most material drivers were traced").
5. **Medium · narrative** (Auditor)
   - Where: Line 373: "Bounded research requests above name the required factual predecessors and Evidence Trace Validator as validation consumer. No CP-DR artifact, question assignment or research hash was supplied, so no adoption record is fabricated."
   - Problem: The closing paragraph is pure process disclosure aimed at the pipeline (rendered as "No Research questions artifact... research hash"). It tells the reader nothing about credit and adds no limitation they can act on.
   - Fix: Drop it, or replace it with one sentence on what the missing evidence means for how far the reader can rely on the validation.
6. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 368-371 Owner / status: "Producer owners; unresolved, no independent historical-analysis block"; "Validation scope owner"; "This module; execution disclosed in QA Validation"
   - Problem: The Owner / status column names no real owner or status a reader can follow up on. "This module" and "Producer owners" are self-referential pipeline labels, so the column only looks accountable.
   - Fix: Use plain status values (Open / Accepted limitation / Not pursued) and name the reader-facing page or party responsible, or drop the column.
7. **Medium · visual** (Auditor, New reader)
   - Where: Gaps table, CP-5_s-360.png approx. x 300-1160, y 1100-1650 (Basis chips on Gap 3, Gap 4, Publication/cutoff control only)
   - Problem: Basis chips appear on only three of the eight rows, and the DOM shows they carry an empty basis (data-basis="[]"). The reader sees a provenance control that opens nothing and an inconsistent row pattern.
   - Fix: Show a Basis chip only when it has content, and put the same provenance treatment on every row.
8. **Low · visual** (New reader)
   - Where: Gaps table, CP-5_s-360.png approx. x 1090-1160 and x 1220-1390, y 1110-1650 (Owner / status and Source columns)
   - Problem: The narrow Owner / status and Source columns wrap to six to nine lines per cell (e.g. the raw filename "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl" broken across lines). Row height balloons and the table becomes a tall, hard-to-scan block.
   - Fix: Shorten the source to a readable label ("10-K FY2024, pp. 103-104") and rebalance column widths so rows stay two to three lines.

### Key findings

Kind: reader passage · handoff lines 61-70 · verdict **BLOCK**

- Narrative: The four bullets put the bold lead-in first, but they judge the analysis pipeline rather than TDG's credit. They use banned workflow vocabulary ("gates", "downstream reuse") and present key figures without the measure name or period.
- Visual: There is no chart in this section. The bullet list itself is legible and well spaced, but only the fourth bullet has a visible Basis link, and the monospace dotted figure chips make the prose look patchy.

1. **High · narrative** (Auditor, New reader)
   - Where: L68 "Decision abstention is the correct treatment of the legal and market gates."; L64 "needs remediation before unqualified downstream reuse ... principal became the default financial numerator ... exposing downstream comparisons to definition drift"; L62 "passing the calculation audit"
   - Problem: The passage is written in pipeline language. It uses "gates", which the house standard bans by name, along with "downstream reuse", "default financial numerator", "definition drift" and "calculation audit". The bold lead-ins judge how the analysis was produced, not TransDigm's credit, so a committee member learns about the run's internal plumbing instead of the issuer.
   - Fix: Restate each lead-in as a credit judgement about TDG, such as which debt figure to use and what it means for leverage, and remove the workflow terms.
2. **High · narrative** (Saboteur, New reader)
   - Where: L62 "The issuer-adjusted earnings bridge closes to USD 4,173 million, and historical coverage of net cash interest reproduces approximately 3.60x."
   - Problem: USD 4,173 million is not named as a measure: "issuer-adjusted earnings" could be EBITDA As Defined or something else. Neither figure gives its period (FY2024 is implied but never stated). "Approximately" hedges a ratio that was reproduced. A reader cannot carry these figures into a leverage or coverage view without the source.
   - Fix: Name the measure (e.g. FY2024 EBITDA as defined by the issuer), state the period for both figures and give the ratio exactly as reproduced.
3. **Medium · narrative** (Saboteur)
   - Where: L64 "The financial foundation leads with USD 25,068 million of principal while the security analysis uses USD 24,880 million of carrying debt. Both figures are disclosed and supported"
   - Problem: The bullet shows two total-debt figures that disagree and says both are supported. It never says which one the committee should use or how much leverage moves between them, so a reader could quote either.
   - Fix: State which debt basis the reader should rely on and give the leverage effect of the USD 188 million difference in one clause.
4. **Medium · narrative** (New reader)
   - Where: L66 "Static cash of USD 1,913 million after the specified payments and filing-defined payment-adjusted liquidity of USD 2,919 million are different measures, not contradictory closing balances."
   - Problem: "The specified payments" is never identified: the special dividend's amount and date are missing. "Filing-defined payment-adjusted liquidity" is opaque. The reader cannot see what separates the two figures or which one bounds liquidity, so this bullet can only be followed with the source document open.
   - Fix: Name the payment and its amount, and define the two liquidity measures in plain words, including which one the reader should use for headroom.
5. **Medium · narrative** (Saboteur)
   - Where: L66 "supported rather than promotional or speculative"; L64 "not an arithmetic error or a new liability"; L68 "they do not establish an attractive or unattractive trade"
   - Problem: Each bullet is framed defensively, mostly by saying what something is not. The fourth bullet makes no finding about TDG at all. The section reads as a rebuttal, not as judgement-first findings, which buries the credit message.
   - Fix: Lead each bullet with a positive statement of what the evidence shows about the issuer, and fold the fourth bullet's abstention point into Limitations.
6. **Medium · visual** (Auditor)
   - Where: Key findings list, shots/CP-5_key-findings.png crop (340,220)-(1020,800), saved as tmp/CP-5-093-a.png; rendered DOM render/CP-5.dom.html, li items 1-3 vs 4
   - Problem: Only the fourth bullet has a visible "Basis" link. In bullets 1-3 the basis is attached only to the figure buttons, so non-numeric claims such as "principal became the default financial numerator" have no visible source. Placement differs from bullet to bullet within one list.
   - Fix: Render a Basis link at the end of every bullet, whether or not it contains figures.
7. **Low · narrative** (Auditor)
   - Where: L65 "Basis: Financial foundation (CP-1); Fundamental credit synthesis (CP-2); Relative value and security selection (CP-3); calculation V01; calculation V02"
   - Problem: The basis data behind the figure buttons carries module codes (CP-1, CP-2, CP-3) and internal calculation IDs (V01, V02). If the popup shows that text, a module code appears on screen. I read this in the DOM's data-basis attribute but did not see the popup itself.
   - Fix: Map basis entries to reader names (module title, filing page) without CP- codes or internal calculation IDs.
8. **Low · visual** (New reader)
   - Where: Figure chips in bullets 1-3 (e.g. "USD 4,173 million", "3.60x"), tmp/CP-5-093-a.png
   - Problem: Figures are set in monospace with a dotted underline inside proportional prose. Five of them in three bullets make the lines look patchy and slow scanning. The small grey "Basis" link at the end of bullet 4 also has low contrast against white.
   - Fix: Keep figure chips in the body font with a lighter cue, and give the Basis link enough contrast to be found.

### Limitations

Kind: reader passage · handoff lines 75-80 · verdict **BLOCK**

- Narrative: The section follows the house order (Limitations comes last, after the judgement and contrary evidence, and references sit in Basis lines). Its two bullets, however, are written in pipeline and audit vocabulary and cite a grade and a defect without stating either.
- Visual: The section has no chart, map or timeline, only two bulleted paragraphs with Basis links. The layout is clean and readable, apart from the faint Basis cue and a narrow text column next to full-width neighbours.

1. **High · narrative** (Auditor, New reader)
   - Where: line 76: "reviews the supplied handoffs for broader gate and integrity issues"; line 78: "Module-specific required-field contracts and claim censuses are not supplied for several earlier producers."
   - Problem: Pipeline words the house standard bans ("handoffs", "gate", "producers") appear on screen unchanged, as the rendered DOM confirms. Internal terms such as "required-field contracts" and "claim censuses" also leave a credit committee reader unable to say what was not checked.
   - Fix: Describe the limits in reader terms, for example "the other analyses were checked only for broad consistency" and "several earlier analyses did not list the fields they required, so their confidence scores cannot be re-scored on a like-for-like basis".
2. **High · narrative** (Saboteur, New reader)
   - Where: line 78: "the present grade applies to this validation run, while the identified security-analysis scoring defect remains open."
   - Problem: The passage cites "the present grade" and "the identified security-analysis scoring defect" but gives neither the grade's value nor what the defect is. The grade (confidence 28, Insufficient Information) appears only in raw front matter further down. A reader cannot tell how far the open defect weakens the clearance, so a caveat that matters reads as housekeeping.
   - Fix: State the grade and its band, and say in one clause what the open scoring defect is and which conclusion it limits.
3. **Medium · narrative** (Saboteur)
   - Where: line 76: "Its clearance is therefore a bounded provenance opinion, not a whole-run assurance opinion."
   - Problem: The limitation names what is not certified but does not say what the reader should not rely on as a result. It omits the specific limits that drive the decision (restriction to historical discussion, the withheld legal and recovery conclusions), so the consequence for committee use has to be pieced together from earlier sections.
   - Fix: Close each limitation with its practical effect, for example which figures or conclusions the committee should treat as unverified.
4. **Low · narrative** (New reader)
   - Where: line 76: "bounded provenance opinion, not a whole-run assurance opinion"
   - Problem: "Provenance opinion" and "whole-run assurance" are audit-team terms that a portfolio manager has to decode.
   - Fix: Use plain wording such as "it confirms the sources behind the five main drivers only, not every figure in the report".
5. **Low · visual** (Auditor)
   - Where: Limitations block, CP-5_limitations.png, region x 330-1440, y 210-440 (crop CP-5-095-a.png)
   - Problem: Each bullet ends with a small low-contrast grey "Basis" link, which is easy to miss. The text column fills about 60% of the content width, leaving a wide empty band to the right, while the map table below uses the full width, so the page rhythm is uneven.
   - Fix: Give the Basis cue enough contrast to meet accessibility standards and keep the prose measure consistent with neighbouring sections.

### Map: support and contradiction

Kind: map · handoff lines 81-93 · verdict **BLOCK**

- Narrative: The section is a bare edge table with no judgement-first lead. Its node names are in pipeline vocabulary (canonical, gate, CP5-00x, RV-/C-/KF codes) and its \"Contradicts\" edges rebut straw claims, so a reader who has not seen the sources cannot tell what the map concludes.
- Visual: The map is visible on the page (not folded away), but its node labels break mid-word or are truncated, and it has no legend and no colour coding. Its edge table is repeated in two inconsistent styles, one of them monospace with underlined links.

1. **High · narrative** (Auditor, New reader)
   - Where: L88-92: "Canonical debt-basis remediation"; "Canonical carrying-value convention ... Principal as canonical default ... CP5-001"; "Executed-document gate"; "source-gate and schema fields"; "CP5-002"
   - Problem: The house rules list "canonical" and "gate" as banned pipeline words, and both appear in node names the reader sees. The screen also shows internal codes: CP5-001/CP5-002 (a module code), RV-C03, RV-Q02, C01/C13, KF1, F1 and "Traceability map" D1/D2. A committee member cannot resolve these without opening other pages.
   - Fix: Use plain credit language for the nodes (for example "Carrying value as the standard debt measure", "Signed legal documents not available") and keep the internal IDs out of what is displayed.
2. **High · visual** (Auditor, New reader)
   - Where: Support and contradiction map, CP-5_maps.png, crop x340-1400 y250-790 (scratchpad/tmp/CP-5-096-a.png): node labels "FY2024 cash-flow state ment", "Historical servicing s upport", "Canonical debt-basis r emediation", "September financing an d October payment disc..."
   - Problem: Nearly every node label wraps at a fixed character count, breaking words in the middle ("state ment", "s upport", "v alues", "pr eference"), and one label is cut off with an ellipsis, so the drawing cannot be read without the table below it. The edge sentence is also dropped, so each arrow carries only a one-word type.
   - Fix: Wrap node labels at word boundaries, size the boxes so no label is cut off, and keep the full text available on the node.
3. **Medium · narrative** (Saboteur)
   - Where: L90: "Accounting debt fair values | Dated instrument valuations exist despite absence of executable comparisons | Contradicts | No valuation information exists"
   - Problem: "Contradicts" is used against claims nobody made ("No valuation information exists", "Principal as canonical default"), so the edges are double negatives. A reader scanning the Edge type column will read three "Contradicts" rows as evidence against the credit, when they actually rebut straw positions or flag pipeline definition defects. The section also has no lead sentence saying what the map concludes.
   - Fix: Open with a one-sentence judgement on what the map shows, and phrase each target node as the claim actually at stake so that Supports and Contradicts read the way a reader expects.
4. **Medium · narrative** (Saboteur)
   - Where: L88: "Balance-sheet carrying debt | The balance-sheet sum differs from the principal default but agrees with the security dashboard | Supports"
   - Problem: The debt-basis edges give no amounts, units or date: USD 25,068 million principal vs USD 24,880 million carrying, a USD 188 million gap, at 30 September 2024. Without them the reader cannot judge whether the "difference" matters.
   - Fix: Put the two debt figures, the gap, the currency and the as-of date in the relationship or the evidence cell.
5. **Medium · narrative** (New reader, Auditor)
   - Where: L90 Evidence cell as rendered: "Security selection a method step correctly preserves this distinction; this is counterevidence, not an attributed upstream error"; L91: "Legal & covenants Blocked"
   - Problem: The code substitution has left the Evidence cell ungrammatical ("Security selection a method step"). The cell also holds the reviewer's commentary and a workflow status ("Blocked") instead of a source reference, which mixes reasoning into what should be a source column.
   - Fix: Keep the Evidence column to source references only, and move any interpretation into the Relationship text or a short note.
6. **Medium · visual** (New reader, Auditor)
   - Where: CP-5_maps.png (y~250-1680) vs CP-5_s-81.png (y~190-755): the same eight-row edge table appears twice on the page
   - Problem: The Maps panel's "Edges of the map, as stated" table and the section table "Map: support and contradiction" repeat each other a screen apart, in two different styles. The Maps copy uses monospace From/To/Edge type text and a column of blue underlined link text, a dense block that reads like code and does not match the house table style.
   - Fix: Show the edge table once, in the house table style, next to the map, and render relationship text as plain text rather than a run of underlined links.
7. **Medium · visual** (Saboteur, New reader)
   - Where: Support and contradiction map, scratchpad/tmp/CP-5-096-a.png: solid, dashed and dotted connectors labelled Supports / Contradicts / Unresolved, all drawn in the same navy
   - Problem: There is no legend, and colour does not separate support from contradiction, so line style is the only cue, which is weak for accessibility. Most of the panel's right half is empty because only one chain reaches a third node.
   - Fix: Add a small legend, separate the edge types with colour as well as line style, and lay the map out more compactly so the empty right half goes.
8. **Low · visual** (Auditor)
   - Where: CP-5_s-81.png section table, From column: "FY2024 cash-flow statement Basis" (every row)
   - Problem: A "Basis" chip sits inside each From cell next to the node name. This crowds the first column, and it looks like part of the label rather than a source link.
   - Fix: Put the basis link in the Evidence/Source column, or at the end of the row, not in the From cell.

### Traceability conclusion

Kind: prose/table · handoff lines 94-98 · verdict **BLOCK**

- Narrative: The section is a second, more internal restatement of the Bottom line. It opens with status labels rather than a plain judgement, does not say which drivers rest on inference, and leaks a rule code (VE-015) and pipeline wording ("gated decision", "orphan claim", "whole-pack or all-cell certification").
- Visual: The section is prose only, with no chart, map or timeline. It renders as two wide, dense paragraphs with no visual weight on the verdict. Nothing is clipped or overlapping.

1. **High · narrative** (Auditor, New reader)
   - Where: line 97: "VE-015 is not triggered: unestablished legal, market, recovery and portfolio outcomes are explicitly limited or withheld."
   - Problem: VE-015 is an internal rule code. It is never defined for the reader, and the house standard bans register codes on screen. A credit committee member cannot tell what test was passed or why it matters.
   - Fix: State the check in plain words (for example, that no unproven legal, market or recovery outcome is presented as established) and leave the rule code out.
2. **High · narrative** (Auditor, New reader)
   - Where: line 95: "That is an inherited gated decision, not a newly discovered orphan claim."
   - Problem: "Gated" and "orphan claim" are pipeline vocabulary, which the house standard says is not reader language. The sentence describes how the workflow works, not anything about the credit.
   - Fix: Say in reader terms that the missing legal documents were already flagged in the legal review and are not a new gap found here, or drop the sentence.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: line 95: "Of the Top 5 material credit drivers, 1 is directly sourced, 2 are calculated, none is assumption-based, 2 are analyst inferences, and none is weak-lineage, untraced, conflicting or insufficient-information."
   - Problem: The counts are not tied to named drivers, and the drivers are only listed in the next paragraph (line 97). The reader cannot tell which two conclusions, such as recovery protection or cash retention, rest on analyst inference. Six of the nine categories are listed only to say they are empty.
   - Fix: Name the two inference-based drivers, and the sourced and calculated ones, in one line or a small five-row table, and drop the empty categories.
4. **Medium · narrative** (Saboteur)
   - Where: line 95: "Overall, evidence traceability is Not Committee-Ready for an unrestricted investment decision and Ready with Remediation for historical fundamental discussion."
   - Problem: The verdict is a pair of capitalised internal status labels with two scopes. "Ready with Remediation" does not say what remediation is needed or who must do it before discussion. Read quickly, it can come across as a pass.
   - Fix: Lead with one plain judgement: usable for discussing historical fundamentals only, and not for a security or sizing decision until the executed legal terms are obtained.
5. **Medium · narrative** (Saboteur, Auditor)
   - Where: line 97: "No Critical unsupported committee-facing claim was identified in this selected review. ... This statement is not a clean-history, whole-pack or all-cell certification."
   - Problem: The paragraph's reassurance is undone by its closing disclaimer, which uses unexplained jargon ("whole-pack", "all-cell", "selected review"). The reader cannot tell how much of the analysis was actually checked.
   - Fix: State the scope once and plainly (the five ranked drivers were checked, the rest of the analysis was not) and remove the jargon caveat.
6. **Medium · narrative** (New reader, Auditor)
   - Where: line 94: "### Traceability conclusion" placed after "### Map: support and contradiction" (line 81) and before the appendix
   - Problem: A second conclusion appears mid-page after the Maps section and largely repeats the Bottom line (line 55) in more internal terms. Neither paragraph has a Basis line, so the counts and the 'no Critical claim' result cannot be traced.
   - Fix: Fold the unique content (the driver classification and the key provenance gap) into Key findings, or give each paragraph a Basis line pointing to the driver ranking and gaps ledger.
7. **Low · visual** (New reader)
   - Where: screenshot CP-5_s-94.png, region x 340-1400, y 215-430 (tmp/CP-5-097-a.png)
   - Problem: Two dense blocks of five and three lines run the full column width (about 170 characters per line), with no visual cue for the verdict. The status phrases "Not Committee-Ready" and "Ready with Remediation" look like ordinary body text, so the judgement does not stand out.
   - Fix: Give the verdict its own short opening line or status chip and keep the measure narrower or the paragraphs shorter.
8. **Low · visual** (Auditor)
   - Where: screenshot CP-5_s-94.png, the full region under "Traceability conclusion"
   - Problem: The five-driver classification is a natural table but is rendered as an inline run-on list. The page next to it has the 'Top five material driver ranking' table, which repeats the drivers without this classification, so the reader has to match the two by memory.
   - Fix: Show the classification as a column in the existing Top five driver ranking table instead of as prose here.

### Analytical appendix — complete canonical registers (part 1 of 2: from 'T5B.1 — Source register and source gate')

Kind: register appendix · handoff lines 104-199 · verdict **BLOCK**

- Narrative: This is a data/register appendix, so it owes only a bottom line, and it does put the auditability verdict last (L198) instead of first. It also leaks pipeline vocabulary and internal register codes throughout.
- Visual: The section has no charts, only wide register tables. In the screenshot they show clipped right-hand Limitation text and large empty row bands; Basis chips correctly replace the Source column.

1. **High · narrative** (Auditor; New reader)
   - Where: L119 "The first four handoffs have no explicit run_id envelope: exact supplied pins and matching request scope are the transport lineage, not invented run IDs." Also L196 "Six transported H2s and all supplied pins available; CP-OS acceptance is controlling" (rendered as "Run activity acceptance")
   - Problem: The reader sees pipeline vocabulary: handoff, run_id envelope, pins, transport lineage, producer, canonical, gate, H2s, qa_status and the raw run key tdg-2024-09-30-credit_snapshot-sol-medium. The house standard bans these terms, and a credit committee member cannot act on them.
   - Fix: Remove the pipeline-integrity rows and sentences (source-gate transport, Markdown/export artifact integrity, qa_status) from the reader page, or restate them as one plain sentence about which inputs the review relied on.
2. **High · narrative** (Auditor; New reader)
   - Where: L183 "CP5-001: sourced principal is the leading numerator despite the carrying-value default"; L174 "CP5-002"; L186 "No new CRITICAL VE-015 issue is asserted"; L126 "CP-1 C03/C05; V03/V04"
   - Problem: Module renaming replaced the CP-n codes, but internal register codes are still on screen: CP5-001/002, VE-015, C01–C19, RV-C03, V01–V11, F1/G1, W1, S1, B1/B2/X1 and the K24 alias. They are undefined on the page, so the Source Trace column and the flags table can only be read on other pages.
   - Fix: Replace the register codes with short plain descriptions (for example 'debt-basis inconsistency' instead of CP5-001), or drop Source Trace and keep the Basis/Source link.
3. **Medium · narrative** (Saboteur; New reader)
   - Where: L198 "Lowest-common-denominator overall assessment: Not Committee-Ready for unrestricted decision use... Overall module status is Ready with Limitations and qa_status Restricted"
   - Problem: One verdict appears under three different labels: Not Committee-Ready, Ready with Limitations and Restricted. The section's own status line (L119, 'Ready with Limitations, not Blocked') sits beside them. A reader cannot tell which one governs the credit use of the findings.
   - Fix: Give one reader-facing verdict at the start of the appendix (e.g. 'usable for historical discussion only, not for a trade decision') and drop the internal status labels.
4. **Medium · narrative** (New reader)
   - Where: L108 table header "Source Document ID | Source Document Name | Source Quality | Period | Entity Covered | Data Supplied | Limitation | Downstream Use | Source" (and 10-column tables at L135, L145, L166)
   - Problem: Every register is a 7–10-column table of terse fragments in 7–8 narrow columns. Several columns repeat each other: Source File says 'K24 exact filename in Sources' on every row, and Source Path says 'Pinned source tool' on every row. Wide tables full of repeated cells slow the reader without adding information.
   - Fix: Drop the constant or duplicate columns (Source Path, Source File, Source Document ID) and keep only the columns that differ by row and matter for credit.
5. **Medium · visual** (Auditor; Saboteur)
   - Where: Top five material driver ranking table, shots/CP-5_s-106.png, x≈1300-1390 (orig px), y≈1700-2400; crop tmp/CP-5-099-b.png
   - Problem: The table is wider than the content column, so the Limitation column is clipped at the card's right edge: row 1 runs 'inference, not' into the border and row 4 'Management' touches it. The limitation caveats, which keep these drivers from being over-read, are the text being cut off.
   - Fix: Fit the table to the column width (fewer columns or wrapping), or give it a visible horizontal scroll affordance, so the Limitation text is never clipped.
6. **Medium · visual** (New reader; Auditor)
   - Where: Source register table K24 row (shots/CP-5_s-106.png y≈300-545 orig px) and driver table row 3 (y≈2010-2270); crop tmp/CP-5-099-a.png
   - Problem: Rows carry large blank bands, about 100–200 px below the last line of text. The likely cause is the hidden Source cell with its long filenames setting the row height. The tables look broken and push content down the page.
   - Fix: Row height should follow the visible cells only, so a source that has moved into the Basis chip leaves no empty space.
7. **Low · narrative** (Saboteur)
   - Where: L168 "Annual CFO 2045, signed capex -165, adjusted EBITDA 4173, net cash interest 1158; USD million"
   - Problem: The calculation trace drops thousands separators and puts the unit at the end of the cell, while the neighbouring tables write 'USD 2,045 million'. On the same page, the two formats make the figures harder to compare.
   - Fix: Use the 'USD 2,045 million' format in the calculation trace, as the other tables do.

### Remediation priority map

Kind: prose/table · handoff lines 297-305 · verdict **BLOCK**

- Narrative: The section is written as internal QA routing (\"handoff\", \"canonical\", \"downstream\", bare issue IDs) instead of a credit judgement, and it never says what the two open defects are or how much they matter.
- Visual: There is no chart. The section is four plain paragraphs of the same weight with unbolded run-in labels and no Basis links, so a section titled as a priority map shows no visible priority or owner structure.

1. **High · narrative** (Auditor; New reader)
   - Where: L300: "Must-fix before canonical Markdown handoff is consumed downstream: no separate envelope defect. Downstream may consume this QA handoff now as a restriction-bearing artifact; it may not consume the affected debt defaults or confidence score as unqualified canonical inputs."
   - Problem: This whole paragraph is pipeline instructions, not credit content, and it reaches the reader word for word (DOM s-297): "canonical", "Markdown handoff", "downstream", "consume", "QA handoff", "envelope defect", "promoted". Those are banned terms under the house standard, and a committee member can do nothing with this paragraph.
   - Fix: Drop the paragraph from the reader page, or state in plain terms which debt figure and which confidence score the reader should not rely on yet, and why.
2. **High · narrative** (Auditor; New reader)
   - Where: L298: "Must-fix before committee: CP5-001 and CP5-002 must be corrected before unrestricted committee clearance"; also L300 "CP5-001 and CP5-002 correction and adoption remain required"
   - Problem: The issue IDs CP5-001 and CP5-002 are shown on screen, and they are shaped like module codes. The section never says what the two defects are, so the reader has to go back to the issue log table above to learn that one is a debt-measure mismatch (principal vs carrying value) and the other is an unvalidated confidence grade.
   - Fix: Name each defect in plain words where it is cited, for example "the debt figure basis (face value vs carrying value) and the unvalidated confidence score", and drop the internal IDs.
3. **Medium · narrative** (Saboteur)
   - Where: L298: "until then, historical discussion is permitted only with their explicit disclosure and the legal/market decision restrictions... No authorized reviewer acceptance of broader use is supplied."
   - Problem: The judgement that matters (committee use is restricted, and the debt and confidence figures are not decision-grade) is buried in permission-style compliance wording. The section never says how much either defect could move leverage or the confidence score, so the reader cannot tell whether the restriction is cosmetic or material.
   - Fix: Lead with one plain judgement sentence on what the reader can and cannot rely on, then state the size of the debt-basis gap (the USD 188 million principal vs carrying difference shown in Calculations).
4. **Medium · narrative** (New reader; Saboteur)
   - Where: L302: "Re-audit if governing documents, maintained-market observations, recovery inputs, a changed distribution, new secured claims or a preferred-security/sizing conclusion enters the active handoffs. Do not require a freshness confirmation for maintained Sector RV."
   - Problem: The triggers are run-maintenance instructions ("active handoffs", "freshness confirmation", "maintained Sector RV") rather than credit events that would change the view, and "RV" is never defined. A reader cannot tell which events matter for the credit.
   - Fix: Restate the triggers as credit events (for example new secured debt issued, or a dividend recap) and spell out "relative value".
5. **Medium · visual** (New reader; Auditor)
   - Where: Remediation priority map, shot CP-5_s-297.png, top region at about y=190-390 (display scale)
   - Problem: Four plain paragraphs of the same weight carry the run-in labels "Must-fix before committee:", "Must-fix before canonical...", "Monitoring follow-up:" and "Formatting / hygiene:" as body text with no bold, list or table. A section called a priority map has no visible priority, owner or status structure, so the reader cannot scan it.
   - Fix: Render it as a short table or a bolded label list (priority, issue in plain words, owner, what clears it) so the order of priority can be seen.
6. **Low · narrative** (Auditor)
   - Where: L304: "Formatting / hygiene: None."
   - Problem: This is an empty internal QA category shown to the reader. It adds no information and signals the page is a working checklist.
   - Fix: Leave empty internal categories out of the reader page.
7. **Low · visual** (Saboteur)
   - Where: shot CP-5_s-297.png, Remediation priority map vs Consolidated issue log; DOM s-297 has no basis-link button
   - Problem: The narrative paragraphs in this section have no Basis link, unlike the table rows nearby, so the reader has no on-page route to the evidence behind the must-fix claims.
   - Fix: Add a Basis line to each paragraph, as the house standard requires for prose passages.

### Calculations

Kind: prose/table · handoff lines 337-359 · verdict **BLOCK**

- Narrative: All 11 V-row sums and the Q02 count reproduce exactly, but the section is a methods ledger with no judgement first: operands have no names, internal codes and tool vocabulary leak through, and a key ratio is printed to 37 decimals.
- Visual: The section has no chart, only one table, and at 1440 px it is clipped: the limitation column is cut off, the Source column is out of view with no scroll cue, and rows are padded with large empty space.

1. **High · narrative** (New reader, Saboteur)
   - Where: line 343-350: "V01 | sum(98,486,24296)" ... "V08 | sum(1880,-2347,-2038) | USD -2,505 million | FY2024 selected-use shortfall"
   - Problem: The operands are bare numbers with no names. A reader cannot tell what 98, 486, 2,347 or 2,038 are, so cannot check the shortfall or debt totals without opening the filing. The -2,505 shortfall is a credit-relevant figure, but its uses are never named.
   - Fix: Name each operand in the Operation cell, for example 'CFO less capex 1,880 - acquisitions 2,347 - distributions 2,038'.
2. **High · visual** (Auditor, Saboteur)
   - Where: Calculations table, shots/CP-5_s-337.png, right edge x~1260-1440 at every row (crop tmp/CP-5-104-a.png)
   - Problem: The table is wider than its card at 1440 px. The 'Period / quantity / limitation' column is cut off mid-word ('FY2024 carrying deb', 'Period / quantity / lin'), the Source column is not visible at all, and nothing on screen shows the table can scroll sideways. A reader cannot see the period limits or the source behind any figure.
   - Fix: Fit all five columns inside the card at 1440 px: narrow the formula column, wrap or shorten the source text, or show a visible horizontal-scroll cue.
3. **Medium · narrative** (Auditor, New reader)
   - Where: line 339: "All new arithmetic uses calculate and the Decimal-38 kernel."; line 357: "P=30 for CP5-001 and CP5-002; clamp unchanged"; line 358: "qa_status Restricted"; "own audit gate not failed"
   - Problem: Pipeline and internal vocabulary reaches the reader: tool and kernel names, internal issue codes CP5-001 and CP5-002 (still rendered in the DOM), the field name qa_status, 'gate' and 'clamp'. None of this is reader language.
   - Fix: Drop the tooling sentence and replace the codes and field names with plain descriptions, for example 'two material issues (debt basis; security-selection confidence grade)' and 'review status: Restricted'.
4. **Medium · narrative** (Saboteur, New reader)
   - Where: line 346: "3.6036269430051813471502590673575129534x; approximately 3.60x"
   - Problem: The interest-cover ratio, the one leverage-style metric in the section, is printed to 37 decimal places. The false precision hides the figure that matters, and the intro sentence calling it 'approximate' does not help.
   - Fix: Show 3.6x (adjusted EBITDA / net cash interest, FY2024) and keep the exact value out of the reader view.
5. **Medium · narrative** (New reader)
   - Where: line 356-357: "sum(72,72,72,72,72,72)=432; ratio(432,10)=43.2" ... "sum(83.2,83.2,83.2,83.2,83.2,83.2,83.2)=582.4; ratio(582.4,10)=58.24"
   - Problem: The confidence-score rows write simple weightings (0.6E, 0.7S) as repeated additions to fit the tool's sum/ratio limits. A committee reader cannot follow the score of 28 and sees mechanics instead of the method.
   - Fix: State the formula once in plain terms, for example 'score = (0.6 x 72 + 0.4 x 100) x 0.7 - 30 = 28.24, shown as 28', with each input labelled.
6. **Medium · visual** (New reader, Auditor)
   - Where: Calculations table rows V01-V11, shots/CP-5_s-337.png y~300-1720 (displayed)
   - Problem: Rows V01-V11 are 115-165 px tall but hold one line of formula and result, leaving large blank areas. The height comes from long text in the hidden Source column, so 11 rows fill a whole screen. The 'Operation' column takes about 40% of the width for short formulas, which squeezes the columns that matter.
   - Fix: Rebalance the column widths so the Source and limitation text wrap less, and the rows shrink to their content.
7. **Low · narrative** (New reader)
   - Where: line 344: "Financial foundation (CP-1), C01/C13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 144–145"; line 352: "RV-C01/C02/C04"
   - Problem: Source cells show raw file names with accession number and .jsonl extension, plus internal register codes (C06/E-DISTRIBUTION, RV-C01). The Q rows cite 'supplied confidence specification' and 'Required-register contract'. A reader cannot identify a source from these.
   - Fix: Cite as 'TDG FY2024 10-K, p. 120' with the module name, without internal row codes.
8. **Low · visual** (Auditor)
   - Where: Calculations table ID column, shots/CP-5_s-337.png x~300-345: V01-V11 show a 'Basis' button, Q01-Q05 do not
   - Problem: Basis links appear on V rows but not on Q rows, so the same table is inconsistent about where each figure's basis can be found.
   - Fix: Give every row a Basis link, or make clear why the Q rows have none.

### Front matter + Request + Next module

Kind: run plumbing · handoff lines 1-33, 34-36, 375-379 · verdict **BLOCK**

- Narrative: This is run plumbing shown to the reader as-is. It includes a module code and a run_id that contradicts the header, and the status labels conflict with each other. Request and Next module are written in pipeline vocabulary that the house standard keeps away from the reader.
- Visual: There is no chart in this section. The front matter renders as an unbroken paragraph of YAML with long hashes that cannot be read. Request and Next module are plain body text with normal spacing, but they take up navigation and page space ahead of the analysis.

1. **High · narrative** (Auditor, Saboteur)
   - Where: Front matter line 10 'filename: tdg_CP-5_20240930.md' and line 7 'run_id: tdg-2024-09-30-credit_snapshot-sol-medium' as rendered in CP-5_s-1.png
   - Problem: A module code (CP-5) is visible on screen, which breaks the house rule. The run_id shown ('tdg-2024-09-30-credit_snapshot-sol-medium') also differs from the run the header says is showing ('TDG-READER-FORMAT-001'), so the reader may think the page belongs to a different run.
   - Fix: Show no module code or internal run identifier in reader text. Where a run is named, use the single run label from the page header.
2. **High · visual** (New reader, Auditor)
   - Where: Front matter, CP-5_s-1.png region y≈190-375 (display): rendered as one <p class="passage-text"> 'issuer_id: tdg module_id: Evidence validation module_name: ... limitation_flags: - HISTORICAL_DISCUSSION_ONLY ...' (handoff lines 1-32)
   - Problem: The raw YAML front matter is shown on the page as one run-on paragraph with no line breaks. It has nine lines of key:value pipeline metadata, six 64-character sha256 hashes and upper-case flag codes, so a credit reader cannot read it and it pushes the Request and Sources down the page.
   - Fix: Hide the front matter from the reader page. At most, show a short labelled status strip (status, QA/committee status, confidence 28/100, band) and keep the hashes and flags in the evidence or audit view.
3. **Medium · narrative** (Saboteur)
   - Where: Front matter lines 11-16 'module_status: Ready with Limitations ... qa_status: Restricted committee_status: Restricted confidence_score: 28 confidence_band: Insufficient Information'
   - Problem: Four different status labels appear side by side with no explanation. 'Ready' next to 'Insufficient Information' at 28/100 leaves the reader unsure whether the validation supports use in committee.
   - Fix: State one reader verdict in plain words (for example, fit for historical discussion only, not for an investment decision), with the confidence score explained in the bottom line rather than in the metadata.
4. **Medium · narrative** (New reader, Auditor)
   - Where: Next module line 379 'Financial foundation should remediate the canonical debt presentation ... then rerun the affected producers and this validator. No fresh acceptance receipt...'
   - Problem: Pipeline words the house standard bans ('canonical', 'producers', 'validator', 'acceptance receipt', 'handoff' on line 377) are shown to the reader. The paragraph is written as instructions to the orchestration system, not to a portfolio manager.
   - Fix: Rewrite as a plain statement of what evidence is still missing and what would lift the restriction, or keep this routing text off the reader page.
5. **Medium · narrative** (New reader)
   - Where: Next module line 377 rendered 'Proceed to Committee challenge (Committee decision) for restricted historical debate ... both open MATERIAL QA issues'
   - Problem: After label substitution the rendered text names the next module twice under two different names. 'both open MATERIAL QA issues' points to items the reader cannot find in this paragraph, and the upper-case MATERIAL is internal grading vocabulary.
   - Fix: Use one reader label for the next module and name the two open issues in plain words (debt-basis presentation, security-selection confidence).
6. **Medium · narrative** (Auditor, New reader)
   - Where: Request line 35 'audit all supplied handoffs for decision-relevant evidence, calculation, definition and gate integrity, and determine permitted committee use'
   - Problem: The Request is a system instruction written in pipeline language ('handoffs', 'gate integrity', 'credit_snapshot'), not reader language.
   - Fix: Phrase the request as the question the reader cares about (are the five main credit drivers properly evidenced, and can committee rely on them?) without pathway or pipeline terms.
7. **Low · visual** (Auditor)
   - Where: On this page TOC, CP-5_s-1.png left rail: 'Front matter', 'Request', 'Sources' listed between 'Maps' and 'Map: support and contradiction'; 'Next module' last (CP-5_s-375.png)
   - Problem: Run plumbing headings ('Front matter', 'Request', 'Next module') take up navigation entries and sit in the middle of the analysis between the limitations and the support map, so the reader's flow is broken.
   - Fix: Fold or drop the plumbing sections and move Sources to the end, so the navigation lists only analytical sections.

### Sources

Kind: prose/table · handoff lines 37-51 · verdict **BLOCK**

- Narrative: The Sources section has no judgement to order, but it is written in pipeline and transport vocabulary, its primary source is a raw filename, and it hides two material scope limits in its closing paragraph.
- Visual: The table renders cleanly in a card, with no clipping or overlap, but a 64-character sha256 column takes about half its width and pushes the useful text into cramped wraps.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 50: "CP-OS acceptance and the pins above establish lineage; this review does not demand new receipts... unprovided schema/system companions and research-routing companion are unavailable, not independent blockers." (rendered as "Run activity acceptance and the pins above..."); also rows 43-48 "supplied accepted Markdown handoff"
   - Problem: The section is written in pipeline vocabulary the house standard bans: handoff, pins, lineage, receipts, runbook, step bundles, schema/system companions, research-routing companion, "supplied accepted". The renderer swapped "CP-OS" for "Run activity" but left everything else, so a credit committee reader cannot tell what was actually checked.
   - Fix: Say in plain words what evidence was used and what was not, e.g. 'TransDigm FY2024 10-K (primary evidence) and the six earlier analyses in this report', with no process or transport wording.
2. **Medium · narrative** (Saboteur)
   - Where: Line 50: "Other inventoried issuer filings were not independently used: their inventory and quarantine dispositions are consumed through Source readiness, not presented as fresh source checks. No external sources or enterprise market observations were acquired."
   - Problem: These are scope limits that matter to the credit view: the validation used only the 10-K and no market data. They sit at the bottom of a Sources table, not in Limitations, so a reader who skips the table misses them.
   - Fix: Move the scope limits (only the FY2024 10-K checked, no market data, no other filings) into Limitations and keep Sources as a plain list.
3. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 41: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl | Primary issuer evidence..."; line 42: "context | Run settings only, not issuer evidence"
   - Problem: The primary source shows as a raw extract filename with an accession number and a .jsonl suffix, and has no plain title, fiscal period or filing date (7 November 2024 appears only deep in the appendix at line 110). The lowercase "context" row is an internal run artefact listed as if it were a source.
   - Fix: Name the source as a reader would cite it, e.g. 'TransDigm Form 10-K, FY ended 30 Sep 2024, filed 7 Nov 2024', and leave run settings out of Sources.
4. **Medium · visual** (New reader, Auditor)
   - Where: Sources table, sha256 column, shot CP-5_s-37.png region x 340-1440, y 220-800 (crop CP-5-091-a.png)
   - Problem: A 64-character hash column takes up about half the table width and gives the reader nothing. It squeezes the useful columns into two- and four-line wraps.
   - Fix: Drop the hash from the reader view, or fold it into a collapsed provenance detail, and use the width for document title, period and filing date.
5. **Low · narrative** (New reader)
   - Where: Lines 43-48: "Business and transaction context | CP-1A; supplied accepted Markdown handoff" rendered as "Business and transaction context | Business & governance; ..."; "Legal Covenant Interpreter | Legal & covenants"
   - Problem: Each upstream analysis appears under two different names in adjacent columns (and the sidebar uses the second set), so column 1 and column 2 repeat each other with inconsistent labels.
   - Fix: Use one name per analysis, the one shown in the page navigation, and merge the two columns into one.
6. **Low · narrative** (Saboteur)
   - Where: Line 47: "Legal Covenant Interpreter | CP-4; supplied accepted Blocked handoff"; line 48: "supplied accepted restricted handoff"
   - Problem: "Blocked" and "restricted" are status codes with no meaning given here. The reader cannot tell whether a legal analysis exists or what limits apply to it.
   - Fix: State the consequence in words, e.g. 'Legal analysis: not completed, governing documents unavailable'.

### Bottom line

Kind: reader passage · handoff lines 54-60 · verdict **BLOCK**

- Narrative: The verdict ('not cleared for a security-selection or portfolio decision') comes first. But it is about the run's traceability more than TransDigm's credit, it is written in banned pipeline words, and the second paragraph only describes the process. Not verified: whether the Basis popover shows module codes such as '(CP-1)' on screen, since only the static screenshot and DOM were checked.
- Visual: There is no chart in this section. The bottom line is drawn as a 16-line block of bold display text, the first paragraph has no Basis link, and the 'Bottom line' heading is hidden.

1. **High · narrative** (Auditor, New reader, Saboteur (promoted))
   - Where: L55 "The principal governance defects are inconsistent canonical debt presentation and a noncanonical confidence-coverage denominator"; L58 "despite the legal producer's block ... Acceptance of a handoff establishes its identity ... overrides any upstream block"
   - Problem: The bottom line uses pipeline words the house standard bans (canonical, noncanonical, producer, handoff, upstream block, evidence-validation workflow). A committee member cannot tell what defect is meant or whether it matters to the credit.
   - Fix: Say it in reader terms, for example that two modules use different debt totals (principal USD 25,068 million against carrying value USD 24,880 million) and that the confidence score is computed on an incomplete base, and drop the pipeline words.
2. **Medium · narrative** (Saboteur, New reader (promoted))
   - Where: L58 "The evidence-validation workflow can proceed despite the legal producer's block because that block is disclosed ... this review neither changes the issuer thesis nor overrides any upstream block."
   - Problem: The second paragraph is about the process and the module's own permissions. It says nothing about TransDigm, yet it gets headline weight and pushes the useful limit (covenant capacity and recoveries are not assessed) into process language.
   - Fix: Cut it to one plain sentence on what the reader cannot rely on yet: no covenant capacity, recovery or relative-value conclusion, because the legal review could not be completed.
3. **Medium · narrative** (Saboteur)
   - Where: L55 "the filing explicitly connects USD 3,000 million of new secured financing to the subsequent shareholder payment"
   - Problem: The judgement depends on cash being raised to pay shareholders, but the passage gives no size or date for the payment and no definition of the USD 1,880 million free cash flow. The reader cannot weigh the cash-retention point it calls central.
   - Fix: State the payment amount and its October 2024 timing, and the free-cash-flow basis, next to the two figures already given.
4. **Medium · visual** (Auditor)
   - Where: Screenshot CP-5_bottom-line.png, first headline paragraph (about y=190-650 at 1440 px); DOM: the L55 paragraph has no basis-link button, only the L58 paragraph does
   - Problem: The first and most important bottom-line paragraph shows no Basis link. Its sources (handoff L56) appear only in the figure popovers, which breaks the rule that every paragraph carries a Basis line.
   - Fix: Render a Basis link after the first paragraph, as is done for the second.
5. **Medium · visual** (New reader, Saboteur (promoted))
   - Where: Screenshot CP-5_bottom-line.png, top block about x=355-1010, y=225-800 (original px): two paragraphs of about 16 lines in large bold display type
   - Problem: The headline style is used for about 150 words of dense bold text. Everything is emphasised equally, the one-clause verdict ('not cleared for a security-selection or portfolio decision') is lost, and the block is tiring to read.
   - Fix: Set only the one-sentence verdict in headline type and the supporting sentences in body weight, as in the VMO2 reference.
6. **Low · visual** (Auditor)
   - Where: Screenshot CP-5_bottom-line.png, top of content; DOM `<h4 class="sr-only">Bottom line</h4>`
   - Problem: The 'Bottom line' heading is screen-reader-only, so the section starts with no visible label, while 'Key findings' and the sections below have visible headings.
   - Fix: Show a small visible 'Bottom line' label above the headline paragraph, matching the other section headings.
7. **Low · visual** (New reader)
   - Where: Screenshot CP-5_bottom-line.png, figures 'USD 1,880 million' and 'USD 3,000 million' inside the bold headline (about y=380-430 original)
   - Problem: Monospace figure chips with dotted underlines sit inside large bold proportional text. The mixed fonts break the line rhythm and look like code.
   - Fix: Size and weight figure chips to match the surrounding headline text, or use a lighter cue that the figure is interactive.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 71-74 · verdict **BLOCK**

- Narrative: The section is one paragraph (handoff line 72, Basis line 73). It argues for widening the review's own clearance rather than presenting credit-substantive counter-evidence, gives no figures, and states its change conditions in pipeline vocabulary that includes the banned word "producer".
- Visual: There is no chart, map or timeline in this section. The layout is a single dense paragraph at a reasonable line length, with a faint, unobtrusive Basis control. Not verified: how the expanded Basis popup renders its data-basis entries such as "Financial foundation (CP-1)"; if they appear as-is, module codes would show on screen.

1. **High · narrative** (Auditor, New reader (promoted from Medium))
   - Where: line 72: "Unrestricted clearance would require producer-owned alignment of the default debt basis, a confidence calculation using the mandated field census ... Additional graph edges or a higher mechanical coverage score would not substitute"
   - Problem: The passage uses "producer", which the house standard names as banned pipeline vocabulary, and also "mandated field census", "graph edges", "mechanical coverage score" and "clearance". A portfolio manager cannot tell what has to happen, or who has to do it, before the view changes.
   - Fix: State the conditions in reader terms, e.g. one agreed debt figure (principal or carrying value) used throughout, a recomputed confidence score, and executed debt documents for any legal question, with no pipeline vocabulary.
2. **Medium · narrative** (Saboteur)
   - Where: line 72: "The strongest case for broader clearance is the unusually explicit source trail: the financial foundation discloses both debt bases, the security analysis logs their difference"
   - Problem: The contrary case argues only about how far the review process can be trusted. It gives no credit-relevant evidence against the issuer view, such as the USD 3,000 million secured financing that funded a shareholder payment, so a committee could read the gap as "no credit counter-case exists".
   - Fix: Lead with the strongest credit-substantive evidence that could overturn or widen the bounded historical view, then give the process conditions.
3. **Medium · narrative** (Saboteur)
   - Where: line 72: "discloses both debt bases ... Selected earnings and cash calculations reproduce"
   - Problem: The passage gives no figures, units or periods. The two debt bases (USD 25,068 million principal vs USD 24,880 million carrying, FY2024) and the specific calculations that reproduced are left for the reader to find in another section.
   - Fix: Name the two debt amounts with currency and period, and say which calculations reproduced (e.g. FY2024 free cash flow USD 1,880 million, about 3.60x net cash interest coverage).
4. **Medium · narrative** (New reader)
   - Where: line 72: "completed evidence for any legal or investment decision actually sought"
   - Problem: The "what would change the view" trigger is open-ended. It gives no observable event, document or threshold, so the reader cannot monitor for it.
   - Fix: List each change trigger as a concrete, observable item (which document, which figure, which decision) the reader could check off.
5. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-5_contrary-evidence.png, section block at roughly x 296-840, y 190-395 (display coordinates)
   - Problem: Contrary evidence, the current stance ("This supports bounded historical discussion now") and the change conditions all sit in one unbroken 10-line, roughly 110-word paragraph. The three-part content has no visual separation, unlike the bulleted Key findings and Limitations around it.
   - Fix: Split it into a short contrary-evidence paragraph followed by a bulleted list of change conditions, matching the list treatment of the neighbouring sections.
6. **Low · visual** (Auditor)
   - Where: Crop scratchpad/tmp/CP-5-094-a.png, trailing "Basis" button after "those conditions."
   - Problem: The Basis control is small, light-grey inline text with no icon or underline. It does not look clickable and has weak contrast against the white background.
   - Fix: Give the Basis control a recognisable link or button affordance at body-text contrast.

### Time-aware governance risk and remediation ownership

Kind: prose/table · handoff lines 99-103 · verdict **BLOCK**

- Narrative: Both paragraphs (L100–L102) read as an internal note to the pipeline about which module fixes what: they use banned pipeline vocabulary, put the judgement last, have no Basis lines and do not size the principal/carrying gap.
- Visual: The section has no chart, map or timeline; it is two plain paragraphs set at a very long line length, and the appendix heading that should follow them is not rendered, so the prose runs straight into a dense nine-column register.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: L100: "The legal producer and market-data predecessor own factual remediation; the security-selection producer owns adoption and re-evaluation, and Committee challenge must preserve the current restrictions until re-audit." and L102: "Financial foundation owns the canonical presentation correction ... This validator does not silently replace their ratios."
   - Problem: The reader sees pipeline vocabulary the house standard bans: "producer", "predecessor", "canonical", "validator", "re-audit" and "adoption". Both paragraphs read as a work-allocation note between modules, not as analysis a credit committee can use.
   - Fix: Say what the reader must not assume (for example, that ranking under the filing does not prove recovery) and which module page holds the restriction, without producer, validator or ownership language.
2. **Medium · narrative** (Saboteur + New reader (promoted))
   - Where: L102: "A separate definition risk already exists: principal-based leverage can be carried into a dashboard whose debt stack is carrying-value-based. The first break is comparability, not cash availability"
   - Problem: The paragraph names the risk but gives no size, so the committee cannot judge materiality. The gap on this page is carrying debt of USD 24,880 million against principal of USD 25,068 million (Top five driver ranking, row 3), about USD 188 million, and the reader cannot tell whether this matters.
   - Fix: State the size of the gap (amount, period and both bases) next to the claim, and say whether it moves leverage enough to matter.
3. **Medium · narrative** (Saboteur)
   - Where: L100: "An unsupported promotion of filing-summary seniority into a recovery recommendation would first break the protection assumption, then distort expected loss or tranche preference, and ultimately contaminate a committee trade decision."
   - Problem: The paragraph opens with a hypothetical failure chain. The actual judgement (keep the legal and market limits until the operative documents are reviewed) comes last, in its last sentence, which breaks judgement-first ordering.
   - Fix: Open with the conclusion (security preference and recovery cannot be relied on until the operative documents and market data are available), then give the trigger.
4. **Medium · narrative** (New reader)
   - Where: L99 heading: "Time-aware governance risk and remediation ownership"
   - Problem: To a portfolio manager, "governance risk" means the issuer's corporate governance, but this section is about how the analysis itself could be misused. "Time-aware" and "remediation ownership" are internal framing with no meaning to the reader.
   - Fix: Use a plain heading that says what the section is, such as "Conclusions that must not be over-read".
5. **Medium · narrative** (Auditor)
   - Where: L100–L102, both paragraphs (rendered at the top of shots/CP-5_s-99.png, about y 230–400 at original scale)
   - Problem: Both paragraphs make factual claims (filing-summary seniority, a principal-based numerator against a carrying-value dashboard) but neither has a Basis line, so the reader cannot trace either claim. This breaks the rule that source references sit in each paragraph's Basis line.
   - Fix: Add a Basis line under each paragraph that points to the filing pages and figures it relies on.
6. **Medium · visual** (Auditor + New reader)
   - Where: shots/CP-5_s-99.png, the end of the section into "Source register and source gate" (about y 400–450 at original scale); DOM render/CP-5.dom.html, where s-99 is followed directly by the s-106 h5
   - Problem: The handoff's L104 heading "Analytical appendix — complete canonical registers" is not rendered (0 matches in the DOM). The narrative therefore runs straight into a dense nine-column source register with no boundary, and the reader cannot see where the judgement ends and the appendix begins.
   - Fix: Show a visible appendix divider or heading, in reader language, between this section and the registers.
7. **Low · narrative** (New reader)
   - Where: L102: "Fundamental credit synthesis and Relative value and security selection own explicit adoption."
   - Problem: Two module names are chained with "and" and capitalised mid-sentence, so the sentence parses as three or four subjects and needs re-reading.
   - Fix: Remove the module ownership sentence, or refer to the affected pages by their on-screen names in a separate clause.
8. **Low · visual** (New reader)
   - Where: shots/CP-5_s-99.png, the two paragraphs at the top (crop tmp/CP-5-098-a.png)
   - Problem: Body text runs about 1,100 px wide, roughly 170 characters per line. Combined with long compound sentences, the two paragraphs read as a dense wall even though they are short.
   - Fix: Cap prose line length at about 75–90 characters, as module narrative sections do in the VMO2 reference.

## Committee decision (CP-6)

Handoff: `/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-reader-format-001/requests/CP-6/65510b7dddd53992a399375adb71437c30fe7996c115f53b529fcb3af1fd3697/1.response.md`

### Bull opening and defense — steps 3 and 5

Kind: prose/table · handoff lines 150-165 · verdict **BLOCK**

- Narrative: The section is two tables after a one-line, process-flavoured lead with no judgement. On screen it shows the banned word 'canonical', the code C06 and step numbering, and the key cash figures lack a named payment or basis.
- Visual: There is no chart in this section. The two bordered tables are tidy and legible, but the narrow, repetitive Source column makes rows tall, and the inline 'Basis' button is faint and runs into the label text.

1. **High · narrative** (Auditor, Saboteur)
   - Where: line 152: "Exactly three claims are advanced; the third is a bounded timing claim, not an invented RV recommendation." (the section's only lead sentence)
   - Problem: The section opens with a remark about how the debate was built, not with a judgement. The verdict on the Bull case (all three claims only 'Partially Rebutted', so the Bull case does not hold up for creditors) sits only in the last columns of the second table. A reader skimming the opening comes away with no view.
   - Fix: Open with a one-sentence bottom line on how much of the Bull case survives (servicing supported, retention and access not), then the tables.
2. **High · narrative** (Auditor, New reader)
   - Where: line 154 column header "Canonical credit implication"; line 150 heading "— steps 3 and 5"; line 157 Source "Financial foundation (CP-1), C06" (rendered as 'C06' in the Source cell)
   - Problem: The banned pipeline word 'canonical', a register code 'C06' and debate-procedure step numbers all show on screen. A committee reader cannot decode any of them.
   - Fix: Rename the column to 'Credit implication', drop 'steps 3 and 5' from the heading, and replace C06 with a reader-facing source description.
3. **High · narrative** (Saboteur, New reader)
   - Where: line 157: "Payment-only cash USD 1,913 million remains positive versus reported USD 6,261 million. This rebuts an assertion that the specified payment alone exhausts cash"
   - Problem: 'Payment-only cash' and 'the specified payment' are never named here: not which payment, its size or the date. The USD 1,913 million cannot be checked against the USD 6,261 million, and the reader cannot tell how big the drain on cash was.
   - Fix: Name the payment, its amount and the date it was paid, and state the cash figure as reported cash at FY2024 year-end less that payment, with the period.
4. **Medium · narrative** (Saboteur)
   - Where: lines 156-158: "Neutral — Stable" given for all three Bull claims B1, B2 and B3
   - Problem: Every Bull claim carries the same 'Neutral — Stable' implication, so the column tells the reader nothing about which claim matters. A reader may also take 'Stable' as a positive outlook call, even though each claim is later only partially rebutted.
   - Fix: Either give each claim the implication it actually supports, or drop the uniform column and state the shared implication once in the lead sentence.
5. **Medium · narrative** (Saboteur)
   - Where: line 158: "FY2025 long-term principal USD 93 million precedes FY2028 USD 6,637 million. This gives time for internally funded servicing before a larger reported funding bucket"
   - Problem: A USD 6.6 billion maturity cluster is called 'a larger reported funding bucket' and framed as time gained. The size of the wall relative to FY2024 FCF of USD 1,880 million (line 156) and to cash is never set out, which plays down the refinancing risk.
   - Fix: State the FY2028 amount as a multiple of FCF or of cash, and say how many years of runway it implies, so the timing claim is weighed against the cliff.
6. **Medium · narrative** (New reader)
   - Where: line 156: "net cash-interest coverage approximately 3.60x are realized resources after interest/tax and before acquisitions/distributions"; line 152 "RV"
   - Problem: The coverage ratio is called 'approximately' but given to two decimals, with no stated numerator or period. 'RV', 'FCF' and 'transmission' are used without definition. The prose is clipped and missing full stops (lines 156-164), which reads like notes rather than committee prose.
   - Fix: Define the ratio (for example FY2024 operating cash flow over net cash interest) with a consistent precision, spell out the abbreviations once, and write complete sentences.
7. **Medium · visual** (New reader, Auditor)
   - Where: Claim table, shot CP-6_s-150.png, crop at x 340-1400 and y 220-700 (CP-6-116-a.png): Source column, e.g. "Financial foundation; Business and transaction context (Business & governance)" and "Fundamental credit synthesis (Fundamental credit)"
   - Problem: The narrow fifth column wraps each source onto four or five lines and repeats the module name twice (long name plus short name in brackets). This makes the rows tall and the Invalidation column hard to scan.
   - Fix: Use one short source name per module and give the Source column less width priority than the opening/transmission column, so each row fits in two or three lines.
8. **Low · visual** (Auditor)
   - Where: Both tables, shot CP-6_s-150.png at around y 280-780 (display): the grey 'Basis' button inline after the claim and attack labels (e.g. "B1 Cash conversion supports current servicing Basis")
   - Problem: The low-contrast 'Basis' control runs into the claim label as if it were part of the text. Its role (open the sources) is not obvious, and it is easy to misread 'time Basis' as a phrase.
   - Fix: Show Basis as a clearly separate chip or icon with enough contrast, set apart from the label text.

### Compliance attack summary and CIO decision — steps 4 and 8–10

Kind: prose/table · handoff lines 207-216 · verdict **BLOCK**

- Narrative: The decision itself is clear and appropriately cautious (Requires More Work, neither side wins, no size), but it is buried after a process recital. It is restated four times, and the text leaks pipeline vocabulary ("canonical", "gate", "priority-twelve", "steps 4 and 8–10") and gives no Basis lines.
- Visual: There is no chart in this section. The four dense full-width paragraphs give no visual emphasis to the posture and flow directly into the appendix tables with little separation.

1. **High · narrative** (Auditor, Saboteur)
   - Where: line 211: "Canonical translation: Requires More Work maps to Requires More Work."; line 215: "The CIO final memo is Requires More Work, mapped identically to the canonical posture"
   - Problem: This is pipeline vocabulary ("canonical", "maps to") shown on screen, confirmed in render/CP-6.dom.html. It also says nothing: a posture mapped onto itself gives the committee no information and makes it look as if a second, hidden posture exists.
   - Fix: Delete the mapping sentences and state the posture once, in plain words, as the decision.
2. **High · narrative** (Auditor, Saboteur)
   - Where: line 209: "Compliance successfully prevents unsupported inclusion, but does not prove a mandate breach or that yield is inadequate. All relevant constraint tests were attempted:"
   - Problem: The section opens with a list of the process steps. The decision ("Final Sizing Posture: Requires More Work") only arrives in paragraph 2 and is repeated in paragraph 4. This breaks the judgement-first order, and a skimming reader can take the Compliance sentence for the outcome.
   - Fix: Open with one bottom-line sentence (Requires More Work, neither side wins, no size), then the drivers, then what would change it.
3. **High · narrative** (Auditor, New reader)
   - Where: line 213: "The implementation gate is the priority-twelve data-quality limitation preventing decision-useful sizing... then test the twelve-type priority order."; line 215: "The implementation gate is data quality"
   - Problem: "Gate" is banned pipeline vocabulary. "Priority-twelve" and "twelve-type priority order" refer to an internal constraint taxonomy that is never defined on the page, so the reader cannot tell what limits anything.
   - Fix: Say in plain words that the missing data (no mandate, holdings or budget) is what stops sizing, and drop the internal priority numbering.
4. **Medium · narrative** (New reader, Auditor)
   - Where: Heading line 207: "Compliance attack summary and CIO decision — steps 4 and 8–10"
   - Problem: "Steps 4 and 8–10" refers to an internal debate protocol that the reader has never seen. It also appears in the On-this-page navigation in the screenshot.
   - Fix: Use a reader heading such as "Portfolio decision and sizing" without step numbers.
5. **Medium · narrative** (New reader)
   - Where: line 209: "issuer/sector/sponsor/country/currency/rating/instrument concentration, CCC/downgrade, correlation, exit liquidity, downside budget, maturity/refinancing/LME"; line 215: "There is no sufficient RV bullet"
   - Problem: Long slash-chains and undefined abbreviations (LME, RV, NAV, CCC) make the passage read like a checklist dump. A portfolio manager has to decode it instead of reading a judgement.
   - Fix: Spell out or drop the abbreviations and replace the slash-chain with a short sentence on which tests could not be run and why.
6. **Medium · narrative** (Saboteur)
   - Where: line 215: "The CIO final memo is Requires More Work... with Neither winning the investment merits... Revisit only after matched compensation, mandate/exposure/budget, legal/downside and tradability evidence are adopted."
   - Problem: Paragraph 4 restates paragraphs 2–3: the posture, Neither wins, the missing inputs and the absence of a size. "Requires More Work" appears four times in the section, which dilutes the one actionable list of what would change the view.
   - Fix: Merge paragraphs 2–4 into one decision paragraph and one short "what would change the view" list.
7. **Medium · narrative** (Auditor)
   - Where: lines 209–215: the four paragraphs, e.g. "the strongest supportive context is the issuer's servicing cash... residual risks are allocation-sensitive cash, later funding concentration and unverified loss protection"
   - Problem: None of the four paragraphs has a Basis line (the screenshot shows none). Factual claims about servicing cash and funding concentration therefore have no source the reader can check.
   - Fix: Add a Basis line under each paragraph that names the upstream analysis it relies on.
8. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-6_s-207.png, region x 290–1160, y 190–505 (displayed); then the "Bear cross-examination" table starting about y 525
   - Problem: The section renders as four unbroken prose blocks of about 5 lines each at full 870 px width, with no visual marker for the decision (posture or winner). It then runs straight into the appendix tables with only a small bold label, so the decision is visually indistinguishable from appendix material.
   - Fix: Show the posture as a highlighted bottom-line line or chip at the top of the section and add a clear break or heading before the appendix registers.

### Analytical appendix — complete canonical registers

Kind: register appendix · handoff lines 217-309 · verdict **BLOCK**

- Narrative: This is a data appendix of seven registers that never states its bottom line. It defines no score scale, its gap ledgers are written in pipeline workflow language, and module codes (CP5-001/CP5-002) and broken \"method step\" references still reach the reader.
- Visual: The assigned screenshot shows the top of the module page, not this section, because the appendix heading has no rendered anchor. Table layout (column widths, wrapping, density of the 8-column tables) could not be checked from the screenshot; only the rendered DOM was checked.

1. **High · narrative** (Saboteur, New reader)
   - Where: Chair evidence weighting, line 237: "| Sponsor/governance alignment | 5 | ... | Bear clearly superior on observed issuer cash retention ..."; line 231: "| Cash-flow durability | 2 | ... | Bull somewhat stronger ..."; line 241: "analyst adjudications under the supplied scale"
   - Problem: The 1-5 score's direction is never defined on the page or in the handoff; the only gloss is "the supplied scale" (line 241). A 5 on governance alignment, where the assessment says the Bear is clearly superior, reads as strong alignment, and a 2 on cash-flow durability sits beside "Bull somewhat stronger". A committee reader cannot tell whether a high score is good or bad for the credit.
   - Fix: Put a one-line scale legend above the table (for example "1 = Bull clearly superior ... 5 = Bear clearly superior") so each score reads the same way as its assessment.
2. **High · narrative** (Auditor, New reader)
   - Where: Issuer debate gaps ledger, line 262 (rendered as Gap 6): "CP5-001/CP5-002 unresolved; source contracts/censuses missing for full cross-producer grading"; Portfolio gaps ledger, line 308 (rendered Gap 7): "CP5-002 unresolved"
   - Problem: The module-code relabelling misses the codes CP5-001 and CP5-002, so module codes still appear on screen (confirmed in render/CP-6.dom.html). The house rule bans any CP code on screen, and the reader cannot tell what these two findings are.
   - Fix: Name the two open findings in reader terms (for example "evidence-validation finding on default leverage presentation") and drop the codes.
3. **High · narrative** (Auditor, New reader)
   - Where: Line 257: "Financial/downside factual predecessors to provide cash-backed scenario ... CP-6 consumes after producer analysis" (rendered "Committee decision consumes after producer analysis"); also lines 258-308 "predecessor", "re-challenge", "cross-producer grading", "portfolio gate", "failed gate"
   - Problem: Every Required Follow-Up cell in both gap ledgers is written in pipeline vocabulary (predecessor, producer, consumes, gate, re-audit, adopt). The rendered DOM has 18 "producer" and 18 "predecessor" hits. A PM reads these as a workflow to-do list, not as the information the committee lacks.
   - Fix: Rewrite each follow-up as the evidence needed (for example "an accessible-cash bridge under a downside case"), with no reference to which internal step supplies it.
4. **Medium · narrative** (Auditor, Saboteur)
   - Where: Line 270 Source cell "Relative value and security selection (CP-3), T3.5/T3B.7" rendered "Relative value and security selection, method steps"; line 295 Evidence Basis "CP-3 T3B.4; CP-4 Blocked" rendered "Security selection a method step; Legal & covenants Blocked"
   - Problem: Stripping the register codes leaves references that point at nothing ("a method step", "method steps"), so the reader cannot trace the cited evidence. The Evidence Basis column also repeats source references outside the Source column, for example "Financial foundation C03/C05" (line 247).
   - Fix: Replace code references with the named finding or table they point to, and keep source references in the Source column only, leaving Evidence Basis as the substantive reason.
5. **Medium · narrative** (New reader)
   - Where: Line 223: "A1: B1 servicing cash"; line 270: "P1: R1 pickup"; line 232: "no proven Zero-Bound"; line 239: "context, page 1"
   - Problem: The row labels A1/B1, P1/R1 and the term "Zero-Bound" are internal debate keys that this section never defines. "context, page 1" is not an identifiable source for a reader who has not seen the request.
   - Fix: Label rows by the claim in plain words (for example "Bull: current cash flow services debt"), define or drop Zero-Bound, and name the actual document behind "context".
6. **Medium · narrative** (Saboteur, New reader)
   - Where: Line 217: "### Analytical appendix — complete canonical registers" followed by seven tables (lines 219-308) with only two short trailing notes (lines 241, 288)
   - Problem: The section has no bottom line. Seven dense tables (up to 8 columns, two gap ledgers both numbered "Gap 1...") run straight on from the CIO decision, and the reader is never told what the registers add or which rows matter for the decision. The heading itself uses the banned word "canonical".
   - Fix: Open the appendix with a one- or two-sentence bottom line that names its decisive rows, rename it without "canonical", and give the two ledgers distinct IDs (Issuer gap 1 vs Portfolio gap 1).
7. **Medium · visual** (Auditor, New reader)
   - Where: Screenshot shots/CP-6_s-217.png (whole frame, 0-2400 px), and render/CP-6.dom.html (no id="s-217"; the appendix heading text is absent; nav goes straight from "Compliance attack summary..." to "Bear cross-examination")
   - Problem: The appendix heading is not rendered and has no anchor, so the section's link lands at the top of the module page. On screen the seven register tables look like more of the main analysis rather than a labelled appendix, and the reader loses the cue that this is supporting detail.
   - Fix: Render the appendix heading with its own anchor and a visible divider, and list it in "On this page" as a parent of the seven tables.
8. **Low · narrative** (New reader)
   - Where: Line 237 Source: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 54" (also line 248)
   - Problem: The source is shown as a raw extraction file name with an accession number and a .jsonl suffix, not as a document a reader would recognise.
   - Fix: Show it as "TransDigm FY2024 Form 10-K, p. 54".

### Front matter + Request + Next module

Kind: run plumbing · handoff lines 1-36, 37-39, 390-395 · verdict **BLOCK**

- Narrative: This unit is run plumbing (front matter, the request sent to the model, and next-step routing). None of it is credit narrative, yet all of it reaches the reader in pipeline vocabulary, and the code-to-name label substitution produces a self-contradicting sentence about whether a Committee decision run is needed.
- Visual: There is no chart in this section. The front matter renders as a dense unstructured wall of YAML keys, flags and hashes, and it shows a run_id that disagrees with the page header; the Request and Next module paragraphs are typographically clean but should not be on the reader page.

1. **High · narrative** (Saboteur, Auditor)
   - Where: Rendered Next module: "No separate Committee decision run is required." (handoff l.392: "No separate CP-6A run is required.")
   - Problem: Replacing module codes with names turned 'CP-6A' into 'Committee decision', so the rendered sentence says no separate Committee decision run is needed. That is false and contradicts the next paragraph, which calls for 'the next full Committee decision challenge'.
   - Fix: Drop the CP-6A sentence or map CP-6A to its own distinct reader name, so the label substitution never produces a sentence that contradicts itself.
2. **High · narrative** (Auditor, New reader)
   - Where: Next module l.394: "Run CP-1 after producer-owned carrying-default remediation inputs are available, then adopt the correction in the fundamental/security producers and rerun Evidence validation ... rerun the affected owners"
   - Problem: The whole section is pipeline run plumbing written for the orchestrator: 'Recommended next command', 'producers', 'owners', 'Markdown artifact', 'fresh receipt', 'fabricated review date'. The house standard says this vocabulary is not reader language, and a credit committee member gets no credit content from it.
   - Fix: Either hide Next module from the reader page or restate it as one plain sentence on what evidence would let the committee move from 'Requires More Work' to a decision.
3. **High · visual** (Auditor, New reader)
   - Where: Front matter block, CP-6_s-1.png y~190-390 (display), rendering handoff lines 1-35, e.g. "module_name: ICDebateChallenge ... limitation_flags: - HISTORICAL_CHALLENGE_ONLY - DEPENDENT_LEGAL_DECISIONS_WITHHELD - OPEN_PRODUCER_QA_RESTRICTIONS" (l.4, 18-21)
   - Problem: The raw YAML front matter appears on the Modules page as one run-together paragraph: snake_case keys, internal class names, SCREAMING_SNAKE flags containing 'PRODUCER', and seven 64-character sha256 hashes. It is pipeline metadata that no reader can use, its list structure is lost, and 'Front matter' is listed in the On this page nav as if it were a reader section.
   - Fix: Keep the front matter out of the reader page, or render only a small labelled status strip (status, confidence, as-of date) in plain words, with no hashes or flag codes.
4. **Medium · narrative** (Saboteur)
   - Where: Front matter l.11-16 and Next module l.392: "module_status: Ready with Limitations / committee_status: Requires More Work / qa_status: Restricted / confidence_score: 17"
   - Problem: The reader gets three competing status words ('Ready', 'Requires More Work', 'Restricted') with no explanation of how they relate. A skimming reader may take 'Ready with Limitations' as clearance, when the actual committee outcome is no decision and confidence 17/100.
   - Fix: Lead with the single committee outcome (Requires More Work; confidence 17/100, insufficient information) and keep the internal readiness status off the reader page.
5. **Medium · narrative** (New reader)
   - Where: Request l.38: "Conduct the issuer investment-committee challenge and absorbed terminal portfolio debate, adjudicate the strongest supported cases, and determine action bias ... pathway: credit_snapshot"
   - Problem: The Request is the instruction the model was sent, written in method jargon ('absorbed terminal portfolio debate', 'action bias', 'pathway: credit_snapshot') that the reader has no way to decode.
   - Fix: Render the request as one plain-English scope line (e.g. the committee question for TDG as of 30 September 2024 on FY2024 evidence), or leave it out of the reader page.
6. **Medium · visual** (Saboteur, Auditor)
   - Where: CP-6_s-1.png: page header 'Showing run: TDG-READER-FORMAT-001' (y~160) vs front matter 'run_id: tdg-2024-09-30-credit_snapshot-sol-medium' (l.7, y~220)
   - Problem: The same page shows two different run identifiers, so a reader cannot tell which run produced this module's content.
   - Fix: Show one run identity, the one in the page header, and suppress the module's internal run_id.
7. **Low · visual** (New reader)
   - Where: On this page nav, CP-6_s-1.png and CP-6_s-390.png x~95-250, entries 'Front matter', 'Request', 'Next module'
   - Problem: Three plumbing sections take up nav entries next to analytical sections, making a 30-plus-entry nav even longer to scan.
   - Fix: Remove the plumbing sections from the nav, or group them under a single collapsed 'Run details' entry.

### Bottom line

Kind: reader passage · handoff lines 58-64 · verdict **BLOCK**

- Narrative: The bottom line comes first and states a judgement, but the judgement is wrapped in Bull/Bear debate language and internal status labels. Its key coverage figure has no basis, the main risk has no figure, and the second paragraph restates the first.
- Visual: There is no chart in this section. Visually, about 170 words are set in bold headline type, figures switch to monospace, and the first paragraph's Basis link is missing on screen (confirmed in CP-6.dom.html) while the second paragraph has one.

1. **High · narrative** (New reader, Auditor)
   - Where: Line 59 "the Bull wins historical servicing support"; line 62 "The final issuer action bias and portfolio posture are both Requires More Work. Neither side wins the complete investment debate: the Bear establishes..."
   - Problem: The verdict is framed as a scored debate between Bull and Bear personas, and it uses internal register labels ("action bias", "portfolio posture", the status string "Requires More Work"). A committee member who does not know the pipeline has to work out who the Bull and Bear are and what these labels mean before the decision becomes clear.
   - Fix: State the committee position in plain credit terms (for example, no position until X and Y are verified) and drop the debate-scoring and register-label vocabulary from the bottom line.
2. **High · visual** (Auditor, Saboteur)
   - Where: Handoff line 60 "Basis: Financial foundation (CP-1); Fundamental credit synthesis (CP-2); Relative value and security selection (CP-3); Evidence validation (CP-5)"; screenshot CP-6_bottom-line.png, first headline paragraph (y about 190-450)
   - Problem: The first Bottom line paragraph has no Basis link on screen. The rendered DOM ends that <p class="passage-text"> without a basis-link button, while the second paragraph has one, so the paragraph that carries the verdict and the USD 1,880 million / 3.60x figures shows no source. That breaks the rule that every paragraph has a Basis line. The basis survives only inside the figure buttons' data-basis.
   - Fix: Render the line-60 Basis as a visible Basis link at the end of the first paragraph, as the second paragraph already does.
3. **Medium · narrative** (Saboteur)
   - Where: Line 59 "approximately 3.60x coverage of net cash interest rebut an immediate funding-failure thesis"
   - Problem: The 3.60x is issuer-adjusted EBITDA divided by net cash interest (CP-1 and CP-2 say so), but the bottom line drops the numerator. A reader will take it as a reported or unadjusted coverage figure, which overstates how firm the main pro-servicing number is.
   - Fix: Name the measure in the sentence (issuer-adjusted EBITDA to net cash interest, FY2024) so the figure carries its basis and period.
4. **Medium · narrative** (Saboteur)
   - Where: Line 59 "They do not establish retained deleveraging when new secured debt financed shareholder extraction and acquisitions competed for internal cash."
   - Problem: The main credit risk named here (debt-funded payouts, leverage) is left unsized: the bottom line gives two strength figures but no leverage multiple and no payout or new-debt amount. Those (USD 3,000 million of new secured debt, about USD 4,348 million of dividends) appear only lower down, so the bottom line weighs a quantified positive against an unquantified negative.
   - Fix: Put one sized figure for the risk side (leverage or the debt-funded distribution) into the bottom line next to the cash-flow figures.
5. **Medium · narrative** (New reader)
   - Where: Line 59 "compensates for equity-directed cash use and unverified loss protection"; line 62 "whether instrument-level compensation and verified downside protection together absorb the issuer's allocation-sensitive leverage"
   - Problem: Abstract nominal phrases ("equity-directed cash use", "allocation-sensitive leverage", "instrument-level compensation") and sentences of 35 words or more make the bottom line hard to read in one pass. The reader cannot tell what concrete test is outstanding (spread versus peers? covenant terms?).
   - Fix: Name the two missing pieces of evidence concretely (security pricing against peers; executed covenant and collateral terms) in short sentences.
6. **Medium · narrative** (Saboteur)
   - Where: Line 59 "The committee should preserve the cash-generative fundamental view while withholding a preferred tranche, trade or position size."; line 62 "The final issuer action bias and portfolio posture are both Requires More Work."
   - Problem: The second paragraph mostly repeats the first paragraph's verdict and adds a closing caveat ("missing evidence is a reason to abstain... not evidence that the securities are intrinsically unattractive"). The committee gets no explicit hold, avoid or buy answer, only 'preserve the view' plus 'withhold', which a reader can take as either mildly positive or neutral.
   - Fix: Lead with one unambiguous action sentence, followed by the single condition that would change it, and cut the restatement.
7. **Medium · visual** (New reader)
   - Where: Screenshot CP-6_bottom-line.png, both headline paragraphs (y about 190-740 at displayed scale), class reading-headline
   - Problem: About 170 words across two paragraphs are set in large bold headline type, which reads as a block of bold with no hierarchy. The second, more qualifying paragraph gets the same weight as the verdict, so the eye cannot find the one-line judgement.
   - Fix: Keep headline type for the opening judgement sentence or the first paragraph only, and set the rest in body weight.
8. **Low · visual** (Auditor)
   - Where: Screenshot CP-6_bottom-line.png, figures "USD 1,880 million" and "3.60x" inside the bold headline (y about 290-310)
   - Problem: Inline figures switch to a monospace code font with dotted underlines in the middle of the bold headline. The jump in typeface and the uneven spacing look like code rather than numbers in prose.
   - Fix: Render the clickable figures in the surrounding typeface (tabular numerals) with a subtler affordance.

### Key findings

Kind: reader passage · handoff lines 65-74 · verdict **BLOCK**

- Narrative: The figures are exact and carry units and fiscal periods, but two bullets of the section break the standard. Pipeline wording leaks to the reader ('canonical', 'Producer-owned corrections'), one bullet is a note on method rather than a finding, and the bold lead-ins score a Bull/Bear debate instead of judging the credit.
- Visual: The section has no chart. It renders as a readable bulleted list with bold lead-ins and figure chips, but it lacks the visible Basis markers that the paragraphs beside it carry, and one wrap leaves a full stop at the start of a line.

1. **High · narrative** (Auditor, New reader)
   - Where: Line 72: "Carrying debt of USD 24,880 million is the canonical financial amount in this debate; ... Producer-owned corrections remain open." (rendered verbatim in CP-6_key-findings.png, 4th bullet)
   - Problem: "canonical" and "Producer-owned corrections" are pipeline words the house standard bans, and they reach the reader on screen (confirmed in render/CP-6.dom.html). A PM cannot tell which corrections are open, who owns them, or whether they change leverage.
   - Fix: Name the open issue in credit terms, e.g. that the leverage ratios based on principal have not been confirmed, and drop the producer and canonical wording.
2. **High · narrative** (Saboteur, New reader)
   - Where: Line 72: "Definition discipline prevents a false investment resolution." (whole 4th bullet)
   - Problem: This 'key finding' describes the module's own method (which debt definition it used, which grades it refused), not a credit finding about TransDigm. It takes a key-findings slot and leaves two debt totals, USD 24,880 million and USD 25,068 million, with no stated leverage consequence. A reader may cite either number.
   - Fix: Either state what the gap between carrying debt and principal means for leverage, as a credit finding, or move this method note to Limitations.
3. **Medium · narrative** (New reader)
   - Where: Line 66: "Operating cash flow is the Bull's strongest evidence, but its victory is narrower than a long recommendation."; line 70: "The Bear cannot equate ... but the Bull cannot extrapolate"
   - Problem: The bold lead-ins frame each finding as a scored Bull/Bear debate, not as a judgement on the credit. A committee reader skimming the bold text learns who won a debate it never saw, not what is true of TDG's credit quality.
   - Fix: Make each bold lead-in a direct credit judgement on the issuer (e.g. "FY2024 free cash flow covers servicing but is not retained for paydown"), with the debate framing kept out of the headline.
4. **Medium · narrative** (Saboteur)
   - Where: Line 68: "The payment-only cash illustration is USD 1,913 million, rather than reported cash of USD 6,261 million. That illustration isolates the committed use; it is neither an actual October balance nor a stress runway."
   - Problem: An undefined constructed figure sits next to the reported balance and is then disowned in the next sentence. The reader cannot rebuild it (it is USD 6,261 million less USD 4,348 million) or see why it matters. The USD 3,000 million and USD 4,348 million also have no transaction date or period.
   - Fix: Say in one clause that this is reported cash less the declared dividend payment, and give the date of the dividend and the debt raise.
5. **Medium · narrative** (New reader)
   - Where: Line 70: "Reported long-term principal is USD 93 million in FY2025 versus USD 6,637 million in FY2028 ... across obligations excluded from that schedule."
   - Problem: FY2026 and FY2027 maturities are skipped, so the reader cannot judge the shape of the maturity profile. "Obligations excluded from that schedule" is never named, so a reader would have to open another page to learn what is missing.
   - Fix: Give the full FY2025–FY2028 sequence, or say that the intervening years are smaller, and name the excluded obligation types in a few words.
6. **Medium · visual** (Auditor)
   - Where: CP-6_key-findings.png, Key findings list (crop scratchpad/tmp/CP-6-109-a.png, y≈220-790 at display scale) compared with the 'Basis' marker after the Contrary evidence and Limitations paragraphs
   - Problem: None of the four key-finding bullets shows a visible Basis marker, while the paragraphs below it do. In the DOM the basis exists only as data attributes on the figure buttons. Bullet 2 cites filing page 54 and the reader cannot see that on the page.
   - Fix: Render the same visible Basis marker at the end of each key-finding bullet, as the prose paragraphs already have.
7. **Low · visual** (Auditor)
   - Where: CP-6_key-findings.png, bullet 2: line break after "USD 6,261 million" leaves ". That illustration ..." starting a new line
   - Problem: The full stop wraps away from the figure chip and opens the next line, which looks broken. The monospaced, dotted-underlined chips also make sentences with four figures look busy.
   - Fix: Keep trailing punctuation joined to the figure chip (no-wrap) so a line never starts with a full stop.

### Limitations

Kind: reader passage · handoff lines 79-84 · verdict **BLOCK**

- Narrative: This section has two bullets. Both are hard to read: the debate personas and pipeline wording (\"producer QA\", \"canonical\", \"upstream\") break the house rule, and the passage does not say plainly that the legal analysis was blocked or how large the disputed leverage difference is.
- Visual: There is no chart in this section. On the page it shows as two bulleted paragraphs with Basis links, set in a narrow column, with too little space before the Timeline heading that follows.

1. **High · narrative** (Auditor + New reader)
   - Where: Line 82: "Open producer QA findings constrain this committee's evidentiary weighting: ... cannot be promoted as settled canonical decision inputs. ... without representing either upstream issue as corrected."
   - Problem: "producer", "canonical" and "upstream" are pipeline words the house standard bans from reader text, and "QA findings" and "confidence census" are internal process labels. They appear on screen as written (screenshot CP-6_limitations.png, second bullet).
   - Fix: State the limitation in credit terms, e.g. that the leverage ratios computed on principal and the confidence grade from the security analysis are still disputed and were not used, with no pipeline vocabulary.
2. **High · narrative** (Saboteur)
   - Where: Line 80: "The Chair cannot adjudicate the joint compensation-versus-loss-protection test from the supplied record." Basis: Legal Covenant Interpreter (CP-4)
   - Problem: The real limit is that the legal and covenant analysis was blocked and never completed. The same page shows this only in the Sources table ("Blocked handoff, not completed legal interpretation") and in the side nav ("Not assessable"). "Supplied record" hides it, and citing the legal module as Basis suggests covenant terms were reviewed.
   - Fix: Name the missing inputs plainly in the limitation: executed legal terms not reviewed and instrument or peer pricing not matched, and say that is why no recommendation is possible.
3. **Medium · narrative** (Saboteur)
   - Where: Line 82: "inherited principal-based leverage and the disputed security-analysis confidence grade cannot be promoted as settled"
   - Problem: The limitation does not say how big the leverage difference is or which figure the reader should rely on. The two debt bases (USD 24,880 million carrying, USD 25,068 million principal) are given only in Key findings, so a committee member cannot tell whether this limitation is material.
   - Fix: Give the two debt bases and their gap, with unit and as-of date, and say which one the verdict uses.
4. **Medium · narrative** (New reader)
   - Where: Line 80: "This limits the verdict to a partial Bull victory on servicing and a partial Bear victory on retention, rather than a winner entitled to an executable investment recommendation."
   - Problem: "The Chair", "Bull" and "Bear" debate roles, and "joint compensation-versus-loss-protection test", are debate shorthand that is never defined for a reader who has not seen the debate. The sentence also repeats the bottom line instead of stating what the evidence could not support.
   - Fix: Use plain credit language (e.g. "we cannot yet tell whether spread compensates for unverified downside protection") and keep this passage to what is limited and why.
5. **Medium · visual** (Auditor)
   - Where: Screenshot CP-6_limitations.png, about y=420-445 (original px): the Timeline heading sits directly under the last Limitations bullet ("corrected. Basis")
   - Problem: There is almost no vertical space between the end of Limitations and the Timeline heading, so the timeline reads like part of the Limitations list. Other section breaks on the page have clear spacing and dividers.
   - Fix: Use the same top margin before Timeline as before the other h3 sections so that Limitations visibly ends.
6. **Low · visual** (New reader)
   - Where: Screenshot CP-6_limitations.png, Limitations bullets at about x=360-990 (original px), with an empty right half
   - Problem: The Limitations bullets are set in a narrow column (about 530 px) while the other prose sections on the page (Committee challenge, Sources note) run full width. This leaves a large empty band and makes the page look uneven.
   - Fix: Use one text width for all prose sections on the module page.

### Committee challenge

Kind: prose/table · handoff lines 85-88 · verdict **CONCERNS**

- Narrative: The judgement in this section holds together, but it sits after Limitations and Sources, uses internal-debate vocabulary ('implementation abstention', 'sourced pickup', 'the Bull/Bear'), never names the 'Requires More Work' verdict, and refers to an 'assumed holding' that the run never supplied.
- Visual: There is no chart in this section. It renders as one wide, dense paragraph with an inline Basis link, and nothing visually separates it from the empty data tables that follow. Not verified: whether the Basis popover shows the CP-x codes held in the data-basis attribute (the DOM has 'Financial foundation (CP-1)' and others; the popover was not opened).

1. **High · narrative** (Saboteur, Auditor)
   - Where: "### Committee challenge" (line 85), which follows Limitations (line 79) and, on the page, Timeline, Front matter, Request and Sources (CP-6_s-85.png, left 'On this page' list, y≈690–915)
   - Problem: The paragraph that states the committee's decisive question and its burden test comes after the limitations and after the Sources list. A reader who stops at Limitations or Sources never reaches it, and the house order (bottom line, key findings, contrary evidence, limitations, then Sources at the end) is broken.
   - Fix: Put the decisive question into the bottom line or key findings, or place this section before Limitations, and keep Sources as the last reader section.
2. **High · narrative** (New reader, Auditor)
   - Where: "The portfolio challenge reaches the same implementation abstention independently: no sourced pickup, verified headroom or exit capacity supports an allocation, and no sourced breach justifies trimming" (line 86)
   - Problem: This is internal process language that is never defined: 'the portfolio challenge', 'implementation abstention', 'sourced pickup', 'sourced breach', and 'Bull'/'Bear' used as if they were named parties. A portfolio manager who did not watch the internal debate cannot tell who these actors are or what spread 'pickup' refers to.
   - Fix: State it in reader terms, for example: with no spread comparison against peers, no mandate headroom and no liquidity evidence, there is no case to buy or sell. Name the bull and bear cases as viewpoints, not as actors.
3. **Medium · narrative** (Saboteur)
   - Where: "Neither burden is satisfied for an investment decision, although both historical operating support and demonstrated extraction survive challenge." (line 86)
   - Problem: The section never states the outcome label that the bottom line uses ('Requires More Work', line 62). It ends on a balanced 'although' clause, so a committee member reading only this section is left without an action.
   - Fix: Open with the verdict ('Requires More Work: neither case is proven') and then give the two burdens.
4. **Medium · narrative** (Saboteur)
   - Where: "no sourced breach justifies trimming an assumed holding" (line 86)
   - Problem: Per line 93, the run supplied no holdings. Talking about 'trimming an assumed holding' suggests a position exists or was modelled, which contradicts the portfolio table directly below.
   - Fix: Say that no holding was supplied, so neither a reduction nor an addition can be assessed.
5. **Medium · visual** (Auditor, New reader)
   - Where: Committee challenge block, CP-6_s-85.png region x≈297–1157, y≈190–295 (display scale)
   - Problem: The decisive question is one five-sentence paragraph of about 120 words set across the full content width (roughly 160–170 characters a line). Its h4 heading has the same visual weight as the data-table headings below, so the committee's key question looks no more important than the empty 'Chart data: portfolio limits' table under it.
   - Fix: Use a narrower text measure or split the paragraph into the question, then the two burdens, then the conclusion, and give the decision-level heading more prominence than the data tables.
6. **Low · narrative** (Saboteur, New reader)
   - Where: "whether creditors are paid for cash that may leave ... rather than simply cite adjusted earnings" (line 86)
   - Problem: The decisive test gives no figure, so the reader has no scale. 'Cash that may leave' could be quantified with the USD 4,348 million of dividends and equivalents already on the page (line 68). 'Adjusted earnings' appears with no measure or period.
   - Fix: Anchor the question with one figure from the key findings (amount, unit, period) and name the earnings measure meant.

### Chart data: portfolio limits

Kind: chart · handoff lines 89-94 · verdict **CONCERNS**

- Narrative: The section is a single table row in which every value is \"Not supplied\". It carries no bottom line, and its one explanatory cell uses pipeline wording (\"this module\", \"for this run\").
- Visual: No chart is drawn: CP-6 has no Charts panel, and the second screenshot shows the module top. On the page the section is a well-spaced but empty six-column table with a Basis chip whose basis list is empty.

1. **High · narrative** (New reader, Auditor)
   - Where: "Portfolio/legal vehicle and NAV denominator are not supplied; this module establishes none for this run. No holding, headroom or breach is inferred." (line 93)
   - Problem: "this module" and "for this run" are pipeline language shown to the reader. The cell also lacks a judgement-first bottom line on what the missing limits mean for the committee decision.
   - Fix: Open with the credit consequence (portfolio fit cannot be tested, so sizing is withheld), then state what is missing, with no module or run wording.
2. **High · visual** (Saboteur, Auditor)
   - Where: Heading "### Chart data: portfolio limits" (line 89); CP-6_s-89.png top (crop CP-6-113-a.png); CP-6_charts.png shows the module top with no chart drawing, and CP-6.dom.html has no chart for this data
   - Problem: The heading promises a chart, but no chart is drawn anywhere on the module page. Every cell is "Not supplied", so the reader gets a six-column empty grid labelled as chart data. "Chart data" is pipeline wording, not reader language.
   - Fix: When no limit exists, show one plain sentence under a reader heading such as "Portfolio limits" (e.g. "No mandate, holdings or limit was supplied, so headroom cannot be assessed") in place of an empty chart-data table.
3. **Medium · narrative** (New reader)
   - Where: "Not supplied: no matched portfolio limit selected | Not supplied: no holdings supplied | Not supplied: no proposal evaluated | Not supplied: no matched mandate supplied | Not established: no portfolio reporting unit supplied" (line 93)
   - Problem: Five slightly different wordings of one fact (no portfolio inputs) make the reader parse five cells to learn one thing. "matched" and "proposal evaluated" are internal terms that are never defined.
   - Fix: Say the single absence once, in plain words, rather than repeating near-synonyms in every column.
4. **Medium · visual** (Auditor, Saboteur)
   - Where: "Basis" chip in the Limit cell, CP-6_s-89.png region x≈300-400, y≈255-315 (rendered button data-basis="[]", aria-label "Basis for row: Not supplied: no matched portfolio limit selected")
   - Problem: The Basis link is attached to a row with an empty basis list (data-basis="[]"). It offers a source trail that leads nowhere, which is a fake affordance.
   - Fix: Hide the Basis chip when the row has no basis entries, or point it to the portfolio input that was checked and found absent.
5. **Low · narrative** (Auditor)
   - Where: "The selected portfolio evaluation states no numerical limit or exposure." (line 93)
   - Problem: The "Basis and limitation" column names an unnamed "selected portfolio evaluation" as its source instead of a document or source module the reader can find in Sources, so it gives no traceable reference.
   - Fix: Name the source as it appears in the Sources table (e.g. Relative value and security selection), or drop the reference.

### Source gates and neutral pre-debate maps — steps 1–2 in each lens

Kind: prose/table · handoff lines 103-149 · verdict **BLOCK**

- Narrative: The section takes inventory of the evidence in internal pipeline language (gates, producers, re-anchor, register codes, CP5-00x IDs), garbles text where codes are substituted, and leaves its real judgement (compensation and capacity cannot be established) to the last line.
- Visual: The section has no chart. It shows three long, dense four-column tables back to back, with inline Basis chips that wrap into the row labels and Source cells padded with repeated names; it is readable but slow, and does little to highlight the few rows that carry evidence.

1. **High · narrative** (Auditor, New reader)
   - Where: L105 "Both debate gates are Ready with Limitations. The financial and fundamental producers are available; the relative-value producer is available but explicitly withholds preference and size." plus heading L103 "steps 1–2 in each lens" and column header L107 "Re-anchor and availability"
   - Problem: This section talks in pipeline language from start to finish: "gates", "producers", "Re-anchor", "artifact", "absorbed portfolio phase", "handoffs", "run_id", "persona adjudication" and "steps 1–2 in each lens". The house standard bans every one of these from the reader's page, and the reader cannot tell what "Ready with Limitations" means for the credit.
   - Fix: Open with a plain judgement, e.g. which parts of the credit case the evidence supports and which it cannot support, and rename the heading and columns in reader language with no step or lens numbering.
2. **High · narrative** (Auditor, Saboteur)
   - Where: L111 "CP-1 C03/C05/C06/C13; CP-1A B1/B7/T5/T6/T7/F1/G1; CP-2 T2.1/R1–R5" rendered as "Fundamental credit a method step/R1–R5"; L113 "CP5-001 and CP5-002 MATERIAL and Open"; L110 "tdg-2024-09-30-credit_snapshot-sol-medium"
   - Problem: Register codes (C03, B1, T5, R1–R5, F1, G1) and validation IDs prefixed with a module code (CP5-001, CP5-002) appear on screen, and so does an internal run identifier. The code substitution also breaks the text: "Fundamental credit a method step/R1–R5" does not read as a sentence. The reader cannot tell which findings or issues are meant.
   - Fix: Name each input and each open validation issue by what it says (e.g. "FY2024 free cash flow, interest cover" or "the open issue on X"), and drop run IDs and register codes from the screen.
3. **Medium · narrative** (Saboteur)
   - Where: L114 rendered as "Earnings changes/Peer benchmark/Downside/Downside/Business & governance/Liquidity/Rates, FX & hedging/Refinancing & LME/Covenant capacity not supplied"
   - Problem: Replacing module codes with names leaves "Downside" listed twice, and the result is a slash-joined list of missing internal modules. It does not say which analyses the credit view lacks, and the second sentence ("Absorbed instrument and portfolio work ... not treated as wholly absent") is a pipeline caveat.
   - Fix: State once, in plain words, which credit analyses are missing (e.g. a full downside case, a liquidity runway, refinancing options, covenant basket capacity) and what each absence prevents the committee from concluding.
4. **Medium · narrative** (Saboteur)
   - Where: L129 "Sponsor / governance | Issuer extraction documented; no controller support assumed | Strong behavior; Insufficient sponsor support" and L124 "FY2025 and FY2028 reported principal buckets ... Strong schedule within exclusions"
   - Problem: The quality labels "Strong" and "Moderate" grade how good the evidence is, but in this table they read as credit grades. "Strong behavior" for documented debt-funded extraction could look like a positive governance view. The maturity row gives no amounts and does not say what "within exclusions" excludes.
   - Fix: Label the column "Evidence quality" and spell out each label (e.g. "well-evidenced: shareholder payouts funded with debt"), and show the FY2025 and FY2028 principal amounts with their unit, or point to where they are shown.
5. **Medium · narrative** (New reader, Auditor)
   - Where: L115 "context, page 1" in the Source column (also L128, L143–145); undefined abbreviations L138 "Spread / YTW / DM", L139 "Peer RV", L126 "Recovery / LGD", L141 "no exit evidence"
   - Problem: The source "context, page 1" does not tell the reader which document is meant. YTW, DM, RV, LGD and LME are never defined for a reader who has not read the sources.
   - Fix: Name the source document (e.g. "Analyst request, page 1") and spell out each abbreviation on first use.
6. **Medium · narrative** (Saboteur, New reader)
   - Where: L148 "Pre-debate, the central portfolio controversy is whether spread / yield / RV evidence is sufficient to compensate for downside / downgrade / concentration / mandate / legal / liquidity risk."
   - Problem: The section's judgement is buried at the end, after three dense tables, and its strings of slash-joined terms weaken it. The plain point, that neither compensation nor portfolio capacity can be established, should come first.
   - Fix: Lead the section with the two controversies and the one-line conclusion that the evidence cannot establish compensation, capacity or legal rights, and let the tables follow as support.
7. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-6_s-103.png, the three stacked tables, y≈270–1930 (displayed scale)
   - Problem: Three dense four-column tables run back to back, about 1,650 px of the page, with only one-line bridges between them. The Basis chip sits inline after the row label and wraps under longer labels (e.g. "Concentration / correlation Basis", "Implementation liquidity Basis"), so it reads like part of the label. Most cells in the last table repeat "Insufficient", which carries little information.
   - Fix: Put the Basis chip in its own consistent position (or a narrow column), and condense the portfolio-map rows that are uniformly "Insufficient" into one sentence or a grouped row, so the few rows with evidence stand out.
8. **Low · visual** (Auditor)
   - Where: Screenshot CP-6_s-103.png, first table, Source column (y≈310–830), e.g. "Financial foundation; Business and transaction context (Business & governance); Fundamental credit synthesis (Fundamental credit)"
   - Problem: Source cells repeat module names twice (full name plus a short name in brackets). This lengthens the cells to four or five wrapped lines and widens the rows for no reader benefit.
   - Fix: Use one reader-facing source name per cell.

### Bear transmission and legal-control test — step 4

Kind: prose/table · handoff lines 166-180 · verdict **CONCERNS**

- Narrative: The verdict is buried at the end, protocol jargon (Zero-Bound, bias ceiling, step 4, required route) and undefined acronyms (LME, ICA) leak into the text, and the transmission paragraph is an unsized wall.
- Visual: The route table lays out cleanly and stays legible, but it has empty-payload Basis buttons inline in the label cells, double-named sources that wrap to 3-4 lines, and raw [Insufficient Information] tokens; the section has no chart.

1. **High · narrative** (Saboteur, Auditor)
   - Where: L179 "The Bear wins the retention objection and exposes incomplete protection evidence; the Bear does not prove imminent distress, legal abuse or inadequate market compensation." (after the 8-sentence L168 paragraph and the table)
   - Problem: The section's judgement comes last, after a long causal-chain paragraph and a four-row table, so a reader who skims the top sees a disruption scenario with no verdict. This breaks the house rule that the judgement comes first.
   - Fix: Open the section with the L179 verdict (Bear wins on retention, does not prove distress or legal abuse), then give the transmission chain and the route table as support.
2. **High · narrative** (New reader, Auditor)
   - Where: L168 "The Bear's Zero-Bound chain is therefore incomplete and does not trigger a proven-Zero-Bound bias ceiling."; L170 "The legal-control attack attempts every required route below"; heading L166 "— step 4"
   - Problem: "Zero-Bound chain", "bias ceiling", "required route" and "step 4" are debate-protocol vocabulary that mean nothing to a credit committee member, and they sit on the paragraph's conclusion line. Pipeline wording is reaching the reader.
   - Fix: Say it plainly, e.g. the evidence does not show a path from an operating shock to cash running out, so no default case is made, and drop the step numbers from the heading.
3. **Medium · narrative** (New reader)
   - Where: L170 "not unused permission or a coercive LME"; L176 "No executed collateral/ICA/anti-subordination package"; L177 "Effective voting/sacred-rights chain absent"
   - Problem: LME and ICA are never defined. Slash-chained legal terms make the table hard to read for a reader who has not seen the credit agreement.
   - Fix: Spell out liability management exercise and intercreditor agreement on first use, and replace the slash chains with short phrases.
4. **Medium · narrative** (Saboteur)
   - Where: L168 "A utilization, production or certified-supplier disruption would first delay shipments or collections. ... The size and timing from operating shock to cash exhaustion are missing; legal remedies, dilution permissions and refinancing access are also unverified."
   - Problem: An eight-sentence wall paragraph with no figures or periods lays out a stress chain and then cancels it in the last two sentences. The reader cannot tell how large or how near the risk is, or whether it matters.
   - Fix: Split it into a short judgement sentence, a bulleted chain of leading indicators, and a single sentence naming the missing sizing (with what would supply it).
5. **Medium · visual** (Auditor, Saboteur)
   - Where: Route table, "Basis" button in each Route tested cell (shots/CP-6_s-166.png, y≈380-620 displayed); DOM render/CP-6.dom.html: button class="basis-link" data-basis="[]"
   - Problem: Each row shows a clickable Basis button, but its basis payload is empty, so the control promises provenance it cannot deliver. It also sits inline as grey text after the route label, where it reads like part of the label.
   - Fix: Show the Basis control only when it has basis entries, styled as a distinct chip or a separate column rather than inline grey text in the label cell.
6. **Medium · visual** (New reader, Auditor)
   - Where: Source column, e.g. "Legal Covenant Interpreter (Legal & covenants)", "Business and transaction context (Business & governance)" (shots/CP-6_s-166.png, table right column)
   - Problem: Every source carries two names for the same module, an internal agent name plus the library label, and wraps to 3-4 lines. This leaks internal naming, and the Source column ends up the tallest column in the table.
   - Fix: Give one reader label per source (the library's module name), linked to that module.
7. **Low · narrative** (Auditor)
   - Where: L168 and L170 prose paragraphs (rendered without a Basis line)
   - Problem: The narrative paragraphs carry no Basis line, so a reader cannot trace the transmission chain or the distribution statement to evidence. The house standard puts source references in each paragraph's Basis line.
   - Fix: Attach a Basis line to each prose paragraph that points to the cash-flow and legal evidence it relies on.
8. **Low · visual** (New reader)
   - Where: Table cells showing "[Insufficient Information]" inline in prose (L175, L177; screenshot rows 2 and 4)
   - Problem: Bracketed status tokens are dropped mid-sentence as raw text instead of the chip used elsewhere, which looks like an unrendered template marker.
   - Fix: Render missing-evidence status as the same styled chip used for status values elsewhere on the page.

### Action bias, greatest uncertainty and Chair memo — steps 8–10

Kind: prose/table · handoff lines 181-190 · verdict **BLOCK**

- Narrative: The section does lead with its judgement (Requires More Work, then Neither wins), but banned pipeline wording ('producer-owned QA repairs', 'blocked legal gate', 'guardrail', the 'steps 8–10' heading), unquantified decisive evidence, undefined action-scale labels and missing Basis lines stop a credit committee from using it as it stands.
- Visual: There is no chart in this section: it is four dense prose blocks in uniform small type, with no emphasis on the lead-in labels or the verdict, so the recommendation is hard to find on the page. Spacing and width are otherwise consistent with the rest of the page.

1. **High · narrative** (Auditor, New reader)
   - Where: L189 "Before conviction increases, adopt producer-owned QA repairs, complete the downside cash bridge"; L189 "remains [Insufficient Information] under the blocked legal gate"; L185 "activates the Requires More Work guardrail ... No average or hidden override replaces these gates."
   - Problem: The reader sees pipeline wording the house standard bans: "producer-owned QA repairs", "blocked legal gate", "guardrail", "gates" and "override". The DOM confirms the text reaches the screen. A committee member cannot act on "adopt producer-owned QA repairs" because it describes the workflow, not the issuer.
   - Fix: Say in credit terms what is missing (for example, the executed credit agreement and indentures were not reviewed) and drop any mention of QA, gates or guardrails.
2. **High · narrative** (Auditor, New reader)
   - Where: Heading L181 "### Action bias, greatest uncertainty and Chair memo — steps 8–10"
   - Problem: "steps 8–10" is an internal method step number. It means nothing to a reader who does not know the debate protocol, and it repeats in the page's On-this-page navigation. Promoted because two personas caught it.
   - Fix: Title the section by what it concludes (for example, "Committee recommendation and main uncertainty") with no step numbering.
3. **Medium · narrative** (Saboteur)
   - Where: L189 "The single best Bull evidence is realized FCF before acquisitions/distributions. The single best Bear evidence is financing expressly tied to equity extraction"
   - Problem: The decisive evidence on each side has no figure, period or unit. The committee is asked to weigh a Bull and a Bear case without the FCF amount, the fiscal year or the size of the equity-linked financing. The same page gives figures only further down, in the Bear cross-examination table (for example, USD -2,505 million FY2024 FCF after distributions).
   - Fix: State each piece of evidence with its amount, currency, period and basis (for example, FY2024 FCF before acquisitions and distributions, USD X million).
4. **Medium · narrative** (New reader)
   - Where: L183 "The decision is driven by supported historical servicing cash alongside demonstrated equity-directed use and unverified compensation/protection, because earnings generation does not reserve cash or establish loss protection, which implies no executable creditor allocation."
   - Problem: The sentence that should justify the recommendation is a chain of abstract nouns and joined clauses ("executable creditor allocation", "allocation-sensitive leverage" at L187). A PM cannot pull out the reason in one reading.
   - Fix: Give the reason in two short, concrete sentences: cash covers debt service today, but cash goes to shareholders and the bond terms and pricing are unverified, so no position can be sized.
5. **Medium · narrative** (New reader, Saboteur)
   - Where: L187 "would permit reconsideration toward Watchlist or, only with verified access and portfolio capacity, Starter Position; it would not automatically authorize Add / Increase ... shift toward Avoid, not Exit"
   - Problem: The section relies on an undefined internal action scale (Requires More Work, Watchlist, Starter Position, Add / Increase, Avoid, Exit) and on undefined abbreviations (RV, FCF). A reader cannot place "Requires More Work" on that scale or judge how far it is from investable.
   - Fix: Define the action ladder once, in reader terms, where it first appears (or link a short legend), and spell out RV and FCF.
6. **Medium · narrative** (Auditor)
   - Where: L183–L189: four paragraphs beginning "Final Action Bias:", "Debate winner:", "Single Greatest Uncertainty:", "The Chair's final memo"
   - Problem: None of the four paragraphs has a Basis line, although each makes evidential claims (historical servicing cash, the reported principal schedule, equity-tied financing). The reader cannot trace them. The Chair memo also repeats the verdict and the debate winner already stated in L183 and L185.
   - Fix: Add a Basis line under each paragraph and cut the Chair memo down to what it adds beyond the first two paragraphs.
7. **Medium · visual** (New reader, Auditor)
   - Where: Screenshot CP-6_s-181.png, section region crop (original px y≈228–606); crop saved as /private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-refactor-optimisation-sweep-01c49e/d3b58d68-0f70-4eca-af09-da4e7774dc7f/scratchpad/tmp/CP-6-118-a.png
   - Problem: The lead-in labels "Final Action Bias:", "Debate winner:" and "Single Greatest Uncertainty:" render in the same regular weight as the body text. The verdict "Requires More Work" gets no emphasis. The result is four dense 4–6-line blocks of small type that the eye cannot scan for the decision.
   - Fix: Make the labels bold or show them as a definition list or chip, and give the verdict visual weight so a reader sees the recommendation at a glance.
8. **Low · narrative** (Saboteur)
   - Where: L187 "This is one underwriting trade-off, not a claim that each missing input is an independent greatest uncertainty."; L189 "This memo introduces no new issuer fact or formal rating."
   - Problem: These closing sentences talk about the method's own rules, not about the issuer. They add length and weaken the ending of the passages that should land the judgement.
   - Fix: Delete the self-referential disclaimers and end each paragraph on the credit point.

### RV Trader opening and defense — steps 3 and 5 of the portfolio lens

Kind: prose/table · handoff lines 191-206 · verdict **CONCERNS**

- Narrative: The content (no relative-value or mandate evidence, so posture Requires More Work) is sound. The section still breaks the house rules: no bottom line before the tables, a banned \"Canonical\" header, internal \"steps of the portfolio lens\" and R/P codes, undefined abbreviations, and two columns that are all \"Insufficient Information\".
- Visual: There is no chart. The two tables render cleanly with good contrast and no clipping. Their faults are empty Basis chips on all six rows (data-basis=\"[]\"), tight wrapping in the label and Source columns, and width spent on identical cells.

1. **High · narrative** (Auditor, New reader)
   - Where: L193 column header "Canonical credit implication"; L191 heading "steps 3 and 5 of the portfolio lens"; rendered in shots/CP-6_s-191.png, top table header and section title
   - Problem: Pipeline vocabulary reaches the reader: "Canonical" is on the house banned list, and "steps 3 and 5 of the portfolio lens" refers to the module's internal procedure, which a committee member cannot interpret.
   - Fix: Rename the column to "Credit implication" and title the section by its question, e.g. "Relative-value case for owning the bonds and its defence".
2. **High · narrative** (Saboteur, Auditor)
   - Where: L205 "No numeric sizing constraint is proposed. Exact size is [Insufficient Information]; the provisional posture is Requires More Work."
   - Problem: The section's judgement comes last, after two tables. It opens straight into a six-row grid with no bottom line. That breaks the judgement-first order, and a skimming reader may never see that the trader could not make any case for value.
   - Fix: Open the section with a one-sentence bottom line (no relative-value case can be made; posture Requires More Work), then the tables.
3. **Medium · narrative** (New reader)
   - Where: L195 "R1 Spread / YTW / DM pickup | [Insufficient Information]: no current matched return/peer comparison. Accounting FV and coupon cannot demonstrate cheapness"; L197 "no active mandate, exposure, NAV or proposal"
   - Problem: YTW, DM, FV and NAV are not defined. The labels R1–R3 and P1–P3 point to pitches and attacks that a reader landing on this section has not seen, so "P1 against R1" means nothing here.
   - Fix: Spell out the abbreviations on first use and replace the R/P codes with short plain labels (e.g. "Spread pickup — attacked as unproven").
4. **Medium · narrative** (Saboteur)
   - Where: L195–L197 and L201–L203: every "Canonical credit implication" and every "Rebuttal status" cell reads "Insufficient Information"
   - Problem: Two whole columns repeat the same value in all six rows, so they carry no information. The grid's layout suggests a contested debate when the substance is one fact: no market or mandate data were supplied.
   - Fix: Collapse the identical columns into one stated sentence and keep only the rows' distinguishing content (what is missing and what would resolve it).
5. **Medium · visual** (Auditor)
   - Where: Rendered DOM render/CP-6.dom.html, Basis buttons for rows CP-6.md:195,196,197,201,202,203 all carry data-basis="[]"; visible as "Basis" chips under each row label in shots/CP-6_s-191.png
   - Problem: Each row shows a clickable Basis chip whose basis list is empty. The reader is offered a source trail that resolves to nothing, which reads as if the evidence exists but is hidden.
   - Fix: Populate the Basis with the row's sources, or do not render the chip when the basis is empty.
6. **Low · narrative** (Auditor, New reader)
   - Where: L195 Source "Relative value and security selection (CP-3), T3.5" rendered as "Relative value and security selection, a method step"; L197 "context, page 1"
   - Problem: The rendered source cells say "a method step", "method steps" and "context, page 1". These are not identifiable sources: the reader cannot tell which document or page backs the row.
   - Fix: Cite the module title and the specific document and page, or the module only, without placeholder wording.
7. **Low · visual** (New reader)
   - Where: shots/CP-6_s-191.png, first table (y≈215–525): row-label column wraps "R3 Implementation despite budget use Basis" over four lines and the Source column wraps to five lines
   - Problem: The narrow first and last columns force heavy wrapping, while the duplicated "Insufficient Information" column uses wide space, so the table is taller and harder to scan than its content needs.
   - Fix: Drop or narrow the constant column and give the width to the label and source columns.

### Audit appendix — evidence trace, conflicts, QA and readiness

Kind: prose/table · handoff lines 310-352 · verdict **BLOCK**

- Narrative: The section is an internal QA and certification appendix rather than reader prose. It surfaces script names, internal finding codes and pipeline vocabulary, and only its debt-basis and liquidity conflict rows carry credit-relevant content.
- Visual: There is no chart. The three tables render cleanly with readable wrapping and no clipping in the area seen, but the module-name substitution produces garbled labels, the weights appear in a different numeral style and scale from the rest of the page, and repeated Basis chips add clutter.

1. **High · narrative** (Auditor + New reader (promoted))
   - Where: QA table, lines 339-348: "prepare_invocation.py | Not run: unavailable | Used supplied current handoffs and exact pins; no new digest, snapshot receipt or fabricated earlier run_id" (also confidence_score.py, completeness_check.py, validate_handoff.py, CP_DR_RESEARCH_BRIEF_V1.md)
   - Problem: The rendered page (CP-6_s-310.png, y≈1300-1930) shows the reader a whole table of script names, transport checks, 'handoffs', 'producers', 'consumer', 'pins', 'YAML identity' and 'six exact transport H2s'. This is pipeline self-certification, and none of it is reader language. A credit committee member cannot act on any of it.
   - Fix: Remove the script, tooling and transport QA table from the reader page, or reduce it to one plain sentence on what was not independently checked.
2. **High · narrative** (Auditor + Saboteur (promoted))
   - Where: Line 329: "Canonical amount is carrying; inherited ratios remain labelled principal overlays only... Producer correction remains Open"; line 333: "CF5 Confidence and open CP5-002"; line 346: "CP5-001 and CP5-002 counted once each"
   - Problem: Module-derived codes (CP5-001, CP5-002) and banned vocabulary ('Canonical', 'Producer', 'upstream-owned', 'inherited') appear on screen in the conflict and QA tables. The debt-basis conflict, which is the one point that bears on credit (carrying USD 24,880m against principal USD 25,068m, with leverage of 6.01x/6.57x measured on principal), is written in pipeline terms, so a reader could miss which leverage basis applies.
   - Fix: State the debt-basis conflict in reader terms: which amount the view uses, that the 6.01x/6.57x leverage is on principal, and that the discrepancy is unresolved. Drop the internal finding codes.
3. **Medium · narrative** (Saboteur + New reader (promoted))
   - Where: Line 312: "The audit summary is Restricted and Requires More Work... Confidence Score is 17/100, band Insufficient Information... No full_analytical_complete or Committee Ready certification is made."
   - Problem: The opening gives internal QA statuses and a raw token (full_analytical_complete) where a credit judgement should be. It never says in reader terms what 17/100 means for the decision: historical credit facts are solid, but compensation, legal protection and position size are unknown. The clarifying sentence is buried at line 325, after the table.
   - Fix: Lead with one judgement sentence on what the committee can and cannot rely on. Then the score, defined in plain words, without internal status tokens.
4. **Medium · narrative** (New reader)
   - Where: Line 314 header: "Strongest lineage_class | Weight"; line 345: "T6A registers: 7+5+6+5; T6E registers: 6+5+6+5... C=100% measures field presence"; line 346: "P=30"
   - Problem: Raw field names (lineage_class), register codes (T6A, T6E, C03/C05, V03/V04, MC2) and undefined symbols (C, P, E) are shown with no definition. The reader cannot tell how the weights produce 17/100 without reading the Calculations section and the internal specification.
   - Fix: Use plain column headers such as 'Evidence type', define the score inputs in one sentence, and drop the register codes from reader-facing cells.
5. **Medium · visual** (Auditor)
   - Where: CP-6_s-310.png, QA table row 'Other scripts and companion schemas/system references', y≈1640-1680 (displayed): "Committee decision/Committee decision schema and system reference files"
   - Problem: The display-name substitution turned 'CP-6/CP-6A schema' into the duplicated 'Committee decision/Committee decision schema'. D2's source likewise reads 'Business and transaction context (Business & governance)', and D6 names the module twice under two names ('Legal Covenant Interpreter (Legal & covenants)'). On screen these read as garbled text.
   - Fix: Apply each module's display name once, and do not let the code-to-name mapping produce duplicated or doubled labels.
6. **Low · visual** (Saboteur)
   - Where: CP-6_s-310.png, claim census table Weight column, y≈300-640 (displayed)
   - Problem: Weights are set in a monospace font, while every other number on the page, including the USD amounts in the conflict table, is proportional. The weights are 0-1 values, but the formula at line 359 uses 90/40/100, so the reader sees two scales for the same weights.
   - Fix: Use one numeral style and one scale for the weights (0-1 or 0-100) in both this table and the Calculations section.
7. **Low · visual** (New reader)
   - Where: CP-6_s-310.png, all three tables: a 'Basis' link on every row next to the row ID
   - Problem: Every row of all three tables carries a 'Basis' chip in addition to a Source column. This duplicates the provenance cue and adds clutter to an already dense, three-table appendix that runs past the bottom of the 2400 px screenshot.
   - Fix: Keep provenance in the Source column for tables, and give tables without a Source column (the QA table) a single basis note.

### Calculations

Kind: prose/table · handoff lines 353-376 · verdict **BLOCK**

- Narrative: The arithmetic checks out (45, 67, 46.9, 17), but the section opens with pipeline boilerplate instead of the score's meaning, leaks codes and pipeline vocabulary, hides that the three zeros are missing evidence, and misuses the Latest/Prior columns.
- Visual: The section has no chart, only two bordered tables that render legibly with no clipping. The visual faults are two empty Basis chips, emphasis on intermediate values rather than the final score, and narrow value columns that wrap short figures.

1. **High · narrative** (Auditor, New reader)
   - Where: L355 "New arithmetic is solely the confidence computation, using the Decimal-38 kernel... accepted upstream amounts, not claims of new kernel execution"; L370 "Canonical carrying debt"; L363 "findings CP5-001/CP5-002"; L364 "qa_status Restricted"
   - Problem: The section opens and runs on pipeline vocabulary (kernel, Decimal-38, upstream, carried-value register, canonical) and shows finding codes CP5-001/CP5-002 and a raw field name qa_status on screen (rendered in the Q6-05/Q6-06 rows). The house rule forbids all of these.
   - Fix: Use reader language: "the only new calculation is the confidence score; every financial figure below comes from earlier sections". Name the debt row "Carrying debt" and replace the codes with plain descriptions of the two open evidence findings.
2. **High · narrative** (Saboteur, New reader)
   - Where: L363 "16.9 before integer presentation; Confidence Score 17/100" / L364 "17 below 40: Insufficient Information; qa_status Restricted"
   - Problem: The headline result (confidence 17/100, Insufficient Information, Restricted) is buried in the fifth and sixth rows of a mechanics table, with no plain statement of what it means for the committee. The opening paragraph gives method boilerplate, not the bottom line a data section owes.
   - Fix: Open the section with one sentence: confidence 17/100 (Insufficient Information, Restricted), driven mainly by three domains with no evidence and two open evidence findings. Then show the mechanics.
3. **Medium · narrative** (Saboteur)
   - Where: L359 "sum(90,40,100,40,90,0,0,0)=360; ratio(360,8) | E=45 | CP-6 material domain weights scaled to 100 before mean"
   - Problem: The three zeros are the domains D6–D8 rated Insufficient Information (L321-323), meaning loss protection, compensation and executable size were not assessed. The row presents them as scored zero, so a reader cannot tell missing from zero, and these zeros drive the low E.
   - Fix: Label the three operands as "not assessable, scored 0 by rule" and name the domains, so missing evidence is visibly distinct from a weak score.
4. **Medium · narrative** (New reader)
   - Where: L361 "sum(45,45,45,45,45,45,100,100,100,100)=670; ratio(670,10)"; L362 "sum(67,67,67,67,67,67,67)=469; ratio(469,10)"; L364 "59 ceiling nonbinding"
   - Problem: The weighting 0.6E+0.4C and 0.7×67 are written as repeated-operand sums, and E, C, S and the 59 ceiling are never defined. A committee member cannot follow or check the score.
   - Fix: Write each step as its formula with the defined terms (for example "Evidence 45 × 0.6 + Coverage 100 × 0.4 = 67" and "× source-readiness factor 0.7 = 46.9"), and say what the ceiling is.
5. **Medium · narrative** (Saboteur)
   - Where: L374 "Reported long-term principal timing | FY2025 USD 93 million | FY2028 USD 6,637 million"; L373 "USD 3,000 million | Approximately USD 4,348 million"; L375 "Not supplied: no comparison needed"
   - Problem: The "Latest / case" and "Prior / comparison" columns are reused for unrelated pairs. FY2028 maturities sit under "Prior", and so does the October payment. A skimming reader can read FY2028 as a prior-period figure or USD 4,348 million as a comparison to the USD 3,000 million funding.
   - Fix: Keep the Latest/Prior columns for true period comparisons only, and move maturity-timing and funding-versus-payment pairs into their own labelled rows or a separate small table.
6. **Medium · narrative** (Auditor, New reader)
   - Where: L373 Source "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 54"; L368-375 sources "C05", "C03", "C13", "V01", "C2-06", "maturity chart"
   - Problem: The Source column shows a raw pipeline file name (.jsonl) and internal register codes that point nowhere a reader can follow. Rendered, it reads "Fundamental credit synthesis (Fundamental credit), C2-06" (screenshot, carried-observation table, Source column).
   - Fix: Cite "TransDigm FY2024 Form 10-K, p. 54" and section names with a readable anchor instead of internal register IDs.
7. **Medium · visual** (Auditor, Saboteur)
   - Where: Carried financial observation table, rows "New secured distribution funding / subsequent payment" and "Selected-use cash shortfall": shots/CP-6_s-353.png, about x 360-560, y 1270-1460 (original px); DOM data-basis="[]"
   - Problem: Only two of eight rows have a "Basis" chip, and both chips have an empty basis payload (data-basis="[]"). The control promises provenance and delivers none, and it makes those two rows look different from the rest for no reason.
   - Fix: Render a Basis chip only when it has content, or give every row consistent provenance through the Source column.
8. **Low · visual** (New reader)
   - Where: Q6 table Result column: tmp/CP-6-123-a.png (crop 350,340-1400,900 of shots/CP-6_s-353.png); "67" and "46.9" in bold monospace, "E=45", "17/100" in plain body text
   - Problem: Bold figure styling is applied to the intermediate values 67 and 46.9 but not to the final 17/100. The emphasis falls on the wrong cells, and the narrow Result and Latest columns wrap short values like "FY2024 approximately 3.60x" onto three lines.
   - Fix: Emphasise only the final score, and widen the result/value columns (or narrow the operand column) so single figures fit on one line.

### Gaps

Kind: prose/table · handoff lines 377-389 · verdict **CONCERNS**

- Narrative: The Gaps section is a bare ledger with no judgement-first lead. Its rows are written in pipeline vocabulary and undefined jargon, and the gap the module itself calls the greatest uncertainty is buried in row 3.
- Visual: The four-column table is legible and well spaced at 1440 px, but the gap-label rewrite produces colliding and malformed IDs (two different "Gap 1" and "Gap 2", plus "Gap 1/005"), and the Basis chips appear on some rows only.

1. **High · narrative** (Auditor, New reader (promoted))
   - Where: line 385: "CP-6-GAP-006: open producer QA | ... CP-3 census repair; CP-5 re-audit. This debate does not repair producers"; line 388: "unavailable machinery and companions ... no fabricated digest, invocation output, adoption row or schema certification"
   - Problem: Pipeline vocabulary that the house standard bans reaches the reader: producer, predecessor, owning analyses, re-challenge, adoption, census repair, transport restrictions, invocation output, schema certification. The whole last row reports on tooling, not on an issuer credit gap.
   - Fix: Describe each gap as missing issuer evidence and its effect on the credit view, and move tooling and run-readiness notes out of the reader table.
2. **High · visual** (Saboteur, New reader (promoted))
   - Where: Gaps table, Gap group column, shots/CP-6_s-377.png y~1230-1500 (display): rendered "Gap 1/005", "Gap 2/004 and Gap 5", "Gap 3 and Gap 1: compensation", "Gap 2/003/004/006/007: portfolio implementation" (handoff lines 381-384: CP-6-GAP-001/005, CP-6A-GAP-001, CP-6A-GAP-002/003/004/006/007)
   - Problem: When the module codes are stripped, the issuer-debate and portfolio-debate gap series collapse into one numbering. "Gap 1" and "Gap 2" now each name two different gaps, and "Gap 1/005" is a malformed half-rewrite. A reader cross-checking against the Issuer and Portfolio debate gaps ledgers will match the compensation row to the stress gap.
   - Fix: Give each ledger's gaps a distinct reader label (e.g. Issuer gap 1, Portfolio gap 1) and rewrite every element of a slash-list, so no label repeats across the two series.
3. **Medium · narrative** (Saboteur)
   - Where: line 383: "Greatest underwriting uncertainty unresolved; no preferred tranche or investment merits winner"
   - Problem: The section opens straight into an eight-row table with no lead sentence. The gap the module itself calls the greatest underwriting uncertainty sits in row 3, after two lower-priority rows, so the reader is never told which gaps would actually change the committee view.
   - Fix: Open with one judgement-first sentence naming the gaps that matter most to the decision, and order the rows by decision impact.
4. **Medium · narrative** (New reader)
   - Where: line 381: "Neither a fully proved Zero-Bound path nor quantified liquidity protection; no durable capacity assertion"; line 382: "definitive funding/LME path"
   - Problem: Undefined jargon and abbreviations (Zero-Bound path, LME, capacity assertion, terminal challenge, mandate constraint) together with telegraphic negations leave a reader who has not read the sources unable to tell what decision is blocked.
   - Fix: Spell out the terms and state each consequence positively, e.g. what the committee cannot yet conclude about liquidity or recovery.
5. **Medium · narrative** (Auditor)
   - Where: Source column, shots/CP-6_s-377.png: "Fundamental credit synthesis (Fundamental credit)", "Legal Covenant Interpreter (Legal & covenants)", "context, page 1" (handoff lines 381-387)
   - Problem: The Source cells name internal modules with a duplicated label in parentheses, an internal agent name (Legal Covenant Interpreter), and "context, page 1", which a reader cannot trace to any document.
   - Fix: Cite the issuer document or the reader-facing module name once, and replace "context, page 1" with the actual source document title.
6. **Low · visual** (Auditor)
   - Where: Gaps table, "Basis" chips beside Gap group labels on only three rows (portfolio implementation, Gap 8: scheduling, and above), shots/CP-6_s-377.png y~1480 and ~1677
   - Problem: Only some rows carry an unlabelled "Basis" chip, placed inline with the gap name, so the reader cannot tell why those rows have one and others do not.
   - Fix: Give every row a Basis affordance in a consistent position, or explain the chip in the table caption.

### Sources

Kind: prose/table · handoff lines 40-55 · verdict **CONCERNS**

- Narrative: The section names its inputs, but in pipeline vocabulary ("handoffs", "lineage under this transport", "supplied accepted"). That wording blurs the fact that the legal input is blocked and two other inputs are restricted, the qualifications that matter most for the committee decision.
- Visual: The table renders cleanly and has no clipping, but the sha256 hashes take nearly half its width, which squeezes the use column into tall wrapped rows. Two rows show Basis buttons with an empty payload.

1. **High · narrative** (Auditor, New reader)
   - Where: L54: "All seven supplied handoffs are consumed and pinned above. Their acceptance establishes lineage under this transport, not substantive investment clearance. ... Supplied method bundles and confidence rules were applied in full"
   - Problem: The closing paragraph is written in pipeline vocabulary ("handoffs", "consumed and pinned", "lineage under this transport", "method bundles"), which the house standard bans from the reader's page. A committee member cannot tell from it what was and was not checked.
   - Fix: State in plain words that the decision relies on the seven earlier analyses listed, that their inclusion does not mean they were re-verified, and that only page 54 of the FY2024 10-K was read directly.
2. **Medium · narrative** (Saboteur, Auditor)
   - Where: L42-L52 table cells, e.g. L50: "Legal & covenants; supplied accepted Blocked handoff, not completed legal interpretation"; L52: "supplied accepted restricted traceability and integrity review"
   - Problem: Every row says "supplied accepted", and that sits next to "Blocked" and "restricted". To a reader, "accepted" reads as approved, which hides the fact that the legal input is missing and the relative-value and validation inputs are restricted. This should qualify the committee decision. The two personas each caught it, so it is promoted one level.
   - Fix: Make the use column say each input's real status for the reader (for example "Legal review not completed; legal conclusions withheld") and drop the internal word "accepted".
3. **Medium · narrative** (New reader)
   - Where: L44: "TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl"; L45: "context | Dated run inputs only; page 1 read, not issuer evidence"
   - Problem: The one primary issuer document appears only as a raw internal file name with a .jsonl suffix. The second row is called just "context", an internal input label that means nothing to a reader.
   - Fix: Name the document as a reader would cite it (TransDigm FY2024 Form 10-K, fiscal year ended 30 September 2024, page 54), and either drop the run-inputs row or label it "Run settings (not issuer evidence)".
4. **Medium · visual** (New reader, Auditor)
   - Where: Sources table, sha256 column, shots/CP-6_s-40.png region x≈890-1390, y≈260-1020 (crop tmp/CP-6-107-a.png)
   - Problem: Raw 64-character sha256 hashes take about 45% of the table's width. As a result the use column, the one that carries meaning, wraps to 3-5 lines a row and the table runs about 750 px tall. A portfolio manager gets nothing from the hashes.
   - Fix: Put the hash in a collapsed detail or a tooltip, or shorten it to a short prefix, and give the freed width to the use column.
5. **Medium · visual** (Saboteur, Auditor)
   - Where: Rows 1-2 'Basis' buttons, render/CP-6.dom.html: class="basis-link" data-basis="[]" on the 10-K and 'context' rows; screenshot y≈290 and y≈358
   - Problem: The first two rows of a sources table show a Basis button whose basis payload is empty (data-basis="[]"). The button looks like an evidence trail but opens nothing, and it is missing from the other seven rows, so it looks arbitrary.
   - Fix: Show Basis only when there is a basis to show. A Sources table is already the reference, so rows here need no Basis button.
6. **Low · narrative** (New reader)
   - Where: L50: "Legal Covenant Interpreter" vs L51 use column "Security selection" and the left nav "Legal & covenants"
   - Problem: The first column uses one set of names ("Legal Covenant Interpreter", "Relative value and security selection", "Fundamental credit synthesis") and the second column and the left nav use another. Two labels for each source make the reader match them up by hand.
   - Fix: Use the nav's module names in both columns.
7. **Low · visual** (Auditor)
   - Where: On this page nav, shots/CP-6_s-40.png y≈1040-1080: 'Front matter', 'Request', 'Sources' placed before 'Committee challenge'
   - Problem: The Sources list sits in the middle of the page, between the request and the analysis. The VMO2 reading order puts sources after the analysis, so here the reference block interrupts the reader on the way from the bottom line to the challenge.
   - Fix: Render Sources at the end of the module page, after the analysis sections.

### Contrary evidence and what would change the view

Kind: reader passage · handoff lines 75-78 · verdict **CONCERNS**

- Narrative: The passage is in the right place in the order and its source references sit only in the Basis line, as the standard requires. But the contrary case gives no figures, the triggers have no thresholds and the last sentence says none are set, and the paragraph speaks the debate's Bull/Bear vocabulary, so the committee cannot act on 'what would change the view'.
- Visual: This section has no chart, map or timeline. On the page it is one dense 10-line paragraph with a small, low-contrast Basis link and an empty right half, which is readable but not scannable. Not verified: whether the Basis popover shows the CP module codes held in its data-basis attribute; I did not open it.

1. **High · narrative** (Saboteur, Auditor)
   - Where: line 76: "Conversely, weaker collections or inventory conversion combined with continuing equity-directed borrowing would strengthen the Bear ... No fixed stress threshold or future market access is assumed."
   - Problem: The 'what would change the view' triggers have no level, size or date: no free-cash-flow, coverage or leverage floor and no size of new borrowing. The last sentence then says no threshold is set at all. A committee cannot monitor these triggers or tell when one has fired, so the view cannot be falsified.
   - Fix: State each trigger as a measurable condition with a unit and period, for example FCF or net cash interest coverage below a stated level, or new secured borrowing for distributions above a stated USD amount. If no threshold can be supported, say so as a limitation, not inside the trigger sentence.
2. **Medium · narrative** (Saboteur, New reader)
   - Where: line 76: "TransDigm already has realized servicing cash, a replacement-driven business, disclosed seniority and limited immediate principal in the reported long-term schedule."
   - Problem: The contrary case is asserted without one figure. The supporting amounts appear only under Key findings: USD 1,880 million FY2024 FCF, about 3.60x coverage, USD 93 million FY2025 principal and USD 6,637 million FY2028. The 'later refinancing concentration' is likewise never dated or sized here, so the reader must go back up the page to weigh the challenge.
   - Fix: Carry the two or three decisive numbers, with their unit and period, into the contrary-evidence sentences, and name the FY2028 maturity amount where the refinancing concentration is cited.
3. **Medium · narrative** (New reader)
   - Where: line 76: "could make the Bull's partial victory investable ... would strengthen the Bear by reducing retained protection"; "The strongest challenge to abstention"; "A supported downside cash bridge ... matched instrument/peer compensation"
   - Problem: The passage uses the debate's internal vocabulary: Bull/Bear as parties, 'partial victory', 'abstention', 'downside cash bridge', 'matched instrument/peer compensation', 'retained protection'. A portfolio manager who has not read the debate sections must decode these terms before getting to the credit point.
   - Fix: Use plain credit language, for example 'the case for holding back a recommendation', 'stressed cash-flow projection', 'bond spread versus comparable issuers', 'cash kept in the business'.
4. **Medium · narrative** (New reader, Saboteur)
   - Where: line 76: whole paragraph, about 125 words in one block, running from "The strongest challenge to abstention..." to "...or future market access is assumed."
   - Problem: One unbroken paragraph holds three different things: the contrary evidence, the conditions that would move the view toward investing, and the conditions that would move it toward the Bear. The two directions of change are easy to miss or blur.
   - Fix: Lead with a one-sentence contrary-evidence judgement, then give two short labelled items: 'Would turn positive if' and 'Would turn negative if'.
5. **Low · visual** (Auditor)
   - Where: Screenshot CP-6_contrary-evidence.png, section block at original y about 225-475 (crop scratchpad/tmp/CP-6-110-a.png): the trailing "Basis" link after "...future market access is assumed."
   - Problem: The Basis reference is a small light-grey word at the end of a long paragraph. Its contrast is low, it has no visual affordance, and it is easy to miss as the only route to this paragraph's sources.
   - Fix: Render Basis as a distinct, adequately contrasted chip or link on its own line under the paragraph, consistent with the reading order of the VMO2 reference.
6. **Low · visual** (New reader)
   - Where: Screenshot CP-6_contrary-evidence.png, original y about 225-475: the single 10-line text block sits in about half the content width, and the right half is empty
   - Problem: No chart belongs to this section. Its only visual is a dense 10-line grey block with no bullets or emphasis, so the triggers cannot be scanned at a glance, unlike the bulleted Key findings and Limitations around it.
   - Fix: Lay the triggers out as two short bulleted lists or a two-row 'positive / negative trigger' table so they can be scanned.

### Events: Decision and watch

Kind: timeline · handoff lines 95-102 · verdict **CONCERNS**

- Narrative: The narrative is one short paragraph. It opens with what is missing, uses pipeline wording ("lanes"), and leaves its only actionable content, the watch conditions, vague and at the end.
- Visual: There is no drawn timeline because no dated events exist, and the Timeline panel's empty state is clean and readable. On the Modules page, however, the section is dominated by a seven-column table with the same "Not supplied" text in every cell, which should collapse to one line.

1. **High · visual** (New reader + Auditor + Saboteur (promoted from Medium))
   - Where: Events table, line 99: every cell reads "Not supplied: no dated committee event or review assignment"; CP-6_s-95.png region y~210-330 (display), full-width 7-column table
   - Problem: A seven-column table (Event date, Date precision, Published, Event, Status, Source, Credit relevance) repeats the same placeholder text seven times, wrapping to four lines per cell. It takes up the most space in the section and tells the reader nothing. The column names are the event register's schema, not reader language.
   - Fix: When there are no events, show one sentence such as "No committee date or review date was set for this run" in place of the table, and keep the table only when it has rows.
2. **Medium · narrative** (Saboteur + Auditor)
   - Where: line 101: "The analysis date is not converted into an event date. No decision meeting, assigned review date or user reminder is supplied. ... The undated watch conditions are new equity-directed borrowing..."
   - Problem: The only content a committee can act on, the watch list, is the last clause of a paragraph that opens with three sentences about what is missing. The judgement comes last, which reverses the house order.
   - Fix: Lead with the watch conditions as a short list and put the note that no dates exist after it.
3. **Medium · narrative** (New reader + Auditor)
   - Where: line 101: "Financing and payout events remain in the issuer-history/financial lanes; maturities remain in the instrument lane."
   - Problem: "Lanes" is internal timeline-routing vocabulary. A portfolio manager cannot tell what these lanes are or where to find them on the page.
   - Fix: Remove the sentence, or name the reader-facing page or section where financing, payout and maturity dates appear.
4. **Medium · narrative** (Saboteur + New reader)
   - Where: line 101: "deterioration in conversion, legal-document adoption and completion of matched market/portfolio evidence"
   - Problem: The watch conditions have no metric, threshold or direction, and some terms are undefined: conversion of what, and what "legal-document adoption" or "matched market/portfolio evidence" means. A committee cannot tell when a trigger has fired.
   - Fix: Write each watch item as a measurable trigger, naming the metric and the level or event that would reopen the view, in plain terms.
5. **Low · visual** (Auditor)
   - Where: CP-6_s-95.png, Events table first cell: "Not supplied: no dated committee event or review assignment Basis"
   - Problem: A "Basis" chip is attached to a placeholder cell in a row whose Source column says "Not supplied", so it points to nothing useful. The explanatory paragraph below the table has no Basis line.
   - Fix: Hide the Basis chip on placeholder rows, and give the explanatory paragraph its own Basis line if it relies on a source.
6. **Low · visual** (Saboteur)
   - Where: CP-6_timeline.png top, Timeline panel row "Decision and watch: Not established for this run / no dated committee event or review assignment" (crop CP-6-114-a.png)
   - Problem: The Timeline panel shows only "Not established". The section itself does list four watch conditions, so a reader who scans only the timeline concludes there is nothing to monitor.
   - Fix: Add an "undated watch items: see Decision and watch" pointer or count to the empty timeline row.
