"""Answer keys here are written by hand: literal check numbers and line numbers, never computed."""

import re
import time

import pytest

from deploy_workflow.prose_checks import (
    DATA_MODULES,
    READER_HEADINGS,
    figure_issues,
    key_figures_issues,
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


def test_check_6_a_calculations_first_column_id_is_refused_outside_calculations_not() -> None:
    # Owner 2026-11-11 (L1): an ID in `## Calculations` is its first column's letter+digit cell.
    table = "\n## Calculations\n\n| Calculation | Value |\n| --- | --- |\n| C3 | 5 |\n"
    assert prose_issues(bottom("See C3 for it.", table)) == ()
    elsewhere = "\n## Gaps\n\n| Metric | Value |\n| --- | --- |\n| M2 | 5 |\n"
    assert prose_issues(bottom("Measure M2 is high.", elsewhere)) == ()


def test_check_6_a_label_first_column_cell_is_not_an_id() -> None:
    table = (
        "\n## Calculations\n\n| ID | Value |\n| --- | --- |\n| C-1 | 3.1x |\n\n"
        "| Carried reader metric | Value |\n| --- | --- |\n"
        "| FY2024 gross debt | USD 25,068 million |\n"
    )
    assert prose_issues(bottom("FY2024 gross debt is large.", table)) == ()
    assert found(prose_issues(bottom("Leverage per C-1 is high.", table))) == [(6, 7)]


def test_check_6_an_id_column_cell_is_an_id_in_any_table() -> None:
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


def test_a_basis_line_after_a_blank_line_is_sentence_text() -> None:
    text = bottom("The view holds.", "\nBasis: CP-2D p. 4.\n")
    assert [c for c, n in found(prose_issues(text)) if n == 9] == [2, 3]


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


def fidelity(passage: str, detail: str, heading: str = "Key findings") -> tuple[str, ...]:
    """A handoff whose reader passage is `passage` and whose Calculations section is `detail`."""
    text = (
        "# Handoff\n\n## Findings\n\n### Bottom line\n\nCredit is mixed.\n\n"
        f"### {heading}\n\n{passage}\n\n## Calculations\n\n{detail}\n"
    )
    return figure_issues(text)


def test_a_reader_figure_the_handoff_does_not_hold_is_refused() -> None:
    issues = fidelity("Leverage is 9.87x.", "| ID | Value |\n| --- | --- |\n| C-1 | 3.1x |")
    assert issues == (
        (
            'Fidelity check, line 11: "9.87x" does not appear elsewhere in the handoff (tables, '
            "calculations or other findings), with the same sign, unit and scale: add it there or "
            "remove it from the passage."
        ),
    )


def test_a_bottom_line_figure_the_handoff_does_not_hold_is_refused() -> None:
    text = "# H\n\n## Findings\n\n### Bottom line\n\nCover was 9.87x.\n\n## Gaps\n\nNone.\n"
    assert len(figure_issues(text)) == 1


def test_a_figure_held_in_a_table_outside_the_passages_is_accepted() -> None:
    assert fidelity("Leverage is 3.1x.", "| ID | Value |\n| --- | --- |\n| C-1 | 3.1x |") == ()
    assert fidelity("Leverage is 3.1x.", "| ID | Value |\n| --- | --- |\n| C-1 | 3.1 |") == ()


def test_a_figure_held_only_inside_a_reader_passage_is_refused() -> None:
    text = (
        "# H\n\n## Findings\n\n### Bottom line\n\nCover was 3.1x.\n\n"
        "### Key findings\n\nCover was 3.1x.\n"
    )
    assert len(figure_issues(text)) == 2


@pytest.mark.parametrize(
    ("passage", "detail", "accepted"),
    [
        # Sign: the handoff writes a decline as (12.3)%; 12.3% states a rise.
        ("Revenue grew 12.3%.", "Revenue change was (12.3)%.", False),
        ("Revenue fell by (12.3)%.", "Revenue change was (12.3)%.", True),
        ("Revenue fell by -12.3%.", "Revenue change was (12.3)%.", True),
        ("Revenue fell by (12.3%).", "Revenue change was (12.3)%.", True),
        ("Revenue fell by -12.3%.", "Revenue change was 12.3%.", False),
        # Unit: 4.1x is a multiple, not a percentage; a bare number states no unit.
        ("Leverage is 4.1%.", "Net leverage was 4.1x.", False),
        ("Leverage is 4.1x.", "Net leverage was 4.1x.", True),
        ("Leverage is 4.1.", "Net leverage was 4.1x.", True),
        ("Leverage is 4.1x.", "Net leverage was 4.1.", True),
        # Scale: 250 thousand is not 250 million.
        ("Cash was US$250 million.", "Cash was 250 US$ thousands.", False),
        ("Cash was US$250 thousand.", "Cash was 250 US$ thousands.", True),
        ("Cash was 250 million.", "Cash was 250 millions.", True),
        # Hyphens in ranges and compounds are not minus signs; a footnote marker is not a sign.
        ("Margins held in 2023-2024.", "The years 2023-2024 and a 5-year plan.", True),
        ("A 5-year plan.", "A 5-year plan, see 1) below.", True),
    ],
)
def test_a_reader_figure_keeps_the_sign_unit_and_scale_the_handoff_wrote(
    passage: str, detail: str, accepted: bool
) -> None:
    issues = fidelity(passage, detail)
    assert (issues == ()) is accepted, issues
    if not accepted:
        assert len(issues) == 1 and "does not match the handoff" in issues[0]
        assert detail.split(" was ")[-1].rstrip(".") in issues[0]


@pytest.mark.parametrize(
    ("passage", "absent"),
    [
        # A malformed figure is read as its digit runs; none is in the handoff.
        ("Version 1.2.3 applies.", ("1.2", "3")),
        ("Dated 28.12.2024.", ("28.12", "2024")),
        ("Margin was 12,5%.", ("12", "5%")),
        ("Debt was 1,2345.", ("1", "2345")),
    ],
)
def test_a_malformed_reader_figure_is_still_checked(passage: str, absent: tuple[str, ...]) -> None:
    issues = fidelity(passage, "Nothing numeric here.")
    assert [i.split('"')[1] for i in issues] == list(absent)


def test_a_number_only_inside_a_longer_number_does_not_match() -> None:
    for number, longer in {"3.14": "13.14", "940": "7,940", "14": "3.14"}.items():
        assert len(fidelity(f"Cover was {number}.", f"The value was {longer}.")) == 1, number


def test_a_date_in_a_passage_needs_no_matching_figure() -> None:
    assert fidelity("The notes mature on 30 September 2029.", "None.") == ()


@pytest.mark.parametrize(
    ("passage", "detail"),
    [
        (
            "The 2029 secured notes carry the risk.",
            "| Notes | Due |\n| --- | --- |\n| A | 15 January 2029 |",
        ),
        (
            "The 2029 secured notes carry the risk.",
            "| Notes | Due |\n| --- | --- |\n| A | 2029-01-15 |",
        ),
        ("Cover fell in Q3.", "| Period | Cover |\n| --- | --- |\n| 30 September 2024 | 3.1x |"),
        ("Cover fell in FY2025E and 9M.", "None."),
    ],
)
def test_a_year_or_period_held_only_as_a_date_or_a_label_is_accepted(
    passage: str, detail: str
) -> None:
    assert fidelity(passage, detail) == ()


@pytest.mark.parametrize(
    ("passage", "detail"),
    [
        ("Spread widened 50 bp.", "| Spread | 50% |"),
        ("Spread widened 50 bps.", "| Spread | 50% |"),
        ("Margin rose 2.5 pp.", "| Margin | 2.5x |"),
    ],
)
def test_a_basis_point_or_point_figure_does_not_match_another_unit(
    passage: str, detail: str
) -> None:
    assert len(fidelity(passage, detail)) == 1


def test_a_basis_point_figure_matches_its_own_unit() -> None:
    assert fidelity("Spread widened 50 bps.", "| Spread | 50 bp |") == ()
    assert fidelity("Margin rose 2.5 pp.", "| Margin | 2.5pp |") == ()


@pytest.mark.parametrize("label", ["FY2025E", "Q3 2024", "H1 2024", "FY2024", "Q3", "9M"])
def test_check_6_a_period_label_first_cell_in_calculations_is_not_an_id(label: str) -> None:
    table = f"\n## Calculations\n\n| Period | Value |\n| --- | --- |\n| {label} | 3.1x |\n"
    assert prose_issues(bottom(f"Cover in {label} was 3.1x.", table)) == ()


def test_a_minus_held_figure_may_be_narrated_as_its_magnitude() -> None:
    assert fidelity("Margin fell 5%.", "| Margin change | -5% |") == ()
    assert len(fidelity("Margin was -5%.", "| Margin change | 5% |")) == 1


def test_a_padded_decimal_matches_its_trimmed_form() -> None:
    assert fidelity("Leverage is 4.1x.", "| Leverage | 4.10x |") == ()
    assert len(fidelity("Leverage is 4.1x.", "| Leverage | 4.15x |")) == 1


FORECAST_BLOCK_DOC = (
    "### Forecast inputs (machine-readable)\n\n```json\n"
    '{"base_drivers": {"ebitda_margin": {"rationale": "FY2025 margin was 31.7%, carried forward"}}}'
    "\n```\n"
)


def test_the_forecast_inputs_block_holds_no_reader_figure() -> None:
    """The block's own rationale text is not a table: it cannot hold what a passage states."""
    text = bottom("The EBITDA margin was 31.7% last year.", FORECAST_BLOCK_DOC + CALCULATIONS)
    assert len(figure_issues(text)) == 1
    held = bottom("The EBITDA margin was 31.7% last year.", CALCULATIONS.replace("3.1x", "31.7%"))
    assert figure_issues(held) == ()


# ---- Decisions 7 and 8 of 2026-11-12: every section the Modules page shows; pipeline wording; the
# bottom line's length. Answer keys are literal: the check number, the line and the section.


def under(heading: str, body: str, h2: str = "Findings") -> str:
    """A handoff with a clean Bottom line, then the section `heading` (such as `### Method`)."""
    return f"# Handoff\n\n## {h2}\n\n### Bottom line\n\nThe view holds.\n\n{heading}\n\n{body}\n"


def named(issues: tuple[str, ...]) -> list[tuple[int, int, str]]:
    """(check, line, section) of each issue; the section is '' when the issue names none."""
    out = []
    for issue in issues:
        match = re.match(
            r'Prose check (\d+) \(.*\), line (\d+): ".*?"(?: in section "(.*)")? — ', issue
        )
        assert match, issue
        out.append((int(match[1]), int(match[2]), match[3] or ""))
    return out


@pytest.mark.parametrize(
    ("sentence", "check"),
    [
        ("Cover comes from CP-2D here.", 2),
        ("The covenant is on page 12 of it.", 3),
        ("Cover is thin [1] here.", 4),
        ("The hash is 0123456789abcdef0123 here.", 5),
    ],
)
def test_checks_2_to_5_read_a_method_style_section_and_name_it(sentence: str, check: int) -> None:
    text = under("### Method", sentence)
    assert {c for c, _, _ in named(prose_issues(text))} == {check}
    assert {(line, section) for _, line, section in named(prose_issues(text))} == {(11, "Method")}


def test_checks_2_to_5_read_calculations_gaps_and_the_findings_lead_in() -> None:
    calc = under("### Method", "Fine.\n\n## Calculations\n\nSee CP-2D.")
    assert named(prose_issues(calc)) == [(2, 15, "Calculations")]
    gaps = under("### Method", "Fine.\n\n## Gaps\n\nSee CP-2D.")
    assert named(prose_issues(gaps)) == [(2, 15, "Gaps")]
    lead = "# H\n\n## Findings\n\nSee CP-2D.\n\n### Bottom line\n\nThe view holds.\n"
    assert named(prose_issues(lead)) == [(2, 5, "Findings")]


def test_a_reader_passage_issue_keeps_its_message_and_check_10_names_the_passage() -> None:
    assert named(prose_issues(bottom("Cover from CP-2D, per the pack."))) == [
        (2, 7, ""),
        (10, 7, "Bottom line"),
    ]


@pytest.mark.parametrize(
    "phrase",
    [
        "handoff",
        "handoffs",
        "this transport",
        "the pack",
        "fact pack",
        "source pack",
        "canonical",
        "re-anchor",
        "re-anchoring",
        "helper script",
        "helper scripts",
        "upstream module",
        "downstream module",
        "downstream owner",
        "downstream work",
        "downstream analysis",
        "downstream use",
        "Handoff",
        "THE PACK",
    ],
)
@pytest.mark.parametrize("where", ["passage", "method", "gaps"])
def test_check_10_refuses_each_banned_phrase_in_a_passage_and_in_another_section(
    phrase: str, where: str
) -> None:
    sentence = f"The note about {phrase} stays."
    text = {
        "passage": bottom(sentence),
        "method": under("### Method", sentence),
        "gaps": under("### Method", "Fine.\n\n## Gaps\n\n" + sentence),
    }[where]
    assert [c for c, _, _ in named(prose_issues(text))] == [10]


@pytest.mark.parametrize(
    "sentence",
    [
        "Consumer demand is steady.",
        "Upstream operations feed the plants.",
        "The transport sector is cyclical.",
        "Debt was USD 1,250 million on EBITDA in FY2024.",
        "Downstream demand for parts is weak.",
        "The downstream segment is small.",
        "A package of measures; the packs are small.",
        "Handsets and canon are not banned.",
        "The upstream module was not run.".replace("upstream module", "upstream supplier"),
    ],
)
def test_check_10_passes_ordinary_credit_language(sentence: str) -> None:
    assert prose_issues(under("### Method", sentence)) == ()


@pytest.mark.parametrize(
    ("token", "found"),
    [
        ("qa_status", "qa_status"),
        ("READY_WITH_LIMITATIONS", "READY_WITH_LIMITATIONS"),
        ("tdg_annual_report.pdf", "tdg_annual_report"),
    ],
)
def test_check_10_refuses_snake_case_and_caps_underscore_tokens(token: str, found: str) -> None:
    issues = prose_issues(under("### Method", f"The status is {token} today."))
    assert named(issues) == [(10, 11, "Method")]
    assert f'"{found}' in issues[0]


def test_check_10_leaves_other_underscore_text_alone() -> None:
    # digits or capitals on a side do not make a snake_case token; no letter makes no caps token
    assert prose_issues(under("### Method", "Items 12_34 and Ab_1 and a_1 are listed.")) == ()


def test_a_file_name_in_a_sentence_is_refused_only_as_a_snake_case_token() -> None:
    # Decision: a file name in a sentence is a source reference in narrative; the checks refuse it
    # only through its form (snake_case): `10-K.htm` alone passes, `tdg_10k_report.pdf` does not.
    assert prose_issues(under("### Method", "See 10-K.htm for it.")) == ()
    assert named(prose_issues(under("### Method", "See tdg_10k_report.pdf for it."))) == [
        (10, 11, "Method")
    ]


FILE = "tdg_annual_report.pdf"


def test_a_file_name_and_pipeline_text_in_a_table_a_fence_or_a_basis_line_pass() -> None:
    body = (
        f"| Source | Use |\n| --- | --- |\n| {FILE} | the pack, CP-2D, qa_status [1] |\n\n"
        "```\nthe handoff CP-2D page 4 qa_status READY_WITH_LIMITATIONS\n```\n\n"
        f"Prose here.\nBasis: {FILE}, p. 4; the pack; CP-2D; qa_status\n\n"
        f"- Item.\n  Basis: {FILE}, page 4\n"
    )
    assert prose_issues(under("### Method", body)) == ()
    assert prose_issues(under("### Method", "Fine.\n\n## Calculations\n\n" + body)) == ()


def test_the_same_text_in_a_sentence_is_refused() -> None:
    body = f"Prose here.\nBasis: {FILE}, p. 4; the pack\nMore prose follows."
    # A Basis line that does not end its paragraph is sentence text (existing rule)
    assert {c for c, _, _ in named(prose_issues(under("### Method", body)))} == {3, 10}


@pytest.mark.parametrize(
    "heading",
    [
        "### Chart data: leverage",
        "### Map: ownership",
        "### Events: Legal",
        "### Forecast inputs (machine-readable)",
        "### Confidence inputs",
    ],
)
def test_data_sections_are_not_sentence_text(heading: str) -> None:
    assert prose_issues(under(heading, "See CP-2D, qa_status, page 4 and the pack [1].")) == ()


def test_a_section_after_a_data_section_is_read_again() -> None:
    text = under("### Chart data: leverage", "Fine.\n\n### Method\n\nSee CP-2D.")
    assert named(prose_issues(text)) == [(2, 15, "Method")]


def test_check_6_stays_on_the_reader_passages() -> None:
    table = "\n## Calculations\n\n| ID | Value |\n| --- | --- |\n| C3 | 5 |\n"
    assert prose_issues(under("### Method", "Measure C3 is high.") + table) == ()
    assert [c for c, _, _ in named(prose_issues(bottom("Measure C3 is high.", table)))] == [6]


def words(count: int) -> str:
    return " ".join(["word"] * count)


def test_a_first_sentence_of_46_words_is_refused_and_45_pass() -> None:
    assert prose_issues(bottom(f"{words(45)}. More follows.")) == ()
    issues = prose_issues(bottom(f"{words(46)}. More follows."))
    assert named(issues) == [(1, 7, "Bottom line")]
    assert "46 words" in issues[0]


def test_a_bottom_line_of_181_words_is_refused_and_180_pass() -> None:
    assert prose_issues(bottom(f"Short view.\n\n{words(178)}.")) == ()
    issues = prose_issues(bottom(f"Short view.\n\n{words(179)}."))
    assert named(issues) == [(1, 5, "Bottom line")]
    assert "181 words" in issues[0]


def test_bottom_line_words_exclude_tables_fences_and_basis_lines() -> None:
    tail = f"\n| A | B |\n| - | - |\n| {words(100)} | x |\n\n```\n{words(100)}\n```\n"
    assert prose_issues(bottom(f"Short view.\nBasis: {words(100)}", tail)) == ()


def test_a_decimal_or_a_closing_bold_does_not_hide_a_long_first_sentence() -> None:
    assert [c for c, _, _ in named(prose_issues(bottom(f"Cover is 3.1x {words(45)}. Then.")))] == [
        1
    ]
    assert prose_issues(bottom(f"**Short view.** {words(60)}.")) == ()


def test_check_4_reports_one_issue_per_bracket_pair_with_the_text_whole() -> None:
    issues = [
        i
        for i in prose_issues(bottom("The view holds [Insufficient Information] here."))
        if "check 4" in i
    ]
    assert len(issues) == 1
    assert '"[Insufficient Information]"' in issues[0]


def test_check_4_two_pairs_on_a_line_are_two_issues() -> None:
    issues = [
        i for i in prose_issues(bottom("The view [a] holds and then [b] ends.")) if "check 4" in i
    ]
    assert [i.split('"')[1] for i in issues] == ["[a]", "[b]"]


def test_check_4_an_unpaired_bracket_is_one_issue_with_context() -> None:
    issues = [i for i in prose_issues(bottom("The view holds [ here.")) if "check 4" in i]
    assert len(issues) == 1
    assert '"The view holds [ here."' in issues[0]


def test_check_4_a_pair_over_80_characters_quotes_each_bracket_with_20_characters_around_it() -> (
    None
):
    long = "a" * 90
    issues = [i for i in prose_issues(bottom(f"The view [{long}] holds.")) if "check 4" in i]
    assert [i.split('"')[1] for i in issues] == [f"The view [{'a' * 20}", f"{'a' * 20}] holds."]


@pytest.mark.parametrize(
    ("passage", "detail"),
    [
        ("EBITDA was USD 4,173 million.", "| EBITDA | 4173 | USD million |"),
        ("EBITDA was USD 4173 million.", "| EBITDA | 4,173 | USD million |"),
        ("Debt was USD 1,291.27 million.", "| Debt | 1291.27 |"),
        ("Debt was USD 1291.27 million.", "| Debt | 1,291.27 |"),
        ("Debt was USD 1,234,567 million.", "| Debt | 1234567 |"),
    ],
)
def test_a_thousands_separator_does_not_change_a_figure(passage: str, detail: str) -> None:
    assert fidelity(passage, detail) == ()


@pytest.mark.parametrize(
    ("passage", "detail", "quoted"),
    [
        ("Debt was USD 4,173 million.", "| Debt | 4173 thousand |", "4,173 million"),
        ("Debt was -4,173.", "| Debt | 4173 |", "-4,173"),
        ("Debt was 5.89x.", "| Debt | 5.8905x |", "5.89x"),
        ("Debt was USD 4,173 million.", "| Debt | 4,174 |", "4,173 million"),
        ("Debt was 4,173.", "| Debt | 73 |", "4,173"),
    ],
)
def test_a_figure_with_a_separator_is_still_refused_when_it_differs(
    passage: str, detail: str, quoted: str
) -> None:
    (issue,) = fidelity(passage, detail)
    assert f'"{quoted}"' in issue


def test_a_comma_that_is_not_a_thousands_separator_still_splits_the_number() -> None:
    assert [i.split('"')[1] for i in fidelity("Cover was 1,25.", "| Cover | 125 |")] == ["1", "25"]
    held = "| Year | Stores |\n| --- | --- |\n| 2024 | 437 |"
    assert fidelity("Cover was 437 in 2024, 437.", held) == ()


def annotated(cell: str) -> str:
    return f"| Measure | Value |\n| --- | --- |\n| Row | {cell} |"


@pytest.mark.parametrize(
    ("passage", "cell"),
    [
        ("Margin was 51.6%.", "3,395 (51.6%)"),
        ("Leverage was 5.89x.", "5.8905x (5.89x)"),
        ("Margin was 45.05%.", "0.45052 (45.05%)"),
    ],
)
def test_a_bracketed_figure_after_a_figure_is_an_annotation_not_a_negative(
    passage: str, cell: str
) -> None:
    assert fidelity(passage, annotated(cell)) == ()


@pytest.mark.parametrize(
    ("passage", "cell"),
    [
        ("Margin was (51.6%).", "3,395 (51.6%)"),
        ("Margin was -51.6%.", "3,395 (51.6%)"),
        ("Margin was 51.6%.", "3,395 | (51.6%)"),
    ],
)
def test_an_annotation_is_a_positive_figure_and_only_one_after_a_figure(
    passage: str, cell: str
) -> None:
    assert len(fidelity(passage, annotated(cell))) >= 1


def test_an_annotation_that_is_itself_negative_keeps_its_minus() -> None:
    assert fidelity("Margin was -5.2%.", annotated("100 (-5.2%)")) == ()
    assert len(fidelity("Margin was 5.2%.", annotated("100 (-5.2%)"))) == 0


@pytest.mark.parametrize(
    ("passage", "cell"),
    [
        ("Margin was 12.3%.", "(12.3)%"),
        ("Net debt change was 120.", "(120)"),
        ("There was a loss of 45.", "a loss of (45)"),
    ],
)
def test_a_bracketed_figure_standing_alone_or_after_words_stays_a_negative(
    passage: str, cell: str
) -> None:
    (issue,) = fidelity(passage, annotated(cell))
    assert "does not match the handoff" in issue


CP1_CHART = "### Chart data\n\n| Period | Cash |\n| --- | --- |\n| 2024-09-30 | 6261 |\n"


def key_figures(value: str, cp1: str = CP1_CHART) -> tuple[str, ...]:
    table = (
        "| Measure | Value | Period | Source |\n| --- | --- | --- | --- |\n"
        f"| Cash | {value} | 2024 | CP-1 |"
    )
    return key_figures_issues(f"## Findings\n\n### Key figures\n\n{table}\n", cp1)


def test_a_key_figure_with_a_thousands_separator_is_the_figure_cp1_states_plainly() -> None:
    assert key_figures("USD 6,261 million") == ()
    assert key_figures("6261", "| Cash | USD 6,261 million |") == ()
    assert key_figures("USD 6,261 million", "| Cash | 6,261 |") == ()
    assert len(key_figures("USD 6,262 million")) == 1
    assert len(key_figures("USD 6,261 thousand", "| Cash | 6261 million |")) == 1


NEGATIVE_AFTER_A_LABEL_OR_FIGURE = [
    ("FY2024 (120)", "120"),
    ("Q3 (45)", "45"),
    ("C12 (30)", "30"),
    ("Note 5 (120)", "120"),
    ("10-K page 120 (45)", "45"),
    ("2023-2024 (120)", "120"),
    ("H1 2024 (45)", "45"),
    ("31 Dec 2024 (45)", "45"),
    ("2024-09-30 (45)", "45"),
    ("D02 (22)/(48)", "22"),
    ("Q1 calculated CFO less capex 41,374; Q2 (26,306); LTM 105,927", "26,306"),
    ("FY2024 (165); FY2023 (139); FY2022 (119)", "139"),
    ("Capital expenditures (42) (36)", "36"),
    ("Dividends paid (30,199) (29,958)", "29,958"),
    ("2,200 (20) 2,180", "20"),
    ("2,248,030 (9,419) (21,140) 2,217,471", "21,140"),
    ("100 (25)", "25"),
    ("40% (364)", "364"),
    ("row 7 (12)", "12"),
    ("p. 9 (12)", "12"),
    ("1291.272 (1,291.28)", "1,291.28"),
    # A label spelling the date and period patterns do not cover (round 2).
    ("LTM Jun-24 (3.2%)", "3.2%"),
    ("Sep-24 (3.2%)", "3.2%"),
    ("FY24/25 (1.5%)", "1.5%"),
    ("2024/25 (2.2%)", "2.2%"),
    ("24/25 (2.2%)", "2.2%"),
    ("FY 24 (2.1%)", "2.1%"),
    ("FY-24 (2.1%)", "2.1%"),
    ("Q3'24 (4.5%)", "4.5%"),
    ("Q3-24 (4.5%)", "4.5%"),
    ("H1 24 (0.4x)", "0.4x"),
    ("3Q 24 (4.5%)", "4.5%"),
    ("2024-09 (3.2%)", "3.2%"),
    ("Year 2 (1.5%)", "1.5%"),
    ("A1 (5%)", "5%"),
    ("v2.5 (1.2x)", "1.2x"),
    # A unitless whole number below 100 is a label number, not an amount.
    ("Tranche 2 (45%)", "45%"),
    ("Level 3 (45%)", "45%"),
    ("12 (5.2%)", "5.2%"),
    # A long figure must not raise; the bracket is a negative.
    ("123,456,789,012,345,678,901,234,567,890 (5)", "5"),
    ("123456789012345.5 (1.123456789012345)", "1.123456789012345"),
    ("999,999,999,999,999 (1.123456789012345)", "1.123456789012345"),
]


@pytest.mark.parametrize(("cell", "figure"), NEGATIVE_AFTER_A_LABEL_OR_FIGURE)
def test_a_bracketed_figure_that_is_not_a_note_is_a_negative_on_the_held_side(
    cell: str, figure: str
) -> None:
    assert len(fidelity(f"The line was {figure}.", annotated(cell))) == 1
    assert fidelity(f"The line was ({figure}).", annotated(cell)) == ()


@pytest.mark.parametrize(
    ("passage", "figure"),
    [
        ("Net debt was 100 (25).", "25"),
        ("Net debt was 100 (364).", "364"),
        ("Net debt was 2,200 (20) 2,180.", "20"),
    ],
)
def test_a_bracketed_figure_on_the_passage_side_keeps_its_sign(passage: str, figure: str) -> None:
    (issue,) = fidelity(passage, annotated("100 | 25 | 364 | 2,200 | 20 | 2,180"))
    assert f'"({figure})"' in issue


# (passage with the figure positive, passage with the same figure in parentheses, held cell), all
# hand-written: the bracket is a note, so the positive passage is held and the negative one is not.
NOTES = [
    ("Margin was 51.6%.", "Margin was (51.6%).", "3,395 (51.6%)"),
    ("Leverage was 5.89x.", "Leverage was (5.89x).", "5.8905x (5.89x)"),
    ("Margin was 45.05%.", "Margin was (45.05%).", "0.45052 (45.05%)"),
    ("Debt was 1,291.27.", "Debt was (1,291.27).", "1291.272 (1,291.27)"),
    ("Debt was 1291.27.", "Debt was (1291.27).", "1291.272 (1,291.27)"),
    ("Debt was 9,432.7.", "Debt was (9,432.7).", "9432.72 (9,432.7)"),
    ("Leverage was 4.72x.", "Leverage was (4.72x).", "USD 19,702 million (4.72x)"),
    ("Margin was 16.2%.", "Margin was (16.2%).", "USD 1,067 million (16.2%)"),
    ("Leverage was 5.89x.", "Leverage was (5.89x).", "5.885x (5.89x)"),
    ("Leverage was 5.88x.", "Leverage was (5.88x).", "5.885x (5.88x)"),
    ("Leverage was 5.90x.", "Leverage was (5.90x).", "5.8905x (5.90x)"),
    # The same number written with thousands separators, to the same decimal places.
    ("Debt was 9,432.72.", "Debt was (9,432.72).", "9432.72 (9,432.72)"),
    ("Debt was 7,844.72.", "Debt was (7,844.72).", "7844.72 (7,844.72)"),
    ("Debt was 2,180.", "Debt was (2,180).", "2180 (2,180)"),
    # An amount, not a label number: a unit, a decimal part, a separator or 100 or more.
    ("Margin was 5.2%.", "Margin was (5.2%).", "12.0 (5.2%)"),
    ("Margin was 5.2%.", "Margin was (5.2%).", "120 (5.2%)"),
    ("Leverage was 0.1x.", "Leverage was (0.1x).", "12% (0.1x)"),
    ("Margin was 5.2%.", "Margin was (5.2%).", "USD 12 million (5.2%)"),
    ("Margin was 5.2%.", "Margin was (5.2%).", "1,200 (5.2%)"),
]


@pytest.mark.parametrize(("passage", "negative", "cell"), NOTES)
def test_a_ratio_or_a_rounding_after_a_figure_is_a_note_read_as_positive(
    passage: str, negative: str, cell: str
) -> None:
    assert fidelity(passage, annotated(cell)) == ()
    (issue,) = fidelity(negative, annotated(cell))
    assert "does not match the handoff" in issue


@pytest.mark.parametrize(
    ("cell", "negative"),
    [
        ("100 (100)", "(100)"),
        ("2,180 (2,180)", "(2,180)"),
        ("45 (45)", "(45)"),
        ("9,432.72 (9432.72)", "(9,432.72)"),
    ],
)
def test_an_identically_written_bracket_is_a_negative_not_a_note(cell: str, negative: str) -> None:
    assert fidelity(f"Cover was {negative}.", annotated(cell)) == ()


def test_a_note_on_the_passage_side_is_read_as_written() -> None:
    held = annotated("3,395 | 51.6%")
    assert fidelity("Ebitda was 3,395 (51.6%).", held) == ()
    assert len(fidelity("Ebitda was 3,395 (51.6%).", annotated("3,395 | (51.6%)"))) == 1


@pytest.mark.parametrize(
    ("cell", "positive", "negative"),
    [
        ("-1,291.272 (1,291.27)", "Debt was 1,291.27.", "Debt was (1,291.27)."),
        ("−4.5 (4)", "Debt was 4.", "Debt was (4)."),
    ],
)
def test_an_unsigned_bracket_after_a_negative_figure_is_a_negative_not_a_note(
    cell: str, positive: str, negative: str
) -> None:
    assert len(fidelity(positive, annotated(cell))) == 1
    assert fidelity(negative, annotated(cell)) == ()


def test_a_minus_repeated_in_the_bracket_after_a_negative_figure_is_read_as_written() -> None:
    cell = annotated("-11.5147826087 (-11.51)")
    assert fidelity("Debt was -11.51.", cell) == ()
    # A minus the handoff writes may be narrated as its magnitude, or in parentheses.
    assert fidelity("Debt was 11.51.", cell) == ()
    assert fidelity("Debt was (11.51).", cell) == ()
    assert len(fidelity("Debt was 11.5.", cell)) == 1


def test_a_long_line_of_notes_is_checked_in_linear_time() -> None:
    line = "1,234.5 (1,234) " * 2500  # 40,000 characters; quadratic look-behind took about 5.5 s
    started = time.monotonic()
    figure_issues(f"## Findings\n\n### Bottom line\n\n{line}\n")
    assert time.monotonic() - started < 2
