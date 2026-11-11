"""The folders under the shared root, and the checks that the root can hold them."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_ROOT = 80
# The longest issuer ID the context form and the launcher accept (tests/test_context_form.py).
MAX_ISSUER_ID = 40


@dataclass(frozen=True)
class Layout:
    root: Path

    @property
    def issuers(self) -> Path:
        return self.root / "issuers"

    @property
    def engine(self) -> Path:
        return self.root / "_engine"

    @property
    def runs(self) -> Path:
        return self.engine / "runs"

    @property
    def drops(self) -> Path:
        """Where a submitted run's source files live, one folder per run."""
        return self.engine / "drops"

    @property
    def state(self) -> Path:
        return self.engine / "state"

    @property
    def logs(self) -> Path:
        return self.engine / "logs"

    @property
    def uploads(self) -> Path:
        return self.engine / "uploads"


def ensure_layout(root: Path) -> Layout:
    """Create every folder under ``root``; refuse a root so long that Windows paths would break.

    A network path is refused too: the spending cap lives in marker files that must be on this
    machine's own disk. A ``<root>/inbox`` folder left by the earlier folder watcher is neither
    read nor changed."""
    if str(root).startswith(("\\\\", "//")):
        raise ValueError(
            f"root {root} is a network path; use a folder on this machine's own disk "
            "(shared to analysts), because the USD 20 cap depends on marker files that must "
            "not sit on a network or synced path"
        )
    resolved = root.resolve()
    if len(str(resolved)) > MAX_ROOT:
        raise ValueError(
            f"root {resolved} is {len(str(resolved))} characters; "
            f"use a shorter path (at most {MAX_ROOT})"
        )
    layout = Layout(resolved)
    for folder in (
        layout.issuers,
        layout.runs,
        layout.drops,
        layout.state,
        layout.logs,
        layout.uploads,
    ):
        folder.mkdir(parents=True, exist_ok=True)
    return layout
