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
