"""GitHub Copilot SDK adapter: the parsing half.

One call's raw body is the JSON array of the session events observed for that call, each
``{"type": <event type>, "data": <event data as camelCase wire keys>}``. ``parse_events`` maps it
to the ``Turn`` the loop prices and records. This half imports nothing from the ``copilot`` SDK
package (the SDK is top-level ``copilot``; this module is ``deploy_workflow.model.copilot``).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from deploy_workflow.model.providers import (
    REPLY_CUT,
    ErrorKind,
    ProviderError,
    _BadReply,
    _count,
    _id,
    _snippet,
    _str_or_none,
    _usage_error,
)
from deploy_workflow.model.redact import Redactor
from deploy_workflow.model.turn import (
    Compaction,
    StopReason,
    ToolCall,
    Turn,
    TurnError,
    Usage,
    dump_json,
    load_json,
)

USAGE = "assistant.usage"
MESSAGE = "assistant.message"
TOOL_START = "tool.execution_start"
SESSION_ERROR = "session.error"
COMPACTION_START = "session.compaction_start"
COMPACTION_COMPLETE = "session.compaction_complete"

# The runtime's context limit per model, in tokens: the ``tokenLimit`` its own events report,
# 272000 for gpt-6.1-sol. Read from the raw bodies of the four retained runs
# (tdg-full-copilot-sol-001, -sol-001-resume, -sol-high-001, -sol-high-001-resume, live/raw/*.json,
# e.g. c6f6170f864287194550faf5980d1383667cd20cdb6fbb97092ed689dc36e1e2-1.json): all 521 files
# carry "tokenLimit":272000 and no other value. Only a model whose limit has been read from the
# runtime is listed: for any other the first-prompt check is silent.
TOKEN_LIMITS: Mapping[str, int] = MappingProxyType({"gpt-6.1-sol": 272_000})
# The SDK's default for background compaction (copilot/session.py ``InfiniteSessionConfig``,
# github_copilot_sdk 1.0.28): the runtime starts summarising at this share of the limit.
COMPACTION_SHARE = Decimal("0.80")
# An ESTIMATE of request bytes per token, from the retained high-effort run's first requests
# (tdg-full-copilot-sol-high-001-resume: ``modules/<digest>/0.request.json`` bytes over the call's
# ``input_tokens``): 3.73 to 4.50 over 15 modules, 3.85 to 3.93 for the four largest (CP-3, CP-5,
# CP-6, CP-8). The lower figure is used so that the estimate does not understate a large prompt.
BYTES_PER_TOKEN_ESTIMATE = Decimal("3.85")

# Both vocabularies: OpenAI's words and Anthropic's, whichever the runtime passes through.
_FINISH: Mapping[str, StopReason] = {
    "stop": "end",
    "end_turn": "end",
    "tool_calls": "tool_use",
    "tool_use": "tool_use",
    "length": "max_tokens",
    "max_tokens": "max_tokens",
}

# 1 AI unit = 1 AI credit = $0.01; the wire counts nano-AIU: usd = nano * 1E-9 * 0.01.
_USD_EXPONENT = -11
# An integer-valued count of more than this many digits is not a plausible charge; it is left
# unpriced (None), whether written as a JSON integer or as a decimal, rather than expanded.
_MAX_NANO_DIGITS = 39


def event_record(event: Any) -> dict[str, Any]:
    """One SDK session event as the body's ``{"type", "data"}`` object."""
    return {"type": event.type.value, "data": event.data.to_dict()}


def _billed_usd(data: Mapping[str, Any]) -> Decimal | None:
    """The charge from ``copilotUsage.totalNanoAiu``, exact; None when absent, negative,
    non-integer-valued or non-numeric. The experimental ``cost`` field is ignored."""
    usage = data.get("copilotUsage")
    raw = usage.get("totalNanoAiu") if isinstance(usage, dict) else None
    if isinstance(raw, bool) or not isinstance(raw, int | Decimal):
        return None
    if isinstance(raw, Decimal) and (
        not raw.is_finite() or raw != raw.to_integral_value() or raw.adjusted() >= _MAX_NANO_DIGITS
    ):
        return None
    nano = int(raw)
    if nano < 0 or len(str(nano)) > _MAX_NANO_DIGITS:
        return None
    # built from its digits: no context rounding, no float
    return Decimal((0, tuple(int(d) for d in str(nano)), _USD_EXPONENT))


def _events(text: str) -> tuple[list[Any], list[tuple[str, dict[str, Any]]]]:
    try:
        body = load_json(text)
    except TurnError:
        raise _BadReply("reply is not JSON") from None
    if not isinstance(body, list):
        raise _BadReply("reply is not a JSON array of events")
    events: list[tuple[str, dict[str, Any]]] = []
    for item in body:
        kind = item.get("type") if isinstance(item, dict) else None
        data = item.get("data") if isinstance(item, dict) else None
        if not isinstance(kind, str) or not isinstance(data, dict):
            raise _BadReply("an event is not an object with a type and data")
        events.append((kind, data))
    return body, events


def _tool_call(data: Mapping[str, Any], seen: list[Any]) -> ToolCall:
    call_id, name = _id(data, "toolCallId"), _id(data, "toolName")
    if data.get("parentToolCallId") is not None:
        raise _BadReply("sub-agent tool call")
    seen.append(name)
    arguments = data.get("arguments")
    if arguments is None:
        return ToolCall(call_id, name, {})
    if isinstance(arguments, dict):
        seen.append(arguments)
        return ToolCall(call_id, name, arguments)
    try:
        raw = dump_json(arguments)
    except TurnError:
        raise _BadReply("tool arguments cannot be written as JSON") from None
    seen.append(raw)
    return ToolCall(call_id, name, {}, bad_arguments=raw)


def _usage(data: Mapping[str, Any]) -> Usage:
    return Usage(
        input_tokens=_count(data, "inputTokens"),
        cached_read_tokens=_count(data, "cacheReadTokens"),
        cache_write_tokens=_count(data, "cacheWriteTokens"),
        output_tokens=_count(data, "outputTokens"),
        reasoning_tokens=_count(data, "reasoningTokens"),
    )


def _request_id(data: Mapping[str, Any]) -> str | None:
    return _str_or_none(data.get("apiCallId")) or _str_or_none(data.get("providerCallId"))


def _session_error(
    data: Mapping[str, Any],
    usage_data: Mapping[str, Any] | None,
    redactor: Redactor,
    seen: list[Any],
) -> ProviderError:
    parts = [_str_or_none(data.get("errorType")), _str_or_none(data.get("message"))]
    detail = ": ".join(p for p in parts if p)
    seen.append(detail)
    code = data.get("statusCode")
    status = code if isinstance(code, int) and not isinstance(code, bool) else None
    snippet = _snippet(redactor, detail)
    counts = _usage(usage_data) if usage_data is not None else Usage()
    if usage_data is None or counts == Usage():
        return ProviderError(ErrorKind.SENT_CHARGE_UNKNOWN, "SessionError", snippet, status)
    return ProviderError(
        ErrorKind.SENT_CHARGE_USAGE,
        "SessionError",
        snippet,
        status,
        counts,
        _billed_usd(usage_data),
        _str_or_none(usage_data.get("model")),
        _request_id(usage_data),
    )


def parse_events(
    text: str, redactor: Redactor, seen: list[Any], cut_as_turn: bool = False
) -> Turn | ProviderError:
    """The turn one call's session events make. A length-cut reply with no tool call is
    ``ReplyCut`` (CP1H-R16) unless ``cut_as_turn``, which keeps it a max_tokens turn. Raises ``_BadReply`` on a body of the wrong shape."""
    body, events = _events(text)
    seen.append(body)
    usages = [d for k, d in events if k == USAGE]
    errors = [d for k, d in events if k == SESSION_ERROR]
    if len(usages) > 1:
        raise _BadReply("more than one assistant.usage event")
    usage_data = usages[0] if usages else None
    contents: list[str] = []
    for kind, data in events:
        if kind == MESSAGE:
            content = data.get("content")
            if not isinstance(content, str):
                raise _BadReply("an assistant.message content is not a string")
            contents.append(content)
    seen.extend(contents)
    seen.append("".join(contents))
    if errors:
        return _session_error(errors[0], usage_data, redactor, seen)
    if usage_data is None:
        raise _BadReply("no assistant.usage event")
    calls = tuple(_tool_call(d, seen) for k, d in events if k == TOOL_START)
    if len({c.call_id for c in calls}) != len(calls):
        raise _BadReply("duplicate toolCallId")
    finish = usage_data.get("finishReason")
    stop: StopReason = _FINISH.get(finish, "other") if isinstance(finish, str) else "other"
    expected = _count(usage_data, "numToolCalls")
    if expected is not None and expected != len(calls):
        raise _BadReply(f"tool count {len(calls)} differs from numToolCalls {expected}")
    if stop == "tool_use" and expected is None:
        raise _BadReply("tool count unknown")
    if stop == "tool_use" and not calls:
        raise _BadReply("stop reason tool_use with no tool call")
    if calls and stop not in ("tool_use", "max_tokens"):
        raise _BadReply("tool calls without finishReason tool_calls")
    usage = _usage(usage_data)
    model, rid = _str_or_none(usage_data.get("model")), _request_id(usage_data)
    billed = _billed_usd(usage_data)
    if stop == "max_tokens" and not calls and not cut_as_turn:
        detail = "finishReason length or max_tokens"
        return _usage_error(REPLY_CUT, detail, 200, usage, model, rid, billed)
    return Turn("".join(contents), calls, usage, stop, model, rid, 200, billed)


def prompt_tokens_estimate(prompt_bytes: int) -> int:
    """An estimate of the tokens in ``prompt_bytes`` of request (``BYTES_PER_TOKEN_ESTIMATE``)."""
    return math.ceil(Decimal(prompt_bytes) / BYTES_PER_TOKEN_ESTIMATE)


def near_limit(model: str, prompt_tokens: int, output_tokens: int) -> int | None:
    """The model's token limit when ``prompt_tokens`` plus the ``output_tokens`` budget passes the
    share of it at which the runtime starts to summarise; None when it does not, or when the
    model's limit is not known."""
    limit = TOKEN_LIMITS.get(model)
    if limit is None or prompt_tokens + output_tokens <= limit * COMPACTION_SHARE:
        return None
    return limit


def _opt_int(data: Mapping[str, Any], key: str) -> int | None:
    value = data.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _compaction_usd(data: Mapping[str, Any]) -> Decimal | None:
    """The summariser's charge, by the rule the route uses for a call (``_billed_usd``). A
    subtotal the runtime marks ``partial`` or ``unavailable`` is not a charge: None."""
    used = data.get("compactionTokensUsed")
    if not isinstance(used, dict) or used.get("aiCreditsStatus", "complete") != "complete":
        return None
    return _billed_usd(used)


def _compaction(kind: str, data: Mapping[str, Any]) -> Compaction | None:
    attempt = _str_or_none(data.get("compactionAttemptId"))
    limit = _opt_int(data, "tokenLimit")
    if kind == COMPACTION_START:
        return Compaction("start", attempt, _opt_int(data, "currentTokens"), None, limit)
    if kind == COMPACTION_COMPLETE:
        done = data.get("success")
        return Compaction(
            "complete",
            attempt,
            _opt_int(data, "preCompactionTokens"),
            _opt_int(data, "postCompactionTokens"),
            limit,
            done if isinstance(done, bool) else None,
            _compaction_usd(data),
        )
    return None


def compactions(text: str) -> tuple[Compaction, ...]:
    """The context compactions one call's body reports, in order. Raises ``_BadReply`` on a body
    of the wrong shape, as ``parse_events`` does."""
    _, events = _events(text)
    found = (_compaction(kind, data) for kind, data in events)
    return tuple(c for c in found if c is not None)
