"""An earlier run's inputs, read from the run records and the run's own source folder.

The service is reachable from other machines: a run ID is looked up in the run records before any
path is built from it, and a linked source folder or ``context.json`` is never read.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from deploy_workflow.inbox import runs
from deploy_workflow.inbox.layout import Layout
from deploy_workflow.inbox.runs import Record
from deploy_workflow.run_start import submissions
from deploy_workflow.run_start.submissions import Refused

log = logging.getLogger(__name__)

_DATES = ("as_of", "cutoff", "current_period", "prior_period")


def source(layout: Layout, run_id: str) -> tuple[Record, Path | None]:
    """The run's record and its source folder, or ``None`` for the folder when it is not a real
    folder holding a regular ``context.json``. ``Refused("unknown run")`` when no record matches."""
    for record in runs.load_all(layout):
        if record.id == run_id:
            break
    else:
        raise Refused("unknown run")
    folder = layout.drops / record.id
    context = folder / "context.json"
    if folder.is_symlink() or not folder.is_dir():
        return record, None
    if context.is_symlink() or not context.is_file():
        return record, None
    return record, folder


def _read_context(folder: Path) -> dict[str, Any] | None:
    try:
        data = json.loads((folder / "context.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        # Not fail-open: the answer says there is no context, and the page then asks for one.
        log.warning("earlier run context unreadable at %s (%s)", folder, error)
        return None
    if not isinstance(data, dict):
        return None
    if not isinstance(data.get("run"), dict) or not isinstance(data.get("identity"), dict):
        return None
    for key in _DATES:
        data["run"][key] = ""
    return data


def _files(folder: Path) -> list[dict[str, Any]]:
    try:
        found = submissions.listing(folder)
    except Refused as error:
        log.warning("earlier run files not listed at %s (%s)", folder, error)
        return []
    return [{"name": name, "size": found[name]} for name in sorted(found)]


def inputs(layout: Layout, run_id: str) -> dict[str, Any]:
    """What a new run can start from: the earlier run's context (dates blank) and file list."""
    record, folder = source(layout, run_id)
    context = _read_context(folder) if folder else None
    return {
        "run": record.id,
        "issuer_id": record.issuer_id,
        "issuer_name": record.issuer_name,
        "pathway": record.pathway,
        "context": context,
        "files": _files(folder) if folder and context is not None else [],
        "level": record.level,
        "modules": list(record.modules),
        "max_turns": record.max_turns,
    }


def issuer(layout: Layout, issuer_id: str) -> dict[str, Any]:
    """Finished runs the issuer has, and the latest run by as-of date (ties: the greater ID)."""
    mine = [r for r in runs.load_all(layout) if r.issuer_id == issuer_id]
    if not mine:
        return {"runs": 0, "latest_as_of": "", "latest_run": "", "issuer_name": ""}
    latest = max(mine, key=lambda r: (r.as_of, r.id))
    return {
        "runs": sum(1 for r in mine if r.status == "finished"),
        "latest_as_of": latest.as_of,
        "latest_run": latest.id,
        "issuer_name": latest.issuer_name,
    }
