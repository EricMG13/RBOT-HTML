# Changes for the work PC

From `01ba2a45d93b` (the version the work PC last adapted) to `643c0cddc59e` (2026-11-12T21:04:47Z). 12 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `76186bd` 2026-11-12 docs(work-pc): change pack for 01ba2a4
- `643c0cd` 2026-11-12 Merge pull request #78 from EricMG13/claude/redesign-run-start

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `README.md` | +29 −24 | L153-161, L163-177, L180, L184-185, L194-195 |
| modified | `VERIFICATION.md` | +11 −0 | L7-17 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/design/2026-11-12-redesign-pass-1.md` | +3 −4 | L63, L85-86 |
| added | `docs/design/2026-11-12-run-start-four-steps.md` | +102 −0 | L1-102 |
| modified | `docs/superpowers/specs/2026-11-11-existing-issuer-run-start-design.md` | +5 −0 | L5-9 |
| modified | `docs/superpowers/specs/2026-11-11-staged-run-start-design.md` | +19 −1 | L5-22, L69 |
| modified | `docs/templates/README.md` | +3 −3 | L314-316 |
| modified | `docs/templates/context-form.html` | +382 −199 | L8, L14, L20, L37-38, L46-50, L52-54, L56, L58-59, L61-79, L84-112, L130-131, L133-135, L138-140, L142, L162, L174-191, L261-268, L271-281, L307-308, L312, L315, L317-325, L329, L331-337, L340, L342-347, L349, L351-387, removed after L394, L397-398, L403-408, L411, L416, L418-420, L422-425, L427, L429-430, L441-442, L445-446, removed after L452, L458-477, L481-482, removed after L485, removed after L502, L505, L546, L558, L586, L632, L647, removed after L648, removed after L649, L657-667, removed after L669, L671-690, L693-699, L703-709, L1480-1488, L1490, L1492, L1496-1497, L1506-1507, L1512, L1523-1535, L1538, L1540, L1556-1557, L1567-1570, L1574, L1578-1580, L1582-1583, L1585, L1588, L1591-1595, L1597, L1601-1605, removed after L1606, L1609, L1612, L1614, L1616, L1620, L1623, L1627, L1672-1673, L1753-1754, L1764, L1872, L1889, L1935, L1939-1941, L1945-1947, L2013-2016, L2019, L2021, L2025-2026, L2059, L2082-2084, removed after L2087, L2089-2092, L2226, L2235, L2590-2593, L2713-2714, L2717-2718, L2721-2722, L2725, L2864, L2965 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/fixtures/run_start_sentences_a6eec82.json` | +157 −0 | L1-157 |
| modified | `tests/test_context_form.py` | +102 −2 | L9, L182-184, removed after L189, L191, L201-224, L277-349 |
| modified | `tests/test_library_page_browser.py` | +1 −1 | L817 |
| modified | `tests/test_run_start_page.py` | +1025 −55 | L147, L158-159, L232-234, L237-245, L247, removed after L248, L251-252, L254-273, removed after L274, removed after L275, removed after L277, L280-409, L508-509, L591, L598-599, L764-765, L767-768, L791, L960-962, L971-976, L978-983, L1110, L1586-1610, L1752, L1760, L1827, L1920-1922, L1925, L2859-3657 |
