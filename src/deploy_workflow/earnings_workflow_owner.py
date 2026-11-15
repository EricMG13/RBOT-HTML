"""CP-1B owner checkpoint runtime: owner submission, bound preparation and intent recovery,
receipt verification, `EarningsWorkflow` and the bounded JSON-lines transport.

Moved unchanged from `earnings_workflow`, which re-exports every name.
"""

from __future__ import annotations

import io
import itertools
import json
import re
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Literal, TextIO, cast
from uuid import uuid4

from pydantic import JsonValue, ValidationError

from deploy_vii.contracts import Module, ModuleView, Run
from deploy_vii.cp0_workflow import submit_cp0_review
from deploy_vii.cp1_workflow import CP1_PROMOTION, PROMOTED
from deploy_vii.execution import (
    Attempt,
    Execution,
    ExecutionSnapshot,
    NotAuthorized,
    StepSubmission,
    StepValidation,
    current_inputs,
)
from deploy_vii.live.submission import submit_model_payload
from deploy_vii.preparation import PreparedPack
from deploy_workflow.earnings import build_earnings_delta_in
from deploy_workflow.earnings_workflow_access import (
    _cp1_candidate,
    _filled,
    _full_cp1,
    _grant,
    _head_record,
    _manifest,
    _owner_session_proof,
    _page,
    _participation,
    _projection,
    _run_currency,
    _safe_fact,
    _source_issues,
)
from deploy_workflow.earnings_workflow_compose import _case_parameters, _compose, _operands
from deploy_workflow.earnings_workflow_contracts import (
    _CASE_MANIFEST,
    _ERRORS,
    _POLICY_SHA256,
    _SCHEMAS,
    _SOURCE_PHASES,
    MAX_ACCESS_READS,
    MAX_AUDIT,
    MAX_FOUNDATION,
    MAX_JSON_DEPTH,
    MAX_LINE,
    MAX_MESSAGES,
    MAX_OWNER_CALLS,
    MAX_OWNER_SESSIONS,
    MAX_RECEIPT,
    AuditEntry,
    BeginRecord,
    BoundSubmission,
    EarningsDeltaReview,
    EarningsOwnerReceipt,
    EarningsOwnerStage,
    EarningsParticipation,
    EarningsReportRecord,
    JsonObject,
    MeasureSelection,
    OutcomeKind,
    OwnerAccessRead,
    OwnerBinding,
    OwnerCaseId,
    OwnerClose,
    OwnerError,
    OwnerSession,
    OwnerSetup,
    OwnerSubmissionEnvelope,
    OwnerToolCall,
    OwnerToolReceipt,
    Phase,
    ReviewOutcome,
    SubmissionIntent,
    SubmissionOutcome,
    Transport,
    TransportMessage,
    WorkflowState,
)
from deploy_workflow.earnings_workflow_store import (
    _binding,
    _canonical,
    _case_pins,
    _FrozenExecution,
    _hash,
    _head,
    _historical,
    _inventory,
    _json_copy,
    _known,
    _parse,
    _payload,
    _put,
    _raw,
    _records,
    _retain,
    _sealed_on_disk,
    _snapshot,
    _stored_bytes,
    _stored_read,
    _text,
    _text_depth,
)
from deploy_workflow.financial_workflow import FinancialBinding, FinancialCall, InputRead
from deploy_workflow.host import SourceSession
from deploy_workflow.tools.upstream import UpstreamTools
from deploy_workflow.workflow import SourceEvidence


def _owner_stage(store: Execution, envelope: OwnerSubmissionEnvelope) -> EarningsOwnerStage:
    historical = _historical(store, envelope.binding)
    snapshot = historical.read()
    _, prior, current = _case_parameters(snapshot.run)
    review = envelope.review
    try:
        raw_review = EarningsDeltaReview.model_validate_json(
            _raw(store, envelope.raw_review_sha256)
        )
    except ValidationError:
        # The one place the actor's own review text is parsed: charged to the actor.
        raise OwnerError("validation_failed") from None
    _, view = _full_cp1(store, envelope.binding)
    build_earnings_delta_in(
        view,
        review.prior_period_id,
        review.current_period_id,
        currency=_run_currency(store.pack(), view),
    )
    if raw_review != review or (review.prior_period_id, review.current_period_id) != (
        prior,
        current,
    ):
        raise OwnerError("validation_failed")
    sessions = _records(store, "owner-sessions", OwnerSession)
    chosen = [s for s in sessions if s.session_id == envelope.participation.session_id]
    if len(chosen) != 1:
        raise OwnerError("identity_mismatch")
    all_calls = tuple(
        sorted(_records(store, "owner-calls", OwnerToolCall), key=lambda c: c.ordinal)
    )
    intents = [
        i
        for i in _records(store, "intents", SubmissionIntent)
        if i.binding.stored_payload_sha256 == envelope.content_hash()
        and i.binding.binding == envelope.binding
        and i.binding.owner_session_id == envelope.participation.session_id
        and i.binding.participation_sha256 == envelope.participation.content_hash()
    ]
    if len(intents) != 1:
        raise OwnerError("identity_mismatch")
    bound = intents[0].binding
    if (
        envelope.participation.call_ids != bound.call_ids
        or envelope.participation.successful_call_ids != bound.successful_call_ids
    ):
        raise OwnerError("identity_mismatch")
    reads_by_hash = {r.content_hash(): r for r in _records(store, "owner-reads", OwnerAccessRead)}
    captured_reads = tuple(reads_by_hash[digest] for digest in bound.input_read_hashes)
    ticket_calls = tuple(
        c for c in all_calls if c.receipt.binding.ticket_id == envelope.binding.ticket_id
    )
    prefix = ticket_calls[: len(envelope.participation.call_ids)]
    actual = _participation(
        store,
        envelope.binding,
        chosen[0],
        captured_reads,
        prefix,
        prior,
        current,
    )
    if actual != envelope.participation:
        raise OwnerError("participation_incomplete")
    _, report, producer = _grant(store, envelope.binding, prior, current)
    selections = tuple(
        MeasureSelection(
            measure_id=p.measure_id,
            prior_fact_id=p.prior_fact_id,
            current_fact_id=p.current_fact_id,
            companion_fact_ids=p.companion_fact_ids,
        )
        for p in report.points
    )
    if review.selections != selections or review.comparison_assessment != (
        "comparative_not_supplied" if report.prior_basis_id is None else "flat_sequential"
    ):
        raise OwnerError("validation_failed")
    operands = _operands(producer, report)
    attempt = next(a for a in snapshot.attempts if a.ticket_id == envelope.binding.ticket_id)
    candidate = _compose(producer, report, operands, review, actual, attempt, snapshot.run)
    return EarningsOwnerStage(
        review_sha256=review.content_hash(),
        participation_sha256=actual.content_hash(),
        report=EarningsReportRecord.model_validate(asdict(report)),
        operands=operands,
        candidate=candidate,
    )


def _stage_validation(store: Execution, envelope: OwnerSubmissionEnvelope) -> StepValidation:
    try:
        stage = _owner_stage(store, envelope)
    except OwnerError as error:
        return StepValidation(issues=(error.code,))
    except ValueError as error:
        # A pydantic ValidationError is a ValueError outside this set, so B1's own
        # composition defects propagate; only the actor review parse is charged.
        if str(error) not in {
            "incompatible_periods",
            "incomplete_register",
            "invalid_source_view",
            "incompatible_dimensions",
            "ambiguous_coordinate",
            "invalid_fact",
        }:
            raise
        return StepValidation(issues=(str(error),))
    return StepValidation(output=stage.model_dump_json())


def submit_earnings_delta(store: Execution, ticket_id: str, payload: str) -> Attempt:
    """Submit the host's durable envelope and settle only its rederived candidate."""
    envelope = OwnerSubmissionEnvelope.model_validate_json(payload)
    setup, _ = _setup(store, _CASE_MANIFEST)
    _verify_open_history(store, setup)
    attempts = [a for a in store.read().attempts if a.ticket_id == ticket_id]
    if len(attempts) != 1 or attempts[0].module_id != "CP-1B" or attempts[0].status != "pending":
        raise OwnerError("stale_binding")
    attempt = attempts[0]
    if envelope.binding.ticket_id != ticket_id:
        raise OwnerError("identity_mismatch")
    if _raw(store, _hash(payload.encode())) != payload.encode():
        raise OwnerError("identity_mismatch")
    intents = _records(store, "intents", SubmissionIntent)
    if not any(
        i.binding.binding == envelope.binding
        and i.binding.stored_payload_sha256 == _hash(payload.encode())
        and i.binding.raw_payload_sha256 == envelope.raw_review_sha256
        and i.binding.participation_sha256 == envelope.participation.content_hash()
        for i in intents
    ):
        raise OwnerError("identity_mismatch")
    if attempt.steps and attempt.steps[0].payload_sha256 != _hash(payload.encode()):
        raise OwnerError("identity_mismatch")
    if attempt.steps and attempt.steps[0].status == "valid":
        output_hash = attempt.steps[0].output_sha256
        if output_hash is None:
            raise OwnerError("identity_mismatch")
        with _stored_read():
            retained = store.step_output(output_hash).encode()
        if _stored_bytes(store, "stages", output_hash) != retained:
            raise OwnerError("identity_mismatch")

    def validation(_pack: PreparedPack, _attempt: Attempt) -> StepValidation:
        result = _stage_validation(store, envelope)
        if not result.issues:
            _retain(store, "stages", EarningsOwnerStage.model_validate_json(result.output or ""))
        return result

    if not attempt.steps or attempt.steps[0].status == "pending":
        attempt = store.submit_step(
            ticket_id, "CP-1B", ("earnings_delta",), "earnings_delta", payload, validation
        )
    if attempt.status == "finished":
        return attempt
    with _stored_read():
        pack = store.pack()
    outcome = validation(pack, attempt)
    if outcome.issues or not outcome.retained_as(attempt.steps[0]):
        raise OwnerError("identity_mismatch")
    stage = EarningsOwnerStage.model_validate_json(outcome.output or "")
    _payload(store, stage.candidate.model_dump_json().encode())
    return store.finish(
        ticket_id,
        stage.candidate.model_dump_json(),
        lambda supplied: () if supplied == stage.candidate else ("validation_failed",),
    )


def _foundation_calls(store: Execution, binding: FinancialBinding) -> tuple[FinancialCall, ...]:
    return tuple(
        sorted(
            (c for c in _records(store, "foundation-calls", FinancialCall) if c.binding == binding),
            key=lambda c: c.sequence,
        )
    )


def _source_session(store: Execution, binding: FinancialBinding) -> SourceSession:
    historical = _historical(store, binding)
    session = SourceSession.from_execution(historical, binding.ticket_id, binding.step_id)
    for sequence, call in enumerate(_foundation_calls(store, binding), 1):
        if call.sequence != sequence:
            raise OwnerError("identity_mismatch")
        replay = session.invoke(call.tool, call.arguments)
        replay["call_id"] = call.call_id
        if _parse(FinancialCall, replay) != call:
            raise OwnerError("identity_mismatch")
    return session


def _prepare_bound(
    store: Execution,
    binding: FinancialBinding | OwnerBinding,
    payload: str,
    session: OwnerSession | None = None,
) -> tuple[BoundSubmission, tuple[str, ...]]:
    if isinstance(binding, OwnerBinding):
        if session is None:
            raise OwnerError("not_permitted")
        actual = [
            s
            for s in _records(store, "owner-sessions", OwnerSession)
            if s.session_id == session.session_id
        ]
        if len(actual) != 1 or actual[0] != session or session.binding != binding:
            raise OwnerError("identity_mismatch")
        _, prior, current = _case_parameters(_historical(store, binding).read().run)
        _owner_session_proof(store, session, (), prior, current)
    raw_hash = _payload(store, payload.encode())
    if isinstance(binding, FinancialBinding):
        historical = _historical(store, binding)
        calls = _foundation_calls(store, binding)
        evidence = calls[-1].source_evidence if calls else SourceEvidence()
        if binding.step_id in _SOURCE_PHASES:
            attached = _source_session(store, binding).bind_submission(payload)
            generated_ids = attached.get("call_ids")
            if (
                not isinstance(generated_ids, list)
                or len(generated_ids) != len(calls)
                or len(set(generated_ids)) != len(generated_ids)
                or attached.get("successful_call_ids")
                != [generated_ids[index] for index, call in enumerate(calls) if call.status == "ok"]
            ):
                raise OwnerError("identity_mismatch")
            # Public replay generates new UUIDs. Only these UUID positions may
            # be replaced; every argument/body/status/evidence field was checked.
            attached = {
                **attached,
                "call_ids": [c.call_id for c in calls],
                "successful_call_ids": [c.call_id for c in calls if c.status == "ok"],
            }
            expected = {
                "schema_version": "submission-binding/1",
                "binding": binding.model_dump(mode="json"),
                "payload_sha256": raw_hash,
                "successful_call_ids": [c.call_id for c in calls if c.status == "ok"],
                "call_ids": [c.call_id for c in calls],
                "source_evidence": evidence.model_dump(mode="json"),
            }
            if attached != expected:
                raise OwnerError("identity_mismatch")
        filled, normalized, paths, kinds = _filled(historical, binding, payload)
        stored_hash = _payload(store, filled.encode())
        issues = _source_issues(historical, binding, filled, evidence, calls)
        reads = tuple(
            sorted(
                (r for r in _records(store, "foundation-reads", InputRead) if r.binding == binding),
                key=lambda r: r.sequence,
            )
        )
        if binding.step_id not in _SOURCE_PHASES and not reads:
            issues = (*issues, "participation_incomplete")
        for sequence, read in enumerate(reads, 1):
            if read.sequence != sequence or (read.inputs_sha256, read.body) != _projection(
                store, binding
            ):
                raise OwnerError("identity_mismatch")
        try:
            canonical = _SCHEMAS[binding.step_id].model_validate_json(filled).content_hash()
        except ValidationError:
            canonical = None
        return BoundSubmission(
            binding=binding,
            raw_payload_sha256=raw_hash,
            stored_payload_sha256=stored_hash,
            canonical_review_sha256=canonical,
            call_ids=tuple(c.call_id for c in calls),
            successful_call_ids=tuple(c.call_id for c in calls if c.status == "ok"),
            source_evidence=evidence,
            input_read_hashes=tuple(r.content_hash() for r in reads),
            participation_sha256=None,
            owner_session_id=None,
            normalization_paths=normalized,
            prefilled_paths=paths,
            prefilled_kinds=kinds,
        ), issues
    owner_calls = tuple(
        sorted(
            (
                c
                for c in _records(store, "owner-calls", OwnerToolCall)
                if c.receipt.binding.ticket_id == binding.ticket_id
            ),
            key=lambda c: c.ordinal,
        )
    )
    session_order = {
        s.session_id: s.index
        for s in _records(store, "owner-sessions", OwnerSession)
        if s.binding.ticket_id == binding.ticket_id
    }
    owner_reads = tuple(
        sorted(
            (
                r
                for r in _records(store, "owner-reads", OwnerAccessRead)
                if r.binding.ticket_id == binding.ticket_id
            ),
            key=lambda r: (_known(session_order, r.session_id), r.sequence),
        )
    )
    try:
        review = EarningsDeltaReview.model_validate_json(payload)
    except ValidationError:
        review = None
    participation = None
    issues = () if review is not None else ("bad_arguments",)
    if review is not None:
        _, prior, current = _case_parameters(_historical(store, binding).read().run)
        if session is None:
            issues = ("participation_incomplete",)
        else:
            try:
                participation = _participation(
                    store, binding, session, owner_reads, owner_calls, prior, current
                )
            except OwnerError as error:
                if error.code not in {
                    "participation_incomplete",
                    "identity_mismatch",
                    "stale_binding",
                }:
                    raise
                issues = (error.code,)
    if participation is not None and review is not None:
        _retain(store, "participations", participation)
        envelope = OwnerSubmissionEnvelope(
            binding=binding, raw_review_sha256=raw_hash, review=review, participation=participation
        )
        stored_hash = _payload(store, envelope.model_dump_json().encode())
    else:
        stored_hash = raw_hash
    return BoundSubmission(
        binding=binding,
        raw_payload_sha256=raw_hash,
        stored_payload_sha256=stored_hash,
        canonical_review_sha256=review.content_hash() if review is not None else None,
        call_ids=tuple(c.receipt.call_id for c in owner_calls),
        successful_call_ids=tuple(
            c.receipt.call_id for c in owner_calls if c.receipt.status == "ok"
        ),
        source_evidence=SourceEvidence(),
        input_read_hashes=tuple(r.content_hash() for r in owner_reads),
        participation_sha256=participation.content_hash() if participation else None,
        owner_session_id=session.session_id if session is not None else None,
        normalization_paths=(),
        prefilled_paths=(),
        prefilled_kinds=(),
    ), issues


def _intent_session(store: Execution, intent: SubmissionIntent) -> OwnerSession | None:
    if not isinstance(intent.binding.binding, OwnerBinding):
        return None
    sessions = [
        s
        for s in _records(store, "owner-sessions", OwnerSession)
        if s.session_id == intent.binding.owner_session_id
    ]
    if len(sessions) != 1 or sessions[0].binding != intent.binding.binding:
        raise OwnerError("identity_mismatch")
    if intent.binding.participation_sha256 is not None:
        parts = [
            p
            for p in _records(store, "participations", EarningsParticipation)
            if p.content_hash() == intent.binding.participation_sha256
        ]
        if len(parts) != 1:
            raise OwnerError("identity_mismatch")
        if parts[0].session_id != intent.binding.owner_session_id:
            raise OwnerError("identity_mismatch")
    _, prior, current = _case_parameters(_historical(store, sessions[0].binding).read().run)
    _owner_session_proof(store, sessions[0], (), prior, current)
    return sessions[0]


def _unresolved(store: Execution) -> tuple[SubmissionIntent, ...]:
    outcomes = _records(store, "outcomes", SubmissionOutcome)
    by_intent = [o.intent_sha256 for o in outcomes]
    if len(set(by_intent)) != len(by_intent):
        raise OwnerError("identity_mismatch")
    intents = tuple(sorted(_records(store, "intents", SubmissionIntent), key=lambda i: i.index))
    if [i.index for i in intents] != list(range(1, len(intents) + 1)) or not set(by_intent) <= {
        i.content_hash() for i in intents
    }:
        raise OwnerError("identity_mismatch")
    pending = tuple(i for i in intents if i.content_hash() not in by_intent)
    if len(pending) > 1 or pending and pending[0] != intents[-1]:
        raise OwnerError("identity_mismatch")
    return pending


def _new_steps(before: ExecutionSnapshot, attempt: Attempt) -> list[StepSubmission]:
    """Steps of `attempt` that `before` does not already account for.

    Steps present in the before-snapshot belong to earlier intents. Subtracting
    them as a multiset keeps an identical resubmission a distinct journal step,
    so it is credited to the intent that produced it and to no other.
    """
    remaining = Counter(
        s.content_hash()
        for a in before.attempts
        if a.ticket_id == attempt.ticket_id
        for s in (*a.steps, *a.step_repairs)
    )
    result = []
    for step in (*attempt.steps, *attempt.step_repairs):
        digest = step.content_hash()
        if remaining[digest] > 0:
            remaining[digest] -= 1
        else:
            result.append(step)
    return result


def _complete_intent(store: Execution, intent: SubmissionIntent) -> SubmissionOutcome:
    bound = intent.binding
    payload = _text(store, bound.raw_payload_sha256)
    rebound, issues = _prepare_bound(store, bound.binding, payload, _intent_session(store, intent))
    if rebound != bound or intent.snapshot_before_sha256 != bound.binding.snapshot_sha256:
        raise OwnerError("identity_mismatch")
    before = _snapshot(store, intent.snapshot_before_sha256)
    current = store.read()
    attempt = next((a for a in current.attempts if a.ticket_id == bound.binding.ticket_id), None)
    if attempt is None:
        raise OwnerError("identity_mismatch")

    def produced(candidate_attempt: Attempt) -> list[StepSubmission]:
        return [
            s
            for s in _new_steps(before, candidate_attempt)
            if s.step_id == bound.binding.step_id
            and s.payload_sha256 == bound.stored_payload_sha256
        ]

    matching = produced(attempt)
    if issues:
        if matching or current.content_hash() != before.content_hash():
            raise OwnerError("identity_mismatch")
        outcome = SubmissionOutcome(
            intent_sha256=intent.content_hash(),
            disposition="refused",
            issues=issues,
            snapshot_after_sha256=current.content_hash(),
            step_sha256=None,
            step_output_sha256=None,
            candidate_sha256=None,
            result_sha256=None,
        )
        _retain(store, "outcomes", outcome)
        return outcome
    terminal_step = bound.binding.step_id in {"source_readiness", "quality", "earnings_delta"}
    needs_submit = (
        not matching
        or matching[-1].status == "pending"
        or terminal_step
        and attempt.status == "pending"
    )
    if needs_submit:
        if attempt.status != "pending":
            raise OwnerError("identity_mismatch")
        if isinstance(bound.binding, OwnerBinding):
            attempt = submit_earnings_delta(
                store, bound.binding.ticket_id, _text(store, bound.stored_payload_sha256)
            )
        elif bound.binding.step_id == "source_readiness":
            attempt = submit_cp0_review(
                store, bound.binding.ticket_id, _text(store, bound.stored_payload_sha256)
            )
        else:
            submitted = submit_model_payload(
                store, bound.binding.ticket_id, bound.binding.step_id, payload
            )
            if (
                submitted.payload,
                submitted.nulls_resolved,
                submitted.prefilled,
                submitted.prefilled_kinds,
            ) != (
                _text(store, bound.stored_payload_sha256),
                bound.normalization_paths,
                bound.prefilled_paths,
                bound.prefilled_kinds,
            ):
                raise OwnerError("identity_mismatch")
            attempt = submitted.journal
        current = store.read()
        matching = produced(attempt)
    if len(matching) != 1 or matching[0].status == "pending":
        raise OwnerError("identity_mismatch")
    step = matching[0]
    if attempt.payload_sha256 is not None:
        with _stored_read():
            candidate_text = store.payload(attempt.payload_sha256)
        _payload(store, candidate_text.encode())
    outcome = SubmissionOutcome(
        intent_sha256=intent.content_hash(),
        disposition="valid" if step.status == "valid" and not attempt.issues else "invalid",
        issues=step.issues or attempt.issues,
        snapshot_after_sha256=current.content_hash(),
        step_sha256=step.content_hash(),
        step_output_sha256=step.output_sha256,
        candidate_sha256=attempt.payload_sha256,
        result_sha256=attempt.result_sha256,
    )
    _retain(store, "outcomes", outcome)
    return outcome


def _preflight(producer: Module, prior: str, current: str, pack: PreparedPack) -> None:
    view = ModuleView(
        module_id="CP-1",
        title="Financials",
        aliases=(),
        status=producer.status,
        artifact_sha256=producer.content_hash(),
        facts=producer.facts,
        tables=producer.tables,
        claims=producer.claims,
        limitations=producer.limitations,
    )
    report = build_earnings_delta_in(view, prior, current, currency=_run_currency(pack, view))
    bases = {report.current_basis_id}
    if report.prior_basis_id is not None:
        bases.add(report.prior_basis_id)
    rows = {
        f.row_id for f in producer.facts if f.fact_id in {p.current_fact_id for p in report.points}
    }
    chosen = tuple(
        f
        for f in producer.facts
        if f.table_id == "T4.14"
        or f.table_id == "T4.10"
        and f.row_id in rows
        and f.field in {*bases, "field_0", "field_1"}
    )
    # Fixed-width digest/cursor sentinels are exclusively a byte-size calculation,
    # never a grant, bound producer, recorded tool call or settlement authority.
    header = {
        "producer": {
            "module_id": "CP-1",
            "sha256": producer.content_hash(),
            "status": producer.status,
        },
        "grant_sha256": "0" * 64,
        "manifest_sha256": "0" * 64,
    }
    if len(chosen) * 3 > MAX_OWNER_CALLS:
        raise OwnerError("transport_limit")
    entries = [_safe_fact(f) for f in chosen]
    for offset in range(len(entries)):
        token = None if offset + 1 == len(entries) else "projection-cursor:" + "0" * 64
        if len(_canonical(_page(header, entries, offset, 1, token, True)).encode()) > 8192:
            raise OwnerError("transport_limit")


class _WriteProposal(BaseException):
    def __init__(self, snapshot: ExecutionSnapshot) -> None:
        self.snapshot = snapshot


class _MutationProbe(_FrozenExecution):
    """Re-enter public core APIs but forbid every actual write and lock mutation."""

    @contextmanager
    def _locked(self) -> Iterator[None]:
        yield

    def _store(self, text: str) -> str:
        raw = text.encode()
        digest = _hash(raw)
        if self._load(digest) != raw:
            raise OwnerError("identity_mismatch")
        return digest

    def _write(self, snapshot: ExecutionSnapshot) -> None:
        raise _WriteProposal(snapshot)


def _propose_owner(probe: _MutationProbe, bound: BoundSubmission) -> None:
    envelope = OwnerSubmissionEnvelope.model_validate_json(_raw(probe, bound.stored_payload_sha256))
    attempt = next(a for a in probe.read().attempts if a.ticket_id == bound.binding.ticket_id)

    def validate(_pack: PreparedPack, _attempt: Attempt) -> StepValidation:
        return _stage_validation(probe, envelope)

    if not attempt.steps or attempt.steps[0].status == "pending":
        attempt = probe.submit_step(
            attempt.ticket_id,
            "CP-1B",
            ("earnings_delta",),
            "earnings_delta",
            _text(probe, bound.stored_payload_sha256),
            validate,
        )
    if attempt.status == "finished":
        return
    outcome = validate(probe.pack(), attempt)
    if outcome.issues or not outcome.retained_as(attempt.steps[0]):
        raise OwnerError("identity_mismatch")
    candidate = EarningsOwnerStage.model_validate_json(outcome.output or "").candidate
    probe.finish(
        attempt.ticket_id,
        candidate.model_dump_json(),
        lambda supplied: () if supplied == candidate else ("validation_failed",),
    )


def _propose_submission(
    store: Execution, before: ExecutionSnapshot, bound: BoundSubmission
) -> ExecutionSnapshot:
    attempt = next((a for a in before.attempts if a.ticket_id == bound.binding.ticket_id), None)
    if attempt is None or attempt.status != "pending":
        # The intent was bound to a pending attempt, and its outcome is written before
        # any later begin; a finished or absent ticket here means a lost outcome record.
        raise OwnerError("identity_mismatch")
    probe = _MutationProbe(store, before)
    try:
        if isinstance(bound.binding, OwnerBinding):
            _propose_owner(probe, bound)
        elif bound.binding.step_id == "source_readiness":
            submit_cp0_review(
                probe, bound.binding.ticket_id, _text(store, bound.stored_payload_sha256)
            )
        else:
            submit_model_payload(
                probe,
                bound.binding.ticket_id,
                bound.binding.step_id,
                _text(store, bound.raw_payload_sha256),
            )
    except _WriteProposal as proposal:
        return proposal.snapshot
    raise OwnerError("identity_mismatch")


def _chain(store: Execution, anchor: str) -> tuple[ExecutionSnapshot, ...]:
    chain: list[ExecutionSnapshot] = []
    seen = set()
    digest: str | None = anchor
    while digest is not None:
        if digest in seen or len(chain) >= MAX_AUDIT:
            raise OwnerError("identity_mismatch")
        seen.add(digest)
        snapshot = _snapshot(store, digest)
        chain.append(snapshot)
        digest = snapshot.parent
    chain.reverse()
    if any(s.run != chain[0].run or s.pack_sha256 != chain[0].pack_sha256 for s in chain):
        raise OwnerError("identity_mismatch")
    return tuple(chain)


def _verify_begin(store: Execution, record: BeginRecord) -> None:
    before = _snapshot(store, record.snapshot_before_sha256)
    if any(a.status == "pending" for a in before.attempts):
        # `_begin` only ever runs with no pending attempt (the core refuses otherwise
        # and nothing is recorded), so a begin recorded from such a snapshot is forged.
        raise OwnerError("identity_mismatch")
    if record.error_code is not None:
        if (
            record.error_code != "not_authorized"
            or record.module_id != "CP-1"
            or record.ticket_id is not None
            or record.attempt is not None
        ):
            raise OwnerError("identity_mismatch")
        try:
            current_inputs(before, record.module_id)
        except NotAuthorized:
            if record.snapshot_after_sha256 == record.snapshot_before_sha256:
                return
        except ValueError as error:
            # The core refuses with a ValueError (execution.py:210-213); a refusal other
            # than NotAuthorized contradicts the recorded `not_authorized` begin.
            raise OwnerError("identity_mismatch") from error
        raise OwnerError("identity_mismatch")
    try:
        _MutationProbe(store, before).begin(record.module_id)
    except _WriteProposal as proposal:
        after = _snapshot(store, record.snapshot_after_sha256)
        generated = proposal.snapshot
        expected = generated.attempts[-1].model_copy(update={"ticket_id": record.ticket_id})
        generated = generated.model_copy(update={"attempts": (*generated.attempts[:-1], expected)})
        if (
            generated != after
            or record.ticket_id != after.attempts[-1].ticket_id
            or record.attempt != after.attempts[-1].number
        ):
            raise OwnerError("identity_mismatch")
        return
    except OwnerError:
        raise
    except ValueError as error:
        # The one replay of the recorded begin. The core refuses a begin with a
        # ValueError (execution.py:210-213: "a ValueError like every other refusal");
        # a successful begin the core refuses from `before` was never made and is forged.
        raise OwnerError("identity_mismatch") from error
    raise OwnerError("identity_mismatch")


def _verify_outcome(
    store: Execution,
    intent: SubmissionIntent,
    outcome: SubmissionOutcome,
    chain: tuple[ExecutionSnapshot, ...],
) -> set[tuple[str, str]]:
    bound = intent.binding
    rebound, issues = _prepare_bound_readonly(store, intent)
    if rebound != bound:
        raise OwnerError("identity_mismatch")
    by_hash = {s.content_hash(): index for index, s in enumerate(chain)}
    if (
        intent.snapshot_before_sha256 not in by_hash
        or outcome.snapshot_after_sha256 not in by_hash
        or intent.snapshot_before_sha256 != bound.binding.snapshot_sha256
    ):
        raise OwnerError("identity_mismatch")
    start, stop = by_hash[intent.snapshot_before_sha256], by_hash[outcome.snapshot_after_sha256]
    if stop < start:
        raise OwnerError("identity_mismatch")
    if issues:
        if outcome != SubmissionOutcome(
            intent_sha256=intent.content_hash(),
            disposition="refused",
            issues=issues,
            snapshot_after_sha256=intent.snapshot_before_sha256,
            step_sha256=None,
            step_output_sha256=None,
            candidate_sha256=None,
            result_sha256=None,
        ):
            raise OwnerError("identity_mismatch")
        return set()
    if outcome.disposition == "refused" or stop == start:
        raise OwnerError("identity_mismatch")
    edges = set()
    for before, after in zip(chain[start:stop], chain[start + 1 : stop + 1], strict=True):
        if _propose_submission(store, before, bound) != after:
            raise OwnerError("identity_mismatch")
        edges.add((before.content_hash(), after.content_hash()))
    after = chain[stop]
    attempt = next(a for a in after.attempts if a.ticket_id == bound.binding.ticket_id)
    steps = [
        s for s in _new_steps(chain[start], attempt) if s.content_hash() == outcome.step_sha256
    ]
    if len(steps) != 1:
        raise OwnerError("identity_mismatch")
    step = steps[0]
    expected = SubmissionOutcome(
        intent_sha256=intent.content_hash(),
        disposition="valid" if step.status == "valid" and not attempt.issues else "invalid",
        issues=step.issues or attempt.issues,
        snapshot_after_sha256=after.content_hash(),
        step_sha256=step.content_hash(),
        step_output_sha256=step.output_sha256,
        candidate_sha256=attempt.payload_sha256,
        result_sha256=attempt.result_sha256,
    )
    if outcome != expected:
        raise OwnerError("identity_mismatch")
    return edges


def _prepare_bound_readonly(
    store: Execution, intent: SubmissionIntent
) -> tuple[BoundSubmission, tuple[str, ...]]:
    """Recompute bound evidence while denying even idempotent audit writes."""
    bound = intent.binding
    raw = _raw(store, bound.raw_payload_sha256)
    binding = bound.binding
    if isinstance(binding, FinancialBinding):
        calls = _foundation_calls(store, binding)
        prefix = calls[: len(bound.call_ids)]
        if tuple(c.call_id for c in prefix) != bound.call_ids:
            raise OwnerError("identity_mismatch")
        evidence = prefix[-1].source_evidence if prefix else SourceEvidence()
        if binding.step_id in _SOURCE_PHASES:
            _source_session(store, binding)
        filled, normalized, paths, kinds = _filled(
            _historical(store, binding), binding, _text(store, bound.raw_payload_sha256)
        )
        if _raw(store, bound.stored_payload_sha256) != filled.encode():
            raise OwnerError("identity_mismatch")
        reads_by_hash = {
            r.content_hash(): r for r in _records(store, "foundation-reads", InputRead)
        }
        reads = tuple(_known(reads_by_hash, digest) for digest in bound.input_read_hashes)
        for read in reads:
            if read.binding != binding or (read.inputs_sha256, read.body) != _projection(
                store, binding
            ):
                raise OwnerError("identity_mismatch")
        issues = _source_issues(_historical(store, binding), binding, filled, evidence, prefix)
        if binding.step_id not in _SOURCE_PHASES and not reads:
            issues = (*issues, "participation_incomplete")
        try:
            canonical = _SCHEMAS[binding.step_id].model_validate_json(filled).content_hash()
        except ValidationError:
            canonical = None
        rebuilt = BoundSubmission(
            binding=binding,
            raw_payload_sha256=bound.raw_payload_sha256,
            stored_payload_sha256=_hash(filled.encode()),
            canonical_review_sha256=canonical,
            call_ids=tuple(c.call_id for c in prefix),
            successful_call_ids=tuple(c.call_id for c in prefix if c.status == "ok"),
            source_evidence=evidence,
            input_read_hashes=bound.input_read_hashes,
            participation_sha256=None,
            owner_session_id=None,
            normalization_paths=normalized,
            prefilled_paths=paths,
            prefilled_kinds=kinds,
        )
        return rebuilt, issues
    owner_calls = tuple(
        sorted(
            (
                c
                for c in _records(store, "owner-calls", OwnerToolCall)
                if c.receipt.binding.ticket_id == binding.ticket_id
            ),
            key=lambda c: c.ordinal,
        )
    )[: len(bound.call_ids)]
    if tuple(c.receipt.call_id for c in owner_calls) != bound.call_ids:
        raise OwnerError("identity_mismatch")
    session = _intent_session(store, intent)
    owner_session_order = {
        s.session_id: s.index
        for s in _records(store, "owner-sessions", OwnerSession)
        if s.binding.ticket_id == binding.ticket_id
    }
    all_owner_reads = tuple(
        sorted(
            (
                r
                for r in _records(store, "owner-reads", OwnerAccessRead)
                if r.binding.ticket_id == binding.ticket_id
            ),
            key=lambda r: (_known(owner_session_order, r.session_id), r.sequence),
        )
    )
    if (
        tuple(r.content_hash() for r in all_owner_reads[: len(bound.input_read_hashes)])
        != bound.input_read_hashes
    ):
        raise OwnerError("identity_mismatch")
    try:
        review = EarningsDeltaReview.model_validate_json(raw)
    except ValidationError:
        review = None
    participation = None
    issues = () if review is not None else ("bad_arguments",)
    if review is not None:
        _, prior, current = _case_parameters(_historical(store, binding).read().run)
        try:
            if session is None:
                raise OwnerError("participation_incomplete")
            owner_reads_by_hash = {
                r.content_hash(): r for r in _records(store, "owner-reads", OwnerAccessRead)
            }
            owner_reads = tuple(owner_reads_by_hash[digest] for digest in bound.input_read_hashes)
            participation = _participation(
                store, binding, session, owner_reads, owner_calls, prior, current
            )
        except OwnerError as error:
            if error.code not in {"participation_incomplete", "identity_mismatch", "stale_binding"}:
                raise
            issues = (error.code,)
    stored = raw
    if participation is not None and review is not None:
        stored = (
            OwnerSubmissionEnvelope(
                binding=binding,
                raw_review_sha256=bound.raw_payload_sha256,
                review=review,
                participation=participation,
            )
            .model_dump_json()
            .encode()
        )
    if _raw(store, bound.stored_payload_sha256) != stored:
        raise OwnerError("identity_mismatch")
    rebuilt = BoundSubmission(
        binding=binding,
        raw_payload_sha256=bound.raw_payload_sha256,
        stored_payload_sha256=_hash(stored),
        canonical_review_sha256=review.content_hash() if review is not None else None,
        call_ids=tuple(c.receipt.call_id for c in owner_calls),
        successful_call_ids=tuple(
            c.receipt.call_id for c in owner_calls if c.receipt.status == "ok"
        ),
        source_evidence=SourceEvidence(),
        input_read_hashes=bound.input_read_hashes,
        participation_sha256=participation.content_hash() if participation else None,
        owner_session_id=bound.owner_session_id,
        normalization_paths=(),
        prefilled_paths=(),
        prefilled_kinds=(),
    )
    return rebuilt, issues


def _verify_cp5_descendants(store: Execution, anchor: ExecutionSnapshot) -> None:
    from deploy_vii.cp5_integrity import submit_cp5_step

    chain = _chain(store, store.read().content_hash())
    positions = [i for i, s in enumerate(chain) if s == anchor]
    if len(positions) != 1:
        raise OwnerError("identity_mismatch")
    for before, after in zip(chain[positions[0] : -1], chain[positions[0] + 1 :], strict=True):
        if (
            tuple(a for a in after.attempts if a.module_id != "CP-5") != anchor.attempts
            or tuple(h for h in after.heads if h.module_id != "CP-5") != anchor.heads
            or after.run != anchor.run
            or after.pack_sha256 != anchor.pack_sha256
        ):
            raise OwnerError("identity_mismatch")
        probe = _MutationProbe(store, before)
        try:
            if len(after.attempts) == len(before.attempts) + 1:
                if after.attempts[-1].module_id != "CP-5":
                    raise OwnerError("identity_mismatch")
                probe.begin("CP-5")
            else:
                changed = [
                    a for a, b in zip(after.attempts, before.attempts, strict=True) if a != b
                ]
                if len(changed) != 1 or changed[0].module_id != "CP-5" or not changed[0].steps:
                    raise OwnerError("identity_mismatch")
                attempt = changed[0]
                submit_cp5_step(
                    probe,
                    attempt.ticket_id,
                    "integrity_review",
                    probe.payload(attempt.steps[0].payload_sha256),
                )
        except _WriteProposal as proposal:
            expected = proposal.snapshot
            if len(after.attempts) == len(before.attempts) + 1:
                replacement = expected.attempts[-1].model_copy(
                    update={"ticket_id": after.attempts[-1].ticket_id}
                )
                expected = expected.model_copy(
                    update={"attempts": (*expected.attempts[:-1], replacement)}
                )
            if expected != after:
                raise OwnerError("identity_mismatch")
        else:
            raise OwnerError("identity_mismatch")


def _policy(case_manifest: Path) -> str:
    if _hash((case_manifest.parent / "transport-expected.json").read_bytes()) != _POLICY_SHA256:
        raise OwnerError("identity_mismatch")
    return _POLICY_SHA256


def _setup(store: Execution, case_manifest: Path) -> tuple[OwnerSetup, dict[str, Any]]:
    records = _records(store, "setup", OwnerSetup)
    if len(records) != 1:
        raise OwnerError("identity_mismatch")
    setup = records[0]
    current = store.read()
    chain = _chain(store, current.content_hash())
    first = chain[0]
    if (
        first.content_hash() != setup.initial_snapshot_sha256
        or first.parent is not None
        or first.attempts
        or first.heads
        or first.run != setup.run
        or first.pack_sha256 != setup.pack_sha256
        or first != ExecutionSnapshot(run=setup.run, pack_sha256=setup.pack_sha256)
        or setup.policy_sha256 != _policy(case_manifest)
    ):
        raise OwnerError("identity_mismatch")
    case, pins = _case_pins(case_manifest, setup.case_id, store.pack(first))
    if pins != setup.pins:
        raise OwnerError("identity_mismatch")
    return setup, case


def _transcript_fields(store: Execution) -> dict[str, Any]:
    positions = {
        s.content_hash(): index
        for index, s in enumerate(_chain(store, _head(store).content_hash()))
    }
    sessions = tuple(
        sorted(
            _records(store, "owner-sessions", OwnerSession),
            key=lambda s: (_known(positions, s.binding.snapshot_sha256), s.index),
        )
    )
    session_order = {s.session_id: index for index, s in enumerate(sessions)}
    intents = tuple(sorted(_records(store, "intents", SubmissionIntent), key=lambda i: i.index))
    intent_order = {i.content_hash(): i.index for i in intents}
    return {
        "transport_messages": tuple(
            sorted(_records(store, "transport-messages", TransportMessage), key=lambda m: m.index)
        ),
        "begins": tuple(sorted(_records(store, "begins", BeginRecord), key=lambda b: b.index)),
        "foundation_calls": tuple(
            sorted(
                _records(store, "foundation-calls", FinancialCall),
                key=lambda c: (_known(positions, c.binding.snapshot_sha256), c.sequence),
            )
        ),
        "foundation_input_reads": tuple(
            sorted(
                _records(store, "foundation-reads", InputRead),
                key=lambda r: (_known(positions, r.binding.snapshot_sha256), r.sequence),
            )
        ),
        "owner_sessions": sessions,
        "owner_access_reads": tuple(
            sorted(
                _records(store, "owner-reads", OwnerAccessRead),
                key=lambda r: (_known(session_order, r.session_id), r.sequence),
            )
        ),
        "owner_calls": tuple(
            sorted(_records(store, "owner-calls", OwnerToolCall), key=lambda c: c.ordinal)
        ),
        "submission_intents": intents,
        "submission_outcomes": tuple(
            sorted(
                _records(store, "outcomes", SubmissionOutcome),
                key=lambda o: _known(intent_order, o.intent_sha256),
            )
        ),
    }


def _verify_begins(store: Execution, begins: tuple[BeginRecord, ...]) -> set[tuple[str, str]]:
    """Authenticate every begin record; return the chain edges the successful ones cover.

    Indices are contiguous from 1; each successful begin covers a distinct edge; a
    refusal ends the run (complete or failed, no further begin), so at most one begin
    is a refusal and it is the last.
    """
    if [b.index for b in begins] != list(range(1, len(begins) + 1)):
        raise OwnerError("identity_mismatch")
    refusals = [b.index for b in begins if b.error_code is not None]
    if len(refusals) > 1 or (refusals and refusals[0] != len(begins)):
        raise OwnerError("identity_mismatch")
    covered: set[tuple[str, str]] = set()
    for begin in begins:
        _verify_begin(store, begin)
        if begin.error_code is None:
            edge = (begin.snapshot_before_sha256, begin.snapshot_after_sha256)
            if edge in covered:
                raise OwnerError("identity_mismatch")
            covered.add(edge)
    return covered


def _verify_open_history(
    store: Execution, setup: OwnerSetup, recovered: BeginRecord | None = None
) -> None:
    """Authenticate the stored history, plus the begin record `_bootstrap_log` recovered.

    `recovered` is held in memory only: it is authenticated here together with the
    stored begins (`_verify_begins`) and every later check, and the caller retains it
    only after this returns. The caller has re-read the head under the lock first, so
    a concurrent opener's crashed core begin cannot leave the binding stale after the
    retain: an open that refuses writes nothing, except the recorded CP-1B `_activate`
    derivation residual (QUEUE, review-adversary-fix-5 L-2).
    """
    fields = _transcript_fields(store)
    chain = _chain(store, _head(store).content_hash())
    begins = fields["begins"] if recovered is None else (*fields["begins"], recovered)
    covered = _verify_begins(store, begins)
    outcomes = {o.intent_sha256: o for o in fields["submission_outcomes"]}
    pending = _unresolved(store)
    for intent in fields["submission_intents"]:
        stored_binding = _stored_bytes(store, "bindings", intent.binding.content_hash())
        if stored_binding != intent.binding.model_dump_json().encode():
            raise OwnerError("identity_mismatch")
        if intent.content_hash() in outcomes:
            edges = _verify_outcome(store, intent, outcomes[intent.content_hash()], chain)
        else:
            if not pending or intent != pending[0]:
                raise OwnerError("identity_mismatch")
            rebound, issues = _prepare_bound_readonly(store, intent)
            if (
                rebound != intent.binding
                or intent.snapshot_before_sha256 != intent.binding.binding.snapshot_sha256
            ):
                raise OwnerError("identity_mismatch")
            start = next(
                (
                    index
                    for index, s in enumerate(chain)
                    if s.content_hash() == intent.snapshot_before_sha256
                ),
                None,
            )
            if start is None:
                raise OwnerError("identity_mismatch")
            edges = set()
            if issues and start != len(chain) - 1:
                raise OwnerError("identity_mismatch")
            for before, after in zip(chain[start:-1], chain[start + 1 :], strict=True):
                if _propose_submission(store, before, intent.binding) != after:
                    raise OwnerError("identity_mismatch")
                edges.add((before.content_hash(), after.content_hash()))
        if covered & edges:
            raise OwnerError("identity_mismatch")
        covered.update(edges)
    if covered != {(a.content_hash(), b.content_hash()) for a, b in itertools.pairwise(chain)}:
        raise OwnerError("identity_mismatch")
    # A private in-memory view supplies only already authenticated immutable
    # records to the common checks; it is never persisted as setup authority.
    _verify_transcripts(
        store,
        _TranscriptRecords(
            run=setup.run,
            foundation_calls=fields["foundation_calls"],
            foundation_input_reads=fields["foundation_input_reads"],
            owner_sessions=fields["owner_sessions"],
            owner_access_reads=fields["owner_access_reads"],
            owner_calls=fields["owner_calls"],
        ),
    )


def _bootstrap_log(store: Execution, setup: OwnerSetup) -> BeginRecord | None:
    """Compute the one begin record a crash between a core begin and its retention loses.

    `_begin` writes the core snapshot first and the BeginRecord second, so a crash in
    between leaves exactly this state: the last chain edge has no record and no stored
    record is bound to the head, because every record bound to a head (foundation
    calls and reads, owner sessions, reads and calls, bindings, intents, outcomes,
    participations) is written only after the begin record. Begin 1 is recovered
    against the setup record; a later begin by `_recover_last_begin`. A last record
    deleted inside that window is indistinguishable from the crash and is recovered to
    the same replay-verified state; one deleted after a record bound to its head was
    written is not, and is left, like every other gap, to `_verify_open_history` to
    refuse. Nothing is written here: the caller authenticates the returned record with
    the stored history (`_verify_open_history`) and retains it only after that passes.
    """
    begins = tuple(sorted(_records(store, "begins", BeginRecord), key=lambda b: b.index))
    chain = _chain(store, _head(store).content_hash())
    if len(chain) == 1:
        return None
    if begins:
        return _recover_last_begin(store, begins, chain)
    first, current = chain[0], chain[-1]
    if (
        len(chain) != 2
        or first.content_hash() != setup.initial_snapshot_sha256
        or current.heads
        or len(current.attempts) != 1
        or any(e.kind != "setup" for e in _inventory(store))
    ):
        raise OwnerError("identity_mismatch")
    attempt = current.attempts[0]
    expected = Attempt(
        ticket_id=attempt.ticket_id,
        module_id="CP-0",
        inputs=current_inputs(first, "CP-0"),
        number=0,
    )
    if attempt != expected:
        raise OwnerError("identity_mismatch")
    return BeginRecord(
        index=1,
        module_id="CP-0",
        snapshot_before_sha256=first.content_hash(),
        snapshot_after_sha256=current.content_hash(),
        ticket_id=attempt.ticket_id,
        attempt=0,
        error_code=None,
    )


def _bound_to(store: Execution, digest: str) -> bool:
    """Whether any stored record is bound to the snapshot `digest`.

    Every record a run writes after a begin names the begin's head: foundation calls and
    reads, owner sessions, reads and calls, bindings and participations through their
    binding, intents through `snapshot_before_sha256`, outcomes through
    `snapshot_after_sha256`. All are written only after the BeginRecord is retained.
    """
    return (
        any(
            c.binding.snapshot_sha256 == digest
            for c in _records(store, "foundation-calls", FinancialCall)
        )
        or any(
            r.binding.snapshot_sha256 == digest
            for r in _records(store, "foundation-reads", InputRead)
        )
        or any(
            s.binding.snapshot_sha256 == digest
            for s in _records(store, "owner-sessions", OwnerSession)
        )
        or any(
            r.binding.snapshot_sha256 == digest
            for r in _records(store, "owner-reads", OwnerAccessRead)
        )
        or any(
            c.receipt.binding.snapshot_sha256 == digest
            for c in _records(store, "owner-calls", OwnerToolCall)
        )
        or any(
            b.binding.snapshot_sha256 == digest
            for b in _records(store, "bindings", BoundSubmission)
        )
        or any(
            i.snapshot_before_sha256 == digest or i.binding.binding.snapshot_sha256 == digest
            for i in _records(store, "intents", SubmissionIntent)
        )
        or any(
            o.snapshot_after_sha256 == digest
            for o in _records(store, "outcomes", SubmissionOutcome)
        )
        or any(
            p.binding.snapshot_sha256 == digest
            for p in _records(store, "participations", EarningsParticipation)
        )
    )


def _recover_last_begin(
    store: Execution, begins: tuple[BeginRecord, ...], chain: tuple[ExecutionSnapshot, ...]
) -> BeginRecord | None:
    """Synthesise the begin record of the last chain edge when only that record is lost.

    Only the last edge is recoverable, and only inside the crash window: no stored
    record is bound to the head, its `before` has no pending attempt and the head adds
    exactly one pending attempt with a fresh ticket, which is what a core `begin()`
    writes (execution.py:626-641) and nothing else does. The record is returned, not
    retained: `_verify_open_history` authenticates it with the stored begins (the same
    core replay, `_verify_begin`) and the rest of the history before the caller retains it.
    """
    before, head = chain[-2], chain[-1]
    if (
        [b.index for b in begins] != list(range(1, len(begins) + 1))
        or any(b.error_code is not None for b in begins)
        or any(b.snapshot_after_sha256 == head.content_hash() for b in begins)
        or any(a.status == "pending" for a in before.attempts)
        or _bound_to(store, head.content_hash())
    ):
        # Not the crash state: a refusal ends the run, a begin reaching the head needs
        # no recovery, a pending attempt in `before` makes the last edge a submission
        # edge, and a record bound to the head was written after the begin record, so
        # that record was deleted. The records are judged as stored by
        # `_verify_open_history`.
        return None
    added = head.attempts[len(before.attempts) :]
    if (
        len(added) != 1
        or added[0].status != "pending"
        or added[0].module_id not in {"CP-0", "CP-1", "CP-1B"}
        or any(a.ticket_id == added[0].ticket_id for a in before.attempts)
        or head
        != before.model_copy(
            update={"parent": before.content_hash(), "attempts": (*before.attempts, added[0])}
        )
    ):
        # The last edge is uncovered and `before` is idle, so only a core begin can have
        # produced the head; any other head is an altered journal. A core begin's ticket
        # is fresh (`_historical` requires one match), which the replay in
        # `_verify_begin` cannot see because it adopts the recorded ticket.
        raise OwnerError("identity_mismatch")
    return BeginRecord(
        index=len(begins) + 1,
        module_id=cast(Literal["CP-0", "CP-1", "CP-1B"], added[0].module_id),
        snapshot_before_sha256=before.content_hash(),
        snapshot_after_sha256=head.content_hash(),
        ticket_id=added[0].ticket_id,
        attempt=added[0].number,
        error_code=None,
    )


@dataclass(frozen=True, slots=True)
class _TranscriptRecords:
    run: Run
    foundation_calls: tuple[FinancialCall, ...]
    foundation_input_reads: tuple[InputRead, ...]
    owner_sessions: tuple[OwnerSession, ...]
    owner_access_reads: tuple[OwnerAccessRead, ...]
    owner_calls: tuple[OwnerToolCall, ...]


def _verify_transcripts(
    store: Execution, receipt: EarningsOwnerReceipt | _TranscriptRecords
) -> None:
    calls_by_binding: dict[str, list[FinancialCall]] = {}
    budgets: dict[tuple[str, str], int] = {}
    call_ids = []
    for call in receipt.foundation_calls:
        binding = call.binding
        if binding.step_id not in _SOURCE_PHASES:
            raise OwnerError("identity_mismatch")
        key = (binding.ticket_id, binding.step_id)
        budgets[key] = budgets.get(key, 0) + 1
        if budgets[key] > MAX_FOUNDATION:
            raise OwnerError("transport_limit")
        calls_by_binding.setdefault(binding.content_hash(), []).append(call)
        call_ids.append(call.call_id)
    for calls in calls_by_binding.values():
        ordered = tuple(sorted(calls, key=lambda c: c.sequence))
        if ordered != _foundation_calls(store, ordered[0].binding):
            raise OwnerError("identity_mismatch")
        _source_session(store, ordered[0].binding)
    reads_by_binding: dict[str, list[InputRead]] = {}
    read_budgets: dict[tuple[str, str], int] = {}
    for read in receipt.foundation_input_reads:
        key = (read.binding.ticket_id, read.binding.step_id)
        read_budgets[key] = read_budgets.get(key, 0) + 1
        if read_budgets[key] > MAX_FOUNDATION or (read.inputs_sha256, read.body) != _projection(
            store, read.binding
        ):
            raise OwnerError("identity_mismatch")
        reads_by_binding.setdefault(read.binding.content_hash(), []).append(read)
    for reads in reads_by_binding.values():
        if sorted(r.sequence for r in reads) != list(range(1, len(reads) + 1)):
            raise OwnerError("identity_mismatch")
    sessions = {s.session_id: s for s in receipt.owner_sessions}
    if len(sessions) != len(receipt.owner_sessions):
        raise OwnerError("identity_mismatch")
    for ticket_id in {s.binding.ticket_id for s in receipt.owner_sessions}:
        indexed = sorted(
            s.index for s in receipt.owner_sessions if s.binding.ticket_id == ticket_id
        )
        if indexed != list(range(1, len(indexed) + 1)) or len(indexed) > MAX_OWNER_SESSIONS:
            raise OwnerError("identity_mismatch")
    if tuple(c.ordinal for c in receipt.owner_calls) != tuple(
        range(1, len(receipt.owner_calls) + 1)
    ):
        raise OwnerError("identity_mismatch")
    for session in receipt.owner_sessions:
        _, prior, current = _case_parameters(receipt.run)
        owner_calls = tuple(c for c in receipt.owner_calls if c.session_id == session.session_id)
        _owner_session_proof(store, session, owner_calls, prior, current)
        owner_reads = tuple(
            r for r in receipt.owner_access_reads if r.session_id == session.session_id
        )
        if (
            [r.sequence for r in owner_reads] != list(range(1, len(owner_reads) + 1))
            or len(owner_reads) > MAX_ACCESS_READS
            or any(
                r.binding != session.binding
                or r.access_manifest_json != session.access_manifest_json
                for r in owner_reads
            )
        ):
            raise OwnerError("identity_mismatch")
    if any(c.session_id not in sessions for c in receipt.owner_calls) or any(
        r.session_id not in sessions for r in receipt.owner_access_reads
    ):
        raise OwnerError("identity_mismatch")
    for ticket_id in {c.receipt.binding.ticket_id for c in receipt.owner_calls}:
        if (
            sum(c.receipt.binding.ticket_id == ticket_id for c in receipt.owner_calls)
            > MAX_OWNER_CALLS
        ):
            raise OwnerError("transport_limit")
    call_ids.extend(c.receipt.call_id for c in receipt.owner_calls)
    if len(call_ids) != len(set(call_ids)):
        raise OwnerError("identity_mismatch")


def _expected_inventory(store: Execution, receipt: EarningsOwnerReceipt) -> tuple[AuditEntry, ...]:
    entries: set[tuple[str, str]] = set()
    setup, _ = _setup(store, _CASE_MANIFEST)
    entries.add(("setup", setup.content_hash()))
    embedded = {
        "transport-messages": receipt.transport_messages,
        "begins": receipt.begins,
        "foundation-calls": receipt.foundation_calls,
        "foundation-reads": receipt.foundation_input_reads,
        "owner-sessions": receipt.owner_sessions,
        "owner-reads": receipt.owner_access_reads,
        "owner-calls": receipt.owner_calls,
        "intents": receipt.submission_intents,
        "outcomes": receipt.submission_outcomes,
    }
    for kind, records in embedded.items():
        for record in records:
            entries.add((kind, record.content_hash()))
            if (
                _stored_bytes(store, kind, record.content_hash())
                != record.model_dump_json().encode()
            ):
                raise OwnerError("identity_mismatch")
    for intent in receipt.submission_intents:
        bound = intent.binding
        entries.add(("bindings", bound.content_hash()))
        if (
            _stored_bytes(store, "bindings", bound.content_hash())
            != bound.model_dump_json().encode()
        ):
            raise OwnerError("identity_mismatch")
        entries.update(
            ("payloads", digest)
            for digest in (bound.raw_payload_sha256, bound.stored_payload_sha256)
        )
        if bound.participation_sha256 is not None:
            entries.add(("participations", bound.participation_sha256))
            envelope = OwnerSubmissionEnvelope.model_validate_json(
                _raw(store, bound.stored_payload_sha256)
            )
            if (
                envelope.participation.content_hash() != bound.participation_sha256
                or _stored_bytes(store, "participations", bound.participation_sha256)
                != envelope.participation.model_dump_json().encode()
            ):
                raise OwnerError("identity_mismatch")
    intents = {i.content_hash(): i for i in receipt.submission_intents}
    for outcome in receipt.submission_outcomes:
        if outcome.intent_sha256 not in intents:
            raise OwnerError("identity_mismatch")
        if outcome.candidate_sha256 is not None:
            entries.add(("payloads", outcome.candidate_sha256))
            with _stored_read():
                journal_candidate = store.payload(outcome.candidate_sha256)
            if _text(store, outcome.candidate_sha256) != journal_candidate:
                raise OwnerError("identity_mismatch")
        if (
            isinstance(intents[outcome.intent_sha256].binding.binding, OwnerBinding)
            and outcome.step_output_sha256 is not None
        ):
            entries.add(("stages", outcome.step_output_sha256))
            with _stored_read():
                stored_stage = store.step_output(outcome.step_output_sha256)
            # The blob is authenticated by the core read above and matched to the step
            # by `_verify_outcome`; a stage that no longer parses is a B1 schema or
            # composition defect, which propagates (lease: programming failures propagate).
            stage = EarningsOwnerStage.model_validate_json(stored_stage)
            envelope = OwnerSubmissionEnvelope.model_validate_json(
                _raw(store, intents[outcome.intent_sha256].binding.stored_payload_sha256)
            )
            if (
                _owner_stage(store, envelope) != stage
                or _stored_bytes(store, "stages", outcome.step_output_sha256)
                != stage.model_dump_json().encode()
            ):
                raise OwnerError("identity_mismatch")
    for message in receipt.transport_messages:
        entries.add(("payloads", message.request_sha256))
    return tuple(
        _parse(AuditEntry, {"kind": kind, "sha256": digest}) for kind, digest in sorted(entries)
    )


def _verify_owner(store: Execution, receipt: EarningsOwnerReceipt, *, sealed: bool) -> None:
    receipt = EarningsOwnerReceipt.model_validate_json(receipt.model_dump_json())
    anchor = _snapshot(store, receipt.owner_snapshot_sha256)
    case, pins = _case_pins(_CASE_MANIFEST, receipt.case_id, store.pack(anchor))
    setup, _ = _setup(store, _CASE_MANIFEST)
    if (
        setup.run,
        setup.pack_sha256,
        setup.case_id,
        setup.pins,
        setup.participant,
        setup.transport,
    ) != (
        receipt.run,
        receipt.pack_sha256,
        receipt.case_id,
        receipt.pins,
        receipt.participant,
        receipt.transport,
    ):
        raise OwnerError("identity_mismatch")
    if (
        receipt.run != anchor.run
        or receipt.pack_sha256 != anchor.pack_sha256
        or receipt.pins != pins
        or _unresolved(store)
        or len(receipt.model_dump_json().encode()) > MAX_RECEIPT
    ):
        raise OwnerError("identity_mismatch")
    chain = _chain(store, receipt.owner_snapshot_sha256)
    if chain[0].attempts or chain[0].heads:
        raise OwnerError("identity_mismatch")
    covered = _verify_begins(store, receipt.begins)
    outcomes = {o.intent_sha256: o for o in receipt.submission_outcomes}
    if (
        len(outcomes) != len(receipt.submission_outcomes)
        or len(outcomes) != len(receipt.submission_intents)
        or [i.index for i in receipt.submission_intents]
        != list(range(1, len(receipt.submission_intents) + 1))
    ):
        raise OwnerError("identity_mismatch")
    budgets: dict[tuple[str, str], int] = {}
    for intent in receipt.submission_intents:
        key = (intent.binding.binding.ticket_id, intent.binding.binding.step_id)
        budgets[key] = budgets.get(key, 0) + 1
        if budgets[key] > MAX_FOUNDATION or intent.content_hash() not in outcomes:
            raise OwnerError("identity_mismatch")
        edges = _verify_outcome(store, intent, outcomes[intent.content_hash()], chain)
        if covered & edges:
            raise OwnerError("identity_mismatch")
        covered.update(edges)
    if covered != {(a.content_hash(), b.content_hash()) for a, b in itertools.pairwise(chain)}:
        raise OwnerError("identity_mismatch")
    _verify_transcripts(store, receipt)
    if _head_record(store, anchor, "CP-0") != receipt.cp0:
        raise OwnerError("identity_mismatch")
    if receipt.outcome == "owner_settled":
        if (
            tuple(h.module_id for h in anchor.heads) != ("CP-0", "CP-1", "CP-1B")
            or any(a.status == "pending" for a in anchor.attempts)
            or _head_record(store, anchor, "CP-1") != receipt.cp1
            or _head_record(store, anchor, "CP-1B") != receipt.cp1b
            or receipt.cp1b is None
            or receipt.cp1b.head.status != "restricted"
            or receipt.cp1b.head.qualification is not None
            or receipt.cp1 is None
            or receipt.cp1.head.qualification != PROMOTED
        ):
            raise OwnerError("identity_mismatch")
        attempt = next(a for a in anchor.attempts if a.ticket_id == receipt.cp1b.ticket_id)
        if len(attempt.steps) != 1 or attempt.steps[0].output_sha256 != receipt.cp1b_stage_sha256:
            raise OwnerError("identity_mismatch")
        _verify_cp5_descendants(store, anchor)
    elif (
        tuple(h.module_id for h in anchor.heads) != ("CP-0",)
        or receipt.cp0.head.status != "restricted"
        or store.read() != anchor
        or any(a.module_id != "CP-0" for a in anchor.attempts)
        or not any(
            b.module_id == "CP-1" and b.error_code == "not_authorized" for b in receipt.begins
        )
        or case["source_state"] != "financial_missing"
    ):
        raise OwnerError("identity_mismatch")
    expected = _expected_inventory(store, receipt)
    if receipt.audit_inventory != expected or _inventory(store) != expected:
        raise OwnerError("identity_mismatch")
    if receipt.transport == "python-api" and receipt.transport_messages:
        raise OwnerError("identity_mismatch")
    if [m.index for m in receipt.transport_messages] != list(
        range(1, len(receipt.transport_messages) + 1)
    ) or len(receipt.transport_messages) > MAX_MESSAGES:
        raise OwnerError("identity_mismatch")
    for message in receipt.transport_messages:
        operation, _, _ = _classify_frame(_raw(store, message.request_sha256))
        if message.operation != operation:
            raise OwnerError("identity_mismatch")
    if sealed:
        root = store.directory / "earnings-owner-audit"
        if (root / "owner-receipt.json").read_bytes() != receipt.model_dump_json().encode() or (
            root / "owner-receipt.sha256"
        ).read_bytes() != receipt.content_hash().encode("ascii"):
            raise OwnerError("identity_mismatch")


_KNOWN_CORE_TAMPER = {
    "Execution snapshot hash mismatch",
    "Execution result blob is not the canonical module",
    "Execution head does not match its result blob",
    "Execution head commands do not match its result blob",
    "Execution head status does not match its result blob",
    "Execution pack blob is not the canonical pack of this snapshot",
    "Required upstream is unrun, stale or blocked",
    "Module is not selected for this run",
    "Invalid blob hash",
    "Invalid execution pointer",
}


@contextmanager
def _tamper_is_identity_mismatch() -> Iterator[None]:
    """Map the known ways tampered or missing stored evidence fails to `identity_mismatch`.

    Fail-closed, never a success path: each listed error means stored evidence is
    absent, malformed or inconsistent, so the caller is refused. `KeyError` and
    `StopIteration` come from looking up records the verified prefix requires
    (`next(...)` and dict indexing over audit data), so a missing record is tamper.
    The mapping can also hide a programming defect of the same type, so the original
    error is kept as `__cause__` (never sent to the actor, whose reply carries only
    the category). Any other `ValueError`, including unknown core messages, propagates.
    """
    try:
        yield
    except OwnerError:
        raise
    except (
        ValidationError,
        FileNotFoundError,
        IsADirectoryError,
        KeyError,
        StopIteration,
        UnicodeDecodeError,
    ) as error:
        raise OwnerError("identity_mismatch") from error
    except ValueError as error:
        if str(error) in _KNOWN_CORE_TAMPER or re.fullmatch(
            r"Execution blob [0-9a-f]{64} (?:is missing|hash mismatch)", str(error)
        ):
            raise OwnerError("identity_mismatch") from error
        raise


def _earlier_receipt(raw: bytes, receipt: EarningsOwnerReceipt) -> bool:
    """`raw` is this store's receipt from an earlier attempt that crashed before the seal."""
    with _stored_read():
        earlier = EarningsOwnerReceipt.model_validate_json(raw)
    later = receipt.transport_messages
    return (
        earlier.model_dump_json().encode() == raw
        and later[: len(earlier.transport_messages)] == earlier.transport_messages
        and all(entry in receipt.audit_inventory for entry in earlier.audit_inventory)
        and earlier.model_copy(
            update={"transport_messages": later, "audit_inventory": receipt.audit_inventory}
        )
        == receipt
    )


def verify_earnings_owner_receipt(store: Execution, receipt: EarningsOwnerReceipt) -> None:
    """Read-only authentication of the owner prefix and permitted CP5 descendants."""
    with _tamper_is_identity_mismatch():
        _verify_owner(store, receipt, sealed=True)


class EarningsWorkflow:
    """One writer over a fresh source foundation and immutable owner evidence."""

    def __init__(self) -> None:
        raise OwnerError("not_permitted")

    @classmethod
    def create(
        cls,
        directory: Path,
        pack: PreparedPack,
        *,
        case_manifest: Path,
        case_id: OwnerCaseId,
        participant: str = "trusted-python",
        transport: Transport = "python-api",
    ) -> EarningsWorkflow:
        if (
            type(participant) is not str
            or not participant
            or transport not in {"python-api", "bounded-json-lines/1"}
        ):
            raise OwnerError("bad_arguments")
        pack = PreparedPack.model_validate_json(pack.model_dump_json())
        case, pins = _case_pins(case_manifest, case_id, pack)
        policy = _policy(case_manifest)
        store = Execution.create(directory, pack)
        initial = store.read()
        if initial != ExecutionSnapshot(run=pack.run, pack_sha256=pack.content_hash()):
            raise OwnerError("identity_mismatch")
        setup = OwnerSetup(
            run=pack.run,
            pack_sha256=pack.content_hash(),
            initial_snapshot_sha256=initial.content_hash(),
            case_id=case_id,
            pins=pins,
            participant=participant,
            transport=transport,
            policy_sha256=policy,
        )
        _retain(store, "setup", setup)
        instance = object.__new__(cls)
        instance._initialize(store, case)
        instance._setup_record = setup
        with instance._locked():
            attempt = instance._begin("CP-0")
            if attempt is None:
                raise OwnerError("identity_mismatch")
            instance._activate(attempt, "source_readiness")
        return instance

    @classmethod
    def open(
        cls, directory: Path, *, case_manifest: Path, participant: str, transport: Transport
    ) -> EarningsWorkflow:
        store = Execution(directory)
        try:
            setup, case = _setup(store, case_manifest)
            if participant != setup.participant or transport != setup.transport:
                raise OwnerError("identity_mismatch")
        except (ValidationError, FileNotFoundError, KeyError, StopIteration, ValueError) as error:
            # Fail-closed: the setup record or case manifest is absent or malformed,
            # so the store cannot be opened. ValueError is deliberately broad here
            # because every setup failure means the store is not a valid B1 store;
            # the original error is kept as __cause__ for the operator.
            if isinstance(error, OwnerError):
                raise
            raise OwnerError("identity_mismatch") from error
        instance = object.__new__(cls)
        instance._initialize(store, case)
        instance._setup_record = setup
        with instance._locked(inspect_sealed=True):
            if instance._sealed:
                with _stored_read():
                    receipt = EarningsOwnerReceipt.model_validate_json(
                        (directory / "earnings-owner-audit/owner-receipt.json").read_bytes()
                    )
                verify_earnings_owner_receipt(store, receipt)
                instance._phase, instance._outcome = "complete", receipt.outcome
                return instance
            # `_initialize` read the head before the lock; another opener may have moved
            # it since (a core begin whose BeginRecord then crashed). Read it again under
            # the lock, or `_activate` below would refuse `stale_binding` after the retain.
            instance._current_sha256 = _head(store).content_hash()
            recovered = _bootstrap_log(store, setup)
            _verify_open_history(store, setup, recovered)
            if recovered is not None:
                # Retained only now, after the whole stored history authenticated it, so
                # an open that refuses leaves the store byte-identical, except the recorded
                # CP-1B `_activate` derivation residual (QUEUE, review-adversary-fix-5 L-2);
                # and before the resume below, which writes records bound to the head.
                _retain(store, "begins", recovered)
            snapshot = _head(store)
            if snapshot.content_hash() == setup.initial_snapshot_sha256:
                attempt = instance._begin("CP-0")
                if attempt is None:
                    raise OwnerError("identity_mismatch")
                instance._activate(attempt, "source_readiness")
                return instance
            unresolved = _unresolved(store)
            if unresolved:
                instance._binding = unresolved[0].binding.binding
                instance._phase = cast(Phase, instance._binding.step_id)
                instance._owner_session = _intent_session(store, unresolved[0])
                return instance
            pending = [a for a in snapshot.attempts if a.status == "pending"]
            if len(pending) > 1:
                raise OwnerError("identity_mismatch")
            if pending:
                attempt = pending[0]
                if attempt.module_id == "CP-0":
                    phase = "source_readiness"
                elif attempt.module_id == "CP-1B":
                    phase = "earnings_delta"
                else:
                    phase = CP1_PROMOTION[len(attempt.steps)]
                instance._activate(attempt, phase, replay=True)
                return instance
            begins = _records(store, "begins", BeginRecord)
            if any(b.error_code == "not_authorized" for b in begins):
                if case["source_state"] == "financial_missing":
                    instance._phase, instance._outcome = "complete", "cp1_not_authorized"
                else:
                    instance._phase, instance._outcome = "failed", None
                return instance
            intents = sorted(_records(store, "intents", SubmissionIntent), key=lambda i: i.index)
            outcomes = {o.intent_sha256: o for o in _records(store, "outcomes", SubmissionOutcome)}
            if not intents or intents[-1].content_hash() not in outcomes:
                raise OwnerError("identity_mismatch")
            instance._binding = intents[-1].binding.binding
            instance._advance(outcomes[intents[-1].content_hash()], intents[-1].binding)
        return instance

    def _initialize(self, store: Execution, case: dict[str, Any]) -> None:
        self._store = store
        self._case = case
        self._operation = Lock()
        self._dispatcher = Lock()
        self._current_sha256 = store.read().content_hash()
        self._source: SourceSession | None = None
        self._upstream: UpstreamTools | None = None
        self._owner_session: OwnerSession | None = None
        self._binding: FinancialBinding | OwnerBinding | None = None
        self._phase: Phase = "failed"
        self._outcome: OutcomeKind | None = None
        self._setup_record: OwnerSetup
        self._sealed = _sealed_on_disk(store)

    @contextmanager
    def _locked(self, *, inspect_sealed: bool = False) -> Iterator[None]:
        from deploy_workflow.platform_io import locks as fcntl

        if not self._operation.acquire(blocking=False):
            raise OwnerError("not_permitted")
        try:
            with (self._store.directory / ".earnings-owner.lock").open("a") as stream:
                try:
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise OwnerError("not_permitted") from None
                try:
                    # Another instance may have sealed since `_initialize` read the flag;
                    # the seal is read again under the lock, before anything is written.
                    self._sealed = self._sealed or _sealed_on_disk(self._store)
                    if self._sealed and not inspect_sealed:
                        raise OwnerError("not_permitted")
                    yield
                finally:
                    fcntl.flock(stream, fcntl.LOCK_UN)
        finally:
            self._operation.release()

    def _current(self) -> ExecutionSnapshot:
        snapshot = self._store.read()
        if snapshot.content_hash() != self._current_sha256:
            raise OwnerError("stale_binding")
        with _stored_read():
            self._store.pack(snapshot)
        return snapshot

    def _begin(self, module_id: str) -> Attempt | None:
        if module_id not in {"CP-0", "CP-1", "CP-1B"}:
            raise OwnerError("not_permitted")
        selected = cast(Literal["CP-0", "CP-1", "CP-1B"], module_id)
        before = self._current()
        records = _records(self._store, "begins", BeginRecord)
        try:
            attempt = self._store.begin(module_id)
        except NotAuthorized:
            if module_id != "CP-1" or self._store.read().content_hash() != before.content_hash():
                raise OwnerError("identity_mismatch") from None
            record = BeginRecord(
                index=len(records) + 1,
                module_id=selected,
                snapshot_before_sha256=before.content_hash(),
                snapshot_after_sha256=before.content_hash(),
                ticket_id=None,
                attempt=None,
                error_code="not_authorized",
            )
            _retain(self._store, "begins", record)
            if self._case["source_state"] != "financial_missing":
                # An actual NotAuthorized on a case whose source is present came
                # from the actor's CP0 review, not a source gap: not a genuine
                # negative, so the run fails rather than claiming the negative outcome.
                self._phase, self._outcome, self._binding = "failed", None, None
                return None
            self._phase, self._outcome, self._binding = "complete", "cp1_not_authorized", None
            return None
        after = self._store.read()
        record = BeginRecord(
            index=len(records) + 1,
            module_id=selected,
            snapshot_before_sha256=before.content_hash(),
            snapshot_after_sha256=after.content_hash(),
            ticket_id=attempt.ticket_id,
            attempt=attempt.number,
            error_code=None,
        )
        _retain(self._store, "begins", record)
        self._current_sha256 = after.content_hash()
        return attempt

    def _activate(self, attempt: Attempt, phase: str, *, replay: bool = False) -> None:
        if phase not in _SCHEMAS:
            raise OwnerError("not_permitted")
        snapshot = self._current()
        self._binding = _binding(snapshot, attempt, phase)
        self._phase, self._outcome = cast(Phase, phase), None
        self._source = None
        self._upstream = None
        self._owner_session = None
        if isinstance(self._binding, FinancialBinding) and phase in _SOURCE_PHASES:
            self._source = (
                _source_session(self._store, self._binding)
                if replay
                else SourceSession.from_execution(self._store, attempt.ticket_id, phase)
            )
        elif isinstance(self._binding, OwnerBinding):
            sessions = tuple(
                s
                for s in _records(self._store, "owner-sessions", OwnerSession)
                if s.binding.ticket_id == attempt.ticket_id
            )
            if len(sessions) >= MAX_OWNER_SESSIONS:
                raise OwnerError("transport_limit")
            grant, _, producer = _grant(
                self._store,
                self._binding,
                self._case["prior_period_id"],
                self._case["current_period_id"],
            )
            tools = UpstreamTools.from_execution(
                self._store, attempt.ticket_id, "earnings_delta", grants=grant
            )
            header = tools.access_manifest
            if header != _manifest(self._binding, grant, producer):
                raise OwnerError("identity_mismatch")
            record = OwnerSession(
                session_id="owner-session:" + uuid4().hex,
                index=len(sessions) + 1,
                binding=self._binding,
                normalized_grant_json=_canonical(grant),
                access_manifest_json=_canonical(header),
            )
            self._current()
            _retain(self._store, "owner-sessions", record)
            self._upstream, self._owner_session = tools, record

    def state(self) -> WorkflowState:
        with self._locked(inspect_sealed=True):
            self._current()
            binding = self._binding if self._phase not in {"complete", "failed"} else None
            return WorkflowState(
                phase=self._phase,
                module_id=binding.module_id if binding else None,
                step_id=binding.step_id if binding else None,
                ticket_id=binding.ticket_id if binding else None,
                attempt=binding.attempt if binding else None,
                prior_period_id=self._case["prior_period_id"],
                current_period_id=self._case["current_period_id"],
                outcome=self._outcome,
            )

    def invoke(self, tool_name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        with self._locked():
            self._current()
            if _unresolved(self._store) or self._binding is None:
                raise OwnerError("not_permitted")
            detached = _json_copy(arguments)
            if type(tool_name) is not str or not isinstance(detached, dict):
                raise OwnerError("bad_arguments")
            if isinstance(self._binding, OwnerBinding):
                if self._upstream is None or self._owner_session is None:
                    raise OwnerError("not_permitted")
                calls = _records(self._store, "owner-calls", OwnerToolCall)
                if (
                    sum(c.receipt.binding.ticket_id == self._binding.ticket_id for c in calls)
                    >= MAX_OWNER_CALLS
                ):
                    raise OwnerError("transport_limit")
                receipt = _parse(OwnerToolReceipt, self._upstream.invoke(tool_name, detached))
                if receipt.binding != self._binding:
                    raise OwnerError("identity_mismatch")
                record = OwnerToolCall(
                    ordinal=len(calls) + 1,
                    session_id=self._owner_session.session_id,
                    receipt=receipt,
                )
                self._current()
                _retain(self._store, "owner-calls", record)
                result = receipt.model_dump(mode="json")
            else:
                if self._source is None or self._phase not in _SOURCE_PHASES:
                    raise OwnerError("not_permitted")
                foundation_calls = _records(self._store, "foundation-calls", FinancialCall)
                if (
                    sum(
                        c.binding.ticket_id == self._binding.ticket_id
                        and c.binding.step_id == self._binding.step_id
                        for c in foundation_calls
                    )
                    >= MAX_FOUNDATION
                ):
                    raise OwnerError("transport_limit")
                source_receipt = _parse(FinancialCall, self._source.invoke(tool_name, detached))
                if source_receipt.binding != self._binding:
                    raise OwnerError("identity_mismatch")
                self._current()
                _retain(self._store, "foundation-calls", source_receipt)
                result = source_receipt.model_dump(mode="json")
            self._current()
            return result

    def read_inputs(self) -> InputRead | OwnerAccessRead:
        with self._locked():
            self._current()
            if _unresolved(self._store) or self._binding is None:
                raise OwnerError("not_permitted")
            record: InputRead | OwnerAccessRead
            if isinstance(self._binding, OwnerBinding):
                if self._upstream is None or self._owner_session is None:
                    raise OwnerError("not_permitted")
                reads = tuple(
                    r
                    for r in _records(self._store, "owner-reads", OwnerAccessRead)
                    if r.session_id == self._owner_session.session_id
                )
                if len(reads) >= MAX_ACCESS_READS:
                    raise OwnerError("transport_limit")
                header = _canonical(self._upstream.access_manifest)
                if header != self._owner_session.access_manifest_json:
                    raise OwnerError("identity_mismatch")
                record = OwnerAccessRead(
                    session_id=self._owner_session.session_id,
                    sequence=len(reads) + 1,
                    binding=self._binding,
                    access_manifest_json=header,
                )
                kind = "owner-reads"
            else:
                if self._phase not in {"narrative", "readiness", "quality"}:
                    raise OwnerError("not_permitted")
                foundation_reads = tuple(
                    r
                    for r in _records(self._store, "foundation-reads", InputRead)
                    if r.binding.ticket_id == self._binding.ticket_id
                    and r.binding.step_id == self._binding.step_id
                )
                if len(foundation_reads) >= MAX_FOUNDATION:
                    raise OwnerError("transport_limit")
                digest, body = _projection(self._store, self._binding)
                record = InputRead(
                    binding=self._binding,
                    sequence=1 + sum(r.binding == self._binding for r in foundation_reads),
                    inputs_sha256=digest,
                    body=body,
                )
                kind = "foundation-reads"
            self._current()
            _retain(self._store, kind, record)
            self._current()
            return record

    def _advance(self, outcome: SubmissionOutcome, bound: BoundSubmission) -> None:
        snapshot = self._store.read()
        self._current_sha256 = snapshot.content_hash()
        attempt = next(a for a in snapshot.attempts if a.ticket_id == bound.binding.ticket_id)
        if outcome.disposition == "refused":
            if isinstance(bound.binding, OwnerBinding) and self._upstream is None:
                # Reopen deliberately cannot restore an opaque nonce. Once the
                # old intent is resolved, persist a fresh actual session; the
                # old intent keeps its original selected ID and captured prefix.
                self._activate(attempt, "earnings_delta")
            elif (
                isinstance(bound.binding, FinancialBinding)
                and bound.binding.step_id in _SOURCE_PHASES
                and self._source is None
            ):
                self._activate(attempt, bound.binding.step_id, replay=True)
            return
        if outcome.disposition == "valid" and bound.binding.step_id == "earnings_delta":
            self._phase, self._outcome, self._binding = "complete", "owner_settled", None
            return
        if outcome.disposition == "valid" and bound.binding.step_id in {
            "source_readiness",
            "quality",
        }:
            module_id = "CP-1" if bound.binding.step_id == "source_readiness" else "CP-1B"
            if module_id == "CP-1B":
                candidate = _cp1_candidate(self._store, snapshot, attempt)
                if candidate.content_hash() != attempt.payload_sha256:
                    raise OwnerError("identity_mismatch")
                head = next(h for h in snapshot.heads if h.module_id == "CP-1")
                _preflight(
                    _FrozenExecution(self._store, snapshot).head_module(head),
                    self._case["prior_period_id"],
                    self._case["current_period_id"],
                    self._store.pack(snapshot),
                )
            next_attempt = self._begin(module_id)
            if next_attempt is not None:
                self._activate(
                    next_attempt, "source_context" if module_id == "CP-1" else "earnings_delta"
                )
        elif attempt.status == "pending":
            phase = (
                CP1_PROMOTION[len(attempt.steps)]
                if outcome.disposition == "valid"
                else bound.binding.step_id
            )
            self._activate(attempt, phase)
        elif attempt.number == 0:
            next_attempt = self._begin(attempt.module_id)
            if next_attempt is None:
                raise OwnerError("identity_mismatch")
            phase = (
                "source_readiness"
                if attempt.module_id == "CP-0"
                else "earnings_delta"
                if attempt.module_id == "CP-1B"
                else "source_context"
            )
            self._activate(next_attempt, phase)
        else:
            self._phase, self._outcome, self._binding = "failed", None, None

    def submit_review(self, payload: str) -> ReviewOutcome:
        with self._locked():
            self._current()
            if self._binding is None or type(payload) is not str:
                raise OwnerError("not_permitted")
            try:
                raw = payload.encode("utf-8")
            except UnicodeEncodeError:
                raise OwnerError("bad_arguments") from None
            if len(raw) > MAX_LINE:
                raise OwnerError("transport_limit")
            if _text_depth(payload) >= MAX_JSON_DEPTH:
                # Refused before any audit write: a payload that cannot be parsed
                # or ruled on must not leave an orphan record without an intent.
                raise OwnerError("bad_arguments")
            pending = _unresolved(self._store)
            if pending:
                intent = pending[0]
                if _hash(raw) != intent.binding.raw_payload_sha256:
                    raise OwnerError("identity_mismatch")
                bound = intent.binding
            else:
                intents = _records(self._store, "intents", SubmissionIntent)
                scoped = [
                    i
                    for i in intents
                    if i.binding.binding.ticket_id == self._binding.ticket_id
                    and i.binding.binding.step_id == self._binding.step_id
                ]
                if len(scoped) >= MAX_FOUNDATION:
                    raise OwnerError("transport_limit")
                bound, _ = _prepare_bound(self._store, self._binding, payload, self._owner_session)
                _retain(self._store, "bindings", bound)
                intent = SubmissionIntent(
                    index=len(intents) + 1,
                    binding=bound,
                    snapshot_before_sha256=self._binding.snapshot_sha256,
                )
                self._current()
                _retain(self._store, "intents", intent)
            outcome = _complete_intent(self._store, intent)
            self._advance(outcome, bound)
            errors = (
                ()
                if outcome.disposition == "valid"
                else tuple(
                    dict.fromkeys(
                        issue
                        if issue in _ERRORS
                        else "participation_incomplete"
                        if outcome.disposition == "refused"
                        else "validation_failed"
                        for issue in outcome.issues
                    )
                )
            )
            return ReviewOutcome(
                module_id=bound.binding.module_id,
                step_id=bound.binding.step_id,
                ticket_id=bound.binding.ticket_id,
                attempt=bound.binding.attempt,
                disposition=outcome.disposition,
                issue_count=len(outcome.issues),
                error_codes=errors,
                snapshot_sha256=self._current_sha256,
                next_phase=self._phase,
                stored_payload_sha256=bound.stored_payload_sha256,
            )

    def write_receipt(self, destination: Path) -> EarningsOwnerReceipt:
        with self._locked():
            snapshot = self._current()
            if self._phase != "complete" or self._outcome is None or _unresolved(self._store):
                raise OwnerError("not_permitted")
            fields = _transcript_fields(self._store)
            positive = self._outcome == "owner_settled"
            cp0 = _head_record(self._store, snapshot, "CP-0")
            cp1 = _head_record(self._store, snapshot, "CP-1") if positive else None
            cp1b = _head_record(self._store, snapshot, "CP-1B") if positive else None
            stage_hash = None
            if cp1b is not None:
                attempt = next(a for a in snapshot.attempts if a.ticket_id == cp1b.ticket_id)
                stage_hash = attempt.steps[0].output_sha256
            receipt = EarningsOwnerReceipt(
                run=snapshot.run,
                pack_sha256=snapshot.pack_sha256,
                owner_snapshot_sha256=snapshot.content_hash(),
                case_id=self._setup_record.case_id,
                pins=self._setup_record.pins,
                participant=self._setup_record.participant,
                transport=self._setup_record.transport,
                outcome=self._outcome,
                cp0=cp0,
                cp1=cp1,
                cp1b=cp1b,
                cp1b_stage_sha256=stage_hash,
                **fields,
                audit_inventory=_inventory(self._store),
                publication_files=(),
            )
            if len(receipt.model_dump_json().encode()) > MAX_RECEIPT:
                raise OwnerError("transport_limit")
            _verify_owner(self._store, receipt, sealed=False)
            self._current()
            raw = receipt.model_dump_json().encode()
            root = self._store.directory / "earnings-owner-audit"
            # `owner-receipt.sha256` is the only commit point. A `owner-receipt.json` left
            # without it by a crash is uncommitted: the newly verified receipt replaces it,
            # and so does a destination holding exactly those uncommitted bytes.
            pending = root / "owner-receipt.json"
            uncommitted = pending.read_bytes() if pending.exists() else None
            if destination.exists():
                exported = destination.read_bytes()
                if exported != raw and (
                    exported != uncommitted or not _earlier_receipt(exported, receipt)
                ):
                    raise OwnerError("identity_mismatch")
                if exported != raw:
                    destination.unlink()
            pending.unlink(missing_ok=True)
            _put(root / "owner-receipt.json", raw)
            _put(destination, raw)
            self._current()
            _put(root / "owner-receipt.sha256", receipt.content_hash().encode("ascii"))
            self._current()
            self._sealed = True
            return receipt


_Operation = Literal["state", "invoke", "read_inputs", "submit_review", "close", "invalid"]


def _classify_frame(raw: bytes) -> tuple[_Operation, dict[str, Any] | None, str | None]:
    if not raw or len(raw) > MAX_LINE + 1:
        raise OwnerError("identity_mismatch")
    if len(raw) == MAX_LINE + 1:
        return "invalid", None, "transport_limit"
    if not raw.endswith(b"\n"):
        return "invalid", None, "bad_arguments"

    def nonfinite(_value: str) -> None:
        raise ValueError("nonfinite JSON")

    try:
        value = json.loads(raw.decode("utf-8", errors="strict"), parse_constant=nonfinite)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return "invalid", None, "bad_arguments"
    if type(value) is not dict or type(value.get("op")) is not str:
        return "invalid", None, "bad_arguments"
    operation = value["op"]
    keys = {
        "state": {"op"},
        "invoke": {"op", "tool", "arguments"},
        "read_inputs": {"op"},
        "submit_review": {"op", "payload"},
        "close": {"op"},
    }
    if operation not in keys:
        return "invalid", None, "not_permitted"
    if set(value) != keys[operation]:
        return "invalid", None, "bad_arguments"
    if operation == "invoke" and (
        type(value["tool"]) is not str or type(value["arguments"]) is not dict
    ):
        return "invalid", None, "bad_arguments"
    if operation == "submit_review" and type(value["payload"]) is not str:
        return "invalid", None, "bad_arguments"
    try:
        _json_copy(value)
    except OwnerError:
        return "invalid", None, "bad_arguments"
    return cast(_Operation, operation), value, None


def _write_reply(writer: TextIO, value: JsonObject) -> None:
    raw = (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8", errors="strict")
    written = writer.buffer.write(raw)
    if type(written) is not int or written != len(raw):
        raise OSError("Incomplete binary transport reply")
    writer.buffer.flush()


def serve_json_lines(
    workflow: EarningsWorkflow, reader: TextIO, writer: TextIO, *, destination: Path
) -> None:
    """Capture exact bounded raw frames before dispatch; use buffers exclusively."""
    if not isinstance(reader, io.TextIOWrapper) or not isinstance(writer, io.TextIOWrapper):
        raise OwnerError("bad_arguments")
    try:
        if (
            reader.closed
            or writer.closed
            or reader.buffer.closed
            or writer.buffer.closed
            or not reader.buffer.readable()
            or not writer.buffer.writable()
        ):
            raise OwnerError("bad_arguments")
    except (AttributeError, ValueError):
        raise OwnerError("bad_arguments") from None
    if workflow._setup_record.transport != "bounded-json-lines/1":
        raise OwnerError("not_permitted")
    if not workflow._dispatcher.acquire(blocking=False):
        raise OwnerError("not_permitted")
    try:
        while True:
            with workflow._locked():
                workflow._current()
                messages = _records(workflow._store, "transport-messages", TransportMessage)
                exhausted = len(messages) >= MAX_MESSAGES
            if exhausted:
                _write_reply(writer, {"status": "refused", "error_code": "transport_limit"})
                return
            raw = reader.buffer.readline(MAX_LINE + 1)
            if not raw:
                return
            if type(raw) is not bytes:
                raise TypeError("Binary transport reader did not return bytes")
            with workflow._locked():
                workflow._current()
                request_hash = _payload(workflow._store, raw)
                operation, request, error = _classify_frame(raw)
                messages = _records(workflow._store, "transport-messages", TransportMessage)
                if len(messages) >= MAX_MESSAGES:
                    raise OwnerError("transport_limit")
                message = TransportMessage(
                    index=len(messages) + 1, operation=operation, request_sha256=request_hash
                )
                _retain(workflow._store, "transport-messages", message)
            closed = False
            if error is not None:
                reply: JsonObject = {"status": "refused", "error_code": error}
            else:
                if request is None:
                    raise OwnerError("internal_error")
                try:
                    if operation == "state":
                        result = workflow.state().model_dump(mode="json")
                    elif operation == "invoke":
                        result = workflow.invoke(request["tool"], request["arguments"])
                    elif operation == "read_inputs":
                        result = workflow.read_inputs().model_dump(mode="json")
                    elif operation == "submit_review":
                        result = workflow.submit_review(request["payload"]).model_dump(mode="json")
                    elif operation == "close":
                        receipt = workflow.write_receipt(destination)
                        result = OwnerClose(
                            outcome=receipt.outcome,
                            owner_receipt_sha256=receipt.content_hash(),
                            owner_snapshot_sha256=receipt.owner_snapshot_sha256,
                        ).model_dump(mode="json")
                        closed = True
                    else:
                        raise OwnerError("not_permitted")
                    reply = {"status": "ok", "result": result}
                except OwnerError as refused:
                    reply = {"status": "refused", "error_code": refused.code}
            _write_reply(writer, reply)
            if closed or len(raw) == MAX_LINE + 1 or not raw.endswith(b"\n"):
                return
    finally:
        workflow._dispatcher.release()
