"""Citation chips for the Credit OS library: what each handoff row or paragraph points at.

Python resolves; the page draws. A citation the patterns below do not match is a gap, never a
guess. Page text comes from the run's ``source-text/<file>`` JSONL (one ``{"page", "text"}``
object per line); the file name and sha256 come from CP-0's inventory or ``## Sources`` table.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Collection, Iterable, Iterator
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, NamedTuple, TypedDict, cast

EXCERPT = 600
NOT_SUPPLIED = "Not supplied"
NO_PAGE = "no page"
NUMBER = re.compile(r"[-−]?\d[\d,]*(?:\.\d+)?")
QUOTE = re.compile(r"“([^”]+)”")
BRACKET = re.compile(r"\[(CP-[0-9A-Z]+):\s*([A-Z]\d{1,2}(?:\s*[,;]\s*[A-Z]\d{1,2})*)\s*\]")
# A page marker: ``page``, ``pages``, ``page:``, ``p.``, ``pp.`` (any case), then the first number
# or range, then (for a plural marker) more after commas. The source key, when the run has any, is
# built from CP-0's inventory in ``key_index``.
MARKER = r"(?<![\w?&=/#.:-])(?P<marker>(?i:pages?|pp?\.))\s*:?\s*"
NUMBERS = (
    r"(?P<a>\d+)(?!\d|\.\d)(?:\s*[-–]\s*(?P<b>\d+)(?!\d|\.\d))?"
    r"(?P<more>(?:\s*,\s*\d+(?!\d|\.\d)(?:\s*[-–]\s*\d+(?!\d|\.\d))?)*)"
)
ITEM = re.compile(r"(\d+)(?:\s*[-–]\s*(\d+))?")
MAX_PAGE_DIGITS = 9  # a longer number is no page (and int() refuses thousands of digits)
# A capitalised word and a comma right before a bare page: a source key the inventory does not hold.
UNKNOWN_KEY = re.compile(r"\b[A-Z]\w*\s*,\s*$")
ALTERNATE = re.compile(r"\balternate\b", re.IGNORECASE)
# Register letters exclude A, B, H and Q, which also open rating grades ("B2"), halves and quarters.
CODE = r"[CD-GI-PR-Z]\d{1,2}"
TRAILING = re.compile(rf"(?:\.\s+|;\s*|(?<=[A-Za-z])\s+)({CODE}(?:\s*[,;]\s*{CODE})*)\.?\s*$")
PERIOD_HEADER = re.compile(r"\b(?:period|year|date)s?\b", re.IGNORECASE)
SENTENCE_END = re.compile(r"[.;]\s")
CLAIM_HEADERS = ("finding", "bottom line")
BASIS = "Basis: "
_SPAN = r"\d+(?:\s*[-–]\s*\d+)?"
BASIS_FILE = re.compile(rf"(?P<file>.+?), (?P<marker>pages?) (?P<pages>{_SPAN}(?:, {_SPAN})*)")
BASIS_MODULE = re.compile(r".+ \((?P<module>CP-[0-9A-Z]+)\)")
BASIS_CALCULATION = re.compile(r"calculation \S+")
# CP-8's two extra items, read only in a CP-8 handoff: the comparison pack (exactly the words) and
# an earlier run's handoff (a plain name, no digits or file names, and a registered module code).
# Neither names a page or a handoff of this run, so there is nothing to open.
BASIS_COMPARISON = "Run comparison"
BASIS_EARLIER_RUN = re.compile(r"[A-Za-z][A-Za-z ,'&/-]* \((?P<code>CP-[0-9A-Z]+)\), earlier run")


class Locator(TypedDict):
    kind: Literal["issuer_page", "upstream", "gap"]
    source: str | None
    page: int | None
    page_end: int | None
    module: str | None
    codes: tuple[str, ...]
    label: str | None
    note: str | None


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
        "note": None,
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
        note=loc["note"],
    )


def split_codes(text: str) -> tuple[str, ...]:
    return tuple(c.strip() for c in re.split(r"[,;]", text) if c.strip())


class Resolved(NamedTuple):
    """The source a written key names: ``source`` is None when the key is ambiguous."""

    source: str | None
    note: str | None
    word: str


class KeyIndex(NamedTuple):
    pattern: re.Pattern[str]
    exact: dict[str, str]  # written key (single spaces) -> inventory key
    prefixes: dict[str, tuple[str, ...]]  # leading words -> the multi-word keys they begin
    alternates: frozenset[str]

    def lookup(self, written: str) -> Resolved | None:
        """What a written key means in this run: an alias in full, or by its leading words."""
        word = " ".join(written.split())
        if word in self.exact:
            return Resolved(self.exact[word], None, word)
        candidates = self.prefixes.get(word, ())
        if not candidates:
            return None
        chosen = [c for c in candidates if c not in self.alternates]
        if len(chosen) != 1:
            left = ", ".join(repr(c) for c in chosen) or "none"
            fits = ", ".join(repr(c) for c in candidates)
            note = f"alias '{word}' fits {fits}; CP-0 roles leave {left}"
            return Resolved(None, note, word)
        skipped = [c for c in candidates if c != chosen[0]]
        note = f"alias '{word}' → '{chosen[0]}'"
        if skipped:
            note += f" ({', '.join(skipped)} marked alternate in CP-0)"
        return Resolved(chosen[0], note, word)


# A listed file name ("report.pdf") is whole: no file-name character, nor a word and a space, may
# precede it, or the citation names a longer unlisted file ("annual-report.pdf", "Draft report.pdf")
# and must not open the listed one. "Source: report.pdf" still reads; "see report.pdf" stays a gap.
FILE_KEY = re.compile(r"\.[A-Za-z0-9]{1,5}$")
# The key's match opens at the start of the whitespace run before it, so that run is read whole
# (a lookbehind is fixed width): the character before the run may not be a file-name character.
FILE_START = r"(?<![\w.\-/\s])\s*"


@lru_cache(maxsize=32)
def key_index(keys: tuple[str, ...], alternates: frozenset[str] = frozenset()) -> KeyIndex:
    """The page-citation pattern for one run: keys are the inventory's, longest first, exact. A key
    that ends in an extension (``FILE_KEY``), whichever inventory section it came from, takes the
    strict start of ``FILE_START`` and registers no word-prefix alias; any other key keeps both."""
    exact: dict[str, str] = {}
    prefixes: dict[str, list[str]] = {}
    for key in keys:
        words = key.split()
        if not words:
            continue
        exact[" ".join(words)] = key
        if FILE_KEY.search(key):
            continue
        for n in range(1, len(words)):
            prefixes.setdefault(" ".join(words[:n]), []).append(key)
    phrases = sorted({*exact, *prefixes}, key=len, reverse=True)
    strict = {p for p in exact if FILE_KEY.search(p)} - set(prefixes)
    spaced = [
        (FILE_START if p in strict else "") + r"\s+".join(re.escape(w) for w in p.split())
        for p in phrases
    ]
    keyed = rf"(?:(?<!\w)(?P<key>{'|'.join(spaced)})(?:\s*,\s*|\s+))?" if spaced else ""
    pattern = re.compile(keyed + MARKER + NUMBERS)
    return KeyIndex(pattern, exact, {k: tuple(v) for k, v in prefixes.items()}, alternates)


def page_locators(match: re.Match[str], key: Resolved | None) -> list[Locator]:
    """One locator per page or range the citation lists; a plural marker may list several."""
    items = [(match["a"], match["b"])]
    if match["marker"].lower() in ("pages", "pp."):
        items += ITEM.findall(match["more"])
    result = []
    for first_text, last_text in items:
        if max(len(first_text), len(last_text or "")) > MAX_PAGE_DIGITS:
            label = f"p.{first_text[:12]}… · not a page number"
            result.append(locator("gap", label=label, note="the cited number is not a page"))
            continue
        first, last = int(first_text), int(last_text) if last_text else None
        if key is None:
            loc = locator(
                "gap", page=first, page_end=last, label=f"p.{span_text(first, last)} · no key"
            )
        elif key.source is None:
            label = f"{key.word} p.{span_text(first, last)} · ambiguous"
            loc = locator("gap", page=first, page_end=last, label=label, note=key.note)
        else:
            loc = locator(
                "issuer_page", source=key.source, page=first, page_end=last, note=key.note
            )
        result.append(loc)
    return result


def _cp8_item(item: str) -> bool:
    """CP-8's own Basis items: `Run comparison`, or `<plain module name> (<code>), earlier run`
    with a code the registry knows."""
    from deploy_vii.registry import modules

    found = BASIS_EARLIER_RUN.fullmatch(item)
    return item == BASIS_COMPARISON or (
        found is not None and found["code"] in {m.module_id for m in modules()}
    )


def basis_pages(marker: str, text: str) -> list[tuple[str, str | None]] | None:
    """The (first, last) page texts of a Basis page list; None when a number is no page or a
    singular marker lists more than one page."""
    spans = ITEM.findall(text)
    if marker == "page" and len(spans) > 1:
        return None
    if any(max(len(a), len(b)) > MAX_PAGE_DIGITS for a, b in spans):
        return None
    return [(a, b or None) for a, b in spans]


def basis_file_locators(
    file: str, spans: list[tuple[str, str | None]], files: dict[str, str | None]
) -> list[Locator]:
    """One locator per listed page or range of one Basis file."""
    result: list[Locator] = []
    for a, b in spans:
        first, last = int(a), int(b) if b else None
        span = span_text(first, last)
        if file not in files:
            label = f"{file} p.{span} · not in inventory"
            note = "the Basis file is not in the CP-0 inventory"
            result.append(locator("gap", page=first, page_end=last, label=label, note=note))
        elif (key := files[file]) is None:
            label = f"{file} p.{span} · ambiguous"
            note = "two inventory keys hold this file with different hashes"
            result.append(locator("gap", page=first, page_end=last, label=label, note=note))
        else:
            result.append(locator("issuer_page", source=key, page=first, page_end=last))
    return result


def basis_locators(
    line: str, files: dict[str, str | None], writer: str | None = None
) -> list[Locator]:
    """The locators of one ``Basis: `` line (H3): items split on ``; `` and read by their form.
    ``files`` maps an inventory file name to its key, or None when two keys hold different bytes.
    ``writer`` is the module whose handoff holds the line; only CP-8 may write the two items
    `_cp8_item` reads."""
    result: list[Locator] = []
    for item in (i.strip() for i in line.removeprefix(BASIS).removesuffix(".").split("; ")):
        if BASIS_CALCULATION.fullmatch(item):
            continue  # the library reads calculations from ## Calculations
        if writer == "CP-8" and _cp8_item(item):
            continue  # the comparison pack or an earlier run's handoff: nothing to quote
        if module := BASIS_MODULE.fullmatch(item):
            result.append(locator("upstream", module=module["module"]))
        elif item in files:
            continue  # a file with no page: nothing to quote
        elif (m := BASIS_FILE.fullmatch(item)) and (spans := basis_pages(m["marker"], m["pages"])):
            result.extend(basis_file_locators(m["file"], spans, files))
        else:
            result.append(locator("gap", label="Basis item not recognised", note=item))
    return result


def scan(
    text: str,
    index: KeyIndex | None = None,
    row_key: Resolved | None = None,
    files: dict[str, str | None] | None = None,
    module: str | None = None,
) -> list[tuple[int, Locator]]:
    """Every citation in ``text`` with its position; what no pattern matches is not guessed.
    ``row_key`` is the source key the row itself names, for a page with no key of its own.
    With ``files`` (file name -> key), a last line starting ``Basis: `` is read by its own forms
    and the patterns see only the text before it."""
    found: list[tuple[int, Locator]] = []
    head, _, last_line = text.rpartition("\n")
    last_line = last_line.strip()
    if files is not None and last_line.startswith(BASIS):
        at = len(head) + 1
        found = [(at, loc) for loc in basis_locators(last_line, files, module)]
        text = head
    for m in BRACKET.finditer(text):
        found.append((m.start(), locator("upstream", module=m[1], codes=split_codes(m[2]))))
    last_key: Resolved | None = None
    previous = 0
    for m in (index or key_index(())).pattern.finditer(text):
        spelled = m.groupdict().get("key")
        written = index.lookup(spelled) if index and spelled else None
        # A strict key's match opens at the whitespace before it: the citation starts at the key.
        begin = m.start() + len(spelled) - len(spelled.lstrip()) if spelled else m.start()
        if SENTENCE_END.search(text, previous, begin):
            last_key = None
        last_key = written or last_key
        previous = m.end()
        # A bare page after an unknown capitalised key ("X, page:3") is a gap, not the last key's.
        stray = written is None and UNKNOWN_KEY.search(text, 0, begin)
        key = written or (None if stray else last_key or row_key)
        found.extend((begin, loc) for loc in page_locators(m, key))
    if (at := text.find(NOT_SUPPLIED)) >= 0:
        found.append((at, locator("gap", label=NOT_SUPPLIED)))
    if (tail := TRAILING.search(text)) and not BRACKET.search(text[tail.start(1) :]):
        found.append((tail.start(1), locator("upstream", codes=split_codes(tail[1]))))
    return sorted(found, key=lambda pair: pair[0])


def parse_locators(
    text: str, keys: Iterable[str] = (), alternates: Iterable[str] = ()
) -> list[Locator]:
    """Every citation in ``text``, in reading order. ``keys`` are the run's inventory keys and
    ``alternates`` those its CP-0 roles mark alternate; without keys no page names a source."""
    index = key_index(tuple(keys), frozenset(alternates))
    return [loc for _, loc in scan(text, index)]


def inventory_tables(
    cp0_sections: list[dict[str, Any]],
) -> Iterator[tuple[list[str], list[list[str]], int]]:
    """(headers, rows' cells, index of the sha256 column) of every inventory table: a section
    headed "...inventory..." holding a table of three or more columns with a sha256 column."""
    for section in cp0_sections:
        if "inventory" not in section["heading"].lower():
            continue
        for block in section["blocks"]:
            if block["type"] != "table":
                continue
            hashes = [i for i, h in enumerate(block["headers"]) if "sha256" in h.lower()]
            if len(block["headers"]) >= 3 and hashes:
                yield block["headers"], [r["cells"] for r in block["rows"]], hashes[0]


class Inventory(dict[str, tuple[str, str]]):
    """key -> (file, sha256), with the keys CP-0's roles mark alternate."""

    alternates: frozenset[str] = frozenset()


def sources_rows(cp0_sections: list[dict[str, Any]]) -> Iterator[tuple[str, str]]:
    """(file, sha256 or "") of every row of a ``## Sources`` table: the file is the first cell and
    the hash the column headed sha256, when the table has one."""
    for section in cp0_sections:
        if section["heading"].strip().lower() != "sources":
            continue
        for block in section["blocks"]:
            if block["type"] != "table":
                continue
            hashes = [i for i, h in enumerate(block["headers"]) if h.strip().lower() == "sha256"]
            for row in block["rows"]:
                cells = row["cells"]
                if cells and cells[0].strip():
                    yield cells[0].strip(), cells[hashes[0]].strip() if hashes else ""


def inventory(
    cp0_sections: list[dict[str, Any]], available: Collection[str] | None = None
) -> Inventory:
    """key -> (file, sha256). An inventory table gives its key in column 0 and its file name in
    column 1; ``alternates`` are the keys whose role marks them alternate. A ``## Sources`` row
    adds its file as its own key (no hash when the table has no sha256 column) unless an
    inventory key already names the file; with ``available`` (the run's source-text files) a row
    naming any other file, such as the run settings, is left out rather than guessed."""
    result = Inventory()
    result.alternates = inventory_alternates(cp0_sections)
    for _, rows, sha_column in inventory_tables(cp0_sections):
        for cells in rows:
            result[cells[0]] = (cells[1], cells[sha_column])
    named = {file for file, _ in result.values()}
    for file, sha in sources_rows(cp0_sections):
        if file not in named and file not in result and (available is None or file in available):
            result[file] = (file, sha)
    return result


def inventory_alternates(cp0_sections: list[dict[str, Any]]) -> frozenset[str]:
    """The keys whose "Role" cell (the column headed with "role") marks them alternate; runs
    whose inventory has no such column have none."""
    result: set[str] = set()
    for headers, rows, _ in inventory_tables(cp0_sections):
        roles = [i for i, h in enumerate(headers) if re.search("role", h, re.IGNORECASE)]
        for cells in rows if roles else []:
            if roles[0] < len(cells) and ALTERNATE.search(cells[roles[0]]):
                result.add(cells[0])
    return frozenset(result)


def read_pages(raw: bytes) -> tuple[dict[int, str], str | None]:
    """The page texts of one source-text file, or the reason it could not be read."""
    pages: dict[int, str] = {}
    try:
        for line in raw.decode("utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                pages[int(record["page"])] = str(record["text"])
    except (ValueError, KeyError, TypeError, OverflowError) as error:
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


def excerpt_start(span: tuple[int, int] | None) -> int:
    return 0 if span is None else max(0, span[0] - (EXCERPT - (span[1] - span[0])) // 2)


def excerpt_around(text: str, span: tuple[int, int] | None) -> str:
    start = excerpt_start(span)
    return text[start : start + EXCERPT]


def match_in_excerpt(text: str, span: tuple[int, int] | None) -> tuple[str | None, int | None]:
    """The page text the quote matched, as printed, and where it sits in ``excerpt_around``."""
    if span is None:
        return None, None
    start = excerpt_start(span)
    first, last = max(span[0], start), min(span[1], start + EXCERPT, len(text))
    return (text[first:last], first - start) if first < last else (None, None)


def avatar(key: str) -> str:
    """What the 18px chip avatar prints: the key, or the initials of a multi-word key."""
    words = key.split()
    return "".join(w[0].upper() for w in words) if len(words) > 1 else key


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
        "avatar": None,
        "match": None,
        "match_at": None,
    }
    base.update(fields)
    return base


class Pages:
    """Source-text files of one run, read once each, with the run's inventory."""

    def __init__(self, run_dir: Path, inv: dict[str, tuple[str, str]]) -> None:
        self.inv = inv
        self.files: dict[str, str | None] = {}
        for key, (file, sha) in inv.items():
            kept = self.files.setdefault(file, key)
            if kept is not None and inv[kept][1] != sha:
                self.files[file] = None
        self.index = key_index(tuple(inv), getattr(inv, "alternates", frozenset()))
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
    """An inventory name is a bare file name: it cannot leave source-text/ (no separator, no drive
    prefix such as C:x, which replaces the folder on Windows)."""
    forbidden = ("/", "\\", "\x00", ":", "..")
    return bool(name) and not any(part in name for part in forbidden)


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
        "sha256": expected or None,
        "hash_matches_inventory": None if actual is None or not expected else actual == expected,
        "quote": quote,
        "reason": problem,
        "avatar": avatar(loc["source"] or ""),
    }
    first = loc["page"] or 0
    last = loc["page_end"] or first
    # From the pages the source has: the cited range is model output and can be any size.
    here = sorted((n, text) for n, text in texts.items() if first <= n <= last)
    if problem is None and not here:
        fields["reason"] = "page not in source text"
    fields["reason"] = "; ".join(r for r in (fields["reason"], loc["note"]) if r) or None
    span, shown = None, here[0] if here else None
    for number, text in here:
        if quote and (span := quote_span(quote, text)):
            shown = (number, text)
            break
    fields["quote_found"] = (span is not None) if quote and here else None
    if shown:
        fields["excerpt"] = excerpt_around(shown[1], span)
        fields["match"], fields["match_at"] = match_in_excerpt(shown[1], span)
    return chip(loc, line, **fields)


GAP_REASONS = {
    NOT_SUPPLIED: "the cell says Not supplied",
}


def other_chip(loc: Locator, line: int, module: str, has_inventory: bool) -> dict[str, Any]:
    """A chip that needs no source text: upstream codes, or a gap the patterns left open."""
    if loc["kind"] == "upstream":
        # Register codes with no module named belong to the citing module itself.
        return chip(loc, line, module=loc["module"] or module)
    unkeyed = "page cited without a source key" if has_inventory else "no inventory"
    reason = loc["note"] or GAP_REASONS.get(loc["label"] or "", unkeyed)
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
    named = pages.index.lookup(first) if row.headers else None
    result = []
    for index, cell in enumerate(row.cells):
        found = scan(cell, pages.index, named if index else None, pages.files, module)
        quotes = bound_quotes(cell, found)
        for pos, loc in found:
            if loc["kind"] == "issuer_page":
                result.append(issuer_chip(loc, row.line, quotes.get(pos) or number, pages))
            else:
                result.append(other_chip(loc, row.line, module, bool(pages.inv)))
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
            texts = workspace / "runs" / folder / "source-text"
            available = {p.name for p in texts.iterdir()} if texts.is_dir() else set()
            by_run[folder] = inventory(parsed.get(record["sha256"]) or [], available)
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
