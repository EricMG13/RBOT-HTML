"""Start a CP-OS run with the bundled Python: the command-line launcher, unchanged.

``Run workflow.cmd`` calls this and passes its arguments through. Without ``--live`` the launcher
only prepares and reviews the run; ``--live`` with a ruling is the paid run (see the README).
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src" if (HERE / "src").is_dir() else HERE.parents[2] / "src"))

from deploy_workflow.owners.cpos_launch import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
