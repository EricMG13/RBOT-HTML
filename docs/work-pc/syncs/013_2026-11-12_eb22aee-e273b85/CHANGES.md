# Changes for the work PC

From `eb22aee01e16` (the version the work PC last adapted) to `e273b85671d7` (2026-11-12T04:58:46Z). 17 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `e0ce46e` 2026-11-12 docs(work-pc): change pack for eb22aee
- `e273b85` 2026-11-12 feat(library): Changes section — what changed since the last run (Merge pull request #56 from EricMG13/claude/changes-section)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +4 −0 | L7-10 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +1 −1 | L34 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +4 −2 | L22-25 |
| added | `apps/issuer-library/credit_os/web/changes.js` | +264 −0 | L1-264 |
| added | `apps/issuer-library/credit_os/web/changes.test.cjs` | +251 −0 | L1-251 |
| added | `apps/issuer-library/credit_os/web/icons/git-compare.svg` | +16 −0 | L1-16 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +16 −0 | L591-606 |
| modified | `apps/issuer-library/credit_os/web/screen.js` | +1 −1 | L483 |
| modified | `apps/issuer-library/credit_os/web/static-boot.js` | +1 −1 | L23 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +3 −3 | L25, L28, L99 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +16 −2 | L91, L806, L1344-1355, L1360, L1375 |
| modified | `apps/issuer-library/update_library.py` | +41 −0 | L39, L149-187, L249 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/library_index.py` | +21 −0 | L419-438, L483 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/library_fixtures.py` | +27 −0 | L13-14, L92, L132-133, L359-380 |
| added | `tests/test_library_changes_browser.py` | +212 −0 | L1-212 |
| modified | `tests/test_library_page_browser.py` | +1 −1 | L975 |
| modified | `tests/test_update_library.py` | +89 −1 | L10, L458-545 |
