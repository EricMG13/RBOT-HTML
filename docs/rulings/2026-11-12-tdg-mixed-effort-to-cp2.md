# One TDG live run to CP-2 with mixed GPT effort, compared with the saved all-medium runs

lifts: live-provider-pause
by: user
date: 2026-11-12
configs: sol-medium

The user instructed "review modules to assess medium or high and use GPT medium and high live
testing and compare vs saved all-medium runs. up to cp-2", then clarified "gpt mixed medium and
high live testing and compare that with existing results for just medium".

Scope: one CP-OS launch of the ten modules up to and including CP-2 in the pathway order (CP-0,
CP-1, CP-1A, CP-1B, CP-1C, CP-1D, CP-DR, CP-2, CP-2A, CP-2E) on OpenAI gpt-6.1-sol, configuration
sol-medium, with `--high-modules CP-0 CP-1A CP-1D CP-2 CP-2A` (high effort on those five, medium
on the rest; the same model and price table). Sources: the retained historical TDG FY2024 public
files (`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, read only). Context: a copy of
the 2026-11-10 baseline's context (`attachments.legal_documents: none`). Cap USD 14 for the run
folder, including the USD 5.73 per-call hold. CP-DR does not search the web. Run directory:
`runs/cpos-tdg-sol-mixed-cp2-001` in the main checkout.

Comparison: the same modules in the saved all-medium runs
`/private/tmp/claude-501/rbot-live7/runs/tdg-all-001` (2026-11-10, primary) and
`runs/cpos-tdg-sol-medium-all-001` (2026-11-09), which are not modified. Module instructions have
changed since both baselines (reader-voice ruling of 2026-11-11), so differences are not
attributable to effort alone.

The provider key comes from the launching environment only; no credential file is read. It proves
this dated case only; automated checks cover handoff structure and anchors, not analytical
accuracy. Outputs are candidates until reviewed.
