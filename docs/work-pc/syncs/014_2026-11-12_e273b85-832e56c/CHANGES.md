# Changes for the work PC

From `e273b85671d7` (the version the work PC last adapted) to `832e56c84d85` (2026-11-12T10:09:43Z). 21 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `b356c29` 2026-11-12 docs(work-pc): change pack for e273b85
- `832e56c` 2026-11-12 feat(pathway): Short Credit Snapshot (CP-0, CP-1, CP-L10) (Merge pull request #57 from EricMG13/claude/short-snapshot)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `METHODOLOGY-REVIEW.md` | +9 −0 | L732-740 |
| modified | `README.md` | +2 −2 | L157-158 |
| modified | `VERIFICATION.md` | +4 −25 | L7-10, removed after L978 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/reader.js` | +2 −0 | L404, L406 |
| modified | `apps/issuer-library/credit_os/web/reader.test.cjs` | +2 −0 | L307-308 |
| modified | `apps/issuer-library/credit_os/web/screen.js` | +1 −1 | L32 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +27 −0 | L1016-1037, L2502-2506 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +2 −1 | L1174-1175 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/VERIFICATION-ARCHIVE.md` | +24 −0 | L214-237 |
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +24 −0 | L192-215 |
| modified | `docs/rulings/2026-11-11-reader-and-issuer-report.md` | +6 −0 | L188-193 |
| modified | `docs/templates/context-form.html` | +9 −5 | L586-587, L599-600, L604, L613, L638-639, L2401 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/contracts.py` | +3 −0 | L43, L70-71 |
| modified | `src/deploy_vii/methodology.json` | +2 −2 | L565, L577 |
| modified | `src/deploy_vii/methods/cpl10.md` | +58 −33 | L1, L3-7, L9-12, L14, L16-19, L21, L23-26, L28-38, L40, L42-46, L48-68 |
| modified | `src/deploy_vii/report_view.py` | +13 −1 | L619-624, L629, L1399-1403, L1411 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +13 −0 | L101, L147-148, L2224-2225, L2265-2272 |
| modified | `src/deploy_workflow/prose_checks.py` | +39 −0 | L833-871 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +209 −1 | L109-111, L113, L754, L979-1144, L3233-3270 |
| modified | `tests/test_library_page_browser.py` | +1 −1 | L846 |
| modified | `tests/test_run_start_page.py` | +24 −0 | L705-728 |
