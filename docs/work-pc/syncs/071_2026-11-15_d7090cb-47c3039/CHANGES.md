# Changes for the work PC

From `d7090cb07f90` (the version the work PC last adapted) to `47c3039dc08f` (2026-11-15T15:52:06Z). 111 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `fc010a7` 2026-11-15 docs(work-pc): change pack for d7090cb
- `47c3039` 2026-11-15 After the restructure: journal harness retired, method scripts as acceptance checks, portfolio inputs (Merge pull request #127 from EricMG13/claude/busy-dijkstra-bgex9m)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.importlinter` | +3 −7 | L42-43, L45, removed after L52, removed after L54 |
| modified | `METHODOLOGY-REVIEW.md` | +82 −3 | L199, L881-959, L982, L1055 |
| modified | `README.md` | +13 −1 | L176-188 |
| modified | `VERIFICATION.md` | +70 −43 | L7-76, removed after L978 |
| modified | `pyproject.toml` | +5 −0 | L16-20 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +3 −2 | L60-62 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +28 −0 | L46-73 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/QUALITY-GATE.md` | +1 −1 | L60 |
| modified | `docs/reuse/selected-methods/CPOS_REGISTER_SCOPE.md` | +12 −2 | L14-23, L46, L54 |
| modified | `docs/reuse/selected-methods/manifest.json` | +73 −3 | L1097, L1099-1168, L1171-1172 |
| added | `docs/reuse/selected-methods/scripts/completeness_check.py` | +672 −0 | L1-672 |
| added | `docs/reuse/selected-methods/scripts/cp_tables.py` | +236 −0 | L1-236 |
| added | `docs/reuse/selected-methods/scripts/validate_handoff.py` | +956 −0 | L1-956 |
| added | `docs/reuse/selected-methods/skills/cp-1-canonical-data-foundation/scripts/credit_metrics.py` | +326 −0 | L1-326 |
| added | `docs/reuse/selected-methods/skills/cp-2d-liquidity-cash-flow-bridge/scripts/liquidity_bridge.py` | +215 −0 | L1-215 |
| added | `docs/reuse/selected-methods/skills/cp-2e-macro-fx-hedging-sensitivity/scripts/rate_fx_sensitivity.py` | +220 −0 | L1-220 |
| added | `docs/reuse/selected-methods/skills/cp-3c-refinancing-lme-risk/scripts/funding_gap.py` | +351 −0 | L1-351 |
| added | `docs/rulings/2026-11-15-full-assessment-portfolio-workbook.md` | +200 −0 | L1-200 |
| added | `docs/rulings/2026-11-15-journal-chain-retired.md` | +90 −0 | L1-90 |
| added | `docs/rulings/2026-11-15-method-script-checks.md` | +339 −0 | L1-339 |
| added | `docs/sweeps/2026-11-15-method-scripts/scope.md` | +156 −0 | L1-156 |
| modified | `docs/templates/README.md` | +150 −2 | L178-180, L183-188, L278-311, L337-443 |
| modified | `docs/templates/context-form.html` | +7 −3 | L894-895, L899-900, L1833-1835 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| added | `src/deploy_vii/inputs/__main__.py` | +92 −0 | L1-92 |
| modified | `src/deploy_vii/inputs/portfolio.py` | +426 −31 | L20, L79-94, L145-190, L634-635, L650-652, L666, L669-671, L689, L706-708, L747, L936-945, L958, L984-989, L991-992, L994, L996, L1010, L1015-1016, L1071-1095, L1099-1100, L1124-1153, L1156, L1158-1191, L1228, L1250-1251, L1261-1277, L1282-1283, L1299-1300, L1303-1509, L1518, L1520 |
| added | `src/deploy_vii/inputs/portfolio_export.py` | +2794 −0 | L1-2794 |
| deleted | `src/deploy_workflow/cpos_status.py` | +0 −14 | — |
| deleted | `src/deploy_workflow/financial_rendering.py` | +0 −214 | — |
| deleted | `src/deploy_workflow/identity_check.py` | +0 −44 | — |
| modified | `src/deploy_workflow/inbox/startup.py` | +1 −1 | L21 |
| added | `src/deploy_workflow/method_scripts.py` | +1055 −0 | L1-1055 |
| added | `src/deploy_workflow/method_scripts_cp1.py` | +300 −0 | L1-300 |
| added | `src/deploy_workflow/method_scripts_cp2e.py` | +263 −0 | L1-263 |
| added | `src/deploy_workflow/method_scripts_cp2g.py` | +467 −0 | L1-467 |
| added | `src/deploy_workflow/method_scripts_cp3.py` | +363 −0 | L1-363 |
| added | `src/deploy_workflow/method_scripts_cp3_ev.py` | +206 −0 | L1-206 |
| added | `src/deploy_workflow/method_scripts_cp4.py` | +177 −0 | L1-177 |
| added | `src/deploy_workflow/model/configs.py` | +56 −0 | L1-56 |
| modified | `src/deploy_workflow/model/handoff.py` | +5 −5 | L46, L60, removed after L73, L112-114, removed after L1247 |
| modified | `src/deploy_workflow/model/record.py` | +0 −4 | removed after L192 |
| added | `src/deploy_workflow/model/run_lock.py` | +41 −0 | L1-41 |
| deleted | `src/deploy_workflow/model_testing/__init__.py` | +0 −0 | — |
| deleted | `src/deploy_workflow/model_testing/__main__.py` | +0 −10 | — |
| deleted | `src/deploy_workflow/model_testing/budget.py` | +0 −263 | — |
| deleted | `src/deploy_workflow/model_testing/cases.py` | +0 −199 | — |
| deleted | `src/deploy_workflow/model_testing/configs.py` | +0 −94 | — |
| deleted | `src/deploy_workflow/model_testing/faults.py` | +0 −133 | — |
| deleted | `src/deploy_workflow/model_testing/mapping.py` | +0 −220 | — |
| deleted | `src/deploy_workflow/model_testing/pathway.py` | +0 −210 | — |
| deleted | `src/deploy_workflow/model_testing/records.py` | +0 −252 | — |
| deleted | `src/deploy_workflow/model_testing/report.py` | +0 −373 | — |
| deleted | `src/deploy_workflow/model_testing/run.py` | +0 −964 | — |
| deleted | `src/deploy_workflow/model_testing/scoring.py` | +0 −461 | — |
| deleted | `src/deploy_workflow/model_testing/slice_budget.py` | +0 −63 | — |
| deleted | `src/deploy_workflow/owner_rendering.py` | +0 −1216 | — |
| modified | `src/deploy_workflow/owners/cpos.py` | +13 −55 | L36, L58-59, removed after L61, removed after L68, L230-238, L297, removed after L827, removed after L868, removed after L1145 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +46 −11 | L34, L72, removed after L92, L172-175, L341, L446-459, removed after L593, L648-650, L1056-1061, L1099-1104, L1116-1121, L1188, L1300-1301, L1624 |
| added | `src/deploy_workflow/portfolio_workbook.py` | +290 −0 | L1-290 |
| deleted | `src/deploy_workflow/prompts/digest.py` | +0 −34 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/brief.json` | +0 −47 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/business_context.json` | +0 −76 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/change_screen.json` | +0 −74 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/committee_challenge.json` | +0 −50 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/compose.json` | +0 −112 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/credit_synthesis.json` | +0 −41 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/decision_ledger.json` | +0 −168 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/downside_pathway.json` | +0 −90 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/earnings_delta.json` | +0 −33 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/earnings_quality.json` | +0 −74 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/financials.json` | +0 −97 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/forward_credit_model.json` | +0 −92 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/integrity_review.json` | +0 −49 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/legal_covenants.json` | +0 −70 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/liquidity_bridge.json` | +0 −49 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/macro_fx.json` | +0 −112 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/market_implied.json` | +0 −119 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/narrative.json` | +0 −46 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/peer_benchmark.json` | +0 −55 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/quality.json` | +0 −39 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/rating_triggers.json` | +0 −75 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/readiness.json` | +0 −39 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/refinancing_risk.json` | +0 −58 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/relative_value.json` | +0 −80 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/research.json` | +0 −101 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/restructuring_fulcrum.json` | +0 −119 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/source_context.json` | +0 −44 | — |
| deleted | `src/deploy_workflow/prompts/rule_lists/source_readiness.json` | +0 −77 | — |
| deleted | `src/deploy_workflow/prompts/rules.py` | +0 −870 | — |
| deleted | `src/deploy_workflow/rendering.py` | +0 −174 | — |
| deleted | `src/deploy_workflow/replay.py` | +0 −660 | — |
| modified | `src/deploy_workflow/run_expectations.py` | +103 −3 | L18, L297, L353, L357-383, L615-682, L712-713, L743, L750, L756 |
| deleted | `src/deploy_workflow/run_pathway.py` | +0 −1359 | — |
| modified | `src/deploy_workflow/tools/__init__.py` | +1 −1 | L1 |
| deleted | `src/deploy_workflow/tools/upstream.py` | +0 −1838 | — |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/fake_launcher.py` | +1 −1 | L17 |
| modified | `tests/inbox_fixtures.py` | +1 −1 | L28 |
| modified | `tests/model/test_live_limits.py` | +5 −48 | removed after L11, removed after L17, L20, L31-32, L86, L89 |
| modified | `tests/model/test_record.py` | +1 −2 | L1180, removed after L1183 |
| modified | `tests/model/test_turn.py` | +2 −3 | L53-54 |
| modified | `tests/test_cpos_launch.py` | +345 −5 | L20, L602-617, L1491-1493, L1499, L2923-2927, L2938, L2941, L8639-8955 |
| modified | `tests/test_cpos_register_scope.py` | +30 −11 | L37-38, L40, removed after L45, L55-60, L252-253, L255-257, L260-262, L300-303, L325-327, L415, L419-423 |
| modified | `tests/test_handoff_loop.py` | +2 −2 | removed after L1212, L1216-1217 |
| modified | `tests/test_inbox_scheduler.py` | +1 −1 | L52 |
| added | `tests/test_method_scripts.py` | +1883 −0 | L1-1883 |
| added | `tests/test_portfolio_export.py` | +1290 −0 | L1-1290 |
| added | `tests/test_portfolio_workbook.py` | +590 −0 | L1-590 |
| modified | `tests/test_quality_gate.py` | +14 −0 | L34-47 |
| modified | `tests/test_run_start_submissions.py` | +42 −0 | L256-297 |

### tools

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tools/quality_gate.py` | +4 −1 | L41-43, L86 |
| added | `tools/synthetic_portfolio_exports.py` | +677 −0 | L1-677 |
| added | `tools/synthetic_portfolio_workbooks.py` | +314 −0 | L1-314 |
