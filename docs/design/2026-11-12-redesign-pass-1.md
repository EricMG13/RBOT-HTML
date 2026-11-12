# Redesign pass 1: run header, Modules and Overview (2026-11-12)

Owner: "general look and layout is better than current, but based older codebase … consider what can
be adapted, repurposed, conflicts (especially when they are not better than current rules, such as no
visible CP-IDs, charts must always be visible within modules)", then "Yes, start" on the Modules and
Overview layout, "refresh design for new PRs", and "cross check with decisions made in prior PRs not
reflected in the design. for example, starting a new run on an issuer from their report page".

Source: the Claude Design project "RBOT first-run experience redesign" (screens L1-L6 of the issuer
library, R0-R5 of run start), drawn against an older copy of this code. Its colours, fonts, radii and
shadow already matched `screen.css`, so it is applied as layout and type. Branch
`claude/redesign-modules-overview`, stacked on `claude/redesign-review-adaptation-892369` (PR 62).

## Built in this pass

| Screen part | Now |
| --- | --- |
| Run header (every run tab) | Back link "Issuer library"; issuer name; a meta line (the catalogue's short name · sector · N runs); "As of"; over http, "Start a run on this issuer" (the issuer's latest run, PR 52's target). The run code and "Change run" left the header. |
| Tabs | Text only; the six labels and their order unchanged. |
| Strip | Showing run, evidence date, pathway, run code as stored, format badges; "All runs of this issuer" at the right. |
| Columns | Navigator 250px, inspector 340px (220px and 300px at 1300px and below; unchanged at 1050px and below). |
| Navigator | Uppercase group headings, lighter entries, the open entry's outline under it. Seven groups, names only. |
| Module page | Group and module name as the eyebrow; the bottom line as the headline (earlier format: with Confidence, Main limitation, "Quoted from the handoff", View source; no navy band); findings as a list; prose at 15px/24px, 66ch; registers, calculations and the audit list as bordered fold rows. Charts stay open on the page. |
| Inspector | A figure's value leads; each block is a titled card; quotes are set as quotes. |
| Overview | Two columns from 1301px: the credit view, bottom line by module and limitations at the left; key charts (with a link to the chart index) and nearest dates at the right. Same passages, same order. |
| Report history, Changes, Forecast, Evidence | Body edges aligned with the header. Report history's own "Start a run" link moved to the header. The Overview's "Chart index" link opens Forecast at the index, on the model last chosen. Nothing else. |

## Not adopted from the mock-up, and why

| Mock-up | Kept instead | Why |
| --- | --- | --- |
| Module codes in the navigator, eyebrows and handoff rows | Names only | Owner ruling, 2026-11-12 |
| Charts in a closed fold on a module page | Charts open on the page | Owner rule |
| Four navigator groups, an eight-part outline | Seven groups, the page's own part list | Decision 5; the mock-up predates Key numbers, Timeline, Maps |
| No Changes tab | Six tabs | M5, M8 |
| Tabs on the title row on Modules | One header on every tab | One chrome; costs 73px of height at 1440×900 |
| "Change run" in the strip | "All runs of this issuer" | It says what it opens |
| Lightest grey text (`#8a90a3`) | `--text-quaternary` | Contrast; the grey is used for dots only |
| Base / Management / Stress switch on Forecast | Main's period-columns grid | Forecast period columns plan, rulings 1-4, 11 |

## Controller rulings in this pass (cost if wrong: a restyle)

1. The module's `h2` stays its name; with a bottom line it is drawn as the eyebrow, without one as the
   headline.
2. "Bottom line" headings of a new-format passage and of the Overview lead stay in the page, visually
   hidden; the headline is that passage.
3. Overview keeps "Written by <module>" as written, in the eyebrow.
4. Nearest dates stays a table (caption, header cells) drawn as rows; Chrome's accessibility tree
   still reports table, rows and cells.
5. The meta line's first part is the catalogue's `issuer` field, the value the library home shows,
   even where the catalogue fell back to the upper-cased issuer id.
6. A fold summary's accessible name is "<title> <detail>" without the " · ".
7. The source page stays inline after the file name in the inspector.

## Open, for the owner

- Library home: issuer rows (mock-up L1) against "one item per column, no per-issuer run count"
  (owner, 2026-11-10); D9, D14.
- Run date ("Ran on") against "Dates refer to evidence, not execution" (D12).
- Run start: the mock-up's Documents → Purpose → Confirm → Start against "Stage 1 is pathway
  selection"; "From file" issuer name and currency against "no second classifier".
- Earlier-format runs: the Overview prints "No bottom line in this handoff." for every module although
  each module page shows the handoff's summary bottom line (H7).
- The comparison module is not excluded from Overview in code (M5 says it is not shown there); read
  from code, not reproduced.
- Line limit: this branch is over 800 changed lines, most of them tests; the natural split is
  header, navigator, module page and inspector first, Overview and the fixes second.

## Earlier decisions against the redesign (cross-check, 2026-11-12)

Read by a read-only agent at f3ae3a1 from `AGENTS.md`, `docs/rulings`, `docs/design`,
`docs/superpowers`, the library README, `VERIFICATION.md` (from 2026-11-10, to line 340) and PRs 47,
48, 52, 56. Code was read, not run. "Mock-up" is the Claude Design file; "Built" is this branch.

| # | Decision | Source | Mock-up | Built | Action |
|---|---|---|---|---|---|
| 1 | Start a run from an issuer, served over http, carrying its latest run | PR 52; existing-issuer spec §4 | Header button on every tab | Was Report history only | Header link, same gate and target (done in this branch) |
| 2 | Rail: Start a run, Issuer library, Run activity, Search | Decision 12; PR 47 | Start a run last | Kept | Keep |
| 3 | A "Start a run" button on the library home | PR 52 gate | L1 blue button | Not in scope | If built: link `/`, shown only over http |
| 4 | "Start again from this run" for failed, capped, rejected or interrupted runs | Existing-issuer spec §4 | Silent | Run start not in scope | Keep |
| 5 | Existing-issuer notice and "from run" marks; dates never carried | PR 52 | Silent | Not in scope | Keep |
| 6 | Paid action is Submit on an approved summary, USD 20 cap | Run-start-submit ruling | "What Submit does" | Not in scope | Keep the text |
| 7 | Model and effort only at Advanced; Balanced by default | 2026-11-12 amendment | Silent | Not in scope | Keep |
| 8 | Web search statement for private cases before Submit | 2026-11-12 amendment | Silent | Not in scope | Keep |
| 9 | Stage 1 is pathway selection; levels Basic / Standard / Advanced | Staged run start spec §3 | Documents first | Not in scope | Owner's call |
| 10 | No second classifier; only period ends are prefilled | Staged run start spec §4 | "From file" name and currency | Not in scope | Prefill only what the launcher reads |
| 11 | The summary names the run the comparison uses ("Changes" row) | M5 amendment | Silent | Not in scope | Keep |
| 12 | Report history: one row per run, as-of first, then start time | Decision 4 | Adds "Ran on" | Kept | Keep the order and "N not assessable" |
| 13 | Earlier format and Earlier methods badges | H7; PR 48 | On L1 and L2 | Kept in history and strip | Add to library rows when built |
| 14 | Run date shown (D12) | Screens pass D12, open | "Ran on" | Not in scope | Owner's call |
| 15 | Distinguish runs of one issuer (D9) | Screens pass D9, open | Issuer rows | Not in scope | Owner's call |
| 16 | Acceptance state beside the actions (D3, D13) | Screens pass | Silent | Kept in the module head | Keep |
| 17 | Short Credit Snapshot pathway and its labels | M6 | Silent | Kept | Keep |
| 18 | Six tabs including Changes; the comparison runs last; a first run says so | M5, M8; PR 56 | No Changes tab | Kept | Keep six tabs |
| 19 | The comparison module is not on Overview | M5 | n.a. | Not enforced in code (predates) | Owner |
| 20 | Overview: lead module order, bottom lines, limitations once, key charts, five nearest dates | H5 | Reflects | Kept, two columns, same order | Keep |
| 21 | Earlier-format Overview selects only reader passages | H7 | Silent | Kept ("No bottom line in this handoff.") | Owner question |
| 22 | Module page: passages, then charts, timeline, maps, then the rest; analysis open | H1, H4 | Folds charts and registers | Kept, charts inline | Do not fold charts |
| 23 | Navigator flat, always open, seven groups, names only | Decision 5 | Codes, four groups | Kept | Keep |
| 24 | No module code or step id on screen | 2026-11-12 amendment; PR 25 | Codes on L4, L5, L6 | Kept | Keep |
| 25 | A figure opens the inspector: file, page, quote, calculation; quiet Basis | Decision 7; H3 | Reflects | Kept, as cards | Keep |
| 26 | Key charts repeated on Overview; chart index on Forecast | Decision 3; PR 39 | Reflects | Overview's "Chart index" link opens Forecast at its top | Link to the index itself |
| 27 | Forecast grid: seven column groups, Base and one Downside, other cases closed, `n.a.` with reason | Forecast period columns plan, rulings 1-4, 11 | Base / Management / Stress switch | Not in scope | Keep the grid, not the switch |
| 28 | Forecast: model selector, Download original HTML, assumption register, Built from | PRs 5-7, 21 | Silent | Not in scope | Keep |
| 29 | Evidence: four lists; files listed only; Supplied, not used; Download all; Run record closed | Decisions 9, 10 | Reflects, with codes | Kept | Keep; no codes |
| 30 | Document date "Not recorded"; no changed-source notice without a hash comparison | PR 47; screens pass | Shows dates and an amber notice | Not in scope | Do not draw data the run lacks |
| 31 | Run activity shows only runs in progress and queued | Decision 10 | Reflects | Kept | Keep |
| 32 | Library home: one row per run, one item per column, no per-issuer run count, filters, selected-run panel | Owner 2026-11-10 (impeccable pass) | Issuer rows with a Runs count | Not in scope | Owner's call |
| 33 | Selected-run panel beside the table (D14) | Screens pass D14, open | No panel | Not in scope | Owner |
| 34 | `n.a.` not a dash; "run" not "case" | Screens pass | Silent | Kept | Keep |
| 35 | No page scroll at 1280 and 1440; tables scroll in their own box | D4; impeccable pass | Silent | Kept | Keep |
| 36 | Reader check against the VMO2 reference, recorded | AGENTS.md | n.a. | Done in this entry's verification | — |

Not verified: PR bodies other than 47, 48, 52 and 56; `2026-11-10-context-form-proposal.md`,
`2026-11-09-run-page-content-review.md`, the facility schedule plan and the static pages spec;
`VERIFICATION.md` below line 340. A decision recorded only there may be missing.
