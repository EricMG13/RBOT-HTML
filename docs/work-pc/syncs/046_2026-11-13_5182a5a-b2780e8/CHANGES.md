# Changes for the work PC

From `5182a5a506b0` (the version the work PC last adapted) to `b2780e846e19` (2026-11-13T08:06:16Z). 22 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `f628136` 2026-11-13 docs(work-pc): change pack for 5182a5a
- `b2780e8` 2026-11-13 feat: full and lite credit assessments; short snapshot deactivated (Merge pull request #96 from EricMG13/claude/lite-full-credit-assessment)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `METHODOLOGY-REVIEW.md` | +13 −0 | L800-812 |
| modified | `README.md` | +11 −5 | L162-167, L178-181, L201 |
| modified | `VERIFICATION.md` | +10 −0 | L7-16 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/reader.js` | +7 −2 | L445-451 |
| modified | `apps/issuer-library/credit_os/web/reader.test.cjs` | +2 −1 | L313-314 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +13 −13 | L2970, L2999-3001, L3013, L3019, L3021, L3438, L3443, L3449-3450, L3463, L3468 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +2 −0 | L50-51 |
| added | `docs/rulings/2026-11-13-full-and-lite-credit-assessments.md` | +84 −0 | L1-84 |
| modified | `docs/templates/context-form.html` | +14 −7 | L734, L748, L789-790, L795, L2426, L2428, L2430-2433, L2439, L2443, L2587 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/contracts.py` | +13 −1 | L44, L49-51, L75-78, L81-85 |
| modified | `src/deploy_vii/report_view.py` | +22 −5 | L509, L526-541, L645, L2661-2663, L2667 |
| modified | `src/deploy_workflow/inbox/scheduler.py` | +8 −1 | L33, L249-250, L263-267 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +12 −2 | L31, L467-474, L2252-2253, L3031 |
| modified | `src/deploy_workflow/run_start/submissions.py` | +8 −1 | L34-40, L730 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +57 −0 | L21, L333-388 |
| modified | `tests/test_context_form.py` | +16 −1 | L16, L18, L77-90 |
| modified | `tests/test_cpos_launch.py` | +269 −27 | L43, L51, L80-81, L100, L117-120, L123-143, L1138-1149, L1151, L1153-1159, L1162-1164, L1242-1387, L2610, L2768, L4239-4245, L4247, L4249-4256, L4323-4372, L6082, L6159 |
| modified | `tests/test_credit_os_catalogue.py` | +1 −1 | L212 |
| modified | `tests/test_library_changes_browser.py` | +1 −1 | L171 |
| modified | `tests/test_library_page_browser.py` | +4 −3 | L1113-1114, L1117, L1240 |
| modified | `tests/test_run_start_page.py` | +134 −47 | L239, L261, L373-376, L850-852, L855-856, L862-891, L894-896, L900-936, L2090-2140, L2840, removed after L2933, L3731 |
| modified | `tests/test_run_start_scheduler.py` | +50 −0 | L86-135 |
