# Changes for the work PC

From `021ac135c05f` (the version the work PC last adapted) to `4f6b32c7f8ce` (2026-11-13T21:25:37Z). 5 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `bb1950c` 2026-11-13 docs(work-pc): change pack for 021ac13
- `4f6b32c` 2026-11-13 fix(forecast): a Markdown model is not called HTML; a true reason for the Pro forma column (Merge pull request #112 from EricMG13/claude/forecast-true-labels)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +7 −0 | L7-13 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +16 −0 | L4310-4325 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +4 −2 | L1326-1329 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_periods.py` | +3 −1 | L441-443 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_periods.py` | +31 −2 | L374-400, L1412-1415 |
