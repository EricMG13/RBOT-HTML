# Changes for the work PC

From `088090f15754` (the version the work PC last adapted) to `1cdfb86fde79` (2026-11-13T23:08:30Z). 20 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `6b71bd7` 2026-11-13 docs(work-pc): change pack for 088090f
- `1cdfb86` 2026-11-13 feat(research): CP-DR web lookup (fetch_page and SEC EDGAR tools), proven offline (Merge pull request #110 from EricMG13/claude/t5-cpdr-lookup-2e88f4)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +71 −81 | L7-77, removed after L966 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/reuse/selected-methods/manifest.json` | +4 −4 | L43, L45, L52, L54 |
| modified | `docs/reuse/selected-methods/skills/cp-dr-deep-research/SKILL.md` | +6 −6 | L153, L156-157, L176, L182, L187 |
| modified | `docs/reuse/selected-methods/skills/cp-dr-deep-research/references/REF_CP-DR_STEPS.md` | +1 −1 | L56 |
| added | `docs/rulings/2026-11-13-cpdr-web-lookup.md` | +361 −0 | L1-361 |
| modified | `docs/templates/context-form.html` | +6 −2 | L1841, L1998-2001, L2008 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/model/handoff.py` | +451 −28 | L20, L26, L74-93, L142-192, L204-215, L219-221, L223-228, L234-240, L258-291, L360-387, L532, L540-541, L546, L550-562, L569-577, L586-705, L709, L713-718, L720-721, L732-733, L738-739, L826-829, L855-860, L925-958, L1105-1108, L1120-1135, L1175, L1185-1209, L1231-1242, L1244, L1256-1258, L1310-1318, L1321-1326, L1383-1390 |
| modified | `src/deploy_workflow/owners/cpos.py` | +49 −2 | L34, L312-332, L604, L854-856, L860-866, L872-876, L879, L885-890, L906-909 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +95 −3 | L80, L86-88, L118-119, L3217-3252, L3459-3466, L3483-3489, L3529-3536, L3556-3570, L3677-3678, L3700-3703, L3707-3712, L3733-3735 |
| added | `src/deploy_workflow/research/web_allowlist.json` | +117 −0 | L1-117 |
| modified | `src/deploy_workflow/research/webfetch.py` | +23 −4 | L364-365, L401-402, L475-477, L513, L523-524, L528-530, L536-545 |
| added | `src/deploy_workflow/research/weblookup.py` | +1587 −0 | L1-1587 |
| modified | `src/deploy_workflow/run_start/service.py` | +9 −7 | L48-56 |
| modified | `src/deploy_workflow/run_start/submissions.py` | +6 −0 | L36, L782-786 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +363 −1 | L8, L2474-2475, L2502, L7263-7621 |
| modified | `tests/test_inbox_runs.py` | +13 −0 | L117-129 |
| modified | `tests/test_run_start_page.py` | +26 −0 | L850-875 |
| modified | `tests/test_run_start_submissions.py` | +58 −0 | L23, L253-309 |
| added | `tests/test_web_lookup_tools.py` | +2064 −0 | L1-2064 |
| added | `tests/test_weblookup.py` | +1784 −0 | L1-1784 |
