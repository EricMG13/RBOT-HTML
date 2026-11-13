# Changes for the work PC

From `598a48fb2ac8` (the version the work PC last adapted) to `00e61cec01e4` (2026-11-13T19:55:31Z). 24 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `460fa53` 2026-11-13 docs(work-pc): change pack for 598a48f
- `caf205c` 2026-11-13 feat(signal): store, folding, ingest and command line (slice 1, part 2 of 2) (Merge pull request #102 from EricMG13/claude/signal-1b-store-ingest-cli)
- `00e61ce` 2026-11-13 feat(signal): slice 2a — topics, feed queries, identity and the HTTP service (Merge pull request #106 from EricMG13/claude/signal-2a-service-api)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `README.md` | +21 −0 | L259-279 |
| modified | `VERIFICATION.md` | +29 −33 | L7-35, removed after L985 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `docs/superpowers/plans/2026-11-13-signal-2-service-and-feed-pages.md` | +473 −0 | L1-473 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| added | `src/deploy_workflow/signal/__main__.py` | +7 −0 | L1-7 |
| added | `src/deploy_workflow/signal/cli.py` | +176 −0 | L1-176 |
| added | `src/deploy_workflow/signal/feedview.py` | +215 −0 | L1-215 |
| added | `src/deploy_workflow/signal/fold.py` | +36 −0 | L1-36 |
| added | `src/deploy_workflow/signal/identity.py` | +79 −0 | L1-79 |
| added | `src/deploy_workflow/signal/ingest.py` | +121 −0 | L1-121 |
| added | `src/deploy_workflow/signal/service.py` | +608 −0 | L1-608 |
| added | `src/deploy_workflow/signal/store.py` | +390 −0 | L1-390 |
| added | `src/deploy_workflow/signal/topics.py` | +140 −0 | L1-140 |
| added | `src/deploy_workflow/signal/web/index.html` | +15 −0 | L1-15 |
| added | `src/deploy_workflow/signal/web/render.js` | +1 −0 | L1 |
| added | `src/deploy_workflow/signal/web/signal.css` | +1 −0 | L1 |
| added | `src/deploy_workflow/signal/web/signal.js` | +1 −0 | L1 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/test_signal_cli.py` | +216 −0 | L1-216 |
| added | `tests/test_signal_feedview.py` | +183 −0 | L1-183 |
| added | `tests/test_signal_fold.py` | +128 −0 | L1-128 |
| added | `tests/test_signal_identity.py` | +114 −0 | L1-114 |
| added | `tests/test_signal_ingest.py` | +139 −0 | L1-139 |
| added | `tests/test_signal_service.py` | +522 −0 | L1-522 |
| added | `tests/test_signal_store.py` | +243 −0 | L1-243 |
| added | `tests/test_signal_topics.py` | +145 −0 | L1-145 |
