# Changes for the work PC

From `dd3c59f70703` (the version the work PC last adapted) to `3b85709550a3` (2026-11-12T16:15:21Z). 9 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `c0b7271` 2026-11-12 docs(work-pc): change pack for dd3c59f
- `3b85709` 2026-11-12 feat(forecast): inputs in thousands with scale 1000 (Merge pull request #71 from EricMG13/claude/forecast-units-scale-b)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +8 −0 | L7-14 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +2 −1 | L42-43 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/store.py` | +39 −4 | L1491-1519, L2781, L2786-2787, L2858, L2903-2905, L2923-2925 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +183 −24 | L14, L18, L43-48, L110, L258, L260-262, L275, L287, L293-354, L377-466, L477, L493, L495, L500, L504-506, L508, L517, L527, L532, L726-728, L731, L758 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +73 −23 | L1598-1602, L1607-1612, L1619-1621, L1626-1631, L1636-1639, L1651, L1660-1662, L1710-1717, L1722-1726, L1728-1732, L1739-1742, L2429-2440, L2459-2464, L2466-2470 |
| modified | `src/deploy_workflow/owners/cpos_periods.py` | +14 −6 | L273, L280, L282-284, L290, L292-294, L814, L818-821 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +86 −0 | L3660-3672, L5038-5070, L5173-5212 |
| added | `tests/test_cpos_scale.py` | +835 −0 | L1-835 |
| modified | `tests/test_credit_os_store.py` | +55 −0 | L1385-1439 |
