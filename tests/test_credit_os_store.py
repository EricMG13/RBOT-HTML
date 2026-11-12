"""Credit OS's store reads a synthetic workspace built by tests/library_fixtures.py."""

import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest
import library_fixtures
from library_fixtures import make_run, without_report

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
    assert "reports" not in result
    assert result["issues"] == []


def test_store_has_no_legacy_routes(tmp_path):
    result = read_store(tmp_path)
    assert result["pins"] == {}
    assert set(result["runs"]) == {"run-a"}
    assert result["outputs"]
    for link in [o["href"] for o in result["outputs"].values()]:
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


def test_every_owner_row_table_can_state_none_without_a_chart_or_problem():
    from deploy_workflow.owners import cpos_launch as launcher

    gap = "Not supplied: no sourced quantity"
    for specs in launcher.OWNER_TABLES.values():
        for spec in specs:
            if not spec.columns or spec.bare:
                continue
            headers = [*spec.columns, "Reporting unit", "Basis and limitation"]
            cells = [gap] * len(spec.columns) + ["US$m", "Synthetic absence."]
            text = chart_section(
                spec.heading, "| " + " | ".join(headers) + " |", "| " + " | ".join(cells) + " |"
            )
            fields = synthetic_charts(text)
            assert launcher.chart_issues(text, spec) == ()
            assert fields["charts"] == [] and fields["issue"] is None, spec.heading
            assert fields["chartGaps"][0]["gap"] == "no sourced quantity"
            invalid = text.replace("Synthetic absence.", "")
            assert launcher.chart_issues(invalid, spec)
            assert synthetic_charts(invalid)["issue"], spec.heading


@pytest.mark.parametrize(
    "name,rows",
    [
        (
            "debt stack",
            [
                ["Loan", "1", "Yes", "500", "2", "US$m", "S"],
                ["Notes", "2", "No", "400", "3", "EURm", "S"],
            ],
        ),
        (
            "liquidity bridge",
            [
                ["Open", "100", "US$m", "S"],
                ["Draw", "50", "EURm", "S"],
                ["Close", "150", "US$m", "S"],
            ],
        ),
        ("liquidity bridge", [["Open", "100", "EURm", "S"], ["Close", "100", "EURm", "S"]]),
        ("peer range — multiples", [["Leverage", "4", "6", "5", "3", "5", "x", "S"]]),
        (
            "recovery by class",
            [["Senior", f"S{n}", "100", "50", "50", "US$m", "S"] for n in range(4)],
        ),
        (
            "recovery by class",
            [
                ["Senior", "Base", "100", "50", "50", "US$m", "S"],
                ["Senior", "Base", "100", "20", "20", "US$m", "S"],
            ],
        ),
        (
            "yield against maturity",
            [["Notes", "2020-01-01", "7.5", "450 bp", "2025-01-01", "Dealer quote", "%", "S"]],
        ),
        ("revenue and EBITDA", [["FY2024", "100", "20", "EURm", "S"]]),
    ],
)
def test_the_store_refuses_the_launchers_invalid_chart_tables(name, rows):
    from deploy_workflow.owners import cpos_launch as launcher

    spec = next(
        t for ts in launcher.OWNER_TABLES.values() for t in ts if t.heading == f"Chart data: {name}"
    )
    text = chart_section(
        spec.heading,
        "| " + " | ".join(launcher._chart_header(spec)) + " |",
        *("| " + " | ".join(row) + " |" for row in rows),
    )
    assert launcher.chart_issues(text, spec), name
    fields = synthetic_charts(text)
    assert not fields["charts"] and fields["issue"], name


def test_the_calendar_draws_the_cp6_user_reminder_status():
    fields = lane_fields("| 2026-01-15 | day | — | Review | User reminder | Analyst note | Due |")
    assert fields["events"] and fields["issue"] is None


def test_launcher_and_store_accept_every_independently_written_owner_fixture():
    from test_cpos_launch import OWNER_TABLES as examples

    from deploy_workflow.owners import cpos_launch as launcher

    specs = {s.heading: s for ts in launcher.OWNER_TABLES.values() for s in ts}
    fixtures = {heading: body for tables in examples.values() for heading, body in tables.items()}
    fixtures["Chart data: value allocation — scenario 3"] = (
        f"{BRIDGE_HEADER}\n| --- | --- | --- | --- |\n"
        "| Opening value | 400 | US$m | Synthetic third scenario. |\n"
        "| Closing value | 400 | US$m | Synthetic third scenario. |\n"
    )
    assert fixtures.keys() == specs.keys()
    for heading, body in fixtures.items():
        text = f"### {heading}\n\n{body}\n"
        assert launcher.chart_issues(text, specs[heading]) == (), heading
        fields = synthetic_charts(text)
        assert fields["issue"] is None, heading
        assert len(fields["charts"] + fields["maps"] + fields["events"]) == 1, heading
    assert store.EVENT_HEADERS == list(launcher.EVENT_COLUMNS)
    assert store.EVENT_STATUS.pattern == launcher.EVENT_STATUS.pattern
    assert store.DIRECTIONS == launcher.DIRECTIONS


def test_a_period_gap_in_another_currency_does_not_relabel_the_numeric_values():
    from deploy_workflow.owners import cpos_launch as launcher

    text = chart_section(
        "Chart data: revenue and EBITDA",
        "| Period | Revenue | Adjusted EBITDA | Reporting unit | Basis and limitation |",
        "| FY2023 | Not supplied: reported in EURm | Not supplied: reported in EURm | EURm | S |",
        "| FY2024 | 100 | 20 | US$m | S |",
    )
    spec = launcher.OWNER_TABLES["CP-1"][0]
    assert launcher.chart_issues(text, spec) == ()
    fields = synthetic_charts(text)
    assert fields["issue"] is None and fields["charts"][0]["unit"] == "US$m"


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


# ---- Package 6 (2026-11-10): the node/edge maps. Every value is synthetic.
EDGE_HEADER = "| From | Relationship | Edge type | To | Evidence |"


def map_fields(*rows: str, name: str = "stress scenario") -> dict:
    return synthetic_charts(chart_section(f"Map: {name}", EDGE_HEADER, *rows))


def test_an_edge_table_is_a_map_named_by_its_heading_and_is_not_a_chart():
    fields = map_fields(
        "| A | rel | Assumption | B | p.1 |", "| B | rel | Test outcome | C | p.2 |"
    )
    (drawn,) = fields["maps"]
    assert fields["issue"] is None and fields["charts"] == []
    assert drawn["name"] == "stress scenario" and drawn["gap"] is None
    assert isinstance(drawn["table"], int)


def test_an_edge_table_of_only_not_supplied_is_a_map_with_its_reason():
    gap = "Not supplied: no scenario stated"
    fields = map_fields(f"| {gap} |" + f" {gap} |" * 4)
    assert fields["issue"] is None and fields["maps"][0]["gap"] == "no scenario stated"


@pytest.mark.parametrize(
    "row",
    [
        "| A | rel | Weighted | B | p.1 |",
        "| A | rel | assumption | B | p.1 |",
        "| | rel | Assumption | B | p.1 |",
        "| A | rel | Assumption | B | |",
        "| A | Not supplied: none | Assumption | B | p.1 |",
    ],
)
def test_an_edge_table_out_of_shape_is_named_not_drawn(row):
    fields = map_fields("| A | rel | Assumption | B | p.1 |", row)
    assert (
        fields["maps"] == [] and "Map: stress scenario is not in its fixed table" in fields["issue"]
    )


def test_an_edge_type_belongs_to_its_own_map_and_an_unknown_map_is_not_drawn():
    assert map_fields("| A | r | Ownership | B | p |", name="stress scenario")["maps"] == []
    assert map_fields("| A | r | Ownership | B | p |", name="legal entities")["maps"]
    assert map_fields("| A | r | Ownership | B | p |", name="unknown")["maps"] == []


def test_the_store_vocabulary_is_the_launchers():
    from deploy_workflow.owners.cpos_launch import MAPS

    assert {f"Map: {k}": v for k, v in store.MAP_EDGES.items()} == {h: t for h, _, t, _ in MAPS}


@pytest.mark.parametrize("dash", ["—", "-", "–"])
def test_an_edge_whose_evidence_is_a_dash_is_not_drawn(dash):
    fields = map_fields(f"| A | rel | Assumption | B | {dash} |")
    assert fields["maps"] == [] and "is not in its fixed table" in fields["issue"]


# ---- Package 7 fix round: revisions (synthetic values).
def test_recorded_revisions_read_the_cap_and_attachments_files(tmp_path):
    (tmp_path / "research").mkdir()
    (tmp_path / "cap.json").write_text(
        json.dumps({"cap_usd": "1", "replayed_from_run": "run-id-1"})
    )
    (tmp_path / "research/attachments.json").write_text(json.dumps({"supersedes": "run-id-2"}))
    issues = []
    assert store.recorded_revisions(tmp_path, issues) == [
        ("Rerun of", "run-id-1"),
        ("Supersedes", "run-id-2"),
    ]
    assert issues == []
    assert store.recorded_revisions(tmp_path / "none", issues) == [] and issues == []


def test_an_unreadable_revision_record_is_named(tmp_path):
    (tmp_path / "cap.json").write_text("{not json")
    issues = []
    assert store.recorded_revisions(tmp_path, issues) == []
    assert len(issues) == 1 and "cap.json" in issues[0]


def test_a_rerun_links_to_the_run_it_replays_through_the_store(tmp_path):
    rows = []
    for name, as_of in (("run-a", "2025-12-31"), ("run-b", "2025-06-30")):
        run_dir = make_run(tmp_path, name, as_of=as_of)
        (delivery,) = (run_dir / "deliveries").iterdir()
        folder = f"runs/{name}/deliveries/{delivery.name}"
        digest = hashlib.sha256((delivery / "report.html").read_bytes()).hexdigest()
        artifact = {
            "folder": folder,
            "label": name,
            "state": "final",
            "available": True,
            "href": f"/files/{folder}/report.html?sha256={digest}",
        }
        rows.append({"id": name, "name": name, "sector": "", "period": "", "artifacts": [artifact]})
    earlier = json.loads((tmp_path / "runs/run-a/workflow.json").read_text())["run"]["run_id"]
    (tmp_path / "runs/run-b/cap.json").write_text(json.dumps({"replayed_from_run": earlier}))
    built = store.workspace_store(tmp_path, {"real": rows, "issues": []})
    assert built["runs"]["run-b"]["revisions"] == [
        {"word": "Rerun of", "id": earlier, "run": "run-a"}
    ]
    assert built["runs"]["run-a"]["revisions"] == []


def test_a_delivery_without_report_html_builds_the_store(tmp_path):
    """New CP-OS deliveries carry no report.html (their completion record has delivery_sha256)."""
    run_dir = make_run(tmp_path, "run-a")
    delivered = without_report(run_dir)
    assert not (delivered / "report.html").exists()
    folder = f"runs/run-a/deliveries/{delivered.name}"
    artifact = {"folder": folder, "label": "r", "state": "final", "available": True, "href": None}
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": [artifact]}
    result = store.workspace_store(tmp_path, {"real": [row], "issues": []})
    assert result["issues"] == []
    assert set(result["runs"]) == {"run-a"}
    assert {o["module"] for o in result["outputs"].values()} == set(MODULES)


@pytest.mark.parametrize(
    "view",
    [{"no_run": True}, {"run": {"issuer_name": "Issuer"}}, {"run": {"run_id": "run-a"}}, [1]],
    ids=["no-run", "no-run-id", "no-issuer-name", "not-an-object"],
)
def test_a_delivery_whose_view_states_no_run_identity_is_named_in_the_issues(tmp_path, view):
    run_dir = make_run(tmp_path, "run-a")
    (delivered,) = (run_dir / "deliveries").iterdir()
    raw = json.dumps(view).encode()
    (delivered / "view.json").write_bytes(raw)
    receipt = json.loads((delivered / "delivery.json").read_text())
    receipt["files"]["view.json"] = hashlib.sha256(raw).hexdigest()
    (delivered / "delivery.json").write_text(json.dumps(receipt))
    artifact = {
        "folder": f"runs/run-a/deliveries/{delivered.name}",
        "label": "r",
        "state": "final",
        "available": True,
        "href": None,
    }
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": [artifact]}
    result = store.workspace_store(tmp_path, {"real": [row], "issues": []})
    assert [i for i in result["issues"] if "could not be read" in i and delivered.name in i]


def test_a_delivery_that_cannot_be_read_is_named_in_the_issues(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    (delivered,) = (run_dir / "deliveries").iterdir()
    (delivered / "delivery.json").write_text("{not json")
    artifact = {
        "folder": f"runs/run-a/deliveries/{delivered.name}",
        "label": "r",
        "state": "final",
        "available": True,
        "href": None,
    }
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": [artifact]}
    result = store.workspace_store(tmp_path, {"real": [row], "issues": []})
    assert [i for i in result["issues"] if "could not be read" in i and delivered.name in i]


def evidence_of(tmp_path: Path, **changes) -> dict:
    """The Evidence record of one fixture run (no published model)."""
    make_run(tmp_path, "run-a", **changes)
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": []}
    result = store.workspace_store(tmp_path, {"real": [row], "issues": []})
    assert result["issues"] == []
    return result["runs"]["run-a"]["evidence"]


def test_evidence_lists_supplied_files_by_who_read_them(tmp_path):
    names = ("A_report.pdf", "B_filing.htm.jsonl", "C_unread.pdf")
    # CP-0's Sources section names A and B; CP-1's names only A. Nothing names C.
    evidence = evidence_of(
        tmp_path, supplied=names, cp0_extra="- A_report.pdf\n- B_filing.htm.jsonl\n"
    )
    assert [
        (s["name"], s["type"], s["documentDate"], s["readBy"]) for s in evidence["sources"]
    ] == [
        ("A_report.pdf", "pdf", None, ["CP-0"]),
        ("B_filing.htm.jsonl", "htm.jsonl", None, ["CP-0"]),
    ]
    assert [(s["name"], s["type"], s["readBy"]) for s in evidence["unused"]] == [
        ("C_unread.pdf", "pdf", [])
    ]
    expected = hashlib.sha256(b"text of C_unread.pdf\n").hexdigest()
    assert evidence["unused"][0]["sha256"] == expected


def test_evidence_does_not_list_the_earlier_runs_handoffs_pinned_for_cp8(tmp_path):
    # CP-8's pinned `prior/<module>.md` sources are not files the issuer supplied; even one a
    # handoff names is neither a source read nor "Supplied, not used".
    evidence = evidence_of(
        tmp_path,
        supplied=("A_report.pdf", "prior/CP-1.md"),
        cp0_extra="- A_report.pdf\n- prior/CP-1.md\n",
    )
    assert [s["name"] for s in evidence["sources"]] == ["A_report.pdf"]
    assert evidence["unused"] == []


def test_evidence_document_date_is_the_cell_a_handoff_table_records_for_the_file(tmp_path):
    names = ("A_report.pdf", "B_2024-01-01_filing.pdf", "C_other.pdf")
    # Hand-written: the date text is copied as stored (not parsed, not taken from a file name);
    # B's row has an empty date cell; C appears in no Document date table.
    register = (
        "\n| Source | Type | Document date | Readiness |\n| --- | --- | --- | --- |\n"
        "| A_report.pdf | Annual report | 31 March 2025 (audited) | Readable |\n"
        "| B_2024-01-01_filing.pdf | Filing |  | Readable |\n"
    )
    evidence = evidence_of(tmp_path, supplied=names, cp0_extra=register)
    found = {s["name"]: s["documentDate"] for s in evidence["sources"] + evidence["unused"]}
    assert found == {
        "A_report.pdf": "31 March 2025 (audited)",
        "B_2024-01-01_filing.pdf": None,
        "C_other.pdf": None,
    }


def test_evidence_a_name_outside_the_sources_section_is_not_a_read(tmp_path):
    # The name appears in CP-1's Findings (cp1_findings sits before Sources), not in its Sources.
    evidence = evidence_of(
        tmp_path, supplied=("A_report.pdf",), cp1_findings="Mentioned: A_report.pdf.\n\n"
    )
    assert evidence["sources"] == []
    assert [s["name"] for s in evidence["unused"]] == ["A_report.pdf"]


def test_evidence_no_sources_section_anywhere_is_use_not_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(
        library_fixtures,
        "HANDOFF",
        library_fixtures.HANDOFF.replace("## Sources\n- fixture\n", "## Gaps\n- none\n"),
    )
    evidence = evidence_of(tmp_path, supplied=("A_report.pdf", "B_filing.pdf"))
    assert evidence["unused"] == []
    assert [s["name"] for s in evidence["unrecorded"]] == ["A_report.pdf", "B_filing.pdf"]
    assert evidence["noSourcesModules"] == ["CP-0", "CP-1"]


def test_evidence_some_handoffs_without_sources_stay_unused_and_are_named(tmp_path, monkeypatch):
    class WithoutSourcesInCP1(str):
        def format(self, **fields):
            text = str(self)
            if fields["module"] == "CP-1":
                text = text.replace("## Sources\n- fixture\n", "## Gaps\n- none\n")
            return str.format(text, **fields)

    monkeypatch.setattr(library_fixtures, "HANDOFF", WithoutSourcesInCP1(library_fixtures.HANDOFF))
    evidence = evidence_of(
        tmp_path, supplied=("A_report.pdf", "B_other.pdf"), cp0_extra="- A_report.pdf\n"
    )
    assert evidence["noSourcesModules"] == ["CP-1"]
    assert evidence["unrecorded"] == []
    assert [s["name"] for s in evidence["sources"]] == ["A_report.pdf"]
    assert [s["name"] for s in evidence["unused"]] == ["B_other.pdf"]


def test_evidence_a_file_is_read_only_when_a_sources_token_is_exactly_its_name(tmp_path):
    names = ("report.pdf", "annual-report.pdf", "Q3 results.pdf", "notes.txt", "other.pdf")
    sources = (
        "- annual-report.pdf\n"  # a list item: only the longer name is named
        "Also: Q3 results.pdf, notes.txt.\n"  # a name with a space; "notes.txt." is not the name
        "\n| File | Role |\n| --- | --- |\n| other.pdf | Primary |\n"  # a table cell
    )
    evidence = evidence_of(tmp_path, supplied=names, cp0_extra=sources)
    read = {f["name"]: f["readBy"] for f in evidence["sources"]}
    assert read == {
        "annual-report.pdf": ["CP-0"],
        "Q3 results.pdf": ["CP-0"],
        "other.pdf": ["CP-0"],
    }
    assert [f["name"] for f in evidence["unused"]] == ["report.pdf", "notes.txt"]


def test_evidence_handoffs_hashes_calls_and_cap_are_as_recorded(tmp_path):
    evidence = evidence_of(tmp_path, supplied=("A_report.pdf",))
    folder = tmp_path / "runs/run-a"
    assert [(h["module"], h["name"]) for h in evidence["handoffs"]] == [
        ("CP-0", "CP-0.md"),
        ("CP-1", "CP-1.md"),
    ]
    for handoff in evidence["handoffs"]:
        # Inside the library folder, so it also opens when the library is served.
        assert handoff["href"] == f"downloads/run-a/{handoff['module']}.md"
    assert evidence["zip"] == "downloads/run-a/handoffs.zip"
    record = evidence["record"]
    assert record["cap"] == "12"
    assert record["calls"] == [
        {
            "module": "CP-0",
            "attempt": None,
            "started": "2026-11-01T10:00:00Z",
            "http_status": None,
            "error_class": None,
            "settled_usd": "0.10",
        },
        {
            "module": "CP-1",
            "attempt": None,
            "started": "2026-11-02T10:00:00Z",
            "http_status": None,
            "error_class": None,
            "settled_usd": "0.20",
        },
    ]
    delivery = next(folder.glob("delivery-*.json"))
    completion = next(folder.glob("completed-*.json"))
    hashes = {h["name"]: h["sha256"] for h in record["hashes"]}
    assert hashes[delivery.name] == hashlib.sha256(delivery.read_bytes()).hexdigest()
    assert hashes[completion.name] == hashlib.sha256(completion.read_bytes()).hexdigest()
    assert hashes["A_report.pdf"] == hashlib.sha256(b"text of A_report.pdf\n").hexdigest()
    assert [i["module"] for i in record["instructions"]] == ["CP-0", "CP-1"]
    first = record["instructions"][0]
    assert first["href"] == "downloads/run-a/instructions/CP-0.md"
    assert first["sha256"] == hashes["instructions/CP-0.md"]


def test_evidence_without_a_workflow_record_is_empty_not_invented(tmp_path):
    make_run(tmp_path, "run-a")
    (tmp_path / "runs/run-a/workflow.json").write_text("{}")
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": []}
    result = store.workspace_store(tmp_path, {"real": [row], "issues": []})
    record = result["runs"]["run-a"]["evidence"]["record"]
    assert record["cap"] is None and record["instructions"] == []
    assert result["runs"]["run-a"]["evidence"]["sources"] == []


def test_a_malformed_call_line_is_named_in_the_issues(tmp_path):
    make_run(tmp_path, "run-a")
    calls = tmp_path / "runs/run-a/live/calls.jsonl"
    calls.write_text(calls.read_text() + "not json\n")
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": []}
    result = store.workspace_store(tmp_path, {"real": [row], "issues": []})
    assert result["issues"] == ["run-a: live/calls.jsonl line 3 is not a call record"]
    assert len(result["runs"]["run-a"]["evidence"]["record"]["calls"]) == 2


def test_an_undecodable_call_file_is_named_in_the_issues_and_lists_no_call(tmp_path):
    make_run(tmp_path, "run-a")
    calls = tmp_path / "runs/run-a/live/calls.jsonl"
    calls.write_bytes(calls.read_bytes() + b'{"module_id": "CP-0", "note": "\xff"}\n')
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": []}
    result = store.workspace_store(tmp_path, {"real": [row], "issues": []})
    assert result["issues"] == [
        "run-a: live/calls.jsonl is not UTF-8 text (line 3); no call is listed"
    ]
    assert result["runs"]["run-a"]["evidence"]["record"]["calls"] == []


@pytest.mark.parametrize(
    ("name", "kind"),
    [
        ("a.pdf", "pdf"),
        ("x.htm.jsonl", "htm.jsonl"),
        ("report v1.2.pdf", "pdf"),
        ("noext", None),
    ],
)
def test_file_type_is_the_extension_words_as_written(name, kind):
    assert store.file_type(name) == kind


def test_downloads_are_the_calculation_and_model_files_of_the_models_the_run_lists():
    def model(mid, run_folder, **extra):
        return {
            "id": mid,
            "issuerKey": "nbg",
            "runId": None,
            "runFolder": run_folder,
            "sources": [],
            "download": f"/files/{mid}.html?download=1",
            "files": [
                {"name": "calculation.json", "href": f"/files/{mid}/calc"},
                {"name": "forecast.md", "href": f"/files/{mid}/md"},
                {"name": "forecast_exact.json", "href": f"/files/{mid}/exact"},
            ],
        } | extra

    run = {"folder": "run-a", "issuerKey": "nbg"}
    models = [
        model("m-b", "run-a"),
        model("m-other", "run-z"),
        model("m-src", "run-z", sources=[{"run": "run-a"}]),
        model("m-issuer", "run-a", issuerKey="zzz"),
    ]
    assert store.run_downloads(run, "run-a", models) == [
        {"label": "Model m-b", "href": "/files/m-b.html?download=1"},
        {"label": "m-b: calculation.json", "href": "/files/m-b/calc"},
        {"label": "m-b: forecast_exact.json", "href": "/files/m-b/exact"},
        {"label": "Model m-src", "href": "/files/m-src.html?download=1"},
        {"label": "m-src: calculation.json", "href": "/files/m-src/calc"},
        {"label": "m-src: forecast_exact.json", "href": "/files/m-src/exact"},
    ]


def test_an_instruction_key_that_is_not_a_module_code_gets_no_link(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    path = run_dir / "workflow.json"
    workflow = json.loads(path.read_text())
    workflow["instructions"]["../../escaped"] = dict(workflow["instructions"]["CP-0"])
    path.write_text(json.dumps(workflow))
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": []}
    result = store.workspace_store(tmp_path, {"real": [row], "issues": []})
    rows = {r["module"]: r for r in result["runs"]["run-a"]["evidence"]["record"]["instructions"]}
    assert rows["../../escaped"]["href"] is None
    assert rows["CP-0"]["href"] == "downloads/run-a/instructions/CP-0.md"
    assert any("'../../escaped'" in i and "no link" in i for i in result["issues"])


# The Forecast grid with a history record: columns hand-written from the plan's answer key.
NO_PF = "no handoff states pro forma adjustments"
NEEDS_9M_2023 = "needs 9M 2023, which CP-1 does not print"


def held(amount, reason=None):
    return {"amount": amount, "reason": reason}


def history_column(identity, amounts, reason=None):
    column_id, kind, label, prior = identity
    revenue, ebitda = amounts

    def entry(amount):
        return held(amount, reason if amount is None else None)

    return {
        "id": column_id,
        "kind": kind,
        "label": label,
        "prior": prior,
        "reason": reason,
        "start": None,
        "end": None,
        "values": {"revenue": entry(revenue), "ebitda": entry(ebitda)},
    }


HISTORY = {
    "schema_version": "cpos-history/1",
    "columns": [
        history_column(("Q3_2024", "QUARTER", "Q3 2024", None), ("250", "75")),
        history_column(("Q3_2025", "QUARTER", "Q3 2025", "Q3_2024"), ("270", "84")),
        history_column(("YTD", "YTD", "YTD (9M 2025)", "PYTD"), ("780", "240")),
        history_column(("PYTD", "PYTD", "PYTD (9M 2024)", None), ("720", "216")),
        history_column(("FY2023", "FY", "FY2023", None), ("940", "276")),
        history_column(("FY2024", "FY", "FY2024", "FY2023"), ("1000", "300")),
        history_column(("LTM", "LTM", "LTM Q3 2025", "PRIOR_LTM"), ("1060", "324")),
        history_column(("PRIOR_LTM", "PRIOR_LTM", "Prior LTM", None), (None, None), NEEDS_9M_2023),
        history_column(("PF", "PF", "PF LTM", None), (None, None), NO_PF),
    ],
    "limits": ["History is CP-1's printed figures."],
}


def forecast_year(year, revenue, ebitda):
    return {"year": year, "revenue": held(revenue), "ebitda": held(ebitda)}


REFERENCE = {
    "outputs": {
        "REFERENCE": {
            "years": [
                forecast_year(2025, "1050", "315"),
                forecast_year(2026, "1092", "338.52"),
                forecast_year(2027, "1124.76", "359.9232"),
            ]
        }
    },
    "scope_limits": ["Every figure is Python's arithmetic."],
}
WITHOUT_HISTORY = json.dumps({"annual_periods": [], "values": {}}).encode()


def with_history(damage):
    record = {"annual_periods": [], "values": {}, "history": {**HISTORY, **damage}}
    return json.dumps(record).encode()


FILES = {
    "forecast_exact.json": json.dumps(REFERENCE).encode(),
    "calculation.json": with_history({}),
    "annual.md": b"No tables here.",
    "quarter.md": b"No tables here.",
}


REQUEST_IN_THOUSANDS = "## Request\n\nBase: September balances, USD thousands, consolidated.\n"


def with_units(units):
    record = {**REFERENCE, "scale": 1000, "units": units}
    return {**FILES, "forecast_exact.json": json.dumps(record).encode()}


def test_the_units_caption_is_the_records_statement_not_the_requests_phrase():
    assert store.read_cashflow(with_units("USD millions"), REQUEST_IN_THOUSANDS)[0]["units"] == (
        "USD millions"
    )
    assert store.read_cashflow(with_units("USD millions"), None)[0]["units"] == "USD millions"


def test_a_record_without_units_keeps_the_requests_phrase():
    assert store.read_cashflow(FILES, REQUEST_IN_THOUSANDS)[0]["units"] == "USD thousands"
    assert store.read_cashflow(FILES, None)[0]["units"] is None


@pytest.mark.parametrize(
    "units",
    [
        5,
        "",
        "x" * 41,
        ["USD millions"],
        "   ",
        "\t",
        "USD\nmillions",
        "USD\x00millions",
        "USD\u202emillions",
        "USD\u2066millions\u2069",
        "USD\u200bmillions",
        None,
    ],
)
def test_units_that_are_not_a_short_text_are_reported_not_shown(units):
    assert store.read_cashflow(with_units(units), None) == (None, ("file", "forecast_exact.json"))


def test_units_of_exactly_forty_printable_characters_are_shown():
    units = "USD millions " + "x" * 27
    assert len(units) == 40
    assert store.read_cashflow(with_units(units), None)[0]["units"] == units


def test_scale_and_units_are_recorded_together_or_not_at_all():
    scale_only = {**REFERENCE, "scale": 1000}
    units_only = {**REFERENCE, "units": "USD millions"}
    for record in (scale_only, units_only):
        files = {**FILES, "forecast_exact.json": json.dumps(record).encode()}
        assert store.read_cashflow(files, None) == (None, ("file", "forecast_exact.json"))


def test_history_columns_precede_the_forecast_in_the_owners_order():
    grid, problem = store.read_cashflow(FILES, None)
    assert problem is None
    assert [(c["group"], c["label"]) for c in grid["columns"]][:9] == [
        ("Quarter", "Q3 2024"),
        ("Quarter", "Q3 2025"),
        ("Year to date", "YTD (9M 2025)"),
        ("Year to date", "PYTD (9M 2024)"),
        ("Fiscal year", "FY2023"),
        ("Fiscal year", "FY2024"),
        ("Last twelve months", "LTM Q3 2025"),
        ("Last twelve months", "Prior LTM"),
        ("Pro forma", "PF LTM"),
    ]
    assert [c["label"] for c in grid["columns"]][9:12] == ["FY2025E", "FY2026E", "FY2027E"]


def test_values_growth_and_margin_read_across_the_new_columns():
    row = {r["label"]: r["cells"] for r in store.read_cashflow(FILES, None)[0]["rows"]}
    assert [c["exact"] for c in row["Revenue"][:7]] == [
        "250",
        "270",
        "780",
        "720",
        "940",
        "1000",
        "1060",
    ]
    growth = row["Revenue YoY growth"]
    assert Fraction(growth[1]["exact"]) == Fraction(8, 100)  # Q3 2025 on Q3 2024
    assert abs(Fraction(growth[2]["exact"]) - Fraction(1, 12)) < Fraction(1, 10**20)  # YTD on PYTD
    assert abs(Fraction(growth[5]["exact"]) - Fraction(3, 47)) < Fraction(1, 10**20)  # FY2024
    assert Fraction(growth[9]["exact"]) == Fraction(5, 100)  # FY2025E on FY2024
    assert growth[6]["status"] == "na"  # LTM: prior LTM missing
    margin = Fraction(row["Adj EBITDA margin"][6]["exact"])
    assert abs(margin - Fraction(324, 1060)) < Fraction(1, 10**20)


def test_an_unavailable_column_gives_every_row_its_reason():
    grid = store.read_cashflow(FILES, None)[0]
    assert all(row["cells"][8]["status"] == "na" for row in grid["rows"])
    reason = {r["label"]: r["cells"][8]["reason"] for r in grid["rows"]}
    assert reason["Revenue"] == reason["Distributions"] == "no handoff states pro forma adjustments"
    assert set(reason.values()) == {"no handoff states pro forma adjustments"}
    prior_reason = NEEDS_9M_2023
    assert all(row["cells"][7]["reason"] == prior_reason for row in grid["rows"])
    assert not any(note.startswith("Pro forma:") for note in grid["notes"])


def test_the_history_notes_and_limits_replace_the_quarter_and_pro_forma_notes():
    grid = store.read_cashflow(FILES, None)[0]
    assert store.Q1_NOTE not in grid["notes"]
    assert (
        "LTM is the last fiscal year when that is the latest period CP-1 labels; otherwise the "
        "last fiscal year plus the year to date less the prior year to date."
    ) in grid["notes"]
    assert grid["limits"] == ["Every figure is Python's arithmetic.", *HISTORY["limits"]]


def test_a_model_without_a_history_record_is_laid_out_as_before():
    files = {**FILES, "calculation.json": WITHOUT_HISTORY}
    grid = store.read_cashflow(files, None)[0]
    assert [c["label"] for c in grid["columns"]][:3] == ["FY2025E", "FY2026E", "FY2027E"]
    assert not any(c["ytd"] for c in grid["columns"])  # the fixture has no quarter column
    assert store.Q1_NOTE not in grid["notes"]
    assert "Pro forma: no pro forma period is recorded in the handoffs." in grid["notes"]


COMMON_LABELS = [
    "Revenue",
    "Revenue YoY growth",
    "COGS (cost of sales)",
    "Gross profit",
    "Gross profit margin",
    "Opex (selling and administrative, amortization of intangibles)",
    "EBIT (income from operations)",
    "D&A (depreciation and amortization)",
    "EBITDA (EBIT + D&A)",
    "Issuer EBITDA (reported)",
]
MIDDLE_LABELS = [
    "Adj EBITDA margin",
    "Adj EBITDA YoY growth",
]
AFTER_INTEREST = [
    "Cash taxes",
    "Cash taxes and working capital, combined",
    "Model cash from operations",
    "Capital expenditure (outflow)",
    "Cash proxy (not issuer free cash flow)",
    "Distributions",
    "Debt repayment",
    "Opening cash",
    "Closing cash",
    "Undrawn facility",
    "Accessible liquidity",
    "Opening debt",
]
CREDIT_LABELS = [
    "Net debt (all modelled cash deducted)",
    "Senior secured leverage (secured debt / Adj EBITDA)",
    "Total leverage (debt / Adj EBITDA)",
    "Net leverage (net debt / Adj EBITDA)",
]
BASE_NOTE = (
    "Base case is the model's reference case: a conditional illustration, not an "
    "evidence-supported central issuer forecast."
)
NM_NOTE = "n.m. \u2014 not modelled: the calculation record does not project this line."
DOWNSIDE_NOTE = "Downside case: no downside case was computed in this run."


def test_the_history_page_labels_and_notes_carry_no_other_issuers_wording():
    grid = store.read_cashflow(FILES, None)[0]
    assert [row["label"] for row in grid["rows"]] == [
        *COMMON_LABELS,
        "Adj EBITDA (as named in Financial foundation)",
        *MIDDLE_LABELS,
        "LTM Adj EBITDA",
        "Interest",
        *AFTER_INTEREST,
        "Closing debt",
        *CREDIT_LABELS,
        "Interest coverage (Adj EBITDA / interest)",
        "Cash proxy / closing debt",
    ]
    assert grid["notes"] == [
        (
            "LTM is the last fiscal year when that is the latest period CP-1 labels; otherwise "
            "the last fiscal year plus the year to date less the prior year to date."
        ),
        BASE_NOTE,
        (
            "Adj EBITDA is the earnings line the forecast inputs name in Financial foundation; "
            "in the forecast it is the model's earnings on that basis, not issuer guidance."
        ),
        (
            "Leverage is closing debt, as the forecast inputs name it in Financial foundation, "
            "over Adj EBITDA. Leverage is shown for twelve-month periods only."
        ),
        (
            "Historical interest is the Financial foundation line the forecast inputs name, "
            "which may be interest expense rather than cash paid; forecast interest is opening "
            "debt times the interest-rate driver."
        ),
        NM_NOTE,
        DOWNSIDE_NOTE,
    ]
    text = " ".join(grid["notes"])
    assert not any(word in text for word in ("As Defined", "securitization", "refinancing"))


def test_a_model_without_a_history_record_keeps_its_labels_and_notes_exactly():
    files = {**FILES, "calculation.json": WITHOUT_HISTORY}
    grid = store.read_cashflow(files, None)[0]
    assert [row["label"] for row in grid["rows"]] == [
        *COMMON_LABELS,
        "Adj EBITDA (EBITDA As Defined)",
        *MIDDLE_LABELS,
        "LTM Adj EBITDA (As Defined)",
        "Cash interest",
        *AFTER_INTEREST,
        "Closing debt (carrying value)",
        *CREDIT_LABELS,
        "Interest coverage (Adj EBITDA / cash interest)",
        "Cash proxy / closing debt",
    ]
    assert grid["notes"] == [
        "Pro forma: no pro forma period is recorded in the handoffs.",
        BASE_NOTE,
        NM_NOTE,
        (
            "EBITDA (EBIT + D&A) differs from the issuer's reported EBITDA, which also deducts "
            "refinancing costs and includes other income or expense."
        ),
        (
            "Adj EBITDA is the issuer's EBITDA As Defined, a non-GAAP measure; in the forecast "
            "it is the model's earnings on that basis, not issuer guidance."
        ),
        (
            "Leverage uses carrying debt including securitization; senior secured debt is the "
            "term loans, secured notes and securitization at carrying value. Ratios are shown "
            "for fiscal years only."
        ),
        DOWNSIDE_NOTE,
    ]


def damaged_column(**changes):
    column = history_column(("FY2024", "FY", "FY2024", None), ("1", "1"))
    return {"columns": [{**column, **changes}]}


@pytest.mark.parametrize(
    "damage",
    [
        {"columns": "x"},
        {
            "columns": [
                {
                    "id": "A",
                    "kind": "WEEK",
                    "label": "A",
                    "prior": None,
                    "reason": None,
                    "values": {},
                }
            ]
        },
        {
            "columns": [
                {"id": "A", "kind": "FY", "label": "A", "prior": "B", "reason": None, "values": {}}
            ]
        },
        {"schema_version": "cpos-history/2"},
        {"limits": "x"},
        {"columns": [HISTORY["columns"][0]] * 2},
        damaged_column(prior="A"),
        damaged_column(kind="WEEK"),
        damaged_column(prior="B"),
        damaged_column(prior="FY2024"),
        damaged_column(reason="   "),
        damaged_column(id="FY24", label="FY24"),
        damaged_column(id="FY20245", label="FY20245"),
        damaged_column(start="2025-13-40"),
        damaged_column(values={"revenue": {"amount": "NaN", "reason": None}}),
        damaged_column(values={"revenue": "1"}),
        damaged_column(label=7),
        damaged_column(reason=7),
    ],
)
def test_a_malformed_history_is_reported_not_shown(damage):
    grid, problem = store.read_cashflow({**FILES, "calculation.json": with_history(damage)}, None)
    assert grid is None and problem == ("file", "calculation.json")


def test_an_undamaged_history_column_is_shown():
    grid, problem = store.read_cashflow(
        {**FILES, "calculation.json": with_history(damaged_column())}, None
    )
    assert problem is None and grid is not None


@pytest.mark.parametrize("kind", ["PYTD", "PRIOR_LTM", "PF", "QUARTER", "YTD", "FY", "LTM"])
def test_a_prior_naming_no_column_is_a_malformed_history_for_every_kind(kind):
    name = "FY2024" if kind == "FY" else kind
    column = history_column((name, kind, name, "GHOST"), ("1", "1"))
    grid, problem = store.read_cashflow(history_files([column]), None)
    assert grid is None and problem == ("file", "calculation.json")


@pytest.mark.parametrize("kind", ["PYTD", "PRIOR_LTM", "PF"])
def test_a_column_of_an_unpaired_kind_has_no_prior(kind):
    other = history_column(("Q", "QUARTER", "Q", None), ("1", "1"))
    column = history_column((kind, kind, kind, "Q"), ("1", "1"))
    grid, problem = store.read_cashflow(history_files([other, column]), None)
    assert grid is None and problem == ("file", "calculation.json")


def test_a_quarter_may_not_name_itself_and_a_fiscal_year_names_the_year_before_or_the_placeholder():
    own = history_column(("Q", "QUARTER", "Q", "Q"), ("1", "1"))
    assert store.read_cashflow(history_files([own]), None)[1] == ("file", "calculation.json")
    for prior in ("FY2021", "FY2024"):  # two years before, itself
        year = history_column(("FY2024", "FY", "FY2024", prior), ("1", "1"))
        far = history_column(("FY2021", "FY", "FY2021", None), ("1", "1"))
        got = store.read_cashflow(history_files([far, year]), None)
        assert got[1] == ("file", "calculation.json"), prior
    placeholder = history_column(("Fiscal year", "FY", "Fiscal year", None), ("1", "1"))
    year = history_column(("FY2024", "FY", "FY2024", "Fiscal year"), ("1", "1"))
    assert store.read_cashflow(history_files([placeholder, year]), None)[1] is None


def test_more_than_sixty_history_columns_are_over_the_limit():
    damage = {
        "columns": [history_column((f"C{i}", "FY", "C", None), ("1", "1")) for i in range(61)]
    }
    grid, problem = store.read_cashflow({**FILES, "calculation.json": with_history(damage)}, None)
    assert grid is None and problem[0] == "limit"


def history_files(columns, limits=None, revenue="1050"):
    history = {**HISTORY, "columns": columns}
    if limits is not None:
        history["limits"] = limits
    record = {"annual_periods": [], "values": {}, "history": history}
    exact = {
        "outputs": {"REFERENCE": {"years": [forecast_year(2025, revenue, "315")]}},
        "scope_limits": [],
    }
    return {
        **FILES,
        "forecast_exact.json": json.dumps(exact).encode(),
        "calculation.json": json.dumps(record).encode(),
    }


def growth_of(grid, label="FY2025E", part="columns"):
    columns = grid[part]["columns"] if part == "other" else grid["columns"]
    rows = grid[part]["rows"] if part == "other" else grid["rows"]
    row = next(r for r in rows if r["label"] == "Revenue YoY growth")
    return row["cells"][[c["label"] for c in columns].index(label)]


def dated(column, start, end):
    return {**column, "start": start, "end": end}


def test_the_first_forecast_year_grows_on_the_history_year_of_its_own_number():
    columns = [
        history_column(("FY2024", "FY", "FY2024", None), ("940", "276")),
        history_column(("FY2025", "FY", "FY2025", "FY2024"), ("1000", "300")),
    ]
    cell = growth_of(store.read_cashflow(history_files(columns), None)[0])
    assert Fraction(cell["exact"]) == Fraction(5, 100)  # 1050 on 1000, not on 940


def test_the_first_forecast_year_falls_back_to_the_year_before_it():
    columns = [history_column(("FY2024", "FY", "FY2024", None), ("1000", "300"))]
    cell = growth_of(store.read_cashflow(history_files(columns), None)[0])
    assert Fraction(cell["exact"]) == Fraction(5, 100)


def test_every_case_in_the_other_grid_grows_on_the_same_base():
    columns = [
        history_column(("FY2024", "FY", "FY2024", None), ("940", "276")),
        history_column(("FY2025", "FY", "FY2025", "FY2024"), ("1000", "300")),
    ]
    files = {**cases("REFERENCE", "UPSIDE", "DOWNSIDE_DRIVERS"), "calculation.json": None}
    files["calculation.json"] = history_files(columns)["calculation.json"]
    grid = store.read_cashflow(files, None)[0]
    cell = growth_of(grid, "FY2025E", "other")
    assert Fraction(cell["exact"]) == Fraction(110, 100) - 1  # Upside 1100 on 1000


def test_growth_between_periods_of_unequal_length_is_not_shown():
    columns = [
        dated(
            history_column(("Q3_2024", "QUARTER", "Q3 2024", None), ("250", "75")),
            "2024-07-01",
            "2024-09-30",
        ),
        dated(
            history_column(("Q3_2025", "QUARTER", "Q3 2025", "Q3_2024"), ("270", "84")),
            "2025-06-01",
            "2025-09-30",
        ),
    ]
    grid = store.read_cashflow(history_files(columns), None)[0]
    cell = growth_of(grid, "Q3 2025")
    assert (cell["status"], cell["reason"]) == (
        "na",
        "the prior-year period has a different length",
    )


def test_growth_on_periods_within_seven_days_of_each_other_is_shown():
    columns = [
        dated(
            history_column(("Q3_2024", "QUARTER", "Q3 2024", None), ("250", "75")),
            "2024-07-01",
            "2024-09-30",
        ),
        dated(
            history_column(("Q3_2025", "QUARTER", "Q3 2025", "Q3_2024"), ("270", "84")),
            "2025-07-01",
            "2025-10-06",
        ),
    ]
    cell = growth_of(store.read_cashflow(history_files(columns), None)[0], "Q3 2025")
    assert Fraction(cell["exact"]) == Fraction(8, 100)


def test_the_first_forecast_year_does_not_grow_on_a_short_fiscal_year():
    columns = [
        dated(
            history_column(("FY2024", "FY", "FY2024", None), ("1000", "300")),
            "2024-04-01",
            "2024-12-31",
        )
    ]
    cell = growth_of(store.read_cashflow(history_files(columns), None)[0])
    assert (cell["status"], cell["reason"]) == (
        "na",
        "the prior fiscal year is not twelve months",
    )


def test_the_first_forecast_year_grows_on_an_ordinary_dated_year():
    column = dated(
        history_column(("FY2024", "FY", "FY2024", None), ("1000", "300")),
        "2024-01-01",
        "2024-12-30",  # 365 days inclusive
    )
    cell = growth_of(store.read_cashflow(history_files([column]), None)[0])
    assert Fraction(cell["exact"]) == Fraction(5, 100)  # 1050 on 1000


def test_the_first_forecast_year_grows_on_a_fifty_three_week_year_and_an_undated_year():
    wide = dated(
        history_column(("FY2024", "FY", "FY2024", None), ("1000", "300")),
        "2023-12-31",
        "2025-01-04",  # 371 days inclusive
    )
    assert Fraction(
        growth_of(store.read_cashflow(history_files([wide]), None)[0])["exact"]
    ) == Fraction(5, 100)
    too_long = dated(wide, "2023-12-30", "2025-01-04")  # 372 days inclusive
    cell = growth_of(store.read_cashflow(history_files([too_long]), None)[0])
    assert cell["status"] == "na"


PAIRS = [
    ("Q", "QUARTER", "FY", "FY2024"),
    ("F", "FY", "QUARTER", "Q4 2024"),
    ("Y", "YTD", "PRIOR_LTM", "PRIOR_LTM"),
    ("L", "LTM", "PYTD", "PYTD"),
    ("P", "PYTD", "YTD", "YTD"),
]


@pytest.mark.parametrize("kind, prior_kind, prior_id", [(p[1], p[2], p[3]) for p in PAIRS])
def test_a_prior_of_another_family_is_a_malformed_history(kind, prior_kind, prior_id):
    other = history_column((prior_id, prior_kind, prior_id, None), ("1", "1"))
    me = history_column(("ME", kind, "me", prior_id), ("1", "1"))
    grid, problem = store.read_cashflow(history_files([other, me]), None)
    assert grid is None and problem == ("file", "calculation.json")


@pytest.mark.parametrize(
    "identity",
    [
        ("FY2024", "QUARTER", "Q4 2024", None),
        ("FY2024", "LTM", "LTM", None),
        ("2024", "FY", "x", None),
    ],
)
def test_a_fiscal_year_id_and_the_fiscal_year_kind_go_together(identity):
    column = history_column(identity, ("1", "1"))
    grid, problem = store.read_cashflow(history_files([column]), None)
    assert grid is None and problem == ("file", "calculation.json")


def test_the_prior_pairs_the_producer_emits_are_accepted():
    pairs = [
        ("Q1", "QUARTER", None),
        ("Q2", "QUARTER", "Q1"),
        ("YTD", "YTD", "PYTD"),
        ("PYTD", "PYTD", None),
        ("FY2023", "FY", None),
        ("FY2024", "FY", "FY2023"),
        ("LTM", "LTM", "PRIOR_LTM"),
        ("PRIOR_LTM", "PRIOR_LTM", None),
    ]
    columns = [history_column((i, k, i, p), ("1", "1")) for i, k, p in pairs]
    assert store.read_cashflow(history_files(columns), None)[1] is None


def test_a_row_the_history_does_not_carry_says_so_and_a_column_reason_still_wins():
    grid = store.read_cashflow(FILES, None)[0]
    row = next(r for r in grid["rows"] if r["label"] == "Distributions")
    assert row["cells"][0]["reason"] == "the period history does not carry this line"
    assert all(r["cells"][8]["reason"] == NO_PF for r in grid["rows"])


def test_the_history_notes_say_leverage_is_for_twelve_month_periods():
    notes = store.read_cashflow(FILES, None)[0]["notes"]
    assert not any("Ratios are shown for fiscal years only." in note for note in notes)
    assert any(note.endswith("Leverage is shown for twelve-month periods only.") for note in notes)
    plain = store.read_cashflow({**FILES, "calculation.json": WITHOUT_HISTORY}, None)[0]["notes"]
    assert any("Ratios are shown for fiscal years only." in note for note in plain)


def test_an_empty_column_reason_is_a_malformed_history_and_null_is_no_reason():
    column = history_column(("PF", "PF", "PF LTM", None), ("1", "1"), reason="")
    grid, problem = store.read_cashflow(history_files([column]), None)
    assert grid is None and problem == ("file", "calculation.json")


@pytest.mark.parametrize("limits", [["x"] * 201, ["x" * 2001]])
def test_history_limits_are_bounded_in_count_and_length(limits):
    column = history_column(("FY2024", "FY", "FY2024", None), ("1", "1"))
    grid, problem = store.read_cashflow(history_files([column], limits), None)
    assert grid is None and problem == ("file", "calculation.json")


def test_history_limits_at_the_bounds_are_kept():
    column = history_column(("FY2024", "FY", "FY2024", None), ("1", "1"))
    limits = ["x" * 2000] * 200
    grid = store.read_cashflow(history_files([column], limits), None)[0]
    assert grid["limits"] == limits


# Base case and one Downside case in the main grid; the other cases in a second grid.
FIRST_YEAR_REVENUE = {
    "REFERENCE": "1050",
    "UPSIDE": "1100",
    "DOWNSIDE_DRIVERS": "1000",
    "DOWNSIDE": "1040",
}


def cases(*keys, years=3):
    outputs = {
        key: {
            "years": [forecast_year(2025 + n, FIRST_YEAR_REVENUE[key], "300") for n in range(years)]
        }
        for key in keys
    }
    exact = {"outputs": outputs, "scope_limits": ["Every figure is Python's arithmetic."]}
    return {**FILES, "forecast_exact.json": json.dumps(exact).encode()}


def test_the_shock_is_the_downside_when_both_downsides_exist():
    grid = store.read_cashflow(cases("REFERENCE", "UPSIDE", "DOWNSIDE_DRIVERS", "DOWNSIDE"), None)[
        0
    ]
    assert [c["group"] for c in grid["columns"]][-6::3] == ["Base case", "Downside case"]
    revenue = next(r for r in grid["rows"] if r["label"] == "Revenue")["cells"]
    assert [revenue[-6]["exact"], revenue[-3]["exact"]] == ["1050", "1040"]
    assert [c["group"] for c in grid["other"]["columns"]][::3] == [
        "Upside",
        "Downside (CP-2G drivers)",
    ]
    other = next(r for r in grid["other"]["rows"] if r["label"] == "Revenue")["cells"]
    assert [other[0]["exact"], other[3]["exact"]] == ["1100", "1000"]
    assert (
        "Downside case is the stress case: a shock applied to the base-case drivers."
        in grid["notes"]
    )


def test_cp2gs_downside_is_the_downside_without_a_shock():
    grid = store.read_cashflow(cases("REFERENCE", "DOWNSIDE_DRIVERS"), None)[0]
    revenue = next(r for r in grid["rows"] if r["label"] == "Revenue")["cells"]
    assert revenue[-3]["exact"] == "1000"
    assert grid["other"] is None
    assert (
        "Downside case is CP-2G's own downside drivers; no CP-2A shock was supplied."
        in grid["notes"]
    )


def test_no_downside_is_an_unavailable_column_not_a_missing_one():
    grid = store.read_cashflow(cases("REFERENCE"), None)[0]
    assert (grid["columns"][-1]["group"], grid["columns"][-1]["label"]) == (
        "Downside case",
        "Downside",
    )
    reason = "no downside case was computed in this run"
    assert all(r["cells"][-1]["reason"] == reason for r in grid["rows"])
    assert "Downside case: no downside case was computed in this run." in grid["notes"]


def test_the_other_grid_holds_only_forecast_columns_and_prior_year_growth_from_the_history():
    grid = store.read_cashflow(cases("REFERENCE", "UPSIDE", "DOWNSIDE_DRIVERS"), None)[0]
    other = grid["other"]
    assert {c["group"] for c in other["columns"]} == {"Upside"}
    assert [c["label"] for c in other["columns"]] == ["FY2025E", "FY2026E", "FY2027E"]
    assert all(len(r["cells"]) == 3 for r in other["rows"])
    growth = next(r for r in other["rows"] if r["label"] == "Revenue YoY growth")["cells"]
    assert Fraction(growth[0]["exact"]) == Fraction(1100, 1000) - 1  # on FY2024, 1000 in history
    assert Fraction(growth[1]["exact"]) == 0


def test_cases_beyond_the_cell_budget_end_in_the_limit_problem():
    files = cases("REFERENCE", "UPSIDE", "DOWNSIDE_DRIVERS", "DOWNSIDE", years=20)
    grid, problem = store.read_cashflow(files, None, budget=1000)
    assert grid is None and problem[0] == "limit"


def test_the_cells_charged_to_the_page_budget_are_both_grids_cells():
    files = cases("REFERENCE", "UPSIDE", "DOWNSIDE", years=3)
    grid = store.read_cashflow(files, None)[0]
    assert grid["other"] is not None
    main = len(grid["rows"]) * len(grid["columns"])
    other = len(grid["other"]["rows"]) * len(grid["other"]["columns"])
    assert other > 0
    assert store.grid_cells(grid) == main + other


def test_a_budget_one_short_of_two_models_with_other_grids_refuses_the_second():
    files = cases("REFERENCE", "UPSIDE", "DOWNSIDE", years=3)
    first = store.read_cashflow(files, None)[0]
    cells = len(first["rows"]) * (len(first["columns"]) + len(first["other"]["columns"]))
    budget = 2 * cells - 1
    built, _ = store.read_cashflow(files, None, budget)
    assert built is not None
    second, problem = store.read_cashflow(files, None, budget - store.grid_cells(built))
    assert second is None and problem[0] == "limit"
    exact, _ = store.read_cashflow(files, None, budget + 1 - store.grid_cells(built))
    assert exact is not None


def downside_of(outputs):
    exact = {"outputs": outputs, "scope_limits": []}
    files = {
        **FILES,
        "forecast_exact.json": json.dumps(exact).encode(),
        "calculation.json": WITHOUT_HISTORY,
    }
    return store.read_cashflow(files, None)[0]


def three_years(revenue):
    return {"years": [forecast_year(2025 + n, revenue, "300") for n in range(3)]}


def test_an_empty_shock_leaves_the_cp2g_downside_as_the_downside_case():
    grid = downside_of(
        {
            "REFERENCE": three_years("1000"),
            "DOWNSIDE_DRIVERS": three_years("900"),
            "DOWNSIDE": {"years": []},
        }
    )
    assert [c["label"] for c in grid["columns"] if c["group"] == "Downside case"] == [
        "FY2025E",
        "FY2026E",
        "FY2027E",
    ]
    assert grid["other"] is None
    assert grid["notes"][-1] == store.DOWNSIDE_NOTES["DOWNSIDE_DRIVERS"]


def test_every_downside_empty_gives_the_placeholder_and_its_note():
    grid = downside_of(
        {
            "REFERENCE": three_years("1000"),
            "DOWNSIDE_DRIVERS": {"years": []},
            "DOWNSIDE": {"years": []},
        }
    )
    assert (grid["columns"][-1]["group"], grid["columns"][-1]["label"]) == (
        "Downside case",
        "Downside",
    )
    assert all(r["cells"][-1]["reason"] == store.NO_DOWNSIDE for r in grid["rows"])
    assert grid["other"] is None
    assert grid["notes"][-1] == store.DOWNSIDE_NOTES[None]


def test_an_empty_case_opens_no_group_in_the_other_grid():
    grid = downside_of({"REFERENCE": three_years("1000"), "UPSIDE": {"years": []}})
    assert grid["other"] is None


def test_the_page_budget_charges_both_grids_of_every_model(monkeypatch):
    files = cases("REFERENCE", "UPSIDE", "DOWNSIDE_DRIVERS", "DOWNSIDE", years=3)
    asked: list[int | None] = []

    def read_model(reads, artifact, manifest, issues, budget=None):
        asked.append(budget)
        ask = store.GridAsk(None, budget)
        grid = store.cashflow_or_issues(artifact["folder"], {}, dict(files), ask, issues)
        return {"id": artifact["folder"], "cashflow": grid}

    monkeypatch.setattr(
        store, "shown_models", lambda root, catalogue, manifests=None: ({"m1", "m2"}, [])
    )
    monkeypatch.setattr(store, "run_shows", lambda *args: True)
    monkeypatch.setattr(store, "read_model", read_model)
    artifacts = [
        {"folder": f, "available": True, "kind": "model", "href": "x"} for f in ("m1", "m2")
    ]
    catalogue = {"real": [{"artifacts": artifacts}]}
    prior = ({}, {}, {}, {"m1": "", "m2": ""})
    one = store.read_cashflow(files, None)[0]
    assert one["other"] is not None
    built = len(one["rows"]) * (len(one["columns"]) + len(one["other"]["columns"]))
    models, _ = store.catalogue_models(Path("."), catalogue, prior)
    assert len(models) == 2 and asked[0] - asked[1] == built
    for budget, second_shown in ((2 * built - 1, False), (2 * built, True)):
        asked.clear()
        monkeypatch.setattr(store, "CASHFLOW_CELL_BUDGET", budget)
        models, _ = store.catalogue_models(Path("."), catalogue, prior)
        assert [m["cashflow"] is not None for m in models] == [True, second_shown]
