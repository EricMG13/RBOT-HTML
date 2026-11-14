# Changes for the work PC

From `c627679960e7` (the version the work PC last adapted) to `c07543a21854` (2026-11-14T00:40:41Z). 20 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `cbf4400` 2026-11-14 docs(work-pc): change pack for c627679
- `c07543a` 2026-11-14 Synthetic loan market-data pack wired to run-start quotes (Merge pull request #121 from EricMG13/claude/synthetic-market-data-screenshots-bb52f7)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +25 −49 | L7-31, removed after L955 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tests/fixtures/market-data/README.md` | +13 −0 | L1-13 |
| added | `tests/fixtures/market-data/chemicals.csv` | +25 −0 | L1-25 |
| added | `tests/fixtures/market-data/entertainment-ratings-average.csv` | +10 −0 | L1-10 |
| added | `tests/fixtures/market-data/entertainment.csv` | +17 −0 | L1-17 |
| added | `tests/fixtures/market-data/healthcare.csv` | +46 −0 | L1-46 |
| added | `tests/fixtures/market-data/index-statistics.csv` | +5 −0 | L1-5 |
| added | `tests/fixtures/market-data/issuer-context-quotes.json` | +24 −0 | L1-24 |
| added | `tests/fixtures/market-data/issuer-quotes.txt` | +5 −0 | L1-5 |
| added | `tests/fixtures/market-data/it-services-ratings-average.csv` | +10 −0 | L1-10 |
| added | `tests/fixtures/market-data/it-services.csv` | +36 −0 | L1-36 |
| added | `tests/fixtures/market-data/power.csv` | +28 −0 | L1-28 |
| added | `tests/fixtures/market-data/schema.json` | +73 −0 | L1-73 |
| added | `tests/fixtures/market-data/software-ratings-average.csv` | +10 −0 | L1-10 |
| added | `tests/fixtures/market-data/software.csv` | +81 −0 | L1-81 |
| added | `tests/fixtures/market-data/telecoms-ratings-average.csv` | +10 −0 | L1-10 |
| added | `tests/fixtures/market-data/telecoms.csv` | +41 −0 | L1-41 |
| modified | `tests/test_cpos_launch.py` | +22 −0 | L3525-3546 |
| added | `tests/test_synthetic_market_data.py` | +228 −0 | L1-228 |

### tools

| Status | File | +/- | Where |
|---|---|---|---|
| added | `tools/synthetic_market_data.py` | +567 −0 | L1-567 |
