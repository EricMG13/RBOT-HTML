# Analysis depth and model routing as launcher settings: proposal for the owner, 2026-11-13

Proposal only. No code, test, run folder or method text was changed, and no model was called.
Revision 3: adds the owner's two ideas (routing presets on the Advanced level; depth by limiting
steps in every module except the critical ones) and is re-checked against `main` at `73aec77`, which
holds all the methodology work it depends on: PRs 103, 107, 108, 110, 111, 113 and 114.

Three separate controls: **tier** (Lite, Full, Deep: which modules run), **routing** (which model
and reasoning effort each module gets) and **depth** (how far a module that runs takes its analysis).

## 1. Bottom line

- Both ideas are workable, and they share one thing that must be decided first: the list of
  critical modules.
- Depth: one run-wide setting, **Brief**, **Standard** or **Extended**. Standard is today's
  behaviour, byte for byte. Brief is a named list of method steps each non-critical module does not
  run; Extended turns on the long forms the methods already define. Critical modules are never
  reduced.
- A step list, not a step count or a turn limit. A module that runs out of turns is lost, not
  shortened, and the method's steps are chained by gates, so the skipped steps have to be named.
- The register cut in PR 107/108 has already taken most of what Brief could save by writing less.
  What is left to save is the work of the steps themselves, which is also where the risk is: a
  module that reasons less may conclude differently. That needs a paid comparison.
- Routing: three of the four presets exist today (Fast, Balanced, High). **Mixed** (Opus at high
  effort on some modules, Sol at medium on the rest) is new: it needs a model per module, where a run
  has one model today. It is simplest on the Copilot route, which serves both models on one account.
- "Critical and large" should be "critical, where a gain is measured". Evidence validation (CP-5) is
  the largest module (USD 2.26 of 8.62) because of what it is sent, not what it reasons; on Opus it
  alone would cost an estimated USD 6 to 7.
- Estimates for a Full run at medium, none measured: Brief saves about 5 to 8 minutes of 62.5 and
  USD 0.3 to 0.5 of 8.62; Extended adds 6 to 16 minutes and USD 0.5 to 1.5; Mixed costs about USD 11
  to 13 a run. The tier remains the large lever.
- Brief is a small prize (5% to 13% of a run, inside unknown run-to-run variation) for a scope file,
  three check changes, page statements and most of an estimated USD 85 to 100 of paid proof. Extended and the Balanced change are cheap.
  Decide whether Brief is worth building at all (question 15).
- Build order: the critical list and the record; the Balanced change; Extended; Brief for two
  modules if wanted; Mixed last, after one paid Mixed against Balanced comparison.

## 2. The critical modules

One list, used by both settings. A module is critical when later modules, the Forecast page or the
charts compute from its figures or reuse its text.

| Module | Why it is critical | Depth | Routing |
| --- | --- | --- | --- |
| Source readiness (CP-0) | Its input gate and content map decide what every module may read | Never reduced | Medium: measured adequate |
| Financial foundation (CP-1) | Nine Full modules, Forecast, charts and Changes read it. PR 111 gives it the Deploy V method and recomputes its figures in code at acceptance | Never reduced | Medium: measured adequate, and now checked in code |
| Business and transaction (CP-1A) | Its transaction, revenue-mix and operating-model registers are reused downstream | Never reduced | High: modest measured gain |
| Fundamental credit (CP-2) | Five Full modules and Changes carry its passages, triggers and definitions | Never reduced; Extended adds Deep Synthesis | High: the measured gain |
| Downside (CP-2A) | Since PR 113 the Forecast page's Downside is computed from its scenario row, and the launcher checks CP-2G's shock against it | Never reduced; Extended allows up to four scenarios | High: the forward interest schedule is its input |
| Forward credit model (CP-2G) | The forecast is computed from its inputs block | Never reduced | Medium: untested |
| Changes (CP-8) | Runs from a pack Python builds; compares the two runs | Never reduced | Medium |

Not critical in a Full run, and so open to Brief: Research (CP-DR), Legal (CP-4),
Rates, FX and ESG (CP-2E), Security selection (CP-3), Evidence validation (CP-5), Committee (CP-6).
They were 53% of the medium run's model time and 59% of its cost.

Inside a non-critical module some items stay protected at every depth, because a page or a check
reads them: the four reader passages, Basis lines, `## Sources`, `## Gaps`, confidence inputs, every
report selector, chart and owner table, the ESG tables
(owner, 2026-11-13: kept), and CP-5's checks of critical-module figures.

## 3. Depth by step list

### What the landed work changes

| Landed on `main` | Effect on a depth setting |
| --- | --- |
| Register scope per module, `CPOS_REGISTER_SCOPE.md`, for ten modules (PR 107) | The fixed cut is done at every depth. CP-2A no longer writes ten registers, CP-3 twenty-three, CP-5 thirteen. Brief cannot save that output again |
| The cut tells the model to keep doing the work: "Any figure, limitation or conclusion you draw from that work goes in a register you do write" | The steps still run. Not running them is the remaining lever, and it is the owner's second idea |
| Presence check: a handoff of the ten modules is refused if it lacks a required register (`required_registers`, `register_issues`, PR 108) | A skipped step's registers must be subtracted from the required list, or a Brief handoff is refused for obeying its instructions |
| CP-5 is told which registers upstream modules were told not to write (`upstream_scope_note`) | The note must also carry the depth omissions, or CP-5 reports them as findings |
| Instruction ceilings per pathway are not raised (PR 111 ruling); on `main` `earnings_update` has 566 characters left of 546,000 and `short_snapshot` 1,788 of 157,500 (the CP-1 session's measurement; the ceiling test passes) | A Brief block must make a module's instructions shorter, not longer |
| CP-DR page and SEC lookups, on by default for a public case, at most 40 distinct addresses a run, setting recorded at start and a contradicting relaunch refused (PR 110) | A depth lever for CP-DR (pages), and the pattern for recording depth |
| CP-1 on the Deploy V method with an acceptance check (PR 111) | Confirms CP-1 has no Brief or Extended form |

### Mechanism

- One file, `docs/reuse/selected-methods/CPOS_DEPTH_SCOPE.md`, with a section per module and depth,
  loaded like the register scope file (`path § module`). Archived method texts stay byte-identical.
- A Brief section names steps by step file and number, and the registers those steps write, in the
  register scope file's own wording ("do not write …"), so `register_scope`, `required_registers`,
  the presence check and CP-5's note read both files through one function.
- It then says: "Analysis depth for this run is Brief, chosen by the user. Do not run the steps
  named. Treat each as complete wherever a gate asks for it. This is not missing evidence: do not
  block, and do not report it as a gap. Every other step applies in full."
- A step file is withheld only when every step in it is skipped (portfolio parts with no portfolio
  file, 4A and 4B with no legal documents). That is what pays for the block within the ceiling.
- Two existing sentences need a depth-aware form: the header "Run the complete selected method
  below", and the transport rule that a file not sent "could not be established".
- Extended uses the methods' own trigger words, as `DEEP_DEBATE_BLOCK` does for CP-6. CP-2's Deep
  Synthesis has no switch today; Extended adds one.
- An Extended block must fit the same ceilings: CP-2's Deep Synthesis block is checked per pathway.
  With 566 characters left on `earnings_update`, neither block may add net text there.
- Standard sends no block, so today's instruction files and their test pins do not change.
- Never a turn limit, write limit or output limit: each cuts a module off instead of shortening it.

### Per module

Measured columns are the medium Full run before the register cut. Step lists are candidates, to be
confirmed against each method and `appendix-inventory.md` when the scope file is written.

| Module | Measured: USD / s | Steps in its files | Brief: candidate steps not run | Extended | Est. Brief saving |
| --- | --- | --- | --- | --- | --- |
| CP-DR | 0.28 / 151 | Research steps | None skipped; fewer ranked questions and a 15-page lookup limit instead of 40 | More questions; the full 40 pages | USD 0.02, 30 s |
| CP-4 | 0.37 / 67 (blocked) | 14 + 4A 13 + 4B 9 | 4A and 4B files withheld when legal documents are declared "none"; with documents, steps 10 and 11 (market-norm comparison, aggressiveness score) | Nothing | USD 0.05 |
| CP-2E | 0.66 / 350 | 10 + ESG 9 | Steps 06 and 07 (FX, commodity) only when step 01 finds no exposure. ESG steps untouched | Every sensitivity | USD 0.04, 50 s |
| CP-3 | 0.80 / 352 | 11 + instrument 12 + portfolio 10 | Portfolio file withheld when no portfolio file is supplied; step 04 (override review); instrument steps 04 to 07 for the recommended instrument and its nearest alternative only | Every instrument | USD 0.08, 75 s |
| CP-5 | 2.26 / 649 | 9 + integrity 11 | Integrity steps 07, 08 and 10 (duplication and committee readiness, handoff envelope, remediation map); steps 04, 05 and 07 (lineage, calculation register, auditability: registers already cut). Citation, maths and consistency audits stay | Trace beyond the top five drivers | USD 0.09, 105 s |
| CP-6 | 0.73 / 566 | 11 + portfolio debate 11 | Portfolio debate file withheld when no portfolio file is supplied | Deep Debate (exists today) | USD 0.06, 45 s |
| Six modules | 5.10 / 2,135 | | | | About USD 0.35 and 305 s, before fewer calls |

Basis of the estimates: output is USD 10 a million tokens; a fit over 26 module results gives about
7.6 seconds a call plus 12.3 seconds per 1,000 output tokens (R² 0.82); each figure is an assumed 10%
to 30% of the module's output. A further 10 to 20 fewer calls would add 1 to 3 minutes and up to
USD 0.2. The shares are assumptions, and the register cut has since changed the baseline.

### The setting, its record and Changes

- One run-wide value, resolved by CP-OS to a depth per module and written in the run record as that
  map. A per-module control can be added later on the same record; I would not build it now.
- Recorded at run start like the lookup setting, and a relaunch with a different depth is refused.
- Run id gains `-brief` or `-extended`; Standard adds nothing, so existing ids are untouched.
- The summary the analyst approves lists, per module, the steps not run, and labels the estimate.
- CP-OS states the depth to the reader from the run record: one sentence on Overview, and per module
  on the Modules page what was not run. Modules do not state it: CP-OS refuses a limitation an earlier
  handoff already states. A module adds a limitation only where a skipped step changes its conclusion.
- A forecast figure blanked for a negative-cash year (PR 114) is missing by rule, not by depth, and
  Changes must not assign it the depth cause.
- Changes (CP-8) still compares runs of different depth; a Brief refresh after a Standard run is the
  main use. The pack gains both depth maps. An item one run left out by depth is listed once as "not
  produced at this depth", under a seventh cause `Depth setting`, never as a change at the issuer.

## 4. Routing presets on the Advanced level

### What exists

The run-start page already offers a model (GPT or Claude) and an effort at the Advanced level only
(`inbox/runs.py`, `_LAUNCHES`). A run has one model; effort can differ per module.

| Owner's preset | Today | Refinement |
| --- | --- | --- |
| High: high effort on all modules | Exists, for either model | None. Measured on Sol: USD 11.37 and 85.9 minutes against 8.62 and 62.5 |
| Fast: medium on all | Exists, called "fast" | None |
| Balanced: high on critical and large modules, medium on others | Exists: high on nine modules (`BALANCED_HIGH_MODULES`), of which two have a measured gain and six are untested | Define the high set by measured gain: CP-1A, CP-2 and CP-2A (`REPORT.md`, effort routing). Spliced estimate USD 9.09 a run against 9.52 for today's Balanced |
| Mixed: Opus high on critical and large, Sol medium on others | Does not exist. One model per run | Below |

### Why not "large"

- CP-5 is large because its first prompt holds every upstream handoff. No run shows high effort or a
  second model improving it, and it is the module nearest Copilot's summarising threshold.
- CP-0 and CP-1 were measured adequate at medium, and CP-1's figures are now recomputed in code.
- High effort's one clear gain (next year's scheduled interest) came from a single source search in
  CP-2, which one instruction sentence would secure at medium.
- So the high set is three of the critical modules: CP-1A and CP-2 on a measured gain, and CP-2A
  because the forecast's Downside now rests on it. Others join when a run shows a gain.

### What Mixed needs

| Need | Detail |
| --- | --- |
| A model per module | The run record holds one config and an effort per module. Mixed adds a config per module; the ledger, cap and resume read it |
| One account | Copilot serves Sol and Opus (`copilot-sol-medium`, `copilot-opus-medium`), so one sign-in covers both. On direct routes Mixed needs both providers' keys in the launching environment |
| Price | Opus lists USD 20 output, 5 to 8 cache write and 0.20 cache read per million tokens, against Sol's 10, 2.50 and 0.10: two to three times per module on the same tokens |
| Cost estimate | CP-1A, CP-2 and CP-2A on Opus at high: about USD 4 to 5 in place of 1.61, so about USD 11 to 13 a run. Adding CP-5: about USD 15 to 18, against a USD 20 cap. I recommend against CP-5 on Opus |
| The cap | Each call reserves its worst case before it is sent; the Opus reservation is larger than Sol's USD 7.17. The reservation must be checked per module's model |
| Research (CP-DR) | Its web search runs only on OpenAI, so CP-DR stays on Sol |
| Limits | Opus allows 64,000 output tokens a call where Sol runs at 32,000; context sizes and the summarising threshold differ per model and are unmeasured for Opus |
| Checks | The same acceptance checks apply to both models; how often Opus drafts are rejected is unknown |
| Ruling | The standing run-start ruling names each config a launch may use; Mixed needs it amended |
| Record | Run id's config part becomes `mixed`; the summary and the Evidence page list model and effort per module |

### Combining the three controls

- The page shows tier, then depth on the main form, then routing at Advanced. Routing defaults to
  Balanced, depth to Standard.
- A module at Brief depth runs at medium effort whatever the preset: paying for high effort on a
  shortened module is wasted.
- Refused until measured: Extended on Deep at High or Mixed (the largest prompt), and Mixed on a
  direct route with one provider key missing.
- Seven routings, three depths and three tiers are 63 combinations. Two are measured (Full, Standard,
  Sol at medium and at high). The page labels each as run and reader-checked, or estimate.

## 5. Risks, paid proof and build order

| Risk | Guard |
| --- | --- |
| A skipped step was how the model reached its conclusion, so the bottom line weakens | Paid comparison on the same sources, scored against a list written before the runs: critical figures identical, each module's call unchanged, errors counted |
| Brief removes something a later module or page reads | The critical list and protected items; a test that no Brief step writes a register with a consumer in the inventory, as the cut-id test does for registers |
| Block and method disagree, drafts are rejected and the saving goes on repairs | Blocks name exact step numbers and register ids; the presence check reads the same scope; rejections counted in the trial |
| The reader takes a Brief or Mixed run for a standard one | Run id, approved summary, Overview and Modules statements from the run record |
| Changes reports depth or model as a change in the credit | The pack's depth maps and the `Depth setting` cause; model and effort per module shown beside both runs |
| Two models write in different styles and a later module misreads an earlier one | The handoff format and checks are the same for both; read in the Mixed trial |
| Mixed exceeds the USD 20 cap mid-run | Pre-launch estimate per module's model; Mixed refused when the estimate plus one reservation exceeds the cap |
| Evidence validation checks less | Its audits of critical figures are never skipped |
| Savings are smaller than run-to-run variation, which is unknown | Two runs per setting before any figure is shown on the page |

Paid runs, on `main` as it now stands (PRs 110 and 111 changed the baseline). Each needs its own
explicit action under the standing ruling.

1. One Standard, Balanced run on the merged tree: the baseline.
2. Two Brief and one more Standard on the same issuer; one Brief and one Standard on a second issuer.
3. One Extended run, read for whether the extra length is extra sourced analysis.
4. A Brief run after a Standard run, to read how Changes words the difference.
5. Two Mixed runs against the Balanced baseline on the same issuer, scored against the same list.
6. The fidelity check `AGENTS.md` requires for the new statements on Overview and Modules.

About nine runs, an estimated USD 85 to 100.

Build order.

1. The critical list as one constant; `--depth`; the run-start answer; the run record, run id suffix
   and summary line. Standard changes no instruction byte. Offline only.
2. Balanced's high set moved to the measured modules. A one-line change, with paid run 1.
3. Extended: CP-2's Deep Synthesis block; Extended sets CP-6's existing option. Removes nothing.
4. If Brief is wanted: the depth scope file with Brief sections for CP-3 and CP-5, read by the presence check and
   CP-5's note; the consumer test; the ceiling test.
5. The depth statements in the library, with the fidelity check; the Changes pack fields and cause.
6. Paid runs 2 to 4. Only then widen Brief or show a saving on the page.
7. Mixed: a config per module, the per-model reservation, the ruling amendment, then paid run 5.

## 6. Questions for the owner

| # | Question | Recommended answer |
| --- | --- | --- |
| 1 | Which modules are critical? | CP-0, CP-1, CP-1A, CP-2, CP-2A, CP-2G and CP-8. One list: depth never reduces them, and the high-effort set is drawn only from them |
| 2 | Is Brief a list of named steps per module, or a number of steps? | Named steps. A number lets the model choose what to drop, which cannot be checked or told to the reader |
| 3 | Depth names | Brief, Standard, Extended. Not the tier names, the effort names, or "level" (the page's disclosure setting) |
| 4 | May Brief skip a step whose registers are all already cut? | Yes for non-critical modules, after the paid comparison shows the module's call and figures unchanged |
| 5 | Build Extended before Brief? | Yes. It is the methods' own switch and removes nothing |
| 6 | Balanced: which modules get high effort? | CP-1A, CP-2 and CP-2A, replacing today's nine, until runs show a gain elsewhere. Not CP-5 |
| 7 | Mixed: which modules go to Opus? | The same three. Not CP-5 (cost) and not CP-DR (web search is on OpenAI only) |
| 8 | Mixed: which route? | Copilot first: one account serves both models. Direct routes later |
| 9 | Is Mixed built before it is measured? | No. One paid Mixed against Balanced comparison decides whether it is worth the per-module model work |
| 10 | Where are the settings? | Depth on the run-start main form and `--depth`. Routing presets at Advanced only, as model and effort are today |
| 11 | Does a Brief module run at medium effort under every preset? | Yes |
| 12 | Who states depth and routing to the reader? | CP-OS from the run record: summary, Overview, Modules; model and effort per module on Evidence |
| 13 | Are runs of different depth or routing compared by Changes? | Yes, same issuer and pathway as now, with the new cause `Depth setting` |
| 14 | May sub-part files be withheld when their input is absent? | Yes, and at every depth: it is a source rule, not a depth choice |
| 15 | Is Brief worth building? | Not yet. Build Extended and the Balanced change; decide on Brief after the tier work shows what time remains to save |

## Not verified

- Every saving and cost for Brief, Extended and Mixed. They are assumed shares and price ratios applied
  to one Sol run per effort level, one issuer, one route, taken before the register cut.
- That a module told to skip steps keeps the same conclusions and figures. This is the main risk.
- Any Opus run on the current texts: its output volume, rejection rate, context limit, summarising
  behaviour and reservation size are unmeasured here. The Mixed cost is a price-ratio estimate.
- That Copilot serves two models within one run without a new session cost or cache loss.
- The candidate step lists. I read step names and the register scope file, not each step's text; a
  step whose registers are cut may still feed a kept step. Each list must be checked when written.
- PRs 110 and 111 in full. I checked the facts this paper relies on against `main` (the lookup limit
  and recorded setting, the ceilings, CP-1's method and check, the register scope modules, the
  Balanced list), not every line of either change. No model has run under the new CP-1 method.
  `run_script` has no PR yet.
- How the model behaves when a Brief block and a method gate disagree, and the cost of any rejected
  drafts that follow.
- Whether today's nine-module Balanced set outperforms the proposed three: six of the nine are untested.
- Which registers and steps have no consumer on other issuers and pathways: the inventory covers two
  TDG Full runs. The eight modules outside Full have no run on current texts and no figures here.
- The time fit (26 points, two runs) is not a model of latency. This paper was not reviewed by a
  second reader.
