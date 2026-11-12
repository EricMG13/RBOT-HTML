"""Provider citation markers in a searching module's answer (paid test tdg-cpdr-web-001).

Answer keys are written by hand. The marker text is copied from the CP-DR handoff that run
delivered (U+E200 "cite" U+E202 "turn..." U+E201, written here as escapes); nothing is produced
by the code under test.
"""

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from test_handoff_loop import Adapter, searched, task

from deploy_workflow.model.handoff import HandoffExecutor, ModuleTools, strip_citation_markers
from deploy_workflow.model.turn import ToolCall
from deploy_workflow.owners.cpos import HandoffTask
from deploy_workflow.prose_checks import prose_issues
from deploy_workflow.run_events import EVENTS, read_events

MARKER_THREE = "citeturn123066view0turn812501view4turn812501view5"
MARKER_TWO = "citeturn123066view1turn765907view4"
HEAD = "## Request\nTDG\n## Sources\nS1\n## Findings\n"
TAIL = "## Calculations\nNone\n## Gaps\nNone\n## Next module\ndelivery\n"
LEAKED = (
    HEAD
    + f"Primary corporate release. {MARKER_THREE} | Howmet; unaudited\n"
    + f"Peers report it {MARKER_TWO}.\n"
    + f"Both agree {MARKER_TWO} {MARKER_THREE} and so on\n"
    + f"Ends here {MARKER_TWO}\n"
    + f"Touching.{MARKER_TWO}Next word\n"
    + "Two  spaces stay, and the word cite and turn stay: cite the turn.\n"
    + TAIL
)
CLEANED = (
    HEAD
    + "Primary corporate release. | Howmet; unaudited\n"
    + "Peers report it.\n"
    + "Both agree and so on\n"
    + "Ends here\n"
    + "Touching.Next word\n"
    + "Two  spaces stay, and the word cite and turn stay: cite the turn.\n"
    + TAIL
)


def only_cleaned(_task: HandoffTask, raw: bytes) -> tuple[str, ...]:
    return () if raw == CLEANED.encode() else ("marker or whitespace left behind",)


def test_a_searching_module_loses_citation_markers_and_the_count_is_recorded(
    tmp_path: Path,
) -> None:
    research = replace(task(), module_id="CP-DR")
    call = ToolCall("w", "write_handoff", {"markdown": LEAKED})
    loop = HandoffExecutor(
        tmp_path / "run",
        adapter=Adapter(searched(call, searches=1)),
        cap_usd=Decimal(10),
        check=only_cleaned,
        events=tmp_path / "events",
        web_search=True,
    )
    assert loop(research) == CLEANED.encode()
    assert call.arguments["markdown"] == LEAKED  # the provider's answer is not edited
    (counts,) = (tmp_path / "run").glob("modules/*/1.markers.json")
    assert json.loads(counts.read_text()) == {"citation_markers_removed": 6}
    (event,) = [
        e
        for e in read_events(tmp_path / "events" / EVENTS)
        if e["event"] == "citation_markers_removed"
    ]
    assert (event["module"], event["count"]) == ("CP-DR", 6)


def test_a_module_that_is_not_searching_is_not_edited(tmp_path: Path) -> None:
    tools = ModuleTools(task(), tmp_path, only_cleaned)
    tools.write_handoff(LEAKED)
    assert tools.draft == LEAKED.encode()
    assert not list(tmp_path.glob("*.markers.json"))


def test_ordinary_text_with_cite_or_turn_is_untouched() -> None:
    plain = "Analysts cite the turn of the year; a turn123view0 token is not a marker.\n"
    assert strip_citation_markers(plain) == (plain, 0)


READER = "# H\n\n## Findings\n\n### Bottom line\n\n{}\n"


def test_a_private_use_character_in_a_reader_passage_is_refused() -> None:
    (issue,) = prose_issues(READER.format("Leverage is lower. It is stable."))
    assert issue == (
        'Prose check 9 (no provider citation marker), line 7: "U+E200" — remove the marker; '
        "put the source in the paragraph's Basis line."
    )


def test_a_plain_citeturn_pattern_in_a_reader_passage_is_refused() -> None:
    (issue,) = prose_issues(READER.format("Leverage is lower citeturn0search3 and stable."))
    assert issue == (
        'Prose check 9 (no provider citation marker), line 7: "citeturn0search3" — remove the '
        "marker; put the source in the paragraph's Basis line."
    )


def test_ordinary_cite_and_turn_words_pass_the_prose_check() -> None:
    assert prose_issues(READER.format("Analysts cite the turn of the year as the low.")) == ()
