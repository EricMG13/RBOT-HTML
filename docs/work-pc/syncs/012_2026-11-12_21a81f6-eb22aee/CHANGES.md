# Changes for the work PC

From `21a81f633802` (the version the work PC last adapted) to `eb22aee01e16` (2026-11-12T04:32:29Z). 33 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `99afe9e` 2026-11-12 docs(work-pc): change pack for 21a81f6
- `eb22aee` 2026-11-12 feat(cp8): CP-8 runs in the run as Changes since the last run (Merge pull request #55 from EricMG13/claude/cp8-changes-r3)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `METHODOLOGY-REVIEW.md` | +20 −0 | L712-731 |
| modified | `VERIFICATION.md` | +27 −0 | L7-33 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/store.py` | +2 −1 | L3437-3438 |
| modified | `apps/issuer-library/credit_os/web/screen.js` | +3 −3 | L26-27, L37 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/VERIFICATION-ARCHIVE.md` | +122 −0 | L92-213 |
| modified | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +141 −0 | L51-191 |
| modified | `docs/templates/context-form.html` | +4 −3 | L625, L1665, L1795-1796 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/methodology.json` | +2 −2 | L540, L551 |
| modified | `src/deploy_vii/methods/cp8.md` | +156 −40 | L1-156 |
| modified | `src/deploy_vii/registry.py` | +20 −5 | L27-30, L88-89, L98-99, L107-118 |
| added | `src/deploy_workflow/changes.py` | +811 −0 | L1-811 |
| added | `src/deploy_workflow/changes_check.py` | +713 −0 | L1-713 |
| modified | `src/deploy_workflow/credit_os_catalogue.py` | +3 −2 | L154-156 |
| modified | `src/deploy_workflow/handoff_delivery.py` | +4 −0 | L153-156 |
| modified | `src/deploy_workflow/inbox/runs.py` | +7 −0 | L8, L29, L72, L189-190, L219-220 |
| modified | `src/deploy_workflow/inbox/scheduler.py` | +6 −2 | L239-241, L282-283, L310 |
| modified | `src/deploy_workflow/markdown_delivery.py` | +5 −0 | L890-894 |
| modified | `src/deploy_workflow/owners/cpos.py` | +132 −16 | L28, L48, L61, L67, L79-85, L103-113, L118-129, L387-389, L391, L416-418, L458-466, L473-489, L494, L502-522, L529-542, L566, L568-569, L613-614, L628, L639-661 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +312 −9 | L23, L36-46, L71-72, L79-85, L208-209, L370-371, L1397-1401, L1429-1433, L1607-1617, L1803-1943, L1953-1954, L1958-1967, L1971-2008, L2017-2051, L2058, removed after L2065, L2067-2070, L2102-2106, L2122-2125, L2133-2135, L2149, L2153-2157, L2162, L2178-2179, L2221-2227, L2321, L2376-2380, L2495 |
| modified | `src/deploy_workflow/prose_checks.py` | +40 −3 | L174-175, L186-191, L199-230 |
| modified | `src/deploy_workflow/run_start/service.py` | +7 −3 | L48-54 |
| modified | `src/deploy_workflow/run_start/submissions.py` | +50 −12 | L34, L588-596, L601-602, L640, L643, L645, L647-660, L663-665, L676, L696, L742-744, L754-756, L758-766, L773 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/canned_provider_launcher.py` | +85 −2 | L15, L22-98, L103, L119-124 |
| modified | `tests/fixtures/fake_launcher.py` | +1 −1 | L23 |
| modified | `tests/fixtures/real_shape_launcher.py` | +1 −1 | L34 |
| modified | `tests/library_fixtures.py` | +10 −4 | L86-89, L104, L109-110, L151-152, L208 |
| added | `tests/test_changes.py` | +2179 −0 | L1-2179 |
| modified | `tests/test_cpos_launch.py` | +5 −4 | L750, L1554-1556, L1578 |
| modified | `tests/test_credit_os_store.py` | +12 −0 | L1086-1097 |
| modified | `tests/test_inbox_runs.py` | +21 −0 | L438-458 |
| modified | `tests/test_run_start_page.py` | +4 −0 | L696-699 |
| modified | `tests/test_run_start_scheduler.py` | +61 −0 | L201-261 |
| modified | `tests/test_run_start_submissions.py` | +40 −3 | L19, L248-282, L588, L788-790 |
