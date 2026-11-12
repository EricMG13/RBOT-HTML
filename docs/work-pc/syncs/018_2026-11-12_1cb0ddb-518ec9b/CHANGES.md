# Changes for the work PC

From `1cb0ddb4c14c` (the version the work PC last adapted) to `518ec9bc3564` (2026-11-12T11:59:24Z). 8 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `9e2c39f` 2026-11-12 docs(work-pc): change pack for 1cb0ddb
- `518ec9b` 2026-11-12 feat(forecast): publish the history record for new runs; CP-1 is asked for the period table (PR 1b) (Merge pull request #60 from EricMG13/claude/forecast-period-columns-1b)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +6 −0 | L7-12 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/handoff_delivery.py` | +3 −0 | L152-154 |
| modified | `src/deploy_workflow/markdown_delivery.py` | +3 −1 | L925-927 |
| modified | `src/deploy_workflow/owners/cpos.py` | +2 −1 | L555, L576 |
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +28 −1 | L481-483, L560-571, L577-589 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +13 −0 | L1585-1596, L2117 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +35 −1 | L1779-1803, L3004, L3064-3072 |
| modified | `tests/test_cpos_periods.py` | +82 −0 | L790-802, L834-859, L869-876, L1057-1075, L1129-1144 |
