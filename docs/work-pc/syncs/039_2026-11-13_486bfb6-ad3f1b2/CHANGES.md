# Changes for the work PC

From `486bfb6c969e` (the version the work PC last adapted) to `ad3f1b2e9e79` (2026-11-13T01:00:41Z). 18 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `f392365` 2026-11-13 docs(work-pc): change pack for 486bfb6
- `ad3f1b2` 2026-11-13 Brand colours and component look; Run activity redesigned, spend off the page (Merge pull request #82 from EricMG13/claude/brand-application)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `README.md` | +2 −3 | L223-224 |
| modified | `VERIFICATION.md` | +11 −45 | L7-17, removed after L963 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +2 −2 | L92-93 |
| modified | `apps/issuer-library/credit_os/SOURCE.md` | +31 −0 | L248-278 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +114 −57 | L5-7, L9-10, L17, L20, L25, L32-33, L42, L58, L80-81, L89, L93, L124, L147, L158, L165, L173, L190-191, L197, L200, L212-213, L217, L227, L275, L277, L311, L331-332, L377, L384, L410-411, L414, L417-418, L421, removed after L423, L427, L432, L456, L516, L627, L632, L648-650, L832-835, L841-899 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +236 −5 | L1467, removed after L1474, L1478-1592, L1666-1668, L3475-3591 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +42 −16 | L1440-1441, L1451, L1453-1465, L1468-1485, L1490-1494, L1496-1498 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/VERIFICATION-ARCHIVE.md` | +45 −0 | L418-462 |
| added | `docs/design/2026-11-13-brand-application.md` | +132 −0 | L1-132 |
| modified | `docs/templates/context-form.html` | +36 −36 | L19-20, L67, L91, L94-95, L100, L117, L134-135, L139, L160-161, L167, L176, L221, L231, L257, L262, L272-274, L287, L313, L315, L319-323, L325, L329, L360, L365, L383, L392 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/assets/app.css` | +7 −5 | L217, L219-221, L223-224, L231 |
| modified | `src/deploy_vii/assets/tokens.css` | +15 −12 | L3-4, L6-8, L11-14, L16-21 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/browser_cdp_measure.cjs` | +77 −0 | L1-77 |
| added | `tests/browser_probe_run_activity.js` | +33 −0 | L1-33 |
| added | `tests/test_brand_tokens.py` | +158 −0 | L1-158 |
| modified | `tests/test_context_form.py` | +22 −0 | L350-371 |
| modified | `tests/test_library_page_browser.py` | +242 −10 | L334-512, L1563, L1575, L1640, L1675, L1682, L1724, L1737, L2357-2412 |
| modified | `tests/test_run_start_page.py` | +38 −18 | L2964, L3001, L3057, L3063-3065, L3096-3097, L3099-3100, L3214, L3301, L3306-3307, L3432-3434, L3437, L3658-3677 |
