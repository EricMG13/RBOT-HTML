"""The shared folder's layout: the folders made, the root-length and network-path refusals."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from deploy_workflow.inbox.layout import Layout, ensure_layout


@pytest.fixture
def layout() -> Iterator[Layout]:
    # pytest's tmp_path is longer than the 80-character root limit on macOS.
    with tempfile.TemporaryDirectory(prefix="ib", dir="/tmp") as short:
        yield ensure_layout(Path(short))


def test_layout_creates_every_folder(layout):
    for folder in (layout.issuers, layout.runs, layout.drops, layout.state, layout.logs):
        assert folder.is_dir()
    assert layout.uploads.is_dir()
    assert layout.engine == layout.root / "_engine"
    assert not (layout.root / "inbox").exists()


def test_layout_refuses_a_long_root(tmp_path):
    with pytest.raises(ValueError):
        ensure_layout(tmp_path / ("x" * 90))


def test_a_root_on_a_network_path_is_refused_in_words_that_name_this_machine(tmp_path):
    for text in ("\\\\server\\share\\root", "//server/share/root"):
        with pytest.raises(ValueError, match="own disk") as refused:
            ensure_layout(Path(text))
        assert "this machine" in str(refused.value) and "watcher machine" not in str(refused.value)


def test_a_root_that_holds_an_old_inbox_leaves_it_alone(layout):
    old = layout.root / "inbox/credit_snapshot/acme"
    old.mkdir(parents=True)
    (old / "a.pdf").write_bytes(b"%PDF")
    again = ensure_layout(layout.root)
    assert again == layout
    assert sorted(p.name for p in (layout.root / "inbox").rglob("*")) == [
        "a.pdf",
        "acme",
        "credit_snapshot",
    ]
