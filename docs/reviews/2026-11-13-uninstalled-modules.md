# Modules not yet installed, and what each is for

Date: 2026-11-13. Survey only: no code changed, no model or provider called. Read against `origin/main`
at `d941eef`. Predecessor folders were read, not changed. `~/Documents/OP Router.rtf` was not read.

## Bottom line

One module that every run depends on, Financial foundation (CP-1), still runs on a short project-written
instruction instead of the older full method. Three older modules were never brought into this project
at all: sector review, issuer monitoring and email intake. Five were retired or replaced on purpose and
are not missing. The other 19 analytical modules are installed and are sent their full method.

"Installed" here means two things the code shows: CP-OS can order and launch the module (it has an entry
in the routing table `_SELECTED`, `src/deploy_workflow/owners/cpos_launch.py:154-273`, and sits in at
least one pathway preset, `src/deploy_vii/contracts.py:53-78`), and the text it is sent is the full
older method, not a short stand-in.

| Status | Count | Modules |
|---|---:|---|
| (a) Installed on the full method | 19 | CP-0, CP-1A, CP-1B, CP-1C, CP-1D, CP-2, CP-2A, CP-2D, CP-2E, CP-2G, CP-2H, CP-3, CP-3C, CP-3D, CP-4, CP-4C, CP-5, CP-6, CP-DR |
| (b) Launchable, but on a short stand-in | 1 | CP-1 |
| (c) In an older package, not listed or launchable here | 3 | Sector review (CP-SR), Issuer monitoring (CP-MON), Email intake (CP-EMAIL) |
| (d) Retired or replaced on purpose | 5 | CP-MEMO, the old CP-8 post-mortem, the CP-MODEL workbook, the Lite screens (CP-L10 to CP-L40), CP-PARSE |

PR 93 (the Deploy V method corrections) is merged, and it carried PR 83's change with it (PR 83 itself
was closed, not merged). So nothing in this file is waiting on an open pull request. The only open one,
PR 98, changes the issuer library's pages, not the modules.

## Modules not fully installed

Size: small = method text and a routing line; medium = also new inputs or a page change; large = other
parts of the workflow read its output and must be re-proved.

| Code | Plain name | Status | What it is for | Who would use the result | Where its method is | What installing it needs | Size |
|---|---|---|---|---|---|---|---|
| CP-1 | Financial foundation | (b) stand-in | Answers "what are the issuer's reported numbers, on a consistent basis?" The full method adds what the short text lacks: a fixed set of credit metrics, a register of every normalisation, a register of conflicting definitions (for example two versions of EBITDA), debt on balance-sheet carrying value, the reporting perimeter, lease and interest classification, debt rate terms, and a trend table across periods | Every later module; the Forecast page, the charts, the Overview figures and the Changes page read its tables | `caos-databricks/vendor/deploy-v/skills/cp-1-canonical-data-foundation` at `dfff264` (the corrected "r14" text; skill 23 KB, steps 43 KB). Deploy V `c4d2e35` holds the earlier version (20 KB and 36 KB). Today's text is `prompts/CP-1.md`, 2.5 KB | Method text; keep this project's period, chart and post-balance-sheet tables; adapt the net debt check; an owner decision on debt basis (the method says carrying value governs, this project's net debt table asks for gross principal); its own paid test run | Large |
| CP-SR | Sector review | (c) not listed | Answers "what is happening in this sector, and what does it mean for credits in it?": sector drivers, a comparison table across issuers, early-warning thresholds. Not about one issuer | Would give Fundamental credit, Peer benchmark and Downside their sector context; no library page shows a sector today | `~/Documents/Modular OS/CP-SR/` (June 2026, version 1.0). Deploy V folded it into Research questions: its skill says it "Replaces CP-SR" and keeps a standalone sector study (`Deploy V/skills/cp-dr-deep-research/SKILL.md:128-131`) | A way to start a run with no issuer (today Research questions requires Source readiness and Financial foundation first, `src/deploy_vii/methodology.json:107-112`); a sector entry in the library; web search, which is granted only on some model routes | Medium |
| CP-MON | Issuer monitoring ("CreditPulse") | (c) not listed | Answers "what has happened to this issuer since we last looked?": collects news, rating actions, filings and market moves, scores each for importance, and routes alerts to the module it affects | Would feed Earnings changes, Downside, Security selection, Legal & covenants and the Committee; the nearest thing here is the Changes page, which compares two runs and does not watch for news | `~/Documents/Modular OS/CP-MON/` (June 2026, version 1.0). Not in Deploy V or any later package | Method text; a routing entry and a library page; a live news and market-data feed and a schedule, neither of which this workflow has | Large |
| CP-EMAIL | Email intake | (c) not listed | Rules for using emails (broker notes, management updates, agent notices) as evidence: which module may use which kind of email, how much weight it carries, and when it goes stale | Would let Source readiness accept emails as sources for every module | `~/Documents/Modular OS/CP-MON/REF_CP-EMAIL_SourceRoutingMatrix.md` (June 2026, version 2.0); a July test is in `~/Documents/Co-Pilot Agents/assessment_cpemail_20260722/`. Not in Deploy V | A way to supply emails as run files; the rules added to Source readiness. It is a set of source rules, not a module with its own output | Medium |
| CP-MEMO | Credit research report (Word) | (d) retired | Merged every module's output into one Word report | Replaced by the issuer library, which shows each run directly | Deploy V `skills/cp-memo-credit-research-report` | Nothing. Owner ruling: `AGENTS.md` ("CP-MEMO is replaced by the actual deliverables"); CP-OS refuses it if selected (`src/deploy_workflow/owners/cpos.py:396-399`) | — |
| CP-8 (old) | Decision ledger and post-mortem | (d) replaced | Recorded each investment decision and later compared it with what happened, to calibrate the process. Needed three past decisions | Replaced by "Changes since the last run", which is installed (`cpos_launch.py:261-262`) and fills the Changes page | Deploy V `skills/cp-8-decision-ledger-post-mortem` (called CP-7 in June) | Nothing. Owner ruling: `AGENTS.md`; `METHODOLOGY-REVIEW.md:771-789` | — |
| CP-MODEL (workbook) | Excel model export | (d) retired | Built an Excel workbook of the credit model | Replaced by the HTML Model, charts and calculation file, which are built by code, not by a model call (`cpos_launch.py:119`) | Deploy V `skills/cp-model` | Nothing. Owner ruling: Excel is an input format only (`AGENTS.md`; `METHODOLOGY-REVIEW.md:532-536`) | — |
| CP-L10, L20, L23, L30, L40 | Lite screens | (d) replaced | Five quick screens: financial change, fundamental credit, liquidity sensitivity, market and recovery opportunity, legal capacity | Replaced by the Lite credit assessment pathway (Source readiness, Financial foundation, Business & governance, Fundamental credit, Downside; `contracts.py:78`). The one-page short snapshot (CP-L10's current text) stays wired but switched off (`contracts.py:74`, `:84`) | Deploy V `skills/cp-l10-financial-change-screen`; a copy is archived in `docs/reuse/selected-methods/skills/cp-l10-financial-change-screen/` and is not sent | Nothing, unless a quick liquidity, market or legal screen is wanted: the Lite pathway does not cover those three topics. Owner rulings: `METHODOLOGY-REVIEW.md:791-811` | — |
| CP-PARSE | Document preparation | (d) replaced | Sorted a document pack by evidence value, handled scans and awkward tables, and packaged the result before analysis | Replaced by the launcher, which lists, converts and pins the files itself; Source readiness is told this has been done (`cpos_launch.py:1793-1806`) | Deploy V `skills/cp-0-source-readiness/references/REF_CP-PARSE_STEPS.md`; archived here, not sent (`cpos_launch.py:155-158`) | Nothing by ruling. One thing lost: no scoring of which documents matter most, and no step for scanned pages. Not verified how the launcher treats a scanned PDF | — |

Not counted above because no method was ever written for them, only a name and one paragraph
(`~/Documents/Co-Pilot Agents/_PROPOSED/PROPOSED_MODULES.md:38-41`): portfolio risk aggregation
(book-level concentration and limits) and an implied rating and default-probability scorecard.

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
- Since PR 93, only the 13 modules of the Full credit assessment have been run on the corrected texts
  (`runs/tdg-copilot-sol-medium-vs-high.md`). Earnings changes, Peer benchmark, Earnings quality,
  Liquidity, Ratings & triggers, Refinancing & LME, Market-implied risk and Recovery & fulcrum have not.
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
