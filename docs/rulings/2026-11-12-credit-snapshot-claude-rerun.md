# One fresh TDG credit snapshot on Claude, after the output-limit fix

lifts: live-provider-pause
by: user
date: 2026-11-12
configs: opus-medium

The credit snapshot proof run `tdg-proof-snapshot-opus-001` stopped in CP-4 when its answer hit the
32,000 output-token limit (`2026-11-12-module-changes-proof-runs-claude.md`). Asked "How should the
credit snapshot proof be finished?", the user said "Claude, raise cap". Asked "Cap the fresh Claude
credit snapshot run at USD 25?", the user said "Yes, USD 25".

Scope: one CP-OS launch of the `credit_snapshot` preset with CP-8 against the earlier run
`tdg-reader-format-001`, on Anthropic claude-opus-5-5 at medium effort, over the retained historical
TDG FY2024 public files (`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, read only) with
the context `runs/tdg-context-2024-09-30.json`. Cap USD 25 for the run folder
`/private/tmp/claude-501/-Users-ericguei-Documents-RBOT-HTML--claude-worktrees-pause-63d136/c8719821-dd4f-4042-ad6b-2051ff7e7dda/scratchpad/preview-ws/runs/tdg-proof-snapshot-opus-002`, outside this repository and every retained run directory. It
is a fresh run: the stopped run cannot be resumed under a different cap. Spend before it on these
proof runs is USD 17.62.

Purpose: show whether CP-4 completes on Claude with the 64,000 output-token limit, and read CP-2G with
the new presets, CP-8 and the library's Changes section on real model output. Web search is not offered
on Claude, so CP-DR reads only the run's files. The provider key comes from the launching environment
only; no credential file is read. It proves this dated case and route only; automated checks cover
handoff structure, not analytical accuracy. Outputs are candidates until reviewed.
