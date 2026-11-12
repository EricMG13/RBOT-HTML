# Changes for the work PC

From `6d8ca7106b68` (the version the work PC last adapted) to `74cd06868199` (2026-11-12T19:55:59Z). 5 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `5db96a9` 2026-11-12 docs(work-pc): change pack for 6d8ca71
- `74cd068` 2026-11-12 fix(cp8): year-shaped figures are read; counts beside a count noun are allowed; a spelled size across lines is read (Merge pull request #75 from EricMG13/claude/cp8-checker-counts)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +7 −0 | L7-12, L28 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +48 −0 | L415-462 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp8.md` | +6 −1 | L109-114 |
| modified | `src/deploy_workflow/changes_check.py` | +183 −19 | L62, L98-108, L110-111, L113-132, L134, L171-186, L188-191, L199-201, removed after L874, L1014-1039, L1057-1061, L1080-1157, L1181, L1202, L1204, L1246-1257, L1273 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +430 −6 | L6, removed after L23, L25, removed after L2942, L3257-3684 |
