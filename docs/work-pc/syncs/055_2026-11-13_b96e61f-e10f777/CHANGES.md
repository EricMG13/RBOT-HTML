# Changes for the work PC

From `b96e61f440cc` (the version the work PC last adapted) to `e10f7778c9c4` (2026-11-13T22:19:55Z). 13 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `2f572ba` 2026-11-13 docs(work-pc): change pack for b96e61f
- `e10f777` 2026-11-13 fix(forecast): the Downside follows the forward credit model; the shock's interest figure is proportional and checked (Merge pull request #113 from EricMG13/claude/downside-follows-forward-model)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +8 −0 | L7-14 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/store.py` | +12 −2 | L1375-1377, L1977-1978, L1990-1992, L2006-2007, L2015-2016 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/rulings/2026-11-13-downside-follows-forward-model.md` | +43 −0 | L1-43 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +16 −4 | L745-747, L749, L756, L759-762, L808-814 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +120 −3 | L17, L112-113, L1887-1890, L2819-2931 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/fixtures/tdg_sol_high_2026_11_13/CP-1-tables.md` | +122 −0 | L1-122 |
| added | `tests/fixtures/tdg_sol_high_2026_11_13/CP-2A-T2DS.1-sol-001.md` | +9 −0 | L1-9 |
| added | `tests/fixtures/tdg_sol_high_2026_11_13/CP-2A-T2DS.1.md` | +7 −0 | L1-7 |
| added | `tests/fixtures/tdg_sol_high_2026_11_13/CP-2G-forecast-block.md` | +62 −0 | L1-62 |
| added | `tests/fixtures/tdg_sol_high_2026_11_13/README.md` | +3 −0 | L1-3 |
| modified | `tests/test_cpos_facilities.py` | +4 −1 | L221-224 |
| modified | `tests/test_cpos_launch.py` | +5 −4 | L4040-4042, L4048, L4053 |
| added | `tests/test_downside_follows_forward_model.py` | +358 −0 | L1-358 |
