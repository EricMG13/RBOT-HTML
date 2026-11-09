# One TDG live run on sol-high for an effort comparison

lifts: live-provider-pause
by: user
date: 2026-11-09
configs: sol-high

The user instructed "Run TDG live test at on GPT high and compare the analysis quality vs
medium", then chose "USD 12 per run" and "Retained medium run" when asked.

Scope: one CP-OS launch of CP-0, CP-1 and CP-1A on OpenAI gpt-6.1-sol at high effort, capped
at USD 12, over the retained historical TDG FY2024 public files (read from
`~/Documents/Final-workflow-PY/data/public-corpus/v1/TDG`, not modified) with the context of
`runs/cpos-launch-live-002`. The new run directory is `runs/cpos-tdg-sol-high-001`. The
medium side is the retained `runs/cpos-launch-live-002` (sol-medium, older code), not rerun.

The provider key comes from the launching environment only; no credential file is read.
This run proves this dated case on sol-high only; it does not prove current credit
conclusions, other issuers or the full pathway.

Extension: the user then instructed "Complete the run up to go-2" and confirmed "Yes cp-2".
The same run directory continues through CP-2 under the same USD 12 ceiling for the whole
run folder. The CP-2 medium side is the retained `runs/cpos-launch-cp2-reader-001`, whose
CP-2 consumed the medium CP-0/CP-1/CP-1A handoffs of `runs/cpos-launch-live-002`.

Resume cannot widen a run (requested modules are part of its identity), so CP-0 through CP-2
run fresh on sol-high in `runs/cpos-tdg-sol-high-cp2-001`, capped at USD 10, keeping both
folders together within USD 12. `runs/cpos-tdg-sol-high-001` is kept unchanged.
