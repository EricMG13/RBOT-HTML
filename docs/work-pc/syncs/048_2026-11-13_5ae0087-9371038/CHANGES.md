# Changes for the work PC

From `5ae00873d407` (the version the work PC last adapted) to `93710385933f` (2026-11-13T13:36:54Z). 51 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `d941eef` 2026-11-13 docs(work-pc): change pack for 5ae0087
- `9371038` 2026-11-13 Issuer library redesign: typed components on every screen; audit material only on Evidence (Merge pull request #98 from EricMG13/claude/report-redesign-evidence)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `AGENTS.md` | +4 −1 | L35-38 |
| modified | `VERIFICATION.md` | +10 −0 | L7-16 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/README.md` | +58 −24 | L21-76, L164-165 |
| modified | `apps/issuer-library/credit_os/web/changes.js` | +160 −126 | L4-6, L13-16, removed after L24, removed after L35, L52-53, L55-58, L60-67, L69-91, L94-95, L97-98, L101-114, L117-148, L150, L152-160, L165-167, L169, L171-172, L175-176, L178-188, L224, L235-239, L242-244, L246-258, L265, L267-273, L275-279, L282, L285 |
| modified | `apps/issuer-library/credit_os/web/changes.test.cjs` | +338 −89 | L7, L69-74, L76-78, L80-81, L83-87, L92, L94-108, L114-115, L118, L121-123, L126, L128-134, L136, L141, L143, L155, L166, L171, L175, L177, L236, L238-249, L252-263, L266-270, L272-274, L280, L282-283, L285-287, L338, L340-341, L351, L359, L362, L364-369, L372-378, L380-601, L604-606 |
| added | `apps/issuer-library/credit_os/web/components.js` | +1192 −0 | L1-1192 |
| added | `apps/issuer-library/credit_os/web/components.test.cjs` | +1563 −0 | L1-1563 |
| added | `apps/issuer-library/credit_os/web/events-maps.test.cjs` | +292 −0 | L1-292 |
| added | `apps/issuer-library/credit_os/web/evidence.js` | +479 −0 | L1-479 |
| added | `apps/issuer-library/credit_os/web/evidence.test.cjs` | +631 −0 | L1-631 |
| added | `apps/issuer-library/credit_os/web/icons/arrow-down.svg` | +14 −0 | L1-14 |
| added | `apps/issuer-library/credit_os/web/icons/arrow-up-right.svg` | +14 −0 | L1-14 |
| added | `apps/issuer-library/credit_os/web/icons/banknote.svg` | +15 −0 | L1-15 |
| added | `apps/issuer-library/credit_os/web/icons/building.svg` | +15 −0 | L1-15 |
| added | `apps/issuer-library/credit_os/web/icons/copy.svg` | +14 −0 | L1-14 |
| added | `apps/issuer-library/credit_os/web/icons/globe.svg` | +15 −0 | L1-15 |
| added | `apps/issuer-library/credit_os/web/icons/history.svg` | +15 −0 | L1-15 |
| added | `apps/issuer-library/credit_os/web/icons/info.svg` | +15 −0 | L1-15 |
| added | `apps/issuer-library/credit_os/web/icons/scale.svg` | +17 −0 | L1-17 |
| modified | `apps/issuer-library/credit_os/web/index.html` | +1 −1 | L28 |
| modified | `apps/issuer-library/credit_os/web/reader.js` | +47 −52 | L5-6, removed after L46, removed after L240, L302-303, L305, L316-336, L340-341, L343, L345-346, L350-360, L403, L408, L418, L422, L485 |
| modified | `apps/issuer-library/credit_os/web/reader.test.cjs` | +26 −50 | L6, removed after L140, removed after L196, L310-311, L330, L553-574 |
| modified | `apps/issuer-library/credit_os/web/screen.css` | +1110 −161 | L5, L7, L11-14, L20, L29, L34-35, L128, removed after L148, removed after L256, removed after L260, removed after L261, removed after L262, L264, L266, L323, removed after L453, L455-456, L474-475, L496, removed after L572, removed after L579, L598-600, removed after L601, removed after L638, removed after L639, removed after L642, removed after L643, L658, L672, L681, L689, L696-697, L742-743, L745, L751, L753, removed after L754, removed after L768, removed after L769, L771, L773-1848 |
| modified | `apps/issuer-library/credit_os/web/screen.js` | +173 −70 | L53, L55, L92-94, L98, L153-154, L157, L166, L242-243, L254-255, L264, L268-271, L274, L277-287, L320, L326, L332-334, L336-337, L388-393, L401-402, L405, removed after L413, L425, L428, L464, L469-483, removed after L492, L522, L525-526, L541-549, L553-580, L582-599, L603, L627, L646, L660-663, L672-673, L681, L683, L692, L697-702, L713-714, L718, L720, L722, L724, L727, L730-731, L737, L745-746, L758, L762-763, L790, L793-794, L797, L802-803, L805-806, L809-812, L815-816, removed after L819, removed after L821, L826-828 |
| added | `apps/issuer-library/credit_os/web/shapes.js` | +175 −0 | L1-175 |
| added | `apps/issuer-library/credit_os/web/shapes.test.cjs` | +243 −0 | L1-243 |
| modified | `apps/issuer-library/credit_os/web/static-boot.js` | +1 −1 | L23 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +2338 −717 | L93-100, L118, L120, L123-125, L127, L130-132, L145-152, L155-157, L162-164, L169-170, L173, L177-181, L183-185, L188-195, L199-200, L202, L206-209, L211-214, L218-223, L228-230, L235-239, L241, L281, L376-378, L380, L382, L537, L539-540, L865-867, L870, L905-952, L984-985, L1003, L1006, L1008-1009, L1058-1064, L1067, L1069-1071, L1074-1076, L1082-1084, L1086-1107, L1109-1122, L1125-1134, L1137, L1140, L1145-1149, L1152, L1157-1159, L1162, L1166, L1170, L1176-1178, L1187, L1189, L1192, L1197-1198, L1201-1203, L1205-1207, L1209-1371, L1374-1418, L1421-1423, L1425, L1428, L1431, L1433-1434, removed after L1443, removed after L1449, L1499, L1502-1503, L1505-1511, L1535-1536, L1540-1541, L1561-1629, L1631-1652, L1664-1667, L1688, L1699-1715, L1729, L1732, L1734-1735, L1737-1747, L1749-1827, L1830-1832, L1837-1870, L1872-1875, L1877, L1880-1886, L1889, L1892, L1894, L1896-1935, L1937-1987, L1991, L1993-1995, removed after L1997, L2006, L2009, L2011, L2064, L2070, L2073-2079, L2081, L2083-2085, removed after L2086, L2104, L2141, L2143-2148, L2151, L2153-2156, L2160-2162, L2538, L2657, L2689, L2692, L2705-2707, L2712-2713, L2715-2717, L3184, L3217-3222, L3224, L3226, L3229, L3231-3232, L3234-3266, L3268-3280, L3289-3292, L3294-3295, L3302, L3306-3316, L3324-3325, L3331, L3347, L3354, L3359, L3413, L3433, removed after L3495, L3497, L3510, L3512-3513, L3516-3523, L3527-3530, L3536, L3538-3539, L3546, L3557, L3567, L3569-3570, L3573-3576, L3588, L3591-3592, L3596-3599, L3602, L3605-3606, L3609, L3613-3615, L3654, L3656-3663, L3665, L3668-3670, L3673, L3676-3679, L3682, L3684-3747, L3749-3755, L3814, L3816, L3821, L3827-3828, L3841, L3846, L3892-3893, L3901, L3958-3965, L3971-5212 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +836 −473 | L102, L144, L147, L193-195, L197-198, L200, L212, removed after L219, L223-226, L230-231, L234, L255-259, removed after L297, L302-306, L312-314, L333-343, L349, L352-354, L363-365, L374, L376, L379, L381, L389, L392-393, L405-407, L409, L411, L415-416, L418-420, L429, L435-440, L442-443, L451-455, L459-460, L462-471, L473-474, L477-478, L497-498, L522-523, L590-591, L613, L637, L644-646, L653-656, L658, L669-671, L673-677, L679-680, L683-684, L686-690, L701-728, L734-738, L745, L749-751, L754-792, L794-795, L797, L799-814, L816-823, L826-833, L836, L881-889, L891, L898, L914, L920, L937, L950, L952-959, L962-963, L965-968, L976-983, L991-992, L995-996, L1003-1004, L1027, L1032-1042, L1045-1047, L1049-1051, L1053-1054, L1057-1058, L1061, L1076-1084, L1106-1118, L1201-1293, L1297, L1307-1327, L1336, L1373-1381, L1384, L1386-1389, L1397, L1403-1404, L1407, L1414-1426, L1428-1486, L1489, L1491-1493, removed after L1494, L1496, L1505, L1509, L1513-1514, L1519-1521, L1530-1558, L1566, L1568, L1574-1596, L1609-1616, L1622, L1627, removed after L1636, L1646-1649, removed after L1653, L1655-1656, L1664-1676, L1678-1713, L1715-1732, L1738-1749, L1751, L1755-1756, L1759-1786, L1788-1801, L1803-1806, L1808, L1812-1816, L1819-1820, L1822-1824, L1826-1830, L1833-1864, removed after L1865, L1874-1881, L1890-1907, L1909-1911, L1916-1917, L1923, L1932, L1936-1942, L1945, L1949-1950, L1958 |
| added | `apps/issuer-library/fixtures/shape-key.json` | +376 −0 | L1-376 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/superpowers/plans/2026-11-13-library-redesign.md` | +320 −0 | L1-320 |
| added | `docs/visualisations/2026-11-13-screen-component-map.md` | +389 −0 | L1-389 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/browser_probe_chip_overlap.js` | +10 −7 | L2-3, L5, L7, L9, L12-16 |
| modified | `tests/browser_probe_chrome.js` | +3 −2 | L6, L19-20 |
| modified | `tests/browser_probe_edges.js` | +3 −0 | L14-16 |
| modified | `tests/browser_probe_field_card.js` | +1 −1 | L8 |
| modified | `tests/browser_probe_gaps.js` | +2 −1 | L8-9 |
| modified | `tests/browser_probe_header_scope.js` | +9 −5 | L2, L8, L13-16, L21-23 |
| modified | `tests/browser_probe_index.js` | +5 −4 | L3, removed after L5, L11-13, L19 |
| modified | `tests/browser_probe_module_page.js` | +13 −5 | L20, L23, L25-31, L34, L46, L51-52 |
| modified | `tests/browser_probe_narrow_tables.js` | +3 −3 | L5, L9, L17 |
| modified | `tests/browser_probe_overview.js` | +3 −2 | L13, L15-16 |
| modified | `tests/browser_probe_overview_layout.js` | +34 −38 | L2-3, removed after L10, L12-13, L15, removed after L16, L19-20, L23-24, L27, L30-40, L43-49, L52-57 |
| modified | `tests/browser_probe_run_activity.js` | +6 −13 | removed after L6, L12-15, L17, L21 |
| modified | `tests/browser_probe_sections.js` | +2 −2 | L16, L22 |
| modified | `tests/browser_probe_start_run.js` | +1 −1 | L12 |
| modified | `tests/test_cpos_launch.py` | +26 −5 | L4266-4268, L4272-4283, L4379-4389 |
| modified | `tests/test_library_changes_browser.py` | +121 −6 | L13, L160, L173-178, L180-193, L209-210, L277-373 |
| modified | `tests/test_library_page_browser.py` | +721 −249 | L42-56, L179-180, L221, L223, L225-227, L229-230, L233-234, L237-238, L241-242, L244-251, L257, L268, L281, L284, L291, L326-328, L330-331, L369-374, L435-440, L498, L504, L506-508, L511, L514, L519-525, L527-529, L532, L537-539, L541-542, L551, L648, L729-732, L921-924, L926, L958-960, L979, L986-988, L1202, L1205-1213, L1248, L1267-1268, L1270-1273, L1277, L1281, L1391-1392, L1396-1397, L1417, L1421-1422, L1425, L1427, removed after L1428, L1432-1435, L1501-1502, L1506-1510, L1519-1522, L1529-1533, L1535-1538, L1540, L1580-1581, L1584, L1601-1602, L1604-1605, L1607-1609, L1658-1665, L1767-1769, L1771, L1773-1781, L1786-1787, L1794, L1796, L1827-1829, L1834, L1836, L1854, L1865-1868, L1876, L1906, L1908-1911, L1928-1931, L1934-1936, L1947-1948, L1970, L1972-1978, L1981, L1986-1987, L1993, L2019-2024, L2026-2027, L2029-2032, L2038-2041, L2043-2045, removed after L2046, L2048-2090, L2092-2098, L2106-2107, L2110-2113, L2115-2116, L2118-2141, L2146-2149, L2152-2153, L2282, removed after L2283, L2286-2292, L2312, L2315-2317, L2327, L2353, L2388-2390, L2442-2443, L2451-2467, L2477-2480, L2538-2885 |
| modified | `tests/test_library_reader_refs.py` | +2 −1 | L233-234 |
| modified | `tests/test_run_start_page.py` | +9 −1 | L1594-1602 |
