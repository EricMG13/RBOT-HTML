"""The update script: one self-contained page, written only to library/, from synthetic runs."""

import json
import re
import sys
from pathlib import Path

import pytest
from library_fixtures import make_run, method

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library

HOSTILE = '</script><script>alert(1)</script><!-- & "quoted"  '
STAMP = "09 Nov 2026, 12:00 UTC"


@pytest.fixture
def stand_in_method(monkeypatch):
    """The synthetic runs' method stands in for the launcher's current one."""
    monkeypatch.setattr("deploy_workflow.library_index.current_method", lambda: method())


def page_data(html: str) -> dict:
    match = re.search(
        r'<script id="library-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert match, "the data block must end at its own closing tag"
    return json.loads(match[1])


def tree(folder: Path) -> dict[str, bytes]:
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def test_the_page_is_written_only_to_library_and_holds_everything_it_needs(
    tmp_path, stand_in_method
):
    make_run(tmp_path, "run-a")
    before = tree(tmp_path)
    target, _ = update_library.update(tmp_path, built_at=STAMP)
    after = tree(tmp_path)
    assert target == tmp_path.resolve() / "library/index.html"
    assert {k: v for k, v in after.items() if not k.startswith("library/")} == before
    assert [k for k in after if k.startswith("library/")] == ["library/index.html"]
    html = target.read_text(encoding="utf-8")
    # Nothing is fetched: no src other than data:, no remote href, url() or @import.
    assert "connect-src 'none'" in html
    assert re.findall(r'\bsrc="(?!data:)', html) == []
    assert re.findall(r'(?:href=["\']?|url\(["\']?|@import\s+["\']?)(?:https?:)?//', html) == []
    data = page_data(html)
    assert data["built_at"] == STAMP
    assert [r["id"] for r in data["runs"]] == ["run-a"]
    assert data["runs"][0]["report"]["href"].startswith("../runs/run-a/deliveries/")


def test_same_inputs_give_the_same_page(tmp_path, stand_in_method):
    make_run(tmp_path, "run-a")
    make_run(tmp_path, "run-b", issuer_id="zzz", issuer_name="Zeta Synthetic")
    first = update_library.update(tmp_path, built_at=STAMP)[0].read_bytes()
    second = update_library.update(tmp_path, built_at=STAMP)[0].read_bytes()
    assert first == second


def test_hostile_run_text_cannot_leave_the_data_block(tmp_path, stand_in_method):
    make_run(tmp_path, "run-a", issuer_name=HOSTILE)
    (tmp_path / "runs" / "<script>alert(1)<!--").mkdir(parents=True)
    html = update_library.update(tmp_path, built_at=STAMP)[0].read_text(encoding="utf-8")
    template = (ROOT / "apps/issuer-library/static/template.html").read_text(encoding="utf-8")
    assert html.count("</script>") == template.count("</script>")
    assert html.count("<!--") == template.count("<!--")
    data = page_data(html)
    assert data["runs"][0]["issuer_name"] == HOSTILE
    assert {n["folder"] for n in data["not_shown"]} == {"<script>alert(1)<!--"}


def test_an_empty_workspace_still_gets_a_page_that_says_so(tmp_path, stand_in_method):
    target, library = update_library.update(tmp_path, built_at=STAMP)
    assert library.runs == [] and library.excluded == []
    assert page_data(target.read_text(encoding="utf-8"))["runs"] == []


def test_the_command_reports_what_it_listed_and_why_others_are_not_shown(
    tmp_path, stand_in_method, capsys
):
    make_run(tmp_path, "run-a")
    (tmp_path / "runs/legacy").mkdir()
    assert update_library.main(["--workspace", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Listed 1 run(s) on the current methodology." in out
    assert "  legacy: not a CP-OS launcher run (no workflow.json)" in out
    assert str(tmp_path.resolve() / "library/index.html") in out


def test_a_linked_library_folder_is_not_written_through(tmp_path, stand_in_method):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    workspace = tmp_path / "workspace"
    (workspace / "runs").mkdir(parents=True)
    (workspace / "library").symlink_to(elsewhere)
    with pytest.raises(SystemExit, match="is a link or a file"):
        update_library.update(workspace, built_at=STAMP)
    assert list(elsewhere.iterdir()) == []


def test_a_missing_workspace_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="Workspace not found"):
        update_library.update(tmp_path / "absent")
