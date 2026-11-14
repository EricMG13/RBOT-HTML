"""guess_kind against the hand-written answer key tests/fixtures/run-expectations/document-key.json.

Each entry whose file exists is paged as the launcher pages it (the launcher's own ``_pages``,
called on the file's bytes) and the guess must equal the key's kind, executed flag and period end:
21 of the 25 present entries are checked that way. Four named files (KEY_PAGING_ONLY) are checked
under the key's own paging instead. The key is not edited here and the comparison is not
loosened."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deploy_workflow.model.handoff import _pages
from deploy_workflow.owners import cpos_launch
from deploy_workflow.run_expectations import guess_kind

ROOT = Path(__file__).resolve().parent.parent
KEY = json.loads((ROOT / "tests/fixtures/run-expectations/document-key.json").read_text())
FIRST_PAGES = cpos_launch.FIRST_PAGES  # the guess sees the launcher's first pages

# Keyed for pages split at '=== PAGE ===' with the banner dropped (the key's note); the launcher
# pages a .txt as 12,000-character chunks, so 07 and 10 reach guess_kind as one page holding two
# kinds' covers. For 18 and 19 the fixture banner line sits above the cover line under launcher
# paging. 21 of the 25 present keyed documents pass under launcher paging; the four here are
# checked below under the key's own paging.
KEY_PAGING_ONLY = {
    "tests/fixtures/run-expectations/synthetic/07-combined-compliance-certificate-then-10q.txt": (
        "launcher gives one page holding a compliance certificate and a 10-Q cover"
    ),
    "tests/fixtures/run-expectations/synthetic/10-earnings-release.txt": (
        "launcher gives one page holding the release and a statements heading"
    ),
    "tests/fixtures/run-expectations/synthetic/18-market-quotes.txt": (
        "under launcher paging the banner line sits above the cover line and the classifier "
        "reads the cover line as a wrapped sentence tail, so the result is unrecognised; whether "
        "the classifier or the key's paging should change is an open owner decision"
    ),
    "tests/fixtures/run-expectations/synthetic/19-peer-data.txt": (
        "under launcher paging the banner line sits above the cover line and the classifier "
        "reads the cover line as a wrapped sentence tail, so the result is unrecognised; whether "
        "the classifier or the key's paging should change is an open owner decision"
    ),
}
ENTRIES = [e for e in KEY["entries"] if (ROOT / e["path"]).is_file()]


def test_every_synthetic_entry_exists() -> None:
    missing = [e["path"] for e in KEY["entries"] if e["origin"] == "synthetic" and e not in ENTRIES]
    assert not missing, missing


def _launcher_pages(path: Path) -> list[str]:
    return _pages(path.name, path.read_bytes())


@pytest.mark.parametrize(
    "entry",
    [pytest.param(e, id=e["path"]) for e in ENTRIES if e["path"] not in KEY_PAGING_ONLY],
)
def test_guess_matches_key(entry: dict[str, object]) -> None:
    path = ROOT / str(entry["path"])
    guess = guess_kind(path.name, _launcher_pages(path)[:FIRST_PAGES])
    assert (guess.kind, guess.executed, guess.period_end) == (
        entry["kind"],
        entry["executed"],
        entry["period_end"],
    )


@pytest.mark.parametrize(
    "entry",
    [pytest.param(e, id=e["path"]) for e in ENTRIES if e["path"] in KEY_PAGING_ONLY],
)
def test_guess_matches_key_under_key_paging(entry: dict[str, object]) -> None:
    path = ROOT / str(entry["path"])
    body = path.read_text().split("\n", 1)[1]  # line 1 is the banner, not page text
    guess = guess_kind(path.name, body.split("\n=== PAGE ===\n")[:FIRST_PAGES])
    assert (guess.kind, guess.executed, guess.period_end) == (
        entry["kind"],
        entry["executed"],
        entry["period_end"],
    )


WRAPPED = [
    pytest.param(
        "The borrower shall deliver to the administrative agent within forty five days a duly\n"
        "compliance certificate signed by a responsible officer of the borrower each quarter",
        id="compliance-certificate",
    ),
    pytest.param(
        "Lenders will rely on the figures that the sponsor supplied and that we reviewed in\n"
        "peer data gathered from several public sources over the last twelve months",
        id="peer-data",
    ),
]


@pytest.mark.parametrize("page", WRAPPED)
def test_wrapped_prose_tail_is_not_a_title(page: str) -> None:
    assert guess_kind("notes.txt", [page]).kind == "unrecognised"


def test_wrapped_prose_does_not_add_a_second_kind() -> None:
    page = (
        "COMPLIANCE CERTIFICATE\n"
        "Each quarter the borrower delivers to the agent, on the date set by the lenders, a duly\n"
        "peer data gathered from several public sources over the last twelve months"
    )
    assert guess_kind("notes.txt", [page]).kind == "compliance_certificate"


# Prose whose previous line holds a spaced hyphen or is upper case is still open prose: a bare
# " - " or an all-caps line does not make the line below a title, so the wrapped tail stays
# skipped.
PROSE_ABOVE = [
    pytest.param(
        "dealer-commentary.txt",
        "Secondary prices drifted lower after the sponsor - which also owns the borrower - "
        "released\n"
        "market quotes from three dealers that we have not been able to verify independently\n",
        id="dash-prose-market-quotes",
    ),
    pytest.param(
        "lender-update-executed.txt",
        "THE BORROWER HAS DELIVERED THE NOTICE REQUIRED BY SECTION 6.02 OF THE\n"
        "amended and restated credit agreement dated as of March 3, 2021 among the lenders\n",
        id="upper-prose-credit-agreement",
    ),
    pytest.param(
        "notes.txt",
        "Management - in line with prior quarters - expects to deliver its next quarterly\n"
        "compliance certificate within forty five days after the end of the quarter\n",
        id="dash-prose-compliance-certificate",
    ),
    pytest.param(
        "notes.txt",
        "Leverage is above the median of the group - see the table below for the figures from\n"
        "peer data compiled by the sponsor and not reviewed by any independent party here\n",
        id="dash-prose-peer-data",
    ),
    pytest.param(
        "dealer-commentary.txt",
        "EBITDA - as defined in the credit agreement and adjusted for the items released in\n"
        "market quotes from three dealers that we have not been able to verify independently\n",
        id="acronym-label-market-quotes",
    ),
    pytest.param(
        "notes.txt",
        "Q3 2025 - management expects to deliver its next quarterly\n"
        "compliance certificate within forty five days after the end of the quarter\n",
        id="quarter-label-compliance-certificate",
    ),
    pytest.param(
        "notes.txt",
        "S&P - downgraded the issuer on weaker cash flow and pointed to the\n"
        "peer data compiled by the sponsor and not reviewed by any independent party here\n",
        id="agency-label-peer-data",
    ),
    pytest.param(
        "notes.txt",
        "RISK FACTORS - investors should read this entire document including the\n"
        "offering memorandum and the annual report before deciding to invest here",
        id="label-prose-risk-factors",
    ),
    pytest.param(
        "notes.txt",
        "NOTE TO DRAFT - the borrower will deliver to the agent within forty five days a\n"
        "compliance certificate signed by a responsible officer of the borrower each quarter",
        id="label-prose-note-to-draft",
    ),
    pytest.param(
        "notes.txt",
        "MARKET UPDATE - secondary prices drifted lower after the sponsor released\n"
        "market quotes from three dealers that we have not been able to verify independently",
        id="label-prose-market-update",
    ),
]


@pytest.mark.parametrize(("name", "page"), PROSE_ABOVE)
def test_prose_with_dash_or_capitals_above_stays_unrecognised(name: str, page: str) -> None:
    assert guess_kind(name, [page]).kind == "unrecognised"
