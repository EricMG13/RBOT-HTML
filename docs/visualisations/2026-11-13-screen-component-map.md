# Issuer library redesign: screen and component map (2026-11-13)

Status: built, 2026-11-13, on branch `claude/report-redesign-evidence` (head `53f4070` when this
status was written). The tables below are the map as drawn before the build; "What was built" at
the end lists where the build differs. Records of the build are in `VERIFICATION.md`.

Case used: TransDigm Group, as of 2024-09-30, Credit Snapshot, run `tdg-proof-snapshot-opus-002`
(13 modules). It is a historical case written under earlier methods; it shows layout and data
shape, not a current credit view.

## 1. Rules this map applies

Owner, 2026-11-13:

1. Review every screen, output and section and map each to a component.
2. Match the chart to the data type; do not repeat one component for different information.
   Repurpose assets, replace repeated words with icons, present more in less space, add a toggle
   where two presentations are useful, combine components, animate live state.
3. Nothing may look extracted from the Markdown.
4. Evidence is audit, tracing and governance. Sources, traces, IDs, registers, calculations and
   gap ledgers leave every other section and live only in Evidence. Other sections present
   findings and links.
5. Components come only from React Bits, shadcnblocks, Flowbite React, Uiverse loaders, HyperUI,
   Preline, Untitled UI and the Ant Design grid.
6. Choose every presentation for the reader: what they need, how they use it, why.
7. Nothing that is inter-module communication is displayed.

Decisions from the owner's answers:

| # | Decision |
|---|---|
| 1 | Components are redrawn in the library's own CSS and plain JS. No React, no build step, no library code copied. |
| 2 | A findings page keeps one small trace icon per paragraph, row or figure. No Source column, Basis text, file name or ID. |
| 3 | The icon opens a side drawer (part of Evidence) that ends with "Open in Evidence". |
| 4 | Per-module record views go. Evidence is the single home, organised by kind with a module filter. |
| 5 | Analysis tables become components chosen by data shape. Numeric ones get a Chart/Table toggle. The table as written is kept in Evidence. |
| 6 | Limitations prose stays on findings pages. Gap tables and ledgers go to Evidence behind a compact signal. |
| 7 | Scope: every library screen. The run start form and the HTML Model's internals are mapped only. |
| 8 | Handoff data only. Nothing is computed. Module-instruction changes are a follow-up list (section 9). |
| 9 | Motion is for live state and short one-off transitions. Nothing loops on a report page. Off under reduced motion and in print. |
| 10 | Fresh branch from main (`claude/report-redesign-evidence`). |
| 11 | Evidence opens on a governance summary, then tabs by kind. |
| 12 | The reader decides first and challenges second. |
| 13 | This map and three mock pages come before any build. |

## 2. The reader

A portfolio manager or credit committee member who has not read the source documents.

| | Decide (findings pages) | Challenge (Evidence) |
|---|---|---|
| What they need | The view, why, what would change it, what changed, what to watch | Where a figure came from, how it was calculated, what is missing, what was run |
| How they use it | Scan in minutes; open one module for depth; compare two cases | Follow one figure from statement to calculation to source page; filter by module |
| Why it shapes design | Judgement first, figures large, one idea per component, no audit vocabulary | Complete, searchable, dense tables are acceptable here |

## 3. Three places for content

| Place | Holds | Examples from the run |
|---|---|---|
| Findings pages (Overview, Changes, Modules, Forecast) | Judgement, figures, charts, events, links | Bottom line, key findings, scenario figures, break points, catalysts |
| Evidence | Audit, tracing, governance | Sources and hashes, Basis lines, calculations (D01 to D24), gap ledgers, registers (T2B.1 to T5.7), instructions sent, run record, cost, the tables as written |
| Not displayed (rule 7) | What modules write for each other or for the orchestrator | See below |

Not displayed anywhere in the library, Evidence included. It remains inside each module's
downloadable original handoff.

- Sections: Request, Next module, Front matter (every module); "Key located evidence for
  downstream owners", "Consumer readiness and command sheet" (CP-0); "Readiness for downstream
  use" (CP-1); "Upstream re-anchor and method trace" (CP-2E); "Module status and QA validation",
  "Forecast inputs (machine-readable)" (CP-2G); "Module status and scope", "QA validation"
  (CP-5); "Approved scope and research brief", "Workstream plan" (CP-DR); "Cross-Module Handoff
  Register", "Watchlist & Cross-Module Handoff" (CP-2A and the same registers elsewhere).
- Columns: Supplied handoff, Use in this module, Effect on this module, downstream_use,
  Consumer, Downstream Module, Receiving Module, Responsible Module, Command,
  Required Consumer Action, Consequence for CP-x, consumer_module_id.
- Sentences inside findings prose that only address another module ("Escalate to CP-4 review")
  are in a cell of a dropped column in every case found; no findings sentence is edited.

Open reading for the owner: I read rule 7 as "drawn nowhere". The alternative is "drawn in
Evidence only". Section 10 lists this.

What a findings page drops from a table it draws: Source, Evidence, Basis and Source Trace
columns (replaced by the trace icon); ID columns; the inter-module columns above. A limitation
attached to a shown row stays one click away on that row and prints expanded, because a
qualification must stay exact.

## 4. Component palette

Each is redrawn by hand from the anatomy read on the live page. "Repurposed" marks a use beyond
the component's usual one.

| ID | Component | Source | Used for | Motion |
|---|---|---|---|---|
| C1 | Sliding-pill navigation | React Bits Gooey Nav and Pill Nav | Main tabs (Overview, Changes, Modules, Forecast, Evidence) | Pill slides 300 ms once per click; no particles |
| C2 | Verdict panel | Untitled UI metrics (featured) + shadcnblocks Status | Bottom line with its lead sentence large | None |
| C3 | Stat tile with prior value | HyperUI Stats ("from" line), shadcnblocks stat-delta | A figure with its earlier period or earlier run | None |
| C4 | Joined figure strip | Preline KPI grid (one container, cell dividers) | Four to six headline figures in one row | None |
| C5 | Numbered findings feed | Untitled UI activity feed, shadcnblocks List Panel (numbered rank) | Key findings: bold lead, body, trace icon | None |
| C6 | Left-rule callout | HyperUI Toast "standout" (repurposed) | What would change the view | None |
| C7 | Two-sided board | HyperUI middle-line timeline (repurposed), shadcnblocks Comparison | Bull against bear drivers, each with its figure | None |
| C8 | Segmented toggle | React Bits Rubber Segment, Preline Segmented Control | Case switch (Base, Moderate, Severe); Chart or Table | Thumb slides 200 ms |
| C9 | Scenario cards | Preline Pricing Cards (repurposed: tier = scenario) | Scenario definitions: assumption, anchor, what it leaves out | None |
| C10 | Range track with threshold tick | Preline grouped progress list with pace tick (repurposed) | One measure across cases against a stated threshold | None |
| C11 | Break-point ladder | HyperUI Steps "check badges on track" (repurposed) | Ranked thresholds on one axis with scenario positions | None |
| C12 | Status checklist | React Bits Status Mark, Preline audit-scope marker | Gate items and readiness lists | None |
| C13 | Progress steps | Untitled UI progress steps, Preline stepper | Run progress; multi-step prose (remediation order) | Current step only, while live |
| C14 | Pathway flow | Preline stepper + Untitled UI tree connectors (combined) | Cause-and-effect maps | None |
| C15 | Dated timeline | Flowbite timeline (horizontal), Preline order status | Catalysts and events: past, next, later | None |
| C16 | Risk matrix | shadcnblocks heat-map chart (repurposed as 3 by 3) | Events by probability and impact | None |
| C17 | Fact list with leader lines | Preline description lists, HyperUI details lists | Company profile, exposures, terms | None |
| C18 | Question accordion | HyperUI accordions, Flowbite accordion | Research questions with an answer-state badge | Native open |
| C19 | Before and after card | shadcnblocks Comparison (content), Preline changelog timeline | Earlier run against current, with cause and effect | None |
| C20 | Module tiles | React Bits Accordion Gallery (repurposed), shadcnblocks Status | Thirteen modules: icon, state, lead sentence, expand | Expand 200 ms |
| C21 | Module dot strip | Preline segmented pills "x of N" (repurposed) | Which modules a run delivered, in one line | None |
| C22 | Trace icon and drawer | Flowbite drawer, Untitled UI slideout, Preline file-details drawer | Statement to calculation to source page to excerpt | Slide in 300 ms |
| C23 | Toast | Flowbite toast | "Hash copied", "Download started" | Fade |
| C24 | Tooltip | React Bits Warm Tooltip, Flowbite tooltip | Metric definitions, icon labels | Delay 400 ms |
| C25 | Tabs with counts | shadcnblocks tabs (count badges), Untitled UI tabs (underline) | Evidence kinds | None |
| C26 | Filter bar with chips | Untitled UI filter bar, Preline filter bars, HyperUI dismiss badges | Module filter and search in Evidence; library home filters | None |
| C27 | Audit table | Untitled UI table, shadcnblocks tables (mono, numeric, expandable rows) | Evidence only | Row expand |
| C28 | Reader stack | Flowbite avatar group, Preline KPI avatar row (repurposed) | Which modules read a source file, as stacked initials | None |
| C29 | Three-segment meter | Preline analytics table severity meter | Gap severity; High, Medium, Low confidence | None |
| C30 | Half-ring gauge | Untitled UI activity gauge, HyperUI circular progress | Governance counts ("13 of 13 delivered") | None |
| C31 | Loaders | Uiverse loaders, React Bits Lattice Loader and Status Mark | Run status: queued, running, done, failed | Loops only while a run is live |
| C32 | Empty state with ghost bars | Preline empty states, HyperUI empty states | A chart the module could not draw, with its stated reason | None |
| C33 | Section rail | React Bits Line Sidebar, HyperUI vertical menu with count badges | In-page index on a module page | None |
| C34 | Chart forms | Untitled UI line and bar charts, shadcnblocks charts (target line), HyperUI charts (data table beside every chart) | Section 5 | Draw-in once |
| C35 | Copy action | Preline description list with copy, Flowbite clipboard | Hashes and calculation IDs in Evidence | Icon swaps to a check |
| C36 | Command search | shadcnblocks Command, Preline command palettes | Jump to a calculation, source or gap in Evidence | None |

Layout: Ant Design's 24-column grid, breakpoints 576, 768, 992, 1200, 1600, with the gutter
capped at 4% so it never overflows a narrow container (carried from the reference branch).

Icons replace repeated words: status (done, running, failed, not established), leading or
lagging indicator, bull or bear, direction (negative, uncertain), unchanged, trace, copy,
download, category (debt, corporate, legal, macro).

## 5. Chart and component choice by data shape

Choice follows the shape and role of the data, never a heading or one module's current list of
tables. Module instructions are changing in other sessions, so a heading-based map would break.
First matching rule wins; an unrecognised shape gets a designed data card, never a raw grid.

| Shape | Becomes | Not |
|---|---|---|
| Line items by two or more periods (a statement) | Statement card: paired bars per line with a Bars or Figures toggle | A line chart through two points |
| Two periods of one measure | C3 stat tile with the prior value | A two-point line |
| Metric, values, definition | Grouped tiles; definition in C24 | A five-column table |
| Additive steps to a total (bridge) | Waterfall | Bars |
| Amounts by year (maturities) | Columns by year | A line |
| Parts of a whole by rank (debt stack, liquidity) | One stacked bar with a ranked legend | A pie |
| Measures by named cases (scenarios) | C8 case toggle over C3 tiles, plus C10 tracks | A table with a column per case |
| Rows are the cases themselves | C9 scenario cards | A table |
| Ranked thresholds on one measure | C11 ladder | A numbered table |
| Rows with two graded columns (probability, impact) | C16 matrix | Two badge columns |
| Status per item | C12 checklist | A status column of words |
| Item, figure, side | C7 two-sided board | A table |
| Earlier against current | C19; a dumbbell when both are numbers | Two columns |
| One state per module | C20 tiles; the repeated state as an icon and a count | Twelve rows saying "Unchanged" |
| Question and answer | C18 | A table |
| Fact with category | C17 grouped by category pill | A three-column table |
| Dated rows | C15 | A table |
| From, relationship, to | C14 | An edge table |
| Ordered prose steps | C13 vertical | Paragraphs |
| Judgement prose | Reading blocks: C2, C5, C6 | Headed paragraphs with Basis lines |

Every chart has: one axis, a legend only for two or more series, direct labels on the values
that matter, a hover value, a Table toggle, a visible "Basis and limitation" footnote where the
module wrote one, and a trace icon. Nothing is recomputed: positions come from values the
module wrote.

## 6. Screen by screen

### 6.1 Shell (every page)

| Part | Today | Becomes | Why for the reader |
|---|---|---|---|
| Top tabs | Plain links | C1 | Shows where they are; one moving element |
| Run identity | Text line "TDG-PROOF-SNAPSHOT-OPUS-002 · Overview" | Issuer name large; a run chip (as of, pathway, state mark); run code only in Evidence | The run code is an audit key |
| Historical case | Not marked | Amber "Historical case, earlier methods" chip where it applies | Prevents reading an old case as current |
| Basis lines, Source columns | Inline text | C22 trace icon | Rule 4 |
| Feedback | None | C23 | Confirms a copy or download |

### 6.2 Library home

| Part | Today | Becomes | Why |
|---|---|---|---|
| Five filter selects | Five dropdowns in a row | C26: search plus chips with counts | Fewer controls; counts show what exists |
| Runs table | Flat table | Issuer cards: latest view lead sentence, as of, pathway pill, C21 strip; Cards or List toggle (C8) | A PM picks an issuer, not a run row |
| Issuer stat tiles | Tiles | C4 strip from the financial foundation module | Same data, one container |
| A run in progress | Not shown | Row with C31 loader and C13 steps | Live state is the one place motion earns its keep |

### 6.3 Report history

| Part | Today | Becomes | Why |
|---|---|---|---|
| Runs table with a text list of modules | Table | Vertical C15: one entry per run with state mark, date, pathway, C21 strip, "What changed" link | History is a sequence, and thirteen module names repeat on every row |

### 6.4 Overview

| Section | Today | Becomes | Why |
|---|---|---|---|
| Credit view: bottom line | Two paragraphs under "Written by Committee decision" | C2: lead sentence large, rest below, trace icon | The decision in one glance |
| Headline figures | Inline in prose | C4 strip of the figures the bottom line cites, from the financial foundation's metric table, each with FY2023 beneath | Scan before reading |
| What decides it | Not on the page (a table inside Committee decision) | C7: bull drivers left, bear drivers right, each with figure and the chair's reading | The "why" as a picture of the debate |
| Key findings | Paragraphs with Basis | C5 | Ordered, scannable |
| Contrary evidence and what would change the view | Paragraph | C6 | The trigger for changing their mind |
| What to watch | Not on the page | C15 from the decision module's dated events | Next action |
| Bottom line by module | Thirteen stacked paragraphs | C20: tile per module with icon and lead sentence; expands to the full bottom line; "Open module" | Thirteen paragraphs hide the one they want |
| Limitations | Paragraphs | Short list plus a gap signal ("N open gaps", C29) linking to Evidence | Decision 6 |
| Chart index, "Evidence and audit" links | Link lists | Removed; Forecast and Evidence are tabs | Navigation, not content |

### 6.5 Changes

| Section | Today | Becomes | Why |
|---|---|---|---|
| Closed, remaining, new | Bar | Kept | Already a visual |
| What changed: the issuer (Measure, Earlier, Current, Cause, Effect) | Table | C19 per measure; a dumbbell when both values are numbers; Cards or Chart toggle | Before and after is a comparison |
| What changed: the analysis (Module, Status, Cause, Why) | Twelve-row table | C20 tiles; unchanged modules collapse into one icon with a count | "Unchanged" twelve times is noise |
| Ledger | Table with filter | Evidence, Gaps tab | Audit |
| First run (no earlier run) | Text | Designed empty state (C32) | Explains why the page is empty |

### 6.6 Modules

Every module page: header (name, icon, state mark), C33 rail, then the four passages as C2
(Bottom line), C5 (Key findings), C6 (Contrary evidence and what would change the view) and a
short Limitations list with the gap signal. Analysis sections follow the shape rules. The table
below is this run's result of those rules.

| Module | Section in this run | Shape | Becomes |
|---|---|---|---|
| Source readiness | Effective source set and identity | Prose | Reading block; the source list itself is Evidence |
| | Events: Sources | Dated rows | C15 |
| Financial foundation | Three reported statements | Statement | Statement cards, Bars or Figures |
| | Financials and credit metrics (35 rows) | Metric, values, definition | Grouped tiles by family (earnings, leverage, cover, liquidity); definitions in C24 |
| | Revenue and EBITDA | Two periods, two measures | Paired columns |
| | EBITDA bridge | Bridge | Waterfall |
| | Leverage; Interest cover | Two periods of one measure | C3 tiles with a threshold note |
| | Liquidity; Debt stack | Parts of a whole | Stacked bars |
| | Debt maturities | Amounts by year | Columns |
| Business and governance | Operating measures | Measure, two periods, change, consequence | C3 tiles with the consequence beneath |
| | Company profile | Fact with category | C17 |
| | Transaction summary | Prose | Reading block |
| | Events; two maps | Dated rows; edges | C15; C14 |
| Fundamental credit | Credit view (four tables with a consequence column) | Metric with consequence | Four panels: figure left, consequence right; one panel per theme, each a different tile layout |
| | Strengths and weaknesses | Prose in two groups | C7 |
| | Map | Edges | C14 |
| Downside | Downside view | Measures by cases | C8 over C3, plus C10 |
| | Scenario definitions | Rows are cases | C9 |
| | Stressed flows and metrics | Measures by cases | Same component as Downside view (one data set, shown once) |
| | Break points ranked | Ranked thresholds | C11 |
| | Map: stress scenario | Edges | C14 |
| | Catalyst view | Prose with dates | Reading block beside C15 |
| | Event risk; what to watch (from the registers) | Two graded columns; indicator rows | C16; watch list with leading or lagging icons |
| | Stress design and status | Mixed | Base-period sentence as a chart footnote; method note, module status and confidence go to Evidence |
| Rates, FX and hedging | Macro and hedging view | Exposure rows | C17 cards by exposure |
| | Events: Hedges | Dated rows | C15 |
| Forward credit model | Forward credit view | Measures by periods and cases | Small multiples: one small line per measure, base and downside, with the FY2024 actual marked |
| Security selection | Recommendation (four security groups) | Rows are options | Comparison cards with a recommendation badge |
| | Relative value; Portfolio fit | Prose | Reading blocks |
| | Events: Instruments (13 rows) | Dated rows | C15 grouped by year; maturity columns toggle |
| Legal and covenants | Legal file gate | Status per item | C12 |
| | Capital structure | One row | C17 |
| | Covenant headroom chart; two maps | Not drawn by the module | C32 with the module's stated reason |
| Evidence validation | Traceability conclusion | Status per item | C12 with C29 |
| | Remediation priority map | Ordered prose steps | C13 vertical |
| | Clearance decision; Overall traceability view | Prose | C2 (smaller); reading block |
| Committee decision | Decision | Item, figure, side | C7 |
| | Debate record; Portfolio debate; Committee challenge | Prose | Reading blocks, two-column for bull and bear |
| | Portfolio limits chart | Not drawn | C32 |
| | Events: Decision and watch | Dated rows | C15 |
| Changes since the last run | Both tables | As 6.5 | The Changes tab shows them |
| Research questions | Executive answer | Question and answer | C18 with answer-state badges |
| | Causal synthesis and scenarios | Prose | Reading block |

### 6.7 Forecast

| Part | Today | Becomes | Why |
|---|---|---|---|
| Model page | HTML Model embedded | Kept (mapped only); framed with a case toggle (C8) | Reuse is a project rule |
| Run charts | Seven charts, similar forms | Small multiples with the form per shape (section 5); Chart or Table toggle | Each measure in the form that fits it |
| Chart not drawn | Text | C32 | Shows what is missing and why |
| Sources under charts | Source text | C22 | Rule 4 |

### 6.8 Evidence

Opens on a governance summary, then tabs. A module filter (C26) and search (C36) apply to every
tab. Dense tables (C27) are acceptable here.

| Part | Today | Becomes |
|---|---|---|
| Governance summary | Does not exist | Row of C30 gauges and C3 tiles: modules delivered, source files read, calculations recorded, open gaps by severity (C29), methods changed since the run, run duration. Counts of listed items only |
| Trace | Per-paragraph chips inside module pages | Tab: statement, module, source file, pages, excerpt, hash match. The drawer (C22) is a single row of this tab |
| Sources | Table: name, type, date, read by (a long list of module names) | Tab: file cards with type icon, C28 reader stack, hash with C35; "Supplied, not used" as a count |
| Calculations | Per-module tables | Tab: C27 with expanding rows (formula, inputs, result, unit) and "used by" links back to the statement |
| Gaps | Per-module tables and ledgers | Tab: grouped by severity (C29), effect and required source; Changes ledger here |
| Registers | Appendix tables in each module | Tab: the tables as written, by module, minus inter-module columns and registers |
| Run record | Hashes, instructions sent, retries and cost (one long table of model calls) | Tab: C13 steps per module with start and accepted times; instructions and hashes with C35; model calls collapsed to a per-module total row that expands |
| Handoffs | Download list | Tab footer: original Markdown per module and "Download all" |

### 6.9 Run activity

| Part | Today | Becomes | Why |
|---|---|---|---|
| Activity list | Text; empty state "could not be read" | C13 across the modules with C31 state marks; the running module shows a loader and elapsed time; C23 on completion or failure | Run status is live state: the one place for animation |
| Empty or unreadable | Sentence | C32 with what to do next | A blank page reads as broken |

### 6.10 Mapped only

| Screen | Recommended form | Note |
|---|---|---|
| Run start form | Four C13 steps (files, pathway, modules, summary); drop zone; summary card showing the USD 20 cap; Submit stays the analyst's explicit action | Not changed in this work |
| HTML Model internals | Unchanged | Reused as built |

## 7. The trace link

On a findings page: a 16 px icon at the end of a paragraph, row or figure, labelled for screen
readers. It opens a drawer: the statement, then calculation (formula, inputs, result), then
source file, pages and excerpt, then "Open in Evidence". At 1600 px and wider the drawer can
stay open beside the page. In print, traces are omitted and Evidence prints separately.

## 8. Motion

| Where | What | Limit |
|---|---|---|
| Run activity, library home | Loader on the running module; step change | Only while a run is live |
| Navigation | Pill slide | 300 ms, once |
| Drawer, tile expand, toggle thumb | Slide or expand | 200 to 300 ms, once |
| Charts | Draw-in | Once on first view |
| Report pages | Nothing loops | Off under reduced motion and in print |

## 9. Follow-up: module-instruction changes (not in this work; needs a paid run)

These would let the page show more without parsing prose.

| Wanted | Why |
|---|---|
| A structured verdict line (action bias, direction) | The Overview could show "Watchlist" as a badge; today it sits inside a sentence |
| Confidence as a field (score, grade) | Today it is a sentence in a status paragraph |
| "Would improve" and "would worsen" as two lists | The callout could be two-sided |
| Units and periods as columns, not inside cells | Cleaner charts without reading "USD 4,173 million" as text |
| A category on each limitation | The gap signal could group by kind |

## 10. Open readings and not verified

Open readings for the owner:

- Rule 7: drawn nowhere (my reading), or drawn in Evidence only.
- Decision 1 was not answered directly; redraw without library code is my default.
- Findings pages may draw a visual from a register where it presents an outcome (event risk
  matrix, watch list), with the register itself in Evidence. This follows "the handoff is used
  like a database".
- Counts of listed items (modules delivered, open gaps) are shown; no financial figure is
  computed.

Not verified:

- The reference sites were read through a summarising fetch and then confirmed live for the
  Flowbite, React Bits and Uiverse pages only. Class lists and sizes are as the fetch reported.
- shadcnblocks is under a commercial licence, most Preline blocks are Pro, and React Bits is
  MIT with a Commons Clause. Nothing is copied; anatomy is redrawn. Licences were read from the
  sites' own pages, not from legal texts.
- The shape rules were derived from one run. Other pathways and the modules changed in other
  sessions may produce shapes not listed; those fall to the designed data card.
- AGENTS.md says source references live in Basis lines and Source columns. That describes what
  modules write; this map changes only where the library draws them. AGENTS.md needed a matching
  line when the build landed: done (see `AGENTS.md`).
- No reader check or fidelity check had been run when this map was written; both were run at build time (done, scope and results in `VERIFICATION.md`, entry 2026-11-13, branch `claude/report-redesign-evidence`).

## 11. What was built

Built as plain JavaScript and CSS in `apps/issuer-library/credit_os/web/` (no library code, no build
step). The mapped tables above are unchanged. The shape classifier is `shapes.js`; each shape is drawn
by `components.js`. Components in use and where the build differs from the map:

| Screen | Components in use | Differences from the map as drawn |
|---|---|---|
| Library home | Search with filter chips and counts, Cards or List toggle, issuer cards | The Leverage basis filter was removed. Excluded run folders are listed under "Not shown". |
| Report history | Run timeline with state mark, date, pathway | A run is named by period and pathway. |
| Overview | Verdict panel, findings feed, measure tiles, sided board, left-rule callout, dated timeline, module tiles | The chart index and the "Evidence and audit" link lists were removed, as mapped. An earlier-format Overview lists no dates. |
| Changes | Before and after cards, module state tiles, empty state for a first run | The differences the build computes are listed in Evidence, not on Changes. The ledger is on the Evidence Gaps tab. |
| Modules | Verdict panel, findings feed, status checklist, question accordion, fact list, record cards, risk matrix, watch list, dated timeline, pathway map, statement bars with a Bars or Figures toggle, empty and gap states | Component choice follows the shape of the data in `shapes.js`, checked against the key `apps/issuer-library/fixtures/shape-key.json`. |
| Forecast | Chart cards with trace controls, empty states | The trace controls work on Forecast (a whole-branch review found them dead and they were fixed). |
| Evidence | Governance summary, then tabs: Summary, Trace, Sources, Calculations, Gaps, Registers, Run record; trace drawer | Registers draw the tables as written, minus inter-module columns. Run codes and hashes are drawn here only. |
| Run activity | Run steps and marks | The steps are labelled and connected. Motion is only for live run state, inside the reduced-motion query. |

Open readings the owner has not ruled on, and checks not made, are in the `VERIFICATION.md` entry
for 2026-11-13. Rule 7 was built as "drawn nowhere": text written for another module is not drawn in
search or the drawer either.
