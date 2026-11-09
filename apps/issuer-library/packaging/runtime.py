"""Bundle official Python and pinned wheels; verify every downloaded SHA-256."""
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
CACHE = ROOT / 'artifacts/issuer-library/runtime-cache'
PINS = {'pydantic':'2.14.1','pydantic-core':'2.50.1','annotated-types':'0.8.0',
        'typing-extensions':'4.16.0','typing-inspection':'0.4.4','pypdf':'6.21.2',
        'openpyxl':'3.1.5','et-xmlfile':'2.0.0'}
PYTHON = {'amd64':'d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf',
          'arm64':'cd992cbfb33be433ff20f150691595efb2862e56f4f1bec684c6077d4775af8e'}

def download(url: str, sha: str, name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / name
    if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != sha:
        with urllib.request.urlopen(url, timeout=90) as response:
            raw = response.read(100 << 20)
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError(f"Checksum mismatch: {name}")
        target.write_bytes(raw)
    return target


def clear_runtime(target: Path, runtime: Path, manifest: Path) -> None:
    """Empty the runtime folder the build owns, so a re-pinned runtime ships no stale wheels.

    Nothing is deleted until the folder is known to be inside the build target.
    """
    if (
        runtime.is_symlink()
        or runtime.is_junction()
        or not runtime.resolve().is_relative_to(target.resolve())
    ):
        raise ValueError(f"Refusing to clear a runtime folder outside the build: {runtime}")
    manifest.unlink(missing_ok=True)
    if runtime.exists():
        shutil.rmtree(runtime)
    runtime.mkdir()


# Windows wrappers, one batch line per entry. Untested on Windows from this build host;
# Smoke-test.ps1 on the target host is the acceptance.
_PYTHON = '"%~dp0engine\\runtime\\python.exe" -I -B -X utf8'
_DOCUMENTS = (
    'if not defined WORKSPACE for /f "usebackq delims=" %%D in '
    "(`powershell -NoProfile -Command \"[Environment]::GetFolderPath('MyDocuments')\"`) "
    'do set "WORKSPACE=%%D\\FinalWorkflow"'
)
WRAPPERS = {
    "Run workflow.cmd": [
        "@echo off",
        "rem Start a CP-OS run with the launcher's own options (see README.md). Without --live",
        "rem it only prepares and reviews the run; --live with a ruling is the paid run.",
        f'{_PYTHON} "%~dp0engine\\run_workflow.py" %*',
        "exit /b %errorlevel%",
    ],
    "Update library.cmd": [
        "@echo off",
        "setlocal",
        "rem Rebuild the Issuer Library page from the workspace's completed runs, then open it.",
        "rem Workspace: the first argument, else FINAL_WORKFLOW_WORKSPACE, else",
        "rem Documents\\FinalWorkflow.",
        'set "WORKSPACE=%~1"',
        'if not defined WORKSPACE set "WORKSPACE=%FINAL_WORKFLOW_WORKSPACE%"',
        _DOCUMENTS,
        'if not defined WORKSPACE set "WORKSPACE=%USERPROFILE%\\Documents\\FinalWorkflow"',
        f'{_PYTHON} "%~dp0engine\\update_library.py" --workspace "%WORKSPACE%"',
        "if errorlevel 1 (",
        "  pause",
        "  exit /b 1",
        ")",
        'start "" "%WORKSPACE%\\library\\index.html"',
    ],
}


def bundle(target: Path, architecture: str | None) -> None:
    engine = target / "engine"
    engine.mkdir(exist_ok=True)
    for name in ["bridge.py", "store.py", "catalog.json", "run_workflow.py"]:
        shutil.copyfile(APP / "engine" / name, engine / name)
    # The static library: its update script and page parts (not their tests), and the two
    # double-click wrappers that run the launcher and the update with the bundled Python.
    shutil.copyfile(APP / "update_library.py", engine / "update_library.py")
    if (engine / "static").exists():
        shutil.rmtree(engine / "static")
    tests = shutil.ignore_patterns("*.test.cjs", "*_check.cjs")
    shutil.copytree(APP / "static", engine / "static", ignore=tests)
    for name, lines in WRAPPERS.items():
        (target / name).write_text("\n".join(lines) + "\n", encoding="ascii", newline="\r\n")
    shutil.copyfile(ROOT / "cases/context/research-minimal.json", engine / "smoke-context.json")
    shutil.copyfile(APP / "packaging/Smoke-test.ps1", target / "Smoke-test.ps1")
    if (engine / "src").exists():
        shutil.rmtree(engine / "src")
    shutil.copytree(
        ROOT / "src", engine / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    # The launcher reads each module's method from these, relative to the engine folder.
    for name in ["docs/reuse/selected-methods", "docs/visualisations", "prompts"]:
        if (engine / name).exists():
            shutil.rmtree(engine / name)
        shutil.copytree(
            ROOT / name, engine / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
    if architecture is None:
        return
    runtime = engine / "runtime"
    # The same pinned runtime from an earlier build needs no download.
    manifest = engine / "runtime-manifest.json"
    if manifest.exists() and (runtime / "python.exe").exists():
        records = json.loads(manifest.read_text())
        if (
            records["python"]["sha256"] == PYTHON[architecture]
            and {k: v["version"] for k, v in records["wheels"].items()} == PINS
        ):
            print("Reusing the pinned Python engine for", architecture, flush=True)
            return
    clear_runtime(target, runtime, manifest)
    filename = f"python-3.13.15-embed-{architecture}.zip"
    source = download(
        "https://www.python.org/ftp/python/3.13.15/" + filename, PYTHON[architecture], filename
    )
    with zipfile.ZipFile(source) as archive:
        archive.extractall(runtime)
    site = runtime / "Lib/site-packages"
    site.mkdir(parents=True, exist_ok=True)
    records = {"python": {"version": "3.13.15", "sha256": PYTHON[architecture]}, "wheels": {}}
    tag = "win_amd64" if architecture == "amd64" else "win_arm64"
    for name, version in PINS.items():
        with urllib.request.urlopen(
            f"https://pypi.org/pypi/{name}/{version}/json", timeout=45
        ) as response:
            metadata = json.load(response)
        matches = [
            item
            for item in metadata["urls"]
            if item["filename"].endswith(".whl")
            and (
                item["filename"].endswith("-none-any.whl")
                or (
                    "-cp313-" in item["filename"]
                    and item["filename"].endswith("-" + tag + ".whl")
                    and "-cp313t-" not in item["filename"]
                )
            )
        ]
        if len(matches) != 1:
            raise ValueError(f"No unique pinned Windows wheel: {name} {version} {tag}")
        item = matches[0]
        wheel = download(item["url"], item["digests"]["sha256"], item["filename"])
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(site)
        records["wheels"][name] = {
            "version": version,
            "filename": item["filename"],
            "sha256": item["digests"]["sha256"],
        }
    (runtime / "python313._pth").write_text("python313.zip\n.\nLib\\site-packages\nimport site\n")
    (engine / "runtime-manifest.json").write_text(json.dumps(records, indent=2) + "\n")
    print("Bundled pinned Python engine for", architecture, flush=True)


if __name__ == "__main__":
    import sys

    bundle(Path(sys.argv[1]), sys.argv[2])
