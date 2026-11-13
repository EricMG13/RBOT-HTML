"""Copilot session events -> Turn. Bodies are JSON arrays of {"type", "data"} events."""

import json
import uuid
from decimal import Decimal
from typing import Any

from deploy_workflow.model.copilot import event_record
from deploy_workflow.model.providers import ErrorKind, ProviderError, parse
from deploy_workflow.model.redact import Redactor
from deploy_workflow.model.turn import ToolCall, Turn, Usage, dump_json

TEXT_TURN = Turn(
    "done",
    (),
    Usage(
        input_tokens=12,
        cached_read_tokens=4,
        cache_write_tokens=0,
        output_tokens=7,
        reasoning_tokens=2,
    ),
    "end",
    "gpt-6.1-sol",
    "api-1",
    200,
    billed_usd=Decimal("0.000123"),
)


def usage(**extra: Any) -> dict[str, Any]:
    return {
        "type": "assistant.usage",
        "data": {"model": "gpt-6.1-sol", "inputTokens": 1, "outputTokens": 2, **extra},
    }


def message(content: str) -> dict[str, Any]:
    return {"type": "assistant.message", "data": {"content": content}}


def start(call_id: str, name: str, arguments: Any) -> dict[str, Any]:
    return {
        "type": "tool.execution_start",
        "data": {"toolCallId": call_id, "toolName": name, "arguments": arguments},
    }


def run(*events: dict[str, Any]) -> Turn | ProviderError:
    return parse("copilot", 200, json.dumps(list(events)).encode(), {}, Redactor())


def turn(*events: dict[str, Any]) -> Turn:
    result = run(*events)
    assert isinstance(result, Turn), result
    return result


def error(*events: dict[str, Any]) -> ProviderError:
    result = run(*events)
    assert isinstance(result, ProviderError), result
    return result


def test_text_turn() -> None:
    result = turn(
        usage(
            inputTokens=12,
            cacheReadTokens=4,
            cacheWriteTokens=0,
            outputTokens=7,
            reasoningTokens=2,
            copilotUsage={"totalNanoAiu": 12300000},
            cost=0.5,
            finishReason="stop",
            apiCallId="api-1",
        ),
        message("done"),
        {"type": "session.idle", "data": {}},
    )
    assert result == TEXT_TURN


def test_tool_turn() -> None:
    result = turn(
        usage(finishReason="tool_calls", numToolCalls=2),
        start("c1", "read", {"p": 1}),
        start("c2", "write", {}),
    )
    assert result.stop_reason == "tool_use"
    assert result.tool_calls == (ToolCall("c1", "read", {"p": 1}), ToolCall("c2", "write", {}))
    assert result.text == ""


def test_non_object_arguments_are_bad_arguments() -> None:
    result = turn(usage(finishReason="tool_calls", numToolCalls=1), start("c1", "read", "[1,2]"))
    assert result.tool_calls == (ToolCall("c1", "read", {}, bad_arguments='"[1,2]"'),)


def test_tool_count_mismatch_is_unparsable() -> None:
    result = error(
        usage(finishReason="tool_calls", numToolCalls=1),
        start("c1", "a", {}),
        start("c2", "b", {}),
    )
    assert result.error_class == "UnparsableReply"
    assert result.kind is ErrorKind.SENT_CHARGE_UNKNOWN


def test_tool_calls_without_count_are_unparsable() -> None:
    result = error(usage(finishReason="tool_calls"), start("c1", "a", {}))
    assert result.error_class == "UnparsableReply"


def test_usage_without_cost_has_no_billed_usd() -> None:
    assert turn(usage(cost=0.5)).billed_usd is None
    assert turn(usage(copilotUsage={"totalNanoAiu": 0})).billed_usd == Decimal(0)
    for bad in ("12300000.5", "-1", '"12300000"'):
        body = '[{"type":"assistant.usage","data":{"copilotUsage":{"totalNanoAiu":' + bad + "}}}]"
        result = parse("copilot", 200, body.encode(), {}, Redactor())
        assert isinstance(result, Turn)
        assert result.billed_usd is None
    whole = '[{"type":"assistant.usage","data":{"copilotUsage":{"totalNanoAiu":12300000.0}}}]'
    result = parse("copilot", 200, whole.encode(), {}, Redactor())
    assert isinstance(result, Turn)
    assert result.billed_usd == Decimal("0.000123")


def test_nano_aiu_keeps_its_digits() -> None:
    # synthetic-body scope: the SDK types the field as float; a live value is exact only below 2**53
    result = turn(usage(copilotUsage={"totalNanoAiu": 123456789012345678}))
    assert result.billed_usd == Decimal("1234567.89012345678")


def test_key_split_across_messages_is_reflected() -> None:
    key = "ghp_" + "A" * 36
    result = error(message(key[:24]), message(key[24:]), usage())
    assert result.error_class == "KeyReflected"


def test_key_in_event_text_is_reflected() -> None:
    result = error(message("see ghp_" + "A" * 36), usage())
    assert result.error_class == "KeyReflected"


def test_two_usage_events_are_unparsable() -> None:
    assert error(usage(), usage()).error_class == "UnparsableReply"


def test_no_usage_is_unparsable() -> None:
    assert error(message("hi")).error_class == "UnparsableReply"


def test_not_a_list_is_unparsable() -> None:
    result = parse("copilot", 200, b"{}", {}, Redactor())
    assert isinstance(result, ProviderError)
    assert result.error_class == "UnparsableReply"


def test_session_error_with_usage_is_sent_usage() -> None:
    err = {
        "type": "session.error",
        "data": {"errorType": "provider", "message": "upstream 503", "statusCode": 503},
    }
    result = error(usage(outputTokens=9), err)
    assert result.kind is ErrorKind.SENT_CHARGE_USAGE
    assert result.error_class == "SessionError"
    assert result.http_status == 503
    assert result.usage is not None
    assert result.usage.output_tokens == 9
    assert "upstream 503" in result.message
    assert error(err).kind is ErrorKind.SENT_CHARGE_UNKNOWN


def test_length_without_calls_is_reply_cut() -> None:
    result = error(usage(finishReason="length", outputTokens=9, apiCallId="a1"))
    assert result.error_class == "ReplyCut"
    assert result.kind is ErrorKind.SENT_CHARGE_USAGE
    assert result.usage is not None
    assert result.usage.output_tokens == 9
    assert result.request_id == "a1"
    body = json.dumps([usage(finishReason="length")]).encode()
    cut = parse("copilot", 200, body, {}, Redactor(), cut_as_turn=True)
    assert isinstance(cut, Turn)
    assert cut.stop_reason == "max_tokens"


def test_length_with_calls_is_a_max_tokens_turn() -> None:
    result = turn(usage(finishReason="length", numToolCalls=1), start("c1", "a", {}))
    assert result.stop_reason == "max_tokens"
    assert len(result.tool_calls) == 1


def test_calls_under_stop_are_unparsable() -> None:
    for extra in ({"finishReason": "stop"}, {"finishReason": "stop", "numToolCalls": 1}, {}):
        assert error(usage(**extra), start("c1", "a", {})).error_class == "UnparsableReply"


def test_anthropic_finish_words() -> None:
    assert turn(usage(finishReason="end_turn")).stop_reason == "end"
    result = turn(usage(finishReason="tool_use", numToolCalls=1), start("c1", "a", {}))
    assert result.stop_reason == "tool_use"
    assert error(usage(finishReason="max_tokens")).error_class == "ReplyCut"


def test_duplicate_tool_call_id_is_unparsable() -> None:
    result = error(
        usage(finishReason="tool_calls", numToolCalls=2), start("c", "a", {}), start("c", "b", {})
    )
    assert result.error_class == "UnparsableReply"


def test_absent_arguments_are_empty() -> None:
    absent = {"type": "tool.execution_start", "data": {"toolCallId": "c1", "toolName": "a"}}
    for event in (absent, start("c1", "a", None)):
        result = turn(usage(finishReason="tool_calls", numToolCalls=1), event)
        assert result.tool_calls == (ToolCall("c1", "a", {}),)


def test_sub_agent_start_is_unparsable() -> None:
    sub = start("c1", "a", {})
    sub["data"]["parentToolCallId"] = "p1"
    result = error(usage(finishReason="tool_calls", numToolCalls=1), sub)
    assert result.error_class == "UnparsableReply"


def test_non_string_content_is_unparsable() -> None:
    for content in (["a"], {"t": 1}, None, 7):
        result = error(
            message("kept"), {"type": "assistant.message", "data": {"content": content}}, usage()
        )
        assert result.error_class == "UnparsableReply"


def test_usage_without_counts_makes_error_unknown() -> None:
    err = {"type": "session.error", "data": {"errorType": "x", "message": "m"}}
    bare = {"type": "assistant.usage", "data": {"model": "m"}}
    assert error(bare, err).kind is ErrorKind.SENT_CHARGE_UNKNOWN


def test_nano_aiu_above_the_digit_cap_is_unpriced() -> None:
    assert turn(usage(copilotUsage={"totalNanoAiu": 10**45})).billed_usd is None


def test_real_sdk_events_round_trip() -> None:
    from copilot.generated.session_events import SessionEvent

    def ev(kind: str, data: dict[str, Any]) -> Any:
        return SessionEvent.from_dict(
            {
                "id": str(uuid.uuid4()),
                "timestamp": "2026-11-06T10:00:00.000Z",
                "type": kind,
                "data": data,
            }
        )

    events = [
        ev(
            "assistant.usage",
            {
                "model": "gpt-6.1-sol",
                "inputTokens": 12,
                "cacheReadTokens": 4,
                "cacheWriteTokens": 0,
                "outputTokens": 7,
                "reasoningTokens": 2,
                "copilotUsage": {"totalNanoAiu": 12300000, "tokenDetails": []},
                "cost": 0.5,
                "finishReason": "stop",
                "apiCallId": "api-1",
            },
        ),
        ev("assistant.message", {"content": "done", "messageId": "m1"}),
        ev("session.idle", {}),
    ]
    body = dump_json([event_record(e) for e in events]).encode()
    result = parse("copilot", 200, body, {}, Redactor())
    assert result == TEXT_TURN


def test_unknown_finish_reason_is_other() -> None:
    assert turn(usage(finishReason="content_filter")).stop_reason == "other"
    assert turn(usage()).stop_reason == "other"


# ---------------------------------------------------------------- compaction events (T3)


def _body(*events: dict[str, Any]) -> str:
    return json.dumps(list(events))


def _event(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"type": kind, "data": data}


def test_a_compaction_start_is_read_from_the_runtimes_own_fields() -> None:
    from deploy_workflow.model.copilot import compactions
    from deploy_workflow.model.turn import Compaction
    from tests.model._compaction import START_CP8

    found = compactions(_body(_event("session.compaction_start", START_CP8)))
    assert found == (
        Compaction(
            kind="start",
            attempt_id="9adc3933-fffb-4810-a23a-717e91c08200",
            tokens_before=241349,
            token_limit=272000,
        ),
    )


def test_a_completed_compaction_carries_its_tokens_and_its_charge() -> None:
    from deploy_workflow.model.copilot import compactions
    from deploy_workflow.model.turn import Compaction
    from tests.model._compaction import COMPLETE_CP6, COMPLETE_CP8, CP6_USD, CP8_USD

    # The charge is the runtime's totalNanoAiu (a JSON float on the wire) x 1E-11; the expected
    # amounts were summed by hand from each fragment's tokenDetails (see _compaction.py).
    cp8 = compactions(_body(_event("session.compaction_complete", COMPLETE_CP8)))
    assert cp8 == (
        Compaction(
            kind="complete",
            attempt_id="9adc3933-fffb-4810-a23a-717e91c08200",
            tokens_before=259070,
            tokens_after=42447,
            token_limit=272000,
            success=True,
            usd=Decimal(CP8_USD),
            usage_reported=True,
            request_count=1,
        ),
    )
    (cp6,) = compactions(_body(_event("session.compaction_complete", COMPLETE_CP6)))
    assert cp6.usd == Decimal(CP6_USD) and cp6.tokens_before == 238958 and cp6.tokens_after == 72125


def test_other_events_and_a_body_with_no_compaction_give_nothing() -> None:
    from deploy_workflow.model.copilot import compactions

    assert compactions(_body(usage(), message("x"))) == ()


def test_a_completed_compaction_with_no_readable_charge_has_no_usd() -> None:
    """Never a zero: an absent usage, a partial or unavailable subtotal, a negative or fractional
    count and a boolean are each an unknown charge."""
    from deploy_workflow.model.copilot import compactions
    from tests.model._compaction import COMPLETE_CP8, with_status, without_usage

    def charge(data: dict[str, Any]) -> Decimal | None:
        (found,) = compactions(_body(_event("session.compaction_complete", data)))
        assert found.kind == "complete"
        return found.usd

    def with_nano(value: Any) -> dict[str, Any]:
        used = {**COMPLETE_CP8["compactionTokensUsed"]}
        used["copilotUsage"] = {"totalNanoAiu": value}
        return {**COMPLETE_CP8, "compactionTokensUsed": used}

    assert charge(without_usage(COMPLETE_CP8)) is None
    assert charge(with_status(COMPLETE_CP8, "partial")) is None
    assert charge(with_status(COMPLETE_CP8, "unavailable")) is None
    assert charge(with_nano(-1)) is None
    assert charge(with_nano(12.5)) is None
    assert charge(with_nano(True)) is None
    assert charge(with_nano(0)) == Decimal(0)  # a reported zero is a zero


def test_a_failed_compaction_is_not_a_success() -> None:
    from deploy_workflow.model.copilot import compactions
    from tests.model._compaction import COMPLETE_CP8

    failed = {**COMPLETE_CP8, "success": False}
    (found,) = compactions(_body(_event("session.compaction_complete", failed)))
    assert found.success is False


def test_a_malformed_body_is_refused() -> None:
    import pytest

    from deploy_workflow.model.copilot import compactions
    from deploy_workflow.model.providers import _BadReply

    with pytest.raises(_BadReply):
        compactions('{"not": "an array"}')


def test_the_same_completion_delivered_twice_is_one_compaction() -> None:
    from deploy_workflow.model.copilot import compactions
    from tests.model._compaction import COMPLETE_CP6, COMPLETE_CP8

    twice = _body(
        _event("session.compaction_complete", COMPLETE_CP8),
        _event("session.compaction_complete", COMPLETE_CP8),
        _event("session.compaction_complete", COMPLETE_CP6),
    )
    assert [c.attempt_id[:8] for c in compactions(twice)] == ["9adc3933", "e52bf4e7"]


def test_a_complete_says_whether_its_usage_block_and_request_count_were_reported() -> None:
    from deploy_workflow.model.copilot import compactions
    from tests.model._compaction import COMPLETE_CP8, without_usage

    (real,) = compactions(_body(_event("session.compaction_complete", COMPLETE_CP8)))
    assert real.usage_reported is True and real.request_count == 1
    (bare,) = compactions(_body(_event("session.compaction_complete", without_usage(COMPLETE_CP8))))
    assert bare.usage_reported is False and bare.request_count is None
    used = {**COMPLETE_CP8["compactionTokensUsed"], "requestCount": 3}
    (many,) = compactions(
        _body(_event("session.compaction_complete", {**COMPLETE_CP8, "compactionTokensUsed": used}))
    )
    assert many.request_count == 3
