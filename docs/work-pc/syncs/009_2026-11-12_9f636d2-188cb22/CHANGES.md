# Changes for the work PC

From `9f636d2560bb` (the version the work PC last adapted) to `188cb225aadf` (2026-11-12T01:32:07Z). 15 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `6299087` 2026-11-12 docs(work-pc): change pack for 9f636d2
- `188cb22` 2026-11-12 Run start: start a run from an earlier run of the same issuer (Merge pull request #52 from EricMG13/claude/initiating-runs-existing-issuers-4a8739)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +21 −31 | L7-27, removed after L986 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +2 −1 | L46-47 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +23 −0 | L126-148 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +3 −2 | L821-822, L1275 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/superpowers/plans/2026-11-11-existing-issuer-run-start.md` | +412 −0 | L1-412 |
| added | `docs/superpowers/specs/2026-11-11-existing-issuer-run-start-design.md` | +183 −0 | L1-183 |
| modified | `docs/templates/context-form.html` | +260 −18 | L110, L375, L521, L537, L543, L1815, L1869, L1871, L1883, L1899, L1904-1905, L1912, L1926-1929, L1974-1980, L1997, L2008, L2027, L2034, L2102, L2110-2301, L2308, L2311-2319, removed after L2336, L2338-2341, L2343, L2349, L2351-2352, L2410, L2422-2426, L2519, L2533-2542, L2746-2747, L2754, L2763 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| added | `src/deploy_workflow/run_start/prior.py` | +106 −0 | L1-106 |
| modified | `src/deploy_workflow/run_start/service.py` | +41 −4 | L57-66, L108, L129-135, L369-374, L393-394, L408-409, L420-432 |
| modified | `src/deploy_workflow/run_start/submissions.py` | +158 −6 | L11, L20, L33, L204, L208-210, L212-226, L305, L316-317, L338, L352, L383-513 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_library_page_browser.py` | +53 −0 | L1138-1190 |
| modified | `tests/test_run_start_page.py` | +864 −4 | L25, L29, L136, L153, L1540-2399 |
| added | `tests/test_run_start_prior.py` | +142 −0 | L1-142 |
| modified | `tests/test_run_start_service.py` | +99 −0 | L13, L359-361, L831-925 |
| modified | `tests/test_run_start_submissions.py` | +386 −0 | L11, L936-1320 |
