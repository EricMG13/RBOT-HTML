"""CP-3 relative value owner: the journal seams over the reused engine.

`docs/CP3-OWNER-LEASE.md` adds no CP-3 arithmetic and no new composer: the reused engine
`deploy_vii.cp3_relative_value` validates the submission and composes the tables, claims and own
limitations. The store-free wrapper that once called it (`compute`) was removed: nothing used it.

Stage 2 connection (`docs/G1X-OWNER-CORE-PROTOCOL.md` §1-§2; CP-3 is a live-contract module, so the
core supplies only the items marked *all*): `QUALIFICATION`, `ENTRY_VALIDATOR` and `probe`. The
store adapter is the engine's own `cp3_upstream(store, attempt)`, which `_validate_step` and so
`probe` already use. CP-3 has no `view` (its step reads no `module_context`), no `RULES` (the
journal applies the product's `ToolRules`), no `precheck` and no reader: the lease names none.
"""

from deploy_vii.contracts import Module
from deploy_vii.cp3_relative_value import (
    PROMOTED,
    RelativeValueReport,
    _validate_step,
    cp3_module,
)
from deploy_vii.execution import Attempt, Execution, ExecutionSnapshot
from deploy_workflow.owners.cp1a import probe_one_step

# The `head_of` qualification `_verify` holds a settled CP-3 head to (`_QUALIFICATION["CP-3"]`).
QUALIFICATION = PROMOTED

# The validator CP-3's own entry hands `Execution.submit_step` (R4-2 invalid-step replay).
ENTRY_VALIDATOR = _validate_step


def _candidate(output: str, attempt: Attempt) -> Module:
    report = RelativeValueReport.model_validate_json(output)
    return cp3_module(report, attempt.inputs, attempt.number)


def probe(store: Execution, snapshot: ExecutionSnapshot, attempt: Attempt) -> None:
    """Raise `identity_mismatch` unless the settled attempt and the CP-3 head rebuild exactly:
    `_validate_step` over the bound heads, then `cp3_module` and `settle`."""
    probe_one_step(store, snapshot, attempt, validate=_validate_step, build=_candidate)
