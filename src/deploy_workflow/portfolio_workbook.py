"""The portfolio workbook in a CP-OS run (ruling 2026-11-15-full-assessment-portfolio-workbook).

The full credit assessment and the portfolio decision collect the fund's workbook: its mandate,
exposures and compliance limits in the layout of the portfolio template
(`deploy_vii.inputs.portfolio`). It reaches the modules as an ordinary source, as every uploaded
file does. This module finds it among the run's sources by its sheets, runs the template's checks
on it against the run's as-of date (`validate_portfolio_bytes`), and words what CP-0, CP-3 and
CP-6 are told and what the launcher prints. A workbook that fails a check is not refused: it stays
a source, and the three modules are told each finding, so no figure that does not reconcile can
become a live constraint or exposure (the CP-6A method's own rule: "mismatched or stale rows create
a gap and cannot become a live constraint or exposure"). It computes nothing a module owns.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from urllib.parse import unquote

from deploy_vii.inputs.portfolio import SHEETS, Issue, PortfolioReport, validate_portfolio_bytes
from deploy_vii.preparation import xlsx_content

# The pathways whose run start page asks for the workbook (owner, 2026-11-15: "yes, wire in the
# portfolio workbook."). Elsewhere a workbook is an ordinary source and nothing here applies.
PATHWAYS = frozenset({"credit_snapshot", "portfolio_decision"})
TOLD = ("CP-0", "CP-3", "CP-6")
# A source is a portfolio workbook when at least two of the template's required sheets are named in
# it, so one misnamed sheet is still found (and reported by the checks).
SIGNATURE = tuple(sheet.name for sheet in SHEETS if not sheet.optional)
SIGNATURE_LEAST = 2
LISTED_AT_MOST = 40  # findings listed in an instruction; the rest are counted
COMMAND = "uv run deploy-vii validate-input portfolio <file> --as-of <the run's as-of date>"
_LAYOUT = (
    "the layout of the portfolio template (its sheets " + ", ".join(SIGNATURE[:-1]) + " and "
    f"{SIGNATURE[-1]})"
)


@dataclass(frozen=True)
class Workbook:
    source: str  # The pinned source name.
    report: PortfolioReport


@dataclass(frozen=True)
class PortfolioCheck:
    """`collected`: the pathway asks for the workbook and the launcher looked for it.
    `declared`: the run's context says one was chosen (attachments.portfolio_workbook)."""

    collected: bool
    declared: bool
    workbooks: tuple[Workbook, ...] = ()

    @property
    def failing(self) -> tuple[Workbook, ...]:
        return tuple(book for book in self.workbooks if not book.report.ok)


NOT_COLLECTED = PortfolioCheck(collected=False, declared=False)


def sheet_names(raw: bytes) -> tuple[str, ...]:
    """The sheet names of an OOXML workbook, or () when it cannot be read as one."""
    try:
        coverage = xlsx_content(raw).coverage
    except Exception:  # noqa: BLE001 - any reader failure means "not a workbook here"
        return ()
    return tuple(unquote(item.locator.removeprefix("sheet:")) for item in coverage)


def is_portfolio_workbook(raw: bytes) -> bool:
    return len(set(sheet_names(raw)) & set(SIGNATURE)) >= SIGNATURE_LEAST


def check(
    workbooks: Mapping[str, bytes], *, pathway: str, declared: bool, run_date: date
) -> PortfolioCheck:
    """Find and check the portfolio workbooks among `workbooks` (source name -> bytes)."""
    if pathway not in PATHWAYS:
        return PortfolioCheck(collected=False, declared=declared)
    found = tuple(
        Workbook(name, validate_portfolio_bytes(name, raw, run_date=run_date))
        for name, raw in sorted(workbooks.items())
        if is_portfolio_workbook(raw)
    )
    return PortfolioCheck(collected=True, declared=declared, workbooks=found)


def _none_text(found: PortfolioCheck, module: str) -> str:
    if module == "CP-3" or (module == "CP-0" and not found.declared):
        return ""
    head = (
        "Portfolio workbook: the run's settings declare one (source `context`, "
        "attachments.portfolio_workbook is true), but no source is a workbook in "
        f"{_LAYOUT}, so none was checked. "
        if found.declared
        else "Portfolio workbook: none was supplied for this run. The run's settings declare "
        "none (source `context`, attachments.portfolio_workbook is false), and no source is a "
        f"workbook in {_LAYOUT}. "
    )
    tail = (
        "Record the declared workbook under `## Gaps` as a missing source.\n\n"
        if module == "CP-0"
        else "State in `### Portfolio posture`, in plain words, that the fund's mandate and "
        "limits were not supplied, so the exact portfolio constraint is not established and "
        "sizing within the fund's limits is not tested.\n\n"
    )
    return (
        head + "Take the fund's mandate, exposures and compliance limits as not supplied: do not "
        "assume a limit, an exposure or headroom. " + tail
    )


def printable(text: str) -> str:
    """Cell text a finding quotes, on one line: a line break or other control character in a
    cell is escaped, as `Issue.render` escapes it, so it cannot start a line of the instructions."""
    return "".join(
        char if char.isprintable() else char.encode("unicode_escape").decode("ascii")
        for char in text
    )


def finding_text(issue: Issue) -> str:
    """One finding as sheet and cell, then what is wrong, on one line."""
    return printable(f"{issue.sheet}!{issue.cell}: {issue.problem}")


def count(number: int, noun: str) -> str:
    return f"{number} {noun}{'' if number == 1 else 's'}"


def _result(book: Workbook) -> str:
    if book.report.ok:
        return f"`{book.source}` passes every check.\n"
    issues = book.report.issues
    lines = [f"- {finding_text(issue)}" for issue in issues[:LISTED_AT_MOST]]
    if len(issues) > LISTED_AT_MOST:
        lines.append(f"- and {len(issues) - LISTED_AT_MOST} more findings, not listed here.")
    return (
        f"`{book.source}` fails {count(len(issues), 'check')}, listed below as sheet and cell, "
        "then what "
        "is wrong. A figure a finding names does not reconcile: it is not a live constraint or "
        "exposure. Do not rest portfolio fit, sizing or a binding constraint on it; carry it as a "
        "gap with the difference stated. Figures no finding names may be read, with the "
        "limitation that the workbook failed its checks.\n" + "\n".join(lines) + "\n"
    )


# What each module does with a workbook that fails a check, and (CP-0 only) with one that passes.
_DUTY = {
    "CP-0": "Record the workbook and its check result in your source register, and each failing "
    "figure under `## Gaps`.",
    "CP-3": "Your portfolio-fit phase reads it as the method says; record each figure that does "
    "not reconcile under `## Gaps`.",
    "CP-6": "State in `### Portfolio posture`, in plain words and without cell references, which "
    "totals or values do not reconcile and that the posture does not rest on them.",
}
_PASSED = {"CP-0": "Record the workbook and its check result in your source register."}


def instructions(found: PortfolioCheck, module: str, as_of: date) -> str:
    """What `module` is told about the portfolio workbook; "" when nothing applies."""
    if not found.collected or module not in TOLD:
        return ""
    if not found.workbooks:
        return _none_text(found, module)
    names = ", ".join(f"`{book.source}`" for book in found.workbooks)
    several = len(found.workbooks) > 1
    text = (
        f"Portfolio workbook: source{'s' if several else ''} {names} "
        f"{'are workbooks' if several else 'is a workbook'} in {_LAYOUT}: the fund's mandate, "
        "exposures and compliance limits. "
        + ("Establish which one is the fund this run's decision is for. " if several else "")
        + (
            ""
            if found.declared
            else "The run's settings do not declare a portfolio workbook (source `context`, "
            "attachments.portfolio_workbook is false): the analyst did not choose it, so use it "
            "only once its fund, measurement basis and as-of date are matched to this run. "
        )
        + "Before this call the launcher checked it against the template: its sheets and "
        "columns, its values and units, the sums and shares that must reconcile, and its dates "
        f"against the run's as-of date {as_of}. Its figures are the fund's own statement and "
        "are not otherwise reviewed: match its fund, measurement basis and as-of date to this "
        "run before use, as the method says.\n"
    )
    duty = _DUTY[module] if found.failing else _PASSED.get(module, "")
    body = text + "".join(_result(book) for book in found.workbooks)
    return body + (duty + "\n" if duty else "") + "\n"


def readiness_lines(found: PortfolioCheck) -> tuple[str, ...]:
    """The launcher's `Portfolio:` lines; () for a pathway that does not collect the workbook."""
    if not found.collected:
        return ()
    if not found.workbooks:
        if found.declared:
            return (
                (
                    "Portfolio: declared, but no source is in the portfolio template's layout; "
                    "CP-0 and CP-6 are told it is missing"
                ),
            )
        return ("Portfolio: none supplied; CP-6 states the fund's limits as not supplied",)
    lines: list[str] = []
    for book in found.workbooks:
        lines.append(f"Portfolio: {book.source}: {book.report.lines()[-1]}")
        lines += [f"Portfolio:   {issue.render()}" for issue in book.report.issues]
    if found.failing:
        lines.append(
            "Portfolio: CP-0, CP-3 and CP-6 are told each finding; no figure a finding names may "
            f"be used as a live constraint or exposure. Check a corrected workbook with: {COMMAND}"
        )
    if not found.declared:
        lines.append("Portfolio: not declared in the context; the modules are told so")
    return tuple(lines)
