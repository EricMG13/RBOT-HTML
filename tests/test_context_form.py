"""The context form (docs/templates/context-form.html) copies tables from the code and from the
library it sits beside, because it opens from disk with no request. Each test keeps one copy to its
source, so a change in the code cannot leave the form forecasting a run that no longer happens."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import get_args

import pytest

from deploy_vii import cp3_relative_value
from deploy_vii.contracts import PATHWAY_MODULES
from deploy_vii.registry import plan
from deploy_workflow.context import (
    ASSUMPTION_LIMITS,
    Cp3Mode,
    IssueClassification,
    Limit,
    RatingScope,
    RunContext,
    load_context,
)
from deploy_workflow.inbox.layout import MAX_ISSUER_ID
from deploy_workflow.inbox.runs import Status
from deploy_workflow.owners import cp2h, valuation_basis
from deploy_workflow.owners.cpos_launch import SOURCE_SUFFIXES, pathway_modules
from deploy_workflow.run_expectations import (
    AGREEMENTS,
    FINANCIAL_KINDS,
    KINDS,
    edges_for,
)

ROOT = Path(__file__).resolve().parents[1]
FORM = (ROOT / "docs/templates/context-form.html").read_text(encoding="utf-8")
WEB = ROOT / "apps/issuer-library/credit_os/web"
# CP-DR and CP-2E are in every preset since 2026-11-11: the peer source no longer changes the run.
PEER_SOURCES = ("cp_dr_public", "user_comps")


def constant(name: str) -> str:
    """The literal of the form script's ``const NAME = ...;``."""
    match = re.search(rf"^const {name} = (.*?);$", FORM, re.MULTILINE | re.DOTALL)
    assert match is not None, f"the form has no const {name}"
    return match[1]


def lists(name: str) -> dict[str, list[str]]:
    """A ``{key: ['a', 'b']}`` table of the form's script."""
    rows = re.findall(r"(\w+): \[([^\]]*)\]", constant(name))
    return {key: re.findall(r"'([^']*)'", items) for key, items in rows}


def context(pathway: str, peer_source: str) -> RunContext:
    raw = json.loads((ROOT / "cases/context/research-minimal.json").read_text(encoding="utf-8"))
    raw["run"]["pathway"] = pathway
    raw["valuation"]["peer_source"] = peer_source
    if pathway == "earnings_update":
        raw["run"].update(run_type="earnings", current_period="q3-2026", prior_period="q2-2026")
    return load_context(json.dumps(raw).encode())


def launched(pathway: str, peer_source: str) -> list[str]:
    """What CP-OS runs for an inbox drop of this pathway and peer source, in order."""
    return list(plan(pathway_modules(context(pathway, peer_source))))


def test_the_pathways_are_the_contracts() -> None:
    assert lists("PATHWAYS") == {pathway: list(m) for pathway, m in PATHWAY_MODULES.items()}


@pytest.mark.parametrize("pathway", sorted(PATHWAY_MODULES))
def test_the_run_order_is_the_launchers_for_each_peer_source(pathway: str) -> None:
    order = lists("RUN_ORDER")[pathway]
    for peer_source in PEER_SOURCES:
        assert order == launched(pathway, peer_source)
    assert "WITH_RESEARCH" not in FORM


def test_the_dependency_edges_are_the_registrys() -> None:
    expected: dict[str, dict[str, str]] = {}
    for pathway in PATHWAY_MODULES:
        for peer_source in PEER_SOURCES:
            for consumer, producers in edges_for(launched(pathway, peer_source)).items():
                if producers:
                    edges = expected.setdefault(consumer, {})
                    edges.update({p: rule[0] for p, rule in producers.items()})
    assert json.loads(constant("EDGES")) == expected


def test_the_module_names_are_the_librarys() -> None:
    screen = (WEB / "screen.js").read_text(encoding="utf-8")
    match = re.search(r"const groups = \[(.*?)\n\];", screen, re.DOTALL)
    assert match is not None
    library = dict(re.findall(r"\['(CP-[\w-]+)','([^']+)'\]", match[1]))
    # CP-MODEL is not in the screen's groups: the library names it by views.js MODEL_ENTRY.
    entry = re.search(
        r"const MODEL_ENTRY=\['(CP-MODEL)','([^']+)'\]",
        (WEB / "views.js").read_text(encoding="utf-8"),
    )
    assert entry is not None
    library[entry[1]] = entry[2]
    form = dict(re.findall(r"^  '(CP-[\w-]+)': \['([^']+)'", constant("MODULES"), re.MULTILINE))
    assert form and form == {code: library[code] for code in form}


def test_the_library_screens_value_lists_are_the_codes() -> None:
    """The screens (views.js) copy value lists too: a value missing there reads "unknown" or
    "not recorded". Sweep 2026-11-10 (wiring)."""
    views = (WEB / "views.js").read_text(encoding="utf-8")

    def listed(name: str) -> list[str]:
        match = re.search(rf"\b{name}=\[([^\]]*)\]", views)
        assert match is not None, name
        return re.findall(r"'(\w+)'", match[1])

    def keyed(name: str) -> list[str]:
        match = re.search(rf"\b{name}=\{{([^}}]*)\}}", views)
        assert match is not None, name
        return re.findall(r"(\w+):'", match[1])

    statuses = list(get_args(Status))
    assert listed("LIVE_STATUSES") == statuses
    assert listed("ENDED_STATUSES") == [s for s in statuses if s not in ("queued", "running")]
    assert keyed("CLASSIFICATIONS") == [c for c in get_args(IssueClassification) if c]
    assert keyed("RATING_SCOPES") == list(get_args(RatingScope))


def test_the_rating_scales_are_cp2hs() -> None:
    scales = {a: sorted(s, key=s.__getitem__) for a, s in cp2h.COMBINED_SCALE.items()}
    assert json.loads(constant("SCALES")) == scales
    assert json.loads(constant("UNRATED")) == list(cp2h.UNRATED)


def test_the_limits_are_the_codes() -> None:
    numbers = {name: int(value) for name, value in re.findall(r"\b([A-Z_]+) = (\d+)\b", FORM)}
    assert {name: numbers[name] for name in ("STALE_DAYS", "MAX_ISSUER_ID")} == {
        "STALE_DAYS": cp3_relative_value.STALE_DAYS,
        "MAX_ISSUER_ID": MAX_ISSUER_ID,
    }
    assert [numbers[n] for n in ("PEER_MONTHS", "PRECEDENT_MONTHS", "MIN_ADMITTED")] == [
        valuation_basis.PEER_MONTHS,
        valuation_basis.PRECEDENT_MONTHS,
        valuation_basis.MIN_ADMITTED,
    ]
    assert set(re.findall(r"'([^']*)'", constant("SOURCE_SUFFIXES"))) == SOURCE_SUFFIXES


def form_limit(field: str) -> Limit:
    """The bounds the form's build() reads one pinned field with; a list's are its items'."""
    match = re.search(rf"\['{field}',\{{(.*?)\}}\]", FORM)
    assert match is not None, f"the form reads no pinned field {field}"
    props = dict(re.findall(r"(\w+):([\w.']+)", match[1]))
    return Limit(
        req=props.get("req") == "true",
        whole=props.get("int") == "true",
        places=int(props["dp"]) if "dp" in props else None,
        low=props.get("min"),
        low_excl=props.get("minEx"),
        high=props.get("max"),
        high_excl=props.get("maxEx"),
    )


@pytest.mark.parametrize("key", sorted(ASSUMPTION_LIMITS))
def test_the_pinned_limits_are_the_readers(key: str) -> None:
    assert form_limit(key.split(".")[1]) == ASSUMPTION_LIMITS[key]


def tokens(css: str) -> dict[str, str]:
    blocks = re.findall(r":root\{([^}]*)\}", css)
    return {k: v.strip() for b in blocks for k, v in re.findall(r"(--[\w-]+):([^;]+)", b)}


def test_the_design_tokens_are_the_librarys() -> None:
    library, form = tokens((WEB / "screen.css").read_text(encoding="utf-8")), tokens(FORM)
    shared = sorted(form.keys() & library.keys())
    # Only --ring-error, --red-bg, --red-border and the redesign's --green-bg are its own.
    assert len(shared) >= len(form) - 4
    assert set(form) - set(library) == {"--ring-error", "--red-bg", "--red-border", "--green-bg"}
    assert {k: form[k] for k in shared} == {k: library[k] for k in shared}


def test_the_stages_are_the_start_pages() -> None:
    assert re.findall(r"'([^']*)'", constant("STAGES")) == [
        "documents",
        "pathway",
        "issuer",
        "legal",
        "market",
        "valuation",
        "assumptions",
        "review",
    ]


def test_the_steps_lay_over_the_stages_in_their_order() -> None:
    steps = lists("STEPS")
    assert steps == {
        "documents": ["documents"],
        "purpose": ["pathway"],
        "confirm": ["issuer", "legal"],
        "more": ["market", "valuation", "assumptions"],
        "start": ["review"],
    }
    stages = re.findall(r"'([^']*)'", constant("STAGES"))
    assert [
        g for step in steps.values() for g in step
    ] == stages  # every group in one step, in order
    assert re.findall(r"(\w+):'([^']*)'", constant("STEP_NAME")) == [
        ("documents", "Documents"),
        ("purpose", "Purpose"),
        ("confirm", "Confirm"),
        ("more", "More context"),
        ("start", "Start"),
    ]
    sections = re.findall(r'<section class="run-step" id="st-(\w+)"', FORM)
    assert sections[: len(stages)] == stages  # the markup follows the same order


def test_the_cp3_modes_are_the_contexts() -> None:
    block = re.search(r"\bcp3_mode: \[(.*?)\n  \],", FORM, re.DOTALL)
    assert block is not None
    offered = re.findall(r"\{v:'(\w*)'", block[1])
    assert offered == [
        "",
        *[mode for mode in get_args(Cp3Mode) if mode],
    ]  # "" is "let the module decide"


def test_the_launchers_reading_is_the_run_expectations() -> None:
    assert re.findall(r"'([^']*)'", constant("AGREEMENTS")) == list(AGREEMENTS)
    assert re.findall(r"'([^']*)'", constant("FINANCIAL_KINDS")) == list(FINANCIAL_KINDS)
    labelled = re.findall(r"(\w+):'", constant("KIND_LABEL"))
    assert labelled == list(KINDS)  # Every kind the reading can name has a label, in its order.


def test_the_page_may_call_its_own_service_and_nothing_wider() -> None:
    meta = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', FORM)
    assert meta is not None
    policy = dict(part.strip().split(" ", 1) for part in meta[1].split(";") if part.strip())
    assert policy["connect-src"] == "'self'"
    assert policy["default-src"] == "'none'" and policy["form-action"] == "'none'"
    assert "http" not in meta[1]  # No external origin.
    assert not re.search(r"<(?:script|link)[^>]+(?:src|href)=[\"']https?:", FORM)


def test_the_rail_links_to_the_library_the_service_serves() -> None:
    assert 'href="/library/#W-Library/cases"' in FORM
    assert 'href="/library/#CP-OS/activity"' in FORM
    assert "data-pathway" not in FORM and "dataset.pathway" not in FORM  # No fixed-pathway copy.


def test_the_summary_tells_the_analyst_what_goes_to_openai_before_submit() -> None:
    lead = re.search(r'<p class="lead">(This is the run you are about to start.*?)</p>', FORM)
    assert lead is not None
    text = lead[1]
    assert "Pages of the documents you uploaded that modules read are sent to OpenAI" in text
    assert "web searches go to OpenAI's search" in text
    assert "told to search with public names only" in text
    assert "queries it actually sent are kept in the run record" in text
    assert "private case the issuer's name and the questions it researches" in text
    assert "use public names only and go to" not in FORM  # the old claim: nothing enforced it
    assert text.index("OpenAI") < FORM.index('id="approve"')
    assert "supplied files only" not in FORM


def test_the_page_states_before_submit_whether_the_run_searches_by_case_kind() -> None:
    assert "This is a private case: the research module will search the web" in FORM
    assert "This is a synthetic case: the research module does not search the web" in FORM
    assert "const SEARCH_KINDS = ['public', 'private'];" in FORM
    assert "['Web search'," in FORM


class _VisibleText(HTMLParser):
    """The markup's text nodes outside ``<script>`` and ``<style>``, whitespace collapsed."""

    def __init__(self) -> None:
        super().__init__()
        self.skipping = 0
        self.nodes: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.skipping += tag in ("script", "style")

    def handle_endtag(self, tag: str) -> None:
        self.skipping -= tag in ("script", "style")

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if text and not self.skipping:
            self.nodes.add(text)


# What Rulings 6-9 of the redesign plan change in the markup after the step logic: nothing.
# Ruling 6 (the title) and 9 (the group number) landed there; 8 (button labels) is script.
CHANGED_BY_RULINGS: frozenset[str] = frozenset()


def test_the_redesigned_markup_keeps_every_sentence_of_the_step_logic_commit() -> None:
    """The answer key is the markup text at a6eec82 (tests/fixtures), written down once: the frame,
    stepper, documents zone and pathway rows restyle the page without dropping a sentence."""
    before = json.loads(
        (ROOT / "tests/fixtures/run_start_sentences_a6eec82.json").read_text(encoding="utf-8")
    )
    page = _VisibleText()
    page.feed(FORM)
    assert len(before) > 100  # a fixture that lost its text would pass anything
    assert set(before) - CHANGED_BY_RULINGS <= page.nodes, sorted(
        set(before) - CHANGED_BY_RULINGS - page.nodes
    )


def _rule(selector: str) -> str:
    """The declarations of the stylesheet's rule for exactly ``selector``."""
    found = re.search(rf"(?:^|\}}|\n){re.escape(selector)}\{{([^}}]*)\}}", FORM)
    assert found is not None, f"the stylesheet has no rule for {selector}"
    return found[1]


def test_the_documents_zone_is_a_one_and_a_half_pixel_dashed_border() -> None:
    """Chrome snaps 1.5px to 1px at 1x, so the browser probe cannot tell the two apart."""
    assert "border:1.5px dashed var(--border-primary)" in _rule(".dropzone")


def test_the_canvas_leaves_no_bottom_padding_and_the_last_element_keeps_its_own_space() -> None:
    assert "padding:28px 32px 0;" in _rule("#canvas") + ";"
    assert "padding:28px 32px;" not in _rule("#canvas") + ";"
    assert "padding-bottom:28px" in _rule(".canvas-in")


def test_what_submit_does_is_the_one_new_heading_and_holds_the_submit_controls() -> None:
    card = re.search(r'<aside class="rv-card" id="rv-card"[^>]*>(.*?)</aside>', FORM, re.DOTALL)
    assert card is not None
    body = card[1]
    assert re.search(r"<h3[^>]*>What Submit does</h3>", body)
    for ident in ("approve", "rv-submit-error", "submit", "submitnote", "rv-facts"):
        assert f'id="{ident}"' in body, ident
    assert FORM.count("What Submit does") == 1


def test_the_page_has_no_skip_label_and_says_steps_not_stages_in_the_errors_sentence() -> None:
    assert "'Skip'" not in FORM and "enteredStep" not in FORM and "enteredGroup" not in FORM
    assert "Fix the steps marked Needs attention first." in FORM
    assert "Fix the stages marked" not in FORM
