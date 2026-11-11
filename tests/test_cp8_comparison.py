"""CP-8 comparison answer: the Dimension table covers the eight requested dimensions."""

from datetime import date

import pytest

from deploy_vii.contracts import Run
from deploy_workflow.handoff_delivery import comparison_files

OLD_DIMENSIONS = (
    "Values",
    "Periods",
    "Assumptions",
    "Conclusions",
    "Sources",
    "Limitations",
    "Output scope",
)
ALL_DIMENSIONS = (*OLD_DIMENSIONS, "Presentation")

RUN = Run(
    run_id="cp8-test",
    issuer_id="TDG",
    issuer_name="TransDigm Group Incorporated",
    as_of=date(2024, 9, 30),
    case_kind="public",
    pathway="credit_snapshot",
    requested_modules=("CP-1", "CP-8"),
)


def answer(dimensions: tuple[str, ...]) -> bytes:
    rows = "".join(f"| {d} | Prior {d} | Current {d} |\n" for d in dimensions)
    return (
        "## Request\n\nCompare prior and current.\n\n"
        "## Sources\n\nS1.\n\n"
        "## Findings\n\n"
        "**Bundle**\n\n"
        "| Bundle | Run | Publication |\n| --- | --- | --- |\n"
        "| Prior | run-a | report A |\n| Current | run-b | report B |\n\n"
        "**Dimension**\n\n"
        "| Dimension | Prior | Current |\n| --- | --- | --- |\n" + rows + "\n"
        "**Section**\n\n"
        "| Section | Prior | Current |\n| --- | --- | --- |\n"
        "| Key findings | present | present |\n\n"
        "**Restriction**\n\n"
        "| Restriction | Prior | Current |\n| --- | --- | --- |\n"
        "| Scope | stated | stated |\n\n"
        "## Calculations\n\nNone.\n\n"
        "## Gaps\n\nNone.\n\n"
        "## Next module\n\nNone.\n"
    ).encode()


def test_eight_dimension_answer_is_accepted() -> None:
    files = comparison_files(RUN, answer(ALL_DIMENSIONS), {})
    assert {"CP-8.md", "report.html", "delivery.json"} <= set(files)
    assert b"Eight requested comparison dimensions" in files["view.json"]


def test_seven_old_dimensions_are_refused() -> None:
    with pytest.raises(ValueError, match=r"^cp8_dimensions: .*eight"):
        comparison_files(RUN, answer(OLD_DIMENSIONS), {})
