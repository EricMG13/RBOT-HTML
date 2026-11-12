# Changes for the work PC

From `b0eeeebea68a` (the version the work PC last adapted) to `6b150cd7486e` (2026-11-12T14:29:14Z). 18 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `a639fb7` 2026-11-12 docs(work-pc): change pack for b0eeeeb
- `6b150cd` 2026-11-12 Show module names, never module codes: library, run start page and Model file (Merge pull request #62 from EricMG13/claude/redesign-review-adaptation-892369)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +32 −87 | L7-37, L46, removed after L935 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/changes.js` | +6 −6 | L114, L125, L149, L153, L161, L229 |
| modified | `apps/issuer-library/credit_os/web/changes.test.cjs` | +15 −2 | L307-308, L317-329 |
| modified | `apps/issuer-library/credit_os/web/reader.js` | +2 −2 | L154-155 |
| modified | `apps/issuer-library/credit_os/web/reader.test.cjs` | +10 −3 | L280, L285, L455-461, L469 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +2 −4 | L7, L29, removed after L577, removed after L589 |
| modified | `apps/issuer-library/credit_os/web/screen.js` | +6 −6 | L69-70, L349, L481-483 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +70 −22 | L119-120, L129, L138, L146, L170-186, L191, L196-210, L1276-1277, L1289, L1291-1292, L1294, L1322, L2132, L2152, L2159, L2162, removed after L2163, L2165-2166, L2183-2197, L2499-2502 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +23 −9 | L62-70, L825, L844, L858, L1319, L1337, L1345-1351, L1354-1355 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/VERIFICATION-ARCHIVE.md` | +87 −0 | L267-353 |
| modified | `docs/rulings/2026-11-11-reader-and-issuer-report.md` | +2 −0 | L292-293 |
| modified | `docs/templates/context-form.html` | +20 −21 | removed after L34, removed after L256, L630-631, L775, L783, L832, L1219, L1580, L1582, L1597, L1723, L1750-1751, L1768, L1806, L1857, L1909, L2102, L2259, L2412, L2484 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/assets/app.css` | +1 −2 | L74, removed after L77 |
| modified | `src/deploy_vii/assets/app.js` | +11 −9 | L18-19, L563, L661-662, L664, L697, L765-766, L776, L827 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_library_changes_browser.py` | +20 −2 | L181, L202-205, L244-258 |
| modified | `tests/test_library_page_browser.py` | +119 −28 | L9, L566-570, L572-573, removed after L574, L581, L583-587, L591-607, L609-619, L624, L636, L639-641, L647-649, L651, L653-710, L712, L714-716, L1167-1168, L1217-1218, L1223-1224 |
| added | `tests/test_model_shell_browser.py` | +200 −0 | L1-200 |
| modified | `tests/test_run_start_page.py` | +149 −4 | L41-51, L702, L1225, L1237, L1469-1470, L2543-2675 |
