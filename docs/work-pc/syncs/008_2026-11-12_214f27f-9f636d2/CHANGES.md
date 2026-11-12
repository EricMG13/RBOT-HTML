# Changes for the work PC

From `214f27fcad2d` (the version the work PC last adapted) to `9f636d2560bb` (2026-11-12T01:21:31Z). 26 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `597e671` 2026-11-12 docs(work-pc): change pack for 214f27f
- `9f636d2` 2026-11-12 Run start page searches the web for CP-DR; citation markers removed; page fixes (Merge pull request #51 from EricMG13/claude/web-search-run-page)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `METHODOLOGY-REVIEW.md` | +10 −0 | L711-720 |
| modified | `README.md` | +3 −1 | L78-80 |
| modified | `VERIFICATION.md` | +76 −79 | L7-82, removed after L996 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +2 −1 | L69-70 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +2 −0 | L227-228 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +3 −1 | L953-955 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/VERIFICATION-ARCHIVE.md` | +91 −0 | L1-91 |
| modified | `docs/rulings/2026-11-11-reader-and-issuer-report.md` | +10 −0 | L235-244 |
| modified | `docs/rulings/2026-11-11-run-start-submit.md` | +19 −1 | L6, L15-32 |
| modified | `docs/templates/context-form.html` | +23 −8 | L464, L513, L1001-1004, L1213-1214, L1223, L1510, L1758-1767, L1774-1775, L2237 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/markdown_delivery.py` | +4 −3 | L917-920 |
| modified | `src/deploy_workflow/model/handoff.py` | +245 −10 | L17, L22, L52, L96-143, L152-161, L320-364, L367-373, L376, L452-453, L511-525, L528-531, L534-539, L541, L547, L565-626, L653, L687, L750-758, L835-861, L1007-1008 |
| modified | `src/deploy_workflow/owners/cp2g.py` | +3 −3 | L364, L436, L1481 |
| modified | `src/deploy_workflow/owners/cpos.py` | +6 −5 | L375-376, L456-457, L462-463 |
| modified | `src/deploy_workflow/owners/cpos_forecast.py` | +167 −24 | L3-7, L25, L27, L33-40, L45-47, L50-51, L120, L124, L132, L145-256, L273, L278-284, L286-287, L293, L295, L297-300, L302-308, L329-332, L370-373, L384 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +86 −11 | L59-66, L1345-1351, L1361, L1393-1399, L1517-1551, L1747, L1749-1753, L1758-1764, L1781-1782, removed after L1793, L1799, L1838-1845, L1973-1975, L2109 |
| modified | `src/deploy_workflow/prose_checks.py` | +41 −0 | L657-677, L694, L796-813, L819 |
| modified | `src/deploy_workflow/run_start/submissions.py` | +3 −0 | L28-29, L540 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/run-expectations/outcome-key.json` | +1 −1 | L3 |
| added | `tests/test_citation_markers.py` | +108 −0 | L1-108 |
| modified | `tests/test_context_form.py` | +21 −0 | L229-249 |
| modified | `tests/test_cpos_launch.py` | +477 −12 | L749, L781-871, L1780-1782, L1784, L1786-1795, L2213-2220, L2261-2265, L2268, L2271-2274, L2276-2279, L2332-2341, L2354, L2420-2748, L2766, L4198-4205 |
| modified | `tests/test_prose_checks.py` | +15 −0 | L535-549 |
| modified | `tests/test_run_start_page.py` | +19 −5 | L239, L247, L263, L676-679, L730, L754-758, L954-956, L998-1000 |
| modified | `tests/test_run_start_submissions.py` | +18 −0 | L247-264 |
| added | `tests/test_web_search_scope.py` | +192 −0 | L1-192 |
