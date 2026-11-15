# Changes for the work PC

From `47c3039dc08f` (the version the work PC last adapted) to `250aa050c1b3` (2026-11-15T20:45:30Z). 18 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `b8cf4ca` 2026-11-15 docs(work-pc): change pack for 47c3039
- `250aa05` 2026-11-15 Method script checks for the remaining modules; export check shows possible borrowers (Merge pull request #128 from EricMG13/claude/busy-dijkstra-bgex9m)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.importlinter` | +2 −2 | L42, L45 |
| modified | `VERIFICATION.md` | +20 −0 | L56-75 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +1 −0 | L61 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-15-method-script-checks.md` | +265 −0 | L336-587, L592-604 |
| modified | `docs/sweeps/2026-11-15-method-scripts/scope.md` | +5 −0 | L70-74 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/inputs/portfolio_export.py` | +14 −3 | L1665, L1679, L1681, L1683-1685, L1689-1696 |
| modified | `src/deploy_workflow/method_scripts.py` | +52 −11 | L31, L53-56, L951-963, L974-976, L980-992, L994, L1029-1033, L1063-1064, L1066-1067, L1069-1070, L1073-1074, L1088-1089, L1092, L1095 |
| added | `src/deploy_workflow/method_scripts_completeness.py` | +297 −0 | L1-297 |
| added | `src/deploy_workflow/method_scripts_cp1b.py` | +274 −0 | L1-274 |
| added | `src/deploy_workflow/method_scripts_cp1c.py` | +555 −0 | L1-555 |
| added | `src/deploy_workflow/method_scripts_cp2h.py` | +327 −0 | L1-327 |
| added | `src/deploy_workflow/method_scripts_cp4c.py` | +439 −0 | L1-439 |
| modified | `src/deploy_workflow/owners/cpos.py` | +5 −1 | L36-40 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +6 −1 | L34-38, L1306 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +176 −15 | L8724-8728, L8770-8790, L8806-8810, L8815-8817, L8821-8824, L8884-9016, L9101-9102, L9111-9112, L9114 |
| modified | `tests/test_method_scripts.py` | +11 −3 | L18, L1847-1850, L1878-1881, L1885, L1891 |
| added | `tests/test_method_scripts_rest.py` | +1251 −0 | L1-1251 |
| modified | `tests/test_portfolio_export.py` | +9 −3 | L921-923, L941-943, L953-955 |
