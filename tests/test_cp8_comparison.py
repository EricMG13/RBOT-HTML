"""CP-8 comparison answer: the Dimension table covers the eight requested dimensions."""

import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from deploy_vii.contracts import Run, View
from deploy_vii.render import render
from deploy_vii.report_view import ReportView
from deploy_workflow.handoff_delivery import HandoffInput, comparison_files
from deploy_workflow.owners.cpos import _comparison_bundle

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
    assert {"CP-8.md", "view.json", "report-view.json", "delivery.json"} <= set(files)
    assert (
        "report.html" not in files
        and "report.html" not in json.loads(files["delivery.json"])["files"]
    )
    assert b"Eight requested comparison dimensions" in files["view.json"]


def test_seven_old_dimensions_are_refused() -> None:
    with pytest.raises(ValueError, match=r"^cp8_dimensions: .*eight"):
        comparison_files(RUN, answer(OLD_DIMENSIONS), {})


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _written(folder: Path, files: dict[str, bytes]) -> HandoffInput:
    for name, raw in files.items():
        (folder / name).write_bytes(raw)
    return HandoffInput(path=f"{folder.name}/delivery.json", sha256=_sha(files["delivery.json"]))


def _earlier_format(files: dict[str, bytes], page: bytes | None = None) -> dict[str, bytes]:
    """The bundle an earlier run published: the rendered report page is a listed file."""
    view = View.model_validate_json(files["view.json"])
    report = ReportView.model_validate_json(files["report-view.json"])
    receipt = json.loads(files["delivery.json"])
    html = render(view, report).encode() if page is None else page
    receipt["files"]["report.html"] = _sha(html)
    return {**files, "report.html": html, "delivery.json": (json.dumps(receipt) + "\n").encode()}


def test_a_bundle_without_a_report_page_is_bound_by_its_receipt(tmp_path: Path) -> None:
    folder = tmp_path / "now"
    folder.mkdir()
    spec = _written(folder, comparison_files(RUN, answer(ALL_DIMENSIONS), {}))
    view, files = _comparison_bundle(tmp_path, spec)
    assert view.run.run_id == RUN.run_id and "report.html" not in files
    (folder / "view.json").write_bytes((folder / "view.json").read_bytes() + b" ")
    with pytest.raises(ValueError, match="^cp8_bundle_changed: publication bytes"):
        _comparison_bundle(tmp_path, spec)


def test_an_earlier_bundle_with_a_report_page_is_still_accepted(tmp_path: Path) -> None:
    folder = tmp_path / "before"
    folder.mkdir()
    old = _earlier_format(comparison_files(RUN, answer(ALL_DIMENSIONS), {}))
    _, files = _comparison_bundle(tmp_path, _written(folder, old))
    assert files["report.html"] == old["report.html"]


def test_an_earlier_bundle_whose_report_page_differs_from_its_views_is_refused(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "before"
    folder.mkdir()
    old = _earlier_format(comparison_files(RUN, answer(ALL_DIMENSIONS), {}), page=b"<p>other</p>")
    with pytest.raises(ValueError, match="^cp8_bundle_binding: HTML differs"):
        _comparison_bundle(tmp_path, _written(folder, old))
