# Modules tab as a module report with source chips — spec

Owner decision, 2026-11-09: "each module should be a report with evidence chips" → mockup
`docs/design/mockups/module-report.html` → "Direction holds". Findings and design language:
`docs/design/2026-11-09-module-report-findings.md`. Amends spec item 4 of
`docs/superpowers/specs/2026-11-09-credit-os-static-pages.md` (feat/credit-os-static-pages).

## Scope

In: the Modules tab (`views.js` module rendering, `screen.js` inspector), a Python citation
resolver in the library build, the `data.js` chip contract, the Overview chart-row widths, the
hedge chart constants. Out: new charts beyond the wired S.1–S.4, Forecast/Calendar, the
library table, any change to module prompts except an optional locator column (below).

## Rendering (per module, one scroll; order fixed)

1. Module head: module name, code, "Current methodology", handoff file and line count; right:
   grey badge `Candidate · not accepted` (or the run's acceptance state), output selector
   (`Saved output · n of m` / `Primary output`), Handoff download.
   No output: one line, "No output found", nothing else on the canvas.
2. Navy band: the handoff's `Bottom line` cell verbatim; `Confidence`; `Main limitation`;
   footer `Quoted from the handoff · <file> · line <n>`.
3. Analytical panel: the module's chart data tables (S.1–S.4 for CP-1) as chart rows with
   the exact value always rendered (`strong`, never clipped) and a chip set per row; below,
   a key-numbers table ≤6 columns × 8 rows built from the module's reader tables. Empty cells
   print `n.a.` with a `title` reason; never `—`.
4. Findings: each row of the `Finding | Creditor impact | Confidence` table: claim, creditor
   impact, confidence pill, chip row.
5. Analysis (owner, 2026-11-09: "Yes, show narrative"): every section of the analysis groups
   (not Limits & monitoring, not Evidence & audit) that parts 2–4 did not consume — Bottom line,
   Finding, chart-data and the chosen key-numbers table are consumed — renders open, in handoff
   order, with its heading, prose blocks as paragraphs and tables as compact tables, every block
   carrying its chip set. Nothing is truncated; a register of many rows renders whole.
6. Limits and contrary evidence: the module's gap/limitation/monitoring sections, two columns;
   `Not supplied` items get gap chips.
7. Evidence & audit: `<details>` closed; Front matter, Request, source-context assessments, the
   extra rows of consumed tables, and the technical audit last, each as a line-number list.

The navigator keeps the module groups; the section outline becomes "On this page" anchors to
the seven parts (`head`, `bottom-line`, `numbers`, `findings`, `analysis`, `limits`, `audit`).
Hash routes stay `#<module>/<anchor>?c=<run>&e=<chip-id>`.

## Chips

Visual: Untitled UI Tag anatomy in Credit OS tokens; height 24px, 4px corners, Red Hat Mono
11px label, leading 18px square avatar with the source key, trailing 6px dot for kind.

| kind | avatar | dot | label | click |
|---|---|---|---|---|
| `issuer_page` | source key from CP-0 inventory (`K`, `M`, `J`), navy | blue | `p.<page>` or `p.<a>–<b>` | inspector: handoff row + page excerpt |
| `handoff_row` | module short code (`C1`, `C0`, `A` for CP-1A), blue-100 | navy | `L<line>` | inspector: handoff row |
| `upstream` | upstream module code | blue-grey | `D1 · D3 · E1` or `CP-1A · E2` | inspector: the upstream register row |
| `gap` | `?`, dashed | hollow | `no page` / `Not supplied` | inspector: the gap text |

Legend line under each chart panel names the four dots.

## Data contract (`data.js`, built by Python)

```json
"chips": {
  "<run>/<delivery>/CP-1.md:358": [
    {"kind": "issuer_page", "source": "K", "file": "TDG_2024-09-30_10-K_…jsonl",
     "sha256": "d75c…edab6", "hash_matches_inventory": true,
     "page": 123, "page_end": null, "quote": "Cash paid during the period for interest, net",
     "quote_found": true, "excerpt": "...<page text window>..."},
    {"kind": "handoff_row", "module": "CP-1", "line": 358, "cells": {"Period": "FY2024", "EBITDA / cash interest": "3.29", "Reporting unit": "x", "Basis and limitation": "..."}}
  ]
}
```

Resolver rules (`src/deploy_workflow/credit_os_catalogue.py` or a sibling module):

- Parse, in a cell or paragraph: `K, page:118`, `K, pages 31-32`, `page:123`, `pages 2-5`
  (source inferred from the enclosing sentence's last named key), `[CP-1: D4, F1]`,
  `D1, D3, E1` trailing register codes.
- Source keys and hashes come only from the run's CP-0 `Complete supplied inventory` table;
  `hash_matches_inventory` compares with `runs/<run>/source-text/<file>` on disk.
- `quote_found`: the quoted string in the cell (text inside “ ” or the numeric cell value with
  thousands separators tolerated; a negative `-n` also matches the accounting form `(n)`, ruling
  R3) occurs in that page's `text`; the chip carries `match`, the exact page span matched, and
  the page marks only that. Never fuzzier than that.
- Source keys are the run's CP-0 inventory keys verbatim (single letters or multi-word aliases
  such as `Annual filing`); a citation may use an alias's leading word when CP-0's "Role in this
  review" column leaves one non-"Alternate" candidate (ruling R23); otherwise `… · ambiguous`.
- A claim with no parseable locator → one `gap` chip, label `no page`. A `Not supplied: …`
  cell → `gap` chip labelled `Not supplied`.
- The resolver adds nothing analytical: no inferred pages, no inferred classes. Provenance
  class in the inspector = handoff-declared (`Documentary Fact | Management Language |
  Analyst Interpretation | Insufficient Information`) else `Not classified`.

## Inspector

Order: source identity (avatar, source title from CP-0's classification cell, file, page) ·
badges `Matches publication` / `Changed since inventory` (amber) · `Quote found on page` /
`Quote not found` (amber) · provenance badge · Claim · Handoff row (field list + basis) ·
Source page excerpt with the quote in `<mark>` · Hash · actions `Open source file`, `Handoff`
· the reading-boundary note. `Back to analysis` / `Esc` restore the trigger and scroll.

## Fixes folded in

- `.chart-row` grid: `minmax(150px,1.1fr) minmax(140px,2fr) 72px auto`; `.summary-chart`
  loses `overflow:hidden`.
- `hedgeChart`: axis start/end and base rule from the run's as-of date and the table's dates.
- One evidence model: `report-adapter.js` chips read the same `chips` map.

## Tests (answer keys written from fixtures, not from code)

- Resolver: `K, page:118` → `{source:"K", page:118}`; `pages 31-32` → `page:31, page_end:32`;
  `[CP-1: D4]` → upstream; a cell with no locator → one `gap`; `quote_found` true for
  `Cash paid during the period for interest, net` on page 123 of the TDG 10-K fixture and
  false for a changed digit; `hash_matches_inventory` false when the file is altered.
- Rendering (`node --test`, static): the module canvas has exactly the seven anchors in order;
  a fixture narrative section renders open under `analysis` with its chips;
  no `—` text node in a table cell; every `.chart-row strong` has a non-empty value; no
  `font-size` below 11px in `screen.css`; the no-output state renders one sentence.
- Browser (`file://`, 1440 and 1280): no horizontal overflow; the value column of every chart
  row is inside the card; a chip click opens the inspector with the page excerpt; Esc returns
  focus to the chip.

## Not in this spec

Wiring S.5 and CR.1–3 to handoffs; new chart kinds; the Deploy VI charts without catalogue
rows; the metric-filter reconciliation in DESIGN.md (#14 in the findings).
