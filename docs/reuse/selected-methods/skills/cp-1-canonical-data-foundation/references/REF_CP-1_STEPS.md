One section per step, in order, each with its gate and output; the last two sections bind every run. Steps 4 to 6 always run: with no data for a statement, write its table empty of figures and log the gaps.

Statement tables (T4.4, T4.5, T4.6) share one shape. The first column is headed `Line item`; then one column per period (the year is the fiscal year the period belongs to), then `Unit` (the currency code and `millions` or `thousands`, the same in every statement table), `Basis` and `Source`. The fixed rows named in steps 4 to 6 are added as the checked-tables rule states. A balance sheet is an instant: it has no start date.

## REF_CP-1_01_FileGateSourceValidation.md
Gate: no financial sources means Blocked; say so in the Bottom line and stop.
1. Inventory every source file in the register's columns, with its evidence tier (Tier 1 audited statements, 2a unaudited with auditor review, 2b unaudited without, 2c lender or sponsor material, 2d rating agency, 3a internal, 3b external). Classify from content, never from file names.
2. Assess sufficiency for income statement, cash flow statement, balance sheet and KPIs; flag the consequence if insufficient.
3. Complete this register before any extraction.

Output `### T4.1 Source register`: `Source File Name` | `Document Type` | `Period Coverage` | `Currency` | `Unit` | `Perimeter` | `Accounting Basis` | `Evidence Quality Tier` | `Analytical Use` | `Limitations`

## REF_CP-1_02_EntityPeriodScope.md
Gate: source-supported only; no entity inference from file names.
1. Establish the entity scope: issuer (legal entity), borrower, guarantor group, restricted group. Note ambiguity.
2. Establish every reporting period (annual, interim, quarterly), fiscal year end, stub and short periods.
3. Flag a perimeter that differs across sources, since it affects step 3.
4. Map every source to its entities and periods.
5. Flag every subsequent event (runbook) with its date below the table.

Output `### T4.2 Entity period key`: `Entity Name` | `Entity Role` | `Fiscal Year End` | `Reporting Currency` | `Reporting Unit` | `Consolidation Perimeter` | `Accounting Basis` | `Available Periods`

## REF_CP-1_03_Normalization.md
Gate: source data for at least one period.
1. Set one basis: one currency (with FX rates and their source), one unit, one perimeter, one accounting basis.
2. Record every adjustment in the register.
3. Carry an incompletely normalised figure with a limitation marker. Flag an unresolvable accounting-basis difference; never choose silently.

Output `### T4.3 Normalization register`: `Adjustment Description` | `Source File` | `Adjustment Type` | `Before Value` | `After Value` | `Rationale` | `Affected Periods`

## REF_CP-1_04_IncomeStatementCoverage.md
Gate: always runs.
1. Extract the full income statement for every available period on the step 3 basis.
2. Cover these lines: Revenue, COGS, Gross Profit, SGA, Other Operating, EBITDA, D&A, EBIT, Interest Expense (total and cash), Interest Income, Other Non-Operating, PBT, Tax (total and cash), Net Income, Exceptionals, SBC. Reconcile the intervening expense block between gross profit and operating profit.
3. Each line carries its source file, period, currency, unit, value and evidence tier in the `Source` and `Basis` cells.
4. EBITDA not stated: derive it from components and say so in `Basis` as calculated; if components are insufficient it is `Not calculable: <reason>`.

Output `### T4.4 Income statement` (statement table). Fixed row: `EBITDA (Reported)`, the issuer's unadjusted EBITDA. Optional fixed row: `EBITDA (Adjusted)`, written only when the issuer states an adjusted figure (name its definition and add-backs in `Basis`). Log both for step 10.
5. Segment schedule: one row per business unit and period with the issuer's label, in the issuer's order. Corporate and eliminations are one separate row per period (aggregate the source's elimination lines first), never an operating unit. When no segment revenue is disclosed, say so in a gap line and state no segment sum, never a zero.
6. Adjusted EBITDA bridge, only when the issuer states adjusted EBITDA: one row per add-back with the issuer's own label, a classification (restructuring, share-based compensation, cost savings, run-rate, synergy, transaction costs or other stated) and a realisation status (realised, unrealised or not stated) that is never inferred from the classification; split an item when only part is realised. Add-backs are never merged, and no plug or balancing line is allowed. With no add-backs stated the bridge is empty and the adjustment is zero. It is the host's `Chart data: EBITDA bridge` table; write no second bridge table.

## REF_CP-1_05_CashFlowStatementCoverage.md
Gate: always runs.
1. Extract the full cash flow statement for every available period.
2. Cover: OCF (before and after working capital), WC Change, Capex (maintenance, growth, total), FCF (levered, unlevered, stating whether working capital is included), Dividends, Acquisitions, Disposals, Debt issuance and repayment, Equity issuance and buyback, Cash Taxes Paid. Trace as in step 4.
3. Capex sub-categories not disclosed are `Not supplied: <reason>`; carry Total Capex. Cash interest paid (cash flow) can differ from cash interest expense (income statement); keep them apart.
4. Outflows are negative and inflows positive. Cash interest and cash tax are cash paid, not accrued expense. Record in `Basis` where the issuer classifies operating-lease cost (inside operating expenses; under IFRS 16 only short-term and variable lease expense), lease principal paid (financing activities under IFRS 16 and for US GAAP finance leases) and interest paid (financing activities is an IFRS option; operating activities under US GAAP). Taxes paid classified outside operating activities are a gap line.

Output `### T4.5 Cash flow statement` (statement table). Fixed rows: `Net Cash from Operating Activities`, `Net Cash from Investing Activities`, `Net Cash from Financing Activities`, `Net Cash Change`, `Opening Cash`, `Closing Cash`, `Cash Interest Paid`. Optional fixed row: `FX Effect on Cash`. `Net Cash Change` excludes nothing: it is operating plus investing plus financing plus the FX effect.

## REF_CP-1_06_BalanceSheetCoverage.md
Gate: always runs.
1. Extract the full balance sheet at each reporting date.
2. Cover: Cash & Equivalents, Restricted Cash, ST Investments, Trade Receivables, Inventories, Other CA, Total CA, PP&E (Net), Goodwill, Other Intangibles, Other NCA, Total Assets, ST Debt, Current Portion LTD, Trade Payables, Other CL, Total CL, Senior Secured Debt, Senior Unsecured Debt, Subordinated Debt, Total Debt, Pension and Lease Obligations, Other NCL, Total Liabilities, Shareholders' Equity, Minority Interests, Total Equity.
3. Debt by seniority: not disclosed is `Not supplied: <reason>`; never estimate. Separate pension and lease obligations from financial debt where possible. A non-debt funding float is flagged here (runbook); also read the subsequent-events note.

Output `### T4.6 Balance sheet` (statement table). Fixed rows: `Total Assets`, `Total Liabilities`, `Total Equity`, `Total Debt`, `Cash & Equivalents`. Optional fixed row: `Temporary Equity`.

Output also `### T4.18 Debt instruments`, one row per instrument at the latest balance-sheet date: `Instrument` | `Type` | `Carrying Value` | `Principal` | `Drawn` | `Commitment` | `Security` | `Ranking` | `Currency` | `Coupon or Margin` | `Rate Type` (fixed, floating or not stated) | `Reference Rate` | `Spread (bps)` | `Floor (bps)` | `Maturity` | `Annual Amortisation` | `Source`. Rules: carrying value and principal are separate columns and neither stands in for the other. Security, ranking and rate type are never inferred from the instrument name. A security, ranking or other term no source states is `Not supplied: <reason>`; for security or ranking it is not evidence of either, and such a row stays out of secured and senior subtotals. A term that does not apply (a floor with none stated, a spread on a fixed rate) is `Not applicable`, not a gap. Annual amortisation is the scheduled principal paid per year in the table's currency and unit: 0 for a bullet or no scheduled amortisation, `Not supplied` with a gap line only when it is not stated. When instrument carrying values are not disclosed, keep each instrument's disclosed principal and add one `Financing cost adjustment` row for the separately disclosed aggregate issuance cost, discount or premium; only that row may be negative. The instruments plus that row reconcile to `Total Debt` (step 7).

## REF_CP-1_07_NormalizedFinancialsTable.md
Gate: at least one of steps 4 to 6 produced data.
1. Cross-check, per period column, the three identities of the checked-tables rule (balance sheet, cash-flow totals, cash roll-forward) and net income against equity movements. Compare to the precision the figures are printed at. A difference in an identity is corrected at the wrong figure, never plugged; when the source itself prints the difference, write `Not supplied: <reason>` on the total it cannot support and add a gap line with its materiality; a difference in net income against equity movements is likewise a gap line.
2. Also reconcile: segment revenue to reported revenue, the EBITDA bridge, the adjusted EBITDA bridge, the operating cash flow identity, the debt instruments to `Total Debt`, and the reported fiscal year to the sum of its quarters. A difference may stand as a warning with its explanation; it is never forced to zero.

Output: no register of its own.

## REF_CP-1_08_DerivedPeriodConstruction.md
Gate: sub-period data must exist. Never estimate.
1. LTM is the latest full year plus the current stub minus the prior-year comparable stub. Construct YTD where applicable. Never replace a directly reported period with a derived one.
   Quarters: a reported discrete quarter comes first. Q2 is H1 less Q1 and Q3 is 9M less H1 only when the quarters are absent. A reported unaudited Q4 stands alone; Q4 is FY less 9M only when no Q4 is reported, and is labelled calculated. A reported fiscal year is never replaced by a sum of quarters. A balance-sheet last-twelve-months figure is the latest period end.
2. Every component must be available (runbook); stub periods must be comparable, or the result is Not Comparable.
3. Pro forma adjustments: record only those a source states. They stay out of period figures, in the host's `Post-balance-sheet adjustments` table; never construct one the source does not state.

Output `### T4.8 Constructed period register`: `Metric Name` | `Derived Period Type` | `Full-Year Component` | `Current Stub` | `Prior-Year Stub` | `Derived Value` | `Calculation Status` | `Source Files` | `Limitations`

## REF_CP-1_09_CalculationRegisterKPIBuild.md
Gate: normalised data for at least some periods.
1. Calculate every KPI of the runbook's list whose inputs are available. A missing input makes the KPI `Not calculable: <reason>`; never estimate it.
2. Cover uses cash interest paid as its denominator.
3. Give each KPI a full audit trail in the register, its calculation status one of the runbook's values.
4. Operating measures (subscribers, users, connections, homes passed, backlog, churn, ARPU) are dashboard rows labelled period-end, period flow or rate. A period-end value is the last observation, a flow may be summed, a rate is shown only where sourced and never averaged. A change of definition or perimeter starts a new row; never join non-comparable series. Do not repeat revenue, EBITDA, leverage or other financial ratios here.

Output `### T4.9 Calculation register`, columns exactly: `Metric Name` | `Formula` | `Numerator Value` | `Numerator Source` | `Denominator Value` | `Denominator Source` | `Period` | `Currency` | `Unit` | `Calculated Value` | `Calculation Status` | `Evidence Quality Tier` | `Limitations`
- `Period` is the period column header (`FY2024`); the six fixed rows are as the checked-tables rule states. `Numerator Value`, `Denominator Value` and `Calculated Value` are each a plain number or `Not supplied:` or `Not calculable:` with a reason, no annotation. `Currency` and `Unit` are never empty; `Unit` is the operands' unit.
- Fixed `Metric Name` values (other metrics keep free names): `Total debt / EBITDA`, `Net debt / EBITDA`, `EBITDA / cash interest` (reported EBITDA), and, only when the issuer states an adjusted EBITDA, `Total debt / adjusted EBITDA`, `Net debt / adjusted EBITDA`, `Adjusted EBITDA / cash interest`. For these six rows `Unit` is `US$m`, the Net debt table's unit.

Output `### T4.10 KPI dashboard`: `KPI Category` | `Metric Name` | one column per period | `Trend Direction` | `Analyst Note`. It also keeps the KPIs T4.9 does not calculate (issuer-reported margins, segment and operating KPIs).

## REF_CP-1_10_DefinitionConflictRegister.md
Gate: always runs; with no conflict, confirm alignment in one sentence (no conflicts across N metrics and M sources).
1. Review every metric: issuer definition against this method's; sources disagreeing; a definition changed across periods.
2. Log each conflict in the register, with its materiality quantified.
3. Common areas: EBITDA (add-backs, management against audited), debt (leases, pensions, drawn facilities), FCF (levered against unlevered), capex (capitalised items, maintenance against growth), net debt (restricted cash, short-term investments).

Debt basis: debt totals use carrying values. Principal and commitment are kept separately and are not substitutes for carrying value. Total Debt is every balance-sheet debt line the issuer carries. Lease liabilities the issuer presents on their own balance-sheet lines are not added to it. A lease or other obligation the issuer carries inside its debt lines stays in, and `Basis` names it. The carrying-against-principal difference is always one row here, with both figures and their locators.

Output `### T4.11 Definition conflict register`: `Metric Name` | `Canonical Definition` | `Issuer-Reported Definition` | `Source of Conflict` | `Periods Affected` | `Materiality` | `Modules Affected` | `Resolution / Recommendation`

## REF_CP-1_11_EvidenceRiskCreditAnalysis.md
Gate: at least one KPI from step 9; with none, write a data-quality analysis only.
1. Apply the depth chain (Analytical depth 2) in sentences to every material finding. Cover: leverage trajectory and drivers; coverage trends (interest cover and FFO/Debt trajectory); cash-flow quality (conversion, working capital, capex intensity); liquidity adequacy (cash and undrawn against near-term obligations); data-quality risks; definition risks; the most material gaps and their credit consequence.
2. Synthesis only: no new data and no new figure; every statement is issuer-specific and traces to an earlier table. Write the runbook's stories where present: non-debt funding float, subsequent events (date, effect, why excluded), multi-figure events (which figure serves which purpose).

Output: the analysis inside `## Findings`, by analytical dimension.

## REF_CP-1_12_CoverageGateDownstreamReadiness.md
Gate: always runs; the final quality gate.
1. Consolidate every gap from every prior step as a plain-sentence line under `## Gaps`: what is missing or unreconciled, for which line item or metric and period, what it restricts, its severity (High, Medium, Low) and the action that would close it. Cumulative; no omissions.
2. Judge readiness of the figures for the requested use: which conclusions and calculations the evidence supports and which stay restricted. Group repeated consequences under their issue.

Output `### T4.13 Readiness`: `Requested Use` | `Readiness Status` (Ready, Ready with Limitations, Not Ready) | `Gaps or Limitations` | `Recommended Actions`

## Anti-patterns (REF_CP-1_AntiPatterns.md)
- Fabrication fails the module: a figure no source gives is `Not supplied: <reason>` with a gap line and its consequence.
- Exact figures at source precision; no rounding without disclosure.

## Discipline (REF_CP-1_Discipline.md)
- An assertion cites a source file and locator. Where sources or definitions disagree, give each figure with its source, log the conflict and name the figure used; never reconcile silently; a definition change from this method's to the issuer's is flagged and logged, never silently adopted.
- Currency or unit switching after step 3 is prohibited.
- Every figure is one of four kinds, labelled in the table's `Basis` cell or the paragraph's Basis line, never inside a sentence: reported (with its source), Normalized (with its register reference), Calculated (with formula and register reference) or Analyst Judgement. Decompose mixed content. Page locators go in `Source` columns and Basis lines, never in a sentence.
- No independent credit recommendation and no unsupported normalisation.
- A draft or incomplete source: state the limitation and its consequence.
