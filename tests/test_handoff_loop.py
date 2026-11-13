"""Offline adversarial tests of the adapted cp-os loop; not live module proof."""

import json
import time
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from deploy_vii.contracts import Run
from deploy_workflow.model.adapter import AdapterReply
from deploy_workflow.model.handoff import REDACTION_FAILED, HandoffExecutor, ModuleTools
from deploy_workflow.model.providers import WEB_SEARCH_BLOCK
from deploy_workflow.model.turn import Compaction, ProviderBlock, ToolCall, Turn, Usage, hosted_kind
from deploy_workflow.owners.cpos import HandoffTask
from deploy_workflow.run_events import read_events


def task() -> HandoffTask:
    return HandoffTask(
        Run(
            run_id="loop-test",
            issuer_id="TDG",
            issuer_name="TransDigm Group Incorporated",
            as_of=date(2024, 9, 30),
            case_kind="public",
            pathway="credit_snapshot",
            requested_modules=("CP-1", "CP-MODEL", "CP-1A", "CP-2"),
        ),
        "CP-2",
        b"Compare evidence and preserve gaps.",
        {"S1.txt": b"Revenue 100\nMissing cash"},
        {"CP-1": b"Revenue 100; cash unavailable"},
        1,
        (),
    )


GOOD = b"## Request\nTDG\n## Sources\nS1\n## Findings\n100\n## Calculations\nNone\n## Gaps\ncash unavailable\n## Next module\ndelivery\n"


def check(_task: HandoffTask, raw: bytes) -> tuple[str, ...]:
    return () if raw == GOOD else ("Expected source amount 100 and missing cash.",)


def turn(*calls: ToolCall, usage: Usage | None = None) -> AdapterReply:
    result = Turn(
        "",
        calls,
        usage or Usage(input_tokens=100, output_tokens=50),
        "tool_use" if calls else "end",
        "gpt-6.1-sol",
        "test",
        200,
    )
    return AdapterReply("ok", result, None, 200, None, None, 1, 2, result.usage)


class Adapter:
    config_id = "sol-medium"
    ruling = None

    def __init__(self, *replies: AdapterReply | Exception) -> None:
        self.replies = list(replies)
        self.requests = []

    def complete(self, request, **_identity):
        self.requests.append(request)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def test_read_reject_edit_retains_exchange_and_current_handoff(tmp_path: Path) -> None:
    adapter = Adapter(
        turn(ToolCall("r", "read_pages", {"source_id": "S1.txt", "first": 1, "last": 1})),
        turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode().replace("100", "101")})),
        turn(ToolCall("e", "edit_handoff", {"edits": [{"old": "101", "new": "100"}]})),
    )
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    assert loop(task()) == GOOD
    assert "Revenue 100; cash unavailable" in adapter.requests[0].messages[1].text
    import json

    roles = json.loads(adapter.requests[0].messages[1].text)["module_roles"]
    assert "legal and covenant" in roles["CP-4"]
    assert "investment-committee" in roles["CP-6"]
    assert "prior and current deliverables" in roles["CP-8"]
    assert "CP-MEMO" not in roles
    assert "REJECTED" in adapter.requests[2].messages[-1].text
    assert len(list(tmp_path.rglob("*.request.json"))) == 3
    assert len(list(tmp_path.rglob("*.response.json"))) == 3
    assert len(list(tmp_path.rglob("*.tools.json"))) == 3
    assert loop.budget.spent > 0
    assert not loop.budget.unsettled
    with pytest.raises(ValueError, match="already_started"):
        loop(task())
    assert len(adapter.requests) == 3


def test_whole_filing_reads_stop_before_the_request_outgrows_the_budget_bound(
    tmp_path: Path,
) -> None:
    """runs/cpos-launch-live-001: parallel reads of whole filings stopped CP-0 with "1124866
    input-token bound is over the 1050000 supported", after paying for reads it never used."""
    filing = (
        "x" * 11_999 + "\n"
    ) * 200  # 200 pages of 12,000 characters, as a large text file reads.
    reads = [
        ToolCall(str(n), "read_pages", {"source_id": "S1.txt", "first": n + 1, "last": n + 8})
        for n in range(0, 192, 8)
    ]
    adapter = Adapter(
        turn(*reads[:8]),
        turn(*reads[8:16]),
        turn(*reads[16:24]),
        turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})),
    )
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    current = replace(task(), sources={"S1.txt": filing.encode()})
    assert loop(current) == GOOD
    # The bound counts two request bytes per token against the 1,050,000-token context.
    assert max(p.stat().st_size for p in tmp_path.rglob("*.request.json")) < 2 * 1_050_000
    tools = [m.text for m in adapter.requests[-1].messages if m.role == "tool"]
    assert tools[0].startswith("<<<SOURCE id=S1.txt")
    assert "gap" in tools[-1] and tools[-1].startswith("ERROR")


def test_reads_continue_until_the_request_reaches_1_1_mb(tmp_path: Path) -> None:
    """Live run tdg-all-001 (2026-11-10): CP-3 and CP-5 began at 0.99 and 1.01 MB, past the
    700,000-byte cap, so every source read they asked for was refused. 1.1 MB is 268,000 tokens
    at the lowest 4.11 request bytes per token measured, under the 272,000-token long-context
    price."""
    filing = ("x" * 11_999 + "\n") * 40
    adapter = Adapter(
        turn(ToolCall("1", "read_pages", {"source_id": "S1.txt", "first": 1, "last": 8})),
        turn(ToolCall("2", "read_pages", {"source_id": "S1.txt", "first": 9, "last": 16})),
        turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})),
    )
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    handoffs = {"CP-1": b"Revenue 100; cash unavailable. " + b"x" * 950_000}
    assert loop(replace(task(), sources={"S1.txt": filing.encode()}, handoffs=handoffs)) == GOOD
    tools = [m.text for m in adapter.requests[-1].messages if m.role == "tool"]
    assert tools[0].startswith("<<<SOURCE id=S1.txt")  # About 1.05 MB with this read.
    assert tools[1].startswith("ERROR: this module has read as much as its context allows")


def test_a_request_past_one_byte_per_token_is_sent_when_it_fits_the_context(
    tmp_path: Path,
) -> None:
    """Live run tdg-all-001 (2026-11-10): CP-5 stopped with "1105073 input-token bound is over the
    1050000 supported", though its largest request sent had 231,568 input tokens. 817 retained
    live calls measured at least 4.11 request bytes per input token."""
    handoffs = {"CP-1": b"Revenue 100; cash unavailable. " + b"x" * 1_200_000}
    adapter = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    assert loop(replace(task(), handoffs=handoffs)) == GOOD
    assert len(adapter.requests) == 1
    assert max(p.stat().st_size for p in tmp_path.rglob("*.request.json")) > 1_050_000


def test_a_request_past_the_context_at_two_bytes_per_token_is_refused_unsent(
    tmp_path: Path,
) -> None:
    handoffs = {"CP-1": b"x" * 2_200_000}
    adapter = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    with pytest.raises(Exception, match="input-token bound is over the 1050000 supported"):
        loop(replace(task(), handoffs=handoffs))
    assert adapter.requests == []
    assert loop.budget.spent == 0


def test_atomic_patch_allowlist_and_page_bounds(tmp_path: Path) -> None:
    module = ModuleTools(task(), tmp_path, check)
    assert module.call("__init__", {}).startswith("ERROR")
    assert module.call("read_pages", {"source_id": "S1.txt", "first": 2, "last": 2}).startswith(
        "ERROR"
    )
    assert module.call("read_pages", {"source_id": "S1.txt", "first": True, "last": 1}).startswith(
        "ERROR"
    )
    module.call("write_handoff", {"markdown": GOOD.decode().replace("100", "101")})
    draft = module.draft
    assert module.call(
        "edit_handoff", {"edits": [{"old": "101", "new": "100"}, {"old": "absent", "new": "x"}]}
    ).startswith("ERROR")
    assert module.draft == draft
    assert not module.accepted


def test_excel_input_preserves_formula_zero_and_cell_locators(tmp_path: Path) -> None:
    import io
    from dataclasses import replace

    from openpyxl import Workbook

    book = Workbook()
    sheet = book.active
    sheet.title = "Annual"
    sheet.append([0, None, "=A1+1", "USD millions"])
    buffer = io.BytesIO()
    book.save(buffer)
    module = ModuleTools(
        replace(task(), sources={"issuer.xlsx": buffer.getvalue()}), tmp_path, check
    )
    read = module.read_pages("issuer.xlsx", 1, 1)
    assert "Sheet Annual" in read and "A1=0" in read and "C1='=A1+1'" in read
    assert "D1='USD millions'" in read and "B1=" not in read
    assert not list(tmp_path.iterdir())  # Input parsing produces no workbook deliverable.


def _workbook(sheet_xml: str, dimension: str = "") -> bytes:
    """A minimal OOXML workbook written by hand, independent of the reader under test."""
    import io
    import zipfile

    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rels = "http://schemas.openxmlformats.org/package/2006/relationships"
    office = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    parts = {
        "[Content_Types].xml": '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
        'content-types"><Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/'
        'sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.'
        'worksheet+xml"/></Types>',
        "_rels/.rels": f'<Relationships xmlns="{rels}"><Relationship Id="r1" '
        f'Type="{office}/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": f'<workbook xmlns="{main}" xmlns:r="{office}"><sheets>'
        '<sheet name="Annual FY" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": f'<Relationships xmlns="{rels}"><Relationship Id="rId1" '
        f'Type="{office}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": f'<worksheet xmlns="{main}">{dimension}'
        f"<sheetData>{sheet_xml}</sheetData></worksheet>",
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in parts.items():
            archive.writestr(name, text)
    return buffer.getvalue()


def _read(tmp_path: Path, source_id: str, raw: bytes) -> str:
    module = ModuleTools(replace(task(), sources={source_id: raw}), tmp_path, check)
    return module.read_pages(source_id, 1, 1)


# Codex review of ac22d9d. Expected by hand: the stored lexeme 9007199254740993.25 is shown
# exactly (a float would give 9007199254740994.0); a formula with no stored value shows its
# cache as [absent], never 0; a non-General number format is shown with the cell.
def test_excel_amount_is_its_exact_stored_lexeme(tmp_path: Path) -> None:
    raw = _workbook(
        '<row r="1"><c r="A1"><v>9007199254740993.25</v></c><c r="B1"><f>A1*2</f></c></row>'
    )
    read = _read(tmp_path, "issuer.xlsx", raw)
    assert "Sheet Annual FY" in read
    assert "A1=9007199254740993.25 | B1='=A1*2' cache=[absent]" in read
    assert "9007199254740994" not in read


# Expected by hand: two stored cells at opposite corners of a sheet whose dimension claims all
# 17,179,869,184 cells are read as exactly those two cells, well within the test's time.
def test_excel_sparse_workbook_reads_only_stored_cells(tmp_path: Path) -> None:
    raw = _workbook(
        '<row r="1"><c r="A1"><v>1</v></c></row>'
        '<row r="1048576"><c r="XFD1048576"><v>2</v></c></row>',
        dimension='<dimension ref="A1:XFD1048576"/>',
    )
    started = time.monotonic()
    read = _read(tmp_path, "issuer.xlsx", raw)
    assert time.monotonic() - started < 5
    assert "date serials are retained without conversion.\nA1=1\nXFD1048576=2\n" in read


# Expected by hand: workbook bytes are a workbook under any source id, and bytes that only begin
# like a ZIP, or a ZIP that is not a workbook, are not.
def test_excel_is_detected_by_content_not_source_id(tmp_path: Path) -> None:
    import io
    import zipfile

    raw = _workbook('<row r="1"><c r="A1" t="inlineStr"><is><t>USD m</t></is></c></row>')
    assert "A1='USD m'" in _read(tmp_path, "S1", raw)
    assert "page=1>>>\nPK\x03\x04 is not a workbook\n<<<END>>>" in _read(
        tmp_path, "notes.xlsx", b"PK\x03\x04 is not a workbook"
    )
    other = io.BytesIO()
    with zipfile.ZipFile(other, "w") as archive:
        archive.writestr("word/document.xml", "<w/>")
    with pytest.raises(UnicodeDecodeError):
        _read(tmp_path, "S2", other.getvalue())


def test_heading_feedback_identifies_exact_repair(tmp_path: Path) -> None:
    module = ModuleTools(task(), tmp_path, check)
    response = module.call(
        "write_handoff", {"markdown": GOOD.decode().replace("## Findings", "## Extra\n## Findings")}
    )
    assert "## Request; ## Sources; ## Findings" in response
    assert "All subsections must use ### or deeper" in response
    assert "Extra" in response


def test_acceptance_is_terminal_within_same_turn(tmp_path: Path) -> None:
    adapter = Adapter(
        turn(
            ToolCall("a", "write_handoff", {"markdown": GOOD.decode()}),
            ToolCall("b", "write_handoff", {"markdown": "corrupt"}),
        )
    )
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    assert loop(task()) == GOOD
    assert len(list(tmp_path.rglob("*.draft.md"))) == 1


def test_explicit_retained_draft_repair_uses_existing_edit_tool(tmp_path: Path) -> None:
    from dataclasses import replace

    original = GOOD.replace(b"100", b"101")
    adapter = Adapter(
        turn(ToolCall("repair", "edit_handoff", {"edits": [{"old": "101", "new": "100"}]}))
    )
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    assert loop(replace(task(), draft=original, attempt=2)) == GOOD
    assert original == GOOD.replace(b"100", b"101")
    assert len(adapter.requests) == 1
    assert '"repair_draft"' in adapter.requests[0].messages[1].text


@pytest.mark.parametrize("reply", [RuntimeError("possibly sent"), turn(usage=Usage())])
def test_unknown_charge_stops_and_holds_budget(tmp_path: Path, reply) -> None:
    adapter = Adapter(reply)
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    with pytest.raises(RuntimeError):
        loop(task())
    assert len(adapter.requests) == 1
    assert loop.budget.stop_reason is not None
    assert loop.budget.spent > 0  # Budget conservatively charges the entire unknown hold.


def test_cap_refuses_before_send(tmp_path: Path) -> None:
    adapter = Adapter()
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal("0.00001"), check=check)
    with pytest.raises(Exception, match="cap"):
        loop(task())
    assert not adapter.requests


def test_existing_calculation_kernel_preserves_missing_zero_and_exact_decimals(
    tmp_path: Path,
) -> None:
    import json

    module = ModuleTools(task(), tmp_path, check)
    assert json.loads(module.calculate("sum", ["0.1", "0.2"]))["value"] == "0.3"
    assert json.loads(module.calculate("sum", ["0", None]))["value"] is None
    assert json.loads(module.calculate("sum", ["0", "0"]))["value"] == "0"
    assert json.loads(module.calculate("ratio", ["1", "0"]))["value"] is None
    declined = json.loads(module.calculate("ratio", ["-6", "-36"]))
    assert declined["value"] is None
    assert declined["reason"] == "ZERO_OR_NEGATIVE_DENOMINATOR"
    assert json.loads(module.calculate("ratio", ["6", "36"]))["value"] == (
        "0.16666666666666666666666666666666666667"
    )
    assert module.calculate("sum", ["NaN"]).startswith("ERROR")
    assert module.calculate("sum", ["1e9999"]).startswith("ERROR")


def _calc(module: ModuleTools, operation: str, values: list[str | None]) -> dict[str, Any]:
    return json.loads(module.calculate(operation, values))


def test_calculate_difference_is_exact_and_refuses_missing(tmp_path: Path) -> None:
    module = ModuleTools(task(), tmp_path, check)
    for values, expected in (
        (["25068", "6261"], "18807"),
        (["24880", "6261"], "18619"),
        (["0.3", "0.1"], "0.2"),
        (["1", "3"], "-2"),
    ):
        assert _calc(module, "difference", values)["value"] == expected
    missing = _calc(module, "sum", ["5", None])
    for values in (["5", None], [None, "5"]):
        got = _calc(module, "difference", values)
        assert got["value"] is None
        assert got["reason"] == missing["reason"]
    assert module.calculate("difference", ["1"]).startswith("ERROR")
    assert module.calculate("difference", ["1", "2", "3"]).startswith("ERROR")


def test_calculate_difference_refuses_an_inexact_result_as_product_does(tmp_path: Path) -> None:
    module = ModuleTools(task(), tmp_path, check)
    big = "12345678901234567890123456789012345678"  # 38 digits; minus 0.1 needs 39
    refused = module.calculate("difference", [big, "0.1"])
    assert refused.startswith("ERROR"), refused
    assert (
        _calc(module, "difference", ["12345678901234567890123456789012345678", "1"])["value"]
        == "12345678901234567890123456789012345677"
    )


def test_calculate_product_is_exact_and_never_rounds(tmp_path: Path) -> None:
    module = ModuleTools(task(), tmp_path, check)
    for values, expected in (
        (["4173", "0.5256"], "2193.3288"),
        (["1.1", "1.1"], "1.21"),
        (["-2", "3"], "-6"),
        (["2", "3", "4"], "24"),
        (["0", "7"], "0"),
    ):
        assert _calc(module, "product", values)["value"] == expected
    assert _calc(module, "product", ["0", None])["value"] is None
    assert _calc(module, "product", ["0", None])["reason"] is not None
    big = "12345678901234567890123"
    refused = module.calculate("product", [big, big])
    assert refused.startswith("ERROR") or json.loads(refused)["value"] is None
    assert module.calculate("product", ["5"]).startswith("ERROR")


@settings(max_examples=100, deadline=None)
@given(
    a=st.integers(min_value=-(10**20), max_value=10**20),
    b=st.integers(min_value=-(10**20), max_value=10**20),
)
def test_calculate_difference_and_product_properties(a: int, b: int) -> None:
    module = ModuleTools(task(), Path("."), check)
    sa, sb = str(a), str(b)
    assert (
        _calc(module, "difference", [sa, sb])["value"]
        == _calc(module, "sum", [sa, str(-b)])["value"]
    )
    forward = module.calculate("product", [sa, sb])
    assert forward == module.calculate("product", [sb, sa])
    if len(str(abs(a * b))) <= 38:
        assert json.loads(forward)["value"] == str(a * b)


def test_preconstructed_executor_reloads_prior_spend(tmp_path: Path) -> None:
    from dataclasses import replace

    one = HandoffExecutor(
        tmp_path,
        adapter=Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()}))),
        cap_usd=Decimal(10),
        check=check,
    )
    two = HandoffExecutor(
        tmp_path,
        adapter=Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()}))),
        cap_usd=Decimal(10),
        check=check,
    )
    one(task())
    prior = one.budget.spent
    two(replace(task(), instructions=b"Changed module instructions"))
    assert two.budget.spent == prior * 2


def test_governance_tool_retains_evidence_rows_and_unscorable_dimensions(tmp_path: Path) -> None:
    import json

    module = ModuleTools(task(), tmp_path, check)
    row = {
        "kind": "behaviour_flag",
        "topic": "Documented distribution",
        "documented_fact": "Source fact",
        "direction": "Extraction-Oriented",
        "behaviour_type": "distribution",
        "amount_funding_source": "Historical distribution; amount not supplied in this fixture",
        "legal_capacity_link": "Capacity not assessed",
        "dimension": "Shareholder extraction risk",
        "risk_mechanic": "Cash leaves issuer",
        "credit_implication": "Reduced buffer",
        "evidence_quality": "High",
        "category": "Documentary Fact",
        "citations": [{"source_id": "S1.txt", "locator": "page 1", "quote": "Source fact"}],
        "limitation": "Historical",
    }
    result = json.loads(module.score_governance([row]))
    assert result["composite"] == "Not Scorable"
    assert result["risk_level"] == "High"
    extraction = next(
        d for d in result["dimensions"] if d["dimension"] == "Shareholder extraction risk"
    )
    assert extraction["score"] == "5"
    assert extraction["deciding"][0]["citations"][0]["quote"] == "Source fact"
    invalid_topic = {**row, "kind": "governance_topic"}
    refused = module.score_governance([invalid_topic])
    assert refused.startswith("ERROR")
    assert "governance topic leaves" in refused
    assert "Extraction-Oriented is a behaviour category" in refused


def test_text_only_and_rejected_draft_limits(tmp_path: Path) -> None:
    for label, replies in [
        ("text", [turn()] * 3),
        ("draft", [turn(ToolCall("w", "write_handoff", {"markdown": "bad"}))] * 3),
    ]:
        adapter = Adapter(*replies)
        loop = HandoffExecutor(tmp_path / label, adapter=adapter, cap_usd=Decimal(10), check=check)
        with pytest.raises(RuntimeError, match="not accepted"):
            loop(task())
        assert len(adapter.requests) == 3


def test_search_source_snippet_keeps_its_place_after_a_length_changing_lowercase(
    tmp_path: Path,
) -> None:
    # U+0130 lowercases to two code points, so a match position found in the lowercased page is
    # not a position in the page; Turkish filings carry that letter. By hand: the match starts at
    # index 201 (200 letters and a space before it), so 80 characters before it are 79 letters and
    # the space, and the 14 after it and the rest of the page fit inside the 80 after.
    page = "İ" * 200 + " total revenue 1,234 million"
    source_task = replace(task(), sources={"S.txt": page.encode()})
    tools = ModuleTools(source_task, tmp_path, check)
    hit = tools.search_source("S.txt", "Total Revenue")
    assert hit == "page 1: …" + "İ" * 79 + " total revenue 1,234 million…"


def test_events_record_each_turn_and_rejection(tmp_path: Path) -> None:
    from deploy_workflow.run_events import EVENTS, read_events

    adapter = Adapter(
        turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode().replace("100", "101")})),
        turn(ToolCall("e", "edit_handoff", {"edits": [{"old": "101", "new": "100"}]})),
    )
    loop = HandoffExecutor(
        tmp_path / "live",
        adapter=adapter,
        cap_usd=Decimal(10),
        check=check,
        max_turns=7,
        events=tmp_path / "run",
    )
    assert loop(task()) == GOOD
    events = read_events(tmp_path / "run" / EVENTS)
    assert [e["event"] for e in events] == ["turn", "draft_rejected", "turn"]
    turns = [e for e in events if e["event"] == "turn"]
    assert [e["turn"] for e in turns] == [1, 2]
    assert {e["max_turns"] for e in turns} == {7}
    assert {e["module"] for e in events} == {"CP-2"}
    assert [e["writes_left"] for e in events if e["event"] == "draft_rejected"] == [2]
    assert all(e["cap_usd"] == "10" and Decimal(e["held_usd"]) > 0 for e in turns)
    assert Decimal(turns[0]["spent_usd"]) == 0 and Decimal(turns[1]["spent_usd"]) > 0


def test_a_refused_reservation_writes_no_turn_event(tmp_path: Path) -> None:
    from deploy_workflow.model.budget import BudgetExhausted
    from deploy_workflow.run_events import EVENTS

    loop = HandoffExecutor(
        tmp_path / "live",
        adapter=Adapter(),
        cap_usd=Decimal("0.000001"),
        check=check,
        events=tmp_path / "run",
    )
    with pytest.raises(BudgetExhausted):
        loop(task())
    assert not (tmp_path / "run" / EVENTS).exists()


def test_no_events_folder_writes_no_events(tmp_path: Path) -> None:
    adapter = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    assert loop(task()) == GOOD
    assert not list(tmp_path.rglob("events.jsonl"))


def test_a_turn_event_that_cannot_be_written_neither_holds_budget_nor_stops_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from deploy_workflow import run_events
    from deploy_workflow.model.budget import Budget

    def full_disk(_fd: int) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(run_events, "os", SimpleNamespace(fsync=full_disk))
    adapter = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    loop = HandoffExecutor(
        tmp_path / "live", adapter=adapter, cap_usd=Decimal(10), check=check, events=tmp_path
    )
    with pytest.warns(RuntimeWarning, match="run event not recorded: turn"):
        assert loop(task()) == GOOD
    assert len(adapter.requests) == 1
    assert not loop.budget.unsettled
    Budget(Decimal(10), tmp_path / "live").reserve(
        "call-next", Decimal("0.01"), config_id="sol-medium"
    )


def _boom(*_a, **_k):
    raise ArithmeticError("injected post-send fault")


@pytest.mark.parametrize("broken", ["redacted_turn", "price_usage"])
def test_a_post_reply_fault_settles_the_hold_as_unknown_and_records_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    """R15: redaction or pricing raising after a paid send must not leave the hold unsettled."""
    import json

    from deploy_workflow.model import handoff as handoff_module
    from deploy_workflow.model.budget import read_reservation_snapshot

    adapter = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    monkeypatch.setattr(handoff_module, broken, _boom)
    with pytest.raises(RuntimeError, match="cpos_live_stopped"):
        loop(task())
    (marker,) = read_reservation_snapshot(tmp_path)
    assert marker.status is not None  # settled, not left held
    assert loop.budget.spent == marker.usd > 0  # the whole hold counts, never zero
    (row,) = [json.loads(n) for n in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert row["cost_status"] == "unknown" and row["settled_usd"] is None
    assert "ArithmeticError: injected post-send fault" in row["error"]


def test_a_redactor_that_fails_on_an_adapter_error_still_settles_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy_workflow.model.budget import read_reservation_snapshot

    adapter = Adapter(RuntimeError("socket gone"))
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    monkeypatch.setattr(loop.redactor, "exception", _boom)
    with pytest.raises(RuntimeError, match="cpos_live_stopped"):
        loop(task())
    (marker,) = read_reservation_snapshot(tmp_path)
    assert marker.status is not None
    assert loop.budget.spent == marker.usd > 0
    (row,) = [json.loads(n) for n in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert row["error"].startswith(REDACTION_FAILED) and row["cost_status"] == "unknown"


def test_a_pricing_fault_stop_is_one_line_and_the_trace_stays_in_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy_workflow.model import handoff as handoff_module

    monkeypatch.setattr(handoff_module, "price_usage", _boom)
    adapter = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    with pytest.raises(RuntimeError) as caught:
        loop(task())
    message = str(caught.value)
    assert "\n" not in message and "Traceback" not in message
    assert message.endswith("unusable reply: ArithmeticError: injected post-send fault")
    (row,) = [json.loads(n) for n in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert "Traceback" in row["error"]


@pytest.mark.parametrize("kind", ["not_sent", "sent_known"])
def test_a_zero_cost_reply_with_a_pricing_fault_is_recorded_computed_and_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: Any
) -> None:
    from deploy_workflow.model import handoff as handoff_module

    monkeypatch.setattr(handoff_module, "price_usage", _boom)
    reply = AdapterReply(kind, None, None, None, "Refused", None, 1, 2, message="refused")
    loop = HandoffExecutor(tmp_path, adapter=Adapter(reply), cap_usd=Decimal(10), check=check)
    with pytest.raises(RuntimeError, match="cpos_live_stopped"):
        loop(task())
    (row,) = [json.loads(n) for n in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert row["settled_usd"] == "0" and row["cost_status"] == "computed"
    assert loop.budget.spent == 0


def test_an_adapter_failure_keeps_its_message_beside_a_pricing_fault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy_workflow.model import handoff as handoff_module

    monkeypatch.setattr(handoff_module, "price_usage", _boom)
    adapter = Adapter(RuntimeError("socket gone after send"))
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    with pytest.raises(RuntimeError, match="cpos_live_stopped"):
        loop(task())
    (row,) = [json.loads(n) for n in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert "socket gone after send" in row["error"] and "injected post-send fault" in row["error"]


def test_a_post_reply_exception_whose_str_raises_still_settles_and_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy_workflow.model import handoff as handoff_module
    from deploy_workflow.model.budget import read_reservation_snapshot

    class Opaque(ArithmeticError):
        def __str__(self) -> str:
            raise ValueError("no text")

    def opaque(*_a: Any, **_k: Any) -> Any:
        raise Opaque

    monkeypatch.setattr(handoff_module, "price_usage", opaque)
    adapter = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    loop = HandoffExecutor(tmp_path, adapter=adapter, cap_usd=Decimal(10), check=check)
    with pytest.raises(RuntimeError, match="cpos_live_stopped"):
        loop(task())
    (marker,) = read_reservation_snapshot(tmp_path)
    assert marker.status is not None and loop.budget.spent == marker.usd > 0
    (row,) = [json.loads(n) for n in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert row["cost_status"] == "unknown"


def test_loop_json_records_the_adapters_auth_only_when_it_has_one(tmp_path: Path) -> None:
    import json

    class Authed(Adapter):
        auth = "gh-login"

    with_auth, without = tmp_path / "a", tmp_path / "b"
    with_auth.mkdir(), without.mkdir()
    HandoffExecutor(with_auth, adapter=Authed(), cap_usd=Decimal(10), check=check)
    HandoffExecutor(without, adapter=Adapter(), cap_usd=Decimal(10), check=check)
    assert json.loads((with_auth / "loop.json").read_text())["auth"] == "gh-login"
    assert "auth" not in json.loads((without / "loop.json").read_text())


# ---------------------------------------------------------------- web search for CP-DR


def searched(call: ToolCall, searches: int) -> AdapterReply:
    """A reply that searched ``searches`` times and opened one page before ``call``."""
    items = [
        {"type": "web_search_call", "id": f"ws_{n}", "status": "completed", "action": action}
        for n, action in enumerate(
            [{"type": "search", "queries": [f"peer {n}"]} for n in range(searches)]
            + [{"type": "open_page", "url": "https://example.com/peer"}]
        )
    ]
    reply = turn(call)
    assert reply.turn is not None
    found = replace(
        reply.turn, provider_blocks=tuple(ProviderBlock(WEB_SEARCH_BLOCK, i) for i in items)
    )
    return replace(reply, turn=found)


def record(folder: Path) -> dict[str, Any]:
    return json.loads((folder / "calls.jsonl").read_text().splitlines()[0])


def test_web_search_is_offered_to_the_research_module_and_each_search_is_charged(
    tmp_path: Path,
) -> None:
    research = replace(task(), module_id="CP-DR")
    write = ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})
    on = Adapter(searched(write, searches=3))
    loop = HandoffExecutor(
        tmp_path / "on", adapter=on, cap_usd=Decimal(10), check=check, web_search=True
    )
    assert loop(research) == GOOD
    offered = [t for t in on.requests[0].tools if hosted_kind(t)]
    assert [(t.name, t.parameters["max_calls"]) for t in offered] == [("web_search", 16)]
    system = on.requests[0].messages[0].text
    assert "web_search" in system and "public" in system and "cutoff" in system
    off = Adapter(turn(write))
    plain = HandoffExecutor(tmp_path / "off", adapter=off, cap_usd=Decimal(10), check=check)
    assert plain(research) == GOOD
    assert not [t for t in off.requests[0].tools if hosted_kind(t)]
    # OpenAI pricing page, fetched 2026-11-10: web search is USD 10.00 per 1,000 calls. Three
    # searches cost USD 0.03 beyond the same tokens; the hold covers 16 calls, USD 0.16.
    assert loop.budget.spent - plain.budget.spent == Decimal("0.03")
    held = Decimal(record(tmp_path / "on")["reserved_usd"])
    assert held - Decimal(record(tmp_path / "off")["reserved_usd"]) == Decimal("0.16")


def test_web_search_leaves_every_other_module_unchanged(tmp_path: Path) -> None:
    write = ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})
    on, off = Adapter(turn(write)), Adapter(turn(write))
    HandoffExecutor(tmp_path / "on", adapter=on, cap_usd=Decimal(10), check=check, web_search=True)(
        task()
    )
    HandoffExecutor(tmp_path / "off", adapter=off, cap_usd=Decimal(10), check=check)(task())
    assert on.requests == off.requests


def test_web_search_is_refused_off_the_openai_configurations(tmp_path: Path) -> None:
    class Opus(Adapter):
        config_id = "opus-medium"

    with pytest.raises(ValueError, match="web search"):
        HandoffExecutor(tmp_path, adapter=Opus(), cap_usd=Decimal(10), check=check, web_search=True)


def test_a_sent_reply_that_cannot_be_read_is_charged_every_search_it_could_have_made(
    tmp_path: Path,
) -> None:
    research = replace(task(), module_id="CP-DR")
    usage = Usage(input_tokens=100, output_tokens=50)
    spent = {}
    for name, web in (("on", True), ("off", False)):
        unread = AdapterReply("sent_usage", None, None, 502, "BadGateway", None, 1, 2, usage)
        loop = HandoffExecutor(
            tmp_path / name,
            adapter=Adapter(unread),
            cap_usd=Decimal(10),
            check=check,
            web_search=web,
        )
        with pytest.raises(RuntimeError, match="cpos_live_stopped"):
            loop(research)
        spent[name] = loop.budget.spent
    assert spent["on"] - spent["off"] == Decimal("0.16")  # 16 searches at USD 0.01, not counted


# ---------------------------------------------------------------- per-module effort


def test_effort_by_module_reaches_requests_call_log_and_loop_json(tmp_path: Path) -> None:
    one = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    other = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
    high_dir, mid_dir = tmp_path / "high", tmp_path / "mid"
    high_dir.mkdir(), mid_dir.mkdir()
    efforts = {"CP-1A": "high"}
    HandoffExecutor(
        high_dir, adapter=one, cap_usd=Decimal(10), check=check, effort_by_module=efforts
    )(replace(task(), module_id="CP-1A"))
    HandoffExecutor(
        mid_dir, adapter=other, cap_usd=Decimal(10), check=check, effort_by_module=efforts
    )(task())
    assert [r.effort for r in one.requests] == ["high"]
    assert [r.effort for r in other.requests] == ["medium"]
    assert record(high_dir)["requested_effort"] == "high"
    assert record(mid_dir)["requested_effort"] == "medium"
    assert json.loads((high_dir / "loop.json").read_text())["effort_by_module"] == {"CP-1A": "high"}


def test_loop_json_omits_an_empty_effort_map(tmp_path: Path) -> None:
    HandoffExecutor(tmp_path, adapter=Adapter(), cap_usd=Decimal(10), check=check)
    assert "effort_by_module" not in json.loads((tmp_path / "loop.json").read_text())


@pytest.mark.parametrize("efforts", [{"CP-NOPE": "high"}, {"CP-1A": "max"}])
def test_effort_by_module_refuses_unknown_modules_and_disallowed_efforts(
    tmp_path: Path, efforts: dict[str, str]
) -> None:
    with pytest.raises(ValueError, match="effort_by_module"):
        HandoffExecutor(
            tmp_path, adapter=Adapter(), cap_usd=Decimal(10), check=check, effort_by_module=efforts
        )


def test_each_modules_invocation_seed_carries_its_own_effort(tmp_path: Path) -> None:
    efforts = {"CP-1A": "high"}
    for module, name in (("CP-1A", "high"), ("CP-2", "mid")):
        folder = tmp_path / name
        folder.mkdir()
        adapter = Adapter(turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})))
        HandoffExecutor(
            folder, adapter=adapter, cap_usd=Decimal(10), check=check, effort_by_module=efforts
        )(replace(task(), module_id=module))
    seeds = {
        name: json.loads(next((tmp_path / name / "modules").glob("*/invocation.json")).read_text())
        for name in ("high", "mid")
    }
    assert seeds["high"]["effort"] == "high"
    assert seeds["mid"]["effort"] == "medium"


def test_every_turn_of_a_module_carries_its_effort(tmp_path: Path) -> None:
    adapter = Adapter(
        turn(ToolCall("r", "read_pages", {"source_id": "S1.txt", "first": 1, "last": 1})),
        turn(ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})),
    )
    HandoffExecutor(
        tmp_path,
        adapter=adapter,
        cap_usd=Decimal(10),
        check=check,
        effort_by_module={"CP-2": "high"},
    )(task())
    assert [r.effort for r in adapter.requests] == ["high", "high"]


# Fragments of the retained high CP-6 drafts (write 1 rejected for "canonical"; write 2 accepted,
# having also replaced two sourced FY2023 figures with "Not supplied").
CP6_FIRST = (
    "## Request\nTDG\n## Sources\nS1\n## Findings\n"
    "| Adjustments | USD 247 million | USD 360 million: acquisition 70; compensation 217 |"
    " FY2023 |\n"
    "| Reported revolving availability | USD 755 million | USD 843 million | FY2023 |\n"
    "The canonical bridge is shown.\n"
    "## Calculations\nNone\n## Gaps\nNone\n## Next module\ndelivery\n"
)
CP6_SECOND = (
    "## Request\nTDG\n## Sources\nS1\n## Findings\n"
    "| Adjustments | Not supplied: prior bridge not adopted for this debate | "
    "USD 360 million: acquisition 70; compensation 217 | FY2023 |\n"
    "| Reported revolving availability | Not supplied: prior availability not adopted for this "
    "debate | USD 843 million | FY2023 |\n"
    "The adopted bridge is shown.\n"
    "## Calculations\nNone\n## Gaps\nNone\n## Next module\ndelivery\n"
)


def _writes(tmp_path: Path, *drafts: str, issues: tuple[str, ...] = ("line 3: canonical",)):
    """A module whose checker rejects every draft containing a flag word, with `issues`."""

    def verdict(_task: HandoffTask, raw: bytes) -> tuple[str, ...]:
        return issues if b"canonical" in raw or b"Not accepted" in raw else ()

    module = ModuleTools(task(), tmp_path, verdict, tmp_path / "run")
    return module, [module.call("write_handoff", {"markdown": d}) for d in drafts]


def _review(tmp_path: Path, n: int) -> dict[str, Any]:
    return json.loads((tmp_path / f"{n}.review.json").read_text())


def test_a_repair_that_drops_two_sourced_figures_is_recorded_and_accepted(tmp_path: Path) -> None:
    from deploy_workflow.run_events import EVENTS, read_events

    module, results = _writes(tmp_path, CP6_FIRST, CP6_SECOND)
    assert module.accepted and results[1].startswith("ACCEPTED")
    dropped = _review(tmp_path, 2)["dropped_values"]
    assert [(d["value"], d["previous_line"]) for d in dropped] == [
        ("USD 247 million", 6),
        ("USD 755 million", 7),
    ]
    event = [e for e in read_events(tmp_path / "run" / EVENTS) if "dropped" in e["event"]]
    assert [(e["event"], e["module"], e["count"]) for e in event] == [
        ("values_dropped_on_repair", "CP-2", 2)
    ]


def test_a_rejected_repair_that_drops_values_asks_for_each_back(tmp_path: Path) -> None:
    second = CP6_SECOND + "The canonical wording remains.\n"
    module, results = _writes(tmp_path, CP6_FIRST, second)
    assert not module.accepted and results[1].startswith("REJECTED")
    assert "USD 247 million (Adjustments, line 6" in results[1]
    assert "USD 755 million (Reported revolving availability, line 7" in results[1]
    assert results[1].endswith(
        ". No issue named them. If a change was intended, keep it; otherwise restore each value."
    )
    assert [d["value"] for d in _review(tmp_path, 2)["dropped_values"]] == [
        "USD 247 million",
        "USD 755 million",
    ]


def test_a_repair_that_adds_a_figure_flags_nothing(tmp_path: Path) -> None:
    second = CP6_FIRST.replace("canonical", "adopted") + "The margin was 9.8% in FY2023.\n"
    module, _ = _writes(tmp_path, CP6_FIRST, second)
    assert module.accepted and _review(tmp_path, 2)["dropped_values"] == []


def test_a_figure_the_issue_named_may_be_removed(tmp_path: Path) -> None:
    second = CP6_FIRST.replace("canonical", "adopted").replace("| USD 755 million ", "| n/a ")
    named = ('line 7: "USD 755 million" is not in the handoff: remove it. canonical',)
    module, _ = _writes(tmp_path, CP6_FIRST, second, issues=named)
    assert module.accepted and _review(tmp_path, 2)["dropped_values"] == []


def test_the_first_write_records_no_key(tmp_path: Path) -> None:
    _, results = _writes(tmp_path, CP6_FIRST)
    assert results[0].startswith("REJECTED")
    assert "dropped_values" not in _review(tmp_path, 1)


def test_a_figure_that_only_moved_to_another_line_is_not_flagged(tmp_path: Path) -> None:
    second = (
        "## Request\nTDG\n## Sources\nS1\n## Findings\n"
        "Note: USD 247 million, USD 755 million, USD 360 million (acquisition 70; compensation 217)"
        " and USD 843 million (FY2023).\nThe adopted bridge.\n"
        "## Calculations\nNone\n## Gaps\nNone\n## Next module\ndelivery\n"
    )
    module, _ = _writes(tmp_path, CP6_FIRST, second)
    assert module.accepted and _review(tmp_path, 2)["dropped_values"] == []


def test_a_clean_accepted_repair_emits_no_event(tmp_path: Path) -> None:
    from deploy_workflow.run_events import EVENTS, read_events

    _writes(tmp_path, CP6_FIRST, CP6_FIRST.replace("canonical", "adopted"))
    assert all(
        e["event"] != "values_dropped_on_repair" for e in read_events(tmp_path / "run" / EVENTS)
    )


# ---------------------------------------------------------------- compaction (T3)
#
# The fragments are the real CP-8 compaction of run tdg-full-copilot-sol-high-001-resume (see
# tests/model/_compaction.py); the amounts below are worked by hand from the sol-medium rates
# (USD per 1M tokens: input 2.00, output 10.00): the call's own 100 input and 50 output tokens
# cost (100 x 2.00 + 50 x 10.00) / 1M = 0.0007, and the compaction's reported charge is
# 9,963,810,000 nano-AIU x 1E-11 = 0.0996381.

ATTEMPT = "9adc3933-fffb-4810-a23a-717e91c08200"
CP8_START = Compaction(kind="start", attempt_id=ATTEMPT, tokens_before=241349, token_limit=272000)
CP8_DONE = Compaction(
    kind="complete",
    attempt_id=ATTEMPT,
    tokens_before=259070,
    tokens_after=42447,
    token_limit=272000,
    success=True,
    usd=Decimal("0.0996381"),
)


def write_call() -> ToolCall:
    return ToolCall("w", "write_handoff", {"markdown": GOOD.decode()})


def compacted(reply: AdapterReply, *found: Compaction) -> AdapterReply:
    return replace(reply, compactions=tuple(found))


def run_events(folder: Path) -> list[dict[str, Any]]:
    return read_events(folder / "events.jsonl")


def row_of(folder: Path) -> dict[str, Any]:
    return json.loads((folder / "live/calls.jsonl").read_text().splitlines()[0])


def compacting_loop(
    tmp_path: Path, *replies: AdapterReply, cap: str = "10"
) -> tuple[HandoffExecutor, Path]:
    folder = tmp_path / "run"
    loop = HandoffExecutor(
        folder / "live",
        adapter=Adapter(*replies),
        cap_usd=Decimal(cap),
        check=check,
        events=folder,
    )
    return loop, folder


def test_a_completed_compaction_is_recorded_charged_and_flagged(tmp_path: Path) -> None:
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), CP8_START, CP8_DONE))
    assert loop(task()) == GOOD
    assert loop.budget.spent == Decimal("0.1003381")  # 0.0007 + 0.0996381
    assert not loop.budget.unsettled
    row = row_of(folder)
    assert Decimal(row["settled_usd"]) == Decimal("0.1003381")
    assert row["cost_status"] == "computed"
    assert row["compactions"] == [
        {
            "kind": "start",
            "attempt_id": ATTEMPT,
            "tokens_before": 241349,
            "tokens_after": None,
            "token_limit": 272000,
            "success": None,
            "usd": None,
            "request_count": None,
        },
        {
            "kind": "complete",
            "attempt_id": ATTEMPT,
            "tokens_before": 259070,
            "tokens_after": 42447,
            "token_limit": 272000,
            "success": True,
            "usd": "0.0996381",
            "request_count": None,
        },
    ]
    seen = [e for e in run_events(folder) if e["event"].startswith("context_compact")]
    assert [(e["event"], e["module"], e["call_index"]) for e in seen] == [
        ("context_compaction_started", "CP-2", 0),
        ("context_compacted", "CP-2", 0),
    ]
    assert seen[0]["tokens_before"] == 241349
    assert (seen[1]["tokens_before"], seen[1]["tokens_after"]) == (259070, 42447)
    assert seen[1]["usd"] == "0.0996381" and seen[1]["applied"] is True
    assert loop.written_after_compaction == CP8_DONE


def test_the_accepted_handoff_is_the_one_the_checker_judges_after_a_compaction(
    tmp_path: Path,
) -> None:
    """The flag does not change acceptance: a draft the checker rejects is still rejected."""
    bad = GOOD.replace(b"100", b"101")
    loop, _ = compacting_loop(
        tmp_path,
        compacted(turn(ToolCall("w", "write_handoff", {"markdown": bad.decode()})), CP8_DONE),
        turn(ToolCall("e", "edit_handoff", {"edits": [{"old": "101", "new": "100"}]})),
    )
    assert loop(task()) == GOOD
    assert "REJECTED" in loop.adapter.requests[1].messages[-1].text


def test_a_compaction_that_started_but_did_not_complete_is_recorded_not_flagged(
    tmp_path: Path,
) -> None:
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), CP8_START))
    assert loop(task()) == GOOD
    assert loop.budget.spent == Decimal("0.0007")  # no compaction charge is known
    assert loop.written_after_compaction is None
    names = [e["event"] for e in run_events(folder) if e["event"].startswith("context_compact")]
    assert names == ["context_compaction_started"]
    assert [c["kind"] for c in row_of(folder)["compactions"]] == ["start"]


def test_a_failed_compaction_is_charged_but_does_not_flag_the_module(tmp_path: Path) -> None:
    failed = replace(CP8_DONE, success=False, usd=Decimal("0.05"))
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), failed))
    assert loop(task()) == GOOD
    assert loop.budget.spent == Decimal("0.0507")
    assert loop.written_after_compaction is None
    (event,) = [e for e in run_events(folder) if e["event"] == "context_compacted"]
    assert event["applied"] is False


def test_a_call_with_no_compaction_writes_nothing_new(tmp_path: Path) -> None:
    loop, folder = compacting_loop(tmp_path, turn(write_call()))
    assert loop(task()) == GOOD
    assert row_of(folder)["compactions"] is None
    assert not [e for e in run_events(folder) if "compact" in e["event"]]
    assert loop.written_after_compaction is None
    assert loop.budget.spent == Decimal("0.0007")


def test_a_compaction_charge_past_the_cap_is_an_overrun_not_a_dropped_charge(
    tmp_path: Path,
) -> None:
    """The call's hold (about USD 5.5 on sol-medium) was inside the cap (USD 10); a compaction
    charge of USD 11 arrives after it. The ledger's overrun rule records the whole amount and
    stops the run; it is neither refused nor left out."""
    huge = replace(CP8_DONE, usd=Decimal(11))
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), huge))
    with pytest.raises(RuntimeError, match="cpos_live_stopped.*overrun=True"):
        loop(task())
    assert loop.budget.stop_kind == "overrun"
    assert loop.budget.spent == Decimal("11.0007")  # 11 + 0.0007: counted, above the cap of 10
    assert loop.budget.spent > loop.budget.cap_usd
    assert Decimal(row_of(folder)["settled_usd"]) == Decimal("11.0007")


def test_a_completed_compaction_with_no_readable_charge_is_an_unknown_charge(
    tmp_path: Path,
) -> None:
    """As an unreadable reply is today: the whole hold stays and the run stops. Never a zero."""
    loop, folder = compacting_loop(
        tmp_path, compacted(turn(write_call()), replace(CP8_DONE, usd=None))
    )
    with pytest.raises(RuntimeError, match="cpos_live_stopped"):
        loop(task())
    row = row_of(folder)
    assert row["cost_status"] == "unknown" and row["settled_usd"] is None
    assert loop.budget.stop_kind == "unknown"
    assert loop.budget.spent == Decimal(row["reserved_usd"]) > 0


class CopilotLike(Adapter):
    """The Copilot route as the executor sees it: a ruling in force and a reported charge."""

    config_id = "copilot-sol-medium"
    ruling = Path("lift.md")


def copilot_loop(tmp_path: Path) -> tuple[HandoffExecutor, Path]:
    folder = tmp_path / "run"
    reply = turn(write_call())
    reply = replace(reply, billed_usd=Decimal("0.01"))
    loop = HandoffExecutor(
        folder / "live", adapter=CopilotLike(reply), cap_usd=Decimal(10), check=check, events=folder
    )
    return loop, folder


def prompt_of(size: int) -> HandoffTask:
    return replace(task(), handoffs={"CP-1": b"x" * size})


def test_a_first_prompt_near_the_copilot_limit_is_flagged_before_the_first_call(
    tmp_path: Path,
) -> None:
    """800,000 bytes of handoff: at 3.85 bytes per token that is about 208,000 tokens, which with
    the 16,000-token output budget passes 80% of 272,000 (217,600). It warns; the run goes on."""
    loop, folder = copilot_loop(tmp_path)
    assert loop(prompt_of(800_000)) == GOOD
    (event,) = [e for e in run_events(folder) if e["event"] == "first_prompt_near_limit"]
    (invocation,) = (folder / "live/modules").glob("*/invocation.json")
    size = invocation.stat().st_size
    expected = -(-size * 100 // 385)  # ceil(size / 3.85), by hand
    assert event["module"] == "CP-2" and event["estimated_tokens"] == expected
    assert event["output_tokens"] == 16000 and event["token_limit"] == 272000
    assert expected + 16000 > 0.8 * 272000


def test_a_small_first_prompt_on_copilot_raises_no_warning(tmp_path: Path) -> None:
    loop, folder = copilot_loop(tmp_path)
    assert loop(prompt_of(1_000)) == GOOD
    assert not [e for e in run_events(folder) if e["event"] == "first_prompt_near_limit"]


def test_the_first_prompt_check_is_for_the_copilot_route_only(tmp_path: Path) -> None:
    loop, folder = compacting_loop(tmp_path, turn(write_call()))  # sol-medium, OpenAI
    assert loop(prompt_of(800_000)) == GOOD
    assert not [e for e in run_events(folder) if e["event"] == "first_prompt_near_limit"]


def test_the_record_reads_back_with_its_compactions_and_an_old_record_still_reads(
    tmp_path: Path,
) -> None:
    from deploy_workflow.model.record import CallRecord
    from deploy_workflow.model_testing.records import read_journal

    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), CP8_START, CP8_DONE))
    assert loop(task()) == GOOD
    (record,) = read_journal(folder / "live/calls.jsonl")
    assert record.compactions is not None and record.compactions[1].usd == Decimal("0.0996381")
    assert record.compaction_usd == Decimal("0.0996381")
    assert record.own_usd == Decimal("0.0007")  # the turn's own charge, without the compaction
    old = row_of(folder)
    del old["compactions"]  # a record written before the field existed
    assert CallRecord.model_validate_json(json.dumps(old)).compactions is None


def _body(findings: str) -> str:
    return (
        "## Request\nTDG\n## Sources\nS1\n## Findings\n"
        + findings
        + "## Calculations\nNone\n## Gaps\nNone\n## Next module\ndelivery\n"
    )


def _dropped(tmp_path: Path, first: str, second: str, issues: tuple[str, ...]) -> list[Any]:
    module, _ = _writes(tmp_path, _body(first + "canonical\n"), _body(second), issues=issues)
    assert module.accepted
    return [d["value"] for d in _review(tmp_path, 2)["dropped_values"]]


def test_a_value_changed_in_place_is_a_dropped_old_value(tmp_path: Path) -> None:
    row = "| Adjustments | USD 247 million | FY2023 |\n"
    assert _dropped(tmp_path, row, row.replace("247", "240"), ("line 6: canonical",)) == [
        "USD 247 million"
    ]


def test_a_deleted_table_row_is_flagged_though_another_row_has_its_shape(tmp_path: Path) -> None:
    rows = "| A | USD 247 million | FY2023 |\n| B | USD 9 million | FY2023 |\n"
    kept = "| B | USD 9 million | FY2023 |\n"
    assert _dropped(tmp_path, rows, kept, ("line 8: canonical",)) == ["USD 247 million"]


def test_an_issue_that_quotes_the_old_number_excuses_a_change_in_place(tmp_path: Path) -> None:
    row = "| Adjustments | USD 247 million | FY2023 |\n"
    issue = ('line 6: "247 million" does not appear elsewhere in the handoff; canonical',)
    assert _dropped(tmp_path, row, row.replace("247", "240"), issue) == []


def test_a_quote_excuses_only_the_line_the_issue_names(tmp_path: Path) -> None:
    rows = "Availability was USD 755 million.\n| Revolver | USD 755 million | FY2023 |\n"
    issue = ('line 6: "USD 755 million" does not appear elsewhere; canonical',)
    second = "Availability is in the table.\n| Revolver | Not supplied | FY2023 |\n"
    assert _dropped(tmp_path, rows, second, issue) == ["USD 755 million"]


def test_a_number_already_on_the_line_is_no_correction_of_it(tmp_path: Path) -> None:
    row = "Net debt was USD 247 million in 2024.\n"
    issue = ("State the 2024 comparison under Findings.",)
    assert _dropped(tmp_path, row, row.replace("247", "240"), issue) == ["USD 247 million"]


def test_a_line_number_in_an_issue_label_excuses_no_value(tmp_path: Path) -> None:
    row = "| Adjustments | USD 247 million | FY2023 |\n"
    assert _dropped(
        tmp_path, row, "| Adjustments | Not supplied | FY2023 |\n", ('line 247: "canonical"',)
    ) == ["USD 247 million"]


def test_an_unrelated_figure_of_another_currency_or_unit_hides_nothing(tmp_path: Path) -> None:
    row = "| Adjustments | USD 247 million | FY2023 |\n"
    other = "EUR 247 million of notes; 247 million shares.\n"
    assert _dropped(tmp_path, row, other, ("line 6: canonical",)) == ["USD 247 million"]


def test_a_bracketed_negative_in_a_table_is_tracked(tmp_path: Path) -> None:
    row = "| FY2022 | 5,429 | (755) |\n"
    assert _dropped(
        tmp_path, row, "| FY2022 | 5,429 | Not supplied |\n", ("line 6: canonical",)
    ) == ["(755)"]


def test_a_dropped_comparison_fault_keeps_acceptance_and_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy_workflow.model import handoff
    from deploy_workflow.run_events import EVENTS, read_events

    def broken(*_a: Any, **_k: Any) -> list[Any]:
        raise IndexError("boom")

    monkeypatch.setattr(handoff, "lost_values", broken)
    module, results = _writes(tmp_path, CP6_FIRST, CP6_SECOND)
    assert module.accepted and results[1] == "ACCEPTED"
    review = _review(tmp_path, 2)
    assert review["issues"] == [] and review["dropped_values_error"] == "IndexError: boom"
    assert "dropped_values" not in review
    failed = [e for e in read_events(tmp_path / "run" / EVENTS) if "failed" in e["event"]]
    assert [(e["event"], e["module"]) for e in failed] == [("dropped_values_check_failed", "CP-2")]
    assert "boom" in failed[0]["error"]


def test_a_comparison_fault_on_a_rejected_repair_keeps_the_checkers_issues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy_workflow.model import handoff

    def broken(*_a: Any, **_k: Any) -> list[Any]:
        raise ValueError("boom")

    monkeypatch.setattr(handoff, "lost_values", broken)
    module, results = _writes(tmp_path, CP6_FIRST, CP6_FIRST)
    assert not module.accepted and results[1].startswith("REJECTED (1 writes left)")
    assert "line 3: canonical" in results[1] and "no longer contains" not in results[1]


@pytest.mark.parametrize(
    ("first", "second", "issue", "value"),
    [
        (
            "| Revolver | USD 256 million | FY2023 |\n",
            "| Revolver | Not supplied | FY2023 |\n",
            "List each issuer source relied on with its exact name and sha256.",
            "USD 256 million",
        ),
        (
            "| Items | 43 | FY2023 |\n",
            "| Items | Not supplied | FY2023 |\n",
            "C43 appears outside the ledger's ref columns; write a ref only in ref columns.",
            "43",
        ),
        (
            "Leverage was 4.1x at USD 700 million of debt.\n",
            "Leverage was 4.1x.\n",
            "Findings run to 700 words; keep them under 600.",
            "USD 700 million",
        ),
    ],
)
def test_an_unquoted_issue_that_names_no_line_excuses_nothing(
    tmp_path: Path, first: str, second: str, issue: str, value: str
) -> None:
    assert _dropped(tmp_path, first, second, (issue + " canonical",)) == [value]


@pytest.mark.parametrize("label", ["lines 6-7", "lines 6 and 7", "lines 5, 6 and 7"])
def test_every_line_an_issue_names_is_named(tmp_path: Path, label: str) -> None:
    rows = "| A | USD 247 million | FY2023 |\n| B | USD 755 million | FY2023 |\n"
    kept = "| A | USD 240 million | FY2023 |\n| B | USD 750 million | FY2023 |\n"
    issue = f'{label}: "247 million" and "755 million" are wrong; canonical'
    assert _dropped(tmp_path, rows, kept, (issue,)) == []


@pytest.mark.parametrize(
    "issue",
    [
        "line 6, 247 million is unsupported; remove",
        "line 6, 2.5 million and 247 million are unsupported",
    ],
)
def test_a_comma_after_a_line_label_does_not_make_the_number_a_line(
    tmp_path: Path, issue: str
) -> None:
    row = "| Adjustments | USD 247 million | FY2023 |\n"
    removed = "| Adjustments | Not supplied | FY2023 |\n"
    assert _dropped(tmp_path, row, removed, (issue + " canonical",)) == []


def test_an_interrupt_in_the_comparison_still_leaves_the_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from deploy_workflow.model import handoff

    def interrupted(*_a: Any, **_k: Any) -> list[Any]:
        raise KeyboardInterrupt

    monkeypatch.setattr(handoff, "lost_values", interrupted)
    module = ModuleTools(
        task(),
        tmp_path,
        lambda _t, raw: ("line 3: canonical",) if b"canonical" in raw else (),
        tmp_path / "run",
    )
    module.call("write_handoff", {"markdown": CP6_FIRST})
    with pytest.raises(KeyboardInterrupt):
        module.call("write_handoff", {"markdown": CP6_SECOND})
    assert _review(tmp_path, 2) == {"issues": []}


# ---------------------------------------------------------------- compaction, fix round 1


class Draining(Adapter):
    """An adapter that, like the Copilot one, can hand back the compaction events still queued for
    a module's session when the module ends."""

    def __init__(self, late: tuple[Compaction, ...], *replies: AdapterReply | Exception) -> None:
        super().__init__(*replies)
        self.late, self.drained = late, []

    def drain_compactions(self, digest: str) -> tuple[Compaction, ...]:
        self.drained.append(digest)
        return self.late


def draining_loop(
    tmp_path: Path, late: tuple[Compaction, ...], *replies: AdapterReply
) -> tuple[HandoffExecutor, Path, Draining]:
    folder = tmp_path / "run"
    adapter = Draining(late, *replies)
    loop = HandoffExecutor(
        folder / "live", adapter=adapter, cap_usd=Decimal(10), check=check, events=folder
    )
    return loop, folder, adapter


def named(folder: Path, event: str) -> list[dict[str, Any]]:
    return [e for e in run_events(folder) if e["event"] == event]


def test_a_start_with_no_completion_is_reported_uncharged_when_the_module_is_accepted(
    tmp_path: Path,
) -> None:
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), CP8_START))
    assert loop(task()) == GOOD
    (event,) = named(folder, "compaction_uncharged")
    assert (event["module"], event["call_index"], event["tokens_before"]) == ("CP-2", 0, 241349)
    assert event["reason"] == "started, no completion reported"
    assert loop.budget.spent == Decimal("0.0007")  # not charged, not an unknown hold


def test_a_start_whose_completion_arrives_in_a_later_call_is_not_uncharged(tmp_path: Path) -> None:
    loop, folder = compacting_loop(
        tmp_path,
        compacted(turn(ToolCall("r", "list_sources", {})), CP8_START),
        compacted(turn(write_call()), CP8_DONE),
    )
    assert loop(task()) == GOOD
    assert not named(folder, "compaction_uncharged")


def test_a_module_that_stops_still_reports_its_uncharged_start(tmp_path: Path) -> None:
    loop, folder = compacting_loop(
        tmp_path, compacted(turn(ToolCall("r", "list_sources", {})), CP8_START), RuntimeError("x")
    )
    with pytest.raises(RuntimeError):
        loop(task())
    assert [e["module"] for e in named(folder, "compaction_uncharged")] == ["CP-2"]


def test_a_late_completion_is_disclosed_with_its_amount_not_settled(tmp_path: Path) -> None:
    """The last call is already settled and logged (write-once), so no marker is invented: the
    amount is an event, and the start it completes is no longer an uncharged start."""
    loop, folder, adapter = draining_loop(
        tmp_path, (CP8_DONE,), compacted(turn(write_call()), CP8_START)
    )
    assert loop(task()) == GOOD
    assert len(adapter.drained) == 1
    (event,) = named(folder, "compaction_charge_late")
    assert (event["module"], event["call_index"], event["usd"]) == ("CP-2", 0, "0.0996381")
    assert not named(folder, "compaction_uncharged")
    assert loop.budget.spent == Decimal("0.0007")
    assert len((folder / "live/calls.jsonl").read_text().splitlines()) == 1


def test_a_late_completion_with_no_readable_charge_is_uncharged(tmp_path: Path) -> None:
    loop, folder, _ = draining_loop(tmp_path, (replace(CP8_DONE, usd=None),), turn(write_call()))
    assert loop(task()) == GOOD
    (event,) = named(folder, "compaction_uncharged")
    assert event["reason"] == "completed after the module ended, no readable charge"


def test_a_failing_drain_does_not_fail_the_module(tmp_path: Path) -> None:
    loop, _, adapter = draining_loop(tmp_path, (), turn(write_call()))

    def broken(digest: str) -> tuple[Compaction, ...]:
        raise OSError("loop gone")

    adapter.drain_compactions = broken  # type: ignore[method-assign]
    assert loop(task()) == GOOD


def test_a_failed_compaction_with_no_usage_block_is_uncharged_and_does_not_stop_the_run(
    tmp_path: Path,
) -> None:
    """The reviewer's probe E1: success false, no usage block."""
    failed = replace(CP8_DONE, success=False, usd=None)
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), failed))
    assert loop(task()) == GOOD
    assert loop.budget.spent == Decimal("0.0007")
    (event,) = named(folder, "compaction_uncharged")
    assert event["reason"] == "failed, no usage reported"
    assert loop.written_after_compaction is None


def test_a_failed_compaction_whose_usage_block_is_unreadable_is_still_an_unknown_charge(
    tmp_path: Path,
) -> None:
    failed = replace(CP8_DONE, success=False, usd=None, usage_reported=True)
    loop, _ = compacting_loop(tmp_path, compacted(turn(write_call()), failed))
    with pytest.raises(RuntimeError, match="cpos_live_stopped"):
        loop(task())
    assert loop.budget.stop_kind == "unknown"


def test_the_same_completion_seen_in_two_calls_is_charged_once(tmp_path: Path) -> None:
    loop, _ = compacting_loop(
        tmp_path,
        compacted(turn(ToolCall("r", "list_sources", {})), CP8_DONE),
        compacted(turn(write_call()), CP8_DONE),
    )
    assert loop(task()) == GOOD
    assert loop.budget.spent == Decimal("0.0007") * 2 + Decimal("0.0996381")


def test_two_completions_in_one_call_are_reported_as_multiple(tmp_path: Path) -> None:
    second = replace(CP8_DONE, attempt_id="b", usd=Decimal("0.05"))
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), CP8_DONE, second))
    assert loop(task()) == GOOD
    (event,) = named(folder, "compaction_multiple")
    assert (event["module"], event["call_index"], event["completions"]) == ("CP-2", 0, 2)
    assert loop.budget.spent == Decimal("0.1503381")


def test_a_completion_with_several_requests_is_reported_as_multiple(tmp_path: Path) -> None:
    loop, folder = compacting_loop(
        tmp_path, compacted(turn(write_call()), replace(CP8_DONE, request_count=2))
    )
    assert loop(task()) == GOOD
    assert len(named(folder, "compaction_multiple")) == 1


def test_one_ordinary_completion_is_not_multiple(tmp_path: Path) -> None:
    loop, folder = compacting_loop(
        tmp_path, compacted(turn(write_call()), replace(CP8_DONE, request_count=1))
    )
    assert loop(task()) == GOOD
    assert not named(folder, "compaction_multiple")


def test_the_first_prompt_warning_is_also_a_plain_line_for_the_launcher(tmp_path: Path) -> None:
    lines: list[str] = []
    folder = tmp_path / "run"
    loop = HandoffExecutor(
        folder / "live",
        adapter=CopilotLike(replace(turn(write_call()), billed_usd=Decimal("0.01"))),
        cap_usd=Decimal(10),
        check=check,
        events=folder,
        notice=lines.append,
    )
    assert loop(prompt_of(800_000)) == GOOD
    (event,) = named(folder, "first_prompt_near_limit")
    (line,) = lines
    assert line.startswith("Context:  CP-2: first prompt about ")
    assert f"{event['estimated_tokens']:,} tokens" in line and "272,000-token limit" in line


def test_a_small_first_prompt_prints_no_notice(tmp_path: Path) -> None:
    lines: list[str] = []
    folder = tmp_path / "run"
    loop = HandoffExecutor(
        folder / "live",
        adapter=CopilotLike(replace(turn(write_call()), billed_usd=Decimal("0.01"))),
        cap_usd=Decimal(10),
        check=check,
        events=folder,
        notice=lines.append,
    )
    assert loop(prompt_of(1_000)) == GOOD
    assert lines == []


def test_compaction_usd_is_exact_beyond_the_default_context() -> None:
    """Probe t3adv-p3: a charge of 38 digits must not round in the subtraction."""
    from deploy_workflow.model.budget import exact_sum
    from deploy_workflow.model.record import CallRecord, CompactionRecord

    big = Decimal(10**37 + 1).scaleb(-11)
    turn_usd = Decimal("0.00000123456")
    rec = CallRecord.model_construct(
        settled_usd=exact_sum((turn_usd, big)),
        compactions=(CompactionRecord.model_construct(usd=big),),
    )
    assert rec.own_usd == turn_usd and rec.compaction_usd == big


# ---------------------------------------------------------------- compaction, end batch


def test_compaction_events_carry_the_attempt_id(tmp_path: Path) -> None:
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), CP8_START, CP8_DONE))
    assert loop(task()) == GOOD
    for name in ("context_compaction_started", "context_compacted"):
        (event,) = named(folder, name)
        assert event["attempt_id"] == ATTEMPT


def test_two_uncharged_starts_in_one_call_are_two_events_with_their_ids(tmp_path: Path) -> None:
    other = replace(CP8_START, attempt_id="second-attempt")
    loop, folder = compacting_loop(tmp_path, compacted(turn(write_call()), CP8_START, other))
    assert loop(task()) == GOOD
    ids = sorted(e["attempt_id"] for e in named(folder, "compaction_uncharged"))
    assert ids == sorted([ATTEMPT, "second-attempt"])


def test_an_attemptless_late_completion_after_an_attemptless_one_is_disclosed(
    tmp_path: Path,
) -> None:
    in_call = replace(CP8_DONE, attempt_id=None)
    late = replace(CP8_DONE, attempt_id=None, usd=Decimal("0.05"))
    loop, folder, _ = draining_loop(tmp_path, (late,), compacted(turn(write_call()), in_call))
    assert loop(task()) == GOOD
    (event,) = named(folder, "compaction_charge_late")
    assert event["usd"] == "0.05"


class Draining2(Draining):
    """A drain that answers differently each time: the module's end, then the run's close."""

    def __init__(self, drains: list[tuple[Compaction, ...]], *replies: AdapterReply) -> None:
        super().__init__((), *replies)
        self.drains = drains

    def drain_compactions(self, digest: str) -> tuple[Compaction, ...]:
        self.drained.append(digest)
        return self.drains.pop(0) if self.drains else ()


def test_a_summary_still_running_at_the_module_end_is_drained_again_before_close(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "run"
    adapter = Draining2([(), (CP8_DONE,), ()], compacted(turn(write_call()), CP8_START))
    loop = HandoffExecutor(
        folder / "live", adapter=adapter, cap_usd=Decimal(10), check=check, events=folder
    )
    assert loop(task()) == GOOD
    assert len(named(folder, "compaction_uncharged")) == 1  # open at the module's end
    loop.drain_late()
    (late,) = named(folder, "compaction_charge_late")
    assert (late["module"], late["usd"], late["attempt_id"]) == ("CP-2", "0.0996381", ATTEMPT)
    loop.drain_late()  # a second sweep finds nothing new and writes nothing again
    assert len(named(folder, "compaction_charge_late")) == 1
    assert len(named(folder, "compaction_uncharged")) == 1


def test_a_sweep_discloses_a_start_that_began_after_the_module_end(tmp_path: Path) -> None:
    folder = tmp_path / "run"
    adapter = Draining2([(), (CP8_START,)], turn(write_call()))
    loop = HandoffExecutor(
        folder / "live", adapter=adapter, cap_usd=Decimal(10), check=check, events=folder
    )
    assert loop(task()) == GOOD
    assert not named(folder, "compaction_uncharged")
    loop.drain_late()
    (event,) = named(folder, "compaction_uncharged")
    assert event["attempt_id"] == ATTEMPT and event["reason"] == "started, no completion reported"


def test_a_value_dropped_by_an_earlier_rejected_draft_is_reported_when_the_third_is_accepted(
    tmp_path: Path,
) -> None:
    from deploy_workflow.run_events import EVENTS, read_events

    second = CP6_SECOND + "The canonical wording remains.\n"
    module, results = _writes(tmp_path, CP6_FIRST, second, CP6_SECOND)
    assert module.accepted and results[2].startswith("ACCEPTED")
    assert [d["value"] for d in _review(tmp_path, 3)["dropped_values"]] == [
        "USD 247 million",
        "USD 755 million",
    ]
    event = [e for e in read_events(tmp_path / "run" / EVENTS) if "dropped" in e["event"]]
    assert [(e["event"], e["module"], e["count"]) for e in event] == [
        ("values_dropped_on_repair", "CP-2", 2)
    ]


def test_a_value_restored_before_acceptance_is_not_reported(tmp_path: Path) -> None:
    from deploy_workflow.run_events import EVENTS, read_events

    second = CP6_SECOND + "The canonical wording remains.\n"
    third = CP6_FIRST.replace("canonical", "adopted")
    module, _ = _writes(tmp_path, CP6_FIRST, second, third)
    assert module.accepted and _review(tmp_path, 3)["dropped_values"] == []
    assert all(
        e["event"] != "values_dropped_on_repair" for e in read_events(tmp_path / "run" / EVENTS)
    )
