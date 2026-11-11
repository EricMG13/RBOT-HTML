# Changes for the work PC

From `94f29dda33f2` (the version the work PC last adapted) to `38d0a9acf372` (2026-11-11T22:16:20Z). 33 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `f885d65` 2026-11-11 docs(work-pc): change pack for 94f29dd
- `38d0a9a` 2026-11-11 CP-OS: reader passages, prose checks, CP-8 presentation; retire the delivered report (Merge pull request #46 from EricMG13/claude/reader-engine-d46913)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `README.md` | +6 −6 | L12, L20-21, L71, L90-91 |
| modified | `VERIFICATION.md` | +40 −0 | L7-46 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/update_library.py` | +2 −0 | L93-94 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-reader-and-issuer-report.md` | +11 −0 | L224-234 |
| modified | `docs/templates/context-form.html` | +4 −1 | L1863-1866 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp0.md` | +1 −1 | L84 |
| modified | `src/deploy_vii/methods/cp1a.md` | +2 −1 | L14-15 |
| modified | `src/deploy_vii/methods/cp2.md` | +2 −1 | L27-28 |
| modified | `src/deploy_vii/methods/cp8.md` | +5 −1 | L14-18 |
| modified | `src/deploy_workflow/credit_os_catalogue.py` | +35 −5 | L236-258, L276-281, L300-304, L312 |
| modified | `src/deploy_workflow/credit_os_chips.py` | +54 −3 | L43-46, L179-209, L211-214, L217-219, L221-226, L416-420, L519 |
| modified | `src/deploy_workflow/handoff_delivery.py` | +26 −59 | L1-9, removed after L15, removed after L40, removed after L51, L142-143, removed after L603, removed after L607, L621-622, L628, L645, L653, L663, L667-669, L684-687, L732, removed after L744, removed after L754, L772 |
| modified | `src/deploy_workflow/inbox/scheduler.py` | +8 −5 | L429-431, L433-436, L440 |
| modified | `src/deploy_workflow/library_index.py` | +38 −15 | L9-13, L146-150, L152-155, L165-166, L168-171, L181, L201, L203, L207-210, L214, L240-241, removed after L435, L448-455 |
| modified | `src/deploy_workflow/markdown_delivery.py` | +0 −111 | removed after L10, removed after L33, removed after L728, removed after L1208, removed after L1209, removed after L1215 |
| modified | `src/deploy_workflow/owners/cpos.py` | +17 −10 | L144-146, L437, L514, L536, L542, L712, L730-735, L868, L879, L883 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +137 −162 | removed after L13, L22, L37, removed after L42, removed after L43, L71-75, L102-104, L189-194, L196-199, L228-229, L238-280, L282-320, L322, removed after L1337, L1340-1343, L1378-1379, L1389, removed after L1393, L1580-1581, L1586-1591, L1633-1636, L1638-1643, removed after L1646, L1663, L1665-1666, L1841-1842, removed after L1891, L2048, L2065 |
| added | `src/deploy_workflow/prose_checks.py` | +792 −0 | L1-792 |
| modified | `src/deploy_workflow/reader_summary.py` | +2 −158 | L1, removed after L3, removed after L4, removed after L6, removed after L10, removed after L29, L39, removed after L46 |
| modified | `src/deploy_workflow/run_start/service.py` | +11 −9 | L430, L432-435, L437, L439-443 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/fake_launcher.py` | +7 −3 | L52-58 |
| modified | `tests/library_fixtures.py` | +6 −3 | L84, L163, L170, L179-181 |
| added | `tests/test_cp8_comparison.py` | +132 −0 | L1-132 |
| modified | `tests/test_cpos_launch.py` | +295 −208 | L35-41, L400-410, L418-428, L430, L442-450, L698, L707-708, L712, L883-890, L925, L935-937, L1116-1155, L1157, L1163-1166, removed after L1167, L1169-1191, L1194, L1202-1206, L1209-1279, L1281, L1284-1290, L1293-1297, L1300-1308, L1311-1320, L1385-1387, L1531, L1544-1546, L1682, L1690, L1775, L1801, L1839, L1847, L1998-2000, L2030, L2195, L2262, L2270, L2275, L2598, L2961-2963, L2965, L3658-3694 |
| modified | `tests/test_credit_os_catalogue.py` | +51 −0 | L296-346 |
| modified | `tests/test_credit_os_chips.py` | +74 −0 | L756-829 |
| modified | `tests/test_inbox_runs.py` | +1 −1 | L164 |
| modified | `tests/test_inbox_scheduler.py` | +37 −8 | L57-58, L64-91, L105, L138-139, L312, L332, L613, L636 |
| modified | `tests/test_library_index.py` | +33 −2 | L62, L128-155, L168, L429-431 |
| added | `tests/test_prose_checks.py` | +534 −0 | L1-534 |
| modified | `tests/test_reader_summary.py` | +23 −170 | L1, L3, L5, L13, L17, L21-23, removed after L24, removed after L25, L27-37, L41, L44-46 |
| modified | `tests/test_run_start_page.py` | +2 −1 | L1315-1316 |
| modified | `tests/test_update_library.py` | +13 −2 | L99-109, L252, L254 |
