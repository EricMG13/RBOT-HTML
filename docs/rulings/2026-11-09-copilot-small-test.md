# One small TDG live test through GitHub Copilot

lifts: live-provider-pause
by: user
date: 2026-11-09
configs: copilot-sol-medium

The user instructed "github copilot and cli installed. run small live test."

Cap: USD 10 for the run folder (one call holds up to USD 7.17).

Scope: the Copilot seat check (`tests/model/test_copilot_live.py`, two short tool exchanges),
then one CP-OS launch of CP-0 and CP-1 on `copilot-sol-medium` (gpt-6.1-sol, medium effort
through the GitHub Copilot SDK) over the retained historical TDG FY2024 public files
(`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, read only), with the context pinned as
`runs/tdg-context-2024-09-30.json` (the file the earlier TDG runs used). Run directory:
`runs/cpos-tdg-copilot-sol-medium-001`.

Second launch: -001 stopped in CP-1 on an IdleTimeout (non-streamed reply longer than 120 s; fixed
in 7780a09) and cannot resume (its timed-out call's outcome is unknown). The user said "Fix and
resume", then "Yes, fresh run": one fresh launch of the same scope in
`runs/cpos-tdg-copilot-sol-medium-002`, cap USD 10.

The runtime is the Copilot SDK runtime 1.0.105 from `python -m copilot download-runtime`
(`COPILOT_CLI_PATH`). Credential: the user chose "Use the CLI sign-in", and after review
"Use gh sign-in" — with no `COPILOT_GITHUB_TOKEN` set, `COPILOT_USE_GH_LOGIN=1` lets the runtime
take the OAuth token of the gh CLI's active account (`gh auth token`; branch
feat/copilot-cli-login). That account pays; `gh auth switch` changes it. The run records
`auth: gh-login`. No credential file is read by the launcher. Prompts carry public TDG filing text to GitHub and the model vendor. This run
checks that the Copilot route works end to end; automated checks cover handoff structure and
anchors, not analytical accuracy.
