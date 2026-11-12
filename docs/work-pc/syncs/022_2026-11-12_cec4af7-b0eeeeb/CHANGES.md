# Changes for the work PC

From `cec4af7c414e` (the version the work PC last adapted) to `b0eeeebea68a` (2026-11-12T13:55:07Z). 13 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `9fd334b` 2026-11-12 docs(work-pc): change pack for cec4af7
- `b0eeeeb` 2026-11-12 fix(cp8): four defects found reading the first real CP-8 run; record the run (Merge pull request #66 from EricMG13/claude/changes-real-run-fixes)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +4 −0 | L7-10 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/changes.js` | +1 −1 | L4 |
| modified | `apps/issuer-library/update_library.py` | +3 −3 | L39, L165-166 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +53 −1 | L103, L267-318 |
| added | `docs/rulings/2026-11-12-credit-snapshot-claude-rerun.md` | +25 −0 | L1-25 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methods/cp8.md` | +22 −5 | L16, L18-20, L52-55, L129-130, L144-149, L165-170 |
| modified | `src/deploy_workflow/changes.py` | +59 −17 | L23-30, L50-54, L80-82, L109-110, L151-154, L215, L248-250, L253, L277, L594-609, L619, L728, L735, L738-739, L764-770, removed after L771, L813, L830, L840 |
| modified | `src/deploy_workflow/changes_check.py` | +95 −6 | L2, L12-13, L28-38, L64, L84-89, L211-216, L500, L502-509, L524-543, L548-555, L580-581, L805-832, L861 |
| modified | `src/deploy_workflow/credit_os_chips.py` | +27 −4 | L47-51, L184-197, L199-201, L206-207, L237, L248, L542 |
| modified | `src/deploy_workflow/owners/cpos.py` | +4 −1 | L488-491 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +6 −1 | L1659-1664 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +260 −5 | L490-510, L724, L870, L877, L883, L1912, L2095-2096, L2314-2545 |
| modified | `tests/test_update_library.py` | +14 −0 | L538-551 |
