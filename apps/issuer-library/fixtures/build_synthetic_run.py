"""Build one SYNTHETIC completed run folder for the Issuer Library from the hand-made handoffs.

    python apps/issuer-library/fixtures/build_synthetic_run.py --workspace FOLDER [--folder NAME]

Writes ``FOLDER/runs/NAME`` (default ``synthetic-nbg-new-format-001``) from the ``SYNTHETIC-*.md``
files beside this script, byte for byte. The run is hand-made to the 2026-11-11 handoff contract:
it is not analysis and no model or provider was called. It has every file ``library_index`` checks
(completion record, delivery manifest and folder, requests, instructions carrying the current
method block, call records) so the library lists it. ``--workspace`` is required and an existing run
folder is never written into.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from deploy_workflow.owners.cpos import request_fingerprint
from deploy_workflow.owners.cpos_launch import METHOD_MARK, method_text

SOURCE_DIR = HERE / "synthetic-new-format"
DEFAULT_FOLDER = "synthetic-nbg-new-format-001"
SCOPE = "SYNTHETIC FIXTURE: hand-made to the 2026-11-11 handoff contract; not analysis."
MODULES = ("CP-0", "CP-1", "CP-1A", "CP-2D", "CP-2")  # CP-2D is upstream of CP-2
SETTLED = ("0.10", "0.20", "0.15", "0.05", "0.30")
SUPPLIED = (
    "NBG_2025-03-31_annual-report.pdf",
    "NBG_2024-12-31_Q4-results.pdf",
    "NBG_2025-02-14_facility-agreement.pdf",
)
RUN = {
    "schema_version": "run/2",
    "run_id": "nbg-2025-03-31-credit_snapshot",
    "issuer_id": "nbg",
    "issuer_name": "Northbridge Synthetic Group",
    "as_of": "2025-03-31",
    "method_version": "deploy-v-r14",
    "case_kind": "public",
    "pathway": "credit_snapshot",
    "requested_modules": list(MODULES),
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def put(path: Path, raw: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return sha(raw)


def write_request(run_dir: Path, module: str, answer: bytes) -> dict[str, str]:
    """The instructions, request record and answer of one module, as CP-OS keeps them."""
    text = f"# {module} for {RUN['issuer_name']} (nbg), as of {RUN['as_of']}\n\n"
    text += f"SYNTHETIC FIXTURE: not a model request.\n\n{METHOD_MARK}{method_text(module)}\n"
    instructions = {
        "path": f"instructions/{module}.md",
        "sha256": put(run_dir / f"instructions/{module}.md", text.encode()),
    }
    inputs: dict[str, Any] = {
        "run": RUN,
        "module_id": module,
        "instructions": text,
        "sources": {},
        "handoffs": {},
        "retained_response_sha256": None,
    }
    folder_sha = request_fingerprint(inputs)
    request = {**inputs, "attempt": 1, "feedback": []}
    raw_request = json.dumps(request, sort_keys=True, indent=2).encode()
    put(run_dir / f"requests/{module}/{folder_sha}/1.request.json", raw_request)
    path = f"requests/{module}/{folder_sha}/1.response.md"
    return {**instructions, "answer": path, "answer_sha256": put(run_dir / path, answer)}


def write_sources(run_dir: Path, folder: str) -> dict[str, dict[str, str]]:
    """Placeholder text for each supplied file, clearly marked; no real document is reproduced."""
    declared = {}
    for name in SUPPLIED:
        note = f"SYNTHETIC FIXTURE placeholder for {name}; no real document.\n".encode()
        digest = put(run_dir / "sources" / f"{name}.txt", note)
        declared[name] = {"path": f"runs/{folder}/sources/{name}.txt", "sha256": digest}
    return declared


def report_html(handoffs: dict[str, bytes]) -> bytes:
    """The placeholder delivered report the library still requires; it carries no analysis."""
    names = ", ".join(sorted(handoffs))
    return (
        "<!doctype html><title>SYNTHETIC FIXTURE report</title><body><main>"
        f"<h1>SYNTHETIC FIXTURE</h1><p>Placeholder; hand-made handoffs only: {names}.</p>"
        "</main></body>"
    ).encode()


def write_delivery(
    run_dir: Path, handoffs: dict[str, bytes], pins: dict[str, dict[str, str]]
) -> tuple[str, str]:
    """The delivery manifest and folder; returns the manifest and report hashes."""
    manifest = json.dumps({"run": RUN, "handoffs": pins}, indent=2).encode()
    manifest_sha = put(run_dir / f"delivery-{sha(manifest)}.json", manifest)
    report = report_html(handoffs)
    files = {
        "report.html": report,
        "view.json": json.dumps({"run": RUN}).encode(),
        **{f"{module}.md": raw for module, raw in handoffs.items()},
    }
    delivery_id = sha(json.dumps({n: sha(r) for n, r in sorted(files.items())}).encode())
    folder = run_dir / "deliveries" / delivery_id
    receipt = {"files": {name: put(folder / name, raw) for name, raw in files.items()}}
    put(folder / "delivery.json", json.dumps(receipt).encode())
    return manifest_sha, sha(report)


def write_calls(run_dir: Path) -> None:
    calls = [
        {
            "module_id": module,
            "attempt": 1,
            "requested_model": "synthetic",
            "reported_model": "synthetic",
            "requested_effort": "none",
            "started_at": f"2026-11-10T10:0{i}:00Z",
            "settled_usd": SETTLED[i],
        }
        for i, module in enumerate(MODULES)
    ]
    put(run_dir / "live/calls.jsonl", "".join(json.dumps(c) + "\n" for c in calls).encode())
    put(run_dir / "live/loop.json", json.dumps({"config": "synthetic-fixture"}).encode())


def build(workspace: Path, folder: str) -> Path:
    """Write the run folder; refuses a name that is not one plain folder or that already exists."""
    if not folder or folder != Path(folder).name or folder in {".", ".."}:
        raise SystemExit(f"--folder must be one plain folder name, not {folder!r}")
    run_dir = workspace / "runs" / folder
    if run_dir.exists():
        raise SystemExit(f"refusing to write into an existing folder: {run_dir}")
    # Read every handoff first, so a missing one leaves nothing written.
    handoffs = {m: (SOURCE_DIR / f"SYNTHETIC-{m}.md").read_bytes() for m in MODULES}
    instructions, pins = {}, {}
    for module in MODULES:
        written = write_request(run_dir, module, handoffs[module])
        instructions[module] = {"path": written["path"], "sha256": written["sha256"]}
        pins[module] = {"path": written["answer"], "sha256": written["answer_sha256"]}
    sources = write_sources(run_dir, folder)
    put(
        run_dir / "workflow.json",
        json.dumps({"run": RUN, "instructions": instructions, "sources": sources}).encode(),
    )
    manifest_sha, report_sha = write_delivery(run_dir, handoffs, pins)
    completion = {
        "kind": "cpos-markdown-delivery/1",
        "execution": "synthetic",
        "scope": SCOPE,
        "provider_cap_usd": "12",
        "modules": {m: pins[m]["path"] for m in MODULES},
        "module_execution": {m: "live-provider" for m in MODULES},
        "delivery_manifest_sha256": manifest_sha,
        "report_sha256": report_sha,
    }
    raw = json.dumps(completion, indent=2).encode()
    put(run_dir / f"completed-{sha(raw)}.json", raw)
    write_calls(run_dir)
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workspace", required=True, type=Path, help="the workspace folder")
    parser.add_argument("--folder", default=DEFAULT_FOLDER, help="the run folder name")
    args = parser.parse_args(argv)
    print(build(args.workspace, args.folder))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
