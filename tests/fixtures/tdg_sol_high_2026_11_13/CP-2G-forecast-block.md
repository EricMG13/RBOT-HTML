### Forecast inputs (machine-readable)

```json
{
  "schema_version": "cpos-forecast-inputs/1",
  "currency": "USD",
  "scale": 1,
  "base": {
    "revenue": {"amount": "7940", "reason": null, "row": "NET SALES", "period": "FY2024"},
    "ebitda": {"amount": "4173", "reason": null, "row": "EBITDA As Defined", "period": "FY2024"},
    "interest": {"amount": "1158", "reason": null, "row": "Cash paid during the period for interest, net", "period": "FY2024"},
    "taxes": {"amount": "539", "reason": null, "row": "Cash paid during the period for income taxes, net of refunds", "period": "FY2024"},
    "wc": {"amount": null, "reason": "Financial foundation has individual signed operating-change rows, but no aggregate working-capital amount in a table cell under a reporting-period header. Its differently scoped changes-block calculation is not such a cell."},
    "capex": {"amount": "165", "reason": null, "row": "Capital expenditures", "period": "FY2024"},
    "fcf": {"amount": "1880", "reason": null, "row": "Free cash flow after capital expenditure", "period": "FY2024"},
    "debt": {"amount": "24880", "reason": null, "row": "Total debt carrying amount", "period": "FY2024"},
    "cash": {"amount": "6261", "reason": null, "row": "Cash and cash equivalents", "period": "FY2024"},
    "undrawn": {"amount": "843", "reason": null, "row": "Undrawn committed revolving facilities at year-end", "period": "FY2024"}
  },
  "base_drivers": {
    "revenue_growth": {"values": ["0.12", "0.12", "0.12"], "category": "Analyst Interpretation", "rationale": "Carry the annual report's FY2024 commercial-aftermarket organic growth of 12.0% across the consolidated company, below total organic growth of 16.2%.", "limitation": "This is a consolidated scenario anchor, not channel guidance, a volume-price bridge or acquisition annualisation."},
    "ebitda_margin": {"values": ["0.5256", "0.5256", "0.5256"], "category": "Analyst Interpretation", "rationale": "Carry FY2024 EBITDA As Defined of 4173 divided by revenue of 7940, rounded to four decimal places.", "limitation": "Issuer adjustments remain embedded; no additional margin expansion, acquisition synergies or contractual EBITDA equivalence is assumed."},
    "capex_pct_revenue": {"values": ["0.0208", "0.0208", "0.0208"], "category": "Analyst Interpretation", "rationale": "Carry FY2024 capital expenditure magnitude of 165 divided by revenue of 7940, rounded to four decimal places.", "limitation": "Maintenance and growth spending are not separately forecast; proportional spending may miss mandatory projects."},
    "tax_wc_pct_revenue": {"values": ["0.1222", "0.1222", "0.1222"], "category": "Analyst Interpretation", "rationale": "Carry the historical composite cash leakage of EBITDA As Defined 4173 less net cash interest 1158 less CFO 2045, or 970, divided by revenue 7940, rounded to four decimal places.", "limitation": "Despite the field name, this includes taxes, working capital and adjusted-earnings-to-cash differences. It is not pure working capital and does not separately forecast cash taxes or a tax shield."},
    "interest_rate": {"values": ["0.0613", "0.0613", "0.0613"], "category": "Analyst Interpretation", "rationale": "Disclosed less-than-one-year scheduled interest of 1524 divided by opening carrying debt of 24880, rounded to four decimal places; apply to opening annual debt.", "limitation": "Composite financing yield, not a coupon or SOFR curve. Later-year hedge changes, intrayear balances and incremental interest on the October draw are not independently modelled."},
    "dividends": {"values": ["4348", "2038", "2038"], "category": "Analyst Interpretation", "rationale": "FY2025 uses the documented October payment of 4216 plus 132. Later years repeat FY2024 paid dividends and equivalents of 2038 as a financial-policy continuation case.", "limitation": "Only the first payment is documented as occurring. Repetition is not a declared future distribution and excludes an additional timing allocation for residual dividend-equivalent liabilities."},
    "debt_repayment": {"values": ["580", "92", "92"], "category": "Documentary Fact", "rationale": "Financial foundation's annual maturity schedule: FY2025 93 plus year-end receivables principal 487, then 92 and 92; no receivables renewal presumed.", "limitation": "Excludes finance-lease principal allocations. FY2025 is net of the matched subsequent 162.5 draw and its additional 162.5 repayment, which cancel annually; debt issuance-cost amortisation is held constant."}
  },
  "downside_shock": {"ebitda_decline": "0.2", "rate_increase": "0.0184"},
  "upside_drivers": {
    "revenue_growth": {"values": ["0.162", "0.162", "0.162"], "category": "Analyst Interpretation", "rationale": "Carry the disclosed FY2024 total organic growth of 16.2% rather than the base 12.0% aftermarket anchor.", "limitation": "No claim that historical recovery growth persists or that future acquisitions are included."},
    "dividends": {"values": ["4348", "38", "38"], "category": "Analyst Interpretation", "rationale": "Retain the documented October settlement, then use FY2023 paid distributions of 38 as an anchor for suspending future special dividends while retaining a smaller payment allowance.", "limitation": "Requires management action; 38 is not a contractual floor or a stated future payment."}
  },
  "downside_drivers": {
    "revenue_growth": {"values": ["0", "0", "0"], "category": "Analyst Interpretation", "rationale": "Hold the sourced FY2024 revenue of 7940 flat, disconfirming continuation of 12.0% aftermarket and 16.2% total organic growth. Apply the separate moderate earnings and financing stress to that flat-sales case.", "limitation": "Flat sales are an explicit scenario, not a missing value replaced with zero; no measured price-volume or channel-demand elasticity is asserted."}
  },
  "facilities": null,
  "years": [
    {"year": 2025, "start": "2024-10-01", "end": "2025-09-30"},
    {"year": 2026, "start": "2025-10-01", "end": "2026-09-30"},
    {"year": 2027, "start": "2026-10-01", "end": "2027-09-30"}
  ],
  "scope_limits": [
    "Consolidated industrial aerospace company; annual periods; USD millions. No separate matched-funding finance-company perimeter is identified.",
    "Historical cash is before the committed October settlement. Financial foundation separately states distribution-only pro forma cash of 1913 and principal-based pro forma net debt of 23155 with net leverage of 5.55x. Including the separate draw, it states cash of 2075.5. These are adopted comparisons, not replacement opening balances.",
    "Downside's selected moderate stress is a 20% earnings decline and 30% proportional increase in cash interest, not a 30-percentage-point rate shock. The proportional interest shock is translated into an additive model-yield change: 0.0613 times 0.30 equals 0.01839, rounded to 0.0184. This is an equivalent aggregate yield sensitivity, not a benchmark-rate prediction.",
    "Apply the 20% earnings shock once to each year's margin level, not recursively to prior-year stressed earnings. The flat-sales override is an additional explicit operating assumption; the result is not identical to applying only the static stress to the growing base case.",
    "The upside and downside inherit all base drivers not expressly changed. The downside shock is applied once; do not apply another interest or margin haircut.",
    "Interest is net cash paid in the historical base, not interest expense. Forward interest uses opening carrying debt and a rounded composite financing yield.",
    "No complete facility balance-and-rate table is printed by Financial foundation. Instrument cash-interest and hedge schedules therefore are not submitted; aggregate rates control the forecast.",
    "CFO is a mechanical cash proxy: EBITDA less interest less composite cash leakage. FCF is that CFO less capex, before acquisitions, distributions and debt principal.",
    "Future acquisitions, disposals, equity proceeds and other unmatched investing/financing flows are excluded as explicit stand-alone scenario boundaries, not claims that unspecified actual flows are zero.",
    "FY2025 gross flows separately include the subsequent draw of 162.5 and repayment of 742.5; their net debt reduction is 580. Later annual scheduled repayments are 92 and 92. Missing finance-lease principal is not invented.",
    "The principal-to-carrying difference of 188 is not amortised or silently released. Forecast debt is a carrying-balance proxy reduced by disclosed principal payments, with no additional issuance costs or noncash accretion modelled.",
    "Undrawn 843 is reported historical revolving availability, not certified accessible liquidity and not an automatic deficit plug. Receivables capacity is not added after its assumed repayment.",
    "Signed negative cash is a pre-financing funding requirement, not an executable closing cash balance. No automatic revolver drawing, new-money interest or negative-cash netting into leverage is assumed.",
    "Minimum operating cash, contractual covenant EBITDA, fixed-charge definitions and complete lease-principal schedules are not established. No liquidity-exhaustion date, covenant headroom, rating or security recommendation is produced.",
    "The three-year horizon ends before FY2028 and FY2029 maturity concentrations; refinancing terms and feasibility remain separate decisions. No case probabilities are assigned.",
    "The aggregate historical working-capital operand and segment-slot allocation are not supplied in eligible Financial foundation table cells. The composite leakage driver permits a bounded aggregate cash forecast, but division-level workbook forecasts cannot be populated from an inferred segment order."
  ]
}
```
