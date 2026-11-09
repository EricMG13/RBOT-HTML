# One TDG live run of every launchable module on sol-medium

lifts: live-provider-pause
by: user
date: 2026-11-09
configs: sol-medium

The user instructed "run enough test under the latest methodology to produce outputs for all
modules" and chose "sol-high, cap USD 25" when asked, then changed it to "sol medium" (cap USD 15).

Scope: one CP-OS launch of the 20 modules the launcher has a method for — CP-0, CP-1, CP-1A,
CP-1B, CP-1C, CP-1D, CP-DR, CP-2, CP-2A, CP-2D, CP-2E, CP-2G, CP-2H, CP-3, CP-3C, CP-3D, CP-4,
CP-4C, CP-5, CP-6 — on OpenAI gpt-6.1-sol at medium effort, capped at USD 15 for the run folder,
over the retained historical TDG FY2024 public files
(`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, read only) with the context pinned
as `runs/tdg-context-2024-09-30.json` (sha256 f7b95e1f…, the same file the two approved
sol-high runs used). Run directory: `runs/cpos-tdg-sol-medium-all-001`.

Not run: CP-8 (comparison route), CP-MODEL (Python model publication), CP-L10 (no launcher
method). The library's Forecast tab fills only once the CP-2G model publication (plan Task 9)
exists.

The provider key comes from the launching environment only; no credential file is read. This
run proves this dated case on sol-medium; automated checks cover handoff structure and anchors,
not analytical accuracy. Outputs are candidates until reviewed.
