"""The table reader's refusals name the line and the fault, so a model can fix its draft."""

import pytest

from deploy_workflow.handoff_delivery import table

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
