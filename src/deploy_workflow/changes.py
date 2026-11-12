"""What changed since the last run: which earlier run CP-8 compares with, and the comparison pack.

Owner, 2026-11-11: CP-8 answers "what has changed since the last time I looked at this", in the
run itself. Everything here is Python and reads files only; nothing calls a provider.

Prior run (`find_prior`, one rule). Among the runs the issuer library lists (`library_index
.admit_run`: completed, answered in their own run, earlier-format and earlier-methods runs
included), those of the same issuer and pathway whose as-of date is on or before this run's,
excluding this run's own folder. The latest is chosen by (as-of date, first model-call start,
folder name). None means no CP-8: the run records "first run of this pathway". The prior run's
folder is read, never written. `prepare` copies its delivered handoffs into the run folder as
`prior/<module>.md` and pins them as sources; a resume reuses those pins.

The pack (`build_pack`) is computed before CP-8 is called, given to CP-8 as the source
`changes.json` and published unchanged in the delivery as `changes.json`. Schema
`cpos-changes/1` (every number is a decimal string; missing is null, never zero):

- `prior`: `{run, as_of, pathway, format: "current"|"earlier", methods_changed: [text]}`;
  `current`: `{as_of, pathway, format}`.
- `measures`: a list of `{key, label, unit, comparable, reason, prior, current, difference}`;
  `prior` and `current` are `{label, unit, value, period, definition}` or null when the run does
  not state the measure. `comparable` is false when a run does not state it, or its label, unit or
  definition text (the table's "Basis and limitation", compared after normalisation) differs;
  `difference` is current minus prior, computed here with Decimal, and null unless `comparable` and
  both values are stated. `reason` says why there is no difference.
- `net_debt_bridge`: `{unit, prior_net_debt, change_in_gross_debt, change_in_cash,
  current_net_debt}`, only when both runs state gross debt, net debt and cash in one unit and
  each run's net debt is its gross debt less its cash.
- `maturity_profile`: `{unit, rows: [{period, prior, current, difference}]}` from the CP-1
  "Chart data: debt maturities" tables, only when both runs have one in one unit.
- `omitted`: `{net_debt_bridge|maturity_profile: reason}` for each of the two left out.
- `modules`: `{module, title, ran_prior, ran_current, prior_bottom_line, current_bottom_line}` for
  every module in either run (CP-8 excluded): the first paragraph of `### Bottom line`, Basis line
  dropped; for an earlier-format handoff the "Bottom line" cell of its Reader summary; else null.
- `limitations`: `{key, text, modules, prior, current}`, one per distinct normalised key
  (`prose_checks.normalise_limitation`) over both runs' `### Limitations` items (an earlier-format
  handoff: its Reader summary's "Main limitation"); a "No limitation changes ..." item is not a
  limitation.
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
from typing import Any

from deploy_vii.contracts import Contract, Identifier
from deploy_workflow.credit_os_catalogue import chart_row, period_order
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
PACK_SCHEMA = "cpos-changes/1"
FIRST_RUN = "first run of this pathway"
NO_LIMITATION = re.compile(r"no limitation changes\b", re.IGNORECASE)
NOT_SUPPLIED = "Not supplied"
# (key, CP-1 chart table, value column): the five measures the library already quotes.
CHART_MEASURES = (
    ("leverage", "leverage", "Total debt / EBITDA"),
    ("net_leverage", "leverage", "Net debt / EBITDA"),
    ("coverage", "interest cover", "EBITDA / cash interest"),
    ("cash", "liquidity", "Cash"),
    ("undrawn", "liquidity", "Undrawn committed facilities"),
)
# (key, row labels): read from the one CP-1 table row of that label, only when it states its unit.
ROW_MEASURES = (
    ("free_cash_flow", ("free cash flow", "fcf")),
    ("gross_debt", ("gross debt", "total debt")),
    ("net_debt", ("net debt",)),
)
MATURITIES = "debt maturities"


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


def workspace_of(directory: Path) -> Path | None:
    """The workspace a run folder belongs to: the folder holding `runs/`, by the rule the launcher
    uses to refresh the library; None when the run folder is not directly inside a `runs` folder."""
    return directory.parent.parent if directory.parent.name == "runs" else None


def find_prior(  # noqa: PLR0913 - the identity of the run and the library's method record
    workspace: Path,
    *,
    folder: str,
    issuer_id: str,
    pathway: str,
    as_of: str,
    method: tuple[MethodText, MethodHeadings] | None = None,
) -> tuple[PriorRun, dict[str, bytes]] | None:
    """The prior run (the rule in this module's docstring) and its delivered handoffs, or None.

    A folder the library would not list is not a candidate: it is skipped, as the library skips
    it. An unreadable one is logged; a refusal is the library's own record of why it is not
    listed, so it is logged at debug level only."""
    method = method or current_method()
    runs = workspace / "runs"
    found: list[tuple[tuple[str, str, str], dict[str, Any], Mapping[str, Any]]] = []
    for name in sorted(os.listdir(runs)) if runs.is_dir() else []:
        path = runs / name
        if name == folder or name.startswith(".") or path.is_symlink() or not path.is_dir():
            continue
        try:
            workflow = json_object(read_inside(path, "workflow.json"), "workflow.json")
            run = workflow.get("run")
            if (
                not isinstance(run, dict)
                or run.get("issuer_id") != issuer_id
                or run.get("pathway") != pathway
                or not isinstance(run.get("as_of"), str)
                or run["as_of"] > as_of
            ):
                continue
            deliveries: dict[str, dict[str, Any]] = {}
            record = admit_run(path, workspace / "library", method, deliveries)
        except Refused as refusal:
            log.debug("earlier run %s is not listed: %s", name, refusal)
            continue
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
            log.warning("earlier run %s is unreadable and is not compared: %r", name, error)
            continue
        started = record["execution"].get("started_at") or ""
        found.append(((record["as_of"], started, name), record, deliveries[name]))
    if not found:
        return None
    _, record, delivered = max(found, key=lambda item: item[0])
    handoffs = {
        module: read_pinned(runs / record["id"], pin["path"], pin["sha256"])
        for module, pin in delivered["handoffs"].items()
        if module != "CP-8"
    }
    prior = PriorRun(
        folder=record["id"],
        run_id=record["run_id"],
        as_of=record["as_of"],
        pathway=record["pathway"],
        earlier_format=any(is_earlier_format(raw.decode("utf-8")) for raw in handoffs.values()),
        methods_changed=tuple(record["method_changes"]),
        started_at=record["execution"].get("started_at"),
        modules=tuple(handoffs),
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

    def record(self) -> dict[str, str | None]:
        return {
            "label": self.label,
            "unit": self.unit,
            "value": self.value,
            "period": self.period,
            "definition": self.definition,
        }


_PLAIN = re.compile(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
_BRACKETED = re.compile(r"\((\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\)")


def number(cell: str) -> str | None:
    """A cell that is exactly one number, as written (a bracketed one negated); else None. A
    stated gap ("Not supplied: ...") and any other text are None: missing is never zero."""
    text = cell.replace("*", "").strip()
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


def _chart_observation(lines: list[str], chart: str, column: str) -> Observation | None:
    try:
        found = chart_row(lines, chart)
    except ValueError:  # Periods that cannot be ordered: never guess which row is the latest.
        return None
    if found is None or column not in found[0]:
        return None
    row = found[0]
    return Observation(
        column,
        row.get("Reporting unit") or None,
        number(row[column]),
        row.get("Period") or None,
        row.get("Basis and limitation") or None,
    )


def _row_observation(text: str, labels: Sequence[str]) -> Observation | None:
    """The latest-period cell of the one table row labelled `labels`; None when no row or more than
    one such row exists, when its periods cannot be ordered, or when no unit is stated (a trailing
    `(unit)` in the label or a `Reporting unit` column)."""
    matches = [
        (table[0], row)
        for table in _tables(text)
        if len(table) > 1
        for row in table[1:]
        if row and _plain(row[0]) in labels and len(row) == len(table[0])
    ]
    if len(matches) != 1:
        return None
    header, row = matches[0]
    columns = [(period_order(cell), i) for i, cell in enumerate(header) if i and period_order(cell)]
    if not columns or len({key[0] for key, _ in columns if key}) != 1:
        return None
    _, at = max(columns, key=lambda item: item[0] or ())
    held = dict(zip(header, row, strict=True))
    unit = re.search(r"\(([^)]+)\)\s*$", row[0].replace("*", ""))
    stated = (unit[1].strip() if unit else None) or held.get("Reporting unit") or None
    if stated is None:
        return None
    return Observation(
        _plain(row[0]),
        stated,
        number(row[at]),
        header[at],
        held.get("Basis and limitation") or None,
    )


def observations(text: str) -> dict[str, Observation]:
    """The measures a CP-1 handoff states (the five chart measures, then the row measures)."""
    lines = text.replace("\r\n", "\n").split("\n")
    found: dict[str, Observation | None] = {
        key: _chart_observation(lines, chart, column) for key, chart, column in CHART_MEASURES
    }
    found.update({key: _row_observation(text, labels) for key, labels in ROW_MEASURES})
    return {key: seen for key, seen in found.items() if seen is not None}


def _same(a: str | None, b: str | None) -> bool:
    return (a is None and b is None) or (
        a is not None and b is not None and normalise_limitation(a) == normalise_limitation(b)
    )


def _compare(key: str, prior: Observation | None, current: Observation | None) -> dict[str, Any]:
    stated = current if current is not None else prior
    if stated is None:
        raise ValueError(f"measure {key} is stated in neither run")
    reason: str | None = None
    if prior is None or current is None:
        reason = "the " + ("earlier" if prior is None else "current") + " run does not state it"
    elif prior.unit is None or current.unit is None or prior.unit != current.unit:
        reason = "the unit differs or is not stated"
    elif prior.label != current.label:
        reason = "the label differs"
    elif not _same(prior.definition, current.definition):
        reason = "the definition text differs"
    comparable = reason is None
    difference = None
    if comparable and prior is not None and current is not None:
        if prior.value is None or current.value is None:
            reason = "a value is not stated"
        else:
            difference = format(decimal(current.value) - decimal(prior.value), "f")
    return {
        "key": key,
        "label": stated.label,
        "unit": stated.unit,
        "comparable": comparable,
        "reason": None if difference is not None else reason or "no difference",
        "prior": None if prior is None else prior.record(),
        "current": None if current is None else current.record(),
        "difference": difference,
    }


def _bridge(
    prior: Mapping[str, Observation], current: Mapping[str, Observation]
) -> tuple[dict[str, str] | None, str]:
    """The net debt bridge, or None and why not. It needs gross debt, net debt and cash stated in
    both runs under the same label, unit and definition, and each run's net debt to be its gross
    debt less its cash."""
    pairs = {}
    for key in ("gross_debt", "net_debt", "cash"):
        name = key.replace("_", " ")
        if key not in prior and key not in current:
            return None, f"{name} is not stated in either run"
        compared = _compare(key, prior.get(key), current.get(key))
        if not compared["comparable"]:
            return None, f"{name} cannot be compared ({compared['reason']})"
        before, now = prior[key], current[key]
        if before.value is None or now.value is None:
            return None, f"{name} has no stated value in a run"
        pairs[key] = (decimal(before.value), decimal(now.value))
    (pg, cg), (pn, cn), (pc, cc) = pairs["gross_debt"], pairs["net_debt"], pairs["cash"]
    if pn != pg - pc or cn != cg - cc:
        return None, "a run's net debt is not its gross debt less its cash"
    if len({prior[k].unit for k in pairs}) != 1:
        return None, "debt and cash are in different units"
    return {
        "unit": str(prior["cash"].unit),
        "prior_net_debt": format(pn, "f"),
        "change_in_gross_debt": format(cg - pg, "f"),
        "change_in_cash": format(cc - pc, "f"),
        "current_net_debt": format(cn, "f"),
    }, ""


def _maturities(text: str) -> tuple[str | None, dict[str, str | None]] | None:
    """(unit, period -> value) of the CP-1 debt maturities chart table; None when it is absent, has
    no unit or mixes units, or repeats a period."""
    for table in _tables(text):
        header = table[0]
        if header[:2] != ["Period", "Debt maturing"] or "Reporting unit" not in header:
            continue
        # Only the chart table, not another table that happens to share its first two columns.
        if f"### Chart data: {MATURITIES}" not in text.replace("\r\n", "\n"):
            continue
        rows = [
            dict(zip(header, row, strict=False)) for row in table[1:] if len(row) == len(header)
        ]
        units = {row["Reporting unit"] for row in rows}
        periods = [row["Period"] for row in rows]
        if len(units) != 1 or len(set(periods)) != len(periods):
            return None
        return units.pop(), {row["Period"]: number(row["Debt maturing"]) for row in rows}
    return None


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


def _limitation_rows(prior: Mapping[str, str], current: Mapping[str, str]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for side, texts in (("prior", prior), ("current", current)):
        for module, text in texts.items():
            for item in _limitations(text):
                key = normalise_limitation(item)
                if not key:
                    continue
                row = rows.setdefault(
                    key, {"key": key, "text": item, "modules": [], "prior": False, "current": False}
                )
                if side == "current":
                    row["text"] = item
                row[side] = True
                if module not in row["modules"]:
                    row["modules"].append(module)
    return list(rows.values())


def _format(text_by_module: Mapping[str, str]) -> str:
    return "earlier" if any(is_earlier_format(t) for t in text_by_module.values()) else "current"


def build_pack(
    prior: PriorRun,
    prior_texts: Mapping[str, str],
    current_texts: Mapping[str, str],
    *,
    as_of: str,
    pathway: str,
) -> dict[str, Any]:
    """The comparison pack (this module's docstring) for the prior run and the handoffs accepted so
    far in this run. CP-8 is not compared with itself."""
    before = {m: t for m, t in prior_texts.items() if m != "CP-8"}
    now = {m: t for m, t in current_texts.items() if m != "CP-8"}
    seen_before = observations(before["CP-1"]) if "CP-1" in before else {}
    seen_now = observations(now["CP-1"]) if "CP-1" in now else {}
    measures = [
        _compare(key, seen_before.get(key), seen_now.get(key))
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
        },
        "current": {"as_of": as_of, "pathway": pathway, "format": _format(now)},
        "measures": measures,
    }
    bridge, why = _bridge(seen_before, seen_now)
    if bridge is None:
        omitted["net_debt_bridge"] = why
    else:
        pack["net_debt_bridge"] = bridge
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
    pack["limitations"] = _limitation_rows(before, now)
    return pack


def pack_bytes(pack: Mapping[str, Any]) -> bytes:
    return (json.dumps(pack, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def pack_builder(
    prior: PriorRun, as_of: str, pathway: str
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
            )
        )

    return build


__all__ = [
    "FIRST_RUN",
    "PACK_NAME",
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
