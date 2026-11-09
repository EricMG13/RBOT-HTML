"""Stand-in for the real launcher in tests. Calls no provider, spends nothing.

``FAKE_PLAN`` (JSON in the environment): prepare_exit, prepare_error, events [[name, {fields}]],
sleep, exit, report (write deliveries/d1/report.html on a live run).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # the package is not installed

from deploy_workflow.run_events import append_event


def main() -> int:
    parser = argparse.ArgumentParser()
    for flag in ("--context", "--sources", "--config", "--cap", "--out", "--ruling", "--max-turns"):
        parser.add_argument(flag)
    parser.add_argument("--modules", nargs="+")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--no-library", action="store_true")
    args = parser.parse_args()
    plan = json.loads(os.environ.get("FAKE_PLAN", "{}"))
    if not args.live:
        if plan.get("prepare_error"):
            print(plan["prepare_error"], file=sys.stderr)
        return int(plan.get("prepare_exit", 0))
    out = Path(args.out)
    for name, fields in plan.get("events", []):
        append_event(out, name, **fields)
    if plan.get("report"):
        target = out / "deliveries" / "d1" / "report.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("<html><body>report</body></html>", encoding="utf-8")
    time.sleep(float(plan.get("sleep", 0.0)))
    return int(plan.get("exit", 0))


if __name__ == "__main__":
    raise SystemExit(main())
