# Sweep contract — refactoring and optimisation, end-to-end wiring, 2026-11-10

Owner: "Move to latest main - run /sweep refactoring and optimisation sweep make sure front to
back and end to end wiring."

| Field | Content |
|---|---|
| Authority | `AGENTS.md` at base: confidence-review, rewrite-tournament post-edit for nontrivial changed functions, `tools/quality_gate.py`, fast targeted tests, one `VERIFICATION.md` entry. Owner's global rules (`~/.claude/CLAUDE.md`). Prior sweep `docs/sweeps/2026-11-10/` (its open rows R7, R8 stay left). |
| Base and comparison | Start tree `origin/main` = `53a5632` (PR 27 merged), clean, branch `claude/sweep-wiring`. Comparison base `c721a0f` (the prior sweep's last merge, PR 18): range `c721a0f..53a5632` = PRs 19–27. |
| Scope | The run path front to back: context form (`docs/templates/context-form.html`) → `context.py` reader → launcher (`owners/cpos_launch.py`) → CP-OS (`owners/cpos.py`, `model/handoff.py`) → delivery (`handoff_delivery.py`, `markdown_delivery.py`, `owners/cpos_forecast.py`) → library (`update_library.py`, `library_index.py`, `credit_os/store.py`) → screens (`credit_os/web/*.js`); and inbox drop → watcher → launcher → filing → library. Depth: the range's changed files in full; the rest by journey probes. |
| Excluded | `src/deploy_vii/` engine internals beyond the registry, `apps/issuer-library/engine/`, `runs/`, predecessor repositories, historical live run folders. |
| Decisions and permissions | No new dependency, pin or behaviour change beyond a confirmed defect's repair. No provider call and no paid run (owner: "Not now"). Commit and open a PR; no merge. |
| Protected behaviour | Exact amounts, missing versus zero, currency, dates, source identities; delivery bytes of existing runs (`delivery_changed` must not fire on a re-verify); the USD 20 per-run cap and daily limit of the watcher; the library's methodology filter; checks listed below. |
| Gates and baseline | `uv run python tools/quality_gate.py --base origin/main`; `node --test apps/issuer-library/credit_os/web/static.test.cjs apps/issuer-library/credit_os/web/calendar.test.cjs`; the `checks.yml` pytest list plus `tests/test_handoff_loop.py tests/test_context_form.py`, known failures deselected; once per branch `uv run pytest -m browser tests/test_library_page_browser.py`. Logs: `.superpowers/sdd/sweep-wiring/evidence/base-*.log`. |
| Targets | Defects: only those reproduced by a failing journey probe or test at base. Structure: in the range's files, a function over the gate's limits, unused reachable code, or one fact kept in two places with no test tying them. Performance: wall-clock median of 5 runs after 1 warm-up, or a deterministic work count; noise = max − min; accept a gain ≥ 20% and ≥ 2 × noise with unchanged output. Impact bands: 1 < 5%, 2 5–20%, 3 20–40%, 4 40–70%, 5 > 70% of the measured path; score = impact × confidence ÷ risk, floor 2, confidence ≥ 2. |
| Runtime | Controller inline (this session has written the range's code directly, owner-accepted); `mx-*` reviewers where available. No GitNexus index: callers traced with grep. Browser checks: headless Chrome via the existing `visit` helper and the app's browser pane. |
| Stop conditions | At most 6 landed items, 2 fix rounds each; branch diff ≤ 800 changed lines; the rest deferred. |
| State and evidence | `.superpowers/sdd/sweep-wiring/` (ignored): `register.md`, `progress.md`, `evidence/`, probes. Committed: this contract, `goal.txt`, `REPORT.md`. |
| Completion | Register rows dispositioned; gates above exit 0 on the final tree; `REPORT.md` with probes and measurements; one `VERIFICATION.md` entry; PR open, unmerged. |
