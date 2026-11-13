# One TDG full credit assessment through GitHub Copilot on GPT Sol

lifts: live-provider-pause
by: user
date: 2026-11-13
configs: copilot-sol-medium

The user instructed "re-run TDG on Sol github". Asked which pathway, the user chose "Full credit
assessment"; asked what "Sol github" means for the provider route, "GitHub Copilot, GPT Sol"; asked
for the cap, "USD 10 lite / USD 25 full".

Cap: USD 25 for the run folder.

Scope: one CP-OS launch of the `credit_snapshot` preset (Full credit assessment), with CP-8 against a
copy of the earlier run `tdg-proof-snapshot-opus-002`, on `copilot-sol-medium` (gpt-6.1-sol, medium
effort through the GitHub Copilot SDK), over the retained historical TDG FY2024 public files
(`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, read only) with the context
`runs/tdg-context-2024-09-30.json` (a copy; the file the earlier TDG runs used). The run folder is
`tdg-full-copilot-sol-001` in a workspace in the launching session's scratchpad, outside this
repository and every retained run directory. The code is `main` at `b2780e8` (the Deploy V method
texts of PR #93 and the full and lite assessments of PR #96).

Credential: the gh CLI's active account (`COPILOT_USE_GH_LOGIN=1`, no `COPILOT_GITHUB_TOKEN`), as in
`2026-11-09-copilot-small-test.md`; runtime 1.0.105 (`COPILOT_CLI_PATH`). That account pays. No
credential file is read by the launcher. Prompts carry public TDG filing text to GitHub and the model
vendor. Web search is not offered on this route, so CP-DR reads only the run's files.

It proves this dated case and route only; automated checks cover handoff structure, not analytical
accuracy. Outputs are candidates until reviewed. It is not a lite run and does not supply the reader
check the lite credit assessment still needs.

Extension (same day). Both runs stopped at CP-5 after ten accepted modules (medium USD 5.77, high
USD 7.78): its handoff was refused three times for one table whose header had 7 cells and separator 8,
and the refusal named no line (fixed in `08df6a4`). The launcher does not resend a module that already
started, and a new run cannot reuse another run's handoffs. Told this, the user said "bypass existing
rules and use existing handoffs to pick up from where you left off. we are comparing outputs, quality
and telemetry between runs.", then "resume". So each stopped folder is copied
(`tdg-full-copilot-sol-001-resume`, `tdg-full-copilot-sol-high-001-resume`), CP-5's retained attempts
are removed from the copy only (`requests/CP-5` and its `live/modules` folder), and the copy is
relaunched with the same arguments: the ten accepted handoffs replay from retained responses and CP-5,
CP-6 and CP-8 are paid, under the same USD 25 ceiling per folder, which still counts the spend already
made. The stopped folders are kept unchanged. This is a one-off bypass of the never-resend guard for
these two folders; the guard itself is unchanged. CP-5's telemetry in the resumed folders covers only
the second attempt; the first is in the stopped folders.
