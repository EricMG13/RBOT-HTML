# Analysis depth as a launcher setting: proposal for the owner, 2026-11-13

Proposal only. No code, test, run folder or method text was changed, and no model was called.
"Tier" means Lite, Full or Deep (which modules run). "Effort" means the model's reasoning level.
"Depth" is what this paper is about: how far each module that runs takes its analysis.

## 1. Bottom line

- Yes, it can be a launcher setting, and part of it exists already. Two method texts carry their own
  depth switch: Committee decision (CP-6) has a Deep Debate mode, which the launcher can already turn
  on, and Fundamental credit (CP-2) has a Deep Synthesis mode, which nothing can turn on today.
- I recommend one run-wide setting with three values: **Brief**, **Standard** and **Extended**.
  Standard is today's behaviour, byte for byte. CP-OS turns the value into a short scope block per
  module, held in one file beside the register scope file; the method texts are not edited.
- Depth is the smaller lever. Estimated for a Full run at medium effort: Brief saves about 9 to 12
  minutes of 62.5 and USD 0.5 to 0.7 of 8.62; Extended adds about 6 to 16 minutes and USD 0.5 to 1.5.
  The tier is the large lever (Lite is an estimated 27 minutes). None of this is measured.
- Build Extended first. The methods define it, it removes nothing, and it cannot lower quality.
  Brief needs a ruling on what may be left out and a paid comparison before any saving is claimed.
- A fixed set is never reduced at any depth: Financial foundation (CP-1) whole, the four reader
  passages, every table a page, a code check or a later module reads, sources and gaps.
- What a Brief run left out is stated by CP-OS from the run record, on the summary you approve, in the
  run id and on the Overview and Modules pages. Modules are not asked to say it: CP-OS refuses a
  limitation that an earlier handoff already states, so twelve identical sentences would be rejected.

## 2. What depth can mean inside one module

Where each lever lives today, and whether a setting already reaches it.

| Lever | Where it lives today | Already a setting? |
| --- | --- | --- |
| Long-form or compact writing | Method text: CP-2 "Deep Synthesis Mode", default compact, 1 to 5 pages (`REF_CP-2_STEPS.md:317-320`); CP-6 "Deep Debate Mode" (`cp-6…/SKILL.md:242-243`); page budgets in CP-2A and CP-4B | CP-6 yes: `module_options.cp6_deep_debate` in the context file sends `DEEP_DEBATE_BLOCK` (`cpos_launch.py:2206`, `:2606`). CP-2 no |
| Registers and optional sections written | Method text, the canon's Analytical appendix section, and CP-OS blocks that already remove some (`CP0_BLOCK`, `cpos_launch.py:1841`) | Being built as a fixed cut per module (`CPOS_REGISTER_SCOPE.md`, in flight). Not depth-dependent |
| Sub-parts bundled in a parent (governance in CP-1A, events in CP-2A, ESG in CP-2E, instrument and portfolio parts in CP-3, 4A/4B in CP-4, integrity review in CP-5, portfolio debate in CP-6) | The file list per module, `_SELECTED` (`cpos_launch.py:157-276`) | No. Every file is always sent |
| Scenarios | Context file: 1 to 4 downside scenarios (`context.py:61`, `:717`); `STRESS_BLOCK` requires at least one paired scenario (`cpos_launch.py:1827`); value-allocation tables 1 to 3, the second and third optional (`:1078`, `_allocation`) | Partly: the analyst sets the count in the context |
| Periods | CP-1's method; the Forecast page shows at most 12 quarters and 8 years (`cpos_periods.py:462`) | No, and it should not be: see section 3 |
| Peers, quotes, ratings | What the analyst supplies: at most 30 peers, 40 quotes, 20 ratings (`context.py:60`); CP-1C needs 3 comparables | By supply only |
| Mode of Security selection | Method's four execution modes | Yes: `module_options.cp3_mode` (`cpos_launch.py:2202`). It changes scope, not depth |
| Source reading (pages, searches, calls) | Code limits: 8 pages a read, 20 hits a search, 3 writes (`handoff.py:83-85`); `--max-turns`, default 32, also on the run-start page's Advanced level; reads stop at a context size (`handoff.py:98`); CP-DR's web search, 16 calls a response (`:103`) | `--max-turns` only, and it is a safety stop: a module that runs out of turns is lost, not shortened |
| Number of findings, challenges, questions | Method text: CP-5 traces the "Top 5 material credit drivers" (step 02); CP-6's claims, attacks and rounds; CP-2's three frameworks (steps 05A to 05C); CP-DR's question list | No |
| Output limit | 32,000 tokens a call (`cpos_launch.py:125`) | No. A ceiling, not a depth |

Three things follow.

- The turn limit, the write limit and the output limit must not be used as depth. They cut a module
  off; they do not make it write a shorter, complete answer.
- Effort already moves depth without saying so. High effort wrote 24% more words and 43% more output
  tokens than medium on the same sources and instructions, and took 27 minutes longer. A depth block
  makes explicit what effort now changes by accident.
- The run-start page already uses the word "level" for basic, standard and advanced disclosure
  (`run_start/submissions.py:88`). The setting should be called depth, never level.

## 3. What is never reduced

A depth setting may change only what nothing else reads. This is the protected set, from
`appendix-inventory.md`, the report routes and the code checks.

| Protected | Why |
| --- | --- |
| Financial foundation (CP-1), whole: statements, the period table, chart data, net debt data, post-balance-sheet events | Nine Full modules, the Forecast page, the charts and Changes read it; its acceptance check is being rebuilt in flight. CP-1 has no Brief form |
| Source readiness (CP-0) | The launcher has already cut it (`CP0_BLOCK`); its input gate and content map are read downstream |
| The four reader passages, Basis lines, `## Sources`, `## Gaps`, confidence inputs | Overview, Modules, Evidence and the trace drawer; `prose_checks`; Python computes the score from the inputs |
| Every report selector, chart table and owner table (`OWNER_TABLES`, `cpos_launch.py:822`) | The checker requires each exactly once; the library draws them |
| CP-2A's scenario table (T2DS.1) and its paired scenario; CP-2G's forecast-inputs block | The forecast is computed from them (`_forecast_issues`); the Forecast page is a completion page |
| CP-2's monitoring triggers, definitions and transmission map; CP-1A's transaction, revenue-mix, operating-model and behaviour registers; CP-2E's registers that are the only support for a passage figure | Later modules reuse their numbers or text (inventory classes DOWN, TEXT, FID, CHECK, LIB) |
| Evidence validation (CP-5)'s checks of protected figures; Changes (CP-8) | CP-5 is the run's check on itself; CP-8 is driven by a pack Python builds |

Rule for the build: a Brief scope may name an item only if the inventory finds no consumer for it in
either run and no route, owner table or check names it. A test enforces this, as the register-scope
work does for its own cut ids.

## 4. Per module: what each setting would change

Measured columns are the medium Full run (`live/calls.jsonl`, recomputed to USD 8.62). "Brief" and
"Extended" columns are proposals; their savings are estimates (basis under the table).

| Module | Measured: USD / s / output tokens | Brief would change | Extended would change | Est. Brief saving |
| --- | --- | --- | --- | --- |
| CP-0 | 0.29 / 201 / 14,347 | Nothing | Nothing | 0 |
| CP-1 | 0.42 / 268 / 22,364 | Nothing (protected) | Nothing; the full method is arriving separately | 0 |
| CP-1A | 0.55 / 342 / 25,961 | History timeline and governance dimensions to the items that carry a credit consequence | Full governance narrative | USD 0.04, 50 s |
| CP-DR | 0.28 / 151 / 8,986 | Fewer, ranked research questions; fewer lookups once the online lookup lands | More questions and lookups (each web response holds up to 16 search fees) | USD 0.02, 30 s |
| CP-4 | 0.37 / 67 / 3,434 (blocked) | 4A and 4B files not sent when legal documents are declared "none" (`REPORT.md` item 9) | Nothing | USD 0.05 |
| CP-2 | 0.44 / 269 / 16,673 | The three frameworks reduced to the factors that pass the materiality filter | Deep Synthesis ON: full prose for four sections, all tables kept | USD 0.03, 40 s |
| CP-2A | 0.62 / 381 / 25,187, 63 calculations | The required paired scenario and one more; sensitivity matrix to the drivers ranked first | Up to four scenarios; full sensitivity matrix | USD 0.08, 95 s |
| CP-2E | 0.66 / 350 / 22,162 | Commodity and FX sensitivities only where the source gate finds an exposure; ESG to its materiality screen | Every sensitivity; full ESG registers | USD 0.06, 70 s |
| CP-2G | 0.41 / 300 / 17,924 | Nothing in the inputs block; shorter driver commentary | Driver rationale per year | USD 0.02, 25 s |
| CP-3 | 0.80 / 352 / 23,980 | Portfolio-fit files (3B) not sent when no portfolio file is supplied; instrument notes for the recommended instrument and its nearest alternative | Every instrument | USD 0.08, 75 s |
| CP-5 | 2.26 / 649 / 42,718, 4 rejected drafts | Integrity review (5A) reduced to the checks on protected figures; top five drivers as the method says | Trace beyond the top five | USD 0.09, 105 s |
| CP-6 | 0.73 / 566 / 14,581 | Portfolio debate (6A) not sent when no portfolio file is supplied; compact debate (already the default) | Deep Debate ON (exists today) | USD 0.06, 45 s |
| CP-8 | 0.79 / 166 / 7,165 | Nothing | Nothing | 0 |
| Run | 8.62 / 4,062 / 245,482 | | | About USD 0.5 and 535 s (9 minutes) of model time, before fewer calls |

Basis of the estimates, so they can be redone.

- Where the money went (medium run): first-prompt cache writes USD 4.80, output USD 2.45, cache reads
  USD 1.33. The first is instructions plus upstream handoffs and is being cut separately (appendix on
  demand). Depth acts mainly on output.
- Time: a least-squares fit over the 26 module results of both runs gives about 7.6 seconds per model
  call plus 12.3 seconds per 1,000 output tokens (R² 0.82). Output is priced at USD 10 a million.
- Each Brief figure is an assumed share of that module's output (10% to 30%) times those two rates,
  plus the bundle file's cache write where a file is not sent. The shares are my assumptions, not
  measurements. A further 10 to 20 fewer calls would add 1 to 3 minutes and up to USD 0.2.
- Overlap: the register cut in flight removes output at every depth, and 61% of the appendix
  characters in the medium run had no consumer. Whatever that cut takes, Brief cannot take again, so
  the figures above are the upper part of the range once it lands.
- Extended: CP-2's and CP-6's long forms, four scenarios and wider tracing add an estimated 30,000 to
  80,000 output tokens, and CP-2's longer passages are carried by the five Full modules that read it
  and by Changes. Hence USD 0.5 to 1.5 and 6 to 16 minutes. On the Deep tier at high effort Extended would push
  Evidence validation toward Copilot's summarising threshold (`REPORT.md` defect 1).

What this says about the owner's aim: most of a run's time is in modules whose work other modules
depend on. Brief can trim them; it cannot halve them. To halve a run, change the tier.

## 5. Three designs for the setting

| | A. One run-wide dial | B. A level per module | C. A depth profile per pathway |
| --- | --- | --- | --- |
| What the user sets | Brief, Standard or Extended | A map, like `--high-modules` | Nothing new: each pathway carries its own depths |
| With tiers | Independent: any tier at any depth | Independent | Fused: "Lite" would also mean brief modules |
| With effort | Independent | Independent | Independent |
| Combinations to prove | 3 depths x 3 tiers; only Standard is proven today | Unbounded | One per pathway |
| Comparison between runs | Two runs differ by one named value | Two runs can differ in twelve places | Clean, but a depth change is a pathway change |
| For | One sentence explains a run | Lets an analyst deepen the one module they care about | No new control |
| Against | Cannot deepen one module alone | Cannot be proven or described to a reader; invites tuning | Does not answer the request: the user cannot raise or lower depth |

Recommendation: **A, recorded as a per-module map.** The user chooses one value. CP-OS resolves it to
a depth per module (CP-0, CP-1 and CP-8 always Standard) and writes that map in the run record, so the
checker, Changes and the pages read one structure. A per-module override (design B) then needs no new
record and can be added later if one run shows the need; I would not build it now. The existing
`cp6_deep_debate` option keeps working: Extended sets it, and the option alone still deepens CP-6 only.

How it combines.

- Tier and depth are two separate controls on the run-start page, depth defaulting to Standard on
  every tier. The page shows each combination's proof status (run and reader-checked, or estimate).
- Effort stays as it is. Brief with high effort is allowed but pointless; Extended on Deep at high is
  refused until one run shows its largest prompt (the existing `first_prompt_near_limit` check).
- The cap does not fall with depth: every call still reserves USD 7.17 before it is sent.

How it is recorded.

| Place | What is recorded |
| --- | --- |
| Run record (`workflow.json`) | The chosen depth and the resolved per-module map. Each module's instruction file is already pinned by hash and holds its scope block |
| Run id | Today `issuer-date-pathway-config` (`cpos_launch.py:2525`). Add `-brief` or `-extended`; Standard adds nothing, so existing ids and comparisons are untouched |
| Summary the analyst approves | One depth line, then per module what is left out or added, and the estimate labelled as an estimate |
| Issuer library | Overview: one sentence, for example "Run at Brief depth: 7 of 12 modules wrote a reduced analysis; see Modules." Modules page: per module, what was left out, in plain words. Text comes from the scope file's reader sentence and the run record; delivery adds no analysis |
| Module limitations | Only where an omission changes that module's conclusion, by the existing rule. No blanket depth sentence |

How Changes (CP-8) treats two runs of different depth.

- They stay comparable. A Brief refresh after a Standard run is the main use of Brief; refusing the
  comparison, as is done for an explicit module subset (`changes.py:186-188`), would remove the
  Changes page exactly where it is wanted.
- Protected values exist at every depth, so issuer rows compare as now.
- The comparison pack gains both runs' depth maps and left-out lists. An item one run has and the
  other left out by depth is listed once as "not produced at this depth". It is never a change at the
  issuer, and never `Method change`, which the method would assign today (`cp8.md:169-177`).
- That needs a seventh cause, `Depth setting`, in the method and its check. The alternative, stretching
  `Method change`, would mislead a reader about why the text differs.

## 6. How depth reaches the model, and which checks must know

Reaching the model without contradicting the method texts.

- One file, `docs/reuse/selected-methods/CPOS_DEPTH_SCOPE.md`, with a section per module and depth.
  It is CP-OS's own text, like the register scope file, and is loaded the same way (a `path § section`
  entry). The archived methods stay byte-identical to their recorded revisions.
- The block goes before the method, where `STRESS_BLOCK`, `CP0_BLOCK` and `DEEP_DEBATE_BLOCK` already
  go (`cpos_launch.py:2591-2615`). Standard sends no block, so today's instruction files and their
  test pins do not change.
- Extended uses the method's own trigger words, as CP-6's block does: "The user explicitly asks for a
  deep synthesis. Deep Synthesis Mode is ON." No override is involved.
- Brief is an override and must say so, by id, as `CP0_BLOCK` does: "Analysis depth for this run is
  Brief. Do not write X and Y. Everything else in the method applies in full. This was chosen by the
  user; it is not missing evidence, so do not block and do not report it as a gap."
- Two existing sentences would contradict a Brief block and need a depth-aware form: the header
  "Run the complete selected method below" (`_instructions`, `cpos_launch.py:2263`), and the transport
  rule that a companion file not sent is "unavailable" and must be written up as something that
  "could not be established" (`:1808-1815`). A file left out by depth is a choice, not a gap.

Checks that must become depth-aware. The design aim is that almost none do, because Brief never
removes a protected item.

| Check | Change |
| --- | --- |
| Report selectors, chart and owner tables, forecast inputs, reader passages, sources (`checker`, `cpos_launch.py:2738`) | None. All protected |
| The register presence check the register-scope work is adding | Must read the scope resolved for the run's depth, or a Brief handoff is rejected for omitting what it was told to omit. This is the one real coupling with in-flight work |
| The cut-id test (no cut id named in launcher or checker text) | Extend to the depth scope file: a Brief id must not be protected |
| Duplicate-limitation check (`prose_checks`) | None, provided modules are not told to state the depth |
| Pre-launch expectations and the summary (`expectations`, `_readiness`) | Add the depth lines |
| Comparison pack and `cp8_issues` | Depth maps, left-out lists, the new cause |
| Layout scope note ("Sections not produced", `_layout`) | Add the depth sentence |
| First-prompt size warning | None in code; Extended makes it fire sooner |
| Delivery fidelity check | None: it compares what handoffs hold |

## 7. Risks, proof and build order

| Risk to analytical quality | Guard |
| --- | --- |
| Brief removes something a later module or page needs | The protected set and its test (section 3); offline delivery of a Brief synthetic run with every page populated |
| Writing a register is how the model does the work, so a module told to write less reasons less and its bottom line weakens | Paid comparison on the same sources, scored against a list written before the runs: protected figures identical, each module's call unchanged, errors counted as in `runs/tdg-copilot-sol-medium-vs-high.md` |
| The reader takes a Brief run for a full one | Run id, summary, Overview and Modules statements drawn from the run record |
| Block and method disagree, the model follows either, drafts are rejected (9 per run today, USD 0.02 to 0.19 each) and the saving is spent on repairs | Blocks name exact ids; the presence check reads the same scope; rejections counted in the trial |
| Changes reports depth as a change in the credit | The pack's depth lists and the new cause; an offline Brief-after-Standard pair |
| Evidence validation checks less | CP-5's checks on protected figures are not reduced; only its integrity sub-part is, and only after the comparison shows no missed error |
| The saving is smaller than run-to-run variation, which is unknown | Two runs per setting before any figure is published |
| Extended lengthens handoffs and reaches the summarising threshold | The existing size warning; no Extended on Deep at high until measured |

To be proven by paid runs before any saving is claimed (after the in-flight work lands, since it
changes the baseline):

1. One Standard run on the new tree. It is needed anyway and is the baseline.
2. Two Brief and one more Standard on the same issuer and effort; one Brief and one Standard on a
   second issuer. Report time, cost, rejected drafts and the scored list.
3. One Extended run, read against the Standard run for whether the extra length is extra sourced
   analysis, which is the methods' own condition.
4. A Brief run after a Standard run of the same issuer, to read how Changes words the difference.
5. The reader check `AGENTS.md` requires for a presentation change (the depth statements on Overview
   and Modules), recorded in `VERIFICATION.md` with its scope.

About seven runs, an estimated USD 50 to 65 at medium on Copilot.

Build order, after the register scope, the CP-1 method and gate, `run_script`, the CP-DR lookup and
the appendix-on-demand supply have landed:

1. The setting and its record: `--depth`, the run-start answer, the run record, the run id suffix,
   the summary line. Standard is the default and changes no instruction byte. Offline only.
2. Extended: CP-2's Deep Synthesis block; Extended sets CP-6's existing option. Offline tests, then
   paid run 3. Nothing is removed, so this can ship on its own.
3. The depth scope file with Brief sections for the three modules with the most output and no
   protected overlap (CP-2A, CP-2E, CP-3), the protected-id test, and the presence check reading depth.
4. The depth statements in the library, with the reader check.
5. The comparison pack fields and the new cause, with the offline pair.
6. Paid runs 1, 2 and 4. Only then widen Brief to other modules or show a saving on the page.

## 8. Questions for the owner

| # | Question | Recommended answer |
| --- | --- | --- |
| 1 | One run-wide dial, a level per module, or a profile per pathway? | One dial, recorded as a per-module map. No per-module control until a run shows the need |
| 2 | Names | Brief, Standard, Extended. Not Lite, Full, Deep (the tiers); not low, medium, high (effort); not "level" (the page's disclosure setting) |
| 3 | May Brief leave out analysis no later module, page or check reads? | Yes, by the rule in section 3 and stated to the reader; nothing a consumer reads, and never CP-0, CP-1 or CP-8 |
| 4 | Build Extended before Brief? | Yes. It is the methods' own switch, removes nothing and needs no ruling on omissions |
| 5 | Who states the depth to the reader? | CP-OS, from the run record, on the summary, Overview and Modules. Modules state it only where it changes a conclusion |
| 6 | Are runs of different depth compared by Changes? | Yes, same issuer and pathway as now, with a new cause `Depth setting` |
| 7 | Does depth go in the run id? | Yes, as a suffix when not Standard |
| 8 | Is depth offered on every tier? | Yes, defaulting to Standard, each combination labelled with its proof status; Extended on Deep at high effort refused until measured |
| 9 | Where is it set? | The run-start page's main form and `--depth`, beside effort; not in the context file, which holds the analysis inputs |
| 10 | May sub-part files be withheld when their input is absent (portfolio parts with no portfolio file, 4A/4B with no legal documents)? | Yes, and at every depth, since it is a source rule and not a depth choice; it is consistent with keeping the sub-parts inside their parents |
| 11 | Paid proof | The seven runs in section 7, after the in-flight work lands; no saving is quoted on the page before them |

## Not verified

- Every saving and cost for Brief and Extended. They are assumed output shares multiplied by measured
  rates from one run per effort level, one issuer, one route. No depth block has been sent to a model.
- That a module told to write less keeps the same conclusions and figures. This is the main risk and
  only a paid comparison can show it.
- The fit of time against calls and output (26 points, two runs). It is not a model of latency, and
  one medium call ran at a third of normal speed while both runs overlapped (`REPORT.md:95`).
- The contents of `CPOS_REGISTER_SCOPE.md`, the register presence check, the CP-1 gate, `run_script`
  and the CP-DR lookup: all in flight in other sessions. I read the register-scope session's note, not
  its branch. The overlap between its cut and Brief is therefore not quantified.
- Which registers have no consumer on other issuers and pathways. The inventory covers two TDG Full
  runs; the eight modules outside Full have no run on current texts and no measured figures here.
- I read the method texts by search (modes, page budgets, step lists, count words), not in full. Other
  depth switches may exist in them. The per-module Brief contents in section 4 are proposals to be
  checked against each method and the inventory when the scope file is written.
- How the model behaves when a Brief block and the method disagree, and the cost of any resulting
  rejected drafts.
- Line numbers are from `claude/quality-defects-appendix-cpdr` at `0985bb5`; `cpos_launch.py` is
  being edited elsewhere and they will move.
- The per-module figures were recomputed in this session from the two retained call logs with a
  script kept in the session scratchpad, not in the repository. This paper was not reviewed by a
  second reader.
