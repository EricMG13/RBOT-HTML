---
issuer_id: tdg
issuer_name: TransDigm Group Incorporated
module_id: CP-2E
analysis_date: 2024-09-30
reporting_period: FY2024
reporting_currency: USD
pathway: credit_snapshot
run_id: tdg-2024-09-30-credit_snapshot-copilot-sol-medium
method_version: deploy-v-r14
artifact: tdg_CP-2E_20240930.md
module_status: Ready with Limitations
committee_status: Requires More Work
macro_risk_level: Moderate
esg_phase: Completed with Limitations
---

## Request
TransDigm Group Incorporated, as of 2024-09-30; pathway: credit_snapshot. Assess rates, hedge protection and expiry risk, FX mismatches, inflation and commodity transmission, and credit-material environmental, social and transition exposures on the consolidated FY2024 basis, keeping subsequent transactions separate.

## Sources

| Source | Document | Document date | sha256 | Use |
|---|---|---|---|---|
| TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl | Annual report on Form 10-K for the year ended September 30, 2024 | not stated | d75c469fdb1966dd895c0f6faa6d5179b380d3ed95aa00aca99aa258059edab6 | Debt and hedge terms, issuer sensitivities, FX forwards, inflation recovery limits, environmental liabilities, physical and transition risks, labor and product liability. Retrospective annual evidence; publication date not established. |

| Supplied analysis | Module | Exact sha256 | Use |
|---|---|---|---|
| tdg_CP-0_20240930.md | Source readiness (CP-0) | 7ae19c7264917275366ee8792370fe0e20e781c357f538ce585e474714d2f737 | Accepted identity, evidence authority, reporting scope and date restrictions. |
| Financial foundation | CP-1 | 323996fab6d5756c1b4197d605372ce918ca615b327f3aa26cdd1fd299045a84 | Carrying debt and gross-principal reconciliation; FY2024 FCF, cash interest and separately dated October transaction-only balances. |
| tdg_CP-1A_20240930.md | Business & governance (CP-1A) | 229568a632d3a1ea81cc567c68745b3eefeb4f7fa9006442c8f8c475f3ab4113 | Business transmission, financial-policy context, instrument maturities and governance boundary. |
| tdg_CP-2_20240930.md | Fundamental credit (CP-2) | 8dfc266a2c192b720696dd4d538496eb10a76e0ff339dd82cf9e581970ffe9b4 | Operating downside, cash-retention implications and fiscal-versus-calendar maturity clarification. |

No external sources were used. All supplied analyses identify the same issuer, September measurement date and selected pathway. Other issuer documents were not needed for the targeted annual analysis.

## Findings

### Bottom line
TransDigm has Moderate macro and hedging sensitivity: disclosed hedges temper rate volatility, but substantial residual floating debt and limited contractual inflation recovery mean creditors should not treat historical margins or reported fixed-rate allocation as permanent cash-flow protection.
Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–178

At year-end, USD 9,189 million of identified floating borrowings was protected by USD 3,400 million of active swaps and a cap, leaving USD 5,789 million exposed. A static 100 bp rise adds USD 57.89 million of annual borrowing cash interest before tax and cash-income offsets; the issuer separately reports approximately USD 30 million, which cannot be reconciled from disclosed assumptions. Replacement collars leave a protection step-down in March 2025. Product liability is the priority environmental or social event-risk channel, not a demonstrated current funding impairment.
Basis: calculation R01; calculation R02; calculation R03; calculation R08; calculation R13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73

### Key findings

- **Rates are the largest measurable residual macro exposure.** Active protection is linked to floating credit-agreement borrowings, with disclosed strikes, dates and accounting effectiveness. It does not cover all floating debt or credit spreads. The calculated borrowing-interest shock reduces cash available for debt repayment even without an operating decline; the annual report's smaller sensitivity must remain a separate issuer case.
Basis: calculation R01; calculation R02; calculation R03; calculation R08; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177
- **The first hedge cliff is only partly replaced.** USD 2,000 million of swaps expires on March 31, 2025 against USD 1,100 million of starting collars, reducing protected notional by USD 900 million. Collars limit upside only above their ceilings and impose payments below their floors; they are not fixed-rate swaps throughout the rate range.
Basis: calculation R13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–176
- **Inflation protection is demonstrated commercially, not generally contractual.** Gross margin reached 58.8% in FY2024 despite inflation, but most contracts do not permit recovery of higher raw-material, tax or labor costs. Lower volume could remove overhead absorption while locked selling prices delay recovery, reducing operating cash alongside persistent interest expense.
Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 46
- **FX is less alarming on the issuer's historical test than the currency map alone suggests.** Management says a 10% exchange-rate change would not materially affect FY2024 net income. USD 120 million of forwards addresses selected transaction flows, not demonstrated group-wide natural matching or translation protection.
Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 178
- **Environmental and social risk is primarily contingent, not an evidenced financing premium.** Environmental remediation accruals total USD 41 million; compliance did not materially affect FY2024 cash flow. Product failure could nevertheless generate uninsured claims and disrupt earnings. No sustainability-linked spread benefit, penalty or protection is established.
Basis: calculation R14; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161

### Contrary evidence and what would change the view
The strongest contrary evidence is effective hedge accounting with specific contractual terms, improved margins through inflation, and the issuer's historically immaterial FX test. Together with positive cash generation, these argue against calling macro exposure an immediate liquidity crisis. They do not prove protection after expiries, repricing during a volume decline, or the absence of uninsured operational events. Full replacement of expiring protection and sustained cash margins under weaker production would support a lower risk view; failure to replace hedges alongside cost inflation and weaker aftermarket demand would support a higher one. A documented reconciliation of the interest sensitivities would determine which measure is appropriate for a net-interest forecast.
Basis: Financial foundation (CP-1); Fundamental credit (CP-2); TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 46–46; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 176–177

### Limitations

- **A single net-interest shock cannot be adopted.** The issuer's sensitivity assumptions do not explain its difference from the disclosed debt-and-hedge reconstruction. The calculated case is therefore limited to annual borrowing interest at constant balances, not a forecast of total net interest or cash income.
Basis: calculation R08; calculation R12; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176
- **Aggregate protection cannot be allocated confidently to each loan tranche.** The annual report links hedges to the credit agreement but does not allocate them among repriced loans; printed swap all-in rates retain an older margin. This analysis relies on disclosed base-rate protection and does not adopt those all-in rates as current loan coupons.
Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 152–153; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–176
- **Non-rate cash volatility cannot be sized.** Currency-matched revenue, costs and cash, FX strikes, input-cost quantities and repricing lags are not established. The FX and inflation conclusions remain directional, and the historical net-income test cannot be converted into a cash-flow stress.
Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 178
- **Environmental and social event losses cannot be translated into liquidity or recovery amounts.** Facility-level hazard values, insurance limits, remediation payment timing and transition expenditure are not disclosed in the evidence used. No adverse funding-access premium, quantified loss severity or sustainability-linked creditor benefit is inferred from that silence.
Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161

### Macro and hedging view
The rate risk classification is Moderate rather than Low because the hedge schedule leaves substantial identified floating exposure and replacement protection is conditional on rate bands. It is not High on the evidence available because the borrowing-interest shock alone leaves positive historical free cash flow, while fixed coupons and existing hedges limit near-term transmission. The initiating downside is a rate increase coinciding with expiring protection; borrowing interest rises immediately on uncovered balances, while cost inflation and weaker production reduce cash generation. Lower retained cash then increases reliance on financing ahead of term maturities. Monitor hedge replacement at the first expiry, actual cash interest, and gross-margin performance together, not hedge notional in isolation.
Basis: calculation R08; calculation R10; calculation R13; Financial foundation (CP-1); Fundamental credit (CP-2); TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–176

### Credit implication
Product liability is the highest-priority environmental or social event-risk driver for committee debate. TransDigm manufactures safety-relevant aircraft components and explicitly warns that insurance may be denied or inadequate after a failure. A major incident could interrupt revenue and require defense or settlement cash, weakening FCF and liquidity before refinancing becomes difficult; there is no supported current default or recovery-loss estimate. Environmental remediation is a quantified balance-sheet obligation, but its cash timing is not established, and management reports no material historical compliance burden. Climate policy and physical hazards remain Watch items tied to air-travel restrictions, asset damage or mandated expenditure. Monitoring should escalate upon a reported serious product incident, coverage dispute, material remediation revision or facility interruption; no future incident date is assumed. The central debate is whether insurance and operating continuity contain product-failure cash demands, not whether an environmental label improves creditor rights.
Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161

### Events: Hedges

| Event date | Date precision | Published | Event | Status | Source | Credit relevance |
|---|---|---|---|---|---|---|
| 2023-03-31 | day | — | Swaps of USD 500 million, USD 1,500 million and USD 700 million and cap of USD 700 million become effective | Historical — Effective Date | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 | USD 3,400 million active at the September 2024 anchor; base rates 3.00%, 3.10%, 1.30% and cap strike 1.25%, respectively |
| 2025-03-31 | day | — | USD 500 million and USD 1,500 million swaps mature; USD 1,100 million collar starts | Scheduled — Maturity Date; Effective Date | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 | USD 900 million step-down in protected notional; new collar floor 2.00%, cap 3.50% |
| 2025-09-30 | day | — | USD 700 million swap and USD 700 million cap mature; USD 500 million and USD 1,338 million collars start | Scheduled — Maturity Date; Effective Date | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 | New collars have floor/cap 2.00%/3.50% and 2.50%/4.50%; total scheduled collar notional USD 2,938 million |
| 2026-09-30 | day | — | USD 1,100 million and USD 500 million collars mature; USD 1,550 million collar starts | Scheduled — Maturity Date; Effective Date | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 | Starting floor/cap 2.50%/4.50%; remaining scheduled notional USD 2,888 million |
| 2027-09-30 | day | — | USD 1,338 million and USD 1,550 million collars mature | Scheduled — Maturity Date | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 | Last dated protection in the disclosed schedule ends before remaining term-loan maturities; no assumed renewal |

### Confidence inputs

| Input | Value |
|---|---|
| Directly Sourced | 8 |
| Calculated | 4 |
| Assumption-Based | 0 |
| Analyst Inference | 3 |
| Weak Lineage | 0 |
| Untraced | 0 |
| Conflicting | 1 |
| Insufficient Information | 4 |
| Fields present | 109 |
| Fields total | 113 |
| Source gate | partial |
| CRITICAL | 0 |
| MATERIAL | 4 |
| MINOR | 0 |

### Analytical appendix — complete canonical registers

### T2F.1 — Macro source gate

| source_document_id | source_document_name | source_quality | period | entity_covered | data_supplied | limitation | downstream_use | Source |
|---|---|---|---|---|---|---|---|---|
| S1 | FY2024 Form 10-K | Primary filing; audited note disclosures; management sensitivities separately attributed | September 30, 2024 instant; FY2024 flows; forward hedge dates | TransDigm Group and consolidated subsidiaries | Debt split, strikes, hedge dates, FX terms, cost recovery limits and operational risks | No full currency-matched operating base, FX trade confirmations or input sensitivities | Rates, FX & hedging; Downside; Forward credit model; Committee decision | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–178 |

| Input | Adopted value / definition | Decision boundary | Source |
|---|---|---|---|
| Gate | Ready with Limitations; partial | Debt split and hedge terms permit rate analysis; absent operating detail restricts only non-rate quantification | Source readiness (CP-0) |
| Identity | tdg; TransDigm Group; 2024-09-30; FY2024; USD consolidated; run tdg-2024-09-30-credit_snapshot-copilot-sol-medium | Industrial aerospace group; no financing-subsidiary matched-funding exclusion supported | Financial foundation (CP-1); Business & governance (CP-1A); Fundamental credit (CP-2) |
| Imported annual cash measures | FCF USD 1,880 million; cash interest paid net USD 1,158 million; adjusted EBITDA USD 4,173 million | FCF is CFO less capex before acquisitions/distributions; cash interest net is not gross borrowing interest | Financial foundation (CP-1) |
| Imported balance and subsequent comparison | Carrying debt USD 24,880 million; gross principal USD 25,068 million; year-end cash USD 6,261 million beside October 18, 2024 transaction-only pro forma cash USD 2,075.50 million | October 16 draw and October 18 payment retained separately; static, not actual closing cash; no new October sensitivity calculated | Financial foundation (CP-1) |
| Maturity correction | November 15, 2027 legal maturity falls in FY2028 | Specific fiscal/calendar issue resolved by Fundamental credit; no independent legal opinion adopted | Fundamental credit (CP-2) |
| Optional inputs | Separate liquidity, hedge trade confirmations, market curves and agency reports not supplied | No curve-based forecast, valuation, covenant headroom or instrument preference | Source readiness (CP-0) |

### T2F.2 — Debt and rate exposure

Amounts below are gross contractual principal for rate exposure unless explicitly identified as carrying values. Balance-sheet debt remains the carrying-value measure; the reconciliation is retained separately.

| Debt Instrument | Amount | Fixed / Floating | Base Rate | Margin / Coupon | Currency | Maturity | Hedge Status | Source Trace | Credit Implication | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| Term loan I | USD 1,871 million | Floating-rate debt | Term SOFR or alternate base rate; no adjusted SOFR floor | SOFR +2.75% | USD | 2028-08-24 | Aggregate credit-agreement protection; tranche allocation not supplied | S1, Note 10 | Base-rate exposure survives on uncovered balances; spread not hedged | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 152–153 |
| Term loan J | USD 3,632 million | Floating-rate debt | Term SOFR or alternate base rate; no adjusted SOFR floor | SOFR +2.50% | USD | 2031-02-28 | Aggregate partial protection | S1, Note 10 | Long maturity exceeds last disclosed hedge date | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 152–153 |
| Term loan K | USD 1,699 million | Floating-rate debt | Term SOFR or alternate base rate; no adjusted SOFR floor | SOFR +2.75% | USD | 2030-03-22 | Aggregate partial protection | S1, Note 10 | Refinancing runway does not remove rate volatility | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 152–153 |
| Term loan L | USD 1,500 million | Floating-rate debt | Term SOFR or alternate base rate; no adjusted SOFR floor | SOFR +2.50% | USD | 2032-01-19 | Aggregate partial protection | S1, Note 10 | Recap borrowing adds floating exposure without earnings | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 152–153 |
| Receivables securitization | USD 487 million | Floating-rate debt | Three-month Term SOFR | +1.45% | USD | 2025-07-11 | No specific hedge linkage disclosed | S1, Item 7A; Business & governance maturity | Renewal risk precedes term-loan maturities; included in gross floating exposure | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73; Business & governance (CP-1A) |
| Secured notes due 2028 | USD 2,100 million | Fixed-rate debt | Fixed coupon | 6.75% | USD | 2028 | Contractual fixed rate | S1, debt table | No immediate base-rate cash repricing; future refinancing rate remains exposed | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| Secured notes due 2029 | USD 2,750 million | Fixed-rate debt | Fixed coupon | 6.375% | USD | 2029 | Contractual fixed rate | S1, debt table | Fixed debt service until refinancing | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| Secured notes due 2030 | USD 1,450 million | Fixed-rate debt | Fixed coupon | 6.875% | USD | 2030 | Contractual fixed rate | S1, debt table | Fixed debt service until refinancing | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| Secured notes due 2031 | USD 1,000 million | Fixed-rate debt | Fixed coupon | 7.125% | USD | 2031 | Contractual fixed rate | S1, debt table | Fixed debt service until refinancing | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| Secured notes due 2032 | USD 2,200 million | Fixed-rate debt | Fixed coupon | 6.625% | USD | 2032 | Contractual fixed rate | S1, debt table | Fixed debt service until refinancing | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| Secured notes due 2033 | USD 1,500 million | Fixed-rate debt | Fixed coupon | 6.00% | USD | 2033 | Contractual fixed rate | S1, debt table | Recap financing increases fixed claims but not immediate base-rate sensitivity | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| Subordinated notes due 2027 | USD 2,650 million | Fixed-rate debt | Fixed coupon | 5.50% | USD | 2027-11-15 | Contractual fixed rate | S1, debt table; Financial foundation maturity | Coupon fixed; refinancing at maturity not hedged by current swaps | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145; Financial foundation (CP-1) |
| Subordinated notes due 2029, lower coupon | USD 1,200 million | Fixed-rate debt | Fixed coupon | 4.625% | USD | 2029-01-15 | Contractual fixed rate | S1, debt table; Financial foundation maturity | Coupon fixed; future refinancing spreads remain exposed | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145; Financial foundation (CP-1) |
| Subordinated notes due 2029, higher coupon | USD 750 million | Fixed-rate debt | Fixed coupon | 4.875% | USD | 2029 | Contractual fixed rate | S1, debt table | Coupon fixed; future refinancing spreads remain exposed | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| Government refundable advances | USD 17 million | Classification not supplied | Repayment tied to specified commercial aviation revenue growth | Interest terms not supplied | Reporting USD; contractual currency not supplied | Repayment schedule not supplied | Not established | S1, Note 10 | Not added to floating sensitivity without disclosed rate linkage | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 152 |
| Finance leases | USD 262 million | Classification not supplied | Rate-reset terms not supplied | Not supplied | Reporting USD; lease currency split not supplied | Individual maturities not extracted | Not established | S1, Note 10 | Retained in debt denominator, not assumed floating | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 145–145 |
| Revolving facilities | USD 0 million drawn; USD 843 million reported availability | Floating-rate debt if drawn | SOFR basis | +2.25%; unused fee 0.50% | USD | 2029-02 | No hedge assigned to undrawn amount | S1, Note 10 | No current drawn exposure added; future borrowing raises sensitivity | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 152; Financial foundation (CP-1) |

### T2F.3 — Hedging register

| Hedge Type | Notional | Instrument Covered | Rate / Strike | Maturity | Coverage Status | Source Trace | Limitation | Source |
|---|---|---|---|---|---|---|---|---|
| Interest-rate swap | USD 500 million | Floating Credit Agreement borrowings | Base fixed 3.00%; printed all-in 6.25% includes legacy 3.25% margin | Effective 2023-03-31; maturity 2025-03-31 | Effective where supported | S1, Notes 19 and 10 | Tranche allocation absent; use base protection, not printed all-in as current coupon | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177 |
| Interest-rate swap | USD 1,500 million | Floating Credit Agreement borrowings | Base fixed 3.10%; printed all-in 6.35% includes legacy 3.25% margin | Effective 2023-03-31; maturity 2025-03-31 | Effective where supported | S1, Note 19 | Same all-in margin qualification; future spread changes unprotected | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177 |
| Interest-rate swap | USD 700 million | Floating Credit Agreement borrowings | Base fixed 1.30%; printed all-in 4.55% includes legacy 3.25% margin | Effective 2023-03-31; maturity 2025-09-30 | Effective where supported | S1, Note 19 | Not protection through term-debt maturity | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177 |
| Interest-rate cap | USD 700 million | Floating Credit Agreement borrowings | Three-month Term SOFR above 1.25% | Effective 2023-03-31; maturity 2025-09-30 | Effective where supported | S1, Note 19 | Protects above strike, not a fixed coupon below it; excludes premium amortization from marginal shock | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177 |
| Collar | USD 1,100 million | Floating Credit Agreement borrowings | Three-month SOFR floor 2.00%; ceiling 3.50% | Effective 2025-03-31; maturity 2026-09-30 | Partial; forward starting | S1, Note 19 | No September 2024 active protection; rates float inside band | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Collar | USD 500 million | Floating Credit Agreement borrowings | Three-month SOFR floor 2.00%; ceiling 3.50% | Effective 2025-09-30; maturity 2026-09-30 | Partial; forward starting | S1, Note 19 | Do not add to active year-end protection | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Collar | USD 1,338 million | Floating Credit Agreement borrowings | Three-month SOFR floor 2.50%; ceiling 4.50% | Effective 2025-09-30; maturity 2027-09-30 | Partial; forward starting | S1, Note 19 | Future rates and balances needed for cash-flow forecast | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Collar | USD 1,550 million | Floating Credit Agreement borrowings | Three-month SOFR floor 2.50%; ceiling 4.50% | Effective 2026-09-30; maturity 2027-09-30 | Partial; forward starting | S1, Note 19 | Upside protection does not eliminate downside floor payments | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Fixed-rate debt | USD 15,600 million principal | Nine note series in debt register | Individual fixed coupons retained above | 2027 through 2033 | Effective where supported | Calculation R06; S1, Note 10 | Contractual fixed funding, not derivative notional; refinancing cost remains variable | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| FX forward | USD 120 million equivalent | Selected third-party forecast sales or transactions; sell USD for CAD and EUR | Trade-level strikes not supplied | Maximum duration twelve months at 2024-09-30; individual expiry dates not supplied | Terms insufficient for independent coverage sizing | S1, Note 19 | USD equivalents at trade-date spot; no group-wide effectiveness or currency-allocation ratio inferred | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 178 |
| Natural hedge; commodity, energy or fuel hedge | Not supplied: no matched quantities or documented instruments established | Operating flows | Not supplied: contractual matching and strikes not established | Not supplied: no dated hedge schedule identified | Insufficient Information | Targeted operating and derivative disclosures | Silence is not a zero exposure or unhedged-all conclusion | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–178 |

### T2F.4 — Floating exposure and debt denominator

| Metric | Amount | Formula / Source | Status | Credit Implication | Source Trace | Source |
|---|---|---|---|---|---|---|
| Total debt, carrying basis | USD 24,880 million | USD 24,394 million current/non-current debt plus USD 486 million short-term securitization; R04 | Calculated; agrees Financial foundation | Primary debt denominator net of issuance costs and discount | S1, Notes 9–10 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 144–145 |
| Gross principal reference | USD 25,068 million | Financial foundation; above carrying by USD 188 million, R05 | Reported inputs; calculated bridge | Principal rate exposure is not carrying debt; do not overwrite inherited principal leverage | Financial foundation C01/C37 | Financial foundation (CP-1) |
| Fixed-coupon notes | USD 15,600 million | R06; nine note series | Calculated | No immediate coupon repricing | S1, debt table | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| Gross floating-rate debt | USD 9,189 million | Term loans USD 8,702 million + securitization USD 487 million; R01 | Calculated | Largest identified shock-sensitive funding base | S1, Item 7A | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73 |
| Hedged floating-rate debt | USD 3,400 million | Active swaps USD 2,700 million and cap USD 700 million; R02 | Calculated; current active coverage | Credit-agreement linkage, base rates and periods support protection; future collars excluded | S1, Note 19 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177 |
| Unhedged floating-rate debt | USD 5,789 million | R01 minus R02; R03 | Calculated; identified disclosed exposure | Annual borrowing cash interest moves with base rate on this residual | S1, Item 7A and Note 19 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Unhedged debt percentage | 23.267684887459807073954983922829581994% | R03 / carrying debt R04; fraction 0.23267684887459807073954983922829581994; R07 | Calculated | Explicit carrying denominator; not the complement of issuer's gross fixed-rate claim | Calculation R07 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 144–145; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Other rate classification | USD 17 million advances; USD 262 million leases | Source debt table; terms do not establish floating reset | Insufficient Information for rate classification | Included in total debt, not silently assigned to floating or fixed | S1, Note 10 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 145–152 |
| Issuer rate allocation | Approximately 77% gross debt fixed; objective at least 75% fixed and 25% variable | Issuer Item 7A characterization | Reported; methodology not reconciled | Do not substitute percentage target for instrument-based exposure | S1, Item 7A | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73 |

### T2F.5 — Sensitivity and FCF transmission

| Sensitivity | Formula | Source Inputs | Estimated Cash Impact | FCF / Liquidity Implication | Status | Source Trace | Source |
|---|---|---|---|---|---|---|---|
| +100 bp static annual borrowing-interest shock | USD 5,789 million × 1.00%; evaluated as divide by 100 | R03 residual; active swaps/cap; unchanged spreads and debt | +USD 57.89 million annual cash interest | Mechanical FCF change −USD 57.89 million before tax and cash-income offsets | Calculated; not net-interest forecast | R08 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177 |
| Historical FCF comparison | USD 1,880 million − USD 57.89 million | Financial foundation historical FCF and R08 | USD 1,822.11 million illustrative residual FCF; interest burden 3.0792553191489361702127659574468085106% of historical FCF | Positive historical buffer remains; not stressed liquidity, current cash, or a forecast | Calculated mechanical comparison | R09–R10 | Financial foundation (CP-1); TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Issuer +one percentage point rate test | Company methodology not supplied | Outstanding term loans and securitization at 2024-09-30 | Approximately +USD 30 million annual interest costs | Smaller issuer case retained separately; not substituted for reconstructed borrowing sensitivity | Reported; reconciliation unresolved | S1, Item 7A; R12 difference USD 27.89 million | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73 |
| Gross floating comparator before hedges | USD 9,189 million ×1.00% | Identified floating borrowings only | +USD 91.89 million annual interest before hedge receipts | Shows protection contribution without claiming full fixed funding | Calculated comparator, not adopted net case | R11 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73 |
| FX / commodity / inflation stress | Not calculable: matched exposure bases, shocks and repricing timing absent | No user shock supplied; issuer FX test preserved in FX register | Not calculable: no supported cash-flow exposure base | No invented conversion of geography, net income or gross cost into cash sensitivity | Insufficient Information | G2–G3 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74 |

### T2F.6 — FX mismatch register

| Exposure Type | Revenue Currency / Region | Cost Currency / Region | Debt / EBITDA / Cash / Covenant Currency | Natural Hedge? | Evidence | Risk Mechanic | Credit Implication | Source Trace | Limitation | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| Translation exposure | Certain foreign subsidiaries' sales primarily affected by GBP and EUR | Local cost currency quantities not supplied | Statements in USD; foreign EBITDA/cash currency breakdown not supplied | Insufficient Information | USD reporting translates foreign operations and asset balances | USD movement changes reported sales, earnings and carrying assets without equivalent immediate cash loss | Separate reported leverage translation from transaction cash exposure | S1, Item 7A | Geography alone not used to infer FX mismatch or natural matching | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74 |
| Transaction exposure | Third-party sales and purchases in foreign currencies; forwards sell USD for CAD/EUR | Purchases identified qualitatively; quantities not supplied | Main loans and note debt USD; EBITDA and covenant currency reconciliation not supplied | Insufficient Information | USD 120 million forwards; maximum twelve-month duration; FY2024 USD 4 million settlement losses in net sales | Forward settlements offset selected forecast flows; strikes and currency shares determine residual | No group-wide coverage percentage or dollar shock assigned | S1, Note 19 | Notional is neither fair value nor proven full cash protection | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 178 |
| Historical issuer sensitivity | Company-wide revenue currency base not supplied | Company-wide cost currency base not supplied | FY2024 net-income test, not covenant or liquidity calculation | Insufficient Information | Issuer says 10% FX change would not materially affect net income; USD 20 million foreign currency losses in cost of sales in FY2024 versus USD 14 million in FY2023 | Recorded transaction losses and translation effects have different accounting paths | Historical test tempers alarm but cannot size FCF effect or prove no residual mismatch | S1, Item 7A and operating results | Materiality threshold, currency correlations and cash tax effects not supplied | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 46; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 74 |
| Covenant mismatch / cash repatriation | Not supplied: matched sales currency | Not supplied: matched expenditure currency | Debt reporting primarily USD; entity cash and contractual covenant conversion rules not supplied | Insufficient Information | Consolidated reporting does not establish cash transferability | Currency translation or inaccessible cash may differ from borrower debt service | No covenant FX headroom or repatriation benefit credited | Financial foundation perimeter | Obtain currency-by-entity and contractual conversion terms | Financial foundation (CP-1) |

### T2F.7 — Commodity and inflation register

| Input / Commodity / Inflation Driver | Cost Exposure | Pass-Through Mechanism | Evidence | Risk Mechanic | Credit Implication | Source Trace | Limitation | Source |
|---|---|---|---|---|---|---|---|---|
| Raw-material exposure; procurement | Contract manufacturing cost quantities not supplied | Generally no contractual recovery; commercial repricing not quantified | Most contracts disallow raw-material, tax and labor cost recovery; some multi-year fixed prices | Higher input cost enters margin before selling prices adjust | FCF durability weaker than proprietary position alone implies | S1, contract risk | Commodity basket, hedges, cost share and repricing lag not supplied | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18 |
| Labour / wage inflation | Union representation approximately 17% of full-time and part-time employees; wage cost not supplied | No general recovery right established | Contract restrictions and bargaining agreements expiring at various dates through January 2029 | Wage increases or stoppages raise unit costs and interrupt shipments | Margin squeeze or delayed collections can compete with cash interest | S1, human capital and contract risk | No future wage settlement or strike assumed | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18 |
| Freight / energy / rent inflation | Freight inflation noted in operating discussion through Fundamental credit; energy/rent cost split not supplied | Indexation or surcharge not established | Gross margin improved through inflation; volume absorption part of benefit | Transportation or facility cost rises may precede recovery; lower output dilutes absorption | Directional cash pressure; no additive cost shock invented | S1, operating results | No individual energy, freight or rent cash sensitivity | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 46; Fundamental credit (CP-2) |
| Historical pricing/productivity mitigant | Gross margin 58.8% FY2024 versus 58.3% FY2023 | Demonstrated commercial operating performance; not automatic indexation | Management attributes improvement to strategy and fixed overhead spread over greater production | Pricing/productivity and volume can offset inflation; downturn reverses absorption | Mitigates current pressure but does not prove downside pass-through | S1, operating results | Price-volume-cost contributions and demand elasticity not separated | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 46 |

### T2F.8 — Macro sensitivity summary

| Macro Driver | Evidence | Risk Mechanic | FCF / Liquidity Impact | Refinancing / RV Implication | Monitoring Trigger | Source Trace | Source |
|---|---|---|---|---|---|---|---|
| Base-rate exposure | USD 5,789 million identified residual floating debt | Base-rate increase raises borrowing interest; cash income and tax not modeled | +USD 57.89 million interest for static 100 bp rise | Less retained funding; no spread valuation or security preference established | Compare reported cash interest with hedge receipts and balances each reporting period | R03/R08; issuer alternative retained | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–73; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Hedge cliff | March 2025 swap expiry exceeds new collar notional | Protection shrinks and becomes band-dependent | Greater future volatility; not a quantified future rate forecast | Greater reliance on cash generation before long-term refinancing | 2025-03-31 replacement; then later schedule dates in event table | R13 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| FX | GBP/EUR translation and selected CAD/EUR transaction hedges | USD changes affect operating translation and settlement cash differently | Historical issuer net-income test immaterial; cash sensitivity not calculable | No supported covenant FX breach or FX-driven financing premium | Forward replacement, settlement losses and currency-matched cash disclosures | FX register | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 178 |
| Inflation and demand interaction | Most contracts lack cost recovery; volume helped FY2024 margins | Wage/material increase and declining output compress unit margins simultaneously | Lower EBITDA and cash before persistent interest | Less refinancing cushion; no inferred covenant headroom | Gross-margin decline with lower production or failed price recovery | Contract and operating disclosures | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 46 |
| Counterparty/default linkage | Credit Agreement default can trigger derivative default and accelerated settlement | Financial stress can terminate protection or require early settlement | Payment direction depends on close-out fair value; no gross notional liability assumed | Can intensify a liquidity event; no claim on recoveries quantified | Counterparty failure, credit-agreement default or early termination notice | S1, Note 19 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 174–175 |

Macro Risk Level: Moderate. Rates, FX & hedging analysis completed with limitations; the single net-interest forecast, non-rate numerical stress and any valuation or covenant-capacity conclusion remain restricted.
Basis: calculation R08; calculation R10; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–178

### T2F.9 — Macro gaps ledger

| Gap | Missing Data | Why It Matters | Impact on Output | Required Follow-Up | Downstream Module Affected |
|---|---|---|---|---|---|
| G1 — Interest sensitivity reconciliation | Assumptions behind approximately USD 30 million issuer shock and approximately 77% gross fixed allocation; hedge-to-tranche schedule and current all-in rates | Different reported and reconstructed sensitivities cannot support one net-interest forecast | Keep issuer and calculated cases distinct; no adoption of issuer fixed share as independent coverage calculation | Obtain issuer treasury bridge, dated hedge allocations, reset conventions and cash-income assumptions | Forward credit model; Committee decision |
| G2 — FX coverage and matching | Revenue/cost/cash/EBITDA by currency and entity; FX strikes and individual maturities; covenant conversion and repatriation terms | Determines transaction residual and cash accessibility, not just translation | Dollar FX shock, natural hedge and covenant currency mismatch not calculable | Obtain treasury currency ladder, trade confirmations and contractual conversion provisions | Forward credit model; Downside; Legal & covenants |
| G3 — Cost recovery | Commodity quantities, energy/freight/rent/wage cost shares, repricing lags, indexation and demand elasticity | Required to size margin and cash effects without using total costs as a proxy | Inflation/commodity stress directional only; no assumed automatic pass-through | Obtain procurement cost bridge and customer pricing clauses | Forward credit model; Downside |
| G4 — Other debt rate terms | Lease reset and advance interest terms and contractual currencies | Could add unmeasured sensitivity outside identified floating loans | Retain in total debt but do not assume fixed or floating | Obtain lease rate schedules and advance agreements | Forward credit model |
| G5 — Future rate profile | Curves, future balances, renewal trades and forecast cash balances | Collars are nonlinear and start after the anchor | Notional path is not a future cash-interest forecast; no October shock inferred | Obtain dated treasury projection and authorized scenario assumptions | Forward credit model |

### T2G.1 — ESG source inventory

| Source | Reliability (audited/assured vs self-reported) | Greenwashing Flag | Module Status |
|---|---|---|---|
| TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 13–13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 25–25; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 31–31; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161 | Remediation accruals are financial-note disclosures within audited statements; climate descriptions and emissions target are self-reported and no separate assurance supplied | No affirmative misleading-claim evidence established; low-emissions description not treated as verified emissions inventory or creditor protection | Completed with Limitations; partial environmental, transition and operational disclosure; no sustainability-linked terms established |

### T2G.2 — Environmental and transition register

| Exposure | Source/Date | Transmission Mechanic | Affected Driver | Evidence ID | Source |
|---|---|---|---|---|---|
| Remediation at operating and third-party sites | FY2024 Form 10-K; 2024-09-30 measurement | Investigations and revisions can increase cash payments; estimates exclude inflation and do not discount expected expenditure | Remediation cash cost and FCF; no payment calendar established | E1; USD 5 million current plus USD 36 million non-current; prior USD 3 million plus USD 41 million | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161 |
| Carbon regulation and aviation demand | FY2024 Form 10-K; publication date not stated | Management expects limited direct manufacturing burden, but regulation harming air travel can reduce replacement consumption | Demand and margin; supplier costs | E2 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |
| Physical climate hazards | FY2024 Form 10-K; publication date not stated | Facilities exposed to storms, fires and rising sea levels can suffer asset damage and production interruption | Shipment cash, repairs, asset value; no insured loss values disclosed | E3 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |
| Voluntary emissions target | At least 50% absolute Scope 1 and Scope 2 reduction by 2031 from FY2019 baseline | Efficiency and green-power actions may require expenditure, but no quantified program or debt linkage supplied | Transition spending not established; no margin ratchet demonstrated | E4 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |

### T2G.3 — Social and operational register

| Exposure | Source/Date | Transmission Mechanic | Event-Risk vs Ongoing | Evidence ID | Source |
|---|---|---|---|---|---|
| Product failure and aircraft accident liability | FY2024 Form 10-K; publication date not stated | Personal injury or death claims can require defense/settlement cash; insurer may deny or inadequately cover losses | Event-Risk; no current accident or sized loss asserted | E5 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31 |
| Labor relations and bargaining | Approximately 17% union represented; agreements through January 2029 | Wage settlements increase costs; stoppages can delay production and collections | Ongoing cost channel; event-risk escalation on dispute | E6 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 13 |
| Employment and other litigation | FY2024 Form 10-K; publication date not stated | Class actions, compensation claims or penalties can absorb cash and management resources | Event-Risk; no incremental quantified liability assigned | E7 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31 |
| Governance boundary | Business & governance, FY2024 | Financial policy and shareholder transfers assessed there, not relabeled as environmental risk | Ongoing; referenced only | E8 | Business & governance (CP-1A) |

### T2G.4 — Materiality classification

| Factor | Materiality Class | Transmission Basis | Catalyst (if Watch) | Evidence ID | Source |
|---|---|---|---|---|---|
| Environmental remediation | Material — Quantified | Recognized obligation USD 41 million at year-end versus USD 44 million prior; cash payment dates not quantified | Already recognized; materiality refers to obligation, not a current liquidity crisis | E1; R14 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161 |
| Product liability | Material — Directional | Safety-critical aircraft products and potentially inadequate insurance create a direct contingent cash channel | Already an identified contingent exposure; no incident assumed | E5 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31 |
| Wage inflation | Material — Directional | Represented workforce and limited contract cost recovery transmit wage increases to margin | Existing operating exposure, not a projected dispute | E6 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18 |
| Climate regulation and air travel | Watch | Issuer identifies possible demand and input-cost effects; no binding cost or demand reduction sized | Air-travel restriction, carbon cost passed by suppliers, or mandated investment | E2 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |
| Physical climate hazards | Watch | Named facility hazards could interrupt output and damage assets | Reported facility interruption or hazard/insurance assessment indicating significant uninsured exposure | E3 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |
| Emissions target as creditor protection | Immaterial to Credit | Voluntary operating target alone grants no demonstrated cash-flow or contractual creditor benefit | Not a Watch claim; no financing benefit credited | E4 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |
| Transition expenditure and sustainability-linked ratchet | Insufficient Information | No sized transition budget, KPI-linked debt schedule, ratchet or verification terms established | Obtain contractual terms before classification | E4; G8 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 145–153 |
| Other employment litigation | Watch | Potential cash litigation channel, but no specific escalating case sized | Material new claim, reserve increase or adverse judgment | E7 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31 |

### T2G.5 — Sustainability-linked mechanics

| Instrument | KPI | SPT + Test Date | Ratchet (direction; bps) | Symmetry | Credit-Meaningful? | Expected Spread Effect | Evidence ID | Source |
|---|---|---|---|---|---|---|---|---|
| No sustainability-linked instrument established in reviewed debt disclosures; not proof none exists | Not supplied: emissions target not linked to identified borrowing | Not supplied: no contractual target/test date; voluntary 2031 goal is not a debt test | Not supplied: step-up/step-down terms not established | Not supplied: no ratchet schedule | Not calculable: contractual benefit, miss consequence and reporting/verification absent | Not calculable: no spread ratchet or greenium evidenced; no zero-bp claim | G8 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 145–153 |

### T2G.6 — Refinancing access and cost of capital

| Effect | Direction | Quantified vs Directional | Linked Maturity/Funding Need | Evidence ID | Source |
|---|---|---|---|---|---|
| ESG investor exclusion, greenium or sustainability-linked price adjustment | Not established; no adverse or favorable funding direction inferred | Insufficient Information; no instrument quotes, mandate evidence or sustainability-linked terms | Receivables maturity July 2025; subordinated maturity November 2027; no ESG effect tied to either | G9 | Business & governance (CP-1A); Fundamental credit (CP-2) |
| Product or facility incident weakens operating cash before refinancing | Adverse only if contingent event occurs | Directional operating-to-liquidity channel; financing restriction not independently observed | Could reduce retained resources ahead of actual maturities; no assumed acceleration date | E3/E5 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31 |

### T2G.7 — Credit implication synthesis

| Material Factor | Risk Mechanic | Credit Implication | Confidence | Evidence ID | Source |
|---|---|---|---|---|---|
| Remediation accruals | Current and non-current obligations can consume cash; future investigations can revise estimates | Monitor payments and reserve adequacy; no immediate refinancing impairment evidenced from USD 41 million obligation | High for reported accrual; payment timing not established | E1/R14 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161 |
| Product liability — priority contingent factor | Component failure can create claims and operating interruption beyond effective insurance | Contingent FCF/liquidity deterioration is supported; probability of default change and loss given default not quantified | Medium for conditional transmission; no incident forecast | E5 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31 |
| Labor and fixed-price recovery | Wage increase enters production costs without general contractual recovery | Ongoing margin risk; overlap with inflation analysis, not an additive second shock | Medium for transmission | E6; contract risk | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18 |
| Climate Watch factors | Air-travel regulation or facility damage could reduce sales and require cash expenditure | Monitor named catalysts; no current stranded-asset write-down, refinancing premium or recovery deduction justified | Medium for conditional channel; magnitude not established | E2/E3 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |
| Voluntary target without debt linkage | Target is not an enforceable payment or covenant term in evidence | Immaterial to Credit as a protection; no spread benefit credited | High for absence of demonstrated linkage, not for absence of all instruments | E4/G8 | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |

### T2G.8 — Environmental and social gaps

| Gap | Missing Item | Why It Matters | Impact on Output | Required Follow-Up |
|---|---|---|---|---|
| G6 — Event severity | Product insurance limits/exclusions, accident loss scenarios, facility asset values and continuity coverage | Converts identified contingent event into cash loss and interruption duration | No event-driven liquidity, default-probability or recovery loss sized | Obtain liability/continuity policies and facility hazard values; monitor reported incident and coverage disputes |
| G7 — Remediation and transition cash | Remediation payment calendar and range; emissions inventory assurance, transition capex/opex and facility hazard costs | Recognized liability and voluntary target do not reveal future annual cash use | No remediation cash forecast or carbon sensitivity; climate factors remain Watch | Obtain site schedules, estimate ranges, assured inventory and funded transition plan |
| G8 — Sustainability instrument terms | Complete sustainability-linked instrument inventory, KPI definitions/ambition, SPTs/test dates, ratchet direction/bps/symmetry, reporting and verification | Determines enforceable pricing changes and whether a target has creditor relevance | No expected spread benefit/penalty, covenant protection or cosmetic/meaningful judgment | Obtain instrument terms and external verification if any; otherwise confirm no such debt |
| G9 — Capital access effect | Investor exclusions, attributable funding quotes and comparable greenium evidence | Needed to establish actual funding-channel change | No ESG-driven spread or refinancing-access premium asserted | Obtain dated investor/financing evidence matched to actual funding need |

### Definition reconciliation and claim lineage

| Claim | Treatment / classification | Strongest lineage | Claim confidence label | Source |
|---|---|---|---|---|
| M01 | Floating term loans and securitization explicitly identified | Directly Sourced | High | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73 |
| M02 | Active derivative terms and effective cash-flow designation | Directly Sourced | High | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177 |
| M03 | Forward collars start after anchor and contain floors/ceilings | Directly Sourced | High | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| M04 | FX forward selected flows and issuer historical test | Directly Sourced | High for attribution | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 73–74; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 178 |
| M05 | Contract recovery limitations and historical margin improvement | Directly Sourced | High | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 46 |
| M06 | Environmental obligations and historical compliance characterization | Directly Sourced | High for facts; management view separately attributed | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161 |
| M07 | Product liability and insurance risk; labor representation | Directly Sourced | High for disclosure | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31 |
| M08 | Climate hazards and voluntary emissions target | Directly Sourced | High for attribution, not assured emissions | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 25 |
| M09 | Debt reconciliation and unhedged exposure | Calculated | High for specified perimeter | R01–R07 |
| M10 | Borrowing cash-interest shock and mechanical FCF comparison | Calculated | High for static formula; not net-interest forecast | R08–R11 |
| M11 | Replacement notional path and first step-down | Calculated | High for schedule; not forward cash protection | R13 |
| M12 | Total remediation obligation | Calculated | High for aggregate, not timing | R14 |
| M13 | Moderate macro risk, rather than immediate liquidity crisis | Analyst Inference | Medium | R08/R10; Financial foundation (CP-1); T2F.8 |
| M14 | Product liability prioritized among contingent environmental/social channels | Analyst Inference | Medium | T2G.4/T2G.7 |
| M15 | Emissions target is not demonstrated creditor protection | Analyst Inference | High for bounded conclusion | T2G.5 |
| M16 | Approximately USD 30 million issuer sensitivity versus USD 57.89 million reconstruction; approximately 77% allocation methodology not reconciled | Conflicting | Insufficient Information for common-basis net-interest adoption | T2F.5; G1 |
| M17 | Matched FX cash sensitivity and natural hedge | Insufficient Information | Insufficient Information | G2 |
| M18 | Input-cost shock and recovery lag sizing | Insufficient Information | Insufficient Information | G3 |
| M19 | Environmental/social loss severity and payment forecast | Insufficient Information | Insufficient Information | G6–G7 |
| M20 | Sustainability ratchets and funding-access pricing effects | Insufficient Information | Insufficient Information | G8–G9 |

The cap and swaps are counted only once as active instruments; basis transactions are not added as additional hedge notional. Accounting effectiveness supports the specified relationships, not every future debt balance or counterparty outcome. The expected reclassification into interest expense is approximately negative USD 25 million over the next twelve months, and expected FX-forward gains in net sales are approximately USD 3 million; these accounting forecasts are not added to the marginal rate shock or treated as liquid cash balances.
Basis: TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–178

| Additional disclosed quantity | Amount / term | Treatment | Source |
|---|---|---|---|
| Active swap subtotal | USD 2,700 million | Three active swaps; included within USD 3,400 million with cap | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| Expected rate derivative reclassification | Approximately −USD 25 million in next twelve months | Existing gains/losses and caplet amortization; not new shock or notional | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 178 |
| Expected FX forward reclassification | Approximately +USD 3 million net-sales gain in next twelve months | Not a forecast of full-group FX cash outcome | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 178 |
| Derivative fair values | Rate assets USD 57 million; liabilities USD 10 million at September 2024 | Neither notional nor available liquidity; no assumed close-out payment equal to gross notional | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 177 |

| Coverage item | Required fields | Present | Definition |
|---|---|---|---|
| Required register schema plus source gate | 113 | 109 | One instance of each required column concept across the seventeen registers plus source gate; extra Source columns excluded. Four decision-evidence concepts remain incomplete: FX matching, cost sensitivity, event cash severity, sustainability instrument pricing. |
| Unresolved material findings | 4 | 4 | Interest-method reconciliation; FX/cost quantification; environmental/social loss calibration; sustainability financing terms. Other requests are narrower monitoring needs, not additional severity findings. |

## Calculations

All issuer monetary operands below are consolidated USD millions at September 30, 2024 unless otherwise stated. Gross principal is used for contractual interest exposure; carrying debt is the required total-debt denominator. Multiplication by one percent is evaluated by dividing by one hundred. The borrowing-interest shock assumes unchanged balances and spreads, full base-rate transmission and continued hedge performance; the active cap is above its disclosed strike in the reported-rate environment. No tax shield, cash-interest income, premium repricing, subsequent borrowing or future renewal is assumed. Historical FCF comparisons are arithmetic illustrations, not forecasts.
Basis: Financial foundation (CP-1); TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177

| ID | Measure and period | Operation / exact operands | Result | Unit / limitation | Source |
|---|---|---|---|---|---|
| R01 | Identified floating principal, 2024-09-30 | 8,702 + 487 | 9,189 | USD million; term loans and securitization | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73 |
| R02 | Active protected principal, 2024-09-30 | 500 + 1,500 + 700 + 700 | 3,400 | USD million; three swaps and cap; forward collars excluded | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 175–177 |
| R03 | Identified unhedged floating principal | 9,189 + (−3,400) | 5,789 | USD million; not all other debt rate terms established | Same source inputs as R01–R02 |
| R04 | Total carrying debt | 24,394 + 486 | 24,880 | USD million; current plus non-current plus securitization | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, pages 144–145; Financial foundation (CP-1) |
| R05 | Principal versus carrying debt delta | 25,068 + (−24,880) | 188 | USD million; issuance cost and discount effects, not additional cash exposure | Financial foundation (CP-1) |
| R06 | Fixed-coupon note principal | 2,650 + 2,100 + 1,200 + 2,750 + 750 + 1,450 + 1,000 + 2,200 + 1,500 | 15,600 | USD million; excludes other debt not classified fixed/floating | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 145 |
| R07 | Unhedged percentage of carrying debt | 5,789 / 24,880 = 0.23267684887459807073954983922829581994; fraction / 0.01 | 23.267684887459807073954983922829581994 | %; not comparable to complement of issuer gross allocation without denominator bridge | R03–R04 sources |
| R08 | Static annual +100 bp borrowing-interest shock | 5,789 / 100 | 57.89 | USD million annual increase; FCF change −USD 57.89 million before offsets | R03 sources; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| R09 | Shock relative to FY2024 historical FCF | 57.89 / 1,880 = 0.030792553191489361702127659574468085106; fraction / 0.01 | 3.0792553191489361702127659574468085106 | %; arithmetic comparison, not expected deterioration | R08; Financial foundation (CP-1) |
| R10 | Illustrative historical FCF after borrowing-interest shock | 1,880 + (−57.89) | 1,822.11 | USD million; no operating, tax or cash-income response | Financial foundation (CP-1); R08 |
| R11 | Gross floating-interest comparator | 9,189 / 100 | 91.89 | USD million annual increase before all hedges | R01 sources |
| R12 | Reconstructed versus issuer sensitivity difference | 57.89 + (−30) | 27.89 | USD million; issuer USD 30 million approximate; not a reconciliation or chosen adjustment | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73; R08 |
| R13 | Hedge replacement notional path | March 2025 active/starting: 700 + 700 + 1,100 = 2,500; September 2025: 1,100 + 500 + 1,338 = 2,938; September 2026: 1,338 + 1,550 = 2,888; first expiry gap: 2,000 − 1,100 = 900 | 2,500; 2,938; 2,888; 900 | USD million; notional only, not future effective fixed debt or predicted cash sensitivity | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176 |
| R14 | Environmental remediation obligations | FY2024 current 5 + non-current 36; FY2023 current 3 + non-current 41 | 41; 44 | USD million; recognized obligation, not annual cash outflow | TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 161 |
| R15 | Required field count | 1 + 8 + 10 + 8 + 6 + 7 + 10 + 8 + 7 + 6 + 4 + 5 + 5 + 5 + 8 + 5 + 5 + 5; present = 113 − 4 | 113; 109 | Required conceptual fields; structural population does not establish missing evidence | Required-register headers and coverage definition |

## Gaps

The decisive unresolved question is why the issuer's reported interest-cost sensitivity differs from the term-by-term reconstruction. Neither number is deleted or averaged. Until the treasury assumptions are supplied, a single net-interest forecast is restricted; the independently traced borrowing-interest scenario remains usable for a bounded comparison. Missing FX, cost and incident-loss inputs restrict their own numerical decisions rather than preventing all macro or environmental analysis.
Basis: calculation R08; calculation R12; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 73; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176

| Bounded research question | Factual predecessor | Consumer | Minimum requested evidence | Restricted conclusion |
|---|---|---|---|---|
| What exact hedge, debt, rate and cash-income assumptions produce the issuer test? | Annual rate disclosure and dated derivative schedule | Rates, FX & hedging; Forward credit model | Treasury sensitivity worksheet at 2024-09-30, hedge allocations and reset conventions | Common-basis net-interest forecast |
| How much FX and inflation risk remains after matching and repricing? | Foreign-currency transaction disclosure and explicit contract recovery restrictions | Rates, FX & hedging; Downside | Currency-matched operating/cash ladder, forward confirmations and input-cost/pricing bridge | Quantified non-rate cash-flow stress |
| What cash-loss range remains after insurance and remediation allocations? | Aircraft product-liability warning and recognized remediation obligations | Rates, FX & hedging; Downside | Insurance limits/exclusions, facility hazard values and dated site payment schedule | Event loss and liquidity/recovery sizing |
| Is any financing actually sustainability-linked and does investor demand affect its pricing? | Voluntary emissions target and conventional debt descriptions | Rates, FX & hedging; Security selection | Complete linked-debt terms or issuer confirmation, verification and attributable financing evidence | Sustainability-driven spread benefit or penalty |

| Other boundary | Consequence | Required action |
|---|---|---|
| Annual evidence is retrospective | No claim that all annual disclosures were tradable information on the September date | Establish official publication chronology only if historical information availability becomes a decision |
| Detailed economic coverage terminology beyond the supplied definitions was not established | Coverage labels describe disclosed instrument mechanics, not legal certification or a broader taxonomy | Use stated rate, maturity and instrument linkage; obtain contract confirmation for legal reliance |
| No assigned research adoption evidence supplied to this analysis | No independently recovered external answers adopted; questions remain bounded requests | Resolve the named questions without treating unanswered requests as issuer facts |

## Next module

Forward credit model should carry separate borrowing-interest and issuer-reported sensitivity cases until the treasury reconciliation is obtained, apply collars only during their actual periods and rate bands, and retain the disclosed expiry ladder. Downside should combine rate and cost pressure with weaker production only through explicit assumptions, avoiding double-counting wage risk as both inflation and a separate social shock. Committee decision should challenge cash retention after hedge expiry and insurance containment of a major product event; neither an ESG spread premium nor covenant protection is established here.
Basis: Financial foundation (CP-1); Fundamental credit (CP-2); calculation R08; calculation R13; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 18; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 31; TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 176
