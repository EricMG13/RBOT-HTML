"""What changed since the last run: which earlier run CP-8 compares with, and the comparison pack.

Owner, 2026-11-11: CP-8 answers "what has changed since the last time I looked at this", in the
run itself. Everything here is Python and reads files only; nothing calls a provider.

Prior run (`find_prior`, one rule). Among the runs the issuer library lists (`library_index
.admit_run`: completed, answered in their own run, earlier-format and earlier-methods runs
included), those that are a comparison base and have the same issuer ID (compared without regard
to case), pathway and case kind, an issuer name equal after case and whitespace folding, and an
as-of date on or before this run's, excluding this run's own folder. A run is a comparison base
when its manifest records `selection: "preset"` (the pathway's own modules) and is not when it
records `"explicit"` (a `--modules` subset); an older run that records neither is a base only if
it delivered the pathway's lead module (`LEAD_MODULE`: CP-2, CP-1B for an earnings update, CP-L10
for a short snapshot). A candidate that fails a test is never used and the reason is returned in
`skipped`. The latest is chosen by (as-of date, first model-call start, folder name). None means
no CP-8: the run records "first run of this pathway". The prior run's folder is read, never
written. `prepare` copies its delivered handoffs into the run folder as `prior/<module>.md` and
pins them as sources; a resume reuses those pins. A chosen run with a handoff that is not valid
UTF-8 is not compared (reason in `skipped`).

The pack (`build_pack`) is computed before CP-8 is called, given to CP-8 as the source
`changes.json` and published unchanged in the delivery as `changes.json`. Schema
`cpos-changes/3` (the library also reads `cpos-changes/2`, which lacks `selection`; every number is
a decimal string; missing is null, never zero):

- `prior`: `{run, as_of, pathway, format: "current"|"earlier", methods_changed: [text], selection}`;
  `current`: `{as_of, pathway, format, selection}`. `selection` is `"preset"` when the run's modules
  were the pathway's own, `"explicit"` for a `--modules` subset and null when the run's manifest
  records neither. When a module is `New` or `Not run this time` and both are `"preset"`, the
  pathway's module set changed between the runs (CP-8's cause is `Method change`).
- `measures`: a list of `{key, label, unit, comparable, reason, prior, current, difference,
  same_period}`; `prior` and `current` are `{label, unit, value, period, definition,
  definition_resolved, definition_written}` or null when the run does
  not state the measure. `difference` is current minus prior, computed here with Decimal whenever
  both values are stated and the units are equal. `comparable` is "no" when the units differ or a
  value or a run is missing (no difference), "yes" when the label and the definition texts (the
  table's "Basis and limitation") are equal once digits, page and locator words and punctuation
  are removed, and otherwise "judge": the difference is given, both definition texts are in the
  pack, and CP-8 states for that row `Same definition` or `Not comparable` (the checker enforces
  it). `reason` says why there is no difference or why a judgement is needed. `same_period` is true
  when both runs state the measure for the same fiscal year or period (`FY2024 / 2024-09-30` and
  `FY2024` are the same): two values for one period mean a definition or a correction, never the
  issuer changing. `definition` is the table's basis text, but where it says `identical definition`
  or `same measure` it is the basis of the table's row for the period before (`definition_resolved`
  true, the text as written in `definition_written`); a pointer by calculation ID is not followed
  (`definition_resolved` false). A year after an instrument word (`notes 2027`, `due 2030`) is part
  of the definition; page and locator numbers are not.
- `net_debt_change`: `{unit, prior_net_debt, change_in_gross_debt, change_in_cash,
  current_net_debt, convention}`, only when both runs state gross debt, net debt and cash in one
  unit (gross and net debt are read only from the Gross debt and Net debt columns of CP-1's
  `### Net debt data` table; a run without that table does not state them, and `omitted` says
  which run), each under the same definition ("yes"), and each
  run's net debt is its gross debt less its cash. A two-point identity of stated balances; it does
  not say what drove the change. An increase in cash reduces net debt.
- `maturity_profile`: `{unit, rows: [{period, prior, current, difference}]}` from the CP-1
  "Chart data: debt maturities" tables (the table directly under that heading), only when both
  runs have one in one unit.
- `omitted`: `{net_debt_change|maturity_profile: reason}` for each of the two left out.
- `modules`: `{module, title, ran_prior, ran_current, prior_bottom_line, current_bottom_line}` for
  every module in either run (CP-8 excluded): the first paragraph of `### Bottom line`, Basis line
  dropped; for an earlier-format handoff the "Bottom line" cell of its Reader summary; else null.
- `limitations`: `{earlier: [{ref, module, text}], current: [{ref, module, text}]}`: each item of
  either run's `### Limitations` (an earlier-format handoff: its Reader summary's "Main
  limitation"; a "No limitation changes ..." item is not a limitation) with a ref, `E1`, `E2` ...
  for the earlier run and `C1`, `C2` ... for the current one, in the order the handoffs are given
  (a run's modules in the order they ran), then the order in the handoff. CP-8 pairs them by
  meaning; Python does not.
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from deploy_vii.contracts import Contract, Identifier
from deploy_workflow.credit_os_catalogue import CHART_PREFIX, chart_row, period_order
from deploy_workflow.library_index import (
    MethodHeadings,
    MethodText,
    Refused,
    admit_run,
    current_method,
    json_object,
    module_titles,
    read_inside,
    read_pinned,
    reader_summary,
)
from deploy_workflow.prose_checks import (
    bottom_line_text,
    is_earlier_format,
    limitation_texts,
    normalise_limitation,
)

log = logging.getLogger(__name__)

PRIOR_PREFIX = "prior/"
PACK_NAME = "changes.json"
PACK_SCHEMA = "cpos-changes/3"
PACK_SCHEMAS = ("cpos-changes/2", PACK_SCHEMA)  # the shapes the library reads
FIRST_RUN = "first run of this pathway"
DELIVERED_WHOLE = " The changes since the last run are CP-8's handoff, delivered whole."
NO_LIMITATION = re.compile(r"no limitation changes\b", re.IGNORECASE)
NOT_SUPPLIED = "Not supplied"
NET_DEBT_TABLE = "Net debt data"  # CP-1's period-row table of gross debt, cash and net debt
# (key, CP-1 period-row table, value column): the five measures the library already quotes, then
# gross and net debt from the net debt table (owner, 2026-11-12, "Yes, add it"). The tables are
# `### Chart data: <name>`, except the net debt table, which the library does not draw.
CHART_MEASURES = (
    ("leverage", "leverage", "Total debt / EBITDA"),
    ("net_leverage", "leverage", "Net debt / EBITDA"),
    ("coverage", "interest cover", "EBITDA / cash interest"),
    ("cash", "liquidity", "Cash"),
    ("undrawn", "liquidity", "Undrawn committed facilities"),
    ("gross_debt", NET_DEBT_TABLE, "Gross debt"),
    ("net_debt", NET_DEBT_TABLE, "Net debt"),
)
# (key, row labels): read from the one CP-1 table row of that label, only when it states its unit.
ROW_MEASURES = (("free_cash_flow", ("free cash flow", "fcf")),)
# The net debt table's own Cash column: the cash of the net debt change, read from the same row as
# gross and net debt. It is not a measure of the pack (the liquidity table's `cash` is).
NET_DEBT_CASH = ("net_debt_cash", NET_DEBT_TABLE, "Cash")
MATURITIES = "debt maturities"
NET_DEBT_CONVENTION = (
    "net debt = gross debt - cash: an increase in cash reduces net debt, a decrease raises it; "
    "a two-point identity of the stated balances, not an analysis of what drove the change"
)
# The module a pathway's run is built around; an older run that did not record whether its
# modules were the preset's or a subset is a comparison base only if it delivered this one.
LEAD_MODULE = {"earnings_update": "CP-1B", "short_snapshot": "CP-L10"}
DEFAULT_LEAD = "CP-2"


class PriorRun(Contract):
    """The earlier run CP-8 compares with, as the manifest records it."""

    folder: str
    run_id: Identifier
    as_of: str
    pathway: str
    earlier_format: bool
    methods_changed: tuple[str, ...]
    started_at: str | None
    modules: tuple[str, ...]
    # How the run's modules were chosen, as its manifest records it (None: not recorded).
    selection: Literal["preset", "explicit"] | None = Field(
        default=None, exclude_if=lambda v: v is None
    )


def workspace_of(directory: Path) -> Path | None:
    """The workspace a run folder belongs to: the folder holding `runs/`, by the rule the launcher
    uses to refresh the library; None when the run folder is not directly inside a `runs` folder."""
    return directory.parent.parent if directory.parent.name == "runs" else None


def _fold(name: str) -> str:
    return " ".join(name.casefold().split())


def _not_a_base(
    workflow: Mapping[str, Any],
    run: Mapping[str, Any],
    delivered: Sequence[str],
    me: Mapping[str, str],
) -> str | None:
    """Why a run of the same issuer and pathway is not a comparison base, or None when it is."""
    if _fold(str(run.get("issuer_name", ""))) != _fold(me["issuer_name"]):
        return f"its issuer name is {run.get('issuer_name')!r}, not {me['issuer_name']!r}"
    if run.get("case_kind") != me["case_kind"]:
        return f"its case kind is {run.get('case_kind')!r}, not {me['case_kind']!r}"
    selection = workflow.get("selection")
    if selection == "explicit":
        return "it was launched with an explicit module subset"
    if selection is None:
        lead = LEAD_MODULE.get(me["pathway"], DEFAULT_LEAD)
        if lead not in delivered:
            return f"it records no module selection and did not run {lead}"
    elif selection != "preset":
        return f"its module selection {selection!r} is not understood"
    return None


def find_prior(  # noqa: PLR0913 - the identity of the run and the library's method record
    workspace: Path,
    *,
    folder: str,
    issuer_id: str,
    issuer_name: str,
    case_kind: str,
    pathway: str,
    as_of: str,
    method: tuple[MethodText, MethodHeadings] | None = None,
    only: str | None = None,
    skipped: list[str] | None = None,
) -> tuple[PriorRun, dict[str, bytes]] | None:
    """The prior run (the rule in this module's docstring) and its delivered handoffs, or None.

    A folder the library would not list is not a candidate: it is skipped, as the library skips
    it. An unreadable one is logged; a refusal is the library's own record of why it is not
    listed, so it is logged at debug level only. A run of the same issuer and pathway that is not
    a comparison base, or whose delivered handoff cannot be read, is never used, and the reason is
    appended to ``skipped`` (one line per run) and logged once. ``only`` limits the candidates to
    the run folder of that name."""
    method = method or current_method()
    runs = workspace / "runs"
    reasons = skipped if skipped is not None else []
    me = {"issuer_name": issuer_name, "case_kind": case_kind, "pathway": pathway}
    found: list[tuple[tuple[str, str, str], dict[str, Any], Mapping[str, Any], Any]] = []
    for name in sorted(os.listdir(runs)) if runs.is_dir() else []:
        path = runs / name
        if name == folder or name.startswith(".") or path.is_symlink() or not path.is_dir():
            continue
        if only is not None and name != only:
            continue
        try:
            workflow = json_object(read_inside(path, "workflow.json"), "workflow.json")
            run = workflow.get("run")
            if (
                not isinstance(run, dict)
                or not isinstance(run.get("issuer_id"), str)
                or run["issuer_id"].casefold() != issuer_id.casefold()
                or run.get("pathway") != pathway
                or not isinstance(run.get("as_of"), str)
                or run["as_of"] > as_of
            ):
                continue
            deliveries: dict[str, dict[str, Any]] = {}
            record = admit_run(path, workspace / "library", method, deliveries)
            why = _not_a_base(workflow, run, tuple(deliveries[name]["handoffs"]), me)
        except Refused as refusal:
            log.debug("earlier run %s is not listed: %s", name, refusal)
            continue
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
            log.warning("earlier run %s is unreadable and is not compared: %r", name, error)
            continue
        if why is not None:
            reasons.append(f"{name}: {why}")
            log.warning("earlier run %s is not a comparison base: %s", name, why)
            continue
        started = record["execution"].get("started_at") or ""
        found.append(
            ((record["as_of"], started, name), record, deliveries[name], workflow.get("selection"))
        )
    if not found:
        return None
    _, record, delivered, selection = max(found, key=lambda item: item[0])
    handoffs = {
        module: read_pinned(runs / record["id"], pin["path"], pin["sha256"])
        for module, pin in delivered["handoffs"].items()
        if module != "CP-8"
    }
    texts = {}
    for module, raw in handoffs.items():
        try:
            texts[module] = raw.decode("utf-8")
        except UnicodeDecodeError:
            why = f"its delivered {module} handoff is not valid UTF-8"
            reasons.append(f"{record['id']}: {why}")
            log.warning("earlier run %s is not compared: %s", record["id"], why)
            return None
    prior = PriorRun(
        folder=record["id"],
        run_id=record["run_id"],
        as_of=record["as_of"],
        pathway=record["pathway"],
        earlier_format=any(is_earlier_format(text) for text in texts.values()),
        methods_changed=tuple(record["method_changes"]),
        started_at=record["execution"].get("started_at"),
        modules=tuple(handoffs),
        selection=selection,
    )
    return prior, handoffs


def prior_sources(prior: PriorRun) -> dict[str, str]:
    """Source name -> path (inside the run folder) of each pinned copy of a prior handoff."""
    return {f"{PRIOR_PREFIX}{module}.md": f"{PRIOR_PREFIX}{module}.md" for module in prior.modules}


def describe_run(prior: PriorRun) -> str:
    """The earlier run in words: pathway, as-of date, folder and any caveat on the comparison."""
    flags = ", ".join(
        [
            *(["earlier format"] if prior.earlier_format else []),
            *(["earlier methods"] if prior.methods_changed else []),
        ]
    )
    caveat = f"; {flags}" if flags else ""
    return f"the {prior.pathway} run as of {prior.as_of} ({prior.folder}{caveat})"


def describe(prior: PriorRun | None) -> str:
    """The one line the run records and the approval summary shows about the comparison."""
    if prior is None:
        return f"changes: {FIRST_RUN}"
    return f"changes: CP-8 compares with {describe_run(prior)}"


# --- measures -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Observation:
    label: str
    unit: str | None
    value: str | None
    period: str | None
    definition: str | None
    written: str | None = None  # the text as the table wrote it, when `definition` is resolved

    def record(self) -> dict[str, str | bool | None]:
        return {
            "label": self.label,
            "unit": self.unit,
            "value": self.value,
            "period": self.period,
            "definition": self.definition,
            "definition_resolved": self.written is not None,
            "definition_written": self.written,
        }


_PLAIN = re.compile(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
_BRACKETED = re.compile(r"\((\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\)")
_MARK = re.compile(r"\s?[x%]$")  # a unit mark written beside the figure: the unit column says it


def number(cell: str) -> str | None:
    """A cell that is exactly one number, as written (a bracketed one negated, a Unicode minus
    read as a minus, a trailing `x` or `%` dropped); else None. A stated gap ("Not supplied: ...")
    and any other text are None: missing is never zero."""
    text = cell.replace("*", "").replace("\u2212", "-").strip()
    if not _PLAIN.fullmatch(text):
        text = _MARK.sub("", text)
    if _PLAIN.fullmatch(text):
        return text
    bracketed = _BRACKETED.fullmatch(text)
    return f"-{bracketed[1]}{bracketed[2] or ''}" if bracketed else None


def decimal(value: str) -> Decimal:
    return Decimal(value.replace(",", ""))


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:-1])]


def _tables(text: str) -> list[list[list[str]]]:
    """Every Markdown table of the text, outside code fences, as rows of cells (header first, the
    separator row dropped)."""
    tables: list[list[list[str]]] = []
    run: list[list[str]] = []
    fenced = False
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        if not fenced and line.lstrip().startswith("|") and line.rstrip().endswith("|"):
            cells = _cells(line)
            if not set("".join(cells)) <= set("-: "):
                run.append(cells)
        elif run:
            tables.append(run)
            run = []
    if run:
        tables.append(run)
    return tables


def _plain(label: str) -> str:
    """A row label compared: no emphasis, no trailing unit in brackets, lower case."""
    return " ".join(
        re.sub(r"\s*\([^)]*\)\s*$", "", label.replace("*", "").replace("`", "")).lower().split()
    )


# A measure either is read (Observation), is not stated (None), or is present but unusable (the
# reason, as a clause that follows "the earlier run" or "the current run").
Reading = Observation | str | None


POINTER = re.compile(r"\b(?:identical|same)\s+(?:definition|measure|basis)\b", re.IGNORECASE)


def _heading(chart: str) -> str:
    return chart if chart == NET_DEBT_TABLE else f"Chart data: {chart}"


def _followed(lines: list[str], chart: str, period: str, text: str | None) -> str | None:
    """The definition a basis cell points to, or None. A basis that says `identical definition` or
    `same measure` points to the basis of the table's row for the period before; that is followed,
    and only that. A pointer by calculation ID (`C01-C04`) is not followed: the calculation table
    is another section of the handoff, and the text is then left as written."""
    if text is None or POINTER.search(text) is None:
        return None
    start = lines.index(f"### {_heading(chart)}")
    rows: list[tuple[tuple[int, ...], str]] = []
    header: list[str] = []
    for line in lines[start + 1 :]:
        if not line.startswith("|"):
            if rows or header:
                break
            continue
        row = _cells(line)
        if not header:
            header = row
        elif not set("".join(row)) <= set("-: ") and len(row) == len(header):
            held = dict(zip(header, row, strict=True))
            key = period_order(held.get("Period", ""))
            if key is not None and held.get("Basis and limitation"):
                rows.append((key, held["Basis and limitation"]))
    here = period_order(period)
    before = [item for item in rows if here is not None and item[0] < here]
    if not before:
        return None
    earlier = max(before)[1]
    return None if POINTER.search(earlier) else earlier


def _chart_observation(lines: list[str], chart: str, column: str) -> Reading:
    try:
        found = chart_row(lines, chart, prefix="" if chart == NET_DEBT_TABLE else CHART_PREFIX)
    except ValueError:  # Periods that cannot be ordered: never guess which row is the latest.
        return "has periods in its table that cannot be ordered"
    if found is None or column not in found[0]:
        return None
    row = found[0]
    written = row.get("Basis and limitation") or None
    resolved = _followed(lines, chart, row.get("Period", ""), written)
    return Observation(
        column,
        row.get("Reporting unit") or None,
        number(row[column]),
        row.get("Period") or None,
        resolved or written,
        written if resolved else None,
    )


def _row_observation(text: str, labels: Sequence[str]) -> Reading:
    """The latest-period cell of the one table row labelled `labels`. None when no such row exists;
    a reason when more than one does, when its periods cannot be ordered, or when no unit is
    stated (a trailing `(unit)` in the label or a `Reporting unit` column)."""
    matches = [
        (table[0], row)
        for table in _tables(text)
        if len(table) > 1
        for row in table[1:]
        if row and _plain(row[0]) in labels and len(row) == len(table[0])
    ]
    if not matches:
        return None
    if len(matches) != 1:
        return "states it in more than one row"
    header, row = matches[0]
    columns = [(period_order(cell), i) for i, cell in enumerate(header) if i and period_order(cell)]
    if not columns or len({key[0] for key, _ in columns if key}) != 1:
        return "has periods in its row that cannot be ordered"
    _, at = max(columns, key=lambda item: item[0] or ())
    held = dict(zip(header, row, strict=True))
    unit = re.search(r"\(([^)]+)\)\s*$", row[0].replace("*", ""))
    stated = (unit[1].strip() if unit else None) or held.get("Reporting unit") or None
    if stated is None:
        return "states it with no unit"
    return Observation(
        _plain(row[0]),
        stated,
        number(row[at]),
        header[at],
        held.get("Basis and limitation") or None,
    )


def _read(text: str) -> tuple[dict[str, Observation], dict[str, str]]:
    """The measures a CP-1 handoff states (the five chart measures, then the row measures), and
    the reason for each it holds but cannot use."""
    lines = text.replace("\r\n", "\n").split("\n")
    found: dict[str, Reading] = {
        key: _chart_observation(lines, chart, column) for key, chart, column in CHART_MEASURES
    }
    found.update({key: _row_observation(text, labels) for key, labels in ROW_MEASURES})
    found[NET_DEBT_CASH[0]] = _chart_observation(lines, NET_DEBT_CASH[1], NET_DEBT_CASH[2])
    seen = {key: item for key, item in found.items() if isinstance(item, Observation)}
    return seen, {key: item for key, item in found.items() if isinstance(item, str)}


def observations(text: str) -> dict[str, Observation]:
    """The measures a CP-1 handoff states."""
    return _read(text)[0]


_LOCATOR = re.compile(
    r"\b(?:pages?|pp?|paras?|paragraphs?|sections?|notes?|lines?|slides?|exhibits?)\b\.?\s*"
    r"(?:\d+(?:[.,]\d+)*(?:\s*(?:[-\u2013/&,]|and(?=\s*\d)|to(?=\s*\d))\s*\d+(?:[.,]\d+)*)*)",
    re.IGNORECASE,
)


# A year after an instrument word names the instrument (`notes 2027`), not a place in a document:
# it is kept (as letters, so the digit and locator removal leave it) and so tells two debts apart.
_INSTRUMENT_YEAR = re.compile(
    r"\b(notes?|bonds?|loans?|facility|facilities|due|maturing|maturity)\s+((?:19|20)\d{2})\b"
)
_YEAR_LETTERS = str.maketrans("0123456789", "abcdefghij")


def _definition_key(text: str | None) -> str | None:
    """A definition text compared: no page or locator references, no digits, no punctuation, lower
    case, one space between words. None stays None (no text)."""
    if text is None:
        return None
    kept = _INSTRUMENT_YEAR.sub(
        lambda m: f"{m[1]} {m[2].translate(_YEAR_LETTERS)}", text.casefold()
    )
    bare = _LOCATOR.sub(" ", kept)
    return " ".join(re.sub(r"[^\w\s]|_|\d", " ", bare).split())


def _clause(who: str, why: str | None) -> str:
    return f"the {who} run {why or 'does not state it'}"


_PERIOD = re.compile(r"FY(\d{4})(?: / (\d{4}-\d{2}-\d{2}))?")


def same_period(a: str, b: str) -> bool:
    """Whether two periods are one. A period is `FY2024`, `FY2024 / 2024-09-30` or `2024-09-30`
    (what `period_order` and `chart_row` let through); any other text stands for itself in the date
    place. If both sides have one, they are the same only if equal; otherwise only the same fiscal
    year is the same period."""

    def split(period: str) -> tuple[str | None, str | None]:
        found = _PERIOD.fullmatch(period.strip())
        if found:
            return found[1], found[2]
        return None, period.strip()

    (year_a, date_a), (year_b, date_b) = split(a), split(b)
    if date_a and date_b:
        return date_a == date_b
    return year_a is not None and year_a == year_b


def _compare(
    key: str,
    prior: Observation | None,
    current: Observation | None,
    prior_why: str | None = None,
    current_why: str | None = None,
) -> dict[str, Any]:
    stated = current if current is not None else prior
    if stated is None:
        raise ValueError(f"measure {key} is stated in neither run")
    comparable, reason, difference = "no", None, None
    one_period = (
        prior is not None
        and current is not None
        and prior.period is not None
        and current.period is not None
        and same_period(prior.period, current.period)
    )
    if prior is None or current is None:
        reason = _clause(*(("earlier", prior_why) if prior is None else ("current", current_why)))
    elif (
        prior.unit is None
        or current.unit is None
        or " ".join(prior.unit.split()) != " ".join(current.unit.split())
    ):
        reason = "the unit differs or is not stated"
    elif prior.value is None or current.value is None:
        reason = "a value is not stated"
    else:
        difference = format(decimal(current.value) - decimal(prior.value), "f")
        same = prior.label.casefold() == current.label.casefold() and _definition_key(
            prior.definition
        ) == _definition_key(current.definition)
        comparable = "yes" if same else "judge"
        reason = None if same else "the label or definition text differs; CP-8 judges"
    return {
        "key": key,
        "label": stated.label,
        "unit": stated.unit,
        "comparable": comparable,
        "reason": reason,
        "prior": None if prior is None else prior.record(),
        "current": None if current is None else current.record(),
        "difference": difference,
        "same_period": one_period,
    }


# What the pack reads each net debt input from, for the reason it leaves the change out.
_READS = {
    "gross_debt": f'the comparison reads the Gross debt column of the CP-1 "{NET_DEBT_TABLE}" '
    "table",
    "net_debt": f'the comparison reads the Net debt column of the CP-1 "{NET_DEBT_TABLE}" table',
    "net_debt_cash": f'the comparison reads the Cash column of the CP-1 "{NET_DEBT_TABLE}" table',
}


def _net_debt_change(by_key: Mapping[str, Mapping[str, Any]]) -> tuple[dict[str, str] | None, str]:
    """The net debt change, or None and why not. It needs gross debt, net debt and cash stated in
    both runs in one unit under the same definition, and each run's net debt to be its gross debt
    less its cash."""
    pairs = {}
    for key in ("gross_debt", "net_debt", "net_debt_cash"):
        name = "cash" if key == "net_debt_cash" else key.replace("_", " ")
        measure = by_key.get(key)
        if measure is None:
            return None, f"{name} is not read from either run's CP-1 ({_READS[key]})"
        if measure["comparable"] == "no":
            return None, f"{name} cannot be compared ({measure['reason']})"
        if measure["comparable"] != "yes":
            return None, f"{name} is not comparable under one definition ({measure['comparable']})"
        pairs[key] = (decimal(measure["prior"]["value"]), decimal(measure["current"]["value"]))
    (pg, cg), (pn, cn), (pc, cc) = pairs["gross_debt"], pairs["net_debt"], pairs["net_debt_cash"]
    if pn != pg - pc or cn != cg - cc:
        return None, "a run's net debt is not its gross debt less its cash"
    units = {" ".join(by_key[k]["unit"].split()) for k in pairs}
    if len(units) != 1:
        return None, "debt and cash are in different units"
    return {
        "unit": str(by_key["net_debt_cash"]["unit"]),
        "prior_net_debt": format(pn, "f"),
        "change_in_gross_debt": format(cg - pg, "f"),
        "change_in_cash": format(cc - pc, "f"),
        "current_net_debt": format(cn, "f"),
        "convention": NET_DEBT_CONVENTION,
    }, ""


def _maturities(text: str) -> tuple[str | None, dict[str, str | None]] | None:
    """(unit, period -> value) of the table directly under the CP-1 debt maturities chart heading;
    None when the heading or that table is absent, has no unit or mixes units, or repeats a
    period."""
    lines = text.replace("\r\n", "\n").split("\n")
    try:
        start = lines.index(f"### Chart data: {MATURITIES}")
    except ValueError:
        return None
    rows: list[list[str]] = []
    for line in lines[start + 1 :]:
        if line.startswith("|") and line.rstrip().endswith("|"):
            rows.append(_cells(line))
        elif rows or line.strip():
            break  # the table follows the heading (blank lines aside) and ends at a non-row
    if (
        len(rows) < 3
        or rows[0][:2] != ["Period", "Debt maturing"]
        or "Reporting unit" not in rows[0]
    ):
        return None
    header = rows[0]
    body = [dict(zip(header, row, strict=False)) for row in rows[2:] if len(row) == len(header)]
    units = {row["Reporting unit"] for row in body}
    periods = [row["Period"] for row in body]
    if len(units) != 1 or len(set(periods)) != len(periods):
        return None
    return units.pop(), {row["Period"]: number(row["Debt maturing"]) for row in body}


def _maturity_profile(prior_text: str, current_text: str) -> tuple[dict[str, Any] | None, str]:
    before, after = _maturities(prior_text), _maturities(current_text)
    if before is None or after is None:
        return None, "a run has no debt maturities table with one unit"
    if before[0] != after[0]:
        return None, "the maturity tables are in different units"
    periods = sorted(set(before[1]) | set(after[1]), key=lambda p: (period_order(p) or (9,), p))
    rows = []
    for period in periods:
        then, now = before[1].get(period), after[1].get(period)
        rows.append(
            {
                "period": period,
                "prior": then,
                "current": now,
                "difference": None
                if then is None or now is None
                else format(decimal(now) - decimal(then), "f"),
            }
        )
    return {"unit": before[0], "rows": rows}, ""


# --- modules and limitations --------------------------------------------------------------------


def _bottom_line(text: str) -> str | None:
    if is_earlier_format(text):
        summary = reader_summary(text)
        return None if summary is None else summary["bottom_line"]
    return bottom_line_text(text)


def _limitations(text: str) -> tuple[str, ...]:
    if is_earlier_format(text):
        summary = reader_summary(text)
        items: tuple[str, ...] = () if summary is None else (summary["limitation"],)
    else:
        items = limitation_texts(text)
    return tuple(item for item in items if item.strip() and not NO_LIMITATION.match(item.strip()))


def _limitation_refs(texts: Mapping[str, str], letter: str) -> list[dict[str, str]]:
    """Every limitation item of a run with its ref: `E1`, `E2` ... or `C1`, `C2` ...; the order is
    the order of the modules as given, then of the items in the handoff."""
    refs: list[dict[str, str]] = []
    for module, text in texts.items():
        for item in _limitations(text):
            if normalise_limitation(item):
                refs.append({"ref": f"{letter}{len(refs) + 1}", "module": module, "text": item})
    return refs


def _format(text_by_module: Mapping[str, str]) -> str:
    return "earlier" if any(is_earlier_format(t) for t in text_by_module.values()) else "current"


def build_pack(  # noqa: PLR0913 - the two runs' texts and the current run's identity
    prior: PriorRun,
    prior_texts: Mapping[str, str],
    current_texts: Mapping[str, str],
    *,
    as_of: str,
    pathway: str,
    selection: str | None = None,
) -> dict[str, Any]:
    """The comparison pack (this module's docstring) for the prior run and the handoffs accepted so
    far in this run. CP-8 is not compared with itself. `selection` is how this run's modules were
    chosen (`preset`, `explicit` or None when not recorded)."""
    before = {m: t for m, t in prior_texts.items() if m != "CP-8"}
    now = {m: t for m, t in current_texts.items() if m != "CP-8"}
    seen_before, unread_before = _read(before["CP-1"]) if "CP-1" in before else ({}, {})
    seen_now, unread_now = _read(now["CP-1"]) if "CP-1" in now else ({}, {})
    measures = [
        _compare(
            key,
            seen_before.get(key),
            seen_now.get(key),
            unread_before.get(key),
            unread_now.get(key),
        )
        for key in (*(k for k, _, _ in CHART_MEASURES), *(k for k, _ in ROW_MEASURES))
        if key in seen_before or key in seen_now
    ]
    omitted: dict[str, str] = {}
    pack: dict[str, Any] = {
        "schema": PACK_SCHEMA,
        "prior": {
            "run": prior.folder,
            "as_of": prior.as_of,
            "pathway": prior.pathway,
            "format": "earlier" if prior.earlier_format else "current",
            "methods_changed": list(prior.methods_changed),
            "selection": prior.selection,
        },
        "current": {
            "as_of": as_of,
            "pathway": pathway,
            "format": _format(now),
            "selection": selection,
        },
        "measures": measures,
    }
    cash_key = NET_DEBT_CASH[0]
    cash = (
        [
            _compare(
                cash_key,
                seen_before.get(cash_key),
                seen_now.get(cash_key),
                unread_before.get(cash_key),
                unread_now.get(cash_key),
            )
        ]
        if cash_key in seen_before or cash_key in seen_now
        else []
    )
    change, why = _net_debt_change({m["key"]: m for m in (*measures, *cash)})
    if change is None:
        omitted["net_debt_change"] = why
    else:
        pack["net_debt_change"] = change
    if "CP-1" in before and "CP-1" in now:
        profile, why = _maturity_profile(before["CP-1"], now["CP-1"])
    else:
        profile, why = None, "a run has no CP-1 handoff"
    if profile is None:
        omitted["maturity_profile"] = why
    else:
        pack["maturity_profile"] = profile
    pack["omitted"] = omitted
    titles = module_titles()
    ids = list(dict.fromkeys((*now, *before)))
    pack["modules"] = [
        {
            "module": m,
            "title": titles.get(m, m),
            "ran_prior": m in before,
            "ran_current": m in now,
            "prior_bottom_line": _bottom_line(before[m]) if m in before else None,
            "current_bottom_line": _bottom_line(now[m]) if m in now else None,
        }
        for m in ids
    ]
    pack["limitations"] = {
        "earlier": _limitation_refs(before, "E"),
        "current": _limitation_refs(now, "C"),
    }
    return pack


def pack_bytes(pack: Mapping[str, Any]) -> bytes:
    return (json.dumps(pack, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def pack_builder(
    prior: PriorRun, as_of: str, pathway: str, selection: str | None = None
) -> Callable[[Mapping[str, bytes], Mapping[str, bytes]], bytes]:
    """`(sources, handoffs) -> pack bytes`; the earlier handoffs are the `prior/` sources."""

    def build(sources: Mapping[str, bytes], handoffs: Mapping[str, bytes]) -> bytes:
        earlier = {
            name.removeprefix(PRIOR_PREFIX).removesuffix(".md"): raw.decode("utf-8")
            for name, raw in sources.items()
            if name.startswith(PRIOR_PREFIX)
        }
        return pack_bytes(
            build_pack(
                prior,
                earlier,
                {m: raw.decode("utf-8") for m, raw in handoffs.items()},
                as_of=as_of,
                pathway=pathway,
                selection=selection,
            )
        )

    return build


__all__ = [
    "FIRST_RUN",
    "PACK_NAME",
    "PACK_SCHEMAS",
    "PRIOR_PREFIX",
    "PriorRun",
    "build_pack",
    "decimal",
    "describe",
    "describe_run",
    "find_prior",
    "number",
    "observations",
    "pack_builder",
    "pack_bytes",
    "prior_sources",
    "workspace_of",
]
