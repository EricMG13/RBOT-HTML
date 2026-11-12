"""CP-2G facility schedule: stated debt-facility terms to a three-year interest and repayment plan.

Pure arithmetic in `cp2g`'s exact context. A facility states either a fixed rate, or a reference
rate (one fraction per forecast year) with a spread and an optional floor. Missing is never zero:
a null amortisation means the facility is not repaid, and every other term is required by its form.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from typing import Annotated

from pydantic import Field, model_validator

from deploy_vii.contracts import Contract
from deploy_workflow.owners import cp2g

PERCENT_PATTERN = r"^[0-9]{1,2}(\.[0-9]{1,4})?$"
Percent = Annotated[str, Field(pattern=PERCENT_PATTERN)]
_CEILINGS = (("fixed_rate_pct", 30), ("spread_pct", 20), ("floor_pct", 10))


class Facility(Contract):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    balance: cp2g.Amount
    fixed_rate_pct: Percent | None
    spread_pct: Percent | None
    floor_pct: Percent | None
    # lax: a Python caller passes the JSON array as a list; the Contract's strict mode wants a tuple
    reference_rate: (
        Annotated[tuple[cp2g.Growth, cp2g.Growth, cp2g.Growth], Field(strict=False)] | None
    )
    annual_amortisation: cp2g.Amount | None
    maturity: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")] | None

    @model_validator(mode="after")
    def _one_rate_form(self) -> "Facility":
        for field, ceiling in _CEILINGS:
            value = getattr(self, field)
            if value is not None and Decimal(value) > ceiling:
                raise ValueError(f"{field} {value} is above {ceiling}")
        floating = (self.reference_rate, self.spread_pct)
        if self.fixed_rate_pct is not None:
            if any(term is not None for term in (*floating, self.floor_pct)):
                raise ValueError("a facility states a fixed rate or a floating one, not both")
        elif self.reference_rate is None or self.spread_pct is None:
            raise ValueError("a facility states a fixed rate, or a reference rate with a spread")
        if self.maturity is not None:
            date.fromisoformat(self.maturity)
        return self


@dataclass(frozen=True)
class FacilityYear:
    opening: Decimal
    rate: Decimal
    interest: Decimal
    repaid: Decimal
    closing: Decimal


@dataclass(frozen=True)
class Schedule:
    rows: tuple[tuple[FacilityYear, FacilityYear, FacilityYear], ...]

    def totals(
        self,
    ) -> tuple[tuple[Decimal, Decimal], tuple[Decimal, Decimal], tuple[Decimal, Decimal]]:
        """(interest, repayment) for each forecast year, summed over the facilities."""
        with localcontext(cp2g._EXACT):
            sums = [
                (
                    sum((row[t].interest for row in self.rows), Decimal(0)),
                    sum((row[t].repaid for row in self.rows), Decimal(0)),
                )
                for t in range(3)
            ]
        return sums[0], sums[1], sums[2]


def _rate(facility: Facility, year: int) -> Decimal:
    if facility.fixed_rate_pct is not None:
        return Decimal(facility.fixed_rate_pct) / 100
    assert facility.reference_rate is not None and facility.spread_pct is not None
    reference = Decimal(facility.reference_rate[year])
    if facility.floor_pct is not None:
        reference = max(reference, Decimal(facility.floor_pct) / 100)
    return reference + Decimal(facility.spread_pct) / 100


def _years(facility: Facility) -> tuple[FacilityYear, FacilityYear, FacilityYear]:
    amortisation = Decimal(facility.annual_amortisation or 0)
    opening = Decimal(facility.balance)
    years: list[FacilityYear] = []
    for t in range(3):
        rate = _rate(facility, t)
        repaid = min(amortisation, opening)
        years.append(FacilityYear(opening, rate, opening * rate, repaid, opening - repaid))
        opening -= repaid
    return years[0], years[1], years[2]


def schedule(facilities: Sequence[Facility]) -> Schedule:
    """One three-year triple per facility, in input order."""
    with localcontext(cp2g._EXACT):
        return Schedule(tuple(_years(f) for f in facilities))
