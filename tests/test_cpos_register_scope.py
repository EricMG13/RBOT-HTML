"""T4 (owner, 2026-11-13): no routing text and no no-consumer registers are written.

The answer key is `docs/sweeps/2026-11-13-optimisation-review/appendix-inventory.md` (one row per
register, both Sol runs) and the controller's lists below (rule R1: a register is cut only when
every inventory row for its id, in both runs, is CUT)."""

import re
from pathlib import Path

import pytest
from test_cpos_launch import (
    OWNER_PATHWAY,
    all_instructions,
    answer,
    good_task,
)

from deploy_vii.contracts import DEACTIVATED_PATHWAYS, PATHWAY_MODULES
from deploy_workflow.owners import cpos_launch
from deploy_workflow.owners.cpos import _checked_handoff
from deploy_workflow.owners.cpos_launch import METHODS, checker

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/sweeps/2026-11-13-optimisation-review/appendix-inventory.md"
SCOPE_FILE = "docs/reuse/selected-methods/CPOS_REGISTER_SCOPE.md"

# Rule R1, as literals. `ownership_register` is not here: handoff_delivery.py:488 names it.
CUT = {
    "CP-0": ["P5", "T3", "T5"],
    "CP-1A": ["source_classification", "credit_translation", "T2D.2", "T2D.6", "T2D.7", "T2D.8"],
    "CP-DR": ["TDR.1", "TDR.3"],
    "CP-2": ["T2.7", "T2.11"],
    "CP-2A": [
        *("T2DS.3", "T2DS.5", "T2DS.7", "T2B.3", "T2B.4", "T2B.5"),
        *("T5.1", "T5.2", "T5.3", "T5.4"),
    ],
    "CP-2E": [
        *("T2F.2", "T2F.4", "T2F.5", "T2F.8", "T2F.9"),
        *("T2G.1", "T2G.2", "T2G.3", "T2G.4", "T2G.5", "T2G.6", "T2G.7", "T2G.8"),
    ],
    "CP-2G": ["T2H.1", "T2H.2", "T2H.9"],
    "CP-3": [
        *("T3.1", "T3.4", "T3.5", "T3.7", "T3.9", "T3.10"),
        *("T3B.2", "T3B.3", "T3B.4", "T3B.5", "T3B.6", "T3B.7", "T3B.8", "T3B.10", "T3B.11"),
        *("T3C.1", "T3C.2", "T3C.3", "T3C.5", "T3C.6", "T3C.7", "T3C.8", "T3C.9"),
    ],
    "CP-5": [
        *("T5B.4", "T5B.5", "T5B.6", "T5B.7", "T5B.8"),
        *("T5.1", "T5.2", "T5.4", "T5.5", "T5.6", "T5.7", "T5.8", "T5.9"),
    ],
    "CP-6": ["T6A.6", "T6A.11", "T6E.4", "T6E.6", "T6E.7", "T6E.11"],
}
# The medium run wrote four CP-1A registers under names, not ids (checked against that run's
# `<!-- table-id: ... -->` tags: T2D.2, T2D.6, T2D.7, T2D.8).
MEDIUM_NAMES = {
    "Source classification": "source_classification",
    "Credit translation register": "credit_translation",
    "Ownership and control evidence": "T2D.2",
    "Acquisition appetite and integration": "T2D.6",
    "Disclosure quality": "T2D.7",
    "Governance dimensions": "T2D.8",
}
# Named by ROUTING_RULES, not by a scope section: nothing reads them either.
ROUTING_IDS = (
    *("T7", "T8", "T2D.10", "downstream_readiness", "T2B.8", "T5.6"),
    *("cp2g.cp_model_forecast_drivers", "cp2b.cp_model_catalysts"),
)
VERBATIM = (
    "Routing in this transport: CP-OS chooses which modules run and in what order, gives each "
    "module the handoffs it needs and keeps every handoff; no reader acts on a recommendation "
    "about what to run next. This overrides every method instruction to return or recommend a "
    "next command, keep a Master Index, managed workspace, export record or run command sheet, "
    "map upstream or downstream dependencies, file a research request or brief, or write a "
    "register whose rows are addressed to receiving modules (cross-module handoff, consumer "
    "actions, analytical consumption, event use, downstream readiness) or the tables "
    "`cp2g.cp_model_forecast_drivers` and `cp2b.cp_model_catalysts`: write none of them. Under "
    "`## Next module` write only: `The orchestrator selects the next module.` A restriction on "
    "how your results may be used is a limitation: state it in `### Limitations` or `## Gaps`, "
    "in plain words. Every figure in a reader passage must still appear in a table you write or "
    "in `## Calculations`."
)
SELF_CHECK_WORDS = (
    "`required_register_ids`",
    "`appendix_contract`",
    "lossless",
    "completeness check",
    "Analytical appendix",
    "do not restore it",
    "do not block",
)
NEXT_MODULE = "The orchestrator selects the next module."


def inventory_rows() -> list[tuple[str, str, str, str]]:
    """(run, module, register, class) for every row of the inventory."""
    run, rows = "", []
    for line in INVENTORY.read_text().splitlines():
        if line.startswith("## "):
            run = line[3:].strip()
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 5 and cells[2].isdigit():
            rows.append((run, cells[0], cells[1], cells[3]))
    return rows


def row_id(run: str, module: str, register: str) -> str | None:
    if run == "medium" and module == "CP-1A" and register in MEDIUM_NAMES:
        return MEDIUM_NAMES[register]
    if run == "high" and module == "CP-1A" and register == "Credit translation":
        return "credit_translation"
    found = re.match(r"^([A-Za-z0-9_.]+)(?= —| \(|$)", register)
    return found[1] if found else None


def scope_items(module: str) -> list[tuple[str, str]]:
    """(id, name) of each register the module's scope section says not to write."""
    body = dict(cpos_launch.method_sections(module))[f"{SCOPE_FILE} § {module}"]
    listed = body.partition("do not write ")[2].partition(". Any figure")[0]
    return [tuple(item.split(" ", 1)) for item in listed.split("; ")]  # type: ignore[misc]


def instructions_of(tmp_path, **options):
    return all_instructions(tmp_path, **options)[1]


@pytest.fixture(scope="module")
def every_module(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("scope")
    return instructions_of(tmp_path, modules=tuple(m for m in METHODS if m != "CP-8"))


def test_routing_rules_are_the_owners_text_plus_the_self_check_sentence():
    text = cpos_launch.ROUTING_RULES
    assert text.startswith(VERBATIM)
    first, second = text[len(VERBATIM) :].strip().split(". ", 1)
    assert second.count(".") == 1, "R4 and the presence rule: two added sentences"
    for words in SELF_CHECK_WORDS:
        assert words in first, words
    for words in ("Every register the method requires", "table-id", "Not supplied: <reason>"):
        assert words in second, words


def test_routing_rules_name_no_register_the_peer_pack_or_the_checks_need():
    text = cpos_launch.ROUTING_RULES
    for kept in ("TDR.2", "TDR.4", "TDR.5", "TDR.6", "Peer pack"):
        assert kept not in text
    # CP-DR's head still carries the peer pack block beside the routing rule.
    assert cpos_launch.PEER_PACK_BLOCK.count("TDR.4") == 1


def test_every_module_gets_routing_rules_once_right_after_transport_rules(every_module):
    assert set(every_module) == set(METHODS) - {"CP-8"}
    for module, text in every_module.items():
        assert text.count(cpos_launch.ROUTING_RULES) == 1, module
        end = text.index(cpos_launch.TRANSPORT_RULES) + len(cpos_launch.TRANSPORT_RULES)
        assert text[end:].startswith(cpos_launch.ROUTING_RULES), module
        assert text.index(cpos_launch.ROUTING_RULES) < text.index(cpos_launch.METHOD_MARK)


@pytest.mark.parametrize("pathway", sorted(set(PATHWAY_MODULES) - set(DEACTIVATED_PATHWAYS)))
def test_every_pathways_modules_get_routing_rules_once_right_after_transport_rules(
    tmp_path, pathway
):
    texts = instructions_of(tmp_path, pathway=pathway)
    assert texts
    for module, text in texts.items():
        assert text.count(cpos_launch.ROUTING_RULES) == 1, (pathway, module)
        end = text.index(cpos_launch.TRANSPORT_RULES) + len(cpos_launch.TRANSPORT_RULES)
        assert text[end:].startswith(cpos_launch.ROUTING_RULES), (pathway, module)


def test_cp0_no_longer_demands_t7_or_t8_or_the_registers_its_scope_cuts(every_module):
    head = every_module["CP-0"].partition(cpos_launch.METHOD_MARK)[0]
    block = cpos_launch.CP0_BLOCK
    assert block in head
    assert "Do not write T7 or T8: CP-OS orders the modules." in block
    assert "Do not write the registers P1, P2, P4, P6, P7 and P8" in block
    assert "Write P3 and the readiness tables T1 input gate, T2 source register" in block
    assert "T4 content-to-module map and T6 evidence trace" in block
    assert "State any missing document under `## Gaps`." in block
    for gone in (
        "T7 master index state",
        "T8 recommended run command sheet",
        "T3 source hierarchy",
        "T5 gaps and conflicts",
        "Write P3 and P5",
        "the document hierarchy",
        "the minimum missing documents",
    ):
        assert gone not in block, gone


def test_the_scope_file_has_exactly_the_ten_measured_modules_in_its_headings():
    text = (ROOT / SCOPE_FILE).read_text()
    assert re.findall(r"^## (\S+)$", text, re.MULTILINE) == list(CUT)
    assert tuple(CUT) == cpos_launch.REGISTER_SCOPE_MODULES


def test_each_measured_module_carries_its_scope_section_last_and_no_other_does(every_module):
    for module in METHODS:
        names = [name for name, _ in cpos_launch.method_sections(module)]
        mine = [n for n in names if n.startswith(SCOPE_FILE)]
        if module in CUT:
            assert mine == [f"{SCOPE_FILE} § {module}"], module
            assert names[-1] == mine[0], f"{module}: the scope section is the last section"
            assert dict(cpos_launch.method_sections(module))[mine[0]] in every_module[module]
        else:
            assert mine == [], module
            assert "Register scope in this transport" not in every_module.get(module, "")


@pytest.mark.parametrize("module", list(CUT))
def test_the_scope_section_is_the_template_with_the_inventory_cut_list(module):
    body = dict(cpos_launch.method_sections(module))[f"{SCOPE_FILE} § {module}"]
    assert body.startswith(f"## {module}\n")
    assert "Register scope in this transport: do not write " in body
    assert (
        ". Any figure, limitation or conclusion you draw from that work goes in a register you "
        "do write, in `## Calculations` or in `## Gaps`."
    ) in body
    for words in SELF_CHECK_WORDS:
        assert words in body, words
    items = scope_items(module)
    assert [i for i, _ in items] == CUT[module]
    assert all(name.strip() for _, name in items), "every id is named with the method's title"


@pytest.mark.parametrize("module", list(CUT))
def test_every_scope_id_is_cut_in_every_inventory_row_of_both_runs(module):
    rows = [r for r in inventory_rows() if r[1] == module]
    for ident in CUT[module]:
        mine = [(r[0], r[3]) for r in rows if row_id(r[0], r[1], r[2]) == ident]
        assert mine, f"{module} {ident}: no inventory row"
        assert {cls for _, cls in mine} == {"CUT"}, (module, ident, mine)


def test_ownership_register_stays_out_while_a_delivery_reader_names_it():
    # handoff_delivery.py:488 reads the CP-1A section `Ownership and control` as table
    # `ownership_register`; rule R1's STOP: leave an id with a reader out of the list.
    assert "ownership_register" not in (ROOT / SCOPE_FILE).read_text()


def _without_constants(source: str, names: tuple[str, ...]) -> str:
    for name in names:
        source = re.sub(rf"^{name} = \(\n.*?\n\)\n", "", source, flags=re.MULTILINE | re.DOTALL)
    return source


def test_no_check_reader_or_library_names_a_cut_or_routing_register():
    """A hit is a reader or a code-sent requirement of a register the transport stops writing."""
    sources = {
        "cpos_launch.py": _without_constants(
            (ROOT / "src/deploy_workflow/owners/cpos_launch.py").read_text(),
            ("ROUTING_RULES", "CP0_BLOCK", "UPSTREAM_SCOPE_NOTE", "ROUTING_REGISTERS"),
        ),
        **{
            name: (ROOT / "src/deploy_workflow" / name).read_text()
            for name in (
                "prose_checks.py",
                "handoff_delivery.py",
                "markdown_delivery.py",
                "changes_check.py",
            )
        },
        "store.py": (ROOT / "apps/issuer-library/credit_os/store.py").read_text(),
        # `firstHeading` is read by store.py:1154 and views.js:91 (T5B.3 and T6A.7 stay in scope).
        "catalog.json": (ROOT / "apps/issuer-library/credit_os/catalog.json").read_text(),
    }
    ids = sorted({i for ids in CUT.values() for i in ids} | set(ROUTING_IDS))
    # Mentions that are not readers: none today. Add (file, id) here, with the reason, if one is.
    # catalog.json `call.heading` (T5B.7, TDR.3) is read only by `pinned_fields` for an entry whose
    # `path` equals the output (store.py:1164); no catalog entry has a `path`, so nothing reads it.
    allowed = {("catalog.json", "T5B.7"), ("catalog.json", "TDR.3")}
    hits = []
    for ident in ids:
        pattern = re.compile(rf"(?<![A-Za-z0-9_.]){re.escape(ident)}(?![A-Za-z0-9_]|\.[0-9A-Za-z])")
        for name, source in sources.items():
            for number, line in enumerate(source.splitlines(), 1):
                if pattern.search(line) and (name, ident) not in allowed:
                    hits.append(f"{name}:{number} {ident}")
    assert hits == []


def test_cp5_is_told_which_upstream_registers_are_out_of_scope_and_no_other_module_is(tmp_path):
    texts = instructions_of(tmp_path, modules=("CP-0", "CP-1", "CP-1A", "CP-2", "CP-3", "CP-5"))
    run_order = list(texts)
    upstream = [m for m in run_order[: run_order.index("CP-5")] if m in CUT]
    assert upstream  # CP-0, CP-1A, CP-2, CP-3 whatever the planner's order
    marker = cpos_launch.UPSTREAM_SCOPE_NOTE.partition("\n")[0]
    for module, text in texts.items():
        head = text.partition(cpos_launch.METHOD_MARK)[0]
        assert (marker in head) == (module == "CP-5"), module
    head = texts["CP-5"].partition(cpos_launch.METHOD_MARK)[0]
    listed = re.findall(r"^- (CP-[0-9A-Z]+): (.*)$", head, re.MULTILINE)
    assert [m for m, _ in listed] == upstream
    for module, line in listed:
        expected = "; ".join(" ".join(item) for item in scope_items(module))
        assert line.rstrip(".") == expected, module
    assert "absence is not a finding" in head
    assert "Next module" in head
    # not a module of the run, and not upstream of CP-5: no line
    assert "- CP-6:" not in head and "- CP-5:" not in head
    # The routing rule is carried in the note.
    for routing in ("Master Index", "run command sheet", "downstream readiness", "cp_model"):
        assert routing in head


def test_a_run_without_cp5_sends_no_upstream_note(tmp_path):
    texts = instructions_of(tmp_path, modules=("CP-0", "CP-1", "CP-2A"))
    marker = cpos_launch.UPSTREAM_SCOPE_NOTE.partition("\n")[0]
    assert all(marker not in text for text in texts.values())


def _cut_registers_text() -> str:
    """One tagged table and one headed register of the kinds the cut removes."""
    return (
        "### T3 — Document hierarchy\n\n| Item | Value |\n| --- | --- |\n| Order | 1 |\n\n"
        "### Fragility and stress transmission\n\n<!-- table-id: T2B.4 -->\n"
        "| Item | Value |\n| --- | --- |\n| Path | 1 |\n\n"
    )


@pytest.mark.parametrize("module", ["CP-0", "CP-2A", "CP-5"])
@pytest.mark.parametrize("with_cut_registers", [False, True])
def test_a_handoff_without_the_cut_registers_and_with_the_one_line_next_module_passes(
    tmp_path, module, with_cut_registers
):
    """Synthetic: the checker and the report adapter neither need a cut register nor refuse one
    (older habits), and read `## Next module` as an H2 only. The retained-run replay is
    `.superpowers/sdd/quality-defects/t4-replay.py`."""
    pathway = OWNER_PATHWAY.get(module, "covenant_refinancing")
    prepared, task, context = good_task(tmp_path, module, pathway)
    text = answer(context, list(prepared.plan.layout.routes))
    assert "## Next module\n\nNone." in text
    text = text.replace("## Next module\n\nNone.", f"## Next module\n\n{NEXT_MODULE}")
    text = text.replace("## Calculations", registers(module) + "## Calculations", 1)
    if with_cut_registers:
        text = text.replace("## Calculations", _cut_registers_text() + "## Calculations", 1)
    issues = _checked_handoff(task, text.encode(), checker(prepared.layout))
    assert issues == ()


# The presence check (T4 stage B). Derived from the method text each module is sent, less its scope
# section and the routing registers; pinned as literals so a method change shows as a diff here.
REQUIRED = {
    "CP-0": ["T1", "T2", "T4", "T6", "P3"],
    "CP-1A": [
        *(
            "transaction_summary",
            "company_description",
            "revenue_business_mix",
            "ownership_register",
        ),
        *("operating_model", "events_timeline", "gaps_ledger", "conflict_log"),
        *("T2D.1", "T2D.3", "T2D.4", "T2D.5", "T2D.9", "T2D.11"),
    ],
    "CP-DR": ["TDR.2", "TDR.4", "TDR.5", "TDR.6"],
    "CP-2": ["T2.1", "T2.10", "T2.12"],
    "CP-2A": ["T2B.1", "T2B.2", "T2B.6", "T2B.7", "T2B.9", "T5.5", "T5.7"],
    "CP-2E": ["T2F.1", "T2F.3", "T2F.6", "T2F.7"],
    "CP-2G": ["T2H.3", "T2H.4", "T2H.5", "T2H.6", "T2H.7", "T2H.8"],
    "CP-3": ["T3.3", "T3.6", "T3B.1", "T3C.4"],
    "CP-5": ["T5B.1", "T5B.2", "T5B.3", "T5.3"],
    "CP-6": ["T6A.4", "T6A.7"],
}
NOTHING = "| Item | Value |\n| --- | --- |\n| Observed | Not supplied: nothing to report |\n\n"


def register(ident: str, form: str = "heading") -> str:
    """One register written the way the retained handoffs write one."""
    if form == "tag":
        return f"### Register\n\n<!-- table-id: cp.{ident} -->\n{NOTHING}"
    return f"### {ident} — Register\n\n{NOTHING}"


def registers(module: str, *, skip: tuple[str, ...] = (), form: str = "heading") -> str:
    return "".join(register(i, form) for i in REQUIRED[module] if i not in skip)


def refusal(module: str, text: str) -> list[str]:
    return [i for i in cpos_launch.register_issues(module, text) if "Missing registers" in i]


@pytest.mark.parametrize("module", list(REQUIRED))
def test_the_required_registers_derived_from_the_method_text_are_pinned(module):
    assert list(cpos_launch.required_registers(module)) == REQUIRED[module]


@pytest.mark.parametrize("module", list(REQUIRED))
def test_no_required_register_is_a_cut_or_routing_register(module):
    named = set(CUT[module]) | set(ROUTING_IDS)
    assert not named & set(cpos_launch.required_registers(module))


def test_a_missing_register_is_refused_with_one_issue_naming_every_missing_id_and_the_forms():
    text = registers("CP-2A", skip=("T2B.1", "T2B.7", "T5.7"))
    issues = cpos_launch.register_issues("CP-2A", text)
    assert len(issues) == 1
    for ident in ("T2B.1", "T2B.7", "T5.7"):
        assert ident in issues[0]
    for form in ("heading", "<!-- table-id:", "Not supplied: <reason>", "module_status: Blocked"):
        assert form in issues[0]
    assert "T2B.2" not in issues[0]


@pytest.mark.parametrize("module", list(REQUIRED))
def test_a_handoff_with_no_register_is_refused_naming_all_of_the_module(module):
    (issue,) = cpos_launch.register_issues(module, "## Findings\n\nText.\n")
    assert all(ident in issue for ident in REQUIRED[module])


@pytest.mark.parametrize("form", ["heading", "tag"])
@pytest.mark.parametrize("module", list(REQUIRED))
def test_each_recognised_form_of_a_register_with_nothing_to_report_is_accepted(module, form):
    assert cpos_launch.register_issues(module, registers(module, form=form)) == ()


def test_one_heading_that_names_several_ids_counts_for_each():
    heading = "### T2B.1, T2B.2 and T2B.6 — Joint\n\n" + NOTHING
    text = heading + registers("CP-2A", skip=("T2B.1", "T2B.2", "T2B.6"))
    assert cpos_launch.register_issues("CP-2A", text) == ()


def test_an_id_that_is_a_prefix_of_another_does_not_count():
    text = registers("CP-1A", skip=("T2D.1",)) + register("T2D.10") + register("T2D.12")
    assert re.search(r"T2D\.1(?![\w.])", refusal("CP-1A", text)[0])


def test_an_id_named_only_in_prose_does_not_count():
    text = registers("CP-6", skip=("T6A.4",)) + "The T6A.4 register is discussed here.\n"
    assert "T6A.4" in refusal("CP-6", text)[0]


@pytest.mark.parametrize("module", list(REQUIRED))
def test_a_cut_register_is_neither_required_nor_refused(module):
    cut = "".join(register(i) for i in CUT[module])
    assert cpos_launch.register_issues(module, registers(module)) == ()
    assert cpos_launch.register_issues(module, registers(module) + cut) == ()


@pytest.mark.parametrize("status", ["Blocked", "blocked", '"Blocked"'])
def test_a_module_blocked_at_its_gate_is_exempt_as_the_method_defines(status):
    front = f"---\nmodule_id: CP-2\nmodule_status: {status}\n---\n\n## Findings\n\nStopped.\n"
    assert cpos_launch.register_issues("CP-2", front) == ()


def test_a_status_other_than_blocked_is_not_exempt():
    front = "---\nmodule_status: Ready with Limitations\ncommittee_status: Blocked\n---\n\nText.\n"
    assert refusal("CP-2", front)
    assert refusal("CP-2", "Text.\nmodule_status: Blocked\n")  # outside the front matter


@pytest.mark.parametrize("module", ["CP-4", "CP-1", "CP-1B", "CP-2D", "CP-3C", "CP-8", "CP-L10"])
def test_modules_outside_the_ten_are_never_checked(module):
    assert cpos_launch.register_issues(module, "## Findings\n\nNo registers.\n") == ()


def test_the_checker_sends_a_handoff_without_its_registers_back_with_one_issue(tmp_path):
    prepared, task, context = good_task(tmp_path, "CP-2")
    full = answer(context, list(prepared.plan.layout.routes))
    assert _checked_handoff(task, full.encode(), checker(prepared.layout)) == ()
    text = re.sub(r"### T2\.\d+ - Register\n\n(?:\|.*\n)+\n", "", full)  # the fixture's own
    assert text != full
    check = checker(prepared.layout)
    issues = _checked_handoff(task, text.encode(), check)
    assert [i for i in issues if "Missing registers" in i] == [
        i for i in issues if "T2.1" in i and "T2.10" in i and "T2.12" in i
    ]
    assert len([i for i in issues if "Missing registers" in i]) == 1
    again = text.replace("## Calculations", registers("CP-2") + "## Calculations", 1)
    assert _checked_handoff(task, again.encode(), check) == ()


# The reviewer's decoys (probes/t4b_id_cell_from_unrelated_table.py, t4b_heading_crossref.py): a
# retained handoff carries these shapes, and none of them is the register.
DECOYS = {
    ("CP-2", "T2.10"): (
        "### Coverage definition\n\n| Component | Required fields | Present | Treatment |\n"
        "|---|---|---|---|\n| T2.10 | 35 | 35 | Five drivers |\n\n"
    ),
    ("CP-1A", "transaction_summary"): (
        "### CP-MODEL snapshot fields\n\n| field_id | value | status | source | locator | date |\n"
        "|---|---|---|---|---|---|\n"
        "| transaction_summary | Dividend recap | READY | S1 | p1 | 2024-09-30 |\n\n"
    ),
    ("CP-5", "T5.3"): (
        "### Upstream scope\n\n| Register | Module | Treatment |\n|---|---|---|\n"
        "| T5.3 | CP-2A event risk register | cut in transport |\n\n"
    ),
}


@pytest.mark.parametrize(("module", "ident"), list(DECOYS))
def test_an_id_in_the_first_cell_of_an_unrelated_table_does_not_count(module, ident):
    text = registers(module, skip=(ident,)) + DECOYS[(module, ident)]
    assert ident in refusal(module, text)[0]


def test_a_heading_that_only_cites_an_id_does_not_count():
    other = "### T2B.2 - Business model snapshot (inputs from T2B.1)\n\n" + NOTHING
    text = registers("CP-2A", skip=("T2B.1", "T2B.2")) + other
    assert re.search(r"T2B\.1(?![\w.])", refusal("CP-2A", text)[0])


def test_the_routing_rule_and_the_refusal_both_say_how_a_module_stops_at_its_gate():
    stop = "`module_status: Blocked` in the front matter and writes the gate register only"
    assert stop in cpos_launch.ROUTING_RULES
    assert "`module_status: Blocked` in the front matter" in refusal("CP-6", "x")[0]


@pytest.mark.parametrize(
    "heading",
    [
        "### Coverage and T2.10 reconciliation",
        "### Inputs, T2.10 cross-reference",
        "### Demand T2.10 sensitivity",
        "### Notes / T2.10",
    ],
)
def test_a_prose_word_before_an_id_does_not_make_the_heading_that_register(heading):
    assert not cpos_launch._has_register(heading + "\n", "T2.10")


@pytest.mark.parametrize(
    ("heading", "ident"),
    [
        ("### T2B.1, T2B.2 and T2B.6 - Registers", "T2B.6"),
        ("### TDR.4 / TDR.5 - Peer pack", "TDR.5"),
        ("### P3 & T1 - Inputs", "T1"),
        ("### transaction_summary, company_description - Business", "company_description"),
    ],
)
def test_an_id_list_lead_still_counts_for_each_id(heading, ident):
    assert cpos_launch._has_register(heading + "\n", ident)
