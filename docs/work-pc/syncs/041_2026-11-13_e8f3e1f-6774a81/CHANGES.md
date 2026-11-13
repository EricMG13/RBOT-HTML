# Changes for the work PC

From `e8f3e1f1bdf8` (the version the work PC last adapted) to `6774a812c97a` (2026-11-13T04:16:45Z). 7 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `c3ccfcf` 2026-11-13 docs(work-pc): change pack for e8f3e1f
- `c575467` 2026-11-13 fix(prose): check 6 reads IDs only from a column headed ID (Merge pull request #85 from EricMG13/claude/redesign-p1-check6)
- `6774a81` 2026-11-13 fix(cp8): missing rows refused, own-row difference allowed, fact rows read whole; method text rewritten (Merge pull request #86 from EricMG13/claude/redesign-c1-cp8-defects)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp8.md` | +40 −26 | L30-32, L51-53, L76-83, L94-96, L115-122, L154-156, L159, L174-179, L198-199, L203-205 |
| modified | `src/deploy_workflow/changes_check.py` | +41 −20 | L23, L49-50, L52-54, removed after L156, L450, removed after L469, L581-586, L631-638, L818-820, L857-859, L861-867, L872, L1209, L1221, L1226-1227, L1237-1238 |
| modified | `src/deploy_workflow/prose_checks.py` | +0 −27 | removed after L488, removed after L490 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/canned_provider_launcher.py` | +4 −4 | L28-30, L35 |
| modified | `tests/test_changes.py` | +287 −49 | L1183-1188, L1196, L1215-1218, removed after L1267, L1320, L1322, L1325, L1328, L1462-1464, L1713-1728, L2696-2713, L2770, L2775, L2780, L2810, L2813, L2819, L2846, L2873, L2875-2877, L2961, L2997, L3002, L3020, L3026, L3037, L3039, L3046, L3073, L3079, L3092, L3105, L3110, L3127, L3252, L3254, L3344, L3891-4097 |
| modified | `tests/test_cpos_launch.py` | +1 −1 | L1827 |
| modified | `tests/test_prose_checks.py` | +15 −4 | L200-202, L204, L209-218, L740 |
