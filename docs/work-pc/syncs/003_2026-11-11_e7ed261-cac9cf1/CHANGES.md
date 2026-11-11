# Changes for the work PC

From `e7ed261f178a` (the version the work PC last adapted) to `cac9cf1081dd` (2026-11-11T13:49:32Z). 43 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `584889a` 2026-11-11 docs(work-pc): change pack for e7ed261
- `cac9cf1` 2026-11-11 Run start page replaces the inbox watcher and folder drop (Merge pull request #44 from EricMG13/claude/no-nothing-6d5113)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `AGENTS.md` | +5 −5 | L54-58 |
| modified | `README.md` | +137 −124 | L3-5, L17-19, L25, L55, L88, L90-92, L94, L99, L105-107, L109-112, L114-124, L126, L128, L130-133, L135-137, L139-212, L214-230, removed after L234, L247-249, L258-259 |
| modified | `VERIFICATION.md` | +46 −0 | L7-52 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +5 −2 | L44-48 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +54 −47 | L3-4, L18-19, L26-27, L32, L34-38, L40-51, L53-56, L58-75, L77-78, L81-85, L117 |
| modified | `apps/issuer-library/credit_os/web/index.html` | +1 −1 | L17 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +20 −0 | L18-30, L987-993 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +12 −4 | L1293, L1309-1315, L1320, L1323, L1386, L1391 |
| modified | `apps/issuer-library/packaging/runtime.py` | +16 −12 | L67, L98, L101-105, L107-108, L110, L114, L120-121, L123, L125, L162 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/rulings/2026-11-11-run-start-submit.md` | +14 −0 | L1-14 |
| added | `docs/superpowers/plans/2026-11-11-staged-run-start.md` | +442 −0 | L1-442 |
| added | `docs/superpowers/specs/2026-11-11-staged-run-start-design.md` | +252 −0 | L1-252 |
| modified | `docs/templates/README.md` | +6 −2 | L299-303, L320 |
| modified | `docs/templates/context-form.html` | +901 −409 | L5, L91, L93-100, removed after L198, L203-205, L272, L309-310, removed after L318, L329-330, L333-334, L336-347, L351-367, L369, L371, L375, L387, L390, L394, L396, L405, L408-410, L412-416, removed after L417, L460-466, L494, L496, L499-505, L509, L511, L513-515, L518-519, L522-524, L532-546, L620, L633-636, L688-698, L715, L717-723, L726-730, L732, L734-735, L898, L962-963, L988, L990, L997-998, L1001, L1076-1082, L1089-1107, L1156, L1169, removed after L1191, L1201-1202, L1206-1212, L1218, L1221-1223, L1225-1227, L1229-1231, L1233-1244, L1246-1272, L1276-1279, L1281-1282, L1286-1287, L1296, L1308-1318, L1327-1328, L1330-1331, L1335-1339, L1348, L1351-1352, L1365-1368, L1371-1372, L1410, L1464, L1471, L1507-1508, L1510-1511, L1527-1529, L1558-1560, removed after L1568, L1581-1585, L1598, L1600-1605, L1608, L1612, L1619, L1623-1802, L1818-1892, L1895-2054, removed after L2055, L2057-2102, L2104-2114, L2116-2118, removed after L2119, L2121-2133, L2153, L2165-2179, L2181, L2186, L2207-2208, L2216, L2221-2226, L2230, L2234-2235, L2238-2239, L2241, L2244-2251, L2258, L2263, L2271-2275, L2282-2285, removed after L2287, L2290, L2305, L2343-2354, L2356, L2373, L2397, L2403-2408, L2419-2421, L2424, L2427, L2430, L2434, L2437, L2452, L2461-2463, L2465-2470, L2472-2473, L2491-2503, L2505-2506, L2508, removed after L2513, L2520-2521, L2525-2526 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/context.py` | +11 −0 | L55-57, L280-286, L297 |
| modified | `src/deploy_workflow/inbox/activity.py` | +4 −3 | L17, L28, L31, L122 |
| deleted | `src/deploy_workflow/inbox/drops.py` | +0 −440 | — |
| modified | `src/deploy_workflow/inbox/filing.py` | +1 −1 | L12 |
| added | `src/deploy_workflow/inbox/layout.py` | +75 −0 | L1-75 |
| modified | `src/deploy_workflow/inbox/runs.py` | +31 −41 | L17-18, L26-27, L48-53, L90, L144-155, L165, L175-178, L184, L203, L211 |
| renamed | `src/deploy_workflow/inbox/watcher.py` → `src/deploy_workflow/inbox/scheduler.py` | +216 −275 | L1-13, L18, L20, L23, L25, L29, L33, removed after L35, L37-38, L40, removed after L43, L45-50, L52, L56-59, removed after L68, L96, L105, L109, removed after L111, L114, L130-131, L133-146, L149, L192-215, L217-305, L341, L369-372, L374-377, removed after L378, L387, removed after L390, L457, removed after L472, removed after L498, L510-527, L529-542, L559-563, L580, removed after L583 |
| modified | `src/deploy_workflow/inbox/startup.py` | +29 −23 | L1, L13, L23, L25-26, L36, L40, L45, L53, L58, L60-63, L85, L89, L107-114, L134-137, L157, removed after L162 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +58 −13 | L379-410, L1598-1611, L1733, L1743-1750, L1755, removed after L1758, L1974, L2022 |
| added | `src/deploy_workflow/run_start/__init__.py` | +0 −0 | — |
| added | `src/deploy_workflow/run_start/__main__.py` | +7 −0 | L1-7 |
| added | `src/deploy_workflow/run_start/service.py` | +582 −0 | L1-582 |
| added | `src/deploy_workflow/run_start/submissions.py` | +578 −0 | L1-578 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/inbox_fixtures.py` | +165 −0 | L1-165 |
| modified | `tests/test_context_form.py` | +54 −2 | L19, L26, L30-35, L175-220 |
| added | `tests/test_context_module_options.py` | +37 −0 | L1-37 |
| modified | `tests/test_cpos_launch.py` | +118 −0 | L8, L17, L3492-3607 |
| modified | `tests/test_inbox_activity.py` | +8 −1 | L16, L441-447 |
| deleted | `tests/test_inbox_drops.py` | +0 −601 | — |
| modified | `tests/test_inbox_filing.py` | +1 −1 | L13 |
| added | `tests/test_inbox_layout.py` | +51 −0 | L1-51 |
| modified | `tests/test_inbox_runs.py` | +49 −40 | L18, removed after L25, removed after L151, removed after L209, L408-455 |
| renamed | `tests/test_inbox_watcher.py` → `tests/test_inbox_scheduler.py` | +358 −725 | L1, removed after L12, removed after L13, removed after L19, L28-41, L44-45, L47, removed after L48, L54, L57, L60-61, removed after L62, L73, L76-77, L81-82, removed after L83, L85-105, L114, L116, L118, L125, L127, L129, L139-140, L142, L149-154, L165, L167-169, L177-178, L184, L190, L199-200, L220, L228-230, L235-236, L240-243, L249-251, L254, L259, L262, L267, L277-278, removed after L281, L289-290, L300-302, L310, L312, L331, L337, L344-345, L348-350, L362, L365, L369, L381, L384-385, L388-389, L392, L394, L402, removed after L443, removed after L448, L450-451, L456, removed after L464, L466, L468, L477, L484-485, L493, L498, L512-513, L535, L537, L560, L562, L570-571, L595-596, L604-606, L608-609, removed after L617, L628, L630, L655, L657, L666, removed after L676, L702, L709, L711-714, L717, removed after L721, L731, L760, L762, L768, removed after L774, L783, L787, L789, L792, L796, L820, removed after L830, L848, L852, removed after L855, L870-871, L873-876, L878, L893, L895, L936, L938, L964, L977, L996, L1011, L1013, removed after L1022, L1025-1026, L1029, L1044, L1051-1052, L1062, L1066-1067, L1078-1244 |
| modified | `tests/test_issuer_library_packaging.py` | +31 −11 | L50, L53-54, L183, L185-186, L188, L197-220 |
| modified | `tests/test_library_page_browser.py` | +22 −34 | removed after L13, L753, L789-809 |
| added | `tests/test_run_start_page.py` | +1524 −0 | L1-1524 |
| added | `tests/test_run_start_scheduler.py` | +623 −0 | L1-623 |
| added | `tests/test_run_start_service.py` | +826 −0 | L1-826 |
| added | `tests/test_run_start_submissions.py` | +916 −0 | L1-916 |
