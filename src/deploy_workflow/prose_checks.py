"""Mechanical prose checks (H6) for a handoff's reader passages.

Pure module: no I/O. The specification is `docs/rulings/2026-11-11-reader-and-issuer-report.md`
(H1, H2, H3, H6); where this file and the ruling differ, the ruling wins.

Reader passages are the bodies of the four H3 sections of `## Findings`. Checks 2-6 and 8 read
only "sentence text": a passage without headings, Basis lines, table rows, fenced code and HTML
comments, list markers removed. Decisions where the ruling is silent:

- A section body ends at the next `#`, `##` or `###` heading outside a fence; `####` stays inside.
- A repeated passage heading is not an error here (presence is not gated beyond check 1); the
  bodies of repeats are pooled so that nothing escapes the checks.
- Check 6 reads a whole cell as one ID (surrounding backticks and asterisks removed) and matches it
  as a whole token: it may not touch a letter, digit, underscore or hyphen.
- Check 7 normalises by dropping every character that is not a word character or whitespace
  (so `year-on-year` becomes `yearonyear`), after lower-casing, and collapsing whitespace. An item
  is a list item or a paragraph; its Basis line is dropped.
- Check 8 treats a minus sign or parentheses as not part of the figure (`-5`, `(1,250)` and `5`,
  `1,250` are judged alike; a currency code or symbol before the opening parenthesis or sign
  still counts as preceding). Only an active ISO 4217 alphabetic code before a space counts as a
  currency code (`FCF` and `LTM` do not). A figure touching a letter is not re-judged as its
  trailing digit group (`USD1,250` is not `250`).
  Unit words are matched case-insensitively, the single-letter scale units `k` and `m` only in
  lower case (`9M` is a period label, not a figure). A unit directly after the digits (`3.1x`,
  `61bp`, `5bn`) counts; any other letter touching the digits (`3rd`, `FY2024`) makes it a
  non-figure, as does a hyphen-joined letter either side (`10-K`, `B-1`, `12-month`).
- Comments are removed before fences and headings are recognised, so a marker inside a multi-line
  comment toggles nothing. A `Basis: ` line is exempt only as the last line of its paragraph or
  item (next line blank, a heading, a list item or a fence, or none); otherwise it is sentence text.
- Blocked and data modules owe only `### Bottom line`; this module never demands the other three
  headings. `DATA_MODULES` names the data modules for callers.
"""

import re
from collections.abc import Mapping
from itertools import groupby
from typing import NamedTuple

DATA_MODULES = frozenset({"CP-0", "CP-PARSE", "CP-1", "CP-1C"})
READER_HEADINGS = (
    "Bottom line",
    "Key findings",
    "Contrary evidence and what would change the view",
    "Limitations",
)

FENCE = "```"
HEADING = re.compile(r"(#{1,6}) +(.*?)\s*")
LIST_MARKER = re.compile(r"\s*(?:[-*]|\d+\.)\s+")
BASIS = "Basis: "
PROSE_OPENERS = "\"“‘'"


class _Section(NamedTuple):
    title: str
    line: int
    body: list[tuple[int, str]]


class _Line(NamedTuple):
    number: int
    text: str
    bullet: bool


class _Visible(NamedTuple):
    number: int
    raw: str
    text: str  # the line without HTML comments
    skipped: bool  # a fence marker or a line inside a fence


def _visible(lines: list[tuple[int, str]]) -> list[_Visible]:
    """Strip HTML comments outside fences, then mark fence markers and fenced lines."""
    out: list[_Visible] = []
    fenced = in_comment = False
    for number, raw in lines:
        text = raw
        if not fenced:
            text, in_comment = _strip_comments(raw, in_comment)
        marker = text.lstrip().startswith(FENCE)
        if marker:
            fenced = not fenced
        out.append(_Visible(number, raw, text, marker or fenced))
    return out


def _findings_sections(text: str) -> list[_Section] | None:
    """Every H3 section under `## Findings`; None when there is no such H2."""
    sections: list[_Section] = []
    found = in_findings = False
    current: _Section | None = None
    for line in _visible(list(enumerate(text.splitlines(), 1))):
        heading = None if line.skipped else HEADING.fullmatch(line.text)
        if heading is not None and len(heading[1]) <= 3:
            current = None
            if len(heading[1]) <= 2:
                in_findings = len(heading[1]) == 2 and heading[2] == "Findings"
                found = found or in_findings
            elif in_findings:
                current = _Section(heading[2], line.number, [])
                sections.append(current)
            continue
        if current is not None:
            current.body.append((line.number, line.raw))
    return sections if found else None


def _pooled(sections: list[_Section]) -> dict[str, list[tuple[int, str]]]:
    passages: dict[str, list[tuple[int, str]]] = {}
    for section in sections:
        if section.title in READER_HEADINGS:
            passages.setdefault(section.title, []).extend(section.body)
    return passages


def reader_passages(text: str) -> dict[str, list[tuple[int, str]]]:
    """The bodies of the four reader H3 sections under `## Findings`, as (line number, line)."""
    return _pooled(_findings_sections(text) or [])


def _strip_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    kept: list[str] = []
    rest = line
    while rest:
        if in_comment:
            end = rest.find("-->")
            if end < 0:
                return "".join(kept), True
            rest, in_comment = rest[end + 3 :], False
        else:
            start = rest.find("<!--")
            if start < 0:
                kept.append(rest)
                break
            kept.append(rest[:start])
            rest, in_comment = rest[start + 4 :], True
    return "".join(kept), in_comment


def _ends_paragraph(following: list[_Visible]) -> bool:
    """True when nothing after a line continues its paragraph or list item."""
    for line in following:
        if line.skipped:
            return True
        if line.text.strip():
            return bool(HEADING.fullmatch(line.text) or LIST_MARKER.match(line.text))
        if not line.raw.strip():
            return True
    return True


def _sentence_lines(body: list[tuple[int, str]]) -> list[_Line]:
    """Sentence text of a passage; blank lines stay (as empty text) to mark paragraph breaks."""
    out: list[_Line] = []
    lines = _visible(body)
    for index, visible in enumerate(lines):
        line = visible.text
        if visible.skipped:
            continue
        stripped = line.strip()
        is_basis = stripped.startswith(BASIS) and _ends_paragraph(lines[index + 1 :])
        if is_basis or stripped.startswith("|") or HEADING.fullmatch(line):
            continue
        marker = LIST_MARKER.match(line)
        out.append(
            _Line(visible.number, line[marker.end() :] if marker else stripped, marker is not None)
        )
    return out


def _limitation_entries(text: str) -> list[tuple[int, str]]:
    """(first line number, normalised text) of every item of `### Limitations`."""
    items: list[tuple[int, list[str]]] = []
    open_item = False
    for line in _sentence_lines(reader_passages(text).get("Limitations", [])):
        if not line.text.strip():
            open_item = False
        elif line.bullet or not open_item:
            items.append((line.number, [line.text]))
            open_item = True
        else:
            items[-1][1].append(line.text)
    normalised = ((number, _normalise(" ".join(parts))) for number, parts in items)
    return [(number, item) for number, item in normalised if item]


def _normalise(item: str) -> str:
    return " ".join(re.sub(r"[^\w\s]|_", "", item.lower()).split())


def limitation_items(text: str) -> tuple[str, ...]:
    """Normalised items of `### Limitations` (lower case, no Basis line, no punctuation)."""
    return tuple(item for _, item in _limitation_entries(text))


def _issue(check: int, name: str, line: int, offending: str, advice: str) -> str:
    return f'Prose check {check} ({name}), line {line}: "{offending}" — {advice}'


def _check_bottom_line(sections: list[_Section] | None) -> list[str]:
    name = "bottom line present"
    if sections is None:
        return [
            _issue(
                1,
                name,
                1,
                "no `## Findings` section",
                "add `## Findings` starting with `### Bottom line`.",
            )
        ]
    if not sections or sections[0].title != "Bottom line":
        first = sections[0] if sections else None
        return [
            _issue(
                1,
                name,
                first.line if first else 1,
                f"### {first.title}" if first else "no H3 section",
                "make `### Bottom line` the first H3 under `## Findings`.",
            )
        ]
    first_line = next(((n, t.strip()) for n, t in sections[0].body if t.strip()), None)
    if first_line is None:
        return [
            _issue(
                1,
                name,
                sections[0].line,
                "### Bottom line",
                "write the bottom line as prose under it.",
            )
        ]
    number, stripped = first_line
    if stripped[0].isalpha() or stripped[0] in PROSE_OPENERS or stripped.startswith("**"):
        return []
    return [
        _issue(
            1,
            name,
            number,
            stripped[:60],
            "start the bottom line with a prose sentence, not a table, list, fence or comment.",
        )
    ]


SIMPLE_CHECKS = (
    (
        2,
        "no module code",
        re.compile(r"\bCP-[A-Z0-9]+\b"),
        "move it to the paragraph's Basis line.",
    ),
    (
        3,
        "no page locator",
        re.compile(r"\bpp?\.\s*\d|\bpages?\s+\d|\bpg\.?\s*\d", re.IGNORECASE),
        "name the document in words and move the page to the paragraph's Basis line.",
    ),
    (
        4,
        "no bracket citation or chip",
        re.compile(r".{0,20}[\[\]【】].{0,20}"),
        "remove the brackets; put the source in the paragraph's Basis line.",
    ),
    (
        5,
        "no hash",
        re.compile(r"\b[0-9a-fA-F]{12,}\b|sha256", re.IGNORECASE),
        "remove the hash from the sentence; hashes belong in the run record or a Basis line.",
    ),
)


def _check_simple(lines: list[_Line]) -> list[str]:
    return [
        _issue(number, name, line.number, found[0].strip(), advice)
        for number, name, pattern, advice in SIMPLE_CHECKS
        for line in lines
        for found in pattern.finditer(line.text)
    ]


def _cells(row: str) -> list[str]:
    inner = row.strip()[1:]
    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
    return [c.strip().strip("`* ") for c in re.split(r"(?<!\\)\|", inner)]


def _tables(text: str) -> list[list[list[str]]]:
    """Pipe tables outside fences, each as rows of cells."""
    rows: list[str | None] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(FENCE):
            fenced = not fenced
            rows.append(None)
            continue
        is_row = not fenced and line.lstrip().startswith("|")
        rows.append(line if is_row else None)
    return [
        [_cells(row) for row in run if row is not None]
        for is_row, chunk in groupby(rows, key=lambda item: item is not None)
        if is_row
        for run in [list(chunk)]
    ]


def _has_letter_and_digit(value: str) -> bool:
    return any(c.isalpha() for c in value) and any(c.isdigit() for c in value)


def _is_id_header(header: str) -> bool:
    folded = header.casefold()
    return folded == "id" or folded.endswith(" id")


def _register_ids(text: str) -> set[str]:
    ids: set[str] = set()
    for rows in _tables(text):
        if len(rows) < 3 or not all(re.fullmatch(r":?-+:?", c) for c in rows[1]):
            continue
        id_columns = [i for i, h in enumerate(rows[0]) if _is_id_header(h)]
        for row in rows[2:]:
            ids.update(row[i] for i in id_columns if i < len(row) and _has_letter_and_digit(row[i]))
    return ids


def _check_register_ids(text: str, lines: list[_Line]) -> list[str]:
    patterns = [
        (found, re.compile(rf"(?<![\w-]){re.escape(found)}(?![\w-])"))
        for found in sorted(_register_ids(text))
    ]
    return [
        _issue(
            6,
            "no register ID",
            line.number,
            found,
            "move it to the paragraph's Basis line (`calculation <id>`) or describe it in words.",
        )
        for line in lines
        for found, pattern in patterns
        if pattern.search(line.text)
    ]


def _check_limitation_repeats(text: str, accepted: Mapping[str, str]) -> list[str]:
    seen = {item for earlier in accepted.values() for item in limitation_items(earlier)}
    issues = []
    for number, item in _limitation_entries(text):
        if item in seen:
            issues.append(
                _issue(
                    7,
                    "no limitation repeated within the run",
                    number,
                    item[:60],
                    "state each limitation once in the run; delete this or move it to `## Gaps`.",
                )
            )
        seen.add(item)
    return issues


_MONTH = (
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December"
    r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)"
)
_ORDINAL = r"(?:st|nd|rd|th)?"
DATE = re.compile(
    rf"\b\d{{4}}-\d{{2}}-\d{{2}}\b"
    rf"|\b{_MONTH}\.?\s+(?:\d{{1,2}}{_ORDINAL},?\s+)?\d{{4}}\b"
    rf"|\b{_MONTH}\.?\s+\d{{1,2}}{_ORDINAL}\b"
    rf"|\b\d{{1,2}}{_ORDINAL}\s+{_MONTH}\b(?:,?\s+\d{{4}}\b)?"
)
# ISO 4217 alphabetic codes in the active list (current amendment; withdrawn codes such as HRK,
# BGN, SLL and ZWL are excluded; fund and metal codes are included).
ISO_4217 = frozenset(
    {
        "AED",
        "AFN",
        "ALL",
        "AMD",
        "ANG",
        "AOA",
        "ARS",
        "AUD",
        "AWG",
        "AZN",
        "BAM",
        "BBD",
        "BDT",
        "BHD",
        "BIF",
        "BMD",
        "BND",
        "BOB",
        "BOV",
        "BRL",
        "BSD",
        "BTN",
        "BWP",
        "BYN",
        "BZD",
        "CAD",
        "CDF",
        "CHE",
        "CHF",
        "CHW",
        "CLF",
        "CLP",
        "CNY",
        "COP",
        "COU",
        "CRC",
        "CUP",
        "CVE",
        "CZK",
        "DJF",
        "DKK",
        "DOP",
        "DZD",
        "EGP",
        "ERN",
        "ETB",
        "EUR",
        "FJD",
        "FKP",
        "GBP",
        "GEL",
        "GHS",
        "GIP",
        "GMD",
        "GNF",
        "GTQ",
        "GYD",
        "HKD",
        "HNL",
        "HTG",
        "HUF",
        "IDR",
        "ILS",
        "INR",
        "IQD",
        "IRR",
        "ISK",
        "JMD",
        "JOD",
        "JPY",
        "KES",
        "KGS",
        "KHR",
        "KMF",
        "KPW",
        "KRW",
        "KWD",
        "KYD",
        "KZT",
        "LAK",
        "LBP",
        "LKR",
        "LRD",
        "LSL",
        "LYD",
        "MAD",
        "MDL",
        "MGA",
        "MKD",
        "MMK",
        "MNT",
        "MOP",
        "MRU",
        "MUR",
        "MVR",
        "MWK",
        "MXN",
        "MXV",
        "MYR",
        "MZN",
        "NAD",
        "NGN",
        "NIO",
        "NOK",
        "NPR",
        "NZD",
        "OMR",
        "PAB",
        "PEN",
        "PGK",
        "PHP",
        "PKR",
        "PLN",
        "PYG",
        "QAR",
        "RON",
        "RSD",
        "RUB",
        "RWF",
        "SAR",
        "SBD",
        "SCR",
        "SDG",
        "SEK",
        "SGD",
        "SHP",
        "SLE",
        "SOS",
        "SRD",
        "SSP",
        "STN",
        "SVC",
        "SYP",
        "SZL",
        "THB",
        "TJS",
        "TMT",
        "TND",
        "TOP",
        "TRY",
        "TTD",
        "TWD",
        "TZS",
        "UAH",
        "UGX",
        "USD",
        "USN",
        "UYI",
        "UYU",
        "UYW",
        "UZS",
        "VED",
        "VES",
        "VND",
        "VUV",
        "WST",
        "XAF",
        "XAG",
        "XAU",
        "XBA",
        "XBB",
        "XBC",
        "XBD",
        "XCD",
        "XCG",
        "XDR",
        "XOF",
        "XPD",
        "XPF",
        "XPT",
        "XSU",
        "XUA",
        "YER",
        "ZAR",
        "ZMW",
        "ZWG",
    }
)
FIGURE = re.compile(
    r"(?<!\w)(?<!\d[,.])(?<![A-Za-z]-)(?P<int>\d{1,3}(?:,\d{3})+|\d+)(?P<dec>\.\d+)?(?!\d|-[A-Za-z])"
)
_UNITS = (
    r"basis points|percentage points|bps|bp|pp|times|notches|notch|days|day|weeks|week"
    r"|months|month|quarters|quarter|years|year|x"
)
AFTER = re.compile(
    rf"\s?(?:(?P<scale>(?i:thousand|million|billion|trillion|bn)|[km])(?![A-Za-z])"
    rf"|(?P<unit>%|(?i:{_UNITS})(?![A-Za-z])))"
)
CURRENCY_BEFORE = re.compile(r"(?:(?<![A-Za-z])(?P<code>[A-Z]{3})\s+|[$€£¥]\s?)\Z")
FIGURE_ADVICE = {
    "decimals": "round to at most two decimals.",
    "scale": "put a currency (`USD` or a symbol) before a scaled amount, or reword a count.",
    "unit": (
        "a number with no unit does not belong in a reader sentence: reword it in words or move "
        "it to a table, or add a unit or currency if it is an amount or ratio (for example "
        "`USD 1,250 million`, `45%`, `3.1x`, `18 months`)."
    ),
}


def _figure_problem(masked: str, found: re.Match[str]) -> tuple[str, str] | None:
    """(reason key, quoted text) if the figure breaks check 8; None if it passes or is no figure."""
    tail = masked[found.end() :]
    after = AFTER.match(tail)
    if tail[:1].isalpha() and after is None:
        return None
    quoted = masked[found.start() : found.end() + (after.end() if after else 0)]
    if found["dec"] and len(found["dec"]) > 3:
        return "decimals", quoted
    before = CURRENCY_BEFORE.search(masked[: found.start()].rstrip("(-−–+"))
    currency = before is not None and (before["code"] is None or before["code"] in ISO_4217)
    if after is not None and after["scale"]:
        return None if currency else ("scale", quoted)
    if after is not None or currency:
        return None
    whole = found["dec"] is None and "," not in found["int"]
    if whole and (
        int(found["int"]) < 100 or (len(found["int"]) == 4 and 1900 <= int(found["int"]) <= 2099)
    ):
        return None
    return "unit", quoted


def _check_figures(lines: list[_Line]) -> list[str]:
    name = "figures carry a unit or currency, at most two decimals"
    issues = []
    for line in lines:
        masked = DATE.sub(lambda m: " " * len(m[0]), line.text)
        for found in FIGURE.finditer(masked):
            problem = _figure_problem(masked, found)
            if problem is not None:
                reason, quoted = problem
                issues.append(
                    _issue(
                        8,
                        name,
                        line.number,
                        line.text[found.start() : found.start() + len(quoted)],
                        FIGURE_ADVICE[reason],
                    )
                )
    return issues


def prose_issues(text: str, accepted: Mapping[str, str] = {}) -> tuple[str, ...]:
    """Every H6 failure in this handoff; `accepted` (module -> Markdown) feeds check 7 only."""
    sections = _findings_sections(text)
    lines = [
        line
        for body in _pooled(sections or []).values()
        for line in _sentence_lines(body)
        if line.text.strip()
    ]
    lines.sort(key=lambda line: line.number)
    return tuple(
        _check_bottom_line(sections)
        + _check_simple(lines)
        + _check_register_ids(text, lines)
        + _check_limitation_repeats(text, accepted)
        + _check_figures(lines)
    )
