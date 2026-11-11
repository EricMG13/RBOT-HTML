"""What the watcher does once before polling: launch checks, the folder lock, log and pages."""

from __future__ import annotations

import logging
import os
import socket
import sys
from decimal import Decimal
from pathlib import Path
from typing import IO

from deploy_workflow.inbox import drops
from deploy_workflow.inbox.drops import Layout
from deploy_workflow.model.adapter import (
    COPILOT_RUNTIME_VARIABLE,
    KEY_VARIABLES,
    LivePauseInForce,
    check_ruling,
)
from deploy_workflow.model_testing.configs import CONFIGS

ROOT = Path(__file__).resolve().parents[3]
FORM = ROOT / "docs/templates/context-form.html"
# The only ruling the watcher runs under; ``Settings.ruling`` defaults to it and start-up checks it.
STANDING_RULING = ROOT / "docs/rulings/2026-11-11-run-start-submit.md"
_PAGE = (
    '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
    '<meta http-equiv="refresh" content="0; url=_engine/library/index.html">'
    "<title>Issuer library</title></head><body>"
    '<p><a href="_engine/library/index.html">Open the issuer library</a></p></body></html>\n'
)


class StartupRefused(ValueError):
    """The watcher cannot launch runs, or another watcher already owns this folder."""


PACKAGE_LOGGER = "deploy_workflow.inbox"
# USD per run the standing ruling allows (docs/rulings/2026-11-11-run-start-submit.md; AGENTS.md).
RULED_RUN_CAP = Decimal(20)


class _RootHandler(logging.FileHandler):
    """The watcher.log handler of one root, attached to the package logger."""

    def __init__(self, layout: Layout, own: str) -> None:
        super().__init__(layout.logs / "watcher.log", encoding="utf-8")
        self.root, self._own, self._others = layout.root, own, f"{own.rsplit('.', 1)[0]}."
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))

    def filter(self, record: logging.LogRecord) -> bool:
        # Another root's watcher logger is not ours; runs and activity records carry no root.
        return record.name == self._own or not record.name.startswith(self._others)


def open_log(layout: Layout, name: str) -> logging.Logger:
    """The watcher's logger, with one file handler on the package logger ``deploy_workflow.inbox``.

    ``watcher``, ``runs`` and ``activity`` all propagate to it, so their documented fail-open
    warnings reach ``_engine/logs/watcher.log`` as well as the watcher's own lines. One file per
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


def check_launchable(config_id: str, ruling: Path, cap: Decimal) -> None:
    if cap.is_nan() or cap > RULED_RUN_CAP:
        raise StartupRefused(
            f"cap {cap} is above USD {RULED_RUN_CAP} per run, the limit of the standing ruling "
            "docs/rulings/2026-11-11-run-start-submit.md"
        )
    if ruling.resolve() != STANDING_RULING.resolve():
        raise StartupRefused(
            f"the watcher runs only under its standing ruling {STANDING_RULING}, not {ruling}"
        )
    config = CONFIGS.get(config_id)
    if config is None:
        raise StartupRefused(f"unknown config {config_id!r}")
    try:
        check_ruling(config_id, ruling)
    except (LivePauseInForce, ValueError, OSError) as error:
        raise StartupRefused(f"live runs are not allowed: {error}") from error
    key = KEY_VARIABLES[config.provider]
    if not os.environ.get(key):
        raise StartupRefused(f"{key} is not set in the launching environment")
    runtime = Path(os.environ.get(COPILOT_RUNTIME_VARIABLE, ""))
    if config.provider == "copilot" and not runtime.is_file():
        raise StartupRefused(f"{COPILOT_RUNTIME_VARIABLE} must name an existing file")


def take_lock(layout: Layout) -> IO[str]:
    """Hold an operating-system lock on byte 0 of ``_engine/watcher.lock`` for the watcher's life.

    The lock goes with the process, however it ends, so no stale lock can block a restart and
    two watchers can never both hold it. Both platforms lock the same byte of the same kind of
    handle: the file is opened without truncating or appending and rewound first, so whatever
    text an earlier holder left cannot move the locked byte. Once the lock is held the file gets
    ``<host> <pid>`` for the message."""
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
        raise StartupRefused(f"another watcher is running on this folder ({holder})") from None
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
    try:
        with (layout.root / "library.html").open("xb") as page:
            page.write(_PAGE.encode())
    except FileExistsError:
        pass  # never overwritten
    drops.write_templates(layout, FORM)
