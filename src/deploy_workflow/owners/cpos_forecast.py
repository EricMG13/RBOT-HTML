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
from decimal import Decimal
from typing import Annotated

from pydantic import Field, ValidationError, model_validator

from deploy_vii.contracts import Contract
from deploy_vii.live.schema import exact_json, json_object
from deploy_vii.readiness import shape_issues
from deploy_workflow.owners import cp2g

HEADING = "### Forecast inputs (machine-readable)"
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
    amount: Signed | None
    reason: str | None

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


def _without_block(text: str) -> str:
    """The handoff less its inputs block, so a CP-1 operand is checked against CP-1's own tables
    and not against the block that states it."""
    kept: list[str] = []
    inside = False
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.strip() == HEADING:
            inside = True
        elif inside and re.match(r"#{1,6}\s", line):
            inside = False
        if not inside:
            kept.append(line)
    return "\n".join(kept)


def _printed(text: str, amount: str) -> bool:
    """Whether CP-1 prints the amount as a whole number token, with or without thousands commas."""
    whole, dot, fraction = amount.lstrip("-").partition(".")
    forms = {f"{whole}{dot}{fraction}", f"{int(whole):,}{dot}{fraction}"}
    return any(
        re.search(rf"(?<![0-9.,]){re.escape(form)}(?![0-9]|[.,][0-9])", text) for form in forms
    )


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
    printed = _without_block(cp1_text) if source == "CP-1" else cp1_text
    for key, operand in inputs.base.items():
        if operand.amount is not None and not _printed(printed, operand.amount):
            raise ValueError(f"{source}: base {key} {operand.amount} is not printed in CP-1")
    return inputs


def _cell(value: cp2g.Val) -> dict[str, str | None]:
    amount = None if value.amount is None else format(value.amount, "f")
    return {"amount": amount, "reason": value.reason}


def _stated(key: str, case: CaseDrivers | None) -> dict[str, object]:
    return {} if case is None else {key: case.model_dump(mode="json", exclude_none=True)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(document: object) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def model_files(cp1: bytes, handoff: bytes, source: str = "CP-2G") -> dict[str, bytes]:
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
    outputs = {}
    for case, (submitted, shock_pair) in cases.items():
        drivers = cp2g.Drivers.from_submission(submitted)
        result = cp2g.forecast(operands=operands, drivers=drivers, shock=shock_pair)
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
            "scope_limits": [LIMIT if source == "CP-2G" else LAYER1_LIMIT, *inputs.scope_limits],
        }
    )
    calculation = _json(
        {
            "schema_version": "cpos-model/1",
            "annual_periods": [],
            "values": {},
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
