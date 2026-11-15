"""CP-1B owner checkpoint: identifiers, error codes, retained record contracts, limits and pins.

Moved unchanged from `earnings_workflow`, which re-exports every name.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, JsonValue, StrictInt, field_validator, model_validator

from deploy_vii.contracts import Contract, Hash, Identifier, Input, Module, Run, Text
from deploy_vii.cp1_workflow import FinancialSubmission
from deploy_vii.downstream_readiness import DownstreamReview
from deploy_vii.execution import Head
from deploy_vii.narrative import NarrativeReview
from deploy_vii.quality import QualityReview
from deploy_vii.readiness import ReadinessReview
from deploy_vii.source_context import SourceContextReview
from deploy_workflow.financial_workflow import FinancialBinding, FinancialCall, InputRead
from deploy_workflow.workflow import SourceEvidence

OwnerCaseId = Literal["E-QOQ-FLAT", "E-NO-YOY", "E-REQUIRED-CP1-MISSING"]
Transport = Literal["python-api", "bounded-json-lines/1"]
Phase = Literal[
    "source_readiness",
    "source_context",
    "financials",
    "narrative",
    "readiness",
    "quality",
    "earnings_delta",
    "complete",
    "failed",
]
OutcomeKind = Literal["owner_settled", "cp1_not_authorized"]
FactStatus = Literal["known", "missing", "conflicting", "not_applicable"]
JsonObject = dict[str, JsonValue]
_AttemptNo = Annotated[StrictInt, Field(ge=0, le=1)]
_Positive = Annotated[StrictInt, Field(ge=1)]
_Count = Annotated[StrictInt, Field(ge=0)]
_ERRORS = frozenset(
    {
        "bad_arguments",
        "not_permitted",
        "stale_binding",
        "identity_mismatch",
        "participation_incomplete",
        "transport_limit",
        "validation_failed",
        "internal_error",
    }
)


class OwnerError(ValueError):
    def __init__(self, code: str) -> None:
        if code not in _ERRORS:
            raise ValueError("bad_arguments")
        super().__init__(code)
        self.code = code


class WorkflowState(Contract):
    phase: Phase
    module_id: Literal["CP-0", "CP-1", "CP-1B"] | None
    step_id: str | None
    ticket_id: Identifier | None
    attempt: _AttemptNo | None
    prior_period_id: Identifier
    current_period_id: Identifier
    outcome: OutcomeKind | None

    @model_validator(mode="after")
    def active_identity(self) -> WorkflowState:
        active = (self.module_id, self.step_id, self.ticket_id, self.attempt)
        if self.phase in {"complete", "failed"}:
            if any(x is not None for x in active):
                raise ValueError("terminal state has no active identity")
        elif any(x is None for x in active) or self.outcome is not None:
            raise ValueError("active state requires its ticket identity")
        return self


class OwnerClose(Contract):
    schema_version: Literal["cp1b-owner-close/1"] = "cp1b-owner-close/1"
    outcome: OutcomeKind
    owner_receipt_sha256: Hash
    owner_snapshot_sha256: Hash


class ReviewOutcome(Contract):
    schema_version: Literal["cp1b-review-outcome/1"] = "cp1b-review-outcome/1"
    module_id: str
    step_id: str
    ticket_id: Identifier
    attempt: _AttemptNo
    disposition: Literal["valid", "invalid", "refused"]
    issue_count: _Count
    error_codes: tuple[str, ...]
    snapshot_sha256: Hash
    next_phase: Phase
    stored_payload_sha256: Hash | None

    @field_validator("error_codes")
    @classmethod
    def public_codes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not set(value) <= _ERRORS:
            raise ValueError("unrecognized owner error category")
        return value


class OwnerBinding(Contract):
    run_id: Identifier
    issuer_id: Identifier
    as_of: str
    method_version: str
    pack_sha256: Hash
    snapshot_sha256: Hash
    module_id: Literal["CP-1B"]
    step_id: Literal["earnings_delta"]
    ticket_id: Identifier
    attempt: _AttemptNo
    inputs: tuple[Input, ...]


class FactReference(Contract):
    producer_module_id: Literal["CP-1"]
    producer_sha256: Hash
    fact_id: Identifier
    table_id: Identifier
    row_id: Identifier
    field: Identifier


class CitationHandle(Contract):
    source_id: Identifier
    source_sha256: Hash
    locator: Text


class OperandReference(Contract):
    fact: FactReference
    period_id: Identifier
    basis_id: Identifier
    source_period: Text
    source_basis: Text
    fact_sha256: Hash
    citation_handles: tuple[CitationHandle, ...]


class OperandLineage(Contract):
    measure_id: Identifier
    prior: OperandReference | None
    current: OperandReference
    companions: tuple[FactReference, ...]


class MeasureSelection(Contract):
    measure_id: Identifier
    prior_fact_id: Identifier | None
    current_fact_id: Identifier
    companion_fact_ids: tuple[Identifier, ...]


class EarningsDeltaReview(Contract):
    schema_version: Literal["cp1b-review/1"] = "cp1b-review/1"
    prior_period_id: Identifier
    current_period_id: Identifier
    selections: Annotated[tuple[MeasureSelection, ...], Field(min_length=12, max_length=12)]
    comparison_assessment: Literal["flat_sequential", "comparative_not_supplied"]
    driver_assessment: Literal["not_supplied"]
    guidance_assessment: Literal["not_supplied"]


class EarningsPointRecord(Contract):
    measure_id: str
    prior_fact_id: str | None
    current_fact_id: str
    companion_fact_ids: tuple[str, ...]
    prior_value: Decimal | None
    current_value: Decimal | None
    prior_status: FactStatus
    current_status: FactStatus
    delta: Decimal | None
    delta_status: FactStatus
    delta_unit: str
    growth: Decimal | None
    growth_status: FactStatus
    reason: str | None
    unit: str
    currency: str | None
    scale: Decimal


class EarningsReportRecord(Contract):
    producer_sha256: str
    prior_period_id: str
    current_period_id: str
    prior_basis_id: str | None
    current_basis_id: str
    points: tuple[EarningsPointRecord, ...]
    limitations: tuple[str, ...]


class OwnerToolReceipt(Contract):
    schema_version: Literal["tool-receipt/1"] = "tool-receipt/1"
    call_id: str
    sequence: _Positive
    binding: OwnerBinding
    tool: str
    arguments: JsonObject
    status: Literal["ok", "refused", "error"]
    body: JsonObject | None
    error_code: str | None
    source_evidence: SourceEvidence

    @field_validator("source_evidence")
    @classmethod
    def no_raw_source_credit(cls, value: SourceEvidence) -> SourceEvidence:
        if value != SourceEvidence():
            raise ValueError("owner has no raw source authority")
        return value


class OwnerSession(Contract):
    session_id: Identifier
    index: _Positive
    binding: OwnerBinding
    normalized_grant_json: Text
    access_manifest_json: Text


class OwnerAccessRead(Contract):
    schema_version: Literal["cp1b-access-read/1"] = "cp1b-access-read/1"
    session_id: Identifier
    sequence: _Positive
    binding: OwnerBinding
    access_manifest_json: Text


class OwnerToolCall(Contract):
    schema_version: Literal["cp1b-owner-call/1"] = "cp1b-owner-call/1"
    ordinal: _Positive
    session_id: Identifier
    receipt: OwnerToolReceipt


class EarningsParticipation(Contract):
    schema_version: Literal["cp1b-participation/1"] = "cp1b-participation/1"
    binding: OwnerBinding
    session_id: Identifier
    grant_sha256: Hash
    manifest_sha256: Hash
    access_read_sha256: Hash
    call_ids: tuple[str, ...]
    successful_call_ids: tuple[str, ...]
    manifest_call_ids: tuple[str, ...]
    period_lookup_call_ids: tuple[str, ...]
    metric_lookup_call_ids: tuple[str, ...]
    citation_call_ids: tuple[str, ...]


class OwnerSubmissionEnvelope(Contract):
    schema_version: Literal["cp1b-owner-submission/1"] = "cp1b-owner-submission/1"
    binding: OwnerBinding
    raw_review_sha256: Hash
    review: EarningsDeltaReview
    participation: EarningsParticipation


class EarningsOwnerStage(Contract):
    schema_version: Literal["cp1b-owner-stage/1"] = "cp1b-owner-stage/1"
    review_sha256: Hash
    participation_sha256: Hash
    report: EarningsReportRecord
    operands: tuple[OperandLineage, ...]
    candidate: Module


class BoundSubmission(Contract):
    schema_version: Literal["cp1b-bound-submission/1"] = "cp1b-bound-submission/1"
    binding: FinancialBinding | OwnerBinding
    raw_payload_sha256: Hash
    stored_payload_sha256: Hash
    canonical_review_sha256: Hash | None
    call_ids: tuple[str, ...]
    successful_call_ids: tuple[str, ...]
    source_evidence: SourceEvidence
    input_read_hashes: tuple[Hash, ...]
    participation_sha256: Hash | None
    owner_session_id: Identifier | None
    normalization_paths: tuple[str, ...]
    prefilled_paths: tuple[str, ...]
    prefilled_kinds: tuple[str, ...]

    @model_validator(mode="after")
    def selected_session(self) -> BoundSubmission:
        if isinstance(self.binding, OwnerBinding) != (self.owner_session_id is not None):
            raise ValueError("owner session association differs from binding kind")
        return self


class SubmissionIntent(Contract):
    index: _Positive
    binding: BoundSubmission
    snapshot_before_sha256: Hash


class SubmissionOutcome(Contract):
    intent_sha256: Hash
    disposition: Literal["valid", "invalid", "refused"]
    issues: tuple[str, ...]
    snapshot_after_sha256: Hash
    step_sha256: Hash | None
    step_output_sha256: Hash | None
    candidate_sha256: Hash | None
    result_sha256: Hash | None


class BeginRecord(Contract):
    index: _Positive
    module_id: Literal["CP-0", "CP-1", "CP-1B"]
    snapshot_before_sha256: Hash
    snapshot_after_sha256: Hash
    ticket_id: Identifier | None
    attempt: _AttemptNo | None
    error_code: Literal["not_authorized", "not_permitted"] | None


class OwnerHeadRecord(Contract):
    ticket_id: Identifier
    attempt: _AttemptNo
    head: Head
    candidate_sha256: Hash
    step_sha256s: tuple[Hash, ...]


class SourceIdentity(Contract):
    source_id: Identifier
    status: Literal["ready", "missing", "unreadable"]
    sha256: Hash | None


class OwnerPins(Contract):
    case_manifest_sha256: Hash
    source_manifest_sha256: Hash
    core_expected_sha256: Hash
    access_expected_sha256: Hash
    render_expected_sha256: Hash
    owner_expected_sha256: Hash
    sources: tuple[SourceIdentity, ...]


class OwnerSetup(Contract):
    schema_version: Literal["cp1b-owner-setup/1"] = "cp1b-owner-setup/1"
    run: Run
    pack_sha256: Hash
    initial_snapshot_sha256: Hash
    case_id: OwnerCaseId
    pins: OwnerPins
    participant: Text
    transport: Transport
    policy_sha256: Hash


class TransportMessage(Contract):
    index: _Positive
    operation: Literal["state", "invoke", "read_inputs", "submit_review", "close", "invalid"]
    request_sha256: Hash


class AuditEntry(Contract):
    kind: Literal[
        "transport-messages",
        "begins",
        "foundation-calls",
        "foundation-reads",
        "owner-sessions",
        "owner-reads",
        "owner-calls",
        "bindings",
        "intents",
        "outcomes",
        "participations",
        "stages",
        "payloads",
        "setup",
    ]
    sha256: Hash


class EarningsOwnerReceipt(Contract):
    schema_version: Literal["cp1b-owner-receipt/1"] = "cp1b-owner-receipt/1"
    run: Run
    pack_sha256: Hash
    owner_snapshot_sha256: Hash
    case_id: OwnerCaseId
    pins: OwnerPins
    participant: Text
    transport: Transport
    outcome: OutcomeKind
    cp0: OwnerHeadRecord
    cp1: OwnerHeadRecord | None
    cp1b: OwnerHeadRecord | None
    cp1b_stage_sha256: Hash | None
    transport_messages: tuple[TransportMessage, ...]
    begins: tuple[BeginRecord, ...]
    foundation_calls: tuple[FinancialCall, ...]
    foundation_input_reads: tuple[InputRead, ...]
    owner_sessions: tuple[OwnerSession, ...]
    owner_access_reads: tuple[OwnerAccessRead, ...]
    owner_calls: tuple[OwnerToolCall, ...]
    submission_intents: tuple[SubmissionIntent, ...]
    submission_outcomes: tuple[SubmissionOutcome, ...]
    audit_inventory: tuple[AuditEntry, ...]
    publication_files: tuple[str, ...]

    @model_validator(mode="after")
    def owner_boundary(self) -> EarningsOwnerReceipt:
        if self.publication_files:
            raise ValueError("owner checkpoint has no publication")
        if self.outcome == "owner_settled":
            if self.cp1 is None or self.cp1b is None or self.cp1b_stage_sha256 is None:
                raise ValueError("settled owner requires complete foundation and stage")
        elif any(x is not None for x in (self.cp1, self.cp1b, self.cp1b_stage_sha256)) or any(
            (
                self.owner_sessions,
                self.owner_access_reads,
                self.owner_calls,
            )
        ):
            raise ValueError("missing CP1 cannot have owner results or participation")
        return self


MAX_LINE = 4194304
MAX_JSON_DEPTH = 100  # nesting bound, well below pydantic's JSON limit of 200
MAX_MESSAGES = 2048
MAX_OWNER_CALLS = 1024
MAX_OWNER_SESSIONS = 16
MAX_ACCESS_READS = 16
MAX_FOUNDATION = 16
MAX_AUDIT = 16384
MAX_RECEIPT = 67108864
_SOURCE_PHASES = frozenset({"source_readiness", "source_context", "financials"})
_MEASURES = (
    "revenue",
    "ebitda",
    "adjusted_ebitda",
    "ebitda_margin",
    "cfo_reported",
    "capex",
    "fcf",
    "cash_closing",
    "total_debt",
    "net_debt",
    "total_leverage_reported",
    "net_leverage_reported",
)
_PROJECTED = tuple(
    sorted(
        (
            "amount",
            "basis",
            "calculation_id",
            "calculation_status",
            "citation_handles",
            "currency",
            "denominator",
            "fact_id",
            "field",
            "label",
            "limitation",
            "period",
            "row_id",
            "scale",
            "status",
            "table_id",
            "text",
            "unit",
            "value_class",
        )
    )
)
_SCHEMAS: dict[str, type[Contract]] = {
    "source_readiness": ReadinessReview,
    "source_context": SourceContextReview,
    "financials": FinancialSubmission,
    "narrative": NarrativeReview,
    "readiness": DownstreamReview,
    "quality": QualityReview,
    "earnings_delta": EarningsDeltaReview,
}
_KINDS: dict[str, type[Contract]] = {
    "setup": OwnerSetup,
    "transport-messages": TransportMessage,
    "begins": BeginRecord,
    "foundation-calls": FinancialCall,
    "foundation-reads": InputRead,
    "owner-sessions": OwnerSession,
    "owner-reads": OwnerAccessRead,
    "owner-calls": OwnerToolCall,
    "bindings": BoundSubmission,
    "intents": SubmissionIntent,
    "outcomes": SubmissionOutcome,
    "participations": EarningsParticipation,
    "stages": EarningsOwnerStage,
}
_PINS = {
    "manifest.json": "60ed95782648064db7806bb7f0714fe030f9563424df50e17500803a2edfb7ec",
    "source_manifest": "6b3eeffe0871923f9f3ed9b6fd6739c86be2ee4dd8a7d35e8a6a516581b93432",
    "expected.json": "041e2e05cec282658e28a9f99f1c2e93e6f6d8c2ab17d790aad760676a6c2599",
    "access-expected.json": "a8210ba05e81c3cba04634bfe82e3e7aa11525892407b41d379ebf0298413d0c",
    "render-expected.json": "7b45f939d2d771611e9b11633f348e7c1174cb7ea0b3eb36eeb20661dc4192c4",
    "owner-expected.json": "a37dc25f8f756364ae88726cdec3f2de1bbf4c20892ca910d22e9646186efd9d",
}
_POLICY_SHA256 = "7fba44bc1cf2d2dd8b26ed941c28b04371ce29f1875f070f48dc6d12b7efa8d6"
_SESSION_POLICY_SHA256 = "7c2e03125b0b48a914b311d84178894b7487250fe0d4934c7549fca8c777afd4"
_CASE_MANIFEST = Path(__file__).resolve().parents[2] / "cases/earnings/manifest.json"
