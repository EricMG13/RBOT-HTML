"""Minimal fragments of real ``session.compaction_*`` events, copied as literals.

Each is the ``data`` of an event in a retained Copilot run's ``live/raw/<digest>-<call>.json``
(run tdg-full-copilot-sol-high-001-resume, GitHub Copilot runtime, gpt-6.1-sol, effort high),
with the summary text, paths and request ids left out. The expected charges are worked by hand
from each fragment's own ``tokenDetails`` (USD per 1M tokens: input 2.00, cache read 0.10,
cache write 2.50, output 10.00) and from ``totalNanoAiu`` x 1E-11:

CP-8 (call 9):  75 x 2.00 + 240,831 x 0.10 + 1,098 x 2.50 + 7,266 x 10.00, over 1M
                = 0.000150 + 0.0240831 + 0.002745 + 0.07266 = USD 0.0996381
                = 9,963,810,000 nano-AIU x 1E-11
CP-6 (call 7):  75 x 2.00 + 218,361 x 0.10 + 0 x 2.50 + 8,928 x 10.00, over 1M
                = 0.000150 + 0.0218361 + 0 + 0.08928 = USD 0.1112661
                = 11,126,610,000 nano-AIU x 1E-11
"""

from __future__ import annotations

from typing import Any

CP8_USD = "0.0996381"
CP6_USD = "0.1112661"


def _detail(count: int, kind: str, per_batch: int) -> dict[str, Any]:
    return {
        "batchSize": 1000000,
        "costPerBatch": per_batch,
        "tokenCount": count,
        "tokenType": kind,
        "model": "gpt-6.1-sol",
    }


def _used(nano: float, read: int, write: int, out: int) -> dict[str, Any]:
    return {
        "aiCreditsStatus": "complete",
        "cacheReadTokens": read,
        "cacheWriteTokens": write,
        "copilotUsage": {
            "totalNanoAiu": nano,
            "tokenDetails": [
                _detail(75, "input", 200000000000),
                _detail(read, "cache_read", 10000000000),
                _detail(write, "cache_write", 250000000000),
                _detail(out, "output", 1000000000000),
            ],
        },
        "inputTokens": read + write + 75,
        "model": "gpt-6.1-sol",
        "outputTokens": out,
        "requestCount": 1,
    }


# c6f6170f...-1.json, event 9: CP-8's compaction starts at its second call.
START_CP8: dict[str, Any] = {
    "compactionAttemptId": "9adc3933-fffb-4810-a23a-717e91c08200",
    "conversationTokens": 231983,
    "currentTokens": 241349,
    "model": "gpt-6.1-sol",
    "systemTokens": 8237,
    "tokenLimit": 272000,
    "toolDefinitionsTokens": 1129,
    "trigger": "threshold",
}
# c6f6170f...-9.json, event 29: the same compaction completes inside CP-8's call 9.
COMPLETE_CP8: dict[str, Any] = {
    "success": True,
    "compactionAttemptId": "9adc3933-fffb-4810-a23a-717e91c08200",
    "compactionTokensUsed": _used(9963810000.0, 240831, 1098, 7266),
    "outcome": "applied",
    "postCompactionTokens": 42447,
    "preCompactionTokens": 259070,
    "tokenLimit": 272000,
    "tokensRemoved": 216623,
    "trigger": "threshold",
}
# e43ce8b1...-3.json, event 21 (start) and e43ce8b1...-7.json, event 9 (complete): CP-6.
START_CP6: dict[str, Any] = {
    "compactionAttemptId": "e52bf4e7-54c0-4e0e-9cd3-619894a8e37e",
    "conversationTokens": 183760,
    "currentTokens": 217891,
    "model": "gpt-6.1-sol",
    "systemTokens": 33002,
    "tokenLimit": 272000,
    "toolDefinitionsTokens": 1129,
    "trigger": "threshold",
}
COMPLETE_CP6: dict[str, Any] = {
    "success": True,
    "compactionAttemptId": "e52bf4e7-54c0-4e0e-9cd3-619894a8e37e",
    "compactionTokensUsed": _used(11126610000.0, 218361, 0, 8928),
    "outcome": "applied",
    "postCompactionTokens": 72125,
    "preCompactionTokens": 238958,
    "tokenLimit": 272000,
    "tokensRemoved": 166833,
    "trigger": "threshold",
}
# 153e5195...-10.json (medium run, CP-8): a start with no complete in the module.
START_MEDIUM_CP8: dict[str, Any] = {
    "compactionAttemptId": "b60d0d7e-bd47-45ff-98f9-e531a6f7c67f",
    "conversationTokens": 216171,
    "currentTokens": 225537,
    "model": "gpt-6.1-sol",
    "systemTokens": 8237,
    "tokenLimit": 272000,
    "toolDefinitionsTokens": 1129,
    "trigger": "threshold",
}


def without_usage(data: dict[str, Any]) -> dict[str, Any]:
    """A complete event whose usage the runtime did not report."""
    return {k: v for k, v in data.items() if k != "compactionTokensUsed"}


def with_status(data: dict[str, Any], status: str) -> dict[str, Any]:
    used = {**data["compactionTokensUsed"], "aiCreditsStatus": status}
    return {**data, "compactionTokensUsed": used}
