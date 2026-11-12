# Changes for the work PC

From `832e56c84d85` (the version the work PC last adapted) to `0e80345d5314` (2026-11-12T10:10:09Z). 19 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `1f2ee9f` 2026-11-12 docs(work-pc): change pack for 832e56c
- `0e80345` 2026-11-12 fix(changes): one reader for CP-8's registers; whole-branch review fixes (Merge pull request #58 from EricMG13/claude/changes-seams-r3)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `AGENTS.md` | +4 −4 | L38-40, L53 |
| modified | `VERIFICATION.md` | +11 −0 | L7-17 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +3 −1 | L51-53 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/changes.js` | +31 −51 | L5-7, removed after L15, L31, removed after L43, removed after L47, L52-59, L116, L118, L144-146, L148-149, L152, L158-160, L162, L169-170, L172, L180, L233-235 |
| modified | `apps/issuer-library/credit_os/web/changes.test.cjs` | +84 −19 | L7, L54-67, L69, L119-120, L131-136, L141-142, L195, L198-199, L209, L212, L233, L235, L237, L240, L245, L248, L252-269, L284, L289-316 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +2 −2 | L1352-1353 |
| modified | `apps/issuer-library/update_library.py` | +32 −2 | L40, L170-192, L195-198, L203-205, L214 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +45 −4 | L48, L189, L214-256 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp8.md` | +6 −4 | L67-68, L74, L78-79, L90 |
| modified | `src/deploy_workflow/changes.py` | +1 −0 | L103 |
| modified | `src/deploy_workflow/changes_check.py` | +165 −18 | L48, L74, L165-174, L320, L322-327, removed after L356, L365, L413-447, L454-456, L464-475, removed after L494, L496, L498-503, removed after L504, removed after L766, L769-771, L776-860 |
| modified | `src/deploy_workflow/library_index.py` | +10 −5 | L420, L425-428, L431-434, L436 |
| modified | `src/deploy_workflow/owners/cpos.py` | +10 −2 | L48-55, L548-549 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +2 −5 | L37, L1433 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/fixtures/changes-seam/rows.json` | +32 −0 | L1-32 |
| modified | `tests/library_fixtures.py` | +9 −2 | L365-369, L373-374, L384-385 |
| modified | `tests/test_changes.py` | +78 −2 | L39, L1799-1801, L2182-2255 |
| modified | `tests/test_library_changes_browser.py` | +28 −0 | L213-240 |
| modified | `tests/test_update_library.py` | +105 −0 | L10, L17, L490, L503-524, L571-650 |
