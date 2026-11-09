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


FRONT = "---\nmodule: CP-2A\nas_of: 2026-01-01\n---\n\n## Request\nWhat is asked.\n"


def test_front_matter_is_the_first_section_verbatim():
    sections = store.parse_source(FRONT)
    assert sections[0] == {
        "heading": "Front matter",
        "level": 1,
        "line": 1,
        "blocks": [
            {"type": "text", "line": 1, "end": 4, "text": "module: CP-2A\nas_of: 2026-01-01"}
        ],
    }
    assert sections[1] == {
        "heading": "Request",
        "level": 2,
        "line": 6,
        "blocks": [{"type": "text", "line": 7, "end": 7, "text": "What is asked."}],
    }
    assert len(sections) == 2


def test_other_body_before_the_first_heading_still_raises():
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("preamble\n## Request\nx\n")
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("---\nkey: v\n---\nstray\n## Request\nx\n")


def test_unterminated_front_matter_raises():
    with pytest.raises(ValueError, match="Body before first heading"):
        store.parse_source("---\nkey: v\n\n## Request\nx\n")


def test_structured_accepts_front_matter():
    sections, error = store.structured(FRONT.encode(), strict=False)
    assert error is None
    assert sections[0]["heading"] == "Front matter"
