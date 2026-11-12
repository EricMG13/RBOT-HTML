# Changes for the work PC

From `643c0cddc59e` (the version the work PC last adapted) to `dc32ab4925bc` (2026-11-12T22:10:30Z). 27 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `16e9c0d` 2026-11-12 docs(work-pc): change pack for 643c0cd
- `dc32ab4` 2026-11-12 Module output review changes: sources resolve, each drawing shown once, reader vocabulary checked everywhere (Merge pull request #79 from EricMG13/claude/modules-page-sources-charts)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `METHODOLOGY-REVIEW.md` | +13 −0 | L750-762 |
| modified | `VERIFICATION.md` | +33 −41 | L7-39, removed after L977 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +2 −1 | L54-55 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/store.py` | +54 −11 | L22-23, L303-308, L310-326, L332, L633-635, L643-647, L664, L834, L870, L1070-1079, L1160, L3649-3651, L3662-3664 |
| modified | `apps/issuer-library/credit_os/web/calendar.js` | +63 −1 | L69-131 |
| modified | `apps/issuer-library/credit_os/web/calendar.test.cjs` | +101 −1 | L4, L77-176 |
| modified | `apps/issuer-library/credit_os/web/reader.js` | +58 −16 | L79-82, L87-90, L107, L120-121, L125, L142, L144, L218-228, L342-350, L352-354, L356-358, L362-363, L370-371, L373-380, L389-394 |
| modified | `apps/issuer-library/credit_os/web/reader.test.cjs` | +97 −1 | L128-135, L395, L410-439, L540-597 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +48 −7 | L402-407, L513, L530-532, L535-541, L544-561, L565-566, L610-611, L834-842 |
| modified | `apps/issuer-library/credit_os/web/screen.js` | +2 −2 | L259, L308 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +549 −17 | L449, L480-491, L512, L522, L530-531, L797, L926, L928, L1336, L1360, L1393-1394, L1630, L1655-1662, L1780-1873, L1935, L1947-1967, L2216, L2219, L2278-2306, L2341, L2398, L2420, L2461-2520, L2554, L2592-2706, L3076-3265 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +174 −53 | L26-27, L29, L33, L71-72, L76-78, L88, L212-234, L254-255, L294-295, L311-320, L323-330, L456, L462-465, L484-485, L488, L525, L531-532, L542, L633-655, L658-667, L678, L680-682, L693, L697-699, L780, L785, L788-799, L801-807, L813, L815, L834, L836-840, L844, L847, L849-868, L870-873, L875-878, L880, L883-884, L887-888, L891, L895 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/rulings/2026-11-12-module-output-review-changes.md` | +88 −0 | L1-88 |
| added | `docs/superpowers/plans/2026-11-12-module-output-review-changes.md` | +143 −0 | L1-143 |

### reviews

| Status | File | +/- | Where |
|---|---|---|---|
| added | `reviews/2026-11-12-module-output-adversarial/earlier-run-tdg-reader-format-001.md` | +4572 −0 | L1-4572 |
| added | `reviews/2026-11-12-module-output-adversarial/latest-run-tdg-proof-snapshot-opus-002.md` | +6826 −0 | L1-6826 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| added | `src/deploy_workflow/confidence.py` | +278 −0 | L1-278 |
| modified | `src/deploy_workflow/credit_os_chips.py` | +96 −30 | L5, L13, L44-45, L139-147, L150-152, L160-161, L165-169, L213-244, L262-263, removed after L291, L294-297, L301, L303, L342-365, L371-374, L550-551, L664-666 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +235 −22 | L35, L297-298, L310-311, L328-329, L334-363, L399-400, L402-404, L406-437, L632-635, L703-730, L743, L1248-1251, L1432-1435, L1453-1458, L1467-1477, L1490, L1544-1559, L1565-1567, L1685-1695, L1697-1700, L1837-1838, L1959-1962, L1968-1974, L1987-2000, L2076-2087, L2142-2143, L2145, L2149-2151, L2579-2600, L2618 |
| modified | `src/deploy_workflow/prose_checks.py` | +164 −29 | L1-2, L66, L91-93, L95, L102-107, L113-118, L122-138, L244-254, L261, L273-281, L318, L330-371, L388-390, L402-438, L440-441, L443-447, L845-847, L849-858, L861-862, L864, L866 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +52 −3 | L448, L455, L464, L2857-2905 |
| added | `tests/test_confidence.py` | +436 −0 | L1-436 |
| modified | `tests/test_cpos_launch.py` | +411 −5 | L161-176, L423-435, L506, L1472-1473, L1485-1486, L1635-1647, L1791-1792, L1802-1903, L4786, L5446-5704 |
| modified | `tests/test_credit_os_chips.py` | +192 −0 | L34, L37, L832-1021 |
| modified | `tests/test_credit_os_store.py` | +136 −3 | L20, L22, L418-420, L2170-2300 |
| modified | `tests/test_library_page_browser.py` | +40 −0 | L2141-2180 |
| modified | `tests/test_prose_checks.py` | +241 −0 | L550-790 |
