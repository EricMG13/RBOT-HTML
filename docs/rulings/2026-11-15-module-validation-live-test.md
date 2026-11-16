# Module validation live test: four TDG pathways through GitHub Copilot on GPT Sol, medium

lifts: live-provider-pause
by: user
date: 2026-11-15
configs: copilot-sol-medium

The user instructed "run live test and repair module validation. test module is functional, inter
module communication, cp-os script validation, markdown rendering and pathways. use sol 6.1 medium
through github cli." Asked for the scope, the user chose "4 pathways, every module"; asked for the
cap, "USD 15 per run, USD 60 total".

Cap: USD 15 per run folder; USD 60 for every launch under this ruling, re-runs included.

Scope: one CP-OS launch each of `credit_snapshot`, `distressed_restructuring`, `earnings_update` and
`relative_value` (together every module of the active pathways), on `copilot-sol-medium` (gpt-6.1-sol,
medium effort, GitHub Copilot SDK runtime 1.0.105), over the retained historical TDG FY2024 public
files (`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, read only) with a copy of
`runs/tdg-context-2024-09-30-legal-none.json` whose pathway is set per launch. `--prior none`: no
CP-8. Run folders are in the launching session's scratchpad, outside this repository and every
retained run directory. After a defect is repaired, the affected modules may be launched again in a
fresh folder under the same caps.

Re-run (same day): after the three repairs were merged (CP-1 T4.9 growth reading, every malformed
table listed in one review, CP-1B's joined T4.6 columns), one fresh `earnings_update` launch,
`tdg-earnings_update-002`, with `--prior tdg-earnings_update-001` so CP-8 runs last and the library's
Changes page is exercised. The four first launches charged USD 21.05 together.

Second re-run (2026-11-16, user: "A live re-test of earnings_update"): after the parked findings
were fixed (CP-1's forecast-block wording, the CP-1B cell-format note, the T4.9 and T4.6 readings, the
runtime released per module, the library's Overview lead and Script checks tab), one fresh
`earnings_update` launch, `tdg-earnings_update-003`, with `--prior tdg-earnings_update-002`. Launches
so far charged USD 24.75 of the USD 60. It charged USD 3.51: USD 28.26 in all.

Credential: the gh CLI's active account (`COPILOT_USE_GH_LOGIN=1`, no `COPILOT_GITHUB_TOKEN`); that
account pays. No credential file is read. Prompts carry public TDG filing text to GitHub and the
model vendor.

It proves this dated case and route only; the method-script checks and the presence checks cover
figures and structure, not analytical judgement. Outputs are candidates until reviewed.
