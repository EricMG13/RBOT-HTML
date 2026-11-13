# Optimisation review of the CP-OS path: discovery report, 2026-11-13

Step: discover only. Nothing in the code, method texts or run folders was changed.

## Bottom line

- The money is in what each module is sent of earlier modules' handoffs, not in the method texts.
  About a quarter of each run's cost is the appendix of upstream handoffs pasted into every later
  module, almost none of which those modules use.
- Three defects that lower analytical quality were found while measuring. They come first, ahead of
  any saving.
- Instruction text is 10-14% of a run and is mostly used; trimming it would save about USD 0.035 per
  run. It is not worth doing.
- Wall-clock: running the three modules that are off the critical path alongside their siblings would
  cut 20% (13 to 16 minutes) at no extra spend, if the Copilot account serves two calls at once.
- Every figure below is attributed from one run per effort level. None has been trialled, and
  run-to-run noise is unknown. The savings are not additive.

## Basis

| | |
| --- | --- |
| Tree | `main` at `d941eef` (includes PR #93, #96, #97) |
| Run data | TDG FY2024 Full credit assessment on Copilot gpt-6.1-sol: medium USD 8.62, 136 calls, 62.5 min wall; high USD 11.37, 165 calls, 85.9 min wall. Folders `tdg-full-copilot-sol-001-resume` and `tdg-full-copilot-sol-high-001-resume` in the session scratchpad workspace |
| Method | 7 investigators, one per dimension, each measuring from `live/calls.jsonl`, the retained requests, drafts, reviews and the code; then one skeptic per dimension re-measured every finding with its own probe and tested the quality risk |
| Result | 46 findings: 7 confirmed, 30 confirmed with a correction (the corrected figure is used here), 7 unproven, 2 refuted |
| Prices used | Copilot route, `src/deploy_workflow/model/pricing.py:141-158`: cache write USD 2.50, cache read 0.10, output 10 per million tokens; they reproduce the billed total exactly |
| Probes and raw findings | session scratchpad `opt-review/` (`swarm-results.json` holds all 46 findings and verdicts) |

Where the bill goes: one cache write of the whole prompt on each module's first call, then cheap
re-reads. Uncached input is under 500 tokens per run. Rejected drafts are already cheap, because the
model patches a draft rather than rewriting it.

## Quality defects found (fix before optimising)

1. **Copilot silently summarises a module's context at about 218,000 tokens (80% of 272,000).**
   In the high run it completed in CP-5 (first attempt), CP-6 and CP-8. The accepted high CP-8 handoff
   was written from a 42,000-token summary in place of about 229,000 tokens of upstream handoffs, and
   it contains a false statement its own CP-1 contradicts. The medium run reached the threshold in CP-5
   and CP-8 but the module ended first. The summariser's charge (USD 0.21 on high) is outside the
   ledger and the cap. `copilot_adapter.py:758-767` takes the SDK default; no code handles the event.
   Order of work: record the event and its spend and flag the module; check each first prompt against
   the limit less the output budget; shrink the prompt (items 1-3 below); only then consider turning
   summarising off, because CP-8's first prompt alone was 240,816 tokens.
2. **A repair can drop sourced values that no issue named.** High CP-6 was rejected for one word on
   one line; its repair also replaced the sourced FY2023 figures USD 247 million and USD 755 million
   with "Not supplied", and the delivered handoff no longer has them. Proposal: on a write that follows
   a rejection, flag any sourced number present in the rejected draft and absent from the repair.
3. **Two checker messages point the model the wrong way.**
   - CP-1's chart-unit message advises removing amounts; obeyed literally it would have replaced 11 to
     13 sourced amounts with gaps. A second table under one heading is reported as malformed rows.
   - The events table's Published rule is never stated and two checks contradict each other. It caused
     6 of 18 rejections, and every dated event row in both runs ended as "—" (37 and 26 rows), although
     the 10-K states its own date. The rule should say Published is the date of the document the row
     is taken from.

## Cost: candidates, largest first (USD per run, medium / high)

| # | Change | Saving | Condition that protects quality |
| --- | --- | --- | --- |
| 1 | Send each upstream handoff inline without its register appendix; offer the full pinned handoff as a readable source, as CP-8 already reads the earlier run | Gross 1.68 / 2.37; net of on-demand reads about 1.2-2.3 (the read cost is an estimate) | Full bytes stay in `task.handoffs`, so the sha and CP-8 checks are unchanged; the new `handoff/` sources are excluded from the issuer-evidence check and from the retained source-hash comparison |
| 2 | One short alias per source, assigned by CP-OS once per run and valid in every handoff and tool; the report still shows full identities | 0.55-0.7 / 0.7-0.9 | Aliases are per run, not per handoff; an unknown alias is refused; test an upstream Basis line copied into a downstream handoff |
| 3 | CP-8 reads the twelve current handoffs on demand, like the earlier run's | A further 0.24 / 0.25 beyond #1 | Every Basis-cited statement CP-8 draws from a current handoff (19 per run) is still present and correct |
| 4 | State the Published rule (defect 3) | 0.14 / 0.27 | The check is not loosened; a 10-K-sourced row carries the 10-K's date |
| 5 | Give `calculate` a multiply operation | Up to 0.23 / 0.73 (upper bound) | Results stay exact; no model arithmetic |
| 6 | Put the source list in the first prompt (nearly every module spends its first call on `list_sources`) | 0.15 / 0.19, 13-14 calls, up to 80 s | Same list, same ids |
| 7 | Report every table fault in one rejection, not only the first | 0.02-0.19 per extra fault, and keeps a write in reserve | Check unchanged |
| 8 | Large `read_pages` results reach the model as a 500-character preview: keep results under the runtime's threshold | About 0.02-0.03 per stub, 2 per run; no page lost silently | Model reaches the same pages |
| 9 | CP-4 without its 4A/4B bundles when a deterministic signal says no executed document is in the pack | 0.05, blocked cases only | Relaunch with the full text if CP-4 reports an executed document; the Blocked handoff keeps its gap rows |

Items 1 and 3 also remove the cause of defect 1: they take CP-5, CP-6 and CP-8 well below the
summarising threshold.

## Effort routing

- High effort's main gain, next year's scheduled interest of USD 1,524 million, came from one source
  search in high's CP-2. No instruction names the forward interest schedule. Naming it in CP-2 and
  CP-2A makes the gain independent of effort (about one extra search, under USD 0.02).
- Medium's two errors that travelled downstream are instruction gaps, one sentence each: the repayment
  schedule is by fiscal year (CP-1); a filing is not post-cutoff when no cutoff is set (CP-DR).
- Medium's withheld forecast: refuted as first proposed. The gap is between CP-2G's rule (carrying debt
  is primary) and CP-1, which is never told which debt measure to print. Fix the operand rule, not
  the effort.
- Proposed map after those fixes: high for CP-1A, CP-2 and CP-2A; medium elsewhere. Spliced cost USD
  9.09 a run against 9.52 for today's balanced default and 11.37 all-high. The splice understates
  upstream-high cost: nearly half of high's extra spend is later modules reading longer handoffs.
- Evidence needed before adopting a map: at least two runs per setting on two issuers, scored against
  a list written before the runs.

## Wall-clock

| Change | Saving | Condition |
| --- | --- | --- |
| Run CP-1A, CP-4 and CP-2E alongside their siblings, two at a time; every module's inputs unchanged | 12.8 / 16.0 minutes (20% / 19%), USD 0 | Today's code refuses a second module at once. Six invariants must hold (ordered acceptance, cap with two holds of USD 7.17, resume, events, per-module session home, a thread-safe adapter). The USD 10 lite cap cannot hold two reservations, so lite stays in order. Requires the Copilot account to serve two calls without queueing |
| Record `first_byte_at` (always null today) | Makes slow calls diagnosable; precondition for the row above | One medium call ran at a third of normal speed while both runs overlapped |
| Cache the annual-report PDF's extraction per run (re-extracted for all 13 modules; only CP-0 reads it) | About 25 s | Same source id and hash |

## Not worth doing

- Trimming or reordering instruction text: at most USD 0.035 a run for the content-neutral part; the
  method's table IDs mostly appear in the handoffs (CP-1A 11 of 11, CP-2A 25 of 26, CP-2E 17 of 17),
  and there is no M365 navigation text left to remove.
- "Not supplied" rows and copied text: about USD 0.07 a run.
- Remaining local overhead: about 1.5% of wall time.
- Raising the three-write limit: the two stops came from refusals that named no line (fixed in
  `08df6a4`), not from the limit.

## Needs an owner decision or a trial before any figure is claimed

| Item | Upper bound, per run | What is missing |
| --- | --- | --- |
| Stop writing part of the appendix (output is the expensive class) | 1.14 / 1.52 | A ruling reversing E8 and E10, and a per-register list |
| Share cached handoff text across modules by putting common text first | 1.25 / 1.52 | A two-session probe showing Copilot shares cache across session ids; current data suggests it does not |
| Skip CP-DR when web search is off and its questions cannot be answered | 0.28 | A ruling on whether a selected module may be skipped; three web-off runs on two issuers |
| Repair a module that used all its writes instead of stopping the run | 0.30 / 0.43 per stop | An owner ruling on the extra write; defect 2's guard first; an offline replay |
| A page map for source navigation (31% of searches find nothing) | Share of 0.33-0.61 | Offline map coverage, then a paid comparison |

## Suggested order

1. Defects 1 to 3 (record and flag summarising; the dropped-number flag; the two messages and the
   Published rule).
2. Cost items 1 and 3 together, then 2. They are the largest and remove the summarising trigger.
3. The four instruction sentences under Effort routing, then one medium run to see whether the gain
   holds at medium.
4. Cost items 5 to 8.
5. Two-at-a-time scheduling, after `first_byte_at` is recorded.

Each landed change needs a before and after on comparable runs; a saving attributed here is not a
measured gain.

## Not verified

- Any trial of a proposed change: all figures are attributed from existing runs.
- Run-to-run noise: one run per effort level, one issuer, one route.
- Whether Copilot serves two concurrent calls without queueing, and whether it shares cache across
  sessions.
- The cost of on-demand register reads (item 1) and of the aliases themselves (item 2).
- The summariser's charge on medium; dry-launch, library rebuild and budget-reload timings were not
  re-measured by the skeptic.
- The other pathways and issuers; the lite pathway has no run.
- I read the digest of all 46 findings and the full text of six; the report was not reviewed by a
  second reader.
