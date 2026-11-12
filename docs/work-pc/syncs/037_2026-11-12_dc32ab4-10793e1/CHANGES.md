# Changes for the work PC

From `dc32ab4925bc` (the version the work PC last adapted) to `10793e1c6a30` (2026-11-12T23:56:22Z). 4 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `4c0eafa` 2026-11-12 docs(work-pc): change pack for dc32ab4
- `10793e1` 2026-11-12 fix(cp8): a currency code glued to digits is read; more currency and scale forms; a bond name is a year (Merge pull request #80 from EricMG13/claude/cp8-checker-currency)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +5 −0 | L7-11 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +1 −0 | L463 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/changes_check.py` | +23 −10 | L98-103, L105-111, removed after L124, L128, L130-132, L139, L141-143, L147, L192 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +126 −0 | L3734-3859 |
