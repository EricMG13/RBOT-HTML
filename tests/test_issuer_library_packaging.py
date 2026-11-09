"""The packaged runtime folder after a re-pin; offline fakes stand in for python.org and PyPI.

No download is made: `download` and `urlopen` are replaced, and the source trees the bundle
copies are small hand-made folders. Expected folder listings are written out here.
"""

import importlib.util
import io
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "library_runtime", ROOT / "apps/issuer-library/packaging/runtime.py"
)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def fake_zip(folder: Path, name: str, files: dict[str, str]) -> Path:
    path = folder / name
    with zipfile.ZipFile(path, "w") as archive:
        for member, text in files.items():
            archive.writestr(member, text)
    return path


@pytest.fixture
def offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Fake sources and downloads; returns the names of the files 'downloaded'."""
    app, root, cache = tmp_path / "repo/apps/issuer-library", tmp_path / "repo", tmp_path / "cache"
    for name in [
        *("engine/bridge.py", "engine/store.py", "engine/catalog.json", "engine/run_workflow.py"),
        *("update_library.py", "static/template.html", "static/app.js"),
        *("static/logic.test.cjs", "static/browser_check.cjs"),
    ]:
        (app / name).parent.mkdir(parents=True, exist_ok=True)
        (app / name).write_text("x")
    (app / "packaging").mkdir()
    (app / "packaging/Smoke-test.ps1").write_text("x")
    (root / "cases/context").mkdir(parents=True)
    (root / "cases/context/research-minimal.json").write_text("{}")
    for name in ["src", "docs/reuse/selected-methods", "docs/visualisations", "prompts"]:
        (root / name).mkdir(parents=True)
        (root / name / "keep.txt").write_text("x")
    cache.mkdir()
    downloaded: list[str] = []

    def download(url: str, sha: str, name: str) -> Path:
        downloaded.append(name)
        if name.startswith("python-"):
            return fake_zip(cache, name, {"python.exe": "x"})
        package, version = name.split("-")[:2]
        files = {f"{package}-{version}.dist-info/METADATA": f"Version: {version}"}
        files[f"{package}/__init__.py"] = version
        if version == "1":
            files[f"{package}/removed_in_2.py"] = "STALE = 1"
        return fake_zip(cache, name, files)

    def urlopen(url: str, timeout: int = 0) -> io.BytesIO:
        name, version = url.split("/pypi/")[1].split("/")[:2]
        wheel = f"{name}-{version}-py3-none-any.whl"
        return io.BytesIO(
            json.dumps(
                {"urls": [{"filename": wheel, "url": "u", "digests": {"sha256": "0"}}]}
            ).encode()
        )

    monkeypatch.setattr(runtime, "APP", app)
    monkeypatch.setattr(runtime, "ROOT", root)
    monkeypatch.setattr(runtime, "download", download)
    monkeypatch.setattr(runtime.urllib.request, "urlopen", urlopen)
    return downloaded


def site_listing(target: Path) -> list[str]:
    site = target / "engine/runtime/Lib/site-packages"
    return sorted(path.relative_to(site).as_posix() for path in site.rglob("*") if path.is_file())


def test_a_re_pinned_runtime_ships_only_the_new_wheels(
    tmp_path: Path, offline: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "windows-amd64"
    target.mkdir()
    monkeypatch.setattr(runtime, "PINS", {"pypdf": "1", "openpyxl": "1"})
    runtime.bundle(target, "amd64")
    # A pin bumped (pypdf 1 -> 2) and a package dropped (openpyxl): nothing of either old one stays.
    monkeypatch.setattr(runtime, "PINS", {"pypdf": "2"})
    runtime.bundle(target, "amd64")
    assert site_listing(target) == ["pypdf-2.dist-info/METADATA", "pypdf/__init__.py"]
    manifest = json.loads((target / "engine/runtime-manifest.json").read_text())
    assert {name: record["version"] for name, record in manifest["wheels"].items()} == {
        "pypdf": "2"
    }
    assert (target / "engine/runtime/python.exe").is_file()
    assert (target / "engine/runtime/python313._pth").is_file()


def test_the_same_pins_reuse_the_runtime_without_a_download(
    tmp_path: Path, offline: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "windows-amd64"
    target.mkdir()
    monkeypatch.setattr(runtime, "PINS", {"pypdf": "1"})
    runtime.bundle(target, "amd64")
    assert offline == ["python-3.13.15-embed-amd64.zip", "pypdf-1-py3-none-any.whl"]
    runtime.bundle(target, "amd64")
    assert len(offline) == 2
    assert "pypdf/removed_in_2.py" in site_listing(target)


def test_a_linked_runtime_folder_is_refused_and_its_target_kept(
    tmp_path: Path, offline: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target, outside = tmp_path / "windows-amd64", tmp_path / "elsewhere"
    (target / "engine").mkdir(parents=True)
    outside.mkdir()
    (outside / "precious.txt").write_text("keep")
    (target / "engine/runtime").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(runtime, "PINS", {"pypdf": "1"})
    with pytest.raises(ValueError, match="outside the build"):
        runtime.bundle(target, "amd64")
    assert (outside / "precious.txt").read_text() == "keep"
    assert offline == []


def test_a_mac_build_has_no_runtime_to_clear(tmp_path: Path, offline: list[str]) -> None:
    target = tmp_path / "darwin-arm64"
    target.mkdir()
    runtime.bundle(target, None)
    assert not (target / "engine/runtime").exists()
    assert offline == []


def test_the_package_ships_the_static_library_and_its_two_windows_wrappers(
    tmp_path: Path, offline: list[str]
) -> None:
    target = tmp_path / "windows-amd64"
    target.mkdir()
    runtime.bundle(target, None)
    engine = target / "engine"
    assert (engine / "update_library.py").is_file() and (engine / "run_workflow.py").is_file()
    assert sorted(p.name for p in (engine / "static").iterdir()) == ["app.js", "template.html"]
    for name in ["Run workflow.cmd", "Update library.cmd"]:
        raw = (target / name).read_bytes()
        assert raw.startswith(b"@echo off\r\n") and b"\n" not in raw.replace(b"\r\n", b"")
    run = (target / "Run workflow.cmd").read_text()
    python = '"%~dp0engine\\runtime\\python.exe" -I -B -X utf8'
    assert f'{python} "%~dp0engine\\run_workflow.py" %*' in run
    update = (target / "Update library.cmd").read_text()
    assert '--workspace "%WORKSPACE%"' in update
    assert 'start "" "%WORKSPACE%\\library\\index.html"' in update


def test_a_linked_engine_folder_is_refused_before_anything_is_deleted(tmp_path: Path) -> None:
    # The engine folder itself leads out of the build: neither its runtime nor manifest is removed.
    target, outside = tmp_path / "windows-amd64", tmp_path / "elsewhere"
    target.mkdir()
    (outside / "runtime").mkdir(parents=True)
    (outside / "runtime/precious.txt").write_text("keep")
    (outside / "runtime-manifest.json").write_text("{}")
    (target / "engine").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="outside the build"):
        runtime.clear_runtime(
            target, target / "engine/runtime", target / "engine/runtime-manifest.json"
        )
    assert (outside / "runtime/precious.txt").read_text() == "keep"
    assert (outside / "runtime-manifest.json").read_text() == "{}"


def test_a_runtime_path_that_climbs_out_of_the_build_is_refused(tmp_path: Path) -> None:
    # Expected by hand: engine/../../elsewhere/runtime resolves to tmp_path/elsewhere/runtime,
    # which is outside tmp_path/build, so nothing is deleted.
    target, outside = tmp_path / "build", tmp_path / "elsewhere"
    (target / "engine").mkdir(parents=True)
    (outside / "runtime").mkdir(parents=True)
    (outside / "runtime/precious.txt").write_text("keep")
    manifest = target / "engine/runtime-manifest.json"
    manifest.write_text("{}")
    with pytest.raises(ValueError, match="outside the build"):
        runtime.clear_runtime(target, target / "engine/../../elsewhere/runtime", manifest)
    assert (outside / "runtime/precious.txt").read_text() == "keep"
    assert manifest.read_text() == "{}"


def test_a_missing_runtime_folder_is_created_empty_and_the_manifest_removed(
    tmp_path: Path,
) -> None:
    target = tmp_path / "build"
    (target / "engine").mkdir(parents=True)
    manifest = target / "engine/runtime-manifest.json"
    manifest.write_text("{}")
    runtime.clear_runtime(target, target / "engine/runtime", manifest)
    assert (target / "engine/runtime").is_dir() and not list((target / "engine/runtime").iterdir())
    assert not manifest.exists()
