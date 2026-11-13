# Changes for the work PC

From `b2780e846e19` (the version the work PC last adapted) to `5ae00873d407` (2026-11-13T11:51:36Z). 5 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `81134f0` 2026-11-13 docs(work-pc): change pack for b2780e8
- `5ae0087` 2026-11-13 fix(handoff): table refusals name the line; record the TDG Copilot Sol medium and high runs (Merge pull request #97 from EricMG13/claude/tdg-full-copilot-sol-run)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/rulings/2026-11-13-tdg-full-copilot-sol-high.md` | +27 −0 | L1-27 |
| added | `docs/rulings/2026-11-13-tdg-full-copilot-sol-rerun.md` | +44 −0 | L1-44 |

### runs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `runs/tdg-copilot-sol-medium-vs-high.md` | +118 −0 | L1-118 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/handoff_delivery.py` | +28 −9 | L310, L312, L316-320, L326-346 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/test_handoff_delivery_table.py` | +63 −0 | L1-63 |
