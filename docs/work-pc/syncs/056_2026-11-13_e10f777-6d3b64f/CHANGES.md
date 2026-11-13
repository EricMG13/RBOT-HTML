# Changes for the work PC

From `e10f7778c9c4` (the version the work PC last adapted) to `6d3b64f15242` (2026-11-13T22:32:34Z). 9 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `8e458ad` 2026-11-13 docs(work-pc): change pack for e10f777
- `6d3b64f` 2026-11-13 Library: name the ESG analysis on the Rates, FX & hedging page and in the run-start catalogue (Merge pull request #100 from EricMG13/claude/wonderful-booth-d512b9)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +10 −0 | L7-16 |

### apps

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `apps/issuer-library/credit_os/web/shapes.js` | +4 −1 | L17-19, L174 |
| modified | `apps/issuer-library/credit_os/web/shapes.test.cjs` | +5 −0 | L244-248 |
| modified | `apps/issuer-library/credit_os/web/static.test.cjs` | +89 −0 | L5229-5317 |
| modified | `apps/issuer-library/credit_os/web/views.js` | +22 −5 | L497-498, L683, L686-687, L788-793, L800, L821-823, L827-831, L834-835 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/templates/context-form.html` | +1 −1 | L772 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/fixtures/esg/CP-2E-h3.md` | +385 −0 | L1-385 |
| added | `tests/fixtures/esg/CP-2E-h4.md` | +414 −0 | L1-414 |
| modified | `tests/test_context_form.py` | +9 −0 | L387-395 |
