"""METHODOLOGY-REVIEW.md's appendix agrees with what CP-OS sends and with the method archive.

Three records state the selected method of each module: the review's appendix table (what the
selection says), ``cpos_launch.METHODS`` (what CP-OS sends) and
``docs/reuse/selected-methods/manifest.json`` (where each sent file came from, at which revision,
with its hash). This test reads the review and the manifest itself; ``METHODS`` is taken from the
launcher because it is what is sent. A difference accepted as known goes in ``KNOWN`` with its
reason; the test fails on any other difference and when a listed one is resolved without being
taken off the list. A revision no one recorded is not a difference when both records say so.
"""

import hashlib
import json
import re
from pathlib import Path

from deploy_workflow.owners.cpos_launch import METHODS

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "docs/reuse/selected-methods/"
APPENDIX = "## Appendix: selected method files"
NOT_RECORDED = "not recorded"
THIS_REPO = "this repo"
COLUMNS = ["Module", "Method file", "Source", "Edited", "Revision", "sha256"]
# The file entered the archive with no commit recorded; the manifest entry says so in these words.
NOT_RECORDED_AT_IMPORT = "not recorded at import"
DEPLOY_V_COPY = " (byte-identical to Deploy V)"
# Differences between the review and the manifest that are known and accepted, each with its
# reason. The provenance gaps of 2026-11-15 were fixed on that day (owner: "fix"); none remain.
KNOWN: dict[str, str] = {}


def review_text() -> str:
    return (ROOT / "METHODOLOGY-REVIEW.md").read_text(encoding="utf-8")


def appendix_rows() -> list[dict[str, str]]:
    """The appendix table, one dict per row keyed by COLUMNS, backticks removed."""
    text = review_text()
    assert text.count(APPENDIX + "\n") == 1
    lines = text.split(APPENDIX + "\n", 1)[1].splitlines()
    table = [line for line in lines if line.startswith("|")]
    first = lines.index(table[0])
    assert lines[first : first + len(table)] == table, "the appendix holds one contiguous table"
    cells = [[cell.strip().strip("`") for cell in line.strip("|").split("|")] for line in table]
    assert cells[0] == COLUMNS and set(cells[1][0]) <= set("-")
    return [dict(zip(COLUMNS, row, strict=True)) for row in cells[2:]]


def manifest() -> dict[str, dict[str, object]]:
    """Archived files by `archive_path` and the project's own sent method files by `path`."""
    data = json.loads((ROOT / ARCHIVE / "manifest.json").read_text(encoding="utf-8"))
    entries = {entry["archive_path"]: entry for entry in data["files"]}
    entries |= {entry["path"]: entry for entry in data["project_files"]}
    assert len(entries) == len(data["files"]) + len(data["project_files"]), "one entry per path"
    return entries


def sent() -> dict[str, set[str]]:
    """Per module the whole files sent; a file sent by `path § heading` section is `shared`."""
    rows: dict[str, set[str]] = {}
    for module, names in METHODS.items():
        for name in names:
            path, section, _ = name.partition(" § ")
            rows.setdefault("shared" if section else module, set()).add(path)
    return rows


def manifest_source(entry: dict[str, object]) -> str:
    """Where the manifest says the archived bytes came from, as the appendix names sources."""
    if entry.get("source") == "this repository":
        return THIS_REPO
    path = str(entry.get("exact_copy_found_at") or entry.get("edited_copy_of") or "")
    consumed = str(entry.get("consumed_path", ""))
    if not path:
        path = consumed if consumed.startswith("/") else ""
    if THIS_REPO in path or (not path and str(entry.get("use", "")).startswith("project-written")):
        return THIS_REPO
    parts = Path(path.split(" (")[0]).parts
    return next(
        (name for name in ("cp-os", "caos-databricks", "Deploy V") if name in parts), NOT_RECORDED
    )


def differences(row: dict[str, str], entry: dict[str, object] | None) -> list[str]:
    """How one appendix row differs from its file's manifest entry."""
    where = f"{row['Module']} {row['Method file']}"
    if entry is None:
        return [f"{where}: not registered in manifest.json"]
    found: list[str] = []
    source = manifest_source(entry)
    named, copy, _ = row["Source"].partition(DEPLOY_V_COPY)
    checked = str(entry.get("deploy_v_check", "")).startswith("byte-identical to Deploy V ")
    if named != source or bool(copy) != checked:
        found.append(f"{where}: source {row['Source']}, manifest {source}")
    edited = "yes" if entry.get("edit") or entry.get("edited_copy_of") else "no"
    assert row["Edited"] == edited, where
    return found + revision_differences(where, row["Revision"], entry, source)


def revision_differences(
    where: str, revision: str, entry: dict[str, object], source: str
) -> list[str]:
    """How the row's Revision differs from the commits its manifest entry records."""
    unrecorded = str(entry.get("source_revision", "")).startswith(NOT_RECORDED_AT_IMPORT)
    if (revision == NOT_RECORDED) != unrecorded:
        return [f"{where}: revision {revision}, manifest {NOT_RECORDED_AT_IMPORT}: {unrecorded}"]
    if revision in (NOT_RECORDED, THIS_REPO):
        assert revision == NOT_RECORDED or source == THIS_REPO, where
        return []
    # Commit ids are searched outside the hash fields, so a sha256 never matches by accident.
    text = json.dumps({k: v for k, v in entry.items() if k not in ("sha256", "source_sha256")})
    found: list[str] = []
    for commit in revision.split(", "):
        assert re.fullmatch(r"[0-9a-f]{7,40}", commit), where
        if not re.search(rf"\b{commit}", text):
            found.append(f"{where}: revision {commit} not in its manifest entry")
    return found


def test_the_appendix_lists_exactly_the_files_cpos_sends() -> None:
    rows = appendix_rows()
    listed: dict[str, set[str]] = {}
    for row in rows:
        listed.setdefault(row["Module"], set()).add(row["Method file"])
    assert len(rows) == sum(len(files) for files in listed.values()), "no row is listed twice"
    assert listed == sent()


def test_each_row_names_the_bytes_on_disk_and_in_the_manifest() -> None:
    entries = manifest()
    for row in appendix_rows():
        digest = hashlib.sha256((ROOT / row["Method file"]).read_bytes()).hexdigest()
        assert row["sha256"] == digest[:12], row["Method file"]
        assert entries[row["Method file"]]["sha256"] == digest, row["Method file"]


def test_the_review_and_the_manifest_differ_only_where_known() -> None:
    entries = manifest()
    found = [
        diff
        for row in appendix_rows()
        for diff in differences(row, entries.get(row["Method file"]))
    ]
    assert len(found) == len(set(found))
    assert sorted(set(found) - KNOWN.keys()) == [], "new differences"
    assert sorted(KNOWN.keys() - set(found)) == [], "resolved: take them off KNOWN"


def test_registered_files_not_sent_are_counted_in_the_review() -> None:
    entries = manifest()
    sent_paths = set().union(*sent().values())
    not_sent = [path for path in entries if path not in sent_paths]
    assert all((ROOT / path).is_file() for path in entries)
    stated = re.findall(r"registers (\d+) further files that CP-OS does not send", review_text())
    assert stated == [str(len(not_sent))]


def test_archive_files_on_disk_are_all_registered() -> None:
    entries = manifest()
    on_disk = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / ARCHIVE).rglob("*")
        # A test that imports an archived script leaves its bytecode cache beside it.
        if path.is_file() and path.name != "manifest.json" and "__pycache__" not in path.parts
    }
    assert on_disk - entries.keys() == set()
