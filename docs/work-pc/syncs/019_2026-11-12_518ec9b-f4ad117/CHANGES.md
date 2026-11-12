# Changes for the work PC

From `518ec9bc3564` (the version the work PC last adapted) to `f4ad1179272d` (2026-11-12T12:00:12Z). 9 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `e55b199` 2026-11-12 docs(work-pc): change pack for 518ec9b
- `f4ad117` 2026-11-12 feat(library): Forecast page shows the main period columns (PR 2) (Merge pull request #63 from EricMG13/claude/forecast-period-columns-2)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +9 −29 | L7-14, L21, removed after L979 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/store.py` | +314 −51 | L1330, L1378-1404, L1429-1430, L1456-1457, L1872-1874, L1876, L1890, L1894-1934, L1964-2081, L2168-2192, L2197-2199, L2213-2214, removed after L2217, removed after L2251, L2255, L2270-2272, L2344-2350, L2352-2354, L2718-2747, L2749-2750, L2757-2759, L2762-2764, L2781-2793, L2801, L2815-2825, L2828-2834, L2877-2878, L2889, L3204 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +1 −0 | L300 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +11 −5 | L915, L931-938, L940-941 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/VERIFICATION-ARCHIVE.md` | +29 −0 | L5-33 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/browser_probe_forecast_cases.js` | +24 −0 | L1-24 |
| modified | `tests/test_cpos_launch.py` | +8 −12 | L3226-3227, L3237-3238, removed after L3240, L3243-3246 |
| modified | `tests/test_credit_os_store.py` | +636 −0 | L6, L1306-1940 |
| modified | `tests/test_library_page_browser.py` | +124 −0 | L10, L1192-1314 |
