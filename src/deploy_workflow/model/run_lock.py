"""The single-writer lock on a run folder, taken by CP-OS and its handoff executor.

Moved from ``run_pathway.py`` when the Deploy VII journal runner was retired (owner, 2026-11-15).
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from pathlib import Path

from deploy_workflow.platform_io import locks as fcntl
from deploy_workflow.run_inputs import RunInputError


class RunDirBusy(RunInputError):
    """Another run holds this run directory's lock (single writer, R9a)."""

    code = "run_dir_busy"


@contextlib.contextmanager
def _single_writer(run_dir: Path) -> Iterator[None]:
    """Hold an exclusive, non-blocking ``flock`` on ``run_dir`` itself for the whole run, fresh or
    resumed (R9a): no lock file is written, and the kernel drops the lock if the process dies.
    A second run on the directory is refused (``RunDirBusy``) before it writes."""
    # ponytail: ``flock`` is advisory; a network filesystem, or a process that never takes this
    # lock, is not excluded (the ceiling of ``CallLog``'s lock too).
    if os.name == "nt":
        fd = os.open(run_dir / ".run.lock", os.O_RDWR | os.O_CREAT, 0o600)
    else:
        fd = os.open(run_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RunDirBusy(f"{run_dir} is held by another run") from None
        yield
    finally:
        os.close(fd)  # closing releases the lock
