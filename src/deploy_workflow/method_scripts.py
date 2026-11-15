"""The selected methods' own scripts, run by Python on a module's returned handoff.

The methods ship calculators (`skills/<skill>/scripts/*.py`) that the model cannot run in this
transport (TRANSPORT_RULES). After a module answers, Python runs the registered script on the
inputs the handoff's own registers state and compares the script's result with the figure the
handoff states. Owner, 2026-11-15: "wire the scripts in as checks".

Loading: a script runs only from bytes whose sha256 is the one `manifest.json` registers for its
archive path (the shared `cp_tables.py` and `validate_handoff.py` it imports by name included);
other bytes are refused. The verified bytes are compiled in memory, so no bytecode is written
into the archive, and `sys.path`, `sys.modules` and `sys.dont_write_bytecode` are restored after.

Comparison: a stated figure agrees when it is within one unit of its last displayed decimal place
of the script's result (or of the script's own rounding, if coarser); currency and scale are read
from the register and must match before anything is compared. A missing input is "not checked"
with the input named, never zero; a figure the handoff does not state is not a finding. Only a
disagreement is an acceptance issue (it names the register, row, both values and the formula);
anything the check cannot read, and any failure inside a script, is "not checked" with its
reason, so a script can never crash or block a run.
"""

import hashlib
import json
import re
import sys
import threading
import types
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from functools import cache
from pathlib import Path
from typing import Any, Literal

from deploy_workflow.prose_checks import ISO_4217

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = "docs/reuse/selected-methods/"
MANIFEST = ARCHIVE + "manifest.json"
SHARED = ARCHIVE + "scripts/"
# Imported by name by every calculator, in load order: cp_tables imports validate_handoff.
SHARED_MODULES = ("validate_handoff", "cp_tables")
LIQUIDITY_BRIDGE = ARCHIVE + "skills/cp-2d-liquidity-cash-flow-bridge/scripts/liquidity_bridge.py"
FUNDING_GAP = ARCHIVE + "skills/cp-3c-refinancing-lme-risk/scripts/funding_gap.py"
RECORD_KIND = "method-script-checks/1"
RECORD_SUFFIX = ".method-checks.json"  # beside a request folder's `<attempt>.review.json`

Status = Literal["agreed", "disagreed", "not checked"]


class ScriptRefused(ValueError):
    """A script, or a module it imports, is not registered or its bytes are not the registered."""


@dataclass(frozen=True)
class Outcome:
    """One figure's check: the script that recomputed it, where the handoff states it, and what
    came of it. ``reason`` is the formula in words for a disagreement and the cause for a figure
    not checked."""

    module: str
    script: str
    figure: str
    register: str
    row: str
    status: Status
    stated: str | None = None
    recomputed: float | None = None
    tolerance: float | None = None
    unit: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class Loaded:
    """A registered script, executed from its verified bytes, and the `cp_tables` it imported."""

    script: types.ModuleType
    tables: types.ModuleType
    sha256: str


# --- loading ------------------------------------------------------------------------------------

_LOCK = threading.Lock()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def registered(root: Path = ROOT) -> dict[str, str]:
    """The sha256 `manifest.json` registers for each archive path."""
    data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    return {entry["archive_path"]: entry["sha256"] for entry in data["files"]}


def _verified(root: Path, path: str, hashes: dict[str, str]) -> bytes:
    if path not in hashes:
        raise ScriptRefused(f"{path} is not registered in {MANIFEST}")
    raw = (root / path).read_bytes()
    if _sha(raw) != hashes[path]:
        raise ScriptRefused(f"{path}: its bytes are not the registered ones ({hashes[path][:12]})")
    return raw


@contextmanager
def _isolated(names: tuple[str, ...]) -> Iterator[None]:
    """Restore the import state a script changes: `sys.path` (each script puts its own folder
    first), the named `sys.modules` entries and `sys.dont_write_bytecode`."""
    path, bytecode = list(sys.path), sys.dont_write_bytecode
    held = {name: sys.modules.get(name) for name in names}
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.path[:] = path
        sys.dont_write_bytecode = bytecode
        for name, module in held.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _execute(name: str, file: Path, raw: bytes) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = str(file)
    sys.modules[name] = module  # a dataclass in the script looks its module up while executing
    exec(compile(raw, str(file), "exec", dont_inherit=True), module.__dict__)  # noqa: S102
    return module


def load(path: str, root: Path = ROOT) -> Loaded:
    """Execute the registered script at ``path`` (an archive path) from its verified bytes, with
    the shared modules it imports by name; refuse any file whose bytes are not registered."""
    hashes = registered(root)
    shared = {name: _verified(root, f"{SHARED}{name}.py", hashes) for name in SHARED_MODULES}
    own = _verified(root, path, hashes)
    name = f"_method_script_{Path(path).stem}"
    with _LOCK, _isolated((*SHARED_MODULES, name)):
        modules = {n: _execute(n, root / f"{SHARED}{n}.py", raw) for n, raw in shared.items()}
        script = _execute(name, root / path, own)
    return Loaded(script, modules["cp_tables"], _sha(own))


@cache
def _loaded(path: str) -> Loaded:
    return load(path)


# --- reading a register -------------------------------------------------------------------------

_HEADING = re.compile(r"^#{1,6}\s")
_FENCE = re.compile(r"^\s*(```|~~~)")
_SEPARATOR = re.compile(r":?-{3,}:?")
Table = tuple[list[str], list[list[str]]]


def _plain(cell: str) -> str:
    return re.sub(r"[*`]", "", cell).strip()


def _cells(line: str) -> list[str]:
    body = line.strip().removeprefix("|").removesuffix("|")
    return [_plain(c) for c in re.split(r"(?<!\\)\|", body)]


def _unfenced(text: str) -> list[str]:
    lines, fenced = [], False
    for line in text.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
            line = ""
        lines.append("" if fenced else line)
    return lines


def _register_start(ident: str) -> re.Pattern[str]:
    """A register's heading starts with its id (after an optional `1.`, the id may be in bold or
    backticks), or a `<!-- table-id: ... -->` tag ends with it: the launcher's `_has_register`."""
    wrap = r"(?:\*\*|`)?"
    heading = rf"#{{2,6}} (?:\d+[.)] )?{wrap}{re.escape(ident)}{wrap}(?!\w|\.\d)"
    tag = rf"<!-- table-id: (?:\S*\.)?{re.escape(ident)} -->\s*$"
    return re.compile(rf"^(?:{heading}|{tag})")


def _table_after(lines: list[str], start: int, name: str) -> Table | str:
    """The first pipe table after line ``start`` and before the next heading."""
    at = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("|")), None)
    if at is None or any(_HEADING.match(line) for line in lines[start + 1 : at]):
        return f"{name} has no table"
    header = _cells(lines[at])
    if at + 1 >= len(lines) or not all(_SEPARATOR.fullmatch(c) for c in _cells(lines[at + 1])):
        return f"{name}'s table has no separator row under its header"
    rows: list[list[str]] = []
    for line in lines[at + 2 :]:
        if not line.lstrip().startswith("|"):
            break
        rows.append(_cells(line))
        if len(rows[-1]) != len(header):
            return f"{name}'s table has a row of {len(rows[-1])} cells under {len(header)} columns"
    return header, rows


def register_table(text: str, ident: str) -> Table | str:
    """The table of the register ``ident`` (a method id such as `T2E.5`), or why it is not read."""
    lines = _unfenced(text)
    pattern = _register_start(ident)
    found = [i for i, line in enumerate(lines) if pattern.match(line)]
    if not found:
        return f"the handoff has no {ident} register"
    if len(found) > 1:
        return f"the handoff has {len(found)} {ident} registers"
    return _table_after(lines, found[0], ident)


def heading_table(text: str, heading: str) -> Table | str:
    """The table under the `###` heading named exactly ``heading``, or why it is not read."""
    lines = _unfenced(text)
    want = heading.casefold()
    found = [i for i, line in enumerate(lines) if _heading_name(line) == want]
    if len(found) != 1:
        count = "no" if not found else str(len(found))
        return f"the handoff has {count} `### {heading}` table{'s' if found else ''}"
    return _table_after(lines, found[0], f"`### {heading}`")


def _heading_name(line: str) -> str | None:
    match = re.match(r"^###\s+(.*?)\s*#*\s*$", line)
    return _plain(match[1]).casefold() if match else None


def _label(cell: str) -> str:
    """A row label as compared: case, spacing, hyphens and the -isation spelling ignored."""
    text = _plain(cell).casefold().replace("amortisation", "amortization")
    text = re.sub(r"\s*/\s*", "/", text.replace("-", " "))
    return re.sub(r"\s+", " ", text).strip(" :")


def _columns(table: Table, wanted: tuple[str, ...], name: str) -> dict[str, int] | str:
    header = [_label(c) for c in table[0]]
    missing = [w for w in wanted if _label(w) not in header]
    if missing:
        return f"{name} has no {', '.join(f'`{m}`' for m in missing)} column"
    return {w: header.index(_label(w)) for w in wanted}


# --- reading a figure ---------------------------------------------------------------------------

_SCALES = {
    "m": "m",
    "mn": "m",
    "mm": "m",
    "million": "m",
    "millions": "m",
    "bn": "bn",
    "billion": "bn",
    "billions": "bn",
    "k": "k",
    "thousand": "k",
    "thousands": "k",
    "units": "units",
    "unit": "units",
}
_SYMBOLS = {"us$": "USD", "€": "EUR", "£": "GBP"}


def blank(cell: str, tables: types.ModuleType) -> bool:
    """A cell that states no figure: the transport's `Not supplied: <reason>`, the method's
    `[Insufficient Information]` and the script's own null words. Never a zero."""
    text = _plain(cell).casefold()
    stated_gap = text.startswith(("not supplied", "[insufficient information]", "insufficient"))
    return stated_gap or bool(tables.is_null(text))


def figure(cell: str, tables: types.ModuleType, suffix: str = "") -> tuple[float, int] | str:
    """The cell as the script's own `parse_figure` reads it, with its displayed decimal places;
    ``suffix`` is a unit word the cell may end with (`months`, `years`)."""
    text = _plain(cell)
    if suffix:
        text = re.sub(rf"\s*{suffix}s?\.?$", "", text, flags=re.IGNORECASE)
    try:
        value = tables.parse_figure(text)
    except ValueError as error:
        return f"`{cell}` is not a figure ({error})"
    if value is None:
        return f"`{cell}` states no figure"
    digits = re.sub(r"[^0-9.,]", "", text)
    decimal = max(digits.rfind("."), digits.rfind(",") if "." in digits else -1)
    return float(value), (len(digits) - decimal - 1 if decimal >= 0 else 0)


def scale_of(cell: str) -> str | None:
    """`m`, `bn`, `k` or `units` as a Scale cell (or the end of a currency-and-scale cell) states
    it; None when it states none of them."""
    words = re.findall(r"[a-z]+", _plain(cell).casefold().replace("us$", " "))
    found = {_SCALES[w] for w in words if w in _SCALES}
    glued = re.search(r"[$€£](m|mn|bn|k)$", _plain(cell).casefold().replace(" ", ""))
    found |= {_SCALES[glued[1]]} if glued else set()
    return found.pop() if len(found) == 1 else None


def currency_of(cell: str) -> str | None:
    """The ISO 4217 code a cell states (`USD`, or `US$`, `€`, `£`), or None when it states none or
    more than one. A bare `$` names no currency."""
    text = _plain(cell)
    codes = {c for c in re.findall(r"\b[A-Z]{3}\b", text) if c in ISO_4217}
    codes |= {code for symbol, code in _SYMBOLS.items() if symbol in text.casefold()}
    return codes.pop() if len(codes) == 1 else None


def _unit(cell: str) -> str | None:
    currency, scale = currency_of(cell), scale_of(cell)
    return f"{currency} {scale}" if currency and scale else None


def _tolerance(places: int, script_step: float) -> float:
    return max(10.0**-places, script_step)


def compare(stated: tuple[float, int], recomputed: float, script_step: float) -> tuple[bool, float]:
    """Whether the stated figure agrees with the script's, and the tolerance applied: one unit in
    the stated figure's last displayed place, or the script's own rounding step if coarser."""
    tolerance = _tolerance(stated[1], script_step)
    close = abs(stated[0] - recomputed) <= tolerance + 1e-9 * max(1.0, abs(recomputed))
    return close, tolerance


@dataclass(frozen=True)
class _Where:
    """Where one figure is stated, and the script that recomputes it; called, an outcome."""

    module: str
    script: str
    figure: str
    register: str

    def __call__(self, status: Status, **rest: Any) -> Outcome:
        return Outcome(
            self.module, self.script, self.figure, self.register, self.figure, status, **rest
        )


@dataclass(frozen=True)
class _Claim:
    """A stated figure and the script's result for it."""

    where: _Where
    stated: str  # the cell as written
    recomputed: float
    step: float  # the script's own rounding step for this figure
    unit: str
    formula: str
    suffix: str = ""  # a unit word the cell may end with
    others: tuple[str, ...] = ()  # rows outside the formula, which may explain a difference


def _judged(claim: _Claim, tables: types.ModuleType) -> Outcome:
    where = claim.where
    read = figure(claim.stated, tables, claim.suffix)
    if isinstance(read, str):
        return where("not checked", stated=claim.stated, reason=read)
    close, tolerance = compare(read, claim.recomputed, claim.step)
    values = {"stated": claim.stated, "recomputed": claim.recomputed, "tolerance": tolerance}
    values |= {"unit": claim.unit}
    if close:
        return where("agreed", **values, reason=claim.formula)
    if claim.others:
        rows = ", ".join(f"`{r}`" for r in claim.others)
        cause = (
            f"{where.register} has rows outside the method's formula ({rows}) that may explain it"
        )
        return where("not checked", **values, reason=cause)
    return where("disagreed", **values, reason=claim.formula)


# --- CP-2D: liquidity_bridge.py on T2E.5 and T2E.6 ---------------------------------------------

# The script's input field -> the T2E.5 row names the method gives it (REF_CP-2D_05 step 2 and
# the formula of its step 5 and of REF_CP-2D_LabelsAndCalc).
BRIDGE_ROWS: dict[str, tuple[str, ...]] = {
    "beginning_accessible_liquidity": ("Beginning accessible liquidity",),
    "operating_cash_flow": ("Operating cash inflow/outflow",),
    "working_capital_movement": ("Working-capital impact", "WC impact"),
    "cash_interest": ("Cash interest",),
    "cash_taxes": ("Cash taxes",),
    "mandatory_capex": ("Mandatory capex",),
    "debt_amortisation_and_maturities": ("Debt amortization/maturities",),
    "other_cash_uses": ("Other cash uses",),
    "committed_inflows": ("Committed inflows",),
}
ENDING = "Ending accessible liquidity"
MTE = "Months to Empty"
# Required rows that build the beginning figure; the script does not read them.
BEGINNING_PARTS = ("Beginning cash", "Accessible revolver availability")
BRIDGE_COLUMNS = ("Bridge Item", "Amount", "Currency and Scale")
MTE_COLUMNS = ("Calculation", "Result", "Formula / Inputs", "Cash-Burn Basis")
BRIDGE_MONTHS = 12  # REF_CP-2D_05: the 12-month liquidity bridge
AMOUNT_STEP = 1e-6  # the scripts round amounts to six places
MONTHS_STEP = 0.01  # liquidity_bridge.py rounds Months to Empty to two places
BRIDGE_FORMULA = (
    "Ending accessible liquidity = Beginning accessible liquidity + Operating cash inflow/outflow "
    "+ Working-capital impact - Cash interest - Cash taxes - Mandatory capex - Debt "
    "amortization/maturities - Other cash uses + Committed inflows (REF_CP-2D_05 step 5); a cash "
    "use is a positive amount the formula subtracts, so one written negative is added"
)
MTE_FORMULA = (
    "Months to Empty = Beginning accessible liquidity / average monthly cash burn, the burn being "
    "the T2E.5 bridge's net outflow over its 12 months; with no net outflow there is no runway "
    "to exhaust and the Result is Not Calculable (REF_CP-2D_06)"
)
CP2D_NOTE = (
    "Python checks two of your figures after you answer, with the method's own "
    "`liquidity_bridge.py` (you cannot run it): Ending accessible liquidity, recomputed from the "
    "T2E.5 rows by the method's formula, and the Months to Empty Result in T2E.6 when its "
    "Cash-Burn Basis is the T2E.5 bridge. So write T2E.5 with these row names, once each: "
    f"{', '.join(names[0] for names in BRIDGE_ROWS.values())} (0 when there are none) and "
    f"{ENDING}, every row in the same Currency and Scale. Write each cash use (cash interest, "
    "cash taxes, mandatory capex, debt amortization/maturities, other cash uses) as a positive "
    "amount: the formula subtracts it. A figure that disagrees with the recomputation is sent "
    "back for repair; one whose input is missing is recorded as not checked, never read as "
    "zero.\n\n"
)
_CP2D_ENDING = _Where("CP-2D", LIQUIDITY_BRIDGE, ENDING, "T2E.5")
_CP2D_MTE = _Where("CP-2D", LIQUIDITY_BRIDGE, MTE, "T2E.6")


@dataclass(frozen=True)
class _Bridge:
    """T2E.5 as the script reads it."""

    inputs: dict[str, float | None]  # every field; None is absent or blank, never zero
    gap: str | None  # the absent or blank inputs, named
    others: tuple[str, ...]  # rows outside the formula
    ending: str  # the Ending row's Amount cell, as written
    unit: str


def _bridge_rows(table: Table, item: int) -> dict[str, list[str]] | str:
    names = {_label(n): field for field, all_names in BRIDGE_ROWS.items() for n in all_names}
    names |= {_label(ENDING): "ending"} | {_label(n): "part:" + n for n in BEGINNING_PARTS}
    rows: dict[str, list[str]] = {}
    for row in table[1]:
        key = names.get(_label(row[item]), "other:" + row[item])
        if key in rows:
            return f"T2E.5 has two `{row[item]}` rows"
        rows[key] = row
    if "ending" not in rows:
        return f"T2E.5 has no `{ENDING}` row"
    return rows


def _bridge_gap(absent: list[str], blanks: list[str]) -> str | None:
    if absent:
        return f"T2E.5 has no {', '.join(f'`{n}`' for n in absent)} row (absent, not zero)"
    if blanks:
        return (
            f"T2E.5 states no amount for {', '.join(f'`{n}`' for n in blanks)} (missing, not zero)"
        )
    return None


def _read_bridge(table: Table, tables: types.ModuleType) -> _Bridge | str:
    cols = _columns(table, BRIDGE_COLUMNS, "T2E.5")
    rows = cols if isinstance(cols, str) else _bridge_rows(table, cols["Bridge Item"])
    if isinstance(cols, str) or isinstance(rows, str):
        return str(rows)
    units = {rows[k][cols["Currency and Scale"]] for k in (*BRIDGE_ROWS, "ending") if k in rows}
    keys = {_unit(u) for u in units}
    if None in keys or len(keys) != 1:
        return f"T2E.5's rows state different or unread currency and scale: {'; '.join(units)}"
    inputs: dict[str, float | None] = dict.fromkeys(BRIDGE_ROWS)
    absent: list[str] = []
    blanks: list[str] = []
    for field, names in BRIDGE_ROWS.items():
        cell = rows[field][cols["Amount"]] if field in rows else None
        read = None if cell is None or blank(cell, tables) else figure(cell, tables)
        if isinstance(read, str):
            return f"T2E.5 `{names[0]}`: {read}"
        inputs[field] = None if read is None else read[0]
        (absent if cell is None else blanks).extend([names[0]] if read is None else [])
    others = tuple(k.removeprefix("other:") for k in rows if k.startswith("other:"))
    ending = rows["ending"][cols["Amount"]]
    return _Bridge(inputs, _bridge_gap(absent, blanks), others, ending, str(keys.pop()))


def _cp2d(text: str, loaded: Loaded) -> list[Outcome]:
    table = register_table(text, "T2E.5")
    bridge = table if isinstance(table, str) else _read_bridge(table, loaded.tables)
    if isinstance(bridge, str):
        return [_CP2D_ENDING("not checked", reason=bridge), _CP2D_MTE("not checked", reason=bridge)]
    result = loaded.script.compute(bridge.inputs, period_months=BRIDGE_MONTHS)
    return [_ending(bridge, result, loaded.tables), _months(text, bridge, result, loaded.tables)]


def _ending(bridge: _Bridge, result: dict[str, Any], tables: types.ModuleType) -> Outcome:
    if blank(bridge.ending, tables):
        return _CP2D_ENDING("not checked", reason=f"T2E.5 states no {ENDING} figure")
    if bridge.gap is not None:
        return _CP2D_ENDING("not checked", stated=bridge.ending, reason=bridge.gap)
    recomputed = result["ending_accessible_liquidity"]
    claim = _Claim(
        _CP2D_ENDING, bridge.ending, recomputed, AMOUNT_STEP, bridge.unit, BRIDGE_FORMULA
    )
    return _judged(replace(claim, others=bridge.others), tables)


def _mte_result(text: str) -> str:
    """T2E.6's Months to Empty Result when its burn basis is the T2E.5 bridge; else why not."""
    table = register_table(text, "T2E.6")
    cols = table if isinstance(table, str) else _columns(table, MTE_COLUMNS, "T2E.6")
    if isinstance(table, str) or isinstance(cols, str):
        raise _NotChecked(str(cols))
    rows = [r for r in table[1] if _label(r[cols["Calculation"]]) == _label(MTE)]
    if len(rows) != 1:
        raise _NotChecked(f"T2E.6 has {len(rows) or 'no'} `{MTE}` rows")
    basis = f"{rows[0][cols['Cash-Burn Basis']]} {rows[0][cols['Formula / Inputs']]}".casefold()
    if "t2e.5" not in basis and "bridge" not in basis:
        raise _NotChecked(
            "T2E.6's cash-burn basis is not the T2E.5 bridge, and the script's burn is that "
            "bridge's net outflow over its 12 months"
        )
    return rows[0][cols["Result"]]


class _NotChecked(Exception):
    """A figure that cannot be checked, and why."""


def _months(
    text: str, bridge: _Bridge, result: dict[str, Any], tables: types.ModuleType
) -> Outcome:
    try:
        stated = _mte_result(text)
    except _NotChecked as why:
        return _CP2D_MTE("not checked", reason=str(why))
    words = _plain(stated).casefold()
    said_none = words.startswith("not calculable")
    if blank(stated, tables) and not said_none:
        return _CP2D_MTE("not checked", stated=stated, reason=f"T2E.6 states no {MTE} figure")
    if bridge.gap is not None:
        return _CP2D_MTE("not checked", stated=stated, reason=bridge.gap)
    months = result["months_to_empty"]
    no_runway = months is None and result["average_monthly_burn"] is not None
    if months is None and not no_runway:  # beginning accessible liquidity is missing
        return _CP2D_MTE("not checked", stated=stated, reason=result["months_to_empty_note"])
    if said_none or no_runway:
        status: Status = "agreed" if said_none and no_runway else "disagreed"
        recomputed = None if no_runway else months
        note = (
            ""
            if recomputed is not None
            else f"; recomputed: Not Calculable ({result['months_to_empty_note']})"
        )
        return _CP2D_MTE(status, stated=stated, recomputed=recomputed, reason=MTE_FORMULA + note)
    claim = _Claim(_CP2D_MTE, stated, months, MONTHS_STEP, "months", MTE_FORMULA, suffix="month")
    return _judged(claim, tables)


# --- CP-3C: funding_gap.py on T3D.2 and `### Funding gap` ---------------------------------------

FUNDING_HEADING = "Funding gap"
FUNDING_COLUMNS = ("Line", "Amount", "Drawn", "Years", "Committed", "Currency", "Scale")
WALL_COLUMNS = ("Instrument", "Amount", "Currency", "Scale", "Years to Maturity")
NOT_APPLICABLE = ("—", "–", "-")
# Each stated line -> (the script's view, its key, the formula in words).
FUNDING_RESULTS: dict[str, tuple[str, str, str]] = {
    "Maturities due": (
        "maturity_wall",
        "total_due",
        (
            "Maturities due = the T3D.2 Amounts whose Years to Maturity are within the Horizon; an "
            "instrument without an amount or a maturity makes the total not calculable"
        ),
    ),
    "Available liquidity": (
        "liquidity",
        "total_available",
        (
            "Available liquidity = Cash + (Amount - Drawn) of each facility with Committed "
            "`Yes` whose Years to expiry are not less than the Horizon; an uncommitted facility, "
            "or one expiring inside the Horizon, adds nothing"
        ),
    ),
    "Funding gap": (
        "gap",
        "funding_gap",
        (
            "Funding gap = Maturities due - (Available liquidity + Forecast free cash flow), or 0 "
            "when that is negative; a Forecast free cash flow not supplied adds nothing"
        ),
    ),
}
CP3C_NOTE = (
    "Python checks the funding gap after you answer, with the method's own `funding_gap.py` (you "
    f"cannot run it). Write it in `## Findings` as a `### {FUNDING_HEADING}` register with the "
    f"columns `{' | '.join(FUNDING_COLUMNS)}`, on the T3D.2 as-of-balance-sheet-date basis and in "
    "one currency and scale: a `Horizon` row (Years: the window, in years from the balance-sheet "
    "date); `Cash`; one `Facility: <name>` row per credit facility (Amount its commitment, Drawn "
    "its drawn amount, Years its years to expiry, Committed `Yes` or `No`); `Forecast free cash "
    "flow` over the window (or `Not supplied: <reason>`); then `Maturities due` (the T3D.2 "
    "Amounts whose Years to Maturity are within the window), `Available liquidity` (cash plus "
    "the undrawn amount of each committed facility that does not expire inside the window) and "
    "`Funding gap` (maturities due less available liquidity and forecast free cash flow, or 0 "
    "when they cover it). A cell that does not apply is `—`. Python recomputes the last three "
    "from this table and T3D.2; one that disagrees is sent back for repair.\n\n"
)


def _funding_where(line: str) -> _Where:
    return _Where("CP-3C", FUNDING_GAP, line, f"`### {FUNDING_HEADING}`")


@dataclass(frozen=True)
class _Funding:
    """`### Funding gap` and T3D.2 as the script reads them."""

    payload: dict[str, Any]
    stated: dict[str, str]  # result line -> its Amount cell as written
    unit: str


def _value(cell: str, tables: types.ModuleType, suffix: str = "") -> float | None:
    """A figure, or None for a cell that states none (never zero); raises `_NotChecked`."""
    if blank(cell, tables) or _plain(cell) in NOT_APPLICABLE:
        return None
    read = figure(cell, tables, suffix)
    if isinstance(read, str):
        raise _NotChecked(read)
    return read[0]


def _funding_rows(table: Table, line: int) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for row in table[1]:
        name = _plain(row[line])
        head, colon, rest = name.partition(":")
        key = f"facility:{rest.strip()}" if colon and _label(head) == "facility" else _label(name)
        if key in rows:
            raise _NotChecked(f"`### {FUNDING_HEADING}` has two `{name}` rows")
        rows[key] = row
    return rows


def _money_unit(rows: list[list[str]], cols: dict[str, int], name: str) -> tuple[str, str]:
    pairs = {(currency_of(r[cols["Currency"]]), scale_of(r[cols["Scale"]])) for r in rows}
    currency, scale = next(iter(pairs)) if len(pairs) == 1 else (None, None)
    if currency is None or scale is None:
        shown = "; ".join(sorted({f"{r[cols['Currency']]} {r[cols['Scale']]}" for r in rows}))
        raise _NotChecked(f"{name} rows state different or unread currencies or scales: {shown}")
    return currency, scale


def _facility(
    name: str, row: list[str], cols: dict[str, int], tables: types.ModuleType
) -> dict[str, Any]:
    committed = _label(row[cols["Committed"]])
    return {
        "facility": name,
        "commitment": _value(row[cols["Amount"]], tables),
        "drawn": _value(row[cols["Drawn"]], tables),
        "years_to_expiry": _value(row[cols["Years"]], tables, "year"),
        "committed": {"yes": True, "no": False}.get(committed),  # anything else is not asserted
    }


def _instruments(text: str, scale: str, tables: types.ModuleType) -> list[dict[str, Any]]:
    table = register_table(text, "T3D.2")
    cols = table if isinstance(table, str) else _columns(table, WALL_COLUMNS, "T3D.2")
    if isinstance(table, str) or isinstance(cols, str):
        raise _NotChecked(str(cols))
    out: list[dict[str, Any]] = []
    for row in table[1]:
        name = row[cols["Instrument"]]
        if scale_of(row[cols["Scale"]]) != scale:
            raise _NotChecked(
                f"T3D.2 `{name}` is in scale `{row[cols['Scale']]}`, the funding gap in `{scale}`"
            )
        out.append(
            {
                "instrument": name,
                "amount": _value(row[cols["Amount"]], tables),
                "years_to_maturity": _value(row[cols["Years to Maturity"]], tables, "year"),
                # an unread currency stays as written, so the script's own guard refuses to total it
                "currency": currency_of(row[cols["Currency"]]) or row[cols["Currency"]],
            }
        )
    return out


def _read_funding(text: str, tables: types.ModuleType) -> _Funding:
    table = heading_table(text, FUNDING_HEADING)
    cols = (
        table
        if isinstance(table, str)
        else _columns(table, FUNDING_COLUMNS, f"`### {FUNDING_HEADING}`")
    )
    if isinstance(table, str) or isinstance(cols, str):
        raise _NotChecked(str(cols))
    rows = _funding_rows(table, cols["Line"])
    money = [r for k, r in rows.items() if k != "horizon" and not blank(r[cols["Amount"]], tables)]
    currency, scale = _money_unit(money, cols, f"`### {FUNDING_HEADING}`")

    def single(line: str, column: str, suffix: str = "") -> float | None:
        row = rows.get(_label(line))
        return None if row is None else _value(row[cols[column]], tables, suffix)

    payload = {
        "horizon_years": single("Horizon", "Years", "year"),
        "currency": currency,
        "cash": single("Cash", "Amount"),
        "forecast_fcf": single("Forecast free cash flow", "Amount"),
        "facilities": [
            _facility(k.split(":", 1)[1], r, cols, tables)
            for k, r in rows.items()
            if k.startswith("facility:")
        ],
        "instruments": _instruments(text, scale, tables),
    }
    stated = {
        line: rows[_label(line)][cols["Amount"]] for line in FUNDING_RESULTS if _label(line) in rows
    }
    return _Funding(payload, stated, f"{currency} {scale}")


def _cp3c(text: str, loaded: Loaded) -> list[Outcome]:
    try:
        funding = _read_funding(text, loaded.tables)
        view = loaded.script.compute(funding.payload)["as_of_balance_sheet_date"]
    except _NotChecked as why:
        return [_funding_where(line)("not checked", reason=str(why)) for line in FUNDING_RESULTS]
    except ValueError as error:  # the script refuses: no horizon, no three-letter currency
        cause = f"the script refused the inputs: {error}"
        return [_funding_where(line)("not checked", reason=cause) for line in FUNDING_RESULTS]
    return [_funding_line(line, funding, view, loaded.tables) for line in FUNDING_RESULTS]


def _funding_line(
    line: str, funding: _Funding, view: dict[str, Any], tables: types.ModuleType
) -> Outcome:
    where = _funding_where(line)
    part, key, formula = FUNDING_RESULTS[line]
    stated = funding.stated.get(line)
    if stated is None or blank(stated, tables):
        return where("not checked", stated=stated, reason=f"the handoff states no {line} figure")
    recomputed = view[part].get(key)
    if recomputed is None:
        return where("not checked", stated=stated, reason=str(view[part].get("reason")))
    return _judged(_Claim(where, stated, recomputed, AMOUNT_STEP, funding.unit, formula), tables)


# --- the checks, their issues and their record --------------------------------------------------

CHECKS: dict[str, tuple[str, Callable[[str, Loaded], list[Outcome]]]] = {
    "CP-2D": (LIQUIDITY_BRIDGE, _cp2d),
    "CP-3C": (FUNDING_GAP, _cp3c),
}
# The instruction each checked module is sent before its method block (the launcher adds it).
NOTES = {"CP-2D": CP2D_NOTE, "CP-3C": CP3C_NOTE}


def run(module: str, text: str) -> tuple[Outcome, ...]:
    """Every check the module's method scripts make on this handoff; none for a module without
    one. A script that cannot be loaded or that fails is one "not checked" outcome, never a
    raise."""
    if module not in CHECKS:
        return ()
    path, check = CHECKS[module]
    try:
        return tuple(check(text, _loaded(path)))
    except Exception as error:  # noqa: BLE001 - a script failure must never stop a run
        cause = f"the check could not run: {type(error).__name__}: {error}"
        return (Outcome(module, path, "all", "", "", "not checked", reason=cause),)


def issue(outcome: Outcome) -> str:
    """The acceptance issue for a disagreement, in words the module can act on."""
    unit = "" if outcome.unit in (None, "months") else f" {outcome.unit}"
    recomputed = "Not Calculable" if outcome.recomputed is None else f"{outcome.recomputed:g}{unit}"
    return (
        f"{outcome.register} row `{outcome.row}` states {outcome.stated}{unit}, but the method's "
        f"`{Path(outcome.script).name}` recomputes {recomputed} from the handoff's own rows. "
        f"{outcome.reason}. Correct the figure or the rows it rests on."
    )


def issues(module: str, text: str) -> tuple[str, ...]:
    """The acceptance issues: one per disagreement; a figure not checked is no issue."""
    return tuple(issue(o) for o in run(module, text) if o.status == "disagreed")


def record(module: str, raw: bytes) -> dict[str, Any] | None:
    """Every check's outcome for one response, for the run's files; None for a module without a
    method-script check."""
    if module not in CHECKS:
        return None
    try:
        outcomes = run(module, raw.decode("utf-8"))
    except UnicodeDecodeError:
        path = CHECKS[module][0]
        outcomes = (Outcome(module, path, "all", "", "", "not checked", reason="not UTF-8"),)
    hashes = registered()
    return {
        "kind": RECORD_KIND,
        "module": module,
        "response_sha256": _sha(raw),
        "scripts": {path: hashes.get(path) for path in sorted({o.script for o in outcomes})},
        "checks": [asdict(o) for o in outcomes],
    }
