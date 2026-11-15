# Changes for the work PC

From `250aa050c1b3` (the version the work PC last adapted) to `1cf9738a7097` (2026-11-15T22:55:53Z). 37 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `256101a` 2026-11-15 docs(work-pc): change pack for 250aa05
- `1cf9738` 2026-11-15 Lite, Full and Deep credit assessments; a hard cap per pathway (Merge pull request #129 from EricMG13/claude/busy-dijkstra-bgex9m)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `AGENTS.md` | +3 −2 | L73-75 |
| modified | `METHODOLOGY-REVIEW.md` | +14 −0 | L960-973 |
| modified | `README.md` | +15 −10 | L131, L136-138, L144, L163-168, L248, L273, L276-277 |
| modified | `VERIFICATION.md` | +39 −53 | L7-45, removed after L984 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +2 −1 | L63-64 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +8 −7 | L134-135, L141, L148, L162, L165-167 |
| modified | `apps/issuer-library/credit_os/web/reader.js` | +1 −0 | L470 |
| modified | `apps/issuer-library/credit_os/web/reader.test.cjs` | +1 −0 | L269 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-run-start-submit.md` | +5 −0 | L46-50 |
| added | `docs/rulings/2026-11-15-pathway-tiers-and-caps.md` | +168 −0 | L1-168 |
| modified | `docs/templates/context-form.html` | +23 −17 | L659, L735, L750, L760, L790, L792-799, L899, L1869-1870, L1979, L2059, L2155-2156, L2158, L2600, L2613 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/contracts.py` | +26 −0 | L45, L82-90, L93-108 |
| modified | `src/deploy_vii/report_view.py` | +55 −10 | L507-522, L542-545, L547-549, L554, L556-558, removed after L559, L562-574, L680-681, L2703, L3003, L3005-3012, L3156-3158 |
| modified | `src/deploy_workflow/inbox/activity.py` | +7 −4 | L18, L123-127, L159, removed after L162, removed after L179 |
| modified | `src/deploy_workflow/inbox/layout.py` | +1 −1 | L56 |
| modified | `src/deploy_workflow/inbox/runs.py` | +39 −7 | L13, L15, L17, L74-104, L229, removed after L234, L237, L239, L262, removed after L267, L271 |
| modified | `src/deploy_workflow/inbox/scheduler.py` | +12 −7 | removed after L28, L32, removed after L65, L105, removed after L295, L297-305, L325, removed after L406, removed after L558, removed after L577 |
| modified | `src/deploy_workflow/inbox/startup.py` | +31 −10 | removed after L8, L12, L36-51, removed after L56, L98, L103-115 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +46 −4 | L31-38, L914-924, L1191-1194, L1533-1549, L1735-1739, L1876 |
| modified | `src/deploy_workflow/portfolio_workbook.py` | +6 −4 | L3-4, L31-34 |
| modified | `src/deploy_workflow/run_expectations.py` | +1 −1 | L623 |
| modified | `src/deploy_workflow/run_start/service.py` | +36 −12 | L3-7, L47-48, L113, L153, L159, L209-228, L274, L277-279, L321, L339 |
| modified | `src/deploy_workflow/run_start/submissions.py` | +28 −10 | L27, L664-666, L671-678, L681-683, L694-695, L701, L704-706, L714, L717-719, L728, L748, L806 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/canned_provider_launcher.py` | +1 −1 | L106 |
| modified | `tests/inbox_fixtures.py` | +1 −1 | L143 |
| modified | `tests/test_changes.py` | +58 −33 | L98-122, L275, L296, L305, L321, L335, L345, L362, L365, L387, L391, L425, L429, L437, L447, L457, L470, L479, L491, L499, L514, L521, L559, L577, L599, L602, L608, L618, L621, L631, L638, L1874, L2067, L2095 |
| modified | `tests/test_context_form.py` | +35 −2 | L16, L91-114, L340-349 |
| modified | `tests/test_cpos_launch.py` | +185 −46 | L107-113, L137-142, L756, L764, L783, L803, L822, L844, L856, L872, L908, L922, L942, L959, L976, L1059, L1095, L1202, L1290, L1472, L1507-1509, L1511, L1549, L1752, L1857, L1896, L2856, L3184, L3312, L3325, L3343, L3544, L3570, L3652, L3923, L4403, L4535, L4778, L4835, L4885, L4927-4990, L6393, L6469, L6494, L6545, L7238, L7619, L7658, L7666, L8066, L9145-9148, L9171-9225 |
| modified | `tests/test_inbox_activity.py` | +39 −45 | L98-99, L106, L123, L126-128, L139, L197, L224, L226, L232, L239, L252, L264, L272, L337, L339, L341, L349, L351, L360-361, L369-370, L377, L380, L384, L391, L393, L401, L403, L406, L415, L418, L431, L434, L454, L461 |
| modified | `tests/test_inbox_runs.py` | +19 −20 | removed after L12, removed after L33, removed after L84, removed after L107, L119, L166, L174, L331, L359, L403, removed after L439, removed after L451, L468-470, removed after L475, L494, L500-506, L510, L530 |
| modified | `tests/test_inbox_scheduler.py` | +9 −13 | L9, removed after L22, L137, L462, L535, L1038-1042 |
| modified | `tests/test_library_index.py` | +1 −1 | L435 |
| added | `tests/test_pathway_tiers.py` | +380 −0 | L1-380 |
| modified | `tests/test_run_start_page.py` | +38 −6 | L239, L262-263, L841-843, L845, L855-877, L905-906, removed after L918, L920-921, L2905, L3151, L3154-3155 |
| modified | `tests/test_run_start_scheduler.py` | +3 −7 | removed after L12, L59, L96, L130, removed after L230, removed after L241, removed after L275 |
| modified | `tests/test_run_start_service.py` | +28 −0 | L75-77, L94-95, L246-268 |
| modified | `tests/test_run_start_submissions.py` | +32 −37 | removed after L14, L242, L263, L310, L349, L356, L363, L389-390, L407, L423, removed after L432, L442, L445, L477, L480, L511, L539, L565, removed after L627, L648, L685, L867, L870, L875, L882, L941, L981, L1009, L1022, L1054, L1087, L1091, L1145, L1161 |
