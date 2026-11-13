# CP-1 runbook — definitions and discipline

CP-1 works from a creditor's perspective: every figure is source-traceable and every calculation auditable. Later modules inherit these definitions unless a current-period source gives an explicit alternative, logged in the definition conflict register.

## Metrics
**Inputs (extracted):** Revenue, EBITDA (Reported), EBITDA (Adjusted), EBIT, D&A, Interest Expense (Cash), Tax (Cash), Capex (Total / Maint / Growth), OCF, FCF, FFO, Net Income, Total Debt, Net Debt, Senior Secured Debt, Cash & Equivalents, Undrawn Committed Facilities, WC Change.

**Calculated:** Leverage: Debt/EBITDA, Net Debt/EBITDA, Senior Secured/EBITDA. Coverage: EBITDA/Cash Interest, (EBITDA−Capex)/Cash Interest, FFO/Debt. Cash flow: FCF, FCF Conversion (FCF/EBITDA), DCF. Liquidity: Cash+Undrawn, Liquidity/Debt. Margin: Gross %, EBITDA %, EBIT %, Net Income %. Growth: Revenue %, EBITDA %. Also FFO interest cover, CFO/Debt, FCF/Debt, DCF/Debt, Capex/Revenue.

Total Debt is balance-sheet carrying value; gross principal is never the leverage denominator, and a ratio on principal is labelled. EBITDA in a ratio is reported EBITDA; a ratio on adjusted EBITDA is a separate, labelled row.

## Calculation status (8 values)
`Verified` | `Calculated` | `Estimated` | `Proxy` | `Not Calculable` | `Partial` | `Conflicted` | `Not Available`

## Null and derived-period rules
- A source dash or blank is a missing value with a gap line, not 0.
- LTM or YTD is valid only if ALL sub-period components are available; one missing component makes the whole derived figure missing.

## Event and liability discipline
- **Multi-figure events:** one economic event with different figures across statements means all figures, each statement role labelled, in ONE conflict row explaining why they differ. Presenting one figure silently is fabrication.
- **Subsequent events:** scan every source for events after the balance-sheet date; flag each with its date; never blend it into period figures.
- **Non-debt funding float:** a material non-debt, non-interest-bearing liability funding operations (customer deposits, deferred revenue, supplier finance) is credit-relevant working-capital float, never ordinary payables: flag its size, trend and obligation and carry it to the analysis as a named evidence, risk mechanic, credit implication story.

## Evidence hierarchy
Audited statements > unaudited with auditor > unaudited > lender or sponsor material > rating agency > internal > external.
