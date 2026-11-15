"""The selected method each module is sent: the method files, in instruction order, per
module (moved from ``cpos_launch``; the launcher re-exports every name).
"""

from deploy_workflow.prose_checks import DATA_MODULES

_SKILLS = "docs/reuse/selected-methods/skills/"
_VII = "src/deploy_vii/methods/"
# The Confidence Score rules `confidence_score.py` applies; the script cannot run in this transport.
_SCORE = "docs/reuse/selected-methods/CANON_SHARED.md § CP_CONFIDENCE_SCORE.md"
# Owner, 2026-11-13 (T4, ruling 2026-11-13-appendix-and-routing-scope.md): the registers a module
# no longer writes, one `## <module>` section each, sent last in the module's method block. Only
# the ten modules the two retained Sol runs measured have one.
REGISTER_SCOPE = "docs/reuse/selected-methods/CPOS_REGISTER_SCOPE.md"
REGISTER_SCOPE_MODULES = (
    *("CP-0", "CP-1A", "CP-DR", "CP-2", "CP-2A", "CP-2E", "CP-2G", "CP-3", "CP-5", "CP-6"),
)
# The method each module runs, per METHODOLOGY-REVIEW.md and what the 2026-11-05 live campaigns
# consumed. prompts/CP-0.md and CP-1-intake.md are TDG case instructions, so they are left out.
# Owner, 2026-11-10 ("Fix all"): each skill is sent every companion its SKILL.md calls mandatory
# or binding (a runbook, a phase's method bundle). Each sent file's own entry in
# docs/reuse/selected-methods/manifest.json records its source, any named edits and, where
# recorded, its revision. Companions the SKILL opens only "to resolve an ambiguity" (the schema
# and system references) are archived, not sent. CANON_SHARED.md is sent only as the reader-layer
# sections of READER_LAYER, to every prose module (ruling
# 2026-11-11, decision 8; the Analytical appendix section was added 2026-11-13, Deploy V methods
# plan, Task 6, because the section above it ends at its heading); the rest of it is archived.
_SELECTED: dict[str, tuple[str, ...]] = {
    # Owner-directed, 2026-11-13 (Deploy V methods plan, Task 3): Deploy V's skill and step file,
    # byte-identical to Deploy V c4d2e35 (the readiness part; CP-PARSE's own step file, the schema
    # and system references are archived, not sent). CP0_BLOCK says what the launcher already did.
    # The DEPLOY VII stand-in (cp0.md, a JSON ReadinessReview) is no longer sent.
    "CP-0": (
        _SKILLS + "cp-0-source-readiness/SKILL.md",
        _SKILLS + "cp-0-source-readiness/references/REF_CP-0_STEPS.md",
    ),
    # Owner, 2026-11-13 (CP-1 moves to the Deploy V method): caos-databricks dfff264's skill,
    # runbook and step file with named edits (no workbook step, no routing, host section layout,
    # carrying-value debt, reported EBITDA first; manifest.json lists them). The schema and
    # system references are archived, not sent. prompts/CP-1.md stays: its amendments are project
    # rules. The 26 KB of STEP_CONTRACTS written for the JSON runtime is no longer sent.
    "CP-1": (
        _SKILLS + "cp-1-canonical-data-foundation/SKILL.md",
        _SKILLS + "cp-1-canonical-data-foundation/references/CP-1_RUNBOOK.md",
        _SKILLS + "cp-1-canonical-data-foundation/references/REF_CP-1_STEPS.md",
        "prompts/CP-1.md",
    ),
    # Owner, 2026-11-13 ("Build rec. 1, then run"): Deploy V's skill from cp-os b57a344 with the
    # bundle its SKILL binds on every run. The DEPLOY VII stand-in (cp1a.md) is no longer sent.
    "CP-1A": (
        _SKILLS + "cp-1a-business-transaction-fact-pack/SKILL.md",
        _SKILLS + "cp-1a-business-transaction-fact-pack/references/REF_CP-1A_STEPS.md",
        _SKILLS + "cp-1a-business-transaction-fact-pack/references/REF_CP-2C_STEPS.md",
    ),
    # Deploy V's skill: earnings_delta.md needs the structured runtime's `read_inputs` view, which
    # CP-OS does not give, so it blocked on every CP-OS run (2026-11-09, 2026-11-10).
    "CP-1B": (
        _SKILLS + "cp-1b-earnings-delta/SKILL.md",
        _SKILLS + "cp-1b-earnings-delta/references/REF_CP-1B_STEPS.md",
    ),
    "CP-1C": (
        _SKILLS + "cp-1c-peer-benchmark/SKILL.md",
        _SKILLS + "cp-1c-peer-benchmark/references/REF_CP-1C_STEPS.md",
    ),
    "CP-1D": (_SKILLS + "cp-1d-earnings-quality/SKILL.md",),
    # Owner, 2026-11-11: the Short Credit Snapshot's one page, read from CP-1's handoff alone.
    "CP-L10": (_VII + "cpl10.md",),
    # Owner, 2026-11-13 ("Build rec. 1, then run"): Deploy V's skill from cp-os b57a344 with the
    # bundle its SKILL binds on every run. The DEPLOY VII stand-in (cp2.md) is no longer sent.
    "CP-2": (
        _SKILLS + "cp-2-fundamental-credit-synthesizer/SKILL.md",
        _SKILLS + "cp-2-fundamental-credit-synthesizer/references/REF_CP-2_STEPS.md",
    ),
    "CP-2A": (
        _SKILLS + "cp-2a-downside-pathway/SKILL.md",
        _SKILLS + "cp-2a-downside-pathway/references/REF_CP-2A_STEPS.md",
        _SKILLS + "cp-2a-downside-pathway/references/REF_CP-2B_STEPS.md",
        # Owner, 2026-11-13 (Deploy V methods plan, Task 6): a CP-OS-only copy of cp2a.md whose
        # tables are T2DS.n, since cp2a.md's T2B.n collide with the step file's. cp2a.md stays on
        # disk, unchanged, for the structured runtime.
        _SKILLS + "cp-2a-downside-pathway/references/CP-2A_STRESS_DESIGN_CPOS.md",
    ),
    "CP-2D": (
        _SKILLS + "cp-2d-liquidity-cash-flow-bridge/SKILL.md",
        _SKILLS + "cp-2d-liquidity-cash-flow-bridge/references/REF_CP-2D_STEPS.md",
    ),
    "CP-2E": (
        _SKILLS + "cp-2e-macro-fx-hedging-sensitivity/SKILL.md",
        _SKILLS + "cp-2e-macro-fx-hedging-sensitivity/references/REF_CP-2E_STEPS.md",
        _SKILLS + "cp-2e-macro-fx-hedging-sensitivity/references/REF_CP-2F_STEPS.md",
    ),
    "CP-2G": (
        _SKILLS + "cp-2g-forward-credit-model/SKILL.md",
        _SKILLS + "cp-2g-forward-credit-model/references/REF_CP-2G_STEPS.md",
    ),
    "CP-2H": (
        _SKILLS + "cp-2h-ratings-migration-trigger/SKILL.md",
        _SKILLS + "cp-2h-ratings-migration-trigger/references/REF_CP-2H_STEPS.md",
    ),
    "CP-3": (
        _SKILLS + "cp-3-relative-value-security-selection/SKILL.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/REF_CP-3_STEPS.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/REF_CP-3A_STEPS.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/CP-3A_RUNBOOK.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/REF_CP-3B_STEPS.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/CP-3B_RUNBOOK.md",
        _SKILLS + "cp-3-relative-value-security-selection/references/CP-3_SCHEMA_REFERENCE.md",
    ),
    # Owner-directed, 2026-11-13 (Deploy V methods plan, Task 2): Deploy V's skill with the runbook
    # and step file its SKILL binds, from Deploy V c4d2e35, plus the named r17 `Scale` edit to
    # register T3D.2. The DEPLOY VII stand-in (cp3c.md) is no longer sent.
    "CP-3C": (
        _SKILLS + "cp-3c-refinancing-lme-risk/SKILL.md",
        _SKILLS + "cp-3c-refinancing-lme-risk/references/REF_CP-3C_STEPS.md",
        _SKILLS + "cp-3c-refinancing-lme-risk/references/CP-3C_RUNBOOK.md",
    ),
    "CP-3D": (
        _SKILLS + "cp-3d-market-implied-risk/SKILL.md",
        _SKILLS + "cp-3d-market-implied-risk/references/REF_CP-3D_STEPS.md",
    ),
    "CP-4": (
        _SKILLS + "cp-4-legal-covenant-interpreter/SKILL.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/CP-4_RUNBOOK.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/REF_CP-4_STEPS.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/CP-4A_RUNBOOK.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/REF_CP-4A_STEPS.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/CP-4B_RUNBOOK.md",
        _SKILLS + "cp-4-legal-covenant-interpreter/references/REF_CP-4B_STEPS.md",
    ),
    "CP-4C": (
        _SKILLS + "cp-4c-restructuring-fulcrum/SKILL.md",
        _SKILLS + "cp-4c-restructuring-fulcrum/references/REF_CP-4C_STEPS.md",
    ),
    "CP-5": (
        _SKILLS + "cp-5-evidence-trace-validator/SKILL.md",
        _SKILLS + "cp-5-evidence-trace-validator/references/CP-5_RUNBOOK.md",
        _SKILLS + "cp-5-evidence-trace-validator/references/REF_CP-5_STEPS.md",
        _SKILLS + "cp-5-evidence-trace-validator/references/REF_CP-5A_STEPS.md",
    ),
    "CP-6": (
        _SKILLS + "cp-6-ic-debate-challenge/SKILL.md",
        _SKILLS + "cp-6-ic-debate-challenge/references/REF_CP-6_STEPS.md",
        _SKILLS + "cp-6-ic-debate-challenge/references/REF_CP-6A_STEPS.md",
    ),
    # Owner, 2026-11-11: what has changed since the last run (replaces the deliverable comparison).
    "CP-8": (_VII + "cp8.md",),
    # Owner-directed, 2026-11-13 (Deploy V methods plan, Task 4): one CP-DR text, the cp-os
    # version 2.0 skill (sha256 0cc76aea, cp-os 5a78f93) with two named edits (open-web limit
    # conditional on the web-search rules; gap row typed `gap`, missing evidence never Blocked).
    # `cpdr.md` stays on disk for another runtime; it is no longer sent: it told the model
    # "Python composes the tables".
    "CP-DR": (
        _SKILLS + "cp-dr-deep-research/SKILL.md",
        _SKILLS + "cp-dr-deep-research/references/REF_CP-DR_STEPS.md",
        _SKILLS + "cp-os-credit-os/references/CP_DR_RESEARCH_BRIEF_V1.md",
    ),
}
_CANON = "docs/reuse/selected-methods/CANON_SHARED.md"
# The reader-facing layer every prose module is sent (not the data modules).
_APPENDIX = f"{_CANON} § Analytical appendix"
READER_LAYER = (
    f"{_CANON} § Reader-facing research layer",
    f"{_CANON} § Credit-research reading order",
    # PROSE_PASSAGES says the canon's "table and appendix rules still apply"; the first section
    # ends at the next `####` heading, so the appendix rule needs its own entry.
    _APPENDIX,
)
METHODS: dict[str, tuple[str, ...]] = {
    module: (
        *((*paths, _SCORE) if any(p.startswith(_SKILLS) for p in paths) else paths),
        *(() if module in DATA_MODULES else READER_LAYER),
        *((f"{REGISTER_SCOPE} § {module}",) if module in REGISTER_SCOPE_MODULES else ()),
    )
    for module, paths in _SELECTED.items()
}
