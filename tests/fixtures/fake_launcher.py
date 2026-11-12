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

from deploy_workflow.model.adapter import KEY_VARIABLES, LivePauseInForce, check_ruling
from deploy_workflow.model_testing.configs import CONFIGS
from deploy_workflow.run_events import append_event


def main() -> int:
    parser = argparse.ArgumentParser()
    for flag in ("--context", "--sources", "--cap", "--out", "--ruling", "--max-turns", "--prior"):
        parser.add_argument(flag)
    parser.add_argument("--config", choices=tuple(CONFIGS), required=True)
    parser.add_argument("--modules", nargs="+")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--balanced", action="store_true")
    parser.add_argument("--no-library", action="store_true")
    args = parser.parse_args()
    plan = json.loads(os.environ.get("FAKE_PLAN", "{}"))
    if args.live and args.ruling is None:
        print(f"--live needs --ruling docs/rulings/<file>.md naming {args.config}", file=sys.stderr)
        return 2
    try:  # the real launcher's checks, run before any work
        if args.ruling is not None:
            check_ruling(args.config, Path(args.ruling))
    except (ValueError, OSError, LivePauseInForce) as error:
        print(error, file=sys.stderr)
        return 2
    key = KEY_VARIABLES[CONFIGS[args.config].provider]
    if args.live and not os.environ.get(key):
        print(f"--live needs {key} in the launching environment", file=sys.stderr)
        return 2
    if not args.live:
        if plan.get("prepare_error"):
            print(plan["prepare_error"], file=sys.stderr)
        return int(plan.get("prepare_exit", 0))
    out = Path(args.out)
    for name, fields in plan.get("events", []):
        append_event(out, name, **fields)
    if plan.get("report"):
        folder = out / "deliveries" / "d1"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "delivery.json").write_text('{"files": {}}', encoding="utf-8")
        if plan.get("report_page"):  # an earlier-format delivery also holds a rendered report
            (folder / "report.html").write_text(
                "<html><body>report</body></html>", encoding="utf-8"
            )
    time.sleep(float(plan.get("sleep", 0.0)))
    return int(plan.get("exit", 0))


if __name__ == "__main__":
    raise SystemExit(main())
