"""Credit OS's store reads a synthetic workspace built by tests/library_fixtures.py."""

import hashlib
import sys
from pathlib import Path

import pytest
from library_fixtures import make_run

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
from credit_os import store

MODULES = ("CP-0", "CP-1")


def read_store(tmp_path: Path) -> dict:
    """The store over one fixture run that the catalogue lists with its delivery as a report."""
    run_dir = make_run(tmp_path, "run-a")
    (delivery,) = (run_dir / "deliveries").iterdir()
    folder = f"runs/run-a/deliveries/{delivery.name}"
    (report,) = delivery.glob("report.html")
    digest = hashlib.sha256(report.read_bytes()).hexdigest()
    artifact = {
        "folder": folder,
        "label": "Synthetic report",
        "state": "final",
        "available": True,
        "href": f"/files/{folder}/report.html?sha256={digest}",
    }
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": [artifact]}
    return store.workspace_store(tmp_path, {"real": [row], "issues": []})


def test_store_reads_a_listed_run(tmp_path):
    result = read_store(tmp_path)
    by_module = {o["module"]: o for o in result["outputs"].values()}
    assert set(by_module) == set(MODULES)
    for output in by_module.values():
        assert output["run"] == "run-a"
        assert output["sha256"] in result["handoffs"]
    handoff_digests = {
        hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (tmp_path / "runs/run-a/deliveries").glob("*/CP-*.md")
    }
    assert {o["sha256"] for o in result["outputs"].values()} == handoff_digests
    (report,) = result["reports"]
    assert "/files/runs/run-a/deliveries/" in report["href"]
    assert report["href"].split("?")[0].endswith("/report.html")
    assert result["issues"] == []


def test_store_has_no_legacy_routes(tmp_path):
    result = read_store(tmp_path)
    assert result["pins"] == {}
    assert set(result["runs"]) == {"run-a"}
    assert result["outputs"] and result["reports"]
    links = [o["href"] for o in result["outputs"].values()]
    for report in result["reports"]:
        links += [report["href"], report["download"], *(f["href"] for f in report["files"])]
    for link in links:
        assert link.startswith("/files/runs/run-a/"), link


FRONT = "---\nmodule: CP-2A\nas_of: 2026-01-01\n---\n\n## Request\nWhat is asked.\n"


def test_front_matter_is_the_first_section_verbatim():
    sections = store.parse_source(FRONT)
    assert sections[0] == {
        "heading": "Front matter",
        "level": 2,
        "line": 1,
        "blocks": [
            {"type": "text", "line": 2, "end": 3, "text": "module: CP-2A\nas_of: 2026-01-01"}
        ],
    }
    assert sections[1] == {
        "heading": "Request",
        "level": 2,
        "line": 6,
        "blocks": [{"type": "text", "line": 7, "end": 7, "text": "What is asked."}],
    }
    assert len(sections) == 2


def test_other_body_before_the_first_heading_still_raises():
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("preamble\n## Request\nx\n")
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("---\nkey: v\n---\nstray\n## Request\nx\n")


def test_unterminated_front_matter_raises():
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("---\nkey: v\n\n## Request\nx\n")


def test_structured_accepts_front_matter():
    sections, error = store.structured(FRONT.encode(), strict=False)
    assert error is None
    assert sections[0]["heading"] == "Front matter"


def _text(text):
    return {"type": "text", "text": text}


def _table(*cells):
    """A table block of one row."""
    return {"type": "table", "headers": ["A", "B", "C"], "rows": [{"cells": list(cells)}]}


def _section(heading, level, *blocks):
    return {"heading": heading, "level": level, "line": 1, "blocks": list(blocks)}


SECTIONS = [
    _section("Front matter", 2, _text("module: CP-1\ncommittee_status: Requires More Work")),
    _section("CP-1 handoff", 1),
    _section("Request", 2, _text("What is asked.")),
    _section("Sources", 2, _text("K is the annual filing.")),
    _section("Findings", 2),
    _section("Reader summary", 3, _table("x", "Medium", "y")),
    _section("Chart data: leverage", 3, _table("x", "y", "z")),
    _section("Liquidity view", 3, _text("Cash covers two years of interest.")),
    _section("Debt register", 3, _text("Drawn amounts."), _table("Term loan", "100")),
    _section("Source register", 3, _table("K", "Annual filing")),
    _section("Source notes", 4, _text("One two.")),
    _section("Calculations", 2, _text("EBITDA 10 less capex 4 is 6.")),
    _section("Bridge", 3, _table("10", "4", "6")),
    _section("Gaps", 2, _text("Not supplied: the credit agreement.")),
    _section("Extra notes", 2, _text("One two three.")),
    _section("Next module", 2, _text("CP-2.")),
]
EXPECTED_PLACEMENT = [
    "audit", "audit", "audit", "audit", "view", "consumed", "consumed", "view", "reference",
    "audit", "audit", "calculations", "calculations", "limits", "audit", "audit",
]  # fmt: skip


def test_sections_are_placed_by_their_level_two_parent():
    assert store.placements(SECTIONS) == EXPECTED_PLACEMENT


AUDIT_HEADINGS = [
    "Exact source register",
    "Exact relied-on source register",
    "Supplied handoff",
    "Supplied handoffs",
    "All supplied current handoffs and lineage",
    "Source-context assessments",
    "Front matter",
    "Request",
]
VIEW_HEADINGS = [
    "Resource bridge and competing uses",
    "Source-gate reasoning and strongest contrary evidence",
    "Financing-source sufficiency boundary",
    "Calculation conventions and lineage",
    "Exact arithmetic and financial-lineage trace",
]


def test_audit_set_by_heading_under_findings_answer_key_from_the_ruling():
    """R31a key (from the deleted node test): eight headings go to audit, five do not."""
    headings = AUDIT_HEADINGS + VIEW_HEADINGS
    sections = [_section("Findings", 2)] + [_section(h, 3, _text("Body.")) for h in headings]
    placed = dict(zip(headings, store.placements(sections)[1:]))
    assert {h: placed[h] for h in AUDIT_HEADINGS} == dict.fromkeys(AUDIT_HEADINGS, "audit")
    assert {h: placed[h] for h in VIEW_HEADINGS} == dict.fromkeys(VIEW_HEADINGS, "view")


def test_words_count_cells_and_prose_not_headings_or_headers():
    assert store.report_fields(SECTIONS, {"confidence": "Medium"})["words"] == {
        "view": 6,
        "reference": 5,
        "calculations": 10,
        "limits": 5,
        "audit": 23,
    }


@pytest.mark.parametrize(
    "cell, expected",
    [
        ("Medium", True),
        ("Not assessable", False),
        ("not assessable.", False),
        (" Not Assessable", False),
    ],
)
def test_established_reads_the_confidence_cell(cell, expected):
    fields = store.report_fields(SECTIONS, {"confidence": cell})
    assert fields["state"]["established"] is expected


def test_no_reader_summary_is_neither():
    assert store.report_fields(SECTIONS, None)["state"]["established"] is None


def test_declared_is_the_front_matter_status_verbatim():
    fields = store.report_fields(SECTIONS, {"confidence": "Medium"})
    assert fields["state"]["declared"] == "Requires More Work"


@pytest.mark.parametrize(
    "front_matter, expected",
    [
        ("module: CP-6\ncommittee_status: Refer\ndepends_on: [CP-1]", "Refer"),
        ("module: CP-6\ncommittee_status:\ndepends_on: [CP-1]", None),
        ("committee_status:   \nrun_id: r1", None),
        ("module: CP-6\ncommittee_status:", None),
    ],
)
def test_empty_committee_status_is_no_status_not_the_next_line(front_matter, expected):
    sections = [
        {
            "heading": "Front matter",
            "level": 2,
            "line": 1,
            "blocks": [{"type": "text", "text": front_matter}],
        }
    ]
    assert store.report_fields(sections, None)["state"]["declared"] == expected


def test_declared_is_read_from_front_matter_the_parser_produced():
    sections = store.parse_source(REAL_FRONT_MATTER_HEAD + "\nBody line.\n")
    assert store.report_fields(sections, None)["state"]["declared"] == "Blocked"


def test_a_later_front_matter_heading_is_not_the_yaml_block():
    text = "## Request\nAsked.\n\n## Front matter\ncommittee_status: Refer\n"
    sections = store.parse_source(text)
    assert store.report_fields(sections, None)["state"]["declared"] is None


def test_a_leading_front_matter_heading_declares_like_the_yaml_block():
    # Accepted (sweep row B3): the parser gives a leading "## Front matter" section and a YAML
    # block the same shape, so a handoff that opens with that heading declares its status too.
    text = "## Front matter\ncommittee_status: Refer\n\n## Request\nAsked.\n"
    sections = store.parse_source(text)
    assert store.report_fields(sections, None)["state"]["declared"] == "Refer"


def test_declared_is_none_without_front_matter():
    sections = [s for s in SECTIONS if s["heading"] != "Front matter"]
    assert store.report_fields(sections, {"confidence": "Medium"})["state"]["declared"] is None


def test_every_built_output_carries_the_three_fields(tmp_path):
    data = read_store(tmp_path)
    (output,) = [o for o in data["outputs"].values() if o["module"] == "CP-1"]
    assert output["state"] == {"established": True, "declared": None}
    assert len(output["placement"]) == len(data["handoffs"][output["sha256"]])
    assert set(output["words"]) == {"view", "reference", "calculations", "limits", "audit"}


# Copied verbatim from the 2026-11-09 sol-medium run (runs/cpos-tdg-sol-medium-all-001, delivery
# abd687ca...c2baa, CP-1C.md): the head of a handoff that opens with YAML front matter.
REAL_FRONT_MATTER_HEAD = (
    Path(__file__).parent / "fixtures/sol_medium_run_2026_11_09/CP-1C-head.md"
).read_text(encoding="utf-8")


def test_yaml_front_matter_is_kept_as_a_leading_section():
    sections = store.parse_source(REAL_FRONT_MATTER_HEAD + "\nBody line.\n")
    lines = REAL_FRONT_MATTER_HEAD.split("\n")
    close = lines.index("---", 1)
    first, second = sections[0], sections[1]
    assert (first["heading"], first["level"], first["line"]) == ("Front matter", 2, 1)
    (block,) = first["blocks"]
    assert block["type"] == "text" and block["line"] == 2 and block["end"] == close
    assert block["text"] == "\n".join(lines[1:close])
    assert second["heading"] == "Request" and second["level"] == 2


def test_an_unclosed_front_matter_marker_still_raises():
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("---\nissuer_id: tdg\n\n## Request\n")


def test_body_after_the_front_matter_and_before_a_heading_still_raises():
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("---\na: 1\n---\nstray body\n# T\n")


@pytest.mark.parametrize(
    "heading",
    [
        "T2H.3 — Assumption register",
        "T2H.3 — assumption lock",
        "T2H.3 — assumption disposition",
        "T2H.3 — Assumptions and definition lock",
    ],
)
def test_the_assumption_register_is_found_by_its_register_id(heading):
    """Live runs tdg-forecast-001..005 (2026-11-10): the method fixes the id T2H.3, not the
    heading's wording, so the Forecast tab must not depend on that wording."""
    sections = [
        _section("T2H.2 — Historical-to-base bridge", 3, _table("a", "b", "c")),
        _section(heading, 3, _text("Vectors are ordered."), _table("B1", "Revenue growth", "0.1")),
    ]
    register = store.register_of(sections)
    assert register is not None and register["heading"] == heading
    assert register["rows"] == [["B1", "Revenue growth", "0.1"]]


def test_the_forecast_notes_send_no_case_elsewhere():
    """The notes do not claim a case lives elsewhere: every computed case is shown."""
    assert not any("stays in the calculation" in note for note in store.CASHFLOW_NOTES)


# Synthetic handoff sections: the chart tables the launcher asks the owning modules for.
def synthetic_charts(*chart_sections: str) -> dict:
    text = "## Findings\n\n" + "\n".join(chart_sections)
    return store.reader_fields(store.sections_of(text))


def chart_section(heading: str, header: str, *rows: str) -> str:
    cells = header.count("|") - 1
    body = "\n".join(rows)
    return f"### {heading}\n\n{header}\n|{' --- |' * cells}\n{body}\n"


BRIDGE_HEADER = "| Step | Amount | Reporting unit | Basis and limitation |"


def bridge(*amounts: str) -> str:
    rows = [f"| Step {i} | {a} | US$m | Synthetic. |" for i, a in enumerate(amounts)]
    return chart_section("Chart data: liquidity bridge", BRIDGE_HEADER, *rows)


def test_an_owner_period_table_is_a_chart_with_its_own_title_case_and_value_columns():
    header = "| Period | Revenue | Adjusted EBITDA | Reporting unit | Basis and limitation |"
    fields = synthetic_charts(
        chart_section(
            "Chart data: revenue and EBITDA",
            header,
            "| FY2023 | 2,100 | 410 | US$m | Synthetic. |",
            "| FY2024 | 2,250 | Not supplied: not stated | US$m | Synthetic. |",
        )
    )
    (chart,) = fields["charts"]
    assert fields["issue"] is None
    # The acronym keeps its case; only the first letter is raised.
    assert (chart["title"], chart["unit"], chart["columns"]) == (
        "Revenue and EBITDA",
        "US$m",
        [1, 2],
    )
    assert "kind" not in chart


def test_a_refinancing_need_table_is_a_two_series_period_chart():
    header = (
        "| Period | Debt maturing | Committed resources | Reporting unit | Basis and limitation |"
    )
    fields = synthetic_charts(
        chart_section(
            "Chart data: refinancing need",
            header,
            "| FY2026 | 500 | 300 | US$m | Synthetic. |",
        )
    )
    (chart,) = fields["charts"]
    assert (chart["title"], chart["columns"]) == ("Refinancing need", [1, 2])


def test_a_step_table_that_reconciles_is_a_bridge_chart():
    fields = synthetic_charts(bridge("900", "120", "-450", "570"))
    (chart,) = fields["charts"]
    assert fields["issue"] is None
    assert chart["kind"] == "waterfall" and chart["amount"] == 1 and chart["unit"] == "US$m"
    assert chart["title"] == "Liquidity bridge" and chart["columns"] == [1]


@pytest.mark.parametrize(
    "amounts",
    [("900", "120", "-450", "560"), ("900", "(450)", "450"), ("900", "x", "900"), ("900",)],
)
def test_a_step_table_that_does_not_reconcile_or_is_not_numeric_is_named_not_drawn(amounts):
    fields = synthetic_charts(bridge(*amounts))
    assert fields["charts"] == []
    assert "Chart data: liquidity bridge is not in its fixed table" in fields["issue"]


def test_a_step_table_with_no_amount_stated_is_not_drawn_and_not_an_error():
    gap = "Not supplied: reported in EUR m"
    fields = synthetic_charts(bridge(gap, gap, gap))
    assert fields["charts"] == [] and fields["issue"] is None


def test_a_bridge_stated_to_one_decimal_reconciles_exactly():
    assert synthetic_charts(bridge("0.1", "0.2", "0.3"))["charts"]
    assert not synthetic_charts(bridge("0.1", "0.2", "0.4"))["charts"]


def test_a_step_table_with_a_header_and_no_rows_is_named_not_drawn():
    fields = synthetic_charts(chart_section("Chart data: liquidity bridge", BRIDGE_HEADER))
    assert fields["charts"] == []
    assert "Chart data: liquidity bridge is not in its fixed table" in fields["issue"]


def test_a_step_table_with_another_header_is_not_taken_as_an_unsupplied_bridge():
    header = "| Step | Amount | Note | Reporting unit | Basis and limitation |"
    gap = "| Step 0 | Not supplied: none | n | US$m | Synthetic. |"
    fields = synthetic_charts(chart_section("Chart data: liquidity bridge", header, gap))
    assert fields["charts"] == [] and fields["issue"]


# ---- Package 2 (2026-11-10): the credit-structure tables. Every value is synthetic.
STACK_HEADER = (
    "| Facility | Ranking | Secured | Amount | Cumulative leverage | Reporting unit "
    "| Basis and limitation |"
)
COVENANT_HEADER = (
    "| Test | Threshold | Current | Headroom | Direction | Reporting unit | Basis and limitation |"
)
TRIGGER_HEADER = (
    "| Agency | Trigger | Threshold | Current | Direction | Reporting unit | Basis and limitation |"
)
LIMITS_HEADER = (
    "| Limit | Current exposure | Proposed exposure | Limit value | Reporting unit "
    "| Basis and limitation |"
)


def stack(*rows: str) -> str:
    return chart_section("Chart data: debt stack", STACK_HEADER, *rows)


def test_a_debt_stack_is_a_stack_chart_with_its_amount_and_leverage_columns():
    fields = synthetic_charts(
        stack(
            "| Term loan | 1 | Yes | 1,200 | 2.4 | US$m | Synthetic. |",
            "| Notes | 2 | No | Not supplied: not stated | Not supplied: no balance | US$m | S. |",
        )
    )
    (chart,) = fields["charts"]
    assert fields["issue"] is None
    assert chart["kind"] == "stack" and chart["title"] == "Debt stack" and chart["unit"] == "US$m"
    assert (chart["label"], chart["rank"], chart["secured"]) == (0, 1, 2)
    assert (chart["amount"], chart["leverage"]) == (3, 4)


@pytest.mark.parametrize(
    "rows",
    [
        ("| A | senior | Yes | 100 | 1.0 | US$m | S. |",),
        ("| A | 2 | Yes | 100 | 1.0 | US$m | S. |", "| B | 1 | Yes | 100 | 2.0 | US$m | S. |"),
        ("| A | 1 | Yes | 1.2bn | 1.0 | US$m | S. |",),
        ("| A | 1 | Yes | 100 | 1x | US$m | S. |",),
    ],
)
def test_a_debt_stack_out_of_shape_is_named_not_drawn(rows):
    fields = synthetic_charts(stack(*rows))
    assert fields["charts"] == []
    assert "Chart data: debt stack is not in its fixed table" in fields["issue"]


def test_a_covenant_table_is_a_bullet_chart_whose_unit_is_shared_only_when_it_is():
    fields = synthetic_charts(
        chart_section(
            "Chart data: covenant headroom",
            COVENANT_HEADER,
            "| Net leverage | 5.0 | 4.2 | 0.8x | Passes at or below | x | S. |",
            "| Liquidity | 100 | 150 | 50 | Passes at or above | US$m | S. |",
        )
    )
    (chart,) = fields["charts"]
    assert chart["kind"] == "bullet" and chart["title"] == "Covenant headroom"
    assert chart["unit"] == ""  # Rows state their own units; none is claimed for the figure.
    assert (chart["label"], chart["threshold"], chart["current"]) == ([0], 1, 2)
    assert (chart["headroom"], chart["direction"]) == (3, 4)


def test_a_rating_trigger_table_is_the_same_bullet_chart_with_no_stated_headroom():
    fields = synthetic_charts(
        chart_section(
            "Chart data: rating triggers",
            TRIGGER_HEADER,
            "| Agency A | Net leverage review | 5.5 | 4.2 | Passes below | x | S. |",
        )
    )
    (chart,) = fields["charts"]
    assert chart["kind"] == "bullet" and chart["unit"] == "x"
    assert (chart["label"], chart["threshold"], chart["current"]) == ([0, 1], 2, 3)
    assert chart["headroom"] is None and chart["direction"] == 4


@pytest.mark.parametrize(
    "row",
    [
        "| T | 5.0x | 4.2 | 0.8x | Passes at or below | x | S. |",
        "| T | 5.0 | 4.2 | 0.8x | Under | x | S. |",
        "| T | 5.0 | 4.2 | 0.8x | Passes at or below |  | S. |",
    ],
)
def test_a_covenant_row_out_of_shape_is_named_not_drawn(row):
    fields = synthetic_charts(chart_section("Chart data: covenant headroom", COVENANT_HEADER, row))
    assert fields["charts"] == []
    assert "Chart data: covenant headroom is not in its fixed table" in fields["issue"]


def test_a_portfolio_limit_table_is_a_limits_chart_and_a_gap_is_allowed():
    fields = synthetic_charts(
        chart_section(
            "Chart data: portfolio limits",
            LIMITS_HEADER,
            "| Single issuer | 3.0 | Not supplied: no proposal | 5.0 | % NAV | S. |",
        )
    )
    (chart,) = fields["charts"]
    assert fields["issue"] is None
    assert chart["kind"] == "limits" and chart["unit"] == "% NAV"
    assert (chart["label"], chart["current"], chart["proposed"], chart["limit"]) == (0, 1, 2, 3)


# ---- Package 3 (2026-11-10): the comparison tables. Every value is synthetic.
PAIR_HEADER = (
    "| Measure | Prior period | Prior | Current period | Current | Reporting unit "
    "| Basis and limitation |"
)
PEER_HEADER = (
    "| Metric | Issuer | Peer low | Peer median | Peer high | Peer count | Reporting unit "
    "| Basis and limitation |"
)
YIELD_HEADER = (
    "| Instrument | Maturity date | Yield | Spread | Quote date | Source class | Reporting unit "
    "| Basis and limitation |"
)
RESULTS = "Chart data: prior and current results"
KPIS = "Chart data: margin and KPI changes"
RESULT_ROWS = (
    "| Revenue | FY2023 | 2,100 | FY2024 | 2,250 | US$m | S. |",
    "| EBITDA | FY2023 | Not supplied: not stated | FY2024 | 410 | US$m | S. |",
)


def test_prior_and_current_results_are_grouped_columns_over_one_unit():
    (chart,) = synthetic_charts(chart_section(RESULTS, PAIR_HEADER, *RESULT_ROWS))["charts"]
    assert chart["kind"] == "grouped" and chart["title"] == "Prior and current results"
    assert (chart["columns"], chart["sub"], chart["unit"]) == ([2, 4], [1, 3], "US$m")


def test_prior_and_current_results_in_two_units_are_named_not_drawn():
    rows = (RESULT_ROWS[0], RESULT_ROWS[1].replace("US$m", "%"))
    fields = synthetic_charts(chart_section(RESULTS, PAIR_HEADER, *rows))
    assert fields["charts"] == [] and f"{RESULTS} is not in its fixed table" in fields["issue"]


def test_margin_and_kpi_changes_are_a_dumbbell_whose_rows_state_their_own_unit():
    rows = ("| EBITDA margin | FY2023 | 19.5 | FY2024 | 21.0 | % | S. |", RESULT_ROWS[0])
    (chart,) = synthetic_charts(chart_section(KPIS, PAIR_HEADER, *rows))["charts"]
    assert chart["kind"] == "dumbbell" and chart["unit"] == ""
    assert (chart["label"], chart["periods"], chart["prior"], chart["current"]) == (0, [1, 3], 2, 4)


@pytest.mark.parametrize(
    ("heading", "row"),
    [
        ("Chart data: another pair table", RESULT_ROWS[0]),
        (RESULTS, "| Revenue | FY2023 | 2.1bn | FY2024 | 2,250 | US$m | S. |"),
        (KPIS, "| EBITDA margin | FY2023 | 19.5 | FY2024 | 21.0 |  | S. |"),
    ],
)
def test_a_pair_table_out_of_shape_is_named_not_drawn(heading, row):
    fields = synthetic_charts(chart_section(heading, PAIR_HEADER, row))
    assert fields["charts"] == [] and f"{heading} is not in its fixed table" in fields["issue"]


@pytest.mark.parametrize(
    "heading", ["Chart data: peer range — percent metrics", "Chart data: peer range — multiples"]
)
def test_a_peer_range_is_a_range_chart_and_a_gap_is_allowed(heading):
    fields = synthetic_charts(
        chart_section(
            heading,
            PEER_HEADER,
            "| EBITDA margin | 21.0 | 12.0 | 18.5 | 26.0 | 7 | % | S. |",
            "| FFO / debt | Not supplied: not stated | 8.0 | 15.0 | 22.0 | 6 | % | S. |",
        )
    )
    (chart,) = fields["charts"]
    assert fields["issue"] is None and chart["kind"] == "range" and chart["unit"] == "%"
    roles = (chart["label"], chart["issuer"], chart["low"], chart["median"], chart["high"])
    assert roles == (0, 1, 2, 3, 4) and chart["count"] == 5


def test_a_peer_range_with_a_percent_sign_in_a_number_is_named_not_drawn():
    row = "| EBITDA margin | 21% | 12.0 | 18.5 | 26.0 | 7 | % | S. |"
    heading = "Chart data: peer range — percent metrics"
    fields = synthetic_charts(chart_section(heading, PEER_HEADER, row))
    assert fields["charts"] == [] and "is not in its fixed table" in fields["issue"]


def test_yield_against_maturity_is_a_scatter_with_its_date_yield_and_text_columns():
    fields = synthetic_charts(
        chart_section(
            "Chart data: yield against maturity",
            YIELD_HEADER,
            "| 2028 note | 2028-06-15 | 6.4 | +310 bp | 2024-12-31 | Dealer quote | % | S. |",
            "| 2031 note | 2031-03-01 | Not supplied: no quote | Not supplied: no quote "
            "| 2024-12-31 | Dealer quote | % | S. |",
        )
    )
    (chart,) = fields["charts"]
    assert fields["issue"] is None and chart["kind"] == "scatter" and chart["unit"] == "%"
    assert (chart["label"], chart["date"], chart["yield"]) == (0, 1, 2)
    assert (chart["spread"], chart["quoted"], chart["source"]) == (3, 4, 5)


def test_a_yield_that_is_not_a_plain_number_is_named_not_drawn():
    row = "| 2028 note | 2028-06-15 | 6.4% | +310 bp | 2024-12-31 | Dealer quote | % | S. |"
    fields = synthetic_charts(
        chart_section("Chart data: yield against maturity", YIELD_HEADER, row)
    )
    assert fields["charts"] == [] and "is not in its fixed table" in fields["issue"]


@pytest.mark.parametrize("when", ["2028-13-01", "2028-00-10", "9999-99-99", "2028-02-31"])
@pytest.mark.parametrize("column", [1, 4])
def test_a_yield_row_with_an_invalid_calendar_date_is_named_not_drawn(when, column):
    cells = ["2028 note", "2028-06-15", "6.4", "+310 bp", "2024-12-31", "Dealer quote", "%", "S."]
    cells[column] = when
    row = "| " + " | ".join(cells) + " |"
    fields = synthetic_charts(
        chart_section("Chart data: yield against maturity", YIELD_HEADER, row)
    )
    assert fields["charts"] == [] and "is not in its fixed table" in fields["issue"]


@pytest.mark.parametrize("count", ["-3", "2.5", "1,0", "seven"])
def test_a_peer_count_that_is_not_a_whole_number_is_named_not_drawn(count):
    row = f"| EBITDA margin | 21.0 | 12.0 | 18.5 | 26.0 | {count} | % | S. |"
    heading = "Chart data: peer range \u2014 percent metrics"
    fields = synthetic_charts(chart_section(heading, PEER_HEADER, row))
    assert fields["charts"] == [] and "is not in its fixed table" in fields["issue"]


def test_a_peer_count_of_zero_is_a_stated_count():
    row = "| EBITDA margin | 21.0 | 12.0 | 18.5 | 26.0 | 0 | % | S. |"
    heading = "Chart data: peer range \u2014 percent metrics"
    assert len(synthetic_charts(chart_section(heading, PEER_HEADER, row))["charts"]) == 1


# ---- Package 4 (2026-11-10): recovery by class and the value allocation. Every value is synthetic.
RECOVERY_HEADER = (
    "| Class | Scenario | Claim | Recovery | Recovery % | Reporting unit | Basis and limitation |"
)
RECOVERY = "Chart data: recovery by class"
RECOVERY_ROWS = (
    "| Senior | Base | 1,200 | 1,080 | 90 | US$m | S. |",
    "| Senior | Downside | 1,200 | Not supplied: no value | Not supplied: no value | US$m | S. |",
)
ALLOCATION = "Chart data: value allocation — scenario 2"


def test_recovery_by_class_is_a_recovery_chart_over_one_unit_and_a_gap_is_allowed():
    fields = synthetic_charts(chart_section(RECOVERY, RECOVERY_HEADER, *RECOVERY_ROWS))
    (chart,) = fields["charts"]
    assert fields["issue"] is None and chart["kind"] == "recovery" and chart["unit"] == "US$m"
    roles = (chart["label"], chart["scenario"], chart["claim"], chart["recovery"], chart["percent"])
    assert roles == (0, 1, 2, 3, 4) and chart["title"] == "Recovery by class"


@pytest.mark.parametrize(
    "row",
    [
        "| Senior | Base | 1,200 | 1,080 | 90% | US$m | S. |",
        "| Senior | Base | 1,200 | 1,080 | 90 | EUR m | S. |",
        "| Senior |  | 1,200 | 1,080 | 90 | US$m | S. |",
    ],
)
def test_a_recovery_table_out_of_shape_or_in_two_units_is_named_not_drawn(row):
    fields = synthetic_charts(chart_section(RECOVERY, RECOVERY_HEADER, RECOVERY_ROWS[0], row))
    if "EUR" not in row:
        fields = synthetic_charts(chart_section(RECOVERY, RECOVERY_HEADER, row))
    assert fields["charts"] == [] and f"{RECOVERY} is not in its fixed table" in fields["issue"]


def test_a_value_allocation_is_a_waterfall_from_enterprise_value_to_the_value_not_distributed():
    fields = synthetic_charts(
        chart_section(
            ALLOCATION,
            BRIDGE_HEADER,
            "| Enterprise value | 1,500 | US$m | S. |",
            "| Costs | -100 | US$m | S. |",
            "| Senior distribution | -720 | US$m | S. |",
            "| Value not distributed | 680 | US$m | S. |",
        )
    )
    (chart,) = fields["charts"]
    assert chart["kind"] == "waterfall" and chart["title"] == "Value allocation — scenario 2"


def test_a_value_allocation_that_does_not_reconcile_is_named_not_drawn_and_a_gap_draws_nothing():
    rows = (
        "| Enterprise value | 1,500 | US$m | S. |",
        "| Value not distributed | 700 | US$m | S. |",
    )
    fields = synthetic_charts(chart_section(ALLOCATION, BRIDGE_HEADER, *rows))
    assert fields["charts"] == [] and "is not in its fixed table" in fields["issue"]
    gap = "| {} | Not supplied: no valuation row | US$m | S. |"
    gaps = (gap.format("Enterprise value"), gap.format("Value not distributed"))
    fields = synthetic_charts(chart_section(ALLOCATION, BRIDGE_HEADER, *gaps))
    assert fields["charts"] == [] and fields["issue"] is None


# ---- Package 5 (2026-11-10): the calendar lanes. Every value is synthetic.
EVENT_HEADER = (
    "| Event date | Date precision | Published | Event | Status | Source | Credit relevance |"
)
EVENT_ROWS = (
    "| 2025-03-31 | day | — | Note matures | Scheduled — due | Indenture p.1 | Wall |",
    "| 2025-06 | month | 2025-05-01 | Call window | Historical — announced | Notice | Cost |",
    "| 2025-Q3 | quarter | — | Review | Scenario — modelled | Memo | Rating |",
    "| 2026 | year | — | Maturity | Scheduled — due | Filing p.2 | Wall |",
)


def lane_fields(*rows: str, lane: str = "Financing") -> dict:
    return synthetic_charts(chart_section(f"Events: {lane}", EVENT_HEADER, *rows))


def test_an_event_table_is_a_lane_named_by_its_heading_and_is_not_a_chart():
    fields = lane_fields(*EVENT_ROWS)
    (lane,) = fields["events"]
    assert fields["issue"] is None and fields["charts"] == []
    assert lane["lane"] == "Financing" and lane["gap"] is None and isinstance(lane["table"], int)


def test_an_event_table_of_only_not_supplied_is_a_lane_with_its_reason():
    gap = "Not supplied: the handoff states no dated event"
    fields = lane_fields(f"| {gap} |" + f" {gap} |" * 6)
    assert fields["issue"] is None
    assert fields["events"][0]["gap"] == "the handoff states no dated event"


@pytest.mark.parametrize(
    "row",
    [
        "| 2025-03 | day | — | E | S | Src | R |",
        "| 2025-02-30 | day | — | E | S | Src | R |",
        "| 2025-03-31 | month | — | E | S | Src | R |",
        "| 2025-Q5 | quarter | — | E | S | Src | R |",
        "| 2025 | week | — | E | S | Src | R |",
        "| 2025-03-31 | day | May 2025 | E | S | Src | R |",
        "| 2025-03-31 | day | — | | S | Src | R |",
        "| Not supplied: undated | day | — | E | S | Src | R |",
    ],
)
def test_an_event_table_out_of_shape_is_named_not_drawn(row):
    fields = lane_fields(EVENT_ROWS[0], row)
    assert (
        fields["events"] == [] and "Events: Financing is not in its fixed table" in fields["issue"]
    )


def test_an_event_table_with_a_changed_header_is_named_not_drawn():
    header = EVENT_HEADER.replace("Event date", "Date")
    fields = synthetic_charts(chart_section("Events: Legal", header, EVENT_ROWS[0]))
    assert fields["events"] == [] and "Events: Legal is not in its fixed table" in fields["issue"]


@pytest.mark.parametrize(
    "row",
    [
        "| 2025-03-31 | day | — | E | Scheduled | Src | R |",
        "| 2025-03-31 | day | — | E | Expected — due | Src | R |",
        "| 2025-03-31 | day | 2025-03-31 | E | Scheduled — due | Src | R |",
    ],
)
def test_an_event_without_a_status_kind_or_with_a_redundant_published_date_is_not_drawn(row):
    assert lane_fields(EVENT_ROWS[0], row)["events"] == []
