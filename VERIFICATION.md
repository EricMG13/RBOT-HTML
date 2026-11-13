# Verification record

Keep one running record here. A pass applies only to the stated scope. Earlier verification of the
engine is in [EricMG13/final-workflow](https://github.com/EricMG13/final-workflow)'s
`VERIFICATION.md`, which also keeps the retained runs this copy leaves out.

## 2026-11-13 — Signal slice 2: service and feed page (branch `claude/signal-2-service-pages`, tip `ba04ff7` plus this entry)
Scope: Signal's HTTP service, feed API and feed page, its packaging, and the optional Signal link on the run start rail. No AI pass, no groups or threads, no settings pages, no login, no model call, no cost. The reader check in `AGENTS.md` applies to the issuer report and is not owed here.
- `uv run pytest` on the ten `tests/test_signal_*.py` unit files, `tests/test_run_start_service.py` and `tests/test_issuer_library_packaging.py`: exit 0, 377 passed.
- `uv run pytest tests/test_signal_page_browser.py -q -m browser`: exit 0, 13 passed, run in local headless Chrome on macOS against the real service with fixture data. A reviewer broke the page thirteen ways in a scratch copy (unsafe title rendering, unsafe links, lost focus, missing error band, low contrast, removed focus ring and others); a test caught each.
- `uv run pytest tests/test_library_page_browser.py -q -m browser` after the shared browser-driver code moved to `tests/browser_cdp_common.cjs`: exit 0, 102 passed, 1 skipped (the opt-in screenshot test); run at `300cbef`, not re-run after the last fix wave, which did not touch those files.
- `node --test src/deploy_workflow/signal/web/render.test.cjs`: exit 0, 10 passed. `uv run python tools/quality_gate.py`: exit 0, 0 findings.
- Security: the service was attacked on loopback by a reviewer (Host and Origin variants, cross-site requests, path traversal, request framing, cookie and name injection, search syntax, slow clients). One weakness was found and fixed: slow clients could hold every connection; there is now a 120-second connection deadline and at most 16 connections per address. The run start `--signal-url` option had its own review: about 75 hostile URL forms and 6,000 generated inputs produced only `http://host:port/` links, and 440 start-up argument combinations behaved the same before and after the change.
- Probes are kept under `.superpowers/sdd/2026-11-13-signal-2-service-and-feed-pages/probes/`, not in the repository. Not all exit 0: `probe_sec4_slowloris` (shares 127.0.0.1 with the connections it holds), `probe_sec7_make_server_contract` (does not catch the refusal it provokes), `probe_sec4r_timer_hygiene` (calls a helper with an older signature), and `probe_branch_growth` and `probe_branch_pill_inflight_pass` (call the time-based count that was replaced by a count by story id; `probe_wave_growth` and `probe_wave_pill` replace them and exit 0).
- Growth, synthetic store of 50,000 stories with the five new indexes: feed reads at most 0.011 s, new-story count 0.014 s, adding a topic at most 0.019 s (reviewer's `probe_wave_growth`).
- Live fetch of two public feeds, no model call, no cost; throwaway root outside the repository; the page was driven before the last two fix commits. `sources propose` and `approve` for UK CMA cases (Atom) and BEREC (RSS), `topics add` Mergers (merger, acquisition) and Telecoms (roaming, spectrum, broadband, mobile), `ingest`: CMA cases 50 new, BEREC 10 new, exit 0; `topics list`: Mergers 22, Telecoms 3. `serve` on 127.0.0.1, page at 1280 px in the desktop app's browser: the name was kept from its cookie, following Mergers filled For you with 22 cards, Save set its pressed state, a search for "roaming" inside For you gave no cards (those stories are under Telecoms), Latest showed CMA and BEREC cards with their topic tags, `/api/status` reported 2 approved, 0 failing, no loop error, and the console stayed empty.

Not verified: anything on Windows (`Start signal.cmd`, Ctrl-C, port refusal); browsers other than Chrome and any screen reader; the 45-second poll timer itself (tests trigger the poll by making the tab visible); the run start rail link clicked in a browser; the real 120-second deadline (tested scaled down) and the per-address share behind a proxy or over IPv6; the ingest loop's own 60-second tick against real feeds; a root on a network or synced folder; store sizes on real data; a display name changed in another tab; a crash between storing a story and matching it to topics; the browser-test clean-up after a hung run. The slice 1 fetcher findings from the pre-merge review of pull request 101 are not addressed here.

## 2026-11-13 — Signal slice 1: command line (branch `claude/intelligence-feature-design-4dd9c3`, tip after the follow-up Low batch)
Scope: Signal slice 1 command line only (`python -m deploy_workflow.signal`); no pages, no AI pass, no login, no model call, no cost.
- `uv run pytest tests/test_signal_store.py tests/test_signal_feeds.py tests/test_signal_fetch.py tests/test_signal_fold.py tests/test_signal_ingest.py tests/test_signal_cli.py -q`: exit 0, 148 passed, 0 warnings.
- `uv run python tools/quality_gate.py`: exit 0, 0 findings in 20 changed files.
- Security: the fetch code had a security audit and a re-review; the total 10-second deadline was rebuilt so a watching thread cuts the connection (a deadline checked on the calling thread cannot run while a standard-library call blocks). The 17 attack probes behind it (`probe_fetch_*`) are kept under `.superpowers/sdd/2026-11-13-signal-1-store-and-ingest/probes/`, not in the repository; at this tip 19 of the 20 probes and the local real-TLS experiment exit 0; `probe_fetch_sec3_post_deadline_connect` case B (a lookup inside `socket.create_connection` that outlives the deadline) still exits 1 because the connect follows that lookup with no point to check between them.
- Live fetch of two public feeds (UK CMA cases Atom, BEREC RSS), no model call, no cost; real network, throwaway root outside the repository. All commands exit 0. `<root>` stands for the long scratch folder passed to `--root`:
```
$ signal --root <root> sources propose "CMA cases" --kind regulator --url https://www.gov.uk/cma-cases.atom --by owner
$ signal --root <root> sources propose "BEREC" --kind regulator --url https://www.berec.europa.eu/en/rss.xml --by owner
$ signal --root <root> sources approve 1
$ signal --root <root> sources approve 2
$ signal --root <root> ingest
CMA cases: ok: 50 new
BEREC: ok: 10 new
$ signal --root <root> stories --limit 5
2026-11-11 12:01  CMA cases  Pilgrim’s / Walkers Deli & Sausage Co merger inquiry
2026-11-11 07:51  BEREC  BEREC views on roaming topics of draft ITRE report
2026-11-11 07:30  CMA cases  AkzoNobel / Axalta merger inquiry
2026-11-11 07:02  CMA cases  McCormick / Unilever merger inquiry
2026-11-10 14:09  CMA cases  Final recommendation that the Secretary of State replace the Assimilated Technology Transfer Block Exemption
$ signal --root <root> sources list
1  approved  healthy  2026-11-11 12:01  CMA cases
2  approved  healthy  2026-11-11 07:51  BEREC
$ signal --root <root> ingest
(no output: sources not due within the minimum interval)
```
- Known limits: DNS lookup, TCP connect and TLS handshake cannot be interrupted, so fetch returns on time but the worker thread may outlive the call until that single step ends; after the deadline no new connection is opened except one whose lookup ends inside `socket.create_connection` itself (it is then closed and refused before the handshake); DNS rebinding between the address check and the connection; two simultaneous passes may both fetch a due source; Windows not run (the duplicate-socket call was chosen for it).
- Not verified: Windows; a live failing source, redirect, or conditional-GET (etag) against a real server; `ingest --loop`; stories were not compared with the feeds by hand beyond the five lines shown; the "no output" second ingest was read as "not due", not checked against the interval setting.

## 2026-11-13 — Issuer library screens redrawn from a screen-to-component map; source references and audit material moved to Evidence (branch `claude/report-redesign-evidence`)
Scope: presentation only, offline, base `517b9fb`, head `d47e3ba` before this entry; no provider or model call, no change to analysis, module instructions or the Python that builds `data.js` (no Python outside `tests/` changed; under `apps/` only the README and `fixtures/shape-key.json` beside the web files changed; under `tests/` 19 files changed, among them `test_library_reader_refs.py`, `test_cpos_launch.py`, `test_run_start_page.py`, `test_library_page_browser.py`, `test_library_changes_browser.py` and the `browser_probe_*.js` helpers, edited to match the new pages). Design: `docs/visualisations/2026-11-13-screen-component-map.md`, plan `docs/superpowers/plans/2026-11-13-library-redesign.md`. Rules applied: findings pages show findings and one trace control per paragraph, row or figure; source references, file names, hashes, ids, calculation ids, registers, gap ledgers and run codes are drawn only on the Evidence page and its drawer; text written for another module is drawn nowhere, search and drawer included; a run is named by period and pathway; nothing is computed or reworded (allowed: counts of listed items, the elapsed clock on Run activity, date display); motion only for live run state.
Reviews: tasks 0 to 13 each had a task review and fix rounds (T1 1, T2 1, T3 3, T4 1, T5 2, T6 2, T7 1, T8 1, T9 2, T10 3, T11 1, T12 2, T13 1; the third rounds from a root-cause plan); two end batches closed 30 deferred Low items. Whole-branch review at `ac1164f`: changes needed, 2 High (trace controls dead on Forecast and Changes; search and the drawer reached text written for another module), 6 Medium, 8 Low. A simplification review recommended four rewrites and deletions and compacting the classifier answer key (same parsed JSON). Fix wave `7881b72..47b8f28`, round 2 `53f4070`, round 3 `d47e3ba` (an Evidence search hit is matched by module and line together); each round was re-reviewed, and the re-review of `d47e3ba` approved with no High or Medium finding open.
Fidelity check (probe output at `53f4070`; the controller reports the same four checks pass at `d47e3ba` with these figures, real run `tdg-proof-snapshot-opus-002`, TransDigm, as of 30 September 2024, credit snapshot, earlier methods): findings, 19 findings routes, 0 failures, 2,463 figure tokens each found in the run's handoff data, and no Basis line, file name, hash, calculation id, method code, register id, run code or run folder in page text; evidence, 9,179 handoff cells present on the Evidence page across 13 modules, 0 failures (inter-module columns excluded by rule); hidden, 45 hidden items absent on 111 routes, 0 failures; overflow, 108 route and width checks, 0 failures. The same four checks pass on a copy of `apps/issuer-library/fixtures/synthetic-new-format`. Before and after the fix wave the visible text of 18 of the 19 findings routes is identical; Forecast differs only by the model's hash being replaced with its period-and-pathway label. On the real run the Gaps tile and tab badge both read 97 (plus 39 ledger rows and 11 model scope limits in their own group heads) and Calculations reads 232 (plus 11 comparison rows and 2 method notes).
Reader check, scope: ONE real run (the run above, TransDigm, earlier methods), read by the controller from 1440 px screenshots at `ac1164f` (Overview, Financial foundation, Changes, Forecast) against the September VMO2 reference (source readiness screen). Verdict: pass with issues. Holds: judgement first on every page; status and register tables became typed components; no source, file, hash or id text on findings pages; one trace control per paragraph, card and figure. Issues left open: chart bar labels are the data's raw values with no thousands separators ("6585"); chart footnotes carry page locators written by the module ("page 153"); two runs with the same period and pathway read identically; the first Forecast card leaves blank space beside a taller neighbour. The Evidence page was not part of this read, Run activity was read on fixture runs only, and the fix wave after `ac1164f` was checked by probes and tests, not re-read by eye.
Gates, by who measured and at which commit: at `d47e3ba` node tests (`node --test apps/issuer-library/credit_os/web/*.test.cjs`) 787 passed, 0 failed, exit 0 (measured by the controller and again by the author of this entry), and the library rebuild exit 0 (controller); at `53f4070`, the code before round 3, the controller measured the five library pytest files (`tests/test_update_library.py tests/test_library_index.py tests/test_library_reader_refs.py tests/test_issuer_library_packaging.py tests/test_context_form.py`) 174 passed exit 0 (also measured by the author of this entry at `53f4070`, node then 786 passed), the quality gate 0 findings, and the browser tests per file, every file exit 0: `test_library_page_browser.py` 102 passed 1 skipped (an opt-in screenshot test), `test_library_changes_browser.py` 8, `test_model_shell_browser.py` 7, `test_run_start_page.py` 144, `test_cpos_launch.py` 8 browser-marked, 269 passed and 1 skipped in all. Round 3 changed `evidence.js`, `screen.js`, one node test file and one line of `test_library_page_browser.py`; at `d47e3ba` its implementer re-ran the two library browser files (102 passed 1 skipped; changes passed), the five pytest files and the quality gate, all exit 0, and the controller did not re-run those.
Merge with `main` at `d941eef` (79 commits; conflicts in this file, `static.test.cjs` and `tests/test_library_page_browser.py`): both records kept; the branch's tests kept with `main`'s pathway titles ("Full credit assessment" for `credit_snapshot`) in the assertions that read them; `main`'s new lite-run browser test proves CP-2 wrote the Overview lead from the key findings' trace controls, because the redesigned Overview draws no "Written by" link. On the merged tree, each exit 0: node tests 787 passed; the five library pytest files 176 passed; quality gate against `d941eef` 0 findings; `tests/test_cpos_launch.py` and `tests/test_run_start_page.py` without browser tests 709 passed, 1 skipped (the paid live test); browser tests per file 274 passed, 1 skipped (changes 8, model shell 7, CP-OS launch 10, run start 147, library page 102 and the opt-in skip; the two tests that first failed were fixed and re-run, not their whole files); library rebuild and the four run-level checks with the figures above. Not re-done after the merge: the reader check, and any read of a lite run in the redesigned pages beyond that one synthetic test.
Open for the owner: the run name does not separate two runs with the same period and pathway; passages draw identifiers and file names as the module wrote them (a module-instruction follow-up); off-contract Markdown inside a passage (a fenced block, a table) is drawn raw or only in Evidence; a module with two saved outputs can share a line number between outputs, so an Evidence search hit could mark the first output's row (no such run exists); excluded run folder names appear under "Not shown" on the library home; an earlier-format Overview lists no dates; at 390 px a scatter chart scrolls in an unfocusable region; "Technical audit" is no longer a navigator search entry; the pull request is about 11,700 added lines against the 800-line guide (only `517b9fb..85cc2d6` stands alone as a separate pull request).
Not verified: the reader check covers one run, one issuer and earlier methods only; no new-format real run exists; print, forced-colours and screen-reader behaviour were not exercised by a person; real keyboard presses (the tests use focus and click); browsers other than Chrome; Run activity against a live service; the full non-browser Python suite (weekly in CI), of which only the named files ran.

## 2026-11-13 — Full and lite credit assessments; short credit snapshot deactivated (branch `claude/lite-full-credit-assessment`)
Scope: offline only; no provider or model call. `credit_snapshot` is titled "Full credit assessment"; the new `lite_credit_assessment` (CP-0, CP-1, CP-1A, CP-2, CP-2A; no CP-MODEL, so no forecast) is offered on the run-start page; `short_snapshot` stays wired, is not offered, and a new run of it is refused at the launcher, the run-start summary and the inbox submit. Ruling: `docs/rulings/2026-11-13-full-and-lite-credit-assessments.md`.
- Synthetic lite run, no model: `test_the_lite_pathway_runs_end_to_end_to_a_verified_delivery_with_a_synthetic_provider` reaches a verified delivery with all nine report blocks populated and no forecast published (`cp_forecast_published` false, no "Model not published" line, as nothing was requested). A second synthetic lite run plans CP-8 last against a lite prior and delivers the Changes pack, and the library renders a lite run with the Forecast page stating that no forecast was published. These prove the pipeline, not model output.
- Prompt-size ceilings are tests per pathway; lite measures 392,429 characters (CP-1 5,717 fewer than with CP-MODEL) against 420,000 (table in the ruling).
- Tests: `PYTHONPATH=src:. uv run pytest tests/test_cpos_launch.py tests/test_cpos_scale.py tests/test_context_form.py tests/test_run_start_page.py tests/test_run_start_scheduler.py tests/test_changes.py tests/test_credit_os_catalogue.py -q`: exit 0, 1807 passed, 1 skipped (the paid test); library, scheduler, service, packaging and update tests: exit 0, 500 passed, 1 skipped.
- Page logic: `node --test` on reader, static, calendar and changes `.test.cjs`: exit 0, 394 pass, 0 fail (re-run after the final fix wave).
- Final fix wave: starting a run from a past short-snapshot run keeps the default pathway, does not mark it carried and says the short credit snapshot is no longer offered (page test); a start from an offered-pathway run keeps its plain message (page test); the lite card names the credit agreement (page test); the README names the lite option.
- `uv run python tools/quality_gate.py`: exit 0, 0 findings in 13 changed files (1,171 changed lines).
- Not accepted: no reader check of a real lite run against the September VMO2 reference (AGENTS.md requires one for a presentation change), so the change is built, not accepted, until one real lite run is read. No lite run has been made; its cost (USD 5.07 baseline, measured before the 2026-11-13 method change) is an estimate. The page was not opened in a browser by hand; no lite case is in `model_testing/configs.py`.

## 2026-11-13 — Prompt-first redesign of CP-8, forecast inputs and prose check 6 (PRs 84-91)
Scope: synthetic tests and retained-data comparisons only. No provider was called. No live model has been sent any instruction changed here.

What changed
- Prose check 6 (PR 85): an ID is a cell of a column headed `ID` or ending ` ID` (ruling E7); 27 lines deleted. Retained: 974 files, 1 wrong refusal removed, 0 added, no ID-shaped value lost.
- CP-8 (PRs 86, 87, 89): a pack measure with no row is refused; a row may print its own difference; a fact row is read in every cell; value cells must equal the pack's value (no grouping comma), unit and period; Basis items are `Run comparison` or a module handoff of a run in which the module ran; `Method change` is required only when both runs record `preset` (E1). Deleted: the trend word list (E11), the reading of numbers in words, list tolerance and cross-line joining (E3), the Basis file-name blacklist, the phrase ban. `methods/cp8.md` rewritten once (R1-R10), so runs holding a CP-8 handoff show "Earlier methods" (E10).
- Forecast (PRs 88, 90, 91): the block states `currency`; delivered units read `<currency> millions`; the stated currency must be named in the Financial foundation handoff; a block with `scale` and no `currency` is refused or withheld; a block with neither reads USD millions as before; Net debt data Period is checked at acceptance; the `LTM Qn YYYY` balance path is deleted (397 lines); the instruction names operands by `row` and `period` only.

Evidence (retained data)
- CP-8: the one retained handoff with a pack (tdg-proof-snapshot-opus-002) gives the same 6 issues throughout (two reworded); page verdicts byte-identical across 974 files; digit reading unchanged across 280,974 lines and a 111,692-case comparison.
- Forecast: every retained block re-derives byte-identically apart from reworded withheld reasons in one calculation file; all 23 retained Financial foundation handoffs name USD.
- LTH run 20261112-164724-01: untouched; a relaunch re-derives a calculation file that differs from the delivered one in 25 cells (24 reworded reasons, 1 earlier limit text), so its delivery id would change.

Not demonstrated
- Any model's first attempt under the new CP-8 forms, the `currency` key, the Net debt Period forms, or balances printed as rows under period columns.
- A non-USD issuer end to end: Financial foundation's chart tables are captioned `US$m`, so USD may always count as named.
- 2 of 4 retained Financial foundation handoffs print cash or undrawn only in one-row-per-period tables; under the new instruction those are stated missing unless Financial foundation prints them as rows.

Recorded limits
- CP-8: a withheld size written in words is refused only when a listed unit word directly follows it; a `Not comparable` row can state a movement as a rate; a row allowed its own difference also passes another withheld difference of the same size; another module's name beside the right code passes in Basis; a fact-row cell such as `30/09/2024` is refused when its number equals a withheld size.
- Forecast: a handoff naming the stated currency anywhere passes; one row in another currency passes.
- Deferred: deletion of the `column` path and per-row unit reader, until a proof run shows how balances are printed (E9).

Superseded reviewer probes (E6 and controller rulings of 2026-11-13): `swarm/probe_cp8.py` P3, `g70/p2_gbp_caption.py`, `g50/probe_split_tables.py`, `gaps4_ordinal_neighbour_leak.py`, `gaps4_spelled_fuzz.py`, the `thirty` lines of `counts_change_noun_leak.py`, `c1-review-precise/probe_empty_register_hint.py`, `f1-rereview/p7_token_rule_table.py` (lower-case rows), and the probes pinning the deleted per-cell currency comparison.

Open for the owner (predate this work): billions unit cells read as millions; `£000`/`€000`/`GBP000`/`USD 000` not read as thousands; the pack reads the unit of `Free cash flow (CFO less capex)` as `CFO less capex`; a forecast block naming debt under an `LTM` column is accepted; digits split by markup pass the withheld-size check; with an explicit selection the checker requires no cause though the method text says `Unresolved`.

Ledger: P1 agent=mx-scaffold fix-rounds=0 gates-first-pass=y; C1 agent=mx-feature fix-rounds=0 gates-first-pass=y; C2 agent=mx-feature fix-rounds=1 gates-first-pass=y; C3 agent=mx-feature fix-rounds=1 gates-first-pass=y; F1 agent=mx-feature fix-rounds=1 gates-first-pass=y; F2 agent=mx-feature fix-rounds=1 gates-first-pass=y; F3 agent=mx-feature fix-rounds=0 gates-first-pass=y; Z0 agent=mx-scaffold fix-rounds=0 gates-first-pass=n/a.

## 2026-11-13 — CP-OS sends different method texts to fifteen modules and the canon appendix section to prose modules (branch `claude/deploy-v-methods`)
Scope: offline only; no model or provider run. Tests in `tests/test_cpos_launch.py` prove that the built instructions carry the named texts (and no longer the replaced ones) for CP-0, CP-1A, CP-3C, CP-DR, CP-2D, CP-4, CP-4C, CP-5, CP-6, CP-2, CP-1D, CP-2G, CP-2H, CP-3 and CP-2A (CP-1A's skill came via PR #83), and the canon Analytical appendix section for prose modules. No reader check against the September VMO2 reference was made, so under AGENTS.md this is not a presentation acceptance. Sources, hashes and named edits: `docs/reuse/selected-methods/manifest.json`; per-module source revisions: METHODOLOGY-REVIEW.md, "Method selections of 2026-11-13".
Manifest: all 28 `sha256` values of the method files this branch changed under `docs/reuse/selected-methods/` (manifest.json itself not counted) were computed and equal the archived files. Eleven entries whose archived file is an edited copy (cp-1d, cp-2, cp-2g, cp-dr, cp-3c, cp-2d, cp-4, cp-4c entries and the CP-2A stress copy) no longer carry `exact_copy_found_at`: it is null and `edited_copy_of` names the source before the named edits; every remaining `exact_copy_found_at` path (130) was checked byte-equal to its archived file. `companions_note`, METHODOLOGY-REVIEW.md and the launcher comment say each file's source is the one its manifest entry names, not that all companions are cp-os copies.
Controller rulings beyond the plan: two dispatch groups for Task 5 (5a CP-2D, CP-4, CP-4C; 5b the small named edits); GitNexus and Context7 not used (no new library API); named edit 2a-4 made CP-DR's pack-tool-only quote and reading clauses conditional on the web-search rules; the CP-DR peer-pack pointer now reads "as your method's PEER PACK section describes them"; the PEER_PACK_BLOCK placeholder row cites its TDR.2 gap row; the CP-6 row widened to the four caos header hunks (caos lines 175, 260, 339, 422); CP-OS gets its own copy of the short CP-2A text with `T2DS` tables (`cp2a.md` stays on disk); one CP-OS sentence sent with the appendix section says the canon's `## Analysis` is this transport's `## Findings`.
Notes: the `deploy_vii` bindings still read the stand-in's T3D numbering (not on the CP-OS path). CP-DR's UNRESOLVED rule requires a recorded `search_source` call, which has no web equivalent. The peer-pack placeholder row cites a TDR.2 gap row that may not exist when every question is answered. CP-L10 and CP-8 now also receive the canon Analytical appendix section and its heading note although their method files are unchanged. The method-text pins changed for 20 of 22 modules (only CP-1 and CP-1C unchanged), so the issuer library will mark earlier runs of those modules "Earlier methods".
Open owner items: step bundle section C says `WebSearch` where the transport tool is `web_search`; archived but unsent CP-6 `*_SYSTEM_REFERENCE.md` still carry stale DOWN (QA) lines; the CP-2A copy's "Connection notes (Stage 2)" describe another runtime (the structured one) and "CP-2A takes no citations" contradicts the head's source rule; the section is left for the owner.
Gates, run after the last code and document edits except this entry, each exit 0: `PYTHONPATH=src:. uv run pytest tests/test_cpos_launch.py -q` 685 passed, 1 skipped (the paid live test); `PYTHONPATH=src:. uv run pytest tests/test_issuer_library_packaging.py -q` 10 passed; `uv run python tools/quality_gate.py` 0 findings in 3 changed files.
Not verified: any model response to the new texts; reader quality against the VMO2 reference; the full suite and slow tests (weekly CI); the structured runtime's readers of the unchanged `src/deploy_vii/methods/*.md` files.

## 2026-11-13 — CP-2 and CP-1A send Deploy V's full skills (branch `claude/cp2-cp1a-deploy-v-skills-054d09`, owner "Build rec. 1, then run")
Scope: offline only, no model run, no provider. `cpos_launch._SELECTED` now sends CP-2 (SKILL, `REF_CP-2_STEPS.md`) and CP-1A (SKILL, `REF_CP-1A_STEPS.md`, `REF_CP-2C_STEPS.md`) from cp-os `b57a344` (hashes in the manifest) instead of the DEPLOY VII stand-ins; both now carry the Confidence Score rules and are asked for `### Confidence inputs`; their method hashes changed, so earlier runs show "Earlier methods" for these two. Prepared on `cases/context/primary-full.json` (no TDG context in the repo; fictional source file): CP-2.md 69,224 bytes, CP-1A.md 101,313 bytes, no stand-in path in either.
Tests: new `test_cp2_and_cp1a_run_the_deploy_v_skills_not_the_deploy_vii_stand_ins` (failed before the change); `tests/test_cpos_launch.py` 665 passed; library, update-library and inbox tests 171 passed; quality gate 0 findings. Only the SCORED/UNSCORED lists, SKILL_MODULES, BINDING_COMPANIONS and the two method pins were updated.
Not verified: a paid run; whether a model follows the 18-step workflow inside the reader-passage format; CP-2/CP-1A handoff length against the output limit; the Confidence inputs section for these two on a real draft.

## 2026-11-13 — Brand colours and component look in the issuer library, run start page and HTML Model; Run activity redesigned, spend off the page (branch `claude/brand-application`)
Scope: presentation only, offline, no provider or model call. Fonts unchanged. Brand values were read from the owner's screenshots. Design record: `docs/design/2026-11-13-brand-application.md`.
Reviews: task reviews of the four build tasks (fix rounds 1, 1, 0, 1), all approved; the whole-branch review returned "changes needed (small)": one Medium defect (the empty-state button's label unreadable on hover, 1.5:1) and Lows, fixed in 23a1a3f, re-review approved.
Fidelity check: on real run `cpos-tdg-sol-medium-all-001` the visible text of eight pages (library home 2,553 characters / 44 number tokens; Overview 1,843 / 6; Changes 1,930 / 84; Financial foundation 18,061 / 217; a second module page 12,831 / 24; Forecast 2,698 / 63; Evidence 2,376 / 43; Report history 1,285 / 18) is identical between the library at 4c0eafa and at 23a1a3f, same data, Chrome 1440 px. The reviewer's box comparison on the same eight routes at 1440 px, 720 px and print: the colour commits move no box; the component look moves boxes by 4–8 px with two reflows of about 20 px. Run activity is excluded from both (redesigned). The comparison scripts are in the session's working folder, not in the repo.
Reader check, scope: ONE real run (`cpos-tdg-sol-medium-all-001`, TransDigm, as of 30 September 2024, earlier format), Financial foundation and Overview, read by the controller from 1440 px screenshots taken at 4a94b0d (the later commits touch Run activity only), against two of the September VMO2 screenshots (source readiness; ownership and operating registers). Verdict: pass with issues. The reference is black text with ruled tables and no charts, so the comparison covers judgement-first order and table legibility, not colour. The judgement headline still comes first; tables are ruled with no zebra; state badges read. Issues: the legend key of the second series is dark green while its bars are bright green (open for the owner); bar labels are raw ("6585"), as before this branch; the run is earlier format, so Overview shows no reader passages and its voice was not exercised. Run activity was read on invented sample runs only.
Contrast (reviewer's probe): lowest new text pair 4.77:1; the olive line `#758000` is 4.34:1 and is used for lines only.
Gates, run at the final code commit 9f9659e before the documents were added (the quick ones were run again after), each exit 0: `node --test` on static, changes, reader and calendar tests 394 passed; `tests/test_context_form.py tests/test_brand_tokens.py` 56 passed; `tests/test_library_page_browser.py tests/test_library_changes_browser.py` 97 passed, 1 skipped (the forecast screenshot test, which needs `FORECAST_SCREENSHOT`); `tests/test_run_start_page.py` 144 passed; `tools/quality_gate.py` 0 findings (954 changed lines in scope). The forced-colours test now also covers `.run-badge`, and the CDP helper removes its temporary Chrome profile on failure.
Size: 1,210 changed lines against `origin/main` at 9f9659e (1,051 added, 159 removed), over the 800-line convention; 839 of them are in paths containing `test`. The documents add to that.
Open for the owner: see the design record's list; M2 (the Model navigator's module-family colours, Ruling 24) and the size are the two that need a ruling.
Not verified: a real run in progress on Run activity; the HTML Model on real data and inside the Forecast frame; yellow, violet, hatches, the ledger and conditional paths on real handoffs (synthetic only); real printing (Chrome emulation); Firefox, Safari and Windows high-contrast mode; whether a retained-run verifier compares rendered Model bytes; the other 124 reference screenshots; the weekly and live suites; mutation testing. Moved to the archive to keep this file under 1,000 lines: the 2026-11-10 Context form proposal entry.

## 2026-11-12 — CP-8 checker: a currency code glued to digits, more currency and scale forms, bond names (branch `claude/cp8-checker-currency`, owner "complete 1")
Scope: offline, synthetic plus read-only reading of 974 retained `.md` handoffs; no provider. C1 `EUR437m`, `USD2010` read as figures; C2 `C$`/`A$`/`R$` prefixes, `mln`/`bln`, `'000`, 18 more currency codes (`_CODES` 22 to 40) around a year-shaped number; C3 `2029s` is a bond name, a year. Tests first: 29 of the new cases failed on the unchanged checker, all pass after; `counts_code_glued.py` flipped 1 to 0.
Corpus (both `counts` modes, token level, old vs new): 1,559 token diffs, 59 files with different held sizes; every one is K-a (`USD`/`EUR` glued to digits, 502 tokens new in each mode: `USD710 million`, `EUR1,000m`, `USD35/share`, all real money; the old reading kept only the fragment `000` of `USD1,000m`, 270 and 265 fragments gone) or K-c (`EUR 2029s, 480bp`, 10 tokens gone, held 2029 lost). K-b (a year-shaped number with a C2 form) 0 tokens, K-d (`mln`/`bln` after a small number) 0 tokens. `gaps_real_run.py` output byte-identical before and after; every other probe exits as on main (three recorded limits unchanged).
Not verified: a real model; `30 C$m` (a small number after a one-letter-prefixed sign is still no unit); a code standing alone before digits that is really a name (`COP26`: 26 is read as a figure; none in the corpus).

## 2026-11-12 — Bracketed note narrowed: a ratio or a rounding of the figure before it (branch `claude/prose-number-reading`, fix round 1; replaces rule 2 of the entry below)
Scope: offline, `prose_checks.py` `_figures` only. Review of the entry below showed real negatives read as positive (`FY2024 (120)`, `Q2 (26,306)`, `D02 (22)/(48)`, `Note 5 (120)`, `Capital expenditures (42) (36)`, `2,200 (20) 2,180`, and `Net debt was 100 (25).` on the passage side). Rule now: a bracketed figure is a note only if it directly follows a real unbracketed figure (not a label, date, year or reference number) and carries `%` or `x` or is a rounding of that figure; otherwise it is a negative as on origin/main. Known limit: `40% (364)` stays a negative; `100 (100)` reads as a rounding.
Tests: 36 new parametrised cases in `tests/test_prose_checks.py` (every reviewer form negative on both sides; ratio, rounding and edge cases as notes); 24 of them failed before the change; no earlier test changed. Real evidence (read-only, same 741 files): 21 removed (the same 21 as before), 0 added, 79 unchanged; of 936 bracketed-after-figure occurrences in 246 contexts, 210 contexts are notes (187 `%`/`x`, 23 roundings) and 36 are negatives (4 after a bracketed figure, 9 date/period label, 14 glued to letters, 1 year, 8 neither ratio nor rounding); CP-L10 Key figures 0 before and after. Probes `nr_label_bracket_negative.py` and `nr_comparative_negatives.py` exit 0; `probe_pr46.py` D1 and D2 pass.
Not verified: a paid run; a note of a different quantity (`40% (364)`) or a ratio-looking negative (`5.0% (2.1%)`) on a real case.
Round 2 (same branch): a figure is real only if not glued (`Sep-24`, `FY-24`, `A1`), not after a period word, and an amount (unit, decimal, separator or 100+); a rounding needs fewer decimals, or the same number with separators added (`9432.72 (9,432.72)`); the rounding runs in a sized Decimal context (no overflow). Tests: 23 new cases failed before, 322 pass; the branch-added `100 (100)` note case now a negative, the `<= 1` check rewritten to assert one exact refusal per case.
Round 2 real evidence (same 741 files): 21 removed (the same 21), 0 added, 79 unchanged; of 246 contexts 187 ratio, 23 rounding (all still notes), 36 negatives; no note became a negative; CP-L10 Key figures 0 before and after.
Round 3 (same branch, Low findings): the three look-behind searches in note detection read a bounded tail (40 characters) instead of the whole text before the figure (linear again); an unsigned bracket after a negative figure is a negative, not a rounding note. Tests: 3 new cases failed before; real evidence on the same 741 files identical to round 2.

## 2026-11-12 — Fidelity check reads figures with a thousands separator and a bracketed note (branch `claude/prose-number-reading`, ruling amendment 2026-11-12 in `2026-11-11-reader-and-issuer-report.md`)
Scope: offline, `prose_checks.py` only (`figure_issues`, `key_figures_issues`); no provider or model call. Two defects that refused correct handoffs: (D1, D-KF) `4,173` and `4173` were different numbers; (D2) `3,395 (51.6%)` held `(51.6%)` as a negative, so the passage's `51.6%` was refused with advice to write the negative.
Change: a figure's digits are compared without thousands separators; a parenthesised figure right after another figure (and its unit) is read as written, not as a negative. Alone or after words it stays negative. Passage and held sides share `_figures`, so both get both rules. Tests: new cases in `tests/test_prose_checks.py` (both comma directions, `1,291.27`, `1,25`, `2024, 437`, unit/scale/sign/decimal mismatches still refused, the three real cells, the three true negatives, `100 (-5.2%)`, Key figures); 11 of them failed before the change; the file's 253 tests passed after.
Real evidence (read-only, 741 retained `.md` files: 222 drafts, 200 responses, 319 handoffs; old = origin/main module, new = this branch, `figure_issues` as the launcher calls it): 21 issues removed (7 thousands separator, 14 bracketed note), 0 added, 79 unchanged. `key_figures_issues` on the 3 retained CP-L10 texts with their CP-1: 0 before and after (the refused CP-L10 drafts of `tdg-proof-short-001` are not retained as files; the old refusal text is in its `1.review.json`).
Probes: `probe_pr46.py` D1 and D2 pass, D3 (check 6, a different defect, not changed) still fails; `probe_key_figures_comma.py` exit 0.
Not verified: a paid run (whether a model now passes at the first draft); Key figures against a real refused CP-L10 draft. (The adjacency rule above was too wide, see the next entry: real negatives directly after a figure, `Q2 (26,306)`, `Capital expenditures (42) (36)`, exist in the retained runs.)

## 2026-11-12 — Module output review changes: sources resolve, each drawing shown once, reader vocabulary checked everywhere (branch `claude/modules-page-sources-charts`, ruling `2026-11-12-module-output-review-changes.md`)
Scope: offline only. No provider or model call was made. Decisions 7 to 11 (launcher text, checker, confidence score, post-balance-sheet table) are proven by tests and hand-written handoffs only, not by a model run. Display changes were checked on a copy of the retained real run `tdg-proof-snapshot-opus-002` (TDG, as of 2024-09-30, credit snapshot): one run, 1440 px, headless Chrome.
Library:
- A chart, map or timeline is shown once, as a drawing with a "Table form" fold; a drawing with no numbers gets a "Not established for this run" card (decision 1).
- Request, Next module and front matter sit in an "Evidence & audit" fold; the front-matter `filename` line is not drawn (decision 2).
- Figures, Basis links, table rows and `Source` cells open the inspector on the file and page; "Row" replaces "Handoff"; "unresolved citations" replaces "citations without a page" (decision 3).
- Register ids lose their module code; no heading says "a method step"; a negative amount is one figure; a fenced block is drawn as a block; wide tables scroll from the keyboard (decisions 4, 5).
- Drawings: bridge labels wrap, the debt stack has a ranking and security legend, the timeline has year ticks, an as-of line and a numbered key, map text wraps on words (decision 6).
Method and checks (new runs only):
- Reader vocabulary is checked in Findings, Calculations and Gaps; new check 10 refuses pipeline wording; the bottom line is at most 45 words in the first sentence and 180 in all (decisions 7, 8).
- Modules state no confidence score, band or QA status and mention no helper scripts; a `### Confidence inputs` table is written and Python computes the score by the method's formula (decision 9).
- Financial foundation writes `### Post-balance-sheet adjustments`; `## Sources` names file, description and date; modules use plain module names; chart tables carry one qualification sentence; map text is at most 60 characters (decisions 10, 11).
Fidelity check (13 module pages of the run, before the branch vs after; every number token; three handoffs against their pages): no number, period, unit or source file name lost unexplained. One loss class was found: the "Not established" card dropped a stating row's other cells on Legal & covenants and Committee decision. Fixed in 188cb5f; re-checked: 8 of 8 statements back on the page. The compare script is `compare.py` in the session scratchpad (not in the repo).
Reader check against the September VMO2 reference: Financial foundation, Business & governance, Fundamental credit. Verdict: pass with issues. Open issues (display or wording, none loses content):
- Business & governance timeline: 8 of 11 events stacked at the right edge, markers on the as-of line.
- Map labels at crossings and arrowheads are ambiguous (the edge table is unambiguous).
- Bar labels are raw ("6585", "7940"); "1 unresolved citation" repeats six times on Debt maturities; the Sources table spends a column on sha256.
- Figure buttons that open a file and page: 29 of 29, 42 of 42, 0 of 65 (Fundamental credit cites upstream modules only). Basis buttons that open a file and page: 62 of 111, 58 of 78, 0 of 58.
Real-run numbers (they measure different things; each is from its own step):
- Task A2 (chips): `issuer_page` chips 0 to 580 on the run. Whole-branch review, three retained runs: 116, 501 and 494 gap chips became page chips (1,111 in all), 0 regressions.
- Task A3: "a method step" on the run 375 to 4 (4 left in CP-5 table cells, the no-title fallback). Task A4: sign-outside-figure 8 to 0.
Gates at a816851 (all exit 0): node tests 363 passed; `uv run python tools/quality_gate.py --base a873f6f` 0 findings, 3165 lines in scope; PR-check pytest 3435 passed, 122 deselected; browser tests 83 passed, 1 skipped (a screenshot helper). Two one-line residual fixes followed (earlier-format map fold guard; "or cash" restored); gates re-run at the final code commit 02a06f6, all exit 0: node tests 364 passed; quality gate 0 findings, 3177 lines in scope; PR-check pytest 3435 passed; browser tests 83 passed, 1 skipped.
Not verified: a paid run (whether a model obeys the new text; the refused-draft rate under the tighter checks); other runs and widths; earlier-format pages on a real run with maps; screen readers; the weekly slow suite.
For the owner:
- Bottom-line limits 45 and 180 words are the controller's values; 11 of 13 real bottom lines on the run exceed 180 words (184 to 286). Keep, raise or drop.
- Check 10 refuses some ordinary wording ("canonical basis", "the pack mix", "upstream module prices"); narrow the list or accept retries.
- The 60-character map limit as worded also shortens Relationship and Evidence, which are not drawn.
- Decision 10 gaps: no pro forma cash column; cumulative rows with two events; the Amount sign convention chosen (4348 and -4348 are both accepted); the table is drawn only on Financial foundation.
- PR size is 3,524 changed lines (whole-branch review) against the 800-line convention: one PR or split by commit range.
- Longer shared text raised the per-call hold (opus-medium largest call 2.98 to 3.02 USD); an opus-medium run with `--cap 3` now refuses offline; the cap test moved 3 to 3.5.
- The confidence score rests on the module's own stated inputs; nothing checks them. A score, band or QA status stated in front matter is refused; one stated in body text is not.
- The bottom line is set in headline type (recorded redesign decision); labels at crossings stay ambiguous; "unnamed module" is shown for a code with no display name; the paid run that proves decisions 7 to 11 is not made.

## 2026-11-12 — Run start in four steps (branch `claude/redesign-run-start`)
Plan and reports: `.superpowers/sdd/2026-11-12-redesign-run-start/`; record: `docs/design/2026-11-12-run-start-four-steps.md`.
Scope: the page `docs/templates/context-form.html` only, tested by synthetic browser tests against a stubbed service. No provider run; no real run started.
Changed: the eight sections stay as groups under five steps (Documents, Purpose, Confirm, More context, Start); documents first; a numbered stepper, fixed footer, readiness column, the Start card "What Submit does", and the run screen in the redesign's look. `build()`, `context.json`, the requests and the service are unchanged; the answer-key tests were not edited. Controller rulings 1-11 are in the record.
Checks: `tests/test_context_form.py` and `tests/test_run_start_page.py` 180 passed, exit 0 (Task 1: 147 then 148; Task 2: 159; Task 3: 169 then 172); three library-page browser tests that load the form passed (the `-k context` filter selects none); quality gate 0 findings, exit 0. Reviewer probes: Task 1 re-review 5 passed, Task 2 14 passed, Task 3 re-review 8 passed. On a 12-module summary Submit first comes into view after 12.5-21.1% of the scroll, and after 69.2-77.1% on the short snapshot; a focused Approve or Submit is always visible.
Reviews (mx-precise): Task 1 changes required (M1 More context dropped off screen when its last held answer was undone; M2 group-level assertions deleted; L1 a legal-error test on an unreachable state), closed in fix a6eec82, re-review approve. Task 2 approve, with three Lows carried to Task 3 and closed there. Task 3 changes required (M1 the sticky card hid Approve and Submit; M2 the run screens lost the title and Start over), closed in fix a4408ff (Rulings 10 and 11), re-review approve; its Lows L1-L3 were fixed in the same round.
Reader check: not applicable to this form. The VMO2 reference check covers the issuer report; the look here was read against the mock-up notes only, with three desktop screenshots by eye in Task 2.
Open, for the owner: the 960px JavaScript/CSS breakpoint both match; the files table keeps a 560px minimum width below 720px; the mock-up's library empty state (R0) is not built.
Whole-branch review: by a separate reviewer; found two Medium defects (a button opening a later group of a step left its heading off screen; the Start module rows collapsed at 375px) and seven Low; fixed in this commit; re-review of the whole-branch fix (4ab364d) by a separate reviewer: approve; every button target lands in view at 1440 and 720px; payload and Submit rules unchanged; reviewer probes `probes/wbr` and `probes/t3r` pass apart from one probe that pinned the README's old short-snapshot sentence, corrected in this commit.
Not verified: look beyond three desktop screenshots (none of Start or the run screen; no pixel comparison with the mock-up); widths 720-960px, print, forced-colors; 375px by a scroll-width probe only; keyboard traversal and screen readers; the run screen driven with literal run data, not a real run; groups kept on More context after a level change until the step is left; real-service submit beyond the existing browser tests; real Tab traversal, screen readers and forced-colors; browsers other than headless Chrome; a real run or provider call (the service was stubbed throughout); `?from=` beyond one credit-snapshot fixture run.

## 2026-11-12 — Forecast inputs name cells of period-row tables; `LTM Qn YYYY` is a balance date (branch `claude/forecast-reader-findings`; findings 1, 2, 6 and the instruction side of 4 of the LTH reader check)
Plan: `docs/superpowers/plans/2026-11-12-forecast-reader-findings.md`, Tasks E1-E4, rulings R1-R6. An operand may name its cell in a table with one row per period as `row` (the period) and `column` (the measure's header); `column` with `period` is refused and partial naming stays refused. The history record reads such tables, and reads a label `LTM Qn YYYY` (row label or column header) as the balance at that label's End for debt, cash and undrawn only, and only when CP-1's period table dates the label to the day the year to date (or the fiscal year) ends; it is never read for a flow. A period row whose `Reporting unit` differs from the named row's is n.a. with the reason, never converted. The limit that listed the LTM header as unread now says what is and is not read. Instructions: the `column` form, `interest` defined as cash interest (interest expense may be named if `scope_limits` says so), balances printed as plain numbers under their period, the LTM label dated in the period table; repair lines name `column`. A block that uses no new key publishes byte-identical files, except the one limit line where CP-1 carries an LTM label.
Scope: offline. Synthetic fixture with a hand answer key (plan lines 43-87); 459 recorded calls replayed before and after (429 identical, 24 differ only where CP-1 holds an LTM label, 6 only in two refusal texts); the real LTH CP-1 of run `20261112-164724-01` read with a HAND-NAMED block (no model ran): FY2024 cash 10.879 and net debt 1,544.718; YTD and LTM cash 175.509, debt 1,534.356, net debt 1,358.847; LTM leverage equals CP-1's own C3 and C4; with the run's block unchanged only one limit line differs. No provider called: no model has yet used `column`.
Commands: pytest (cpos launch, facilities, periods, scale, store, handoff loop) exit 0; quality gate 0 findings, exit 0. Reviews: task reviews (mx-precise), two adversarial reviews (mx-adversary: no flow leaked, no balance in a column ending another day; one Medium on mixed units, fixed), whole-branch review with confidence review and rewrite tournament (mx-architect), two fix waves. Hand-picked mutants 34/40 killed, then the four untested ones (M03, M06, M19, M35) killed by new tests; M10 and M11 survive singly.
Known, for the owner: an operand with no base amount cannot name a history-only cell, so LTH's June 2025 undrawn 618.5 and LTM liquidity stay n.a. (R3); the delivered LTH run does not change, cash and debt balances appear only when a model names them by `column` or CP-1 prints plain balances (`1,534.356 at 2025-06-30` is not read); a scale-1000 issuer cannot name the US$m chart tables; nothing checks that a stock is named at the base period (R6); two tables that state one balance in different units and disagree publish the same-unit figure unflagged (CP-1's validation refuses such a handoff); a currency difference between rows is not detected; re-delivering a run whose CP-1 has an LTM label gives a new delivery id; the branch is about 1,400 changed lines against the 800-line limit.
Not verified: any model response to the new instructions; a paid run; the Forecast page's rendering of the new reasons and limits; the layer-1 `column` path through a delivery; the weekly and live suites; mutation testing beyond the hand-picked mutants. Moved to the archive to keep this file under 1,000 lines: the 2026-11-10 Library and report screens entry.

## 2026-11-12 — Forecast page: neutral labels and notes, lines with no figure folded, readable model picker (branch `claude/forecast-reader-findings-page`; findings 3, 4, 5, 7 of the LTH reader check)
Plan: `docs/superpowers/plans/2026-11-12-forecast-reader-findings.md`, Tasks P1-P3. On a delivery with a history record the rows read `Adj EBITDA (as named in Financial foundation)`, `LTM Adj EBITDA`, `Closing debt`, `Interest`, `Interest coverage (Adj EBITDA / interest)`, and the notes that named EBITDA As Defined, securitization and refinancing costs are replaced by three issuer-neutral notes. A line with no figure in any column of any case moves, with its cells and reasons, into a closed list `Lines with no figure in this run (N)`; the seven column groups stay. The model picker reads `<run date> · <pathway> · <run id>`, not the delivery hash; a recorded predecessor is named by its label. Controller correction to the plan's wording: the interest note ends at "rather than cash paid" (the plan's second clause was false when facilities are stated).
Scope: offline; presentation only. Store and node tests with hand-named expectations; the base commit's grid compared with the tip's cell for cell on six inputs, the real LTH delivery included (equal apart from the new `empty` flag); every table row of the real page byte-identical to before, in the main table or the fold; `Why cells show n.a.` unchanged (117 lines).
Reader check, scope: ONE real run (`20261112-164724-01`, LTH, Sonnet by a reverted local patch) rebuilt from a copy of its run root with this branch and read in Chrome at 1440 px by the controller, and in headless Chrome by the reviewer's probe: picker `18 August 2025 · Credit snapshot · 20261112-164724-01`; 17 of 34 lines folded, each with no figure anywhere; main grid shows Revenue, Adjusted EBITDA, Earnings to cash proxy, Cash and liquidity (Distributions, Debt repayment), Debt and Credit metrics; no note carries another issuer's wording. Against the September VMO2 reference: the same three screenshots as the entry below (none shows a forecast grid); the reference writes a gap in words in the cell, this page keeps `n.a.` with the reason in a tooltip and the closed list. Not read: the other 57 screenshots.
Commands: pytest (seven store and library files) 472 passed, exit 0; node 4 files, exit 0; browser `-k "forecast or cashflow or model"` 5 passed, 1 skipped, exit 0; quality gate 0 findings, exit 0. Reviews: task review (mx-precise), whole-branch review with confidence review and rewrite tournament (mx-architect), one fix wave.
Known, for the owner: lines fold on older HTML-Model deliveries too once their library is rebuilt (two lines on the retained TDG delivery, both empty in every column); on the LTH run Closing cash, Accessible liquidity, Net debt and Net leverage are in the fold because that run's model did not name cash; folded lines do not print unless the fold is open; the other-case table still lists every line; the Profitability rows keep the first issuer's captions (they are always folded on a run with a history record; predates this change); the run's own text still says "opus-medium".
Not verified: a real HTML-Model delivery in a browser; two deliveries or a predecessor in a real library; keyboard and screen-reader use beyond markup; widths other than 1440 px; a new paid run.

## 2026-11-12 — CP-8 checker: a year with a unit is a figure, counts beside a count noun, a spelled size across lines (branch `claude/cp8-checker-counts`, owner "fix 1 and 2")
Scope: offline, synthetic plus read-only reading of retained runs; no provider. R1 years, R2 counts, R3 line breaks as in the amendment at the end of the presets ruling. Tests first: 19 of the new cases failed on the unchanged checker, all pass after; the one old case that pinned the count limit now asserts acceptance. `gaps_real_run.py` on `tdg-proof-snapshot-opus-002` is byte-identical before and after. The figure reading over 37 held CP-1/CP-2 handoffs of the preview workspace reads 6 year-shaped tokens as figures, all in two contexts that are real figures (`USD 1913 million`, `FY2024 USD 2045 million`); a first version read `AND 2023` as a currency, fixed by a currency-code list.
Fix round 2 (M-A plural/`mn` scale after a year, `US$ million`; L-A1 ISO exemption stops mid-number; L-B separator needs three dashes in every cell, 0 of 10,319 real separator rows in 974 retained files had fewer): figure readings over those files differ only where a year range's second year or an ISO-shaped digit run is no longer cut (e.g. `2025-2045`), listed in the amendment.
Fix round 3 (a year with a unit: one `_YEAR_UNIT` test with explicit word ends, separate from the small-number `_UNITED`; duplicate `_UNITS` removed, `mypy --strict` errors in the file 9 to 0; `2010 millions` moved from figure to year): 25 new cases failed first; corpus counts and held sizes identical to 404fb77.
Not verified: a real model; the reader view (no presentation change); bare years (always years); counts of 100 or more beside a noun (raw reading).

## 2026-11-12 — Reader check of the Forecast page on a real run (LTH, run `20261112-164724-01`; closes the check left pending for PRs 59, 60, 63, 70, 71)
Scope: ONE live run started from the run start page by the controller on the owner's instruction ("you do it", "Yes, submit"): Life Time Group Holdings, Credit Snapshot, Advanced, modules CP-0, CP-1, CP-2A, CP-2G only, as-of 2025-08-18, current period fy-2024, no legal documents declared, five retained LTH files (10-K 2024, 10-Q June 2025, three credit amendments). Model: `claude-sonnet-5-5` (requested and reported on all 51 model-call records), by a temporary uncommitted local patch of the `opus-medium`/`opus-high` configurations made on the owner's instruction ("use sonnet just for this test") and reverted after the run; the run's own text says "opus-medium", which is wrong for this run. Spend recorded USD 3.71 at Opus rates (an overstatement; Sonnet is cheaper), cap USD 20. One retained response per module; the live record holds up to three drafts for some modules, not examined. Run root `~/rbot-run-root`, outside the repository. This is one issuer on a model the service does not offer; it is not a GPT Sol or Claude Opus result and not a complete Credit Snapshot.
What the model did: the CP-2G block states `scale` 1 and names the row and period of all five base operands it gives (revenue, EBITDA, interest, free cash flow, debt; e.g. "Total revenue, USD million" / FY2024); every one passed the cell check. CP-1 itself restated the filings' thousands in US$ million, so the block is correctly at scale 1 and the scale-1000 path was NOT exercised. Five base operands were declined as missing with a reason (taxes, working capital, capex, cash, undrawn revolver).
Forecast page read in Chrome at 1526 px against the delivery's `forecast_exact.json` and `calculation.json` and CP-1: caption "USD millions"; seven groups in the owner's order; history filled from the named rows for YTD H1 2025, PYTD H1 2024, FY2024 and LTM Q2 2025 (revenue 1,468 / 1,264 / 2,621 / 2,824; Adj EBITDA 403 / 320 / 677 / 760; interest 47 / 75 / 148 / 120; coverage), FY2024 closing debt 1,556 and total leverage 2.30x; values equal the record and CP-1's printed cells (spot check of those rows, not every cell); base and downside FY2025E to FY2027E computed; YTD growth 16.06% shown, growth across unequal periods withheld; the downside note is present.
Read against the September VMO2 reference: three of the screenshots only (Evidence Trace registers, T4.5 to T4.8, T2.11 to T2.12); none of the three shows a forecast grid, so the comparison is of table voice, not layout. The reference states the unit and period in the cell and writes a gap in words ("Not Calculable from Provided Materials") with a Source / Limitation column; this page states the unit once in the caption and shows "n.a." with the reason in a tooltip and a closed list of 117 lines.
Found, for the owner (none fixed here): (1) Cash, liquidity, net debt and net leverage are n.a. in every column although CP-1 prints FY2024 cash 10.879 and June 2025 cash 175.509 and undrawn 618.5: those CP-1 tables have one row per period and a measure as column header, which the cell check cannot name (the limit recorded for the gross-debt table). (2) LTM closing debt is n.a. for the same reason (CP-1 prints 1,534.356). (3) The Quarter, Prior LTM and Pro forma columns are wholly n.a.; with the Profitability block (n.a./n.m. throughout) about half the grid is empty. (4) The row "Cash interest" shows CP-1's net interest expense, which CP-1 says is not cash interest. (5) Three footnotes are another issuer's wording: "EBITDA As Defined", "refinancing costs", "securitization" (`store.py` near line 1369); LTH has none of these. (6) The limitations list says "column headers not read as periods: LTM Q2 2025" while the LTM column is filled. (7) The model picker shows a 64-character hash and "relationship not recorded".
Not verified: GPT Sol or Claude Opus on the new instructions; a block at `scale` 1000; a refusal and its repair line on a real answer; the other 57 reference screenshots; every grid cell against the record; Overview, Changes, Modules and Evidence pages of this run; any other issuer. Moved to the archive to keep this file under 1,000 lines: the 2026-11-10 Forecast tab entry (run tdg-forecast-005).

## 2026-11-12 — Two CP-8 checker gaps closed (branch `claude/cp8-checker-gaps`, owner "Yes, fix both")
Scope: offline, synthetic; no provider. (A) K9 refuses a withheld difference written without a unit (`Cash fell by 30.`), in passages, `## Gaps`, Why and ledger cells; same exemptions; K10 counts unchanged. (B) `Same definition` / `Not comparable` are read from the start of the Effect cell only (`_says`), checker and `page_verdicts` alike; the words starting another cell are refused naming it; a pack `no` measure still accepts `Not comparable` in any cell. Tests first (26 failed before); five seam fixture cases added, none changed. Probes whycell_unitless, whycell_probe, ndsame_why, ndsame_k9, netdebt2_attacks, realfix_check, seam3_verdicts exit 0.
Fix round 1 (reviewer findings): a line-start number is a list marker only on a line that really begins a list item (first line, or after a blank line, heading or list item), never in a table cell; K10 and the unit-bearing K9 reading read the line as before, so a wrapped `110.` / `437.` is refused again. A day beside a month name (`30 September 2024`) is no size for the bare-number K9 reading; `September 30, 2024` still refused (predates the branch: `_FIGURE` reads `30,`). The verdict words doubled in another cell and the Effect cell are refused. Ten new test cases failed first; probes gaps_linestart, gaps_dates (one case still fails, as noted), gaps_misplaced_with_effect run.
Not verified: a real model; a bare count equal to a withheld size is refused and a size in words is not read (recorded in the presets ruling).
Limits fixed (owner "Fix the limits first", L1-L4): a number after a bullet line is a marker only if `1`; a day beside a month is a date only with a four-digit year, and a complete date is blanked before both readings; whole numbers in English words (2 to 999,999) are read in the bare K9 reading. 22 new test cases failed on the unchanged checker; two tests that pinned the old limits now assert the rulings.
Not verified (limits): decimals, fractions, ordinals, `a hundred`, `a dozen` in words; a real model.
Fix round 2: a year is 19xx/20xx only (a figure after a yearless date is read again); a decimal, fraction or ordinal in words is not read in part; U+2010-U+2015 hyphens join a spelled number. 20 new test cases failed first; probes gaps3_year_not_year, gaps3_words_limits (line-break case remains) run.
Fix round 3 (H1 year before a comma, M1 ISO dates, M2 `change`/`difference` not count nouns, L1 count noun on the next line, L2 delimiter without pipes, L3 code after a year): new cases failed first, all pass. Over 974 retained `.md` files vs `5db96a9`: 0 year-comma tokens and 0 ISO-date parts read, 39 newly read year-shaped tokens all with a currency or unit (`US$1913 million`, `FY2024 USD 2045 million`), no non-year figure lost.

## 2026-11-12 — A withheld difference is refused in the analysis register's Why and the ledger (branch `claude/cp8-why-cell-withheld`, owner "fine, PR and merge")
Scope: offline, synthetic; no provider. K9's register exemption narrowed to the Effect cell of the measure's own issuer row (`Same definition` with `Correction` or `Method change`); the analysis Why, ledger, fact rows and other measures' rows refuse a withheld size (pack `no`, said `Not comparable`, same-period flagged, same-period net debt change incl. cash), as before in passages. Same functions, per-line exemption. 295 tests in `tests/test_changes.py` pass, none changed or weakened; 9 new cases failed on the old code first. CI fast-tests: exit 0, 3000 passed; node set: exit 0, 298 passed; `tools/quality_gate.py`: exit 0, 0 findings; reviewer probes ndsame_why, ndsame_k9, ndsame_flag, netdebt2_attacks, seam3_verdicts, realfix_check (real accepted-then-corrected handoff), t4r4_same_period: all exit 0.
Not verified: a real model writing a Why cell; a collision of a withheld size with another measure's stated value is still refused (as in passages).

## 2026-11-12 — Forecast inputs in thousands: `scale` 1000 (branch `claude/forecast-units-scale-b`, PR B, stacked on PR A)
Plan: `docs/superpowers/plans/2026-11-12-forecast-named-rows-and-units.md`, Tasks B1-B6. A forecast inputs block may state `scale` 1000: it then states base amounts, amount drivers and facility balances exactly as CP-1 prints them in USD thousands, and Python divides by 1000 exactly before any check or calculation. The cell and printed checks compare the stated text with CP-1; the history record reads the named rows and publishes the same unit; the published record carries `scale` and `units` and the library's caption uses them. A named row whose own cells or headers name the other unit is refused, and a scale-1000 CP-2G block must name its rows. Both instruction texts ask for `scale`. A block without `scale` produces byte-identical files.
Scope: offline. Synthetic fixtures with hand-computed answer keys (`tests/test_cpos_scale.py`); a millions fixture and the same fixture times 1000 at scale 1000 publish identical figures in every file, facilities and cases included (also on 800 generated fixtures, reviewer's probe); the store's grid compared with a hand key on 1,768 cells, 0 differences; two retained thousands handoffs (LTH, IHRT) read with hand-written named blocks and synthetic drivers: every base and fiscal-year history value equals the printed cell divided by 1000; the unit rule run over the numeric rows of the six retained CP-1 handoffs refuses 11 rows, all printed in millions inside thousands handoffs. No provider called: no model has stated `scale`.
Reader check: NOT done on a real run; pending the owner's paid run on a thousands issuer. On synthetic data the grid of a thousands block equals the millions grid cell for cell and the caption reads USD millions.
Commands: PR-check pytest list 3097 passed, 113 deselected, 1 warning, exit 0; quality gate against PR A 0 findings, exit 0; node 278 pass, exit 0. Reviews: task reviews (mx-precise), adversarial review (mx-adversary: no arithmetic defect), whole-branch review with confidence review and rewrite tournament (mx-architect), one fix wave. Hand-picked mutants 85/100 killed; survivors left: T07, C02, C03, F03, U03, U08, U09, U10, U11, U12, U15, K08, R01, R04, G03.
Known, for the owner: nothing detects a missing or wrong `scale` (six-digit thousands without it read as millions; a millions handoff at scale 1000 publishes figures a thousand times too small); the unit check reads only named operands and only unit words in the row, the named column's header and the table's first header cell, so a millions cell with no unit words nearby, a facility balance or an amount driver in the other unit is not caught; revolver availability is printed in millions on all four retained thousands issuers, so Liquidity is n.a. there until an operand-level scale is decided; a delivery without the history record reads CP-1 as printed under the record's caption (new runs always ask for the record); the PR is about 1345 changed lines against the 800-line limit, waived by the owner on 2026-11-12 (split B-i/B-ii exists).
Not verified: any model response to the instructions; the Forecast page in a browser; a paid thousands run; non-USD issuers; the weekly and live suites; mutation testing beyond the hand-picked mutants.

## 2026-11-12 — CP-2G names its rows; history from named rows only (branch `claude/forecast-units-scale`, PR A)
Plan: `docs/superpowers/plans/2026-11-12-forecast-named-rows-and-units.md`, Tasks A1-A4. A CP-2G forecast inputs block may name, for each base operand with an amount, the CP-1 table row and period column it was read from; a named amount must be that one cell under the sign rule, and the instruction asks for the names. The history record is built from named rows only: the code that located a line by its amount is deleted, which removes the wrong-row residual recorded for PR 1. A block that names nothing still forecasts as before and gets no history (every line: the inputs do not name the row and period). A refused base operand may be restated as missing instead of nulling every driver.
Scope: offline. Synthetic fixtures with hand-computed answer keys; the reviewer's residual probe before the change (exit 1) and after (n.a. with the header named); 1,500 and 4,500 generated CP-1 handoffs compared with the code before the change (unnamed CP-2G blocks byte-identical with the history flag off; layer-1 blocks identical); retained CP-1 handoffs (the live TDG forecast run, web TDG, NATL) read with hand-named blocks and synthetic drivers, which prove the cell check and the history on real tables, not a model's ability to name rows. No retained delivery holds model files, so byte-identical re-derivation rests on the synthetic pin and the generated comparison. No provider called: no CP-2G has yet named a row.
Commands: PR-check pytest list 2969 passed, 113 deselected, 1 warning, exit 0; quality gate against main 0 findings, exit 0; node 278 pass, exit 0. Reviews: task reviews (mx-precise), adversarial review (mx-adversary: no High or Medium; 12,000 generated cases raise nothing and every shown value is a cell of the named row), whole-branch review with confidence review and rewrite tournament (mx-architect), one fix wave. Hand-picked mutants 34/40 killed; survivors M20, K04, K06, K08, K10, K18, on lines that predate this branch.
Known, for the owner: a block that names nothing shows seven history columns of n.a. with the naming reason; names are not tied to one table, so a same-label row in another table that prints the base amount under the same period adds its periods; the repair wording for a schema refusal of a base operand still offers nulling every driver; a delivery made with the history flag from an unnamed CP-2G block before this change would not re-derive byte for byte (none is retained); the PR is about 1086 changed lines against the 800-line limit, waived by the owner on 2026-11-12 (a clean split exists at the instruction commit).
Not verified: any model response to the new instruction or repair line; the Forecast page in a browser for this change; the weekly and live suites; mutation testing beyond the hand-picked mutants.

## 2026-11-12 — A same-period net debt difference is the analysis's, not the issuer's (branch `claude/net-debt-same-period`, owner "Yes, fix it")
Scope: offline, synthetic. Pack: `net_debt_change` gains `same_period` and the two rows' periods, gross debt and cash (schema stays `/3`, additive). Checker: the cash difference is passed through K9's functions as a measure-shaped record, so a same-period change's gross debt, cash and net debt sizes are refused in checked lines while both values may be stated. Tab: flagged and non-zero shows both runs' balances, periods and the sentence, no change figure; zero or two periods unchanged; a pack without the flag as before; periods now beside the cash movement. Hand-written expectations (7,100 to 6,990 gross, 910 to 880 cash, 6,190 to 6,110 net; 2,100 to 2,000, 300 to 250). Changed expectations: the two exact-dict `net_debt_change` assertions in `tests/test_changes.py` gain the new keys (different periods, `same_period` false). `cp8.md` states the rule.
Not verified: a real model writing a same-period net debt CP-8; the page in a browser against a real pack.

## 2026-11-12 — CP-1 states gross debt in `### Net debt data` so the net debt change can be shown (branch `claude/cp1-gross-debt-row`, base a639fb7, owner "Yes, add it")
Scope: offline, synthetic. A `Gross debt` row cannot sit in an existing chart table (all four are period-row tables); controller ruling: a fifth period-row owner table on CP-1, all seven pathways (`Period | Gross debt | Cash | Net debt | Reporting unit | Basis and limitation`, US$m, not a `Chart data:` heading so the library does not draw it). Checker: net debt = gross debt - cash exactly in Decimal when all three are stated, and, where the liquidity table has a row `same_period` calls the same period (`FY2024` and `FY2024 / 2024-09-30` are; `2024-09-30` and `FY2024` are not), a stated cash equal to that row's Cash. Pack: `gross_debt`, `net_debt` and the table's own Cash (not the liquidity table's) are read from the same latest row of that table, so the net debt change makes no cross-table read; the #66 exact-label row rule now reads only free cash flow. Hand-written expectations in `tests/test_cpos_launch.py` and `tests/test_changes.py` (2,100 - 300 = 1,800; 2,000 - 250 = 1,750). Method: `cp8.md` wording only (CP-1's method is unchanged: the instruction is the launcher's owner-table rule, so no CP-1 method revision); older runs show "methods changed" for CP-8 by hash.
Compatibility: an older run (no table) is still a CP-8 base and renders; its net debt change is left out, `omitted` naming the run.
Knock-on read in code: the library draws only `Chart data:` headings (this table is a reference section); `cpos_forecast` reads cells by row label and period header, so the table's period-labelled rows and measure headers cannot be named as an operand; CP-L10 Key figures only gain held figures; the report strip routes only chart blocks.
Not verified: a real model writing this table; the library page with a real handoff carrying it; the VMO2 reader check (no presentation change was made to a delivered report).

## 2026-11-12 — Redesign pass 1: run header, Modules, inspector and Overview (branch `claude/redesign-modules-overview`, stacked on PR 62)

Scope: offline, macOS, headless Chrome; no provider called. Presentation only, from the Claude Design
redesign: the run header (back link, meta line, "Start a run on this issuer" over http), text-only tabs,
the strip, 250px navigator, the module page (bottom line as headline, findings list, fold rows; charts
stay open), the inspector as cards, and the Overview in two columns. What was built, what was not adopted
and the cross-check against earlier decisions: `docs/design/2026-11-12-redesign-pass-1.md`.
- On 13d258b: `node --test` reader, static, calendar, changes: exit 0, 295 passed. `uv run pytest
  tests/test_library_page_browser.py tests/test_library_changes_browser.py tests/test_model_shell_browser.py
  -m browser -q`: exit 0, 95 passed, 1 skipped (a screenshot helper). `uv run pytest tests/test_context_form.py
  tests/test_run_start_page.py tests/test_library_reader_refs.py tests/test_library_index.py
  tests/test_update_library.py -q`: exit 0, 252 passed. `uv run python tools/quality_gate.py`: exit 0, 0 findings.
- Fidelity: a scratch library built from the four listed TDG runs (all earlier format), every in-app route
  crawled from `file://` before the change (fe3dd7d) and after (13d258b) with folds, audit items and the
  inspector opened; every word on each of 252 routes (710 page and inspector states) compared by count.
  Nothing is missing except the header's "Change run" link and its duplicate run-code chip, removed on
  purpose. The same comparison reported 249 drops before those two were allowed, so it does detect a
  removed string. No module code on those routes (252 routes, 0 hits).
- Reader check, scope: one real run (`cpos-tdg-sol-medium-all-001`) read at 1440 on the Liquidity and
  Financial foundation pages and the Overview, against two of the September VMO2 screenshots. The module
  page reads judgement first (bottom line, confidence and main limitation, findings with creditor impact,
  analysis, limits, registers folded), the reference's order; no source reference sits in a narrative
  sentence. The Overview of this earlier-format run says "No bottom line in this handoff." for every module
  (unchanged by this pass; owner question). Main's Forecast period-columns grid was read under the new
  header at 1280 on its synthetic four-case model only.
- Reviews: three task reviews, a whole-branch review (approve with fixes, Lows only), a review of the fix
  batch (one High: without the start link the "As of" block broke over four lines; fixed and re-reviewed),
  and a re-review of the chart index route (one Medium: it opened the first forecast model, not the chosen
  one; fixed and re-reviewed). Each finding's probe ran before and after.
- Not verified: no real run is new format, so new-format pages and the Overview's lead, key charts and
  nearest dates rest on synthetic fixtures. "Start a run on this issuer" was not clicked through to a
  running start service. Forecast with a published model and the inspector on Changes, Forecast and
  Evidence were not rendered. Safari, Firefox, real browser zoom, print against the previous layout,
  screen readers and Windows not run. The header is 73px taller at 1440×900. This branch is 1,535 changed
  lines of code and tests against the 800-line convention, waived by the owner on 2026-11-12 (PR 67).

## 2026-11-12 — No module code on screen (branch `claude/redesign-review-adaptation-892369`, owner ruling 2026-11-12)

Scope: offline, macOS, headless Chrome; no provider called. Display only: the issuer library and the
run start page name a module and never show its code (`CP-…`). Stored handoffs, routes, `href`s,
download names, saved answers and stored source file names and paths are unchanged. The ruling is the
2026-11-12 amendment in `docs/rulings/2026-11-11-reader-and-issuer-report.md` (it replaces "the code
second" in decision 5).
- `node --test apps/issuer-library/credit_os/web/reader.test.cjs apps/issuer-library/credit_os/web/static.test.cjs apps/issuer-library/credit_os/web/calendar.test.cjs`: exit 0, 266 passed.
- `uv run pytest tests/test_context_form.py tests/test_run_start_page.py tests/test_library_reader_refs.py tests/test_library_index.py -q`: exit 0, 185 passed.
- `uv run pytest tests/test_library_page_browser.py -m browser -q`: exit 0, 41 passed.
- `uv run pytest tests/test_model_shell_browser.py -m browser -q`: exit 0, 7 passed.
- `uv run python tools/quality_gate.py`: exit 0, 0 findings.
- Fidelity: a scratch library built from the four listed TDG runs (all earlier format), every in-app
  route crawled in headless Chrome with folds, audit items and the inspector opened: 248 routes, no
  `CP-…` in text, `title` or `aria-label`, no "Name (Name)". The first crawl found 25 codes in Evidence's
  "Methods changed since this run", which no fixture carried; fixed and tested. A stored source file name
  that holds a `CP-` token is shown as stored (synthetic new-format run, browser test). The Changes tab and the Short Credit Snapshot pathway that
  main added are covered by the same probes (the Changes route is scanned; the run start probe visits `short_snapshot`).
- Reader check, scope: one real run (`cpos-tdg-sol-medium-all-001`) read on Report history, the Modules
  navigator, the Liquidity page with its inspector, and Evidence, for this change only: names stand where
  codes stood and nothing else moved. Not read against the September VMO2 reference for voice; the
  change touches no prose.
- Reviews: task review, whole-branch review, three fix rounds (service refusal text on the run start
  page; "Methods changed"; stored file names), each re-reviewed.
- Not verified: no real run is new format, so new-format pages rest on the synthetic fixture. On a
  new-format page or the Changes tab a dotted token shaped like a step id (`T4.24`) reads "a method step", as
  earlier-format pages have since 2026-11-10 (open, owner's call). Run start states the six-pathway,
  three-level probe does not reach (upload, poll and carried-run messages). The shell's own navigation and
  headings of the standalone HTML file (`src/deploy_vii/assets`) are covered by the new browser test;
  its body content and files already delivered are not. Screen readers and Windows not run.

## 2026-11-12 — First real CP-8 run read, and four defects fixed (branch `claude/changes-real-run-fixes`; ruling `2026-11-12-credit-snapshot-claude-rerun.md` and the amendment in `2026-11-11-module-presets-and-changes.md`)
Scope: live, dated TDG FY2024 public case, candidates not reviewed. `tdg-proof-snapshot-opus-002` on opus-medium: 13 of 13 modules accepted, including CP-4 (64,000 output limit) and CP-8 (one rejected draft), delivered, USD 19.45 charged of a USD 25 cap; total proof-run spend USD 37.07. CP-8 found no issuer change (both runs read the same FY2024 filings) and marked undrawn facilities Not comparable (843 vs 1006 US$m: securitization availability added); the library Changes tab rendered it. Reading it found D1 (Basis lines cited `changes.json` and `prior/CP-1.md, page 4`), D2 (unchanged measures carried the cause `Unresolved`), D3 (the tab said gross debt is not stated although both CP-1s state it) and D4 (new modules were `Unresolved`); each fixed with a failing test first (D3 by saying what the comparison reads, not by fuzzy matching; no CP-1 layout change). Offline checks, not live: the real accepted CP-8 handoff through the new checker, with the pack rebuilt from the real handoffs (measures, modules, limitations and maturity profile equal to the real pack's; `omitted`, `schema` and `selection` differ by design) and the selections as recorded (`tdg-reader-format-001`'s manifest has no `selection` key, so null; the current run `preset`): 6 refusals (4 D2, 2 D1) with the first version of D4, 14 (4 D2, 8 D4, 2 D1) once a prior with no recorded selection counts as a preset run (a prior accepted as a base only for its lead module is a whole-pathway run); CI fast tests command exit 0 (2937 passed; node 278 passed); `quality_gate.py` exit 0. Probes `seam3_verdicts.py`, `seam3_page.cjs`, `t4r4_same_period.py` exit 0; `t4r4_sentences.py` exits 1 and `t4r4_fact_row_leak.py` passes only vacuously, both because the probe's Cash and Undrawn rows (zero difference) say `Unresolved`, which D2 now refuses; copies with `None` there exit 0 (62 ok; 7 refused, each for its own reason).
Not proven: CP-DR web guidance on Claude; CP-8 on a pair where the issuer changed; the VMO2 reader check; the D1, D2 and D4 fixes on a new live CP-8 draft (the model may still write other forms); gross debt, net debt and free cash flow still unread from the two real CP-1 layouts.

## 2026-11-12 — Proof runs on Claude and OpenAI, and the Anthropic output limit (branch `claude/anthropic-output-limit`; rulings `2026-11-12-module-changes-proof-runs*.md`)
Scope: live, dated TDG FY2024 public case, candidates not reviewed. OpenAI sol-medium: three runs stopped at CP-1 with "You have no credits remaining"; USD 1.39 spent; nothing proven. Claude opus-medium: `tdg-proof-short-opus-001` (short_snapshot) CP-0, CP-1, CP-L10 accepted and delivered, USD 1.95, CP-L10 accepted on its first draft with a ten-row Key figures table; `tdg-proof-portfolio-opus-001` (portfolio_decision) CP-0, CP-1, CP-1A, CP-DR, CP-2, CP-2E accepted, stopped on its USD 10 cap in CP-3, USD 7.82, CP-1's layer-1 forecast inputs block accepted by `cpos_forecast.parse(..., "CP-1")`; `tdg-proof-snapshot-opus-001` (credit_snapshot with CP-8 against tdg-reader-format-001) CP-0, CP-1, CP-1A, CP-DR accepted, stopped in CP-4 at the output limit, USD 6.46. Opus cost about USD 1.3-1.6 a module.
Defect: CP-4 call 19 ended `max_tokens` at 32,000 output tokens (7,431 thinking) inside `write_handoff`, so the call was lost (`StreamCut`, run stopped). Anthropic spends thinking out of the output limit. Fix: `cpos_launch.output_limit` asks Anthropic configs for 64,000 (others 32,000) and the hold follows (+USD 0.64 a call; opus-medium credit_snapshot 2.34 -> 2.98, portfolio_decision 2.11 -> 2.75, short_snapshot 0.99 -> 1.63). `wb_cap_presets.py` exit 0 (USD 20 cap admits every preset, with and without CP-8); `wb_cp8_hold_sizes.py` exit 0 but it imports the 32,000 constant, so it does not size Opus at 64,000. Known limit: a `max_tokens` stop inside a tool call is retried only when no usage was reported (`loop._RETRY_CLASSES`), so a charged cut stops the run; nothing tells the model to write shorter.
Not proven: CP-8 and the Changes tab on real output; CP-2G with the new presets; CP-DR web search guidance (not offered on Claude); the VMO2 reader check; that 64,000 is enough for CP-4 (not rerun).

## 2026-11-12 — Forecast page main period columns, PR 2 (branch `claude/forecast-period-columns-2`, stacked on `-1b`)
Plan: `docs/superpowers/plans/2026-11-12-forecast-period-columns.md`, Tasks 7-10. For a model whose `calculation.json` carries a `history` record the library's Forecast grid shows Quarter, Year to date (YTD, PYTD), Fiscal year, Last twelve months (LTM, Prior LTM), Pro forma, Base case and one Downside case (the stress shock when computed, else CP-2G's own downside drivers, else an unavailable column), and the other cases in a closed second grid. The store validates the record whole (kinds, prior pairs, dates, bounds) and shows nothing from a malformed one. Growth is refused across periods whose lengths differ by more than 7 days and on a fiscal year that is not twelve months; the first forecast year grows on the forecast's base year. A model without `history` keeps its layout except the case names, the second grid, the downside note and the placeholder.
Scope: offline, synthetic. Hand-written history records and answer keys in `tests/test_credit_os_store.py`; the browser test injects the real `store.read_cashflow` output of a two-key hand-written record into a built library (not a model published by `update_library`). Fidelity was checked at the store through the real producer against the plan's answer key (probe `arch2_answer_key_on_the_grid.py`, 119 cells), not on the page. Retained CP-1 header forms were checked in PR 1. No provider called. No retained run has a forecast inputs block with drivers, so no real run's Forecast page was read and no published model without a history was read in a browser.
Reader check: NOT done on a real run; it is pending the owner's paid run and the reading against the September VMO2 reference. The synthetic page was read at 1280 px by the controller only: seven groups in the owner's order; an unavailable column reads n.a. with its reason in the cell's label, distinguishable from a zero; at 1280 px the Downside case is off screen to the right (the grid scrolls inside its region); n.a. reasons sit in tooltips and a closed list; order inside groups is old-to-new for quarters and fiscal years, current-then-prior for YTD and LTM (ruling 2).
Commands: store, launch, periods, facilities and library pytest 1060 passed, 1 skipped, exit 0; browser pytest 43 passed, 1 skipped, exit 0; node 278 pass, exit 0; quality gate against 1b 0 findings, exit 0. Reviews: task reviews (mx-precise), adversarial review of the store changes with one re-review (mx-adversary; 6,000 generated records raise nothing; 144 no-history grids match the base), whole-branch review with confidence review and rewrite tournament (mx-architect; hand-picked mutants 19/19 killed). Probes stale by ruling: `adv4_notes_and_reasons.py`, `adv4_budget_and_work.py`, `adv4_producer_roundtrip.py`, `task7_no_history_unchanged.py`, `task8_hostile_and_placeholder.py` (superseded by `adv5_*` and `task9_*`).
Known, for the owner: the PR is about 1186 changed lines against the 800-line limit, waived by the owner on 2026-11-12 (a split on commits exists but no part ships alone); `scope_limits` and odd numeral forms in `checked_entries` predate the branch; growth on a negative prior shows a percentage (before this branch); "Why cells show n.a." lists the main grid only.
Not verified: a real run's Forecast page and the reader check on it; the page rendered from a published model; a no-history model in a browser; widths other than 1280 px, print, screen reader, touch; the weekly and live suites; mutation testing beyond the hand-picked mutants, none in `views.js`.

## 2026-11-12 — Forecast history record, PR 1 of the period columns (branches `claude/forecast-period-columns-1a` and `-1b`)
Plan: `docs/superpowers/plans/2026-11-12-forecast-period-columns.md` (rulings 1-16). `cpos_periods` reads the period columns CP-1 prints, ties each of the forecast's base lines to one base period, and builds quarters, YTD, PYTD, fiscal years, LTM, prior LTM and PF with exact Decimal arithmetic and a date check against CP-1's `Period | Start | End` table; `model_files` publishes it as `history` in `calculation.json` only when the delivery request asks (new CP-OS runs do; an earlier delivery re-derives byte for byte). CP-1 is asked for the period table whenever a forecast is wanted. Nothing on the page changes: the library does not read `history` until PR 2.
Scope: offline. Synthetic fixtures with hand-computed answer keys (`tests/test_cpos_periods.py`); six retained CP-1 handoffs read only for header forms (every statement-table period header is read; date-headed balance columns, `FY2024, annual definition`, `Rolling reported periods to 2024-12-28` and metric-specific headers are not, by rule); one retained live forecast run's CP-1 and CP-2G (`tdg-forecast-002`, read only) on which revenue, EBITDA, interest, taxes, capex and cash are located from the FY2024 base and fcf, debt and undrawn are not (their rows sit under a header that is not a period). No provider called and no model response: no CP-1 has yet printed the period table.
Commands: on 1b after the rebase onto 92d0a17, PR-check pytest list 2828 passed, 113 deselected, exit 0; quality gate 0 findings, exit 0 (against 1a and against main); node 278 pass, exit 0. On 1a, `tests/test_cpos_periods.py`, `test_cpos_facilities.py` and `test_cpos_launch.py` 726 passed, 1 skipped, exit 0; quality gate 0 findings, exit 0. Reviews: task reviews (mx-precise), adversarial review of `cpos_periods` with two re-reviews (mx-adversary; an 8,000-case generated-input run raises nothing and leaves no value without an amount or a reason), whole-branch review with confidence review and rewrite tournament (mx-architect), one fix wave and its re-review.
Known and accepted, for the owner: a line is located by its base amount, so if the right row sits under a header that is not a period and one other row prints the identical amount in the base period, that row's figures are published (probe `adv2_right_row_unheaded.py`); naming each operand's row and period in the CP-2G block removes this. A forecast whose base is not under one period header gets no history. Split at the owner's choice: 1a is the module and its tests (about 2,190 code lines, over the 800-line limit, waived by the owner on 2026-11-12), 1b the wiring (about 170). `cpos_forecast._tables` has a slow heading pattern on hostile input (before this branch).
Not verified: any real model response to the period-table instruction; the layer-1 path on a real handoff; a real earlier forecast delivery re-deriving from its manifest; the Forecast page (PR 2) and its reader check against the September VMO2 reference; browser, live and weekly suites; mutation testing.

## 2026-11-12 — Every pathway asks CP-1 for the chart tables (branch `claude/cp1-tables-all-pathways`, base 0e80345, owner "Yes, all pathways")
Scope: `cpos_launch._owner_tables` adds, for CP-1, the four `### Chart data:` tables its report routes do not already ask (instructions and checker); no report section. Offline, canned provider. Tests written by hand: all seven pathways' CP-1 instructions carry each heading once with its exact header, the checker accepts the complete canned answer and refuses each dropped table; a pack built from the canned CP-1 answer of relative_value, distressed_restructuring, portfolio_decision and short_snapshot states the five measures and a maturity profile. Probes `wb_pack_measures_by_pathway.py` 1 -> 0; `wb_cap_presets.py`, `wb_cp8_hold_sizes.py`, `wb_presets_order.py` exit 0 (short_snapshot hold 0.97 -> 0.99 on Opus configs). Gates: CI fast-tests command 2693 passed exit 0 (node changes/reader/static/calendar tests exit 0); browser subset 151 passed exit 0; quality gate 0 findings exit 0.
Not verified: a real model writing the four tables on those pathways; the Changes tab of a real run of those pathways; CP-1 output cost beyond the offline hold.

## 2026-11-12 — Changes seam round 3: one reader of CP-8's registers (branch `claude/changes-seams-r3`, base c9f84e1)
Scope: `changes_check.page_verdicts` derives the measure verdicts, module rows and ledger counts; `update_library.changes_data` carries them as `run.changes.verdicts` (null without a pack, or with a note or problem; an unreadable CP-8 output is a stated problem); `changes.js` only displays them (no register parsed for a verdict); a fact row that looks like a pack label (NFKC, alphanumerics, casefold) is refused. Offline. Expected verdicts are hand-written in `tests/fixtures/changes-seam/rows.json` (`page` per case; new cases: hidden-character label, `\x85`, `\x1f`, two Same definition rows, no closing pipe), read by `test_changes.py`, `test_update_library.py` (checker and library agree) and `changes.test.cjs`. Gates: CI fast tests exit 0 (node 18 changes tests; pytest 2683 passed), browser subset 151 passed exit 0, quality gate exit 0. Reviewer probes that call the deleted page functions (`wbr1_seam`, `wbr2_seam`, `rc_store_path`, `wb_*`, `t5_*` expecting the page to read a pack's `yes` or a table) break or pass vacuously by design.
Not verified: any real model output; the Changes tab against the September VMO2 reference; old handoffs against K9/K10 (known limit in the ruling).

## 2026-11-12 — Whole-branch review fixes (branch `claude/changes-seams`, stacked on `claude/short-snapshot`)
Scope: M1 one reading of CP-8's registers (shape: the checker requires exactly the forms the tab reads, plus one shared fixture `tests/fixtures/changes-seam/rows.json` read by a Python and a node test; a Python-side verdict hand-off was larger); M2 Over time compares run folders; L1 recorded no-comparison reasons reach the library verbatim; L2 scope no longer says "delivered whole" with "not produced"; L3 four test files added to CI fast-tests (about 7 s). M3, L4, L5 recorded only (ruling amendment). Offline, no model call.
Gates: CI fast-tests command from `checks.yml` 2631 passed, exit 0; browser `-k "run_start or context_form or library or inbox"` 151 passed, exit 0; library node set 276 passed, exit 0; `tools/quality_gate.py` 0 findings, exit 0 (also `--base origin/claude/short-snapshot`).
Probes (`wb_*`, then `t5_*`, `t4r4_*`): not_comparable_position, measure_label, module_cell(.py, .cjs), test_seams f1 and f4, changes_tab.cjs flipped to exit 0 or to the defect gone (f1, f4 now fail their reproduce assertions); wb_join_ids.cjs still exit 1 because it models the old `views.js` argument (the real call is covered by the browser test `test_over_time_joins_two_runs_the_pack_names_by_run_folder`); M3 and L4 probes still exit 1 (recorded limits). t5_*, t4r4_* exit 0.
Fix round 2: one row per pack measure (a second is refused); white space (non-breaking, doubled) normalised before a verdict is read, in the checker and in `changes.js`; `cp8.md` now states the Effect-cell rule and the one-row rule (git blob `ba25e4d`, new method revision; the library fixtures stand in for it); the ruling sentence on unreadable verdicts is stated per `yes` / `judge` / `no`. Rows added to the shared fixture. `wbr1_seam.py` exit 0; test_changes 195, CI fast 2635, browser 151, node 276 passed; quality gate 0 findings.
Not verified: any real model output; the Changes tab against the September VMO2 reference. A real model following the revised `cp8.md`.

## 2026-11-12 — Short Credit Snapshot pathway (branch `claude/short-snapshot`, stacked on `claude/changes-section`, decision M6)
Scope: `short_snapshot` = CP-0, CP-1, CP-L10 (hand-written preset key); CP-L10 method rewritten as a one-page prose module with a Key figures table; CP-L10 leads the Overview; offline, canned provider, no paid call. Tests written by hand: the preset, the order, the other presets without CP-L10, an end-to-end canned run to a verified delivery, four refused variants (a passage figure in no table, no Bottom line, a module code in a sentence, no Key figures table), node tests (lead, label), browser tests (run start page card and the service's three-module review; the library lists the run as "Short credit snapshot" with CP-L10 as lead). Fix round 2: Key figures sign exact, one table, missing CP-1 refused, browser test renamed to be selected by the browser gate. Fix round 1: methodology.json title and purpose; Key figures header and Value figures checked against the CP-1 handoff (`prose_checks.key_figures_issues`; proves a figure exists in CP-1, not that it is the right measure or period). Gates, exit 0 each: CI fast list 2,277 passed; node 271; browser gate 148; test_cpos_launch.py 532 passed; quality gate 0 findings.
Not verified: that a Key figures figure is the right measure or period in CP-1 (only that it exists there); a real CP-L10 answer from a model; a reader check against the VMO2 reference; an earlier-format or CP-8-compared short snapshot in the library; Chrome only. Moved to the archive to keep this file under 1,000 lines: the 2026-11-10 library-links entry.

## 2026-11-12 — Changes tab in the issuer library (branch `claude/changes-section`, stacked on PR #55, decision M8)
Scope: `changes.js` renders the pack and CP-8's handoff; the store carries `run.changes`; offline. CI fast list 2,265 passed; node 268; browser gate 147 passed; quality gate 0; answer keys are literals; fix round 1: same-period differences are not issuer moves, no inferred first run, periods must match to join (probes exit 0).
Not verified: a real CP-8 run in the tab; a CP-8 refusal's pack (the delivery omits it); dark mode (none); a reader check against the VMO2 reference.

## 2026-11-12 — CP-8 fixes, rounds 1-3 (branches `claude/cp8-changes-r1`, `-r3`)

Scope: engine, method and run start service, offline, no provider call. Round 1: pack schema `cpos-changes/2` (difference
for equal units; `comparable` yes/no/judge; refs `E1`/`C1`); the checker reads each row and every printed difference; a CP-8
not accepted, an unbuildable pack or a hold over the cap delivers without CP-8; the approval names the earlier run and the
digest binds it (`--prior`); display name "Changes since the last run". Round 2: `same_period`, `definition_resolved`. Round 3:
the sentence word lists are deleted; the check is mechanical (K1-K12): `changes.same_period` (same date, else same fiscal
year), a withheld difference in no checked line, every figure of a checked line held in the pack, its definition texts or a
handoff of either run (the launch caller passes this run's handoffs and `prior/*.md`), fact rows carry held amounts but no
pack value or difference (Q-1). Answer keys are hand-written in `tests/test_changes.py`. Changed expectations (by the rulings):
`test_a_cp8_that_is_not_accepted_loses_only_itself...` (exit 0); the summary digest is `bound(digest, prior)`; 500 US$m not
held; "debt was 333"; two movement-in-words cases and one trend assertion dropped; a test renamed. Real pair (cpos-tdg-sol-medium-all-001
then tdg-reader-format-001): five measures, all `judge`; 20 `E`, 11 `C` refs; CP-8's first request 318,153 bytes, hold 5.73.
Results before the merge with main: fast set 1,439 passed, browser 138 passed, quality gate 0; reviewer probes `t4r3_same_period_rows`,
`t4r4_fact_row_leak`, `t4r4_sentences`, `t4r4_same_period`, `t4r2_prior` pass. After merging main (99afe9e; tests adapted to its model-choice API): CI fast list plus test_changes 2,433 passed; whole fast suite without tests/model 1,787 passed; browser 144 passed; node 257 passed; quality gate 0.
Not verified: a real model writing the ledger or judging a definition; whether the estimate matches a live first request; the
library's Changes section; a real CP-8 handoff against the new figure rule (hand-written mini pack and probes only).
## 2026-11-12 — CP-8 in the run: prior run, pins, comparison pack, check (branch `claude/cp8-changes`, decisions M5, M7, M8)

Scope: engine and method, offline, no provider call. Built: `changes.py` (prior-run rule, `prior/*` pins, `changes.json`),
`changes_check.py`, registry fan-in, `cp8.md`, `changes.json` in the delivery, the summary's `changes` line. Answer keys are
hand-written in `tests/test_changes.py`; isolation is checked on the requests sent. Changed: `test_cpos_launch.py` no longer
passes every method to `--modules`; `test_run_start_page.py` asserts `changes`. Results then: fast set plus `test_changes.py`
1,063 passed; all non-live, non-browser, non-slow less `tests/model` and `tests/test_financial_workflow.py` 1,477 passed;
browser 100 passed; quality gate 0. Not verified: any real model writing CP-8's registers; whether CP-8's request fits a long
run's context; real earlier runs on the lean-copy deliveries; the library's Changes section.

## 2026-11-12 — Run start page: effort (Fast / Balanced / High) and model (GPT Sol / Claude Opus)

Scope: offline, macOS; no provider was called and no run was started. Owner instruction recorded as
the 2026-11-12 amendment in `docs/rulings/2026-11-11-run-start-submit.md` (configs sol-medium,
sol-high, opus-medium, opus-high; USD 20 cap unchanged).
- Effort map: `BALANCED_HIGH_MODULES` (CP-1A, CP-1D, CP-2, CP-2A, CP-3, CP-3C, CP-4, CP-4C, CP-6);
  basis per module in `runs/tdg-mixed-effort-comparison.md`. Twelve of twenty assignments are
  inferred from module type, not measured.
- Engine: config `opus-high` (claude-opus-5-5, effort high, opus-medium price object);
  `cpos_launch --balanced`. Service: answers carry `model` and `effort`, defaults gpt/balanced,
  other values only at Advanced; six (model, effort) pairs map to the four configs; start-up
  requires the ruling to name all four; Claude refused without the Anthropic key. Page:
  two Advanced-only radio groups and a "Model and effort" summary row.
- Passed: quality gate 0 findings (42 files); 1,787 tests across the page, launcher, handoff loop,
  run start, inbox, packaging and `tests/model` files. Four failures, none from this change: the
  three in `tests/known-failures.txt`, and `test_upload_to_filed_report_with_the_real_launcher`,
  which fails identically on a clean `38d23de` checkout (empty `record.report`) and is not listed.
- Reviews: task reviews of engine, service and page, and a security review of the paid-launch
  gating (five invariants, seven saved probes), no High. One Medium fixed with a failing test
  first (the Claude-unavailable refusal now links to Pathway); Low test gaps closed in the same round.
- Page seen in a browser at desktop and 375 px (no horizontal overflow); controls appear only at
  Advanced with Balanced and GPT Sol selected. Not a reader check: no report page changed.
- Open, not fixed: a queued Claude run started after a restart without the Anthropic key fails
  as "launcher exited 2" and counts toward the daily limit (nothing is spent); a pre-change
  sealed-but-unmoved submission fails with a misleading reason; on the CLI a ruling naming
  sol-medium also admits `--balanced` / `--high-modules`; AGENTS.md names
  `tests/nightly-known-failures.txt` but the file is `tests/known-failures.txt`.
- Not verified: any live call (Opus at high effort, Balanced on either model, Claude from the
  page); the summary and Submit against a running service by hand; Windows; the full suite;
  confidence-review and rewrite-tournament on this change.

## 2026-11-12 — Per-module effort (`--high-modules`) and one mixed-effort TDG live run

Scope: historical TDG FY2024 (as of 2024-09-30), ruling `docs/rulings/2026-11-12-tdg-mixed-effort-to-cp2.md`;
one paid run on gpt-6.1-sol. Not a current credit view; one run per setting.
- Code: `HandoffExecutor(effort_by_module=...)`, passed by `run_live_handoffs` and `cpos_launch
  --high-modules`. `tests/test_handoff_loop.py` and `tests/test_cpos_launch.py` passed (472, 1 skipped);
  quality gate 0 findings; task review passed with three Low test gaps open (pass-through to
  `run_live_handoffs`, seed digest, multi-turn). confidence-review and rewrite-tournament not run.
- Live: `runs/cpos-tdg-sol-mixed-cp2-001` (main checkout), high on CP-0, CP-1A, CP-1D, CP-2, CP-2A.
  `live/calls.jsonl` records high on CP-0, CP-1A, CP-1D and medium on CP-1, CP-1B, CP-DR, CP-1C.
  Six modules accepted; stopped at CP-1D (three drafts refused: "Invalid Markdown table header",
  which names no table; the fault was a 7-column header over an 8-column separator). USD 3.46.
  CP-2, CP-2A, CP-2E did not run; no report was published.
- Comparison with the saved all-medium runs: `runs/tdg-mixed-effort-comparison.md` (handoffs read
  by a separate reviewer, tabled figures checked against the 10-K). High: clear gain on CP-1D
  (unaccepted draft), none on CP-0, inconclusive on CP-1A; the medium modules needed no more.
- Not verified: CP-2 onward under mixed effort; a same-code all-medium control (instructions
  changed after both baselines); the full test suite.
## 2026-11-12 — CP-2G facility schedule (branch `claude/cash-flow-model-comparison-498459`)

Owner waiver 2026-11-12: the 800-line PR limit is waived for this branch's pull request (about 1,290
changed lines: plan document about 340, tests about 520; the whole-branch review found no sensible split).

Scope: CP-2G facility schedule: offline synthetic tests only; no provider called, no model response
retained; a live CP-2G run that states `facilities` has not been done; the Forecast page was not
exercised with the new `forecast_exact.json` keys.
- `uv run pytest tests/test_cpos_facilities.py -q`: exit 0, 55 passed (the answer key puts the debt outside the stated facilities at the analyst's rate: 37.5, 34.8, 30.6).
- `uv run pytest tests/test_cpos_launch.py -q -k "forecast or told_how"`: exit 0, 24 passed; the whole
  file: 507 passed, 1 skipped (the paid live test).
- `uv run python tools/quality_gate.py`: exit 0, 0 findings.
- Independent checks: the output for a block without facilities is byte-identical to origin/main 36b6d8f
  (sha256 e5017389abc2c878a0b0bae323a50bcbadf35c3a08f676f277c1505b9d047089 over the five model files);
  the arithmetic matched an independent Fraction calculation over 74 accepted seeded random blocks
  (11 with debt outside the stated facilities, per-case rates included; reviewer's probe, not in the suite); the
  adversarial review found and fixed two Medium defects (negative total debt from repayments above
  base debt; unbounded floating all-in rate). Three boundary tests each kill their mutant (`0 <= rate`
  to `0 < rate`; `unallocated < 0` to `<= 0`; `due < start` to `<=`).
- Known limits: debt outside the stated facilities bears interest at the analyst's assumed rate, not a sourced one; with base debt
  missing no unit check runs on facility balances; the printed-in-CP-1 check for rate terms accepts
  any matching percent anywhere in CP-1.

## 2026-11-11 — Starting a run from an earlier run: the whole branch (branch `claude/initiating-runs-existing-issuers-4a8739`)

Owner waiver 2026-11-12: the 800-line PR limit is waived for #52 (2,784 changed lines).

Scope: offline, macOS, headless Chrome against the run start service over a fake launcher (no provider
called, no paid run). The whole branch after its whole-branch review: carry from an earlier run (locked
ID, documents, answers, pathway, module subset, turns), the existing-issuer notice, "Start again from
this run", and "Start a run" on the library's Report history. This wave fixed the review's seam findings
(`?from=` with a submitted run still held, carried-file marks against uploads, the carried pathway and
subset/turns marks, `open_regular` through `platform_io.regular_open`, hidden names, refused listings).
- `uv run pytest tests/test_run_start_prior.py tests/test_run_start_submissions.py tests/test_run_start_service.py -q`: exit 0, 170 passed.
- `uv run pytest tests/test_run_start_page.py tests/test_library_page_browser.py -q --deselect tests/test_run_start_page.py::test_upload_to_filed_report_with_the_real_launcher`: exit 0, 131 passed (91 page, 40 library), none skipped (Chrome ran).
  `test_upload_to_filed_report_with_the_real_launcher` fails on the base already and is not part of this change.
- Review probes (`wb_seams.py`: 10 passed; the earlier probes exit as before, `probe_carry_races.py`'s
  seal-between-copies case still fails: ruled out of this wave).
- `uv run python tools/quality_gate.py`: exit 0.
- Fidelity: the notice text, marks, load messages and the progress note are asserted in the DOM Chrome builds.
- Reader check: not done; pending. No real run was read against the September VMO2 reference.
- CP-8 summary lines (the "changes section" and the two-prior-runs lines) are not built: the CP-8 redesign has not merged.
- Windows not run: the `O_BINARY` open of a carried file is from reading `platform_io.regular_open` only.

## 2026-11-12 — Run start page browser tests after the preset change (branch `claude/web-search-run-page`)

The browser tests (`-m browser`) were not run for the commits from 73b499b (presets) to d185d83. Run then:
`tests/test_run_start_page.py` 14 failed, 42 passed (at 0e2c564: 1 failed, 55 passed). Causes: (a) real page
defect, `build()` required "Current period" whenever CP-2G was in the run; CP-2G joined credit_snapshot and
covenant_refinancing, so a Basic submission that the launcher accepts (`cpos_launch.prepare` takes a blank period)
was blocked. The page now requires it for an earnings update only, labels it recommended, and adds a "Note" row
for CP-2G when it is blank (10 tests). (b) stale expectations: Standard now shows the research-questions stage
for credit_snapshot and covenant_refinancing (CP-DR is in every pathway); the services-forecast and limit-tick
tests now count the page's own CP-DR note, CP-2A no-legal-documents limit and CP-2G reading it. (c) pre-existing
since PR #46: a delivery files no report page, so `record.report` is `""`; the assertion now says so (the run
page's link to the library's Report history for the run is checked by the next test). The research-text
assertion already matched the final copy. After: that file 56 passed; `-m browser -k "run_start or context_form
or library or inbox"` 100 passed, exit 0; the fast set 756 passed, exit 0; quality gate 0 findings, exit 0.
Not verified: a forecast run with a blank current period through a live provider.

## 2026-11-12 — Web search from the run page; leaked citation markers (branch `claude/web-search-run-page`, decisions M1, M4)

(a) Paid test, this dated case only (TDG FY2024, ruling `2026-11-11-cpdr-web-search-live-test.md`, run `tdg-cpdr-web-001`): CP-0, CP-1, CP-DR and CP-1C accepted, charged USD 3.39131650. CP-DR located HEICO and
Howmet figures and CP-1C read them. Defect: the delivered CP-DR handoff held 54 provider citation markers
(U+E200 `cite` U+E202 `turn..view..` U+E201) in reader prose, which the eight prose checks did not catch.
Fix: markers are removed from a searching module's answer before the check (count in `<n>.markers.json` and a
`citation_markers_removed` event; provider response unchanged), plus prose check 9 for any other shape
(reader-ruling amendment). On that handoff the removal leaves 0 markers and adds no double space or
space before a comma or full stop. Not verified: `store:false` behaviour was not separately inspected, peer
figures were not checked against the cited pages, analytical accuracy.
(b) This change, offline (no provider call): the standing run-start ruling lists `web-search`; `prepare`'s
cap check holds the CP-DR search fee (USD 0.16) as the live loop does; the summary passes it; the page's
approval summary says what goes to OpenAI; READMEs updated. Tests: `test_citation_markers.py`, the
`prepare` and ruling tests in `test_cpos_launch.py`, `test_context_form.py`, `test_run_start_submissions.py`.
`test_inbox_scheduler.py::test_a_submission_is_run_by_the_real_launcher_and_listed` failed identically on the base
`claude/forecast-layer1` (canned answers; stopped at the checker); commit ebd4c13 fixed it (the canned launcher
answers CP-2G with a forecast block).
(c) Fix round 1 (security review, offline, no provider call): the page and ruling no longer say queries "use
public names only" as a fact: the module is told to, the queries it sent are kept in `<n>.response.json`, and
`flag_search_queries` flags afterwards any query with a supplied file name or a source figure of 4+ digits (years
1900-2100 excepted) as a `search_query_flagged` event and `<n>.queries.json` (detection, not prevention; the
library's Run record does not show the count: its store has no field). Owner ruling 2026-11-12: web search for
`public` and `private` cases, off for `synthetic` (one rule, `web_search_offered`; offline hold, live hold and
the `Web:` line agree; the page says before Submit whether the run searches). Source guidance and a `Source type`
cell on web rows (METHODOLOGY-REVIEW.md): no paid run has exercised the new source guidance. Markers: a marker
never spans lines, stripping is linear, the tool result tells the model how many were removed and an edit may quote
marked text, check 9 covers `cite\s*turn\d+[a-z]+\d+` anywhere in the handoff and only U+E200-U+E202.
Forecast riders: `~~~` fences are code, `\|` stays in its cell, working capital is the cell sign-reversed as CP-2G
reads it (the base's test fixtures now print wc as `(10)`).

## 2026-11-11 — Forecast from layer 1 (branch `claude/forecast-layer1`, decision M3)

CP-MODEL (preset or `--modules`) means "publish the forecast"; it makes no model call. Without CP-2G,
CP-1 gets a layer-1 variant of the forecast block (base operands as CP-1 prints them, run-rate drivers,
no cases, no shock) and the forecast comes from it; with CP-2G the block, checks and files are unchanged.
A bad or absent CP-1 block is not a CP-1 check: the model is withheld through the existing fail-open
(stderr, `model_not_published` event, `forecast_failure` in the completion record). Published limits
say "run-rate inputs the CP-1 handoff stated"; the library shows them under Model limitations, unchanged.
Offline, synthetic handoffs only (no provider call, no run folder touched): new tests fail on the base
and pass now. `uv run pytest tests/test_cpos_launch.py tests/test_handoff_loop.py tests/test_update_library.py
tests/test_credit_os_store.py -q -m "not live and not browser"` 666 passed, exit 0; `uv run python
tools/quality_gate.py` 0 findings, exit 0. Changed expectations: `--modules CP-MODEL` is no longer refused;
earnings_update's report scope now names the run-rate forecast; the publish-failure stub takes a source
argument.
Fix round 1 (the operand-key row rule) was replaced in round 2 after re-review: CP-1 keeps its natural
tables; each layer-1 base operand states `{"amount","reason":null,"row","period"}`, the exact first-cell
label and period header it was read from, and Python reads that one cell (tables outside fences, `## Sources`,
the block and the reader passages; trimmed and emphasis-stripped, case-sensitive; `1,000`, `-1,000`, `(1,000)`,
U+2212 parse as signed; `1,000k`, `12%`, `n.a.` do not). Outflows (cp2g.OUTFLOWS) compare by magnitude, all
others signed; zero, or several differing, cells refuse the operand by name (fail-open unchanged). CP-2G
refuses a `row`/`period` and keeps its check byte for byte. The block still does not vouch for a reader
figure in `figure_issues`. Probes `r2_m1_row_defeats.py`, `m3_layer1_operand.py`, `m3_block_vouches_reader.py`,
`r2_m2_block_edges.py` exit 0 (the first two pass partly because the old-shape blocks they build carry no
row/period and are refused; the accept/refuse cases are in the new tests). `uv run pytest tests/test_cpos_launch.py
tests/test_prose_checks.py tests/test_handoff_loop.py tests/test_update_library.py -q -m "not live and not browser"`
690 passed, exit 0; `uv run python tools/quality_gate.py` 0 findings, exit 0.
Known limits: driver values are not checked against their anchors (the rationale is free text); runs
interrupted before this change refuse to resume. Not verified: a real model writing the layer-1 block; the library on a layer-1 model beyond the
store tests; `tests/test_financial_workflow.py`.

## 2026-11-11 — Pathway presets: CP-DR and CP-2E everywhere (branch `claude/module-presets`)

Decisions M1-M7 are recorded in `docs/rulings/2026-11-11-module-presets-and-changes.md` (a decision
record; it does not lift the pause).

(a) Live run facts, this dated case only (ruling `docs/rulings/2026-11-11-reader-format-live-test.md`): TDG
FY2024 public files, context `runs/tdg-context-2024-09-30.json`, `credit_snapshot`, sol-medium, cap USD 15;
run folder outside the repository. CP-0, CP-1, CP-1A, CP-2, CP-4, CP-3, CP-5 and CP-6 were all accepted and
delivered; charged USD 3.20906590; two drafts were rejected and repaired within the retry limit (CP-1, CP-3).
Reader check so far: only CP-6's reader passages were read by the controller: judgement first, sources on
Basis lines, no codes in sentences. Remaining weakness: pipeline wording in reader text ("producer-owned
corrections remain open", "canonical financial amount", "open producer QA findings") and dense prose.
Not verified: the other seven modules' prose; a side-by-side against the VMO2 reference; analytical accuracy.

(b) This change, offline only (no provider call, no run folder read or written): M1 and M2 presets, CP-2G
added to credit_snapshot and covenant_refinancing, CP-8 removed from portfolio_decision, context-form
copy. Gate results: `uv run pytest tests/test_cpos_launch.py
tests/test_context_form.py tests/test_inbox_activity.py -q -m "not live and not browser"` 509 passed, exit 0;
`tests/test_cp8_comparison.py tests/test_handoff_loop.py` 44 passed, exit 0; `uv run python
tools/quality_gate.py` 0 findings, exit 0. Plans per pathway were prepared offline by the parametrised
test (every pathway, four peer sources); `tests/test_financial_workflow.py` was not run (over the
fast-test limit). M3-M7 are decided and not built here.

## 2026-11-11 — Runs on earlier methods are listed and marked (branch `claude/list-earlier-method-runs`)

Scope: offline, macOS; synthetic fixtures only (`tests/library_fixtures.py`, the fake launcher run). No
model call, no run folder under `runs/` read or changed. Owner decision 2026-11-11: a run whose module
methods changed since it ran is listed with `method_changes` and shown as "Earlier methods" (Report history
status, run label; Run record lists the changes). Other refusals are unchanged. Real TDG runs were not
rebuilt here.
- Gates: `uv run pytest tests/test_library_index.py tests/test_update_library.py tests/test_credit_os_catalogue.py -q` 90 passed, exit 0; `node --test` static, reader, calendar 257 pass, exit 0; `uv run python tools/quality_gate.py` 0 findings, exit 0.

## 2026-11-11 — Issuer library presentation to the reader ruling (branch `claude/library-layout-637b87`)

Owner waiver 2026-11-11: the 800-line PR limit is waived for #47 (5,969 changed lines).

Scope: offline, macOS, headless Chrome; the library app (`apps/issuer-library`) only. No provider was
called, no run was started, no stored handoff or run folder was changed (retained runs were read through
a symlinked `runs` folder in a scratch workspace). No run in the new handoff format exists yet: the new
format was seen only on a hand-made synthetic fixture (`apps/issuer-library/fixtures/synthetic-new-format/`,
built into a scratch workspace by `fixtures/build_synthetic_run.py`); the earlier format on the three
listed retained TDG runs (`cpos-tdg-sol-high-001`, `cpos-tdg-sol-high-cp2-001`,
`cpos-tdg-copilot-sol-medium-002`). This is not the reader check against the September VMO2 reference
that AGENTS.md requires for a presentation change: that needs a real new-format run and stays open.
- Built (decisions 3-7, 9, 10, 12, 14; H1, H3, H4, H5, H7): rail without Reports; per issuer Report
  history, Overview, Modules, Forecast, Evidence with a run label; delivered report view, its adapter and
  the Calendar tab retired; Overview selects passages only (CP-6 else CP-2 lead, bottom lines, limitations
  de-duplicated by the check-7 normalisation, key charts, nearest dates); flat Modules navigator of the
  modules that ran; figures and a quiet Basis link open the inspector; earlier-format trailing citations
  move verbatim behind Basis; Evidence's four lists with handoff and instruction copies under
  `library/downloads/`; Run activity shows live runs only.
- Gates (HEAD of the branch at push): `node --test` reader/static/calendar 245 pass, exit 0; `uv run
  pytest -m "not live and not browser"` on the eight library test files 348 passed, exit 0;
  `tests/test_library_page_browser.py` 38 passed; `uv run python tools/quality_gate.py` 0 findings, exit 0.
  `tests/test_library_reader_refs.py` asserts every Basis item and Source cell of each synthetic handoff is
  reachable from the rendered page, with hand-written counts.
- Walk-through at 1440 px and 375 px on both libraries: every page renders with no console error except
  the pre-existing missing `../activity.js` when opened outside the run start service; a figure opens the
  inspector by keyboard (Enter) and Esc returns focus; no horizontal overflow at 375 px.
- Known limits: the inspector shows a source page's excerpt for a Basis item only once the engine's
  `credit_os_chips` change (PR #46) is merged; earlier-format dates written as text cannot feed Nearest
  dates; document dates of source files are not recorded anywhere, so Evidence shows "Not recorded";
  key charts are selected per module from the catalogue (rows carry no chart identity);
  `src/deploy_workflow/run_start/service.py` still links finished runs to `library/reports/`, which this
  branch no longer writes (fixed on the engine branch).

## 2026-11-11 — Reader standard and checks in CP-OS; delivered report retired (branch `claude/reader-engine-d46913`)

Scope: instructions, checks and delivery changed; proven by synthetic passages and offline tests
only. No provider was called and no run was started. No retained model response written under the
new standard exists yet, and the reading check of one real run against the September VMO2
reference (decision 11) is not done.
- Changed: CP-OS instructions (`owners/cpos_launch.py`): every prose module is told to open
  `## Findings` with `### Bottom line`, `### Key findings`, `### Contrary evidence and what would
  change the view`, `### Limitations`; data modules (CP-0/CP-PARSE, CP-1, CP-1C) and blocked
  modules only `### Bottom line`; the Basis line form of H3; figures with currency or unit; no
  labels; persona kept with "Lead with the judgement; use data to support it, not to narrate it.";
  CANON_SHARED's reader-facing layer and reading order sent to prose modules. `### Reader summary`,
  the per-module opening H3, the CP-2-only reader standard and its front lines are removed.
- Checks: the eight H6 prose checks (`prose_checks.py`) run in the CP-OS handoff check on the reader
  passages; a failure is repair feedback naming check, line and text, inside the existing retry and
  cap. Hand-written passing and failing passages per check (`tests/test_prose_checks.py`); check 7
  across a run shown with the fake provider. Instructions and checks were cross-checked by a
  whole-branch review: every instructed form passes all eight checks. The Reader-summary figure rule was restored
  for the new passages as a fidelity check (`figure_issues`, labelled `Fidelity check:`, not a ninth
  prose check): every reader-passage figure must appear outside the reader passages with the same
  sign, unit and scale (owner, 2026-11-11). Review fixes in the same entry: the library build skips
  a delivery with no `report.html` (`apps/issuer-library/update_library.py`, the cause of the 14
  failures above); check 6 also takes the first-column letter+digit cells of `## Calculations`
  tables (period labels excepted); a Basis line after a blank line is sentence text.
- CP-8 requires an eighth dimension, Presentation (`tests/test_cp8_comparison.py`).
- Delivery: new deliveries write no `report.html`; completion records carry `delivery_sha256`
  (of `delivery.json`); HTML Model, charts, calculation JSON and forecast files unchanged. Earlier
  runs with `report.html` are still listed and accepted as CP-8 bundles (tests on both formats).
- Passed, exit 0: the affected fast tests (`test_cpos_launch`, `test_prose_checks`,
  `test_reader_summary`, `test_handoff_loop`, `test_library_index`, `test_cp8_comparison`,
  `test_credit_os_catalogue`, inbox tests, `test_run_start_page`, `test_update_library`,
  `test_credit_os_store`; `-m "not live and not browser"`) on this branch merged with the library
  branch (`claude/library-layout-637b87` at 3294c8d) in a scratch worktree: 899 passed;
  `tools/quality_gate.py`: 0 findings. Before the `update_library.py` fix, 14 of those tests failed on
  its `report.html` read.
- Limitation (owner ruling: left as is): `owner_rendering.py:992`, `financial_rendering.py:167` and
  `rendering.py:162` still write `report.html` outside CP-OS.
- Not verified: any real model response to the new instructions; the reading check against VMO2;
  the browser test of the library's Run activity link (library side); the full weekly suite.

## 2026-11-11 — Reader and issuer report ruling, documents only (branch `claude/reader-ruling-docs-2d2c2a`)

Scope: documents only. Changed: `docs/rulings/2026-11-11-reader-and-issuer-report.md` (new),
`AGENTS.md`, `METHODOLOGY-REVIEW.md`, `README.md` and this entry. No code, test, prompt text or app
changed; no provider was called. Nothing enforces the ruling yet: CP-OS still sends the reader
standard to CP-2 only, delivery still publishes `report.html`, and the library is unchanged.
- The two following sessions must prove, against the ruling's "Handoff contract":
  module instructions, checks and delivery: every prose module is sent the four reader passages
  and the Basis line form, data modules the bottom line; the eight prose checks block a handoff
  and send a targeted repair request within the existing cap, each shown failing on a crafted
  handoff and passing on a conforming one; CP-8 compares presentation; fidelity checks unchanged.
  Library presentation: Report history, Overview selection (CP-6 then CP-2 lead), the flat
  Modules navigator, Evidence's four lists and the Basis/inspector behaviour, each on a
  conforming fixture and on an existing run labelled "Earlier format" with stored handoffs
  byte-unchanged.
- Judgement quality is proven only by reading one real run per change against the September
  VMO2 reference; no paid run is allowed in these sessions, so that reading stays open.

## 2026-11-11 — Run start page: the inbox watcher and folder drop removed (branch `claude/no-nothing-6d5113`)

Scope: offline, macOS, with stand-in launchers (the fake launcher `tests/fixtures/fake_launcher.py`
and the canned-provider launcher `tests/fixtures/canned_provider_launcher.py`). No provider was
called and nothing ran on Windows. This is not proof of a paid run.
- Built: `inbox/watcher.py` is now `inbox/scheduler.py` (`Scheduler`; the folder scan, claim,
  settle timer, rejection into `inbox/failed`, `_template` copies and the watcher's own command
  line are gone); `Layout` and `ensure_layout` moved to `inbox/layout.py` and make no `inbox`;
  `inbox/drops.py` and `Start watcher.cmd` are deleted; `Start run page.cmd <root> [address]`
  runs `-m deploy_workflow.run_start`; the package ships the 2026-11-11 ruling; the issuer-ID
  length limit moved from the drop check to the summary. Records the watcher wrote still load and
  show; every run it queued (a record with no submission) is marked failed at start-up with a
  reason and is never started.
- Passed on this tree, exit 0 (final wave, after the whole-branch review): `uv run pytest` on
  `tests/test_inbox_scheduler.py`, `test_inbox_runs.py`, `test_inbox_activity.py`,
  `test_inbox_filing.py`, `test_inbox_layout.py`, `test_run_start_submissions.py`,
  `test_run_start_scheduler.py`, `test_run_start_service.py`, `test_run_start_page.py`,
  `test_context_form.py`, `test_context_module_options.py`, `test_cpos_launch.py`,
  `test_issuer_library_packaging.py`, `test_library_page_browser.py` and `test_library_index.py`:
  933 passed, 1 skipped (the paid test), in Chrome, so the 55 page tests ran;
  `uv run python tools/quality_gate.py`: 0 findings; `node --test` on `static.test.cjs` and
  `calendar.test.cjs`: 187 passed (the library's own JavaScript, which CI runs).
- Final wave, what it changed: the summary joins the launcher's forecast with the page's own
  rules and asks a tick for every gap, limited and will-refuse item and every check that has a
  fix; the as-of and legal-disagreement rules are limited for the whole run; Run activity shows the
  submitter and, when served, links the library's own copy of a finished run's report (the page's
  finished view links the same copy); library files are opened with `platform_io.regular_open`
  (binary, no wait on a FIFO); a timeout the service meets itself is a 500; a reload with a
  saved submission the service no longer holds says so and offers a new submission as a
  separate click; `runs.prepare` and `Scheduler.run_forever` are deleted.
- Reviewer probes after the wave (`.superpowers/sdd/2026-11-11-staged-run-start/probes/`): the four
  review gaps, the served library report, the FIFO and the issuer-ID wording pass. Three probes
  still fail by ruling or scope and are explained in `final-wave-report.md`: the filed
  `issuers/...` link (the ruling links the library's copy, no new route), the service's answer
  for a submitted submission (the ruling makes the page, not the service, say it), and the refused
  folder's file list (not in this wave). `t8r1_server_side_timeout.py` tests Python's own
  exception classes and cannot pass; `tests/test_run_start_service.py` covers the behaviour.
- CI deselects every page test (they need Chrome), so no CI run touches the approval or Submit.
- The real launcher ran in one scheduler test (canned provider answers, the real library
  rebuild); the others stand in a launcher.
- Not verified: a paid run through Submit; whether CP-3 and CP-6 honour `module_options`; Windows
  (`Start run page.cmd`, the file lock, paths); browsers other than Chrome; more than two
  analysts submitting at once; `../runs/...` download links, which the service does not serve; the
  full test suite (weekly job); the page tests in CI (CI deselects them); Windows file opening
  (`O_BINARY` is requested through `platform_io`, not run there).

## 2026-11-11 — Work-PC change packs (`tools/work_pc_delta.py`)

Scope: offline tooling only; no analytical module, provider call or deliverable changed.
The work PC takes ZIP downloads without git, so `generate` writes a numbered pack per sync
(package/version tables from `pyproject.toml` and `uv.lock`, merged PR titles, every changed
file with the new-version line ranges, the full patch) and `check` compares any folder with
the git blob hashes in `manifest.json`.

Confidence review: same-day packs sorted by hash, not order (confirmed, fixed with a
sequence prefix); `\x1f` stripped as whitespace dropped PR titles (confirmed, fixed);
a pack's own commit leaking into the next pack (tested: excluded); renames, deletions,
names with spaces, transitive-only lock changes, CRLF re-saves, `.venv` noise (tested).
`check` matched a `git archive` ZIP of `04e7221` exactly. Whole-history pack
`472bdea..04e7221`: 5.9 MB. No symlinks in the tree (they would be reported as `extra`).

Verification: `pytest tests/test_work_pc_delta.py tests/test_quality_gate.py` 5 passed;
`tools/quality_gate.py` 0 findings. First pack `04e7221..6f5ac16` (PR #42); `check` on a
`git archive` of the PR head: identical.

Follow-up: `.github/workflows/work-pc-pack.yml` makes and commits a pack after each push to
`main`; a range with only pack-folder changes makes none (tested), and the CI fast-test
list now includes `tests/test_work_pc_delta.py`. The workflow itself first runs on merge;
a protected `main` would refuse its push (the run fails visibly; hand generation remains).
2026-11-12: packs 001–017 chain without gaps; every merged PR #42–#61 appears; `check` on
`origin/main` identical. `plan` (copy/delete/merge/keep per file, 6 tests pass) on an archive
of `04e7221` with two edits against `origin/main`: 2 merge, 140 copy, 7 delete, 1 keep.

## 2026-11-10 — Visuals package 8: complete the whole-branch review

Scope: continued the interrupted `claude/visuals-p8` changes from reviewed package 7
(original tip `44108e6`). Offline synthetic tests and a deterministic rebuild from retained
handoffs; no provider call or new analytical run. Packages 1–8 were later pushed and merged through GitHub PRs #33–#40. No further rewrite tournaments,
per the current user's instruction.

Confidence review, ranked doubts and outcomes:
- **Missing evidence could force invented rows (M1).** Every owner row table now accepts its
  explicit all-gap form; the library retains the reason in `chartGaps` without a chart or an
  invalid-table complaint. Checked all independently written owner fixtures and the original
  reviewer's no-data probe. Empty unit/basis and mixed gap/data rows remain invalid. A stated
  gap in a unit/basis cell remains permitted as explicit missing information, never a guessed unit.
- **Index claims could disagree with actual pages (M2).** Not-assessable modules' charts show
  their limitation and no placement/table-form link; maps remain available as their pages draw
  them. Static regressions and the original folded-page browser probe (updated to expect the
  removed link) verify this through the generated library.
- **Event-log failure could masquerade as no history (M3/L4).** The run record carries the read
  error; the page names and escapes it. Non-object JSON records invalidate the log without
  stopping the build. Missing logs remain distinct. The shared log reader's existing tolerance
  for an unfinished final JSON line is unchanged.
- **Launcher/store disagreement could misstate figures (L1-L3/L5).** Fixed currency instructions,
  reminder status, unit constraints, peer bounds, maturity ordering, scenario count and duplicate
  class/scenario rejection. The reviewer's parity probe reports zero disagreements. Confidence
  review additionally reproduced a missing EUR period relabelling later USD figures; the chart
  now takes its unit from a numeric row. No numeric value is converted or derived.
- **Cleanup could remove a live caller (L6).** Traced callers and removed unused owner metadata,
  UI options, the redundant format lookup/CSS class and comparison-registry intermediate;
  repeated allocation/map instructions are emitted once. Affected fixtures still pass.
- **Package limit (M4).** Removed one redundant test-heading comment from package 2 and restacked
  the later local packages. Package 2 is exactly 800 changed lines; each other package is below
  800. Original branch tips are retained under `refs/codex-backups/visuals-p*-before-p8-review`.

Verification (each test process bounded to 300 seconds using Python subprocess timeout because
this macOS host has no `timeout` executable):
- `uv run pytest -q --tb=short -m 'not live' tests/test_cpos_launch.py
  tests/test_update_library.py tests/test_credit_os_store.py tests/test_library_page_browser.py`:
  **612 passed, 1 deselected**, including Chrome over file URLs; 84.40 seconds.
- `node --test apps/issuer-library/credit_os/web/static.test.cjs
  apps/issuer-library/credit_os/web/calendar.test.cjs`: **186 passed**.
- `uv run python tools/quality_gate.py`: **0 findings**; `git diff --check` clean.
- Retained-source rebuild into a temporary directory: `cpos-tdg-copilot-sol-medium-002`,
  `cpos-tdg-sol-high-001`, `cpos-tdg-sol-high-cp2-001`. The unfinished Copilot run was excluded
  for no completion record; `cpos-tdg-sol-medium-all-001` was excluded for the changed shared
  methodology. Original run directories were read only. This is library compatibility evidence,
  not proof that a model satisfies the new combined chart instructions or a complete TDG pathway.
- Still outside scope: paid model output for the new contracts, Windows, screen-reader/print
  testing, the pre-existing escaped-pipe parser discrepancy and the weekly full test suite.

## 2026-11-10 — Word documents (.docx) in the issuer folder (branch `claude/optimistic-johnson-bmnwip`, after main `3ac4db6`)

Owner: "Add docx compatibility too". Input only: nothing is written as Word.

- How it reads them:
  - The launcher now reads `.docx`. Like an HTML filing, a Word file is converted to text pages
    (`docx_text.py`) and pinned as `<name>.jsonl`, headed by its name and hash.
  - The text covers body paragraphs in order, table rows as cells joined by ` | `, and tabs and
    line breaks. Tracked deletions and tab-stop definitions are not text. Headers, footers,
    footnotes and comments are not read.
  - Parsing uses the workbook reader's guarded XML parse (no DTD or entity) and its size limits.
    A file that is not a Word document, or has no text, stops the launch naming the file.
- Unchanged:
  - HTML filings convert to the same bytes as before, so existing run folders still resume.
  - Old `.doc` files are still not read; the form says to save them as PDF.
- Also updated: the context form's file types (its copy is drift-tested against the launcher's),
  its help text, and README. The inbox reads the same list.
- Tests:
  - `tests/test_docx_text.py` (7) and a launcher test, written first; the tab-stop case found a
    defect, fixed before commit.
  - Launcher, context-form, inbox-drops, library-page and Word tests: all pass except 3 inbox
    permission tests that also fail on main here, because the sandbox runs as root.
  - Quality gate: 0 findings.
- Not verified: Word files made by Word itself; the tests build minimal files by hand.

## 2026-11-10 — Web search for the research module, offline (branch `claude/optimistic-johnson-bmnwip`, after main `1fbc57c`)

Owner: "Cp-dr supplies the peers … By default cp-dr always provides the peers or 1C and 2 can never
run", then "Yes" to working out web search for CP-DR. No provider was called; no paid run.

- Sources:
  - OpenAI pages fetched 2026-11-10 through owner-approved network access: the pricing page, the
    web search guide, the Responses reference and the gpt-6.1-sol model page.
  - Quoted in `cases/pricing/openai-web-search.json`: USD 10.00 per 1,000 calls plus search
    content tokens at model rates; tool `{"type": "web_search"}`; `include`
    `web_search_call.action.sources`; `max_tool_calls`; web search listed as supported for
    gpt-6.1-sol.
- What changed:
  - **Grant.** CP-DR searches only when the run's ruling lists `web-search` on its `configs:`
    line (`owners/cpos.py` `web_search_ruled`), and only on OpenAI. Other providers are refused
    before a call. The launcher prints a `Web:` line when CP-DR runs.
  - **Request.** Only CP-DR's requests carry the hosted tool, with at most 16 calls per response.
    Its system text adds the rules: public names only in a query, nothing published after the
    research cutoff, every web item cited by URL and date, figures quoted verbatim.
  - **Record.** A reply's `web_search_call` items are kept in the response record under
    `openai-web-search` and never sent back. A reasoning item before one is dropped, since it
    would go back without the item that followed it.
  - **Money.** Each searching call holds USD 0.16 more and is charged USD 0.01 per search action.
    Opening a page or searching within one is not charged; the guide names only search actions.
    A sent reply that cannot be read is charged the whole USD 0.16.
- Unchanged without the grant: the stored request and the OpenAI body for CP-2 and for CP-DR
  hash the same before and after (checked by script on both checkouts).
- Tests:
  - Written first: `tests/model/test_providers.py` (3) and `tests/test_handoff_loop.py` (3) failed
    at import before the code existed. `tests/test_cpos_launch.py` (1) fails with the launcher's
    grant wiring reverted.
  - Added after: the unreadable-reply charge test; reverting that charge to zero fails it.
  - `tests/model/test_pricing.py` pins the fee to the key file.
  - `tests/model`, the loop, launcher, library-page, context-form and inbox-watcher tests: 1,178
    passed, 3 skipped. 8 failed, every one of them also failing on unchanged code here: the 3 on
    `tests/known-failures.txt`, and 5 inbox-watcher permission tests, because the sandbox runs as
    root.
  - Quality gate: 0 findings.
- Not verified, until a paid run:
  - that web search runs with `store: false`;
  - that search content tokens are in `usage.input_tokens`;
  - that CP-DR ends a searching turn with a tool call under `tool_choice: "required"`;
  - whether its peer pack respects the cutoff;
  - whether CP-1C then has peers.
- Not done: the standing inbox ruling and every other ruling are unchanged, so web search stays off
  until the owner adds `web-search` to a ruling.
- Merged as `88c50ee` (#30). Owner: "Merge then test".
  - Ruling `docs/rulings/2026-11-10-cpdr-web-search-test.md`: CP-0, CP-1, CP-DR and CP-1C on TDG,
    `sol-medium` with web search, cap USD 10.
  - Dry launch here (no provider call) with tdg-all-001's context and a one-line stand-in source:
    the four modules are accepted and the launcher prints "CP-DR searches the web (the ruling lists
    web-search)".
  - Each call holds USD 5.73, or 5.89 for CP-DR, so the run can spend about USD 4.10 before the
    next hold no longer fits the cap. A stop there can be resumed.
  - The paid run needs the owner's machine, which has the TDG files and the key.

## 2026-11-10 — Context form against live run tdg-all-001 (branch `claude/optimistic-johnson-bmnwip`, after main `53a5632`)

Owner: "Yes do that" (compare tdg-all-001 with the form's forecast), "Your recommendation", then
"Cp-dr supplies the peers, the user does not provide them unless they specifically want to in the
context file…" and "User can provide peers but it is optional". Design note section 8. Compared
against the run's record below. The run folder was not read.

- Forecasts were made before the run reported. Of the 10 modules with a recorded outcome, the form
  flagged 9 and the launcher's `run_expectations` 5. The form's miss was CP-DR: Ready, but Blocked.
  The form's 4 Gaps for a missing source (CP-1C, CP-2H, CP-3D, CP-3) came back Blocked.
  CP-1D's Gap came back Restricted.
- CP-1D: no bridge is now Limited (its reads worked in the run).
- CP-DR: the form no longer asks for the peers' filings. Supplying peers is optional: add the
  peers' filings to the folder, which CP-DR is told to read, or give your own peer figures. CP-DR
  carries a Note, not counted: CP-OS gives no module a web search tool (`model/handoff.py`
  `TOOLS`). CP-OS sends CP-DR both cp-os's SKILL v1.1 (2026-07-22, web or hybrid research; blocks
  without web) and `cpdr.md` (2026-10-31, LOCAL). Neither reaches public peers here.
- Not changed: CP-2H, CP-3D and CP-3 had every read refused in the run, so they wait for a rerun.
  The registry keeps CP-DR optional for CP-1C and CP-2. That is a registry decision, not a form
  one.
- Tests: `test_the_research_module_supplies_the_peers_and_the_bridge_is_forecast_as_run` fails on
  the first version of this change, which asked about peer files, and passes now.
  `tests/test_library_page_browser.py` and `tests/test_context_form.py`: 45 passed. Quality gate: 0
  findings.
- Not verified: no live run of the changed forecast; one issuer, one date.

## 2026-11-10 — Sweep: end-to-end wiring (branch `claude/sweep-wiring`, base `53a5632`)

Owner: "Move to latest main - run /sweep refactoring and optimisation sweep make sure front to back
and end to end wiring." Contract and report: `docs/sweeps/2026-11-10-wiring/`. Range `c721a0f..53a5632`
(PRs 19–27). Offline, canned provider answers, no spend.

- Journeys proved at base:
  - The live TDG context round-trips through the context form, with only the intended changes. The
    launcher reads the form's output.
  - Every pathway: launcher → CP-OS → delivery → real library → five screens and `report.html`,
    with no console message and no unfilled value.
  - An inbox drop is run by the real launcher, filed byte for byte and listed. Before this, the
    watcher tests used stand-in launchers.
- No product defect was reproduced. Landed, tests and CI only:
  - `test_each_pathways_run_reaches_the_library_screens` (browser, 6 pathways).
  - `test_a_drop_is_run_by_the_real_launcher_filed_and_listed` with
    `tests/fixtures/canned_provider_launcher.py`. Dividing the watcher's `--cap` by 100 fails it
    and passes the stand-in test.
  - `test_the_library_screens_value_lists_are_the_codes`: run statuses, classification and rating
    scope in `views.js` against the Python literals; fails when a status is dropped.
  - `checks.yml` now runs `test_handoff_loop.py` and `test_context_form.py` on every PR.
- Performance, median of 5 after one warm-up, noise = max − min. `prepare()` over all 20 modules:
  23.8 ms (noise 18.0). Library rebuild of 10 run folders: 372.9 ms (noise 37.0), with no single
  hot spot. Nothing above the floor; page render unmeasured.
- `prepare(retained=)` and its resume helpers had no production caller. Owner: "Remove it". 127
  lines are gone from `cpos_launch.py`. The prepared run folder (manifest and instructions) hashes
  the same before and after for all six pathways. CP-OS's replay of pinned answers stays, and its
  test now pins them in the manifest directly. Reverting the producers pin check still fails it.
- Gates on the final tree, all exit 0:
  - quality gate: 0 findings.
  - `node --test` static and calendar.
  - CI pytest list plus the two added files: 1529 passed, 13 deselected (7 known failures, 6
    browser), after the removal took out two tests.
  - Browser (`test_library_page_browser.py`, `test_cpos_launch.py`): 29 passed. After the
    removal, `test_cpos_launch.py`'s 7 browser tests passed again.
  - Base logs: the same commands at `53a5632`, all exit 0.
- Not verified:
  - a live run of the journeys;
  - page render timing;
  - `TERM_LABELS` against the builder of `run.facilities` (not traced);
  - the form's download click (its `build()` output was used);
  - Windows paths.
