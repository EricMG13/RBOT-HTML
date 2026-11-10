# One TDG live test of the research module's web search

lifts: live-provider-pause
by: user
date: 2026-11-10
configs: sol-medium, web-search

Asked "Should I write that ruling and the command for session A? Yes, cap USD 10 / Not now" after
the web search change (PR #30), the user said "Merge then test".

Scope: one CP-OS launch of CP-0, CP-1, CP-DR and CP-1C on OpenAI gpt-6.1-sol at medium effort, over
the retained historical TDG FY2024 public files (`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`,
read only), with the context of run `tdg-all-001` (peer source `cp_dr_public`). CP-DR may use
OpenAI's hosted web search (USD 0.01 a search; `cases/pricing/openai-web-search.json`). Cap USD 10
for the run folder. Run directory: a new folder outside the repository, such as
`/private/tmp/claude-501/rbot-live8/runs/tdg-cpdr-web-001`.

Purpose: show, for this dated case, whether OpenAI accepts web search on these requests
(`store: false`), whether CP-DR ends its searching turns with a tool call, whether its peer pack
(TDR.4 to TDR.6) cites located, dated figures from on or before the 2024-09-30 cutoff, and whether
CP-1C reads those peers. Compare CP-DR and CP-1C with run `tdg-all-001`, where both were Blocked.

The run writes nothing inside this repository or any retained run directory. The provider key
comes from the launching environment only; no credential file is read. Search queries leave the
environment, so CP-DR is told to put only public names in them. It proves this dated case only;
automated checks cover handoff structure and anchors, not analytical accuracy. Outputs are
candidates until reviewed.
