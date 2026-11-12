"""The CP-2G forecast files a launcher run publishes beside its report. Pure: bytes in, bytes out.

The forecast source's handoff (CP-2G's, else CP-1's run-rate block) states inputs only, in one
fenced JSON block under ``HEADING``: the CP-1 base amounts, the seven driver
paths, an optional downside shock and the three forecast years. Python (``cp2g.forecast``,
38-digit exact) computes every figure; no figure is read from the handoff's prose. A block that
is missing, malformed or states a base amount CP-1 does not print raises
ValueError; the caller decides what that means (the run fails open, see cpos.run_handoffs).
"""

import hashlib
import json
import re
from dataclasses import fields
from datetime import date, timedelta
from decimal import Decimal, Inexact, localcontext
from typing import Annotated

from pydantic import Field, ValidationError, model_validator

from deploy_vii.contracts import Contract
from deploy_vii.live.schema import exact_json, json_object
from deploy_vii.readiness import shape_issues
from deploy_workflow.owners import cp2g
from deploy_workflow.owners.cpos_facilities import Facility, Schedule, schedule
from deploy_workflow.prose_checks import FORECAST_HEADING, reader_passages

HEADING = FORECAST_HEADING
SCHEMA_VERSION = "cpos-forecast-inputs/1"
LIMIT = (
    "Every figure is Python's arithmetic over inputs the CP-2G handoff stated; the inputs, not "
    "the arithmetic, are unreviewed. Not analytical review."
)
# Owner, 2026-11-11: a forecast works from layer 1 and is better with CP-2G. Without CP-2G the
# source is CP-1's run-rate block, and the published limit says so.
LAYER1_LIMIT = (
    "Every figure is Python's arithmetic over run-rate inputs the CP-1 handoff stated, from the "
    "financial foundation's own figures; no CP-2G model, case or shock was run. The inputs, not "
    "the arithmetic, are unreviewed. Not analytical review."
)
SOURCES = ("CP-2G", "CP-1")
Signed = Annotated[str, Field(pattern=r"^-?[0-9]{1,6}(\.[0-9]{1,4})?$")]


class Operand(Contract):
    """A base operand. Either source's block may also say where it read an amount: the first cell
    of the table row (`row`) and the header of the period column (`period`)."""

    amount: Signed | None
    reason: str | None
    row: str | None = None
    period: str | None = None

    @model_validator(mode="after")
    def one_of(self) -> "Operand":
        if (self.amount is None) == (self.reason is None):
            raise ValueError("an operand states an amount or a reason, never both or neither")
        return self


class Shock(Contract):
    ebitda_decline: cp2g.Share
    rate_increase: cp2g.Share


class CaseDrivers(Contract):
    """A CP-2G case's drivers that differ from base; every other driver is inherited from base."""

    revenue_growth: cp2g.GrowthDriver | None = None
    ebitda_margin: cp2g.FractionDriver | None = None
    capex_pct_revenue: cp2g.FractionDriver | None = None
    tax_wc_pct_revenue: cp2g.FractionDriver | None = None
    interest_rate: cp2g.FractionDriver | None = None
    dividends: cp2g.AmountDriver | None = None
    debt_repayment: cp2g.AmountDriver | None = None

    @model_validator(mode="after")
    def names_a_driver(self) -> "CaseDrivers":
        if all(getattr(self, name) is None for name in cp2g.DRIVERS):
            raise ValueError("a case names at least one driver; write null for no case")
        return self

    def over(self, base: cp2g.BaseDrivers) -> cp2g.BaseDrivers:
        changed = {n: getattr(self, n) for n in cp2g.DRIVERS if getattr(self, n) is not None}
        return base.model_copy(update=changed)


class Span(Contract):
    year: int
    start: str
    end: str


class ForecastInputs(Contract):
    schema_version: str = Field(pattern=re.escape(SCHEMA_VERSION))
    base: dict[str, Operand]
    base_drivers: cp2g.BaseDrivers
    downside_shock: Shock | None
    upside_drivers: CaseDrivers | None = None
    downside_drivers: CaseDrivers | None = None
    years: tuple[Span, Span, Span]
    facilities: Annotated[tuple[Facility, ...], Field(min_length=1, max_length=40)] | None = None
    scope_limits: tuple[str, ...]

    @model_validator(mode="after")
    def consistent(self) -> "ForecastInputs":
        if set(self.base) != set(cp2g.OPERAND_METRIC):
            raise ValueError(f"base must state exactly {', '.join(cp2g.OPERAND_METRIC)}")
        first = self.years[0].year
        if [s.year for s in self.years] != [first, first + 1, first + 2]:
            raise ValueError("years must be three consecutive fiscal years")
        if any(date.fromisoformat(s.start) > date.fromisoformat(s.end) for s in self.years):
            raise ValueError("a year starts after it ends")
        if any(
            date.fromisoformat(b.start) != date.fromisoformat(a.end) + timedelta(days=1)
            for a, b in zip(self.years, self.years[1:], strict=False)
        ):
            raise ValueError("each year must start the day after the previous one ends")
        if self.facilities is not None and len({f.name.casefold() for f in self.facilities}) < len(
            self.facilities
        ):
            raise ValueError("facility names must be unique")
        return self


def _block(text: str, source: str = "CP-2G") -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    starts = [i for i, line in enumerate(lines) if line.strip() == HEADING]
    if len(starts) != 1:
        raise ValueError(f"{source}: needs exactly one `{HEADING}` heading, found {len(starts)}")
    body: list[str] = []
    for line in lines[starts[0] + 1 :]:
        if re.match(r"#{1,6}\s", line):
            break
        body.append(line)
    found = re.findall(r"^```json\n(.*?)\n```[ \t]*$", "\n".join(body), re.DOTALL | re.MULTILINE)
    if len(found) != 1 or "\n".join(body).count("```") != 2:
        raise ValueError(f"{source}: `{HEADING}` needs exactly one fenced json block")
    return str(found[0])


def _printed(text: str, amount: str) -> bool:
    """Whether CP-1 prints the amount as a whole number token, with or without thousands commas."""
    whole, dot, fraction = amount.lstrip("-").partition(".")
    forms = {f"{whole}{dot}{fraction}", f"{int(whole):,}{dot}{fraction}"}
    return any(
        re.search(rf"(?<![0-9.,]){re.escape(form)}(?![0-9]|[.,][0-9])", text) for form in forms
    )


def _printed_percent(text: str, value: str) -> bool:
    """Whether CP-1 prints the rate term as stated, as a percent: `6.00%` or `6.00 %`, the number
    not the tail of a longer one."""
    return re.search(rf"(?<![0-9.,]){re.escape(value)} ?%", text) is not None


_CELL = re.compile(r"(?:\+|(?P<minus>[-\u2212]))?(?P<digits>[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)")
_BRACKET = re.compile(r"\((?P<digits>[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\)")


def _cut(text: str, size: int = 80) -> str:
    """Handoff text quoted in a message: at most `size` characters, then `...`."""
    return text if len(text) <= size else text[:size] + "..."


def _plain(cell: str) -> str:
    """A label or header as compared: trimmed, without Markdown emphasis; case kept."""
    return cell.strip().strip("*_`").strip()


def _signed(cell: str) -> Decimal | None:
    """`1,000`, `+1,000`, `-1,000`, `\u22121,000` and `(1,000)` as signed numbers; anything else,
    such as a unit or scale suffix, a percentage or `n.a.`, is not a number."""
    text = _plain(cell)
    with localcontext(cp2g._EXACT):  # a numeral the context cannot hold raises Inexact, not rounds
        if (bracket := _BRACKET.fullmatch(text)) is not None:
            return -Decimal(bracket["digits"].replace(",", ""))
        if (plain := _CELL.fullmatch(text)) is None:
            return None
        value = Decimal(plain["digits"].replace(",", ""))
        return -value if plain["minus"] else value


def _tables(text: str) -> list[list[list[str]]]:
    """The Markdown tables of CP-1 outside fenced code, `## Sources`, the forecast block and the
    reader passages: each a list of rows of cells, header first, delimiter row dropped."""
    skipped = {number for body in reader_passages(text).values() for number, _ in body}
    tables: list[list[list[str]]] = []
    run: list[list[str]] = []
    seen_delimiter = False
    fence = ""  # the marker (``` or ~~~) of the code fence in force, else empty
    block = sources = False
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if marker := next((m for m in ("```", "~~~") if stripped.startswith(m)), ""):
            fence = "" if fence == marker else (fence or marker)
        fenced = bool(fence)
        heading = None if fenced else re.match(r"(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if heading is not None:
            block = stripped == HEADING
            if len(heading[1]) <= 2:
                sources = len(heading[1]) == 2 and heading[2] == "Sources"
        cells = (
            [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", stripped[1:-1])]
            if stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 1
            else None
        )
        if cells is None or fenced or block or sources or number in skipped:
            if len(run) > 1:
                tables.append(run)
            run, seen_delimiter = [], False
            continue
        if run and not seen_delimiter:
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                seen_delimiter = True
            else:
                run = [cells]  # no delimiter row under the first row: not a table
        else:
            run.append(cells)
    if len(run) > 1:
        tables.append(run)
    return tables


def _cells(text: str, label: str, period: str) -> set[str]:
    """The distinct texts of the cells at `label` (a row's first cell) and `period` (a header
    cell) over every table of the handoff."""
    found: set[str] = set()
    for table in _tables(text):
        header, *rows = table
        for column in (i for i, h in enumerate(header) if i > 0 and _plain(h) == _plain(period)):
            found.update(
                row[column] for row in rows if len(row) > column and _plain(row[0]) == _plain(label)
            )
    return found


def _agrees(key: str, cell: Decimal, amount: Decimal) -> bool:
    """The one sign rule. Working capital is read as CP-2G reads it (`Operands.from_cp1`): the
    operand is the cell with its sign reversed, so a printed (45), an investment, is 45 and a
    printed +45, a release, is -45; a magnitude match would turn a release into an outflow.
    Interest, taxes and capex are positive magnitudes however CP-1 prints them; every other
    operand compares signed."""
    with localcontext(cp2g._EXACT):
        if key == "wc":
            return -cell == amount
        return abs(cell) == amount if key in cp2g.OUTFLOWS else cell == amount


def _layer1_problem(text: str, key: str, operand: Operand) -> str | None:
    """Why the operand is not the cell it names, or None when it is. Both sources use it: CP-1's
    layer-1 block always, a CP-2G block when it names any cell."""
    if operand.amount is None:
        return (
            None
            if operand.row is None and operand.period is None
            else (f"base {key} states no amount, so it names no row or period")
        )
    row, period = operand.row or "", operand.period or ""
    if not _plain(row) or not _plain(period):
        return f"base {key} must name the `row` label and `period` header it was read from"
    where = f"row `{_cut(row, 77)}`, period `{_cut(period, 77)}`"
    found = _cells(text, row, period)
    if not found:
        return f"base {key}: no table cell of CP-1 is at {where}"
    not_the_cell = (
        f"base {key} {operand.amount} is not CP-1's cell at {where} ({_cut(min(found), 77)})"
    )
    try:
        values = {_signed(cell) for cell in found}
    except Inexact:
        return not_the_cell
    if len(found) > 1 and len(values) > 1 or None in values:
        shown = sorted(_cut(cell, 77) for cell in found)
        return f"base {key}: {where} is not one number in CP-1 ({len(found)} cells: {shown})"
    (value,) = values
    try:
        agrees = value is not None and _agrees(key, value, Decimal(operand.amount))
    except Inexact:
        agrees = False
    return None if agrees else not_the_cell


def _declined(document: dict[str, object], source: str) -> None:
    """A block whose every driver has all-null values is the method declining to forecast."""
    drivers = document.get("base_drivers")
    if not isinstance(drivers, dict) or not drivers:
        return
    if not all(
        isinstance(d, dict)
        and isinstance(d.get("values"), list)
        and bool(d["values"])
        and all(v is None for v in d["values"])
        for d in drivers.values()
    ):
        return
    limits = document.get("scope_limits")
    why = limits[0] if isinstance(limits, list) and limits and isinstance(limits[0], str) else ""
    why = why if len(why) <= 200 else why[:197] + "..."
    raise ValueError(
        f"{source}: the handoff gives no forecast drivers, so no forecast was computed"
        + (f" ({why})" if why else "")
    )


def parse(source_text: str, cp1_text: str, source: str = "CP-2G") -> ForecastInputs:
    """The validated inputs block; ValueError names the first thing wrong with it. `source` is
    the module that wrote the block: CP-2G, or CP-1 for a layer-1 forecast (base operands and
    run-rate drivers only: no shock and no cases)."""
    if source not in SOURCES:
        raise ValueError(f"{source}: is not a forecast source")
    document = json_object(_block(source_text, source))
    if document is None:
        raise ValueError(f"{source}: the forecast inputs block is not a bounded JSON object")
    _declined(document, source)
    try:
        inputs = ForecastInputs.model_validate_json(exact_json(document))
    except ValidationError as error:
        issues = shape_issues(error)
        if len(issues) <= 3:
            raise ValueError(f"{source}: forecast inputs: {'; '.join(issues)}") from error
        raise ValueError(
            f"{source}: forecast inputs: {len(issues)} problems; first: {'; '.join(issues[:3])}"
        ) from error
    if source == "CP-1" and (
        inputs.downside_shock or inputs.upside_drivers or inputs.downside_drivers
    ):
        raise ValueError("CP-1: a layer-1 forecast states no shock and no cases")
    if source == "CP-1" and inputs.facilities:
        raise ValueError("CP-1: a layer-1 forecast states no facilities")
    named = source == "CP-1" or any(
        operand.row is not None or operand.period is not None for operand in inputs.base.values()
    )
    for key, operand in inputs.base.items():
        if named:
            if (problem := _layer1_problem(cp1_text, key, operand)) is not None:
                raise ValueError(f"{source}: {problem}")
        elif operand.amount is not None and not _printed(cp1_text, operand.amount):
            raise ValueError(f"{source}: base {key} {operand.amount} is not printed in CP-1")
    if inputs.facilities:
        _check_facilities(inputs, inputs.facilities, cp1_text)
    return inputs


def _check_facilities(
    inputs: ForecastInputs, facilities: tuple[Facility, ...], cp1_text: str
) -> None:
    """Each stated term is printed in CP-1, the balances fit the base debt, and no case names a
    driver the schedule replaces."""
    for facility in facilities:
        if not _printed(cp1_text, facility.balance):
            raise ValueError(
                f"CP-2G: facility {facility.name} balance {facility.balance} is not printed in CP-1"
            )
        for field in ("fixed_rate_pct", "spread_pct", "floor_pct"):
            value = getattr(facility, field)
            if value is not None and not _printed_percent(cp1_text, value):
                raise ValueError(
                    f"CP-2G: facility {facility.name} {field} {value}% is not printed in CP-1"
                )
    debt = inputs.base["debt"].amount
    if debt is not None:
        with localcontext(cp2g._EXACT):
            total = sum((Decimal(f.balance) for f in facilities), Decimal(0))
            too_much = total > Decimal("1.25") * Decimal(debt)
            repaid = sum((r for _, r in schedule(facilities).totals()), Decimal(0))
            over_debt = repaid > Decimal(debt)
        if too_much:
            raise ValueError(
                f"CP-2G: facility balances total {format(total, 'f')}, more than 1.25 times base "
                f"debt {debt}; check the unit"
            )
        if over_debt:
            raise ValueError(
                f"CP-2G: scheduled repayments total {_plain_amount(repaid)}, more than base debt "
                f"{_plain_amount(Decimal(debt))}"
            )
    for name in ("upside_drivers", "downside_drivers"):
        case: CaseDrivers | None = getattr(inputs, name)
        if case is not None and case.debt_repayment is not None:
            raise ValueError(
                f"CP-2G: {name} states debt_repayment, which is not used when facilities are stated"
            )


_FACILITY_YEAR = ("opening", "rate", "interest", "repaid", "closing")
FACILITY_LIMIT = (
    "Cash interest on the stated facilities and scheduled repayment are computed from the "
    "facility terms the CP-2G handoff stated; the analyst's repayment assumption is not used."
)


def _cell(value: cp2g.Val) -> dict[str, str | None]:
    amount = None if value.amount is None else format(value.amount, "f")
    return {"amount": amount, "reason": value.reason}


def _stated(key: str, case: CaseDrivers | None) -> dict[str, object]:
    return {} if case is None else {key: case.model_dump(mode="json", exclude_none=True)}


def _plain_amount(amount: Decimal) -> str:
    return format(amount.normalize(), "f")


def _facility_detail(
    inputs: ForecastInputs, facilities: tuple[Facility, ...], plan: Schedule
) -> tuple[dict[str, object], list[str]]:
    """The published facility keys and the three appended scope limits."""
    per_facility = [
        {
            "name": facility.name,
            "years": [
                {"year": span.year, **{k: format(getattr(y, k), "f") for k in _FACILITY_YEAR}}
                for span, y in zip(inputs.years, row, strict=True)
            ],
        }
        for facility, row in zip(facilities, plan.rows, strict=True)
    ]
    debt = inputs.base["debt"]
    with localcontext(cp2g._EXACT):
        unallocated = (
            None
            if debt.amount is None
            else Decimal(debt.amount) - sum((Decimal(f.balance) for f in facilities), Decimal(0))
        )
    limits = [FACILITY_LIMIT]
    if unallocated is None:
        limits.append("Base debt is missing, so debt outside the stated facilities is not known.")
    elif unallocated > 0:
        limits.append(
            f"Debt of {_plain_amount(unallocated)} is not in a stated facility; it bears interest "
            "at the analyst's assumed rate and is not repaid in this forecast."
        )
    elif unallocated < 0:
        limits.append(
            f"Stated facility balances exceed base debt by {_plain_amount(-unallocated)}; "
            "interest is computed on the stated balances."
        )
    spans = [(date.fromisoformat(s.start), date.fromisoformat(s.end), s.year) for s in inputs.years]
    for facility in facilities:
        if facility.maturity is None:
            continue
        due = date.fromisoformat(facility.maturity)
        if due < spans[0][0]:
            limits.append(
                f"{facility.name} has a stated maturity of {facility.maturity}, before the "
                "forecast; it is assumed refinanced and no repayment at maturity is modelled."
            )
        elif due <= spans[2][1]:
            year = next(y for start, end, y in spans if start <= due <= end)
            limits.append(
                f"{facility.name} matures in FY{year} and is assumed refinanced; "
                "no repayment at maturity is modelled."
            )
    return {
        "facilities": [f.model_dump(mode="json") for f in facilities],
        "facility_schedule": per_facility,
        "unallocated_debt": {
            "amount": None if unallocated is None else format(unallocated, "f"),
            "reason": debt.reason if unallocated is None else None,
        },
    }, limits


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(document: object) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def _unallocated(debt: Decimal | None, facilities: tuple[Facility, ...] | None) -> Decimal | None:
    """Base debt not in a stated facility, when known and positive; else None."""
    if debt is None or facilities is None:
        return None
    with localcontext(cp2g._EXACT):
        rest = Decimal(debt) - sum((Decimal(f.balance) for f in facilities), Decimal(0))
    return rest if rest > 0 else None


def _with_remainder(
    totals: tuple[tuple[Decimal, Decimal], ...] | None,
    remainder: Decimal | None,
    rate: cp2g.Triple,
) -> tuple[tuple[Decimal, Decimal], ...] | None:
    """The schedule's pairs with the unallocated debt's interest at the case's own rate added;
    it is not repaid."""
    if totals is None or remainder is None:
        return totals
    with localcontext(cp2g._EXACT):
        return tuple(
            (i + remainder * r, repaid) for (i, repaid), r in zip(totals, rate, strict=True)
        )


def model_files(
    cp1: bytes, handoff: bytes, source: str = "CP-2G", *, history: bool = False
) -> dict[str, bytes]:
    """The five files `credit_os/store.py` reads for a model, from the CP-1 handoff and the
    forecast source's (CP-2G's, or CP-1's own for a layer-1 forecast: then `handoff` is `cp1`)."""
    inputs = parse(handoff.decode("utf-8"), cp1.decode("utf-8"), source)
    operands = cp2g.Operands(
        **{
            key: cp2g.Val(None if o.amount is None else Decimal(o.amount), o.reason)
            for key, o in inputs.base.items()
        }
    )
    # Owner, 2026-11-10: CP-2G's own cases are computed from their changed drivers; CP-2A's shock
    # is a separate case on base drivers, never compounded with CP-2G's downside.
    base = inputs.base_drivers
    cases: dict[str, tuple[cp2g.BaseDrivers, tuple[Decimal, Decimal] | None]] = {
        "REFERENCE": (base, None)
    }
    if inputs.upside_drivers is not None:
        cases["UPSIDE"] = (inputs.upside_drivers.over(base), None)
    if inputs.downside_drivers is not None:
        cases["DOWNSIDE_DRIVERS"] = (inputs.downside_drivers.over(base), None)
    if inputs.downside_shock is not None:
        shock = inputs.downside_shock
        cases["DOWNSIDE"] = (base, (Decimal(shock.ebitda_decline), Decimal(shock.rate_increase)))
    facilities = inputs.facilities
    plan = None if facilities is None else schedule(facilities)
    totals = None if plan is None else plan.totals()
    remainder = _unallocated(operands.debt.amount, facilities)
    outputs = {}
    for case, (submitted, shock_pair) in cases.items():
        drivers = cp2g.Drivers.from_submission(submitted)
        result = cp2g.forecast(
            operands=operands,
            drivers=drivers,
            shock=shock_pair,
            schedule=_with_remainder(totals, remainder, drivers.interest_rate),
        )
        outputs[case] = {
            "years": [
                {
                    "year": span.year,
                    "planning_start": span.start,
                    "planning_end": span.end,
                    **{f.name: _cell(getattr(year, f.name)) for f in fields(cp2g.Year)},
                }
                for span, year in zip(inputs.years, result.years, strict=True)
            ]
        }
    detail, limits = (
        ({}, [])
        if facilities is None or plan is None
        else _facility_detail(inputs, facilities, plan)
    )
    exact = _json(
        {
            "schema_version": "cpos-forecast-exact/1",
            "consumed": {
                "CP-1.md": _sha(cp1),
                **({"CP-2G.md": _sha(handoff)} if source == "CP-2G" else {}),
            },
            "base": {key: _cell(value) for key, value in operands.items()},
            "reference_drivers": inputs.base_drivers.model_dump(mode="json"),
            "downside_shock": None
            if inputs.downside_shock is None
            else inputs.downside_shock.model_dump(mode="json"),
            # Written only when stated, so a delivery made before cases existed re-derives
            # byte for byte.
            **_stated("upside_drivers", inputs.upside_drivers),
            **_stated("downside_drivers", inputs.downside_drivers),
            "outputs": outputs,
            **detail,
            "scope_limits": [
                LIMIT if source == "CP-2G" else LAYER1_LIMIT,
                *inputs.scope_limits,
                *limits,
            ],
        }
    )
    # Imported here: cpos_periods imports this module's helpers at module level.
    from deploy_workflow.owners.cpos_periods import history as period_history

    named = {
        key: (o.row, o.period)
        for key, o in inputs.base.items()
        if o.amount is not None and o.row is not None and o.period is not None
    }
    calculation = _json(
        {
            "schema_version": "cpos-model/1",
            "annual_periods": [],
            "values": {},
            # Written only when asked, so a delivery made before it re-derives byte for byte.
            **(
                {
                    "history": period_history(
                        _tables(cp1.decode("utf-8")),
                        operands,
                        named=named,
                        forecast_year=inputs.years[0].year,
                    )
                }
                if history
                else {}
            ),
            "forecast_exact_file": "forecast_exact.json",
            "forecast_exact_sha256": _sha(exact),
        }
    )
    return {
        "annual.md": cp1,
        "forecast.md": handoff,
        "forecast_exact.json": exact,
        "calculation.json": calculation,
        "quarter.md": b"No quarter handoff in this run.\n",
    }
