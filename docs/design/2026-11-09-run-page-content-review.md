# Adversarial review: the issuer run page after the narrative was shown

**Scope:** the rebuilt library page for `cpos-tdg-sol-medium-all-001` (Overview and the 20 module
pages, branch head 5d994c0, 1440px) and the 20 handoffs behind it, read as a database
(`library/data.js`). Content and presentation only. Layout rules and the handoff method are open
to change (owner, 2026-11-09). No code was changed.
**Verdict:** BLOCK as a reading surface. The page is now complete and traceable, and it is not a report.

## Measurements

| Fact | Value |
|---|---|
| Handoff text in the run | 72,860 words, 540 paragraphs, 238 tables, 1,520 rows |
| Distinct table header shapes | 178, of which 162 occur in one module only |
| Shapes present in all 20 modules | 2: `Bottom line, Confidence, Main limitation` and `Finding, Creditor impact, Confidence` |
| Bottom lines saying "Not assessable" | 13 of 20 |
| Words in the 12 blocked analytical modules | 31,225 (43% of the run) |
| CP-1 Analysis part | 22,560px tall, 6,819 words, 515 chips, 14 tables |
| CP-2E Analysis part | 17,781px, 6,010 words, 21 headings |
| CP-2A (blocked) Analysis part | 3,664px, 1,259 words, no number |
| Chips in the run | 752 resolve to a page, 878 say "no page" or "no key" |
| Modules with front matter status | 13 of 20 |
| Modules citing CP-1 | 19, with 233 mentions |

Word share by content family: analysis and registers 38%, sources 25%, gaps and limits 14%,
method and conventions 9%, request 4%, bottom line 3%, findings 1%.

## Critical findings

**C1. The Overview leads with nothing, then repeats it 13 times.** (Saboteur, New Hire)
The top band is titled "Committee decision" and quotes CP-6: "Committee action and portfolio
implementation remain blocked". Below it, 19 equal cards follow, 12 of them a sentence saying the
module is blocked. The seven modules that reached a conclusion (CP-1, CP-1A, CP-2, CP-2D, CP-2E,
CP-3C, CP-DR) have the same weight as the ones that did not. A reader concludes the run is empty.
It is not: it holds a coherent credit view on cash generation, leverage, the shareholder payment,
liquidity, maturities and rate protection.

**C2. Blocked modules render 2,000 to 3,400 words of absence as "Analysis".** (Saboteur, Auditor)
CP-2A has no stress result, yet its page carries a Findings part, a 1,259-word Analysis part and a
Limits part. All of it restates one fact: the upstream input was not accepted. The page gives
absence the same form as analysis, so the reader must read it to learn it is empty. 43% of the
run's text is of this kind.

**C3. The Analysis part is the handoff, not a selection from it.** (New Hire, Saboteur)
Ruling R28 opened every unconsumed section in handoff order. On CP-1 that is 22,560px. The
credit interpretation (678 words, the actual analysis) sits after seven reported statements and
registers, at roughly screen 15. Reported statements, calculation bridges and narrative are three
different things with three different uses, and they are drawn the same way.

## Warnings

**W1. Module status is in the data and not on the page.** (Auditor)
13 handoffs declare `committee_status` (11 Blocked, 2 Requires More Work). The head shows
"Candidate · not accepted" on all 20, which carries no information. Seven handoffs have no front
matter at all, so status cannot be read uniformly.

**W2. "Confidence: Medium" hides an unreviewed dependency.** (Auditor)
CP-1 is cited by 19 modules. CP-2's bottom line is CP-1 plus CP-1A restated. No page shows what a
conclusion depends on, or what a module's failure invalidates.

**W3. The same conclusion is printed three times per module.** (New Hire)
The band, the findings and the first narrative section say the same thing. CP-1's own text says
"the reader summary restates conclusions developed in the detailed analysis".

**W4. More than half the chips say nothing.** (Saboteur)
878 of 1,630 chips are "no page" or "no key". On a claim row they bury the 752 that resolve.
Only 458 chips have a quote found on the cited page, and the chip does not show which.

**W5. Method vocabulary leaks into reader headings.** (New Hire)
"T2F.1 — Macro source gate and inventory", "Decimal-38 calculation trace",
"cp2b.cp_model_catalysts — blocked interface", "Analytical appendix — complete canonical
registers", "Chart data: leverage".

**W6. Gaps cannot be joined across modules.** (New Hire, Auditor)
About 100 gap rows, each module with its own columns and wording. By leading words only one key
is shared by two modules. "Executed governing documents not supplied" blocks CP-4, CP-4C and
CP-3, and the page says so three times in three phrasings instead of once with three consequences.

**W7. Key numbers is empty where numbers exist.** (New Hire)
CP-2E prints "No key numbers table" above registers of debt, hedge notional and rate sensitivity
that sit in Analysis. The first-qualifying-table rule (R15, R26) picks nothing rather than the
module's headline figures.

## Notes

- N1. Overview charts all come from CP-1. "Missing values have no bar" prints four times.
- N2. `Next module` and `Downstream readiness` sections are routing data shown as prose.
- N3. The handoff's provenance classes (Documentary Fact, Management Language, Analyst
  Interpretation) are not visible on the reading path.

## What to show and what not

| Content family | Share | Decision | Where |
|---|---|---|---|
| Bottom line | 3% | Show | Run page, grouped by theme; module band |
| Findings | 1% | Show, and join | One run-level findings register; top rows per theme |
| Narrative views ("… view", "Credit implication", contrary evidence, interpretation) | about 8% | Show open | Module page, directly after findings |
| Reported statements and registers | about 20% | Show on demand | Collapsed reference tables with title and row count |
| Calculations and bridges | about 10% | Off the reading path | Opened from the number they produce; audit |
| Gaps, remediation, research briefs | 14% | Show once | One run-level open-items register; three lines per module |
| Limits and monitoring | part of 14% | Show, capped | Module page, the triggers only |
| Sources and registers | 25% | Hide | One run-level Sources page from CP-0; audit |
| Method, conventions, QA limits | 9% | Hide | Audit |
| Request, front matter | 4% | Hide; status surfaced | Head badge |
| Next module, readiness | small | Convert | Dependency column in the module matrix |
| Blocked-module body | 43% of words | Collapse | One row: status, blocked by, needed to unblock |

## How to present it

The module is the unit of production. The reader's unit is a credit question. The run page should
be the report, and module pages its appendix.

1. **What this run establishes.** One paragraph assembled from the seven concluding bottom lines,
   then "Not established: downside, forecast, ratings, legal, recovery, relative value, market".
2. **Credit story by question.** Business; financial base; liquidity and refinancing; macro and
   hedging. Each: the bottom line, the two or three highest-confidence findings, one chart or
   number set, a link to the module. Questions with no answer show one line and the blocker.
3. **Findings register.** Every finding row in the run, filter by question, confidence and module.
4. **Open items.** Blockers ranked by how many modules they stop, with the follow-up.
5. **Module matrix.** 20 rows: status, confidence, depends on, blocked by, words of analysis.

Module page: keep head, band, numbers, findings. Split Analysis into **View** (narrative, open)
and **Statements and registers** (collapsed tables). Chips show only resolved sources; unresolved
citations become one count line. A blocked module is a short page: status, blocker, what it
needs, and its handoff link.

## Handoff changes that make this mechanical

The page cannot query 178 table shapes. Six changes to the method would make the Markdown a
database rather than 20 documents:

1. Front matter on all 20: `status`, `blocked_by`, `depends_on`.
2. Typed section headings from a fixed set: View, Register, Statement, Calculation, Gap, Monitor.
3. One gap table shape for every module with a shared gap id.
4. A finding id, a question tag and supporting row references on each finding.
5. A blocked module emits the short form only: status, blocker, needs. No registers of absence.
6. A named headline-numbers table per module, so Key numbers is declared and not guessed.

Without these, items 1, 2 and 5 of the presentation can still be built from the two universal
tables and the 13 front-matter blocks. The findings and open-items registers would stay unjoined.

## Summary

Showing the narrative fixed "very little analysis" and exposed the next problem: the page now
shows everything at one weight, and 43% of everything is a description of what is missing. The
most important change is at run level: lead with the seven conclusions the run reached, and reduce
each blocked module to one line naming its blocker.

Not verified: word shares come from a heading-keyword census, not a hand classification. The
gap-overlap count uses the first four words of each row. Only 1440px was measured. Other runs
were not reviewed.
