"""The Evidence page of a run, as data (`run_evidence`).

Part of the library's store (`credit_os.store`, which re-exports every name here).
"""

import json
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple
from urllib.parse import quote

from credit_os.source import (
    HANDOFF_NAME,
    describe,
    regular_chunks,
    sha256,
)

SHA_TEXT = re.compile(r"[0-9a-f]{64}")
EXTENSION_WORDS = re.compile(r"((?:\.[A-Za-z]+)+)$")
CALL_FIELDS = (
    ("module", "module_id"),
    ("attempt", "attempt"),
    ("started", "started_at"),
    ("http_status", "http_status"),
    ("error_class", "error_class"),
    ("settled_usd", "settled_usd"),
)


def stored_text(value: Any) -> str | None:
    """A stored string as it is; anything else is missing, never a made-up value."""
    return value if isinstance(value, str) else None


def run_json(path: Path, issues: list[str], what: str) -> Any:
    """A run file's JSON, or None with an issue naming why not (a documented fail-open: the
    Evidence page then lacks that part; the failure is in Workspace issues)."""
    try:
        return json.loads(b"".join(regular_chunks(path, follow=False)).decode("utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        issues.append(f"{what} could not be read ({describe(error)})")
        return None


def file_type(name: str) -> str | None:
    """The file's trailing alphabetic extension words as written (`pdf`, `htm.jsonl`)."""
    found = EXTENSION_WORDS.search(name)
    return found[1][1:] if found else None


def sources_section_text(sections: list[dict[str, Any]]) -> str:
    """Every cell and paragraph under the handoff's `## Sources` heading (its subsections too)."""
    parts: list[str] = []
    inside = False
    for section in sections:
        if section["level"] <= 2:
            inside = section["level"] == 2 and section["heading"].strip() == "Sources"
        if not inside:
            continue
        for block in section["blocks"]:
            if block["type"] == "text":
                parts.append(block["text"])
            elif block["type"] == "table":
                parts.extend(block["headers"])
                parts.extend(cell for row in block["rows"] for cell in row["cells"])
    return "\n".join(parts)


def names_file(sources_text: str, name: str) -> bool:
    """Whether the Sources text names the file exactly: the whole name, with only the start or end
    of the text, white space, `|` or `,` on either side. `report.pdf` is not named by
    `annual-report.pdf`."""
    return re.search(rf"(?<![^\s|,]){re.escape(name)}(?![^\s|,])", sources_text) is not None


def has_sources_section(sections: list[dict[str, Any]]) -> bool:
    """Whether the handoff has a `## Sources` heading at all (even an empty one)."""
    return any(s["level"] == 2 and s["heading"].strip() == "Sources" for s in sections)


def document_dates(sections: list[dict[str, Any]]) -> dict[str, str]:
    """The Document date a handoff's table records for a file: in a table with `Source` and
    `Document date` columns, the date cell of the row whose Source cell is exactly the file name,
    copied as written. A blank cell, or one reading "not stated" (any case, surrounding space
    ignored), records nothing, so a later module that saw the date supplies it; no date is parsed
    or read from a file name."""
    found: dict[str, str] = {}
    for section in sections:
        for block in section["blocks"]:
            if block["type"] != "table":
                continue
            heads = [h.strip() for h in block["headers"]]
            if "Source" not in heads or "Document date" not in heads:
                continue
            name_at, date_at = heads.index("Source"), heads.index("Document date")
            for row in block["rows"]:
                date = row["cells"][date_at].strip()
                if date and date.casefold() != "not stated":
                    found.setdefault(row["cells"][name_at].strip(), date)
    return found


def run_calls(run_dir: Path, folder: str, issues: list[str]) -> list[dict[str, Any]]:
    """live/calls.jsonl as recorded: one row per call with the fields as stored. A file that is not
    UTF-8 text lists no call and is named in the issues (documented fail-open: no byte is replaced
    with a guess)."""
    try:
        raw = b"".join(regular_chunks(run_dir / "live" / "calls.jsonl", follow=False))
    except FileNotFoundError:
        return []
    except OSError as error:
        issues.append(f"{folder}: live/calls.jsonl could not be read ({describe(error)})")
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        bad = raw[: error.start].count(b"\n") + 1
        issues.append(
            f"{folder}: live/calls.jsonl is not UTF-8 text (line {bad}); no call is listed"
        )
        return []
    calls: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            call = json.loads(line)
        except ValueError:
            call = None
        if not isinstance(call, dict):
            issues.append(f"{folder}: live/calls.jsonl line {number} is not a call record")
            continue
        calls.append({key: call.get(field) for key, field in CALL_FIELDS})
    return calls


def run_hashes(run_dir: Path, workflow: dict[str, Any], issues: list[str]) -> list[dict[str, Any]]:
    """The hashes a run records: its supplied files and instructions (workflow.json), then its
    delivery manifest and completion record, hashed from the files themselves."""
    rows: list[dict[str, Any]] = []
    for part in ("sources", "instructions"):
        entries = workflow.get(part)
        for name, entry in (entries if isinstance(entries, dict) else {}).items():
            entry = entry if isinstance(entry, dict) else {}
            label = name if part == "sources" else str(entry.get("path") or name)
            rows.append({"name": label, "sha256": stored_text(entry.get("sha256"))})
    for pattern in ("delivery-*.json", "completed-*.json"):
        for path in sorted(run_dir.glob(pattern)):
            try:
                rows.append({"name": path.name, "sha256": sha256(path)})
            except OSError as error:
                issues.append(
                    f"{run_dir.name}: {path.name} could not be hashed ({describe(error)})"
                )
                rows.append({"name": path.name, "sha256": None})
    return rows


def instruction_rows(
    workflow: dict[str, Any], folder: str, issues: list[str]
) -> list[dict[str, Any]]:
    """The instructions each module was sent, as the run's workflow.json records them. A usable
    row links to the copy update_library writes under the library folder (so it opens when the
    library is served too)."""
    entries = workflow.get("instructions")
    rows: list[dict[str, Any]] = []
    for module, entry in (entries if isinstance(entries, dict) else {}).items():
        entry = entry if isinstance(entry, dict) else {}
        path, digest = entry.get("path"), stored_text(entry.get("sha256"))
        parts = PurePosixPath(path).parts if isinstance(path, str) else ()
        safe = (
            isinstance(path, str)
            and bool(parts)
            and not (path.startswith("/") or ".." in parts or "\\" in path or ":" in path)
        )
        usable = safe and digest is not None and SHA_TEXT.fullmatch(digest) is not None
        named = isinstance(module, str) and HANDOFF_NAME.fullmatch(module) is not None
        if not named:
            issues.append(f"{folder}: instructions key {module!r} is not a module code; no link")
        elif not usable:
            issues.append(f"{folder}: instructions for {module} have no usable path or hash")
        usable = usable and named
        rows.append(
            {
                "module": module,
                "href": f"downloads/{quote(folder)}/instructions/{quote(module)}.md"
                if usable
                else None,
                "sha256": digest,
            }
        )
    return rows


def run_downloads(
    run: dict[str, Any], key: str, models: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """The Model and calculation files of the models this run's Forecast lists (the rule of
    views.js runModels), each as a label and a download link."""
    rows: list[dict[str, Any]] = []
    for model in sorted(models, key=lambda m: m["id"]):
        holds = model["issuerKey"] == run["issuerKey"] and (
            (model["runId"] is not None and model["runId"] == run["folder"])
            or model["runFolder"] == run["folder"]
            or any(source["run"] == key for source in model["sources"])
        )
        if not holds:
            continue
        rows.append({"label": f"Model {model['id']}", "href": model["download"]})
        rows.extend(
            {"label": f"{model['id']}: {f['name']}", "href": f["href"]}
            for f in model["files"]
            if f["name"] in ("calculation.json", "forecast_exact.json")
        )
    return rows


# A write's script-check record sits beside its `<attempt>.review.json` (the writer's own suffix is
# deploy_workflow.method_scripts.RECORD_SUFFIX).
CHECK_STATUS_ORDER = ("agreed", "disagreed", "contradicted", "missing", "noted", "not checked")
CHECK_TEXT_FIELDS = ("figure", "register", "row", "status", "reason", "script", "stated", "unit")


def check_outcome(entry: Any) -> dict[str, Any] | None:
    """One outcome as the record stores it (text exact, numbers as written, a missing field None);
    an entry that is not an object with a text status is not an outcome."""
    if not isinstance(entry, dict) or not isinstance(entry.get("status"), str):
        return None
    row: dict[str, Any] = {name: stored_text(entry.get(name)) for name in CHECK_TEXT_FIELDS}
    for name in ("recomputed", "tolerance"):
        value = entry.get(name)
        row[name] = (
            value if isinstance(value, (int, float)) and not isinstance(value, bool) else None
        )
    row["recomputedLabel"] = stored_text(entry.get("recomputed_label"))
    return row


def check_record(path: Path, folder: str, issues: list[str]) -> dict[str, Any] | None:
    """A write's script-check record as data, or None (with an issue when the file is damaged: a
    documented fail-open, the Evidence page then lacks that module's section)."""
    name = f"{folder}: {path.relative_to(path.parents[3]).as_posix()}"
    found = run_json(path, issues, name)
    if found is None:
        return None
    outcomes = (
        [check_outcome(entry) for entry in found.get("checks", [])]
        if isinstance(found, dict) and isinstance(found.get("checks"), list)
        else None
    )
    if outcomes is None or None in outcomes:
        issues.append(f"{name} is not a script-check record; nothing is shown from it")
        return None
    scripts = found.get("scripts")
    scripts = scripts if isinstance(scripts, dict) else {}
    seen = Counter(o["status"] for o in outcomes if o)
    order = [*CHECK_STATUS_ORDER, *sorted(set(seen) - set(CHECK_STATUS_ORDER))]
    return {
        "response": stored_text(found.get("response_sha256")),
        "counts": [{"status": status, "n": seen[status]} for status in order if seen[status]],
        "scripts": [
            {"name": script, "sha256": stored_text(digest)} for script, digest in scripts.items()
        ],
        "outcomes": outcomes,
    }


CHECK_FILE = re.compile(r"(\d+)\.method-checks(?:-[0-9a-f]{64})?\.json")


def check_files(folder: Path) -> list[tuple[int, str, Path]]:
    """Each attempt's record file as (attempt, request folder name, path). The writer keeps a
    recheck that differs as `<n>.method-checks-<sha>.json` beside `<n>.method-checks.json`, and the
    recheck is the one acted on (cpos._retain_review): of an attempt's files the newest is taken."""
    newest: dict[tuple[int, str], Path] = {}
    for path in sorted(folder.glob("*/*.json")):
        named = CHECK_FILE.fullmatch(path.name)
        if not named or path.parent.is_symlink() or path.is_symlink():
            continue
        key = (int(named[1]), path.parent.name)
        if key not in newest or path.stat().st_mtime_ns >= newest[key].stat().st_mtime_ns:
            newest[key] = path
    return [(attempt, name, path) for (attempt, name), path in sorted(newest.items())]


def run_script_checks(
    run_dir: Path, run: dict[str, Any], outputs: dict[str, Any], issues: list[str]
) -> list[dict[str, Any]]:
    """Each module's script-check record of its accepted write, in the run's module order: the
    last attempt's record among those whose response is the delivered handoff. A module whose
    records match none (a rejected attempt's record is never shown for the accepted one) shows
    nothing and is named in the issues; a module with no record, and a run with none, give
    nothing."""
    found: list[dict[str, Any]] = []
    for module, entry in run["modules"].items():
        records = [
            (attempt, record)
            for attempt, _, path in check_files(run_dir / "requests" / module)
            if (record := check_record(path, run["folder"], issues))
        ]
        delivered = {outputs[name]["sha256"] for name in entry["outputs"] if name in outputs}
        accepted = [r for r in records if r[1]["response"] in delivered]
        if records and not accepted:
            issues.append(
                f"{run['folder']}: {module} has script-check records but none is of the delivered"
                " handoff; none is shown"
            )
        if accepted:
            attempt, record = accepted[-1]
            found.append({"module": module, "attempt": attempt} | record)
    return found


class EvidenceReads(NamedTuple):
    """What the store holds when Evidence is built: the workspace root, the outputs, the parsed
    handoffs by hash and the models."""

    root: Path
    outputs: dict[str, Any]
    sections: dict[str, list[dict[str, Any]]]
    models: list[dict[str, Any]]


def run_evidence(
    key: str, run: dict[str, Any], held: EvidenceReads, issues: list[str]
) -> dict[str, Any]:
    """The run's Evidence page, as data: supplied files and who read them, the delivered
    handoffs, the downloads and the run record. Every value is as stored; one the run does not
    record is None."""
    folder = run["folder"]
    run_dir = held.root / "runs" / folder
    workflow = run_json(run_dir / "workflow.json", issues, f"{folder}: workflow.json")
    workflow = workflow if isinstance(workflow, dict) else {}
    handoffs = []
    read_by: dict[str, list[str]] = {}
    no_sources: list[str] = []
    dates: dict[str, str] = {}
    supplied = workflow.get("sources")
    supplied = supplied if isinstance(supplied, dict) else {}
    # The earlier run's handoffs, pinned for CP-8 alone (owner, 2026-11-11), are not issuer files.
    names = [name for name in supplied if name != "context" and not name.startswith("prior/")]
    for module, entry in run["modules"].items():
        output = held.outputs.get(entry["default"] or "")
        if output is None:
            continue
        handoffs.append(
            {
                "module": module,
                "name": f"{module}.md",
                "href": f"downloads/{quote(folder)}/{quote(module)}.md",
            }
        )
        parsed = held.sections[output["sha256"]]
        for name, date in document_dates(parsed).items():
            dates.setdefault(name, date)
        if not has_sources_section(parsed):
            no_sources.append(module)
        text = sources_section_text(parsed)
        for name in names:
            if names_file(text, name):
                read_by.setdefault(name, []).append(module)
    rows = [
        {
            "name": name,
            "sha256": stored_text(supplied[name].get("sha256"))
            if isinstance(supplied[name], dict)
            else None,
            "type": file_type(name),
            "documentDate": dates.get(name),
            "readBy": read_by.get(name, []),
        }
        for name in names
    ]
    cap = workflow.get("provider_cap_usd")
    # No delivered handoff has a Sources section: the run recorded nothing about use, so an
    # unnamed file is "use not recorded", not "not used" (missing is not zero).
    nothing_recorded = len(no_sources) == len(handoffs)
    unnamed = [row for row in rows if not row["readBy"]]
    return {
        "sources": [row for row in rows if row["readBy"]],
        "unused": [] if nothing_recorded else unnamed,
        "unrecorded": unnamed if nothing_recorded else [],
        "noSourcesModules": no_sources,
        "handoffs": handoffs,
        "zip": f"downloads/{quote(folder)}/handoffs.zip" if handoffs else None,
        "downloads": run_downloads(run, key, held.models),
        "scriptChecks": run_script_checks(run_dir, run, held.outputs, issues),
        "record": {
            "hashes": run_hashes(run_dir, workflow, issues),
            "instructions": instruction_rows(workflow, folder, issues),
            "calls": run_calls(run_dir, folder, issues),
            "cap": cap if isinstance(cap, (str, int, float)) else None,
        },
    }
