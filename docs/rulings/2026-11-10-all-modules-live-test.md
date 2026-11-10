# One TDG live run of every analytical module after the method-gap fixes

lifts: live-provider-pause
by: user
date: 2026-11-10
configs: sol-medium

Asked "Should I run a paid all-modules live test to see which blocks are gone? My estimate is
USD 4–6, capped at USD 20", the user said "Yes, run it".

Scope: one CP-OS launch of all twenty analytical modules (CP-0, CP-1, CP-1A, CP-1B, CP-1C, CP-1D,
CP-2, CP-2A, CP-2D, CP-2E, CP-2G, CP-2H, CP-3, CP-3C, CP-3D, CP-4, CP-4C, CP-5, CP-6, CP-DR) on
OpenAI gpt-6.1-sol at medium effort, over the retained historical TDG FY2024 public files
(`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, read only), with the context of run
`tdg-forecast-004` (`attachments.legal_documents: none`). Cap USD 20 for the run folder. Run
directory: `/private/tmp/claude-501/rbot-live7/runs/tdg-all-001`.

Purpose: compare each module's disposition with the retained run `cpos-tdg-sol-medium-all-001`
(same files, same model configuration, before the fixes on `claude/module-method-gaps`).

The run writes nothing inside this repository or any retained run directory. The provider key
comes from the launching environment only; no credential file is read. It proves this dated case
only; automated checks cover handoff structure and anchors, not analytical accuracy. Outputs are
candidates until reviewed.
