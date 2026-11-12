# Changes for the work PC

From `6d3cbd0c1b42` (the version the work PC last adapted) to `01ba2a45d93b` (2026-11-12T20:52:35Z). 8 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `50dcfb0` 2026-11-12 docs(work-pc): change pack for 6d3cbd0
- `01ba2a4` 2026-11-12 feat(forecast): name cells of period-row tables; LTM label as a balance date (Merge pull request #76 from EricMG13/claude/forecast-reader-findings)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +7 −26 | L7-13, removed after L974 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/VERIFICATION-ARCHIVE.md` | +26 −0 | L392-417 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +35 −13 | L54-57, L63, L69-72, L75-79, L278-279, L281, L283-288, L332-334, L344, L360-361, L464-465, L759, L762-763, L765 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +52 −12 | L1618-1628, L1639-1640, L1710-1716, L1735-1746, L1755-1756, L2463-2470, L2487-2489, L2493-2498, L2500 |
| modified | `src/deploy_workflow/owners/cpos_periods.py` | +310 −46 | L12, L15, L59, L98-117, L124-126, L130-132, L139-146, L150-151, L157-161, L170, L248, L252-255, L261, L284-288, L311-315, L328, L350-354, L359-360, L362-365, L370-424, L426-429, L431-433, L436-457, L486-493, L546-547, L736-804, L903-908, L912-913, L933-946, L949-951, L956-957, L965-973, L976-978, L986, L1007-1011, L1021-1028, L1030-1039, L1077-1081, L1087, L1095-1098, L1102 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +111 −9 | L2867-2870, L2892, L2908-2909, L2933-2934, L3163, L3333-3336, L4983, L5019-5021, L5297-5389 |
| modified | `tests/test_cpos_periods.py` | +613 −0 | L3, L1375-1986 |
| modified | `tests/test_cpos_scale.py` | +4 −3 | L243, L270-272 |
