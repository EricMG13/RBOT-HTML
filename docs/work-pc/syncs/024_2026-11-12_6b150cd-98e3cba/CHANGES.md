# Changes for the work PC

From `6b150cd7486e` (the version the work PC last adapted) to `98e3cba954d7` (2026-11-12T14:29:42Z). 18 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `d1ea958` 2026-11-12 docs(work-pc): change pack for 6b150cd
- `98e3cba` 2026-11-12 Redesign pass 1: run header, Modules, inspector and Overview take the new layout (Merge pull request #67 from EricMG13/claude/redesign-modules-overview)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +36 −0 | L7-42 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +4 −3 | L128, L130-132 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +206 −10 | L158-159, removed after L163, L165, L167, removed after L341, removed after L424, removed after L425, L459, L601-801 |
| modified | `apps/issuer-library/credit_os/web/screen.js` | +19 −10 | L300-304, L312, L343-349, L354, removed after L355, L362, L369, L372, L550, L564 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +161 −12 | L27-28, L286, L355, L357-358, L366-367, L558, L763, L911, L917, L967, L1228-1245, L2046, L2604-2732 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +60 −25 | L410, L487-490, L496, L512, L534-537, L542, L546, L558, L570, L578-579, L600-601, L603, L818-839, L851, L859, L1239-1241, L1261, L1264, L1273-1275, L1298-1299, L1424-1427, L1431, L1433 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/design/2026-11-12-redesign-pass-1.md` | +117 −0 | L1-117 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/browser_probe_chip_overlap.js` | +16 −0 | L1-16 |
| added | `tests/browser_probe_chrome.js` | +31 −0 | L1-31 |
| added | `tests/browser_probe_content_padding.js` | +8 −0 | L1-8 |
| added | `tests/browser_probe_edges.js` | +22 −0 | L1-22 |
| added | `tests/browser_probe_field_card.js` | +13 −0 | L1-13 |
| added | `tests/browser_probe_header_scope.js` | +24 −0 | L1-24 |
| added | `tests/browser_probe_module_page.js` | +50 −0 | L1-50 |
| added | `tests/browser_probe_overview_layout.js` | +67 −0 | L1-67 |
| added | `tests/browser_probe_overview_style.js` | +9 −0 | L1-9 |
| added | `tests/browser_probe_start_run.js` | +26 −0 | L1-26 |
| modified | `tests/test_library_page_browser.py` | +747 −12 | L1232, L1251, L1267-1289, L1292-1303, L1306-1307, L1310-1874, L1998-2140 |
