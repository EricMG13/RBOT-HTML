"""Citation chips: locators parsed from handoff text, resolved against a run's source text.
Expected locators and flags are written here from the fixture text, not read from the code."""

import hashlib
import json
import sys
from pathlib import Path

import pytest
from library_fixtures import CITED, SOURCE_NAME, SOURCE_PAGES, inventory_text, make_run, method

from deploy_workflow.credit_os_catalogue import catalogue
from deploy_workflow.credit_os_chips import chips, inventory, parse_locators
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


def test_upstream_bracket():
    assert parse_locators("[CP-1: D4, F1]") == [loc("upstream", module="CP-1", codes=("D4", "F1"))]
    assert parse_locators("[CP-1A: E2]") == [loc("upstream", module="CP-1A", codes=("E2",))]
    assert parse_locators("[CP-1: D4; F3]")[0]["codes"] == ("D4", "F3")


def test_trailing_register_codes_belong_to_the_module_itself():
    got = parse_locators("Same basis; pre-dividend cash. D1, D3, E1.")
    assert got == [loc("upstream", codes=("D1", "D3", "E1"))]


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
    assert k["hash_matches_inventory"] is False and k["quote_found"] is None


def test_update_library_writes_chips_into_data_js(tmp_path):
    run, store = built(tmp_path)
    update_library.update_library(tmp_path)
    text = (tmp_path / "library/data.js").read_text(encoding="utf-8")
    data = json.loads(text.removeprefix("window.CREDIT_OS_DATA=").rstrip().removesuffix(";"))
    key = line_of(run, store, "| Cash interest")
    assert data["chips"][key][0]["quote_found"] is True
