# Changes for the work PC

From `98e3cba954d7` (the version the work PC last adapted) to `e8c28602639f` (2026-11-12T14:57:26Z). 8 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `10e3c44` 2026-11-12 docs(work-pc): change pack for 98e3cba
- `e8c2860` 2026-11-12 feat(cp1): Net debt data table so the comparison can show the net debt change (Merge pull request #68 from EricMG13/claude/cp1-gross-debt-row)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +6 −0 | L7-12 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +36 −3 | L297, L317-351 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp8.md` | +2 −2 | L22-23 |
| modified | `src/deploy_workflow/changes.py` | +44 −28 | L50-52, L85, L115-118, L125-126, L129-132, L396-399, L407, L433, L493, removed after L602, L605-608, L617-618, L627, L634, L776-790 |
| modified | `src/deploy_workflow/credit_os_catalogue.py` | +11 −5 | L86-95, L97 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +71 −4 | L45, L573-632, L637, L645, L2314-2320, L2372 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +111 −25 | L612, L614, removed after L615, L620-629, removed after L635, L638, L714-715, L730-731, L767-769, L782, L801, L806-808, L814-815, L846-847, L973, L975, L1063, L1065-1066, L2554-2583, L2585-2631 |
| modified | `tests/test_cpos_launch.py` | +84 −0 | L156-160, L475-476, L4782-4858 |
