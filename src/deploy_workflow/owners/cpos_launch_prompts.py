"""The fixed text of a module's instructions: the reader and voice rules, the transport,
routing and per-module blocks, and the report selectors. Moved from ``cpos_launch``; the
launcher re-exports every name.
"""

from collections.abc import Sequence
from typing import get_args

from deploy_vii.business_context import Category
from deploy_workflow import confidence
from deploy_workflow.credit_os_chips import MODULE_NAMES
from deploy_workflow.handoff_delivery import MarkdownRoute
from deploy_workflow.owners import cp2g, cpos_forecast
from deploy_workflow.owners import cpos_cp1_check as cp1_check
from deploy_workflow.owners.cpos_launch_tables import (
    MONEY,
    OwnerTable,
    _adjusted,
    _chart_header,
    _owner_table,
)

# The user's Microsoft 365 Copilot custom instruction (supplied 2026-11-05, every clause kept),
# plus the one line the 2026-11-11 ruling (decision 8) adds: a persona that applies to every module.
READER_PERSONA = (
    "You are a senior credit research analyst at a leading credit fund, specialising in high "
    "yield credit and leveraged loans. Your research is used throughout the firm for key "
    "investment decisions; it is presented to senior credit committees and affects portfolio "
    "management. Your findings are institutional-grade, deeply analytical and data-dense, fully "
    "reasoned with explicit links from data to risk to credit implication. Say nothing generic "
    "unless it is tied to issuer-specific mechanics. Write in a detailed, structured style "
    "grounded in the provided data, and say when information is insufficient. State explicitly "
    "when information comes from external sources. Lead with the judgement; use data to support "
    "it, not to narrate it.\n\n"
)
# Reader passages (ruling 2026-11-11, H1-H3, decision 8): the checker enforces the mechanical
# checks of `prose_checks`, not the judgement.
PROSE_PASSAGES = (
    "Reader passages. The reader is a portfolio manager or credit committee member who has not "
    "read the source documents. After the analysis is finished, open `## Findings` with these "
    "four sections, each exactly once, in this order, before any other `## Findings` content:\n"
    "- `### Bottom line`: one or two paragraphs. The first sentence states this module's view "
    "and its consequence for creditors, in at most 45 words. Start it with a word, not a figure "
    "or a symbol. The whole Bottom line is at most 180 words.\n"
    "- `### Key findings`: one paragraph or one list item per finding, each starting with the "
    "judgement; give figures only where they move the view.\n"
    "- `### Contrary evidence and what would change the view`: prose giving the strongest "
    "evidence against the view and what would change it.\n"
    "- `### Limitations`: a bulleted list, one limitation per item, each saying which "
    "conclusion it changes and how. A limitation that changes no conclusion goes in the "
    "`## Gaps` table instead; if no limitation changes a conclusion, write one item naming "
    "this module: `- No limitation changes the conclusions of <plain module name>.` CP-OS "
    "refuses a limitation that any handoff accepted earlier in "
    "this run already states, so word each limitation for this module's own conclusion.\n"
    "Everything else in `## Findings` (method sections, registers, tables, report selectors) "
    "follows `### Limitations`; registers are written as tables, and all of its content is "
    "exact. If this module is blocked, write only "
    "`### Bottom line` of these four sections; a blocked module's `### Bottom line` begins "
    "exactly `Not assessable: ` followed by why (the exact words that mark it blocked), and a "
    'module that is not blocked must not use the words "not assessable" in its Bottom line. '
    "The report selectors below are still each written exactly once even if blocked: a "
    "table selector keeps its exact table header with one row stating not assessable "
    "(as a table row, in its table), and a prose selector holds one sentence saying so. Where the "
    "credit-research reading order's opening H3 or front sequence (the 90-150 word view, "
    "quantified drivers and front metrics table) differs from these passages, these passages "
    "govern; its table and appendix rules still apply after `### Limitations`, except that the "
    "report selectors' exact headings and table headers govern over the reader layer's table "
    "rules (6 columns and 8 body rows).\n\n"
)
# Sent to every module that is sent the canon's Analytical appendix section: that section says
# `## Analysis` and an appendix heading, while a handoff has the fixed H2s and CP-OS refuses an
# added `## Analysis`. There is no appendix-specific check. Demoting a report heading to `####`
# under the appendix heading is refused for `Bottom line` (the first-`###` check) and for the
# selector headings (`Map: ...`, `Confidence inputs`; the exact-heading checks), but is not
# refused for `Key findings`, `Contrary evidence and what would change the view` or
# `Limitations`. Adding `## Analysis` as an H2 is refused (the six-H2 check).
APPENDIX_HEADING_NOTE = (
    "Where the canon's Analytical appendix section says `## Analysis`, this handoff's section is "
    "`## Findings`: write the appendix heading as a `###` heading there, after `### Limitations`; "
    "the other required `###` headings stay `###` and are not nested under it.\n\n"
)
DATA_PASSAGE = (
    "Reader passage. The reader is a portfolio manager or credit committee member who has not "
    "read the source documents. Open `## Findings` with `### Bottom line`: one or two "
    "paragraphs whose first sentence states this module's view and its consequence for "
    "creditors, in at most 45 words; the whole Bottom line is at most 180 words. If this module "
    "is blocked, its `### Bottom line` begins exactly "
    "`Not assessable: ` followed by why (the exact words that mark it blocked); a module that "
    'is not blocked must not use the words "not assessable" in its Bottom line. Your tables '
    "follow as the main content, unchanged and exact.\n\n"
)
VOICE_RULES = (
    "- Write evidence, risk mechanism and credit implication as ordinary sentences, never as "
    "labels (no `Evidence:`, `Mechanic:` or `Implication:` lead-ins). This overrides method "
    "templates that write `Evidence:`, `Risk Mechanic:`, `Credit Implication:` or similar "
    "labels in prose or registers: write those as sentences.\n"
    "- In the reader passages write no module code, page number, bracket, chip, hash, or "
    "table, register or calculation ID in a sentence. Name a source in words only when it "
    "matters to the argument.\n"
    "- End a paragraph or list item that rests on a source, an upstream handoff or a "
    "calculation with a Basis line: its last line, with no blank line before it, starting "
    "exactly `Basis: `, items separated by `; `, with an optional final full stop. An item is "
    "`<source file name>`, `<source file name>, page <n>` or `<source file name>, pages "
    "<n>–<m>` (the file name exactly as listed in `## Sources`); `<plain module name> (<code>)` "
    "for an upstream handoff, for example `Liquidity (CP-2D)`; or `calculation <id>` for a row "
    "of this handoff's `## Calculations`, whose table has a column headed `ID` or ending ` ID` "
    "holding that id. A paragraph that rests on none of these has no Basis line. Write the "
    "Basis line on one line, never wrapped.\n"
    "- In the reader passages give every figure its currency or unit, with at most two "
    "decimals: `USD 1,250 million`, `$3.2bn`, `3.1x`, `61 bp`, `45%`, `18 months`. The accepted "
    "units are exactly: %, x, bp, bps, basis points, percentage points, pp, times, notch(es), "
    "day(s), week(s), month(s), quarter(s), year(s), or a currency code or symbol before the "
    "figure; the scale words thousand, million, billion, trillion, k, m and bn are accepted "
    "only with a currency. Any other number (a count of 100 or more, a model, section or "
    "index number) does not belong in a reader sentence: reword it in words or put it in a "
    "table. Never round an exact value to fit the two-decimal rule: an exact value with more "
    "decimals stays in a table. A coupon with more than two decimals (6.375%) is named by "
    'the note\'s maturity and rank instead ("the 2029 secured notes"). Keep a figure and its '
    "currency on one line. Years, dates, "
    "period labels (`Q3`, `FY2024`, `LTM`, `9M`) and whole counts below 100 need no unit. "
    "Write a range with the unit on both ends (`100 bp to 150 bp`). This overrides any method "
    "rule against bare figures or for `{ref|unit}` references in text fields: those belong to "
    "the JSON transport.\n"
    "- Every figure in a reader passage must also appear in the handoff's tables or "
    "`## Calculations` with the same sign, unit and scale.\n"
    "- In reader passages, when the documents do not state an item, say so in words; the "
    "`[Insufficient Information]` tag belongs in tables only. In sentence text write "
    '"not established" in plain words instead of the tag.\n'
    "- A table that cites sources has a column headed `Source` naming the file and page in the "
    "Basis item form. Raw locators, hashes and IDs stay in `## Sources`, "
    "tables and Basis lines. Write a register as a table; a register written as bullets or prose "
    "follows the sentence rules (no bracket tag, no page locator, no ID).\n"
    "- Keep `## Request` to the issuer, as-of date, pathway and scope, in at most three "
    "sentences.\n"
    "- When you quote year-end net debt, net leverage or cash from Financial foundation and its "
    "`Post-balance-sheet adjustments` table has a row for an event, state the pro forma figure "
    "beside it, with its unit and the event's date. When the table says none was found, add "
    "nothing. When Financial foundation does not state the pro forma figure, say it is not "
    "established; never work one out yourself.\n"
    "- In every sentence under `## Findings`, `## Calculations` and `## Gaps`, write for the "
    "reader, not for the pipeline. Write no module code, page locator, bracket or hash, and "
    'none of these words: "handoff", "this transport", "the pack", "fact pack", "source pack", '
    '"canonical", "re-anchor", "helper script", "upstream module", "downstream" before module, '
    "owner, work, analysis or use, a snake_case token or a CAPS_WITH_UNDERSCORE token. Name "
    "the document (for example the 2024 annual report), the module by its plain name or the "
    "analysis instead. Tables, fenced blocks, Basis lines and the chart, map, event and "
    "forecast input sections are not sentence text.\n"
    "- Refer to another module only by its plain name from this list, never by its code or "
    "an invented name: "
    + "; ".join(MODULE_NAMES.values())
    + ". In a Basis item the form stays `<plain module name> (<code>)`.\n"
    "\n"
)
# Sent only to a module that is asked for a chart table or a map (decision 11 of 2026-11-12).
CHART_NOTE_RULE = (
    "After each `### Chart data:` table write one sentence stating the main qualification a "
    'reader needs to read the figures correctly, or "No qualification." if there is none.\n\n'
)
MAP_TEXT_RULE = "Text in a map node or edge is at most 60 characters.\n\n"
# Sent only to a module whose method carries the score (decision 9 of 2026-11-12).
CONFIDENCE_RULE = (
    f"Write the inputs for your confidence score in `### {confidence.HEADING}`, listed with the "
    "report selectors below; the score and band are computed from it by Python, and the section "
    "is a data section, not sentence text. A blocked module writes one row in it instead, "
    "`| Not assessable | Not supplied: <reason> |`, and no score is computed.\n\n"
)


# Every module (owner, 2026-11-10, "Fix all"). Retained run cpos-tdg-sol-medium-all-001 and the
# 2026-11-10 inbox run: CP-1D, CP-3 and CP-5 blocked only for want of an acceptance receipt or a
# helper script's output, neither of which exists in this transport; only CP-2G had been told so.
TRANSPORT_RULES = (
    "Acceptance, helper scripts and entry values in this transport: CP-OS checked every handoff it "
    "supplies before passing it on, and pins each by its sha256. That check is the acceptance, "
    "validation and lineage the method asks of an upstream handoff: do not block for want of an "
    "acceptance receipt, invocation digest, settled-head verification or fresh snapshot. The "
    "method's helper scripts (`prepare_invocation.py`, `validate_handoff.py`, "
    "`completeness_check.py` and any other `scripts/*.py`) cannot be run "
    "here: do each check or calculation yourself, with `calculate` and by the rules in the "
    "method block, and do not block for it. Never mention the scripts, the tooling or anything "
    "that could not be run anywhere in the handoff. Do not state a confidence score, a "
    "confidence band or a QA status: this overrides the method's `qa_status`, confidence score "
    "and band fields, its Audit Summary score and its helper-script steps, so leave those fields "
    "and steps out. Python computes any score and band the report shows; a claim's own "
    "confidence label, where the method asks for one, is still written. A companion file "
    "the method names that "
    "is not in the method block below is unavailable; do not block the module for it. CP-OS "
    "supplies only the handoffs of the modules the registry "
    "names as this module's producers (CP-5: every analyst before it); an upstream module the "
    "method names that is not supplied is unavailable in the same way. Where the method relies on "
    "something unavailable, say in the Limitations passage or under `## Gaps`, in plain words, "
    "what could not be established and why it matters, without naming the file, script or "
    "module code. Nobody can answer a "
    "question during this run: take each entry "
    "value from the context and the supplied handoffs, then the method's declared safe default; "
    "where neither gives it the value is missing, so block only the decision the method ties to "
    "it. A supplied handoff that itself reports Blocked or a gap is a real limitation: restrict "
    "only the work that depends on it. Missing evidence still blocks exactly what the method says "
    "it blocks.\n\n"
)
# Every module, directly after TRANSPORT_RULES. Owner, 2026-11-13: "inter module communication
# should [be] handled by orchestrator, so does not need to be held in the instructions". The last
# sentence is the controller's (T4 ruling R4): the methods' own validators (`required_register_ids`,
# `appendix_contract`, the lossless profile, `completeness_check.py`) are never run here, but
# TRANSPORT_RULES has the module do their checks itself, and those would restore what is cut.
ROUTING_RULES = (
    "Routing in this transport: CP-OS chooses which modules run and in what order, gives each "
    "module the handoffs it needs and keeps every handoff; no reader acts on a recommendation "
    "about what to run next. This overrides every method instruction to return or recommend a "
    "next command, keep a Master Index, managed workspace, export record or run command sheet, "
    "map upstream or downstream dependencies, file a research request or brief, or write a "
    "register whose rows are addressed to receiving modules (cross-module handoff, consumer "
    "actions, analytical consumption, event use, downstream readiness) or the tables "
    "`cp2g.cp_model_forecast_drivers` and `cp2b.cp_model_catalysts`: write none of them. Under "
    "`## Next module` write only: `The orchestrator selects the next module.` A restriction on "
    "how your results may be used is a limitation: state it in `### Limitations` or `## Gaps`, "
    "in plain words. Every figure in a reader passage must still appear in a table you write or "
    "in `## Calculations`. Nothing excluded here or in a `Register scope` section is required by "
    "the method's `required_register_ids`, `appendix_contract`, lossless profile or completeness "
    "check, or the canon's Analytical appendix rule: do not restore it or block for want of it.\n\n"
)
# Only the modules in REGISTER_SCOPE_MODULES, directly after ROUTING_RULES: what the presence check
# (`register_issues`) asks of every register the scope section does not exclude.
PRESENCE_RULE = (
    "Write every other register the method requires under a heading that starts with its id or a "
    "`<!-- table-id: -->` tag that carries it; one with nothing to report has one row "
    "`Not supplied: <reason>`, never left out; a module that stops at its gate states "
    "`module_status: Blocked` in the front matter and writes the gate register only.\n\n"
)
# CP-5 only: it audits the other modules' handoffs. The first line is the marker the tests look for;
# `{lines}` is one `- <module>: <registers>` line per upstream module that has a scope section.
UPSTREAM_SCOPE_NOTE = (
    "Register scope of the handoffs you audit, in this transport:\n"
    "CP-OS told each module below not to write the registers listed, so their absence is not a "
    "finding: do not report it as a gap, a missing register, an issue or a must-fix, do not "
    "lower the clearance for it, and do not ask for it to be restored.\n"
    "{lines}\n"
    "The routing rule above holds for every module in the same way: no Master Index, run command "
    "sheet, `## Next module` recommendation, cross-module handoff, consumer actions, analytical "
    "consumption, event use or downstream readiness register and neither of the tables "
    "`cp2g.cp_model_forecast_drivers` and `cp2b.cp_model_catalysts` was asked for, so their "
    "absence is not a finding either.\n\n"
)
# CP-2A only. Its two methods disagree on who sets the stress sizes; run tdg-forecast-005 followed
# the SKILL, gave no shock, and CP-2G had no stress case to compute. The stress design text is
# the later correction (LEAD adaptation, ruling Q2), and the owner allowed labelled judgment for
# CP-2G's drivers on 2026-11-10 ("Yes, allow judgment").
STRESS_BLOCK = (
    "Stress design: where the method sections below differ on stress magnitudes, "
    "`CP-2A_STRESS_DESIGN_CPOS.md` governs. You choose the base period, the scenarios, the "
    "shock sizes and the watch levels as labelled analyst assumptions (`Analyst Interpretation`, "
    "confidence never High), each anchored to a stated figure (a decline the sources report, a "
    "calculated break point, a disclosed rate exposure): name the anchor and what the assumption "
    "leaves out. A labelled, anchored assumption is not the invented or unsupported stress "
    "magnitude the other sections forbid; an unlabelled or unanchored one still is. State at least "
    "one scenario as a pair, an EBITDA decline and a cash-interest rate increase, each a fraction "
    "from 0 to 1 with at most four decimal places, so a forward model can apply it.\n\n"
)
# CP-0 only. The skill's preparation phase assumes a runtime that lists and hashes the sources
# itself; here the launcher did, before the call. The two rules after it are the later Deploy V
# corrections in the caos-databricks copy of the skill (D31 V4, G1-18); the skill sent is older.
CP0_BLOCK = (
    "Source readiness here: the launcher has already listed, hashed and pinned the sources "
    "before this call, so the preparation the method describes is done. Do not write the "
    "registers P1, P2, P4, P6, P7 and P8. Do not write T7 or T8: CP-OS orders the modules. Write "
    "P3 and the readiness tables T1 input gate, T2 source register, T4 content-to-module map "
    "and T6 evidence trace. State any missing document under `## Gaps`. A result is "
    "CONDITIONAL only for a source the "
    "effective-source set does not carry. An upstream analytical handoff that has not been "
    "produced yet is never a readiness ground and never a `CONDITIONAL` condition: modules are "
    "put in order by navigation, not by readiness. The package, parse and hash checks were done "
    "by the launcher: record no result for them. When no "
    "objective is stated, the objective is the selected pathway's use case; record it in T1 and "
    "assess readiness against it.\n\n"
)
# CP-DR and CP-1C, when the context's peer source is CP-DR and both run (cpdr.md, "The peer pack").
# Owner, 2026-11-10: "Cp-1c is supposed to get that information from cp-dr by default".
PEER_PACK_BLOCK = (
    "Peer pack: the context sets `valuation.peer_source` to `cp_dr_public` and CP-1C is in this "
    "run, so this run requests the peer pack with CP-1C as its consumer. Inside `## Findings` "
    "write TDR.4 (candidate peers), TDR.5 (alignment observations: period, definition, currency, "
    "segment) and TDR.6 (located figures, one row per peer and operand: `revenue`, `ebitda`, "
    "`debt`, `interest`, `ffo`, each with unit, currency, period end, source locator and a "
    "verbatim quote), as your method's PEER PACK section describes them. "
    "Use every source this run holds "
    "that is not the issuer's own document, and any research or web tool this environment gives "
    "you. Name no peer and type no figure from memory. Where no peer evidence can be reached, "
    "still write the three tables, each holding one row whose `peer_id` is `none` (row header "
    "`none.none`) and whose text cells say what was searched and that nothing was found; that row "
    "cites its TDR.2 gap row.\n\n"
)
PEER_READER_BLOCK = (
    "Peer source: the context sets `valuation.peer_source` to `cp_dr_public`, so take the peer set "
    "and its figures from the CP-DR handoff's TDR.4, TDR.5 and TDR.6 before any other discovery. "
    "You own inclusion, comparability, normalisation and every statistic. Block the benchmark for "
    "want of peers only when those tables hold no usable peer, and say so.\n\n"
)
# Goes into CP-2G's instructions before METHOD_MARK, never into the method block.
UNIT_RULE = (
    "State `currency` and `scale` in every block, as the statements print them (`1000` for "
    "thousands, `1` for millions), and state every amount in the block in that one unit "
    "exactly as printed; an amount printed in the other unit is stated as missing, with the "
    "reason, not converted. "
)
FORECAST_BLOCK = (
    f"Forecast inputs: write `{cpos_forecast.HEADING}` inside `## Findings`, holding exactly "
    "one fenced json block and no other fence. You state "
    "inputs only; Python computes every forecast figure, so put no forecast figure in the block. "
    "`currency` is the three-letter code of the currency CP-1's statement tables are printed in "
    "(`USD`, `GBP`, `EUR`), and `scale` is `1` when they print millions of it and `1000` when "
    "they print thousands; every amount in this block is stated in that one currency and unit, "
    "exactly as CP-1 prints it, and Python divides by `scale`, so every published figure is "
    "millions of that currency. Do not convert an amount yourself. "
    + UNIT_RULE
    + '`base` holds exactly these ten operands, each `{"amount": "<decimal>", '
    '"reason": null, "row": "<label>", "period": "<header>"}` or '
    '`{"amount": null, "reason": "<why CP-1 does not state it>"}`: '
    f"{', '.join(cp2g.OPERAND_METRIC)}. "
    "`row` is the exact first-cell text of the row of one of the CP-1 handoff's tables that you "
    "read the amount from, and `period` the exact header text of that table's column (for "
    'example `"row": "Net sales", "period": "FY2024"`). Name the cell of every operand that has '
    "an amount by `row` and `period` and nothing else. Take a balance from a row under a "
    "period column (`FY2024`, `H1 2025`), never from a column headed `LTM …` and never from a "
    "table with one row per period (CP-1's `Chart data:` tables and `Net debt data`); where "
    "CP-1 prints the balance only there, state the operand as missing with that reason. "
    "`interest` is interest paid in cash in the base period; where CP-1 prints only interest "
    "expense you may name that cell and must say in `scope_limits` that interest is interest "
    "expense, not cash paid. "
    'Copy the amount as that cell prints it (with `"scale": 1000` a cell printing '
    '2,620,995 is `"2620995"`; at most nine digits and one decimal place); for interest, taxes '
    "and capex "
    "write the positive magnitude whatever sign the cell shows; for working capital write the "
    "cell's value with its sign reversed (a cell printing (45), an investment, is 45; a cell "
    "printing 45 or +45, a release, is -45). A figure in CP-1's prose, a basis line or its "
    "sources is not a cell: an amount CP-1 prints in no table cell is stated as missing, with "
    "the reason. An amount CP-1 prints only in the other unit (for example revolver availability "
    "in millions where the statements are in thousands) is stated as missing, with the "
    "reason; do not rescale it. Where CP-1 prints the amount under more than one column, name "
    "a column headed by a reporting period (`FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`): the "
    "Forecast page shows history only for a line named under such a header. `base_drivers` is "
    "the method's base-case driver "
    "submission (revenue_growth, ebitda_margin, capex_pct_revenue, tax_wc_pct_revenue, "
    "interest_rate, dividends, debt_repayment; each with `values` for the three forecast years, "
    "`category`, `rationale` and `limitation`). Each driver's `values` are three decimal strings, "
    'one per forecast year (for example ["0.05", "0.04", "0.03"]), each rounded to at most four '
    'decimal places (a ratio of 0.48022670 is written "0.4802"); the `dividends` and '
    '`debt_repayment` values are amounts in the block\'s unit (with `"scale": 1000`, 20 '
    'million is `"20000"`, at most one decimal place) and every other driver is a ratio and is '
    "never scaled; `category` is exactly one of "
    f"{', '.join(f'`{c}`' for c in get_args(Category))}. When the method gives no forecast "
    "(for example a blocked dependency), still write the block, with every driver's `values` as "
    "`[null, null, null]`. `downside_shock` is "
    '`{"ebitda_decline": "<0 to 1>", "rate_increase": "<0 to 1>"}`: both values are copied '
    "unchanged from one CP-2A scenario row; `rate_increase` is that row's proportional "
    "cash-interest increase, never a yield change; null when no shock was supplied; Python "
    "applies it to your downside drivers, or to the base drivers when you set none. "
    "`upside_drivers` and `downside_drivers` are your own upside and downside cases: each holds "
    "only the drivers that differ from base, in the same driver form (every other driver is "
    "inherited from base), or null when you set no such case. "
    "`facilities` is optional: state it when CP-1 prints the debt facilities' balances and rate "
    "terms, otherwise write null. Each row is "
    '`{"name", "balance", "fixed_rate_pct", "spread_pct", "floor_pct", "reference_rate", '
    '"annual_amortisation", "maturity"}`. `balance` is in the block\'s unit and `fixed_rate_pct`, '
    "`spread_pct` and `floor_pct` are percents, each copied exactly as CP-1 prints it; CP-1 must "
    'print each rate with its % sign (a 9.500% coupon is "9.500"). A fixed-rate facility states '
    "`fixed_rate_pct` and null for the other rate fields; a floating-rate facility states "
    "`spread_pct`, `floor_pct` or null, and `reference_rate`, your assumed reference rate for "
    "each forecast year as three decimal fractions "
    '(4% is "0.04", not "4"); the reference rate (or the floor, when higher) plus the spread '
    "must be between 0% and 30% in every year. The facilities' "
    "scheduled repayments over the three years must not exceed base debt. "
    "`annual_amortisation` is in the block's unit, a year, or null when CP-1 states none; "
    "`maturity` is YYYY-MM-DD or null. A row's `balance` is its drawn principal. Leave out a "
    "facility whose balance CP-1 prints only in the other unit. At most 40 rows; names are "
    "unique ignoring case; balances may total at most 1.25 times base debt; `fixed_rate_pct` is "
    "at most 30, `spread_pct` at most 20 and `floor_pct` at most 10; `reference_rate` values have "
    "at most four decimal places. When `facilities` is stated Python computes cash interest on "
    "those facilities and scheduled repayment from it; debt not in a row bears interest at your "
    "`interest_rate` driver and is not repaid; the `debt_repayment` driver is not used, so do "
    "not vary it in `upside_drivers` or `downside_drivers`. "
    "`years` is three consecutive fiscal years, each "
    '`{"year": <int>, "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}`. '
    "`scope_limits` is a list of text limits. Set `schema_version` to "
    f"`{cpos_forecast.SCHEMA_VERSION}`.\n\n"
    # Live run tdg-forecast-001 (2026-11-10): with no command qualifier the method's entry protocol
    # found no forecast horizon and blocked, and it named the helper scripts as a second gate.
    "Entry values: this run's command is `Run CP-2G [forecast horizon: the three fiscal years "
    "after the base period] [base period: the current period the context names] "
    "[cases: base/upside/downside]`. CP-OS has locked these: do not ask for them and do not block "
    "the forecast for them. The horizon is the block's `years`. The method's helper scripts "
    "(`prepare_invocation.py`, `validate_handoff.py`, the scoring script) cannot be run in this "
    "transport: do each check yourself, with `calculate`, and do not mention the scripts in the "
    "handoff. That, and the lack of an acceptance receipt for a handoff "
    "CP-OS supplied, is not a reason to block.\n\n"
    # Owner, 2026-11-10 ("Yes, allow judgment"): run tdg-forecast-002 gave no driver at all
    # because the filings carry no numeric three-year guidance.
    "Drivers: give a value for every driver in every forecast year. Where the sources state a "
    "number, use it under its category. Where they do not, give your own judgment as "
    "`Analyst Interpretation`, anchored to a stated figure (the midpoint of a guidance range, "
    "CP-1's latest-year ratio carried forward, a scheduled maturity or a declared payment): name "
    "the anchor in `rationale` and what the judgment leaves out in `limitation`. A judgment is "
    "an input to a mechanical forecast, not a finding. Leave a driver's values null, as "
    "`Insufficient Information`, only when no stated figure can anchor it.\n\n"
)
# Goes into CP-1's instructions whenever a forecast is wanted, with or without CP-2G: the period
# table lets Python date-check the last twelve months. CP-1 states no new figure in it.
PERIOD_TABLE_BLOCK = (
    "Period table: inside `## Findings`, print one table whose header is exactly "
    "`| Period | Start | End |`, with one row for every period column header you use in your "
    "financial tables. `Period` is that header's text exactly as you print it (for example "
    "`9M 2025` or `FY2024`); `Start` and `End` are the period's first and last day as "
    "YYYY-MM-DD. Head period columns as `FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`, the year "
    "being the fiscal year the period belongs to. Print each statement line once, in one table "
    "that has a column for every period you state for it; a line split across two tables "
    "cannot be combined. Where a table states its unit, write it as the three-letter currency "
    "code and `millions` or `thousands` (`USD millions`), the same in every statement table; "
    "the `Chart data:` tables and `Net debt data` keep the unit their own rule gives. "
    "Python uses this table to check that the last twelve months are twelve months; add no "
    "figure to it. Print every balance the forecast needs (total debt, cash, undrawn committed "
    "facilities) as a row of a table whose columns are those period headers, each a plain "
    "number at that period's end: the `H1 2025` column holds the 30 June 2025 balance. Put the "
    "date in the row label or the Source, not in the cell. A column headed `LTM …` holds flows "
    "only, never a balance.\n\n"
)


# Goes into CP-1's instructions when PERIOD_TABLE_BLOCK is not sent: the check needs the table.
PERIOD_REQUIRED_BLOCK = (
    "Period table: inside `## Findings`, print one table headed "
    f"`| {' | '.join(cp1_check.PERIOD_HEADER)} |`, a row for each period column "
    "header of your statement tables (`Period` as printed, for example `FY2024`; `Start` and "
    "`End` as YYYY-MM-DD); add no figure.\n\n"
)


def _fixed_rows(spec: cp1_check.StatementSpec) -> str:
    optional = f"; optional {', '.join(f'`{r}`' for r in spec.optional)}" if spec.optional else ""
    return f"`### {spec.heading}`: {', '.join(f'`{r}`' for r in spec.fixed)}{optional}"


# Goes into CP-1's instructions on every run: what the acceptance check reads, rendered from the
# constants the check itself uses, so the words cannot drift from it.
CP1_CHECK_BLOCK = (
    "Checked tables: CP-OS recomputes your figures at acceptance and sends back any that fail, so "
    "print these inside `## Findings` (only there, outside code fences), each heading exact and "
    "written once in the whole handoff, followed by blank lines, then its table (header and "
    "separator rows first), then a blank line. Nowhere write an HTML comment, another heading or "
    "bold line with a checked heading's words, or a line break other than a newline. Each "
    "statement table is headed `| Line item | <one column per period> | Unit | Basis | Source |`; "
    "a period header is "
    f"exactly one of {', '.join(f'`{f}`' for f in cp1_check.PERIOD_FORMS)}; the Unit of a fixed "
    f"row is a currency code and `millions` or `thousands` (`{cp1_check.UNIT_EXAMPLE}`). Keep the "
    "issuer's own lines and labels and add these rows beside them, labels exact, one row each: "
    + "; ".join(_fixed_rows(spec) for spec in cp1_check.STATEMENTS)
    + f". A cell is {cp1_check.PLAIN}; a missing figure is never zero, and no words go beside a "
    "number. `Total Debt` is the balance-sheet carrying value, current plus long-term, net of "
    "issuance costs and discounts. `Net Cash Change`, the three activity totals and `FX Effect "
    "on Cash` are signed (an outflow is negative); `Cash Interest Paid` is the positive amount "
    "paid.\n"
    f"`### {cp1_check.REGISTER_HEADING}`, headed `| {' | '.join(cp1_check.REGISTER_COLUMNS)} |`, "
    "one row for each of these Metric Names and each period in the leverage and interest-cover "
    "tables: "
    + ", ".join(f"`{m.name}`" for m in cp1_check.METRICS[:3])
    + "; and, only when the issuer states an adjusted EBITDA, "
    + ", ".join(f"`{m.name}`" for m in cp1_check.METRICS[3:])
    + ". Where `EBITDA (Reported)` is `Not supplied:` in every period and `EBITDA (Adjusted)` is "
    "stated, head the leverage and interest-cover columns with the adjusted names instead; never "
    "mix the two. `Period` is the Period cell of the "
    "`Net debt data` row the ratio belongs to (`FY2024 / 2024-09-30` or the date alone, which "
    "must be the `End` of a Period-table row), "
    "`Unit` is that row's Reporting unit, `Currency` the code. Numerator and Denominator Value "
    "are the plain figures of the statement tables and `Net debt data`; Calculated Value is "
    "numerator over denominator printed to exactly two decimal places, worked with "
    "`calculate`; a zero or negative denominator is "
    "`Not calculable: <reason>`.\n"
    f"`### {cp1_check.RECON_HEADING}` is specified by its selector below.\n"
    f"The {cp1_check.PERIOD_TABLE} (a row for every statement column, asked for separately) is "
    "the sixth table: a row is a fiscal-year row when its date is the "
    "`End` of that column's row there, whatever form its Period cell takes (an `FY2024 / date` "
    "cell must name a row and its `End`). The money unit is `US$m` when your statements are in "
    "USD, else their currency code and `m` (`GBPm`), in millions even where a statement prints "
    "thousands; the net debt, reconciliation and money chart tables and the register's fixed "
    "rows use it (the leverage and interest-cover tables stay `x`), and `Currency` is the "
    "statements' code. A figure in another currency is `Not "
    "supplied: reported in <unit>`.\n"
    "Refused, naming the row, both figures and the difference: a table or fixed row missing; a "
    "Unit, period header or Period not as above; a cell that is not a plain number or stated gap; "
    "a Calculated Value more than half a unit of its second decimal from numerator over "
    "denominator, or stated beside a gap operand; a figure stated on one side of a tie and a gap "
    "or nothing on the other: chart figure and Calculated Value, numerator and `Net debt data` "
    "Gross debt (or Net debt), and, for fiscal-year rows only (an interim EBITDA is a "
    "last-twelve-months figure, so interim rows have no statement tie), EBITDA and cash interest "
    "against their statement lines, and Gross debt and Cash against `Total Debt` and `Cash & "
    "Equivalents`, each in that fiscal year's statement column; assets that differ from "
    "liabilities plus any temporary equity plus equity, the cash flows plus any FX effect from "
    "the net change, or opening cash plus the change from closing cash (when the filing itself "
    "prints such a difference, write `Not supplied: <reason>` on the total it cannot support and "
    "add a line under `## Gaps`); a ladder that does not add to the principal, a `Debt maturing` "
    "gap beside a stated principal, principal plus reconciling items that is not the carrying "
    "value, or a carrying value that is not Gross debt. Correct whichever figure is wrong. If "
    "you are blocked, still print every table: each fixed row (one period column) with `Not "
    "supplied: <reason>` in each figure cell, the register with one row whose Metric Name is "
    "`Not assessable` and `Not supplied: <reason>` in every other cell, and the reconciliation "
    "row with `Not supplied: <reason>` in each figure, and the Period table with `Not supplied: "
    "<reason>` as Start and End (only while no table states a figure).\n\n"
)
# Goes into CP-1's instructions when the forecast is published without CP-2G (owner, 2026-11-11:
# "allow forecast to function with just relevant layer 1 modules"). Same JSON shape as
# FORECAST_BLOCK, so cpos_forecast has one code path; the model still computes nothing.
LAYER1_FORECAST_BLOCK = (
    f"Forecast inputs: write `{cpos_forecast.HEADING}` inside `## Findings`, holding exactly "
    "one fenced json block and no other fence, after your tables. You state inputs only; Python "
    "computes every forecast figure, so put no forecast figure in the block. `currency` is the "
    "three-letter code of the currency your statement tables are printed in (`USD`, `GBP`, "
    "`EUR`), and `scale` is `1` when they print millions of it and `1000` when they print "
    "thousands; every amount in this block is stated in that one currency and unit, exactly as "
    "your tables print it, and Python divides by `scale`, so every published figure is millions "
    "of that currency. Do not convert an amount yourself. "
    + UNIT_RULE
    + '`base` holds exactly these ten operands, each `{"amount": "<decimal>", "reason": null, '
    '"row": "<label>", "period": "<header>"}` or '
    '`{"amount": null, "reason": "<why you do not state it>"}`: '
    f"{', '.join(cp2g.OPERAND_METRIC)}. `row` is the exact first-cell text of the row of one of "
    "your own tables that you read the amount from, and `period` the exact header text of that "
    'table\'s column (for example `"row": "Net sales", "period": "FY2024"`). '
    "Name the cell of every operand that has an amount by `row` and `period` and nothing else. "
    "Take a balance from a row under a period column (`FY2024`, `H1 2025`), never from a column "
    "headed `LTM …` and never from a table with one row per period (your `Chart data:` tables "
    "and `Net debt data`); where you print the balance only there, state the operand as "
    "missing with that reason. "
    "`interest` is interest paid in cash in the base period; where CP-1 prints only interest "
    "expense you may name that cell and must say in `scope_limits` that interest is interest "
    "expense, not cash paid. "
    'Copy the amount as that cell prints it (with `"scale": 1000` a cell printing 2,620,995 is '
    '`"2620995"`; at most nine digits and one decimal place); for interest, taxes and capex '
    "write the positive magnitude whatever sign the cell shows; for working capital write the "
    "cell's value with its sign reversed (a cell printing (45), an investment, is 45; a cell "
    "printing 45 or +45, a release, is -45). Print your tables as "
    "you normally would; add nothing for this block. A figure in prose, a basis line or the "
    "sources is not a cell. An amount your tables print only in the other unit is stated as "
    "missing, with the reason. Where your tables print the amount under more than one column, "
    "name a column headed by a reporting period (`FY2024`, `Q3 2025`, `H1 2025` or `9M 2025`): "
    "the Forecast page shows history only for a line named under such a header. "
    "`base_drivers` is a run-rate base case and nothing more "
    "(revenue_growth, ebitda_margin, capex_pct_revenue, tax_wc_pct_revenue, interest_rate, "
    "dividends, debt_repayment; each with `values` for the three forecast years, `category`, "
    "`rationale` and `limitation`). Anchor every driver to a figure you state: carry the latest "
    "year's ratio forward, or use a scheduled maturity or a declared payment, and name the anchor "
    "in `rationale`. Add no analyst judgement beyond that run-rate. Each driver's `values` are "
    'three decimal strings, one per forecast year (for example ["0.05", "0.04", "0.03"]), each '
    "rounded to at most four decimal places; the `dividends` and `debt_repayment` values are "
    'amounts in the block\'s unit (with `"scale": 1000`, 20 million is `"20000"`, at '
    "most one decimal place) and every other driver is a ratio and is never scaled; `category` "
    "is exactly one of "
    f"{', '.join(f'`{c}`' for c in get_args(Category))}. Leave a driver's values null, as "
    "`Insufficient Information`, when no stated figure can anchor it; when none can, set every "
    "driver's `values` to `[null, null, null]`. Set `downside_shock`, `upside_drivers` and "
    "`downside_drivers` to null: there are no cases and no shock in this forecast. `years` is "
    'three consecutive fiscal years after the base period, each `{"year": <int>, "start": '
    '"YYYY-MM-DD", "end": "YYYY-MM-DD"}`. `scope_limits` is a list of text limits. Set '
    f"`schema_version` to `{cpos_forecast.SCHEMA_VERSION}`. This block does not change your "
    "findings or any table.\n\n"
)


# Goes into CP-8's instructions: which earlier run it compares with and where the pack is.
CP8_BLOCK = (
    "This run compares with an earlier run of the same issuer and pathway: {prior}. The "
    "comparison pack is source `changes.json` and the earlier run's delivered handoffs are the "
    "sources `prior/<module>.md`; the current run's handoffs are supplied as usual. Write the "
    "registers exactly as the method says. CP-OS checks every issuer row that holds a figure "
    "against the pack measure it names, every difference you print against the pack's, every "
    "module and every limitation ref of the pack for exactly one row, and the fixed Status and "
    "Cause lists, and sends the handoff back if one fails. The earlier run's handoffs and the "
    "pack are evidence for this module alone.\n"
    "For this module the Basis item forms above are replaced by these three: `<plain module "
    "name> (<code>)` for a handoff of this run, `<plain module name> (<code>), earlier run` for "
    "a handoff of the earlier run, and `Run comparison` for the comparison pack, with no page "
    "for a handoff. The files `changes.json` and `prior/<module>.md` are listed in `## "
    "Sources` and are never named in a Basis line.\n\n"
)
BRIDGE_RULES = (
    " Each row is one step: the first row is the opening amount and the last row is the closing "
    "amount; the rows between are the signed changes the method states (a negative number for an "
    "outflow), in the order the method states them. The opening plus those changes must reconcile "
    "to the closing at the precision the table states, or the table is sent back: state the "
    "missing step, never a plug. If the bridge cannot be stated, write `Not supplied: <reason>` "
    "in every Amount."
)


CURRENCY_RULE = (
    "An issuer reporting in another currency or scale writes "
    "`Not supplied: reported in <unit>` in monetary cells. "
)


def _and_list(names: Sequence[str]) -> str:
    return f"{', '.join(names[:-1])} and {names[-1]}" if len(names) > 1 else "".join(names)


def _none_rule(spec: OwnerTable) -> str:
    """The one sentence every row table (not a step table, which has its own) is sent for the case
    that its module has nothing to report; `_states_none` accepts exactly that row."""
    if not spec.columns:
        return ""
    if spec.none_text:
        return (
            f" If no such event is stated, write one row whose Event is exactly `{spec.none_text}` "
            f"(no other punctuation or wording), whose {_and_list(spec.columns[1:])} are each "
            "`\u2014`, with Reporting unit and Basis and limitation stated (say which sources "
            "were read)."
        )
    cells = "every cell" if spec.bare else "every cell before Reporting unit"
    return (
        f" If the handoff supplies none, write one row whose {cells} is `Not supplied: <reason>`"
        f"{'' if spec.bare else ', with Reporting unit and Basis and limitation stated'}: "
        "the module "
        "states none, and the page shows it as not established for this run."
    )


def _selector(route: MarkdownRoute | OwnerTable) -> str:
    if isinstance(route, OwnerTable) or route.kind == "chart":
        spec = _owner_table(route)
        if spec.scored:
            return (
                f"- `### {spec.heading}`: exactly one Markdown table headed "
                f"`| {' | '.join(confidence.HEADER)} |`, with one row for each of these inputs, "
                f"named exactly: {', '.join(confidence.INPUT_ROWS)}. "
                f"{', '.join(confidence.LINEAGE_ROWS)} are whole numbers (0 where none) of the "
                "material claims whose strongest evidence is of that lineage class; "
                f"{confidence.PRESENT_ROW} and {confidence.TOTAL_ROW} are whole numbers of the "
                "required fields (the source gate and the method's required schema fields) "
                f"present and in all, {confidence.TOTAL_ROW} at least 1 and not below "
                f"{confidence.PRESENT_ROW}; {confidence.GATE_ROW} is `pass`, `partial` or `fail`; "
                f"{', '.join(confidence.FINDING_ROWS)} are whole numbers of unresolved findings of "
                "that severity. Write no score, band or status."
            )
        if spec.bare:
            return (
                f"- `### {spec.heading}`: exactly one Markdown table headed "
                f"`| {' | '.join(_chart_header(spec))} |`, one row per "
                f"{'edge' if spec.edges else 'dated event'}. "
                f"Every cell is stated, never blank. {spec.rules}{_none_rule(spec)}"
            )
        others = [n for n in spec.numbers if spec.in_unit and n not in spec.in_unit]
        counted = [n for n in spec.numbers if n not in others]
        numbers = f" ({', '.join(counted)})" if counted else ""
        where = "in the Reporting unit the row states"
        if spec.chart_unit:
            where = f"in {spec.chart_unit}, with that as the Reporting unit"
        rest = (
            f" {', '.join(others)} is a plain number in the unit its rule states." if others else ""
        )
        twin = " (adjusted names where `Checked tables` allows)"
        return (
            f"- `### {spec.heading}`: exactly one Markdown table headed "
            f"`| {' | '.join(_chart_header(spec))} |`{twin if _adjusted(spec) else ''}, one row "
            f"per {'step' if spec.steps else spec.noun}. "
            f"Value cells{numbers} are plain numbers {where}, or `Not supplied: <reason>`.{rest} "
            + (CURRENCY_RULE if spec.chart_unit and spec.chart_unit != MONEY else "")
            + f"{'Every other cell is stated, never blank. ' if spec.columns else ''}"
            "Basis and limitation is never blank."
            + (BRIDGE_RULES if spec.steps else "")
            + (f" {spec.rules}" if spec.rules else "")
            + _none_rule(spec)
        )
    what = (
        "exactly one populated Markdown table under it." if route.kind == "table" else "prose only."
    )
    return f"- `### {route.heading}`: {what}"


CP3_MODE_LABELS = {
    "clo_screening": "CLO Screening",
    "single_name_rv": "Single-Name RV",
    "capital_structure_rv": "Capital-Structure RV",
    "watchlist_monitoring": "Watchlist Monitoring",
}
CP3_MODE_BLOCK = (
    "The user selected the execution mode {label} (source `context`, module_options.cp3_mode). "
    "Use it at Step 1; do not choose another.\n\n"
)
# CP-6 on every pathway that runs it (owner, 2026-11-15: "module cp-6A within cp-6 should be fully
# functional"; ruling 2026-11-15-full-assessment-cp3c-cp6a.md). Where the absorbed CP-6A phase's
# decision goes; `posture_issues` refuses a handoff without it. The method itself is unchanged.
POSTURES = (
    *("Include", "Avoid", "Resize-Reduce", "Resize-Increase", "Maintain-Hold"),
    "Requires More Work",
)
POSTURE_HEADING = "Portfolio posture"
CP6A_BLOCK = (
    "Portfolio debate: the method's absorbed CP-6A phase is part of this run. Write its "
    "registers T6E.4, T6E.6, T6E.7 and T6E.11 as you write the issuer debate's. Write its Final "
    "Sizing Posture, Exact Portfolio Constraint and CIO Final Memo in one `## Findings` section "
    f"headed exactly `### {POSTURE_HEADING}`, after `### Limitations`. Its first sentence is the "
    "method's formulation and starts exactly `Final Sizing Posture: ` followed by one of "
    f"{', '.join(POSTURES[:-1])} or {POSTURES[-1]}. The reader sentence rules apply to that "
    "section, and each of its paragraphs that rests on a source or a supplied handoff ends with "
    "its Basis line. Give the posture and the binding portfolio constraint as one of your Key "
    "findings. A handoff without that section or that first sentence is refused unless the "
    "module is blocked.\n\n"
)
DEEP_DEBATE_BLOCK = (
    "The user explicitly asks for a full debate (source `context`, "
    "module_options.cp6_deep_debate). Deep Debate Mode is ON.\n\n"
)
SOURCES_RULES = (
    "Write the issuer sources in `## Sources` as a table with the columns "
    "`Source | Document | Document date | sha256 | Use`. `Source` is the exact file name as "
    "supplied "
    "(it is the key that joins the row to the file; never shorten or reword it). `Document` says "
    'in plain words what the document is, for example "Annual report on Form 10-K for the year '
    'ended 30 September 2024". `Document date` is the date the document was filed or published '
    'if the document states it, otherwise "not stated". `sha256` is the exact hash and `Use` '
    "says what this module used it for. Do not list the run settings (the context file) as a "
    "source. A web page found by search is listed by the rules of this module's web section, "
    "which add a Source type cell.\n\n"
)
# The method block follows this line and runs to the end of a module's instructions.
METHOD_MARK = "Selected method, verbatim:\n\n"
