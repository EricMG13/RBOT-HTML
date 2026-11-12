# Changes for the work PC

From `931eb337fe81` (the version the work PC last adapted) to `dd3c59f70703` (2026-11-12T16:13:51Z). 7 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `4224a74` 2026-11-12 docs(work-pc): change pack for 931eb33
- `dd3c59f` 2026-11-12 feat(forecast): CP-2G names the row and period of each base operand; history from named rows only (Merge pull request #70 from EricMG13/claude/forecast-units-scale)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +7 −0 | L7-13 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/superpowers/plans/2026-11-12-forecast-named-rows-and-units.md` | +996 −0 | L1-996 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +54 −39 | L16, L46-47, L161-165, L175-181, L244-247, L251-252, L259-260, L262-263, L266-272, L274-277, L279-283, L333-335, L337-341, L582-586 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +28 −12 | L1603, L1605-1617, L2407-2420 |
| modified | `src/deploy_workflow/owners/cpos_periods.py` | +52 −159 | removed after L11, L14, L97, removed after L106, removed after L107, removed after L110, removed after L124, L156-158, L163, removed after L176, L213, removed after L225, L236, L238-240, L242, removed after L243, L247-248, removed after L261, L269-273, L279, L281, removed after L283, removed after L286, L289, L293, L303-305, L385, L445-447, L449-451, L554, L559, L567, L725, L727-730, L766, L810, L813, L818-825 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +347 −4 | L2855-2938, L2940-2957, L3158-3163, L3322-3338, L4905-5126 |
| modified | `tests/test_cpos_periods.py` | +216 −175 | L12, removed after L15, L22-23, removed after L24, L119-148, removed after L169, removed after L229, L435-436, L443-445, L815, L852, L876-877, L879, L881, L886, L892, removed after L922, L926-930, L946-949, L1055, L1059-1063, L1065, L1074-1075, L1130-1133, L1135-1137, removed after L1195, removed after L1211, L1213-1216, L1218-1225, L1241-1373 |
