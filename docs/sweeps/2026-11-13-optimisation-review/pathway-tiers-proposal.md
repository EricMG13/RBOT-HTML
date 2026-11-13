# Lite, Full and Deep credit assessments: proposal for the owner, 2026-11-13

Proposal only. No code, test, run folder or method text was changed, and no model was called.
Module codes are given once, in the table in section 3; tables after it use the codes.

## 1. Bottom line and the questions that are yours

- Three tiers are workable on the pathways that exist: Lite (5 modules, unchanged), Full (the core
  modules) and Deep (all 20 analytical modules, a source-starved one skipped with a stated limitation).
- Deep cannot run safely on GitHub Copilot today. Its largest first prompts would be about 300,000 to
  310,000 tokens against a 272,000 limit. It fits (about 143,000) once upstream handoffs are sent
  without their appendix, which you have already decided. Build Deep after that change, not before.
- Deep costs an estimated USD 10 to 14 a run and takes about 100 minutes in order, 79 two at a time.
  Its run order is a chain 15 modules long, so running more than two at once gains four minutes.
- Full should stay as it is until one Deep run shows the other modules working on their current
  texts; then I recommend adding three (Earnings changes, Earnings quality, Liquidity).

Decided today and built on here, not reopened. "Deep is all runnable models": Deep is every runnable
module, each skipped only when its sources are too thin; Full is the core modules without the
specialists far from their lead; Lite is as now. Also: Lite's id and five modules; Full keeps its id;
the short snapshot stays wired and off; handoffs go downstream without their appendix, readable on
demand; Financial foundation gets a code gate, the full Deploy V method and carrying-value debt;
Research questions gets an online lookup; upstream defects are caught at handoff only.

| # | Question | Recommended answer |
| --- | --- | --- |
| 1 | Where is Full's line? (section 3) | Option C: one step from the lead and filings are enough. It adds three modules to today's Full. Switch it on only after a Deep run shows the three accepted; today's Full until then |
| 2 | When a Deep module's sources are missing: skip it, or run it and let it block? (section 4) | Skip before launch, shown on the summary you approve; the page keeps the section with a stated limitation. A module that starts and finds less than declared still writes a Blocked handoff, as now |
| 3 | Which missing sources skip a module? | Only the four rules that exist: no peers, no ratings, no quotes, legal documents declared "none". No new rule until a run shows the need |
| 4 | Does Full get the same skip? | Not yet. Deep only, until you have read how a skipped module looks |
| 5 | Deep's identity and first comparison (section 7) | A new pathway id. A first Deep run of an issuer says "first run of this pathway"; it is not compared with a Full run |
| 6 | The five purpose pathways (Earnings Update, Relative Value, Covenant & Refinancing, Distressed & Restructuring, Portfolio Decision) | Keep all five as they are until Deep has one accepted, reader-checked run; rule on switching any off after that. Earnings Update stays in any case |
| 7 | What Deep's front page shows | Full's twelve sections, the two downside sections Lite already has, and one lead section for each further module: about 24, not all 56 |
| 8 | Cap and effort for Deep | USD 25 at medium or balanced (the run-start rule says USD 20 per run and would need amending for Deep); high only on request, at USD 30 |
| 9 | Concurrency | Two at a time for Full and Deep once the six conditions in section 5 are built and tested; never three; Lite in order |
| 10 | The eight sub-parts inside a parent (section 8) | Keep all eight inside their parents |
| 11 | Paid proof (section 9) | Two Deep runs after the appendix change lands: one on a rich pack, one on a filings-only pack, cap USD 25 each, and a reader check of the first |

## 2. Today

Eight pathway ids exist (`src/deploy_vii/contracts.py:36-45`, presets `:52-79`; titles and report
sections `src/deploy_vii/report_view.py:506-641`). "Calls" counts modules that call the model; the
cash flow model (CP-MODEL) is in five presets and makes no call. Changes since the last run (CP-8) is
not counted: it is added last when an earlier run of the same issuer and pathway is listed
(`cpos_launch.py`, `_prepare`). The measured Full runs had 13 calling modules: these 12 and CP-8.

| Pathway (id) | Calls | Modules, in the order the registry gives (`registry.py:137-165`) | Status |
| --- | ---: | --- | --- |
| Full credit assessment (`credit_snapshot`) | 12 | CP-0, CP-1, CP-1A, CP-DR, CP-4, CP-2, CP-2A, CP-2E, CP-2G, CP-3, CP-5, CP-6 | Run twice on current texts, 13 November |
| Lite credit assessment (`lite_credit_assessment`) | 5 | CP-0, CP-1, CP-1A, CP-2, CP-2A | Built; no real run |
| Earnings Update (`earnings_update`) | 7 | CP-0, CP-1, CP-1B, CP-DR, CP-2E, CP-1D, CP-5 | Offered |
| Relative Value (`relative_value`) | 12 | CP-0, CP-1, CP-1A, CP-3D, CP-DR, CP-1C, CP-2, CP-2E, CP-2D, CP-3C, CP-3, CP-5 | Offered |
| Covenant & Refinancing (`covenant_refinancing`) | 12 | CP-0, CP-1, CP-1A, CP-DR, CP-4, CP-2, CP-2A, CP-2E, CP-2D, CP-2G, CP-3C, CP-5 | Offered |
| Distressed & Restructuring (`distressed_restructuring`) | 13 | CP-0, CP-1, CP-1A, CP-DR, CP-4, CP-1C, CP-2, CP-2A, CP-2E, CP-2G, CP-2H, CP-4C, CP-5 | Offered |
| Portfolio Decision (`portfolio_decision`) | 9 | CP-0, CP-1, CP-1A, CP-DR, CP-2, CP-2E, CP-3, CP-5, CP-6 | Offered |
| Short credit snapshot (`short_snapshot`) | 3 | CP-0, CP-1, CP-L10 | Wired, deactivated (`contracts.py:84`) |

Eight modules are in neither Full nor Lite: Earnings changes, Peer benchmark, Earnings quality,
Liquidity, Ratings & triggers, Refinancing & LME, Market-implied risk, Recovery & fulcrum. They sit
only in the four purpose pathways (`contracts.py:57-69`). The last run I can confirm for them is the
all-module run of 10 November, on the older method texts (`VERIFICATION.md:908-921`).

One gap found while reading: Lite's page has the downside stress and break-point sections
(`report_view.py:538-539`); Full's has neither (`:511-524`), although Full runs the same module. Full
is not a superset of Lite on the page. Question 7 closes this for Deep.

## 3. The three tiers

Definition, so the line can be redrawn by rule and not by taste:

- The core chain is Source readiness, Financial foundation, Business & governance, Fundamental credit
  and Security selection, with Legal & covenants as the lead of the legal family. Evidence validation,
  Committee decision and Changes close every run that has them; they read whatever ran.
- A specialist's lead is the numbered module of its family (CP-2H's lead is CP-2).
- Its distance is one plus the number of other specialists whose handoffs it cannot start without
  (required inputs in `src/deploy_vii/methodology.json`). Distance 1: it can start as soon as the core
  has run. Distance 3: two other specialists must be accepted first.
- It needs a scarce source when a pre-launch rule (`src/deploy_workflow/run_expectations.py:366-599`)
  marks it empty without a document a filings-only pack lacks.
- A specialist that needs a scarce source is far from its lead. Whether distance 2 is also far, or
  only distance 3, is the choice between options B and C below.

| Module | Lead | Distance | Needs beyond the filings | Lite | Full today | Full, option C | Deep |
| --- | --- | ---: | --- | :-: | :-: | :-: | :-: |
| Source readiness (CP-0) | core | - | - | yes | yes | yes | yes |
| Financial foundation (CP-1) | core | - | - | yes | yes | yes | yes |
| Cash flow model (CP-MODEL), no model call | CP-1 | - | - | no | yes | yes | yes |
| Business & governance (CP-1A) | core | - | - | yes | yes | yes | yes |
| Earnings changes (CP-1B) | CP-1 | 1 | A prior period in the filings; no rule | no | no | add | yes |
| Peer benchmark (CP-1C) | CP-1 | 1 | A peer list, or research that can look peers up (`:421`) | no | no | no | skip if none |
| Earnings quality (CP-1D) | CP-1 | 1 | The management EBITDA bridge; no rule | no | no | add | yes |
| Research questions (CP-DR) | CP-1 | 1 | Online lookup (being built) | no | yes | yes | yes |
| Fundamental credit (CP-2) | core | - | - | yes | yes | yes | yes |
| Downside (CP-2A) | CP-2 | 1 | - | yes | yes | yes | yes |
| Liquidity (CP-2D) | CP-2 | 1 | None (US dollar limit only, `:449`) | no | no | add | yes |
| Rates, FX & hedging (CP-2E) | CP-2 | 1 | - | no | yes | yes | yes |
| Forward credit model (CP-2G) | CP-2 | 2 | - | no | yes | yes, by exception | yes |
| Ratings & triggers (CP-2H) | CP-2 | 3 | Ratings (`:462`) | no | no | no | skip if none |
| Security selection (CP-3) | core | - | Quotes; without them its view reads "Unclear" (`:484`) | no | yes | yes | yes |
| Refinancing & LME (CP-3C) | CP-3 | 2 | - (waits for Liquidity) | no | no | no | yes |
| Market-implied risk (CP-3D) | CP-3 | 1 | Quotes (`:494`) | no | no | no | skip if none |
| Legal & covenants (CP-4) | core | - | Executed legal documents (`:505`) | no | yes | yes | skip if none |
| Recovery & fulcrum (CP-4C) | CP-4 | 3 | Executed legal documents, through CP-4 | no | no | no | skip with CP-4 |
| Evidence validation (CP-5) | closes | - | - | no | yes | yes | yes |
| Committee decision (CP-6) | closes | - | - | no | yes | yes | yes |
| Changes since the last run (CP-8) | closes | - | An earlier run of the same pathway | auto | auto | auto | auto |

Lite is the core chain less Security selection, plus Downside. Deep is every row. Full is where the
line could move:

| Option | Rule | Calling modules, with CP-8 | For | Against |
| --- | --- | --- | --- | --- |
| A | Today's list | 13 | The only tier with runs on current texts; nothing to rebuild | Not your rule: it leaves out three specialists that are one step from their lead and need only filings, and keeps one at two steps |
| B | Distance up to 2, no scarce source | 17 (adds CP-1B, CP-1D, CP-2D, CP-3C) | A clean rule with no exception | On a filings-only pack Deep skips the other four, so Deep and Full become nearly the same run |
| C | Distance 1, no scarce source; the forecast module stays because the Forecast page is a completion page (`AGENTS.md:53`) | 16 (adds CP-1B, CP-1D, CP-2D) | Applies "far from its lead" literally; the three added are already read, when present, by modules Full runs (CP-2, CP-2A, CP-2G, CP-3, CP-4: their `optional` lists in `methodology.json`) | One stated exception; three modules unproven on current texts join the default run |

Recommendation: C, in two steps. Full stays at A until one Deep run has shown Earnings changes,
Earnings quality and Liquidity accepted on their current texts; then Full moves to C with its own paid
run and reader check. Any enlargement of Full needs the appendix change first (section 6).

## 4. "Source availability is too low to run it"

What happens today: nothing is skipped. A module without its sources runs, pays for its first prompt
and writes a handoff that says Blocked. Legal & covenants did this in both 13 November runs at USD
0.37 each (`runs/tdg-copilot-sol-medium-vs-high.md:46`, `:71`). On 10 November the four specialists
blocked for a missing source cost USD 2.18 between them (that run's call log; older texts).

| Module | Existing rule (`run_expectations.py`) | Today | Deep, proposed |
| --- | --- | --- | --- |
| CP-1C | Peer source "none", or public peers without Research questions (`:421-436`): gap | Runs, blocks | Skip. Once Research questions can look peers up and is in the run, the rule no longer fires and it runs |
| CP-2H | No ratings entered and no ratings file (`:462-472`): gap | Runs, blocks | Skip |
| CP-3D | No quotes entered and no quotes file (`:494-503`): gap | Runs, blocks | Skip |
| CP-4 | Legal documents declared "none" (`:505-515`): will refuse | Runs, blocks; the page offers "run without" | Skip |
| CP-4C | None of its own; it requires CP-4 (`methodology.json`, CP-4C `required`) | Blocks with CP-4 | Skip whenever CP-4 is skipped |
| CP-3 | No quotes and no price talk (`:484-492`): gap | Runs; relative value "Unclear" | Run. It is core; the gap is stated in its own section |
| CP-2D | Reporting currency not US dollars (`:449-460`): limited | Runs with the limit | Run with the limit |
| CP-1B, CP-1D, CP-3C, CP-2G, CP-2E, CP-DR | No source rule | Run | Run. On 10 November CP-1B ran and CP-1D was Restricted on five filings |
| CP-3, CP-6 portfolio parts | The portfolio-file rule fires only in Portfolio Decision (`:586-598`) | Stated gap inside the parent | Unchanged |

Where the decision lives: before launch, from the rules above, which CP-OS already evaluates on your
declarations and the recognised files and shows on the summary (`cpos_launch.py`, `_prepare` calls
`expectations`). You see each skip and accept it before any spend. I do not recommend a second skip
from Source readiness's handoff yet: its findings are prose tables no code reads, and deciding on
them would make the run order depend on model output. If Source readiness finds less than declared,
the module runs and blocks as today. That matches "catch at handoff only, for now".

What the reader sees: the section the skipped module would have filled stays on the page with one
sentence, for example "Ratings & triggers was not run: no ratings were supplied. Add ratings in
Context or a ratings file." The Modules page lists it as not run with the same reason. Today a section
with no owner is dropped and named only in the scope note (`cpos_launch.py`, `_layout`, "Sections not
produced"); that is not enough for a reader who has not read the sources.

How it is recorded, so Changes does not read it as a change of view:

- The run's manifest lists each skipped module with the rule that skipped it. The run is still
  recorded as the pathway's own module set. This matters: a run recorded as an explicit subset is
  never used as a comparison base (`src/deploy_workflow/changes.py:186-188`).
- The comparison pack carries both runs' skip lists. Changes then states "not run in either run", or
  "run this time: ratings now supplied" with the cause New source, or "not run this time: quotes no
  longer supplied". Without this, its method would call the module New or Not run this time with the
  cause Method change (`src/deploy_vii/methods/cp8.md:169-177`), which is wrong here.

## 5. Run order and concurrency

Layers: modules on one line can start together once the lines above are accepted. An input a module
"may read" becomes a wait whenever that input is in the run (`registry.py:78-83`).

| Layer | Lite | Full today | Full, option C | Deep |
| ---: | --- | --- | --- | --- |
| 1 | CP-0 | CP-0 | CP-0 | CP-0 |
| 2 | CP-1, CP-1A | CP-1, CP-1A | CP-1, CP-1A | CP-1, CP-1A |
| 3 | CP-2 | CP-DR, CP-4 | CP-1B, CP-DR | CP-1B, CP-DR |
| 4 | CP-2A | CP-2 | CP-1D | CP-1C, CP-1D |
| 5 | (CP-8) | CP-2A, CP-2E | CP-2, CP-4 | CP-2, CP-4 |
| 6 | | CP-2G | CP-2A, CP-2E, CP-2D | CP-2A, CP-2E, CP-2D |
| 7 | | CP-3 | CP-2G | CP-2G |
| 8 | | CP-5 | CP-3 | CP-2H |
| 9 | | CP-6 | CP-5 | CP-3D |
| 10 | | (CP-8) | CP-6 | CP-3C |
| 11 | | | (CP-8) | CP-4C |
| 12 to 15 | | | | CP-3, CP-5, CP-6, (CP-8) |

Critical paths at the measured durations. Lite: CP-0, CP-1A, CP-2, CP-2A. Full today: CP-0, CP-1,
CP-DR, CP-2, CP-2A, CP-2G, CP-3, CP-5, CP-6, CP-8, with CP-1A, CP-4 and CP-2E off it. Option C: CP-0,
CP-1, CP-1B, CP-1D, CP-2, CP-2A, CP-2G, CP-3, CP-5, CP-6, CP-8.

Deep's critical path is CP-0, CP-1, CP-1B, CP-1D, CP-2, CP-2A, CP-2G, CP-2H, CP-3D, CP-3C, CP-4C,
CP-3, CP-5, CP-6, CP-8: 15 of 21. Only six modules sit off it (CP-1A, CP-DR, CP-1C, CP-4, CP-2E,
CP-2D), worth 24 minutes at medium; that is the most any concurrency can save. The chain is long
because each late specialist may read the one before it: Market-implied risk needs only quotes but
waits for Ratings & triggers, which waits for the forecast. Shortening it means a module no longer
reading a handoff it reads today. That is a method change and is not proposed.

Wall-clock, minutes, medium / high effort, with CP-8:

| Tier | In order | Two at a time | A layer at a time | Basis |
| --- | ---: | ---: | ---: | --- |
| Lite | 27 / 43 | 23 / 36 | 23 / 36 | Estimate: the five modules' durations in the Full runs |
| Full today | 62.5 / 85.9 | 49.7 / 69.9 | 49.7 / 69.9 | Measured in order (`REPORT.md:24`); the rest is a replay of those durations |
| Full, option C | 79 / 108 | 63 / 86 | 59 / 82 | 13 measured, 3 estimated |
| Deep, all run | 100 / 137 | 79 / 108 | 76 / 104 | 13 measured, 8 estimated |
| Deep, four skipped | 81 / 112 | 63 / 86 | 59 / 82 | 13 measured, 4 estimated |

Estimated durations: CP-1B 374 s, CP-1D 344 s, CP-2D 247 s and CP-3C 168 s from the 10 November run
(older texts, another route); 271 s, the mean of the ten measured analyst modules, for the four that
were blocked that day; high is medium times 1.37. Two at a time assumes the Copilot account serves two
calls without queueing, which is not established (`REPORT.md:94`, `:135`).

The cap. Every call reserves USD 7.17 before it is sent, and a call is refused when spend plus
reservations would pass the cap (`src/deploy_workflow/model/budget.py:16`). So a run in order needs
its total cost plus 7.17; two at a time needs the spend at the last moment two modules overlap plus
14.34; three needs that plus 21.51. Costs are from section 6: today's supply for Lite and Full
today, after the appendix change for option C and Deep.

| Tier | In order needs (medium / balanced / high) | Two at a time needs | Caps |
| --- | --- | --- | --- |
| Lite | 9.9 / 10.4 / 10.9 with CP-8; 9.5 / 9.9 / 10.3 on a first run, without it | 14.8 | USD 10 holds a first lite run at medium and is at the edge at balanced; it never holds two reservations. USD 20 holds everything |
| Full today | 15.8 / 16.7 / 18.5 (measured costs) | 18.3 (`findings.json`, orchestration-2) | USD 20 holds; USD 25 gives room for one failed attempt |
| Full, option C | 15.4 / 16.2 / 17.8, plus on-demand reads | about 20.2 | USD 20 in order; USD 25 for two at a time at high |
| Deep | 17.5 / 18.5 / 20.5, plus 0.5 to 1.5 of on-demand reads | about 20.8 | USD 20 is not enough. USD 25 holds at medium and balanced, two at a time. Three at once needs about USD 28 for four minutes: no |

When the cap cannot hold two reservations the proposed scheduler runs in order; it does not stop the run.

What must not run together, and why:

- Evidence validation reads every analyst module, so it starts alone after all of them. Committee
  decision requires it. Changes reads every handoff and is last (`registry.py:84-89`).
- Nothing that reads Financial foundation starts before its new code gate passes. Business &
  governance reads only Source readiness, so it may run beside Financial foundation.
- A handoff is accepted in run order even if its module finishes early, because one prose check reads
  every earlier accepted handoff. That is the first of the review's six conditions (`REPORT.md:94`);
  the others are the cap holding two reservations, resume, event writes, a session home per module
  and an adapter proven on two overlapping calls.

## 6. Cost and context

USD per run on GitHub Copilot gpt-6.1-sol, with CP-8. "Today" is today's supply of whole handoffs;
"after" is handoffs sent without their appendix, before the cost of reading registers on demand
(unmeasured; the review assumed USD 0.5 to 0.9 for Full).

| Tier | Medium: today / after | Balanced: today / after | High: today / after | Of which measured |
| --- | --- | --- | --- | --- |
| Lite | 2.7 / 2.4 | 3.2 / 2.8 | 3.7 / 3.2 | None as a lite run; module costs taken from the Full runs |
| Full today | 8.62 / 7.0 | 9.5 / 7.6 | 11.37 / 9.0 | 8.62 and 11.37 measured; balanced is a splice; "after" uses the review's attributed saving |
| Full, option C | 10.6 / 8.3 | 11.7 / 9.0 | 13.9 / 10.7 | 13 modules; 1.1 to 1.5 is estimated |
| Deep, all run | cannot run / 10.3 | cannot run / 11.3 | cannot run / 13.3 | 13 modules; 2.6 to 3.4 is estimated. On today's supply it would be 13.8 / 15.4 / 18.2 |
| Deep, four skipped | 11.2 / 8.7 | 12.5 / 9.5 | 14.8 / 11.1 | 13 modules; 1.3 to 2.1 is estimated |

Basis. Measured: the 13 modules' cost, first-prompt size, calls and handoff sizes in the two retained
runs (`runs/tdg-copilot-sol-medium-vs-high.md:42-55`), which I recomputed from their call logs to the
same totals. Estimated: each of the eight unrun modules is priced as its first prompt at USD 2.50 a
million tokens, ten re-reads at 0.10 and its output at 10 (`REPORT.md:27`); its first prompt is its
method text (30,000 to 60,000 characters, measured in this tree) plus the handoffs it is sent; its
handoff is assumed to be the mean of the ten measured analyst handoffs (56,000 characters, 23,000
without the appendix). That gives USD 0.33 to 0.56 each at medium; on 10 November they cost 0.35 to
0.66. Each of the 13 also pays to carry the added handoffs. Treat the estimated part as right to
within about a third. Balanced figures understate, as the review notes (`REPORT.md:84-86`).

Financial foundation on the full method (decided today): the longer instruction adds about USD 0.04
a run. If its handoff grows, every 10,000 added characters cost about USD 0.09 in Full and 0.15 in
Deep, because 10 and 17 modules read it. Neither is in the table. Both are estimates.

Largest first prompt, thousand tokens, medium / high. Copilot starts summarising at about 218,000 of
272,000 (`REPORT.md:36`); CP-OS warns when a first prompt plus the 32,000 output budget passes that
(`near_limit` in `src/deploy_workflow/model/copilot.py`), which is a first prompt of about 186,000.

| Tier | Today | After the appendix change |
| --- | --- | --- |
| Lite | CP-8 94 / 116 | CP-2A 55 / 57 |
| Full today | CP-8 193 / 241 (measured 192,798 and 240,816); CP-5 183 / 225; CP-6 181 / 213 | CP-5 96 / 105 |
| Full, option C | CP-8 237 / 296; CP-5 227 / 280; CP-6 210 / 250 | CP-5 114 / 125 |
| Deep, all run | CP-8 310 / 389; CP-5 300 / 372; CP-6 254 / 305; CP-3 233 / 280 | CP-5 143 / 157; CP-3 130 / 140; CP-8 130 / 145 |

- Deep cannot run until the appendix change lands: two of its first prompts exceed the limit itself
  at medium effort and four at high.
- Option C cannot run safely before it either: three first prompts start above the warning line at
  medium.
- After the change Deep fits with room at medium. A module's context grew by 29,000 to 50,000 tokens
  between its first prompt and its peak in the measured runs, so Deep at high effort would peak at
  about 186,000 to 207,000 in Evidence validation, close to the threshold. Hence medium or balanced
  for Deep.

## 7. Pathway ids, titles and history

| Tier | Id | Effect on earlier runs |
| --- | --- | --- |
| Lite | `lite_credit_assessment`, unchanged | None |
| Full | `credit_snapshot`, unchanged | Earlier runs stay comparison bases: matching is on issuer, pathway id and "the pathway's own modules" (`changes.py:233-241`, `:186-195`). If option C is adopted, the first comparison lists the three added modules as New, cause Method change, which is true |
| Deep | New id, for example `deep_credit_assessment`; title "Deep credit assessment" | No earlier run exists, so the first Deep run of an issuer has no comparison |

Should a first Deep run compare with the issuer's last Full run? I recommend no. The standing rule is
same issuer and same pathway (`AGENTS.md:38`); comparing a 21-module run with a 13-module one would
fill the Changes page with modules that are new only because the tier differs.

The five purpose pathways. Three choices: keep them offered; fold them into Deep and stop offering
them; or keep them wired and switch them off, as was done for the short snapshot. I recommend keeping
them offered for now. Each has a front page built for its question (8 to 15 sections),
and those are the only pages that show the specialist sections until Deep's page is built and read.
Earnings Update is a third of Deep's size and answers a different question, so it stays whatever is
decided for the other four.

Run-start page: add Deep with what it needs ("filings; legal documents, quotes, ratings and peers
where you have them: modules without their sources are skipped and said so"); regenerate the three
tables the page keeps in step with the code (`context-form.html:732-758`); show each skip on the
summary and the tier's cap in place of the fixed "USD 20 cap" sentence (`:659`). Issuer library:
Overview with Deep's sections; Modules with a "not run: reason" state; Changes reading the skip lists.

Deep's report sections. All pathways together define 56 sections; Full shows 12. Three choices: Full's
12 only (the specialists' work is then visible only on the Modules page); all 56 (a long, repetitive
page, and every section is also an instruction to its module, so prompts and output grow); or Full's
12, the two downside sections, and one lead section per further module: results against the prior
period (CP-1B), peer positioning (CP-1C), earnings quality (CP-1D), liquidity runway (CP-2D), forward
credit path (CP-2G), rating triggers (CP-2H), refinancing paths (CP-3C), market against fundamentals
(CP-3D), covenant tests and headroom (CP-4), recovery by class (CP-4C). I recommend the third, about
24. The section list is a presentation decision and needs the reader check.

## 8. The eight sub-parts that run only inside a parent

Each is a step file sent with its parent's method (`cpos_launch.py`, `_SELECTED`). I checked that all
eight leave traces in the 13 November handoffs; I did not judge their depth.

| Sub-part | Parent | Step file | Note |
| --- | --- | --- | --- |
| Governance and sponsor | CP-1A | REF_CP-2C, 27 KB | |
| Events and catalysts | CP-2A | REF_CP-2B, 7 KB | Its table caused 6 of 18 rejected drafts (`REPORT.md:52-55`) |
| Instrument preference | CP-3 | REF_CP-3A, 22 KB | |
| Portfolio fit and sizing | CP-3 | REF_CP-3B, 22 KB | No portfolio file is supplied, so it can only state a gap |
| Covenant capacity | CP-4 | REF_CP-4A, 29 KB | Idle whenever CP-4 is blocked or skipped |
| Research integrity review | CP-5 | REF_CP-5A, 32 KB | |
| Portfolio debate | CP-6 | REF_CP-6A, 38 KB | No portfolio file is supplied |
| ESG and sustainability | CP-2E | REF_CP-2F, 13 KB | Its tables are in both runs' CP-2E handoffs; no page names it |

The question: keep each inside its parent, or launch it as its own module in Deep? Recommendation:
keep all eight inside. A split would buy a page, an effort level and a skip rule of its own. It would
cost a first prompt each (an estimated USD 0.3 to 0.5, so USD 3 to 4 for all eight), one more handoff
for Evidence validation and Changes to carry, and a longer chain where it is already 15. The parents
already write these parts. If one is to be split first, the two portfolio parts are the candidates,
because they are the ones a skip rule would help; that depends on a portfolio file being supplied,
which is a separate decision.

## 9. What it would take

Build, in order:

1. Land the appendix-on-demand supply (already decided). Deep and any larger Full depend on it.
2. Add the Deep pathway: id, title, question, its 20 modules plus the cash flow model, its sections,
   and a prompt-size ceiling like the other pathways'.
3. Mark the four source rules as skipping in Deep; remove a skipped module and whatever requires it
   before the order is planned; record each skip and its reason in the manifest while keeping the run
   recorded as the pathway's own module set.
4. Keep a skipped module's section on the page with its stated limitation; show "not run: reason" on
   the Modules page.
5. Give the comparison pack both runs' skip lists; add the rule to the Changes method and its check.
6. Set the cap by tier (Deep USD 25) and amend the run-start ruling accordingly.
7. Update the run-start page: the new pathway, regenerated tables, skips on the summary.
8. Offline proof: a synthetic Deep run to a verified delivery with all sections placed; the same with
   four modules skipped; a pair of synthetic runs showing Changes reports a skip as a source change.
9. Separately, and not required for Deep: the two-at-a-time scheduler with its six conditions.
10. Only after a Deep run: move Full to option C, with its own run.

To be proven by paid runs before acceptance:

- Deep on a rich pack, medium effort, cap USD 25: all twenty modules accepted on current texts; no
  module written after a summarised context; the largest first prompt recorded against the estimate
  here; cost and duration against section 5 and 6.
- Deep on a filings-only pack: the four skips shown before launch, stated on the page, not charged;
  a second run of the same issuer showing how Changes words them.
- The reader check `AGENTS.md` requires for a presentation change: the first Deep run read against the
  September VMO2 reference and recorded in `VERIFICATION.md` with its scope.
- If two at a time is built: one paid run with the time to first byte recorded.

Risks:

- Eight modules have no run on their current texts. The two Full runs had nine rejected drafts each
  and both stopped once at Evidence validation; a first Deep run should be expected to stop.
- A stopped module cannot be resumed and accepted handoffs cannot be reused in a new run
  (`runs/tdg-copilot-sol-medium-vs-high.md:105-106`). With 21 modules a stop late in the chain loses
  more. This limit matters more for Deep than for any other tier.
- Evidence validation is already a quarter of a Full run's cost; in Deep it reads 18 handoffs.
- The carrying-value debt decision changes the table the comparison pack reads for net debt. The first
  comparison after it will show a definition change, not a change at the issuer.
- A front page with twice the sections can read flat and repetitive; the reader check decides.
- The cost and time figures for the eight are estimates from an older run and from averages.

## 10. Not verified

Estimated, not measured:

- Every cost, duration and prompt size for the eight unrun modules, Lite, option C and Deep; the
  "after" columns; on-demand register reads; the effect of the full Financial foundation method. The
  projection was computed in this session from the two retained runs' call logs and the registry and
  is not saved as a script, because this task allowed one file.
- The Lite cap arithmetic: no lite run exists. USD 10 as the lite cap rests on your words in
  `docs/rulings/2026-11-13-tdg-full-copilot-sol-rerun.md:10`; the service default is USD 20.
- Whether Copilot serves two calls at once without queueing; run-to-run variation.
- `cpos_launch.py` is cited by function name, not line: another session is editing that file.

From the sibling survey, checked:

- Confirmed: Full's preset has 13 entries and omits the eight modules, which sit only in the four
  purpose pathways; the three older modules (sector review, issuer monitoring, email rules) have no
  entry in the registry; the eight sub-parts are bundled with the parents named.
- Confirmed with corrections: the 10 November all-module run stopped at Evidence validation on
  request size, but on the OpenAI route's 1,050,000-token bound under a counting rule since fixed, not
  on Copilot's limit. Its ruling lists twenty modules where `VERIFICATION.md:914` says nineteen, and
  its call log shows six Evidence validation calls costing USD 0.85 where the record says it stopped
  "before any call".
- Not confirmed: that the eight have had no run since their texts changed (I checked the presets and
  the two 13 November rulings, not every run folder); that 20 of 22 method texts changed on 13
  November; that the 99-document TransDigm pack holds the credit agreement, peers and bond prices; the
  size and content of the full Financial foundation method; Deploy V's catalogue wording on sub-parts.
