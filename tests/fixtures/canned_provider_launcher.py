"""The real launcher (`deploy_workflow.owners.cpos_launch`), with the provider call replaced by the
suite's canned module answers. No network and no spend: the watcher's tests start it in place of
the launcher to join drop, launch, CP-OS, delivery, filing and the library in one journey."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_cpos_launch import answer

from deploy_workflow.model.adapter import AdapterReply, LiveAdapter
from deploy_workflow.model.turn import ToolCall, Turn, Usage
from deploy_workflow.owners import cpos_launch


def main(argv: list[str]) -> int:
    def given(flag: str) -> Path:
        return Path(argv[argv.index(flag) + 1])

    preview = Path(tempfile.mkdtemp()) / "preview"
    prepared = cpos_launch.prepare(
        given("--context"), given("--sources"), preview, config="sol-medium", cap="50"
    )
    routes = list(prepared.layout.routes)

    def complete(_adapter: LiveAdapter, request: Any, **_: Any) -> AdapterReply:
        context = json.loads(request.messages[1].text)
        usage = Usage(
            input_tokens=10,
            cached_read_tokens=0,
            cache_write_tokens=0,
            output_tokens=5,
            reasoning_tokens=0,
        )
        call = ToolCall("1", "write_handoff", {"markdown": answer(context, routes)})
        turn = Turn("", (call,), usage, "tool_use", "fake", "fake", 200)
        return AdapterReply("ok", turn, None, 200, None, None, 1, 2, usage)

    with mock.patch.object(LiveAdapter, "complete", complete):
        return cpos_launch.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
