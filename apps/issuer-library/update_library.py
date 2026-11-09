"""Update the Issuer Library: one static page of completed runs on the current methodology.

    python apps/issuer-library/update_library.py [--workspace FOLDER]

Reads ``FOLDER/runs`` (default: this checkout; the Windows package needs ``--workspace``, which
``Update library.cmd`` supplies) and writes only ``FOLDER/library/index.html``. The
page holds its data, styles, script and fonts, links to the runs' original reports and handoffs by
relative path, and opens from disk: no server, no network access. Which runs it lists is decided
by ``deploy_workflow.library_index``. No analysis is run and no provider is called.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
PACKAGED = (HERE / "src").is_dir()  # The Windows package keeps the engine's src beside this file.
ROOT = HERE if PACKAGED else HERE.parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from deploy_workflow.library_index import Library, build_library

SCHEMA = "issuer-library/2"
FONTS = (
    ("Red Hat Display", "RedHatDisplay-SemiBold.woff2", 600),
    ("Red Hat Display", "RedHatDisplay-Bold.woff2", 700),
    ("Red Hat Text", "RedHatText-Regular.woff2", 400),
    ("Red Hat Text", "RedHatText-Medium.woff2", 500),
    ("Red Hat Text", "RedHatText-SemiBold.woff2", 600),
    ("Red Hat Mono", "RedHatMono-Medium.woff2", 500),
    ("Red Hat Mono", "RedHatMono-SemiBold.woff2", 600),
)
_PLACEHOLDER = re.compile(r"/\*(DATA|STYLE|LOGIC|APP|FONTS|LOGO|LICENSE)\*/")


def deliverable_assets() -> Path:
    """The deliverables' own design assets, wherever the engine's packages are installed."""
    import deploy_vii

    return Path(deploy_vii.__file__).resolve().parent / "assets"


def assets() -> dict[str, str]:
    shared = deliverable_assets()
    fonts = []
    for family, file, weight in FONTS:
        encoded = base64.b64encode((shared / "fonts" / file).read_bytes()).decode()
        fonts.append(
            f'@font-face{{font-family:"{family}";font-weight:{weight};font-display:swap;'
            f'src:url(data:font/woff2;base64,{encoded}) format("woff2")}}'
        )
    logo = (shared / "brand/ssim-logo-stacked-black-trim.png").read_bytes()
    return {
        "FONTS": "\n".join(fonts),
        "STYLE": "".join(
            (path).read_text(encoding="utf-8")
            for path in (shared / "tokens.css", shared / "app.css", STATIC / "library.css")
        ),
        "LOGIC": (STATIC / "logic.js").read_text(encoding="utf-8"),
        "APP": (STATIC / "app.js").read_text(encoding="utf-8"),
        "LOGO": "data:image/png;base64," + base64.b64encode(logo).decode(),
        "LICENSE": (shared / "fonts/OFL.txt").read_text(encoding="utf-8").replace("--", "—"),
    }


def page_data(library: Library, workspace: Path, built_at: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "built_at": built_at,
        "workspace": str(workspace),
        "runs": library.runs,
        "not_shown": [{"folder": name, "reason": reason} for name, reason in library.excluded],
    }


def embedded_json(value: object) -> str:
    """JSON that cannot end its ``<script>`` element or open a comment inside it."""
    return json.dumps(value, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c")


def render_page(template: str, data: dict[str, Any], parts: dict[str, str]) -> str:
    """Fill each placeholder once; inserted text is never searched for placeholders again."""
    replacements = parts | {"DATA": embedded_json(data)}
    return _PLACEHOLDER.sub(lambda match: replacements[match[1]], template)


def write_page(page_dir: Path, html: str) -> Path:
    """Replace ``page_dir/index.html`` whole, through a temporary file beside it."""
    if page_dir.is_symlink() or (page_dir.exists() and not page_dir.is_dir()):
        raise SystemExit(f"Not written: {page_dir} is a link or a file, not the library folder")
    page_dir.mkdir(exist_ok=True)
    target = page_dir / "index.html"
    descriptor, name = tempfile.mkstemp(dir=page_dir, prefix=".index-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(html)
        os.chmod(name, 0o644)  # mkstemp makes it owner-only; the page is shared like the reports.
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)
    return target


def update(workspace: Path, built_at: str | None = None) -> tuple[Path, Library]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise SystemExit(f"Workspace not found: {workspace}")
    page_dir = workspace / "library"
    library = build_library(workspace, page_dir)
    stamp = built_at or datetime.now(UTC).strftime("%d %b %Y, %H:%M UTC")
    template = (STATIC / "template.html").read_text(encoding="utf-8")
    html = render_page(template, page_data(library, workspace, stamp), assets())
    return write_page(page_dir, html), library


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--workspace", type=Path, default=None if PACKAGED else ROOT, help="folder holding runs/"
    )
    args = parser.parse_args(argv)
    if args.workspace is None:
        parser.error("give --workspace: the folder holding runs/")
    target, library = update(args.workspace)
    print(f"Listed {len(library.runs)} run(s) on the current methodology.")
    for run in library.runs:
        print(f"  {run['id']}: {run['issuer_name']}, as of {run['as_of']}")
    if library.excluded:
        print(f"Not shown: {len(library.excluded)} run folder(s).")
        for name, reason in library.excluded:
            print(f"  {name}: {reason}")
    print(f"Open {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
