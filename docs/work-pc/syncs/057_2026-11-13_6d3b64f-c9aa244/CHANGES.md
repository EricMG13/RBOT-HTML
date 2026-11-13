# Changes for the work PC

From `6d3b64f15242` (the version the work PC last adapted) to `c9aa24401a6e` (2026-11-13T22:40:02Z). 31 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `985e191` 2026-11-13 docs(work-pc): change pack for 6d3b64f
- `c9aa244` 2026-11-13 Fix three quality defects: checker messages, dropped values on repair, Copilot summarising (Merge pull request #103 from EricMG13/claude/quality-defects-appendix-cpdr)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `AGENTS.md` | +3 −2 | L61-63 |
| modified | `METHODOLOGY-REVIEW.md` | +17 −0 | L835-851 |
| modified | `VERIFICATION.md` | +19 −43 | L7-25, removed after L968 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/store.py` | +5 −7 | L814, L816-818, L820 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/reuse/selected-methods/CPOS_REGISTER_SCOPE.md` | +48 −0 | L1-48 |
| modified | `docs/reuse/selected-methods/manifest.json` | +8 −0 | L1087-1094 |
| modified | `docs/rulings/2026-11-11-reader-and-issuer-report.md` | +15 −2 | L59-61, L122-123, L169-171, L356-362 |
| added | `docs/rulings/2026-11-13-appendix-and-routing-scope.md` | +118 −0 | L1-118 |
| added | `docs/sweeps/2026-11-13-optimisation-review/REPORT.md` | +142 −0 | L1-142 |
| added | `docs/sweeps/2026-11-13-optimisation-review/appendix-inventory.md` | +439 −0 | L1-439 |
| added | `docs/sweeps/2026-11-13-optimisation-review/findings.json` | +938 −0 | L1-938 |
| added | `docs/sweeps/2026-11-13-optimisation-review/frontend-changes-needed.md` | +111 −0 | L1-111 |
| added | `docs/sweeps/2026-11-13-optimisation-review/module-scripts-inventory.tsv` | +59 −0 | L1-59 |
| added | `docs/sweeps/2026-11-13-optimisation-review/pathway-tiers-proposal.md` | +411 −0 | L1-411 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/model/adapter.py` | +3 −0 | L41, L119-120 |
| modified | `src/deploy_workflow/model/copilot.py` | +89 −0 | L11, L14, L30, L44-61, L226-293 |
| modified | `src/deploy_workflow/model/copilot_adapter.py` | +44 −1 | L11, L39, L66, L139, L623-654, L794-797, L841-844 |
| modified | `src/deploy_workflow/model/handoff.py` | +318 −9 | L15, L19, L45-46, L56, L61, L73, L77-78, L95-97, L376-384, L405, L553, L555-582, L590-596, L598, L604-659, L666-669, L674-676, L678-680, L761, L784-786, L791-801, L831-838, L905-907, L968-1121, L1181-1185, L1205, L1222, L1302-1306, L1309 |
| modified | `src/deploy_workflow/model/record.py` | +40 −5 | L38, L126-144, L232-246, L640-641, L670-671, L732 |
| modified | `src/deploy_workflow/model/turn.py` | +27 −0 | L221-247 |
| modified | `src/deploy_workflow/owners/cpos.py` | +88 −6 | L83, L292-293, L311-372, L601-606, L774-779, L783-787, L831, L849, L862, L879, L891, L1078 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +474 −21 | L14, L30, L35, L68, L76, L82, L100, L108, L114, L153-159, L304, L863-865, L1155-1159, L1431-1470, L1478, L1514-1518, L1539-1540, L1554-1555, L1611-1624, L1629, L1632, removed after L1720, L1722-1723, L1742, L1855-1897, L1919-1922, L2315-2433, L2470-2471, L2794, L2990, L3211-3416, L3434, L3643, L3650, L3654 |
| modified | `src/deploy_workflow/prose_checks.py` | +154 −3 | L37, L887-904, L1003, L1005-1006, L1028-1029, L1038, L1069-1197 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/model/_compaction.py` | +121 −0 | L1-121 |
| modified | `tests/model/test_copilot_adapter.py` | +211 −0 | L1195-1405 |
| modified | `tests/model/test_copilot_parse.py` | +129 −0 | L285-413 |
| modified | `tests/test_cpos_launch.py` | +683 −35 | L35, L54, L388, L390-391, L518-528, L565, L611-621, L626, L2084-2087, L2473-2477, L2479, L2481, L2485-2486, L2488-2489, L2491, L2496-2497, L2499, L5174-5182, L5186-5194, L5202-5259, L5264, L5311, L5316-5321, L5326-5343, L5457-5523, L5535, L5887, L6892-7355 |
| added | `tests/test_cpos_register_scope.py` | +637 −0 | L1-637 |
| modified | `tests/test_credit_os_store.py` | +16 −2 | L882-896, removed after L907, L910 |
| modified | `tests/test_handoff_loop.py` | +815 −1 | L17, L19, L814-1626 |
| modified | `tests/test_run_start_service.py` | +9 −1 | L490-498 |
