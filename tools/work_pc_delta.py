"""Write the work-PC delta pack: what changed on main since the work PC last synced.

The work PC receives this repository as a ZIP download (no git), already adapted to
its environment. This pack tells it exactly which files, lines and package versions
changed between the commit it last adapted (base) and the commit being downloaded
(head), so it re-adapts only those places. Standard library only; needs git here.

    python tools/work_pc_delta.py generate --base 04e7221            # first pack
    python tools/work_pc_delta.py generate --base "2026-11-10 18:00"  # base by date
    python tools/work_pc_delta.py generate                            # next pack
    python tools/work_pc_delta.py check <folder>                      # on the work PC

Each pack goes to docs/work-pc/syncs/<NNN>_<date>_<base>-<head>/ (CHANGES.md, changes.patch,
SYNC.json); packs chain, each starting where the previous one ended. manifest.json holds
the git blob hash of every file at the latest head, so `check` (no git needed) shows
whether a downloaded copy matches it, i.e. whether the packs cover everything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PACK_DIR = "docs/work-pc"
STATUS = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "T": "type changed"}
SKIPPED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
}
SCOPE = ("--", ".", f":(exclude){PACK_DIR}")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    command = ["git", "-c", "core.quotePath=false", *args]
    return subprocess.run(command, check=False, cwd=root, capture_output=True, encoding="utf-8")


def git(root: Path, *args: str) -> str:
    done = run_git(root, *args)
    if done.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def resolve(root: Path, ref: str, head: str) -> str:
    """A commit-ish, or a date meaning the last first-parent commit of head by then."""
    found = run_git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if found.returncode == 0:
        return found.stdout.strip()
    sha = git(root, "rev-list", "-1", "--first-parent", f"--before={ref}", head).strip()
    if not sha:
        raise SystemExit(f"--base {ref!r} is neither a commit nor a date after the first commit")
    return sha


@dataclass(frozen=True)
class FileChange:
    status: str
    path: str
    old_path: str | None
    added: int | None  # None for binary files
    removed: int | None
    where: str


def new_side_ranges(diff: str) -> str:
    """Line ranges of each hunk in the head version: where to look in the file."""
    parts = []
    for line in diff.splitlines():
        match = HUNK.match(line)
        if match:
            start, count = int(match[1]), int(match[2] or "1")
            if count == 0:
                parts.append(f"removed after L{start}")
            elif count == 1:
                parts.append(f"L{start}")
            else:
                parts.append(f"L{start}-{start + count - 1}")
    return ", ".join(parts)


def line_counts(root: Path, base: str, head: str) -> dict[str, tuple[int | None, int | None]]:
    """Added and removed lines per head path; (None, None) for a binary file."""
    counts: dict[str, tuple[int | None, int | None]] = {}
    fields = iter(git(root, "diff", "-z", "-M", "--numstat", base, head, *SCOPE).split("\0"))
    for field in fields:
        if not field:
            continue
        plus, minus, path = field.split("\t", 2)
        if not path:  # a rename: old and new names follow as separate fields
            next(fields)
            path = next(fields)
        counts[path] = (None, None) if plus == "-" else (int(plus), int(minus))
    return counts


def file_changes(root: Path, base: str, head: str) -> list[FileChange]:
    counts = line_counts(root, base, head)
    changes = []
    tokens = iter(git(root, "diff", "-z", "-M", "--name-status", base, head, *SCOPE).split("\0"))
    for code in tokens:
        if not code:
            continue
        old = next(tokens) if code[0] in "RC" else None
        path = next(tokens)
        paths = [old, path] if old else [path]
        hunks = "" if code[0] == "D" else git(root, "diff", "-U0", "-M", base, head, "--", *paths)
        added, removed = counts.get(path, (None, None))
        changes.append(FileChange(code[0], path, old, added, removed, new_side_ranges(hunks)))
    return changes


def read_toml(root: Path, rev: str, path: str) -> dict[str, Any]:
    shown = run_git(root, "show", f"{rev}:{path}")
    return tomllib.loads(shown.stdout) if shown.returncode == 0 else {}


def locked_versions(lock: dict[str, Any]) -> dict[str, str]:
    versions: dict[str, set[str]] = {}
    for package in lock.get("package", []):
        versions.setdefault(package["name"], set()).add(str(package.get("version", "?")))
    return {name: ", ".join(sorted(found)) for name, found in versions.items()}


def requirement_settings(project: dict[str, Any]) -> dict[str, str]:
    """The pyproject entries that decide what must be installed on the work PC."""
    settings = {
        "requires-python": str(project.get("project", {}).get("requires-python", "")),
        "uv required-version": str(
            project.get("tool", {}).get("uv", {}).get("required-version", "")
        ),
        "dependencies": ", ".join(project.get("project", {}).get("dependencies", [])),
    }
    for group, specs in project.get("dependency-groups", {}).items():
        settings[f"dependency group {group}"] = ", ".join(str(spec) for spec in specs)
    return {key: value for key, value in settings.items() if value}


def compare(before: dict[str, str], after: dict[str, str]) -> list[str]:
    rows = []
    for name in sorted(before.keys() | after.keys()):
        old, new = before.get(name), after.get(name)
        if old == new:
            continue
        rows.append(f"| {name} | {old or '(absent)'} | {new or '(removed)'} |")
    return rows


def dependency_section(root: Path, base: str, head: str) -> list[str]:
    lines = ["## Packages and versions", ""]
    for title, before, after in (
        (
            "pyproject.toml requirements",
            requirement_settings(read_toml(root, base, "pyproject.toml")),
            requirement_settings(read_toml(root, head, "pyproject.toml")),
        ),
        (
            "uv.lock installed versions (direct and transitive)",
            locked_versions(read_toml(root, base, "uv.lock")),
            locked_versions(read_toml(root, head, "uv.lock")),
        ),
    ):
        rows = compare(before, after)
        lines += [f"### {title}", ""]
        if rows:
            lines += ["| Item | Before | After |", "|---|---|---|", *rows]
        else:
            lines.append("No change.")
        lines.append("")
    return lines


def merged_changes(root: Path, base: str, head: str) -> list[str]:
    """Each main commit since base; a merge shows its PR title (the body's first line)."""
    log = git(
        root,
        "log",
        "--first-parent",
        "--reverse",
        "--date=short",
        "--format=%h%x1f%ad%x1f%s%x1f%b%x1e",
        f"{base}..{head}",
    )
    lines = ["## Changes merged to main (oldest first)", ""]
    for record in filter(None, (chunk.strip("\n") for chunk in log.split("\x1e"))):
        sha, date, subject, body = record.split("\x1f", 3)
        title = next((line for line in body.splitlines() if line.strip()), "")
        named = (
            f"{title} ({subject})"
            if subject.startswith("Merge pull request") and title
            else subject
        )
        lines.append(f"- `{sha}` {date} {named}")
    return [*lines, ""] if len(lines) > 2 else [*lines, "None.", ""]


def file_section(changes: list[FileChange]) -> list[str]:
    lines = [
        "## Files changed",
        "",
        "`Where` gives line ranges in the new version; open those lines first.",
        "",
    ]
    by_area: dict[str, list[FileChange]] = {}
    for change in changes:
        by_area.setdefault(
            change.path.split("/", 1)[0] if "/" in change.path else "(root)", []
        ).append(change)
    for area in sorted(by_area):
        lines += [f"### {area}", "", "| Status | File | +/- | Where |", "|---|---|---|---|"]
        for change in by_area[area]:
            name = (
                f"`{change.old_path}` → `{change.path}`" if change.old_path else f"`{change.path}`"
            )
            size = "binary" if change.added is None else f"+{change.added} −{change.removed}"
            status = STATUS.get(change.status, change.status)
            lines.append(f"| {status} | {name} | {size} | {change.where or '—'} |")
        lines.append("")
    return lines


def manifest(root: Path, head: str) -> dict[str, str]:
    """Git blob hash of every regular file at head, outside the pack folder."""
    files = {}
    for entry in git(root, "ls-tree", "-r", "-z", head).split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        mode, kind, sha = meta.split()
        if kind == "blob" and mode in ("100644", "100755") and not path.startswith(PACK_DIR + "/"):
            files[path] = sha
    return files


def blob_hash(data: bytes) -> str:
    """Git's object id for file content, computable without git."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def write_pack(root: Path, base: str, head: str) -> Path:
    changes = file_changes(root, base, head)
    commit_date = git(root, "log", "-1", "--format=%cI", head).strip()
    syncs = root / PACK_DIR / "syncs"
    number = len(list(syncs.glob("[0-9][0-9][0-9]_*"))) + 1 if syncs.is_dir() else 1
    out = syncs / f"{number:03d}_{commit_date[:10]}_{base[:7]}-{head[:7]}"
    out.mkdir(parents=True)
    sync = {
        "base": base,
        "head": head,
        "head_date": commit_date,
        "generated": datetime.now(UTC).isoformat(timespec="seconds"),
        "files_changed": len(changes),
    }
    header = [
        "# Changes for the work PC",
        "",
        (
            f"From `{base[:12]}` (the version the work PC last adapted) to `{head[:12]}` "
            f"({commit_date}). {len(changes)} file(s) changed. "
            "See docs/work-pc/README.md for how to use this."
        ),
        "",
    ]
    body = header + dependency_section(root, base, head) + merged_changes(root, base, head)
    (out / "CHANGES.md").write_text("\n".join(body + file_section(changes)), encoding="utf-8")
    patch = git(root, "diff", "-M", "--binary", base, head, *SCOPE)
    (out / "changes.patch").write_text(patch, encoding="utf-8", newline="\n")
    (out / "SYNC.json").write_text(json.dumps(sync, indent=2) + "\n", encoding="utf-8")
    record = {"head": head, "head_date": commit_date, "files": manifest(root, head)}
    (root / PACK_DIR / "manifest.json").write_text(
        json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def local_files(folder: Path) -> dict[str, Path]:
    """Files under folder by posix path, without the pack folder, caches and environments."""
    found = {}
    for directory, subdirectories, names in os.walk(folder):
        subdirectories[:] = [name for name in subdirectories if name not in SKIPPED_DIRS]
        for name in names:
            path = Path(directory, name)
            relative = path.relative_to(folder).as_posix()
            if not relative.startswith(PACK_DIR + "/"):
                found[relative] = path
    return found


def check(folder: Path, record_path: Path) -> list[str]:
    """Files in folder that differ from, are missing from, or are absent in the manifest."""
    expected: dict[str, str] = json.loads(record_path.read_text(encoding="utf-8"))["files"]
    found = local_files(folder)
    report = [
        f"differs  {name}"
        for name in sorted(expected.keys() & found.keys())
        if blob_hash(found[name].read_bytes()) != expected[name]
    ]
    report += [f"missing  {name}" for name in sorted(expected.keys() - found.keys())]
    report += [f"extra    {name}" for name in sorted(found.keys() - expected.keys())]
    return report


def generate(root: Path, base_ref: str | None, head_ref: str) -> str:
    head = resolve(root, head_ref, head_ref)
    record = root / PACK_DIR / "manifest.json"
    if base_ref is None:
        if not record.is_file():
            raise SystemExit("--base is required until a first pack records manifest.json")
        base_ref = json.loads(record.read_text(encoding="utf-8"))["head"]
    base = resolve(root, base_ref, head)
    if base == head:
        return f"nothing to do: the last pack already ends at {head[:12]}"
    out = write_pack(root, base, head)
    return f"wrote {out.relative_to(root).as_posix()}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("generate", help="write the next pack (needs git)")
    make.add_argument("--base", help="commit or date the work PC last adapted")
    make.add_argument("--head", default="origin/main", help="commit being downloaded")
    verify = commands.add_parser("check", help="compare a folder with manifest.json")
    verify.add_argument("folder", type=Path, help="the downloaded or adapted copy")
    verify.add_argument(
        "--manifest", type=Path, help="default: <folder>/docs/work-pc/manifest.json"
    )
    root = Path(__file__).resolve().parents[1]
    args = parser.parse_args(argv)
    if args.command == "generate":
        print(generate(root, args.base, args.head))
        return 0
    report = check(args.folder, args.manifest or args.folder / PACK_DIR / "manifest.json")
    print("\n".join(report) or "identical to the manifest: the packs cover every change")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
