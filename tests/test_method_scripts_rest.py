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


# --- CP-4C: recovery_waterfall.py on T4E.5 and T4E.6 ---------------------------------------------

# SYNTHETIC, USD m, one entity. Worked by hand, each row its own step (allocation = the lesser of
# claim and available value, residual = available - allocation):
# Base: 1,000 -> Admin 100 (100, 900) -> TLB 600 (600, 300) -> Notes 500 (300, 0) -> Sub 200
#       (0, 0). Fulcrum: Senior notes (300 of 500, the first partial recovery).
# Low:  600 -> Admin 100 (100, 500) -> TLB 600 (500, 0) -> Notes 500 (0, 0). Fulcrum: TLB.
T4E5_HEAD = (
    "| scenario | entity | available value | priority claim | allocation | residual "
    "| currency and scale | legal evidence ID |\n|---|---|---|---|---|---|---|---|\n"
)
BASE_ROWS = [
    ("Base", "HoldCo", "1,000", "Admin and DIP: 100", "100", "900"),
    ("Base", "HoldCo", "900", "Senior secured TLB: 600", "600", "300"),
    ("Base", "HoldCo", "300", "Senior notes: 500", "300", "0"),
    ("Base", "HoldCo", "0", "Subordinated notes: 200", "0", "0"),
]
LOW_ROWS = [
    ("Low", "HoldCo", "600", "Admin and DIP: 100", "100", "500"),
    ("Low", "HoldCo", "500", "Senior secured TLB: 600", "500", "0"),
    ("Low", "HoldCo", "0", "Senior notes: 500", "0", "0"),
]
T4E6 = """### T4E.6 - Fulcrum

| scenario/EV range | last covered class | first impaired class | fulcrum class/range | note |
|---|---|---|---|---|
| Base (EV 1,000) | Senior secured TLB | Senior notes | {base} | Valuation. |
| Low (EV 600) | Admin and DIP | Senior secured TLB | {low} | Valuation. |

"""


def t4e5(rows=None) -> str:
    rows = BASE_ROWS + LOW_ROWS if rows is None else rows
    body = "".join(f"| {' | '.join(r)} | USD m | L1 |\n" for r in rows)
    return "### T4E.5 - Waterfall allocation\n\n" + T4E5_HEAD + body + "\n"


def cp4c(t4e5_text: str, base="Senior notes", low="Senior secured TLB") -> str:
    shell = "---\nmodule_id: CP-4C\n---\n\n## Findings\n\n{}## Calculations\n\n## Gaps\n"
    return shell.format(t4e5_text + T4E6.format(base=base, low=low))


def cp4c_run(text: str) -> list[ms.Outcome]:
    return list(ms.run("CP-4C", text))


def by_status(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for o in cp4c_run(text):
        out.setdefault(o.status, []).append(o.figure)
    return out


def test_cp4c_all_right():
    found = by_status(cp4c(t4e5()))
    assert set(found) == {"agreed"}
    assert len(found["agreed"]) == 2 * 7 + 2  # allocation and residual per row, two fulcra
    assert ms.issues("CP-4C", cp4c(t4e5())) == ()


def swap(rows, at, column, value):
    rows = [list(r) for r in rows]
    rows[at][column] = value
    return [tuple(r) for r in rows]


@pytest.mark.parametrize(
    ("rows", "why"),
    [
        # rounded inputs: 999.6 shown as 1,000 with 899.6 left; one unit of the last place
        (swap(BASE_ROWS, 0, 5, "899.6"), "rounding"),
        # an allocation written as an outflow, as the value allocation chart writes it
        (swap(BASE_ROWS, 1, 4, "-600"), "outflow sign"),
        (swap(BASE_ROWS, 1, 4, "(600)"), "bracketed outflow"),
        # decorated cells and a unit in the cell itself
        (swap(BASE_ROWS, 1, 4, "**USD 600m**"), "decorated"),
        # a secured claim limited by collateral: the secured part, then the deficiency later
        (
            [
                ("Base", "HoldCo", "1,000", "TLB secured part: 400", "400", "600"),
                ("Base", "HoldCo", "600", "Senior notes: 500", "500", "100"),
                ("Base", "HoldCo", "100", "TLB deficiency: 200", "100", "0"),
            ],
            "collateral split",
        ),
        # claims ranking equally in one row
        ([("Base", "HoldCo", "1,000", "TLB and RCF: 1,500", "1,000", "0")], "pari passu"),
        # another entity's pool: its own rows
        (BASE_ROWS + [("Base", "OpCo", "250", "Trade claims: 300", "250", "0")], "entity"),
        # an allocation the governing evidence sets otherwise, with its reason
        (swap(BASE_ROWS, 2, 4, "250 (settlement)"), "governing evidence"),
        # a gap
        (swap(BASE_ROWS, 2, 4, "Not supplied: plan not filed"), "gap"),
    ],
)
def test_cp4c_correct_but_unusual_waterfalls_are_not_sent_back(rows, why):
    text = cp4c(t4e5(rows), base="Not supplied: see T4E.5", low="Not supplied: no low case")
    assert ms.issues("CP-4C", text) == (), why


@pytest.mark.parametrize(
    ("rows", "fulcrum"),
    [
        # collateral split: the deficiency recovers 100 of 200, the first partial step
        (
            [
                ("Base", "HoldCo", "1,000", "TLB secured part: 400", "400", "600"),
                ("Base", "HoldCo", "600", "Senior notes: 500", "500", "100"),
                ("Base", "HoldCo", "100", "TLB deficiency: 200", "100", "0"),
            ],
            "TLB deficiency",
        ),
        # pari passu in one row: 1,000 of 1,500
        ([("Base", "HoldCo", "1,000", "TLB and RCF: 1,500", "1,000", "0")], "TLB and RCF"),
    ],
)
def test_cp4c_fulcrum_of_a_split_or_shared_claim(rows, fulcrum):
    text = cp4c(t4e5(rows), base=fulcrum, low="Not supplied: no low case")
    assert {o.figure: o.status for o in cp4c_run(text)}["Fulcrum (Base)"] == "agreed"


def test_cp4c_fulcrum_written_with_a_note_or_as_a_range():
    for cell in ("Senior notes (60% recovery)", "Claim: Senior notes - partial"):
        found = {o.figure: o.status for o in cp4c_run(cp4c(t4e5(), base=cell))}
        assert found["Fulcrum (Base)"] == "agreed", cell
    found = {o.figure: o.status for o in cp4c_run(cp4c(t4e5(), base="TLB to Senior notes"))}
    assert found["Fulcrum (Base)"] == "not checked"
    # none covered partly: every class whole, value left -> `None`
    whole = [("Up", "HoldCo", "2,000", "TLB: 600", "600", "1,400")]
    text = cp4c(t4e5(whole)).replace("| Base (EV 1,000) |", "| Up |")
    found = {
        o.figure: o.status
        for o in cp4c_run(text.replace("| Senior notes | Valuation", "| None | Valuation"))
    }
    assert found["Fulcrum (Up)"] == "agreed"


def test_cp4c_no_fulcrum_check_across_entities_or_a_broken_chain():
    entity = BASE_ROWS + [("Base", "OpCo", "250", "Trade claims: 300", "250", "0")]
    found = {o.figure: o for o in cp4c_run(cp4c(t4e5(entity)))}
    assert found["Fulcrum (Base)"].status == "not checked"
    assert "more than one entity" in found["Fulcrum (Base)"].reason
    broken = swap(BASE_ROWS, 2, 2, "350")  # available 350 after a residual of 300: a new pool
    broken = swap(broken, 2, 4, "350")  # notes then take 350 of 500 (lesser of), residual 0
    broken = swap(broken, 2, 5, "0")
    found = {o.figure: o for o in cp4c_run(cp4c(t4e5(broken)))}
    assert found["Fulcrum (Base)"].status == "not checked"
    assert ms.issues("CP-4C", cp4c(t4e5(broken))) == ()


def test_cp4c_unread_inputs_are_not_checked_never_zero():
    nameless = swap(BASE_ROWS, 2, 3, "Senior notes")  # no claim amount
    found = {o.figure: o for o in cp4c_run(cp4c(t4e5(nameless)))}
    assert found["Row: Senior notes (Base)"].status == "not checked"
    assert found["Fulcrum (Base)"].status == "not checked"
    assert ms.issues("CP-4C", cp4c(t4e5(nameless))) == ()
    euro = swap(BASE_ROWS, 1, 4, "EUR 600m")
    assert ms.issues("CP-4C", cp4c(t4e5(euro), low="x")) == ()
    (only,) = cp4c_run("no register here")
    assert only.status == "not checked" and "no T4E.5" in only.reason


@pytest.mark.parametrize(
    ("rows", "base", "figure", "recomputed"),
    [
        (swap(BASE_ROWS, 1, 4, "550"), "Senior notes", "Allocation: Senior secured TLB", 600),
        (swap(BASE_ROWS, 1, 4, "700"), "Senior notes", "Allocation: Senior secured TLB", 600),
        (swap(BASE_ROWS, 2, 5, "50"), "Senior notes", "Residual: Senior notes", 0),
    ],
)
def test_cp4c_wrong_steps_are_sent_back(rows, base, figure, recomputed):
    issues = ms.issues("CP-4C", cp4c(t4e5(rows + LOW_ROWS), base=base))
    assert len(issues) == 1 and f"`{figure} (Base, HoldCo)`" in issues[0]
    assert f"recomputes {recomputed} USD m" in issues[0]


def test_cp4c_a_wrong_fulcrum_is_sent_back():
    (issue,) = ms.issues("CP-4C", cp4c(t4e5(), base="Senior secured TLB"))
    assert "`Fulcrum (Base)`" in issue and "recomputes Senior notes" in issue


def test_cp4c_note_fits_and_names_the_rows():
    assert "`<class>: <amount>`" in ms.NOTES["CP-4C"] and len(ms.NOTES["CP-4C"]) < 1_300


def test_cp4c_a_trailing_equity_row_and_units_in_the_headers():
    equity = BASE_ROWS + [("Base", "HoldCo", "0", "Equity", "0", "0")]
    found = {o.figure: o.status for o in cp4c_run(cp4c(t4e5(equity)))}
    assert found["Fulcrum (Base)"] == "agreed"  # the seniors' fulcrum stands
    assert found["Row: Equity (Base)"] == "not checked"
    head = (
        "| Scenario | Entity | Available value (USD m) | Priority claim | Allocation (USD m) "
        "| Residual (USD m) | Legal evidence ID |\n|---|---|---|---|---|---|---|\n"
    )
    body = "".join(f"| {' | '.join(r)} | L1 |\n" for r in BASE_ROWS)
    text = cp4c("### T4E.5 - Waterfall\n\n" + head + body + "\n", low="x")
    assert ms.issues("CP-4C", text) == ()
    assert {o.status for o in cp4c_run(text) if o.figure.startswith("Allocation")} == {"agreed"}


# --- CP-1C: peer_statistics.py on T4.6 and T4.10 -------------------------------------------------

# SYNTHETIC. EBITDA margin, peers A to E Comparable (18.0, 20.0, 24.0, 26.0, 30.0 %), F Not
# Comparable (15.0), the borrower 22.0. N = 5: average 118 / 5 = 23.6, median 24.0, min 18.0,
# max 30.0. EV/EBITDA, peers A to D (9.0, 10.0, 12.0, 14.0 x): N = 4, median (10 + 12) / 2 = 11.0,
# min 9.0, max 14.0, no average (the method's gate is 5). T4.10 on EBITDA USD 500m: Low 9.0 x 500
# = 4,500, Median 11.0 x 500 = 5,500, High 14.0 x 500 = 7,000.
T43 = """### T4.3 - Operating benchmark

| Entity | Revenue | Rev Growth | Gross Margin | EBITDA | EBITDA Margin | EBIT Margin | Period \
| Currency | Calc Status | Comp Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Borrower Co (borrower) | 1,000 | 5.0% | 40.0% | 220 | 22.0% | 15.0% | FY2024 | USD | Reported \
| Comparable |
| Peer A | 900 | 4.0% | 38.0% | 162 | 18.0% | 12.0% | FY2024 | USD | Reported | Comparable |
| Peer B | 800 | 3.0% | 39.0% | 160 | 20.0% | 13.0% | FY2024 | USD | Reported | Comparable |
| Peer C | 1,100 | 6.0% | 41.0% | 264 | 24.0% | 16.0% | FY2024 | USD | Calculated | Comparable \
with Limitations |
| Peer D | 1,200 | 7.0% | 42.0% | 312 | 26.0% | 17.0% | FY2024 | USD | Reported | Comparable |
| Peer E | 1,000 | 8.0% | 45.0% | 300 | 30.0% | 20.0% | FY2024 | USD | Reported | Comparable |
| Peer F | 700 | 1.0% | 30.0% | 105 | 15.0% | 9.0% | FY2024 | USD | Reported | Not Comparable |

"""
T48 = """### T4.8 - Trading comps

| Entity | Mkt Cap | Mkt Cap Date | EV | EV/Rev | EV/EBITDA | Period Used | Metric Def \
| Comp Status | Source |
|---|---|---|---|---|---|---|---|---|---|
| Peer A | 1,000 | 2024-09-30 | 1,458 | 1.6x | 9.0x | LTM | Reported | Comparable | S1 |
| Peer B | 1,100 | 2024-09-30 | 1,600 | 2.0x | 10.0x | LTM | Reported | Comparable | S1 |
| Peer C | 2,500 | 2024-09-30 | 3,168 | 2.9x | 12.0x | LTM | Reported | Comparable | S1 |
| Peer D | 3,500 | 2024-09-30 | 4,368 | 3.6x | 14.0x | LTM | Reported | Comparable | S1 |

"""
T46 = """### T4.6 - Summary statistics

| Metric | Borrower Value | Peer Avg | Median | Min | Max | Q1 | Q3 | N | Borrower Position |
|---|---|---|---|---|---|---|---|---|---|
| EBITDA Margin | 22.0% | {avg} | {median} | 18.0% | 30.0% | 20.0% | 26.0% | {n} | Below median |
| EV/EBITDA | — | Not calculable (N=4) | 11.0x | 9.0x | 14.0x | 9.75x | 12.5x | 4 | n/a |

"""
T410 = """### T4.10 - Implied enterprise value

| Method | Multiple Source/Value | Borrower Metric/Period | Low | Median | High | Calc Status \
| Limitations |
|---|---|---|---|---|---|---|---|
| EV/EBITDA trading comps | T4.6 | EBITDA FY2024 USD 500m | USD 4,500m | USD 5,500m | {high} \
| Calculated | Indicative only. |

"""


def cp1c(t46=None, extra="", high="USD 7,000m", **cells) -> str:
    stats = {"avg": "23.6%", "median": "24.0%", "n": "5"} | cells
    body = T43 + T48 + (t46 if t46 is not None else T46.format(**stats)) + T410.format(high=high)
    return f"---\nissuer_name: Borrower Co\nmodule_id: CP-1C\n---\n\n## Findings\n\n{body}{extra}"


def cp1c_by(text: str) -> dict[str, ms.Outcome]:
    return {o.figure: o for o in ms.run("CP-1C", text)}


def test_cp1c_all_right():
    found = cp1c_by(cp1c())
    margin = {k: o.status for k, o in found.items() if k.endswith("EBITDA Margin")}
    assert margin == dict.fromkeys(
        [f"Peer {s}: EBITDA Margin" for s in ("Avg", "Median", "Min", "Max")], "agreed"
    ) | dict.fromkeys(["Peer Q1: EBITDA Margin", "Peer Q3: EBITDA Margin"], "not checked")
    assert "quantile convention" in found["Peer Q1: EBITDA Margin"].reason
    assert found["Peer Avg: EV/EBITDA"].status == "agreed"  # Not calculable at N = 4
    assert found["Peer Median: EV/EBITDA"].status == "agreed"
    for case in ("Low", "Base", "High"):
        assert found[f"Implied EV {case}: EV/EBITDA trading comps"].status == "agreed", case
    assert ms.issues("CP-1C", cp1c()) == ()


def test_cp1c_the_outlier_free_version_is_read_when_n_says_so():
    # T4.7 flags Peer E (30.0%): without it N = 4, median (20 + 24) / 2 = 22.0, no average.
    t47 = "### T4.7 - Outliers\n\n| Entity | Metric | Value |\n|---|---|---|\n"
    t47 += "| Peer E | EBITDA Margin | 30.0% |\n\n"
    text = cp1c(avg="Not calculable", median="22.0%", n="4", extra=t47)
    found = cp1c_by(text)
    assert found["Peer Median: EBITDA Margin"].status == "agreed"
    assert found["Peer Max: EBITDA Margin"].status == "disagreed"  # 30.0 stated; 26.0 without E
    # with N = 5 the full set is read, and the stated 30.0 maximum agrees
    assert ms.issues("CP-1C", cp1c(extra=t47)) == ()


@pytest.mark.parametrize(
    ("old", "new", "why"),
    [
        (
            "| Peer A | 900 | 4.0% | 38.0% | 162 | 18.0% |",
            "| Peer A | 900 | 4.0% | 38.0% | 162 | 18.04% |",
            "an input shown to two places",
        ),
        ("| Borrower Co (borrower) |", "| Borrower Co |", "the borrower named as the issuer"),
        ("| Borrower Co (borrower) |", "| The Company |", "the borrower found by its value"),
        ("| EBITDA Margin |", "| **EBITDA margin** |", "decorated metric"),
        ("| 23.6% |", "| 23.60% |", "more places"),
        (
            "| USD | Reported | Not Comparable |\n",
            "| USD | Provisional | Comparable |\n",
            "Peer F a provisional figure, kept out of aggregates",
        ),
        ("| 5 | Below median |", "| 6 | Below median |", "N from another peer set: not checked"),
    ],
)
def test_cp1c_correct_but_unusual_handoffs_are_not_sent_back(old, new, why):
    text = cp1c()
    assert old in text, why
    assert ms.issues("CP-1C", text.replace(old, new, 1)) == (), why


def test_cp1c_the_skills_joined_layout_and_a_joined_column():
    joined = """### T4.6 - Summary statistics

| Metric | Borrower Value | Peer Avg/Median/Min/Max | Q1/Q3 | N | Borrower Position |
|---|---|---|---|---|---|
| EBITDA Margin | 22.0% | 23.6% / 24.0% / 18.0% / 30.0% | 20.0% / 26.0% | 5 | Below |
| Net Leverage | 4.0x | n.m. / 4.5x / 3.5x / 5.5x | — | 3 | Below |

"""
    t45 = """### T4.5 - Credit metrics

| Entity | Total/Net/Sr Sec Leverage | Int/Adj Int Coverage | FFO/Debt | Liquidity | Period \
| Currency | Calc/Comp Status |
|---|---|---|---|---|---|---|---|
| Peer A | 4.0x / 3.5x / 2.0x | 3.0x / 3.2x | 20.0% | 300 | FY2024 | USD | Reported / Comparable |
| Peer B | 5.0x / 4.5x / 3.0x | 2.5x / 2.7x | 15.0% | 200 | FY2024 | USD | Reported / Comparable |
| Peer C | 6.0x / 5.5x / 4.0x | 2.0x / 2.2x | 10.0% | 100 | FY2024 | USD | Reported / Comparable |

"""
    # Net leverage, N = 3: median 4.5, min 3.5, max 5.5, no average (gate 5).
    found = cp1c_by(cp1c(t46=joined + t45))
    for stat in ("Avg", "Median", "Min", "Max"):
        assert found[f"Peer {stat}: Net Leverage"].status == "agreed", stat
        assert found[f"Peer {stat}: EBITDA Margin"].status == "agreed", stat


def test_cp1c_amounts_and_unread_cells_are_not_checked():
    t46 = T46.format(avg="23.6%", median="24.0%", n="5") + (
        "| Revenue | 1,000 | 940 | 900 | 800 | 1,200 | — | — | 5 | Above |\n"
    )
    text = cp1c(t46=t46.replace("|\n\n|", "|\n|"))
    found = cp1c_by(text)
    assert found["Peer Median: Revenue"].status == "not checked"  # no unit to compare in
    assert ms.issues("CP-1C", text) == ()
    (only,) = ms.run("CP-1C", "nothing")
    assert only.status == "not checked"


@pytest.mark.parametrize(
    ("cells", "figure", "recomputed"),
    [
        ({"median": "22.0%"}, "Peer Median: EBITDA Margin", "0.24"),
        ({"avg": "24.6%"}, "Peer Avg: EBITDA Margin", "0.236"),
    ],
)
def test_cp1c_a_wrong_statistic_is_sent_back(cells, figure, recomputed):
    (issue,) = ms.issues("CP-1C", cp1c(**cells))
    assert f"`{figure}`" in issue


def test_cp1c_an_average_below_the_gate_is_sent_back():
    text = cp1c().replace("| Not calculable (N=4) |", "| 11.25x |")
    (issue,) = ms.issues("CP-1C", text)
    assert "`Peer Avg: EV/EBITDA`" in issue and "Not Calculable" in issue


def test_cp1c_a_wrong_implied_ev_is_sent_back():
    (issue,) = ms.issues("CP-1C", cp1c(high="USD 7,500m"))
    assert "`Implied EV High: EV/EBITDA trading comps`" in issue and "recomputes 7000" in issue


def test_cp1c_a_peer_gap_or_a_noted_status_is_read_as_the_method_reads_it():
    # Peer F becomes Comparable but states no margin: left out, never zero (N stays 5).
    gap = "| Peer F | 700 | 1.0% | 30.0% | 105 | Not supplied: not disclosed | 9.0% | FY2024 | USD "
    gap += "| Reported | Comparable |\n"
    text = cp1c().replace(
        "| Peer F | 700 | 1.0% | 30.0% | 105 | 15.0% | 9.0% | FY2024 | USD | Reported "
        "| Not Comparable |\n",
        gap,
    )
    text = text.replace("| Comparable |\n| Peer B", "| Comparable (size gap) |\n| Peer B")
    statuses = {o.figure: o.status for o in ms.run("CP-1C", text) if "Margin" in o.figure}
    assert {v for k, v in statuses.items() if " Q" not in k} == {"agreed"}


# --- CP-2H: covenant_headroom.py (trigger_headroom) on T2R.4 -------------------------------------

# SYNTHETIC, worked by hand. Maximum 6.0x against 5.2x: 6.0 - 5.2 = 0.8, Compliant. Minimum 2.0x
# against 1.8x: 1.8 - 2.0 = -0.2, Breached. Range 5.0x-5.5x, maximum, against 5.2x: 5.0 - 5.2 =
# -0.2 to the binding (lower) bound, 5.5 - 5.2 = 0.3 to the upper; Breached against the binding
# bound. Two cases 5.2x / 6.4x against a maximum 6.0x: 0.8 Compliant, -0.4 Breached.
T2R4_HEAD = (
    "| agency | rating type | trigger direction | metric | threshold | case/period value "
    "| headroom | status |\n|---|---|---|---|---|---|---|---|\n"
)
T2R4_ROWS = [
    "| Moody's | CFR | maximum | Debt/EBITDA | 6.0x | Base FY2025: 5.2x | 0.8x | Compliant |",
    "| S&P | ICR | minimum | EBITDA/interest | 2.0x | Base FY2025: 1.8x | -0.2x | Breached |",
    (
        "| Fitch | IDR | maximum | Net leverage | 5.0x-5.5x | 5.2x | -0.2x / 0.3x "
        "| Breached (lower bound) |"
    ),
    (
        "| Moody's | CFR | maximum | Gross leverage | 6.0x | 5.2x / 6.4x | 0.8x / -0.4x "
        "| Compliant / Breached |"
    ),
]


def cp2h(*rows: str) -> str:
    body = "\n".join(rows or T2R4_ROWS)
    return f"## Findings\n\n### T2R.4 - Quantitative triggers\n\n{T2R4_HEAD}{body}\n\n## Gaps\n"


def cp2h_by(text: str) -> dict[str, str]:
    return {o.figure: o.status for o in ms.run("CP-2H", text)}


def test_cp2h_all_right():
    found = cp2h_by(cp2h())
    assert set(found.values()) == {"agreed"}, found
    assert len(found) == 2 * 5  # headroom and status, one row each and two cases in the last
    assert ms.issues("CP-2H", cp2h()) == ()


@pytest.mark.parametrize(
    ("old", "new", "why"),
    [
        ("| maximum | Debt/EBITDA |", "| Maximum (leverage ceiling) | Debt/EBITDA |", "noted"),
        ("| 6.0x | Base FY2025: 5.2x |", "| > 6.0x | Base FY2025E: 5.2x |", "comparator, year"),
        ("| 0.8x | Compliant |", "| 0.76x | Compliant |", "an unrounded input"),
        ("| -0.2x | Breached |", "| (0.2x) | Breach (point-in-time) |", "brackets, words"),
        ("| -0.2x / 0.3x |", "| 0.3x |", "one bound's distance of a range"),
        ("| maximum | Debt/EBITDA |", "| downgrade | Debt/EBITDA |", "no ceiling or floor"),
        ("| 6.0x | Base FY2025: 5.2x |", "| Aggressive financial policy | Base |", "qualitative"),
        ("| Compliant |\n", "| Watch |\n", "a status the script has no word for"),
    ],
)
def test_cp2h_correct_but_unusual_rows_are_not_sent_back(old, new, why):
    text = cp2h()
    assert old in text, why
    assert ms.issues("CP-2H", text.replace(old, new, 1)) == (), why


def test_cp2h_status_at_the_rounding_edge_is_not_decided():
    # 6.0x against 5.97x shown as 6.0x: headroom 0.0 recomputed, Breached stated from 6.03x
    row = "| Moody's | CFR | maximum | Debt/EBITDA | 6.0x | 6.0x | 0.0x | Breached |"
    assert cp2h_by(cp2h(row))["Status: Debt/EBITDA"] == "not checked"


@pytest.mark.parametrize(
    ("old", "new", "figure"),
    [
        ("| -0.2x | Breached |", "| 0.2x | Breached |", "Headroom: EBITDA/interest"),
        ("| -0.2x | Breached |", "| -0.2x | Compliant |", "Status: EBITDA/interest"),
        ("| 0.8x / -0.4x |", "| 0.8x / 0.4x |", "Headroom: Gross leverage (case 2)"),
    ],
)
def test_cp2h_a_wrong_headroom_or_status_is_sent_back(old, new, figure):
    (issue,) = ms.issues("CP-2H", cp2h().replace(old, new, 1))
    assert f"`{figure}`" in issue


def test_cp2h_a_range_compares_each_stated_bound():
    # 5.0x-5.5x against 5.2x: -0.2 to the lower bound, 0.3 to the upper. A wrong second figure
    # (0.7; tolerance 0.1 + the inputs' rounding 0.1) is a disagreement, not ignored.
    text = cp2h().replace("| -0.2x / 0.3x |", "| -0.2x / 0.7x |")
    (issue,) = ms.issues("CP-2H", text)
    assert "`Headroom: Net leverage`" in issue
