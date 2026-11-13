# Changes for the work PC

From `0d2b2f1e3d42` (the version the work PC last adapted) to `06a3caa77968` (2026-11-13T23:57:50Z). 7 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `ca15a8e` 2026-11-13 docs(work-pc): change pack for 0d2b2f1
- `06a3caa` 2026-11-13 CP-1 follow-ups: spaced prefixed currency symbol keeps the gap option; library list marks adjusted leverage (Merge pull request #117 from EricMG13/claude/cp1-spaced-prefix-advice)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +8 −0 | L7-14 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/screen.css` | +1 −0 | L127 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +13 −0 | L2134-2146 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +1 −1 | L1426 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-13-cp1-deploy-v-method-and-acceptance-check.md` | +10 −4 | L88-96, L143 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +7 −5 | L1510-1511, L1515-1518, L1520 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_cp1_check.py` | +21 −0 | L1961-1963, L1979-1996 |
