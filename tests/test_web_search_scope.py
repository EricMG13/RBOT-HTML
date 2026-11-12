"""Web search scope: which cases search, the after-the-fact check of what was searched for, and
the citation-marker stripping edges (fix round 1 of the run-page web search)."""

from __future__ import annotations

import json
import time
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from test_handoff_loop import GOOD, Adapter, searched, task, turn

from deploy_workflow.model.handoff import HandoffExecutor, ModuleTools, strip_citation_markers
from deploy_workflow.model.providers import WEB_SEARCH_BLOCK
from deploy_workflow.model.turn import ProviderBlock, ToolCall, hosted_kind
from deploy_workflow.run_events import EVENTS, read_events

OPEN, SEP, CLOSE = "", "", ""
MARK = f"{OPEN}cite{SEP}turn0view0{CLOSE}"


def research(case_kind: str):
    base = task()
    return replace(
        base, module_id="CP-DR", run=base.run.model_copy(update={"case_kind": case_kind})
    )


def run_research(tmp_path: Path, case_kind: str) -> tuple[Adapter, list[dict]]:
    adapter = Adapter(searched(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()}), 1))
    HandoffExecutor(
        tmp_path / "run",
        adapter=adapter,
        cap_usd=Decimal(10),
        check=lambda _t, _r: (),
        events=tmp_path / "ev",
        web_search=True,
    )(research(case_kind))
    return adapter, read_events(tmp_path / "ev" / EVENTS)


def held(events: list[dict]) -> Decimal:
    return Decimal(next(e for e in events if e["event"] == "turn")["held_usd"])


def test_a_synthetic_case_is_not_offered_web_search_and_holds_no_fee(tmp_path: Path) -> None:
    held_for = {}
    for kind in ("public", "private", "synthetic"):
        adapter, events = run_research(tmp_path / kind, kind)
        offered = any(hosted_kind(t) for t in adapter.requests[0].tools)
        assert offered is (kind != "synthetic"), kind
        held_for[kind] = held(events)
    assert held_for["public"] == held_for["private"]
    assert held_for["public"] - held_for["synthetic"] == Decimal("0.16")


def test_a_flagged_query_is_recorded_and_does_not_fail_the_run(tmp_path: Path) -> None:
    leak = {
        "type": "web_search_call",
        "id": "ws_0",
        "status": "completed",
        "action": {
            "type": "search",
            "queries": ["TransDigm peers Revenue 1,234,567 S1.txt", "TransDigm aerospace peers"],
        },
    }
    reply = turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()}))
    assert reply.turn is not None
    reply = replace(
        reply,
        turn=replace(reply.turn, provider_blocks=(ProviderBlock(WEB_SEARCH_BLOCK, leak),)),
    )
    leaking = research("public")
    leaking = replace(leaking, sources={"S1.txt": b"Revenue 1,234,567\nMissing cash"})
    out = HandoffExecutor(
        tmp_path / "run",
        adapter=Adapter(reply),
        cap_usd=Decimal(10),
        check=lambda _t, _r: (),
        events=tmp_path / "ev",
        web_search=True,
    )(leaking)
    assert out == GOOD  # detection, not prevention: the run goes on
    flagged = [
        e for e in read_events(tmp_path / "ev" / EVENTS) if e["event"] == "search_query_flagged"
    ]
    assert [e["query"] for e in flagged] == ["TransDigm peers Revenue 1,234,567 S1.txt"]
    assert {"S1.txt" in e["reason"] or "1234567" in e["reason"] for e in flagged} == {True}
    (record,) = (tmp_path / "run").glob("modules/*/0.queries.json")
    assert len(json.loads(record.read_text())["search_query_flagged"]) == 1


def test_year_and_public_names_are_not_flagged(tmp_path: Path) -> None:
    from deploy_workflow.model.handoff import flag_search_queries

    sources = {"annual.txt": "Sales 2024 were 2,500 and 12,345.6 in 2019."}
    assert flag_search_queries(["TransDigm 2024 peers", "Howmet 2500"], sources) == [
        ("Howmet 2500", "possible leak: figure 2500 occurs in this run's source text")
    ]
    assert flag_search_queries(["peers of annual"], sources) == [
        ("peers of annual", "possible leak: source file name annual.txt")
    ]
    assert flag_search_queries(["TransDigm 2024 2019 peers", "12 345", "7,777"], sources) == []


def test_a_marker_never_spans_lines() -> None:
    text = f"Revenue {OPEN} was 1,234.\n| EBITDA | 567 |\nok {CLOSE} tail"
    assert strip_citation_markers(text) == (text, 0)


def test_stripping_is_linear_on_long_whitespace() -> None:
    start = time.perf_counter()
    out, n = strip_citation_markers(" " * 80_000 + "x " + MARK)
    assert n == 1 and out == " " * 80_000 + "x"
    assert time.perf_counter() - start < 2


def test_many_unclosed_openers_are_linear() -> None:
    start = time.perf_counter()
    text = (OPEN + "a" * 20) * 3000 + "z" * 60_000 + " x" + MARK
    strip_citation_markers(text)
    assert time.perf_counter() - start < 2


def test_the_model_is_told_how_many_markers_were_removed_and_may_quote_its_own_text(
    tmp_path: Path,
) -> None:
    marked = GOOD.decode().replace("100\n", f"100 is the figure{MARK} here\n", 1)
    tools = ModuleTools(
        replace(task(), module_id="CP-DR"), tmp_path, lambda _t, _r: ("no",), strip_markers=True
    )
    first = tools.write_handoff(marked)
    assert "1 citation marker was removed" in first
    result = tools.edit_handoff([{"old": f"figure{MARK} here", "new": "figure here."}])
    assert not result.startswith("ERROR")


@pytest.mark.parametrize("who", ["citeturn0image0", "citeturn0fetch1", "cite turn0view0"])
def test_check_9_catches_other_marker_shapes(who: str) -> None:
    from deploy_workflow.prose_checks import prose_issues

    doc = f"# H\n\n## Findings\n\n### Bottom line\n\nLeverage is lower {who} here.\n"
    assert any("Prose check 9" in i for i in prose_issues(doc))


def test_check_9_refuses_only_the_providers_delimiters_and_anywhere_in_the_handoff() -> None:
    from deploy_workflow.prose_checks import prose_issues

    head = "# H\n\n## Findings\n\n### Bottom line\n\nLeverage is lower.\n\n"
    other = prose_issues(head + "Icon  and  glyphs.\n")
    assert not any("Prose check 9" in i for i in other)
    for ch in (OPEN, CLOSE, SEP):
        assert any("Prose check 9" in i for i in prose_issues(head + f"## Gaps\n\nPeer {ch} x\n"))
        assert any("Prose check 9" in i for i in prose_issues(head + f"| a {ch} | b |\n"))


def instructions(tmp_path: Path, **kwargs: bool) -> str:
    adapter = Adapter(searched(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()}), 1))
    HandoffExecutor(
        tmp_path,
        adapter=adapter,
        cap_usd=Decimal(10),
        check=lambda _t, _r: (),
        **kwargs,
    )(research("public"))
    return adapter.requests[0].messages[0].text


def test_the_source_guidance_is_in_a_searching_cp_dr_and_absent_without_search(
    tmp_path: Path,
) -> None:
    on = instructions(tmp_path / "on", web_search=True)
    off = instructions(tmp_path / "off")
    for phrase in ("Rely primarily on reputable sources", "go to the original", "Source type"):
        assert phrase in on
        assert phrase not in off


def test_a_web_source_row_without_a_source_type_is_refused() -> None:
    from deploy_workflow.model.handoff import web_source_issues

    good = (
        "## Sources\n| Source | URL | Source type |\n|---|---|---|\n"
        "| S2 | https://x.org | Rating agency |\n## Findings\n"
    )
    bare = good.replace("Rating agency", "unknown")
    assert web_source_issues(good) == []
    assert len(web_source_issues(bare)) == 1
    assert web_source_issues("## Sources\n| S1 | file.txt |\n## Findings\n") == []
    assert web_source_issues("## Findings\n| a | https://x |\n") == []
