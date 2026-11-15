"""METHODOLOGY-REVIEW.md's appendix agrees with what CP-OS sends and with the method archive.

Three records state the selected method of each module: the review's appendix table (what the
selection says), ``cpos_launch.METHODS`` (what CP-OS sends) and
``docs/reuse/selected-methods/manifest.json`` (where each archived file came from, with its
hash). This test reads the review and the manifest itself; ``METHODS`` is taken from the launcher
because it is what is sent. Every difference known on 2026-11-15 is listed in ``KNOWN`` with its
reason, so the test passes today, fails on any new difference and fails when a listed one is
resolved without being taken off the list.
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
# The archive's three top-level CP-3B duplicates: on disk, not registered, not sent.
UNREGISTERED = {"CP-3B_RUNBOOK.md", "CP-3B_SCHEMA_REFERENCE.md", "REF_CP-3B_STEPS.md"}

_B57 = "the review names cp-os b57a344 (its 2026-11-10 or 2026-11-13 section); the entry names no "
_B57 += "commit (manifest companions_note dates the 2026-11-10 companions to b57a344)"
_NONE = "neither the review nor the manifest entry names a source revision; the entry gives only "
_NONE += "the cp-os path the file was found at"
_REPO = "project file, not archived in manifest.json; its revision is this repo's git history"
_SKILLS = ARCHIVE + "skills/"
KNOWN: dict[str, str] = {
    f"CP-0 {_SKILLS}cp-0-source-readiness/{name}: source Deploy V, manifest cp-os": (
        "both hold: the entry's file is the cp-os copy and its deploy_v_check records it "
        "byte-identical to Deploy V c4d2e35, which the review names"
    )
    for name in ("SKILL.md", "references/REF_CP-0_STEPS.md")
}
KNOWN[f"CP-DR {_SKILLS}cp-dr-deep-research/SKILL.md: source cp-os, manifest {NOT_RECORDED}"] = (
    "the entry has no exact_copy_found_at or edited_copy_of; its note says cp-os b57a344 plus "
    "named edits"
)
KNOWN.update(
    {
        f"{module} {path}: not registered in manifest.json": _REPO
        for module, path in (
            ("CP-1", "prompts/CP-1.md"),
            ("CP-L10", "src/deploy_vii/methods/cpl10.md"),
            ("CP-8", "src/deploy_vii/methods/cp8.md"),
        )
    }
)
KNOWN.update(
    {
        f"{module} {_SKILLS}{path}: revision b57a344 not in its manifest entry": _B57
        for module, path in (
            ("CP-1A", "cp-1a-business-transaction-fact-pack/SKILL.md"),
            ("CP-1A", "cp-1a-business-transaction-fact-pack/references/REF_CP-1A_STEPS.md"),
            ("CP-1A", "cp-1a-business-transaction-fact-pack/references/REF_CP-2C_STEPS.md"),
            ("CP-1B", "cp-1b-earnings-delta/SKILL.md"),
            ("CP-1B", "cp-1b-earnings-delta/references/REF_CP-1B_STEPS.md"),
            ("CP-2", "cp-2-fundamental-credit-synthesizer/SKILL.md"),
            ("CP-2", "cp-2-fundamental-credit-synthesizer/references/REF_CP-2_STEPS.md"),
            ("CP-2A", "cp-2a-downside-pathway/references/REF_CP-2A_STEPS.md"),
            ("CP-2H", "cp-2h-ratings-migration-trigger/SKILL.md"),
            ("CP-3", "cp-3-relative-value-security-selection/references/CP-3A_RUNBOOK.md"),
            ("CP-3", "cp-3-relative-value-security-selection/references/REF_CP-3B_STEPS.md"),
            ("CP-3", "cp-3-relative-value-security-selection/references/CP-3B_RUNBOOK.md"),
            ("CP-3", "cp-3-relative-value-security-selection/references/CP-3_SCHEMA_REFERENCE.md"),
            ("CP-6", "cp-6-ic-debate-challenge/references/REF_CP-6A_STEPS.md"),
            ("CP-DR", "cp-os-credit-os/references/CP_DR_RESEARCH_BRIEF_V1.md"),
        )
    }
)
KNOWN[f"shared {ARCHIVE}CANON_SHARED.md: revision b57a344 not in its manifest entry"] = _B57
KNOWN[
    f"CP-3C {_SKILLS}cp-3c-refinancing-lme-risk/references/CP-3C_RUNBOOK.md: "
    "revision c4d2e35 not in its manifest entry"
] = "the entry names the Deploy V path without a commit; its two sibling entries name c4d2e35"
KNOWN.update(
    {
        f"{module} {_SKILLS}{path}: the review names no revision": _NONE
        for module, path in (
            ("CP-1C", "cp-1c-peer-benchmark/SKILL.md"),
            ("CP-1C", "cp-1c-peer-benchmark/references/REF_CP-1C_STEPS.md"),
            ("CP-2A", "cp-2a-downside-pathway/SKILL.md"),
            ("CP-2A", "cp-2a-downside-pathway/references/REF_CP-2B_STEPS.md"),
            ("CP-2E", "cp-2e-macro-fx-hedging-sensitivity/SKILL.md"),
            ("CP-2E", "cp-2e-macro-fx-hedging-sensitivity/references/REF_CP-2E_STEPS.md"),
            ("CP-2E", "cp-2e-macro-fx-hedging-sensitivity/references/REF_CP-2F_STEPS.md"),
            ("CP-2G", "cp-2g-forward-credit-model/SKILL.md"),
            ("CP-2H", "cp-2h-ratings-migration-trigger/references/REF_CP-2H_STEPS.md"),
            ("CP-3", "cp-3-relative-value-security-selection/references/REF_CP-3_STEPS.md"),
            ("CP-3", "cp-3-relative-value-security-selection/references/REF_CP-3A_STEPS.md"),
            ("CP-3D", "cp-3d-market-implied-risk/SKILL.md"),
            ("CP-3D", "cp-3d-market-implied-risk/references/REF_CP-3D_STEPS.md"),
            ("CP-4C", "cp-4c-restructuring-fulcrum/references/REF_CP-4C_STEPS.md"),
            ("CP-5", "cp-5-evidence-trace-validator/SKILL.md"),
            ("CP-5", "cp-5-evidence-trace-validator/references/REF_CP-5_STEPS.md"),
            ("CP-6", "cp-6-ic-debate-challenge/references/REF_CP-6_STEPS.md"),
        )
    }
)


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
    data = json.loads((ROOT / ARCHIVE / "manifest.json").read_text(encoding="utf-8"))
    entries = {entry["archive_path"]: entry for entry in data["files"]}
    assert len(entries) == len(data["files"]), "one entry per archived path"
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
    path = str(entry.get("exact_copy_found_at") or entry.get("edited_copy_of") or "")
    consumed = str(entry.get("consumed_path", ""))
    if path in ("", "None"):  # CPOS_REGISTER_SCOPE.md's entry holds the string "None"
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
        assert (row["Source"], row["Edited"], row["Revision"]) == (THIS_REPO, "n/a", THIS_REPO), (
            where
        )
        return [f"{where}: not registered in manifest.json"]
    found: list[str] = []
    source = manifest_source(entry)
    if row["Source"] != source:
        found.append(f"{where}: source {row['Source']}, manifest {source}")
    edited = "yes" if entry.get("edit") or entry.get("edited_copy_of") else "no"
    assert row["Edited"] == edited, where
    # Commit ids are searched outside the hash fields, so a sha256 never matches by accident.
    text = json.dumps({k: v for k, v in entry.items() if k not in ("sha256", "source_sha256")})
    if row["Revision"] == NOT_RECORDED:
        found.append(f"{where}: the review names no revision")
    elif row["Revision"] == THIS_REPO:
        assert source == THIS_REPO, where
    else:
        for commit in row["Revision"].split(", "):
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
        entry = entries.get(row["Method file"])
        assert entry is None or entry["sha256"] == digest, row["Method file"]


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


def test_archive_files_on_disk_are_registered_except_the_named_duplicates() -> None:
    entries = manifest()
    on_disk = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / ARCHIVE).rglob("*")
        # A test that imports an archived script leaves its bytecode cache beside it.
        if path.is_file() and path.name != "manifest.json" and "__pycache__" not in path.parts
    }
    unregistered = on_disk - entries.keys()
    assert unregistered == {ARCHIVE + name for name in UNREGISTERED}
    appendix = review_text().split(APPENDIX, 1)[1]
    for name in UNREGISTERED:
        assert f"`{name}`" in appendix, name
        copy = f"{ARCHIVE}skills/cp-3-relative-value-security-selection/references/{name}"
        assert (ROOT / ARCHIVE / name).read_bytes() == (ROOT / copy).read_bytes(), name
