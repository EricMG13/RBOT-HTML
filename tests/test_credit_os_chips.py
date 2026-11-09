"""Citation chips: locators parsed from handoff text, resolved against a run's source text.
Expected locators and flags are written here from the fixture text, not read from the code."""

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest
from library_fixtures import CITED, SOURCE_NAME, SOURCE_PAGES, inventory_text, make_run, method

from deploy_workflow.credit_os_catalogue import catalogue
from deploy_workflow.credit_os_chips import (
    chips,
    chips_for_output,
    inventory,
    parse_locators,
)
from deploy_workflow.library_index import build_library

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library
from credit_os.store import workspace_store


def loc(kind, source=None, page=None, page_end=None, **rest):
    base = {"module": None, "codes": (), "label": None}
    return {"kind": kind, "source": source, "page": page, "page_end": page_end, **base, **rest}


def test_single_page():
    assert parse_locators("K, page:118 states the opinion") == [loc("issuer_page", "K", 118)]


def test_page_range():
    assert parse_locators("M, pages 31-32") == [loc("issuer_page", "M", 31, 32)]


def test_two_keyed_pages_and_a_bare_one_inherits_the_last_key():
    got = parse_locators("Cash K, page:120 and later page:123")
    assert got == [loc("issuer_page", "K", 120), loc("issuer_page", "K", 123)]


def test_keys_switch_between_sources():
    got = parse_locators("M, page:3, and J, pages 2-3")
    assert got == [loc("issuer_page", "M", 3), loc("issuer_page", "J", 2, 3)]


def test_bare_page_with_no_key_is_a_gap():
    (got,) = parse_locators("page:145 only")
    assert got["kind"] == "gap" and got["page"] == 145 and got["source"] is None
    assert got["label"] == "p.145 · no key"


def test_upstream_bracket():
    assert parse_locators("[CP-1: D4, F1]") == [loc("upstream", module="CP-1", codes=("D4", "F1"))]
    assert parse_locators("[CP-1A: E2]") == [loc("upstream", module="CP-1A", codes=("E2",))]
    assert parse_locators("[CP-1: D4; F3]")[0]["codes"] == ("D4", "F3")


def test_trailing_register_codes_belong_to_the_module_itself():
    got = parse_locators("Same basis; pre-dividend cash. D1, D3, E1.")
    assert got == [loc("upstream", codes=("D1", "D3", "E1"))]


def test_a_trailing_code_after_a_word_or_a_semicolon_is_found():
    assert parse_locators("Derived from calculation E1.") == [loc("upstream", codes=("E1",))]
    assert parse_locators("K, page:120; D2.") == [
        loc("issuer_page", "K", 120),
        loc("upstream", codes=("D2",)),
    ]
    assert parse_locators("K, page:120;D2.")[1] == loc("upstream", codes=("D2",))


def test_a_quarter_label_ending_a_sentence_is_not_a_register_code():
    assert parse_locators("Reported in Q4.") == []


def test_not_supplied_is_a_labelled_gap():
    assert parse_locators("Not supplied: x") == [loc("gap", label="Not supplied")]


def test_no_citation_gives_nothing():
    assert parse_locators("Plain prose with 3.29x cover.") == []


def test_inventory_reads_the_label_file_and_hash():
    sections = [
        {
            "heading": "Complete supplied inventory and provenance",
            "level": 3,
            "line": 1,
            "blocks": [
                {
                    "type": "table",
                    "line": 3,
                    "headers": ["Label", "Exact supplied source name", "Exact sha256", "Other"],
                    "rows": [{"line": 5, "cells": ["K", "k.jsonl", "ab" * 32, "x"]}],
                }
            ],
        }
    ]
    assert inventory(sections) == {"K": ("k.jsonl", "ab" * 32)}
    assert inventory([{**sections[0], "heading": "Other"}]) == {}


def built(tmp_path, with_cp0=True, text_bytes=SOURCE_PAGES):
    digest = hashlib.sha256(SOURCE_PAGES).hexdigest()
    run = make_run(
        tmp_path,
        "run-a",
        cp0_extra=inventory_text(digest) if with_cp0 else "",
        cp1_extra=CITED,
    )
    folder = run / "source-text"
    folder.mkdir()
    (folder / SOURCE_NAME).write_bytes(text_bytes)
    library = build_library(tmp_path, tmp_path / "library", method())
    store = workspace_store(tmp_path, catalogue(tmp_path, library))
    return run, store


@pytest.fixture(autouse=True)
def stand_in_method(monkeypatch):
    monkeypatch.setattr("deploy_workflow.library_index.current_method", lambda: method())


def line_of(run, store, start):
    (output_id,) = [i for i, o in store["outputs"].items() if o["module"] == "CP-1"]
    path = run.parent.parent / "runs" / output_id
    for number, text in enumerate(path.read_text().splitlines(), 1):
        if text.startswith(start):
            return f"{output_id}:{number}"
    raise AssertionError(start)


def test_quote_found_and_not(tmp_path):
    run, store = built(tmp_path)
    got = chips(tmp_path, store)
    (k, up) = got[line_of(run, store, "| Cash interest")]
    assert k["kind"] == "issuer_page" and k["source"] == "K" and k["page"] == 123
    assert k["file"] == SOURCE_NAME
    assert k["quote"] == "1,158" and k["quote_found"] is True
    assert k["hash_matches_inventory"] is True
    assert "1,158" in k["excerpt"] and len(k["excerpt"]) <= 600
    assert up["kind"] == "upstream" and up["codes"] == ["D1", "D3"]
    (wrong,) = got[line_of(run, store, "| Wrong interest")]
    assert wrong["quote"] == "1,159" and wrong["quote_found"] is False
    (said,) = got[line_of(run, store, "| Quoted interest")]
    assert said["quote"] == "Cash paid during the period" and said["quote_found"] is True


def test_upstream_gap_and_paragraph_rows(tmp_path):
    run, store = built(tmp_path)
    got = chips(tmp_path, store)
    (up,) = got[line_of(run, store, "| Upstream")]
    assert (up["kind"], up["module"], up["codes"]) == ("upstream", "CP-1", ["D4", "F1"])
    (gap,) = got[line_of(run, store, "| Absent")]
    assert gap["kind"] == "gap" and gap["label"] == "Not supplied"
    (para,) = got[line_of(run, store, "A paragraph")]
    assert para["page"] == 124 and para["quote"] is None and para["quote_found"] is None
    assert para["excerpt"] == "Interest paid was lower."


def test_one_changed_byte_breaks_the_hash_match(tmp_path):
    run, store = built(tmp_path, text_bytes=SOURCE_PAGES + b" ")
    (k, _) = chips(tmp_path, store)[line_of(run, store, "| Cash interest")]
    assert k["hash_matches_inventory"] is False
    assert k["quote_found"] is True


def test_no_cp0_makes_every_issuer_page_a_gap(tmp_path):
    run, store = built(tmp_path, with_cp0=False)
    (k, _) = chips(tmp_path, store)[line_of(run, store, "| Cash interest")]
    assert k["kind"] == "gap" and k["reason"] == "no inventory" and k["quote_found"] is None


def test_a_missing_source_file_is_reported_on_the_chip(tmp_path):
    run, store = built(tmp_path)
    (run / "source-text" / SOURCE_NAME).unlink()
    (k, _) = chips(tmp_path, store)[line_of(run, store, "| Cash interest")]
    assert k["reason"] == "source text file not found"
    assert k["hash_matches_inventory"] is None and k["quote_found"] is None


def test_update_library_writes_chips_into_data_js(tmp_path):
    run, store = built(tmp_path)
    update_library.update_library(tmp_path)
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    key = line_of(run, store, "| Cash interest")
    assert data["chips"][key][0]["quote_found"] is True


# --- Fix round 1: rulings R1-R7 ---------------------------------------------------------------

PAGES_TWO = (
    b'{"page": 10, "text": "alpha is here. Receivables (165) and total 1,158."}\n'
    b'{"page": 20, "text": "beta only."}\n'
)


def one_run(tmp_path, pages=PAGES_TWO, name="K.jsonl", file="K.jsonl", digest=None):
    """A run folder with one source-text file and the inventory naming it; returns both."""
    run = tmp_path / "run"
    (run / "source-text").mkdir(parents=True)
    (run / "source-text" / name).write_bytes(pages)
    return run, {"K": (file, digest or hashlib.sha256(pages).hexdigest())}


def table(*rows):
    return [
        {
            "heading": "H",
            "level": 3,
            "line": 1,
            "blocks": [
                {
                    "type": "table",
                    "line": 2,
                    "headers": ["Item", "Value", "Basis"],
                    "rows": [{"line": 4 + i, "cells": list(r)} for i, r in enumerate(rows)],
                }
            ],
        }
    ]


def run_chips(run, inv, *rows):
    return chips_for_output(run, "x/CP-1.md", "CP-1", table(*rows), inv)


def test_each_quote_binds_to_the_page_cited_before_it(tmp_path):
    run, inv = one_run(tmp_path)
    inv["M"] = inv["K"]
    got = run_chips(run, inv, ("a", "-", "K, page:10 says “alpha” and M, page:20 differs"))
    first, second = got["x/CP-1.md:4"]
    assert (first["page"], first["quote"], first["quote_found"]) == (10, "alpha", True)
    assert (second["page"], second["quote"], second["quote_found"]) == (20, None, None)


def test_a_numeric_cell_binds_to_every_page_of_the_row(tmp_path):
    run, inv = one_run(tmp_path)
    got = run_chips(run, inv, ("a", "1158", "K, page:10 and K, page:20"))
    first, second = got["x/CP-1.md:4"]
    assert (first["quote"], first["quote_found"]) == ("1158", True)
    assert (second["quote"], second["quote_found"]) == ("1158", False)


def test_an_accounting_negative_matches_its_bracketed_page_form(tmp_path):
    run, inv = one_run(tmp_path)
    (found,) = run_chips(run, inv, ("a", "-165", "K, page:10"))["x/CP-1.md:4"]
    assert found["quote_found"] is True
    (other,) = run_chips(run, inv, ("a", "-166", "K, page:10"))["x/CP-1.md:4"]
    assert other["quote_found"] is False


def test_unseparated_number_matches_the_separated_page_text(tmp_path):
    run, inv = one_run(tmp_path)
    (found,) = run_chips(run, inv, ("a", "1158", "K, page:10"))["x/CP-1.md:4"]
    assert found["quote_found"] is True
    (other,) = run_chips(run, inv, ("a", "158", "K, page:10"))["x/CP-1.md:4"]
    assert other["quote_found"] is False


def test_a_missing_source_file_has_no_hash_verdict(tmp_path):
    run, inv = one_run(tmp_path, file="P.jsonl")
    (got,) = run_chips(run, inv, ("a", "1", "K, page:10"))["x/CP-1.md:4"]
    assert got["hash_matches_inventory"] is None
    assert got["reason"] == "source text file not found"


def test_inventory_names_that_leave_source_text_are_refused(tmp_path):
    run, inv = one_run(tmp_path)
    (run / "secret.jsonl").write_bytes(PAGES_TWO)
    inv["K"] = ("../secret.jsonl", inv["K"][1])
    (got,) = run_chips(run, inv, ("a", "1", "K, page:10"))["x/CP-1.md:4"]
    assert got["kind"] == "gap" and got["reason"] == "source name not a file name"
    assert got["excerpt"] is None


def test_an_unreadable_source_file_becomes_the_chip_reason(tmp_path):
    run, inv = one_run(tmp_path)
    path = run / "source-text" / "K.jsonl"
    path.chmod(0)
    try:
        if os.access(path, os.R_OK):
            pytest.skip("permissions are not enforced for this user")
        (got,) = run_chips(run, inv, ("a", "1", "K, page:10"))["x/CP-1.md:4"]
    finally:
        path.chmod(0o644)
    assert got["reason"].startswith("source text unreadable")
    assert got["hash_matches_inventory"] is None


def inventory_section(heading, headers):
    return [
        {
            "heading": heading,
            "level": 3,
            "line": 1,
            "blocks": [
                {
                    "type": "table",
                    "line": 3,
                    "headers": headers,
                    "rows": [{"line": 5, "cells": ["K", "k.jsonl", "cd" * 32] + ["x"] * 0}],
                }
            ],
        }
    ]


def test_inventory_heading_variants():
    variant = inventory_section(
        "Supplied inventory and frozen source roster",
        ["Alias", "Exact source name / source ID", "Exact sha256"],
    )
    assert inventory(variant) == {"K": ("k.jsonl", "cd" * 32)}
    no_hash = inventory_section("Inventory", ["Alias", "Name", "Note"])
    assert inventory(no_hash) == {}


def claim_sections(heading_level_two, table_heading, headers):
    row = {"line": 6, "cells": ["No locator here", "x", "y"]}
    block = {"type": "table", "line": 4, "headers": headers, "rows": [row]}
    return [
        {"heading": heading_level_two, "level": 2, "line": 1, "blocks": []},
        {"heading": table_heading, "level": 3, "line": 3, "blocks": [block]},
    ]


def test_claim_rows_without_a_locator_get_a_no_page_gap(tmp_path):
    h = ["Finding", "Creditor impact", "Confidence"]
    for sections in (
        claim_sections("Findings", "Reader summary", ["Item", "B", "C"]),
        claim_sections("Other", "Reader summary", h),
        claim_sections("Other", "Chart data: leverage", ["Period", "B", "C"]),
        claim_sections("Other", "Reader", ["Bottom line", "B", "C"]),
    ):
        got = chips_for_output(tmp_path, "x/CP-1.md", "CP-1", sections, {})
        (gap,) = got["x/CP-1.md:6"]
        assert gap["kind"] == "gap" and gap["label"] == "no page" and gap["reason"]
    register = claim_sections("Sources", "Register", ["Item", "B", "C"])
    assert chips_for_output(tmp_path, "x/CP-1.md", "CP-1", register, {}) == {}


def test_gap_labels_are_short_and_carry_a_reason(tmp_path):
    run, _ = one_run(tmp_path)
    got = run_chips(
        run,
        {},
        ("a", "1", "K, page:10"),
        ("b", "1", "Not supplied"),
        ("c", "1", "page:3"),
    )
    (unresolved,) = got["x/CP-1.md:4"]
    assert (unresolved["label"], unresolved["reason"]) == ("K p.10 · unresolved", "no inventory")
    assert got["x/CP-1.md:5"][0]["label"] == "Not supplied" and got["x/CP-1.md:5"][0]["reason"]
    assert got["x/CP-1.md:6"][0]["label"] == "p.3 · no key" and got["x/CP-1.md:6"][0]["reason"]


@pytest.mark.parametrize(
    "text",
    [
        "Q4",
        "B3",
        "Corporate family rating. B2.",
        "See the webpage 3 times",
        "https://example.com/report?page:12",
        "homepage:7",
        "K, page 1.5",
        "D1.",
    ],
)
def test_no_false_locators(text):
    assert parse_locators(text) == []


def test_a_bare_page_does_not_inherit_a_key_from_an_earlier_sentence():
    got = parse_locators("K, page:118. Proxy page:7 says so.")
    assert got[0] == loc("issuer_page", "K", 118)
    assert got[1]["kind"] == "gap" and got[1]["page"] == 7


# --- Fix round 2: R6 (stat errors), R8, R9 -----------------------------------------------------


def test_an_overlong_inventory_name_becomes_the_chip_reason(tmp_path):
    run, inv = one_run(tmp_path)
    inv["K"] = ("x" * 300 + ".jsonl", inv["K"][1])
    (got,) = run_chips(run, inv, ("a", "1", "K, page:10"))["x/CP-1.md:4"]
    assert got["reason"] and got["hash_matches_inventory"] is None


def test_an_unsearchable_source_text_folder_becomes_the_chip_reason(tmp_path):
    run, inv = one_run(tmp_path)
    folder = run / "source-text"
    folder.chmod(0o600)
    try:
        if os.access(folder / "K.jsonl", os.R_OK):
            pytest.skip("permissions are not enforced for this user")
        (got,) = run_chips(run, inv, ("a", "1", "K, page:10"))["x/CP-1.md:4"]
    finally:
        folder.chmod(0o700)
    assert got["reason"]


def test_a_bare_page_inherits_the_key_named_by_the_rows_first_cell(tmp_path):
    run, inv = one_run(tmp_path)
    got = run_chips(run, inv, ("K", "pages 10, pages 20", "n/a"), ("Z", "page 10", "n/a"))
    first, second = got["x/CP-1.md:4"]
    assert (first["kind"], first["source"], first["page"]) == ("issuer_page", "K", 10)
    assert (second["kind"], second["source"], second["page"]) == ("issuer_page", "K", 20)
    (stray,) = got["x/CP-1.md:5"]
    assert stray["kind"] == "gap" and stray["label"] == "p.10 · no key"


def thousands_pages():
    return (
        b'{"page": 1, "text": "odd 1,6,5 and 16,5 here"}\n'
        b'{"page": 2, "text": "loss -165 and (165) here"}\n'
        b'{"page": 3, "text": "gain 165 here"}\n'
    )


def test_thousands_commas_only_in_three_digit_groups(tmp_path):
    run, inv = one_run(tmp_path, pages=thousands_pages())
    (got,) = run_chips(run, inv, ("a", "165", "K, page:1"))["x/CP-1.md:4"]
    assert got["quote_found"] is False


def test_a_positive_number_does_not_match_a_negative_or_bracketed_value(tmp_path):
    run, inv = one_run(tmp_path, pages=thousands_pages())
    (got,) = run_chips(run, inv, ("a", "165", "K, page:2"))["x/CP-1.md:4"]
    assert got["quote_found"] is False
    (plain,) = run_chips(run, inv, ("a", "165", "K, page:3"))["x/CP-1.md:4"]
    assert plain["quote_found"] is True


def test_a_period_column_never_becomes_the_quote(tmp_path):
    run, inv = one_run(tmp_path)
    sections = table(("2024", "1158", "K, page:10"))
    sections[0]["blocks"][0]["headers"] = ["Fiscal year", "Cash interest", "Basis"]
    got = chips_for_output(run, "x/CP-1.md", "CP-1", sections, inv)
    (found,) = got["x/CP-1.md:4"]
    assert found["quote"] == "1158" and found["quote_found"] is True


def test_a_header_only_containing_period_letters_is_not_a_period_column(tmp_path):
    run, inv = one_run(tmp_path)
    for header, expected in (("Update", "1158"), ("Candidates", "1158"), ("Fiscal year", None)):
        sections = table(("1158", "x", "K, page:10"))
        sections[0]["blocks"][0]["headers"] = [header, "Cash interest", "Basis"]
        got = chips_for_output(run, "x/CP-1.md", "CP-1", sections, inv)
        (found,) = got["x/CP-1.md:4"]
        assert found["quote"] == expected, header


RANGE_PAGES = (
    b'{"page": 1, "text": "fiscal 2023-2024 results"}\n{"page": 2, "text": "loss -2024 only"}\n'
)


def test_a_positive_number_is_found_inside_a_range_but_not_as_a_negative(tmp_path):
    run, inv = one_run(tmp_path, pages=RANGE_PAGES)
    (in_range,) = run_chips(run, inv, ("a", "2024", "K, page:1"))["x/CP-1.md:4"]
    assert in_range["quote_found"] is True
    (negative,) = run_chips(run, inv, ("a", "2024", "K, page:2"))["x/CP-1.md:4"]
    assert negative["quote_found"] is False
