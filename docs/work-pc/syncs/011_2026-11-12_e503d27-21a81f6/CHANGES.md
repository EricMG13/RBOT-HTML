# Changes for the work PC

From `e503d273393c` (the version the work PC last adapted) to `21a81f633802` (2026-11-12T03:55:29Z). 33 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `7eabcc4` 2026-11-12 docs(work-pc): change pack for e503d27
- `21a81f6` 2026-11-12 Run start: per-module effort, Balanced default, model choice (Merge pull request #54 from EricMG13/claude/silly-wing-3d4cce)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `VERIFICATION.md` | +49 −54 | L7-55, removed after L968 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/rulings/2026-11-11-run-start-submit.md` | +15 −2 | L6, L13, L16-28 |
| added | `docs/rulings/2026-11-12-tdg-mixed-effort-to-cp2.md` | +29 −0 | L1-29 |
| modified | `docs/templates/context-form.html` | +30 −9 | L348-353, L520, L1115-1121, L1230, L1662, L1778-1782, L1794-1795, L1799-1800, L2104, L2120, L2365-2366, L2489 |

### runs

| Status | File | +/- | Where |
|---|---|---|---|
| added | `runs/tdg-mixed-effort-comparison.md` | +100 −0 | L1-100 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/inbox/runs.py` | +41 −7 | L28-40, L65-67, L160-172, L174-182, removed after L196, L201, L207, removed after L226, L231 |
| modified | `src/deploy_workflow/inbox/scheduler.py` | +6 −4 | removed after L64, L105, L231-232, L253, L303-304, removed after L540, removed after L560 |
| modified | `src/deploy_workflow/inbox/startup.py` | +23 −14 | L13, L43-44, L84-89, L99-112 |
| modified | `src/deploy_workflow/model/handoff.py` | +19 −3 | L23, L58, L644, L656-663, L681, L687-689, L752, L755, L779, L957 |
| modified | `src/deploy_workflow/model/pricing.py` | +10 −8 | L159-166, L171-172 |
| modified | `src/deploy_workflow/model/turn.py` | +5 −2 | L20-21, L29, L42, L52 |
| modified | `src/deploy_workflow/model_testing/configs.py` | +2 −0 | L48-49 |
| modified | `src/deploy_workflow/owners/cpos.py` | +13 −1 | L602-611, L624, L652-653 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +78 −3 | L67, L76, L1996, L2001-2002, L2026, L2031-2064, L2079-2090, L2177-2184, L2192-2203, L2209-2213, L2227 |
| modified | `src/deploy_workflow/run_start/service.py` | +8 −7 | L44-50, L438 |
| modified | `src/deploy_workflow/run_start/submissions.py` | +39 −11 | L30, L32-33, L56-59, L84-85, L104-110, L117-125, L581-582, L589-590, L659, L662-663, L670, L682, L685-686, L718, L736-737 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/fixtures/fake_launcher.py` | +1 −0 | L28 |
| modified | `tests/fixtures/real_shape_launcher.py` | +1 −0 | L37 |
| modified | `tests/inbox_fixtures.py` | +3 −1 | L134-135, L143 |
| modified | `tests/model/test_budget.py` | +1 −1 | L378 |
| modified | `tests/model/test_live_limits.py` | +9 −1 | L47-50, L60-64 |
| modified | `tests/model/test_pricing.py` | +5 −3 | L87, L93, L98, L182, L184 |
| modified | `tests/model/test_providers.py` | +8 −1 | L277, L284-290 |
| modified | `tests/model/test_turn.py` | +4 −1 | L44, L123, L184, L198 |
| modified | `tests/test_cpos_launch.py` | +183 −0 | L4234-4347, L4375-4443 |
| modified | `tests/test_handoff_loop.py` | +69 −0 | L744-812 |
| modified | `tests/test_inbox_activity.py` | +9 −0 | L104-112 |
| modified | `tests/test_inbox_runs.py` | +51 −9 | removed after L86, removed after L110, L159, L167, L323, L352, L396, removed after L432, removed after L447, L452-497 |
| modified | `tests/test_inbox_scheduler.py` | +141 −2 | L11, L46, L55, L132-133, L137, L379, L410-543 |
| modified | `tests/test_run_start_page.py` | +117 −2 | L520-528, L694, L1550-1642, L2501-2514 |
| modified | `tests/test_run_start_scheduler.py` | +3 −5 | L43-44, L60, removed after L181, removed after L193 |
| modified | `tests/test_run_start_service.py` | +2 −0 | L51-52 |
| modified | `tests/test_run_start_submissions.py` | +142 −37 | L53-54, L238, L250-260, L272-289, removed after L297, L308, L311, L343, L346, L377, L405, L413, L418-420, L431, L494, L515, L552, L734, L737, L742, L749, L806, L846, L874, L886, L918, L951, L955-1040 |
