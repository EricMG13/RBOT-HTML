# Lite, Full and Deep credit assessments, and a cap per pathway

by: user
date: 2026-11-15

This is a decision record. It does not lift the paid-run pause and carries no `lifts:` or `configs:`
line; paid execution still needs its own explicit action. No run has been made with this change, and
the build made no provider call.

Owner's words, 2026-11-15: "restructure the pathways: Deep max $40, Full $25 and Lite $15". Asked
three questions, the owner chose: on the modules, "Lite/Full as now, Deep = all (Recommended)"; on
the five purpose pathways, "Keep alongside"; on the cap rule, "Hard cap per pathway (Recommended)".
Earlier the same day: "no live run yet, and pathway will be restructured before live run", and, on
CP-3's enterprise value, that it is "supposed to" come "by default using peer multiples" from CP-DR or
CP-1C, with the pathway part waiting for this restructure (`2026-11-15-method-script-checks.md`,
"CP-3's enterprise value").

## Amends

- `2026-11-11-run-start-submit.md`: its "USD 20 per run folder" becomes the run's pathway cap in the
  table below. The Submit-on-an-approved-summary action, the configurations and every other part of
  that standing ruling are unchanged; the service still runs only under it.
- `AGENTS.md`: the cap sentence now points at the per-pathway caps.
- Not amended: `2026-11-13-full-and-lite-credit-assessments.md` (Full and Lite keep their ids, modules
  and sections) and the deactivation of the short credit snapshot.

## Decisions

- Lite stays `lite_credit_assessment` (CP-0, CP-1, CP-1A, CP-2, CP-2A) and Full stays
  `credit_snapshot` ("Full credit assessment", 15 entries with CP-MODEL). Neither id, module list nor
  section list changed: retained runs, CP-8's same-pathway comparison and the library depend on them.
- Deep is a new pathway, `deep_credit_assessment`, "Deep credit assessment": Full plus CP-1B, CP-1C,
  CP-1D, CP-2H, CP-3D and CP-4C (21 entries with CP-MODEL, 20 model calls without CP-8). Its order is
  the registry's plan (`deploy_vii.registry.plan`), not an appended list: CP-0, CP-1, CP-1A, CP-1B,
  CP-DR, CP-1C, CP-1D, CP-2, CP-4, CP-2A, CP-2E, CP-2D, CP-2G, CP-2H, CP-3D, CP-3C, CP-4C, CP-3, CP-5,
  CP-6, then CP-8 when an earlier Deep run of the issuer is listed. CP-DR and CP-1C come before CP-2
  and CP-3, so CP-3 is sent CP-1C's handoff and the CP-3 check compares its `EV multiple` with CP-1C's
  T4.10 (`deploy_workflow.method_scripts_cp3`). CP-3 waits for every specialist it may read (CP-1D,
  CP-2H, CP-3D, CP-3C, CP-4C); CP-5 reads all eighteen analyst handoffs.
- Deep's report sections (24): Full's twelve, Lite's two downside sections (CP-2A), and one lead
  section for each module Full neither runs nor shows: headline results (CP-1B), earnings quality
  (CP-1D), peer positioning (CP-1C), liquidity runway (CP-2D), forward credit path (CP-2G), rating
  triggers (CP-2H), covenant tests and headroom (CP-4), recovery by class (CP-4C), refinancing paths
  (CP-3C), market against fundamentals (CP-3D). Each is owned as in its purpose pathway, and Full's
  twelve keep Full's owners. CP-DR and CP-2E keep no section, as in Full. The figure producers of
  those blocks (S.5, RV.3, CR.1, DR recovery and rating triggers) apply to Deep too. This list is a
  presentation choice made in this build, not by the owner.
- The portfolio workbook is collected for Deep as for Full: it runs CP-0, CP-3 and CP-6.
- The five purpose pathways stay offered beside the three, unchanged, at USD 20 each.
- CP-8 compares a run only with an earlier run of the same pathway. A first Deep run of an issuer is a
  first run: it is not compared with that issuer's Full run.

## Caps

One table, `PATHWAY_CAP_USD` in `src/deploy_vii/contracts.py`. USD per run folder, enforced by the
existing budget (`deploy_workflow.model.budget`): a call is refused when spend plus its hold would
pass the cap, and the run stops as `capped`.

| Pathway | Cap, USD |
| --- | ---: |
| Lite credit assessment (`lite_credit_assessment`) | 15 |
| Full credit assessment (`credit_snapshot`) | 25 |
| Deep credit assessment (`deep_credit_assessment`) | 40 |
| Earnings Update, Relative Value, Covenant & Refinancing, Distressed & Restructuring, Portfolio Decision | 20 |
| Short credit snapshot (deactivated) | 20 |

Read by: the run start page's pathway choices and its summary (the service's answer names the cap);
the service's launches (`runs.cap_of`, passed as `--cap`); the run activity (each run's cap); and the
launcher, as its default when `--cap` is not given and as the most `--cap` may ask.

- The launcher refuses a `--cap` above the cap of the context's pathway, whoever asks; a lower cap
  is allowed. This is a tightening: before this change the command line took any positive `--cap`
  (the USD 20 was enforced only by the run start service), and owner-commissioned runs used USD 12
  and USD 25. A run above its pathway's cap now needs the table and this ruling changed first.
- The ruled figures are written a second time in `inbox/startup.py` (`RULED_CAPS_USD`). The service
  refuses to start when a table entry is above its ruled figure or has none, so raising a cap takes
  a ruling and two deliberate edits, as the single USD 20 check did before.
- The page sends the cap it displays with each summary and Submit (`X-Shown-Cap`); the service
  refuses a request without it or with another figure ("this page is out of date ... Reload the
  page"). A tab opened before this change shows USD 20 and sends none, so it can neither get a
  summary nor start a run. The page's per-pathway caps are a copy of the table; a test holds the
  copy to hand-written figures and to the table.
- A run folder started under the earlier USD 20 resumes only at that cap: the launcher refuses the
  pathway's new default with the folder's cap named, and `--cap 20` resumes it. A folder's cap
  never rises.

- A summary records the cap it showed beside its digest; Submit refuses when the table now gives
  another cap ("review the summary again"), and the queued record keeps the cap.
- A record queued before this change holds no cap. Its summary showed USD 20, so it launches at the
  lower of USD 20 and its pathway's cap: never more than was approved, nor more than the table allows
  (a queued Lite run at USD 15, a Full run at USD 20).
- A summary issued before this change records no cap, so Submit refuses it; the analyst makes a new
  summary, which shows the new cap.
- Known: a summary that returned an error issues no digest and no cap; a Submit after it is refused
  as "the documents or answers changed after approval", which does not name the cause.
- The page still opens with Full selected; only the order of the choices changed (Lite first).
- The run start summary shows the cap and no spend estimate; none was added.

## Estimated spend against the caps

An estimate, not a measurement, on GPT Sol at the page's default (Balanced: high effort on the effort
map's modules). Basis: each module's USD in the two retained 13 November Full runs on gpt-6.1-sol
(`runs/tdg-copilot-sol-medium-vs-high.md`); CP-1B, CP-1C and CP-1D from the 10 November all-module
run (older texts); CP-2D, CP-2H, CP-3C, CP-3D and CP-4C at the mean measured analyst module (USD 0.51
at medium); high at each module's measured high/medium ratio, else 1.32; CP-5 and CP-8 scaled by the
handoffs they read. Treat it as right to within about a third. A GPT Sol call holds USD 5.73 (5.89
for CP-DR with web search) whatever its size, so a run in order needs about its spend plus 5.73.

| Pathway | Cap | Medium | Balanced | High | Balanced with CP-8, plus one hold |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lite | 15 | 2.3 | 2.8 | 3.1 | 8.8 |
| Full | 25 | 9.3 | 10.4 | 12.2 | 17.0 |
| Deep | 40 | 13.6 | 15.2 | 17.9 | 22.2 |

Not in the estimate: the size of Deep's largest first requests. CP-5 is sent eighteen handoffs and
CP-8 twenty, and the 13 November proposal projected about 300,000 tokens for each on whole handoffs,
before the register cut of that day shortened them. Above GPT Sol's 272,000 listed input tokens the
input rate doubles (the hold already covers it); no run has measured these requests since the cut.

On GPT Sol every tier fits its cap with room. On Claude Opus the one measured full run cost USD 19.45
(13 modules, 2026-11-12, medium) against USD 8.62 for the same modules on GPT Sol, 2.26 times. At
that ratio, with CP-8, Full today is about USD 23 at medium and 25 at Balanced, at or past its USD 25
cap once an Opus hold of about USD 3 is counted, and Deep is about USD 34 at medium, 37 at Balanced
and 44 at High: near or past its USD 40 cap. An Opus
run of either can stop at the cap before CP-6 or CP-8. The caps are the owner's and are not changed
here.

## What Deep cannot be sure of in one run

Every added module gets its required producers within the run; none needs a prior-period handoff.
What can be missing is the sources, and then the module runs, pays its first prompt and says so under
its own method gate. Nothing is skipped.

- CP-1B reads CP-1's periods; it compares periods found in the filings (year on year, sequential),
  not an earlier run. With one period in the files it reports the comparisons as not comparable.
- CP-1D needs the management EBITDA bridge; without it every bridge cell is not applicable and the
  module comes back restricted.
- CP-1C needs peers: CP-DR's public peers (Deep has CP-DR) or the analyst's comparables.
- CP-2H needs ratings; without them the summary shows a gap and the method marks the module
  Insufficient Information.
- CP-3D needs quotes; without them the summary shows a gap.
- CP-4C requires CP-4 (a blocking edge); when CP-4 stops at its gate for want of executed documents,
  CP-4C receives a Blocked handoff and stops at its own gate.

## Instruction size

Head plus method, CP-8 left out, on `tests/test_cpos_launch.py`'s synthetic input: Deep measured
1,805,013 characters. Its ceiling, by that file's rule for a new pathway (rounded up to the next
10,000 plus 5%), is 1,900,500. The seven other pathways' instructions are byte-identical before and
after this change; no other ceiling moved.

## Left open

- A paid run: no model has produced a Deep run. The owner starts it.
- Skipping a module whose sources are missing (proposal `docs/sweeps/2026-11-13-optimisation-review/
  pathway-tiers-proposal.md`, section 4) is not built: the owner chose "Deep = all".

## Owner's answers after the build (2026-11-15)

Asked four questions with the options and a recommendation each, the owner chose:

- Deep's report sections: "Keep the 24 (Recommended)", until a real Deep run has been read.
- Claude Opus against the caps: "Leave caps; measure first (Recommended)". The caps stay 15, 25
  and 40 for every model; the first Full and Deep runs go on GPT Sol, and Opus is decided after a
  measured run. Until then an Opus Full or Deep run can stop at its cap.
- Submissions queued before this change: "Lower of $20 and cap (Recommended)".
- This change to `main`: "Open and merge (Recommended)", when its checks are green.

