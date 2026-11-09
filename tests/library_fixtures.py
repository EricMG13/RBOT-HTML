"""Hand-built CP-OS run folders for the Issuer Library tests. Synthetic: they mirror the files
CP-OS writes (workflow.json, instructions, handoffs, delivery manifest, delivery folder, completion
record, call records) without running CP-OS, so each test can damage exactly one of them."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

METHOD = {
    "CP-0": "=== methods/cp0.md sha256 {h} ===\n# CP-0 method\nRead the sources.",
    "CP-1": "=== prompts/CP-1.md sha256 {h} ===\n# CP-1 method\nBuild the foundation.",
}


def method_block(module: str, version: str = "") -> str:
    body = METHOD[module].split("\n", 1)[1] + version
    heading = METHOD[module].split("\n", 1)[0].format(h=sha(body.encode()))
    return f"{heading}\n{body}"


def method(version: str = ""):
    """A stand-in for the launcher's current method: (text, headings) per module."""

    def text(module):
        return method_block(module, version) if module in METHOD else None

    def headings(module):
        block = method_block(module, version)
        return [(block.split(" ")[1], block.split("\n", 1)[0])]

    return text, headings


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def put(path: Path, raw: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return sha(raw)


HANDOFF = """# {module} handoff

## Request
{name}, as of {as_of}.

## Findings

### Reader summary

| Bottom line | Confidence | Main limitation |
| --- | --- | --- |
| {bottom} | Medium | Synthetic fixture only. |

| Finding | Creditor impact | Confidence |
| --- | --- | --- |
| One observed item. | None assessed. | Low |

## Sources
- fixture
"""


@dataclass(frozen=True)
class RunSpec:
    issuer_id: str = "nbg"
    issuer_name: str = "Northbridge Synthetic Group"
    as_of: str = "2025-03-31"
    modules: tuple[str, ...] = ("CP-0", "CP-1")
    execution: str = "live-provider"
    version: str = ""
    settled: tuple[str | None, ...] = ("0.10", "0.20")
    view_issuer: str | None = None
    sent_extra: str = ""  # Text sent after the method block, such as a section since dropped.


def make_run(workspace: Path, folder: str, **changes) -> Path:
    """One completed run folder, consistent in every hash unless a test changes it after."""
    spec = RunSpec(**changes)
    issuer_id, issuer_name, as_of, modules = (
        spec.issuer_id,
        spec.issuer_name,
        spec.as_of,
        spec.modules,
    )
    run_dir = workspace / "runs" / folder
    run = {
        "schema_version": "run/2",
        "run_id": f"{issuer_id}-{as_of}-credit_snapshot",
        "issuer_id": issuer_id,
        "issuer_name": issuer_name,
        "as_of": as_of,
        "method_version": "deploy-v-r14",
        "case_kind": "public",
        "pathway": "credit_snapshot",
        "requested_modules": list(modules),
    }
    instructions, handoffs, selected = {}, {}, {}
    for module in modules:
        text = f"# {module} for {issuer_name}\n\nSelected method, verbatim:\n\n"
        text += method_block(module, spec.version) + spec.sent_extra + "\n"
        instructions[module] = {
            "path": f"instructions/{module}.md",
            "sha256": put(run_dir / f"instructions/{module}.md", text.encode()),
        }
        answer = HANDOFF.format(
            module=module, name=issuer_name, as_of=as_of, bottom=f"{module} bottom line."
        )
        # As CP-OS keeps it: the folder is named by the sha256 of the request's inputs.
        inputs = {
            "run": run,
            "module_id": module,
            "instructions": text,
            "sources": {},
            "handoffs": {},
            "retained_response_sha256": None,
        }
        folder_sha = sha(json.dumps(inputs, sort_keys=True).encode())
        request = {**inputs, "attempt": 1, "feedback": []}
        raw_request = json.dumps(request, sort_keys=True, indent=2).encode()
        put(run_dir / f"requests/{module}/{folder_sha}/1.request.json", raw_request)
        path = f"requests/{module}/{folder_sha}/1.response.md"
        handoffs[module] = {"path": path, "sha256": put(run_dir / path, answer.encode())}
        selected[module] = path
    put(run_dir / "workflow.json", json.dumps({"run": run, "instructions": instructions}).encode())
    manifest = json.dumps({"run": run, "handoffs": handoffs}, indent=2).encode()
    manifest_sha = sha(manifest)
    put(run_dir / f"delivery-{manifest_sha}.json", manifest)
    view_run = dict(run, issuer_id=spec.view_issuer or issuer_id)
    report = f"<!doctype html><title>{issuer_name} report</title><p>Report</p>".encode()
    files = {
        "report.html": report,
        "view.json": json.dumps({"run": view_run}).encode(),
        **{f"{m}.md": (run_dir / handoffs[m]["path"]).read_bytes() for m in modules},
    }
    delivery_id = sha(json.dumps({n: sha(r) for n, r in sorted(files.items())}).encode())
    delivered = run_dir / "deliveries" / delivery_id
    receipt = {"files": {name: put(delivered / name, raw) for name, raw in files.items()}}
    put(delivered / "delivery.json", json.dumps(receipt).encode())
    completion = {
        "kind": "cpos-markdown-delivery/1",
        "execution": "live-provider",
        "scope": "Synthetic fixture run; not analytical review.",
        "provider_cap_usd": "12",
        "modules": selected,
        "module_execution": {m: spec.execution for m in modules},
        "delivery_manifest_sha256": manifest_sha,
        "report_sha256": sha(report),
    }
    raw = json.dumps(completion, indent=2).encode()
    put(run_dir / f"completed-{sha(raw)}.json", raw)
    calls = [
        {
            "module_id": modules[i % len(modules)],
            "requested_model": "gpt-6.1-sol",
            "reported_model": "gpt-6.1-sol",
            "requested_effort": "medium",
            "started_at": f"2026-11-0{i + 1}T10:00:00Z",
            "settled_usd": amount,
        }
        for i, amount in enumerate(spec.settled)
    ]
    put(run_dir / "live/calls.jsonl", "".join(json.dumps(c) + "\n" for c in calls).encode())
    put(run_dir / "live/loop.json", json.dumps({"config": "sol-medium"}).encode())
    return run_dir


def rewrite_manifest(run_dir: Path, change) -> None:
    """Replace the delivery manifest with a changed one and point the completion record at it."""
    (old,) = run_dir.glob("delivery-*.json")
    manifest = json.loads(old.read_text())
    change(manifest)
    old.unlink()
    raw = json.dumps(manifest, indent=2).encode()
    new_sha = put(run_dir / f"delivery-{sha(raw)}.json", raw)
    rewrite_completion(run_dir, lambda record: record.update(delivery_manifest_sha256=new_sha))


def rewrite_completion(run_dir: Path, change) -> None:
    """Replace the completion record with a changed one, named by its new hash."""
    (old,) = run_dir.glob("completed-*.json")
    record = json.loads(old.read_text())
    change(record)
    old.unlink()
    raw = json.dumps(record, indent=2).encode()
    put(run_dir / f"completed-{sha(raw)}.json", raw)
