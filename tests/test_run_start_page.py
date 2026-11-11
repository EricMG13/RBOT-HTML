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
import sys
import threading
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from inbox_fixtures import settings
from test_library_page_browser import chrome

from deploy_workflow.inbox import startup
from deploy_workflow.inbox.scheduler import Scheduler
from deploy_workflow.owners.cpos_launch import (
    update_library_at,
)  # the real one, before any test patches it
from deploy_workflow.run_start import service

pytest_plugins = ["inbox_fixtures"]
pytestmark = pytest.mark.browser

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "docs/templates/context-form.html"
RESEARCH_MINIMAL = json.loads((ROOT / "cases/context/research-minimal.json").read_text("utf-8"))

# Synthetic documents the launcher's own offline reading classifies by their cover lines.
AGREEMENT = "Credit Agreement\nEXECUTION VERSION\ndated as of March 1, 2024\nBetween the parties.\n"
REPORT = "Annual Report 2025\nFor the fiscal year ended December 31, 2025\nNet sales were 100.\n"
DRAFT = "Credit Agreement\nDRAFT\ndated as of March 1, 2024\nBetween the parties.\n"
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
const settle = ms => new Promise(r => setTimeout(r, ms));
// Answers a pathway's first stages the way an analyst would, then opens the review and waits
// for the service's summary (the page asks for it on entering the review).
const issuer = async (pathway, docs) => {
  pick('data-k="pathway"', pathway);
  await uploadFiles(docs);
  type('i-issuer_name', 'Acme Corp'); type('d-as_of', '2026-10-31');
  pick('data-k="issue_classification"', 'high_yield');
};
const summarised = async () => {
  for (let i = 0; i < 300 && !(SUMMARY && !SUMMARY_BUSY); i++) await settle(50);
  return SUMMARY;
};
const review = async () => { gotoStep('review'); return summarised(); };
const ticks = () => [...document.querySelectorAll('#rv-ready [data-tick]')];
const change = el => el.dispatchEvent(new Event('change', {bubbles: true}));
const tickAll = () => ticks().forEach(t => { t.checked = true; change(t); });
const $ = id => document.getElementById(id);
const approve = () => { const a = $('approve'); a.checked = true; change(a); };
const gate = () => ({approve: document.getElementById('approve').disabled,
  approved: document.getElementById('approve').checked,
  submit: document.getElementById('submit').disabled});
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
    root: Path | None = None  # the shared folder, for tests that read the service's records

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


@contextmanager
def _serving(root: Path, tmp_path: Path, **changes: Any) -> Iterator[tuple[Page, Scheduler]]:
    watcher = Scheduler(settings(root, **changes))
    server = service.make_server(watcher, "127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    profile = tmp_path / "profile"
    profile.mkdir()
    folder = tmp_path / "served"
    folder.mkdir()
    try:
        yield (
            Page(f"http://127.0.0.1:{server.server_address[1]}", folder, profile, [], root),
            watcher,
        )
    finally:
        server.shutdown()
        server.server_close()
        watcher.close()


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
    with _serving(root, tmp_path) as (served, _watcher):
        yield served


@pytest.fixture
def page_with_launcher(
    root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Callable[[str], tuple[Page, Scheduler]]]:
    """The served page over a launcher script of the test's choice (the real one, canned)."""
    chrome()
    monkeypatch.setattr(startup, "FORM", FORM)
    stack = ExitStack()

    def start(launcher: str) -> tuple[Page, Scheduler]:
        return stack.enter_context(_serving(root, tmp_path, launcher=(sys.executable, launcher)))

    with stack:
        yield start


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
      .filter(x => x.scope === 'run' && x.go === 'legal' && x.reason.includes('.txt'))
      .map(x => x.reason);
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
    assert seen["hidden"] == {"aliases": False}  # An answered field is never hidden.


def test_a_started_page_makes_no_request_that_the_policy_blocks(page):
    # A same-origin fetch is what the policy's connect-src must allow; the page's own calls are the
    # service's, so the probe makes one and expects it to succeed.
    seen = page.run("""
    const res = await fetch('/', {cache: 'no-store'});
    return {ok: res.ok, status: res.status};
    """)
    assert seen == {"ok": True, "status": 200}
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


def _forecast(page, body):
    """The module statuses and the headline the panel shows after ``body`` has answered the page."""
    return page.run(
        body
        + """
    update();
    return {status: Object.fromEntries(readiness(build()).mods.map(m => [m.id, m.status])),
      run: readiness(build()).run.map(x => x.reason),
      headline: document.getElementById('pn-sum').textContent.trim(),
      reasons: Object.fromEntries(readiness(build()).mods
        .map(m => [m.id, m.items.map(i => i.reason)]))};
    """
    )


def test_a_file_chosen_as_executed_that_the_launcher_does_not_recognise_is_not_ready(page):
    seen = _forecast(
        page,
        f"""
    pick('data-k="pathway"', 'covenant_refinancing');
    await uploadFiles([file('memo.txt', {json.dumps(MEMO)})]);
    choose('legal-file', 'memo.txt');""",
    )
    assert seen["status"]["CP-4"] == "check"  # cp4-declared-executed-none-recognised
    assert any("memo.txt" in r and "recognises no executed" in r for r in seen["reasons"]["CP-4"])
    assert "Ready" not in seen["headline"], seen["headline"]


def test_an_executed_answer_against_a_draft_reading_is_not_ready(page):
    seen = _forecast(
        page,
        f"""
    pick('data-k="pathway"', 'covenant_refinancing');
    await uploadFiles([file('draft-agreement.txt', {json.dumps(DRAFT)})]);
    choose('legal-file', 'draft-agreement.txt');
    pick('data-k="legal_documents"', 'executed');""",
    )
    assert len(seen["run"]) == 1 and "draft-agreement.txt" in seen["run"][0]
    assert "reads it as a draft" in seen["run"][0]
    assert seen["status"]["CP-4"] != "ready"
    assert "draft-agreement.txt" in " ".join(seen["reasons"]["CP-4"])
    assert "Ready" not in seen["headline"], seen["headline"]


def test_an_executed_agreement_chosen_as_executed_keeps_the_legal_module_ready(page):
    seen = _forecast(
        page,
        f"""
    pick('data-k="pathway"', 'covenant_refinancing');
    await uploadFiles([file('credit-agreement.txt', {json.dumps(AGREEMENT)}),
      file('annual.txt', {json.dumps(REPORT)})]);
    choose('legal-file', 'credit-agreement.txt');""",
    )
    assert seen["status"]["CP-4"] == "ready"
    assert seen["headline"] == "Ready", seen


def test_two_reports_of_one_period_do_not_make_the_period_comparison_ready(page):
    seen = _forecast(
        page,
        f"""
    pick('data-k="pathway"', 'earnings_update');
    await uploadFiles([file('annual.txt', {json.dumps(REPORT)}),
      file('annual-copy.txt', {json.dumps(REPORT)})]);
    type('d-current_period', 'fy-2025'); type('d-prior_period', 'fy-2024');""",
    )
    # The reading states kind and period end, not which periods the pair covers.
    assert seen["status"]["CP-1B"] == "check"
    assert "confirmed when the summary is made" in " ".join(seen["reasons"]["CP-1B"])
    assert "Ready" not in seen["headline"], seen["headline"]


def test_a_report_does_not_make_the_guidance_forecast_ready(page):
    seen = _forecast(
        page,
        f"""
    pick('data-k="pathway"', 'distressed_restructuring');
    await uploadFiles([file('annual.txt', {json.dumps(REPORT)})]);""",
    )
    # The reading does not say whether guidance is stated; other rules may make it worse.
    assert seen["status"]["CP-2G"] != "ready"
    assert "confirmed when the summary is made" in " ".join(seen["reasons"]["CP-2G"])


def test_a_limit_that_points_to_the_legal_stage_offers_the_stage(page):
    seen = page.run(
        f"""
    pick('data-k="pathway"', 'relative_value');
    await uploadFiles([file('credit-agreement.txt', {json.dumps(AGREEMENT)})]);
    const go = readiness(build()).counted.filter(x => x.go === 'legal').length;
    return {{stages: stages(), go}};"""
    )
    assert seen["go"] == 1 and "legal" in seen["stages"]


def test_a_stage_holding_an_answer_is_shown_at_every_level(page):
    seen = page.run("""
    pick('data-k="pathway"', 'relative_value');
    level('standard');
    // A complete row, so that no error is what keeps the stage on screen.
    const row = addRow('quote');
    const set = (k, v) => {
      const el = row.querySelector(`[data-k="${k}"]`);
      el.value = v;
      el.dispatchEvent(new Event('input', {bubbles: true}));
    };
    set('facility_id', 'tlb-2031'); set('price', '99'); set('provider', 'Dealer run');
    set('as_of', '2026-10-30'); type('d-as_of', '2026-10-31');
    const kind = row.querySelector('[data-k="kind"]');
    kind.checked = true;
    kind.dispatchEvent(new Event('change', {bubbles: true}));
    level('basic');
    return {stages: stages(), rows: build().quotes.length, errs: errs.map(e => e.st)};
    """)
    assert seen["rows"] == 1 and "market" not in seen["errs"]
    assert "market" in seen["stages"]


def _records(page):
    from deploy_workflow.inbox.layout import Layout
    from deploy_workflow.inbox.runs import load_all

    assert page.root is not None
    return load_all(Layout(page.root))


# The outcomes that need a tick, one per item (the owner's ruling for the review).
LIMITS = ("gap", "limited", "will_refuse")
ORDER = ["will_refuse", "gap", "limited", "check", "information", "ready"]


def test_the_review_shows_the_services_forecast_per_module(page):
    seen = page.run(f"""
    await issuer('credit_snapshot', [file('annual.txt', {json.dumps(REPORT)})]);
    const S = await review();
    const mrows = [...document.querySelectorAll('#rv-ready [data-module]')].map(r => ({{
      id: r.dataset.module, outcome: r.dataset.outcome, text: r.textContent}}));
    const goto = [...document.querySelectorAll('#rv-ready [data-module="CP-4"] [data-goto]')]
      .map(b => [b.dataset.goto, b.textContent]);
    return {{S, rows: mrows, goto, facts: document.getElementById('rv-facts').textContent,
      ready: document.getElementById('rv-ready').textContent,
      panel: document.getElementById('panel').hidden}};
    """)
    summary = seen["S"]
    assert summary["error"] == "" and summary["digest"]
    shown = [r["id"] for r in seen["rows"] if r["id"] != "run"]
    assert shown == summary["modules"]  # the service's order, not the page's own
    by_module = {r["id"]: r for r in seen["rows"]}
    for module in summary["modules"]:
        own = [i["outcome"] for i in summary["items"] if i["scope"] == module]
        want = min(own, key=ORDER.index) if own else "ready"
        assert by_module[module]["outcome"] == want, module
    for item in summary["items"]:  # every reason the service gave is shown
        assert item["reason"] in seen["ready"]
    assert by_module["CP-4"]["outcome"] == "will_refuse"  # legal documents: none, on CP-4
    assert ["legal", "Go to Legal"] in seen["goto"]
    for text in ("sol-medium", "USD 20", "Acme Corp", "2026-10-31", "1 read"):
        assert text in seen["facts"], text
    for section in summary["omitted"]:
        assert section in seen["facts"]
    assert "confirmed when the summary is made" not in seen["ready"]


def test_the_services_outcome_replaces_the_confirmed_when_the_summary_is_made_check(page):
    seen = page.run(f"""
    await issuer('earnings_update', [file('annual.txt', {json.dumps(REPORT)}),
      file('annual-copy.txt', {json.dumps(REPORT)})]);
    type('d-current_period', 'fy-2025'); type('d-prior_period', 'fy-2024');
    update();
    const before = readiness(build()).mods.find(m => m.id === 'CP-1B').items.map(i => i.reason);
    const S = await review();
    const row = document.querySelector('#rv-ready [data-module="CP-1B"]');
    return {{before, S, text: row.textContent, outcome: row.dataset.outcome}};
    """)
    assert any("confirmed when the summary is made" in r for r in seen["before"])
    assert "confirmed when the summary is made" not in seen["text"]
    own = [i for i in seen["S"]["items"] if i["scope"] == "CP-1B"]
    for item in own:
        assert item["reason"] in seen["text"]
    want = min((i["outcome"] for i in own), key=ORDER.index) if own else "ready"
    assert seen["outcome"] == want


def test_every_rule_the_service_can_fire_has_a_stage_on_the_page(page):
    from deploy_workflow.run_expectations import RULES

    seen = page.run("return {map: STAGE_OF_RULE, stages: STAGES};")
    assert sorted(seen["map"]) == sorted(r.key for r in RULES)
    assert set(seen["map"].values()) <= set(seen["stages"]) | {""}  # "" = no stage fixes it


def test_a_limit_must_be_ticked_before_approval_and_an_error_blocks_it(page):
    seen = page.run(f"""
    await issuer('credit_snapshot', [file('annual.txt', {json.dumps(REPORT)})]);
    const S = await review();
    const out = {{S, start: gate(), n: ticks().length,
      rowOutcomes: ticks().map(t => t.closest('[data-module]').dataset.outcome)}};
    const all = ticks();
    all.slice(1).forEach(t => {{ t.checked = true; change(t); }});
    out.partial = gate();
    all[0].checked = true; change(all[0]);
    out.ticked = gate();
    approve();
    out.approved = gate();
    all[0].checked = false; change(all[0]);
    out.untick = gate();
    // A refusal the service makes (a name longer than it accepts) blocks approval.
    document.getElementById('submitter').value = 'x'.repeat(500);
    change(document.getElementById('submitter'));
    gotoStep('review');
    out.after = await summarised();
    out.refusal = {{state: document.getElementById('rv-state').textContent, gate: gate(),
      links: [...document.querySelectorAll('#rv-state [data-goto]')].map(b => b.dataset.goto),
      ticks: ticks().length}};
    return out;
    """)
    need = [i for i in seen["S"]["items"] if i["outcome"] in LIMITS]
    assert need and seen["n"] == len(need)  # one tick per gap, limited or will-refuse item
    assert set(seen["rowOutcomes"]) <= set(LIMITS)
    assert seen["start"] == {"approve": True, "approved": False, "submit": True}
    assert seen["partial"]["approve"] is True  # one tick still missing
    assert seen["ticked"] == {"approve": False, "approved": False, "submit": True}
    assert seen["approved"] == {"approve": False, "approved": True, "submit": False}
    assert seen["untick"] == {"approve": True, "approved": False, "submit": True}
    assert seen["after"]["error"] and "digest" not in seen["after"]
    assert "80 characters" in seen["refusal"]["state"]  # the service's own sentence, as text
    assert seen["refusal"]["gate"] == {"approve": True, "approved": False, "submit": True}
    assert seen["refusal"]["links"] == ["pathway"] and seen["refusal"]["ticks"] == 0


def test_basic_lists_its_defaults_and_offers_answer_this_now(page):
    seen = page.run(f"""
    level('basic');
    await issuer('relative_value', [file('annual.txt', {json.dumps(REPORT)})]);
    const S = await review();
    const before = stages();
    const button = document.querySelector('#rv-ready [data-now]');
    const out = {{S, before, defaults: document.getElementById('rv-defaults').textContent,
      now: button ? [button.dataset.now, button.textContent] : null}};
    button.click();
    out.after = {{cur, level: LEVEL, stages: stages()}};
    level('standard');
    gotoStep('review'); await summarised();
    out.standard = document.getElementById('rv-defaults').textContent;
    out.standardNow = document.querySelectorAll('#rv-ready [data-now]').length;
    return out;
    """)
    quotes = [i for i in seen["S"]["items"] if i["id"].endswith(":cp3-no-quotes-no-talk")]
    assert quotes and quotes[0]["outcome"] == "gap"  # the fix is in the Market stage
    assert "market" not in seen["before"]  # which Basic does not ask
    assert seen["now"] == ["market", "Answer this now"]
    assert seen["after"]["cur"] == "market" and seen["after"]["level"] == "basic"
    assert "market" in seen["after"]["stages"]
    for text in ("Peer figures", "Valuation basis", "Automatic", "Quotes", "Ratings", "None"):
        assert text in seen["defaults"], text
    assert "Deep Debate" in seen["defaults"] and "Off" in seen["defaults"]
    assert "Valuation basis" in seen["standard"]  # Standard still defaults the basis
    assert "Quotes" not in seen["standard"] and seen["standardNow"] == 0


def test_editing_after_approval_clears_it(page):
    seen = page.run(f"""
    await issuer('credit_snapshot', [file('annual.txt', {json.dumps(REPORT)}),
      file('memo.txt', {json.dumps(MEMO)})]);
    const first = await review();
    tickAll(); approve();
    const out = {{approved: gate()}};
    type('i-issuer_name', 'Acme Corp II');
    out.answer = {{gate: gate(), digest: SUMMARY ? SUMMARY.digest : null, ticks: ticks().length}};
    const second = await summarised();
    out.second = {{gate: gate(), differs: second.digest !== first.digest, ticks: ticks().length,
      checked: ticks().filter(t => t.checked).length}};
    tickAll(); approve();
    out.again = gate();
    await removeFile('memo.txt');
    out.file = {{gate: gate(), summary: SUMMARY ? SUMMARY.digest : null}};
    gotoStep('review');
    const third = await summarised();
    out.third = {{gate: gate(), differs: third.digest !== second.digest}};
    return out;
    """)
    assert seen["approved"] == {"approve": False, "approved": True, "submit": False}
    assert seen["answer"]["gate"] == {"approve": True, "approved": False, "submit": True}
    assert seen["answer"]["digest"] != "" and seen["answer"]["ticks"] in (
        0,
        seen["second"]["ticks"],
    )
    assert seen["second"]["gate"]["approved"] is False and seen["second"]["differs"]
    assert seen["second"]["checked"] == 0  # a new summary needs its ticks again
    assert seen["again"] == {"approve": False, "approved": True, "submit": False}
    assert seen["file"]["gate"] == {"approve": True, "approved": False, "submit": True}
    assert seen["third"]["differs"] and seen["third"]["gate"]["approved"] is False


def _submit(page, count):
    return page.run(f"""
    const calls = [];
    const real = window.fetch;
    window.fetch = (path, init) => {{ calls.push(String(path)); return real(path, init); }};
    await issuer('credit_snapshot', [file('annual.txt', {json.dumps(REPORT)})]);
    await review();
    tickAll(); approve();
    const sid = SUB, out = {{start: gate()}};
    const button = document.getElementById('submit');
    for (let i = 0; i < {count}; i++) {{ button.click(); submitRun(); }}  // click and function
    out.clicked = gate();
    for (let i = 0; i < 200 && $('run-progress').hidden; i++) await settle(50);
    out.submits = calls.filter(c => c.endsWith('/submit')).length;
    out.progress = {{hidden: document.getElementById('run-progress').hidden,
      text: document.getElementById('run-progress').textContent,
      form: document.getElementById('f').hidden,
      id: document.getElementById('run-id').textContent,
      modules: [...document.querySelectorAll('#run-progress [data-module]')]
        .map(m => [m.dataset.module, m.dataset.state]),
      link: [...document.querySelectorAll('#run-progress a')]
        .map(a => [a.getAttribute('href'), a.textContent])}};
    out.storage = Object.keys(localStorage);
    const late = await fetch(`/api/submissions/${{sid}}/files?name=late.txt`,
      {{method: 'POST', body: 'x'}});
    out.late = [late.status, (await late.json()).error];
    return out;
    """)


def test_submit_starts_one_run_and_the_page_shows_its_progress(page):
    seen = _submit(page, 1)
    [record] = _records(page)
    assert seen["start"] == {"approve": False, "approved": True, "submit": False}
    assert seen["clicked"]["submit"] is True  # disabled from the first click
    assert seen["submits"] == 1
    progress = seen["progress"]
    assert not progress["hidden"] and progress["form"] is True
    assert progress["id"] == record.id and "queued" in progress["text"]
    assert next(m for m, _ in progress["modules"]) == "CP-0"
    assert [m for m, _ in progress["modules"]][-1] == "Report"
    assert {state for _, state in progress["modules"]} == {"waiting"}
    assert ["/library/#CP-OS/activity", "Run activity"] in progress["link"]
    assert seen["storage"] == ["run-start/run"]  # the answers and submission id are forgotten
    # The service releases the folder once the files move to the run, so it answers "unknown
    # submission" (404); "this submission has been submitted" (400) holds between seal and release.
    assert seen["late"][0] in (400, 404) and seen["late"][1] in (
        "unknown submission",
        "this submission has been submitted",
    )
    again = page.run("""
    return {hidden: document.getElementById('run-progress').hidden,
      id: document.getElementById('run-id').textContent, form: document.getElementById('f').hidden,
      storage: Object.keys(localStorage),
      rows: document.querySelectorAll('#doclist tbody tr').length};
    """)
    assert again == {
        "hidden": False,
        "id": record.id,
        "form": True,
        "storage": ["run-start/run"],
        "rows": 0,
    }


def test_a_double_click_on_submit_starts_one_run(page):
    seen = _submit(page, 3)
    assert seen["submits"] == 1
    assert len(_records(page)) == 1


def test_a_refused_digest_returns_to_the_review_with_the_services_text(page):
    seen = page.run(f"""
    await issuer('credit_snapshot', [file('annual.txt', {json.dumps(REPORT)})]);
    await review();
    tickAll(); approve();
    // A file added behind the page's back: the digest the page holds no longer matches the files.
    await fetch(`/api/submissions/${{SUB}}/files?name=sneaky.txt`, {{method: 'POST', body: 'x'}});
    document.getElementById('submit').click();
    for (let i = 0; i < 100 && !$('rv-submit-error').textContent; i++) await settle(50);
    return {{refusal: document.getElementById('rv-submit-error').textContent, gate: gate(),
      hidden: $('run-progress').hidden, stage: cur, storage: Object.keys(localStorage)}};
    """)
    assert "changed after approval" in seen["refusal"]
    assert seen["gate"]["approved"] is False and seen["gate"]["submit"] is True
    assert seen["hidden"] is True and seen["stage"] == "review"
    assert "run-start/run" not in seen["storage"]
    assert _records(page) == []


def test_the_documents_changed_error_is_retried_not_shown(page):
    seen = page.run(f"""
    await issuer('credit_snapshot', [file('annual.txt', {json.dumps(REPORT)})]);
    const real = window.fetch;
    let n = 0;
    window.fetch = async (path, init) => {{
      if (String(path).endsWith('/summary') && n++ === 0) {{
        await real(path, init);  // the real summary runs, then the first answer is lost
        const lost = 'the documents changed while the summary was being made; '
          + 'open the summary again';
        return new Response(JSON.stringify({{error: lost}}),
          {{status: 200, headers: {{'Content-Type': 'application/json'}}}});
      }}
      return real(path, init);
    }};
    const S = await review();
    return {{n, refusal: S.error, digest: !!S.digest, state: $('rv-state').textContent}};
    """)
    assert seen["n"] == 2 and seen["refusal"] == "" and seen["digest"]
    assert "changed while" not in seen["state"]


def test_the_research_text_is_fixed(page):
    seen = page.run("""
    pick('data-k="pathway"', 'relative_value');
    return {text: document.querySelector('#research-src .strip-text').textContent};
    """)
    assert seen["text"] == (
        "Research works from the supplied files only. "
        "Add peers' filings to the documents if you want them used."
    )


def test_upload_to_filed_report_with_the_real_launcher(
    root, tmp_path, monkeypatch, page_with_launcher
):
    # No provider is called: the launcher is the real one with canned module answers.
    from inbox_fixtures import HERE, layout, pump, status
    from test_cpos_launch import AS_OF, ISSUER, issuer_folder

    from deploy_workflow.inbox.runs import load_all
    from deploy_workflow.owners import cpos_launch

    monkeypatch.setattr(cpos_launch, "update_library_at", update_library_at)
    folder = issuer_folder(tmp_path)
    body = "\n".join(
        f"await uploadFiles([file({json.dumps(p.name)}, {json.dumps(p.read_text())})]);"
        for p in sorted(folder.rglob("*.*"))
        if p.suffix in (".txt", ".md")
    )
    page, watcher = page_with_launcher(str(HERE / "fixtures/canned_provider_launcher.py"))
    first = page.run(f"""
    level('basic');
    pick('data-k="pathway"', 'credit_snapshot');
    {body}
    await uploadFiles([file('credit-agreement.txt', {json.dumps(AGREEMENT)})]);
    choose('legal-file', 'credit-agreement.txt');
    // The canned answers name this issuer and date (tests/test_cpos_launch.py ISSUER, AS_OF).
    type('i-issuer_name', {json.dumps(ISSUER)}); type('d-as_of', {json.dumps(AS_OF)});
    pick('data-k="issue_classification"', 'high_yield');
    await review();
    tickAll(); approve();
    document.getElementById('submit').click();
    for (let i = 0; i < 200 && $('run-progress').hidden; i++) await settle(50);
    return {{id: document.getElementById('run-id').textContent, ticks: ticks().length}};
    """)
    pump(watcher, lambda: status(root) not in ([], ["queued"], ["running"]), limit=120)
    [record] = load_all(layout(root))
    assert record.id == first["id"]
    assert record.status == "finished", record.reason
    assert record.report.startswith("issuers/") or "/issuers/" in record.report
    assert (root / record.report).is_file()
    assert f'"{record.id}"' in (root / "_engine/library/data.js").read_text(encoding="utf-8")
    after = page.run("""
    const text = () => $('run-progress').textContent;
    for (let i = 0; i < 100 && !/finished/.test(text()); i++) await settle(100);
    return {text: document.getElementById('run-progress').textContent,
      modules: [...document.querySelectorAll('#run-progress [data-module]')]
        .map(m => m.dataset.state)};
    """)
    assert "finished" in after["text"]
    assert set(after["modules"]) == {"done"}
