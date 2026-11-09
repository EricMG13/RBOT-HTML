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
from typing import Any, Literal, NamedTuple, TypedDict, cast

EXCERPT = 600
NOT_SUPPLIED = "Not supplied"
NO_PAGE = "no page"
NUMBER = re.compile(r"[-−]?\d[\d,]*(?:\.\d+)?")
QUOTE = re.compile(r"“([^”]+)”")
BRACKET = re.compile(r"\[(CP-[0-9A-Z]+):\s*([A-Z]\d{1,2}(?:\s*[,;]\s*[A-Z]\d{1,2})*)\s*\]")
PAGE = re.compile(
    r"(?:(?P<key>\b[A-Z])\s*,\s*)?(?<![\w?&=/#.:-])[Pp]ages?\s*:?\s*(?P<a>\d+)(?!\d|\.\d)"
    r"(?:\s*[-–]\s*(?P<b>\d+)(?!\d|\.\d))?"
)
# Register letters exclude A, B, H and Q, which also open rating grades ("B2"), halves and quarters.
CODE = r"[CD-GI-PR-Z]\d{1,2}"
TRAILING = re.compile(rf"(?:\.\s+|;\s*|(?<=[A-Za-z])\s+)({CODE}(?:\s*[,;]\s*{CODE})*)\.?\s*$")
PERIOD_HEADER = re.compile(r"\b(?:period|year|date)s?\b", re.IGNORECASE)
SENTENCE_END = re.compile(r"[.;]\s")
CLAIM_HEADERS = ("finding", "bottom line")


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


def span_text(page: int | None, page_end: int | None) -> str:
    return f"{page}-{page_end}" if page_end else f"{page}"


def as_gap(loc: Locator) -> Locator:
    """The same citation, unresolved: kept with its key and pages so the reader sees what failed."""
    return locator(
        "gap",
        source=loc["source"],
        page=loc["page"],
        page_end=loc["page_end"],
        label=f"{loc['source']} p.{span_text(loc['page'], loc['page_end'])} · unresolved",
    )


def split_codes(text: str) -> tuple[str, ...]:
    return tuple(c.strip() for c in re.split(r"[,;]", text) if c.strip())


def page_locator(match: re.Match[str], last_key: str | None) -> Locator:
    first = int(match["a"])
    last = int(match["b"]) if match["b"] else None
    key = match["key"] or last_key
    if key is None:
        return locator(
            "gap", page=first, page_end=last, label=f"p.{span_text(first, last)} · no key"
        )
    return locator("issuer_page", source=key, page=first, page_end=last)


def scan(text: str, row_key: str | None = None) -> list[tuple[int, Locator]]:
    """Every citation in ``text`` with its position; what no pattern matches is not guessed.
    ``row_key`` is the source key the row itself names, for a page with no key of its own."""
    found: list[tuple[int, Locator]] = []
    for m in BRACKET.finditer(text):
        found.append((m.start(), locator("upstream", module=m[1], codes=split_codes(m[2]))))
    last_key: str | None = None
    previous = 0
    for m in PAGE.finditer(text):
        if SENTENCE_END.search(text, previous, m.start()):
            last_key = None
        last_key = m["key"] or last_key
        previous = m.end()
        found.append((m.start(), page_locator(m, last_key or row_key)))
    if (at := text.find(NOT_SUPPLIED)) >= 0:
        found.append((at, locator("gap", label=NOT_SUPPLIED)))
    if (tail := TRAILING.search(text)) and not BRACKET.search(text[tail.start(1) :]):
        found.append((tail.start(1), locator("upstream", codes=split_codes(tail[1]))))
    return sorted(found, key=lambda pair: pair[0])


def parse_locators(text: str) -> list[Locator]:
    """Every citation in ``text``, in reading order."""
    return [loc for _, loc in scan(text)]


def inventory(cp0_sections: list[dict[str, Any]]) -> dict[str, tuple[str, str]]:
    """key -> (file, sha256) from the CP-0 inventory table: any section headed "...inventory..."
    holding a table with a sha256 column; the key is column 0 and the file name column 1."""
    result: dict[str, tuple[str, str]] = {}
    for section in cp0_sections:
        if "inventory" not in section["heading"].lower():
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


def read_pages(raw: bytes) -> tuple[dict[int, str], str | None]:
    """The page texts of one source-text file, or the reason it could not be read."""
    pages: dict[int, str] = {}
    try:
        for line in raw.decode("utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                pages[int(record["page"])] = str(record["text"])
    except (ValueError, KeyError, TypeError) as error:
        return {}, f"source text unreadable: {type(error).__name__}: {error}"
    return pages, None


def numeric_cell(cells: list[str], headers: list[str]) -> str | None:
    """The first purely numeric cell outside a period, year or date column: the number is the
    claim for every page the row cites."""
    for i, cell in enumerate(cells):
        label = headers[i] if i < len(headers) else ""
        if NUMBER.fullmatch(cell.strip()) and not PERIOD_HEADER.search(label):
            return cell.strip()
    return None


def bound_quotes(cell: str, found: list[tuple[int, Locator]]) -> dict[int, str]:
    """Each “…” quote, bound to the nearest page locator before it (the first quote wins)."""
    bound: dict[int, str] = {}
    for m in QUOTE.finditer(cell):
        before = [pos for pos, loc in found if pos < m.start() and loc["page"] is not None]
        if before:
            bound.setdefault(max(before), m[1])
    return bound


def number_pattern(quote: str) -> str:
    """A number as the page may print it: thousands commas only between 3-digit groups; a
    negative also as its bracketed accounting form; a positive never as either."""
    text = quote.strip().replace(",", "").replace("−", "-")
    negative = text.startswith("-")
    whole, _, fraction = text.lstrip("-").partition(".")
    body = ""
    for i, digit in enumerate(whole):
        body += digit + (",?" if i < len(whole) - 1 and (len(whole) - i - 1) % 3 == 0 else "")
    if fraction:
        body += r"\." + fraction
    if negative:
        return rf"(?:[-−]{body}|\({body}\))"
    # A positive may follow a hyphen only as the end of a range ("2023-2024"): a digit before it.
    return rf"(?:(?<![-−(])|(?<=\d-)|(?<=\d−)){body}"


def quote_span(quote: str, text: str) -> tuple[int, int] | None:
    """Where ``quote`` occurs in ``text``; a number matches as ``number_pattern`` says."""
    if NUMBER.fullmatch(quote.strip()):
        found = re.search(rf"(?<!\d)(?<!\d,){number_pattern(quote)}(?!\d)(?!\.\d)", text)
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
    """Source-text files of one run, read once each, with the run's inventory."""

    def __init__(self, run_dir: Path, inv: dict[str, tuple[str, str]]) -> None:
        self.inv = inv
        self.folder = run_dir / "source-text"
        self.cache: dict[str, tuple[dict[int, str], str | None, str | None]] = {}

    def get(self, name: str) -> tuple[dict[int, str], str | None, str | None]:
        """(pages, actual sha256 or None when nothing was read, problem or None)."""
        if name not in self.cache:
            self.cache[name] = self.read(self.folder / name)
        return self.cache[name]

    @staticmethod
    def read(path: Path) -> tuple[dict[int, str], str | None, str | None]:
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            return {}, None, "source text file not found"
        except OSError as error:
            return {}, None, f"source text unreadable: {type(error).__name__}: {error}"
        pages, problem = read_pages(raw)
        return pages, hashlib.sha256(raw).hexdigest(), problem


def is_file_name(name: str) -> bool:
    """An inventory name is a bare file name: it cannot leave source-text/."""
    return bool(name) and not any(part in name for part in ("/", "\\", "\x00")) and ".." not in name


def issuer_chip(loc: Locator, line: int, quote: str | None, pages: Pages) -> dict[str, Any]:
    inv = pages.inv
    entry = inv.get(loc["source"] or "")
    if not inv:
        return chip(as_gap(loc), line, reason="no inventory")
    if entry is None:
        return chip(as_gap(loc), line, reason="key not in inventory")
    file, expected = entry
    if not is_file_name(file):
        return chip(as_gap(loc), line, reason="source name not a file name")
    texts, actual, problem = pages.get(file)
    fields: dict[str, Any] = {
        "file": file,
        "sha256": expected,
        "hash_matches_inventory": None if actual is None else actual == expected,
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


GAP_REASONS = {
    NOT_SUPPLIED: "the cell says Not supplied",
}


def other_chip(loc: Locator, line: int, module: str) -> dict[str, Any]:
    """A chip that needs no source text: upstream codes, or a gap the patterns left open."""
    if loc["kind"] == "upstream":
        # Register codes with no module named belong to the citing module itself.
        return chip(loc, line, module=loc["module"] or module)
    reason = GAP_REASONS.get(loc["label"] or "", "page cited without a source key")
    return chip(loc, line, reason=reason)


class Row(NamedTuple):
    line: int
    cells: list[str]
    headers: list[str]  # empty for a paragraph
    claim: bool


def chips_for_cells(row: Row, module: str, pages: Pages) -> list[dict[str, Any]]:
    """Chips of one row or paragraph. A “…” quote is tested only against the page it follows;
    a numeric cell is tested against every page of the row. A bare page takes the source key the
    row's first cell names. A claim row that cites nothing gets one ``no page`` gap."""
    number = numeric_cell(row.cells, row.headers)
    first = row.cells[0].strip()
    named = first if row.headers and first in pages.inv else None
    result = []
    for index, cell in enumerate(row.cells):
        found = scan(cell, named if index else None)
        quotes = bound_quotes(cell, found)
        for pos, loc in found:
            if loc["kind"] == "issuer_page":
                result.append(issuer_chip(loc, row.line, quotes.get(pos) or number, pages))
            else:
                result.append(other_chip(loc, row.line, module))
    if row.claim and not result:
        result.append(
            chip(
                locator("gap", label=NO_PAGE), row.line, reason="the row cites no page or register"
            )
        )
    return result


def is_claim_table(findings: bool, heading: str, headers: list[str]) -> bool:
    """A claim table: under ## Findings, chart data, or headed Finding or Bottom line."""
    first = headers[0].strip().lower() if headers else ""
    return findings or heading.startswith("Chart data") or first in CLAIM_HEADERS


def chips_for_output(
    run_dir: Path,
    output_id: str,
    module: str,
    sections: list[dict[str, Any]],
    inv: dict[str, tuple[str, str]],
) -> dict[str, list[dict[str, Any]]]:
    """Chips of one handoff, keyed ``<output id>:<line>`` for each row or paragraph with any."""
    pages = Pages(run_dir, inv)
    result: dict[str, list[dict[str, Any]]] = {}
    findings = False
    for section in sections:
        if section["level"] == 2:
            findings = section["heading"].strip().lower().startswith("findings")
        for block in section["blocks"]:
            if block["type"] == "table":
                head = block["headers"]
                claim = is_claim_table(findings, section["heading"], head)
                rows = [Row(r["line"], r["cells"], head, claim) for r in block["rows"]]
            else:
                rows = [Row(block["line"], [block["text"]], [], False)]
            for row in rows:
                if found := chips_for_cells(row, module, pages):
                    result[f"{output_id}:{row.line}"] = found
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
