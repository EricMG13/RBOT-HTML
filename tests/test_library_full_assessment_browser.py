"""CP-3C and CP-6's portfolio debate (CP-6A) in the library, in a real browser (headless Chrome).

Owner, 2026-11-15: CP-3C and CP-6A are part of the full credit assessment. The run is the synthetic
fixture built with `--with-cp3c-cp6` (hand-made handoffs; no model was called), so this checks the
pages against the handoffs they are drawn from, not any analysis. The answer key is read from the
fixture's own Markdown here, never from the library's code.
"""

import html
import re
import subprocess
import sys
from pathlib import Path

import pytest
from test_library_page_browser import visit

pytestmark = pytest.mark.browser

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "apps/issuer-library/fixtures"
RUN = "?c=synthetic-nbg-new-format-001"


def section(module: str, heading: str) -> list[str]:
    """The lines of one `###` section of a fixture handoff, up to the next heading."""
    lines = (FIXTURES / f"synthetic-new-format/SYNTHETIC-{module}.md").read_text().splitlines()
    start = lines.index(f"### {heading}") + 1
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("#"))
    return [line for line in lines[start:end] if line.strip()]


def cells(module: str, heading: str) -> list[str]:
    """The body cells of the section's table (header and separator rows dropped)."""
    rows = [line for line in section(module, heading) if line.startswith("|")][2:]
    return [c.strip() for row in rows for c in row.strip("|").split("|")]


@pytest.fixture(scope="module")
def library(tmp_path_factory) -> Path:
    workspace = tmp_path_factory.mktemp("full")
    for script, extra in (
        ("fixtures/build_synthetic_run.py", ["--with-cp3c-cp6"]),
        ("update_library.py", []),
    ):
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "apps/issuer-library" / script),
                "--workspace",
                str(workspace),
                *extra,
            ],
            check=True,
            capture_output=True,
        )
    return workspace / "library/index.html"


def shown(page: Path, route: str) -> str:
    dom, console = visit(page, route)
    assert console == []
    dom = re.sub(r"<script.*?</script>", "", dom, flags=re.DOTALL)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", dom)).split())


def test_cp6_page_draws_the_portfolio_posture_and_the_cp6a_tables_without_ids(library):
    text = shown(library, f"#CP-6{RUN}")
    posture = section("CP-6", "Portfolio posture")
    assert posture[0].startswith("Final Sizing Posture: Requires More Work.")
    for line in posture:
        if not line.startswith("Basis: "):
            assert line in text, line
    for heading, title in (
        ("T6E.4 — Compliance cross-examination", "Compliance cross-examination"),
        ("T6E.6 — CIO evidence weighting", "CIO evidence weighting"),
        ("T6E.7 — Allocation decision matrix", "Allocation decision matrix"),
    ):
        assert title in text, title
        for cell in cells("CP-6", heading):
            if not cell.endswith(".pdf"):  # a Source column is drawn only on Evidence
                assert cell in text, (heading, cell)
    # Audit material is drawn only on Evidence and in the trace drawer.
    for audit in ("T6E.4", "T6E.6", "T6E.7", "T6E.11", "CP-6A-GAP-001", ".pdf", "sha256"):
        assert audit not in text, audit


def test_the_portfolio_debate_gaps_ledger_is_on_evidence(library):
    text = shown(library, f"#W-Evidence/registers{RUN}&m=CP-6")
    for cell in cells("CP-6", "T6E.11 — Gaps ledger (portfolio debate)"):
        assert cell in text, cell


def test_cp3c_page_and_overview_draw_its_passages(library):
    page = shown(library, f"#CP-3C{RUN}")
    overview = shown(library, f"#W-Overview{RUN}")
    bottom = section("CP-3C", "Bottom line")[0]
    assert bottom in page and bottom in overview
    for line in section("CP-3C", "Key findings"):
        if not line.startswith("Basis: "):
            assert line.removeprefix("- ") in page, line
    assert section("CP-6", "Key findings")[2].removeprefix("- ") in overview
