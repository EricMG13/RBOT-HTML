# CP-1 runbook — definitions and discipline

CP-1 extracts, normalises and quality-assesses issuer financial data into statement tables, KPIs and calculation registers, from a creditor's perspective. Every figure is source-traceable and every calculation auditable. Later modules inherit these definitions unless a current-period source gives an explicit alternative that is logged in the definition conflict register.

## Metrics
**Inputs (extracted):** Revenue, EBITDA (Reported), EBITDA (Adjusted), EBIT, D&A, Interest Expense (Cash), Tax (Cash), Capex (Total / Maint / Growth), OCF, FCF, FFO, Net Income, Total Debt, Net Debt, Senior Secured Debt, Cash & Equivalents, Undrawn Committed Facilities, WC Change.

**Calculated:** Leverage: Debt/EBITDA, Net Debt/EBITDA, Senior Secured/EBITDA. Coverage: EBITDA/Cash Interest, (EBITDA−Capex)/Cash Interest, FFO/Debt. Cash flow: FCF, FCF Conversion (FCF/EBITDA), DCF. Liquidity: Cash+Undrawn, Liquidity/Debt. Margin: Gross %, EBITDA %, EBIT %, Net Income %. Growth: Revenue %, EBITDA %. Also FFO interest cover, CFO/Debt, FCF/Debt, DCF/Debt, Capex/Revenue.

Total Debt is balance-sheet carrying value (current plus long-term, net of issuance costs and discounts); gross principal is never the leverage denominator. Where the two differ materially, ONE definition-conflict row logs both figures and any ratio on the other basis is labelled. Net Debt is Total Debt less cash. EBITDA in a ratio is reported EBITDA; a ratio on adjusted EBITDA is a separate, labelled row.

## Calculation status (8 values)
`Verified` | `Calculated` | `Estimated` | `Proxy` | `Not Calculable` | `Partial` | `Conflicted` | `Not Available`

## Null and derived-period rules
- A missing value is never zero unless the source states zero. A source dash or blank is a missing value with a gap line, not 0.
- A KPI with a missing numerator or denominator is `Not Calculable`.
- LTM or YTD is valid only if ALL sub-period components are available; one missing component makes the whole derived figure missing.

## Event and liability discipline
- **Multi-figure events:** one economic event with different figures across statements (for example a debt extinguishment: profit-and-loss charge, cash-flow non-cash add-back, cash paid) means all figures, each statement role labelled, in ONE conflict row explaining why they differ. Presenting one figure silently is fabrication.
- **Subsequent events:** scan every source for events after the balance-sheet date (dividends declared, refinancings, buybacks, disposals); flag each with its date; never blend it into period figures.
- **Non-debt funding float:** a material non-debt, non-interest-bearing liability funding operations (customer deposits, deferred revenue, supplier finance) is credit-relevant working-capital float: flag its size, trend and obligation, and carry it to the analysis as a named evidence, risk mechanic, credit implication story; never ordinary payables.

## Evidence hierarchy
Audited statements > unaudited with auditor > unaudited > lender or sponsor material > rating agency > internal > external.

## Definition conflict, worked
BAD: "Net Debt/EBITDA was 4.2x based on the lender presentation." The presentation uses adjusted EBITDA; the reported-basis ratio is 5.1x and the difference is not disclosed.
GOOD: "Net Debt/EBITDA is 5.1x on reported EBITDA (annual report p.45) and 4.2x on adjusted EBITDA (lender presentation p.12); EUR 25m of add-backs account for the difference." One definition-conflict row logs it.

## Fail or restrict
Unsupported claim | missing trace | undocumented calculation | unresolved conflict | malformed table | blocked upstream | classification from a file name | currency switch | definition change without a log entry.
