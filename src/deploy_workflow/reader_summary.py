"""Read the Reader summary tables of an earlier-format handoff (the library still shows them)."""

import re

HEADING = re.compile(r"^### Reader summary[ \t]*$", re.MULTILINE)
NEXT_HEADING = re.compile(r"^#{2,3} ", re.MULTILINE)
TABLES = (
    ("Bottom line", "Confidence", "Main limitation"),
    ("Finding", "Creditor impact", "Confidence"),
)


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:-1])]


def _tables(section: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    in_table = False
    for line in section.splitlines():
        is_row = line.lstrip().startswith("|") and line.rstrip().endswith("|")
        if is_row and not in_table:
            tables.append([])
        if is_row and not set(line) <= set("|-: \t"):
            tables[-1].append(_cells(line))
        in_table = is_row
    return tables


def _bounds(text: str, heading: re.Match[str]) -> tuple[int, int]:
    """Where the section under ``heading`` starts and ends: at the next level-2 or -3 heading."""
    following = NEXT_HEADING.search(text, heading.end())
    return heading.end(), following.start() if following else len(text)


def reader_tables(text: str) -> list[list[list[str]]]:
    """The tables under the handoff's one ``### Reader summary``, header rows included.

    Empty when the heading is missing or repeated.
    """
    text = text.replace("\r\n", "\n")
    headings = list(HEADING.finditer(text))
    if len(headings) != 1:
        return []
    start, end = _bounds(text, headings[0])
    return _tables(text[start:end])
