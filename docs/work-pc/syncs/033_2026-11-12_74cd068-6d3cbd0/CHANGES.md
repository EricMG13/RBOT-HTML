# Changes for the work PC

From `74cd06868199` (the version the work PC last adapted) to `6d3cbd0c1b42` (2026-11-12T20:49:13Z). 7 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `c807ebc` 2026-11-12 docs(work-pc): change pack for 74cd068
- `6d3cbd0` 2026-11-12 fix(library): Forecast page labels, fold for empty lines, readable model picker (Merge pull request #77 from EricMG13/claude/forecast-reader-findings-page)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +8 −0 | L7-14 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/store.py` | +40 −9 | L1378-1395, L2722-2732, L2770-2774, L2779, L2838-2840, L2872-2873 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +1 −1 | L299 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +97 −1 | L917, L2733-2828 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +20 −6 | L136-137, L139-148, L961, L973, L986-988, L990, L1007-1008 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/superpowers/plans/2026-11-12-forecast-reader-findings.md` | +160 −0 | L1-160 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_credit_os_store.py` | +172 −0 | L1508-1679 |
