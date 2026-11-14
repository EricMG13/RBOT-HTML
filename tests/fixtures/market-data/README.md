# Synthetic loan market data (SYNTHETIC)
All names, ids and numbers are invented; only the shape of Bloomberg-style loan sheets stays.
Regenerate: `uv run python tools/synthetic_market_data.py` (seed and as-of from schema.json).
`schema.json` is the answer key for tests/test_synthetic_market_data.py. Files: `<sector>.csv`,
`<sector>-ratings-average.csv` (issuer-layout sectors) and `index-statistics.csv`.
Dirty cells are literal: `#N/A N/A` (price changes, Moody's rating), `#N/A Field Not Applicable`.
A Delta of `0` is a real zero; a dirty token is missing data, never zero.
Healthcare: one row holds `#NAME?` in every column except Bloomberg ID and Group.
Power: one unpriced row has `#N/A N/A` in Bid, Ask, Delta 1M, Delta YTD, Mid YTM, Mid 3Y DM.
Peers Bloomberg ID mixes `SYN`+7 digits and FIGI-style `SYN01`+7 chars. No colours.
`issuer-quotes.txt` is read by the run-start classifier as `market_quotes` (clears CP-3 and CP-3D
no-quotes gaps); `issuer-context-quotes.json` holds the same tranches as run-context `quotes` rows.
Both are one telecoms issuer (first with two clean tranches); sector peer sheets stay unrecognised.
