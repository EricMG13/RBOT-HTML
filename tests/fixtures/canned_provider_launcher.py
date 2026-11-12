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
from test_cpos_launch import AS_OF, ISSUER, covenant_answer

from deploy_workflow.model.adapter import AdapterReply, LiveAdapter
from deploy_workflow.model.turn import ToolCall, Turn, Usage
from deploy_workflow.owners import cpos_launch


def cp8_answer(context: dict, out: Path) -> str:
    """CP-8's canned answer: the registers written from the comparison pack CP-OS pinned (the file
    `inputs/<sha256>` the run folder holds, named by the `changes.json` source's hash), as a model
    that read the pack would write them. The checker stays the real one."""
    pack = json.loads((out / "inputs" / context["sources"]["changes.json"]).read_text())

    def shown(side: dict, unit: str) -> str:
        joined = f"{side['value']}{unit}" if unit in ("x", "%") else f"{side['value']} {unit}"
        return f"{joined} ({side['period']})"

    issuer = []
    for m in pack["measures"]:
        if m["difference"] is None:
            continue
        effect = (
            f"The pack's difference is {m['difference']}."
            if m["comparable"] == "yes"
            else "Not comparable: the definitions differ."
        )
        before, now = shown(m["prior"], m["unit"]), shown(m["current"], m["unit"])
        issuer.append(f"| {m['label']} | {before} | {now} | New period | {effect} |")
    issuer = issuer or [
        "| No material change | — | — | None | The comparison pack shows no comparable change. |"
    ]
    analysis = [
        f"| Module ({m['module']}) | "
        + (
            "Unchanged | None | Nothing differs."
            if m["ran_prior"] and m["ran_current"]
            else "New | Method change | It did not run before."
            if m["ran_current"]
            else "Not run this time | Method change | It did not run now."
        )
        + " |"
        for m in pack["modules"]
    ]
    earlier, current = pack["limitations"]["earlier"], pack["limitations"]["current"]
    ledger = [
        *(
            [
                (
                    f"| {', '.join(row['ref'] for row in earlier)} | — "
                    "| The earlier run's limitations are no longer stated. | No longer stated | — |"
                )
            ]
            if earlier
            else []
        ),
        *(f"| — | {row['ref']} | {row['text']} | New | — |" for row in current),
    ]
    lines = ["# CP-8", "", "## Request", f"{ISSUER} as of {AS_OF}.", "", "## Sources", ""]
    lines += [f"- {n} {h}" for n, h in context["sources"].items()]
    lines += [f"- {n} {h['sha256']}" for n, h in context["handoffs"].items()]
    lines += [
        *("", "## Findings", "", "### Bottom line", ""),
        "The credit picture is about the same as in the earlier run, so creditors' position holds.",
        *("", "### Key findings", "", "The comparison pack lists what moved, and nothing more."),
        *("", "### Contrary evidence and what would change the view", ""),
        "Nothing in the comparison contradicts the view.",
        *("", "### Limitations", "", "- The earlier run's wording is compared in substance only."),
        *("", "### What changed: the issuer", ""),
        "| Measure or fact | Earlier | Current | Cause | Effect on the credit view |",
        "| --- | --- | --- | --- | --- |",
        *issuer,
        *("", "### What changed: the analysis", "", "| Module | Status | Cause | Why |"),
        "| --- | --- | --- | --- |",
        *analysis,
        *("", "### Limitations ledger", ""),
        "| Earlier ref | Current ref | Limitation | Status | What closed it |",
        "| --- | --- | --- | --- | --- |",
        *ledger,
        *("", "## Calculations", "", "None.", "", "## Gaps", "", "None.", "", "## Next module"),
        *("", "None.", ""),
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    def given(flag: str) -> Path:
        return Path(argv[argv.index(flag) + 1])

    out = given("--out")
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
        text = (
            cp8_answer(context, out)
            if context["module_id"] == "CP-8"
            else covenant_answer(context, routes)
        )
        call = ToolCall("1", "write_handoff", {"markdown": text})
        turn = Turn("", (call,), usage, "tool_use", "fake", "fake", 200)
        return AdapterReply("ok", turn, None, 200, None, None, 1, 2, usage)

    with mock.patch.object(LiveAdapter, "complete", complete):
        return cpos_launch.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
