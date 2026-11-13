# Changes for the work PC

From `c9aa24401a6e` (the version the work PC last adapted) to `6279aeaa5724` (2026-11-13T22:44:23Z). 4 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `43b3513` 2026-11-13 docs(work-pc): change pack for c9aa244
- `6279aea` 2026-11-13 fix(forecast): no net debt, net leverage or liquidity is published for a forecast year with negative cash (Merge pull request #114 from EricMG13/claude/negative-cash-not-calculable)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +8 −0 | L7-14 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/rulings/2026-11-13-negative-cash-not-calculable.md` | +31 −0 | L1-31 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +18 −1 | L633-649, L799 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/test_negative_cash_not_calculable.py` | +201 −0 | L1-201 |
