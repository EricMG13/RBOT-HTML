# TDG FY2024 (as of 2024-09-30): full credit assessment on Copilot gpt-6.1-sol, medium vs high effort

Rulings: `docs/rulings/2026-11-13-tdg-full-copilot-sol-rerun.md`,
`docs/rulings/2026-11-13-tdg-full-copilot-sol-high.md`. Historical case; not a current credit view.
One run per setting, so differences may be run-to-run variation rather than effort.

## Bottom line

- Same credit conclusion in both runs: Requires More Work, relative value Unclear, no size. The same
  core figures, and no wrong shared figure was found in either run.
- High effort cost 1.32x (USD 11.37 vs 8.62) and took 1.40x the model time (95 vs 68 minutes).
- High was judged better in 7 of 13 modules, medium in none, no material difference in 4, and CP-5 a
  split. The gain is evidence a committee would use, not a different view. Most of it traces to one
  figure medium did not use: next year's scheduled interest of USD 1,524 million.
- Medium made two analytical errors that travelled downstream; high made none of that kind, but it
  missed the capex guidance and one stated date.
- Both runs stopped at CP-5 on the first attempt for the same checker reason, unrelated to effort.

## Runs

| Side | Run folder (scratchpad workspace `tdg-ws/runs/`) | Effort | Modules | Charged USD |
| --- | --- | --- | --- | --- |
| Medium | `tdg-full-copilot-sol-001-resume` | medium, every call | 13 accepted, delivered | 8.62 |
| High | `tdg-full-copilot-sol-high-001-resume` | high, every call (`--high-modules`) | 13 accepted, delivered | 11.37 |
| Earlier run (context only) | `tdg-proof-snapshot-opus-002` | claude-opus-5-5 medium | 13 | 19.45 |

Like for like between medium and high: same code (`main` at `b2780e8`), instructions, files, context,
route and CP-8 comparison run. Not like for like with the earlier Opus run: it used the method texts
from before PR #93, so it is listed for scale only.

Both runs stopped at CP-5 after ten accepted modules and were finished in copies of their folders with
CP-5's retained attempts removed (the owner's instruction, recorded in the first ruling). CP-5's cost
below includes the failed attempt. Both runs carry the run id `…-copilot-sol-medium`, because the id
comes from the configuration name; the effort actually sent is in each call's `requested_effort`.

## Telemetry per module (`live/calls.jsonl`, `events.jsonl`, delivered handoffs)

USD / model calls / drafts rejected / reasoning tokens / model seconds / handoff words.

| Module | Medium | High | High ÷ medium USD |
| --- | --- | --- | --- |
| CP-0 | 0.29 / 8 / 0 / 491 / 201 / 5,139 | 0.43 / 11 / 0 / 5,485 / 385 / 6,448 | 1.48 |
| CP-1 | 0.42 / 10 / 1 / 1,227 / 268 / 7,587 | 0.63 / 18 / 1 / 4,271 / 453 / 8,978 | 1.50 |
| CP-1A | 0.55 / 12 / 1 / 831 / 342 / 9,569 | 0.66 / 14 / 1 / 2,903 / 445 / 11,474 | 1.20 |
| CP-DR | 0.28 / 8 / 0 / 1,099 / 151 / 3,603 | 0.44 / 10 / 0 / 3,972 / 266 / 5,493 | 1.57 |
| CP-4 | 0.37 / 6 / 0 / 137 / 67 / 1,714 | 0.37 / 4 / 0 / 667 / 67 / 1,396 | 1.00 |
| CP-2 | 0.44 / 6 / 0 / 993 / 269 / 7,882 | 0.61 / 11 / 0 / 2,430 / 371 / 10,004 | 1.39 |
| CP-2A | 0.62 / 14 / 1 / 3,658 / 381 / 10,143 | 0.80 / 15 / 1 / 5,080 / 537 / 12,487 | 1.29 |
| CP-2E | 0.66 / 12 / 1 / 1,092 / 350 / 9,295 | 0.80 / 12 / 1 / 3,286 / 439 / 10,479 | 1.21 |
| CP-2G | 0.41 / 8 / 0 / 1,711 / 300 / 8,294 | 0.77 / 20 / 0 / 6,545 / 613 / 11,980 | 1.88 |
| CP-3 | 0.80 / 12 / 1 / 1,160 / 352 / 11,203 | 0.97 / 11 / 1 / 2,964 / 434 / 14,908 | 1.21 |
| CP-5 | 2.26 / 21 / 4 / 4,854 / 649 / 8,508 | 2.80 / 20 / 3 / 11,483 / 952 / 9,941 | 1.24 |
| CP-6 | 0.73 / 8 / 0 / 545 / 566 / 8,575 | 0.99 / 8 / 1 / 3,209 / 357 / 10,693 | 1.36 |
| CP-8 | 0.79 / 11 / 0 / 850 / 166 / 3,498 | 1.08 / 11 / 0 / 5,966 / 380 / 3,985 | 1.37 |
| Total | 8.62 / 136 / 9 / 18,648 / 4,060 / 95,010 | 11.37 / 165 / 9 / 58,261 / 5,700 / 118,266 | 1.32 |

- Tokens: medium 15.4 million input (87% read from cache) and 245,000 output; high 19.6 million input
  (87% cached) and 352,000 output. No call errored in either run.
- High used 3.1x the reasoning tokens and wrote 24% more words. Rejected drafts were equal (9 each).
- CP-5 is a quarter of each run's cost: it reads every other handoff, and its first attempt failed.
- Earlier Opus run, for scale: USD 19.45, 162 calls, 112,609 reasoning tokens, 75,985 words.

## Analysis quality (independent read of both runs' handoffs; figures checked against the 10-K)

| Module (what it does in this run) | Verdict | What decides it |
| --- | --- | --- |
| CP-0 source readiness | No material difference | Same go-ahead and restrictions. |
| CP-1 financial foundation and credit metrics | High, narrowly | Medium calls the November 2027 notes a data conflict; they fall in fiscal 2028, as the 10-K says. High includes the USD 487 million securitization in FY2025 maturities (580, not 93). High left the October draw and distribution dates as month only although the 10-K gives 16 and 18 October. |
| CP-1A business and governance | High | High cites the 10-K's order for excess cash (debt prepayment last) and reconciles the FY2024 distribution (1,937 + 83 + 18 = 2,038). Medium says the 2033 maturity day is not established; the 10-K states it. |
| CP-DR deep research | High | Medium excluded the 10-K as post-cutoff although no cutoff was set. High built a retrieval list of the credit agreement, amendments 13-17 and indentures, and found that Amendment No. 17 is titled differently in the exhibit index and the debt note. Neither could answer its two questions (web search off). |
| CP-4 legal and covenants | No material difference | Both correctly Blocked: no executed governing document in the files. |
| CP-2 fundamental credit | High | High sets FY2024 EBITDA against next year's scheduled interest: 4,173 / 1,524 = 2.74x, against the historical 3.60x that medium only restates. High omits the issuer's pro forma liquidity of 2,919, which medium keeps. |
| CP-2A downside stress | High | High's interest shock (30%) is tied to the step-up from 1,158 to 1,524; medium's (2.5-10%) ignores it, leaving about USD 318 million too much free cash flow in its moderate case. Arithmetic is right in both. |
| CP-2E rates, FX, hedging, ESG | No material difference | Identical rate findings, all checked. |
| CP-2G forecast | High, with one flaw | Medium published no forecast, saying total debt was missing, while its own handoff states 24,880. High published full base and downside paths (recomputed, correct) but used capex at 2.08% of sales, not the guided 2.5-3.5%, overstating free cash flow by about 82 in FY2025. |
| CP-3 credit view | High, slightly | Same recommendation. High quantifies what would change it (FY2026 funding gap of 310.26 if distributions repeat; coverage watch 2.00x against a downside of 1.68x); medium's is qualitative because its CP-2G withheld the forecast. |
| CP-5 QA gate | Split | Medium raised 4 Material issues, all real, including its own CP-1 maturity error and the withheld forecast. High raised 2 Material and 2 Minor, all real, one over-graded. Medium missed an orphan calculation reference in its own CP-3 of the kind high caught in its run. |
| CP-6 committee challenge | High, slightly | Both specific to this issuer. High's best question is the 3.60x-to-2.74x coverage point; medium's is that the October payment was 2.31x annual free cash flow. |
| CP-8 changes vs earlier run | High, slightly | Same headline (issuer unchanged; Watchlist became Requires More Work). High attributes more changes (maturities 93 to 580; forecast yield basis). High wrongly says no combined October pro forma is stated; its own CP-1 states it. |

Errors by kind:

- Medium, analytical: the false maturity "conflict" (CP-1, repeated in CP-DR as a research target);
  the forecast withheld on an input the handoff itself held (CP-2G, which weakened CP-3 and CP-8);
  the interest stress calibrated to history.
- High, sourcing: October dates left as month only in CP-1 (its CP-1A has them); capex guidance not
  used in CP-2G; pro forma liquidity 2,919 omitted in CP-2; one contradiction in CP-8.
- Both: heavily hedged, long appendix tables that repeat "Not supplied".

## Issuer report

- Both deliveries have all 11 blocks populated, nothing unplaced, the same structure.
- In both, the front-page call reads "Assessment pending": neither shows the Requires More Work
  recommendation that CP-3 and CP-6 give.
- The financials grid has 83 rows on medium and 16 on high, and the company profile 5 rows against 1,
  both from how each CP-1 wrote its tables.
- The high run's report and handoffs are labelled `copilot-sol-medium` (run id and delivery scope), so
  a reader cannot tell from the report which effort produced it.

## Findings for the workflow, not for effort

- The checker's "Invalid Markdown table header" refusal named no line; it stopped both runs at CP-5,
  as it stopped CP-1D on 2026-11-12 (`tdg-mixed-effort-comparison.md`). With the line and the cell
  counts in the message (`08df6a4`), CP-5 was accepted in both relaunches.
- A stopped module cannot be resumed and a new run cannot reuse accepted handoffs; the pick-up here
  was a manual bypass in copies.
- The run id and delivery scope do not record `--high-modules`.
- The front-page call does not pick up the recommendation.

## Scope and limits

- One run per effort level; one issuer, one date, one route; web search off.
- The quality read was done by three reviewing agents (Opus), each on a group of modules, checking a
  sample of figures against the 10-K source text and redoing computed values. No person has read the
  handoffs or opened the library pages.
- Not checked: every row of the financial statements tables; the upside cases; all of high's forecast
  rows; the annual-report PDF (no extracted text); the 10-Q pages cited in CP-DR; how the report
  renders.
