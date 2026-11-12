# Changes for the work PC

From `e8c28602639f` (the version the work PC last adapted) to `931eb337fe81` (2026-11-12T16:01:00Z). 8 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `c2de9b1` 2026-11-12 docs(work-pc): change pack for e8c2860
- `931eb33` 2026-11-12 fix(cp8): a same-period net debt difference is the analysis's, not the issuer's (Merge pull request #69 from EricMG13/claude/net-debt-same-period)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +4 −0 | L7-10 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/changes.js` | +12 −2 | L92-95, L98-105 |
| modified | `apps/issuer-library/credit_os/web/changes.test.cjs` | +29 −0 | L330-358 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +13 −3 | L349-361 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp8.md` | +5 −1 | L99-103 |
| modified | `src/deploy_workflow/changes.py` | +17 −6 | L49-57, L616, L644-650 |
| modified | `src/deploy_workflow/changes_check.py` | +39 −4 | L224-248, L258, L269-279, L763, L775 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +117 −0 | L834-840, L2620-2626, L2646-2748 |
