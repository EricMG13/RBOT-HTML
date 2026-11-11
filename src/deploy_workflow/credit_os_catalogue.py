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
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from deploy_workflow.context import CONTEXT_SOURCE_ID, ContextRefused, load_context
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
_FISCAL_YEAR = re.compile(r"FY(\d{4})")
_DATED_YEAR = re.compile(r"FY(\d{4}) / (\d{4}-\d{2}-\d{2})")
_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
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


def period_order(cell: str) -> tuple[int, ...] | None:
    """Sort key of a Period cell: ``FY2024``, ``2024-09-30`` or ``FY2024 / 2024-09-30`` (ordered
    by its date); None for any other text, an impossible date, or a year that disagrees."""
    year = _FISCAL_YEAR.fullmatch(cell)
    if year:
        return (1, int(year[1]))
    both = _DATED_YEAR.fullmatch(cell)
    date = _ISO_DATE.fullmatch(both[2] if both else cell)
    if date is None or (both and both[1] != date[1]):
        return None
    try:
        day = datetime(int(date[1]), int(date[2]), int(date[3]))
    except ValueError:
        return None
    return (2, day.year, day.month, day.day)


def chart_row(lines: list[str], chart: str) -> tuple[dict[str, str], int] | None:
    """The latest-period row of ``### Chart data: <chart>`` as {column: cell}, with its 1-based
    line. The latest is chosen by the Period value, whatever the row order. None when the table
    is absent; ValueError when its periods cannot be ordered (never a guess)."""
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
    header = cells(lines[table[0]])
    ranked: list[tuple[tuple[int, ...], dict[str, str], int]] = []
    for number in table[2:]:
        values = cells(lines[number])
        key = period_order(dict(zip(header, values, strict=False)).get("Period", ""))
        if len(values) != len(header) or key is None:
            raise ValueError("a row has no period that can be ordered")
        ranked.append((key, dict(zip(header, values, strict=True)), number + 1))
    keys = [key for key, _, _ in ranked]
    if len({key[0] for key in keys}) != 1 or len(set(keys)) != len(keys):
        raise ValueError("the periods mix forms or repeat")
    _, row, number = max(ranked, key=lambda item: item[0])
    return row, number


def context_values(folder: Path, issues: list[str]) -> dict[str, str]:
    """Ticker, sector, country, currency and period of the context CP-OS pinned for the run.

    ``workflow.json`` names the context by hash (``sources["context"]``); its bytes are under
    ``inputs/<sha256>``. Bytes that fail the hash or the context rules leave every field empty
    and are recorded as an issue.
    """
    try:
        workflow = json_object(read_inside(folder, "workflow.json"), "workflow.json")
        sources = workflow.get("sources")
        pin = sources.get(CONTEXT_SOURCE_ID) if isinstance(sources, dict) else None
        if not isinstance(pin, dict):
            return {}  # This run was launched without a context form; its fields stay empty.
        digest = pin.get("sha256")
        raw = read_pinned(folder, f"inputs/{digest}", digest)
        context = load_context(raw)
    except (Refused, ContextRefused) as error:
        issues.append(f"{folder.name}: context not used ({error})")
        return {}
    found = {
        "ticker": context.identity.ticker,
        "sector": context.identity.sector,
        "country": context.identity.country,
        "reporting_currency": context.run.reporting_currency,
        "current_period": context.run.current_period,
    }
    return {key: value.strip() for key, value in found.items() if value.strip()}


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
    unordered: set[str] = set()
    for chart, key, column in _METRICS:
        try:
            found = chart_row(lines, chart)
        except ValueError as error:
            if chart not in unordered:
                unordered.add(chart)
                issues.append(f"{name}: CP-1 {chart} table has no metric ({error})")
            continue
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


# The files `credit_os/store.py` reads for a model (its CASHFLOW_FILES).
MODEL_FILES = ("forecast_exact.json", "calculation.json", "annual.md", "quarter.md")


def forecast_published(folder: Path, relative: str, files: Mapping[str, str]) -> bool:
    """Whether the verified delivery's receipt says it carries the Python-computed forecast."""
    receipt = json_object(read_inside(folder, f"{relative}/delivery.json"), "delivery.json")
    return receipt.get("cp_forecast_published") is True and set(MODEL_FILES) <= set(files)


NO_REPORT_PAGE = "this delivery has no report page; the library shows the run itself"


def model_artifact(
    report: dict[str, Any], delivered: str, files: Mapping[str, str]
) -> dict[str, Any]:
    """The Forecast artifact of a delivery, pinned to a file the delivery publishes.

    An earlier-format delivery shows it through its report page. A newer one has no report page, so
    the reader-facing published file (``model.html``, else ``annual.md``) is pinned instead; with
    neither, the artifact is listed as unavailable with the reason."""
    model = {**report, "kind": "model", "label": "Forecast"}
    if "report.html" in files:
        return {**model, "issue": "", "available": True}
    name = next((n for n in ("model.html", "annual.md") if n in files), None)
    if name is None:
        return {**model, "issue": "the delivery publishes no forecast file", "available": False}
    return {
        **model,
        "issue": "",
        "available": True,
        "href": pinned_url(f"{delivered}/{name}", files[name]),
    }


def delivery_fields(
    workspace: Path,
    run: dict[str, Any],
    sources: dict[str, Any],
    issues: list[str],
    verified: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    """The run's verified delivery as one artifact, and the metrics its CP-1 handoff states.

    ``verified`` is the delivery this build already verified (``Library.deliveries``), used as is
    and never changed; without it the delivery is verified here."""
    name = run["id"]
    folder = workspace / "runs" / name
    try:
        if verified is not None:
            relative, files, view = verified["folder"], verified["files"], verified["view"]
        else:
            report = run["report"]
            relative, files = (
                delivery_folder(folder, report["sha256"])
                if report is not None
                else delivery_folder(folder, run["delivery_sha256"], receipt_hash=True)
            )
            view = json_object(read_inside(folder, f"{relative}/view.json"), "view.json")
        published = forecast_published(folder, relative, files)
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
        "issue": "" if "report.html" in files else NO_REPORT_PAGE,
        "available": "report.html" in files,
        "href": pinned_url(f"{delivered}/report.html", files["report.html"])
        if "report.html" in files
        else "",
    }
    metrics = {}
    if cp1 is not None:
        pin = {"path": f"{delivered}/CP-1.md", "sha256": cp1["sha256"]}
        metrics = handoff_metrics(name, pin, text, sources, issues)
    artifacts = [artifact]
    if published:
        artifacts.append(model_artifact(artifact, delivered, files))
    return artifacts, metrics


def run_record(
    workspace: Path,
    run: dict[str, Any],
    sources: dict[str, Any],
    issues: list[str],
    verified: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    name = run["id"]
    context = context_values(workspace / "runs" / name, issues)
    period, period_kind = period_fields(context)
    summary, gaps = summary_fields(run)
    title = pathway_title(run["pathway"])
    artifacts, metrics = delivery_fields(workspace, run, sources, issues, verified)
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
        "completion": None,
        "checkpoints": None,
        "ratings": [],
        "classification": "",
        "classification_source": "",
        "private_side": False,
        "private_side_source": "",
        "facilities": [],
        "identity_source": "",
        "sector_source": "",
        "handoff": "",
        "handoff_href": "",
        "checklist": None,
    }


def catalogue(workspace: Path, library: Library) -> dict[str, Any]:
    """Every run ``library_index`` listed, in its order, as the JSON Credit OS reads."""
    sources: dict[str, Any] = {}
    issues: list[str] = []
    real = [
        run_record(workspace, run, sources, issues, library.deliveries.get(run["id"]))
        for run in library.runs
    ]
    return {
        "real": real,
        "illustrative": [],
        "sources": sources,
        "built_at": datetime.now(UTC).strftime("%d %b %Y, %H:%M:%S UTC"),
        "issues": issues,
        "workspace": str(workspace),
        "live": False,
        "policy_locked": False,
    }
