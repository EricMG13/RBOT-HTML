"""CP-1B earnings delta composition (`compose_delta`): period wording, limitations, operand
lineage and register claims. `owners/cp1b.py` reaches it through `earnings_workflow`.

Moved unchanged from `earnings_workflow`, which re-exports every name.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from deploy_vii.bindings.cp1b import cp1b_layouts
from deploy_vii.contracts import (
    Citation,
    Claim,
    Fact,
    Input,
    Module,
    ReportTable,
    Run,
    TableColumn,
    TableRow,
)
from deploy_vii.execution import Attempt
from deploy_vii.prose import tokenize
from deploy_vii.report_view import scale_label
from deploy_workflow.earnings import EarningsDeltaReport
from deploy_workflow.earnings_workflow_contracts import (
    CitationHandle,
    EarningsDeltaReview,
    EarningsParticipation,
    FactReference,
    OperandLineage,
    OperandReference,
    OwnerCaseId,
    OwnerError,
)
from deploy_workflow.earnings_workflow_store import _canonical, _parse

_DEFAULT_UNIT = "US$ m"


def _report_currency(report: EarningsDeltaReport) -> str:
    """The one currency of the report's money points (`build_earnings_delta_in` checked every money
    fact carries the run's); a report that names none or several fails closed."""
    codes = {p.currency for p in report.points if p.currency is not None}
    if len(codes) != 1 or not re.fullmatch(r"[A-Z]{3}", next(iter(codes))):
        raise OwnerError("identity_mismatch")
    return next(iter(codes))


def _money_unit(currency: str) -> str:
    """The money unit the report view states for `currency` (`US$ m`, `EUR m`), from the view's
    own `scale_label`, which the CP-1B layout check compares the row labels with."""
    unit = scale_label("MILLIONS", currency)
    if unit is None:
        raise OwnerError("identity_mismatch")
    return unit


def _currency_evidence(currency: str) -> dict[str, str]:
    """The currency of the figures the evidence operands select. A USD report keeps its pinned
    bytes (the operands' `fact_sha256` already covers it); any other currency is stated."""
    return {} if currency == "USD" else {"currency": currency}


def _numeric_rows(
    unit: str,
) -> tuple[tuple[str, str, tuple[str, ...], tuple[tuple[str, str], ...]], ...]:
    """The two numeric tables, their money labels stated in `unit` (`US$ m`, `EUR m`): the table
    ids, titles, columns and labelled rows of the CP-1B layout the report view checks
    (`deploy_vii.bindings.cp1b.cp1b_layouts`), so the two cannot drift."""
    return tuple(
        (layout.table_id, layout.title, layout.fields, layout.rows)
        for layout in cp1b_layouts(unit)[:2]
    )


_ASSESSMENT_ROWS = (
    ("variance.summary", "Numerical comparison"),
    ("drivers", "Driver evidence"),
    ("guidance", "Guidance evidence"),
    ("comparative.prior-year", "Prior-year comparison"),
    ("comparative.trailing-leverage", "Leverage comparison"),
    ("evidence.inputs", "Selected input evidence"),
    ("scope.limitations", "Scope limitations"),
)


def _common_limits(currency: str) -> tuple[str, str, str]:
    return (
        f"Unaudited consolidated IFRS financials in {currency} millions; borrower, guarantor and restricted-group perimeters are not established.",
        "No causal-driver evidence is supplied by the selected authorized CP1 inputs.",
        "No management-guidance or operational-KPI evidence is supplied by the selected authorized CP1 inputs.",
    )


_COMMON_LIMITS = _common_limits("USD")
_QUARTER_ID = re.compile(r"q([1-4])-([0-9]{4})")
_FY_ID = re.compile(r"fy-([0-9]{4})")
_UNSUPPORTED = "unsupported_pair"
_FOUR_QUARTERS_REQUIRED = re.compile(r"Four complete contiguous quarters\b[^;]*\brequired\b")
_FOUR_QUARTERS = "Four complete contiguous quarters"
_LEVERAGE_MEASURES = ("total_leverage_reported", "net_leverage_reported")
_CHECKPOINT_LIMIT = "Owner checkpoint only; complete CP5 consumption and selected-run/native rendering are not accepted by this receipt."


def _case_parameters(run: Run) -> tuple[OwnerCaseId, str, str]:
    selected: dict[str, tuple[OwnerCaseId, str, str]] = {
        "slice-cp1b-flat-v1": ("E-QOQ-FLAT", "q3-2025", "q4-2025"),
        "slice-cp1b-no-yoy-v1": ("E-NO-YOY", "fy-2024", "fy-2025"),
        "slice-cp1b-missing-source-v1": ("E-REQUIRED-CP1-MISSING", "q3-2025", "q4-2025"),
    }
    if (
        run.run_id not in selected
        or run.requested_modules != ("CP-1B", "CP-5")
        or run.pathway != "earnings_update"
    ):
        raise OwnerError("identity_mismatch")
    return selected[run.run_id]


def _owner_perimeter_limit(currency: str) -> str:
    return (
        f"Consolidated IFRS financials in {currency} millions; audit status, borrower, guarantor "
        "and restricted-group perimeters are not established."
    )


_OWNER_PERIMETER_LIMIT = _owner_perimeter_limit("USD")


def _period_word(pid: str) -> str:
    """The period word of a period id: `q3-2025` is `Q3`, `fy-2024` is `FY2024`. An id of any other
    shape has no word the prose can state, so it fails closed."""
    quarter, year = _QUARTER_ID.fullmatch(pid), _FY_ID.fullmatch(pid)
    if quarter is not None:
        return f"Q{quarter[1]}"
    if year is not None:
        return f"FY{year[1]}"
    raise OwnerError("identity_mismatch")


def _period_year(pid: str) -> int:
    match = _QUARTER_ID.fullmatch(pid) or _FY_ID.fullmatch(pid)
    if match is None:
        raise OwnerError("identity_mismatch")
    return int(match[match.lastindex or 1])


def _period_noun(pid: str) -> str:
    return "quarter" if _QUARTER_ID.fullmatch(pid) else "year"


def _prior_year_series(report: EarningsDeltaReport) -> str:
    year = _period_year(report.current_period_id) - 1
    return f"FY{year} annual income statement or prior-year quarterly series is supplied."


def _opening_word(report: EarningsDeltaReport) -> str:
    """`Opening-2024` for a missing prior of FY2024; empty when the pair has a prior."""
    if report.prior_basis_id is not None:
        return ""
    return f"Opening-{_period_year(report.prior_period_id)}"


def _leverage_reasons(report: EarningsDeltaReport) -> tuple[str, ...]:
    """The reasons on the leverage points of a pair that has a prior; every prior leverage value
    must be missing, or the "unavailable" prose is false and the pair fails closed."""
    points = [p for p in report.points if p.measure_id in _LEVERAGE_MEASURES]
    if any(p.prior_status != "missing" for p in points):
        raise ValueError(_UNSUPPORTED)
    return tuple(dict.fromkeys(p.reason for p in points if p.reason))


def _standalone(reasons: tuple[str, ...]) -> bool:
    return bool(reasons) and all(_FOUR_QUARTERS_REQUIRED.search(r) for r in reasons)


def _leverage_gap(report: EarningsDeltaReport) -> str:
    """The flat pair's prior trailing-leverage gap, from the leverage points' own `reason`."""
    prior, current = (_period_word(report.prior_period_id), _period_word(report.current_period_id))
    reasons = _leverage_reasons(report)
    if _standalone(reasons):
        return (
            f"{_FOUR_QUARTERS} are unavailable for {prior} trailing leverage; "
            f"current {current} standalone leverage remains valid."
        )
    why = f" ({'; '.join(reasons)})" if reasons else ""
    return f"{prior} trailing leverage comparison is unavailable{why}; current {current} leverage remains valid."


def _leverage_limit(report: EarningsDeltaReport) -> str:
    prior, current = (_period_word(report.prior_period_id), _period_word(report.current_period_id))
    if report.prior_basis_id is None:
        return (
            f"Requested {prior} comparison basis is absent; current {current} values remain known. "
            f"{_opening_word(report)} balance data is not a substituted income comparator."
        )
    standalone = " standalone" if _standalone(_leverage_reasons(report)) else ""
    return (
        f"{prior} trailing leverage comparison is unavailable; "
        f"current {current}{standalone} leverage remains valid."
    )


def _own_limits(report: EarningsDeltaReport, *, owner: bool = False) -> tuple[str, ...]:
    """CP-1B's own limitations, written from the report's own periods. `owner` is the owner walk
    (`owners/cp1b`): no checkpoint line (it names the receipt path) and a perimeter line that claims
    only what the delta core checks (the dimensions), not that the statements are unaudited, which
    no owner-path check establishes."""
    gap = report.prior_basis_id is None
    currency = _report_currency(report)
    common = _common_limits(currency)
    return (
        *((_owner_perimeter_limit(currency), *common[1:]) if owner else common),
        f"No {_prior_year_series(report)}",
        "No year-on-year earnings comparison or broader nonzero earnings qualification."
        if gap
        else "Bounded flat sequential earnings comparison only; no broader nonzero earnings qualification.",
        *(() if owner else (_CHECKPOINT_LIMIT,)),
        _leverage_limit(report),
    )


def _reference(producer_sha256: str, fact: Fact) -> FactReference:
    return FactReference(
        producer_module_id="CP-1",
        producer_sha256=producer_sha256,
        fact_id=fact.fact_id,
        table_id=fact.table_id,
        row_id=fact.row_id,
        field=fact.field,
    )


def _operands(producer: Module, report: EarningsDeltaReport) -> tuple[OperandLineage, ...]:
    facts = {f.fact_id: f for f in producer.facts}
    producer_sha256 = producer.content_hash()

    def operand(fid: str, pid: str, basis: str) -> OperandReference:
        fact = facts[fid]
        if fact.period is None or fact.basis is None:
            raise OwnerError("identity_mismatch")
        return OperandReference(
            fact=_reference(producer_sha256, fact),
            period_id=pid,
            basis_id=basis,
            source_period=fact.period,
            source_basis=fact.basis,
            fact_sha256=fact.content_hash(),
            citation_handles=tuple(
                CitationHandle(
                    source_id=c.source_id, source_sha256=c.source_sha256, locator=c.locator
                )
                for c in fact.citations
            ),
        )

    return tuple(
        OperandLineage(
            measure_id=p.measure_id,
            prior=operand(p.prior_fact_id, report.prior_period_id, report.prior_basis_id)
            if p.prior_fact_id is not None and report.prior_basis_id is not None
            else None,
            current=operand(p.current_fact_id, report.current_period_id, report.current_basis_id),
            companions=tuple(
                _reference(producer_sha256, facts[fid]) for fid in p.companion_fact_ids
            ),
        )
        for p in report.points
    )


def _citations(facts: tuple[Fact, ...]) -> tuple[Citation, ...]:
    return tuple(dict.fromkeys(c for f in facts for c in f.citations))


def _period_heading(producer: Module, pid: str, role: str, absent: bool) -> str:
    if absent:
        return f"Requested {pid} (not supplied)"
    rows: dict[str, dict[str, Fact]] = {}
    for fact in producer.facts:
        if fact.table_id == "T4.14":
            rows.setdefault(fact.row_id, {})[fact.field] = fact
    selected = [row for row in rows.values() if row["period_id"].text == pid]
    if len(selected) != 1:
        raise OwnerError("identity_mismatch")
    start = date.fromisoformat(selected[0]["start_date"].text or "")
    end = date.fromisoformat(selected[0]["end_date"].text or "")
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    label = f"{start.day} {months[start.month - 1]}–{end.day} {months[end.month - 1]} {end.year}"
    return f"{role.title()} {pid} ({label})"


def _compose(
    producer: Module,
    report: EarningsDeltaReport,
    operands: tuple[OperandLineage, ...],
    review: EarningsDeltaReview,
    participation: EarningsParticipation,
    attempt: Attempt,
    run: Run,
) -> Module:
    """The receipt path's candidate: the shared composer with the review and participation
    inputs and the checkpoint limitation."""
    return compose_delta(
        producer,
        report,
        operands,
        (
            Input(input_id="earnings-review", sha256=review.content_hash()),
            Input(input_id="earnings-participation", sha256=participation.content_hash()),
        ),
        _own_limits(report),
        attempt,
        run,
    )


def _register_rows(producer: Module) -> list[dict[str, str]]:
    """The T4.14 period rows of the head, as field -> text."""
    rows: dict[str, dict[str, str]] = {}
    for fact in producer.facts:
        if fact.table_id == "T4.14":
            rows.setdefault(fact.row_id, {})[fact.field] = fact.text or ""
    return list(rows.values())


def _row_of(rows: list[dict[str, str]], pid: str) -> dict[str, str] | None:
    return next((r for r in rows if r.get("period_id") == pid), None)


def _row_is(pid: str, row: dict[str, str]) -> bool:
    """Whether the T4.14 row bears out the period words of the id: kind, fiscal year, quarter."""
    quarter, year = _QUARTER_ID.fullmatch(pid), _FY_ID.fullmatch(pid)
    if quarter is not None:
        return (row.get("period_type"), row.get("fiscal_quarter"), row.get("fiscal_year")) == (
            "QUARTER",
            quarter[1],
            quarter[2],
        )
    return year is not None and (row.get("period_type"), row.get("fiscal_year")) == ("FY", year[1])


def _fiscal_year(row: dict[str, str]) -> int:
    text = row.get("fiscal_year", "")
    return int(text) if text.isascii() and text.isdigit() else -1


def _no_earlier_series(rows: list[dict[str, str]], year: int) -> bool:
    """No duration row (FY, quarter, LTM, YTD) of fiscal year `year` or earlier; a row whose
    fiscal year is unreadable cannot be shown to be later, so it counts against the claim."""
    return all(r.get("period_type") == "PERIOD_END" or _fiscal_year(r) > year for r in rows)


def _opening_matches(rows: list[dict[str, str]], year: int) -> bool:
    """Opening PERIOD_END rows, when the register has any, include one dated end of `year`. A
    register with none (the literal pinned one) keeps the pinned bytes: the claim stands on the
    prior id being the year before the current period."""
    opening = [
        r.get("end_date", "")[:4]
        for r in rows
        if r.get("period_type") == "PERIOD_END" and r.get("period_id", "").startswith("opening-")
    ]
    return not opening or str(year) in opening


def _require_flat_or_gap(report: EarningsDeltaReport) -> None:
    """The composer's "is flat" prose is true only of a pair whose every T1B.1 delta is a known
    zero, and every current value it calls known must be; any other report fails closed."""
    if any(p.current_status != "known" for p in report.points):
        raise ValueError(_UNSUPPORTED)
    if report.prior_basis_id is None:
        return
    earnings = {m for _, _, _, rows in _numeric_rows(_DEFAULT_UNIT)[:1] for m, _ in rows}
    if any(
        p.delta_status != "known" or p.delta != 0 for p in report.points if p.measure_id in earnings
    ):
        raise ValueError(_UNSUPPORTED)


def _require_register_claims(producer: Module, report: EarningsDeltaReport) -> None:
    """Every claim the prose makes is read from the head's T4.14 rows or the composer refuses
    with `unsupported_pair` (no key exists for a pair it cannot state truthfully): the period words
    match the rows, a pair with a prior is adjacent ("sequential"), no FY or earlier duration row
    contradicts "No FY{y} annual income statement or prior-year quarterly series", and a
    missing-prior pair is the FY the year before the current period, with its opening row."""
    _require_flat_or_gap(report)
    rows = _register_rows(producer)
    _period_word(report.prior_period_id)
    current = _row_of(rows, report.current_period_id)
    if current is None or not _row_is(report.current_period_id, current):
        raise ValueError(_UNSUPPORTED)
    year = int(current["fiscal_year"]) - 1
    if not _no_earlier_series(rows, year):
        raise ValueError(_UNSUPPORTED)
    if report.prior_basis_id is None:
        gap = _FY_ID.fullmatch(report.prior_period_id)
        if gap is None or int(gap[1]) != year or not _opening_matches(rows, year):
            raise ValueError(_UNSUPPORTED)
        return
    prior = _row_of(rows, report.prior_period_id)
    if prior is None or not _row_is(report.prior_period_id, prior):
        raise ValueError(_UNSUPPORTED)
    gap_days = date.fromisoformat(current["start_date"]) - date.fromisoformat(prior["end_date"])
    if gap_days != timedelta(days=1):
        raise ValueError(_UNSUPPORTED)


def compose_delta(
    producer: Module,
    report: EarningsDeltaReport,
    operands: tuple[OperandLineage, ...],
    tail: tuple[Input, ...],
    own_limits: tuple[str, ...],
    attempt: Attempt,
    run: Run,
) -> Module:
    """The CP-1B candidate over a CP-1 head and its delta report, for both paths. `tail` is
    what follows the attempt inputs (the receipt path's review and participation, the owner
    walk's one `earnings-delta-submission`); `own_limits` is the module's own limitation list,
    so the checkpoint line belongs to the receipt path only."""
    gap = report.prior_basis_id is None
    _require_register_claims(producer, report)
    prior_word, current_word = (
        _period_word(report.prior_period_id),
        _period_word(report.current_period_id),
    )
    facts_by_id = {f.fact_id: f for f in producer.facts}
    points = {p.measure_id: p for p in report.points}
    lineage = {p.measure_id: p for p in operands}
    pair = f"{report.prior_period_id}->{report.current_period_id}"
    headings = {
        "prior": _period_heading(producer, report.prior_period_id, "prior", gap),
        "current": _period_heading(producer, report.current_period_id, "current", False),
        "delta": "Change (native unit; margin pp)",
        "growth": "Growth (%)",
    }
    opening = _opening_word(report)
    table_limit = (
        f"Missing selected {prior_word} comparison basis; current {current_word} values remain known; "
        f"{opening} balance data exists; this is not a claim that balance data is unavailable; "
        f"{opening} is not silently aliased to requested {prior_word} income basis; "
        "Whole-million monetary display; exact canonical values remain in facts/passports"
        if gap
        else "Whole-million monetary display; exact canonical values remain in facts/passports; "
        f"{_period_noun(report.current_period_id).title()} earnings use own-period values; "
        "leverage uses its selected trailing basis"
    )
    facts: list[Fact] = []
    tables = []
    currency = _report_currency(report)
    for table_id, title, columns, measures in _numeric_rows(_money_unit(currency)):
        rows = []
        for measure, label in measures:
            point = points[measure]
            prior = facts_by_id.get(point.prior_fact_id) if point.prior_fact_id else None
            current = facts_by_id[point.current_fact_id]
            ids = []
            for field in columns:
                fid = f"cp1b:{table_id}:{measure}:{field}"
                common: dict[str, Any] = {
                    "fact_id": fid,
                    "table_id": table_id,
                    "row_id": measure,
                    "field": field,
                    "label": f"{label} · {field}",
                    "decimals": None,
                }
                if field in {"prior", "current"}:
                    original = prior if field == "prior" else current
                    if original is None:
                        fact = Fact(
                            **common,
                            amount=None,
                            status="missing",
                            unit=point.unit,
                            currency=point.currency,
                            scale=point.scale,
                            period=report.prior_period_id,
                            limitation="COMPARATIVE_NOT_SUPPLIED",
                        )
                    else:
                        fact = original.model_copy(
                            update={
                                **common,
                                "period": report.prior_period_id
                                if field == "prior"
                                else report.current_period_id,
                                "calculation_id": None,
                                "formula": None,
                            }
                        )
                        fact = Fact.model_validate_json(fact.model_dump_json())
                else:
                    growth = field == "growth"
                    status = point.growth_status if growth else point.delta_status
                    nongrowth = growth and status == "not_applicable"
                    unit = (
                        "PERCENT"
                        if growth
                        else "pp"
                        if point.delta_unit == "PERCENTAGE_POINTS"
                        else point.delta_unit
                    )
                    formula = (
                        "(current - prior) / prior"
                        if growth
                        else "100 * (current - prior)"
                        if measure == "ebitda_margin"
                        else "current - prior"
                    )
                    fact = Fact(
                        **common,
                        amount=point.growth if growth else point.delta,
                        status=status,
                        unit=unit,
                        currency=None if growth or unit == "pp" else point.currency,
                        scale=Decimal(1) if growth or unit == "pp" else point.scale,
                        period=pair,
                        basis=_canonical(lineage[measure].model_dump(mode="json")),
                        citations=_citations(tuple(f for f in (prior, current) if f is not None)),
                        value_class="calculated",
                        calculation_id=None
                        if nongrowth
                        else f"cp1b-calc:{report.prior_period_id}:{report.current_period_id}:{measure}:{field}",
                        calculation_status=status,
                        formula=None if nongrowth else formula,
                        limitation="GROWTH_NOT_APPLICABLE" if nongrowth else point.reason,
                    )
                facts.append(fact)
                ids.append(fid)
            rows.append(TableRow(row_id=measure, label=label, fact_ids=tuple(ids)))
        tables.append(
            ReportTable(
                table_id=table_id,
                title=title,
                row_header="Measure",
                columns=tuple(TableColumn(field=f, label=headings[f]) for f in columns),
                rows=tuple(rows),
                limitation=table_limit,
            )
        )
    evidence = {
        "producer_module_id": "CP-1",
        "producer_sha256": producer.content_hash(),
        "prior_period_id": report.prior_period_id,
        "current_period_id": report.current_period_id,
        "prior_basis_id": report.prior_basis_id,
        "current_basis_id": report.current_basis_id,
        "operands": [o.model_dump(mode="json") for o in operands],
        **_currency_evidence(currency),
    }
    all_selected = tuple(
        facts_by_id[fid]
        for p in report.points
        for fid in (p.prior_fact_id, p.current_fact_id, *p.companion_fact_ids)
        if fid is not None
    )
    shared_citations = _citations(all_selected)
    assessments = (
        (
            "missing" if gap else "known",
            None
            if gap
            else f"The selected {report.prior_period_id} to {report.current_period_id} own-{_period_noun(report.current_period_id)} earnings comparison is flat; no causal-driver inference is supported.",
            f"COMPARATIVE_NOT_SUPPLIED: requested {prior_word} comparison basis is absent; current {current_word} values remain known."
            if gap
            else None,
            "analyst_judgment",
            shared_citations,
        ),
        (
            "missing",
            None,
            "DRIVER_EVIDENCE_NOT_SUPPLIED: no price, volume, FX or other causal-driver evidence is supplied by the selected authorized CP1 inputs.",
            "analyst_judgment",
            (),
        ),
        (
            "missing",
            None,
            "GUIDANCE_NOT_SUPPLIED: no management-guidance evidence is supplied by the selected authorized CP1 inputs.",
            "analyst_judgment",
            (),
        ),
        (
            "missing",
            None,
            f"COMPARATIVE_NOT_SUPPLIED: no {_prior_year_series(report)}",
            "analyst_judgment",
            shared_citations,
        ),
        (
            "missing",
            None,
            f"COMPARATIVE_NOT_SUPPLIED: requested {prior_word} leverage comparison basis is absent; current {current_word} leverage remains valid."
            if gap
            else _leverage_gap(report),
            "analyst_judgment",
            shared_citations,
        ),
        ("known", _canonical(evidence), None, "normalized", shared_citations),
        ("known", "\n".join(own_limits), None, "normalized", ()),
    )
    rows = []
    for (rid, label), (assessment_status, text, limitation, value_class, citations) in zip(
        _ASSESSMENT_ROWS, assessments, strict=True
    ):
        fid = f"cp1b:T1B.3:{rid}:assessment"
        facts.append(
            _parse(
                Fact,
                {
                    "fact_id": fid,
                    "label": label,
                    "table_id": "T1B.3",
                    "row_id": rid,
                    "field": "assessment",
                    "status": assessment_status,
                    "text": text,
                    "limitation": limitation,
                    "period": pair,
                    "value_class": value_class,
                    "citations": [c.model_dump(mode="json") for c in citations],
                },
            )
        )
        rows.append(TableRow(row_id=rid, label=label, fact_ids=(fid,)))
    tables.append(
        ReportTable(
            table_id="T1B.3",
            title="Evidence and analytical gaps",
            row_header="Assessment",
            columns=(TableColumn(field="assessment", label="Assessment"),),
            rows=tuple(rows),
        )
    )
    text = (
        "Current earnings observations: {cp1b:T1B.1:revenue:current|MILLIONS} {cp1b:T1B.1:ebitda:current|MILLIONS}. Requested prior income comparison is unavailable [cp1b:T1B.1:revenue:prior] [cp1b:T1B.1:revenue:delta] [cp1b:T1B.1:revenue:growth]."
        if gap
        else "Flat sequential earnings comparison: {cp1b:T1B.1:revenue:delta|MILLIONS} {cp1b:T1B.1:ebitda:delta|MILLIONS} {cp1b:T1B.1:adjusted_ebitda:delta|MILLIONS}. Current balance observations: {cp1b:T1B.2:cash_closing:current|MILLIONS} {cp1b:T1B.2:total_debt:current|MILLIONS} {cp1b:T1B.2:net_debt:current|MILLIONS}."
    )
    reference_ids = tuple(run.text for run in tokenize(text) if run.kind != "text")
    owned = {f.fact_id: f for f in facts}
    claim = Claim(
        claim_id="cp1b-comparison",
        text=text,
        citations=_citations(tuple(owned[fid] for fid in reference_ids)),
        limitation=f"COMPARATIVE_NOT_SUPPLIED: requested {prior_word} income and comparison basis are absent; current {current_word} values remain known. {opening} balance data is not an income comparator."
        if gap
        else "Flat sequential earnings only; causal drivers, management guidance and prior-year income are not supplied. The prior trailing-leverage comparison is unavailable.",
    )
    return Module(
        run_id=run.run_id,
        issuer_id=run.issuer_id,
        as_of=run.as_of,
        method_version=run.method_version,
        module_id="CP-1B",
        status="candidate",
        attempt=attempt.number,
        inputs=(*attempt.inputs, *tail),
        facts=tuple(facts),
        tables=tuple(tables),
        claims=(claim,),
        limitations=own_limits,
    )
