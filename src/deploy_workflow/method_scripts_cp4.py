"""CP-4's method script, `covenant_headroom.py`, run on T4C.4 (harness:
`deploy_workflow.method_scripts`).

CP-4's SKILL gives the script T4C.4 headroom: max-ratio headroom = Threshold - Current Basis,
min-ratio headroom = Current Basis - Threshold (REF_CP-4A_04), with the direction taken from the
row's `Test Type`, "required and never inferred". The check reads T4C.4 `Test`, `Test Type`,
`Threshold`, `Current Basis`, `Headroom` and `Status` (REF_CP-4A_04's columns).

Test Type is passed to the script's own `normalise_test_type` as written (or its first word, as
`max-ratio (leverage)` gives `max-ratio`); a row whose type the script does not recognise is not
checked. Two of the script's aliases are refused here: a bare `maintenance` or `incurrence` says
when a test applies, not whether it is a ceiling or a floor, so reading one as max-ratio would be
the guess the script exists to prevent.

Threshold, Current Basis and Headroom must each be one figure in one unit: a ratio (`5.00x` or a
bare figure), a percentage, or an amount with its currency and scale. Status is compared only when
it states one of the script's words (Compliant, At threshold, Breached). Maximum additional debt
and T4C.5 basket capacity are not checked: their inputs are free text in `Formula` and `Current
Input`, not columns.
"""

import re
from dataclasses import dataclass, replace
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    ARCHIVE,
    Loaded,
    Outcome,
    Status,
    _Claim,
    _columns,
    _judged,
    _label,
    _NotChecked,
    _plain,
    _Where,
    blank,
    currency_of,
    figure,
    half,
    register_table,
    scale_of,
)

COVENANT_HEADROOM = ARCHIVE + "skills/cp-2h-ratings-migration-trigger/scripts/covenant_headroom.py"
HEADROOM_COLUMNS = ("Test", "Test Type", "Threshold", "Current Basis", "Headroom", "Status")
STATUSES = ("compliant", "at threshold", "breached")
TIMING_ONLY = ("maintenance", "incurrence")  # the script's aliases that name no direction
HEADROOM_STEP = 1e-6  # the script rounds headroom to six places
HEADROOM_FORMULA = (
    "Headroom = Threshold - Current Basis for a max-ratio test, Current Basis - Threshold for a "
    "min-ratio test (REF_CP-4A_04); positive is Compliant, zero At threshold, negative Breached"
)
CP4_NOTE = (
    "Python checks T4C.4 after you answer, with the method's own `covenant_headroom.py` (you "
    "cannot run it): each test's Headroom (max-ratio: Threshold - Current Basis; min-ratio: "
    "Current Basis - Threshold) and its Status (Compliant, At threshold or Breached). So write "
    "Test Type as `max-ratio` or `min-ratio` (it is never inferred: a row without one is not "
    "checked), and Threshold, Current Basis and Headroom each as one figure in one unit (`5.00x`). "
    "A figure that disagrees is sent back for repair; one whose input is missing is not checked, "
    "never read as zero.\n\n"
)
_UNIT_SUFFIX = re.compile(r"(?i)\s*(?:x|%)(?=\)?$)")
_COMPARATOR = re.compile(r"^(?:[≤≥<>=]|&[lg]t;)+\s*")


def _where(figure_name: str, test: str) -> _Where:
    return _Where("CP-4", COVENANT_HEADROOM, f"{figure_name}: {test}", "T4C.4")


@dataclass(frozen=True)
class _Figure:
    """One cell as read: its figure text without its unit, and the unit."""

    text: str
    unit: str  # `x` for a ratio (or a bare figure), `%`, or `<currency> <scale>`


def _figure(cell: str) -> _Figure:
    text = _COMPARATOR.sub("", _plain(cell))
    if text.rstrip(") ").endswith("%"):
        return _Figure(_UNIT_SUFFIX.sub("", text), "%")
    currency, scale = currency_of(text), scale_of(text)
    if currency and scale:
        return _Figure(core.bare(text), f"{currency} {scale}")
    return _Figure(_UNIT_SUFFIX.sub("", text), "x")


def _test_type(cell: str, loaded: Loaded) -> str:
    """The script's direction for the stated type, or `_NotChecked` (never a default)."""
    text, reason = _plain(cell), ""
    if blank(text, loaded.tables):
        raise _NotChecked("T4C.4 states no Test Type, and the script never infers one")
    for candidate in (text, re.split(r"[\s(]", text, maxsplit=1)[0]):
        if _label(candidate) in TIMING_ONLY:
            raise _NotChecked(f"Test Type `{cell}` names when the test applies, not its direction")
        try:
            return str(loaded.script.normalise_test_type(candidate, "T4C.4"))
        except ValueError as error:
            reason = str(error)
    raise _NotChecked(f"the script does not read Test Type `{cell}`: {reason}")


def _row(row: list[str], cols: dict[str, int], loaded: Loaded) -> list[Outcome]:
    test = _plain(row[cols["Test"]])
    headroom, status = _where("Headroom", test), _where("Status", test)
    try:
        result = _headroom(row, cols, loaded)
    except _NotChecked as error:
        return [w("not checked", reason=str(error)) for w in (headroom, status)]
    stated = _figure(row[cols["Headroom"]])
    if blank(row[cols["Headroom"]], loaded.tables):
        first = headroom("not checked", reason="T4C.4 states no Headroom figure")
    elif stated.unit != result["unit"]:
        why = f"the Headroom is in `{stated.unit}`, its test in `{result['unit']}`"
        first = headroom("not checked", stated=row[cols["Headroom"]], reason=why)
    else:
        claim = _Claim(
            headroom, stated.text, result["headroom"], HEADROOM_STEP, stated.unit, HEADROOM_FORMULA
        )
        first = _judged(replace(claim, slack=result["slack"]), loaded.tables)
    return [first, _status(status, row[cols["Status"]], result)]


def _headroom(row: list[str], cols: dict[str, int], loaded: Loaded) -> dict[str, Any]:
    direction = _test_type(row[cols["Test Type"]], loaded)
    values: dict[str, float] = {}
    units: set[str] = set()
    slack = 0.0
    for name in ("Threshold", "Current Basis"):
        cell = row[cols[name]]
        if blank(cell, loaded.tables):
            raise _NotChecked(f"T4C.4 states no {name} (missing, not zero)")
        read = _figure(cell)
        number = figure(read.text, loaded.tables)
        if isinstance(number, str):
            raise _NotChecked(f"{name}: {number}")
        values[name], units = number[0], units | {read.unit}
        slack += half(number[1])  # a difference: its inputs' rounding adds up
    if len(units) != 1:
        raise _NotChecked(f"Threshold and Current Basis are in different units: {sorted(units)}")
    test: dict[str, Any] = {"test": _plain(row[cols["Test"]]), "test_type": direction}
    test |= {"threshold": values["Threshold"], "current_ratio": values["Current Basis"]}
    return {**loaded.script.headroom(test), "unit": units.pop(), "slack": slack}


def _status(where: _Where, cell: str, result: dict[str, Any]) -> Outcome:
    stated = _label(cell)
    word = next((s for s in STATUSES if stated == s or stated.startswith(s + " ")), None)
    if word is None:
        why = f"Status `{cell}` is none of Compliant, At threshold, Breached"
        return where("not checked", stated=cell, reason=why)
    found = str(result["status"])
    if _label(found) != word and abs(result["headroom"]) <= result["slack"]:
        why = (
            f"the recomputed headroom {result['headroom']:g} is within the displayed inputs' "
            f"rounding ({result['slack']:g}) of zero, so they cannot settle `{cell}` against "
            f"{found}"
        )
        return where("not checked", stated=cell, recomputed_label=found, reason=why)
    agreed: Status = "agreed" if _label(found) == word else "disagreed"
    return where(agreed, stated=cell, recomputed_label=found, reason=HEADROOM_FORMULA)


def check(text: str, loaded: Loaded) -> list[Outcome]:
    """Each T4C.4 test's headroom and status, recomputed by the script from its own row."""
    table = register_table(text, "T4C.4")
    cols = table if isinstance(table, str) else _columns(table, HEADROOM_COLUMNS, "T4C.4")
    if isinstance(table, str) or isinstance(cols, str):
        return [_where("Headroom", "all")("not checked", reason=str(cols))]
    return [o for row in table[1] for o in _row(row, cols, loaded)]


core.register("CP-4", COVENANT_HEADROOM, check, CP4_NOTE)
