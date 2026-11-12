# Standing ruling: run start page live launches on sol-medium

lifts: live-provider-pause
by: user
date: 2026-11-11
configs: sol-medium, web-search

The user was asked: "The explicit paid action would become 'Submit after an approved summary',
at the same USD 20 cap", and said: "2. Approved". On the service: "one users CLI will provide for
all other users".

Scope: live launches started by `deploy_workflow.run_start` from a submission whose summary the
analyst approved, USD 20 per run folder, on sol-medium only. The provider key comes from the
service's environment only; no credential file is read. Replaces 2026-11-09-inbox-automation.md.

Amendment 2026-11-12 (web search for CP-DR on the run page): asked "Web search for CP-DR on the run
page ... Recommended: amend the ruling to add web search (USD 0.01 a search, up to USD 0.16 held per
call; only public names leave the machine)", the user said "1. approved". The `configs:` line now
also lists `web-search`; the "sol-medium only" in the scope above means the model, and search is
the one added grant. The research module is told to search with public names only; that is an
instruction to the model, not a control, so the queries it actually sent are kept in the run record
and any that carry a supplied file name or a source figure are flagged afterwards
(`search_query_flagged`; detection only). Case-kind rule (owner, 2026-11-12; replaces the controller's interim public-only default, which
was pending this confirmation). Asked about private cases, the owner said: "1. focus primarily
using reputable and relevant sources 2. there are privates cases. work environment permits the use
of these files". Web search is therefore offered when the run's case kind is `public` or
`private`, and is off only for `synthetic` (no real issuer to search for; no search fee held;
the launcher prints "Web:      off: synthetic case"). For a private case the run start page states,
before Submit, that the research module will search the web and that the issuer's name and the
questions it researches go to OpenAI's search. The same answer set the source guidance: CP-DR's
search instruction tells it to rely primarily on reputable, relevant sources and to state a weaker
source as a limitation (`model/handoff.py` `WEB_SEARCH_RULES`).
