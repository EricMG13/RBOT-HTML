# Changes for the work PC

From `37f891f008f2` (the version the work PC last adapted) to `395bf380f092` (2026-11-16T04:10:05Z). 34 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `cff0c8d` 2026-11-16 docs(work-pc): change pack for 37f891f
- `395bf38` 2026-11-16 Live module validation on GPT Sol medium: repairs, parked findings fixed, live re-test (Merge pull request #131 from EricMG13/claude/module-validation-testing-31a837)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +128 −139 | L7-134, removed after L973 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/evidence.py` | +117 −0 | L8, L222-336, L410 |
| modified | `apps/issuer-library/credit_os/web/evidence.js` | +47 −4 | L27, L342-381, L392, L395, L406, L409, L424, L435 |
| modified | `apps/issuer-library/credit_os/web/evidence.test.cjs` | +66 −0 | L632-697 |
| modified | `apps/issuer-library/credit_os/web/reader.js` | +8 −1 | L486-493 |
| modified | `apps/issuer-library/credit_os/web/reader.test.cjs` | +22 −1 | L6, L576-596 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +9 −0 | L1029-1037 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +29 −2 | L1006, L1008, L1192-1218 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +14 −14 | L1469, L1481, L1672, L1685-1686, L1711-1712, L1717, L1740-1742, L1746, L1760, L1766 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-reader-and-issuer-report.md` | +7 −0 | L200-206 |
| modified | `docs/rulings/2026-11-15-method-script-checks.md` | +4 −0 | L381-382, L516-517 |
| added | `docs/rulings/2026-11-15-module-validation-live-test.md` | +40 −0 | L1-40 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/handoff_delivery.py` | +110 −27 | L300-329, removed after L339, L344-348, L350-351, L360-432 |
| modified | `src/deploy_workflow/method_scripts_cp1.py` | +124 −19 | L12-25, L100-142, L163, L172-219, L221-223, L227-236, L268-269, L316-318 |
| modified | `src/deploy_workflow/method_scripts_cp1b.py` | +163 −23 | L12-22, L27-29, L34, L59, L77-138, L151, L188, L201-202, L256-334, L413-414 |
| modified | `src/deploy_workflow/method_scripts_cp3.py` | +23 −0 | L114-123, L130-142 |
| modified | `src/deploy_workflow/model/copilot_adapter.py` | +20 −0 | L644-663 |
| modified | `src/deploy_workflow/model/handoff.py` | +25 −3 | L1017, L1530-1532, L1536-1537, L1539-1540, L1550-1566 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +8 −1 | L62, L67, L1300, L1321-1325 |
| modified | `src/deploy_workflow/owners/cpos_launch_prompts.py` | +18 −5 | L305-315, L413, L565-570 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/fixtures/CP-1B-earnings_update-tdg-fy2024-t44-t46.md` | +45 −0 | L1-45 |
| added | `tests/fixtures/cp1_earnings_update_draft1_t49.md` | +46 −0 | L1-46 |
| added | `tests/fixtures/live_2026_11_15/distressed-CP-1-draft1.md` | +516 −0 | L1-516 |
| added | `tests/fixtures/live_2026_11_15/earnings_update-CP-1-draft1.md` | +575 −0 | L1-575 |
| added | `tests/fixtures/live_2026_11_15/earnings_update-CP-1-draft3-accepted.md` | +582 −0 | L1-582 |
| added | `tests/fixtures/live_2026_11_15/relative_value-CP-1-draft1.md` | +597 −0 | L1-597 |
| modified | `tests/model/test_copilot_adapter.py` | +128 −0 | L1406-1533 |
| modified | `tests/test_cpos_facilities.py` | +52 −0 | L506-557 |
| modified | `tests/test_cpos_launch.py` | +47 −7 | L1510-1512, L1519, L5077-5078, L9080-9082, L9085-9086, L9089, L9261-9295 |
| modified | `tests/test_handoff_delivery_table.py` | +71 −1 | L3-4, L7, L66-133 |
| modified | `tests/test_handoff_loop.py` | +80 −0 | L1698-1777 |
| modified | `tests/test_method_scripts.py` | +354 −0 | L13, L1779-2115, L2230-2245 |
| modified | `tests/test_method_scripts_rest.py` | +226 −1 | L773-780, L1259-1476 |
| modified | `tests/test_update_library.py` | +171 −0 | L3, L664-833 |
