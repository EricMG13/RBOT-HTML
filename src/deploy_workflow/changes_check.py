"""The check of CP-8's handoff against its comparison pack. Pure: no I/O, no provider.

CP-8 explains and never calculates (owner, 2026-11-11). Beside the prose checks every handoff
meets, this module refuses, naming the line, a CP-8 handoff in which:

- one of the three registers (`### What changed: the issuer`, `### What changed: the analysis`,
  `### Limitations ledger`) is missing, repeated, has other columns, or has no row;
- a Status or Cause is not from its fixed list, an issuer row has an analysis-only cause, a
  `Presentation` cause is not on an `Unchanged` row, or a `None` cause is not on `Unchanged` or on
  the single `No material change` row;
- a module of the pack has no analysis row, has two, or the row's Status contradicts the pack
  (`New` only when the module ran now and not before, `Not run this time` only the reverse, neither
  for a module that ran in both);
- a limitation of the pack has no ledger row, has two, a row names none of the pack's, or its Status
  contradicts the pack (both runs state it: `Remaining`; only the current: `New`; only the earlier:
  `Closed` or `No longer stated`); a `Closed` row's last cell does not name a module that ran in
  the current run (the evidence);
- a figure of the issuer register is not a value in the pack (compared as Decimal, sign aside;
  dates, period labels, years and whole numbers below 100 are not figures), or an earlier or
  current cell of a row naming a pack measure holds a figure other than that run's value for the
  measure, or a row naming a measure the pack marks not comparable does not say "not comparable".
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from deploy_workflow.changes import decimal, number
from deploy_workflow.prose_checks import normalise_limitation

ISSUER = "What changed: the issuer"
ANALYSIS = "What changed: the analysis"
LEDGER = "Limitations ledger"
COLUMNS = {
    ISSUER: ("Measure or fact", "Earlier", "Current", "Cause", "Effect on the credit view"),
    ANALYSIS: ("Module", "Status", "Cause", "Why"),
    LEDGER: ("Limitation", "Status", "What closed it"),
}
STATUSES = ("Unchanged", "Strengthened", "Weakened", "Reversed", "New", "Not run this time")
CAUSES = ("New period", "New source", "Method change", "Correction", "Presentation", "Unresolved")
ISSUER_CAUSES = ("New period", "New source", "Unresolved")
LEDGER_STATUSES = ("Closed", "Remaining", "New", "No longer stated")
NO_CHANGE = "No material change"
_MODULE = re.compile(r"\bCP-[A-Z0-9]+\b")
_FIGURE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")
_EXEMPT = re.compile(
    r"\d{4}-\d{2}(?:-\d{2})?|\b(?:FY|CY)\d{2,4}E?\b|\b[QH][1-4]\b|\bLTM\b|\b\d+M\b|\b(?:19|20)\d{2}\b"
)
_NOT_EVIDENCE = frozenset({"", "-", "—", "–", "n/a", "none", "not stated"})


def _section(lines: list[str], title: str) -> tuple[list[str], list[list[str]]] | str:
    """(header, rows) of the one table under `### title`, or why there is none."""
    starts = [i for i, line in enumerate(lines) if line.strip() == f"### {title}"]
    if len(starts) != 1:
        return f"`### {title}` must appear exactly once (found {len(starts)})."
    rows: list[list[str]] = []
    for line in lines[starts[0] + 1 :]:
        if re.match(r"#{1,6}\s", line):
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


_UNIT_AFTER = re.compile(
    r"\s*(?:%|x\b|bps?\b|pp\b|m\b|bn\b|k\b|million|billion|thousand|percent|per cent|times|"
    r"percentage points|[A-Z]{3}\b|[A-Za-z]{0,2}[$€£¥])",
    re.IGNORECASE,
)
_CURRENCY_BEFORE = re.compile(r"(?:[$€£¥]|\b[A-Z]{3}) ?$")


def _numbers(cell: str, *, effect: bool = False) -> list[Decimal]:
    """The figures of a cell, as absolute Decimal values: every number that is not part of a date,
    period label or year. In a prose cell (`effect`) a whole number below 100 is a count and not a
    figure unless it carries a unit or a currency."""
    masked = _EXEMPT.sub(" ", cell)
    found = []
    for match in _FIGURE.finditer(masked):
        token = match[0]
        small = "." not in token and "," not in token and int(token) < 100
        united = _UNIT_AFTER.match(masked, match.end()) or _CURRENCY_BEFORE.search(
            masked[max(0, match.start() - 4) : match.start()]
        )
        if effect and small and not united:
            continue
        found.append(abs(decimal(token)))
    return found


def _pack_values(pack: Mapping[str, Any]) -> set[Decimal]:
    values: set[str | None] = set()
    for measure in pack["measures"]:
        values.add(measure["difference"])
        values.update((measure[side] or {}).get("value") for side in ("prior", "current"))
    bridge = pack.get("net_debt_bridge") or {}
    values.update(v for k, v in bridge.items() if k != "unit")
    for row in (pack.get("maturity_profile") or {}).get("rows", ()):
        values.update((row["prior"], row["current"], row["difference"]))
    return {abs(decimal(v)) for v in values if v is not None and number(v) is not None}


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


def _issuer_issues(rows: list[list[str]], pack: Mapping[str, Any]) -> list[str]:
    issues = []
    allowed = _pack_values(pack)
    measures = pack["measures"]
    if not rows:
        return [f"`### {ISSUER}` needs a row; if nothing changed, one `{NO_CHANGE}` row."]
    for row in rows:
        name, earlier, current, cause, effect = row
        if name.strip().strip("*") == NO_CHANGE:
            if cause != "None":
                issues.append(f"The `{NO_CHANGE}` row's Cause is `None`.")
            continue
        if cause not in ISSUER_CAUSES:
            issues.append(
                f"Issuer register, {name!r}: Cause {cause!r} is not one of "
                + ", ".join(f"`{c}`" for c in ISSUER_CAUSES)
                + " (an analysis change belongs in the analysis register)."
            )
        for cell, prose in ((earlier, False), (current, False), (effect, True)):
            issues += [
                f"Issuer register, {name!r}: the figure {value} is not in the comparison pack; "
                "CP-8 never calculates."
                for value in dict.fromkeys(_numbers(cell, effect=prose))
                if value not in allowed
            ]
        for measure in (m for m in measures if m["label"].lower() == _plain(name)):
            for side, cell in (("prior", earlier), ("current", current)):
                stated = (measure[side] or {}).get("value")
                held = {abs(decimal(stated))} if stated is not None and number(stated) else set()
                issues += [
                    f"Issuer register, {name!r}: {side} figure {value} is not the pack's "
                    f"{side} value ({stated})."
                    for value in dict.fromkeys(_numbers(cell))
                    if value not in held
                ]
            if not measure["comparable"] and "not comparable" not in " ".join(row).lower():
                issues.append(
                    f"Issuer register, {name!r}: the pack marks this measure not comparable "
                    f'({measure["reason"]}); say "not comparable" and give no difference.'
                )
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


def _ledger_issues(rows: list[list[str]], pack: Mapping[str, Any]) -> list[str]:
    issues = []
    wanted = {row["key"]: row for row in pack["limitations"]}
    ran_now = {m["module"] for m in pack["modules"] if m["ran_current"]}
    seen: dict[str, int] = {}
    for text, status, closed in rows:
        key = normalise_limitation(text)
        if key not in wanted:
            issues.append(
                f"Limitations ledger: {text[:60]!r} is not a limitation in the pack; "
                "copy its text exactly."
            )
            continue
        seen[key] = seen.get(key, 0) + 1
        row = wanted[key]
        expected = (
            ("Remaining",)
            if row["prior"] and row["current"]
            else ("New",)
            if row["current"]
            else ("Closed", "No longer stated")
        )
        if status not in LEDGER_STATUSES:
            issues.append(f"Limitations ledger: Status {status!r} is not one of {LEDGER_STATUSES}.")
        elif status not in expected:
            issues.append(
                f"Limitations ledger, {text[:60]!r}: the pack says "
                f"{' or '.join(expected)}, not {status!r}."
            )
        elif status == "Closed" and not (
            closed.strip().lower() not in _NOT_EVIDENCE and set(_MODULE.findall(closed)) & ran_now
        ):
            issues.append(
                f"Limitations ledger, {text[:60]!r}: `Closed` needs evidence in the current run: "
                "name the module whose handoff shows it and say what it shows; "
                "otherwise `No longer stated`."
            )
    issues += [
        f"Limitations ledger: {row['text'][:60]!r} needs exactly one row "
        f"(found {seen.get(key, 0)})."
        for key, row in wanted.items()
        if seen.get(key, 0) != 1
    ]
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
    return tuple(issues)
