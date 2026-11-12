# Changes for the work PC

From `8e53c1991e69` (the version the work PC last adapted) to `6d8ca7106b68` (2026-11-12T17:44:52Z). 6 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `bcb0788` 2026-11-12 docs(work-pc): change pack for 8e53c19
- `6d8ca71` 2026-11-12 fix(cp8): refuse a unitless withheld difference; read the verdict from the Effect cell only (Merge pull request #73 from EricMG13/claude/cp8-checker-gaps)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +8 −0 | L15-22 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +43 −0 | L372-414 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp8.md` | +7 −1 | L106-112 |
| modified | `src/deploy_workflow/changes_check.py` | +216 −14 | L190-192, L194-207, L397-400, L413, L823-1005, L1030, L1048-1053, L1058-1059, L1061, L1152 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/changes-seam/rows.json` | +6 −1 | L23-28 |
| modified | `tests/test_changes.py` | +407 −0 | L2854-3260 |
