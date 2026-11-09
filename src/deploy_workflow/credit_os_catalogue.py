"""The Credit OS catalogue built from the runs the Issuer Library lists. Reads files only.

Credit OS's library screens read one JSON (``apps/issuer-library/credit_os/store.py``):
``{"real": [run, ...], "sources": {...}, "workspace": ..., "issues": [...]}``.
A run here is a record ``library_index`` admitted, so every handoff is read through the delivery
copy whose path and sha256 it verified, never from a folder it left out. A value the run does not
state is left empty or absent, never filled in.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from deploy_workflow.library_index import (
    Library,
    Refused,
    delivery_folder,
    json_object,
    read_inside,
    read_pinned,
)

SEGMENT_SAFE = "$&+:=@"  # What url.PathEscape keeps in one path segment.
LISTED = {".md", ".txt", ".pdf", ".html", ".htm", ".json", ".csv", ".xlsx"}
RUN_FILE_LIMIT = 5000
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_PERIOD = re.compile(r"^(q[1-4]|h[12]|fy)-\d{4}$")
_PERIOD_KINDS = {"f": "Annual", "h": "Half-year", "q": "Quarterly"}  # By first letter.
_NOT_SUPPLIED = "Not supplied"
# (chart table, metric key, value column) in the CP-1 handoff; the unit and basis columns are
# the table's own "Reporting unit" and "Basis and limitation".
_METRICS = (
    ("leverage", "leverage", "Total debt / EBITDA"),
    ("leverage", "net_leverage", "Net debt / EBITDA"),
    ("interest cover", "coverage", "EBITDA / cash interest"),
    ("liquidity", "cash", "Cash"),
    ("liquidity", "undrawn", "Undrawn committed facilities"),
)


def file_url(name: str) -> str:
    return "/files/" + "/".join(quote(part, safe=SEGMENT_SAFE) for part in name.split("/"))


def pinned_url(name: str, sha256: str) -> str:
    return f"{file_url(name)}?sha256={sha256}"


def pathway_title(pathway: str) -> str:
    from deploy_vii.report_view import pathways

    return next((item.title for item in pathways() if item.id == pathway), pathway)


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:-1])]


def chart_row(lines: list[str], chart: str) -> tuple[dict[str, str], int] | None:
    """The last row of ``### Chart data: <chart>`` as {column: cell}, with its 1-based line."""
    try:
        start = lines.index(f"### Chart data: {chart}")
    except ValueError:
        return None
    table: list[int] = []
    for number in range(start + 1, len(lines)):
        if lines[number].startswith("|"):
            table.append(number)
        elif table or lines[number].startswith("#"):
            break
    if len(table) < 3:  # header, separator, at least one row
        return None
    header, last = cells(lines[table[0]]), table[-1]
    row = cells(lines[last])
    return (dict(zip(header, row, strict=False)), last + 1) if len(row) == len(header) else None


def context_values(folder: Path, issues: list[str]) -> dict[str, str]:
    """Ticker, sector, country, currency and period the run's ``context.json`` states, if any."""
    if not os.path.lexists(folder / "context.json"):
        return {}  # Not every run folder keeps the context form; its fields stay empty.
    try:
        record = json_object(read_inside(folder, "context.json"), "context.json")
    except Refused as error:
        issues.append(f"{folder.name}: context.json not used ({error})")
        return {}
    found: dict[str, str] = {}
    for section, key in (
        ("identity", "ticker"),
        ("identity", "sector"),
        ("identity", "country"),
        ("run", "reporting_currency"),
        ("run", "current_period"),
    ):
        part = record.get(section)
        value = part.get(key) if isinstance(part, dict) else None
        if isinstance(value, str) and value.strip():
            found[key] = value.strip()
    return found


def period_fields(context: dict[str, str]) -> tuple[str, str]:
    period = context.get("current_period", "")
    if not _PERIOD.match(period):
        return "", ""
    return period.upper(), _PERIOD_KINDS[period[0]]


def summary_fields(run: dict[str, Any]) -> tuple[str, list[str]]:
    """CP-2's bottom line, else the latest module's; with that module's main limitation."""
    modules = [m for m in run["modules"] if m["summary"] is not None]
    chosen = next((m for m in modules if m["id"] == "CP-2"), modules[-1] if modules else None)
    if chosen is None:
        return "", []
    summary = chosen["summary"]
    return summary["bottom_line"], [summary["limitation"]]


def run_files(folder: Path, name: str, issues: list[str]) -> list[dict[str, str]]:
    """The run's retained files in name order; links and hidden entries are not listed."""
    found: list[dict[str, str]] = []
    for base, directories, files in os.walk(folder):
        directories[:] = sorted(d for d in directories if not d.startswith("."))
        for entry in sorted(files):
            path = Path(base) / entry
            if entry.startswith(".") or path.is_symlink() or path.suffix.lower() not in LISTED:
                continue
            relative = path.relative_to(folder).as_posix()
            found.append({"name": relative, "href": file_url(f"runs/{name}/{relative}")})
    if len(found) > RUN_FILE_LIMIT:
        issues.append(f"{name}: run file limit ({RUN_FILE_LIMIT}) reached; files not listed")
        return []
    return found


def handoff_metrics(
    name: str, pin: dict[str, str], text: str, sources: dict[str, Any], issues: list[str]
) -> dict[str, dict[str, str]]:
    """Metrics quoted from the CP-1 chart tables' latest rows; a cell not supplied gives no key."""
    lines = text.replace("\r\n", "\n").split("\n")
    metrics: dict[str, dict[str, str]] = {}
    for chart, key, column in _METRICS:
        found = chart_row(lines, chart)
        if found is None:
            continue
        row, number = found
        value = row.get(column, "")
        if value.startswith(_NOT_SUPPLIED):
            continue
        unit, basis, period = (
            row.get(c, "") for c in ("Reporting unit", "Basis and limitation", "Period")
        )
        if not (_NUMBER.fullmatch(value) and unit and basis and period):
            issues.append(f"{name}: CP-1 {chart} {column!r} is not a quotable metric; left out")
            continue
        source = f"{name}.cp1-{chart.replace(' ', '-')}"
        quote_text = lines[number - 1]
        sources[source] = {
            **pin,
            "line": number,
            "quote": quote_text,
            "href": pinned_url(pin["path"], pin["sha256"]),
        }
        metrics[key] = {
            "value": value,
            "unit": unit,
            "period": period,
            "basis": basis,
            "source": source,
            "provenance": "cited",
        }
    return metrics


def delivery_fields(
    workspace: Path, run: dict[str, Any], sources: dict[str, Any], issues: list[str]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    """The run's verified delivery as one artifact, and the metrics its CP-1 handoff states."""
    name = run["id"]
    folder = workspace / "runs" / name
    try:
        relative, files = delivery_folder(folder, run["report"]["sha256"])
        view = json_object(read_inside(folder, f"{relative}/view.json"), "view.json")
        cp1 = next((m for m in run["modules"] if m["id"] == "CP-1"), None)
        text = ""
        if cp1 is not None:
            raw = read_pinned(folder, f"{relative}/CP-1.md", cp1["sha256"])
            text = raw.decode("utf-8", errors="replace")
    except (Refused, OSError) as error:
        issues.append(f"{name}: delivery not catalogued ({error})")
        return [], {}
    delivered = f"runs/{name}/{relative}"
    mode = view.get("mode")
    artifact = {
        "folder": delivered,
        "kind": "report",
        "label": relative.rsplit("/", 1)[-1],
        "state": mode if isinstance(mode, str) and mode else "candidate",
        "relationship": "direct",
        "available": True,
        "href": pinned_url(f"{delivered}/report.html", files["report.html"]),
    }
    metrics = {}
    if cp1 is not None:
        pin = {"path": f"{delivered}/CP-1.md", "sha256": cp1["sha256"]}
        metrics = handoff_metrics(name, pin, text, sources, issues)
    return [artifact], metrics


def run_record(
    workspace: Path, run: dict[str, Any], sources: dict[str, Any], issues: list[str]
) -> dict[str, Any]:
    name = run["id"]
    context = context_values(workspace / "runs" / name, issues)
    period, period_kind = period_fields(context)
    summary, gaps = summary_fields(run)
    title = pathway_title(run["pathway"])
    artifacts, metrics = delivery_fields(workspace, run, sources, issues)
    return {
        "id": name,
        "issuer": context.get("ticker") or run["issuer_id"].upper(),
        "name": run["issuer_name"],
        "title": title,
        "workflow": title,
        "sector": context.get("sector", ""),
        "country": context.get("country", ""),
        "currency": context.get("reporting_currency", ""),
        "date": run["as_of"],
        "period": period,
        "period_kind": period_kind,
        "summary": summary,
        "gaps": gaps,
        "metrics": metrics,
        "artifacts": artifacts,
        "files": run_files(workspace / "runs" / name, name, issues),
        "checklist": None,
    }


def catalogue(workspace: Path, library: Library) -> dict[str, Any]:
    """Every run ``library_index`` listed, in its order, as the JSON Credit OS reads."""
    sources: dict[str, Any] = {}
    issues: list[str] = []
    real = [run_record(workspace, run, sources, issues) for run in library.runs]
    return {"real": real, "sources": sources, "workspace": str(workspace), "issues": issues}
