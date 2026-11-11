# Credit OS static pages for RBOT-HTML — spec

Owner decisions, 2026-11-09 (session quotes in quotation marks):

1. "there should only be the library and issuer reports." No New run, Run activity or Settings.
   Runs start only from `python -m deploy_workflow.owners.cpos_launch`.
2. "library picks up new reports following a completed run and adds it to the library." A run
   that CP-OS completes with a verified report appears in the library without a manual step.
3. "both the library and the report should be in the design of credit OS" — Final-workflow-PY
   `apps/issuer-library/web` at commit `07e14eca` (rail, issuer header, workspace tabs, navigator,
   inspector, screen.css/brand.css, fonts, icons).
4. "add the Calendar and forecast. all modules should be here." Issuer report tabs: Overview,
   Modules, Calendar, Forecast, Reports, Evidence. The module navigator lists every module in the
   Credit OS module catalog; a module a run did not produce says so. Owner chose "List all, no new
   run": no paid run is part of this work.
5. Pages stay static: they open from disk (`file://`), make no network request, need no server
   and add no dependency (no FastAPI/uvicorn).
6. Only runs listed by `deploy_workflow.library_index` (completed by CP-OS, current methodology)
   appear. Approved runs today: `runs/cpos-tdg-sol-high-001`, `runs/cpos-tdg-sol-high-cp2-001`.
   No legacy seed or curated legacy case may appear.
Amended 2026-11-11: a run whose methods have since changed is listed and marked 'Earlier methods' (docs/rulings/2026-11-11-reader-and-issuer-report.md).
