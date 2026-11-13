# Changes for the work PC

From `1cdfb86fde79` (the version the work PC last adapted) to `0ababbe51991` (2026-11-13T23:35:30Z). 4 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `7c21c1e` 2026-11-13 docs(work-pc): change pack for 1cdfb86
- `0ababbe` 2026-11-13 fix(signal): an unexpected error on one source no longer starves the rest (Merge pull request #115 from EricMG13/claude/signal-ingest-starvation)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +14 −0 | L7-20 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/signal/ingest.py` | +23 −3 | L3, L25-26, L73-77, L82-96 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_signal_ingest.py` | +47 −5 | L85-94, L96-99, L101-133 |
| modified | `tests/test_signal_service.py` | +27 −5 | L415-417, L421-425, L428-446 |
