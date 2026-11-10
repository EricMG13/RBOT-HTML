# Library and report screens: what the reader needs, what is production detail (2026-11-10)

Owner: "refine and improve its enterprise SaaS look and persona requirements … remove anything not
complimentary to UX; distinguish what is backend relevant, but adds no value to the user in
frontend", then "run /adversarial-reviewer … the design not the code", and "check PR 20 too".
Method: `/impeccable` (distill, clarify, polish, Operate mode) and an adversarial design review, by
one agent, no sub-agents. Branch `claude/forecast-publication-screens` = `claude/forecast-publication`
(PR 19) + `claude/period-charts` (PR 20) + this pass. Looked at in headless Chrome over `file://` at
1440 and 1280 on the four retained TDG runs; nothing displayed from a handoff changed value, period,
unit, source reference or limitation.

## Who reads these screens

From the Credit OS product statement (`Final-workflow-PY/apps/issuer-library/PRODUCT.md`; this
repository has none): a credit analyst on a Windows desktop, in a local browser, who (1) finds a
run, (2) reads what it concluded and how far to trust it, (3) checks a figure against its source
when it matters, (4) opens or downloads the report. They do not operate the pipeline.

| Requirement | Where it is met |
|---|---|
| Tell runs and reports apart | Library row (run id on one line), report rows and the report selector name the run |
| Know what a run concluded, at a glance | Count line, coverage strip, credit story, module matrix (status only) |
| Know what is not established | Not-assessable lines, Open items, one "Not established for this run" line |
| Know the report's standing before quoting it | Acceptance badge beside Open report, on report rows and in the reader |
| Trace a figure | Chips and View source open the inspector; handoff, line and hash live there |
| Not be alarmed by nothing | Amber only for a changed or invalid source; never-assessed completeness is neutral |

## Frontend content: reader value or production detail

Kept in the reading path: issuer, run id, sector, evidence date, ratios with their basis, rating,
bottom lines, findings, creditor impact, confidence, main limitations, declared status, page chips,
acceptance state, analytical qualification.

| Was on screen | What it is | Now |
|---|---|---|
| SHA-256 folder id as a deliverable's link text (library panel) and beside every report row | Delivery folder name | The report's name; the id is the link's title |
| "Candidate · file hashes checked at build" | Build integrity check | "Candidate · not accepted" (the recorded acceptance; "Accepted" when recorded) |
| "Built from 20 handoffs · byte-identical by SHA-256" and "Files in this deliverable · 24" (two bars above a report) | Provenance | One disclosure: "Built from 20 handoffs · each matches its run file · 24 files"; the SHA-256 prefix column stays inside it |
| Module head: "Current methodology · Handoff `CP-1.md` · 33 sections" | A constant, a file name, a parse count | Removed; the module is named, never coded; Evidence & audit keeps the section count |
| Module head: "Saved output" with one output | Storage term | Removed; shown only when a label tells outputs apart |
| Band link "CP-1.md · line 54" | File locator | "View source"; the module's handoff and the line are its title and the inspector's |
| Module matrix: "Words to read", "Words of reference" | Handoff size | Removed; each fold still says how long it is |
| "1 citation without a page" on all 33 findings of the Overview | Citation-resolution count | Overview findings show resolved chips only (as its spec says); the count stays on the module page |
| Five empty metric cards "Not established for this case." | Absent data, repeated | One line naming the five measures |
| Amber "Workflow completeness · Not assessed" box; Completeness filter | A checklist no run has | Neutral note; the filter is offered once a run records a completeness |
| "Reset filters" always shown; pager "1 / 5" on the list of reports | Idle controls | Reset shows while something is filtered or sorted; the list has no pager |
| "Return to library" in the report bar | Duplicate of the rail and Change run | Removed |
| "Change case", "this case", "another case" | A second word for a run | "run" throughout |
| "View source ↗" | An out-arrow on an in-app action | "View source"; ↗ only on links that open a new tab |
| `—` for a missing figure | | `n.a.` with the reason as title, as on the module and forecast pages |
| Embedded report navigator: "Canonical data foundation", "Ic debate challenge" | The delivery's skill titles | The workspace's module names; the delivery's own title is the link's title |

Production detail left in place because it is already where an auditor looks: the evidence
inspector (line, handoff, hash), Evidence & audit lists, the Evidence tab's file identity, the
provenance table; each names its module, none shows a code (see Codes off the screen).

## Adversarial design review (three hostile readers)

Verdict before the fixes: **BLOCK** (D1, Critical by promotion). After them: **CONCERNS** (two
warnings open, D9 and D10). Fixed here unless marked open.

| # | Sev | Reader | Finding | Disposition |
|---|---|---|---|---|
| D1 | Critical (two readers) | Breaker, newcomer | Four reports of one issuer and date carried one name; the only difference on screen was a 64-character hash, and the report selector's four options were identical. A reader opens or quotes the wrong run's report. | Fixed: report rows and selector name the run; hash is a title |
| D2 | Warning | Breaker | The Completeness filter could only return nothing (no run is assessed), and its state was an amber alert on every run: an alarm that always fires. | Fixed |
| D3 | Warning | Truster | "Open report" was the primary button with the report's "not accepted" state in 11px text at the far end of the panel. | Fixed: acceptance badge beside the buttons |
| D4 | Warning | Breaker | At 1280px a 31-character run id wrapped and the row grew from 41 to 61px. | Fixed: one line, 11px at ≤1300px, ellipsis and title beyond that |
| D5 | Warning | Newcomer | One module had two names: "Financial foundation" in the workspace, "Canonical data foundation" in the embedded report's navigator. | Fixed |
| D6 | Warning | Newcomer | "run", "case" and "saved output" for one thing; "Blocked" as an unlabelled badge beside the acceptance badge. | Fixed: "run"; the declared badge's title says whose word it is |
| D7 | Note | Breaker | A sorted column looked like every other (aria-sort only). | Fixed: ↑ / ↓ and primary text on the sorted header |
| D8 | Note | Truster | The delivery's limits note opened the report as five bold 11.5px bullets above its title. | Fixed in the adapter: regular weight, 12px, 100ch |
| D9 | Warning, open | Breaker, newcomer | Library rows of one issuer differ only by run id and by rounding (6.5744× beside 6.57×); "Latest run per issuer" lists four runs that share the latest evidence date. No column says what a run is in the reader's terms (when it ran, how many modules conclude). | Owner: a distinguishing column, or a tie-break in the screening rule |
| D10 | Warning, open | Newcomer | Chips print a handoff line number (`C1 L107`); avatar letters and dot colours are explained only by a legend under charts. | Fixed (owner ruling, see Codes off the screen): the row chip reads "Handoff", the line stays in its title and the inspector |
| D11 | Note, open | Newcomer | The coverage strip is twenty module codes; names are tooltips. | Fixed: the strip is the module names as small wrapping pills (see Codes off the screen) |
| D12 | Note, open | Truster | No run date on any screen ("dates refer to evidence, not execution"), so an old analysis looks like today's. | Owner: show the run's own date where the manifest records one |
| D13 | Note, open | Truster | "Candidate · not accepted" and "Analytical qualification: partial" are never explained. | Owner: wording is governance, not design |
| D14 | Note, open | Breaker | The selected-run panel is below the table; with many runs the table scrolls away on selection. | Owner decision already open (panel beside the table) |

## PR 20 (reader charts over time)

Sound: periods on the x axis, exact values on the columns, one button per period with its values in
the accessible name, chips under the period, sideways scroll in its own box. One refinement here: a
period is at most 320px wide, so a two-period chart sits at the card's left under its title and
legend instead of at the card's two ends (520px apart at 1440). Open for its author: two-period
cards could share a row; a single-series legend repeats the card's subject; a negative value is
proven on a fixture only.

## Amendments to the specs

- `2026-11-09-run-report-spec.md`, item 6: the module matrix is name, confidence and declared
  status; the two word columns are removed. Item 3 already asked for "resolved chips" on findings.
- `2026-11-09-module-report-spec.md`: the head carries the module's name only (no code line, no
  title); the band's link reads "View source".
- `2026-11-10-impeccable-pass.md`, Left as found: `—` for a missing value is now `n.a.`.

## Codes off the screen

A reader sees what a code identifies, never the code. Display only: `data.js`, the retained
handoffs, hash routes, `href`s and `download` names are unchanged. Register references (`C9`, `G1`-`G8`,
`D1`, `E1`, `M1`-`M3`, `K`, `AP1`-`AP11`, `GAP-001`, `EVT-01`) stay. Checked by crawling every in-app
route of the four retained TDG runs and the four delivered reports for `CP-…` and step ids: 22,649 and
1,914 hits before, none after.

| Place | Was | Now |
| --- | --- | --- |
| Navigation item, module head `h2` | Title "CP-1"; a code line under the head | No title, no code line |
| `nameCodes` text | The name in an `abbr` whose title was the code; exceptions for the audit list, Evidence tab, Forecast tab, run activity, chips, coverage strip | The name; no exception; titles and `aria-label`s are named too |
| Coverage strip | `CP-1`, name in the title | The name in a small pill, `aria-label` "Name, state", no title |
| Handoff chip | `C1 L107` | "Handoff"; "Handoff row, line 107" in its title and label |
| Upstream chip | `A` avatar, "CP-1A · E2" | No avatar, "Business & governance · E2" |
| Evidence inspector | "Financial foundation (CP-1) · Line 54"; `…--CP-1.md` | "Financial foundation · Line 54"; "Financial foundation handoff" and the run |
| Band link, library source details | "CP-1.md · line 54" | "Financial foundation handoff, line 54" |
| Reports "Built from" | Module `CP-1`, link `CP-1.md` | Module name, link "Handoff" |
| Evidence tab | "Financial foundation · CP-1", labels and file identity with the code | The name; an output label equal to the code is not shown; "Financial foundation handoff" |
| Handoff text | `CP-2D`; `CP-6-GAP-001`; `CP-2R` | The module name; "Gap 1" on its own page, "Committee decision gap 1" elsewhere; "unnamed module" |
| Module the groups do not name | Listed under its code | "Unnamed module" |
| Step ids | A step column of ids, `T4.11 — …` headings with the id in a title, ids in prose | The column is not drawn; the heading shows the rest; an id reads as its title from the same output, a range "A to B", none found "a method step" |
| Delivered reports | Names in text only, the code added to a title; the delivery banners not named | Text, `title` and `aria-label`, banners included |

Why nine hits in the delivered reports were missed: the pass observed the navigator, the view and
the call, and the delivery's scope and limit banners sit outside them.

## Not done

No `PRODUCT.md` or `DESIGN.md` exists in this repository (`/impeccable init` and `document` would
write them). The delivered report's own layout inside the frame (its navigator tally "0 lim · 0
pass", "deploy-v-r14", its amber "CANDIDATE PREVIEW" beside the workspace's grey badge) belongs to
the delivery renderer and is unchanged. Phone widths were not looked at (headless Chrome's minimum
window is wider than a phone).
