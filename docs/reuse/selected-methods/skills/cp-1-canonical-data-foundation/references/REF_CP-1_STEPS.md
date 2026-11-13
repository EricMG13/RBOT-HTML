Method steps, one section per step, in order. Each step states its gate and its output. The last two sections bind every run.

Statement tables (T4.4, T4.5, T4.6) share one shape. The first column is headed `Line item`; then one column per period, headed `FY2024`, `Q3 2025`, `H1 2025` or `9M 2025` (the year is the fiscal year the period belongs to); then `Unit` (the currency code and `millions` or `thousands`, for example `USD millions`, the same in every statement table), `Basis` and `Source`. Issuer line items keep the issuer's own label. The fixed rows named in steps 4 to 6 are added beside them, one row each, with exactly that label in the first cell. Every cell is a plain number (a minus sign for a negative, no currency symbol, bracket or text) or `Not supplied: <reason>` or `Not calculable: <reason>`. A balance sheet is an instant: it has no start date.

## REF_CP-1_01_FileGateSourceValidation.md
Gate: no financial sources means Blocked; say so in the Bottom line and stop.
1. Inventory every source file: name, type, period coverage, currency, unit, perimeter, accounting basis, evidence tier (runbook hierarchy). Classify from content, never from file names.
2. Assess sufficiency for income statement, cash flow statement, balance sheet and KPIs; flag the consequence if insufficient.
3. Record analytical use and limitations per source. Complete this register before any extraction.

Output `### T4.1 Source register`: `Source File Name` | `Document Type` | `Period Coverage` | `Currency` | `Unit` | `Perimeter` | `Accounting Basis` | `Evidence Quality Tier` | `Analytical Use` | `Limitations`

## REF_CP-1_02_EntityPeriodScope.md
Gate: source-supported only; no entity inference from file names.
1. Establish the entity scope: issuer (legal entity), borrower, guarantor group, restricted group. Note ambiguity.
2. Establish every reporting period (annual, interim, quarterly), fiscal year end, stub and short periods.
3. Record currency, unit, consolidation perimeter and accounting basis; flag a perimeter that differs across sources, since it affects step 3.
4. Map every source to its entities and periods.
5. Scan every source for subsequent events (see the runbook) and flag each with its date below the table.

Output `### T4.2 Entity period key`: `Entity Name` | `Entity Role` | `Fiscal Year End` | `Reporting Currency` | `Reporting Unit` | `Consolidation Perimeter` | `Accounting Basis` | `Available Periods`

## REF_CP-1_03_Normalization.md
Gate: source data for at least one period.
1. Set one basis: one currency (with FX rates and their source), one unit, one perimeter, one accounting basis.
2. Record every adjustment: what, source file, type, before and after, rationale, affected periods.
3. Carry an incompletely normalised figure with a limitation marker. Flag an unresolvable accounting-basis difference; never choose silently.
4. The basis then applies to every later step; switching currency or unit is prohibited.

Output `### T4.3 Normalization register`: `Adjustment Description` | `Source File` | `Adjustment Type` | `Before Value` | `After Value` | `Rationale` | `Affected Periods`

## REF_CP-1_04_IncomeStatementCoverage.md
Gate: always runs; with no income statement data, write the table empty of figures and log every gap.
1. Extract the full income statement for every available period on the step 3 basis.
2. Cover these lines, each `Not supplied: <reason>` where unavailable: Revenue, COGS, Gross Profit, SGA, Other Operating, EBITDA, D&A, EBIT, Interest Expense (total and cash), Interest Income, Other Non-Operating, PBT, Tax (total and cash), Net Income, Exceptionals, SBC. Reconcile the intervening expense block between gross profit and operating profit.
3. Each line carries its source file, period, currency, unit, value and evidence tier in the `Source` and `Basis` cells.
4. EBITDA not stated: derive it from components and say so in `Basis` as calculated; if components are insufficient it is `Not calculable: <reason>`.

Output `### T4.4 Income statement` (statement table). Fixed row: `EBITDA (Reported)`, the issuer's unadjusted EBITDA. Optional fixed row: `EBITDA (Adjusted)`, written only when the issuer states an adjusted figure (name its definition and add-backs in `Basis`). Log both for step 10; never fabricate a missing line.

## REF_CP-1_05_CashFlowStatementCoverage.md
Gate: always runs; with no cash flow statement, write the table empty of figures and log the gaps.
1. Extract the full cash flow statement for every available period.
2. Cover: OCF (before and after working capital), WC Change, Capex (maintenance, growth, total), FCF (levered, unlevered), Dividends, Acquisitions, Disposals, Debt issuance and repayment, Equity issuance and buyback, Cash Taxes Paid. Same source tracing and missing-value rules as step 4.
3. Capex split is rarely disclosed: `Not supplied: <reason>` for sub-categories, carry Total Capex. Cash interest paid (cash flow) can differ from cash interest expense (income statement); keep them apart.

Output `### T4.5 Cash flow statement` (statement table). Fixed rows: `Net Cash from Operating Activities`, `Net Cash from Investing Activities`, `Net Cash from Financing Activities`, `Net Cash Change`, `Opening Cash`, `Closing Cash`, `Cash Interest Paid`. Optional fixed row: `FX Effect on Cash`. `Net Cash Change` excludes nothing: it is operating plus investing plus financing plus the FX effect.

## REF_CP-1_06_BalanceSheetCoverage.md
Gate: always runs; with no balance sheet, write the table empty of figures and log the gaps.
1. Extract the full balance sheet at each reporting date.
2. Cover: Cash & Equivalents, Restricted Cash, ST Investments, Trade Receivables, Inventories, Other CA, Total CA, PP&E (Net), Goodwill, Other Intangibles, Other NCA, Total Assets, ST Debt, Current Portion LTD, Trade Payables, Other CL, Total CL, Senior Secured Debt, Senior Unsecured Debt, Subordinated Debt, Total Debt, Pension and Lease Obligations, Other NCL, Total Liabilities, Shareholders' Equity, Minority Interests, Total Equity.
3. Debt classification by seniority is critical for later analysis: not disclosed is `Not supplied: <reason>`; never estimate. Separate pension and lease obligations from financial debt where possible. A non-debt funding float is flagged here (runbook); also read the subsequent-events note.

Output `### T4.6 Balance sheet` (statement table). Fixed rows: `Total Assets`, `Total Liabilities`, `Total Equity`, `Total Debt`, `Cash & Equivalents`. Optional fixed row: `Temporary Equity`. `Total Debt` is balance-sheet carrying value (step 10).

## REF_CP-1_07_NormalizedFinancialsTable.md
Gate: at least one of steps 4 to 6 produced data.
1. T4.4 to T4.6, on the step 3 basis, are the normalised financials. Write no consolidated copy of them.
2. Cross-check, per period column: Total Assets equals Total Liabilities plus Temporary Equity (when present) plus Total Equity; operating plus investing plus financing plus FX effect (when present) equals Net Cash Change; Opening Cash plus Net Cash Change equals Closing Cash; net income against equity movements. Compare to the precision the figures are printed at. A difference is a gap line with its materiality; correct the wrong figure rather than plug it.

Output: no register of its own.

## REF_CP-1_08_DerivedPeriodConstruction.md
Gate: sub-period data must exist; a missing component makes the derived figure missing. Never estimate.
1. LTM is the latest full year plus the current stub minus the prior-year comparable stub. Construct YTD where applicable. Never replace a directly reported period with a derived one.
2. Every sub-period component must be available (runbook rule); stub periods must be comparable, or the result is Not Comparable.
3. Record component sources, formula, calculation status and limitations.

Output `### T4.8 Constructed period register`: `Metric Name` | `Derived Period Type` | `Full-Year Component` | `Current Stub` | `Prior-Year Stub` | `Derived Value` | `Calculation Status` | `Source Files` | `Limitations`

## REF_CP-1_09_CalculationRegisterKPIBuild.md
Gate: normalised data for at least some periods.
1. Calculate every KPI of the runbook's list whose inputs are available. A missing input makes the KPI `Not calculable: <reason>`; never estimate it.
2. Leverage and cover use these operands: total debt and net debt at balance-sheet carrying value; reported EBITDA as the denominator; cash interest paid as the cover denominator. Where the issuer states an adjusted EBITDA, add the adjusted rows beside them.
3. Give each KPI a full audit trail: formula, numerator and denominator with sources, period, currency, unit, value, calculation status (runbook values), evidence tier, limitations.
4. Show each KPI's trend and an analyst note in the KPI dashboard.

Output `### T4.9 Calculation register`, columns exactly: `Metric Name` | `Formula` | `Numerator Value` | `Numerator Source` | `Denominator Value` | `Denominator Source` | `Period` | `Currency` | `Unit` | `Calculated Value` | `Calculation Status` | `Evidence Quality Tier` | `Limitations`
- One row per period the leverage and interest-cover chart tables state. `Period` is the period column header (`FY2024`). `Numerator Value`, `Denominator Value` and `Calculated Value` are each a plain number or `Not supplied:` or `Not calculable:` with a reason; write no annotation inside them. `Currency` and `Unit` are never empty; `Unit` is the operands' unit.
- Fixed `Metric Name` values (other metrics keep free names): `Total debt / EBITDA`, `Net debt / EBITDA`, `EBITDA / cash interest` (reported EBITDA), and, only when the issuer states an adjusted EBITDA, `Total debt / adjusted EBITDA`, `Net debt / adjusted EBITDA`, `Adjusted EBITDA / cash interest`. For these six rows `Unit` is `US$m`, the Net debt table's unit. The ratio is `Calculated Value`, and the leverage and interest-cover chart figures are those values for the same period.

Output `### T4.10 KPI dashboard`: `KPI Category` | `Metric Name` | one column per period | `Trend Direction` | `Analyst Note`. It also keeps the KPIs T4.9 does not calculate (issuer-reported margins, segment and operating KPIs).

## REF_CP-1_10_DefinitionConflictRegister.md
Gate: always runs; with no conflict, confirm alignment in one sentence (no conflicts across N metrics and M sources).
1. Review every metric: issuer definition against this method's; sources disagreeing; a definition changed across periods.
2. Log each conflict: metric, this method's definition, issuer definition, source, periods, materiality (quantified), what it affects, resolution.
3. Common areas: EBITDA (add-backs, management against audited; the most common source in leveraged finance), debt (leases, pensions, drawn facilities), FCF (levered against unlevered), capex (capitalised items, maintenance against growth), net debt (restricted cash, short-term investments).
4. Multi-figure events are one row with all figures (runbook).

Debt basis (binding): debt totals use carrying values. Principal and commitment are kept separately and are not substitutes for carrying value. A lease liability is not in total debt. The carrying-against-principal difference is always one row here, with both figures and their locators.

Output `### T4.11 Definition conflict register`: `Metric Name` | `Canonical Definition` | `Issuer-Reported Definition` | `Source of Conflict` | `Periods Affected` | `Materiality` | `Modules Affected` | `Resolution / Recommendation`

## REF_CP-1_11_EvidenceRiskCreditAnalysis.md
Gate: at least one KPI from step 9; with none, write a data-quality analysis only.
1. Apply evidence, risk mechanic, credit implication to every material finding, in sentences.
2. Cover: leverage trajectory and drivers; coverage trends; cash-flow quality (conversion, working capital, capex intensity); liquidity adequacy (cash and undrawn against near-term obligations); data-quality risks; definition risks; the most material gaps and their credit consequence.
3. Synthesis only: no new data and no new figure; every statement is issuer-specific and traces to an earlier table. Where present, write the stories the runbook names: non-debt funding float, subsequent events (date, effect, why excluded from period figures), multi-figure events (which figure serves which purpose).

Output: the analysis inside `## Findings`, by analytical dimension.

## REF_CP-1_12_CoverageGateDownstreamReadiness.md
Gate: always runs; the final quality gate.
1. Consolidate every gap from every prior step as a plain-sentence line under `## Gaps`: what is missing or unreconciled, for which line item or metric and period, what it restricts, its severity (High, Medium, Low) and the action that would close it. Cumulative; no omissions.
2. Judge readiness of the figures for the requested use: which conclusions and calculations the evidence supports and which stay restricted. Group repeated consequences under their underlying issue.

Output `### T4.13 Readiness`: `Requested Use` | `Readiness Status` (Ready, Ready with Limitations, Not Ready) | `Gaps or Limitations` | `Recommended Actions`

## Anti-patterns (REF_CP-1_AntiPatterns.md)
- Silent reconciliation. "EBITDA was EUR 120m in FY2023" when source A says 120 and source B says 115. Right: "EBITDA (reported) was EUR 120m per the audited statements (AR 2023, p. 45); management-adjusted EBITDA was EUR 115m per the lender presentation (p. 12); the conflict is logged and the audited figure is used."
- Data fabrication. "Capex was approximately EUR 30m based on industry norms" when no source gives it. Right: "Capex: Not supplied: not disclosed in the provided sources", with a gap line and the consequence for free cash flow.
- Exact figures at source precision; no rounding without disclosure; institutional creditor tone; no filler.

## Discipline (REF_CP-1_Discipline.md)
- An assertion cites a source file and locator. Conflicting definitions are logged, never reconciled silently; a definition change from this method's to the issuer's is flagged and logged, never silently adopted.
- Currency or unit switching after step 3 is prohibited.
- Every figure is one of four kinds, labelled: source data (citation), normalised ([Normalized] with its register reference), calculated ([Calculated] with formula and register reference), analyst judgement ([Analyst Judgement]). Decompose mixed content.
- A draft or incomplete source: state the limitation and its consequence. A figure derived by calculation cites its inputs and formula.
