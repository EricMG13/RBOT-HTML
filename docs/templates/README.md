## Portfolio workbook (`portfolio.template.xlsx`)

Task PF-1, 25 October 2026. The Portfolio Decision page needs the fund's mandate, exposures
and compliance limits. In your own environment you supply them as one XLSX workbook; the
Portfolio Fit and Portfolio Debate owners read it from the pack. This template shows the
layout. Its rows are a **synthetic example for a fictional fund (Test CLO I Ltd (synthetic))
and fictional issuers, not fund or market data**: replace every row. The `README` sheet in the
workbook says the same. Its NAV-level figures (NAV US$ 630,928,502 at 2026-05-29; limits C-01,
C-04, C-05, C-10 and SECTOR) are the design mock's, so the Portfolio Fit module can be tested
against the design's `fit` object.

`scripts/build_templates.py` generates the workbook, so the same rows always produce the same
bytes. `tests/product/test_inputs_portfolio.py` fails if the committed file and the script's
output differ. Edit the script, never the binary.

### Sheets

The workbook has these sheets, in this order, plus an optional `README` sheet anywhere. Any
other sheet is refused. `Holdings_Detail` is optional; every other sheet is required. Row 1 of
each sheet must be exactly its headers, from A1, in the order below, with nothing after the
last one. Each row from row 2 down is one item. Blank rows are skipped. Cells to the right of
the last header are not read.

| Sheet | One row per | Headers (row 1) | No two rows share |
| --- | --- | --- | --- |
| `Mandate` | mandate field | `section`, `field`, `value`, `notes` (A1 to D1) | `section` and `field` |
| `Exposure_Summary` | metric | `metric`, `value`, `unit`, `as_of` (A1 to D1) | `metric` |
| `Rating_Distribution` | rating bucket | `rating_bucket`, `pct_nav`, `issuers` (A1 to C1) | `rating_bucket` |
| `Sector_Exposure` | sector | `sector`, `pct_nav`, `issuers`, `limit_pct_nav`, `headroom_pct_nav`, `status` (A1 to F1) | `sector` |
| `Top_Holdings` | holding | `rank`, `issuer`, `instrument`, `pct_nav`, `rating` (A1 to E1) | `rank` |
| `Maturity_Profile` | maturity bucket | `bucket`, `pct_nav` (A1 to B1) | `bucket` |
| `Compliance_Monitor` | constraint | `id`, `constraint_category`, `parameter`, `limit`, `limit_unit`, `breach_type`, `scope`, `source_document`, `current_value`, `headroom`, `status`, `last_checked`, `checked_by` (A1 to M1) | `id` |
| `Holdings_Detail` (optional) | position | `issuer`, `instrument`, `facility_id`, `par`, `market_value`, `pct_nav`, `rating`, `sector`, `seniority`, `maturity` (A1 to J1) | `facility_id` |

Every column is required unless the tables below say optional. Rules that apply to every sheet:

- **Numbers** are plain numbers: digits, an optional sign and one decimal point, with an
  optional exponent of at most two digits (`1e3`), and at most 40 characters. No `%`, units,
  spaces or thousands separators. The validator reads each number as a decimal from the cell's
  stored text, never as a binary float, and compares exactly.
- **Percent of NAV** cells (`pct_nav`, `limit_pct_nav`, `headroom_pct_nav`, `limit`,
  `current_value` and `headroom` when `limit_unit` is `% NAV`, and `Exposure_Summary` `value`
  when `unit` is `% NAV`) are plain numbers in percent: `2.5` means 2.5 % NAV. A number cell
  formatted as a percentage (for example `0.00%`) is refused: Excel stores 2.5 % as 0.025, which
  would read 100 times too small. A format that only shows a literal sign (`0.00"%"`) is
  accepted. A `pct_nav` below 0 is refused: a share of NAV is at least 0.
- **Dates** are text `YYYY-MM-DD` and real calendar dates. The template formats these columns
  as Text. A date Excel has turned into a serial number (such as `46171`) is rejected.
- **Values, not formulas**: `prepare` freezes the stored values and never recalculates.
  Excel error cells (`#N/A`, `#DIV/0!` and the like) and TRUE/FALSE cells are refused in
  every column.
- **No total rows** in `Rating_Distribution`, `Sector_Exposure` or `Maturity_Profile` (a label
  containing the word `total` or `subtotal`, such as `Total` or `Top 20 Subtotal`). Python adds
  the rows up. A genuine label that contains the word, such as a sector `Total Return Swaps`,
  is refused too: rename it without the word (for example `TR Swaps`).
- Hidden rows, columns and sheets are refused, not read: one issue for a sheet whose filled
  cells are all hidden, else one per row holding a hidden filled cell. Unhide them or delete
  them.
- Cell addresses must be canonical uppercase A1 coordinates within A1:XFD1048576, with no
  spaces, line breaks or leading row zeroes. Sheet locators must retain their canonical
  URI spelling so typed values quote the exact frozen cell. Invalid addresses or locators
  are refused: save the file as an Excel Workbook (.xlsx) and validate again.
- The typed reader requires a ready source and retained coverage for each contracted data
  sheet. Unavailable sources, blocked extraction, and unreadable or empty data sheets are
  refused. Normal degraded XLSX extraction and an unreadable optional README remain valid.

#### `Mandate`

| Column | Header | Rule |
| --- | --- | --- |
| A | `section` | One of `Strategy`, `Key Parties`, `Capital Structure`, `Mandate Constraints`, `Liquidity Terms`, `Fees`, `Reporting` (exact text). |
| B | `field` | The field's name. |
| C | `value` | The field's value, as text. |
| D | `notes` | Optional free text. |

These five rows are required (section and field exact text); other rows are free:

| `section` | `field` | `value` |
| --- | --- | --- |
| `Strategy` | `fund_name` | The fund's name. |
| `Strategy` | `strategy` | One of `CLO`, `Indexed Loans`, `Indexed HY`, `Other`. |
| `Capital Structure` | `nav` | The fund's NAV, a plain number above 0. |
| `Capital Structure` | `nav_currency` | The NAV's currency, a three-letter upper-case ISO 4217 code such as `USD`. |
| `Reporting` | `as_of` | The NAV and compliance date, `YYYY-MM-DD`. |

#### `Exposure_Summary`

| Column | Header | Rule |
| --- | --- | --- |
| A | `metric` | The metric's name. A row `nav` is required. Do not supply `one_pct_nav`: Python computes 1 % of NAV from `nav`. |
| B | `value` | A plain number. The `nav` row's value must be the same number as the Mandate `nav` (`630928502` and `630928502.00` are the same number). |
| C | `unit` | The unit, such as `USD`, `% NAV`, `years` or `count`. The `nav` row's unit must be the Mandate `nav_currency`. |
| D | `as_of` | The metric's date, `YYYY-MM-DD`. |

#### `Rating_Distribution`

| Column | Header | Rule |
| --- | --- | --- |
| A | `rating_bucket` | The rating bucket, such as `B` or `Unrated`. |
| B | `pct_nav` | Percent of NAV. The column must sum to between 99.0 and 101.0 inclusive; if part of NAV has no bucket, add a row `Unallocated` with the remainder. |
| C | `issuers` | A whole number of at least 0. |

#### `Sector_Exposure`

| Column | Header | Rule |
| --- | --- | --- |
| A | `sector` | The sector's name. |
| B | `pct_nav` | Percent of NAV. |
| C | `issuers` | A whole number of at least 0. |
| D | `limit_pct_nav` | Optional. The sector limit, percent of NAV. |
| E | `headroom_pct_nav` | Optional, and only with `limit_pct_nav`. Must equal `limit_pct_nav` minus `pct_nav` to within 0.01. |
| F | `status` | Optional, and only with `limit_pct_nav`. `Pass`, `Watch` or `Breach`, under the status rule below with `pct_nav` as the current value. |

#### `Top_Holdings`

| Column | Header | Rule |
| --- | --- | --- |
| A | `rank` | A whole number of at least 1. The ranks must be exactly 1 to the number of rows, with no gaps or repeats. |
| B | `issuer` | The issuer's name. |
| C | `instrument` | A plain description of the instrument. |
| D | `pct_nav` | Percent of NAV. |
| E | `rating` | The rating as reported, such as `B2 / B`. |

#### `Maturity_Profile`

| Column | Header | Rule |
| --- | --- | --- |
| A | `bucket` | The maturity bucket, such as `3-5 Years`. |
| B | `pct_nav` | Percent of NAV. |

#### `Compliance_Monitor`

| Column | Header | Rule |
| --- | --- | --- |
| A | `id` | `C-01` style (capital letters, a hyphen, two digits) or `SECTOR` for the row that holds the sector limit. |
| B | `constraint_category` | The constraint category, such as `Single Name`. |
| C | `parameter` | A description of the constraint. |
| D | `limit` | A plain number in `limit_unit`. Every limit is a maximum. |
| E | `limit_unit` | `% NAV`, or the Mandate `nav_currency` (such as `USD`) for an amount limit. |
| F | `breach_type` | `Hard` or `Soft`. |
| G | `scope` | One of `issuer`, `rating_bucket`, `sector`, `seniority`, `instrument`, `duration`, `diversification`, `yield`, `pricing`, `covenant`, `esg`, `other`. |
| H | `source_document` | The document that sets the limit. |
| I | `current_value` | A plain number in `limit_unit`. |
| J | `headroom` | A plain number. For a `% NAV` row it must equal `limit` minus `current_value` to within 0.01. |
| K | `status` | `Pass`, `Watch` or `Breach`, under the status rule below. |
| L | `last_checked` | The date the row was checked, `YYYY-MM-DD`. |
| M | `checked_by` | Who checked the row; the template says `analyst`. |

**Status rule** (`Compliance_Monitor`, and `Sector_Exposure` rows with a limit): `Breach`
exactly when the current value exceeds the limit. Otherwise `Pass`, or `Watch` while the
headroom (limit minus current value, computed by the validator) is under 10 % of the limit.

Every limit is a maximum. A minimum (for example a minimum share of first-lien loans) is
entered as the maximum of its complement (a maximum share of second-lien and unsecured), or
as a metric on `Exposure_Summary`. Limits in other units (years, counts, rating notches) and
information-only rows belong on `Exposure_Summary` as metrics. Known limitation:
`Compliance_Monitor` has no direction field, so every limit is a maximum and minimum rows go on
`Exposure_Summary`.

#### `Holdings_Detail` (optional)

| Column | Header | Rule |
| --- | --- | --- |
| A | `issuer` | The issuer's name. |
| B | `instrument` | A plain description of the instrument. |
| C | `facility_id` | The facility's id, using only letters, digits, `-` and `_` (for example `TLB-2030`). |
| D | `par` | The par amount, a plain number. |
| E | `market_value` | The market value, a plain number. |
| F | `pct_nav` | Percent of NAV. |
| G | `rating` | The rating as reported. |
| H | `sector` | The sector's name. |
| I | `seniority` | The seniority, such as `1st Lien`. |
| J | `maturity` | The maturity date, `YYYY-MM-DD`. |

### Check the file

```
uv run deploy-vii validate-input portfolio path/to/portfolio.xlsx                      # one line per issue, then a summary
uv run deploy-vii validate-input portfolio path/to/portfolio.xlsx --as-of 2026-11-15   # also check its dates against the run's as-of date
uv run deploy-vii validate-input portfolio path/to/portfolio.xlsx --json               # the report as JSON
```

`--as-of` is the run's as-of date: the Mandate `as_of` must then be on or before it and at most 30
days before it, and no `last_checked` after it. The launcher runs the same check with the run's
as-of date on every portfolio workbook among a full credit assessment's or portfolio decision's
documents and tells CP-0, CP-3 and CP-6 each finding (ruling
`docs/rulings/2026-11-15-full-assessment-portfolio-workbook.md`).

The command exits 0 when the file passes and 1 otherwise. A passing file ends
`OK: <n> sheets, <m> compliance rows` (the template prints `OK: 8 sheets, 5 compliance rows`;
README is not counted). A failing one prints one line per issue, then `FAILED: <k> issues`.
Each issue reads `<file>:<sheet>!<cell>: <problem> — fix: <fix>`, for example:

```
portfolio.xlsx:Compliance_Monitor!J2: headroom 0.15 is not limit 2.5 minus current_value 2.37 = 0.13 (to within 0.01) — fix: enter limit minus current_value, or correct limit or current_value
```

The validator reads the workbook through the same extraction `prepare` uses
(`preparation.xlsx_content`). Workbook-level issues name the `Mandate` sheet, cell A1. If a
sheet is empty, its header is wrong or it has no rows, the validator reports only that and
does not check the sheet's rows; rules that compare sheets skip a sheet or cell that already
has an issue. These are the fixes it can print:

| Finding | Fix printed |
| --- | --- |
| File cannot be read | check the path and that the file is readable |
| Not an OOXML workbook (for example CSV or legacy `.xls`), too large to prepare, or two sheets with the same name | save the file as an Excel Workbook (.xlsx) and validate again |
| A damaged ZIP member (corrupt compressed data, a truncated member or an encrypted member) | save the file again as an Excel Workbook (.xlsx) and validate again; prepare would also refuse this file |
| A sheet that is not in the contract | delete the sheet or move it to another workbook; keep only Mandate, Exposure_Summary, Rating_Distribution, Sector_Exposure, Top_Holdings, Maturity_Profile, Compliance_Monitor, Holdings_Detail (optional) and README (optional) |
| Sheets out of order | order the sheets as in docs/templates/portfolio.template.xlsx: Mandate, Exposure_Summary, Rating_Distribution, Sector_Exposure, Top_Holdings, Maturity_Profile, Compliance_Monitor, Holdings_Detail (optional) and README (optional) |
| A required sheet is missing | add the sheet `<sheet>` with its header row, as in docs/templates/portfolio.template.xlsx |
| A sheet is empty | copy the header row of `<sheet>` from docs/templates/portfolio.template.xlsx and add one row per `<one row per>` |
| Header row not the sheet's (missing, extra or out of order) | set row 1 to exactly: `<the sheet's headers>` (A1 to `<last>`1, nothing after `<last>`1) |
| Header but no rows | add one row per `<one row per>`, starting in row 2 |
| Two rows share the sheet's key (reported on the later row) | keep one row per `<key>`, or correct the repeated value |
| A cell holds a formula | replace the formula with its value (Paste Special, Values) |
| A cell holds an Excel error such as `#N/A` | enter the real value in place of the error, or leave an optional cell empty |
| A cell holds TRUE or FALSE | enter text or a plain number, not TRUE or FALSE |
| A number that is not a plain number | enter a plain number: digits, an optional sign and one decimal point (no %, units, spaces or thousands separators) |
| A number longer than 40 characters | enter the number with at most 40 characters (Excel keeps 15 significant digits) |
| A number cell formatted as a percentage in a percent-of-NAV column | format the cell as General and enter 2.5 for 2.5 % NAV |
| A hidden sheet, or a row holding a hidden cell (a hidden row or column) | unhide the sheet, row or column, or delete it: hidden cells are not read as data |
| A date that is empty, not an ISO date, or an Excel date serial | enter the date as text YYYY-MM-DD (format the column as Text so Excel keeps it) |
| A total or subtotal row | leave out total and subtotal rows; Python adds the rows up |
| `Mandate` `section` empty or not one of the seven | enter one of Strategy, Key Parties, Capital Structure, Mandate Constraints, Liquidity Terms, Fees or Reporting |
| `Mandate` `field` empty | enter the field's name, e.g. fund_name |
| `Mandate` `value` empty | enter the field's value, or delete the row |
| No `Strategy` / `fund_name` row | add a row: section Strategy, field fund_name, value the fund's name |
| No `Strategy` / `strategy` row | add a row: section Strategy, field strategy, value CLO, Indexed Loans, Indexed HY or Other |
| No `Capital Structure` / `nav` row | add a row: section Capital Structure, field nav, value the fund's NAV as a plain number |
| No `Capital Structure` / `nav_currency` row | add a row: section Capital Structure, field nav_currency, value the NAV's three-letter currency code, e.g. USD |
| No `Reporting` / `as_of` row | add a row: section Reporting, field as_of, value the NAV and compliance date as text YYYY-MM-DD |
| `strategy` not one of the four | enter one of CLO, Indexed Loans, Indexed HY or Other |
| `nav` zero or negative | enter the fund's NAV, a number above 0 |
| `nav_currency` not three upper-case letters | enter the three-letter upper-case ISO 4217 code, e.g. USD |
| `Exposure_Summary` `metric` empty | enter the metric's name, e.g. nav |
| `Exposure_Summary` `value` empty | enter the metric's value as a plain number |
| `Exposure_Summary` `unit` empty | enter the unit, e.g. USD, % NAV, years or count |
| No `nav` metric | add a row: metric nav, value the fund's NAV (the Mandate nav), unit the nav_currency, as_of the NAV date |
| `nav` metric differs from the Mandate `nav` | enter the same NAV on Exposure_Summary and Mandate |
| `nav` metric's unit is not the Mandate `nav_currency` | enter the nav row's unit as the Mandate nav_currency, e.g. USD |
| A `one_pct_nav` row | delete the one_pct_nav row; Python computes 1 % of NAV from nav |
| `rating_bucket` empty | enter the rating bucket, e.g. B or Unrated |
| A `pct_nav` empty | enter the share of NAV in percent as a plain number (2.5 means 2.5 % NAV) |
| A `pct_nav` below 0 | enter the share of NAV as a number of at least 0; a short position is not a share |
| `Rating_Distribution` `pct_nav` sum outside 99.0 to 101.0 | correct the percentages, or add a row Unallocated with the remainder of NAV |
| `issuers` empty or not a whole number of at least 0 | enter the number of issuers as a whole number of at least 0, e.g. 12 |
| `sector` empty | enter the sector's name |
| `headroom_pct_nav` not `limit_pct_nav` minus `pct_nav` | enter limit_pct_nav minus pct_nav, or correct the limit or the exposure |
| `headroom_pct_nav` without `limit_pct_nav` | enter limit_pct_nav, or leave headroom_pct_nav empty |
| `Sector_Exposure` `status` without `limit_pct_nav` | enter limit_pct_nav, or leave status empty |
| `status` empty or not `Pass`, `Watch` or `Breach` | enter Pass, Watch or Breach |
| `rank` empty, not a whole number of at least 1, or ranks with gaps | number the holdings 1, 2, 3 and so on, with no gaps or repeats |
| `issuer` empty | enter the issuer's name |
| `instrument` empty | describe the instrument, e.g. Term Loan B due 2030 |
| `rating` empty | enter the rating as reported, e.g. B2 / B |
| `bucket` empty | enter the maturity bucket, e.g. 3-5 Years |
| `id` empty or not `C-01` style or `SECTOR` | enter an id such as C-01 (capital letters, a hyphen, two digits), or SECTOR for the sector-limit row |
| `constraint_category` empty | enter the constraint category, e.g. Single Name |
| `parameter` empty | describe the constraint, e.g. Max single issuer exposure |
| `limit` empty | enter the limit as a plain number in limit_unit (2.5 means 2.5 % NAV) |
| `limit_unit` empty, not `% NAV` or a currency code, or a currency other than the Mandate `nav_currency` | enter % NAV, or the Mandate nav_currency code (e.g. USD) for an amount limit |
| `breach_type` empty or not `Hard` or `Soft` | enter Hard or Soft |
| `scope` empty or not one of the twelve | enter one of issuer, rating_bucket, sector, seniority, instrument, duration, diversification, yield, pricing, covenant, esg or other |
| `source_document` empty | enter the document that sets the limit, e.g. Indenture s7.11 |
| `current_value` empty | enter the current exposure as a plain number in limit_unit |
| `headroom` empty | enter limit minus current_value as a plain number |
| `headroom` not `limit` minus `current_value` (`% NAV` rows) | enter limit minus current_value, or correct limit or current_value |
| `status` not `Breach` although the current value exceeds the limit | enter Breach, or correct the values: a current value above its limit is a breach |
| `status` `Breach` although the current value does not exceed the limit | enter Pass or Watch, or correct the values: only a current value above its limit is a breach |
| `status` `Watch` with headroom of at least 10 % of the limit | enter Pass: Watch is for headroom under 10 % of the limit |
| `checked_by` empty | enter who checked the row, e.g. analyst |
| `facility_id` empty or with other characters | enter the facility's id using letters, digits, - and _ only, e.g. TLB-2030 |
| `par` empty | enter the par amount as a plain number |
| `market_value` empty | enter the market value as a plain number |
| `seniority` empty | enter the seniority, e.g. 1st Lien |

The checks of sums and values (owner, 2026-11-15: "check data first likely incorrect sums and
values"). Arithmetic is exact. Shares are stored to two decimals, so a share recomputed from
amounts is compared to within 0.01 and a sum of n stored shares to within n x 0.005; a figure
missing or already reported is never taken as 0, and the rule that needs it is skipped.

| Finding | Fix printed |
| --- | --- |
| `Maturity_Profile` `pct_nav` sum outside 99.0 to 101.0 | correct the percentages, or add a row Unknown with the remainder of NAV |
| `Rating_Distribution` or `Maturity_Profile` sum between 0.99 and 1.01 (shares entered as fractions) | enter each share in percent of NAV: 2.5 means 2.5 % NAV, not 0.025 |
| `Sector_Exposure`, `Top_Holdings` or `Holdings_Detail` `pct_nav` sum above 101.0 | correct the percentages: these rows are parts of NAV and cannot add to more than all of it |
| `Holdings_Detail` `pct_nav` not `market_value` / Mandate `nav` x 100 (to within 0.01) | enter market_value / nav x 100, or correct market_value or the Mandate nav (both in the same unit and currency) |
| `Holdings_Detail` `market_value` per 100 of `par` outside 1 to 150 | enter par and market_value in the same unit and currency (both in units, not thousands) |
| `par` or `market_value` not above 0 | enter a number above 0 |
| `limit`, `current_value` or `limit_pct_nav` below 0 | enter a number of at least 0: a limit or an exposure is never negative |
| `Top_Holdings` ranked out of size order (a holding larger than the one ranked above it) | rank the holdings from the largest share of NAV down |
| `Top_Holdings` two rows with the same `issuer` and `instrument` | keep one row per issuer and instrument, or correct the repeated value |
| `Top_Holdings` `pct_nav` not the `Holdings_Detail` rows of the same issuer and instrument | enter the same share of NAV on Top_Holdings and Holdings_Detail, or correct the one that is wrong |
| `Exposure_Summary` `top10_pct_nav` below the ten largest holdings, or (ten listed) above them | correct top10_pct_nav or the Top_Holdings percentages: the ten largest holdings add to top10_pct_nav |
| `Holdings_Detail` rows of a sector adding to more than its `Sector_Exposure` `pct_nav` | correct the sector's pct_nav or the holdings' sector or pct_nav: the holdings in a sector cannot add to more than the sector |
| `SECTOR` row's `current_value` or `limit` not the `pct_nav` or `limit_pct_nav` of the one sector its `parameter` names | enter the same figure on Compliance_Monitor and Sector_Exposure, or correct the one that is wrong |
| A currency-unit `current_value` above the Mandate `nav` | enter the current value in the Mandate nav_currency and the same unit as nav (units, not thousands), or correct it |
| An `Exposure_Summary` amount in another currency than the Mandate `nav_currency` | enter the amount in the Mandate nav_currency, or move it to another workbook: an amount in another currency is not comparable with NAV |
| An `Exposure_Summary` `as_of` other than the Mandate `as_of` | enter the metric as at the Mandate as_of date, or correct the date |
| A `last_checked` before the Mandate `as_of` | check the row again at the Mandate as_of date and enter that date |
| A `Holdings_Detail` `maturity` before the Mandate `as_of` | delete the matured position, or correct its maturity date |
| With `--as-of`: the Mandate `as_of` or a `last_checked` after the run's as-of date | enter the date the figures were measured, on or before the run's as-of date |
| With `--as-of`: the Mandate `as_of` more than 30 days before it | supply the workbook as at a date at most 30 days before the run's as-of date |

Not checkable from the template's columns, so not checked: limit utilisation (no utilisation
column), par times price (no price column; the 1 to 150 range above catches a unit mix-up only),
issuer counts against `obligors` (an issuer can sit in two rating buckets), and `headroom` on
currency rows (stated, never used for room). A formula is refused outright, so a cached value that
disagrees with its operands is never read.

### How the file reaches the Portfolio Fit module

1. **Pack.** List the workbook as one source in your `prepare` request, with `media_type`
   `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`:

   ```json
   {"source_id": "portfolio", "path": "portfolio.xlsx",
    "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
   ```

   `prepare` freezes one span per stored cell, with locators `sheet:Mandate!<cell>`,
   `sheet:Exposure_Summary!<cell>`, `sheet:Rating_Distribution!<cell>`,
   `sheet:Sector_Exposure!<cell>`, `sheet:Top_Holdings!<cell>`, `sheet:Maturity_Profile!<cell>`,
   `sheet:Compliance_Monitor!<cell>` and `sheet:Holdings_Detail!<cell>`. It stores the raw
   values and evaluates no formulas.
2. **CP-0.** The CP-0 reviewer classes the source's authority. Python never sets it.
3. **Portfolio Fit and Portfolio Debate.** `deploy_vii.inputs.portfolio.portfolio_facts` reads
   the prepared source into typed rows (decimals, dates, whole numbers), each with its row
   number so a reader quotes the frozen cell by its locator. It refuses a workbook the
   validator does not pass. Python, not the model, computes 1 % of NAV and the room under each
   limit.

Keep real portfolio files out of Git. They belong in your environment's pack root, not in this
repository.

## Portfolio export (the fund's own files, beside the template)

Owner, 2026-11-15 (ruling `docs/rulings/2026-11-15-full-assessment-portfolio-workbook.md`, "The
export shape"). A fund's systems export the same facts as CSVs and a workbook. They are accepted as
they are, checked, and never converted into the template: converting would mean choosing between
figures that disagree, which the CP-6A method says to surface instead. The launcher finds the files
by their headers among a full credit assessment's or portfolio decision's documents
(`src/deploy_vii/inputs/portfolio_export.py`).

| File | Recognised by |
| --- | --- |
| Mandate (CSV) | first row `Section`, `Field`, `Value` (and `Notes`); capital structure rows under a `Capital Structure` section with a `Total` row; an `As of` field |
| Constraints (CSV, one or more) | a header with `Parameter`, `Limit` and `Current Value` (optional `ID`, `Constraint Category`, `Breach Type`, `Source Document`, `Headroom`, `Status`, `Last Checked`, `Checked By`) |
| Exposure report (CSV) | sections stacked in one sheet, each a title row (one cell), a header row and data rows: summary metrics, rating distribution, sectors, largest holdings, maturity profile, recognised by the title's words; `Total`, `Subtotal` and `Other` rows |
| Holdings (XLSX) | a `Holdings` sheet whose header has a borrower column (also `Ticker`, `Index Sector`, `Loan Name`, `FIGI`, `Ranking`, `Ratings`, `Margin`, `Maturity`, `Bid`, `Ask`, `Δ 1M`, `Δ YTD`, `Mid YTM`, `Mid 3Y DM` and `Holdings` = par); an optional `Market Data` sheet |

Values keep their unit: `≤ 2.5% NAV`, `≥ Caa1 (numeric ≤ 17)`, `B1 (14.3)`, `313 bps`, `4.82 yrs`,
`2.7 notches`, `USD 300,000,000`, `14.95m`. A value that cannot be read with its unit, an
approximate value (`~100%`) or a vendor token (`#N/A N/A`) is missing, never zero, and reported.

The holdings are the authority: par, market value at mid ((bid + ask) / 2 x par / 100), position,
borrower, ticker and sector counts, issuer, sector and second-lien shares of that market value, and
par-weighted price, margin and yield (yields outside -10 % to 100 % left out) are recomputed from
them. The classes of defect checked:

| Class | Check |
| --- | --- |
| 1 | Stated par, NAV, positions, obligors and sectors against the holdings (par and counts exact; NAV to within 0.5 % plus rounding, because the fund marks it and the check prices at mid; positions with no price are named) |
| 2 | The largest issuer, the ten largest issuers and each listed holding (present, market value, share, positions) against the holdings |
| 3 | Each listed sector's share against the holdings', and its limit on the holdings' share: a breach the stated share hides |
| 4 | Every Total and Subtotal row against its rows: shares and amounts to within the rounding of the figures added (half a unit in each one's last place), counts exactly |
| 5 | Average price, margin, yield and second-lien share against the holdings; the stated price against stated NAV over par; a stated yield below the stated margin |
| 6 | The capital structure's tranches against its stated total, and the total against the collateral NAV (95 % to 105 %) |
| 7 | Maturities before 1950: two-digit years read as 19xx; maturities before the as-of date |
| 8 | Yields outside -10 % to 100 % and discount margins outside -1,000 to 10,000 bps, with the average with and without them |
| 9 | Vendor error tokens in numeric columns and ratings (withdrawn ratings and watch flags are notes, not defects) |
| 10 | FIGIs not 12 characters, a FIGI on two rows, a ticker naming two borrowers, damaged names, a rating in Ranking, rows of empty cells |
| 11 | Dates after the run's as-of date or more than 30 days before it |
| 12 | Limits and values that cannot be read with their unit, approximate values, a value without the limit's unit; status and headroom against limit and value; each constraint the holdings can recompute (largest issuer, largest sector, second lien) against them |

Not recomputed: rating and maturity distributions (no rating scale or bucket rule is part of the
export), the weighted average life and rating factors. They are listed as not checked.

```
uv run deploy-vii validate-input portfolio-export <mandate>.csv <constraints>.csv <exposure>.csv <holdings>.xlsx --as-of 2026-11-15
```

`tools/synthetic_portfolio_exports.py` builds a SYNTHETIC clean export and one per class.

## Run context form (`context-form.html`, `context.json`, schema `context/1`)

The form writes `context.json`; `src/deploy_vii/context.py` reads it, and the form's `build()` is the
normative rule set. The file is now also the run start page: `python -m deploy_workflow.run_start`
serves it, Submit after an approved summary takes the place of the Download step, and the service
writes `context.json` into the run's own source folder, so analysts no longer handle the file or
drop folders (the inbox is gone; root `README.md`, section 3). Where the notes below say "download",
they describe the rules the page applies before Submit. New optional fields, each omitted from the file when empty (so older files load
and re-save unchanged; a file that uses one needs this version or later):

- `identity.issue_classification`: `investment_grade` or `high_yield`. The form requires a choice
  (nothing preselected); the reader accepts a file without it.
- `deal_terms[].coupon_pct`, `margin_bps` (plain non-negative numbers, no sign or unit) and `maturity`
  (`YYYY-MM-DD`). Facility rows are allowed on every run type and required (at least one) for Primary only.
  Tenor and price talk are shown for Primary only; the form writes them blank on other run types.
- `attachments.legal_documents` has no preselected choice in the form (`executed`, `draft` or `none`).

The form (adopted 2026-11-10; design and module review in
`docs/design/2026-11-10-context-form-proposal.md`) asks in five steps: documents, purpose, confirm (issuer, dates, legal file), more context (market,
valuation, assumptions and questions, only where a module of the run uses them), then a check
before download.

**Rules the form adds.** `context.py` does not enforce these, so a hand-written file without them
still loads; the form will not download without them:
- `identity.issuer_id` at most 40 characters (the summary refuses longer).
- `run.pathway` `earnings_update` if and only if `run.run_type` `earnings`.
- `run.current_period` where CP-2G runs (the forecast's base).
- An explicit answer for each attachment the pathway uses.
- A confirmation that an `executed` or `draft` legal document is in the folder.
- The reader's own refusals, caught before download: a research question with `|`, and U+0085,
  U+2028 or U+2029 in any text.

**The research cutoff is always written.** It follows the as-of date until the analyst changes it,
and a loaded file with a blank cutoff gets the as-of date, with a note. The code reads blank as the
as-of date, so nothing changes for it. The modules, which read the raw file, had reported a blank one
as "information cutoff not supplied" (an ambiguity flagged for every module in the TDG
all-modules run).

**What it shows without enforcing:**
- Notes, for example an as-of date before the newest file, a stale quote, two rows for one rating
  agency, or a peer older than 12 months.
- An expected outcome for each module (Ready, Check, Gap, Limited, Will refuse), ported from
  `run_expectations.RULES` with dependency propagation. Download needs one acknowledgement while
  any limit remains.

**Copied tables.** The form copies these from the code and the library:
- the run order per pathway and peer source;
- the dependency edges;
- module names, rating scales, limits and design tokens.

`tests/test_context_form.py` fails when one drifts from its source.
