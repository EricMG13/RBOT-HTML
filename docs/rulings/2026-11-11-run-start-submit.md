# Standing ruling: run start page live launches on sol-medium

lifts: live-provider-pause
by: user
date: 2026-11-11
configs: sol-medium sol-high opus-medium opus-high

The user was asked: "The explicit paid action would become 'Submit after an approved summary',
at the same USD 20 cap", and said: "2. Approved". On the service: "one users CLI will provide for
all other users".

Scope: live launches started by `deploy_workflow.run_start` from a submission whose summary the
analyst approved, USD 20 per run folder, on the configurations listed above (amended below). The provider key comes from the
service's environment only; no credential file is read. Replaces 2026-11-09-inbox-automation.md.

Amendment, 2026-11-12 (user): "within run start lanuncher, set claude GPT mixed effort to default
(balanced). only within advanced, allow switching between Fast (all medium), balanced and High
(all high). but also model selection between Claude opus and GPT Sol".

The original ruling covered sol-medium only. From this amendment a run started from the page uses
GPT Sol (gpt-6.1-sol) or Claude Opus (claude-opus-5-5) at one of three efforts: Fast (every module
medium), Balanced (the default: high on the modules the effort map names, medium on the rest) or
High (every module high). Model and effort can differ from the defaults (GPT Sol, Balanced) only
at the Advanced level. The USD 20 cap per run folder and the Submit-on-an-approved-summary action
are unchanged. Effort map and its evidence: `runs/tdg-mixed-effort-comparison.md`.
