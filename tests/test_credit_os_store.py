"""Credit OS's store reads a synthetic workspace built by tests/library_fixtures.py."""

import sys
from pathlib import Path

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
    artifact = {
        "folder": folder,
        "label": "Synthetic report",
        "state": "final",
        "available": True,
        "href": f"/files/{folder}/report.html?sha256=r",
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
    (report,) = result["reports"]
    assert "/files/runs/run-a/deliveries/" in report["href"]
    assert report["href"].split("?")[0].endswith("/report.html")
    assert result["issues"] == []


def test_store_has_no_legacy_routes(tmp_path):
    result = read_store(tmp_path)
    assert result["outputs"] and result["reports"]
    links = [o["href"] for o in result["outputs"].values()]
    for report in result["reports"]:
        links += [report["href"], report["download"], *(f["href"] for f in report["files"])]
    for link in links:
        assert link.startswith("/files/runs/run-a/"), link
