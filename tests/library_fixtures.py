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


FINDING_ROW = "| One observed item. | None assessed. | Low |"
HANDOFF = """# {module} handoff

## Request
{name}, as of {as_of}.

## Findings

### Reader summary

| Bottom line | Confidence | Main limitation |
| --- | --- | --- |
| {bottom} | {confidence} | Synthetic fixture only. |

| Finding | Creditor impact | Confidence |
| --- | --- | --- |
{finding}

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
    cp0_extra: str = ""  # Text appended to the CP-0 handoff, such as a source inventory.
    cp0_confidence: str = "Medium"  # The Confidence cell of the CP-0 Reader summary.
    cp1_finding: str = FINDING_ROW  # The one row of the CP-1 Reader summary's findings table.
    cp1_findings: str = ""  # Text inserted into the CP-1 handoff just before its Sources section.
    cp1_extra: str = ""  # Text appended to the CP-1 handoff, such as chart data tables.
    sent_extra: str = ""  # Text sent after the method block, such as a section since dropped.
    supplied: tuple[str, ...] = ()  # Supplied file names, as workflow.json `sources` lists them.


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
            module=module,
            name=issuer_name,
            as_of=as_of,
            bottom=f"{module} bottom line.",
            confidence=spec.cp0_confidence if module == "CP-0" else "Medium",
            finding=spec.cp1_finding if module == "CP-1" else FINDING_ROW,
        )
        if module == "CP-0":
            answer += spec.cp0_extra
        if module == "CP-1":
            head, heading, tail = answer.rpartition("## Sources")
            answer = head + spec.cp1_findings + heading + tail + spec.cp1_extra
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
    workflow = {"run": run, "instructions": instructions, "provider_cap_usd": "12"}
    if spec.supplied:
        workflow["sources"] = {
            name: {
                "path": f"source-text/{name}.txt",
                "sha256": put(run_dir / f"source-text/{name}.txt", f"text of {name}\n".encode()),
            }
            for name in spec.supplied
        }
    put(run_dir / "workflow.json", json.dumps(workflow).encode())
    manifest = json.dumps({"run": run, "handoffs": handoffs}, indent=2).encode()
    manifest_sha = sha(manifest)
    put(run_dir / f"delivery-{manifest_sha}.json", manifest)
    view_run = dict(run, issuer_id=spec.view_issuer or issuer_id)
    # A legacy CP-OS report.html, as older deliveries carry it. The library no longer reads or
    # shows it (the report adapter is retired); it is listed and hash-checked like any delivered
    # file, and without_report() builds the same delivery without it.
    payload = json.dumps(
        {"run": {"issuer_name": issuer_name}, "report": {"pathway": {"title": "Credit snapshot"}}}
    ).replace("<", "\\u003c")
    report = (
        f'<!doctype html><title>{issuer_name} report</title><body><main id="view-root">'
        f'<div class="page-head"><h1>Report</h1></div></main>'
        f'<aside id="inspector"><div class="insp-head"></div>'
        f'<div id="inspector-content" role="tabpanel"><p>Select a figure or source</p></div>'
        f'</aside><script id="report-data" type="application/json">{payload}</script></body>'
    ).encode()
    files = {
        **({"report.html": report} if spec.report_page else {}),
        "view.json": json.dumps({"run": view_run}).encode(),
        **{f"{m}.md": (run_dir / handoffs[m]["path"]).read_bytes() for m in modules},
    }
    delivery_id = sha(json.dumps({n: sha(r) for n, r in sorted(files.items())}).encode())
    delivered = run_dir / "deliveries" / delivery_id
    receipt = {"files": {name: put(delivered / name, raw) for name, raw in files.items()}}
    receipt_sha = put(delivered / "delivery.json", json.dumps(receipt).encode())
    completion = {
        "kind": "cpos-markdown-delivery/1",
        "execution": "live-provider",
        "scope": "Synthetic fixture run; not analytical review.",
        "provider_cap_usd": "12",
        "modules": selected,
        "module_execution": {m: spec.execution for m in modules},
        "delivery_manifest_sha256": manifest_sha,
        **(
            {"report_sha256": sha(report)} if spec.report_page else {"delivery_sha256": receipt_sha}
        ),
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


def without_report(run_dir: Path) -> Path:
    """Make the run's delivery one of the new kind.

    No report.html in the folder or in its delivery.json, and a completion record that carries
    delivery_sha256 (of delivery.json) instead of report_sha256. Returns the delivery folder."""
    (delivered,) = (run_dir / "deliveries").iterdir()
    (delivered / "report.html").unlink()
    receipt = json.loads((delivered / "delivery.json").read_text())
    del receipt["files"]["report.html"]
    raw = json.dumps(receipt).encode()
    (delivered / "delivery.json").write_bytes(raw)

    def swap(record: dict) -> None:
        del record["report_sha256"]
        record["delivery_sha256"] = sha(raw)

    rewrite_completion(run_dir, swap)
    return delivered


# Cited handoff text and its source-text file, for tests/test_credit_os_chips.py.
SOURCE_PAGES = (
    b'{"page": 122, "text": "Other note text."}\n'
    b'{"page": 123, "text": "Cash paid during the period for interest, net $ 1,158 and more."}\n'
    b'{"page": "124", "text": "Interest paid was lower."}\n'
)
SOURCE_NAME = "NBG_2024-12-31_10-K_fixture.htm.jsonl"


def inventory_text(digest: str) -> str:
    """A CP-0 inventory section, the sha256 of the supplied K source being `digest`."""
    return f"""
### Complete supplied inventory and provenance

| Label | Exact supplied source name | Exact sha256 | Source disposition |
| --- | --- | --- | --- |
| K | {SOURCE_NAME} | {digest} | Primary annual source. |
| Settings | context | {"0" * 64} | Dated settings only. |
"""


CITED = """
### Cited rows

| Item | Value | Basis |
| --- | --- | --- |
| Cash interest | 1,158 | K, page:123 states the figure. D1, D3. |
| Wrong interest | 1,159 | K, page:123 states the figure. |
| Quoted interest | 7 | K, page:123 says “Cash paid during the period”. |
| Upstream | 2 | [CP-1: D4, F1] |
| Absent | n/a | Not supplied: no covenant package. |

A paragraph citing K, page:124 only.
"""


# What a module report shows beyond the plain fixture: a cited chart row, a finding whose
# citation quotes the page, and a reader table with two numeric columns. Appended to the CP-1
# handoff with CITED.
REPORT_ROWS = """
### Chart data: interest paid

| Period | Cash interest | Reporting unit | Basis and limitation |
| --- | --- | --- | --- |
| FY2024 | 1158 | US$m | K, page:123 states the figure. D1. |
| FY2023 | 1160 | US$m | K, page:122 does not state it. |

### Cash table

| Measure | FY2023 | FY2024 | Unit |
| --- | --- | --- | --- |
| Cash interest | 1,160 | 1,158 | US$m |
| Gross coupons | Not supplied | Not supplied | US$m |

### Quoted findings

| Finding | Creditor impact | Confidence |
| --- | --- | --- |
| Cash interest was paid. | K, page:123 says “Cash paid during the period”. | High |
"""


# An inventory keyed by multi-word aliases with a "Role in this review" column, as one real run
# writes it, and a CP-1 section citing them by leading word. `alias_inventory_text` takes the
# sha256 of the annual filing and of the annual PDF.
ALIAS_FILING_NAME = "NBG_FY2024_10-K_alias.htm.jsonl"
ALIAS_PDF_NAME = "NBG_FY2024_annual-report_alias.pdf.jsonl"
ALIAS_FILING_PAGES = (
    b'{"page": 71, "text": "Revenue was 3,472 in the year and (11) of other items."}\n'
    b'{"page": 72, "text": "Second page of the filing."}\n'
)
ALIAS_PDF_PAGES = b'{"page": 71, "text": "Revenue was 9,999 in the PDF."}\n'


def alias_inventory_text(filing_digest: str, pdf_digest: str) -> str:
    return f"""
### Supplied source inventory and integrity

| Alias | Exact supplied source name | Exact sha256 | Role in this review |
| --- | --- | --- | --- |
| Annual filing | {ALIAS_FILING_NAME} | {filing_digest} | Primary annual authority |
| Annual PDF | {ALIAS_PDF_NAME} | {pdf_digest} | Sampled alternate annual representation |
| Settings | context | {"0" * 64} | Dated settings only |
"""


ALIAS_CITED = """
### Alias rows

| Item | Value | Basis |
| --- | --- | --- |
| Short form | 3472 | Annual page:71 states the figure. |
| Bracketed | -11 | Annual p.71 prints it. |
| Listed | 1 | Annual pages 71, 72 and Annual filing pp.71–72. |
"""
