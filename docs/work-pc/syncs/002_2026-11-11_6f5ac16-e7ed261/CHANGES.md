# Changes for the work PC

From `6f5ac16d7c71` (the version the work PC last adapted) to `e7ed261f178a` (2026-11-11T10:48:35Z). 5 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `ea1741e` 2026-11-11 Work-PC change packs: what changed since the last sync, without git (Merge pull request #42 from EricMG13/claude/offline-code-adaptation-wd7gs8)
- `e7ed261` 2026-11-11 Work-PC change packs made automatically after every push to main (Merge pull request #43 from EricMG13/claude/offline-code-adaptation-wd7gs8)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +7 −1 | L23-29 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +1 −1 | L43 |
| added | `.github/workflows/work-pc-pack.yml` | +48 −0 | L1-48 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_work_pc_delta.py` | +2 −1 | L93-94 |

### tools

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tools/work_pc_delta.py` | +3 −2 | L328-330 |
