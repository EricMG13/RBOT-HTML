"""tools/quality_gate.py: which files it takes into scope."""

import shutil
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


def _repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.invalid")
    _git(tmp_path, "config", "user.name", "test")
    return tmp_path


def test_a_moved_file_is_compared_with_the_file_it_was_moved_from(tmp_path):
    # Moving a legacy file down a layer must not put all of its old code in scope.
    repo = _repo(tmp_path)
    # git breaks (-B) only files of 400 bytes or more; each of these is about 600.
    body = "".join(f"value_number_{n} = {n}  # line {n}\n" for n in range(1, 21))
    kept = body.replace("value_number", "kept_number")
    (repo / "old.py").write_text(body, encoding="utf-8")
    (repo / "kept.py").write_text(kept, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "mv", "old.py", "new.py")
    (repo / "old.py").write_text("from new import *\n", encoding="utf-8")  # the alias left behind
    (repo / "new.py").write_text(body.replace("_7 = 7 ", "_7 = 70 "), encoding="utf-8")
    (repo / "copy.py").write_text(kept, encoding="utf-8")  # a copy of a file that stays as it was
    _git(repo, "add", ".")
    assert quality_gate.moved_sources(repo, "HEAD") == {"new.py": "old.py"}
    assert quality_gate.moved_lines(repo, "HEAD", "old.py", "new.py") == {7}
    assert quality_gate.changed_lines(repo, "HEAD", "new.py") == set(range(1, 21))
    assert quality_gate.changed_lines(repo, "HEAD", "copy.py") == set(range(1, 21))


SRC = Path(__file__).resolve().parents[1] / "src"
CONTRACTS = Path(__file__).resolve().parents[1] / ".importlinter"
ENGINE_CONTRACT = (
    "deploy_vii, the engine, imports neither deploy_workflow nor the issuer library's credit_os"
)
LAYERS_CONTRACT = "deploy_workflow: services, orchestration, delivery, analytical, engine"
OWNERS_CONTRACT = "every deploy_workflow.owners module is listed"


def _tree(tmp_path: Path, monkeypatch) -> Path:
    """A copy of the repository's packages and import contracts, imported ahead of the real ones."""
    shutil.copytree(SRC, tmp_path / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(CONTRACTS, tmp_path / ".importlinter")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "src"))
    return tmp_path


def _broken(root: Path) -> list[tuple[str, str, str, str]]:
    result = quality_gate.run_gate(root, "HEAD", checks="imports")
    lines = (root / ".importlinter").read_text(encoding="utf-8").splitlines()
    return [(f.tool, f.path, f.code, lines[f.line - 1]) for f in result.findings]


def test_the_import_contracts_hold_on_the_repository_as_it_is(tmp_path, monkeypatch):
    assert _broken(_tree(tmp_path, monkeypatch)) == []


def test_an_engine_import_of_deploy_workflow_breaks_the_gate(tmp_path, monkeypatch):
    root = _tree(tmp_path, monkeypatch)
    reverse = root / "src/deploy_vii/display.py"
    lazy = "\n\ndef _late():\n    from deploy_workflow import confidence\n\n    return confidence\n"
    reverse.write_text(reverse.read_text(encoding="utf-8") + lazy, encoding="utf-8")
    assert _broken(root) == [("imports", ".importlinter", "BROKEN", f"name = {ENGINE_CONTRACT}")]
    assert quality_gate.main(["--root", str(root), "--checks", "imports"]) == 1


def test_a_lower_layer_import_of_a_higher_one_breaks_the_gate(tmp_path, monkeypatch):
    root = _tree(tmp_path, monkeypatch)
    low = root / "src/deploy_workflow/run_scopes.py"
    low.write_text(low.read_text(encoding="utf-8") + "\nimport deploy_workflow.library_index\n")
    assert _broken(root) == [("imports", ".importlinter", "BROKEN", f"name = {LAYERS_CONTRACT}")]


def test_a_new_module_fails_until_it_is_placed_in_a_layer(tmp_path, monkeypatch):
    root = _tree(tmp_path, monkeypatch)
    (root / "src/deploy_workflow/owners/one_step.py").write_text("X = 1\n", encoding="utf-8")
    (root / "src/deploy_workflow/owner_steps.py").write_text("X = 1\n", encoding="utf-8")
    assert _broken(root) == [
        ("imports", ".importlinter", "BROKEN", f"name = {LAYERS_CONTRACT}"),
        ("imports", ".importlinter", "BROKEN", f"name = {OWNERS_CONTRACT}"),
    ]


def _layer_members(section: str) -> set[str]:
    layers = section.split("layers =\n", 1)[1].split("\nignore_imports", 1)[0]
    return {name.strip() for line in layers.splitlines() for name in line.split(":")}


def test_both_contracts_name_the_same_owners_modules():
    # The owners contract makes the list exhaustive; the layers contract must place each of them.
    text = CONTRACTS.read_text(encoding="utf-8")
    layers = text.split("[importlinter:contract:deploy-workflow-layers]")[1].split("\n[")[0]
    owners = text.split("[importlinter:contract:owners-listed]")[1]
    in_layers = {m.removeprefix("owners.") for m in _layer_members(layers) if "owners." in m}
    assert in_layers == _layer_members(owners)
    assert "cpos_launch" in in_layers and "pins" in in_layers
