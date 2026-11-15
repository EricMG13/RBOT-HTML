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
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

from deploy_workflow.owners.cpos import request_fingerprint
from deploy_workflow.owners.cpos_launch import METHOD_MARK, method_text

SOURCE_DIR = HERE / "synthetic-new-format"
DEFAULT_FOLDER = "synthetic-nbg-new-format-001"
SCOPE = "SYNTHETIC FIXTURE: hand-made to the 2026-11-11 handoff contract; not analysis."
MODULES = ("CP-0", "CP-1", "CP-1A", "CP-2", "CP-2D")  # engine registry order: CP-2D runs after CP-2
# `--with-cp3c-cp6` (owner, 2026-11-15: CP-3C and CP-6A are part of the full credit assessment):
# CP-3C after CP-2D, and CP-6 with its portfolio debate; CP-6's other producers are not in it.
EXTRA = ("CP-3C", "CP-6")
SETTLED = ("0.10", "0.20", "0.15", "0.30", "0.05", "0.25", "0.35")
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


def write_request(run_dir: Path, run: dict[str, Any], module: str, answer: bytes) -> dict[str, str]:
    """The instructions, request record and answer of one module, as CP-OS keeps them."""
    text = f"# {module} for {RUN['issuer_name']} (nbg), as of {RUN['as_of']}\n\n"
    text += f"SYNTHETIC FIXTURE: not a model request.\n\n{METHOD_MARK}{method_text(module)}\n"
    instructions = {
        "path": f"instructions/{module}.md",
        "sha256": put(run_dir / f"instructions/{module}.md", text.encode()),
    }
    inputs: dict[str, Any] = {
        "run": run,
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


def write_delivery(
    run_dir: Path, run: dict[str, Any], handoffs: dict[str, bytes], pins: dict[str, dict[str, str]]
) -> tuple[str, str]:
    """The delivery manifest and folder; returns the manifest hash and the delivery.json hash."""
    manifest = json.dumps({"run": run, "handoffs": pins}, indent=2).encode()
    manifest_sha = put(run_dir / f"delivery-{sha(manifest)}.json", manifest)
    files = {
        "view.json": json.dumps({"run": run}).encode(),
        **{f"{module}.md": raw for module, raw in handoffs.items()},
    }
    delivery_id = sha(json.dumps({n: sha(r) for n, r in sorted(files.items())}).encode())
    folder = run_dir / "deliveries" / delivery_id
    receipt = {"files": {name: put(folder / name, raw) for name, raw in files.items()}}
    receipt_sha = put(folder / "delivery.json", json.dumps(receipt).encode())
    return manifest_sha, receipt_sha


def write_calls(run_dir: Path, modules: tuple[str, ...]) -> None:
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
        for i, module in enumerate(modules)
    ]
    put(run_dir / "live/calls.jsonl", "".join(json.dumps(c) + "\n" for c in calls).encode())
    put(run_dir / "live/loop.json", json.dumps({"config": "synthetic-fixture"}).encode())


def build(workspace: Path, folder: str, *, extra: bool = False) -> Path:
    """Write the run folder; refuses a name that is not one plain folder or that already exists.
    ``extra`` adds the `EXTRA` modules' handoffs."""
    modules = (*MODULES, *EXTRA) if extra else MODULES
    run = {**RUN, "requested_modules": list(modules)}
    if not folder or folder != Path(folder).name or folder in {".", ".."}:
        raise SystemExit(f"--folder must be one plain folder name, not {folder!r}")
    run_dir = workspace / "runs" / folder
    if run_dir.exists():
        raise SystemExit(f"refusing to write into an existing folder: {run_dir}")
    # Read every handoff first, so a missing one leaves nothing written.
    handoffs = {m: (SOURCE_DIR / f"SYNTHETIC-{m}.md").read_bytes() for m in modules}
    instructions, pins = {}, {}
    for module in modules:
        written = write_request(run_dir, run, module, handoffs[module])
        instructions[module] = {"path": written["path"], "sha256": written["sha256"]}
        pins[module] = {"path": written["answer"], "sha256": written["answer_sha256"]}
    sources = write_sources(run_dir, folder)
    put(
        run_dir / "workflow.json",
        json.dumps({"run": run, "instructions": instructions, "sources": sources}).encode(),
    )
    manifest_sha, receipt_sha = write_delivery(run_dir, run, handoffs, pins)
    completion = {
        "kind": "cpos-markdown-delivery/1",
        "execution": "synthetic",
        "scope": SCOPE,
        "provider_cap_usd": "12",
        "modules": {m: pins[m]["path"] for m in modules},
        "module_execution": {m: "live-provider" for m in modules},
        "delivery_manifest_sha256": manifest_sha,
        "delivery_sha256": receipt_sha,
    }
    raw = json.dumps(completion, indent=2).encode()
    put(run_dir / f"completed-{sha(raw)}.json", raw)
    write_calls(run_dir, modules)
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workspace", required=True, type=Path, help="the workspace folder")
    parser.add_argument("--folder", default=DEFAULT_FOLDER, help="the run folder name")
    parser.add_argument(
        "--with-cp3c-cp6", action="store_true", help="add the CP-3C and CP-6 handoffs too"
    )
    args = parser.parse_args(argv)
    print(build(args.workspace, args.folder, extra=args.with_cp3c_cp6))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
