# The full credit assessment collects the portfolio workbook, checked first

by: user
date: 2026-11-15

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line; paid execution still needs its own explicit action. No run has been made with this change.

Owner's words, 2026-11-15, answering the question left open by
`2026-11-15-full-assessment-cp3c-cp6a.md` ("Mandate and exposure inputs: ... Whether the full
assessment should collect the workbook is the owner's decision"): "yes, wire in the portfolio
workbook." and, about their own workbook (a folder "Portfolio Data" on their computer, which no
session could reach): "check data first likely incorrect sums and values."

Scope: offline only. No provider was called. The full credit assessment is the `credit_snapshot`
pathway (`2026-11-13-full-and-lite-credit-assessments.md`). This record answers that ruling's "Left
open" item on mandate and exposure inputs; that ruling is not edited.

## What was true before

- Only `portfolio_decision` asked for the workbook: the run start page showed "Which file is it?
  Portfolio workbook" for that pathway alone and wrote `attachments.portfolio_workbook` (true when a
  file was chosen). The launcher read the workbook as it reads every uploaded file, pinned it as a
  source, and gave no module an instruction about it; `validate_portfolio`
  (`src/deploy_vii/inputs/portfolio.py`) ran nowhere in the CP-OS path. The forecast had one rule,
  `portfolio-workbook-false` (Gap, CP-6, portfolio decision without a workbook).
- `validate_portfolio` checked the layout (sheets, headers, hidden cells, formulas refused, Excel
  errors, TRUE/FALSE, plain numbers, percent-formatted cells in percent columns, ISO dates, keys,
  total rows) and a few values: the Mandate's required fields, NAV above 0, the Exposure_Summary nav
  equal to the Mandate's, the Rating_Distribution adding to 99 to 101, headroom equal to limit minus
  exposure (to within 0.01, `% NAV` rows and sectors), status consistent with limit and exposure,
  top-holding ranks 1 to n, a negative `pct_nav`. It checked no other sum, no share against its
  amounts, no unit or currency mix in amounts, no date against another or against the run.
- The documented self-check, `deploy-vii validate-input`, did not exist as a command in this
  repository.
- CP-3's portfolio-fit registers (T3C.1 to T3C.3, T3C.5 to T3C.9) are cut in every pathway by
  `CPOS_REGISTER_SCOPE.md § CP-3` (`2026-11-13-appendix-and-routing-scope.md`), the portfolio
  decision included; the method's phase runs inside every CP-3 run.

## Decisions

- Run start page: the portfolio workbook question is asked in `credit_snapshot` as in
  `portfolio_decision` (`PORTFOLIO_PATHWAYS` in `docs/templates/context-form.html`). It is asked,
  not required. A full assessment without it runs as before, and CP-6 is told that none was supplied
  and states that in its `### Portfolio posture` section (exact constraint not established, sizing
  within the fund's limits not tested), as the CP-6A gate's own rule asks. Why not required: the
  workbook serves one section of the committee module, and a run without it still answers the
  credit question; the portfolio decision, where the workbook is the question, keeps its Gap.
- Forecast (`run_expectations.RULES`), all read from the launcher's own search and checks:
  `portfolio-workbook-none` (CP-6, Note, full assessment without a workbook: no tick),
  `portfolio-workbook-not-found` (CP-6, Check: a workbook chosen but no uploaded workbook in the
  template's layout; one tick), `portfolio-workbook-not-chosen` (CP-6, Check: a workbook in the
  layout among the documents but not chosen; one tick), `portfolio-workbook-fails-checks` (CP-6,
  Limited: one tick, the reason names the first finding). A clean, chosen workbook adds no item. The
  USD 20 cap and its check are unchanged; the forecast shows no USD figure.
- Launcher (`src/deploy_workflow/portfolio_workbook.py`, called by `cpos_launch._prepare` for these
  two pathways only): a source is a portfolio workbook when two or more of the template's required
  sheets are named in it. Each is checked with `validate_portfolio_bytes` against the run's as-of
  date. CP-0, CP-3 and CP-6 are told the source, the check result and, for a failing workbook, every
  finding (at most 40 listed) and that a figure a finding names is not a live constraint or exposure;
  CP-0 records the result in its source register and gaps, CP-3 records the figures under Gaps, CP-6
  says in plain words in its posture which totals do not reconcile. The launcher's readiness print
  gains `Portfolio:` lines. Every other pathway's instructions, items and readiness are byte for
  byte as before.
- What a failed check does: the existing convention of the validator is that any finding refuses
  the workbook for typed use (`portfolio_facts` raises). The CP-OS path has no typed use, so the
  workbook is restricted, not refused: it stays a source, the run is not stopped, the three modules
  are told each finding, and the forecast's Limited item must be ticked. This follows the CP-6A
  method's rule that mismatched or stale rows "create a gap and cannot become a live constraint or
  exposure".
- Checks added to `validate_portfolio`, each naming sheet and cell, the stated and the recomputed
  figure and the difference: Maturity_Profile adding to 99 to 101; a distribution adding to about 1
  (fractions); Sector_Exposure, Top_Holdings and Holdings_Detail adding to at most 101; each holding's
  `pct_nav` against `market_value` / NAV x 100 (to within 0.01); market value per 100 of par
  between 1 and 150 (units); par and market value above 0; limit, exposure and sector limit not
  negative; top holdings in size order and with no repeated issuer and instrument; top holdings
  against the holdings detail; `top10_pct_nav` against the ten largest; a sector's holdings not
  above the sector; the sector-limit row against the sector it names; a currency exposure above NAV;
  an Exposure_Summary amount in another currency; metric dates and `last_checked` against the
  Mandate `as_of`; matured positions; with a run date, `as_of` after it or more than 30 days before
  it and `last_checked` after it. Arithmetic is exact (`Decimal`); tolerances exist only for shares
  stored to two decimals (0.01 for one recomputed share, 0.005 per stored share in a sum) and are
  tested at their edges. A blank is never taken as 0: a rule whose operand is missing is skipped.
- `uv run deploy-vii validate-input portfolio <file> [--as-of YYYY-MM-DD] [--json]` now exists
  (`[project.scripts]`, `src/deploy_vii/inputs/__main__.py`), so the owner can check a workbook
  before uploading it.
- `portfolio_decision`: it shares the launcher's search and checks, so a workbook it is given is now
  checked and its findings told to CP-0, CP-3 and CP-6 (new), CP-6 is told when none was supplied
  (new), and the forecast gains the not-found, not-chosen and fails-checks items. Its existing Gap
  for a missing workbook is unchanged.
- CP-3B: not restored. The register cut is per module and `portfolio_decision` runs CP-3 with the
  same cut, so mirroring it restores nothing. CP-3's portfolio-fit phase still runs and is told the
  workbook and its findings. Restoring T3C.1 to T3C.3 and T3C.5 to T3C.9 when a workbook is supplied
  needs an owner decision: it would make the register scope depend on the pathway or the inputs
  (it is per module today), add instruction size and output to CP-3, CP-5 and CP-6 in both
  pathways, and reverse part of a cut made because no consumer read them.

## The export shape

Later on 2026-11-15 the owner uploaded their portfolio data to the coordinating session (not to this
repository; no session here has read it). The coordinating session reported its shape and defects:
four CSV exports (a mandate file; a constraints compliance monitor; a near-identical constraints
sheet named "CP-3C Portfolio Constraints"; an exposure report with five stacked sections) and a
workbook with a Holdings sheet (382 loans) and a Market Data sheet, all pasted constants, with
twelve classes of defect: the report not reconciling to the holdings; concentration figures
disagreeing with the rows; limits that pass on stated figures but breach on recomputed ones;
subtotals that nearly add; inconsistent summary metrics; a capital structure that does not
balance the collateral; maturities a century off; impossible yields and margins; vendor error
tokens; identifier defects; stale dates; and limits and values written as text with units.

Decisions:

- The export is accepted beside the template, not instead of it, and never converted into it.
  Converting would mean choosing between figures that disagree, which the CP-6A method says to
  surface. The template stays the documented typed contract.
- `src/deploy_vii/inputs/portfolio_export.py` reads the export (files recognised by their headers;
  the report's sections by their title rows) and checks it with the holdings as the authority:
  stated figures are claims checked against the holdings' recomputation and against their own
  totals. Values keep their units; what cannot be read, an approximate value or a vendor token is
  missing, never zero, and reported. Each of the twelve classes has a check and a SYNTHETIC
  fixture (`tools/synthetic_portfolio_exports.py`, invented names and numbers, none of the
  owner's), with hand-written expected findings (`tests/test_portfolio_export.py`).
- Tolerances: a stated figure may differ from the exact one by half a unit in its last place (a sum
  by the sum of those halves); a figure the fund marks itself (NAV, market values, the average
  price, shares of NAV) may also differ from a recomputation at mid by 0.5 % of the stated figure;
  counts and par are exact. Yields outside -10 % to 100 % and discount margins outside -1,000 to
  10,000 bps are impossible; maturities before 1950 are two-digit years read as 19xx; the capital
  structure must fund 95 % to 105 % of the collateral.
- The launcher finds the export among the run's `.csv` and `.xlsx` sources in the same two
  pathways, and tells CP-0, CP-3 and CP-6 the files and their roles, what the holdings give, the
  notes (withdrawn ratings, watch flags, figures not recomputed) and every finding, with the same
  restriction as a failing workbook. The forecast items are the same four. On the run start page
  the analyst uploads every file of the export and chooses the holdings workbook as the portfolio
  workbook.
- `uv run deploy-vii validate-input portfolio-exports <folder or files> --as-of <date>` checks
  the export together and prints a reconciliation table of the headline figures first.
- Extended on the coordinating session's later request (branch
  `claude/busy-dijkstra-bgex9m-s12b-portfolio-exports`): the parts may be CSV files or sheets of
  one workbook; rating buckets with issuer counts (Moody's, else S&P), the lien split, the
  par-weighted life and maturity buckets are recomputed, maturity figures as given with the 19xx
  correction beside them and never applied; a bid above its ask, a holding above its tranche, a
  borrower under two tickers, a value of another column's kind and the par a missing price leaves
  out are reported; findings come breach first, then totals and balances, then contradicted
  figures, then dates, then cell defects. Obligors are counted by borrower name. The owner noted
  the same day: "no live run yet, and pathway will be restructured before live run"; nothing here
  changes a pathway's module list.
- Corrected after the coordinating session ran the check on the owner's files and reported false
  findings where the reader's reading of the layout differed from the real one: capital structure
  amounts followed by a spread; constraint parameters mapped by what they say (top ten, named
  sector, n-th largest; unmappable rows not checked); the named largest compared; `1L`/`2L` lien
  tokens; `0% NAV`, `Info only` and em dashes; the second constraints layout, and two constraints
  files compared; name-and-figure summary cells; the largest-holdings columns and total row; report
  names matched to legal borrower names on a stated basis; sector totals where Other states no
  count; figures shown to the stated places plus two. Each layout fact has a SYNTHETIC fixture.
- Corrected after the second check on the owner's files: an exclusion row's `0% NAV` is a
  maximum (and a zero limit with no direction word is "at most 0%"); the weighted average price,
  a life stated in a `(yrs)` column name, and second lien from the constraints are now in the
  reconciliation table, and the yield there carries its unit; a listed name no borrower matches
  names the borrowers that may be meant, as possible and never compared; the positions line
  states the row total.

Open, for the owner: the export names one constraints sheet "CP-3C Portfolio Constraints". In this
repository portfolio fit is CP-3B, inside CP-3; CP-3C is Refinancing & LME. The coordinating session
has asked the owner which was meant. Nothing here acts on the name: both constraints files are read
as constraints and told to CP-0, CP-3 and CP-6.

Not proven: the reader was built from the coordinating session's description, not the owner's
files. Their exact headers, section titles and date formats may differ from what is recognised;
the self-check then says which file was not recognised or which section was not found, and the
reader is adjusted on that evidence.

## Cost

No run has measured this. Measured on the synthetic launcher input (as-of 2025-03-31), the
instructions grow by: no workbook, 677 characters (CP-6 only); a clean workbook, 779 (CP-0), 714
(CP-3) and 714 (CP-6); a workbook with three findings, about 1,750 each, so about 250 per listed
finding, at most 40 listed (about 10,000 more characters each). The workbook itself was already a
source the modules could read and is still read only when a module searches it. Estimate, not
measured: at GPT Sol's input price (USD 2 a million tokens, about four characters a token) and
some 30 calls per module before caching, no workbook or a clean one adds about USD 0.01 to 0.03 a
run; a workbook failing with 40 findings listed up to about USD 0.5. The USD 20 cap and its check
are unchanged, and the run start page shows no USD forecast.

## Left open

- A paid run: no model has produced CP-6A output with a workbook under these instructions.
- The owner's own workbook and export have not been read here; they can be checked with the
  commands above.
- The "CP-3C Portfolio Constraints" name, as above.
- CP-3B's cut registers, as above.
- `docs/templates/README.md` still describes the Deploy VII pack path ("How the file reaches the
  Portfolio Fit module", `scripts/build_templates.py`, `tests/product/test_inputs_portfolio.py`),
  none of which exists in this repository; the template binary has no generating script here.

## Status

Built and tested offline: the checks against hand-written findings on SYNTHETIC workbooks
(`tools/synthetic_portfolio_workbooks.py`, `tests/test_portfolio_workbook.py`), the launcher's
instructions, items and readiness for the full assessment with no workbook, a clean one and one with
wrong sums, and every other pathway unchanged. Not accepted: acceptance needs the paid run.
