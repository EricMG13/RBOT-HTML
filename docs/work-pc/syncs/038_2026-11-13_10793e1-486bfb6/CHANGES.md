# Changes for the work PC

From `10793e1c6a30` (the version the work PC last adapted) to `486bfb6c969e` (2026-11-13T00:03:07Z). 4 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `a945877` 2026-11-12 docs(work-pc): change pack for 10793e1
- `486bfb6` 2026-11-13 fix(prose): thousands separators and bracketed notes no longer cause wrong refusals (Merge pull request #81 from EricMG13/claude/prose-number-reading)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +15 −0 | L12-26 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-reader-and-issuer-report.md` | +45 −0 | L251-295 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/prose_checks.py` | +119 −13 | L38, L875-879, L927-1011, L1015-1017, L1020, L1022-1033, L1035-1046 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_prose_checks.py` | +265 −0 | L4, L12, L793-1055 |
