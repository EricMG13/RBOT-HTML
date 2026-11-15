"""What the service does once before polling: launch checks, the folder lock, log and page."""

from __future__ import annotations

import logging
import os
import socket
import sys
from pathlib import Path
from typing import IO

from deploy_vii.contracts import PATHWAY_CAP_USD
from deploy_workflow.inbox import runs
from deploy_workflow.inbox.layout import Layout
from deploy_workflow.model.adapter import (
    COPILOT_RUNTIME_VARIABLE,
    KEY_VARIABLES,
    LivePauseInForce,
    check_ruling,
)
from deploy_workflow.model.configs import CONFIGS

ROOT = Path(__file__).resolve().parents[3]
# The start page the service serves.
FORM = ROOT / "docs/templates/context-form.html"
# The only ruling the service runs under; ``Settings.ruling`` defaults to it and start-up checks it.
STANDING_RULING = ROOT / "docs/rulings/2026-11-11-run-start-submit.md"
_PAGE = (
    '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
    '<meta http-equiv="refresh" content="0; url=_engine/library/index.html">'
    "<title>Issuer library</title></head><body>"
    '<p><a href="_engine/library/index.html">Open the issuer library</a></p></body></html>\n'
)


# The caps the owner ruled, USD per run (docs/rulings/2026-11-15-pathway-tiers-and-caps.md),
# written here a second time on purpose: start-up refuses a `PATHWAY_CAP_USD` entry above its
# figure here (or with none), so raising a cap takes a ruling and two deliberate edits.
RULED_CAPS_USD: dict[str, int] = {
    "lite_credit_assessment": 15,
    "credit_snapshot": 25,
    "deep_credit_assessment": 40,
    "earnings_update": 20,
    "relative_value": 20,
    "covenant_refinancing": 20,
    "distressed_restructuring": 20,
    "portfolio_decision": 20,
    "short_snapshot": 20,
}


class StartupRefused(ValueError):
    """The service cannot launch runs, or another service already owns this folder."""


PACKAGE_LOGGER = "deploy_workflow.inbox"
# The one provider whose key start-up does not require: no key only makes its submissions refusable.
OPTIONAL_KEY_PROVIDER = "anthropic"


class _RootHandler(logging.FileHandler):
    """The watcher.log handler of one root (the file keeps its old name), on the package logger."""

    def __init__(self, layout: Layout, own: str) -> None:
        super().__init__(layout.logs / "watcher.log", encoding="utf-8")
        self.root, self._own, self._others = layout.root, own, f"{own.rsplit('.', 1)[0]}."
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))

    def filter(self, record: logging.LogRecord) -> bool:
        # Another root's scheduler logger is not ours; runs and activity records carry no root.
        return record.name == self._own or not record.name.startswith(self._others)


def open_log(layout: Layout, name: str) -> logging.Logger:
    """The scheduler's logger, with one file handler on the package logger.

    The package logger is ``deploy_workflow.inbox``.

    ``scheduler``, ``runs`` and ``activity`` all propagate to it, so their documented fail-open
    warnings reach ``_engine/logs/watcher.log`` as well as the scheduler's own lines. One file per
    root; ``close_log`` removes the handler."""
    package = logging.getLogger(PACKAGE_LOGGER)
    own = f"{name}.{layout.root}"
    if not any(isinstance(h, _RootHandler) and h.root == layout.root for h in package.handlers):
        package.addHandler(_RootHandler(layout, own))
    package.setLevel(logging.INFO)
    return logging.getLogger(own)


def close_log(layout: Layout) -> None:
    package = logging.getLogger(PACKAGE_LOGGER)
    for handler in list(package.handlers):
        if isinstance(handler, _RootHandler) and handler.root == layout.root:
            package.removeHandler(handler)
            handler.close()


def check_launchable(ruling: Path) -> None:
    """Refuse start-up unless every launch the service can make is allowed by the standing ruling.

    All four configs of ``runs.LAUNCH_CONFIGS`` must be known and named by the ruling. The OpenAI
    key is required; the Anthropic key is optional (without it a Claude submission is refused, see
    ``submissions.require_provider_key``). Each run's cap is its pathway's (``runs.cap_of``,
    ruling 2026-11-15-pathway-tiers-and-caps), and no pathway's cap may pass the ruled figure
    in ``RULED_CAPS_USD``."""
    for pathway, cap in PATHWAY_CAP_USD.items():
        ruled = RULED_CAPS_USD.get(pathway)
        if ruled is None or not cap.is_finite() or cap > ruled:
            raise StartupRefused(
                f"the {pathway} cap USD {cap} is above the ruled USD {ruled} of "
                "docs/rulings/2026-11-15-pathway-tiers-and-caps.md"
                if ruled is not None
                else f"the {pathway} cap USD {cap} has no ruled figure in "
                "docs/rulings/2026-11-15-pathway-tiers-and-caps.md"
            )
    if ruling.resolve() != STANDING_RULING.resolve():
        raise StartupRefused(
            f"the service runs only under its standing ruling {STANDING_RULING}, not {ruling}"
        )
    for config_id in runs.LAUNCH_CONFIGS:
        config = CONFIGS.get(config_id)
        if config is None:
            raise StartupRefused(f"unknown config {config_id!r}")
        try:
            check_ruling(config_id, ruling)
        except (LivePauseInForce, ValueError, OSError) as error:
            raise StartupRefused(f"live runs are not allowed: {error}") from error
        key = KEY_VARIABLES[config.provider]
        if config.provider != OPTIONAL_KEY_PROVIDER and not os.environ.get(key):
            raise StartupRefused(f"{key} is not set in the launching environment")
        runtime = Path(os.environ.get(COPILOT_RUNTIME_VARIABLE, ""))
        if config.provider == "copilot" and not runtime.is_file():
            raise StartupRefused(f"{COPILOT_RUNTIME_VARIABLE} must name an existing file")


def take_lock(layout: Layout) -> IO[str]:
    """Hold an operating-system lock on byte 0 of ``_engine/watcher.lock`` for the service's life.

    The file keeps the name ``watcher.lock`` so a folder watcher left running from an earlier
    version and this service exclude each other. The lock goes with the process, however it ends,
    so no stale lock can block a restart and two holders can never both hold it. Both platforms
    lock the same byte of the same kind of handle: the file is opened without truncating or
    appending and rewound first, so whatever text an earlier holder left cannot move the locked
    byte. Once the lock is held the file gets ``<host> <pid>`` for the message."""
    descriptor = os.open(layout.engine / "watcher.lock", os.O_RDWR | os.O_CREAT, 0o644)
    handle = os.fdopen(descriptor, "r+", encoding="utf-8")
    try:
        handle.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        try:
            handle.seek(0)
            holder = handle.read().strip() or "no details"
        except (OSError, UnicodeDecodeError):  # Windows: the locked byte cannot be read
            holder = "no details"
        handle.close()
        raise StartupRefused(
            "another run page service (or an old folder watcher) is running "
            f"on this folder ({holder})"
        ) from None
    handle.seek(0)
    handle.truncate()
    handle.write(f"{socket.gethostname()} {os.getpid()}")
    handle.flush()
    return handle


def release_lock(handle: IO[str]) -> None:
    try:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        handle.close()


def write_pages(layout: Layout) -> None:
    """The ``library.html`` page that opens the library; an existing one is never overwritten."""
    try:
        with (layout.root / "library.html").open("xb") as page:
            page.write(_PAGE.encode())
    except FileExistsError:
        pass  # never overwritten
