### Forecast inputs (machine-readable)

```json
{
  "schema_version": "cpos-forecast-inputs/1",
  "base": {
    "revenue": {"amount": "7940", "reason": null},
    "ebitda": {"amount": "3813", "reason": null},
    "interest": {"amount": "1158", "reason": null},
    "taxes": {"amount": "539", "reason": null},
    "wc": {"amount": null, "reason": "CP-1 does not state a single canonical working-capital operand for this forecast interface; cash-flow components and a management bridge are separate definitions."},
    "capex": {"amount": "165", "reason": null},
    "fcf": {"amount": "1880", "reason": null},
    "debt": {"amount": "24880", "reason": null},
    "cash": {"amount": "6261", "reason": null},
    "undrawn": {"amount": "843", "reason": null}
  },
  "base_drivers": {
    "revenue_growth": {"values": [null, null, null], "category": "analyst_judgment", "rationale": "No driver selected before required dependency and forecast-scope gates clear.", "limitation": "No approved operating plan or growth assumptions supplied; not a zero-growth case."},
    "ebitda_margin": {"values": [null, null, null], "category": "analyst_judgment", "rationale": "No margin assumption selected before the model gate clears.", "limitation": "Historical reported EBITDA is not guidance; acquisition and mix normalization remain incomplete."},
    "capex_pct_revenue": {"values": [null, null, null], "category": "analyst_judgment", "rationale": "No three-year capex driver selected at the blocked gate.", "limitation": "Upstream liquidity work identifies limited-year guidance, not a locked three-year forecast or maintenance/growth split."},
    "tax_wc_pct_revenue": {"values": [null, null, null], "category": "analyst_judgment", "rationale": "No combined tax and working-capital driver selected.", "limitation": "Canonical working-capital base and forward cash timing are missing; no cash-conversion plug permitted."},
    "interest_rate": {"values": [null, null, null], "category": "analyst_judgment", "rationale": "No effective forward interest rate selected.", "limitation": "Historical net cash interest, scheduled contractual interest and static rate sensitivity have different periods and definitions."},
    "dividends": {"values": [null, null, null], "category": "analyst_judgment", "rationale": "No full-year distribution schedule selected before scope and dependencies clear.", "limitation": "A known declared payment is not a complete annual schedule; future undeclared distributions are not assumed zero."},
    "debt_repayment": {"values": [null, null, null], "category": "analyst_judgment", "rationale": "No annual repayment path selected.", "limitation": "Mandatory schedules, receivables renewal and voluntary cash allocation must be reconciled; FCF is not automatically swept to debt."}
  },
  "downside_shock": null,
  "years": [
    {"year": 2025, "start": "2024-10-01", "end": "2025-09-30"},
    {"year": 2026, "start": "2025-10-01", "end": "2026-09-30"},
    {"year": 2027, "start": "2026-10-01", "end": "2027-09-30"}
  ],
  "scope_limits": [
    "Blocked interface only: CP-2A is explicitly blocked and supplies no scenario; no forecast figures are submitted.",
    "FY2025-FY2027 is the required post-actual interface calendar, not a locked underwriting horizon or evidence that the full refinancing horizon is covered.",
    "Base operands are copied from CP-1 FY2024 consolidated USD-million data; outflows are positive magnitudes.",
    "Debt uses carrying value; EBITDA uses reported EBITDA; interest uses cash paid net; taxes use cash paid net of refunds; undrawn uses the reported revolver only.",
    "Missing working capital and driver values prevent forecast computation; null is not zero.",
    "Cash accessibility, facility conditions, acquisition deployment, financing movements, minimum cash and complete CFO bridge are unresolved.",
    "Retrospective annual evidence is not certified available at the as-of date; December-quarter results are excluded."
  ]
}
```
