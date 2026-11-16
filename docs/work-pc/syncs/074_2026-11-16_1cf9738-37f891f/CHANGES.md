# Changes for the work PC

From `1cf9738a7097` (the version the work PC last adapted) to `37f891f008f2` (2026-11-16T03:53:21Z). 3 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `d84a457` 2026-11-15 docs(work-pc): change pack for 1cf9738
- `37f891f` 2026-11-16 fix(pdf): keep text that pypdf layout mode skips in Form XObjects (Merge pull request #130 from EricMG13/claude/markitdown-readability-7a9d5c)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_vii/preparation.py` | +22 −2 | L38-40, L206-222, L254, L268 |
| modified | `src/deploy_workflow/model/handoff.py` | +2 −4 | L42, L466 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/test_pdf_form_text.py` | +149 −0 | L1-149 |
