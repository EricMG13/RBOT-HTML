# Changes for the work PC

From `a561bc76be19` (the version the work PC last adapted) to `d7090cb07f90` (2026-11-15T13:03:27Z). 156 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

| Item | Before | After |
|---|---|---|
| dependencies | pydantic==2.14.1, pypdf==6.21.2, openpyxl==3.1.5, github-copilot-sdk==1.0.28 | pydantic==2.14.1, pypdf==6.21.2, openpyxl==3.1.5, github-copilot-sdk==1.0.28, issuer-library |
| dependency group dev | pytest==9.1.1, ruff==0.17.1, mypy==2.4.0, hypothesis==6.170.5 | pytest==9.1.1, ruff==0.17.1, mypy==2.4.0, hypothesis==6.170.5, import-linter==2.16 |

### uv.lock installed versions (direct and transitive)

| Item | Before | After |
|---|---|---|
| click | (absent) | 8.5.1 |
| grimp | (absent) | 3.20 |
| import-linter | (absent) | 2.16 |
| issuer-library | (absent) | 0.1.0 |
| markdown-it-py | (absent) | 4.3.0 |
| mdurl | (absent) | 0.1.2 |
| rich | (absent) | 15.0.0 |

## Changes merged to main (oldest first)

- `9d040f8` 2026-11-14 docs(work-pc): change pack for a561bc7
- `d7090cb` 2026-11-15 Restructure: packaging, HTTP base, import contracts, splits, removals; CP-3C and CP-6A in the full assessment (Merge pull request #126 from EricMG13/claude/busy-dijkstra-bgex9m)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| added | `.importlinter` | +70 −0 | L1-70 |
| modified | `METHODOLOGY-REVIEW.md` | +119 −3 | L194, L199, L740-741, L862-976 |
| modified | `README.md` | +7 −4 | L111, L114-115, L164-167 |
| modified | `VERIFICATION.md` | +101 −131 | L7-107, removed after L951 |
| modified | `pyproject.toml` | +25 −4 | L6-18, removed after L20, L23-32, L34, L38 |
| modified | `uv.lock` | +102 −1 | L5-10, L86-94, L107, L110, L119, L128, L137, L165-187, L288-301, L311-321, L346-366, L524-536 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +7 −2 | L19-23, L60-61 |
| modified | `.github/workflows/work-pc-pack.yml` | +6 −1 | L5-6, L38-41 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +10 −4 | L12, L40-45, L70, L87, L201 |
| added | `apps/issuer-library/credit_os/__init__.py` | +1 −0 | L1 |
| added | `apps/issuer-library/credit_os/cashflow.py` | +1739 −0 | L1-1739 |
| added | `apps/issuer-library/credit_os/evidence.py` | +300 −0 | L1-300 |
| added | `apps/issuer-library/credit_os/handoff_fields.py` | +524 −0 | L1-524 |
| added | `apps/issuer-library/credit_os/source.py` | +295 −0 | L1-295 |
| modified | `apps/issuer-library/credit_os/store.py` | +468 −2804 | L4-5, removed after L8, removed after L10, removed after L11, L14, L16, L19-252, L255-484, removed after L488, removed after L570, removed after L575, removed after L606, removed after L720, removed after L950, removed after L1018, removed after L1557 |
| modified | `apps/issuer-library/engine/run_workflow.py` | +0 −4 | removed after L7 |
| modified | `apps/issuer-library/fixtures/build_synthetic_run.py` | +28 −22 | removed after L17, removed after L22, L31-34, L63, L72, L98, L101, L104, L114, L125, L131-135, L142, L144-145, L151, L153, L159-160, L166, L174-176, L178 |
| modified | `apps/issuer-library/fixtures/synthetic-new-format/README.md` | +5 −0 | L13-17 |
| added | `apps/issuer-library/fixtures/synthetic-new-format/SYNTHETIC-CP-3C.md` | +54 −0 | L1-54 |
| added | `apps/issuer-library/fixtures/synthetic-new-format/SYNTHETIC-CP-6.md` | +92 −0 | L1-92 |
| modified | `apps/issuer-library/packaging/runtime.py` | +7 −4 | L66-71, L201 |
| added | `apps/issuer-library/pyproject.toml` | +19 −0 | L1-19 |
| modified | `apps/issuer-library/update_library.py` | +1 −5 | L3, removed after L30 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/QUALITY-GATE.md` | +41 −4 | L11, L18-21, L25-31, L48-72, L107-110 |
| deleted | `docs/VERIFICATION-ARCHIVE.md` | +0 −499 | — |
| deleted | `docs/design/mockups/module-report-1280.png` | binary | — |
| deleted | `docs/design/mockups/module-report-1440.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/01-library.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/02-run-overview.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/03-module-findings.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/04-calendar.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/05-forecast.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/06-evidence.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/07-reports.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/08-report-reader.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/09-run-activity.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/10-context-form-purpose.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/11-context-form-sources.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/12-context-form-check.png` | binary | — |
| deleted | `docs/design/screenshots/2026-11-10/README.md` | +0 −32 | — |
| deleted | `docs/reuse/selected-methods/CP-3B_RUNBOOK.md` | +0 −170 | — |
| deleted | `docs/reuse/selected-methods/CP-3B_SCHEMA_REFERENCE.md` | +0 −54 | — |
| modified | `docs/reuse/selected-methods/CPOS_REGISTER_SCOPE.md` | +5 −1 | L10-13, L52 |
| deleted | `docs/reuse/selected-methods/REF_CP-3B_STEPS.md` | +0 −275 | — |
| modified | `docs/reuse/selected-methods/manifest.json` | +109 −128 | L9-10, L25-26, L32-34, L40-42, L51-52, L69-70, L76-78, L99-100, L115-117, L149-151, L158-159, L166-167, L174-176, L259-261, L289-290, L297-299, L306-307, L314-316, L344-345, L352-354, L382-384, removed after L528, removed after L550, removed after L577, L625-626, L644-645, L699-700, L799-800, L818-819, L831-832, L958-959, L965-966, L975-976, L985-986, L992-993, L999-1000, L1006-1007, L1022-1023, L1097, L1099-1124, L1127 |
| deleted | `docs/reuse/selected-methods/runtime/before-retained-planning-PINS.json` | +0 −221 | — |
| deleted | `docs/reuse/selected-methods/runtime/before-retained-planning-cpos.py` | +0 −851 | — |
| deleted | `docs/reuse/selected-methods/runtime/before-retained-planning-handoff_delivery.py` | +0 −625 | — |
| deleted | `docs/reuse/selected-methods/runtime/before-retained-planning-markdown_delivery.py` | +0 −352 | — |
| deleted | `docs/reuse/selected-methods/runtime/before-retained-planning-registry.py` | +0 −496 | — |
| deleted | `docs/reuse/selected-methods/runtime/cp2d-before-maturity-scope.md` | +0 −45 | — |
| deleted | `docs/reuse/selected-methods/runtime/cpos-before-deliverable-comparison.py` | +0 −641 | — |
| deleted | `docs/reuse/selected-methods/runtime/cpos-before-earnings-presentation.py` | +0 −826 | — |
| deleted | `docs/reuse/selected-methods/runtime/cpos-before-handoff-orchestration.py` | +0 −305 | — |
| deleted | `docs/reuse/selected-methods/runtime/cpos-before-model-publication.py` | +0 −593 | — |
| deleted | `docs/reuse/selected-methods/runtime/cpos-before-retained-handoffs.py` | +0 −552 | — |
| deleted | `docs/reuse/selected-methods/runtime/handoff-delivery-before-comparison.py` | +0 −460 | — |
| deleted | `docs/reuse/selected-methods/runtime/handoff-delivery-before-cpos-verification.py` | +0 −367 | — |
| deleted | `docs/reuse/selected-methods/runtime/handoff-delivery-before-earnings-presentation.py` | +0 −600 | — |
| deleted | `docs/reuse/selected-methods/runtime/handoff-delivery-before-model-publication.py` | +0 −384 | — |
| deleted | `docs/reuse/selected-methods/runtime/liquidity-bridge-before-maturity-scope.md` | +0 −8 | — |
| deleted | `docs/reuse/selected-methods/runtime/tdg-model-original-builder.py` | +0 −114 | — |
| added | `docs/rulings/2026-11-15-full-assessment-cp3c-cp6a.md` | +108 −0 | L1-108 |
| deleted | `docs/superpowers/plans/2026-11-09-credit-os-static-pages.md` | +0 −177 | — |
| deleted | `docs/superpowers/plans/2026-11-09-inbox-automation.md` | +0 −619 | — |
| deleted | `docs/superpowers/plans/2026-11-09-run-report-phase-a.md` | +0 −340 | — |
| deleted | `docs/superpowers/plans/2026-11-11-existing-issuer-run-start.md` | +0 −412 | — |
| deleted | `docs/superpowers/plans/2026-11-11-staged-run-start.md` | +0 −442 | — |
| deleted | `docs/superpowers/plans/2026-11-12-cp2g-facility-schedule.md` | +0 −313 | — |
| deleted | `docs/superpowers/plans/2026-11-13-signal-1-store-and-ingest.md` | +0 −493 | — |
| deleted | `docs/superpowers/plans/2026-11-13-signal-2-service-and-feed-pages.md` | +0 −473 | — |
| deleted | `docs/sweeps/2026-11-10-wiring/CONTRACT.md` | +0 −19 | — |
| deleted | `docs/sweeps/2026-11-10-wiring/REPORT.md` | +0 −44 | — |
| deleted | `docs/sweeps/2026-11-10-wiring/goal.txt` | +0 −4 | — |
| deleted | `docs/sweeps/2026-11-10/CONTRACT.md` | +0 −16 | — |
| deleted | `docs/sweeps/2026-11-10/REPORT.md` | +0 −131 | — |
| deleted | `docs/sweeps/2026-11-10/goal.txt` | +0 −5 | — |
| modified | `docs/templates/README.md` | +1 −1 | L298 |
| modified | `docs/templates/context-form.html` | +4 −4 | L10, L733, L747, L758 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| added | `src/deploy_vii/context.py` | +980 −0 | L1-980 |
| modified | `src/deploy_vii/contracts.py` | +4 −2 | L53-54, L56-57 |
| modified | `src/deploy_vii/distressed_figures.py` | +2 −2 | L4, L62 |
| modified | `src/deploy_vii/execution.py` | +2 −2 | L54-55 |
| added | `src/deploy_vii/financial_series.py` | +442 −0 | L1-442 |
| added | `src/deploy_vii/liquidity_series.py` | +218 −0 | L1-218 |
| modified | `src/deploy_vii/methods/cp2e.md` | +2 −2 | L39-40 |
| modified | `src/deploy_vii/methods/cp4c.md` | +1 −1 | L40 |
| added | `src/deploy_vii/platform_io.py` | +127 −0 | L1-127 |
| modified | `src/deploy_vii/readiness.py` | +1 −1 | L419 |
| modified | `src/deploy_vii/report_view.py` | +3 −3 | L1954, L3056, L3082 |
| added | `src/deploy_vii/restructuring_series.py` | +258 −0 | L1-258 |
| modified | `src/deploy_vii/table_markdown.py` | +5 −0 | L31-35 |
| added | `src/deploy_vii/trailing_period.py` | +32 −0 | L1-32 |
| modified | `src/deploy_workflow/context.py` | +9 −976 | L1, L3-5, removed after L7, removed after L8, L10-11, L13-15 |
| modified | `src/deploy_workflow/credit_os_catalogue.py` | +1 −1 | L244 |
| modified | `src/deploy_workflow/earnings_workflow.py` | +9 −3924 | L1-2, L4-6, removed after L10, removed after L11, removed after L12, L15, removed after L26, removed after L28, L33, removed after L34, L36, removed after L37, removed after L59, removed after L91, removed after L97, removed after L101, removed after L159, removed after L168, removed after L175, removed after L338, L689 |
| modified | `src/deploy_workflow/financial_series.py` | +8 −437 | L1, L3-5, L8, L10-11, L13 |
| added | `src/deploy_workflow/http_base.py` | +399 −0 | L1-399 |
| modified | `src/deploy_workflow/inbox/runs.py` | +2 −1 | L88-89 |
| modified | `src/deploy_workflow/liquidity_series.py` | +8 −213 | L1, L3-5, L8, L10-11, L13 |
| modified | `src/deploy_workflow/owner_workflow.py` | +10 −194 | L19-24, removed after L26, removed after L27, L37, removed after L91, removed after L100, L111, L137-138, removed after L300, removed after L774, removed after L3683 |
| modified | `src/deploy_workflow/owners/cp0_attachments.py` | +0 −3 | removed after L29 |
| modified | `src/deploy_workflow/owners/cp1b.py` | +6 −7 | L7-9, L12-14 |
| modified | `src/deploy_workflow/owners/cp1c.py` | +2 −31 | removed after L128, removed after L1587, L2644, L2646, removed after L2669, removed after L2674, removed after L3038 |
| modified | `src/deploy_workflow/owners/cp1d.py` | +0 −17 | removed after L1880, removed after L2100, removed after L2111, removed after L2379 |
| modified | `src/deploy_workflow/owners/cp2a.py` | +12 −36 | L7, removed after L58, removed after L71, L78-84, removed after L88, removed after L314, removed after L1436, L1438-1439, L1619-1620, removed after L1695 |
| modified | `src/deploy_workflow/owners/cp2d.py` | +8 −50 | L14, L222, removed after L1777, L1779-1780, removed after L2036, removed after L2047, removed after L2324, removed after L2337, removed after L2408, L2412-2415 |
| modified | `src/deploy_workflow/owners/cp2e.py` | +4 −70 | L8, L10, removed after L38, L478-479, removed after L2295 |
| modified | `src/deploy_workflow/owners/cp2g.py` | +2 −56 | removed after L62, removed after L84, removed after L90, removed after L91, removed after L995, L1348, removed after L2679, L2681, removed after L2813, removed after L3000 |
| modified | `src/deploy_workflow/owners/cp2h.py` | +3 −30 | removed after L108, removed after L110, removed after L111, L1953, L2069, removed after L2123, removed after L2330, L2332 |
| modified | `src/deploy_workflow/owners/cp3.py` | +3 −81 | L1, L5, L14, removed after L17, removed after L18, removed after L19, removed after L21, removed after L23 |
| modified | `src/deploy_workflow/owners/cp3c.py` | +2 −95 | L16, removed after L53, removed after L636, removed after L2126, removed after L2545, L2985 |
| modified | `src/deploy_workflow/owners/cp3d.py` | +11 −80 | L12, removed after L15, removed after L24, L40, removed after L44, L69-76, removed after L1272, L2835 |
| modified | `src/deploy_workflow/owners/cp4.py` | +2 −39 | L4, removed after L13, L18, removed after L133 |
| modified | `src/deploy_workflow/owners/cp4c.py` | +9 −61 | removed after L87, L94-101, removed after L104, removed after L428, removed after L1302, L3519 |
| modified | `src/deploy_workflow/owners/cp5.py` | +6 −47 | L5-6, L13-16, removed after L23, removed after L28, removed after L30, removed after L36, removed after L44, removed after L50 |
| modified | `src/deploy_workflow/owners/cp8.py` | +2 −64 | L7, removed after L54, L2443 |
| modified | `src/deploy_workflow/owners/cpl10.py` | +1 −66 | removed after L48, removed after L131, removed after L169, L1619 |
| modified | `src/deploy_workflow/owners/cpos.py` | +6 −255 | L1, L10-12, L33-34, removed after L35, removed after L57, removed after L1226, removed after L1228, removed after L1268 |
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +1 −1 | L753 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +184 −2308 | L24-25, L29, removed after L30, L34, removed after L43, removed after L47, L71, removed after L77, L93, removed after L97, L103-171, removed after L173, L176, removed after L181, L186-253, removed after L283, removed after L308, removed after L448, removed after L522, removed after L546, L667-692, L1077, L1267, removed after L1570, L1704-1714, L1718 |
| added | `src/deploy_workflow/owners/cpos_launch_methods.py` | +175 −0 | L1-175 |
| added | `src/deploy_workflow/owners/cpos_launch_prompts.py` | +722 −0 | L1-722 |
| added | `src/deploy_workflow/owners/cpos_launch_review.py` | +173 −0 | L1-173 |
| added | `src/deploy_workflow/owners/cpos_launch_tables.py` | +1291 −0 | L1-1291 |
| modified | `src/deploy_workflow/owners/pins.py` | +22 −0 | L21, L514-534 |
| modified | `src/deploy_workflow/platform_io.py` | +9 −113 | L1, L3-6, L8, L10-11, L13 |
| modified | `src/deploy_workflow/prose_checks.py` | +9 −0 | L204-212 |
| modified | `src/deploy_workflow/research/dossier.py` | +3 −5 | L16-18, removed after L86 |
| modified | `src/deploy_workflow/restructuring_series.py` | +8 −253 | L1, L3-5, L8, L10-11, L13 |
| modified | `src/deploy_workflow/run_start/service.py` | +44 −273 | L5-7, L25, removed after L98, removed after L99, removed after L100, L107, L111-112, removed after L115, removed after L133, L159, removed after L160, L163-164, L167, L170, removed after L181, L183, L186, L189, L192, L198, L201, L212, L222, L224, L227, L230, L233, L236, L240, L249, L260, L268, L271, L274, L277, L282, L290, L298, L306, L311, L339-342, L389, L416-417 |
| modified | `src/deploy_workflow/signal/service.py` | +39 −223 | L5-8, removed after L41, removed after L43, L51, L55-58, removed after L78, removed after L79, L84-88, L90-94, L97, removed after L124, L307, removed after L308, L311-312, L329-330, L334, L337-339, L341-342, removed after L347, L349, L353, L355, L359-361, removed after L396, L409, L413 |
| modified | `src/deploy_workflow/trailing_period.py` | +8 −27 | L1, L3-5, L8, L10-11, L13 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +151 −8 | L86-87, L89-90, L109-112, L594-604, L653, L1398, L1405, L1407-1408, L1473-1475, L1478, L2902-2904, L2924, L8497-8615 |
| modified | `tests/test_cpos_register_scope.py` | +42 −7 | L50-52, L54, L246-263, L279-291, L301-304, L406-408 |
| modified | `tests/test_credit_os_catalogue.py` | +0 −2 | removed after L5, removed after L13 |
| modified | `tests/test_credit_os_chips.py` | +0 −2 | removed after L6, removed after L40 |
| modified | `tests/test_credit_os_store.py` | +1 −3 | removed after L4, removed after L7, L9, removed after L12 |
| modified | `tests/test_downside_follows_forward_model.py` | +1 −4 | removed after L10, L16, removed after L22 |
| added | `tests/test_http_base.py` | +596 −0 | L1-596 |
| modified | `tests/test_inbox_activity.py` | +4 −0 | L22-24, L153 |
| modified | `tests/test_issuer_library_packaging.py` | +22 −6 | L10-11, L114-115, L117, L144, L312-314, L320-332 |
| modified | `tests/test_library_changes_browser.py` | +0 −2 | removed after L6, removed after L14 |
| added | `tests/test_library_full_assessment_browser.py` | +102 −0 | L1-102 |
| modified | `tests/test_library_page_browser.py` | +0 −1 | removed after L30 |
| modified | `tests/test_library_reader_refs.py` | +4 −2 | removed after L14, removed after L21, L45-48 |
| added | `tests/test_methodology_selection.py` | +167 −0 | L1-167 |
| modified | `tests/test_quality_gate.py` | +159 −0 | L3, L32-189 |
| modified | `tests/test_run_start_service.py` | +14 −6 | L30, L215-221, L628-629, L730, L807, L830, L834 |
| modified | `tests/test_run_start_submissions.py` | +5 −1 | L41-43, L975, L1445 |
| modified | `tests/test_signal_service.py` | +16 −22 | L191-192, L194-197, removed after L198, L200-203, L205-207, L552-554 |
| modified | `tests/test_update_library.py` | +0 −2 | removed after L4, removed after L12 |
| modified | `tests/test_work_pc_delta.py` | +191 −0 | L175-365 |

### tools

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tools/cp1_check_proof.py` | +0 −2 | removed after L16, removed after L20 |
| modified | `tools/quality_gate.py` | +173 −13 | L3, L7-10, L13-15, L23, L25, L37-40, L59-61, L63-65, L110-222, L321-340, L346-358, L361-362, L364, L372, L382, L385, L392 |
| modified | `tools/work_pc_delta.py` | +71 −4 | L11, L16-18, L32, L37, L54-55, L266-310, L315, L340-345, L440-447, L450-452 |
