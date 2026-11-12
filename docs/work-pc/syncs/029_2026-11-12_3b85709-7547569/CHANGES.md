# Changes for the work PC

From `3b85709550a3` (the version the work PC last adapted) to `754756913ea7` (2026-11-12T16:27:25Z). 5 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `f98ff70` 2026-11-12 docs(work-pc): change pack for 3b85709
- `7547569` 2026-11-12 fix(cp8): a withheld difference may only be printed in its own issuer row (Merge pull request #72 from EricMG13/claude/cp8-why-cell-withheld)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +3 −0 | L7-9 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +10 −0 | L362-371 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp8.md` | +5 −2 | L98, L103-106 |
| modified | `src/deploy_workflow/changes_check.py` | +38 −14 | L43-46, L771, L773-775, L782, L789-809, L831, L841, L843-846, L853, L855 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +105 −0 | L2749-2853 |
