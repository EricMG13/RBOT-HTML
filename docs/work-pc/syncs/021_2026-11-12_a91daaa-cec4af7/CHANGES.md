# Changes for the work PC

From `a91daaa3b0dd` (the version the work PC last adapted) to `cec4af7c414e` (2026-11-12T12:12:20Z). 5 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `184cec8` 2026-11-12 docs(work-pc): change pack for a91daaa
- `cec4af7` 2026-11-12 fix(launch): Claude configs ask for 64,000 output tokens; record the proof runs (Merge pull request #65 from EricMG13/claude/anthropic-output-limit)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +4 −0 | L7-10 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/rulings/2026-11-12-module-changes-proof-runs-claude.md` | +27 −0 | L1-27 |
| added | `docs/rulings/2026-11-12-module-changes-proof-runs.md` | +36 −0 | L1-36 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +19 −3 | L120-135, L1886, L2186, L2581 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +51 −0 | L4724-4774 |
