"""What the watcher does once before polling: launch checks, the folder lock, log and pages."""

from __future__ import annotations

import logging
import os
import socket
import sys
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
_PAGE = (
    '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
    '<meta http-equiv="refresh" content="0; url=_engine/library/index.html">'
    "<title>Issuer library</title></head><body>"
    '<p><a href="_engine/library/index.html">Open the issuer library</a></p></body></html>\n'
)


class StartupRefused(ValueError):
    """The watcher cannot launch runs, or another watcher already owns this folder."""


def open_log(layout: Layout, name: str) -> logging.Logger:
    logger = logging.getLogger(f"{name}.{layout.root}")
    if not logger.handlers:
        handler = logging.FileHandler(layout.logs / "watcher.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def check_launchable(config_id: str, ruling: Path) -> None:
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
