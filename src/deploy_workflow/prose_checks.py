"""Mechanical prose checks (H6) for a handoff's reader passages and, for checks 2-5 and 10, the
sentence text of every shown section (`## Findings`, `## Calculations`, `## Gaps`).

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
  item (next line blank, a heading, a list item or a fence, or none) with no blank line before it;
  otherwise it is sentence text.
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
    section: str = ""  # the heading of the section the line is in, for the issue text


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


def _sections(text: str, h2_titles: tuple[str, ...], lead_in: bool) -> tuple[list[_Section], bool]:
    """Every H3 section under the H2s named, and whether `## Findings` was seen. With `lead_in`
    the text between an H2 and its first H3 is a section too, titled as the H2."""
    sections: list[_Section] = []
    found = inside = False
    current: _Section | None = None
    for line in _visible(list(enumerate(text.splitlines(), 1))):
        heading = None if line.skipped else HEADING.fullmatch(line.text)
        if heading is not None and len(heading[1]) <= 3:
            current = None
            if len(heading[1]) <= 2:
                inside = len(heading[1]) == 2 and heading[2] in h2_titles
                found = found or (inside and heading[2] == "Findings")
                if inside and lead_in:
                    current = _Section(heading[2], line.number, [])
                    sections.append(current)
            elif inside:
                current = _Section(heading[2], line.number, [])
                sections.append(current)
            continue
        if current is not None:
            current.body.append((line.number, line.raw))
    return sections, found


def _findings_sections(text: str) -> list[_Section] | None:
    """Every H3 section under `## Findings`; None when there is no such H2."""
    sections, found = _sections(text, ("Findings",), lead_in=False)
    return sections if found else None


# Sections whose body is data for a drawing, a calendar or a calculation, not sentence text.
DATA_SECTION_PREFIXES = ("chart data:", "map:", "events:", "forecast inputs", "confidence inputs")


def _shown_sentence_lines(text: str) -> list[_Line]:
    """Sentence text of everything the Modules page shows as prose: every section under
    `## Findings`, `## Calculations` and `## Gaps` except the data sections."""
    sections, _ = _sections(text, ("Findings", "Calculations", "Gaps"), lead_in=True)
    return [
        line._replace(section=section.title)
        for section in sections
        if not section.title.casefold().startswith(DATA_SECTION_PREFIXES)
        for line in _sentence_lines(section.body)
        if line.text.strip()
    ]


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
        joined = index > 0 and bool(lines[index - 1].raw.strip())  # No blank line before it.
        is_basis = stripped.startswith(BASIS) and joined and _ends_paragraph(lines[index + 1 :])
        if is_basis or stripped.startswith("|") or HEADING.fullmatch(line):
            continue
        marker = LIST_MARKER.match(line)
        out.append(
            _Line(visible.number, line[marker.end() :] if marker else stripped, marker is not None)
        )
    return out


def _limitation_items(text: str) -> list[tuple[int, str]]:
    """(first line number, text) of every item of `### Limitations`, its Basis line dropped."""
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
    return [(number, " ".join(parts)) for number, parts in items]


def _limitation_entries(text: str) -> list[tuple[int, str]]:
    """(first line number, normalised text) of every item of `### Limitations`."""
    normalised = ((number, _normalise(item)) for number, item in _limitation_items(text))
    return [(number, item) for number, item in normalised if item]


def _normalise(item: str) -> str:
    return " ".join(re.sub(r"[^\w\s]|_", "", item.lower()).split())


def normalise_limitation(item: str) -> str:
    """The key by which two limitation lines are the same limitation (check 7's normalisation)."""
    return _normalise(item)


def limitation_texts(text: str) -> tuple[str, ...]:
    """The items of `### Limitations` as written (Basis line dropped, lines joined by a space)."""
    return tuple(item for _, item in _limitation_items(text))


def is_earlier_format(text: str) -> bool:
    """H7: the handoff's `## Findings` does not open with `### Bottom line`."""
    sections = _findings_sections(text)
    return not sections or sections[0].title != "Bottom line"


def _first_paragraph(section: _Section) -> list[_Line]:
    paragraph: list[_Line] = []
    for line in _sentence_lines(section.body):
        if not line.text.strip():
            if paragraph:
                break
            continue
        paragraph.append(line)
    return paragraph


def bottom_line_text(text: str) -> str | None:
    """The first paragraph of `### Bottom line` as written, its Basis line dropped; None when
    the handoff has no such passage."""
    sections = _findings_sections(text)
    if not sections or sections[0].title != "Bottom line":
        return None
    return " ".join(line.text for line in _first_paragraph(sections[0])) or None


def limitation_items(text: str) -> tuple[str, ...]:
    """Normalised items of `### Limitations` (lower case, no Basis line, no punctuation)."""
    return tuple(item for _, item in _limitation_entries(text))


def _issue(check: int, name: str, line: int, offending: str, advice: str) -> str:
    return f'Prose check {check} ({name}), line {line}: "{offending}" — {advice}'


def _issue_in(check: int, name: str, where: tuple[int, str], offending: str, advice: str) -> str:
    """An issue that names the section (heading) the line is in, as well as the line."""
    line, section = where
    return (
        f'Prose check {check} ({name}), line {line}: "{offending}" in section "{section}" '
        f"— {advice}"
    )


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
        return _check_bottom_line_length(sections[0])
    return [
        _issue(
            1,
            name,
            number,
            stripped[:60],
            "start the bottom line with a prose sentence, not a table, list, fence or comment.",
        )
    ]


BOTTOM_LINE_FIRST_SENTENCE_WORDS = 45  # Decision 8 of 2026-11-12.
BOTTOM_LINE_WORDS = 180
SENTENCE_END = re.compile(r"[.!?][\"')\]”’*`]*(?:\s|$)")


def _check_bottom_line_length(section: _Section) -> list[str]:
    """The first sentence is at most 45 words and the whole passage at most 180, words being
    whitespace-separated. The sentence ends at the first `.`, `!` or `?` followed by a space or
    the end of the paragraph, so `3.1x` does not end it and an abbreviation such as `Inc.` may,
    which only shortens the sentence counted."""
    name = "bottom line shape"
    issues = []
    paragraph = _first_paragraph(section)
    first = " ".join(line.text for line in paragraph)
    end = SENTENCE_END.search(first)
    sentence = first[: end.end()] if end else first
    if len(sentence.split()) > BOTTOM_LINE_FIRST_SENTENCE_WORDS:
        issues.append(
            _issue_in(
                1,
                name,
                (paragraph[0].number, section.title),
                " ".join(sentence.split()[:8]) + " ...",
                f"the first sentence is {len(sentence.split())} words; state the view and its "
                f"consequence for creditors in at most {BOTTOM_LINE_FIRST_SENTENCE_WORDS} words.",
            )
        )
    total = sum(len(line.text.split()) for line in _sentence_lines(section.body))
    if total > BOTTOM_LINE_WORDS:
        issues.append(
            _issue_in(
                1,
                name,
                (section.line, section.title),
                f"{total} words",
                f"the whole Bottom line is at most {BOTTOM_LINE_WORDS} words; move detail to "
                "Key findings.",
            )
        )
    return issues


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
        # One issue per bracket pair, the bracketed text whole when it is at most 80 characters; a
        # bracket with no partner (or a longer pair) is one issue per bracket character.
        re.compile(r"\[[^\[\]]{0,80}\]|【[^【】]{0,80}】|[\[\]【】]"),
        "remove the brackets; put the source in the paragraph's Basis line.",
    ),
    (
        5,
        "no hash",
        re.compile(r"\b[0-9a-fA-F]{12,}\b|sha256", re.IGNORECASE),
        "remove the hash from the sentence; hashes belong in the run record or a Basis line.",
    ),
)


# Check 10 (decision 7 of 2026-11-12): wording that belongs to the pipeline, not to the reader.
# The phrases are the ruling's list; `downstream` is refused only before module, owner, work,
# analysis or use; a snake_case token has a lower-case letter either side of an underscore; a
# CAPS_WITH_UNDERSCORE token is all capitals, digits and underscores with a letter in it. A file
# name in a sentence is refused only when it is itself a snake_case token (source references
# belong to a Basis line, a table or `## Sources`).
PIPELINE_WORDING = re.compile(
    r"(?i:\bhandoffs?\b|\bthis transport\b|\bthe pack\b|\bfact pack\b|\bsource pack\b"
    r"|\bcanonical\b|\bre-anchor\w*|\bhelper scripts?\b|\bupstream modules?\b"
    r"|\bdownstream (?:modules?|owners?|work|analys[ie]s|use)\b)"
    r"|\w*[a-z]_[a-z]\w*"
    r"|\b(?=[A-Z0-9_]*[A-Z])[A-Z0-9]+(?:_[A-Z0-9]+)+\b"
)


def _check_pipeline_wording(lines: list[_Line]) -> list[str]:
    return [
        _issue_in(
            10,
            "no pipeline wording",
            (line.number, line.section),
            found[0],
            "write for the reader, not for the pipeline: name the document (for example the 2024 "
            "annual report), the module by its plain name or the analysis instead.",
        )
        for line in lines
        for found in PIPELINE_WORDING.finditer(line.text)
    ]


def _quoted(number: int, text: str, found: re.Match[str]) -> str:
    """What an issue quotes: the match, and for a bare bracket (check 4) 20 characters each side."""
    if number == 4 and len(found[0]) == 1:
        return text[max(0, found.start() - 20) : found.end() + 20].strip()
    return found[0].strip()


def _check_simple(lines: list[_Line]) -> list[str]:
    """Checks 2-5. An issue in a reader passage keeps its short form (the passage is known from
    the line); an issue in any other section names the section."""
    return [
        _issue(number, name, line.number, _quoted(number, line.text, found), advice)
        if line.section in READER_HEADINGS
        else _issue_in(
            number, name, (line.number, line.section), _quoted(number, line.text, found), advice
        )
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


PERIOD_LABEL = re.compile(
    r"(?:FY\d+E?|[QH]\d|LTM|\d+M)(?:\s+\d{4})?", re.IGNORECASE
)  # A period, not an ID.


def _calculation_tables(text: str) -> list[list[list[str]]]:
    """Pipe tables under `## Calculations`, up to the next H2 outside a fence."""
    kept: list[str] = []
    in_calculations = fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(FENCE):
            fenced = not fenced
        heading = None if fenced else HEADING.fullmatch(line)
        if heading is not None and len(heading[1]) <= 2:
            in_calculations = heading[2] == "Calculations"
        if in_calculations:
            kept.append(line)
    return _tables("\n".join(kept))


def _register_ids(text: str) -> set[str]:
    ids: set[str] = set()
    for rows in _calculation_tables(text):
        header = len(rows) >= 2 and all(re.fullmatch(r":?-+:?", c) for c in rows[1])
        ids.update(
            row[0]
            for row in rows[2 if header else 0 :]
            if row and _has_letter_and_digit(row[0]) and not PERIOD_LABEL.fullmatch(row[0])
        )
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


# Check 9: the provider's citation delimiters (U+E200 to U+E202; a genuine private-use character
# elsewhere is not refused) or the plain-text form a copy step leaves, citeturn0view0,
# citeturn0image0, cite turn0fetch1. Unlike checks 2-6 it reads the whole handoff, not only the
# reader passages: a marker left in Gaps or a Sources cell is as much a defect.
PROVIDER_MARKER = re.compile(r"[\ue200-\ue202]|cite\s*turn\d+[a-z]+\d+")


def _check_provider_markers(text: str) -> list[str]:
    return [
        _issue(
            9,
            "no provider citation marker",
            number,
            f"U+{ord(found[0]):04X}" if len(found[0]) == 1 else found[0],
            "remove the marker; put the source in the paragraph's Basis line.",
        )
        for number, line in enumerate(text.split("\n"), start=1)
        for found in PROVIDER_MARKER.finditer(line)
    ]


def prose_issues(text: str, accepted: Mapping[str, str] = {}) -> tuple[str, ...]:
    """Every H6 failure in this handoff; `accepted` (module -> Markdown) feeds check 7 only.
    Checks 2-5 and 10 read the sentence text of every section the Modules page shows (decision 7
    of 2026-11-12); checks 6 and 8 stay on the reader passages."""
    sections = _findings_sections(text)
    passages = sorted(
        (
            line
            for body in _pooled(sections or []).values()
            for line in _sentence_lines(body)
            if line.text.strip()
        ),
        key=lambda line: line.number,
    )
    shown = _shown_sentence_lines(text)
    return tuple(
        _check_bottom_line(sections)
        + _check_simple(shown)
        + _check_register_ids(text, passages)
        + _check_limitation_repeats(text, accepted)
        + _check_figures(passages)
        + _check_provider_markers(text)
        + _check_pipeline_wording(shown)
    )


# Fidelity check (decision 11, owner 2026-11-11), ported from the retired Reader-summary figure
# check: it is not one of the eight prose checks. A number as the reader sees it is the longest
# run of digits at that place (3.14 is read whole, never as 3.1; a malformed 1.2.3 or 12,5 is
# still read, as 1.2 and 3, or 12 and 5), with the sign it was written with (a leading minus, or
# parentheses) and the unit or scale beside it. On the passage side dates and period labels
# are masked as in check 8. A held currency code is not compared with the passage's (old behaviour).
CODE = re.compile(r"\bCP-[A-Z0-9]+\b|\bT\d+[A-Z]?\.\d+\b|\b[0-9A-Fa-f]{16,}\b")
_NUMBER_UNIT = (
    r"%|x\b|\s?pp\b|\s?bps\b|\s?bp\b|\s?per ?cent\b"
    r"|(?:\s?(?:US\$|USD|\$|EUR|€|GBP|£))?\s?(?:thousands?|millions?|billions?|trillions?|bn|mm|k|m)\b"
)
NUMBER = re.compile(
    r"(?<!\d)(?P<open>\()?(?P<minus>(?<![\w)])[-\u2212])?"
    r"(?P<n>\d+(?:,\d{3}(?!\d))*(?:\.\d+)?)"
    rf"(?P<u1>{_NUMBER_UNIT})?(?P<close>\))?(?P<u2>{_NUMBER_UNIT})?",
    re.IGNORECASE,
)
SCALES = {
    "thousand": "k",
    "thousands": "k",
    "k": "k",
    "million": "m",
    "millions": "m",
    "mm": "m",
    "m": "m",
    "bps": "bp",
    "billion": "b",
    "billions": "b",
    "bn": "b",
    "trillion": "t",
    "trillions": "t",
}


class _Figure(NamedTuple):
    number: str  # Trailing decimal zeros dropped: 4.10 is 4.1.
    negative: bool
    bracketed: bool  # The sign was written as parentheses, not a minus.
    unit: str | None
    shown: str


def _unit(written: str | None) -> str | None:
    """The unit or scale of a figure, spelled one way: `%`, `x`, `k`, `m`, `b`, ..."""
    if not written:
        return None
    word = re.sub(r"^(?:us\$|usd|\$|eur|€|gbp|£)?\s*", "", written.strip().casefold())
    return "%" if "cent" in word else SCALES.get(word, word)


PERIOD_WORD = re.compile(r"\b(?:[QH][1-4]|FY\d{2,4}E?|LTM|\d+M)\b")


def _figures(text: str, passage: bool = False) -> list[_Figure]:
    """Figures of `text`. On the passage side dates and period labels are not figures (as in
    check 8); held text is read unmasked, so a year held only in a date still matches."""
    masked = CODE.sub(" ", text)
    if passage:
        masked = PERIOD_WORD.sub(
            lambda m: " " * len(m[0]), DATE.sub(lambda m: " " * len(m[0]), masked)
        )
    return [
        _Figure(
            found["n"].rstrip("0").rstrip(".") if "." in found["n"] else found["n"],
            bool(found["minus"] or (found["open"] and found["close"])),
            bool(found["open"] and found["close"] and not found["minus"]),
            _unit(found["u1"] or found["u2"]),
            found[0].strip(),
        )
        for found in NUMBER.finditer(masked)
    ]


def _fidelity_problem(figure: _Figure, held: list[_Figure]) -> str | None:
    """Why a passage figure is not held in the handoff, or None: 12.3% is not (12.3)%, 4.1x is
    not 4.1%, 250 thousand is not 250 million; a number matches only as a whole number."""
    same = [h for h in held if h.number == figure.number]
    where = "elsewhere in the handoff (tables, calculations or other findings)"
    if not same:
        return (
            f'"{figure.shown}" does not appear {where}, with the same sign, unit and scale: add '
            "it there or remove it from the passage."
        )
    # A figure the handoff writes with a minus may be narrated as its magnitude ("fell 5%");
    # one written in parentheses, or a minus the handoff does not write, may not.
    if any(
        (h.negative == figure.negative or (h.negative and not h.bracketed and not figure.negative))
        and (h.unit == figure.unit or None in (h.unit, figure.unit))
        for h in same
    ):
        return None
    written = ", ".join(dict.fromkeys(h.shown for h in same[:3]))
    return (
        f'"{figure.shown}" does not match the handoff, which writes it as {written}: keep the '
        "sign and unit as written."
    )


KEY_FIGURES_HEADING = "### Key figures"
KEY_FIGURES_HEADER = ["Measure", "Value", "Period", "Source"]


def key_figures_issues(text: str, cp1: str) -> tuple[str, ...]:
    """CP-L10's Key figures: exactly one table with the columns `Measure | Value | Period |
    Source`, and every figure of a Value cell held in the CP-1 handoff with the same sign, unit
    and scale (the sign must match exactly; a unit CP-1 carries only in a column header is not
    matched). It proves the figure exists in CP-1, not that it is the right measure or period."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == KEY_FIGURES_HEADING), None)
    if start is None:
        return ()  # the report selector check names a missing section
    section: list[str] = []
    for line in lines[start + 1 :]:
        if re.match(r"#{1,6}\s", line):
            break
        section.append(line)
    tables = _tables("\n".join(section))
    if not tables or any(t[0] != KEY_FIGURES_HEADER for t in tables):
        header = "`| Measure | Value | Period | Source |`"
        return (f"Key figures: the table header must be exactly {header}.",)
    issues = []
    if len(tables) > 1:
        issues.append("Key figures: write exactly one table under the heading.")
    held = _figures(cp1)
    for table in tables:
        for row in table[2:]:
            for figure in dict.fromkeys(_figures(row[1] if len(row) > 1 else "")):
                same = [h for h in held if h.negative == figure.negative]
                if _fidelity_problem(figure, same) is not None:
                    issues.append(
                        f'Key figures: "{figure.shown}" is not stated in the CP-1 handoff with '
                        "the same sign, unit and scale: copy it exactly from CP-1 or remove "
                        "the row."
                    )
    return tuple(issues)


FORECAST_HEADING = "### Forecast inputs (machine-readable)"


def _forecast_block_lines(text: str) -> set[int]:
    """Line numbers of the forecast inputs block (its heading to the next heading). Its rationale
    and limit text is the module's input to a calculation, not a table, so it holds no figure."""
    lines: set[int] = set()
    inside = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip() == FORECAST_HEADING:
            inside = True
        elif inside and re.match(r"#{1,6}\s", line):
            inside = False
        if inside:
            lines.add(number)
    return lines


def figure_issues(text: str) -> tuple[str, ...]:
    """Every figure of a reader passage not held, with its sign, unit and scale, in the handoff
    outside the reader passages. Sentence text only, as in the prose checks."""
    passages = _pooled(_findings_sections(text) or [])
    inside = {number for body in passages.values() for number, _ in body}
    inside |= _forecast_block_lines(text)
    held = _figures(
        "\n".join(line for number, line in enumerate(text.splitlines(), 1) if number not in inside)
    )
    lines = sorted(
        (line for body in passages.values() for line in _sentence_lines(body) if line.text.strip()),
        key=lambda line: line.number,
    )
    issues = []
    for line in lines:
        for figure in dict.fromkeys(_figures(line.text, passage=True)):
            problem = _fidelity_problem(figure, held)
            if problem is not None:
                issues.append(f"Fidelity check, line {line.number}: {problem}")
    return tuple(issues)
