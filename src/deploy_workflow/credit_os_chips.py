"""Citation chips for the Credit OS library: what each handoff row or paragraph points at.

Python resolves; the page draws. A citation the patterns below do not match is a gap, never a
guess. Page text comes from the run's ``source-text/<file>`` JSONL (one ``{"page", "text"}``
object per line); the file name and sha256 come from CP-0's "Complete supplied inventory" table.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

EXCERPT = 600
NOT_SUPPLIED = "Not supplied"
NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
QUOTE = re.compile(r"“([^”]+)”")
BRACKET = re.compile(r"\[(CP-[0-9A-Z]+):\s*([A-Z]\d{1,2}(?:\s*[,;]\s*[A-Z]\d{1,2})*)\s*\]")
PAGE = re.compile(
    r"(?:(?P<key>\b[A-Z])\s*,\s*)?[Pp]ages?\s*:?\s*(?P<a>\d+)(?:\s*[-–]\s*(?P<b>\d+))?"
)
TRAILING = re.compile(r"(?:^|[.;]\s+)([A-Z]\d{1,2}(?:\s*,\s*[A-Z]\d{1,2})*)\.?\s*$")


class Locator(TypedDict):
    kind: Literal["issuer_page", "upstream", "gap"]
    source: str | None
    page: int | None
    page_end: int | None
    module: str | None
    codes: tuple[str, ...]
    label: str | None


def locator(kind: Literal["issuer_page", "upstream", "gap"], **fields: Any) -> Locator:
    """A Locator with every field present; ``fields`` names only those that are not empty."""
    base: dict[str, Any] = {
        "kind": kind,
        "source": None,
        "page": None,
        "page_end": None,
        "module": None,
        "codes": (),
        "label": None,
    }
    unknown = set(fields) - set(base)
    if unknown:
        raise TypeError(f"Unknown locator fields: {sorted(unknown)}")
    return cast(Locator, base | fields)


def as_gap(loc: Locator) -> Locator:
    """The same citation, unresolved: kept with its key and pages so the reader sees what failed."""
    return locator(
        "gap",
        source=loc["source"],
        page=loc["page"],
        page_end=loc["page_end"],
        label=f"Source {loc['source']} page {loc['page']}",
    )


def split_codes(text: str) -> tuple[str, ...]:
    return tuple(c.strip() for c in re.split(r"[,;]", text) if c.strip())


def page_locator(match: re.Match[str], last_key: str | None) -> Locator:
    first = int(match["a"])
    last = int(match["b"]) if match["b"] else None
    key = match["key"] or last_key
    if key is None:
        return locator("gap", page=first, page_end=last, label="Page without a source key")
    return locator("issuer_page", source=key, page=first, page_end=last)


def parse_locators(text: str) -> list[Locator]:
    """Every citation in ``text``, in reading order; what no pattern matches is not guessed."""
    found: list[tuple[int, Locator]] = []
    for m in BRACKET.finditer(text):
        found.append((m.start(), locator("upstream", module=m[1], codes=split_codes(m[2]))))
    last_key: str | None = None
    for m in PAGE.finditer(text):
        last_key = m["key"] or last_key
        found.append((m.start(), page_locator(m, last_key)))
    if (at := text.find(NOT_SUPPLIED)) >= 0:
        found.append((at, locator("gap", label=NOT_SUPPLIED)))
    if (tail := TRAILING.search(text)) and not BRACKET.search(text[tail.start(1) :]):
        found.append((tail.start(1), locator("upstream", codes=split_codes(tail[1]))))
    return [loc for _, loc in sorted(found, key=lambda pair: pair[0])]


def inventory(cp0_sections: list[dict[str, Any]]) -> dict[str, tuple[str, str]]:
    """key -> (file, sha256) from CP-0's "Complete supplied inventory" table."""
    result: dict[str, tuple[str, str]] = {}
    for section in cp0_sections:
        if not section["heading"].startswith("Complete supplied inventory"):
            continue
        for block in section["blocks"]:
            if block["type"] != "table":
                continue
            hashes = [i for i, h in enumerate(block["headers"]) if "sha256" in h.lower()]
            if len(block["headers"]) < 3 or not hashes:
                continue
            for row in block["rows"]:
                cells = row["cells"]
                result[cells[0]] = (cells[1], cells[hashes[0]])
    return result


def read_pages(path: Path) -> tuple[dict[int, str], str | None]:
    """The page texts of one source-text file, or the reason it could not be read."""
    pages: dict[int, str] = {}
    try:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            pages[int(record["page"])] = str(record["text"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {}, f"source text unreadable: {type(error).__name__}: {error}"
    return pages, None


def quote_of(cells: list[str]) -> str | None:
    """The first “…” span among the cells, else the first purely numeric cell."""
    for cell in cells:
        if m := QUOTE.search(cell):
            return m[1]
    return next((c for c in cells if NUMBER.fullmatch(c.strip())), None)


def quote_span(quote: str, text: str) -> tuple[int, int] | None:
    """Where ``quote`` occurs in ``text``; a number matches whole, ignoring thousands commas."""
    if NUMBER.fullmatch(quote.strip()):
        digits = quote.strip().replace(",", "")
        body = ",?".join(re.escape(ch) for ch in digits)
        found = re.search(rf"(?<!\d)(?<!\d,){body}(?!\d)(?!\.\d)", text)
    else:
        found = re.search(re.escape(quote), text)
    return found.span() if found else None


def excerpt_around(text: str, span: tuple[int, int] | None) -> str:
    if span is None:
        return text[:EXCERPT]
    start = max(0, span[0] - (EXCERPT - (span[1] - span[0])) // 2)
    return text[start : start + EXCERPT]


def chip(loc: Locator, line: int, **fields: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "kind": loc["kind"],
        "source": loc["source"],
        "file": None,
        "sha256": None,
        "hash_matches_inventory": None,
        "page": loc["page"],
        "page_end": loc["page_end"],
        "quote": None,
        "quote_found": None,
        "excerpt": None,
        "module": loc["module"],
        "codes": list(loc["codes"]),
        "line": line,
        "label": loc["label"],
        "reason": None,
    }
    base.update(fields)
    return base


class Pages:
    """Source-text files of one run, read once each."""

    def __init__(self, run_dir: Path) -> None:
        self.folder = run_dir / "source-text"
        self.cache: dict[str, tuple[dict[int, str], str | None, str | None]] = {}

    def get(self, name: str) -> tuple[dict[int, str], str | None, str | None]:
        """(pages, actual sha256 or None, problem or None)."""
        if name not in self.cache:
            path = self.folder / name
            if not path.is_file():
                self.cache[name] = ({}, None, "source text file not found")
            else:
                pages, problem = read_pages(path)
                self.cache[name] = (pages, hashlib.sha256(path.read_bytes()).hexdigest(), problem)
        return self.cache[name]


def issuer_chip(
    loc: Locator, line: int, quote: str | None, inv: dict[str, tuple[str, str]], pages: Pages
) -> dict[str, Any]:
    if not inv:
        return chip(as_gap(loc), line, reason="no inventory")
    entry = inv.get(loc["source"] or "")
    if entry is None:
        return chip(as_gap(loc), line, reason="key not in inventory")
    file, expected = entry
    texts, actual, problem = pages.get(file)
    fields: dict[str, Any] = {
        "file": file,
        "sha256": expected,
        "hash_matches_inventory": actual == expected if actual else False,
        "quote": quote,
        "reason": problem,
    }
    first = loc["page"] or 0
    wanted = range(first, (loc["page_end"] or first) + 1)
    here = [(n, texts[n]) for n in wanted if n in texts]
    if problem is None and not here:
        fields["reason"] = "page not in source text"
    span, shown = None, here[0] if here else None
    for number, text in here:
        if quote and (span := quote_span(quote, text)):
            shown = (number, text)
            break
    fields["quote_found"] = (span is not None) if quote and here else None
    if shown:
        fields["excerpt"] = excerpt_around(shown[1], span)
    return chip(loc, line, **fields)


def chips_for_cells(
    cells: list[str], line: int, module: str, inv: dict[str, tuple[str, str]], pages: Pages
) -> list[dict[str, Any]]:
    quote = quote_of(cells)
    result = []
    for cell in cells:
        for loc in parse_locators(cell):
            if loc["kind"] == "issuer_page":
                result.append(issuer_chip(loc, line, quote, inv, pages))
            else:
                # Register codes with no module named belong to the citing module itself.
                owner = module if loc["kind"] == "upstream" else None
                result.append(chip(loc, line, module=loc["module"] or owner))
    return result


def chips_for_output(
    run_dir: Path,
    output_id: str,
    module: str,
    sections: list[dict[str, Any]],
    inv: dict[str, tuple[str, str]],
) -> dict[str, list[dict[str, Any]]]:
    """Chips of one handoff, keyed ``<output id>:<line>`` for each row or paragraph with any."""
    pages = Pages(run_dir)
    result: dict[str, list[dict[str, Any]]] = {}
    for section in sections:
        for block in section["blocks"]:
            if block["type"] == "table":
                units = [(r["line"], r["cells"]) for r in block["rows"]]
            else:
                units = [(block["line"], [block["text"]])]
            for line, cells in units:
                found = chips_for_cells(cells, line, module, inv, pages)
                if found:
                    result[f"{output_id}:{line}"] = found
    return result


def chips(workspace: Path, store: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Chips for every output of the store, keyed like the page's evidence keys."""
    outputs: dict[str, Any] = store["outputs"]
    parsed: dict[str, Any] = store["handoffs"]
    by_run: dict[str, dict[str, tuple[str, str]]] = {}
    for output_id in sorted(outputs):
        record = outputs[output_id]
        folder = output_id.split("/", 1)[0]
        if record["module"] == "CP-0" and not by_run.get(folder):
            by_run[folder] = inventory(parsed.get(record["sha256"]) or [])
    result: dict[str, list[dict[str, Any]]] = {}
    for output_id, record in outputs.items():
        folder = output_id.split("/", 1)[0]
        result |= chips_for_output(
            workspace / "runs" / folder,
            output_id,
            record["module"],
            parsed.get(record["sha256"]) or [],
            by_run.get(folder, {}),
        )
    return result
