# Modules not yet installed, and what each is for

Date: 2026-11-13. Survey only: no code changed, no model or provider called. Read against `origin/main`
at `d941eef`. Predecessor folders were read, not changed. `~/Documents/OP Router.rtf` was not read.

## Bottom line

One module that every run depends on, Financial foundation (CP-1), still runs on a stand-in instead of
the older full method. Three older modules were never brought into this project at all: sector review,
issuer monitoring and email intake. Eight were retired or replaced on purpose and are not missing. The
other 19 analytical modules are installed and are sent their full method. Seven modules that the June
Credit Operating System ran on their own, and the ESG module added after it, run here only as a part of
another module, with no launch and no page of their own (see the crosswalk and the ESG section below).

"Installed" here means two things the code shows: CP-OS can order and launch the module (it has an entry
in the routing table `_SELECTED`, `src/deploy_workflow/owners/cpos_launch.py:154-273`, and sits in at
least one pathway preset, `src/deploy_vii/contracts.py:53-78`), and the text it is sent is the full
older method, not a short stand-in.

| Status | Count | Modules |
|---|---:|---|
| (a) Installed on the full method | 19 | CP-0, CP-1A, CP-1B, CP-1C, CP-1D, CP-2, CP-2A, CP-2D, CP-2E, CP-2G, CP-2H, CP-3, CP-3C, CP-3D, CP-4, CP-4C, CP-5, CP-6, CP-DR |
| (b) Launchable, but on a short stand-in | 1 | CP-1 |
| (c) In an older package, not listed or launchable here | 3 | Sector review (CP-SR), Issuer monitoring (CP-MON), Email intake (CP-EMAIL) |
| (d) Retired or replaced on purpose | 8 | CP-MEMO, the old CP-8 post-mortem, the CP-MODEL workbook, the Lite screens (CP-L10 to CP-L40), CP-PARSE, and the Credit Operating System's report renderer (CP-RENDER), appendix parser (CP-EXTRACT) and data store (CP-DB) |

PR 93 (the Deploy V method corrections) is merged, and it carried PR 83's change with it (PR 83 itself
was closed, not merged). So nothing in this file is waiting on an open pull request. The only open one,
PR 98, changes the issuer library's pages, not the modules.

## Modules not fully installed

Size: small = method text and a routing line; medium = also new inputs or a page change; large = other
parts of the workflow read its output and must be re-proved.

| Code | Plain name | Status | What it is for | Who would use the result | Where its method is | What installing it needs | Size |
|---|---|---|---|---|---|---|---|
| CP-1 | Financial foundation | (b) stand-in | Answers "what are the issuer's reported numbers, on a consistent basis?" The full method adds what the short text lacks: a fixed set of credit metrics, a register of every normalisation, a register of conflicting definitions (for example two versions of EBITDA), debt on balance-sheet carrying value, the reporting perimeter, lease and interest classification, debt rate terms, and a trend table across periods | Every later module; the Forecast page, the charts, the Overview figures and the Changes page read its tables | `caos-databricks/vendor/deploy-v/skills/cp-1-canonical-data-foundation` at `dfff264` (the corrected "r14" text; skill 23 KB, steps 43 KB). Deploy V `c4d2e35` holds the earlier version (20 KB and 36 KB). Today's text is 26 KB: `prompts/CP-1.md` (2.5 KB) plus five step texts (24 KB) written for the earlier runtime that returned JSON (`cpos_launch.py:163`, `:291`, `:2128-2129`) | Method text; keep this project's period, chart and post-balance-sheet tables; adapt the net debt check; an owner decision on debt basis (the method says carrying value governs, this project's net debt table asks for gross principal); its own paid test run | Large |
| CP-SR | Sector review | (c) not listed | Answers "what is happening in this sector, and what does it mean for credits in it?": sector drivers, a comparison table across issuers, early-warning thresholds. Not about one issuer | Would give Fundamental credit, Peer benchmark and Downside their sector context; no library page shows a sector today | `~/Documents/Modular OS/CP-SR/` (June 2026, version 1.0). Deploy V folded it into Research questions: its skill says it "Replaces CP-SR" and keeps a standalone sector study (`Deploy V/skills/cp-dr-deep-research/SKILL.md:128-131`) | A way to start a run with no issuer (today Research questions requires Source readiness and Financial foundation first, `src/deploy_vii/methodology.json:107-112`); a sector entry in the library; web search, which is granted only on some model routes | Medium |
| CP-MON | Issuer monitoring ("CreditPulse") | (c) not listed | Answers "what has happened to this issuer since we last looked?": collects news, rating actions, filings and market moves, scores each for importance, and routes alerts to the module it affects | Would feed Earnings changes, Downside, Security selection, Legal & covenants and the Committee; the nearest thing here is the Changes page, which compares two runs and does not watch for news | `~/Documents/Modular OS/CP-MON/` (June 2026, version 1.0). Not in Deploy V or any later package | Method text; a routing entry and a library page; a live news and market-data feed and a schedule, neither of which this workflow has | Large |
| CP-EMAIL | Email intake | (c) not listed | Rules for using emails (broker notes, management updates, agent notices) as evidence: which module may use which kind of email, how much weight it carries, and when it goes stale | Would let Source readiness accept emails as sources for every module | `~/Documents/Modular OS/CP-MON/REF_CP-EMAIL_SourceRoutingMatrix.md` (June 2026, version 2.0); a July test is in `~/Documents/Co-Pilot Agents/assessment_cpemail_20260722/`. Not in Deploy V | A way to supply emails as run files; the rules added to Source readiness. It is a set of source rules, not a module with its own output | Medium |
| CP-MEMO | Credit research report (Word) | (d) retired | Merged every module's output into one Word report | Replaced by the issuer library, which shows each run directly | Deploy V `skills/cp-memo-credit-research-report` | Nothing. Owner ruling: `AGENTS.md` ("CP-MEMO is replaced by the actual deliverables"); CP-OS refuses it if selected (`src/deploy_workflow/owners/cpos.py:396-399`) | — |
| CP-8 (old) | Decision ledger and post-mortem | (d) replaced | Recorded each investment decision and later compared it with what happened, to calibrate the process. Needed three past decisions | Replaced by "Changes since the last run", which is installed (`cpos_launch.py:261-262`) and fills the Changes page | Deploy V `skills/cp-8-decision-ledger-post-mortem` (called CP-7 in June) | Nothing. Owner ruling: `AGENTS.md`; `METHODOLOGY-REVIEW.md:771-789` | — |
| CP-MODEL (workbook) | Excel model export | (d) retired | Built an Excel workbook of the credit model | Replaced by the HTML Model, charts and calculation file, which are built by code, not by a model call (`cpos_launch.py:119`) | Deploy V `skills/cp-model` | Nothing. Owner ruling: Excel is an input format only (`AGENTS.md`; `METHODOLOGY-REVIEW.md:532-536`) | — |
| CP-L10, L20, L23, L30, L40 | Lite screens | (d) replaced | Five quick screens: financial change, fundamental credit, liquidity sensitivity, market and recovery opportunity, legal capacity | Replaced by the Lite credit assessment pathway (Source readiness, Financial foundation, Business & governance, Fundamental credit, Downside; `contracts.py:78`). The one-page short snapshot (CP-L10's current text) stays wired but switched off (`contracts.py:74`, `:84`) | Deploy V `skills/cp-l10-financial-change-screen`; a copy is archived in `docs/reuse/selected-methods/skills/cp-l10-financial-change-screen/` and is not sent | Nothing, unless a quick liquidity, market or legal screen is wanted: the Lite pathway does not cover those three topics. Owner rulings: `METHODOLOGY-REVIEW.md:791-811` | — |
| CP-RENDER | Report renderer | (d) replaced | Produced three committee documents: full committee report, IC summary, portfolio summary | Replaced by the issuer library pages. The library has no separate IC summary or portfolio summary | `Credit Operating System/Modular OS/README/MODULES_REFERENCE_v2.md:70` | Nothing by ruling (`AGENTS.md`: the separately delivered report is retired) | — |
| CP-EXTRACT, CP-DB | Appendix parser and data store | (d) replaced | Read each module's Word output into a database | Replaced by Markdown handoffs and the run folder | `MODULES_REFERENCE_v2.md:69`, `:71` | Nothing | — |
| CP-PARSE | Document preparation | (d) replaced | Sorted a document pack by evidence value, handled scans and awkward tables, and packaged the result before analysis | Replaced by the launcher, which lists, converts and pins the files itself; Source readiness is told this has been done (`cpos_launch.py:1793-1806`) | Deploy V `skills/cp-0-source-readiness/references/REF_CP-PARSE_STEPS.md`; archived here, not sent (`cpos_launch.py:155-158`) | Nothing by ruling. One thing lost: no scoring of which documents matter most, and no step for scanned pages. Not verified how the launcher treats a scanned PDF | — |

Not counted above because no method was ever written for them, only a name and one paragraph
(`~/Documents/Co-Pilot Agents/_PROPOSED/PROPOSED_MODULES.md:38-41`): portfolio risk aggregation
(book-level concentration and limits) and an implied rating and default-probability scorecard.

## Is the full Financial foundation method more robust than the current one?

Yes as an analytical method; no as a checked output; the strongest version is the full method with this
project's checks kept. Not proven by any run.

| | Current (26 KB) | Full method (caos-databricks `dfff264`, 67 KB) |
|---|---|---|
| Written for | Mostly the earlier JSON runtime: "Every `amount` is a JSON number", "the schema or the validator enforces each one" (`src/deploy_vii/live/prompts.py:766` onward). This transport is Markdown, so the model must work out which rules still apply. This is the same fault PR 93 removed from Source readiness and Refinancing & LME | Markdown handoffs, 13 ordered steps |
| Metrics | Whatever the run's tables ask for; no fixed list | A fixed set (leverage, coverage, cash flow, liquidity, margin, growth), each with formula, both operands and their sources, period, and one of eight calculation statuses (`REF_CP-1_STEPS.md:170-195`) |
| Definitions | No register | A definition-conflict register that must either log each conflict (EBITDA, debt, free cash flow, capex, net debt) or state that there is none (`:198-222`) |
| Adjustments | Reported versus calculated kept apart; an expense reconciliation | A normalisation register, a constructed-period register (for example last twelve months) and a pro forma adjustment register |
| Debt | Gross principal in the net debt table (`cpos_launch.py:674-693`) | Balance-sheet carrying value governs; leases kept apart from financial debt; rate and amortisation terms per facility |
| Reasoning | Prose may not contain a figure (a rule of the JSON runtime) | Every conclusion as evidence, then mechanism, then creditor consequence; the strongest contrary evidence; disagreements reconciled or kept as gaps |
| Checked by code | Yes: net debt must equal gross debt less cash to the unit, cash must match the liquidity table, periods must be in one form, chart tables, post-balance-sheet adjustments (`cpos_launch.py:674-725`) | No: it relies on helper scripts (credit metrics, completeness check) that this project does not run, and its last step feeds the retired Excel workbook |

So the full method asks the right questions and the current one has the better guard rails. Installing
it means: send the full text, drop its workbook step, keep this project's tables and checks, and settle
the debt basis. The June Credit Operating System version of this module (13 step files) is the ancestor
of the same text; Deploy V added the workbook step and caos-databricks the lease, interest and
debt-term corrections.

## Why eight installed modules have no run on their current texts

They have been run, but not since their texts were corrected on 13 November.

- All of them ran live on 9 and 10 November in the two all-module TransDigm runs. On 10 November 18 of 19
  modules were accepted. Earnings changes ran; Earnings quality was Restricted; Peer benchmark, Ratings &
  triggers, Market-implied risk and Recovery & fulcrum were Blocked, each for a missing source only (no
  peers, no rating reports, no market data, no legal documents) (`VERIFICATION.md:908-921`).
- PR 93 changed the method text of 20 of 22 modules on 13 November. Every paid run since then has been a
  Full credit assessment (`docs/rulings/2026-11-13-tdg-full-copilot-sol-rerun.md`,
  `-high.md`; `runs/tdg-copilot-sol-medium-vs-high.md`). That preset has 13 modules and does not include
  these eight (`src/deploy_vii/contracts.py:53-56`). They sit in the Earnings update, Relative value,
  Covenant & refinancing and Distressed presets (`:57-69`), none of which has been run since.
- The test pack is the second reason. The TransDigm runs use five filings, so four of the eight would
  again return "no source" whatever the method says. The 99-document TransDigm pack from 4 November
  (`~/Documents/cp-os/runs/TDG-20261104-full5/`) has the credit agreement, peers and bond prices they need.

One all-module run on the 99-document pack would exercise all eight on their current texts. It is a paid
run and needs your instruction and a cap; the 10 November run cost USD 10.32 on five filings.

## Crosswalk to the Credit Operating System (June 2026)

`~/Documents/Credit Operating System/` holds `Modular OS/` (24 modules, 3 infrastructure parts and one
cross-module reference; `README/MODULES_REFERENCE_v2.md`) and `caos/` (an application that runs the same
24 as agents; `caos/backend/agents/`, `caos/backend/governance/module_registry.json`). Its codes are not
this project's codes: seven letters moved when Deploy V regrouped the modules. Matched by the step-file
names, which carry over one for one.

| Credit Operating System | What it is for | Here | Status here |
|---|---|---|---|
| CP-0 Source readiness | Are the documents good enough to start? | CP-0 | (a) |
| CP-X Planner and router | Which modules run, in what order | CP-OS | Installed as the orchestrator |
| CP-1 Canonical data foundation | Reported numbers on one basis | CP-1 | (b) stand-in |
| CP-1A Business and transaction fact pack | What the company does and what the deal is | CP-1A | (a) |
| CP-1B Earnings delta | What moved since last period | CP-1B | (a) |
| CP-1C Peer benchmark | How it compares with peers | CP-1C | (a) |
| CP-2 Fundamental credit synthesizer | The credit view | CP-2 | (a) |
| CP-2B Downside pathway | What breaks first and how far it falls | CP-2A | (a) |
| CP-2C Event and catalyst register | Dated events that could move the credit | Part of CP-2A (`cpos_launch.py:193`) | Inside a parent |
| CP-2D Governance and sponsor score | Will owners and management act for or against creditors? | Part of CP-1A (`:169`) | Inside a parent |
| CP-2E Liquidity and cash-flow bridge | Is there enough cash, and for how long? | CP-2D | (a) |
| CP-2F Macro, FX and hedging | Exposure to rates, currencies and input costs | CP-2E | (a) |
| CP-3 Relative value and security selection | Is the instrument cheap or dear? | CP-3 | (a) |
| CP-3B Recovery and instrument preference | Recovery by instrument; which one to own | Part of CP-3 (`:219-220`) | Inside a parent |
| CP-3C Portfolio fit and position sizing | How much to hold, within limits | Part of CP-3 (`:221-222`) | Inside a parent; no portfolio input supplied |
| CP-3D Refinancing and LME risk | Can it refinance; is a liability exercise likely? | CP-3C | (a) |
| CP-4 Legal and covenant interpreter | What the documents permit | CP-4 | (a) |
| CP-4C Covenant capacity calculator | Headroom under each test and basket | Part of CP-4 (`:241-242`) | Inside a parent |
| CP-5B Evidence trace validator | Does every claim trace to a source? | CP-5 | (a) |
| CP-5 Research integrity QA | Audit of the whole run across eight lanes | Part of CP-5 (`:254`) | Inside a parent |
| CP-6A IC debate | Bull and bear case, action bias | CP-6 | (a) |
| CP-6E Portfolio debate | Final portfolio posture and sizing | Part of CP-6 (`:259`) | Inside a parent; no portfolio input supplied |
| CP-SR Sector review | Sector-level credit review | None | (c) |
| CP-MON CreditPulse | Continuous issuer monitoring and alerts | None | (c) |
| REF_CP-EMAIL | Rules for using emails as evidence | None | (c) |
| CP-RENDER | Committee report, IC summary, portfolio summary | Issuer library | (d) |
| CP-EXTRACT, CP-DB | Parse module output into a database | Markdown handoffs, run folder | (d) |

"Inside a parent" follows Deploy V's own catalogue, which says of each: "Alternate command for the
complete owner workflow; no separate artifact"
(`Deploy V/skills/cp-os-credit-os/references/CREDIT_OS_V_MODULE_CATALOG_v2.json`, `superseded_module_ids`).
The step text is sent in full, but the part cannot be launched alone, has no pathway entry and no page
of its own, and its output is whatever the parent chooses to write in one handoff. If you want any of the
seven back as its own module, each is small: a routing entry, a library name and a preset line, since
the method text is already here. The library already names three sub-parts of Legal & covenants this way
(`src/deploy_workflow/credit_os_chips.py:73-75`) without their being launchable.

Modules this project has that the Credit Operating System did not: Earnings quality (CP-1D), Forward
credit model (CP-2G), Ratings & triggers (CP-2H), Market-implied risk (CP-3D), Recovery & fulcrum (CP-4C),
Research questions (CP-DR), Changes since the last run (CP-8).

## The ESG module

There was one, and its method is still sent, but nothing in this project shows it by name.

| When | Where | Form |
|---|---|---|
| May to early June 2026 | `~/Documents/prompts`, `Agent Files`, `Modular OS`, `Credit Operating System` | No ESG module. The only mention is one row of the sector review's criteria (`Modular OS/CP-SR/REF_CP-SR_B_InvestigationCriteria.md:39`) |
| 22 June 2026 | `~/Documents/Co-Pilot Agents/_PROPOSED/PROPOSED_MODULES.md` | Proposed and promoted as its own module, then coded CP-2G, "ESGSustainabilityCreditRisk", because ESG had been covered "only at sector level" and sustainability-linked margin ratchets were not modelled |
| July to August 2026 | `Co-Pilot Agents/DEPLOY_A_ONEDRIVE_AGENTS/CP-2F`, `DEPLOY_B_COWORK_SKILLS/skills/cp-2f-esg-sustainability-credit-risk`, `DEPLOY_C_GENERATED_SKILLS/skills/cp-2f-…` | Its own module, coded CP-2F, nine steps |
| September 2026, Deploy V `c4d2e35` | `Deploy V/skills/cp-2e-macro-fx-hedging-sensitivity/SKILL.md:311` | Folded into Rates, FX & hedging: "Absorbed phase — CP-2F, binding on every CP-2E run" |
| This project | `docs/reuse/selected-methods/skills/cp-2e-macro-fx-hedging-sensitivity/` | The same: the nine-step file is byte-identical to Deploy V's and is sent with CP-2E (`cpos_launch.py:203-207`) |

What it is for: it answers "which environmental, social and transition factors actually reach this
credit, and through what channel?" Its nine steps are a disclosure inventory, environmental and
transition exposure, social and operational exposure, a materiality classification, sustainability-linked
debt mechanics (targets and margin step-ups), the link to refinancing access and cost of capital, a credit
synthesis, gaps and an overall implication. It is not an ESG score: most factors are to be marked
immaterial.

Status: inside a parent, like the seven above, and less visible than any of them. The words "ESG" and
"sustainability" appear nowhere in this project's launcher, catalogue or library pages; the reader sees
only "Rates, FX & hedging" (`src/deploy_workflow/credit_os_chips.py:70`). Making it its own module is
small (routing entry, name, preset line). Not verified: whether any run's Rates, FX & hedging handoff
actually contains the ESG tables; the run folders were not available to this session.

## Installed, but one part cannot work yet

These are status (a). The method is sent in full, but something the method relies on is not supplied, so
part of the output will be a stated gap.

| Module | What is missing | Rests on |
|---|---|---|
| Security selection (CP-3), portfolio fit part | The method reads a portfolio workbook (holdings, limits). None is supplied; the archive deliberately leaves out the sample workbooks | `METHODOLOGY-REVIEW.md:699-702` |
| Committee decision (CP-6), portfolio debate part | The same portfolio workbook; a Portfolio Decision run without it is flagged as a gap before launch | `src/deploy_workflow/run_expectations.py:585-598` |
| Research questions (CP-DR) | Web search is offered only when a ruling grants it and the model route supports it; otherwise it reads the run's own files and most questions come back unresolved | `src/deploy_workflow/model/handoff.py:103-110`; `docs/rulings/2026-11-13-tdg-full-copilot-sol-rerun.md` ("Web search is not offered on this route") |
| Peer benchmark (CP-1C) | It cannot find peers itself; it needs a peer list in the run context or Research questions in the same run | `run_expectations.py:420-436` |
| Security selection (CP-3), Market-implied risk (CP-3D) | No market quotes unless the analyst supplies them | `run_expectations.py:473-503` |
| Ratings & triggers (CP-2H) | No ratings unless entered or supplied as a file | `run_expectations.py:461-472` |
| Downside (CP-2A) | Sent the full method plus a short project text that sets how stress sizes are chosen; where they differ the short text governs | `cpos_launch.py:190-198`; `METHODOLOGY-REVIEW.md:703-705` |
| All 19 | The calculations the older methods hand to scripts (credit metrics, liquidity bridge, rate and currency sensitivity, bond yield and spread, covenant headroom, recovery waterfall, funding gap, peer statistics) are done by the model with a calculator, and the older completeness check is not run. Only the confidence score is computed by code | `cpos_launch.py:142`; `METHODOLOGY-REVIEW.md:699` |

Sub-modules the library names separately are part of their parent and are sent with it: covenant
capacity, structural priority and intercreditor control inside Legal & covenants (`cpos_launch.py:237-245`;
names at `src/deploy_workflow/credit_os_chips.py:73-75`); instrument preference and portfolio fit inside
Security selection (`:216-224`); events and catalysts inside Downside (`:190-193`); governance and sponsor
inside Business & governance (`:166-170`); sustainability risk inside Rates, FX & hedging (`:203-207`);
debt-like obligations inside Earnings quality (`:181`); portfolio debate inside Committee decision
(`:256-260`). None is missing.

## Recommended order

1. **Financial foundation (CP-1) on the full method.** It is the only stand-in left and every other
   module reads it, so its gaps (no definition-conflict register, no normalisation register, debt basis)
   limit all 19 installed modules. It is also the riskiest change, because the Forecast, charts and
   Changes page read its tables; it needs its own test run and the debt-basis decision first.
2. **A portfolio input for Security selection and the Committee.** Not a new module, but it is the
   cheapest way to make two installed modules do work they are already instructed to do: position size
   and portfolio fit. Needs a place to supply the holdings and limits file.
3. **Sector review, as a standalone mode of Research questions.** The method text is already in the
   repo (the version 2.0 research skill); what is missing is a run that starts without an issuer and a
   place to show it. It gives Fundamental credit and Peer benchmark the sector context the 13 November
   review found thin.

Leave for later: issuer monitoring (needs live feeds and a schedule this workflow does not have) and
email intake (needs a way to supply emails; small once that exists).

## Not verified

- No model was run. "Installed on the full method" means the instruction that would be sent contains the
  full text; it says nothing about output quality.
- The crosswalk was matched on step-file names and counts, not by comparing the step texts line by line;
  whether a part inside a parent is as deep as its June standalone version was not checked.
- In `Credit Operating System/caos/` I read the agent folder names, the module registry and the headings
  of `docs/CAOS_Master_Blueprint.md`, not the agent code. The repository has no commit, so no revision
  can be cited for it.
- The comparison of the two Financial foundation methods is of instruction texts only; no output of the
  full method in this project exists.
- The older packages were read by folder listing and by the opening of each module's main file, not
  line by line: `~/Documents/Modular OS`, `Agent Files`, `prompts`, `Co-Pilot Agents`. A module that
  exists only inside another file there could have been missed.
- The May prompt for a multi-year trend history (`~/Documents/prompts/M1D …`) appears to have been folded
  into Financial foundation's trend table in Deploy V; I checked that the table exists, not that it
  covers everything the May prompt asked.
- Not read: `Deploy V Development`, `Deploy VI`, `DEPLOY VII`, `Deploy Workflow`, `deploy workflow
  Codex`, `caos-v2` and the other `caos-*` folders (except the one CP-1 path cited), `final-workflow`
  and its siblings. `METHODOLOGY-REVIEW.md:430-442` records that those hold the same module list.
- `docs/reviews/2026-11-13-older-methodologies.md` is not on `main`; I read the uncommitted copy in the
  worktree `pause-63d136`, with its companion `2026-11-13-deploy-v-implementation.md`.
- The "AI Assurance Auditor" that one deployment summary mentions was not found on disk.
