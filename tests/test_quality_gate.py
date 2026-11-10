"""tools/quality_gate.py: which files it takes into scope."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import quality_gate


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_changed_files_keeps_names_with_spaces_and_accents(tmp_path):
    # Dropped silently, such a file would pass the gate without being checked.
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.invalid")
    _git(tmp_path, "config", "user.name", "test")
    names = ["a b.py", "café.py", "plain.py"]
    for name in names:
        (tmp_path / name).write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "base")
    for name in names:
        (tmp_path / name).write_text("x = 2\n", encoding="utf-8")
    (tmp_path / "new file.py").write_text("y = 1\n", encoding="utf-8")
    assert quality_gate.changed_files(tmp_path, "HEAD") == sorted([*names, "new file.py"])
    assert quality_gate.changed_lines(tmp_path, "HEAD", "a b.py") == {1}
    assert quality_gate.changed_lines(tmp_path, "HEAD", "new file.py") is None
