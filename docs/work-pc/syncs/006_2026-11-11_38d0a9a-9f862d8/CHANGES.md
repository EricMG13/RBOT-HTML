# Changes for the work PC

From `38d0a9acf372` (the version the work PC last adapted) to `9f862d8267fe` (2026-11-11T22:16:41Z). 43 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `48a3d11` 2026-11-11 docs(work-pc): change pack for 38d0a9a
- `9f862d8` 2026-11-11 Issuer library presentation to the reader ruling (stacked on #45) (Merge pull request #47 from EricMG13/claude/library-layout-637b87)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `README.md` | +9 −6 | L87-95 |
| modified | `VERIFICATION.md` | +34 −0 | L7-40 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +3 −2 | L34, L49-50 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +19 −8 | L22-37, L58, L108-109 |
| modified | `apps/issuer-library/credit_os/SOURCE.md` | +27 −2 | removed after L51, L221-247 |
| modified | `apps/issuer-library/credit_os/store.py` | +343 −249 | L97-107, removed after L431, removed after L1064, removed after L1077, removed after L1091, L1176, L1183-1184, L1186-1188, L1190-1199, L2977-2990, L2996-2998, L3012-3015, L3212-3491, removed after L3505, L3519-3520, removed after L3528, L3533-3543, L3545, L3553, removed after L3566 |
| modified | `apps/issuer-library/credit_os/web/index.html` | +3 −3 | L17, L22, L25 |
| added | `apps/issuer-library/credit_os/web/reader.js` | +441 −0 | L1-441 |
| added | `apps/issuer-library/credit_os/web/reader.test.cjs` | +492 −0 | L1-492 |
| deleted | `apps/issuer-library/credit_os/web/report-adapter.css` | +0 −48 | — |
| deleted | `apps/issuer-library/credit_os/web/report-adapter.js` | +0 −92 | — |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +52 −57 | L7, L20, L24-25, L29, L33, L35, L38, L42, L78, removed after L251, L275, L285, L462-468, removed after L469, removed after L473, L476, removed after L483, removed after L484, removed after L503, L510, L551, L555-557, L562, L565-590 |
| modified | `apps/issuer-library/credit_os/web/screen.js` | +78 −80 | L42, L46, L51, L59, L69, L98, L186, L192, L271-273, L275, L287-288, removed after L292, L295, L302, L306-307, L334-356, L359-362, L364, L371-374, L382, L391, L456, L481-483, removed after L488, L512, L514, L518, L525-528, L535, L539, L548-549, L551, L556-557, L564-565, L575, L589, removed after L590, removed after L600, L605-606, L617, L710 |
| modified | `apps/issuer-library/credit_os/web/static-boot.js` | +3 −3 | L6, L19, L23 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +814 −629 | L18-46, L99, L104-106, L108-110, L112-113, L115-131, L133-198, L203-214, L311-313, L317-321, L393, L437-440, L442, L519, L590-591, L660, L740-741, L855-856, L862, L866-867, L869-872, removed after L873, L875-974, L976-1022, L1025-1028, L1030-1033, L1036-1144, L1146-1340, L1343-1353, removed after L1357, L1364, L1366, L1378, L1395, L1397-1398, L1400-1401, L1428, L1430, L1452-1456, L1498, L1500, L1507, L1509, removed after L1519, L1534, removed after L1536, removed after L1543, L1576-1578, L1584, L1599, L1602, L1604, L1607-1609, removed after L1716, removed after L1785, L1923, L1925-1926, L1930-1935, L1939-1941, removed after L1956, L1961, removed after L1964, L1983-1984, removed after L1988, L2089, L2092-2101, L2116, L2161-2164, removed after L2183, L2186, L2190, removed after L2247, removed after L2254, removed after L2263, L2277, L2284, L2301, L2307-2335, removed after L2337, removed after L2369, L2379-2456, L2459-2462, removed after L2464, L2467-2470, L2474, removed after L2478 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +308 −332 | L89, L91, removed after L115, removed after L131, removed after L149, removed after L158, L160, L164-165, removed after L171, L407, removed after L438, removed after L472, L475, L478-479, L495, L500-501, L508, L511, L514, L535-536, L551-552, L556-557, L561-595, L617-618, L647, removed after L657, L667, L669-672, L674-676, L693, L713-714, L725, L730, L746, removed after L747, L752-759, L779, L786, L792-799, L802, L804-818, removed after L823, L825-826, L831-861, removed after L863, L961, L974, L977, L990-992, L994, L996-997, L1001, L1003-1004, removed after L1005, L1043-1045, L1090, L1122-1130, L1134, removed after L1151, removed after L1153, L1165-1183, L1185-1239, L1242-1250, L1252-1254, L1257, L1259, removed after L1260, removed after L1268, L1271, removed after L1273, L1275, removed after L1282, L1284, L1296-1335, L1340-1341, L1343, L1350, L1352-1354, removed after L1357, L1359-1360, L1362, L1365, removed after L1371 |
| added | `apps/issuer-library/fixtures/build_synthetic_run.py` | +177 −0 | L1-177 |
| added | `apps/issuer-library/fixtures/synthetic-new-format/README.md` | +15 −0 | L1-15 |
| added | `apps/issuer-library/fixtures/synthetic-new-format/SYNTHETIC-CP-0.md` | +36 −0 | L1-36 |
| added | `apps/issuer-library/fixtures/synthetic-new-format/SYNTHETIC-CP-1.md` | +38 −0 | L1-38 |
| added | `apps/issuer-library/fixtures/synthetic-new-format/SYNTHETIC-CP-1A.md` | +62 −0 | L1-62 |
| added | `apps/issuer-library/fixtures/synthetic-new-format/SYNTHETIC-CP-2.md` | +57 −0 | L1-57 |
| added | `apps/issuer-library/fixtures/synthetic-new-format/SYNTHETIC-CP-2D.md` | +26 −0 | L1-26 |
| modified | `apps/issuer-library/update_library.py` | +80 −80 | L7-11, L17, L22, L36, L38, L49-50, L60-62, L66, L69, L71, L73, L102-104, L108, L126, L140-194, L200, L213 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/QUALITY-GATE.md` | +1 −1 | L68 |
| modified | `docs/templates/context-form.html` | +2 −2 | L598, L602 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/browser_probe_bridge.js` | +2 −2 | L3-4 |
| deleted | `tests/browser_probe_calendar.js` | +0 −19 | — |
| modified | `tests/browser_probe_gaps.js` | +11 −12 | L4-8, L10-13, L16, L19 |
| modified | `tests/browser_probe_index.js` | +8 −12 | L3, removed after L5, L7, L10-11, removed after L12, L15, L17-19 |
| added | `tests/browser_probe_inspector.js` | +28 −0 | L1-28 |
| modified | `tests/browser_probe_module_report.js` | +3 −2 | L13, L19-20 |
| added | `tests/browser_probe_narrow_tables.js` | +22 −0 | L1-22 |
| modified | `tests/browser_probe_overview.js` | +9 −36 | L3-5, L9, L11-15 |
| modified | `tests/browser_probe_structure.js` | +2 −2 | L3-4 |
| modified | `tests/library_fixtures.py` | +34 −3 | L84, L146-155, L160-162, L233-252 |
| modified | `tests/test_context_form.py` | +10 −3 | L94-95, L97-104 |
| modified | `tests/test_credit_os_catalogue.py` | +1 −2 | L251 |
| modified | `tests/test_credit_os_store.py` | +289 −153 | L9-10, L49, L57-58, L956, removed after L1000, L1003-1004, L1006-1029, L1031, L1035, L1038-1292 |
| modified | `tests/test_library_page_browser.py` | +295 −85 | L162-167, L212-215, L220-227, L230-257, L270-273, L278-283, L415-417, L436-439, L441-443, L446, L484-490, L509, L516-523, L525-527, L566-567, L571-573, L580-581, L863, L882, L896-899, L902, L905-907, L910-918, L922, L931-932, removed after L935, L937, L939-947, L951-952, L970-1137 |
| added | `tests/test_library_reader_refs.py` | +235 −0 | L1-235 |
| modified | `tests/test_run_start_page.py` | +6 −6 | L1319-1320, L1322-1325 |
| modified | `tests/test_update_library.py` | +125 −48 | removed after L2, removed after L40, L53, L64-65, L68, L71, L77, L79, L81-84, L98-124, L145, L201-226, L331, L334, L357, L359, L379-434 |
