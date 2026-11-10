# Module view as a report with source chips — consolidated findings

Date: 2026-11-09. Inputs: the adversarial review of module presentation across 11 deploy
projects (this session); the [charts](#local_4c437fc4-94fd-4551-9b49-deb8c06aab6c) session's
module/chart gap list; the owner rulings recorded by
[RBOT-HTML setup](#local_c54dfddf-84f1-4507-b409-061b9b48e063) and
[Features](#local_fc4cbbf2-714b-45f9-a610-cb0d9a8876b8); and the Credit OS design rules at
Final-workflow-PY `apps/issuer-library/DESIGN.md`, commit `07e14eca` (the design the owner
approved: "use final workflows design and charts"). Target: `feat/credit-os-static-pages`.

## Design language (binding; from DESIGN.md at 07e14eca and the owner's rulings)

Vocabulary. Use these words in specs, code and UI text:

| Term | Meaning |
|---|---|
| Rail (56px), issuer header, workspace tabs, module navigator (238px), analytical canvas, evidence inspector (280px) | The shell's parts |
| Overview, Modules, Calendar, Forecast, Reports, Evidence | The run's tabs (owner added Calendar and Forecast; "all modules should be here") |
| Run activity | Read-only page over `activity.excluded` and `activity.issues`; no controls (Features ruling) |
| Primary output / Saved output | Which file is shown; neither verifies analytical acceptance |
| Candidate · not accepted | Acceptance label, grey badge; amber is for attention only |
| View source / Open source file / Back to analysis | Opens the exact module row / the original file / restores the trigger |
| Evidence & audit | Lazily rendered disclosure for inventories, requests, calculation transcripts, downstream handoffs |
| Not classified | Unknown provenance in the inspector; lists show a class only when the handoff declares one |
| Declared provenance classes | `Documentary Fact`, `Management Language`, `Analyst Interpretation`, `Insufficient Information` (what handoffs declare today; `screen.js:137`) |
| n.a. with its reason | Never "—"; missing is never plotted as zero |
| Chip (4px corners) | Inline codes and keys; in the library a removable filter chip. This document's "source chip" is the inline code on a claim or table cell |

Rules the new design must keep:

- Static pages from `file://`, no network, no dependency; runs start from `cpos_launch` only.
- Every figure is calculated in Python at build time; the page draws, it never computes.
- The module "opens selected analytical sections, not the entire Markdown handoff. Findings
  and a relevant analytical panel lead; supporting sections and limitations expand in place."
- "Exact decimal strings remain visible independently of chart geometry"; the page must not
  overflow horizontally; charts attach to their own source tables; chart order chronological.
- The frontend assigns no credit judgement, grade, probability or new analytical result;
  analytical outcomes never become provenance labels; green/red only where the producer
  declared them.
- Top bands, chart readings and cautions quote the handoff or are short legends.
- Forecast shows the not-run state without a CP-2G output; the model is published beside the
  report when CP-2G ran (plan Task 9).
- The 91-view catalogue is a planning reference, "not a claim that every figure is populated".
- No paid run as part of design work; no legacy seed cases.

## What is wrong today, checked against that language

| # | Finding | Severity | Design rule it breaks | Source |
|---|---|---|---|---|
| 1 | "View source" and `C558`-style chips resolve to the handoff line holding the claim; the inspector shows the model's own paragraph as the source. Handoffs carry 279 page citations (`K, page:118`); `source-text/*.jsonl` is page-addressed and its hashes match CP-0's inventory, yet no chip reaches an issuer page. | Critical | "Narrative claims and every plotted mark have exact-source actions"; AGENTS.md: preserve source references | Review |
| 2 | A module is a pager (CP-1: 28 pages, CP-0: 12) of equal-weight sections; appendix registers rank with findings; opening a module hides the module list. | Warning | "Findings and a relevant analytical panel lead; supporting sections and limitations expand in place"; audit content "does not compete with the main analytical reading path" | Review |
| 3 | Overview chart rows clip the value column at 1440px (`.chart-row` needs ~385px, gets 307px; `.summary-chart{overflow:hidden}`). | Warning | "Exact decimal strings remain visible independently of chart geometry" | Review |
| 4 | Module pages show "Saved output" and confidence but not "Candidate · not accepted"; only the Overview footer and `report.html` carry it. | Warning | Acceptance label is part of the view; "Saved output" does not verify acceptance | Review |
| 5 | The embedded `report.html` (Reports tab) and the Modules tab present the same handoffs with different evidence models and layouts. Two surfaces are by design (the report is embedded in a sandboxed reader); two evidence models are not. | Warning | One inspector, one "View source" meaning | Review |
| 6 | Hedge chart hard-codes TDG: axis Mar 2023–Sep 2027, base `2024-09-30`, `'FX forwards'` unit (`views.js:175-179`). | Warning | Values come from the handoff, not the frontend | Review |
| 7 | 21 of 25 navigator entries say "Not run in this run"; the body says that label does not show the module was not run. DESIGN.md's wording is "No output found"; the spec's is "a module a run did not produce says so". | Warning | "Module availability uses visible neutral words"; every state includes text, once | Review |
| 8 | 7 catalogued figures have no drawing code (S.6, EU.1–3, PD.1, RV.1; DR.6 draws only the empty frame). | Note | Catalogue is a plan, not a claim; record as planning status, not defects | Charts |
| 9 | Only S.1–S.4 and RV.1 can be built from handoffs (`handoff_delivery.py:110`); S.5, RV.3a/b, CR.1–3, DR.2–6 read an older format nothing feeds; `cp*_chart_series` is called by nothing. | Warning | Dead code behind catalogued "Figure producer" rows | Charts |
| 10 | 7 chart kinds drawn vs Deploy VI's 13 (no tornado, dumbbell, scatter, risk-matrix, horizontal bar); RV.1 drawn as grouped columns for want of a scatter. | Note | — | Charts |
| 11 | ~10 Deploy VI charts have no catalogue row; 7 more exist here only as tables. CP-8's `expected_realised` is not a gap (post-mortem dropped by ruling). | Note | — | Charts |
| 12 | Catalogue and 24 chart tests dropped from the lean copy; `restructuring_series.py:5` names a module that does not exist. | Note | — | Charts |
| 13 | Bottom line stated twice per module (navy band + Reader summary); source keys K/M/J explained on another page; `sectionGroups` regex misfiles headings. | Note | Top band quotes the handoff or is a short legend | Review |
| 14 | DESIGN.md says the library "has no metric filters"; the built library shows Leverage/Coverage columns and a "Credit metrics & period" filter group (plan 4 work). Not a module-view issue; the design doc or the page needs reconciling. | Note | DESIGN.md "The one app" | Review |

Modules: Deploy V–VII and Deploy Workflow have the same 24 modules as this version. Modular OS
(pre-Deploy V, not in METHODOLOGY-REVIEW) had CP-MON, CP-SR, CP-6E, CP-X and a richer
CP-2C/CP-3B; out of scope unless the owner rules otherwise.

## What other projects already solved (borrow, in Credit OS vocabulary)

| Borrow | From | Credit OS equivalent |
|---|---|---|
| Report order: conclusion → reader tables (≤6×8, one-line takeaway) → findings → appendix | Deploy V `CANON_SHARED.md` ~L250 | Already the DESIGN.md rule; the pager is the deviation |
| Inline source code opens file, page, verbatim excerpt | RBOT Direction C "source passport" | Evidence inspector, "View source" / "Open source file" |
| Legend for what a mark is (cited / calculated / model-authored) | Deploy VI mockups; design pack A/B/C | Keep as *where it resolves* (issuer page / handoff row / upstream module / gap); the *class* stays the handoff's declared provenance or Not classified |
| Status banner at the module top | Direction C | Issuer header + grey "Candidate · not accepted" badge |

## Design target: the Modules tab

Owner, 2026-11-09: "Direction holds" on `mockups/module-report.html`. The binding spec is
`2026-11-09-module-report-spec.md`; this section is the rationale it was built from.

One module = one analytical canvas, read top to bottom, same shell:

1. **Module head** — name, Primary/Saved output selector, "Candidate · not accepted" badge,
   as-of date, method revision. A module with no output: one neutral line (pick one wording:
   DESIGN.md's "No output found" or the spec's phrase), no second sentence.
2. **Navy band** — the handoff's bottom line, quoted once, with confidence and main limitation.
3. **Analytical panel** — the module's reader table or chart (≤6 columns × 8 rows), every
   value a source chip; exact decimals always visible beside the mark.
4. **Findings** — claim · creditor impact · source chips.
5. **Limits** — contrary evidence, gaps, monitoring; expand in place.
6. **Evidence & audit** — collapsed: registers, inventories, calculation transcripts, downstream
   handoffs, complete and unchanged.

The navigator keeps the grouped section outline as in-page anchors; it no longer pages.

Source chips:

- Label: readable source and page (`10-K FY24 · p.118`), never a bare code. Upstream
  references read `CP-1 · D4`.
- Resolved at build time in Python (`update_library.py`), emitted in `data.js`:
  `{kind: issuer_page | handoff_row | upstream | gap, source_hash, page, line, quote_found}`.
- Click → evidence inspector: the exact handoff row (today's behaviour), then the issuer page
  text from `source-text` with the cited sentence highlighted, "Matches publication" when the
  file hash equals CP-0's inventory, "Open source file" for the original.
- Provenance class in the inspector = what the handoff declared, else Not classified. The chip
  kind is a fact about resolution, not a judgement.
- A claim with no resolvable locator gets a `gap` chip; never a self-citation.

Charts in the module view, first wave: the approved model chart strip S.1–S.4 (CP-1), already
wired. S.5 and CR.1–3 (CP-4, CP-2D, CP-3C) are catalogue "First" rows whose code exists but
reads the wrong format (#9); wiring them is a separate task, not part of the chip work.

## Component sources (owner, 2026-11-09: "Use assets from here or copy and make your own from the examples")

Same convention as `DESIGN-SOURCES.md`: Untitled UI React components as the anatomy, adapted
as original DOM/CSS in Credit OS tokens; no React, Tailwind or Untitled UI runtime bundled.

| Untitled UI component | Used for | Adaptation |
|---|---|---|
| [Tags](https://www.untitledui.com/react/components/tags) — size `sm`, `dot`, `count` | Source chips on claims and cells. Dot colour = resolution kind (blue issuer page, navy handoff row, blue-grey upstream module, grey gap); `count` when one claim cites the same page more than once | No `onRemove`/checkbox variants in content; removable tags stay the library's filter chips. 4px corners, Red Hat Mono label, 11px floor |
| [Avatars](https://www.untitledui.com/react/components/avatars) — size `xs`, `rounded={false}`, `initials`, `placeholderIcon`, `border` | Source identity mark in chips and the inspector: initials are the handoff's source key (`K`, `M`, `J`); placeholder icon is the Lucide document-type glyph for a source without a key | Square-ish, not circular: these are documents, not people |
| Avatars — `AvatarLabelGroup` (`sm`) | Inspector source header: file name as title, `p.118 · sha256 d75c…` as subtitle | — |
| Avatars — group stack with `+N` overflow | A finding backed by several sources shows the first three marks and `+N`; opening it lists all | `ring` in panel colour |
| Avatars — `verified` / `status` indicators | Not used for hash state. "Matches publication" stays the grey text badge DESIGN.md already uses; a changed or missing file is the amber badge | Green is reserved for producer-declared states |

Licence: the Untitled UI React source is at github.com/untitleduico/react, which
`DESIGN-SOURCES.md` records as MIT. The fetched component pages state "free and open-source"
but print no licence string; confirm the LICENSE file in that repository before copying any
code, and record the commit in `SOURCE.md`. Copying examples means the anatomy and states; the
pixel sizes come from Credit OS tokens (the pages name none).

## Work it implies (not sequenced; no code changed yet)

- Citation resolver (Python): parse `K, page:118`, `pages 31-32`, `[CP-1: D4]`; verify quote
  presence in `source-text`; emit chip data. Add a per-row locator column to handoff summary
  tables where rows have none (CP-0's findings table) via the module prompts.
- Module renderer: six-part canvas replacing the pager; outline as anchors. Record edits in
  `SOURCE.md` as the plan requires.
- Fix `.chart-row` widths; derive `hedgeChart` axis and base date from the handoff and as-of.
- One evidence model for `report.html` chips and the Modules tab (the report adapter can reuse
  the resolver output).
- Decide the no-output wording and update DESIGN.md or the page to match.
- Restore the catalogue and chart tests to this repo; delete the dead `chart_producers`
  reference; mark #8–#11 in `catalogue.csv` status, not as library defects.
- Reconcile #14 (metric filters) in DESIGN.md.

Spec amendment needed: `docs/superpowers/specs/2026-11-09-credit-os-static-pages.md` item 4
describes Modules as the owner approved it in the running app ("reader summary, findings and
section outline, with source links"). This document's target replaces the paging reading mode;
the owner's words for the change: "each module should be a report with evidence chips".

Not verified: nothing above was run or built.
