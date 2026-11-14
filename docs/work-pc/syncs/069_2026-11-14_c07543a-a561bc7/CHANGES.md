# Changes for the work PC

From `c07543a21854` (the version the work PC last adapted) to `a561bc76be19` (2026-11-14T01:39:33Z). 11 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `0f16bad` 2026-11-14 docs(work-pc): change pack for c07543a
- `a561bc7` 2026-11-14 Synthetic pack follow-ups: stronger tests, document-key test, shared word replaced (Merge pull request #124 from EricMG13/claude/synthetic-pack-followups)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +28 −2 | L7-32, L51-52 |

### .github

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `.github/workflows/checks.yml` | +1 −0 | L39 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/market-data/healthcare.csv` | +2 −2 | L10, L28 |
| modified | `tests/fixtures/market-data/it-services.csv` | +1 −1 | removed after L19, L29 |
| modified | `tests/fixtures/market-data/power.csv` | +1 −1 | L23 |
| modified | `tests/fixtures/market-data/schema.json` | +7 −0 | L45-51 |
| modified | `tests/fixtures/market-data/software.csv` | +2 −2 | removed after L24, L71-72 |
| modified | `tests/fixtures/market-data/telecoms.csv` | +2 −2 | removed after L18, L33-34 |
| added | `tests/test_document_key.py` | +186 −0 | L1-186 |
| modified | `tests/test_synthetic_market_data.py` | +52 −0 | L8, L117-167 |

### tools

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tools/synthetic_market_data.py` | +1 −1 | L148 |
