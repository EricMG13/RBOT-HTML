"""CP-1B owner checkpoint: foundation step inputs (projections, prefill, source coverage), the
CP-1 producer, and the owner's grant, pages, session proof and participation.

Moved unchanged from `earnings_workflow`, which re-exports every name.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError

from deploy_vii.contracts import Fact, Module, ModuleView
from deploy_vii.cp1_quality import cp1_quality_inputs
from deploy_vii.cp1_workflow import (
    CP1_PROMOTION,
    PROMOTED,
    CP1Handoff,
    FinancialStage,
    FinancialSubmission,
    cp1_registers,
    promote_cp1,
    validate_cp1_stage,
)
from deploy_vii.downstream_readiness import DownstreamInputs
from deploy_vii.execution import Attempt, Execution, ExecutionSnapshot, clipped
from deploy_vii.live.context import narrative_evidence, readiness_inputs
from deploy_vii.live.schema import normalise
from deploy_vii.live.submission import PREFILLED, STEPS, known_bindings, prefill
from deploy_vii.live.tools import ToolRules
from deploy_vii.preparation import PreparedPack
from deploy_vii.quality import QualityReview, assess_quality
from deploy_vii.readiness import citation_issues
from deploy_vii.source_context import SourceContextReview
from deploy_workflow.context import ContextRefused, context_facts
from deploy_workflow.earnings import EarningsDeltaReport, build_earnings_delta_in
from deploy_workflow.earnings_workflow_contracts import (
    _PROJECTED,
    _SOURCE_PHASES,
    EarningsParticipation,
    OwnerAccessRead,
    OwnerBinding,
    OwnerError,
    OwnerHeadRecord,
    OwnerSession,
    OwnerToolCall,
)
from deploy_workflow.earnings_workflow_store import _canonical, _FrozenExecution, _hash, _historical
from deploy_workflow.financial_workflow import (
    FinancialBinding,
    FinancialCall,
    _missing_units,
    _quality_read,
    _statement_units,
)
from deploy_workflow.owners.period_basis import PeriodRefused, currency_basis
from deploy_workflow.statement_lines import LineTools, seen_tables
from deploy_workflow.tools.upstream import UpstreamTools
from deploy_workflow.workflow import SourceEvidence


def _projection(store: Execution, binding: FinancialBinding) -> tuple[str, str]:
    historical = _historical(store, binding)
    attempt = next(a for a in historical.read().attempts if a.ticket_id == binding.ticket_id)
    if binding.step_id == "quality":
        return _quality_read(cp1_registers(historical, attempt.ticket_id))
    if binding.step_id not in {"narrative", "readiness"}:
        raise OwnerError("not_permitted")
    for index, step in enumerate(attempt.steps, 1):
        validation = validate_cp1_stage(
            historical,
            historical.pack(),
            attempt.model_copy(update={"steps": attempt.steps[:index]}),
        )
        if validation.issues or not validation.retained_as(step):
            raise OwnerError("identity_mismatch")
    output = historical.step_output(attempt.steps[-1].output_sha256 or "")
    if binding.step_id == "narrative":
        stage = FinancialStage.model_validate_json(output)
        return stage.narrative_inputs.content_hash(), narrative_evidence(stage)
    downstream = DownstreamInputs.model_validate_json(output)
    return downstream.content_hash(), readiness_inputs(downstream)


def _filled(
    store: Execution, binding: FinancialBinding, payload: str
) -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if binding.step_id == "source_readiness":
        return payload, (), (), ()
    model = STEPS[binding.step_id].schema
    normal, resolved = normalise(model, payload)
    filled = prefill(
        model,
        normal,
        known_bindings(store, binding.ticket_id, binding.step_id),
        PREFILLED[binding.step_id],
    )
    return filled.payload, resolved, filled.paths, filled.kinds


def _column_periods(headers: tuple[str, ...], periods: Any) -> tuple[str, ...] | None:
    """Only explicit source headings select reported columns; never infer aliases."""
    for header in headers:
        cells = re.split(r"\s{2,}", header.strip())[1:]
        if not cells:
            continue
        found = []
        for cell in cells:
            quarter = re.fullmatch(r"Q([1-4]) (\d{4})", cell)
            annual = re.fullmatch(r"FY (\d{4})", cell)
            dated = re.fullmatch(r"(Opening|Q[1-4]|FY) (\d{4}-\d{2}-\d{2})", cell)
            matches = []
            for period in periods:
                if (
                    (
                        quarter
                        and period.period_type == "QUARTER"
                        and period.fiscal_quarter == int(quarter[1])
                        and re.findall(r"\d{4}", period.fiscal_year) == [quarter[2]]
                    )
                    or (
                        annual
                        and period.period_type == "FY"
                        and re.findall(r"\d{4}", period.fiscal_year) == [annual[1]]
                    )
                    or (
                        dated
                        and str(period.end_date) == dated[2]
                        and (
                            dated[1] == "Opening"
                            and period.period_type == "PERIOD_END"
                            or dated[1] == "FY"
                            and period.period_type == "FY"
                            or dated[1].startswith("Q")
                            and period.period_type == "QUARTER"
                            and period.fiscal_quarter == int(dated[1][1])
                        )
                    )
                ):
                    matches.append(period.period_id)
            if len(matches) != 1:
                break
            found.append(matches[0])
        if len(found) == len(cells) and len(set(found)) == len(found):
            return tuple(found)
    return None


def _source_issues(
    store: Execution,
    binding: FinancialBinding,
    payload: str,
    evidence: SourceEvidence,
    calls: tuple[FinancialCall, ...],
) -> tuple[str, ...]:
    if binding.step_id not in _SOURCE_PHASES:
        return ()
    context = None
    if binding.step_id == "financials":
        attempt = next(a for a in store.read().attempts if a.ticket_id == binding.ticket_id)
        context = SourceContextReview.model_validate_json(
            store.payload(attempt.steps[0].payload_sha256)
        )
    issues = list(
        ToolRules().issues(binding.step_id, payload, seen=evidence.seen(), context=context)
    )
    pack = store.pack()
    if context is None:
        required_reads = {("identity", "page:1")}
        financial = next(s for s in pack.sources if s.source_id == "financial")
        if financial.status == "ready":
            required_reads.add(("financial", "page:1"))
        elif not any(
            call.tool == "read_pages"
            and call.status == "refused"
            and call.error_code == "unavailable"
            and call.body is None
            and call.arguments.get("source_id") == "financial"
            and type(call.arguments.get("first_page")) is int
            and type(call.arguments.get("last_page")) is int
            and call.arguments["first_page"] <= 1 <= call.arguments["last_page"]
            for call in calls
        ):
            issues.append("Missing financial source requires its actual unavailable-read refusal")
        if not required_reads <= set(evidence.read):
            issues.append(
                "Current source epoch must read the required identity and financial pages"
            )
        return tuple(issues)
    financial_ids = tuple(s.source_id for s in context.sources if s.classification == "financial")
    required_reads = {
        (s.source_id, span.locator)
        for s in pack.sources
        if s.source_id in financial_ids and s.status == "ready"
        for span in s.spans
    }
    if not required_reads <= set(evidence.read):
        issues.append("Financials must read every supplied financial page in this epoch")
    units = [
        (s.source_id, locator)
        for s in pack.sources
        if s.source_id in financial_ids and s.status == "ready"
        for locator in _statement_units(s.spans)
    ]
    required = set(units)
    if not required:
        issues.append("No statement unit is located in the financial sources")
    elif not required <= set(evidence.extracted):
        missing = _missing_units(units, evidence.extracted)
        issues.append(clipped(("Financials must extract every located statement unit: ", *missing)))
    tables = seen_tables(LineTools(pack, sources=financial_ids), evidence.seen(), context)
    try:
        submission = FinancialSubmission.model_validate_json(payload)
    except ValidationError:
        return tuple(issues)
    measured = set()
    for table in tables:
        key = (table.source_id, table.locator)
        if key not in required:
            continue
        if table.lines:
            measured.add(key)
        for extracted in table.lines:
            caption = (extracted.caption or "").upper()
            statement = (
                "IS"
                if "INCOME" in caption or "OPERATIONS" in caption
                else "CFS"
                if "CASH FLOW" in caption
                else "BS"
                if "BALANCE SHEET" in caption
                else None
            )
            covered = False
            for book in submission.financial.books:
                columns = _column_periods(table.headers, book.periods)
                if columns is None or len(columns) != len(extracted.values):
                    continue
                if all(
                    any(
                        line.period_id == pid
                        and line.statement == statement
                        and " ".join(line.label.split()) == " ".join(extracted.label.split())
                        and line.value.amount == value
                        and any(
                            c.source_id == table.source_id
                            and c.locator == table.locator
                            and extracted.label in c.quote
                            for c in line.value.citations
                        )
                        for line in book.statement_lines
                    )
                    for pid, value in zip(columns, extracted.values, strict=True)
                ):
                    covered = True
                    break
            if not covered:
                issues.append(
                    f"Uncovered extracted statement line: {table.source_id} {table.locator} line {extracted.line_no}"
                )
    if measured != required:
        issues.append("Statement extraction is unmeasured; empty tables do not establish coverage")
    return tuple(issues)


def _cp1_candidate(store: Execution, snapshot: ExecutionSnapshot, attempt: Attempt) -> Module:
    if tuple(s.step_id for s in attempt.steps) != CP1_PROMOTION or any(
        s.status != "valid" for s in attempt.steps
    ):
        raise OwnerError("identity_mismatch")
    frozen = _FrozenExecution(store, snapshot)
    registers = cp1_registers(frozen, attempt.ticket_id)
    handoff = CP1Handoff.model_validate_json(
        frozen.step_output(attempt.steps[4].output_sha256 or "")
    )
    review = QualityReview.model_validate_json(frozen.payload(attempt.steps[4].payload_sha256))
    if handoff.registers_sha256 != registers.content_hash() or handoff.quality != assess_quality(
        cp1_quality_inputs(registers), review
    ):
        raise OwnerError("identity_mismatch")
    candidates: list[Module] = []

    class Probe(_FrozenExecution):
        def finish(self, ticket_id: str, payload: str, validator: Any, **kwargs: Any) -> Attempt:
            if ticket_id != attempt.ticket_id or kwargs.get("qualification") != PROMOTED:
                raise OwnerError("identity_mismatch")
            candidate = Module.model_validate_json(payload)
            if validator(candidate):
                raise OwnerError("identity_mismatch")
            candidates.append(candidate)
            return attempt

    pending = attempt.model_copy(update={"status": "pending"})
    historical = snapshot.model_copy(
        update={
            "attempts": tuple(
                pending if a.ticket_id == attempt.ticket_id else a for a in snapshot.attempts
            )
        }
    )
    promote_cp1(
        Probe(store, historical), attempt.ticket_id, frozen.payload(attempt.steps[4].payload_sha256)
    )
    if len(candidates) != 1:
        raise OwnerError("identity_mismatch")
    return candidates[0]


def _head_record(store: Execution, snapshot: ExecutionSnapshot, module_id: str) -> OwnerHeadRecord:
    heads = [h for h in snapshot.heads if h.module_id == module_id]
    if len(heads) != 1:
        raise OwnerError("identity_mismatch")
    head = heads[0]
    attempts = [
        a
        for a in snapshot.attempts
        if a.module_id == module_id and a.result_sha256 == head.result_sha256
    ]
    if len(attempts) != 1 or attempts[0].status != "finished" or attempts[0].payload_sha256 is None:
        raise OwnerError("identity_mismatch")
    attempt = attempts[0]
    candidate_sha256 = attempt.payload_sha256
    if candidate_sha256 is None:
        raise OwnerError("identity_mismatch")
    _FrozenExecution(store, snapshot).head_module(head)
    return OwnerHeadRecord(
        ticket_id=attempt.ticket_id,
        attempt=attempt.number,
        head=head,
        candidate_sha256=candidate_sha256,
        step_sha256s=tuple(s.content_hash() for s in attempt.steps),
    )


def _full_cp1(store: Execution, binding: OwnerBinding) -> tuple[Module, ModuleView]:
    historical = _historical(store, binding)
    snapshot = historical.read()
    record = _head_record(store, snapshot, "CP-1")
    producer = historical.head_module(record.head)
    run = snapshot.run
    if (
        record.head.qualification != PROMOTED
        or producer.status not in {"accepted", "restricted"}
        or (producer.run_id, producer.issuer_id, producer.as_of, producer.method_version)
        != (run.run_id, run.issuer_id, run.as_of, run.method_version)
        or producer.content_hash() != record.head.result_sha256
        or not any(
            i.input_id == "CP-1"
            and i.sha256 == producer.content_hash()
            and i.status == producer.status
            for i in binding.inputs
        )
    ):
        raise OwnerError("identity_mismatch")
    view = ModuleView(
        module_id="CP-1",
        title="Financials",
        aliases=(),
        status=producer.status,
        artifact_sha256=producer.content_hash(),
        facts=producer.facts,
        tables=producer.tables,
        claims=producer.claims,
        limitations=(*producer.limitations, *producer.inherited_limitations),
    )
    return producer, view


def _run_currency(pack: PreparedPack, view: ModuleView) -> str:
    """The run's reporting currency for `build_earnings_delta_in`: `USD` for a pack with no run
    context, else the context's, checked against the CP-1 T4.14 register (`currency_basis`). A
    refused context or register is the delta core's `incompatible_dimensions`."""
    try:
        return currency_basis(context_facts(pack), view.facts).currency
    except (PeriodRefused, ContextRefused) as error:
        raise ValueError("incompatible_dimensions") from error


def _grant(
    store: Execution, binding: OwnerBinding, prior: str, current: str
) -> tuple[dict[str, Any], EarningsDeltaReport, Module]:
    producer, view = _full_cp1(store, binding)
    report = build_earnings_delta_in(
        view, prior, current, currency=_run_currency(store.pack(), view)
    )
    chosen = {f.fact_id: f for f in producer.facts if f.table_id == "T4.14"}
    metrics: dict[str, dict[str, Fact]] = {}
    for fact in producer.facts:
        if fact.table_id == "T4.10":
            metrics.setdefault(fact.row_id, {})[fact.field] = fact
    for point in report.points:
        rows = [
            row
            for row in metrics.values()
            if row.get("field_1") is not None
            and row["field_1"].status == "known"
            and row["field_1"].text == point.measure_id
        ]
        if len(rows) != 1 or "field_0" not in rows[0]:
            raise OwnerError("identity_mismatch")
        row = rows[0]
        selected = [row["field_0"], row["field_1"], row[report.current_basis_id]]
        if report.prior_basis_id is not None:
            selected.append(row[report.prior_basis_id])
        chosen.update((f.fact_id, f) for f in selected)
    coordinates = [
        {"fact_id": f.fact_id, "table_id": f.table_id, "row_id": f.row_id, "field": f.field}
        for f in sorted(chosen.values(), key=lambda f: (f.table_id, f.row_id, f.field, f.fact_id))
    ]
    grant = {
        "schema_version": "cp1b-upstream-grant/2",
        "consumer_module_id": "CP-1B",
        "step_id": "earnings_delta",
        "producers": [
            {
                "module_id": "CP-1",
                "sha256": producer.content_hash(),
                "coordinates": coordinates,
                "projected_fields": list(_PROJECTED),
            }
        ],
        "raw_source_ids": [],
    }
    return grant, report, producer


def _manifest(binding: OwnerBinding, grant: dict[str, Any], producer: Module) -> dict[str, Any]:
    coordinates = grant["producers"][0]["coordinates"]
    periods = [c for c in coordinates if c["table_id"] == "T4.14"]
    header = {
        "schema_version": "cp1b-access-manifest/1",
        "consumer": {"module_id": "CP-1B", "step_id": "earnings_delta"},
        "producer": {
            "module_id": "CP-1",
            "sha256": producer.content_hash(),
            "status": producer.status,
        },
        "snapshot_sha256": binding.snapshot_sha256,
        "ticket_id": binding.ticket_id,
        "attempt": binding.attempt,
        "grant_sha256": _hash(_canonical(grant).encode()),
        "period_index": {
            "table_id": "T4.14",
            "authorized_complete": True,
            "row_count": len({c["row_id"] for c in periods}),
            "coordinate_count": len(periods),
        },
        "coordinate_count": len(coordinates),
        "projected_fields": list(_PROJECTED),
        "max_page_entries": 20,
        "max_body_bytes": 8192,
    }
    return {
        **header,
        "manifest_sha256": _hash(
            _canonical({"header": header, "coordinates": coordinates}).encode()
        ),
    }


def _safe_fact(fact: Fact) -> dict[str, Any]:
    data = fact.model_dump(mode="json", include=set(_PROJECTED) - {"citation_handles"})
    data["citation_handles"] = [
        {"source_id": c.source_id, "source_sha256": c.source_sha256, "locator": c.locator}
        for c in fact.citations
    ]
    return {key: data[key] for key in _PROJECTED}


def _catalog(grant: dict[str, Any], producer: Module) -> list[dict[str, Any]]:
    facts = {f.fact_id: f for f in producer.facts}
    result = []
    for coordinate in grant["producers"][0]["coordinates"]:
        fact = facts.get(coordinate["fact_id"])
        if fact is None or any(getattr(fact, k) != v for k, v in coordinate.items()):
            raise OwnerError("identity_mismatch")
        result.append(_safe_fact(fact))
    return result


def _page(
    header: dict[str, Any],
    entries: list[dict[str, Any]],
    offset: int,
    count: int,
    token: str | None,
    projection: bool,
) -> dict[str, Any]:
    return {
        "producer": header["producer"],
        **({"projection": "granted_fact_projection"} if projection else {}),
        "grant_sha256": header["grant_sha256"],
        "manifest_sha256": header["manifest_sha256"],
        "coordinate_count": len(entries),
        "offset": offset,
        "entries": entries[offset : offset + count],
        "next_cursor": token,
        "complete": offset + count == len(entries),
    }


def _verify_pages(
    header: dict[str, Any],
    entries: list[dict[str, Any]],
    calls: tuple[OwnerToolCall, ...],
    projection: bool,
) -> tuple[str, ...]:
    """Authenticate issued cursor graphs without replaying private nonce tokens."""
    tool = "read_access_projection" if projection else "read_access_manifest"
    prefix = "projection-cursor:" if projection else "access-cursor:"
    issued: dict[str, int] = {}
    replay: dict[tuple[str | None, int], dict[str, Any]] = {}
    paths: dict[str | None, tuple[str, ...]] = {None: ()}
    complete: tuple[str, ...] = ()
    for call in calls:
        receipt = call.receipt
        if receipt.tool != tool or receipt.status != "ok":
            continue
        args, body = receipt.arguments, receipt.body
        if (
            set(args)
            != {"producer_module_id", "producer_sha256", "manifest_sha256", "cursor", "limit"}
            or args["producer_module_id"] != "CP-1"
            or args["producer_sha256"] != header["producer"]["sha256"]
            or args["manifest_sha256"] != header["manifest_sha256"]
            or type(args["limit"]) is not int
            or not 1 <= args["limit"] <= 20
            or body is None
        ):
            raise OwnerError("identity_mismatch")
        cursor = args["cursor"]
        if cursor is None:
            offset = 0
        elif not isinstance(cursor, str) or cursor not in issued:
            raise OwnerError("identity_mismatch")
        else:
            offset = issued[cursor]
        token = body.get("next_cursor")
        if token is not None and (
            not isinstance(token, str)
            or re.fullmatch(re.escape(prefix) + "[0-9a-f]{64}", token) is None
        ):
            raise OwnerError("identity_mismatch")
        best = 0
        for count in range(1, min(args["limit"], len(entries) - offset) + 1):
            marker = None if offset + count == len(entries) else prefix + "0" * 64
            if (
                len(_canonical(_page(header, entries, offset, count, marker, projection)).encode())
                <= 8192
            ):
                best = count
        if not best or body != _page(header, entries, offset, best, token, projection):
            raise OwnerError("identity_mismatch")
        end = offset + best
        if (token is None) != (end == len(entries)):
            raise OwnerError("identity_mismatch")
        key = (cursor, args["limit"])
        if key in replay and replay[key] != body:
            raise OwnerError("identity_mismatch")
        replay[key] = body
        if token is not None:
            if token in issued and issued[token] != end:
                raise OwnerError("identity_mismatch")
            issued[token] = end
        if cursor in paths:
            path = (*paths[cursor], receipt.call_id)
            if token is not None:
                paths[token] = path
            if end == len(entries):
                complete = path
    return complete


def _owner_session_proof(
    store: Execution,
    session: OwnerSession,
    calls: tuple[OwnerToolCall, ...],
    prior: str,
    current: str,
) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    grant, _, producer = _grant(store, session.binding, prior, current)
    header = _manifest(session.binding, grant, producer)
    if session.normalized_grant_json != _canonical(
        grant
    ) or session.access_manifest_json != _canonical(header):
        raise OwnerError("identity_mismatch")
    if [c.receipt.sequence for c in calls] != list(range(1, len(calls) + 1)):
        raise OwnerError("identity_mismatch")
    for call in calls:
        receipt = call.receipt
        if (
            call.session_id != session.session_id
            or receipt.binding != session.binding
            or receipt.source_evidence != SourceEvidence()
            or receipt.status != "ok"
            and receipt.body is not None
        ):
            raise OwnerError("identity_mismatch")
    manifest_pages = _verify_pages(header, grant["producers"][0]["coordinates"], calls, False)
    projection_pages = _verify_pages(header, _catalog(grant, producer), calls, True)
    permitted = {c["fact_id"] for c in grant["producers"][0]["coordinates"]}
    facts = {f.fact_id: f for f in producer.facts}
    verified: set[str] = set()
    citation_calls = []
    historical = _historical(store, session.binding)
    for call in calls:
        receipt = call.receipt
        if receipt.status != "ok":
            continue
        if receipt.tool in {"read_access_manifest", "read_access_projection"}:
            continue
        args = receipt.arguments
        if (
            args.get("producer_module_id") != "CP-1"
            or args.get("producer_sha256") != producer.content_hash()
        ):
            raise OwnerError("identity_mismatch")
        if receipt.tool == "verify_upstream":
            ids = args.get("fact_ids")
            if (
                set(args) != {"producer_module_id", "producer_sha256", "kind", "fact_ids"}
                or args.get("kind") != "citations"
                or not isinstance(ids, list)
                or not 1 <= len(ids) <= 20
                or any(not isinstance(fid, str) for fid in ids)
                or len(set(ids)) != len(ids)
                or not set(ids) <= permitted
            ):
                raise OwnerError("identity_mismatch")
            fact_ids = tuple(fid for fid in ids if isinstance(fid, str))
            issues = [
                {"code": "fact_citation", "fact_ids": [fid]}
                for fid in fact_ids
                for _ in citation_issues(facts[fid].citations, historical.pack().sources)
            ]
            expected = {
                "producer": header["producer"],
                "grant_sha256": header["grant_sha256"],
                "manifest_sha256": header["manifest_sha256"],
                "kind": "citations",
                "verdict": "invalid" if issues else "valid",
                "issue_count": len(issues),
                "issues": issues,
            }
            if receipt.body != expected or len(_canonical(expected).encode()) > 8192:
                raise OwnerError("identity_mismatch")
            if not issues:
                verified.update(fact_ids)
                citation_calls.append(receipt.call_id)
        elif receipt.tool == "lookup_upstream":
            # Optional legacy lookups are authenticated through the unchanged public
            # tool on a read-only historical session; no opaque cursor is replayed.
            replay = UpstreamTools.from_execution(
                historical, session.binding.ticket_id, "earnings_delta", grants=grant
            ).invoke(receipt.tool, dict(args))
            if (
                replay["status"] != receipt.status
                or replay["body"] != receipt.body
                or replay["error_code"] != receipt.error_code
            ):
                raise OwnerError("identity_mismatch")
        else:
            raise OwnerError("identity_mismatch")
    if verified != permitted:
        citation_calls = []
    return header, manifest_pages, projection_pages, tuple(citation_calls)


def _participation(
    store: Execution,
    binding: OwnerBinding,
    session: OwnerSession,
    reads: tuple[OwnerAccessRead, ...],
    calls: tuple[OwnerToolCall, ...],
    prior: str,
    current: str,
) -> EarningsParticipation:
    ticket_calls = tuple(c for c in calls if c.receipt.binding.ticket_id == binding.ticket_id)
    selected = tuple(c for c in ticket_calls if c.session_id == session.session_id)
    header, manifest, projection, citations = _owner_session_proof(
        store, session, selected, prior, current
    )
    access = tuple(
        r
        for r in reads
        if r.session_id == session.session_id
        and r.binding == binding
        and r.access_manifest_json == session.access_manifest_json
    )
    if session.binding != binding or not access or not manifest or not projection or not citations:
        raise OwnerError("participation_incomplete")
    by_id = {c.receipt.call_id: c.receipt for c in selected}

    def supplies(cid: str, table: str) -> bool:
        body = by_id[cid].body
        entries = body.get("entries") if body is not None else None
        if not isinstance(entries, list):
            raise OwnerError("identity_mismatch")
        return any(isinstance(e, dict) and e.get("table_id") == table for e in entries)

    period_pages = tuple(cid for cid in projection if supplies(cid, "T4.14"))
    metric_pages = tuple(cid for cid in projection if supplies(cid, "T4.10"))
    return EarningsParticipation(
        binding=binding,
        session_id=session.session_id,
        grant_sha256=header["grant_sha256"],
        manifest_sha256=header["manifest_sha256"],
        access_read_sha256=access[-1].content_hash(),
        call_ids=tuple(c.receipt.call_id for c in ticket_calls),
        successful_call_ids=tuple(
            c.receipt.call_id for c in ticket_calls if c.receipt.status == "ok"
        ),
        manifest_call_ids=manifest,
        period_lookup_call_ids=period_pages,
        metric_lookup_call_ids=metric_pages,
        citation_call_ids=citations,
    )
