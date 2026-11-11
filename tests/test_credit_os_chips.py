"""Citation chips: locators parsed from handoff text, resolved against a run's source text.
Expected locators and flags are written here from the fixture text, not read from the code."""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import pytest
from library_fixtures import (
    ALIAS_CITED,
    ALIAS_FILING_NAME,
    ALIAS_FILING_PAGES,
    ALIAS_PDF_NAME,
    ALIAS_PDF_PAGES,
    CITED,
    SOURCE_NAME,
    SOURCE_PAGES,
    alias_inventory_text,
    inventory_text,
    make_run,
    method,
)

from deploy_workflow.credit_os_catalogue import catalogue
from deploy_workflow.credit_os_chips import (
    chips,
    chips_for_output,
    inventory,
    inventory_alternates,
    is_file_name,
    parse_locators,
    read_pages,
)
from deploy_workflow.library_index import build_library

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/issuer-library"))
import update_library
from credit_os.store import workspace_store

KEYS = ("K", "M", "J", "PDF", "Settings")


def loc(kind, source=None, page=None, page_end=None, **rest):
    base = {"module": None, "codes": (), "label": None, "note": None}
    return {"kind": kind, "source": source, "page": page, "page_end": page_end, **base, **rest}


def test_single_page():
    assert parse_locators("K, page:118 states the opinion", KEYS) == [loc("issuer_page", "K", 118)]


def test_page_range():
    assert parse_locators("M, pages 31-32", KEYS) == [loc("issuer_page", "M", 31, 32)]


def test_two_keyed_pages_and_a_bare_one_inherits_the_last_key():
    got = parse_locators("Cash K, page:120 and later page:123", KEYS)
    assert got == [loc("issuer_page", "K", 120), loc("issuer_page", "K", 123)]


def test_keys_switch_between_sources():
    got = parse_locators("M, page:3, and J, pages 2-3", KEYS)
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
    assert parse_locators("K, page:120; D2.", KEYS) == [
        loc("issuer_page", "K", 120),
        loc("upstream", codes=("D2",)),
    ]
    assert parse_locators("K, page:120;D2.", KEYS)[1] == loc("upstream", codes=("D2",))


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
    # R24: with no inventory no key is read, so the page is unkeyed (was "K p.10 · unresolved").
    assert (unresolved["label"], unresolved["reason"]) == ("p.10 · no key", "no inventory")
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
    got = parse_locators("K, page:118. Proxy page:7 says so.", KEYS)
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


# --- Final fix round: R24 (inventory keys), R23 (aliases, page forms), R25 (match) ------------

ALIASES = ("March filing", "June filing", "Annual filing", "Annual PDF", "Settings")
ALTERNATE_PDF = ("Annual PDF",)
NOTE_ANNUAL = "alias 'Annual' → 'Annual filing' (Annual PDF marked alternate in CP-0)"


def aliased(text):
    return parse_locators(text, ALIASES, ALTERNATE_PDF)


def pages_of(got):
    return [(g["source"], g["page"], g["page_end"]) for g in got]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("K, page:121 and PDF, page:106 each contain it", [("K", 121, None), ("PDF", 106, None)]),
        (
            "Settings, page:1 has a blank cutoff; K, page:120",
            [("Settings", 1, None), ("K", 120, None)],
        ),
        ("K p.5", [("K", 5, None)]),
        ("PDF pages 7–9", [("PDF", 7, 9)]),
    ],
)
def test_keys_are_the_inventorys_not_one_capital_letter(text, expected):
    assert pages_of(parse_locators(text, ("K", "PDF", "Settings"))) == expected


def test_a_key_the_inventory_lacks_leaves_a_gap_and_inherits_nothing():
    got = parse_locators("K, page:1 and X, page:2", ("K", "M"))
    assert got[0] == loc("issuer_page", "K", 1)
    assert got[1]["kind"] == "gap" and got[1]["label"] == "p.2 · no key" and got[1]["page"] == 2
    (alone,) = parse_locators("Settings, page:9", ("K",))
    assert alone["kind"] == "gap" and alone["source"] is None and alone["page"] == 9


def test_the_longest_key_wins_and_keys_are_matched_exactly():
    got = parse_locators("PDF, page:3 and PDFX, page:4", ("P", "PDF"))
    assert pages_of(got[:1]) == [("PDF", 3, None)]
    assert got[1]["kind"] == "gap"
    assert parse_locators("K, page:5", ("k",))[0]["kind"] == "gap"
    assert parse_locators("a.b, page:5", ("a.b",))[0]["source"] == "a.b"
    assert parse_locators("axb, page:5", ("a.b",))[0]["kind"] == "gap"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Annual page:71", [(71, None)]),
        ("Annual pages 71, 123", [(71, None), (123, None)]),
        ("Annual pages 63, 71, 120, 144-145", [(63, None), (71, None), (120, None), (144, 145)]),
        ("Annual p. 71", [(71, None)]),
        ("Annual p.59", [(59, None)]),
        ("Annual pp.55,123", [(55, None), (123, None)]),
        ("Annual pp.62–63", [(62, 63)]),
        ("Annual pages 13, 24–25, 31", [(13, None), (24, 25), (31, None)]),
        ("Annual pages: 4", [(4, None)]),
        ("Annual PAGE 8", [(8, None)]),
    ],
)
def test_every_page_form_of_a_leading_word_resolves_to_the_primary_alias(text, expected):
    got = aliased(text)
    assert [(g["page"], g["page_end"]) for g in got] == expected
    assert {g["source"] for g in got} == {"Annual filing"}
    assert {g["note"] for g in got} == {NOTE_ANNUAL}


def test_the_alias_in_full_and_a_unique_leading_word():
    (full,) = aliased("Annual filing page:71")
    assert full == loc("issuer_page", "Annual filing", 71)
    (pdf,) = aliased("Annual PDF pp.3–4")
    assert pdf == loc("issuer_page", "Annual PDF", 3, 4)
    (march,) = aliased("March pages 31-32")
    assert march == loc(
        "issuer_page", "March filing", 31, 32, note="alias 'March' → 'March filing'"
    )
    (june,) = aliased("June filing p.2")
    assert june["source"] == "June filing" and june["note"] is None


def test_a_leading_word_that_fits_two_non_alternate_aliases_is_a_gap():
    (got,) = parse_locators("Annual p.71", ALIASES, ())
    assert got["kind"] == "gap" and got["source"] is None and got["page"] == 71
    assert got["label"] == "Annual p.71 · ambiguous"
    assert "Annual filing" in got["note"] and "Annual PDF" in got["note"]
    both = parse_locators("Annual pp.5–6", ALIASES, ("Annual filing", "Annual PDF"))
    assert [g["label"] for g in both] == ["Annual p.5-6 · ambiguous"]


def test_an_exact_alias_beats_a_leading_word():
    (got,) = parse_locators("Annual page:3", ("Annual", "Annual filing"), ())
    assert got == loc("issuer_page", "Annual", 3)


def test_a_bare_page_after_an_aliased_one_inherits_the_resolved_alias():
    got = aliased("Annual p.71 and later page:72")
    assert pages_of(got) == [("Annual filing", 71, None), ("Annual filing", 72, None)]


def test_a_listed_item_that_is_not_a_page_is_not_read():
    assert pages_of(aliased("Annual page:71, 2024 results")) == [("Annual filing", 71, None)]


def test_inventory_alternates_reads_the_role_column():
    headers = ["Alias", "Exact supplied source name", "Exact sha256", "Role in this review"]
    sections = inventory_section("Supplied source inventory", headers)
    rows = [
        ["Annual filing", "a", "ab" * 32, "Primary annual authority"],
        ["Annual PDF", "b", "cd" * 32, "Sampled alternate annual representation"],
        ["Quarter", "c", "ef" * 32, "Alternate quarterly copy"],
    ]
    sections[0]["blocks"][0]["rows"] = [{"line": 5 + i, "cells": r} for i, r in enumerate(rows)]
    assert inventory_alternates(sections) == {"Annual PDF", "Quarter"}
    plain = inventory_section("Inventory", ["Alias", "Name", "Exact sha256", "Source disposition"])
    plain[0]["blocks"][0]["rows"][0]["cells"] = ["K", "k.jsonl", "ab" * 32, "alternate"]
    assert inventory_alternates(plain) == frozenset()


def alias_run(tmp_path):
    filing = hashlib.sha256(ALIAS_FILING_PAGES).hexdigest()
    pdf = hashlib.sha256(ALIAS_PDF_PAGES).hexdigest()
    run = make_run(
        tmp_path,
        "run-b",
        cp0_extra=alias_inventory_text(filing, pdf),
        cp1_extra=ALIAS_CITED,
    )
    (run / "source-text").mkdir()
    (run / "source-text" / ALIAS_FILING_NAME).write_bytes(ALIAS_FILING_PAGES)
    (run / "source-text" / ALIAS_PDF_NAME).write_bytes(ALIAS_PDF_PAGES)
    library = build_library(tmp_path, tmp_path / "library", method())
    return run, workspace_store(tmp_path, catalogue(tmp_path, library))


def test_alias_run_end_to_end(tmp_path):
    run, store = alias_run(tmp_path)
    got = chips(tmp_path, store)
    (short,) = got[line_of(run, store, "| Short form")]
    assert (short["source"], short["file"], short["avatar"]) == (
        "Annual filing",
        ALIAS_FILING_NAME,
        "AF",
    )
    assert (short["page"], short["quote"], short["quote_found"]) == (71, "3472", True)
    assert short["reason"] == NOTE_ANNUAL and short["hash_matches_inventory"] is True
    assert short["match"] == "3,472" and short["excerpt"][short["match_at"] :].startswith("3,472")
    (bracket,) = got[line_of(run, store, "| Bracketed")]
    assert (bracket["quote"], bracket["quote_found"], bracket["match"]) == ("-11", True, "(11)")
    first, second, third = got[line_of(run, store, "| Listed")]
    assert [(c["source"], c["page"], c["page_end"]) for c in (first, second)] == [
        ("Annual filing", 71, None),
        ("Annual filing", 72, None),
    ]
    assert (third["source"], third["page"], third["page_end"]) == ("Annual filing", 71, 72)
    assert third["avatar"] == "AF" and third["reason"] is None
    assert first["reason"] == NOTE_ANNUAL and second["reason"] == NOTE_ANNUAL


def test_a_pdf_alias_chip_reads_the_pdf_text(tmp_path):
    run, _ = alias_run(tmp_path)
    (pdf,) = chips_for_output(
        run,
        "x/CP-1.md",
        "CP-1",
        table(("a", "9999", "Annual PDF p.71")),
        {"Annual PDF": (ALIAS_PDF_NAME, hashlib.sha256(ALIAS_PDF_PAGES).hexdigest())},
    )["x/CP-1.md:4"]
    assert (pdf["avatar"], pdf["quote_found"], pdf["match"]) == ("AP", True, "9,999")


def test_a_single_letter_key_keeps_its_letter_as_avatar(tmp_path):
    run, inv = one_run(tmp_path)
    (got,) = run_chips(run, inv, ("a", "1", "K, page:10"))["x/CP-1.md:4"]
    assert got["avatar"] == "K"


def test_an_alias_first_cell_names_the_source_of_a_bare_page(tmp_path):
    run, inv = one_run(tmp_path)
    inv = {"Annual filing": inv["K"]}
    (got,) = run_chips(run, inv, ("Annual", "page 10", "n/a"))["x/CP-1.md:4"]
    assert (got["source"], got["page"], got["reason"]) == (
        "Annual filing",
        10,
        "alias 'Annual' → 'Annual filing'",
    )


def test_match_is_the_exact_page_span_of_a_tolerant_number(tmp_path):
    pages = b'{"page": 3, "text": "Net sales were 3,472 and the loss was (11) before tax."}\n'
    run, inv = one_run(tmp_path, pages=pages)
    (comma,) = run_chips(run, inv, ("a", "3472", "K, page:3"))["x/CP-1.md:4"]
    assert comma["quote_found"] is True and comma["match"] == "3,472"
    assert comma["excerpt"][comma["match_at"] : comma["match_at"] + 5] == "3,472"
    (bracket,) = run_chips(run, inv, ("a", "-11", "K, page:3"))["x/CP-1.md:4"]
    assert bracket["match"] == "(11)"
    (text,) = run_chips(run, inv, ("a", "-", "K, page:3 says “Net sales”"))["x/CP-1.md:4"]
    assert text["match"] == "Net sales" and text["match_at"] == 0
    (miss,) = run_chips(run, inv, ("a", "999", "K, page:3"))["x/CP-1.md:4"]
    assert (miss["quote_found"], miss["match"], miss["match_at"]) == (False, None, None)
    (none,) = run_chips(run, inv, ("a", "-", "K, page:3"))["x/CP-1.md:4"]
    assert (none["quote"], none["match"]) == (None, None)


def test_match_stays_inside_a_clipped_excerpt(tmp_path):
    long = "x" * 900
    pages = ('{"page": 1, "text": "' + long + '"}\n').encode()
    run, inv = one_run(tmp_path, pages=pages)
    (got,) = run_chips(run, inv, ("a", "-", f"K, page:1 says “{long}”"))["x/CP-1.md:4"]
    assert got["quote_found"] is True
    assert got["match"] in got["excerpt"] and len(got["match"]) <= 600
    assert got["excerpt"][got["match_at"] :].startswith(got["match"])


def test_an_ambiguous_alias_becomes_a_gap_chip_with_its_reason(tmp_path):
    headers = ["Alias", "Exact supplied source name", "Exact sha256", "Role in this review"]
    sections = inventory_section("Supplied source inventory", headers)
    rows = [
        ["Annual filing", "a.jsonl", "ab" * 32, "Primary"],
        ["Annual PDF", "b.jsonl", "cd" * 32, "Primary as well"],
    ]
    sections[0]["blocks"][0]["rows"] = [{"line": 5 + i, "cells": r} for i, r in enumerate(rows)]
    inv = inventory(sections)
    assert inv.alternates == frozenset()
    run, _ = one_run(tmp_path)
    (got,) = chips_for_output(run, "x/CP-1.md", "CP-1", table(("a", "1", "Annual p.5")), inv)[
        "x/CP-1.md:4"
    ]
    assert (got["kind"], got["source"], got["label"]) == ("gap", None, "Annual p.5 · ambiguous")
    assert got["reason"].startswith("alias 'Annual' fits 'Annual filing', 'Annual PDF'")
    assert got["avatar"] is None and got["excerpt"] is None


def test_overflowing_page_number_is_a_reason_not_an_exception():
    pages, problem = read_pages(b'{"page": 1e400, "text": "x"}\n')
    assert pages == {}
    assert problem is not None and problem.startswith("source text unreadable")


@pytest.mark.parametrize("name", ["C:secret.jsonl", "C:..x", "a:b"])
def test_a_drive_relative_name_is_not_a_bare_file_name(name):
    assert not is_file_name(name)


def test_a_huge_page_range_reads_only_the_pages_the_source_has(tmp_path):
    # Handoff text is model output: "pp. 10-300000000" must not be walked page by page.
    run, inv = one_run(tmp_path)
    started = time.monotonic()
    (got,) = run_chips(run, inv, ("a", "-", "K, pp. 10-300000000 says “alpha”"))["x/CP-1.md:4"]
    assert time.monotonic() - started < 5
    assert (got["kind"], got["page"], got["page_end"]) == ("issuer_page", 10, 300000000)
    assert got["quote_found"] is True


def test_a_page_number_too_long_to_be_one_is_a_gap_not_an_exception(tmp_path):
    run, inv = one_run(tmp_path)
    digits = "9" * 5000  # int() refuses a decimal string this long
    (got,) = run_chips(run, inv, ("a", "-", f"K, page:{digits}"))["x/CP-1.md:4"]
    assert got["kind"] == "gap" and got["label"] == "p.999999999999… · not a page number"


# --- H3 Basis line: the last line of a paragraph or list item ----------------------------------

ANNUAL = "Annual report 2024.pdf"
BASIS_PAGES = (
    b'{"page": 40, "text": "forty text"}\n'
    b'{"page": 41, "text": "Leverage was 6.1x at year end."}\n'
    b'{"page": 42, "text": "forty two text"}\n'
)


def paragraph_chips(run, inv, text):
    sections = [
        {
            "heading": "H",
            "level": 3,
            "line": 1,
            "blocks": [{"type": "paragraph", "line": 7, "text": text}],
        }
    ]
    return chips_for_output(run, "x/CP-2D.md", "CP-2D", sections, inv).get("x/CP-2D.md:7", [])


def test_basis_line_file_and_page_gives_an_issuer_page_chip(tmp_path):
    run, inv = one_run(tmp_path, BASIS_PAGES, ANNUAL, ANNUAL)
    text = f"The issuer's leverage stays high.\nBasis: {ANNUAL}, page 41."
    (got,) = paragraph_chips(run, inv, text)
    assert (got["kind"], got["source"], got["file"]) == ("issuer_page", "K", ANNUAL)
    assert (got["page"], got["page_end"]) == (41, None)
    assert got["excerpt"] == "Leverage was 6.1x at year end."


def test_basis_line_page_range_with_an_en_dash(tmp_path):
    run, inv = one_run(tmp_path, BASIS_PAGES, ANNUAL, ANNUAL)
    (got,) = paragraph_chips(run, inv, f"Claim.\nBasis: {ANNUAL}, pages 40–42")
    assert (got["kind"], got["page"], got["page_end"]) == ("issuer_page", 40, 42)


def test_basis_line_module_item_is_upstream_and_calculation_gives_no_chip(tmp_path):
    run, inv = one_run(tmp_path, BASIS_PAGES, ANNUAL, ANNUAL)
    (got,) = paragraph_chips(run, inv, "Claim.\nBasis: Liquidity (CP-2D); calculation K1")
    assert (got["kind"], got["module"], got["codes"]) == ("upstream", "CP-2D", [])


def test_basis_line_file_not_in_inventory_is_a_gap(tmp_path):
    run, inv = one_run(tmp_path, BASIS_PAGES, ANNUAL, ANNUAL)
    (got,) = paragraph_chips(run, inv, "Claim.\nBasis: Other file.pdf, page 3.")
    assert got["kind"] == "gap" and "not in inventory" in got["label"]


def test_basis_line_file_without_a_page_and_unknown_item(tmp_path):
    run, inv = one_run(tmp_path, BASIS_PAGES, ANNUAL, ANNUAL)
    assert paragraph_chips(run, inv, f"Claim.\nBasis: {ANNUAL}") == []
    (got,) = paragraph_chips(run, inv, "Claim.\nBasis: something odd")
    assert got["kind"] == "gap" and got["label"] == "Basis item not recognised"
    assert "something odd" in got["reason"]


def test_a_paragraph_without_a_basis_line_keeps_the_trailing_code_chip(tmp_path):
    run, inv = one_run(tmp_path, BASIS_PAGES, ANNUAL, ANNUAL)
    (got,) = paragraph_chips(run, inv, "Leverage stays high, see K1.")
    assert (got["kind"], got["module"], got["codes"]) == ("upstream", "CP-2D", ["K1"])


def test_an_indented_basis_line_under_a_list_item_resolves(tmp_path):
    run, inv = one_run(tmp_path, BASIS_PAGES, ANNUAL, ANNUAL)
    for text in (
        f"- Claim.\n  Basis: {ANNUAL}, page 41.",
        f"1. Claim.\n   Basis: {ANNUAL}, page 41.",
        f"Claim.\nBasis: {ANNUAL}, page 41. ",
    ):
        (got,) = paragraph_chips(run, inv, text)
        assert (got["kind"], got["source"], got["page"]) == ("issuer_page", "K", 41), text
