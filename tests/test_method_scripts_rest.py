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
        gaps = {o.register for o in outcomes if "states a gap" in o.reason}
        assert len(columns | gaps) == 14, name  # 17 declared, less the three cut
        assert gaps <= {"T2G.5"}, name  # h3's T2G.5: every row `Not supplied` (no linked debt)


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
    # Margins 18, 20, 24, 26, 30: inclusive Q1 sits at position (5 - 1) x 0.25 = 1, so 20.0, and
    # Q3 at position 3, so 26.0 (owner, 2026-11-15: "Inclusive").
    assert margin == dict.fromkeys(
        [f"Peer {s}: EBITDA Margin" for s in ("Avg", "Median", "Min", "Max", "Q1", "Q3")], "agreed"
    )
    # Multiples 9, 10, 12, 14: Q1 at position 0.75, 9 + 0.75 x 1 = 9.75; Q3 at 2.25,
    # 12 + 0.25 x 2 = 12.5.
    assert found["Peer Q1: EV/EBITDA"].status == found["Peer Q3: EV/EBITDA"].status == "agreed"
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


# --- CP-1B: credit_metrics.py (growth) on T4.6 and T4.4 ------------------------------------------

# SYNTHETIC, USD m, worked by hand: Revenue 2,100 -> 2,250: 2,250 / 2,100 - 1 = 7.142857% (7.1%).
# EBITDA 410 -> 380: 380 / 410 - 1 = -7.317% (-7.3%). FCF 0 -> 50: no percentage (zero prior).
T46_1B = """### T4.6 - Variance register

| Metric | Comparison Basis | Prior Value | Current Value | Abs Change | % Change | Mgmt Driver \
| Analyst Driver | Credit Implication |
|---|---|---|---|---|---|---|---|---|
| Revenue | YoY | USD 2,100m | USD 2,250m | USD 150m | {revenue} | Price | Volume | Positive |
| EBITDA | YoY | 410 | 380 | -30 | {ebitda} | Costs | Mix | Negative |
| FCF | YoY | 0 | 50 | 50 | {fcf} | WC | WC | Neutral |
| EBITDA margin | YoY | 19.5% | 16.9% | -2.6pp | {margin} | Costs | Mix | Negative |

"""
T44_1B = """### T4.4 - Performance table

| Line Item | FY2022 | FY2023 | FY2024 | YoY Change (Abs) | YoY Change (%) | Analyst Note |
|---|---|---|---|---|---|---|
| Revenue | 1,900 | 2,100 | 2,250 | 150 | {yoy} | Growth. |
| Net Income | 10 | -20 | 15 | 35 | n.m. | Swing. |

"""


def cp1b(t44: str | None = None, **cells: str) -> str:
    stated = {"revenue": "7.1%", "ebitda": "-7.3%", "fcf": "n.m.", "margin": "-2.6pp"} | cells
    t46 = T46_1B.format(**{k: v for k, v in stated.items() if k != "yoy"})
    t44 = T44_1B.format(yoy=stated.get("yoy", "7.1%")) if t44 is None else t44
    return f"## Findings\n\n{t46}{t44}## Gaps\n"


def cp1b_by(text: str) -> dict[tuple[str, str], str]:
    return {(o.register, o.figure): o.status for o in ms.run("CP-1B", text)}


def test_cp1b_all_right():
    found = cp1b_by(cp1b())
    assert found[("T4.6", "% Change: Revenue")] == "agreed"
    assert found[("T4.6", "% Change: EBITDA")] == "agreed"
    assert found[("T4.6", "% Change: FCF")] == "agreed"  # n.m. on a zero prior
    assert found[("T4.6", "% Change: EBITDA margin")] == "not checked"  # points
    assert found[("T4.4", "% Change: Revenue")] == "agreed"  # FY2024 against FY2023
    assert found[("T4.4", "% Change: Net Income")] == "not checked"  # negative prior
    assert ms.issues("CP-1B", cp1b()) == ()
    assert "CP-1B" not in ms.NOTES  # earnings_update has no room for the note


@pytest.mark.parametrize(
    ("cells", "why"),
    [
        ({"revenue": "7.14%"}, "more places"),
        ({"revenue": "+7.1%"}, "a plus sign"),
        ({"revenue": "7.1"}, "a bare figure above 1 in a % column"),
        ({"ebitda": "(7.3%)"}, "brackets"),
        ({"ebitda": "-0.073"}, "a decimal: not read"),
        ({"margin": "-13.3%"}, "a margin's relative change: not compared"),
        ({"fcf": "Not meaningful (zero base)"}, "a null word with its reason"),
    ],
)
def test_cp1b_correct_but_unusual_cells_are_not_sent_back(cells, why):
    assert ms.issues("CP-1B", cp1b(**cells)) == (), why


def test_cp1b_t44_period_pairs():
    # columns in descending order, and a quarter layout: the latest year against a year earlier
    desc = (
        "### T4.4 - Performance\n\n| Line Item | FY2024 | FY2023 | YoY Change (%) |\n"
        "|---|---|---|---|\n| Revenue | 2,250 | 2,100 | 7.1% |\n\n"
    )
    quarters = (
        "### T4.4 - Performance\n\n| Line Item | Q3 2023 | Q2 2024 | Q3 2024 | YoY Change (%) |\n"
        "|---|---|---|---|---|\n| Revenue | 500 | 520 | 550 | 10.0% |\n\n"  # 550 / 500 - 1 = 10%
    )
    for t44 in (desc, quarters):
        assert cp1b_by(cp1b(t44=t44))[("T4.4", "% Change: Revenue")] == "agreed"
    lone = quarters.replace("Q3 2023", "Q1 2024")  # no Q3 2023: no pair
    assert cp1b_by(cp1b(t44=lone))[("T4.4", "% Change: all")] == "not checked"


@pytest.mark.parametrize(
    ("cells", "figure"),
    [
        ({"revenue": "8.1%"}, "% Change: Revenue"),
        ({"ebitda": "7.3%"}, "% Change: EBITDA"),  # the sign
        ({"fcf": "100.0%"}, "% Change: FCF"),  # a figure over a zero prior
        ({"yoy": "5.0%"}, "% Change: Revenue"),
    ],
)
def test_cp1b_a_wrong_change_is_sent_back(cells, figure):
    (issue,) = ms.issues("CP-1B", cp1b(**cells))
    assert f"`{figure}`" in issue


@pytest.mark.parametrize(
    ("row", "why"),
    [
        # A duration is not a range bound: 6.0 - 5.2 = 0.8, Compliant (review, 2026-11-15).
        (
            (
                "| Moody's | CFR | maximum | Debt/EBITDA | > 6.0x for 2 consecutive quarters "
                "| 5.2x | 0.8x | Compliant |"
            ),
            "duration",
        ),
        # A minimum 25% within 3 years against 22%: 22 - 25 = -3, Breached.
        ("| S&P | ICR | minimum | FFO/debt | 25% within 3 years | 22% | -3% | Breached |", "years"),
        # `between ... and` is a range: 5.0 - 5.2 = -0.2 to the binding bound.
        (
            (
                "| Fitch | IDR | maximum | Net leverage | between 5.0x and 5.5x | 5.2x | -0.2x "
                "| Breached |"
            ),
            "between",
        ),
        # An unsigned breach with the word that carries its sign: -0.2.
        ("| S&P | ICR | minimum | Coverage | 2.0x | 1.8x | 0.2x shortfall | Breached |", "word"),
        ("| S&P | ICR | minimum | Coverage | 2.0x | 1.8x | Breach of 0.2x | Breached |", "word"),
        # A case label with its own number: `(12 months)` is not a second case.
        (
            "| S&P | ICR | minimum | Coverage | 2.0x | LTM (12 months): 1.8x | -0.2x | Breached |",
            "label",
        ),
    ],
)
def test_cp2h_review_cases_are_read_as_written(row, why):
    found = cp2h_by(cp2h(row))
    assert set(found.values()) == {"agreed"}, (why, found)


def test_cp4c_review_a_unit_mismatch_stops_the_fulcrum_too():
    # USD 1.0bn available against TLB: USD 400m: the row is not checked, and its scenario's
    # fulcrum is not computed from the raw 1.0 and 400 (review, 2026-11-15).
    rows = [("Base", "HoldCo", "USD 1.0bn", "TLB: USD 400m", "400", "600")]
    found = {o.figure: o.status for o in cp4c_run(cp4c(t4e5(rows), base="Equity", low="x"))}
    assert found["Fulcrum (Base)"] == "not checked"
    assert ms.issues("CP-4C", cp4c(t4e5(rows), base="Equity", low="x")) == ()


def test_cp4c_review_rows_that_repeat_the_pool_are_read_as_one_pool():
    # Every row states the pool, 1,000; residual is what is left after the rows above:
    # Admin 100 (100, 900), TLB 600 (600, 300), Notes 500 (300, 0). Fulcrum: Senior notes.
    rows = [
        ("Base", "HoldCo", "1,000", "Admin and DIP: 100", "100", "900"),
        ("Base", "HoldCo", "1,000", "Senior secured TLB: 600", "600", "300"),
        ("Base", "HoldCo", "1,000", "Senior notes: 500", "300", "0"),
    ]
    text = cp4c(t4e5(rows), low="x")
    assert {o.status for o in cp4c_run(text) if o.figure != "Fulcrum (Low)"} == {"agreed"}
    wrong = cp4c(t4e5(swap(rows, 2, 4, "500")), low="x")  # notes cannot take 500 of 300 left
    (issue,) = ms.issues("CP-4C", wrong)
    assert "`Allocation: Senior notes (Base, HoldCo)`" in issue and "recomputes 300" in issue


def test_cp4c_review_a_fulcrum_at_a_class_boundary_is_not_decided():
    # 1,000 against Admin 100 + TLB 900: value runs out exactly at the TLB/notes boundary. The
    # script names no fulcrum; `Senior secured TLB` (last covered) or `Senior notes` (first
    # impaired) is defensible: not checked, never sent back.
    rows = [
        ("Base", "HoldCo", "1,000", "Admin and DIP: 100", "100", "900"),
        ("Base", "HoldCo", "900", "Senior secured TLB: 900", "900", "0"),
        ("Base", "HoldCo", "0", "Senior notes: 500", "0", "0"),
    ]
    for name in ("Senior secured TLB", "Senior notes", "None"):
        found = {o.figure: o.status for o in cp4c_run(cp4c(t4e5(rows), base=name, low="x"))}
        assert found["Fulcrum (Base)"] in ("agreed", "not checked"), name
    # inside a class it is still decided: Admin and DIP is not the fulcrum there
    found = {o.figure: o.status for o in cp4c_run(cp4c(t4e5(rows), base="Admin and DIP", low="x"))}
    assert found["Fulcrum (Base)"] == "disagreed"


def test_cp4c_review_equal_ranking_claims_listed_in_one_row_are_summed():
    # `TLB: 900; RCF: 600` is one class of 1,500; 1,000 available: allocation 1,000, residual 0.
    rows = [("Base", "HoldCo", "1,000", "TLB: 900; RCF: 600", "1,000", "0")]
    text = cp4c(t4e5(rows), base="TLB and RCF", low="x")
    found = {o.figure: o.status for o in cp4c_run(text)}
    assert found["Allocation: TLB and RCF (Base, HoldCo)"] == "agreed"
    assert found["Fulcrum (Base)"] == "agreed"


@pytest.mark.parametrize(
    "cell",
    ["n/a (N=4)", "Suppressed (N=4)", "Below gate", "Not computed", "NC", "n.a.", "N<5"],
)
def test_cp1c_review_words_below_the_gate_are_never_sent_back(cell):
    # EV/EBITDA has N = 4: the method's gate gives no average; a cell stating no figure cannot
    # disagree with "no figure" (review, 2026-11-15).
    text = cp1c().replace("| Not calculable (N=4) |", f"| {cell} |")
    assert ms.issues("CP-1C", text) == ()
    assert cp1c_by(text)["Peer Avg: EV/EBITDA"].status in ("agreed", "not checked")


def test_cp1c_review_an_indicative_figure_below_the_gate_disagrees():
    # Step 04D: "Min 3 for median, 4 quartile, 5 avg"; REF: "Do not calculate average ...
    # unless sufficient comparable datapoints exist". No indicative exception.
    text = cp1c().replace("| Not calculable (N=4) |", "| 11.25x (indicative only) |")
    (issue,) = ms.issues("CP-1C", text)
    assert "`Peer Avg: EV/EBITDA`" in issue


def test_cp1c_review_an_absolute_metric_is_not_taken_as_the_multiple():
    # T4.6 holds an absolute EBITDA row and no EV/EBITDA row: T4.10's `EV/EBITDA trading comps`
    # is not matched to it (`ebitda` is a part of `ev/ebitda`, not the multiple).
    t46 = (
        "### T4.6 - Summary statistics\n\n| Metric | Borrower Value | Peer Avg | Median | Min "
        "| Max | Q1 | Q3 | N | Borrower Position |\n|---|---|---|---|---|---|---|---|---|---|\n"
        "| EBITDA | 220 | 240 | 264 | 160 | 312 | — | — | 5 | Below |\n\n"
    )
    text = cp1c(t46=t46)
    assert ms.issues("CP-1C", text) == ()
    found = cp1c_by(text)
    assert found["Implied EV Low: EV/EBITDA trading comps"].status == "not checked"


def test_cp1c_review_an_empty_cell_in_a_joined_column_is_one_peer_without_a_value():
    t45 = (
        "### T4.5 - Credit metrics\n\n| Entity | Total/Net/Sr Sec Leverage | Calc/Comp Status |\n"
        "|---|---|---|\n| Peer A | 4.0x / 3.5x / 2.0x | Reported / Comparable |\n"
        "| Peer B |  | Reported / Comparable |\n"
        "| Peer C | 6.0x / 5.5x / 4.0x | Reported / Comparable |\n\n"
    )
    # Net leverage over A and C (B states none): N = 2, min 3.5, max 5.5, no median (gate 3).
    t46 = (
        "### T4.6 - S\n\n| Metric | Borrower Value | Peer Avg/Median/Min/Max | N |\n"
        "|---|---|---|---|\n| Net Leverage | 4.0x | n.m. / n.m. / 3.5x / 5.5x | 2 |\n\n"
    )
    found = cp1c_by(cp1c(t46=t46 + t45))
    assert {found[f"Peer {s}: Net Leverage"].status for s in ("Avg", "Median", "Min", "Max")} == {
        "agreed"
    }


# --- completeness: every enforced module, headers written in harmless other ways ------------------

ENFORCED = ("CP-0", "CP-1A", "CP-DR", "CP-2", "CP-2A", "CP-2E", "CP-2G", "CP-3", "CP-5", "CP-6")


def _declared(module: str) -> dict[str, list[str]]:
    """The required registers' declared columns, read by the method's own `load_contract` from
    the SKILL.md the module is sent (not by the check under test), less this transport's cuts."""
    from deploy_workflow.owners.cpos_launch import required_registers

    contract = mc.contract(module)
    assert isinstance(contract, dict), module
    required = set(required_registers(module))
    return {i: s["columns"] for i, s in contract["registers"].items() if i in required}


def _title(c: str) -> str:
    return f"**{c.replace('_', ' ').title()}**"


def _unit_and_spaces(c: str) -> str:
    return c.replace("/", " / ").replace("_", " ") + " (USD m)"


def _plural_footnote(c: str) -> str:
    return (c if c.endswith("s") else c + "s") + "†"


def _br(c: str) -> str:
    return c.replace(" ", "<br>", 1).replace("1–5", "(1-5)")


TRANSFORMS = {
    "as declared": lambda c: c,
    "title case, bold": _title,
    "spaced slash, unit": _unit_and_spaces,
    "plural, footnote mark": _plural_footnote,
    "line break, bracketed range": _br,
}


@pytest.mark.parametrize("transform", sorted(TRANSFORMS))
@pytest.mark.parametrize("module", ENFORCED)
def test_completeness_accepts_every_enforced_registers_harmless_headers(module, transform):
    change = TRANSFORMS[transform]
    parts = [f"---\nmodule_id: {module}\n---\n\n## Findings\n"]
    for ident, columns in _declared(module).items():
        header = [change(c) for c in reversed(columns)] + ["Source"]  # any order, an extra column
        rows = f"|{'---|' * len(header)}\n| {' | '.join(['Synthetic.'] * len(header))} |\n"
        parts.append(f"### {ident} - Register\n\n| {' | '.join(header)} |\n{rows}")
    text = "\n".join(parts) + "\n## Gaps\n"
    assert ms.shared_issues(module, text) == (), (module, transform)
    agreed = [o for o in complete(module, text) if o.figure == "columns" and o.status == "agreed"]
    assert len(agreed) == len(_declared(module)), (module, transform)


@pytest.mark.parametrize(
    ("declared", "header"),
    [
        ("Raw Score 1–5", "Raw Score (1-5)"),  # CP-3 T3.3 (review, 2026-11-15)
        ("Raw Score 1–5", "Raw Score"),
        ("Affected Section / Flag / Export Record", "Affected Section / Flag"),  # CP-1A T2D.11
        ("Gap", "Gap #"),
        ("Gap", "Gap No."),
        ("Formula / Source", "Formula or Source"),
        ("Evidence ID", "Evidence ID¹"),
        ("Missing Data", "Missing<br>Data"),
    ],
)
def test_completeness_review_header_forms(declared, header):
    assert mc._present(declared, [header])


@pytest.mark.parametrize("declared", ["dependency", "Responsible Module", "downstream module"])
def test_completeness_review_routing_columns_are_never_required(declared):
    # ROUTING_RULES: no upstream or downstream dependencies, no rows addressed to modules.
    assert mc.ROUTING_COLUMN.search(declared)
    for kept in ("Module Status", "Originating Module", "independence_family"):
        assert not mc.ROUTING_COLUMN.search(kept), kept


@pytest.mark.parametrize(
    "row",
    [
        # A cushion described against a breach is not a breach: 6.0 - 5.2 = 0.8, Compliant.
        "| Moody's | CFR | maximum | Debt/EBITDA | 6.0x | 5.2x | 0.8x to breach | Compliant |",
        "| Moody's | CFR | maximum | Debt/EBITDA | 6.0x | 5.2x | 0.8x before breach | Compliant |",
        "| Moody's | CFR | maximum | Debt/EBITDA | 6.0x | 5.2x | 0.8x (no breach) | Compliant |",
        # Durations and counts with a hyphen are not range bounds.
        (
            "| Moody's | CFR | maximum | Debt/EBITDA | Above 6.0x sustained over 12-18 months "
            "| 5.2x | 0.8x | Compliant |"
        ),
        "| Moody's | CFR | maximum | Debt/EBITDA | 6.0x (12-18 months) | 5.2x | 0.8x | Compliant |",
        # A minimum 15% (one to two notches) against 18%: 18 - 15 = 3.
        "| S&P | ICR | minimum | FFO/debt | 15% (1-2 notches) | 18% | 3% | Compliant |",
    ],
)
def test_cp2h_second_review_cases_are_not_sent_back(row):
    assert ms.issues("CP-2H", cp2h(row)) == ()
    assert "agreed" in set(cp2h_by(cp2h(row)).values())


def test_cp2h_a_point_breach_read_as_not_sustained_is_not_decided():
    # REF_CP-2H_C: "a point-in-time breach is not automatically a trigger".
    row = "| Moody's | CFR | maximum | Debt/EBITDA | 6.0x | 6.4x | -0.4x | Compliant (one-period "
    row += "breach, not sustained) |"
    found = cp2h_by(cp2h(row))
    assert found["Headroom: Debt/EBITDA"] == "agreed"
    assert found["Status: Debt/EBITDA"] == "not checked"


@pytest.mark.parametrize(
    "cell", ["n.a.", "N.A.", "NMF", "n.m", "New", "N/A (zero base)", "n/a (new)"]
)
def test_cp1b_review_words_over_a_zero_prior_are_never_sent_back(cell):
    # FCF 0 -> 50: the script gives no percentage; a cell stating no figure cannot disagree.
    assert ms.issues("CP-1B", cp1b(fcf=cell)) == ()


def test_cp1b_review_the_joined_yoy_layout_keeps_a_null_word_whole():
    t44 = (
        "### T4.4 - Performance\n\n| Line Item | FY2023 | FY2024 | YoY Abs/% |\n|---|---|---|---|\n"
        "| FCF | 0 | 50 | 50 / n/m |\n| Revenue | 2,100 | 2,250 | 150 / 7.1% |\n\n"
    )
    found = cp1b_by(cp1b(t44=t44))
    assert found[("T4.4", "% Change: FCF")] == "agreed"
    assert found[("T4.4", "% Change: Revenue")] == "agreed"


@pytest.mark.parametrize(("item", "cell"), [("COGS", "(10.0%)"), ("Cash Interest Paid", "-10.0%")])
def test_cp1b_review_a_cost_may_carry_the_unfavourable_sign(item, cell):
    # 1,000 -> 1,100 is +10.0%; a cost's rise written as (10.0%) is the same change.
    t44 = (
        "### T4.4 - Performance\n\n| Line Item | FY2023 | FY2024 | YoY Change (%) |\n"
        f"|---|---|---|---|\n| {item} | 1,000 | 1,100 | {cell} |\n\n"
    )
    assert cp1b_by(cp1b(t44=t44))[("T4.4", f"% Change: {item}")] == "agreed"
    revenue = t44.replace(f"| {item} |", "| Revenue |")  # not a cost: the sign is wrong
    assert cp1b_by(cp1b(t44=revenue))[("T4.4", "% Change: Revenue")] == "disagreed"


def test_cp1b_review_unread_cells_do_not_hide_other_rows():
    # `n.a.` on a non-zero prior and `.` once crashed the whole check; the wrong EBITDA sign must
    # still be sent back.
    for cell in ("n.a.", "."):
        (issue,) = ms.issues("CP-1B", cp1b(revenue=cell, ebitda="7.3%"))
        assert "`% Change: EBITDA`" in issue


def test_cp1b_review_an_en_dash_minus_and_a_one_sided_unit():
    assert cp1b_by(cp1b(ebitda="–7.3%"))[("T4.6", "% Change: EBITDA")] == "agreed"
    one_sided = cp1b().replace("| USD 2,250m |", "| 2,250 |")  # USD 2,100m beside a bare 2,250
    assert cp1b_by(one_sided)[("T4.6", "% Change: Revenue")] == "not checked"


def test_cp1b_review_a_quarter_beside_year_to_date_is_not_paired():
    t44 = (
        "### T4.4 - Performance\n\n| Line Item | Q3 2023 | Q3 2024 | 9M 2023 | 9M 2024 "
        "| YoY Change (%) |\n|---|---|---|---|---|---|\n| Revenue | 500 | 550 | 1,500 | 1,560 "
        "| 10.0% |\n\n"
    )
    assert cp1b_by(cp1b(t44=t44))[("T4.4", "% Change: all")] == "not checked"


def test_cp1c_review_a_gate_explanation_with_a_digit_is_a_word():
    text = cp1c().replace("| Not calculable (N=4) |", "| Not calculated: N below 5 |")
    assert ms.issues("CP-1C", text) == ()


@pytest.mark.parametrize(
    "method",
    ["Transaction EV/EBITDA (T4.9)", "EV/EBITDA trading comps (ex-outliers)"],
)
def test_cp1c_review_t410_matches_only_the_multiple_it_names(method):
    # Step 06C names transaction multiples as their own method, and step 05 an ex-outlier
    # version: neither is T4.6's trading EV/EBITDA, so neither is compared with it.
    text = cp1c(high="USD 7,500m").replace("| EV/EBITDA trading comps |", f"| {method} |")
    found = cp1c_by(text)
    assert found[f"Implied EV High: {method}"].status == "not checked"
    assert ms.issues("CP-1C", text) == ()


def test_cp4c_review_a_deficit_pool_does_not_hide_another_rows_error():
    # OpCo states (50) available (a deficit): the script refuses that row only; HoldCo's wrong
    # residual (950 where 1,000 - 100 = 900) is still sent back.
    rows = [
        ("Base", "OpCo", "(50)", "Trade: 100", "0", "(50)"),
        ("Base", "HoldCo", "1,000", "Admin and DIP: 100", "100", "950"),
    ]
    (issue,) = ms.issues("CP-4C", cp4c(t4e5(rows), base="x", low="x"))
    assert "`Residual: Admin and DIP (Base, HoldCo)`" in issue


def test_cp4c_review_unicode_minus_and_pro_rata_rows():
    minus = swap(BASE_ROWS, 1, 4, "−600")  # U+2212, an outflow: compared by magnitude
    assert {o.figure: o.status for o in cp4c_run(cp4c(t4e5(minus)))}[
        "Allocation: Senior secured TLB (Base, HoldCo)"
    ] == "agreed"
    # Two claims ranking equally written as two rows sharing 300 pro rata: 500 and 250 each
    # recover 40% (200 and 100). Right, though not the one-row form the note asks: not checked,
    # never "repaired" to 300.
    rows = [
        ("Base", "HoldCo", "300", "Senior notes: 500", "200", "100"),
        ("Base", "HoldCo", "300", "Trade claims: 250", "100", "200"),
    ]
    assert ms.issues("CP-4C", cp4c(t4e5(rows), base="x", low="x")) == ()


@pytest.mark.parametrize(
    ("declared", "header"),
    [
        # a joined declared name written as its natural parts (CP-2G T2H.5, T2H.6, T2H.4, T2H.8)
        ("gross/net leverage", ["Gross leverage", "Net leverage"]),
        ("opening debt/cash", ["Opening debt", "Opening cash"]),
        ("closing debt/cash", ["Closing debt", "Closing cash"]),
        ("evidence/assumption IDs", ["Evidence IDs", "Assumption IDs"]),
        ("target/date", ["Target", "Target date"]),
        # the method's own wording around the declared name
        ("interest", ["Cash interest"]),
        ("issuance", ["Debt issuance"]),
        ("coverage", ["EBITDA / interest coverage"]),
        ("margin", ["EBITDA margin (%)"]),
        ("EBITDA", ["Adjusted EBITDA"]),
        ("FCF", ["Free cash flow (FCF)"]),
        ("CFO", ["Cash from operations (CFO)"]),
        # other decorations
        ("revenue", ["Revenue, USD m"]),
        ("period", ["Period(s) covered"]),
    ],
)
def test_completeness_second_review_header_forms(declared, header):
    assert mc._present(declared, header)


def test_completeness_half_a_joined_name_is_still_missing():
    assert not mc._present("gross/net leverage", ["Gross leverage"])
    assert not mc._present("opening debt/cash", ["Opening debt"])


@pytest.mark.parametrize(
    "row",
    [
        "| All | Not supplied: no forecast | E-12 |",  # a Source or Evidence ID beside the gap
        "| All | n/a | Not applicable: no floating debt |",
        "| FY2025E | Base | Not supplied: not forecast |",  # two labels
        "| Not calculable: no EBITDA | — | — |",
        "| Unavailable: not disclosed | S1 | — |",
    ],
)
def test_completeness_review_gap_rows_with_other_cells(row):
    text = cp2e(
        f"### T2F.4 - Unhedged Exposure Table\n\n| A | B | C |\n|---|---|---|\n{row}\n\n", T2F5
    )
    assert ms.shared_issues("CP-2E", text) == ()


def test_completeness_review_a_register_split_under_sub_headings_is_read_whole():
    split = (
        "### T2F.4 - Unhedged Exposure Table\n\n#### Exposure\n\n"
        "| Metric | Amount | Formula / Source | Status |\n|---|---|---|---|\n"
        "| Total debt | USD 2,000m | T2F.2 | Reported |\n\n#### Implication\n\n"
        "| Metric | Credit Implication | Source Trace |\n|---|---|---|\n"
        "| Total debt | Context. | S1 |\n\n"
    )
    assert statuses("CP-2E", cp2e(split, T2F5))[("T2F.4", "columns")] == "agreed"


def test_cp1c_quartiles_follow_the_scripts_inclusive_convention():
    # The exclusive convention on 9, 10, 12, 14 gives Q1 9.25 and Q3 13.5; the script's inclusive
    # one gives 9.75 and 12.5, so the exclusive figures are sent back.
    exclusive = cp1c().replace("| 9.75x | 12.5x |", "| 9.25x | 13.5x |", 1)
    found = cp1c_by(exclusive)
    assert found["Peer Q1: EV/EBITDA"].status == found["Peer Q3: EV/EBITDA"].status == "disagreed"
    assert "inclusive" in found["Peer Q1: EV/EBITDA"].reason
    assert len(ms.issues("CP-1C", exclusive)) == 2
    # A quartile the handoff words instead of stating is never a disagreement.
    worded = cp1c().replace("| 9.75x | 12.5x |", "| Not calculable | n.m. |", 1)
    assert cp1c_by(worded)["Peer Q1: EV/EBITDA"].status == "not checked"
    assert ms.issues("CP-1C", worded) == ()


def test_cp1c_a_table_without_quartile_columns_is_not_checked_for_them():
    text = cp1c()
    for cut in (" Q1 | Q3 |", "---|---|---|---|---|---|---|---|---|---|"):
        assert cut in text
    bare = text.replace("| Q1 | Q3 | N |", "| N |", 1)
    bare = bare.replace("| 20.0% | 26.0% | ", "| ", 1).replace("| 9.75x | 12.5x | ", "| ", 1)
    found = cp1c_by(bare)
    assert found["Peer Q1: EBITDA Margin"].status == "not checked"
    assert found["Peer Median: EBITDA Margin"].status == "agreed"
    assert ms.issues("CP-1C", bare) == ()


# --- CP-1B: the method's joined T4.6 layout and `reported` percentages (live TDG FY2024 run) ----

LIVE_1B = (ROOT / "tests/fixtures/CP-1B-earnings_update-tdg-fy2024-t44-t46.md").read_text()


def live_1b(text: str = LIVE_1B) -> dict[tuple[str, str], ms.Outcome]:
    return {(o.register, o.figure): o for o in ms.run("CP-1B", text)}


def test_cp1b_live_handoff_checks_the_joined_t46_and_reported_percentages():
    found = live_1b()
    agreed = {
        ("T4.4", "Revenue"): 20.5771,
        ("T4.4", "COGS"): 19.1396,
        ("T4.4", "Gross profit"): 21.6033,
        ("T4.4", "SG&A"): 25.641,
        ("T4.4", "Reported EBITDA"): 21.1245,
        ("T4.6", "Operating profit"): 20.8005,
        ("T4.6", "Reported EBITDA"): 21.1245,
        ("T4.6", "Issuer-adjusted EBITDA, segment bridge"): 22.9161,
        ("T4.6", "Operating cash flow"): 48.7273,
    }
    for (register, name), value in agreed.items():
        outcome = found[(register, f"% Change: {name}")]
        assert outcome.status == "agreed", (register, name, outcome.reason)
        assert outcome.recomputed is not None
        assert abs(outcome.recomputed - value) < 1e-3, (register, name, outcome.recomputed)
    sales = found[("T4.6", "% Change: Sales, total and organic/acquisition")]
    assert sales.status == "not checked"
    assert "pairs" in sales.reason
    assert found[("T4.6", "% Change: Leverage and coverage")].status == "not checked"
    assert not [o for o in found.values() if o.status == "disagreed"]
    assert ms.issues("CP-1B", LIVE_1B) == ()


def test_cp1b_live_handoff_wrong_figures_are_sent_back_and_other_words_are_not_read():
    wrong44 = LIVE_1B.replace("| 20.6% reported |", "| 22.0% reported |", 1)
    assert live_1b(wrong44)[("T4.4", "% Change: Revenue")].status == "disagreed"
    wrong46 = LIVE_1B.replace("+608; 20.80%", "+608; 25.0%", 1)
    assert live_1b(wrong46)[("T4.6", "% Change: Operating profit")].status == "disagreed"
    approx = LIVE_1B.replace("| 20.6% reported |", "| 20.6% approx |", 1)
    assert live_1b(approx)[("T4.4", "% Change: Revenue")].status == "not checked"
    calculated = LIVE_1B.replace("| 20.6% reported |", "| 20.58% calculated |", 1)
    assert live_1b(calculated)[("T4.4", "% Change: Revenue")].status == "agreed"


def joined_1b(pair: str, change: str) -> ms.Outcome:
    head = (
        "### T4.6 Variance register\n\n| Metric | Basis | Prior/Current | Abs/% | Driver |"
        " Source |\n"
        "|---|---|---|---|---|---|\n"
    )
    text = head + f"| Revenue | Annual YoY | {pair} | {change} | d | s |\n"
    (outcome,) = [o for o in ms.run("CP-1B", text) if o.register == "T4.6"]
    return outcome


@pytest.mark.parametrize(
    ("pair", "change", "status"),
    [
        ("2923 / 3531", "+608 (20.8%)", "agreed"),
        ("2000 / 1900", "-100 (5.0%)", "agreed"),
        ("2923 / 3531", "+608 / 20.8%", "agreed"),
        ("2923 / 3531", "+608 (+20.8%)", "agreed"),
        ("2923 / 3531", "+608 (-20.8%)", "disagreed"),
        ("2000 / 1900", "-100 (+5.0%)", "disagreed"),
        ("2000 / 1900", "(5.0%)", "agreed"),
        ("2000 / 1900", "-100; (5.0%)", "agreed"),
        ("6585 / 7940", "+1355; 16.2% organic", "not checked"),
        ("2923 / 3531", "+608; 20.8% approx", "not checked"),
        ("2923 / 3531", "+608; 25.0% reported", "disagreed"),
    ],
)
def test_cp1b_joined_abs_percent_is_read_only_when_the_percentage_ends_it(pair, change, status):
    assert joined_1b(pair, change).status == status


@pytest.mark.parametrize(
    ("metric", "pair", "change", "status"),
    [
        ("EBITDA margin", "52.3 / 53.0, %", "+0.7%", "not checked"),
        ("EBITDA margin", "47.8 / 48.0, %", "+0.2; 0.2%", "not checked"),
        ("Leverage", "6.27 / 6.53, x", "+0.26; 4.1%", "not checked"),
        ("Leverage", "6.27 / 6.53, times", "+0.26; 4.1%", "not checked"),
        ("Margin", "47.8 / 48.0, bps", "+20; 0.4%", "not checked"),
        ("Margin", "47.8 / 48.0, pp", "+0.2; 0.4%", "not checked"),
        ("Margin", "47.8 / 48.0, points", "+0.2; 0.4%", "not checked"),
        ("Revenue", "950 / 1.2, USD m then USD bn", "+250; 26.3%", "not checked"),
        ("Operating profit", "2923 / 3531, USD millions", "+608; 20.80%", "agreed"),
    ],
)
def test_cp1b_joined_unit_words_after_the_comma_decide_whether_the_row_is_read(
    metric, pair, change, status
):
    head = (
        "### T4.6 Variance register\n\n| Metric | Basis | Prior/Current | Abs/% | Driver |"
        " Source |\n|---|---|---|---|---|---|\n"
    )
    text = head + f"| {metric} | Annual YoY | {pair} | {change} | d | s |\n"
    (outcome,) = [o for o in ms.run("CP-1B", text) if o.register == "T4.6"]
    assert outcome.status == status, outcome


# --- parked finding h: a range in Abs/%; a stated gap in the CP-3 unit cells ----------------------


def _joined_t46(change: str) -> ms.Outcome:
    text = (
        "### T4.6 - Comparison\n\n| Metric | Basis | Prior/Current | Abs/% | Driver | Source |\n"
        f"|---|---|---|---|---|---|\n| Revenue | Annual YoY | 6585 / 7940 | {change} | d | s |\n"
    )
    (outcome,) = [o for o in ms.run("CP-1B", text) if o.register == "T4.6"]
    return outcome


@pytest.mark.parametrize(
    "cell", ["20 –21%", "20-21%", "20 to 21%", "20–21 %", "20% to 21%", "20 - 21%"]
)
def test_cp1b_a_range_in_abs_pct_is_not_one_figure(cell):
    outcome = _joined_t46(cell)
    assert outcome.status == "not checked", outcome
    assert "range" in outcome.reason


@pytest.mark.parametrize(
    ("cell", "status"),
    [
        ("-21%", "disagreed"),
        ("(21%)", "disagreed"),
        ("1355; -21.0%", "disagreed"),
        ("+1355; 20.6%", "agreed"),
    ],
)
def test_cp1b_a_real_negative_in_abs_pct_is_still_read(cell, status):
    assert _joined_t46(cell).status == status


def _waterfall(rows: list[tuple[str, ...]]) -> list[ms.Outcome]:
    body = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    text = (
        "## Findings\n### Recovery waterfall\n"
        "| Line | Amount | Low | Base | High | Currency | Scale |\n"
        f"|---|---|---|---|---|---|---|\n{body}\n## Gaps\nNone.\n"
    )
    return ms.run("CP-3", text)


_GAP = "Not supplied: no supported valuation cases"
_EV_GAP = ("Enterprise value", _GAP, _GAP, _GAP, _GAP, _GAP, _GAP)
_CLAIM = ("Claim: RCF", "50", "n/a", "n/a", "n/a", "USD", "millions")


def test_cp3_a_waterfall_that_states_a_gap_names_the_gap_not_a_unit_difference():
    (outcome,) = _waterfall([_EV_GAP, _CLAIM])
    assert outcome.status == "not checked"
    assert "different or unread" not in outcome.reason
    assert "state a gap" in outcome.reason and outcome.reason.count(_GAP) == 1


@pytest.mark.parametrize(("currency", "scale"), [("EUR", "millions"), ("USD", "thousands")])
def test_cp3_a_real_unit_mix_keeps_its_reason(currency, scale):
    other = ("Claim: Notes", "70", "n/a", "n/a", "n/a", currency, scale)
    (outcome,) = _waterfall([_EV_GAP, _CLAIM, other])
    assert outcome.status == "not checked"
    assert "different or unread currencies or scales" in outcome.reason
