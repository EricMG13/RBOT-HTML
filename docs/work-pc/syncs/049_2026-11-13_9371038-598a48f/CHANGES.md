# Changes for the work PC

From `93710385933f` (the version the work PC last adapted) to `598a48fb2ac8` (2026-11-13T19:54:58Z). 9 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `8e3954a` 2026-11-13 docs(work-pc): change pack for 9371038
- `598a48f` 2026-11-13 feat(signal): feed parsing and safe fetching (slice 1, part 1 of 2) (Merge pull request #101 from EricMG13/claude/signal-1a-fetch-feeds)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/design/mockups/signal.html` | +355 −0 | L1-355 |
| added | `docs/signal/sources.json` | +1651 −0 | L1-1651 |
| added | `docs/superpowers/plans/2026-11-13-signal-1-store-and-ingest.md` | +493 −0 | L1-493 |
| added | `docs/superpowers/specs/2026-11-13-signal-design.md` | +282 −0 | L1-282 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| added | `src/deploy_workflow/signal/__init__.py` | +1 −0 | L1 |
| added | `src/deploy_workflow/signal/feeds.py` | +166 −0 | L1-166 |
| added | `src/deploy_workflow/signal/fetch.py` | +332 −0 | L1-332 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/test_signal_feeds.py` | +156 −0 | L1-156 |
| added | `tests/test_signal_fetch.py` | +685 −0 | L1-685 |
