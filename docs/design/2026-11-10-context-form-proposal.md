# Context form: progressive, module-aware (2026-11-10)

**Adopted 2026-11-10** (owner: "Approved"). The page is now
[`docs/templates/context-form.html`](../templates/context-form.html), which the inbox copies into each
pathway's `_template`. It writes the same `context/1` file as the form it replaced: three fixture
contexts give byte-identical output. Sections 1 to 5 are the review and design as proposed. Section 7
records what changed at adoption, after main's ruling that CP-1C takes its peers from CP-DR by default.

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
| Relative Value | CP-0, CP-1, CP-1A, CP-3D, CP-1C, CP-2, CP-2D, CP-3C, CP-3, CP-5 (with CP-DR before CP-1C when the peer source is `cp_dr_public`: section 7) |
| Covenant & Refinancing | CP-0, CP-1, CP-1A, CP-2, CP-4, CP-2D, CP-3C, CP-5 |
| Distressed & Restructuring | CP-0, CP-1, CP-1A, CP-1C, CP-4, CP-2, CP-2A, CP-2G, CP-2H, CP-4C, CP-5 (order on main `4ce88c2`; with CP-DR after CP-1A when the peer source is `cp_dr_public`) |
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
| CP-DR | research_questions, cutoff, peer_source | Joins Relative Value and Distressed when the peer source is `cp_dr_public` (main `a2f5e8e`): builds the peer pack CP-1C reads and answers the context's questions first. No web access in this transport: only files in the folder. |
| CP-2E | the cp2e pin | In no pathway, so an inbox run never uses it. |

Stale wording in the current form:
- Pinned assumptions are built: owner route `pins.py`, and advisory on the inbox route.
- "USD fixed" for CP-2D is now wrong. Only a facility in another currency is not calculable.
- CP-8 "blocked without the prior decision" does not apply to the inbox.
- `cp_dr_public` is the default peer source, and before main `a2f5e8e` it always gave CP-1C a gap.
  Since then CP-DR joins to supply the peers (section 7).

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
   - As proposed: no default where CP-1C runs, and "I'll give peer figures" marked as the only
     working choice. Superseded at adoption (section 7): `cp_dr_public` is the default again, CP-DR
     joins the run, and the form asks whether the peers' filings are in the folder.
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
- a Yes/No answer for each attachment the pathway uses;
- the legal confirmation tick.

**Unchanged:**
- the `context/1` shape and key order;
- the `<html lang="en">` hook and `data-pathway` fixing;
- the `build()` and `fill()` globals;
- every reader bound, copied from the current form.

## 4. Design language (after main `caeb622`)

The page now uses the Credit OS language of `apps/issuer-library/credit_os/web/screen.css`. It
follows the screens pass (`2026-11-10-screens-pass.md`): what a reader acts on leads, and production
detail is quiet, in a title, or behind a disclosure.

**Copied from `screen.css`:**
- the tokens (its lines 5 and 81);
- the Untitled UI component foundation: 40px buttons and fields with an 8px radius, 12px cards, pill
  badges and the focus ring;
- the New run patterns it still carries (`.run-stages` progress bars, `.run-field`, `.step-actions`,
  `.run-strip` alerts, the start confirmation).

**The frame:** the navy rail with the brand symbol, then one white card holding the title (with the
run's pathway, market and module count), the stage bars and the workbench. Run readiness sits in
that card as the inspector column.

**Inbox copies** (the pathway is fixed):
- The rail links to Issuer library and Run activity at `<root>/_engine/library/`.
- The page loads that library's fonts, which lifts the README limit "form copies in the inbox use
  system fonts". The repository copy uses `src/deploy_vii/assets/fonts`; only one base is requested,
  so no request fails (console empty in both).
- Only the folder's own pathway card is shown.

**Reader terms:**
- Module names lead and codes are their titles.
- Answers show option labels, not schema values (`High yield`, not `high_yield`).
- Live-run ids are code comments or titles.
- No command lines, "launcher", "owner route" or "Python" in the reader's copy.

**Signals:**
- Unanswered reads as a neutral dashed "Check".
- Amber is kept for Gap and Limited (they need an acknowledgement).
- Red is for errors and Will refuse.
- An asterisk marks required; a quiet badge marks recommended.

## 5. Review of main (`caeb622`): suggestions

1. **New run patterns.** `screen.css` still carries the New run and Settings patterns
   (`.run-stages`, `.module-steps`, `.run-field`, `.step-actions`, `#new-run`, `#context-editor`,
   `.settings`). Their markup was removed (`credit_os/SOURCE.md`: "New run and Settings are gone").
   - The proposal is the natural owner of those patterns. It has to copy them inline, because it
     opens from disk under its own CSP.
   - Either retire them from `screen.css`, or keep them and add a test that the form's copied tokens
     equal `screen.css` lines 5 and 81.
2. **Drift tests** (added at adoption, `tests/test_context_form.py`). The form duplicates tables
   from Python and the library; one test each stops silent drift:
   - `RUN_ORDER` against `registry.plan` per pathway;
   - `EDGES` against `run_expectations.edges_for`;
   - `MODULES` names against `report-adapter.js` `MODULE_NAMES`;
   - `SCALES` against `cp2h.COMBINED_SCALE`;
   - the peer, precedent and staleness limits against `valuation_basis` and `cp3_relative_value`.
3. **CP-2G's own cases (`a51a8a1`).** The forecast's downside shock still comes from CP-2A's scenario,
   so the form's CP-2A assumptions can now reach the forecast. The form says so where CP-2G runs. The
   forecast also needs a fiscal-year base; the form requires the current period on Distressed and
   asks for `fy-YYYY`.
4. **No way from the library to the form.** The library's empty state ("No runs in this workspace
   yet. The data file holds no retained runs.") and Run activity give a first-time analyst no route
   to start a run.
   - Suggested: one line on both, "To start a run, fill in the form in
     `inbox\<pathway>\_template\` and drop the folder in `inbox\<pathway>\`".
   - From `_engine/library/` the forms are at `../../inbox/<pathway>/_template/`.
5. **Show the forecast in Run activity.** The watcher could write the launcher's offline
   `expectations` for each drop into Run activity. The owner could then compare forecast with
   outcome per module, which is the calibration this form's rules need, and the comparison of actual
   output with instructions that `AGENTS.md` asks for. Today nothing shows them.
6. **On adoption:**
   - update `README.md` (the inbox font limit is gone; the form's steps);
   - update the two `FORM_PROBE` expectations;
   - mention the form-only rules in `docs/templates/README.md`.

## 6. Decisions for the owner

1. ~~Adopt as `docs/templates/context-form.html`?~~ Adopted (owner, "Approved"); see section 7.
2. Should `context.py` mirror the form-only rules, or keep accepting hand-written files without them?
3. Should the launcher print its `expectations` (computed today but only read by tests), so a CLI run
   shows the same forecast as the form?
4. Owner route: CP-1D and CP-2D need an fy/q4 base (`period_basis.run_basis`), but an earnings update
   names quarters. Is that conflict intended?
5. CP-2E is in no pathway, so the cp2e pin has no effect from the inbox; the form hides it unless a
   loaded file holds it. Keep, remove, or add CP-2E to a pathway? (CP-DR now joins with the default
   peer source, so research questions are answered there.)

## 7. At adoption (2026-11-10, after main `4ce88c2`)

**Main's ruling and what the form does with it.** Owner: "Cp-1c is supposed to get that information
from cp-dr by default". `cpos_launch.pathway_modules` now adds CP-DR to a pathway that has CP-1C when
the peer source is `cp_dr_public`. The form follows:
- **Peer source.** `cp_dr_public` is the default again. The form-only "choose a peer source" rule is
  gone.
- **Run order.** It depends on the peer source (`RUN_ORDER`, `WITH_RESEARCH`); main also moved CP-2A
  after CP-2. The readiness panel lists CP-DR where it joins.
- **Peer files.** CP-DR has no web access in this transport (main's own verification note), so a new
  Source files item asks whether the peers' filings or a peer data file are in the folder. Unanswered
  makes CP-DR a Check; "Not available" makes CP-1C a Gap.
- **Questions.** The Questions stage is shown where CP-DR runs. CP-DR answers the context's questions
  first (`cpdr.md`) and routes each to CP-1C, CP-2 or both.
- `Named peers` (`user_list`) keeps its Gap: nothing looks up their figures, and CP-DR joins only for
  `cp_dr_public`.

**Other changes at adoption:**
- The form replaced `context-form.html`; the proposal file is gone.
- `tests/test_library_page_browser.py` `FORM_PROBE` now reads the pathway cards. On the Earnings
  Update copy it expects the run type to stay `earnings`. The probe runs in its own function scope,
  because the form declares globals.
- `tests/test_context_form.py` keeps the copied tables to their sources: pathways, run order per
  peer source, edges, module names, rating scales, limits, pinned bounds against
  `context.ASSUMPTION_LIMITS`, and design tokens. Each was seen to fail on a one-line change to the
  form. Main had already moved CP-2A in the Distressed order; the test caught the copy written before
  that.
- `README.md`, `apps/issuer-library/README.md` and `docs/templates/README.md` describe the form.
  - The inbox font limit is gone: inbox copies load the built library's fonts.
  - A copy already in a pathway's `_template` is never replaced: delete it and restart the watcher.

**Still open:** decisions 2 to 5 in section 6; suggestions 1, 4 and 5 in section 5.

