# Source of the Credit OS copy

Copied read-only from `~/Documents/Final-workflow-PY` at commit `07e14eca` (apps/issuer-library/web and
apps/issuer-library/engine were clean there). Copied files are excluded from the 800-line PR cap only while
byte-identical to the source; edits below count against it.

Also copied byte-identical (sha256 e50f55b76a8730c6da70160b8d8214f7e1c3f54a7ddca57ba35bc81584cbb087):
`docs/visualisations/catalogue.csv` -> `docs/visualisations/catalogue.csv`. store.py reads it through
`REPO / "docs/visualisations/catalogue.csv"` (REPO resolves to this repo's root), so `workspace_store` fails
without it.

## Files (path here relative to apps/issuer-library/credit_os; source path relative to Final-workflow-PY apps/issuer-library; sha256 of the source file)

| File | Source | sha256 at source | Identical now |
| --- | --- | --- | --- |
| `catalog.json` | `engine/catalog.json` | `246632c321c6bd9b54119295b1b336a7826fec9ae8c34eae882574be85ff36a2` | NO, edited (see Task 7) |
| `store.py` | `engine/store.py` | `7e616ca5d4865dc5ff9d0bd9588761acba898d7aa47ce4d8b416646a25e4424d` | NO, edited (see below) |
| `web/brand/symbol.svg` | `web/brand/symbol.svg` | `67d73e1e8a6700b1528dabb1ad4c2e91963325bbde625cc4f84be5e294430dfd` | yes |
| `web/brand.css` | `web/brand.css` | `f32514f93805caeee3c910fc019683d405e98a0860140d839b4ac242d1e52e4f` | yes |
| `web/fonts/OFL.txt` | `web/fonts/OFL.txt` | `98eac4800faf2b800dfb11f82e38b779ebe473e05e343c18aeb65eabb74442ae` | yes |
| `web/fonts/RedHatDisplay-Bold.woff2` | `web/fonts/RedHatDisplay-Bold.woff2` | `a28973642bc0dc1404138a6b32031b5f1bbc131d1b5a92a0214d16cfe8091793` | yes |
| `web/fonts/RedHatDisplay-SemiBold.woff2` | `web/fonts/RedHatDisplay-SemiBold.woff2` | `5ed4d4d4aa40abda2e2aafd0083e3ee109290c3e86392778e934755a4db67332` | yes |
| `web/fonts/RedHatMono-Medium.woff2` | `web/fonts/RedHatMono-Medium.woff2` | `ab9f475ace2c1e5ed9ee31d964bbadd72dd84b6ab65e71445be80f1fe95c7a0d` | yes |
| `web/fonts/RedHatMono-SemiBold.woff2` | `web/fonts/RedHatMono-SemiBold.woff2` | `d3c80dda632cbceb3419ef8c6a54af6bf5139b50b83300f467c3c24cdc8e794c` | yes |
| `web/fonts/RedHatText-Medium.woff2` | `web/fonts/RedHatText-Medium.woff2` | `abfc3d5ff9e975d487ec295895efdc2e5848f804d0982bee87ce0d8f55c9a3d1` | yes |
| `web/fonts/RedHatText-Regular.woff2` | `web/fonts/RedHatText-Regular.woff2` | `8b6c947032e889935aeef9d3a987fe4760b5bb029af531f2511e5824602a550a` | yes |
| `web/fonts/RedHatText-SemiBold.woff2` | `web/fonts/RedHatText-SemiBold.woff2` | `3f3c8935bd6bf319b0b1f3d80b7247646fefa6dd77aca88347d0ab16e7c1e9aa` | yes |
| `web/hydrate.js` | `web/hydrate.js` | `da1530fec0280377adc976efa1a7dba3389197eecc8564ace9870c8a25ea3994` | yes |
| `web/icons/LICENSE` | `web/icons/LICENSE` | `b495047bd93a9b06913511076f504daba17d5bbeb3e0650f3bb53a4220329c57` | yes |
| `web/icons/activity.svg` | `web/icons/activity.svg` | `050fbcda05e13c2051cf857683645e19c6b180861ef4d0cc28a6f09ba1ea1666` | yes |
| `web/icons/arrow-left.svg` | `web/icons/arrow-left.svg` | `c5f4b88076108eb1a0d95336e1aa7e7bb1419a3a92af96f6247d88cd3456f933` | yes |
| `web/icons/arrow-right.svg` | `web/icons/arrow-right.svg` | `288397fdb73bb4f783cf9eabb726ff47357df1d4e3f1201dd748090579f108b9` | yes |
| `web/icons/calendar-days.svg` | `web/icons/calendar-days.svg` | `9330eb8d7c4989e97b6361314abbf02953243c602874725c9e58ceca00da3bd7` | yes |
| `web/icons/chart-no-axes-combined.svg` | `web/icons/chart-no-axes-combined.svg` | `2f8a708c357488cfde7428d9b055b9bb4a99c08dc71e9296da03ecc19291c4ab` | yes |
| `web/icons/check.svg` | `web/icons/check.svg` | `7f33acc9a77a61659531044525fc008edebe215bf4dcf1c789c8674ad3277db0` | yes |
| `web/icons/chevron-down.svg` | `web/icons/chevron-down.svg` | `66ea878e72ed3488bb3b464c39dfdccee8d1f78e560dccea40e5e12da0e87e87` | yes |
| `web/icons/chevron-right.svg` | `web/icons/chevron-right.svg` | `2758143d7b2434e4aa7307dfd34405c87909ff4052f21b5f3f40d45224b4f19b` | yes |
| `web/icons/circle-check.svg` | `web/icons/circle-check.svg` | `3e519680ab8e2a8ad8f56a340c10d61957d872237aaa868cf324b0900a74f384` | yes |
| `web/icons/download.svg` | `web/icons/download.svg` | `3daeee13ded5a3afa2198b1bb4e2262d163922f97d96ac6ff9953e8ed4fe039d` | yes |
| `web/icons/file-text.svg` | `web/icons/file-text.svg` | `52ca55846c202335fb870c8aa23e9345630ec10489303756d62e750f7109605c` | yes |
| `web/icons/files.svg` | `web/icons/files.svg` | `97adf06fc0511e7a40be93ecda04466ed196718ab4a5e3a62b1148cc49697775` | yes |
| `web/icons/folder-open.svg` | `web/icons/folder-open.svg` | `ee57452b40e71df310214091dd9da1941a397c83197b8ff8d7ae66dd4242578b` | yes |
| `web/icons/layers.svg` | `web/icons/layers.svg` | `ce16d0a955e3581cda17f6b2fd5c5bc2034b405f9cecc31c8ebb8495b4afc1bb` | yes |
| `web/icons/layout-grid.svg` | `web/icons/layout-grid.svg` | `b8903f61d09b1d75e55c71158277d26570962f69c2099446a251871e0a2d6678` | yes |
| `web/icons/panel-left.svg` | `web/icons/panel-left.svg` | `029f67b9e3eeb7ddf7c7c499b174c50388725e8ea50d4ea59ed7dbaf8d61cb82` | yes |
| `web/icons/plus.svg` | `web/icons/plus.svg` | `7f6af73bf1ff6c4bca3f18351c8d1bdec6749c0c2530c4de5da85d520c21df17` | yes |
| `web/icons/refresh-cw.svg` | `web/icons/refresh-cw.svg` | `2e10dd403c85a24f163d59fc6151aa21147fe9402e1305dfc8979208caee8944` | yes |
| `web/icons/search.svg` | `web/icons/search.svg` | `283d371c2e433817bb9c0c8310caa6c77fa4177c0f4f1168d9c83b97af7389dc` | yes |
| `web/icons/settings-2.svg` | `web/icons/settings-2.svg` | `06d06c191bd7eb28afaf9d40acb5c49ef69448fdeda91801d9823d7c440a4e10` | yes |
| `web/icons/triangle-alert.svg` | `web/icons/triangle-alert.svg` | `4866f38b8560d410f21e3226413e0b77997b6dfbb6931fadfe0a0d5aef9ffeb4` | yes |
| `web/icons/x.svg` | `web/icons/x.svg` | `4a9cdab38fbb96162e7dace28e33f4ca0e49d8963a6162abc3d4691b7d675117` | yes |
| `web/screen.css` | `web/screen.css` | `b6d3a1d6ccd9a38b323553c385fb3919c08446859a5aad5d309f9fceffd19402` | yes |
| `web/screen.js` | `web/screen.js` | `3f2b152ab197e4191bffb006188d15a303da3b092cf15e96c107713db314a80b` | NO, edited (see below) |
| `web/screening.js` | `web/screening.js` | `f46f679ab376e57ce238f69d420591b7c9c923ac91c7915d07999e0c8406292c` | yes |
| `web/views.js` | `web/views.js` | `087bd61b814e4d8bcf1be4f6cc3a926ce8aba643b6ee919e9937360f602aee45` | NO, edited (see below) |

## Edits after copying (store.py only; lines are in the edited file; no behaviour change)

Made to pass `tools/quality_gate.py` (ruff with tools/ruff-gate.toml, strict mypy). Annotations only, plus a comment split.

| Line | Edit | Why |
| --- | --- | --- |
| 29-30 | Route-key comment split over two lines | ruff E501 (108 > 100) |
| 351-353 | `locate_quote` annotated `(list[dict[str, Any]], dict[str, Any], str) -> dict[str, Any]` | mypy no-untyped-def |
| 392-394 | `default_output` annotated `(str, list[str], str | None, dict[str, int | None]) -> str | None` | mypy no-untyped-def |
| 404-406 | `locate_row` annotated like `locate_quote` | mypy no-untyped-def |
| 418-420 | `pinned_fields` annotated `(list[dict[str, Any]], dict[str, Any], str) -> dict[str, Any]` | mypy no-untyped-def |
| 446 | `_reader_summary` annotated `(dict[str, Any]) -> dict[str, Any] | None` | mypy no-untyped-def |
| 472 | `_chart_table` annotated `(dict[str, Any]) -> dict[str, Any] | None` | mypy no-untyped-def |
| 489-490 | `reader_fields` annotated `(list[dict[str, Any]]) -> dict[str, Any]`; docstring shortened | mypy no-untyped-def; ruff E501 (105 > 100) |
| 653, 661, 684 | Removed three `# type: ignore[no-untyped-call]  # legacy untyped ...` comments | the callees are now typed, so mypy reports them as unused-ignore |

## Static shell (Task 3): edited and derived web files

The pages are static: library and issuer screens only, data from `window.CREDIT_OS_DATA` (set by `data.js`), no server calls, no polling. Edited files count against the 800-line cap.

Files created from Credit OS files (source path relative to Final-workflow-PY apps/issuer-library; source sha256):

| File | Source | sha256 at source | What changed, why |
| --- | --- | --- | --- |
| `web/index.html` | `web/index.html` | `246830bf3578f1c7c5c4b5238ff7fd90055220e71b58c8fc6d777f2bbc3787b4` | Rail reduced to Issuer library, Reports, Search; removed the workspace-updated and service-down notices, `#run-strip` and the `#new-run` section; scripts are `data.js` then `static-boot.js` (was `boot.js`). No run controls, no server. |
| `web/static-boot.js` | `web/boot.js` | `303ff7ffbee04488dbc09aee7d3ef7791d3f29f5c259d656d5cf27fb4a0a3581` | Reads `window.CREDIT_OS_DATA` instead of `/api/catalogue` and `/api/workspace`; calls `hydrate(workspace)`; sets the same `DESIGN_*` globals; a missing or unreadable data file is stated in `DESIGN_APP.problem` and the console. Dropped the 30 s discovery poll, reload buttons, `watchRuns`, and `actions.js` from the script list. |
| `web/shared.js` | `web/actions.js` | `31c83561213c309843d1f13a17ddca53988f81005cbd9f754ee6644b476469c7` (lines 168-170 only) | Keeps `titleBase` and `applyTitle` (without the `runMark` prefix, which only the run watcher set). `shownRunHref` and `presentRun` are not moved: they only served the run watcher and strip, so their call sites are deleted (a copy would be a stub). `loadRunActivity`, `installNewRun`, `installSettings` are deleted. |

Edits to copied files:

| File | Edit | Why |
| --- | --- | --- |
| `web/views.js` | `destinations` table keeps six keys (W-Library W-Overview W-Calendar W-Reports W-Evidence W-Forecast); `CP-OS`, `W-NewRun`, `W-Settings`, `W-Help` removed | run, settings and help screens need a server |
| `web/views.js` | Deleted `mayDiscardDraft`, `settingsView`, `HELP`, `retainedRecordHtml`, `outputCount` and the `CP-OS`, `W-NewRun`, `W-Settings`, `W-Help` branches of `workspaceView` | only served the removed screens |
| `web/views.js` | `watchFrame`: dropped the `missingText` parameter, `missing()` and the HEAD `fetch`; frame `load` event and timeout message kept | no server calls; file:// pages cannot HEAD a file |
| `web/views.js` | Library "New run" button removed; empty-state text no longer links to Settings | New run and Settings are gone |
| `web/views.js` | `updateWorkspaceChrome`: rail `place` map is Issuer library and Reports only; removed the Research workspace and Run activity rail lines (incl. `shownRunHref`) | those rail links no longer exist |
| `web/screen.js` | `isAnalytical`, `appDestinations`, `showsCodes`, the "Workspace tools" group lose `CP-OS`, `W-NewRun`, `W-Settings`, `W-Help` | removed destinations |
| `web/screen.js` | Removed `loadRunActivity` call, the `creating`/`#new-run` toggling, `presentRun()`, `newRun.show()`, `installNewRun()`, `installSettings()`; `watchFrame` calls drop the `missingText` argument | removed screens and server features |

## Calendar from any run's CP-1A (Task 4)

New file `web/calendar.js` (pure `eventTable`, `eventOrder`, `orderEvents`; tests in `web/calendar.test.cjs`) is not a copy. Edits to copied files:

| File | Edit | Why |
| --- | --- | --- |
| `web/views.js` | `calendarRun`/`calendarSections` replaced by `eventsOutput`, `hedgesOutput`, `calendarRun` (first run with the source) and `calendarSections`; the `W-Calendar` branch of `workspaceView` renders the run's own CP-1A event table, or the hedge chart only when a CP-2E output exists and carries a `hedges` visual | the `pins['CP-1A']` lookup tied the calendar to one pinned legacy run |
| `web/views.js` | `availability` says `Not run in this run` where it said `No output found` (module absent from the run) | navigator wording; all 20 `catalog.json` modules already sit in the `groups` list |
| `web/views.js` | `unavailableView` body for a module with no entry now ends `The run did not produce this module.`, where it said `That alone does not show the module was not run or not applicable.` (superseded by run report Phase A at merge 4dad3d9: the Phase A `unavailableView` is kept and this sentence is no longer on the page) | the old sentence contradicted the `Not run in this run` heading (final review L2) |
| `web/screen.js` | `eventTimeline(id, table)` rewritten: ordered by `orderEvents`, row text shown as retained, columns labelled from the table headers; the five hard-coded TDG dates and the FY / combined split removed; `renderContent` uses it for the pinned CP-1A `events` section only when that section holds an event table | the fixed `order` map only fit one run's table |
| `web/static-boot.js` | `calendar.js` added first in the script list | views.js and screen.js call its functions |

Task 5 edit: `REPO` also resolves to `credit_os`'s parent when that folder holds `src` (the Windows package ships `engine/credit_os` beside `engine/src`).

## Legacy run pins removed from catalog.json (Task 7, owner ruling: "remove them")

`catalog.json` now sha256 `9dae11282c931c50a7c662aab50e0d4e0a14c168677df1af0667f4b7a5b46d34`. Edit: deleted every `path` key (20; each pinned a legacy run file under tdg-002, tdg-003, tdg-004, tdg-guidance-001, tdg-peers-2024-001, tdg-run-comparison-001, ford-otosan-2024-001 or frontier-2020-001) and the CP-8 `compare` object (its `prior`/`current`/`repaired`/`recheck` named legacy builds and a legacy run file). The 20 module IDs and the other fields (`period`, `firstHeading`, `scope`, `basis`, `call`, `visual`) stay. `store.py` pins a module only when `catalog[module]["path"]` equals an output id, so `workspace_store` now returns `pins == {}` and the navigator, which lists modules from its own groups, is unchanged.

## Read-only Run activity (Task 8, owner ruling: lean version, low governance risk)

`CP-OS` returns as a destination with the single section `activity`, over data built at build time. The original Run activity view (`web/views.js`, `web/actions.js` at 07e14eca) is a live view over a server and is not copied: the new `activityView` is written for this library, reuses Credit OS's `missing-state`, `report-list`, `report-row` and `code` classes, and has no control, form, polling, fetch or write. Forecast needs no change: `forecastView` already shows "No forecast model was published from this run's files" when a run has no CP-2G model (now pinned by tests).

| File | Edit | Why |
| --- | --- | --- |
| `web/views.js` | `destinations` table gains `'CP-OS':['Run activity',[['activity','Run activity',[]]]]` (seven keys); new `activityView(activity)`; `workspaceView` renders it for `CP-OS`; `updateWorkspaceChrome` rail `place` map adds `CP-OS`: Run activity | owner ruling amends the earlier six-destination list |
| `web/screen.js` | `isAnalytical` excludes `CP-OS`; `appDestinations` adds `CP-OS` (needs no selected run); the screen-reader announcement omits the run name for app destinations | Run activity is not a module and belongs to no run |
| `web/static-boot.js` | Reads `window.CREDIT_OS_DATA.activity` (`{excluded: [[folder, reason], ...], issues: [...]}`, missing = a stated problem) into the global `window.DESIGN_ACTIVITY` | how the view gets its data; a global beside `DESIGN_DATA`, `DESIGN_WORKSPACE`, `DESIGN_CATALOGUE` |
| `web/index.html` | Rail link "Run activity" (`#CP-OS/activity`, `icons/activity.svg`) | navigation |

Task 8 fix: `web/static-boot.js` no longer defaults `activity` to an empty list. `window.DESIGN_ACTIVITY` is `null` unless `CREDIT_OS_DATA.activity` holds arrays `excluded` and `issues`; the catalogue/workspace check now names what is missing (`catalogue`, `workspace`) and activity is read apart, so a data file that lacks only `activity` keeps the rest working. `web/views.js` `activityView(null)` says Run activity could not be read, never the all-clear.

## Module report with source chips (module-report plan, Task 2)

The Modules tab draws one report per analytical output (head, band, key numbers, findings, limits, Evidence & audit) from the handoff and `window.CREDIT_OS_DATA.chips`. Design: `docs/design/mockups/module-report.html`, spec `docs/design/2026-11-09-module-report-spec.md`.

| File | Edit | Why |
| --- | --- | --- |
| `web/views.js` | `moduleHead` split into `headTools` and an empty head for outputs; `comparisonChart` and `readerChart` take a `chips` flag (row becomes a group holding the row button and its chips); new `moduleReport` and its parts, `chipView`, `chipsMarkup`, `keyNumbers`, `REPORT_PARTS`; `outlineMarkup` is the six "On this page" anchors; `navigationSections` and `firstSection` return those parts for an output; `routeHref` takes a `chip` index (`&chip=`); `availability` and `unavailableView` say "No output found" | the report replaces the per-section canvas; the owner ruled one wording for no output |
| `web/screen.js` | `renderContent` returns `moduleReport`, the old body is `sectionView` (opened from Evidence & audit); `showInspector(key, chip)` adds the source-page part (`chipSection`); `parseRoute` reads `chip` and maps any unknown section to the head; `renderRoute` scrolls between parts without redrawing (`scrollToPart`, `positionKey`); click handlers for chips, audit items and anchor links; `nameCodes` skips chips, the audit list and the head's code; arrow-key chart navigation ignores chips | chips, inspector and navigation for the report |
| `web/screen.css` | appended `.module-head`, `.band`, `.panel-card`, `.chart-row` chip column, `.table-card`, `.chip`, `.av`, `.dot`, `article.finding`, `.limits`, `details.audit`, inspector chip part | the mockup's styles in the existing tokens |
| `web/static.test.cjs` | report, chip, key-number, anchor, wording and font-size tests; the "Not run in this run" assertion now pins `NO_OUTPUT` | covers the above; the wording was ruled |

## Overview chart widths, hedge-chart constants, key-numbers groups (module-report plan, Task 3)

| File | Edit | Why |
| --- | --- | --- |
| `web/views.js` | `hedgeChart` reads its axis from the table's `YYYY-MM-DD` dates and the run's `asOf` (start = earliest date or as-of minus 18 months, end = latest or as-of plus 36 months, month-end clamped; labels formatted from those dates; base rule = as-of; forward = start after as-of; unit from the table's unit column, none if absent); `keyNumbers` takes the first qualifying table from all analysis groups, not only the first | hard-coded dates, labels and `USDm` belonged to one case; the real CP-2E register sits in the second group |
| `web/screen.js` | `chipSection` hides "Open source file" on the structural condition only (`hash_matches_inventory === null` and no excerpt) | a text match on the reason could hide a working link |
| `web/screen.css` | `.chart-row` columns `minmax(150px,1.1fr) minmax(140px,2fr) 72px auto`; `.summary-chart` loses `overflow:hidden` | the value no longer clips; the Overview card shows its row in full |
| `web/static.test.cjs` | key numbers in the second group, hedge chart axis/base/forward/unit tests, no-literals test, structural-hide test | covers the above |

Task 3 fix round 1: `web/screen.css` Overview `.chart-row` columns lowered to `minmax(96px,1.1fr) minmax(72px,2fr) 56px auto` (also in the 1300px override) so the value stays inside the 349px three-up card at 1440 (ruling R19); `.panel-card .chart-row` chip column is `minmax(min-content,1fr)` with `.chips{min-width:0;max-width:100%;flex-wrap:wrap}` so chips wrap, never clip (R20). `web/screen.js` `openAuditSection` catches a drawing failure, logs it and says so in the item (documented fail-open, as `moduleBody`; R21). `web/static.test.cjs` adds the audit-failure test.

Low-findings batch: `web/views.js` `comparisonChart` prints `n.a.` (full cell text in `title`) and draws no bar for a non-numeric value, where it printed the text in the 56px value column; `hedgeChart` reads dates only from columns headed date, expiry, maturity, period or tenor (every cell when no header matches). `web/static.test.cjs`: text-value chart row test; the hedge fixture gains a non-date column holding dates and its window header becomes "Maturity window".

## Front matter section (module-report plan, Task 4a, ruling R22)

| File | Edit | Why |
| --- | --- | --- |
| `store.py` | new `front_matter(lines)`; `parse_source` starts with it: a first nonblank line of exactly `---` and a later line of exactly `---` become a level-1 "Front matter" section holding the lines between, verbatim, as one text block; any other body before the first heading still raises | 13 of the 20 real handoffs open with YAML front matter and were flattened to one "Unstructured handoff" block; nothing is parsed or inferred |
| `tests/test_credit_os_store.py` | four tests: section shape, other preamble still raises, unterminated `---` raises, `structured(strict=False)` has no error | covers the above |

## Final fix round (module-report plan, rulings R23-R27)

`window.CREDIT_OS_DATA.chips` is produced by `src/deploy_workflow/credit_os_chips.py`, called from the `chips(...)` line of `update_library.py` (`apps/issuer-library/update_library.py`). Besides the existing fields each `issuer_page` chip carries `avatar` (the key, or the initials of a multi-word key such as `AF` for `Annual filing`), `match` (the page text the quote matched, a substring of `excerpt`) and `match_at` (its offset in `excerpt`); the resolver reads the run's CP-0 inventory keys and aliases, and the page prints what it is given.

| File | Edit | Why |
| --- | --- | --- |
| `web/views.js` | `chipView` prints `chip.avatar` (falls back to the source key); `numericColumn` makes a key-numbers column numeric only when every cell with a value parses (empty, dash, `n.a.` and `Not supplied...` cells are skipped); the head and the audit summary both print `data[id].sections.length` sections | R23 avatar; R26; R27 |
| `web/screen.js` | `chipSection` marks `chip.match` at `chip.match_at` (no search for the quote) and prints `Cited as <key>` for a chip with a file | R25; the inspector shows the full key |
| `web/static.test.cjs` | tests for the marked span, the avatar, the full key, the numeric rule and the one section count | covers the above |

R28 (owner, 2026-11-09): part 5 "Analysis" between Findings and Limits.

| File | Edit | Why |
| --- | --- | --- |
| `web/views.js` | `REPORT_PARTS` gains `analysis` (seven parts); `keyNumbersChoice`/`sourceTable` split out of `keyNumbers`; `analysisBlocks` lists unconsumed blocks of the analysis-group sections (consumed: Bottom line, Finding, `Chart data` tables and the key-numbers table); `reportAnalysis` draws them open with `rich()`, `cellView` and `chipsMarkup`; `reportAudit` drops sections shown in Analysis (a section whose key-numbers table is cut stays, for its extra rows) | R28 |
| `web/screen.css` | `.analysis-section`, `.analysis-text`; tables reuse `.table-card` (scrolls inside) | R28 |
| `web/index.html`, `web/screen.js` | the `<main>` landmark id `analysis` becomes `canvas` (skip link and focus calls), freeing `#analysis` for the part | the deep link `#<module>/analysis` scrolls with `getElementById` |
| `web/static.test.cjs`, `tests/test_library_page_browser.py`, `tests/browser_probe_fits.js` | seven-anchor tests, narrative/register, consumed-section, audit and no-duplicate-id tests; overflow check of the analysis part at 1440 and 1280 | R28 |

## Run report, Phase A (rulings R34, R35, R36, R37, R38, R39, R40, R41)

| File | Edit | Why |
| --- | --- | --- |
| `store.py` (Task 1) | new `EVIDENCE_HEADING`, `placements`, `section_words` and `report_fields`; `collect_runs` calls them and stores `placement` on the output record, parallel to its sections | R34 (a section under a heading outside the level-2 skeleton is `audit`), R35 (not established = the Confidence cell starts with `not assessable`), R37 (ancestor evidence rule under `Findings` only), R38 (placement lives on the output record, not on the shared sections) |
| `web/views.js` (Task 2) | `chipView` marks an `issuer_page` chip with `quote_found: true` as `verified` with `title="Quote found on page"`; `chipsMarkup` skips gap chips other than `Not supplied` (`unresolvedGap`) and ends with one `chip-count` button (`data-gaps`) reading `N citation(s) without a page` | R40: count route and wording; the spec draws no single `no page` chip |
| `web/screen.js` (Task 2) | `parseRoute` accepts `chip=gaps` only when the key has an unresolved chip; `showInspector(key,'gaps')` lists every unresolved chip with `chipSection`; the document click handler opens it from `[data-gaps]` and records the button as the Esc focus target | R40 |
| `web/screen.css` (Task 2) | `.chip.verified`, `.chip-count` | R40 |
| `web/static.test.cjs`, `tests/test_library_page_browser.py`, `tests/browser_probe_gaps.js` (Task 2) | verified, fold and singular tests; browser test for the count click, list size and Esc focus | covers the above |
| `web/views.js` (Task 3) | `REPORT_PARTS` becomes the nine parts (`head, bottom-line, numbers, findings, analysis, limits, reference, calculations, audit`); `reportParts(id)` returns the present parts as `[anchor, label, html]` and `moduleReport`, `outlineMarkup` and `navigationSections` read it; every drawn section has `id="s-<line>"`; sections are drawn by `data[id].placement` (`view` in Analysis, `reference` in a closed `Statements and registers · n tables · m rows`, `calculations` in a closed `Calculations · n words`, `limits` in Limits); `METHOD_CODE` (R36's wider form) drops a leading method code from displayed headings and keeps it in `title`; a module whose `state.established` is `false` shows head, band, findings, limits and one closed `Full handoff text · n words` (`handoff-text`) holding the other three; the declared status is a badge beside the acceptance badge; the audit list holds the entries with a section placed `audit` or `consumed`, plus the `audit` entry; key numbers are chosen among the `reference` sections and that table also stays whole in Reference. Removed: `EMPTY_PART`, `sectionGroups`, `analysisSections`, `limitsGroup`, `analysisBlocks`, `EVIDENCE_HEADING`, `isEvidenceSection`, `isBottomLine` (the store's `placements` decides, R34, R37); an empty part is omitted with no sentence. The key-numbers cut note now reads `N more rows are under Statements and registers.` | R34, R36, R38 (placement read from the output record), R40 (`s-<line>` section route, `handoff-text` anchor) |
| `web/screen.js` (Task 3) | `parseRoute` accepts a present part anchor or the `s-<line>` of a drawn section, else the head, and carries the section's label for the announcement; `scrollToPart` opens every `<details>` that is or holds the target before it scrolls; a route with `e` opens the details holding its trigger and, with no click behind it, makes that trigger the Esc focus target; the navigator outline is listed only for a module report (Run activity no longer lists report parts it does not have) | R40 |
| `web/screen.css` (Task 3) | `details.fold` (the two closed parts and the not-assessable fold) beside `details.audit`; the empty-part rules go | R40 |
| `web/static.test.cjs`, `tests/test_library_page_browser.py`, `tests/browser_probe_fits.js`, `tests/browser_probe_gaps.js`, `tests/browser_probe_sections.js` (Task 3) | nine-anchor, folded, closed-part, heading, declared-badge and Analysis tests; R39 applied to the browser tests (`cp1_findings`; `## Credit analysis` becomes `### Credit analysis`); the register fit test reads the Reference part; the count test opens the UNKEYED paragraph's count (`2 citations without a page`, list of 2); section and row routes into the closed Reference part, and no overflow at 1440 and 1280 | R39, R40 |
| `web/views.js` (Task 4) | `runReport(context)` replaces `summaryView`: count line from `state` (`N of M modules reach a conclusion · K not assessable`, `· J without a reader summary`) with the acceptance badge, a coverage strip of `a.cov` links (`filled` when established), the `CP-6` band only when `CP-6` is established, the credit story per reading group (an established module: bottom line, confidence pill, declared status, findings with chips, main limitation, its charts; a not-assessable module: one `.na-line`; an output with no Reader summary: one `<name> · No reader summary` line), the findings register (`registerRowShown`; not-assessable rows hidden until `#register-all`), open items (one row per module with a summary, linking to `#<module>/limits`), the module matrix (`words.view`; `words.reference + words.calculations`), deliverables and a Source inventory link. `reportFindings` is split into `findingBlocks` and `findingArticle`; `comparisonChart` and `readerChart` take a `note` flag so the `Missing values have no bar` note prints once per group; `moduleHref` is split from `moduleLink`; `runAcceptanceText` is shared with the module head. Removed: `CALL_ORDER`, `firstFinding`, `moduleSummary`, `leadModule`, `summaryLead`, `summaryCharts`, `summaryCard`, `summaryView` | R35 (not established), R41 (no Reader summary), R40 (limits route) |
| `web/screen.js` (Task 4) | the `change` handler applies `registerRowShown` to the register rows from the two `select[data-register-filter]` and `#register-all`, and shows the `tr.register-empty` row (`No findings match`) when no register row is shown | R35 |
| `web/screen.css` (Task 4) | the run-report rules (`.run-summary`, `.coverage`, `a.cov`, `.story-*`, `.na-line`, `.nosum-line`, `.register-tools`, `table.register`, `table.open-items`, `table.matrix`); removed with their last caller: `.summary-lead`, `.summary-owner`, `.summary-charts`, `.summary-chart`, `.summary-card`, `.summary-text`, `.summary-note`, `.question-map`; `.choose-line` shares the `.na-line` rule | the run report as a whole (R35, R41) |
| `web/static.test.cjs`, `tests/browser_probe_overview.js`, `tests/test_library_page_browser.py`, `tests/library_fixtures.py` (Task 4) | four-module run-report harness (CP-1, CP-2A, CP-6, CP-X); the Overview probe now checks chart values inside their cards, no overflow and the register checkbox (`RunSpec.cp0_confidence` makes CP-0 not assessable in the browser run) | covers the above |
| `web/views.js`, `web/screen.js`, `web/static.test.cjs` (Task 4 fix 1) | `runGroups` keeps a module that has saved outputs but no default (`id` and `out` null, `choices` = its output count): it is counted in the total, listed in its group as a `.choose-line` (`<code> <name> · N saved outputs. Choose one`, linking `#<module>`), unfilled in the coverage strip, a matrix row reading `N saved outputs`, with no register rows and no output chosen by the page; the count line appends ` · K without a chosen output` only when K > 0. The register carries a `tr.register-empty` row, visible when no row is shown. `runPage` takes an optional `shape` argument for the module entries | review finding M1, L1 |
| `web/views.js`, `web/static.test.cjs` (Task 5 fix) | `storyLine`: the choose line writes the module name once (no bare code for the code-to-name pass to turn into a second name) and its link carries the current run (`#<module>?c=<run>`); the node test expects the name-only text and the `?c=run-a` href | R41 (choose line), reviewer Low findings |
| `store.py` (final fix) | `COMMITTEE_STATUS` is `^committee_status:[ \t]*(\S.*)$`, so an empty `committee_status:` is no declared status instead of the next front-matter line; the `EVIDENCE_HEADING` comment no longer points at the deleted JS constant | whole-branch review M1, I2 |
| `web/views.js` (final fix) | finding rows come from Python's `summary.findings` (`findingRows`; `findingArticle(id,row)`) in the module page, the credit story and the register; `findingBlocks` and the header sniffing for `Confidence` are removed (`isFindingsTable` stays for Key numbers); the register no longer tests `established!==null` (a null summary has no rows) | whole-branch review L1 |
| `web/static.test.cjs`, `tests/test_credit_os_store.py`, `tests/test_library_page_browser.py`, `tests/library_fixtures.py`, `tests/browser_probe_overview.js`, `tests/browser_probe_sections.js` (final fix) | `summary.findings` in the harness; empty-status cases; R31a key back to eight headings; row route from the head opens its fold; `chip=gaps` on a row without a gap; filtered register shows the empty row; chart note once per group with two modules; an `Other modules` module in the register and open items; `RunSpec.cp1_finding` | whole-branch review M1, L1-L6 |

## Task 9 fix: a model shows under the run folder it was delivered in (R25)

A launcher run's folder is usually not its run ID (`--out runs/my-first-run`), so a published forecast was listed under no run.

| File | Edit | Why |
| --- | --- | --- |
| `store.py` | New `run_folder_of(folder)` (the `x` of `runs/<x>/deliveries/<id>`); `read_model` adds `runFolder`; `run_shows` also accepts a run whose folder equals it | match a model to the run folder that holds its delivery, not only to the run ID in its `view.json` |
| `web/views.js` | `runModels` adds `m.runFolder===run.folder`; `modelOwnRun` accepts `contexts[key].folder===model.runFolder` | same rule in the page, with the same issuer-key check |

## Follow-up fix: YAML front matter is kept, not rejected

Handoffs that open with YAML front matter (`---` ... `---`) raised "Body before first heading" and were shown unstructured.

| File | Edit | Why |
| --- | --- | --- |
| `store.py` | `parse_source` keeps a leading `---` ... `---` block as its own first section headed `Front matter` (level 2, one text block of the lines between the markers, locators from the source). No closing marker, or a body line between the closing marker and the first heading: unchanged, still raises "Body before first heading" (owner ruling R28) | keep every nonblank body line, as the docstring promises; found by the first real CP-2G run |

Merge of origin/main (controller ruling): the Front matter section follows main's dc2320c contract, level 2 with block locators covering only the lines between the `---` markers (the branch's level 1 `front_matter()` helper is removed; `parse_source` holds the one implementation). `tests/test_credit_os_store.py` `test_front_matter_is_the_first_section_verbatim`: level 1 -> 2, block `line` 1 -> 2, `end` 4 -> 3.

Merge fix (M1): `web/screen.css` moves main's live-run `.chip-done`, `.chip-running`, `.chip-waiting` rules after the run report's `.chip` rule (same specificity, so order decides) and leaves `.chips`, `.run-stalled`, `.run-files`, `.run-held`, `.run-reason`, `.run-note` in place, so the live-run chips keep the state colours they had on main; `tests/test_library_page_browser.py` adds `test_live_run_chips_show_their_state_colours`.

## Library layout to the 2026-11-11 reader ruling (decisions 1, 4, 12 and H7)

The delivered report is retired from the library, so the copied report pages and everything that served them are gone. The earlier rows above about `W-Calendar`, `W-Reports`, the Reports rail entry and `watchFrame` describe the copy as first made; these rows are what holds now.

| File | Edit | Why |
| --- | --- | --- |
| `web/report-adapter.css`, `web/report-adapter.js` | Deleted (rows removed from the table above) | the presented copy of the delivered report no longer exists |
| `web/reader.js` | New, pure (no DOM): reader passages, Basis lines, figures, earlier-format rules, history order, `pathwayTitle`, `runModuleCodes`; tests in `web/reader.test.cjs`; loaded by `static-boot.js` before `views.js` | the 2026-11-11 handoff contract in one tested place |
| `web/index.html`, `web/views.js` | Rail is Start a run, Issuer library, Run activity, Search; issuer tabs are Report, Overview, Modules, Forecast, Evidence; `destinations` keys are W-Library W-Report W-Overview W-Evidence W-Forecast CP-OS | decision 12 |
| `web/views.js` | `historyView` (Report history) and `runLabel` (the run line under the tabs, "Earlier format" badge) replace `contextBar`; `reportList`, `reportView`, `reportManifest`, `runReports`, `calendarSections`, `calendarRun`, `issuerReports`, `reportsBuiltFrom`, `reportsUsing`, `tracedRun`, `reportName`, `isReportRoute` deleted; the Library page's "Open report"/"All reports" become "Open run" and "History"; a catalogued report is named, never linked | decisions 1, 4, 12 |
| `web/views.js`, `web/screen.js` | `watchFrame` and its timer stay for the Forecast page's published-model frame only (`cancelModelFrame`); the report frame and its status plumbing are deleted | the model is part of the issuer report; the delivered report is not |
| `web/screen.js` | `parseRoute` sends an old `#W-Reports/...` or `#W-Calendar/...` hash to the run's Report history (the library when no run exists) | an old link opens a page, not a blank |
| `web/screen.css` | `.report-workspace`, `.report-content`, `#report-preview` and the context pop-over rules deleted; `.history-table` added | the rules served only the retired pages |
| `store.py` | `report_record`, `catalogue_reports`, `built_from`, `delivery_and_view` and `CURATED_REPORTS` labels removed; no `reports` list in the store; `curated_builds` keeps the compared-deliverable check; `collect_runs` no longer returns a handoff-source index; a delivery that cannot be read is named in the issues | a CP-OS delivery has no `report.html` and the library lists a run without one (completion record `delivery_sha256`); nothing here reads or requires one. An earlier run's `report_sha256` and `report.html` are only listed as stored files in its Evidence run record |
| `update_library.py` | No `library/reports/**`, no `present_report`; `/files/...` hrefs become `../...` paths whatever their query | decision 1 |
| `web/views.js` | `runReport(context)` is the Overview of ruling H5: lead (CP-6, else CP-2, not blocked, with a Bottom line), bottom line per module in the run record's order, de-duplicated Limitations, key charts and maps of modules whose visuals-catalogue `placement` names Overview (`onOverview`), nearest five dates from the event lanes (`nearestDates`). `passageParagraph`/`passageHtml` draw every handoff paragraph. Removed: `coverageStrip`, `storyModule`, `storyLine`, `storyCharts`, `creditStory`, `findingsRegister`, `openItems`, `moduleMatrix`, `registerRowShown`; the Task 4 run-report entries above are superseded | decisions 6, 12; H5, H7 |
| `web/screen.js`, `web/screen.css` | no Overview outline (`runOutline`, `runPart`), no register filter handler; `.overview-workspace` hides the navigator and Browse modules button on the Overview; the Task 4 run-report rules are removed and `.overview-part`, `.passage-*`, `.basis`, `.dates-table` added | decision 6 |
| `web/static.test.cjs`, `tests/test_library_page_browser.py`, `tests/browser_probe_overview.js`, `tests/browser_probe_index.js`, `tests/browser_probe_bridge.js`, `tests/browser_probe_structure.js` | the "run report" tests are rewritten to the Overview (expectations hand-written from the synthetic fixture); `browser_probe_calendar.js` is deleted (lanes are no longer drawn on the Overview); chart, map and status-map browser checks moved to the module, Evidence and Forecast pages | H5 |

## Evidence and Run activity (library layout T6, ruling 2026-11-11 decisions 9 and 10)

| File | Change | Why |
| --- | --- | --- |
| `store.py` | Each run gains `evidence` (`run_evidence`): supplied files with `readBy` and "Supplied, not used", handoff downloads, calculation and Model downloads, the run record (hashes, instructions, calls, cap), every value as stored | the Evidence page's four lists |
| `update_library.py` | Writes `library/downloads/<run folder>/handoffs.zip` (delivered Markdown byte for byte) | "Download all" works from disk |
| `web/views.js` | `evidenceView` replaces the retained-outputs inventory, status map and lanes; `activityView(live)` draws running and queued runs only; `libraryNotShown` holds the excluded folders and build issues, closed, at the end of the library page | decisions 9 and 10 |

## Brand colours (brand application plan, Task 1, Rulings 1-3, 5, 6)

| File | Change | Why |
| --- | --- | --- |
| `web/screen.css` | The three `:root` blocks take the brand token values; eight tokens `--series-1..4` and `--series-1..4-ln` are added; `a` uses `--blue-700`; literal greys become tokens; `.series-0..3`, `.path-N`, `.point-N`, `.path-key-N`, `.ledger-other`, `.outflow` and the stack rules use the series tokens (bright fills carry a 1px inset outline in their line value; legend swatches, lines and points use the line values); the select chevron is `#63676e`. Colours only: no font, size or spacing change | brand-spec.md; one commit with `docs/templates/context-form.html` because `tests/test_context_form.py` requires equal token values |
| `web/screen.css` (fix round 1) | Hatched stack segments on the bright fills (`series-1..3`) draw their stripe in the series line value; `.path-2`, `.point-2`, `.path-key-2` use `--series-4-ln`; `.axis` uses `--navy`, `.gridline` uses `--gray-200`. Colours only | the white stripe vanished on bright fills; the upside path was too close to the amber downside path |
| `web/static.test.cjs` | Brand tests: token values, no bright fill in `color`/`stroke`, retired values absent; hatch stripe, legend swatch and ledger state pins; upside path, axis and grid | covers the brand colours above |

## Component look (brand application plan, Task 4)

| File | Change | Why |
| --- | --- | --- |
| `web/screen.css` | Box properties only, no font change: `.badge`, `.grade`, `.forecast-built .code` and the live-run `.chip-*` take radius 6px (badge and grade padding `0 6px` / `1px 6px`); the current workspace tab is `--text-primary` under its 2px `--blue` underline, other tabs `--text-quaternary`, hover `--text-secondary`; `.tertiary-action` pads 12px; table header text is `--text-quaternary`; `.metric-label` and `.missing-state p` are `--text-quaternary`; `.empty-symbol` is 48px with radius 10px; `.caution` has radius 8px and an inset ring in `--amber-border`; `.run-strip` radius 8px; compact toolbar selects take radius 8px; module-step markers are white with a 1.5px ring, a completed step is `--gray-200` with a dark tick | the component reference (Untitled UI, Ant Design) as the look of the existing components |
| `web/static.test.cjs` | A static test of the button, input, badge and tab values | covers the above |

## Run activity redesign (brand application plan, Task 5; owner, 2026-11-12: "Yes, build it", "remove the run spend")

| File | Change | Why |
| --- | --- | --- |
| `web/views.js` | `liveRunRow` becomes `liveRunCard` (name, one line, pathway tag, status badge, `<progress>`, module badges, foot); `liveWaitingRow` and a waiting `table`; counts `dl`; `liveRunSpend` removed; the empty state gains an "Issuer library" link | the approved Run activity design; the page no longer shows spend |
| `web/screen.css` | A Run activity block at the end (cards, badges, tag, progress, table, notice, counts, centred empty state, narrow and print rules); `--green-bg` added to `:root` | the same design; Red Hat faces as before |
| `web/static.test.cjs`, `tests/test_library_page_browser.py`, `tests/browser_probe_run_activity.js` | Old row-markup and spend tests rewritten; tests added for progress, badges, the table, counts, escaping, layout at 1440 and 375, and an open file list across a reload | covers the above |
