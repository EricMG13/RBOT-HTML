"""The table reader's refusals name the line and the fault, so a model can fix its draft."""

from pathlib import Path

import pytest

from deploy_workflow.handoff_delivery import table, table_faults

HEAD = "| A | B | C | D | E | F | G |"
SEP7 = "|---|---|---|---|---|---|---|"
SEP8 = "|---|---|---|---|---|---|---|---|"
ROW = "| 1 | 2 | 3 | 4 | 5 | 6 | 7 |"


def refusal(*lines: str, start: int = 231) -> str:
    with pytest.raises(ValueError) as caught:
        table([(start + i, text) for i, text in enumerate(lines)])
    return str(caught.value)


def test_header_and_separator_cell_counts_are_named_at_the_header_line() -> None:
    message = refusal(HEAD, SEP8, ROW)
    assert message.startswith("Invalid Markdown table header")
    assert "line 231" in message
    assert "7 cells" in message
    assert "separator row has 8" in message
    assert "| A | B | C" in message


def test_separator_that_is_not_dashes_is_named() -> None:
    message = refusal(HEAD, ROW, ROW)
    assert message.startswith("Invalid Markdown table header")
    assert "line 231" in message
    assert "not made of ---" in message


def test_row_with_wrong_cell_count_names_its_line_and_counts() -> None:
    message = refusal(HEAD, SEP7, ROW, "| 1 | 2 |", start=40)
    assert message.startswith("Markdown table row does not match its header")
    assert "line 43" in message
    assert "2 cells" in message
    assert "7" in message


def test_row_with_empty_first_cell_names_its_line() -> None:
    message = refusal(HEAD, SEP7, "|  | 2 | 3 | 4 | 5 | 6 | 7 |", start=40)
    assert message.startswith("Markdown table row does not match its header")
    assert "line 42" in message
    assert "first cell is empty" in message


def test_missing_closing_pipe_names_its_line() -> None:
    message = refusal(HEAD, SEP7, "| 1 | 2 | 3", start=40)
    assert message.startswith("Markdown table rows require both boundary pipes")
    assert "line 42" in message


def test_too_short_table_names_its_first_line() -> None:
    message = refusal(HEAD, SEP7, start=12)
    assert message.startswith("Expected a populated Markdown table")
    assert "line 12" in message


def test_no_table_keeps_the_plain_message() -> None:
    assert refusal() == "Expected a populated Markdown table"


LIVE = Path(__file__).parent / "fixtures" / "live_2026_11_15"
# Live 2026-11-15, copilot-sol-medium, TDG FY2024: (header line, header cells, separator cells).
LIVE_FAULTS = {
    "earnings_update-CP-1-draft1.md": ((323, 4, 5), (382, 7, 8)),
    "relative_value-CP-1-draft1.md": ((278, 7, 8), (325, 17, 18)),
    "distressed-CP-1-draft1.md": ((222, 5, 6), (258, 5, 6)),
}


@pytest.mark.parametrize("name", sorted(LIVE_FAULTS))
def test_every_malformed_table_of_a_rejected_draft_is_listed_once(name: str) -> None:
    faults = table_faults((LIVE / name).read_text(encoding="utf-8"))
    assert len(faults) == 2
    for fault, (line, head, sep) in zip(faults, LIVE_FAULTS[name], strict=True):
        assert fault.startswith(f"Invalid Markdown table header at line {line}: ")
        assert f"the header has {head} cells and the separator row has {sep}" in fault


def test_the_accepted_draft_has_no_table_fault() -> None:
    accepted = LIVE / "earnings_update-CP-1-draft3-accepted.md"
    assert table_faults(accepted.read_text(encoding="utf-8")) == ()


def test_each_body_row_with_the_wrong_cell_count_is_listed_and_a_fence_is_not_a_table() -> None:
    bad_rows = f"{HEAD}\n{SEP7}\n{ROW}\n| 1 | 2 |\n{ROW}\n| 1 |\n"  # lines 4 and 6 are short
    text = f"{bad_rows}\n```\n{HEAD}\n{SEP8}\n```\n"  # the fenced pair is not a table
    faults = table_faults(text)
    assert [f.split(" at line ")[1][:1] for f in faults] == ["4", "6"]
    assert all(f.startswith("Markdown table row does not match its header") for f in faults)


def test_a_lone_pipe_line_and_a_table_inside_a_comment_are_not_faults() -> None:
    assert table_faults("| only one line |\n\ntext") == ()
    assert table_faults(f"<!--\n{HEAD}\n{SEP8}\n{ROW}\n-->\n") == ()


def test_orphan_rows_after_a_blank_line_say_a_blank_line_splits_a_table() -> None:
    text = f"{HEAD}\n{SEP7}\n{ROW}\n\n{ROW}\n{ROW}\n"
    (fault,) = table_faults(text)
    assert fault.startswith("Invalid Markdown table header at line 5: the second row is not made")
    assert fault.endswith("(a blank line splits a table: remove it, or give these rows their own "
                          "header and separator)")  # fmt: skip


def test_prose_lines_starting_with_a_pipe_and_lacking_a_closing_pipe_are_not_a_table() -> None:
    assert table_faults("|ΔEBITDA| rose by two\n|ΔLeverage| fell by one\n") == ()


def test_a_table_lists_its_faults_in_line_order() -> None:
    faults = table_faults(f"{HEAD}\n{SEP8}\n| 1 | 2 |\n")
    assert [f.split(" at line ")[1][:1] for f in faults] == ["1", "3"]
