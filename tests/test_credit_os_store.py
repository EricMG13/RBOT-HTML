"""Credit OS's store reads a synthetic workspace built by tests/library_fixtures.py."""

import hashlib
import sys
from pathlib import Path

import pytest
from library_fixtures import make_run

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
from credit_os import store

MODULES = ("CP-0", "CP-1")


def read_store(tmp_path: Path) -> dict:
    """The store over one fixture run that the catalogue lists with its delivery as a report."""
    run_dir = make_run(tmp_path, "run-a")
    (delivery,) = (run_dir / "deliveries").iterdir()
    folder = f"runs/run-a/deliveries/{delivery.name}"
    (report,) = delivery.glob("report.html")
    digest = hashlib.sha256(report.read_bytes()).hexdigest()
    artifact = {
        "folder": folder,
        "label": "Synthetic report",
        "state": "final",
        "available": True,
        "href": f"/files/{folder}/report.html?sha256={digest}",
    }
    row = {"id": "run-a", "name": "run-a", "sector": "", "period": "", "artifacts": [artifact]}
    return store.workspace_store(tmp_path, {"real": [row], "issues": []})


def test_store_reads_a_listed_run(tmp_path):
    result = read_store(tmp_path)
    by_module = {o["module"]: o for o in result["outputs"].values()}
    assert set(by_module) == set(MODULES)
    for output in by_module.values():
        assert output["run"] == "run-a"
        assert output["sha256"] in result["handoffs"]
    handoff_digests = {
        hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (tmp_path / "runs/run-a/deliveries").glob("*/CP-*.md")
    }
    assert {o["sha256"] for o in result["outputs"].values()} == handoff_digests
    (report,) = result["reports"]
    assert "/files/runs/run-a/deliveries/" in report["href"]
    assert report["href"].split("?")[0].endswith("/report.html")
    assert result["issues"] == []


def test_store_has_no_legacy_routes(tmp_path):
    result = read_store(tmp_path)
    assert result["pins"] == {}
    assert set(result["runs"]) == {"run-a"}
    assert result["outputs"] and result["reports"]
    links = [o["href"] for o in result["outputs"].values()]
    for report in result["reports"]:
        links += [report["href"], report["download"], *(f["href"] for f in report["files"])]
    for link in links:
        assert link.startswith("/files/runs/run-a/"), link


# Copied verbatim from the 2026-11-09 sol-medium run (runs/cpos-tdg-sol-medium-all-001, delivery
# abd687ca...c2baa, CP-1C.md): the head of a handoff that opens with YAML front matter.
REAL_FRONT_MATTER_HEAD = (
    Path(__file__).parent / "fixtures/sol_medium_run_2026_11_09/CP-1C-head.md"
).read_text(encoding="utf-8")


def test_yaml_front_matter_is_kept_as_a_leading_section():
    sections = store.parse_source(REAL_FRONT_MATTER_HEAD + "\nBody line.\n")
    lines = REAL_FRONT_MATTER_HEAD.split("\n")
    close = lines.index("---", 1)
    first, second = sections[0], sections[1]
    assert (first["heading"], first["level"], first["line"]) == ("Front matter", 2, 1)
    (block,) = first["blocks"]
    assert block["type"] == "text" and block["line"] == 2 and block["end"] == close
    assert block["text"] == "\n".join(lines[1:close])
    assert second["heading"] == "Request" and second["level"] == 2


def test_an_unclosed_front_matter_marker_still_raises():
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("---\nissuer_id: tdg\n\n## Request\n")
