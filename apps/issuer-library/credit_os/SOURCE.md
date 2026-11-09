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
| `web/report-adapter.css` | `web/report-adapter.css` | `8819ac13bef113ea3a3f8ebdef58b92493c87b80e88ea3e96e1770b527787601` | yes |
| `web/report-adapter.js` | `web/report-adapter.js` | `d581bcc5aaf9eda65f885651a08d40d64b6a09c0482f9c098b89615a02f5577a` | yes |
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
| `web/screen.js` | `eventTimeline(id, table)` rewritten: ordered by `orderEvents`, row text shown as retained, columns labelled from the table headers; the five hard-coded TDG dates and the FY / combined split removed; `renderContent` uses it for the pinned CP-1A `events` section only when that section holds an event table | the fixed `order` map only fit one run's table |
| `web/static-boot.js` | `calendar.js` added first in the script list | views.js and screen.js call its functions |

Task 5 edit: `REPO` also resolves to `credit_os`'s parent when that folder holds `src` (the Windows package ships `engine/credit_os` beside `engine/src`).

## Legacy run pins removed from catalog.json (Task 7, owner ruling: "remove them")

`catalog.json` now sha256 `9dae11282c931c50a7c662aab50e0d4e0a14c168677df1af0667f4b7a5b46d34`. Edit: deleted every `path` key (20; each pinned a legacy run file under tdg-002, tdg-003, tdg-004, tdg-guidance-001, tdg-peers-2024-001, tdg-run-comparison-001, ford-otosan-2024-001 or frontier-2020-001) and the CP-8 `compare` object (its `prior`/`current`/`repaired`/`recheck` named legacy builds and a legacy run file). The 20 module IDs and the other fields (`period`, `firstHeading`, `scope`, `basis`, `call`, `visual`) stay. `store.py` pins a module only when `catalog[module]["path"]` equals an output id, so `workspace_store` now returns `pins == {}` and the navigator, which lists modules from its own groups, is unchanged.
