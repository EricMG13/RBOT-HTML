"""Filing: safe folder names, one issuer folder per issuer ID, reports copied without overwrite."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

from deploy_workflow import platform_io
from deploy_workflow.inbox.drops import Layout

REGISTRY_NAME = "issuers.json"
_UNSAFE = re.compile(r'[\\/:*?"<>|]')
_RESERVED = re.compile(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])", re.IGNORECASE)


def safe_name(text: str, limit: int = 80) -> str:
    """A name that is safe as a folder or file name on Windows, macOS and Linux."""
    text = "".join(" " if unicodedata.category(c) == "Cc" else c for c in text)
    cleaned = " ".join(_UNSAFE.sub(" ", text).split()).rstrip(". ")
    cleaned = cleaned[:limit].rstrip(". ")
    if not cleaned or _RESERVED.fullmatch(cleaned.split(".", 1)[0].strip()):
        return "_" + cleaned
    return cleaned


def _same_name(name: str) -> str:
    """The form in which two names are one folder on a case- and normalisation-insensitive disk."""
    return unicodedata.normalize("NFC", name).casefold()


def _registry_path(layout: Layout) -> Path:
    return layout.state / REGISTRY_NAME


def _load(layout: Layout) -> dict[str, str]:
    path = _registry_path(layout)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data.items()
    ):
        raise ValueError(f"{path} is not a map of issuer ID to folder name")
    return data


def _save(layout: Layout, registry: dict[str, str]) -> None:
    path = _registry_path(layout)
    fd, temp = tempfile.mkstemp(prefix=".issuers-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(registry, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        platform_io.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def issuer_folder(layout: Layout, issuer_id: str, issuer_name: str) -> tuple[Path, bool]:
    """The issuer's folder, fixed by the first run for that ID; and whether the name now differs."""
    registry = _load(layout)
    # Cut the name, never the ID: the ID is what keeps two issuers' folders apart. Cleaning only
    # shortens a name, so the joined text stays within the limit.
    room = max(0, 80 - len(f" ({issuer_id})"))
    wanted = safe_name(f"{issuer_name[:room]} ({issuer_id})")
    fixed = registry.get(issuer_id)
    if fixed is not None:
        differs = fixed != wanted and re.fullmatch(re.escape(wanted) + r" \d+", fixed) is None
        return layout.issuers / fixed, differs
    taken = {_same_name(name) for name in registry.values()}
    name, number = wanted, 1
    while _same_name(name) in taken or (layout.issuers / name).exists():
        number += 1
        name = f"{wanted} {number}"
    registry[issuer_id] = name
    _save(layout, registry)
    return layout.issuers / name, False


def file_report(  # noqa: PLR0913 - signature fixed by the build plan; callers pass keywords
    layout: Layout,
    report: Path,
    *,
    issuer_id: str,
    issuer_name: str,
    as_of: str,
    pathway: str,
    claimed: frozenset[Path] = frozenset(),
) -> Path:
    """Copy ``report`` into the issuer's folder under a name that is never already in use.

    A file already there for this as-of date and pathway with the same bytes, and not in
    ``claimed`` (files another run's record names), is reused: a stop between filing and saving
    the record must not file the same report twice."""
    folder, _ = issuer_folder(layout, issuer_id, issuer_name)
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{safe_name(as_of)} {safe_name(pathway)}"
    data = report.read_bytes()
    for name in sorted(os.listdir(folder)):
        path = folder / name
        if (
            re.fullmatch(re.escape(stem) + r"(-\d+)?\.html", name)
            and path not in claimed
            and path.is_file()
            and not path.is_symlink()
            and path.read_bytes() == data
        ):
            return path
    number = 1
    while True:
        target = folder / (f"{stem}.html" if number == 1 else f"{stem}-{number}.html")
        try:
            with target.open("xb") as handle:
                try:
                    handle.write(data)
                except BaseException:
                    handle.close()
                    target.unlink(missing_ok=True)  # No partial report is left behind.
                    raise
        except FileExistsError:
            number += 1
            continue
        return target
