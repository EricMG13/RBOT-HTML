"""Answer keys here are written by hand: literal check numbers and line numbers, never computed."""

import re

import pytest

from deploy_workflow.prose_checks import (
    DATA_MODULES,
    READER_HEADINGS,
    limitation_items,
    prose_issues,
    reader_passages,
)

PREFIX = (
    "# Handoff\n\n## Findings\n\n"  # four lines: `### Bottom line` is line 5, the next text line 7
)
CALCULATIONS = "\n## Calculations\n\n| ID | Value |\n| --- | --- |\n| C-1 | 3.1x |\n"


def bottom(sentence: str, tail: str = "") -> str:
    return f"{PREFIX}### Bottom line\n\n{sentence}\n{tail}"


def found(issues: tuple[str, ...]) -> list[tuple[int, int]]:
    """(check, line) pairs read off the issue text, which names both."""
    pairs = []
    for issue in issues:
        match = re.match(r"Prose check (\d+) \(.*\), line (\d+): ", issue)
        assert match, issue
        pairs.append((int(match[1]), int(match[2])))
    return pairs


FULL = (
    """# Handoff

## Sources

| File | Type |
| --- | --- |
| a.pdf | report |

## Findings

### Bottom line

The credit is resilient and creditors are well covered.
Basis: a.pdf, pages 12–14; Liquidity (CP-2D); calculation C-1.

### Key findings

- Leverage is manageable at 3.1x, which supports the view.
  Basis: calculation C-1; a.pdf, p. 4; 0123456789abcdef0123456789abcdef
- Liquidity covers USD 1,250 million of maturities to 30 September 2024.

### Contrary evidence and what would change the view

A weaker FY2024 and a 10-K restatement would change the view.

### Limitations

- Revenue is unaudited, so the leverage conclusion could soften.
  Basis: a.pdf, page 3

### Method

| Check | Source |
| --- | --- |
| CP-2D | a.pdf, p. 4 |
"""
    + CALCULATIONS
)


def test_constants() -> None:
    assert DATA_MODULES == {"CP-0", "CP-PARSE", "CP-1", "CP-1C"}
    assert READER_HEADINGS[0] == "Bottom line"
    assert len(READER_HEADINGS) == 4


def test_full_prose_module_passes_with_basis_lines_exempt() -> None:
    assert prose_issues(FULL) == ()


def test_data_module_with_only_bottom_line_and_tables_passes() -> None:
    text = bottom(
        "Source files were parsed and are readable.",
        "\n| File | Page |\n| --- | --- |\n| CP-1 | p. 4 |\n| CP-2D | page 9 |\n",
    )
    assert prose_issues(text) == ()


def test_blocked_module_with_only_bottom_line_passes() -> None:
    assert (
        prose_issues(bottom("Not assessable: no source file was supplied for this module.")) == ()
    )


def test_reader_passages_keeps_only_the_four_sections_with_line_numbers() -> None:
    text = (
        "# H\n\n## Findings\n\n### Bottom line\n\nGood.\n\n### Method\n\nSkipped.\n\n"
        "### Limitations\n\n- One thing.\n\n## Gaps\n\nOut.\n"
    )
    assert reader_passages(text) == {
        "Bottom line": [(6, ""), (7, "Good."), (8, "")],
        "Limitations": [(14, ""), (15, "- One thing."), (16, "")],
    }


def test_reader_passages_ignores_headings_in_a_fence_and_other_h2() -> None:
    text = (
        "## Request\n\n### Bottom line\n\nNot here.\n\n## Findings\n\n### Bottom line\n\n"
        "```\n### Limitations\n```\n"
    )
    assert list(reader_passages(text)) == ["Bottom line"]


def test_limitation_items_are_normalised_and_basis_dropped() -> None:
    text = (
        f"{PREFIX}### Bottom line\n\nOk.\n\n### Limitations\n\n"
        "- Revenue is **unaudited**, so the view could soften.\n  Basis: a.pdf, page 3\n"
        "- Second item (minor).\n"
    )
    assert limitation_items(text) == (
        "revenue is unaudited so the view could soften",
        "second item minor",
    )


def test_check_1_missing_findings() -> None:
    assert found(prose_issues("# Handoff\n\nNothing.\n")) == [(1, 1)]


def test_check_1_first_h3_not_bottom_line() -> None:
    text = f"{PREFIX}### Key findings\n\nThe view holds.\n"
    assert found(prose_issues(text)) == [(1, 5)]


@pytest.mark.parametrize(
    "first",
    ["- a list item", "| a | b |", "```", "<!-- note -->", "#### heading", "12 months of data"],
)
def test_check_1_first_line_not_prose(first: str) -> None:
    assert found(prose_issues(bottom(first))) == [(1, 7)]


@pytest.mark.parametrize(
    "first", ['"Quoted" view.', "“Curly” view.", "'Single' view.", "**Bold** view."]
)
def test_check_1_prose_openers(first: str) -> None:
    assert prose_issues(bottom(first)) == ()


def test_check_1_empty_bottom_line() -> None:
    assert found(prose_issues(f"{PREFIX}### Bottom line\n\n### Key findings\n\nText.\n")) == [
        (1, 5)
    ]


def test_check_2_module_code_message() -> None:
    assert prose_issues(bottom("Liquidity from CP-2D is strong.")) == (
        'Prose check 2 (no module code), line 7: "CP-2D" — move it to the paragraph\'s Basis line.',
    )


@pytest.mark.parametrize(
    "sentence",
    ["See p. 12 for it.", "On page 4 it appears.", "At pp.3 it is.", "At PAGE 9 it ends."],
)
def test_check_3_page_locator(sentence: str) -> None:
    assert found(prose_issues(bottom(f"The view holds. {sentence}"))) == [(3, 7)]


@pytest.mark.parametrize(
    "sentence", ["The view holds [1].", "The view holds [a.pdf].", "The view holds 【1†x】."]
)
def test_check_4_bracket_or_chip(sentence: str) -> None:
    assert found(prose_issues(bottom(sentence))) == [(4, 7)]


def test_check_5_hash_in_sentence_fails_and_in_basis_is_ignored() -> None:
    sentence = "The file ends 0123456789abcdef0123 here."
    assert found(prose_issues(bottom(sentence))) == [(5, 7)]
    assert found(prose_issues(bottom("The view holds with sha256 noted."))) == [(5, 7)]
    assert prose_issues(bottom("The view holds.\nBasis: x.pdf; 0123456789abcdef0123; sha256")) == ()


def test_check_6_calculation_id_in_sentence() -> None:
    assert found(prose_issues(bottom("Leverage per C-1 is high.", CALCULATIONS))) == [(6, 7)]


def test_check_6_whole_token_only() -> None:
    assert prose_issues(bottom("Cases AC-1 and C-12 differ.", CALCULATIONS)) == ()


def test_check_6_calculations_id_is_the_id_column_not_the_first_cell() -> None:
    table = "\n## Calculations\n\n| Metric | Value |\n| --- | --- |\n| M2 | 5 |\n"
    assert prose_issues(bottom("Measure M2 is high.", table)) == ()
    keyed = "\n## Calculations\n\n| Metric | ID |\n| --- | --- |\n| Leverage | M2 |\n"
    assert found(prose_issues(bottom("Measure M2 is high.", keyed))) == [(6, 7)]


def test_check_6_register_id_column_anywhere() -> None:
    table = "\n### Method\n\n| Risk ID | Name |\n| --- | --- |\n| R-7 | A1 |\n"
    assert found(prose_issues(bottom("Risk R-7 is key.", table))) == [(6, 7)]
    assert prose_issues(bottom("Name A1 is not an ID.", table)) == ()


def test_check_7_repeat_inside_handoff_and_across_accepted() -> None:
    text = (
        "# H\n\n## Findings\n\n### Bottom line\n\nThe view holds.\n\n### Limitations\n\n"
        "- Revenue is unaudited, so the view could soften.\n"
        "- Other point.\n"
        "- revenue is UNAUDITED so the view could soften!\n  Basis: a.pdf, page 3\n"
    )
    assert found(prose_issues(text)) == [(7, 13)]
    accepted = {"CP-2": "## Findings\n\n### Limitations\n\n- Other point.\n"}
    assert found(prose_issues(text, accepted)) == [(7, 12), (7, 13)]
    assert found(
        prose_issues(text, {"CP-2": "## Findings\n\n### Limitations\n\n- Different.\n"})
    ) == [(7, 13)]


def test_check_7_distinct_limitations_pass() -> None:
    text = f"{PREFIX}### Bottom line\n\nOk.\n\n### Limitations\n\n- First point.\n- Second point.\n"
    assert prose_issues(text, {"CP-2": "## Findings\n\n### Limitations\n\n- Third point.\n"}) == ()


@pytest.mark.parametrize(
    "figure",
    [
        "2024",
        "2024-09-30",
        "30 September 2024",
        "September 30, 2024",
        "March 2025",
        "Q3",
        "FY2024",
        "LTM",
        "9M",
        "10-K",
        "B-1",
        "12",
        "99",
        "USD 1,250 million",
        "$3.2bn",
        "3.1x",
        "61 bp",
        "61bp",
        "45%",
        "18 months",
        "EUR 5",
        "(USD 1,250)",
        "-5%",
        "12-month",
    ],
)
def test_check_8_passing_figures(figure: str) -> None:
    assert prose_issues(bottom(f"The ratio stands at {figure}, which matters.")) == ()


@pytest.mark.parametrize(
    "figure", ["1,250", "12 million shares", "3.456%", "250 million", "100", "5bn", "250m", "2.5"]
)
def test_check_8_failing_figures(figure: str) -> None:
    assert found(prose_issues(bottom(f"The ratio stands at {figure}, which matters."))) == [(8, 7)]


def test_check_8_message_names_the_figure() -> None:
    (issue,) = prose_issues(bottom("Debt is 1,250 now."))
    assert issue.startswith("Prose check 8 (")
    assert 'line 7: "1,250" — ' in issue


def test_excluded_text_is_ignored_by_checks_2_to_8() -> None:
    text = (
        f"{PREFIX}### Bottom line\n\nThe view holds.\n\n```\nCP-2D p. 4 [1] 1,250\n```\n\n"
        "<!-- see [1] CP-2D\nand 1,250 p. 4 -->\n\n| CP-2D | p. 4 | 1,250 |\n"
        "Basis: a.pdf, page 4; Liquidity (CP-2D); calculation C-1\n"
    )
    assert prose_issues(text) == ()


def test_text_after_a_closed_comment_on_the_same_line_is_checked() -> None:
    assert found(prose_issues(bottom("The view holds. <!-- note --> See CP-2D."))) == [(2, 7)]


def test_list_marker_is_not_a_figure() -> None:
    text = f"{PREFIX}### Bottom line\n\nThe view holds.\n\n### Key findings\n\n1. Leverage holds.\n"
    assert prose_issues(text) == ()


def test_checks_apply_to_all_four_passages() -> None:
    text = (
        f"{PREFIX}### Bottom line\n\nThe view holds.\n\n### Key findings\n\n- See CP-2D here.\n\n"
        "### Contrary evidence and what would change the view\n\nDebt is 1,250 now.\n\n"
        "### Limitations\n\n- A gap [1].\n"
    )
    assert found(prose_issues(text)) == [(2, 11), (4, 19), (8, 15)]


@pytest.mark.parametrize("delimiter", ["|:-:|:-:|", "|--|--|", "| - | - |", "| :-- | --: |"])
def test_check_6_every_gfm_delimiter_row_makes_a_table(delimiter: str) -> None:
    text = (
        bottom("Leverage per C-1 is high.")
        + f"\n## Calculations\n\n| ID | Value |\n{delimiter}\n| C-1 | 3.1x |\n"
    )
    assert found(prose_issues(text)) == [(6, 7)]


@pytest.mark.parametrize(
    "sentence",
    ["FCF 250 million is retained.", "LTM 1,250 million of it.", "The FCF 1,250 is small."],
)
def test_check_8_acronym_is_not_a_currency(sentence: str) -> None:
    assert found(prose_issues(bottom(sentence))) == [(8, 7)]


@pytest.mark.parametrize("code", ["USD", "EUR", "GBP", "JPY", "CHF", "SEK"])
def test_check_8_iso_codes_are_currencies(code: str) -> None:
    assert prose_issues(bottom(f"Debt was {code} 250 million.")) == ()


def test_iso_4217_has_the_2025_guilder_and_no_non_currency_codes() -> None:
    from deploy_workflow.prose_checks import ISO_4217

    assert {"XCG", "ANG"} <= ISO_4217
    assert not {"XXX", "XTS"} & ISO_4217


def test_check_8_xcg_is_a_currency_and_xxx_is_not() -> None:
    assert prose_issues(bottom("Debt was XCG 250 million.")) == ()
    assert found(prose_issues(bottom("Debt was XXX 250 million."))) == [(8, 7)]


@pytest.mark.parametrize("marker", ["```", "### Method"])
def test_marker_inside_multiline_comment_does_not_hide_later_text(marker: str) -> None:
    text = bottom("The view holds.", f"<!--\n{marker}\n-->\nSee CP-2D here.\n")
    assert found(prose_issues(text)) == [(2, 11)]


def test_basis_line_inside_a_paragraph_is_sentence_text() -> None:
    text = bottom("The view holds.", "Basis: CP-2D shows debt of 1,250 [1].\nMore prose follows.\n")
    assert [c for c, n in found(prose_issues(text)) if n == 8] == [2, 4, 8]


def test_basis_line_ending_a_paragraph_or_item_stays_exempt() -> None:
    text = bottom(
        "The view holds.",
        "Basis: CP-2D p. 4.\n\n- Item one.\n  Basis: CP-2D p. 5.\n- Item two.\nBasis: CP-1.\n",
    )
    assert prose_issues(text) == ()


def test_figure_touching_a_letter_is_not_rejudged_as_its_tail() -> None:
    assert prose_issues(bottom("Revenue was USD1,250 million.")) == ()


def test_check_6_a_calculations_first_cell_is_not_an_id_unless_its_column_is() -> None:
    period_keyed = "\n## Calculations\n\n| Period | Value |\n| --- | --- |\n| FY2024 | 3.1x |\n"
    assert prose_issues(bottom("FY2024 leverage is high.", period_keyed)) == ()
    suffixed = "\n## Calculations\n\n| Run ID | Value |\n| --- | --- |\n| C-1 | 3.1x |\n"
    assert found(prose_issues(bottom("Leverage per C-1 is high.", suffixed))) == [(6, 7)]


def test_check_8_a_figure_with_no_unit_is_told_to_reword_or_use_a_table() -> None:
    (issue,) = prose_issues(bottom("The issuer operates 1,200 stores."))
    assert "reword it in words or move it to a table" in issue
    (decimals,) = prose_issues(bottom("The ratio is 3.456%."))
    assert "round to at most two decimals" in decimals
