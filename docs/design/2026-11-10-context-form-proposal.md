# Context form proposal: progressive, module-aware (2026-11-10)

Proposal for review, not adopted. The working page is
[`docs/templates/context-form-proposal.html`](../templates/context-form-proposal.html). It opens from
disk and writes the same `context/1` file as `context-form.html`. The live form, the inbox copies and
the tests are unchanged.

Goal (owner, 2026-11-10): analysts should give each module the right context the first time, so that
fewer paid runs have to be repeated. Any change to the context means a whole new run. A resumed run
refuses changed sources or context (`owners/cpos_launch.py` 705-707, 863-864), and the inbox always
starts a fresh run folder (`inbox/runs.py` 150).

## 1. Module review: what each module takes from the context

**Inbox/launcher route** (what analysts trigger):
- The whole `context.json` is pinned as a source, and every model reads it as "the user's dated
  settings".
- Python itself reads only these fields: pathway, `issuer_id`, `issuer_name`, as-of, `case_kind` and
  aliases (`cpos_launch.py` 764-786, 816-823).
- So every declaration in the file reaches every module, including the attachments and the legal
  documents.

**Owner route** (`run_pathway`, `owners/*.py`): Python validators also read the fields below.

The modules run, in order, come from `deploy_vii.registry.plan` over each pathway's analytical
modules. CP-1A is added to Relative Value and Portfolio Decision as a required producer. CP-MODEL and
CP-8 are not launched.

| Pathway | Modules run from the inbox |
|---|---|
| Credit Snapshot | CP-0, CP-1, CP-1A, CP-2, CP-4, CP-3, CP-5, CP-6 |
| Earnings Update | CP-0, CP-1, CP-1B, CP-1D, CP-5 |
| Relative Value | CP-0, CP-1, CP-1A, CP-3D, CP-1C, CP-2, CP-2D, CP-3C, CP-3, CP-5 |
| Covenant & Refinancing | CP-0, CP-1, CP-1A, CP-2, CP-4, CP-2D, CP-3C, CP-5 |
| Distressed & Restructuring | CP-0, CP-1, CP-1A, CP-1C, CP-2A, CP-4, CP-2, CP-2G, CP-2H, CP-4C, CP-5 |
| Portfolio Decision | CP-0, CP-1, CP-1A, CP-2, CP-3, CP-5, CP-6 |

| Module | Context it uses | Without it, or when it is wrong |
|---|---|---|
| CP-0 Source readiness | attachments, legal_documents, issuer identity | Owner route: a declared attachment or legal document not in the pack refuses the review (`cp0_attachments.py` 60-85). |
| CP-1 Financial foundation | reporting_currency | Not USD: the chart strip reads "Not supplied" (US$m only). |
| CP-1B Earnings changes | current_period, prior_period, currency | Owner route: an unresolved current period refuses; a missing prior period is a gap (`cp1b.py` 251-271). |
| CP-1C Peer benchmark | valuation, as_of | `cp_dr_public` and `user_list` give "No peer figures" (`cp1c.py` 1569-1574). The automatic basis needs 3 admitted peers (at most 12 months old) or 3 precedents (at most 36 months) (`valuation_basis.py` 19-20). |
| CP-1D Earnings quality | management_bridge; an fy/q4 base | No bridge: every bridge cell is not applicable. |
| CP-2A Downside | cp2a pin; legal_documents (as read by the models) | tdg-forecast-003: a false `executed` blocked it; -004 with `none` came back Restricted. |
| CP-2D Liquidity | cp2d pin; facility currency | A facility in another currency is not calculable (no FX). |
| CP-2G Forward model | current_period (the forecast base) | Blank: no base period. Owner route: it needs an fy or q4 base. |
| CP-2H Ratings & triggers | ratings | No rows: Insufficient Information. Only S&P, Moody's and Fitch, one row per agency, on the agency's scale (`cp2h.py` 453-483). |
| CP-3 Security selection | quotes, deal talk | No quote and no talk: Insufficient Information. Talk only: capped below High. A quote older than 30 days is stale (`cp3_relative_value.py` 450). |
| CP-3C, CP-3D, CP-4C | their pins; quotes (CP-3D) | No quotes: CP-3D has nothing to read. |
| CP-4 Legal & covenants | legal_documents | `none`: the method stops ("No executed governing document"). `draft`: Provisional. |
| CP-6 Committee decision | portfolio_workbook (Portfolio Decision) | Gap. |
| CP-DR, CP-2E | research_questions, cutoff; the cp2e pin | In no pathway, so an inbox run never uses them. |

Stale wording in the current form:
- Pinned assumptions are built: owner route `pins.py`, and advisory on the inbox route.
- "USD fixed" for CP-2D is now wrong. Only a facility in another currency is not calculable.
- CP-8 "blocked without the prior decision" does not apply to the inbox.
- `cp_dr_public` is the default peer source, but it always gives CP-1C a gap.

## 2. What made runs repeat, and what the proposal does about each

1. **A legal declaration that did not match the folder (most costly).** In tdg-forecast-003 the
   context said `executed` for a folder of public filings. CP-2A blocked and CP-2G never ran. The
   relaunch with `none` (-004) cost a second run (`VERIFICATION.md`).
   - The question now reads "Which legal documents are in this folder?", with no preselection.
   - The `none` option says a 10-K exhibit index is not the agreement.
   - `executed` and `draft` need a tick confirming the file itself is in the folder.
   - The optional folder check flags an `executed` declaration with no agreement-like file name, and
     a `none` declaration while one exists.
2. **As-of date before the evidence.** In `cpos-tdg-sol-medium-all-001` (as-of 2024-09-30) CP-2G
   excluded the December-quarter results as not available at the as-of date.
   - A new optional field asks for the newest file's date.
   - The run counts as a limit if the as-of date is before that date, or not after the current
     period's (calendar) end.
   - The help text is corrected: source files are not date-checked; context entries are.
3. **Peer data.** CP-1C was blocked at the peer-data gate in the all-modules run.
   - Where CP-1C runs, the peer source has no default.
   - "I'll give peer figures" is marked as the only working choice.
   - Stale peers and precedents are flagged on the row.
   - Fewer than 3 admitted makes CP-1C a Gap.
4. **Periods.** Nothing ties the run type to the pathway: a Research run on Earnings Update leaves
   both periods optional.
   - Earnings Update now always uses the earnings run type, and that run type is offered only there.
   - Where CP-2G runs, the current period is required, with a note asking for fy or q4.
5. **Drops the inbox or launcher refuses** (free, but they cost a round trip):
   - An `issuer_id` over 40 characters: the form now caps it, and the automatic ID is cut at a hyphen.
   - Several cases a folder check can see:
     - two context files;
     - a context in a subfolder;
     - a `.docx`, `.pptx` or `.xls` file, or a name starting with `_` or `~$`;
     - an empty file;
     - an `X.htm` next to an `X.htm.jsonl`.
   - The "Before you drop" checklist names the right `inbox\<pathway>\` folder.
6. **Files the reader refuses, which the current form writes:**
   - a research question containing `|`;
   - pasted U+0085, U+2028 or U+2029 characters.
   Both are confirmed refused by `context.load_context`. The proposal stops them.
7. **A lost click.** When a blur adds a message, the Next button moves between mousedown and mouseup,
   and the click does nothing. This was seen in a browser test of the proposal; the current form uses
   the same pattern. The proposal defers that re-render until the click, for mouse and touch.

## 3. The design

- **Stages follow the run.** Purpose (pathway first, as plain-English questions with each pathway's
  modules), Issuer, Dates, Source files, then Market, Valuation, Assumptions and Questions, each shown
  only when a module in the run uses it, and finally Check & download.
  - A stage that holds loaded entries or problems is always shown.
  - Later stages stay locked while an earlier one has problems.
- **Every input says who uses it.** "Used by" chips use the reader names (Source readiness, Legal &
  covenants…), and each source item says what is lost without it.
- **Run readiness panel.** A client-side port of `run_expectations.RULES`, with dependency
  propagation through the registry edges, shows each module as Ready, Check, Gap, Limited or Will
  refuse, with the reason and the fix. Unanswered questions show as waiting, never as Ready.
- **Pre-flight.** The review lists the expected outcomes, with links to the stage that fixes each, and
  the notes still open. Download is blocked by errors, and needs one acknowledgement when limits remain.

**Form-only rules** (stricter than `context.py`, which still accepts files without them):
- issuer_id at most 40 characters;
- the Earnings Update pathway ⇔ the earnings run type;
- current_period required where CP-2G runs;
- the peer source chosen where CP-1C runs;
- a Yes/No answer for each attachment the pathway uses;
- the legal confirmation tick.

**Unchanged:**
- the `context/1` shape and key order;
- the `<html lang="en">` hook and `data-pathway` fixing;
- the `build()` and `fill()` globals;
- every reader bound, copied from the current form.

## 4. Decisions for the owner

1. Adopt as `docs/templates/context-form.html`? The inbox would then copy it. Two expectations in
   `tests/test_library_page_browser.py` `FORM_PROBE` would change:
   - the pathway is a card group, not the `#s1-pathway` select;
   - on the Earnings Update copy the run type stays `earnings`.
2. Should `context.py` mirror the form-only rules, or keep accepting hand-written files without them?
3. Should the launcher print its `expectations` (computed today but only read by tests), so a CLI run
   shows the same forecast as the form?
4. Owner route: CP-1D and CP-2D need an fy/q4 base (`period_basis.run_basis`), but an earnings update
   names quarters. Is that conflict intended?
5. CP-DR and CP-2E are in no pathway, so research questions and the cp2e pin have no effect from the
   inbox. The proposal hides both unless a loaded file holds them. Keep, remove, or add the modules to
   a pathway?
