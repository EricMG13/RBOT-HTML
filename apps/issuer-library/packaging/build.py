"""Build the Windows packages: pinned Python, the engine and the static library. No compiler, no
server and no provider call; the runtime and wheels are verified against their SHA-256 digests."""

import hashlib
import shutil
import zipfile
from pathlib import Path

from runtime import bundle

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
OUTPUT = ROOT / "artifacts/issuer-library"


def main() -> None:
    for architecture in ("amd64", "arm64"):
        target = OUTPUT / f"windows-{architecture}"
        target.mkdir(parents=True, exist_ok=True)
        bundle(target, architecture)
        shutil.copyfile(APP / "README.md", target / "README.md")
        shutil.copyfile(ROOT / "src/deploy_vii/assets/fonts/OFL.txt", target / "FONT-LICENSE.txt")
        archive = OUTPUT / f"Issuer-Library-{architecture}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
            for file in sorted(target.rglob("*")):
                if file.is_file():
                    handle.write(file, file.relative_to(target))
        print(f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}")


if __name__ == "__main__":
    main()
