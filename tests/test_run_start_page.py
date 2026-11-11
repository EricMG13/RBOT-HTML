"""The start page, served by the real service over the fake launcher, driven in headless Chrome.

Nothing here calls a provider. The service reads the page from ``startup.FORM`` on every request,
so each test serves the page with its probe script appended, exactly as the form's other browser
tests do. Uploading through a real file chooser cannot be scripted, so probes call the one
function the pickers call (``uploadFiles``) with ``File`` objects. Needs Google Chrome or
Chromium; skipped where there is none (then none of these tests is verified)."""

from __future__ import annotations

import json
import re
import subprocess
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from inbox_fixtures import settings
from test_library_page_browser import chrome

from deploy_workflow.inbox import startup
from deploy_workflow.inbox.watcher import Watcher
from deploy_workflow.run_start import service

pytest_plugins = ["inbox_fixtures"]
pytestmark = pytest.mark.browser

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "docs/templates/context-form.html"
RESEARCH_MINIMAL = json.loads((ROOT / "cases/context/research-minimal.json").read_text("utf-8"))

# Synthetic documents the launcher's own offline reading classifies by their cover lines.
AGREEMENT = "Credit Agreement\nEXECUTION VERSION\ndated as of March 1, 2024\nBetween the parties.\n"
REPORT = "Annual Report 2025\nFor the fiscal year ended December 31, 2025\nNet sales were 100.\n"
MEMO = "Meeting notes\nNothing here names a document.\n"

PRELUDE = """
const form = document.getElementById('f');
const fire = () => form.dispatchEvent(new Event('change', {bubbles: true}));
const pick = (attr, value) => {
  const el = document.querySelector(`[${attr}][value="${value}"]`);
  el.checked = true;
  el.dispatchEvent(new Event('change', {bubbles: true}));
};
const type = (id, value) => {
  const el = document.getElementById(id);
  el.value = value;
  el.dispatchEvent(new Event('input', {bubbles: true}));
};
const tick = k => {
  const el = document.querySelector(`[data-k="${k}"]`);
  el.checked = true;
  el.dispatchEvent(new Event('change', {bubbles: true}));
};
const choose = (id, value) => {
  const el = document.getElementById(id);
  el.value = value;
  el.dispatchEvent(new Event('change', {bubbles: true}));
};
const file = (name, text) => new File([text], name);
const stages = () => [...document.querySelectorAll('#stepper button')].map(b => b.dataset.step);
const level = value => pick('data-c="level"', value);
const radio = v => document.querySelector(`[data-k="legal_documents"][value="${v}"]`);
const rows = () => [...document.querySelectorAll('#doclist tbody tr')].map(r =>
  [...r.cells].map(c => c.textContent.trim()));
const limits = () => readiness(build()).counted.map(x => x.reason);
"""

WRAP = """<script>
(() => {
const done = value => {
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(value);
  document.body.append(out);
};
(async () => {
  try {
    await READY;
    done(await (async () => {
BODY
    })());
  } catch (error) {
    done({error: String(error && error.stack || error)});
  }
})();
})();
</script>
</body>"""


@dataclass
class Page:
    """The served start page; ``run`` loads it in Chrome with a probe and returns its value."""

    base: str
    folder: Path
    profile: Path
    console: list[str]

    def run(self, body: str) -> dict[str, Any]:
        text = FORM.read_text(encoding="utf-8")
        probe = WRAP.replace("BODY", PRELUDE + body)
        patched = self.folder / "form.html"
        patched.write_text(text.replace("</body>", probe, 1), encoding="utf-8")
        startup.FORM = patched
        done = subprocess.run(
            [
                chrome(),
                "--headless=new",
                "--disable-gpu",
                "--window-size=1280,900",
                "--enable-logging=stderr",
                "--v=0",
                f"--user-data-dir={self.profile}",
                "--virtual-time-budget=20000",
                "--dump-dom",
                self.base + "/",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        self.console[:] = re.findall(r"CONSOLE[^\n]*", done.stderr)
        found = re.search(r'<pre id="probe">(.*?)</pre>', done.stdout, re.DOTALL)
        assert found is not None, done.stdout[-2000:]
        import html

        value = json.loads(html.unescape(found[1]))
        assert "error" not in value, value["error"]
        return value  # type: ignore[no-any-return]


@pytest.fixture
def page(
    root: Path,
    fake_env: Callable[[dict[str, Any]], None],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Page]:
    chrome()  # skips here when there is no browser
    monkeypatch.setattr(startup, "FORM", FORM)
    fake_env({"sleep": 30})
    watcher = Watcher(settings(root))
    server = service.make_server(watcher, "127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    profile = tmp_path / "profile"
    profile.mkdir()
    folder = tmp_path / "served"
    folder.mkdir()
    try:
        yield Page(f"http://127.0.0.1:{server.server_address[1]}", folder, profile, [])
    finally:
        server.shutdown()
        server.server_close()
        watcher.close()


def test_basic_shows_five_stages_and_standard_and_advanced_add_theirs(page):
    seen = page.run("""
    const out = {};
    pick('data-k="pathway"', 'credit_snapshot');
    level('basic'); out.basic = stages();
    level('standard'); out.standard = stages();
    level('advanced'); out.advanced = stages();
    out.subset = {advanced: !document.getElementById('adv-run').hidden};
    level('basic'); out.subset.basic = !document.getElementById('adv-run').hidden;
    pick('data-k="pathway"', 'relative_value');
    level('basic'); out.rvBasic = stages();
    level('standard'); out.rvStandard = stages();
    pick('data-k="pathway"', 'covenant_refinancing');
    level('standard'); out.covStandard = stages();
    level('advanced'); out.covAdvanced = stages();
    return out;
    """)
    five = ["pathway", "documents", "issuer", "legal", "review"]
    assert seen["basic"] == five
    assert seen["standard"] == [
        "pathway",
        "documents",
        "issuer",
        "legal",
        "market",
        "valuation",
        "review",
    ]
    assert seen["advanced"] == seen["standard"]
    assert seen["subset"] == {"advanced": True, "basic": False}  # module subset and turns
    # Research questions come from Standard; pinned assumptions from Advanced.
    assert seen["rvBasic"] == ["pathway", "documents", "issuer", "review"]
    assert seen["rvStandard"] == [
        "pathway",
        "documents",
        "issuer",
        "market",
        "valuation",
        "assumptions",
        "review",
    ]
    assert seen["covStandard"] == five
    assert seen["covAdvanced"] == [
        "pathway",
        "documents",
        "issuer",
        "legal",
        "assumptions",
        "review",
    ]


def test_executed_cannot_be_chosen_until_an_uploaded_file_is_selected(page):
    seen = page.run(f"""
    const state = () => ({{executed: radio('executed').disabled, draft: radio('draft').disabled,
      none: radio('none').disabled, answer: build().attachments.legal_documents}});
    const out = {{before: state()}};
    await uploadFiles([file('credit-agreement.txt', {json.dumps(AGREEMENT)})]);
    out.uploaded = state();
    choose('legal-file', 'credit-agreement.txt');
    out.selected = state();
    choose('legal-file', '');
    out.cleared = state();
    return out;
    """)
    only_none = {"executed": True, "draft": True, "none": False, "answer": "none"}
    assert seen["before"] == only_none
    assert seen["uploaded"] == only_none  # An uploaded file is not yet the agreement.
    assert seen["selected"] == {
        "executed": False,
        "draft": False,
        "none": True,
        "answer": "executed",
    }
    assert seen["cleared"] == only_none


def test_a_file_the_launcher_does_not_recognise_as_an_agreement_adds_a_limit(page):
    seen = page.run(f"""
    await uploadFiles([file('credit-agreement.txt', {json.dumps(AGREEMENT)}),
      file('memo.txt', {json.dumps(MEMO)})]);
    // The limits that name an uploaded file (module-level ones, such as "draft only", name none).
    const legal = () => readiness(build()).counted
      .filter(x => x.go === 'legal' && x.reason.includes('.txt')).map(x => x.reason);
    const out = {{}};
    choose('legal-file', 'credit-agreement.txt'); out.agreement = legal();
    choose('legal-file', 'memo.txt'); out.memo = legal();
    choose('legal-file', 'credit-agreement.txt'); pick('data-k="legal_documents"', 'draft');
    out.contradicted = legal();
    choose('legal-file', ''); out.none = legal();
    return out;
    """)
    assert seen["agreement"] == []  # Read as an executed agreement, and executed is what was said.
    assert len(seen["memo"]) == 1 and "memo.txt" in seen["memo"][0]
    assert "not read as a credit agreement or indenture" in seen["memo"][0]
    assert len(seen["contradicted"]) == 1 and "credit-agreement.txt" in seen["contradicted"][0]
    assert "executed" in seen["contradicted"][0]
    assert (
        len(seen["none"]) == 1 and "credit-agreement.txt" in seen["none"][0]
    )  # Says none, reads one.


def test_an_as_of_date_before_the_newest_period_end_adds_a_limit(page):
    seen = page.run(f"""
    await uploadFiles([file('annual.txt', {json.dumps(REPORT)})]);
    const out = {{newest: document.getElementById('d-newest').value}};
    const before = () => limits().filter(r => r.includes('before your newest file'));
    type('d-as_of', '2025-06-30'); out.early = before();
    type('d-as_of', '2026-01-15'); out.late = before();
    return out;
    """)
    assert seen["newest"] == "2025-12-31"  # The reading's period end fills the newest-file date.
    assert len(seen["early"]) == 1 and "2025-06-30" in seen["early"][0]
    assert seen["late"] == []


def test_a_skipped_file_is_listed_as_will_not_be_read(page):
    seen = page.run(f"""
    await uploadFiles([file('annual.txt', {json.dumps(REPORT)}), file('deck.pptx', 'PK'),
      file('memo.txt', {json.dumps(MEMO)}), file('a&lt;b&amp;c.pptx', 'PK'),
      file('<i>\\\\..\\\\x.txt', 'x')]);  // The service refuses this one, quoting the name raw.
    const refused = document.getElementById('upload-errors');
    const italics = document.querySelectorAll('#upload-errors i, #doclist i').length;
    return {{rows: rows(), refused: refused.textContent, italics,
      hidden: refused.hidden}};
    """)
    by_name = {row[0]: row[1:] for row in seen["rows"]}
    assert "Will not be read" in by_name["deck.pptx"][0]
    assert "Will not be read" in by_name["a&lt;b&amp;c.pptx"][0]  # Shown as text, never as markup.
    assert not seen["hidden"] and "<i>" in seen["refused"]  # The refusal quotes the name as text.
    assert seen["italics"] == 0
    assert by_name["memo.txt"][0] == "Not recognised"
    assert "financial report" in by_name["annual.txt"][0].lower()
    assert "2025-12-31" in by_name["annual.txt"][0]


def test_an_empty_file_is_the_launchers_refusal_and_blocks_the_later_stages(page):
    seen = page.run(f"""
    await uploadFiles([file('annual.txt', {json.dumps(REPORT)}), file('blank.txt', '')]);
    const sq = [...document.querySelectorAll('#stepper button')]
      .map(b => [b.dataset.step, b.textContent]);
    return {{refusal: document.querySelector('#docf .fielderr').textContent, sq,
      rows: rows().length, blocked: errs.some(e => e.st === 'documents')}};
    """)
    assert "blank.txt" in seen["refusal"] and seen["blocked"]
    assert seen["rows"] == 0  # No reading while the folder is refused.
    states = {step: text for step, text in seen["sq"]}
    assert "Locked" in states["issuer"]


def test_the_three_levels_build_the_same_context_for_the_same_answers(page):
    seen = page.run("""
    type('i-issuer_name', 'Acme Corp'); type('d-as_of', '2026-10-31');
    pick('data-k="issue_classification"', 'high_yield');
    type('i-aliases', 'Acme\\nACM'); type('i-sponsor', 'Peak Capital');
    pick('data-k="cp3_mode"', 'single_name_rv');
    const built = {};
    for (const l of ['basic', 'standard', 'advanced', 'basic']) {
      level(l);
      built[l] = JSON.stringify(build());
    }
    return {same: new Set(Object.values(built)).size, level: LEVEL, built: JSON.parse(built.basic)};
    """)
    assert seen["same"] == 1 and seen["level"] == "basic"
    assert seen["built"]["identity"]["aliases"] == ["Acme", "ACM"]
    assert seen["built"]["module_options"] == {
        "cp3_mode": "single_name_rv",
        "cp6_deep_debate": False,
    }


def test_basic_builds_the_defaults_the_form_had(page):
    expected = json.loads(json.dumps(RESEARCH_MINIMAL))
    expected["run"]["cutoff"] = expected["run"]["as_of"]  # The form writes the cutoff, never blank.
    expected["identity"]["issue_classification"] = (
        "high_yield"  # The form asks it; the file did not.
    )
    seen = page.run(f"""
    level('basic');
    await uploadFiles([file('credit-agreement.txt', {json.dumps(AGREEMENT)})]);
    type('i-issuer_name', 'Northbridge Group'); type('d-as_of', '2026-10-31');
    pick('data-k="issue_classification"', 'high_yield');
    choose('legal-file', 'credit-agreement.txt');
    const built = build();
    return {{built, keys: Object.keys(built), problems: errs.map(e => e.msg)}};
    """)
    assert seen["problems"] == []
    assert seen["built"] == expected
    assert seen["keys"] == [
        "schema",
        "run",
        "identity",
        "deal_terms",
        "quotes",
        "ratings",
        "valuation",
        "assumptions",
        "attachments",
        "research_questions",
    ]  # module_options is last, and absent while both values are the defaults.


def test_module_options_come_last_when_set(page):
    seen = page.run("""
    level('standard');
    pick('data-k="cp3_mode"', 'watchlist_monitoring');
    const first = Object.keys(build());
    pick('data-k="cp3_mode"', '');
    tick('cp6_deep_debate');
    return {first, second: Object.keys(build()), options: build().module_options};
    """)
    assert seen["first"][-1] == "module_options" and seen["second"][-1] == "module_options"
    assert seen["options"] == {"cp3_mode": "", "cp6_deep_debate": True}


def test_a_reload_keeps_the_answers_and_the_uploaded_files(page):
    first = page.run(f"""
    await uploadFiles([file('credit-agreement.txt', {json.dumps(AGREEMENT)}),
      file('annual.txt', {json.dumps(REPORT)})]);
    level('standard');
    type('i-issuer_name', 'Acme Corp'); type('d-as_of', '2026-10-31');
    choose('legal-file', 'credit-agreement.txt');
    return {{rows: rows().length, saved: localStorage.length}};
    """)
    assert first == {"rows": 2, "saved": 1}
    second = page.run("""
    return {rows: rows().map(r => r[0]), level: LEVEL, name: build().identity.issuer_name,
      asOf: build().run.as_of, legalFile: document.getElementById('legal-file').value,
      legal: build().attachments.legal_documents, newest: document.getElementById('d-newest').value,
      stages: stages()};
    """)
    assert second["rows"] == ["annual.txt", "credit-agreement.txt"]
    assert second["level"] == "standard" and second["name"] == "Acme Corp"
    assert second["asOf"] == "2026-10-31"
    assert (second["legalFile"], second["legal"]) == ("credit-agreement.txt", "executed")
    assert second["newest"] == "2025-12-31"
    assert "market" in second["stages"]


def test_removing_a_document_deletes_it_from_the_service_and_keeps_the_answers(page):
    page.run(f"""
    await uploadFiles([file('annual.txt', {json.dumps(REPORT)})]);
    type('i-issuer_name', 'Acme Corp');
    return {{}};
    """)
    seen = page.run("""
    document.querySelector('#doclist [data-remove-file]').click();
    await new Promise(r => setTimeout(r, 500));
    return {rows: rows().length, name: build().identity.issuer_name,
      status: document.getElementById('docstatus').textContent};
    """)
    assert seen["rows"] == 0 and seen["name"] == "Acme Corp"


def test_changing_level_keeps_answers(page):
    seen = page.run("""
    level('advanced');
    type('i-aliases', 'Acme\\nACM'); type('i-guarantors', 'Opco LLC');
    pick('data-k="cp3_mode"', 'clo_screening');
    tick('cp6_deep_debate');
    pick('data-k="basis"', 'precedents');
    type('turns', '12');
    level('basic');
    const b = build();
    const hidden = {aliases: document.getElementById('i-aliases').closest('.f').hidden};
    level('advanced');
    return {aliases: b.identity.aliases, guarantors: b.identity.guarantors,
      options: b.module_options,
      basis: b.valuation.basis, turns: answers().max_turns, hidden,
      shownAgain: !document.getElementById('i-aliases').closest('.f').hidden};
    """)
    assert seen["aliases"] == ["Acme", "ACM"] and seen["guarantors"] == ["Opco LLC"]
    assert seen["options"] == {"cp3_mode": "clo_screening", "cp6_deep_debate": True}
    assert seen["basis"] == "precedents" and seen["turns"] == 12
    assert seen["shownAgain"]


def test_a_started_page_makes_no_request_that_the_policy_blocks(page):
    page.run("return {};")
    assert [m for m in page.console if "Content Security Policy" in m] == []


def test_the_pathway_stage_takes_the_name_and_the_answers_object_is_the_services(page):
    seen = page.run("""
    type('submitter', 'Dana');
    pick('data-k="pathway"', 'credit_snapshot');
    const a = answers();
    return {keys: Object.keys(a).sort(), by: a.submitted_by, level: a.level, turns: a.max_turns,
      modules: a.modules, context: a.context.schema};
    """)
    assert seen["keys"] == ["context", "level", "max_turns", "modules", "submitted_by"]
    assert (seen["by"], seen["level"], seen["turns"], seen["modules"]) == ("Dana", "basic", 32, [])
    assert seen["context"] == "context/1"
