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
