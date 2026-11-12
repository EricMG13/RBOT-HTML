# Changes for the work PC

From `188cb225aadf` (the version the work PC last adapted) to `e503d273393c` (2026-11-12T02:55:28Z). 10 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `36b6d8f` 2026-11-12 docs(work-pc): change pack for 188cb22
- `e503d27` 2026-11-12 CP-2G: forecast interest and repayment from stated debt facilities (Merge pull request #53 from EricMG13/claude/cash-flow-model-comparison-498459)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +23 −36 | L7-29, removed after L973 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +1 −1 | L42 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/superpowers/plans/2026-11-12-cp2g-facility-schedule.md` | +313 −0 | L1-313 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp2g.md` | +2 −2 | L12, L24 |
| modified | `src/deploy_workflow/owners/cp2g.py` | +25 −10 | L498, L502, L504-508, L515-519, L552-556, L559-564, L568, L570 |
| added | `src/deploy_workflow/owners/cpos_facilities.py` | +121 −0 | L1-121 |
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +174 −3 | L16, L25, L102, L119-122, L151-156, L313-314, L323-324, L328-375, L385-448, L457-480, L504-507, L511-516, L528-532, L550-555 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +25 −0 | L1494-1513, L1972-1976 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/test_cpos_facilities.py` | +502 −0 | L1-502 |
| modified | `tests/test_cpos_launch.py` | +55 −0 | L8, L3219-3251, L4240-4260 |
