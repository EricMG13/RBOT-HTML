"""The Reader summary tables of an earlier-format handoff, as the library reads them."""

from deploy_workflow.reader_summary import reader_tables

EARLIER = """# Example

## Findings

### Reader summary

| Bottom line | Confidence | Main limitation |
| --- | --- | --- |
| Cover supports the credit. | Medium | Liquidity not supplied. |

| Finding | Creditor impact | Confidence |
| --- | --- | --- |
| Net debt was 7,940. | Limits new debt. | High |

### Detail

| Not | Read |
| --- | --- |
| a | table |
"""


def test_the_two_summary_tables_are_read_with_their_headers() -> None:
    assert reader_tables(EARLIER) == [
        [
            ["Bottom line", "Confidence", "Main limitation"],
            ["Cover supports the credit.", "Medium", "Liquidity not supplied."],
        ],
        [
            ["Finding", "Creditor impact", "Confidence"],
            ["Net debt was 7,940.", "Limits new debt.", "High"],
        ],
    ]


def test_windows_line_endings_do_not_hide_the_section() -> None:
    assert len(reader_tables(EARLIER.replace("\n", "\r\n"))) == 2


def test_a_missing_or_repeated_heading_gives_no_tables() -> None:
    assert reader_tables("## Findings\n\nNothing.\n") == []
    assert reader_tables(EARLIER + "\n### Reader summary\n\n| A |\n| - |\n| b |\n") == []
