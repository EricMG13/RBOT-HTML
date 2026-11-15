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


def _syncs(repo: Path, *names: str) -> Path:
    syncs = repo / work_pc_delta.PACK_DIR / "syncs"
    for name in names:
        (syncs / name).mkdir(parents=True)
        (syncs / name / "SYNC.json").write_text("{}\n", encoding="utf-8")
    return syncs


def _record(repo: Path, **fields: object) -> Path:
    record = repo / work_pc_delta.PACK_DIR / "manifest.json"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({"files": {}, **fields}), encoding="utf-8")
    return record


def _number(pack: Path) -> str:
    return pack.name.split("_", 1)[0]


def _last_pack(repo: Path) -> object:
    record = repo / work_pc_delta.PACK_DIR / "manifest.json"
    return json.loads(record.read_text(encoding="utf-8"))["last_pack"]


def test_numbers_continue_after_packs_are_pruned(tmp_path):
    repo, base, head = _repo(tmp_path)
    first = work_pc_delta.write_pack(repo, base, head)
    later = _commit(repo, {"same.txt": "two\n"}, "two")
    second = work_pc_delta.write_pack(repo, head, later)
    assert (_number(first), _number(second), _last_pack(repo)) == ("001", "002", 2)
    # Counting folders would now give 002 again: one folder left, plus one.
    removed = work_pc_delta.prune(repo, 0, work_pc_delta.date(2999, 1, 1), dry_run=False)
    assert removed[0] == f"removed {first.name}"
    assert not first.exists()
    assert second.exists()
    last = _commit(repo, {"same.txt": "three\n"}, "three")
    assert _number(work_pc_delta.write_pack(repo, later, last)) == "003"
    assert _last_pack(repo) == 3


def test_number_comes_from_the_manifest_when_no_pack_is_left(tmp_path):
    repo, base, head = _repo(tmp_path)
    _record(repo, head=base, last_pack=41)
    (repo / work_pc_delta.PACK_DIR / "syncs").mkdir()  # every pack pruned
    assert _number(work_pc_delta.write_pack(repo, base, head)) == "042"
    assert _last_pack(repo) == 42


def test_number_falls_back_to_the_highest_folder_without_the_manifest_field(tmp_path):
    repo, base, head = _repo(tmp_path)
    _record(repo, head=base)  # the manifest as written before last_pack existed
    # Two folders, the higher one numbered 069: a count would give 003.
    _syncs(repo, "007_2026-11-11_aaaaaaa-bbbbbbb", "069_2026-11-14_ccccccc-ddddddd")
    assert _number(work_pc_delta.write_pack(repo, base, head)) == "070"
    assert _last_pack(repo) == 70


def test_number_never_goes_below_a_folder_that_is_still_there(tmp_path):
    repo, base, head = _repo(tmp_path)
    _record(repo, head=base, last_pack=5)  # a stale record must not reissue 006-009
    _syncs(repo, "009_2026-11-14_ccccccc-ddddddd")
    assert _number(work_pc_delta.write_pack(repo, base, head)) == "010"


def test_first_pack_is_number_one(tmp_path):
    repo, base, head = _repo(tmp_path)
    assert _number(work_pc_delta.write_pack(repo, base, head)) == "001"
    assert _last_pack(repo) == 1


PRUNE_TODAY = work_pc_delta.date(2026, 12, 1)


def test_prune_removes_only_packs_dated_before_the_window(tmp_path):
    names = [
        "003_2026-11-16_aaaaaaa-bbbbbbb",  # 15 days before 1 December: past a 14-day window
        "004_2026-11-17_bbbbbbb-ccccccc",  # exactly 14 days: kept
        "005_2026-11-18_ccccccc-ddddddd",  # 13 days: kept
        "006_2026-12-02_ddddddd-eeeeeee",  # dated after today: kept
    ]
    syncs = _syncs(tmp_path, *names)
    planned = work_pc_delta.prune(tmp_path, 14, PRUNE_TODAY, dry_run=True)
    assert planned == [
        "would remove 003_2026-11-16_aaaaaaa-bbbbbbb",
        "prune: 1 to remove, 3 kept, 0 left alone; window 14 days before 2026-12-01",
    ]
    assert sorted(entry.name for entry in syncs.iterdir()) == names  # a dry run removes nothing
    done = work_pc_delta.prune(tmp_path, 14, PRUNE_TODAY, dry_run=False)
    assert done == [
        "removed 003_2026-11-16_aaaaaaa-bbbbbbb",
        "prune: 1 removed, 3 kept, 0 left alone; window 14 days before 2026-12-01",
    ]
    assert sorted(entry.name for entry in syncs.iterdir()) == names[1:]
    # A wider window keeps what a narrower one removes.
    assert work_pc_delta.prune(tmp_path, 13, PRUNE_TODAY, dry_run=True)[0] == (
        "would remove 004_2026-11-17_bbbbbbb-ccccccc"
    )


def test_prune_never_removes_the_newest_pack(tmp_path):
    names = ["010_2026-01-01_aaaaaaa-bbbbbbb", "011_2025-06-01_bbbbbbb-ccccccc"]
    syncs = _syncs(tmp_path, *names)
    # Both are far past the window; 011 is the newest by number although dated earlier.
    assert work_pc_delta.prune(tmp_path, 14, PRUNE_TODAY, dry_run=False) == [
        "removed 010_2026-01-01_aaaaaaa-bbbbbbb",
        "prune: 1 removed, 1 kept, 0 left alone; window 14 days before 2026-12-01",
    ]
    assert [entry.name for entry in syncs.iterdir()] == [names[1]]
    assert work_pc_delta.prune(tmp_path, 0, PRUNE_TODAY, dry_run=False)[0].startswith(
        "prune: 0 removed, 1 kept"
    )
    assert (syncs / names[1]).is_dir()


def test_prune_leaves_and_reports_what_is_not_named_like_a_pack(tmp_path):
    odd = [
        "12_2026-01-01_aaaaaaa-bbbbbbb",  # two-digit number
        "013_2026-13-01_aaaaaaa-bbbbbbb",  # no such month
        "014_20260101_aaaaaaa-bbbbbbb",  # date without dashes
        "notes",
    ]
    syncs = _syncs(tmp_path, "001_2026-01-01_aaaaaaa-bbbbbbb", "002_2026-01-02_x-y", *odd)
    (syncs / "015_2026-01-01_a-file").write_text("not a folder\n", encoding="utf-8")
    report = work_pc_delta.prune(tmp_path, 14, PRUNE_TODAY, dry_run=False)
    assert report == [
        "removed 001_2026-01-01_aaaaaaa-bbbbbbb",
        "left alone (not NNN_YYYY-MM-DD_...): 013_2026-13-01_aaaaaaa-bbbbbbb",
        "left alone (not NNN_YYYY-MM-DD_...): 014_20260101_aaaaaaa-bbbbbbb",
        "left alone (not NNN_YYYY-MM-DD_...): 015_2026-01-01_a-file",
        "left alone (not NNN_YYYY-MM-DD_...): 12_2026-01-01_aaaaaaa-bbbbbbb",
        "left alone (not NNN_YYYY-MM-DD_...): notes",
        "prune: 1 removed, 1 kept, 5 left alone; window 14 days before 2026-12-01",
    ]
    assert sorted(entry.name for entry in syncs.iterdir()) == sorted(
        ["002_2026-01-02_x-y", "015_2026-01-01_a-file", *odd]
    )


def test_prune_with_no_syncs_folder_or_a_negative_window(tmp_path):
    assert work_pc_delta.prune(tmp_path, 14, PRUNE_TODAY, dry_run=False) == [
        "prune: 0 removed, 0 kept, 0 left alone; window 14 days before 2026-12-01"
    ]
    try:
        work_pc_delta.prune(tmp_path, -1, PRUNE_TODAY, dry_run=False)
    except SystemExit as stopped:
        assert "--keep-days" in str(stopped)
    else:
        raise AssertionError("a negative window must be refused")


def test_check_plan_and_generate_work_after_every_old_pack_is_pruned(tmp_path):
    repo, base, head = _repo(tmp_path)
    first = work_pc_delta.write_pack(repo, base, head)
    later = _commit(repo, {"same.txt": "two\n"}, "two")
    second = work_pc_delta.write_pack(repo, head, later)
    record = repo / work_pc_delta.PACK_DIR / "manifest.json"
    before = record.read_bytes()
    work_pc_delta.prune(repo, 0, work_pc_delta.date(2999, 1, 1), dry_run=False)
    assert not first.exists()
    assert record.read_bytes() == before  # pruning does not touch the manifest
    download = _extract(repo, later, tmp_path / "download")
    assert work_pc_delta.check(download, record) == []
    adapted = _extract(repo, later, tmp_path / "adapted")
    (adapted / "local.cfg").write_text("proxy\n", encoding="utf-8")
    assert work_pc_delta.plan(download, adapted, record) == [
        "keep   local.cfg",
        "plan: 0 merge, 0 copy, 0 delete, 1 keep",
    ]
    # With the newest pack gone as well (by hand), generate still continues from the manifest.
    work_pc_delta.shutil.rmtree(second)
    last = _commit(repo, {"same.txt": "three\n"}, "three")
    message = work_pc_delta.generate(repo, None, last)
    assert message.startswith(f"wrote {work_pc_delta.PACK_DIR}/syncs/003_")
    assert message.endswith(f"_{later[:7]}-{last[:7]}")
    assert work_pc_delta.check(_extract(repo, last, tmp_path / "newest"), record) == []


def test_prune_command_lists_without_removing(tmp_path, monkeypatch, capsys):
    tool = tmp_path / "tools" / "work_pc_delta.py"
    tool.parent.mkdir()
    tool.write_text("", encoding="utf-8")
    monkeypatch.setattr(work_pc_delta, "__file__", str(tool))
    syncs = _syncs(tmp_path, "001_2001-01-01_aaaaaaa-bbbbbbb", "002_2001-01-02_bbbbbbb-ccccccc")
    assert work_pc_delta.main(["prune", "--dry-run"]) == 0
    assert capsys.readouterr().out.startswith("would remove 001_2001-01-01_aaaaaaa-bbbbbbb\n")
    assert len(list(syncs.iterdir())) == 2
    assert work_pc_delta.main(["prune", "--keep-days", "9"]) == 0
    assert capsys.readouterr().out.startswith("removed 001_2001-01-01_aaaaaaa-bbbbbbb\n")
    assert [entry.name for entry in syncs.iterdir()] == ["002_2001-01-02_bbbbbbb-ccccccc"]
