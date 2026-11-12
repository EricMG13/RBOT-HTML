"""The check of CP-8's handoff against its comparison pack (`deploy_workflow.changes`, schema
`cpos-changes/3`). Pure: no I/O, no provider.

CP-8 explains and never calculates (owner, 2026-11-11). The check reads no sentence for its
meaning: it tests structure, lists and numbers only. Beside the prose checks every handoff meets,
it refuses, naming the line, a CP-8 handoff in which:

- one of the three registers (`### What changed: the issuer`, `### What changed: the analysis`,
  `### Limitations ledger`) is missing, repeated, has other columns, or has no table (K1);
- a Status or Cause is not from its fixed list, an issuer row has an analysis-only cause (but
  `Correction` and `Method change` on a measure of one period with two values), a `Presentation`
  cause is not on an `Unchanged` row, or a `None` cause is not on `Unchanged`, on the single
  `No material change` row or on a measure row of zero difference (K2);
- a module of the pack has no analysis row, has two, or the row's Status contradicts the pack (K3);
- the ledger names a ref the pack does not hold, holds a ref in the wrong column, holds a pack ref
  in no row or in more than one, has a Status that contradicts its refs (an `E` and a `C` ref:
  `Remaining`; only `E`: `Closed` or `No longer stated`; only `C`: `New`), has no limitation in
  words, or closes a limitation without naming a module of the current run as evidence; or a ref
  is written anywhere but the two ref columns (K4);
- a row of a pack measure does not print that measure's earlier and current value, with its sign
  and unit, in the right columns (K5);
- a measure the pack marks `judge` is said neither or both of `Same definition` and
  `Not comparable`, one the pack marks `no` is not said `Not comparable`, or a `Not comparable`
  row draws a trend (K6);
- a measure the two runs state for one period with different values is given the cause
  `New period` or `New source`, or is neither `Not comparable` nor `Same definition` with the
  cause `Correction` or `Method change` (K7);
- a measure the pack gives a difference of zero, and that the row does not say `Not comparable`,
  has a Cause other than `None`: nothing changed, so `Unresolved` is refused for it (K2);
- a `New` or `Not run this time` module, when the pack says both runs' modules were the pathway's
  preset (`current.selection` is `preset` and `prior.selection` is `preset` or null: a prior run
  with no recorded selection was accepted as a base only because it ran the pathway's lead
  module, so it is a whole-pathway run), has a Cause other than `Method change` or a Why that
  says the pack does not say (K12); with either run `explicit`, or a pack of the earlier shape
  (no `selection` key), nothing is required;
- a `Basis: ` line names `changes.json` or a `prior/` file, gives a page for an earlier-run
  handoff, or writes the two forms CP-8 may add in another way: `Run comparison` for the comparison
  pack and `<plain module name> (<code>), earlier run` for an earlier run's handoff (K13);
- a difference printed anywhere (a figure after `by`, or after a direction word) is not a pack
  difference, or its direction word contradicts the pack's sign, or it carries a sign after a
  direction word (K8);
- the difference of a measure that is `no`, said `Not comparable` or of one period with two values
  is printed in a checked line (K9; a measure said `Same definition` may print it in register rows,
  and a difference equal to the measure's own value is no difference);
- a figure of a checked line is held in no evidence (K10): the pack's values, the figures of its
  definition texts, the handoffs CP-8 was sent (this run's) and the earlier run's. Checked lines
  are all but the `## Request`, `## Sources`, `## Calculations` and `## Next module` sections; of
  an issuer row only the Effect cell. No figure is rounded or worked out;
- a fact row (a row naming no pack measure) prints a figure equal to a pack measure's earlier or
  current value, or one held in no evidence (K11).

A "figure" is a number that is not a date, a period label, a year or (in a passage) a whole number
below 100 without a unit (a count); in a measure's Earlier and Current cells every number counts.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from deploy_workflow.changes import PACK_NAME, PRIOR_PREFIX, decimal, number

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
COMPARISON = "Run comparison"  # CP-8's Basis item for the comparison pack; an earlier handoff is
# `<plain module name> (<code>), earlier run`
_HANDOFF_PAGE = re.compile(
    r"\(CP-[A-Z0-9]+\).*(?:\bpages?\b|\bpp?\.\s*\d)", re.IGNORECASE
)  # any page locator on a handoff item
_DOES_NOT_SAY = re.compile(r"\bthe\s+pack\s+does\s+not\s+say\b", re.IGNORECASE)
_MODULE = re.compile(r"\bCP-[A-Z0-9]+\b")
_MODULE_CELL = re.compile(r"\((CP-[A-Z0-9]+)\)$")  # the code ends the cell, in brackets
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


def _plain(text: str) -> str:
    """A cell as `page_verdicts` reads it: without bold or code marks, with every run of white space
    (a non-breaking space too) one space."""
    return " ".join(text.replace("**", "").replace("`", "").split())


def _says(row: Sequence[str], word: str) -> bool:
    """Whether a cell of the row starts with the verdict word; the word anywhere else in a cell is
    no verdict."""
    return any(_plain(cell).lower().startswith(word) for cell in row)


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


def _unchanged(measure: Mapping[str, Any]) -> bool:
    """The pack gives this measure a difference of zero: nothing changed between the runs."""
    difference = _signed(measure["difference"])
    return difference is not None and difference == 0


def _flagged(measure: Mapping[str, Any]) -> bool:
    """A measure of one period with two values: the issuer did not change, so a difference is a
    difference of definition or a correction (rule 3 of the method)."""
    difference = _signed(measure["difference"])
    return bool(measure["same_period"]) and difference is not None and difference != 0


# The net debt change's two differences, each a measure's difference (`change_in_cash` is the
# difference of the cash the pack reads from the same table; it is no measure of the pack).
_CHANGE_KEYS = (("change_in_gross_debt", "gross_debt"), ("change_in_cash", "net_debt_cash"))


def _net_debt_cash(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The net debt change's cash as a measure-shaped record (key, label, difference, values,
    same_period), so that it is withheld by the rules that withhold a measure; none when the pack
    has no net debt change or it is of two periods."""
    change = pack.get("net_debt_change")
    if not change or not change.get("same_period"):
        return []
    return [
        {
            "key": "net_debt_cash",
            "label": "Cash",
            "comparable": "yes",
            "difference": change.get("change_in_cash"),
            "prior": {"value": change.get("prior_cash")},
            "current": {"value": change.get("current_cash")},
            "same_period": True,
        }
    ]


def _pack_differences(
    pack: Mapping[str, Any], *, without: frozenset[str] = frozenset()
) -> set[Decimal]:
    """Every difference the pack gives (signed), but those of the measures named in `without`."""
    change = pack.get("net_debt_change") or {}
    rows = (pack.get("maturity_profile") or {}).get("rows", ())
    return _present(
        [
            *(_signed(m["difference"]) for m in pack["measures"] if m["key"] not in without),
            *(_signed(change.get(field)) for field, key in _CHANGE_KEYS if key not in without),
            *(_signed(row["difference"]) for row in rows),
        ]
    )


def _pack_values(pack: Mapping[str, Any]) -> set[Decimal]:
    """Every value the pack holds (signed): measures, net debt change, maturity rows."""
    change = pack.get("net_debt_change") or {}
    rows = (pack.get("maturity_profile") or {}).get("rows", ())
    found = _pack_differences(pack) | _present(
        [
            _signed(change.get(k))
            for k in (
                "prior_net_debt",
                "current_net_debt",
                "prior_gross_debt",
                "current_gross_debt",
                "prior_cash",
                "current_cash",
            )
        ]
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
    """The row's statement on whether the two values share a definition; a row that says
    `Not comparable` draws no trend."""
    text = " ".join(_plain(cell) for cell in row).lower()
    issues = []
    for word in (SAME, NOT_COMPARABLE):
        if measure["comparable"] != "no" and word in text and not _says(row, word):
            issues.append(
                f"{where}: `{word}` is a verdict only at the start of a cell; write it first in "
                "the Effect cell."
            )
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
    if NOT_COMPARABLE in text and _TREND.search(row[4]):
        issues.append(f"{where}: a `Not comparable` row draws no trend from the two values.")
    return issues


def _measure_row_issues(name: str, row: Sequence[str], measure: Mapping[str, Any]) -> list[str]:
    where = f"Issuer register, {name!r}"
    issues = _value_cell_issues(where, "earlier", row[1], measure["prior"])
    issues += _value_cell_issues(where, "current", row[2], measure["current"])
    return issues + _definition_issues(where, row, measure)


def _same_period_issues(name: str, row: Sequence[str], cause: str) -> list[str]:
    """A measure the two runs state for one period, with different values: the issuer did not
    change. The row says `Not comparable`, or `Same definition` with the cause `Correction` or
    `Method change`; never `New period` or `New source`."""
    where = f"Issuer register, {name!r}"
    if cause in ("New period", "New source"):
        return [
            (
                f"{where}: both runs state this measure for the same period, so the issuer did "
                f"not change and the cause is not `{cause}`; it is a definition "
                "(`Not comparable`), a `Correction` or a `Method change`."
            )
        ]
    if _says(row, NOT_COMPARABLE) or (_says(row, SAME) and cause in SAME_PERIOD_CAUSES):
        return []
    return [
        (
            f"{where}: both runs state this measure for the same period with different values; "
            "write `Not comparable`, or `Same definition` with the cause `Correction` or "
            "`Method change`."
        )
    ]


def _fact_row_issues(
    name: str, row: Sequence[str], pack: Mapping[str, Any], held: frozenset[Decimal]
) -> list[str]:
    """A row naming no pack measure: no cell prints a difference of the pack, its label, Earlier and
    Current cells print no value of a pack measure (that is the measure's own row) and only figures
    held in the evidence."""
    own = {
        abs(value)
        for measure in pack["measures"]
        for side in ("prior", "current")
        if (value := _signed((measure[side] or {}).get("value"))) is not None
    }
    differences = _pack_differences(pack)
    sizes = {abs(d) for d in differences if d != 0}
    issues = []
    for index in (0, 1, 2, 4):
        cell = row[index]
        for figure in dict.fromkeys(f.size for f in _figures(cell, counts=False)):
            if figure in sizes and figure not in own:
                issues.append(
                    f"Issuer register, {name!r}: the figure {figure} is a difference of the pack; "
                    "a difference belongs to its measure's own row, not to a fact row."
                )
            elif index == 4:
                continue
            elif figure in own:
                issues.append(
                    f"Issuer register, {name!r}: the figure {figure} is a value of a pack measure; "
                    "name a pack measure by its exact label in that measure's own row."
                )
            elif figure not in held | _evidence(pack):
                issues.append(_not_held(f"Issuer register, {name!r}", figure))
        if index != 4:
            issues += _direction_issues(cell, differences, f"Issuer register, {name!r}")
    return issues


def _rows_by_measure(
    rows: Sequence[list[str]], pack: Mapping[str, Any]
) -> dict[str, list[list[str]]]:
    """The issuer rows of each pack measure (by key), a row's label read through `_plain`: the one
    reading of which row is a measure's, shared by the check and the page's verdicts."""
    keys = {m["label"]: m["key"] for m in pack["measures"]}
    found: dict[str, list[list[str]]] = {}
    for row in rows:
        key = keys.get(_plain(row[0]))
        if key is not None:
            found.setdefault(key, []).append(row)
    return found


def _module_code(cell: str) -> str | None:
    """The module code a cell of the analysis register ends with, in brackets (`Name (CP-2)`)."""
    named = _MODULE_CELL.search(_plain(cell))
    return named[1] if named else None


def _rows_by_module(rows: Sequence[list[str]]) -> dict[str, list[list[str]]]:
    """The analysis rows of each module code their first cell names."""
    found: dict[str, list[list[str]]] = {}
    for row in rows:
        code = _module_code(row[0])
        if code is not None:
            found.setdefault(code, []).append(row)
    return found


def _alnum(text: str) -> str:
    """A label as it looks: NFKC, only letters and digits, case folded."""
    return "".join(c for c in unicodedata.normalize("NFKC", text) if c.isalnum()).casefold()


def _issuer_issues(
    rows: list[list[str]], pack: Mapping[str, Any], held: frozenset[Decimal] = frozenset()
) -> list[str]:
    issues: list[str] = []
    if not rows:
        return [f"`### {ISSUER}` needs a row; if nothing changed, one `{NO_CHANGE}` row."]
    labels = {m["label"]: m for m in pack["measures"]}
    looks_like = {_alnum(label) for label in labels}
    first = {key: found[0] for key, found in _rows_by_measure(rows, pack).items()}
    for row in rows:
        name, cause = row[0], row[3]
        if name.strip().strip("*") == NO_CHANGE:
            if cause != "None":
                issues.append(f"The `{NO_CHANGE}` row's Cause is `None`.")
            continue
        measure = labels.get(_plain(name))
        if measure is None and _alnum(name) in looks_like:
            issues.append(
                f"Issuer register, {name!r}: the label looks like a pack measure's but is not "
                "its exact label (a hidden character?); name a pack measure by its exact label."
            )
            continue
        if measure is not None and first[measure["key"]] is not row:
            issues.append(
                f"Issuer register, {name!r}: a second row for this pack measure; write one "
                "row per measure."
            )
            continue
        flagged = measure is not None and _flagged(measure)
        unchanged = measure is not None and _unchanged(measure) and not _says(row, NOT_COMPARABLE)
        causes = (*ISSUER_CAUSES, *(SAME_PERIOD_CAUSES if flagged else ()))
        if unchanged:
            if cause != "None":
                issues.append(
                    f"Issuer register, {name!r}: Cause {cause!r} is not `None`; the pack's "
                    "difference is zero, so nothing changed (`Unresolved` is for a change whose "
                    "cause is not known)."
                )
        elif cause not in causes:
            issues.append(
                f"Issuer register, {name!r}: Cause {cause!r} is not one of "
                + ", ".join(f"`{c}`" for c in causes)
                + " (an analysis change belongs in the analysis register)."
            )
        if measure is None:
            issues += _fact_row_issues(name, row, pack, held)
            continue
        issues += _measure_row_issues(name, row, measure)
        if flagged:
            issues += _same_period_issues(name, row, cause)
    return issues


def _preset_issues(code: str, cause: str, why: str) -> list[str]:
    """A module that ran in one run only, between two runs of the pathway's own module set: the
    pathway's module set changed, so the cause is known (`Method change`) and the pack is not
    said to lack it."""
    issues = []
    if cause != "Method change":
        issues.append(
            f"Analysis register, {code}: both runs used the pathway's own modules, so the "
            f"pathway's module set changed between them: the Cause is `Method change`, "
            f"not {cause!r}."
        )
    if _DOES_NOT_SAY.search(why):
        issues.append(
            f"Analysis register, {code}: both runs used the pathway's own modules, so the words "
            "`the pack does not say` are refused: say that the pathway's module set changed "
            "between the runs."
        )
    return issues


def _analysis_issues(rows: list[list[str]], pack: Mapping[str, Any]) -> list[str]:
    issues = []
    ran = {m["module"]: (m["ran_prior"], m["ran_current"]) for m in pack["modules"]}
    seen = {code: len(found) for code, found in _rows_by_module(rows).items() if code in ran}
    prior, current = pack.get("prior") or {}, pack.get("current") or {}
    # An absent `selection` key is a pack of the earlier shape; a null is a run that predates it.
    both_preset = (
        "selection" in prior
        and current.get("selection") == "preset"
        and prior["selection"] in ("preset", None)
    )
    for module, status, cause, why in rows:
        code = _module_code(module)
        if code is None or code not in ran:
            issues.append(
                f"Analysis register: {module!r} does not name one module of the pack; the cell "
                "ends with its code in brackets, as `Credit view (CP-2)`."
            )
            continue
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
        if both_preset and status in ("New", "Not run this time"):
            issues += _preset_issues(code, cause, why)
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


def _evidence(pack: Mapping[str, Any]) -> frozenset[Decimal]:
    """The sizes the pack itself holds: every value, and the figures of its definition texts."""
    sizes = {abs(v) for v in _pack_values(pack)}
    for measure in pack["measures"]:
        for side in ("prior", "current"):
            for key in ("definition", "definition_written"):
                text = (measure[side] or {}).get(key)
                sizes |= {f.size for f in _figures(text)} if isinstance(text, str) else set()
    return frozenset(sizes)


def _not_held(where: str, size: Decimal) -> str:
    return (
        f"{where}: the figure {size} is held in neither the comparison pack nor a handoff of "
        "either run; CP-8 copies figures exactly and never rounds or calculates."
    )


def _withheld(pack: Mapping[str, Any], said_nc: frozenset[str]) -> frozenset[str]:
    """Measures whose difference a reader is not given: the pack marks them `no`, CP-8's row says
    `Not comparable`, or both runs state them for one period with different values."""
    return frozenset(
        m["key"]
        for m in (*pack["measures"], *_net_debt_cash(pack))
        if m["comparable"] == "no" or m["key"] in said_nc or _flagged(m)
    )


def _withheld_sizes(
    pack: Mapping[str, Any], said_nc: frozenset[str], *, register: bool
) -> dict[Decimal, str]:
    """The non-zero differences a checked line may not print, with their measure's label. A measure
    of one period with two values, not said `Not comparable`, may print its difference in register
    rows; a difference equal to a value of its own measure is no difference."""
    found: dict[Decimal, str] = {}
    for measure in (*pack["measures"], *_net_debt_cash(pack)):
        difference = _signed(measure["difference"])
        barred = measure["comparable"] == "no" or measure["key"] in said_nc
        if difference is None or difference == 0 or not (barred or _flagged(measure)):
            continue
        if register and not barred:
            continue
        if abs(difference) not in {abs(v) for v in _measure_values(measure) - {difference}}:
            found[abs(difference)] = measure["label"]
    return found


def _passage_issues(
    lines: list[str],
    pack: Mapping[str, Any],
    said_nc: frozenset[str] = frozenset(),
    held: frozenset[Decimal] = frozenset(),
) -> list[str]:
    """What the handoff prints outside the registers' value cells. `held` is the sizes of the
    figures of the handoffs CP-8 was sent; the pack's own are added.

    - Differences, anywhere (K8): a figure after `by` or a direction word is a pack difference in
      the pack's direction.
    - Every checked line (all but the `## Request`, `## Sources`, `## Calculations` and
      `## Next module` sections; of an issuer row the Effect cell only): the difference of a
      withheld measure is not printed (K9) and every other figure is held in the evidence (K10)."""
    allowed = held | _evidence(pack)
    withheld = _withheld(pack, said_nc)
    barred = frozenset(
        m["key"] for m in pack["measures"] if m["comparable"] == "no" or m["key"] in said_nc
    )
    passage_differences = _pack_differences(pack, without=withheld)
    register_differences = _pack_differences(pack, without=barred)
    kept = {
        False: _withheld_sizes(pack, said_nc, register=False),
        True: _withheld_sizes(pack, said_nc, register=True),
    }
    in_issuer, h2 = False, ""
    issues: list[str] = []
    for line in lines:
        if _HEADING.match(line):
            in_issuer = line.strip() == f"### {ISSUER}"
            if line.startswith("## "):
                h2 = line[3:].strip()
        text = line.strip()
        row = text.startswith("|") and text.endswith("|")
        if in_issuer and row:
            line = re.split(r"(?<!\\)\|", text[1:-1])[-1]
        issues += _direction_issues(
            line, register_differences if row else passage_differences, "A passage"
        )
        if h2 in NOT_PASSAGES:
            continue
        for size in dict.fromkeys(f.size for f in _figures(line, counts=False)):
            if size in kept[row]:
                issues.append(
                    f"A passage: the figure {size} is the difference of {kept[row][size]}, which "
                    "this handoff withholds (not comparable, or one period with two values); a "
                    "difference of it is not printed here."
                )
            elif size not in allowed:
                issues.append(_not_held("A passage", size))
    return issues


def _basis_issues(lines: Sequence[str]) -> list[str]:
    """CP-8's Basis items: the comparison pack is `Run comparison`, an earlier run's handoff is
    `<plain module name> (<code>), earlier run`; no pipeline file name and no page of a handoff."""
    issues = []
    for line in lines:
        text = line.strip()
        if not text.startswith("Basis: "):
            continue
        for item in (i.strip() for i in text.removeprefix("Basis: ").removesuffix(".").split("; ")):
            if PACK_NAME in item or PRIOR_PREFIX in item:
                issues.append(
                    f"Basis item {item!r} names a pipeline file; write the comparison pack as "
                    f"`{COMPARISON}` and an earlier run's handoff as `<plain module name> "
                    "(<code>), earlier run`."
                )
            elif item.startswith(COMPARISON) and item != COMPARISON:
                issues.append(
                    f"Basis item {item!r}: the comparison pack is exactly `{COMPARISON}`."
                )
            elif _HANDOFF_PAGE.search(item):
                issues.append(
                    f"Basis item {item!r} gives a page for a handoff; a handoff is "
                    "`<plain module name> (<code>)`, or `<plain module name> (<code>), earlier "
                    "run` for the earlier run, with no page."
                )
    return issues


def cp8_issues(text: str, pack: Mapping[str, Any], held: Sequence[str] = ()) -> tuple[str, ...]:
    """Every failure of the CP-8 handoff `text` against its comparison pack (none: accepted).
    `held` is the texts CP-8 was sent beside the pack: this run's handoffs and the earlier run's."""
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
    sizes = frozenset(f.size for evidence in held for f in _figures(evidence))
    if ISSUER in tables:
        issues += _issuer_issues(tables[ISSUER][1], pack, sizes)
    if ANALYSIS in tables:
        issues += _analysis_issues(tables[ANALYSIS][1], pack)
    if LEDGER in tables:
        issues += _ledger_issues(tables[LEDGER][1], pack)
    issuer = tables[ISSUER][1] if ISSUER in tables else []
    said_nc = frozenset(
        key
        for key, found in _rows_by_measure(issuer, pack).items()
        if any(_says(row, NOT_COMPARABLE) for row in found)
    )
    issues += _basis_issues(lines)
    issues += _outside_ref_issues(lines, pack)
    issues += _passage_issues(lines, pack, said_nc, sizes)
    return tuple(dict.fromkeys(issues))


def _verdict(
    kind: str, label: str, reason: str | None, change: str | None = None
) -> dict[str, str | None]:
    return {"kind": kind, "label": label, "reason": reason, "analysis_change": change}


def _page_measure(measure: Mapping[str, Any], found: list[list[str]]) -> dict[str, str | None]:
    """The verdict the Changes tab shows for one pack measure, from the pack and its issuer rows
    (the first rule that applies):

    1. the pack says `no`: not comparable, with the pack's reason;
    2. a row says `Not comparable`: not comparable, with that row's Effect cell;
    3. two rows, a row the check would refuse on its definition statement, or (one period with two
       values) one it would refuse on that: not judged;
    4. one period with two values: `Same definition`, with the row's Cause as the analysis change,
       when the row says it, else not judged;
    5. the pack says `yes`: comparable;
    6. the single row says `Same definition`: comparable;
    7. otherwise not judged."""
    unjudged = _verdict("unjudged", "Comparability not judged", measure.get("reason"))
    if measure["comparable"] == "no":
        return _verdict("not_comparable", "Not comparable", measure.get("reason"))
    for said_not in found:
        if _says(said_not, NOT_COMPARABLE):
            return _verdict("not_comparable", "Not comparable", said_not[4])
    row = found[0] if found else None
    flagged = _flagged(measure)
    where = measure["label"]
    refused = row is not None and (
        _definition_issues(where, row, measure)
        or (flagged and bool(_same_period_issues(where, row, row[3])))
    )
    if len(found) > 1 or refused:
        return unjudged
    said = row is not None and _says(row, SAME)
    if flagged:
        change = row[3] or "Not stated by CP-8" if row is not None else None
        return _verdict("comparable", "Same definition", None, change) if said else unjudged
    if measure["comparable"] == "yes":
        return _verdict("comparable", "Comparable", None)
    return _verdict("comparable", "Same definition", None) if said else unjudged


def _ledger_counts(rows: list[list[str]] | None) -> list[list[Any]] | None:
    """The ledger rows counted per Status (`LEDGER_STATUSES` in order, then `Other` when any row has
    another); None when the ledger has no readable table."""
    if rows is None:
        return None
    counts: list[list[Any]] = [
        [s, sum(1 for r in rows if _plain(r[3]) == s)] for s in LEDGER_STATUSES
    ]
    if other := len(rows) - sum(n for _, n in counts):
        counts.append(["Other", other])
    return counts


def page_verdicts(text: str | None, pack: Mapping[str, Any]) -> dict[str, Any]:
    """What the Changes tab shows of CP-8's registers, read once, here: the page never parses a
    register for a verdict. `text` is CP-8's handoff (None: none is held). A register that is
    missing or malformed counts as having no rows.

    - `measures`: per pack measure key, `{kind, label, reason, analysis_change}` (`_page_measure`);
    - `modules`: per pack module whose code has exactly one analysis row, its `status`, `cause`
      and `why`;
    - `ledger`: the count of ledger rows per status (`LEDGER_STATUSES`, then `Other`), or None when
      the ledger has no readable table."""
    lines = (text or "").replace("\r\n", "\n").split("\n")

    def rows_of(title: str) -> list[list[str]] | None:
        found = _section(lines, title)
        if isinstance(found, str) or _columns(found, title):
            return None
        return found[1]

    by_measure = _rows_by_measure(rows_of(ISSUER) or [], pack)
    measures = {m["key"]: _page_measure(m, by_measure.get(m["key"], [])) for m in pack["measures"]}
    by_module = _rows_by_module(rows_of(ANALYSIS) or [])
    modules = {}
    for m in pack["modules"]:
        once = by_module.get(m["module"], [])
        if len(once) == 1:
            modules[m["module"]] = {"status": once[0][1], "cause": once[0][2], "why": once[0][3]}
    return {"measures": measures, "modules": modules, "ledger": _ledger_counts(rows_of(LEDGER))}
