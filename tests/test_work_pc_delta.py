"""tools/work_pc_delta.py: packs list every change, and check finds what packs miss."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import work_pc_delta


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return done.stdout.strip()


def _commit(repo: Path, files: dict[str, str | None], message: str) -> str:
    for name, text in files.items():
        path = repo / name
        if text is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


LOCK = '[[package]]\nname = "{0}"\nversion = "{1}"\n'


def _repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "test")
    base = _commit(
        repo,
        {
            "pyproject.toml": '[project]\ndependencies = ["pypdf==6.0"]\n',
            "uv.lock": LOCK.format("pypdf", "6.0") + LOCK.format("old", "1.0"),
            "src/a b.py": "x = 1\ny = 2\nz = 3\n",
            "gone.txt": "bye\n",
            "same.txt": "kept\n",
            "move me.txt": "line\n" * 20,
        },
        "base",
    )
    head = _commit(
        repo,
        {
            "pyproject.toml": '[project]\ndependencies = ["pypdf==6.1"]\n',
            "uv.lock": LOCK.format("pypdf", "6.1") + LOCK.format("new", "2.0"),
            "src/a b.py": "x = 1\ny = 20\nz = 3\nw = 4\n",
            "gone.txt": None,
            "move me.txt": None,
            "moved.txt": "line\n" * 20,
            "added.md": "new\n",
        },
        "Merge pull request #7 from someone/branch\n\nAdd the new parts",
    )
    return repo, base, head


def test_pack_lists_packages_files_and_lines(tmp_path):
    repo, base, head = _repo(tmp_path)
    out = work_pc_delta.write_pack(repo, base, head)
    changes = (out / "CHANGES.md").read_text(encoding="utf-8")
    # Versions come from both files, including a package only in the lock.
    assert "| dependencies | pypdf==6.0 | pypdf==6.1 |" in changes
    assert "| pypdf | 6.0 | 6.1 |" in changes
    assert "| old | 1.0 | (removed) |" in changes
    assert "| new | (absent) | 2.0 |" in changes
    # Every file with status, where to look in the new version, and the PR title.
    assert "| modified | `src/a b.py` | +2 −1 | L2, L4 |" in changes
    assert "| deleted | `gone.txt` | +0 −1 | — |" in changes
    assert "| renamed | `move me.txt` → `moved.txt` | +0 −0 | — |" in changes
    assert "| added | `added.md` | +1 −0 | L1 |" in changes
    assert "same.txt" not in changes
    assert "Add the new parts (Merge pull request #7" in changes
    patch = (out / "changes.patch").read_text(encoding="utf-8")
    assert "+y = 20" in patch
    assert json.loads((out / "SYNC.json").read_text(encoding="utf-8"))["base"] == base


def test_next_pack_starts_where_the_last_ended_and_skips_its_own_folder(tmp_path, monkeypatch):
    repo, base, head = _repo(tmp_path)
    assert work_pc_delta.generate(repo, base, head).startswith("wrote ")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "pack")
    # The pack commit touches only the pack folder: no pack for it alone.
    assert work_pc_delta.generate(repo, None, "HEAD").startswith("nothing to do")
    later = _commit(repo, {"same.txt": "changed\n"}, "later")
    message = work_pc_delta.generate(repo, None, later)
    packs = sorted((repo / work_pc_delta.PACK_DIR / "syncs").iterdir())
    newest = (packs[-1] / "CHANGES.md").read_text(encoding="utf-8")
    assert message.endswith(packs[-1].name)
    assert "`same.txt`" in newest
    assert "`docs/work-pc/" not in newest  # the previous pack's own commit is not a change
    assert "1 file(s) changed" in newest


def test_check_matches_an_archive_and_names_each_difference(tmp_path):
    repo, base, head = _repo(tmp_path)
    work_pc_delta.write_pack(repo, base, head)
    copy = tmp_path / "download"
    copy.mkdir()
    archive = subprocess.run(["git", "archive", head], cwd=repo, check=True, capture_output=True)
    subprocess.run(["tar", "-x", "-C", str(copy)], input=archive.stdout, check=True)
    record = repo / work_pc_delta.PACK_DIR / "manifest.json"
    (copy / ".venv").mkdir()
    (copy / ".venv" / "ignored.py").write_text("", encoding="utf-8")
    assert work_pc_delta.check(copy, record) == []
    (copy / "same.txt").write_text("kept\r\n", encoding="utf-8", newline="")
    (copy / "added.md").unlink()
    (copy / "local.cfg").write_text("adapted\n", encoding="utf-8")
    assert work_pc_delta.check(copy, record) == [
        "differs  same.txt",
        "missing  added.md",
        "extra    local.cfg",
    ]


def test_base_by_date_is_the_last_commit_by_then(tmp_path):
    repo, base, head = _repo(tmp_path)
    assert work_pc_delta.resolve(repo, base[:7], head) == base
    by_then = _git(repo, "log", "-1", "--format=%cI", head)
    assert work_pc_delta.resolve(repo, by_then, head) == head
    # A date is "--before", never a commit name, so it cannot pick a later commit.


def _extract(repo: Path, rev: str, into: Path) -> Path:
    into.mkdir()
    archive = subprocess.run(["git", "archive", rev], cwd=repo, check=True, capture_output=True)
    subprocess.run(["tar", "-x", "-C", str(into)], input=archive.stdout, check=True)
    return into


def test_plan_sorts_each_file_by_who_changed_it(tmp_path):
    repo, base, head = _repo(tmp_path)
    record = tmp_path / "base.json"
    record.write_text(json.dumps({"files": work_pc_delta.manifest(repo, base)}), encoding="utf-8")
    download = _extract(repo, head, tmp_path / "download")
    adapted = _extract(repo, base, tmp_path / "adapted")
    (adapted / "src" / "a b.py").write_text("x = 1  # work PC\ny = 2\nz = 3\n", encoding="utf-8")
    (adapted / "same.txt").write_text("kept, adapted\n", encoding="utf-8")
    (adapted / "local.cfg").write_text("proxy\n", encoding="utf-8")
    assert work_pc_delta.plan(download, adapted, record) == [
        "merge  src/a b.py",  # upstream and the work PC both changed it
        "copy   added.md",
        "copy   moved.txt",
        "copy   pyproject.toml",
        "copy   uv.lock",
        "delete gone.txt",
        "delete move me.txt",
        "keep   local.cfg",  # the work PC's own file
        "keep   same.txt",  # adapted, unchanged upstream
        "plan: 1 merge, 4 copy, 2 delete, 2 keep",
    ]


def test_plan_action_covers_every_case():
    assert work_pc_delta.plan_action("b", "b", "b") is None
    assert work_pc_delta.plan_action("b", "b", "x") == "keep"
    assert work_pc_delta.plan_action(None, None, "x") == "keep"
    assert work_pc_delta.plan_action("b", "n", "b") == "copy"
    assert work_pc_delta.plan_action(None, "n", None) == "copy"
    assert work_pc_delta.plan_action("b", None, "b") == "delete"
    assert work_pc_delta.plan_action("b", "n", "n") is None  # already the same
    assert work_pc_delta.plan_action("b", "n", "x") == "merge"
    assert work_pc_delta.plan_action("b", None, "x") == "merge"  # deleted upstream, adapted
    assert work_pc_delta.plan_action("b", "n", None) == "merge"  # removed by the work PC
