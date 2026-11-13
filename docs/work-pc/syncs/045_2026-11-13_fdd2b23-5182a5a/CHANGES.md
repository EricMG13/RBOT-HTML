# Changes for the work PC

From `fdd2b234abfb` (the version the work PC last adapted) to `5182a5a506b0` (2026-11-13T04:44:08Z). 34 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `9e4b74c` 2026-11-13 docs(work-pc): change pack for fdd2b23
- `5182a5a` 2026-11-13 CP-OS: send the corrected Deploy V methods (includes and supersedes #83) (Merge pull request #93 from EricMG13/claude/deploy-v-methods)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### (root)

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `METHODOLOGY-REVIEW.md` | +62 −3 | L700-705, L710-765 |
| modified | `VERIFICATION.md` | +14 −0 | L36-49 |

### docs

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `docs/reuse/selected-methods/manifest.json` | +156 −54 | L14-18, L41-45, L50-54, L60-62, L94-97, L109-112, L124-129, L169-174, L179-181, L186-188, L193-195, L200-202, L214-216, L221-223, L228-233, L476-481, L486-488, L537, L582-584, L586-588, L676-677, L832-836, L1017-1086, L1089 |
| added | `docs/reuse/selected-methods/skills/cp-1a-business-transaction-fact-pack/SKILL.md` | +568 −0 | L1-568 |
| added | `docs/reuse/selected-methods/skills/cp-1a-business-transaction-fact-pack/references/REF_CP-1A_STEPS.md` | +124 −0 | L1-124 |
| added | `docs/reuse/selected-methods/skills/cp-1a-business-transaction-fact-pack/references/REF_CP-2C_STEPS.md` | +312 −0 | L1-312 |
| modified | `docs/reuse/selected-methods/skills/cp-1d-earnings-quality/SKILL.md` | +2 −1 | L165, L183 |
| added | `docs/reuse/selected-methods/skills/cp-2-fundamental-credit-synthesizer/SKILL.md` | +326 −0 | L1-326 |
| added | `docs/reuse/selected-methods/skills/cp-2-fundamental-credit-synthesizer/references/REF_CP-2_STEPS.md` | +350 −0 | L1-350 |
| added | `docs/reuse/selected-methods/skills/cp-2a-downside-pathway/references/CP-2A_STRESS_DESIGN_CPOS.md` | +32 −0 | L1-32 |
| modified | `docs/reuse/selected-methods/skills/cp-2d-liquidity-cash-flow-bridge/SKILL.md` | +17 −10 | L22, L28, L73, L75-82, L84, L86, L88, L111, L116, L253 |
| modified | `docs/reuse/selected-methods/skills/cp-2d-liquidity-cash-flow-bridge/references/REF_CP-2D_STEPS.md` | +2 −2 | L96, L113 |
| modified | `docs/reuse/selected-methods/skills/cp-2g-forward-credit-model/references/REF_CP-2G_STEPS.md` | +1 −1 | L19 |
| modified | `docs/reuse/selected-methods/skills/cp-2h-ratings-migration-trigger/SKILL.md` | +1 −1 | L96 |
| modified | `docs/reuse/selected-methods/skills/cp-3-relative-value-security-selection/SKILL.md` | +3 −3 | L115, L517, L582 |
| added | `docs/reuse/selected-methods/skills/cp-3c-refinancing-lme-risk/SKILL.md` | +215 −0 | L1-215 |
| added | `docs/reuse/selected-methods/skills/cp-3c-refinancing-lme-risk/references/CP-3C_RUNBOOK.md` | +151 −0 | L1-151 |
| added | `docs/reuse/selected-methods/skills/cp-3c-refinancing-lme-risk/references/REF_CP-3C_STEPS.md` | +289 −0 | L1-289 |
| modified | `docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/SKILL.md` | +41 −23 | L41, L47, L88-96, L299, L301-308, L310, L312, L314, L351, L353, L403-404, L455, L457-464, L466, L468, L470, L502, L530 |
| modified | `docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/references/CP-4A_RUNBOOK.md` | +3 −3 | L40, L98, L143 |
| modified | `docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/references/CP-4B_RUNBOOK.md` | +4 −4 | L39, L65, L114, L139 |
| modified | `docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/references/CP-4_RUNBOOK.md` | +3 −3 | L42, L63, L106 |
| modified | `docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/references/REF_CP-4A_STEPS.md` | +8 −8 | L30, L74, L93, L188, L206, L263, L278, L407 |
| modified | `docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/references/REF_CP-4B_STEPS.md` | +6 −6 | L25, L31, L42, L77, L110, L177 |
| modified | `docs/reuse/selected-methods/skills/cp-4-legal-covenant-interpreter/references/REF_CP-4_STEPS.md` | +2 −2 | L46, L99 |
| modified | `docs/reuse/selected-methods/skills/cp-4c-restructuring-fulcrum/SKILL.md` | +21 −25 | L8, L12, L30, L41, L47, L88-96, L109, L114-115, L119, L124, L134, L243 |
| modified | `docs/reuse/selected-methods/skills/cp-5-evidence-trace-validator/references/CP-5_RUNBOOK.md` | +6 −4 | L9, L11, L108, L174, L176, L253 |
| modified | `docs/reuse/selected-methods/skills/cp-5-evidence-trace-validator/references/REF_CP-5A_STEPS.md` | +1 −1 | L88 |
| modified | `docs/reuse/selected-methods/skills/cp-6-ic-debate-challenge/SKILL.md` | +5 −5 | L8, L170, removed after L171, L255, L334, removed after L335, L417 |
| modified | `docs/reuse/selected-methods/skills/cp-dr-deep-research/SKILL.md` | +60 −11 | L77, L104-118, L128-129, L142-143, L145-150, L152-157, L159-184, L187, L205 |
| modified | `docs/reuse/selected-methods/skills/cp-dr-deep-research/references/REF_CP-DR_STEPS.md` | +2 −2 | L63, L83 |

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +88 −18 | L147-153, L155-162, L164-170, L184-189, L194-197, L225-232, L263-267, removed after L271, L276, L280-282, L364-375, L1768-1770, L1773, L1782-1798, L1807, L1811-1813, L2226, L2538 |
| modified | `src/deploy_workflow/run_expectations.py` | +5 −4 | L389-391, L457-458 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_cpos_launch.py` | +591 −28 | L10, L52, L424-438, L440, L548, L575, L1512, L1707, L1712-1716, L1718-1721, L1740-1755, L1766-2150, L2168-2171, L2236-2264, L2266, L2268-2269, L2271-2287, L2384-2385, L2470-2474, L6270-6368 |
