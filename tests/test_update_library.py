"""The update script: the static Credit OS library, written only to library/, from fixtures."""

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest
from library_fixtures import make_run, method

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library
from deploy_workflow.library_index import Refused

PREFIX = "window.CREDIT_OS_DATA="
HOSTILE = '</script><script>alert(1)</script><!-- & "quoted"  '


@pytest.fixture(autouse=True)
def stand_in_method(monkeypatch):
    """The synthetic runs' method stands in for the launcher's current one."""
    monkeypatch.setattr("deploy_workflow.library_index.current_method", lambda: method())


def tree(folder: Path) -> dict[str, bytes]:
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def data_of(workspace: Path) -> dict:
    text = (workspace / "library/data.js").read_text(encoding="utf-8")
    assert text.startswith(PREFIX) and text.rstrip().endswith(";")
    return json.loads(text.removeprefix(PREFIX).rstrip().removesuffix(";"))


def delivered_report(run_dir: Path) -> Path:
    (report,) = run_dir.glob("deliveries/*/report.html")
    return report


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def test_writes_static_library(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    before = tree(tmp_path)
    library = update_library.update_library(tmp_path)
    after = tree(tmp_path)
    assert [r["id"] for r in library.runs] == ["run-a"]
    # Only library/ is written; nothing else in the workspace changes, no temporary folder is left.
    assert {k: v for k, v in after.items() if not k.startswith("library/")} == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["library", "runs"]
    for name in ("index.html", "data.js", "static-boot.js", "screen.css", "fonts/OFL.txt"):
        assert (tmp_path / "library" / name).is_file()
    assert not [k for k in after if k.endswith(".test.cjs")]
    presented = [k for k in after if k.startswith("library/reports/")]
    delivery = delivered_report(run_dir).parent.name
    assert presented == [f"library/reports/run-a/{delivery}/report.html"]
    data = data_of(tmp_path)
    assert data["catalogue"]["real"][0]["id"] == "run-a"
    assert data["workspace"]["reports"][0]["href"] == (f"reports/run-a/{delivery}/report.html")
    assert not [s for s in strings(data) if s.startswith("/files/")]
    assert "../runs/run-a/" in "\n".join(strings(data))
    assert not [s for s in strings(data) if "sha256=" in s and s.startswith(("../", "reports/"))]
    page = (tmp_path / "library/index.html").read_text(encoding="utf-8")
    assert "default-src 'none'" in page and "connect-src 'none'" in page
    assert re.findall(r'\b(?:src|href)="(?:https?:)?//', page) == []


def test_presented_report_keeps_original(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    original = delivered_report(run_dir)
    raw = original.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    update_library.update_library(tmp_path)
    assert hashlib.sha256(original.read_bytes()).hexdigest() == digest
    (copy,) = (tmp_path / "library/reports").rglob("report.html")
    shown = copy.read_bytes()
    assert shown.startswith(raw[: raw.rindex(b"</body>")])
    assert b"<style data-library-presentation>" in shown
    assert b"<script data-library-presentation>" in shown
    assert shown.count(b"data-library-presentation") == 2


def test_presentation_goes_before_the_last_body_close():
    html = b"<body>a</body><p>b</P></BODY>tail"
    shown = update_library.present_report(html)
    start = shown.index(b"<style data-library-presentation>")
    assert shown[:start] == b"<body>a</body><p>b</P>"
    assert shown.endswith(b"</script></BODY>tail")


def test_refuses_library_symlink(tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    workspace = tmp_path / "workspace"
    (workspace / "runs").mkdir(parents=True)
    (workspace / "library").symlink_to(elsewhere)
    with pytest.raises(Refused, match="is a link or a file"):
        update_library.update_library(workspace)
    assert list(elsewhere.iterdir()) == []


def test_empty_workspace(tmp_path):
    library = update_library.update_library(tmp_path)
    assert library.runs == [] and library.excluded == []
    assert data_of(tmp_path)["catalogue"]["real"] == []
    assert (tmp_path / "library/index.html").is_file()


def test_unlisted_run_contributes_nothing(tmp_path):
    make_run(tmp_path, "run-a")
    half = make_run(tmp_path, "run-half", issuer_id="zzz", issuer_name="Zeta Synthetic")
    next(half.glob("completed-*.json")).unlink()  # Not complete, so library_index does not list it.
    (tmp_path / "runs/legacy").mkdir()
    library = update_library.update_library(tmp_path)
    assert [r["id"] for r in library.runs] == ["run-a"]
    assert {name for name, _ in library.excluded} == {"run-half", "legacy"}
    data = data_of(tmp_path)
    # Run activity names the excluded folder and its reason; nothing else carries it.
    assert [name for name, _ in data["activity"]["excluded"]] == ["run-half", "legacy"]
    listed = json.dumps({k: v for k, v in data.items() if k != "activity"})
    assert "run-half" not in listed and "Zeta Synthetic" not in json.dumps(data)
    assert not (tmp_path / "library/reports/run-half").exists()
    assert [p.name for p in (tmp_path / "library/reports").iterdir()] == ["run-a"]


def test_hostile_run_text_cannot_leave_the_data_file(tmp_path):
    make_run(tmp_path, "run-a", issuer_name=HOSTILE)
    update_library.update_library(tmp_path)
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    assert "</script" not in text and "<!--" not in text
    assert data_of(tmp_path)["catalogue"]["real"][0]["name"] == HOSTILE


def test_a_rebuild_replaces_the_library_whole(tmp_path):
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    (tmp_path / "library/stale.txt").write_text("old")
    update_library.update_library(tmp_path)
    assert not (tmp_path / "library/stale.txt").exists()
    assert (tmp_path / "library/index.html").is_file()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["library", "runs"]


def test_a_failed_build_keeps_the_previous_library(tmp_path, monkeypatch):
    make_run(tmp_path, "run-a")
    update_library.update_library(tmp_path)
    before = tree(tmp_path / "library")

    def broken(*args):
        raise RuntimeError("cannot build")

    monkeypatch.setattr(update_library, "workspace_store", broken)
    with pytest.raises(RuntimeError, match="cannot build"):
        update_library.update_library(tmp_path)
    assert tree(tmp_path / "library") == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["library", "runs"]


def test_the_command_reports_what_it_listed_and_why_others_are_not_shown(tmp_path, capsys):
    make_run(tmp_path, "run-a")
    (tmp_path / "runs/legacy").mkdir()
    assert update_library.main(["--workspace", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Listed 1 run(s) on the current methodology." in out
    assert "  legacy: not a CP-OS launcher run (no workflow.json)" in out
    assert str(tmp_path.resolve() / "library/index.html") in out


def test_a_missing_workspace_is_refused(tmp_path):
    with pytest.raises(Refused, match="Workspace not found"):
        update_library.update_library(tmp_path / "absent")


def test_the_command_turns_a_refusal_into_an_exit(tmp_path):
    with pytest.raises(SystemExit, match="Workspace not found"):
        update_library.main(["--workspace", str(tmp_path / "absent")])


def test_data_js_carries_excluded_runs(tmp_path):
    make_run(tmp_path, "run-a")
    half = make_run(tmp_path, "run-half", issuer_id="zzz", issuer_name="Zeta Synthetic")
    next(half.glob("completed-*.json")).unlink()
    library = update_library.update_library(tmp_path)
    activity = data_of(tmp_path)["activity"]
    assert activity["excluded"] == [[name, reason] for name, reason in library.excluded]
    assert [name for name, _ in activity["excluded"]] == ["run-half"]
    assert activity["excluded"][0][1]  # library_index's own reason, not empty
    assert all(isinstance(i, str) for i in activity["issues"])
