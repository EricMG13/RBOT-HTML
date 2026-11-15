"""CP-OS handoff orchestration.

``run_handoffs`` drives the checked public snapshot or explicitly mapped Markdown
report sections using the existing dependency planner and separate delivery adapter.
Explicit ``run_live_handoffs`` uses the adapted cp-os module loop with the existing
provider adapter and durable budget. Replay and host exchanges remain provider-free.
``run_comparison`` uses the same exchange for the current CP-8 definition:
compare complete prior/current delivery bundles, then publish its checked answer.
It does not invoke the imported investment-decision ledger owner.

The native report-navigation API that followed here (`navigation`, `verify_navigation`, its
`NavigationProof` over a verified owner run receipt) was removed: nothing called it.
"""

import argparse
import hashlib
import json
import logging
import re
import sys
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal
from uuid import uuid4

from pydantic import Field, TypeAdapter, model_validator

from deploy_vii.contracts import Contract, Hash, Run, View
from deploy_vii.registry import dependencies, plan
from deploy_vii.render import render
from deploy_workflow import platform_io
from deploy_workflow.changes import (
    DELIVERED_WHOLE,
    PACK_NAME,
    PRIOR_PREFIX,
    PriorRun,
    pack_builder,
    prior_sources,
)
from deploy_workflow.handoff_delivery import (
    HEADINGS,
    DeliveryRequest,
    HandoffInput,
    MarkdownLayout,
    ModelDelivery,
    comparison_files,
    deliver,
    delivery_files,
    verify_delivery,
    verify_files,
)
from deploy_workflow.model.budget import BudgetExhausted
from deploy_workflow.model.configs import CONFIGS, ModelConfig
from deploy_workflow.model.run_lock import RunDirBusy, _single_writer
from deploy_workflow.owners import cpos_forecast
from deploy_workflow.run_events import append_event, stop_reason
from deploy_workflow.run_scopes import PUBLIC_S1A_MODULES
from deploy_workflow.workflow import _put

if TYPE_CHECKING:
    from deploy_workflow.model.adapter import LiveAdapter
    from deploy_workflow.model.copilot_adapter import CopilotAdapter
    from deploy_workflow.model.handoff import HandoffExecutor


log = logging.getLogger(__name__)

# What a run records when CP-8 was planned and not produced (owner, 2026-11-12): the completion
# record's `changes` line, the delivery manifest's `changes_note`, a run event and stderr.
NOT_PRODUCED = "changes: not produced \u2014 "


class RetainedHandoff(HandoffInput):
    """A prior checked answer and the exact source/upstream context it may be reused with."""

    source_hashes: dict[str, Hash]
    upstream: dict[str, Hash]


class HandoffPlan(Contract):
    """Pinned inputs for the public snapshot or explicitly selected report sections."""

    run: Run
    sources: dict[str, HandoffInput] = Field(min_length=1)
    instructions: dict[str, HandoffInput]
    retained_handoffs: dict[str, RetainedHandoff] = Field(default_factory=dict)
    model: ModelDelivery | None = None
    publish_forecast: bool = Field(default=False, exclude_if=lambda v: not v)
    layout: MarkdownLayout | None = None
    # The earlier run CP-8 compares with (owner, 2026-11-11; `deploy_workflow.changes`). Its
    # delivered handoffs are the `prior/<module>.md` sources, given to CP-8 only. `changes_note` is
    # the line the launch recorded about the comparison, for the completion record.
    prior: PriorRun | None = Field(default=None, exclude_if=lambda v: v is None)
    changes_note: str | None = Field(default=None, exclude_if=lambda v: v is None)
    # How the run's modules were chosen: the pathway's preset or an explicit `--modules` list.
    # Only a preset run is a comparison base (`deploy_workflow.changes.find_prior`); an older
    # manifest records neither and is left unchanged.
    selection: Literal["preset", "explicit"] | None = Field(
        default=None, exclude_if=lambda v: v is None
    )
    execution: Literal["host-session", "retained-response-replay", "synthetic", "live-provider"]
    max_attempts: int = Field(default=2, ge=1, le=3)
    provider_cap_usd: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def prior_pins(self) -> "HandoffPlan":
        """CP-8 is requested exactly when an earlier run is pinned, and the `prior/` sources are
        exactly that run's handoffs."""
        held = {name for name in self.sources if name.startswith(PRIOR_PREFIX)}
        wanted = set() if self.prior is None else set(prior_sources(self.prior))
        if held != wanted or ("CP-8" in self.run.requested_modules) != (self.prior is not None):
            raise ValueError(
                "cpos_prior: CP-8 and the prior/ sources go together with the prior run"
            )
        return self

    @model_validator(mode="after")
    def execution_budget(self) -> "HandoffPlan":
        if self.execution == "live-provider":
            if self.provider_cap_usd <= 0 or self.max_attempts != 1:
                raise ValueError(
                    "Live mode needs a positive cap and one outer attempt; repairs occur inside the loop"
                )
        elif self.provider_cap_usd != 0:
            raise ValueError("Non-live modes require a zero provider cap")
        return self


class ComparisonPlan(Contract):
    """CP-8 consumes complete prior/current delivery receipts, without decision records."""

    run: Run
    prior: HandoffInput
    current: HandoffInput
    instructions: HandoffInput
    execution: Literal["host-session", "retained-response-replay", "synthetic", "live-provider"]
    max_attempts: int = Field(default=2, ge=1, le=3)
    provider_cap_usd: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def execution_budget(self) -> "ComparisonPlan":
        if self.execution == "live-provider":
            if self.provider_cap_usd <= 0 or self.max_attempts != 1:
                raise ValueError(
                    "Live mode needs a positive cap and one outer attempt; repairs occur inside the loop"
                )
        elif self.provider_cap_usd != 0:
            raise ValueError("Non-live modes require a zero provider cap")
        return self


@dataclass(frozen=True)
class HandoffTask:
    """Exact local model inputs; bytes and mapping proxies prevent in-place edits."""

    run: Run
    module_id: str
    instructions: bytes
    sources: Mapping[str, bytes]
    handoffs: Mapping[str, bytes]
    attempt: int
    feedback: tuple[str, ...]
    draft: bytes | None = None  # Explicit targeted repair; never automatic retry of a sent call.
    # Every handoff accepted so far in the run: read by the checker alone (prose check 7), so it
    # is not in the request fingerprint.
    accepted: Mapping[str, bytes] = MappingProxyType({})


def _pinned_inputs(base: Path, entries: Mapping[str, HandoffInput]) -> dict[str, bytes]:
    result = {}
    for name, spec in entries.items():
        raw = (base / spec.path).read_bytes()
        if _sha(raw) != spec.sha256:
            raise ValueError(f"cpos_input_changed: {name}")
        result[name] = raw
    return result


def _checked_handoff(
    task: HandoffTask,
    response: bytes,
    check: Callable[[HandoffTask, bytes], tuple[str, ...]],
) -> tuple[str, ...]:
    try:
        text = response.decode("utf-8")
    except UnicodeDecodeError:
        return ("The response must be UTF-8 Markdown.",)
    actual = tuple(line[3:] for line in text.splitlines() if line.startswith("## "))
    if actual != HEADINGS:
        return (
            "Use exactly these six H2 headings, once in this order: "
            + "; ".join("## " + heading for heading in HEADINGS)
            + ". All subsections must use ### or deeper, never ##. "
            + f"Received H2 headings: {actual!r}.",
        )
    issues = check(task, response)
    if type(issues) is not tuple or any(not isinstance(x, str) or not x.strip() for x in issues):
        raise ValueError("cpos_check: verifier must return a tuple of nonempty issue strings")
    return issues


def _retain_request(path: Path, raw: bytes, module_id: str) -> bool:
    """Retain an attempt's request; whether it was already retained (dispatched earlier). A
    retained request differs only in its feedback, which the recheck of the attempt before it now
    gives differently, so that attempt's answer cannot stand for this one."""
    started = path.exists()
    if started and path.read_bytes() != raw:
        raise ValueError(
            f"cpos_feedback_changed: {module_id}: the retained {path.name} answered other feedback "
            "than the recheck of the attempt before it now gives"
        )
    _put(path, raw)
    return started


def _retain_review(path: Path, raw: bytes) -> None:
    """Retain a verdict. A recheck that differs from the retained one (a fixed or tightened
    checker) is kept beside it under its own hash and is the one acted on; earlier verdicts stay as
    evidence (S01-C05)."""
    if path.exists() and path.read_bytes() != raw:
        path = path.with_name(f"{path.name.removesuffix('.json')}-{_sha(raw)}.json")
    _put(path, raw)


def request_fingerprint(inputs: Mapping[str, object]) -> str:
    """The name of a module's request folder: the sha256 of everything the request was given,
    instructions included. Each ``<n>.request.json`` there holds these inputs plus its attempt and
    feedback, so a reader can check that the folder still holds what it was named for."""
    return _sha(json.dumps(inputs, sort_keys=True).encode())


def _handoff(  # noqa: PLR0913 - existing signature
    task: HandoffTask,
    directory: Path,
    execute: Callable[[HandoffTask], bytes],
    check: Callable[[HandoffTask, bytes], tuple[str, ...]],
    max_attempts: int,
    *,
    retained: bytes | None = None,
) -> tuple[bytes, str]:
    """Retain before checking; resume checked bytes, never a half-finished call."""
    inputs = {
        "run": task.run.model_dump(mode="json"),
        "module_id": task.module_id,
        "instructions": task.instructions.decode("utf-8"),
        "sources": {k: _sha(v) for k, v in task.sources.items()},
        "handoffs": {k: _sha(v) for k, v in task.handoffs.items()},
        "retained_response_sha256": None if retained is None else _sha(retained),
    }
    if task.draft is not None:
        inputs["repair_draft_sha256"] = _sha(task.draft)
    fingerprint = request_fingerprint(inputs)
    folder = directory / "requests" / task.module_id / fingerprint
    feedback: tuple[str, ...] = ()
    for attempt in range(1, max_attempts + 1):
        current = replace(task, attempt=attempt, feedback=feedback)
        request_path = folder / f"{attempt}.request.json"
        response_path = folder / f"{attempt}.response.md"
        review_path = folder / f"{attempt}.review.json"
        request = {**inputs, "attempt": attempt, "feedback": feedback}
        raw_request = json.dumps(request, sort_keys=True, indent=2).encode()
        already_started = _retain_request(request_path, raw_request, task.module_id)
        if response_path.exists():
            response = response_path.read_bytes()
        elif already_started:
            raise ValueError(f"cpos_interrupted: response not retained for {task.module_id}")
        else:
            response = retained if retained is not None else execute(current)
            if not isinstance(response, bytes):
                raise ValueError("cpos_response: executor must return bytes")
            # first: the retained response is what a resume trusts, so the note is already there
            _retain_compaction(execute, retained, folder / f"{attempt}{COMPACTION_NOTE}")
            _put(response_path, response)
        if retained is not None and response != retained:
            raise ValueError(f"cpos_response_changed: {task.module_id}")
        if review_path.exists():
            previous = json.loads(review_path.read_bytes())
            if previous["response_sha256"] != _sha(response):
                raise ValueError(f"cpos_response_changed: {task.module_id}")
        feedback = _checked_handoff(current, response, check)
        review = {"response_sha256": _sha(response), "issues": feedback}
        _retain_review(review_path, json.dumps(review, sort_keys=True, indent=2).encode())
        if not feedback:
            return response, str(response_path.relative_to(directory))
        if retained is not None:
            raise ValueError(f"cpos_retained_rejected: {task.module_id}: {'; '.join(feedback)}")
    raise ValueError(f"cpos_module_failed: {task.module_id}: {'; '.join(feedback)}")


def _with_web_checks(
    execute: Callable[[HandoffTask], bytes],
    check: Callable[[HandoffTask, bytes], tuple[str, ...]],
) -> Callable[[HandoffTask, bytes], tuple[str, ...]]:
    """The check ``_handoff`` runs on every response it holds, a retained one on resume included:
    the launcher's checker, then the web checks of the run's lookup (``HandoffExecutor.web_issues``,
    none unless the module is offered lookup). The executor's own loop gives a live write the same
    web issues through ``ModuleTools`` and ``execute.check`` stays the bare checker, so a live
    write's feedback names each issue once: this wrapper runs only on the response the loop
    returned, which that loop accepted, and on the next attempt's feedback."""
    from deploy_workflow.model.handoff import HandoffExecutor

    if not isinstance(execute, HandoffExecutor):
        return check

    def checked(task: HandoffTask, raw: bytes) -> tuple[str, ...]:
        return (*check(task, raw), *execute.web_issues(task, raw))

    return checked


COMPACTION_NOTE = ".compaction.json"  # beside ``<attempt>.response.md``: the context was summarised


def _retain_compaction(
    execute: Callable[[HandoffTask], bytes], retained: bytes | None, note: Path
) -> None:
    """Keep, beside a response just produced, that the GitHub Copilot runtime summarised the
    session's context before the module wrote it (``HandoffExecutor.written_after_compaction``).
    A resume reads the note, not the executor, so the flag survives and nothing is called twice."""
    from deploy_workflow.model.handoff import HandoffExecutor

    if retained is not None or not isinstance(execute, HandoffExecutor):
        return
    found = execute.written_after_compaction
    if found is None:
        return
    body = {
        "attempt_id": found.attempt_id,
        "tokens_before": found.tokens_before,
        "tokens_after": found.tokens_after,
        "token_limit": found.token_limit,
    }
    _put(note, json.dumps(body, sort_keys=True).encode())


def _compaction_flag(response: Path) -> dict[str, str | int | bool]:
    """The ``module_accepted`` event fields for a module whose retained response has a compaction
    note: ``written_after_compaction`` and the tokens before it where the runtime gave them. A note
    that cannot be read still flags the module: the flag is never dropped."""
    note = response.with_name(response.name.removesuffix(".response.md") + COMPACTION_NOTE)
    if not note.is_file():
        return {}
    try:
        before = json.loads(note.read_bytes()).get("tokens_before")
    except (OSError, ValueError, AttributeError) as error:
        log.warning(
            "compaction note %s is unreadable (%s); the module is still flagged", note, error
        )
        return {"written_after_compaction": True}
    if isinstance(before, int) and not isinstance(before, bool):
        return {"written_after_compaction": True, "compaction_tokens_before": before}
    return {"written_after_compaction": True}


def review_line(module: str, tokens_before: int | None) -> str:
    """The plain line for a module written after GitHub Copilot summarised its context."""
    counted = "" if tokens_before is None else f" ({tokens_before:,} tokens before)"
    return (
        f"Review: {module} was written after GitHub Copilot summarised its context{counted}; "
        "check its figures against the earlier modules."
    )


def report_compaction(directory: Path, response_path: str, module: str) -> None:
    """Print the review line for ``module`` to stderr when its retained response has a
    compaction note (the route that has no run events, the CP-8 comparison, uses this)."""
    flag = _compaction_flag(directory / response_path)
    if flag:
        before = flag.get("compaction_tokens_before")
        print(review_line(module, before if isinstance(before, int) else None), file=sys.stderr)


def _refuse_decided_stale(
    ordered: Sequence[str],
    producers: Mapping[str, set[str]],
    specs: Mapping[str, RetainedHandoff],
) -> None:
    """Refuse, before any call, a retained module whose pinned upstream is not exactly the
    producers it is sent: the pins alone decide that, so no call may precede the refusal."""
    for module_id in ordered:
        spec = specs.get(module_id)
        if spec is not None and set(spec.upstream) != producers[module_id]:
            raise ValueError(f"cpos_retained_stale: {module_id}")


def _refuse_pins_of_replayed(
    specs: Mapping[str, RetainedHandoff], handoffs: Mapping[str, bytes]
) -> None:
    """Refuse a retained module whose pin of an already accepted module differs from those bytes.
    Run before each dispatch, so no call precedes a refusal the replayed modules already decide."""
    for module_id, spec in specs.items():
        if any(m in handoffs and sha != _sha(handoffs[m]) for m, sha in spec.upstream.items()):
            raise ValueError(f"cpos_retained_stale: {module_id}")


def run_handoffs(  # noqa: C901, PLR0912, PLR0913, PLR0915 -- legacy orchestrator; events is one more observer
    manifest: Path,
    directory: Path,
    *,
    execute: Callable[[HandoffTask], bytes],
    check: Callable[[HandoffTask, bytes], tuple[str, ...]],
    on_handoff: Callable[[HandoffTask, bytes], None] | None = None,
    events: Path | None = None,
) -> Path:
    """CP-OS exchange: plan, retain, check, pass current handoffs, deliver.

    Paid execution must use the explicit bounded live executor. The required
    checker compares output with instructions/evidence;
    Markdown shape alone is never analytical approval. Reusing this directory
    rechecks retained answers. Changed instructions/sources invalidate the affected
    requests and their actual consumers. All revisions remain retained. A crash
    after dispatch without retained output refuses automatic repeat. Explicitly
    retained handoffs are checked without executor calls, only when their pinned
    source and upstream context still match; completion records each module's origin.
    An optional observer runs after each checked response is durable and before
    the next module. It may stop for evidence review; resume rechecks the bytes.
    The start observer runs before each module is dispatched.
    With ``events`` (a live run's directory) each module, the delivery and its
    completion are appended to ``events.jsonl`` there; otherwise nothing is written.
    Their declared consumed inputs bound reuse planning; a checked published case
    does not trigger a new analytical build merely to satisfy a native producer.
    """
    request = HandoffPlan.model_validate_json(manifest.read_bytes())
    from deploy_workflow.model.adapter import LiveAdapter
    from deploy_workflow.model.copilot_adapter import CopilotAdapter
    from deploy_workflow.model.handoff import HandoffExecutor

    live = isinstance(execute, HandoffExecutor) and isinstance(
        execute.adapter, LiveAdapter | CopilotAdapter
    )
    if (request.execution == "live-provider") != live:
        raise ValueError("cpos_execution_mode: live mode requires the bounded live executor")
    if (
        live
        and isinstance(execute, HandoffExecutor)
        and (
            execute.budget.cap_usd != request.provider_cap_usd
            or execute.directory.resolve() != (directory / "live").resolve()
            or execute.check is not check
        )
    ):
        raise ValueError("cpos_live_binding: executor must share this run's cap, state and checker")
    if request.execution == "live-provider" and request.layout is None:
        raise ValueError("cpos_layout: a live-provider run needs a delivery layout")
    if request.layout is None and (
        request.run.pathway != "credit_snapshot"
        or request.run.case_kind != "public"
        or request.run.requested_modules != PUBLIC_S1A_MODULES
    ):
        raise ValueError("cpos_scope: only the public five-section handoff snapshot is supported")
    planned = plan(
        request.run.requested_modules,
        retained={m: tuple(spec.upstream) for m, spec in request.retained_handoffs.items()},
    )
    if request.layout is not None:
        from deploy_vii.report_view import pathways

        selected_modules = set(planned)
        # CP-8 is allowed here: in a run it compares with the pinned earlier run. The comparison
        # of two delivered bundles (`run_comparison`) is a different route.
        if selected_modules & {"CP-MODEL", "CP-MEMO", "CP-OS"}:
            raise ValueError(
                "cpos_scope: select analytical Markdown modules; the Model uses its existing route"
            )
        preset = next(p for p in pathways() if p.id == request.run.pathway)
        if (
            len(set(request.layout.blocks)) != len(request.layout.blocks)
            or not set(request.layout.blocks) <= set(preset.blocks)
            or {r.block_id for r in request.layout.routes} != set(request.layout.blocks)
            or any(
                r.module_id not in selected_modules
                and not (r.module_id == "CP-MODEL" and request.model is not None)
                for r in request.layout.routes
            )
            or any(r.module_id not in selected_modules for r in request.layout.front)
        ):
            raise ValueError(
                "cpos_layout: route selected modules to unique blocks of the requested pathway"
            )
    ordered = tuple(m for m in planned if m != "CP-MODEL")
    if request.publish_forecast and (request.layout is None or "CP-1" not in ordered):
        raise ValueError("cpos_forecast: a forecast needs a layout and the CP-1 module")
    if set(request.instructions) != set(ordered):
        raise ValueError("cpos_instructions: exactly one pinned instruction per analytical module")
    if set(request.retained_handoffs) - set(ordered):
        raise ValueError("cpos_retained_inputs: handoff names must be selected analytical modules")
    sources = _pinned_inputs(manifest.parent, request.sources)
    # The earlier run's handoffs are for CP-8 alone: every other module is sent the run's own
    # sources only.
    run_sources = {k: v for k, v in sources.items() if not k.startswith(PRIOR_PREFIX)}
    instructions = _pinned_inputs(manifest.parent, request.instructions)
    retained = _pinned_inputs(manifest.parent, request.retained_handoffs)
    # Each module is sent only its declared producers' handoffs (CP-5 every analyst before it).
    # Run tdg-all-001 (2026-11-10) sent every earlier handoff: CP-5's first request was 1 MB.
    producers = dependencies(ordered)
    _refuse_decided_stale(ordered, producers, request.retained_handoffs)
    source_hashes = {name: _sha(raw) for name, raw in sources.items()}
    for module_id, retained_spec in request.retained_handoffs.items():
        if retained_spec.source_hashes != source_hashes:
            raise ValueError(f"cpos_retained_sources: {module_id}")
    for raw in instructions.values():
        raw.decode("utf-8")
    model_inputs = {} if request.model is None else dict(request.model.extra_handoffs)
    if request.model is not None and request.model.forecast_exact is not None:
        model_inputs["forecast_exact"] = request.model.forecast_exact
    model_raws = _pinned_inputs(manifest.parent, model_inputs)
    identity = request.model_dump(
        mode="json",
        exclude={
            "sources",
            "instructions",
            "retained_handoffs",
            "model",
            "layout",
            "publish_forecast",
        },
    )
    directory.mkdir(parents=True, exist_ok=True)
    with _single_writer(directory):
        _put(directory / "identity.json", json.dumps(identity, sort_keys=True).encode())
        for raw in (
            *sources.values(),
            *instructions.values(),
            *retained.values(),
            *model_raws.values(),
        ):
            _put(directory / "inputs" / _sha(raw), raw)
        handoffs: dict[str, bytes] = {}
        selected: dict[str, str] = {}
        changes: HandoffInput | None = None
        not_produced = _recorded_not_produced(directory)  # an earlier launch's decision stands
        if not_produced is not None:
            ordered = tuple(m for m in ordered if m != "CP-8")
            print(
                f"{NOT_PRODUCED}{not_produced} (recorded by the earlier launch of this run; "
                "no new call, the delivery is left as it is)",
                file=sys.stderr,
            )
        for module_id in ordered:
            _refuse_pins_of_replayed(request.retained_handoffs, handoffs)
            spec = request.retained_handoffs.get(module_id)
            supplied = {m: handoffs[m] for m in ordered if m in producers[module_id]}
            if spec is not None and spec.upstream != {m: _sha(raw) for m, raw in supplied.items()}:
                raise ValueError(f"cpos_retained_stale: {module_id}")
            task_sources = run_sources
            if module_id == "CP-8":
                if request.prior is None:
                    raise ValueError("cpos_prior: CP-8 needs the pinned earlier run")
                # Computed by Python from the earlier run's pinned handoffs and this run's accepted
                # ones before CP-8 is called; it is also published as the delivery's changes.json.
                try:
                    pack = pack_builder(
                        request.prior,
                        request.run.as_of.isoformat(),
                        request.run.pathway,
                        request.selection,
                    )(sources, supplied)
                except (ValueError, ArithmeticError) as error:
                    # The one fail-open of CP-8 (see below): a handoff text the pack cannot read.
                    not_produced = f"the comparison pack could not be built ({error})"
                    break
                _put(directory / "inputs" / _sha(pack), pack)
                changes = HandoffInput(path="inputs/" + _sha(pack), sha256=_sha(pack))
                task_sources = {**sources, PACK_NAME: pack}
            task = HandoffTask(
                request.run,
                module_id,
                instructions[module_id],
                MappingProxyType(task_sources),
                MappingProxyType(supplied),
                1,
                (),
                accepted=MappingProxyType(dict(handoffs)),
            )
            if events is not None:
                append_event(events, "module_started", module=module_id)
            try:
                raw, path = _handoff(
                    task,
                    directory,
                    execute,
                    _with_web_checks(execute, check),
                    request.max_attempts,
                    retained=retained.get(module_id),
                )
            except (ValueError, RuntimeError) as error:
                # Fail-open, by design and only for CP-8 (owner, 2026-11-12): the comparison is
                # optional to completion, so a CP-8 that is not accepted within its bounds, or
                # whose call does not fit the cap, does not stop the run's delivery of everything
                # the other modules produced. Any other module's failure, and any other fault of
                # CP-8's call (a provider stop, an overrun, an interrupted call), still propagates.
                # The reason is logged, recorded in the completion record, the delivery manifest
                # and a run event, and printed to stderr.
                if module_id != "CP-8" or not _cp8_unaccepted(error):
                    raise
                not_produced = with_notes(error)
                break
            handoffs[module_id] = raw
            selected[module_id] = path
            if events is not None:
                append_event(
                    events,
                    "module_accepted",
                    module=module_id,
                    **_compaction_flag(directory / path),
                )
            if on_handoff is not None:
                on_handoff(task, raw)
        layout = request.layout
        if "CP-8" in ordered and "CP-8" not in handoffs:
            ordered = tuple(m for m in ordered if m != "CP-8")
            changes = None
            print(f"{NOT_PRODUCED}{not_produced}", file=sys.stderr)
            log.warning("CP-8 was not produced; the run delivers without it: %s", not_produced)
            if events is not None:
                append_event(events, "changes_not_produced", reason=str(not_produced))
        changes_note = request.changes_note
        if not_produced is not None:
            changes_note = f"{NOT_PRODUCED}{not_produced}"
            if layout is not None:
                scope = layout.scope.replace(DELIVERED_WHOLE, "")
                scope += f" Changes since the last run (CP-8): {changes_note}."
                layout = layout.model_copy(update={"scope": scope})
        forecast, failure = request.publish_forecast, None
        if forecast:
            try:
                source = "CP-2G" if "CP-2G" in handoffs else "CP-1"
                cpos_forecast.model_files(handoffs["CP-1"], handoffs[source], source, history=True)
            except ValueError as error:
                # Fail-open, by design and only for ValueError (the inputs block is missing or
                # invalid): the report is complete without the forecast, so the run still
                # delivers, and the reason is logged here, in the completion record and on stderr.
                # With CP-2G absent the block is CP-1's layer-1 block, which is never a blocking
                # check on CP-1 (owner, 2026-11-11): its fault only withholds the model.
                forecast, failure = False, str(error)
                print(f"Model not published: {failure}", file=sys.stderr)
                if events is not None:
                    append_event(events, "model_not_published", reason=failure)
        if events is not None:
            append_event(events, "delivery_started")
        delivery_request = DeliveryRequest(
            run=request.run,
            handoffs={
                m: HandoffInput(path=selected[m], sha256=_sha(handoffs[m]))
                for m in (ordered if request.layout is not None else ("CP-1", "CP-1A", "CP-2"))
            },
            layout=layout,
            forecast=forecast,
            history=forecast,  # a new run publishes the history record with its forecast
            changes=changes,
            changes_note=changes_note if not_produced is not None else None,
            module_execution=_module_execution(ordered, retained, request)
            if request.layout is not None
            else None,
            model=None
            if request.model is None
            else request.model.model_copy(
                update={
                    "extra_handoffs": {
                        k: HandoffInput(path="inputs/" + spec.sha256, sha256=spec.sha256)
                        for k, spec in request.model.extra_handoffs.items()
                    },
                    "forecast_exact": None
                    if request.model.forecast_exact is None
                    else HandoffInput(
                        path="inputs/" + request.model.forecast_exact.sha256,
                        sha256=request.model.forecast_exact.sha256,
                    ),
                }
            ),
        )
        delivery_raw = delivery_request.model_dump_json(indent=2).encode()
        manifest_id = _sha(delivery_raw)
        delivery_manifest = directory / f"delivery-{manifest_id}.json"
        _put(delivery_manifest, delivery_raw)
        publication = delivery_files(delivery_manifest)
        delivery_id = _sha(
            json.dumps(
                {name: _sha(raw) for name, raw in publication.items()}, sort_keys=True
            ).encode()
        )
        destination = directory / "deliveries" / delivery_id
        if not destination.exists():
            staging = directory / "pending-deliveries" / uuid4().hex
            deliver(delivery_manifest, staging)
            verify_delivery(delivery_manifest, staging)
            destination.parent.mkdir(parents=True, exist_ok=True)
            platform_io.replace(staging, destination)
        receipt = verify_delivery(delivery_manifest, destination)
        completion = {
            "kind": "cpos-handoff-snapshot/1"
            if request.layout is None
            else "cpos-markdown-delivery/1",
            "execution": request.execution,
            "scope": layout.scope
            if layout is not None
            else "public five-section snapshot"
            + (
                " plus deterministic HTML Model/charts/calculation JSON"
                if request.model is not None
                else "; Model publication not requested"
            )
            + "; not full pathway/native acceptance",
            "provider_cap_usd": str(request.provider_cap_usd) if live else 0,
            "modules": selected,
            "module_execution": _module_execution(ordered, retained, request),
            "cp_model_published": request.model is not None,
            "cp_forecast_published": forecast,
            "forecast_failure": failure,
            **({} if changes_note is None else {"changes": changes_note}),
            "delivery_manifest_sha256": manifest_id,
            "delivery_sha256": _sha(receipt.read_bytes()),
        }
        completion_raw = json.dumps(completion, indent=2).encode()
        _put(directory / f"completed-{_sha(completion_raw)}.json", completion_raw)
        if events is not None:
            append_event(events, "delivered")
        return receipt


def _cp8_unaccepted(error: BaseException) -> bool:
    """Whether a failure of CP-8's loop is "not accepted within its bounds" or "its hold does not
    fit the cap": the two refusals the run survives. A provider stop, an overrun, an interrupted or
    already started call is not one of them."""
    return isinstance(error, BudgetExhausted) or str(error).startswith(
        ("cpos_live_not_accepted: CP-8", "cpos_module_failed: CP-8")
    )


def _recorded_not_produced(directory: Path) -> str | None:
    """The reason an earlier launch of this run folder recorded for delivering without CP-8, or
    None. A relaunch keeps that decision: it makes no new call for CP-8."""
    for path in sorted(directory.glob("completed-*.json")):
        try:
            note = json.loads(path.read_bytes()).get("changes")
        except (OSError, ValueError, AttributeError) as error:
            log.warning("completion record %s is unreadable (%s)", path.name, error)
            continue
        if isinstance(note, str) and note.startswith(NOT_PRODUCED):
            return note.removeprefix(NOT_PRODUCED)
    return None


def _module_execution(
    ordered: tuple[str, ...], retained: Mapping[str, object], request: HandoffPlan
) -> dict[str, Literal["host-session", "retained-response-replay", "synthetic", "live-provider"]]:
    """How each module was produced: a retained handoff is a replay whatever the run's mode."""
    return {m: "retained-response-replay" if m in retained else request.execution for m in ordered}


def live_adapter_for(
    selected: "ModelConfig", ruling: Path, environ: Mapping[str, str], rulings_root: Path | None
) -> "LiveAdapter | CopilotAdapter":
    """The adapter for one model configuration: the Copilot SDK adapter for a copilot provider,
    else the HTTP adapter. A ``CopilotAdapter`` holds a runtime process and kept sessions:
    its builder must ``close()`` it after the executor finishes."""
    from deploy_workflow.model.adapter import LiveAdapter
    from deploy_workflow.model.copilot_adapter import CopilotAdapter
    from deploy_workflow.model.turn import ModelSpec

    spec = ModelSpec(selected.config_id, selected.provider, selected.model, selected.effort)
    if selected.provider == "copilot":
        return CopilotAdapter(spec, ruling, environ=environ, rulings_root=rulings_root)
    return LiveAdapter(spec, ruling, environ=environ, rulings_root=rulings_root)


def with_notes(error: BaseException) -> str:
    """``str(error)`` followed by its notes (a release failure is recorded as one), joined by "; "."""
    text = str(error)
    notes = "; ".join(n for n in getattr(error, "__notes__", ()) if n not in text)
    return f"{text}; {notes}" if notes else text


def _release(
    adapter: "LiveAdapter | CopilotAdapter", executor: "HandoffExecutor | None" = None
) -> None:
    """Close the Copilot adapter (it holds a runtime process); HTTP adapters hold nothing. Before
    it closes, the executor drains each module's session once more for a context summary still
    running when its module ended (the launcher totals the run's events after the close)."""
    from deploy_workflow.model.copilot_adapter import CopilotAdapter

    if isinstance(adapter, CopilotAdapter):
        try:
            if executor is not None:
                executor.drain_late()
        finally:
            adapter.close()


# The token a ruling's ``configs:`` line carries to let the research module search the web (owner,
# 2026-11-10: "Cp-dr supplies the peers"). Without it CP-DR reads only the run's files.
WEB_SEARCH_GRANT = "web-search"


def web_search_ruled(ruling: Path | None, rulings_root: Path | None = None) -> bool:
    """Whether ``ruling`` lists ``web-search`` among its configs."""
    from deploy_workflow.model.adapter import LivePauseInForce, check_ruling

    if ruling is None:
        return False
    try:
        check_ruling(WEB_SEARCH_GRANT, ruling, rulings_root=rulings_root)
    except LivePauseInForce:
        return False
    return True


def web_search_run(config: str, ruling: Path | None, rulings_root: Path | None = None) -> bool:
    """Whether a run of ``config`` searches the web: the ruling lists it and the provider is OpenAI.

    Search is OpenAI's hosted tool (``HandoffExecutor`` refuses it elsewhere), so a Claude run under
    the same ruling runs with search off rather than stopping."""
    return CONFIGS[config].provider == "openai" and web_search_ruled(ruling, rulings_root)


def run_live_handoffs(  # noqa: PLR0913 -- the explicit paid entry point takes every run option
    manifest: Path,
    directory: Path,
    *,
    ruling: Path,
    check: Callable[[HandoffTask, bytes], tuple[str, ...]],
    environ: Mapping[str, str] | None = None,
    max_turns: int = 24,
    max_output_tokens: int = 16000,
    on_handoff: Callable[[HandoffTask, bytes], None] | None = None,
    config: str = "sol-medium",
    rulings_root: Path | None = None,
    effort_by_module: Mapping[str, str] | None = None,
    on_notice: Callable[[str], None] | None = None,
    web_lookup: str = "default",
    web_hosts: Sequence[str] = (),
    lookup_cutoff: date | None = None,
) -> Path:
    """Explicit paid entry point; callers supply an evidence/instruction checker.

    ``web_lookup`` (``default``, ``on`` or ``off``), ``web_hosts`` (the case's own
    investor-relations hosts) and ``lookup_cutoff`` (the run's research cutoff; the as-of date
    when None) set the research module's page and SEC EDGAR lookups. ``default`` is settled
    here, against the plan's modules and case kind, so the executor and ``loop.json`` hold the
    answer; a run folder started earlier keeps the setting its ``live/loop.json`` recorded, and a
    contradicting setting is refused (``ValueError``).

    No provider execution occurs during build, import, replay or normal delivery.
    Credentials come from the launching environment, never a file in this API.
    """
    import os

    from deploy_workflow.model.handoff import (
        HandoffExecutor,
        recorded_web_lookup,
        settled_web_lookup,
    )
    from deploy_workflow.model.redact import Redactor
    from deploy_workflow.research.weblookup import Runtime

    request = HandoffPlan.model_validate_json(manifest.read_bytes())
    if request.execution != "live-provider":
        raise ValueError("cpos_live_mode: manifest must explicitly declare live-provider")
    environment = os.environ if environ is None else environ
    lookup = settled_web_lookup(
        web_lookup,
        list(request.instructions),
        request.run.case_kind,
        recorded_web_lookup(directory / "live" / "loop.json"),
    )
    adapter = live_adapter_for(CONFIGS[config], ruling, environment, rulings_root)
    executor: HandoffExecutor | None = None
    try:
        executor = HandoffExecutor(
            directory / "live",
            adapter=adapter,
            cap_usd=request.provider_cap_usd,
            check=check,
            redactor=Redactor.from_environ(environment),
            max_turns=max_turns,
            max_output_tokens=max_output_tokens,
            events=directory,
            web_search=web_search_run(config, ruling, rulings_root),
            effort_by_module=effort_by_module,
            notice=on_notice,
            web_lookup=lookup,
            web_hosts=web_hosts,
            lookup_cutoff=lookup_cutoff,
            lookup_runtime=Runtime(env=environment),
        )
        result = run_handoffs(
            manifest,
            directory,
            execute=executor,
            check=check,
            on_handoff=on_handoff,
            events=directory,
        )
    except BaseException as stop:
        # Documented fail-open: a release failure must not mask the stop it follows; it is
        # recorded as a note on the propagating exception.
        if isinstance(stop, Exception) and not isinstance(stop, RunDirBusy):
            # A refused second invocation never held the folder; the running run owns its log.
            append_event(directory, "stopped", reason=stop_reason(stop))
        try:
            _release(adapter, executor)
        except Exception as failure:  # noqa: BLE001 -- noted on the propagating stop
            note = f"adapter release also failed: {failure}"
            stop.add_note(note)
            if (
                isinstance(stop, Exception)
                and len(stop.args) == 1
                and isinstance(stop.args[0], str)
            ):
                stop.args = (f"{stop.args[0]}; {note}",)  # callers that print str(stop) show it
        raise
    try:
        _release(adapter, executor)
    except Exception as failure:  # noqa: BLE001 -- the finished run's result outranks the release
        warnings.warn(f"adapter release failed: {failure}", RuntimeWarning, stacklevel=2)
    return result


def replay_handoffs(
    manifest: Path, directory: Path, responses_manifest: Path | None = None
) -> Path:
    """Drive CP-OS with pinned prior answers; byte parity is not fresh analytical review."""
    request = HandoffPlan.model_validate_json(manifest.read_bytes())
    if request.execution != "retained-response-replay":
        raise ValueError("cpos_replay_mode: the manifest must declare retained-response-replay")
    entries: Mapping[str, HandoffInput]
    if responses_manifest is None:
        entries = request.retained_handoffs
        base = manifest.parent
    else:
        entries = TypeAdapter(dict[str, HandoffInput]).validate_json(
            responses_manifest.read_bytes()
        )
        base = responses_manifest.parent
    if set(entries) != set(request.instructions):
        raise ValueError("cpos_replay_inputs: responses must match selected analytical modules")
    responses = _pinned_inputs(base, entries)
    return run_handoffs(
        manifest,
        directory,
        execute=lambda task: responses[task.module_id],
        check=lambda task, raw: (
            () if raw == responses[task.module_id] else ("Replay bytes differ.",)
        ),
    )


def _comparison_bundle(base: Path, spec: HandoffInput) -> tuple[View, dict[str, bytes]]:
    """Check complete frozen bundle bytes and their embedded report/view consistency."""
    receipt_path = base / spec.path
    receipt_raw = receipt_path.read_bytes()
    if _sha(receipt_raw) != spec.sha256:
        raise ValueError("cp8_bundle_changed: delivery receipt")
    receipt = json.loads(receipt_raw)
    hashes = TypeAdapter(dict[str, Hash]).validate_python(receipt["files"])
    required = {"view.json", "report-view.json"}
    if (
        not required <= set(hashes)
        or "delivery.json" in hashes
        or any(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) is None for name in hashes)
    ):
        raise ValueError("cp8_bundle_files: unsafe or incomplete delivery file set")
    files = {name: (receipt_path.parent / name).read_bytes() for name in hashes}
    if any(_sha(files[name]) != digest for name, digest in hashes.items()):
        raise ValueError("cp8_bundle_changed: publication bytes")
    if {p.name for p in receipt_path.parent.iterdir()} != set(hashes) | {receipt_path.name}:
        raise ValueError("cp8_bundle_files: unlisted or missing publication files")
    if receipt.get("cp_model_published") is True and "model.html" not in files:
        raise ValueError("cp8_bundle_files: declared Model HTML is missing")
    view = View.model_validate_json(files["view.json"])
    from deploy_vii.report_view import ReportView

    report = ReportView.model_validate_json(files["report-view.json"])
    # Earlier bundles also carry the rendered report page: it must still match the retained
    # views. Later bundles carry none and are bound by the receipt and file hashes checked above.
    if "report.html" in files and (
        files["report.html"].decode().count(OPEN_TAG) != 1
        or _extract(files["report.html"]) != _extract(render(view, report).encode())
    ):
        raise ValueError("cp8_bundle_binding: HTML differs from retained View/ReportView")
    if "model.html" in files:
        if not {"model-view.json", "model-report-view.json", "calculation.json"} <= set(files):
            raise ValueError("cp8_bundle_files: incomplete Model publication")
        model_view = View.model_validate_json(files["model-view.json"])
        model_report = ReportView.model_validate_json(files["model-report-view.json"])
        if (
            (
                model_view.run.run_id,
                model_view.run.issuer_id,
                model_view.run.issuer_name,
                model_view.run.as_of,
            )
            != (view.run.run_id, view.run.issuer_id, view.run.issuer_name, view.run.as_of)
            or len(model_view.modules) != 1
            or model_view.modules != tuple(m for m in view.modules if m.module_id == "CP-MODEL")
            or model_view.modules[0].artifact_sha256 != _sha(files["calculation.json"])
        ):
            raise ValueError(
                "cp8_bundle_binding: Model identity/content differs from the current bundle"
            )
        if files["model.html"].decode().count(OPEN_TAG) != 1 or _extract(
            files["model.html"]
        ) != _extract(render(model_view, model_report).encode()):
            raise ValueError("cp8_bundle_binding: Model HTML differs from retained views")
    return view, {**files, "delivery.json": receipt_raw}


def _check_comparison_pair(request: ComparisonPlan, prior: View, current: View) -> None:
    """Both deliveries are the selected issuer's, the current one has the selected date, and they
    are a prior delivery and a later-or-same-dated current one: CP-8 compares a prior run's
    deliverables with the current run's (AGENTS.md), never a delivery with itself."""
    for view in (prior, current):
        if (view.run.issuer_id, view.run.issuer_name) != (
            request.run.issuer_id,
            request.run.issuer_name,
        ):
            raise ValueError("cp8_issuer: both deliveries must identify the selected issuer")
    if current.run.as_of != request.run.as_of:
        raise ValueError(
            "cp8_as_of: comparison uses the selected current delivery's financial date"
        )
    if request.prior.sha256 == request.current.sha256:
        raise ValueError("cp8_same_delivery: prior and current pin the same delivery receipt")
    if prior.run.as_of > current.run.as_of:
        raise ValueError(
            "cp8_order: the prior delivery's financial date is after the current delivery's"
        )


def run_comparison(
    manifest: Path,
    directory: Path,
    *,
    execute: Callable[[HandoffTask], bytes],
    check: Callable[[HandoffTask, bytes], tuple[str, ...]],
) -> Path:
    """CP-OS: verify both deliveries, request/check CP-8, publish its actual handoff."""
    request = ComparisonPlan.model_validate_json(manifest.read_bytes())
    from deploy_workflow.model.adapter import LiveAdapter
    from deploy_workflow.model.copilot_adapter import CopilotAdapter
    from deploy_workflow.model.handoff import HandoffExecutor

    live = isinstance(execute, HandoffExecutor) and isinstance(
        execute.adapter, LiveAdapter | CopilotAdapter
    )
    if (request.execution == "live-provider") != live:
        raise ValueError("cpos_execution_mode: live mode requires the bounded live executor")
    if (
        live
        and isinstance(execute, HandoffExecutor)
        and (
            execute.budget.cap_usd != request.provider_cap_usd
            or execute.directory.resolve() != (directory / "live").resolve()
            or execute.check is not check
        )
    ):
        raise ValueError("cpos_live_binding: executor must share this run's cap, state and checker")
    if request.run.requested_modules != ("CP-8",) or request.run.pathway != "credit_snapshot":
        raise ValueError("cp8_scope: select CP-8 deliverable comparison on the snapshot shell")
    prior_view, prior = _comparison_bundle(manifest.parent, request.prior)
    current_view, current = _comparison_bundle(manifest.parent, request.current)
    _check_comparison_pair(request, prior_view, current_view)
    instructions = _pinned_inputs(manifest.parent, {"CP-8": request.instructions})["CP-8"]
    instructions.decode("utf-8")
    sources = {
        **{"prior/" + k: v for k, v in prior.items()},
        **{"current/" + k: v for k, v in current.items()},
    }
    source_hashes = {name: _sha(raw) for name, raw in sources.items()}
    identity = request.model_dump(mode="json", exclude={"prior", "current", "instructions"})
    if not live:
        identity["provider_cap_usd"] = 0  # Preserve identities of existing provider-free runs.
    directory.mkdir(parents=True, exist_ok=True)
    with _single_writer(directory):
        _put(directory / "identity.json", json.dumps(identity, sort_keys=True).encode())
        for raw in (*sources.values(), instructions):
            _put(directory / "inputs" / _sha(raw), raw)
        task = HandoffTask(
            request.run,
            "CP-8",
            instructions,
            MappingProxyType(sources),
            MappingProxyType({}),
            1,
            (),
        )

        def checked_response(current_task: HandoffTask, raw: bytes) -> tuple[str, ...]:
            try:
                comparison_files(current_task.run, raw, source_hashes)
            except ValueError as error:
                if str(error).startswith("cp8_dimensions:"):
                    return (str(error),)
                raise
            return check(current_task, raw)

        response, response_path = _handoff(
            task, directory, execute, checked_response, request.max_attempts
        )
        report_compaction(directory, response_path, "CP-8")
        files = comparison_files(request.run, response, source_hashes)
        delivery_id = _sha(
            json.dumps({name: _sha(raw) for name, raw in files.items()}, sort_keys=True).encode()
        )
        destination = directory / "deliveries" / delivery_id
        if not destination.exists():
            staging = directory / "pending-deliveries" / uuid4().hex
            for name, raw in files.items():
                _put(staging / name, raw)
            verify_files(staging, files)
            destination.parent.mkdir(parents=True, exist_ok=True)
            platform_io.replace(staging, destination)
        receipt = verify_files(destination, files)
        completion = {
            "kind": "cpos-deliverable-comparison/1",
            "execution": request.execution,
            "scope": "Checked CP-8 comparison of selected delivery bundles; "
            "not decision calibration or full pathway acceptance",
            "provider_cap_usd": str(request.provider_cap_usd) if live else 0,
            "response": response_path,
            "response_sha256": _sha(response),
            "input_files": source_hashes,
            "delivery_id": delivery_id,
            "delivery_sha256": _sha(receipt.read_bytes()),
        }
        raw_completion = json.dumps(completion, indent=2).encode()
        _put(directory / f"completed-{_sha(raw_completion)}.json", raw_completion)
        return receipt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CP-OS retained-handoff replay and deliverable comparison; no providers"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument(
        "--compare", action="store_true", help="Replay CP-8 over prior/current delivery bundles"
    )
    parser.add_argument(
        "--replay-responses",
        type=Path,
        help="Optional when every analytical handoff is pinned in retained_handoffs",
    )
    args = parser.parse_args()
    if args.compare:
        request = ComparisonPlan.model_validate_json(args.manifest.read_bytes())
        if request.execution != "retained-response-replay" or args.replay_responses is None:
            raise ValueError(
                "cp8_replay: declare retained-response-replay and pin the CP-8 response map"
            )
        entries = TypeAdapter(dict[str, HandoffInput]).validate_json(
            args.replay_responses.read_bytes()
        )
        if set(entries) != {"CP-8"}:
            raise ValueError("cp8_replay: response map must contain only CP-8")
        response = _pinned_inputs(args.replay_responses.parent, entries)["CP-8"]
        print(
            run_comparison(
                args.manifest,
                args.state,
                execute=lambda task: response,
                check=lambda task, raw: () if raw == response else ("Replay bytes differ.",),
            )
        )
    else:
        print(replay_handoffs(args.manifest, args.state, args.replay_responses))


OPEN_TAG = '<script id="report-data" type="application/json">'
CLOSE_TAG = "</script>"


def _refuse(prefix: str, detail: str) -> ValueError:
    return ValueError(f"{prefix}: {detail}")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract(page: bytes) -> dict[str, Any]:
    """The `report-data` JSON of a page. The first closing script tag ends it (render.py escapes
    every `<` in DATA), so the text between is exact. Anything else is `cpos_target_missing`."""
    try:
        text = page.decode()
    except UnicodeDecodeError:
        raise _refuse("cpos_target_missing", "page is not UTF-8") from None
    start = text.find(OPEN_TAG)
    if start < 0:
        raise _refuse("cpos_target_missing", "no report-data tag")
    start += len(OPEN_TAG)
    end = text.find(CLOSE_TAG, start)
    if end < 0:
        raise _refuse("cpos_target_missing", "report-data tag is not closed")
    try:
        data = json.loads(text[start:end])
    except ValueError:
        raise _refuse("cpos_target_missing", "report-data is not JSON") from None
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("modules"), list)
        or not isinstance(data.get("nav"), list)
        or not isinstance(data.get("report"), dict)
        or not isinstance(data["report"].get("blocks"), list)
    ):
        raise _refuse("cpos_target_missing", "report-data lacks modules, nav or report blocks")
    result: dict[str, Any] = data
    return result


if __name__ == "__main__":
    main()
