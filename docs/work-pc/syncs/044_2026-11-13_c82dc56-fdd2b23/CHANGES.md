# Changes for the work PC

From `c82dc5605ab6` (the version the work PC last adapted) to `fdd2b234abfb` (2026-11-13T04:21:58Z). 8 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `1bbfed0` 2026-11-13 docs(work-pc): change pack for c82dc56
- `fdd2b23` 2026-11-13 docs(prompt): one Net debt Period form per case; instruction leftovers (Merge pull request #95 from EricMG13/claude/redesign-wb-instruction-text)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +29 −37 | L7-35, removed after L955 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/VERIFICATION-ARCHIVE.md` | +37 −0 | L419-455 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +84 −19 | L43-60, L136, L157-158, L330-352, L391-393, L396, L409-410, L438-443, L473-474, L481, L525, L561-573, L595-596, L807-814, L817 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +96 −47 | L50, L626-631, L643-666, L669-670, L679-686, L1755-1758, L1764-1768, L1777-1780, L1792, L1795, L1802, L1866-1876, L1884-1889, L1897-1901, L1914, L1923, L2704, L2707, L2714, L2722, L2734-2744 |
| modified | `src/deploy_workflow/owners/cpos_periods.py` | +19 −134 | removed after L58, L97, removed after L105, L110-114, L136, removed after L142, removed after L150, removed after L227, removed after L230, L236, L286, L321, removed after L422, L426-429, L440, L444, removed after L454, removed after L510, removed after L698, removed after L805, L835, removed after L845, L860, removed after L974, L982 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +110 −25 | L3480, L5333-5335, L5337, L5355-5358, L5705-5712, L5720-5724, L5740, L5742-5743, L5746, L5750-5751, L5794-5795, L5797, L5800-5801, L5804-5880 |
| modified | `tests/test_cpos_periods.py` | +121 −261 | L341, L345, L403, L408-410, L431-433, L530, L902, L1384-1386, L1591, removed after L1598, removed after L1666, removed after L1678, removed after L1685, L1690-1692, L1696-1697, L1699-1700, L1748-1846 |
| modified | `tests/test_cpos_scale.py` | +263 −8 | L211, L431-433, L458, L470, L492, L817, L822, L838-1091 |
