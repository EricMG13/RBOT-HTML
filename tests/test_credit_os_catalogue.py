"""The Credit OS catalogue over synthetic library runs (tests/library_fixtures.py). Expected values
are written here from the fixture text, not read back from the code under test."""

import hashlib
import json
import sys
from pathlib import Path

from library_fixtures import make_run, method

from deploy_workflow.credit_os_catalogue import catalogue
from deploy_workflow.library_index import build_library

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
from credit_os import store

LEVERAGE = "| FY2024 | 6.57 | 4.93 | x | Same basis; pre-dividend cash. D1, D3. |"
COVER = "| FY2024 | 3.29 | x | Issuer EBITDA / cash interest, net. D1. |"
LIQUIDITY = "| 2024-09-30 | 6261 | 843 | US$m | Available RCF only, after letters of credit. |"
CHARTS = f"""
### Chart data: leverage

| Period | Total debt / EBITDA | Net debt / EBITDA | Reporting unit | Basis and limitation |
| --- | --- | --- | --- | --- |
| FY2023 | 6.33 | 5.22 | x | Earlier year. |
{LEVERAGE}

### Chart data: interest cover

| Period | EBITDA / cash interest | Reporting unit | Basis and limitation |
| --- | --- | --- | --- |
| FY2023 | 2.71 | x | Earlier year. |
{COVER}

### Chart data: liquidity

| Period | Cash | Undrawn committed facilities | Reporting unit | Basis and limitation |
| --- | --- | --- | --- | --- |
| 2023-09-30 | 3472 | 755 | US$m | Earlier year. |
{LIQUIDITY}
"""
CONTEXT = {
    "schema": "context/1",
    "run": {
        "run_type": "research",
        "pathway": "credit_snapshot",
        "case_kind": "public",
        "as_of": "2025-03-31",
        "cutoff": "",
        "current_period": "fy-2024",
        "prior_period": "fy-2023",
        "reporting_currency": "USD",
    },
    "identity": {
        "issuer_name": "Northbridge Synthetic Group",
        "issuer_id": "nbg",
        "borrower_name": "",
        "parent_name": "",
        "guarantors": [],
        "aliases": [],
        "listed_equity": True,
        "ticker": "NBG",
        "sector": "Industrials",
        "country": "United States",
        "sponsor": "",
    },
    "deal_terms": [],
    "quotes": [],
    "ratings": [],
    "valuation": {
        "peer_source": "cp_dr_public",
        "basis": "auto",
        "issuer_market": {
            "market_cap_m": "",
            "net_debt_m": "",
            "ev_m": "",
            "ebitda_basis": "LTM",
            "as_of": "",
            "source": "",
        },
        "peers": [],
        "precedents": [],
        "user_multiple": {"value": "", "basis": "LTM", "rationale": ""},
    },
    "assumptions": {k: None for k in ("cp2a", "cp2d", "cp2e", "cp3c", "cp3d", "cp4c")},
    "attachments": {
        "portfolio_workbook": False,
        "prior_case": False,
        "management_bridge": False,
        "legal_documents": "executed",
    },
    "research_questions": [],
}


def pin_context(run_dir: Path, raw: bytes, pinned_sha: str | None = None) -> None:
    """Pin the context as CP-OS does: workflow.json sources["context"], bytes at inputs/<sha256>."""
    digest = hashlib.sha256(raw).hexdigest()
    (run_dir / "inputs").mkdir(exist_ok=True)
    (run_dir / "inputs" / (pinned_sha or digest)).write_bytes(raw)
    workflow = json.loads((run_dir / "workflow.json").read_text())
    workflow["sources"] = {"context": {"path": "context.json", "sha256": pinned_sha or digest}}
    (run_dir / "workflow.json").write_text(json.dumps(workflow))


def built(workspace: Path) -> dict:
    library = build_library(workspace, workspace / "library", method())
    return catalogue(workspace, library)


def delivered_cp1(run_dir: Path) -> tuple[str, list[str]]:
    (delivery,) = (run_dir / "deliveries").iterdir()
    path = f"runs/{run_dir.name}/deliveries/{delivery.name}/CP-1.md"
    return path, (delivery / "CP-1.md").read_text().split("\n")


def test_catalogue_lists_only_library_runs(tmp_path):
    make_run(tmp_path, "run-a")
    broken = make_run(tmp_path, "run-b")
    (broken / "workflow.json").unlink()  # library_index leaves a non-launcher run out
    result = built(tmp_path)
    assert [run["id"] for run in result["real"]] == ["run-a"]
    assert result["workspace"] == str(tmp_path)


def test_metrics_quote_the_handoff_row(tmp_path):
    run_dir = make_run(tmp_path, "run-a", cp1_extra=CHARTS)
    path, lines = delivered_cp1(run_dir)
    result = built(tmp_path)
    metrics = result["real"][0]["metrics"]
    expected = {
        "leverage": ("6.57", "x", LEVERAGE),
        "net_leverage": ("4.93", "x", LEVERAGE),
        "coverage": ("3.29", "x", COVER),
        "cash": ("6261", "US$m", LIQUIDITY),
        "undrawn": ("843", "US$m", LIQUIDITY),
    }
    assert set(metrics) == set(expected)
    for key, (value, unit, row) in expected.items():
        metric = metrics[key]
        assert (metric["value"], metric["unit"]) == (value, unit)
        source = result["sources"][metric["source"]]
        assert source["quote"] == row
        assert source["line"] == lines.index(row) + 1
        assert source["path"] == path


def newest_first(charts: str) -> str:
    """CHARTS with each table's earlier-year row moved below the latest one."""
    lines = charts.split("\n")
    for index in range(len(lines) - 2, -1, -1):
        if "Earlier year." in lines[index]:
            lines[index], lines[index + 1] = lines[index + 1], lines[index]
    return "\n".join(lines)


def test_metrics_take_the_latest_period_not_the_last_row(tmp_path):
    run_dir = make_run(tmp_path, "run-a", cp1_extra=newest_first(CHARTS))
    _, lines = delivered_cp1(run_dir)
    result = built(tmp_path)
    metrics = result["real"][0]["metrics"]
    assert {k: m["value"] for k, m in metrics.items()} == {
        "leverage": "6.57",
        "net_leverage": "4.93",
        "coverage": "3.29",
        "cash": "6261",
        "undrawn": "843",
    }
    assert {m["period"] for m in metrics.values()} == {"FY2024", "2024-09-30"}
    for row in (LEVERAGE, COVER, LIQUIDITY):
        quoted = [s for s in result["sources"].values() if s["quote"] == row]
        assert quoted and all(s["line"] == lines.index(row) + 1 for s in quoted)
    assert result["issues"] == []


def test_periods_that_cannot_be_ordered_give_no_metric_and_an_issue(tmp_path):
    charts = CHARTS.replace("| FY2023 | 6.33", "| Q1 FY2023 | 6.33")
    make_run(tmp_path, "run-a", cp1_extra=charts)
    result = built(tmp_path)
    metrics = result["real"][0]["metrics"]
    assert "leverage" not in metrics and "net_leverage" not in metrics
    assert {"coverage", "cash", "undrawn"} <= set(metrics)
    (issue,) = [i for i in result["issues"] if "leverage" in i]
    assert issue.startswith("run-a: CP-1 leverage table has no metric")


def test_not_supplied_is_absent(tmp_path):
    charts = CHARTS.replace("| 3.29 |", "| Not supplied: no cash interest line |")
    charts = charts.replace("| 4.93 |", "| Not supplied: no net debt |")
    make_run(tmp_path, "run-a", cp1_extra=charts)
    metrics = built(tmp_path)["real"][0]["metrics"]
    assert "coverage" not in metrics
    assert "net_leverage" not in metrics
    assert metrics["leverage"]["value"] == "6.57"


def test_identity_from_context(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    pin_context(run_dir, json.dumps(CONTEXT).encode())
    run = built(tmp_path)["real"][0]
    assert (run["issuer"], run["name"], run["sector"], run["country"]) == (
        "NBG",
        "Northbridge Synthetic Group",
        "Industrials",
        "United States",
    )
    assert (run["currency"], run["date"]) == ("USD", "2025-03-31")
    assert (run["period"], run["period_kind"], run["title"]) == (
        "FY-2024",
        "Annual",
        "Credit Snapshot",
    )
    assert run["summary"] == "CP-1 bottom line."
    assert run["gaps"] == ["Synthetic fixture only."]


def test_context_not_matching_its_pin_is_an_issue_with_empty_fields(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    pin_context(run_dir, json.dumps(CONTEXT).encode(), pinned_sha="0" * 64)
    result = built(tmp_path)
    run = result["real"][0]
    assert run["issuer"] == "NBG"  # issuer_id upper, not the unpinned ticker
    assert (run["sector"], run["country"], run["currency"], run["period"]) == ("", "", "", "")
    assert any(i.startswith("run-a: context not used") for i in result["issues"])


def test_context_the_rules_refuse_is_an_issue_with_empty_fields(tmp_path):
    run_dir = make_run(tmp_path, "run-a")
    pin_context(run_dir, json.dumps({**CONTEXT, "schema": "other"}).encode())
    result = built(tmp_path)
    assert result["real"][0]["sector"] == ""
    assert any("context not used" in i for i in result["issues"])


def test_run_without_context_leaves_fields_empty(tmp_path):
    make_run(tmp_path, "run-a")
    run = built(tmp_path)["real"][0]
    assert run["issuer"] == "NBG"
    assert (run["sector"], run["country"], run["currency"], run["period"]) == ("", "", "", "")
    assert run["checklist"] is None


def test_store_joins_the_catalogue(tmp_path):
    make_run(tmp_path, "run-a", cp1_extra=CHARTS)
    result = built(tmp_path)
    (artifact,) = result["real"][0]["artifacts"]
    assert artifact["available"] and "/report.html?sha256=" in artifact["href"]
    joined = store.workspace_store(tmp_path, result)
    assert {o["module"] for o in joined["outputs"].values()} == {"CP-0", "CP-1"}
    (report,) = joined["reports"]
    assert report["href"].split("?")[0].endswith("/report.html")
    assert joined["issues"] == []
