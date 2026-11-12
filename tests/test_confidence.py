"""The confidence score is computed from a module's inputs table by Python.

The answer key is the archived script `confidence_score.py`, never edited: every expected value
here is what that script prints, run as a subprocess (the hand-picked cases) or loaded once and
called for a seeded batch (the property loop)."""

import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

from deploy_workflow import confidence
from deploy_workflow.confidence import Refused, Score

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "docs/reuse/selected-methods/skills/cp-5-evidence-trace-validator/scripts/confidence_score.py"
)
CLASSES = (
    "Directly Sourced",
    "Calculated",
    "Assumption-Based",
    "Analyst Inference",
    "Weak Lineage",
    "Untraced",
    "Conflicting",
    "Insufficient Information",
)


def oracle(lineage, present, total, gate, findings):
    """What the archived script prints for one input set, run as the script runs."""
    payload = {
        "lineage": lineage,
        "fields_present": present,
        "fields_total": total,
        "source_gate": gate,
        "findings": findings,
    }
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--json", json.dumps(payload)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    out = json.loads(done.stdout)
    return out["confidence_score"], out["confidence_band"], out["qa_status"]


CASES = {
    "canon worked example": (
        {"Directly Sourced": 8, "Calculated": 2, "Assumption-Based": 2},
        95,
        100,
        "pass",
        {"MINOR": 1},
    ),
    "all direct": ({"Directly Sourced": 10}, 100, 100, "pass", {}),
    "critical cap": ({"Directly Sourced": 10}, 100, 100, "pass", {"CRITICAL": 1}),
    "material cap": ({"Directly Sourced": 10}, 100, 100, "pass", {"MATERIAL": 1}),
    "critical beats material": (
        {"Directly Sourced": 10},
        100,
        100,
        "pass",
        {"CRITICAL": 1, "MATERIAL": 2},
    ),
    "lower clamp": ({"Weak Lineage": 3}, 1, 10, "pass", {"CRITICAL": 3, "MINOR": 4}),
    "all direct, full coverage": ({"Directly Sourced": 4}, 10, 10, "pass", {}),
    "exactly 80": ({"Directly Sourced": 10}, 5, 10, "pass", {}),
    "exactly 79": ({"Directly Sourced": 6, "Weak Lineage": 4}, 9, 10, "pass", {}),
    "failed gate": ({"Directly Sourced": 1}, 1, 1, "fail", {}),
    "partial gate": ({"Calculated": 5, "Untraced": 1}, 7, 9, "partial", {"MINOR": 2}),
    "no claims": ({}, 1, 1, "pass", {}),
    "half rounds to even (2.5)": ({}, 1, 16, "pass", {}),
    "half rounds to even (7.5)": ({}, 3, 16, "pass", {}),
    "half rounds to even (12.5)": ({}, 5, 16, "pass", {}),
    "no coverage, pass": ({"Directly Sourced": 1}, 0, 10, "pass", {}),
    "no coverage, partial": ({"Directly Sourced": 1}, 0, 10, "partial", {"MINOR": 0}),
    "zero findings": (
        {"Analyst Inference": 2, "Conflicting": 1},
        3,
        4,
        "pass",
        {"MINOR": 0, "MATERIAL": 0},
    ),
    "case folded names": ({"directly sourced": 3, "CALCULATED": 1}, 9, 10, "PASS", {"minor": 1}),
}


@pytest.mark.parametrize("name", CASES)
def test_score_equals_the_archived_script(name):
    lineage, present, total, gate, findings = CASES[name]
    got = confidence.score(lineage, present, total, gate, findings)
    assert isinstance(got, Score)
    assert (got.value, got.band, got.status) == oracle(lineage, present, total, gate, findings)


def test_the_caps_and_clamps_are_the_ones_the_cases_exercise():
    def value(name):
        return confidence.score(*CASES[name]).value

    assert confidence.score(*CASES["canon worked example"]).value == 89
    assert confidence.score(*CASES["critical cap"]) == Score(
        39, "Insufficient Information", "Blocked"
    )
    assert confidence.score(*CASES["material cap"]) == Score(59, "Low", "Restricted")
    assert confidence.score(*CASES["critical beats material"]).status == "Blocked"
    assert value("lower clamp") == 0 and value("all direct, full coverage") == 100
    assert [value(f"half rounds to even ({n})") for n in ("2.5", "7.5", "12.5")] == [2, 8, 12]


def test_seeded_random_input_sets_equal_the_archived_script():
    rng = random.Random(20261112)
    sets = []
    for _ in range(400):
        total = rng.randint(1, 30)
        sets.append(
            {
                "lineage": {c: rng.randint(0, 12) for c in CLASSES if rng.random() < 0.7},
                "fields_present": rng.randint(0, total),
                "fields_total": total,
                "source_gate": rng.choice(["pass", "partial", "fail"]),
                "findings": {
                    k: rng.randint(0, 2)
                    for k in ("CRITICAL", "MATERIAL", "MINOR")
                    if rng.random() < 0.6
                },
            }
        )
    driver = (
        "import importlib.util, json, sys\n"
        "spec = importlib.util.spec_from_file_location('key', sys.argv[1])\n"
        "key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)\n"
        "out = []\n"
        "for p in json.load(sys.stdin):\n"
        "    r = key.compute(p['lineage'], p['fields_present'], p['fields_total'],\n"
        "                    p['source_gate'], p['findings'])\n"
        "    out.append([r['confidence_score'], r['confidence_band'], r['qa_status']])\n"
        "print(json.dumps(out))\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", driver, str(SCRIPT)],
        input=json.dumps(sets),
        capture_output=True,
        text=True,
        check=True,
    )
    expected = json.loads(done.stdout)
    got = [
        list(
            (
                s := confidence.score(
                    p["lineage"],
                    p["fields_present"],
                    p["fields_total"],
                    p["source_gate"],
                    p["findings"],
                )
            )
            and (s.value, s.band, s.status)
        )
        for p in sets
    ]
    assert got == expected
    assert {g[2] for g in got} == {"Passed", "Restricted", "Blocked"}


@pytest.mark.parametrize(
    "args",
    [
        ({"Bogus": 1}, 1, 1, "pass", {}),
        ({"Calculated": -1}, 1, 1, "pass", {}),
        ({}, 0, 0, "pass", {}),
        ({}, 2, 1, "pass", {}),
        ({}, 1, 1, "maybe", {}),
        ({}, 1, 1, "pass", {"SEVERE": 1}),
        ({}, 1, 1, "pass", {"MINOR": -1}),
    ],
)
def test_an_input_the_script_refuses_is_refused(args):
    lineage, present, total, gate, findings = args
    payload = json.dumps(
        {
            "lineage": lineage,
            "fields_present": present,
            "fields_total": total,
            "source_gate": gate,
            "findings": findings,
        }
    )
    assert (
        subprocess.run(
            [sys.executable, str(SCRIPT), "--json", payload], capture_output=True, check=False
        ).returncode
        == 2
    )
    with pytest.raises(ValueError):
        confidence.score(*args)


def table(rows, header="| Input | Value |"):
    return "\n".join([header, "| --- | --- |", *(f"| {k} | {v} |" for k, v in rows)])


GOOD_ROWS = [
    ("Directly Sourced", 8),
    ("Calculated", 2),
    ("Assumption-Based", 2),
    ("Analyst Inference", 0),
    ("Weak Lineage", 0),
    ("Untraced", 0),
    ("Conflicting", 0),
    ("Insufficient Information", 0),
    ("Fields present", 95),
    ("Fields total", 100),
    ("Source gate", "pass"),
    ("CRITICAL", 0),
    ("MATERIAL", 0),
    ("MINOR", 1),
]


def handoff(rows=GOOD_ROWS, header="| Input | Value |", after="### Next\n\ntext\n"):
    head = "## Findings\n\n### Bottom line\n\nx\n\n### Confidence inputs\n\n"
    return f"{head}{table(rows, header)}\n\n{after}"


def test_from_handoff_reads_the_table():
    assert confidence.from_handoff(handoff()) == Score(89, "High", "Passed")


def test_from_handoff_reads_the_table_at_the_end_of_the_text_and_in_any_row_order():
    rows = list(reversed(GOOD_ROWS))
    assert confidence.from_handoff(handoff(rows, after="")) == Score(89, "High", "Passed")


def test_a_handoff_without_the_section_is_refused_as_absent():
    got = confidence.from_handoff("## Findings\n\n### Bottom line\n\nx\n")
    assert isinstance(got, Refused) and got.absent


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        ([r for r in GOOD_ROWS if r[0] != "Source gate"], "Source gate"),
        ([r for r in GOOD_ROWS if r[0] != "MINOR"], "MINOR"),
        ([*GOOD_ROWS, ("MINOR", 2)], "MINOR"),
        ([*GOOD_ROWS, ("Mystery", 2)], "Mystery"),
        ([("Calculated", "many") if r[0] == "Calculated" else r for r in GOOD_ROWS], "Calculated"),
        ([("Calculated", "2.5") if r[0] == "Calculated" else r for r in GOOD_ROWS], "Calculated"),
        ([("Calculated", "-1") if r[0] == "Calculated" else r for r in GOOD_ROWS], "Calculated"),
        ([("Calculated", "") if r[0] == "Calculated" else r for r in GOOD_ROWS], "Calculated"),
        ([("Fields total", 0) if r[0] == "Fields total" else r for r in GOOD_ROWS], "Fields total"),
        (
            [("Fields present", 101) if r[0] == "Fields present" else r for r in GOOD_ROWS],
            "Fields present",
        ),
        (
            [("Source gate", "maybe") if r[0] == "Source gate" else r for r in GOOD_ROWS],
            "Source gate",
        ),
        ([("Source gate", 1) if r[0] == "Source gate" else r for r in GOOD_ROWS], "Source gate"),
    ],
)
def test_a_missing_duplicate_unknown_or_non_numeric_row_is_refused_with_the_reason(rows, reason):
    got = confidence.from_handoff(handoff(rows))
    assert isinstance(got, Refused) and not got.absent
    assert reason in got.reason


def test_a_table_with_another_header_or_no_rows_is_refused():
    wrong = confidence.from_handoff(handoff(header="| Name | Amount |"))
    assert isinstance(wrong, Refused) and "Input | Value" in wrong.reason
    none = confidence.from_handoff("### Confidence inputs\n\nNo table here.\n")
    assert isinstance(none, Refused) and not none.absent


def test_a_second_section_of_the_name_does_not_hide_a_bad_first_one():
    bad = handoff([r for r in GOOD_ROWS if r[0] != "MINOR"])
    assert isinstance(confidence.from_handoff(bad + "\n" + handoff()), Refused)


def test_the_band_threshold_is_80_exactly():
    exact, below = (confidence.score(*CASES[n]) for n in ("exactly 80", "exactly 79"))
    assert (exact.value, exact.band) == (80, "High")
    assert (below.value, below.band) == (79, "Medium")


def test_two_well_formed_sections_of_the_name_are_refused():
    got = confidence.from_handoff(handoff() + "\n" + handoff())
    assert isinstance(got, Refused) and not got.absent
    assert "more than once" in got.reason


def test_a_three_cell_row_is_refused():
    text = handoff().replace("| MINOR | 1 |", "| MINOR | 1 | extra |")
    got = confidence.from_handoff(text)
    assert isinstance(got, Refused) and "2 cells" in got.reason


def test_a_section_only_inside_a_fence_is_not_the_table():
    fenced = "## Findings\n\n```text\n" + handoff() + "```\n"
    got = confidence.from_handoff(fenced)
    assert isinstance(got, Refused) and got.absent
    both = handoff().replace(
        "### Confidence inputs",
        "```text\n### Confidence inputs\n| Input | x |\n```\n\n### Confidence inputs",
    )
    assert confidence.from_handoff(both) == Score(89, "High", "Passed")


@pytest.mark.parametrize("sep", ["| :-- | --: |", "| - | - |", "|:-:|:-:|", "| --- | :---: |"])
def test_any_gfm_separator_row_is_accepted(sep):
    text = handoff().replace("| --- | --- |", sep)
    assert confidence.from_handoff(text) == Score(89, "High", "Passed")


@pytest.mark.parametrize("digits", [20, 21, 309, 400, 5000])
def test_a_huge_claim_or_finding_count_is_refused_not_an_overflow(digits):
    rows = [("Calculated", "9" * digits) if r[0] == "Calculated" else r for r in GOOD_ROWS]
    got = confidence.from_handoff(handoff(rows))
    if digits <= confidence.MAX_DIGITS:
        assert isinstance(got, Score)
    else:
        assert isinstance(got, Refused) and not got.absent and "digits" in got.reason
    if digits > confidence.MAX_DIGITS:
        with pytest.raises(ValueError):
            confidence.score({"Calculated": 10**digits}, 1, 1, "pass", {})
        with pytest.raises(ValueError):
            confidence.score({}, 1, 1, "pass", {"MINOR": 10**digits})


@pytest.mark.parametrize("digits", [400, 4000, 4001, 5000])  # digits written, not zeros
def test_a_huge_field_count_is_exact_or_refused_never_raised(digits):
    rows = [
        (r[0], "1" + "0" * (digits - 1)) if r[0] in ("Fields present", "Fields total") else r
        for r in GOOD_ROWS
    ]
    got = confidence.from_handoff(handoff(rows))
    if digits <= 4000:
        lineage = dict(zip(CLASSES, (8, 2, 2, 0, 0, 0, 0, 0)))
        assert got == confidence.score(
            lineage, 10 ** (digits - 1), 10 ** (digits - 1), "pass", {"MINOR": 1}
        )
    else:
        assert isinstance(got, Refused) and "digits" in got.reason


WRONG = {
    "missing row": [r for r in GOOD_ROWS if r[0] != "Source gate"],
    "duplicate row": [*GOOD_ROWS, ("MINOR", 2)],
    "unknown row": [*GOOD_ROWS, ("Mystery", 2)],
    "word for a count": [("Calculated", "many") if r[0] == "Calculated" else r for r in GOOD_ROWS],
    "huge count": [("Calculated", "9" * 400) if r[0] == "Calculated" else r for r in GOOD_ROWS],
    "present above total": [
        ("Fields present", 101) if r[0] == "Fields present" else r for r in GOOD_ROWS
    ],
    "bad gate": [("Source gate", "maybe") if r[0] == "Source gate" else r for r in GOOD_ROWS],
}


@pytest.mark.parametrize("name", WRONG)
def test_the_shown_reason_is_a_short_plain_sentence_never_model_text(name):
    text = handoff(WRONG[name]).replace("Mystery", "Mystery # `CP-5` |")
    got = confidence.from_handoff(text)
    assert isinstance(got, Refused)
    assert got.shown in confidence.SHOWN
    for bad in ("#", "`", "|", "CP-", "Mystery", "many", "maybe", "Source gate"):
        assert bad not in got.shown
    assert not got.shown.endswith(".")


def test_every_refusal_has_a_shown_sentence_from_the_fixed_set():
    for header in ("| Name | Amount |", "| Input | Value |"):
        got = confidence.from_handoff(handoff(header=header, rows=[("Mystery", 1)]))
        assert isinstance(got, Refused) and got.shown in confidence.SHOWN


def test_fenced_lines_inside_the_section_are_not_table_rows_or_headings():
    after = "```text\n| Mystery | 1 |\n# not a heading\n```\n\n### Next\n\ntext\n"
    assert confidence.from_handoff(handoff(after=after)) == Score(89, "High", "Passed")
    inside = handoff(after="```text\n### Confidence inputs\n```\n")
    assert confidence.from_handoff(inside) == Score(89, "High", "Passed")


def test_a_negative_count_is_not_a_whole_number():
    rows = [("Calculated", "-1") if r[0] == "Calculated" else r for r in GOOD_ROWS]
    got = confidence.from_handoff(handoff(rows))
    assert isinstance(got, Refused) and got.shown == confidence.SHOWN_NOT_WHOLE
