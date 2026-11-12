# Changes for the work PC

From `efe17f2e568c` (the version the work PC last adapted) to `1cb0ddb4c14c` (2026-11-12T11:53:36Z). 4 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `510f72d` 2026-11-12 docs(work-pc): change pack for efe17f2
- `1cb0ddb` 2026-11-12 feat(forecast): cpos_periods builds the history record from CP-1's period columns (PR 1a) (Merge pull request #59 from EricMG13/claude/forecast-period-columns-1a)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +1 −1 | L42 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/superpowers/plans/2026-11-12-forecast-period-columns.md` | +740 −0 | L1-740 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| added | `src/deploy_workflow/owners/cpos_periods.py` | +943 −0 | L1-943 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/test_cpos_periods.py` | +1250 −0 | L1-1250 |
