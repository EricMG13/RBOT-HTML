"""The check of CP-8's handoff against its comparison pack (`deploy_workflow.changes`, schema
`cpos-changes/2`). Pure: no I/O, no provider.

CP-8 explains and never calculates (owner, 2026-11-11). Beside the prose checks every handoff
meets, this module refuses, naming the line, a CP-8 handoff in which:

- one of the three registers (`### What changed: the issuer`, `### What changed: the analysis`,
  `### Limitations ledger`) is missing, repeated, has other columns, or has no table;
- a Status or Cause is not from its fixed list, an issuer row has an analysis-only cause, a
  `Presentation` cause is not on an `Unchanged` row, or a `None` cause is not on `Unchanged` or on
  the single `No material change` row;
- a module of the pack has no analysis row, has two, or the row's Status contradicts the pack;
- in the issuer register a row whose Earlier or Current cell holds a figure does not name a pack
  measure by its exact label (a row without figures is a fact row: free text); a row that names one
  does not print that measure's earlier and current value, with its sign and unit, in the right
  columns, or prints a figure that is not one of that measure's values; a row of a measure the pack
  marks `judge` says neither or both of `Same definition` and `Not comparable`; a row of a measure
  the pack marks `no` does not say `Not comparable`; a row that says `Not comparable` prints the
  difference or draws a trend;
- a difference printed anywhere in the handoff (a figure after `by`, or after a direction word)
  is not a pack difference, or its direction word contradicts the pack's sign, or it carries a
  sign after a direction word;
- the ledger names a ref the pack does not hold, holds a ref in the wrong column, holds a pack ref
  in no row or in more than one, has a Status that contradicts its refs (an `E` and a `C` ref:
  `Remaining`; only `E`: `Closed` or `No longer stated`; only `C`: `New`), has no limitation in
  words, or closes a limitation without naming a module of the current run as evidence; or a ref
  is written anywhere but the two ref columns.

A "figure" in an Earlier or Current cell of a row that names no measure is a number that is not a
date, a period label, a year or a whole number below 100 without a unit (a count); in a row that
names a measure every number of its Earlier and Current cells counts.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from deploy_workflow.changes import decimal, number

ISSUER = "What changed: the issuer"
ANALYSIS = "What changed: the analysis"
LEDGER = "Limitations ledger"
COLUMNS = {
    ISSUER: ("Measure or fact", "Earlier", "Current", "Cause", "Effect on the credit view"),
    ANALYSIS: ("Module", "Status", "Cause", "Why"),
    LEDGER: ("Earlier ref", "Current ref", "Limitation", "Status", "What closed it"),
}
STATUSES = ("Unchanged", "Strengthened", "Weakened", "Reversed", "New", "Not run this time")
CAUSES = ("New period", "New source", "Method change", "Correction", "Presentation", "Unresolved")
ISSUER_CAUSES = ("New period", "New source", "Unresolved")
LEDGER_STATUSES = ("Closed", "Remaining", "New", "No longer stated")
NO_CHANGE = "No material change"
NOT_PASSAGES = ("Request", "Sources", "Calculations", "Next module")  # H2s that are no prose
SAME_PERIOD_CAUSES = ("Correction", "Method change")
COUNT_BELOW = 100  # a whole number below this, without a unit, is a count
SAME = "same definition"
NOT_COMPARABLE = "not comparable"
_MODULE = re.compile(r"\bCP-[A-Z0-9]+\b")
_REF = re.compile(r"\b[EC]\d+\b")
_REF_ANY_CASE = re.compile(r"\b[EC]\d+\b", re.IGNORECASE)
_HEADING = re.compile(r"#{1,6}\s")
_FIGURE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")
# Dates, period labels, years and a month count of 1M to 12M are not figures.
_EXEMPT = re.compile(
    r"\d{4}-\d{2}(?:-\d{2})?|\b(?:FY|CY)\d{2,4}E?\b|\b[QH][1-4]\b|\bLTM\b|\b(?:[1-9]|1[0-2])M\b"
    r"|\b(?:19|20)\d{2}\b"
)
_UNITED = re.compile(
    r"\s*(?:%|x\b|bps?\b|pp\b|[mk]\b|bn\b|(?i:million|billion|thousand|percent)"
    r"|(?:[A-Z]{2,3})?[$€£¥]\w{0,2}\b|[A-Z]{3}\b)"
)
_CURRENCY = re.compile(r"(?:[$€£¥]|\b[A-Z]{3}) ?$")
_NOT_EVIDENCE = frozenset({"", "-", "—", "–", "n/a", "none", "not stated"})
_DASHES = frozenset({"", "-", "—", "–"})
_UP = r"rose|rise|risen|rises|increased?|increases|grew|grown|up|higher|gained|added"
_DOWN = r"fell|fall|fallen|falls|decreased?|decreases|declined?|dropped|down|lower|reduced|shrank"
_TREND = re.compile(
    rf"\b(?:{_UP}|{_DOWN}|strengthen\w*|weaken\w*|improv\w*|worsen\w*|deteriorat\w*|better|worse"
    r"|eased|tightened|trend\w*)\b",
    re.IGNORECASE,
)
_DIRECTION = re.compile(rf"\b(?:(?P<up>{_UP})|(?P<down>{_DOWN}))\b", re.IGNORECASE)
_SENTENCE_END = re.compile(r"[.;:!?]\s")
# A figure written as a difference: after `by` or a direction word (ends at the first digit).
_AS_DIFFERENCE = re.compile(
    rf"\b(?:by|{_UP}|{_DOWN})\s+(?:by\s+)?(?:about\s+|roughly\s+|nearly\s+)?"
    r"(?:[-+−]\s?)?\(?\s?\d$",
    re.IGNORECASE,
)


class Figure:
    """A figure of a text: its signed value, where it stands, and whether a minus was written."""

    def __init__(self, signed: Decimal, start: int, end: int, *, minus: bool) -> None:
        self.signed = signed
        self.start = start
        self.end = end
        self.minus = minus

    @property
    def size(self) -> Decimal:
        return abs(self.signed)


def _figures(cell: str, *, counts: bool = True) -> list[Figure]:
    """The figures of a cell. A number is not one if it is part of a date, a period label or a year
    (`_EXEMPT`); with `counts` False a whole number below 100 is a count and not a figure unless it
    carries a unit or a currency. A minus (`-` or U+2212, not inside a word or number) or enclosing
    brackets make the figure negative."""
    masked = _EXEMPT.sub(lambda m: " " * len(m[0]), cell)
    found = []
    for match in _FIGURE.finditer(masked):
        token = match[0]
        small = "." not in token and "," not in token and int(token) < COUNT_BELOW
        united = _UNITED.match(masked, match.end())
        currency = _CURRENCY.search(masked[max(0, match.start() - 4) : match.start()])
        if not counts and small and not united and not currency:
            continue
        before = masked[max(0, match.start() - 2) : match.start()]
        minus = re.search(r"(?:^|[^\w.])[-−]$", before) is not None
        bracket = before.endswith("(") and masked[match.end() : match.end() + 1] == ")"
        value = decimal(token)
        found.append(
            Figure(-value if minus or bracket else value, match.start(), match.end(), minus=minus)
        )
    return found


def _section(lines: list[str], title: str) -> tuple[list[str], list[list[str]]] | str:
    """(header, rows) of the one table under `### title`, or why there is none."""
    starts = [i for i, line in enumerate(lines) if line.strip() == f"### {title}"]
    if len(starts) != 1:
        return f"`### {title}` must appear exactly once (found {len(starts)})."
    rows: list[list[str]] = []
    for line in lines[starts[0] + 1 :]:
        if _HEADING.match(line):
            break
        text = line.strip()
        if text.startswith("|") and text.endswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", text[1:-1])]
            if not set("".join(cells)) <= set("-: "):
                rows.append(cells)
    if not rows:
        return f"`### {title}` holds no table."
    return rows[0], rows[1:]


def _plain(name: str) -> str:
    """A row's first cell compared with a measure's label: no emphasis, no trailing brackets."""
    bare = re.sub(r"\s*\([^)]*\)\s*$", "", name.replace("*", "").replace("`", ""))
    return " ".join(bare.lower().split())


def _signed(value: Any) -> Decimal | None:
    return decimal(value) if isinstance(value, str) and number(value) is not None else None


def _present(values: Sequence[Decimal | None]) -> set[Decimal]:
    return {v for v in values if v is not None}


def _measure_values(measure: Mapping[str, Any]) -> set[Decimal]:
    return _present(
        [
            _signed(measure["difference"]),
            *(_signed((measure[side] or {}).get("value")) for side in ("prior", "current")),
        ]
    )


def _flagged(measure: Mapping[str, Any]) -> bool:
    """A measure of one period with two values: the issuer did not change, so a difference is a
    difference of definition or a correction (rule 3 of the method)."""
    difference = _signed(measure["difference"])
    return bool(measure["same_period"]) and difference is not None and difference != 0


def _pack_differences(
    pack: Mapping[str, Any], *, without: frozenset[str] = frozenset()
) -> set[Decimal]:
    """Every difference the pack gives (signed), but those of the measures named in `without`."""
    change = pack.get("net_debt_change") or {}
    rows = (pack.get("maturity_profile") or {}).get("rows", ())
    return _present(
        [
            *(_signed(m["difference"]) for m in pack["measures"] if m["key"] not in without),
            *(_signed(change.get(k)) for k in ("change_in_gross_debt", "change_in_cash")),
            *(_signed(row["difference"]) for row in rows),
        ]
    )


def _pack_values(pack: Mapping[str, Any]) -> set[Decimal]:
    """Every value the pack holds (signed): measures, net debt change, maturity rows."""
    change = pack.get("net_debt_change") or {}
    rows = (pack.get("maturity_profile") or {}).get("rows", ())
    found = _pack_differences(pack) | _present(
        [_signed(change.get(k)) for k in ("prior_net_debt", "current_net_debt")]
        + [_signed(row[k]) for row in rows for k in ("prior", "current")]
    )
    for measure in pack["measures"]:
        found |= _measure_values(measure)
    return found


def _columns(table: tuple[list[str], list[list[str]]], title: str) -> list[str]:
    header, rows = table
    issues = []
    if tuple(header) != COLUMNS[title]:
        issues.append(
            f"`### {title}` needs exactly these columns: " + " | ".join(COLUMNS[title]) + "."
        )
    issues += [
        f"`### {title}`: a row has {len(r)} cells, not {len(header)}."
        for r in rows
        if len(r) != len(header)
    ]
    return issues


def _direction_issues(text: str, differences: set[Decimal], where: str) -> list[str]:
    """The figures of `text` written as differences (after `by` or a direction word) must be pack
    differences, in the pack's direction: a direction word before the figure agrees with the sign of
    the difference; a sign written after a direction word is refused (write the size and the
    word)."""
    issues = []
    for figure in _figures(text, counts=False):
        lead = text[max(0, figure.start - 60) : figure.start]
        if not _AS_DIFFERENCE.search(lead + text[figure.start : figure.start + 1]):
            continue
        sizes = {d for d in differences if abs(d) == figure.size}
        if not sizes:
            issues.append(
                f"{where}: the figure {figure.size} is written as a difference but is not a "
                "difference in the comparison pack; CP-8 never calculates."
            )
            continue
        words = list(_DIRECTION.finditer(_SENTENCE_END.split(lead)[-1]))
        if words and figure.minus:
            issues.append(
                f"{where}: the difference {figure.signed} carries a sign after a direction word; "
                "write its size with the word (fell by 0.60x) or the signed value alone."
            )
        elif words and not any((d > 0) == bool(words[-1]["up"]) for d in sizes):
            issues.append(
                f"{where}: the direction of the difference {figure.size} contradicts the pack's "
                f"sign ({', '.join(str(d) for d in sorted(sizes))})."
            )
        elif not words and figure.minus and figure.signed not in differences:
            issues.append(
                f"{where}: the difference {figure.signed} is not a pack difference (sign)."
            )
    return issues


def _unit_differs(cell: str, figure: Figure, unit: str | None) -> bool:
    """True when the text directly after the figure states a unit or scale other than the measure's
    (`300 US$bn` for US$m), unless the unit is split around the figure (`US$300m`)."""
    if unit is None:
        return False
    tail = re.split(r"[(,;]|\.\s|\.$", cell[figure.end :], maxsplit=1)[0]
    tail = re.sub(r"\s+", "", tail).lower()
    want = re.sub(r"\s+", "", unit).lower()
    if not tail or tail.startswith(want):
        return False
    head = re.sub(r"\s+", "", cell[max(0, figure.start - len(want)) : figure.start]).lower()
    return not (want.endswith(tail) and head.endswith(want[: -len(tail)]))


def _value_cell_issues(
    where: str, side: str, cell: str, held: Mapping[str, Any] | None
) -> list[str]:
    """An Earlier or Current cell of a measure's row: it prints that run's value with its sign and
    unit, and no other figure."""
    stated = _signed((held or {}).get("value"))
    printed = _figures(cell)
    issues = []
    for figure in printed:
        if figure.signed != stated:
            issues.append(
                f"{where}: {side} figure {figure.signed} is not the pack's {side} value "
                f"({'not stated' if stated is None else stated})."
            )
        elif _unit_differs(cell, figure, (held or {}).get("unit")):
            issues.append(
                f"{where}: the unit written after the {side} figure {figure.signed} is not the "
                f"pack's ({(held or {}).get('unit')}); the scale is part of the value."
            )
    if stated is not None and not any(f.signed == stated for f in printed):
        issues.append(f"{where}: the {side} cell must print the pack's {side} value ({stated}).")
    return issues


def _definition_issues(where: str, row: Sequence[str], measure: Mapping[str, Any]) -> list[str]:
    """The row's statement on whether the two values share a definition, and what a row that says
    `Not comparable` may print."""
    text = " ".join(row).lower()
    issues = []
    if measure["comparable"] == "judge":
        said = [word for word in (SAME, NOT_COMPARABLE) if word in text]
        if len(said) != 1:
            issues.append(
                f"{where}: the pack leaves the definition to CP-8; write for this row either "
                f"`Same definition` or `Not comparable` (only one of the two; found {len(said)})."
            )
    elif measure["comparable"] == "no" and NOT_COMPARABLE not in text:
        issues.append(
            f"{where}: the pack marks this measure not comparable ({measure['reason']}); say "
            '"not comparable" and give no difference.'
        )
    if NOT_COMPARABLE in text:
        difference = _signed(measure["difference"])
        values = _present([_signed((measure[s] or {}).get("value")) for s in ("prior", "current")])
        if difference is not None and any(
            f.size == abs(difference) and f.size not in {abs(v) for v in values}
            for f in _figures(row[4], counts=False)
        ):
            issues.append(f"{where}: a `Not comparable` row must not print the difference.")
        if _TREND.search(row[4]):
            issues.append(f"{where}: a `Not comparable` row draws no trend from the two values.")
    return issues


def _measure_row_issues(
    name: str, row: Sequence[str], measure: Mapping[str, Any], pack: Mapping[str, Any]
) -> list[str]:
    where = f"Issuer register, {name!r}"
    issues = _value_cell_issues(where, "earlier", row[1], measure["prior"])
    issues += _value_cell_issues(where, "current", row[2], measure["current"])
    allowed = _measure_values(measure)
    if measure["key"] == "net_debt":
        change = pack.get("net_debt_change") or {}
        allowed |= _present([_signed(v) for k, v in change.items() if k != "convention"])
    issues += [
        f"{where}: the figure {figure.size} is not a value of this measure in the comparison "
        "pack; CP-8 never calculates."
        for figure in _figures(row[4], counts=False)
        if figure.size not in {abs(v) for v in allowed}
    ]
    return issues + _definition_issues(where, row, measure)


def _same_period_issues(name: str, row: Sequence[str], cause: str) -> list[str]:
    """A measure the two runs state for one period, with different values: the issuer did not
    change. The row says `Not comparable`, or `Same definition` with the cause `Correction` or
    `Method change`; never `New period` or `New source`."""
    where = f"Issuer register, {name!r}"
    text = " ".join(row).lower()
    if cause in ("New period", "New source"):
        return [
            (
                f"{where}: both runs state this measure for the same period, so the issuer did "
                f"not change and the cause is not `{cause}`; it is a definition "
                "(`Not comparable`), a `Correction` or a `Method change`."
            )
        ]
    if NOT_COMPARABLE in text or (SAME in text and cause in SAME_PERIOD_CAUSES):
        return []
    return [
        (
            f"{where}: both runs state this measure for the same period with different values; "
            "write `Not comparable`, or `Same definition` with the cause `Correction` or "
            "`Method change`."
        )
    ]


def _issuer_issues(rows: list[list[str]], pack: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if not rows:
        return [f"`### {ISSUER}` needs a row; if nothing changed, one `{NO_CHANGE}` row."]
    everything = {abs(v) for v in _pack_values(pack)}
    labels = {m["label"].lower(): m for m in pack["measures"]}
    for row in rows:
        name, earlier, current, cause, effect = row
        if name.strip().strip("*") == NO_CHANGE:
            if cause != "None":
                issues.append(f"The `{NO_CHANGE}` row's Cause is `None`.")
            continue
        measure = labels.get(_plain(name))
        flagged = measure is not None and _flagged(measure)
        causes = (*ISSUER_CAUSES, *(SAME_PERIOD_CAUSES if flagged else ()))
        if cause not in causes:
            issues.append(
                f"Issuer register, {name!r}: Cause {cause!r} is not one of "
                + ", ".join(f"`{c}`" for c in causes)
                + " (an analysis change belongs in the analysis register)."
            )
        if measure is not None:
            issues += _measure_row_issues(name, row, measure, pack)
            if flagged:
                issues += _same_period_issues(name, row, cause)
        elif any(_figures(cell, counts=False) for cell in (earlier, current)):
            issues.append(
                f"Issuer register, {name!r}: a row with a figure in Earlier or Current must name "
                "a pack measure by its exact label (a row without figures is a fact row)."
            )
        else:
            issues += [
                f"Issuer register, {name!r}: the figure {figure.size} is not in the comparison "
                "pack; CP-8 never calculates."
                for figure in _figures(effect, counts=False)
                if figure.size not in everything
            ]
    return issues


def _analysis_issues(rows: list[list[str]], pack: Mapping[str, Any]) -> list[str]:
    issues = []
    seen: dict[str, int] = {}
    ran = {m["module"]: (m["ran_prior"], m["ran_current"]) for m in pack["modules"]}
    for module, status, cause, _ in rows:
        codes = _MODULE.findall(module)
        if len(codes) != 1 or codes[0] not in ran:
            issues.append(f"Analysis register: {module!r} does not name one module of the pack.")
            continue
        code = codes[0]
        seen[code] = seen.get(code, 0) + 1
        before, now = ran[code]
        if status not in STATUSES:
            issues.append(f"Analysis register, {code}: Status {status!r} is not one of {STATUSES}.")
        elif status == "New" and (before or not now):
            issues.append(
                f"Analysis register, {code}: `New` is only for a module that ran now, not before."
            )
        elif status == "Not run this time" and (now or not before):
            issues.append(
                f"Analysis register, {code}: `Not run this time` is only for a module that ran "
                "before and not now."
            )
        elif status not in {"New", "Not run this time"} and not (before and now):
            issues.append(
                f"Analysis register, {code}: the module did not run in both runs, so its Status "
                "is `New` or `Not run this time`."
            )
        if cause not in (*CAUSES, "None"):
            issues.append(f"Analysis register, {code}: Cause {cause!r} is not one of {CAUSES}.")
        elif cause == "Presentation" and status != "Unchanged":
            issues.append(
                f"Analysis register, {code}: a `Presentation` difference is not a finding; "
                "the Status is `Unchanged`."
            )
        elif cause == "None" and status != "Unchanged":
            issues.append(f"Analysis register, {code}: only an `Unchanged` row has Cause `None`.")
    issues += [
        f"Analysis register: {c} needs exactly one row (found {seen.get(c, 0)})."
        for c in ran
        if seen.get(c, 0) != 1
    ]
    return issues


def _refs_of(cell: str, letter: str, column: str) -> tuple[list[str], list[str]]:
    """(refs, issues) of a ref cell: refs separated by commas, spaces, `&` or `and`, or a dash."""
    text = cell.strip()
    if text in _DASHES:
        return [], []
    tokens = [t for t in re.split(r"[,\s&]+|\band\b", text) if t]
    bad = [t for t in tokens if not re.fullmatch(r"[EC]\d+", t)]
    wrong = [t for t in tokens if t not in bad and not t.startswith(letter)]
    issues = [
        f"Limitations ledger: the {column} cell holds {t!r}, which is not a ref." for t in bad
    ]
    issues += [
        f"Limitations ledger: {t} is in the {column} column, which takes only {letter} refs."
        for t in wrong
    ]
    return [t for t in tokens if t not in bad and t not in wrong], issues


def _ledger_status_issues(
    label: str, status: str, stated: tuple[bool, bool], closed: str, ran: set[str]
) -> list[str]:
    """The Status of one ledger row against its refs (`stated`: an earlier, a current ref)."""
    earlier, current = stated
    expected = (
        ("Remaining",)
        if earlier and current
        else ("New",)
        if current
        else ("Closed", "No longer stated")
    )
    if status not in LEDGER_STATUSES:
        return [f"Limitations ledger, {label}: Status {status!r} is not one of {LEDGER_STATUSES}."]
    if status not in expected:
        return [
            f"Limitations ledger, {label}: its refs say {' or '.join(expected)}, not {status!r}."
        ]
    if status == "Closed" and not (
        closed.strip().lower() not in _NOT_EVIDENCE and set(_MODULE.findall(closed)) & ran
    ):
        return [
            (
                f"Limitations ledger, {label}: `Closed` needs evidence in the current run: name "
                "the module whose handoff shows it and say what it shows; otherwise "
                "`No longer stated`."
            )
        ]
    return []


def _ledger_issues(rows: list[list[str]], pack: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    wanted = {item["ref"] for side in ("earlier", "current") for item in pack["limitations"][side]}
    ran_now = {m["module"] for m in pack["modules"] if m["ran_current"]}
    seen: dict[str, int] = {}
    for earlier_cell, current_cell, text, status, closed in rows:
        earlier, bad_e = _refs_of(earlier_cell, "E", "Earlier ref")
        current, bad_c = _refs_of(current_cell, "C", "Current ref")
        refs = earlier + current
        unknown = [r for r in refs if r not in wanted]
        issues += bad_e + bad_c
        issues += [f"Limitations ledger: {r} is not a ref of the comparison pack." for r in unknown]
        for ref in refs:
            seen[ref] = seen.get(ref, 0) + 1
        if bad_e or bad_c or unknown:
            continue
        if not refs:
            issues.append(f"Limitations ledger: the row {text[:60]!r} names no ref.")
            continue
        if text.strip().lower() in _NOT_EVIDENCE or _REF.fullmatch(text.strip()):
            issues.append(
                f"Limitations ledger, {', '.join(refs)}: the Limitation cell must state the "
                "limitation in plain words."
            )
        issues += _ledger_status_issues(
            ", ".join(refs), status, (bool(earlier), bool(current)), closed, ran_now
        )
    issues += [
        f"Limitations ledger: {ref} needs exactly one row (found {seen.get(ref, 0)})."
        for ref in sorted(wanted, key=lambda r: (r[0], int(r[1:])))
        if seen.get(ref, 0) != 1
    ]
    return issues


def _outside_ref_issues(lines: list[str], pack: Mapping[str, Any]) -> list[str]:
    """A pack ref written anywhere but the two ref columns of the ledger."""
    refs = {item["ref"] for side in ("earlier", "current") for item in pack["limitations"][side]}
    in_ledger = False
    found: dict[str, None] = {}
    for line in lines:
        if _HEADING.match(line):
            in_ledger = line.strip() == f"### {LEDGER}"
        text = line
        stripped = line.strip()
        if in_ledger and stripped.startswith("|") and stripped.endswith("|"):
            text = " ".join(re.split(r"(?<!\\)\|", stripped[1:-1])[2:])
        found.update(
            dict.fromkeys(r.upper() for r in _REF_ANY_CASE.findall(text) if r.upper() in refs)
        )
    return [
        f"{ref} appears outside the ledger's ref columns; a ref may be written only in the "
        "Earlier ref and Current ref columns, never in a sentence or another cell."
        for ref in found
    ]


# Words by which a passage names a measure (beside its label): a sentence about "leverage" is about
# the leverage measure. Only a passage's sentences are read with these, never a register row.
ALIASES = {
    "leverage": ("leverage",),
    "net_leverage": ("net leverage",),
    "coverage": ("cover", "coverage"),
    "cash": ("cash",),
    "undrawn": ("undrawn", "committed facilities"),
    "free_cash_flow": ("free cash flow", "fcf"),
    "gross_debt": ("gross debt", "total debt"),
    "net_debt": ("net debt",),
}
_EXPLAINS = re.compile(r"\b(?:correct\w*|method change\w*|restat\w*)\b", re.IGNORECASE)
_SENTENCES = re.compile(r"(?<=[.;:!?])\s+")


def _named(sentence: str, pack: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """The pack measures a sentence names, by their label or their ALIASES."""
    lowered = sentence.lower()
    found = []
    for measure in pack["measures"]:
        words = (measure["label"].lower(), *ALIASES.get(measure["key"], ()))
        if any(re.search(rf"\b{re.escape(word)}\b", lowered) for word in words):
            found.append(measure)
    return found


def _withheld(pack: Mapping[str, Any], said_nc: frozenset[str]) -> frozenset[str]:
    """Measures whose difference a reader is not given: the pack marks them `no`, CP-8's row says
    `Not comparable`, or both runs state them for one period with different values."""
    return frozenset(
        m["key"]
        for m in pack["measures"]
        if m["comparable"] == "no" or m["key"] in said_nc or _flagged(m)
    )


def _sentence_issues(
    sentence: str,
    pack: Mapping[str, Any],
    withheld: frozenset[str],
    shown: frozenset[Decimal],
    *,
    figures: bool,
) -> list[str]:
    """A reader sentence: no direction or trend word attached to a withheld measure's name (unless
    the sentence names the correction or method change), and, in `figures`, every figure is a pack
    value of a measure it names (or of the pack at large when it names none) or is printed in one
    of CP-8's own register rows."""
    named = _named(sentence, pack)
    issues = []
    if (
        any(m["key"] in withheld for m in named)
        and _TREND.search(sentence)
        and not _EXPLAINS.search(sentence)
    ):
        issues.append(
            "A passage: a direction or trend is drawn for a measure whose values are not "
            f"comparable or are of one period ({sentence.strip()[:70]!r}); say what differs, "
            "not that it moved."
        )
    if not figures:
        return issues
    if named:
        held = set().union(*(_measure_values(m) for m in named if m["key"] not in withheld))
        for measure in (m for m in named if m["key"] in withheld):
            held |= _measure_values(measure) - {_signed(measure["difference"])}
        allowed = {abs(v) for v in held}
    else:
        allowed = {abs(v) for v in _pack_values(pack) - _withheld_differences(pack, withheld)}
    issues += [
        f"A passage: the figure {figure.size} is not a pack value of a measure the sentence "
        "names, nor printed in a register row; CP-8 never calculates."
        for figure in dict.fromkeys(_figures(sentence, counts=False))
        if figure.size not in allowed and figure.size not in shown
    ]
    return issues


def _withheld_differences(pack: Mapping[str, Any], withheld: frozenset[str]) -> set[Decimal]:
    return _present([_signed(m["difference"]) for m in pack["measures"] if m["key"] in withheld])


def _passage_issues(
    lines: list[str],
    pack: Mapping[str, Any],
    said_nc: frozenset[str] = frozenset(),
    shown: frozenset[Decimal] = frozenset(),
) -> list[str]:
    """What the handoff prints outside the registers' checked cells.

    - Differences, anywhere: a figure after `by` or a direction word is a pack difference in the
      pack's direction; the difference of a measure CP-8's row calls `Not comparable`, or the pack
      marks `no`, is printed nowhere; that of a same-period measure with different values only in
      the register rows, never in a passage.
    - Reader passages (every prose line but the registers, `### Limitations` for its figures,
      and the `## Request`, `## Sources`, `## Calculations` and `## Next module` sections): each
      sentence by `_sentence_issues`.
    In the issuer register only the Effect cell is read (the Earlier and Current cells hold values,
    checked against their measure)."""
    withheld = _withheld(pack, said_nc)
    barred = frozenset(
        m["key"] for m in pack["measures"] if m["comparable"] == "no" or m["key"] in said_nc
    )
    passage_differences = _pack_differences(pack, without=withheld)
    register_differences = _pack_differences(pack, without=barred)
    in_issuer, h2, h3 = False, "", ""
    issues: list[str] = []
    for line in lines:
        if _HEADING.match(line):
            in_issuer = line.strip() == f"### {ISSUER}"
            if line.startswith("## "):
                h2, h3 = line[3:].strip(), ""
            elif line.startswith("### "):
                h3 = line[4:].strip()
        text = line.strip()
        row = text.startswith("|") and text.endswith("|")
        if in_issuer and row:
            line = re.split(r"(?<!\\)\|", text[1:-1])[-1]
        issues += _direction_issues(
            line, register_differences if row else passage_differences, "A passage"
        )
        if not row and h2 not in NOT_PASSAGES:
            reading = h3 != "Limitations"
            for sentence in _SENTENCES.split(line):
                issues += _sentence_issues(sentence, pack, withheld, shown, figures=reading)
    return issues


def cp8_issues(text: str, pack: Mapping[str, Any]) -> tuple[str, ...]:
    """Every failure of the CP-8 handoff `text` against its comparison pack (none: accepted)."""
    lines = text.replace("\r\n", "\n").split("\n")
    tables: dict[str, tuple[list[str], list[list[str]]]] = {}
    issues: list[str] = []
    for title in COLUMNS:
        found = _section(lines, title)
        if isinstance(found, str):
            issues.append(found)
            continue
        problems = _columns(found, title)
        issues += problems
        if not problems:
            tables[title] = found
    checks: Sequence[tuple[str, Any]] = (
        (ISSUER, _issuer_issues),
        (ANALYSIS, _analysis_issues),
        (LEDGER, _ledger_issues),
    )
    for title, check in checks:
        if title in tables:
            issues += check(tables[title][1], pack)
    labels = {m["label"].lower(): m["key"] for m in pack["measures"]}
    issuer = tables[ISSUER][1] if ISSUER in tables else []
    said_nc = frozenset(
        labels[_plain(row[0])]
        for row in issuer
        if _plain(row[0]) in labels and NOT_COMPARABLE in " ".join(row).lower()
    )
    shown = frozenset(
        figure.size
        for _, rows in tables.values()
        for row in rows
        for cell in row
        for figure in _figures(cell, counts=False)
    )
    issues += _outside_ref_issues(lines, pack)
    issues += _passage_issues(lines, pack, said_nc, shown)
    return tuple(dict.fromkeys(issues))
