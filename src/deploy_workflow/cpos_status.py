"""Atomic public progress projection; never contains prompts or credentials."""

import json
from pathlib import Path

from deploy_workflow.platform_io import write_atomic


def progress(directory: Path, module: str, step: str) -> None:
    atomic_json(directory / "progress.json", {"module": module, "step": step})


def atomic_json(target: Path, value: object) -> None:
    write_atomic(target, json.dumps(value))
