"""Filing: safe folder names, one folder per issuer ID, reports filed without overwrite."""

from __future__ import annotations

import os
import tempfile
import unicodedata
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


def test_a_new_id_whose_folder_name_is_taken_by_another_id_gets_a_number(layout):
    # Two different IDs that clean to the same wanted name.
    first, _ = issuer_folder(layout, "a/b", "n")
    second, differs = issuer_folder(layout, "a b", "n")
    assert first.name == "n (a b)" and second.name == "n (a b) 2" and differs is False


def test_name_differs_ignores_the_numeric_suffix(layout):
    issuer_folder(layout, "a/b", "n")
    second, _ = issuer_folder(layout, "a b", "n")
    again, differs = issuer_folder(layout, "a b", "n")
    assert again == second and second.name.endswith(" 2") and differs is False
    _, renamed = issuer_folder(layout, "a b", "other")
    assert renamed is True


def test_names_that_differ_only_in_unicode_form_or_case_get_separate_folders(layout):
    composed, _ = issuer_folder(layout, "caf\u00e9", "n")
    decomposed, _ = issuer_folder(layout, unicodedata.normalize("NFD", "caf\u00e9"), "n")
    upper, _ = issuer_folder(layout, "CAF\u00c9", "n")
    keys = {unicodedata.normalize("NFC", f.name).casefold() for f in (composed, decomposed, upper)}
    assert len(keys) == 3


def test_a_failed_write_leaves_no_partial_report_and_raises(layout, tmp_path, monkeypatch):
    report = tmp_path / "r.html"
    report.write_bytes(b"data")
    real_open = Path.open

    def failing_open(self, mode="r", *args, **kwargs):
        handle = real_open(self, mode, *args, **kwargs)
        if mode == "xb":

            def boom(_data):
                raise OSError("disk full")

            handle.write = boom
        return handle

    monkeypatch.setattr(Path, "open", failing_open)
    kw = {"issuer_id": "x", "issuer_name": "X", "as_of": "d", "pathway": "p"}
    with pytest.raises(OSError, match="disk full"):
        file_report(layout, report, **kw)
    monkeypatch.undo()
    assert list((layout.issuers / "X (x)").iterdir()) == []


def test_safe_name_drops_c1_controls():
    assert safe_name("a\x81b\x9fc") == "a b c"


@pytest.mark.parametrize(
    "cases",
    [
        [
            ("../../x", ".."),
            ("..", "/etc"),
            ("a", "." * 300),
            ("\x00", "\x1f"),
            ("a/b", "n"),
            ("a b", "n"),
        ]
    ],
)
def test_hostile_names_and_ids_stay_under_issuers_in_separate_folders(layout, tmp_path, cases):
    report = tmp_path / "r.html"
    report.write_bytes(b"x")
    root = layout.issuers.resolve()
    owner: dict[Path, str] = {}
    for issuer_id, name in cases:
        folder, _ = issuer_folder(layout, issuer_id, name)
        filed = file_report(
            layout, report, issuer_id=issuer_id, issuer_name=name, as_of="../..", pathway="/etc/x"
        )
        assert root in filed.resolve().parents
        assert owner.setdefault(folder.resolve(), issuer_id) == issuer_id
    assert len(owner) == len(cases)


def test_m3_the_registry_save_waits_out_a_refused_replace(layout, monkeypatch):
    real, refusals = os.replace, [2]

    def refuse_twice(source, target):
        if refusals[0]:
            refusals[0] -= 1
            raise PermissionError(13, "in use", str(target))
        real(source, target)

    monkeypatch.setattr(os, "replace", refuse_twice)
    folder, _ = issuer_folder(layout, "acme", "Acme")
    assert refusals == [0] and folder.name == "Acme (acme)"


def test_l2_a_report_already_filed_with_the_same_bytes_is_reused(layout, tmp_path):
    report = tmp_path / "report.html"
    report.write_bytes(b"one")
    kw = {
        "issuer_id": "acme",
        "issuer_name": "Acme",
        "as_of": "2026-11-09",
        "pathway": "earnings_update",
    }
    first = file_report(layout, report, **kw)
    again = file_report(layout, report, **kw)  # after a stop before the record was saved
    assert again == first
    assert sorted(p.name for p in first.parent.iterdir()) == ["2026-11-09 earnings_update.html"]
    other = file_report(layout, report, claimed=frozenset({first}), **kw)  # another run's file
    assert other.name == "2026-11-09 earnings_update-2.html"
    assert file_report(layout, report, claimed=frozenset({first}), **kw) == other


def test_l5_a_long_issuer_name_is_cut_and_the_issuer_id_stays_whole(layout):
    folder, _ = issuer_folder(layout, "x" * 40, "L" * 200)
    assert folder.name == "L" * (80 - len(" (" + "x" * 40 + ")")) + f" ({'x' * 40})"
    assert len(folder.name) == 80
