"""The method-script checks built after the first seven (ruling
docs/rulings/2026-11-15-method-script-checks.md): the shared `completeness_check.py`, then CP-4C,
CP-1C, CP-2H and CP-1B.

Every handoff here is SYNTHETIC unless named: written by hand in the transport's layout, with each
expected outcome worked by hand from the method's declared columns or formula, not from the
production code. The two retained CP-2E handoffs (`tests/fixtures/esg/CP-2E-h3.md` and `-h4.md`,
TransDigm, as of 30 September 2024, the 2026-11-13 Sol runs) are the only real handoffs read.
"""

from pathlib import Path

import pytest

from deploy_workflow import method_scripts as ms
from deploy_workflow import method_scripts_completeness as mc

ROOT = Path(__file__).resolve().parents[1]
ESG = ROOT / "tests/fixtures/esg"


def complete(module: str, text: str) -> list[ms.Outcome]:
    return [o for o in ms.shared(module, text) if o.script == mc.COMPLETENESS]


def statuses(module: str, text: str) -> dict[tuple[str, str], str]:
    return {(o.register, o.figure): o.status for o in complete(module, text)}


# --- completeness_check.py ----------------------------------------------------------------------

# CP-2E's T2F.4 and T2F.5 with every column its Output profile declares (SKILL.md, CP-2E profile):
# T2F.4 Metric; Amount; Formula / Source; Status; Credit Implication; Source Trace.
# T2F.5 Sensitivity; Formula; Source Inputs; Estimated Cash Impact; FCF / Liquidity Implication;
# Status; Source Trace.
T2F4 = """### T2F.4 - Unhedged Exposure Table

| Metric | Amount | Formula / Source | Status | Credit Implication | Source Trace |
|---|---|---|---|---|---|
| Total debt | USD 2,000m | T2F.2 | Reported | Context. | S1 |
| Gross floating-rate debt | USD 800m | T2F.2 | Reported | Context. | S1 |

"""
T2F5 = """### T2F.5 - Rate Sensitivity Table

| Sensitivity | Formula | Source Inputs | Estimated Cash Impact | FCF / Liquidity Implication \
| Status | Source Trace |
|---|---|---|---|---|---|---|
| +100 bps cash-interest impact | Unhedged x 1% | T2F.4 | USD 5.0m | Small. | Calculated | S1 |

"""
SHELL = "---\nmodule_id: CP-2E\n---\n\n## Findings\n\n{}## Calculations\n\n## Gaps\n"


def cp2e(*registers: str) -> str:
    return SHELL.format("".join(registers))


def test_the_retained_cp2e_handoffs_are_not_sent_back():
    """Real: both retained CP-2E handoffs (TransDigm, 2026-11-13 Sol runs) write every declared
    column of every in-scope register. The method's own CLI run on them (2026-11-15) reported 7
    placeholder cells in h3 (T2F.3 row 11, T2F.5 row 5, T2F.6 rows 1 to 4, T2G.4 row 7) and none in
    h4: here they are noted, never sent back."""
    for name, noted in (
        ("CP-2E-h3.md", {"T2F.3", "T2F.5", "T2F.6", "T2G.4"}),
        ("CP-2E-h4.md", set()),
    ):
        text = (ESG / name).read_text(encoding="utf-8")
        assert ms.shared_issues("CP-2E", text) == (), name
        outcomes = complete("CP-2E", text)
        assert {o.register for o in outcomes if o.status == "noted"} == noted, name
        cut = {o.register for o in outcomes if "not required in this transport" in o.reason}
        assert cut == {"T2F.2", "T2F.8", "T2F.9"}, name  # CPOS_REGISTER_SCOPE.md § CP-2E
        columns = {o.register for o in outcomes if o.figure == "columns" and o.status == "agreed"}
        assert len(columns) == 14, name  # 17 declared, less the three cut


def test_the_h3_placeholder_count_is_the_scripts_own():
    text = (ESG / "CP-2E-h3.md").read_text(encoding="utf-8")
    t2f6 = [o for o in complete("CP-2E", text) if o.register == "T2F.6" and o.status == "noted"]
    assert "row 4" in t2f6[0].reason and "row 5" not in t2f6[0].reason


def test_the_declared_columns_pass():
    assert statuses("CP-2E", cp2e(T2F4, T2F5))[("T2F.4", "columns")] == "agreed"
    assert ms.shared_issues("CP-2E", cp2e(T2F4, T2F5)) == ()


@pytest.mark.parametrize(
    ("old", "new"),
    [
        # emphasis, code, case
        ("| Metric | Amount |", "| **Metric** | `AMOUNT` |"),
        # a unit in the header
        ("| Amount |", "| Amount (USD m) |"),
        # spacing and the joined name written as two columns
        ("| Formula / Source | Status |", "| Formula | Source | Status |"),
        # `_`, hyphen, plural
        ("| Source Trace |", "| Source_Trace |"),
        ("| Credit Implication |", "| Credit-Implications |"),
        # a column the method does not declare (the transport's Source column), at either end
        ("| Metric |", "| Source | Metric |"),
        ("| Source Trace |", "| Source Trace | Note |"),
        # columns in another order
        ("| Metric | Amount |", "| Amount | Metric |"),
    ],
)
def test_a_decorated_or_rearranged_header_is_not_sent_back(old, new):
    table = T2F4.replace(old, new, 1)
    width = new.count("|") - old.count("|")
    if width:  # keep the rows as wide as the header
        table = table.replace("| S1 |\n", "| S1 |" + " x |" * width + "\n")
        table = table.replace("|---|---|---|---|---|---|", "|---" * (6 + width) + "|")
    assert ms.shared_issues("CP-2E", cp2e(table, T2F5)) == (), new


def test_a_header_joined_or_split_or_starting_with_the_name_is_read():
    # hand-worked: each declared name against the header written another valid way
    assert mc._present("currency", ["Currency and scale"])
    assert mc._present("currency and scale", ["Currency", "Scale"])
    assert mc._present("evidence/date", ["Evidence", "Date"])
    assert mc._present("principal", ["Principal amount (USD m)"])
    assert mc._present("Natural Hedge?", ["natural hedge"])
    assert mc._present("Event-Risk vs Ongoing", ["Event risk vs. ongoing"])
    assert mc._present("SPT + Test Date", ["SPT and test date"])
    assert mc._present("Reliability (audited/assured vs self-reported)", ["Reliability"])
    # but half of a joined name is not the name
    assert not mc._present("evidence/date", ["Date"])
    assert not mc._present("Estimated Cash Impact", ["Cash impact"])


def test_a_register_with_nothing_to_report_is_not_judged_by_its_columns():
    """The presence rule's form: one row `Not supplied: <reason>`, under any header."""
    gap = "### T2F.4 - Unhedged Exposure Table\n\n| Item | Value |\n| --- | --- |\n"
    gap += "| Observed | Not supplied: no floating-rate debt |\n\n"
    single = "### T2F.5 - Rate Sensitivity\n\n| Note |\n| --- |\n| [Insufficient Information] |\n\n"
    text = cp2e(gap, single)
    assert ms.shared_issues("CP-2E", text) == ()
    assert statuses("CP-2E", text)[("T2F.4", "columns")] == "not checked"


def test_a_register_written_as_rows_or_without_a_table_is_not_judged():
    rows = "### T2F.4 - Unhedged Exposure Table\n\n| Field | Value |\n| --- | --- |\n"
    rows += "| Metric | Total debt |\n| Amount | USD 2,000m |\n| Status | Reported |\n\n"
    prose = "### T2F.5 - Rate Sensitivity Table\n\nA +100 bps move costs USD 5.0m a year.\n\n"
    text = cp2e(rows, prose)
    assert ms.shared_issues("CP-2E", text) == ()
    by = statuses("CP-2E", text)
    assert by[("T2F.4", "columns")] == by[("T2F.5", "columns")] == "not checked"


def test_a_cut_register_and_a_routing_column_are_never_required():
    # T2F.2 is cut (CPOS_REGISTER_SCOPE.md § CP-2E): written with any columns, it is not judged.
    cut = "### T2F.2 - Debt & Rate Exposure Register\n\n| A |\n| --- |\n| 1 |\n\n"
    # T2F.1's `downstream_use` names receiving modules, which ROUTING_RULES forbids.
    t2f1 = "### T2F.1 - Macro source gate\n\n| source_document_id | source_document_name "
    t2f1 += "| source_quality | period | entity_covered | data_supplied | limitation |\n"
    t2f1 += (
        "|---|---|---|---|---|---|---|\n| S1 | 10-K | Primary | FY2024 | Group | Debt | None |\n\n"
    )
    text = cp2e(cut, t2f1, T2F4, T2F5)
    assert ms.shared_issues("CP-2E", text) == ()
    assert statuses("CP-2E", text)[("T2F.1", "columns")] == "agreed"


def test_a_blocked_module_owes_nothing():
    text = cp2e(T2F4.replace("| Credit Implication |", "| Other |"))
    blocked = text.replace("module_id: CP-2E", "module_id: CP-2E\nmodule_status: Blocked - gate")
    assert ms.shared_issues("CP-2E", blocked) == ()
    assert [o.status for o in complete("CP-2E", blocked)] == ["not checked"]


def test_short_registers_and_placeholders_are_noted_not_sent_back():
    # CP-2's T2.12 declares a minimum of 8 rows; three triggers and an `n/a` cell are recorded.
    t212 = "### T2.12 - Monitoring triggers\n\n| Trigger | Threshold / Signal | Why It Matters "
    t212 += "| Credit Impact | Source / Limitation |\n|---|---|---|---|---|\n"
    t212 += (
        "| Leverage | 6.0x | Cushion | Negative | S1 |\n| Coverage | n/a | Cushion | Neg | S1 |\n"
    )
    t212 += "| Liquidity | USD 1bn | Runway | Negative | S1 |\n\n"
    text = SHELL.replace("CP-2E", "CP-2").format(t212)
    assert ms.shared_issues("CP-2", text) == ()
    by = statuses("CP-2", text)
    assert by[("T2.12", "rows")] == by[("T2.12", "placeholders")] == "noted"
    assert by[("T2.12", "columns")] == "agreed"


def test_a_missing_declared_column_is_sent_back_once_per_register():
    lacking = T2F4.replace(" Credit Implication |", "").replace(" Context. |", "")
    lacking = lacking.replace("|---|---|---|---|---|---|", "|---|---|---|---|---|")
    renamed = T2F5.replace("| Estimated Cash Impact |", "| Cash impact |")
    (first, second) = ms.shared_issues("CP-2E", cp2e(lacking, renamed))
    assert first.startswith("T2F.4 lacks the method's column `Credit Implication`")
    assert second.startswith("T2F.5 lacks the method's column `Estimated Cash Impact`")
    by = statuses("CP-2E", cp2e(lacking, renamed))
    assert by[("T2F.4", "columns")] == by[("T2F.5", "columns")] == "missing"


def test_a_module_without_a_presence_check_is_noted_only():
    """CP-4C has no register-scope section and no calibration: a missing column is recorded."""
    t4e1 = "### T4E.1 - Distress gate\n\n| trigger | status |\n|---|---|\n| Default | Met |\n\n"
    text = SHELL.replace("CP-2E", "CP-4C").format(t4e1)
    assert ms.shared_issues("CP-4C", text) == ()
    assert statuses("CP-4C", text)[("T4E.1", "columns")] == "noted"


def test_modules_with_no_profile_or_no_skill():
    # CP-1's SKILL.md (caos-databricks) declares no Output profile; CP-L10 and CP-8 are sent none.
    (outcome,) = complete("CP-1", "anything")
    assert outcome.status == "not checked" and "no completeness contract" in outcome.reason
    assert complete("CP-L10", "anything") == [] and complete("CP-8", "anything") == []


def test_every_module_sent_a_skill_reads_its_own_profile():
    """Each sent SKILL.md's profile is the module's own (no other module's registers)."""
    from deploy_workflow.owners.cpos_launch_methods import METHODS

    for module in METHODS:
        found = mc.contract(module) if mc.skill(module) else "none"
        if module in ("CP-1", "CP-L10", "CP-8"):
            assert isinstance(found, str), module
            continue
        assert isinstance(found, dict) and found["registers"], module


def test_a_register_split_over_two_tables_or_after_prose_is_read_whole():
    split = "### T2F.4 - Unhedged Exposure Table\n\nThe exposure, then its trace.\n\n"
    split += "| Metric | Amount | Formula / Source | Status |\n|---|---|---|---|\n"
    split += "| Total debt | USD 2,000m | T2F.2 | Reported |\n\n"
    split += "| Metric | Credit Implication | Source Trace |\n|---|---|---|\n"
    split += "| Total debt | Context. | S1 |\n\n"
    assert ms.shared_issues("CP-2E", cp2e(split, T2F5)) == ()
    assert statuses("CP-2E", cp2e(split, T2F5))[("T2F.4", "columns")] == "agreed"
    # A table after the next heading is not this register's.
    later = split.replace("\n| Metric | Credit", "\n### Notes\n\n| Metric | Credit")
    assert statuses("CP-2E", cp2e(later, T2F5))[("T2F.4", "columns")] == "missing"


def test_a_dotted_declared_name_matches_its_spelled_forms():
    # CP-DR's TDR.5 declares `peer_id.dimension` (PEER_PACK_BLOCK names it as the method does).
    for header in ("peer_id.dimension", "Peer ID.dimension", "peer id dimension"):
        assert mc._present("peer_id.dimension", [header]), header
