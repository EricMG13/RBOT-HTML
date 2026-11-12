# Changes for the work PC

From `9f862d8267fe` (the version the work PC last adapted) to `214f27fcad2d` (2026-11-12T01:21:20Z). 25 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `38d23de` 2026-11-11 docs(work-pc): change pack for 9f862d8
- `4d6eca6` 2026-11-12 Library: list runs whose methods changed, marked Earlier methods (Merge pull request #48 from EricMG13/claude/list-earlier-method-runs)
- `214f27f` 2026-11-12 Presets: CP-DR and CP-2E on every pathway; CP-2G on two; CP-8 leaves the portfolio preset (Merge pull request #49 from EricMG13/claude/module-presets)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `METHODOLOGY-REVIEW.md` | +5 −0 | L706-710 |
| modified | `README.md` | +3 −2 | L94-96 |
| modified | `VERIFICATION.md` | +32 −0 | L7-38 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +8 −5 | L110-117 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +28 −0 | L170-178, L2441-2459 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +9 −5 | L796-798, L807, L819, L1327, L1329, L1333, L1338 |
| modified | `apps/issuer-library/update_library.py` | +12 −2 | L140-147, L208, L289, L291-292 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/rulings/2026-11-11-cpdr-web-search-live-test.md` | +24 −0 | L1-24 |
| added | `docs/rulings/2026-11-11-module-presets-and-changes.md` | +50 −0 | L1-50 |
| modified | `docs/rulings/2026-11-11-reader-and-issuer-report.md` | +2 −0 | L274-275 |
| added | `docs/rulings/2026-11-11-reader-format-live-test.md` | +23 −0 | L1-23 |
| modified | `docs/superpowers/specs/2026-11-09-credit-os-static-pages.md` | +1 −0 | L21 |
| modified | `docs/superpowers/specs/2026-11-09-inbox-automation-design.md` | +1 −0 | L167 |
| modified | `docs/templates/context-form.html` | +22 −27 | L572-577, L581-582, L584-589, L593, L659, L979-981, L1195, L2147, L2234 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/contracts.py` | +12 −15 | L50-51, L53, L55-56, L59-60, L63-67, removed after L68 |
| modified | `src/deploy_workflow/inbox/activity.py` | +1 −1 | L49 |
| modified | `src/deploy_workflow/library_index.py` | +16 −10 | L3-4, L14, L16-20, L291-293, L297, L310-311, L440, L462 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +4 −8 | L1679-1682 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/canned_provider_launcher.py` | +2 −2 | L15, L41 |
| modified | `tests/fixtures/run-expectations/outcome-key.json` | +5 −1 | L497, L499-501, L503 |
| modified | `tests/test_context_form.py` | +5 −4 | L40, L77-80 |
| modified | `tests/test_cpos_launch.py` | +81 −35 | L58-61, L75-76, L78-82, L84-85, removed after L87, L89-105, L107, L985-986, L988-989, L991-996, L1000-1007, L1017, L1028, L1511-1524, L1527-1530, L1532-1535, L1582, L1689-1691, L1694-1697 |
| modified | `tests/test_inbox_activity.py` | +16 −8 | L43-49, L51-59 |
| modified | `tests/test_library_index.py` | +40 −21 | L68, L71-83, L229-233, L239-246, L449, L461-468, L474-477 |
| modified | `tests/test_update_library.py` | +24 −1 | L7, L187, L240-261 |
