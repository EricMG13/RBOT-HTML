"""Update the Issuer Library: the static Credit OS library and issuer pages of completed runs.

    python apps/issuer-library/update_library.py [--workspace FOLDER]

Reads ``FOLDER/runs`` (default: this checkout; the Windows package needs ``--workspace``, which
``Update library.cmd`` supplies) and writes only ``FOLDER/library/``: ``index.html`` with its
scripts, styles, fonts and icons, ``data.js`` (the catalogue and the workspace store, as data),
and ``reports/<run>/<delivery>/report.html``, each run's delivered report with the library's
presentation added. The delivered reports themselves are never changed. The page opens from disk:
no server, no network access. Which runs it lists is decided by ``deploy_workflow.library_index``.
No analysis is run and no provider is called.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit

HERE = Path(__file__).resolve().parent
WEB = HERE / "credit_os" / "web"
PACKAGED = (HERE / "src").is_dir()  # The Windows package keeps the engine's src beside this file.
ROOT = HERE if PACKAGED else HERE.parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from credit_os.store import regular_chunks, workspace_store

from deploy_vii.registry import dependencies, edge_rule, plan
from deploy_workflow.credit_os_catalogue import catalogue
from deploy_workflow.credit_os_chips import chips
from deploy_workflow.library_index import (
    Library,
    Refused,
    build_library,
    read_pinned,
)
from deploy_workflow.run_events import read_events

# Nothing is fetched: the page and the reports it frames come from its own folder, and no request
# can leave it.
POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; "
    "img-src 'self' data:; frame-src 'self'; connect-src 'none'; base-uri 'none'; "
    "form-action 'none'"
)
CSP_META = f'<meta http-equiv="Content-Security-Policy" content="{POLICY}">'
FILES = "/files/"


def last_body_close(html: bytes) -> int:
    """Offset of the final ``</body>`` in html, len(html) when there is none (ASCII case-fold)."""
    found = html.lower().rfind(b"</body>")
    return len(html) if found < 0 else found


def present_report(original: bytes) -> bytes:
    """The delivered report with the library's presentation inserted before its last ``</body>``."""
    style = (WEB / "report-adapter.css").read_bytes()
    brand = (WEB / "brand.css").read_bytes()
    script = (WEB / "report-adapter.js").read_bytes()
    position = last_body_close(original)
    return b"".join(
        [
            original[:position],
            b"<style data-library-presentation>",
            style,
            brand,
            b"</style><script data-library-presentation>",
            script,
            b"</script>",
            original[position:],
        ]
    )


def write_presented_reports(workspace: Path, library: Library, folder: Path) -> set[str]:
    """Each listed run's verified report, presented, under ``folder/reports``.

    Returns the workspace-relative paths of the originals that have a presented copy."""
    presented = set()
    for run in library.runs:
        run_dir = workspace / "runs" / run["id"]
        verified = library.deliveries[run["id"]]  # This build verified every file of it already.
        relative, files = verified["folder"], verified["files"]
        original = read_pinned(run_dir, f"{relative}/report.html", files["report.html"])
        target = folder / "reports" / run["id"] / relative.split("/", 1)[1] / "report.html"
        target.parent.mkdir(parents=True)
        target.write_bytes(present_report(original))
        presented.add(f"runs/{run['id']}/{relative}/report.html")
    return presented


def relative_href(href: str, presented: set[str]) -> str:
    """A server ``/files/...`` href as a path from ``library/index.html``, query removed.

    A report opened for reading points at its presented copy; a download keeps the original."""
    parts = urlsplit(href)
    path = unquote(parts.path)[len(FILES) :]
    if "download=1" not in parts.query and path in presented:
        _, run, _, delivery, name = path.split("/")
        return quote(f"reports/{run}/{delivery}/{name}", safe="/")
    return "../" + quote(path, safe="/")


def relocate(value: Any, presented: set[str]) -> Any:
    """``value`` with every ``/files/...`` string rewritten by ``relative_href``."""
    if isinstance(value, str):
        return relative_href(value, presented) if value.startswith(FILES) else value
    if isinstance(value, list):
        return [relocate(item, presented) for item in value]
    if isinstance(value, dict):
        return {key: relocate(item, presented) for key, item in value.items()}
    return value


def embedded_json(value: object) -> str:
    """JSON that cannot end its ``<script>`` element or open a comment inside it."""
    return json.dumps(value, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c")


def run_events(
    run_dir: Path, folder: str, issues: list[str]
) -> tuple[list[dict[str, Any]], str | None]:
    """Read events or return a named failure; a missing log has no events and no failure."""
    path = run_dir / "events.jsonl"
    if not path.is_symlink() and not path.exists():
        return [], None  # A replay or a run that never started: normal.
    try:
        if path.is_symlink() or not path.is_file():
            raise ValueError("not a regular file")
        events = read_events(path)
        if any(not isinstance(event, dict) for event in events):
            raise ValueError("event is not an object")
        return events, None
    except (OSError, ValueError) as error:
        issues.append(f"{folder}: events.jsonl could not be read ({type(error).__name__})")
        return [], type(error).__name__


def run_record(run_dir: Path, folder: str, issues: list[str]) -> dict[str, Any] | None:
    """The method's dependency edges for the run's requested modules (deploy_vii.registry, with
    each edge's degradation rule) and the modules in recorded order with the times its event log
    states. Nothing is written, and no time is made up: a module with no event has none."""
    try:
        raw = json.loads(b"".join(regular_chunks(run_dir / "workflow.json", follow=False)))
        requested = tuple(raw["run"]["requested_modules"])
        order, deps = plan(requested), dependencies(requested)
        edges = [
            [producer, consumer, edge_rule(consumer, producer)]
            for consumer in order
            for producer in sorted(deps[consumer])
        ]
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        issues.append(f"{folder}: run record could not be read ({type(error).__name__})")
        return None
    events, events_issue = run_events(run_dir, folder, issues)
    seen: dict[str, dict[str, str | None]] = {}
    for event in events:
        module, at = event.get("module"), event.get("at")
        name = event.get("event")
        kind = {"module_started": "started", "module_accepted": "accepted"}.get(str(name))
        if kind and isinstance(module, str) and isinstance(at, str):
            seen.setdefault(module, {"started": None, "accepted": None})
            seen[module][kind] = seen[module][kind] or at
    started = [m for m, t in seen.items() if t["started"]]
    steps = [{"module": m, **seen[m]} for m in started]
    steps += [{"module": m, "started": None, "accepted": None} for m in order if m not in started]
    record = {"edges": edges, "steps": steps, "timed": bool(started)}
    if events_issue:
        record["eventsIssue"] = events_issue
    return record


def run_records(workspace: Path, store: dict[str, Any]) -> None:
    """Add each shown run's `record` (see run_record) to the store, reading the run folder only."""
    for run in store["runs"].values():
        record = run_record(workspace / "runs" / run["folder"], run["folder"], store["issues"])
        if record:
            run["record"] = record


def build_into(folder: Path, workspace: Path, library: Library) -> None:
    shutil.copytree(WEB, folder, ignore=shutil.ignore_patterns("*.test.cjs"), dirs_exist_ok=True)
    cat = catalogue(workspace, library)
    store = workspace_store(workspace, cat)
    run_records(workspace, store)
    presented = write_presented_reports(workspace, library, folder)
    # Run activity, as data: the folders left out and why, and every issue the build recorded
    # (the store's list already holds the catalogue's; each is kept once, in order).
    activity = {
        "excluded": [[name, reason] for name, reason in library.excluded],
        "issues": list(dict.fromkeys([*cat["issues"], *store["issues"]])),
    }
    data = relocate(
        {
            "catalogue": cat,
            "workspace": store,
            "activity": activity,
            "chips": chips(workspace, store),
        },
        presented,
    )
    (folder / "data.js").write_text(
        "window.CREDIT_OS_DATA=" + embedded_json(data) + ";\n", encoding="utf-8", newline="\n"
    )
    page = folder / "index.html"
    html = page.read_text(encoding="utf-8")
    if "<head>" not in html:
        raise Refused("Not written: the page template has no <head> to hold its policy")
    page.write_text(html.replace("<head>", "<head>\n  " + CSP_META, 1), encoding="utf-8")


def remove_folder(folder: Path) -> None:
    """Remove a leftover build folder; a failure is reported on stderr, not hidden."""

    def report(function: Any, path: str, error: BaseException) -> None:
        print(f"Could not remove {path}: {error}", file=sys.stderr)

    if folder.exists():
        shutil.rmtree(folder, onexc=report)


def update_library(workspace: Path) -> Library:
    """Rebuild ``workspace/library`` whole: built beside it, then swapped in.

    Raises ``library_index.Refused`` (a ValueError) when the workspace or ``library`` cannot be
    used; only ``main`` turns that into an exit."""
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise Refused(f"Workspace not found: {workspace}")
    target = workspace / "library"
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise Refused(f"Not written: {target} is a link or a file, not the library folder")
    library = build_library(workspace, target)
    staging = Path(tempfile.mkdtemp(dir=workspace, prefix=".library-new-"))
    old = workspace / ".library-old"
    try:
        build_into(staging, workspace, library)
        staging.chmod(0o755)  # mkdtemp makes it owner-only; the page is shared like the reports.
        remove_folder(old)
        had_library = target.exists()
        if had_library:
            target.rename(old)
        try:
            staging.rename(target)
        except OSError:
            if had_library:
                old.rename(target)  # The previous library stays if the new one cannot be placed.
            raise
        remove_folder(old)
    finally:
        remove_folder(staging)
    return library


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--workspace", type=Path, default=None if PACKAGED else ROOT, help="folder holding runs/"
    )
    args = parser.parse_args(argv)
    if args.workspace is None:
        parser.error("give --workspace: the folder holding runs/")
    try:
        library = update_library(args.workspace)
    except Refused as error:
        raise SystemExit(str(error)) from error
    print(f"Listed {len(library.runs)} run(s) on the current methodology.")
    for run in library.runs:
        print(f"  {run['id']}: {run['issuer_name']}, as of {run['as_of']}")
    if library.excluded:
        print(f"Not shown: {len(library.excluded)} run folder(s).")
        for name, reason in library.excluded:
            print(f"  {name}: {reason}")
    print(f"Open {args.workspace.resolve() / 'library' / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
