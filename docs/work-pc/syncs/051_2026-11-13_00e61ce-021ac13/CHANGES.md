# Changes for the work PC

From `00e61cec01e4` (the version the work PC last adapted) to `021ac135c05f` (2026-11-13T19:55:52Z). 30 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `6edbfea` 2026-11-13 docs(work-pc): change pack for 00e61ce
- `021ac13` 2026-11-13 feat(signal): slice 2b — feed page, browser proof, packaging and the run start rail link (Merge pull request #109 from EricMG13/claude/signal-2-service-pages)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `README.md` | +24 −1 | L263-264, L273-274, L277-296 |
| modified | `VERIFICATION.md` | +13 −40 | L7-19, removed after L958 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +1 −1 | L34 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/packaging/runtime.py` | +25 −1 | L117-138, L170-172 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/design/mockups/signal-slice2-foryou-empty-1280.png` | binary | — |
| added | `docs/design/mockups/signal-slice2-latest-1280.png` | binary | — |
| added | `docs/design/mockups/signal-slice2-latest-375.png` | binary | — |
| modified | `docs/templates/context-form.html` | +1 −1 | L438 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/run_start/service.py` | +69 −14 | L93, L157-158, L194, L363-365, L570-611, L613, L628, L638, L640, L642, L644-657, L666 |
| modified | `src/deploy_workflow/signal/cli.py` | +3 −2 | L14, L134, L174 |
| modified | `src/deploy_workflow/signal/feedview.py` | +35 −5 | L6-7, L41, L89-110, L173-177, L214, L217-219, L223 |
| modified | `src/deploy_workflow/signal/service.py` | +34 −8 | L83-97, L223-226, L230-232, L234, L398-400, L405, L409-410, L606, L610, L613-615 |
| modified | `src/deploy_workflow/signal/store.py` | +5 −0 | L115-119 |
| modified | `src/deploy_workflow/signal/topics.py` | +16 −4 | L76-90, L113 |
| modified | `src/deploy_workflow/signal/web/index.html` | +95 −1 | L7, L12-105 |
| modified | `src/deploy_workflow/signal/web/render.js` | +202 −1 | L1-202 |
| added | `src/deploy_workflow/signal/web/render.test.cjs` | +126 −0 | L1-126 |
| modified | `src/deploy_workflow/signal/web/signal.css` | +188 −1 | L1-188 |
| modified | `src/deploy_workflow/signal/web/signal.js` | +458 −1 | L1-458 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/browser_cdp_common.cjs` | +46 −0 | L1-46 |
| modified | `tests/browser_cdp_measure.cjs` | +3 −31 | removed after L5, L7, L11, L15 |
| added | `tests/browser_signal_driver.cjs` | +113 −0 | L1-113 |
| modified | `tests/test_issuer_library_packaging.py` | +57 −0 | L49-51, L214-244, L298-320 |
| modified | `tests/test_run_start_service.py` | +108 −0 | L928-1035 |
| modified | `tests/test_signal_cli.py` | +19 −2 | L11-12, L171-187 |
| modified | `tests/test_signal_feedview.py` | +32 −19 | L145-176, removed after L191, removed after L196 |
| added | `tests/test_signal_page_browser.py` | +794 −0 | L1-794 |
| modified | `tests/test_signal_service.py` | +58 −8 | L191-217, L250, L287-290, L292-293, L295-302, L455-464, L484-485, L509-512 |
| modified | `tests/test_signal_store.py` | +15 −0 | L190-204 |
| modified | `tests/test_signal_topics.py` | +54 −0 | L1, L147-199 |
