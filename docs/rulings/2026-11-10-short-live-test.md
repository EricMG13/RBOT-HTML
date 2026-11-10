# One short TDG live test: an inbox drop and the forecast modules

lifts: live-provider-pause
by: user
date: 2026-11-10
configs: sol-medium

The user instructed "run short CLI live test to verify items 1 and 2 in “not verified”". The two
items, from the verification record of the library link fix, were: the inbox watcher, a live model
run and delivery; and a run without a report or with a published forecast model.

Scope, both on OpenAI gpt-6.1-sol at medium effort over the retained historical TDG FY2024 public
files (`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, read only; the drop is a copy):

1. One drop into `inbox/earnings_update/` of a watcher started for this test, under the standing
   ruling `2026-11-09-inbox-automation.md`, with `--cap 10` (below that ruling's USD 20). The
   pathway's five modules: CP-0, CP-1, CP-1B, CP-1D, CP-5. Context: `runs/tdg-context-2024-09-30.json`
   with the pathway set to `earnings_update`. Shared folder: `/private/tmp/claude-501/rbot-live`.
2. One CP-OS launch of CP-0, CP-1, CP-2A and CP-2G with the unchanged context, capped at USD 10
   for the run folder (one call holds up to USD 5.73). Run directory:
   `/private/tmp/claude-501/rbot-live2/runs/tdg-forecast-001`.

Neither run writes inside this repository or any retained run directory. The provider key comes
from the launching environment only; no credential file is read. The runs prove this dated case
and these routes; automated checks cover handoff structure and anchors, not analytical accuracy.
Outputs are candidates until reviewed.
