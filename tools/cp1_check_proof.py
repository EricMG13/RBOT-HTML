"""Offline proof of CP-1's acceptance check: no provider call, no network.

    uv run python tools/cp1_check_proof.py HANDOFF.md [HANDOFF.md ...]
    uv run python tools/cp1_check_proof.py --instructions SCRATCH_DIR [HANDOFF.md ...]

Each handoff is read and every issue the check finds is printed, one per line (exit 1 when any
handoff has an issue, 0 when none does). With `--instructions` every pathway is also prepared
offline in SCRATCH_DIR (the way `all_instructions` in tests/test_cpos_launch.py does) and the
script prints CP-1's instruction size, the sha256 of each method section sent to CP-1, and the
pathway's total against its ceiling (the `INSTRUCTION_BUDGET` of that test file, read, not copied).
"""

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deploy_workflow.owners import cpos_launch
from deploy_workflow.owners.cpos_cp1_check import cp1_issues

TESTS = ROOT / "tests/test_cpos_launch.py"
ISSUER = "Northbridge Synthetic Group"
AS_OF = "2025-03-31"


def instruction_budget() -> dict[str, int]:
    """The per-pathway ceilings, read from the launcher test that holds the answer key."""
    for node in ast.parse(TESTS.read_text()).body:
        if isinstance(node, ast.Assign) and [getattr(t, "id", "") for t in node.targets] == [
            "INSTRUCTION_BUDGET"
        ]:
            value = ast.literal_eval(node.value)
            assert isinstance(value, dict)
            return {str(k): int(v) for k, v in value.items()}
    raise SystemExit(f"INSTRUCTION_BUDGET not found in {TESTS}")


def check_handoffs(paths: list[Path]) -> int:
    found = 0
    for path in paths:
        issues = cp1_issues(path.read_text(encoding="utf-8"))
        print(f"{path}: {len(issues)} issue(s)")
        for number, issue in enumerate(issues, 1):
            print(f"  {number}. {issue}")
        found += len(issues)
    return found


def prepare_pathway(scratch: Path, pathway: str) -> tuple[Path, cpos_launch.Prepared]:
    work = scratch / pathway
    issuer = work / "issuer"
    (issuer / "filings").mkdir(parents=True, exist_ok=True)
    (issuer / "annual.txt").write_text("Net sales were 100.")
    (issuer / "filings/notes.md").write_text("Notes mature in 2030.")
    data = json.loads((ROOT / "cases/cpdr-context-cutoff/context.json").read_text())
    data["run"].update(pathway=pathway, as_of=AS_OF, cutoff="")
    data["identity"].update(issuer_name=ISSUER, issuer_id="nbg")
    context = work / "context.json"
    context.write_text(json.dumps(data))
    return work, cpos_launch.prepare(context, issuer, work / "out", config="sol-medium", cap="50")


def report_sizes(scratch: Path) -> None:
    sections = cpos_launch.method_sections("CP-1")
    print("CP-1 method sections sent (name, characters, sha256):")
    for name, text in sections:
        print(f"  {name}  {len(text):,}  {hashlib.sha256(text.encode()).hexdigest()}")
    for pathway, ceiling in sorted(instruction_budget().items()):
        work, prepared = prepare_pathway(scratch, pathway)
        texts = {
            module: (work / "out" / spec.path).read_text()
            for module, spec in prepared.plan.instructions.items()
        }
        total = sum(len(t) for m, t in texts.items() if m != "CP-8")
        cp1 = len(texts["CP-1"]) if "CP-1" in texts else 0
        verdict = "within" if total <= ceiling else "OVER"
        print(
            f"{pathway}: CP-1 {cp1:,}; total {total:,} / ceiling {ceiling:,} "
            f"(headroom {ceiling - total:,}) {verdict}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("handoffs", nargs="*", type=Path)
    parser.add_argument("--instructions", type=Path, metavar="DIR")
    args = parser.parse_args()
    found = check_handoffs(args.handoffs)
    if args.instructions is not None:
        report_sizes(args.instructions.resolve())
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
