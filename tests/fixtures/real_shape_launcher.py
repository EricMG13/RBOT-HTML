"""Stand-in launcher that leaves a run folder in the shape CP-OS leaves. Calls no provider.

Takes the real launcher's flags. Without --live: exits 0, or 2 when the sources hold REFUSE.txt.
With --live: writes a completed run folder (``tests/library_fixtures.make_run``), one settled
charge through the real ``Budget`` and the real ``delivered`` event, so the real library rebuild
lists the run.

``DEPLOY_WORKFLOW_PID_FILE``: like the real launcher, writes its own process ID there first.
``REAL_SHAPE_HOLD``: a path; on a live run, stays alive until that file exists.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import library_fixtures

from deploy_workflow.model.budget import Budget
from deploy_workflow.run_events import append_event


def main() -> int:
    pid_file = os.environ.get("DEPLOY_WORKFLOW_PID_FILE")
    if pid_file:
        Path(pid_file).write_text(str(os.getpid()), encoding="utf-8")
    parser = argparse.ArgumentParser()
    for flag in ("--context", "--sources", "--config", "--cap", "--out", "--ruling", "--prior"):
        parser.add_argument(flag)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--no-library", action="store_true")
    args = parser.parse_args()
    if not args.no_library:
        print("the watcher must pass --no-library", file=sys.stderr)
        return 2
    if not args.live:
        return 0
    if not args.ruling:
        print("a live launch must carry the ruling", file=sys.stderr)
        return 2
    hold = os.environ.get("REAL_SHAPE_HOLD")
    while hold and not Path(hold).exists():
        time.sleep(0.05)
    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    out = Path(args.out)
    append_event(out, "module_started", module="CP-0")
    library_fixtures.make_run(
        out.parent.parent,
        out.name,
        issuer_id=context["identity"]["issuer_id"],
        issuer_name=context["identity"]["issuer_name"],
        as_of=context["run"]["as_of"],
    )
    budget = Budget(Decimal(args.cap), out / "live")
    call = "call-" + "a" * 32
    budget.reserve(call, Decimal("1.25"), config_id=args.config)
    budget.settle(call, Decimal("1.10"))
    append_event(out, "module_accepted", module="CP-0")
    append_event(out, "delivery_started")
    time.sleep(0.3)
    append_event(out, "delivered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
