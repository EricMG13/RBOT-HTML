"""Filing: safe folder names, one folder per issuer ID, reports filed without overwrite."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from deploy_workflow.inbox.drops import Layout, ensure_layout
from deploy_workflow.inbox.filing import file_report, issuer_folder, safe_name


@pytest.fixture
def layout() -> Iterator[Layout]:
    # pytest's tmp_path is longer than the 80-character root limit on macOS.
    with tempfile.TemporaryDirectory(prefix="ib", dir="/tmp") as short:
        yield ensure_layout(Path(short))


@pytest.mark.parametrize(
    ("raw", "safe"),
    [
        ("Acme Corp.", "Acme Corp"),
        ('A/B:C*?"<>|D', "A B C D"),
        ("CON", "_CON"),
        ("nul.txt", "_nul.txt"),
        ("  ", "_"),
        ("x" * 200, "x" * 80),
        ("../../etc", ".. .. etc"),
    ],
)
def test_safe_name(raw, safe):
    assert safe_name(raw) == safe


def test_one_folder_per_issuer_id(layout):
    first, differs = issuer_folder(layout, "acme", "ACME Corp")
    again, differs_again = issuer_folder(layout, "acme", "Acme Corp.")
    other, _ = issuer_folder(layout, "acme-2", "ACME Corp")
    assert first.name == "ACME Corp (acme)" and differs is False
    assert again == first and differs_again is True
    assert other.name == "ACME Corp (acme-2)" and other != first


def test_repeat_report_gets_a_suffix_and_nothing_is_overwritten(layout, tmp_path):
    report = tmp_path / "report.html"
    report.write_bytes(b"one")
    kw = {
        "issuer_id": "acme",
        "issuer_name": "Acme",
        "as_of": "2026-11-09",
        "pathway": "earnings_update",
    }
    first = file_report(layout, report, **kw)
    report.write_bytes(b"two")
    second = file_report(layout, report, **kw)
    assert first.name == "2026-11-09 earnings_update.html" and first.read_bytes() == b"one"
    assert second.name == "2026-11-09 earnings_update-2.html" and second.read_bytes() == b"two"
