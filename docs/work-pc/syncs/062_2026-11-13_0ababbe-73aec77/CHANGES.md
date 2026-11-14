# Changes for the work PC

From `0ababbe51991` (the version the work PC last adapted) to `73aec77fb107` (2026-11-13T23:43:43Z). 30 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `ce18c8c` 2026-11-13 docs(work-pc): change pack for 0ababbe
- `73aec77` 2026-11-13 CP-1: Deploy V method (adapted), carrying-value basis, figures checked in code at acceptance (Merge pull request #111 from EricMG13/claude/cp1-deploy-v-method)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `METHODOLOGY-REVIEW.md` | +9 −0 | L750-758 |
| modified | `VERIFICATION.md` | +16 −26 | L7-22, removed after L970 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/store.py` | +25 −4 | L626-628, L728-730, L732, L746-747, L752-767 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +13 −0 | L2640-2652 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +2 −2 | L1426, L1515 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/reuse/selected-methods/manifest.json` | +49 −0 | L1088-1136 |
| added | `docs/reuse/selected-methods/skills/cp-1-canonical-data-foundation/SKILL.md` | +33 −0 | L1-33 |
| added | `docs/reuse/selected-methods/skills/cp-1-canonical-data-foundation/references/CP-1_RUNBOOK.md` | +28 −0 | L1-28 |
| added | `docs/reuse/selected-methods/skills/cp-1-canonical-data-foundation/references/CP-1_SCHEMA_REFERENCE.md` | +92 −0 | L1-92 |
| added | `docs/reuse/selected-methods/skills/cp-1-canonical-data-foundation/references/CP-1_SYSTEM_REFERENCE.md` | +60 −0 | L1-60 |
| added | `docs/reuse/selected-methods/skills/cp-1-canonical-data-foundation/references/REF_CP-1_STEPS.md` | +122 −0 | L1-122 |
| added | `docs/rulings/2026-11-13-cp1-deploy-v-method-and-acceptance-check.md` | +145 −0 | L1-145 |
| modified | `docs/templates/context-form.html` | +4 −5 | L1341, removed after L1382, L1460, L1464, L1827 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/changes.py` | +39 −16 | L35-49, L104, L438-444, L450, L453-455, L459, L461, L572-576, L597-601 |
| modified | `src/deploy_workflow/credit_os_catalogue.py` | +12 −1 | L187-194, L213-214, L239-240 |
| modified | `src/deploy_workflow/markdown_delivery.py` | +134 −33 | L39, L68-78, L553-557, L560-563, L565, L567-568, L574-644, L648-649, L664-666, L724-726, L753, L758, L767, L1030, L1032-1034, L1064-1067, L1085, L1088, L1190-1206, L1208 |
| modified | `src/deploy_workflow/model/handoff.py` | +51 −16 | L21, L76, L78, removed after L79, removed after L83, removed after L84, L86-87, L328-332, L335, L534-568, L822, L826, L843-845 |
| added | `src/deploy_workflow/owners/cpos_cp1_check.py` | +1398 −0 | L1-1398 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +299 −67 | L25-26, L30, removed after L33, L98-99, L185-195, removed after L323, L634, L638-639, L653, L656-657, L700, L712, L714-727, L805-822, L863, L877, L890, L899-901, L914, L1395-1396, L1471-1479, L1482, L1485-1493, L1495-1540, L1547-1548, L1559-1562, L1566-1571, L1577-1578, L1810-1865, L1872, L1874, L1895-1896, L2232-2313, L2463, L2466-2467, L2469, L2488, L3025-3026, L3146-3150, L3226 |
| modified | `src/deploy_workflow/run_expectations.py` | +2 −16 | removed after L350, removed after L405, L655, L679 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/run-expectations/outcome-key.json` | +3 −13 | L3, removed after L374, L406, L409 |
| modified | `tests/test_changes.py` | +87 −15 | L752-754, L1748, L1763-1764, L1767-1768, L1779, L1886-1887, L1911, L1930, L2076, L2078, L4410-4481 |
| modified | `tests/test_context_form.py` | +37 −0 | L396-432 |
| added | `tests/test_cpos_cp1_check.py` | +2053 −0 | L1-2053 |
| modified | `tests/test_cpos_launch.py` | +758 −25 | L37, L173-174, L177-178, L226-293, L526, L541, L633, L1988-1991, L2026, L2436-2753, L2868-2873, L2883, L3028-3030, L3032-3044, L3153-3156, L3179, L3181, L5347, L5349, L5749, L5753-5755, L5759, L5882, L5938, L5966-5974, L6725, L6727-6733, L6779-6781, L6785-6791, L8136-8387, L8409-8450 |
| modified | `tests/test_credit_os_catalogue.py` | +26 −0 | L346-371 |
| modified | `tests/test_credit_os_store.py` | +58 −3 | L376-380, L419, L440, L2319-2369 |
| modified | `tests/test_handoff_loop.py` | +71 −0 | L12-13, L375-443 |
| modified | `tests/test_library_index.py` | +8 −13 | L462-463, L465-469, L472 |

### tools

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tools/cp1_check_proof.py` | +134 −0 | L1-134 |
